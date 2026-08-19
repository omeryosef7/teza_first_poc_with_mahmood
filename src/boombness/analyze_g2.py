"""analyze_g2.py — does Boombness predict ASR? (plan §9). Committed, reproducible, gate-bearing.

THIS SCRIPT EXISTS BECAUSE THE FIRST G2 TABLE WAS COMPUTED AD HOC AND WAS WRONG.
The tick-16 audit found four defects in it, three of them result-corrupting, and the headline
verdict inverted once they were fixed. Every one traces to a join or a filter that was decided in
a throwaway shell heredoc and never written down:

  (1) THE PREDICTOR WAS READ OFF THE WRONG PROMPT. The join stripped `query_kind` from `family_id`,
      which is a sound key, but it silently pulled the representation from the `semantic_one_word`
      prompt while ASR came from the `behavioral` prompt. Those are different prompts with
      different final queries. The quantity that bears on a GCG objective is `d_surface` on the
      ATTACK prompt. Here the judge is joined to the extract on `prompt_id` DIRECTLY, and the
      script refuses to proceed if the query kinds disagree.

  (2) 72 OF 270 DOUBLESPEAK ROWS WERE SILENTLY DROPPED by that join, and not at random: the
      dropped set was entirely strength=none/consistent/near/plain with ASR 0.224 vs 0.176 and
      refusal 0.000 vs 0.101. Coverage is now reported explicitly and loudly.

  (3) 36 OF THE 198 ROWS HAD n_examples=0 — no demonstrations, therefore no codeword mapping,
      therefore not doublespeak prompts at all. That stratum alone had rho=+0.727 and was carrying
      the correlation. `--min-examples 1` is the default and the n=0 stratum is reported separately.

  (4) THREE OF FIVE COEFFICIENTS DID NOT REPRODUCE. Nothing in the repo could regenerate them.

ESTIMAND PAIRING (audit T5, 2026-08-18). `clustered_inference` used to report a single key `rho` --
the RAW POOLED Spearman -- and, three keys later, `p_within_domain_perm`. Those are two different
quantities: the permutation demeans x and y WITHIN DOMAIN first, so its p tests the within-domain
association and says nothing about the pooled one. Nothing in the key names said so, and every
consumer of this artifact read the p as the p of the rho beside it. The file even quantified its own
mismatch and no one noticed: `qwen3_g2_analysis.json` carries rho=+0.3638 next to
`within_domain_slope`=+0.1381 (2.6x smaller) with the cited p=0.0050 attached to the +0.364 headline,
and `g2_analysis_lastpos.json` carries a "significant" cited p=0.0235 for a quantity the file never
reports as an estimate while its reported rho=+0.086 is n.s. Both point estimates are now emitted
under unambiguous names -- `rho_pooled` and `rho_within_domain` -- every p key names its own estimand
(`p_iid_pooled_rho`, `p_cr1_pooled_slope`, `p_perm_within_domain_rho`), and `p_estimand` names the
quantity the citable p tests. Names match analyze_g64.py exactly so the three scripts agree. NEITHER
ESTIMATE WAS PROMOTED OR DEMOTED; only the pairing became legible.

LAYER SELECTION (audit T6, 2026-08-18). `--headline-predictor` names ONE column out of the family
this script scans in full -- 28 columns on the default `--layers` (10 layers x {cos, proj} of
`d_surface`, plus `logit_lens` wherever the extract wrote it). The headline's rho and its "cite this
one" permutation p were reported as if the column had been prespecified, and the family size was
recorded nowhere, which is the hole C-4 opened in `reanalyze_corrected` one file over (there, once
the family was written down, the corrected answer CHANGED). `report["layer_selection"]` now records
the family and its size `m`, and gives every member four inferential numbers: the marginal
within-domain permutation p (valid only for a prespecified column); `p_perm_maxT_family`, the same
permutation with the maximum taken over all `m` columns on SHARED draws (single-step
Westfall-Young, the correlation-aware analogue of Bonferroni); `p_perm_maxT_stepdown_family`, its
free step-down refinement, WHICH IS THE ONE TO CITE FOR A CHOSEN COLUMN; and Holm over the marginal
p-values with `m` recorded. `report["holm_family"]` does the same for the i.i.d. pooled table, via
the house `reanalyze_corrected.holm_table`.

WHAT IT DID TO THE PUBLISHED NUMBERS. Nothing moved on the headline itself -- rho_pooled +0.30667
and rho_within_domain +0.26178 are bit-identical to the pre-fix code on all three artifacts -- but
the citable p for `d_surface|L12|proj` at `codeword_last` goes 5.0e-04 -> 1.5e-03 once the m=28
scan is paid for, and it still clears Holm at m=28. The `lastpos` artifact does NOT survive: its
0.0235 becomes 0.191 step-down and Holm rejects nothing, which is exactly the "significant p for a
quantity never reported as an estimate" the critique flagged in that file.

Alongside the correction, the COST of selecting is measured rather than assumed (the C-8 precedent:
for `probes`, nested selection moved AUROC by 0.0012-0.0018 and changed nothing -- but that was
measured). `nested_selection` re-picks the argmax on all clusters but one and scores it on the
held-out cluster; `fixed_headline_heldout` repeats that without re-picking, so the gap between them
separates the price of choosing from ordinary out-of-sample shrinkage.

Outputs a JSON report and prints the table, so the numbers in the log are traceable to a command.
"""
from __future__ import annotations

import argparse
import collections
import re
import json
import math
import os
import sys
from typing import Dict, List, Optional, Sequence

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import read_jsonl, require_done  # noqa: E402


def spearman(x, y):
    from scipy.stats import spearmanr
    r = spearmanr(x, y)
    return float(r.statistic), float(r.pvalue)


def rank_partial(x, y, z):
    """Spearman(x, y | z): Pearson correlation of the residuals of the RANKS.

    Added because the tick-24 audit showed the headline predictor was ~55% shared with the
    residual-stream norm at the same position: Spearman(d_surface|L8|proj, hnorm|L8) = -0.731 and
    Spearman(hnorm|L8, ASR) = -0.315, so partialling the norm out dropped the reported rho from
    +0.342 to +0.151. A quantity a GCG objective would push (position ON the axis) is not the
    same as how large the activation is, and the two must be separated before either is claimed.
    """
    import numpy as np
    from scipy.stats import rankdata, pearsonr
    rx, ry, rz = (rankdata(np.asarray(v, dtype=float)) for v in (x, y, z))
    def resid(a, b):
        b1 = np.column_stack([np.ones_like(b), b])
        beta, *_ = np.linalg.lstsq(b1, a, rcond=None)
        return a - b1 @ beta
    ex, ey = resid(rx, rz), resid(ry, rz)
    r, p = pearsonr(ex, ey)
    return float(r), float(p)


def rank_corr_pair(x, y, clusters) -> Dict[str, float]:
    """BOTH point estimates the clustered block reports, computed side by side (audit T5).

    `rho_pooled` is the ordinary Spearman. `rho_within_domain` is the same rank correlation after
    each cluster's mean is removed from BOTH variables -- and that, not `rho_pooled`, is the
    quantity the within-domain permutation p tests. The two can differ in magnitude (2.6x on the
    qwen3 artifact) and, on data with a Simpson structure, in SIGN. They lived one key apart with no
    label until 2026-08-18, so every reader paired the within-domain p with the pooled rho.

    This is a module-level function precisely so the pairing is testable: while it was eight inline
    lines inside `main`, no test could reach it, and the defect survived four audits.

    The pipeline is identical to the permutation's own (ranks -> standardise -> demean by cluster),
    so the estimate and its p-value cannot drift apart.
    """
    import numpy as _np
    X = std_ranks(x)
    Y = std_ranks(y)
    rho_pooled = float(_np.dot(X, Y) / len(X))
    Xw, Yw = demean_by_cluster(X, clusters), demean_by_cluster(Y, clusters)
    dxx, dyy = float(_np.dot(Xw, Xw)), float(_np.dot(Yw, Yw))
    rho_w = (float(_np.dot(Xw, Yw)) / math.sqrt(dxx * dyy)) if dxx > 0 and dyy > 0 else float("nan")
    return {"rho_pooled": rho_pooled, "rho_within_domain": rho_w,
            "p_estimand_of_within_domain_permutation": "rho_within_domain"}


