"""
Split 7A unseeded eval into N parallel shards.

Each shard gets its own run dir with a subset manifest.
After all shards complete, merge their FREE_GENERATION_RESULTS_UNSEEDED.jsonl
into the main run dir.

Usage:
  python scripts/split_unseeded_shards.py [--n-shards 5]
"""
import argparse
import json
import shutil
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.parent
MAIN_RUN_DIR = PROJECT_DIR / "outputs/stage_gcg_full/gcg_full_qwen3_7a_5a_full520"
MANIFEST_PATH = PROJECT_DIR / "outputs/stage_gcg_full/advbench_full520_manifest.jsonl"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-shards", type=int, default=5)
    args = parser.parse_args()

    manifest = [json.loads(l) for l in open(MANIFEST_PATH) if l.strip()]
    all_task_ids = [r["task_id"] for r in manifest]
    print(f"Total behaviors: {len(all_task_ids)}")

    # Find already-done task_ids
    done_ids = set()
    for src in [
        MAIN_RUN_DIR / "FREE_GENERATION_RESULTS_UNSEEDED.jsonl",
        MAIN_RUN_DIR / "_unseeded_tmp/FREE_GENERATION_RESULTS.jsonl",
    ]:
        if src.exists():
            rows = [json.loads(l) for l in open(src) if l.strip()]
            done_ids.update(r["task_id"] for r in rows)
    print(f"Already done: {len(done_ids)} behaviors")

    remaining = [t for t in all_task_ids if t not in done_ids]
    print(f"Remaining: {len(remaining)} behaviors → split into {args.n_shards} shards")

    # Split into shards
    shard_size = len(remaining) // args.n_shards
    shards = []
    for i in range(args.n_shards):
        start = i * shard_size
        end = start + shard_size if i < args.n_shards - 1 else len(remaining)
        shards.append(remaining[start:end])

    # Build task_id → manifest row lookup
    manifest_by_id = {r["task_id"]: r for r in manifest}

    for idx, shard_ids in enumerate(shards, start=1):
        shard_dir = PROJECT_DIR / f"outputs/stage_gcg_full/gcg_full_qwen3_7a_unseeded_shard{idx}"
        shard_dir.mkdir(parents=True, exist_ok=True)

        # Write shard manifest
        shard_manifest = [manifest_by_id[t] for t in shard_ids if t in manifest_by_id]
        with open(shard_dir / "MANIFEST.jsonl", "w") as f:
            for row in shard_manifest:
                f.write(json.dumps(row) + "\n")

        # Copy CONFIG.json and FINAL_CANDIDATES.jsonl
        for fname in ["CONFIG.json", "FINAL_CANDIDATES.jsonl"]:
            src = MAIN_RUN_DIR / fname
            if src.exists():
                shutil.copy2(src, shard_dir / fname)

        print(f"Shard {idx}: {len(shard_ids)} behaviors → {shard_dir.name}")

    print("\nSubmit with:")
    for idx in range(1, args.n_shards + 1):
        shard_dir = f"outputs/stage_gcg_full/gcg_full_qwen3_7a_unseeded_shard{idx}"
        print(f"  sbatch --export=ALL,RUN_DIR={shard_dir},SEEDS=100:200:300 "
              f"slurm_scripts/run_gcg_unseen_seed_eval.slurm")


if __name__ == "__main__":
    main()
