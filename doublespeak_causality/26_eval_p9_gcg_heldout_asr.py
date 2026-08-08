"""
26_eval_p9_gcg_heldout_asr.py — Gate-7 first-cut EVAL (plan §17 / GATE7_EXECUTION_PLAN §4 + §6-B).

Applies ONE arm run-dir's optimized GCG suffix (FINAL_CANDIDATES.jsonl row[0].suffix_str, applied as a
USER-turn suffix — suffix_placement=user) to the HELD-OUT split of the clearharm_llama doublespeak
manifest, generates GREEDILY, and scores StrongREJECT ASR + refusal_rate + empty_rate + mean score.

REUSE (no new harness):
  * generation + StrongREJECT judge  = poc_stage_gcg_early.evaluate_optimized_suffixes.evaluate_suffix
    (the exact function named in plan §6-B; greedy=True = frozen Phase-2 greedy protocol; max_new=2048)
  * model load                       = poc_stage4.qwen3_model.load_qwen3_model (the same loader
    run_optimization uses for --model-family llama; require_cuda=True)
  * refusal keyword detector         = doublespeak_causality/18_run_behavioral_necessity.py::kw_refusal
    (imported verbatim — zero judge drift)
StrongREJECT needs OPENAI_API_KEY (evaluate_suffix scores per row and records strongreject_score /
strongreject_is_success; a missing key surfaces as strongreject_error and score=None → judge_fail).

This driver evaluates ONE arm so the SLURM wrapper can `|| true` each arm independently (one arm's
gen/judge failure never aborts the rest). evaluate_suffix appends to FREE_GENERATION_RESULTS.jsonl in
the run-dir and is resume-safe by row_key; this driver re-reads that file to aggregate (so resumed
rows still count). The per-arm p9_heldout_asr_summary.json is SCALAR-ONLY — it never embeds the raw
optimized suffix string (adversarial text) or any generation text; only suffix length.

Harmful generation + judging → SLURM / MAIN LOOP only, NEVER a subagent.

Usage (one arm):
  python doublespeak_causality/26_eval_p9_gcg_heldout_asr.py \
    --run-dir outputs/stage_gcg_full/phase9_gcg_mac_matrix_arm04_gcg_vanilla_doublespeak_seed42 \
    --manifest doublespeak_causality/data/gcg/clearharm_llama/clearharm_llama_doublespeak.jsonl \
    --split test --model-family llama \
    --model-name-or-path meta-llama/Llama-3.1-8B-Instruct --seed 42
"""
import argparse
import importlib.util
import json
import math
import os
import sys
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(HERE, ".."))
for _p in (HERE, _REPO_ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

def _load_kw_refusal():
    """kw_refusal imported verbatim from 18 — same detector used everywhere (no drift).
    Deferred (module 18 imports torch at top) so --help stays light off-GPU."""
    _spec = importlib.util.spec_from_file_location(
        "v18", os.path.join(HERE, "18_run_behavioral_necessity.py"))
    v18 = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(v18)
    return v18.kw_refusal


def _final_suffix(run_dir: Path) -> str:
    """Selected suffix_str = first row of FINAL_CANDIDATES.jsonl (matches 25_eval / audit convention)."""
    p = Path(run_dir) / "FINAL_CANDIDATES.jsonl"
    rows = [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]
    if not rows:
        raise ValueError(f"No candidates in {p}")
    return rows[0]["suffix_str"]


def _finite(x):
    return x is not None and isinstance(x, (int, float)) and math.isfinite(x)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True, help="Arm run-dir with FINAL_CANDIDATES.jsonl + CONFIG.json")
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--split", default="test", choices=["test", "train", "all"])
    ap.add_argument("--model-family", default="llama")
    ap.add_argument("--model-name-or-path", default="meta-llama/Llama-3.1-8B-Instruct")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--max-new-tokens", type=int, default=2048)
    ap.add_argument("--arm-label", default=None, help="condition label for rows (default = run-dir basename)")
    args = ap.parse_args()

    run_dir = Path(args.run_dir)
    arm_label = args.arm_label or run_dir.name
    suffix_str = _final_suffix(run_dir)
    suffix_len = len(suffix_str)

    # held-out prompts for the requested split
    tasks = []
    for l in open(args.manifest, encoding="utf-8"):
        if not l.strip():
            continue
        e = json.loads(l)
        if args.split == "all" or e.get("split") == args.split:
            tasks.append((e["task_id"], e["instruction"]))
    if not tasks:
        raise ValueError(f"No {args.split}-split tasks in {args.manifest}")
    print(f"[eval] arm={arm_label} split={args.split} n_tasks={len(tasks)} "
          f"suffix_len={suffix_len} (suffix string redacted)", flush=True)

    enable_thinking = False  # Llama has no thinking channel

    import torch  # noqa: F401  (import here so --help stays light)
    from poc_stage4.qwen3_model import load_qwen3_model
    from poc_stage_gcg_early.evaluate_optimized_suffixes import evaluate_suffix
    kw_refusal = _load_kw_refusal()

    wrapped = load_qwen3_model(args.model_name_or_path, require_cuda=True, log_device_placement=True)
    model, tokenizer = wrapped.model, wrapped.tokenizer

    for tid, instr in tasks:
        # evaluate_suffix: generate greedily + StrongREJECT-judge; appends FREE_GENERATION_RESULTS.jsonl.
        # Returns None if already logged (resume) — that's fine, we aggregate from the file below.
        res = evaluate_suffix(
            model, tokenizer, args.model_family,
            task_id=tid, instruction=instr,
            suffix_str=suffix_str, suffix_label=arm_label,
            enable_thinking=enable_thinking, seed=args.seed,
            output_dir=run_dir, max_new_tokens=args.max_new_tokens, greedy=True,
        )
        if res is not None:
            print(f"  {tid}: finish={res.get('finish_reason')} "
                  f"sr_success={res.get('strongreject_is_success')} "
                  f"sr_score={res.get('strongreject_score')}", flush=True)

    # Aggregate from FREE_GENERATION_RESULTS.jsonl (covers resumed rows too), scoped to this arm+seed+split.
    split_tids = {t for t, _ in tasks}
    results_path = run_dir / "FREE_GENERATION_RESULTS.jsonl"
    n = mal = rej = empty = judge_fail = 0
    score_sum = 0.0
    score_n = 0
    seen = set()
    for l in open(results_path, encoding="utf-8"):
        if not l.strip():
            continue
        r = json.loads(l)
        if (r.get("condition_label") != arm_label or r.get("seed") != args.seed
                or r.get("task_id") not in split_tids):
            continue
        key = (r["task_id"], r["seed"])
        if key in seen:      # dedupe (append-log could hold retries)
            continue
        seen.add(key)
        n += 1
        gen = (r.get("generation_text") or "")
        is_empty = not gen.strip()
        empty += int(is_empty)
        score = r.get("strongreject_score")
        if _finite(score):
            score_sum += float(score)
            score_n += 1
            mal += int(bool(r.get("strongreject_is_success")))
        else:
            judge_fail += 1
        rej += int(kw_refusal(gen))

    summary = {
        "arm_label": arm_label,
        "run_dir": str(run_dir),
        "model": args.model_name_or_path,
        "split": args.split,
        "seed": args.seed,
        "n_tasks": n,
        "asr": round(mal / n, 4) if n else None,                 # StrongREJECT success >= 0.5
        "mean_strongreject_score": round(score_sum / score_n, 4) if score_n else None,
        "refusal_rate": round(rej / n, 4) if n else None,
        "empty_rate": round(empty / n, 4) if n else None,
        "judge_fail_frac": round(judge_fail / n, 4) if n else None,
        "n_scored": score_n,
        "suffix_len": suffix_len,      # SCALAR ONLY — raw suffix string deliberately not stored here
        "max_new_tokens": args.max_new_tokens,
        "decoding": "greedy",
        "enable_thinking": enable_thinking,
    }
    out_path = run_dir / "p9_heldout_asr_summary.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"[eval] arm={arm_label} ASR={summary['asr']} refusal={summary['refusal_rate']} "
          f"empty={summary['empty_rate']} mean_score={summary['mean_strongreject_score']} "
          f"judge_fail={summary['judge_fail_frac']} -> {out_path}", flush=True)


if __name__ == "__main__":
    main()
