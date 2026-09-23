"""The CSI argv generator: the head path, the new cell path, and what its --check does NOT do.

WHY THIS FILE EXISTS AT ALL. `scripts/gates/dcs_csi_pr010_argv.py` is the single place an arm's argv is
defined for every PR-CSI family, and until now **nothing tested it**. Its only verification was its own
`--check`, invoked inside the slurm script at submit time. That is how S-260 happened: `argv_for`
compared the arm name to the literal `"HD_BASE"`, so PR-CSI-013's base arm `BT_BASE` was handed
`--intervene` with no `--knockout-heads` -- an ALL-32 KNOCKOUT standing in as the family's CLEAN
REFERENCE -- and 14 arms of job 918967 ran that way before it was caught. A unit test on the base arm
would have caught it in milliseconds.

Run:  python -m pytest tests/test_csi_argv_generator.py -q
"""
import importlib.util
import io
import contextlib
import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GEN = os.path.join(ROOT, "scripts", "gates", "dcs_csi_pr010_argv.py")

HEAD_FAMILIES = [
    ("configs/dcs_csi_pr010_head_causal_basket.json", "csi3_head_basket", 24),
    ("configs/dcs_csi_pr011_head_all32_controls_basket.json", "csi4_all32_basket", 24),
    ("configs/dcs_csi_pr012_head_census_basket.json", "csi5_census_basket", 44),
    ("configs/dcs_csi_pr013_button_head_replication.json", "csi6_btnhead_button", 23),
]


def _mod():
    spec = importlib.util.spec_from_file_location("argv_under_test", GEN)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _pr(rel):
    return json.load(open(os.path.join(ROOT, rel)))


def _cellpr(tmp_path, n=9, head=2, band="6-14", base=("CL_BASE", "CL_KO")):
    lo, hi = (int(x) for x in band.split("-"))
    cells = {("CL_L%02d" % L): [[L, head]] for L in range(lo, lo + n)}
    pr = {"id": "PR-CSI-014-TEST", "split": "validation", "codeword": "basket",
          "NO_RANK_TEST": True, "base_arms": list(base), "n_arms_per_split": n + 2,
          "intervention": {"intervene": "demo_all:attn_knockout:%s:1.0" % band,
                           "knockout_scope": "target_surface_row_only", "band": band},
          "cell_sets": cells}
    p = tmp_path / "cellpr.json"
    p.write_text(json.dumps(pr))
    return str(p), pr


# ---------------------------------------------------------------- the head path is UNCHANGED

@pytest.mark.parametrize("rel,tag,n", HEAD_FAMILIES)
def test_head_families_build_the_expected_number_of_arms(rel, tag, n):
    m = _mod()
    arms = m.all_arms(_pr(rel))
    assert len(arms) == n, f"{rel} built {len(arms)} arms, expected {n}"
    assert all(len(t) == 3 for t in arms), "all_arms must return (arm, heads, cells) triples"
    assert all(c is None for _, _, c in arms), "a head family must carry no cell lists"


@pytest.mark.parametrize("rel,tag,n", HEAD_FAMILIES)
def test_S260_the_clean_reference_arm_CARRIES_NO_INTERVENTION(rel, tag, n):
    """THE S-260 REGRESSION, on every family. This is the bug that voided job 918967."""
    m = _mod()
    pr = _pr(rel)
    b0 = m.base_arms_of(pr)[0]
    av = m.argv_for(b0, None, "validation", pr, 20260913, tag)
    for flag in ("--intervene", "--knockout-scope", "--knockout-heads", "--knockout-cells"):
        assert flag not in av, (
            f"{rel}: clean reference {b0} carries {flag} -- an intervened arm standing in as the "
            f"baseline, which is exactly S-260")


@pytest.mark.parametrize("rel,tag,n", HEAD_FAMILIES)
def test_every_non_base_arm_IS_intervened(rel, tag, n):
    m = _mod()
    pr = _pr(rel)
    b0 = m.base_arms_of(pr)[0]
    for arm, heads, cells in m.all_arms(pr):
        if arm == b0:
            continue
        av = m.argv_for(arm, heads, "validation", pr, 20260913, tag, cells=cells)
        assert "--intervene" in av, f"{rel}: arm {arm} carries no --intervene"


@pytest.mark.parametrize("rel,tag,n", HEAD_FAMILIES)
def test_the_KO_denominator_arm_carries_NO_head_list(rel, tag, n):
    """base_arms[1] is the all-32 knockout; an empty list is how 'all heads' is expressed."""
    m = _mod()
    pr = _pr(rel)
    b1 = m.base_arms_of(pr)[1]
    av = m.argv_for(b1, None, "validation", pr, 20260913, tag)
    assert "--intervene" in av and "--knockout-heads" not in av


# ---------------------------------------------------------------- the cell path

def test_cell_family_emits_knockout_cells_and_never_knockout_heads(tmp_path):
    m = _mod()
    path, pr = _cellpr(tmp_path)
    for arm, heads, cells in m.all_arms(pr):
        av = m.argv_for(arm, heads, "validation", pr, 20260913, "csi7_cell_basket", cells=cells)
        assert "--knockout-heads" not in av, f"cell arm {arm} emitted a HEAD selector"
        if cells is not None:
            i = av.index("--knockout-cells") + 1
            assert av[i] == ",".join("%d:%d" % (L, h) for L, h in cells), av[i]


