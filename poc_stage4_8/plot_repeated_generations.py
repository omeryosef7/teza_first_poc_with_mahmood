"""
Stage 4.8 — Figures for repeated-generation analysis.

Generates up to 9 figures depending on which analysis files exist.
Figures that require missing inputs are silently skipped with a notice.

Usage:
  python -m poc_stage4_8.plot_repeated_generations
      --run-dir outputs/stage4_8/runs/<timestamp>
      [--output-dir PATH]
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

_COND_COLORS = {"A": "#2196F3", "D": "#FF9800", "F": "#4CAF50"}
_COND_LABELS = {
    "A": "Puzzle+thinking",
    "D": "No puzzle+thinking",
    "F": "Benign wrapper+thinking",
}
_CONDITIONS = ["A", "D", "F"]
_SR_THRESHOLD = 0.5


def _load_jsonl(path: Path) -> list[dict]:
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def _load_csv(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


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


def _setup_matplotlib():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({
        "figure.dpi": 150,
        "font.size": 10,
        "axes.titlesize": 11,
        "axes.labelsize": 10,
    })
    return plt


def fig1_seed_outcomes_by_cell(rows: list[dict], out_dir: Path) -> None:
    """Heatmap of SR success per (source × condition × seed)."""
    import numpy as np
    plt = _setup_matplotlib()

    sources = sorted(set(r.get("source_example_id", "") for r in rows))
    seeds = sorted(set(int(_f(r.get("seed", -1))) for r in rows if r.get("seed") is not None))

    fig, axes = plt.subplots(1, len(_CONDITIONS), figsize=(5 * len(_CONDITIONS), 0.5 * len(sources) + 2.5), squeeze=False)

    for col_i, cond in enumerate(_CONDITIONS):
        ax = axes[0][col_i]
        matrix = []
        for src in sources:
            row_vals = []
            for seed in seeds:
                matching = [r for r in rows
                            if r.get("source_example_id") == src
                            and r.get("condition") == cond
                            and int(_f(r.get("seed", -1))) == seed]
                if not matching:
                    row_vals.append(float("nan"))
                else:
                    r = matching[0]
                    sr = _b(r.get("sr_success"))
                    if r.get("finish_reason") == "max_new_tokens":
                        row_vals.append(0.5)  # censored — gray
                    elif sr is True:
                        row_vals.append(1.0)
                    elif sr is False:
                        row_vals.append(0.0)
                    else:
                        row_vals.append(float("nan"))
            matrix.append(row_vals)

        mat = np.array(matrix)
        im = ax.imshow(mat, aspect="auto", vmin=0, vmax=1, cmap="RdYlGn", interpolation="nearest")

        src_labels = [s.split("|")[0].replace("goal_index=", "g") + "|" + s.split("|")[2].replace("conversation_id=", "cv") for s in sources]
        ax.set_xticks(range(len(seeds)))
        ax.set_xticklabels([f"s{s}" for s in seeds], fontsize=7)
        ax.set_yticks(range(len(sources)))
        ax.set_yticklabels(src_labels, fontsize=6)
        ax.set_title(f"Cond {cond}: {_COND_LABELS.get(cond, cond)}", fontsize=9)
        ax.set_xlabel("Seed")

    axes[0][0].set_ylabel("Source prompt")
    fig.suptitle("Stage 4.8 — SR success by (prompt × condition × seed)\nGreen=success, Red=failure, Grey=censored", fontsize=10)
    plt.tight_layout()
    path = out_dir / "fig1_seed_outcomes_by_cell.png"
    plt.savefig(path, bbox_inches="tight")
    plt.close()
    print(f"  Saved {path.name}  [seed outcomes heatmap]")


def fig2_variance_decomposition(var_decomp: dict, cell_summary: list[dict], out_dir: Path) -> None:
    """Bar chart: between-cell vs within-cell (seed) variance."""
    plt = _setup_matplotlib()

    fig, axes = plt.subplots(1, 2, figsize=(10, 4))

    # Left: global variance decomposition
    ax = axes[0]
    labels = ["Between-cell\n(prompt+condition)", "Within-cell\n(seed/stochastic)"]
    vals = [
        _f(var_decomp.get("between_cell_variance", float("nan"))),
        _f(var_decomp.get("mean_within_cell_variance", float("nan"))),
    ]
    colors = ["#2196F3", "#FF9800"]
    bars = ax.bar(labels, vals, color=colors, edgecolor="black", linewidth=0.5)
    for bar, val in zip(bars, vals):
        if not math.isnan(val):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.002,
                    f"{val:.3f}", ha="center", va="bottom", fontsize=9)
    ax.set_ylabel("Variance in SR score")
    ax.set_title("SR Score Variance Decomposition")
    ax.set_ylim(bottom=0)

    # Right: per-cell within-cell variance by condition
    ax = axes[1]
    for cond in _CONDITIONS:
        cond_cells = [r for r in cell_summary if r.get("condition") == cond]
        variances = [_f(r.get("sr_score_variance", float("nan"))) for r in cond_cells]
        variances = [v for v in variances if not math.isnan(v)]
        if variances:
            x_pos = _CONDITIONS.index(cond)
            ax.bar(x_pos, sum(variances) / len(variances),
                   color=_COND_COLORS[cond], alpha=0.7, edgecolor="black", linewidth=0.5,
                   label=_COND_LABELS.get(cond, cond))
            for j, v in enumerate(variances):
                ax.scatter(x_pos + (j - len(variances) / 2) * 0.08, v,
                           color=_COND_COLORS[cond], s=20, zorder=5, alpha=0.7)

    ax.set_xticks(range(len(_CONDITIONS)))
    ax.set_xticklabels([f"Cond {c}" for c in _CONDITIONS])
    ax.set_ylabel("Within-cell SR score variance")
    ax.set_title("Per-Cell Stochastic Variance by Condition")
    ax.set_ylim(bottom=0)

    fig.suptitle("Stage 4.8 — Variance Decomposition", fontsize=11)
    plt.tight_layout()
    path = out_dir / "fig2_within_vs_between_prompt_variability.png"
    plt.savefig(path, bbox_inches="tight")
    plt.close()
    print(f"  Saved {path.name}  [variance decomposition]")


def fig3_condition_effects(cell_summary: list[dict], out_dir: Path) -> None:
    """Paired condition comparison with prompt fixed effects."""
    plt = _setup_matplotlib()

    fig, ax = plt.subplots(figsize=(7, 5))

    # For each source prompt, plot A vs D and A vs F
    sources = sorted(set(r.get("source_example_id", "") for r in cell_summary))

    for src in sources:
        src_cells = {r["condition"]: r for r in cell_summary if r.get("source_example_id") == src}
        if "A" not in src_cells:
            continue
        a_rate = _f(src_cells["A"].get("success_rate", float("nan")))
        if math.isnan(a_rate):
            continue
        for cond in ("D", "F"):
            if cond in src_cells:
                other_rate = _f(src_cells[cond].get("success_rate", float("nan")))
                if not math.isnan(other_rate):
                    ax.plot([cond, "A"], [other_rate, a_rate],
                            color=_COND_COLORS[cond], alpha=0.4, linewidth=1, marker="o",
                            markersize=4, zorder=3)

    # Condition means
    for cond in _CONDITIONS:
        cond_cells = [r for r in cell_summary if r.get("condition") == cond]
        rates = [_f(r.get("success_rate", float("nan"))) for r in cond_cells]
        rates = [r for r in rates if not math.isnan(r)]
        if rates:
            mean_rate = sum(rates) / len(rates)
            ax.scatter([cond], [mean_rate], s=120, color=_COND_COLORS[cond],
                       zorder=10, edgecolors="black", linewidth=1.5,
                       label=f"{_COND_LABELS.get(cond, cond)}\nmean={mean_rate:.2f}")

    ax.set_xlabel("Condition")
    ax.set_ylabel("SR success rate per cell")
    ax.set_title("Stage 4.8 — Condition Effects\n(lines connect same source prompt)")
    ax.legend(fontsize=8, loc="upper left")
    ax.set_ylim(-0.05, 1.05)
    plt.tight_layout()
    path = out_dir / "fig3_condition_effects_with_prompt_fixed_effects.png"
    plt.savefig(path, bbox_inches="tight")
    plt.close()
    print(f"  Saved {path.name}  [condition effects]")


def fig4_thinking_length_by_outcome(rows: list[dict], out_dir: Path) -> None:
    """Think tokens by seed and outcome."""
    plt = _setup_matplotlib()

    fig, ax = plt.subplots(figsize=(7, 5))

    complete = [r for r in rows if r.get("finish_reason") == "eos_token"]
    for r in complete:
        think = _f(r.get("think_token_count", 0))
        sr = _b(r.get("sr_success"))
        cond = r.get("condition", "?")
        seed = int(_f(r.get("seed", 0)))
        color = "#2ecc71" if sr is True else "#e74c3c" if sr is False else "#aaa"
        marker = {"A": "o", "D": "s", "F": "^"}.get(cond, "x")
        ax.scatter([seed], [think], color=color, marker=marker, s=40, alpha=0.7, zorder=5)

    from matplotlib.lines import Line2D
    legend_handles = [
        Line2D([0], [0], marker="o", color="w", markerfacecolor="#2ecc71", markersize=8, label="Success"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor="#e74c3c", markersize=8, label="Failure"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor="#aaa", markersize=8, label="Unknown"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor="gray", markersize=8, label="Cond A (circle)"),
        Line2D([0], [0], marker="s", color="w", markerfacecolor="gray", markersize=8, label="Cond D (square)"),
        Line2D([0], [0], marker="^", color="w", markerfacecolor="gray", markersize=8, label="Cond F (triangle)"),
    ]
    ax.legend(handles=legend_handles, fontsize=8, loc="upper right")
    ax.set_xlabel("Seed")
    ax.set_ylabel("Thinking token count")
    ax.set_title("Stage 4.8 — Thinking Length by Seed and Outcome")
    ax.set_yscale("symlog", linthresh=100)
    plt.tight_layout()
    path = out_dir / "fig4_thinking_length_by_seed_and_outcome.png"
    plt.savefig(path, bbox_inches="tight")
    plt.close()
    print(f"  Saved {path.name}  [thinking length by seed]")


def fig5_matched_cell_projection(matched_cells: list[dict], proj_rows: list[dict], out_dir: Path) -> None:
    """Projection scores in matched cells: success vs failure."""
    plt = _setup_matplotlib()

    # For each matched cell, get projection for success/failure rows
    matched_lookup = {(r["source_example_id"], r["condition"]) for r in matched_cells}
    relevant = [p for p in proj_rows if (p.get("source_example_id"), p.get("condition")) in matched_lookup]

    if not relevant:
        print("  SKIP fig5: no projection rows for matched cells")
        return

    fig, ax = plt.subplots(figsize=(7, 5))

    success_proj = [_f(r.get("layer22_first_500_mean_projection")) for r in relevant if _b(r.get("sr_success")) is True]
    failure_proj = [_f(r.get("layer22_first_500_mean_projection")) for r in relevant if _b(r.get("sr_success")) is False]
    success_proj = [v for v in success_proj if not math.isnan(v)]
    failure_proj = [v for v in failure_proj if not math.isnan(v)]

    ax.violinplot([success_proj, failure_proj], positions=[0, 1], showmeans=True, showmedians=True)
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["Success", "Failure"])
    ax.set_ylabel("Layer-22 first-500 projection (provisional direction)")
    ax.set_title(f"Stage 4.8 — Projection in Matched Cells\n"
                 f"n_success={len(success_proj)}, n_failure={len(failure_proj)}")

    if success_proj and failure_proj:
        mean_diff = sum(success_proj) / len(success_proj) - sum(failure_proj) / len(failure_proj)
        ax.text(0.5, 0.02, f"Mean diff (success − failure) = {mean_diff:.3f}",
                transform=ax.transAxes, ha="center", fontsize=9, color="gray")

    plt.tight_layout()
    path = out_dir / "fig5_matched_success_failure_projection.png"
    plt.savefig(path, bbox_inches="tight")
    plt.close()
    print(f"  Saved {path.name}  [matched cell projection]")


def fig6_loo_direction_performance(direction_results: dict, out_dir: Path) -> None:
    """LOO AUC and balanced accuracy per held-out prompt."""
    plt = _setup_matplotlib()

    loo = direction_results.get("loo_results", [])
    if not loo:
        print("  SKIP fig6: no LOO results in direction_results.json")
        return

    fig, axes = plt.subplots(1, 2, figsize=(10, 4))

    prompts = [r.get("held_out_prompt", f"fold_{i}") for i, r in enumerate(loo)]
    aucs = [_f(r.get("auc", float("nan"))) for r in loo]
    bal_accs = [_f(r.get("balanced_accuracy", float("nan"))) for r in loo]

    ax = axes[0]
    colors = ["#2ecc71" if a >= 0.7 else "#e74c3c" for a in aucs]
    ax.bar(range(len(prompts)), aucs, color=colors, edgecolor="black", linewidth=0.5)
    ax.axhline(0.7, color="gray", linestyle="--", linewidth=1, label="AUC=0.7 threshold")
    ax.axhline(0.5, color="black", linestyle=":", linewidth=1, label="Random baseline")
    ax.set_xticks(range(len(prompts)))
    ax.set_xticklabels([f"G{p[-1] if len(p) > 0 else i}" for i, p in enumerate(prompts)], fontsize=8)
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("AUC")
    ax.set_title("Leave-One-Prompt-Out AUC")
    ax.legend(fontsize=8)

    ax = axes[1]
    ax.bar(range(len(prompts)), bal_accs, color=colors, edgecolor="black", linewidth=0.5)
    ax.axhline(0.5, color="black", linestyle=":", linewidth=1, label="Random baseline")
    ax.set_xticks(range(len(prompts)))
    ax.set_xticklabels([f"G{p[-1] if len(p) > 0 else i}" for i, p in enumerate(prompts)], fontsize=8)
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Balanced Accuracy")
    ax.set_title("Leave-One-Prompt-Out Balanced Accuracy")
    ax.legend(fontsize=8)

    fig.suptitle("Stage 4.8 — LOO Direction Performance\n(behavior-conditioned predictive direction)", fontsize=10)
    plt.tight_layout()
    path = out_dir / "fig6_heldout_direction_performance.png"
    plt.savefig(path, bbox_inches="tight")
    plt.close()
    print(f"  Saved {path.name}  [LOO direction performance]")


def fig7_old_vs_new_direction(direction_results: dict, out_dir: Path) -> None:
    """Comparison: provisional direction vs behavior-conditioned direction."""
    plt = _setup_matplotlib()

    old_auc = _f(direction_results.get("old_direction_auc", float("nan")))
    new_auc = _f(direction_results.get("mean_loo_auc", float("nan")))
    perm_p = _f(direction_results.get("permutation_p", float("nan")))

    fig, ax = plt.subplots(figsize=(6, 4))
    labels = ["Provisional direction\n(harmful−harmless)", "Behavior-conditioned\n(success−failure, LOO CV)"]
    vals = [old_auc, new_auc]
    colors = ["#9E9E9E", "#2196F3"]
    bars = ax.bar(labels, vals, color=colors, edgecolor="black", linewidth=0.8)
    for bar, val in zip(bars, vals):
        if not math.isnan(val):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.01,
                    f"{val:.3f}", ha="center", va="bottom", fontsize=10, fontweight="bold")
    ax.axhline(0.5, color="black", linestyle=":", linewidth=1.5, label="Random baseline")
    ax.axhline(0.7, color="gray", linestyle="--", linewidth=1, label="AUC=0.7 threshold")
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Mean LOO AUC")
    ax.set_title(f"Direction Comparison\n(permutation p={perm_p:.3f})")
    ax.legend(fontsize=8)
    plt.tight_layout()
    path = out_dir / "fig7_old_vs_behavior_conditioned_direction.png"
    plt.savefig(path, bbox_inches="tight")
    plt.close()
    print(f"  Saved {path.name}  [direction comparison]")


def fig9_censoring_heatmap(rows: list[dict], out_dir: Path) -> None:
    """Censoring count per (source × condition)."""
    import numpy as np
    plt = _setup_matplotlib()

    sources = sorted(set(r.get("source_example_id", "") for r in rows))
    conds = _CONDITIONS

    matrix = []
    for src in sources:
        row_vals = []
        for cond in conds:
            matching = [r for r in rows if r.get("source_example_id") == src and r.get("condition") == cond]
            n_censored = sum(1 for r in matching if r.get("finish_reason") == "max_new_tokens")
            row_vals.append(n_censored)
        matrix.append(row_vals)

    mat = np.array(matrix)
    fig, ax = plt.subplots(figsize=(5, max(3, 0.4 * len(sources) + 2)))
    im = ax.imshow(mat, aspect="auto", vmin=0, cmap="YlOrRd", interpolation="nearest")
    for i in range(len(sources)):
        for j in range(len(conds)):
            ax.text(j, i, str(mat[i, j]), ha="center", va="center", fontsize=9)

    src_labels = [s.split("|")[0].replace("goal_index=", "g") + "|" + s.split("|")[2].replace("conversation_id=", "cv") for s in sources]
    ax.set_xticks(range(len(conds)))
    ax.set_xticklabels([f"Cond {c}" for c in conds])
    ax.set_yticks(range(len(sources)))
    ax.set_yticklabels(src_labels, fontsize=7)
    ax.set_title("Stage 4.8 — Censored rows per cell\n(max_new_tokens hit)")
    plt.colorbar(im, ax=ax, label="n censored")
    plt.tight_layout()
    path = out_dir / "fig9_censoring_by_prompt_condition.png"
    plt.savefig(path, bbox_inches="tight")
    plt.close()
    print(f"  Saved {path.name}  [censoring heatmap]")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Generate Stage 4.8 analysis figures.")
    p.add_argument("--run-dir", type=Path, required=True)
    p.add_argument("--output-dir", type=Path, default=None)
    args = p.parse_args(argv)

    run_dir = args.run_dir
    out_dir = args.output_dir or (run_dir / "plots")
    out_dir.mkdir(parents=True, exist_ok=True)

    # Load whatever exists
    run_summary_path = run_dir / "run_summary.jsonl"
    if not run_summary_path.exists():
        print(f"ERROR: {run_summary_path} not found")
        return 1

    rows = _load_jsonl(run_summary_path)
    print(f"Loaded {len(rows)} rows from run_summary.jsonl")

    analysis_dir = run_dir / "analysis"
    cell_summary_path = analysis_dir / "cell_summary.csv"
    matched_path = analysis_dir / "matched_outcome_cells.csv"
    var_decomp_path = analysis_dir / "variance_decomposition.json"

    repr_dir = run_dir / "representations"
    proj_summary_path = repr_dir / "projection_summary.jsonl"

    dir_results_path = run_dir / "direction_analysis" / "direction_results.json"

    cell_summary = _load_csv(cell_summary_path) if cell_summary_path.exists() else []
    matched_cells = _load_csv(matched_path) if matched_path.exists() else []
    var_decomp = json.loads(var_decomp_path.read_text()) if var_decomp_path.exists() else {}
    proj_rows = _load_jsonl(proj_summary_path) if proj_summary_path.exists() else []
    direction_results = json.loads(dir_results_path.read_text()) if dir_results_path.exists() else {}

    print(f"Analysis data: {len(cell_summary)} cells, {len(matched_cells)} matched, {len(proj_rows)} projection rows")

    # Generate all available figures
    fig1_seed_outcomes_by_cell(rows, out_dir)
    fig4_thinking_length_by_outcome(rows, out_dir)
    fig9_censoring_heatmap(rows, out_dir)

    if cell_summary:
        fig3_condition_effects(cell_summary, out_dir)
        if var_decomp:
            fig2_variance_decomposition(var_decomp, cell_summary, out_dir)
        else:
            print("  SKIP fig2: variance_decomposition.json not found")
    else:
        print("  SKIP figs 2,3: cell_summary.csv not found (run analyze_repeated_generations.py first)")

    if proj_rows and matched_cells:
        fig5_matched_cell_projection(matched_cells, proj_rows, out_dir)
    else:
        print(f"  SKIP fig5: {'no projection rows' if not proj_rows else 'no matched cells'}")

    if direction_results:
        fig6_loo_direction_performance(direction_results, out_dir)
        fig7_old_vs_new_direction(direction_results, out_dir)
    else:
        print("  SKIP figs 6,7: direction_results.json not found (run extract_behavior_conditioned_direction.py first)")

    print(f"\nAll figures written to {out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
