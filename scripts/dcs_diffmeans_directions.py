#!/usr/bin/env python3
"""DCS — PHASE 3 §9 — DIFFERENCE-IN-MEANS DIRECTIONS on the codeword's L6-14 hidden state.

WHY THIS FILE EXISTS, AND WHAT IT IS NOT
----------------------------------------
`PR-035` / `R-086` / `R-089` answered the **CLASSIFIER** question (the brief's §10): a multinomial
logistic probe trained on cell `B` identifies WHICH of bomb/knife/gun the demonstrations installed,
0.7485 vs 0.333 chance, 6/6 leave-one-domain-out folds. That is a **decodability** result and it is
`POSITIVE` and independently verified (§54).

This file asks the **DIRECTION** question (the brief's §9), which is a *different instrument* and is
NOT covered by `PR-035`:

    v_c(l)             = mean_f [ h_l(cell C, family f) - h_l(cell A, family f) ]     (PAIRED)
    v_bomb_specific(l) = v_bomb(l) - mean( v_knife(l), v_gun(l), v_club(l) )

This is exactly the "difference-in-means direction (secondary instrument)" the preregistration
already declares in §6.3 of the log, which has never been run. The brief is explicit that a geometry
proxy failing ONCE (`R-002`, pre-aggregated means, no test statistic, no train/test split) is not a
reason to abandon diff-in-means; the instrument here is not that one -- every direction is estimated
on TRAIN domains only and scored on HELD-OUT domains.

⛔ A direction is a strictly WEAKER instrument than a fitted probe: it is a rank-1, unsupervised-
covariance-free readout. A null here would NOT contradict `R-086`. A positive here would say the
concept-identity signal is carried by a **single linear axis constructible without labels on the
test cell**, which is what a steering / ablation experiment would need.

TRAIN/TEST DISCIPLINE (non-negotiable, and the whole point)
----------------------------------------------------------
n = 6 domains. LEAVE-ONE-DOMAIN-OUT. For held-out domain d, every one of the four v_c(l) and the
residualised v_bomb_specific(l) is estimated from the paired (C - A) differences of the OTHER FIVE
domains only. The z-standardisation constants are also computed on TRAIN-domain cell-`A` rows only.
No held-out row touches any estimated quantity. There is NO layer selection and NO hyperparameter:
the reported statistic is the mean over the whole inherited band L6-14, so there is nothing to tune
and no selection defect of the §28.2 kind is possible here.

⛔⛔ THE PRIMARY TEST — DECLARED HERE, IN THE FILE, AND THERE IS EXACTLY ONE ⛔⛔
------------------------------------------------------------------------------
  PRIMARY  On the `button` arm: does held-out cell-`C` **bomb** project onto `v_bomb_specific`
           MORE than the pooled cell-`C` hard negatives (knife, gun, club) do?

    unit of independence : DOMAIN, n = 6
    per-domain statistic : Delta_d = [ mean over l in 6..14 of AUROC_d(C_bomb vs pooled C_negatives
                                        | projection on v_hat_bomb_specific(l)) ] - 0.5
    test                 : EXACT TWO-SIDED SIGN TEST on sign(Delta_d), n = 6
    alpha                : 0.05
    ATTAINABLE p-FLOOR   : 2 / 2^6 = 0.03125   <-- stated BEFORE any p is computed.
                           => only 6/6 or 0/6 domains can clear alpha at all. 5/6 gives p = 0.21875.

  ⛔ EVERY OTHER NUMBER IN THIS FILE IS **DESCRIPTIVE** AND CARRIES **NO p-VALUE**.
     That is not modesty, it is arithmetic: with n = 6 the sign-test floor is 0.03125, so ANY Holm
     family with m >= 2 has an adjusted floor of 2 * 0.03125 = 0.0625 > 0.05 and is UNINFORMATIVE
     BY CONSTRUCTION -- it could not reject even on a perfect 6/6. Declaring one primary and
     refusing to attach p-values to the rest is the only honest option at this n.
     (Same reasoning as `R-083`/`R-088`, and a sign test has no relabel symmetry, so `C-058`/`C-062`
      does not apply here -- see §52's blast-radius table.)

CONTROLS AND LIMITATIONS THAT ARE COMPUTED, NOT ASSERTED
--------------------------------------------------------
* `n_examples = 0` NULL. At zero demonstrations cells `A` and `C` are BYTE-IDENTICAL prompts (this
  script re-verifies that from the banks), so the direction must be ~0 and every AUROC ~0.5. This is
  the same blocking null that voided `PR-031` (`C-049`) and repaired it (`R-084`). Reported.
* §46.1 / `C-060` CELL-`A` OVERLAP. `bomb` and `club` share byte-identical cell-`A` prompts on 82
  design cells across the banks. Because v_c SUBTRACTS cell `A`, a shared cell `A` makes the A-term
  CANCEL in v_bomb - v_club (helpful), while a non-shared cell `A` leaves a benign-corpus difference
  as a NUISANCE TERM inside v_bomb_specific (harmful). This script MEASURES the overlap on the exact
  paired families it uses and reports it as a limitation.
* BOMB-ABSENT CONTROL: `v_knife - v_club`, held-out `C_knife` vs `C_club`. Bomb appears in no term
  of that direction, so a remapping-STRENGTH axis anchored on bomb cannot produce it. This is the
  direction analogue of §23.5 clause 4 -- the contrast `R-089` restored the `PR-035` verdict on.
  ⛔ Descriptive, no p: the one p in this file is already spent on the primary.
* LEXICAL TRANSFER: directions fitted on `button` ONLY, evaluated on `basket`. Two variants, both
  descriptive: (T1) fit on all 6 button domains, and (T2) fit on button minus domain d, score basket
  domain d -- T2 also removes the shared-domain channel. ⚠ §46.2 (`C-060`) already records that
  cells `B`/`E` share demonstration blocks between `button_X` and `basket_X`; this instrument uses
  cells `A`/`C`, which are modally distinct, but the banks are still not independent samples.

REUSE
-----
Population construction, the §28.1 exclusion, cache loading, cache binding and run discovery are
IMPORTED from `scripts/dcs_verify_pr035_primary.py` (`build`, `load_cache`, `attach`, `find_run`) --
they are not re-copied, so this file cannot drift from the verified `PR-035` population. The exact
two-sided sign test is imported from `scripts/dcs_pr037_analysis.py`. ⛔ Nothing is imported from
`scripts/dcs_bombness_specificity.py`, which is frozen.

USAGE
-----
  python scripts/dcs_diffmeans_directions.py --self-test
  python scripts/dcs_diffmeans_directions.py [--out results.json] [--arms button,basket]
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import dcs_verify_pr035_primary as vp                      # build/load_cache/attach/find_run
from dcs_pr037_analysis import sign_test_two_sided         # exact two-sided sign test

# ------------------------------------------------------------------ declared constants (§6.2/§6.3)
CLASSES = ("bomb", "knife", "gun", "club")
TARGET = "bomb"
HARDNEG = ("knife", "gun", "club")
LAYERS = tuple(range(6, 15))          # inherited band, block convention L == hidden_states[L+1]
NEXAMPLES = (4, 8)                    # the doses the headline results use (§6.2)
CHANNEL = "semantic_one_word"         # what PR-035 actually ran (vp.CHANNEL)
N_DOMAINS = 6
SIGN_FLOOR = 2.0 / 2 ** N_DOMAINS     # 0.03125 -- printed before any p
HNORM_TOL = vp.HNORM_TOL

PRIMARY_NAME = ("button / v_bomb_specific / held-out C_bomb vs pooled C_{knife,gun,club} / "
                "band-mean AUROC vs 0.5 / exact two-sided sign test over 6 domains")


# =============================================================================== small statistics
def auroc(pos, neg):
    """Tie-corrected AUROC = P(score(pos) > score(neg)) + 0.5 P(=). None if a side is empty."""
    pos = np.asarray(pos, dtype=float).ravel()
    neg = np.asarray(neg, dtype=float).ravel()
    if pos.size == 0 or neg.size == 0:
        return None
    x = np.concatenate([pos, neg])
    order = np.argsort(x, kind="mergesort")
    sx = x[order]
    ranks = np.empty(x.size, dtype=float)
    i = 0
    while i < sx.size:
        j = i
        while j + 1 < sx.size and sx[j + 1] == sx[i]:
            j += 1
        ranks[order[i:j + 1]] = 0.5 * (i + j) + 1.0
        i = j + 1
    n1 = pos.size
    return float((ranks[:n1].sum() - n1 * (n1 + 1) / 2.0) / (n1 * neg.size))


def std_diff(a, b):
    """Cohen's d, pooled sd. None when it is not defined."""
    a = np.asarray(a, dtype=float).ravel()
    b = np.asarray(b, dtype=float).ravel()
    if a.size < 2 or b.size < 2:
        return None
    s = np.sqrt(0.5 * (a.var(ddof=1) + b.var(ddof=1)))
    return float((a.mean() - b.mean()) / s) if s > 0 else None


