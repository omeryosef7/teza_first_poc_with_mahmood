from __future__ import annotations

"""
Stage 4 token-level dynamics analysis — multi-direction subspace variant.

DIFFERENCE FROM analyze_stage6_token_dynamics.py (single direction):
  analyze_stage6_token_dynamics.py: projects each generated token onto ONE direction vector
  This script:                      projects each generated token onto K direction vectors

Loads direction_subspace.pt (shape [K, d_model]) produced by select_direction_subspace.py.
For each generated token, computes K projections per layer (one per subspace direction).

This lets you see whether the K directions decay at different rates during CoT hijacking
and which direction is most sensitive to the attack's "refusal dilution" effect.

WHAT CHANGED vs. the single-direction version:
  - Input: direction_subspace.pt [K, d_model] instead of direction.pt [d_model]
  - Hook: projects onto all K directions, stores list-of-K instead of scalar
  - Output schema:
      layer_projections: {layer_idx: [proj_rank0, proj_rank1, ...]}   (list of K floats)
  - Plots: K lines per per-example plot; K lines on aggregate plot

INPUTS:
  --stage6-input          Stage 6 trace JSON directory (same as single-direction script)
  --direction-subspace-path  Directory containing direction_subspace.pt + direction_subspace_metadata.json

OUTPUTS (to --output-dir):
  per_example/<id>.json         per-token × per-layer × per-rank projections
  per_prompt_metrics.jsonl      one row per example with generation stats
  token_level_metrics.jsonl     flat (prompt_id, gen_tok_idx, layer, rank, refusal_projection)
  plots/                        per-example and aggregate plots showing K direction traces
  manifest.json                 run metadata
"""

import argparse
import json
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import torch

from poc_stage4.model_family_utils import load_model_by_family
from poc_stage4.run_state import append_jsonl, atomic_write_json, log_progress
from poc_stage4.schemas import make_json_safe

ARTIFACT_VERSION = "poc_stage4_token_dynamics_subspace_v1"
STAGE_NAME = "stage4_dyn_sub"
DEFAULT_SUBSPACE_DIR = "outputs/stage4/qwen3-14b/direction_subspace"


# ---------------------------------------------------------------------------
# Subspace loading
# ---------------------------------------------------------------------------

def load_direction_subspace(
    subspace_dir: str | Path,
) -> tuple[torch.Tensor, dict[str, Any]]:
    """Load direction_subspace.pt and its metadata. Returns (subspace, metadata)."""
    base = Path(subspace_dir)
    pt_path = base / "direction_subspace.pt"
    meta_path = base / "direction_subspace_metadata.json"

    if not pt_path.exists():
        raise FileNotFoundError(f"Missing direction_subspace.pt: {pt_path}")
    if not meta_path.exists():
        raise FileNotFoundError(f"Missing direction_subspace_metadata.json: {meta_path}")

    subspace = torch.load(pt_path, map_location="cpu")
    if subspace.ndim != 2:
        raise ValueError(
            f"direction_subspace.pt must have shape [K, d_model], got {list(subspace.shape)}"
        )

    with meta_path.open("r", encoding="utf-8") as fh:
        metadata = json.load(fh)

    return subspace.float(), metadata


# ---------------------------------------------------------------------------
# Hook: project onto K directions simultaneously
# ---------------------------------------------------------------------------

def make_subspace_projection_hook(
    layer_idx: int,
    subspace_cpu: torch.Tensor,
    projections_store: dict[int, list[list[float]]],
):
    """
    Forward pre-hook: captures residual stream input at layer_idx and projects
    all sequence positions onto each of the K subspace directions.

    Stores projections_store[layer_idx] as a list of K lists:
        [[proj_rank0_token0, proj_rank0_token1, ...],
         [proj_rank1_token0, proj_rank1_token1, ...],
         ...]
    """
    def hook_fn(module: Any, hook_input: Any) -> None:
        act = hook_input[0] if isinstance(hook_input, tuple) else hook_input
        # act: [1, seq_len, d_model] on GPU
        dirs = subspace_cpu.to(device=act.device, dtype=torch.float32)
        # proj: [seq_len, K]
        proj = (act[0].float() @ dirs.T).detach().cpu()
        # Store as list of K lists (one list per direction rank)
        k = proj.shape[1]
        projections_store[layer_idx] = [proj[:, r].tolist() for r in range(k)]
        del dirs

    return hook_fn


