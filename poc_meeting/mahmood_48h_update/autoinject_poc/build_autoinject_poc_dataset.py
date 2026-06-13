"""
Build the AutoInject POC dataset from existing Stage 4.7 and Stage 4.8 results.

Each row represents one run cell with safe metadata only.
No raw prompt text or harmful content is included.

Primary source: outputs/stage4_7/runs/run_array_20260610_1442/analysis/canonical_per_run_results.csv
Secondary source: outputs/stage4_8/runs/run_array_20260611_0109/run_summary.jsonl
Onset data: outputs/meeting/mahmood_48h_update_20260611_143740/onset_proxy_dataset.csv

Output: outputs/meeting/mahmood_48h_update_20260611_143740/autoinject_poc/autoinject_poc_dataset.csv
"""

import csv
import hashlib
import json
import math
import os

STAGE47_CSV = (
    "outputs/stage4_7/runs/run_array_20260610_1442/analysis/canonical_per_run_results.csv"
)
STAGE48_JSONL = (
    "outputs/stage4_8/runs/run_array_20260611_0109/run_summary.jsonl"
)
ONSET_CSV = (
    "outputs/meeting/mahmood_48h_update_20260611_143740/onset_proxy_dataset.csv"
)
OUT_PATH = (
    "outputs/meeting/mahmood_48h_update_20260611_143740/autoinject_poc/autoinject_poc_dataset.csv"
)

CONDITION_META = {
    "A": {"has_puzzle": True,  "has_thinking": True,  "is_length_matched": False, "is_bare_target": False},
    "D": {"has_puzzle": False, "has_thinking": True,  "is_length_matched": False, "is_bare_target": True},
    "F": {"has_puzzle": True,  "has_thinking": False, "is_length_matched": True,  "is_bare_target": False},
    "E": {"has_puzzle": False, "has_thinking": False, "is_length_matched": False, "is_bare_target": True},
}

OUTPUT_COLS = [
    "candidate_id",
    "stage",
    "safe_example_hash",
    "goal_index",
    "condition",
    "wrapper_type",
    "has_puzzle",
    "has_thinking",
    "is_length_matched",
    "is_bare_target",
    "sr_score",
    "sr_success",
    "think_token_count",
    "censored",
    "onset_percent",
    "onset_bucket",
    "confidence",
    "seed",
]


def safe_bool(val):
    if isinstance(val, bool):
        return val
    if isinstance(val, str):
        return val.strip().lower() in ("true", "1", "yes")
    return bool(val)


def safe_float(val, default=0.0):
    try:
        return float(val)
    except (TypeError, ValueError):
        return default


def safe_int(val, default=0):
    try:
        return int(val)
    except (TypeError, ValueError):
        return default


def make_hash(source_id, goal_index, condition):
    raw = f"{source_id}|{goal_index}|{condition}"
    return hashlib.md5(raw.encode()).hexdigest()[:12]


