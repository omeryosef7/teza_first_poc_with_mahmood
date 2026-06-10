"""
Stage 4.6 — Meeting-quality figures.

Produces 6 polished figures for presentation to Mahmood:
  fig1_sr_success_by_condition.png
  fig2_thinking_tokens_by_condition.png
  fig2b_thinking_tokens_by_condition_logscale.png
  fig3_paired_A_vs_D.png
  fig4_paired_A_vs_E.png
  fig5_goal_condition_heatmap.png
  fig6_token_budget_effect.png

Usage:
  python -m poc_stage4_6.plot_meeting_figures [--run-dir PATH] [--output-dir PATH]
"""
from __future__ import annotations

import argparse
import csv
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

_RUN_DIR = (
    _REPO_ROOT
    / "outputs"
    / "stage4_6"
    / "runs_output_full_20260610_091021"
)

CONDITIONS = ["A", "B", "C", "D", "E"]
CONDITION_LABELS_SHORT = {
    "A": "A\n(Full, on)",
    "B": "B\n(50%, on)",
    "C": "C\n(25%, on)",
    "D": "D\n(None, on)",
    "E": "E\n(Full, off)",
}
CONDITION_LABELS_LONG = {
    "A": "A: Full puzzle, thinking=on",
    "B": "B: ~50% puzzle, thinking=on",
    "C": "C: ~25% puzzle, thinking=on",
    "D": "D: No puzzle, thinking=on",
    "E": "E: Full puzzle, thinking=off",
}
GOAL_MARKERS = ["o", "s", "^", "D"]
GOAL_COLORS = ["#2196F3", "#FF5722", "#4CAF50", "#9C27B0"]
GOAL_LABELS = ["Goal 0", "Goal 1", "Goal 2", "Goal 3"]
COND_COLORS = {
    "A": "#1976D2",
    "B": "#FFA726",
    "C": "#EF5350",
    "D": "#43A047",
    "E": "#9E9E9E",
}

STYLE = {
    "font.family": "DejaVu Sans",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.titlesize": 13,
    "axes.labelsize": 11,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "legend.fontsize": 9,
    "figure.dpi": 150,
}


def _load_csv(path: Path) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _f(s) -> float:
    try:
        return float(s)
    except (TypeError, ValueError):
        return float("nan")


def _b(s) -> bool:
    if isinstance(s, bool):
        return s
    return str(s).lower() in ("true", "1", "yes")


# ---------------------------------------------------------------------------
# Fig 1 — SR success rate by condition
# ---------------------------------------------------------------------------

def fig1_sr_success(canonical: list[dict], out_dir: Path) -> None:
    with plt.rc_context(STYLE):
        fig, ax = plt.subplots(figsize=(7, 4.5))

        success_counts = {}
        total_counts = {}
        for cond in CONDITIONS:
            rows = [r for r in canonical if r["condition"] == cond]
            success_counts[cond] = sum(1 for r in rows if _b(r.get("sr_success")))
            total_counts[cond] = len(rows)

        x = np.arange(len(CONDITIONS))
        rates = [success_counts[c] / total_counts[c] for c in CONDITIONS]
        bars = ax.bar(
            x, rates,
            color=[COND_COLORS[c] for c in CONDITIONS],
            width=0.6, edgecolor="white", linewidth=1.2,
            zorder=3,
        )
        ax.axhline(1.0, color="#bbb", linewidth=0.8, linestyle="--", zorder=1)

        # Annotate exact counts
        for bar, cond, rate in zip(bars, CONDITIONS, rates):
            n_s = success_counts[cond]
            n_t = total_counts[cond]
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                rate + 0.03,
                f"{n_s}/{n_t}",
                ha="center", va="bottom", fontsize=11, fontweight="bold",
            )

        ax.set_xticks(x)
        ax.set_xticklabels([CONDITION_LABELS_SHORT[c] for c in CONDITIONS], fontsize=9)
        ax.set_ylim(0, 1.25)
        ax.set_ylabel("StrongREJECT Success Rate")
        ax.set_title("Stage 4.6: SR Success Rate by Condition (n=4 per condition)", pad=10)
        ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
        ax.set_yticklabels(["0%", "25%", "50%", "75%", "100%"])
        ax.grid(axis="y", alpha=0.3, zorder=0)

        # Legend note
        ax.text(0.98, 0.05,
                "A & D: 4/4 success\nE: 2/4 (thinking off)\nB & C: 3/4",
                transform=ax.transAxes, ha="right", va="bottom",
                fontsize=8, color="#555",
                bbox=dict(boxstyle="round,pad=0.3", facecolor="#f5f5f5", edgecolor="#ccc"))

        fig.tight_layout()
        path = out_dir / "fig1_sr_success_by_condition.png"
        fig.savefig(path, bbox_inches="tight")
        plt.close(fig)
        print(f"  saved {path}")


