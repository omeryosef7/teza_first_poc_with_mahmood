from __future__ import annotations

"""
compare_prompt_projections.py — Stage 4 supplementary analysis.

Answers the core CoT-hijacking research question:
  WHERE does a puzzle-attack prompt "land" in the refusal direction subspace,
  relative to harmless and direct-harmful prompts?

For each of 3 prompt types × 3 time points we extract a scalar projection onto
each of the K subspace directions.  A single causal forward pass covers all three
time-points at once (causal attention: `<think>` can't attend to later tokens).

  Prompt types
  ─────────────
  harmless     : benign requests  (refusal_direction/dataset/splits/harmless_train.json)
  direct_harm  : plain harmful    (refusal_direction/dataset/splits/harmful_train.json)
  puzzle_attack: CoT-hijacking    (Stage 6 trace artifacts, full_prompt_plus_generation_token_ids)

  Time points (for Qwen3-14B)
  ────────────────────────────
  startofthink  : <think>   token  (token_id 151667) — first generated token
  endofthink    : </think>  token  (token_id 151668) — after full reasoning chain
  endofresponse : <|im_end|> token (token_id 151645) — after the complete answer

For harmless/direct_harm the model must generate a full trace; we use the same
`model.generate()` path used by extract_refusal_direction_endofthink.py.

For puzzle_attack we reuse the pre-computed Stage 6 sequences — one forward pass.

OUTPUTS  (to --output-dir, default outputs/stage4/qwen3-14b/prompt_type_comparison/)
  projections.csv      one row per (prompt_id, prompt_type, compliance, time_point, layer, rank)
  summary.csv          mean ± std projection per (prompt_type, time_point, layer, rank)
  plots/
    grid_{layer}_{rank}.png   3 rows (time-points) × 3 cols (types) — violin/box plot
    summary_best.png          best (layer, rank) from 4C, all types × time-points
"""

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

import torch


# ---------------------------------------------------------------------------
# Position-finding helpers
# ---------------------------------------------------------------------------

def _find_think_start_pos(
    full_ids: list[int],
    think_start_ids: list[int],
    prompt_token_count: int,
) -> int | None:
    """Return absolute index of the first occurrence of <think> at/after prompt end."""
    n = len(think_start_ids)
    for i in range(prompt_token_count, len(full_ids) - n + 1):
        if full_ids[i: i + n] == think_start_ids:
            return i + n - 1
    return None


def _find_think_end_pos(full_ids: list[int], think_end_ids: list[int]) -> int | None:
    """Return absolute index of last token of first </think> in sequence."""
    n = len(think_end_ids)
    for i in range(len(full_ids) - n + 1):
        if full_ids[i: i + n] == think_end_ids:
            return i + n - 1
    return None


def _find_eos_pos(full_ids: list[int], eos_id: int) -> int | None:
    """Return absolute index of last token, verified to be eos_id."""
    if full_ids and full_ids[-1] == eos_id:
        return len(full_ids) - 1
    return None


# ---------------------------------------------------------------------------
# Core activation capture: one forward pass, three positions
# ---------------------------------------------------------------------------

def capture_at_three_positions(
    model_base: Any,
    full_ids: list[int],
    *,
    startofthink_pos: int,
    endofthink_pos: int,
    endofresponse_pos: int,
    max_seq_len: int = 30000,
    device: Any = None,
) -> dict[str, torch.Tensor] | None:
    """
    Run a single forward pass on full_ids.
    Capture residual-stream activations at the three token positions for all layers.

    Returns dict:
      {"startofthink": Tensor[n_layers, d_model],
       "endofthink":   Tensor[n_layers, d_model],
       "endofresponse": Tensor[n_layers, d_model]}
    or None if the sequence exceeds max_seq_len.
    """
    if len(full_ids) > max_seq_len:
        return None

    layers = model_base.layers
    n_layers = model_base.num_layers
    d_model = model_base.hidden_size

    if device is None:
        try:
            device = model_base.model.get_input_embeddings().weight.device
        except Exception:
            device = next(model_base.model.parameters()).device

    positions = {
        "startofthink": startofthink_pos,
        "endofthink": endofthink_pos,
        "endofresponse": endofresponse_pos,
    }

    # [time_point, n_layers, d_model]
    caches: dict[str, torch.Tensor] = {
        k: torch.zeros((n_layers, d_model), dtype=torch.float32)
        for k in positions
    }

    hooks = []

    def _make_hook(li: int) -> Any:
        def _hook(module: Any, hook_input: Any) -> None:
            act = hook_input[0] if isinstance(hook_input, tuple) else hook_input
            for tp, pos in positions.items():
                caches[tp][li] = act[0, pos].detach().float().cpu()
        return _hook

    for li, layer in enumerate(layers):
        hooks.append(layer.register_forward_pre_hook(_make_hook(li)))

    input_tensor = torch.tensor(full_ids, dtype=torch.long).unsqueeze(0).to(device)
    try:
        with torch.no_grad():
            model_base.model(input_ids=input_tensor, use_cache=False)
    finally:
        for h in hooks:
            h.remove()

    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    return {k: v.clone() for k, v in caches.items()}


