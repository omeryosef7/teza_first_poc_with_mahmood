"""Freeze PR-CSI-018 -- the per-CELL census of SIX fresh button heads whose screen prediction is NOT L14.

WHY THIS FAMILY EXISTS. PR-CSI-016 asked whether the basket TRAIN screen's per-cell prediction transfers
to BUTTON and returned CANNOT ANSWER: both its admitted heads predicted L14, so a shared top-of-band
bias and a correct screen were indistinguishable (S-317). S-317 concluded that was STRUCTURAL. S-319
WITHDREW that: joining the screen (an argmax for all 32 heads) with PR-CSI-013's RANDOM control draws
(21 heads measured on button validation) yields SIX live heads whose prediction is not L14, over four
distinct layers. S-320 re-derived their exact S-311 bars and all six survive the 1.5 gate.

THE CANDIDATES, and every exclusion has a reason recorded rather than a silence:
  INCLUDED  6 -> L11 | 11 -> L8 | 20 -> L11 | 24 -> L10 | 27 -> L10 | 29 -> L6
  EXCLUDED  17, 19, 23 -- PR-CSI-016 ALREADY measured their button cells. Head 19's argmax is known to
            be L14 and to match. Counting a known success as a fresh draw is selection on data already
            read, and the cleanest possible way to manufacture a p (S-320).
  EXCLUDED  16 -> L14 -- live and fresh, but it predicts THE LAYER THE SPANNING RULE EXISTS TO GUARD
            AGAINST. PR-CSI-016 measured that an L14 prediction can match for reasons unrelated to the
            screen. Including it would raise the permutation floor from 0.00556 to 0.00079, and both
            clear alpha by a wide margin, so the floor is NOT the binding constraint -- keeping every
            candidate's prediction out of the adversary's favoured layer is worth more than the floor.
  EXCLUDED  10 (1.45) and 28 (1.25) -- below the preregistered 1.5 admission ratio on the EXACT bars.

THE PRIMARY. For each ADMITTED head let Lhat(h) be the argmax over its nine band cells of |E|. M is the
number whose Lhat equals the frozen screen prediction. Three p-values are reported and THE CLAIM IS
STATED WITH THE WEAKEST (S-312):
  binomial     P(Binom(K, 1/9) >= M)
  conditional  the same over heads whose predicted layer is unique among the admitted
  permutation  over distinct assignments of the prediction MULTISET {L8, L11, L6, L11, L10, L10}
               -- 180 of them, floor 0.00556. This is the one a shared band bias CANNOT fake, because
               a bias says nothing about WHICH head gets which layer.
The SPANNING RULE stands: matching heads must not all share one band layer, or CANNOT ANSWER.

THE BARS are a frozen RULE (S-311), computed from each head's own whole-head HD_<h> arm in THIS family,
because a bar must come from the family it judges. PR-CSI-013 already measured those same whole-head
arms, so their values are frozen here as a VOID condition rather than a hope: S-318 demonstrated that
PR-016's HD_19 reproduced PR-013's BT_CTRL_01 BIT-IDENTICALLY across two jobs and two NODES, so
anything other than exact reproduction means the population, bank, exclusions or model revision drifted.
"""
import argparse, hashlib, json, math, os, sys
from collections import Counter
from math import comb, factorial

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dcs_csi_pr010_freeze import atomic_write_json      # reuse; never re-implement the writer

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DOSE_UNIT = 2016
BAND = [6, 7, 8, 9, 10, 11, 12, 13, 14]
HEADS = [6, 11, 20, 24, 27, 29]
CELL_MAPPED_ON_BUTTON = [17, 19, 23]          # PR-CSI-016; excluded as known draws
SCREEN_ARTIFACT = "outputs/boombness/dcs_csi/w1_screen_train_basket_916132.json"
PR013_REPORT = "reports/DCS_CSI_PR013_BUTTON_HEAD_validation.json"
PR013_PREREG = "configs/dcs_csi_pr013_button_head_replication.json"
ALPHA = 0.05
ADMIT_RATIO = 1.5
Z = 1.96


def _md5(p):
    with open(p, "rb") as fh:
        return hashlib.md5(fh.read()).hexdigest()