def _m(xs):
    xs = [x for x in xs if x is not None]
    return float(np.mean(xs)) if xs else None


# ============================================================================= data (REUSED loaders)
def _pack(rows, layers):
    """rows carry `_vec` [len(layers), H] from vp.attach."""
    if not rows:
        return {"dom": np.array([], dtype=object), "fam": np.array([], dtype=object),
                "X": np.zeros((0, len(layers), 1), dtype=np.float32)}
    return {"dom": np.array([r["domain"] for r in rows], dtype=object),
            "fam": np.array([r["family_id"] for r in rows], dtype=object),
            "X": np.stack([r["_vec"] for r in rows]).astype(np.float32)}


def _bind_q95(run_dir, layers, reps):
    """V6 of dcs_verify_pr035_primary, same logic: ||rep|| must match THIS run's own hnorm|L*.
    A producer-side join of one class to another bank's cache is lossless under prompt_id."""
    byid = {}
    with open(os.path.join(run_dir, "results.jsonl")) as fh:
        for line in fh:
            r = json.loads(line)
            byid[r["prompt_id"]] = r
    errs = []
    for pid, v in list(reps.items())[:400]:
        row = byid.get(pid)
        if not row:
            continue
        for j, L in enumerate(layers):
            h = row.get("hnorm|L%d" % L)
            if h:
                errs.append(abs(float(np.linalg.norm(v[j])) - float(h)) / max(1e-9, abs(float(h))))
    return float(np.quantile(errs, 0.95)) if errs else None


def load_arm(codeword, nex=NEXAMPLES, cells=("A", "C"), verbose=True):
    """Build the {(class, cell): packed} population for one codeword, REUSING PR-035's builders.

    vp.build applies §28.1's exclusion; vp.attach binds each class to ITS OWN run's cache."""
    prev = vp.CODEWORD
    vp.CODEWORD = codeword
    try:
        arm, bind, layers_ref, runs = {}, {}, None, {}
        for cc in CLASSES:
            run = vp.find_run(cc)
            if run is None:
                raise SystemExit("no complete extract run for %s_%s" % (codeword, cc))
            runs[cc] = os.path.basename(run)
            layers, reps = vp.load_cache(run)
            if layers_ref is None:
                layers_ref = list(layers)
            elif list(layers) != layers_ref:
                raise SystemExit("%s_%s layers %s != %s" % (codeword, cc, layers, layers_ref))
            bind[cc] = _bind_q95(run, layers, reps)
            for cell in cells:
                rows = vp.attach(vp.build(cc, (cell,), tuple(nex)), layers, reps, cc)
                arm[(cc, cell)] = _pack(rows, layers)
            del reps
            if verbose:
                print("    %-7s %-5s run=%s  %s" % (
                    codeword, cc, runs[cc],
                    " ".join("%s:%d" % (c, arm[(cc, c)]["X"].shape[0]) for c in cells)))
    finally:
        vp.CODEWORD = prev
    return {"arm": arm, "layers": layers_ref, "bind": bind, "runs": runs,
            "domains": sorted({d for cc in CLASSES for d in arm[(cc, "C")]["dom"]})}


def cellA_overlap(codeword, nex=NEXAMPLES):
    """§46.1 / C-060, MEASURED on the paired families this instrument actually uses: how often is
    cell `A` byte-identical between two concept banks? A shared cell `A` CANCELS in v_c - v_c'; a
    non-shared one leaves a benign-corpus nuisance inside v_bomb_specific."""
    prev = vp.CODEWORD
    vp.CODEWORD = codeword
    try:
        A = {}
        for cc in CLASSES:
            A[cc] = {r["family_id"]: r for r in vp.build(cc, ("A",), tuple(nex))}
    finally:
        vp.CODEWORD = prev
    out = []
    for i, a in enumerate(CLASSES):
        for b in CLASSES[i + 1:]:
            common = sorted(set(A[a]) & set(A[b]))
            same_p = sum(1 for f in common if A[a][f]["full_prompt"] == A[b][f]["full_prompt"])
            same_d = sum(1 for f in common if A[a][f].get("demo_block") == A[b][f].get("demo_block"))
            out.append({"pair": "%s/%s" % (a, b), "n_common_families": len(common),
                        "identical_full_prompt": same_p, "identical_demo_block": same_d,
                        "frac_identical_prompt": (same_p / len(common)) if common else None})
    return out


def n0_prompt_identity(codeword):
    """The n_examples=0 null's premise, verified from the banks rather than assumed: at zero
    demonstrations cell A and cell C (and every concept bank) carry the SAME prompt text."""
    prev = vp.CODEWORD
    vp.CODEWORD = codeword
    try:
        A = {cc: {r["family_id"]: r for r in vp.build(cc, ("A",), (0,))} for cc in CLASSES}
        C = {cc: {r["family_id"]: r for r in vp.build(cc, ("C",), (0,))} for cc in CLASSES}
    finally:
        vp.CODEWORD = prev
    ac = []
    for cc in CLASSES:
        com = sorted(set(A[cc]) & set(C[cc]))
        ac.append((cc, len(com), sum(1 for f in com
                                     if A[cc][f]["full_prompt"] == C[cc][f]["full_prompt"])))
    com = sorted(set(C[TARGET]) & set(C["knife"]))
    xb = (len(com), sum(1 for f in com
                        if C[TARGET][f]["full_prompt"] == C["knife"][f]["full_prompt"]))
    return {"A_vs_C_same_bank": [{"class": c, "n": n, "identical": k} for c, n, k in ac],
            "C_bomb_vs_C_knife": {"n": xb[0], "identical": xb[1]}}


# ============================================================================== the instrument
def paired_index(arm):
    """Pair cell C to cell A on `family_id` -- 'PAIRED where prompt ids allow it'. family_id encodes
    domain|split|slot|n_examples|strength|consistency|position|role_style|query_kind, so it is the
    natural pairing key and it is unique within a cell."""
    pidx = {}
    for cc in CLASSES:
        A, C = arm[(cc, "A")], arm[(cc, "C")]
        pos = {f: i for i, f in enumerate(A["fam"])}
        ia, ic, dm = [], [], []
        for j, f in enumerate(C["fam"]):
            i = pos.get(f)
            if i is not None:
                ia.append(i)
                ic.append(j)
                dm.append(C["dom"][j])
        pidx[cc] = (np.array(ia, dtype=int), np.array(ic, dtype=int), np.array(dm, dtype=object))
    return pidx


