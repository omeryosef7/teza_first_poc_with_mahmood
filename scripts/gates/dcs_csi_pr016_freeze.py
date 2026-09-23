"""Freeze PR-CSI-016 -- the per-CELL census of heads 17, 19 and 23 on BUTTON validation.

WHY THIS FAMILY, AND WHY IT IS DIFFERENT FROM PR-CSI-014/015. Those two were CENSUSES: descriptive,
no rank, no p, because AM-37/S-294 measured that no admissible held-out axis existed for a
confirmatory cell test. S-309 amended that inventory: `button validation` was blocked for HEAD 2 and
only for head 2 -- PR-CSI-013's own RANDOM control draws already measured 20 other heads there, and
head 19 sits at E = -0.035568, |E|/bar = 5.69, agreeing with its basket value to 88.7%.

So this family is HELD OUT ON TWO COORDINATES and CAN CARRY A p:

  the LAYER prediction   basket TRAIN screen, 67 domains   -- on record since commit 94aab78b
  the READ               button VALIDATION, 23 domains     -- a different SPLIT *and* a different CODEWORD

⛔ THE HEAD SET IS STILL NOT HELD OUT. Heads {17,19,23} come from D34, a basket-VALIDATION census
(S-307 §6). This family does not repair that and does not claim to. What is held out is the
within-head LAYER, which is the quantity the primary tests.

THE PRIMARY, and it is a real test rather than a map. For each ADMITTED head h let Lhat(h) be the
argmax over that head's nine band cells of |E|. The screen's prediction S(h) was frozen before any
button arm existed. M = #{h : Lhat(h) == S(h)}. Under H0 -- the screen's per-cell prediction is
unrelated to the button depth profile -- Lhat(h) is uniform over the 9 band layers and independent
across heads, so p = P(Binom(K, 1/9) >= M).

  K=3: M=3 -> p=0.001372   M=2 -> p=0.034294   M=1 -> p=0.297668
  K=2: M=2 -> p=0.012346
  K=1: floor is 1/9 = 0.1111 -> CANNOT ANSWER for any M

⚠⚠ THE SPANNING RULE, AND IT IS NOT A DETAIL. The screen says L14 for TWO of the three heads. If the
button intervention carries a shared bias toward the top of the band, M=2 arrives FOR FREE and p =
0.034 would read as a pass while measuring nothing about the screen. So the preregistered success
criterion additionally requires THE MATCHING HEADS NOT TO BE CONFINED TO ONE LAYER. Basket's own
result (L14, L14, L7) spans two layers and would satisfy it; a bare "both L14 heads matched, head 23
did not" does not, and is declared CANNOT ANSWER here, before any number exists.

ADMISSION IS COMPUTED FROM THE WHOLE-HEAD ARM ALONE, NEVER FROM THE CELLS -- otherwise the test would
select the heads on the data it then reads. Head h is admitted iff its full-band arm HD_<h> has a
ci95 excluding 0 AND |E| >= 1.5 x that head's bar. A dropped head is reported WITH ITS POWER and is
NOT counted as a miss; K falls and the floor rises accordingly.

⚠ THE BARS CANNOT BE FROZEN AS NUMBERS. Heads 17 and 23 have NEVER had a button arm, so their bars do
not exist until this family runs. S-311 therefore lets the prereg freeze the DERIVATION -- naming the
full-band arm each bar is computed from -- with the reader refusing a source arm that is missing, not
in the family, or narrower than the whole head (which would compute the bar from the very quantity it
judges). Head 19's bar IS predictable from PR-013 and is recorded below as a FALSIFIABLE PREDICTION,
not as the bar that will be used.

⛔ THE WHOLE-HEAD ARMS ARE EXPRESSED AS NINE-CELL LISTS, because the census reader refuses a prereg
carrying both `head_sets` and `cell_sets`. That makes each one dose-identical to BT_KO (9 x 224 =
2016) and identical on `knockout_heads` (both empty -> "ALL"): the collision S-310 had to close
before this family could exist at all.
"""
import argparse, hashlib, json, math, os, sys
from math import comb

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dcs_csi_pr010_freeze import atomic_write_json      # reuse; never re-implement the writer

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DOSE_UNIT = 2016
BAND = [6, 7, 8, 9, 10, 11, 12, 13, 14]
HEADS = [17, 19, 23]
# S-269's reading of the basket TRAIN screen, on record in commit 94aab78b (2026-09-23 01:05) and in
# runargs/dcs_csi_pr015_read.txt (fbf1fbf5) before job 922176 started. NOT re-derived here: this file
# QUOTES a prior commitment, and R27 flagged that the PR-015 freeze script quoted the same literal
# without pinning the artefact -- so the artefact's md5 is recorded alongside it.
SCREEN = {"17": 14, "19": 14, "23": 7}
SCREEN_ARTIFACT = "outputs/boombness/dcs_csi/w1_screen_train_basket_916132.json"
ALPHA = 0.05
ADMIT_RATIO = 1.5