# --------------------------------------------------------------------------------------------- #
# LAYER-FAMILY SELECTION (audit T6, 2026-08-18)
#
# `--headline-predictor` names ONE column out of a family this script scans in full: with the
# default `--layers`, 10 layers x {cos, proj} of `d_surface` plus `logit_lens` wherever it exists
# = 28 columns, all correlated with each other. The headline's rho and its "cite this one"
# within-domain permutation p were reported as though the column had been prespecified, and the
# family size was recorded NOWHERE -- the exact hole C-4 opened for `reanalyze_corrected`'s Holm
# family, one file over.
#
# Two corrections are computed here, and both are reported rather than one being chosen:
#
#   * `p_perm_maxT_family` / `p_perm_maxT_stepdown_family` -- max-statistic (Westfall-Young)
#     permutation p-values, single-step and free step-down. Each of the SAME within-cluster draws
#     that produces the marginal p also yields max_j |rho_j|, so the adjusted p for column j is
#     P(max |rho^perm| >= |rho_j^obs|), over the whole family (single-step) or over the columns no
#     larger than j in the observed ordering (step-down). Because the draws are shared across
#     columns they use the family's real correlation structure rather than assuming independence,
#     which for 28 near-collinear layer columns is far less conservative than Bonferroni. This is
#     the honest "would the BEST column have looked this good by chance?" answer, it controls FWER
#     over the family, and the step-down version is the one to cite for a chosen column.
#   * Holm over the same marginal permutation p-values, with the family size `m` recorded. Holm is
#     step-down but correlation-blind while single-step maxT is correlation-aware but not
#     step-down, so NEITHER DOMINATES THE OTHER and they can disagree (they do on the Qwen3
#     artifact). Both control FWER; both are reported rather than one being chosen.
#
# The permutation permutes y WITHIN CLUSTER on the group-demeaned ranks -- the identical footing as
# `p_perm_within_domain_rho` in `clustered_inference`, so the marginal p of the headline column
# here and the headline p there are the same estimand (they differ only by the draw seed).
# --------------------------------------------------------------------------------------------- #
def std_ranks(v):
    """ranks -> standardise. Shared by `rank_corr_pair` and the family permutation so the point
    estimate and the p-value cannot be computed on two different pipelines (audit T5's shape)."""
    import numpy as _np
    from scipy import stats as _st
    X = _st.rankdata(_np.asarray(v, dtype=float))
    return (X - X.mean()) / (X.std(ddof=0) or 1.0)


def demean_by_cluster(arr, clusters):
    """Subtract each cluster's mean. Returns a new array; `arr` is not modified."""
    import numpy as _np
    out = _np.array(arr, dtype=float, copy=True)
    for g in sorted(set(clusters), key=repr):
        gi = [i for i in range(len(out)) if clusters[i] == g]
        out[gi] = out[gi] - out[gi].mean()
    return out


def family_within_domain_perm(cols: Dict[str, Sequence[float]], y, clusters,
                              n_perm: int = 2000, seed: int = 20260819) -> Dict[str, object]:
    """Joint within-cluster permutation over an ENTIRE predictor family (audit T6).

    `cols` maps predictor name -> that predictor's values, every column read on the SAME rows in
    the SAME order as `y` and `clusters`. One set of `n_perm` draws is shared by all columns, which
    is what makes the max-statistic adjustment valid under the family's own correlation structure.

    Returns per column: `rho_pooled`, `rho_within_domain`, the marginal within-domain permutation p
    (`p_perm_within_domain_rho`, the same estimand `clustered_inference` cites), and
    `p_perm_maxT_family` -- the selection-adjusted p. Plus the family metadata (`m`, `n_perm`,
    `seed`, the argmax column) that C-4 established must be recorded rather than inferred.
    """
    import numpy as _np
    names = list(cols)
    if not names:
        return {"m": 0, "n": 0, "per_predictor": {}}
    n = len(y)
    for nm in names:
        if len(cols[nm]) != n:
            raise ValueError(f"family column {nm!r} has {len(cols[nm])} rows, y has {n} — every "
                             "family column must be read on the same rows in the same order")
    Xs = _np.column_stack([std_ranks(cols[nm]) for nm in names])
    Ys = std_ranks(y)
    Xw = _np.column_stack([demean_by_cluster(Xs[:, j], clusters) for j in range(len(names))])
    Yw = demean_by_cluster(Ys, clusters)
    rho_pooled = (Xs.T @ Ys) / n
    ssx = (Xw * Xw).sum(axis=0)
    ssy = float(Yw @ Yw)
    # NO SILENT NaN COLUMNS. A predictor with no within-cluster variation left (constant, or
    # constant inside every cluster) has an undefined within-domain correlation. Dropping it
    # quietly would shrink the family without saying so -- and the family size is the whole point
    # of this block -- while carrying it as NaN would poison the max statistic.
    dead = [names[j] for j in range(len(names)) if not (ssx[j] > 0)]
    if dead or not (ssy > 0):
        raise ValueError(
            "no within-cluster variation left for %s -- an undefined within-domain correlation "
            "cannot be a member of a max-statistic family" % (dead or ["the target y"],))
    denom = _np.sqrt(ssx * ssy)
    obs = (Xw.T @ Yw) / denom
    aobs = _np.abs(obs)

    rng = _np.random.default_rng(seed)
    by_g: Dict[object, List[int]] = collections.OrderedDict()
    for i, g in enumerate(clusters):
        by_g.setdefault(g, []).append(i)
    groups = [_np.asarray(v, dtype=int) for v in by_g.values()]
    R = _np.empty((n_perm, len(names)), dtype=float)
    for b in range(n_perm):
        Yp = Yw.copy()
        for gi in groups:
            Yp[gi] = Yw[rng.permutation(gi)]
        R[b] = _np.abs((Xw.T @ Yp) / denom)

    # (1) MARGINAL: the p a prespecified column would get. Same estimand and same footing as
    #     `clustered_inference.p_perm_within_domain_rho`, differing only in the draw seed.
    p_marg = ((R >= aobs).sum(axis=0) + 1) / (n_perm + 1)
    # (2) SINGLE-STEP maxT (Westfall-Young): P(max over the whole family >= this column's |rho|).
    #     The correlation-aware analogue of Bonferroni.
    p_max = ((R.max(axis=1)[:, None] >= aobs).sum(axis=0) + 1) / (n_perm + 1)
    # (3) FREE STEP-DOWN maxT: the same draws, but each column is compared against the max over
    #     only the columns no LARGER than it in the observed ordering, then the adjusted p-values
    #     are made monotone. Uniformly at least as powerful as (2) and, unlike Holm, it knows the
    #     family is near-collinear. This is the one to cite for a chosen column.
    order = _np.argsort(-aobs, kind="stable")
    Rord, tord = R[:, order], aobs[order]
    Q = _np.maximum.accumulate(Rord[:, ::-1], axis=1)[:, ::-1]
    p_sd = ((Q >= tord).sum(axis=0) + 1) / (n_perm + 1)
    p_sd = _np.maximum.accumulate(p_sd)
    p_step = _np.empty_like(p_sd)
    p_step[order] = p_sd

    import reanalyze_corrected as _rc          # house Holm, which records the family size m
    holm_tab = _rc.holm_table({nm: float(p_marg[j]) for j, nm in enumerate(names)},
                              m=len(names))
    per = {}
    for j, nm in enumerate(names):
        per[nm] = {"rho_pooled": float(rho_pooled[j]),
                   "rho_within_domain": float(obs[j]),
                   "p_perm_within_domain_rho": float(p_marg[j]),
                   "p_perm_maxT_family": float(p_max[j]),
                   "p_perm_maxT_stepdown_family": float(p_step[j]),
                   "holm_rejected_within_domain": bool(holm_tab[nm]["rejected"]),
                   "holm_thr": float(holm_tab[nm]["thr"]),
                   "holm_rank": int(holm_tab[nm]["rank"])}
    jbest = int(_np.argmax(aobs))
    return {"m": len(names), "n": n, "n_clusters": len(groups), "n_perm": n_perm, "seed": seed,
            "family": names, "per_predictor": per,
            "argmax_predictor": names[jbest],
            "argmax_rho_within_domain": float(obs[jbest]),
            "p_floor": 1.0 / (n_perm + 1)}


