#!/usr/bin/env python3
"""
Phase-6 (§10) predictive-signal search on the §9 mechanistic dataset.

Finds the earliest layer/position where **attack success** is linearly separable from **failure** in
Qwen3-14B residual streams, using grouped **leave-one-goal-out** (LOGO) out-of-fold AUC (§10.3) — the
same Fisher mean-difference method as `poc_stage_ae/analyze_early_token_signals.py`, whose helpers we
REUSE. The only extension: pool several §9 fine-conditions into one coarse group so the success/failure
split (which spans two condition-shards in our dataset) can be analysed together, e.g.:
  --conditions F G   → suffix success (F=fail, G=success shards, labelled per-row by StrongREJECT)
  --conditions C D   → the core §10 ATTACK success direction
  --conditions A B   → clean compliance (control)

Labels come from a scores file (row_key → strongreject_is_success), so the split is label-driven, not
shard-driven. Output: per (position, layer) LOGO AUC CSV, sorted; prints the shallowest strong signal.
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
import pandas as pd
import torch

from poc_stage_ae.analyze_early_token_signals import (
    _load_goal, _rowkey_labels, _auc_from_scores, _goal_shards,
)


def _labels_from_scores(scores_path: Path) -> dict[str, bool]:
    labels: dict[str, bool] = {}
    with open(scores_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            if r.get("generation_status") != "ok":
                continue
            v = r.get("strongreject_is_success")
            if v is not None:
                labels[r["row_key"]] = bool(v)
    return labels


def _rowkey_order(meta: pd.DataFrame) -> list[str]:
    """Row-key list in the SAME order `_rowkey_labels` uses (row_offset), so it aligns
    positionally with the tensor rows — needed to emit per-row projections for §10.4."""
    return meta.drop_duplicates("row_key").sort_values("row_offset")["row_key"].tolist()


def analyze_group(hidden_dir: Path, model: str, conditions: list[str],
                  labels: dict[str, bool], emit_projections: list | None = None) -> pd.DataFrame:
    # Union of goals across the pooled conditions; per goal, concat rows over conditions present.
    goals = sorted({g for c in conditions for g in _goal_shards(hidden_dir, model, c)})
    if not goals:
        return pd.DataFrame()

    per_goal_tensor, per_goal_y, per_goal_rk = {}, {}, {}
    position_names, n_layers = None, None
    for g in goals:
        tensors, ys, rks = [], [], []
        for c in conditions:
            pt = hidden_dir / f"{model}_{c}_goal{g}.pt"
            if not pt.exists():
                continue
            meta, tensor = _load_goal(hidden_dir, model, c, g)
            tensors.append(tensor)
            ys.append(_rowkey_labels(meta, labels))
            rks.extend(_rowkey_order(meta))
            if position_names is None:
                pos_order = meta.drop_duplicates("position_name").sort_values("position_offset")
                position_names = pos_order["position_name"].tolist()
                n_layers = int(meta["layer_count"].iloc[0])
        if not tensors:
            continue
        per_goal_tensor[g] = torch.cat(tensors, dim=0)
        per_goal_y[g] = np.concatenate(ys)
        per_goal_rk[g] = rks
    goals = [g for g in goals if g in per_goal_tensor]
    if not per_goal_tensor:  # no shards for any requested condition → empty result, not a crash
        return pd.DataFrame()

    d_model = next(iter(per_goal_tensor.values())).shape[-1]
    n_pos = len(position_names)
    # Some captured positions carry NaN placeholder vectors: answer_content_1/2/3 are
    # non-applicable under enable_thinking=True (all rows), and endofthink is NaN when a
    # generation never closed </think> (finish_reason=max_new_tokens). Mask them PER POSITION
    # via a finite check so a single NaN row cannot poison that position's Fisher sums, while
    # every other position of that same row still contributes. Counts are per-position for the
    # same reason (a NaN at one position must not drop the row from all positions' LOGO folds).
    sum_pos = {g: np.zeros((n_pos, n_layers, d_model)) for g in goals}
    sum_neg = {g: np.zeros((n_pos, n_layers, d_model)) for g in goals}
    cnt_pos = {g: np.zeros(n_pos, dtype=np.int64) for g in goals}
    cnt_neg = {g: np.zeros(n_pos, dtype=np.int64) for g in goals}
    finite_mask = {}  # g -> [n_rows, n_pos] bool: row i usable at position p
    for g in goals:
        t = per_goal_tensor[g].to(torch.float32).numpy()
        finite = np.isfinite(t).all(axis=(2, 3))  # [n_rows, n_pos]
        finite_mask[g] = finite
        for i, label in enumerate(per_goal_y[g]):
            if label is None:
                continue
            for p in range(n_pos):
                if not finite[i, p]:
                    continue
                (sum_pos if label else sum_neg)[g][p] += t[i, p]
                (cnt_pos if label else cnt_neg)[g][p] += 1

    total_sum_pos, total_sum_neg = sum(sum_pos.values()), sum(sum_neg.values())
    total_cnt_pos, total_cnt_neg = sum(cnt_pos.values()), sum(cnt_neg.values())  # each [n_pos]
    pooled_scores = {(p, l): [] for p in range(n_pos) for l in range(n_layers)}
    pooled_labels = {(p, l): [] for p in range(n_pos) for l in range(n_layers)}

    for g in goals:  # grouped leave-one-goal-out
        tr_pos = total_cnt_pos - cnt_pos[g]  # [n_pos]
        tr_neg = total_cnt_neg - cnt_neg[g]
        t = per_goal_tensor[g].to(torch.float32).numpy()
        y = per_goal_y[g]
        rk = per_goal_rk[g]
        finite = finite_mask[g]
        for p in range(n_pos):
            if tr_pos[p] == 0 or tr_neg[p] == 0:  # position needs both classes in the training fold
                continue
            direction_p = ((total_sum_pos[p] - sum_pos[g][p]) / tr_pos[p]
                           - (total_sum_neg[p] - sum_neg[g][p]) / tr_neg[p])  # [n_layers, d_model]
            for l in range(n_layers):
                dvec = direction_p[l]
                nrm = np.linalg.norm(dvec)
                if nrm == 0 or not np.isfinite(nrm):
                    continue
                proj = t[:, p, l, :] @ (dvec / nrm)
                for i, label in enumerate(y):
                    if label is None or not finite[i, p]:
                        continue
                    pooled_scores[(p, l)].append(proj[i])
                    pooled_labels[(p, l)].append(label)
                    if emit_projections is not None:
                        # Out-of-fold projection per row (goal g held out) → feeds the §10.4
                        # confound control (residualize on prompt length, recompute AUC).
                        emit_projections.append({
                            "position_name": position_names[p], "position_index": p,
                            "layer_index": l, "goal_index": g, "row_key": rk[i],
                            "projection": float(proj[i]), "label": bool(label),
                        })

    recs = []
    for p, pos_name in enumerate(position_names):
        for l in range(n_layers):
            sc = np.array(pooled_scores[(p, l)])
            if len(sc) == 0:
                continue
            auc = _auc_from_scores(sc, np.array(pooled_labels[(p, l)], dtype=object))
            recs.append({"group": "+".join(conditions), "position_name": pos_name,
                         "position_index": p, "layer_index": l,
                         "normalized_depth": l / (n_layers - 1) if n_layers > 1 else 0.0,
                         "n_pooled": len(sc), "logo_auc": auc})
    return pd.DataFrame.from_records(recs)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", default="outputs/phase5_mechanistic/extraction")
    ap.add_argument("--model", default="qwen3")
    ap.add_argument("--conditions", nargs="+", required=True, help="fine conditions to pool, e.g. F G")
    ap.add_argument("--scores", default="outputs/phase5_mechanistic/phase6_scores.jsonl")
    ap.add_argument("--out", required=True)
    ap.add_argument("--emit-projections", default=None,
                    help="optional jsonl path: per-row out-of-fold projections for the §10.4 confound control")
    args = ap.parse_args()

    hidden_dir = Path(args.run_dir) / "hidden_states" / "shards"
    labels = _labels_from_scores(Path(args.scores))
    emit = [] if args.emit_projections else None
    df = analyze_group(hidden_dir, args.model, args.conditions, labels, emit_projections=emit)
    if df.empty:
        print("[phase6] no data / no both-class goals for", args.conditions)
        return 1
    if emit is not None:
        ep = Path(args.emit_projections)
        ep.parent.mkdir(parents=True, exist_ok=True)
        with open(ep, "w") as f:
            for row in emit:
                f.write(json.dumps(row) + "\n")
        print(f"[phase6] emitted {len(emit)} per-row projections → {ep}")
    df = df.sort_values("logo_auc", ascending=False)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.out, index=False)
    n_succ = sum(labels.get(k, False) for k in labels)
    print(f"[phase6] group={'+'.join(args.conditions)} labelled={len(labels)} "
          f"(success={n_succ}) → {args.out}")
    top = df.dropna(subset=["logo_auc"]).head(8)
    print("[phase6] top (position, layer) by LOGO AUC:")
    for _, r in top.iterrows():
        print(f"    {r['position_name']:16s} layer {int(r['layer_index']):2d} "
              f"(depth {r['normalized_depth']:.2f})  AUC={r['logo_auc']:.3f}  n={int(r['n_pooled'])}")
    # shallowest position×layer with AUC>=0.7
    strong = df[(df["logo_auc"] >= 0.70)].sort_values(["position_index", "layer_index"])
    if not strong.empty:
        r = strong.iloc[0]
        print(f"[phase6] shallowest AUC>=0.70: {r['position_name']} layer {int(r['layer_index'])} "
              f"AUC={r['logo_auc']:.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
