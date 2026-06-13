"""
Deep L22 temporal analysis: WHERE in the thinking block does the
provisional harmful-vs-harmless contrast direction separate success from failure?

The projection_summary.jsonl contains 10 normalized time bins for Layer 22:
  layer22_normalized_bin_1  ...  layer22_normalized_bin_10

Bin 1 = first 10% of thinking tokens, bin 10 = last 10%.

This analysis tests:
1. Does L22 separation appear early (bins 1-3) or late (bins 7-10)?
2. Does Condition A (high ASR) show systematically lower L22 throughout,
   or only in specific phases?
3. Is the L22 pattern consistent with "delayed safety commitment" —
   i.e., does the model commit early (low L22 early) or hesitate (high L22 early)?

IMPORTANT: All findings labeled 'provisional' — L22 direction is not validated.
"""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path

try:
    from PIL import Image, ImageDraw
    _PIL_OK = True
except ImportError:
    _PIL_OK = False

_REPO_ROOT = Path(__file__).resolve().parent.parent
_PROJ_JSONL = _REPO_ROOT / "outputs/stage4_7/runs/run_array_20260610_1442/projection_analysis/projection_summary.jsonl"
_CANON_CSV = _REPO_ROOT / "outputs/stage4_7/runs/run_array_20260610_1442/analysis/canonical_per_run_results.csv"
_OUT_DIR = _REPO_ROOT / "outputs/rl_experiment/l22_temporal_analysis"

N_BINS = 10
CONDITIONS = ["A", "D", "F", "E"]
CONDITION_COLORS = {
    "A": (70, 130, 180),
    "D": (60, 179, 113),
    "F": (205, 92, 92),
    "E": (255, 165, 0),
}
SUCCESS_COLOR = (70, 130, 180)
FAILURE_COLOR = (205, 92, 92)


def _safe_float(v) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return math.nan


def load_data() -> list[dict]:
    """Load and merge projection + canonical data."""
    proj = {}
    for line in _PROJ_JSONL.read_text().splitlines():
        line = line.strip()
        if line:
            r = json.loads(line)
            proj[r["run_id"]] = r

    rows = []
    for row in csv.DictReader(_CANON_CSV.open()):
        run_id = row["run_id"]
        pr = proj.get(run_id, {})
        merged = {
            "run_id": run_id,
            "goal_idx": int(row.get("goal_index", 0)),
            "condition": row["condition"],
            "sr_success": row["sr_success"] == "True",
            "sr_score": _safe_float(row.get("strongreject_score", "")),
            "think_tokens": int(_safe_float(row.get("think_token_count", "0"), )),
            "l22_think_phase": _safe_float(pr.get("layer22_think_phase_mean_projection", "")),
            "l22_first_500": _safe_float(pr.get("layer22_first_500_mean_projection", "")),
            "l22_last_500_think": _safe_float(pr.get("layer22_last_500_think_mean_projection", "")),
        }
        for b in range(1, N_BINS + 1):
            merged[f"l22_bin_{b}"] = _safe_float(pr.get(f"layer22_normalized_bin_{b}", ""))
        rows.append(merged)
    return rows


def _mean(vals: list[float]) -> float:
    valid = [v for v in vals if not math.isnan(v)]
    return sum(valid) / len(valid) if valid else math.nan


def _std(vals: list[float]) -> float:
    valid = [v for v in vals if not math.isnan(v)]
    if len(valid) < 2:
        return math.nan
    m = sum(valid) / len(valid)
    return math.sqrt(sum((x - m) ** 2 for x in valid) / (len(valid) - 1))


