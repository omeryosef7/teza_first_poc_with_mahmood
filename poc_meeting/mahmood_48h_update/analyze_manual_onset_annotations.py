"""
Analyze completed manual onset annotations.

Reads the annotated manual_onset_review_subset_30_40.csv and computes:
  - n_reviewed, agreement_rate
  - breakdown of too_early / too_late / correct / no_engagement / unclear
  - whether "mostly early onset" conclusion is supported
  - fig_manual_vs_heuristic_onset.png (if >= 10 annotated rows)

Output directory: outputs/meeting/mahmood_48h_update_20260611_143740/
Output files:
  - manual_onset_validation_summary.csv
  - manual_onset_validation_report.md
  - fig_manual_vs_heuristic_onset.png (if enough data)
"""

import csv
import os
import sys
from collections import Counter, defaultdict

MEETING_DIR = "outputs/meeting/mahmood_48h_update_20260611_143740"
SUBSET_PATH = os.path.join(MEETING_DIR, "manual_onset_review_subset_30_40.csv")
SUMMARY_CSV = os.path.join(MEETING_DIR, "manual_onset_validation_summary.csv")
REPORT_MD = os.path.join(MEETING_DIR, "manual_onset_validation_report.md")
FIG_PATH = os.path.join(MEETING_DIR, "fig_manual_vs_heuristic_onset.png")

VALID_LABELS = {
    "before_first_engagement",
    "first_engagement",
    "after_engagement",
    "no_engagement",
    "unclear",
}

AGREEMENT_LABELS = {"first_engagement"}
TOO_EARLY_LABELS = {"after_engagement"}  # heuristic fired too early vs manual
TOO_LATE_LABELS = {"before_first_engagement"}  # heuristic fired too late vs manual


def load_csv(path):
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(dict(row))
    return rows