# ---------------------------------------------------------------------------
# Load puzzle-attack traces from Stage 6
# ---------------------------------------------------------------------------

def load_puzzle_traces(
    stage6_input: Path,
    *,
    think_start_ids: list[int],
    think_end_ids: list[int],
    eos_id: int,
    max_per_type: int | None = None,
    max_seq_len: int = 30000,
) -> list[dict[str, Any]]:
    """
    Load Stage 6 traces and extract the three positions for each.
    Returns list of dicts:
      {"full_ids": list[int], "startofthink_pos": int, "endofthink_pos": int,
       "endofresponse_pos": int, "compliance": bool | None, "prompt_id": str}
    """
    files = sorted(stage6_input.glob("*.json"))
    records: list[dict[str, Any]] = []

    for path in files:
        if max_per_type is not None and len(records) >= max_per_type:
            break
        try:
            art = json.loads(path.read_text())
        except Exception:
            continue

        # Only eos-terminated traces have a valid endofresponse position
        if art.get("generation_finish_reason") != "eos_token":
            continue

        full_ids = art.get("full_prompt_plus_generation_token_ids")
        if not full_ids or len(full_ids) > max_seq_len:
            continue

        ptc = art.get("prompt_token_count", 0)
        sp = _find_think_start_pos(full_ids, think_start_ids, ptc)
        ep = _find_think_end_pos(full_ids, think_end_ids)
        rp = _find_eos_pos(full_ids, eos_id)

        if sp is None or ep is None or rp is None:
            continue

        compliance = art.get("qwen_run_success")
        prompt_id = art.get("output_json", path.stem)

        records.append({
            "full_ids": full_ids,
            "startofthink_pos": sp,
            "endofthink_pos": ep,
            "endofresponse_pos": rp,
            "compliance": compliance,
            "prompt_id": prompt_id,
        })

    return records


# ---------------------------------------------------------------------------
# Generate full traces for harmless/direct_harm prompts
# ---------------------------------------------------------------------------

def generate_traces_for_prompts(
    model_base: Any,
    prompts: list[str],
    *,
    think_start_ids: list[int],
    think_end_ids: list[int],
    eos_id: int,
    max_generation_tokens: int = 8192,
    max_seq_len: int = 30000,
    progress_enabled: bool = True,
    group_label: str = "prompts",
) -> list[dict[str, Any]]:
    """
    Format each prompt with enable_thinking=True, generate until EOS or max tokens,
    then find the three positions.

    Returns list of dicts (same schema as load_puzzle_traces records, minus compliance).
    """
    try:
        input_device = model_base.model.get_input_embeddings().weight.device
    except Exception:
        input_device = next(model_base.model.parameters()).device

    records: list[dict[str, Any]] = []

    for idx, prompt in enumerate(prompts):
        if progress_enabled:
            print(
                f"  [{group_label}] {idx+1}/{len(prompts)} ...",
                file=sys.stderr, flush=True,
            )

        formatted = model_base.format_prompts([prompt], enable_thinking=True)[0]
        prompt_ids = model_base.tokenizer(
            formatted, return_tensors="pt", padding=False, truncation=False,
        ).input_ids[0].tolist()
        prompt_len = len(prompt_ids)

        input_tensor = torch.tensor(prompt_ids, dtype=torch.long).unsqueeze(0).to(input_device)

        with torch.no_grad():
            out = model_base.model.generate(
                input_tensor,
                max_new_tokens=max_generation_tokens,
                do_sample=False,
                temperature=None,
                top_p=None,
                pad_token_id=model_base.tokenizer.eos_token_id,
            )

        full_ids = out[0].tolist()

        if len(full_ids) > max_seq_len:
            if progress_enabled:
                print(f"  [{group_label}] skipping: seq_len={len(full_ids)} > {max_seq_len}", file=sys.stderr)
            continue

        sp = _find_think_start_pos(full_ids, think_start_ids, prompt_len)
        ep = _find_think_end_pos(full_ids, think_end_ids)
        rp = _find_eos_pos(full_ids, eos_id)

        if sp is None or ep is None or rp is None:
            if progress_enabled:
                print(
                    f"  [{group_label}] skipping: sp={sp} ep={ep} rp={rp} "
                    f"(finish_reason={'eos' if rp is not None else 'max_tokens'})",
                    file=sys.stderr,
                )
            continue

        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        records.append({
            "full_ids": full_ids,
            "startofthink_pos": sp,
            "endofthink_pos": ep,
            "endofresponse_pos": rp,
            "compliance": None,
            "prompt_id": f"{group_label}_{idx}",
        })

    return records


