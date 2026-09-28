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


def verdict(rank, n_controls, split="train", cand=None, necessity=False):
    """Mirror of the analyser's P1-i decision, kept deliberately in one place.

    If this drifts from dcs_csi_subspace_analyze.main(), the drift is itself the bug this file is
    meant to expose -- see `test_mirror_matches_source` below, which greps the source for the
    branch conditions so a silent divergence fails loudly.

    S-533: the mirror gained the CANDIDATE SIGN term, and the source-grep below caught the drift
    the moment the analyser changed -- which is this file working exactly as intended.
    `cand=None` means "sign not under test" and keeps the pre-S-533 cases readable.
    """
    rank_p = rank / float(n_controls + 1)
    floor = 1.0 / (n_controls + 1)
    attainable = floor < 0.05
    sign_ok = True if cand is None else ((cand < 0) if necessity else (cand > 0))
    if rank == 1 and attainable and sign_ok:
        return "PASS"
    if rank == 1 and attainable and not sign_ok:
        return "WRONG SIGN"
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
                   "if rank == 1 and attainable and cand_sign_ok:",
                   "elif rank == 1 and attainable and not cand_sign_ok:",
                   "elif rank == 1:",
                   "PRIMARY INCONCLUSIVE",
                   # S-533 / R41 CRITICAL-1. Without these the analyser can print
                   # "PRIMARY PASSES ... the single most NEGATIVE value" on a POSITIVE candidate.
                   "cand_sign_ok = (cand_rec < 0) if NEC else (cand_rec > 0)",
                   "RANK 1 WITH THE WRONG SIGN"):
        check("source still contains %r" % needle[:44], needle in src)

    print("\n[S-533 / R41 CRITICAL-1 -- the candidate SIGN guard]")
    # The defect: rank measures EXTREMITY WITHIN THE FAMILY, not direction of effect. Under
    # necessity a POSITIVE candidate still ranks 1 if every control is MORE positive.
    check("necessity + NEGATIVE candidate at rank 1 -> PASS",
          verdict(1, 24, cand=-0.00216, necessity=True) == "PASS",
          "this is D44's actual configuration")
    check("necessity + POSITIVE candidate at rank 1 -> NOT a PASS",
          verdict(1, 24, cand=+0.00216, necessity=True) != "PASS",
          "the branch that printed 'most NEGATIVE value' on a positive number")
    check("necessity + POSITIVE candidate at rank 1 -> WRONG SIGN, not DOES NOT PASS",
          verdict(1, 24, cand=+0.00216, necessity=True) == "WRONG SIGN",
          "neither fact is hidden: extreme in family, wrong direction")
    check("sufficiency + POSITIVE candidate at rank 1 -> PASS",
          verdict(1, 46, cand=+0.00264, necessity=False) == "PASS",
          "D23/D24's configuration")
    check("sufficiency + NEGATIVE candidate at rank 1 -> NOT a PASS",
          verdict(1, 46, cand=-0.00264, necessity=False) != "PASS")
    check("the guard is NARROWING ONLY: it never creates a PASS",
          all(not (verdict(r, nn, cand=c, necessity=nec) == "PASS"
                   and verdict(r, nn) != "PASS")
              for r in (1, 2, 5) for nn in (8, 24, 46)
              for c in (-1.0, +1.0) for nec in (True, False)),
          "every sign-guarded PASS was already a PASS without the guard")
    check("all five committed necessity candidates still PASS at rank 1 (no verdict moves)",
          all(verdict(1, 24, cand=c, necessity=True) == "PASS"
              for c in (-0.00852, -0.00848, -0.0087, -0.01283, -0.00216)),
          "measured at S-532 before the change")

    print("\n%s (%d failure(s))" % ("ALL VERDICT BRANCHES REACHABLE" if not FAILS
                                    else "FAILURES: " + ", ".join(FAILS), len(FAILS)))
    return 1 if FAILS else 0


# ---------------------------------------------------------------------------------------------
# PYTEST ENTRY POINTS -- ADDED S-534.
# This file was script-style (`main()` + `raise SystemExit`) with ZERO `def test_` functions, and
# it was NOT in the pre-commit hook's GUARD_TESTS allowlist. So it ran ONLY when invoked by hand.
# At S-533 its mirror-vs-source check caught a real drift in dcs_csi_subspace_analyze.py -- but it
# caught it because I ran the file manually, NOT because the suite enforced it. A guard that only
# fires when someone remembers to fire it is not a guard. Both halves are fixed at S-534: these
# wrappers make pytest collect it, and the file is added to GUARD_TESTS and to the installer.
# ---------------------------------------------------------------------------------------------
def test_every_verdict_branch_reachable_and_sign_guarded():
    """main() returns the failure count; 0 is the only acceptable value."""
    assert main() == 0, "see the printed PASS/FAIL lines above for which check failed"


def test_sign_guard_is_narrowing_only():
    """The S-533 guard must never CREATE a pass -- checked independently of main()."""
    for rank in (1, 2, 5):
        for n in (8, 24, 46):
            for cand in (-1.0, +1.0):
                for nec in (True, False):
                    guarded = verdict(rank, n, cand=cand, necessity=nec)
                    unguarded = verdict(rank, n)
                    if guarded == "PASS":
                        assert unguarded == "PASS", (
                            "guard CREATED a pass at rank=%d n=%d cand=%s nec=%s"
                            % (rank, n, cand, nec))


def test_committed_necessity_reads_still_pass():
    """The five committed necessity candidates are all negative, so none loses its PASS."""
    for cand in (-0.00852, -0.00848, -0.0087, -0.01283, -0.00216):
        assert verdict(1, 24, cand=cand, necessity=True) == "PASS", cand


def test_wrong_sign_is_its_own_outcome():
    assert verdict(1, 24, cand=+0.00216, necessity=True) == "WRONG SIGN"
    assert verdict(1, 46, cand=-0.00264, necessity=False) == "WRONG SIGN"


if __name__ == "__main__":
    raise SystemExit(main())
