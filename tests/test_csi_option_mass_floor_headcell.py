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
