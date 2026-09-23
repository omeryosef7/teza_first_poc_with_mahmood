"""PR-CSI-014's cell identity and per-cell dose: the reader primitives and the collision they avoid.

WHY THIS FILE EXISTS. S-246 measured that the head-level DOSE cannot identify an arm: a K-head arm
records K x 2016 prefill edits and the ALL-32 arm records 2016, so a singleton is indistinguishable
from the full knockout. Identity therefore comes from each arm's OWN recorded field.

The cell axis reintroduces that collision in a NEW and nastier form. A cell arm passes
`--knockout-cells` and NOT `--knockout-heads`, so its recorded `knockout_heads` is the EMPTY STRING --
which `recorded_heads()` correctly maps to "ALL", because for a HEAD family an omitted flag IS the
all-32 arm. Read through the head-level check, every 1-cell arm would therefore be reported as the
all-32 knockout: a 224-edit arm certified as the 2016-edit denominator.

And the per-cell dose is a PREDICTION, not a measurement. 2016 was measured; 2016/9 = 224 assumes the
edits are uniform across the nine layers, which no artefact on disk can confirm because the hook
counters are summed across layers before they are written. These tests pin that the code SAYS so.

Run:  python -m pytest tests/test_csi_cell_identity.py -q
"""
import importlib.util
import json
import os
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CENSUS = os.path.join(ROOT, "scripts", "dcs_csi_head_census.py")
SWEEP = os.path.join(ROOT, "scripts", "gates", "dcs_csi_pr012_gate0_sweep.py")
PY = sys.executable


def _load():
    spec = importlib.util.spec_from_file_location("census_under_test", CENSUS)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _rundir(tmp_path, args):
    d = tmp_path / "run"
    d.mkdir(exist_ok=True)
    (d / "config.json").write_text(json.dumps({"args": args}))
    return str(d)


# ---------------------------------------------------------------- recorded_cells

def test_absent_field_is_None_not_a_value(tmp_path):
    """Every artefact produced BEFORE S-291 lacks the key. 'Predates the flag' must not read as
    'used no cells' -- R20-6: any check whose PASS is consistent with reading nothing is not a check."""
    c = _load()
    assert c.recorded_cells(_rundir(tmp_path, {"knockout_heads": "2"})) is None


def test_empty_field_is_NOT_A_CELL_ARM_and_emphatically_not_ALL(tmp_path):
    """THE CENTRAL ASYMMETRY. For heads, empty means ALL (the widest intervention). For cells, empty
    means the arm is not cell-scoped. Returning 'ALL' here would make a plain head arm read as a
    288-cell arm."""
    c = _load()
    got = c.recorded_cells(_rundir(tmp_path, {"knockout_heads": "", "knockout_cells": ""}))
    assert got == "NOT_A_CELL_ARM", got
    assert got != "ALL"


def test_single_cell_parses(tmp_path):
    c = _load()
    assert c.recorded_cells(_rundir(tmp_path, {"knockout_cells": "10:2"})) == [(10, 2)]


def test_several_cells_come_back_SORTED(tmp_path):
    """The prereg comparison is by equality, so both sides must be canonically ordered."""
    c = _load()
    got = c.recorded_cells(_rundir(tmp_path, {"knockout_cells": "14:19,7:23"}))
    assert got == [(7, 23), (14, 19)], got


def test_list_form_parses_too(tmp_path):
    c = _load()
    assert c.recorded_cells(_rundir(tmp_path, {"knockout_cells": [[10, 2], [7, 23]]})) \
        == [(7, 23), (10, 2)]


def test_a_cell_arm_records_empty_knockout_heads_which_reads_as_ALL(tmp_path):
    """THE COLLISION ITSELF, asserted as a fact about the data rather than a worry.

    This is why the sweep must not consult recorded_heads on a cell family."""
    c = _load()
    d = _rundir(tmp_path, {"knockout_heads": "", "knockout_cells": "10:2"})
    assert c.recorded_heads(d) == "ALL", (
        "if this ever stops being 'ALL' the collision is gone and the guard can be simplified")
    assert c.recorded_cells(d) == [(10, 2)]


# ---------------------------------------------------------------- band_width / per_cell_dose

def test_band_width_from_the_explicit_band_field():
    c = _load()
    assert c.band_width({"intervention": {"band": "6-14"}}) == 9


def test_band_width_falls_back_to_the_intervene_string():
    c = _load()
    assert c.band_width(
        {"intervention": {"intervene": "demo_all:attn_knockout:6-14:1.0"}}) == 9


