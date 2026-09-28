#!/usr/bin/env python3
"""`--control-prefixes` must not be able to select a family that only LOOKS right.

*** WHY THIS FILE EXISTS. ***
REVIEW R41 (S-532) measured three ways to get the wrong control family out of an unvalidated
`startswith`, against the 34 real necessity arm names:

    "KO_NEC_SHUF"               -> 24 controls, floor 1/25 = 0.0400   <- the intended family
    "KO_NEC_SHUF, KO_NEC_RAND"  -> 24, floor STILL 0.0400.  The leading space makes the second
                                   prefix match nothing, so the read is of the SHUFFLED-ONLY
                                   family while the command line says otherwise, and the printed
                                   floor is the one you expected. Silent.
    "KO_NEC"                    -> 32, INCLUDING the candidate itself and the positive control.
                                   The candidate is ranked against itself (a comparison that
                                   cannot fail) and against an arm built to be maximal.

PR-CSI-022/023 VOID 8 freezes the control family, the primary statistic, the prefix strings AND
the floor -- and nothing in the analyser asserted any of them. The rank floor is 1/(n+1), so a
family of the wrong size silently changes the p the read is allowed to report.

This tests the SELECTION and REFUSAL logic in isolation; it needs no run directories. The
source-grep at the end is what fails if the guards are removed from the analyser.
"""
import os
import sys

FAILS = []
SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "scripts", "dcs_csi_subspace_analyze.py")

# The 34 arms of a necessity family, exactly as slurm_scripts/dcs_csi_p1_arms.slurm launches them
# across halves 1, 2, 4 and 5 (half 3 is 8 EXTRA random controls and is not part of this design).
ARMS = (["NEC_BASE", "NEC_KO", "KO_NEC_FULL", "KO_NEC_AXIS", "KO_NEC_ORTH", "KO_NEC_AXIS_ANCHOR"]
        + ["KO_NEC_SHUF%d" % i for i in range(24)]
        + ["KO_NEC_RAND%d" % i for i in range(4)])
CANDIDATE, FULL = "KO_NEC_AXIS", "KO_NEC_FULL"


def check(name, cond, detail=""):
    print(("  PASS  " if cond else "  FAIL  ") + name + (("   " + detail) if detail else ""))
    if not cond:
        FAILS.append(name)


def select(prefix_arg, strip=True):
    """Mirror of the analyser's selection. `strip=False` reproduces the pre-S-533 behaviour."""
    pref = [x.strip() for x in prefix_arg.split(",")] if strip else prefix_arg.split(",")
    if not pref or any(x == "" for x in pref):
        raise ValueError("empty prefix")
    return [x for x in ARMS if x.startswith(tuple(pref))]


def floor_of(n):
    return 1.0 / (n + 1)


