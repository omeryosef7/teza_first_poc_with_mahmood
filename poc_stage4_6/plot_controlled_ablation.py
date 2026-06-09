"""
Stage 4.6 — Plot controlled ablation results.

Reads analysis CSVs produced by analyze_controlled_ablation.py and
produces 8 plots under outputs/stage4_6/runs_output/plots/.

Reuses matplotlib style from existing Stage 4.5 plot code.

Usage:
  python -m poc_stage4_6.plot_controlled_ablation [--run-dir PATH] [--output-dir PATH]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from poc_stage4_5 import common

_OUTPUT_BASE = _REPO_ROOT / "outputs" / "stage4_6"
CONDITIONS = ["A", "B", "C", "D", "E"]
CONDITION_LABELS = {
    "A": "Full\n(think on)",
    "B": "50%\n(think on)",
    "C": "25%\n(think on)",
    "D": "None\n(think on)",
    "E": "Full\n(think off)",
}
COLORS = {
    "A": "#2196F3",
    "B": "#4CAF50",
    "C": "#FF9800",
    "D": "#F44336",
    "E": "#9C27B0",
}


def _setup_style() -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "axes.grid": True,
        "grid.alpha": 0.4,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "font.size": 11,
        "axes.titlesize": 12,
        "axes.labelsize": 11,
    })


def _read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return common.read_csv_as_list(path)


def _to_float(v: Any) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return float("nan")


def _to_bool(v: Any) -> bool | None:
    if v in (True, "True", "true", 1, "1"):
        return True
    if v in (False, "False", "false", 0, "0"):
        return False
    return None


def plot_all(run_dir: Path, output_dir: Path) -> None:
    _setup_style()
    import matplotlib.pyplot as plt

    output_dir.mkdir(parents=True, exist_ok=True)

    analysis_dir = run_dir / "analysis"
    cond_summary = _read_csv(analysis_dir / "condition_summary.csv")
    goal_cond = _read_csv(analysis_dir / "goal_condition_summary.csv")
    trend = _read_csv(analysis_dir / "puzzle_fraction_trend.csv")
    per_run = _read_csv(analysis_dir / "per_run_results.csv")
    paired_path = analysis_dir / "paired_comparisons.json"
    paired = json.loads(paired_path.read_text()) if paired_path.exists() else {}

    # -- Plot 1: SR success rate per condition (bar chart) --
    _plot_success_rate_by_condition(cond_summary, output_dir / "p1_sr_success_rate_by_condition.png", plt)
    print("p1_sr_success_rate_by_condition.png")

    # -- Plot 2: Mean StrongREJECT score per condition with 95% CI --
    _plot_sr_score_by_condition(cond_summary, output_dir / "p2_mean_sr_score_by_condition.png", plt)
    print("p2_mean_sr_score_by_condition.png")

    # -- Plot 3: Mean think tokens per condition --
    _plot_think_tokens_by_condition(cond_summary, output_dir / "p3_think_tokens_by_condition.png", plt)
    print("p3_think_tokens_by_condition.png")

    # -- Plot 4: SR success rate per condition, faceted by goal --
    _plot_success_rate_by_goal_condition(goal_cond, output_dir / "p4_sr_success_by_goal_condition.png", plt)
    print("p4_sr_success_by_goal_condition.png")

    # -- Plot 5: StrongREJECT score vs puzzle fraction trend (per source) --
    _plot_sr_score_vs_puzzle_fraction(trend, output_dir / "p5_sr_score_vs_puzzle_fraction.png", plt)
    print("p5_sr_score_vs_puzzle_fraction.png")

    # -- Plot 6: Think tokens vs puzzle fraction trend --
    _plot_think_tokens_vs_puzzle_fraction(trend, output_dir / "p6_think_tokens_vs_puzzle_fraction.png", plt)
    print("p6_think_tokens_vs_puzzle_fraction.png")

    # -- Plot 7: Thinking mode effect — A vs E paired scatter --
    _plot_thinking_mode_scatter(per_run, output_dir / "p7_thinking_mode_A_vs_E_scatter.png", plt)
    print("p7_thinking_mode_A_vs_E_scatter.png")

    # -- Plot 8: Per-source success heatmap (condition × goal) --
    _plot_success_heatmap(per_run, output_dir / "p8_success_heatmap_condition_goal.png", plt)
    print("p8_success_heatmap_condition_goal.png")

    plt.close("all")
    print(f"\nAll plots written to {output_dir}")


def _plot_success_rate_by_condition(rows: list[dict], path: Path, plt: Any) -> None:
    fig, ax = plt.subplots(figsize=(8, 5))
    conds = [r["condition"] for r in rows if r.get("condition")]
    rates = [_to_float(r.get("sr_success_rate", "nan")) for r in rows if r.get("condition")]
    colors = [COLORS.get(c, "#888") for c in conds]
    labels = [CONDITION_LABELS.get(c, c) for c in conds]
    bars = ax.bar(labels, rates, color=colors, edgecolor="white", linewidth=1.5)
    ax.set_ylabel("SR Success Rate")
    ax.set_title("StrongREJECT Success Rate by Ablation Condition\n(Stage 4.6 — LLM-generated exploratory)")
    ax.set_ylim(0, 1.05)
    for bar, rate in zip(bars, rates):
        if not np.isnan(rate):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.02,
                    f"{rate:.2f}", ha="center", va="bottom", fontsize=9)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def _plot_sr_score_by_condition(rows: list[dict], path: Path, plt: Any) -> None:
    fig, ax = plt.subplots(figsize=(8, 5))
    conds = [r["condition"] for r in rows if r.get("condition")]
    means = [_to_float(r.get("mean_strongreject_score", "nan")) for r in rows if r.get("condition")]
    ci_lo = [_to_float(r.get("sr_ci_low", "nan")) for r in rows if r.get("condition")]
    ci_hi = [_to_float(r.get("sr_ci_high", "nan")) for r in rows if r.get("condition")]
    x = np.arange(len(conds))
    labels = [CONDITION_LABELS.get(c, c) for c in conds]
    colors = [COLORS.get(c, "#888") for c in conds]

    ax.bar(x, means, color=colors, edgecolor="white", linewidth=1.5)
    for i, (lo, hi, m) in enumerate(zip(ci_lo, ci_hi, means)):
        if not np.isnan(lo) and not np.isnan(hi):
            ax.errorbar(x[i], m, yerr=[[m - lo], [hi - m]], fmt="none", color="black", capsize=4)

    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylabel("Mean StrongREJECT Score")
    ax.set_title("Mean StrongREJECT Score by Condition with 95% Bootstrap CI\n(Stage 4.6 — exploratory)")
    ax.set_ylim(0, 1.05)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def _plot_think_tokens_by_condition(rows: list[dict], path: Path, plt: Any) -> None:
    fig, ax = plt.subplots(figsize=(8, 5))
    conds = [r["condition"] for r in rows if r.get("condition")]
    means = [_to_float(r.get("mean_think_tokens", "nan")) for r in rows if r.get("condition")]
    labels = [CONDITION_LABELS.get(c, c) for c in conds]
    colors = [COLORS.get(c, "#888") for c in conds]
    ax.bar(labels, means, color=colors, edgecolor="white", linewidth=1.5)
    ax.set_ylabel("Mean Think Tokens")
    ax.set_title("Mean Thinking Tokens by Ablation Condition\n(Stage 4.6 — exploratory)")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def _plot_success_rate_by_goal_condition(rows: list[dict], path: Path, plt: Any) -> None:
    goals = sorted(set(int(r["goal_index"]) for r in rows if r.get("goal_index") != ""))
    if not goals:
        return
    fig, axes = plt.subplots(1, len(goals), figsize=(4 * len(goals), 5), sharey=True)
    if len(goals) == 1:
        axes = [axes]
    for ax, gi in zip(axes, goals):
        group = [r for r in rows if int(r.get("goal_index", -1)) == gi]
        conds = [r["condition"] for r in group]
        rates = [_to_float(r.get("sr_success_rate", "nan")) for r in group]
        colors = [COLORS.get(c, "#888") for c in conds]
        labels = [CONDITION_LABELS.get(c, c) for c in conds]
        ax.bar(labels, rates, color=colors, edgecolor="white")
        ax.set_title(f"Goal {gi}")
        ax.set_ylim(0, 1.05)
        ax.set_xlabel("Condition")
    axes[0].set_ylabel("SR Success Rate")
    fig.suptitle("SR Success Rate by Goal and Condition\n(Stage 4.6 — exploratory)", y=1.02)
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def _plot_sr_score_vs_puzzle_fraction(rows: list[dict], path: Path, plt: Any) -> None:
    fig, ax = plt.subplots(figsize=(8, 5))
    goals = sorted(set(int(r["goal_index"]) for r in rows if r.get("goal_index") != ""))
    markers = ["o", "s", "^", "D"]
    for gi, marker in zip(goals, markers):
        group = sorted(
            [r for r in rows if int(r.get("goal_index", -1)) == gi],
            key=lambda r: _to_float(r.get("puzzle_fraction_target", "nan"))
        )
        xs = [_to_float(r.get("puzzle_fraction_target", "nan")) for r in group]
        ys = [_to_float(r.get("strongreject_score", "nan")) for r in group]
        ax.plot(xs, ys, marker=marker, label=f"Goal {gi}", linewidth=1.5, markersize=8)
    ax.set_xlabel("Puzzle Fraction (0=no puzzle, 1=full puzzle)")
    ax.set_ylabel("StrongREJECT Score")
    ax.set_xlim(-0.05, 1.1)
    ax.set_ylim(0, 1.05)
    ax.set_title("StrongREJECT Score vs Puzzle Fraction\n(thinking=on; Stage 4.6 — exploratory)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def _plot_think_tokens_vs_puzzle_fraction(rows: list[dict], path: Path, plt: Any) -> None:
    fig, ax = plt.subplots(figsize=(8, 5))
    goals = sorted(set(int(r["goal_index"]) for r in rows if r.get("goal_index") != ""))
    markers = ["o", "s", "^", "D"]
    for gi, marker in zip(goals, markers):
        group = sorted(
            [r for r in rows if int(r.get("goal_index", -1)) == gi],
            key=lambda r: _to_float(r.get("puzzle_fraction_target", "nan"))
        )
        xs = [_to_float(r.get("puzzle_fraction_target", "nan")) for r in group]
        ys = [_to_float(r.get("think_token_count", "nan")) for r in group]
        ax.plot(xs, ys, marker=marker, label=f"Goal {gi}", linewidth=1.5, markersize=8)
    ax.set_xlabel("Puzzle Fraction (0=no puzzle, 1=full puzzle)")
    ax.set_ylabel("Think Token Count")
    ax.set_title("Think Tokens vs Puzzle Fraction\n(thinking=on; Stage 4.6 — exploratory)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def _plot_thinking_mode_scatter(per_run: list[dict], path: Path, plt: Any) -> None:
    a_map = {r["source_example_id"]: r for r in per_run if r.get("condition") == "A"}
    e_map = {r["source_example_id"]: r for r in per_run if r.get("condition") == "E"}
    common_ids = sorted(set(a_map) & set(e_map))
    if not common_ids:
        return
    fig, ax = plt.subplots(figsize=(5, 5))
    xs = [_to_float(a_map[eid].get("strongreject_score", "nan")) for eid in common_ids]
    ys = [_to_float(e_map[eid].get("strongreject_score", "nan")) for eid in common_ids]
    goals = [int(a_map[eid].get("goal_index", -1)) for eid in common_ids]
    cmap = plt.get_cmap("tab10")
    for x, y, gi in zip(xs, ys, goals):
        ax.scatter(x, y, color=cmap(gi), s=80, zorder=3)
    ax.plot([0, 1], [0, 1], "k--", alpha=0.4, label="x=y (no effect)")
    ax.set_xlabel("SR Score — Condition A (thinking=on)")
    ax.set_ylabel("SR Score — Condition E (thinking=off)")
    ax.set_title("Thinking Mode Effect: A vs E\n(same full prompt; Stage 4.6 — exploratory)")
    ax.set_xlim(-0.05, 1.05)
    ax.set_ylim(-0.05, 1.05)
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def _plot_success_heatmap(per_run: list[dict], path: Path, plt: Any) -> None:
    goals = sorted(set(int(r.get("goal_index", -1)) for r in per_run if r.get("goal_index") != ""))
    conds = CONDITIONS
    data = np.full((len(goals), len(conds)), fill_value=np.nan)
    for i, gi in enumerate(goals):
        for j, cond in enumerate(conds):
            group = [r for r in per_run if int(r.get("goal_index", -1)) == gi and r.get("condition") == cond]
            if group:
                successes = [1 if _to_bool(r.get("is_success")) is True else 0 for r in group]
                data[i, j] = np.mean(successes) if successes else np.nan

    fig, ax = plt.subplots(figsize=(7, 4))
    im = ax.imshow(data, aspect="auto", vmin=0, vmax=1, cmap="RdYlGn")
    ax.set_xticks(range(len(conds)))
    ax.set_xticklabels([CONDITION_LABELS.get(c, c).replace("\n", " ") for c in conds], rotation=15)
    ax.set_yticks(range(len(goals)))
    ax.set_yticklabels([f"Goal {gi}" for gi in goals])
    ax.set_title("Success Rate Heatmap: Condition × Goal\n(Stage 4.6 — exploratory)")
    for i in range(len(goals)):
        for j in range(len(conds)):
            v = data[i, j]
            if not np.isnan(v):
                ax.text(j, i, f"{v:.2f}", ha="center", va="center",
                        fontsize=10, color="white" if v < 0.5 or v > 0.8 else "black")
    plt.colorbar(im, ax=ax, label="Success Rate")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Plot Stage 4.6 controlled ablation results.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--run-dir", type=Path, default=_OUTPUT_BASE / "runs_output")
    p.add_argument("--output-dir", type=Path, default=None)
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    out_dir = args.output_dir or (args.run_dir / "plots")
    plot_all(run_dir=args.run_dir, output_dir=out_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
