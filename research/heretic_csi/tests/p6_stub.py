#!/usr/bin/env python3
"""Stub for the branch test of p6_stage0_batch.slurm (tests/test_p6_stage0_batch_branches.sh). Replaces the three
python components that need a GPU or real data: `score` (readout), `extract`, `g3`. Behaviour per codeword comes from
STUB_PLAN="cw:mode,..." with modes: pass (readout rc=4 + G3_PASS + extraction OK), g3fail, health (OOM rows ->
ERROR_HEALTH), noreadout (readout crashes, no DONE dir), extractfail (G3_PASS but extraction leaves no DONE)."""
import json, os, sys, time
mode_of = dict(x.split(":") for x in os.environ.get("STUB_PLAN", "").split(",") if x)
job = os.environ.get("SLURM_JOB_ID", "stub")


def mk(path, done=True):
    os.makedirs(path, exist_ok=True)
    json.dump({"slurm_job_id": job}, open(os.path.join(path, "RUNMETA.json"), "w"))
    if done:
        open(os.path.join(path, "DONE.json"), "w").write("{}")


kind = sys.argv[1]; args = sys.argv[2:]
if kind == "score":
    tag = args[args.index("--tag") + 1]; cw = tag.split("_")[2]; m = mode_of.get(cw, "pass")
    d = f"outputs/boombness/score_behavior/{tag}_{time.strftime('%Y%m%d_%H%M%S')}_{os.getpid()}"
    if m == "noreadout":
        mk(d, done=False); sys.exit(1)
    mk(d); open(os.path.join(d, "plan.txt"), "w").write(m)
    sys.exit(4)  # score_behavior's pooled tail-gate rc, must be tolerated
if kind == "extract":
    tag = args[args.index("--tag") + 1]; cw = tag.split("_")[2]; m = mode_of.get(cw, "pass")
    d = f"outputs/boombness/extract_boombness/{tag}_{time.strftime('%Y%m%d_%H%M%S')}_{os.getpid()}"
    mk(d, done=(m != "extractfail")); sys.exit(0 if m != "extractfail" else 1)
if kind == "g1":
    print(json.dumps({"codeword": args[0], "split": "train", "install_strength_C_minus_A": 0.5, "ci95": [0.4, 0.6]}))
    sys.exit(0)
if kind == "g3":
    cw, rd = args[0], args[1]
    m = open(os.path.join(rd, "plan.txt")).read().strip() if os.path.exists(os.path.join(rd, "plan.txt")) else "g3fail"
    st = {"pass": "G3_PASS", "extractfail": "G3_PASS", "g3fail": "G3_FAIL", "health": "ERROR_HEALTH"}.get(m, "G3_FAIL")
    print(json.dumps({"codeword": cw, "readout_dir": rd, "status": st, "G3": "PASS" if st == "G3_PASS" else "FAIL"}))
