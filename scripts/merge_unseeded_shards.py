"""
Merge 7A unseeded shard results into the main run dir.

Collects FREE_GENERATION_RESULTS_UNSEEDED.jsonl from:
  - main run dir (from 655837 and the watcher's copy)
  - each shard dir (gcg_full_qwen3_7a_unseeded_shard{1..5})

Deduplicates by row_key and writes to main dir's UNSEEDED file.

Usage:
  python scripts/merge_unseeded_shards.py
"""
import json
import shutil
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.parent
MAIN_RUN_DIR = PROJECT_DIR / "outputs/stage_gcg_full/gcg_full_qwen3_7a_5a_full520"
N_SHARDS = 5


def main():
    seen_keys = set()
    all_rows = []

    sources = [MAIN_RUN_DIR] + [
        PROJECT_DIR / f"outputs/stage_gcg_full/gcg_full_qwen3_7a_unseeded_shard{i}"
        for i in range(1, N_SHARDS + 1)
    ]

    for src_dir in sources:
        # Try UNSEEDED file first, then tmp
        for fname in ["FREE_GENERATION_RESULTS_UNSEEDED.jsonl",
                      "_unseeded_tmp/FREE_GENERATION_RESULTS.jsonl"]:
            fpath = src_dir / fname
            if fpath.exists():
                rows = [json.loads(l) for l in open(fpath) if l.strip()]
                new = 0
                for r in rows:
                    k = r.get("row_key", "")
                    if k not in seen_keys:
                        seen_keys.add(k)
                        all_rows.append(r)
                        new += 1
                print(f"  {src_dir.name}/{fname}: {len(rows)} rows, {new} new")
                break

    dst = MAIN_RUN_DIR / "FREE_GENERATION_RESULTS_UNSEEDED.jsonl"
    if dst.exists():
        shutil.copy2(dst, dst.with_suffix(".jsonl.pre_merge_backup"))
    with open(dst, "w") as f:
        for r in all_rows:
            f.write(json.dumps(r) + "\n")

    print(f"\nMerged {len(all_rows)} rows → {dst}")

    # Quick ASR summary
    from collections import defaultdict
    by_cond = defaultdict(list)
    for r in all_rows:
        s = 1 if r.get("strongreject_is_success", False) else 0
        by_cond[r.get("condition_label", "?")].append(s)
    print("\nUnseeded ASR summary (so far):")
    for c in ["optimized_weighted", "neutral_control", "random_spaces", "task_only"]:
        vals = by_cond.get(c, [])
        if vals:
            print(f"  {c}: {sum(vals)}/{len(vals)} = {sum(vals)/len(vals)*100:.2f}%")
    print(f"\nTotal rows: {len(all_rows)} / 3120")


if __name__ == "__main__":
    main()
