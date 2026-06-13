#!/usr/bin/env python3
"""
Task 3, Step 2 — Analyze Stage 4.8 extension (or report plan if not yet run).

Combines original Stage 4.8 + extension data, checks matched-cell threshold,
and reports readiness for behavior-conditioned direction extraction.

Usage:
    python -m poc_meeting.mahmood_48h_update.analyze_stage48_extension \
        --output-dir outputs/meeting/mahmood_48h_update_<TIMESTAMP>
"""

import argparse
import csv
import json
import logging
import math
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s", stream=sys.stderr)
log = logging.getLogger(__name__)

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
MATCHED_CELL_THRESHOLD = 4


def _read_csv(p: Path) -> list[dict]:
    if not p.exists():
        return []
    with open(p, newline="") as f:
        return list(csv.DictReader(f))


def _float(v, default=float("nan")):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def _int(v, default=0):
    try:
        return int(v)
    except (TypeError, ValueError):
        return default


def _bool(v) -> bool:
    return str(v).lower() in ("true", "1", "yes")


def find_extension_dir() -> Path | None:
    """Find the most recent extension run dir."""
    base = _REPO_ROOT / "outputs/stage4_8/runs"
    candidates = sorted(base.glob("run_array_extension_*"), reverse=True)
    for c in candidates:
        if (c / "extension_manifest.jsonl").exists():
            return c
    return None


def load_cell_summary(run_dir: Path) -> list[dict]:
    return _read_csv(run_dir / "analysis" / "cell_summary.csv")


def combine_cell_summaries(orig: list[dict], ext: list[dict]) -> list[dict]:
    """Combine original and extension cell summaries by re-aggregating."""
    if not ext:
        return orig
    from collections import defaultdict
    combined: dict[tuple, dict] = {}
    for r in orig + ext:
        key = (r["source_example_id"], r["condition"])
        if key not in combined:
            combined[key] = {
                "source_example_id": r["source_example_id"],
                "condition": r["condition"],
                "goal_index": r["goal_index"],
                "n_seeds": 0, "n_censored": 0, "n_complete": 0, "n_valid_seg": 0,
                "n_success": 0, "n_failure": 0,
                "sr_scores": [], "think_tokens": [],
            }
        c = combined[key]
        c["n_seeds"] += _int(r.get("n_seeds"))
        c["n_censored"] += _int(r.get("n_censored"))
        c["n_complete"] += _int(r.get("n_complete"))
        c["n_valid_seg"] += _int(r.get("n_valid_seg"))
        c["n_success"] += _int(r.get("n_success"))
        c["n_failure"] += _int(r.get("n_failure"))

    rows = []
    for key, c in combined.items():
        n_c = c["n_complete"]
        k = c["n_success"]
        sr = k / n_c if n_c > 0 else float("nan")
        has_s = c["n_success"] > 0
        has_f = c["n_failure"] > 0
        rows.append({
            "source_example_id": c["source_example_id"],
            "condition": c["condition"],
            "goal_index": c["goal_index"],
            "n_seeds": c["n_seeds"],
            "n_censored": c["n_censored"],
            "n_complete": n_c,
            "n_valid_seg": c["n_valid_seg"],
            "n_success": k,
            "n_failure": c["n_failure"],
            "success_rate": round(sr, 4),
            "is_matched_outcome_cell": has_s and has_f,
            "has_success": has_s,
            "has_failure": has_f,
        })
    return rows


