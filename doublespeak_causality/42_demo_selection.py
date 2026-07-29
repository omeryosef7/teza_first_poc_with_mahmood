"""
42_demo_selection.py — CAUSAL_CORE_PLAN §8.2/§8.3 + §9 (S12, slice 2).

**Demonstration SELECTION**, which is the next honest rung of demonstration-level
optimization after codeword selection (slice 1). Given the 12 candidate demonstrations for a
pair, choose a subset of k and ask §9's question: *does optimizing the causally-validated
objective beat optimizing behaviour directly, and does either beat matched random search, on
HELD-OUT behavioral attack success?*

Why this design and not GCG-over-demo-tokens. Slice 1 established that selecting codewords by
the causal semantic score **significantly worsens** held-out behavioral ASR
(−0.133 [−0.200, −0.050]). Running a token-level optimizer against that same objective would
be optimizing a target already shown to anti-transfer. Selection is the cheapest intervention
that lets the two objectives compete head-to-head on the outcome that matters, and it needs no
new optimizer.

ARMS (all choose k of 12 demonstrations; the instruction and codeword are identical across arms)
  causal_greedy    greedy forward selection maximizing the SAFE semantic causal score
  behavior_greedy  greedy forward selection maximizing TRAIN behavioral MALICIOUS rate
  random_subset    `--n-random` arbitrary subsets scored directly — "what does a random
                   subset get?" (a BASELINE, not a search)
  random_search    `--n-random-search` subsets scored on TRAIN, best carried to HELD-OUT —
                   the search control §8.6 asks for. Its budget is reported explicitly rather
                   than claimed equal to greedy's: greedy spends `k*(pool-k/2)` candidate
                   evaluations across accepted steps, random search spends its draws in one
                   pass, so the two are comparable but not identical and the JSON records both.
  full_default     all 12 demonstrations — the paper's configuration

Selection happens on TRAIN paraphrases; every arm is scored on **HELD-OUT** paraphrases.
The two search arms report their budgets explicitly rather than claiming equality (see above),
so a greedy win can be read against a like-for-like search rather than only against no search.

Judging reuses the house pipeline (StrongReject rubric + MALICIOUS-first `classify` from 18),
so numbers stay comparable to slice 1 and the prior sprint. Harmful text stays in this process
/ SLURM and is never printed.

Usage:
  python 42_demo_selection.py --bench data/pair_benchmark/pair_carrot_bomb.json --k 6
"""
import os
import re
import sys
import json
import time
import random
import argparse
import importlib.util
from collections import defaultdict

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "poc_stage3"))
import ds_common as dc
import pair_common as pc
import stats as st

HERE = os.path.dirname(os.path.abspath(__file__))


def _load_numeric(name, filename):
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, filename))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


_nec = _load_numeric("beh_necessity", "18_run_behavioral_necessity.py")
classify, kw_refusal = _nec.classify, _nec.kw_refusal