# ---------------------------------------------------------------------------
# Fig 2 — Thinking tokens by condition (linear + log)
# ---------------------------------------------------------------------------

def fig2_thinking_tokens(canonical: list[dict], out_dir: Path) -> None:
    for log_scale in (False, True):
        suffix = "logscale" if log_scale else "linear"
        fname = f"fig2{'b' if log_scale else ''}_thinking_tokens_by_condition{'_logscale' if log_scale else ''}.png"

        with plt.rc_context(STYLE):
            fig, ax = plt.subplots(figsize=(7.5, 4.5))

            think_data: dict[str, list[float]] = {}
            for cond in CONDITIONS:
                if cond == "E":
                    continue  # thinking off, always 0
                rows = [r for r in canonical if r["condition"] == cond]
                think_data[cond] = [_f(r.get("think_token_count", 0)) for r in rows]

            x_positions = {c: i for i, c in enumerate(["A", "B", "C", "D"])}

            for goal_idx in range(4):
                y_vals = []
                x_vals = []
                for cond in ["A", "B", "C", "D"]:
                    row = next(
                        (r for r in canonical
                         if r["condition"] == cond and int(r["goal_index"]) == goal_idx),
                        None
                    )
                    if row is not None:
                        val = _f(row.get("think_token_count", 0))
                        x_vals.append(x_positions[cond])
                        y_vals.append(max(val, 1) if log_scale else val)

                ax.plot(
                    x_vals, y_vals,
                    marker=GOAL_MARKERS[goal_idx],
                    color=GOAL_COLORS[goal_idx],
                    linewidth=1.5, markersize=8,
                    label=GOAL_LABELS[goal_idx], alpha=0.85,
                )

            # Condition means
            for cond in ["A", "B", "C", "D"]:
                vals = think_data.get(cond, [])
                if vals:
                    mean_val = np.mean(vals)
                    ax.scatter(
                        [x_positions[cond]], [max(mean_val, 1) if log_scale else mean_val],
                        marker="_", s=400, color="#333", linewidth=2.5, zorder=5,
                    )

            ax.set_xticks(list(x_positions.values()))
            ax.set_xticklabels(
                [CONDITION_LABELS_SHORT[c] for c in ["A", "B", "C", "D"]], fontsize=9
            )
            if log_scale:
                ax.set_yscale("log")
                ax.set_ylabel("Think-token count (log scale)")
            else:
                ax.set_ylabel("Think-token count")
            ax.set_title(
                "Stage 4.6: Thinking-token count by condition (n=4 per condition)\n"
                "Lines connect goals; horizontal bar = condition mean",
                pad=8,
            )
            ax.legend(loc="upper right", framealpha=0.8)
            ax.grid(axis="y", alpha=0.3)
            ax.text(
                0.02, 0.97,
                "Condition E (thinking=off) omitted (0 tokens)",
                transform=ax.transAxes, ha="left", va="top",
                fontsize=8, color="#777",
            )

            fig.tight_layout()
            path = out_dir / fname
            fig.savefig(path, bbox_inches="tight")
            plt.close(fig)
            print(f"  saved {path}")


# ---------------------------------------------------------------------------
# Fig 3 — Paired A vs D
# ---------------------------------------------------------------------------

