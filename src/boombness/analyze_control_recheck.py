"""analyze_control_recheck.py -- re-test the layer profile against a control that can actually fail.

WHY. Review #5 (R5-7) established that every "the matched random control is inert" claim in this
repo used an ISOTROPIC draw in R^4096, which removes ~0.01-0.04% of the structure the arm removes
(at L8: arm 84.0% of the 2x2 cell-mean spread, isotropic control 0.005%). Its inertness is
high-dimensional geometry, not an experimental result -- such a control cannot fail, so it certifies
nothing.

`in_subspace_orth` draws inside the span of the centred cell means and is exactly orthogonal to the
arm direction (|cos| <= 1.7e-08 verified over both splits x 32 layers). It removes 5.4-7.3% of that
spread -- ~1000x the isotropic control, still ~13x less than the arm. It is therefore
SUBSPACE-matched, not magnitude-matched: it answers "does ablating the REST of the concept subspace
do this?", which is the direction-specificity question, and NOT "would any perturbation of
comparable size do this?".

SCOPE, MEASURED (see the log): the fraction of a direction's squared norm inside the cell-mean span
is 100.0000% for d_surface at every layer and 0.65-2.72% for refusalness. So this control is valid
for d_surface arms and INVALID for refusalness arms -- for those it would be ~98% orthogonal anyway
and no better than the isotropic draw. This script therefore refuses any arm whose recorded
intervention direction is not d_surface.

ESTIMAND. Paired per prompt against the SAME baseline, aggregated to domain clusters (G-1 df), the
identical estimand as `analyze_external_arms.py` so the numbers are directly comparable to the
committed layer profile. The arm-minus-control contrast is also paired per prompt, which is tighter
than differencing two independently-clustered means.

SAFETY: judge scalars only; never opens gens.jsonl.
"""
from __future__ import annotations

import argparse
import collections
import glob
import json
import os
import statistics as st
import subprocess
import sys
from typing import Dict, List

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from analyze_g8 import cluster_mean_ci  # noqa: E402
from common import read_jsonl, REPO_ROOT as REPO  # noqa: E402

SCORE = "strongreject_score"
FLAG = "malicious_at_0.5"


def load(dirs: List[str]) -> Dict[str, dict]:
    out, dupes = {}, []
    for d in dirs:
        for r in read_jsonl(os.path.join(d, "results.jsonl")):
            if r.get("judge_status") != "ok":
                continue
            if r["prompt_id"] in out:
                dupes.append(r["prompt_id"])
            out[r["prompt_id"]] = r
    if dupes:
        raise SystemExit(f"[recheck] {len(dupes)} prompt_id in more than one shard of {dirs}")
    return out


def gens_of(judge_dir: str) -> str:
    with open(os.path.join(judge_dir, "config.json")) as fh:
        return json.load(fh)["args"]["gens"]


def intervention_of(judge_dir: str) -> dict:
    """Read the arm's actual intervention from the GENERATION run, not from the tag."""
    g = gens_of(judge_dir)
    p = os.path.join(REPO, g, "summary.json") if not os.path.isabs(g) else os.path.join(g, "summary.json")
    if not os.path.exists(p):
        return {}
    with open(p) as fh:
        return json.load(fh).get("intervention") or {}


def paired(base: Dict[str, dict], arm: Dict[str, dict], field: str) -> dict:
    pids = sorted(set(base) & set(arm))
    d = {}
    for p in pids:
        a, b = arm[p].get(field), base[p].get(field)
        if a is None or b is None:
            continue
        d[p] = ((1.0 if a else 0.0) - (1.0 if b else 0.0)) if field == FLAG else float(a) - float(b)
    cl = collections.defaultdict(list)
    for p in d:
        cl[str(base[p].get("domain"))].append(d[p])
    r = cluster_mean_ci(dict(cl), n_effective=len(d))
    return {"n": len(d), "delta_cluster_mean": r.get("mean"), "se": r.get("se"),
            "ci95_domain_clustered": r.get("ci"), "p_cl": r.get("p_vs_0"),
            "n_domains": r.get("n_clusters"), "delta_pooled": st.mean(d.values()) if d else None}


