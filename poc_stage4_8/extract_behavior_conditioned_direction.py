"""
Stage 4.8 — Extract behavior-conditioned predictive direction.

Uses only matched cells (≥1 success, ≥1 failure, both with completed
think/final segmentation and first-500-token representations).

Procedure:
  1. Load matched_outcome_cells.csv and per-example representations
  2. Within each (source, condition) cell, center representations by cell mean
  3. Leave-one-prompt-out CV: train on 3 prompts' matched cells, test on held-out
  4. Compute success-minus-failure direction from centered training examples
  5. Evaluate on held-out prompt: projection diff, AUC, balanced accuracy
  6. Permutation test (1000 permutations, permute labels within cells)
  7. Compare against old provisional direction (harmful-vs-harmless)

Primary layer: 22
Primary window: first_500 thinking tokens (does NOT leak final answer)
Direction name: "behavior-conditioned predictive direction" (not causal)

Usage:
  python -m poc_stage4_8.extract_behavior_conditioned_direction
      --run-dir outputs/stage4_8/runs/<timestamp>
      [--representations-dir PATH]
      [--output-dir PATH]
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path
from typing import Any

import numpy as np

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

_OLD_DIRECTION_DIR = _REPO_ROOT / "outputs" / "stage4" / "qwen3-14b" / "refusal_direction"
_PRIMARY_LAYER = 22
_PRIMARY_WINDOW = "first_500"
_EXPLORATORY_LAYERS = [13, 16, 38, 39]
_EXPLORATORY_WINDOWS = ["first_128", "first_2000", "prompt_end"]
_N_PERM = 1000
_PERM_SEED = 42
_BOOT_SEED = 42
_N_BOOT = 500


def _load_jsonl(path: Path) -> list[dict]:
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def _f(x, default=float("nan")) -> float:
    try:
        return float(x)
    except (TypeError, ValueError):
        return default


def _b(x) -> bool | None:
    if x is None:
        return None
    if isinstance(x, bool):
        return x
    s = str(x).lower()
    if s in ("true", "1"):
        return True
    if s in ("false", "0"):
        return False
    return None


def load_representations(
    representations_dir: Path,
    layer: int,
    window: str,
) -> dict[str, np.ndarray]:
    """
    Load per-example representation vectors from representations_dir.
    Returns dict: run_id → vector (numpy array, shape [hidden_dim] or scalar projection).
    """
    feat_key = f"layer{layer}_{window}_mean_projection"
    result: dict[str, Any] = {}

    # Try loading from projection summary JSONL first (scalar projections)
    proj_path = representations_dir / "projection_summary.jsonl"
    if proj_path.exists():
        rows = _load_jsonl(proj_path)
        for r in rows:
            run_id = r.get("run_id", "")
            val = r.get(feat_key)
            if val is not None:
                result[run_id] = np.array([float(val)])
        print(f"  Loaded {len(result)} scalar projections from {proj_path}")
        return result

    # Try per-example JSON files
    for json_file in representations_dir.glob("*.json"):
        try:
            data = json.loads(json_file.read_text())
            run_id = data.get("run_id", json_file.stem)
            val = data.get(feat_key)
            if val is not None:
                result[run_id] = np.array([float(val)])
        except Exception:
            continue
    if result:
        print(f"  Loaded {len(result)} representations from per-example JSON files")
    return result


def _center_within_cell(
    representations: dict[str, Any],
    rows: list[dict],
) -> dict[str, np.ndarray]:
    """
    Within each (source, condition) cell, subtract the cell mean from each representation.
    Returns dict: run_id → centered representation.
    """
    from collections import defaultdict
    cells: dict[tuple, list[str]] = defaultdict(list)
    for r in rows:
        run_id = r.get("run_id", "")
        if run_id in representations:
            cell_key = (r.get("source_example_id", ""), r.get("condition", ""))
            cells[cell_key].append(run_id)

    centered: dict[str, np.ndarray] = {}
    for (src, cond), run_ids in cells.items():
        vecs = np.stack([representations[rid] for rid in run_ids])
        cell_mean = vecs.mean(axis=0)
        for rid in run_ids:
            centered[rid] = representations[rid] - cell_mean
    return centered


def _direction_from_examples(
    centered: dict[str, np.ndarray],
    rows_with_labels: list[tuple[str, bool]],  # (run_id, is_success)
) -> np.ndarray | None:
    """
    Compute success-minus-failure direction from centered representations.
    Returns normalized direction or None if no examples.
    """
    success_vecs = []
    failure_vecs = []
    for run_id, is_success in rows_with_labels:
        if run_id not in centered:
            continue
        if is_success:
            success_vecs.append(centered[run_id])
        else:
            failure_vecs.append(centered[run_id])
    if not success_vecs or not failure_vecs:
        return None
    mean_success = np.mean(success_vecs, axis=0)
    mean_failure = np.mean(failure_vecs, axis=0)
    direction = mean_success - mean_failure
    norm = np.linalg.norm(direction)
    if norm < 1e-10:
        return None
    return direction / norm


def _auc(labels: list[bool], scores: list[float]) -> float | None:
    """Compute AUC from binary labels and continuous scores."""
    try:
        from sklearn.metrics import roc_auc_score
        if len(set(labels)) < 2:
            return None
        return float(roc_auc_score(labels, scores))
    except ImportError:
        # Fallback: Wilcoxon rank-sum AUC
        pos_scores = [s for l, s in zip(labels, scores) if l]
        neg_scores = [s for l, s in zip(labels, scores) if not l]
        if not pos_scores or not neg_scores:
            return None
        concordant = sum(1 for p in pos_scores for n in neg_scores if p > n)
        ties = sum(1 for p in pos_scores for n in neg_scores if p == n)
        total = len(pos_scores) * len(neg_scores)
        return (concordant + 0.5 * ties) / total


def _balanced_accuracy(labels: list[bool], preds: list[bool]) -> float | None:
    if not labels:
        return None
    tp = sum(1 for l, p in zip(labels, preds) if l and p)
    fp = sum(1 for l, p in zip(labels, preds) if not l and p)
    tn = sum(1 for l, p in zip(labels, preds) if not l and not p)
    fn = sum(1 for l, p in zip(labels, preds) if l and not p)
    n_pos = tp + fn
    n_neg = tn + fp
    sens = tp / n_pos if n_pos else 0.0
    spec = tn / n_neg if n_neg else 0.0
    return (sens + spec) / 2.0


def loo_cv(
    rows: list[dict],
    representations: dict[str, Any],
    matched_cells: set[tuple[str, str]],
    layer: int,
    window: str,
    n_perm: int = _N_PERM,
    perm_seed: int = _PERM_SEED,
) -> dict:
    """
    Leave-one-prompt-out cross-validation.
    For each held-out source prompt, train direction on remaining prompts' matched cells,
    evaluate on held-out prompt.
    """
    feat_key = f"layer{layer}_{window}_mean_projection"

    # Build centered representations
    centered = _center_within_cell(representations, rows)

    source_ids = sorted(set(r.get("source_example_id", "") for r in rows))
    fold_results = []

    for held_out in source_ids:
        # Training: rows from other prompts in matched cells only
        train_rows = [
            r for r in rows
            if r.get("source_example_id") != held_out
            and (r.get("source_example_id", ""), r.get("condition", "")) in matched_cells
            and r.get("run_id") in centered
            and _b(r.get("sr_success")) is not None
        ]
        # Test: rows from held-out prompt (any condition, complete, valid seg)
        test_rows = [
            r for r in rows
            if r.get("source_example_id") == held_out
            and r.get("finish_reason") == "eos_token"
            and r.get("thinking_segmentation_status") == "parsed_from_think_tags"
            and r.get("run_id") in centered
            and _b(r.get("sr_success")) is not None
        ]
        if not train_rows or not test_rows:
            fold_results.append({
                "held_out_prompt": held_out,
                "n_train": len(train_rows),
                "n_test": len(test_rows),
                "note": "insufficient train or test",
            })
            continue

        train_labels = [(r.get("run_id", ""), _b(r.get("sr_success")) is True) for r in train_rows]
        direction = _direction_from_examples(centered, train_labels)
        if direction is None:
            fold_results.append({
                "held_out_prompt": held_out,
                "n_train": len(train_rows),
                "n_test": len(test_rows),
                "note": "direction extraction failed (no success or failure in training)",
            })
            continue

        # Evaluate on test set
        test_projections = []
        test_labels_bin = []
        for r in test_rows:
            run_id = r.get("run_id", "")
            if run_id not in centered:
                continue
            proj = float(np.dot(centered[run_id], direction))
            label = _b(r.get("sr_success")) is True
            test_projections.append(proj)
            test_labels_bin.append(label)

        if not test_projections:
            fold_results.append({
                "held_out_prompt": held_out,
                "n_train": len(train_rows),
                "n_test": len(test_rows),
                "note": "no evaluable test projections",
            })
            continue

        threshold = 0.0  # project centered representations — threshold at 0
        test_preds = [p > threshold for p in test_projections]

        auc = _auc(test_labels_bin, test_projections)
        bal_acc = _balanced_accuracy(test_labels_bin, test_preds)
        mean_pos = float(np.mean([p for l, p in zip(test_labels_bin, test_projections) if l])) if any(test_labels_bin) else None
        mean_neg = float(np.mean([p for l, p in zip(test_labels_bin, test_projections) if not l])) if any(not l for l in test_labels_bin) else None
        proj_diff = (mean_pos - mean_neg) if (mean_pos is not None and mean_neg is not None) else None

        fold_results.append({
            "held_out_prompt": held_out,
            "n_train": len(train_rows),
            "n_test": len(test_rows),
            "n_test_success": sum(test_labels_bin),
            "n_test_failure": sum(not l for l in test_labels_bin),
            "auc": auc,
            "balanced_accuracy": bal_acc,
            "projection_diff": proj_diff,
            "mean_proj_success": mean_pos,
            "mean_proj_failure": mean_neg,
            "direction_positive_for_success": proj_diff is not None and proj_diff > 0,
        })

    # Aggregate across folds
    valid_folds = [f for f in fold_results if "auc" in f and f["auc"] is not None]
    mean_auc = float(np.mean([f["auc"] for f in valid_folds])) if valid_folds else None
    mean_bal_acc = float(np.mean([f["balanced_accuracy"] for f in valid_folds if f.get("balanced_accuracy") is not None])) if valid_folds else None
    n_positive = sum(1 for f in valid_folds if f.get("direction_positive_for_success"))
    sign_consistent = n_positive == len(valid_folds) if valid_folds else False

    # Permutation test (permute outcome labels within cells)
    perm_aucs = []
    if valid_folds and n_perm > 0:
        rng = np.random.default_rng(perm_seed)
        for _ in range(n_perm):
            perm_rows = []
            # Permute labels within each (source, condition) cell
            from collections import defaultdict
            cells_map: dict[tuple, list[int]] = defaultdict(list)
            for i, r in enumerate(rows):
                cell_key = (r.get("source_example_id", ""), r.get("condition", ""))
                cells_map[cell_key].append(i)
            # Build permuted label lookup
            perm_labels: dict[str, bool] = {}
            for cell_key, indices in cells_map.items():
                cell_rows_perm = [rows[i] for i in indices]
                orig_labels = [_b(r.get("sr_success")) is True for r in cell_rows_perm]
                perm_idx = rng.permutation(len(orig_labels))
                for r, perm_label in zip(cell_rows_perm, [orig_labels[i] for i in perm_idx]):
                    perm_labels[r.get("run_id", "")] = perm_label
            # Evaluate one fold (use first held_out for efficiency)
            if valid_folds:
                held_out = valid_folds[0]["held_out_prompt"]
                train_perm = [
                    (r.get("run_id", ""), perm_labels.get(r.get("run_id", ""), False))
                    for r in rows
                    if r.get("source_example_id") != held_out
                    and (r.get("source_example_id", ""), r.get("condition", "")) in matched_cells
                    and r.get("run_id") in centered
                ]
                direction_perm = _direction_from_examples(centered, train_perm)
                if direction_perm is not None:
                    test_r = [r for r in rows if r.get("source_example_id") == held_out and r.get("run_id") in centered and _b(r.get("sr_success")) is not None]
                    perm_projs = [float(np.dot(centered[r.get("run_id","")], direction_perm)) for r in test_r]
                    perm_lbls = [perm_labels.get(r.get("run_id",""), False) for r in test_r]
                    if perm_projs and len(set(perm_lbls)) > 1:
                        pa = _auc(perm_lbls, perm_projs)
                        if pa is not None:
                            perm_aucs.append(pa)

    perm_p = None
    if perm_aucs and mean_auc is not None:
        perm_p = float(np.mean([a >= mean_auc for a in perm_aucs]))

    return {
        "layer": layer,
        "window": window,
        "n_folds": len(fold_results),
        "n_valid_folds": len(valid_folds),
        "mean_auc": mean_auc,
        "mean_balanced_accuracy": mean_bal_acc,
        "n_folds_positive_direction": n_positive,
        "sign_consistent": sign_consistent,
        "permutation_p_approx": perm_p,
        "n_permutations": len(perm_aucs),
        "fold_results": fold_results,
        "note": (
            "behavior-conditioned predictive direction — not causal. "
            "Trained on success-minus-failure within matched cells (≥1 success, ≥1 failure). "
            "Evaluated on held-out source prompts only."
        ),
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Extract Stage 4.8 behavior-conditioned direction.")
    p.add_argument("--run-dir", type=Path, required=True)
    p.add_argument("--representations-dir", type=Path, default=None)
    p.add_argument("--output-dir", type=Path, default=None)
    args = p.parse_args(argv)

    run_dir = args.run_dir
    rep_dir = args.representations_dir or (run_dir / "representations")
    out_dir = args.output_dir or (run_dir / "direction_analysis")
    out_dir.mkdir(parents=True, exist_ok=True)

    # Load run_summary
    summary_path = run_dir / "run_summary.jsonl"
    if not summary_path.exists():
        print(f"ERROR: {summary_path} not found")
        return 1
    rows = _load_jsonl(summary_path)
    print(f"Loaded {len(rows)} rows")

    # Load matched cells
    matched_path = run_dir / "analysis" / "matched_outcome_cells.csv"
    if not matched_path.exists():
        print(f"ERROR: {matched_path} not found. Run analyze_repeated_generations.py first.")
        return 1
    with open(matched_path, encoding="utf-8") as f:
        matched_rows = list(csv.DictReader(f))
    matched_cells: set[tuple[str, str]] = {
        (r["source_example_id"], r["condition"]) for r in matched_rows
    }
    print(f"Loaded {len(matched_cells)} matched cells")

    if not matched_cells:
        print("No matched cells found. Cannot extract direction.")
        print("Applying decision gate: Branch C (insufficient within-cell variation)")
        result = {
            "created_utc": str(Path(__file__).stat().st_mtime),
            "decision_gate_branch": "C",
            "note": (
                "No matched outcome cells (cells with both success and failure). "
                "Cannot extract behavior-conditioned direction. "
                "Recommend: more prompts, a separately preregistered sampling setting, "
                "or cross-model replication."
            ),
        }
        with open(out_dir / "direction_results.json", "w") as f:
            json.dump(result, f, indent=2)
        return 0

    # Check representations available
    if not rep_dir.exists():
        print(f"Representations dir not found: {rep_dir}")
        print("Run compute_repeated_generation_representations.py first.")
        return 1

    all_results = []
    for layer in [_PRIMARY_LAYER] + _EXPLORATORY_LAYERS:
        for window in [_PRIMARY_WINDOW] + _EXPLORATORY_WINDOWS:
            print(f"\nLayer {layer}, window={window} ...")
            reps = load_representations(rep_dir, layer, window)
            if not reps:
                print(f"  No representations found for layer={layer} window={window}")
                continue

            res = loo_cv(rows, reps, matched_cells, layer=layer, window=window)
            is_primary = layer == _PRIMARY_LAYER and window == _PRIMARY_WINDOW
            res["is_primary"] = is_primary
            all_results.append(res)

            if is_primary:
                print(
                    f"  PRIMARY: mean_auc={res['mean_auc']} "
                    f"mean_bal_acc={res['mean_balanced_accuracy']} "
                    f"sign_consistent={res['sign_consistent']} "
                    f"perm_p={res['permutation_p_approx']}"
                )

    # Compare to old direction
    old_dir_results = None
    old_proj_path = rep_dir / "old_direction_projections.jsonl"
    if old_proj_path.exists():
        old_rows = _load_jsonl(old_proj_path)
        # Use the old projection as a scalar feature
        old_reps: dict[str, np.ndarray] = {
            r["run_id"]: np.array([_f(r.get("old_direction_projection", float("nan")))])
            for r in old_rows
            if not math.isnan(_f(r.get("old_direction_projection", float("nan"))))
        }
        if old_reps:
            old_dir_results = loo_cv(rows, old_reps, matched_cells, layer=-1, window="old_direction")
            old_dir_results["note"] = "Old provisional harmful-vs-harmless direction for comparison"
            all_results.append(old_dir_results)

    # Decision gate
    primary = next((r for r in all_results if r.get("is_primary")), None)
    branch = "C"  # default: insufficient variation
    if primary and primary.get("n_valid_folds", 0) > 0:
        if primary.get("mean_auc") is not None and primary["mean_auc"] > 0.6 and primary.get("sign_consistent"):
            branch = "A"  # sufficient prediction, recommend intervention pilot
        elif primary.get("mean_auc") is not None:
            branch = "B"  # variation exists but direction doesn't generalize

    # Write results
    from datetime import datetime, timezone
    final_result = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "primary_layer": _PRIMARY_LAYER,
        "primary_window": _PRIMARY_WINDOW,
        "n_matched_cells": len(matched_cells),
        "decision_gate_branch": branch,
        "direction_name": "behavior-conditioned predictive direction",
        "direction_status": "predictive_not_causal",
        "results_by_layer_window": all_results,
        "old_direction_results": old_dir_results,
    }
    out_path = out_dir / "direction_results.json"
    with open(out_path, "w") as f:
        json.dump(final_result, f, indent=2, default=str)
    print(f"\nWrote {out_path}")
    print(f"Decision gate: Branch {branch}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
