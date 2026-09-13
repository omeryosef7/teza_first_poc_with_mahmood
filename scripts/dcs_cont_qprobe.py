#!/usr/bin/env python3
"""Q-PROBE: is there a QUERY-SIDE installation representation -- one the knockout can touch?

WHY THIS IS THE RIGHT NEXT CANDIDATE (§42 Phase 4, §44 criterion 10).
F5 / A11 is the phase's one TEST-confirmed probe, but it is CAUSALLY INERT: its site
`cw_demo_mean` is the mean over demonstration codeword occurrences (`last[:-1]`), which sit
BEFORE the edited query row, so F5's input is bit-identical across `ko` and `ctrl`
(C-CONT-040). It predicts installation but cannot mediate the only intervention this phase
owns. The query span is the ONLY region the row-knockout actually edits. So a probe on a
QUERY-SIDE site (`cw_query` = the codeword occurrence inside the query; `cw_demo_last`; the
`rel*` query-span positions) is the only kind of candidate that could satisfy §44 #10 --
"aggressive full-state patch at its site has causal leverage". This script asks the prior
question first, on TRAIN/VALIDATION only: does a query-side state predict installation AT ALL,
and how does it compare to the demo-side incumbent F5?

WHAT IT REUSES. Everything heavy is `dcs_cont_layerpos_map` (lpm): load_corpus,
load_installation, load_split, family_slot, spearman. The LOO-by-domain ridge kernel is the
SAME one `dcs_cont_f5_probe.py` uses (replicated here, not imported, so f5_probe -- which is
bound to the FROZEN DR-072 confirmation -- is not touched). Target `y_install` is the
concept-free semantic-installation readout, predicted from the BEHAVIOURAL prompt's hidden
state (anti-circularity, per the registry).

TRAPS THIS RESPECTS (claim table §D):
  * #1 topic: a within-domain-centred target, and the incumbent F5 is reported alongside so a
    query-side "win" that merely re-reads the same plateau state is visible, not hidden.
  * #4 no TEST: refuses if any test-split domain reaches the fit populations OR the corpus.
  * #6 selection: the (site,layer) grid is scored on TRAIN LOO; the HONEST number for the
    winner is its VALIDATION transfer at that FIXED (site,layer), reported without retuning.
  * #7 permutation null: permutes the label within domain and re-runs BOTH fit and score.
It does NOT itself claim causal leverage -- that needs the ko/ctrl differ-across-arms test and
a patch, which are follow-ups. It answers only: does a query-side installation signal exist.
"""
from __future__ import annotations
import argparse, importlib.util, json, os, statistics, sys
import torch

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "scripts"))

CORPUS = "outputs/boombness/extract_boombness/cont1_behavioral_button_bomb_20260910_152806_272296"
READOUT = "outputs/boombness/score_behavior/ts116m_readout_button_bomb_20260907_133811_3183103"
LAM = 100.0                                   # same fixed ridge as F5 (not retuned per site)
LADDER = [1e1, 1e2, 1e3, 1e4, 1e5, 1e6]
PLATEAU = [16, 18, 20, 22, 24, 26, 28, 30, 31]   # intersected with captured layers at runtime
F5_SITE, F5_LAYER = "cw_demo_mean", 24        # the demo-side incumbent to beat / compare to


