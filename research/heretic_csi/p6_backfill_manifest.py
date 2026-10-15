#!/usr/bin/env python3
"""One-off backfill (review #7 item 4) for G3-passers whose Stage-0/axisfit ran BEFORE the manifest upgrade: add
axis {path, sha256 (recomputed), axisfit_job (from the axisfit log)} and G1 (re-computed by p6_install_strength.py on the
manifest's readout dir, provenance recorded). Never changes status, readout or extract fields."""
import glob, hashlib, json, os, re, subprocess, sys
REPO = "/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
PY = "/home/sharifm/students/omeryosef/miniconda3/envs/poc_stage2/bin/python"
for cw in sys.argv[1:]:
    man = os.path.join(REPO, f"outputs/heretic_csi/p6/stage0_{cw}.json"); m = json.load(open(man))
    assert m["status"] == "G3_PASS", (cw, m["status"])
    ax = f"/specific/scratches/scratch/omeryosef/hcsi_p6/axes/hcsi_p6_axis_{cw}.pt"
    if os.path.exists(ax) and "axis" not in m:
        sha = hashlib.sha256(open(ax, "rb").read()).hexdigest()
        job = None
        for log in glob.glob(os.path.join(REPO, "outputs/heretic_csi/logs/p6axis_*.out")):
            if f"DONE_MARKER p6_axisfit cw={cw} " in open(log).read():
                job = re.search(r"p6axis_(\d+)\.out", log).group(1)
        m["axis"] = {"path": ax, "sha256": sha, "axisfit_job": job, "backfilled": True}
    if not m.get("g1"):
        g1 = subprocess.check_output([PY, os.path.join(REPO, "research/heretic_csi/p6_install_strength.py"), cw, m["readout_dir"], "train"], cwd=REPO).decode()
        m["g1"] = json.loads(g1); m["g1_provenance"] = {"script": "research/heretic_csi/p6_install_strength.py", "readout_dir": m["readout_dir"], "split": "train", "backfilled": True}
    json.dump(m, open(man, "w"), indent=1)
    print(cw, m["status"], m.get("axis", {}).get("sha256", "")[:12], m.get("axis", {}).get("axisfit_job"), m["g1"]["install_strength_C_minus_A"], m["g1"]["ci95"])
