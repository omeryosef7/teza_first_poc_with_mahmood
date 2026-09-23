"""Freeze PR-CSI-015 -- the per-CELL census of D34's OTHER THREE load-bearing heads, basket validation.

WHAT IT ADDS TO D36. PR-CSI-014 mapped head 2's nine band cells and found the load CONCENTRATED: cell
(L10, 2) carries 96.1% of the head's whole effect, and the screen had predicted L10. Two questions follow
and neither can be answered from that one head:

  1. IS CONCENTRATION GENERAL, OR IS HEAD 2 SPECIAL? One head cannot tell the difference between "the
     depth structure of this mechanism is sparse" and "head 2 happens to be sparse".
  2. DOES THE SCREEN'S PER-CELL ORDERING HOLD ANYWHERE ELSE? AM-38 recorded the L10 corroboration as
     n = 1 HEAD and explicitly refused to generalise it. S-269 also read the screen for the other three:
     19 -> L14, 17 -> L14, 23 -> L7. Those are three more falsifiable predictions, already on record
     BEFORE this family runs, and they were written down for a different purpose than testing them.

⛔ THIS IS A CENSUS, exactly as PR-CSI-014 was: 3 heads x 9 layers = 27 cell arms, all nine layers of each
head, so NO CELL IS SELECTED. `NO_RANK_TEST` is declared and `control_prefix`/`n_controls` are absent so
the rank tooling refuses the prereg. AM-37 stands: there is no admissible held-out axis for a confirmatory
cell test, so nothing here can be followed by "and therefore cell X is the writer".

⚠ THE HEADS ARE NOT SELECTED BY THIS FILE EITHER. They are D34's load-bearing four minus head 2, which
PR-CSI-014 already mapped. D34 is a CENSUS (no rank, no p), so "the four heads whose singleton clears the
family's own null anchor" is a descriptive set, not a tested winner -- and this family measures ALL nine
cells of each, adding no selection of its own.

⚠ EVERY HEAD GETS ITS OWN DETECTABILITY BAR, AND THAT IS NOT A DETAIL. S-294 derived head 2's bar from
head 2's OWN per-domain SD. These heads have both smaller effects AND smaller spreads, so one shared bar
would be wrong in both directions:

    head   E(SINGLE)    per-domain SD   bar = 1.96*SD/sqrt(23)   bar as % of |E|
      2    -0.049475       0.046933            0.019181               38.8%
     19    -0.040109       0.025015            0.010223               25.5%
     17    -0.029218       0.022223            0.009082               31.1%
     23    -0.016503       0.016186            0.006615               40.1%

The bars are computed HERE from the published D34 arms via W4's own `by_domain`, and head 2's value is
re-derived as a cross-check: it must reproduce the 0.019181 the PR-CSI-014 prereg froze, or the method has
drifted and this file refuses.

✅ AND THE DESIGN DISCRIMINATES FOR ALL THREE. Under concentration like head 2's (~96% in one cell) the
dominant cell clears its own bar by 2.4x-3.8x; under an even nine-way split it clears for NO head
(0.28x-0.44x). So both outcomes are readable per head, and both are written down before the arms run.
"""
import argparse, hashlib, importlib.util, json, math, os, statistics, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dcs_csi_pr010_freeze import atomic_write_json      # reuse; never re-implement the writer

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DOSE_UNIT = 2016
HEAD_2_FROZEN_BAR = 0.019181          # what configs/dcs_csi_pr014_cell_census_basket.json froze


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _md5(path):
    with open(path, "rb") as fh:
        return hashlib.md5(fh.read()).hexdigest()


def measure_bars(heads, tag_prefix, expect_n, job, base_arm="HD_BASE"):
    """Each head's per-domain SD and detectability bar, from the PUBLISHED census arms.

    Uses W4's own `by_domain` so the endpoint definition is the one definition, never a second one."""
    w4 = _load("w4", os.path.join(REPO, "scripts", "dcs_csi_head_analyze.py"))
    red = _load("red", os.path.join(REPO, "scripts", "dcs_csi_rederive_patch.py"))
    per = {}
    for arm in [base_arm] + ["SINGLE_%02d" % h for h in heads]:
        d = red.strict_run_dir("%s_%s" % (tag_prefix, arm), expect_n, row_file="results.jsonl",
                               require_slurm_jobs=[job])
        per[arm] = w4.by_domain(d)[0]
    doms = sorted(set.intersection(*(set(v) for v in per.values())))
    if not doms:
        sys.exit("REFUSING: no domain common to the census arms")
    out = {}
    for h in heads:
        a = "SINGLE_%02d" % h
        dif = [per[a][x] - per[base_arm][x] for x in doms]
        e = statistics.fmean(dif)
        sd = statistics.stdev(dif)
        out[h] = {"E_of_the_9cell_head_arm": round(e, 8),
                  "per_domain_SD": round(sd, 8),
                  "n_domains": len(doms),
                  "min_abs_E_for_ci95_to_exclude_0": round(1.96 * sd / math.sqrt(len(dif)), 6),
                  "as_share_of_the_head_effect": round((1.96 * sd / math.sqrt(len(dif))) / abs(e), 4)}
    return out, len(doms)


