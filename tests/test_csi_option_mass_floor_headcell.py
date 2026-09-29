#!/usr/bin/env python3
"""The head/cell option-mass floor (PR-CSI-025) must exist, must be inert by default, and must bite.

*** WHY THIS FILE EXISTS. ***
AM-55-a (S-458) recorded that §1-§4 and §H CANNOT run the readout-validity sensitivity that
reassured §A, because their instrument has no option-mass concept at all. S-547 measured that
precisely: ZERO option-mass mentions across the 1750 lines of dcs_csi_head_census.py,
dcs_csi_head_analyze.py and dcs_csi_head_single_rank.py, against 33 in the axis analyser. S-548
added the flag. This file is the test the sprint rule demands: one that FAILS WITHOUT IT.

THREE PROPERTIES, and the middle one is the one that would silently rot:
  1. the flag EXISTS and refuses the ways it must,
  2. the default path is BYTE-IDENTICAL to the old behaviour -- `keep_keys=None` means 26 existing
     callers of load_installation are unaffected BY CONSTRUCTION, which is what VOID 7 asks,
  3. a real floor actually REMOVES rows -- a filter that silently keeps everything would pass a
     naive test and make the whole sensitivity vacuous.
"""
import importlib.util
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


LPM = os.path.join(REPO, "scripts", "dcs_cont_layerpos_map.py")
CENSUS = os.path.join(REPO, "scripts", "dcs_csi_head_census.py")
ANALYZE = os.path.join(REPO, "scripts", "dcs_csi_head_analyze.py")
SCORE = os.path.join(REPO, "outputs", "boombness", "score_behavior")


def _a_head_run_dir():
    import glob
    ds = sorted(glob.glob(os.path.join(SCORE, "csi11_cell8_basket_validation_BK_BASE_*")))
    return ds[0] if ds else None


def test_flags_exist_in_the_census():
    src = open(CENSUS).read()
    assert "--option-mass-floor" in src, "PR-CSI-025's floor flag is gone"
    assert "--option-mass-reference" in src, "the reference-arm flag is gone"
    assert "_option_mass_keys" in src, "the key-set helper is gone"


def test_loader_takes_keep_keys_and_defaults_to_none():
    src = open(LPM).read()
    assert "def load_installation(run_dir: str, keep_keys=None)" in src, (
        "load_installation lost keep_keys, or its default stopped being None -- the default is what "
        "makes the change inert for 26 callers")
    assert "if keep_keys is not None and k not in keep_keys:" in src


def test_by_domain_threads_keep_keys():
    src = open(ANALYZE).read()
    assert "def by_domain(run_dir, keep_keys=None):" in src
    assert "keep_keys=keep_keys" in src, "by_domain accepts keep_keys but does not pass it on"


def test_default_path_is_byte_identical():
    """Property 2: with keep_keys unset, nothing changes for any existing caller."""
    d = _a_head_run_dir()
    if d is None:
        return  # no corpus in this checkout; the source assertions above still bind
    lpm = _load("lpm", LPM)
    assert lpm.load_installation(d) == lpm.load_installation(d, keep_keys=None)


def test_full_key_set_is_also_identical():
    d = _a_head_run_dir()
    if d is None:
        return
    lpm = _load("lpm", LPM)
    base = lpm.load_installation(d)
    assert lpm.load_installation(d, keep_keys=set(base[0])) == base


def test_a_real_floor_actually_removes_rows():
    """Property 3: the filter must BITE. A no-op filter makes the sensitivity vacuous."""
    d = _a_head_run_dir()
    if d is None:
        return
    lpm = _load("lpm", LPM)
    full = lpm.load_installation(d)[0]
    few = lpm.load_installation(d, keep_keys=set(sorted(full)[:5]))[0]
    assert len(few) == 5 < len(full), (
        "keep_keys did not restrict the key set: %d vs %d" % (len(few), len(full)))


def test_floor_refuses_without_a_reference_arm():
    src = open(CENSUS).read()
    assert "needs --option-mass-reference" in src, (
        "a floor with no reference arm must REFUSE -- otherwise a per-arm floor gets applied by "
        "accident, which is the defect the axis analyser's first floor version had")


def test_floor_refuses_a_reference_arm_not_in_the_family():
    src = open(CENSUS).read()
    assert "is not an arm of this family" in src
    assert "BF_BASE" in src and "BK_BASE" in src, (
        "the refusal must name the non-uniform BASE arms; PR-CSI-025 VOID 7 exists because HD_BASE "
        "does not exist for the cell families")


def test_floor_refuses_when_it_retains_nothing():
    src = open(CENSUS).read()
    assert "retains ZERO keys" in src, "a sensitivity over an empty key set must refuse, not pass"


def test_missing_option_mass_is_not_treated_as_zero():
    src = open(CENSUS).read()
    assert "missing is not zero" in src


# ---- R42-F1/F9/F11, S-576: the census DISCLOSES thinning but deliberately does NOT guard it ------

