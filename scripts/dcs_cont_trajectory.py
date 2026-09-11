#!/usr/bin/env python3
"""F4: trajectory features over DEPTH. Mandate sections 11, 46.

WHY NOW
-------
CONT-ENTRY 056's full-depth sweep showed the within-domain score at cw_demo_mean rises monotonically
from L0 (+0.19) and plateaus at L22-L30 (+0.55). A profile with that shape is a trajectory result in
embryo, and section 11 asks directly whether HOW A REPRESENTATION CHANGES ACROSS DEPTH predicts
better than any static layer does. Section 46 lists trajectories among the prerequisites.

WHAT IT DOES
------------
Per slot, build the depth profile s(L) of the leave-one-DOMAIN-out score at each captured layer, all
within-domain centred (topic removed by construction). Then derive section-11 features -- area under
the depth profile, early-to-late slope, peak layer, early/late difference -- and ask whether any of
them predicts within-domain installation better than the BEST SINGLE LAYER.

The comparison that matters is against the best single layer, not against zero: a trajectory feature
that merely recovers the plateau has found nothing new.
"""
from __future__ import annotations
import argparse, importlib.util, json, os, statistics, sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_s = importlib.util.spec_from_file_location("lpm", os.path.join(REPO, "scripts",
                                                                "dcs_cont_layerpos_map.py"))
lpm = importlib.util.module_from_spec(_s); _s.loader.exec_module(lpm)


def main() -> int:
    import torch
    ap = argparse.ArgumentParser()
    ap.add_argument("--beh-run", required=True)
    ap.add_argument("--readout-run", required=True)
    ap.add_argument("--site", default="cw_demo_mean")
    ap.add_argument("--split", default="train", choices=["train", "validation"])
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    assign = lpm.load_split()
    keep = {d for d, s in assign.items() if s == a.split} - set(lpm.EXCLUDED_DOMAINS)
    inst, _, _ = lpm.load_installation(os.path.join(REPO, a.readout_run))
    mp, rows, sha = lpm.load_corpus(os.path.join(REPO, a.beh_run))
    ro, src = lpm.readout_bank_sha(os.path.join(REPO, a.readout_run))
    if ro != sha:
        raise lpm.Refusal("BANK MISMATCH %s vs %s (%s)" % (sha, ro, src))
    si = mp["sites"].index(a.site); layers = list(mp["layers"])

    byk = {}
    for r in rows:
        if r["domain"] in keep:
            t = mp["reps"].get(r["prompt_id"])
            if t is not None:
                byk[((r["domain"], lpm.family_slot(r["family_id"])), r["cell"])] = t[si].float()
    keys = sorted({k for (k, _) in byk})
    comp = [k for k in keys if all((k, c) in byk for c in ("A", "B", "C", "E"))]
    doms = sorted({d for d, _ in comp})
    order = [k for d in doms for k in comp if k[0] == d]
    dof = [k[0] for k in order]
    ys = []
    for d in doms:
        ks = [k for k in comp if k[0] == d]
        my = statistics.mean([inst[k] for k in ks])
        ys += [inst[k] - my for k in ks]

    # per-layer LOO scores -> [n_slots, n_layers]
    S = []
    for li, L in enumerate(layers):
        xs = []
        for d in doms:
            ks = [k for k in comp if k[0] == d]
            mx = sum(byk[(k, "C")][li] for k in ks) / len(ks)
            xs += [byk[(k, "C")][li] - mx for k in ks]
        X = torch.stack(xs, 0); yt = torch.tensor(ys, dtype=torch.float32)
        sxy = (yt.unsqueeze(0) @ X).squeeze(0)
        sc = [0.0] * len(ys)
        for d in doms:
            idx = [i for i, dd in enumerate(dof) if dd == d]
            v = sxy - sum(X[i] * ys[i] for i in idx)
            nv = float(v.norm())
            for i in idx:
                sc[i] = float(torch.dot(X[i], v)) / nv if nv > 0 else 0.0
        S.append(sc)
    n = len(ys); nl = len(layers)
    per_layer = {layers[li]: lpm.spearman(S[li], ys) for li in range(nl)}
    best_layer = max(per_layer, key=lambda L: abs(per_layer[L]))
    # ---- section-11 trajectory features, each z-scored per layer first so a layer with a larger
    # score scale cannot dominate the sum purely by scale.
    mu = [statistics.mean(S[li]) for li in range(nl)]
    sd = [statistics.pstdev(S[li]) or 1.0 for li in range(nl)]
    Z = [[(S[li][i] - mu[li]) / sd[li] for li in range(nl)] for i in range(n)]
    Lx = [float(L) for L in layers]; mL = statistics.mean(Lx)
    den = sum((x - mL) ** 2 for x in Lx)
    feats = {
        "auc_depth": [statistics.mean(Z[i]) for i in range(n)],
        "slope_depth": [sum((Lx[li] - mL) * Z[i][li] for li in range(nl)) / den for i in range(n)],
        "late_minus_early": [statistics.mean(Z[i][nl // 2:]) - statistics.mean(Z[i][:nl // 2])
                             for i in range(n)],
        "peak_layer": [float(layers[max(range(nl), key=lambda li: Z[i][li])]) for i in range(n)],
    }
    out = {"schema": "dcs_cont_trajectory/1", "status": "EXPLORATORY", "site": a.site,
           "split": a.split, "bank_file_sha16": sha, "n_slots": n, "n_domains": len(doms),
           "layers": layers, "per_layer_rho": {str(k): v for k, v in per_layer.items()},
           "best_single_layer": {"layer": best_layer, "rho": per_layer[best_layer]},
           "trajectory_features": {}}
    print("[traj] %d slots / %d domains, site=%s" % (n, len(doms), a.site))
    print("  best SINGLE layer: L%d  rho = %+.4f" % (best_layer, per_layer[best_layer]))
    for nm, v in feats.items():
        r = lpm.spearman(v, ys)
        out["trajectory_features"][nm] = {"rho_loo": r,
                                          "beats_best_single_layer": bool(abs(r) > abs(per_layer[best_layer]))}
        print("  %-18s rho = %+.4f   %s" % (nm, r,
              "BEATS best single layer" if abs(r) > abs(per_layer[best_layer]) else "does not beat it"))
    op = os.path.join(REPO, a.out); os.makedirs(os.path.dirname(op), exist_ok=True)
    json.dump(out, open(op, "w", encoding="utf-8"), indent=1)
    print("[traj] wrote %s" % a.out)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except lpm.Refusal as e:
        print("REFUSING: %s" % e, file=sys.stderr); raise SystemExit(2)
