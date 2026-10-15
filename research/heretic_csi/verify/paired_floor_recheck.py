#!/usr/bin/env python3
"""F3 re-check of the paired-floor numbers: (A) per-arm survivors (what verify_s049 did: each arm's domain means over
the floor-kept ids THAT ARM HAS) vs (B) common keys (floor-kept ids present in EVERY arm of the pool + liveness)."""
import sys, os, json, collections
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
import verify_s049 as V
V.JOBS.update({1022698: ("button", 4, "validation"), 1022699: ("basket", 4, "validation")})
CELLS = [966084, 968532, 1022699, 1022698, 966157, 968534]


def run(job, floor_mode, common):
    cw, rank, split = V.JOBS[job]
    dirs = V.run_dirs(job); data = {a: V.load(d)[0] for a, d in dirs.items()}
    ids = {r["prompt_id"] for r in data["BASE"]}
    ok = lambda a: {r["prompt_id"] for r in data[a] if r["option_mass"] >= 0.05}
    keep = ids & ok("BASE")
    if floor_mode == "strict":
        keep &= ok("KO") & ok("KO_FULL")
    cand = f"KO_CAND_r{rank}"
    ctrls = sorted(a for a in dirs if a.startswith((f"KO_RAND_r{rank}_", f"KO_SHUF_r{rank}_")))
    arms = ["BASE", "KO", "KO_SELF", "KO_FULL", cand] + ctrls
    if common:
        for a in arms:
            keep &= {r["prompt_id"] for r in data[a]}
    pd = {a: V.per_domain(data[a], keep) for a in arms}
    D = sorted(pd["KO"])
    st = {a: float(np.mean([pd[a][d] - pd["KO"][d] for d in D if d in pd[a]])) for a in [cand] + ctrls}
    rk_strict = 1 + sum(st[a] > st[cand] for a in ctrls)
    rk_ties = 1 + sum(st[a] >= st[cand] for a in ctrls)
    num = sum(pd[cand][d] - pd["KO"][d] for d in D); den = sum(pd["KO_FULL"][d] - pd["KO"][d] for d in D)
    best = max(ctrls, key=lambda a: st[a])
    short = {a: len(ids) - len({r['prompt_id'] for r in data[a]}) for a in arms if len({r['prompt_id'] for r in data[a]}) < len(ids)}
    return {"job": job, "codeword": cw, "rank": rank, "split": split, "floor": floor_mode,
            "computation": "B_common_keys" if common else "A_per_arm_survivors",
            "n_rows_kept(BASE-arm count)": len(keep), "n_domains": len(D), "cand_stat": st[cand], "test_rank": rk_strict,
            "test_rank_ties_against": rk_ties, "n_controls": len(ctrls), "p": rk_ties / (len(ctrls) + 1), "recovery": num / den,
            "best_control": best, "best_control_stat": st[best], "margin": st[cand] - st[best], "n_short_arms": len(short),
            "max_rows_short": max(short.values()) if short else 0}


if __name__ == "__main__":
    out = []
    for j in CELLS:
        for fm in ("base", "strict"):
            for common in (False, True):
                r = run(j, fm, common); out.append(r)
                print(f"{r['codeword']:6s} r{r['rank']:<2d} {r['split']:10s} {fm:6s} {r['computation']:20s} rows={r['n_rows_kept(BASE-arm count)']:4d} "
                      f"rank={r['test_rank']}/{r['n_controls']+1} (ties-against {r['test_rank_ties_against']}) p={r['p']:.4f} rec={r['recovery']:.4f} "
                      f"cand={r['cand_stat']:.5f} best={r['best_control']}:{r['best_control_stat']:.5f} short_arms={r['n_short_arms']}(max {r['max_rows_short']})", flush=True)
    json.dump({"schema": "hcsi_verify_paired_floor_recheck/1", "rows": out},
              open(f"{V.ROOT}/reports/heretic_csi/VERIFY_PAIRED_FLOOR_RECHECK.json", "w"), indent=1)