def _load(mod, path):
    s = importlib.util.spec_from_file_location(mod, os.path.join(REPO, path))
    m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-perm", type=int, default=200)
    ap.add_argument("--corpus", default=CORPUS)
    ap.add_argument("--readout", default=READOUT)
    ap.add_argument("--out", default=os.path.join(REPO, "reports/DCS_CONT_QPROBE.json"))
    a = ap.parse_args()

    lpm = _load("lpm", "scripts/dcs_cont_layerpos_map.py")
    assign = lpm.load_split(); EX = set(lpm.EXCLUDED_DOMAINS)
    TR = {d for d, v in assign.items() if v == "train"} - EX
    VA = {d for d, v in assign.items() if v == "validation"} - EX
    if any(assign[d] == "test" for d in TR | VA):
        print("REFUSING: a test domain leaked into the fit populations"); return 2
    inst, _, _ = lpm.load_installation(os.path.join(REPO, a.readout))
    mp, rows, _ = lpm.load_corpus(os.path.join(REPO, a.corpus), mmap=True)  # low-RAM on shared node
    if any(assign.get(r["domain"]) == "test" for r in rows):
        print("REFUSING: corpus contains test-split rows"); return 2

    sites_all = list(mp["sites"]); layers_all = list(mp["layers"])
    layers = [L for L in PLATEAU if L in layers_all]
    # query-side sites: the codeword occurrence inside the query, the demo/query boundary, and
    # every captured query-span rel_end position. Demo-side incumbent kept for comparison only.
    qside = [s for s in sites_all
             if s in ("cw_query", "cw_demo_last") or str(s).startswith("rel")]
    print("captured sites (%d): %s" % (len(sites_all), sites_all))
    print("captured layers: %s" % layers_all)
    print("QUERY-SIDE sites under test (%d): %s" % (len(qside), qside))
    print("plateau layers swept: %s\n" % layers)
    if not qside:
        print("REFUSING: no query-side site captured in this corpus -- needs GPU re-extraction "
              "with --capture-rel-end / cw_query. Nothing to probe on CPU here."); return 3

    def build(keep, site, cell, layer):
        # slice-before-float: from the mmap'd store, read only [site, layer] (a 4096 vector) per
        # row rather than materialising the full [20, 19, 4096] tensor in float32 -- that full
        # copy is what OOM-killed the first run on this shared node.
        si = sites_all.index(site); li = layers_all.index(layer)
        byk = {}
        for r in rows:
            if r["domain"] in keep:
                t = mp["reps"].get(r["prompt_id"])
                if t is not None:
                    byk[((r["domain"], lpm.family_slot(r["family_id"])), r["cell"])] = t[si, li].float()
        comp = [k for k in sorted({k for k, _ in byk}) if all((k, c) in byk for c in "ABCE")]
        doms = sorted({d for d, _ in comp}); xs = []; ys = []; dof = []
        for d in doms:
            ks = [k for k in comp if k[0] == d]
            V = torch.stack([byk[(k, cell)] for k in ks], 0)
            xs.append(V - V.mean(0, keepdim=True))
            yv = [inst[k] for k in ks]; m = statistics.mean(yv)
            ys += [v - m for v in yv]; dof += [d] * len(ks)
        return torch.cat(xs, 0).double(), torch.tensor(ys, dtype=torch.float64), dof, doms

    def loo(X, y, dof, doms, lam):
        K = X @ X.T; pred = [0.0] * len(y)
        for d in doms:
            te = [i for i, x in enumerate(dof) if x == d]; tr = [i for i, x in enumerate(dof) if x != d]
            ti = torch.tensor(tr); ei = torch.tensor(te)
            al = torch.linalg.solve(K[ti][:, ti] + lam * torch.eye(len(tr), dtype=torch.float64), y[ti])
            p = K[ei][:, ti] @ al
            for j, i in enumerate(te): pred[i] = float(p[j])
        return lpm.spearman(pred, y.tolist()), pred

    def transfer(site, layer, cell="C"):
        Xa, ya, da, doa = build(TR, site, cell, layer)
        Xb, yb, db, dob = build(VA, site, cell, layer)
        al = torch.linalg.solve(Xa @ Xa.T + LAM * torch.eye(len(ya), dtype=torch.float64), ya)
        return lpm.spearman((Xb @ Xa.T @ al).tolist(), yb.tolist()), len(yb), len(dob)

    out = {"corpus": a.corpus, "readout": a.readout, "lambda": LAM,
           "captured_sites": sites_all, "query_side_sites": qside,
           "plateau_layers": layers, "grid_train_rho": {}, "note": "TRAIN grid is a search; "
           "the honest number for the winner is its VALIDATION transfer at the fixed (site,layer)."}

    # ---- TRAIN grid: within-domain LOO ridge at every (query-side site, plateau layer)
    print("[TRAIN] within-domain LOO-by-domain ridge, lambda=%.0e" % LAM)
    best = None
    for site in qside:
        out["grid_train_rho"][site] = {}
        for L in layers:
            X, y, dof, doms = build(TR, site, "C", L)
            r, _ = loo(X, y, dof, doms, LAM)
            out["grid_train_rho"][site]["L%d" % L] = round(r, 4)
            if best is None or r > best[2]:
                best = (site, L, r, len(y), len(doms))
        print("   %-14s  " % site + "  ".join("L%d=%+.3f" % (L, out["grid_train_rho"][site]["L%d" % L]) for L in layers))
    bsite, bL, brho, bn, bd = best
    print("\n[TRAIN] best query-side cell: %s L%d  rho_loo=%+.4f  (%d slots / %d domains)"
          % (bsite, bL, brho, bn, bd))

    # ---- incumbent F5 (demo-side) on the SAME TRAIN corpus, for a like-for-like comparison
    f5_rho = None
    if F5_SITE in sites_all and F5_LAYER in layers_all:
        Xf, yf, df, domf = build(TR, F5_SITE, "C", F5_LAYER)
        f5_rho, _ = loo(Xf, yf, df, domf, LAM)
        print("[TRAIN] incumbent F5 demo-side %s L%d rho_loo=%+.4f" % (F5_SITE, F5_LAYER, f5_rho))
    out["train_best"] = {"site": bsite, "layer": bL, "rho_loo": round(brho, 4),
                         "slots": bn, "domains": bd}
    out["train_f5_incumbent_rho_loo"] = round(f5_rho, 4) if f5_rho is not None else None

    # ---- permutation null for the winner (both fit and score permuted within domain)
    Xb, yb, dofb, domb = build(TR, bsite, "C", bL)
    rho_b, _ = loo(Xb, yb, dofb, domb, LAM)
    g = torch.Generator().manual_seed(20260913); null = []
    IDX = {d: [i for i, x in enumerate(dofb) if x == d] for d in domb}
    for _ in range(a.n_perm):
        yp = yb.clone()
        for d in domb:
            idx = IDX[d]; pm = torch.randperm(len(idx), generator=g)
            for j, i in enumerate(idx): yp[i] = yb[idx[pm[j]]]
        r, _ = loo(Xb, yp, dofb, domb, LAM); null.append(r)
    null.sort(); pval = (sum(1 for v in null if v >= rho_b) + 1) / (a.n_perm + 1)
    print("[TRAIN] winner permutation null (%d perms): p50=%+.3f p95=%+.3f max=%+.3f -> p=%.4f"
          % (a.n_perm, null[a.n_perm // 2], null[int(.95 * a.n_perm)], null[-1], pval))
    out["train_best_perm_p"] = pval

    # ---- VALIDATION transfer: the winner at its FIXED (site,layer), and F5 incumbent, no retune
    vr, vn, vd = transfer(bsite, bL)
    print("\n[VALIDATION] winner %s L%d transfer rho=%+.4f  (%d slots / %d domains)"
          % (bsite, bL, vr, vn, vd))
    out["validation_best"] = {"site": bsite, "layer": bL, "rho": round(vr, 4),
                              "slots": vn, "domains": vd}
    if F5_SITE in sites_all and F5_LAYER in layers_all:
        f5v, f5n, f5d = transfer(F5_SITE, F5_LAYER)
        print("[VALIDATION] incumbent F5 %s L%d transfer rho=%+.4f" % (F5_SITE, F5_LAYER, f5v))
        out["validation_f5_incumbent"] = {"site": F5_SITE, "layer": F5_LAYER, "rho": round(f5v, 4)}

    json.dump(out, open(a.out, "w"), indent=1)
    print("\nwrote %s" % os.path.relpath(a.out, REPO))
    print("\nINTERPRETATION GUARD: a query-side rho comparable to F5 is necessary but NOT "
          "sufficient for §44 #10. The causal test (does this site's input differ across "
          "ko/ctrl, and does a patch move installation) is the follow-up and is NOT claimed here.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
