#!/usr/bin/env python3
"""
Staged ASR-rerank for the per-behavior Native-CoT pilot
(docs/GCG_PERBEHAVIOR_NATIVECOT_PLAN.md).

For each behavior: collect candidates from ALL its optimization runs (styles×seeds)
— final, best-loss, Pareto, periodic checkpoints — then select the best candidate by
REAL StrongREJECT ASR via a staged eval:
  Stage 1: 1 generation/candidate  -> rank
  Stage 2: top-M candidates, K more seeds
  Stage 3: top-2, N seeds -> per-behavior best-candidate ASR
Controls (neutral " ", random_spaces 16 spaces) evaluated at the same N seeds.

Reuses evaluate_optimized_suffixes.evaluate_suffix (1 gen + StrongREJECT; resumable
by row_key). Loads Qwen3-14B once. NON-GPU-optional: generation needs the model;
StrongREJECT needs OPENAI_API_KEY.

Usage: python scripts/staged_asr_rerank.py [--behaviors advbench_001,advbench_002] [--M 5 --K 3 --N 10]
"""
from __future__ import annotations
import argparse, json, sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
OUT = ROOT / "outputs" / "stage_gcg_percot_v2"
RUNS = OUT / "runs"
MANI = OUT / "manifests"
MODEL = "Qwen/Qwen3-14B"


# ---------- candidate extraction (subagent A) ----------
def extract_run_candidates(run_dir: Path, top_pareto=6, ckpt_stride=100):
    fc = run_dir / "FINAL_CANDIDATES.jsonl"
    il = run_dir / "ITERATION_LOG.jsonl"
    if not fc.exists() or not il.exists():
        return []
    iters = [json.loads(l) for l in open(il) if l.strip()]
    final_lines = [json.loads(l) for l in open(fc) if l.strip()]
    if not iters or not final_lines:
        return []
    cands = []
    f = final_lines[0]
    cands.append(dict(suffix_str=f["suffix_str"], origin="final", task_loss=iters[-1]["task_loss"], step=iters[-1]["step"]))
    b = min(iters, key=lambda r: r["task_loss"])
    cands.append(dict(suffix_str=b["suffix_str"], origin="best-loss", task_loss=b["task_loss"], step=b["step"]))
    for p in sorted(final_lines[1:], key=lambda r: r.get("task_loss", 9e9))[:top_pareto]:
        cands.append(dict(suffix_str=p["suffix_str"], origin=f"pareto@{p.get('step')}", task_loss=p.get("task_loss"), step=p.get("step")))
    by_step = {r["step"]: r for r in iters}
    for step in sorted(by_step):
        if (step + 1) % ckpt_stride == 0:
            r = by_step[step]
            cands.append(dict(suffix_str=r["suffix_str"], origin=f"step-{step}", task_loss=r["task_loss"], step=step))
    return cands


def collect_per_behavior(run_dirs, cap=20):
    seen = {}
    for rd in run_dirs:
        for c in extract_run_candidates(rd):
            k = c["suffix_str"]
            if k not in seen or (c["task_loss"] or 9e9) < (seen[k]["task_loss"] or 9e9):
                seen[k] = c
    return sorted(seen.values(), key=lambda c: (c["task_loss"] if c["task_loss"] is not None else 9e9))[:cap]


# ---------- staged eval ----------
def _read_row(eval_dir: Path, task_id, label, seed):
    f = eval_dir / "FREE_GENERATION_RESULTS.jsonl"
    rk = f"{task_id}|{label}|{seed}"
    if f.exists():
        for l in open(f):
            if l.strip() and json.loads(l).get("row_key") == rk:
                return json.loads(l)
    return {}


def make_scorer(model, tokenizer, evaluate_suffix, eval_dir, task_id, instruction, mnt=2048):
    def _score(suffix, label, seed):
        r = evaluate_suffix(model, tokenizer, "qwen3", task_id, instruction, suffix, label,
                            True, seed, eval_dir, mnt)
        if r is None:
            r = _read_row(eval_dir, task_id, label, seed)
        return (r.get("strongreject_score") or 0.0), bool(r.get("strongreject_is_success"))
    return _score