def test_band_width_refuses_when_there_is_no_band():
    c = _load()
    with pytest.raises(SystemExit) as e:
        c.band_width({"intervention": {}})
    assert "no intervention band" in str(e.value)


def test_band_width_refuses_an_inverted_band():
    c = _load()
    with pytest.raises(SystemExit):
        c.band_width({"intervention": {"band": "14-6"}})


def test_per_cell_dose_is_224_on_the_sprint_band():
    c = _load()
    assert c.per_cell_dose({"intervention": {"band": "6-14"}}) == (224, 9)
    assert 224 * 9 == c.DOSE_UNIT


def test_per_cell_dose_refuses_a_NON_DIVISIBLE_band():
    """If DOSE_UNIT does not divide by the band width, the uniformity assumption is ALREADY false and
    gating on a rounded number would enforce an arithmetic that cannot hold."""
    c = _load()
    with pytest.raises(SystemExit) as e:
        c.per_cell_dose({"intervention": {"band": "6-10"}})     # 5 layers; 2016/5 is not an integer
    assert "not divisible" in str(e.value)


def test_the_prediction_is_documented_as_a_prediction():
    """A gate that enforces an assumption while reading like it verifies an identity is the defect."""
    src = open(CENSUS).read()
    i = src.index("def per_cell_dose")
    doc = src[i:i + 1800]
    assert "PREDICTION, NOT A MEASURED IDENTITY" in doc
    assert "uniformity" in doc


# ---------------------------------------------------------------- the sweep's family guards

def _sweep(prereg_path):
    return subprocess.run([PY, SWEEP, "--prereg", prereg_path, "--tag-prefix", "nope",
                           "--split", "validation"], capture_output=True, text=True)


def test_sweep_refuses_a_prereg_with_BOTH_head_sets_and_cell_sets(tmp_path):
    p = tmp_path / "both.json"
    p.write_text(json.dumps({"id": "X", "head_sets": {"A": [1]},
                             "cell_sets": {"B": [[10, 2]]},
                             "intervention": {"band": "6-14"}}))
    r = _sweep(str(p))
    assert r.returncode != 0
    assert "BOTH head_sets and cell_sets" in (r.stdout + r.stderr)


def test_sweep_refuses_a_prereg_with_NEITHER(tmp_path):
    p = tmp_path / "neither.json"
    p.write_text(json.dumps({"id": "X", "intervention": {"band": "6-14"}}))
    r = _sweep(str(p))
    assert r.returncode != 0
    assert "neither head_sets nor cell_sets" in (r.stdout + r.stderr)


def test_sweep_never_announces_an_UNDECLARED_dose_as_confirmed(tmp_path):
    """A cell family's dose check must never print as though it confirmed a measured identity.

    ⚠ UPDATED BY S-305, AND THE INTENT IS UNCHANGED. This used to assert the literal string
    "PREDICTED, NOT MEASURED", which the sweep printed unconditionally. It now reads the status from the
    prereg (because asserting it was wrong on PR-CSI-015, whose prereg declares MEASURED), and this
    prereg declares no status at all -- so the assertion is on the PROPERTY the test was always for:
    an undeclared dose must fall back to UNVERIFIED and must never read as an identity."""
    p = tmp_path / "cells.json"
    p.write_text(json.dumps({
        "id": "PR-CSI-014-TEST", "intervention": {"band": "6-14"},
        "base_arms": ["CELL_BASE", "CELL_KO"],
        "cell_sets": {"CELL_CANDIDATE": [[10, 2]], "CELL_CTRL_00": [[7, 23]]}}))
    r = _sweep(str(p))
    out = r.stdout + r.stderr
    assert "CELL family: per-cell dose 224 = 2016/9 layers" in out, out
    assert "UNVERIFIED" in out, out
    assert "STATUS NOT DECLARED BY THE PREREG" in out, out
    assert "is an IDENTITY" not in out, (
        "a prereg that declares NO dose status had its dose announced as an identity")


def test_sweep_reports_a_MEASURED_dose_as_an_identity_when_the_prereg_says_so(tmp_path):
    """The other half of S-305: a family whose prereg declares the dose MEASURED must not be warned
    about as unverified, or the gate contradicts the preregistration on every run."""
    p = tmp_path / "cells_measured.json"
    p.write_text(json.dumps({
        "id": "PR-CSI-0XX-TEST", "intervention": {"band": "6-14"},
        "base_arms": ["CELL_BASE", "CELL_KO"],
        "DOSE_EXPECTATION": {"STATUS": "MEASURED (a prior family observed it)"},
        "cell_sets": {"CELL_A": [[10, 2]], "CELL_B": [[7, 23]]}}))
    out = _sweep(str(p)).stdout + _sweep(str(p)).stderr
    assert "MEASURED" in out, out
    assert "is an IDENTITY" in out, out
    assert "is a PREDICTION from DOSE_UNIT" not in out, (
        "the gate warned that a MEASURED dose is a prediction, contradicting the prereg")


