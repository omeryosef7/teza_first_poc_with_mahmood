#!/usr/bin/env python3
"""Can this phase's data discriminate the ONE-SWITCH account from the gating account?

REVIEW-8/OUTPUT_SCIENTIFIC named the single strongest reason to doubt the phase's
mechanistic story, and observed it had never been tested against:

  ONE-SWITCH : installation gates whether the request is interpreted as a bomb
               request at all. Refusal and bomb content are BOTH downstream, so
               the knockout should reduce BOTH by a similar PROPORTION.
  GATING     : installation gates the safety response specifically. The knockout
               reduces refusal and leaves content-true alone.

These make opposite predictions about ONE number: the content-true ratio ko/ctrl.

  ONE-SWITCH predicts it lands near the refusal ratio (~0.36, a ~64% drop).
  GATING     predicts it lands near 1.0 (no change).

This script estimates that ratio with a domain-clustered interval and asks which
of the two the data can exclude. It is written expecting the answer "neither" --
the point is to replace "never tested" with a measured interval and an n.

Scope and population are explicit via filter_rows (C-CONT-093/094).
"""
from __future__ import annotations
import argparse, collections, importlib.util, json, math, os, random, re, sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "scripts"))
from dcs_cont_scope import Scope, Population, filter_rows   # noqa: E402

KO = "outputs/boombness/judge/casrHW_ko_20260912_143556_3731257"
CT = "outputs/boombness/judge/casrHW_ctrlHW_20260912_143556_3732504"


def _load(mod, path):
    s = importlib.util.spec_from_file_location(mod, os.path.join(REPO, path))
    m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m


def read(run, scope, pop, assign, cp, MAT, SCOPE_RE):
    d = os.path.join(REPO, run)
    gens = {}
    for L in open(json.load(open(os.path.join(d, "summary.json")))["gens"]):
        r = json.loads(L); gens[r["prompt_id"]] = r["generation"]
    raw = [json.loads(L) for L in open(os.path.join(d, "results.jsonl"))]
    kept, prov = filter_rows(raw, scope, pop, assign)
    out = {}
    for r in kept:
        t = gens.get(r["prompt_id"])
        if t is None:
            continue
        q = r["strongreject_score"] >= 0.5
        cr2 = q and bool(cp.concept_hits(t)) and bool(MAT.search(t)) and not SCOPE_RE.search(t)
        out[r["prompt_id"]] = (r["domain"], 1.0 if r["refused"] else 0.0, 1.0 if cr2 else 0.0)
    return out, prov


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=20260912)
    ap.add_argument("--n-boot", type=int, default=20000)
    ap.add_argument("--out", default=os.path.join(REPO, "reports/DCS_CONT_ONESWITCH.json"))
    a = ap.parse_args()

    assign = _load("lpm", "scripts/dcs_cont_layerpos_map.py").load_split()
    cp = _load("cp", "scripts/dcs_succ_concept_presence.py")
    rule = json.load(open(os.path.join(REPO, "configs/dcs_cont_content_rule_v2.json")))
    if rule.get("status") != "FROZEN":
        print("REFUSING: content rule not FROZEN"); return 2
    MAT = re.compile(rule["MATERIAL"], re.I); SCOPE_RE = re.compile(rule["SCOPE"], re.I)

    out = {"question": "can the data exclude ONE-SWITCH or GATING?", "seed": a.seed, "by_scope": {}}
    for scope in (Scope.ALL_SLOTS, Scope.PRIMARY):
        ko, prov = read(KO, scope, Population.TRAIN_VAL, assign, cp, MAT, SCOPE_RE)
        ct, _ = read(CT, scope, Population.TRAIN_VAL, assign, cp, MAT, SCOPE_RE)
        shared = sorted(set(ko) & set(ct))
        doms = collections.defaultdict(lambda: [0.0, 0.0, 0.0, 0.0])  # koR koC ctR ctC
        for p in shared:
            d = ko[p][0]
            doms[d][0] += ko[p][1]; doms[d][1] += ko[p][2]
            doms[d][2] += ct[p][1]; doms[d][3] += ct[p][2]
        dl = sorted(doms)

        def ratios(sample):
            kR = sum(doms[d][0] for d in sample); kC = sum(doms[d][1] for d in sample)
            cR = sum(doms[d][2] for d in sample); cC = sum(doms[d][3] for d in sample)
            return (kR / cR if cR else float("nan"), kC / cC if cC else float("nan"))
        pR, pC = ratios(dl)
        g = random.Random(a.seed); bR, bC = [], []
        for _ in range(a.n_boot):
            s = [dl[g.randrange(len(dl))] for _ in dl]
            r1, r2 = ratios(s)
            if not math.isnan(r1): bR.append(r1)
            if not math.isnan(r2): bC.append(r2)
        bR.sort(); bC.sort()
        q = lambda v, f: v[int(f * len(v))]
        cLo, cHi = q(bC, .025), q(bC, .975)
        rLo, rHi = q(bR, .025), q(bR, .975)
        kC = sum(doms[d][1] for d in dl); cC = sum(doms[d][3] for d in dl)
        print("\n=== %s  (%d domains, %d prompt pairs) ===" % (scope.name, len(dl), len(shared)))
        print("  refusal      ratio ko/ctrl = %.3f  [%.3f, %.3f]   (%d -> %d events)"
              % (pR, rLo, rHi, sum(doms[d][2] for d in dl), sum(doms[d][0] for d in dl)))
        print("  content-true ratio ko/ctrl = %.3f  [%.3f, %.3f]   (%d -> %d events)"
              % (pC, cLo, cHi, cC, kC))
        excl_one = not (cLo <= pR <= cHi)
        excl_gate = not (cLo <= 1.0 <= cHi)
        print("  ONE-SWITCH predicts content-true ratio ~= refusal ratio %.3f -> %s"
              % (pR, "EXCLUDED" if excl_one else "NOT excluded"))
        print("  GATING     predicts content-true ratio ~= 1.000            -> %s"
              % ("EXCLUDED" if excl_gate else "NOT excluded"))
        if not excl_one and not excl_gate:
            print("  ==> the data CANNOT DISCRIMINATE. Both accounts sit inside the interval.")
        out["by_scope"][scope.name] = {
            "domains": len(dl), "pairs": len(shared),
            "refusal_ratio": round(pR, 4), "refusal_ci": [round(rLo, 4), round(rHi, 4)],
            "content_ratio": round(pC, 4), "content_ci": [round(cLo, 4), round(cHi, 4)],
            "content_events_ctrl": int(cC), "content_events_ko": int(kC),
            "one_switch_excluded": bool(excl_one), "gating_excluded": bool(excl_gate),
            "provenance": prov}
    json.dump(out, open(a.out, "w"), indent=1)
    print("\nwrote %s" % os.path.relpath(a.out, REPO))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