def directions(arm, pidx, train_doms):
    """v_c(l) = mean over TRAIN paired families of [ h_l(C,f) - h_l(A,f) ], plus the residualised
    v_bomb_specific = v_bomb - mean(v_knife, v_gun, v_club). float64, unnormalised."""
    v, n_used = {}, {}
    td = set(train_doms)
    for cc in CLASSES:
        ia, ic, dm = pidx[cc]
        m = np.array([d in td for d in dm], dtype=bool)
        if not m.any():
            return None, None
        D = (arm[(cc, "C")]["X"][ic[m]].astype(np.float64)
             - arm[(cc, "A")]["X"][ia[m]].astype(np.float64))
        v[cc] = D.mean(axis=0)
        n_used[cc] = int(m.sum())
    v["bomb_specific"] = v[TARGET] - np.mean([v[c] for c in HARDNEG], axis=0)
    # BOMB-ABSENT control, the direction analogue of §23.5 clause 4 (the contrast R-089 leans on):
    # bomb appears NOWHERE in this direction, so a strength axis anchored on bomb cannot drive it.
    v["knife_minus_club"] = v["knife"] - v["club"]
    return v, n_used


def unit(v):
    n = np.linalg.norm(v, axis=1, keepdims=True)
    return v / np.maximum(n, 1e-12)


def project(X, vhat):
    """X [n, nL, H] -> [n, nL] projections on the per-layer unit direction."""
    if X.shape[0] == 0:
        return np.zeros((0, vhat.shape[0]))
    return np.einsum("nlh,lh->nl", X.astype(np.float64), vhat)


def _z(arm, vhat, train_doms):
    """Centre/scale constants from TRAIN-domain cell-`A` rows pooled over the four banks. AUROC and
    Cohen's d are invariant to this; it exists only so the printed projections read in units of the
    benign baseline's own spread."""
    td = set(train_doms)
    base = []
    for cc in CLASSES:
        A = arm[(cc, "A")]
        m = np.array([d in td for d in A["dom"]], dtype=bool)
        if m.any():
            base.append(project(A["X"][m], vhat))
    if not base:
        return 0.0, 1.0
    B = np.concatenate(base, axis=0)
    sd = B.std(axis=0)
    sd[sd < 1e-12] = 1.0
    return B.mean(axis=0), sd


def _rows(pack, dom):
    m = np.array([d == dom for d in pack["dom"]], dtype=bool)
    return pack["X"][m]


def eval_fold(arm, v, train_doms, test_doms, layers):
    """Score held-out rows on the two directions of interest. Returns per-layer metric arrays."""
    out = {}
    for dname in (TARGET, "bomb_specific"):
        vhat = unit(v[dname])
        mu, sd = _z(arm, vhat, train_doms)
        g = {}
        for cc in CLASSES:
            for cell in ("A", "C"):
                X = np.concatenate([_rows(arm[(cc, cell)], d) for d in test_doms], axis=0) \
                    if test_doms else arm[(cc, cell)]["X"]
                g["%s_%s" % (cell, cc)] = (project(X, vhat) - mu) / sd
        negC = np.concatenate([g["C_%s" % c] for c in HARDNEG], axis=0)
        nL = len(layers)
        rec = {"mean_proj": {k: [float(g[k][:, l].mean()) if g[k].shape[0] else None
                                for l in range(nL)] for k in g},
               "n": {k: int(g[k].shape[0]) for k in g}}
        rec["auroc_Cbomb_vs_Abomb"] = [auroc(g["C_bomb"][:, l], g["A_bomb"][:, l]) for l in range(nL)]
        rec["d_Cbomb_vs_Abomb"] = [std_diff(g["C_bomb"][:, l], g["A_bomb"][:, l]) for l in range(nL)]
        rec["auroc_Cbomb_vs_negC"] = [auroc(g["C_bomb"][:, l], negC[:, l]) for l in range(nL)]
        rec["d_Cbomb_vs_negC"] = [std_diff(g["C_bomb"][:, l], negC[:, l]) for l in range(nL)]
        for c in HARDNEG:
            rec["auroc_Cbomb_vs_C%s" % c] = [auroc(g["C_bomb"][:, l], g["C_%s" % c][:, l])
                                             for l in range(nL)]
        out[dname] = rec

    # BOMB-ABSENT control: does held-out C_knife project above held-out C_club on v_knife - v_club?
    vhat = unit(v["knife_minus_club"])
    mu, sd = _z(arm, vhat, train_doms)
    gk, gc = {}, {}
    for cc, store in (("knife", gk), ("club", gc)):
        X = np.concatenate([_rows(arm[(cc, "C")], d) for d in test_doms], axis=0) \
            if test_doms else arm[(cc, "C")]["X"]
        store["z"] = (project(X, vhat) - mu) / sd
    nL = len(layers)
    out["bomb_absent_knife_vs_club"] = {
        "auroc": [auroc(gk["z"][:, l], gc["z"][:, l]) for l in range(nL)],
        "d": [std_diff(gk["z"][:, l], gc["z"][:, l]) for l in range(nL)],
        "mean_z_C_knife": [float(gk["z"][:, l].mean()) if gk["z"].shape[0] else None
                           for l in range(nL)],
        "mean_z_C_club": [float(gc["z"][:, l].mean()) if gc["z"].shape[0] else None
                          for l in range(nL)]}

    # descriptive: does each concept's OWN direction separate its OWN held-out C from its own A?
    own = {}
    for cc in CLASSES:
        vhat = unit(v[cc])
        mu, sd = _z(arm, vhat, train_doms)
        XC = np.concatenate([_rows(arm[(cc, "C")], d) for d in test_doms], axis=0) \
            if test_doms else arm[(cc, "C")]["X"]
        XA = np.concatenate([_rows(arm[(cc, "A")], d) for d in test_doms], axis=0) \
            if test_doms else arm[(cc, "A")]["X"]
        pc, pa = (project(XC, vhat) - mu) / sd, (project(XA, vhat) - mu) / sd
        own[cc] = {"auroc": [auroc(pc[:, l], pa[:, l]) for l in range(len(layers))],
                   "d": [std_diff(pc[:, l], pa[:, l]) for l in range(len(layers))],
                   "mean_proj_C": [float(pc[:, l].mean()) if pc.shape[0] else None
                                   for l in range(len(layers))],
                   "mean_proj_A": [float(pa[:, l].mean()) if pa.shape[0] else None
                                   for l in range(len(layers))]}
    out["own_direction_C_vs_A"] = own
    return out


def lodo(bundle, verbose=True):
    """Leave-one-domain-out over the 6 domains. Directions from TRAIN domains only, always."""
    arm, layers, domains = bundle["arm"], bundle["layers"], bundle["domains"]
    pidx = paired_index(arm)
    folds, dirs = {}, {}
    for d in domains:
        train = [x for x in domains if x != d]
        v, n_used = directions(arm, pidx, train)
        if v is None:
            continue
        folds[d] = eval_fold(arm, v, train, [d], layers)
        folds[d]["n_train_pairs"] = n_used
        dirs[d] = v
    return {"folds": folds, "dirs": dirs, "pidx": pidx, "layers": layers, "domains": domains}