def main():
    print("[the intended family]")
    sel = select("KO_NEC_SHUF")
    check("KO_NEC_SHUF selects exactly 24", len(sel) == 24, "floor=%.4f" % floor_of(len(sel)))
    check("its floor is exactly 0.0400", abs(floor_of(24) - 0.04) < 1e-12)
    check("the candidate is NOT in it", CANDIDATE not in sel)
    check("the positive control is NOT in it", FULL not in sel)
    check("KO_NEC_AXIS_ANCHOR is NOT in it", "KO_NEC_AXIS_ANCHOR" not in sel)
    check("no RAND arm is in it", not any(x.startswith("KO_NEC_RAND") for x in sel))

    print("\n[the SILENT defect: a space makes a prefix match nothing]")
    unstripped = select("KO_NEC_SHUF, KO_NEC_RAND", strip=False)
    check("unstripped ' KO_NEC_RAND' silently yields 24, not 28", len(unstripped) == 24,
          "and floor %.4f is the one you expected -- nothing looks wrong" % floor_of(len(unstripped)))
    check("stripping FIXES it: 28 arms", len(select("KO_NEC_SHUF, KO_NEC_RAND")) == 28,
          "floor=%.4f" % floor_of(28))
    check("the two differ, so stripping is load-bearing",
          len(unstripped) != len(select("KO_NEC_SHUF, KO_NEC_RAND")))

    print("\n[the LOUD defect the guard must refuse: candidate inside its own family]")
    broad = select("KO_NEC")
    check("KO_NEC selects 32", len(broad) == 32)
    check("KO_NEC includes the CANDIDATE", CANDIDATE in broad,
          "the candidate would be ranked against itself")
    check("KO_NEC includes the POSITIVE CONTROL", FULL in broad,
          "an arm built to be maximal")
    check("so a candidate-in-family check is REQUIRED, not cosmetic", CANDIDATE in broad)

    print("\n[the empty prefix]")
    for bad in ("", "KO_NEC_SHUF,", ",", "  "):
        try:
            select(bad)
            check("empty prefix %r is refused" % bad, False, "it was ACCEPTED")
        except ValueError:
            check("empty prefix %r is refused" % bad, True)

    print("\n[family size changes the reportable p]")
    check("24 -> 0.0400 clears alpha", floor_of(24) < 0.05)
    check("23 -> 0.0417 ALSO clears alpha, so a dropped arm is silent",
          floor_of(23) < 0.05, "%.4f -- still passes, wrong floor" % floor_of(23))
    check("19 -> 0.0500 does NOT clear alpha", not (floor_of(19) < 0.05))

    print("\n[guards present in the analyser source]")
    src = open(SRC).read()
    for needle in ('_prefixes = [x.strip() for x in a.control_prefixes.split(",")]',
                   'any(x == "" for x in _prefixes)',
                   "is inside the control family selected by --control-prefixes",
                   "--expect-n-controls",
                   "--expect-n-domains",
                   "a.expect_n_controls is not None and len(ctrl_arms) != a.expect_n_controls",
                   "a.expect_n_domains is not None and len(doms) != a.expect_n_domains"):
        check("source contains %r" % needle[:46], needle in src)

    print("\n%s (%d failure(s))" % ("CONTROL FAMILY GUARDED" if not FAILS
                                   else "FAILURES: " + ", ".join(FAILS), len(FAILS)))
    return 1 if FAILS else 0


# ---------------------------------------------------------------------------------------------
# PYTEST ENTRY POINTS -- ADDED S-534, for the reason given in test_subspace_verdict_branches.py:
# this file shipped at S-533 with zero `def test_` functions and was not in GUARD_TESTS, so the
# "516 passed" of that commit DID NOT INCLUDE IT.
# ---------------------------------------------------------------------------------------------
def test_control_family_guarded():
    assert main() == 0, "see the printed PASS/FAIL lines above"


def test_intended_prefix_selects_exactly_24():
    assert len(select("KO_NEC_SHUF")) == 24


def test_candidate_and_positive_control_never_in_intended_family():
    sel = select("KO_NEC_SHUF")
    assert CANDIDATE not in sel and FULL not in sel


def test_broad_prefix_would_swallow_the_candidate():
    """Why the unconditional candidate-in-family refusal exists."""
    broad = select("KO_NEC")
    assert CANDIDATE in broad and FULL in broad


def test_unstripped_space_silently_shrinks_the_family():
    """The silent defect: floor stays 0.0400 so nothing looks wrong."""
    assert len(select("KO_NEC_SHUF, KO_NEC_RAND", strip=False)) == 24
    assert len(select("KO_NEC_SHUF, KO_NEC_RAND")) == 28


def test_empty_prefix_refused():
    import pytest
    for bad in ("", ",", "KO_NEC_SHUF,", "  "):
        with pytest.raises(ValueError):
            select(bad)


def test_one_dropped_arm_changes_the_floor_but_not_the_verdict():
    assert floor_of(24) < 0.05 and floor_of(23) < 0.05
    assert abs(floor_of(24) - 0.0400) < 1e-4 and abs(floor_of(23) - 0.0417) < 1e-4


if __name__ == "__main__":
    raise SystemExit(main())