def test_sweep_still_reads_no_endpoint_after_the_cell_reader_was_added():
    """recorded_cells joined the scanned-callable list; the guard must still pass on all of them."""
    src = open(SWEEP).read()
    assert "recorded_cells, liveness, strict_run_dir" in src, \
        "recorded_cells is not in the endpoint-blindness scan list"


def test_cell_branch_does_not_consult_recorded_heads():
    """The collision guard, asserted structurally: inside the IS_CELLS branch identity must come from
    recorded_cells alone."""
    src = open(SWEEP).read()
    i = src.index("elif IS_CELLS:")
    j = src.index("else:", i)
    branch = src[i:j]
    assert "recorded_cells(d)" in branch
    assert "recorded_heads" not in branch, \
        "the cell branch consults recorded_heads, which returns 'ALL' for every cell arm"


# ---------------------------------------------------------------- zero-landed is not a pass

def test_zero_landed_arms_is_NOT_reported_as_a_pass(tmp_path):
    """S-292. This printed 'GATE 0: every landed arm passes (0 of 23)' and exited 0 whenever nothing
    matched -- a typo in --tag-prefix, the wrong split, a job id that produced nothing.

    It is the rule this sweep's own docstring invokes against the dose check, violated by the sweep:
    a check whose PASS is consistent with reading NOTHING is not a check."""
    p = tmp_path / "heads.json"
    p.write_text(json.dumps({"id": "X", "intervention": {"band": "6-14"},
                             "base_arms": ["A_BASE", "A_KO"],
                             "head_sets": {"A_ONE": [2]}}))
    r = subprocess.run([PY, SWEEP, "--prereg", str(p), "--tag-prefix",
                        "tag_that_matches_nothing_at_all", "--split", "validation"],
                       capture_output=True, text=True)
    out = r.stdout + r.stderr
    assert "NOTHING TO CHECK" in out, out
    assert "THIS IS NOT A PASS" in out, out
    assert "every landed arm passes" not in out, \
        "a pass was reported over an empty set of arms"
    assert r.returncode == 3, (
        f"expected exit 3 (zero landed, distinguishable from a real GATE 0 failure which exits 1), "
        f"got {r.returncode}")


def test_a_real_gate0_failure_and_zero_landed_have_DIFFERENT_exit_codes():
    """Zero-landed is legitimate early in a live family, so a caller must be able to tell it apart
    from an arm that actually failed."""
    src = open(SWEEP).read()
    assert "sys.exit(3)" in src
    i = src.index("landed arm(s) FAILED")
    assert "sys.exit(" in src[max(0, i - 120):i], "the real-failure path no longer exits non-zero"


# ---------------------------------------------------------------- S-301: a missing bar must REFUSE

CENSUS_READER = os.path.join(ROOT, "scripts", "dcs_csi_head_census.py")
PR014 = os.path.join(ROOT, "configs", "dcs_csi_pr014_cell_census_basket.json")
PR015 = os.path.join(ROOT, "configs", "dcs_csi_pr015_cell_census_3heads_basket.json")


def _has_pr014_arms():
    import glob
    return len(glob.glob(os.path.join(
        ROOT, "outputs/boombness/score_behavior/csi7_cell_basket_validation_*/DONE.json"))) >= 11


@pytest.mark.skipif(not _has_pr014_arms(), reason="PR-CSI-014's landed arms are needed")
def test_a_cell_prereg_with_NO_BAR_refuses_instead_of_printing_a_false_null(tmp_path):
    """S-301. THE MOST DAMAGING SHAPE OF R20-6, on the one field the verdict turns on.

    The bar used to be read from exactly one path. A prereg naming its bars anywhere else left the
    threshold None, every cell tested 'below the bar', and the headline printed
    "0 of N cells CLEAR THE PREREGISTERED BAR" -- a null MANUFACTURED BY A MISSING FIELD, and
    indistinguishable in the output from the preregistered-coherent "nothing concentrates" result."""
    pr = json.load(open(PR014))
    pr.pop("DETECTABILITY_PREREGISTERED", None)
    p = tmp_path / "nobar.json"
    p.write_text(json.dumps(pr))
    r = subprocess.run([PY, CENSUS_READER, "--prereg", str(p),
                        "--tag-prefix", "csi7_cell_basket_validation", "--split", "validation",
                        "--expect-n", "230", "--require-slurm-job", "921664", "--out", os.devnull],
                       capture_output=True, text=True)
    out = r.stdout + r.stderr
    assert r.returncode != 0, "a bar-less cell prereg was READ instead of refused"
    assert "REFUSING" in out and "no preregistered detectability bar" in out, out[-400:]
    assert "CLEAR THE PREREGISTERED BAR" not in out, (
        "a headline verdict was printed with no bar to judge against -- this is the false null S-301 "
        "exists to prevent")