def write_heatmap(cells: list[dict], out: Path) -> None:
    """Heatmap of success_rate per goal × condition, marking matched cells."""
    goals = sorted(set(str(r["goal_index"]) for r in cells))
    conds = [c for c in ("A", "D", "F") if any(r["condition"] == c for r in cells)]
    matrix = np.full((len(goals), len(conds)), float("nan"))
    matched = np.zeros((len(goals), len(conds)), dtype=bool)

    for r in cells:
        gi = str(r["goal_index"])
        c = r["condition"]
        if gi in goals and c in conds:
            i = goals.index(gi)
            j = conds.index(c)
            matrix[i, j] = _float(r.get("success_rate")) * 100
            matched[i, j] = _bool(r.get("is_matched_outcome_cell", False))

    fig, ax = plt.subplots(figsize=(5, 4))
    im = ax.imshow(matrix, aspect="auto", vmin=0, vmax=100, cmap="RdYlGn")
    ax.set_xticks(range(len(conds)))
    ax.set_xticklabels(conds, fontsize=12)
    ax.set_yticks(range(len(goals)))
    ax.set_yticklabels([f"Goal {g}" for g in goals], fontsize=11)
    for i in range(len(goals)):
        for j in range(len(conds)):
            val = matrix[i, j]
            if not math.isnan(val):
                ax.text(j, i, f"{val:.0f}%", ha="center", va="center", fontsize=11,
                        color="black" if val < 70 else "white")
                if matched[i, j]:
                    rect = plt.Rectangle((j - 0.45, i - 0.45), 0.9, 0.9,
                                         fill=False, edgecolor="blue", linewidth=3)
                    ax.add_patch(rect)
    import matplotlib.patches as mpatches
    matched_patch = mpatches.Patch(facecolor="none", edgecolor="blue", linewidth=2,
                                   label="Matched cell (has success + failure)")
    ax.legend(handles=[matched_patch], loc="upper right", fontsize=8)
    plt.colorbar(im, ax=ax, label="Success rate %")
    ax.set_title("Stage 4.8 (+ Extension if available)\nSuccess rate per goal × condition", fontsize=11)
    fig.tight_layout()
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    log.info("Saved %s", out)


