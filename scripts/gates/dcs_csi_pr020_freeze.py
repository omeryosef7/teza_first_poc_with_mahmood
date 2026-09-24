#!/usr/bin/env python
"""Freeze PR-CSI-020 -- the per-CELL census of EIGHT live BASKET heads that have never been censused.

WHY THIS FAMILY EXISTS. D37 is the basket cell-census result and the claim table records it as
"VALIDATION, DESCRIPTIVE. RUNG 1. No rank, no p, no control family." D39 (PR-CSI-018) carries this
sprint's ONLY preregistered p and it is on BUTTON. This family gives the ORIGINAL codeword what
button already has.

⚠ AND IT IS A WEAKER HELD-OUT CLAIM THAN PR-CSI-018's, IN ONE DIMENSION. PR-CSI-018 took a
basket-TRAIN screen and predicted BUTTON cells -- held out on split AND codeword. This takes the
same basket-TRAIN screen and predicts BASKET validation cells: held out on SPLIT ONLY. That is
stated here, in the prereg, so D39's stronger framing cannot carry over by association.

HOW THE EIGHT WERE CHOSEN, and every step used NO basket CELL data:
  * LIVE on basket validation by the S-311 rule applied to PR-CSI-012's published SINGLE_<h> arms
    (|E| >= 1.5 x bar AND ci95 excluding 0) -- a WHOLE-HEAD property.
  * NOT already cell-censused: heads 2 (PR-CSI-014) and 17, 19, 23 (PR-CSI-015) are EXCLUDED.
    Counting a known outcome as a fresh draw is selection on data already read -- the same reason
    PR-CSI-018 excluded 17/19/23 on button.
  * The obvious candidate set -- the four never-censused heads of the screen's TOP-8 (6, 13, 24, 28)
    -- CANNOT CERTIFY EVER: heads 13 and 24 both predict L10, giving 12 distinct assignments and a
    permutation floor of 0.0833 > alpha (S-347). Widening the pool beyond the top-8 is what makes a
    viable family exist, and that widening was done BEFORE any cell of these heads was measured.

TWO COMPOSITION FACTS THAT ARE FROZEN HERE RATHER THAN DISCOVERED LATER:
  * HEADS 6, 11 AND 27 had these SAME predictions tested on BUTTON by PR-CSI-018, and ALL THREE
    MATCHED. Testing them on basket validation is a REPLICATION on a different population, not an
    independent draw. The family certifies WITHOUT them (the five never-tested heads give 120
    assignments, floor 0.008333), so a SECONDARY over those five is preregistered alongside.
  * HEAD 18 PREDICTS L14, the band-edge rival. PR-CSI-018 excluded head 16 for exactly this, and
    that was right THERE, where a small set could not be told from top-of-band bias. Here the eight
    predictions span SIX distinct layers, so the spanning rule and the permutation p both bite.
    Head 18 is INCLUDED, and the rule that includes it is frozen before the cells are measured;
    dropping it after seeing the composition would be post-hoc selection.

POWER, by a SEEDED MONTE CARLO under a named model (S-354). The first freeze used exact
enumeration over match patterns, which is valid only if p depends on M alone -- true of the
statistic that freeze used, FALSE of the reader's. S-353 showed no rule in M and M_unique alone
characterises certification, so only NECESSARY conditions are frozen, never a complete table.

WARNING -- THIS IS THE SECOND FREEZE. The first, md5 9fce4bda, was DEFECTIVE and never ran:
review R32 found the census would refuse it outright, two required keys missing and with them the
estimator definition; the launcher had no tag for it; its permutation statistic was not the
reader's; and five VOID conditions PR-CSI-018 carried had been dropped. Nothing was measured
under it.
"""
import argparse, hashlib, json, os, sys
import collections, itertools
from math import comb, factorial

import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DOSE_UNIT = 2016
BAND = [6, 7, 8, 9, 10, 11, 12, 13, 14]
HEADS = [4, 6, 10, 11, 13, 18, 21, 27]
ALREADY_CELL_MAPPED_ON_BASKET = [2, 17, 19, 23]      # PR-CSI-014 and PR-CSI-015
PREDICTION_TESTED_ON_BUTTON = [6, 11, 27]            # PR-CSI-018; all three MATCHED there
SCREEN_ARTIFACT = "outputs/boombness/dcs_csi/w1_screen_train_basket_916132.json"
PR012_PREREG = "configs/dcs_csi_pr012_head_census_basket.json"
PR012_REPORT = "reports/DCS_CSI_PR012_CENSUS_validation.json"
ALPHA = 0.05
ADMIT_RATIO = 1.5
MC_N = 200000              # S-354: the power Monte Carlo, N and seed FROZEN into the prereg
MC_SEED = 20260924
Z = 1.96
P0 = 1.0 / len(BAND)


def md5(path):
    return hashlib.md5(open(os.path.join(REPO, path), "rb").read()).hexdigest()


