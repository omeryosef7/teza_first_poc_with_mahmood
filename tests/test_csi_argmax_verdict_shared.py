"""The argmax verdict lives in ONE place, and PR-CSI-020's published read still reproduces.

S-402 moved the verdict body out of dcs_csi_pr016_argmax_test.py so that PR-CSI-021 (rung 2) can
apply the SAME statistic to a DIFFERENT quantity. S-389 settled that it must be the same; S-350
measured what the alternative is worth -- two "independent implementations" of this statistic
agreed ONLY at M = K, and the difference would have published a PASS against a prereg recording
that it could not certify.
"""
import importlib.util
import json
import os
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PY = sys.executable
SHARED = os.path.join(ROOT, "scripts", "dcs_csi_argmax_verdict.py")
READER = os.path.join(ROOT, "scripts", "dcs_csi_pr016_argmax_test.py")


def _code(path):
    out = []
    for line in open(path, encoding="utf-8").read().splitlines():
        out.append("" if line.lstrip().startswith("#") else line.split("#")[0])
    return "\n".join(out)


def test_the_verdict_is_defined_ONCE():
    """The reader must CALL the shared verdict, not carry its own copy of the branches."""
    rc = _code(READER)
    assert "_verdict.decide(" in rc, "the reader no longer calls the shared verdict"
    # the branch texts must live in the shared module and NOT be duplicated in the reader
    for marker in ("STRUCTURALLY UNWINNABLE", "the SPANNING RULE is violated",
                   "a tie for the argmax on head"):
        assert marker in _code(SHARED), "%r is missing from the shared verdict" % marker
        assert marker not in rc, (
            "%r is ALSO in the reader -- the branches have been duplicated, which is exactly the "
            "drift S-350 measured" % marker)


def test_the_shared_module_still_carries_its_provenance_comments():
    """The body was MOVED, not retyped, so the R28/R29/R30-B fixes embedded in its comments must
    travel with it. If someone rewrites it clean, the reasons are lost and the bugs come back."""
    src = open(SHARED, encoding="utf-8").read()
    for tag in ("R29/S-322", "R29/S-323", "R30-B/S-332", "R28/S-312"):
        assert tag in src, "the %s rationale was dropped in the move" % tag


