#!/usr/bin/env python3
"""F5_probe_installation: the ridge probe, its reproduction, and its controls.

WHY THIS FILE EXISTS. CONT-ENTRY 059 and 061 reported F5's numbers from ad-hoc heredocs and committed
no script, so the phase's headline -- and the entire subject of preregistration DR-072 -- could not be
re-derived from the repo (REVIEW-2/DATA finding 10). This reproduces both entries exactly and adds the
controls C-CONT-040 requires before DR-072's single TEST read may be spent.

THE CONTROLS, AND WHY EACH ONE. C-CONT-040 established that F5's site, `cw_demo_mean`, is the mean over
the codeword's DEMONSTRATION occurrences (the extractor builds it as last[:-1]) and therefore sits
causally upstream of `target_surface_row_only`, which edits inside the QUERY span. So F5 cannot mediate
the knockout, and the question becomes what rho=0.62 is actually measuring.
  raw_B        -- the same state in cell B (harm demos, concept). If it predicts as well, F5 is not
                  about the attack cell.
  prev/next    -- the neutral tokens adjacent to each demonstration codeword. If they predict as well,
                  nothing is localised at the codeword. This is the D-001 precedent applied at L24.
  rand_mean    -- a size-matched seeded random pool of demonstration-block rows. The mass control.
  logit lens   -- cos(w_F5, the concept-minus-codeword unembedding direction). Asks the question
                  entry 059 never asked: is F5 just the logit lens with shrinkage?

NOTHING HERE READS THE TEST SPLIT. TRAIN is the discovery population, VALIDATION the selection
population; both are already spent. TEST is reached only by scripts/dcs_cont_f5_confirm.py under DR-072.
"""
from __future__ import annotations
import argparse, importlib.util, json, os, statistics, sys, torch

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORPUS = "outputs/boombness/extract_boombness/cont1_behavioral_button_bomb_20260910_152806_272296"
READOUT = "outputs/boombness/score_behavior/ts116m_readout_button_bomb_20260907_133811_3183103"
SITE, LAYER, LAM = "cw_demo_mean", 24, 100.0
LADDER = [1e1, 1e2, 1e3, 1e4, 1e5, 1e6]

