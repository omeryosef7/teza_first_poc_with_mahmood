#!/usr/bin/env python3
"""Write/refresh outputs/heretic_csi/p6/stage0_<cw>.json on EVERY path of p6_stage0_batch.slurm (review #7 item 4):
status, each step's rc, readout/extract dirs with their own slurm jobs, the G3 JSON (+ explicit g3_status), G1 for
G3-passers with provenance (+ explicit g1_status: PASS iff CI95 lower > 0.05). Locked + atomic via p6_manifest_io
(review #8 item 3). A Stage-0 rerun does NOT bury G2 in previous_manifest: g2/g2_status are carried forward at top
level (G2 is computed from its own arms, independent of the Stage-0 readout); the axis record is carried forward only
if the extraction dir is unchanged (otherwise it is stale and goes to previous_manifest).
Usage: p6_write_manifest.py MAN CW STATUS --readout RD --extract XD --gate JSON --readout-rc RC --extract-rc RC --g1 JSON"""
import argparse, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import p6_manifest_io  # noqa: E402
ap = argparse.ArgumentParser()
ap.add_argument("man"); ap.add_argument("cw"); ap.add_argument("status")
for k in ("--readout", "--extract", "--gate", "--readout-rc", "--extract-rc", "--g1"):
    ap.add_argument(k, default="")
a = ap.parse_args()


def js(x):
    try:
        return json.loads(x) if x else None
    except Exception:
        return {"unparsed": x}


def build(prev):
    rjob = None
    if a.readout and os.path.exists(os.path.join(a.readout, "RUNMETA.json")):
        rjob = str(json.load(open(os.path.join(a.readout, "RUNMETA.json"))).get("slurm_job_id"))
    g3 = js(a.gate); g1 = js(a.g1)
    out = {"codeword": a.cw, "status": a.status, "batch_job": os.environ.get("SLURM_JOB_ID"),
           "rc": {"readout": a.readout_rc or None, "extract": a.extract_rc or None},
           "g3": g3, "g3_status": (g3 or {}).get("G3") if a.status in ("G3_PASS", "G3_FAIL", "ERROR_EXTRACT") else "UNDECIDED",
           "g1": g1, "g1_status": (("PASS" if g1["ci95"][0] > 0.05 else "FAIL") if isinstance(g1, dict) and "ci95" in g1 else
                                   ("NOT_APPLICABLE_G3_FAIL" if a.status == "G3_FAIL" else "UNDECIDED")),
           "g1_provenance": ({"script": "research/heretic_csi/p6_install_strength.py", "readout_dir": a.readout, "split": "train"} if g1 else None),
           "readout_dir": a.readout or None, "readout_slurm_job": rjob,
           "extract_dir": a.extract or None, "extract_realpath": os.path.realpath(a.extract) if a.extract else None,
           "extract_slurm_job": os.environ.get("SLURM_JOB_ID") if a.extract else None, "slurm_job": rjob}
    keep = dict(prev)
    for k in ("g2", "g2_status"):
        if k in keep:
            out[k] = keep.pop(k)
    if "axis" in keep and keep.get("extract_dir") and keep.get("extract_dir") == out["extract_dir"]:
        out["axis"] = keep.pop("axis")
    if "g2_status" not in out:
        out["g2_status"] = "NOT_APPLICABLE_G3_FAIL" if a.status == "G3_FAIL" else "UNDECIDED"
    keep.pop("previous_manifest", None)  # one level of history only (no unbounded nesting)
    out["previous_manifest"] = keep or None
    return out


p6_manifest_io.update(a.man, build)