# ---------------------------------------------------------------------------
# Input handling (same as single-direction version)
# ---------------------------------------------------------------------------

def _collect_trace_files(stage6_input: Path) -> list[Path]:
    if stage6_input.is_file():
        return [stage6_input]
    files = sorted(stage6_input.glob("*.json"))
    return [f for f in files if not f.name.startswith("batch_summary")]


def _read_artifact(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _prompt_id(artifact: dict[str, Any], path: Path) -> str:
    sel = artifact.get("selected_example") or {}
    return str(sel.get("example_id") or path.stem)


def _safe_filename(prompt_id: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_.\-]+", "_", prompt_id).strip("_.-")
    return (cleaned or "example")[:200]


def _model_input_device(model: Any) -> torch.device:
    try:
        return model.get_input_embeddings().weight.device
    except Exception:
        return next(model.parameters()).device


# ---------------------------------------------------------------------------
# Projection computation
# ---------------------------------------------------------------------------

def compute_subspace_projections_for_example(
    *,
    artifact: dict[str, Any],
    model: Any,
    subspace: torch.Tensor,
    selected_layers: list[int],
    max_new_tokens_to_analyze: int | None,
) -> dict[str, Any]:
    """
    Run a forward pass on the full sequence and return per-layer subspace projections.

    projections: {layer_idx: [[float x seq_len] x K]}
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

    seq_len_needed = prompt_len + n_gen_analyzed
    input_ids_list = full_ids[:seq_len_needed]
    if len(input_ids_list) < seq_len_needed:
        warnings.append(
            f"Sequence shorter than expected: got {len(input_ids_list)}, needed {seq_len_needed}"
        )
        n_gen_analyzed = max(0, len(input_ids_list) - prompt_len)

    input_ids = torch.tensor(input_ids_list, dtype=torch.long).unsqueeze(0)
    input_device = _model_input_device(model)
    subspace_cpu = subspace.cpu()

    projections_store: dict[int, list[list[float]]] = {}
    transformer_layers = model.model.layers
    n_model_layers = len(transformer_layers)

    handles = []
    for li in selected_layers:
        if li >= n_model_layers:
            warnings.append(f"Layer {li} out of range (model has {n_model_layers} layers)")
            continue
        handles.append(transformer_layers[li].register_forward_pre_hook(
            make_subspace_projection_hook(li, subspace_cpu, projections_store)
        ))

    try:
        with torch.no_grad():
            model(input_ids=input_ids.to(input_device))
    finally:
        for h in handles:
            h.remove()
        del handles

    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    generation_rows = [
        row for row in token_table if row.get("segment") == "generation"
    ]
    if len(generation_rows) != n_gen_full:
        warnings.append(
            f"token_table generation rows ({len(generation_rows)}) != generation_token_count ({n_gen_full})"
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
    projections: dict[int, list[list[float]]],
    generation_rows: list[dict[str, Any]],
    selected_layers: list[int],
    prompt_len: int,
    n_gen_analyzed: int,
    k: int,
) -> list[dict[str, Any]]:
    """
    One entry per generated token; layer_projections maps layer → list of K floats.
    """
    token_level_data: list[dict[str, Any]] = []
    for gen_idx in range(n_gen_analyzed):
        abs_idx = prompt_len + gen_idx
        row = generation_rows[gen_idx] if gen_idx < len(generation_rows) else {}
        layer_proj: dict[str, list[float | None]] = {}
        for li in selected_layers:
            per_rank = projections.get(li)
            if per_rank is not None:
                vals: list[float | None] = []
                for rank_proj in per_rank:
                    if abs_idx < len(rank_proj):
                        v = rank_proj[abs_idx]
                        vals.append(float(v) if isinstance(v, (int, float)) else None)
                    else:
                        vals.append(None)
                layer_proj[str(li)] = vals
            else:
                layer_proj[str(li)] = [None] * k
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


def _emit_token_level_rows(
    *,
    output_path: Path,
    prompt_id: str,
    token_level_data: list[dict[str, Any]],
    artifact: dict[str, Any],
    selected_layers: list[int],
) -> None:
    """Flat rows: (prompt_id, gen_tok_idx, layer, rank, refusal_projection)."""
    sr = artifact.get("strongreject_result") or {}
    sj = artifact.get("source_judge") or {}
    n_gen_full = artifact.get("generation_token_count", 0)
    qwen_success = artifact.get("qwen_run_success")
    sr_score = sr.get("strongreject_score")

    for tok in token_level_data:
        for li in selected_layers:
            proj_list = tok["layer_projections"].get(str(li), [])
            for rank, proj_val in enumerate(proj_list):
                row = {
                    "prompt_id": prompt_id,
                    "generated_token_index": tok["generated_token_index"],
                    "absolute_token_index": tok["absolute_token_index"],
                    "layer": li,
                    "subspace_rank": rank,
                    "token_id": tok["token_id"],
                    "token_text": tok["token_text"],
                    "is_special_token": tok["is_special_token"],
                    "role_or_part": tok["role_or_part"],
                    "refusal_projection": proj_val,
                    "qwen_run_success": qwen_success,
                    "strongreject_score": sr_score,
                    "judge_score": sj.get("judge_score"),
                    "generation_length": n_gen_full,
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
    subspace_metadata: dict[str, Any],
    plots_dir: Path,
    max_layers_plotted: int = 4,
) -> None:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return

    if not token_level_data:
        return

    k = subspace_metadata.get("k_actual", 1)
    direction_meta = subspace_metadata.get("directions", [])

    step = max(1, len(selected_layers) // max_layers_plotted)
    plot_layers = selected_layers[::step]

    x = [tok["generated_token_index"] for tok in token_level_data]
    n_plots = len(plot_layers)
    fig, axes = plt.subplots(n_plots, 1, figsize=(12, 3 * n_plots), squeeze=False)

    for ax_idx, li in enumerate(plot_layers):
        ax = axes[ax_idx][0]
        for rank in range(k):
            y = []
            for tok in token_level_data:
                proj_list = tok["layer_projections"].get(str(li), [])
                val = proj_list[rank] if rank < len(proj_list) else None
                y.append(float(val) if val is not None else float("nan"))
            layer_info = (
                f"layer={direction_meta[rank]['layer']}" if rank < len(direction_meta) else f"rank {rank}"
            )
            ax.plot(x, y, label=f"rank {rank} ({layer_info})", linewidth=0.8, alpha=0.85)
        ax.set_xlabel("Generated token index")
        ax.set_ylabel("Projection")
        ax.set_title(f"Layer {li} — refusal subspace projections", fontsize=9)
        ax.axhline(0, color="black", linewidth=0.5, linestyle="--")
        ax.legend(fontsize=7, ncol=2)

    fig.suptitle(f"Subspace projections\n{prompt_id[:80]}", fontsize=9)
    fig.tight_layout()

    safe_id = _safe_filename(prompt_id)
    plots_dir.mkdir(parents=True, exist_ok=True)
    fig.savefig(plots_dir / f"subspace_proj_{safe_id}.png", dpi=100)
    plt.close(fig)


def _plot_aggregate(
    *,
    all_token_data: list[tuple[dict[str, Any], list[dict[str, Any]]]],
    selected_layers: list[int],
    subspace_metadata: dict[str, Any],
    plots_dir: Path,
) -> None:
    try:
        import collections
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return

    if not all_token_data or not selected_layers:
        return

    k = subspace_metadata.get("k_actual", 1)
    # Use the layer from the highest-ranked direction, or first layer
    direction_meta = subspace_metadata.get("directions", [])
    ref_layer = direction_meta[0]["layer"] if direction_meta else selected_layers[0]
    if ref_layer not in selected_layers:
        ref_layer = selected_layers[0]

    by_label: dict[str, list[list[list[float | None]]]] = collections.defaultdict(list)
    for artifact_meta, tok_data in all_token_data:
        label = str(artifact_meta.get("qwen_run_success"))
        series = []
        for rank in range(k):
            rank_series = [
                (tok["layer_projections"].get(str(ref_layer)) or [None] * k)[rank]
                for tok in tok_data
            ]
            series.append(rank_series)
        by_label[label].append(series)

    colors = {"True": "tab:red", "False": "tab:blue", "unknown": "tab:gray"}
    fig, axes = plt.subplots(k, 1, figsize=(12, 3 * k), squeeze=False)

    for rank in range(k):
        ax = axes[rank][0]
        for label, all_series in by_label.items():
            rank_series_list = [s[rank] for s in all_series if rank < len(s)]
            if not rank_series_list:
                continue
            max_len = max(len(s) for s in rank_series_list)
            means = []
            for pos in range(max_len):
                vals = [s[pos] for s in rank_series_list if pos < len(s) and s[pos] is not None]
                means.append(sum(vals) / len(vals) if vals else float("nan"))
            ax.plot(
                range(max_len), means,
                label=f"success={label} (n={len(rank_series_list)})",
                color=colors.get(label), linewidth=1.5,
            )
        layer_label = direction_meta[rank]["layer"] if rank < len(direction_meta) else "?"
        ax.set_title(f"Subspace rank {rank} — layer {layer_label} (aggregate, ref_layer={ref_layer})", fontsize=9)
        ax.set_xlabel("Generated token index")
        ax.set_ylabel("Mean projection")
        ax.axhline(0, color="black", linewidth=0.5, linestyle="--")
        ax.legend(fontsize=8)

    fig.tight_layout()
    plots_dir.mkdir(parents=True, exist_ok=True)
    fig.savefig(plots_dir / f"subspace_proj_aggregate_layer{ref_layer}.png", dpi=100)
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
            "Stage 4 token-level dynamics — subspace variant. "
            "Reads Stage 6 trace artifacts and computes K refusal-direction projections "
            "per generated token per layer."
        )
    )
    parser.add_argument("--stage6-input", required=True,
                        help="Directory of Stage 6 trace JSONs or a single JSON file.")
    parser.add_argument("--output-dir", required=True,
                        help="Output directory for all artifacts.")
    parser.add_argument(
        "--model-family", default="qwen3", choices=["qwen3", "gemma4"],
        help="Model family. Controls the HF loader. Default: qwen3.",
    )
    parser.add_argument("--model-name-or-path", default=None,
                        help="HF model name or path. Default: inferred from --model-family.")
    parser.add_argument("--direction-subspace-path", default=DEFAULT_SUBSPACE_DIR,
                        help=("Path to directory containing direction_subspace.pt "
                              f"and direction_subspace_metadata.json. Default: {DEFAULT_SUBSPACE_DIR}"))
    parser.add_argument("--layers", default="all",
                        help='Comma-separated layer indices or "all". Default: all.')
    parser.add_argument("--max-examples", type=int, default=None)
    parser.add_argument("--max-new-tokens-to-analyze", type=int, default=None)
    parser.add_argument("--smoke", action="store_true",
                        help="Smoke mode: max 5 examples × 128 tokens.")
    parser.add_argument("--resume", action="store_true",
                        help="Skip examples whose per-example output JSON already exists.")
    parser.add_argument("--emit-token-level-jsonl", action="store_true", default=False,
                        help="Write flat token_level_metrics.jsonl (~240 MB/example, 52 GB/variant). "
                             "Off by default — per_example/ JSON files contain the same data and are "
                             "used by analyze_subspace_dynamics_stats.py.")
    parser.add_argument("--plot", action="store_true", default=True)
    parser.add_argument("--no-plot", action="store_false", dest="plot")
    parser.add_argument("--run-name", default=None)
    return parser


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def run(args: argparse.Namespace) -> None:
    from poc_stage4.model_family_utils import DEFAULT_MODEL_BY_FAMILY
    if args.model_name_or_path is None:
        args.model_name_or_path = DEFAULT_MODEL_BY_FAMILY[args.model_family]

    if args.smoke:
        if args.max_examples is None:
            args.max_examples = 5
        if args.max_new_tokens_to_analyze is None:
            args.max_new_tokens_to_analyze = 128

    run_name = args.run_name or f"token_dynamics_subspace_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
    output_dir = Path(args.output_dir)
    per_example_dir = output_dir / "per_example"
    plots_dir = output_dir / "plots"
    output_dir.mkdir(parents=True, exist_ok=True)
    per_example_dir.mkdir(parents=True, exist_ok=True)

    progress_path = output_dir / "progress.jsonl"
    per_prompt_path = output_dir / "per_prompt_metrics.jsonl"
    token_level_path = output_dir / "token_level_metrics.jsonl"
    manifest_path = output_dir / "manifest.json"

    log_progress(STAGE_NAME, "Loading direction subspace", path=args.direction_subspace_path)
    subspace, subspace_meta = load_direction_subspace(args.direction_subspace_path)
    k = int(subspace.shape[0])
    log_progress(STAGE_NAME, "Loaded subspace", shape=list(subspace.shape), k=k)

    log_progress(STAGE_NAME, "Loading model", model=args.model_name_or_path,
                 model_family=args.model_family)
    qwen = load_model_by_family(
        args.model_name_or_path, args.model_family,
        require_cuda=True, log_device_placement=True,
    )
    model = qwen.model
    n_model_layers = len(model.model.layers)

    selected_layers = _resolve_layers(args.layers, model)
    log_progress(STAGE_NAME, f"Selected {len(selected_layers)} layers", layers=selected_layers[:5])

    stage6_input = Path(args.stage6_input)
    if not stage6_input.exists():
        raise FileNotFoundError(f"--stage6-input does not exist: {stage6_input}")
    trace_files = _collect_trace_files(stage6_input)
    if not trace_files:
        raise ValueError(f"No Stage 6 trace JSON files in: {stage6_input}")
    log_progress(STAGE_NAME, f"Found {len(trace_files)} trace files")

    if args.max_examples is not None:
        trace_files = trace_files[: args.max_examples]

    manifest_draft = {
        "artifact_version": ARTIFACT_VERSION,
        "stage": "4_token_dynamics_subspace",
        "run_name": run_name,
        "smoke": bool(args.smoke),
        "created_utc": _utc_now(),
        "git_commit": _git_commit(),
        "stage6_input": str(stage6_input),
        "model_name_or_path": args.model_name_or_path,
        "model_family": args.model_family,
        "direction_subspace_path": str(args.direction_subspace_path),
        "subspace_k": k,
        "subspace_shape": list(subspace.shape),
        "subspace_directions": subspace_meta.get("directions", []),
        "selected_layers": selected_layers,
        "n_model_layers": n_model_layers,
        "max_examples": args.max_examples,
        "max_new_tokens_to_analyze": args.max_new_tokens_to_analyze,
        "examples_attempted": 0,
        "examples_completed": 0,
        "examples_skipped": 0,
        "examples_failed": 0,
        "status": "in_progress",
        "command": " ".join(sys.argv),
    }
    atomic_write_json(manifest_path, manifest_draft)

    counters = {"attempted": 0, "completed": 0, "skipped": 0, "failed": 0}
    all_token_data: list[tuple[dict[str, Any], list[dict[str, Any]]]] = []

    for trace_path in trace_files:
        t0 = time.time()
        try:
            artifact = _read_artifact(trace_path)
        except Exception as exc:
            log_progress(STAGE_NAME, f"Failed to read {trace_path}: {exc}")
            counters["failed"] += 1
            continue

        prompt_id = _prompt_id(artifact, trace_path)
        counters["attempted"] += 1

        per_example_path = per_example_dir / f"{_safe_filename(prompt_id)}.json"
        if args.resume and per_example_path.exists():
            log_progress(STAGE_NAME, "Skipping (resume)", prompt_id=prompt_id)
            append_jsonl(progress_path, {
                "event": "skipped", "prompt_id": prompt_id, "reason": "resume_existing",
                "utc": _utc_now(),
            })
            counters["skipped"] += 1
            continue

        append_jsonl(progress_path, {"event": "started", "prompt_id": prompt_id, "utc": _utc_now()})
        log_progress(STAGE_NAME, "Processing", prompt_id=prompt_id)

        try:
            result = compute_subspace_projections_for_example(
                artifact=artifact,
                model=model,
                subspace=subspace,
                selected_layers=selected_layers,
                max_new_tokens_to_analyze=args.max_new_tokens_to_analyze,
            )
        except Exception as exc:
            elapsed = round(time.time() - t0, 3)
            log_progress(STAGE_NAME, f"Error on {prompt_id}: {exc}")
            append_jsonl(progress_path, {
                "event": "failed", "prompt_id": prompt_id,
                "error": str(exc), "elapsed_seconds": elapsed, "utc": _utc_now(),
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
            k=k,
        )

        sr = artifact.get("strongreject_result") or {}
        sj = artifact.get("source_judge") or {}

        per_example_artifact = {
            "artifact_version": ARTIFACT_VERSION,
            "prompt_id": prompt_id,
            "source_artifact_path": str(trace_path),
            "model_name_or_path": args.model_name_or_path,
            "direction_subspace_path": str(args.direction_subspace_path),
            "subspace_k": k,
            "subspace_directions": subspace_meta.get("directions", []),
            "prompt_token_count": artifact.get("prompt_token_count"),
            "generation_token_count": result["n_gen_full"],
            "analyzed_token_count": result["n_gen_analyzed"],
            "qwen_run_success": artifact.get("qwen_run_success"),
            "strongreject_score": sr.get("strongreject_score"),
            "judge_score": sj.get("judge_score"),
            "selected_layers": selected_layers,
            "warnings": result["warnings"],
            "token_level_data": token_level_data,
            "created_utc": _utc_now(),
        }
        atomic_write_json(per_example_path, per_example_artifact)

        append_jsonl(per_prompt_path, make_json_safe({
            "prompt_id": prompt_id,
            "source_artifact_path": str(trace_path),
            "qwen_run_success": artifact.get("qwen_run_success"),
            "judge_score": sj.get("judge_score"),
            "strongreject_score": sr.get("strongreject_score"),
            "prompt_token_count": artifact.get("prompt_token_count"),
            "generation_token_count": result["n_gen_full"],
            "analyzed_generation_token_count": result["n_gen_analyzed"],
            "subspace_k": k,
            "selected_layers": selected_layers,
            "warnings": result["warnings"],
            "completed_utc": _utc_now(),
        }))

        if args.emit_token_level_jsonl:
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
            "elapsed_seconds": elapsed, "analyzed_tokens": result["n_gen_analyzed"],
            "utc": _utc_now(),
        })
        log_progress(STAGE_NAME, "Completed", prompt_id=prompt_id, elapsed=elapsed)

        all_token_data.append((per_example_artifact, token_level_data))
        counters["completed"] += 1
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    if args.plot:
        log_progress(STAGE_NAME, "Generating plots")
        for ex_meta, tok_data in all_token_data:
            _plot_example(
                prompt_id=ex_meta["prompt_id"],
                token_level_data=tok_data,
                selected_layers=selected_layers,
                subspace_metadata=subspace_meta,
                plots_dir=plots_dir,
            )
        _plot_aggregate(
            all_token_data=all_token_data,
            selected_layers=selected_layers,
            subspace_metadata=subspace_meta,
            plots_dir=plots_dir,
        )

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
        completed=counters["completed"], failed=counters["failed"],
        output_dir=str(output_dir),
    )


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
