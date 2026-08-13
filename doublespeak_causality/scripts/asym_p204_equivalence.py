#!/usr/bin/env python
"""
ASYMMETRY SPRINT §20.4 — retrospective equivalence bounds on the sprint's negatives.

A null result ("0/3 seeds significant") is not a claim. This converts each paired-binary
negative into a BOUNDED claim: the equivalence margin delta such that effects larger than
delta are rejected at alpha=0.05.

Method. For paired binary outcomes the TOST rejection region at alpha=0.05 is exactly the
90% CI on the paired difference (Schuirmann). We take the percentile bootstrap over
PAIRED items (resample task_ids, not arms -- the pairing is the design), matching the
bootstrap already used elsewhere in the sprint (§3). The reported bound is
    delta = max(|CI_lo|, |CI_hi|)
i.e. "effects larger than delta in either direction are ruled out; smaller ones are not".

Per plan §20.4 this is the FIRST of two passes and is explicitly NOT for publication --
§20.6 must first supply a real multi-direction SD so the margins can be expressed in
units of the natural spread rather than raw ASR. Output is written with
"provisional": true so it cannot be mistaken for the publishable pass.

Reads only scalar per-row fields via the aggregator's collect(); never model text.
"""
import argparse, json, sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from aggregate_perprompt_asr import collect, _load_kw_refusal  # noqa: E402

JOBDIR = Path("doublespeak_causality/data/gcg/clearharm_llama_v3/perprompt_test")

# The `seed` field on an eval row is the GENERATION seed, which was 42 for every arm.
# The GCG optimization seed is carried only by the joblist / output_dir. Filtering rows
# by the optimization seed silently yields zero rows for seeds 43/44.
EVAL_SEED = 42


def arm_vector(arm: str, seed: int, budget: str, kw):
    """-> dict task_id -> success(bool). `seed` selects the joblist (optimization seed)."""
    tag = f"_{budget}" if budget else ""
    jl = JOBDIR / f"joblist_asym_p75_{arm}{tag}_seed{seed}.jsonl"
    if not jl.exists():
        return None, f"missing joblist {jl.name}"
    label = f"asym_p75_{arm}{tag}"      # eval-time condition_label carries no seed suffix
    out = {}
    for line in open(jl, encoding="utf-8"):
        if not line.strip():
            continue
        job = json.loads(line)
        # own-prompt outcome only, exactly as aggregate_perprompt_asr does
        for r in collect(job["output_dir"], label, EVAL_SEED, kw):
            if r["task_id"] == job["task_id"] and r["success"] is not None:
                out[r["task_id"]] = bool(r["success"])
    return out, None


def tost(pairs, n_boot=20000, rng_seed=0):
    """pairs: array of per-item (a - b) in {-1,0,+1}. -> point, ci90, bound."""
    d = np.asarray(pairs, dtype=float)
    n = len(d)
    rng = np.random.default_rng(rng_seed)
    idx = rng.integers(0, n, size=(n_boot, n))
    boots = d[idx].mean(axis=1)
    lo, hi = np.percentile(boots, [5.0, 95.0])
    return float(d.mean()), (float(lo), float(hi)), float(max(abs(lo), abs(hi))), n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="doublespeak_causality/outputs/asym_p204_equivalence.json")
    ap.add_argument("--n-boot", type=int, default=20000)
    args = ap.parse_args()

    kw = _load_kw_refusal()
    CONTRASTS = [("mechanism", "matched_random"), ("mechanism", "vanilla"),
                 ("matched_random", "vanilla")]
    results, notes = [], []

    for budget, blab in (("s5", "low (5 steps)"), ("", "full")):
        for a_arm, b_arm in CONTRASTS:
            per_seed = []
            for seed in (42, 43, 44):
                A, ea = arm_vector(a_arm, seed, budget, kw)
                B, eb = arm_vector(b_arm, seed, budget, kw)
                if A is None or B is None:
                    notes.append(f"{blab} {a_arm}-{b_arm} seed{seed}: {ea or eb}")
                    continue
                shared = sorted(set(A) & set(B))
                if len(shared) < 20:      # standing rule: >=20 paired items per experiment
                    notes.append(f"{blab} {a_arm}-{b_arm} seed{seed}: only {len(shared)} paired")
                    continue
                d = [float(A[t]) - float(B[t]) for t in shared]
                pt, ci, bound, n = tost(d, args.n_boot, rng_seed=seed)
                per_seed.append({"seed": seed, "n_paired": n, "delta_asr": pt,
                                 "ci90": ci, "equiv_bound": bound,
                                 "n_dropped_unpaired": len(set(A) ^ set(B)),
                                 # cross-check handles against the §7.5 published table
                                 "asr_a": float(np.mean([A[t] for t in shared])),
                                 "asr_b": float(np.mean([B[t] for t in shared]))})
            if not per_seed:
                continue
            # Pool across seeds: seeds share the 37 prompts, so pooling items would fake
            # independence. Report the per-seed bounds and the worst (widest) of them.
            worst = max(s["equiv_bound"] for s in per_seed)
            results.append({"budget": blab, "contrast": f"{a_arm} - {b_arm}",
                            "per_seed": per_seed,
                            "mean_delta": float(np.mean([s["delta_asr"] for s in per_seed])),
                            "worst_equiv_bound": worst,
                            "n_seeds": len(per_seed)})

    payload = {"provisional": True,
               "not_for_publication_reason":
                   "plan §20.4 requires a second pass after §20.6 supplies a multi-direction SD",
               "method": "percentile bootstrap over paired items; 90% CI = TOST region at alpha=0.05",
               "n_boot": args.n_boot, "results": results, "notes": notes}
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(payload, indent=2))

    print(f"§20.4 PROVISIONAL equivalence bounds  (n_boot={args.n_boot})")
    print(f"{'budget':<14}{'contrast':<30}{'mean d':>8}{'worst bound':>13}  per-seed 90% CI")
    for r in results:
        cis = "  ".join(f"[{s['ci90'][0]:+.3f},{s['ci90'][1]:+.3f}]" for s in r["per_seed"])
        print(f"{r['budget']:<14}{r['contrast']:<30}{r['mean_delta']:>+8.3f}"
              f"{r['worst_equiv_bound']:>13.3f}  {cis}")
    for nline in notes:
        print(f"  [note] {nline}")
    print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