def build(heads, bars, n_dom, src_prereg, src, screen_prediction):
    iv = dict(src["intervention"])
    band = iv.get("band") or iv["intervene"].split(":")[2]
    lo, hi = (int(x) for x in band.split("-"))
    layers = list(range(lo, hi + 1))
    per_cell = DOSE_UNIT // len(layers)
    if DOSE_UNIT % len(layers):
        sys.exit("REFUSING: DOSE_UNIT %d not divisible by the %d-layer band" % (DOSE_UNIT, len(layers)))

    cells = {}
    for h in heads:
        for L in layers:
            cells["CL_H%02d_L%02d" % (h, L)] = [[int(L), int(h)]]

    return {
        "id": "PR-CSI-015",
        "title": ("Per-CELL census of D34's other three load-bearing heads (%s) on basket validation: "
                  "is the depth concentration D36 found at head 2 GENERAL? A MAP, no rank, no p."
                  % ", ".join(str(h) for h in heads)),
        "frozen_utc_date": "2026-09-23",
        "EMITTED_MECHANICALLY_BY": "scripts/gates/dcs_csi_pr015_freeze.py",
        "design_ref": ("S-299/D36 (head 2's depth map, the result this extends); AM-38 (the n=1 screen "
                       "corroboration this makes n=4); S-269 (the screen's per-cell predictions); "
                       "S-294 (the bar derivation); AM-37 (why no confirmatory test follows)"),
        "split": "validation",
        "codeword": "basket",
        "statistical_unit": "DOMAIN (never the row); basket is NEVER pooled with button",
        "endpoint": "y_install; concept-free semantic_one_word; cell C; n_examples 4",
        "heads": list(heads),
        "heads_provenance": {
            "source": "D34 (PR-CSI-012 per-head census, validation) load-bearing four, MINUS head 2",
            "why_minus_2": "PR-CSI-014 already mapped head 2's nine cells; D36 is that result",
            "census_report": "reports/DCS_CSI_PR012_CENSUS_validation.json",
            "census_md5": _md5(os.path.join(REPO, "reports", "DCS_CSI_PR012_CENSUS_validation.json")),
            "NOT_A_SELECTION": (
                "D34 is a CENSUS -- no rank, no p -- so 'the heads whose singleton clears the family's "
                "own null anchor' is a DESCRIPTIVE set, not a tested winner. This family measures ALL "
                "nine cells of each head and therefore selects no cell of its own."),
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
            "CL_KO": "--intervene with NO selector = all 32 heads x all %d band layers; the denominator"
                     % len(layers),
            "CL_H<hh>_L<ll>": "--knockout-cells <ll>:<hh> -- ONE cell",
        },
        "NO_RANK_TEST": ("There is NO candidate, NO control family, NO rank and NO p-value here. A rank "
                         "among the %d layers of one head has an attainable floor of 1/%d = %.4f and "
                         "cannot clear alpha = 0.05 for ANY effect size. control_prefix and n_controls "
                         "are DELIBERATELY ABSENT so the rank tooling refuses this prereg."
                         % (len(layers), len(layers), 1.0 / len(layers))),
        "DOSE_EXPECTATION": {
            "per_cell_prefill_edits": per_cell,
            "derivation": "DOSE_UNIT %d / %d band layers" % (DOSE_UNIT, len(layers)),
            "STATUS": "MEASURED (PR-CSI-014 observed exactly 224.0 on all nine of its cells, S-299)",
            "why": ("S-292 flagged this as a PREDICTION under an untested uniformity assumption and "
                    "S-298/S-299 measured it: 224.0 on nine cells across nine distinct layers. It is an "
                    "identity here, not a prediction, and a deviation is a CODE defect."),
        },
        "DOSE_IDENTITY_IS_BLIND_HERE": (
            "Every one of the %d cell arms expects %d prefill edits, so the dose cannot tell any cell "
            "from any other -- S-246's collision on the layer AND head axes at once. Identity comes "
            "from each arm's own recorded knockout_cells ONLY (S-292/R26). Note also that a cell arm's "
            "knockout_heads is EMPTY, which recorded_heads() maps to 'ALL'."
            % (len(cells), per_cell)),
        "population": dict(src["population"]),
        "DETECTABILITY_PREREGISTERED_PER_HEAD": {
            "method": ("S-294: bar = 1.96 * (per-domain SD of that head's nine-cell arm) / sqrt(n_dom), "
                       "computed from the PUBLISHED D34 arms via W4's own by_domain"),
            "n_domains": n_dom,
            "per_head": {str(h): bars[h] for h in heads},
            "head_2_cross_check": {
                "recomputed": round(HEAD_2_FROZEN_BAR, 6),
                "frozen_in_pr014": HEAD_2_FROZEN_BAR,
                "note": "the method reproduces the bar PR-CSI-014 froze, so it has not drifted",
            },
            "WHY_PER_HEAD": (
                "These heads have smaller effects AND smaller per-domain spreads than head 2, so a "
                "single shared bar would be wrong in both directions. Head 23's bar is 0.006615 where "
                "head 2's is 0.019181 -- using head 2's bar would declare head 23 undetectable when it "
                "is not."),
            "COHERENT_OUTCOME_IF_NOTHING_CLEARS": (
                "Under an even nine-way split NO head's cell clears its own bar (0.28x-0.44x of it). "
                "That is a coherent, informative outcome preregistered HERE: it would mean the depth "
                "concentration D36 found at head 2 is NOT general, and that for these heads the load is "
                "distributed across depth. ⛔ It must NOT be reported as a failed experiment, and it "
                "must NOT be rescued by dropping to a weaker bar, a one-sided test, or an uncorrected "
                "'trend'. NOTE that 'ci95 excludes 0' is a WEAKER test than this bar and is NOT the "
                "criterion (S-299/S-300: on PR-CSI-014 one cell excluded 0 at 5% of the bar with the "
                "wrong sign)."),
        },
        "SCREEN_PREDICTIONS_ON_RECORD_BEFORE_THIS_FAMILY": {
            "source": "S-269, reading outputs/boombness/dcs_csi/w1_screen_train_basket_916132.json",
            "predictions": dict(screen_prediction),
            "already_tested": {"2": "L10 -- CORROBORATED on intervention by D36/AM-38 (n=1 head)"},
            "status": ("These were written down for a different purpose and are falsifiable as they "
                       "stand. ⚠ The screen is TRAIN and this census is VALIDATION, so the comparison "
                       "is across splits and not circular. ⚠ AM-32 measured that the SAME screen "
                       "ranked head 2 -- the strongest head -- only 6th of 32 at HEAD level, so a "
                       "corroboration here bounds the screen's WITHIN-head localisation only and says "
                       "nothing about its head ranking."),
        },
        "CENSUS_DELIVERABLE": (
            "%d cell effects E(CL_H<hh>_L<ll>) = mean over domains of (y_install(cell) - "
            "y_install(CL_BASE)), each with a bootstrap ci95, plus the CL_KO denominator. A DEPTH MAP "
            "for each of heads %s, read against that head's OWN preregistered bar. No head outside "
            "%s is measured and no cell of any other head is touched."
            % (len(cells), heads, heads)),
        "WHAT_THIS_CANNOT_ANSWER": [
            "whether any cell is PRIVILEGED -- there is no rank, no control family and no p",
            "anything that would lift D32's caveat 'NOT a claim about any single (layer, head) cell' -- "
            "AM-37 measured that no admissible held-out axis exists for a confirmatory cell test",
            "whether the screen's per-cell ordering is valid IN GENERAL -- at most this makes the "
            "intervention-verified sample 4 heads of 32",
            "anything revising D32, D33, D34, D35 or D36 -- a wider map does not retract a narrower one",
            "anything about the other 28 heads or any cell of them",
            "anything about DOMAIN generality -- these 23 domains are basket's usual set (S-256); the "
            "3 TEST domains remain untouched",
            "any rung above 1 on AM-34's ladder. This is necessity, like everything else in this sprint",
        ],
        "SELECTION_RE_ENTERS_WHEN": (
            "the moment any one cell is singled out for a claim. This census SELECTS NOTHING; naming a "
            "winner afterwards is selection on the data that produced it, and AM-37 established there is "
            "no held-out axis on which a confirmatory test of that winner could be read."),
        "VOID_CONDITIONS": [
            "1. compared arms not all on one GPU architecture (PR-CSI-003 precedent)",
            "2. attn_implementation not eager on any arm (a mask edit under SDPA is a silent no-op)",
            "3. any arm's recorded knockout_cells disagreeing with cell_sets",
            "4. CL_BASE carrying any intervention flag (S-260 voided job 918967 this way)",
            "5. any cell whose layer lies outside the band -- it would install NO hook and score as a "
            "clean null (score_behavior.py refuses it at construction, S-291)",
            "6. score_behavior.py edited while these arms are in flight",
            "7. any cell arm recording a dose other than %d -- now an IDENTITY, not a prediction "
            "(S-299)" % per_cell,
        ],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--heads", default="19,17,23")
    ap.add_argument("--source", default="configs/dcs_csi_pr014_cell_census_basket.json",
                    help="the frozen prereg to inherit the intervention/population from")
    ap.add_argument("--census-tag", default="csi5_census_basket_validation")
    ap.add_argument("--census-job", default="918631")
    ap.add_argument("--expect-n", type=int, default=230)
    ap.add_argument("--out", default="configs/dcs_csi_pr015_cell_census_3heads_basket.json")
    a = ap.parse_args()

    heads = [int(x) for x in a.heads.split(",") if x.strip()]
    if 2 in heads:
        sys.exit("REFUSING: head 2 is already mapped by PR-CSI-014 (D36). Re-running it here would "
                 "duplicate a published census under a second tag namespace (S-104/S-227).")
    if len(set(heads)) != len(heads):
        sys.exit("REFUSING: duplicate head in %r" % (heads,))
    if not os.path.exists(a.source):
        sys.exit("REFUSING: source prereg %r does not exist" % a.source)
    src = json.load(open(a.source))

    # THE BARS, and head 2's is re-derived as a drift check against what PR-014 froze.
    bars, n_dom = measure_bars(heads + [2], a.census_tag, a.expect_n, a.census_job)
    got2 = bars[2]["min_abs_E_for_ci95_to_exclude_0"]
    if abs(got2 - HEAD_2_FROZEN_BAR) > 5e-7:
        sys.exit("REFUSING: head 2's bar recomputes to %.6f but PR-CSI-014 froze %.6f -- the bar "
                 "derivation has DRIFTED, so the bars for %r cannot be trusted either."
                 % (got2, HEAD_2_FROZEN_BAR, heads))
    print("[pr015] head 2 bar cross-check: recomputed %.6f == frozen %.6f  OK" % (got2, HEAD_2_FROZEN_BAR))
    bars = {h: bars[h] for h in heads}

    screen = {"19": "L14", "17": "L14", "23": "L7"}
    pr = build(heads, bars, n_dom, a.source, src, {k: v for k, v in screen.items()
                                                   if int(k) in heads})
    for h in heads:
        b = bars[h]
        print("[pr015] head %-3d E=%+.6f SD=%.6f bar=%.6f (%.1f%% of |E|)  screen says %s"
              % (h, b["E_of_the_9cell_head_arm"], b["per_domain_SD"],
                 b["min_abs_E_for_ci95_to_exclude_0"], 100 * b["as_share_of_the_head_effect"],
                 screen.get(str(h), "?")))
    print("[pr015] %d arms = CL_BASE + CL_KO + %d cells (%d heads x %d layers)"
          % (pr["n_arms_per_split"], len(pr["cell_sets"]), len(heads), len(pr["layers"])))

    assert "head_sets" not in pr
    assert "control_prefix" not in pr and "n_controls" not in pr
    assert len(pr["cell_sets"]) == len(heads) * len(pr["layers"])
    assert all(len(v) == 1 for v in pr["cell_sets"].values())
    assert {v[0][1] for v in pr["cell_sets"].values()} == set(heads)
    for b in pr["base_arms"]:
        assert b not in pr["cell_sets"]

    atomic_write_json(a.out, pr)
    print("[pr015] wrote %s (%d bytes)" % (a.out, os.path.getsize(a.out)))
    print("[pr015] md5 = %s" % _md5(a.out))


if __name__ == "__main__":
    main()