def paired_diff(base, arm, ctrl, field: str) -> dict:
    """(arm - base) - (ctrl - base), per prompt. Tighter than differencing two cluster means."""
    pids = sorted(set(base) & set(arm) & set(ctrl))
    d = {}
    for p in pids:
        vals = [x[p].get(field) for x in (arm, ctrl, base)]
        if any(v is None for v in vals):
            continue
        f = (lambda v: 1.0 if v else 0.0) if field == FLAG else float
        d[p] = (f(vals[0]) - f(vals[2])) - (f(vals[1]) - f(vals[2]))
    cl = collections.defaultdict(list)
    for p in d:
        cl[str(base[p].get("domain"))].append(d[p])
    r = cluster_mean_ci(dict(cl), n_effective=len(d))
    return {"n": len(d), "delta_cluster_mean": r.get("mean"), "se": r.get("se"),
            "p_cl": r.get("p_vs_0"), "n_domains": r.get("n_clusters")}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--baseline", required=True)
    ap.add_argument("--layer", action="append", default=[], required=True,
                    metavar="L=ARM_DIR[,ARM_DIR2]:ISO_DIR:SUB_DIR[,SUB_DIR2]",
                    help="repeatable, one per depth. Comma-separated dirs are judge SHARDS of one "
                         "run and are unioned; the union is asserted duplicate-free.")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    base = load([args.baseline])
    out = {
        "script": "src/boombness/analyze_control_recheck.py",
        "purpose": "re-test d_surface layer-profile depths against a SUBSPACE-matched control that "
                   "can fail, replacing an isotropic control that cannot (review #5, R5-7)",
        "estimand": "paired per prompt vs the same baseline, domain-clustered (G-1 df); the "
                    "arm-minus-control contrast is paired per prompt",
        "control_scope": "in_subspace_orth is valid ONLY for d_surface arms: measured, d_surface is "
                         "100.0000% inside the centred cell-mean span at every layer while "
                         "refusalness is 0.65-2.72%, so for a refusalness arm this control would be "
                         "~98% orthogonal anyway and no better than the isotropic draw",
        "git_commit": subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO,
                                     capture_output=True, text=True).stdout.strip(),
        "baseline": os.path.relpath(args.baseline, REPO),
        "layers": {},
    }
    for spec in args.layer:
        L, rest = spec.split("=", 1)
        arm_s, iso_s, sub_s = rest.split(":")
        arm = load(arm_s.split(","))
        iso = load(iso_s.split(","))
        sub = load(sub_s.split(","))
        # GUARD: refuse a non-d_surface arm, and refuse a control that is not the right one.
        iv = intervention_of(arm_s.split(",")[0])
        if iv and iv.get("direction") != "d_surface":
            raise SystemExit(f"[recheck] L{L}: arm direction is {iv.get('direction')!r}, not "
                             f"d_surface; in_subspace_orth is not a valid control for it")
        iv_sub = intervention_of(sub_s.split(",")[0])
        if iv_sub and iv_sub.get("direction") != "in_subspace_orth":
            raise SystemExit(f"[recheck] L{L}: subspace control run is {iv_sub.get('direction')!r}")
        entry = {"arm_intervention": iv, "subspace_control_intervention": iv_sub,
                 "n_common": len(set(base) & set(arm) & set(iso) & set(sub)), "vs_baseline": {},
                 "arm_minus_control": {}}
        for field in (SCORE, FLAG):
            entry["vs_baseline"][field] = {
                "arm_d_surface": paired(base, arm, field),
                "control_isotropic": paired(base, iso, field),
                "control_subspace_matched": paired(base, sub, field)}
            entry["arm_minus_control"][field] = {
                "vs_isotropic": paired_diff(base, arm, iso, field),
                "vs_subspace_matched": paired_diff(base, arm, sub, field)}
        out["layers"][f"L{L}"] = entry

    # MULTIPLICITY over the depths tested. The arm-minus-control contrast is the specificity test,
    # and it is run once per depth, so the family is the depth set -- exactly the correction this
    # sprint applied to the layer profile itself (where Holm rejected nothing at m=11). Reporting
    # four individually-significant contrasts without it would be the defect the sprint keeps
    # catching in its own inherited results.
    for field in (SCORE, FLAG):
        ps = {k: e["arm_minus_control"][field]["vs_subspace_matched"].get("p_cl")
              for k, e in out["layers"].items()}
        items = sorted(((k, v) for k, v in ps.items() if v is not None), key=lambda kv: kv[1])
        m, adj, run = len(items), {}, 0.0
        for i, (k, v) in enumerate(items):
            run = max(run, min(1.0, (m - i) * v))
            adj[k] = run
        out.setdefault("multiplicity_arm_minus_subspace_control", {})[field] = {
            "family": "one specificity contrast per depth tested",
            "m": m, "raw": dict(items), "holm_adjusted": adj,
            "holm_rejects_at_0.05": sorted(k for k, v in adj.items() if v <= 0.05)}

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w") as fh:
        json.dump(out, fh, indent=2)
    print(f"[recheck] wrote {os.path.relpath(args.out, REPO)}")
    print(f"  {'layer':>6} {'ARM':>10} {'p':>9} {'ISO ctrl':>10} {'p':>7} {'SUBSPACE ctrl':>14} "
          f"{'p':>7} {'arm-sub':>9} {'p':>8}")
    for k, e in out["layers"].items():
        v = e["vs_baseline"][SCORE]
        a, i, s = v["arm_d_surface"], v["control_isotropic"], v["control_subspace_matched"]
        dm = e["arm_minus_control"][SCORE]["vs_subspace_matched"]
        f = lambda x: "   n/a" if x is None else f"{x:+.4f}"
        g = lambda x: "  n/a " if x is None else f"{x:.4f}"
        print(f"  {k:>6} {f(a['delta_cluster_mean']):>10} {g(a['p_cl']):>9} "
              f"{f(i['delta_cluster_mean']):>10} {g(i['p_cl']):>7} "
              f"{f(s['delta_cluster_mean']):>14} {g(s['p_cl']):>7} "
              f"{f(dm['delta_cluster_mean']):>9} {g(dm['p_cl']):>8}")
    h = out["multiplicity_arm_minus_subspace_control"][SCORE]
    print(f"\n  Holm over the {h['m']} specificity contrasts: "
          f"rejects {h['holm_rejects_at_0.05'] or 'NOTHING'} at 0.05")
    print("  adjusted: " + ", ".join(f"{k} {v:.4f}" for k, v in sorted(h["holm_adjusted"].items(),
                                                                      key=lambda kv: kv[1])))


if __name__ == "__main__":
    main()
