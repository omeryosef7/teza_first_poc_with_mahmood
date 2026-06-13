#!/usr/bin/env python3
"""
Prepare Stage 4.8 extension v2: seeds 106-115 for goals 0 and 2.

Creates a new manifest JSONL and run directory targeting 10 new seeds
for the same goals/conditions as the original Stage 4.8 run.

These additional seeds push towards ≥4 matched outcome cells,
which unlocks behavior-conditioned direction extraction at Layer 22.
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

_REPO = Path(__file__).resolve().parent
_ORIG_MANIFEST = _REPO / "outputs/stage4_8/repeated_generation_manifest.jsonl"
_OUT_BASE = _REPO / "outputs/stage4_8/runs"

NEW_SEEDS = list(range(106, 116))   # 106..115 inclusive
TARGET_GOALS = ["0", "2"]
TARGET_CONDITIONS = ["A", "D", "F"]

SOURCE_IDS = {
    "0": "goal_index=0|attack_iteration=1|conversation_id=5|target_model=gpt-o4-mini",
    "2": "goal_index=2|attack_iteration=1|conversation_id=3|target_model=gpt-o4-mini",
}


def build_run_id(source_example_id: str, condition: str, seed: int) -> str:
    # Format: goal_index=0__attack_iteration=1__conversation_id=5__target_model=gpt-o4-mini__cond_A__seed_106
    parts = dict(p.split("=", 1) for p in source_example_id.split("|"))
    return (
        f"goal_index={parts['goal_index']}__"
        f"attack_iteration={parts['attack_iteration']}__"
        f"conversation_id={parts['conversation_id']}__"
        f"target_model={parts['target_model']}__"
        f"cond_{condition}__seed_{seed}"
    )


def load_template_row(goal: str, condition: str) -> dict:
    rows = [json.loads(l) for l in _ORIG_MANIFEST.read_text().splitlines() if l.strip()]
    for r in rows:
        if str(r["goal_index"]) == goal and r["condition"] == condition:
            return dict(r)
    raise ValueError(f"No template for goal={goal} cond={condition}")


def main():
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = _OUT_BASE / f"run_array_extension2_{ts}"
    run_dir.mkdir(parents=True, exist_ok=True)

    manifest_rows = []
    for goal in TARGET_GOALS:
        source_id = SOURCE_IDS[goal]
        for cond in TARGET_CONDITIONS:
            template = load_template_row(goal, cond)
            for seed in NEW_SEEDS:
                row = dict(template)
                row["seed"] = seed
                row["source_example_id"] = source_id
                row["run_id"] = build_run_id(source_id, cond, seed)
                row["prompt_hash"] = row.get("prompt_hash", "")
                manifest_rows.append(row)

    manifest_path = run_dir / "repeated_generation_manifest.jsonl"
    with manifest_path.open("w") as f:
        for row in manifest_rows:
            f.write(json.dumps(row) + "\n")

    # Write status JSON
    status = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "n_rows": len(manifest_rows),
        "new_seeds": NEW_SEEDS,
        "target_goals": TARGET_GOALS,
        "target_conditions": TARGET_CONDITIONS,
        "manifest_path": str(manifest_path),
        "run_dir": str(run_dir),
        "status": "prepared",
        "purpose": "extension v2: seeds 106-115 for goals 0 and 2; unblock direction extraction (need >=4 matched cells)",
    }
    (run_dir / "extension_status.json").write_text(json.dumps(status, indent=2))

    print(f"Extension v2 prepared.")
    print(f"  Run dir:   {run_dir}")
    print(f"  Manifest:  {manifest_path}")
    print(f"  Rows:      {len(manifest_rows)} ({len(TARGET_GOALS)} goals × {len(TARGET_CONDITIONS)} conds × {len(NEW_SEEDS)} seeds)")
    print(f"  Seeds:     {NEW_SEEDS}")
    print()
    print(f"To submit:")
    print(f"  sbatch --array=0,2 \\")
    print(f"    --export=ALL,RUN_DIR={run_dir},MANIFEST={manifest_path} \\")
    print(f"    slurm_scripts/stage4_8_repeated_generations_array.slurm")
    print()
    print(f"RUN_DIR={run_dir}")
    print(f"MANIFEST={manifest_path}")


if __name__ == "__main__":
    main()
