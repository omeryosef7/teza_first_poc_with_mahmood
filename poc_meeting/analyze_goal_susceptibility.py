"""
Goal susceptibility diagnostic for Mahmood meeting.
Uses existing Stage 4.7 and Stage 4.8 outputs — no new GPU jobs.
Does not inspect or print raw harmful text.

Outputs:
  outputs/meeting/mahmood_20260611/tables/goal_susceptibility_summary.csv
  outputs/meeting/mahmood_20260611/figures/07_goal_susceptibility_map.png

Usage:
    python poc_meeting/analyze_goal_susceptibility.py
"""

import csv
import json
import math
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S47_ANALYSIS = os.path.join(BASE, "outputs/stage4_7/runs/run_array_20260610_1442/analysis")
S48_ANALYSIS = os.path.join(BASE, "outputs/stage4_8/runs/run_array_20260611_0109/analysis")
S47_MECH = os.path.join(S47_ANALYSIS, "mechanistic_summary.csv")
S47_GOAL = os.path.join(S47_ANALYSIS, "goal_stratified_summary.csv")
S48_CELL = os.path.join(S48_ANALYSIS, "cell_summary.csv")
OUT_DIR = os.path.join(BASE, "outputs/meeting/mahmood_20260611")
TABLE_DIR = os.path.join(OUT_DIR, "tables")
FIG_DIR = os.path.join(OUT_DIR, "figures")
os.makedirs(TABLE_DIR, exist_ok=True)
os.makedirs(FIG_DIR, exist_ok=True)


def mean(lst):
    return sum(lst) / len(lst) if lst else float("nan")


def spearman(x, y):
    n = len(x)
    if n < 3:
        return float("nan")
    rx = sorted(range(n), key=lambda i: x[i])
    ry = sorted(range(n), key=lambda i: y[i])
    rankx = [0] * n
    ranky = [0] * n
    for rank, idx in enumerate(rx):
        rankx[idx] = rank + 1
    for rank, idx in enumerate(ry):
        ranky[idx] = rank + 1
    d2 = sum((rankx[i] - ranky[i]) ** 2 for i in range(n))
    return 1 - 6 * d2 / (n * (n**2 - 1))


# ── Stage 4.7 goal-stratified summary ─────────────────────────────────────────
print("Loading Stage 4.7 goal-stratified data...")
goal47 = {}
if os.path.exists(S47_GOAL):
    with open(S47_GOAL) as f:
        for row in csv.DictReader(f):
            g = row.get("goal_index", row.get("goal_index", "?"))
            c = row.get("condition", "?")
            goal47[(g, c)] = row
    print(f"  Loaded {len(goal47)} goal×condition rows from {os.path.basename(S47_GOAL)}")
else:
    print(f"  WARNING: {S47_GOAL} not found; computing from canonical CSV")

# Fallback: compute from canonical_per_run_results.csv
s47_canon = os.path.join(S47_ANALYSIS, "canonical_per_run_results.csv")
goal47_raw = {}
with open(s47_canon) as f:
    for row in csv.DictReader(f):
        g = str(row["goal_index"])
        c = row["condition"]
        key = (g, c)
        if key not in goal47_raw:
            goal47_raw[key] = {"scores": [], "think_tokens": [], "l22_proj": [], "n_cc": 0, "n_cc_success": 0}
        entry = goal47_raw[key]
        is_censored = row.get("is_censored", "False").strip().lower() == "true"
        sr_score = float(row["strongreject_score"]) if row["strongreject_score"] else 0.0
        think_tokens = float(row["think_token_count"]) if row["think_token_count"] else 0.0
        l22_str = row.get("layer22_first_500_mean_projection", "")
        entry["scores"].append(sr_score)
        entry["think_tokens"].append(think_tokens)
        if l22_str:
            entry["l22_proj"].append(float(l22_str))
        if not is_censored:
            entry["n_cc"] += 1
            sr_success = row.get("sr_success_complete_case", "False").strip().lower() == "true"
            if sr_success:
                entry["n_cc_success"] += 1

# ── Stage 4.8 cell summary ─────────────────────────────────────────────────────
print("Loading Stage 4.8 cell data...")
goal48 = {}
with open(S48_CELL) as f:
    for row in csv.DictReader(f):
        g = str(row["goal_index"])
        c = row["condition"]
        goal48[(g, c)] = row

# ── Build combined goal susceptibility table ───────────────────────────────────
all_goals = sorted(set(
    [k[0] for k in goal47_raw] + [k[0] for k in goal48]
))
all_conds_47 = ["A", "D", "F", "E"]
all_conds_48 = ["A", "D", "F"]

