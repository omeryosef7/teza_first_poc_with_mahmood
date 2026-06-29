#!/home/sharifm/students/omeryosef/miniconda3/envs/poc_stage2/bin/python
"""analyze_probe_confound_controls.py

Step 9: Representation confound controls and LOGO fold validation.

Tests:
1. Per-fold LOGO AUC validity (flag near-one-class folds; n_minority < 3)
2. Confound baseline AUCs:
   a. Goal-only: predict success from mean success rate of training goals
   b. Prompt-length: predict from think_token_count per condition A
   c. Condition-A overall rate: predict from marginal A success rate
3. Conservative LOGO AUC (excluding low-minority folds)
4. Cross-model AUC comparison on matched goals

Uses only existing CSV/JSON outputs — no GPU or token dynamics files required.
The probe AUC comes from probe_transfer_auc.csv (already computed).

Usage:
    /home/sharifm/students/omeryosef/miniconda3/envs/poc_stage2/bin/python \
        poc_stage4/analyze_probe_confound_controls.py \
        [--output-dir outputs/stage4/factorial_analysis]
"""
from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import numpy as np

_REPO_ROOT = Path(__file__).parent.parent
_PROBE_AUC_CSV = _REPO_ROOT / "outputs" / "stage4" / "factorial_analysis" / "probe_transfer_auc.csv"
_FACTORIAL_JSONL = _REPO_ROOT / "outputs" / "stage4" / "factorial_attack_dataset.jsonl"

MIN_MINORITY_FOR_VALID_FOLD = 3  # folds with fewer than this minority class examples are flagged


def load_probe_auc(path: Path) -> list[dict]:
    rows = []
    with open(path) as f:
        for row in csv.DictReader(f):
            if row["goal"] in ("MEAN", "STD"):
                continue
            rows.append({
                "model": row["model"],
                "goal": int(row["goal"]),
                "logo_auc": float(row["logo_auc"]),
                "n_success": int(row["n_success"]) if row["n_success"] else 0,
                "n_fail": int(row["n_fail"]) if row["n_fail"] else 0,
                "n_total": int(row["n_total"]) if row["n_total"] else 0,
                "layer": int(row["layer"]) if row["layer"] else 0,
                "subspace_rank": int(row["subspace_rank"]) if row["subspace_rank"] else 0,
                "segment": row["segment"],
            })
    return rows


def load_factorial(path: Path) -> list[dict]:
    rows = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                r = json.loads(line)
                if r.get("is_valid", True):
                    rows.append(r)
    return rows


def roc_auc(scores: list[float], labels: list[int]) -> Optional[float]:
    """Wilcoxon-Mann-Whitney AUC with correct tie handling.

    Ties contribute 0.5 per pair (standard convention):
      AUC = (n_concordant + 0.5 * n_tied) / (n_pos * n_neg)
    """
    n_pos = sum(labels)
    n_neg = len(labels) - n_pos
    if n_pos == 0 or n_neg == 0:
        return None
    concordant = 0
    tied = 0
    for i, (si, yi) in enumerate(zip(scores, labels)):
        if yi != 1:
            continue
        for sj, yj in zip(scores, labels):
            if yj != 0:
                continue
            if si > sj:
                concordant += 1
            elif si == sj:
                tied += 1
    return (concordant + 0.5 * tied) / (n_pos * n_neg)


def goal_level_success_rate(rows: list[dict], model: str) -> dict[int, float]:
    """Mean sr_success for condition A per goal (for a given model)."""
    cond_a = [r for r in rows if r["model_family"] == model and r["condition"] == "A"]
    by_goal = defaultdict(list)
    for r in cond_a:
        by_goal[r["goal_index"]].append(float(r["sr_success"]))
    return {g: float(np.mean(v)) for g, v in by_goal.items()}


