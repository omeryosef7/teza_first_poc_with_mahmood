"""Forced-choice mapping-installation verdict, emitted WITH the floor that makes it readable.

Every other headline this sprint is produced by a script that writes a JSON artifact carrying its own
pre-registration.  The installation counts were not: they were computed ad hoc in a tick, and that is
exactly why two threshold errors went unnoticed until they were audited by hand.

* **C-31** applied an "installs / does not" cut at **0.500** without testing it against chance.  On 48
  binary rows `basket_gun` 19/48 is p=0.193 (**absent**, not inverted) and `ticket_knife` 30/48 is
  p=0.111 (**not established**, though 0.625 > 0.500).
* **C-33** found the same omission in the *pre-screen advice*: "clear chance by a real margin" names
  the right concept and no number, so it admits 30/48.
* **C-32** showed the population cannot be grown out of the problem: every bank supplies **72**
  natural_doublespeak forced-choice rows, **12 per dose over n in {0,1,2,4,8,16}**, so 48 run and
  **60** is the ceiling with demonstrations.  Power to detect a true 0.625 is **0.331 at n=48** and
  **0.399 at n=60**; `ticket_knife` is unresolvable with this bank, not merely unrun.

So this module refuses to emit a bare fraction.  A count is classified only against ``critical_k``,
the smallest k with two-sided exact p < alpha at that n -- **recomputed for the n actually used**,
never carried over from another population (C-33: 32/48, 39/60, 59/96).  Counts that clear neither
tail are ``NOT_ESTABLISHED``, which is a distinct verdict from ``ABSENT``, and the artifact also
reports the design's power so an unresolvable cell is visible as unresolvable rather than as a null.

Scalar fields only; no prompt or completion text is read.

Usage
-----
    python src/boombness/mapping_installation_verdict.py \
        --probe window_knife=outputs/boombness/score_behavior/wkA_... \
        --probe ticket_knife=outputs/boombness/score_behavior/tkA_... \
        --tag install
"""

from __future__ import annotations

import argparse
import collections
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common  # noqa: E402

#: The effect size the design was hoping to resolve (C-32's power table is quoted at this rate).
REFERENCE_RATE = 0.625


def binom_two_sided(k, n):
    """Two-sided exact binomial p against a fair coin. Same convention as the bridge."""
    if n == 0:
        return 1.0
    k = min(k, n - k)
    return min(1.0, 2.0 * sum(math.comb(n, i) for i in range(k + 1)) / (2.0 ** n))


