"""Mutation-test the R10 MAJOR-10 fix, the RIGHT way (beside the original, so __file__ resolves)."""
import os, subprocess, sys

REPO = "/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
SRCP = os.path.join(REPO, "scripts/gates/dcs_csi_pr005_gate0.py")
MUTP = os.path.join(REPO, "scripts/gates/_mut_gate0_tmp.py")
src = open(SRCP).read()

MUTATIONS = [
    ("BASELINE", src, "expect 0(a) PASS, 54 inspected"),
    ("drop 4 stage-1 arms from the list",
     src.replace('+ ["KO_SHUF%d" % i for i in range(0, 4)])', '+ [])', 1),
     "54 -> 50 inspected; the OLD assert (n>=50) would still pass"),
    ("point stage-1 at a nonexistent job",
     src.replace('STAGE1_JOBS = ["902004", "902005"]', 'STAGE1_JOBS = ["902004"]', 1),
     "some stage-1 arms unresolved"),
]

try:
    for lbl, mut, expect in MUTATIONS:
        if lbl != "BASELINE":
            assert mut != src, "%s: PATTERN DID NOT APPLY" % lbl
        open(MUTP, "w").write(mut)
        r = subprocess.run([sys.executable, MUTP], cwd=REPO, capture_output=True, text=True)
        out = r.stdout + r.stderr
        insp = [l for l in out.splitlines() if "inspected" in l or "UNRESOLVED" in l]
        err = [l for l in out.splitlines() if "MAJOR-10" in l or "AssertionError" in l]
        print("== %-38s exit=%d  (%s)" % (lbl, r.returncode, expect))
        for l in insp[:2]:
            print("     %s" % l.strip()[:120])
        for l in err[:1]:
            print("     %s" % l.strip()[:150])
finally:
    if os.path.exists(MUTP):
        os.remove(MUTP)
    print("\nmutant removed: %s" % (not os.path.exists(MUTP)))