def screen_predictions():
    """Each head's screen argmax layer and margin, RE-DERIVED from the artefact, never hardcoded."""
    scr = json.load(open(os.path.join(REPO, SCREEN_ARTIFACT)))
    if scr.get("split") != "train" or scr.get("codeword") != "basket":
        sys.exit("REFUSING: screen is %r/%r; this family requires train/basket."
                 % (scr.get("split"), scr.get("codeword")))
    if sorted(scr["band_layers"]) != sorted(BAND):
        sys.exit("REFUSING: screen band %r != this family's %r." % (scr["band_layers"], BAND))
    atp = scr["AtP_by_cell"]
    out = {}
    for h in HEADS:
        vals = {L: abs(atp["%d,%d" % (L, h)]) for L in BAND}
        order = sorted(BAND, key=lambda L: -vals[L])
        out[str(h)] = {"layer": order[0], "margin": vals[order[0]] / vals[order[1]]}
    return out, scr


def pr012_whole_head():
    """PR-CSI-012's measured basket whole-head effects for these heads, DERIVED not hardcoded."""
    rep = json.load(open(os.path.join(REPO, PR012_REPORT)))
    if rep.get("prereg_id") != "PR-CSI-012" or rep.get("split") != "validation":
        sys.exit("REFUSING: %s is %r/%r, not PR-CSI-012/validation."
                 % (PR012_REPORT, rep.get("prereg_id"), rep.get("split")))
    hs = json.load(open(os.path.join(REPO, PR012_PREREG)))["head_sets"]
    a2h = {int(v[0]): a for a, v in hs.items() if isinstance(v, list) and len(v) == 1}
    out = {}
    for h in HEADS:
        arm = a2h.get(h)
        if arm is None or arm not in rep.get("E", {}):
            sys.exit("REFUSING: PR-CSI-012 has no single-head arm for head %d, so its VOID "
                     "reference cannot be derived and this file will not invent one." % h)
        lo, hi = rep["ci95"][arm]
        out[str(h)] = {
            "source_family": "PR-CSI-012", "source_arm": arm,
            "E": rep["E"][arm], "ci95": [lo, hi], "ci95_excludes_0": not (lo < 0 < hi),
            # R29/S-323: the tolerance lives WITH the number the reader compares against.
            "void_tolerance": 1e-6,
            "ENFORCED_BY": "scripts/dcs_csi_head_census.py -- it REFUSES when |diff| exceeds "
                           "void_tolerance. ⚠ S-349: the key is the FAMILY-NEUTRAL "
                           "`whole_head_REFERENCE`; until S-349 the reader looked ONLY for "
                           "`pr013_whole_head_REFERENCE`, so a BASKET family would have had to "
                           "MISNAME PR-012's numbers as PR-013's to be checked at all."}
    return out


def n_assign(layers):
    c = collections.Counter(layers)
    n = factorial(len(layers))
    for v in c.values():
        n //= factorial(v)
    return n


def binom_ge(K, M):
    return 1.0 if K == 0 else sum(comb(K, m) * P0 ** m * (1 - P0) ** (K - m)
                                  for m in range(M, K + 1))


# ⚠⚠ S-352/S-354. THE PERMUTATION STATISTIC IS THE READER'S, COPIED FROM IT.
# The first version of this file compared permutations against the PREDICTION vector; the reader
# (dcs_csi_pr016_argmax_test.py:226-230) compares them against the OBSERVED ARGMAX vector. The two
# coincide only at M = K. R32-A found it; measured on one case, reader 0.000099..0.000595 against
# this file's 0.002679. The reader's is correct -- a permutation test conditions on the observed
# outcome -- and the consequence was that the prereg's decision table described a test the reader
# does not implement: a 4-of-8 outcome would have been published PASS against a prereg recording
# that it could not certify.
#
# SPEED (S-354): positions sharing an observed layer are INTERCHANGEABLE, so the match-count
# distribution depends only on the signature (a_6..a_14). It caches, and 11 995 signatures appeared
# in the power run -- which is why the uncached form could not finish.
_PERM_CACHE = {}


def _perm_matrix(pred, adm):
    key = tuple(pred[h] for h in adm)
    m = _PERM_CACHE.get(("M", key))
    if m is None:
        m = np.array(sorted(set(itertools.permutations(key))), dtype=np.int8)
        _PERM_CACHE[("M", key)] = m
    return m


def perm_tail(pred, adm, obs):
    """P(matches >= m) for every m, matching the READER: permutations of the prediction multiset
    scored against the OBSERVED argmax vector."""
    band_sorted = sorted(set(pred[h] for h in adm) | set(obs))
    sig = (tuple(pred[h] for h in adm), tuple(obs.count(L) for L in band_sorted))
    hit = _PERM_CACHE.get(sig)
    if hit is not None:
        return hit
    rep = []
    for L in band_sorted:
        rep += [L] * obs.count(L)
    P = _perm_matrix(pred, adm)
    matches = (P == np.array(rep, dtype=np.int8)).sum(axis=1)
    counts = np.bincount(matches, minlength=len(adm) + 1)
    tail = np.cumsum(counts[::-1])[::-1] / float(len(P))
    _PERM_CACHE[sig] = tail
    return tail