rows = []
for g in all_goals:
    row_out = {"goal_index": g}

    # Stage 4.7 per condition
    for c in all_conds_47:
        entry = goal47_raw.get((g, c), {})
        n_cc = entry.get("n_cc", 0)
        n_cc_success = entry.get("n_cc_success", 0)
        mean_sr = mean(entry.get("scores", [])) if entry.get("scores") else float("nan")
        mean_think = mean(entry.get("think_tokens", [])) if entry.get("think_tokens") else float("nan")
        mean_l22 = mean(entry.get("l22_proj", [])) if entry.get("l22_proj") else float("nan")
        row_out[f"s47_{c}_n_cc"] = n_cc
        row_out[f"s47_{c}_n_cc_success"] = n_cc_success
        row_out[f"s47_{c}_cc_rate"] = round(n_cc_success / n_cc, 3) if n_cc > 0 else float("nan")
        row_out[f"s47_{c}_mean_sr"] = round(mean_sr, 3) if not math.isnan(mean_sr) else float("nan")
        row_out[f"s47_{c}_mean_think"] = round(mean_think, 0) if not math.isnan(mean_think) else float("nan")
        row_out[f"s47_{c}_mean_l22_first500"] = round(mean_l22, 3) if not math.isnan(mean_l22) else float("nan")

    # Stage 4.8 per condition
    for c in all_conds_48:
        cell = goal48.get((g, c), {})
        n_seeds = int(cell.get("n_seeds", 0)) if cell else 0
        n_success = int(cell.get("n_success", 0)) if cell else 0
        sr_var = float(cell.get("sr_score_variance", 0)) if cell else float("nan")
        mean_think_48 = float(cell.get("mean_think_tokens", 0)) if cell else float("nan")
        is_matched = cell.get("is_matched_outcome_cell", "False").strip().lower() == "true" if cell else False
        row_out[f"s48_{c}_n_seeds"] = n_seeds
        row_out[f"s48_{c}_n_success"] = n_success
        row_out[f"s48_{c}_rate"] = round(n_success / n_seeds, 3) if n_seeds > 0 else float("nan")
        row_out[f"s48_{c}_sr_var"] = round(sr_var, 4)
        row_out[f"s48_{c}_mean_think"] = round(mean_think_48, 0)
        row_out[f"s48_{c}_is_matched_cell"] = is_matched

    # Goal-level classification
    a_rate_47 = row_out.get("s47_A_cc_rate", float("nan"))
    a_rate_48 = row_out.get("s48_A_rate", float("nan"))
    avg_a = mean([r for r in [a_rate_47, a_rate_48] if not math.isnan(r)])
    if avg_a >= 0.9:
        row_out["susceptibility_class"] = "universal_success"
    elif avg_a <= 0.1:
        row_out["susceptibility_class"] = "universal_failure"
    elif 0.25 <= avg_a <= 0.75:
        row_out["susceptibility_class"] = "intermediate"
    else:
        row_out["susceptibility_class"] = "partial"

    # Candidate for matched-cell experiment
    any_matched = any(row_out.get(f"s48_{c}_is_matched_cell", False) for c in all_conds_48)
    row_out["is_current_matched_cell_goal"] = any_matched
    row_out["candidate_for_next_experiment"] = (
        row_out["susceptibility_class"] == "intermediate"
        and not math.isnan(a_rate_47)
    )
    rows.append(row_out)

# Write summary CSV
summary_path = os.path.join(TABLE_DIR, "goal_susceptibility_summary.csv")
if rows:
    fieldnames = list(rows[0].keys())
    with open(summary_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} goals to {summary_path}")

# Print summary table
print("\n=== Goal Susceptibility Summary ===")
header = f"{'Goal':5s} | {'s47_A':8s} | {'s47_D':8s} | {'s47_F':8s} | {'s48_A':8s} | {'s48_D':8s} | {'s48_F':8s} | Class"
print(header)
print("-" * len(header))
for r in rows:
    g = r["goal_index"]
    def fmt(k): v = r.get(k, float("nan")); return f"{v:.0%}" if not math.isnan(float(v)) else " n/a "
    print(f"{g:5s} | {fmt('s47_A_cc_rate'):8s} | {fmt('s47_D_cc_rate'):8s} | {fmt('s47_F_cc_rate'):8s} | "
          f"{fmt('s48_A_rate'):8s} | {fmt('s48_D_rate'):8s} | {fmt('s48_F_rate'):8s} | "
          f"{r['susceptibility_class']}")

