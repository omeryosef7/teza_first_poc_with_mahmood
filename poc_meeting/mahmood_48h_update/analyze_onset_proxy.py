#!/usr/bin/env python3
"""
Task 2, Step 2 — Analyze onset proxy dataset.

Computes summary statistics from the onset proxy dataset:
onset by condition, by success, by bucket, and optional
Layer-22 projection alignment to onset position.

Usage:
    python -m poc_meeting.mahmood_48h_update.analyze_onset_proxy \
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
from scipy import stats

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s", stream=sys.stderr)
log = logging.getLogger(__name__)

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def _read_csv(path: Path) -> list[dict]:
    if not path.exists():
        log.error("File not found: %s", path)
        return []
    with open(path, newline="") as f:
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


def _valid_onset_rows(rows: list[dict]) -> list[dict]:
    """Return rows with high or medium confidence and a valid onset_percent."""
    valid = []
    for r in rows:
        if r.get("confidence") not in ("high", "medium"):
            continue
        op = _float(r.get("onset_percent"))
        if math.isnan(op):
            continue
        valid.append(r)
    return valid


def _summarize_group(rows: list[dict]) -> dict:
    pcts = [_float(r["onset_percent"]) for r in rows if not math.isnan(_float(r.get("onset_percent")))]
    token_before = [_float(r.get("tokens_before_onset")) for r in rows
                    if not math.isnan(_float(r.get("tokens_before_onset")))]
    think_toks = [_float(r.get("think_token_count")) for r in rows
                  if not math.isnan(_float(r.get("think_token_count")))]
    buckets = [r.get("onset_bucket", "") for r in rows]
    return {
        "n": len(rows),
        "mean_onset_pct": round(float(np.mean(pcts)), 4) if pcts else float("nan"),
        "median_onset_pct": round(float(np.median(pcts)), 4) if pcts else float("nan"),
        "std_onset_pct": round(float(np.std(pcts)), 4) if pcts else float("nan"),
        "mean_tokens_before_onset": round(float(np.mean(token_before)), 1) if token_before else float("nan"),
        "median_tokens_before_onset": round(float(np.median(token_before)), 1) if token_before else float("nan"),
        "mean_think_tokens": round(float(np.mean(think_toks)), 1) if think_toks else float("nan"),
        "n_early": buckets.count("early"),
        "n_middle": buckets.count("middle"),
        "n_late": buckets.count("late"),
        "n_none": buckets.count("none"),
    }


def compute_onset_by_condition(valid_rows: list[dict]) -> list[dict]:
    groups: dict[str, list[dict]] = defaultdict(list)
    for r in valid_rows:
        groups[r["condition"]].append(r)
    out = []
    for cond in sorted(groups):
        s = _summarize_group(groups[cond])
        s["condition"] = cond
        out.append(s)
    return out


def compute_onset_by_success(valid_rows: list[dict]) -> list[dict]:
    groups: dict[bool | None, list[dict]] = defaultdict(list)
    for r in valid_rows:
        sr = _bool(r.get("sr_success"))
        groups[sr].append(r)
    out = []
    for sr_val in [True, False]:
        rows_g = groups[sr_val]
        s = _summarize_group(rows_g)
        s["sr_success"] = sr_val
        out.append(s)
    return out


def compute_onset_bucket_asr(all_rows: list[dict]) -> list[dict]:
    """ASR% by onset_bucket (includes all confidence levels)."""
    groups: dict[str, list] = defaultdict(list)
    for r in all_rows:
        b = r.get("onset_bucket", "unavailable")
        sr = _bool(r.get("sr_success"))
        groups[b].append(sr)
    out = []
    for bucket in ("early", "middle", "late", "none", "unavailable"):
        vals = groups[bucket]
        n = len(vals)
        n_valid = sum(1 for v in vals if v is not None)
        n_success = sum(1 for v in vals if v is True)
        asr_pct = 100 * n_success / n_valid if n_valid > 0 else float("nan")
        out.append({"onset_bucket": bucket, "n": n, "n_valid": n_valid,
                    "n_success": n_success, "asr_pct": round(asr_pct, 1)})
    return out


def compute_correlations(valid_rows: list[dict]) -> dict:
    onset_pcts = np.array([_float(r["onset_percent"]) for r in valid_rows])
    sr_scores = np.array([_float(r.get("strongreject_score")) for r in valid_rows])
    think_toks = np.array([_float(r.get("think_token_count")) for r in valid_rows])
    sr_success = np.array([1.0 if _bool(r.get("sr_success")) else 0.0 for r in valid_rows])

    def spear(x, y):
        mask = ~(np.isnan(x) | np.isnan(y))
        if mask.sum() < 5:
            return float("nan"), float("nan")
        r, p = stats.spearmanr(x[mask], y[mask])
        return round(float(r), 4), round(float(p), 4)

    r1, p1 = spear(onset_pcts, sr_scores)
    r2, p2 = spear(onset_pcts, think_toks)
    r3, p3 = spear(onset_pcts, sr_success)

    # Mann-Whitney U: success vs failure onset_percent
    succ = onset_pcts[sr_success == 1]
    fail = onset_pcts[sr_success == 0]
    succ = succ[~np.isnan(succ)]
    fail = fail[~np.isnan(fail)]
    if len(succ) >= 3 and len(fail) >= 3:
        mw = stats.mannwhitneyu(succ, fail, alternative="two-sided")
        mw_u = round(float(mw.statistic), 2)
        mw_p = round(float(mw.pvalue), 4)
    else:
        mw_u, mw_p = float("nan"), float("nan")

    # Kruskal-Wallis across conditions
    cond_groups = defaultdict(list)
    for r in valid_rows:
        op = _float(r.get("onset_percent"))
        if not math.isnan(op):
            cond_groups[r["condition"]].append(op)
    if len(cond_groups) >= 2:
        groups_vals = list(cond_groups.values())
        if all(len(g) >= 2 for g in groups_vals):
            kw = stats.kruskal(*groups_vals)
            kw_h = round(float(kw.statistic), 3)
            kw_p = round(float(kw.pvalue), 4)
        else:
            kw_h, kw_p = float("nan"), float("nan")
    else:
        kw_h, kw_p = float("nan"), float("nan")

    return {
        "n_valid": len(valid_rows),
        "spearman_onset_vs_sr_score": {"r": r1, "p": p1},
        "spearman_onset_vs_think_tokens": {"r": r2, "p": p2},
        "spearman_onset_vs_sr_success": {"r": r3, "p": p3},
        "mannwhitney_onset_success_vs_failure": {"U": mw_u, "p": mw_p,
                                                  "n_success": int(len(succ)),
                                                  "n_failure": int(len(fail))},
        "kruskal_wallis_onset_across_conditions": {"H": kw_h, "p": kw_p},
    }


def try_projection_alignment(repr_dir: Path, onset_rows: list[dict]) -> list[dict] | None:
    """
    Align Layer-22 normalized bin projections to onset position.
    Returns list of {offset_bin, mean_projection, n_success, n_failure, n} or None if unavailable.
    """
    if not repr_dir.exists():
        log.info("Representations dir not found, skipping projection alignment.")
        return None

    # Load a sample repr file to find available fields
    repr_files = list(repr_dir.glob("*.json"))
    if not repr_files:
        return None

    # Build map: run_id → repr data
    repr_map = {}
    layer_key = "l22_norm_bin"  # will discover actual key
    for rf in repr_files:
        try:
            with open(rf) as fh:
                rd = json.load(fh)
        except Exception:
            continue
        run_id = rd.get("run_id", rf.stem)
        # Extract normalized bins for layer 22
        bins = {}
        for k, v in rd.items():
            if "layer_22" in k and "normalized_bin" in k:
                try:
                    bn = int(k.split("normalized_bin_")[1].split("_")[0])
                    if isinstance(v, (int, float)):
                        bins[bn] = float(v)
                except Exception:
                    pass
        if bins:
            repr_map[run_id] = bins

    if not repr_map:
        log.info("No Layer-22 normalized bin data found in representations.")
        return None

    log.info("Loaded Layer-22 bins from %d representation files.", len(repr_map))

    # Match onset rows to repr data
    # onset_percent → onset_bin (1-10)
    aligned: list[dict] = []
    for r in onset_rows:
        op = _float(r.get("onset_percent"))
        if math.isnan(op):
            continue
        eid = r.get("example_id", "")
        # Try to find repr by run_id prefix match
        rd_bins = repr_map.get(eid)
        if rd_bins is None:
            # Try partial match
            for k in repr_map:
                if eid in k or k in eid:
                    rd_bins = repr_map[k]
                    break
        if rd_bins is None:
            continue
        onset_bin = max(1, min(10, int(op * 10) + 1))
        sr_succ = _bool(r.get("sr_success"))
        for bn, proj in rd_bins.items():
            offset = bn - onset_bin
            aligned.append({
                "run_id": eid,
                "condition": r["condition"],
                "sr_success": sr_succ,
                "onset_bin": onset_bin,
                "absolute_bin": bn,
                "offset_bin": offset,
                "projection": proj,
            })

    if not aligned:
        return None

    # Aggregate by offset_bin
    by_offset: dict[int, dict] = defaultdict(lambda: defaultdict(list))
    for a in aligned:
        by_offset[a["offset_bin"]]["proj"].append(a["projection"])
        by_offset[a["offset_bin"]]["sr_success"].append(a["sr_success"])
        by_offset[a["offset_bin"]]["condition"].append(a["condition"])

    result = []
    for offset in sorted(by_offset):
        g = by_offset[offset]
        projs = g["proj"]
        sr_vals = [1 if v else 0 for v in g["sr_success"] if v is not None]
        n_total = len(projs)
        if n_total < 3:
            continue
        result.append({
            "offset_bin": offset,
            "n": n_total,
            "n_success": sum(sr_vals),
            "n_failure": n_total - sum(sr_vals),
            "mean_projection": round(float(np.mean(projs)), 4),
            "std_projection": round(float(np.std(projs)), 4),
        })
    return result


def write_onset_analysis_md(
    by_cond: list[dict],
    by_success: list[dict],
    by_bucket: list[dict],
    correlations: dict,
    all_rows: list[dict],
    valid_rows: list[dict],
    out: Path,
) -> None:
    lines = [
        "# Onset Analysis Results",
        f"\n_Generated: {datetime.utcnow().isoformat()}Z_",
        "",
        f"**Total examples:** {len(all_rows)}  "
        f"**High+medium confidence:** {len(valid_rows)} ({100*len(valid_rows)/max(1,len(all_rows)):.0f}%)",
        "",
        "> **Caveat:** The onset proxy is a heuristic based on keyword overlap.",
        "> It approximates the first position where target-specific terms appear",
        "> in the thinking trace. Results should be treated as directional signals,",
        "> not ground truth. Manual validation is recommended before strong claims.",
        "> See `manual_onset_review_packet.csv`.",
        "",
        "## 1. Is onset usually early, middle, late, or unavailable?",
        "",
        "| onset_bucket | n | ASR% |",
        "|-------------|---|-----|",
    ]
    for r in by_bucket:
        lines.append(f"| {r['onset_bucket']} | {r['n']} | {r['asr_pct']:.1f}% |")

    lines += ["", "## 2. Does condition A delay onset relative to D/F?", "",
              "| Condition | n | Mean onset% | Median onset% | Mean tokens before | n_early | n_late |",
              "|-----------|---|------------|--------------|------------------|---------|--------|"]
    for r in sorted(by_cond, key=lambda x: x.get("condition", "")):
        lines.append(
            f"| {r['condition']} | {r['n']} "
            f"| {r['mean_onset_pct']:.1%} | {r['median_onset_pct']:.1%} "
            f"| {r['mean_tokens_before_onset']:.0f} | {r['n_early']} | {r['n_late']} |"
        )

    lines += ["", "## 3. Do successful runs have earlier or later onset?", "",
              "| sr_success | n | Mean onset% | Median onset% | Mean tokens before |",
              "|-----------|---|------------|--------------|------------------|"]
    for r in by_success:
        lines.append(
            f"| {r['sr_success']} | {r['n']} "
            f"| {r['mean_onset_pct']:.1%} | {r['median_onset_pct']:.1%} "
            f"| {r['mean_tokens_before_onset']:.0f} |"
        )

    c = correlations
    lines += [
        "",
        "## 4. Statistical tests (high+medium confidence only)",
        "",
        f"- Spearman ρ(onset% vs SR score): r = {c['spearman_onset_vs_sr_score']['r']}, p = {c['spearman_onset_vs_sr_score']['p']}",
        f"- Spearman ρ(onset% vs think tokens): r = {c['spearman_onset_vs_think_tokens']['r']}, p = {c['spearman_onset_vs_think_tokens']['p']}",
        f"- Mann-Whitney U (success vs failure onset%): U = {c['mannwhitney_onset_success_vs_failure']['U']}, p = {c['mannwhitney_onset_success_vs_failure']['p']}",
        f"- Kruskal-Wallis (onset% across conditions): H = {c['kruskal_wallis_onset_across_conditions']['H']}, p = {c['kruskal_wallis_onset_across_conditions']['p']}",
        "",
        "## 5. Uncertainties (because proxy is heuristic)",
        "",
        "- Keyword extraction from condition D prompt may include non-target structural words",
        "  that also appear in puzzle wrapper. This biases onset toward earlier positions.",
        "- Word-level tokenization does not match model tokenization. Onset position in tokens",
        "  is approximate.",
        "- For condition A, puzzle text occurs before the target span. If puzzle words happen to",
        "  match target keywords (unlikely but possible), onset will be falsely early.",
        "- Confidence tier 'medium' (1 match) may reflect coincidental overlap.",
        "- The onset proxy is computed on think_text word tokens, not the model's actual token",
        "  sequence. Onset_token_idx should be interpreted as a rough proportional measure.",
        "",
        "## 6. Manual annotations needed",
        "",
        "See `manual_onset_review_packet.csv` for examples prepared for human review.",
        "Before making strong claims about onset timing, at minimum 20 examples (stratified",
        "by condition and outcome) should be manually annotated.",
        "",
        "Recommended annotation process: reviewer reads the redacted_snippet in context of",
        "the full (non-redacted) thinking trace (researcher access only), and assigns:",
        "`before_target / first_target_engagement / after_target / no_engagement / unclear`",
    ]
    out.write_text("\n".join(lines))
    log.info("Wrote %s", out)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--s48-repr-dir", type=Path,
                        default=_REPO_ROOT / "outputs/stage4_8/runs/run_array_20260611_0109/representations")
    args = parser.parse_args(argv)

    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)

    dataset_path = out / "onset_proxy_dataset.csv"
    if not dataset_path.exists():
        log.error("onset_proxy_dataset.csv not found in %s — run build_onset_proxy_dataset.py first", out)
        return 1

    all_rows = _read_csv(dataset_path)
    log.info("Loaded %d rows from onset_proxy_dataset.csv", len(all_rows))

    valid_rows = _valid_onset_rows(all_rows)
    log.info("%d high/medium confidence rows with valid onset_percent", len(valid_rows))

    if not valid_rows:
        log.warning("No valid onset rows. Onset analysis will be minimal.")

    # Compute summary tables
    by_cond = compute_onset_by_condition(valid_rows)
    by_success = compute_onset_by_success(valid_rows)
    by_bucket = compute_onset_bucket_asr(all_rows)
    correlations = compute_correlations(valid_rows) if valid_rows else {}

    # Write onset_by_condition.csv
    fn_cond = ["condition", "n", "mean_onset_pct", "median_onset_pct", "std_onset_pct",
               "mean_tokens_before_onset", "median_tokens_before_onset",
               "mean_think_tokens", "n_early", "n_middle", "n_late", "n_none"]
    with open(out / "onset_by_condition.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fn_cond, extrasaction="ignore")
        w.writeheader()
        w.writerows(by_cond)
    log.info("Wrote onset_by_condition.csv")

    # Write onset_by_success.csv
    fn_succ = ["sr_success", "n", "mean_onset_pct", "median_onset_pct", "std_onset_pct",
               "mean_tokens_before_onset", "median_tokens_before_onset",
               "mean_think_tokens", "n_early", "n_middle", "n_late", "n_none"]
    with open(out / "onset_by_success.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fn_succ, extrasaction="ignore")
        w.writeheader()
        w.writerows(by_success)
    log.info("Wrote onset_by_success.csv")

    # Write onset_bucket_asr.csv
    with open(out / "onset_bucket_asr.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["onset_bucket", "n", "n_valid", "n_success", "asr_pct"])
        w.writeheader()
        w.writerows(by_bucket)
    log.info("Wrote onset_bucket_asr.csv")

    # Write correlations JSON
    if correlations:
        (out / "onset_correlations.json").write_text(json.dumps(correlations, indent=2))
        log.info("Wrote onset_correlations.json")

    # Try projection alignment
    proj_alignment = try_projection_alignment(args.s48_repr_dir, valid_rows)
    if proj_alignment:
        with open(out / "onset_aligned_projection.csv", "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["offset_bin", "n", "n_success", "n_failure",
                                               "mean_projection", "std_projection"])
            w.writeheader()
            w.writerows(proj_alignment)
        log.info("Wrote onset_aligned_projection.csv (%d offset bins)", len(proj_alignment))
    else:
        log.info("Projection alignment not available; skipping onset_aligned_projection.csv")

    # Write interpretation markdown
    write_onset_analysis_md(by_cond, by_success, by_bucket, correlations,
                            all_rows, valid_rows, out / "ONSET_ANALYSIS_RESULTS.md")

    return 0


if __name__ == "__main__":
    sys.exit(main())