def certifies(pred, adm, obs):
    """The READER's rule, applied to an observed argmax vector."""
    matched = [adm[i] for i in range(len(adm)) if obs[i] == pred[adm[i]]]
    M = len(matched)
    lay = [pred[h] for h in adm]
    uq = [h for h in adm if lay.count(pred[h]) == 1]
    Mu = sum(1 for h in matched if h in uq)
    if M > 0 and len({pred[h] for h in matched}) < 2:
        return False
    w = max(binom_ge(len(adm), M), binom_ge(len(uq), Mu) if uq else 1.0,
            perm_tail(pred, adm, obs)[M])
    return w <= ALPHA


def power_mc(pred, adm, q, n, seed):
    """P(certify) under the NAMED model: each head matches with probability q independently, and a
    miss lands UNIFORMLY on one of the other 8 band layers. Both halves are assumptions and the
    prereg says so -- S-351 measured that the empirical argmax marginal is NOT uniform."""
    rng = np.random.default_rng(seed)
    alt = [np.array([L for L in BAND if L != pred[h]]) for h in adm]
    hit = 0
    for _ in range(n):
        u = rng.random(len(adm))
        obs = [pred[adm[i]] if u[i] < q else int(rng.choice(alt[i])) for i in range(len(adm))]
        if certifies(pred, adm, obs):
            hit += 1
    return hit / float(n)