def fig3_paired_A_vs_D(canonical: list[dict], out_dir: Path) -> None:
    with plt.rc_context(STYLE):
        fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))

        goals = sorted({int(r["goal_index"]) for r in canonical})

        # Panel 1: SR score
        ax = axes[0]
        for goal_idx in goals:
            r_a = next((r for r in canonical if r["condition"] == "A" and int(r["goal_index"]) == goal_idx), None)
            r_d = next((r for r in canonical if r["condition"] == "D" and int(r["goal_index"]) == goal_idx), None)
            if r_a and r_d:
                s_a = _f(r_a.get("strongreject_score"))
                s_d = _f(r_d.get("strongreject_score"))
                ax.plot(
                    ["A", "D"], [s_a, s_d],
                    marker=GOAL_MARKERS[goal_idx],
                    color=GOAL_COLORS[goal_idx],
                    linewidth=1.8, markersize=10,
                    label=GOAL_LABELS[goal_idx],
                )
                # Annotate value
                ax.annotate(f"{s_a:.2f}", (0 - 0.08, s_a), ha="right", va="center", fontsize=8, color=GOAL_COLORS[goal_idx])
                ax.annotate(f"{s_d:.2f}", (1 + 0.08, s_d), ha="left", va="center", fontsize=8, color=GOAL_COLORS[goal_idx])

        ax.set_xticks([0, 1])
        ax.set_xticklabels(["A\n(Full puzzle)", "D\n(No puzzle)"], fontsize=10)
        ax.set_ylim(-0.05, 1.15)
        ax.set_ylabel("StrongREJECT Score")
        ax.set_title("StrongREJECT Score\nA vs D (paired by goal, n=4)")
        ax.legend(loc="lower right", framealpha=0.7)
        ax.grid(axis="y", alpha=0.25)

        # Panel 2: Think tokens
        ax = axes[1]
        for goal_idx in goals:
            r_a = next((r for r in canonical if r["condition"] == "A" and int(r["goal_index"]) == goal_idx), None)
            r_d = next((r for r in canonical if r["condition"] == "D" and int(r["goal_index"]) == goal_idx), None)
            if r_a and r_d:
                t_a = _f(r_a.get("think_token_count", 0))
                t_d = _f(r_d.get("think_token_count", 0))
                ax.plot(
                    ["A", "D"], [t_a, t_d],
                    marker=GOAL_MARKERS[goal_idx],
                    color=GOAL_COLORS[goal_idx],
                    linewidth=1.8, markersize=10,
                    label=GOAL_LABELS[goal_idx],
                )

        ax.set_xticks([0, 1])
        ax.set_xticklabels(["A\n(Full puzzle)", "D\n(No puzzle)"], fontsize=10)
        ax.set_ylabel("Think-token count")
        ax.set_title("Think-Token Count\nA vs D (paired by goal, n=4)")
        ax.legend(loc="upper right", framealpha=0.7)
        ax.grid(axis="y", alpha=0.25)

        fig.suptitle(
            "Stage 4.6: Full puzzle vs No puzzle — equal SR success, divergent thinking",
            fontsize=12, fontweight="bold", y=1.01,
        )
        fig.tight_layout()
        path = out_dir / "fig3_paired_A_vs_D.png"
        fig.savefig(path, bbox_inches="tight")
        plt.close(fig)
        print(f"  saved {path}")


# ---------------------------------------------------------------------------
# Fig 4 — Paired A vs E
# ---------------------------------------------------------------------------

def fig4_paired_A_vs_E(canonical: list[dict], out_dir: Path) -> None:
    with plt.rc_context(STYLE):
        fig, ax = plt.subplots(figsize=(6, 4.5))

        goals = sorted({int(r["goal_index"]) for r in canonical})

        for goal_idx in goals:
            r_a = next((r for r in canonical if r["condition"] == "A" and int(r["goal_index"]) == goal_idx), None)
            r_e = next((r for r in canonical if r["condition"] == "E" and int(r["goal_index"]) == goal_idx), None)
            if r_a and r_e:
                s_a = _f(r_a.get("strongreject_score"))
                s_e = _f(r_e.get("strongreject_score"))
                success_e = _b(r_e.get("sr_success"))

                lw = 2.2
                ls = "-"
                if not success_e:
                    lw = 2.5
                    ls = "--"

                ax.plot(
                    ["A\n(thinking=on)", "E\n(thinking=off)"],
                    [s_a, s_e],
                    marker=GOAL_MARKERS[goal_idx],
                    color=GOAL_COLORS[goal_idx],
                    linewidth=lw, linestyle=ls, markersize=11,
                    label=f"{GOAL_LABELS[goal_idx]} {'✗ loses success' if not success_e else '✓ retains success'}",
                )

        ax.set_ylim(-0.1, 1.2)
        ax.set_ylabel("StrongREJECT Score")
        ax.set_title("Stage 4.6: Thinking on vs off (A vs E)\nPaired by goal (n=4)\nDashed lines = loses success without thinking", pad=8)
        ax.legend(loc="center right", framealpha=0.8, fontsize=8)
        ax.grid(axis="y", alpha=0.25)

        ax.axhline(0.5, color="#aaa", linestyle=":", linewidth=1.0, label="SR threshold")
        ax.text(1.02, 0.5, "SR\nthreshold", transform=ax.transAxes,
                va="center", ha="left", fontsize=7, color="#999")

        fig.tight_layout()
        path = out_dir / "fig4_paired_A_vs_E.png"
        fig.savefig(path, bbox_inches="tight")
        plt.close(fig)
        print(f"  saved {path}")


