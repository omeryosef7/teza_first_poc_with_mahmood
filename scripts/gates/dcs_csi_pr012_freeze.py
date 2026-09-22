"""Freeze PR-CSI-012 -- the PER-HEAD CENSUS for basket. S-245 designed it; this emits it.

⛔ THIS IS NOT A RANK TEST AND THE PREREG SAYS SO IN THREE PLACES.
S-245 established that a rank test among the eight HD_TOPK heads CANNOT certify: 8 singletons give an
attainable floor of 1/8 = 0.125, which fails alpha = 0.05 for ANY effect size. And testing the post-hoc
winners ~{2,19} would be selection on the validation data that generated the hypothesis. So the
deliverable here is 32 EFFECTS WITH CIs -- a MAP -- and there is no p-value, no candidate and no control
family. `control_prefix` and `n_controls` are DELIBERATELY ABSENT so that the rank-test tooling (W4,
gate 0, the GATE 0 sweep) REFUSES this prereg rather than inventing a family from it.

⚠ AND THE DOSE IDENTITY IS BLIND HERE. Measured from PR-011's landed arms: HD_KO (all 32 band heads)
records a median of 2016.0 prefill edits and a K-head arm records K x 2016 (the all-head arm never
expands -- S-215). A SINGLETON therefore records 1 x 2016 = 2016.0, WHICH IS EXACTLY HD_KO'S COUNT.
The realised-dose check that guarded PR-010 and PR-011 cannot tell a singleton from the all-head arm,
so this prereg requires the arm's own recorded `knockout_heads` to be asserted against the head set
(the argv gate already does exactly that -- R20-1 verified it on 20 arms, 0 mismatches).
"""
import argparse, hashlib, json, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dcs_csi_pr010_freeze import atomic_write_json      # reuse; never re-implement the writer

N_HEADS = 32


