"""
Build the Stage GCG-Full AdvBench behavior manifest.

Reads llm-attacks/data/advbench/harmful_behaviors.csv (520 behaviors),
selects 25 evenly-spaced rows (20 train + 5 val), and writes
outputs/stage_gcg_full/advbench_manifest_v1.jsonl.

Also writes a SHA256 checksum to advbench_manifest_v1.sha256 so that
config.py can verify manifest integrity at run time.

Usage:
    python -m poc_stage_gcg_early.build_advbench_manifest
    python -m poc_stage_gcg_early.build_advbench_manifest --n-train 20 --n-val 5
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
_CSV_PATH = _REPO_ROOT / "llm-attacks" / "data" / "advbench" / "harmful_behaviors.csv"
_DEFAULT_OUTPUT_DIR = _REPO_ROOT / "outputs" / "stage_gcg_full"
_DEFAULT_OUTPUT_FILE = "advbench_manifest_v1.jsonl"


def _evenly_spaced_indices(n_total: int, n_select: int) -> list[int]:
    """Return n_select indices evenly spaced in [0, n_total)."""
    if n_select > n_total:
        raise ValueError(f"Cannot select {n_select} from {n_total} rows")
    step = n_total / n_select
    return [int(i * step) for i in range(n_select)]


def build_manifest(
    csv_path: Path,
    n_train: int,
    n_val: int,
    model: str,
    seed: int,
) -> list[dict]:
    """Read AdvBench CSV and return a list of SurrogateTask-compatible dicts."""
    with open(csv_path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    n_total = len(rows)
    n_select = n_train + n_val
    selected_indices = _evenly_spaced_indices(n_total, n_select)

    tasks = []
    for rank, row_idx in enumerate(selected_indices):
        row = rows[row_idx]
        split = "train" if rank < n_train else "val"
        task_id = f"advbench_{row_idx + 1:03d}"   # 1-based row number from CSV
        tasks.append({
            "task_id": task_id,
            "instruction": row["goal"],
            "safe_target_prefix": row["target"],
            "early_prefix": None,
            "neutral_control_suffix": " ",
            "split": split,
            "seed": seed,
            "model": model,
            "enable_thinking": True,
            "source": "advbench",
            "advbench_row": row_idx + 1,        # 1-based for human readability
        })

    return tasks


def write_manifest(tasks: list[dict], output_path: Path) -> str:
    """Write JSONL and return SHA256 hex digest of the file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        for task in tasks:
            f.write(json.dumps(task, ensure_ascii=False) + "\n")

    digest = hashlib.sha256(output_path.read_bytes()).hexdigest()
    sha_path = output_path.with_suffix(".sha256")
    sha_path.write_text(f"{digest}  {output_path.name}\n")
    return digest


def main() -> None:
    parser = argparse.ArgumentParser(description="Build AdvBench GCG-Full manifest")
    parser.add_argument("--n-train", type=int, default=20, help="Number of train behaviors (default 20)")
    parser.add_argument("--n-val", type=int, default=5, help="Number of val behaviors (default 5)")
    parser.add_argument("--model", default="qwen3", help="Model family tag (default: qwen3)")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output-dir", default=str(_DEFAULT_OUTPUT_DIR))
    parser.add_argument("--output-file", default=_DEFAULT_OUTPUT_FILE)
    args = parser.parse_args()

    csv_path = _CSV_PATH
    if not csv_path.exists():
        print(f"ERROR: AdvBench CSV not found at {csv_path}", file=sys.stderr)
        sys.exit(1)

    tasks = build_manifest(csv_path, args.n_train, args.n_val, args.model, args.seed)
    output_path = Path(args.output_dir) / args.output_file

    if output_path.exists():
        print(f"WARNING: Output file already exists: {output_path}")
        print("Overwriting...")

    digest = write_manifest(tasks, output_path)

    n_train = sum(1 for t in tasks if t["split"] == "train")
    n_val = sum(1 for t in tasks if t["split"] == "val")

    print(f"Wrote {len(tasks)} behaviors ({n_train} train, {n_val} val) to:")
    print(f"  {output_path}")
    print(f"SHA256: {digest}")
    print()
    print("Train behaviors:")
    for t in tasks:
        if t["split"] == "train":
            print(f"  [{t['task_id']}] {t['instruction'][:80]}")
    print()
    print("Val behaviors:")
    for t in tasks:
        if t["split"] == "val":
            print(f"  [{t['task_id']}] {t['instruction'][:80]}")


if __name__ == "__main__":
    main()