def heldout_layer_selection(cols: Dict[str, Sequence[float]], y, clusters
                            ) -> Dict[str, object]:
    """Leave-one-CLUSTER-out nested selection: what does the selected column buy out of sample?

    The critique (T6) asks for a corrected p and/or a held-out selection. C-8 set the precedent for
    the second half: for `probes`, nested selection was found to move AUROC by 0.0012-0.0018 and to
    change no conclusion -- MEASURED, not assumed. This is the same measurement for G2's layer
    scan. For each cluster g the argmax |rho_within| is chosen on the OTHER clusters only and then
    evaluated on g (where "within-domain" and "pooled" coincide, g being a single cluster). The
    n-weighted mean of those held-out rhos is compared with the in-sample argmax, and the gap is
    the selection cost.

    `selection_is_stable` is the same diagnostic C-8 used: if the folds do not agree on a column,
    the argmax was noise.
    """
    import numpy as _np
    names = list(cols)
    n = len(y)
    groups = sorted(set(clusters), key=repr)
    if len(groups) < 2 or not names:
        return {"available": False,
                "reason": f"need >=2 clusters and >=1 column; got {len(groups)} and {len(names)}"}
    folds = []
    for g in groups:
        tr = [i for i in range(n) if clusters[i] != g]
        te = [i for i in range(n) if clusters[i] == g]
        if len(te) < 4 or len(tr) < 4:
            folds.append({"cluster": str(g), "n_test": len(te), "skipped": True,
                          "reason": "fewer than 4 rows on one side"})
            continue
        tr_cl = [clusters[i] for i in tr]
        best, best_abs = None, -1.0
        for nm in names:
            rw = rank_corr_pair([cols[nm][i] for i in tr], [y[i] for i in tr],
                                tr_cl)["rho_within_domain"]
            if rw == rw and abs(rw) > best_abs:
                best, best_abs = nm, abs(rw)
        # NO SILENT NaN FOLD (verifier, 2026-08-19). Two ways this fold can fail to produce a
        # number, both of which the first version of this function carried straight into the
        # weighted mean: (a) EVERY column has an undefined within-cluster rho on the selection
        # folds, so there is no argmax to carry over -- the old code then did `cols[None]` and
        # died with a bare KeyError; (b) the HELD-OUT cluster has no variation in y (a domain
        # where every prompt scored the same is entirely plausible here) or in x, so the held-out
        # Spearman is NaN. In case (b) the old code appended `heldout_rho: nan`, the fold counted
        # as used, and every downstream number -- the weighted mean, `selection_cost_abs_rho` --
        # came out NaN while `available: True` and `selection_is_stable: True` were still
        # reported. `family_within_domain_perm` refuses exactly this condition for the family;
        # refusing it there and averaging it here is the one-of-two-paths class (R-12).
        if best is None:
            folds.append({"cluster": str(g), "n_test": len(te), "skipped": True,
                          "reason": "no column had a defined within-cluster rho on the "
                                    "selection folds, so there was no argmax to hold out"})
            continue
        r_sel, _ = spearman([cols[best][i] for i in te], [y[i] for i in te])
        if r_sel != r_sel:
            folds.append({"cluster": str(g), "n_test": len(te), "skipped": True,
                          "selected_on_other_clusters": best,
                          "reason": "held-out rho is undefined (no variation in y or in the "
                                    "selected column inside the held-out cluster)"})
            continue
        folds.append({"cluster": str(g), "n_test": len(te), "skipped": False,
                      "selected_on_other_clusters": best,
                      "selected_rho_in_selection_folds": float(best_abs),
                      "heldout_rho": float(r_sel)})
    used = [f for f in folds if not f.get("skipped")]
    n_undef = sum(1 for f in folds if f.get("skipped") and "undefined" in f.get("reason", ""))
    if not used:
        return {"available": False, "reason": "every fold was skipped", "folds": folds,
                "n_folds_skipped": len(folds), "n_folds_undefined": n_undef}
    wsum = sum(f["n_test"] for f in used)
    heldout = sum(f["heldout_rho"] * f["n_test"] for f in used) / wsum
    in_sample = max((abs(rank_corr_pair(cols[nm], y, clusters)["rho_within_domain"])
                     for nm in names), default=float("nan"))
    picks = sorted({f["selected_on_other_clusters"] for f in used})
    return {"available": True, "n_folds": len(used), "folds": folds,
            "n_folds_skipped": len(folds) - len(used), "n_folds_undefined": n_undef,
            "in_sample_argmax_abs_rho_within_domain": float(in_sample),
            "heldout_selected_rho_weighted_mean": float(heldout),
            "selection_cost_abs_rho": float(in_sample - abs(heldout)),
            "distinct_columns_selected": picks,
            # stability is a statement about the folds that ACTUALLY produced a held-out number.
            "selection_is_stable": len(picks) == 1 and len(used) == len(folds)}


def heldout_fixed_column(col: Sequence[float], y, clusters) -> Dict[str, object]:
    """The same leave-one-cluster-out evaluation for a column that is FIXED across folds.

    The contrast that isolates selection: `heldout_layer_selection` re-chooses per fold, this does
    not, so the difference between the two held-out means is the part of the gap attributable to
    choosing the column rather than to out-of-sample shrinkage generally.

    SAME AVAILABILITY CONTRACT AS `heldout_layer_selection` (verifier, 2026-08-19). The first
    version of this function had no minimum-cluster guard while its sibling did, so on the
    supported `--cluster-by ''` path -- one pseudo-cluster, nothing held out -- it evaluated the
    column on ALL the rows and published the result as `heldout_rho_weighted_mean`. On the real
    G2 inputs that field came out at +0.30666778020417, digit for digit the IN-SAMPLE
    `rho_within_domain` printed six lines above it, under a note promising a held-out number.
    A guard applied to one of two sibling paths and dropped on the other is the class that caused
    R-12; both paths now answer `available` and neither reports a mean it did not hold out.
    """
    n = len(y)
    groups = sorted(set(clusters), key=repr)
    if len(groups) < 2:
        return {"available": False,
                "reason": f"need >=2 clusters to hold one out; got {len(groups)}. With clustering "
                          f"disabled every row is in one pseudo-cluster, so evaluating on 'the "
                          f"held-out cluster' would be evaluating in sample.",
                "folds": [], "heldout_rho_weighted_mean": None}
    per, wsum, acc = [], 0, 0.0
    for g in groups:
        te = [i for i in range(n) if clusters[i] == g]
        if len(te) < 4:
            per.append({"cluster": str(g), "n_test": len(te), "skipped": True,
                        "reason": "fewer than 4 rows in the held-out cluster"})
            continue
        r, _ = spearman([col[i] for i in te], [y[i] for i in te])
        if r != r:
            per.append({"cluster": str(g), "n_test": len(te), "skipped": True,
                        "reason": "held-out rho is undefined (no variation in y or in the column "
                                  "inside the held-out cluster)"})
            continue
        per.append({"cluster": str(g), "n_test": len(te), "skipped": False, "heldout_rho": float(r)})
        acc += float(r) * len(te)
        wsum += len(te)
    used = [f for f in per if not f.get("skipped")]
    n_undef = sum(1 for f in per if f.get("skipped") and "undefined" in f.get("reason", ""))
    if not wsum:
        return {"available": False, "reason": "every fold was skipped", "folds": per,
                "n_folds": 0, "n_folds_skipped": len(per), "n_folds_undefined": n_undef,
                "heldout_rho_weighted_mean": None}
    return {"available": True, "folds": per, "n_folds": len(used),
            "n_folds_skipped": len(per) - len(used), "n_folds_undefined": n_undef,
            "heldout_rho_weighted_mean": acc / wsum}


