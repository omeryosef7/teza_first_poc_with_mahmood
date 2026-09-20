"""Mutation-test the R10 ledger-integrity check, CORRECTLY.

The first attempt copied the mutated script to /tmp and ran it with cwd=REPO. All three mutations
"failed" -- with the SAME spurious error, `only 0 runs carried an expect_n`, because the script
resolves the corpus relative to __file__ and from /tmp there is no corpus. A mutation table built
that way proves nothing: it is exactly BLOCKER-2's shape (a check whose result does not depend on
the thing it claims to test).

Fix: write the mutant BESIDE the original inside src/boombness/ so __file__ resolves identically,
run it, then remove it. Each mutation additionally asserts its pattern actually applied.
"""
import os, subprocess, sys

REPO = "/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
SRCP = os.path.join(REPO, "src/boombness/run_completeness_check.py")
MUTP = os.path.join(REPO, "src/boombness/_mut_rcc_tmp.py")
src = open(SRCP).read()

MUTATIONS = [
    ("BASELINE (no mutation)", src, "expect exit 0"),
    ("empty the ledger allowlist",
     src.replace('KNOWN_LEDGER_DISAGREEMENT = {\n    "d38beh',
                 'KNOWN_LEDGER_DISAGREEMENT = {}\n_unused_allowlist = {\n    "d38beh', 1),
     "d38beh must now be reported STALE -> exit 1"),
    ("neuter the comparison (always equal)",
     src.replace('det["rows_on_disk"] != ledger', 'False', 1),
     "no violation can ever be found -> exit 0 and 0 disagree"),
    ("neuter the _short_detail capture",
     src.replace('_short_detail[rid] = {"dir": d', '_short_detail_OFF = {"dir": d', 1),
     "nothing is re-measured -> '0 KNOWN_SHORT run(s) re-measured'"),
]

try:
    for lbl, mut, expect in MUTATIONS:
        if lbl != "BASELINE (no mutation)":
            assert mut != src, "%s: PATTERN DID NOT APPLY -- the mutation is a no-op" % lbl
        with open(MUTP, "w") as fh:
            fh.write(mut)
        r = subprocess.run([sys.executable, MUTP], cwd=REPO, capture_output=True, text=True)
        integ = [l for l in r.stdout.splitlines() if "exempted-run integrity" in l]
        stale = [l for l in r.stdout.splitlines() if "EXEMPTION STALE" in l]
        broke = [l for l in r.stdout.splitlines() if "The scanner has broken" in l]
        print("== %-38s exit=%d   (%s)" % (lbl, r.returncode, expect))
        if broke:
            print("   !! SPURIOUS: the scanner did not run -- this row proves NOTHING")
        if integ:
            print("   %s" % integ[0].strip()[len("[run-complete] "):][:120])
        for l in stale[:1]:
            print("   %s" % l.strip()[:120])
        if not integ and not broke:
            print("   (no integrity line emitted)")
finally:
    if os.path.exists(MUTP):
        os.remove(MUTP)
    print("\nmutant removed: %s" % (not os.path.exists(MUTP)))