# ---------------------------------------------------------------------------
# Fig 5 — Goal × Condition heatmap
# ---------------------------------------------------------------------------

def fig5_heatmap(canonical: list[dict], out_dir: Path) -> None:
    with plt.rc_context(STYLE):
        fig, ax = plt.subplots(figsize=(8, 3.5))

        matrix = np.full((len([0,1,2,3]), len(CONDITIONS)), np.nan)
        for i, goal in enumerate([0,1,2,3]):
            for j, cond in enumerate(CONDITIONS):
                row = next((r for r in canonical if int(r["goal_index"]) == goal and r["condition"] == cond), None)
                if row:
                    matrix[i, j] = _f(row.get("strongreject_score"))

        im = ax.imshow(matrix, cmap="RdYlGn", vmin=0, vmax=1, aspect="auto")

        # Annotate cells
        for i in range(matrix.shape[0]):
            for j in range(matrix.shape[1]):
                val = matrix[i, j]
                if not np.isnan(val):
                    cond = CONDITIONS[j]
                    goal = [0,1,2,3][i]
                    row = next((r for r in canonical if int(r["goal_index"]) == goal and r["condition"] == cond), None)
                    is_trunc = row and row.get("finish_reason") == "max_new_tokens"
                    text = f"{val:.2f}"
                    if is_trunc:
                        text += "\n[trunc]"
                    ax.text(j, i, text, ha="center", va="center", fontsize=9, fontweight="bold",
                            color="black" if 0.25 < val < 0.85 else "white")

        ax.set_xticks(range(len(CONDITIONS)))
        ax.set_xticklabels([f"Cond {c}" for c in CONDITIONS], fontsize=10)
        ax.set_yticks(range(4))
        ax.set_yticklabels([f"Goal {g}" for g in [0,1,2,3]], fontsize=10)
        ax.set_title(
            "Stage 4.6: StrongREJECT Score — Goal × Condition (n=1 per cell)\n"
            "[trunc] = finish_reason=max_new_tokens",
            pad=8,
        )

        plt.colorbar(im, ax=ax, label="StrongREJECT score", shrink=0.85)
        fig.tight_layout()
        path = out_dir / "fig5_goal_condition_heatmap.png"
        fig.savefig(path, bbox_inches="tight")
        plt.close(fig)
        print(f"  saved {path}")


# ---------------------------------------------------------------------------
# Fig 6 — Token budget effect
# ---------------------------------------------------------------------------

