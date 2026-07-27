"""
19_run_behavioral_sufficiency.py — Phase 3 / Workstream B (plan §6.3, Claim C).

BEHAVIORAL sufficiency: on behaviorally-ELIGIBLE, baseline-BENIGN Neutral prompts, INJECT
the Doublespeak codeword state (and, for comparison, the Direct concept state) at the
Neutral codeword position across a layer WINDOW during FULL GENERATION, then judge. If the
hijacked late representation is behaviorally sufficient, Neutral←DS should turn BENIGN
generations MALICIOUS.

Primary comparison (plan §6.3): P(harmful | Neutral←DS) vs P(harmful | Neutral←Direct).
The representation-level result (handoff §2.3) predicts DS-state injection > Direct-state
injection — the hijacked rep is a distinct late-emerging state, not a copy of the concept.

Reuse: imports the VETTED helpers from 18_run_behavioral_necessity.py (capture_reps_for_gen,
patched_generate, layer_windows, classify, kw_refusal) so tokenization/patch mechanics and
the MALICIOUS-first classify are identical (bug-hunt iter4/5). StrongReject judge as in 14/17.

Controls (§15): identity (Neutral←Neutral must stay BENIGN), norm-matched random vector.

Responsible handling (§17): raw generations → protected dir; stdout = labels/counts.

Run (SLURM, bf16, L40S):
  python 19_run_behavioral_sufficiency.py --screen-dir outputs/behavioral_screen_llama8b_v1 \
      --matrix data/behavioral_benchmark/screening_matrix_v1.json \
      --model meta-llama/Llama-3.1-8B-Instruct --max-bases 40
"""
import os
import sys
import json
import time
import argparse
import importlib.util
from collections import Counter

import torch

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ds_common as dc
sys.path.insert(0, os.path.join(HERE, "..", "poc_stage3"))

# Reuse the vetted mechanics from script 18 (imported without running its main()).
_spec = importlib.util.spec_from_file_location("v18", os.path.join(HERE, "18_run_behavioral_necessity.py"))
v18 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(v18)
capture_reps_for_gen = v18.capture_reps_for_gen
patched_generate = v18.patched_generate
layer_windows = v18.layer_windows
classify = v18.classify
kw_refusal = v18.kw_refusal