def analyze_temporal(rows: list[dict]) -> dict:
    """Per-bin L22 means split by condition and outcome."""
    result = {}

    # 1. By condition
    by_cond: dict[str, dict[str, list[float]]] = {c: {f"bin_{b}": [] for b in range(1, N_BINS+1)} for c in CONDITIONS}
    by_cond_overall: dict[str, list] = {c: [] for c in CONDITIONS}

    # 2. By outcome (success/failure) across all conditions
    by_outcome: dict[str, dict[str, list[float]]] = {
        "success": {f"bin_{b}": [] for b in range(1, N_BINS+1)},
        "failure": {f"bin_{b}": [] for b in range(1, N_BINS+1)},
    }

    # 3. By condition × outcome
    by_cond_outcome: dict[str, dict[str, dict[str, list[float]]]] = {
        c: {
            "success": {f"bin_{b}": [] for b in range(1, N_BINS+1)},
            "failure": {f"bin_{b}": [] for b in range(1, N_BINS+1)},
        }
        for c in CONDITIONS
    }

    for row in rows:
        c = row["condition"]
        outcome = "success" if row["sr_success"] else "failure"
        for b in range(1, N_BINS + 1):
            v = row[f"l22_bin_{b}"]
            if not math.isnan(v):
                if c in by_cond:
                    by_cond[c][f"bin_{b}"].append(v)
                by_outcome[outcome][f"bin_{b}"].append(v)
                if c in by_cond_outcome:
                    by_cond_outcome[c][outcome][f"bin_{b}"].append(v)
        l22 = row["l22_think_phase"]
        if not math.isnan(l22) and c in by_cond_overall:
            by_cond_overall[c].append(l22)

    result["by_condition_overall"] = {
        c: {"mean_l22": round(_mean(vals), 4), "n": len(vals), "asr": round(sum(r["sr_success"] for r in rows if r["condition"] == c) / max(len([r for r in rows if r["condition"] == c]), 1), 3)}
        for c, vals in by_cond_overall.items()
    }
    result["by_condition_bins"] = {
        c: {f"bin_{b}": round(_mean(by_cond[c][f"bin_{b}"]), 4) for b in range(1, N_BINS+1)}
        for c in CONDITIONS
    }
    result["by_outcome_bins"] = {
        outcome: {f"bin_{b}": round(_mean(by_outcome[outcome][f"bin_{b}"]), 4) for b in range(1, N_BINS+1)}
        for outcome in ["success", "failure"]
    }
    result["delta_outcome_bins"] = {
        f"bin_{b}": round(
            _mean(by_outcome["success"][f"bin_{b}"]) - _mean(by_outcome["failure"][f"bin_{b}"]), 4
        )
        for b in range(1, N_BINS+1)
    }
    result["by_cond_outcome"] = {
        c: {
            outcome: {f"bin_{b}": round(_mean(by_cond_outcome[c][outcome][f"bin_{b}"]), 4) for b in range(1, N_BINS+1)}
            for outcome in ["success", "failure"]
        }
        for c in CONDITIONS
    }

    # Find the bin with maximum separation between success and failure
    bin_deltas = [(b, abs(_mean(by_outcome["success"][f"bin_{b}"]) - _mean(by_outcome["failure"][f"bin_{b}"])))
                  for b in range(1, N_BINS+1)
                  if not math.isnan(_mean(by_outcome["success"][f"bin_{b}"])) and not math.isnan(_mean(by_outcome["failure"][f"bin_{b}"]))]
    if bin_deltas:
        max_sep_bin = max(bin_deltas, key=lambda x: x[1])
        result["max_separation_bin"] = max_sep_bin[0]
        result["max_separation_delta"] = round(max_sep_bin[1], 4)

    # Early vs late analysis (bins 1-3 vs bins 8-10)
    early_sep = _mean([abs(_mean(by_outcome["success"][f"bin_{b}"]) - _mean(by_outcome["failure"][f"bin_{b}"]))
                       for b in range(1, 4)
                       if not math.isnan(_mean(by_outcome["success"][f"bin_{b}"]))])
    late_sep = _mean([abs(_mean(by_outcome["success"][f"bin_{b}"]) - _mean(by_outcome["failure"][f"bin_{b}"]))
                      for b in range(8, N_BINS+1)
                      if not math.isnan(_mean(by_outcome["success"][f"bin_{b}"]))])
    result["early_vs_late"] = {
        "early_mean_sep": round(early_sep, 4),
        "late_mean_sep": round(late_sep, 4),
        "interpretation": (
            "Earlier separation" if early_sep > late_sep else "Later separation"
        ) + " (consistent with " + (
            "'early commitment' — refusal direction dampened from start of thinking"
            if early_sep > late_sep else
            "'gradual commitment' — refusal direction changes over thinking duration"
        ) + ")",
    }

    return result


