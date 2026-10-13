#!/usr/bin/env python3
"""HERETIC-CSI P5/C1: HELD-OUT (VALIDATION) probe quality per codeword.

S-043 quantified C1 ("basket simply has a better probe") with TRAIN leave-one-domain-out rho only.
This computes the held-out analogue: fit on TRAIN domains (minus EXCLUDED), score on VALIDATION
domains, same construction as scripts/dcs_csi_axis.py (REUSED unchanged: build / ridge_w / pls1),
same site (rel-6) and layer (18, forced, matching the rescue layer).

Per rank r in --ranks: PLS(r) fit on TRAIN -> OLS head on TRAIN projections -> predict VALIDATION.
Also ridge (full-dim, lambda=100). Statistic: Spearman(pred, y) over within-domain-centred VALIDATION
rows (the identical statistic axis.py uses). Uncertainty: domain-cluster bootstrap (unit = domain).
Null: within-domain label shuffle on TRAIN (axis.shuffled_y), refit, score on VALIDATION.
TEST is never read (axis/lpm refuse a corpus containing TEST domains).
"""
from __future__ import annotations
import argparse, json, os, random, sys, hashlib
import torch

REPO = "/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
sys.path.insert(0, os.path.join(REPO, "scripts"))
import importlib.util


def _load(mod, rel):
    s = importlib.util.spec_from_file_location(mod, os.path.join(REPO, rel))
    m = importlib.util.module_from_spec(s); sys.modules[mod] = m; s.loader.exec_module(m); return m


def boot_ci(lpm, pred, y, dof, n=2000, seed=0):
    doms = sorted(set(dof)); rng = random.Random(seed)
    by = {d: [i for i, x in enumerate(dof) if x == d] for d in doms}
    vals = []
    for _ in range(n):
        idx = [i for d in (rng.choice(doms) for _ in doms) for i in by[d]]
        vals.append(lpm.spearman([pred[i] for i in idx], [y[i] for i in idx]))
    vals.sort()
    return [vals[int(0.025 * n)], vals[int(0.975 * n) - 1]]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--codeword", required=True)
    ap.add_argument("--corpus", required=True)
    ap.add_argument("--readout", required=True)
    ap.add_argument("--layer", type=int, default=18)
    ap.add_argument("--site", default="rel-6")
    ap.add_argument("--ranks", default="1,2,3,4,8,16,32")
    ap.add_argument("--n-shuffle", type=int, default=20)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    ax = _load("dcs_csi_axis", "scripts/dcs_csi_axis.py")
    lpm = _load("lpm", "scripts/dcs_cont_layerpos_map.py")
    assign = lpm.load_split(); EX = set(lpm.EXCLUDED_DOMAINS)
    TR = {d for d, v in assign.items() if v == "train"} - EX
    VA = {d for d, v in assign.items() if v == "validation"} - EX
    inst, n_inst, kinds = lpm.load_installation(os.path.join(REPO, a.readout))
    mp, rows, csha = lpm.load_corpus(os.path.join(REPO, a.corpus), mmap=True, allow_query_kinds=("behavioral",))
    rsha, _ = lpm.readout_bank_sha(os.path.join(REPO, a.readout))
    if rsha != csha:
        raise SystemExit("REFUSING: corpus/readout bank sha mismatch")
    if any(assign.get(r["domain"]) == "test" for r in rows):
        raise SystemExit("REFUSING: corpus contains TEST domains")
    S, Ls = list(mp["sites"]), list(mp["layers"])
    cd = {r["domain"] for r in rows}
    Xtr, ytr, dtr, domtr, _ = ax.build(lpm, mp, rows, inst, S, Ls, cd & TR, a.site, a.layer)
    Xva, yva, dva, domva, _ = ax.build(lpm, mp, rows, inst, S, Ls, cd & VA, a.site, a.layer)
    assert not (set(domtr) & set(domva)), "train/validation domain overlap"

    def heldout_pls(Xt, yt, r):
        W = ax.pls1(Xt, yt, r)
        beta = torch.linalg.lstsq(Xt @ W.T, yt.unsqueeze(1)).solution.squeeze(1)
        return ((Xva @ W.T) @ beta).tolist(), int(W.shape[0])

    res = {"schema": "hcsi_p6_heldout_probe/1", "codeword": a.codeword, "layer": a.layer, "site": a.site,
           "corpus": a.corpus, "readout": a.readout, "bank_sha16": csha,
           "n_train_rows": len(ytr), "n_train_domains": len(domtr),
           "n_val_rows": len(yva), "n_val_domains": len(domva),
           "val_domains_sha16": hashlib.sha256("|".join(domva).encode()).hexdigest()[:16],
           "statistic": "Spearman(pred,y) over within-domain-centred VALIDATION rows; fit TRAIN only",
           "ci": "95% domain-cluster bootstrap (2000)", "by_rank": {}}
    yv = yva.tolist()
    for r in [int(x) for x in a.ranks.split(",")]:
        pred, rr = heldout_pls(Xtr, ytr, r)
        rho = lpm.spearman(pred, yv)
        null = []
        for s in range(a.n_shuffle):
            yp = ax.shuffled_y(ytr, dtr, domtr, 1000 + s)
            pn, _ = heldout_pls(Xtr, yp, r)
            null.append(lpm.spearman(pn, yv))
        ge = sum(1 for v in null if v >= rho)
        res["by_rank"][str(r)] = {"rank_effective": rr, "val_rho": round(rho, 4),
                                  "ci95": [round(v, 4) for v in boot_ci(lpm, pred, yv, dva)],
                                  "shuffle_null_mean": round(sum(null) / len(null), 4),
                                  "shuffle_null_max": round(max(null), 4),
                                  "shuffle_rank_p": round((ge + 1) / (len(null) + 1), 4)}
        print(a.codeword, "rank", r, res["by_rank"][str(r)], flush=True)
    w = ax.ridge_w(Xtr, ytr)
    pr = (Xva @ w).tolist()
    res["ridge_full"] = {"val_rho": round(lpm.spearman(pr, yv), 4),
                         "ci95": [round(v, 4) for v in boot_ci(lpm, pr, yv, dva)]}
    print(a.codeword, "ridge", res["ridge_full"])
    json.dump(res, open(a.out, "w"), indent=2)
    print("DONE_MARKER", a.out)


if __name__ == "__main__":
    main()