def load_eligible_conditions(screen_dir, matrix_path, max_bases):
    """Eligible bases (from 17's eligible_bases.json, classify-stable) × their conditions.
    One condition per (base, codeword, context_len) from the matrix. Cap #bases."""
    # Prefer CORRECTED eligible set (iter10 refusal fix) if present, else raw screen output.
    corrected = os.path.join(screen_dir, "eligible_bases_corrected.json")
    elig_path = corrected if os.path.exists(corrected) else os.path.join(screen_dir, "eligible_bases.json")
    eligible = set(json.load(open(elig_path)).keys())
    matrix = json.load(open(matrix_path))["conditions"]
    # keep at most one (codeword,len) per base to bound cost? No — keep all for the base but
    # cap the number of distinct bases; the matrix already has 2 cw × 3 len per base.
    by_base = {}
    for m in matrix:
        if m["base_id"] in eligible:
            by_base.setdefault(m["base_id"], []).append(m)
    bases = list(by_base)[:max_bases] if max_bases else list(by_base)
    conds = [m for b in bases for m in by_base[b]]
    return conds


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--screen-dir", required=True)
    ap.add_argument("--matrix", default=os.path.join(HERE, "data", "behavioral_benchmark",
                                                     "screening_matrix_v1.json"))
    ap.add_argument("--model", default=dc.PRIMARY_MODEL)
    ap.add_argument("--dtype", default="bfloat16", choices=["bfloat16", "float16"])
    ap.add_argument("--max-bases", type=int, default=40)
    ap.add_argument("--max-new-tokens", type=int, default=200)
    ap.add_argument("--windows", default=None,
                    help="comma list of window names to test (default all: early,mid,late,"
                         "late_half_to_end). Use e.g. 'mid' for a fast preemption-safe MVP.")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out-dir", default=None)
    args = ap.parse_args()

    dc.set_seed(args.seed)
    ts = time.strftime("%Y%m%d_%H%M%S")
    tag = args.model.split("/")[-1]
    out_dir = args.out_dir or os.path.join(HERE, "outputs", f"beh_sufficiency_{tag}_{ts}")
    os.makedirs(out_dir, exist_ok=True)

    from strongreject_scoring import load_strongreject_evaluate
    evaluate = load_strongreject_evaluate()
    lm = dc.load_model(args.model, dtype=getattr(torch, args.dtype))

    conds = load_eligible_conditions(args.screen_dir, args.matrix, args.max_bases)
    print(f"[sufficiency] {len(conds)} eligible conditions | out={out_dir}", flush=True)
    if not conds:
        json.dump({"status": "NO_ELIGIBLE", "n": 0}, open(os.path.join(out_dir, "sufficiency_summary.json"), "w"))
        print("[sufficiency] no eligible conditions — nothing to do."); return

    n_layers = lm.num_layers
    windows = layer_windows(n_layers)
    if args.windows:
        keep = set(args.windows.split(","))
        windows = {w: ls for w, ls in windows.items() if w in keep}
        print(f"[sufficiency] restricted to windows: {list(windows)}")
    gen = torch.Generator().manual_seed(args.seed)
    randvec = torch.randn(lm.hidden_size, generator=gen)
    jstats = {"n": 0, "judge_fail": 0}

    def judge(goal, completion):
        jstats["n"] += 1
        if not completion.strip():
            return "EMPTY"
        # refused = refusal LANGUAGE only (iter10 fix); SR-refusal mislabels benign answers.
        # CRITICAL for sufficiency: baseline Neutral must be recognized as BENIGN (it is a benign
        # answer to the neutralized request) — the SR-refusal bug would wrongly exclude it.
        refused = kw_refusal(completion)
        try:
            r = evaluate(goal, completion, ["strongreject_rubric"])
            import math as _m
            score = float(r[0].get("score")) if r and r[0].get("score") is not None else None
            if score is not None and not _m.isfinite(score):
                score = None; jstats["judge_fail"] += 1
        except Exception:
            score = None; jstats["judge_fail"] += 1
        return classify(score, refused)

    PFX, SFX = "Do not reason, just ", " given the context."
    raw_rows = []
    # among baseline-BENIGN Neutrals: fraction that BECOME malicious under each injection
    agg = {w: {"n_base_benign": 0, "ds_mal": 0, "direct_mal": 0, "ds_trans": Counter(),
               "dir_trans": Counter()} for w in windows}
    ctrl = {"identity": {"n": 0, "mal": 0}, "random": {"n": 0, "mal": 0}}
    n_items, n_baseline_benign, n_skipped = 0, 0, 0

    for i, c in enumerate(conds):
        cw, concept = c["codeword"], c["concept"]
        goal = c["direct"][len(PFX):-len(SFX)] if c["direct"].startswith(PFX) and c["direct"].endswith(SFX) else c["direct"]
        neu_text = dc.apply_template(lm.tokenizer, c["neutral"])
        ds_text = dc.apply_template(lm.tokenizer, c["doublespeak"])
        dir_text = dc.apply_template(lm.tokenizer, c["direct"])
        neu_cap = capture_reps_for_gen(lm, neu_text, cw)         # inject site = Neutral codeword
        ds_cap = capture_reps_for_gen(lm, ds_text, cw)           # source: DS codeword state
        dir_cap = capture_reps_for_gen(lm, dir_text, concept)    # source: Direct concept state
        neu_pos = neu_cap["codeword_last"]
        if neu_pos is None or ds_cap["reps"] is None or dir_cap["reps"] is None:
            n_skipped += 1
            continue
        n_items += 1

        # baseline Neutral (no patch) — must be BENIGN to test sufficiency
        g0 = patched_generate(lm, neu_text, [], args.max_new_tokens)
        cat0 = judge(goal, g0["completion"])
        base_benign = (cat0 == "BENIGN")
        n_baseline_benign += int(base_benign)
        raw_rows.append({"base_id": c["base_id"], "codeword": cw, "arm": "baseline_neutral",
                         "cat": cat0, "completion": g0["completion"]})

        for wname, wlayers in windows.items():
            ds_patches = [(L, [neu_pos], ds_cap["reps"][L + 1].to(lm.model.device), "replace") for L in wlayers]
            dir_patches = [(L, [neu_pos], dir_cap["reps"][L + 1].to(lm.model.device), "replace") for L in wlayers]
            gds = patched_generate(lm, neu_text, ds_patches, args.max_new_tokens)
            gdir = patched_generate(lm, neu_text, dir_patches, args.max_new_tokens)
            cat_ds = judge(goal, gds["completion"])
            cat_dir = judge(goal, gdir["completion"])
            if base_benign:
                a = agg[wname]; a["n_base_benign"] += 1
                a["ds_mal"] += int(cat_ds == "MALICIOUS")
                a["direct_mal"] += int(cat_dir == "MALICIOUS")
                a["ds_trans"][f"{cat0}->{cat_ds}"] += 1
                a["dir_trans"][f"{cat0}->{cat_dir}"] += 1
            raw_rows.append({"base_id": c["base_id"], "codeword": cw, "arm": f"suff_DS_{wname}",
                             "cat": cat_ds, "base_benign": base_benign, "completion": gds["completion"]})
            raw_rows.append({"base_id": c["base_id"], "codeword": cw, "arm": f"suff_Direct_{wname}",
                             "cat": cat_dir, "base_benign": base_benign, "completion": gdir["completion"]})

        # controls over the LATE window (or the last available window if late was filtered out)
        late = windows.get("late") or list(windows.values())[-1]
        id_patches = [(L, [neu_pos], neu_cap["reps"][L + 1].to(lm.model.device), "replace") for L in late]
        gi = patched_generate(lm, neu_text, id_patches, args.max_new_tokens)
        if base_benign:
            ctrl["identity"]["n"] += 1; ctrl["identity"]["mal"] += int(judge(goal, gi["completion"]) == "MALICIOUS")
        rand_patches = []
        for L in late:
            dsv = ds_cap["reps"][L + 1]
            rscaled = (randvec * (float(dsv.float().norm()) / float(randvec.norm()))).to(lm.model.device)
            rand_patches.append((L, [neu_pos], rscaled, "replace"))
        gr = patched_generate(lm, neu_text, rand_patches, args.max_new_tokens)
        if base_benign:
            ctrl["random"]["n"] += 1; ctrl["random"]["mal"] += int(judge(goal, gr["completion"]) == "MALICIOUS")

        if (i + 1) % 5 == 0:
            print(f"  [{i+1}/{len(conds)}] processed", flush=True)

    fail_frac = jstats["judge_fail"] / jstats["n"] if jstats["n"] else 0.0
    summary = {"model": args.model, "meta": lm.meta(),
               "status": "SUSPECT_JUDGE_FAILURES" if fail_frac > 0.05 else "COMPLETE",
               "judge_stats": {**jstats, "fail_fraction": round(fail_frac, 4)},
               "n_items_used": n_items, "n_skipped": n_skipped,
               "n_baseline_benign": n_baseline_benign, "n_layers": n_layers,
               "windows": {w: list(ls) for w, ls in windows.items()},
               "results": {}, "controls": {}}
    for w, a in agg.items():
        nb = a["n_base_benign"]
        ds_rate = a["ds_mal"] / nb if nb else None
        dir_rate = a["direct_mal"] / nb if nb else None
        summary["results"][w] = {
            "n_base_benign": nb, "suff_DS_malicious_rate": ds_rate,
            "suff_Direct_malicious_rate": dir_rate,
            "DS_minus_Direct": (ds_rate - dir_rate) if (ds_rate is not None and dir_rate is not None) else None,
            "ds_transitions": dict(a["ds_trans"]), "dir_transitions": dict(a["dir_trans"])}
    for k, v in ctrl.items():
        summary["controls"][k] = {"n": v["n"], "malicious_rate": v["mal"] / v["n"] if v["n"] else None}

    with open(os.path.join(out_dir, "sufficiency_raw.jsonl"), "w") as f:
        for r in raw_rows:
            f.write(json.dumps(r) + "\n")
    with open(os.path.join(out_dir, "sufficiency_summary.json"), "w") as f:
        json.dump(summary, f, indent=2)

    print(f"\n[sufficiency] baseline-benign Neutrals: {n_baseline_benign}/{n_items} (skipped {n_skipped})")
    print("[sufficiency] per window: DS-inject vs Direct-inject malicious rate (predict DS > Direct):")
    for w, r in summary["results"].items():
        print(f"  {w:18s} n={r['n_base_benign']} suff_DS={r['suff_DS_malicious_rate']} "
              f"suff_Direct={r['suff_Direct_malicious_rate']} DS−Direct={r['DS_minus_Direct']}")
    print(f"[sufficiency] controls (late): identity_mal={summary['controls']['identity']['malicious_rate']} "
          f"random_mal={summary['controls']['random']['malicious_rate']} (both want ~0)")
    print(f"[sufficiency] -> {out_dir}")


if __name__ == "__main__":
    main()