@pytest.mark.skipif(not os.path.exists(PR015), reason="PR-CSI-015 prereg not emitted")
def test_every_head_in_a_multihead_cell_prereg_has_its_OWN_bar():
    """PR-CSI-015's three heads have different per-domain spreads, so one shared bar would be wrong in
    both directions -- head 23's is 0.006615 where head 2's is 0.019181."""
    pr = json.load(open(PR015))
    heads = sorted({int(c[0][1]) for c in pr["cell_sets"].values()})
    per = pr["DETECTABILITY_PREREGISTERED_PER_HEAD"]["per_head"]
    for h in heads:
        assert str(h) in per, f"head {h} has cells but no preregistered bar"
        v = per[str(h)].get("min_abs_E_for_ci95_to_exclude_0")
        assert isinstance(v, (int, float)) and v > 0, f"head {h}'s bar is {v!r}"
    assert len({per[str(h)]["min_abs_E_for_ci95_to_exclude_0"] for h in heads}) == len(heads), \
        "the three bars are not distinct, so they were not derived per head"


def test_the_reader_never_derives_clears_from_a_nullable_threshold():
    """Structural guard: `clears` must come from the per-arm resolver, which refuses on absence."""
    src = open(CENSUS_READER).read()
    assert "clears = abs(E[k]) > _bar_for(k)" in src, \
        "the per-row verdict is not using the refusing per-arm bar resolver"
    assert "_thr is not None and abs(E[k])" not in src, \
        "a nullable-threshold test is back; a missing bar would read as 'below the bar'"


def test_the_dose_status_banner_is_read_from_the_prereg_not_hardcoded():
    """It said "PREDICTED, NOT MEASURED" literally -- true when S-292 wrote it, FALSE once PR-CSI-014
    measured 224.0 on nine cells. A banner that cannot stop saying 'predicted' will mislead."""
    src = open(CENSUS_READER).read()
    assert '"STATUS", "STATUS NOT DECLARED BY THE PREREG"' in src
    i = src.index("CELL family: per-cell dose")
    assert "PREDICTED, NOT MEASURED" not in src[i:i + 200], "the status is still hardcoded at the banner"


# ---------------------------------------------------------------- S-305: no tool hardcodes the status

SWEEP_SRC = open(SWEEP).read()
CENSUS_SRC = open(CENSUS_READER).read()


def test_no_reader_or_gate_hardcodes_the_dose_STATUS():
    """S-305. The string "PREDICTED, NOT MEASURED" was true when S-292 wrote it and FALSE once S-299
    measured 224.0 on nine cells. S-301 fixed it in the census reader and NOT in the sweep, so the sweep
    then asserted the OPPOSITE OF THE PREREG on every PR-CSI-015 run.

    This is the class test, not the instance test: a family's dose status is the PREREG's statement, and
    no tool may assert it. The only legitimate live occurrence of the literal is a freeze script
    declaring its own family's status."""
    for name, src in (("gate0 sweep", SWEEP_SRC), ("census reader", CENSUS_SRC)):
        code = "\n".join(l for l in src.splitlines() if not l.lstrip().startswith("#"))
        assert "PREDICTED, NOT MEASURED" not in code, (
            f"{name} hardcodes a dose status; it must read DOSE_EXPECTATION.STATUS from the prereg")
        assert 'DOSE_EXPECTATION") or {}).get(' in src or '"STATUS"' in src, \
            f"{name} does not read the status from the prereg at all"


@pytest.mark.skipif(not os.path.exists(PR015), reason="PR-CSI-015 prereg not emitted")
def test_each_prereg_declares_its_own_dose_status_and_they_DIFFER():
    """PR-014 froze the dose as a PREDICTION (it was); PR-015 declares it MEASURED (S-299 measured it).
    If these ever agree, one of them is stating something it did not establish."""
    a = json.load(open(PR014))["DOSE_EXPECTATION"]["STATUS"]
    b = json.load(open(PR015))["DOSE_EXPECTATION"]["STATUS"]
    assert "PREDICTED" in a.upper(), a
    assert "MEASURED" in b.upper() and "PREDICTED" not in b.upper(), b
