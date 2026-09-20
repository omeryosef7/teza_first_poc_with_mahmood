"""PR-CSI-005 Part 2 -- gates 0(a), 0(b), 0(c), 0(f), run BEFORE any number is read.

Gate 0(d), the code-identity anchor, is a separate script (dcs_csi_pr005_gate0d.py) and already
PASSED (sprint entry S-134). Gate 0(e) -- "no interim read" -- is procedural and is enforced by this
script refusing to report anything if the family is incomplete.

EVERY CHECK PRINTS THE SIZE OF ITS COMPARISON AND ASSERTS THAT SIZE FIRST (sprint entry S-134: a gate
that can pass on an empty comparison is not a gate). Counting run DIRECTORIES is NOT counting finished
arms -- a directory exists from the moment an arm starts; DONE.json is what says it finished. That
distinction is P0.4's whole subject.
"""
import json, os, glob, re, sys

REPO = "/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
SB = os.path.join(REPO, "outputs/boombness/score_behavior")
LOGS = os.path.join(REPO, "outputs/boombness/logs")

NEW_JOBS = ["912835", "912836", "912837"]          # I1, I2, K
STAGE1_JOBS = ["902004", "902005"]
NEW_ARMS = ["KO_RAND%d" % i for i in range(6, 22)] + ["KO_SHUF%d" % i for i in range(4, 24)]
STAGE1_ARMS = (["BASE", "KO", "KO_SELF", "KO_FULL", "KO_AXIS", "KO_PLS", "KO_ORTH",
                "KO_AXIS_ANCHOR"] + ["KO_RAND%d" % i for i in range(0, 6)]
               + ["KO_SHUF%d" % i for i in range(0, 4)])
EXPECT_N, ALLOW_SHORT = 670, 4
OUT_PATHS = ["reports/DCS_CSI_SUBSPACE_button_train_L18_n46.json",
             "reports/DCS_CSI_REDERIVE_button_train_L18_n46.json",
             "reports/DCS_CSI_SUBSPACE_button_train_L18_shufonly.json"]

fail = []


def newest(arm, jobs):
    """The run dir for `arm` whose RUNMETA job id is in `jobs`. Never 'the newest dir'."""
    hits = []
    for d in glob.glob(os.path.join(SB, "csi1_button_train_%s_2026*" % arm)):
        rm = os.path.join(d, "RUNMETA.json")
        if not os.path.exists(rm):
            continue
        if str(json.load(open(rm)).get("slurm_job_id")) in jobs:
            hits.append(d)
    return sorted(hits)[-1] if hits else None


print("=" * 96)
print("GATE 0(c) -- the family is COMPLETE and no arm collapsed")
finished, unfinished, rows = [], [], {}
for a in NEW_ARMS:
    d = newest(a, NEW_JOBS)
    if d is None:
        unfinished.append((a, "no run dir from jobs %s" % ",".join(NEW_JOBS))); continue
    p = os.path.join(d, "DONE.json")
    if not os.path.exists(p):
        unfinished.append((a, "no DONE.json -- STILL WRITING")); continue
    j = json.load(open(p))
    finished.append(a); rows[a] = j.get("rows_written", 0)
print("  36 expected | %d FINISHED (DONE.json present) | %d not finished" % (len(finished), len(unfinished)))
for a, why in unfinished:
    print("     NOT FINISHED: %-12s %s" % (a, why))
if unfinished:
    print("\nREFUSING TO EVALUATE THE REMAINING GATES: the family is incomplete.")
    print("PR-CSI-005 Part 2 clause (e) forbids an interim read by name. Re-run when all 36 have")
    print("a DONE.json. (Counting run DIRECTORIES would have said 'all 36 present' -- they exist")
    print("from the moment an arm starts. DONE.json is what says it FINISHED.)")
    sys.exit(2)

zero = [a for a in finished if rows[a] == 0]
collapsed = [(a, rows[a]) for a in finished if rows[a] < EXPECT_N - ALLOW_SHORT]
print("  rows: min=%d max=%d | zero-row arms=%d | below %d (allow-short %d)=%d"
      % (min(rows.values()), max(rows.values()), len(zero), EXPECT_N - ALLOW_SHORT, ALLOW_SHORT, len(collapsed)))
if zero:
    print("     ZERO-ROW (the V100 degeneracy signature even if the GPU string says otherwise): %s" % zero)
if collapsed:
    print("     SHORT BEYOND allow-short -- prereg says RE-RUN via group X, never drop: %s" % collapsed)
print("  GATE 0(c): %s" % ("PASS" if not zero and not collapsed else "FAIL"))
if zero or collapsed:
    fail.append("0c")

print("=" * 96)
print("GATE 0(a) -- architecture pin, from the RUNS not from the sbatch line")
gpus, n = {}, 0
for a in NEW_ARMS:
    d = newest(a, NEW_JOBS)
    g = json.load(open(os.path.join(d, "RUNMETA.json"))).get("gpu")
    gpus[g] = gpus.get(g, 0) + 1; n += 1
for a in STAGE1_ARMS:
    d = newest(a, STAGE1_JOBS)
    if d is None:
        continue
    g = json.load(open(os.path.join(d, "RUNMETA.json"))).get("gpu")
    gpus[g] = gpus.get(g, 0) + 1; n += 1
assert n >= 50, "only %d run dirs inspected -- selector broken, not a result" % n
print("  inspected %d run dirs (36 new + %d stage-1)" % (n, n - 36))
for g, c in sorted(gpus.items(), key=lambda kv: -kv[1]):
    print("     %-34r %d" % (g, c))
ok_a = set(gpus) == {"NVIDIA GeForce RTX 3090"}
print("  GATE 0(a): %s" % ("PASS -- every admitted run is RTX 3090" if ok_a else "FAIL -- other GPU present => VOID, family is RE-RUN not patched"))
if not ok_a:
    fail.append("0a")

print("=" * 96)
print("GATE 0(b) -- no [layer-override] in the three NEW job logs; banner LAYER=18 RANK=5")
checked = 0
for j in NEW_JOBS:
    fs = glob.glob(os.path.join(LOGS, "csi_p1_%s.out" % j)) + glob.glob(os.path.join(LOGS, "csi_p1_%s.err" % j))
    assert fs, "no log file found for job %s" % j
    txt = "".join(open(f, errors="replace").read() for f in fs)
    checked += 1
    ov = "[layer-override]" in txt
    ban = re.findall(r"LAYER=(\d+)\s+RANK=(\d+)", txt)
    print("     job %s: layer-override=%s  banner=%s" % (j, ov, ban[:1] or "NOT FOUND"))
    if ov:
        fail.append("0b:%s override" % j)
    if not ban or ban[0] != ("18", "5"):
        fail.append("0b:%s banner" % j)
assert checked == 3, "checked %d logs, expected 3" % checked
print("  GATE 0(b): %s" % ("PASS" if not [f for f in fail if f.startswith("0b")] else "FAIL"))

print("=" * 96)
print("GATE 0(f) -- output paths must NOT exist")
for p in OUT_PATHS:
    ex = os.path.exists(os.path.join(REPO, p))
    print("     %-58s exists=%s" % (p, ex))
    if ex:
        fail.append("0f:%s" % p)
print("  checked %d paths" % len(OUT_PATHS))
print("  GATE 0(f): %s" % ("PASS" if not [f for f in fail if f.startswith("0f")] else "FAIL"))

print("=" * 96)
print("PART 2 VERDICT: %s" % ("ALL GATES PASS -- Part 3 may be run ONCE, as written"
                              if not fail else "FAIL -> %s" % fail))
sys.exit(0 if not fail else 1)
