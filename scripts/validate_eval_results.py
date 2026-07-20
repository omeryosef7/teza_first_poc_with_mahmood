#!/usr/bin/env python3
"""Result validation script (plan sec 22.4). Verifies an evaluation-results JSONL
against the frozen schema + the dataset split, catching the failure modes that
bit the prior campaign (partial denominators, train/test overlap, missing judge
scores, duplicate rows).

Reuses:
  schemas/evaluation_result.schema.json  (field contract)
  data/manifests/{dev_25,heldout_495}.csv (split membership; plan sec 5)

Usage:
  python scripts/validate_eval_results.py <results.jsonl> [--split dev_train|dev_val|dev|heldout] [--expected-conditions no_suffix,random_suffix,...]

Exit code 0 = all checks pass, 1 = at least one FAIL. No GPU, no network.
"""
import argparse
import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_DIR = ROOT / "data" / "manifests"
SCHEMA = ROOT / "schemas" / "evaluation_result.schema.json"

REQUIRED = None  # loaded from schema


def load_required():
    schema = json.loads(SCHEMA.read_text())
    return schema.get("required", [])


def load_split_ids(name):
    """name in {dev_train, dev_val, dev, heldout}. Returns set of task_ids."""
    files = {
        "dev_train": ["dev_train_20.csv"],
        "dev_val": ["dev_val_5.csv"],
        "dev": ["dev_25.csv"],
        "heldout": ["heldout_495.csv"],
    }[name]
    ids = set()
    for fn in files:
        with open(MANIFEST_DIR / fn) as f:
            for row in csv.DictReader(f):
                ids.add(row["task_id"])
    return ids


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("results", help="path to eval results JSONL")
    ap.add_argument("--split", choices=["dev_train", "dev_val", "dev", "heldout"],
                    help="declared split; rows must stay inside it (no train/test leakage)")
    ap.add_argument("--expected-conditions", default="",
                    help="comma-separated conditions that must all be present")
    args = ap.parse_args()

    required = load_required()
    rows = []
    with open(args.results) as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as e:
                print(f"FAIL parse: line {i}: {e}")
                sys.exit(1)

    fails = []
    warns = []

    if not rows:
        fails.append("no rows in results file")

    # 1. required fields present + judge scores present.
    # "required" = key must exist and be non-None. Empty string is a valid value
    # (e.g. suffix is legitimately "" for no_suffix / non-suffix attacks). A small
    # subset must additionally be non-empty (identifiers).
    MUST_BE_NONEMPTY = {"run_id", "task_id", "code_commit", "condition", "decoding_config"}
    missing_field = Counter()
    for r in rows:
        for k in required:
            if k not in r or r[k] is None or (k in MUST_BE_NONEMPTY and r[k] == ""):
                missing_field[k] += 1
    if missing_field:
        fails.append(f"required fields missing/empty: {dict(missing_field)}")

    # 2. no duplicate (run_id, task_id, condition, seed)
    seen = Counter((r.get("run_id"), r.get("task_id"), r.get("condition"), r.get("seed"))
                   for r in rows)
    dups = {k: c for k, c in seen.items() if c > 1}
    if dups:
        fails.append(f"{len(dups)} duplicate (run_id,task_id,condition,seed) keys, e.g. {list(dups)[:3]}")

    # 3. no train/test overlap
    if args.split:
        allowed = load_split_ids(args.split)
        stray = sorted({r.get("task_id") for r in rows} - allowed)
        if stray:
            fails.append(f"{len(stray)} task_ids outside declared split '{args.split}': {stray[:5]}")

    # 4. all conditions present
    if args.expected_conditions:
        want = {c.strip() for c in args.expected_conditions.split(",") if c.strip()}
        have = {r.get("condition") for r in rows}
        missing = sorted(want - have)
        if missing:
            fails.append(f"expected conditions missing: {missing}")

    # 5. consistent denominators per condition (each condition covers the same task_ids x seeds)
    by_cond = defaultdict(set)
    for r in rows:
        by_cond[r.get("condition")].add((r.get("task_id"), r.get("seed")))
    sizes = {c: len(s) for c, s in by_cond.items()}
    if len(set(sizes.values())) > 1:
        warns.append(f"conditions have unequal denominators (possible partial eval): {sizes}")

    # 6. judge score sanity (reject bools: isinstance(True, int) is True in Python)
    def bad_score(v):
        return isinstance(v, bool) or not isinstance(v, (int, float)) \
            or not (0.0 <= float(v) <= 1.0)
    bad_scores = [r.get("task_id") for r in rows if bad_score(r.get("strongreject_score"))]
    if bad_scores:
        fails.append(f"{len(bad_scores)} rows with out-of-range/non-numeric strongreject_score")

    # 6b. enum validation against the schema (condition, decoding_config)
    schema = json.loads(SCHEMA.read_text())
    props = schema.get("properties", {})
    for field in ("condition", "decoding_config"):
        allowed = set(props.get(field, {}).get("enum", []))
        if allowed:
            bad = sorted({r.get(field) for r in rows if r.get(field) not in allowed})
            if bad:
                fails.append(f"invalid {field} value(s) not in schema enum: {bad}")

    # 7. code_commit consistency (single version per run_id)
    commits = defaultdict(set)
    for r in rows:
        commits[r.get("run_id")].add(r.get("code_commit"))
    mixed = {rid: cs for rid, cs in commits.items() if len(cs) > 1}
    if mixed:
        warns.append(f"run_id(s) span multiple code_commits: {list(mixed)[:3]}")

    print(f"[validate] {args.results}: {len(rows)} rows, conditions={sizes}")
    for w in warns:
        print(f"WARN: {w}")
    for fmsg in fails:
        print(f"FAIL: {fmsg}")
    if fails:
        sys.exit(1)
    print("PASS: all validation checks passed")


if __name__ == "__main__":
    main()
