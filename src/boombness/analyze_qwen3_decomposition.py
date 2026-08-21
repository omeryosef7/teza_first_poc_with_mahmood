"""analyze_qwen3_decomposition.py -- decompose Qwen3's +0.3476 remove-both effect.

WHY. The committed Qwen3 internal-bank design has three cells and is missing the one that
decomposes the effect:

    remove refusalness @ L20 alone .......... -0.0048  (inert)
    remove BOTH (d_surface L11 + refusal L20) +0.3476  (p 0.00028)
    norm-matched double random .............. +0.0143  (inert)
    remove d_surface @ L11 alone ............ NEVER RUN  <-- this script

PRE-REGISTERED before judging (see the log): if arm B is also ~0, then neither leg moves ASR alone
while the pair moves it +0.35 -- a strong INTERACTION rather than a decomposition, and not what the
final report's phrasing implies.

THE INTERACTION IS TESTED DIRECTLY, not inferred from three marginal p-values. Plan section 8 asks
"does removing both exceed the sum of each alone?", which is a contrast, not a comparison of
significance verdicts:

    interaction = (D - base) - (B - base) - (C - base) = D - B - C + base,  paired per prompt

Positive => super-additive (the legs help each other). Zero => additive. This is the same
difference-of-two-significances trap review #4 flagged and review #9 caught the report committing.

ESTIMAND. Paired per prompt, aggregated over the 6 domain clusters (G-1 = 5 df), identical to
consolidate_deliverables.py, whose helpers this script imports verbatim so the numbers stay
comparable to the committed block.

SESSION MATCHING. --tag-prefix selects ONE judging session for all arms. R6-6 established that
comparing arms judged in different sessions produced a real artifact; the default prefix is the
new single-session batch.

SAFETY: judge scalars only; never opens gens.jsonl.
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import statistics as st
import subprocess

from consolidate_deliverables import (REPO, judge_rows, paired_delta, asr, newest)
from analyze_g8 import cluster_mean_ci

FIELDS = ("malicious_at_0.5", "strongreject_score")


def interaction(base, arm_b, arm_c, arm_d, field: str) -> dict:
    """(D - B - C + base) per prompt, then domain-clustered. Super-additivity of the two legs."""
    pids = sorted(set(base) & set(arm_b) & set(arm_c) & set(arm_d))
    f = (lambda v: (1.0 if v else 0.0)) if field == "malicious_at_0.5" else float
    d = {}
    for p in pids:
        vals = [x[p].get(field) for x in (arm_d, arm_b, arm_c, base)]
        if any(v is None for v in vals):
            continue
        D, Bv, C, S = (f(v) for v in vals)
        d[p] = (D - S) - (Bv - S) - (C - S)
    if not d:
        return {"n": 0, "error": "no shared prompt_id with all four arms"}
    cl = collections.defaultdict(list)
    for p in d:
        cl[str(base[p].get("domain"))].append(d[p])
    r = cluster_mean_ci(dict(cl), n_effective=len(d))
    return {"n": len(d), "interaction_cluster_mean": r.get("mean"), "se": r.get("se"),
            "ci95_domain_clustered": r.get("ci"), "p_cl": r.get("p_vs_0"),
            "n_domains": r.get("n_clusters"),
            "meaning": "(D-base) - (B-base) - (C-base); >0 = removing both exceeds the sum of "
                       "each alone (super-additive), 0 = additive"}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag-prefix", default="q3dec_",
                    help="ONE judging session for every arm (R6-6)")
    ap.add_argument("--arms", default="base,C20,D20,D20ctrl,B11,B11ctrl")
    ap.add_argument("--expect-rows", type=int, default=0,
                    help="per-arm judged row count; 0 disables the check")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    tags = [t for t in a.arms.split(",") if t]
    runs = {t: newest(a.tag_prefix + t) for t in tags}
    rows = {t: judge_rows(runs[t]) for t in tags}

    # GUARD: every arm must carry the same prompt ids, or a "paired" delta is not paired.
    ref = set(rows[tags[0]])
    for t in tags:
        if a.expect_rows and len(rows[t]) != a.expect_rows:
            raise SystemExit(f"[q3dec] {t}: {len(rows[t])} judged rows, expected {a.expect_rows}")
        if set(rows[t]) != ref:
            raise SystemExit(f"[q3dec] {t}: prompt-id set differs from {tags[0]} "
                             f"({len(set(rows[t]) ^ ref)} symmetric-difference ids)")

    by = {}
    for cond in ("natural_doublespeak", "benign_literal"):
        by[cond] = {t: {p: r for p, r in rows[t].items() if r.get("condition") == cond}
                    for t in tags}

    out = {
        "script": "src/boombness/analyze_qwen3_decomposition.py",
        "purpose": "decompose Qwen3's +0.3476 remove-both effect with the never-run d_surface-only "
                   "arm, and test super-additivity directly rather than by comparing p-values",
        "estimand": "paired per prompt vs the same baseline, domain-clustered (G-1 df)",
        "session_matching": f"all arms from judging session {a.tag_prefix!r} (R6-6)",
        "git_commit": subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO,
                                     capture_output=True, text=True).stdout.strip(),
        "runs": {t: os.path.relpath(runs[t], REPO) for t in tags},
        "n_judged_rows": {t: len(rows[t]) for t in tags},
        "conditions": {},
    }
    for cond, pools in by.items():
        blk = {"n_rows": len(pools[tags[0]]), "arms": {}}
        for t in tags:
            if t == "base":
                blk["arms"][t] = {"asr": asr(pools[t])}
                continue
            blk["arms"][t] = {
                "asr": asr(pools[t]),
                **{f: paired_delta(pools["base"], pools[t], f) for f in FIELDS},
            }
        if all(k in pools for k in ("base", "B11", "C20", "D20")):
            blk["INTERACTION_super_additivity"] = {
                f: interaction(pools["base"], pools["B11"], pools["C20"], pools["D20"], f)
                for f in FIELDS}
        out["conditions"][cond] = blk

    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w") as fh:
        json.dump(out, fh, indent=1)
    print(f"[q3dec] wrote {a.out}")
    for cond, blk in out["conditions"].items():
        print(f"  == {cond} (n={blk['n_rows']})")
        for t, v in blk["arms"].items():
            m = v.get("malicious_at_0.5")
            if m:
                print(f"     {t:9s} asr {v['asr']:.4f}  dASR {m['delta_cluster_mean']:+.4f} "
                      f"p {m['p_cl']:.4g}")
            else:
                print(f"     {t:9s} asr {v['asr']:.4f}  (baseline)")
        it = blk.get("INTERACTION_super_additivity", {}).get("malicious_at_0.5")
        if it and it.get("interaction_cluster_mean") is not None:
            print(f"     INTERACTION {it['interaction_cluster_mean']:+.4f}  p {it['p_cl']:.4g}")


if __name__ == "__main__":
    main()