def _md5(path):
    with open(path, "rb") as fh:
        return hashlib.md5(fh.read()).hexdigest()


def binom_tail(M, K, p=1.0 / 9.0):
    return sum(comb(K, i) * p ** i * (1 - p) ** (K - i) for i in range(M, K + 1))


def verify_screen_literal():
    """R27/S-308 filed the bare `screen = {...}` literal in the PR-015 freeze script as a MINOR: it is
    the prediction side of the headline and the script never opened the artefact it cites. Here it is
    re-derived from the 288-cell grid and REFUSED on mismatch."""
    p = os.path.join(REPO, SCREEN_ARTIFACT)
    if not os.path.exists(p):
        sys.exit("REFUSING: the screen artefact %r does not exist. A prereg quoting a prediction "
                 "from a file that is not there is S-167c." % SCREEN_ARTIFACT)
    scr = json.load(open(p))
    if scr.get("split") != "train":
        sys.exit("REFUSING: the screen's split is %r, not 'train'. The whole cross-split claim "
                 "depends on the prediction being TRAIN-side." % scr.get("split"))
    if scr.get("codeword") != "basket":
        sys.exit("REFUSING: the screen's codeword is %r, not 'basket'." % scr.get("codeword"))
    atp = scr["AtP_by_cell"]
    for h in HEADS:
        got = max(BAND, key=lambda L: abs(atp["%d,%d" % (L, h)]))
        if got != SCREEN[str(h)]:
            sys.exit("REFUSING: head %d's screen argmax re-derives to L%d but this file asserts L%d. "
                     "The literal has DRIFTED from the artefact it quotes." % (h, got, SCREEN[str(h)]))
    print("[pr016] screen literal re-derived from %s (md5 %s): %s  OK"
          % (SCREEN_ARTIFACT, _md5(p), {k: "L%d" % v for k, v in SCREEN.items()}))
    return _md5(p)


def head19_bar_prediction():
    """Head 19 is the ONE head whose button bar is predictable before the run, from PR-CSI-013's own
    control arm BT_CTRL_01. Recorded as a FALSIFIABLE PREDICTION, never as the bar that will be used
    -- the bar that WILL be used is computed by the S-311 rule from this family's own HD_19."""
    rep = os.path.join(REPO, "reports/DCS_CSI_PR013_BUTTON_HEAD_validation.json")
    pr13 = os.path.join(REPO, "configs/dcs_csi_pr013_button_head_replication.json")
    if not (os.path.exists(rep) and os.path.exists(pr13)):
        sys.exit("REFUSING: PR-CSI-013's report/prereg are missing; head 19's prediction cannot be "
                 "derived and this file will not invent one.")
    d = json.load(open(rep))
    hs = json.load(open(pr13))["head_sets"]
    arm = next((a for a, v in hs.items() if (sorted(v)[0] if isinstance(v, list) else v) in (19, [19])
                or 19 in (v if isinstance(v, list) else [v])), None)
    if arm is None or arm not in d.get("ci95", {}):
        sys.exit("REFUSING: no PR-013 arm resolves to head 19.")
    lo, hi = d["ci95"][arm]
    sd = (hi - lo) / 2.0 / 1.96 * math.sqrt(23)
    return {"arm_in_pr013": arm, "E": d["E"][arm], "ci95": [lo, hi],
            "implied_per_domain_SD": sd, "predicted_bar": 1.96 * sd / math.sqrt(23),
            "STATUS": "A FALSIFIABLE PREDICTION, NOT THE BAR. The bar used is computed by the S-311 "
                      "rule from THIS family's own HD_19 arm. If the two disagree by more than 25% "
                      "that is a finding about cross-job reproducibility and must be reported."}


