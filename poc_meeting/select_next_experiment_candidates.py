"""
Next experiment candidate selector for Mahmood meeting.
Uses existing Stage 4.7 and Stage 4.8 outputs — no GPU jobs.
Identifies prompts/conditions likely to produce intermediate success rates
and matched-outcome cells for a future mechanistic experiment.

Output:
  outputs/meeting/mahmood_20260611/tables/next_experiment_candidates.csv

Usage:
    python poc_meeting/select_next_experiment_candidates.py
"""

import csv
import json
import math
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S47_ANALYSIS = os.path.join(BASE, "outputs/stage4_7/runs/run_array_20260610_1442/analysis")
S48_ANALYSIS = os.path.join(BASE, "outputs/stage4_8/runs/run_array_20260611_0109/analysis")
OUT_DIR = os.path.join(BASE, "outputs/meeting/mahmood_20260611/tables")
os.makedirs(OUT_DIR, exist_ok=True)


def mean(lst):
    return sum(lst) / len(lst) if lst else float("nan")


# ── Criteria ────────────────────────────────────────────────────────────────────
# For a cell to be a good matched-outcome candidate:
#   - success rate between 0.3 and 0.7 (not near-deterministic)
#   - no censoring (complete generations)
#   - good segmentation
#   - moderate thinking length (not too short — avoids trivial compliance)
#   - shows variation across seeds or conditions (Stage 4.8 cells preferred)

TARGET_RATE_LOW = 0.3
TARGET_RATE_HIGH = 0.7
MIN_THINK_TOKENS = 500  # avoid very short thinking as candidate

candidates = []

# ── Stage 4.8 cells ─────────────────────────────────────────────────────────────
print("Evaluating Stage 4.8 cells...")
s48_cell_path = os.path.join(S48_ANALYSIS, "cell_summary.csv")
with open(s48_cell_path) as f:
    for row in csv.DictReader(f):
        n_complete = int(row["n_complete"])
        n_censored = int(row["n_censored"])
        n_valid_seg = int(row["n_valid_seg"])
        success_rate = float(row["success_rate"])
        mean_think = float(row["mean_think_tokens"])
        sr_var = float(row["sr_score_variance"])
        is_matched = row["is_matched_outcome_cell"].strip().lower() == "true"
        has_success = row["has_success"].strip().lower() == "true"
        has_failure = row["has_failure"].strip().lower() == "true"

        qualifies = (
            n_censored == 0
            and n_valid_seg == n_complete  # good segmentation
            and TARGET_RATE_LOW <= success_rate <= TARGET_RATE_HIGH
            and mean_think >= MIN_THINK_TOKENS
        )

        reason_parts = []
        if n_censored > 0:
            reason_parts.append(f"censored={n_censored}")
        if success_rate < TARGET_RATE_LOW:
            reason_parts.append(f"rate_too_low={success_rate:.2f}")
        if success_rate > TARGET_RATE_HIGH:
            reason_parts.append(f"rate_too_high={success_rate:.2f}")
        if mean_think < MIN_THINK_TOKENS:
            reason_parts.append(f"think_too_short={mean_think:.0f}")
        if n_valid_seg < n_complete:
            reason_parts.append(f"seg_incomplete={n_valid_seg}/{n_complete}")

        candidates.append({
            "source": "stage4_8",
            "source_example_id": row["source_example_id"],
            "condition": row["condition"],
            "goal_index": row["goal_index"],
            "n_seeds_or_prompts": n_complete,
            "n_censored": n_censored,
            "n_success": int(row["n_success"]),
            "success_rate": round(success_rate, 3),
            "sr_score_variance": round(sr_var, 4),
            "mean_think_tokens": round(mean_think, 0),
            "good_segmentation": n_valid_seg == n_complete,
            "is_currently_matched_cell": is_matched,
            "qualifies": qualifies,
            "disqualification_reason": "; ".join(reason_parts) if reason_parts else "",
            "priority_for_expansion": qualifies and not is_matched,
        })

