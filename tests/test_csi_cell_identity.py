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


def test_sweep_announces_a_cell_family_as_UNVERIFIED(tmp_path):
    """A cell family's dose check must never print as though it confirmed a measured identity."""
    p = tmp_path / "cells.json"
    p.write_text(json.dumps({
        "id": "PR-CSI-014-TEST", "intervention": {"band": "6-14"},
        "base_arms": ["CELL_BASE", "CELL_KO"],
        "cell_sets": {"CELL_CANDIDATE": [[10, 2]], "CELL_CTRL_00": [[7, 23]]}}))
    r = _sweep(str(p))
    out = r.stdout + r.stderr
    assert "CELL family: per-cell dose 224 = 2016/9 layers" in out, out
    assert "PREDICTED, NOT MEASURED" in out, out
    assert "UNVERIFIED" in out, out


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
