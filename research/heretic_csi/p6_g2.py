#!/usr/bin/env python3
"""P6 gate G2 (KO liveness) from the four arms of p6_g2.slurm (BASE / KO / KO_SELF / KO_FULL, tag hcsi_p6g2_<cw>_*),
selected strictly by RUNMETA slurm_job_id == --job + DONE (never recency). y_install = sigmoid(logp_concept −
logp_codeword) per row (frozen CSI readout); rows paired by prompt_id across arms; domain = unit (domain mean of paired
differences); 95% domain-cluster bootstrap (2000, seed 20261015).
G2 PASS iff KO−BASE CI95 upper < 0 AND KO_FULL−KO CI95 lower > 0 (PREREG_P6 gates_mechanical.G2). KO_SELF−KO reported
(identity sanity; should be ~0). Writes the result into outputs/heretic_csi/p6/stage0_<cw>.json["g2"] (+ prints JSON)."""
import argparse, glob, json, math, os, random, re, statistics, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import p6_pop, p6_manifest_io  # noqa: E402
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
# review #8: codeword guard on every arm + every arm must score EXACTLY the rescue BASE-arm TRAIN population
pop, expath = p6_pop.population(a.cw)
errors = []
for k, d in dirs.items():
    errors += p6_pop.bank_guard(d, a.cw)
Y = {k: load(v) for k, v in dirs.items()}
for k, v in Y.items():
    if set(v) != pop:
        errors.append(f"{k}: scored {len(v)} rows, population {len(pop)} (missing {len(pop - set(v))}, extra {len(set(v) - pop)})")
if not pop:
    errors.append("empty population")
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
res["population"] = {"exclusion_file": os.path.relpath(expath, REPO), "n": len(pop)}
val = {}
for k, d in dirs.items():
    rm = json.load(open(os.path.join(d, "RUNMETA.json")))
    val[k] = {"slurm_job_id": rm.get("slurm_job_id"), "done": os.path.exists(os.path.join(d, "DONE.json")),
              "rows": sum(1 for _ in open(os.path.join(d, "results.jsonl"))), "gpu": rm.get("gpu")}
ar = os.path.join(REPO, f"outputs/heretic_csi/p6/g2_arm_runner_{a.job}.json")
arj = json.load(open(ar)) if os.path.exists(ar) else {}
res["validation"] = {"arm_dirs": val, "single_gpu_type": len({v["gpu"] for v in val.values()}) == 1,
                     "arm_runner": {k: arj.get(k) for k in ("n_arms_requested", "n_arms_run", "n_ok", "n_model_loads", "hook_leak_detected")} if arj else None}
res["errors"] = errors
res["G2"] = ("ERROR" if errors else
             "PASS" if (res["KO_minus_BASE"]["ci95"][1] < 0 and res["KO_FULL_minus_KO"]["ci95"][0] > 0) else "FAIL")
man = os.path.join(REPO, f"outputs/heretic_csi/p6/stage0_{a.cw}.json")
p6_manifest_io.update(man, lambda m: {**m, "g2": res, "g2_status": res["G2"]})
rep = os.path.join(REPO, f"reports/heretic_csi/hcsi_p6_g2_{a.cw}.json")
if os.path.isdir(os.path.dirname(rep)):
    json.dump(res, open(rep, "w"), indent=1)
print(json.dumps(res))
