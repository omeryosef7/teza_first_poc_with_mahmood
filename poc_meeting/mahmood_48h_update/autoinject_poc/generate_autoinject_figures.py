"""
Generate all required AutoInject POC figures using PIL.
Run after all analysis scripts have produced their CSVs.
"""

import csv
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from pil_plot_utils import draw_bar_chart, draw_grouped_bar_chart, draw_heatmap

DATASET_PATH = (
    "outputs/meeting/mahmood_48h_update_20260611_143740/autoinject_poc/autoinject_poc_dataset.csv"
)
SENSITIVITY_CSV = (
    "outputs/meeting/mahmood_48h_update_20260611_143740/autoinject_poc/autoinject_reward_sensitivity_grid.csv"
)
OUT_DIR = "outputs/meeting/mahmood_48h_update_20260611_143740/autoinject_poc"


def safe_bool(val):
    if isinstance(val, bool):
        return val
    if isinstance(val, str):
        return val.strip().lower() in ("true", "1")
    return bool(val)


def safe_float(val, default=0.0):
    try:
        return float(val)
    except (TypeError, ValueError):
        return default


def load_csv(path):
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(dict(row))
    return rows


def compute_rewards(rows):
    think_vals = [safe_float(r.get("think_token_count", "0")) for r in rows]
    max_log = math.log1p(max(think_vals)) if max(think_vals) > 0 else 1.0
    for r in rows:
        sr_score = safe_float(r.get("sr_score", "0"))
        sr_success = safe_bool(r.get("sr_success", False))
        think = safe_float(r.get("think_token_count", "0"))
        censored = safe_bool(r.get("censored", False))
        onset = safe_float(r.get("onset_percent", "0"))
        log_think_norm = math.log1p(think) / max_log if max_log > 0 else 0.0
        r["reward_asr"] = float(sr_success)
        r["reward_sr_score"] = sr_score
        r["reward_combined"] = sr_score + 0.1 * onset + 0.1 * log_think_norm - 0.5 * float(censored)
    return rows


def gen_policy_rewards_figure(rows):
    """fig_autoinject_policy_rewards.png: Mean reward by condition for 3 reward definitions."""
    reward_keys = ["reward_asr", "reward_sr_score", "reward_combined"]
    reward_labels = ["ASR (binary)", "SR Score (continuous)", "Combined reward"]
    conditions = ["A", "D", "F", "E"]

    groups = {}
    for cond in conditions:
        pool = [r for r in rows if r.get("condition") == cond]
        groups[cond] = {}
        for rk, rl in zip(reward_keys, reward_labels):
            if pool:
                groups[cond][rl] = sum(r[rk] for r in pool) / len(pool)
            else:
                groups[cond][rl] = 0.0

    out_path = os.path.join(OUT_DIR, "fig_autoinject_policy_rewards.png")
    draw_grouped_bar_chart(
        groups=groups,
        title="AutoInject Offline Optimization: Mean Reward by Condition",
        subtitle="Offline Replay Mode — NOT a real optimization run",
        xlabel="Structural Condition (A/D/F/E)",
        ylabel="Mean reward",
        output_path=out_path,
        width=800, height=480,
    )
    print(f"Written: {out_path}")


def gen_reward_tradeoffs_figure(rows):
    """fig_autoinject_reward_tradeoffs.png: Scatter-like bar of ASR vs think tokens."""
    conditions = ["A", "D", "F", "E"]
    cond_colors = {
        "A": (76, 175, 80), "D": (33, 150, 243),
        "F": (255, 152, 0), "E": (156, 39, 176),
    }

    # ASR bars with think_token annotation
    cond_asr = {}
    cond_think = {}
    for cond in conditions:
        pool = [r for r in rows if r.get("condition") == cond]
        if pool:
            asr = sum(safe_bool(r.get("sr_success", False)) for r in pool) / len(pool)
            think = sum(safe_float(r.get("think_token_count", "0")) for r in pool) / len(pool) / 1000
            cond_asr[cond] = asr
            cond_think[cond] = think

    out_path = os.path.join(OUT_DIR, "fig_autoinject_reward_tradeoffs.png")
    draw_bar_chart(
        data=cond_asr,
        title="Attack Success Rate (ASR) by Structural Condition",
        subtitle="Note: Condition A also has highest think tokens (~13K). Optimizing length alone risks reward hacking.",
        xlabel="Structural Condition",
        ylabel="ASR",
        output_path=out_path,
        colors=cond_colors,
        y_max=1.0,
        width=650, height=430,
    )
    print(f"Written: {out_path}")


