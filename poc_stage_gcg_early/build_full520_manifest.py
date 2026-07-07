"""
Build full 520-behavior AdvBench manifest for ablation 4F.

Reads all 520 rows from llm-attacks/data/advbench/harmful_behaviors.csv
and writes a JSONL manifest compatible with evaluate_optimized_suffixes.py.

All 520 behaviors are marked as split="val" (held-out evaluation only;
we do not optimize against them — we only evaluate the existing suffix).

Usage:
    python -m poc_stage_gcg_early.build_full520_manifest \\
        --output outputs/stage_gcg_full/advbench_full520_manifest.jsonl
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

_DEFAULT_CSV = _REPO_ROOT / "llm-attacks" / "data" / "advbench" / "harmful_behaviors.csv"
_DEFAULT_OUT = _REPO_ROOT / "outputs" / "stage_gcg_full" / "advbench_full520_manifest.jsonl"


def main():
    parser = argparse.ArgumentParser(description="Build full 520-row AdvBench manifest")
    parser.add_argument(
        "--csv",
        type=Path,
        default=_DEFAULT_CSV,
        help=f"AdvBench harmful_behaviors.csv (default: {_DEFAULT_CSV})",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=_DEFAULT_OUT,
        help=f"Output JSONL path (default: {_DEFAULT_OUT})",
    )
    args = parser.parse_args()

    csv_path = args.csv
    out_path = args.output

    if not csv_path.exists():
        print(f"ERROR: CSV not found: {csv_path}", flush=True)
        sys.exit(1)

    out_path.parent.mkdir(parents=True, exist_ok=True)

    rows = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            goal   = row.get("goal", "").strip()
            target = row.get("target", "").strip()
            if not goal or not target:
                continue

            task_id = f"advbench_full_{i+1:04d}"

            task = {
                "task_id": task_id,
                "instruction": goal,
                "target_prefix": target,
                "safe_target_prefix": target,
                "neutral_control_suffix": " ",
                "split": "val",
                "seed": 42,
                "model": "qwen3",
                "enable_thinking": True,
                "source": "advbench",
                "advbench_row": i + 1,
            }
            rows.append(task)

    print(f"[build_full520] Loaded {len(rows)} behaviors from {csv_path}", flush=True)

    with open(out_path, "w", encoding="utf-8") as f:
        for task in rows:
            f.write(json.dumps(task) + "\n")

    sha256 = hashlib.sha256(out_path.read_bytes()).hexdigest()
    sha_path = out_path.with_suffix(".sha256")
    sha_path.write_text(sha256 + "\n")

    print(f"[build_full520] Written {len(rows)} rows to {out_path}", flush=True)
    print(f"[build_full520] SHA256: {sha256}", flush=True)
    print(f"[build_full520] SHA256 file: {sha_path}", flush=True)


if __name__ == "__main__":
    main()
