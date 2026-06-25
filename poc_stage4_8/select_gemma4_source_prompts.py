"""
Stage 4.8 — Select 4 source prompts for the Gemma4 repeated-generation factorial.

Selects one source prompt per goal (goals 0–3) from the 220 clean Gemma4 Stage 6
traces in outputs/stage6/gemma_traces_full_1_11_eos_fixed/.

Selection criteria:
  - thinking_segmentation_status == "parsed_from_thought_channel"
  - generation_validation_status == "valid"
  - generation_finish_reason == "eos_token"
  - One per goal (0–3)
  - Tie-break: |strongreject_score - 0.5| ascending (prefer intermediate behaviour),
    then conversation_id ascending (deterministic)

Output:
  outputs/stage4_8_gemma/source_prompt_selection.csv
  outputs/stage4_8_gemma/source_prompt_selection_manifest.json

Usage:
  python -m poc_stage4_8.select_gemma4_source_prompts
      [--traces-dir outputs/stage6/gemma_traces_full_1_11_eos_fixed]
      [--output-dir outputs/stage4_8_gemma]
      [--goals 0,1,2,3]
"""
from __future__ import annotations

import argparse
import csv
import glob
import json
import math
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

_TRACES_DIR = _REPO_ROOT / "outputs" / "stage6" / "gemma_traces_full_1_11_eos_fixed"
_OUTPUT_DIR = _REPO_ROOT / "outputs" / "stage4_8_gemma"
_GOALS = [0, 1, 2, 3]

_FNAME_RE = re.compile(
    r"gemma_4_e4b_it_trace_goal_index_(\d+)_attack_iteration_(\d+)_conversation_id_(\d+)_target_model_(.+)\.json$"
)


def _f(x, default: float = float("nan")) -> float:
    try:
        return float(x)
    except (TypeError, ValueError):
        return default


def _interest_score(sr_score: float) -> float:
    if math.isnan(sr_score):
        return 1.0
    return abs(sr_score - 0.5)


def _parse_fname(fname: str) -> dict | None:
    m = _FNAME_RE.search(fname)
    if not m:
        return None
    return {
        "goal_index": int(m.group(1)),
        "attack_iteration": int(m.group(2)),
        "conversation_id": int(m.group(3)),
        "target_model": m.group(4),
    }


def load_trace_index(traces_dir: Path) -> list[dict]:
    """Scan all traces, extract key fields without loading token tables."""
    records = []
    pattern = str(traces_dir / "gemma_4_e4b_it_trace_*.json")
    paths = sorted(glob.glob(pattern))
    print(f"Found {len(paths)} trace files in {traces_dir}")

    for p in paths:
        fname = Path(p).name
        parsed = _parse_fname(fname)
        if parsed is None:
            continue

        try:
            with open(p, encoding="utf-8") as f:
                trace = json.load(f)
        except Exception as e:
            print(f"  SKIP {fname}: {e}")
            continue

        sr_result = trace.get("strongreject_result", {})
        if not isinstance(sr_result, dict):
            sr_result = {}

        sr_score = _f(sr_result.get("strongreject_score"))
        attack_prompt = sr_result.get("attack_prompt", "")
        goal_text = sr_result.get("goal", "")

        seg_status = trace.get("thinking_segmentation_status", "")
        val_status = trace.get("generation_validation_status", "")
        finish_reason = trace.get("generation_finish_reason", "")
        think_token_count = trace.get("token_table_length", 0)  # approximate; not critical

        # Build source_example_id mirroring the Qwen3 convention
        gi = parsed["goal_index"]
        ai = parsed["attack_iteration"]
        ci = parsed["conversation_id"]
        tm = parsed["target_model"]
        source_example_id = f"goal_index={gi}|attack_iteration={ai}|conversation_id={ci}|target_model={tm}"

        records.append({
            "source_example_id": source_example_id,
            "goal_index": gi,
            "attack_iteration": ai,
            "conversation_id": ci,
            "target_model": tm,
            "sr_score": sr_score,
            "sr_success": bool(not math.isnan(sr_score) and sr_score >= 0.5),
            "attack_prompt": attack_prompt,
            "goal": goal_text,
            "thinking_segmentation_status": seg_status,
            "generation_validation_status": val_status,
            "generation_finish_reason": finish_reason,
            "trace_path": p,
        })

    print(f"Indexed {len(records)} traces")
    return records


def select_prompts(
    records: list[dict],
    goals: list[int],
) -> tuple[list[dict], list[dict]]:
    selected = []
    rejected = []

    for goal in goals:
        goal_recs = [r for r in records if r["goal_index"] == goal]

        # Eligibility
        eligible = [
            r for r in goal_recs
            if r["thinking_segmentation_status"] == "parsed_from_thought_channel"
            and r["generation_validation_status"] == "valid"
            and r["generation_finish_reason"] == "eos_token"
        ]

        ineligible = [r for r in goal_recs if r not in eligible]
        for r in ineligible:
            rejected.append({**r, "rejection_reason": "ineligible_generation"})

        if not eligible:
            print(f"  WARNING: No eligible traces for goal {goal}")
            continue

        # Sort by interest score (closest to 0.5), break ties by conversation_id
        eligible_sorted = sorted(eligible, key=lambda r: (_interest_score(r["sr_score"]), r["conversation_id"]))
        winner = eligible_sorted[0]
        selected.append(winner)

        print(
            f"  goal={goal}: selected conv={winner['conversation_id']} "
            f"iter={winner['attack_iteration']} "
            f"sr={winner['sr_score']:.3f} "
            f"seg={winner['thinking_segmentation_status']}"
        )

        for r in eligible_sorted[1:]:
            rejected.append({**r, "rejection_reason": "not_selected_for_goal"})

    return selected, rejected


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--traces-dir", default=str(_TRACES_DIR))
    parser.add_argument("--output-dir", default=str(_OUTPUT_DIR))
    parser.add_argument("--goals", default="0,1,2,3")
    args = parser.parse_args()

    goals = [int(g) for g in args.goals.split(",")]
    traces_dir = Path(args.traces_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    records = load_trace_index(traces_dir)
    selected, rejected = select_prompts(records, goals)

    # Write CSV
    csv_path = output_dir / "source_prompt_selection.csv"
    fieldnames = [
        "source_example_id", "goal_index", "attack_iteration", "conversation_id",
        "target_model", "sr_score", "sr_success", "thinking_segmentation_status",
        "generation_validation_status", "generation_finish_reason", "trace_path",
    ]
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for s in selected:
            writer.writerow({k: s.get(k, "") for k in fieldnames})

    # Write manifest JSON
    manifest = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "traces_dir": str(traces_dir),
        "n_selected": len(selected),
        "n_rejected": len(rejected),
        "goals": goals,
        "selected": [
            {
                "source_example_id": s["source_example_id"],
                "goal_index": s["goal_index"],
                "attack_prompt": s["attack_prompt"],
                "goal": s["goal"],
                "sr_score": s["sr_score"],
                "trace_path": s["trace_path"],
            }
            for s in selected
        ],
    }
    manifest_path = output_dir / "source_prompt_selection_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print(f"\nSelected {len(selected)} source prompts → {csv_path}")
    print(f"Manifest → {manifest_path}")
    for s in selected:
        print(f"  goal={s['goal_index']} source_id={s['source_example_id']} sr={s['sr_score']:.3f}")


if __name__ == "__main__":
    main()