def holm(pvals: Dict[str, float], alpha: float = 0.05, m: Optional[int] = None) -> Dict[str, bool]:
    """Delegates to the house Holm (`reanalyze_corrected.holm_table`), which records the family
    size `m` alongside each decision.

    This used to be a private re-implementation. It gave the same decisions, but it could not be
    told what the family WAS -- exactly the gap C-4 found one file over, where writing the family
    size down changed which layers were rejected. Two implementations of one correction is how they
    drift apart, so there is now one.
    """
    import reanalyze_corrected as _rc
    return {k: bool(v["rejected"]) for k, v in _rc.holm_table(pvals, alpha, m).items()}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--judge", required=True)
    ap.add_argument("--extract", required=True)
    ap.add_argument("--score", required=True, help="score_behavior run (for semantic log-odds)")
    ap.add_argument("--arm", default="natural_doublespeak")
    ap.add_argument("--cluster-by", default="domain",
                    help="cluster variable for CR1 + within-cluster permutation inference "
                         "(audit B1b); empty string disables")
    ap.add_argument("--headline-predictor", default="d_surface|L12|proj",
                    help="the predictor the write-up quotes; clustered inference is run on it")
    ap.add_argument("--extract-position", default="codeword_last",
                    help="token position the EXTRACT run read at; refusalness must match it "
                         "(audit D3 / RETRACTION #5)")
    ap.add_argument("--min-examples", type=int, default=1,
                    help="drop n_examples<this; 0-demo prompts establish no mapping and are not "
                         "doublespeak prompts (audit finding 3)")
    ap.add_argument("--layers", default="4,8,11,12,16,18,20,24,28,31")
    ap.add_argument("--refusalness", default=None,
                    help="refusalness run dir; enables the §9 Q6/Q7 mediation analysis that "
                         "decides the §18 outcome label (A: Boombness is the story; C: refusal "
                         "suppression is the story and Boombness is a correlate)")
    ap.add_argument("--family-n-perm", type=int, default=2000,
                    help="permutation draws for the layer-family selection test (audit T6). The "
                         "adjusted-p floor is 1/(n+1), so this must exceed m/alpha for any "
                         "family member to be rejectable at all: 2000 supports m up to 100 at "
                         "alpha=0.05.")
    ap.add_argument("--family-seed", type=int, default=20260819,
                    help="seed for the family permutation. Deliberately NOT the clustered block's "
                         "20260817, so the two p-values are visibly independent draws of the same "
                         "estimand rather than one number reported twice (R-12's shape).")
    ap.add_argument("--require-bank-block", default="",
                    help="comma list of bank_block values to keep (R-18). Default: no filter, which "
                         "is how the published n=234 came to include experimentally-manipulated rows.")
    ap.add_argument("--slot0-only", action="store_true",
                    help="drop sibling families (family_slot != 0). They reuse demonstrations from "
                         "their slot-0 sibling and are not independent prompts (R-18).")
    ap.add_argument("--out", default=None)
    ap.add_argument("--allow-partial", action="store_true",
                    help="analyse a run with no DONE.json (output must not be reported)")

    args = ap.parse_args()
    if args.judge:
        require_done(args.judge, allow_partial=args.allow_partial)
    if args.extract:
        require_done(args.extract, allow_partial=args.allow_partial)
    if args.score:
        require_done(args.score, allow_partial=args.allow_partial)
    if args.refusalness:
        require_done(args.refusalness, allow_partial=args.allow_partial)

    J = read_jsonl(os.path.join(args.judge, "results.jsonl"))
    E = read_jsonl(os.path.join(args.extract, "results.jsonl"))
    S = read_jsonl(os.path.join(args.score, "results.jsonl"))
    layers = [int(x) for x in args.layers.split(",")]

    # ---- ASR, keyed by prompt_id (the attack prompt) --------------------------------- #
    asr = {r["prompt_id"]: r["strongreject_score"] for r in J
           if r.get("strongreject_score") is not None and r.get("condition") == args.arm}
    n_arm_total = len(asr)

    # ---- representation on the SAME prompt: join on prompt_id, assert query kind ----- #
    rep: Dict[str, Dict[int, float]] = {}
    qk_seen = collections.Counter()
    for r in E:
        if not r.get("is_final_occurrence") or r["prompt_id"] not in asr:
            continue
        qk_seen[r.get("query_kind")] += 1
        d = rep.setdefault(r["prompt_id"], {})
        for L in layers:
            for stat in ("cos", "proj"):
                c = f"d_surface|L{L}|{stat}"
                if c in r:
                    d[(L, stat)] = r[c]
        for L in layers:
            c = f"ll|L{L}|boombness"
            if c in r:
                d[(L, "ll")] = r[c]
        # The residual-stream NORM at the same position. `d_surface|L|proj` is an unnormalised
        # inner product, so it scales with ||h||, and ||h|| is itself an ASR predictor. Without
        # this control a "Boombness" association can be mostly "how big the activation is".
        for L in layers:
            c = f"hnorm|L{L}"
            if c in r:
                d[(L, "hnorm")] = r[c]
    if set(qk_seen) - {"behavioral"}:
        raise SystemExit(
            f"representation rows came from query kinds {dict(qk_seen)} — the predictor must be "
            "read off the SAME prompt that was generated from and judged (audit finding 1)")

    # ---- semantic log-odds: only available on the semantic probe prompt -------------- #
    # Kept, but explicitly labelled as a DIFFERENT prompt, joined on the stripped family key.
    def fam_key(fid): return "|".join(fid.split("|")[:-1])
    sem_by_fam = {fam_key(r["family_id"]): r["semantic_logodds"] for r in S
                  if r.get("readout") == "semantic" and r.get("condition") == args.arm
                  and r.get("semantic_logodds") is not None}
    meta = {r["prompt_id"]: r for r in J if r["prompt_id"] in asr}

    keys = [p for p in asr if p in rep]
    n_examples = {p: meta[p].get("n_examples") for p in keys}
    kept = [p for p in keys if (n_examples[p] or 0) >= args.min_examples]
    zero = [p for p in keys if (n_examples[p] or 0) == 0]

    # ---- R-18: ROW PROVENANCE. This filter is on `condition` and NOTHING ELSE, which is how the
    # headline n=234 came to contain 72 sibling-slot families (which SHARE demonstrations with their
    # slot-0 siblings -- pseudo-replication) and 72 rows from the `strength`/`consistency`/`position`
    # blocks, which exist to EXPERIMENTALLY MANIPULATE how readable the codeword is. A manipulation
    # that moves both Boombness and ASR manufactures correlation in an otherwise observational
    # statistic. Measured: rho falls +0.3067 (n=234) -> +0.0860 (n=90) once both are removed, at the
    # 0.4th percentile of random 90-row subsets.
    #
    # The composition is now ALWAYS recorded, whether or not it is filtered, so that this can never
    # again be invisible to a reader of the artifact. That is the actual fix; the flags are a
    # convenience.
    def _slot_of(row):
        """family_slot, from the row if present, else parsed from `family_id`.

        The judge rows do NOT carry `family_slot`, so the first version of this check reported
        `{None: 234}` and its sibling-row count as 0 -- a guard that cannot fire, which is the
        defect this file is trying to expose. `family_id` is built as
        `{domain}|{split}|slot{N}|n{n}|...` (prompt_families.py:341), so the slot is recoverable.
        Returns None ONLY when neither source is available, and that count is reported.
        """
        v = row.get("family_slot")
        if v is not None:
            return v
        fid = row.get("family_id") or ""
        m = re.search(r"\|slot(\d+)\|", fid)
        return int(m.group(1)) if m else None

    blocks = {p: (meta[p].get("bank_block"), _slot_of(meta[p])) for p in kept}
    unknown_prov = sum(1 for p in kept if blocks[p][0] is None)
    unknown_slot = sum(1 for p in kept if blocks[p][1] is None)
    composition = {
        "by_bank_block": dict(collections.Counter(b for b, _ in blocks.values())),
        "by_family_slot": dict(collections.Counter(sl for _, sl in blocks.values())),
        "n_rows_with_no_bank_block_recorded": unknown_prov,
        "n_rows_with_no_family_slot_recoverable": unknown_slot,
        "note": ("R-18. The row set is filtered on `condition` only unless --require-bank-block / "
                 "--slot0-only are passed. Sibling slots (family_slot != 0) reuse demonstrations "
                 "from their slot-0 sibling and are NOT independent prompts; the strength / "
                 "consistency / position blocks are experimental manipulations of codeword "
                 "readability and do not belong in an observational correlation."),
    }
    if args.require_bank_block:
        want = {x.strip() for x in args.require_bank_block.split(",") if x.strip()}
        before = len(kept)
        kept = [p for p in kept if blocks[p][0] in want]
        print(f"[G2] --require-bank-block {sorted(want)}: {before} -> {len(kept)} rows")
        composition["require_bank_block"] = sorted(want)
    if args.slot0_only:
        before = len(kept)
        kept = [p for p in kept if blocks[p][1] in (0, None)]
        print(f"[G2] --slot0-only: {before} -> {len(kept)} rows (sibling families dropped)")
        composition["slot0_only"] = True
    # Recompute AFTER filtering. The first version printed the PRE-filter composition next to a
    # post-filter n, which is precisely the kind of mismatched label this whole check exists to
    # prevent -- it showed `families: 72` on a run that had just dropped all 72 of them.
    composition["n_analysed_after_filters"] = len(kept)
    composition["by_bank_block_BEFORE_filters"] = composition.pop("by_bank_block")
    composition["by_family_slot_BEFORE_filters"] = composition.pop("by_family_slot")
    composition["by_bank_block"] = dict(collections.Counter(blocks[p][0] for p in kept))
    composition["by_family_slot"] = dict(collections.Counter(blocks[p][1] for p in kept))
    print(f"[G2] ROW COMPOSITION of the ANALYSED set (n={len(kept)}): "
          f"{composition['by_bank_block']} | family_slot {composition['by_family_slot']}")
    if not args.require_bank_block and not args.slot0_only:
        sib = sum(v for k, v in composition["by_family_slot"].items() if k not in (0, None))
        manip = sum(v for k, v in composition["by_bank_block"].items()
                    if k in ("strength", "consistency", "position"))
        if sib or manip:
            print(f"[G2] ⚠ R-18 WARNING: {sib} sibling-slot row(s) and {manip} "
                  f"designed-variance row(s) are INCLUDED. rho over this set mixes "
                  f"pseudo-replicated and experimentally-manipulated prompts with the core design. "
                  f"Re-run with --slot0-only --require-bank-block core2x2,extra_conditions,families "
                  f"minus the manipulated blocks to see the clean estimate.")

    print(f"[G2] arm={args.arm}: {n_arm_total} judged prompts; {len(keys)} with a representation "
          f"({100*len(keys)/max(n_arm_total,1):.0f}% coverage); "
          f"{len(kept)} after --min-examples {args.min_examples}; {len(zero)} zero-demo dropped")
    if len(keys) < n_arm_total:
        print(f"[G2] WARNING: {n_arm_total - len(keys)} judged prompts have no representation row")

    y = [asr[p] for p in kept]
    # PROVENANCE (2026-08-18). The artifact recorded judge/extract/score but NOT argv, and NOT the
    # --refusalness directory, even though the mediation block that decides the §18 outcome label
    # runs off it: `g2_analysis_cwpos.json` shipped a full `mediation` section with no record of
    # which refusalness run produced it, so this re-run had to recover the path from the G9
    # artifacts (the position guard then confirmed the match). analyze_g64.py had the same argv gap
    # and it was closed there in this audit; a script that does not record its inputs cannot satisfy
    # the standing "every published number is regenerable" rule.
    import subprocess as _sp

    def _git(*a):
        try:
            return _sp.check_output(["git", *a], stderr=_sp.DEVNULL).decode().strip()
        except Exception:
            return None

    inputs = {"judge": os.path.abspath(args.judge), "extract": os.path.abspath(args.extract),
              "score": os.path.abspath(args.score),
              "refusalness": (os.path.abspath(args.refusalness) if args.refusalness else None)}
    report: Dict[str, object] = {
        "provenance": {"argv": sys.argv, "git_commit": _git("rev-parse", "HEAD"),
                       "git_dirty": bool(_git("status", "--porcelain")),
                       "python": sys.executable,
                       # EVERY input path in ONE place (C-10 follow-through). `refusalness` was the
                       # hole the audit named, but judge/extract/score sat outside `provenance`
                       # entirely, so "does this artifact record its inputs?" had two answers
                       # depending on where you looked. Mirrors analyze_g64.py's `provenance.inputs`
                       # so the two artifacts are read the same way. The three top-level keys are
                       # kept for the consumers that already read them.
                       "inputs": dict(inputs),
                       "refusalness": inputs["refusalness"]},
        "row_composition": composition,
        "arm": args.arm, "judge": inputs["judge"],
        "extract": inputs["extract"], "score": inputs["score"],
        "n_judged_in_arm": n_arm_total, "n_with_representation": len(keys),
        "n_analysed": len(kept), "n_zero_demo_excluded": len(zero),
        "min_examples": args.min_examples,
        # The knobs that DEFINE the selection family and the joins, recorded as data rather than
        # left to be parsed back out of argv (audit T6: the family is a claim, not a CLI detail).
        "layers": layers, "headline_predictor": args.headline_predictor,
        "cluster_by": args.cluster_by or None, "extract_position": args.extract_position,
        "representation_query_kinds": dict(qk_seen),
    }

    rows = []
    pv = {}
    # THE SELECTION FAMILY (audit T6). Every column this loop scans is a column the headline could
    # have been -- that IS the family, and it must be recorded rather than reconstructed later from
    # `--layers`, because a column is dropped whenever any analysed row lacks it. Captured here, in
    # the one loop that decides membership, so the recorded family cannot disagree with the scanned
    # one. `semantic_logodds` is deliberately NOT a member: it is read on a different prompt and a
    # smaller row set, so it shares no permutation draws with these.
    family_cols: Dict[str, List[float]] = collections.OrderedDict()
    for L in layers:
        for stat in ("cos", "proj", "ll"):
            xs = [rep[p].get((L, stat)) for p in kept]
            if any(v is None for v in xs):
                continue
            if stat == "hnorm":
                continue
            r, p = spearman(xs, y)
            name = f"d_surface|L{L}|{stat}" if stat != "ll" else f"logit_lens|L{L}"
            family_cols[name] = list(xs)
            hn = [rep[pp].get((L, "hnorm")) for pp in kept]
            if all(v is not None for v in hn):
                rp, pp_ = rank_partial(xs, y, hn)
                rn, pn = spearman(hn, y)
            else:
                rp = pp_ = rn = pn = float("nan")
            rows.append((name, r, p, float(_sd(xs)), rp, pp_, rn))
            pv[name] = p
    # semantic predictor, on its own (different) prompt
    sem_keys = [p for p in kept if fam_key(meta[p]["family_id"]) in sem_by_fam]
    if sem_keys:
        xs = [sem_by_fam[fam_key(meta[p]["family_id"])] for p in sem_keys]
        ys = [asr[p] for p in sem_keys]
        r, p = spearman(xs, ys)
        rows.append((f"semantic_logodds (n={len(sem_keys)}, OTHER prompt)", r, p, float(_sd(xs)),
                     float("nan"), float("nan"), float("nan")))
        pv["semantic_logodds"] = p

    # House Holm (`reanalyze_corrected.holm_table`), not the local one: it records the family size
    # `m`, the rank and the threshold that produced each decision. C-4 is the precedent -- a Holm
    # whose family size was never recorded, one file over, and the correction turned out to change
    # which layers were rejected. `m` defaults to len(pv), which is the honest family here because
    # every one of these p-values was actually computed.
    import reanalyze_corrected as _rc
    holm_tab = _rc.holm_table(pv)
    rej = {k: bool(v["rejected"]) for k, v in holm_tab.items()}
    rows.sort(key=lambda t: -abs(t[1]))
    print(f"\n{'predictor':38s} {'rho':>8s} {'p':>9s} {'Holm':>5s} "
          f"{'rho|hnorm':>10s} {'p':>9s} {'hnorm~y':>8s}  norm-share")
    for name, r, p, sd, rp, pp_, rn in rows:
        share = (1 - abs(rp) / abs(r)) if (r and math.isfinite(rp) and abs(r) > 1e-9) else float("nan")
        flag = ""
        if math.isfinite(share) and share > 0.33:
            flag = "  <-- >1/3 of this is the NORM, not the axis"
        print(f"{name:38s} {r:>+8.3f} {p:>9.2e} {str(rej.get(name.split(' ')[0], '')):>5s} "
              f"{rp:>+10.3f} {pp_:>9.2e} {rn:>+8.3f} {100*share:>8.0f}%{flag}")
    # The `spearman`/`p` pair in this table IS estimand-consistent (both pooled, both i.i.d.) --
    # unlike the clustered block below, which used to pair a pooled rho with a within-domain p
    # (audit T5). The estimand is stated anyway so no reader has to reconstruct it from the code.
    report["predictors"] = [{"name": n, "spearman": r, "p": p, "sd": sd,
                             "estimand": "rho_pooled", "p_estimand": "rho_pooled (i.i.d.)",
                             "partial_given_hnorm": rp, "partial_p": pp_,
                             "partial_p_estimand": "rho_partial_hnorm_pooled (i.i.d.)",
                             "hnorm_vs_asr": rn,
                             "holm_rejected": bool(rej.get(n.split(" ")[0], False)),
                             "holm_m": (holm_tab.get(n.split(" ")[0], {}) or {}).get("m"),
                             "holm_rank": (holm_tab.get(n.split(" ")[0], {}) or {}).get("rank"),
                             "holm_thr": (holm_tab.get(n.split(" ")[0], {}) or {}).get("thr")}
                            for n, r, p, sd, rp, pp_, rn in rows]
    report["holm_family"] = {
        "m": len(pv), "alpha": 0.05, "members": sorted(pv),
        "estimand": "rho_pooled",
        "p_estimand": "rho_pooled (i.i.d.) -- these are the i.i.d. pooled Spearman p-values, "
                      "WITHDRAWN as the sole inference in retraction R1. The multiplicity "
                      "correction for the citable within-domain estimand is in "
                      "`layer_selection`, not here.",
        "rule": ("every predictor this run actually tested: the d_surface/logit_lens columns "
                 "present on all analysed rows for --layers, plus semantic_logodds. Recorded "
                 "because C-4 showed a Holm whose family size lives only in the code is a Holm "
                 "nobody can check."),
        "n_rows_per_member": {"layer_columns": len(kept), "semantic_logodds": len(sem_keys)},
        "members_are_not_all_on_the_same_rows": bool(sem_keys) and len(sem_keys) != len(kept)}

    # ---------------------------------------------------------------------------------------
    # CLUSTERED INFERENCE (audit B1b, 2026-08-17). Every p-value above treats the prompts as
    # i.i.d., but they are 6 domains x 39, and the PREDICTOR is strongly clustered by domain
    # (ICC ~ 0.45). Retraction R1's stated root cause was pseudo-replication, and this script
    # re-introduced it. The headline p was overstated by ~3.5 orders of magnitude.
    #
    # Two defensible alternatives are reported and BOTH are printed, because with G=6 clusters a
    # cluster-robust sandwich is itself unreliable (the usual rule of thumb wants 30-50 clusters):
    #   * CR1 domain-clustered p on the rank-rank slope;
    #   * a WITHIN-DOMAIN permutation p, which destroys all between-domain signal and is exact-ish
    #     under the null of no within-domain association. This is the one to cite.
    # Also reported: the per-domain rho table, which was previously quoted in the write-up
    # ("positive in 5 of 6 domains") without any committed script producing it — the exact
    # provenance failure that caused retraction R2.
    # ---------------------------------------------------------------------------------------
    # The clustered block is the guard installed for RETRACTION #1 (pseudo-replication). It was
    # reachable only via a truthy --cluster-by, so a one-character typo would silently republish the
    # WITHDRAWN i.i.d. p as the only inference in the file. It now refuses instead.
    if args.cluster_by and args.cluster_by not in (meta[kept[0]].keys() if kept else {}):
        raise SystemExit(
            f"[G2] REFUSING: --cluster-by {args.cluster_by!r} is not a field on the judged rows "
            f"(available e.g. domain/split/bank_block). Clustered inference is MANDATORY here — the "
            f"i.i.d. p was withdrawn as pseudo-replication (R1). Pass a real field, or "
            f"--cluster-by '' to deliberately publish i.i.d. inference only.")
    if not args.cluster_by:
        print("[G2] WARNING: clustering DISABLED — the i.i.d. p below was WITHDRAWN as "
              "pseudo-replication in retraction R1 and must not be reported alone.")
    if args.cluster_by:
        import numpy as _np
        from scipy import stats as _st
        cl = [meta[k].get(args.cluster_by) for k in kept]
        headline = args.headline_predictor
        _pp = headline.split("|")          # e.g. d_surface|L12|proj -> (12, "proj")
        _hl = (int(_pp[1].lstrip("L")), _pp[2])
        xs = [rep[k].get(_hl) for k in kept]
        ys = [asr[k] for k in kept]
        ok = [i for i in range(len(kept))
              if xs[i] is not None and ys[i] is not None and cl[i] is not None]
        if len(ok) > 10 and len({cl[i] for i in ok}) > 1:
            X = _st.rankdata([xs[i] for i in ok]); Y = _st.rankdata([ys[i] for i in ok])
            G = [cl[i] for i in ok]
            X = (X - X.mean()) / X.std(ddof=0); Y = (Y - Y.mean()) / Y.std(ddof=0)
            n = len(X); A = _np.column_stack([_np.ones(n), X])
            beta, *_ = _np.linalg.lstsq(A, Y, rcond=None)
            resid = Y - A @ beta
            bread = _np.linalg.inv(A.T @ A)
            meat = _np.zeros((2, 2))
            groups = sorted(set(G))
            for g in groups:
                idx = [i for i in range(n) if G[i] == g]
                sg_ = A[idx].T @ resid[idx]
                meat += _np.outer(sg_, sg_)
            Gn = len(groups)
            cr1 = (Gn / max(Gn - 1, 1)) * ((n - 1) / max(n - 2, 1))
            V = bread @ (cr1 * meat) @ bread
            se_cl = math.sqrt(max(V[1, 1], 0.0))
            t_cl = beta[1] / se_cl if se_cl else float("nan")
            p_cl = 2 * _st.t.sf(abs(t_cl), df=max(Gn - 1, 1))
            # WITHIN-DOMAIN permutation, on the GROUP-DEMEANED slope (audit A3).
            # The previous statistic was the total slope from an intercept-only design. Shuffling
            # within a group preserves that group's mean of Y exactly, so the BETWEEN-domain
            # component survived every permutation draw and the null was not centred on zero
            # (null mean +0.100 against an observed +0.307 — a third of the statistic was a fixed
            # between-domain offset). Size stayed nominal so nothing was falsely rejected, but the
            # quantity was not the one the label "within-domain" promised, and its power depends on
            # the SIGN of the between-domain slope (0.000 in the adverse case). Demeaning X and Y
            # within domain makes the statistic actually within-domain.
            Xw, Yw = X.copy(), Y.copy()
            for g in groups:
                gi = [i for i in range(n) if G[i] == g]
                Xw[gi] = Xw[gi] - Xw[gi].mean()
                Yw[gi] = Yw[gi] - Yw[gi].mean()
            Aw = _np.column_stack([_np.ones(n), Xw])
            bw, *_ = _np.linalg.lstsq(Aw, Yw, rcond=None)
            rng = _np.random.default_rng(20260817)
            obs = abs(bw[1])
            cnt = 0
            NPERM = 2000
            byg = {g: [i for i in range(n) if G[i] == g] for g in groups}
            for _ in range(NPERM):
                Yp = Yw.copy()
                for g, idx in byg.items():
                    Yp[idx] = Yw[rng.permutation(idx)]
                bp, *_ = _np.linalg.lstsq(Aw, Yp, rcond=None)
                if abs(bp[1]) >= obs:
                    cnt += 1
            p_perm = (cnt + 1) / (NPERM + 1)
            r_naive, p_naive = spearman([xs[i] for i in ok], [ys[i] for i in ok])
            # THE POINT ESTIMATE THE PERMUTATION ACTUALLY TESTS (audit T5). Xw/Yw are the
            # standardised ranks after within-domain demeaning, so their correlation IS the
            # within-domain rank correlation, and it is what `p_perm` is a p-value for. It existed
            # only as the local `bw[1]` slope, under a name (`within_domain_slope`) that did not
            # read as an alternative to `rho`. Because the within-group permutation preserves each
            # group's multiset of Yw, sd(Yw) and sd(Xw) are invariant across draws, so |slope| and
            # |correlation| induce the IDENTICAL permutation p -- reporting the correlation costs
            # nothing and makes the pair comparable with `rho_pooled` on the same scale.
            rho_w = rank_corr_pair([xs[i] for i in ok], [ys[i] for i in ok],
                                   [cl[i] for i in ok])["rho_within_domain"]
            print(f"\n[G2] CLUSTERED INFERENCE for {headline} (cluster={args.cluster_by}, "
                  f"G={Gn}, n={n})")
            print(f"  rho_pooled                {r_naive:+.4f}   (raw pooled Spearman)")
            print(f"  rho_within_domain         {rho_w:+.4f}   (rank corr. after demeaning within "
                  f"{args.cluster_by})")
            print(f"  p_iid_pooled_rho          {p_naive:.2e}   <-- estimand rho_pooled; OVERSTATED: prompts are not independent")
            print(f"  p_cr1_pooled_slope        {p_cl:.2e}   <-- estimand: the POOLED rank-rank slope (G={Gn} is few; indicative)")
            print(f"  p_perm_within_domain_rho  {p_perm:.2e}   <-- CITE THIS ONE, PAIRED WITH rho_within_domain, NOT WITH rho_pooled")
            report["clustered_inference"] = {
                "predictor": headline, "cluster_by": args.cluster_by, "n": n, "n_clusters": Gn,
                # two point estimates, named (audit T5) -- same names as analyze_g64.py
                "rho_pooled": r_naive,
                "rho_within_domain": rho_w,
                "p_iid_pooled_rho": p_naive,
                "p_cr1_pooled_slope": p_cl,
                "p_perm_within_domain_rho": p_perm,
                "p_estimand": "rho_within_domain",
                "p_estimand_by_key": {
                    "p_iid_pooled_rho": "rho_pooled (assumes i.i.d. prompts; WITHDRAWN as the sole "
                                        "inference in retraction R1)",
                    "p_cr1_pooled_slope": "the pooled rank-rank slope (total_slope)",
                    "p_perm_within_domain_rho": "rho_within_domain / within_domain_slope"},
                "within_domain_slope": float(bw[1]), "total_slope": float(beta[1]),
                "n_perm": NPERM,
                "keys_renamed_2026_08_18": {"rho": "rho_pooled", "p_iid": "p_iid_pooled_rho",
                                            "p_cr1": "p_cr1_pooled_slope",
                                            "p_within_domain_perm": "p_perm_within_domain_rho"},
                "estimand_note": (
                    "rho_pooled and rho_within_domain are DIFFERENT quantities. "
                    "p_perm_within_domain_rho is a p-value for rho_within_domain ONLY. Quoting it "
                    "beside rho_pooled -- which is what this artifact did before 2026-08-18 -- "
                    "attaches a within-domain p to a between+within point estimate.")}
            per = {}
            for g in groups:
                idx = byg[g]
                if len(idx) > 3:
                    rg, pg = spearman([xs[ok[i]] for i in idx], [ys[ok[i]] for i in idx])
                    per[str(g)] = {"n": len(idx), "rho": rg, "p": pg}
            report["per_cluster"] = per
            npos = sum(1 for v in per.values() if v["rho"] > 0)
            print(f"\n[G2] PER-{args.cluster_by.upper()} rho for {headline} "
                  f"({npos} of {len(per)} positive):")
            for g, v in sorted(per.items(), key=lambda kv: -kv[1]["rho"]):
                near = "   <-- essentially null" if abs(v["rho"]) < 0.1 else ""
                print(f"  {g:20s} n={v['n']:>4d}  rho={v['rho']:+.3f}  p={v['p']:.3f}{near}")

    # ---------------------------------------------------------------------------------------
    # LAYER SELECTION, REPORTED HONESTLY (audit T6, 2026-08-18)
    #
    # The block above quotes ONE column. This one says what it was chosen out of, and what its
    # numbers look like once that choice is paid for. Three things, none of which existed before:
    #
    #   * the FAMILY and its size `m`, recorded in the artifact. C-4's lesson, applied before it
    #     bites: a multiplicity correction whose family size lives only in the code is a
    #     correction nobody can check, and when C-4's was finally checked it changed the answer.
    #   * `p_perm_maxT_family` -- the same within-domain permutation, run jointly over all `m`
    #     columns on SHARED draws, giving each column a p for "would the BEST of the m have looked
    #     this good under the null?". Plus Holm over the marginal permutation p-values, so both
    #     the correlation-aware and the independence-assuming corrections are on the record.
    #   * a leave-one-cluster-out NESTED selection, which measures the cost of selecting rather
    #     than assuming it (the C-8 precedent: for `probes`, nested selection moved AUROC by
    #     0.0012-0.0018 and changed no conclusion -- but that was measured, not asserted).
    #
    # This runs whether or not --cluster-by is set: with clustering disabled every row is placed in
    # one pseudo-cluster, which makes the within-cluster demeaning global and the permutation the
    # ordinary i.i.d. one. ONE code path, deliberately -- the "one-of-two-paths" bug class has hit
    # this repo three times (most recently R-12), always where a fix landed on the single path and
    # missed the composed one.
    # ---------------------------------------------------------------------------------------
    if args.headline_predictor not in family_cols:
        raise SystemExit(
            f"[G2] REFUSING: --headline-predictor {args.headline_predictor!r} is not one of the "
            f"{len(family_cols)} columns this run scanned "
            f"({', '.join(list(family_cols)[:6])}{'...' if len(family_cols) > 6 else ''}). The "
            f"clustered block would have silently analysed whatever subset of rows happened to "
            f"carry it. Name a column in --layers, or widen --layers.")
    sel_clusters = ([meta[k].get(args.cluster_by) for k in kept] if args.cluster_by
                    else ["_no_clustering"] * len(kept))
    sel_ok = [i for i in range(len(kept)) if sel_clusters[i] is not None]
    sel_cols = collections.OrderedDict(
        (nm, [v[i] for i in sel_ok]) for nm, v in family_cols.items())
    sel_y = [y[i] for i in sel_ok]
    sel_cl = [sel_clusters[i] for i in sel_ok]
    fam = family_within_domain_perm(sel_cols, sel_y, sel_cl,
                                    n_perm=args.family_n_perm, seed=args.family_seed)
    hl_name = args.headline_predictor
    hl = fam["per_predictor"][hl_name]
    # DRIFT GUARD. The family's point estimate for the headline column and `clustered_inference`'s
    # `rho_within_domain` are the same quantity on the same rows; if they ever stop agreeing, one
    # of the two pipelines has changed and the adjusted p would be adjusting a different number
    # than the one printed above -- audit T5's defect, re-entering through the selection block.
    ci_prev = report.get("clustered_inference")
    if ci_prev:
        # The n-mismatch branch used to be the guard's OFF switch: `if ci_prev["n"] == fam["n"]`
        # meant that the one condition proving the two pipelines had selected different rows --
        # and therefore that the adjusted p adjusts a rho computed on a different sample than the
        # one printed above -- silently disabled the check. A guard that stands down exactly when
        # it should fire is a dead guard; both pipelines filter `cluster is not None` on the same
        # `kept` rows, so a mismatch is a bug, not a configuration (verifier, 2026-08-19).
        if ci_prev.get("n") != fam["n"]:
            raise SystemExit(
                f"[G2] REFUSING: clustered_inference analysed {ci_prev.get('n')} rows but the "
                f"selection family analysed {fam['n']} for the same headline {hl_name} on the "
                f"same --cluster-by. The selection-adjusted p would be adjusting a rho estimated "
                f"on a different sample than the one printed above.")
        drift = abs(float(ci_prev["rho_within_domain"]) - hl["rho_within_domain"])
        if not (drift < 1e-9):
            raise SystemExit(
                f"[G2] REFUSING: the selection family computes rho_within_domain="
                f"{hl['rho_within_domain']:+.10f} for {hl_name} but clustered_inference reports "
                f"{ci_prev['rho_within_domain']:+.10f} on the same {fam['n']} rows (drift "
                f"{drift:.3e}). Two pipelines for one estimand is how T5 happened.")
    nested = heldout_layer_selection(sel_cols, sel_y, sel_cl)
    fixed = heldout_fixed_column(sel_cols[hl_name], sel_y, sel_cl)
    argmax_name = fam["argmax_predictor"]
    print(f"\n[G2] LAYER SELECTION (family m={fam['m']}, n={fam['n']}, "
          f"{fam['n_clusters']} cluster(s), {fam['n_perm']} shared draws)")
    print(f"  headline {hl_name}")
    print(f"    rho_within_domain          {hl['rho_within_domain']:+.4f}")
    print(f"    p_perm_within_domain_rho   {hl['p_perm_within_domain_rho']:.2e}   "
          f"<-- MARGINAL: as if this column had been prespecified")
    print(f"    p_perm_maxT_family         {hl['p_perm_maxT_family']:.2e}   "
          f"<-- SELECTION-ADJUSTED (single-step) over the m={fam['m']} columns actually scanned")
    print(f"    p_perm_maxT_stepdown       {hl['p_perm_maxT_stepdown_family']:.2e}   "
          f"<-- SELECTION-ADJUSTED (free step-down); CITE THIS ONE for a CHOSEN column")
    print(f"    holm over the family       rejected={hl['holm_rejected_within_domain']} "
          f"(rank {hl['holm_rank']}, thr {hl['holm_thr']:.2e}, m={fam['m']})")
    if argmax_name != hl_name:
        am = fam["per_predictor"][argmax_name]
        print(f"  NOTE: the headline is NOT the family argmax. |rho_within| is largest at "
              f"{argmax_name} ({am['rho_within_domain']:+.4f} vs {hl['rho_within_domain']:+.4f}).")
    if nested.get("available"):
        print(f"  nested (leave-one-{args.cluster_by or 'cluster'}-out) selection over the same "
              f"family:")
        print(f"    in-sample argmax |rho_within|      "
              f"{nested['in_sample_argmax_abs_rho_within_domain']:+.4f}")
        print(f"    held-out rho of the fold-selected  "
              f"{nested['heldout_selected_rho_weighted_mean']:+.4f}")
        _fx = fixed.get("heldout_rho_weighted_mean")
        print("    held-out rho of the FIXED headline " +
              (f"{_fx:+.4f}" if _fx is not None else f"n/a ({fixed.get('reason')})"))
        print(f"    selection cost (|rho| units)       "
              f"{nested['selection_cost_abs_rho']:+.4f}   "
              f"selection_is_stable={nested['selection_is_stable']} "
              f"({len(nested['distinct_columns_selected'])} distinct column(s) picked)")
    report["layer_selection"] = {
        "headline_predictor": hl_name,
        "headline": hl,
        "cluster_by": args.cluster_by or None,
        "clustering_disabled": not bool(args.cluster_by),
        "family_rule": (
            "every predictor column the scan loop evaluated on all analysed rows: "
            "d_surface|L*|{cos,proj} and logit_lens|L* for the layers given by --layers, minus "
            "any column missing on some analysed row. semantic_logodds is EXCLUDED because it is "
            "read on a different prompt and a smaller row set, so it cannot share draws."),
        "layers_scanned": layers,
        "m": fam["m"], "family": fam["family"], "n": fam["n"], "n_clusters": fam["n_clusters"],
        "n_perm": fam["n_perm"], "seed": fam["seed"], "p_floor": fam["p_floor"],
        "argmax_predictor": argmax_name,
        "argmax_rho_within_domain": fam["argmax_rho_within_domain"],
        "headline_is_family_argmax": argmax_name == hl_name,
        "per_predictor": fam["per_predictor"],
        "nested_selection": nested,
        "fixed_headline_heldout": fixed,
        # `p_perm_within_domain_rho` now appears TWICE in this artifact under one name, with two
        # different values, because the two blocks draw their permutations from different seeds
        # (20260817 there, --family-seed here). That is the shape C-10 was raised about --
        # "does this artifact record X?" having two answers depending on where you looked -- so
        # the relationship is written down rather than left for a reader to trip over.
        "marginal_p_cross_reference": {
            "same_estimand": "rho_within_domain",
            "this_block": hl["p_perm_within_domain_rho"],
            "clustered_inference": (report.get("clustered_inference") or {}).get(
                "p_perm_within_domain_rho"),
            "seed_here": args.family_seed,
            "seed_clustered_inference": 20260817,
            "note": ("Two INDEPENDENT permutation draws of the same marginal quantity on the same "
                     "rows, not two quantities and not one number reported twice; they differ by "
                     "Monte-Carlo error only (n_perm draws => se ~ sqrt(p(1-p)/n_perm)). Neither "
                     "is the citable number for a CHOSEN column: that is "
                     "p_perm_maxT_stepdown_family."),
        },
        "p_estimand": "rho_within_domain",
        "estimand_note": (
            "Every p here is a p-value for rho_within_domain, NEVER for rho_pooled. "
            "p_perm_within_domain_rho is the MARGINAL within-domain permutation p -- valid only "
            "for a column named before the data were seen; it is the number the pre-2026-08-18 "
            "artifact published for a column chosen out of m. p_perm_maxT_family is single-step "
            "Westfall-Young over the same shared draws (the correlation-aware analogue of "
            "Bonferroni). p_perm_maxT_stepdown_family is the free step-down version, which is "
            "uniformly at least as powerful and is THE ONE TO CITE for a chosen column. Holm over "
            "the marginal p-values is reported too: it is step-down but correlation-blind, so "
            "neither it nor single-step maxT dominates the other and they can disagree (on the "
            "Qwen3 artifact Holm rejects at m=28 while single-step maxT gives 0.061). All three "
            "control the family-wise error rate over the m columns."),
        "nested_selection_note": (
            "leave-one-cluster-out: the column is re-chosen by argmax |rho_within_domain| on the "
            "other clusters and evaluated on the held-out one, so no cluster contributes to both "
            "choosing and scoring. `fixed_headline_heldout` repeats the evaluation WITHOUT "
            "re-choosing, so the gap between the two isolates the cost of selection from ordinary "
            "out-of-sample shrinkage."),
    }

    if zero:
        yz = [asr[p] for p in zero]
        for L in (12, 31):
            xs = [rep[p].get((L, "cos")) for p in zero]
            if all(v is not None for v in xs):
                r, p = spearman(xs, yz)
                print(f"  [zero-demo stratum, n={len(zero)}] d_surface|L{L}|cos rho={r:+.3f} p={p:.2e}")

    # ---- §9 Q6/Q7: does Boombness survive controlling for refusalness? -------------- #
    if args.refusalness:
        R = read_jsonl(os.path.join(args.refusalness, "results.jsonl"))
        refus = {r["prompt_id"]: r for r in R if r["prompt_id"] in asr}
        rk = [p for p in kept if p in refus]
        print(f"\n[G2] refusalness joined on prompt_id for {len(rk)}/{len(kept)} analysed prompts")
        # POSITION-MATCH ASSERTION (audit D3, 2026-08-17). RETRACTION #5 happened because
        # `d_surface` was read at `codeword_last` while refusalness was read at the last prompt
        # token, and NOTHING in the join checked. `refusalness.py` records `readout_position` on
        # every row and no script has ever read it. A comparison of two probes at two different
        # tokens is not a comparison, so this now refuses rather than warns.
        rpos = {r.get("readout_position") for r in R if r.get("prompt_id") in asr}
        epos = args.extract_position
        if rpos - {None}:
            if len(rpos - {None}) > 1:
                raise SystemExit(f"[G2] refusalness rows mix readout positions {rpos} — "
                                 f"a single run must use one position")
            rp = (rpos - {None}).pop()
            if rp != epos:
                raise SystemExit(
                    f"[G2] REFUSING: refusalness was read at '{rp}' but the representation at "
                    f"'{epos}'. Comparing them is the footing mismatch that caused RETRACTION #5. "
                    f"Re-run refusalness.py with --position {epos}, or pass "
                    f"--extract-position {rp} if that is genuinely what you want to compare.")
            print(f"[G2] position match OK: both probes read at '{rp}'")
        else:
            print("[G2] WARNING: refusalness rows carry no `readout_position` field (pre-2026-08-17 "
                  "run) — the position match CANNOT be verified. Treat any Boombness-vs-refusalness "
                  "ratio from this run as unfooted.")
        if rk:
            import numpy as np
            from sklearn.linear_model import LinearRegression
            yv = np.array([asr[p] for p in rk])
            med: Dict[str, object] = {"n": len(rk)}
            # SYMMETRIC HEAD-TO-HEAD. The first version pinned refusalness to L18 (near its own
            # minimum) and compared it against the argmax-selected Boombness column, then quoted
            # the resulting 40x. Given the same freedom, refusalness's best layer is L12
            # (R2 0.0386, rho +0.167 p=0.011) and the honest ratio is ~3.7x. The joint model over
            # all refusal layers is also reported, because "+0.0005 added" was one fixed column
            # against a selected one; jointly refusalness adds ~+0.039.
            refus_layers = [RL for RL in (12, 14, 16, 18, 20)
                            if f"refusalness|L{RL}|proj" in refus[rk[0]]]
            R_all = np.column_stack([[refus[p][f"refusalness|L{RL}|proj"] for p in rk]
                                     for RL in refus_layers]) if refus_layers else None
            best_rl, best_r2 = None, -1.0
            for RL in refus_layers:
                v = np.array([refus[p][f"refusalness|L{RL}|proj"] for p in rk]).reshape(-1, 1)
                r2 = LinearRegression().fit(v, yv).score(v, yv)
                if r2 > best_r2:
                    best_rl, best_r2 = RL, r2
            if R_all is not None:
                r2_joint = LinearRegression().fit(R_all, yv).score(R_all, yv)
                print(f"  refusalness: best single layer L{best_rl} R2={best_r2:.4f}; "
                      f"all {len(refus_layers)} layers jointly R2={r2_joint:.4f}")
                med["refusalness_best_layer"] = best_rl
                med["refusalness_best_r2"] = best_r2
                med["refusalness_joint_r2"] = r2_joint
                # within-arm range restriction, the reason the R2 is small at all
                for RL in refus_layers:
                    v = [refus[p][f"refusalness|L{RL}|proj"] for p in rk]
                    med[f"refusalness_L{RL}_sd_within_arm"] = float(np.std(v))
            for RL in refus_layers:
                col = f"refusalness|L{RL}|proj"
                rv = np.array([refus[p][col] for p in rk])
                r0, p0 = spearman(rv.tolist(), yv.tolist())
                print(f"  refusalness L{RL:<2d} -> ASR   rho={r0:+.3f} p={p0:.2e}  sd={float(rv.std()):.3f}")
                med[f"refusalness_L{RL}_vs_asr"] = {"spearman": r0, "p": p0}
                # does the best representation predictor add over refusalness alone?
                for name, LL, stat in (("d_surface|L8|proj", 8, "proj"),
                                       ("d_surface|L12|proj", 12, "proj"),
                                       ("d_surface|L31|cos", 31, "cos")):
                    xv = np.array([rep[p].get((LL, stat), float("nan")) for p in rk])
                    if np.isnan(xv).any():
                        continue
                    X1 = rv.reshape(-1, 1)
                    X2 = np.column_stack([rv, xv])
                    r1 = LinearRegression().fit(X1, yv).score(X1, yv)
                    r2 = LinearRegression().fit(X2, yv).score(X2, yv)
                    # and the reverse: does refusalness add over Boombness alone?
                    Xb = xv.reshape(-1, 1)
                    rb = LinearRegression().fit(Xb, yv).score(Xb, yv)
                    add_joint = float("nan")
                    if R_all is not None:
                        Xj = np.column_stack([R_all, xv])
                        add_joint = LinearRegression().fit(Xj, yv).score(Xj, yv) - rb
                    print(f"    R2 refusal-L{RL}-only {r1:.4f} | +{name} -> {r2:.4f} "
                          f"(Boombness adds {r2-r1:+.4f}) | {name}-only {rb:.4f} "
                          f"(this refusal layer adds {r2-rb:+.4f}; ALL refusal layers jointly add "
                          f"{add_joint:+.4f})")
                    # PERSIST THE JOINT COMPARISON, not just the single-layer one (audit 18.8/19.7).
                    # `add_joint` — how much ALL refusalness layers add over Boombness — was
                    # print-only, so the numbers the §18 label actually turns on existed in a
                    # terminal scrollback and in prose, and NOT in any artifact. That is the same
                    # "nothing in the repo regenerates this" failure that caused RETRACTION #2,
                    # sitting under the label itself. The asymmetry is also recorded explicitly:
                    # `delta_refusal_over_boombness` is 1 refusal column vs 1 Boombness column,
                    # while `add_joint` is 5 refusal columns vs 1 — those two are NOT a symmetric
                    # pair and were once quoted as if they were.
                    med[f"L{RL}_vs_{name}"] = {"r2_refusal_only": r1, "r2_both": r2,
                                               "delta_boombness_over_refusal": r2 - r1,
                                               "r2_boombness_only": rb,
                                               "delta_refusal_over_boombness": r2 - rb,
                                               "r2_refusal_joint_plus_boombness":
                                                   (rb + add_joint) if add_joint == add_joint else None,
                                               "delta_refusal_JOINT_over_boombness": add_joint,
                                               "n_refusal_cols_single": 1,
                                               "n_refusal_cols_joint":
                                                   (int(R_all.shape[1]) if R_all is not None else 0),
                                               "n_boombness_cols": 1,
                                               "asymmetry_note":
                                                   "delta_refusal_over_boombness is 1-vs-1; "
                                                   "delta_refusal_JOINT_over_boombness is "
                                                   "n_refusal_cols_joint-vs-1. Do not quote them as a "
                                                   "symmetric pair."}
            report["mediation"] = med

    out = args.out or os.path.join(args.judge, "g2_analysis.json")
    with open(out, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\n[G2] -> {out}")
    return 0


def _sd(xs):
    xs = [x for x in xs if x is not None]
    if len(xs) < 2:
        return float("nan")
    m = sum(xs) / len(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1))


if __name__ == "__main__":
    raise SystemExit(main())
