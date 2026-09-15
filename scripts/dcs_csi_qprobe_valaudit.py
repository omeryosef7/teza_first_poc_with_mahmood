#!/usr/bin/env python3
"""P0.3 AUDIT: is `dcs_cont_qprobe.py`'s VALIDATION transfer independent of its TRAIN fit?

THE SUSPICION. reports/DCS_CONT_QPROBE_basket.json reports
    train_best.rho_loo = 0.6525  and  validation_best.rho = 0.6525
at the same (rel-6, L18) cell -- byte-identical to 4 dp. That is the exact shape of a bug in
which the "validation" path silently re-reads the TRAIN population. The button pair
(0.5935 / 0.6450) is not degenerate, so if a leak exists it is population-dependent.

WHAT THIS DOES. It replays qprobe's OWN build/loo/transfer kernels verbatim (copied, not
imported, so nothing frozen is touched) for both codewords at the cell each report names, and
prints, at FULL float precision and with no rounding anywhere:
  * the TRAIN / VALIDATION / TEST domain sets and their pairwise intersections,
  * the row populations each `build()` actually returns (n slots, n domains, prompt-id sets),
  * train rho_loo and validation transfer rho as repr(float),
  * an explicit disjointness check on the (domain, slot) keys of the two built populations.
A leak shows up as a non-empty key intersection or as bit-identical rho; a coincidence shows up
as two different floats that happen to round to the same 4 dp.
"""
from __future__ import annotations
import importlib.util, json, os, statistics, sys
import torch

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "scripts"))
LAM = 100.0

PAIRS = [
    ("button",
     "outputs/boombness/extract_boombness/cont1_behavioral_button_bomb_20260910_152806_272296",
     "outputs/boombness/score_behavior/ts116m_readout_button_bomb_20260907_133811_3183103",
     "rel-6", 20),
    ("basket",
     "outputs/boombness/extract_boombness/cont1_behavioral_basket_bomb_20260910_113902_3966018",
     "outputs/boombness/score_behavior/ts116m_readout_basket_bomb_20260907_152329_3191150",
     "rel-6", 18),
]
F5_SITE, F5_LAYER = "cw_demo_mean", 24


def _load(mod, path):
    s = importlib.util.spec_from_file_location(mod, os.path.join(REPO, path))
    m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m


