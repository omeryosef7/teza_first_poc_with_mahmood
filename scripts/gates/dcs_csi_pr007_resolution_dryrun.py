"""PR-CSI-007 RESOLUTION DRY-RUN -- exercise the anti-corruption mechanism against REAL duplicates.

Three cancelled generations left arms on disk carrying the SAME TAGS as in-family arms (S-147/S-148).
Measured 2026-09-21: KO_AXIS_ANCHOR exists under 914044 (cancelled) AND 914476 (in-family); KO_RAND6
under 914045 AND 914477; KO_RAND12 and KO_SHUF12 duplicate as 914478/914479 run. That is the
S-104/S-127 duplicate-tag hazard, live.

The only thing standing between that and a corrupted family is the read's `resolve()`: filter the tag
glob by RUNMETA.slurm_job_id and assert at most one hit. This script runs THAT EXACT LOGIC against the
current on-disk state and checks two directions rather than one:

   (1) every in-family arm resolves to exactly one dir, under the job it should belong to;
   (2) NO cancelled-generation dir is ever selected.

(2) is the half a passing (1) would hide: a resolver that returned the newest dir would also satisfy
(1) whenever the in-family arm happened to be newer, which it usually is.

READS ONLY RUNMETA.json. No results.jsonl, no summary, no scientific number -- this is safe to run
while the family is still in flight, which is the whole point of running it now.
"""
import json, os, glob, sys, collections

REPO = "/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
os.chdir(REPO)
SB = "outputs/boombness/score_behavior"

JOB_A, JOB_B, JOB_I1, JOB_I2, JOB_K, JOB_SW = "914043", "914476", "914477", "914478", "914479", "914048"
CANCELLED = ["914044", "914045", "914046", "914047", "914417", "914418", "914419", "914420",
             "914472", "914473", "914474", "914475"]

GROUP = {
    JOB_A:  ["BASE", "KO", "KO_SELF", "KO_FULL", "KO_AXIS", "KO_PLS", "KO_ORTH"],
    JOB_B:  ["KO_AXIS_ANCHOR"] + ["KO_SHUF%d" % i for i in range(4)] + ["KO_RAND%d" % i for i in range(6)],
    JOB_I1: ["KO_RAND%d" % i for i in range(6, 12)] + ["KO_SHUF%d" % i for i in range(4, 10)],
    JOB_I2: ["KO_RAND%d" % i for i in range(12, 22)] + ["KO_SHUF%d" % i for i in range(10, 12)],
    JOB_K:  ["KO_SHUF%d" % i for i in range(12, 24)],
}
fail = []


def resolve(arm, job):
    """VERBATIM the read's resolver (runargs/dcs_csi_pr007_read.txt:314-319)."""
    hits = [d for d in glob.glob(os.path.join(SB, "csi1_button_validation_%s_2026*" % arm))
            if os.path.exists(os.path.join(d, "RUNMETA.json"))
            and str(json.load(open(os.path.join(d, "RUNMETA.json"))).get("slurm_job_id")) == job]
    assert len(hits) <= 1, "arm %s resolves to %d dirs under job %s -- ambiguous" % (arm, len(hits), job)
    return hits[0] if hits else None


def job_of(d):
    rm = os.path.join(d, "RUNMETA.json")
    if not os.path.exists(rm):
        return None
    return str(json.load(open(rm)).get("slurm_job_id"))


allarms = [(a, j) for j in GROUP for a in GROUP[j]]
print("[dryrun] SIZE family = %d arms across %d jobs" % (len(allarms), len(GROUP)))
if len(allarms) != 54:
    sys.exit("EXPECTED 54 arms, the GROUP map holds %d -- refusing to dry-run a wrong family" % len(allarms))

# ---- the duplicate census: what is actually on disk right now -------------------------------
tags = collections.defaultdict(list)
for d in sorted(glob.glob(os.path.join(SB, "csi1_button_validation_*_2026*"))):
    if not os.path.exists(os.path.join(d, "DONE.json")):
        continue
    arm = os.path.basename(d)[len("csi1_button_validation_"):].rsplit("_2026", 1)[0]
    tags[arm].append((job_of(d), d))
dups = {a: v for a, v in tags.items() if len(v) > 1}
print("[dryrun] tags on disk: %d | DUPLICATED tags: %d %s"
      % (len(tags), len(dups), sorted(dups)))
if not dups:
    print("[dryrun] NOTE: no duplicate exists on disk yet, so direction (2) is untested this run.")

# ---- (1) every landed in-family arm resolves to exactly one, correct, dir --------------------
resolved, missing = {}, []
for arm, job in allarms:
    try:
        d = resolve(arm, job)
    except AssertionError as e:
        fail.append("AMBIGUOUS: %s" % e)
        continue
    if d is None:
        missing.append((arm, job))
        continue
    got = job_of(d)
    if got != job:
        fail.append("WRONG JOB: %s resolved to %s which is job %s, expected %s" % (arm, d, got, job))
    resolved[arm] = d
print("[dryrun] resolved %d arms | not yet on disk %d (jobs still running/pending)"
      % (len(resolved), len(missing)))

# ---- (2) NO cancelled-generation dir was selected -- the half (1) would hide -----------------
selected_jobs = collections.Counter(job_of(d) for d in resolved.values())
print("[dryrun] selected dirs by job: %s" % dict(selected_jobs))
bad = sorted(set(selected_jobs) & set(CANCELLED))
if bad:
    fail.append("A CANCELLED-GENERATION JOB WAS SELECTED: %s" % bad)

# and prove the cancelled dirs exist and were correctly passed over
on_disk_cancelled = [(a, j, d) for a, v in tags.items() for (j, d) in v if j in CANCELLED]
print("[dryrun] cancelled-generation dirs present on disk: %d" % len(on_disk_cancelled))
for a, j, d in sorted(on_disk_cancelled):
    picked = resolved.get(a)
    state = "correctly NOT selected" if picked != d else "*** SELECTED -- CORRUPTION ***"
    if picked == d:
        fail.append("cancelled dir selected for arm %s: %s" % (a, d))
    print("     job %s  arm %-16s %s" % (j, a, state))

if not on_disk_cancelled:
    print("[dryrun] NOTE: no cancelled dir on disk, so direction (2) is vacuous this run.")

print()
if fail:
    print("=== DRY-RUN FAILURES ===")
    for f in fail:
        print("   -", f)
    sys.exit(1)
print("=== DRY-RUN PASS: %d arms resolved, 0 cancelled-generation dirs selected, %d duplicate tag(s) "
      "correctly disambiguated ===" % (len(resolved), len(dups)))