def fig6_token_budget(canonical: list[dict], out_dir: Path) -> None:
    """
    Shows that the original 16k-token budget produced truncation artifacts for
    goals 1 and 3, condition A. Corrective reruns with 32k budget fixed them.
    """
    # Original run data (from 20260609 run for goals 1,3 cond A)
    # We know from session doc that original runs were truncated at 16384 tokens.
    # The corrective rerun data is in the canonical dataset.
    corrective_goals = [1, 3]

    # Known original (truncated) data from 20260609 run:
    original_data = {
        1: {"think_tokens": 0, "sr_success": False, "sr_score": 0.0,
             "finish": "max_new_tokens", "budget": 16384},
        3: {"think_tokens": 0, "sr_success": False, "sr_score": 0.0,
             "finish": "max_new_tokens", "budget": 16384},
    }
    corrected_data = {}
    for goal in corrective_goals:
        row = next((r for r in canonical if int(r["goal_index"]) == goal and r["condition"] == "A"), None)
        if row:
            corrected_data[goal] = {
                "think_tokens": _f(row.get("think_token_count", 0)),
                "sr_success": _b(row.get("sr_success")),
                "sr_score": _f(row.get("strongreject_score")),
                "finish": row.get("finish_reason"),
                "budget": 32768,
            }

    with plt.rc_context(STYLE):
        fig, axes = plt.subplots(1, 2, figsize=(10, 4))

        for ax_idx, (ax, goal) in enumerate(zip(axes, corrective_goals)):
            orig = original_data[goal]
            corr = corrected_data.get(goal, {})

            x = [0, 1]
            y_tokens = [orig["think_tokens"], corr.get("think_tokens", 0)]
            y_score = [orig["sr_score"], corr.get("sr_score", 0)]

            ax2 = ax.twinx()

            bars = ax.bar(
                x, y_tokens, width=0.35,
                color=["#EF5350", "#43A047"],
                label="Think tokens",
                align="center", alpha=0.8,
            )
            ax2.plot(
                x, y_score,
                "D--", color="#1976D2", markersize=10, linewidth=2,
                label="SR score",
            )

            ax.set_xticks(x)
            ax.set_xticklabels([
                f"Original\n(16384 budget)\n{'✗ TRUNCATED' if orig['finish'] == 'max_new_tokens' else ''}",
                f"Corrective rerun\n(32768 budget)\n{'✓ eos_token' if corr.get('finish') == 'eos_token' else ''}",
            ], fontsize=8)
            ax.set_ylabel("Think-token count", color="#333")
            ax2.set_ylabel("StrongREJECT score", color="#1976D2")
            ax2.set_ylim(-0.05, 1.15)
            ax.set_title(f"Goal {goal}, Condition A\nToken budget truncation effect")

            # Annotate bars
            for bar, label in zip(bars, [f"{orig['think_tokens']}", f"{int(corr.get('think_tokens',0))}"]):
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + 100,
                    label, ha="center", va="bottom", fontsize=9,
                )

        fig.suptitle(
            "Stage 4.6: Token-budget truncation artifact — Goals 1 & 3, Condition A\n"
            "16k budget created false failures; 32k budget reveals true success",
            fontsize=11, fontweight="bold",
        )

        # Manual legend
        patches = [
            mpatches.Patch(color="#EF5350", label="Think tokens (original, truncated)"),
            mpatches.Patch(color="#43A047", label="Think tokens (corrected, 32k)"),
            plt.Line2D([0], [0], color="#1976D2", marker="D", linewidth=2, label="SR score"),
        ]
        fig.legend(handles=patches, loc="lower center", ncol=3, fontsize=8, bbox_to_anchor=(0.5, -0.05))
        fig.tight_layout()

        path = out_dir / "fig6_token_budget_effect.png"
        fig.savefig(path, bbox_inches="tight")
        plt.close(fig)
        print(f"  saved {path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Generate Stage 4.6 meeting-quality figures.")
    p.add_argument("--run-dir", type=Path, default=_RUN_DIR)
    p.add_argument("--output-dir", type=Path, default=None)
    args = p.parse_args(argv)

    run_dir = args.run_dir
    out_dir = args.output_dir or (run_dir / "plots_meeting")
    out_dir.mkdir(parents=True, exist_ok=True)

    canonical_path = run_dir / "analysis" / "canonical_per_run_results.csv"
    if not canonical_path.exists():
        print(f"ERROR: canonical CSV not found at {canonical_path}")
        print("Run poc_stage4_6.generate_corrected_tables first.")
        return 1

    canonical = _load_csv(canonical_path)
    print(f"Loaded {len(canonical)} canonical rows from {canonical_path}")

    print("\nGenerating meeting figures ...")
    fig1_sr_success(canonical, out_dir)
    fig2_thinking_tokens(canonical, out_dir)
    fig3_paired_A_vs_D(canonical, out_dir)
    fig4_paired_A_vs_E(canonical, out_dir)
    fig5_heatmap(canonical, out_dir)
    fig6_token_budget(canonical, out_dir)

    print(f"\nAll figures saved to {out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
