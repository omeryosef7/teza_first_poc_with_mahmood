#!/usr/bin/env python3
"""Primary endpoint for the interventional patch test (§44 #10): REFUSAL RECOVERY, domain-clustered.
Content-safe -- reads gens.jsonl, applies judge_boombness.kw_refusal (the phase's NATIVE keyword refusal
detector, the same field A4 used; NOT the OpenAI judge) to each generation, and emits ONLY refusal rates,
counts, and CIs. The generation text never leaves this process.

Arms (per codeword, never pooled): CTRL (no knockout), KO (A1 knockout), RESCUE_CLEAN (ko + rescue query
span from the clean forward). Decision rule (pre-declared CONT-167): if the knockout de-refuses
(refusal CTRL>KO) and RESCUE_CLEAN moves refusal materially from KO back toward CTRL, the query-side
representation carries the effect (§44 #10 PASS). Independence unit = DOMAIN: refusal is averaged within
domain first, then across domains, and the bootstrap resamples DOMAINS (dcs_cont_scope.domain_bootstrap).
Recovery fraction = (KO->RESCUE change) / (KO->CTRL change), reported with a domain bootstrap CI.
"""
from __future__ import annotations
import argparse, glob, importlib.util, json, os, sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load(mod, path):
    s = importlib.util.spec_from_file_location(mod, os.path.join(REPO, path))
    m = importlib.util.module_from_spec(s); sys.modules[mod] = m; s.loader.exec_module(m); return m


def latest_dir(tag):
    ds = sorted(glob.glob(os.path.join(REPO, "outputs/boombness/score_behavior", tag + "_*")))
    ds = [d for d in ds if os.path.exists(os.path.join(d, "gens.jsonl"))]
    if not ds:
        return None
    # prefer ones with DONE.json, else newest
    done = [d for d in ds if os.path.exists(os.path.join(d, "DONE.json"))]
    return (done or ds)[-1]


def load_arm(tag, kw_refusal):
    d = latest_dir(tag)
    if d is None:
        return None, None
    per = {}
    with open(os.path.join(d, "gens.jsonl")) as f:
        for line in f:
            r = json.loads(line)
            per[r["prompt_id"]] = {"domain": r["domain"], "refused": bool(kw_refusal(r["generation"])),
                                   "empty": not r["generation"].strip()}
    return d, per


def dom_rate(per, pids):
    """within-domain mean refusal, then across domains -> (rate, {domain: rate})."""
    by = {}
    for pid in pids:
        rec = per[pid]
        by.setdefault(rec["domain"], []).append(1.0 if rec["refused"] else 0.0)
    dr = {dm: sum(v) / len(v) for dm, v in by.items()}
    rate = sum(dr.values()) / len(dr) if dr else None
    return rate, dr


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--codeword", required=True, choices=("button", "basket"))
    ap.add_argument("--n-boot", type=int, default=20000)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    scope = _load("scope", "scripts/dcs_cont_scope.py")
    # the phase's NATIVE keyword refusal detector (judge_boombness.py:571 uses this same bj.kw_refusal)
    bj = _load("bnec", "doublespeak_causality/18_run_behavioral_necessity.py")
    kw = bj.kw_refusal

    arms = {}
    dirs = {}
    for arm, tag in (("ctrl", "patch_ctrl_%s" % a.codeword),
                     ("ko", "patch_ko_%s" % a.codeword),
                     ("rescue_clean", "patch_rescue_clean_%s" % a.codeword)):
        d, per = load_arm(tag, kw)
        dirs[arm] = d
        arms[arm] = per
        print("%-13s dir=%s rows=%s" % (arm, os.path.basename(d) if d else "MISSING",
                                        len(per) if per else 0))
    if any(arms[x] is None for x in arms):
        print("Not all arms present yet -- rerun when jobs finish."); return 2

    common = sorted(set(arms["ctrl"]) & set(arms["ko"]) & set(arms["rescue_clean"]))
    print("common prompt_ids across 3 arms:", len(common))
    doms = sorted({arms["ctrl"][p]["domain"] for p in common})
    print("domains:", len(doms))

    rates, drates = {}, {}
    for arm in arms:
        rates[arm], drates[arm] = dom_rate(arms[arm], common)

    def diff_stat(a1, a2):
        def stat(sample):
            n = d = 0.0
            for dm in sample:
                if dm in drates[a1] and dm in drates[a2]:
                    n += drates[a1][dm] - drates[a2][dm]; d += 1
            return (n / d) if d else None
        return stat

    def boot(a1, a2):
        try:
            b = scope.domain_bootstrap(doms, diff_stat(a1, a2), a.n_boot, seed=20260915, max_drop=0.10)
            return {"point": round(b["point"], 4), "ci": [round(b["lo"], 4), round(b["hi"], 4)],
                    "dropped": b["draws_dropped"]}
        except Exception as e:
            return {"error": str(e)[:80]}

    ko_deref = boot("ctrl", "ko")       # knockout de-refusal (expect > 0, replicates A4)
    recovery = boot("rescue_clean", "ko")  # rescue recovery (the test: expect > 0 if causal)
    resid = boot("ctrl", "rescue_clean")   # residual gap to ctrl

    # recovery fraction with a domain bootstrap
    def frac_stat(sample):
        num = den = 0.0; k = 0
        for dm in sample:
            if dm in drates["ctrl"] and dm in drates["ko"] and dm in drates["rescue_clean"]:
                num += drates["rescue_clean"][dm] - drates["ko"][dm]
                den += drates["ctrl"][dm] - drates["ko"][dm]; k += 1
        return (num / den) if den else None
    try:
        bf = scope.domain_bootstrap(doms, frac_stat, a.n_boot, seed=20260915, max_drop=0.20)
        frac = {"point": round(bf["point"], 3), "ci": [round(bf["lo"], 3), round(bf["hi"], 3)],
                "dropped": bf["draws_dropped"]}
    except Exception as e:
        frac = {"error": str(e)[:80]}

    out = {"schema": "dcs_cont_patch_endpoint/1", "codeword": a.codeword,
           "scope": "slot0 PRIMARY", "population": "train+val (TEST unspent)",
           "endpoint": "native kw_refusal, domain-clustered", "n_common": len(common), "n_domains": len(doms),
           "refusal_rate_by_arm": {k: round(v, 4) for k, v in rates.items()},
           "ko_derefusal_ctrl_minus_ko": ko_deref,
           "recovery_rescue_minus_ko": recovery,
           "residual_ctrl_minus_rescue": resid,
           "recovery_fraction": frac,
           "run_dirs": {k: os.path.basename(v) if v else None for k, v in dirs.items()}}
    outp = a.out or os.path.join(REPO, "reports/DCS_CONT_PATCH_ENDPOINT_%s.json" % a.codeword)
    json.dump(out, open(outp, "w"), indent=1)
    print(json.dumps({k: out[k] for k in ("refusal_rate_by_arm", "ko_derefusal_ctrl_minus_ko",
                                          "recovery_rescue_minus_ko", "recovery_fraction")}, indent=1))
    print("wrote", os.path.relpath(outp, REPO))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
