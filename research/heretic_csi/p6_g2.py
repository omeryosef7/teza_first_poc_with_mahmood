#!/usr/bin/env python3
"""P6 gate G2 (KO liveness) from the four arms of p6_g2.slurm (BASE / KO / KO_SELF / KO_FULL, tag hcsi_p6g2_<cw>_*),
selected strictly by RUNMETA slurm_job_id == --job + DONE (never recency). y_install = sigmoid(logp_concept −
logp_codeword) per row (frozen CSI readout); rows paired by prompt_id across arms; domain = unit (domain mean of paired
differences); 95% domain-cluster bootstrap (2000, seed 20261015).
G2 PASS iff KO−BASE CI95 upper < 0 AND KO_FULL−KO CI95 lower > 0 (PREREG_P6 gates_mechanical.G2). KO_SELF−KO reported
(identity sanity; should be ~0). Writes the result into outputs/heretic_csi/p6/stage0_<cw>.json["g2"] (+ prints JSON)."""
import argparse, glob, json, math, os, random, re, statistics, sys
REPO = os.environ.get("P6_REPO", "/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood")  # override only for tests/test_p6_g2.py
ap = argparse.ArgumentParser(); ap.add_argument("cw"); ap.add_argument("--job", required=True); a = ap.parse_args()


def pick(arm):
    hits = []
    pat = re.compile(rf"^hcsi_p6g2_{re.escape(a.cw)}_{arm}_\d{{8}}_\d{{6}}_\d+$")  # exact tag (KO must not match KO_SELF/KO_FULL)
    for d in glob.glob(os.path.join(REPO, f"outputs/boombness/score_behavior/hcsi_p6g2_{a.cw}_{arm}_*")):
        if not pat.match(os.path.basename(d)):
            continue
        try:
            m = json.load(open(os.path.join(d, "RUNMETA.json")))
        except Exception:
            continue
        if str(m.get("slurm_job_id")) == a.job and os.path.exists(os.path.join(d, "DONE.json")):
            hits.append(d)
    if len(hits) != 1:
        sys.exit(f"G2: {a.cw} {arm}: expected exactly 1 DONE dir for job {a.job}, got {hits}")
    return hits[0]


def load(d):
    out = {}
    for l in open(os.path.join(d, "results.jsonl")):
        r = json.loads(l)
        if r.get("logp_concept") is None or r.get("logp_codeword") is None:
            continue
        out[r["prompt_id"]] = (r["domain"], 1 / (1 + math.exp(-(r["logp_concept"] - r["logp_codeword"]))))
    return out


dirs = {k: pick(k) for k in ("BASE", "KO", "KO_SELF", "KO_FULL")}
Y = {k: load(v) for k, v in dirs.items()}
keys = sorted(set.intersection(*(set(v) for v in Y.values())))


def contrast(hi, lo):
    by = {}
    for k in keys:
        by.setdefault(Y[hi][k][0], []).append(Y[hi][k][1] - Y[lo][k][1])
    dm = {d: statistics.mean(v) for d, v in by.items()}
    ds = sorted(dm); rng = random.Random(20261015)
    bs = sorted(statistics.mean(dm[rng.choice(ds)] for _ in ds) for _ in range(2000))
    return {"point": round(statistics.mean(dm.values()), 5), "ci95": [round(bs[49], 5), round(bs[1949], 5)], "n_domains": len(ds)}


res = {"codeword": a.cw, "job": a.job, "n_paired_rows": len(keys), "arms": {k: os.path.relpath(v, REPO) for k, v in dirs.items()},
       "KO_minus_BASE": contrast("KO", "BASE"), "KO_FULL_minus_KO": contrast("KO_FULL", "KO"),
       "KO_SELF_minus_KO": contrast("KO_SELF", "KO")}
res["G2"] = "PASS" if (res["KO_minus_BASE"]["ci95"][1] < 0 and res["KO_FULL_minus_KO"]["ci95"][0] > 0) else "FAIL"
man = os.path.join(REPO, f"outputs/heretic_csi/p6/stage0_{a.cw}.json")
m = json.load(open(man)); m["g2"] = res; json.dump(m, open(man, "w"), indent=1)
print(json.dumps(res))
