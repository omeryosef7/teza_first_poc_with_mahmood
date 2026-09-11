#!/usr/bin/env python3
"""Mandate section 15: matched reference geometry, with every contrast and its OWN null.

WHY THIS FILE EXISTS. CONT-ENTRY 077/078/079/082 were run as heredocs. Only their JSON outputs were
committed, so when REVIEW-3 found the p-values were computed against the wrong quantity there was no
code on disk to adjudicate it (REVIEW-3/CODE-5, REVIEW-3/STATISTICAL-5 and item 10). This script is
the adjudicable version.

THE BUG IT FIXES (C-CONT-059). The heredoc accumulated `spearman(cB, y_perm)` -- the null of rho_B --
and printed that p beside the B-minus-ctx difference. Bomb was unaffected (both at the floor) but
knife's "significant" +0.0623 is p=0.0845 against its own null. Here every reported quantity is
permuted against ITSELF.

THE COMPARATORS, AND WHY MORE THAN ONE (C-CONT-059, REVIEW-3/STATISTICAL-7,8).
  B - ctx  : the original. `ctx` = cos to the mean of the A and E states. Its rho sits near zero by
             CANCELLATION (rho_A negative, rho_E positive), which flatters the gap. Reported, but not
             as the headline.
  B - E    : the fair single-reference contrast. E is the same concept in a benign context, so this
             isolates "explicit concept in HARMFUL context" from "explicit concept".
  mismatch : cos to a DIFFERENT slot's B state from the same domain. If this matches or beats the
             matched pairing, the token-level alignment section 15 asks for is doing no work.
  proto    : cos to the domain-mean of all B states. Same question, stronger form.
"""
from __future__ import annotations
import argparse, importlib.util, json, os, random, statistics, sys, torch

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def _load(mod, path):
    s = importlib.util.spec_from_file_location(mod, os.path.join(REPO, path))
    m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", required=True)
    ap.add_argument("--readout", required=True)
    ap.add_argument("--label", required=True)
    ap.add_argument("--site", default="cw_demo_mean")
    ap.add_argument("--layers", default="14,24")
    ap.add_argument("--n-perm", type=int, default=2000)
    ap.add_argument("--seed", type=int, default=20260911)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    lpm = _load("lpm", "scripts/dcs_cont_layerpos_map.py")
    cos = torch.nn.functional.cosine_similarity
    mp, rows, _ = lpm.load_corpus(os.path.join(REPO, a.corpus))
    inst, _, _ = lpm.load_installation(os.path.join(REPO, a.readout))
    assign = lpm.load_split(); EX = set(lpm.EXCLUDED_DOMAINS)
    if any(assign.get(r["domain"]) == "test" for r in rows):
        print("REFUSING: corpus contains test-split rows"); return 2
    keep = {d for d, v in assign.items() if v in ("train", "validation")} - EX
    meta = json.load(open(os.path.join(REPO, a.corpus, "metadata.json")))

    byk = {}
    for r in rows:
        if r["domain"] in keep:
            t = mp["reps"].get(r["prompt_id"])
            if t is not None:
                byk[((r["domain"], lpm.family_slot(r["family_id"])), r["cell"])] = t.float()
    comp = [k for k in sorted({k for k, _ in byk}) if all((k, c) in byk for c in "ABCE") and k in inst]
    doms = sorted({d for d, _ in comp})
    order = [k for d in doms for k in comp if k[0] == d]
    dof = [k[0] for k in order]
    si = mp["sites"].index(a.site)

    def centre(v):
        o = [0.0] * len(v)
        for d in doms:
            idx = [i for i, q in enumerate(dof) if q == d]
            m = statistics.mean(v[i] for i in idx)
            for i in idx: o[i] = v[i] - m
        return o

    out = {"label": a.label, "corpus": a.corpus, "readout": a.readout, "site": a.site,
           "bank_file_sha16": meta.get("bank_file_sha16"), "n_slots": len(order),
           "n_domains": len(doms), "n_perm": a.n_perm, "seed": a.seed,
           "population": "train+validation", "by_layer": {}}

    for L in [int(x) for x in a.layers.split(",")]:
        if L not in mp["layers"]:
            continue
        li = mp["layers"].index(L)
        g = random.Random(a.seed)
        B = []; A = []; E = []; X = []; MM = []; PR = []; Y = []
        for k in order:
            h = byk[(k, "C")][si, li]
            B.append(float(cos(h, byk[(k, "B")][si, li], dim=0)))
            A.append(float(cos(h, byk[(k, "A")][si, li], dim=0)))
            E.append(float(cos(h, byk[(k, "E")][si, li], dim=0)))
            X.append(float(cos(h, (byk[(k, "A")][si, li] + byk[(k, "E")][si, li]) / 2, dim=0)))
            sib = [q for q in comp if q[0] == k[0] and q != k]
            MM.append(float(cos(h, byk[(g.choice(sib), "B")][si, li], dim=0)) if sib else float("nan"))
            ks = [q for q in comp if q[0] == k[0]]
            PR.append(float(cos(h, torch.stack([byk[(q, "B")][si, li] for q in ks], 0).mean(0), dim=0)))
            Y.append(inst[k])
        cB, cA, cE, cX, cMM, cPR, cY = map(centre, (B, A, E, X, MM, PR, Y))
        stats = {n: lpm.spearman(v, cY) for n, v in
                 (("rho_B", cB), ("rho_A", cA), ("rho_E", cE), ("rho_ctx", cX),
                  ("rho_mismatch", cMM), ("rho_prototype", cPR))}
        stats["B_minus_ctx"] = stats["rho_B"] - stats["rho_ctx"]
        stats["B_minus_E"] = stats["rho_B"] - stats["rho_E"]
        stats["matched_minus_mismatch"] = stats["rho_B"] - stats["rho_mismatch"]

        # EVERY quantity permuted against ITSELF -- the C-CONT-059 fix.
        gg = random.Random(a.seed)
        nulls = {k2: [] for k2 in stats}
        for _ in range(a.n_perm):
            yp = list(cY)
            for d in doms:
                idx = [i for i, q in enumerate(dof) if q == d]
                vv = [cY[i] for i in idx]; gg.shuffle(vv)
                for j, i in enumerate(idx): yp[i] = vv[j]
            rb = lpm.spearman(cB, yp); rx = lpm.spearman(cX, yp)
            re = lpm.spearman(cE, yp); rm = lpm.spearman(cMM, yp)
            nulls["rho_B"].append(rb); nulls["rho_ctx"].append(rx)
            nulls["rho_E"].append(re); nulls["rho_A"].append(lpm.spearman(cA, yp))
            nulls["rho_mismatch"].append(rm)
            nulls["rho_prototype"].append(lpm.spearman(cPR, yp))
            nulls["B_minus_ctx"].append(rb - rx)
            nulls["B_minus_E"].append(rb - re)
            nulls["matched_minus_mismatch"].append(rb - rm)
        res = {}
        for k2, v in stats.items():
            nl = sorted(nulls[k2])
            p = (sum(1 for x in nl if x >= v) + 1) / (a.n_perm + 1)
            res[k2] = {"value": v, "p_against_its_own_null": p,
                       "p_is_floor": p <= 1.0 / (a.n_perm + 1) + 1e-12,
                       "null_p95": nl[int(0.95 * a.n_perm)]}
        out["by_layer"][str(L)] = res
        print("[s15] %-13s L%-3d B %+.4f (p=%.4f) | B-E %+.4f (p=%.4f) | B-ctx %+.4f (p=%.4f) | "
              "matched-mismatch %+.4f (p=%.4f) | proto %+.4f"
              % (a.label, L, res["rho_B"]["value"], res["rho_B"]["p_against_its_own_null"],
                 res["B_minus_E"]["value"], res["B_minus_E"]["p_against_its_own_null"],
                 res["B_minus_ctx"]["value"], res["B_minus_ctx"]["p_against_its_own_null"],
                 res["matched_minus_mismatch"]["value"],
                 res["matched_minus_mismatch"]["p_against_its_own_null"],
                 res["rho_prototype"]["value"]))
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    json.dump(out, open(a.out, "w"), indent=1)
    print("[s15] wrote %s" % a.out)
    return 0

if __name__ == "__main__":
    sys.exit(main())
