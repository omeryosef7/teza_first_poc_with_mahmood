"""
Merge shard FREE_GENERATION_RESULTS.jsonl files into the main 7A run dir.

Usage:
    python scripts/merge_7a_shards.py [--n-shards 6] [--dry-run]

Deduplicates by row_key = task_id + "|" + condition_label + "|" + str(seed).
The first occurrence (main dir rows first, then shard 1-6) is kept.
Result is written to the main dir's FREE_GENERATION_RESULTS.jsonl.
"""
import argparse, json
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
STAGE_DIR = PROJECT / "outputs/stage_gcg_full"
MAIN_RUNDIR = STAGE_DIR / "gcg_full_qwen3_7a_5a_full520"

def row_key(r):
    return f"{r['task_id']}|{r.get('condition_label', '')}|{r.get('seed', '')}"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-shards", type=int, default=6)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    all_rows = {}  # key → row (dict), preserving insertion order

    # Load main dir first (already-done rows take priority)
    main_file = MAIN_RUNDIR / "FREE_GENERATION_RESULTS.jsonl"
    if main_file.exists():
        with open(main_file) as f:
            for line in f:
                if line.strip():
                    r = json.loads(line)
                    k = row_key(r)
                    if k not in all_rows:
                        all_rows[k] = r
        print(f"Main dir: {len(all_rows)} rows")

    # Load shards
    for idx in range(1, args.n_shards + 1):
        shard_file = STAGE_DIR / f"gcg_full_qwen3_7a_shard{idx}" / "FREE_GENERATION_RESULTS.jsonl"
        if not shard_file.exists():
            print(f"Shard {idx}: missing ({shard_file}) — skipping")
            continue
        before = len(all_rows)
        with open(shard_file) as f:
            for line in f:
                if line.strip():
                    r = json.loads(line)
                    k = row_key(r)
                    if k not in all_rows:
                        all_rows[k] = r
        added = len(all_rows) - before
        print(f"Shard {idx}: +{added} rows (file had {sum(1 for _ in open(shard_file) if _.strip())} rows)")

    total = len(all_rows)
    print(f"\nMerged total: {total} / 6240 rows")

    if args.dry_run:
        print("[dry-run] Not writing.")
        return

    out_path = MAIN_RUNDIR / "FREE_GENERATION_RESULTS.jsonl"
    # Backup original
    backup = MAIN_RUNDIR / "FREE_GENERATION_RESULTS.jsonl.pre_merge_backup"
    if main_file.exists() and not backup.exists():
        import shutil
        shutil.copy2(main_file, backup)
        print(f"Backed up original to {backup.name}")

    with open(out_path, "w") as f:
        for r in all_rows.values():
            f.write(json.dumps(r) + "\n")

    print(f"Written: {out_path}")
    print(f"Total rows: {total} / 6240")

    if total >= 6200:
        print("\n>>> 7A COMPLETE — ready for replay + analysis + unseeded pipeline")
    else:
        print(f"\nStill missing {6240 - total} rows — resubmit incomplete shards.")

if __name__ == "__main__":
    main()
