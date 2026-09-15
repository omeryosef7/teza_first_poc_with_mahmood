#!/usr/bin/env python3
"""Every VERDICT branch of dcs_csi_subspace_analyze must be reachable on an input that should
trigger it.

*** WHY THIS FILE EXISTS. ***
Review R3-B1: the analyser's PASS branch was DEAD CODE. `rank_p = rank/(n+1)` bottoms out at
1/(n+1), so PASS required >= 20 controls while every run in the record had 10, 8 or 4 -- and the
else-branch then reported a rank-1 candidate as "INSIDE the controls, not above them", which is
false. It shipped, and the sprint's headline negative was being read off a verdict that could not
have said anything else.

The rule adopted after review round 2 was "every control must be tested against a deliberately
broken input". R3-B1 is that rule's inverse and it was not applied to the verdict logic itself.
Hence: **every verdict branch gets an input that should produce it**, checked here, so a branch
cannot silently become unreachable again.

This tests the VERDICT FUNCTION's decision logic in isolation -- it does not need run directories.
"""
import os
import sys

FAILS = []


def check(name, cond, detail=""):
    print(("  PASS  " if cond else "  FAIL  ") + name + (("   " + detail) if detail else ""))
    if not cond:
        FAILS.append(name)


def verdict(rank, n_controls, split="train"):
    """Mirror of the analyser's P1-i decision, kept deliberately in one place.

    If this drifts from dcs_csi_subspace_analyze.main(), the drift is itself the bug this file is
    meant to expose -- see `test_mirror_matches_source` below, which greps the source for the
    branch conditions so a silent divergence fails loudly.
    """
    rank_p = rank / float(n_controls + 1)
    floor = 1.0 / (n_controls + 1)
    attainable = floor < 0.05
    if rank == 1 and attainable:
        return "PASS"
    if rank == 1:
        return "INCONCLUSIVE"
    return "DOES NOT PASS"


def main():
    print("[verdict branches — each must be reachable]")
    # PASS needs rank 1 AND enough controls that the floor clears 0.05 -> n >= 20.
    check("PASS is reachable (rank 1, n=20)", verdict(1, 20) == "PASS",
          "floor=%.4g" % (1 / 21))
    check("PASS is NOT claimed with too few controls (rank 1, n=10)",
          verdict(1, 10) == "INCONCLUSIVE", "floor=%.4g > 0.05" % (1 / 11))
    check("INCONCLUSIVE is reachable (rank 1, n=10)", verdict(1, 10) == "INCONCLUSIVE")
    check("DOES NOT PASS is reachable (rank 4, n=10)", verdict(4, 10) == "DOES NOT PASS")
    check("rank 2 is never PASS however many controls", verdict(2, 100) == "DOES NOT PASS")

    print("\n[the exact configurations this sprint shipped]")
    for rank, n, want in ((4, 10, "DOES NOT PASS"),   # rank-1 candidate, TRAIN and VALIDATION
                          (3, 10, "DOES NOT PASS"),   # rank-5 candidate, TRAIN
                          (2, 3, "DOES NOT PASS"),    # rank-5, partial family
                          (1, 10, "INCONCLUSIVE")):   # the case B1 got WRONG
        check("rank %d of %d -> %s" % (rank, n + 1, want), verdict(rank, n) == want)

    print("\n[the B1 regression itself]")
    check("a rank-1 candidate with 10 controls is NOT called 'inside the controls'",
          verdict(1, 10) != "DOES NOT PASS",
          "this is exactly what R3-B1 shipped")

    print("\n[mirror matches the source]")
    src = open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            "scripts", "dcs_csi_subspace_analyze.py")).read()
    for needle in ('attainable = dist["rank_p_floor"] < 0.05',
                   "if rank == 1 and attainable:",
                   "elif rank == 1:",
                   "PRIMARY INCONCLUSIVE"):
        check("source still contains %r" % needle[:44], needle in src)

    print("\n%s (%d failure(s))" % ("ALL VERDICT BRANCHES REACHABLE" if not FAILS
                                    else "FAILURES: " + ", ".join(FAILS), len(FAILS)))
    return 1 if FAILS else 0


if __name__ == "__main__":
    raise SystemExit(main())
