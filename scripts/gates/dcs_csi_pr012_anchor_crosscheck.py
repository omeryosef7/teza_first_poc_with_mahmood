"""Cross-validate the CENSUS READER against W4, using the three arms both families ran.

⛔ THE EXPECTATION AND ITS TOLERANCE ARE FROZEN IN THIS FILE, WRITTEN WHILE THE CENSUS DOES NOT EXIST
(918631 at 18 of 44 arms; REVIEW R21). After seeing a mismatch, any threshold chosen would be a
threshold chosen to accommodate it.

WHAT THIS TESTS. PR-CSI-012 re-runs HD_BASE, HD_KO, HD_TOPK and HD_BOTK -- the same arms on the same
rows that PR-CSI-010 and PR-CSI-011 ran. The census reader computes E through W4's own `by_domain` /
`load_installation`, so if the reader is correct AND the forward pass reproduces, its E for those three
arms must equal W4's PUBLISHED values:

    E(HD_KO)   = -0.22696123      ci95 [-0.27586414, -0.17868012]
    E(HD_TOPK) = -0.19598350      ci95 [-0.24306753, -0.15349093]
    E(HD_BOTK) = -0.01256722      ci95 [-0.02020293, -0.00465766]
                                  (reports/DCS_CSI_PR011_ALL32_validation.json, job 918169)

⚠ WHAT IS AND IS NOT ALREADY ESTABLISHED. S-243 section 5 found these values BIT-IDENTICAL across jobs
916536 and 918169 -- but BOTH RAN ON n-301. The census runs on n-303: same GPU model (RTX 3090) and same
compute capability (8.6), DIFFERENT PHYSICAL NODE. Cross-node bit-identity has never been measured in
this sprint, so predicting it would be extending a same-node result to a cross-node case -- the exact
shape of the R9/S-147 error. Three outcomes are therefore preregistered, not one.

THE TOLERANCE, AND WHY 1e-4. |E(HD_BOTK)| = 0.01256722 is the family's own near-null comparator, and
1 % of it is 1.26e-4. A tolerance of 1e-4 is below that, so a difference this small cannot move the
anchor arms relative to the comparator that defines "no effect" here. The number is derived from an
already-published value rather than chosen today.
"""
import argparse, json, os, sys

W4_E = {"HD_KO": -0.22696123, "HD_TOPK": -0.19598350, "HD_BOTK": -0.01256722}
W4_SRC = "reports/DCS_CSI_PR011_ALL32_validation.json"
TOL = 1e-4


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--census", default="reports/DCS_CSI_PR012_CENSUS_validation.json")
    a = ap.parse_args()
    if not os.path.exists(a.census):
        sys.exit("REFUSING: %r does not exist yet." % a.census)
    cen = json.load(open(a.census))
    if not cen.get("NO_RANK_TEST"):
        sys.exit("REFUSING: %r is not a census report" % a.census)

    print("ANCHOR CROSS-CHECK -- census reader vs W4's published E (%s)" % W4_SRC)
    print("%-10s %16s %16s %14s  %s" % ("arm", "census", "W4 published", "abs diff", "verdict"))
    exact = 0
    worst = 0.0
    bad = []
    for arm, want in W4_E.items():
        got = cen["E"].get(arm)
        if got is None:
            bad.append("%s: ABSENT from the census" % arm)
            print("%-10s %16s %16.8f %14s  FAIL (absent)" % (arm, "--", want, "--"))
            continue
        d = abs(got - want)
        worst = max(worst, d)
        if d == 0.0:
            v = "EXACT"; exact += 1
        elif d <= TOL:
            v = "within %g" % TOL
        else:
            v = "FAIL"; bad.append("%s: |diff| %.3e > %g" % (arm, d, TOL))
        print("%-10s %16.8f %16.8f %14.3e  %s" % (arm, got, want, d, v))

    print()
    if bad:
        for b in bad:
            print("  " + b)
        sys.exit("STOP. The census reader does not reproduce W4's published anchors within the "
                 "preregistered tolerance. EITHER the reader is wrong OR the run did not reproduce; "
                 "the census MUST NOT be used until this is explained. (frozen expectation, R21)")
    if exact == len(W4_E):
        print("PASS-STRONG: all three anchors BIT-IDENTICAL to W4's published values. This validates "
              "the census reader's endpoint AND establishes CROSS-NODE determinism (n-301 -> n-303), "
              "which S-243 section 5 did not test.")
    else:
        print("PASS: all three anchors agree within the preregistered %g. The census reader is "
              "validated. CROSS-NODE BIT-IDENTITY DOES NOT HOLD (worst |diff| %.3e) -- a finding in "
              "its own right, and one that invalidates nothing: it is far below 1 %% of "
              "|E(HD_BOTK)|." % (TOL, worst))


if __name__ == "__main__":
    main()
