"""judge_pass_interval.py — an interval on the p-value, not a point estimate of it.

WHY. Every arm in this sprint produces one-directional flips, so its cluster sign-flip p equals its
attainable floor `2/2^k` with k = the number of INFORMATIVE DOMAINS. The p is therefore a count, and one
prompt crossing the judge's 0.5 threshold can move a whole domain in or out. Measured fragility: pushing
a layer above 0.05 needs 2-4 rows out of 495, and judge noise between passes is 0-2 rows.

So "p = 0.0039" was never the right object. This assembles every independent judge pass over
BYTE-IDENTICAL generations and reports the RANGE of the delta, the flip count and the p, which is what
a reader needs in order to know whether a layer's significance is a property of the model or of which
judge pass happened to be quoted.

A pass is a (baseline, arm) pair judged together. Passes must not be mixed across baselines: the
2026-08-22 finding that L8 moved 3.5x on ZERO arm-row changes -- the row that moved was in the BASELINE
-- is exactly what mixing would hide.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import statistics as st
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import read_jsonl  # noqa: E402
from unanalysed_inventory import git_commit_safe  # noqa: E402

J = "outputs/boombness/judge"

#: label -> (baseline glob, arm glob per layer template)
PASSES = {
    "pass1": (f"{J}/abg_base_*", {8: f"{J}/abg_B_*", 12: f"{J}/abgL12_B_*"}),
    "pass2_abrep": (f"{J}/abrep_base_*", {8: f"{J}/abrep_L8_*", 12: f"{J}/abrep_L12_*"}),
    "pass3": (f"{J}/rjp3_base_*", {8: f"{J}/rjp3_L8_*", 12: f"{J}/rjp3_L12_*"}),
    "pass4": (f"{J}/rjp4_base_*", {8: f"{J}/rjp4_L8_*", 12: f"{J}/rjp4_L12_*"}),
}


def rows(pat):
    m = {}
    for d in sorted(glob.glob(pat)):
        f = os.path.join(d, "results.jsonl")
        if os.path.exists(f):
            for r in read_jsonl(f):
                if r.get("strongreject_score") is not None:
                    m[r["prompt_id"]] = r
    return m


def stats(base, arm, thr):
    import itertools
    ids = sorted(set(base) & set(arm))
    if not ids:
        return None
    suc = lambda r: r["strongreject_score"] >= thr
    dom = {}
    for i in ids:
        dom.setdefault(base[i].get("domain"), []).append(int(suc(arm[i])) - int(suc(base[i])))
    nets = [sum(v) for v in dom.values()]
    inf = [v for v in nets if v != 0]
    obs = sum(nets) / len(ids)
    if not inf:
        return {"n": len(ids), "delta": obs, "net": 0, "k": 0, "p": 1.0}
    cnt = sum(1 for s in itertools.product((1, -1), repeat=len(inf))
              if abs(sum(a * b for a, b in zip(s, inf)) / len(ids)) >= abs(obs) - 1e-12)
    return {"n": len(ids), "delta": obs, "net": sum(nets), "k": len(inf),
            "p": cnt / 2 ** len(inf), "floor": 2.0 / 2 ** len(inf)}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--threshold", type=float, default=0.5)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    res, incomplete = {}, []
    for pname, (bpat, arms) in PASSES.items():
        base = rows(bpat)
        if len(base) < 495:
            incomplete.append(f"{pname}:baseline({len(base)})")
            continue
        for L, apat in arms.items():
            arm = rows(apat)
            if len(arm) < 495:
                incomplete.append(f"{pname}:L{L}({len(arm)})")
                continue
            s = stats(base, arm, args.threshold)
            if s:
                res.setdefault(f"L{L}", {})[pname] = s

    doc = {"question": "how much does a layer's significance depend on WHICH judge pass is quoted?",
           "why": "flips are one-directional, so p = 2/2^k with k = informative domains; the p is a "
                  "count and 1-2 rows of judge noise can move a domain in or out",
           "threshold": args.threshold, "incomplete_passes": incomplete, "by_layer": {}}
    for L, passes in sorted(res.items()):
        ps = [v["p"] for v in passes.values()]
        ds = [v["delta"] for v in passes.values()]
        ks = [v["k"] for v in passes.values()]
        doc["by_layer"][L] = {
            "passes": passes, "n_passes": len(ps),
            "p_min": min(ps), "p_max": max(ps), "p_range_factor": (max(ps) / min(ps)) if min(ps) else None,
            "delta_min": min(ds), "delta_max": max(ds),
            "informative_clusters_min": min(ks), "informative_clusters_max": max(ks),
            "significant_in_all_passes": all(p <= 0.05 for p in ps),
            "median_p": st.median(ps)}
        print(f"  {L}: " + "  ".join(f"{k}={v['p']:.4f}(Δ{v['delta']:+.4f},k={v['k']})"
                                     for k, v in passes.items()))
        print(f"      p range {min(ps):.4f}–{max(ps):.4f} "
              f"({(max(ps)/min(ps) if min(ps) else float('nan')):.1f}×), "
              f"significant in all {len(ps)} passes: {all(p <= 0.05 for p in ps)}")
    # THE THIRD PATH. `git rev-parse HEAD` raises FileNotFoundError on batch nodes (no git binary),
    # and this call sits between the analysis and the only `open(out, "w")` -- so the run dies before
    # writing and the artifact silently keeps its PREVIOUS contents while sacct says FAILED. That has
    # already fired twice in this repo; `git_commit_safe` was written to end it and was threaded into
    # two of the three scripts that need it. This was the third. Found by audit #13.
    doc["provenance"] = {"argv": sys.argv, "git_commit": git_commit_safe()}
    with open(args.out, "w") as f:
        json.dump(doc, f, indent=2)
    if incomplete:
        print(f"\n  incomplete (excluded): {', '.join(incomplete)}")
    print(f"\n[judge-interval] -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
