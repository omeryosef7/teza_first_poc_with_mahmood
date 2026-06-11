"""
Stage 4.8 — Compute layer projections on repeated-generation outputs.

Mirrors poc_stage4_7/compute_selected_layer_dynamics.py exactly, adapted for
Stage 4.8 run layout (60 rows, seed column, conditions A/D/F only).

Projects generation token residual streams at layers 13, 16, 22, 38, 39 onto
the provisional direction. Primary window: first 500 thinking tokens.

IMPORTANT:
  - Direction is diagnostic only — do NOT claim causal mechanism
  - Only conditions A, D, F computed (all have thinking enabled)
  - Resume-safe: skips run_ids already in projection_summary.jsonl

Usage:
  python -m poc_stage4_8.compute_repeated_generation_representations
      --run-dir outputs/stage4_8/runs/<timestamp>
      [--output-dir PATH]
      [--goals 0,1,2,3]
      [--conditions A,D,F]
      [--force]
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

SELECTED_LAYERS = [13, 16, 22, 38, 39]
PRIMARY_LAYER = 22
N_BINS = 10


def _load_direction():
    from poc_stage4.direction_loader import load_direction
    loaded = load_direction(_DIRECTION_DIR, allow_provisional_direction=True)
    return loaded.direction, loaded.metadata


def _load_model():
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


def _compute_projections(
    token_ids: list[int],
    model: Any,
    direction: Any,
    think_token_count: int,
) -> dict[str, Any]:
    import torch

    device = next(model.parameters()).device
    direction_vec = direction.to(device=device, dtype=torch.float32)
    if direction_vec.ndim == 1:
        direction_vec = direction_vec / (direction_vec.norm() + 1e-8)

    input_ids = torch.tensor([token_ids], dtype=torch.long, device=device)
    n_total = len(token_ids)

    captured: dict[int, list[float]] = {layer: [] for layer in SELECTED_LAYERS}
    hooks = []

    def _make_hook(layer_idx: int):
        def hook(module, inputs, output):
            hidden = output[0] if isinstance(output, (tuple, list)) else output
            h = hidden[0].to(torch.float32)
            proj = (h @ direction_vec).detach().cpu().tolist()
            captured[layer_idx].extend(proj)
        return hook

    try:
        for layer_idx in SELECTED_LAYERS:
            h = model.model.layers[layer_idx].register_forward_hook(_make_hook(layer_idx))
            hooks.append(h)
        with torch.no_grad():
            _ = model(input_ids=input_ids, use_cache=False)
    finally:
        for h in hooks:
            h.remove()

    result: dict[str, Any] = {}
    for layer_idx, proj_list in captured.items():
        if not proj_list:
            continue
        tag = f"layer{layer_idx}"

        think_end = min(n_total - 1, think_token_count) if think_token_count > 0 else 0
        think_proj = proj_list[:think_end] if think_end > 0 else []
        final_proj = proj_list[think_end:]

        def _mean(lst):
            return sum(lst) / len(lst) if lst else None

        result[f"{tag}_first_500_mean_projection"] = _mean(proj_list[:500])
        result[f"{tag}_first_2000_mean_projection"] = _mean(proj_list[:2000])
        result[f"{tag}_think_phase_mean_projection"] = _mean(think_proj)
        result[f"{tag}_final_phase_mean_projection"] = _mean(final_proj)
        result[f"{tag}_last_500_think_mean_projection"] = _mean(think_proj[-500:]) if think_proj else None

        bin_size = max(1, n_total // N_BINS)
        for b in range(N_BINS):
            start = b * bin_size
            end = (b + 1) * bin_size if b < N_BINS - 1 else n_total
            result[f"{tag}_normalized_bin_{b+1}"] = _mean(proj_list[start:end])

    return result


def _load_done_ids(summary_path: Path) -> set[str]:
    if not summary_path.exists():
        return set()
    done = set()
    for line in summary_path.read_text().splitlines():
        line = line.strip()
        if line:
            try:
                done.add(json.loads(line).get("run_id", ""))
            except json.JSONDecodeError:
                pass
    return done


def run_representations(
    run_dir: Path,
    output_dir: Path | None,
    goals_filter: list[int] | None,
    conditions_filter: list[str] | None,
    force: bool,
    dry_run: bool,
) -> None:
    summary_path = run_dir / "run_summary.jsonl"
    if not summary_path.exists():
        print(f"ERROR: run_summary.jsonl not found at {summary_path}")
        sys.exit(1)

    rows = [json.loads(l) for l in summary_path.read_text().splitlines() if l.strip()]
    print(f"Loaded {len(rows)} rows")

    # Only process completed, thinking-enabled rows
    rows = [r for r in rows if r.get("finish_reason") == "eos_token"]
    rows = [r for r in rows if r.get("condition") in ("A", "D", "F")]
    rows = [r for r in rows if r.get("thinking_segmentation_status") == "parsed_from_think_tags"]
    if goals_filter:
        rows = [r for r in rows if int(r.get("goal_index", -1)) in goals_filter]
    if conditions_filter:
        rows = [r for r in rows if r.get("condition") in conditions_filter]

    print(f"Eligible rows (eos_token + A/D/F + parsed_from_think_tags): {len(rows)}")

    out_dir = output_dir or (run_dir / "representations")
    out_dir.mkdir(parents=True, exist_ok=True)

    proj_summary_path = out_dir / "projection_summary.jsonl"
    done_ids = set() if force else _load_done_ids(proj_summary_path)
    if done_ids:
        print(f"  Resuming: {len(done_ids)} already done")

    if dry_run:
        for r in rows:
            status = "SKIP" if r.get("run_id") in done_ids else "RUN"
            print(f"  [{status}] {r['run_id']} seed={r.get('seed')}")
        return

    print("Loading provisional direction ...")
    direction, dir_meta = _load_direction()
    print(f"  layer={dir_meta.get('layer')} status={dir_meta.get('selection_status')}")

    print("Loading model ...")
    tokenizer, model = _load_model()
    print("  model loaded")

    n_done = n_skipped = n_failed = 0

    for row in rows:
        run_id = row.get("run_id", "")
        if run_id in done_ids and not force:
            n_skipped += 1
            continue

        artifact_path = Path(row.get("artifact_path", ""))
        if not artifact_path.exists():
            # Try to reconstruct path
            artifact_path = run_dir / "per_example" / f"{run_id}.json"
        if not artifact_path.exists():
            print(f"  SKIP {run_id}: artifact not found")
            n_failed += 1
            continue

        artifact = json.loads(artifact_path.read_text())
        token_ids = artifact.get("generation_token_ids")
        if not token_ids:
            print(f"  SKIP {run_id}: no generation_token_ids")
            n_failed += 1
            continue

        think_token_count = int(row.get("think_token_count") or 0)
        seed = row.get("seed")
        cond = row.get("condition")
        print(f"  Processing {run_id} (cond={cond} seed={seed} think={think_token_count} gen_len={len(token_ids)}) ...")

        try:
            proj = _compute_projections(
                token_ids=list(token_ids),
                model=model,
                direction=direction,
                think_token_count=think_token_count,
            )

            result_row = {
                "run_id": run_id,
                "source_example_id": row.get("source_example_id"),
                "condition": cond,
                "goal_index": row.get("goal_index"),
                "seed": seed,
                "selection_stratum": row.get("selection_stratum", ""),
                "think_token_count": think_token_count,
                "strongreject_score": row.get("strongreject_score"),
                "sr_success": row.get("sr_success"),
                "finish_reason": row.get("finish_reason"),
                "direction_layer": dir_meta.get("layer"),
                "direction_status": "provisional_projection_diagnostic_only",
                **proj,
            }

            # Write per-example
            per_ex_path = out_dir / f"{run_id}_projection.json"
            with open(per_ex_path, "w") as f:
                json.dump(result_row, f, indent=2)

            # Append to summary
            with open(proj_summary_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(result_row, default=str) + "\n")

            l22 = proj.get("layer22_first_500_mean_projection")
            print(f"    L22_first500={l22:.3f}" if l22 is not None else "    L22 N/A")
            n_done += 1

        except Exception as exc:
            print(f"  ERROR {run_id}: {exc}")
            n_failed += 1

    # Write manifest
    manifest = {
        "created_utc": common.utc_now(),
        "run_dir": str(run_dir),
        "n_done": n_done,
        "n_skipped": n_skipped,
        "n_failed": n_failed,
        "selected_layers": SELECTED_LAYERS,
        "primary_layer": PRIMARY_LAYER,
        "direction_status": "provisional_projection_diagnostic_only",
        "direction_layer": dir_meta.get("layer") if not dry_run else None,
        "note": (
            "Layer 22 is pre-specified primary. Layers 13, 16, 38, 39 are exploratory. "
            "All projections are diagnostic only — no causal claims."
        ),
    }
    with open(out_dir / "representations_manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"\nDone. {n_done} computed, {n_skipped} skipped, {n_failed} failed.")
    print(f"Output: {out_dir}")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Compute Stage 4.8 layer projections.")
    p.add_argument("--run-dir", type=Path, required=True)
    p.add_argument("--output-dir", type=Path, default=None)
    p.add_argument("--goals", type=str, default=None)
    p.add_argument("--conditions", type=str, default=None)
    p.add_argument("--force", action="store_true", default=False)
    p.add_argument("--dry-run", action="store_true", default=False)
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    run_representations(
        run_dir=args.run_dir,
        output_dir=args.output_dir,
        goals_filter=[int(g) for g in args.goals.split(",")] if args.goals else None,
        conditions_filter=[c.strip() for c in args.conditions.split(",")] if args.conditions else None,
        force=args.force,
        dry_run=args.dry_run,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
