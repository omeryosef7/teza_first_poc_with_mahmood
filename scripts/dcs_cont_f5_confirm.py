#!/usr/bin/env python3
"""DR-072: the single confirmatory TEST read for F5_probe_installation.

This script does NOT decide anything. Every free parameter -- site, layer, cell, lambda, the fit
population, the centring, the unit of analysis, the null, and the decision rule -- is read out of
the FROZEN preregistration and enforced here. If the config is not FROZEN, this refuses to run.

Discovery was TRAIN (CONT-ENTRY 059). Selection was VALIDATION (CONT-ENTRY 061). Both are spent.
TEST is read ONCE, under this document, and the read counts even if the run errors.
"""
from __future__ import annotations
import argparse, importlib.util, json, os, sys, statistics, torch

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def _load(mod, path):
    s = importlib.util.spec_from_file_location(mod, os.path.join(REPO, path))
    m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=os.path.join(REPO, "configs/dcs_cont_dr072_f5_confirmation.json"))
    ap.add_argument("--out", default=os.path.join(REPO, "outputs/dcs_cont/f5_confirmation_TEST.json"))
    ap.add_argument("--confirm-test-read", action="store_true",
                    help="required; reading TEST is a one-time act and must be deliberate")
    a = ap.parse_args()

    cfg = json.load(open(a.config))
    if cfg.get("status") != "FROZEN":
        print("REFUSING: config status is %r, not FROZEN" % cfg.get("status")); return 2
    if cfg.get("id") != "DR-072":
        print("REFUSING: config id is %r, not DR-072" % cfg.get("id")); return 2
    if not a.confirm_test_read:
        print("REFUSING: --confirm-test-read not given. This reads the TEST split."); return 2
    sp, pv = cfg["specification"], cfg["provenance"]
    if sp.get("no_retuning") is None:
        print("REFUSING: config carries no no_retuning clause"); return 2

    lpm = _load("lpm", "scripts/dcs_cont_layerpos_map.py")
    assign = lpm.load_split(); EX = set(lpm.EXCLUDED_DOMAINS)
    FIT = {d for d, v in assign.items() if v in ("train", "validation")} - EX
    TST = {d for d, v in assign.items() if v == "test"} - EX
    if FIT & TST:
        print("REFUSING: fit and test populations overlap"); return 2

    inst, _, _ = lpm.load_installation(os.path.join(REPO, pv["installation_run"]))
    mp, rows, _ = lpm.load_corpus(os.path.join(REPO, pv["corpus"]))
    meta = json.load(open(os.path.join(REPO, pv["corpus"], "metadata.json")))
    if meta.get("bank_file_sha16") != pv["bank_file_sha16"]:
        print("REFUSING: bank mismatch %s != %s" % (meta.get("bank_file_sha16"), pv["bank_file_sha16"])); return 2
    si = mp["sites"].index(sp["site"]); li = mp["layers"].index(int(sp["layer"]))

    def build(keep):
        byk = {}
        for r in rows:
            if r["domain"] in keep:
                t = mp["reps"].get(r["prompt_id"])
                if t is not None:
                    byk[((r["domain"], lpm.family_slot(r["family_id"])), r["cell"])] = t.float()
        comp = [k for k in sorted({k for k, _ in byk}) if all((k, c) in byk for c in "ABCE")]
        doms = sorted({d for d, _ in comp}); xs = []; ys = []; dof = []
        for d in doms:
            ks = [k for k in comp if k[0] == d]
            V = torch.stack([byk[(k, sp["cell"])][si, li] for k in ks], 0)
            xs.append(V - V.mean(0, keepdim=True))
            yv = [inst[k] for k in ks]; m = statistics.mean(yv)
            ys += [v - m for v in yv]; dof += [d] * len(ks)
        return torch.cat(xs, 0).double(), torch.tensor(ys, dtype=torch.float64), dof, doms

    n_test_rows = sum(1 for r in rows if r['domain'] in TST)
    if n_test_rows == 0:
        print("REFUSING: the corpus contains 0 rows from any TEST domain.")
        print("  corpus: %s" % pv['corpus'])
        print("  This is the search corpus, extracted with --only-split train,validation, so it")
        print("  CANNOT leak TEST -- the discipline working as designed, not a failure.")
        print("  NOTHING WAS READ: no TEST quantity was computed, so the DR-072 single read is")
        print("  NOT spent. Re-run against a corpus extracted with --only-split test.")
        return 3
    Xf, yf, _, df = build(FIT); Xt, yt, dot, dt = build(TST)
    lam = float(sp["lambda"])
    K = Xf @ Xf.T
    alpha = torch.linalg.solve(K + lam * torch.eye(len(yf), dtype=torch.float64), yf)
    pred = (Xt @ Xf.T @ alpha).tolist()
    rho = lpm.spearman(pred, yt.tolist())
    comp_pred = (Xt @ (Xf.T @ yf)).tolist()
    rho_comp = lpm.spearman(comp_pred, yt.tolist())

    per = []
    for d in dt:
        idx = [i for i, x in enumerate(dot) if x == d]
        per.append(lpm.spearman([pred[i] for i in idx], [float(yt[i]) for i in idx]))
    frac_pos = sum(1 for v in per if v > 0) / len(per)

    nperm = int(cfg["null"]["n_permutations"])
    g = torch.Generator().manual_seed(int(cfg["null"]["seed"]))
    null = []
    for _ in range(nperm):
        yp = yt.clone()
        for d in dt:
            idx = [i for i, x in enumerate(dot) if x == d]
            pm = torch.randperm(len(idx), generator=g)
            for j, i in enumerate(idx): yp[i] = yt[idx[pm[j]]]
        null.append(lpm.spearman(pred, yp.tolist()))
    null.sort()
    p = (sum(1 for v in null if v >= rho) + 1) / (nperm + 1)

    dr = cfg["decision_rule"]
    ok_sign, ok_p, ok_frac = rho > 0, p < 0.05, frac_pos >= 0.60
    beats = rho > rho_comp
    verdict = "CONFIRMED" if (ok_sign and ok_p and ok_frac) else "NOT CONFIRMED"

    print("DR-072 -- F5_probe_installation, CONFIRMATORY TEST READ")
    print("  config %s (FROZEN %s)" % (os.path.basename(a.config), cfg["frozen_at"]))
    print("  site=%s layer=%s cell=%s lambda=%g   fit=%d doms/%d slots   TEST=%d doms/%d slots"
          % (sp["site"], sp["layer"], sp["cell"], lam, len(df), len(yf), len(dt), len(yt)))
    print("  rho_test                      %+.4f" % rho)
    print("  comparator (unregularised)    %+.4f   -> F5 beats it: %s" % (rho_comp, beats))
    print("  per-domain rho: mean %+.4f median %+.4f positive in %d/%d (%.1f%%)"
          % (statistics.mean(per), statistics.median(per), sum(1 for v in per if v > 0), len(per), 100 * frac_pos))
    print("  null (%d perms, predictor FIXED): p50=%+.4f p95=%+.4f max=%+.4f -> p=%.5f"
          % (nperm, null[nperm // 2], null[int(0.95 * nperm)], null[-1], p))
    print("  prespecified: rho>0 %s | p<0.05 %s | >=60%% domains %s" % (ok_sign, ok_p, ok_frac))
    print("  point prediction was %s" % dr["point_prediction"])
    print("\n  VERDICT: %s" % verdict)
    if verdict == "CONFIRMED" and not beats:
        print("  NOTE: F5 is significant but does NOT beat the prespecified comparator;")
        print("        the REGULARISATION claim is NOT CONFIRMED.")
    print("\n  things_that_must_not_be_said:")
    for s in cfg["things_that_must_not_be_said"]:
        print("   - %s" % s)

    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    json.dump({"config": os.path.basename(a.config), "config_id": cfg["id"], "rho_test": rho,
               "rho_comparator": rho_comp, "f5_beats_comparator": beats, "p": p, "n_perm": nperm,
               "per_domain_rho": per, "frac_domains_positive": frac_pos,
               "n_fit_domains": len(df), "n_fit_slots": len(yf),
               "n_test_domains": len(dt), "n_test_slots": len(yt),
               "criteria": {"rho_gt_0": ok_sign, "p_lt_0.05": ok_p, "frac_ge_0.60": ok_frac},
               "verdict": verdict,
               "things_that_must_not_be_said": cfg["things_that_must_not_be_said"]},
              open(a.out, "w"), indent=1)
    print("\n  wrote %s" % a.out)
    return 0

if __name__ == "__main__":
    sys.exit(main())
