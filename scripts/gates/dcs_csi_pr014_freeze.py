"""Freeze PR-CSI-014 -- the PER-CELL CENSUS of h*'s nine band cells, on basket validation.

⛔ THIS IS A CENSUS, NOT THE CONFIRMATORY TEST THE DESIGN ORIGINALLY WANTED, AND THAT IS NOT A
DOWNGRADE MADE FOR CONVENIENCE. `external_md/DCS_CSI_PR014_CELL_LEVEL_DESIGN.md` §5(b) planned a
descriptive pass to pick `L*` and then a 23-arm confirmatory rank test on a held-out axis. **S-294
measured that no admissible axis exists** -- basket validation is where `L*` would be selected; basket
train is contaminated because h* entered `HD_TOPK` by a TRAIN selection; button is where D35 measured h*
at E = -0.003522 with a ci95 crossing zero; the 3 TEST domains need n > 3.8 at the most optimistic
observed `SD/|E|` and n > 6.5-11 at realistic ones; and no third codeword bank exists. So steps 4-5 of
that design are UNREACHABLE and AM-37 records that D32's single-cell caveat cannot be lifted.

What remains is a MAP, and it is worth having for three reasons that do not depend on a rank test:
  1. a depth map of h*'s load at CELL granularity -- strictly finer than D34, which by construction
     cannot say at what depth, since every census arm knocked its head out at all nine layers at once;
  2. it turns the per-cell dose of `DOSE_UNIT / 9 = 224` from a PREDICTION into a MEASUREMENT (S-292);
  3. it is the FIRST intervention test of the screen's per-CELL ordering. S-254 measured rho = +0.7713
     between the screen and the census at HEAD level, but AM-32 also recorded that the same screen
     ranked h* -- the single strongest head -- only 6th, and S-269's claim that h* is dominated by one
     cell at L10 has never been checked against an intervention.

⛔ NO RANK, NO CANDIDATE, NO CONTROL FAMILY, NO p. `control_prefix` and `n_controls` are DELIBERATELY
ABSENT so the rank-test tooling REFUSES this prereg rather than inventing a family from it -- the same
construction PR-CSI-012 used, and the reason `NO_RANK_TEST` is asserted.

⚠ THE DETECTABILITY THRESHOLD IS PREREGISTERED, AND SO IS THE OUTCOME WHERE NOTHING CLEARS IT. S-294
measured the per-domain SD of h*'s nine-cell arm at 0.046933 over 23 domains, so a cell needs
|E| > 1.96*SD/sqrt(23) = 0.019181 to exclude zero -- **38.8% of the whole nine-cell effect**. If the load
is spread evenly (~11% per cell) NO CELL WILL CLEAR THE BAR. That is a coherent, informative outcome --
evidence that the effect is distributed across depth rather than sited at one layer -- and it is written
down HERE, before any arm runs, exactly as `runargs/dcs_csi_pr012_read.txt` preregistered
non-decomposability before AM-36 observed it.

⚠ AND THE DOSE IDENTITY IS BLIND HERE TOO, IN A NEW WAY. A one-cell arm passes --knockout-cells and NOT
--knockout-heads, so its recorded `knockout_heads` is EMPTY -- which `recorded_heads()` maps to "ALL",
because for a head family an omitted flag IS the all-32 arm. Read through the head-level check every
1-cell arm would be certified as the all-32 knockout: a 224-edit arm passing as the 2016-edit
denominator. Identity here therefore comes from `knockout_cells` ONLY (S-292).

h* IS NOT RE-DERIVED. It is READ from PR-CSI-013's prereg, which was itself emitted mechanically under
the rule frozen 2026-09-22 (md5 fae4adc6...) before any census number existed. Re-deriving it here would
be a SECOND definition of the same selection, which is the defect S-246 fixed in four tools at once.
"""
import argparse, hashlib, json, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dcs_csi_pr010_freeze import atomic_write_json      # reuse; never re-implement the writer

