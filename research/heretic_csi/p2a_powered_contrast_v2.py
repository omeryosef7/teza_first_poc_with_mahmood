#!/usr/bin/env python3
"""PR-HCSI-S084 DESCRIPTIVE contrast, v2 (supersedes p2a_powered_contrast.py; review #3 findings 1-2).

Fix: every arm in a cell is averaged over the rows COMMON to ALL arms of that cell (intersection of prompt_ids,
then the BASE-referenced option-mass floor 0.05), exactly like the frozen analyzer's common-key set. v1
averaged each arm over its own surviving rows (several RAND_r1 arms are 1-2 rows short), which is wrong.
Reports z per codeword/rank and the interaction I under three control families: RAND-only, SHUF-only,
pooled (RAND+SHUF). Descriptive only. Output -> NEW file P2A_BUTTON_R4_CONTRAST_v2.json (v1 kept).
"""
import collections, json, math, os, sys
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "verify"))
import verify_s049 as V

CELLS = {("basket", 1): 968532, ("basket", 4): 1022699, ("button", 1): 968534, ("button", 4): 1022698}
OUT = os.path.join(V.ROOT, "reports/heretic_csi/P2A_BUTTON_R4_CONTRAST_v2.json")
FAMS = ("rand", "shuf", "pooled")


def cell(job, rank):
    dirs = V.run_dirs(job)
    data = {a: V.load(d)[0] for a, d in dirs.items()}
    base_ok = {r["prompt_id"] for r in data["BASE"] if r["option_mass"] >= 0.05}
    common = set.intersection(*[{r["prompt_id"] for r in rows} for rows in data.values()]) & base_ok
    def dom_means(rows):
        acc = collections.defaultdict(list)
        for r in rows:
            if r["prompt_id"] in common:
                acc[r["domain"]].append(1 / (1 + math.exp(-(r["logp_concept"] - r["logp_codeword"]))))
        return {d: float(np.mean(v)) for d, v in acc.items()}
    pd = {a: dom_means(rows) for a, rows in data.items()}
    doms = sorted(pd["KO"])
    cand = f"KO_CAND_r{rank}"
    rand = sorted(a for a in dirs if a.startswith(f"KO_RAND_r{rank}_"))
    shuf = sorted(a for a in dirs if a.startswith(f"KO_SHUF_r{rank}_"))
    assert len(rand) == 46 and len(shuf) == 10, (job, len(rand), len(shuf))
    arms = [cand] + rand + shuf
    M = np.array([[pd[a][d] - pd["KO"][d] for d in doms] for a in arms])
    return doms, M, len(common), len(rand)


def z_of(M, idx, nrand, fam):
    e = M[:, idx].mean(axis=1)
    c = {"rand": e[1:1 + nrand], "shuf": e[1 + nrand:], "pooled": e[1:]}[fam]
    return float((e[0] - c.mean()) / c.std(ddof=1))


def main():
    tabs = {k: cell(j, k[1]) for k, j in CELLS.items()}
    doms = tabs[("basket", 1)][0]
    assert all(t[0] == doms for t in tabs.values())
    allidx = np.arange(len(doms))
    I = lambda zz: (zz[("button", 4)] - zz[("button", 1)]) - (zz[("basket", 4)] - zz[("basket", 1)])
    out = {"prereg": "PR-HCSI-S084 descriptive contrast v2 (common-row fix)", "supersedes": "P2A_BUTTON_R4_CONTRAST.json",
           "n_domains": len(doms), "n_common_rows": {f"{k[0]}_r{k[1]}": t[2] for k, t in tabs.items()}, "by_family": {}}
    rng = np.random.default_rng(20261014)
    idxs = [rng.integers(0, len(doms), len(doms)) for _ in range(2000)]
    for fam in FAMS:
        z = {k: z_of(t[1], allidx, t[3], fam) for k, t in tabs.items()}
        boots = [I({k: z_of(t[1], ix, t[3], fam) for k, t in tabs.items()}) for ix in idxs]
        lo, hi = np.percentile(boots, [2.5, 97.5])
        out["by_family"][fam] = {"z": {f"{k[0]}_r{k[1]}": round(v, 3) for k, v in z.items()},
                                 "interaction_I": round(I(z), 3), "I_ci95": [round(float(lo), 3), round(float(hi), 3)]}
    out["reading"] = "DESCRIPTIVE. The interaction's sign/size depends on the control family; see by_family."
    json.dump(out, open(OUT, "w"), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
