#!/usr/bin/env python3
"""Cross-job/node OVERLAP check for resumed P2b cells (PREREG AMENDMENT 5, rule S-084-style).

A primary cell whose arms come from two allocations (a preempted job + its resume, possibly on different nodes) is
only analysable if the two allocations produce the SAME numbers. The resume allocation re-runs a few arms that the
preempted allocation already completed, under distinct OVL tags the analyzer never reads; this script requires, per
pair, identical prompt_id sets and per-row max |dy_install| <= 1e-6 (and reports |d logp|), with the ORIGINAL dir
from the preempted job and the OVL dir from the resume job/node. Verdict OVERLAP_OK or OVERLAP_FAIL (=> the cell
is VOID).
"""
import argparse, importlib.util, json, math, os, sys

REPO = "/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
_s = importlib.util.spec_from_file_location("rederive", os.path.join(REPO, "scripts/dcs_csi_rederive_patch.py"))
rederive = importlib.util.module_from_spec(_s); _s.loader.exec_module(rederive)


def rows(d):
    out = {}
    for l in open(os.path.join(d, "results.jsonl")):
        r = json.loads(l)
        lc, lk = r["logp_concept"], r["logp_codeword"]
        m = max(lc, lk)
        out[r["prompt_id"]] = {"y": math.exp(lc - m) / (math.exp(lc - m) + math.exp(lk - m)), "lc": lc, "lk": lk}
    return out


def prov(d):
    m = json.load(open(os.path.join(d, "metadata.json")))
    return {"dir": os.path.basename(d), "slurm_job_id": m.get("slurm_job_id"), "host": m.get("hostname"), "gpu": m.get("gpu")}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prefix", required=True, help="analysed prefix, e.g. hcsi_p2b_basket_k4")
    ap.add_argument("--ovl-prefix", required=True, help="overlap prefix, e.g. hcsi_p2b_basket_k4ovl")
    ap.add_argument("--arms", required=True, help="comma list, e.g. KO,KO_CAND_r1,KO_RAND_r1_0,KO_DER_r1_0")
    ap.add_argument("--expect-n", type=int, required=True)
    ap.add_argument("--orig-job", required=True, help="slurm job id the ORIGINAL dirs must come from (preempted job)")
    ap.add_argument("--tol", type=float, default=1e-6)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    res, ok = [], True
    for arm in a.arms.split(","):
        o = rederive.strict_run_dir(f"{a.prefix}_{arm}", a.expect_n, row_file="results.jsonl")
        v = rederive.strict_run_dir(f"{a.ovl_prefix}_{arm}", a.expect_n, row_file="results.jsonl")
        po, pv = prov(o), prov(v)
        ro, rv = rows(o), rows(v)
        same = set(ro) == set(rv)
        dy = max(abs(ro[k]["y"] - rv[k]["y"]) for k in ro) if same else float("inf")
        dl = max(max(abs(ro[k]["lc"] - rv[k]["lc"]), abs(ro[k]["lk"] - rv[k]["lk"])) for k in ro) if same else float("inf")
        good = same and dy <= a.tol and po["slurm_job_id"] == a.orig_job and po["gpu"] == pv["gpu"] == "NVIDIA RTX A5000"
        ok &= good
        res.append({"arm": arm, "orig": po, "overlap": pv, "same_prompt_ids": same, "n": len(ro),
                    "max_abs_dy": dy, "max_abs_dlogp": dl, "ok": good})
        print(json.dumps(res[-1]))
    verdict = "OVERLAP_OK" if ok else "OVERLAP_FAIL"
    json.dump({"verdict": verdict, "tol": a.tol, "pairs": res}, open(a.out, "w"), indent=1)
    print(verdict)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
