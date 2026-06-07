"""
Stage 4 token-level dynamics analysis.

Consumes Stage 6 Qwen3-14B token trace artifacts and computes per-prompt,
per-generated-token, per-layer refusal-direction projection metrics.

Moves from:
    layer → refusal_score
to:
    prompt_id × generated_token_index × layer → refusal_projection

Reuses:
  - poc_stage4.qwen3_model.load_qwen3_model
  - poc_stage4.direction_loader.load_direction
  - poc_stage4.run_state.append_jsonl / atomic_write_json / log_progress
  - poc_stage4.schemas.make_json_safe
  - Chain_of_Thought_Hijacking/refusal_direction/pipeline/utils/hook_utils.add_hooks
    (paper code, context manager for temporary hook registration)
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import torch

from poc_stage4.direction_loader import load_direction
from poc_stage4.qwen3_model import load_qwen3_model
from poc_stage4.run_state import append_jsonl, atomic_write_json, log_progress
from poc_stage4.schemas import make_json_safe

ARTIFACT_VERSION = "poc_stage4_token_dynamics_v1"
STAGE_NAME = "stage4_token_dyn"
DEFAULT_MODEL = "Qwen/Qwen3-14B"
DEFAULT_DIRECTION_DIR = "outputs/stage4/qwen3-14b/refusal_direction"
DEFAULT_MAX_EXAMPLES_SMOKE = 5
DEFAULT_MAX_NEW_TOKENS_SMOKE = 128


# ---------------------------------------------------------------------------
# Hook utilities
# ---------------------------------------------------------------------------

def _import_add_hooks():
    """
    Import add_hooks from the paper code (Chain_of_Thought_Hijacking).
    Falls back to a minimal inline implementation if the paper code is not
    importable (e.g. missing jaxtyping dependency).
    """
    repo_root = Path(__file__).resolve().parent.parent
    hook_utils_path = (
        repo_root
        / "Chain_of_Thought_Hijacking"
        / "refusal_direction"
        / "pipeline"
        / "utils"
        / "hook_utils.py"
    )
    if hook_utils_path.exists():
        spec = importlib.util.spec_from_file_location("_hook_utils_paper", hook_utils_path)
        if spec is not None and spec.loader is not None:
            try:
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)  # type: ignore[union-attr]
                add_hooks = getattr(mod, "add_hooks", None)
                if add_hooks is not None:
                    return add_hooks
            except Exception as exc:
                log_progress(STAGE_NAME, f"Paper hook_utils import failed ({exc}); using fallback")

    # Minimal fallback context manager — same semantics as paper version
    import contextlib
    import functools

    @contextlib.contextmanager
    def add_hooks(module_forward_pre_hooks, module_forward_hooks, **kwargs):
        handles = []
        try:
            for module, hook in module_forward_pre_hooks:
                partial_hook = functools.partial(hook, **kwargs)
                handles.append(module.register_forward_pre_hook(partial_hook))
            for module, hook in module_forward_hooks:
                partial_hook = functools.partial(hook, **kwargs)
                handles.append(module.register_forward_hook(partial_hook))
            yield
        finally:
            for h in handles:
                h.remove()

    return add_hooks


def get_residual_projection_pre_hook(
    layer_idx: int,
    direction_cpu: torch.Tensor,
    projections_store: dict[int, list[float]],
):
    """
    Read-only pre-hook: captures residual stream input at layer_idx and
    projects all sequence positions onto the refusal direction.

    Consistent with poc_stage4/activation_capture.py:
    register_forward_pre_hook on layers[layer_idx] captures the input to
    that layer, which equals the output of layers[layer_idx-1] (same as
    hidden_states[layer_idx] from output_hidden_states=True).

    Used via add_hooks() from the paper code (hook_utils.py).
    Returns None so the forward pass is not modified.
    """
    _debug_done: list[bool] = []  # mutable cell so nested fn can set it

    def hook_fn(module: Any, input: Any) -> None:
        act = input[0] if isinstance(input, tuple) else input  # [1, seq_len, d_model]
        dir_on_device = direction_cpu.to(act.device)
        proj_tensor = (act[0].float() @ dir_on_device).detach()
        # Debug: log shape/dtype for first call on each layer
        if not _debug_done:
            _debug_done.append(True)
            import sys
            print(
                f"[hook_debug] layer={layer_idx}"
                f" act.shape={tuple(act.shape)}"
                f" dir.shape={tuple(dir_on_device.shape)}"
                f" proj.shape={tuple(proj_tensor.shape)}"
                f" act.device={act.device}"
                f" dir.device={dir_on_device.device}",
                file=sys.stderr, flush=True,
            )
        proj = proj_tensor.cpu().tolist()
        if not isinstance(proj, list):
            proj = [float(proj)]
        projections_store[layer_idx] = proj

    return hook_fn


# ---------------------------------------------------------------------------
# Input handling
# ---------------------------------------------------------------------------

def _collect_trace_files(stage6_input: Path) -> list[Path]:
    if stage6_input.is_file():
        return [stage6_input]
    files = sorted(stage6_input.glob("*.json"))
    # skip batch_summary and other non-trace files
    return [f for f in files if not f.name.startswith("batch_summary")]


def _read_artifact(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _prompt_id(artifact: dict[str, Any]) -> str:
    return str(artifact.get("selected_example", {}).get("example_id") or path_to_prompt_id(artifact))


def path_to_prompt_id(artifact: dict[str, Any]) -> str:
    return artifact.get("output_json") or "unknown"


def _safe_filename(prompt_id: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_.\-]+", "_", prompt_id).strip("_.-")
    return (cleaned or "example")[:200]


# ---------------------------------------------------------------------------
# Projection computation
# ---------------------------------------------------------------------------

def _model_input_device(model: Any) -> torch.device:
    try:
        return model.get_input_embeddings().weight.device
    except Exception:
        return next(model.parameters()).device


def compute_projections_for_example(
    *,
    artifact: dict[str, Any],
    model: Any,
    direction: torch.Tensor,
    selected_layers: list[int],
    max_new_tokens_to_analyze: int | None,
    add_hooks: Any,  # kept in signature for API compatibility; not used
) -> dict[str, Any]:
    """
    Run a single forward pass on the full sequence from a Stage 6 artifact
    and return per-layer projection lists over generated tokens.

    Uses forward pre-hooks (NOT output_hidden_states=True) so that only one
    layer's activation occupies GPU memory at a time.  With output_hidden_states
    the forward pass holds all 41 hidden-state tensors simultaneously (~6-10 GB
    for long sequences), which causes OOM on top of the ~39 GB model footprint.
    Hooks project each layer's activation onto the refusal direction immediately
    and store only the resulting Python float list, keeping peak extra GPU usage
    to ~160 MB (one float32 activation tensor for seq_len ≈ 8000).

    This approach requires a single GPU (device_map={"": 0}), which is enforced
    by the SLURM script (--gpus=1, nodelist n-802..n-805).

    Returns a dict with:
      projections:    {layer_idx: list[float]} — full sequence length
      generation_rows: list of token_table rows for generation segment
      prompt_len:     int
      n_gen_full:     int
      n_gen_analyzed: int
      warnings:       list[str]
    """
    warnings: list[str] = []

    full_ids = artifact.get("full_prompt_plus_generation_token_ids")
    prompt_len = artifact.get("prompt_token_count")
    n_gen_full = artifact.get("generation_token_count", 0)
    token_table = artifact.get("token_table", [])

    if not full_ids:
        raise ValueError("Artifact missing full_prompt_plus_generation_token_ids")
    if prompt_len is None:
        raise ValueError("Artifact missing prompt_token_count")

    n_gen_analyzed = n_gen_full
    if max_new_tokens_to_analyze is not None and max_new_tokens_to_analyze < n_gen_full:
        n_gen_analyzed = max_new_tokens_to_analyze

    # Slice the sequence to prompt + analyzed generation only
    seq_len_needed = prompt_len + n_gen_analyzed
    input_ids_list = full_ids[:seq_len_needed]
    if len(input_ids_list) < seq_len_needed:
        warnings.append(
            f"full_prompt_plus_generation_token_ids shorter than expected "
            f"(got {len(input_ids_list)}, expected {seq_len_needed})"
        )
        n_gen_analyzed = max(0, len(input_ids_list) - prompt_len)

    input_ids = torch.tensor(input_ids_list, dtype=torch.long).unsqueeze(0)
    input_device = _model_input_device(model)
    direction_cpu = direction.cpu()

    # --- Forward pre-hooks: capture + project one layer at a time ---
    # register_forward_pre_hook on layer[i] fires with the residual stream
    # input to layer i, which equals output_hidden_states[i].  We immediately
    # project onto the refusal direction and store only the Python float list.
    projections_store: dict[int, list[float]] = {}
    transformer_layers = model.model.layers
    n_model_layers = len(transformer_layers)

    def _make_hook(layer_idx: int):
        def _hook(module: Any, hook_input: Any) -> None:
            act = hook_input[0] if isinstance(hook_input, tuple) else hook_input
            # act: [1, seq_len, hidden_size] on GPU (bfloat16)
            dir_dev = direction_cpu.to(act.device)
            proj = (act[0].float() @ dir_dev).detach().cpu().tolist()
            projections_store[layer_idx] = proj if isinstance(proj, list) else [float(proj)]
            del dir_dev
        return _hook

    handles = []
    for li in selected_layers:
        if li >= n_model_layers:
            warnings.append(f"Layer {li} out of range (model has {n_model_layers} layers)")
            continue
        handles.append(transformer_layers[li].register_forward_pre_hook(_make_hook(li)))

    try:
        with torch.no_grad():
            model(input_ids=input_ids.to(input_device))
    finally:
        for h in handles:
            h.remove()
        del handles

    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    # Build generation-segment token rows indexed by generated_token_index
    generation_rows: list[dict[str, Any]] = [
        row for row in token_table if row.get("segment") == "generation"
    ]
    if len(generation_rows) != n_gen_full:
        warnings.append(
            f"token_table generation rows ({len(generation_rows)}) != "
            f"generation_token_count ({n_gen_full})"
        )

    return {
        "projections": projections_store,
        "generation_rows": generation_rows,
        "prompt_len": prompt_len,
        "n_gen_full": n_gen_full,
        "n_gen_analyzed": n_gen_analyzed,
        "warnings": warnings,
    }


# ---------------------------------------------------------------------------
# Output building
# ---------------------------------------------------------------------------

def _build_token_level_data(
    *,
    projections: dict[int, list[float]],
    generation_rows: list[dict[str, Any]],
    selected_layers: list[int],
    prompt_len: int,
    n_gen_analyzed: int,
) -> list[dict[str, Any]]:
    """
    Build the token_level_data list for the per-example JSON.
    One entry per generated token, with layer_projections dict.
    """
    token_level_data: list[dict[str, Any]] = []
    for gen_idx in range(n_gen_analyzed):
        abs_idx = prompt_len + gen_idx
        row = generation_rows[gen_idx] if gen_idx < len(generation_rows) else {}
        layer_proj: dict[str, float | None] = {}
        for li in selected_layers:
            proj_list = projections.get(li)
            if proj_list is not None and abs_idx < len(proj_list):
                val = proj_list[abs_idx]
                layer_proj[str(li)] = float(val) if isinstance(val, (int, float)) else None
            else:
                layer_proj[str(li)] = None
        token_level_data.append({
            "generated_token_index": gen_idx,
            "absolute_token_index": abs_idx,
            "token_id": row.get("token_id"),
            "token_text": row.get("decoded_single_token"),
            "is_special_token": row.get("is_special_token"),
            "role_or_part": row.get("role_or_part"),
            "layer_projections": layer_proj,
        })
    return token_level_data


def _build_per_example_artifact(
    *,
    prompt_id: str,
    source_artifact_path: str,
    artifact: dict[str, Any],
    token_level_data: list[dict[str, Any]],
    selected_layers: list[int],
    n_gen_full: int,
    n_gen_analyzed: int,
    model_name: str,
    direction_path: str,
    warnings: list[str],
) -> dict[str, Any]:
    sr = artifact.get("strongreject_result") or {}
    sj = artifact.get("source_judge") or {}
    return {
        "artifact_version": ARTIFACT_VERSION,
        "prompt_id": prompt_id,
        "source_artifact_path": source_artifact_path,
        "model_name_or_path": model_name,
        "refusal_direction_path": direction_path,
        "prompt_token_count": artifact.get("prompt_token_count"),
        "generation_token_count": n_gen_full,
        "analyzed_token_count": n_gen_analyzed,
        "qwen_run_success": artifact.get("qwen_run_success"),
        "strongreject_score": sr.get("strongreject_score"),
        "judge_score": sj.get("judge_score"),
        "selected_layers": selected_layers,
        "thinking_segmentation_status": artifact.get("thinking_segmentation_status"),
        "warnings": warnings,
        "token_level_data": token_level_data,
        "created_utc": _utc_now(),
    }


def _emit_token_level_rows(
    *,
    output_path: Path,
    prompt_id: str,
    token_level_data: list[dict[str, Any]],
    artifact: dict[str, Any],
    selected_layers: list[int],
) -> None:
    """Append flat (prompt_id × gen_tok_idx × layer) rows to token_level_metrics.jsonl."""
    sr = artifact.get("strongreject_result") or {}
    sj = artifact.get("source_judge") or {}
    n_gen_full = artifact.get("generation_token_count", 0)
    qwen_success = artifact.get("qwen_run_success")
    sr_score = sr.get("strongreject_score")

    for tok in token_level_data:
        for li in selected_layers:
            row = {
                "prompt_id": prompt_id,
                "generated_token_index": tok["generated_token_index"],
                "absolute_token_index": tok["absolute_token_index"],
                "layer": li,
                "token_id": tok["token_id"],
                "token_text": tok["token_text"],
                "is_special_token": tok["is_special_token"],
                "role_or_part": tok["role_or_part"],
                "refusal_projection": tok["layer_projections"].get(str(li)),
                "qwen_run_success": qwen_success,
                "strongreject_score": sr_score,
                "judge_score": sj.get("judge_score"),
                "generation_length": n_gen_full,
                "distance_from_prompt_end": tok["generated_token_index"],
            }
            append_jsonl(output_path, row)


# ---------------------------------------------------------------------------
# Plotting
# ---------------------------------------------------------------------------

def _plot_example(
    *,
    prompt_id: str,
    token_level_data: list[dict[str, Any]],
    selected_layers: list[int],
    plots_dir: Path,
    max_layers_plotted: int = 8,
) -> None:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return

    if not token_level_data:
        return

    # Pick a representative subset of layers evenly spaced
    step = max(1, len(selected_layers) // max_layers_plotted)
    plot_layers = selected_layers[::step]

    x = [tok["generated_token_index"] for tok in token_level_data]
    fig, ax = plt.subplots(figsize=(12, 4))
    for li in plot_layers:
        y = [tok["layer_projections"].get(str(li)) for tok in token_level_data]
        y_clean = [v if v is not None else float("nan") for v in y]
        ax.plot(x, y_clean, label=f"layer {li}", linewidth=0.8, alpha=0.8)

    ax.set_xlabel("Generated token index")
    ax.set_ylabel("Refusal direction projection")
    ax.set_title(f"Refusal projection over generation\n{prompt_id[:80]}", fontsize=9)
    ax.legend(fontsize=7, ncol=2)
    ax.axhline(0, color="black", linewidth=0.5, linestyle="--")
    fig.tight_layout()

    safe_id = _safe_filename(prompt_id)
    out_path = plots_dir / f"refusal_proj_{safe_id}.png"
    plots_dir.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=100)
    plt.close(fig)


def _plot_aggregate(
    *,
    per_prompt_rows: list[dict[str, Any]],
    all_token_data: list[tuple[dict[str, Any], list[dict[str, Any]]]],
    selected_layers: list[int],
    plots_dir: Path,
    layer_for_agg: int | None = None,
) -> None:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import collections
    except ImportError:
        return

    if not all_token_data or layer_for_agg is None:
        return

    # Group by qwen_run_success label
    by_label: dict[str, list[list[float | None]]] = collections.defaultdict(list)
    for artifact_meta, tok_data in all_token_data:
        label = str(artifact_meta.get("qwen_run_success"))
        proj_series = [tok["layer_projections"].get(str(layer_for_agg)) for tok in tok_data]
        if proj_series:
            by_label[label].append(proj_series)

    if not by_label:
        return

    fig, ax = plt.subplots(figsize=(12, 4))
    colors = {"True": "tab:red", "False": "tab:blue", "unknown": "tab:gray"}
    for label, series_list in by_label.items():
        max_len = max(len(s) for s in series_list)
        # Compute mean per position
        means: list[float] = []
        for pos in range(max_len):
            vals = [s[pos] for s in series_list if pos < len(s) and s[pos] is not None]
            means.append(sum(vals) / len(vals) if vals else float("nan"))
        ax.plot(range(max_len), means, label=f"success={label} (n={len(series_list)})",
                color=colors.get(label), linewidth=1.5)

    ax.set_xlabel("Generated token index")
    ax.set_ylabel(f"Mean refusal projection (layer {layer_for_agg})")
    ax.set_title(f"Aggregate refusal projection — layer {layer_for_agg}")
    ax.legend()
    ax.axhline(0, color="black", linewidth=0.5, linestyle="--")
    fig.tight_layout()
    plots_dir.mkdir(parents=True, exist_ok=True)
    fig.savefig(plots_dir / f"refusal_proj_aggregate_layer{layer_for_agg}.png", dpi=100)
    plt.close(fig)


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _git_commit() -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True, text=True, timeout=5,
        )
        return result.stdout.strip() if result.returncode == 0 else None
    except Exception:
        return None


def _resolve_layers(layers_arg: str, model: Any) -> list[int]:
    n = len(model.model.layers)
    if layers_arg.strip().lower() == "all":
        return list(range(n))
    result = []
    for part in layers_arg.split(","):
        part = part.strip()
        if not part:
            continue
        val = int(part)
        if val < 0:
            val = n + val
        if 0 <= val < n:
            result.append(val)
        else:
            raise ValueError(f"Layer index {val} out of range for model with {n} layers")
    return sorted(set(result))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Stage 4 token-level dynamics analysis. "
            "Reads Stage 6 Qwen3-14B token trace artifacts and computes "
            "refusal-direction projection per generated token per layer."
        )
    )
    parser.add_argument(
        "--stage6-input", required=True,
        help="Directory of Stage 6 trace JSON files, or a single JSON file.",
    )
    parser.add_argument(
        "--output-dir", required=True,
        help="Output directory for all artifacts.",
    )
    parser.add_argument(
        "--model-name-or-path", default=DEFAULT_MODEL,
        help=f"HuggingFace model name/path. Default: {DEFAULT_MODEL}",
    )
    parser.add_argument(
        "--refusal-direction-path", default=DEFAULT_DIRECTION_DIR,
        help=(
            "Path to directory containing direction.pt and selected_direction.json. "
            f"Default: {DEFAULT_DIRECTION_DIR}"
        ),
    )
    parser.add_argument(
        "--layers", default="all",
        help='Comma-separated layer indices or "all". Default: all layers.',
    )
    parser.add_argument(
        "--max-examples", type=int, default=None,
        help="Limit number of examples processed.",
    )
    parser.add_argument(
        "--max-new-tokens-to-analyze", type=int, default=None,
        help="Max generated tokens analyzed per example. Default: all.",
    )
    parser.add_argument(
        "--smoke", action="store_true",
        help=(
            f"Smoke-run mode: sets --max-examples {DEFAULT_MAX_EXAMPLES_SMOKE} "
            f"and --max-new-tokens-to-analyze {DEFAULT_MAX_NEW_TOKENS_SMOKE} "
            "unless those flags are explicitly provided."
        ),
    )
    parser.add_argument(
        "--resume", action="store_true",
        help="Skip examples whose per-example output JSON already exists.",
    )
    parser.add_argument(
        "--device", default="auto",
        help="Device for model (auto/cuda/cpu). Default: auto.",
    )
    parser.add_argument(
        "--dtype", default="bfloat16",
        help="Torch dtype (bfloat16/float16/float32/auto). Default: bfloat16.",
    )
    parser.add_argument(
        "--allow-provisional-direction", action="store_true",
        help="Allow Stage 4A1 provisional directions (smoke/debug only).",
    )
    parser.add_argument(
        "--plot", action="store_true", default=True,
        help="Generate plots (default: true when matplotlib is available).",
    )
    parser.add_argument(
        "--no-plot", action="store_false", dest="plot",
        help="Disable plot generation.",
    )
    parser.add_argument(
        "--run-name", default=None,
        help="Human-readable run label. Default: token_dynamics_<timestamp>.",
    )
    parser.add_argument(
        "--span-metadata-file", default=None,
        help=(
            "Optional path to a JSON file with span metadata per example "
            "(for future attention-based metrics). Not yet implemented; "
            "a warning is stored in the manifest when absent."
        ),
    )
    return parser


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def run(args: argparse.Namespace) -> None:
    # Apply smoke defaults
    if args.smoke:
        if args.max_examples is None:
            args.max_examples = DEFAULT_MAX_EXAMPLES_SMOKE
        if args.max_new_tokens_to_analyze is None:
            args.max_new_tokens_to_analyze = DEFAULT_MAX_NEW_TOKENS_SMOKE

    run_name = args.run_name or f"token_dynamics_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
    output_dir = Path(args.output_dir)
    per_example_dir = output_dir / "per_example"
    plots_dir = output_dir / "plots"
    output_dir.mkdir(parents=True, exist_ok=True)
    per_example_dir.mkdir(parents=True, exist_ok=True)

    progress_path = output_dir / "progress.jsonl"
    per_prompt_path = output_dir / "per_prompt_metrics.jsonl"
    token_level_path = output_dir / "token_level_metrics.jsonl"
    manifest_path = output_dir / "manifest.json"

    log_progress(STAGE_NAME, "Loading model", model=args.model_name_or_path)
    qwen = load_qwen3_model(
        args.model_name_or_path,
        require_cuda=True,
        log_device_placement=True,
    )
    model = qwen.model
    n_model_layers = len(model.model.layers)

    log_progress(STAGE_NAME, "Loading refusal direction", path=args.refusal_direction_path)
    loaded_dir = load_direction(
        args.refusal_direction_path,
        allow_provisional_direction=args.allow_provisional_direction,
    )
    direction = loaded_dir.direction.float()
    direction = direction / direction.norm()
    direction_meta = loaded_dir.metadata
    direction_layer = direction_meta.get("layer")

    log_progress(STAGE_NAME, "Resolving layers")
    selected_layers = _resolve_layers(args.layers, model)
    log_progress(STAGE_NAME, f"Selected {len(selected_layers)} layers", layers=selected_layers[:5])

    add_hooks = _import_add_hooks()

    log_progress(STAGE_NAME, "Collecting Stage 6 trace files", path=args.stage6_input)
    stage6_input = Path(args.stage6_input)
    if not stage6_input.exists():
        raise FileNotFoundError(f"--stage6-input does not exist: {stage6_input}")
    trace_files = _collect_trace_files(stage6_input)
    if not trace_files:
        raise ValueError(f"No Stage 6 trace JSON files found in: {stage6_input}")
    log_progress(STAGE_NAME, f"Found {len(trace_files)} trace files")

    if args.max_examples is not None:
        trace_files = trace_files[: args.max_examples]
        log_progress(STAGE_NAME, f"Limited to {len(trace_files)} examples by --max-examples")

    # Span metadata note
    span_metadata_warning = None
    if args.span_metadata_file is None:
        span_metadata_warning = (
            "No --span-metadata-file provided; attention-based span metrics not available in this run."
        )

    # Write draft manifest (updated at end with final counts)
    manifest_draft = {
        "artifact_version": ARTIFACT_VERSION,
        "stage": "4_token_dynamics",
        "run_name": run_name,
        "smoke": bool(args.smoke),
        "created_utc": _utc_now(),
        "git_commit": _git_commit(),
        "stage6_input": str(stage6_input),
        "model_name_or_path": args.model_name_or_path,
        "refusal_direction_path": str(args.refusal_direction_path),
        "direction_selection_status": direction_meta.get("selection_status"),
        "direction_layer_from_stage4a2": direction_layer,
        "selected_layers": selected_layers,
        "n_model_layers": n_model_layers,
        "max_examples": args.max_examples,
        "max_new_tokens_to_analyze": args.max_new_tokens_to_analyze,
        "examples_attempted": 0,
        "examples_completed": 0,
        "examples_skipped": 0,
        "examples_failed": 0,
        "tokens_source": "full_prompt_plus_generation_token_ids_from_stage6_artifact",
        "span_metadata_warning": span_metadata_warning,
        "command": " ".join(sys.argv),
        "status": "in_progress",
    }
    atomic_write_json(manifest_path, manifest_draft)

    counters = {"attempted": 0, "completed": 0, "skipped": 0, "failed": 0}
    all_token_data: list[tuple[dict[str, Any], list[dict[str, Any]]]] = []

    for trace_path in trace_files:
        t0 = time.time()
        try:
            artifact = _read_artifact(trace_path)
        except Exception as exc:
            log_progress(STAGE_NAME, f"Failed to read artifact {trace_path}: {exc}")
            counters["failed"] += 1
            continue

        prompt_id = _prompt_id(artifact)
        counters["attempted"] += 1

        # Resume check
        per_example_path = per_example_dir / f"{_safe_filename(prompt_id)}.json"
        if args.resume and per_example_path.exists():
            log_progress(STAGE_NAME, "Skipping (resume)", prompt_id=prompt_id)
            append_jsonl(progress_path, {
                "event": "skipped", "prompt_id": prompt_id,
                "reason": "resume_existing", "utc": _utc_now(),
            })
            counters["skipped"] += 1
            continue

        append_jsonl(progress_path, {
            "event": "started", "prompt_id": prompt_id, "utc": _utc_now(),
        })
        log_progress(STAGE_NAME, "Processing", prompt_id=prompt_id)

        try:
            result = compute_projections_for_example(
                artifact=artifact,
                model=model,
                direction=direction,
                selected_layers=selected_layers,
                max_new_tokens_to_analyze=args.max_new_tokens_to_analyze,
                add_hooks=add_hooks,  # kept in signature for compatibility, unused
            )
        except Exception as exc:
            elapsed = round(time.time() - t0, 3)
            log_progress(STAGE_NAME, f"Error on {prompt_id}: {exc}")
            append_jsonl(progress_path, {
                "event": "failed", "prompt_id": prompt_id,
                "error": str(exc), "error_type": type(exc).__name__,
                "elapsed_seconds": elapsed, "utc": _utc_now(),
            })
            counters["failed"] += 1
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            continue

        token_level_data = _build_token_level_data(
            projections=result["projections"],
            generation_rows=result["generation_rows"],
            selected_layers=selected_layers,
            prompt_len=result["prompt_len"],
            n_gen_analyzed=result["n_gen_analyzed"],
        )

        sr = artifact.get("strongreject_result") or {}
        sj = artifact.get("source_judge") or {}

        # Write per-example JSON (full token × layer grid)
        per_example_artifact = _build_per_example_artifact(
            prompt_id=prompt_id,
            source_artifact_path=str(trace_path),
            artifact=artifact,
            token_level_data=token_level_data,
            selected_layers=selected_layers,
            n_gen_full=result["n_gen_full"],
            n_gen_analyzed=result["n_gen_analyzed"],
            model_name=args.model_name_or_path,
            direction_path=str(args.refusal_direction_path),
            warnings=result["warnings"],
        )
        atomic_write_json(per_example_path, per_example_artifact)

        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        # Append to per_prompt_metrics.jsonl
        append_jsonl(per_prompt_path, make_json_safe({
            "prompt_id": prompt_id,
            "source_artifact_path": str(trace_path),
            "qwen_run_success": artifact.get("qwen_run_success"),
            "judge_score": sj.get("judge_score"),
            "strongreject_score": sr.get("strongreject_score"),
            "prompt_token_count": artifact.get("prompt_token_count"),
            "generation_token_count": result["n_gen_full"],
            "analyzed_generation_token_count": result["n_gen_analyzed"],
            "selected_layers": selected_layers,
            "thinking_segmentation_status": artifact.get("thinking_segmentation_status"),
            "warnings": result["warnings"],
            "completed_utc": _utc_now(),
        }))

        # Append to flat token_level_metrics.jsonl
        _emit_token_level_rows(
            output_path=token_level_path,
            prompt_id=prompt_id,
            token_level_data=token_level_data,
            artifact=artifact,
            selected_layers=selected_layers,
        )

        elapsed = round(time.time() - t0, 3)
        append_jsonl(progress_path, {
            "event": "completed", "prompt_id": prompt_id,
            "elapsed_seconds": elapsed,
            "analyzed_tokens": result["n_gen_analyzed"],
            "warnings": result["warnings"],
            "utc": _utc_now(),
        })
        log_progress(
            STAGE_NAME, "Completed",
            prompt_id=prompt_id, elapsed=elapsed,
            analyzed_tokens=result["n_gen_analyzed"],
        )

        all_token_data.append((per_example_artifact, token_level_data))
        counters["completed"] += 1

        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    # Plots
    if args.plot:
        log_progress(STAGE_NAME, "Generating plots")
        for example_meta, tok_data in all_token_data:
            _plot_example(
                prompt_id=example_meta["prompt_id"],
                token_level_data=tok_data,
                selected_layers=selected_layers,
                plots_dir=plots_dir,
            )
        _plot_aggregate(
            per_prompt_rows=[],
            all_token_data=all_token_data,
            selected_layers=selected_layers,
            plots_dir=plots_dir,
            layer_for_agg=direction_layer if direction_layer in selected_layers else (
                selected_layers[-1] if selected_layers else None
            ),
        )

    # Final manifest
    manifest_final = dict(manifest_draft)
    manifest_final.update({
        "examples_attempted": counters["attempted"],
        "examples_completed": counters["completed"],
        "examples_skipped": counters["skipped"],
        "examples_failed": counters["failed"],
        "finished_utc": _utc_now(),
        "status": "completed",
    })
    atomic_write_json(manifest_path, manifest_final)

    log_progress(
        STAGE_NAME, "Done",
        completed=counters["completed"],
        failed=counters["failed"],
        skipped=counters["skipped"],
        output_dir=str(output_dir),
    )


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