def band(vals):
    """Mean over the whole L6-14 band. NO layer selection anywhere in this file."""
    vals = [x for x in vals if x is not None]
    return float(np.mean(vals)) if vals else None


def primary(res):
    """THE one preregistered test. See the module docstring."""
    doms = sorted(res["folds"])
    per = {d: band(res["folds"][d]["bomb_specific"]["auroc_Cbomb_vs_negC"]) for d in doms}
    deltas = [per[d] - 0.5 for d in doms if per[d] is not None]
    p, neg, pos, n, floor = sign_test_two_sided(deltas)
    return {"name": PRIMARY_NAME, "per_domain_band_auroc": per,
            "deltas": {d: (per[d] - 0.5 if per[d] is not None else None) for d in doms},
            "n_domains": n, "n_positive": pos, "n_negative": neg,
            "p_two_sided_sign": p, "attainable_floor": floor,
            "mean_band_auroc": _m(list(per.values()))}


def transfer(fit_bundle, eval_bundle, layers):
    """LEXICAL TRANSFER: directions fitted on the FIT arm (button) only, scored on the EVAL arm
    (basket). T1 fits on all 6 fit-arm domains; T2 fits on fit-arm minus d and scores eval-arm d,
    which additionally removes the shared-domain channel. Both DESCRIPTIVE, no p-value."""
    fa, ea = fit_bundle["arm"], eval_bundle["arm"]
    pidx = paired_index(fa)
    doms = sorted(set(fit_bundle["domains"]) & set(eval_bundle["domains"]))
    out = {}

    v_all, _ = directions(fa, pidx, fit_bundle["domains"])
    t1 = {}
    for d in doms:
        t1[d] = eval_fold(ea, v_all, fit_bundle["domains"], [d], layers)
    out["T1_fit_all_button_domains"] = {
        "per_domain_band_auroc_spec_bomb_vs_negC": {
            d: band(t1[d]["bomb_specific"]["auroc_Cbomb_vs_negC"]) for d in doms},
        "per_domain_band_auroc_vbomb_C_vs_A": {
            d: band(t1[d][TARGET]["auroc_Cbomb_vs_Abomb"]) for d in doms},
        "per_domain_band_d_vbomb_C_vs_A": {
            d: band(t1[d][TARGET]["d_Cbomb_vs_Abomb"]) for d in doms}}

    t2 = {}
    for d in doms:
        v, _ = directions(fa, pidx, [x for x in fit_bundle["domains"] if x != d])
        if v is None:
            continue
        t2[d] = eval_fold(ea, v, [x for x in fit_bundle["domains"] if x != d], [d], layers)
    out["T2_fit_button_minus_d_score_basket_d"] = {
        "per_domain_band_auroc_spec_bomb_vs_negC": {
            d: band(t2[d]["bomb_specific"]["auroc_Cbomb_vs_negC"]) for d in t2},
        "per_domain_band_auroc_vbomb_C_vs_A": {
            d: band(t2[d][TARGET]["auroc_Cbomb_vs_Abomb"]) for d in t2},
        "per_domain_band_d_vbomb_C_vs_A": {
            d: band(t2[d][TARGET]["d_Cbomb_vs_Abomb"]) for d in t2}}
    for k in out:
        out[k]["mean_band_auroc_spec_bomb_vs_negC"] = _m(
            list(out[k]["per_domain_band_auroc_spec_bomb_vs_negC"].values()))
        out[k]["mean_band_auroc_vbomb_C_vs_A"] = _m(
            list(out[k]["per_domain_band_auroc_vbomb_C_vs_A"].values()))
    out["note"] = ("DESCRIPTIVE ONLY, no p-value: the primary is already declared and n=6 makes any "
                   "second test uninformative (floor 0.03125, Holm m>=2 floor 0.0625 > alpha).")
    return out


def geometry(res, layers):
    """Descriptive geometry of the directions themselves: are the four v_c even distinct, and is
    v_bomb_specific stable across the six train folds?"""
    doms = sorted(res["dirs"])
    nL = len(layers)
    cos_cross, norms, stab = {}, {}, {}
    for i, a in enumerate(CLASSES):
        norms[a] = [float(np.mean([np.linalg.norm(res["dirs"][d][a][l]) for d in doms]))
                    for l in range(nL)]
        for b in CLASSES[i + 1:]:
            cos_cross["%s/%s" % (a, b)] = [
                float(np.mean([float(np.dot(unit(res["dirs"][d][a])[l], unit(res["dirs"][d][b])[l]))
                               for d in doms])) for l in range(nL)]
    norms["bomb_specific"] = [float(np.mean([np.linalg.norm(res["dirs"][d]["bomb_specific"][l])
                                             for d in doms])) for l in range(nL)]
    for nm in (TARGET, "bomb_specific"):
        cs = []
        for l in range(nL):
            U = np.stack([unit(res["dirs"][d][nm])[l] for d in doms])
            G = U @ U.T
            cs.append(float(np.mean(G[np.triu_indices(len(doms), 1)])))
        stab[nm] = cs
    return {"mean_norm": norms, "mean_cosine_between_concept_directions": cos_cross,
            "mean_cosine_between_train_folds": stab,
            "note": "descriptive; no p-value attached"}


# ================================================================================ printing
def _fmt(x, nd=4):
    return "  n/a " if x is None else ("%.*f" % (nd, x))