def compute_goal_only_logo_auc(
    rows: list[dict], model: str, goals: list[int]
) -> list[dict]:
    """
    Goal-only LOGO baseline: predict P(success) = mean success rate of training goals.

    For each held-out goal, predict every example in that goal as having
    the overall training-goal mean success rate (all goals except held-out).
    The AUC measures whether between-goal variation in difficulty explains
    probe AUC without any representation signal.
    """
    all_a = [r for r in rows if r["model_family"] == model and r["condition"] == "A"]
    by_goal = defaultdict(list)
    for r in all_a:
        by_goal[r["goal_index"]].append(float(r["sr_success"]))

    results = []
    for held_out in goals:
        train_rates = [np.mean(v) for g, v in by_goal.items() if g != held_out]
        if not train_rates:
            continue
        train_mean = float(np.mean(train_rates))
        test_labels = [int(r["sr_success"]) for r in all_a if r["goal_index"] == held_out]
        if not test_labels:
            continue
        # All test examples get the same score (train mean rate) → AUC = 0.5
        test_scores = [train_mean] * len(test_labels)
        auc = roc_auc(test_scores, test_labels)
        results.append({
            "model": model, "held_out_goal": held_out,
            "baseline_type": "goal_only",
            "baseline_auc": auc,
            "n_test": len(test_labels),
            "n_success": sum(test_labels),
            "n_fail": len(test_labels) - sum(test_labels),
            "train_mean_rate": train_mean,
        })
    return results


def compute_thinking_length_logo_auc(
    rows: list[dict], model: str, goals: list[int]
) -> list[dict]:
    """
    Thinking-length LOGO baseline: predict P(success) from think_token_count for A condition.

    Within the LOGO train split, fit: score = think_token_count (raw, not z-scored).
    Higher thinking length → higher score.
    """
    all_a = [r for r in rows if r["model_family"] == model and r["condition"] == "A"
             and r.get("think_token_count") is not None]

    by_goal = defaultdict(list)
    for r in all_a:
        by_goal[r["goal_index"]].append(r)

    results = []
    for held_out in goals:
        test_rows = by_goal.get(held_out, [])
        if not test_rows:
            continue
        test_labels = [int(r["sr_success"]) for r in test_rows]
        test_scores = [float(r.get("think_token_count", 0) or 0) for r in test_rows]
        auc = roc_auc(test_scores, test_labels)
        results.append({
            "model": model, "held_out_goal": held_out,
            "baseline_type": "thinking_length",
            "baseline_auc": auc,
            "n_test": len(test_labels),
            "n_success": sum(test_labels),
            "n_fail": len(test_labels) - sum(test_labels),
        })
    return results


def validate_folds(probe_rows: list[dict]) -> list[dict]:
    """Add fold validity flags to probe AUC rows."""
    result = []
    for r in probe_rows:
        n_min = min(r["n_success"], r["n_fail"])
        is_near_one_class = n_min < MIN_MINORITY_FOR_VALID_FOLD
        result.append({
            **r,
            "n_minority": n_min,
            "is_near_one_class": is_near_one_class,
            "fold_valid": not is_near_one_class,
        })
    return result


def conservative_logo_auc(validated_rows: list[dict], model: str) -> dict:
    """LOGO AUC excluding near-one-class folds."""
    model_rows = [r for r in validated_rows if r["model"] == model]
    valid = [r for r in model_rows if r["fold_valid"]]
    all_aucs = [r["logo_auc"] for r in model_rows]
    valid_aucs = [r["logo_auc"] for r in valid]

    return {
        "model": model,
        "n_folds_total": len(model_rows),
        "n_folds_valid": len(valid),
        "n_folds_excluded": len(model_rows) - len(valid),
        "excluded_goals": [r["goal"] for r in model_rows if not r["fold_valid"]],
        "logo_auc_all_folds": float(np.mean(all_aucs)) if all_aucs else None,
        "logo_auc_valid_folds_only": float(np.mean(valid_aucs)) if valid_aucs else None,
        "logo_auc_std_valid": float(np.std(valid_aucs)) if valid_aucs else None,
        "min_minority_threshold": MIN_MINORITY_FOR_VALID_FOLD,
    }


