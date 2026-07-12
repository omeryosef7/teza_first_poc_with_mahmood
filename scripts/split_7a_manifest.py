"""
Split the 7A manifest into N shards for parallel evaluation.

Usage:
    python scripts/split_7a_manifest.py [--n-shards 6]

Creates:
  - outputs/stage_gcg_full/advbench_cot_shard{1..N}_manifest.jsonl
  - outputs/stage_gcg_full/gcg_full_qwen3_7a_shard{1..N}/  (with FINAL_CANDIDATES.jsonl + CONFIG.json)

Skips tasks that are fully done in the main 7A run dir (all 12 rows present).
"""
import argparse, json, shutil
from collections import Counter
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
STAGE_DIR = PROJECT / "outputs/stage_gcg_full"
MAIN_RUNDIR = STAGE_DIR / "gcg_full_qwen3_7a_5a_full520"
FULL_MANIFEST = STAGE_DIR / "advbench_cot_full520_manifest.jsonl"
N_ROWS_PER_TASK = 12  # 4 conditions × 3 seeds

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-shards", type=int, default=6)
    args = ap.parse_args()

    # --- find fully-done task_ids ---
    done_counts: Counter = Counter()
    free_gen = MAIN_RUNDIR / "FREE_GENERATION_RESULTS.jsonl"
    if free_gen.exists():
        with open(free_gen) as f:
            for line in f:
                if line.strip():
                    r = json.loads(line)
                    done_counts[r["task_id"]] += 1

    fully_done = {t for t, c in done_counts.items() if c >= N_ROWS_PER_TASK}
    print(f"Fully done tasks: {len(fully_done)}")

    # --- load full manifest ---
    all_tasks = [json.loads(l) for l in open(FULL_MANIFEST) if l.strip()]
    remaining = [t for t in all_tasks if t["task_id"] not in fully_done]
    print(f"Tasks remaining: {len(remaining)} / {len(all_tasks)}")

    # --- split into shards ---
    n = args.n_shards
    base, extra = divmod(len(remaining), n)
    shards, start = [], 0
    for i in range(n):
        size = base + (1 if i < extra else 0)
        shards.append(remaining[start:start + size])
        start += size

    # --- copy assets from main run dir ---
    candidates_src = MAIN_RUNDIR / "FINAL_CANDIDATES.jsonl"
    config_src = MAIN_RUNDIR / "CONFIG.json"

    for idx, shard_tasks in enumerate(shards, start=1):
        # write manifest
        manifest_path = STAGE_DIR / f"advbench_cot_shard{idx}_manifest.jsonl"
        with open(manifest_path, "w") as f:
            for row in shard_tasks:
                f.write(json.dumps(row) + "\n")
        print(f"Shard {idx}: {len(shard_tasks)} tasks → {manifest_path.name}")

        # create run dir
        shard_dir = STAGE_DIR / f"gcg_full_qwen3_7a_shard{idx}"
        shard_dir.mkdir(exist_ok=True)

        for src in [candidates_src, config_src]:
            dst = shard_dir / src.name
            if not dst.exists():
                shutil.copy2(src, dst)

        print(f"  → run dir: {shard_dir.name}")

    print(f"\nDone. Submit with:")
    for i in range(1, n + 1):
        print(f"  sbatch --export=ALL,SHARD_ID={i} slurm_scripts/run_gcg_full_7a_shard.slurm")

if __name__ == "__main__":
    main()