# ── Stage 4.7 source examples ───────────────────────────────────────────────────
print("Evaluating Stage 4.7 canonical results...")
s47_canon_path = os.path.join(S47_ANALYSIS, "canonical_per_run_results.csv")
# Aggregate by source_example_id × condition
s47_cells = {}
with open(s47_canon_path) as f:
    for row in csv.DictReader(f):
        key = (row["source_example_id"], row["condition"])
        if key not in s47_cells:
            s47_cells[key] = {
                "source_example_id": row["source_example_id"],
                "condition": row["condition"],
                "goal_index": row["goal_index"],
                "n": 0, "n_censored": 0, "n_cc": 0, "n_cc_success": 0,
                "think_tokens": [], "has_seg_issues": False
            }
        cell = s47_cells[key]
        cell["n"] += 1
        is_censored = row.get("is_censored", "False").strip().lower() == "true"
        if is_censored:
            cell["n_censored"] += 1
        else:
            cell["n_cc"] += 1
            sr_success = row.get("sr_success_complete_case", "False").strip().lower() == "true"
            if sr_success:
                cell["n_cc_success"] += 1
        think_str = row.get("think_token_count", "")
        if think_str and float(think_str) > 0:
            cell["think_tokens"].append(float(think_str))
        seg_status = row.get("thinking_segmentation_status", "")
        if seg_status and seg_status not in ("parsed_from_think_tags", "thinking_off_no_tags"):
            cell["has_seg_issues"] = True

for (sei, cond), cell in s47_cells.items():
    n_cc = cell["n_cc"]
    n_cc_success = cell["n_cc_success"]
    cc_rate = n_cc_success / n_cc if n_cc > 0 else float("nan")
    mean_think = mean(cell["think_tokens"])
    n_censored = cell["n_censored"]
    good_seg = not cell["has_seg_issues"]

    qualifies = (
        n_censored == 0
        and good_seg
        and not math.isnan(cc_rate)
        and TARGET_RATE_LOW <= cc_rate <= TARGET_RATE_HIGH
        and mean_think >= MIN_THINK_TOKENS
    )

    reason_parts = []
    if n_censored > 0:
        reason_parts.append(f"censored={n_censored}")
    if not math.isnan(cc_rate):
        if cc_rate < TARGET_RATE_LOW:
            reason_parts.append(f"rate_too_low={cc_rate:.2f}")
        if cc_rate > TARGET_RATE_HIGH:
            reason_parts.append(f"rate_too_high={cc_rate:.2f}")
    if math.isnan(mean_think) or mean_think < MIN_THINK_TOKENS:
        reason_parts.append(f"think_too_short={mean_think:.0f}")
    if not good_seg:
        reason_parts.append("seg_issue")

    # Stage 4.7 has only 1 generation per cell, so variance = N/A
    candidates.append({
        "source": "stage4_7",
        "source_example_id": sei,
        "condition": cond,
        "goal_index": cell["goal_index"],
        "n_seeds_or_prompts": n_cc,
        "n_censored": n_censored,
        "n_success": n_cc_success,
        "success_rate": round(cc_rate, 3) if not math.isnan(cc_rate) else float("nan"),
        "sr_score_variance": float("nan"),  # single generation
        "mean_think_tokens": round(mean_think, 0) if not math.isnan(mean_think) else float("nan"),
        "good_segmentation": good_seg,
        "is_currently_matched_cell": False,
        "qualifies": qualifies,
        "disqualification_reason": "; ".join(reason_parts) if reason_parts else "",
        "priority_for_expansion": qualifies,
    })

# ── Write output ───────────────────────────────────────────────────────────────
out_path = os.path.join(OUT_DIR, "next_experiment_candidates.csv")
if candidates:
    fieldnames = list(candidates[0].keys())
    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(sorted(candidates,
                                key=lambda r: (not r["qualifies"], r["goal_index"], r["source"])))

# ── Summary ────────────────────────────────────────────────────────────────────
qualified = [c for c in candidates if c["qualifies"]]
priority = [c for c in candidates if c.get("priority_for_expansion")]

print(f"\nTotal cells evaluated: {len(candidates)}")
print(f"  Qualifying (rate 0.3–0.7, no censoring, good seg, think≥{MIN_THINK_TOKENS}): {len(qualified)}")
print(f"  Priority for expansion (qualify + not yet matched): {len(priority)}")
print(f"\nQualifying cells:")
for c in qualified:
    matched_note = " [ALREADY MATCHED]" if c["is_currently_matched_cell"] else ""
    print(f"  [{c['source']:<8s}] goal={c['goal_index']} cond={c['condition']} "
          f"rate={c['success_rate']:.0%} think={c['mean_think_tokens']:.0f}{matched_note}")

print(f"\n{out_path}")
print("\nDone.")
