#!/usr/bin/env python3
"""The search redone WITHIN domain, with the null model first. C-CONT-013's prescription.

WHY THE FIRST SEARCH FAILED, IN ONE LINE
----------------------------------------
`dcs_cont_layerpos_map.py` aggregates `y_install` to the DOMAIN MEAN. Most of the family-level
variance in installation is WITHIN domain, so the between-domain component the map targets is
largely TOPIC -- and topic is readable from any state at any position. Measured: the RAW cell-C
state with no contrast at all predicts the domain-mean target BETTER than the best contrast did
(0.7504 vs 0.6972), and so does (A+B+C+E)/4, which is orthogonal to every contrast computed.

WHAT THIS FILE DOES DIFFERENTLY
-------------------------------
1. THE TARGET IS WITHIN-DOMAIN. Both x and y are centred within each domain before anything is
   fitted, so a domain-constant signal -- topic -- contributes exactly zero by construction. What
   is left is: across the slots of ONE domain, does the representation track which slots installed?
2. THE NULL MODEL RUNS FIRST AND IS REPORTED FIRST. `raw_C` (the cell-C state itself, no contrast)
   and `mean4` ((A+B+C+E)/4, orthogonal to every contrast) are computed for every cell of the map
   before any contrast is, and a contrast that does not beat them is not a finding. In the first
   search five nuisance controls were built and the null model was not among them.
3. GENERALISATION IS STILL BY DOMAIN. Slots within a domain share a demonstration pool, so a
   slot-level split would leak; the leave-one-out unit remains the DOMAIN even though the signal
   being predicted is within-domain.

DISCIPLINE: TRAIN only. EXPLORATORY. button and basket never pooled.
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
    ap.add_argument("--split", default="train", choices=["train", "validation"])
    ap.add_argument("--n-perm", type=int, default=400)
    ap.add_argument("--seed", type=int, default=20260911)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    assign = lpm.load_split()
    inst, _, kinds = lpm.load_installation(os.path.join(REPO, a.readout_run))
    mp, rows, bank_sha = lpm.load_corpus(os.path.join(REPO, a.beh_run))
    ro_sha, ro_src = lpm.readout_bank_sha(os.path.join(REPO, a.readout_run))
    if ro_sha != bank_sha:
        raise lpm.Refusal("BANK MISMATCH corpus %s vs readout %s (%s)" % (bank_sha, ro_sha, ro_src))
    keep = {d for d, s in assign.items() if s == a.split} - set(lpm.EXCLUDED_DOMAINS)
    sites, layers = list(mp["sites"]), list(mp["layers"])

    byk = {}
    for r in rows:
        if r["domain"] not in keep:
            continue
        t = mp["reps"].get(r["prompt_id"])
        if t is None:
            raise lpm.Refusal("row %r has no stack" % r["prompt_id"])
        byk[((r["domain"], lpm.family_slot(r["family_id"])), r["cell"])] = t.float()
    keys = sorted({k for (k, _) in byk})
    comp = [k for k in keys if all((k, c) in byk for c in ("A", "B", "C", "E"))]
    missing = [k for k in comp if k not in inst]
    if missing:
        raise lpm.Refusal("%d keys have a representation but no target" % len(missing))
    doms = sorted({d for d, _ in comp})
    # HOW MUCH SIGNAL IS EVEN WITHIN DOMAIN? Report it before anything is fitted.
    within, between = [], []
    gm = statistics.mean([inst[k] for k in comp])
    for d in doms:
        ks = [k for k in comp if k[0] == d]
        dm = statistics.mean([inst[k] for k in ks])
        between.append((dm - gm) ** 2 * len(ks))
        within += [(inst[k] - dm) ** 2 for k in ks]
    frac_within = sum(within) / (sum(within) + sum(between))
    print("[wd] %d keys over %d domains | y variance: %.1f%% WITHIN domain, %.1f%% between"
          % (len(comp), len(doms), 100 * frac_within, 100 * (1 - frac_within)))
    if frac_within < 0.10:
        raise lpm.Refusal("only %.1f%% of target variance is within domain; a within-domain search "
                          "has almost nothing to predict" % (100 * frac_within))

    def centred(vecs, vals):
        """Centre x and y within each domain. Returns per-key lists aligned with `comp`."""
        xs, ys = [], []
        for d in doms:
            ks = [k for k in comp if k[0] == d]
            mx = sum(vecs[k] for k in ks) / len(ks)
            my = statistics.mean([vals[k] for k in ks])
            for k in ks:
                xs.append(vecs[k] - mx)
                ys.append(vals[k] - my)
        return xs, ys

    dom_of = []
    for d in doms:
        dom_of += [d] * len([k for k in comp if k[0] == d])

    FAMILIES = ("raw_C_NULLMODEL", "mean4_NULLMODEL", "interaction",
                "C_minus_B_LEXICAL", "E_minus_A_LEXICAL")
    out = {"schema": "dcs_cont_within_domain_map/1", "status": "EXPLORATORY",
           "beh_run": a.beh_run, "readout_run": a.readout_run, "split": a.split,
           "bank_file_sha16": bank_sha, "n_keys": len(comp), "n_domains": len(doms),
           "frac_target_variance_within_domain": frac_within,
           "note": ("x and y are centred WITHIN domain, so any domain-constant signal (topic) "
                    "contributes exactly zero. The null models are computed first and a contrast "
                    "that does not beat them is not a finding."),
           "families_order": list(FAMILIES), "map": {}}

    cells_X = {}
    for si, site in enumerate(sites):
        for li, L in enumerate(layers):
            cell = {}
            for fam in FAMILIES:
                vecs = {}
                for k in comp:
                    A, B, C, E = (byk[(k, c)][si, li] for c in ("A", "B", "C", "E"))
                    vecs[k] = {"raw_C_NULLMODEL": C,
                               "mean4_NULLMODEL": (A + B + C + E) / 4,
                               "interaction": (C - B) + (E - A),
                               "C_minus_B_LEXICAL": C - B,
                               "E_minus_A_LEXICAL": E - A}[fam]
                xs, ys = centred(vecs, {k: inst[k] for k in comp})
                X = torch.stack(xs, 0)
                yt = torch.tensor(ys, dtype=torch.float32)
                # LEAVE-ONE-DOMAIN-OUT: a domain never contributes to the direction scoring it.
                scores = [0.0] * len(ys)
                sum_xy = (yt.unsqueeze(0) @ X).squeeze(0)
                for d in doms:
                    idx = [i for i, dd in enumerate(dom_of) if dd == d]
                    v = sum_xy - sum(X[i] * ys[i] for i in idx)
                    nv = float(v.norm())
                    for i in idx:
                        scores[i] = float(torch.dot(X[i], v)) / nv if nv > 0 else 0.0
                cell[fam] = lpm.spearman(scores, ys)
                cells_X.setdefault("%s|L%d" % (site, L), {})[fam] = (X, ys)
            out["map"]["%s|L%d" % (site, L)] = cell

    # ---- FAMILY-WISE NULL, PERMUTING WITHIN DOMAIN ---------------------------------------- #
    # I declared --n-perm in the first version of this file and never used it, which would have
    # published a map with no null attached under a flag implying one. The permutation must shuffle
    # y WITHIN each domain: that preserves both the domain structure and the within-domain variance,
    # so the null is "no relationship between this representation and which SLOT installed", not
    # "no domain structure", which is already removed by the centring.
    # VECTORISED. The first implementation looped 35 cells x 5 families x 200 perms x 67 domain
    # fits = 2.3 MILLION leave-one-out fits and would have run for hours. A within-domain
    # permutation only changes the PER-DOMAIN SUMS S_d = X_d^T y_d, so all B permutations can be
    # done as block matrix products: S_d = Y_d @ X_d is [B, dim], the leave-one-domain-out
    # direction is total - S_d, and the scores for that domain's rows are one batched dot product.
    import random as _rnd
    g = _rnd.Random(a.seed)
    dom_idx = {d: [i for i, dd in enumerate(dom_of) if dd == d] for d in doms}
    B = a.n_perm
    fam_max = {f: torch.zeros(B) for f in FAMILIES}
    for key, per_fam in cells_X.items():
        for fam, (X, ys) in per_fam.items():
            yt0 = torch.tensor(ys, dtype=torch.float32)
            Y = yt0.unsqueeze(0).repeat(B, 1)                       # [B, n]
            for d in doms:                                          # shuffle WITHIN each domain
                idx = dom_idx[d]
                for b in range(B):
                    sh = idx[:]; g.shuffle(sh)
                    Y[b, idx] = yt0[torch.tensor(sh)]
            S = {}
            tot = torch.zeros(B, X.shape[1])
            for d in doms:
                idx = torch.tensor(dom_idx[d])
                S[d] = Y[:, idx] @ X[idx]                           # [B, dim]
                tot = tot + S[d]
            sc = torch.zeros(B, X.shape[0])
            for d in doms:
                idx = torch.tensor(dom_idx[d])
                v = tot - S[d]                                      # [B, dim]
                nv = v.norm(dim=1).clamp_min(1e-12)
                sc[:, idx] = (X[idx].unsqueeze(0) * v.unsqueeze(1)).sum(2) / nv.unsqueeze(1)
            for b in range(B):
                r = abs(lpm.spearman([float(x) for x in sc[b]], [float(x) for x in Y[b]]))
                if r > float(fam_max[fam][b]):
                    fam_max[fam][b] = r
    fam_max = {f: [float(x) for x in v] for f, v in fam_max.items()}

    def pct(v, q):
        w = sorted(v); return w[min(len(w) - 1, int(q * len(w)))]
    out["permutation_null"] = {
        "n_perm": a.n_perm, "seed": a.seed,
        "unit_shuffled": "y_install WITHIN each domain (preserves domain structure and within-domain variance)",
        "per_family": {f: {"p50": pct(v, .50), "p95": pct(v, .95), "p99": pct(v, .99)}
                       for f, v in fam_max.items()},
        "n_cells_per_family": len(cells_X)}
    for f in FAMILIES:
        thr = out["permutation_null"]["per_family"][f]["p95"]
        for key in out["map"]:
            out["map"][key]["%s__exceeds_fwer95" % f] = bool(abs(out["map"][key][f]) > thr)

    os.makedirs(os.path.dirname(os.path.join(REPO, a.out)), exist_ok=True)
    json.dump(out, open(os.path.join(REPO, a.out), "w"), indent=1)
    print("[wd] wrote %s" % a.out)
    for fam in FAMILIES:
        best = sorted(out["map"].items(), key=lambda kv: -abs(kv[1][fam]))[:4]
        tag = "  <- NULL MODEL" if "NULLMODEL" in fam else ""
        thr = out["permutation_null"]["per_family"][fam]["p95"]
        nex = sum(1 for v in out["map"].values() if abs(v[fam]) > thr)
        print("  %-22s p95_null=%.4f  cells>p95: %2d/%d  top: %s%s"
              % (fam, thr, nex, len(out["map"]),
                 ", ".join("%s=%+.4f" % (k, v[fam]) for k, v in best), tag))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except lpm.Refusal as e:
        print("REFUSING: %s" % e, file=sys.stderr); raise SystemExit(2)
