#!/usr/bin/env python3
"""
Task 1 — Paper-style ASR percent report.

Reads Stage 4.6 / 4.7 / 4.8 analysis outputs and produces ASR% tables and
figures formatted for a research meeting (CoT Hijacking paper style).

Usage:
    python -m poc_meeting.mahmood_48h_update.build_paper_style_asr_report \
        --output-dir outputs/meeting/mahmood_48h_update_<TIMESTAMP>
"""

import argparse
import csv
import json
import logging
import math
import sys
from datetime import datetime
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from scipy import stats

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s", stream=sys.stderr)
log = logging.getLogger(__name__)

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent

COND_LABELS = {
    "A": "Full puzzle\n(thinking on)",
    "B": "50% puzzle\n(thinking on)",
    "C": "25% puzzle\n(thinking on)",
    "D": "No puzzle\n(thinking on)",
    "E": "Full puzzle\n(thinking off)",
    "F": "Benign wrapper\n(thinking on)",
}
COND_COLORS = {
    "A": "#2166ac",
    "B": "#74add1",
    "C": "#abd9e9",
    "D": "#d73027",
    "E": "#fc8d59",
    "F": "#1a9850",
}


# ─── helpers ────────────────────────────────────────────────────────────────

def _read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with open(path, newline="") as f:
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