# ---------------------------------------------------------------------------
# Project activations onto subspace
# ---------------------------------------------------------------------------

def project_onto_subspace(
    activations: dict[str, torch.Tensor],
    subspace: torch.Tensor,
    focus_layers: list[int] | None,
) -> list[dict[str, Any]]:
    """
    activations: {"startofthink": [n_layers, d_model], ...}
    subspace:    [K, d_model]
    Returns list of {time_point, layer, rank, projection} rows.
    """
    rows = []
    K = subspace.shape[0]
    for time_point, layer_acts in activations.items():
        n_layers = layer_acts.shape[0]
        for layer in range(n_layers):
            if focus_layers is not None and layer not in focus_layers:
                continue
            act = layer_acts[layer].float()  # [d_model]
            for rank in range(K):
                direction = subspace[rank].float()  # [d_model]
                proj = float(torch.dot(act, direction).item())
                rows.append({
                    "time_point": time_point,
                    "layer": layer,
                    "rank": rank,
                    "projection": proj,
                })
    return rows


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run_comparison(
    *,
    model_name: str,
    model_family: str,
    subspace_dir: Path,
    stage6_input: Path,
    output_dir: Path,
    num_harmless: int,
    num_direct_harm: int,
    max_puzzle: int | None,
    max_generation_tokens: int,
    max_seq_len: int,
    focus_layers: list[int] | None,
    no_progress: bool,
) -> None:
    from poc_stage4.default_prompts import load_prompt_sets
    from poc_stage4.model_family_utils import (
        DEFAULT_MODEL_BY_FAMILY,
        get_thinking_end_token_ids,
        get_thinking_start_token_ids,
        load_model_by_family,
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "plots").mkdir(exist_ok=True)
    progress = not no_progress

    # Load subspace
    subspace_pt = subspace_dir / "direction_subspace.pt"
    if not subspace_pt.exists():
        raise FileNotFoundError(f"Subspace not found: {subspace_pt}")
    subspace = torch.load(subspace_pt, map_location="cpu", weights_only=True).float()
    K = subspace.shape[0]

    meta_path = subspace_dir / "direction_subspace_metadata.json"
    subspace_meta = json.loads(meta_path.read_text()) if meta_path.exists() else {}
    print(f"[compare_projections] Loaded subspace shape={list(subspace.shape)} from {subspace_dir.name}")

    if focus_layers is None and subspace_meta:
        focus_layers = [d["layer"] for d in subspace_meta.get("directions", [])]
        print(f"[compare_projections] Auto-detected focus_layers from metadata: {focus_layers}")

    # Load model
    print(f"[compare_projections] Loading model {model_name} ...", file=sys.stderr, flush=True)
    model_base = load_model_by_family(model_name, model_family)

    think_start_ids = get_thinking_start_token_ids(model_base.tokenizer, model_family)
    think_end_ids   = get_thinking_end_token_ids(model_base.tokenizer, model_family)
    eos_id = model_base.tokenizer.eos_token_id

    print(f"[compare_projections] think_start_ids={think_start_ids} think_end_ids={think_end_ids} eos_id={eos_id}")

    # ── Puzzle attack traces (pre-computed) ──
    print("[compare_projections] Loading puzzle attack traces from Stage 6 ...", file=sys.stderr, flush=True)
    puzzle_records = load_puzzle_traces(
        stage6_input,
        think_start_ids=think_start_ids,
        think_end_ids=think_end_ids,
        eos_id=eos_id,
        max_per_type=max_puzzle,
        max_seq_len=max_seq_len,
    )
    print(f"[compare_projections] Loaded {len(puzzle_records)} puzzle traces")

    # ── Harmless and direct_harm prompts (need generation) ──
    harmful_prompts, harmless_prompts, _ = load_prompt_sets(
        num_harmful=num_direct_harm,
        num_harmless=num_harmless,
        seed=42,
    )

    print(f"[compare_projections] Generating harmless traces ({len(harmless_prompts)} prompts) ...", file=sys.stderr, flush=True)
    harmless_records = generate_traces_for_prompts(
        model_base, harmless_prompts,
        think_start_ids=think_start_ids,
        think_end_ids=think_end_ids,
        eos_id=eos_id,
        max_generation_tokens=max_generation_tokens,
        max_seq_len=max_seq_len,
        progress_enabled=progress,
        group_label="harmless",
    )
    print(f"[compare_projections] Got {len(harmless_records)} harmless traces")

    print(f"[compare_projections] Generating direct_harm traces ({len(harmful_prompts)} prompts) ...", file=sys.stderr, flush=True)
    direct_harm_records = generate_traces_for_prompts(
        model_base, harmful_prompts,
        think_start_ids=think_start_ids,
        think_end_ids=think_end_ids,
        eos_id=eos_id,
        max_generation_tokens=max_generation_tokens,
        max_seq_len=max_seq_len,
        progress_enabled=progress,
        group_label="direct_harm",
    )
    print(f"[compare_projections] Got {len(direct_harm_records)} direct_harm traces")

    # ── Capture activations and project ──
    all_rows: list[dict[str, Any]] = []

    prompt_type_records = [
        ("harmless",     harmless_records),
        ("direct_harm",  direct_harm_records),
        ("puzzle_attack", puzzle_records),
    ]

    for prompt_type, records in prompt_type_records:
        print(f"[compare_projections] Projecting {len(records)} {prompt_type} traces ...", file=sys.stderr, flush=True)
        for rec in records:
            acts = capture_at_three_positions(
                model_base,
                rec["full_ids"],
                startofthink_pos=rec["startofthink_pos"],
                endofthink_pos=rec["endofthink_pos"],
                endofresponse_pos=rec["endofresponse_pos"],
                max_seq_len=max_seq_len,
            )
            if acts is None:
                continue

            proj_rows = project_onto_subspace(acts, subspace, focus_layers)
            for pr in proj_rows:
                all_rows.append({
                    "prompt_id": rec["prompt_id"],
                    "prompt_type": prompt_type,
                    "compliance": rec.get("compliance"),
                    **pr,
                })

    # ── Write CSV ──
    if not all_rows:
        print("[compare_projections] WARNING: no rows collected.", file=sys.stderr)
        return

    csv_path = output_dir / "projections.csv"
    fieldnames = ["prompt_id", "prompt_type", "compliance", "time_point", "layer", "rank", "projection"]
    with csv_path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_rows)
    print(f"[compare_projections] Wrote {len(all_rows)} rows to {csv_path}")

    # ── Summary CSV (mean ± std per group) ──
    _write_summary_csv(all_rows, output_dir / "summary.csv")

    # ── Plots ──
    _make_plots(all_rows, output_dir / "plots", subspace_meta=subspace_meta)


