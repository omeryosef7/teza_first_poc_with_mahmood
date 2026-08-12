#!/usr/bin/env python3
"""Batched evaluator for §7.5: load the model ONCE, then loop over many (suffix, prompt) evals.

Why this exists: `26_eval_p9_gcg_heldout_asr.py` loads the model on every invocation. §7.5 needs
~37 per-prompt evals plus ~37 transfer sources per arm per seed, i.e. ~74 model loads (~5 GPU-h
of pure loading per arm-seed, ~45 h across the approved matrix). This driver pays that once.

It does NOT reimplement scoring: it calls the SAME
`poc_stage_gcg_early.evaluate_optimized_suffixes.evaluate_suffix` that `26_eval` calls, writing
to the same `FREE_GENERATION_RESULTS.jsonl` with the same `(task_id, suffix_label, seed)` row
key -- so results are resume-safe, deduped, and directly comparable to the universal arms.
Aggregate afterwards with `scripts/aggregate_perprompt_asr.py`.

Two modes:
  --mode perprompt --joblist J.jsonl --arm-label L
      Each prompt's own suffix on its own prompt (the §7.5 diagonal / threat-model number).
  --mode transfer --plan P.jsonl
      Each source's suffix on that source's target list (diagonal + off-diagonal).

Safety: reads suffix strings to feed the generator but NEVER prints or stores them; stdout is
task_ids and scalars only (§3.14).
"""
from __future__ import annotations
import argparse, json, os, sys, time
from pathlib import Path

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)


def final_suffix(run_dir: str) -> str:
    with open(os.path.join(run_dir, "FINAL_CANDIDATES.jsonl")) as fh:
        return json.loads(fh.readline())["suffix_str"]


def load_split(manifest: str, split: str):
    rows = [json.loads(l) for l in open(manifest) if l.strip()]
    if split and split != "all":
        rows = [r for r in rows if r.get("split") == split]
    return [(r["task_id"], r["instruction"]) for r in rows]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", required=True, choices=["perprompt", "transfer"])
    ap.add_argument("--joblist", help="perprompt mode")
    ap.add_argument("--arm-label", help="perprompt mode: condition label to record")
    ap.add_argument("--plan", help="transfer mode")
    ap.add_argument("--split", default="test")
    ap.add_argument("--model-family", default="llama")
    ap.add_argument("--model-name-or-path", default="meta-llama/Llama-3.1-8B-Instruct")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--max-new-tokens", type=int, default=2048)
    ap.add_argument("--shard", type=int, default=0)
    ap.add_argument("--nshard", type=int, default=1)
    ap.add_argument("--dry-run", action="store_true",
                    help="build and report the work list, then exit WITHOUT loading the model. "
                         "Lets a shard layout be validated on a login node (no GPU, seconds).")
    args = ap.parse_args()
    if not 0 <= args.shard < args.nshard:
        raise SystemExit(f"--shard {args.shard} out of range for --nshard {args.nshard}")

    # ---- build the work list BEFORE loading the model, so a bad config fails in seconds ----
    # work item = (output_dir, suffix_str, suffix_label, task_id, instruction)
    work = []
    if args.mode == "perprompt":
        if not (args.joblist and args.arm_label):
            raise SystemExit("--mode perprompt needs --joblist and --arm-label")
        jobs = [json.loads(l) for l in open(args.joblist) if l.strip()]
        n_unfinished = 0
        for j in jobs:
            try:
                suf = final_suffix(j["output_dir"])
            except Exception:
                n_unfinished += 1
                continue
            tasks = load_split(j["manifest"], "all")   # the 1-row manifest
            for tid, instr in tasks:
                work.append((j["output_dir"], suf, args.arm_label, tid, instr))
        print(f"[eval-pp] {len(jobs)} listed, {n_unfinished} without a finished optimization", flush=True)
    else:
        if not args.plan:
            raise SystemExit("--mode transfer needs --plan")
        plan = [json.loads(l) for l in open(args.plan) if l.strip()]
        n_unfinished = 0
        for p in plan:
            try:
                suf = final_suffix(p["source_run_dir"])
            except Exception:
                n_unfinished += 1
                continue
            for tid, instr in load_split(p["target_manifest"], p.get("split", args.split)):
                work.append((p["source_run_dir"], suf, p["arm_label"], tid, instr))
        print(f"[eval-xfer] {len(plan)} sources, {n_unfinished} without a finished optimization", flush=True)

    if not work:
        raise SystemExit("no work items -- nothing has finished optimizing yet")
    n_total = len(work)
    work = [w for i, w in enumerate(work) if i % args.nshard == args.shard]
    print(f"[eval] shard {args.shard}/{args.nshard}: {len(work)} of {n_total} "
          f"(suffix,prompt) evaluations", flush=True)
    if args.dry_run:
        # task_ids only -- never the suffix or the instruction text.
        print("[eval][dry-run] first ids: "
              + ", ".join(t for _, _, _, t, _ in work[:5]) + (" ..." if len(work) > 5 else ""))
        print("[eval][dry-run] no model loaded, exiting")
        return

    from poc_stage4.qwen3_model import load_qwen3_model
    from poc_stage_gcg_early.evaluate_optimized_suffixes import evaluate_suffix
    wrapped = load_qwen3_model(args.model_name_or_path, require_cuda=True,
                               log_device_placement=True)
    model, tokenizer = wrapped.model, wrapped.tokenizer
    print("[eval] model loaded once; starting loop", flush=True)

    t0 = time.time()
    done = skipped = failed = 0
    for i, (odir, suf, label, tid, instr) in enumerate(work):
        try:
            res = evaluate_suffix(
                model, tokenizer, args.model_family,
                task_id=tid, instruction=instr,
                suffix_str=suf, suffix_label=label,
                enable_thinking=False, seed=args.seed,
                output_dir=Path(odir), max_new_tokens=args.max_new_tokens, greedy=True,
            )
            if res is None:
                skipped += 1          # already logged -> resume
            else:
                done += 1
                print(f"  [{i+1}/{len(work)}] {tid} sr_success={res.get('strongreject_is_success')}"
                      f" sr_score={res.get('strongreject_score')}", flush=True)
        except Exception as e:
            failed += 1
            print(f"  [{i+1}/{len(work)}] {tid} FAILED: {e!r}", flush=True)
        if (i + 1) % 20 == 0:
            print(f"[eval] {i+1}/{len(work)} ({time.time()-t0:.0f}s)", flush=True)

    print(f"[eval] finished: generated={done} resumed={skipped} failed={failed} "
          f"in {time.time()-t0:.0f}s", flush=True)
    if failed:
        raise SystemExit(f"{failed} evaluations failed -- do not aggregate until resolved")


if __name__ == "__main__":
    main()