def build():
    screen, scr = screen_predictions()
    ref = pr012_whole_head()
    pred = {h: screen[str(h)]["layer"] for h in HEADS}
    fresh = [h for h in HEADS if h not in PREDICTION_TESTED_ON_BUTTON]
    lay_all = [pred[h] for h in HEADS]
    lay_fresh = [pred[h] for h in fresh]
    uq_all = [h for h in HEADS if lay_all.count(pred[h]) == 1]

    cell_sets = {}
    for h in HEADS:
        cell_sets["HD_%d" % h] = [[L, h] for L in BAND]
        for L in BAND:
            cell_sets["BK_H%d_L%02d" % (h, L)] = [[L, h]]
    base_arms = ["BK_BASE", "BK_KO"]
    n_arms = len(cell_sets) + len(base_arms)
    if n_arms != len(HEADS) * (len(BAND) + 1) + 2:
        sys.exit("REFUSING: resolved %d arms, expected %d."
                 % (n_arms, len(HEADS) * (len(BAND) + 1) + 2))

    pr = {
        "id": "PR-CSI-020",
        "title": "Per-CELL census of EIGHT live BASKET heads never previously censused: does the "
                 "basket-TRAIN screen's per-cell prediction hold on basket VALIDATION?",
        "frozen_utc_date": "2026-09-24",
        "EMITTED_MECHANICALLY_BY": "scripts/gates/dcs_csi_pr020_freeze.py",
        "design_ref": "S-347 (viability), S-348 (power), S-349 (the reference key)",
        "split": "validation", "codeword": "basket", "concept": "bomb",
        "statistical_unit": "DOMAIN (PART I 3.1). Rows never inflate n.",
        "endpoint": "y_install via the concept-free semantic_one_word readout, cell C, n_examples 4",
        "heads": HEADS, "band": "6-14", "layers": BAND,
        "base_arms": base_arms, "cell_sets": cell_sets, "n_arms_per_split": n_arms,
        "intervention": {"intervene": "demo_all:attn_knockout:6-14:1.0",
                         "knockout_scope": "target_surface_row_only", "band": "6-14"},
        "arms": {"BK_BASE": "no --intervene; the clean reference",
                 "BK_KO": "--knockout-cells omitted = the all-32 band knockout; the denominator",
                 "HD_<h>": "all nine band cells of head h; the bar source AND the admission arm",
                 "BK_H<h>_L<ll>": "ONE cell; the judged units"},
        "CANDIDATE_PROVENANCE": {
            "nominated_on": "the basket TRAIN screen (LAYER) and PR-CSI-012's basket whole-head "
                            "magnitude (admission ELIGIBILITY). NEITHER uses any basket CELL data.",
            "why_these_eight": "live on basket validation (|E|/bar >= 1.5 on the S-311 rule applied "
                               "to PR-CSI-012's SINGLE_<h> arms, ci95 excluding 0) AND never "
                               "cell-censused",
            "EXCLUDED_already_cell_mapped": {
                "heads": ALREADY_CELL_MAPPED_ON_BASKET,
                "why": "PR-CSI-014 measured head 2's cells and PR-CSI-015 measured 17/19/23's. "
                       "Counting a known outcome as a fresh draw is selection on data already "
                       "read -- the same exclusion PR-CSI-018 applied to 17/19/23 on button."},
            "⚠ WHY_NOT_THE_SCREEN_TOP_8": "the four never-censused heads of the screen's top-8 "
                                          "(6, 13, 24, 28) predict {L9, L10, L10, L11}: heads 13 "
                                          "and 24 COLLIDE on L10, giving 12 distinct assignments "
                                          "and a permutation floor of 0.0833 > alpha. THAT FAMILY "
                                          "COULD NOT CERTIFY ON ANY OUTCOME (S-347). The pool was "
                                          "widened before any cell of any head here was measured.",
            "⚠ PREDICTION_ALREADY_TESTED_ON_BUTTON": {
                "heads": PREDICTION_TESTED_ON_BUTTON,
                "outcome_there": "ALL THREE MATCHED in PR-CSI-018 (S-335)",
                "why_it_matters": "the screen artefact is the SAME frozen file, so for these three "
                                  "this is a REPLICATION on a different population, not an "
                                  "independent draw. It is legitimate -- the prior is 'the screen "
                                  "is right', which is the hypothesis -- but it is a prior and it "
                                  "is named here rather than discovered afterwards.",
                "⚠ AND_THERE_IS_NO_SECONDARY_TO_FALL_BACK_ON": "the first freeze carried a "
                    "five-head SECONDARY; R32-A showed nothing could compute it and its "
                    "anti-fallback guard did not bind. It is DELETED. These three heads are in "
                    "the primary and nowhere else."},
            "⚠ HEAD_18_PREDICTS_L14": "the band-edge rival. PR-CSI-018 excluded head 16 for this, "
                                      "correctly, where a small set could not be told from "
                                      "top-of-band bias. Here the eight predictions span SIX "
                                      "distinct layers, so the spanning rule and the permutation p "
                                      "both bite. Head 18 is INCLUDED and this rule is frozen "
                                      "BEFORE any cell is measured; dropping it after seeing the "
                                      "composition would be post-hoc selection."},
        "SCREEN_PREDICTIONS_ON_RECORD_BEFORE_THIS_FAMILY": {
            "artifact": SCREEN_ARTIFACT, "artifact_md5_at_freeze": md5(SCREEN_ARTIFACT),
            "screen_blob": scr.get("grad_root") or scr.get("model_id"),
            "predictions": {str(h): "L%d" % pred[h] for h in HEADS},
            "margins_over_runner_up": {str(h): screen[str(h)]["margin"] for h in HEADS},
            "distinct_layers": sorted(set(lay_all)),
            "RE_DERIVED_BY_THIS_SCRIPT": "yes -- from AtP_by_cell, not copied from any entry"},
        "PRIMARY": {
            "statistic": "M = number of ADMITTED heads whose argmax band layer by |E| equals that "
                         "head's frozen screen-predicted layer",
            "null": "the screen's per-cell prediction is unrelated to the basket depth profile",
            "alpha": ALPHA,
            "binomial": "P(Binom(K, 1/9) >= M)",
            "conditional": "the same over ADMITTED heads whose predicted layer is unique among the "
                           "admitted set",
            "permutation": {
                "DEFINITION_VERBATIM": "p_perm = the fraction of the DISTINCT assignments q of the "
                                       "prediction multiset to the admitted heads for which "
                                       "#{i : q_i == the OBSERVED argmax layer of head i} >= M",
                "⚠ WHAT_IT_IS_COMPARED_AGAINST": "the OBSERVED ARGMAX VECTOR, not the prediction "
                    "vector. S-352: the first freeze of this family compared against the "
                    "predictions, which is a DIFFERENT statistic -- they coincide only at M = K, "
                    "and on one measured case the two gave 0.000099..0.000595 against 0.002679. "
                    "The reader (scripts/dcs_csi_pr016_argmax_test.py) has always used the "
                    "observed vector; this text now matches it, and THAT is the statistic.",
                "multiset_at_K8": ["L%d" % x for x in sorted(lay_all)],
                "n_distinct_assignments_at_K8": n_assign(lay_all),
                "floor_at_K8": 1.0 / n_assign(lay_all)},
            "ALL_THREE_FLOORS_AT_K8": {
                "permutation": 1.0 / n_assign(lay_all),
                "conditional": binom_ge(len(uq_all), len(uq_all)),
                "binomial": binom_ge(len(HEADS), len(HEADS)),
                "WEAKEST": max(1.0 / n_assign(lay_all), binom_ge(len(uq_all), len(uq_all)),
                               binom_ge(len(HEADS), len(HEADS))),
                "why_all_three": "the WEAKEST gates, so recording only the permutation floor (as "
                                 "the first freeze did) omits the one that actually decides a "
                                 "perfect result"},
            "SUCCESS": "the WEAKEST of the three p-values <= 0.05 AND the spanning rule satisfied",
            "GATING": "weakest_of_three",
            "FAILURE": "the weakest p > 0.05 with K >= 3",
            "SPANNING_RULE": "the MATCHING heads must not all share one band layer, or CANNOT "
                             "ANSWER whatever the p-values say",
            "HOW_THE_CLAIM_MUST_BE_STATED": "with the WEAKEST of the three, each named. Quoting the "
                                            "binomial alone is FORBIDDEN.",
            "⛔ THERE_IS_NO_SECONDARY_ANALYSIS": {
                "what_was_removed": "the first freeze preregistered a SECONDARY over the five "
                                    "never-tested heads (%s), with a floor of %.6f."
                                    % (fresh, 1.0 / n_assign(lay_fresh)),
                "why_it_is_gone": "R32-A: NOTHING IN THE REPOSITORY COULD COMPUTE IT. The reader "
                    "produces one verdict over pr['heads']; a secondary would have been computed "
                    "BY HAND AFTER THE READ. And its ⛔ NOT_A_FALLBACK guard did not bind: it was "
                    "keyed on the PRIMARY 'failing', while the likeliest route to a rescue is "
                    "CANNOT ANSWER (a tie under VOID 6, a spanning violation, K < 3) -- in which "
                    "the primary has not failed and nothing forbade reporting a passing secondary.",
                "consequence": "the three replication heads (%s) stay IN the primary and are "
                               "disclosed by name. No five-head analysis may be reported from this "
                               "family at all; it would be a separate preregistration."
                               % PREDICTION_TESTED_ON_BUTTON},
            "⛔ NO_POST_HOC_SHARPNESS_SUBSETTING": {
                "margins": {str(h): screen[str(h)]["margin"] for h in HEADS},
                "rule": "the margins are frozen per head HERE precisely so that a margin-restricted "
                        "subset reported after the read can be recognised as one. Reporting any "
                        "such subset -- as the result, as a rescue of a null, or as a "
                        "qualification of a positive -- IS FORBIDDEN."}},
        "ADMISSION": {
            "rule": "head h is ADMITTED iff its whole-head arm HD_<h> has a ci95 excluding 0 AND "
                    "|E(HD_<h>)| >= %s x bar(h)" % ADMIT_RATIO,
            "ratio": ADMIT_RATIO,
            "COMPUTED_FROM": "the whole-head arm ALONE, never from the cells",
            "A_DROPPED_HEAD_IS_NOT_A_MISS": "it leaves K and is reported with its measured power",
            "EXPECTED": "all eight are expected to be admitted -- S-347 measured their |E|/bar on "
                        "PR-CSI-012's arms at 2.49 / 2.33 / 2.13 / 2.07 / 1.92 / 1.92 / 1.84 / 1.80 "
                        "(heads 6, 18, 10, 21, 4, 11, 13, 27). Heads 27 and 13 are the THIN ones.",
            "⚠ THESE_ARE_EXPECTATIONS_NOT_THE_VERDICT": "they come from PR-CSI-012's arms; this "
                                                        "family recomputes admission from its OWN "
                                                        "HD_<h> arms by the S-311 rule.",
            "✅ LOSING_A_THIN_HEAD_MAKES_THIS_FAMILY_STRONGER": "heads 13 and 27 are the two that "
                "COLLIDE on L10. Dropping either breaks the tie and raises K_unique from 4 to 5, "
                "raising P(certify | q=0.83) from 0.8563 to 0.9578 (S-348). PR-CSI-018 had the "
                "OPPOSITE exposure: losing either of its two unique-layer heads was fatal."},
        "DETECTABILITY_PREREGISTERED_PER_HEAD": {
            "method": "the S-311 RULE, computed at read time from this family's own HD_<h> arms",
            "BAR_IS_A_RULE": {
                "z": Z,
                "rule": "bar(h) = z * SD(per-domain paired delta of HD_<h> minus the base arm, "
                        "ddof=1) / sqrt(n_domains)",
                "DDOF_IS_PINNED": "S-318 verified ddof=1 reproduces published bars exactly",
                "WHY_NOT_A_NUMBER": "a bar must come from the family it judges"},
            "per_head": {str(h): {"bar_source_arm": "HD_%d" % h,
                                  "screen_predicted_layer": pred[h],
                                  "screen_margin_over_runner_up": screen[str(h)]["margin"],
                                  "whole_head_REFERENCE": ref[str(h)]} for h in HEADS},
            "⚠ NOT_HELD_OUT": "THE SCREEN IS basket TRAIN AND THIS CENSUS IS basket VALIDATION, so "
                              "the LAYER is held out on SPLIT ONLY -- **NOT on codeword**. "
                              "PR-CSI-018 was held out on BOTH (a basket screen predicting BUTTON "
                              "cells), so D39's framing is STRONGER than anything this family can "
                              "claim and must not be carried over to it. The HEAD SET is chosen "
                              "using PR-CSI-012's basket validation magnitudes, i.e. the SAME "
                              "split this family reads. ⚠ THE FIRST FREEZE DEFENDED THIS WITH "
                              "THE WRONG ARGUMENT -- that liveness is a whole-head property while "
                              "the test is which CELL within a head. R32-A showed that defends the "
                              "wrong thing: selecting heads on whole-head validation magnitude CAN "
                              "tilt the marginal distribution of argmax layers, and BOTH the "
                              "binomial and the conditional rest on a uniform-over-9 null that "
                              "S-351 measured to be empirically wrong. WHAT ACTUALLY PROTECTS THE "
                              "FAMILY is the PERMUTATION component: it conditions on the observed "
                              "argmaxes, so a shared band bias cannot fake it, and because GATING "
                              "is weakest_of_three the gate is valid whenever ANY ONE component "
                              "is. PR-CSI-018's frozen read said this in terms; the first freeze "
                              "of this family replaced it and lost the argument that works.",
            "NOT_THE_PRIMARY": "the bar governs the depth map's CLEARS/does-not-clear; the PRIMARY "
                               "is argmax agreement and does not use the bar"},
        "POWER_BY_SEEDED_MONTE_CARLO": {
            "⚠ WHY_NOT_EXACT_ENUMERATION": "the first freeze computed power as an exact sum over "
                "the 2^K match patterns. That is only possible if p depends on M ALONE -- which is "
                "true of the statistic that freeze used and FALSE of the reader's, where p is "
                "scored against the OBSERVED ARGMAX VECTOR and therefore depends on WHERE the "
                "misses land. S-353: two outcomes with identical M and identical M_unique can get "
                "different verdicts, so no exact table over match counts exists.",
            "model": "each admitted head matches its prediction with probability q INDEPENDENTLY; "
                     "a miss lands UNIFORMLY on one of the other 8 band layers",
            "N": MC_N, "seed": MC_SEED,
            "P_certify_by_q": {str(q): power_mc(pred, HEADS, q, MC_N, MC_SEED)
                               for q in (P0, 0.33, 0.5, 0.67, 0.83, 1.0)},
            "⚠ BOTH_HALVES_OF_THE_MODEL_ARE_ASSUMPTIONS": {
                "independence": "positive correlation across heads would widen the true spread and "
                                "make these OPTIMISTIC",
                "uniform_misses": "S-351 MEASURED that the empirical argmax marginal is NOT uniform "
                                  "-- over the 10 heads this sprint has cell-censused, L10 and L14 "
                                  "take 60%. So this half is known to be wrong IN DETAIL. R32-A "
                                  "computed the type I under the empirical marginal at 0.00306, "
                                  "BELOW the uniform figure, i.e. the error is in the conservative "
                                  "direction -- but that number is R32-A's and is NOT asserted here."},
            "TYPE_I": "P(certify | q = 1/9) is recorded above. It is far below alpha = 0.05, which "
                      "is the price of gating on the WEAKEST of three. A NULL from this family is "
                      "therefore WEAK evidence against the screen, not strong. ⚠ The first freeze "
                      "put this at 0.0004; under the reader's statistic it is ~0.0041 (S-354), an "
                      "order of magnitude higher and still conservative.",
            "⚠ POWERED_FOR_A_STRONG_SCREEN": "at q = 0.33 power is ~0.10 (the first freeze said "
                "~0.05, which OVERSTATED the limitation). This family can confirm a screen that "
                "works; it cannot distinguish a mediocre screen from a useless one.",
            "NECESSARY_CONDITIONS_FOR_CERTIFICATION": {
                "rule": "M >= 3 AND M_unique >= 3",
                "why": "P(Binom(8,1/9) >= 2) = 0.22051131 > alpha forces M >= 3; "
                       "P(Binom(4,1/9) >= 2) = 0.06355738 > alpha forces M_unique >= 3. "
                       "⚠ P(Binom(8,1/9) >= 3) = 0.04999816 clears alpha by 1.8e-6 -- a knife edge, "
                       "recorded because it is one.",
                "⛔ NECESSARY_BUT_NOT_SUFFICIENT": "S-353 exhibited 34 outcomes satisfying this rule "
                    "that do NOT certify (e.g. M=3, M_unique=3, weakest 0.091071), because p_perm "
                    "depends on where the misses land. NO rule in (M, M_unique) alone "
                    "characterises certification, and this prereg does not pretend one does."}},
        "DOSE_EXPECTATION": {
            "per_cell_prefill_edits": DOSE_UNIT // len(BAND),
            "whole_head_arm_prefill_edits": DOSE_UNIT,
            "derivation": "DOSE_UNIT %d / %d band layers" % (DOSE_UNIT, len(BAND)),
            "STATUS": "MEASURED (S-299, S-306, S-317, and S-335 on 62 arms)",
            "⚠ BLIND_AS_AN_IDENTITY": "all 72 cell arms expect %d and all 8 HD_ arms plus BK_KO "
                                      "expect %d, so the dose cannot distinguish arms within "
                                      "either group. Identity MUST come from each run's own "
                                      "knockout_cells (S-292/S-310)."
                                      % (DOSE_UNIT // len(BAND), DOSE_UNIT)},
        "population": {"validation_domains": 23, "validation_expect_n": 230,
                       "test_domains": 23,
                       "test_note": "TEST is NEVER touched. S-314: it is ALSO already spent and "
                                    "selection-contaminated, so it is not an axis even in principle."},
        "CENSUS_DELIVERABLE": "72 single-cell effects E(BK_H<h>_L<ll>) = the MEAN OVER THE 23 "
                              "DOMAINS of (y_install(cell) - y_install(BK_BASE)), each with a "
                              "percentile bootstrap ci95 over DOMAIN resamples; the eight "
                              "whole-head HD_<h> arms supplying the S-311 bars and the ADMISSION "
                              "decision, EXCLUDED from every per-cell count; and the BK_KO "
                              "all-32 denominator. ⚠ The first freeze omitted this key entirely, "
                              "so the census REFUSED the prereg before loading any arm -- after "
                              "~3.9 GPU-hours would have been spent (R32-A/R32-B). It is also "
                              "where the ESTIMATOR is defined, so without it the family had no "
                              "estimator definition anywhere, a PART I 3.5 violation.",
        "DOSE_IDENTITY_IS_BLIND_HERE": "72 cell arms share a prefill dose of 224 and NINE arms "
                                       "share 2016 (the eight HD_<h> plus BK_KO). The dose "
                                       "therefore carries NO identity information within either "
                                       "group. Arm identity MUST be asserted from each run's own "
                                       "knockout_cells, and for BK_KO from its recording NO cell "
                                       "list (S-292/S-310).",
        "ESTIMATOR_AND_RESAMPLER": {
            "estimator": "per arm, E = mean over DOMAINS of the per-domain paired delta "
                         "(arm minus BK_BASE). DOMAIN is the unit (PART I 3.1); rows never "
                         "inflate n.",
            "bootstrap": {"method": "percentile, resampling DOMAINS", "B": 10000,
                          "seed": 20260922, "ci": 0.95,
                          "⚠ WHY_FROZEN_HERE": "these were COMMAND-LINE DEFAULTS of "
                              "scripts/dcs_csi_head_census.py, not preregistered quantities. Every "
                              "published census used them, so this is a sprint-wide gap rather "
                              "than a new one -- PR-CSI-020 is where it closes (R32-A CONCERN 2)."},
            "bar_rule": "bar(h) = 1.96 * SD(per-domain paired delta of HD_<h> minus BK_BASE, "
                        "ddof=1) / sqrt(23)"},
        "MEASURED_ARGMAX_MARGINAL_BEFORE_THIS_FAMILY": {
            "what": "the marginal distribution of the INTERVENTION argmax layer over the 10 heads "
                    "this sprint had cell-censused before PR-CSI-020 (PR-014, PR-015, PR-018)",
            "counts": {"L6": 1, "L7": 1, "L8": 1, "L9": 0, "L10": 3,
                       "L11": 1, "L12": 0, "L13": 0, "L14": 3},
            "⚠ IT_IS_NOT_UNIFORM": "L10 and L14 take 60% of ten heads against a uniform 11.1% each, "
                "and this family predicts L10 twice and L14 once. A random screen predicting THIS "
                "multiset would match at ~0.1625, not 1/9 = 0.1111 (S-351), so THE BINOMIAL p IS "
                "ANTI-CONSERVATIVE FOR THIS MULTISET.",
            "why_the_family_is_still_valid": "the PERMUTATION p conditions on the observed argmaxes "
                "and the CONDITIONAL runs over unique-layer heads, so a favourable marginal cancels "
                "in both; and under weakest_of_three the binomial is always the smallest of the "
                "three and never gates. This is exactly why S-317/S-319 moved the gating off the "
                "binomial.",
            "⛔ NOT_A_CORRECTED_NULL": "0.1625 is a DIAGNOSTIC and must not be substituted into "
                "anything. Building a 'corrected binomial' after seeing this marginal would be the "
                "post-hoc statistic-selection this sprint forbids."},
        "NO_RANK_TEST": "this family carries no control pool and no rank; the rank tooling must "
                        "refuse it",
        "VOID_CONDITIONS": {
            "1": "any arm's recorded knockout_cells differs from cell_sets",
            "2": "BK_BASE records any intervention flag",
            "3": "BK_KO records a cell list (it must record NONE)",
            "4": "any arm's rows != 230 or domains != 23",
            "5": "the screen artefact's md5 differs from artifact_md5_at_freeze",
            "6": "a tie for the argmax on any admitted head -- CANNOT ANSWER, M and p NOT computed",
            "7": "more than one run directory for any arm (S-261/S-334)",
            "8": "any HD_<h> arm differs from its whole_head_REFERENCE by more than void_tolerance. "
                 "ENFORCED by scripts/dcs_csi_head_census.py (S-323), under the FAMILY-NEUTRAL key "
                 "(S-349)",
            "9": "arms split across GPU ARCHITECTURES (S-037/S-119). The frozen READ pins a single "
                 "slurm job id; PR-CSI-012's reference arms ran on 3090s and VOID 8's tolerance is "
                 "1e-6, so architecture is load-bearing here. ⚠ RESTORED: PR-CSI-018 carried this "
                 "and the first freeze of PR-CSI-020 dropped it (R32-A CONCERN 6)",
            "10": "attn_implementation != eager on any arm. ⚠ RESTORED; enforced by NO code -- it "
                  "is checked by reading each arm's config at read time",
            "11": "scripts/ or src/ edited while arms are in flight. ⚠ RESTORED; enforced by NO "
                  "code. The launcher records the commit at submit (CSI_GIT_BLOB), and R30-D "
                  "measured that per-arm RUNMETA git_commit names the code that ran for only the "
                  "FIRST arm, so the launcher's BLOB line is the family's commit of record",
            "12": "the frozen READ amended after any number from this family is seen. ⚠ RESTORED",
            "⚠ WHICH OF THESE ARE ACTUALLY ENFORCED BY CODE": "1, 3, 4, 6, 7 and 8 are. 2 is "
                "enforced by the census's base-arm identity check (S-332). 5, 9, 10, 11 and 12 are "
                "PROSE, checked by the operator at read time. R32-B found that condition 5 in "
                "particular -- the screen md5 -- is read by no reader, gate or test, which is the "
                "R29/VOID-8 shape one condition over. It is recorded as prose HERE rather than "
                "silently implied to be automatic."},
        "WHAT_THIS_CANNOT_ANSWER": [
            "whether the screen predicts for heads that are NULL on basket -- this family admits "
            "only live ones, by construction",
            "anything about the OTHER 24 heads, or about cells outside band 6-14",
            "anything about the SOURCE of the effect (S-316/AM-40 stand; the mass instrument's "
            "criterion licenses a REFUTATION reading only, S-337/S-343)",
            "anything about TEST",
            "whether the screen's sub-argmax ORDERING transfers -- S-307 measured that it does not"],
        "MUST_NOT_BE_SAID_IF_POSITIVE": [
            "the binomial p alone -- the claim is the WEAKEST of the three, each named. ⚠ This "
            "now has a MEASURED reason and not only a methodological one: S-351 measured that for "
            "THIS prediction multiset a random screen would match at ~0.1625 against the "
            "binomial's assumed 1/9, so quoting it alone would be quantitatively misleading by "
            "~46%, not merely incomplete",
            "that this is held out on codeword -- IT IS NOT. Split only. D39 is the cross-codeword "
            "result; this is not, and conflating them would overstate both",
            "'cell (L, h) is the writer' -- there is STILL no control family of ARBITRARY cells "
            "anywhere in this sprint. This is NECESSITY, rung 1 of AM-34's ladder",
            "that the screen is a validated cell selector IN GENERAL -- eight heads, every one "
            "chosen BECAUSE it was live on basket",
            "any margin-restricted subset of the eight",
            "that D37 is superseded -- D37 is descriptive and stands; this ADDS a preregistered p"],
        "MUST_NOT_BE_SAID_IF_NULL": [
            "that the screen is useless -- type I here is far below alpha and power at a MEDIOCRE "
            "screen (q = 0.33) is ~0.05, so a null is WEAK evidence against it",
            "that D39 is withdrawn -- D39 stands on its own preregistered read of button",
            "that D37 is withdrawn -- D37 is descriptive and rests on its own arms",
            "that the basket depth structure is absent -- D36/D37 measured it directly"],
        "SELECTION_RE_ENTERS_WHEN": "any head is added, re-ordered, or dropped OTHER THAN BY THE "
                                    "FROZEN ADMISSION RULE, after an arm has run. ⚠ The first "
                                    "freeze said 'added, dropped or re-ordered' without that "
                                    "exception, which contradicted ADMISSION -- whose whole job is "
                                    "to drop heads after the arms have run (R32-A CONCERN 5).",
    }
    return pr


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="configs/dcs_csi_pr020_cell_census_basket_8heads.json")
    a = ap.parse_args()
    pr = build()
    path = os.path.join(REPO, a.out)
    with open(path, "w") as fh:
        json.dump(pr, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    print("wrote %s  (%d bytes, md5 %s)"
          % (a.out, os.path.getsize(path), md5(a.out)))
    print("arms: %d   heads: %s" % (pr["n_arms_per_split"], pr["heads"]))
    print("predictions: %s" % pr["SCREEN_PREDICTIONS_ON_RECORD_BEFORE_THIS_FAMILY"]["predictions"])
    print("permutation: %d assignments, floor %.8f"
          % (pr["PRIMARY"]["permutation"]["n_distinct_assignments_at_K8"],
             pr["PRIMARY"]["permutation"]["floor_at_K8"]))
    p = pr["POWER_BY_SEEDED_MONTE_CARLO"]["P_certify_by_q"]
    print("power: type I %.5f | q=0.33 %.5f | q=0.83 %.5f   (MC N=%d seed=%d)"
          % (p[str(P0)], p["0.33"], p["0.83"],
             pr["POWER_BY_SEEDED_MONTE_CARLO"]["N"], pr["POWER_BY_SEEDED_MONTE_CARLO"]["seed"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