def gen_sensitivity_heatmap():
    """fig_autoinject_reward_selection_heatmap.png: heatmap of best condition per weight combo."""
    if not os.path.exists(SENSITIVITY_CSV):
        print(f"Sensitivity CSV not yet available: {SENSITIVITY_CSV}")
        return

    rows = load_csv(SENSITIVITY_CSV)
    if not rows:
        return

    # Build: (alpha_onset, alpha_thinking) -> best condition for reward_combined
    # Use beta_censoring=0.5 slice
    a_onset_vals = sorted(set(safe_float(r.get("alpha_onset", "0")) for r in rows))
    a_think_vals = sorted(set(safe_float(r.get("alpha_thinking", "0")) for r in rows))
    cond_to_num = {"A": 4, "D": 3, "F": 2, "E": 1, "?": 0}

    # Filter to beta_censoring=0.5
    filtered = [r for r in rows if abs(safe_float(r.get("beta_censoring", "0")) - 0.5) < 0.01]

    matrix = []
    row_labels = []
    for ao in a_onset_vals:
        row_vals = []
        row_labels.append(f"α_onset={ao}")
        for at in a_think_vals:
            match = [r for r in filtered
                     if abs(safe_float(r.get("alpha_onset","0")) - ao) < 0.01
                     and abs(safe_float(r.get("alpha_thinking","0")) - at) < 0.01]
            if match:
                best_cond = match[0].get("best_condition_combined", "?")
                row_vals.append(float(cond_to_num.get(best_cond, 0)))
            else:
                row_vals.append(0.0)
        matrix.append(row_vals)

    col_labels = [f"α_think={v}" for v in a_think_vals]

    out_path = os.path.join(OUT_DIR, "fig_autoinject_reward_selection_heatmap.png")
    draw_heatmap(
        matrix=matrix,
        row_labels=row_labels,
        col_labels=col_labels,
        title="Best Condition by Reward Weights (b_censor=0.5) [4=A 3=D 2=F 1=E]",
        output_path=out_path,
        colormap="blues",
        annotation_format=".0f",
        width=700, height=500,
    )
    print(f"Written: {out_path}")


def gen_manual_onset_placeholder():
    """fig_manual_vs_heuristic_onset.png: placeholder until annotations are done."""
    out_path = os.path.join(
        "outputs/meeting/mahmood_48h_update_20260611_143740",
        "fig_manual_vs_heuristic_onset.png"
    )
    if os.path.exists(out_path):
        return

    data = {
        "first_engagement\n(correct)": 0,
        "after_engagement\n(too early)": 0,
        "before_first\n(too late)": 0,
        "no_engagement": 0,
        "unclear": 0,
    }
    draw_bar_chart(
        data={"correct": 0, "too_early": 0, "too_late": 0, "no_engage": 0, "unclear": 0},
        title="Manual vs. Heuristic Onset Annotation",
        subtitle="[Pending — fill in manual_onset_review_subset_30_40.csv and re-run analyze_manual_onset_annotations.py]",
        xlabel="Label",
        ylabel="Count",
        output_path=out_path,
        width=600, height=380,
    )
    print(f"Written (placeholder): {out_path}")


def main():
    rows = load_csv(DATASET_PATH)
    rows = compute_rewards(rows)

    gen_policy_rewards_figure(rows)
    gen_reward_tradeoffs_figure(rows)
    gen_sensitivity_heatmap()
    gen_manual_onset_placeholder()


if __name__ == "__main__":
    main()
