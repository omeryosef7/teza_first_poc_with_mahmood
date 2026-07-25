#!/usr/bin/env python3
"""
Phase-3 free-generation evaluation of TROPT-optimized triggers (plan §7.5 B1-B8).

Reuses the existing Stage-9 harness `poc_stage_gcg_early.evaluate_optimized_suffixes.evaluate_suffix`
(free-gen + inline StrongREJECT scoring) and the shared loader
`poc_stage4.qwen3_model.load_qwen3_model` — no new generation/scoring/loading code.

Input: one or more TROPT `triggers.jsonl` files (from scripts/phase3_tropt_optimize.py),
each row: {task_id, category, instruction, template, target, best_trigger_str, optimizer,
target_style, model, best_loss}. `best_trigger_str` already carries the leading space, so
`instruction + best_trigger_str` reproduces the TROPT template exactly.

For every task the optimized trigger of each optimizer is evaluated (label=`tropt_<optimizer>`)
plus two shared controls evaluated once per task: `task_only` (" ") and `random_spaces`
(16 space tokens) — matching the plan's required baselines (§6.4: no-suffix, random suffix).
Primary decoding is greedy (frozen protocol, configs/evaluation/greedy.yaml).

Writes <out-dir>/FREE_GENERATION_RESULTS.jsonl (append, resume-safe by row_key).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


def _load_triggers(paths: list[str]) -> list[dict]:
    rows: list[dict] = []
    for p in paths:
        fp = Path(p)
        if not fp.exists():
            print(f"[phase3-eval] WARN missing triggers file: {fp}", flush=True)
            continue
        with open(fp, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    rows.append(json.loads(line))
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--triggers", nargs="+", required=True,
                    help="one or more TROPT triggers.jsonl paths")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--model-name", default="Qwen/Qwen3-14B")
    ap.add_argument("--model-family", default="qwen3")
    ap.add_argument("--seeds", type=int, nargs="+", default=[0])
    ap.add_argument("--limit", type=int, default=0, help="first N tasks (0=all)")
    ap.add_argument("--max-new-tokens", type=int, default=2048)
    ap.add_argument("--sampled", action="store_true",
                    help="use sampled decoding (default: greedy, frozen protocol)")
    ap.add_argument("--no-thinking", action="store_true")
    args = ap.parse_args()

    greedy = not args.sampled
    enable_thinking = not args.no_thinking
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    triggers = _load_triggers(args.triggers)
    if not triggers:
        print("[phase3-eval] no triggers loaded; nothing to do", flush=True)
        return 1

    # Group triggers by task_id (preserve first-seen order); a task may have >1 optimizer.
    by_task: dict[str, list[dict]] = {}
    order: list[str] = []
    for r in triggers:
        tid = r["task_id"]
        if tid not in by_task:
            by_task[tid] = []
            order.append(tid)
        by_task[tid].append(r)
    if args.limit > 0:
        order = order[: args.limit]

    print(f"[phase3-eval] {len(triggers)} triggers over {len(order)} tasks; "
          f"decoding={'greedy' if greedy else 'sampled'} seeds={args.seeds} "
          f"enable_thinking={enable_thinking}", flush=True)

    from poc_stage4.qwen3_model import load_qwen3_model
    from poc_stage_gcg_early.evaluate_optimized_suffixes import evaluate_suffix

    wrapped = load_qwen3_model(args.model_name, require_cuda=True, log_device_placement=True)
    model, tokenizer = wrapped.model, wrapped.tokenizer

    # Shared baselines (plan §6.4): no-suffix (task_only) and random matched-length suffix.
    task_only_suffix = " "
    random_suffix_str = tokenizer.decode([220] * 16, skip_special_tokens=True)

    n_written = 0
    for tid in order:
        rows = by_task[tid]
        instruction = rows[0]["instruction"]
        for seed in args.seeds:
            # Optimized trigger, one per optimizer present for this task.
            for r in rows:
                label = f"tropt_{r.get('optimizer', 'unknown')}"
                res = evaluate_suffix(
                    model, tokenizer, args.model_family,
                    task_id=tid, instruction=instruction,
                    suffix_str=r["best_trigger_str"], suffix_label=label,
                    enable_thinking=enable_thinking, seed=seed,
                    output_dir=out_dir, max_new_tokens=args.max_new_tokens, greedy=greedy,
                )
                if res is not None:
                    n_written += 1
                    print(f"[phase3-eval] task={tid} {label} seed={seed} "
                          f"sr={res.get('strongreject_score')} finish={res['finish_reason']}",
                          flush=True)
            # Shared controls, once per task/seed.
            for suffix_str, label in ((task_only_suffix, "task_only"),
                                      (random_suffix_str, "random_spaces")):
                res = evaluate_suffix(
                    model, tokenizer, args.model_family,
                    task_id=tid, instruction=instruction,
                    suffix_str=suffix_str, suffix_label=label,
                    enable_thinking=enable_thinking, seed=seed,
                    output_dir=out_dir, max_new_tokens=args.max_new_tokens, greedy=greedy,
                )
                if res is not None:
                    n_written += 1
                    print(f"[phase3-eval] task={tid} {label} seed={seed} "
                          f"sr={res.get('strongreject_score')} finish={res['finish_reason']}",
                          flush=True)

    print(f"[phase3-eval] done. {n_written} new rows → {out_dir}/FREE_GENERATION_RESULTS.jsonl",
          flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
