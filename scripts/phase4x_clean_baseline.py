#!/usr/bin/env python3
"""
Phase-4X clean (no-attack) baseline (plan §31.5/§31.6 headroom gate).

Sends each dev-25 goal to an open-source HF target with NO attack scaffold and NO suffix
(a bare user turn), so clean ASR can be compared to the attacked CoT-Hijacking ASR to prove
the attack has real headroom. Reuses the exact target backend used by the attack —
`models.hf_local.HFLocalLLM.batched_generate` (byte-repair + <think>-strip already handled) —
via `poc_stage2.hijacking_wrapper.ensure_hijacking_import_path`. No generation logic reimplemented.

Output rows match the StrongREJECT scorer's required schema
(poc_stage3/strongreject_scoring.py: goal, target_response, goal_index) so the same
`slurm_scripts/run_strongreject_cpu.slurm` scores them. Resume-safe by goal_index.

Greedy by default (temperature=0 → HFLocalLLM uses do_sample=False), matching the frozen §6 protocol.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


def _load_goals(manifest: str, limit: int) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    with open(manifest, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            rows.append((r["task_id"], r["instruction"]))
    if limit > 0:
        rows = rows[:limit]
    return rows


def _done_goal_indices(out_path: Path) -> set[int]:
    done: set[int] = set()
    if out_path.exists():
        with open(out_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        done.add(int(json.loads(line)["goal_index"]))
                    except (KeyError, ValueError):
                        pass
    return done


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--hf-id", required=True, help="e.g. deepseek-ai/DeepSeek-R1-Distill-Llama-8B")
    ap.add_argument("--manifest", default="data/manifests/dev_25.csv")
    ap.add_argument("--out-jsonl", required=True)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--max-new-tokens", type=int, default=4096)
    args = ap.parse_args()

    goals = _load_goals(args.manifest, args.limit)
    out_path = Path(args.out_jsonl)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    done = _done_goal_indices(out_path)
    todo = [(i, tid, g) for i, (tid, g) in enumerate(goals) if i not in done]
    print(f"[clean-baseline] hf:{args.hf_id} goals={len(goals)} todo={len(todo)} "
          f"(skip {len(done)} done) → {out_path}", flush=True)
    if not todo:
        print("[clean-baseline] nothing to do", flush=True)
        return 0

    # Reuse the attack's exact HF target backend (byte-repair + think-strip included).
    from poc_stage2.hijacking_wrapper import ensure_hijacking_import_path
    ensure_hijacking_import_path()
    from models.hf_local import HFLocalLLM  # type: ignore

    model = HFLocalLLM(args.hf_id, max_new_tokens=args.max_new_tokens)

    convs = [[{"role": "user", "content": g}] for _, _, g in todo]
    # temperature=0 → greedy (HFLocalLLM sets do_sample=False); top_p unused when greedy.
    responses = model.batched_generate(convs, max_n_tokens=args.max_new_tokens,
                                       temperature=0.0, top_p=1.0)
    assert len(responses) == len(todo), f"resp {len(responses)} != todo {len(todo)}"

    ts = datetime.now(timezone.utc).isoformat()
    with open(out_path, "a", encoding="utf-8") as f:
        for (gi, tid, goal), resp in zip(todo, responses):
            row = {
                "task_id": tid,
                "goal_index": gi,
                "goal": goal,
                "target_response": resp,
                # StrongREJECT scorer requires these Stage-2 fields to be PRESENT
                # (poc_stage3/strongreject_scoring.py REQUIRED_STAGE2_FIELDS); a clean
                # baseline runs no gemini judge, so they are null placeholders. The rubric
                # computes strongreject_score independently of these.
                "is_success": None,
                "judge_score": None,
                "target_model": f"hf:{args.hf_id}",
                "condition": "clean_no_attack",
                "decoding": "greedy",
                "timestamp_utc": ts,
            }
            f.write(json.dumps(row, ensure_ascii=True) + "\n")
            f.flush()
            print(f"[clean-baseline] gi={gi} task={tid} resp_len={len(resp)}", flush=True)

    print(f"[clean-baseline] done → {out_path}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
