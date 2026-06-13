"""
Build a stratified 30-40 row manual onset annotation subset.

Sources:
  1. manual_onset_review_packet.csv (10 rows from existing package)
  2. onset_proxy_dataset.csv (supplement to reach 30-40 rows)

Stratification criteria:
  - condition: A, D, F
  - sr_success: True, False
  - goal_index: emphasize 0 and 2
  - onset_bucket: early, middle, late, none
  - confidence: high, medium, low

Output: manual_onset_review_subset_30_40.csv (safe fields only)
"""

import csv
import hashlib
import os
import random
from collections import defaultdict

MEETING_DIR = "outputs/meeting/mahmood_48h_update_20260611_143740"
PACKET_PATH = os.path.join(MEETING_DIR, "manual_onset_review_packet.csv")
ONSET_PATH = os.path.join(MEETING_DIR, "onset_proxy_dataset.csv")
OUT_PATH = os.path.join(MEETING_DIR, "manual_onset_review_subset_30_40.csv")

TARGET_COLS = [
    "row_id",
    "example_id",
    "goal_index",
    "condition",
    "stage",
    "sr_success",
    "think_token_count",
    "onset_percent",
    "onset_bucket",
    "confidence",
    "redacted_snippet",
    "redacted_context_hash",
    "heuristic_onset_token_idx",
    "manual_onset_token_idx",
    "manual_label",
    "reviewer_notes",
]

SAFE_FIELDS_FROM_PACKET = {
    "example_id", "goal_index", "condition", "stage", "sr_success",
    "think_token_count", "onset_percent", "onset_bucket", "confidence",
    "redacted_snippet", "redacted_context_hash", "onset_token_idx",
}

SAFE_FIELDS_FROM_ONSET = {
    "example_id", "goal_index", "condition", "stage", "sr_success",
    "strongreject_score", "think_token_count", "onset_percent",
    "onset_bucket", "confidence", "redacted_snippet", "redacted_context_hash",
    "onset_token_idx",
}


def safe_bool(val):
    if isinstance(val, bool):
        return val
    if isinstance(val, str):
        return val.strip().lower() in ("true", "1", "yes")
    return bool(val)


def load_csv(path):
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(dict(row))
    return rows


def normalise_row(row, source):
    """Return a normalised dict with safe fields only."""
    out = {}
    out["example_id"] = row.get("example_id", "")
    out["goal_index"] = row.get("goal_index", "")
    out["condition"] = row.get("condition", "")
    out["stage"] = row.get("stage", "")
    out["sr_success"] = row.get("sr_success", "")
    out["think_token_count"] = row.get("think_token_count", "")
    out["onset_percent"] = row.get("onset_percent", "0.0")
    out["onset_bucket"] = row.get("onset_bucket", "")
    out["confidence"] = row.get("confidence", "")
    out["redacted_snippet"] = row.get("redacted_snippet", "")
    out["redacted_context_hash"] = row.get("redacted_context_hash", "")
    onset_key = "onset_token_idx" if "onset_token_idx" in row else "heuristic_onset_token_idx"
    out["heuristic_onset_token_idx"] = row.get(onset_key, "")
    out["manual_onset_token_idx"] = ""
    out["manual_label"] = ""
    out["reviewer_notes"] = ""
    out["_source"] = source
    return out


def stratification_key(row):
    condition = row.get("condition", "?")
    sr = "T" if safe_bool(row.get("sr_success", False)) else "F"
    gi = str(row.get("goal_index", "?"))
    bucket = row.get("onset_bucket", "?")
    conf = row.get("confidence", "?")
    return (condition, sr, gi, bucket, conf)


def stratified_sample(rows, target):
    """Downsample rows to target using stratified sampling."""
    # Group by (condition, sr_success, goal_index)
    strata = defaultdict(list)
    for row in rows:
        cond = row.get("condition", "?")
        sr = "T" if safe_bool(row.get("sr_success", False)) else "F"
        gi = str(row.get("goal_index", "?"))
        strata[(cond, sr, gi)].append(row)

    # Round-robin across strata to get target rows
    selected = []
    keys = sorted(strata.keys())
    i = 0
    while len(selected) < target and any(strata[k] for k in keys):
        k = keys[i % len(keys)]
        if strata[k]:
            selected.append(strata[k].pop(0))
        i += 1

    return selected


def main():
    random.seed(42)

    # Combine all available rows from both sources
    packet_rows = load_csv(PACKET_PATH)
    onset_rows = load_csv(ONSET_PATH)

    included_ids = set()
    all_candidates = []

    for row in packet_rows:
        eid = row.get("example_id", "")
        if eid not in included_ids:
            all_candidates.append(normalise_row(row, "manual_packet"))
            included_ids.add(eid)

    for row in onset_rows:
        eid = row.get("example_id", "")
        if eid not in included_ids:
            all_candidates.append(normalise_row(row, "onset_proxy"))
            included_ids.add(eid)

    print(f"Total unique candidates across both sources: {len(all_candidates)}")

    # Stratified downsample to 35 rows (in 30-40 range)
    TARGET_TOTAL = 35
    all_rows = stratified_sample(all_candidates, TARGET_TOTAL)
    print(f"Total rows in subset after stratified sampling: {len(all_rows)} (target: {TARGET_TOTAL})")
    print(f"Total rows in subset: {len(all_rows)} (target: {TARGET_TOTAL})")

    # Assign row_id
    for i, row in enumerate(all_rows):
        row["row_id"] = str(i + 1)

    # Write output
    with open(OUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=TARGET_COLS)
        writer.writeheader()
        for row in all_rows:
            writer.writerow({col: row.get(col, "") for col in TARGET_COLS})

    print(f"Written: {OUT_PATH}")

    # Print stratification summary
    cond_counts = defaultdict(int)
    sr_counts = defaultdict(int)
    gi_counts = defaultdict(int)
    bucket_counts = defaultdict(int)
    conf_counts = defaultdict(int)

    for row in all_rows:
        cond_counts[row.get("condition", "?")] += 1
        sr_counts[str(safe_bool(row.get("sr_success", "False")))] += 1
        gi_counts[str(row.get("goal_index", "?"))] += 1
        bucket_counts[row.get("onset_bucket", "?")] += 1
        conf_counts[row.get("confidence", "?")] += 1

    print("\nStratification summary:")
    print(f"  Conditions: {dict(cond_counts)}")
    print(f"  sr_success: {dict(sr_counts)}")
    print(f"  goal_index: {dict(gi_counts)}")
    print(f"  onset_bucket: {dict(bucket_counts)}")
    print(f"  confidence: {dict(conf_counts)}")


if __name__ == "__main__":
    main()
