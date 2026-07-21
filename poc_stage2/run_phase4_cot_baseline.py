#!/usr/bin/env python3
"""Phase 4 (RESEARCH_PLAN_DISTILLING_JAILBREAKS.md sec 8): run the real
Chain-of-Thought Hijacking attack baseline on our dev-25 AdvBench goals,
REUSING the existing wrapper (poc_stage2.hijacking_wrapper.run_hijacking_slice)
with its explicit-goals path. No attack logic is reimplemented here.

Loads goals from data/manifests/*.csv so results tie back to our task_ids
(plan sec 5 split). Writes schema-conformant JSONL + summary + a
task_id<->goal_index map to outputs/.

Usage (smoke first, then full):
  python -m poc_stage2.run_phase4_cot_baseline --target-model gpt-o4-mini --limit 2 --n-streams 1 --n-iterations 1
  python -m poc_stage2.run_phase4_cot_baseline --target-model gpt-o4-mini            # full dev-25

Requires API keys in .env (loaded by the wrapper).
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from poc_stage2.hijacking_wrapper import run_hijacking_slice, summary_as_jsonable

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def load_manifest_goals(manifest: Path):
    rows = []
    with open(manifest) as f:
        for r in csv.DictReader(f):
            rows.append((r["task_id"], r["category"], r["instruction"]))
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", default="data/manifests/dev_25.csv")
    ap.add_argument("--target-model", default="gpt-o4-mini")
    ap.add_argument("--n-iterations", type=int, default=2)
    ap.add_argument("--n-streams", type=int, default=6)
    ap.add_argument("--limit", type=int, default=0, help="run only first N goals (smoke); 0=all")
    ap.add_argument("--output-dir", default="outputs/phase4_cot_baseline")
    args = ap.parse_args()

    manifest = PROJECT_ROOT / args.manifest
    entries = load_manifest_goals(manifest)
    if args.limit:
        entries = entries[: args.limit]
    task_ids = [e[0] for e in entries]
    goals = [e[2] for e in entries]

    result = run_hijacking_slice(
        target_model=args.target_model,
        start_example=1,
        end_example=1 + len(goals),
        n_iterations=args.n_iterations,
        n_streams=args.n_streams,
        goals=goals,
        wandb_mode="disabled",
    )

    out_dir = PROJECT_ROOT / args.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    slice_tag = f"dev{len(goals)}" if not args.limit else f"smoke{len(goals)}"
    # sanitize target_model for filenames (hf:org/model -> hf_org_model)
    safe_model = args.target_model.replace("hf:", "hf_").replace("/", "_").replace(":", "_")
    stem = f"phase4_cot_{safe_model}_{slice_tag}"

    # task_id <-> goal_index map (goal_index is the absolute_index the wrapper stamps,
    # here start_index=0 so goal_index == position in our list)
    id_map = {i: task_ids[i] for i in range(len(task_ids))}
    (out_dir / f"{stem}_taskmap.json").write_text(json.dumps(id_map, indent=2))

    jsonl_path = out_dir / f"{stem}.jsonl"
    with jsonl_path.open("w", encoding="utf-8") as fh:
        for row in result.rows:
            d = row.to_dict()
            gi = d.get("goal_index")
            d["task_id"] = id_map.get(gi, id_map.get(int(gi) if gi is not None else -1))
            fh.write(json.dumps(d, ensure_ascii=False) + "\n")

    (out_dir / f"{stem}_summary.json").write_text(
        json.dumps(summary_as_jsonable(result), indent=2, ensure_ascii=False) + "\n")

    print(f"[phase4] target={args.target_model} goals={len(goals)} "
          f"ASR={result.summary.get('attack_success_rate'):.3f} "
          f"({result.summary.get('num_successes')}/{result.summary.get('num_goals')})")
    print(f"[phase4] wrote {jsonl_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
