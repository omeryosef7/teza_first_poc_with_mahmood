"""analyze_subspace_prediction.py -- is the Gate D signal `d_surface`, or the whole concept subspace?

THE DEFECT THIS FIXES IN MY OWN GATE D. Decision Gate D failed requirement 4 ("random / control
directions must fail") on the evidence that `d_naive` and `d_context` predict ASR as well as
`d_surface`. That evidence is weak, because those are not controls:

  * cos(d_surface, d_naive)   = 0.93-0.97 at the layers Gate D selected (L29-L31)
  * cos(d_surface, d_context) = 0.25-0.39
  * and as MEASUREMENTS the per-prompt metric values correlate at Spearman 0.98 / 0.87
    (0.97 / 0.80 within level), i.e. the three "independent directions" are close to one measurement.

Worse, all four fitted directions lie **100.0000% inside the same 3-dimensional subspace** at every
layer -- they are four coordinates of the span of the four 2x2 cell means, not four directions.
Comparing `d_surface` against them asks whether a different coordinate of the same space predicts,
which is not a specificity test.

THE TEST THIS RUNS INSTEAD. A random axis drawn INSIDE that same span and exactly orthogonal to
`d_surface` (`signals.in_subspace_control_direction(..., orthogonalize_against_arm=True)`), over
several independent seeds. If it predicts ASR too, the predictive signal belongs to the subspace and
not to `d_surface`, and requirement 4 fails for a demonstrated reason instead of a confounded one.

NO GPU. The extraction cached the final-occurrence representation per prompt
(`cache/final_occurrence_reps.pt`, [32, hidden] per prompt), and on this bank the final occurrence IS
the query occurrence (`is_query_occurrence == is_final_occurrence` on 7080/7080 rows), which is the
position Gate D's selected metrics use. So any direction can be scored offline.

ESTIMAND. Within-level Spearman against StrongReject, averaged over levels with G-1 df -- the same
within-level estimand Gate D reports, which strips the designed between-level variance that carries
two thirds of the pooled correlation.

CONTROLS ON THE CONTROL: residual norm (`hnorm`) and token position are scored the same way, because
"any scalar predicts" would be the boring explanation and it must be excluded rather than assumed.

SAFETY: reads cached activations and judge scalars; never opens gens.jsonl.
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

import torch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))), "doublespeak_causality"))
from analyze_g8 import cluster_mean_ci  # noqa: E402
from analyze_phase_d import spearman, level_of  # noqa: E402
from common import read_jsonl, REPO_ROOT as REPO  # noqa: E402
import signals as sg  # noqa: E402


def within_level(vals: Dict[str, float], outcome: Dict[str, float],
                 level: Dict[str, str]) -> dict:
    per = collections.defaultdict(lambda: ([], []))
    for p, v in vals.items():
        if p not in outcome:
            continue
        per[level[p]][0].append(v)
        per[level[p]][1].append(outcome[p])
    rhos = {k: spearman(*t) for k, t in per.items()}
    rhos = {k: v for k, v in rhos.items() if v is not None}
    cl = cluster_mean_ci({k: [v] for k, v in rhos.items()}, n_effective=len(rhos))
    return {"mean_rho": cl.get("mean"), "se": cl.get("se"), "p_cl": cl.get("p_vs_0"),
            "n_levels": cl.get("n_clusters"), "per_level": rhos}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--extract", required=True)
    ap.add_argument("--fit", required=True,
                    help="directions_fit_{dev,heldout}.pt -- pass the PREFIX path to either; both "
                         "are loaded and each row is scored CROSS-FIT, with the direction fitted on "
                         "the OTHER split, exactly as the extraction wrote its own columns.")
    ap.add_argument("--judge", action="append", required=True)
    ap.add_argument("--layers", default="29,30,31")
    ap.add_argument("--seeds", default="20260901,20260902,20260903")
    ap.add_argument("--condition", default="natural_doublespeak")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    cache = torch.load(os.path.join(args.extract, "cache", "final_occurrence_reps.pt"),
                       map_location="cpu", weights_only=False)
    reps = cache["reps"]
    # CROSS-FIT, which the first version dropped (review #6, D1). The extraction scores every row
    # with the direction fitted on the OTHER split -- `directions_fitted_on` is "heldout" on all
    # 3000 dev rows and "dev" on all 3000 heldout rows, `is_self_fit` false on 7080/7080. Scoring
    # everything from one payload is a stated-method violation. Its measured impact here is small
    # (only 6 of 900 dev prompts share a family with the dev fit, ~0.33% of rows) but the cross-fit
    # numbers are systematically ~11% higher, and the honest run is the one that matches the extract.
    base_fit = args.fit.replace("_dev.pt", "").replace("_heldout.pt", "")
    fits = {sp: torch.load(f"{base_fit}_{sp}.pt", map_location="cpu", weights_only=False)
            for sp in ("dev", "heldout")}
    fit = fits["dev"]                      # geometry/subspace reporting only; scoring is cross-fit
    other = {"dev": "heldout", "heldout": "dev"}
    ex = [r for r in read_jsonl(os.path.join(args.extract, "results.jsonl"))
          if r.get("condition") == args.condition]
    ju: Dict[str, dict] = {}
    for d in args.judge:
        for r in read_jsonl(os.path.join(d, "results.jsonl")):
            if r.get("judge_status") == "ok" and r.get("condition") == args.condition:
                ju[r["prompt_id"]] = r
    level = {r["prompt_id"]: level_of(r) for r in ex}
    pids = [p for p in sorted({r["prompt_id"] for r in ex})
            if p in ju and reps.get(p) is not None]
    outcome = {p: float(ju[p]["strongreject_score"]) for p in pids}

    split_of = {r["prompt_id"]: str(r.get("split")) for r in ex}

    def score(L: int, dmap, cos: bool) -> Dict[str, float]:
        """`dmap` maps split -> direction; each prompt is scored with the OTHER split's vector."""
        out = {}
        norm = {sp: (v.float() / (v.float().norm() + 1e-8)) for sp, v in dmap.items()}
        for p in pids:
            dn = norm[other[split_of[p]]]
            h = reps[p][L].float()
            out[p] = float(torch.dot(h, dn) / (h.norm() + 1e-8)) if cos else float(torch.dot(h, dn))
        return out

    # How much of each named direction lies inside the centred cell-mean span, per layer. If this
    # is 100% for all of them they are coordinates of one subspace, not independent directions.
    cm = fit["cell_means"]
    span = {}
    for L in [int(x) for x in args.layers.split(",")]:
        rows = [cm[c][L].float().reshape(-1) for c in sorted(cm)]
        M = torch.stack(rows)
        M = M - M.mean(0, keepdim=True)
        U, S, Vh = torch.linalg.svd(M, full_matrices=False)
        k = int((S > S.max() * 1e-3).sum())
        B = Vh[:k]
        span[f"L{L}"] = {"subspace_rank": k, "frac_inside_span": {
            n: float((B @ (fit[n][L].float() / fit[n][L].float().norm())).pow(2).sum())
            for n in ("d_surface", "d_naive", "d_context", "d_inter") if n in fit}}

    out = {
        "script": "src/boombness/analyze_subspace_prediction.py",
        "question": "is Gate D's predictive signal d_surface, or any axis of the concept subspace?",
        "estimand": "within-level Spearman vs strongreject_score, cluster mean over levels (G-1 df)",
        "git_commit": subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO,
                                     capture_output=True, text=True).stdout.strip(),
        "inputs": {"extract": os.path.relpath(args.extract, REPO),
                   "fit": os.path.relpath(args.fit, REPO),
                   "judge": [os.path.relpath(d, REPO) for d in args.judge]},
        "n_prompts": len(pids),
        "subspace_membership": span,
        "results": {},
    }
    for L in [int(x) for x in args.layers.split(",")]:
        entry = {}
        for name in ("d_surface", "d_naive", "d_context", "d_inter"):
            if name in fit:
                entry[name] = {ro: within_level(
                    score(L, {sp: fits[sp][name][L] for sp in fits}, ro == "cos"), outcome, level)
                    for ro in ("cos", "proj")}
        for seed in [int(s) for s in args.seeds.split(",")]:
            dmap, hows, coss = {}, {}, {}
            for sp, pay in fits.items():
                dd, how = sg.in_subspace_control_direction(
                    pay, L, pay["d_surface"][L].float(), seed=seed,
                    orthogonalize_against_arm=True)
                dmap[sp] = dd
                hows[sp] = how
                coss[sp] = float(torch.dot(pay["d_surface"][L].float()
                                           / pay["d_surface"][L].float().norm(),
                                           dd.float() / dd.float().norm()))
            entry[f"in_subspace_orth_seed{seed}"] = {
                "how": hows, "cos_with_d_surface": coss,
                **{ro: within_level(score(L, dmap, ro == "cos"), outcome, level)
                   for ro in ("cos", "proj")}}
        # BORING-EXPLANATION CONTROLS: if a bare scalar predicts, none of the above means anything.
        entry["hnorm"] = {"proj": within_level(
            {p: float(reps[p][L].float().norm()) for p in pids}, outcome, level)}
        out["results"][f"L{L}"] = entry
    tok = {r["prompt_id"]: float(r.get("token_pos") or 0) for r in ex if r.get("is_query_occurrence")}
    out["token_position_control"] = within_level({p: tok[p] for p in pids if p in tok},
                                                 outcome, level)

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w") as fh:
        json.dump(out, fh, indent=2)
    print(f"[subspace] wrote {os.path.relpath(args.out, REPO)}  n={len(pids)}")
    for L, e in out["results"].items():
        print(f"  {L}: " + "  ".join(
            f"{k.replace('in_subspace_orth_seed','ctrl')}={v['cos']['mean_rho']:+.4f}"
            for k, v in e.items() if "cos" in v))
        print(f"        hnorm={e['hnorm']['proj']['mean_rho']:+.4f} "
              f"(p={e['hnorm']['proj']['p_cl']})")
    t = out["token_position_control"]
    print(f"  token_pos={t['mean_rho']:+.4f} (p={t['p_cl']})")


if __name__ == "__main__":
    main()