def test_cell_family_base_arms_are_head_level(tmp_path):
    """base[0] clean, base[1] the all-32/all-band denominator: neither is cell-scoped."""
    m = _mod()
    path, pr = _cellpr(tmp_path)
    arms = m.all_arms(pr)
    assert arms[0] == ("CL_BASE", None, None)
    assert arms[1] == ("CL_KO", None, None)
    assert len(arms) == 11


def test_cell_arm_count_and_ordering(tmp_path):
    m = _mod()
    path, pr = _cellpr(tmp_path)
    names = [a for a, _, _ in m.all_arms(pr)]
    assert names == ["CL_BASE", "CL_KO"] + ["CL_L%02d" % L for L in range(6, 15)]


def test_a_prereg_with_BOTH_head_sets_and_cell_sets_is_REFUSED(tmp_path):
    m = _mod()
    path, pr = _cellpr(tmp_path)
    pr["head_sets"] = {"X": [1]}
    with pytest.raises(SystemExit) as e:
        m.all_arms(pr)
    assert "BOTH head_sets and cell_sets" in str(e.value)


def test_a_base_arm_inside_cell_sets_is_REFUSED(tmp_path):
    m = _mod()
    path, pr = _cellpr(tmp_path)
    pr["cell_sets"]["CL_BASE"] = [[10, 2]]
    with pytest.raises(SystemExit) as e:
        m.all_arms(pr)
    assert "also appears in cell_sets" in str(e.value)


def test_an_arm_carrying_BOTH_selectors_is_REFUSED(tmp_path):
    """score_behavior refuses this too (S-291); the generator refuses first and names the arm."""
    m = _mod()
    path, pr = _cellpr(tmp_path)
    with pytest.raises(SystemExit) as e:
        m.argv_for("CL_L10", [2], "validation", pr, 20260913, "csi7", cells=[(10, 2)])
    assert "BOTH a head list and a cell list" in str(e.value)


# ---------------------------------------------------------------- what --check catches

def _run_check(m, prereg_path, tag):
    sys.argv = ["x", "--prereg", prereg_path, "--split", "validation", "--tag-prefix", tag,
                "--check"]
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        m.main()
    return buf.getvalue()


def test_check_passes_on_a_wellformed_cell_family(tmp_path):
    m = _mod()
    path, pr = _cellpr(tmp_path)
    out = _run_check(m, path, "csi7_cell_basket")
    assert "CHECK PASSED" in out
    assert "9 arms carry a frozen cell list" in out, out
    assert "BASE-ARM CHECK PASSED" in out


def test_check_CATCHES_a_corrupted_EMISSION(tmp_path):
    """The real guarantee: if argv_for mangles a cell list, --check refuses.

    S-260 was an EMISSION bug, so this is the failure mode that actually occurred."""
    m = _mod()
    path, pr = _cellpr(tmp_path)
    orig = m.argv_for

    def broken(arm, heads, split, prereg, seed, tag_prefix, cells=None):
        av = orig(arm, heads, split, prereg, seed, tag_prefix, cells=cells)
        if "--knockout-cells" in av:
            i = av.index("--knockout-cells") + 1
            if av[i] == "10:2":
                av[i] = "10:19"
        return av

    m.argv_for = broken
    with pytest.raises(SystemExit) as e:
        _run_check(m, path, "csi7_cell_basket")
    assert "cell list drifted from the prereg" in str(e.value)


def test_check_does_NOT_validate_the_PREREG_ITSELF_and_that_is_BY_DESIGN(tmp_path):
    """⚠ A LIMITATION RECORDED AS A TEST so nobody over-trusts the phrase "drifted from the prereg".

    `all_arms` reads the cell list FROM the prereg and `--check` compares the emission back AGAINST the
    prereg, so both sides have one source: editing the prereg moves them together and is NOT caught.
    The head path has always had this property too.

    That is not a hole in the wrong place. Prereg correctness is guaranteed by a DIFFERENT mechanism --
    the prereg is emitted mechanically by a freeze script and its md5 is pinned by the artefacts that
    cite it (`EMITTED_MECHANICALLY_BY`, `nomination_rule_md5`). This check's job is EMISSION INTEGRITY.
    If this test ever fails because the tamper IS caught, the check grew a capability and this docstring
    should be rewritten rather than the assertion loosened."""
    m = _mod()
    path, pr = _cellpr(tmp_path)
    pr["cell_sets"]["CL_L10"] = [[10, 19]]          # a WRONG prereg, self-consistently wrong
    p2 = tmp_path / "tampered.json"
    p2.write_text(json.dumps(pr))
    out = _run_check(m, str(p2), "csi7_cell_basket")
    assert "CHECK PASSED" in out, (
        "the check now catches a tampered prereg -- good, but the claim in this test's docstring is "
        "stale and must be rewritten")
