#!/usr/bin/env python3
"""Exact tests to replace the bootstrap resolution floor.

WHY THIS EXISTS
---------------
Most p-values in this phase are reported as `p = 0.00005`. That is not a
measurement. It is `1 / 20000`, the smallest non-zero value a 20000-draw
domain-clustered bootstrap can resolve, and it appears identically next to
effects that differ in strength by orders of magnitude. REVIEW-7 accepted the
point; this closes it.

Where an effect is SIGN-CONSISTENT across independent domains, the sign test is
exact and needs no resampling at all. It is also the more conservative choice:
it throws away every effect magnitude and keeps only the direction.

The independence unit is the DOMAIN, as everywhere else in this phase.

TIES
----
The standard sign test DISCARDS ties. That is not a convenience here, it is the
substantive point of CONT-ENTRY 126: in 28 domains neither arm ever refuses, so
the difference is exactly 0 BY CONSTRUCTION and carries no information about
direction. Counting structural zeros as "failures to replicate" understates an
effect with no counterexamples. Both denominators are reported below so the
reader can see the choice rather than inherit it.

SCOPE -- THE DEFECT THIS FILE SHIPPED WITH (C-CONT-093)
-------------------------------------------------------
The first version of this script carried NO scope field and its headline number,
p = 2.33e-10 for the refusal effect, was computed on the ALL-SLOTS scope that
CONT-ENTRY 120 had already declared SECONDARY. On the declared slot0 PRIMARY the
same effect is 8- / 0+ / 59 tied, p = 0.0078 -- EIGHT ORDERS OF MAGNITUDE weaker.

That is C-CONT-089 repeated inside the entry that was fixing p-value defects, two
entries before I wrote scripts/dcs_cont_scope.py to prevent exactly it. Every
result below now carries its scope explicitly and BOTH scopes are printed, because
a sign count without a scope is not a result.

PROVENANCE OF THE COUNTS
------------------------
Counts marked verified=True were recomputed from raw judge artifacts for this
file. Counts marked verified=False are carried from the named entry and are
LABELLED AS SUCH -- they have not been re-derived here and must not be quoted as
if they had been.
"""
from __future__ import annotations
import json
from dataclasses import dataclass, asdict
from fractions import Fraction


def exact_sign_test(n_pos: int, n_neg: int) -> dict:
    """Two-sided exact sign test. Ties must already be excluded by the caller.

    Uses exact integer/Fraction arithmetic -- at n=67 the p-value is ~6.8e-21 and
    float accumulation of binomial terms is not something to trust silently.
    """
    n = n_pos + n_neg
    if n == 0:
        return {"n": 0, "p_two_sided": None, "note": "no non-tied domains; no test"}
    k = min(n_pos, n_neg)
    # two-sided = 2 * P(X <= k) under Binomial(n, 1/2)
    tail = sum(_choose(n, i) for i in range(k + 1))
    p = Fraction(2 * tail, 2 ** n)
    return {
        "n_nontied": n, "n_pos": n_pos, "n_neg": n_neg,
        "p_two_sided": float(min(p, Fraction(1))),
        "p_exact_fraction": f"{2*tail}/2^{n}",
    }


def _choose(n: int, k: int) -> int:
    from math import comb
    return comb(n, k)


@dataclass
class Result:
    claim: str
    quantity: str
    n_neg: int
    n_pos: int
    n_tied: int
    tie_reason: str
    provenance: str
    bootstrap_reported: str


RESULTS = [
    Result(
        claim="A4 / A15  [PRIMARY]",
        quantity="refusal difference, knockout minus control (matched hardware, button)",
        n_neg=8, n_pos=0, n_tied=59,
        tie_reason="on the declared slot0 primary only 8 domains can move at all; this is the "
                   "number that should have been published in CONT-ENTRY 132",
        provenance="recomputed here from casrHW_ko / casrHW_ctrlHW (verified)",
        bootstrap_reported="p = 0.00005 (floor)",
    ),
    Result(
        claim="A4 / A15  [secondary]",
        quantity="same, on the ALL-SLOTS scope CONT-ENTRY 120 declared secondary",
        n_neg=33, n_pos=0, n_tied=34,
        tie_reason="28 of the 34 are domains where NEITHER arm ever refuses. This is the number "
                   "CONT-ENTRY 132 published WITHOUT saying it was the secondary scope",
        provenance="recomputed here from casrHW_ko / casrHW_ctrlHW (verified)",
        bootstrap_reported="p = 0.00005 (floor)",
    ),
    Result(
        claim="A1 (button)  [secondary]",
        quantity="semantic installation drop under the codeword-row knockout",
        n_neg=67, n_pos=0, n_tied=0,
        tie_reason="none",
        provenance="CONT-ENTRY 100 -- NOT re-derived here; all-slots. REVIEW-8 reports the primary "
                   "as 65/2 -> 3.1e-17, i.e. scope-robust, but I have not verified that myself",
        bootstrap_reported="p = 0.00005 (floor)",
    ),
]

def main() -> int:
    out = []
    print("EXACT SIGN TESTS -- replacing the 1/20000 bootstrap floor")
    print("independence unit: DOMAIN; ties discarded (see module docstring)\n")
    for r in RESULTS:
        t = exact_sign_test(r.n_pos, r.n_neg)
        # D4: the original sensitivity added ties to the SUPPORTING side, which can only make
        # the p smaller. Both directions are now reported; the against-direction is the honest one.
        naive = exact_sign_test(r.n_pos + r.n_tied, r.n_neg)   # ties counted AGAINST
        rec = {**asdict(r), "exact": t,
               "if_ties_counted_AGAINST": naive["p_two_sided"]}
        out.append(rec)
        print(f"{r.claim:12s} {r.quantity[:58]}")
        print(f"  {r.n_neg} negative / {r.n_pos} positive / {r.n_tied} tied"
              f"   ({r.tie_reason[:60]})")
        print(f"  bootstrap said : {r.bootstrap_reported}")
        print(f"  EXACT          : p = {t['p_two_sided']:.3g}   ({t['p_exact_fraction']})")
        print(f"  provenance     : {r.provenance}\n")
    print("SCOPE MATTERS: the same refusal effect is p = %.3g on the declared PRIMARY and\n"
          "p = %.3g on the secondary -- the published figure was the secondary, unlabelled."
          % (out[0]["exact"]["p_two_sided"], out[1]["exact"]["p_two_sided"]))
    with open("reports/DCS_CONT_EXACT_TESTS.json", "w") as f:
        json.dump({"schema": "exact_tests/1",
                   "why": "p=0.00005 is 1/20000, a resampling resolution floor, not a measurement",
                   "independence_unit": "domain",
                   "results": out}, f, indent=1)
    print("\nwrote reports/DCS_CONT_EXACT_TESTS.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