def generate_temporal_figure(analysis: dict, out_path: Path) -> None:
    if not _PIL_OK:
        return
    W, H = 1100, 700
    img = Image.new("RGB", (W, H), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    title = "L22 Temporal Analysis: Projection over 10 thinking-block bins"
    draw.text((20, 12), title, fill=(0, 0, 0))
    draw.text((20, 30), "(provisional harmful-vs-harmless contrast direction, Layer 22 of Qwen3-14B)", fill=(100, 100, 100))

    # Two sub-plots: by condition (left) and success vs failure (right)
    _plot_lines(draw, analysis["by_condition_bins"], "By Condition",
                60, 70, 500, 600, CONDITION_COLORS)
    _plot_lines_pair(draw, analysis["by_outcome_bins"]["success"],
                     analysis["by_outcome_bins"]["failure"],
                     "By Outcome (all conditions)", "Success", "Failure",
                     580, 70, 1060, 600, SUCCESS_COLOR, FAILURE_COLOR)

    img.save(str(out_path))


def _plot_lines(draw, bins_by_key: dict, title: str, x0, y0, x1, y1, color_map: dict) -> None:
    all_vals = [v for series in bins_by_key.values() for v in series.values() if not math.isnan(v)]
    if not all_vals:
        return
    y_min = min(all_vals) - 0.3
    y_max = max(all_vals) + 0.3
    y_range = y_max - y_min

    draw.text((x0, y0 - 18), title, fill=(0, 0, 0))
    draw.line([(x0, y0), (x0, y1)], fill=(0, 0, 0), width=2)
    draw.line([(x0, y1), (x1, y1)], fill=(0, 0, 0), width=2)

    for y_tick in [y_min, (y_min + y_max) / 2, y_max]:
        py = int(y1 - (y_tick - y_min) / y_range * (y1 - y0))
        draw.line([(x0 - 4, py), (x0, py)], fill=(0, 0, 0))
        draw.text((x0 - 40, py - 6), f"{y_tick:.1f}", fill=(0, 0, 0))

    bin_w = (x1 - x0) / N_BINS
    for i in range(1, N_BINS + 1):
        bx = int(x0 + (i - 0.5) * bin_w)
        draw.text((bx - 4, y1 + 4), str(i), fill=(0, 0, 0))

    legend_y = y0
    for key, series in sorted(bins_by_key.items()):
        color = color_map.get(key, (100, 100, 100))
        pts = []
        for b in range(1, N_BINS + 1):
            v = series.get(f"bin_{b}", math.nan)
            if math.isnan(v):
                continue
            px = int(x0 + (b - 0.5) * bin_w)
            py = int(y1 - (v - y_min) / y_range * (y1 - y0))
            pts.append((px, py))
        for i in range(len(pts) - 1):
            draw.line([pts[i], pts[i+1]], fill=color, width=2)
        if pts:
            draw.ellipse([pts[0][0]-3, pts[0][1]-3, pts[0][0]+3, pts[0][1]+3], fill=color)
        draw.rectangle([x1 - 80, legend_y, x1 - 65, legend_y + 10], fill=color)
        draw.text((x1 - 60, legend_y), key, fill=(0, 0, 0))
        legend_y += 18


def _plot_lines_pair(draw, series_success: dict, series_failure: dict,
                     title: str, label_s: str, label_f: str,
                     x0, y0, x1, y1, color_s, color_f) -> None:
    all_vals = [v for d in [series_success, series_failure] for v in d.values() if not math.isnan(v)]
    if not all_vals:
        return
    y_min = min(all_vals) - 0.3
    y_max = max(all_vals) + 0.3
    y_range = y_max - y_min

    draw.text((x0, y0 - 18), title, fill=(0, 0, 0))
    draw.line([(x0, y0), (x0, y1)], fill=(0, 0, 0), width=2)
    draw.line([(x0, y1), (x1, y1)], fill=(0, 0, 0), width=2)

    for y_tick in [y_min, (y_min + y_max) / 2, y_max]:
        py = int(y1 - (y_tick - y_min) / y_range * (y1 - y0))
        draw.line([(x0 - 4, py), (x0, py)], fill=(0, 0, 0))
        draw.text((x0 - 40, py - 6), f"{y_tick:.1f}", fill=(0, 0, 0))

    bin_w = (x1 - x0) / N_BINS
    for i in range(1, N_BINS + 1):
        bx = int(x0 + (i - 0.5) * bin_w)
        draw.text((bx - 4, y1 + 4), str(i), fill=(0, 0, 0))

    for series, color, label in [(series_success, color_s, label_s), (series_failure, color_f, label_f)]:
        pts = []
        for b in range(1, N_BINS + 1):
            v = series.get(f"bin_{b}", math.nan)
            if math.isnan(v):
                continue
            px = int(x0 + (b - 0.5) * bin_w)
            py = int(y1 - (v - y_min) / y_range * (y1 - y0))
            pts.append((px, py))
        for i in range(len(pts) - 1):
            draw.line([pts[i], pts[i+1]], fill=color, width=2)
        if pts:
            draw.ellipse([pts[0][0]-3, pts[0][1]-3, pts[0][0]+3, pts[0][1]+3], fill=color)
        legend_x = x1 - 120
        legend_y = y0 + (0 if label == label_s else 20)
        draw.rectangle([legend_x, legend_y, legend_x + 15, legend_y + 10], fill=color)
        draw.text((legend_x + 20, legend_y), label, fill=(0, 0, 0))


def write_report(analysis: dict, out_dir: Path) -> Path:
    lines = [
        "# L22 Temporal Analysis — Thinking-Block Projection Dynamics",
        "",
        "**Generated by:** `poc_rl_loop/analyze_l22_temporal.py`",
        "**Data source:** Stage 4.7 `projection_summary.jsonl` (48 rows)",
        "**Layer 22 direction:** Provisional harmful-vs-harmless contrast direction",
        "**IMPORTANT:** All findings are exploratory. L22 is not validated as a causal refusal mechanism.",
        "",
        "---",
        "",
        "## 1. L22 Projection by Condition (overall thinking-phase mean)",
        "",
        "| Condition | N | ASR | Mean L22 |",
        "|-----------|---|-----|---------|",
    ]
    for c, info in sorted(analysis["by_condition_overall"].items()):
        lines.append(f"| {c} | {info['n']} | {info['asr']:.1%} | {info['mean_l22']:.4f} |")

    lines += [
        "",
        "## 2. L22 Projection Over 10 Normalized Bins (success vs failure)",
        "",
        "Bin 1 = first 10% of thinking tokens; Bin 10 = last 10%.",
        "",
        "| Bin | Success | Failure | Delta (S-F) | Interpretation |",
        "|-----|---------|---------|------------|----------------|",
    ]
    for b in range(1, N_BINS + 1):
        s = analysis["by_outcome_bins"]["success"][f"bin_{b}"]
        f = analysis["by_outcome_bins"]["failure"][f"bin_{b}"]
        d = analysis["delta_outcome_bins"][f"bin_{b}"]
        direction = "lower in success" if d < 0 else "higher in success"
        lines.append(f"| {b} | {s:.3f} | {f:.3f} | {d:+.3f} | {direction} |")

    ev_late = analysis.get("early_vs_late", {})
    lines += [
        "",
        "## 3. Early vs Late Separation",
        "",
        f"- **Bins 1-3 (early):** mean |delta| = {ev_late.get('early_mean_sep', '?'):.4f}",
        f"- **Bins 8-10 (late):** mean |delta| = {ev_late.get('late_mean_sep', '?'):.4f}",
        f"- **{ev_late.get('interpretation', '')}**",
        "",
        f"Maximum separation at **bin {analysis.get('max_separation_bin', '?')}** "
        f"(|delta| = {analysis.get('max_separation_delta', '?'):.4f}).",
        "",
        "## 4. What This Means for Delayed Safety Commitment",
        "",
        "If L22 separation is **early** (bins 1-3): the refusal direction is dampened from the",
        "very start of thinking. This suggests the model 'commits' to processing the harmful",
        "target almost immediately — consistent with the strong delayed safety commitment hypothesis.",
        "",
        "If L22 separation is **late** (bins 7-10): the model initially shows similar refusal",
        "direction activation, but diverges near the end of thinking. This is more consistent",
        "with a gradual divergence pattern.",
        "",
        "If separation is **uniform**: L22 may not track the commitment mechanism directly,",
        "or the direction itself is capturing a different phenomenon.",
        "",
        "**Remember:** This is provisional analysis. The L22 direction was extracted from a small",
        "dataset and may not generalise. See Stage 4.8 extension for more matched cells.",
        "",
        "## 5. Per-Condition Temporal Profiles",
        "",
    ]
    for c in CONDITIONS:
        if c not in analysis.get("by_cond_outcome", {}):
            continue
        suc = analysis["by_cond_outcome"][c]["success"]
        fail = analysis["by_cond_outcome"][c]["failure"]
        lines.append(f"### Condition {c}")
        lines.append("| Bin | Success | Failure | Delta |")
        lines.append("|-----|---------|---------|-------|")
        for b in range(1, N_BINS + 1):
            sv = suc.get(f"bin_{b}", math.nan)
            fv = fail.get(f"bin_{b}", math.nan)
            if math.isnan(sv) or math.isnan(fv):
                lines.append(f"| {b} | — | — | — |")
            else:
                lines.append(f"| {b} | {sv:.3f} | {fv:.3f} | {sv-fv:+.3f} |")
        lines.append("")

    lines += [
        "---",
        "",
        "*Figure: `fig_l22_temporal.png` — L22 projection over 10 thinking-block bins, by condition and outcome.*",
        "",
        "*This is provisional diagnostic analysis only.*",
    ]

    out_path = out_dir / "L22_TEMPORAL_ANALYSIS.md"
    out_path.write_text("\n".join(lines) + "\n")
    return out_path


def main():
    _OUT_DIR.mkdir(parents=True, exist_ok=True)

    print("Loading data...")
    rows = load_data()
    print(f"Loaded {len(rows)} rows")

    print("Running temporal analysis...")
    analysis = analyze_temporal(rows)

    # Save raw analysis JSON
    (_OUT_DIR / "l22_temporal_analysis.json").write_text(json.dumps(analysis, indent=2, default=str))

    print("Generating figure...")
    generate_temporal_figure(analysis, _OUT_DIR / "fig_l22_temporal.png")

    print("Writing report...")
    report_path = write_report(analysis, _OUT_DIR)
    print(f"Report: {report_path}")

    # Print key finding
    ev = analysis.get("early_vs_late", {})
    print(f"\nKey finding: {ev.get('interpretation', '?')}")
    print(f"  Early (bins 1-3): {ev.get('early_mean_sep', '?'):.4f}")
    print(f"  Late  (bins 8-10): {ev.get('late_mean_sep', '?'):.4f}")
    print(f"  Max separation at bin {analysis.get('max_separation_bin', '?')}: |delta|={analysis.get('max_separation_delta', '?'):.4f}")


if __name__ == "__main__":
    main()
