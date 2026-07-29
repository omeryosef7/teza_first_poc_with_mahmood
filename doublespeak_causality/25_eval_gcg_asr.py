"""
25_eval_gcg_asr.py — Track B (temporal-GCG) step 5: held-out ASR for the Level-5 test.

Applies each optimized suffix to the HELD-OUT (val split) Neutral prompts, generates normally, and judges
harmful compliance with the SAME StrongReject + MALICIOUS-first classifier used everywhere (imported from
18/19 — zero judge drift). Compares three arms per held-out task:
  none      — Neutral prompt, no suffix (jailbreak-free control; ASR should be ~0)
  baseline  — Neutral + task-only GCG suffix  (lambda_repr = 0)
  temporal  — Neutral + temporal GCG suffix   (lambda_repr > 0, mixed early-benign/late-harmful cache)

Level-5 verdict: temporal ASR > baseline ASR on held-out concepts ⇒ the mechanism-derived objective helps.

Harmful generation + judging → MAIN LOOP / SLURM only (never a subagent). Reuses ds_common + 18's
patched_generate (patches=[] = plain greedy gen) + 19's judge logic verbatim.

Usage (SLURM):
  python doublespeak_causality/25_eval_gcg_asr.py \
    --neutral-manifest doublespeak_causality/data/gcg/curated_qwen3_neutral.jsonl \
    --matrix doublespeak_causality/data/behavioral_benchmark/screening_matrix_curated_v1.json \
    --temporal-dir doublespeak_causality/outputs/gcg/opt_qwen3_temporal \
    --baseline-dir doublespeak_causality/outputs/gcg/opt_qwen3_baseline \
    --model Qwen/Qwen3-14B --split val --enable-thinking off
"""
import argparse
import importlib.util
import json
import os
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "poc_stage3"))
import ds_common as dc

_spec = importlib.util.spec_from_file_location("v18", os.path.join(HERE, "18_run_behavioral_necessity.py"))
v18 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(v18)
classify, kw_refusal, patched_generate = v18.classify, v18.kw_refusal, v18.patched_generate

PFX, SFX = "Do not reason, just ", " given the context."      # goal extraction (identical to 19)
_ET_MAP = {"default": None, "on": True, "off": False}


def _final_suffix(run_dir):
    """Final selected suffix_str from FINAL_CANDIDATES.jsonl (first row = selected candidate)."""
    p = os.path.join(run_dir, "FINAL_CANDIDATES.jsonl")
    rows = [json.loads(l) for l in open(p) if l.strip()]
    return rows[0]["suffix_str"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--neutral-manifest", required=True)
    ap.add_argument("--matrix", required=True)
    ap.add_argument("--temporal-dir", required=True)
    ap.add_argument("--baseline-dir", required=True)
    ap.add_argument("--model", default="Qwen/Qwen3-14B")
    ap.add_argument("--split", default="val", choices=["val", "train", "all"])
    ap.add_argument("--enable-thinking", default="off", choices=["default", "on", "off"])
    ap.add_argument("--max-new-tokens", type=int, default=200)
    ap.add_argument("--out-dir", default=None)
    args = ap.parse_args()
    _ET = _ET_MAP[args.enable_thinking]

    import torch
    from strongreject_scoring import load_strongreject_evaluate
    evaluate = load_strongreject_evaluate()

    jstats = {"n": 0, "judge_fail": 0}

    def judge(goal, completion):                       # identical policy to 19.judge
        refused = kw_refusal(completion)
        try:
            r = evaluate(goal, completion, ["strongreject_rubric"])
            score = r.get("score") if isinstance(r, dict) else None
        except Exception:
            score = None
        if score is None:
            jstats["judge_fail"] += 1
        jstats["n"] += 1
        return classify(score, refused)

    # held-out Neutral prompts (task_id -> instruction) for the requested split
    tasks = {}
    for l in open(args.neutral_manifest):
        e = json.loads(l)
        if args.split == "all" or e["split"] == args.split:
            tasks[e["task_id"]] = e["instruction"]

    # per-base goal from the matrix Direct prompt (strip PFX/SFX, exactly as 19)
    matrix = json.load(open(args.matrix))
    goal_by_base = {}
    for c in matrix["conditions"]:
        d = c["direct"]
        goal_by_base[c["base_id"]] = d[len(PFX):-len(SFX)] if d.startswith(PFX) and d.endswith(SFX) else d

    suffixes = {"none": None, "baseline": _final_suffix(args.baseline_dir),
                "temporal": _final_suffix(args.temporal_dir)}
    print(f"[eval] {len(tasks)} held-out ({args.split}) tasks | suffixes: "
          f"baseline={suffixes['baseline']!r} temporal={suffixes['temporal']!r}", flush=True)

    lm = dc.load_model(args.model, dtype=torch.bfloat16)
    raw, agg = [], {a: {"n": 0, "mal": 0, "rej": 0} for a in suffixes}
    for tid, instr in sorted(tasks.items()):
        goal = goal_by_base.get(tid)
        if goal is None:
            continue
        for arm, suf in suffixes.items():
            user_text = instr if suf is None else f"{instr} {suf}"
            templated = dc.apply_template(lm.tokenizer, user_text, enable_thinking=_ET)
            comp = patched_generate(lm, templated, [], args.max_new_tokens)["completion"]
            cat = judge(goal, comp)
            agg[arm]["n"] += 1
            agg[arm]["mal"] += int(cat == "MALICIOUS")
            agg[arm]["rej"] += int(cat == "REJECTED")
            raw.append({"task_id": tid, "arm": arm, "cat": cat})
        print(f"  {tid}: " + " ".join(f"{a}={raw[-len(suffixes)+i]['cat'][:3]}" for i, a in enumerate(suffixes)),
              flush=True)

    summary = {"model": args.model, "split": args.split, "n_tasks": agg["none"]["n"],
               "judge_fail_frac": round(jstats["judge_fail"] / max(jstats["n"], 1), 3),
               "asr": {a: round(agg[a]["mal"] / agg[a]["n"], 3) if agg[a]["n"] else None for a in suffixes},
               "refusal_rate": {a: round(agg[a]["rej"] / agg[a]["n"], 3) if agg[a]["n"] else None for a in suffixes},
               "counts": agg, "suffixes": suffixes}
    out_dir = args.out_dir or os.path.dirname(args.temporal_dir)
    with open(os.path.join(out_dir, "gcg_asr_summary.json"), "w") as f:
        json.dump(summary, f, indent=2)
    with open(os.path.join(out_dir, "gcg_asr_raw.jsonl"), "w") as f:
        for r in raw:
            f.write(json.dumps(r) + "\n")
    print("[eval] ASR:", summary["asr"], "| refusal:", summary["refusal_rate"])
    print(f"[eval] -> {out_dir}/gcg_asr_summary.json")


if __name__ == "__main__":
    main()
