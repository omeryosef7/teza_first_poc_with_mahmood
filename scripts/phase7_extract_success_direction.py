"""Phase-7 (§11) — extract the attack-SUCCESS direction as a causal intervention vector.

Takes the §9 C∪D residual-stream dataset + StrongREJECT labels and, at a chosen (position, layer),
computes the FULL-DATA Fisher mean-difference direction
    d = mean(hidden | success) − mean(hidden | failure),  d_unit = d/||d||
plus σ = std over all C∪D rows of the projection ⟨hidden, d_unit⟩ — the "natural projection
distribution" scale (§11.1), so an intervention coefficient can be expressed as α·σ (α in std units).

This is the intervention vector for `scripts/phase7_steer_generate.py`: adding +α·σ·d_unit should push
toward the success state (increase ASR / reduce refusal); subtracting should do the reverse (§11.5).

Reuses the phase-6 loaders (`_load_goal`, `_labels_from_scores`, `_rowkey_labels`, `_goal_shards`) — no
new data plumbing. Output layout matches `poc_stage4/direction_loader` (direction.pt +
selected_direction.json) so downstream steering code can consume it, but selection_status is set to a
Phase-7-specific tag (this is a success direction, not a Stage-4A refusal direction).

Usage:
  python scripts/phase7_extract_success_direction.py \
    --conditions C D --position think_content_1 --layer 20 \
    --out-dir outputs/phase7_causal/success_dir__think_content_1__L20
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import numpy as np
import torch

from poc_stage_ae.analyze_early_token_signals import _load_goal, _rowkey_labels, _goal_shards
from scripts.phase6_signal_search import _labels_from_scores


def extract_direction(hidden_dir: Path, model: str, conditions: list[str],
                      labels: dict[str, bool], position: str, layer: int):
    goals = sorted({g for c in conditions for g in _goal_shards(hidden_dir, model, c)})
    if not goals:
        raise SystemExit(f"no goals for conditions {conditions}")

    # Discover position order/index and d_model from the first shard.
    pos_index = None
    succ_rows, fail_rows = [], []
    n_rows_total, n_dropped_nan, n_no_label = 0, 0, 0
    for g in goals:
        for c in conditions:
            if not (hidden_dir / f"{model}_{c}_goal{g}.pt").exists():
                continue
            meta, tensor = _load_goal(hidden_dir, model, c, g)  # tensor [n_rows, n_pos, n_layers, d]
            if pos_index is None:
                pos_order = meta.drop_duplicates("position_name").sort_values("position_offset")
                names = pos_order["position_name"].tolist()
                if position not in names:
                    raise SystemExit(f"position '{position}' not in {names}")
                pos_index = names.index(position)
                # Layer slots: 0=embedding output, 1..B-1 = block outputs, last = post-final-norm.
                # Only 0..B-1 are steerable (input of layers[L] via forward_pre_hook); the last slot
                # is post-norm with no layers[L] to hook. Reject it so the direction can't be
                # extracted for a layer the Phase-7 steerer would crash on.
                n_slots = int(tensor.shape[2])
                if not (0 <= layer < n_slots - 1):
                    raise SystemExit(
                        f"--layer {layer} out of steerable range [0, {n_slots - 2}]; "
                        f"slot {n_slots - 1} is post-final-norm (not a residual-stream input).")
            y = _rowkey_labels(meta, labels)
            t = tensor.to(torch.float32).numpy()
            for i, lab in enumerate(y):
                n_rows_total += 1
                if lab is None:
                    n_no_label += 1
                    continue
                vec = t[i, pos_index, layer, :]
                if not np.isfinite(vec).all():
                    n_dropped_nan += 1
                    continue
                (succ_rows if lab else fail_rows).append(vec)

    succ = np.array(succ_rows)
    fail = np.array(fail_rows)
    if len(succ) < 2 or len(fail) < 2:
        raise SystemExit(f"insufficient labelled rows: success={len(succ)} fail={len(fail)}")

    mu_succ = succ.mean(axis=0)
    mu_fail = fail.mean(axis=0)
    d = mu_succ - mu_fail
    norm = float(np.linalg.norm(d))
    d_unit = d / (norm + 1e-8)

    allrows = np.concatenate([succ, fail], axis=0)
    proj = allrows @ d_unit
    sigma = float(proj.std())
    # In-sample separability sanity check (not out-of-fold; the LOGO AUC lives in the phase-6 report).
    proj_succ = succ @ d_unit
    proj_fail = fail @ d_unit
    meta_out = {
        "selection_status": "phase7_success_direction",
        "conditions": conditions,
        "position_name": position,
        "position_index": int(pos_index),
        "selected_layer": int(layer),
        "d_model": int(d_unit.shape[0]),
        "n_success": int(len(succ)),
        "n_failure": int(len(fail)),
        "raw_diff_norm": norm,
        "projection_sigma": sigma,
        "proj_success_mean": float(proj_succ.mean()),
        "proj_failure_mean": float(proj_fail.mean()),
        "separation_in_sigma": float((proj_succ.mean() - proj_fail.mean()) / (sigma + 1e-8)),
        "n_rows_total": n_rows_total,
        "n_dropped_nan": n_dropped_nan,
        "n_no_label": n_no_label,
        "note": ("d = mean(success) - mean(failure); unit-normalized. Steer with coeff = alpha*sigma. "
                 "Positive alpha pushes toward success (expect ASR up / refusal down)."),
    }
    return torch.tensor(d_unit, dtype=torch.float32), meta_out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", default="outputs/phase5_mechanistic/extraction")
    ap.add_argument("--model", default="qwen3")
    ap.add_argument("--conditions", nargs="+", default=["C", "D"])
    ap.add_argument("--scores", default="outputs/phase5_mechanistic/phase6_scores.jsonl")
    ap.add_argument("--position", required=True)
    ap.add_argument("--layer", type=int, required=True)
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()

    hidden_dir = Path(args.run_dir) / "hidden_states" / "shards"
    labels = _labels_from_scores(Path(args.scores))
    direction, meta = extract_direction(hidden_dir, args.model, args.conditions,
                                        labels, args.position, args.layer)
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    torch.save(direction, out / "direction.pt")
    with open(out / "selected_direction.json", "w") as f:
        json.dump(meta, f, indent=2)
    print(f"[phase7] success direction {args.position} L{args.layer} → {out}")
    print(f"[phase7]   n_success={meta['n_success']} n_failure={meta['n_failure']} "
          f"sigma={meta['projection_sigma']:.3f} separation={meta['separation_in_sigma']:.2f}σ "
          f"(dropped_nan={meta['n_dropped_nan']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
