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
import re
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
    from an arm that actually failed.

    ⚠ R27/S-308 REWROTE THIS TEST. It used to `src.index("landed arm(s) FAILED")` -- a LITERAL -- and
    it broke the moment the summary line was reworded, even though the property it exists to protect
    was untouched. That is precisely the failure mode S-305 named ("write the test for the PROPERTY
    rather than the string"), and this file is where the lesson should have landed first. The
    property is: the zero-landed path and the real-failure path must exit with DIFFERENT non-zero
    codes, 3 and 1 respectively, and neither may be 0.
    """
    src = open(SWEEP).read()
    assert "sys.exit(3)" in src, "the zero-landed path must still exit 3"
    # Find the failure summary by its STRUCTURE -- a sys.exit carrying a GATE 0 failure message --
    # not by any particular wording of that message.
    fail_exits = [m for m in re.finditer(r"sys\.exit\(\s*\n?\s*\"GATE 0: ", src)]
    assert fail_exits, "no sys.exit() carrying a 'GATE 0:' failure message remains in the sweep"
    # And it must not be the exit-3 path: exit 3 is a bare code, the failure path carries a string
    # (which exits 1). Both must exist and be distinct.
    assert "sys.exit(3)" not in "".join(
        src[m.start():m.start() + 200] for m in fail_exits), \
        "the real-failure path must not collapse into the zero-landed exit code"


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


# ================================================================ R27 / S-308
# Four properties closed after adversarial review R27. Each is written against the PROPERTY the fix
# exists to guarantee, not against any wording -- S-305's lesson, applied here because R27 broke a
# literal-matching test in this very file while the property behind it was untouched.

SWEEP_PR015_ARGS = ["--tag-prefix", "csi8_cell3_basket_validation", "--split", "validation",
                    "--require-slurm-job", "922176"]


def _has_pr015_arms():
    import glob
    return len(glob.glob(os.path.join(
        ROOT, "outputs/boombness/score_behavior/csi8_cell3_basket_validation_*/DONE.json"))) >= 29


@pytest.mark.skipif(not _has_pr015_arms(), reason="PR-CSI-015's 29 landed arms are needed")
def test_a_PARTIAL_per_head_bar_block_REFUSES_and_does_not_borrow_another_heads_bar(tmp_path):
    """R27. S-301 closed TOTAL absence of a bar and left PARTIAL absence wide open.

    A prereg that declares bars PER HEAD but omits one head, while also carrying a legacy global
    bar, used to judge the missing head against ANOTHER HEAD'S criterion -- silently, exit 0. R27
    demonstrated the consequence on the real 29 arms: deleting head 23 and leaving head 2's frozen
    0.019181 flipped CL_H23_L07 from CLEARS to below-the-bar, the headline from 3-of-27 to 2-of-27,
    and head 23 from preregistered outcome A to outcome C -- the distributed-profile NULL.

    PROPERTY: if a prereg declares bars per head, that declaration must be TOTAL or the read refuses.
    """
    pr = json.load(open(PR015))
    del pr["DETECTABILITY_PREREGISTERED_PER_HEAD"]["per_head"]["23"]
    pr["DETECTABILITY_PREREGISTERED"] = {"min_abs_E_for_ci95_to_exclude_0": 0.019181}
    p = tmp_path / "partial.json"
    p.write_text(json.dumps(pr))
    r = subprocess.run([PY, CENSUS_READER, "--prereg", str(p), "--expect-n", "230",
                        "--out", os.devnull] + SWEEP_PR015_ARGS,
                       capture_output=True, text=True)
    out = r.stdout + r.stderr
    assert r.returncode != 0, "a partial per-head bar block was READ instead of refused"
    assert "REFUSING" in out, out[-400:]
    assert "CLEAR THE PREREGISTERED BAR" not in out, (
        "a headline was printed while one head was being judged against another head's bar")


@pytest.mark.skipif(not _has_pr015_arms(), reason="PR-CSI-015's 29 landed arms are needed")
@pytest.mark.parametrize("status,identity_expected", [
    ("MEASURED (PR-CSI-014 observed exactly 224.0, S-299)", True),
    ("PREDICTED, NOT MEASURED", False),
    ("NOT MEASURED -- this is an untested assumption", False),
    ("NOT YET MEASURED", False),
    ("UNMEASURED -- no cell arm has landed", False),
])
def test_the_dose_identity_banner_fails_closed_on_every_NEGATED_form(tmp_path, status,
                                                                     identity_expected):
    """R27. S-305's fix inverted the polarity of this branch but kept a SUBSTRING test on prose, so
    the NEGATION of its own keyword still matched: 'NOT MEASURED' contains 'MEASURED'. The sweep then
    announced an explicitly-unmeasured dose as an IDENTITY whose violation is 'a CODE defect'.

    PROPERTY: only an affirmative declaration may reach the identity branch. Every negative form, and
    absence, must read as UNVERIFIED (R20-6).
    """
    pr = json.load(open(PR015))
    pr["DOSE_EXPECTATION"]["STATUS"] = status
    p = tmp_path / "dose.json"
    p.write_text(json.dumps(pr))
    r = subprocess.run([PY, os.path.join(ROOT, "scripts", "gates",
                                         "dcs_csi_pr012_gate0_sweep.py"),
                        "--prereg", str(p)] + SWEEP_PR015_ARGS,
                       capture_output=True, text=True)
    out = r.stdout + r.stderr
    said_identity = "is an IDENTITY for this family" in out
    said_unverified = "is a PREDICTION from DOSE_UNIT" in out
    assert said_identity == identity_expected, (
        "STATUS %r -> identity=%s, expected %s\n%s" % (status, said_identity, identity_expected,
                                                       out[:600]))
    assert said_identity != said_unverified, "the two branches must be mutually exclusive"


@pytest.mark.skipif(not _has_pr015_arms(), reason="PR-CSI-015's 29 landed arms are needed")
def test_the_published_dose_status_comes_from_the_PREREG_and_not_from_a_hardcode(tmp_path):
    """R27 -- THE FOURTH INSTANCE OF THE S-305 CLASS, and the first to reach a PUBLISHED artefact.
    S-301 replaced this hardcode at the print banner and left the identical one 160 lines below,
    where it is written into the JSON for every cell arm. PR-CSI-015's published report therefore
    declared all 27 cell arms 'PREDICTED ... untested uniformity assumption' while its own prereg
    declared MEASURED and its own stdout said CONFIRMED.

    PROPERTY: the status written into the report is the prereg's, whatever the prereg says.
    """
    pr = json.load(open(PR015))
    pr["DOSE_EXPECTATION"]["STATUS"] = "SENTINEL-FROM-THE-PREREG-NOT-THE-CODE"
    p = tmp_path / "sent.json"
    p.write_text(json.dumps(pr))
    out_json = tmp_path / "r.json"
    r = subprocess.run([PY, CENSUS_READER, "--prereg", str(p), "--expect-n", "230",
                        "--out", str(out_json)] + SWEEP_PR015_ARGS,
                       capture_output=True, text=True)
    assert r.returncode == 0, (r.stdout + r.stderr)[-600:]
    rep = json.load(open(out_json))
    cell_status = {v.get("dose_expectation_status")
                   for k, v in rep["GATE_0_and_identity"]["per_arm"].items()
                   if k not in ("CL_BASE", "CL_KO")}
    assert cell_status == {"SENTINEL-FROM-THE-PREREG-NOT-THE-CODE"}, (
        "the report's dose status is not the prereg's: %r" % (cell_status,))


@pytest.mark.skipif(not _has_pr015_arms(), reason="PR-CSI-015's 29 landed arms are needed")
def test_the_detectability_metadata_is_NOT_null_for_a_PER_HEAD_prereg(tmp_path):
    """R27. S-301 taught `_bar_for` the PER_HEAD container and left the three OTHER consumers of the
    same block reading the old name only. The published PR-CSI-015 report consequently carried
    DETECTABILITY_PREREGISTERED and NOTHING_CLEARED_THE_BAR_IS_A_PREREGISTERED_COHERENT_OUTCOME as
    null, while its own WEAKER_CRITERION_NOTE told the reader the criterion lived in a field that
    was null. The numbers were right; the artefact could not be audited against its own criterion.

    PROPERTY: whatever container a prereg uses, a report that HAS a criterion must RECORD it.
    """
    out_json = tmp_path / "r.json"
    r = subprocess.run([PY, CENSUS_READER, "--prereg", PR015, "--expect-n", "230",
                        "--out", str(out_json)] + SWEEP_PR015_ARGS,
                       capture_output=True, text=True)
    assert r.returncode == 0, (r.stdout + r.stderr)[-600:]
    cf = json.load(open(out_json))["CELL_FAMILY"]
    assert cf.get("DETECTABILITY_PREREGISTERED") is not None, \
        "the detectability block is null although the prereg declares one"
    assert cf.get("NOTHING_CLEARED_THE_BAR_IS_A_PREREGISTERED_COHERENT_OUTCOME") is not None, \
        "the coherent-outcome text is null although the prereg declares one"
    # and the per-head bars must be recorded and must match the prereg exactly
    per = json.load(open(PR015))["DETECTABILITY_PREREGISTERED_PER_HEAD"]["per_head"]
    for h, d in per.items():
        assert abs(cf["preregistered_bar_per_head"][h]
                   - d["min_abs_E_for_ci95_to_exclude_0"]) < 1e-12
    # the note must not point the reader at a field that is null
    if cf.get("preregistered_bar") is None:
        assert "preregistered_bar_per_head" in cf["WEAKER_CRITERION_NOTE"], \
            "the note points at 'preregistered_bar', which is null on a multi-head family"


# ================================================================ R27 / S-310
# THE COLLISION ON THE DENOMINATOR. R27 filed this as "not exploitable today"; PR-CSI-016 is the
# family that makes it exploitable, because the census reader REFUSES a prereg carrying both
# head_sets and cell_sets, so PR-016's whole-head arms must be expressed as 9-CELL LISTS -- and a
# 9-cell band arm records an EMPTY knockout_heads (which recorded_heads maps to "ALL") and the
# IDENTICAL dose 9 x 224 = 2016. Identity field and dose both collide with CL_KO.

def _farm(tmp_path, real_dirs, swap_arm, new_cells):
    """A scratch SCORE_DIR: symlinks to the real arm dirs, with ONE arm's config.json replaced by a
    copy whose knockout_cells names `new_cells`. Everything else is the real run, byte for byte."""
    farm = tmp_path / "score"
    farm.mkdir()
    for d in real_dirs:
        base = os.path.basename(d)
        if swap_arm + "_2026" in base:
            tgt = farm / base
            tgt.mkdir()
            for f in os.listdir(d):
                if f == "config.json":
                    cfg = json.load(open(os.path.join(d, f)))
                    (cfg.get("args") or cfg)["knockout_cells"] = new_cells
                    (tgt / f).write_text(json.dumps(cfg))
                else:
                    os.symlink(os.path.join(d, f), tgt / f)
        else:
            os.symlink(d, farm / base)
    return str(farm)


@pytest.mark.skipif(not _has_pr015_arms(), reason="PR-CSI-015's 29 landed arms are needed")
def test_the_ALL32_denominator_cannot_be_impersonated_by_a_full_band_9cell_arm(tmp_path):
    """PROPERTY: the all-32 knockout arm must be distinguishable from a one-head, full-band 9-cell
    arm. They share the dose (2016) AND the head-level identity field (both record an empty
    knockout_heads), so the ONLY discriminator is that a true all-32 arm carries NO cell list.

    Before the fix the sweep printed "ALL 32   PASS" for a cell-scoped denominator and exited 0.
    """
    import glob as _glob
    import importlib.util as _ilu
    real = sorted(_glob.glob(os.path.join(
        ROOT, "outputs/boombness/score_behavior/csi8_cell3_basket_validation_*")))
    nine = ",".join("%d:17" % L for L in range(6, 15))
    farm = _farm(tmp_path, real, "CL_KO", nine)

    spec = _ilu.spec_from_file_location(
        "sweep_under_test", os.path.join(ROOT, "scripts", "gates", "dcs_csi_pr012_gate0_sweep.py"))
    mod = _ilu.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.census.rederive.SCORE_DIR = farm          # both the sweep and strict_run_dir read this one

    argv = ["dcs_csi_pr012_gate0_sweep.py", "--prereg", PR015,
            "--tag-prefix", "csi8_cell3_basket_validation", "--split", "validation",
            "--require-slurm-job", "922176"]
    old = sys.argv[:]
    sys.argv = argv
    try:
        with pytest.raises(SystemExit) as ei:
            mod.main()
    finally:
        sys.argv = old
    assert ei.value.code not in (0, None), (
        "a CELL-SCOPED denominator was certified as the all-32 knockout -- the S-246 collision on "
        "the KO arm, which is exactly the shape PR-CSI-016 contains")


@pytest.mark.skipif(not _has_pr015_arms(), reason="PR-CSI-015's 29 landed arms are needed")
def test_the_real_unmodified_denominator_still_PASSES(tmp_path):
    """The companion the above needs: a guard that refuses everything is not a guard. The REAL
    CL_KO -- empty knockout_heads, empty knockout_cells -- must still pass."""
    import glob as _glob
    import importlib.util as _ilu
    real = sorted(_glob.glob(os.path.join(
        ROOT, "outputs/boombness/score_behavior/csi8_cell3_basket_validation_*")))
    farm = _farm(tmp_path, real, "CL_KO", "")     # swapped, but with the ORIGINAL empty value

    spec = _ilu.spec_from_file_location(
        "sweep_ok", os.path.join(ROOT, "scripts", "gates", "dcs_csi_pr012_gate0_sweep.py"))
    mod = _ilu.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.census.rederive.SCORE_DIR = farm
    argv = ["x", "--prereg", PR015, "--tag-prefix", "csi8_cell3_basket_validation",
            "--split", "validation", "--require-slurm-job", "922176"]
    old = sys.argv[:]
    sys.argv = argv
    try:
        rc = mod.main()
    except SystemExit as e:
        rc = e.code
    finally:
        sys.argv = old
    assert rc in (0, None), "the genuine all-32 denominator was refused: rc=%r" % (rc,)


# ================================================================ S-311
# THE BAR AS A FROZEN *RULE* RATHER THAN A FROZEN NUMBER.
# PR-CSI-016 reads BUTTON, where heads 17 and 23 have never had an arm, so no bar for them can exist
# as a number before the family runs -- while S-308 (correctly) made a missing numeric bar a REFUSAL.
# The prereg may therefore freeze the DERIVATION instead, naming the whole-head arm it is computed
# from. These tests pin the properties that keep that from being a loophole.

PR012 = os.path.join(ROOT, "configs", "dcs_csi_pr012_head_census_basket.json")


def _pr015_with_rule(tmp_path, head, source_arm, rule=True, source_cells=None):
    pr = json.load(open(PR015))
    ph = pr["DETECTABILITY_PREREGISTERED_PER_HEAD"]["per_head"][str(head)]
    ph.pop("min_abs_E_for_ci95_to_exclude_0", None)
    ph["bar_source_arm"] = source_arm
    if rule:
        pr["DETECTABILITY_PREREGISTERED_PER_HEAD"]["BAR_IS_A_RULE"] = {
            "z": 1.96,
            "rule": "bar(h) = z * SD(per-domain paired delta of <bar_source_arm> vs the base arm) "
                    "/ sqrt(n_domains)",
        }
    if source_cells is not None:
        pr["cell_sets"][source_arm] = source_cells
        pr["n_arms_per_split"] = len(pr["cell_sets"]) + len(pr["base_arms"])
    p = tmp_path / "rule.json"
    p.write_text(json.dumps(pr))
    return str(p)


@pytest.mark.skipif(not _has_pr015_arms(), reason="PR-CSI-015's 29 landed arms are needed")
@pytest.mark.parametrize("case,kw,needle", [
    # ⚠ R28/S-312 added an EARLIER refusal for a source arm that is not in the family, so this case
    # must name an arm that IS in the family or it refuses for the other (also correct) reason.
    ("a source arm named with NO rule block", dict(source_arm="CL_H17_L14", rule=False),
     "declares no DETECTABILITY_PREREGISTERED_PER_HEAD['BAR_IS_A_RULE']"),
    ("a source arm that is not in the family", dict(source_arm="HD_NOSUCH", rule=True),
     "is not an arm of prereg"),
    ("a source arm that is a SINGLE CELL", dict(source_arm="CL_H17_L14", rule=True),
     "not that head's FULL BAND"),
])
def test_a_bar_RULE_refuses_every_way_it_could_become_a_loophole(tmp_path, case, kw, needle):  # noqa: E501
    """PROPERTY: a rule is only a criterion if it is frozen, total, and derived from an arm that is
    NOT the quantity it judges. The single-cell case is the important one -- a bar computed from the
    very cell it is used to test is the circularity the whole detectability block exists to avoid.
    """
    p = _pr015_with_rule(tmp_path, 17, **kw)
    r = subprocess.run([PY, CENSUS_READER, "--prereg", p, "--expect-n", "230",
                        "--out", os.devnull] + SWEEP_PR015_ARGS, capture_output=True, text=True)
    out = r.stdout + r.stderr
    assert r.returncode != 0, "%s was ACCEPTED\n%s" % (case, out[-500:])
    assert needle in out, "%s refused for the wrong reason:\n%s" % (case, out[-500:])
    assert "CLEAR THE PREREGISTERED BAR" not in out


@pytest.mark.skipif(not (_has_pr015_arms() and os.path.exists(PR012)),
                    reason="PR-CSI-015's arms and PR-CSI-012's prereg are needed")
def test_the_bar_RULE_reproduces_the_NUMBER_that_PR015_froze(tmp_path):
    """THE POSITIVE TEST, and it is exact rather than approximate.

    D34's `SINGLE_17` arm IS head 17's full band -- all nine band layers of head 17 -- and PR-CSI-015's
    frozen bar 0.009082 was derived from it by exactly the rule under test. So if the read-time rule
    is correct it must recompute that number to every printed digit. A rule that agrees with the
    frozen number on a case where both exist is the only evidence that the rule may be trusted on
    heads 17 and 23 of PR-CSI-016, where only the rule will exist.
    """
    import glob as _glob
    import importlib.util as _ilu

    src = _glob.glob(os.path.join(
        ROOT, "outputs/boombness/score_behavior/csi5_census_basket_validation_SINGLE_17_*"))[0]
    real = sorted(_glob.glob(os.path.join(
        ROOT, "outputs/boombness/score_behavior/csi8_cell3_basket_validation_*")))
    farm = tmp_path / "score"
    farm.mkdir()
    for d in real:
        os.symlink(d, farm / os.path.basename(d))
    # D34's whole-head arm, re-badged into this family's namespace. It was run with --knockout-heads,
    # so its config and job id are rewritten to what a PR-016-style HD_ arm would record; every other
    # byte -- crucially results.jsonl, the per-domain data the bar is computed from -- is the real run.
    hd = farm / "csi8_cell3_basket_validation_HD_17_20260922_191521_939328"
    hd.mkdir()
    for f in os.listdir(src):
        if f == "config.json":
            cfg = json.load(open(os.path.join(src, f)))
            args = cfg.get("args") or cfg
            args["knockout_heads"] = ""
            args["knockout_cells"] = ",".join("%d:17" % L for L in range(6, 15))
            args["arm"] = "HD_17"
            (hd / f).write_text(json.dumps(cfg))
        elif f == "RUNMETA.json":
            rm = json.load(open(os.path.join(src, f)))
            rm["slurm_job_id"] = "922176"
            (hd / f).write_text(json.dumps(rm))
        else:
            os.symlink(os.path.join(src, f), hd / f)

    nine = [[L, 17] for L in range(6, 15)]
    prereg = _pr015_with_rule(tmp_path, 17, "HD_17", rule=True, source_cells=nine)
    out_json = tmp_path / "r.json"

    spec = _ilu.spec_from_file_location("census_rule", CENSUS_READER)
    mod = _ilu.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.rederive.SCORE_DIR = str(farm)
    old = sys.argv[:]
    sys.argv = ["census", "--prereg", prereg, "--tag-prefix", "csi8_cell3_basket_validation",
                "--split", "validation", "--expect-n", "230", "--require-slurm-job", "922176",
                "--out", str(out_json)]
    try:
        rc = mod.main()
    except SystemExit as e:
        rc = e.code
    finally:
        sys.argv = old
    assert rc in (0, None), "the rule path refused a well-formed prereg: rc=%r" % (rc,)

    cf = json.load(open(out_json))["CELL_FAMILY"]
    computed = cf["bars_COMPUTED_FROM_A_FROZEN_RULE"]["17"]["bar"]
    frozen = json.load(open(PR015))["DETECTABILITY_PREREGISTERED_PER_HEAD"]["per_head"]["17"][
        "min_abs_E_for_ci95_to_exclude_0"]
    assert abs(round(computed, 6) - frozen) < 1e-9, (
        "the read-time RULE gives %.8f where PR-CSI-015 FROZE %.6f -- the derivation has drifted, so "
        "it cannot be trusted on a head where only the rule exists" % (computed, frozen))
    # and the source arm must not be counted as a cell
    assert "HD_17" not in cf["cells_clearing_the_preregistered_bar"]
    assert cf["n_cells_judged"] == 27, "the 9-cell source arm leaked into the depth map"
    assert cf["bar_source_arms_EXCLUDED_FROM_THE_DEPTH_MAP"] == ["HD_17"]
    assert cf["per_cell_dose_verdict"].startswith("CONFIRMED"), (
        "the 2016-dose source arm leaked into the per-CELL dose check")


@pytest.mark.skipif(not _has_pr015_arms(), reason="PR-CSI-015's 29 landed arms are needed")
def test_a_head_with_BOTH_a_number_and_a_source_arm_REFUSES(tmp_path):
    """R28/S-312. The number won, so _bar_from_rule never ran and NONE of its guards (in-family,
    landed, full-band) were applied to the named arm -- yet the arm had ALREADY been removed from the
    census by the exclusion. R28 demonstrated an arm silently vanishing from a published depth map
    with no check having looked at it: head 17 keeping its frozen bar while naming head 23's own
    headline cell as its source dropped CL_H23_L07 -- the cell carrying head 23's outcome A -- and
    printed '2 of 26 cells CLEAR', exit 0."""
    pr = json.load(open(PR015))
    pr["DETECTABILITY_PREREGISTERED_PER_HEAD"]["per_head"]["17"]["bar_source_arm"] = "CL_H23_L07"
    pr["DETECTABILITY_PREREGISTERED_PER_HEAD"]["BAR_IS_A_RULE"] = {"z": 1.96, "rule": "r"}
    p = tmp_path / "both.json"
    p.write_text(json.dumps(pr))
    r = subprocess.run([PY, CENSUS_READER, "--prereg", str(p), "--expect-n", "230",
                        "--out", os.devnull] + SWEEP_PR015_ARGS, capture_output=True, text=True)
    out = r.stdout + r.stderr
    assert r.returncode != 0, "a head with two criteria was READ\n%s" % out[-500:]
    assert "BOTH a frozen bar" in out and "ONE criterion" in out, out[-400:]
    assert "CLEAR THE PREREGISTERED BAR" not in out


@pytest.mark.skipif(not _has_pr015_arms(), reason="PR-CSI-015's 29 landed arms are needed")
@pytest.mark.parametrize("rule,needle", [
    ({"rule": "r"}, "without `z`"),
    ({"z": 0.0, "rule": "r"}, "outside [0.5, 5.0]"),
    ({"z": 99.0, "rule": "r"}, "outside [0.5, 5.0]"),
])
def test_the_rules_only_numeric_parameter_must_be_DECLARED_and_SANE(tmp_path, rule, needle):
    """R28/S-312. A missing z silently used 1.96 and then wrote "z": 1.96 into the report as though
    the prereg had frozen it -- false metadata in a published artefact, the R27/S-308 class. And
    z=0.0 gave a bar of 0.0 and '11 of 27 cells CLEAR THE PREREGISTERED BAR', exit 0."""
    pr = json.load(open(PR015))
    ph = pr["DETECTABILITY_PREREGISTERED_PER_HEAD"]["per_head"]["17"]
    ph.pop("min_abs_E_for_ci95_to_exclude_0")
    ph["bar_source_arm"] = "CL_H17_L14"          # refused later for not being a full band; z first
    pr["DETECTABILITY_PREREGISTERED_PER_HEAD"]["BAR_IS_A_RULE"] = rule
    p = tmp_path / "z.json"
    p.write_text(json.dumps(pr))
    r = subprocess.run([PY, CENSUS_READER, "--prereg", str(p), "--expect-n", "230",
                        "--out", os.devnull] + SWEEP_PR015_ARGS, capture_output=True, text=True)
    out = r.stdout + r.stderr
    assert r.returncode != 0 and needle in out, out[-500:]


def test_a_HEAD_family_whose_KO_predates_knockout_cells_is_still_READABLE():
    """R28/S-312 -- S-310 OVER-REACHED. Requiring the all-32 arm to record an EMPTY knockout_cells
    made D34 (PR-CSI-012) unreadable, because its HD_KO predates the flag entirely and the field is
    ABSENT. A published family this sprint calls load-bearing stopped being reproducible.
    PROPERTY: the cell-scoped denominator check applies to CELL families, where every arm is
    post-S-291; a HEAD family has no arm that could impersonate the denominator."""
    pr012 = os.path.join(ROOT, "configs", "dcs_csi_pr012_head_census_basket.json")
    if not os.path.exists(pr012):
        pytest.skip("PR-CSI-012 prereg absent")
    import glob as _g
    if len(_g.glob(os.path.join(
            ROOT, "outputs/boombness/score_behavior/csi5_census_basket_validation_*/DONE.json"))) < 44:
        pytest.skip("D34's arms are not on disk")
    r = subprocess.run([PY, CENSUS_READER, "--prereg", pr012,
                        "--tag-prefix", "csi5_census_basket_validation", "--split", "validation",
                        "--expect-n", "230", "--out", os.devnull], capture_output=True, text=True)
    out = r.stdout + r.stderr
    assert "GATE 0 PASS on all 44 arms" in out, (
        "D34 is no longer re-readable -- the S-310 denominator check over-reached:\n%s" % out[-700:])


# ================================================================ S-315
# R27/S-308 taught the sweep that "run dirs exist but were REFUSED" is a FAILURE rather than "not
# landed". That is right for a ledger mismatch, a bad DONE.status or two complete dirs -- and WRONG
# for an arm being written right now, whose DONE.json simply does not exist yet. The frozen reads say
# GATE 0 "may be swept incrementally at any time", so under S-308 alone every mid-family sweep cried
# wolf. These two tests pin BOTH halves, because fixing one by breaking the other is the failure mode.

SWEEP_SCRIPT = os.path.join(ROOT, "scripts", "gates", "dcs_csi_pr012_gate0_sweep.py")


def _sweep_farm(tmp_path, mutate):
    """Scratch SCORE_DIR of symlinks to PR-015's 29 real arm dirs. `mutate(dst, name)` is called for
    each arm dir and may choose to materialise it instead of symlinking."""
    import glob as _g
    farm = tmp_path / "score"
    farm.mkdir()
    for d in sorted(_g.glob(os.path.join(
            ROOT, "outputs/boombness/score_behavior/csi8_cell3_basket_validation_*"))):
        base = os.path.basename(d)
        if not mutate(farm, d, base):
            os.symlink(d, farm / base)
    return str(farm)


def _run_sweep(farm):
    import importlib.util as _ilu
    spec = _ilu.spec_from_file_location("sweep_s315", SWEEP_SCRIPT)
    mod = _ilu.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.census.rederive.SCORE_DIR = farm
    old = sys.argv[:]
    sys.argv = ["s", "--prereg", PR015, "--tag-prefix", "csi8_cell3_basket_validation",
                "--split", "validation", "--require-slurm-job", "922176"]
    import io as _io
    import contextlib
    buf = _io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            rc = mod.main()
    except SystemExit as e:
        rc = e.code
    finally:
        sys.argv = old
    return rc, buf.getvalue()


@pytest.mark.skipif(not _has_pr015_arms(), reason="PR-CSI-015's 29 landed arms are needed")
def test_an_IN_FLIGHT_arm_is_not_reported_as_a_GATE_0_FAILURE(tmp_path):
    """S-315. An arm still being written has a run dir and no DONE.json. It must be reported as IN
    FLIGHT -- neither passed nor failed -- and the sweep must NOT report a GATE 0 FAILURE, or every
    incremental sweep during a live family is a false alarm.

    ⚠ R30-D/S-332 SHARPENED THIS. The test used to assert rc in (0, None), which conflated two
    different things: "this is not a failure" (S-315's point) and "this is a passing GATE 0" (which
    it is NOT -- 28 of 29 arms were checked). R30-D demonstrated the cost on a fixture: an arm with
    DONE.json deleted and results.jsonl truncated to 117 of 230 rows printed ".. IN FLIGHT" and
    "every landed arm passes", exit 0 -- indistinguishable from a complete pass, forever, because
    the sweep never learns the job is gone. The exit codes now separate all three states:
        1 = a real GATE 0 failure        3 = ran, but NOT the family's verdict        0 = all arms
    S-315's intent is preserved exactly -- an in-flight arm still never yields exit 1."""
    def mutate(farm, src, base):
        if "_CL_H23_L14_" not in base:
            return False
        dst = farm / base
        dst.mkdir()
        for f in os.listdir(src):
            if f == "DONE.json":
                continue                       # <- the arm has not finished writing
            os.symlink(os.path.join(src, f), dst / f)
        return True
    rc, out = _run_sweep(_sweep_farm(tmp_path, mutate))
    assert "IN FLIGHT" in out, out[-700:]
    assert rc != 1, "an in-flight arm was treated as a GATE 0 FAILURE: rc=%r\n%s" % (rc, out[-700:])
    assert "THIS SWEEP IS PARTIAL" in out, "a partial sweep did not say so"
    assert "every landed arm passes (28 of 29)" in out, out[-400:]
    # R30-D/S-332: and it must NOT read as a complete pass either.
    assert rc == 3, "a PARTIAL sweep exited %r -- exit 0 is a complete GATE 0 pass" % (rc,)
    assert "GATE 0 IS NOT COMPLETE" in out, out[-500:]


@pytest.mark.skipif(not _has_pr015_arms(), reason="PR-CSI-015's 29 landed arms are needed")
def test_a_COMPLETE_sweep_still_exits_0(tmp_path):
    """R30-D/S-332's companion: a guard that refuses everything is not a guard. With all 29 arms
    landed and passing, the sweep must still exit 0 -- otherwise the new arm-count check has simply
    made every sweep unusable rather than making exit 0 mean something."""
    rc, out = _run_sweep(_sweep_farm(tmp_path, lambda farm, src, base: False))
    assert "every landed arm passes (29 of 29)" in out, out[-500:]
    assert "GATE 0 IS NOT COMPLETE" not in out, out[-500:]
    assert rc in (0, None), "a COMPLETE sweep was refused: rc=%r\n%s" % (rc, out[-700:])


@pytest.mark.skipif(not _has_pr015_arms(), reason="PR-CSI-015's 29 landed arms are needed")
def test_S308_STILL_HOLDS_a_refused_arm_that_HAS_a_DONE_json_is_still_a_FAILURE(tmp_path):
    """The companion, and the one that matters: S-315 must not undo S-308. An arm whose DONE.json
    ledger disagrees with its results.jsonl has FINISHED writing and is corrupt, not in flight.
    R27 demonstrated that this used to print 'every landed arm passes (28 of 29)' and exit 0 -- on
    CL_H19_L14, one of the three cells that cleared the bar."""
    def mutate(farm, src, base):
        if "_CL_H19_L14_" not in base:
            return False
        dst = farm / base
        dst.mkdir()
        for f in os.listdir(src):
            if f == "DONE.json":
                done = json.load(open(os.path.join(src, f)))
                done["rows_written"] = int(done.get("rows_written", 230)) + 1   # ledger lies
                (dst / f).write_text(json.dumps(done))
            else:
                os.symlink(os.path.join(src, f), dst / f)
        return True
    rc, out = _run_sweep(_sweep_farm(tmp_path, mutate))
    assert "IN FLIGHT" not in out, "a corrupt FINISHED arm was excused as in flight:\n%s" % out[-700:]
    assert rc not in (0, None), "a ledger mismatch was not a failure: rc=%r\n%s" % (rc, out[-700:])
    assert "GATE 0 FAIL" in out and "CL_H19_L14" in out, out[-700:]


# ================================================================ R29 / S-323
# VOID condition 8 was PROSE. R29 established that VOID_CONDITIONS is emitted by every freeze script
# and consumed by NO reader, gate or test, and that pr013_whole_head_REFERENCE was written by one
# script and read by none -- while PR-CSI-018's frozen read asserted "VOID CONDITION 8 IS CHECKED
# HERE AND IT IS FREE". The compounding harm: a drifted whole-head arm silently moves that head's BAR
# (the bar is 1.96*SD of that same arm), so the head is quietly DROPPED by ADMISSION and published as
# "NOT_A_MISS", shrinking K and the permutation space with no provenance warning.

def _pr015_with_reference(tmp_path, head, ref_E, tol=1e-6):
    """PR-015's prereg with a whole-head reference bolted onto one head, using a REAL 9-cell source
    arm so the S-311 rule path is the one under test."""
    pr = json.load(open(PR015))
    nine = [[L, head] for L in range(6, 15)]
    pr["cell_sets"]["HD_%d" % head] = nine
    pr["n_arms_per_split"] = len(pr["cell_sets"]) + len(pr["base_arms"])
    ph = pr["DETECTABILITY_PREREGISTERED_PER_HEAD"]["per_head"][str(head)]
    ph.pop("min_abs_E_for_ci95_to_exclude_0", None)
    ph["bar_source_arm"] = "HD_%d" % head
    ph["pr013_whole_head_REFERENCE"] = {"E": ref_E, "void_tolerance": tol}
    pr["DETECTABILITY_PREREGISTERED_PER_HEAD"]["BAR_IS_A_RULE"] = {
        "z": 1.96, "rule": "bar = z*SD(paired delta)/sqrt(n)"}
    p = tmp_path / "ref.json"
    p.write_text(json.dumps(pr))
    return str(p)


def _farm_with_hd17(tmp_path):
    """PR-015's 29 real arms plus D34's SINGLE_17 re-badged as a 9-cell HD_17 (the S-311 fixture)."""
    import glob as _g
    src = _g.glob(os.path.join(
        ROOT, "outputs/boombness/score_behavior/csi5_census_basket_validation_SINGLE_17_*"))[0]
    farm = tmp_path / "score"
    farm.mkdir()
    for d in sorted(_g.glob(os.path.join(
            ROOT, "outputs/boombness/score_behavior/csi8_cell3_basket_validation_*"))):
        os.symlink(d, farm / os.path.basename(d))
    hd = farm / "csi8_cell3_basket_validation_HD_17_20260922_191521_939328"
    hd.mkdir()
    for f in os.listdir(src):
        if f == "config.json":
            c = json.load(open(os.path.join(src, f)))
            a = c.get("args") or c
            a["knockout_heads"] = ""
            a["knockout_cells"] = ",".join("%d:17" % L for L in range(6, 15))
            a["arm"] = "HD_17"
            (hd / f).write_text(json.dumps(c))
        elif f == "RUNMETA.json":
            r = json.load(open(os.path.join(src, f)))
            r["slurm_job_id"] = "922176"
            (hd / f).write_text(json.dumps(r))
        else:
            os.symlink(os.path.join(src, f), hd / f)
    return str(farm)


def _census_on(farm, prereg, tmp_path):
    import importlib.util as _ilu
    spec = _ilu.spec_from_file_location("census_void8", CENSUS_READER)
    mod = _ilu.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.rederive.SCORE_DIR = farm
    old = sys.argv[:]
    sys.argv = ["c", "--prereg", prereg, "--tag-prefix", "csi8_cell3_basket_validation",
                "--split", "validation", "--expect-n", "230", "--require-slurm-job", "922176",
                "--out", str(tmp_path / "o.json")]
    import io as _io
    import contextlib
    buf = _io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            rc = mod.main()
    except SystemExit as e:
        rc = e.code
    finally:
        sys.argv = old
    # sys.exit("message") puts the refusal in e.code, NOT on stdout. Searching only the captured
    # stdout would have made every refusal assertion below vacuous -- it looked for text that is
    # structurally never there. Both channels are returned as one searchable blob.
    text = buf.getvalue() + ("" if rc in (0, None) else "\n%s" % (rc,))
    return rc, text


@pytest.mark.skipif(not _has_pr015_arms(), reason="PR-CSI-015's arms are needed")
def test_VOID_8_REFUSES_a_whole_head_arm_that_drifted_from_its_frozen_reference(tmp_path):
    """PROPERTY: a prereg that freezes a prior measurement of the same head/codeword/split must have
    that condition ENFORCED, not merely stated. S-318 showed bit-identical reproduction across two
    jobs and two nodes, so any difference above the declared tolerance means the population, bank,
    exclusions or model revision drifted and nothing in the family is readable."""
    farm = _farm_with_hd17(tmp_path)
    # the real HD_17 arm is D34's SINGLE_17, E = -0.02921839. Freeze a WRONG reference.
    pr = _pr015_with_reference(tmp_path, 17, ref_E=-0.01000000)
    rc, out = _census_on(farm, pr, tmp_path)
    assert rc not in (0, None), "a drifted whole-head arm was READ:\n%s" % out[-800:]
    assert "VOID CONDITION" in out and "DRIFTED" in out, out[-800:]
    assert "CLEAR THE PREREGISTERED BAR" not in out, "a headline was printed despite the VOID"


@pytest.mark.skipif(not _has_pr015_arms(), reason="PR-CSI-015's arms are needed")
def test_VOID_8_PASSES_and_PRINTS_when_the_arm_matches_its_reference(tmp_path):
    """The companion: a guard that refuses everything is not a guard. With the true value frozen the
    read proceeds AND emits a PROVENANCE line, so the check is visible rather than merely absent."""
    farm = _farm_with_hd17(tmp_path)
    pr = _pr015_with_reference(tmp_path, 17, ref_E=-0.02921839)
    rc, out = _census_on(farm, pr, tmp_path)
    assert rc in (0, None), "a MATCHING reference was refused:\n%s" % out[-800:]
    assert "PROVENANCE head 17" in out and " OK" in out, out[-800:]
    assert "3 of 27 cells CLEAR" in out or "CLEAR THE PREREGISTERED BAR" in out


@pytest.mark.skipif(not _has_pr015_arms(), reason="PR-CSI-015's arms are needed")
def test_a_reference_whose_source_arm_is_ABSENT_refuses_rather_than_skipping(tmp_path):
    """R20-6: absence is not a pass. If the arm the reference names did not land, the condition
    cannot be evaluated and the read must stop -- not quietly continue unchecked."""
    farm = _farm_with_hd17(tmp_path)
    pr = json.load(open(_pr015_with_reference(tmp_path, 17, ref_E=-0.02921839)))
    pr["DETECTABILITY_PREREGISTERED_PER_HEAD"]["per_head"]["17"]["bar_source_arm"] = "HD_NOSUCH"
    p = tmp_path / "absent.json"
    p.write_text(json.dumps(pr))
    rc, out = _census_on(farm, str(p), tmp_path)
    assert rc not in (0, None) and "REFUSING" in out, out[-600:]


# ================================================================ R30-A / S-333
# Everything named as a bar_source_arm is REMOVED FROM THE CENSUS BEFORE ANY CHECK LOOKS AT IT.


@pytest.mark.skipif(not _has_pr015_arms(), reason="PR-CSI-015's 29 landed arms are needed")
def test_a_STRAY_per_head_entry_cannot_silently_delete_arms_from_the_census(tmp_path):
    """R30-A F3. `_BAR_SOURCE_ARMS` unions the granularity set with EVERY arm any per_head entry
    names, and `_judged` then drops all of them. `_bar_from_rule`'s in-family / full-band guards
    only run for heads that reach `_bar_for` -- heads that still have judged cells -- so a per_head
    key for a head with NO single-cell arms (a typo, a template leftover, a retired head) deleted
    arms from the depth map with ZERO validation.

    R30-A showed one stray entry cutting n_cells_judged 8 -> 7, and four of them deleting a whole
    head: gone from the depth map, from the per-head bars, from every clearing count, the headline
    moving "6 of 8 cells CLEAR" -> "3 of 4", exit 0, and no stdout line mentioning it.

    PROPERTY: a per_head key that is not a head of this family is a REFUSAL, not a silent deletion."""
    # PR-015's own heads keep their frozen NUMBER bars (so they name no arm and are untouched);
    # the ONLY thing added is a rule block and one stray per_head key for a head that does not exist.
    pr = json.load(open(PR015))
    pr["DETECTABILITY_PREREGISTERED_PER_HEAD"]["BAR_IS_A_RULE"] = {
        "z": 1.96,
        "rule": "bar(h) = z * SD(per-domain paired delta of <bar_source_arm> vs the base arm) "
                "/ sqrt(n_domains)",
    }
    ph = pr["DETECTABILITY_PREREGISTERED_PER_HEAD"]["per_head"]
    victim = "CL_H19_L07"
    assert victim in pr["cell_sets"], "fixture invalid: %s is not an arm of PR-015" % victim
    ph["99"] = {"bar_source_arm": victim}      # head 99 does not exist in this family
    p2 = tmp_path / "stray.json"
    p2.write_text(json.dumps(pr))

    r = subprocess.run([PY, CENSUS_READER, "--prereg", str(p2), "--expect-n", "230",
                        "--out", os.devnull] + SWEEP_PR015_ARGS, capture_output=True, text=True)
    out = r.stdout + r.stderr
    assert r.returncode != 0, (
        "a stray per_head entry silently removed %s from the census:\n%s" % (victim, out[-700:]))
    assert "not a head of prereg" in out, out[-700:]
    assert victim in out, "the refusal did not name the arm it would have deleted:\n%s" % out[-700:]
    assert "CLEAR THE PREREGISTERED BAR" not in out, "a depth map was published anyway"


@pytest.mark.skipif(not _has_pr015_arms(), reason="PR-CSI-015's 29 landed arms are needed")
def test_the_EXCLUDED_arms_are_named_on_stdout_not_only_in_the_JSON(tmp_path):
    """R30-A F4. The exclusion set was written to the report as
    `bar_source_arms_EXCLUDED_FROM_THE_DEPTH_MAP` and printed NOWHERE. These families are read from
    the log, so a depth map and a clearing count appeared with no indication that arms had been
    removed to produce them. An exclusion that changes the headline belongs on the transcript."""
    out_json = tmp_path / "census.json"
    r = subprocess.run([PY, CENSUS_READER, "--prereg", PR015, "--expect-n", "230",
                        "--out", str(out_json)] + SWEEP_PR015_ARGS, capture_output=True, text=True)
    out = r.stdout + r.stderr
    assert r.returncode == 0, "the unmodified PR-015 census was refused:\n%s" % out[-800:]
    assert "EXCLUDED FROM THE DEPTH MAP" in out, (
        "the census published a depth map without naming the arms it excluded:\n%s" % out[-800:])
    rep = json.load(open(out_json))
    named = rep["CELL_FAMILY"]["bar_source_arms_EXCLUDED_FROM_THE_DEPTH_MAP"] or []
    for arm in named:
        assert arm in out, "arm %s is excluded in the JSON but never printed:\n%s" % (arm, out[-800:])


@pytest.mark.skipif(not _has_pr015_arms(), reason="PR-CSI-015's 29 landed arms are needed")
def test_the_detectability_resolver_searches_BOTH_blocks_not_just_the_first(tmp_path):
    """R30-A F6. `_detect_block` was `PER_HEAD or DETECTABILITY_PREREGISTERED or {}` -- an `or`, not
    a search -- so once a prereg carried a per-head block the legacy block was unreachable for EVERY
    field. A prereg that DOES record COHERENT_OUTCOME_IF_NOTHING_CLEARS_IT in the legacy block
    published `null` for it, and stdout would have said "THE PREREG RECORDS NO COHERENT-OUTCOME
    TEXT" against a prereg that records exactly that text. This is S-308's "a null in a published
    artefact" transposed from the bars onto the outcome text.

    PROPERTY: a field the per-head block does not define is still found in the legacy block."""
    pr = json.load(open(PR015))
    assert pr["DETECTABILITY_PREREGISTERED_PER_HEAD"]["per_head"], "fixture invalid: no per_head"
    needle = "R30-A/S-333 sentinel: nothing clearing the bar is a preregistered coherent outcome"
    pr.setdefault("DETECTABILITY_PREREGISTERED", {})
    pr["DETECTABILITY_PREREGISTERED"]["COHERENT_OUTCOME_IF_NOTHING_CLEARS_IT"] = needle
    # BOTH spellings the resolver accepts -- PR-015 uses the one without the trailing _IT, so
    # popping only the other leaves the per-head block winning on precedence (correctly) and the
    # test proves nothing.
    for _sp in ("COHERENT_OUTCOME_IF_NOTHING_CLEARS_IT", "COHERENT_OUTCOME_IF_NOTHING_CLEARS"):
        pr["DETECTABILITY_PREREGISTERED_PER_HEAD"].pop(_sp, None)
    p = tmp_path / "twoblocks.json"
    p.write_text(json.dumps(pr))

    out_json = tmp_path / "census.json"
    r = subprocess.run([PY, CENSUS_READER, "--prereg", str(p), "--expect-n", "230",
                        "--out", str(out_json)] + SWEEP_PR015_ARGS, capture_output=True, text=True)
    assert r.returncode == 0, (r.stdout + r.stderr)[-800:]
    rep = json.load(open(out_json))
    got = rep["CELL_FAMILY"].get("NOTHING_CLEARED_THE_BAR_IS_A_PREREGISTERED_COHERENT_OUTCOME")
    assert got == needle, (
        "the legacy detectability block was unreachable because a per-head block exists; the report "
        "published %r for a field the prereg DOES record" % (got,))