def _write_summary_csv(rows: list[dict], path: Path) -> None:
    import statistics
    from collections import defaultdict
    groups: dict[tuple, list[float]] = defaultdict(list)
    for r in rows:
        key = (r["prompt_type"], r["time_point"], r["layer"], r["rank"])
        groups[key].append(r["projection"])

    with path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["prompt_type", "time_point", "layer", "rank", "n", "mean", "std"])
        writer.writeheader()
        for (pt, tp, layer, rank), vals in sorted(groups.items()):
            writer.writerow({
                "prompt_type": pt, "time_point": tp, "layer": layer, "rank": rank,
                "n": len(vals),
                "mean": round(statistics.mean(vals), 6),
                "std": round(statistics.stdev(vals), 6) if len(vals) > 1 else 0.0,
            })
    print(f"[compare_projections] Wrote summary to {path}")


def _make_plots(rows: list[dict], plot_dir: Path, *, subspace_meta: dict) -> None:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import statistics
        from collections import defaultdict
    except ImportError:
        print("[compare_projections] matplotlib not available — skipping plots", file=sys.stderr)
        return

    TIME_POINTS = ["startofthink", "endofthink", "endofresponse"]
    PROMPT_TYPES = ["harmless", "direct_harm", "puzzle_attack"]
    COLORS = {"harmless": "#2196F3", "direct_harm": "#F44336", "puzzle_attack": "#FF9800"}

    # Find distinct (layer, rank) combos
    combos = sorted({(r["layer"], r["rank"]) for r in rows})

    for layer, rank in combos:
        fig, axes = plt.subplots(1, len(TIME_POINTS), figsize=(14, 5), sharey=True)
        fig.suptitle(f"Subspace projection — layer {layer}, rank {rank}", fontsize=12)

        for col, tp in enumerate(TIME_POINTS):
            ax = axes[col]
            data_by_type = {pt: [] for pt in PROMPT_TYPES}
            for r in rows:
                if r["time_point"] == tp and r["layer"] == layer and r["rank"] == rank:
                    data_by_type[r["prompt_type"]].append(r["projection"])

            positions_box = range(len(PROMPT_TYPES))
            box_data = [data_by_type[pt] for pt in PROMPT_TYPES]
            bp = ax.boxplot(box_data, positions=list(positions_box), patch_artist=True,
                            medianprops={"color": "black", "linewidth": 2})
            for patch, pt in zip(bp["boxes"], PROMPT_TYPES):
                patch.set_facecolor(COLORS[pt])
                patch.set_alpha(0.7)

            ax.set_title(tp, fontsize=10)
            ax.set_xticks(list(positions_box))
            ax.set_xticklabels([pt.replace("_", "\n") for pt in PROMPT_TYPES], fontsize=8)
            if col == 0:
                ax.set_ylabel("projection")
            ax.axhline(0, color="gray", linestyle="--", linewidth=0.8)

        plt.tight_layout()
        out_path = plot_dir / f"projection_L{layer}_R{rank}.png"
        plt.savefig(out_path, dpi=120, bbox_inches="tight")
        plt.close(fig)

    print(f"[compare_projections] Saved {len(combos)} plots to {plot_dir}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Compare refusal subspace projections across 3 prompt types "
            "(harmless / direct_harm / puzzle_attack) at 3 time points "
            "(startofthink / endofthink / endofresponse)."
        )
    )
    parser.add_argument(
        "--subspace-dir",
        default="outputs/stage4/qwen3-14b/direction_subspace_behavioral",
        help="Directory containing direction_subspace.pt. Default: behavioral subspace.",
    )
    parser.add_argument(
        "--stage6-input",
        default="outputs/stage6/all_traces_full_1_11",
        help="Stage 6 trace artifacts (puzzle prompts).",
    )
    parser.add_argument(
        "--output-dir",
        default="outputs/stage4/qwen3-14b/prompt_type_comparison",
    )
    parser.add_argument("--model-family", default="qwen3", choices=["qwen3", "gemma4"])
    parser.add_argument("--model-name", default=None)
    parser.add_argument(
        "--num-harmless", type=int, default=50,
        help="Number of harmless prompts to generate traces for. Default: 50.",
    )
    parser.add_argument(
        "--num-direct-harm", type=int, default=50,
        help="Number of direct_harm prompts to generate traces for. Default: 50.",
    )
    parser.add_argument(
        "--max-puzzle", type=int, default=None,
        help="Max puzzle traces to load from Stage 6. Default: all.",
    )
    parser.add_argument(
        "--max-generation-tokens", type=int, default=8192,
        help="Max new tokens when generating harmless/direct_harm traces. Default: 8192.",
    )
    parser.add_argument(
        "--max-seq-len", type=int, default=30000,
        help="Skip sequences longer than this. Default: 30000.",
    )
    parser.add_argument(
        "--focus-layers", default=None,
        help="Comma-separated layer indices to include. Default: auto from subspace metadata.",
    )
    parser.add_argument("--no-progress", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()

    from poc_stage4.model_family_utils import DEFAULT_MODEL_BY_FAMILY
    model_family = args.model_family
    model_name = args.model_name or DEFAULT_MODEL_BY_FAMILY[model_family]

    focus_layers: list[int] | None = None
    if args.focus_layers:
        focus_layers = [int(x.strip()) for x in args.focus_layers.split(",") if x.strip()]

    try:
        run_comparison(
            model_name=model_name,
            model_family=model_family,
            subspace_dir=Path(args.subspace_dir),
            stage6_input=Path(args.stage6_input),
            output_dir=Path(args.output_dir),
            num_harmless=args.num_harmless,
            num_direct_harm=args.num_direct_harm,
            max_puzzle=args.max_puzzle,
            max_generation_tokens=args.max_generation_tokens,
            max_seq_len=args.max_seq_len,
            focus_layers=focus_layers,
            no_progress=args.no_progress,
        )
    except Exception as exc:
        import traceback
        traceback.print_exc()
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