def critical_k(n, alpha=0.05):
    """Smallest k with two-sided exact p < alpha at this n.

    MUST be recomputed per n. C-33 failed by reading one threshold ("above chance") as if it were
    population-independent; at n=48 it is 32, at n=60 it is 39, at n=96 it is 59.
    """
    for k in range(n // 2, n + 1):
        if binom_two_sided(k, n) < alpha:
            return k
    return None


def power_at(n, k, rate=REFERENCE_RATE):
    """P(reaching k of n) when the true rate is `rate` -- how often a real effect would register."""
    if k is None:
        return 0.0
    return sum(math.comb(n, i) * rate ** i * (1 - rate) ** (n - i) for i in range(k, n + 1))


def classify(wins, n, alpha=0.05):
    k = critical_k(n, alpha)
    if k is None:
        return "UNRESOLVABLE_AT_ANY_COUNT", k
    if wins >= k:
        return "INSTALLED", k
    if wins <= n - k:
        # Significantly BELOW chance means the model prefers the CODEWORD -- that is an INVERTED
        # mapping, not an absent one. Naming this tail "ABSENT" would have let a positive claim of
        # absence be read off a cell that only rules out installation (see the note on `basket_gun`).
        return "INVERTED", k
    # The cell C-31 got wrong: above 0.500 but not above chance.
    return "NOT_ESTABLISHED", k


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--probe", action="append", default=[], required=True, metavar="LABEL=RUNDIR")
    ap.add_argument("--alpha", type=float, default=0.05)
    ap.add_argument("--tag", default="install")
    ap.add_argument("--experiment", default="mapping_installation_verdict")
    args = ap.parse_args()

    run = common.RunDir(args.experiment, args=args, tag=args.tag)
    ledger = common.FailureLedger()

    per = {}
    for spec in args.probe:
        if "=" not in spec:
            raise SystemExit(f"[install] REFUSING: --probe needs LABEL=RUNDIR, got {spec!r}")
        lab, d = spec.split("=", 1)
        if lab in per:
            raise SystemExit(f"[install] REFUSING: duplicate probe label {lab!r}; a collision would "
                             f"silently drop an arm.")
        rows = [json.loads(l) for l in open(os.path.join(d, "results.jsonl"))]
        sm = json.load(open(os.path.join(d, "summary.json")))

        # Provenance gates: a verdict off a degraded run is worse than no verdict.
        if sm.get("option_mass_gate") != "PASS":
            raise SystemExit(f"[install] REFUSING {lab}: option_mass_gate is "
                             f"{sm.get('option_mass_gate')!r}, not PASS.")
        nfail = (sm.get("failures") or {}).get("n_failed", 0)
        if nfail:
            raise SystemExit(f"[install] REFUSING {lab}: {nfail} rows failed to generate.")

        # *** ATTRITION IS NOT JUST LOST POWER; THE SURVIVORS ARE A BIASED SUBSET ***
        # `n` below is taken from the rows on disk, so a silently shrunken population would simply
        # get a SMALLER critical_k and still produce a verdict that looks completely valid. That is
        # the C-33 shape arriving through the data instead of through the prose.
        # It is worse than a power loss: the attrition observed in practice is CUDA OOM (job 789095,
        # 92 of 160 rows), and OOM is length-correlated, so the rows that survive are systematically
        # the shorter prompts. A fraction computed on them is not an estimate of the bank's rate.
        n_bank = sm.get("n_bank_rows")
        n_res = sm.get("n_result_rows")
        if n_bank is not None and n_res is not None and n_res < n_bank:
            raise SystemExit(
                f"[install] REFUSING {lab}: {n_res} of {n_bank} rows survived. The threshold would "
                f"silently adapt to the smaller n and still print a verdict, but the survivors of "
                f"length-correlated attrition are not a random subset of the bank.")

        n = len(rows)
        wins = sum(1 for r in rows if r["p_concept"] > r["p_codeword"])
        ties = sum(1 for r in rows if r["p_concept"] == r["p_codeword"])
        verdict, k = classify(wins, n, args.alpha)
        for _ in range(n):
            ledger.ok()
        per[lab] = {
            "run_dir": d,
            "model": sm.get("model"),
            "arm": sm.get("arm"),
            "n": n,
            "mapped_wins": wins,
            "ties_not_counted_as_wins": ties,
            "frac": wins / n if n else None,
            "critical_k_at_this_n": k,
            "p_two_sided_vs_chance": binom_two_sided(wins, n),
            "alpha": args.alpha,
            "VERDICT": verdict,
            "power_to_detect_%.3f" % REFERENCE_RATE: power_at(n, k),
            "dose_balance": dict(collections.Counter(r.get("n_examples") for r in rows)),
            "conditions": sorted({str(r.get("condition")) for r in rows}),
        }

    out = {
        "schema": "MAPPING_INSTALLATION_VERDICT/1",
        "per_probe": per,
        "PRE_REGISTRATION": {
            "predicate": "mapped_win := p_concept > p_codeword (a tie is NOT a win)",
            "rule": ("INSTALLED iff wins >= critical_k(n, alpha); INVERTED iff wins <= n - critical_k "
                     "(significantly below chance = prefers the codeword); "
                     "otherwise NOT_ESTABLISHED. 0.500 is NOT a threshold (C-31)."),
            "threshold_is_per_n": ("critical_k is recomputed for the n actually used and never carried "
                                   "across populations (C-33): 32/48, 39/60, 59/96."),
            "power_caveat": ("C-32: this bank supplies 72 forced-choice natural_doublespeak rows, 12 "
                             "per dose over n in {0,1,2,4,8,16}; 48 run and 60 is the ceiling with "
                             "demonstrations. Power at 0.625 is 0.331 (n=48) and 0.399 (n=60), so a "
                             "NOT_ESTABLISHED cell here is an unresolvable design, not a null result."),
        },
    }
    path = os.path.join(run.path, "mapping_installation_verdict.json")
    with open(path, "w") as fh:
        json.dump(out, fh, indent=2, sort_keys=True)
    run.finish(summary={"n_probes": len(per),
                        "verdicts": {k: v["VERDICT"] for k, v in per.items()}}, ledger=ledger)
    print(f"[install] wrote {path}")
    for k, v in sorted(per.items()):
        print(f"  {k:16s} {v['mapped_wins']}/{v['n']} p={v['p_two_sided_vs_chance']:.3g} "
              f"crit={v['critical_k_at_this_n']} -> {v['VERDICT']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
