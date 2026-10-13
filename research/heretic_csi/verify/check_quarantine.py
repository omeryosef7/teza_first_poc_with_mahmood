#!/usr/bin/env python3
"""F3: independently verify the parent's preemption-quarantine rule using the job logs (final attempt) as ground truth."""
import json, os, re, glob, collections
ROOT = "/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
SB = f"{ROOT}/outputs/boombness/score_behavior"
JOBS = [966084, 965928, 966157, 966158, 968532, 968533, 968534, 968535, 969085, 969086, 969087, 969088]
def jobid(d):
    for f in ("metadata.json", "RUNMETA.json"):
        p = os.path.join(d, f)
        if os.path.exists(p):
            try:
                v = json.load(open(p)).get("slurm_job_id")
                if v: return str(v)
            except Exception: pass
    return None
by_job = collections.defaultdict(list)
for d in glob.glob(f"{SB}/hcsi_p2a_*") + glob.glob(f"{SB}/_preempted_attempts/hcsi_p2a_*"):
    j = jobid(d)
    if j: by_job[j].append(d)
out = {}
for j in JOBS:
    logged = set()
    for ln in open(f"{ROOT}/outputs/heretic_csi/logs/sweep_{j}.out"):
        m = re.match(r"\[score\] \{'semantic': \d+\} -> (\S+)", ln.strip())
        if m: logged.add(os.path.basename(m.group(1)))
    dirs = by_job[str(j)]
    live = {os.path.basename(d) for d in dirs if "_preempted_attempts" not in d}
    quar = {os.path.basename(d) for d in dirs if "_preempted_attempts" in d}
    arms_live = collections.Counter(json.load(open(os.path.join(SB, b, "config.json")))["args"]["arm"] for b in live)
    out[j] = {"n_logged": len(logged), "n_live_same_jobid": len(live), "n_quarantined": len(quar),
              "live_eq_logged": live == logged, "quarantined_intersect_logged": len(quar & logged),
              "live_not_logged": sorted(live - logged)[:5], "logged_missing": sorted(logged - live)[:5],
              "dup_arms_live": [a for a, c in arms_live.items() if c > 1],
              "quar_all_DONE": sum(os.path.exists(os.path.join(SB, "_preempted_attempts", b, "DONE.json")) for b in quar)}
    print(j, out[j])
json.dump(out, open(f"{ROOT}/reports/heretic_csi/VERIFY_S049_quarantine_check.json", "w"), indent=1)