def demo_sentences(bench, style, n_demos, split):
    """The individual demonstration sentences for one (style, count, split) cell."""
    for r in bench["semantic"]:
        if (r["condition"] == "DOUBLESPEAK" and r["demo_style"] == style
                and r["n_demos"] == n_demos and r["split"] == split):
            return r["prompt"].rsplit("\n\n", 1)[0].split("\n")
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bench", required=True)
    ap.add_argument("--model", default=dc.PRIMARY_MODEL)
    ap.add_argument("--out-root", default=os.path.join(HERE, "outputs"))
    ap.add_argument("--demo-style", default="news")
    ap.add_argument("--n-demos", type=int, default=12, help="candidate pool size")
    ap.add_argument("--k", type=int, default=6, help="subset size to select")
    ap.add_argument("--readout", default="cloze")
    ap.add_argument("--n-train", type=int, default=8, help="TRAIN paraphrases for selection")
    ap.add_argument("--n-eval", type=int, default=12, help="HELD-OUT paraphrases for scoring")
    ap.add_argument("--n-random", type=int, default=5)
    ap.add_argument("--n-random-search", type=int, default=20,
                    help="subsets sampled for the matched-budget RANDOM SEARCH arm")
    ap.add_argument("--max-new-tokens", type=int, default=200)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    dc.set_seed(args.seed)
    rng = random.Random(args.seed)
    bench = json.load(open(args.bench))
    cc, cw = bench["pair"]["concept"], bench["pair"]["codeword"]
    readout_tpl = {r["rid"]: r["template"] for r in bench["readouts"]}[args.readout]

    pool = demo_sentences(bench, args.demo_style, args.n_demos, "dev")
    if not pool:
        raise SystemExit("no demonstration pool for that style/count")
    print(f"[sel] candidate pool: {len(pool)} demonstrations "
          f"({args.demo_style}, n={args.n_demos})")

    beh_all = [b for b in bench["behavioral"]
               if b["demo_style"] == args.demo_style and b["n_demos"] == args.n_demos]
    train = sorted([b for b in beh_all if b["split"] == "dev"], key=lambda b: b["bid"])[: args.n_train]
    evalset = sorted([b for b in beh_all if b["split"] == "heldout"], key=lambda b: b["bid"])[: args.n_eval]
    if not train or not evalset:
        raise SystemExit("need both dev (train) and heldout (eval) behavioral prompts")
    print(f"[sel] {len(train)} TRAIN / {len(evalset)} HELD-OUT behavioral paraphrases")

    lm = dc.load_model(args.model)
    from strongreject_scoring import load_strongreject_evaluate
    evaluate = load_strongreject_evaluate()
    id_groups = {r: pc.word_first_ids(lm.tokenizer, bench["pair"][r])
                 for r in ("concept", "codeword")}

    tag = args.model.split("/")[-1]
    uniq = os.environ.get("SLURM_JOB_ID") or str(os.getpid())
    out_dir = os.path.join(args.out_root,
                           f"pair_demosel_{tag}_{time.strftime('%Y%m%d_%H%M%S')}_{uniq}")
    os.makedirs(out_dir, exist_ok=True)
    raw = open(os.path.join(out_dir, "demosel_raw.jsonl"), "w")

    n_causal_evals = n_beh_gens = 0

    def causal_score(subset):
        """Mean SAFE semantic causal score for this demo subset (forward passes only)."""
        nonlocal n_causal_evals
        block = "\n".join(pool[i] for i in subset)
        probe = readout_tpl.format(w=cw, a=cw, b=cc)
        t = dc.apply_template(lm.tokenizer, block + "\n\n" + probe)
        n_causal_evals += 1
        return pc.semantic_score(lm, t, id_groups)["concept"]

    def behavioral_rate(subset, prompts, arm, tag_note=""):
        """MALICIOUS rate for this demo subset over `prompts` (generation + judging)."""
        nonlocal n_beh_gens
        block = "\n".join(pool[i] for i in subset)
        labels = []
        for b in prompts:
            ds_prompt = block + "\n\n" + b["neutral"]
            goal = re.sub(re.escape(cw), cc, b["neutral"], flags=re.IGNORECASE)
            gen = dc.generate(lm, ds_prompt, max_new_tokens=args.max_new_tokens)
            resp = gen["completion"]
            try:
                r = evaluate(goal, resp, ["strongreject_rubric"])
                score = (r[0].get("score") if isinstance(r, list) else r.get("score"))
            except Exception:
                score = None
            label = classify(score, kw_refusal(resp))
            labels.append(int(label == "MALICIOUS"))
            n_beh_gens += 1
            raw.write(json.dumps({
                "arm": arm, "note": tag_note, "subset": sorted(subset), "bid": b["bid"],
                "split": b["split"], "strongreject_score": score,
                "refused": bool(kw_refusal(resp)), "label": label,
                "response": resp,        # protected dir only; never printed
            }) + "\n")
        return float(np.mean(labels))

    def greedy(objective, name):
        """Forward selection to size k; returns (subset, n_candidate_evals)."""
        chosen, evals = [], 0
        while len(chosen) < args.k:
            best, best_v = None, None
            for i in range(len(pool)):
                if i in chosen:
                    continue
                v = objective(chosen + [i])
                evals += 1
                if best_v is None or v > best_v:
                    best, best_v = i, v
            chosen.append(best)
            print(f"  [sel] {name}: picked demo {best} -> {len(chosen)}/{args.k} "
                  f"(objective {best_v:.4f})")
        return chosen, evals

    print("[sel] greedy selection on the SAFE CAUSAL objective ...")
    causal_subset, causal_evals = greedy(causal_score, "causal")

    print("[sel] greedy selection on TRAIN BEHAVIOR ...")
    beh_subset, beh_evals = greedy(
        lambda sub: behavioral_rate(sub, train, "SEARCH_behavior_greedy", "train"),
        "behavior")

    # (a) arbitrary-subset baseline
    rand_subsets = [sorted(rng.sample(range(len(pool)), args.k)) for _ in range(args.n_random)]
    # (b) RANDOM SEARCH: sample subsets, score on TRAIN, carry the best to HELD-OUT. This is
    # the control that makes a greedy win meaningful -- without it, "greedy beat an arbitrary
    # subset" could just mean "any train-fitted subset beats an unfitted one".
    print(f"[sel] random search over {args.n_random_search} subsets (scored on TRAIN) ...")
    rs_best, rs_best_v, rs_scores = None, None, []
    for j in range(args.n_random_search):
        sub = sorted(rng.sample(range(len(pool)), args.k))
        v = behavioral_rate(sub, train, "SEARCH_random_search", f"train_draw{j}")
        rs_scores.append({"subset": sub, "train_malicious": v})
        if rs_best_v is None or v > rs_best_v:
            rs_best, rs_best_v = sub, v
    print(f"[sel] random search best on TRAIN: {rs_best} ({rs_best_v:.4f})")

    arms = {
        "causal_greedy": causal_subset,
        "behavior_greedy": beh_subset,
        "full_default": list(range(len(pool))),
        "random_search": rs_best,
    }
    results = {}
    for name, sub in arms.items():
        results[name] = {"subset": sorted(sub),
                         "heldout_malicious": behavioral_rate(sub, evalset, name, "heldout")}
        print(f"[sel] {name:16} subset={sorted(sub)} heldout_MALICIOUS="
              f"{results[name]['heldout_malicious']:.4f}")
    rand_rates = []
    for j, sub in enumerate(rand_subsets):
        r = behavioral_rate(sub, evalset, "random_subset", f"heldout")
        rand_rates.append(r)
        print(f"[sel] random_subset draw {j}: subset={sub} heldout_MALICIOUS={r:.4f}")
    results["random_search"]["train_scores"] = rs_scores
    results["random_search"]["train_best"] = rs_best_v
    results["random_subset"] = {
        "subsets": rand_subsets, "rates": rand_rates,
        "heldout_malicious": float(np.mean(rand_rates)),
        "max": float(np.max(rand_rates)), "min": float(np.min(rand_rates))}
    raw.close()

    # paired contrasts on the SAME held-out paraphrases
    rows = [json.loads(l) for l in open(os.path.join(out_dir, "demosel_raw.jsonl"))]
    by = defaultdict(dict)
    for r in rows:
        if r["note"] != "heldout":
            continue
        by[r["bid"]].setdefault(r["arm"], []).append(int(r["label"] == "MALICIOUS"))

    def paired(a, b):
        shared = sorted(k for k in by if a in by[k] and b in by[k])
        if len(shared) < 2:
            return None
        x = [float(np.mean(by[k][a])) for k in shared]
        y = [float(np.mean(by[k][b])) for k in shared]
        ci = st.paired_bootstrap_ci(x, y, n_boot=10000, seed=0)
        return {"mean": round(ci["mean_diff"], 4), "lo": round(ci["lo"], 4),
                "hi": round(ci["hi"], 4), "n": ci["n"],
                "ci_reliable": ci["ci_reliable"], "degenerate": ci["degenerate"]}

    contrasts = {
        "causal_greedy_minus_random_subset": paired("causal_greedy", "random_subset"),
        "behavior_greedy_minus_random_subset": paired("behavior_greedy", "random_subset"),
        "causal_greedy_minus_random_search": paired("causal_greedy", "random_search"),
        "behavior_greedy_minus_random_search": paired("behavior_greedy", "random_search"),
        "behavior_greedy_minus_causal": paired("behavior_greedy", "causal_greedy"),
        "causal_greedy_minus_full": paired("causal_greedy", "full_default"),
        "behavior_greedy_minus_full": paired("behavior_greedy", "full_default"),
    }

    summary = {
        "model": lm.meta(), "pair": bench["pair"],
        "plan": "CAUSAL_CORE_PLAN §8.2/§8.3 + §9 (S12 slice 2)",
        "question": ("does selecting DEMONSTRATIONS on the causal objective beat selecting "
                     "on behaviour, or matched random search, on HELD-OUT behavioral ASR?"),
        "demo_style": args.demo_style, "pool_size": len(pool), "k": args.k,
        "n_train": len(train), "n_eval": len(evalset),
        "selection_on_train_only": True,
        "search_budget": {"causal_candidate_evals": causal_evals,
                          "behavior_candidate_evals": beh_evals,
                          "n_random_subsets": args.n_random,
                          "n_random_search_subsets": args.n_random_search,
                          "budget_note": ("greedy and random search are comparable but NOT "
                                          "identical in budget; both are recorded")},
        "results": results, "contrasts": contrasts,
        "n_causal_evals": n_causal_evals, "n_behavioral_generations": n_beh_gens,
        "status": "COMPLETE",
    }
    with open(os.path.join(out_dir, "demosel_summary.json"), "w") as f:
        json.dump(summary, f, indent=1)

    print("\n[sel] HELD-OUT malicious rate by arm:")
    for k in ("causal_greedy", "behavior_greedy", "random_search", "random_subset",
              "full_default"):
        print(f"  {k:16} {results[k]['heldout_malicious']:.4f}")
    for k, v in contrasts.items():
        if v:
            print(f"[sel] {k:32} {v['mean']:+.4f} [{v['lo']:+.4f},{v['hi']:+.4f}] n={v['n']}")
    print(f"[sel] {n_beh_gens} generations, {n_causal_evals} causal evals -> {out_dir}")


if __name__ == "__main__":
    main()