def test_PR_CSI_020s_published_read_still_reproduces(tmp_path):
    """⛔ THE GATE ON THE REFACTOR. A published verdict may not move because the code was tidied."""
    prereg = os.path.join(ROOT, "configs", "dcs_csi_pr020_cell_census_basket_8heads.json")
    census = os.path.join(ROOT, "reports",
                          "DCS_CSI_PR020_CELL_CENSUS_basket_8heads_validation.json")
    published = os.path.join(ROOT, "reports",
                             "DCS_CSI_PR020_ARGMAX_TEST_basket_8heads_validation.json")
    for f in (prereg, census, published):
        if not os.path.exists(f):
            pytest.skip("PR-CSI-020 artefacts absent in this checkout")
    out = str(tmp_path / "again.json")
    r = subprocess.run([PY, READER, "--prereg", prereg, "--census", census, "--out", out],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    a, b = json.load(open(published)), json.load(open(out))
    for k in ("VERDICT", "K_admitted", "M_matches", "p_one_sided", "gating_p_name", "gating_p",
              "why", "matching_layers", "spanning_rule_satisfied"):
        assert a[k] == b[k], "%s MOVED: %r -> %r" % (k, a[k], b[k])
    # ⚠ S-428, THE ONE NAMED EXCEPTION, AND IT GATES MORE THAN IT EXCLUDES. The published artefact
    # carries a GATING_FLOOR.WHAT_THIS_IS sentence that is FALSE at K >= 3 -- it claimed a floor
    # above alpha yields "CANNOT ANSWER (structural), never FAIL", which the verdict module rejects
    # by name. The PUBLISHED FILE IS NOT REWRITTEN: it records what was read, and AM-45's
    # byte-identity claim rests on it. So this one prose field is compared by CONTRACT rather than
    # by equality -- the old text must be gone from the new output and the corrected text present.
    _old_gf = a["ROBUSTNESS"].pop("GATING_FLOOR")
    _new_gf = b["ROBUSTNESS"].pop("GATING_FLOOR")
    for _k in ("name", "p", "parts"):
        assert _old_gf[_k] == _new_gf[_k], "GATING_FLOOR.%s MOVED: %r -> %r" % (
            _k, _old_gf[_k], _new_gf[_k])
    assert "never FAIL" in _old_gf["WHAT_THIS_IS"], "the published artefact no longer carries the " \
        "false sentence this exception exists for -- delete the exception"
    assert "never FAIL" not in _new_gf["WHAT_THIS_IS"]
    assert "NEVER changes the verdict" in _new_gf["WHAT_THIS_IS"]
    assert a["ROBUSTNESS"] == b["ROBUSTNESS"], "ROBUSTNESS moved"
    for x in (a, b):
        # ⚠ these three record the INVOCATION, not the verdict: a timestamp and the two input
        # paths as typed. This test passes absolute paths where the published run used relative
        # ones, so comparing them would fail for a reason that has nothing to do with the
        # statistic. Everything that DECIDES anything is compared above and below.
        x.pop("generated_utc", None)
        x.pop("census_report", None)
        x.pop("prereg", None)
    assert a == b, "the published verdict JSON is not reproduced exactly"


def test_binom_tail_agrees_with_the_readers_own_math():
    """The shared module exposes binom_tail; it must be the same function the reader used."""
    spec = importlib.util.spec_from_file_location("shared", SHARED)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    from math import comb
    for K, M, p0 in ((8, 6, 1 / 9.), (4, 3, 1 / 9.), (8, 8, 1 / 9.), (3, 0, 1 / 9.)):
        want = sum(comb(K, i) * p0 ** i * (1 - p0) ** (K - i) for i in range(M, K + 1))
        assert abs(m.binom_tail(M, K, p0) - want) < 1e-15


def test_s421_structural_K_lt_3_sentence_matches_the_arithmetic():
    """S-421: the K<3 structural branch asserted "floor > alpha" UNCONDITIONALLY.

    The branch fires when the GATING p exceeds alpha at K < 3, which does not imply the FLOOR does.
    On a PR-CSI-016-shaped K=2/M=1 read the floor is the binomial 0.012346 -- BELOW alpha -- and the
    emitted sentence read "binomial = 0.012346 > alpha = 0.05". The verdict was right; the sentence
    justifying it was false. This fails on the pre-S-421 text."""
    spec = importlib.util.spec_from_file_location("_v_s421", SHARED)
    V = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(V)
    band = list(range(6, 15))
    rows = [{"head": 17, "screen_predicted_layer": 14, "argmax_layer": 14,
             "argmax_is_a_TIE": False, "COUNTED_IN_M": True},
            {"head": 19, "screen_predicted_layer": 14, "argmax_layer": 9,
             "argmax_is_a_TIE": False, "COUNTED_IN_M": False}]
    d = V.decide(rows, band, 0.05, None, "PR-CSI-016")
    assert d["verdict"] == "CANNOT ANSWER"
    why = d["why"]
    assert "STRUCTURAL: K=2" in why
    # the floor here is BELOW alpha, so the text must NOT claim it exceeds alpha
    assert "0.012346 > alpha" not in why, "the sentence asserts a false inequality: %s" % why
    assert "<= alpha" in why and "The reason is K alone" in why

    # and the >alpha case must still say so: K=2 with M=0 forces the permutation floor of 0.5
    rows2 = [{"head": 4, "screen_predicted_layer": 11, "argmax_layer": 7,
              "argmax_is_a_TIE": False, "COUNTED_IN_M": False},
             {"head": 6, "screen_predicted_layer": 8, "argmax_layer": 9,
              "argmax_is_a_TIE": False, "COUNTED_IN_M": False}]
    d2 = V.decide(rows2, band, 0.05, "weakest_of_three", "PR-CSI-020")
    assert d2["verdict"] == "CANNOT ANSWER"
    assert "> alpha" in d2["why"] and "NO outcome could have certified" in d2["why"]


def test_s428_gating_floor_prose_does_not_claim_the_floor_changes_the_verdict():
    """S-428: the emitted GATING_FLOOR text asserted "CANNOT ANSWER (structural), never FAIL"
    unconditionally, and SHIPPED that way in D39 and D40.

    The verdict module rejects that rule by name. At K >= 3 a gating p above alpha is a FAIL with
    the floor reported beside it; CANNOT ANSWER (structural) is reached only at K < 3. Fails on the
    pre-S-428 string."""
    src = open(os.path.join(ROOT, "scripts", "dcs_csi_pr016_argmax_test.py"), encoding="utf-8").read()
    i = src.find('"WHAT_THIS_IS"')
    assert i > 0, "the GATING_FLOOR WHAT_THIS_IS field is gone"
    blob = src[i:i + 1200]
    assert "never FAIL" not in blob, "the emitted prose still claims the floor overrides a FAIL"
    assert "NEVER changes the verdict" in blob
    assert "only at K < 3" in blob

    # and the behaviour the prose must match, executed
    spec = importlib.util.spec_from_file_location("_v_s428", SHARED)
    V = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(V)
    band = list(range(6, 15))
    rows = [{"head": h, "screen_predicted_layer": p, "argmax_layer": a,
             "argmax_is_a_TIE": False, "COUNTED_IN_M": False}
            for h, p, a in ((1, 6, 7), (2, 8, 9), (3, 10, 11), (4, 12, 13))]
    d = V.decide(rows, band, 0.05, "weakest_of_three", "PR-CSI-020")
    assert d["verdict"] == "FAIL", "K>=3 with the floor above alpha must FAIL, not CANNOT ANSWER"