def report(R):
    P = print
    P("=" * 100)
    P("DCS PHASE 3 §9 — DIFFERENCE-IN-MEANS DIRECTIONS  (v_c = mean[h(C_f)] - mean[h(A_f)], PAIRED)")
    P("=" * 100)
    P("Independence unit: DOMAIN, n = %d.  EXACT two-sided sign-test floor = 2/2^%d = %.5f"
      % (N_DOMAINS, N_DOMAINS, SIGN_FLOOR))
    P("⛔ STATED BEFORE ANY p: only 6/6 or 0/6 domains can clear alpha=0.05.  5/6 gives p=0.21875.")
    P("⛔ Holm with m>=2 would have floor %.5f > 0.05 => UNINFORMATIVE BY CONSTRUCTION."
      % (2 * SIGN_FLOOR))
    P("⇒ EXACTLY ONE PRIMARY TEST IS DECLARED; everything else below is DESCRIPTIVE, NO p-value.")
    P("")
    P("PRIMARY: %s" % PRIMARY_NAME)
    P("")

    for arm_name in R["arms_order"]:
        A = R["arms"][arm_name]
        P("-" * 100)
        P("ARM %s   layers %s   domains %s" % (arm_name, A["layers"], A["domains"]))
        P("   population (per class): cell A = %s, cell C = %s, paired families = %s"
          % (A["counts"]["A"], A["counts"]["C"], A["counts"]["paired"]))
        P("   cache binding q95 rel-err vs each run's OWN hnorm|L* (tol %.0e): %s"
          % (HNORM_TOL, ", ".join("%s %.2e" % (c, A["bind"][c]) for c in CLASSES)))
        if A["bind_fail"]:
            P("   ⛔ BIND FAIL for %s — a class's states may come from another bank." % A["bind_fail"])
        P("")
        P("   [DESCRIPTIVE] held-out C vs A on each concept's OWN direction v_c, band-mean L6-14")
        P("     %-8s %-10s %-10s %-10s" % ("class", "AUROC", "Cohen d", "domains>0.5"))
        for cc in CLASSES:
            per = A["own"][cc]
            P("     %-8s %-10s %-10s %d/%d" % (cc, _fmt(per["mean_auroc"]), _fmt(per["mean_d"], 3),
                                               per["n_above"], per["n_dom"]))
        P("")
        P("   [DESCRIPTIVE] projections on v_bomb  (z-units of the TRAIN cell-A pooled spread)")
        P("     mean z: C_bomb %s   A_bomb %s   C_knife %s   C_gun %s   C_club %s"
          % tuple(_fmt(A["vbomb"]["mean_z"][k], 3) for k in
                  ("C_bomb", "A_bomb", "C_knife", "C_gun", "C_club")))
        P("     C_bomb vs A_bomb : AUROC %s  Cohen d %s  domains>0.5 %d/%d"
          % (_fmt(A["vbomb"]["auroc_CvA"]), _fmt(A["vbomb"]["d_CvA"], 3),
             A["vbomb"]["n_above_CvA"], A["vbomb"]["n_dom"]))
        P("     HARD NEGATIVES — C_bomb vs pooled C_{knife,gun,club}: AUROC %s  d %s  domains>0.5 %d/%d"
          % (_fmt(A["vbomb"]["auroc_vs_negC"]), _fmt(A["vbomb"]["d_vs_negC"], 3),
             A["vbomb"]["n_above_negC"], A["vbomb"]["n_dom"]))
        for c in HARDNEG:
            P("        vs C_%-6s AUROC %s" % (c, _fmt(A["vbomb"]["auroc_vs_%s" % c])))
        P("")
        P("   [DESCRIPTIVE] projections on v_bomb_specific = v_bomb - mean(v_knife,v_gun,v_club)")
        P("     mean z: C_bomb %s   A_bomb %s   C_knife %s   C_gun %s   C_club %s"
          % tuple(_fmt(A["vspec"]["mean_z"][k], 3) for k in
                  ("C_bomb", "A_bomb", "C_knife", "C_gun", "C_club")))
        P("     C_bomb vs A_bomb : AUROC %s  Cohen d %s  domains>0.5 %d/%d"
          % (_fmt(A["vspec"]["auroc_CvA"]), _fmt(A["vspec"]["d_CvA"], 3),
             A["vspec"]["n_above_CvA"], A["vspec"]["n_dom"]))
        P("     HARD NEGATIVES — C_bomb vs pooled C_{knife,gun,club}: AUROC %s  d %s  domains>0.5 %d/%d"
          % (_fmt(A["vspec"]["auroc_vs_negC"]), _fmt(A["vspec"]["d_vs_negC"], 3),
             A["vspec"]["n_above_negC"], A["vspec"]["n_dom"]))
        for c in HARDNEG:
            P("        vs C_%-6s AUROC %s" % (c, _fmt(A["vspec"]["auroc_vs_%s" % c])))
        P("")
        ba = A["bomb_absent_knife_vs_club"]
        P("   [DESCRIPTIVE] BOMB-ABSENT control — v_knife - v_club, held-out C_knife vs C_club")
        P("     (bomb appears in NO term of this direction, so a strength axis anchored on bomb")
        P("      cannot produce it; the direction analogue of §23.5 clause 4 / R-089)")
        P("     AUROC %s   Cohen d %s   domains>0.5 %d/%d   per-domain %s"
          % (_fmt(ba["mean_auroc"]), _fmt(ba["mean_d"], 3), ba["n_above"], ba["n_dom"],
             " ".join(_fmt(ba["per_domain"][d], 3) for d in sorted(ba["per_domain"]))))
        P("")
        P("   [DESCRIPTIVE] per-layer band profile, v_bomb_specific, C_bomb vs pooled C_negatives")
        P("     layer  " + " ".join("%6d" % l for l in A["layers"]))
        P("     AUROC  " + " ".join("%6s" % _fmt(x, 3) for x in A["vspec"]["auroc_vs_negC_by_layer"]))
        P("")

    # ---- the one primary
    pr = R["primary"]
    P("=" * 100)
    P("⛔ PRIMARY TEST — the ONLY p-value in this file")
    P("=" * 100)
    P("   %s" % pr["name"])
    P("   attainable floor (stated before the p): %.5f" % SIGN_FLOOR)
    for d in sorted(pr["per_domain_band_auroc"]):
        a = pr["per_domain_band_auroc"][d]
        P("     %-14s band-mean AUROC %s   delta %s   %s"
          % (d, _fmt(a), _fmt(None if a is None else a - 0.5),
             "+" if (a is not None and a > 0.5) else "-"))
    P("   mean band AUROC over domains : %s" % _fmt(pr["mean_band_auroc"]))
    P("   domains with AUROC > 0.5     : %d / %d" % (pr["n_positive"], pr["n_domains"]))
    P("   EXACT TWO-SIDED SIGN TEST p  : %s   (floor %s)"
      % (_fmt(pr["p_two_sided_sign"], 5), _fmt(pr["attainable_floor"], 5)))
    P("   VERDICT                      : %s" % R["verdict"])
    P("")

    # ---- n_examples = 0 null
    P("-" * 100)
    P("[CONTROL] n_examples = 0 NULL — at zero demonstrations A and C are the SAME PROMPT")
    n0 = R["n0"]
    P("   bank check: A vs C identical full_prompt per class: %s"
      % ", ".join("%s %d/%d" % (r["class"], r["identical"], r["n"])
                  for r in n0["prompt_identity"]["A_vs_C_same_bank"]))
    P("   bank check: C_bomb vs C_knife identical full_prompt: %d/%d"
      % (n0["prompt_identity"]["C_bomb_vs_C_knife"]["identical"],
         n0["prompt_identity"]["C_bomb_vs_C_knife"]["n"]))
    if n0.get("skipped"):
        P("   ⛔ SKIPPED: %s" % n0["skipped"])
    else:
        P("   ||v_bomb||          band-mean: %s   (vs %s at n_examples in {4,8}) -> ratio %s"
          % (_fmt(n0["norm_vbomb"], 3), _fmt(n0["norm_vbomb_ref"], 3), _fmt(n0["ratio_vbomb"], 5)))
        P("   ||v_bomb_specific|| band-mean: %s   (vs %s at n_examples in {4,8}) -> ratio %s"
          % (_fmt(n0["norm_vspec"], 3), _fmt(n0["norm_vspec_ref"], 3), _fmt(n0["ratio_vspec"], 5)))
        P("   held-out AUROC C_bomb vs A_bomb        on v_bomb          : %s" % _fmt(n0["auroc_CvA"]))
        P("   held-out AUROC C_bomb vs pooled C_negs on v_bomb_specific : %s  (%d/%d domains > 0.5)"
          % (_fmt(n0["auroc_vs_negC"]), n0["n_above_negC"], n0["n_dom"]))
        P("   ⇒ %s" % n0["reading"])
    P("")

    # ---- lexical transfer
    P("-" * 100)
    P("[DESCRIPTIVE — NO p] LEXICAL TRANSFER: directions fitted on `button` only, scored on `basket`")
    if R.get("transfer"):
        for k in ("T1_fit_all_button_domains", "T2_fit_button_minus_d_score_basket_d"):
            t = R["transfer"][k]
            P("   %s" % k)
            P("     v_bomb_specific, C_bomb vs pooled C_negs : mean band AUROC %s   per-domain %s"
              % (_fmt(t["mean_band_auroc_spec_bomb_vs_negC"]),
                 " ".join(_fmt(t["per_domain_band_auroc_spec_bomb_vs_negC"][d], 3)
                          for d in sorted(t["per_domain_band_auroc_spec_bomb_vs_negC"]))))
            P("     v_bomb,          C_bomb vs A_bomb        : mean band AUROC %s   per-domain %s"
              % (_fmt(t["mean_band_auroc_vbomb_C_vs_A"]),
                 " ".join(_fmt(t["per_domain_band_auroc_vbomb_C_vs_A"][d], 3)
                          for d in sorted(t["per_domain_band_auroc_vbomb_C_vs_A"]))))
    else:
        P("   not run (basket arm not loaded)")
    P("")

    # ---- geometry
    P("-" * 100)
    P("[DESCRIPTIVE — NO p] GEOMETRY of the directions themselves (button arm, band-mean)")
    g = R["arms"][R["arms_order"][0]]["geometry"]
    P("   mean ||v||: " + "  ".join("%s %s" % (k, _fmt(band(v), 2))
                                    for k, v in g["mean_norm"].items()))
    P("   mean cos(v_a, v_b) between concept directions:")
    for k, v in g["mean_cosine_between_concept_directions"].items():
        P("       %-14s %s" % (k, _fmt(band(v), 3)))
    P("   mean cos between the 6 train folds' own estimate: v_bomb %s   v_bomb_specific %s"
      % (_fmt(band(g["mean_cosine_between_train_folds"][TARGET]), 3),
         _fmt(band(g["mean_cosine_between_train_folds"]["bomb_specific"]), 3)))
    P("")

    # ---- limitations
    P("=" * 100)
    P("⛔ LIMITATIONS — measured, not asserted")
    P("=" * 100)
    P("1. §46.1 / C-060: cell `A` is NOT always a different corpus across banks, and v_c SUBTRACTS")
    P("   cell `A`, so this matters for v_bomb_specific. Measured on the EXACT paired families used:")
    for arm_name in R["arms_order"]:
        for row in R["arms"][arm_name]["cellA_overlap"]:
            P("     %-7s %-12s common %3d  byte-identical full_prompt %3d (%s)  demo_block %3d"
              % (arm_name, row["pair"], row["n_common_families"], row["identical_full_prompt"],
                 _fmt(row["frac_identical_prompt"], 3), row["identical_demo_block"]))
    P("   Reading: on the identical families the cell-A term CANCELS exactly inside v_bomb - v_c',")
    P("   which HELPS; on the remaining families a benign-corpus difference survives as a NUISANCE")
    P("   term inside v_bomb_specific. This instrument cannot separate the two, and the overlap")
    P("   fraction above is the size of the part that is clean by construction.")
    P("2. n = 6 domains. The sign-test floor is 0.03125 and there is no way to buy more domains;")
    P("   the concept-backed population is the whole population (§6.2).")
    P("3. ONE model, ONE codeword for the primary (`button`), ONE band (L6-14), ONE channel")
    P("   (`semantic_one_word`), doses {4, 8}. `basket` is a lexical replication, not a new sample.")
    P("4. §46.2 / C-060: cells B/E share demonstration blocks between button_X and basket_X. This")
    P("   instrument uses cells A/C (modally distinct), but the two arms are still not independent.")
    P("5. §46.3 / C-060: R-078's installation gate PASSES 6 bank x domain x dose cells whose cell-C")
    P("   mean log-odds is still NEGATIVE (gun and knife on farm_storage / lab_safety). A paired")
    P("   improvement is not an installed mapping, and those rows are inside cell C here too.")
    P("6. ⛔ REMAPPING STRENGTH IS NOT FULLY CONTROLLED. R-078 measured very different installation")
    P("   strengths (club +6.435, knife +4.089) and `gun` DOES NOT INSTALL at all, while")
    P("   v_bomb_specific subtracts a MEAN over three concepts of unequal strength. The bomb-absent")
    P("   knife-vs-club row above is the only control here that a bomb-anchored strength axis cannot")
    P("   explain; the pooled-negative PRIMARY is NOT immune to a strength component and this")
    P("   instrument cannot decompose it. ⚠ The per-negative breakdown (vs gun / knife / club) is")
    P("   reported for exactly that reason: if the effect were pure strength it should track")
    P("   R-078's ordering.")
    P("7. ⛔ A DIRECTION IS NOT A CAUSE. This is the same decodability class of evidence as R-086")
    P("   (§54.3): gate R5 -- does the demonstration->query knockout destroy it? -- is NOT RUN.")
    P("8. This instrument is strictly WEAKER than PR-035's fitted probe (rank-1, no covariance).")
    P("   A null here would NOT contradict R-086's 0.7485; it would bound how much of the signal")
    P("   lives on a single label-free axis.")
    P("=" * 100)