def binom_tail(M, K, p):
    return sum(comb(K, i) * p ** i * (1 - p) ** (K - i) for i in range(M, K + 1))


def perm_assignments(layers):
    n = factorial(len(layers))
    for v in Counter(layers).values():
        n //= factorial(v)
    return n


def screen_predictions():
    """Re-derived from the 288-cell grid, never a literal. R27 filed the un-pinned literal in the
    PR-015 freeze script as a MINOR; PR-016 fixed it and this inherits the fix."""
    p = os.path.join(REPO, SCREEN_ARTIFACT)
    if not os.path.exists(p):
        sys.exit("REFUSING: the screen artefact %r does not exist (S-167c)." % SCREEN_ARTIFACT)
    scr = json.load(open(p))
    if scr.get("split") != "train" or scr.get("codeword") != "basket":
        sys.exit("REFUSING: the screen is split=%r codeword=%r; the cross-split, cross-codeword claim "
                 "requires train/basket." % (scr.get("split"), scr.get("codeword")))
    atp = scr["AtP_by_cell"]
    out = {}
    for h in HEADS:
        prof = {L: atp["%d,%d" % (L, h)] for L in BAND}
        order = sorted(BAND, key=lambda L: -abs(prof[L]))
        if order[0] == 14:
            sys.exit("REFUSING: head %d's screen argmax re-derives to L14, but this family is defined "
                     "as the NON-L14 heads. The candidate set has drifted from S-319/S-320." % h)
        out[str(h)] = {"layer": order[0],
                       "margin_over_runner_up": abs(prof[order[0]]) / max(abs(prof[order[1]]), 1e-12),
                       "signed_atp": prof[order[0]]}
    return out, _md5(p)


def pr013_whole_head():
    """PR-CSI-013's measured button whole-head effects for these heads, DERIVED not hardcoded."""
    rep = json.load(open(os.path.join(REPO, PR013_REPORT)))
    hs = json.load(open(os.path.join(REPO, PR013_PREREG)))["head_sets"]
    a2h = {}
    for arm, v in hs.items():
        flat = []
        for x in (v if isinstance(v, list) else [v]):
            flat.extend(x if isinstance(x, (list, tuple)) else [x])
        if len(set(flat)) == 1:
            a2h[int(flat[0])] = arm
    out = {}
    for h in HEADS:
        arm = a2h.get(h)
        if arm is None or arm not in rep["E"]:
            sys.exit("REFUSING: PR-CSI-013 has no single-head arm for head %d, so its VOID reference "
                     "cannot be derived and this file will not invent one." % h)
        lo, hi = rep["ci95"][arm]
        out[str(h)] = {"pr013_arm": arm, "E": rep["E"][arm], "ci95": [lo, hi],
                       "ci95_excludes_0": not (lo < 0 < hi)}
    return out