def main():
    if not os.path.exists(SUBSET_PATH):
        print(f"ERROR: Subset file not found: {SUBSET_PATH}")
        sys.exit(1)

    rows = load_csv(SUBSET_PATH)
    n_total = len(rows)

    # Identify annotated rows (manual_label is non-empty)
    annotated = [r for r in rows if r.get("manual_label", "").strip()]
    n_reviewed = len(annotated)

    if n_reviewed == 0:
        print("No annotations found yet. Fill in manual_label column and re-run.")
        _write_empty_report(n_total, REPORT_MD, SUMMARY_CSV)
        return

    # Validate labels
    invalid = [r for r in annotated if r.get("manual_label", "").strip() not in VALID_LABELS]
    if invalid:
        print(f"WARNING: {len(invalid)} rows have unrecognised labels:")
        for r in invalid:
            print(f"  row_id={r.get('row_id')} label={r.get('manual_label')!r}")

    valid_annotated = [r for r in annotated if r.get("manual_label", "").strip() in VALID_LABELS]

    # Label distribution
    label_counts = Counter(r["manual_label"].strip() for r in valid_annotated)

    n_agree = sum(label_counts.get(l, 0) for l in AGREEMENT_LABELS)
    n_too_early = sum(label_counts.get(l, 0) for l in TOO_EARLY_LABELS)
    n_too_late = sum(label_counts.get(l, 0) for l in TOO_LATE_LABELS)
    n_no_engagement = label_counts.get("no_engagement", 0)
    n_unclear = label_counts.get("unclear", 0)

    n_valid = len(valid_annotated)
    agreement_rate = n_agree / n_valid if n_valid > 0 else 0.0

    # Breakdown by condition
    by_condition = defaultdict(lambda: Counter())
    for r in valid_annotated:
        cond = r.get("condition", "?")
        label = r.get("manual_label", "").strip()
        by_condition[cond][label] += 1

    # Breakdown by sr_success
    by_success = defaultdict(lambda: Counter())
    for r in valid_annotated:
        sr = r.get("sr_success", "").strip()
        label = r.get("manual_label", "").strip()
        by_success[sr][label] += 1

    # Verdict on "mostly early onset" conclusion
    # The heuristic labels most rows as "early" (onset near token 0).
    # If many manual labels are "after_engagement", the heuristic is too aggressive (fires too early).
    # If many are "first_engagement", heuristic is well-calibrated.
    # If many are "no_engagement", the "early onset" claim is undermined.

    heuristic_early_rows = [r for r in valid_annotated if r.get("onset_bucket", "") == "early"]
    n_heuristic_early = len(heuristic_early_rows)
    early_label_counts = Counter(r["manual_label"].strip() for r in heuristic_early_rows)
    n_early_confirmed = early_label_counts.get("first_engagement", 0)
    n_early_too_aggressive = early_label_counts.get("after_engagement", 0)
    n_early_no_engage = early_label_counts.get("no_engagement", 0)

    if n_heuristic_early == 0:
        verdict = "not_yet_validated"
        verdict_rationale = "No heuristic-early rows were annotated."
    else:
        confirm_rate = n_early_confirmed / n_heuristic_early
        aggressive_rate = n_early_too_aggressive / n_heuristic_early
        no_engage_rate = n_early_no_engage / n_heuristic_early

        if confirm_rate >= 0.7:
            verdict = "supported"
            verdict_rationale = (
                f"{n_early_confirmed}/{n_heuristic_early} heuristic-early rows confirmed "
                f"as first_engagement ({confirm_rate:.0%}). Early onset conclusion is well-supported."
            )
        elif confirm_rate >= 0.5:
            verdict = "partially_supported"
            verdict_rationale = (
                f"{n_early_confirmed}/{n_heuristic_early} heuristic-early rows confirmed "
                f"({confirm_rate:.0%}); {n_early_too_aggressive} too aggressive, "
                f"{n_early_no_engage} show no engagement. Conclusion holds but with caveats."
            )
        elif aggressive_rate >= 0.4 or no_engage_rate >= 0.3:
            verdict = "weakened"
            verdict_rationale = (
                f"Only {n_early_confirmed}/{n_heuristic_early} confirmed ({confirm_rate:.0%}). "
                f"{n_early_too_aggressive} rows show heuristic fired too early; "
                f"{n_early_no_engage} show no actual target engagement. "
                "The 'mostly early onset' conclusion should be stated with stronger caveats."
            )
        else:
            verdict = "unclear"
            verdict_rationale = (
                f"Mixed results ({confirm_rate:.0%} confirmed). Cannot draw a clean conclusion. "
                "More annotations needed."
            )

    # Write summary CSV
    summary_rows = []
    summary_rows.append({
        "metric": "n_total_in_subset", "value": n_total, "notes": ""
    })
    summary_rows.append({
        "metric": "n_reviewed", "value": n_reviewed, "notes": ""
    })
    summary_rows.append({
        "metric": "n_valid_labels", "value": n_valid, "notes": ""
    })
    summary_rows.append({
        "metric": "agreement_rate", "value": f"{agreement_rate:.3f}",
        "notes": "fraction labeled first_engagement"
    })
    summary_rows.append({
        "metric": "n_too_early_heuristic", "value": n_too_early,
        "notes": "after_engagement: heuristic onset before actual engagement"
    })
    summary_rows.append({
        "metric": "n_too_late_heuristic", "value": n_too_late,
        "notes": "before_first_engagement: heuristic onset after actual engagement"
    })
    summary_rows.append({
        "metric": "n_no_engagement", "value": n_no_engagement, "notes": ""
    })
    summary_rows.append({
        "metric": "n_unclear", "value": n_unclear, "notes": ""
    })
    summary_rows.append({
        "metric": "early_onset_verdict", "value": verdict,
        "notes": verdict_rationale
    })

    with open(SUMMARY_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["metric", "value", "notes"])
        writer.writeheader()
        writer.writerows(summary_rows)

    # Write report MD
    _write_report(
        n_total, n_reviewed, n_valid, agreement_rate,
        label_counts, by_condition, by_success,
        verdict, verdict_rationale,
        n_heuristic_early, n_early_confirmed, n_early_too_aggressive, n_early_no_engage,
        REPORT_MD
    )

    # Plot if enough data
    if n_reviewed >= 10:
        _make_figure(valid_annotated, FIG_PATH)

    print(f"Written: {SUMMARY_CSV}")
    print(f"Written: {REPORT_MD}")
    print(f"\nVERDICT: {verdict}")
    print(f"  {verdict_rationale}")


def _write_empty_report(n_total, report_path, summary_path):
    msg = f"""# Manual Onset Validation Report

**Status:** No annotations yet.

The subset file (`manual_onset_review_subset_30_40.csv`) has {n_total} rows ready for annotation.
Please fill in the `manual_label` column (and optionally `manual_onset_token_idx` and
`reviewer_notes`) for each row, then re-run this script.

See `MANUAL_ONSET_ANNOTATION_INSTRUCTIONS_SHORT.md` for label definitions.
"""
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(msg)
    with open(summary_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["metric", "value", "notes"])
        writer.writeheader()
        writer.writerow({"metric": "n_total_in_subset", "value": n_total, "notes": ""})
        writer.writerow({"metric": "n_reviewed", "value": 0, "notes": "not yet annotated"})