# ================================================================================ orchestration
def _summarise_arm(bundle, res):
    layers = bundle["layers"]
    folds = res["folds"]
    doms = sorted(folds)

    def agg(dname, key):
        return _m([band(folds[d][dname][key]) for d in doms])

    def above(dname, key, thr=0.5):
        return sum(1 for d in doms
                   if (band(folds[d][dname][key]) is not None and band(folds[d][dname][key]) > thr))

    out = {"layers": layers, "domains": bundle["domains"], "bind": bundle["bind"],
           "runs": bundle["runs"],
           "bind_fail": [c for c in CLASSES
                         if bundle["bind"].get(c) is None or bundle["bind"][c] > HNORM_TOL],
           "counts": {"A": {c: int(bundle["arm"][(c, "A")]["X"].shape[0]) for c in CLASSES},
                      "C": {c: int(bundle["arm"][(c, "C")]["X"].shape[0]) for c in CLASSES},
                      "paired": {c: int(res["pidx"][c][0].size) for c in CLASSES}},
           "own": {}, "geometry": geometry(res, layers), "per_domain": {}}
    for cc in CLASSES:
        out["own"][cc] = {
            "mean_auroc": _m([band(folds[d]["own_direction_C_vs_A"][cc]["auroc"]) for d in doms]),
            "mean_d": _m([band(folds[d]["own_direction_C_vs_A"][cc]["d"]) for d in doms]),
            "n_above": sum(1 for d in doms
                           if (band(folds[d]["own_direction_C_vs_A"][cc]["auroc"]) or 0) > 0.5),
            "n_dom": len(doms)}
    for tag, dname in (("vbomb", TARGET), ("vspec", "bomb_specific")):
        rec = {"n_dom": len(doms),
               "mean_z": {k: _m([band(folds[d][dname]["mean_proj"][k]) for d in doms])
                          for k in ("C_bomb", "A_bomb", "C_knife", "C_gun", "C_club")},
               "auroc_CvA": agg(dname, "auroc_Cbomb_vs_Abomb"),
               "d_CvA": agg(dname, "d_Cbomb_vs_Abomb"),
               "n_above_CvA": above(dname, "auroc_Cbomb_vs_Abomb"),
               "auroc_vs_negC": agg(dname, "auroc_Cbomb_vs_negC"),
               "d_vs_negC": agg(dname, "d_Cbomb_vs_negC"),
               "n_above_negC": above(dname, "auroc_Cbomb_vs_negC"),
               "auroc_vs_negC_by_layer": [
                   _m([folds[d][dname]["auroc_Cbomb_vs_negC"][l] for d in doms])
                   for l in range(len(layers))]}
        for c in HARDNEG:
            rec["auroc_vs_%s" % c] = agg(dname, "auroc_Cbomb_vs_C%s" % c)
        out[tag] = rec
    out["bomb_absent_knife_vs_club"] = {
        "mean_auroc": _m([band(folds[d]["bomb_absent_knife_vs_club"]["auroc"]) for d in doms]),
        "mean_d": _m([band(folds[d]["bomb_absent_knife_vs_club"]["d"]) for d in doms]),
        "n_above": sum(1 for d in doms
                       if (band(folds[d]["bomb_absent_knife_vs_club"]["auroc"]) or 0) > 0.5),
        "n_dom": len(doms),
        "per_domain": {d: band(folds[d]["bomb_absent_knife_vs_club"]["auroc"]) for d in doms}}
    out["per_domain"] = {d: {
        "band_auroc_vspec_bomb_vs_negC": band(folds[d]["bomb_specific"]["auroc_Cbomb_vs_negC"]),
        "band_auroc_vbomb_bomb_vs_negC": band(folds[d][TARGET]["auroc_Cbomb_vs_negC"]),
        "band_auroc_vbomb_C_vs_A": band(folds[d][TARGET]["auroc_Cbomb_vs_Abomb"]),
        "band_d_vbomb_C_vs_A": band(folds[d][TARGET]["d_Cbomb_vs_Abomb"]),
        "band_auroc_vspec_C_vs_A": band(folds[d]["bomb_specific"]["auroc_Cbomb_vs_Abomb"]),
        "n_train_pairs": folds[d]["n_train_pairs"]} for d in doms}
    return out