def load_onset_index(onset_path):
    """Build index: example_id -> {onset_percent, onset_bucket, confidence}"""
    idx = {}
    if not os.path.exists(onset_path):
        return idx
    with open(onset_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            eid = row.get("example_id", "")
            if eid:
                idx[eid] = {
                    "onset_percent": safe_float(row.get("onset_percent", ""), 0.0),
                    "onset_bucket": row.get("onset_bucket", ""),
                    "confidence": row.get("confidence", ""),
                }
    return idx


def load_stage47(csv_path, onset_idx):
    rows = []
    if not os.path.exists(csv_path):
        print(f"WARNING: Stage 4.7 CSV not found: {csv_path}")
        return rows
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            eid = row.get("run_id", "") or row.get("source_example_id", "")
            condition = row.get("condition", "")
            goal_index = safe_int(row.get("goal_index", "0"), 0)
            source_id = row.get("source_example_id", eid)
            cond_meta = CONDITION_META.get(condition, {})
            safe_hash = make_hash(source_id, goal_index, condition)

            sr_score = safe_float(row.get("strongreject_score", ""), 0.0)
            sr_success = safe_bool(row.get("sr_success", "False"))
            think_tokens = safe_int(row.get("think_token_count", "0"), 0)
            censored = safe_bool(row.get("is_censored", "False"))

            onset_info = onset_idx.get(eid, {})

            cid = f"s47_{i:04d}_{condition}_{goal_index}"
            rows.append({
                "candidate_id": cid,
                "stage": "4.7",
                "safe_example_hash": safe_hash,
                "goal_index": goal_index,
                "condition": condition,
                "wrapper_type": condition,
                "has_puzzle": cond_meta.get("has_puzzle", False),
                "has_thinking": cond_meta.get("has_thinking", False),
                "is_length_matched": cond_meta.get("is_length_matched", False),
                "is_bare_target": cond_meta.get("is_bare_target", False),
                "sr_score": sr_score,
                "sr_success": sr_success,
                "think_token_count": think_tokens,
                "censored": censored,
                "onset_percent": onset_info.get("onset_percent", ""),
                "onset_bucket": onset_info.get("onset_bucket", ""),
                "confidence": onset_info.get("confidence", ""),
                "seed": 0,
            })
    return rows


def load_stage48(jsonl_path, onset_idx):
    rows = []
    if not os.path.exists(jsonl_path):
        print(f"WARNING: Stage 4.8 JSONL not found: {jsonl_path}")
        return rows
    with open(jsonl_path, encoding="utf-8") as f:
        for i, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                continue

            eid = d.get("run_id", "")
            condition = d.get("condition", "")
            goal_index = safe_int(d.get("goal_index", "0"), 0)
            seed = safe_int(d.get("seed", "0"), 0)
            source_id = d.get("source_example_id", eid)
            cond_meta = CONDITION_META.get(condition, {})
            safe_hash = make_hash(source_id, goal_index, condition)

            sr_score = safe_float(d.get("strongreject_score", ""), 0.0)
            sr_success = safe_bool(d.get("sr_success", False))
            think_tokens = safe_int(d.get("think_token_count", "0"), 0)
            censored = safe_bool(d.get("is_censored", False))

            onset_info = onset_idx.get(eid, {})

            cid = f"s48_{i:04d}_{condition}_{goal_index}_s{seed}"
            rows.append({
                "candidate_id": cid,
                "stage": "4.8",
                "safe_example_hash": safe_hash,
                "goal_index": goal_index,
                "condition": condition,
                "wrapper_type": condition,
                "has_puzzle": cond_meta.get("has_puzzle", False),
                "has_thinking": cond_meta.get("has_thinking", False),
                "is_length_matched": cond_meta.get("is_length_matched", False),
                "is_bare_target": cond_meta.get("is_bare_target", False),
                "sr_score": sr_score,
                "sr_success": sr_success,
                "think_token_count": think_tokens,
                "censored": censored,
                "onset_percent": onset_info.get("onset_percent", ""),
                "onset_bucket": onset_info.get("onset_bucket", ""),
                "confidence": onset_info.get("confidence", ""),
                "seed": seed,
            })
    return rows


def main():
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)

    onset_idx = load_onset_index(ONSET_CSV)
    print(f"Loaded onset index: {len(onset_idx)} entries")

    rows_47 = load_stage47(STAGE47_CSV, onset_idx)
    print(f"Stage 4.7 rows: {len(rows_47)}")

    rows_48 = load_stage48(STAGE48_JSONL, onset_idx)
    print(f"Stage 4.8 rows: {len(rows_48)}")

    all_rows = rows_47 + rows_48
    print(f"Total candidate rows: {len(all_rows)}")

    # Condition distribution
    from collections import Counter
    cond_dist = Counter(r["condition"] for r in all_rows)
    sr_dist = Counter(r["sr_success"] for r in all_rows)
    print(f"Condition distribution: {dict(cond_dist)}")
    print(f"sr_success distribution: {dict(sr_dist)}")

    with open(OUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_COLS)
        writer.writeheader()
        for row in all_rows:
            writer.writerow({col: row.get(col, "") for col in OUTPUT_COLS})

    print(f"Written: {OUT_PATH}")


if __name__ == "__main__":
    main()