# Correlation analysis
print("\n=== Goal-level correlations (Stage 4.7, condition A) ===")
valid_goals = [r for r in rows if not math.isnan(float(r.get("s47_A_cc_rate", float("nan"))))]
if len(valid_goals) >= 3:
    a_rates = [float(r["s47_A_cc_rate"]) for r in valid_goals]
    a_think = [float(r["s47_A_mean_think"]) for r in valid_goals if not math.isnan(float(r.get("s47_A_mean_think", float("nan"))))]
    a_l22 = [float(r["s47_A_mean_l22_first500"]) for r in valid_goals if not math.isnan(float(r.get("s47_A_mean_l22_first500", float("nan"))))]
    if len(a_think) == len(a_rates):
        rho_think = spearman(a_rates, a_think)
        print(f"  Spearman rho (goal success rate vs mean think tokens, cond A, n={len(a_rates)}): {rho_think:.3f}")
    if len(a_l22) == len(a_rates):
        rho_l22 = spearman(a_rates, a_l22)
        print(f"  Spearman rho (goal success rate vs mean L22 projection, cond A, n={len(a_rates)}): {rho_l22:.3f}")

candidates = [r["goal_index"] for r in rows if r.get("candidate_for_next_experiment")]
print(f"\nCandidate goals for matched-cell experiment (intermediate success rate): {candidates}")

# ── Figure: goal susceptibility map ───────────────────────────────────────────
try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    import numpy as np

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    fig.suptitle("Goal Susceptibility: Stage 4.7 vs Stage 4.8", fontsize=14, fontweight="bold")

    goals = [r["goal_index"] for r in rows]
    colors = {"universal_success": "#2ecc71", "intermediate": "#f39c12",
              "partial": "#e67e22", "universal_failure": "#e74c3c"}

    # Left: Stage 4.7 success rates by goal and condition
    ax = axes[0]
    x = np.arange(len(goals))
    width = 0.2
    conds_47 = [("A", "#2980b9"), ("D", "#e67e22"), ("F", "#8e44ad"), ("E", "#95a5a6")]
    for i, (c, col) in enumerate(conds_47):
        rates = []
        for r in rows:
            v = r.get(f"s47_{c}_cc_rate", float("nan"))
            rates.append(float(v) if not math.isnan(float(v)) else 0.0)
        ax.bar(x + i * width - 1.5 * width, rates, width, label=f"Cond {c}", color=col, alpha=0.85)
    ax.set_xticks(x)
    ax.set_xticklabels([f"Goal {g}" for g in goals])
    ax.set_ylabel("Complete-case success rate")
    ax.set_title("Stage 4.7: Success rate by goal × condition")
    ax.set_ylim(0, 1.05)
    ax.legend(loc="upper right", fontsize=9)
    ax.axhline(0.5, color="gray", linewidth=0.8, linestyle="--", alpha=0.5)

    # Right: Stage 4.8 success rates by goal and condition
    ax = axes[1]
    conds_48 = [("A", "#2980b9"), ("D", "#e67e22"), ("F", "#8e44ad")]
    for i, (c, col) in enumerate(conds_48):
        rates = []
        for r in rows:
            v = r.get(f"s48_{c}_rate", float("nan"))
            rates.append(float(v) if not math.isnan(float(v)) else 0.0)
        ax.bar(x + i * width - 1.0 * width, rates, width, label=f"Cond {c}", color=col, alpha=0.85)

    # Highlight matched-cell goals
    for i, r in enumerate(rows):
        if r.get("is_current_matched_cell_goal"):
            ax.axvspan(i - 0.45, i + 0.45, alpha=0.08, color="green")

    ax.set_xticks(x)
    ax.set_xticklabels([f"Goal {g}" for g in goals])
    ax.set_ylabel("Stochastic success rate (5 seeds)")
    ax.set_title("Stage 4.8: Success rate by goal × condition\n(shaded = matched-outcome cell)")
    ax.set_ylim(0, 1.05)
    ax.legend(loc="upper right", fontsize=9)
    ax.axhline(0.5, color="gray", linewidth=0.8, linestyle="--", alpha=0.5)

    plt.tight_layout()
    fig_path = os.path.join(FIG_DIR, "07_goal_susceptibility_map.png")
    plt.savefig(fig_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"\nSaved figure: {fig_path}")
except ImportError:
    print("\nmatplotlib not available; skipping figure generation")
    fig_path = None

print("\nDone.")
