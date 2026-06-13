#!/usr/bin/env python3
"""
Task 2, Step 3 — Plot onset analysis results.

Generates meeting-ready figures from the onset proxy dataset and summary tables.

Usage:
    python -m poc_meeting.mahmood_48h_update.plot_onset_results \
        --output-dir outputs/meeting/mahmood_48h_update_<TIMESTAMP>
"""

import argparse
import csv
import json
import logging
import math
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s", stream=sys.stderr)
log = logging.getLogger(__name__)

COND_COLORS = {
    "A": "#2166ac",
    "D": "#d73027",
    "F": "#1a9850",
    "E": "#fc8d59",
}
COND_LABELS = {
    "A": "Full puzzle (A)",
    "D": "No puzzle (D)",
    "F": "Benign wrapper (F)",
    "E": "Thinking off (E)",
}


def _read_csv(p: Path) -> list[dict]:
    if not p.exists():
        log.warning("File not found: %s", p)
        return []
    with open(p, newline="") as f:
        return list(csv.DictReader(f))


def _float(v, default=float("nan")):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def _bool(v) -> bool | None:
    if v is None or v == "":
        return None
    return str(v).lower() in ("true", "1", "yes")


def _save(fig, path: Path, dpi: int = 150) -> None:
    fig.savefig(path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    log.info("Saved %s", path)


def fig_onset_percent_by_condition(dataset: list[dict], out: Path) -> None:
    """Violin/box plot: onset_percent by condition (high+medium confidence)."""
    valid = [r for r in dataset if r.get("confidence") in ("high", "medium")
             and not math.isnan(_float(r.get("onset_percent")))]
    groups = {}
    for r in valid:
        c = r.get("condition", "")
        if c in COND_COLORS:
            op = _float(r["onset_percent"])
            groups.setdefault(c, []).append(op * 100)

    order = [c for c in ("A", "D", "F", "E") if c in groups]
    if not order:
        log.warning("No onset data for fig_onset_percent_by_condition")
        return

    data = [groups[c] for c in order]
    fig, ax = plt.subplots(figsize=(7, 5))
    parts = ax.violinplot(data, positions=range(1, len(order) + 1),
                          showmedians=True, showextrema=True)
    for i, (cond, pc) in enumerate(zip(order, parts["bodies"])):
        pc.set_facecolor(COND_COLORS.get(cond, "#888"))
        pc.set_alpha(0.6)
    # Add individual points
    rng = np.random.default_rng(0)
    for i, (cond, vals) in enumerate(zip(order, data)):
        jitter = rng.uniform(-0.1, 0.1, len(vals))
        ax.scatter(i + 1 + jitter, vals, color=COND_COLORS.get(cond, "#888"),
                   s=20, alpha=0.5, zorder=3)
    ax.set_xticks(range(1, len(order) + 1))
    ax.set_xticklabels([COND_LABELS.get(c, c) for c in order], fontsize=10)
    ax.set_ylabel("Onset position (% of thinking trace)", fontsize=11)
    ax.set_title("Onset% by Condition (high+med confidence)\n[PROVISIONAL HEURISTIC]", fontsize=11)
    ax.set_ylim(-5, 105)
    n_str = ", ".join(f"{c}:n={len(groups[c])}" for c in order)
    ax.text(0.02, 0.97, n_str, transform=ax.transAxes, fontsize=8, va="top")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    _save(fig, out)


def fig_onset_percent_success_vs_failure(dataset: list[dict], out: Path) -> None:
    """Violin plot: onset_percent by sr_success."""
    valid = [r for r in dataset if r.get("confidence") in ("high", "medium")
             and not math.isnan(_float(r.get("onset_percent")))]
    succ_vals = [_float(r["onset_percent"]) * 100 for r in valid if _bool(r.get("sr_success")) is True]
    fail_vals = [_float(r["onset_percent"]) * 100 for r in valid if _bool(r.get("sr_success")) is False]

    if not succ_vals and not fail_vals:
        log.warning("No data for fig_onset_percent_success_vs_failure")
        return

    fig, ax = plt.subplots(figsize=(6, 5))
    data = [v for v in [succ_vals, fail_vals] if v]
    labels = [l for v, l in zip([succ_vals, fail_vals], ["Success\n(SR≥0.5)", "Failure\n(SR<0.5)"]) if v]
    colors = ["#2166ac", "#d73027"][:len(data)]

    if any(len(v) >= 2 for v in data):
        parts = ax.violinplot(data, positions=range(1, len(data) + 1),
                              showmedians=True, showextrema=True)
        for pc, color in zip(parts["bodies"], colors):
            pc.set_facecolor(color)
            pc.set_alpha(0.6)
    rng = np.random.default_rng(1)
    for i, (vals, color) in enumerate(zip(data, colors)):
        jitter = rng.uniform(-0.1, 0.1, len(vals))
        ax.scatter(i + 1 + jitter, vals, color=color, s=25, alpha=0.6, zorder=3)

    ax.set_xticks(range(1, len(data) + 1))
    ax.set_xticklabels(labels, fontsize=11)
    ax.set_ylabel("Onset position (% of thinking trace)", fontsize=11)
    ax.set_title("Onset% by Outcome\n[PROVISIONAL HEURISTIC]", fontsize=11)
    ax.set_ylim(-5, 105)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    _save(fig, out)


def fig_asr_by_onset_bucket(bucket_rows: list[dict], out: Path) -> None:
    """Bar chart: ASR% by onset_bucket."""
    rows = [r for r in bucket_rows if r["onset_bucket"] not in ("unavailable",)]
    if not rows:
        log.warning("No bucket data for fig_asr_by_onset_bucket")
        return

    labels = [r["onset_bucket"] for r in rows]
    asr = [_float(r["asr_pct"]) for r in rows]
    ns = [int(r["n"]) for r in rows]
    colors = ["#2166ac", "#74add1", "#fc8d59", "#d73027"][:len(rows)]

    fig, ax = plt.subplots(figsize=(7, 5))
    x = np.arange(len(rows))
    bars = ax.bar(x, asr, color=colors, edgecolor="black", linewidth=0.7, width=0.5)
    for bar, val, n in zip(bars, asr, ns):
        if not math.isnan(val):
            ax.text(bar.get_x() + bar.get_width() / 2, val + 1.5, f"{val:.0f}%\nn={n}",
                    ha="center", va="bottom", fontsize=10)
    ax.set_xticks(x)
    ax.set_xticklabels([l.capitalize() for l in labels], fontsize=11)
    ax.set_ylabel("ASR%", fontsize=11)
    ax.set_title("ASR% by Onset Bucket\n[PROVISIONAL HEURISTIC]", fontsize=11)
    ax.set_ylim(0, 110)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    _save(fig, out)


def fig_tokens_before_onset_by_condition(dataset: list[dict], out: Path) -> None:
    """Box plot: tokens_before_onset by condition."""
    valid = [r for r in dataset if r.get("confidence") in ("high", "medium")
             and r.get("onset_bucket") != "unavailable"]
    groups = {}
    for r in valid:
        c = r.get("condition", "")
        if c in COND_COLORS:
            tb = _float(r.get("tokens_before_onset"))
            if not math.isnan(tb):
                groups.setdefault(c, []).append(tb)

    order = [c for c in ("A", "D", "F", "E") if c in groups]
    if not order:
        log.warning("No data for fig_tokens_before_onset_by_condition")
        return

    data = [groups[c] for c in order]
    fig, ax = plt.subplots(figsize=(7, 5))
    bp = ax.boxplot(data, patch_artist=True, medianprops=dict(color="black", linewidth=2))
    for patch, cond in zip(bp["boxes"], order):
        patch.set_facecolor(COND_COLORS.get(cond, "#888"))
        patch.set_alpha(0.7)
    ax.set_xticks(range(1, len(order) + 1))
    ax.set_xticklabels([COND_LABELS.get(c, c) for c in order], fontsize=10)
    ax.set_ylabel("Tokens before onset", fontsize=11)
    ax.set_title("Tokens Before First Target Engagement by Condition\n[PROVISIONAL HEURISTIC]", fontsize=11)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    _save(fig, out)


def fig_think_tokens_vs_onset_percent(dataset: list[dict], out: Path) -> None:
    """Scatter: think_token_count vs onset_percent, colored by condition."""
    valid = [r for r in dataset if r.get("confidence") in ("high", "medium")
             and not math.isnan(_float(r.get("onset_percent")))]
    if not valid:
        log.warning("No data for fig_think_tokens_vs_onset_percent")
        return

    fig, ax = plt.subplots(figsize=(7, 5))
    markers = {"A": "o", "D": "s", "F": "^", "E": "D"}
    for cond in ("A", "D", "F", "E"):
        rows = [r for r in valid if r.get("condition") == cond]
        if not rows:
            continue
        x = [_float(r.get("think_token_count")) for r in rows]
        y = [_float(r["onset_percent"]) * 100 for r in rows]
        ax.scatter(x, y, label=COND_LABELS.get(cond, cond),
                   color=COND_COLORS.get(cond, "#888"), marker=markers.get(cond, "o"),
                   alpha=0.65, s=45)

    ax.set_xlabel("Thinking token count", fontsize=11)
    ax.set_ylabel("Onset position (% of thinking trace)", fontsize=11)
    ax.set_title("Thinking Tokens vs Onset%\n[PROVISIONAL HEURISTIC]", fontsize=11)
    ax.legend(fontsize=9)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    _save(fig, out)


def fig_projection_aligned(proj_rows: list[dict], out: Path) -> None:
    """Line chart: mean projection by offset bin (relative to onset)."""
    if not proj_rows:
        return
    offsets = sorted(set(r["offset_bin"] for r in proj_rows))
    mean_proj = [next(r["mean_projection"] for r in proj_rows if r["offset_bin"] == o) for o in offsets]
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(offsets, mean_proj, "o-", color="#2166ac", linewidth=2, markersize=6)
    ax.axvline(0, color="red", linestyle="--", linewidth=1.5, label="Onset")
    ax.set_xlabel("Offset bin (relative to onset bin)", fontsize=11)
    ax.set_ylabel("Mean Layer-22 projection", fontsize=11)
    ax.set_title("Layer-22 Projection Aligned to Onset Position\n[PROVISIONAL HEURISTIC — diagnostic only]", fontsize=11)
    ax.legend(fontsize=9)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    _save(fig, out)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(argv)

    out = Path(args.output_dir)

    dataset = _read_csv(out / "onset_proxy_dataset.csv")
    by_cond = _read_csv(out / "onset_by_condition.csv")
    by_success = _read_csv(out / "onset_by_success.csv")
    by_bucket = _read_csv(out / "onset_bucket_asr.csv")
    proj_aligned = _read_csv(out / "onset_aligned_projection.csv") if (out / "onset_aligned_projection.csv").exists() else []

    if not dataset:
        log.error("onset_proxy_dataset.csv not found — run build_onset_proxy_dataset.py first")
        return 1

    fig_onset_percent_by_condition(dataset, out / "fig_onset_percent_by_condition.png")
    fig_onset_percent_success_vs_failure(dataset, out / "fig_onset_percent_success_vs_failure.png")
    fig_asr_by_onset_bucket(by_bucket, out / "fig_asr_by_onset_bucket.png")
    fig_tokens_before_onset_by_condition(dataset, out / "fig_tokens_before_onset_by_condition.png")
    fig_think_tokens_vs_onset_percent(dataset, out / "fig_think_tokens_vs_onset_percent.png")

    if proj_aligned:
        # Parse floats
        for r in proj_aligned:
            r["offset_bin"] = int(r["offset_bin"])
            r["mean_projection"] = float(r["mean_projection"])
        fig_projection_aligned(proj_aligned, out / "fig_projection_aligned_to_onset.png")

    return 0


if __name__ == "__main__":
    sys.exit(main())
