#!/usr/bin/env python3
"""F3 independent verification of PR-HCSI-S051 (rank-4 VALIDATION): jobs 1022698 (button, primary) and
1022699 (basket, descriptive). Reuses ONLY F3's own verify_s049.py (independent of the frozen analyzer) and adds
the candidate-vs-best-control margin and a leave-one-domain-out (LODO) rank check."""
import json, sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
import verify_s049 as V

V.JOBS[1022698] = ("button", 4, "validation")
V.JOBS[1022699] = ("basket", 4, "validation")
OUT = f"{V.ROOT}/reports/heretic_csi/VERIFY_S072_r4_validation.json"


def margin_and_lodo(job, floor_mode):
    cw, rank, _ = V.JOBS[job]
    dirs = V.run_dirs(job)
    data = {a: V.load(d) for a, d in dirs.items()}
    all_ids = {r["prompt_id"] for r in data["BASE"][0]}
    ok = lambda arm: {r["prompt_id"] for r in data[arm][0] if r["option_mass"] >= 0.05}
    keep = {"base": all_ids & ok("BASE"), "base_ko_full": all_ids & ok("BASE") & ok("KO") & ok("KO_FULL"),
            "none": all_ids}[floor_mode]
    pd = {a: V.per_domain(rows, keep) for a, (rows, _, _) in data.items()}
    cand = f"KO_CAND_r{rank}"
    ctrls = sorted(a for a in dirs if a.startswith((f"KO_RAND_r{rank}_", f"KO_SHUF_r{rank}_")))
    D = sorted(pd["KO"])

    def eff(a, doms):
        return float(np.mean([pd[a][d] - pd["KO"][d] for d in doms if d in pd[a]]))
    e = {a: eff(a, D) for a in [cand] + ctrls}
    best = max(ctrls, key=lambda a: e[a])
    cand_minus_ko_per_dom = [pd[cand][d] - pd["KO"][d] for d in D]
    lodo = []
    for d in D:
        dd = [x for x in D if x != d]
        ee = {a: eff(a, dd) for a in [cand] + ctrls}
        lodo.append({"dropped": d, "rank": 1 + sum(ee[a] > ee[cand] for a in ctrls)})
    rng = np.random.default_rng(0)
    boots = [float(np.mean(rng.choice(cand_minus_ko_per_dom, len(D)))) for _ in range(4000)]
    return {"floor_mode": floor_mode, "cand_effect_dKO": e[cand], "best_control": best, "best_control_effect": e[best],
            "margin_cand_minus_best_control": e[cand] - e[best],
            "margin_over_control_sd": (e[cand] - e[best]) / float(np.std([e[a] for a in ctrls], ddof=1)),
            "control_effect_mean": float(np.mean([e[a] for a in ctrls])),
            "cand_minus_KO_CI95_domain_boot": [float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5))],
            "n_domains_cand_gt_KO": int(sum(v > 0 for v in cand_minus_ko_per_dom)), "n_domains": len(D),
            "lodo_ranks": sorted({x["rank"] for x in lodo}), "lodo_max_rank": max(x["rank"] for x in lodo),
            "lodo_domains_breaking_rank1": [x for x in lodo if x["rank"] > 1]}


if __name__ == "__main__":
    jobs = [int(x) for x in sys.argv[1].split(",")]
    try:
        res = json.load(open(OUT))
    except Exception:
        res = {"schema": "hcsi_verify_s072/1", "prereg": "configs/heretic_csi/prereg_S051_rank4_validation.json", "cells": {}}
    res["pt_rank_check"] = {cw: V.check_pt(cw) for cw in ("basket", "button")}
    q = {}
    for j in jobs:
        c = V.analyse(j, floor_mode="base")
        c["sensitivity_strict_floor"] = {k: v for k, v in V.analyse(j, floor_mode="base_ko_full").items()
                                         if k in ("test_rank", "p_rank", "recovery_fraction", "recovery_CI95_domain_bootstrap", "n_rows_after_floor")}
        c["sensitivity_no_floor"] = {k: v for k, v in V.analyse(j, floor_mode="none").items()
                                     if k in ("test_rank", "p_rank", "recovery_fraction", "n_rows_after_floor")}
        c["margin_lodo"] = {fm: margin_and_lodo(j, fm) for fm in ("base", "base_ko_full")}
        c["mutations"] = {"swap_candidate_p": [V.analyse(j, floor_mode="base", mutate="swap_candidate", seed=s)["p_rank"] for s in range(20)],
                          "shuffle_arm_identity_p": [V.analyse(j, floor_mode="base", mutate="shuffle_domain_labels", seed=s)["p_rank"] for s in range(20)]}
        c["quarantined_unreferenced_dirs"] = V.QUAR.get(j, [])
        res["cells"][str(j)] = c
        print(json.dumps({k: c[k] for k in ("codeword", "rank", "split", "n_rows_BASE", "n_domains", "domain_split_counts", "TEST_present",
                                             "n_rows_after_floor", "test_rank", "p_rank", "recovery_fraction", "recovery_CI95_domain_bootstrap",
                                             "KO_minus_BASE", "KO_SELF_minus_KO", "KO_FULL_minus_KO", "n_controls", "live_ranks",
                                             "control_vs_cand_written_norm_relerr_max", "arms_short", "all_DONE_ok", "distinct_basis_keys", "seeds")}, indent=0))
        print(json.dumps(c["sensitivity_strict_floor"]), json.dumps(c["sensitivity_no_floor"]))
        print(json.dumps(c["margin_lodo"], indent=0))
        print("mut medians", np.median(c["mutations"]["swap_candidate_p"]), np.median(c["mutations"]["shuffle_arm_identity_p"]))
    json.dump(res, open(OUT, "w"), indent=1)
    print("wrote", OUT)
