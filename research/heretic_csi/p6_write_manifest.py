#!/usr/bin/env python3
"""Write/refresh outputs/heretic_csi/p6/stage0_<cw>.json on EVERY path of p6_stage0_batch.slurm (review #7 item 4):
status, each step's rc, readout/extract dirs with their own slurm jobs, the G3 JSON, G1 (installer strength) for
G3-passers with its provenance; previous manifest kept under previous_manifest (never silently overwritten).
Usage: p6_write_manifest.py MAN CW STATUS --readout RD --extract XD --gate JSON --readout-rc RC --extract-rc RC --g1 JSON"""
import argparse, json, os
ap = argparse.ArgumentParser()
ap.add_argument("man"); ap.add_argument("cw"); ap.add_argument("status")
for k in ("--readout", "--extract", "--gate", "--readout-rc", "--extract-rc", "--g1"):
    ap.add_argument(k, default="")
a = ap.parse_args()
prev = json.load(open(a.man)) if os.path.exists(a.man) else {}
rjob = None
if a.readout and os.path.exists(os.path.join(a.readout, "RUNMETA.json")):
    rjob = str(json.load(open(os.path.join(a.readout, "RUNMETA.json"))).get("slurm_job_id"))
def js(x):
    try:
        return json.loads(x) if x else None
    except Exception:
        return {"unparsed": x}
out = {"codeword": a.cw, "status": a.status, "batch_job": os.environ.get("SLURM_JOB_ID"),
       "rc": {"readout": a.readout_rc or None, "extract": a.extract_rc or None},
       "g3": js(a.gate), "g1": js(a.g1),
       "g1_provenance": ({"script": "research/heretic_csi/p6_install_strength.py", "readout_dir": a.readout, "split": "train"} if a.g1 else None),
       "readout_dir": a.readout or None, "readout_slurm_job": rjob,
       "extract_dir": a.extract or None, "extract_realpath": os.path.realpath(a.extract) if a.extract else None,
       "extract_slurm_job": os.environ.get("SLURM_JOB_ID") if a.extract else None,
       "slurm_job": rjob, "previous_manifest": prev or None}
json.dump(out, open(a.man, "w"), indent=1)