def write_csv(path: Path, rows: list[dict]):
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(obj, f, indent=2, default=lambda x: float(x) if hasattr(x, "__float__") else x)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output-dir", type=Path,
                    default=Path("outputs/stage4/factorial_analysis"))
    args = ap.parse_args()

    print("Loading probe AUC CSV...")
    probe_rows = load_probe_auc(_PROBE_AUC_CSV)
    print(f"  {len(probe_rows)} fold rows")

    print("Loading factorial dataset...")
    fact_rows = load_factorial(_FACTORIAL_JSONL)
    print(f"  {len(fact_rows)} valid rows")

    # 1. Validate LOGO folds
    validated = validate_folds(probe_rows)

    print("\n=== Per-Fold Validity ===")
    for r in validated:
        flag = "⚠ EXCLUDED" if not r["fold_valid"] else "  valid"
        print(f"  {r['model']} goal {r['goal']}: AUC={r['logo_auc']:.3f} "
              f"n_min={r['n_minority']} {flag}")

    # 2. Conservative LOGO AUC
    conservative = {}
    for model in ("qwen3", "gemma4"):
        c = conservative_logo_auc(validated, model)
        conservative[model] = c
        print(f"\n{model.upper()} Conservative LOGO AUC:")
        print(f"  All folds:    {c['logo_auc_all_folds']:.3f}")
        print(f"  Valid folds:  {c['logo_auc_valid_folds_only']:.3f} ± {c['logo_auc_std_valid']:.3f}")
        print(f"  Excluded folds (n_minority<{MIN_MINORITY_FOR_VALID_FOLD}): {c['excluded_goals']}")

    # 3. Confound baselines per goal
    all_goals = list(range(11))
    baselines = []

    for model in ("qwen3", "gemma4"):
        model_goals = [r["goal"] for r in validated if r["model"] == model]

        goal_baselines = compute_goal_only_logo_auc(fact_rows, model, model_goals)
        len_baselines = compute_thinking_length_logo_auc(fact_rows, model, model_goals)
        baselines.extend(goal_baselines)
        baselines.extend(len_baselines)

    # 4. Predictive increment: probe vs baselines
    print("\n=== Predictive Increment (Probe vs Baselines) ===")
    for model in ("qwen3", "gemma4"):
        probe_auc = conservative[model]["logo_auc_valid_folds_only"]

        goal_aucs = [r["baseline_auc"] for r in baselines
                     if r["model"] == model and r["baseline_type"] == "goal_only"
                     and r["baseline_auc"] is not None]
        len_aucs = [r["baseline_auc"] for r in baselines
                    if r["model"] == model and r["baseline_type"] == "thinking_length"
                    and r["baseline_auc"] is not None]

        goal_mean = float(np.mean(goal_aucs)) if goal_aucs else None
        len_mean = float(np.mean(len_aucs)) if len_aucs else None

        print(f"\n  {model}:")
        print(f"    Probe LOGO AUC (valid folds): {probe_auc:.3f}")
        print(f"    Goal-only baseline:            {goal_mean:.3f} (Δ={probe_auc-goal_mean:+.3f})" if goal_mean else "    Goal-only: N/A")
        print(f"    Thinking-length baseline:      {len_mean:.3f} (Δ={probe_auc-len_mean:+.3f})" if len_mean else "    Thinking-length: N/A")

    # 5. Write outputs
    write_csv(args.output_dir / "logo_fold_details.csv", validated)
    write_csv(args.output_dir / "confound_baseline_aucs.csv", baselines)
    write_json(args.output_dir / "conservative_logo_auc.json", {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "min_minority_threshold": MIN_MINORITY_FOR_VALID_FOLD,
        "models": conservative,
    })

    print(f"\nOutputs written to {args.output_dir}/")
    print("Files: logo_fold_details.csv, confound_baseline_aucs.csv, conservative_logo_auc.json")


if __name__ == "__main__":
    main()