def test_the_census_refuses_a_negative_floor():
    """R42-F11: `> 0.0` let a negative floor skip the filter and still be RECORDED as applied."""
    src = open(CENSUS).read()
    assert "if a.option_mass_floor < 0.0:" in src
    i = src.index("if a.option_mass_floor < 0.0:")
    seg = src[i:i + 500]
    assert "REFUSING" in seg and "recorded in the artefact as though it had been applied" in seg


def test_the_census_records_per_domain_retention():
    """S-561: the domain SET is unchanged while the domains are THINNED 10 -> 1, and nothing in the
    artefact let a reader see it. The four published sensitivity artefacts were produced blind to it."""
    src = open(CENSUS).read()
    for key in ("rows_per_domain", "rows_per_domain_histogram",
                "min_rows_per_domain", "max_rows_per_domain"):
        assert key in src, "census does not record %s" % key
    assert "WHY_ROWS_PER_DOMAIN_IS_RECORDED" in src


def test_the_census_does_NOT_refuse_a_thin_domain_and_says_why():
    """THE DESIGN DECISION, PINNED. The paired reader got a refusing --min-rows at S-564; the census
    deliberately did not, because it produced the four PUBLISHED artefacts and a refusing default
    would change a shipped instrument's behaviour on re-run -- which is what VOID 7 forbids. A later
    reader 'fixing' this asymmetry would silently invalidate the published reads."""
    src = open(CENSUS).read()
    # ⚠ the first version of this assertion tested for the STRING "--min-rows", which the census's
    # own explanatory comment contains ("the paired reader got a refusing --min-rows at S-564").
    # Testing for a mention rather than for the FLAG is the same over-matching defect this file's
    # sibling tests keep catching elsewhere; it is the argparse registration that must be absent.
    assert 'ap.add_argument("--min-rows"' not in src, \
        "the census must not grow a refusing retention gate"
    assert "min_rows_per_domain" in src, "...but it must still RECORD the retention"
    assert "VOID 7" in src[src.index("WHY_ROWS_PER_DOMAIN_IS_RECORDED"):
                           src.index("WHY_ROWS_PER_DOMAIN_IS_RECORDED") + 600]


def test_the_key_count_is_not_labelled_a_row_count():
    """R42-F9: it printed a KEY count as '%d of %d rows retained'. They coincide on every family read
    so far (230 rows -> 230 distinct keys), so 146/230 was right and the LABEL was not."""
    src = open(CENSUS).read()
    assert "KEYS retained" in src
    assert "rows retained (%.1f%%)" not in src


def test_the_disclosure_is_additive_only():
    """VOID 7: the retention block must not touch keep_keys, per[], or any arm's data -- it reads the
    reference arm again and writes metadata. Verified end-to-end at S-576 by re-running the csi5
    census and diffing: 0 mismatches across 43 arms' E, ci95 and loo_marginal."""
    src = open(CENSUS).read()
    i = src.index("_inst, _, _ = w4.lpm.load_installation(ref_dir, keep_keys=keep_keys)")
    j = src.index("print(\"[option-mass]")
    block = src[i:j]
    for forbidden in ("keep_keys =", "per[", "slots[", "E[", "CI["):
        assert forbidden not in block, "retention block mutates %r" % forbidden


# ---- R42-F7 / F8, S-577 -------------------------------------------------------------------------

def test_the_schema_distinguishes_the_two_artefact_shapes():
    """R42-F8: `dcs_csi_head_census/1` denoted BOTH shapes -- artefacts written before S-549 carry no
    `option_mass` block, every artefact written after always does. A reader could not tell which."""
    src = open(CENSUS).read()
    assert '"schema": "dcs_csi_head_census/2"' in src
    assert '"schema": "dcs_csi_head_census/1"' not in src


def test_liveness_is_NOT_filtered_and_the_artefact_says_so():
    """R42-F7, and the fix is NOT the one the review proposed. It suggested filtering liveness to the
    retained keys; that would be WRONG -- GATE 0 reads the INTERVENTION (prefill/decode edits, dose),
    which fired on every row of the run regardless of whether that row's readout clears a floor.
    Filtering would under-report what the run did. The defect was that nothing SAID the count is
    unfiltered, leaving `n_rows: 230` beside `n_keys_retained: 146` for a reader to reconcile."""
    src = open(CENSUS).read()
    assert "live[arm] = w4.liveness(dirs[arm])" in src, "liveness must stay unfiltered"
    assert "w4.liveness(dirs[arm], keep_keys" not in src, "liveness must NOT take the floor's keys"
    assert "GATE_0_ROW_COUNTS_ARE_UNFILTERED" in src, "the artefact must disclose it"
    i = src.index("GATE_0_ROW_COUNTS_ARE_UNFILTERED")
    seg = src[i:i + 700]
    assert "will exceed" in seg and "n_keys_retained" in seg
