"""
Stage 4.7 — Meeting-quality figures from replication results.

Requires:
  - outputs/stage4_7/runs/<run_timestamp>/analysis/condition_summary.csv
  - outputs/stage4_7/runs/<run_timestamp>/analysis/paired_contrasts.csv
  - outputs/stage4_7/runs/<run_timestamp>/analysis/goal_stratified_summary.csv
  - outputs/stage4_7/runs/<run_timestamp>/analysis/bootstrap_cis.json
  - outputs/stage4_7/runs/<run_timestamp>/analysis/sign_tests.json
  - (optional) analysis/mechanistic_summary.csv  for figs 5,6,8

Produces 9 PNGs in:
  outputs/stage4_7/runs/<run_timestamp>/plots/

Usage:
  python -m poc_stage4_7.plot_replication
      --run-dir outputs/stage4_7/runs/<run_timestamp>
      [--analysis-dir PATH]
      [--output-dir PATH]
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

CONDITIONS = ["A", "D", "F", "E"]
CONDITION_LABELS = {
    "A": "A: Full puzzle\n(thinking=on)",
    "D": "D: No puzzle\n(thinking=on)",
    "F": "F: Benign wrapper\n(thinking=on)",
    "E": "E: Full puzzle\n(thinking=off)",
}
CONDITION_COLORS = {
    "A": "#2166ac",
    "D": "#4dac26",
    "F": "#d01c8b",
    "E": "#f4a582",
}
SR_THRESHOLD = 0.5
DPI = 150
FIGSIZE_WIDE = (10, 5)
FIGSIZE_SQUARE = (7, 6)
FIGSIZE_TALL = (8, 8)


def _load_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _f(x, default=float("nan")):
    try:
        return float(x)
    except (TypeError, ValueError):
        return default


def _save(fig, path: Path, title_for_log: str) -> None:
    fig.savefig(path, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved {path.name}  [{title_for_log}]")


def _watermark(ax, text="Stage 4.7 — diagnostic only"):
    ax.annotate(
        text, xy=(0.99, 0.01), xycoords="axes fraction",
        ha="right", va="bottom", fontsize=6, color="gray", alpha=0.7,
    )


# ---------------------------------------------------------------------------
# Fig 1: SR score and success by condition
# ---------------------------------------------------------------------------
def fig1_behavior_by_condition(cond_summary: list[dict], out_dir: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=FIGSIZE_WIDE)

    conds = [r for cond in CONDITIONS for r in cond_summary if r["condition"] == cond]
    labels = [CONDITION_LABELS.get(r["condition"], r["condition"]).replace("\n", " ") for r in conds]
    colors = [CONDITION_COLORS.get(r["condition"], "gray") for r in conds]
    x = np.arange(len(conds))

    # Panel left: success rate
    ax = axes[0]
    success_rates = [_f(r.get("sr_success_rate")) for r in conds]
    n_success = [int(_f(r.get("n_sr_success"), 0)) for r in conds]
    n_total = [int(_f(r.get("n"), 0)) for r in conds]
    bars = ax.bar(x, success_rates, color=colors, alpha=0.85, edgecolor="black", linewidth=0.7)
    ax.axhline(y=0, color="black", linewidth=0.5)
    for xi, b, ns, nt in zip(x, bars, n_success, n_total):
        ax.text(xi, b.get_height() + 0.02, f"{ns}/{nt}", ha="center", va="bottom", fontsize=9, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=9)
    ax.set_ylabel("SR Success Rate", fontsize=10)
    ax.set_ylim(0, 1.3)
    ax.set_title("SR Success Rate by Condition", fontsize=11, fontweight="bold")
    ax.axhline(y=SR_THRESHOLD, color="gray", linestyle="--", linewidth=0.8, alpha=0.6, label=f"Threshold ({SR_THRESHOLD})")
    ax.legend(fontsize=8)
    _watermark(ax)

    # Panel right: mean SR score with CI
    ax = axes[1]
    means = [_f(r.get("mean_sr_score")) for r in conds]
    ci_lo = [_f(r.get("ci_low_95_sr_score")) for r in conds]
    ci_hi = [_f(r.get("ci_high_95_sr_score")) for r in conds]
    yerr_lo = [max(0, m - lo) if not math.isnan(m) and not math.isnan(lo) else 0 for m, lo in zip(means, ci_lo)]
    yerr_hi = [max(0, hi - m) if not math.isnan(m) and not math.isnan(hi) else 0 for m, hi in zip(means, ci_hi)]
    bars = ax.bar(x, means, color=colors, alpha=0.85, edgecolor="black", linewidth=0.7)
    ax.errorbar(x, means, yerr=[yerr_lo, yerr_hi], fmt="none", color="black", capsize=4, linewidth=1.2)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=9)
    ax.set_ylabel("Mean StrongREJECT Score", fontsize=10)
    ax.set_ylim(0, 1.2)
    ax.set_title("Mean SR Score by Condition\n(bootstrap 95% CI, n=12 prompts)", fontsize=11, fontweight="bold")
    ax.axhline(y=SR_THRESHOLD, color="gray", linestyle="--", linewidth=0.8, alpha=0.6, label=f"Threshold")
    ax.legend(fontsize=8)
    _watermark(ax)

    fig.suptitle("Stage 4.7 — Behavioral Outcomes by Condition", fontsize=12, fontweight="bold", y=1.01)
    fig.tight_layout()
    _save(fig, out_dir / "fig1_behavior_by_condition.png", "behavioral overview")


# ---------------------------------------------------------------------------
# Fig 2: Thinking length by condition (log scale)
# ---------------------------------------------------------------------------
def fig2_thinking_length_by_condition(cond_summary: list[dict], paired_contrasts: list[dict], out_dir: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=FIGSIZE_WIDE)

    # Left: strip plot with per-prompt points for A, D, F
    ax = axes[0]
    think_conds = ["A", "D", "F"]
    source_ids = list(dict.fromkeys(r.get("source_example_id") for r in paired_contrasts))
    for xi, cond in enumerate(think_conds):
        color = CONDITION_COLORS[cond]
        vals = []
        for sid in source_ids:
            r = next((row for row in paired_contrasts
                      if row.get("source_example_id") == sid and row.get("cond_ref") == cond
                      and row.get("contrast") == "A_vs_D"), None)
            if r is None:
                r = next((row for row in paired_contrasts
                          if row.get("source_example_id") == sid and row.get("cond_comp") == cond
                          and row.get("contrast") == "A_vs_D"), None)
            if r:
                if cond == "A":
                    v = _f(r.get("think_tokens_ref"))
                else:
                    v = _f(r.get("think_tokens_comp"))
                if not math.isnan(v) and v > 0:
                    vals.append(v)

        jitter = np.random.default_rng(42).uniform(-0.15, 0.15, size=len(vals))
        ax.scatter(xi + jitter, vals, color=color, alpha=0.7, s=40, zorder=3)
        mean_v = np.mean(vals) if vals else None
        if mean_v:
            ax.hlines(mean_v, xi - 0.3, xi + 0.3, colors=color, linewidths=2.5, linestyles="-", zorder=4)

    ax.set_xticks([0, 1, 2])
    ax.set_xticklabels(["A: Full puzzle", "D: No puzzle", "F: Benign wrapper"], fontsize=9)
    ax.set_ylabel("Think-phase Token Count", fontsize=10)
    ax.set_yscale("log")
    ax.set_title("Think Tokens (log scale)\nper source prompt, thinking-on conditions", fontsize=10, fontweight="bold")
    ax.set_ylim(bottom=10)
    _watermark(ax)

    # Right: bar chart with mean thinking tokens for all conditions from summary
    ax = axes[1]
    conds = [r for cond in CONDITIONS for r in cond_summary if r["condition"] == cond]
    labels = [CONDITION_LABELS.get(r["condition"], r["condition"]).replace("\n", " ") for r in conds]
    colors = [CONDITION_COLORS.get(r["condition"], "gray") for r in conds]
    x = np.arange(len(conds))
    means = [_f(r.get("mean_think_tokens")) for r in conds]
    means_safe = [max(1, m) if not math.isnan(m) else 0 for m in means]
    bars = ax.bar(x, means_safe, color=colors, alpha=0.85, edgecolor="black", linewidth=0.7)
    for xi, b, m in zip(x, bars, means):
        label = f"{int(m):,}" if not math.isnan(m) else "n/a"
        ax.text(xi, b.get_height() * 1.05, label, ha="center", va="bottom", fontsize=8)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=9)
    ax.set_ylabel("Mean Think Tokens (log scale)", fontsize=10)
    ax.set_yscale("log")
    ax.set_ylim(bottom=1)
    ax.set_title("Mean Think Tokens by Condition\n(E shows 0 — no thinking phase)", fontsize=10, fontweight="bold")
    _watermark(ax)

    fig.suptitle("Stage 4.7 — Thinking Length Analysis", fontsize=12, fontweight="bold", y=1.01)
    fig.tight_layout()
    _save(fig, out_dir / "fig2_thinking_length_by_condition.png", "thinking tokens")


# ---------------------------------------------------------------------------
# Fig 3: Full vs bare vs length-matched (A, D, F direct comparison)
# ---------------------------------------------------------------------------
def fig3_full_vs_bare_vs_length_matched(paired_contrasts: list[dict], out_dir: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=FIGSIZE_WIDE)

    source_ids = sorted(set(r.get("source_example_id") for r in paired_contrasts))

    # Build per-source score dict for A, D, F
    scores: dict[str, dict[str, float]] = {sid: {} for sid in source_ids}
    for r in paired_contrasts:
        sid = r.get("source_example_id")
        c1, c2 = r.get("cond_ref"), r.get("cond_comp")
        s1 = _f(r.get("score_ref"))
        s2 = _f(r.get("score_comp"))
        if sid:
            if not math.isnan(s1):
                scores[sid][c1] = s1
            if not math.isnan(s2):
                scores[sid][c2] = s2

    # Paired line plot: A vs D
    ax = axes[0]
    for sid in source_ids:
        sa = scores.get(sid, {}).get("A")
        sd = scores.get(sid, {}).get("D")
        sf = scores.get(sid, {}).get("F")
        if sa is not None and sd is not None:
            ax.plot([0, 1], [sa, sd], "o-", color="gray", alpha=0.5, linewidth=1)
        if sa is not None and sf is not None:
            ax.plot([0, 2], [sa, sf], "o--", color="gray", alpha=0.3, linewidth=0.8)

    for xi, cond in enumerate(["A", "D", "F"]):
        vals = [scores[sid].get(cond) for sid in source_ids if scores[sid].get(cond) is not None]
        if vals:
            ax.scatter([xi] * len(vals), vals, color=CONDITION_COLORS[cond], s=60, zorder=5, alpha=0.85)
            ax.hlines(np.mean(vals), xi - 0.25, xi + 0.25, colors=CONDITION_COLORS[cond], linewidths=2.5)

    ax.set_xticks([0, 1, 2])
    ax.set_xticklabels(["A\nFull puzzle", "D\nNo puzzle", "F\nBenign wrap"], fontsize=9)
    ax.set_ylabel("StrongREJECT Score", fontsize=10)
    ax.set_ylim(-0.05, 1.15)
    ax.axhline(y=SR_THRESHOLD, color="gray", linestyle="--", linewidth=0.8, alpha=0.5)
    ax.set_title("SR Score: A vs D vs F\n(paired by source prompt)", fontsize=10, fontweight="bold")
    _watermark(ax)

    # Panel right: signed differences A-D and A-F per source
    ax = axes[1]
    ad_diffs = []
    af_diffs = []
    for sid in source_ids:
        sa = scores.get(sid, {}).get("A")
        sd = scores.get(sid, {}).get("D")
        sf = scores.get(sid, {}).get("F")
        if sa is not None and sd is not None:
            ad_diffs.append(sa - sd)
        if sa is not None and sf is not None:
            af_diffs.append(sa - sf)

    x = np.arange(len(source_ids[:len(ad_diffs)]))
    width = 0.35
    ax.bar(x - width / 2, ad_diffs[:len(x)], width=width, color=CONDITION_COLORS["D"], alpha=0.8, label="A − D", edgecolor="black", linewidth=0.5)
    ax.bar(x + width / 2, af_diffs[:len(x)], width=width, color=CONDITION_COLORS["F"], alpha=0.8, label="A − F", edgecolor="black", linewidth=0.5)
    ax.axhline(y=0, color="black", linewidth=1)
    ax.set_xlabel("Source Prompt (index)", fontsize=9)
    ax.set_ylabel("Score Difference (A minus comparison)", fontsize=10)
    ax.set_title("Paired Differences: A−D and A−F\n(positive = A scores higher)", fontsize=10, fontweight="bold")
    ax.legend(fontsize=9)
    _watermark(ax)

    fig.suptitle("Stage 4.7 — Full Puzzle vs No Puzzle vs Benign Wrapper", fontsize=12, fontweight="bold", y=1.01)
    fig.tight_layout()
    _save(fig, out_dir / "fig3_full_vs_bare_vs_length_matched.png", "A vs D vs F")


# ---------------------------------------------------------------------------
# Fig 4: Thinking on vs off (A vs E)
# ---------------------------------------------------------------------------
def fig4_thinking_on_vs_off(paired_contrasts: list[dict], out_dir: Path) -> None:
    ae_rows = [r for r in paired_contrasts if r.get("contrast") == "A_vs_E"]
    if not ae_rows:
        print("  Skipping fig4 — no A_vs_E rows")
        return

    fig, axes = plt.subplots(1, 2, figsize=FIGSIZE_WIDE)

    source_ids = [r.get("source_example_id") for r in ae_rows]
    scores_a = [_f(r.get("score_ref")) for r in ae_rows]
    scores_e = [_f(r.get("score_comp")) for r in ae_rows]
    success_a = [r.get("sr_success_ref") for r in ae_rows]
    success_e = [r.get("sr_success_comp") for r in ae_rows]

    # Paired score lines
    ax = axes[0]
    for i, (sa, se) in enumerate(zip(scores_a, scores_e)):
        if math.isnan(sa) or math.isnan(se):
            continue
        color = "crimson" if sa > se else ("steelblue" if se > sa else "gray")
        ax.plot([0, 1], [sa, se], "o-", color=color, alpha=0.6, linewidth=1.4)
    valid_a = [s for s in scores_a if not math.isnan(s)]
    valid_e = [s for s in scores_e if not math.isnan(s)]
    if valid_a:
        ax.hlines(np.mean(valid_a), -0.2, 0.2, colors=CONDITION_COLORS["A"], linewidths=3, zorder=5)
    if valid_e:
        ax.hlines(np.mean(valid_e), 0.8, 1.2, colors=CONDITION_COLORS["E"], linewidths=3, zorder=5)
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["A: Full puzzle\nthinking=on", "E: Full puzzle\nthinking=off"], fontsize=10)
    ax.set_ylabel("StrongREJECT Score", fontsize=10)
    ax.set_ylim(-0.05, 1.15)
    ax.axhline(y=SR_THRESHOLD, color="gray", linestyle="--", linewidth=0.8, alpha=0.5)
    ax.set_title("SR Score: A vs E\n(paired by source prompt)", fontsize=10, fontweight="bold")
    patches = [
        mpatches.Patch(color="crimson", label="A > E (thinking helps)", alpha=0.7),
        mpatches.Patch(color="steelblue", label="E > A (thinking hurts)", alpha=0.7),
        mpatches.Patch(color="gray", label="Tied", alpha=0.7),
    ]
    ax.legend(handles=patches, fontsize=8)
    _watermark(ax)

    # Success outcome table
    ax = axes[1]
    outcomes = {
        "A=✓ E=✓": sum(1 for sa, se in zip(success_a, success_e) if str(sa).lower() in ("true","1") and str(se).lower() in ("true","1")),
        "A=✓ E=✗": sum(1 for sa, se in zip(success_a, success_e) if str(sa).lower() in ("true","1") and str(se).lower() not in ("true","1")),
        "A=✗ E=✓": sum(1 for sa, se in zip(success_a, success_e) if str(sa).lower() not in ("true","1") and str(se).lower() in ("true","1")),
        "A=✗ E=✗": sum(1 for sa, se in zip(success_a, success_e) if str(sa).lower() not in ("true","1") and str(se).lower() not in ("true","1")),
    }
    ax.bar(range(len(outcomes)), list(outcomes.values()), color=["#2166ac", "#d73027", "#fdae61", "#4dac26"], edgecolor="black", linewidth=0.7)
    ax.set_xticks(range(len(outcomes)))
    ax.set_xticklabels(list(outcomes.keys()), fontsize=9, rotation=15)
    ax.set_ylabel("Count", fontsize=10)
    ax.set_title("McNemar contingency table\n(success binary, n pairs)", fontsize=10, fontweight="bold")
    ax.set_yticks(range(0, max(outcomes.values()) + 2))
    _watermark(ax)

    fig.suptitle("Stage 4.7 — Thinking On vs Thinking Off", fontsize=12, fontweight="bold", y=1.01)
    fig.tight_layout()
    _save(fig, out_dir / "fig4_thinking_on_vs_off.png", "A vs E")


# ---------------------------------------------------------------------------
# Fig 5: Layer 22 early projection
# ---------------------------------------------------------------------------
def fig5_layer22_early_projection(mech_rows: list[dict], out_dir: Path) -> None:
    if not mech_rows:
        print("  Skipping fig5 — no mechanistic data")
        return

    fig, axes = plt.subplots(1, 2, figsize=FIGSIZE_WIDE)

    metric_keys = [("layer22_first_500_mean_projection", "First 500 tokens"), ("layer22_first_2000_mean_projection", "First 2000 tokens")]
    for ax, (key, label) in zip(axes, metric_keys):
        for cond in ["A", "D", "F"]:
            vals = [_f(r.get(key)) for r in mech_rows if r.get("condition") == cond]
            vals = [v for v in vals if not math.isnan(v)]
            if not vals:
                continue
            jitter = np.random.default_rng(7).uniform(-0.12, 0.12, size=len(vals))
            xi = ["A", "D", "F"].index(cond)
            ax.scatter(xi + jitter, vals, color=CONDITION_COLORS[cond], s=50, alpha=0.75, zorder=3)
            ax.hlines(np.mean(vals), xi - 0.25, xi + 0.25, colors=CONDITION_COLORS[cond], linewidths=2.5)

        ax.set_xticks([0, 1, 2])
        ax.set_xticklabels(["A: Full puzzle", "D: No puzzle", "F: Benign wrap"], fontsize=9)
        ax.set_ylabel("Layer 22 Projection (a.u.)", fontsize=10)
        ax.axhline(y=0, color="black", linewidth=0.5, linestyle="--", alpha=0.4)
        ax.set_title(f"L22 projection — {label}", fontsize=10, fontweight="bold")
        _watermark(ax)

    fig.suptitle("Stage 4.7 — Layer 22 Early Projection\n[DIAGNOSTIC ONLY — provisional direction]",
                 fontsize=11, fontweight="bold", y=1.01)
    fig.tight_layout()
    _save(fig, out_dir / "fig5_layer22_early_projection.png", "L22 early projection")


# ---------------------------------------------------------------------------
# Fig 6: Layer 22 normalized trajectory (10 bins)
# ---------------------------------------------------------------------------
def fig6_layer22_normalized_trajectory(mech_rows: list[dict], out_dir: Path) -> None:
    if not mech_rows:
        print("  Skipping fig6 — no mechanistic data")
        return

    fig, ax = plt.subplots(figsize=FIGSIZE_SQUARE)
    n_bins = 10
    for cond in ["A", "D", "F"]:
        cond_rows = [r for r in mech_rows if r.get("condition") == cond]
        bin_means = []
        bin_sems = []
        for b in range(1, n_bins + 1):
            key = f"layer22_normalized_bin_{b}"
            vals = [_f(r.get(key)) for r in cond_rows]
            vals = [v for v in vals if not math.isnan(v)]
            if vals:
                bin_means.append(np.mean(vals))
                bin_sems.append(np.std(vals) / math.sqrt(len(vals)))
            else:
                bin_means.append(None)
                bin_sems.append(None)
        x = np.arange(1, n_bins + 1)
        valid = [(xi, m, s) for xi, m, s in zip(x, bin_means, bin_sems) if m is not None]
        if not valid:
            continue
        xv, mv, sv = zip(*valid)
        ax.plot(xv, mv, "o-", color=CONDITION_COLORS[cond], label=CONDITION_LABELS[cond].replace("\n", " "), linewidth=1.8, markersize=5)
        ax.fill_between(xv, np.array(mv) - np.array(sv), np.array(mv) + np.array(sv),
                        color=CONDITION_COLORS[cond], alpha=0.2)

    ax.set_xlabel("Normalized Position (decile)", fontsize=10)
    ax.set_ylabel("Layer 22 Projection (a.u.)", fontsize=10)
    ax.axhline(y=0, color="black", linewidth=0.5, linestyle="--", alpha=0.4)
    ax.set_title("Layer 22 Projection — Normalized Trajectory\n(mean ± 1 SE across source prompts, conditions A/D/F)\n"
                 "[DIAGNOSTIC ONLY — provisional direction]", fontsize=10, fontweight="bold")
    ax.legend(fontsize=9)
    ax.set_xticks(range(1, n_bins + 1))
    ax.set_xticklabels([f"{b*10}%" for b in range(1, n_bins + 1)], fontsize=8)
    _watermark(ax)
    fig.tight_layout()
    _save(fig, out_dir / "fig6_layer22_normalized_trajectory.png", "L22 normalized trajectory")


# ---------------------------------------------------------------------------
# Fig 7: Per-goal × condition heatmap
# ---------------------------------------------------------------------------
def fig7_per_goal_condition_heatmap(goal_strat: list[dict], out_dir: Path) -> None:
    if not goal_strat:
        print("  Skipping fig7 — no goal_stratified data")
        return

    goals = sorted(set(int(r["goal_index"]) for r in goal_strat))
    matrix = np.full((len(goals), len(CONDITIONS)), np.nan)
    success_matrix = np.full((len(goals), len(CONDITIONS)), np.nan)
    for r in goal_strat:
        gi = goals.index(int(r["goal_index"]))
        ci = CONDITIONS.index(r["condition"]) if r["condition"] in CONDITIONS else -1
        if ci < 0:
            continue
        matrix[gi, ci] = _f(r.get("mean_sr_score"))
        ns = int(_f(r.get("n_sr_success"), 0))
        n = int(_f(r.get("n"), 0))
        success_matrix[gi, ci] = ns

    fig, ax = plt.subplots(figsize=(8, 4))
    im = ax.imshow(matrix, aspect="auto", cmap="RdYlGn", vmin=0.0, vmax=1.0)
    plt.colorbar(im, ax=ax, label="Mean StrongREJECT Score")
    for i in range(len(goals)):
        for j in range(len(CONDITIONS)):
            val = matrix[i, j]
            ns_val = success_matrix[i, j]
            n_total_rows = [r for r in goal_strat if int(r["goal_index"]) == goals[i] and r["condition"] == CONDITIONS[j]]
            n_total = int(_f(n_total_rows[0].get("n"), 0)) if n_total_rows else 0
            if not math.isnan(val):
                label = f"{val:.2f}\n({int(ns_val)}/{n_total})"
                ax.text(j, i, label, ha="center", va="center", fontsize=8,
                        color="black" if 0.3 < val < 0.7 else ("white" if val < 0.3 else "black"))
    ax.set_xticks(range(len(CONDITIONS)))
    ax.set_xticklabels([CONDITION_LABELS[c].replace("\n", " ") for c in CONDITIONS], fontsize=9)
    ax.set_yticks(range(len(goals)))
    ax.set_yticklabels([f"Goal {g}" for g in goals], fontsize=9)
    ax.set_title("Stage 4.7 — Per-Goal × Condition SR Score Heatmap\n(mean score, n_success/n_prompts in cell)",
                 fontsize=10, fontweight="bold")
    _watermark(ax)
    fig.tight_layout()
    _save(fig, out_dir / "fig7_per_goal_condition_heatmap.png", "goal×condition heatmap")


# ---------------------------------------------------------------------------
# Fig 8: Projection vs thinking length scatter
# ---------------------------------------------------------------------------
def fig8_projection_vs_thinking_length(mech_rows: list[dict], out_dir: Path) -> None:
    if not mech_rows:
        print("  Skipping fig8 — no mechanistic data")
        return

    fig, axes = plt.subplots(1, 2, figsize=FIGSIZE_WIDE)

    for ax, (proj_key, xlabel) in zip(axes, [
        ("layer22_think_phase_mean_projection", "Think-phase mean L22 projection"),
        ("layer22_last_500_think_mean_projection", "Last-500 think tokens L22 projection"),
    ]):
        for cond in ["A", "D", "F"]:
            cond_rows = [r for r in mech_rows if r.get("condition") == cond]
            xs = []
            ys = []
            for r in cond_rows:
                proj = _f(r.get(proj_key))
                think = _f(r.get("think_token_count", 0))
                if not math.isnan(proj) and not math.isnan(think) and think > 0:
                    xs.append(math.log10(think))
                    ys.append(proj)
            if xs:
                ax.scatter(xs, ys, color=CONDITION_COLORS[cond], label=cond, s=50, alpha=0.75)
        ax.set_xlabel("log₁₀(think_token_count)", fontsize=10)
        ax.set_ylabel(xlabel, fontsize=9)
        ax.set_title(f"L22 Projection vs log(think tokens)\n[diagnostic only]", fontsize=10, fontweight="bold")
        ax.legend(fontsize=9)
        _watermark(ax)

    fig.suptitle("Stage 4.7 — Projection vs Thinking Length\n[DIAGNOSTIC ONLY — provisional direction]",
                 fontsize=11, fontweight="bold", y=1.01)
    fig.tight_layout()
    _save(fig, out_dir / "fig8_projection_vs_thinking_length.png", "projection vs thinking length")


# ---------------------------------------------------------------------------
# Fig 9: Finish reason and truncation
# ---------------------------------------------------------------------------
def fig9_finish_reason_and_truncation(paired_contrasts: list[dict], cond_summary: list[dict], out_dir: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=FIGSIZE_WIDE)

    # Panel left: n_truncated per condition from summary
    ax = axes[0]
    conds = [r for cond in CONDITIONS for r in cond_summary if r["condition"] == cond]
    labels = [r["condition"] for r in conds]
    n_total = [int(_f(r.get("n"), 0)) for r in conds]
    n_truncated = [int(_f(r.get("n_truncated"), 0)) for r in conds]
    n_ok = [nt - nc for nt, nc in zip(n_total, n_truncated)]
    colors = [CONDITION_COLORS.get(r["condition"], "gray") for r in conds]
    x = np.arange(len(conds))

    ax.bar(x, n_ok, label="eos_token (complete)", color=colors, alpha=0.85, edgecolor="black", linewidth=0.7)
    ax.bar(x, n_truncated, bottom=n_ok, label="max_new_tokens (truncated)", color="crimson", alpha=0.7, edgecolor="black", linewidth=0.7)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=10)
    ax.set_ylabel("Count", fontsize=10)
    ax.set_title("Finish Reason by Condition\n(truncated = hit max_new_tokens)", fontsize=10, fontweight="bold")
    ax.legend(fontsize=8)
    _watermark(ax)

    # Panel right: SR score for truncated vs non-truncated rows
    ax = axes[1]
    for cond in CONDITIONS:
        cond_contrast_rows = [r for r in paired_contrasts if r.get("cond_ref") == cond]
        if not cond_contrast_rows:
            cond_contrast_rows = [r for r in paired_contrasts if r.get("cond_comp") == cond]
        for xi, (label, fr_val) in enumerate([("eos_token", "eos_token"), ("max_new_tokens", "max_new_tokens")]):
            matching = [
                _f(r.get("score_ref") if r.get("cond_ref") == cond else r.get("score_comp"))
                for r in paired_contrasts
                if (r.get("cond_ref") == cond and r.get("finish_reason_ref") == fr_val)
                or (r.get("cond_comp") == cond and r.get("finish_reason_comp") == fr_val)
            ]
            matching = [v for v in matching if not math.isnan(v)]
            if matching:
                ax.scatter([xi + ["A", "D", "F", "E"].index(cond) * 0.1], [np.mean(matching)],
                           color=CONDITION_COLORS[cond], marker="o" if fr_val == "eos_token" else "x",
                           s=80, alpha=0.8, zorder=5)

    ax.set_xticks([0, 1])
    ax.set_xticklabels(["eos_token\n(complete)", "max_new_tokens\n(truncated)"], fontsize=9)
    ax.set_ylabel("Mean SR Score", fontsize=10)
    ax.set_ylim(-0.05, 1.15)
    ax.axhline(y=SR_THRESHOLD, color="gray", linestyle="--", linewidth=0.8, alpha=0.5)
    ax.set_title("SR Score by Finish Reason\n(per condition, dot=mean)", fontsize=10, fontweight="bold")
    patches = [mpatches.Patch(color=CONDITION_COLORS[c], label=c) for c in CONDITIONS]
    ax.legend(handles=patches, fontsize=8)
    _watermark(ax)

    fig.suptitle("Stage 4.7 — Truncation Analysis", fontsize=12, fontweight="bold", y=1.01)
    fig.tight_layout()
    _save(fig, out_dir / "fig9_finish_reason_and_truncation.png", "finish reason & truncation")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Plot Stage 4.7 replication figures.")
    p.add_argument("--run-dir", type=Path, required=True)
    p.add_argument("--analysis-dir", type=Path, default=None)
    p.add_argument("--output-dir", type=Path, default=None)
    args = p.parse_args(argv)

    run_dir = args.run_dir
    analysis_dir = args.analysis_dir or (run_dir / "analysis")
    out_dir = args.output_dir or (run_dir / "plots")
    out_dir.mkdir(parents=True, exist_ok=True)

    # Load tables
    cond_summary = _load_csv(analysis_dir / "condition_summary.csv")
    paired_contrasts = _load_csv(analysis_dir / "paired_contrasts.csv")
    goal_strat = _load_csv(analysis_dir / "goal_stratified_summary.csv")
    mech_rows = _load_csv(analysis_dir / "mechanistic_summary.csv")

    if not cond_summary:
        print(f"ERROR: {analysis_dir / 'condition_summary.csv'} not found. Run analyze_replication.py first.")
        return 1

    print(f"Loaded: {len(cond_summary)} condition rows, {len(paired_contrasts)} contrast rows, "
          f"{len(goal_strat)} goal-strat rows, {len(mech_rows)} mechanistic rows")
    print(f"Output dir: {out_dir}")
    print()

    fig1_behavior_by_condition(cond_summary, out_dir)
    fig2_thinking_length_by_condition(cond_summary, paired_contrasts, out_dir)
    fig3_full_vs_bare_vs_length_matched(paired_contrasts, out_dir)
    fig4_thinking_on_vs_off(paired_contrasts, out_dir)
    fig5_layer22_early_projection(mech_rows, out_dir)
    fig6_layer22_normalized_trajectory(mech_rows, out_dir)
    fig7_per_goal_condition_heatmap(goal_strat, out_dir)
    fig8_projection_vs_thinking_length(mech_rows, out_dir)
    fig9_finish_reason_and_truncation(paired_contrasts, cond_summary, out_dir)

    print(f"\nAll figures written to {out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