DOSE_UNIT = 2016            # MEASURED (S-215, S-246)
# S-294, measured from csi5_census_basket_validation_{HD_BASE,SINGLE_02} via W4's own by_domain.
PER_DOMAIN_SD_9CELL = 0.046933
E_9CELL = -0.049475


def _md5(path):
    with open(path, "rb") as fh:
        return hashlib.md5(fh.read()).hexdigest()


def band_layers(spec_or_band):
    lo, hi = (int(x) for x in str(spec_or_band).split("-"))
    if hi < lo:
        sys.exit("REFUSING: band %r is inverted" % (spec_or_band,))
    return list(range(lo, hi + 1))


def build(src_path, src, codeword, split):
    h_star = src.get("h_star")
    if h_star is None:
        sys.exit("REFUSING: %r carries no h_star. PR-CSI-014's candidate head must be READ from the "
                 "frozen source, never re-derived here (S-246)." % src_path)
    iv = dict(src["intervention"])
    band = iv.get("band") or iv["intervene"].split(":")[2]
    layers = band_layers(band)
    if len(layers) < 2:
        sys.exit("REFUSING: a %d-layer band has no depth structure to map" % len(layers))

    cells = {("CL_L%02d" % L): [[int(L), int(h_star)]] for L in layers}
    per_cell = DOSE_UNIT // len(layers)
    if DOSE_UNIT % len(layers) != 0:
        sys.exit("REFUSING: DOSE_UNIT %d is not divisible by the %d-layer band, so a per-cell dose is "
                 "not an integer and the uniformity assumption is already false (S-292)."
                 % (DOSE_UNIT, len(layers)))
    n_dom = src["population"]["%s_domains" % split]
    thresh = 1.96 * PER_DOMAIN_SD_9CELL / (n_dom ** 0.5)

    return {
        "id": "PR-CSI-014",
        "title": ("Per-CELL census of head %d's %d band cells on %s %s: at what DEPTH does the "
                  "load sit? A MAP, with no rank and no p." % (h_star, len(layers), codeword, split)),
        "frozen_utc_date": "2026-09-23",
        "EMITTED_MECHANICALLY_BY": "scripts/gates/dcs_csi_pr014_freeze.py",
        "design_ref": ("external_md/DCS_CSI_PR014_CELL_LEVEL_DESIGN.md (design); S-294 (the POWER "
                       "result that made steps 4-5 of that design unreachable); S-291/S-292/S-293 "
                       "(the --knockout-cells implementation and its gates)"),
        "split": split,
        "codeword": codeword,
        "statistical_unit": "DOMAIN (never the row); basket is NEVER pooled with button",
        "endpoint": "y_install; concept-free semantic_one_word; cell C; n_examples 4",
        "h_star": int(h_star),
        "h_star_provenance": {
            "read_from": src_path,
            "source_md5": _md5(src_path),
            "source_id": src.get("id"),
            "nomination_rule": src.get("nomination_rule"),
            "nomination_rule_md5": src.get("nomination_rule_md5"),
            "note": ("h* was selected on BASKET by a rule frozen 2026-09-22 BEFORE the census existed. "
                     "It is READ here, not re-derived: a second derivation of one selection is the "
                     "defect S-246 fixed in four tools."),
        },
        "band": band,
        "layers": layers,
        "base_arms": ["CL_BASE", "CL_KO"],
        "cell_sets": cells,
        "n_arms_per_split": len(cells) + 2,
        "intervention": {"intervene": iv["intervene"], "knockout_scope": iv["knockout_scope"],
                         "band": band},
        "arms": {
            "CL_BASE": "no --intervene; the clean reference",
            "CL_KO": ("--intervene with NO selector = all 32 heads x all %d band layers; the "
                      "denominator, and the arm every cell is a fraction of" % len(layers)),
            "CL_L<NN>": "--knockout-cells <NN>:%d -- ONE cell" % h_star,
        },
        "NO_RANK_TEST": ("There is NO candidate, NO control family, NO rank and NO p-value here. A rank "
                         "among the %d layers of one head has an attainable floor of 1/%d = %.4f and "
                         "cannot clear alpha = 0.05 for ANY effect size (design section 2). "
                         "control_prefix and n_controls are DELIBERATELY ABSENT so the rank-test "
                         "tooling refuses this prereg rather than inventing a family from it."
                         % (len(layers), len(layers), 1.0 / len(layers))),
        "DOSE_EXPECTATION": {
            "per_cell_prefill_edits": per_cell,
            "derivation": "DOSE_UNIT %d / %d band layers" % (DOSE_UNIT, len(layers)),
            "STATUS": "PREDICTED, NOT MEASURED",
            "why": ("DOSE_UNIT = 2016 was MEASURED (S-215, S-246). Dividing by the band width assumes "
                    "the edits are spread UNIFORMLY across layers, which cannot be tested from any "
                    "artefact on disk because pair_common sums the hook counters across layers before "
                    "writing them. THIS FAMILY'S FIRST ARM VALIDATES THE ARITHMETIC. If a one-cell arm "
                    "records anything other than %d, the uniformity assumption is REFUTED and every "
                    "cell dose expectation in the sprint must be re-derived before anything is read."
                    % per_cell),
        },
        "DOSE_IDENTITY_IS_BLIND_HERE": (
            "A one-cell arm passes --knockout-cells and NOT --knockout-heads, so its recorded "
            "knockout_heads is EMPTY, which recorded_heads() maps to 'ALL' -- for a HEAD family an "
            "omitted flag IS the all-32 arm. Read through the head-level check every 1-cell arm would "
            "be certified as the all-32 knockout: a %d-edit arm passing as the %d-edit denominator. "
            "Identity here comes from knockout_cells ONLY (S-292), asserted per arm against cell_sets."
            % (per_cell, DOSE_UNIT)),
        "population": dict(src["population"]),
        "DETECTABILITY_PREREGISTERED": {
            "per_domain_SD_of_the_9cell_arm": PER_DOMAIN_SD_9CELL,
            "E_of_the_9cell_arm": E_9CELL,
            "n_domains": n_dom,
            "min_abs_E_for_ci95_to_exclude_0": round(thresh, 6),
            "as_share_of_the_whole_head_effect": round(thresh / abs(E_9CELL), 4),
            "source": "S-294, measured via W4's own by_domain on job 918631's arms",
            "COHERENT_OUTCOME_IF_NOTHING_CLEARS_IT": (
                "If the load is spread evenly across the %d cells (~%.1f%% each) NO CELL CLEARS THE "
                "BAR. That is an informative outcome and is preregistered as coherent HERE, before any "
                "arm runs: it is evidence that the effect is DISTRIBUTED ACROSS DEPTH rather than sited "
                "at one layer. It must NOT be reported as a failed experiment, and it must not be "
                "rescued by dropping to a weaker bar after the fact."
                % (len(layers), 100.0 / len(layers))),
        },
        "CENSUS_DELIVERABLE": (
            "%d cell effects E(CL_L<NN>) = mean over domains of (y_install(cell) - y_install(CL_BASE)), "
            "each with a bootstrap ci95, plus the CL_KO denominator. A MAP of where head %d's load sits "
            "by depth. No head other than %d is measured and no cell of any other head is touched."
            % (len(layers), h_star, h_star)),
        "WHAT_THIS_CANNOT_DO": [
            "certify that any cell is privileged -- there is no rank, no control family and no p",
            "lift D32's caveat 'NOT a claim about any single (layer, head) cell' -- AM-37 records that "
            "this cannot be done with the axes this sprint has",
            "revise D32, D33, D34 or D35 -- a finer map does not retract a coarser measurement",
            "say anything about the other 31 heads, or about any cell of them",
            "say anything about DOMAIN generality -- the %s domains are the same ones basket's other "
            "families used (S-256); the 3 TEST domains remain untouched" % split,
            "reach RUNG 2, 3 or 4 of AM-34's ladder. This is RUNG 1 (necessity) like everything else "
            "in this sprint",
        ],
        "SELECTION_RE_ENTERS_WHEN": (
            "the moment any one cell is singled out for a claim. This census SELECTS NOTHING; naming a "
            "winner afterwards is selection on the data that produced it, and S-294 established there "
            "is no held-out axis on which a confirmatory test of that winner could be read."),
        "VOID_CONDITIONS": [
            "1. compared arms not all on one GPU architecture (PR-CSI-003 precedent)",
            "2. attn_implementation not eager on any arm (a mask edit under SDPA is a silent no-op)",
            "3. any arm's recorded knockout_cells disagreeing with cell_sets",
            "4. CL_BASE carrying any intervention flag (S-260: an all-32 knockout as the clean "
            "reference voided job 918967)",
            "5. any arm knocking out a cell whose layer lies outside the band (it would install no "
            "hook and score as a clean null)",
            "6. score_behavior.py edited while these arms are in flight",
        ],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", default="configs/dcs_csi_pr013_button_head_replication.json",
                    help="the frozen prereg to READ h* from (never re-derived here)")
    ap.add_argument("--codeword", default="basket")
    ap.add_argument("--split", default="validation", choices=("train", "validation"))
    ap.add_argument("--out", default="configs/dcs_csi_pr014_cell_census_basket.json")
    a = ap.parse_args()

    if not os.path.exists(a.source):
        sys.exit("REFUSING: source prereg %r does not exist" % a.source)
    src = json.load(open(a.source))
    if a.split == "train":
        sys.exit("REFUSING: TRAIN selected HD_TOPK, so h* entered this sprint by a TRAIN selection and "
                 "a TRAIN census would restate it. VALIDATION is the only admissible split for a "
                 "census of h*'s cells (the same reason PR-CSI-012 gave).")

    pr = build(a.source, src, a.codeword, a.split)
    print("[pr014] h* = %d  READ FROM %s (md5 %s)"
          % (pr["h_star"], a.source, pr["h_star_provenance"]["source_md5"][:8]))
    print("[pr014] band %s -> %d layers -> %d arms (%s, %s, CL_L%02d..CL_L%02d)"
          % (pr["band"], len(pr["layers"]), pr["n_arms_per_split"],
             pr["base_arms"][0], pr["base_arms"][1], pr["layers"][0], pr["layers"][-1]))
    d = pr["DOSE_EXPECTATION"]
    print("[pr014] per-cell dose %d (%s) -- %s"
          % (d["per_cell_prefill_edits"], d["derivation"], d["STATUS"]))
    t = pr["DETECTABILITY_PREREGISTERED"]
    print("[pr014] a cell must reach |E| > %.6f to exclude 0 on %d domains = %.1f%% of the whole "
          "head effect" % (t["min_abs_E_for_ci95_to_exclude_0"], t["n_domains"],
                           100 * t["as_share_of_the_whole_head_effect"]))
    print("[pr014] if the load is even (~%.1f%%/cell) NOTHING clears the bar -- preregistered as "
          "COHERENT" % (100.0 / len(pr["layers"])))

    # self-checks BEFORE the write: the shape the readers will assert
    assert "head_sets" not in pr, "a cell prereg must not carry head_sets"
    assert "control_prefix" not in pr and "n_controls" not in pr, \
        "control_prefix/n_controls must be ABSENT so the rank tooling refuses this prereg"
    assert len(pr["cell_sets"]) == len(pr["layers"])
    assert all(len(v) == 1 for v in pr["cell_sets"].values()), "every arm here is ONE cell"
    assert all(v[0][1] == pr["h_star"] for v in pr["cell_sets"].values()), "every cell is h*'s"
    assert sorted(v[0][0] for v in pr["cell_sets"].values()) == pr["layers"]
    for b in pr["base_arms"]:
        assert b not in pr["cell_sets"], "a base arm carries no cell list"

    atomic_write_json(a.out, pr)
    print("[pr014] wrote %s (%d bytes)" % (a.out, os.path.getsize(a.out)))
    print("[pr014] md5 = %s" % _md5(a.out))


if __name__ == "__main__":
    main()
