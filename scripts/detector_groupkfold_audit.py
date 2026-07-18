#!/usr/bin/env python3
"""Detector robustness rerun: GroupKFold-by-behavior and leave-one-generation-seed-out.

Reuses the exact same feature extraction as poc_stage_gcg_early/train_realtime_detector.py
(layer-averaged hidden state at relative generated-token position `pos`, label =
"optimized" substring vs neutral_control), but replaces the plain StratifiedKFold
(no grouping) with:
  1. GroupKFold(groups=task_id) -- no behavior appears in both train and val.
  2. Leave-one-generation-seed-out -- train on 2 of {42,43,44}, test on the 3rd.

Run under the poc_stage2 conda env (has torch + sklearn):
  /home/sharifm/students/omeryosef/miniconda3/envs/poc_stage2/bin/python \
      scripts/detector_groupkfold_audit.py --run-dir outputs/stage_gcg_full/gcg_full_qwen3_weighted

Outputs a JSON report to <run-dir>/../../stage_gcg_ablation/detector_groupkfold/<run-name>_groupkfold.json
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import torch
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupKFold, StratifiedKFold, cross_val_predict
from sklearn.metrics import roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


def load_samples(run_dir: Path, target_rel_pos: int = 0):
    hs_dir = run_dir / "hidden_states"
    pt_files = sorted(hs_dir.glob("*.pt"))
    X, y, groups, seeds = [], [], [], []
    skipped = 0
    for pt_file in pt_files:
        data = torch.load(pt_file, map_location="cpu", weights_only=False)
        cond = data.get("condition_label", "unknown")
        gen_start = data.get("gen_start", 0)
        positions = data.get("positions", [])
        hs_dict = data.get("hidden_states", {})
        task_id = data.get("task_id")
        seed = data.get("seed")

        if "optimized" in cond:
            label = 1
        elif cond == "neutral_control":
            label = 0
        else:
            continue

        target_abs_pos = gen_start + target_rel_pos
        if target_abs_pos not in positions:
            skipped += 1
            continue

        layers = sorted(hs_dict.keys(), key=int)
        vecs = []
        for layer_str in layers:
            pos_str = str(target_abs_pos)
            if pos_str in hs_dict[layer_str]:
                v = hs_dict[layer_str][pos_str]
                if isinstance(v, torch.Tensor):
                    vecs.append(v.float().numpy())
        if not vecs:
            skipped += 1
            continue

        X.append(np.mean(vecs, axis=0))
        y.append(label)
        groups.append(task_id)
        seeds.append(seed)

    return np.array(X), np.array(y), np.array(groups), np.array(seeds), skipped


def make_pipe():
    return Pipeline([
        ("scaler", StandardScaler()),
        ("clf", LogisticRegression(max_iter=1000, C=1.0, class_weight="balanced")),
    ])


def run_groupkfold(X, y, groups, n_splits=5):
    n_groups = len(set(groups))
    n_splits = min(n_splits, n_groups)
    gkf = GroupKFold(n_splits=n_splits)
    fold_aucs = []
    for train_idx, val_idx in gkf.split(X, y, groups):
        if len(set(y[val_idx])) < 2:
            continue  # AUC undefined for single-class fold
        pipe = make_pipe()
        pipe.fit(X[train_idx], y[train_idx])
        prob = pipe.predict_proba(X[val_idx])[:, 1]
        fold_aucs.append(float(roc_auc_score(y[val_idx], prob)))
    return {
        "method": f"GroupKFold(n_splits={n_splits}, groups=task_id)",
        "n_groups": n_groups,
        "fold_aucs": fold_aucs,
        "mean_auc": float(np.mean(fold_aucs)) if fold_aucs else None,
        "std_auc": float(np.std(fold_aucs)) if fold_aucs else None,
        "n_folds_evaluable": len(fold_aucs),
    }


def run_stratified_baseline(X, y, n_splits=5):
    cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)
    fold_aucs = []
    for train_idx, val_idx in cv.split(X, y):
        pipe = make_pipe()
        pipe.fit(X[train_idx], y[train_idx])
        prob = pipe.predict_proba(X[val_idx])[:, 1]
        fold_aucs.append(float(roc_auc_score(y[val_idx], prob)))
    return {
        "method": "StratifiedKFold(n_splits=5, no grouping) -- ORIGINAL METHODOLOGY",
        "fold_aucs": fold_aucs,
        "mean_auc": float(np.mean(fold_aucs)),
        "std_auc": float(np.std(fold_aucs)),
    }


def run_leave_one_seed_out(X, y, groups, seeds):
    distinct_seeds = sorted(set(int(s) for s in seeds if s is not None))
    results = {}
    for held_out in distinct_seeds:
        train_mask = seeds != held_out
        test_mask = seeds == held_out
        if len(set(y[train_mask])) < 2 or len(set(y[test_mask])) < 2:
            results[str(held_out)] = {"error": "single-class split, AUC undefined"}
            continue
        pipe = make_pipe()
        pipe.fit(X[train_mask], y[train_mask])
        prob = pipe.predict_proba(X[test_mask])[:, 1]
        auc = float(roc_auc_score(y[test_mask], prob))
        results[str(held_out)] = {
            "held_out_seed": held_out,
            "n_train": int(train_mask.sum()),
            "n_test": int(test_mask.sum()),
            "auc": auc,
        }
    return results


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--pos", type=int, default=0)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    run_dir = Path(args.run_dir)
    X, y, groups, seeds, skipped = load_samples(run_dir, args.pos)

    report = {
        "run_dir": str(run_dir),
        "pos": args.pos,
        "n_samples": len(y),
        "n_optimized": int(y.sum()),
        "n_neutral": int((1 - y).sum()),
        "n_distinct_behaviors": len(set(groups)),
        "n_distinct_seeds": len(set(int(s) for s in seeds if s is not None)),
        "skipped": skipped,
    }

    if len(y) == 0 or len(set(y)) < 2:
        report["error"] = "insufficient data (need both classes present)"
        print(json.dumps(report, indent=2))
        return

    report["stratified_baseline"] = run_stratified_baseline(X, y)
    report["groupkfold_by_behavior"] = run_groupkfold(X, y, groups)
    report["leave_one_generation_seed_out"] = run_leave_one_seed_out(X, y, groups, seeds)

    out_path = Path(args.out) if args.out else Path("outputs/stage_gcg_ablation/detector_groupkfold") / f"{run_dir.name}_groupkfold.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2))
    print(f"Wrote {out_path}")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
