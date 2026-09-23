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