def run_null_n0(codeword, ref_arm_summary, verbose=True):
    """n_examples = 0 blocking null, same instrument, same LODO discipline."""
    ident = n0_prompt_identity(codeword)
    try:
        b0 = load_arm(codeword, nex=(0,), verbose=verbose)
    except SystemExit as e:
        return {"prompt_identity": ident, "skipped": str(e)}
    res0 = lodo(b0)
    if not res0["folds"]:
        return {"prompt_identity": ident, "skipped": "no usable folds at n_examples=0"}
    doms = sorted(res0["folds"])
    g0 = geometry(res0, b0["layers"])
    nb = band(g0["mean_norm"][TARGET])
    ns = band(g0["mean_norm"]["bomb_specific"])
    rb = band(ref_arm_summary["geometry"]["mean_norm"][TARGET])
    rs = band(ref_arm_summary["geometry"]["mean_norm"]["bomb_specific"])
    a_cva = _m([band(res0["folds"][d][TARGET]["auroc_Cbomb_vs_Abomb"]) for d in doms])
    a_neg = _m([band(res0["folds"][d]["bomb_specific"]["auroc_Cbomb_vs_negC"]) for d in doms])
    n_ab = sum(1 for d in doms
               if (band(res0["folds"][d]["bomb_specific"]["auroc_Cbomb_vs_negC"]) or 0) > 0.5)
    near0 = (rs and ns is not None and (ns / rs) < 0.10)
    near_chance = a_neg is not None and abs(a_neg - 0.5) < 0.10
    reading = ("NULL PASSES: at zero demonstrations the direction is ~0 and the hard-negative "
               "separation is at chance, so the instrument is not reading the §28.1 exclusion, the "
               "bank identity, or the template."
               if (near0 and near_chance) else
               "⛔ NULL DOES NOT PASS as expected — the direction is NOT near zero and/or the "
               "hard-negative AUROC is not at chance at n_examples=0. Any positive result above is "
               "VOID by the same rule that voided PR-031 (C-049).")
    return {"prompt_identity": ident, "domains": doms,
            "norm_vbomb": nb, "norm_vspec": ns, "norm_vbomb_ref": rb, "norm_vspec_ref": rs,
            "ratio_vbomb": (nb / rb) if (nb is not None and rb) else None,
            "ratio_vspec": (ns / rs) if (ns is not None and rs) else None,
            "auroc_CvA": a_cva, "auroc_vs_negC": a_neg, "n_above_negC": n_ab, "n_dom": len(doms),
            "reading": reading, "null_passes": bool(near0 and near_chance)}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--repo-root", default=os.path.dirname(_HERE))
    ap.add_argument("--arms", default="button,basket",
                    help="codeword arms to load; the PRIMARY is always `button`")
    ap.add_argument("--out", default=None, help="optional JSON path (nothing is written otherwise)")
    ap.add_argument("--skip-null", action="store_true", help="skip the n_examples=0 blocking null")
    ap.add_argument("--self-test", action="store_true",
                    help="run the synthetic planted-direction self-test and exit")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args(argv)

    if args.self_test:
        return self_test()

    os.chdir(args.repo_root)
    arms = [a.strip() for a in args.arms.split(",") if a.strip()]
    if "button" not in arms:
        raise SystemExit("the PRIMARY is defined on the `button` arm; it must be included")

    print("repo root: %s" % os.getcwd())
    print("loading arms %s (this reads one ~200 MB rep cache per class, 4 per arm)" % arms)
    bundles, results, summaries = {}, {}, {}
    for a in arms:
        bundles[a] = load_arm(a, verbose=not args.quiet)
        results[a] = lodo(bundles[a])
        summaries[a] = _summarise_arm(bundles[a], results[a])
        summaries[a]["cellA_overlap"] = cellA_overlap(a)

    pr = primary(results["button"])
    if pr["p_two_sided_sign"] is None:
        verdict = "CANNOT ANSWER — no usable domains"
    elif pr["p_two_sided_sign"] <= 0.05 and pr["n_positive"] > pr["n_negative"]:
        verdict = ("POSITIVE (direction instrument) — v_bomb_specific separates held-out C_bomb "
                   "from the pooled hard negatives in %d/%d domains, p = %.5f (floor %.5f)"
                   % (pr["n_positive"], pr["n_domains"], pr["p_two_sided_sign"], SIGN_FLOOR))
    elif pr["p_two_sided_sign"] <= 0.05:
        verdict = ("⛔ POSITIVE IN THE WRONG DIRECTION — %d/%d domains BELOW 0.5, p = %.5f"
                   % (pr["n_negative"], pr["n_domains"], pr["p_two_sided_sign"]))
    else:
        verdict = ("NULL at the declared primary — %d/%d domains above 0.5, p = %.5f; with n=6 the "
                   "floor is %.5f so this is a genuine non-rejection, NOT evidence of absence"
                   % (pr["n_positive"], pr["n_domains"], pr["p_two_sided_sign"], SIGN_FLOOR))

    R = {"arms_order": arms, "arms": summaries, "primary": pr, "verdict": verdict,
         "declared": {"primary": PRIMARY_NAME, "attainable_floor": SIGN_FLOOR,
                      "n_domains": N_DOMAINS, "layers": list(LAYERS),
                      "n_examples": list(NEXAMPLES), "query_kind": CHANNEL,
                      "everything_else": "DESCRIPTIVE, no p-value (Holm m>=2 floor 0.0625 > 0.05)"}}
    R["n0"] = ({"prompt_identity": n0_prompt_identity("button"), "skipped": "--skip-null"}
               if args.skip_null else run_null_n0("button", summaries["button"],
                                                  verbose=not args.quiet))
    if "basket" in arms:
        R["transfer"] = transfer(bundles["button"], bundles["basket"], bundles["button"]["layers"])

    print("")
    report(R)
    if args.out:
        with open(args.out, "w") as fh:
            json.dump(R, fh, indent=2, default=str)
        print("wrote %s" % os.path.abspath(args.out))
    return 0