def _write_report(
    n_total, n_reviewed, n_valid, agreement_rate,
    label_counts, by_condition, by_success,
    verdict, verdict_rationale,
    n_heuristic_early, n_early_confirmed, n_early_too_aggressive, n_early_no_engage,
    path
):
    lines = [
        "# Manual Onset Validation Report",
        "",
        f"**Rows in subset:** {n_total}",
        f"**Rows annotated:** {n_reviewed}",
        f"**Valid labels:** {n_valid}",
        f"**Agreement rate** (heuristic correct, labeled `first_engagement`): "
        f"{agreement_rate:.1%}",
        "",
        "## Label Distribution",
        "",
        "| Label | Count | Percent |",
        "|-------|-------|---------|",
    ]
    for label in ["first_engagement", "before_first_engagement", "after_engagement",
                  "no_engagement", "unclear"]:
        cnt = label_counts.get(label, 0)
        pct = cnt / n_valid * 100 if n_valid > 0 else 0.0
        lines.append(f"| {label} | {cnt} | {pct:.1f}% |")

    lines += [
        "",
        "## Heuristic Calibration Summary",
        "",
        f"- Heuristic labeled **early**: {n_heuristic_early} rows reviewed",
        f"- Confirmed correct (`first_engagement`): {n_early_confirmed}",
        f"- Too aggressive (fired too early, `after_engagement`): {n_early_too_aggressive}",
        f"- No engagement found (`no_engagement`): {n_early_no_engage}",
        "",
        "## By Condition",
        "",
        "| Condition | first_engagement | after_engagement | before_first | no_engagement | unclear |",
        "|-----------|-----------------|-----------------|--------------|---------------|---------|",
    ]
    for cond in sorted(by_condition.keys()):
        c = by_condition[cond]
        lines.append(
            f"| {cond} | {c.get('first_engagement',0)} | {c.get('after_engagement',0)} "
            f"| {c.get('before_first_engagement',0)} | {c.get('no_engagement',0)} "
            f"| {c.get('unclear',0)} |"
        )

    lines += [
        "",
        "## By sr_success",
        "",
        "| sr_success | first_engagement | after_engagement | before_first | no_engagement | unclear |",
        "|------------|-----------------|-----------------|--------------|---------------|---------|",
    ]
    for sr in sorted(by_success.keys()):
        c = by_success[sr]
        lines.append(
            f"| {sr} | {c.get('first_engagement',0)} | {c.get('after_engagement',0)} "
            f"| {c.get('before_first_engagement',0)} | {c.get('no_engagement',0)} "
            f"| {c.get('unclear',0)} |"
        )

    lines += [
        "",
        "## Verdict on 'Mostly Early Onset' Conclusion",
        "",
        f"**Verdict:** `{verdict}`",
        "",
        f"{verdict_rationale}",
        "",
        "## Interpretation",
        "",
    ]

    if verdict == "supported":
        lines += [
            "The heuristic onset detection is well-calibrated for early-onset cases.",
            "The 'mostly early onset' conclusion appears robust and can be stated with confidence.",
            "Recommend: report onset finding with the note that manual review confirmed heuristic.",
        ]
    elif verdict == "partially_supported":
        lines += [
            "The heuristic is partially correct but shows some over-triggering.",
            "The 'mostly early onset' conclusion holds but should be stated cautiously:",
            "'Most onset detections occur very early in the thinking block, though some early",
            "heuristic triggers may fire before actual target engagement.'",
        ]
    elif verdict == "weakened":
        lines += [
            "The heuristic appears too aggressive — it fires early even when the model is not",
            "yet engaging with the target task. The 'mostly early onset' conclusion is weakened.",
            "Recommend: acknowledge that the heuristic may over-estimate early engagement;",
            "manual validation revealed a non-trivial fraction of false early triggers.",
        ]
    else:
        lines += [
            "Results are mixed or insufficient for a clean verdict.",
            "More annotations (full dataset or higher-confidence subset) are needed.",
        ]

    lines += [
        "",
        "---",
        "",
        "*This report was generated by `poc_meeting/mahmood_48h_update/analyze_manual_onset_annotations.py`*",
    ]

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def _make_figure(rows, fig_path):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import numpy as np

        labels_order = [
            "first_engagement", "before_first_engagement", "after_engagement",
            "no_engagement", "unclear",
        ]
        label_counts = Counter(r["manual_label"].strip() for r in rows)
        counts = [label_counts.get(l, 0) for l in labels_order]
        short_labels = ["correct", "too_late", "too_early", "no_engage", "unclear"]
        colors = ["#4caf50", "#ff9800", "#f44336", "#9e9e9e", "#90caf9"]

        fig, ax = plt.subplots(figsize=(8, 4))
        bars = ax.bar(short_labels, counts, color=colors, edgecolor="white", linewidth=0.5)
        ax.set_ylabel("Count")
        ax.set_title("Manual vs. Heuristic Onset Annotation\n(first_engagement = heuristic correct)")
        for bar, cnt in zip(bars, counts):
            if cnt > 0:
                ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.1,
                        str(cnt), ha="center", va="bottom", fontsize=10)
        ax.set_ylim(0, max(counts) + 2)
        plt.tight_layout()
        plt.savefig(fig_path, dpi=150, bbox_inches="tight")
        plt.close()
        print(f"Written: {fig_path}")
    except ImportError as e:
        print(f"Could not generate figure (missing package): {e}")


if __name__ == "__main__":
    main()