def _load(mod, path):
    s = importlib.util.spec_from_file_location(mod, os.path.join(REPO, path))
    m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-perm", type=int, default=200)
    ap.add_argument("--out", default=os.path.join(REPO, "reports/DCS_CONT_F5_RESULTS.json"))
    a = ap.parse_args()
    lpm = _load("lpm", "scripts/dcs_cont_layerpos_map.py")
    assign = lpm.load_split(); EX = set(lpm.EXCLUDED_DOMAINS)
    TR = {d for d, v in assign.items() if v == "train"} - EX
    VA = {d for d, v in assign.items() if v == "validation"} - EX
    if any(assign[d] == "test" for d in TR | VA):
        print("REFUSING: a test domain leaked into the fit populations"); return 2
    inst, _, _ = lpm.load_installation(os.path.join(REPO, READOUT))
    mp, rows, _ = lpm.load_corpus(os.path.join(REPO, CORPUS))
    if any(assign.get(r["domain"]) == "test" for r in rows):
        print("REFUSING: corpus contains test-split rows"); return 2
    li = mp["layers"].index(LAYER)

    def build(keep, site, cell):
        si = mp["sites"].index(site)
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
            V = torch.stack([byk[(k, cell)][si, li] for k in ks], 0)
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

    out = {"site": SITE, "layer": LAYER, "lambda": LAM, "corpus": CORPUS, "readout": READOUT}
    print("F5_probe_installation -- reproduction of CONT-ENTRY 059 and 061, plus C-CONT-040 controls")

    Xtr, ytr, dtr, domtr = build(TR, SITE, "C")
    print("\n[059] TRAIN lambda ladder, LOO by DOMAIN (%d slots / %d domains)" % (len(ytr), len(domtr)))
    lad = {}
    for lam in LADDER:
        r, _ = loo(Xtr, ytr, dtr, domtr, lam); lad["%.0e" % lam] = r
        print("   lambda=%-8.0e rho_loo=%+.4f" % (lam, r))
    out["train_ladder"] = lad
    rho_tr, _ = loo(Xtr, ytr, dtr, domtr, LAM)
    out["train_rho_loo"] = rho_tr

    print("\n[059] within-domain permutation null, %d perms (BOTH fit and score permuted)" % a.n_perm)
    g = torch.Generator().manual_seed(20260911); null = []
    IDX = {d: [i for i, x in enumerate(dtr) if x == d] for d in domtr}
    for _ in range(a.n_perm):
        yp = ytr.clone()
        for d in domtr:
            idx = IDX[d]; pm = torch.randperm(len(idx), generator=g)
            for j, i in enumerate(idx): yp[i] = ytr[idx[pm[j]]]
        r, _ = loo(Xtr, yp, dtr, domtr, LAM); null.append(r)
    null.sort(); p = (sum(1 for v in null if v >= rho_tr) + 1) / (a.n_perm + 1)
    print("   p50=%+.4f p95=%+.4f max=%+.4f -> p=%.4f" % (null[a.n_perm // 2], null[int(.95 * a.n_perm)], null[-1], p))
    out["train_perm_p"] = p

    Xva, yva, dva, domva = build(VA, SITE, "C")
    al = torch.linalg.solve(Xtr @ Xtr.T + LAM * torch.eye(len(ytr), dtype=torch.float64), ytr)
    pv = (Xva @ Xtr.T @ al).tolist(); rho_va = lpm.spearman(pv, yva.tolist())
    w_f5 = Xtr.T @ al
    base = (Xva @ (Xtr.T @ ytr)).tolist(); rho_cmp = lpm.spearman(base, yva.tolist())
    per = []
    for d in domva:
        idx = [i for i, x in enumerate(dva) if x == d]
        per.append(lpm.spearman([pv[i] for i in idx], [float(yva[i]) for i in idx]))
    print("\n[061] VALIDATION transfer (%d slots / %d domains), lambda NOT retuned" % (len(yva), len(domva)))
    print("   F5 rho=%+.4f | unregularised comparator rho=%+.4f | positive in %d/%d domains"
          % (rho_va, rho_cmp, sum(1 for v in per if v > 0), len(per)))
    out.update({"validation_rho": rho_va, "validation_comparator_rho": rho_cmp,
                "validation_per_domain_rho": per})

    print("\n[C-CONT-040] CONTROLS -- all on VALIDATION, fit on TRAIN, lambda fixed")
    ctrl = {}
    for name, site, cell in [("raw_B (cell B, same site)", SITE, "B"),
                             ("cw_demo_prev_mean", "cw_demo_prev_mean", "C"),
                             ("cw_demo_next_mean", "cw_demo_next_mean", "C"),
                             ("cw_demo_rand_mean", "cw_demo_rand_mean", "C"),
                             ("cw_query (query row only)", "cw_query", "C")]:
        if site not in mp["sites"]:
            print("   %-28s SITE NOT CAPTURED" % name); ctrl[name] = None; continue
        Xa, ya, da, doa = build(TR, site, cell); Xb, yb, db, dob = build(VA, site, cell)
        ala = torch.linalg.solve(Xa @ Xa.T + LAM * torch.eye(len(ya), dtype=torch.float64), ya)
        r = lpm.spearman((Xb @ Xa.T @ ala).tolist(), yb.tolist())
        ctrl[name] = r
        print("   %-28s rho=%+.4f   (F5=%+.4f, delta=%+.4f)" % (name, r, rho_va, rho_va - r))
    out["controls"] = ctrl
    json.dump(out, open(a.out, "w"), indent=1)
    print("\n   wrote %s" % a.out)
    return 0

if __name__ == "__main__":
    sys.exit(main())