def write_matched_cells_report(cells: list[dict], n_matched: int, has_ext: bool, out: Path) -> None:
    lines = [
        "# Stage 4.8 Matched Cells Report",
        f"\n_Generated: {datetime.utcnow().isoformat()}Z_",
        "",
        f"**Data source:** Original Stage 4.8" + (" + Extension" if has_ext else " (extension not yet run)"),
        "",
        "## Threshold for Behavior-Conditioned Direction Extraction",
        "",
        f"- **Required:** ≥ {MATCHED_CELL_THRESHOLD} matched cells (cells with ≥1 success AND ≥1 failure)",
        f"- **Current:** {n_matched} matched cells",
        f"- **Status:** {'✅ THRESHOLD MET' if n_matched >= MATCHED_CELL_THRESHOLD else '❌ BELOW THRESHOLD'}",
        "",
    ]
    if n_matched < MATCHED_CELL_THRESHOLD:
        needed = MATCHED_CELL_THRESHOLD - n_matched
        lines += [
            f"## What Is Needed: {needed} More Matched Cell(s)",
            "",
            "A matched cell is a (source_example_id × condition) pair with both",
            "a success (sr_score ≥ 0.5) and a failure (sr_score < 0.5) among its seeds.",
            "",
            "To generate more matched cells:",
            "1. Run the Stage 4.8 extension (goals 0 and 2, seeds 106–115)",
            "2. Goals with intermediate success probability are the best candidates",
            "3. Alternatively, add more seeds for existing cells that have only successes or failures",
            "",
        ]
    else:
        lines += [
            "## Next Steps (Threshold Met)",
            "",
            "Behavior-conditioned direction extraction can proceed:",
            "```bash",
            "python -m poc_stage4_8.extract_behavior_conditioned_direction \\",
            "    --run-dir outputs/stage4_8/runs/run_array_<combined>",
            "```",
            "",
            "This extracts a direction from Layer-22 first-500-token representations",
            "using Leave-One-Prompt-Out cross-validation.",
            "",
            "**Important:** Do NOT compare A vs D/F — only compare success vs failure",
            "within the same prompt+condition cell.",
            "",
        ]

    lines += [
        "## Current Matched Cells",
        "",
        "| Goal | Condition | n_seeds | n_success | n_failure | is_matched |",
        "|------|-----------|---------|---------|---------|-----------|",
    ]
    for r in sorted(cells, key=lambda x: (str(x["goal_index"]), x["condition"])):
        is_m = _bool(r.get("is_matched_outcome_cell", False))
        lines.append(
            f"| {r['goal_index']} | {r['condition']} | {r['n_seeds']} "
            f"| {r['n_success']} | {r['n_failure']} | {'✅' if is_m else '—'} |"
        )

    out.write_text("\n".join(lines))
    log.info("Wrote %s", out)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--orig-dir", type=Path,
                        default=_REPO_ROOT / "outputs/stage4_8/runs/run_array_20260611_0109")
    args = parser.parse_args(argv)

    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)

    # Load original
    log.info("Loading original Stage 4.8 cell summary...")
    orig_cells = load_cell_summary(args.orig_dir)
    log.info("  %d original cells", len(orig_cells))

    # Check for extension
    ext_dir = find_extension_dir()
    has_ext = False
    ext_cells = []
    if ext_dir and (ext_dir / "analysis" / "cell_summary.csv").exists():
        log.info("Found extension data at %s", ext_dir)
        ext_cells = load_cell_summary(ext_dir)
        has_ext = True
        log.info("  %d extension cells", len(ext_cells))
    else:
        log.info("Extension not yet run (or not analyzed). Reporting original data only.")

    # Combine
    cells = combine_cell_summaries(orig_cells, ext_cells) if has_ext else orig_cells

    # Count matched
    n_matched = sum(1 for r in cells if _bool(r.get("is_matched_outcome_cell", False)))
    log.info("Matched outcome cells: %d / %d (threshold: %d)", n_matched, len(cells), MATCHED_CELL_THRESHOLD)

    # Write combined CSV if extension exists
    if has_ext:
        comb_path = out / "stage48_combined_cell_outcomes.csv"
        fn = ["source_example_id", "condition", "goal_index", "n_seeds", "n_censored",
              "n_complete", "n_valid_seg", "n_success", "n_failure", "success_rate",
              "is_matched_outcome_cell", "has_success", "has_failure"]
        with open(comb_path, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fn, extrasaction="ignore")
            w.writeheader()
            w.writerows(cells)
        log.info("Wrote %s", comb_path)

    # Write status JSON
    status_path = out / "stage48_extension_status.json"
    existing_status = json.loads(status_path.read_text()) if status_path.exists() else {}
    existing_status.update({
        "current_matched_cells": n_matched,
        "threshold_met": n_matched >= MATCHED_CELL_THRESHOLD,
        "has_extension_data": has_ext,
        "ext_run_dir": str(ext_dir) if ext_dir else None,
        "analyzed_utc": datetime.utcnow().isoformat() + "Z",
    })
    status_path.write_text(json.dumps(existing_status, indent=2))

    # Write matched cells report
    write_matched_cells_report(cells, n_matched, has_ext, out / "stage48_matched_cells_report.md")

    # Write heatmap
    write_heatmap(cells, out / "fig_stage48_matched_cells_heatmap.png")

    # If threshold met: write behavior-conditioned direction README
    if n_matched >= MATCHED_CELL_THRESHOLD:
        bcd_readme = out / "behavior_conditioned_direction_README.md"
        bcd_readme.write_text(
            "# Behavior-Conditioned Direction Extraction\n\n"
            f"Threshold met: {n_matched} matched cells ≥ {MATCHED_CELL_THRESHOLD}.\n\n"
            "## Extraction Approach\n\n"
            "- Use Layer-22 first-500-token mean projection per example\n"
            "- Compare success vs failure within same (source_example_id × condition) cell\n"
            "- Leave-One-Prompt-Out cross-validation across source_example_ids\n"
            "- Do NOT compare across conditions (A vs D/F)\n"
            "- Report LOO AUC and confidence interval\n\n"
            "## Caution\n\n"
            "Even if a direction extracts cleanly, it captures *behavioral* differences,\n"
            "not a causal mechanism. The direction anti-correlates with thinking depth\n"
            "(see Stage 4.7 mechanistic analysis) and should not be interpreted as a\n"
            "refusal mechanism. Label as 'provisional behavior-contrast direction'.\n"
        )
        log.info("Wrote behavior_conditioned_direction_README.md")

    return 0


if __name__ == "__main__":
    sys.exit(main())
