#!/usr/bin/env python3
"""F6: a low-rank subspace on the WITHIN-DOMAIN installation target. Mandate sections 14, 46.

WHY THIS EXISTS
---------------
CONT-ENTRY 052's section-46 audit found F6 declared on day one and never fitted -- the only one of
the seven prerequisites that was completely untouched. Section 46 forbids any no-representation
conclusion until at least one low-rank approach has been run, so this runs one.

WHAT IT DOES
------------
PLS regression with scalar target, r components, on the WITHIN-DOMAIN centred data (topic removed by
construction, CONT-ENTRY 030). Component 1 of PLS with a scalar y IS the covariance direction the
map already uses, so r=1 reproduces the existing number and r>1 asks the question F6 exists for:
IS THE PREDICTIVE STRUCTURE MULTI-DIMENSIONAL, or is one direction all there is?

Leave-one-DOMAIN-out throughout: the subspace is fitted without the held-out domain and then used to
predict it. Slots within a domain share a demonstration pool, so a slot-level split would leak.

Rank is NOT selected here. Every rank is reported; selection on VALIDATION under a pre-declared rule
is a separate step that has not happened (section 14).
"""
from __future__ import annotations
import argparse, importlib.util, json, os, statistics, sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_s = importlib.util.spec_from_file_location("lpm", os.path.join(REPO, "scripts",
                                                                "dcs_cont_layerpos_map.py"))
lpm = importlib.util.module_from_spec(_s); _s.loader.exec_module(lpm)


def pls_fit(X, y, r):
    """PLS-1 with deflation. Returns (weights [r,d], coefs [r]) fitted on X,y."""
    import torch
    Xd = X.clone(); yd = y.clone()
    W, C, P = [], [], []
    for _ in range(r):
        w = Xd.t() @ yd
        n = w.norm()
        if float(n) < 1e-9:
            break
        w = w / n
        t = Xd @ w                       # scores
        tt = float(t @ t)
        if tt < 1e-12:
            break
        c = float(t @ yd) / tt           # regression of y on this score
        p = (Xd.t() @ t) / tt            # loadings
        Xd = Xd - torch.outer(t, p)      # deflate X
        yd = yd - c * t                  # deflate y
        W.append(w); C.append(c); P.append(p)
    return (torch.stack(W, 0), torch.tensor(C), torch.stack(P, 0)) if W else (None, None, None)


def pls_predict(X, W, C, P):
    """Apply the fitted PLS model WITH deflation.

    C-CONT-043. The previous body was `sum_k c_k * (X w_k)` -- every component scored against the
    UNDEFLATED X, which its own docstring called a "deflation-free approximation". That is exact at
    rank 1 and wrong for every rank above it, because component k's score is defined on the residual
    left by components 1..k-1, not on the original matrix. It understated ranks >= 2 and manufactured
    the rise-then-fall curve CONT-ENTRY 053 read as "the structure is one-dimensional".

    The fit already computes the loadings P needed to reproduce the deflation at predict time; they
    were simply discarded. Rank 1 is unchanged, so 053's rank-1 number stands.
    """
    import torch  # module-level helpers take torch locally in this file; see C-CONT-009
    Xd = X.clone()
    out = torch.zeros(X.shape[0], dtype=X.dtype)
    for k in range(len(C)):
        t = Xd @ W[k]
        out = out + C[k] * t
        Xd = Xd - torch.outer(t, P[k])
    return out


def main() -> int:
    import torch
    ap = argparse.ArgumentParser()
    ap.add_argument("--beh-run", required=True)
    ap.add_argument("--readout-run", required=True)
    ap.add_argument("--site", default="cw_demo_mean")
    ap.add_argument("--layer", type=int, default=14)
    ap.add_argument("--ranks", default="1,2,4,8")
    ap.add_argument("--split", default="train", choices=["train", "validation"])
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    assign = lpm.load_split()
    keep = {d for d, s in assign.items() if s == a.split} - set(lpm.EXCLUDED_DOMAINS)
    inst, _, _ = lpm.load_installation(os.path.join(REPO, a.readout_run))
    mp, rows, sha = lpm.load_corpus(os.path.join(REPO, a.beh_run))
    ro, src = lpm.readout_bank_sha(os.path.join(REPO, a.readout_run))
    if ro != sha:
        raise lpm.Refusal("BANK MISMATCH corpus %s vs readout %s (%s)" % (sha, ro, src))
    si, li = mp["sites"].index(a.site), mp["layers"].index(a.layer)

    byk = {}
    for r in rows:
        if r["domain"] in keep:
            t = mp["reps"].get(r["prompt_id"])
            if t is not None:
                byk[((r["domain"], lpm.family_slot(r["family_id"])), r["cell"])] = t[si, li].float()
    keys = sorted({k for (k, _) in byk})
    comp = [k for k in keys if all((k, c) in byk for c in ("A", "B", "C", "E"))]
    doms = sorted({d for d, _ in comp})

    xs, ys, dof = [], [], []
    for d in doms:
        ks = [k for k in comp if k[0] == d]
        mx = sum(byk[(k, "C")] for k in ks) / len(ks)          # raw cell-C state
        my = statistics.mean([inst[k] for k in ks])
        for k in ks:
            xs.append(byk[(k, "C")] - mx); ys.append(inst[k] - my); dof.append(d)
    X = torch.stack(xs, 0); Y = torch.tensor(ys, dtype=torch.float32)
    print("[lowrank] %d slots over %d domains, site=%s L%d, within-domain centred"
          % (len(ys), len(doms), a.site, a.layer))

    out = {"schema": "dcs_cont_lowrank/1", "status": "EXPLORATORY",
           "beh_run": a.beh_run, "site": a.site, "layer": a.layer, "split": a.split,
           "bank_file_sha16": sha, "n_slots": len(ys), "n_domains": len(doms),
           "note": ("PLS-1 with scalar target; component 1 IS the covariance direction the map "
                    "already uses, so rank 1 reproduces it. Rank is NOT selected here -- every rank "
                    "is reported and selection on VALIDATION has not happened."),
           "by_rank": {}}
    for r in [int(x) for x in a.ranks.split(",") if x.strip()]:
        pred = [0.0] * len(ys)
        for d in doms:
            ho = [i for i, dd in enumerate(dof) if dd == d]
            tr = [i for i, dd in enumerate(dof) if dd != d]
            W, C, P = pls_fit(X[tr], Y[tr], r)
            if W is None:
                continue
            p = pls_predict(X[ho], W, C, P)
            for j, i in enumerate(ho):
                pred[i] = float(p[j])
        rho = lpm.spearman(pred, ys)
        out["by_rank"][str(r)] = {"rho_loo": rho}
        print("  rank %-2d  rho_loo = %+.4f" % (r, rho))
    op = os.path.join(REPO, a.out); os.makedirs(os.path.dirname(op), exist_ok=True)
    json.dump(out, open(op, "w", encoding="utf-8"), indent=1)
    print("[lowrank] wrote %s" % a.out)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except lpm.Refusal as e:
        print("REFUSING: %s" % e, file=sys.stderr); raise SystemExit(2)
