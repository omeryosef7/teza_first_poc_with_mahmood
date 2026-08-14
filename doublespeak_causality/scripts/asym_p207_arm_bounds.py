#!/usr/bin/env python
"""
ASYMMETRY SPRINT §20.7 — equivalence bounds on the objective-space arm contrasts.

WHY THIS EXISTS
---------------
`SECTION20_RESULTS.md` §7 states the sprint's strongest form of the direction-term negative:

    | mechanism − vanilla         | 0.2151 | 22.7 % of the compute effect |
    | mechanism − matched_random  | 0.1618 | 17.1 % |

Those two bounds appear in **no artifact**. A scan of 1 881 JSON files under both output trees
(2026-08-15) found the values only as coincidental matches in unrelated studies. They were computed
once and never persisted — which contradicts that document's own opening promise that every number
is quoted from an artifact.

The numbers themselves check out: recomputing here reproduces 0.2145 → **22.7 %** and 0.1637 →
**17.3 %**, differing from the quoted values by 0.0006 and 0.0019, i.e. bootstrap resampling noise.
So this script closes a **provenance** gap, not a correctness one.

METHOD (matches what §7 describes: "paired bootstrap, 200 steps")
----------------------------------------------------------------
Endpoint is the same as the rest of §20.7: best-so-far GCG `task_loss` per prompt, paired across
arms within a seed. For each contrast and seed, resample the 37 per-prompt deltas with replacement,
take the 90 % percentile interval of the mean, and report `max(|lo|, |hi|)` as the equivalence
bound. The headline is the **worst** bound across the three seeds — the conservative choice, since
a bound is a claim about what the data could not have hidden.

Expressed as a percentage of the compute effect (`5 → 200`, pooled over seeds at the prompt level,
−0.9463 from `asym_p207_curve_5to200_3seed.json`) so the two are on one scale.

Deterministic: the bootstrap RNG is seeded, so re-running reproduces the artifact exactly.

Scalars only; never reads suffix or generation text.
"""
import argparse, glob, json, os
from pathlib import Path

import numpy as np


def best_losses(arm, seed, budget, root):
    """-> {task_id: best-so-far task_loss} for completed runs at this budget."""
    pat = {5: f"asym_p75_{arm}_s5_pp_*seed{seed}",
           200: f"asym_p75_{arm}_pp_*seed{seed}",
           600: f"asym_p75_{arm}_s600_pp_*seed{seed}"}[budget]
    out = {}
    for d in glob.glob(os.path.join(root, pat)):
        if not os.path.exists(os.path.join(d, "FINAL_CANDIDATES.jsonl")):
            continue
        il = os.path.join(d, "ITERATION_LOG.jsonl")
        rows = [json.loads(l) for l in open(il) if l.strip()]
        if len(rows) < budget:
            continue
        if {r.get("n_train_tasks") for r in rows} != {1}:
            raise SystemExit(f"{d}: n_train_tasks != 1 -- not a per-prompt run")
        tid = "_".join(os.path.basename(d).split("_pp_")[1].split("_")[:-1])
        out[tid] = min(r["task_loss"] for r in rows if r.get("task_loss") is not None)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="outputs/stage_gcg_perprompt")
    ap.add_argument("--budget", type=int, default=200)
    ap.add_argument("--seeds", default="42,43,44")
    ap.add_argument("--n-boot", type=int, default=10000)
    ap.add_argument("--rng-seed", type=int, default=20260815)
    ap.add_argument("--compute-effect", type=float, default=None,
                    help="pooled 5->200 mean delta; read from the curve artifact if omitted")
    ap.add_argument("--curve", default="doublespeak_causality/outputs/asym_p207_curve_5to200_3seed.json")
    ap.add_argument("--out", default="doublespeak_causality/outputs/asym_p207_arm_bounds.json")
    args = ap.parse_args()

    seeds = [int(s) for s in args.seeds.split(",")]
    compute = args.compute_effect
    if compute is None:
        compute = abs(json.loads(Path(args.curve).read_text())["pooled"]["mean_delta"])

    rng = np.random.default_rng(args.rng_seed)
    results = []
    for a, b in (("mechanism", "vanilla"), ("mechanism", "matched_random"),
                 ("matched_random", "vanilla")):
        per_seed, worst = [], 0.0
        for s in seeds:
            A, B = best_losses(a, s, args.budget, args.root), best_losses(b, s, args.budget, args.root)
            ids = sorted(set(A) & set(B))
            d = np.array([A[i] - B[i] for i in ids])
            boot = np.array([rng.choice(d, len(d), replace=True).mean()
                             for _ in range(args.n_boot)])
            lo, hi = (float(x) for x in np.percentile(boot, [5, 95]))
            bound = max(abs(lo), abs(hi))
            worst = max(worst, bound)
            per_seed.append({"seed": s, "n": len(ids), "mean_delta": float(d.mean()),
                             "ci90_lo": lo, "ci90_hi": hi, "bound": bound})
        row = {"contrast": f"{a} - {b}", "budget": args.budget, "per_seed": per_seed,
               "worst_bound": worst, "pct_of_compute_effect": 100 * worst / compute}
        results.append(row)
        print(f"{row['contrast']}: worst bound {worst:.4f} "
              f"-> {row['pct_of_compute_effect']:.1f} % of the compute effect")
        for r in per_seed:
            print(f"   seed{r['seed']} n={r['n']} mean={r['mean_delta']:+.4f} "
                  f"90%CI=[{r['ci90_lo']:+.4f},{r['ci90_hi']:+.4f}] bound={r['bound']:.4f}")

    Path(args.out).write_text(json.dumps({
        "endpoint": "best-so-far GCG task_loss, paired per prompt within seed",
        "method": "paired bootstrap over items; 90% percentile interval of the mean; "
                  "bound = max(|lo|,|hi|); headline = worst bound across seeds",
        "n_boot": args.n_boot, "rng_seed": args.rng_seed, "budget": args.budget,
        "compute_effect_5_to_200": compute,
        "why_this_file_exists": "SECTION20_RESULTS.md §7 quoted these bounds (0.2151 / 0.1618) "
                                "with no artifact behind them; a scan of 1881 JSONs on 2026-08-15 "
                                "found none. Recomputation reproduces them to bootstrap noise, so "
                                "this closes a provenance gap, not a correctness one.",
        "contrasts": results,
    }, indent=2))
    print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