def staged_behavior(model, tokenizer, evaluate_suffix, task_id, instruction, candidates,
                    M=5, K=3, N=10):
    eval_dir = OUT / "eval" / task_id
    eval_dir.mkdir(parents=True, exist_ok=True)
    score = make_scorer(model, tokenizer, evaluate_suffix, eval_dir, task_id, instruction)
    N_seeds = list(range(N))
    # Stage 1: 1 gen (seed 0) per candidate
    s1 = {i: score(c["suffix_str"], f"cand{i}", 0)[0] for i, c in enumerate(candidates)}
    topM = sorted(s1, key=s1.get, reverse=True)[:M]
    # Stage 2: seeds 1..K for topM
    s2 = {}
    for i in topM:
        vals = [s1[i]] + [score(candidates[i]["suffix_str"], f"cand{i}", sd)[0] for sd in range(1, K + 1)]
        s2[i] = sum(vals) / len(vals)
    top2 = sorted(s2, key=s2.get, reverse=True)[:2]

    def asr_over_N(suffix, label):
        succ = [score(suffix, label, sd)[1] for sd in N_seeds]
        return sum(succ) / len(succ)

    per_top = {i: asr_over_N(candidates[i]["suffix_str"], f"cand{i}") for i in top2}
    best_i = max(per_top, key=per_top.get)
    neutral_asr = asr_over_N(" ", "neutral_control")
    random_asr = asr_over_N(" " * 16, "random_spaces")
    return {
        "task_id": task_id,
        "n_candidates": len(candidates),
        "best_candidate_origin": candidates[best_i]["origin"],
        "best_candidate_suffix": candidates[best_i]["suffix_str"],
        "best_asr": per_top[best_i],
        "top2_asr": {int(i): per_top[i] for i in top2},
        "neutral_asr": neutral_asr,
        "random_asr": random_asr,
        "uplift_over_neutral": per_top[best_i] - neutral_asr,
        "stage1_top": {int(i): s1[i] for i in topM},
    }


def behavior_instruction(task_id):
    m = MANI / f"{task_id}__a_affirm.jsonl"
    return json.loads(open(m).readline())["instruction"] if m.exists() else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--behaviors", default=None, help="comma list of task_ids; default=auto-discover")
    ap.add_argument("--M", type=int, default=5); ap.add_argument("--K", type=int, default=3)
    ap.add_argument("--N", type=int, default=10)
    args = ap.parse_args()

    # discover behaviors -> their run dirs (only runs with FINAL_CANDIDATES)
    beh_runs = defaultdict(list)
    for rd in sorted(RUNS.glob("*/")):
        if not (rd / "FINAL_CANDIDATES.jsonl").exists():
            continue
        tid = rd.name.split("__")[0]
        beh_runs[tid].append(rd)
    behaviors = args.behaviors.split(",") if args.behaviors else sorted(beh_runs)
    print(f"[rerank] behaviors with completed runs: {[b for b in behaviors if b in beh_runs]}")

    from poc_stage4.qwen3_model import load_qwen3_model
    from poc_stage_gcg_early.evaluate_optimized_suffixes import evaluate_suffix
    wrapped = load_qwen3_model(MODEL, require_cuda=True, log_device_placement=True, device_map="auto")
    model, tok = wrapped.model, wrapped.tokenizer

    results_path = OUT / "PERBEHAVIOR_ASR_RESULTS.jsonl"
    with open(results_path, "a") as fout:
        for tid in behaviors:
            if tid not in beh_runs:
                continue
            instr = behavior_instruction(tid)
            cands = collect_per_behavior(beh_runs[tid])
            if not cands:
                print(f"[rerank] {tid}: no candidates"); continue
            res = staged_behavior(model, tok, evaluate_suffix, tid, instr, cands, args.M, args.K, args.N)
            fout.write(json.dumps(res) + "\n"); fout.flush()
            print(f"[rerank] {tid}: best_asr={res['best_asr']:.2f} (origin={res['best_candidate_origin']}) "
                  f"neutral={res['neutral_asr']:.2f} random={res['random_asr']:.2f} uplift={res['uplift_over_neutral']:+.2f}")
    print(f"[rerank] wrote {results_path}")


if __name__ == "__main__":
    main()