def build(screen_md5, h19):
    cells, arms_doc = {}, {}
    for h in HEADS:
        cells["HD_%d" % h] = [[L, h] for L in BAND]          # the bar source / whole-head arm
        for L in BAND:
            cells["BC_H%d_L%02d" % (h, L)] = [[L, h]]
    per_head = {str(h): {"bar_source_arm": "HD_%d" % h,
                         "screen_predicted_layer": SCREEN[str(h)]} for h in HEADS}
    per_head["19"]["head19_bar_prediction_from_pr013"] = h19
    K = len(HEADS)
    return {
        "id": "PR-CSI-016",
        "title": "Per-CELL census of heads 17, 19, 23 on BUTTON validation: does the depth "
                 "localisation D36/PR-015 found on basket TRANSFER ACROSS CODEWORDS, and does the "
                 "basket TRAIN screen predict the button cell? A TEST, with a p.",
        "frozen_utc_date": "2026-09-23",
        "EMITTED_MECHANICALLY_BY": "scripts/gates/dcs_csi_pr016_freeze.py",
        "design_ref": "S-309 (the axis amendment that unblocks button); S-306/S-307 (the basket "
                      "result this tests); S-310 (the denominator collision this family's shape "
                      "creates); S-311 (the bar as a frozen rule); AM-37/S-294 (why earlier cell "
                      "families could not carry a p)",
        "split": "validation",
        "codeword": "button",
        "concept": "bomb",
        "statistical_unit": "DOMAIN for every E (23 domains, 230 rows, never the row). THE TEST UNIT "
                            "IS THE HEAD: K admitted heads, one argmax each.",
        "endpoint": "y_install; concept-free semantic_one_word; cell C; n_examples 4",
        "heads": HEADS,
        "band": "6-14",
        "layers": BAND,
        "base_arms": ["BC_BASE", "BC_KO"],
        "cell_sets": cells,
        "n_arms_per_split": len(cells) + 2,
        "intervention": {"intervene": "demo_all:attn_knockout:6-14:1.0",
                         "knockout_scope": "target_surface_row_only", "band": "6-14"},
        "arms": {
            "BC_BASE": "no --intervene; the clean reference",
            "BC_KO": "--intervene with NO selector = all 32 heads x all 9 band layers; the denominator",
            "HD_<h>": "--knockout-cells for ALL NINE band cells of head h. The whole-head arm: it "
                      "supplies that head's bar (S-311 rule) and its ADMISSION, and it is the "
                      "head-level cross-codeword replication of D34. NOT all three are new: HD_19 "
                      "re-runs the head PR-CSI-013 already measured on button as its control arm "
                      "BT_CTRL_01 (E = -0.035568), so it is a cross-JOB reproduction check rather "
                      "than a first measurement. HD_17 and HD_23 have never had a button arm. "
                      "EXCLUDED from the depth map and from every per-cell count.",
            "BC_H<h>_L<ll>": "--knockout-cells <ll>:<h> -- ONE cell",
        },
        "SCREEN_PREDICTIONS_ON_RECORD_BEFORE_THIS_FAMILY": {
            "predictions": {k: "L%d" % v for k, v in SCREEN.items()},
            "source": "S-269's reading of the basket TRAIN AtP screen",
            "artifact": SCREEN_ARTIFACT,
            "artifact_md5_at_freeze": screen_md5,
            "committed_in": "94aab78b (S-269, 2026-09-23 01:05) and fbf1fbf5 (the PR-015 frozen read)",
            "RE_DERIVED_BY_THIS_SCRIPT": "yes -- argmax_L |AtP_by_cell[L,h]| over the 288-cell grid; "
                                         "a mismatch is a REFUSAL (R27 filed the un-pinned literal "
                                         "in the PR-015 freeze script as a MINOR)",
            "⚠ NOT_HELD_OUT": "the screen is TRAIN and basket; the HEAD SET is basket VALIDATION "
                              "(D34). The LAYER is held out on split AND codeword; the HEAD is not.",
        },
        "PRIMARY": {
            "statistic": "M = number of ADMITTED heads whose argmax band layer by |E| equals that "
                         "head's frozen screen-predicted layer",
            "null": "H0: the screen's per-cell prediction is unrelated to the button depth profile, "
                    "so each admitted head's argmax is uniform over the 9 band layers and "
                    "independent across heads",
            "test": "one-sided p = P(Binom(K, 1/9) >= M)",
            "alpha": ALPHA,
            "p_table": {"K=%d,M=%d" % (K2, M): round(binom_tail(M, K2), 6)
                        for K2 in (3, 2, 1) for M in range(K2, -1, -1)},
            "SUCCESS": "p <= 0.05 AND the spanning rule below is satisfied",
            "FAILURE": "p > 0.05 with K >= 2",
            "SPANNING_RULE": {
                "rule": "the MATCHING heads must not all share one band layer",
                "WHY": "the screen predicts L14 for TWO of the three heads. If the button "
                       "intervention carries a shared bias toward the top of the band, M=2 arrives "
                       "for free and p=0.034 would read as a pass while measuring NOTHING about the "
                       "screen. Frozen before any number exists.",
                "IF_VIOLATED": "CANNOT ANSWER on the screen question, whatever p says. The depth map "
                               "is still reportable as a description.",
            },
            "MUST_ALSO_BE_REPORTED": "the full per-head argmax, the intervention's own argmax "
                                     "marginal across the admitted heads, and every dropped head "
                                     "with its power",
            "ROBUSTNESS_CO_PRIMARIES_ADDED_BEFORE_LAUNCH_R28_S312": {
                "WHY": "the SPANNING RULE blocks the M=2 shared-bias pass and leaves M=3 OPEN. If "
                       "the button intervention carries the top-of-band bias this design "
                       "hypothesises, heads 17 and 19 are pinned to L14 FOR FREE and the only "
                       "informative event is head 23 landing on L7 -- probability 1/9 = 0.1111, "
                       "which cannot clear alpha. The binomial p would read 0.001372 and understate "
                       "the type-I error of the SCIENTIFIC claim by ~81x. R28 demonstrated exactly "
                       "that by building the biased world and running the real reader on it.",
                "p_conditional": "P(Binom(K_unique, 1/9) >= M_unique) over the ADMITTED heads whose "
                                 "screen-predicted layer is not shared with another admitted head. "
                                 "With 17 and 19 both predicted L14, K_unique = 1, floor 0.1111.",
                "p_permutation": "the exact permutation p over assignments of the screen's prediction "
                                 "MULTISET to the admitted heads. It asks whether the screen put the "
                                 "ODD prediction on the RIGHT head, which a shared band bias cannot "
                                 "fake because it says nothing about WHICH head gets the minority "
                                 "layer. With {L14, L14, L7} its floor is 1/3.",
                "HOW_THE_CLAIM_MUST_BE_STATED": "with the WEAKEST of the three, each named. A "
                                                "headline quoting only the binomial p is FORBIDDEN "
                                                "whenever two admitted heads share a predicted layer.",
                "NOT_A_SUCCESS_CRITERION": "these do NOT gate the preregistered PASS/FAIL, because "
                                           "requiring them would make this family unable to pass for "
                                           "a STRUCTURAL reason (K_unique = 1) rather than an "
                                           "empirical one. They BOUND THE WORDING -- which S-307 "
                                           "established is the honest use of a robustness number, "
                                           "except that these are frozen BEFORE the run, not after.",
            },
        },
        "ADMISSION": {
            "rule": "head h is ADMITTED iff its whole-head arm HD_<h> has a ci95 excluding 0 AND "
                    "|E(HD_<h>)| >= %.1f x bar(h)" % ADMIT_RATIO,
            "ratio": ADMIT_RATIO,
            "COMPUTED_FROM": "the whole-head arm ALONE, never from the cells -- admitting on the "
                             "cells would select the heads on the data the primary then reads",
            "A_DROPPED_HEAD_IS_NOT_A_MISS": "it is removed from K and reported with its power. K "
                                            "falls and the floor rises; at K=1 the floor is 1/9 = "
                                            "0.1111 and the family is CANNOT ANSWER.",
            "EXPECTED": "head 19 is expected to be admitted (PR-013 measured |E|/bar = 5.69 there). "
                        "Heads 17 and 23 have NEVER had a button arm and may fail this gate. That "
                        "is the family's real risk and it is priced here, not hidden.",
        },
        "DETECTABILITY_PREREGISTERED_PER_HEAD": {
            "method": "S-311: the bar is frozen as a RULE, not a number, because heads 17 and 23 "
                      "have never had a button arm and no number for them can exist before the run",
            "BAR_IS_A_RULE": {
                "z": 1.96,
                "rule": "bar(h) = z * SD(per-domain paired delta of arm <bar_source_arm> minus the "
                        "base arm) / sqrt(n_domains)",
                "WHY_NOT_A_NUMBER": "heads 17 and 23 have no prior button arm. Head 19's bar IS "
                                    "predictable from PR-013 and is recorded as a falsifiable "
                                    "PREDICTION under per_head['19'], never as the bar used.",
                "VERIFIED": "the identical rule, run against D34's SINGLE_17 arm, reproduces the "
                            "0.009082 that PR-CSI-015 froze as a NUMBER (tests/test_csi_cell_"
                            "identity.py::test_the_bar_RULE_reproduces_the_NUMBER_that_PR015_froze)",
            },
            "per_head": per_head,
            "⚠ NOT_HELD_OUT": "each bar is computed from this family's own whole-head arm on the "
                              "same 23 domains the cells are read on. It is a DIFFERENT ARM and only "
                              "its SPREAD is used, never its mean, so it is not circular in the "
                              "strong sense -- but it is NOT held out and must not be called so "
                              "(S-307 §6 made the same point about PR-015's bars).",
            "NOT_THE_PRIMARY": "the primary is the argmax agreement, which needs no bar at all. The "
                               "bars serve ADMISSION and the descriptive depth map only.",
        },
        "DOSE_EXPECTATION": {
            "per_cell_prefill_edits": DOSE_UNIT // len(BAND),
            "whole_head_arm_prefill_edits": DOSE_UNIT,
            "derivation": "DOSE_UNIT %d / %d band layers" % (DOSE_UNIT, len(BAND)),
            "STATUS": "MEASURED (PR-CSI-014 observed exactly 224.0 on nine cells across nine layers, "
                      "S-299; PR-CSI-015 reproduced it on 27 more, S-306)",
            "⚠ BLIND_AS_AN_IDENTITY": "all 27 cell arms expect 224 and all three HD_ arms expect "
                                      "2016 -- the SAME dose as BC_KO. Identity comes from each "
                                      "arm's own knockout_cells ONLY (S-310).",
        },
        "population": {"validation_domains": 23, "validation_expect_n": 230, "test_domains": 23,
                       "test_note": "TEST is NEVER touched",
                       "TEST_DOMAIN_COUNT_CORRECTED": "PR-CSI-014's and PR-CSI-015's preregs both "
                                                      "record test_domains = 3, and S-294's axis "
                                                      "inventory rests on it ('the 3 TEST domains "
                                                      "need n > 3.8'). The frozen manifest "
                                                      "dcs_ts116_domain_split.json declares "
                                                      "n_test = 23, and BOTH banks carry 4416 rows "
                                                      "over 23 distinct TEST domains -- identical "
                                                      "to validation. See S-312. TEST is NOT "
                                                      "touched here.",
                       "SAME_DOMAINS_AS_BASKET": "S-256 verified the 23 validation domains are the "
                                                 "same set. This family therefore controls the "
                                                 "CODEWORD, not the domain sample."},
        "CANNOT_ANSWER_IF": [
            "fewer than 2 heads are ADMITTED (at K=1 the floor 1/9 = 0.1111 cannot clear alpha=0.05)",
            "the spanning rule is violated -- the matching heads all share one band layer",
            "any admitted head's nine cells contain a tie for the argmax",
        ],
        "VOID_CONDITIONS": [
            "1. arms split across GPU architectures (S-037/S-119)",
            "2. attn_implementation != eager on any arm",
            "3. any TEST domain in any arm",
            "4. BC_BASE carrying any intervention flag",
            "5. an arm whose recorded knockout_cells != this prereg's cell_sets entry for it",
            "6. score_behavior.py or src/ edited while these arms are in flight",
            "7. any single-cell arm recording a dose other than %d, or any HD_ arm other than %d"
            % (DOSE_UNIT // len(BAND), DOSE_UNIT),
            "8. BC_KO recording a non-empty knockout_cells (S-310: a 9-cell arm is dose-identical "
            "and identity-identical to it on knockout_heads)",
            "9. the read amended after any number is seen",
        ],
        # ⚠⚠ R28/S-312 -- THE BLOCKER R28 CAUGHT. These five fields are validated by the census
        # reader's S-296 PRE-FLIGHT, before a single arm is loaded, and the first emission of this
        # prereg carried NONE of them. STEP 1 of the frozen read would have refused -- AFTER 32 arms
        # and ~1.8 GPU-hours had already been spent. S-296 exists precisely so that a missing field
        # costs milliseconds; it only does so if the prereg is run through the reader BEFORE launch,
        # which is what R28 did and what I had not.
        "NO_RANK_TEST": "There is no candidate cell, no control family of arbitrary cells and no "
                        "rank here. The PRIMARY is a per-head ARGMAX agreement against a prediction "
                        "frozen on a different split AND a different codeword, tested as "
                        "Binom(K, 1/9). control_prefix and n_controls are DELIBERATELY ABSENT so the "
                        "rank tooling refuses this prereg.",
        "CENSUS_DELIVERABLE": "27 single-cell effects E(BC_H<h>_L<ll>) = mean over domains of "
                              "(y_install(cell) - y_install(BC_BASE)), each with a bootstrap ci95; "
                              "three whole-head arms HD_<h> that supply the bars and the ADMISSION "
                              "and are EXCLUDED from every per-cell count; and the BC_KO denominator.",
        "SELECTION_RE_ENTERS_WHEN": "any single cell is named as 'the' site. The PRIMARY tests a "
                                    "PREDICTION made before the data existed, which is why it can "
                                    "carry a p; naming a winner afterwards is selection on the data "
                                    "that produced it, and AM-37 still holds that no admissible "
                                    "held-out axis exists for THAT test.",
        "DOSE_IDENTITY_IS_BLIND_HERE": "all 27 single-cell arms expect 224, and the three HD_ arms "
                                       "expect 2016 -- the SAME dose as BC_KO. The dose cannot tell "
                                       "any cell from any other, nor a whole-head arm from the "
                                       "denominator. Identity comes from each arm's own "
                                       "knockout_cells ONLY (S-292/S-310).",
        "WHAT_THIS_CANNOT_ANSWER": [
            "whether any cell is PRIVILEGED among ARBITRARY cells -- there is no control family of "
            "arbitrary cells anywhere in this sprint",
            "whether the depth localisation generalises beyond these three heads, which were "
            "selected as load-bearing on basket VALIDATION and are NOT held out",
            "whether per-cell effects ADD -- PR-CSI-012's prereg listed this as unanswerable and "
            "S-307 measured the departure without resolving it",
            "anything about the other 29 heads, about DOMAIN generality, or about the 3 TEST domains",
            "anything behavioural: y_install is a semantic readout, not a refusal endpoint",
        ],
        "MUST_NOT_BE_SAID_IF_POSITIVE": [
            "the binomial p ALONE whenever two admitted heads share a predicted layer -- the "
            "conditional and permutation p's must be quoted beside it and the claim stated with the "
            "weakest (R28/S-312)",
            "that cell (L,h) is 'the writer' -- this tests the SCREEN's prediction, not a cell's "
            "privilege among arbitrary cells; there is still no control family of arbitrary cells",
            "that the screen is a validated cell selector IN GENERAL -- at most this makes the "
            "intervention-verified sample 3 more heads, on a second codeword, and all of them were "
            "selected as load-bearing on basket VALIDATION",
            "anything about the other 29 heads, or about DOMAIN generality, or about TEST",
        ],
        "MUST_NOT_BE_SAID_IF_NULL": [
            "that the basket result is withdrawn -- a failure to transfer across codewords is a "
            "statement about TRANSFER, and S-306/S-307 stand on their own data",
            "that the screen is useless -- a null here bounds it to the codeword it was computed on",
            "'underpowered' without quoting K, the dropped heads and their measured power",
        ],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="configs/dcs_csi_pr016_cell_census_button.json")
    a = ap.parse_args()
    screen_md5 = verify_screen_literal()
    h19 = head19_bar_prediction()
    print("[pr016] head 19 button prediction from PR-013 %s: E=%+.6f -> predicted bar %.6f"
          % (h19["arm_in_pr013"], h19["E"], h19["predicted_bar"]))
    pr = build(screen_md5, h19)

    assert "head_sets" not in pr and "control_prefix" not in pr and "n_controls" not in pr
    assert len(pr["cell_sets"]) == len(HEADS) * (len(BAND) + 1)
    assert pr["n_arms_per_split"] == len(pr["cell_sets"]) + 2 == 32
    for h in HEADS:                       # the bar source arms must be full bands, and unique
        assert sorted(pr["cell_sets"]["HD_%d" % h]) == sorted([[L, h] for L in BAND])
    assert sum(1 for v in pr["cell_sets"].values() if len(v) == 1) == 27
    for b in pr["base_arms"]:
        assert b not in pr["cell_sets"]

    atomic_write_json(a.out, pr)
    print("[pr016] %d arms = BC_BASE + BC_KO + 3 HD_ (9 cells each) + 27 single cells"
          % pr["n_arms_per_split"])
    print("[pr016] wrote %s (%d bytes)  md5 %s" % (a.out, os.path.getsize(a.out), _md5(a.out)))


if __name__ == "__main__":
    main()
