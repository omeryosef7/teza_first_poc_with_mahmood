#!/usr/bin/env python3
"""PR-HCSI-S084 DESCRIPTIVE basket-vs-button contrast on VALIDATION (never a pass/fail).

Cells (original 56-control families, matched size): basket r1 968532, basket r4 1022699, button r1 968534,
button r4 1022698. Per cell: z = (e_cand - mean_ctrl e) / sd_ctrl e, e_arm = mean over domains of
(domain-mean y_install[arm] - domain-mean y_install[KO]), rows filtered by the BASE-referenced option-mass
floor 0.05 (frozen rule). Interaction I = (z_btn_r4 - z_btn_r1) - (z_bsk_r4 - z_bsk_r1); 95% CI by a
domain-cluster bootstrap resampling the shared VALIDATION domains jointly across all four cells.
Loaders reuse F3's independent verifier (verify_s049: run dirs from sweep logs, y = logistic(lp_c - lp_cw)).
"""
import json, os, sys
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "verify"))
import verify_s049 as V

CELLS = {("basket", 1): 968532, ("basket", 4): 1022699, ("button", 1): 968534, ("button", 4): 1022698}
OUT = os.path.join(V.ROOT, "reports/heretic_csi/P2A_BUTTON_R4_CONTRAST.json")


def cell_domain_table(job, rank):
    dirs = V.run_dirs(job)
    data = {a: V.load(d)[0] for a, d in dirs.items()}
    keep = {r["prompt_id"] for r in data["BASE"] if r["option_mass"] >= 0.05}
    pd = {a: V.per_domain(rows, keep) for a, rows in data.items()}
    cand = f"KO_CAND_r{rank}"
    ctrls = sorted(a for a in dirs if a.startswith((f"KO_RAND_r{rank}_", f"KO_SHUF_r{rank}_")))
    assert len(ctrls) == 56, (job, len(ctrls))
    doms = sorted(pd["KO"])
    # matrix [arm, domain] of (arm - KO) domain means
    arms = [cand] + ctrls
    M = np.array([[pd[a][d] - pd["KO"][d] for d in doms] for a in arms])
    return doms, M, len(keep)


def z_of(M, idx):
    e = M[:, idx].mean(axis=1)
    return float((e[0] - e[1:].mean()) / e[1:].std(ddof=1))


def main():
    tabs = {k: cell_domain_table(j, k[1]) for k, j in CELLS.items()}
    doms = tabs[("basket", 1)][0]
    assert all(t[0] == doms for t in tabs.values()), "cells must share the same VALIDATION domains"
    allidx = np.arange(len(doms))
    z = {k: z_of(t[1], allidx) for k, t in tabs.items()}
    I = lambda zz: (zz[("button", 4)] - zz[("button", 1)]) - (zz[("basket", 4)] - zz[("basket", 1)])
    rng = np.random.default_rng(20261014)
    boots = []
    for _ in range(2000):
        idx = rng.integers(0, len(doms), len(doms))
        boots.append(I({k: z_of(t[1], idx) for k, t in tabs.items()}))
    lo, hi = np.percentile(boots, [2.5, 97.5])
    res = {"prereg": "PR-HCSI-S084 (descriptive contrast)", "n_domains": len(doms),
           "rows_after_base_floor": {f"{k[0]}_r{k[1]}": tabs[k][2] for k in tabs},
           "z": {f"{k[0]}_r{k[1]}": round(v, 3) for k, v in z.items()},
           "interaction_I": round(I(z), 3), "I_ci95": [round(float(lo), 3), round(float(hi), 3)],
           "interpretation_frozen": "I>0 with CI excluding 0 is CONSISTENT WITH button gaining specificity r1->r4 more than basket; otherwise unsupported by a contrast. DESCRIPTIVE only."}
    json.dump(res, open(OUT, "w"), indent=1)
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