def main() -> int:
    lpm = _load("lpm", "scripts/dcs_cont_layerpos_map.py")
    assign = lpm.load_split(); EX = set(lpm.EXCLUDED_DOMAINS)
    TR = {d for d, v in assign.items() if v == "train"} - EX
    VA = {d for d, v in assign.items() if v == "validation"} - EX
    TE = {d for d, v in assign.items() if v == "test"}
    print("[split] |TRAIN|=%d |VALIDATION|=%d |TEST|=%d  excluded=%s"
          % (len(TR), len(VA), len(TE), sorted(EX)))
    print("[split] TR&VA=%s  TR&TE=%s  VA&TE=%s" % (sorted(TR & VA), sorted(TR & TE), sorted(VA & TE)))
    if TR & VA or TR & TE or VA & TE:
        print("REFUSING: split manifest itself is not a partition"); return 2

    for name, corpus, readout, site, layer in PAIRS:
        print("\n" + "=" * 78)
        print("[%s] corpus=%s" % (name, corpus))
        print("[%s] readout=%s  cell under audit = (%s, L%d)" % (name, readout, site, layer))
        inst, _, _ = lpm.load_installation(os.path.join(REPO, readout))
        mp, rows, csha = lpm.load_corpus(os.path.join(REPO, corpus), mmap=True)
        rsha, rsrc = lpm.readout_bank_sha(os.path.join(REPO, readout))
        print("[%s] bank: corpus=%s readout=%s (%s) agree=%s" % (name, csha, rsha, rsrc, rsha == csha))
        if rsha != csha:
            print("REFUSING: bank mismatch"); return 2
        if any(assign.get(r["domain"]) == "test" for r in rows):
            print("REFUSING: corpus contains test-split rows"); return 2
        sites_all = list(mp["sites"]); layers_all = list(mp["layers"])

        def build(keep, site, cell, layer, want_ids=False):
            si = sites_all.index(site); li = layers_all.index(layer)
            byk = {}; pid = {}
            for r in rows:
                if r["domain"] in keep:
                    t = mp["reps"].get(r["prompt_id"])
                    if t is not None:
                        k = ((r["domain"], lpm.family_slot(r["family_id"])), r["cell"])
                        if k in byk:
                            raise SystemExit("duplicate key %r" % (k,))
                        byk[k] = t[si, li].float(); pid[k] = r["prompt_id"]
            comp = [k for k in sorted({k for k, _ in byk}) if all((k, c) in byk for c in "ABCE")]
            doms = sorted({d for d, _ in comp}); xs = []; ys = []; dof = []
            for d in doms:
                ks = [k for k in comp if k[0] == d]
                V = torch.stack([byk[(k, cell)] for k in ks], 0)
                xs.append(V - V.mean(0, keepdim=True))
                yv = [inst[k] for k in ks]; m = statistics.mean(yv)
                ys += [v - m for v in yv]; dof += [d] * len(ks)
            X = torch.cat(xs, 0).double(); Y = torch.tensor(ys, dtype=torch.float64)
            if want_ids:
                ids = set()
                for k in comp:
                    for c in "ABCE":
                        ids.add(pid[(k, c)])
                return X, Y, dof, doms, set(comp), ids
            return X, Y, dof, doms

        def loo(X, y, dof, doms, lam):
            K = X @ X.T; pred = [0.0] * len(y)
            for d in doms:
                te = [i for i, x in enumerate(dof) if x == d]
                tr = [i for i, x in enumerate(dof) if x != d]
                ti = torch.tensor(tr); ei = torch.tensor(te)
                al = torch.linalg.solve(K[ti][:, ti] + lam * torch.eye(len(tr), dtype=torch.float64), y[ti])
                p = K[ei][:, ti] @ al
                for j, i in enumerate(te): pred[i] = float(p[j])
            return lpm.spearman(pred, y.tolist()), pred

        # ---- populations actually built
        Xa, ya, da, doa, ka, ida = build(TR, site, "C", layer, want_ids=True)
        Xb, yb, db, dob, kb, idb = build(VA, site, "C", layer, want_ids=True)
        print("[%s] TRAIN  population: %d slots / %d domains / %d prompt_ids" % (name, len(ya), len(doa), len(ida)))
        print("[%s] VALID  population: %d slots / %d domains / %d prompt_ids" % (name, len(yb), len(dob), len(idb)))
        print("[%s] key intersection TRAIN&VALID = %d   prompt_id intersection = %d"
              % (name, len(ka & kb), len(ida & idb)))
        print("[%s] domain intersection = %s" % (name, sorted(set(doa) & set(dob))))
        print("[%s] X shapes: train %s valid %s" % (name, tuple(Xa.shape), tuple(Xb.shape)))
        print("[%s] y hashes: train %s valid %s"
              % (name, hash(tuple(ya.tolist())), hash(tuple(yb.tolist()))))

        # ---- the two numbers, at full precision
        rho_tr, _ = loo(Xa, ya, da, doa, LAM)
        al = torch.linalg.solve(Xa @ Xa.T + LAM * torch.eye(len(ya), dtype=torch.float64), ya)
        pv = (Xb @ Xa.T @ al).tolist()
        rho_va = lpm.spearman(pv, yb.tolist())
        print("[%s] TRAIN  rho_loo      = %s   (round4=%.4f)" % (name, repr(rho_tr), round(rho_tr, 4)))
        print("[%s] VALID  transfer rho = %s   (round4=%.4f)" % (name, repr(rho_va), round(rho_va, 4)))
        print("[%s] identical bits? %s   |diff| = %s" % (name, rho_tr == rho_va, repr(abs(rho_tr - rho_va))))

        # ---- F5 incumbent, same two paths, as a second independent witness
        if F5_SITE in sites_all and F5_LAYER in layers_all:
            Xf, yf, dff, domf = build(TR, F5_SITE, "C", F5_LAYER)
            r_f5_tr, _ = loo(Xf, yf, dff, domf, LAM)
            Xg, yg, _, _ = build(VA, F5_SITE, "C", F5_LAYER)
            alf = torch.linalg.solve(Xf @ Xf.T + LAM * torch.eye(len(yf), dtype=torch.float64), yf)
            r_f5_va = lpm.spearman((Xg @ Xf.T @ alf).tolist(), yg.tolist())
            print("[%s] F5 TRAIN rho_loo = %s ; F5 VALID transfer = %s"
                  % (name, repr(r_f5_tr), repr(r_f5_va)))

        # ---- a leak would also make the VALIDATION number insensitive to the TRAIN fit.
        # Refit on a HALF of TRAIN and re-transfer: a genuine transfer moves, a re-read does not.
        half = sorted(doa)[: len(doa) // 2]
        Xh, yh, dh, domh = build(set(half), site, "C", layer)
        alh = torch.linalg.solve(Xh @ Xh.T + LAM * torch.eye(len(yh), dtype=torch.float64), yh)
        rho_half = lpm.spearman((Xb @ Xh.T @ alh).tolist(), yb.tolist())
        print("[%s] SENSITIVITY: refit on %d/%d TRAIN domains -> VALID rho = %s"
              % (name, len(domh), len(doa), repr(rho_half)))
        del mp, rows
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