def build(screen, screen_md5, ref):
    cells = {}
    for h in HEADS:
        cells["HD_%d" % h] = [[L, h] for L in BAND]
        for L in BAND:
            cells["BF_H%d_L%02d" % (h, L)] = [[L, h]]
    preds = [screen[str(h)]["layer"] for h in HEADS]
    n_assign = perm_assignments(preds)
    per_head = {str(h): {"bar_source_arm": "HD_%d" % h,
                         "screen_predicted_layer": screen[str(h)]["layer"],
                         "screen_margin_over_runner_up": screen[str(h)]["margin_over_runner_up"],
                         "pr013_whole_head_REFERENCE": ref[str(h)]} for h in HEADS}
    return {
        "id": "PR-CSI-018",
        "title": "Per-CELL census of six fresh BUTTON heads whose basket-TRAIN screen prediction is NOT "
                 "L14: does the screen's cell prediction transfer across codewords, on heads where a "
                 "band-edge bias cannot fake the answer?",
        "frozen_utc_date": "2026-09-23",
        "EMITTED_MECHANICALLY_BY": "scripts/gates/dcs_csi_pr018_freeze.py",
        "design_ref": "S-317 (PR-016's CANNOT ANSWER and why); S-319 (the withdrawal of the structural "
                      "block, and the six-head inventory); S-320 (exact S-311 bars; head 19 excluded "
                      "as a known draw); S-312 (the robustness co-primaries); S-310 (the 9-cell/KO "
                      "collision); S-311 (the bar as a rule)",
        "split": "validation", "codeword": "button", "concept": "bomb",
        "statistical_unit": "DOMAIN for every E (23 domains, 230 rows, never the row). THE TEST UNIT "
                            "IS THE HEAD.",
        "endpoint": "y_install; concept-free semantic_one_word; cell C; n_examples 4",
        "heads": HEADS, "band": "6-14", "layers": BAND,
        "base_arms": ["BF_BASE", "BF_KO"],
        "cell_sets": cells,
        "n_arms_per_split": len(cells) + 2,
        "intervention": {"intervene": "demo_all:attn_knockout:6-14:1.0",
                         "knockout_scope": "target_surface_row_only", "band": "6-14"},
        "arms": {
            "BF_BASE": "no --intervene; the clean reference",
            "BF_KO": "--intervene with NO selector = all 32 heads x 9 band layers; the denominator",
            "HD_<h>": "--knockout-cells for ALL NINE band cells of head h. Supplies that head's bar "
                      "(S-311 rule) and its ADMISSION, and re-measures the whole-head effect "
                      "PR-CSI-013 already recorded -- see VOID condition 8. EXCLUDED from the depth "
                      "map and from every per-cell count.",
            "BF_H<h>_L<ll>": "--knockout-cells <ll>:<h> -- ONE cell",
        },
        "CANDIDATE_PROVENANCE": {
            "nominated_on": "the basket TRAIN screen (layer) and PR-CSI-013's button whole-head "
                            "magnitude (admission eligibility). NEITHER uses any button CELL data.",
            "why_these_six": "live on button (|E|/bar >= 1.5 on the EXACT S-311 bars, ci95 excluding "
                             "0) AND a screen prediction that is NOT L14",
            "EXCLUDED_already_cell_mapped": {
                "heads": CELL_MAPPED_ON_BUTTON,
                "why": "PR-CSI-016 measured their button cells. Head 19's argmax is KNOWN to be L14 "
                       "and to match. Counting a known success as a fresh draw is selection on data "
                       "already read (S-320).",
            },
            "EXCLUDED_head_16": "live and fresh, but predicts L14 -- the layer the spanning rule "
                                "exists to guard against, and PR-CSI-016 measured that an L14 "
                                "prediction can match for reasons unrelated to the screen. Its "
                                "inclusion would move the permutation floor 0.00556 -> 0.00079; both "
                                "clear alpha, so the floor is not the binding constraint and keeping "
                                "every prediction out of the adversary's layer is worth more.",
            "EXCLUDED_below_gate": {"10": 1.45, "28": 1.25},
            "⚠ NOT_HELD_OUT": "the screen is TRAIN and basket, so the LAYER is held out on split AND "
                              "codeword. The HEAD SET is chosen using PR-CSI-013's button validation "
                              "magnitudes -- the same 23 domains this family reads. That is admission "
                              "eligibility, not the tested quantity, but it is NOT held out and must "
                              "not be described as such.",
        },
        "SCREEN_PREDICTIONS_ON_RECORD_BEFORE_THIS_FAMILY": {
            "predictions": {k: "L%d" % v["layer"] for k, v in screen.items()},
            "artifact": SCREEN_ARTIFACT, "artifact_md5_at_freeze": screen_md5,
            "RE_DERIVED_BY_THIS_SCRIPT": "yes -- argmax_L |AtP_by_cell[L,h]| over the 288-cell grid; a "
                                         "drift to L14 on any head is a REFUSAL",
            "distinct_layers": sorted(set(preds)),
        },
        "PRIMARY": {
            "statistic": "M = number of ADMITTED heads whose argmax band layer by |E| equals that "
                         "head's frozen screen-predicted layer",
            "null": "the screen's per-cell prediction is unrelated to the button depth profile",
            "alpha": ALPHA,
            "binomial": "P(Binom(K, 1/9) >= M)",
            "conditional": "the same over ADMITTED heads whose predicted layer is unique among the "
                           "admitted set",
            "permutation": {
                "space": "distinct assignments of the prediction MULTISET to the admitted heads",
                "multiset_at_K6": sorted("L%d" % L for L in preds),
                "n_distinct_assignments_at_K6": n_assign,
                "floor_at_K6": 1.0 / n_assign,
                "WHY_IT_IS_THE_LOAD_BEARING_ONE": "a shared band-edge bias cannot fake it, because a "
                                                  "bias says nothing about WHICH head gets which "
                                                  "layer. PR-CSI-016 died precisely here.",
            },
            "SUCCESS": "the WEAKEST of the three p-values <= 0.05 AND the spanning rule satisfied",
            "FAILURE": "the weakest p > 0.05 with K >= 3",
            "SPANNING_RULE": "the MATCHING heads must not all share one band layer, or CANNOT ANSWER "
                             "whatever the p-values say",
            "HOW_THE_CLAIM_MUST_BE_STATED": "with the WEAKEST of the three, each named. Quoting the "
                                            "binomial alone is FORBIDDEN.",
            "⛔ NO_POST_HOC_SHARPNESS_SUBSETTING": {
                "the_temptation": "the six screen predictions differ wildly in how DECISIVE they are. "
                                  "Margins over the runner-up: head 6 5.96x, 24 4.70x, 27 1.58x, "
                                  "11 1.51x, 29 1.26x, 20 1.07x. Head 20's is effectively a coin flip "
                                  "between L11 and its runner-up, and S-307 recorded that a near-tie "
                                  "which happens to land right is far weaker corroboration than a "
                                  "decisive peak.",
                "why_there_is_NO_gate": "every sharpness gate changes whether this family can certify "
                                        "AT ALL, which makes the threshold a free parameter tuned by "
                                        "its effect on the floor: margin>=1.25 leaves 5 heads and a "
                                        "floor of 0.0167; margin>=1.5 leaves 4 and a floor of 0.0833, "
                                        "which CANNOT clear alpha; margin>=2.0 leaves 2 and 0.5. "
                                        "Choosing among those by looking at the floor is exactly the "
                                        "selection this sprint forbids, so NO sharpness gate is "
                                        "applied and all six heads are admitted on magnitude alone.",
                "why_that_is_SOUND_and_not_merely_convenient": "a flat screen prediction is a "
                                                               "near-random one, which is precisely "
                                                               "what the PERMUTATION null models. Flat "
                                                               "predictions therefore cost POWER, not "
                                                               "VALIDITY -- they make a true effect "
                                                               "harder to detect and cannot manufacture "
                                                               "a false one.",
                "FORBIDDEN_AFTER_THE_READ": "reporting any margin-restricted subset of the heads as "
                                            "the result, or as a rescue of a null, or as a "
                                            "qualification of a positive. The margins are frozen HERE, "
                                            "per head, precisely so that a post-hoc subset can be "
                                            "recognised as one. If a sharpness analysis is wanted it "
                                            "is a NEW preregistration on NEW heads.",
            },
        },
        "ADMISSION": {
            "rule": "head h is ADMITTED iff its whole-head arm HD_<h> has a ci95 excluding 0 AND "
                    "|E(HD_<h>)| >= %.1f x bar(h)" % ADMIT_RATIO,
            "ratio": ADMIT_RATIO,
            "COMPUTED_FROM": "the whole-head arm ALONE, never from the cells",
            "A_DROPPED_HEAD_IS_NOT_A_MISS": "it leaves K and is reported with its measured power",
            "EXPECTED": "all six are expected to be admitted -- S-320 measured their EXACT S-311 "
                        "|E|/bar at 2.86 / 2.85 / 2.49 / 2.42 / 1.84 / 1.54 on PR-CSI-013's arms. A "
                        "head that fails here when PR-013 says it should not is itself a finding.",
        },
        "DETECTABILITY_PREREGISTERED_PER_HEAD": {
            "method": "S-311: the bar is a RULE, computed from this family's own whole-head arm",
            "BAR_IS_A_RULE": {
                "z": Z,
                "rule": "bar(h) = z * SD(per-domain paired delta of HD_<h> minus the base arm, "
                        "ddof=1) / sqrt(n_domains)",
                "DDOF_IS_PINNED": "S-318 verified ddof=1 reproduces PR-CSI-016's published bars "
                                  "exactly and ddof=0 does not",
                "WHY_NOT_A_NUMBER": "a bar must come from the family it judges. PR-CSI-013's values "
                                    "are frozen as VOID condition 8 instead.",
            },
            "per_head": per_head,
            "⚠ NOT_HELD_OUT": "each bar comes from this family's own whole-head arm on the same 23 "
                              "domains the cells are read on. A DIFFERENT ARM, and only its SPREAD is "
                              "used -- not circular in the strong sense, but NOT held out.",
            "NOT_THE_PRIMARY": "the primary is the argmax agreement, which needs no bar. The bars "
                               "serve ADMISSION and the descriptive depth map only.",
        },
        "DOSE_EXPECTATION": {
            "per_cell_prefill_edits": DOSE_UNIT // len(BAND),
            "whole_head_arm_prefill_edits": DOSE_UNIT,
            "derivation": "DOSE_UNIT %d / %d band layers" % (DOSE_UNIT, len(BAND)),
            "STATUS": "MEASURED (S-299 on nine cells, S-306 on 27 more, S-317 on 27 more)",
            "⚠ BLIND_AS_AN_IDENTITY": "all 54 cell arms expect 224 and all six HD_ arms expect 2016, "
                                      "the SAME dose as BF_KO. Identity comes from each arm's own "
                                      "knockout_cells ONLY (S-310).",
        },
        "population": {"validation_domains": 23, "validation_expect_n": 230, "test_domains": 23,
                       "test_note": "TEST is NEVER touched. S-314: it is ALSO already spent and "
                                    "selection-contaminated, so it is not an axis even in principle.",
                       "SAME_DOMAINS_AS_BASKET": "S-256; this controls the CODEWORD, not the domains"},
        "NO_RANK_TEST": "There is no candidate cell, no control family of arbitrary cells and no rank. "
                        "The PRIMARY is a per-head ARGMAX agreement against a prediction frozen on a "
                        "different split AND codeword. control_prefix and n_controls are DELIBERATELY "
                        "ABSENT so the rank tooling refuses this prereg.",
        "CENSUS_DELIVERABLE": "54 single-cell effects E(BF_H<h>_L<ll>) = mean over domains of "
                              "(y_install(cell) - y_install(BF_BASE)), each with a bootstrap ci95; six "
                              "whole-head HD_<h> arms supplying the bars and ADMISSION, EXCLUDED from "
                              "every per-cell count; and the BF_KO denominator.",
        "SELECTION_RE_ENTERS_WHEN": "any single cell is named as 'the' site. The PRIMARY tests a "
                                    "PREDICTION made before the data existed, which is why it carries "
                                    "a p; naming a winner afterwards is selection on the data that "
                                    "produced it.",
        "DOSE_IDENTITY_IS_BLIND_HERE": "54 cell arms share 224 and seven arms share 2016 (six HD_ plus "
                                       "BF_KO). Identity comes from knockout_cells ONLY (S-292/S-310).",
        "WHAT_THIS_CANNOT_ANSWER": [
            "whether any cell is PRIVILEGED among ARBITRARY cells -- there is no control family of "
            "arbitrary cells anywhere in this sprint",
            "anything about the SOURCE of the effect -- S-316 blocked that family pending a mass "
            "measurement that has not been made",
            "whether the screen predicts for heads that are NULL on button; this family admits only "
            "live ones, by design",
            "anything about the other 26 heads, DOMAIN generality, or TEST",
            "anything behavioural: y_install is a semantic readout, not a refusal endpoint",
        ],
        "VOID_CONDITIONS": [
            "1. arms split across GPU architectures (S-037/S-119)",
            "2. attn_implementation != eager on any arm",
            "3. any TEST domain in any arm",
            "4. BF_BASE carrying any intervention flag",
            "5. an arm whose recorded knockout_cells != this prereg's cell_sets entry for it",
            "6. score_behavior.py or src/ edited while these arms are in flight",
            "7. any single-cell arm recording a dose other than %d, or any HD_ arm other than %d"
            % (DOSE_UNIT // len(BAND), DOSE_UNIT),
            "8. ⚠ PROVENANCE: any HD_<h> arm whose E differs from PR-CSI-013's measurement of the "
            "SAME head, codeword and split by more than 1e-6. S-318 demonstrated bit-identical "
            "reproduction across two jobs and two NODES, so a difference means the population, bank, "
            "exclusions or model revision has drifted and nothing here is readable.",
            "9. BF_KO recording a non-empty knockout_cells (S-310)",
            "10. the read amended after any number is seen",
        ],
        "MUST_NOT_BE_SAID_IF_POSITIVE": [
            "the binomial p alone -- the claim is stated with the WEAKEST of the three (S-312)",
            "that cell (L,h) is 'the writer' -- this tests the SCREEN's prediction, not a cell's "
            "privilege among arbitrary cells",
            "that the screen is a validated cell selector IN GENERAL -- at most this adds six heads on "
            "a second codeword, all chosen because they were live there",
            "anything about heads that are NULL on button, which this family excludes by construction",
        ],
        "MUST_NOT_BE_SAID_IF_NULL": [
            "that the basket result is withdrawn -- S-306/S-307 stand on their own data; this is "
            "about TRANSFER",
            "that PR-CSI-016 is explained -- it returned CANNOT ANSWER and still does",
            "'underpowered' without quoting K, the dropped heads and their MEASURED power",
        ],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="configs/dcs_csi_pr018_cell_census_button_nonL14.json")
    a = ap.parse_args()

    for h in HEADS:
        if h in CELL_MAPPED_ON_BUTTON:
            sys.exit("REFUSING: head %d is already cell-mapped on button (PR-CSI-016). Its argmax is "
                     "KNOWN, so including it counts a known draw. (S-320)" % h)
    screen, screen_md5 = screen_predictions()
    ref = pr013_whole_head()
    for h in HEADS:
        if not ref[str(h)]["ci95_excludes_0"]:
            sys.exit("REFUSING: head %d's PR-CSI-013 button ci95 crosses 0, so it is not an "
                     "admission-eligible candidate." % h)
    pr = build(screen, screen_md5, ref)

    assert "head_sets" not in pr and "control_prefix" not in pr and "n_controls" not in pr
    assert len(pr["cell_sets"]) == len(HEADS) * (len(BAND) + 1)
    assert pr["n_arms_per_split"] == len(pr["cell_sets"]) + 2 == 62
    assert sum(1 for v in pr["cell_sets"].values() if len(v) == 1) == len(HEADS) * len(BAND)
    for h in HEADS:
        assert sorted(pr["cell_sets"]["HD_%d" % h]) == sorted([[L, h] for L in BAND])
    for b in pr["base_arms"]:
        assert b not in pr["cell_sets"]

    atomic_write_json(a.out, pr)
    preds = [screen[str(h)]["layer"] for h in HEADS]
    print("[pr018] screen re-derived from %s (md5 %s)" % (SCREEN_ARTIFACT, screen_md5))
    for h in HEADS:
        print("[pr018]   head %-3d -> L%-3d (margin %.2fx over runner-up)   PR-013 E=%+.6f"
              % (h, screen[str(h)]["layer"], screen[str(h)]["margin_over_runner_up"],
                 ref[str(h)]["E"]))
    print("[pr018] prediction multiset %s -> %d distinct assignments, permutation floor %.5f"
          % (sorted("L%d" % L for L in preds), perm_assignments(preds), 1.0 / perm_assignments(preds)))
    for K in (6, 5, 4, 3):
        print("[pr018]   K=%d  binomial floor %.3e" % (K, binom_tail(K, K, 1.0 / len(BAND))))
    print("[pr018] %d arms = BF_BASE + BF_KO + %d HD_ (9 cells each) + %d single cells"
          % (pr["n_arms_per_split"], len(HEADS), len(HEADS) * len(BAND)))
    print("[pr018] wrote %s (%d bytes)  md5 %s" % (a.out, os.path.getsize(a.out), _md5(a.out)))


if __name__ == "__main__":
    main()
