#!/usr/bin/env python3
"""Select THE run dir of a given experiment/tag produced by THIS SLURM job (never by recency): RUNMETA slurm_job_id
must equal --job, and DONE.json must exist. Exactly one match required, else exit 2 (prevents stale/partial dirs from
preempted attempts — e.g. ts116m_readout_candle_bomb_20261014_171043_2895750 of preempted 1039942 — being used).
--verify DIR checks an already-chosen dir the same way (used by p6_axisfit on the Stage-0 manifest)."""
import argparse, glob, json, os, sys


def ok(d, job):
    try:
        m = json.load(open(os.path.join(d, "RUNMETA.json")))
    except Exception:
        return False
    return str(m.get("slurm_job_id")) == str(job) and os.path.exists(os.path.join(d, "DONE.json"))


ap = argparse.ArgumentParser()
ap.add_argument("--job", required=True)
ap.add_argument("--glob")
ap.add_argument("--verify")
a = ap.parse_args()
if a.verify:
    sys.exit(0 if ok(os.path.realpath(a.verify), a.job) else 2)
hits = [d for d in glob.glob(a.glob) if os.path.isdir(d) and not os.path.islink(d) and ok(d, a.job)]
if len(hits) != 1:
    print(f"SELECT_RUN_FAILED job={a.job} glob={a.glob} matches={hits}", file=sys.stderr); sys.exit(2)
print(hits[0])