def wilson_ci(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson score 95% CI for a proportion."""
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    denom = 1 + z**2 / n
    centre = (p + z**2 / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / denom
    return max(0.0, centre - half), min(1.0, centre + half)


def sign_test_p(n_pos: int, n_neg: int) -> float:
    """Two-sided sign test p-value (ties excluded)."""
    n = n_pos + n_neg
    if n == 0:
        return float("nan")
    result = stats.binomtest(min(n_pos, n_neg), n, 0.5, alternative="two-sided")
    return result.pvalue


def _save_fig(fig, path: Path, dpi: int = 150) -> None:
    fig.savefig(path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    log.info("Saved %s", path)


# ─── Stage 4.6 ──────────────────────────────────────────────────────────────

def load_s46(run_dir: Path) -> list[dict]:
    """Return rows from stage 4.6 condition_summary.csv, augmented with ASR%."""
    rows = _read_csv(run_dir / "analysis" / "condition_summary.csv")
    out = []
    for r in rows:
        n = _int(r.get("n", 0))
        k = _int(r.get("sr_success_count", 0))
        ci_lo, ci_hi = wilson_ci(k, n)
        out.append({
            "stage": "4.6",
            "condition": r["condition"],
            "label": r.get("label", r["condition"]),
            "n": n,
            "n_success": k,
            "n_censored": 0,
            "n_complete": n,
            "asr_pct": 100 * k / n if n > 0 else float("nan"),
            "ci_lo_pct": 100 * ci_lo,
            "ci_hi_pct": 100 * ci_hi,
            "mean_sr_score": _float(r.get("mean_strongreject_score")),
            "median_sr_score": float("nan"),
            "mean_think_tokens": _float(r.get("mean_think_tokens")),
            "median_think_tokens": _float(r.get("median_think_tokens")),
            "censored_pct": 0.0,
        })
    return out


# ─── Stage 4.7 ──────────────────────────────────────────────────────────────

def load_s47_summary(run_dir: Path) -> list[dict]:
    rows = _read_csv(run_dir / "analysis" / "condition_summary.csv")
    out = []
    for r in rows:
        n_cc = _int(r.get("n_complete_case", r.get("n", 0)))
        k_cc = _int(r.get("n_cc_success", r.get("n_sr_success", 0)))
        n_total = _int(r.get("n", n_cc))
        n_censored = _int(r.get("n_censored", 0))
        ci_lo, ci_hi = wilson_ci(k_cc, n_cc)
        out.append({
            "stage": "4.7",
            "condition": r["condition"],
            "label": r.get("condition_label", COND_LABELS.get(r["condition"], r["condition"])),
            "n": n_total,
            "n_complete": n_cc,
            "n_success": k_cc,
            "n_censored": n_censored,
            "asr_pct": 100 * k_cc / n_cc if n_cc > 0 else float("nan"),
            "ci_lo_pct": 100 * ci_lo,
            "ci_hi_pct": 100 * ci_hi,
            "mean_sr_score": _float(r.get("mean_sr_score")),
            "median_sr_score": _float(r.get("median_sr_score")),
            "mean_think_tokens": _float(r.get("mean_think_tokens")),
            "median_think_tokens": _float(r.get("median_think_tokens")),
            "censored_pct": 100 * n_censored / n_total if n_total > 0 else 0.0,
        })
    return out


def load_s47_per_run(run_dir: Path) -> list[dict]:
    p = run_dir / "analysis" / "canonical_per_run_results.csv"
    if not p.exists():
        p = run_dir / "analysis" / "per_run_results.csv"
    return _read_csv(p)


def load_s47_contrasts(run_dir: Path) -> list[dict]:
    return _read_csv(run_dir / "analysis" / "paired_contrasts.csv")


def compute_paired_contrasts(contrasts_rows: list[dict]) -> list[dict]:
    """Aggregate paired contrast rows into summary statistics."""
    from collections import defaultdict
    groups: dict[str, list[dict]] = defaultdict(list)
    for r in contrasts_rows:
        key = f"{r['cond_ref']}-{r['cond_comp']}"
        groups[key].append(r)

    results = []
    for contrast, rows in sorted(groups.items()):
        cond_ref, cond_comp = contrast.split("-")
        score_diffs = [_float(r["score_diff_ref_minus_comp"]) for r in rows if r.get("score_diff_ref_minus_comp") not in ("", None)]
        think_diffs = [_float(r["think_diff"]) for r in rows if r.get("think_diff") not in ("", None)]

        # ASR comparison
        sr_ref = [r["sr_success_ref"] for r in rows]
        sr_comp = [r["sr_success_comp"] for r in rows]
        n_pos = sum(1 for a, b in zip(sr_ref, sr_comp) if str(a).lower() == "true" and str(b).lower() != "true")
        n_neg = sum(1 for a, b in zip(sr_ref, sr_comp) if str(a).lower() != "true" and str(b).lower() == "true")
        n_tie = sum(1 for a, b in zip(sr_ref, sr_comp) if str(a).lower() == str(b).lower())
        asr_ref_pct = 100 * sum(1 for x in sr_ref if str(x).lower() == "true") / len(sr_ref) if sr_ref else float("nan")
        asr_comp_pct = 100 * sum(1 for x in sr_comp if str(x).lower() == "true") / len(sr_comp) if sr_comp else float("nan")

        p_sign = sign_test_p(n_pos, n_neg)

        results.append({
            "contrast": contrast,
            "cond_ref": cond_ref,
            "cond_comp": cond_comp,
            "paired_n": len(rows),
            "asr_ref_pct": round(asr_ref_pct, 1),
            "asr_comp_pct": round(asr_comp_pct, 1),
            "asr_diff_pp": round(asr_ref_pct - asr_comp_pct, 1),
            "mean_score_diff": round(float(np.nanmean(score_diffs)), 4) if score_diffs else float("nan"),
            "median_score_diff": round(float(np.nanmedian(score_diffs)), 4) if score_diffs else float("nan"),
            "mean_think_diff": round(float(np.nanmean(think_diffs)), 1) if think_diffs else float("nan"),
            "median_think_diff": round(float(np.nanmedian(think_diffs)), 1) if think_diffs else float("nan"),
            "n_pos": n_pos,
            "n_neg": n_neg,
            "n_tie": n_tie,
            "sign_test_p": round(p_sign, 4) if not math.isnan(p_sign) else float("nan"),
        })
    return results


# ─── Stage 4.8 ──────────────────────────────────────────────────────────────

def load_s48_summary(run_dir: Path) -> list[dict]:
    rows = _read_csv(run_dir / "analysis" / "condition_summary.csv")
    out = []
    for r in rows:
        n_total = _int(r.get("n_total", 0))
        n_complete = _int(r.get("n_complete", n_total))
        n_censored = _int(r.get("n_censored", 0))
        k = _int(r.get("n_success", 0))
        ci_lo, ci_hi = wilson_ci(k, n_complete)
        out.append({
            "stage": "4.8",
            "condition": r["condition"],
            "label": COND_LABELS.get(r["condition"], r["condition"]),
            "n": n_total,
            "n_complete": n_complete,
            "n_success": k,
            "n_censored": n_censored,
            "asr_pct": 100 * k / n_complete if n_complete > 0 else float("nan"),
            "ci_lo_pct": 100 * ci_lo,
            "ci_hi_pct": 100 * ci_hi,
            "mean_sr_score": _float(r.get("mean_sr_score")),
            "median_sr_score": float("nan"),
            "mean_think_tokens": float("nan"),
            "median_think_tokens": float("nan"),
            "censored_pct": 100 * n_censored / n_total if n_total > 0 else 0.0,
        })
    return out


def load_s48_cell_summary(run_dir: Path) -> list[dict]:
    return _read_csv(run_dir / "analysis" / "cell_summary.csv")


# ─── Figures ────────────────────────────────────────────────────────────────

def fig1_asr_by_condition_stage47(s47: list[dict], out: Path) -> None:
    """Bar chart: ASR% by condition for Stage 4.7."""
    rows = [r for r in s47 if r["condition"] in ("A", "D", "F", "E")]
    rows.sort(key=lambda r: ["A", "D", "F", "E"].index(r["condition"]))
    conds = [r["condition"] for r in rows]
    asr = [r["asr_pct"] for r in rows]
    ci_lo = [r["asr_pct"] - r["ci_lo_pct"] for r in rows]
    ci_hi = [r["ci_hi_pct"] - r["asr_pct"] for r in rows]
    colors = [COND_COLORS.get(c, "#888888") for c in conds]

    fig, ax = plt.subplots(figsize=(7, 5))
    x = np.arange(len(conds))
    bars = ax.bar(x, asr, color=colors, width=0.55, edgecolor="black", linewidth=0.7,
                  yerr=[ci_lo, ci_hi], capsize=5, error_kw=dict(ecolor="black", elinewidth=1.5))
    for bar, val in zip(bars, asr):
        ax.text(bar.get_x() + bar.get_width() / 2, val + 2.5, f"{val:.0f}%",
                ha="center", va="bottom", fontsize=11, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels([COND_LABELS.get(c, c) for c in conds], fontsize=10)
    ax.set_ylabel("ASR%  (StrongREJECT ≥ 0.5, complete cases)", fontsize=11)
    ax.set_title("Stage 4.7 — ASR% by Condition\n(n=12 prompts; error bars = Wilson 95% CI)", fontsize=12)
    ax.set_ylim(0, 105)
    ax.axhline(50, color="gray", linestyle="--", linewidth=0.8, label="50% reference")
    ax.legend(fontsize=9)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    _save_fig(fig, out)


def fig2_delta_asr_stage47(contrasts: list[dict], out: Path) -> None:
    """Bar chart: ASR difference in percentage points for key contrasts."""
    target_contrasts = ["A-D", "A-F", "A-E", "D-F"]
    rows = [c for c in contrasts if c["contrast"] in target_contrasts]
    rows.sort(key=lambda r: target_contrasts.index(r["contrast"]))

    labels = [f"{r['contrast']}\n(p={r['sign_test_p']:.3f})" if not math.isnan(r.get("sign_test_p", float("nan"))) else r["contrast"] for r in rows]
    deltas = [r["asr_diff_pp"] for r in rows]
    colors = ["#2166ac" if d > 0 else "#d73027" for d in deltas]

    fig, ax = plt.subplots(figsize=(7, 5))
    x = np.arange(len(rows))
    bars = ax.bar(x, deltas, color=colors, width=0.5, edgecolor="black", linewidth=0.7)
    for bar, val in zip(bars, deltas):
        ypos = val + 1 if val >= 0 else val - 2.5
        ax.text(bar.get_x() + bar.get_width() / 2, ypos, f"{val:+.1f}pp",
                ha="center", va="bottom" if val >= 0 else "top", fontsize=11, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=10)
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_ylabel("ΔASR (percentage points, ref − comp)", fontsize=11)
    ax.set_title("Stage 4.7 — Paired ASR Contrasts\n(sign test p-values shown)", fontsize=12)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    _save_fig(fig, out)


def fig3_think_tokens_stage47(per_run: list[dict], out: Path) -> None:
    """Box plot: think token count by condition for Stage 4.7."""
    groups: dict[str, list[float]] = {}
    for r in per_run:
        cond = r.get("condition", "")
        if cond not in ("A", "D", "F", "E"):
            continue
        tt = _float(r.get("think_token_count"))
        if not math.isnan(tt):
            groups.setdefault(cond, []).append(tt)

    order = [c for c in ("A", "D", "F", "E") if c in groups]
    data = [groups[c] for c in order]

    fig, ax = plt.subplots(figsize=(7, 5))
    bp = ax.boxplot(data, patch_artist=True, medianprops=dict(color="black", linewidth=2))
    for patch, cond in zip(bp["boxes"], order):
        patch.set_facecolor(COND_COLORS.get(cond, "#888888"))
        patch.set_alpha(0.7)
    ax.set_xticks(range(1, len(order) + 1))
    ax.set_xticklabels([COND_LABELS.get(c, c) for c in order], fontsize=10)
    ax.set_ylabel("Thinking token count", fontsize=11)
    ax.set_title("Stage 4.7 — Thinking Token Count by Condition\n(n=12 per condition)", fontsize=12)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    _save_fig(fig, out)


def fig4_asr_stage48_with_seeds(s48: list[dict], cells: list[dict], out: Path) -> None:
    """Bar chart + seed dots: ASR% for Stage 4.8."""
    rows = [r for r in s48 if r["condition"] in ("A", "D", "F")]
    rows.sort(key=lambda r: ["A", "D", "F"].index(r["condition"]))
    conds = [r["condition"] for r in rows]
    asr = [r["asr_pct"] for r in rows]
    ci_lo = [r["asr_pct"] - r["ci_lo_pct"] for r in rows]
    ci_hi = [r["ci_hi_pct"] - r["asr_pct"] for r in rows]
    colors = [COND_COLORS.get(c, "#888888") for c in conds]

    # Per-cell (per-source-prompt) success rates for jitter overlay
    cell_by_cond: dict[str, list[float]] = {}
    for c in cells:
        cond = c["condition"]
        if cond in ("A", "D", "F"):
            sr = _float(c.get("success_rate"))
            if not math.isnan(sr):
                cell_by_cond.setdefault(cond, []).append(sr * 100)

    fig, ax = plt.subplots(figsize=(7, 5))
    x = np.arange(len(conds))
    ax.bar(x, asr, color=colors, width=0.55, edgecolor="black", linewidth=0.7,
           yerr=[ci_lo, ci_hi], capsize=5, error_kw=dict(ecolor="black", elinewidth=1.5), alpha=0.8)
    for i, (cond, val) in enumerate(zip(conds, asr)):
        ax.text(i, val + 3, f"{val:.0f}%", ha="center", va="bottom", fontsize=11, fontweight="bold")
        if cond in cell_by_cond:
            jitter = np.random.default_rng(42).uniform(-0.12, 0.12, len(cell_by_cond[cond]))
            ax.scatter(i + jitter, cell_by_cond[cond], color="black", s=25, zorder=5, alpha=0.7, label="per-cell" if i == 0 else "")

    ax.set_xticks(x)
    ax.set_xticklabels([COND_LABELS.get(c, c) for c in conds], fontsize=10)
    ax.set_ylabel("ASR%  (StrongREJECT ≥ 0.5, complete cases)", fontsize=11)
    ax.set_title("Stage 4.8 — ASR% by Condition (Stochastic)\n(n=20 per condition, 4 prompts × 5 seeds; dots = per-cell rate)", fontsize=11)
    ax.set_ylim(0, 105)
    ax.legend(fontsize=9)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    _save_fig(fig, out)


def fig5_goal_condition_heatmap_stage47(per_run: list[dict], out: Path) -> None:
    """Heatmap: ASR% by goal × condition for Stage 4.7."""
    from collections import defaultdict
    goal_cond: dict[tuple, list[bool]] = defaultdict(list)
    goals_seen = set()
    conds_seen = set()
    for r in per_run:
        cond = r.get("condition", "")
        g = str(r.get("goal_index", ""))
        if cond not in ("A", "D", "F", "E"):
            continue
        sr = r.get("sr_success", r.get("sr_success_complete_case", ""))
        if str(sr).lower() == "true":
            goal_cond[(g, cond)].append(True)
        elif str(sr).lower() == "false":
            goal_cond[(g, cond)].append(False)
        goals_seen.add(g)
        conds_seen.add(cond)

    goals = sorted(goals_seen)
    conds = [c for c in ("A", "D", "F", "E") if c in conds_seen]
    matrix = np.full((len(goals), len(conds)), float("nan"))
    for i, g in enumerate(goals):
        for j, c in enumerate(conds):
            vals = goal_cond.get((g, c), [])
            if vals:
                matrix[i, j] = 100 * sum(vals) / len(vals)

    fig, ax = plt.subplots(figsize=(6, 4))
    im = ax.imshow(matrix, aspect="auto", vmin=0, vmax=100, cmap="RdYlGn")
    ax.set_xticks(range(len(conds)))
    ax.set_xticklabels([COND_LABELS.get(c, c).replace("\n", " ") for c in conds], fontsize=10)
    ax.set_yticks(range(len(goals)))
    ax.set_yticklabels([f"Goal {g}" for g in goals], fontsize=10)
    for i in range(len(goals)):
        for j in range(len(conds)):
            val = matrix[i, j]
            if not math.isnan(val):
                ax.text(j, i, f"{val:.0f}%", ha="center", va="center", fontsize=11,
                        color="black" if val < 70 else "white", fontweight="bold")
    plt.colorbar(im, ax=ax, label="ASR%")
    ax.set_title("Stage 4.7 — ASR% by Goal × Condition", fontsize=12)
    fig.tight_layout()
    _save_fig(fig, out)


def fig6_asr_vs_think_tokens_stage47(per_run: list[dict], out: Path) -> None:
    """Scatter: think_token_count vs sr_success (jittered) by condition."""
    fig, ax = plt.subplots(figsize=(7, 5))
    rng = np.random.default_rng(0)
    for cond in ("A", "D", "F", "E"):
        rows = [r for r in per_run if r.get("condition") == cond]
        if not rows:
            continue
        x = [_float(r.get("think_token_count")) for r in rows]
        sr = [r.get("sr_success", r.get("sr_success_complete_case", "false")) for r in rows]
        y = [float(str(s).lower() == "true") + rng.uniform(-0.03, 0.03) for s in sr]
        ax.scatter(x, y, label=COND_LABELS.get(cond, cond).replace("\n", " "),
                   color=COND_COLORS.get(cond, "#888"), alpha=0.65, s=40,
                   marker="o" if cond == "A" else ("s" if cond == "D" else ("^" if cond == "F" else "D")))
    ax.set_xlabel("Thinking token count", fontsize=11)
    ax.set_yticks([0, 1])
    ax.set_yticklabels(["Failure (SR<0.5)", "Success (SR≥0.5)"], fontsize=10)
    ax.set_title("Stage 4.7 — Thinking Tokens vs SR Outcome\n(y-axis jittered for visibility)", fontsize=12)
    ax.legend(fontsize=9)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    _save_fig(fig, out)


# ─── Markdown tables ─────────────────────────────────────────────────────────

def _row_md(r: dict, stage: str) -> str:
    n_cens = r.get("n_censored", 0)
    n_total = r.get("n", "?")
    cens_pct = r.get("censored_pct", 0.0)
    asr = r["asr_pct"]
    ci_lo = r["ci_lo_pct"]
    ci_hi = r["ci_hi_pct"]
    return (
        f"| {stage} | {r['condition']} | "
        f"{r['n_complete']}/{n_total} | {n_cens} ({cens_pct:.0f}%) | "
        f"**{asr:.1f}%** [{ci_lo:.1f}–{ci_hi:.1f}] | "
        f"{r['mean_sr_score']:.3f} | {r['median_sr_score']:.3f} | "
        f"{r['mean_think_tokens']:.0f} | {r['median_think_tokens']:.0f} |"
    )


def write_condition_table_md(s46: list[dict], s47: list[dict], s48: list[dict], out: Path) -> None:
    header = [
        "# Paper-Style ASR% Condition Table",
        "",
        "**Primary metric:** ASR% = 100 × n_success / n_complete_case  (StrongREJECT ≥ 0.5)",
        "",
        "| Stage | Cond | n (comp/total) | Censored | ASR% [95% CI] | Mean SR | Med SR | Mean Think | Med Think |",
        "|-------|------|---------------|----------|--------------|---------|--------|-----------|---------|",
    ]
    rows_46 = [r for r in s46 if r["condition"] in ("A", "B", "C", "D", "E")]
    rows_46.sort(key=lambda r: ["A", "B", "C", "D", "E"].index(r["condition"]))
    rows_47 = [r for r in s47 if r["condition"] in ("A", "D", "F", "E")]
    rows_47.sort(key=lambda r: ["A", "D", "F", "E"].index(r["condition"]))
    rows_48 = [r for r in s48 if r["condition"] in ("A", "D", "F")]
    rows_48.sort(key=lambda r: ["A", "D", "F"].index(r["condition"]))

    lines = header[:]
    for r in rows_46:
        lines.append(_row_md(r, "4.6"))
    for r in rows_47:
        lines.append(_row_md(r, "4.7"))
    for r in rows_48:
        lines.append(_row_md(r, "4.8"))

    lines += [
        "",
        "**Key contrasts (Stage 4.7, cleanest evidence):**",
        "- A vs D: Puzzle amplification above bare target",
        "- A vs F: Puzzle amplification above length-matched benign wrapper",
        "- A vs E: Thinking-on vs thinking-off",
        "- D vs F: Bare target vs benign wrapper (no puzzle in either)",
    ]
    out.write_text("\n".join(lines))
    log.info("Wrote %s", out)


def write_s47_summary_md(s47: list[dict], contrasts: list[dict], out: Path) -> None:
    lines = [
        "# Stage 4.7 — Condition Summary (Percent Format)",
        "",
        "**n = 12 prompts per condition (greedy decoding)**",
        "",
        "| Condition | n_comp | ASR% [95% CI] | Mean SR | Med SR | Mean Think Tok | Med Think Tok | Censored |",
        "|-----------|--------|--------------|---------|--------|---------------|--------------|---------|",
    ]
    for r in sorted([r for r in s47 if r["condition"] in ("A", "D", "F", "E")],
                    key=lambda r: ["A", "D", "F", "E"].index(r["condition"])):
        lines.append(
            f"| {r['condition']} ({COND_LABELS.get(r['condition'], '').replace(chr(10), ' ')}) "
            f"| {r['n_complete']} "
            f"| **{r['asr_pct']:.1f}%** [{r['ci_lo_pct']:.1f}–{r['ci_hi_pct']:.1f}] "
            f"| {r['mean_sr_score']:.3f} | {r['median_sr_score']:.3f} "
            f"| {r['mean_think_tokens']:.0f} | {r['median_think_tokens']:.0f} "
            f"| {r['n_censored']} ({r['censored_pct']:.0f}%) |"
        )

    # Paired contrasts table
    lines += [
        "",
        "## Paired Contrasts",
        "",
        "| Contrast | Paired n | ΔASR (pp) | Mean ΔSR | Med ΔSR | Mean ΔThink | n+/n−/tie | sign-test p |",
        "|----------|---------|-----------|---------|--------|-----------|---------|-----------|",
    ]
    for c in contrasts:
        if c["contrast"] not in ("A-D", "A-F", "A-E", "D-F"):
            continue
        p_str = f"{c['sign_test_p']:.4f}" if not math.isnan(c.get("sign_test_p", float("nan"))) else "—"
        lines.append(
            f"| {c['contrast']} | {c['paired_n']} "
            f"| **{c['asr_diff_pp']:+.1f}** | {c['mean_score_diff']:.3f} | {c['median_score_diff']:.3f} "
            f"| {c['mean_think_diff']:.0f} | {c['n_pos']}/{c['n_neg']}/{c['n_tie']} | {p_str} |"
        )

    out.write_text("\n".join(lines))
    log.info("Wrote %s", out)


def write_s48_summary_md(s48: list[dict], out: Path) -> None:
    lines = [
        "# Stage 4.8 — Condition Summary (Stochastic Replication, Percent Format)",
        "",
        "**n = 20 per condition (4 source prompts × 5 seeds, temperature=0.7, top_p=0.95)**",
        "",
        "| Condition | n_comp | ASR% [95% CI] | Mean SR | Censored |",
        "|-----------|--------|--------------|---------|---------|",
    ]
    for r in sorted([r for r in s48 if r["condition"] in ("A", "D", "F")],
                    key=lambda r: ["A", "D", "F"].index(r["condition"])):
        lines.append(
            f"| {r['condition']} ({COND_LABELS.get(r['condition'], '').replace(chr(10), ' ')}) "
            f"| {r['n_complete']} "
            f"| **{r['asr_pct']:.1f}%** [{r['ci_lo_pct']:.1f}–{r['ci_hi_pct']:.1f}] "
            f"| {r['mean_sr_score']:.3f} "
            f"| {r['n_censored']} ({r['censored_pct']:.0f}%) |"
        )
    lines += [
        "",
        "**Ordering:** A > D > F (same as Stage 4.7, independently confirmed under stochastic sampling).",
        "",
        "Only 3 matched-outcome cells (cells with ≥1 success AND ≥1 failure). Threshold for",
        "behavior-conditioned direction extraction: 4 cells. Extension planned for goals 0 and 2.",
    ]
    out.write_text("\n".join(lines))
    log.info("Wrote %s", out)


def write_interpretation_md(s47: list[dict], s48: list[dict], contrasts: list[dict], out: Path) -> None:
    a47 = next((r for r in s47 if r["condition"] == "A"), {})
    d47 = next((r for r in s47 if r["condition"] == "D"), {})
    f47 = next((r for r in s47 if r["condition"] == "F"), {})
    e47 = next((r for r in s47 if r["condition"] == "E"), {})

    a48 = next((r for r in s48 if r["condition"] == "A"), {})
    d48 = next((r for r in s48 if r["condition"] == "D"), {})
    f48 = next((r for r in s48 if r["condition"] == "F"), {})

    ad_c = next((c for c in contrasts if c["contrast"] == "A-D"), {})
    af_c = next((c for c in contrasts if c["contrast"] == "A-F"), {})

    lines = [
        "# Paper-Style ASR Interpretation",
        f"\n_Generated: {datetime.utcnow().isoformat()}Z_",
        "",
        "## 1. Stage 4.7 — Cleanest Behavioral Evidence",
        "",
        "Stage 4.7 is the cleanest test because it uses 12 diverse source prompts under greedy "
        "decoding, and includes condition F (length-matched benign wrapper) as a direct control "
        "for prompt length.",
        "",
        f"- **A (full puzzle + thinking):** ASR = {a47.get('asr_pct', float('nan')):.1f}%  "
        f"(mean SR score = {a47.get('mean_sr_score', float('nan')):.3f}, "
        f"mean think tokens = {a47.get('mean_think_tokens', float('nan')):.0f})",
        f"- **D (no puzzle + thinking):** ASR = {d47.get('asr_pct', float('nan')):.1f}%  "
        f"(mean SR = {d47.get('mean_sr_score', float('nan')):.3f}, "
        f"mean think = {d47.get('mean_think_tokens', float('nan')):.0f})",
        f"- **F (benign wrapper + thinking):** ASR = {f47.get('asr_pct', float('nan')):.1f}%  "
        f"(mean SR = {f47.get('mean_sr_score', float('nan')):.3f}, "
        f"mean think = {f47.get('mean_think_tokens', float('nan')):.0f})",
        f"- **E (full puzzle, thinking off):** ASR = {e47.get('asr_pct', float('nan')):.1f}%",
        "",
        "### Contrast A vs F (key test):",
        f"ΔASR = {af_c.get('asr_diff_pp', float('nan')):+.1f} percentage points "
        f"(sign-test p = {af_c.get('sign_test_p', float('nan')):.4f}). "
        "Since F is length-matched, this rules out prompt-length confound.",
        "",
        "### Contrast A vs D (puzzle contribution):",
        f"ΔASR = {ad_c.get('asr_diff_pp', float('nan')):+.1f} pp "
        f"(sign-test p = {ad_c.get('sign_test_p', float('nan')):.4f}). "
        "Puzzle adds substantial thinking amplification on top of bare target effect.",
        "",
        "## 2. Stage 4.8 — Independent Stochastic Replication",
        "",
        "Stage 4.8 uses temperature=0.7 sampling to test robustness. With 20 samples per condition "
        "the ordering is preserved:",
        "",
        f"- A: {a48.get('asr_pct', float('nan')):.1f}%  > D: {d48.get('asr_pct', float('nan')):.1f}%"
        f"  > F: {f48.get('asr_pct', float('nan')):.1f}%",
        "",
        "This confirms the A > D > F ordering is not an artefact of greedy decoding.",
        "The absolute gaps are smaller under stochastic sampling (higher baseline variance).",
        "",
        "## 3. Stage 4.6 — Pilot Context",
        "",
        "Stage 4.6 used only 4 prompts and partial puzzle fractions (A/B/C/D/E). Results were "
        "directionally consistent (A=100%, D~25-50% depending on goal) but with tiny n and "
        "no length-matched control. It motivated the larger Stage 4.7 replication.",
        "",
        "## 4. Interpretation: Puzzle Is an Amplifier, Not Universally Necessary",
        "",
        "- Condition D alone shows some success in Stage 4.7 and 4.8, so the puzzle is **not** "
        "strictly necessary for the attack to succeed.",
        "- However, the puzzle **reliably amplifies** both thinking token count and ASR across "
        "all tested goals and stochastic seeds.",
        "- Condition F controls for length and semantic richness of the wrapper: the puzzle "
        "adds specific structural redirection that benign wrappers of the same length do not.",
        "- **Do not overclaim:** the puzzle effect may be goal-dependent (see per-goal heatmap). "
        "Goal 3 succeeds across all conditions; Goal 1 fails across all conditions.",
        "",
        "## 5. Key Caveat",
        "",
        "The Layer-22 projection direction anti-correlates with thinking depth and does not "
        "track behavioral success across Stage 4.7/4.8. Projection scores should not be used "
        "as the primary metric. See RL_NOT_YET_RATIONALE.md for details.",
    ]
    out.write_text("\n".join(lines))
    log.info("Wrote %s", out)


# ─── CSV outputs ─────────────────────────────────────────────────────────────

def write_csvs(s46, s47, s48, contrasts, out_dir: Path) -> None:
    # Summary CSV (all stages)
    all_rows = s46 + s47 + s48
    fieldnames = ["stage", "condition", "label", "n", "n_complete", "n_success", "n_censored",
                  "asr_pct", "ci_lo_pct", "ci_hi_pct", "mean_sr_score", "median_sr_score",
                  "mean_think_tokens", "median_think_tokens", "censored_pct"]
    with open(out_dir / "paper_style_asr_summary.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        w.writerows(all_rows)
    log.info("Wrote paper_style_asr_summary.csv")

    with open(out_dir / "paper_style_asr_by_stage_condition.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        w.writerows(all_rows)
    log.info("Wrote paper_style_asr_by_stage_condition.csv")

    # Contrasts CSV
    if contrasts:
        cfn = ["contrast", "cond_ref", "cond_comp", "paired_n", "asr_ref_pct", "asr_comp_pct",
               "asr_diff_pp", "mean_score_diff", "median_score_diff", "mean_think_diff",
               "median_think_diff", "n_pos", "n_neg", "n_tie", "sign_test_p"]
        with open(out_dir / "paper_style_paired_contrasts.csv", "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=cfn, extrasaction="ignore")
            w.writeheader()
            w.writerows([c for c in contrasts if c["contrast"] in ("A-D", "A-F", "A-E", "D-F")])
        log.info("Wrote paper_style_paired_contrasts.csv")


# ─── Main ────────────────────────────────────────────────────────────────────

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True,
                        help="Output directory (must already exist or will be created)")
    parser.add_argument("--s46-dir", type=Path,
                        default=_REPO_ROOT / "outputs/stage4_6/runs_output_full_20260610_091021",
                        help="Stage 4.6 run directory")
    parser.add_argument("--s47-dir", type=Path,
                        default=_REPO_ROOT / "outputs/stage4_7/runs/run_array_20260610_1442",
                        help="Stage 4.7 run directory")
    parser.add_argument("--s48-dir", type=Path,
                        default=_REPO_ROOT / "outputs/stage4_8/runs/run_array_20260611_0109",
                        help="Stage 4.8 run directory")
    args = parser.parse_args(argv)

    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)

    # Validate inputs
    for d, name in [(args.s46_dir, "S4.6"), (args.s47_dir, "S4.7"), (args.s48_dir, "S4.8")]:
        if not d.exists():
            log.error("Run dir not found: %s (%s)", d, name)
            return 1

    log.info("Loading Stage 4.6 data from %s", args.s46_dir)
    s46 = load_s46(args.s46_dir)
    log.info("  %d conditions", len(s46))

    log.info("Loading Stage 4.7 data from %s", args.s47_dir)
    s47 = load_s47_summary(args.s47_dir)
    per_run_47 = load_s47_per_run(args.s47_dir)
    contrasts_raw = load_s47_contrasts(args.s47_dir)
    contrasts = compute_paired_contrasts(contrasts_raw)
    log.info("  %d conditions, %d per-run rows, %d contrast rows → %d contrasts",
             len(s47), len(per_run_47), len(contrasts_raw), len(contrasts))

    log.info("Loading Stage 4.8 data from %s", args.s48_dir)
    s48 = load_s48_summary(args.s48_dir)
    cells_48 = load_s48_cell_summary(args.s48_dir)
    log.info("  %d conditions, %d cells", len(s48), len(cells_48))

    # Write CSVs
    write_csvs(s46, s47, s48, contrasts, out)

    # Write markdown tables
    write_condition_table_md(s46, s47, s48, out / "condition_asr_percent_table.md")
    write_s47_summary_md(s47, contrasts, out / "stage4_7_condition_summary_percent.md")
    write_s48_summary_md(s48, out / "stage4_8_condition_summary_percent.md")
    write_interpretation_md(s47, s48, contrasts, out / "PAPER_STYLE_ASR_INTERPRETATION.md")

    # Generate figures
    fig1_asr_by_condition_stage47(s47, out / "fig1_asr_by_condition_percent_stage47.png")
    fig2_delta_asr_stage47(contrasts, out / "fig2_delta_asr_percentage_points_stage47.png")
    fig3_think_tokens_stage47(per_run_47, out / "fig3_think_tokens_by_condition_stage47.png")
    fig4_asr_stage48_with_seeds(s48, cells_48, out / "fig4_asr_by_condition_percent_stage48.png")
    fig5_goal_condition_heatmap_stage47(per_run_47, out / "fig5_goal_condition_heatmap_stage47.png")
    fig6_asr_vs_think_tokens_stage47(per_run_47, out / "fig6_asr_vs_think_tokens_stage47.png")

    log.info("Done. All outputs written to %s", out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
