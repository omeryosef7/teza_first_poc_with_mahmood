"""
Stage 4.7 — Compute selected-layer projection dynamics on replication outputs.

Re-runs a forward pass over the full generated sequence (prompt + generation)
with forward hooks registered at layers 13, 16, 22, 38, 39 only.
Projects residual stream activations onto the provisional Stage 4 direction.

IMPORTANT:
  - Does NOT use output_hidden_states=True (memory-prohibitive for long sequences)
  - Does NOT use multi-GPU splitting
  - Uses allow_provisional_direction=True — direction is diagnostic only
  - Manifest states direction_status = "provisional_projection_diagnostic_only"

Output: outputs/stage4_7/runs/<run_timestamp>/projection_analysis/

Per-generation output fields (thinking-enabled conditions A, D, F):
  first_500_mean_projection
  first_2000_mean_projection
  think_phase_mean_projection
  final_phase_mean_projection
  last_500_think_mean_projection
  normalized_progress_bin_1..10

For condition E (thinking disabled):
  prompt_end_projection
  final_phase_mean_projection

Usage:
  python -m poc_stage4_7.compute_selected_layer_dynamics
      --run-dir outputs/stage4_7/runs/<run_timestamp>
      [--output-dir PATH]
      [--goals 0,1,2,3]
      [--conditions A,D,F,E]
      [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from poc_stage4_5 import common

_DIRECTION_DIR = _REPO_ROOT / "outputs" / "stage4" / "qwen3-14b" / "refusal_direction"
_MODEL = "Qwen/Qwen3-14B"
_MODEL_REVISION = "40c069824f4251a91eefaf281ebe4c544efd3e18"

# Layers to analyze
SELECTED_LAYERS = [13, 16, 22, 38, 39]
PRIMARY_LAYER = 22
EXPLORATORY_LAYERS = [13, 16, 38, 39]
N_BINS = 10


def _load_direction():
    from poc_stage4.direction_loader import load_direction
    loaded = load_direction(_DIRECTION_DIR, allow_provisional_direction=True)
    return loaded.direction, loaded.metadata


def _load_model_cpu_safe():
    """Load tokenizer + model on single GPU."""
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    tok = AutoTokenizer.from_pretrained(
        _MODEL, revision=_MODEL_REVISION, trust_remote_code=True
    )
    model = AutoModelForCausalLM.from_pretrained(
        _MODEL,
        revision=_MODEL_REVISION,
        torch_dtype=torch.bfloat16,
        device_map="auto",
        trust_remote_code=True,
    )
    model.eval()
    return tok, model


def _compute_projections_for_sequence(
    token_ids: list[int],
    model,
    tokenizer,
    direction,
    think_token_count: int,
    has_thinking: bool,
) -> dict[str, Any]:
    """
    Run forward pass with hooks, compute token-level projection onto direction.
    Returns dict of projection summary statistics.
    """
    import torch

    device = next(model.parameters()).device
    direction_vec = direction.to(device=device, dtype=torch.float32)
    if direction_vec.ndim == 1:
        direction_vec = direction_vec / (direction_vec.norm() + 1e-8)

    input_ids = torch.tensor([token_ids], dtype=torch.long, device=device)
    n_tokens = len(token_ids)

    # Store per-layer, per-token projections
    captured: dict[int, list[float]] = {layer: [] for layer in SELECTED_LAYERS}

    hooks = []

    def _make_hook(layer_idx: int):
        def hook(module, inputs, output):
            # output[0] shape: (batch, seq_len, hidden)
            if isinstance(output, (tuple, list)):
                hidden = output[0]
            else:
                hidden = output
            # Project each token
            h = hidden[0].to(torch.float32)  # (seq_len, hidden)
            proj = (h @ direction_vec).detach().cpu().tolist()
            captured[layer_idx].extend(proj)
        return hook

    # Register hooks on selected layers
    try:
        for layer_idx in SELECTED_LAYERS:
            layer = model.model.layers[layer_idx]
            h = layer.register_forward_hook(_make_hook(layer_idx))
            hooks.append(h)

        with torch.no_grad():
            _ = model(input_ids=input_ids, use_cache=False)

    finally:
        for h in hooks:
            h.remove()

    # Compute summary statistics for each layer
    result: dict[str, Any] = {}

    for layer_idx, proj_list in captured.items():
        if not proj_list:
            continue
        layer_tag = f"layer{layer_idx}"

        # Determine phase boundaries
        # For thinking-enabled: [0..think_phase_end] = think, [think_phase_end+1..] = final
        # think_token_count is the number of thinking tokens
        # prompt occupies the first (n_tokens - generation_tokens) positions,
        # but we're projecting over the ENTIRE sequence (prompt + generation)
        # For simplicity, use think_token_count as the approximation of
        # the thinking-phase length in generation tokens.

        n_gen = len(proj_list) - 0  # full sequence (prompt + gen projected together)
        n_total = len(proj_list)

        if has_thinking and think_token_count > 0:
            # Approximate: thinking phase = last think_token_count tokens before final
            # Final phase = last (n_total - think_token_count) tokens (at least 1)
            think_end = min(n_total - 1, think_token_count)
            think_proj = proj_list[:think_end]
            final_proj = proj_list[think_end:]
        else:
            think_proj = []
            final_proj = proj_list

        # First N tokens
        first_500 = proj_list[:500]
        first_2000 = proj_list[:2000]
        last_500_think = think_proj[-500:] if think_proj else []

        def _mean(lst):
            return sum(lst) / len(lst) if lst else None

        if has_thinking:
            result[f"{layer_tag}_first_500_mean_projection"] = _mean(first_500)
            result[f"{layer_tag}_first_2000_mean_projection"] = _mean(first_2000)
            result[f"{layer_tag}_think_phase_mean_projection"] = _mean(think_proj)
            result[f"{layer_tag}_final_phase_mean_projection"] = _mean(final_proj)
            result[f"{layer_tag}_last_500_think_mean_projection"] = _mean(last_500_think)

            # Normalized progress bins (10 bins over the full sequence)
            bin_size = max(1, n_total // N_BINS)
            for b in range(N_BINS):
                start = b * bin_size
                end = (b + 1) * bin_size if b < N_BINS - 1 else n_total
                result[f"{layer_tag}_normalized_bin_{b+1}"] = _mean(proj_list[start:end])
        else:
            # Condition E: no thinking
            result[f"{layer_tag}_prompt_end_projection"] = _mean(proj_list[:min(10, n_total)])
            result[f"{layer_tag}_final_phase_mean_projection"] = _mean(final_proj)

    return result


def analyze_run(
    run_dir: Path,
    output_dir: Path | None,
    goals_filter: list[int] | None,
    conditions_filter: list[str] | None,
    dry_run: bool,
) -> None:
    summary_path = run_dir / "run_summary.jsonl"
    if not summary_path.exists():
        print(f"ERROR: run_summary.jsonl not found in {run_dir}")
        sys.exit(1)

    rows = [json.loads(l) for l in summary_path.read_text().splitlines() if l.strip()]
    print(f"Loaded {len(rows)} rows from {summary_path}")

    if goals_filter:
        rows = [r for r in rows if int(r.get("goal_index", -1)) in goals_filter]
    if conditions_filter:
        rows = [r for r in rows if r.get("condition") in conditions_filter]

    out_dir = output_dir or (run_dir / "projection_analysis")
    out_dir.mkdir(parents=True, exist_ok=True)

    # Load direction
    print("Loading provisional direction ...")
    direction, dir_meta = _load_direction()
    print(f"  layer={dir_meta.get('layer')} status={dir_meta.get('selection_status')}")

    if dry_run:
        print("[DRY RUN] — would process {} rows".format(len(rows)))
        return

    print("Loading model ...")
    tokenizer, model = _load_model_cpu_safe()
    print("  model loaded")

    all_projection_results: list[dict] = []

    for row in rows:
        run_id = row.get("run_id", "")
        artifact_path = Path(row.get("artifact_path", ""))
        if not artifact_path.exists():
            print(f"  SKIP {run_id}: artifact not found at {artifact_path}")
            continue

        artifact = json.loads(artifact_path.read_text())
        token_ids = artifact.get("generation_token_ids")
        if not token_ids:
            print(f"  SKIP {run_id}: no generation_token_ids in artifact")
            continue

        # Reconstruct full sequence: encode prompt + generation
        user_msg = None
        # We can't re-tokenize the user message (not stored for safety)
        # Instead, use the generation token count as approximate thinking boundary
        think_token_count = int(row.get("think_token_count") or 0)
        has_thinking = row.get("condition") != "E"
        cond = row.get("condition")

        print(f"  Processing {run_id} (cond={cond} think_tok={think_token_count}) ...")

        try:
            proj = _compute_projections_for_sequence(
                token_ids=list(token_ids),
                model=model,
                tokenizer=tokenizer,
                direction=direction,
                think_token_count=think_token_count,
                has_thinking=has_thinking,
            )

            result_row = {
                "run_id": run_id,
                "source_example_id": row.get("source_example_id"),
                "condition": cond,
                "goal_index": row.get("goal_index"),
                "selection_stratum": row.get("selection_stratum", ""),
                "think_token_count": think_token_count,
                "strongreject_score": row.get("strongreject_score"),
                "sr_success": row.get("sr_success"),
                "finish_reason": row.get("finish_reason"),
                "direction_layer": dir_meta.get("layer"),
                "direction_status": "provisional_projection_diagnostic_only",
                **proj,
            }
            all_projection_results.append(result_row)

            # Write per-example
            per_ex_path = out_dir / f"{run_id}_projection.json"
            with open(per_ex_path, "w", encoding="utf-8") as f:
                json.dump(result_row, f, indent=2)

            print(f"    L22 first_500={proj.get('layer22_first_500_mean_projection', 'N/A'):.3f}" if proj.get("layer22_first_500_mean_projection") else f"    done (E condition)")

        except Exception as exc:
            print(f"  ERROR {run_id}: {exc}")

    # Write combined summary
    summary_out = out_dir / "projection_summary.jsonl"
    with open(summary_out, "w", encoding="utf-8") as f:
        for r in all_projection_results:
            f.write(json.dumps(r, default=str) + "\n")
    print(f"\nWrote {summary_out} ({len(all_projection_results)} rows)")

    # Write manifest
    manifest = {
        "created_utc": common.utc_now(),
        "run_dir": str(run_dir),
        "n_rows": len(all_projection_results),
        "selected_layers": SELECTED_LAYERS,
        "primary_layer": PRIMARY_LAYER,
        "exploratory_layers": EXPLORATORY_LAYERS,
        "direction_path": str(_DIRECTION_DIR / "direction.pt"),
        "direction_status": "provisional_projection_diagnostic_only",
        "direction_layer": dir_meta.get("layer"),
        "output_hidden_states_used": False,
        "multi_gpu_used": False,
        "note": (
            "Layer 22 is the pre-specified primary layer. "
            "Layers 13, 16, 38, 39 are exploratory comparison layers. "
            "All results are diagnostic only — do not claim causal refusal suppression."
        ),
    }
    with open(out_dir / "projection_manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    print(f"Wrote {out_dir / 'projection_manifest.json'}")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Compute Stage 4.7 selected-layer projection dynamics.")
    p.add_argument("--run-dir", type=Path, required=True)
    p.add_argument("--output-dir", type=Path, default=None)
    p.add_argument("--goals", type=str, default=None)
    p.add_argument("--conditions", type=str, default=None)
    p.add_argument("--dry-run", action="store_true", default=False)
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    goals = [int(g) for g in args.goals.split(",")] if args.goals else None
    conditions = [c for c in args.conditions.split(",")] if args.conditions else None
    analyze_run(
        run_dir=args.run_dir,
        output_dir=args.output_dir,
        goals_filter=goals,
        conditions_filter=conditions,
        dry_run=args.dry_run,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