# ================================================================================== self-test
def _synth(planted, seed, H=96, n_fam=28, n_dom=N_DOMAINS, nL=3, sig=4.0, shared=3.0, noise=1.0):
    """Synthetic arm with a PLANTED per-concept direction.

    Every class gets its own per-family benign base (mimicking §8.1 / C-060: cell A is *modally* a
    different corpus per bank), a LARGE shared remapping component that all four concepts share, and
    -- when `planted` -- a concept-specific component on a class-specific orthonormal axis. A correct
    implementation must (a) recover the planted axis via the paired C-A difference, and (b) find
    v_bomb_specific ~ 0 and chance AUROC when `planted` is False, because then the four classes
    differ by NOTHING but noise."""
    rng = np.random.default_rng(seed)
    Q = np.linalg.qr(rng.normal(size=(H, len(CLASSES) + 1)))[0]
    u = {c: Q[:, i] for i, c in enumerate(CLASSES)}
    w = Q[:, len(CLASSES)]
    doms = ["dom%d" % i for i in range(n_dom)]
    arm = {}
    for cc in CLASSES:
        rA, rC = [], []
        for d in doms:
            for f in range(n_fam):
                fam = "%s|%d" % (d, f)
                base = rng.normal(size=(nL, H)) * 2.0
                hA = base + rng.normal(size=(nL, H)) * noise
                hC = base + shared * w[None, :] + rng.normal(size=(nL, H)) * noise
                if planted:
                    hC = hC + sig * u[cc][None, :]
                rA.append({"domain": d, "family_id": fam, "_vec": hA.astype(np.float32)})
                rC.append({"domain": d, "family_id": fam, "_vec": hC.astype(np.float32)})
        arm[(cc, "A")] = _pack(rA, list(range(nL)))
        arm[(cc, "C")] = _pack(rC, list(range(nL)))
    return {"arm": arm, "layers": list(range(nL)), "bind": {c: 0.0 for c in CLASSES},
            "runs": {c: "synthetic" for c in CLASSES}, "domains": doms}


def self_test():
    print("=" * 100)
    print("SELF-TEST — synthetic data with a planted per-concept direction")
    print("=" * 100)
    print("floor stated first: exact two-sided sign test on n=%d domains has floor %.5f"
          % (N_DOMAINS, SIGN_FLOOR))
    ok = True

    # --- A. planted signal: the primary MUST fire at 6/6 and at the floor.
    b = _synth(planted=True, seed=20260906)
    res = lodo(b)
    pr = primary(res)
    s = _summarise_arm(b, res)
    print("\n[A] PLANTED concept direction (sig=4.0 on an axis orthogonal to the shared remap)")
    print("    per-domain band AUROC (C_bomb vs pooled C_negs on v_bomb_specific):")
    for d in sorted(pr["per_domain_band_auroc"]):
        print("       %-8s %s" % (d, _fmt(pr["per_domain_band_auroc"][d])))
    print("    domains > 0.5 : %d/%d      sign-test p = %s (floor %.5f)"
          % (pr["n_positive"], pr["n_domains"], _fmt(pr["p_two_sided_sign"], 5), SIGN_FLOOR))
    print("    v_bomb C vs A : AUROC %s   v_bomb_specific C_bomb vs negs AUROC %s"
          % (_fmt(s["vbomb"]["auroc_CvA"]), _fmt(s["vspec"]["auroc_vs_negC"])))
    print("    mean cos(v_a,v_b) between concept directions: %s   (planted axes are orthogonal;"
          " the large SHARED remap makes the raw cosines high, which is the point of residualising)"
          % _fmt(_m([band(v) for v in
                     s["geometry"]["mean_cosine_between_concept_directions"].values()]), 3))
    if not (pr["n_positive"] == N_DOMAINS and abs(pr["p_two_sided_sign"] - SIGN_FLOOR) < 1e-12):
        print("    ⛔ FAIL: the planted direction was not recovered at 6/6 / the floor.")
        ok = False
    elif (s["vspec"]["auroc_vs_negC"] or 0) < 0.90:
        print("    ⛔ FAIL: planted separation recovered but weak (<0.90).")
        ok = False
    else:
        print("    ✅ PASS: planted direction recovered, 6/6 domains, p at the attainable floor.")

    # --- B. shared remap ONLY (no concept-specific component): v_bomb_specific must be ~0 and the
    #        primary must not systematically fire. 20 independent replicates = a small calibration.
    N_REP = 50
    print("\n[B] NULL — shared remap only, NO concept-specific component (%d replicates)" % N_REP)
    fires, aurocs, ratios = 0, [], []
    for k in range(N_REP):
        bn = _synth(planted=False, seed=1000 + k)
        rn = lodo(bn)
        pn = primary(rn)
        sn = _summarise_arm(bn, rn)
        aurocs.append(sn["vspec"]["auroc_vs_negC"])
        nb = band(sn["geometry"]["mean_norm"][TARGET])
        ns = band(sn["geometry"]["mean_norm"]["bomb_specific"])
        ratios.append(ns / nb if nb else None)
        if pn["p_two_sided_sign"] is not None and pn["p_two_sided_sign"] <= 0.05:
            fires += 1
    fpr = fires / float(N_REP)
    print("    mean band AUROC (C_bomb vs pooled C_negs on v_bomb_specific) : %s  (chance 0.5)"
          % _fmt(_m(aurocs)))
    print("    mean ||v_bomb_specific|| / ||v_bomb||                        : %s  (descriptive: the"
          " residual here is pure estimation noise, so this ratio is a NOISE FLOOR, not 0)" % _fmt(_m(ratios), 3))
    print("    replicates where the PRIMARY rejects at alpha=0.05           : %d/%d  (FPR %.3f;"
          " the test can only ever reject at p=%.5f, so the expected rate is %.4f)"
          % (fires, N_REP, fpr, SIGN_FLOOR, SIGN_FLOOR))
    if abs((_m(aurocs) or 0) - 0.5) > 0.10:
        print("    ⛔ FAIL: null AUROC is not near chance.")
        ok = False
    elif fpr > 0.25:
        print("    ⛔ FAIL: the primary rejects far too often on data with no concept signal.")
        ok = False
    else:
        print("    ✅ PASS: no concept signal => direction ~0, AUROC ~chance, primary does not fire.")

    # --- C. train/test discipline: a direction fitted on TRAIN only must not know the held-out rows.
    print("\n[C] LEAKAGE GUARD — refit the primary with the held-out domain PUT BACK into the fit")
    b2 = _synth(planted=True, seed=777)
    pidx = paired_index(b2["arm"])
    leak = []
    for d in b2["domains"]:
        v_all, _ = directions(b2["arm"], pidx, b2["domains"])          # <- includes d: WRONG on purpose
        f = eval_fold(b2["arm"], v_all, b2["domains"], [d], b2["layers"])
        leak.append(band(f["bomb_specific"]["auroc_Cbomb_vs_negC"]))
    res2 = lodo(b2)
    honest = [band(res2["folds"][d]["bomb_specific"]["auroc_Cbomb_vs_negC"]) for d in b2["domains"]]
    print("    honest (train = other 5 domains) mean band AUROC : %s" % _fmt(_m(honest)))
    print("    leaky  (train includes the test domain)          : %s" % _fmt(_m(leak)))
    print("    ⇒ the two differ by %s; the reported pipeline uses the HONEST one by construction"
          % _fmt(abs((_m(leak) or 0) - (_m(honest) or 0)), 4))
    if _m(leak) is None or _m(honest) is None:
        print("    ⛔ FAIL: leakage guard did not produce numbers.")
        ok = False
    else:
        print("    ✅ PASS: both paths run; lodo() never passes the test domain to directions().")

    print("\n" + "=" * 100)
    print("SELF-TEST %s" % ("PASS" if ok else "⛔ FAIL"))
    print("=" * 100)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