def build(screen_path, prereg_id, hd_topk, hd_botk, gate_path, gate_pearson):
    with open(screen_path, "rb") as fh:
        blob = hashlib.md5(fh.read()).hexdigest()[:8]
    screen = json.load(open(screen_path))

    hs = {}
    for h in range(N_HEADS):
        hs["SINGLE_%02d" % h] = [h]
    for h in hd_topk:
        hs["LOO_%02d" % h] = sorted(x for x in hd_topk if x != h)
    hs["HD_TOPK"] = list(hd_topk)
    hs["HD_BOTK"] = list(hd_botk)

    singles = sorted(k for k in hs if k.startswith("SINGLE_"))
    loos = sorted(k for k in hs if k.startswith("LOO_"))
    assert len(singles) == 32 and len(loos) == len(hd_topk) == 8
    for k in loos:
        assert len(hs[k]) == 7, k
    # every LOO is HD_TOPK minus exactly one member, and the 8 LOOs are distinct
    assert len({tuple(hs[k]) for k in loos}) == 8
    for k in loos:
        assert set(hs[k]) < set(hd_topk) and len(set(hd_topk) - set(hs[k])) == 1

    return {
        "id": prereg_id,
        "title": "Per-head CENSUS for basket: measure every single-head knockout and every "
                 "leave-one-out of HD_TOPK. A MAP, not a verdict.",
        "frozen_utc_date": "2026-09-22",
        "design_ref": "sprint log S-245 (design), S-243 section 6 + S-244 (motivation), "
                      "reports/DCS_CSI_PHASE3_HEAD_CIRCUIT_DESIGN.md sections 4-6 (endpoint/arm shape)",
        "endpoint": "y_install; concept-free semantic_one_word; cell C; n_examples 4",
        "statistical_unit": "DOMAIN (never the row); button is NEVER pooled with basket",
        "intervention": {"intervene": "demo_all:attn_knockout:6-14:1.0",
                         "knockout_scope": "target_surface_row_only", "band": "6-14"},
        "split": "validation",
        "split_justification":
            "TRAIN selected HD_TOPK, so a TRAIN census would restate the selection. VALIDATION is used "
            "because a CENSUS SELECTS NOTHING -- every head is measured, so there is no multiplicity to "
            "correct and no winner chosen on this split. See NO_RANK_TEST and SELECTION_RE_ENTERS_WHEN.",

        "NO_RANK_TEST":
            "There is NO candidate, NO control family, NO rank and NO p-value in this preregistration. "
            "A rank among the 8 HD_TOPK singletons has an attainable floor of 1/8 = 0.125 and therefore "
            "CANNOT clear alpha = 0.05 for any effect size (S-245). `control_prefix` and `n_controls` "
            "are ABSENT ON PURPOSE so the rank-test tooling refuses this file instead of inventing a "
            "family from it.",
        "CENSUS_DELIVERABLE":
            "32 single-head effects E(SINGLE_h) = mean over domains of (y_install(SINGLE_h) - "
            "y_install(HD_BASE)), each with a domain-clustered bootstrap ci95; plus 8 leave-one-out "
            "effects E(LOO_h); plus HD_KO as the all-32 denominator and HD_TOPK/HD_BOTK for continuity "
            "with D32/D33. Reported as a table, ordered by point estimate, WITH the CIs.",
        "SELECTION_RE_ENTERS_WHEN":
            "the moment any single head is singled out for a claim. Any CONFIRMATORY per-head claim "
            "requires a HELD-OUT AXIS: the 3 untouched TEST domains, or -- preferred, because it is a "
            "genuine replication rather than a reused split -- the `button` codeword, whose banks "
            "already exist. This preregistration licenses a MAP and explicitly does not license "
            "'head X is the writer'.",
        "WHAT_THIS_CANNOT_ANSWER": [
            "which (layer, head) CELL carries the effect -- the band 6-14 is knocked out as a whole, "
            "exactly as in D32; this census is over HEAD INDICES, not cells",
            "whether per-head effects ADD. Singletons measure each head alone and LOOs measure each "
            "head's marginal contribution to the 8-set; a gap between the two is interpretable but a "
            "full interaction model over 2^8 subsets is not run and is not claimed",
            "anything about a head that matters OUTSIDE the band or off p* -- inherited from the "
            "screen's site choice (S-244's own CANNOT_ANSWER)",
            "whether the AtP screen or S-243/6's gap statistic was right. The census REPLACES both "
            "surrogates with an intervention; it does not adjudicate between them retrospectively"
        ],

        "DOSE_IDENTITY_IS_BLIND_HERE":
            "Measured from PR-011's landed arms: HD_KO records median 2016.0 prefill edits and a K-head "
            "arm records K x 2016 (the all-head arm never expands, S-215). A SINGLETON records "
            "1 x 2016 = 2016.0 -- IDENTICAL TO HD_KO. The realised-dose check that guarded PR-010 and "
            "PR-011 therefore CANNOT distinguish a singleton arm from the all-head arm. Arm identity on "
            "this family must be asserted from the run's own recorded `knockout_heads` against "
            "head_sets, which the argv gate already does (R20-1: 20 arms, 0 mismatches). Expected "
            "counts: SINGLE_* 2016.0, LOO_* 14112.0 (7x), HD_TOPK/HD_BOTK 16128.0 (8x), HD_KO 2016.0, "
            "HD_BASE 0.",

        "head_sets": hs,
        "n_arms_per_split": 2 + len(singles) + len(loos) + 2,
        "arms": {
            "HD_BASE": "no --intervene; the clean reference (--base-arm)",
            "HD_KO": "--knockout-heads omitted = all 32 band heads; the denominator",
            "SINGLE_hh": "--knockout-heads <h>; one head, for every h in 0..31",
            "LOO_hh": "--knockout-heads = HD_TOPK minus head h; 7 heads, for every h in HD_TOPK",
            "HD_TOPK": "the D32/D33 candidate, re-run here for continuity",
            "HD_BOTK": "the D32/D33 comparator, re-run here as the noise scale"
        },
        "population": {"validation_domains": 23, "validation_expect_n": 230,
                       "test_domains": 3, "test_note": "TEST is NEVER touched by this preregistration"},
        "screen_provenance": {
            "screen": screen_path, "screen_blob": blob,
            "n_rows_used": screen.get("n_rows_used"), "n_domains": screen.get("n_domains"),
            "note": "recorded for provenance ONLY. The census does not use S[h] to order, select or "
                    "weight anything -- S-245 is the reason this family exists."},
        "gate2_attribution_trustworthiness": {"artifact": gate_path, "pearson": gate_pearson,
                                              "note": "already passed; carried forward unchanged"},
        "VOID_CONDITIONS": [
            "1. compared arms not all on one GPU architecture (PR-CSI-003 precedent; S-119/S-121)",
            "2. attn_implementation not eager on any arm",
            "3. any arm's recorded knockout_heads not equal to its head_sets entry (the ONLY arm-identity "
            "check that works on this family -- see DOSE_IDENTITY_IS_BLIND_HERE)",
            "4. src/boombness/score_behavior.py edited while any arm of this family is running",
            "5. a TEST domain appearing in any arm",
            "6. the read amended after any number from this family has been seen"
        ],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--screen", default="outputs/boombness/dcs_csi/w1_screen_train_basket_916132.json")
    ap.add_argument("--from-prereg", default="configs/dcs_csi_pr010_head_causal_basket.json",
                    help="HD_TOPK/HD_BOTK are taken from here, NOT re-derived (they are frozen)")
    ap.add_argument("--pr-id", default="PR-CSI-012")
    ap.add_argument("--out", default="configs/dcs_csi_pr012_head_census_basket.json")
    ap.add_argument("--check", action="store_true", help="build and validate; write nothing")
    a = ap.parse_args()

    src = json.load(open(a.from_prereg))
    topk, botk = src["head_sets"]["HD_TOPK"], src["head_sets"]["HD_BOTK"]
    g = src["gate2_attribution_trustworthiness"]
    pr = build(a.screen, a.pr_id, topk, botk, g["artifact"], g["pearson"])

    # the refusals the rank tooling must produce on this file
    assert "control_prefix" not in pr and "n_controls" not in pr, "census must carry no control family"
    assert "attainable_floor" not in pr, "census has no floor because it has no rank"
    print("[pr012] id            = %s" % pr["id"])
    print("[pr012] HD_TOPK       = %s   (from %s, not re-derived)" % (topk, a.from_prereg))
    print("[pr012] singletons    = 32   LOO = %d   total arms = %d"
          % (len([k for k in pr["head_sets"] if k.startswith("LOO_")]), pr["n_arms_per_split"]))
    print("[pr012] control_prefix/n_controls/attainable_floor: ABSENT (by design)")
    if a.check:
        print("[pr012] --check: validated, nothing written"); return
    n = atomic_write_json(a.out, pr)
    print("[pr012] wrote+verified %s (%d bytes)" % (a.out, n))
    print("[pr012] md5 = %s" % hashlib.md5(open(a.out, "rb").read()).hexdigest())


if __name__ == "__main__":
    main()
