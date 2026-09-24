"""PR-CSI-016's primary reader: every verdict branch must be reachable and correct.

R3-B1 (S-057) found a verdict whose PASS branch was DEAD CODE and whose FAIL text was false. This
file exists so that cannot recur here: each branch is driven by a synthetic census report and
asserted, BEFORE any button arm has run.
"""
import json
import os
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PY = sys.executable
READER = os.path.join(ROOT, "scripts", "dcs_csi_pr016_argmax_test.py")
PR016 = os.path.join(ROOT, "configs", "dcs_csi_pr016_cell_census_button.json")
BAND = list(range(6, 15))


def _census(tmp_path, peaks, admit=(True, True, True), whole=-0.030, bar=0.006, tie=None):
    """A synthetic PR-CSI-016 census report. `peaks` maps head -> the layer that will carry the
    largest |E|; `admit` decides whether each head's whole-head arm clears the admission gate."""
    pr = json.load(open(PR016))
    E, CI = {}, {}
    for i, h in enumerate([str(x) for x in pr["heads"]]):
        src = pr["DETECTABILITY_PREREGISTERED_PER_HEAD"]["per_head"][h]["bar_source_arm"]
        e = whole if admit[i] else -0.0005
        E[src] = e
        CI[src] = [e - 0.004, e + 0.004] if admit[i] else [-0.004, 0.004]
        for L in BAND:
            E["BC_H%s_L%02d" % (h, L)] = -0.0005
            CI["BC_H%s_L%02d" % (h, L)] = [-0.002, 0.001]
        E["BC_H%s_L%02d" % (h, peaks[h])] = -0.025
        if tie == int(h):                       # a second cell with the identical |E|
            other = next(L for L in BAND if L != peaks[h])
            E["BC_H%s_L%02d" % (h, other)] = -0.025
    E["BC_KO"] = -0.22
    CI["BC_KO"] = [-0.27, -0.18]
    rep = {
        "prereg_id": "PR-CSI-016", "split": "validation", "ON_PROTOCOL": True,
        # ⚠⚠ R28/S-312. THIS HELPER IS WHY A BLOCKER SURVIVED NINE GREEN TESTS. It used to emit
        # {"all_pass": True} -- a key scripts/dcs_csi_head_census.py has NEVER written. The reader
        # gated on it, so it refused every REAL census report while every test passed. A test that
        # invents its input validates the test, not the code. The shape below is the one the census
        # actually writes, and test_the_synthetic_census_shape_matches_the_REAL_one pins it against a
        # published report so this cannot drift again.
        "GATE_0_and_identity": {"per_arm": {k: {"pass": True} for k in list(E) + ["BC_BASE"]},
                                "identity": {}},
        "E": E, "ci95": CI,
        "CELL_FAMILY": {"bars_COMPUTED_FROM_A_FROZEN_RULE": {
            h: {"bar": bar, "source_arm":
                pr["DETECTABILITY_PREREGISTERED_PER_HEAD"]["per_head"][h]["bar_source_arm"]}
            for h in [str(x) for x in pr["heads"]]}},
    }
    p = tmp_path / "census.json"
    p.write_text(json.dumps(rep))
    return str(p)


def _run(tmp_path, census):
    out = tmp_path / "verdict.json"
    r = subprocess.run([PY, READER, "--prereg", PR016, "--census", census, "--out", str(out)],
                       capture_output=True, text=True)
    assert r.returncode == 0, (r.stdout + r.stderr)[-800:]
    return json.load(open(out)), r.stdout


pytestmark = pytest.mark.skipif(not os.path.exists(PR016), reason="PR-CSI-016 prereg not emitted")


def test_PASS_requires_both_a_small_p_AND_a_spanning_match(tmp_path):
    """The basket-shaped outcome: 17->L14, 19->L14, 23->L7, all three matching. M=3, K=3,
    p=0.001372, matches span TWO layers."""
    v, out = _run(tmp_path, _census(tmp_path, {"17": 14, "19": 14, "23": 7}))
    assert v["VERDICT"] == "PASS", v["why"]
    assert v["K_admitted"] == 3 and v["M_matches"] == 3
    assert abs(v["p_one_sided"] - 0.001372) < 1e-5
    assert v["spanning_rule_satisfied"] and v["matching_layers"] == ["L7", "L14"]


def test_the_SPANNING_RULE_blocks_the_shared_bias_pass(tmp_path):
    """⚠ THE ONE THIS FAMILY MOST NEEDS. Heads 17 and 19 both match at L14 and head 23 misses:
    M=2, K=3, p=0.0343 <= 0.05, which WOULD read as a pass. But both matches sit on the band edge,
    so a shared depth bias and a correct screen are indistinguishable. Must be CANNOT ANSWER."""
    v, out = _run(tmp_path, _census(tmp_path, {"17": 14, "19": 14, "23": 11}))
    assert v["M_matches"] == 2 and v["p_one_sided"] <= 0.05, "the hazard did not arise as designed"
    assert v["VERDICT"] == "CANNOT ANSWER", v["why"]
    assert not v["spanning_rule_satisfied"]
    assert "SPANNING RULE" in v["why"] and "NOT quotable as a pass" in v["why"]


def test_a_spanning_two_of_three_DOES_pass(tmp_path):
    """The companion: a rule that refused every M=2 would be refusing on count, not on bias.
    19->L14 and 23->L7 match, 17 misses: two matches on two different layers."""
    v, _ = _run(tmp_path, _census(tmp_path, {"17": 11, "19": 14, "23": 7}))
    assert v["M_matches"] == 2 and v["VERDICT"] == "PASS", v["why"]
    assert v["matching_layers"] == ["L7", "L14"]


def test_FAIL_when_the_screen_predicts_no_better_than_chance(tmp_path):
    v, _ = _run(tmp_path, _census(tmp_path, {"17": 11, "19": 10, "23": 12}))
    assert v["VERDICT"] == "FAIL" and v["M_matches"] == 0, v["why"]


def test_K1_is_CANNOT_ANSWER_because_the_floor_cannot_clear_alpha(tmp_path):
    """Two heads dropped by the ADMISSION gate. Even a perfect single match gives 1/9 = 0.1111."""
    v, _ = _run(tmp_path, _census(tmp_path, {"17": 14, "19": 14, "23": 7},
                                  admit=(False, True, False)))
    assert v["K_admitted"] == 1 and v["VERDICT"] == "CANNOT ANSWER", v["why"]
    assert "floor" in v["why"]
    assert len(v["dropped_heads"]) == 2
    assert all("NOT_A_MISS" in d for d in v["dropped_heads"])


def test_a_dropped_head_is_not_counted_against_the_screen(tmp_path):
    """PROPERTY: admission removes a head from K; it must never appear as a miss. Head 17 is dropped
    and the remaining two match on two layers -> PASS at K=2, not FAIL at K=3."""
    v, _ = _run(tmp_path, _census(tmp_path, {"17": 14, "19": 14, "23": 7},
                                  admit=(False, True, True)))
    assert v["K_admitted"] == 2 and v["M_matches"] == 2
    assert v["VERDICT"] == "PASS" and abs(v["p_one_sided"] - 0.012346) < 1e-5


def test_a_TIE_for_the_argmax_is_CANNOT_ANSWER(tmp_path):
    v, _ = _run(tmp_path, _census(tmp_path, {"17": 14, "19": 14, "23": 7}, tie=19))
    assert v["VERDICT"] == "CANNOT ANSWER" and "tie" in v["why"].lower(), v["why"]


PR015_REPORT = os.path.join(ROOT, "reports", "DCS_CSI_PR015_CELL_CENSUS_3HEADS_validation.json")


@pytest.mark.skipif(not os.path.exists(PR015_REPORT), reason="a published census report is needed")
def test_the_synthetic_census_shape_matches_the_REAL_one():
    """R28/S-312. The BLOCKER was a reader gating on a key its producer never writes, hidden by a
    helper that fabricated that key. PROPERTY: whatever GATE 0 record this file synthesises must have
    the same shape as the one `dcs_csi_head_census.py` actually publishes. Pinned against a real
    committed report so the two cannot drift apart again."""
    real = json.load(open(PR015_REPORT))["GATE_0_and_identity"]
    import tempfile, pathlib
    with tempfile.TemporaryDirectory() as td:
        fake = json.load(open(_census(pathlib.Path(td), {"17": 14, "19": 14, "23": 7})))
    assert set(fake["GATE_0_and_identity"]) <= set(real), (
        "the synthetic GATE 0 record carries keys the real census never writes: %s"
        % (set(fake["GATE_0_and_identity"]) - set(real)))
    assert "per_arm" in real and isinstance(real["per_arm"], dict) and real["per_arm"]
    a_real_arm = next(iter(real["per_arm"].values()))
    assert "pass" in a_real_arm, "the census no longer records a per-arm 'pass'; the reader's GATE 0 "                                  "check is keyed on it"


def test_the_reader_refuses_a_census_with_a_FAILING_ARM_however_cheerful_the_summary(tmp_path):
    """The check must consult the per-arm record, not a summary flag. A report with one failing arm
    and an optimistic top-level flag must still be refused."""
    c = _census(tmp_path, {"17": 14, "19": 14, "23": 7})
    rep = json.load(open(c))
    rep["GATE_0_and_identity"]["per_arm"]["BC_H17_L06"]["pass"] = False
    rep["GATE_0_and_identity"]["all_pass"] = True          # the cheerful summary
    open(c, "w").write(json.dumps(rep))
    r = subprocess.run([PY, READER, "--prereg", PR016, "--census", c,
                        "--out", str(tmp_path / "x.json")], capture_output=True, text=True)
    out = r.stdout + r.stderr
    assert r.returncode != 0 and "GATE 0 did not pass" in out and "BC_H17_L06" in out, out[-400:]


def test_the_reader_refuses_a_census_with_no_per_arm_record_at_all(tmp_path):
    c = _census(tmp_path, {"17": 14, "19": 14, "23": 7})
    rep = json.load(open(c))
    rep["GATE_0_and_identity"] = {"all_pass": True}        # the shape the BLOCKER assumed
    open(c, "w").write(json.dumps(rep))
    r = subprocess.run([PY, READER, "--prereg", PR016, "--census", c,
                        "--out", str(tmp_path / "x.json")], capture_output=True, text=True)
    out = r.stdout + r.stderr
    assert r.returncode != 0 and "Absence is not a pass" in out, out[-400:]


def test_the_reader_refuses_a_TRAIN_split_report(tmp_path):
    c = _census(tmp_path, {"17": 14, "19": 14, "23": 7})
    rep = json.load(open(c))
    rep["split"] = "train"
    open(c, "w").write(json.dumps(rep))
    r = subprocess.run([PY, READER, "--prereg", PR016, "--census", c,
                        "--out", str(tmp_path / "x.json")], capture_output=True, text=True)
    assert r.returncode != 0 and "VALIDATION read" in (r.stdout + r.stderr)


def test_a_dropped_head_whose_argmax_DID_match_is_not_published_as_a_mismatch(tmp_path):
    """R28/S-312: ARGMAX_EQUALS_SCREEN is the observation, COUNTED_IN_M is the scoring decision.
    A head declined by ADMISSION must not appear to contradict the screen."""
    v, _ = _run(tmp_path, _census(tmp_path, {"17": 14, "19": 14, "23": 7},
                                  admit=(False, True, True)))
    h17 = next(r for r in v["per_head"] if r["head"] == 17)
    assert h17["ADMITTED"] is False
    assert h17["ARGMAX_EQUALS_SCREEN"] is True, "the observation was suppressed by the scoring rule"
    assert h17["COUNTED_IN_M"] is False


def test_a_tie_publishes_NO_quotable_M_or_p(tmp_path):
    v, _ = _run(tmp_path, _census(tmp_path, {"17": 14, "19": 14, "23": 7}, tie=19))
    assert v["VERDICT"] == "CANNOT ANSWER"
    assert v["M_matches"] is None and v["p_one_sided"] is None, (
        "a tied head is undetermined, but M/p were published anyway: %r / %r"
        % (v["M_matches"], v["p_one_sided"]))


def test_a_spanning_CANNOT_ANSWER_does_not_publish_the_IF_NULL_prohibitions(tmp_path):
    """R28/S-312: the spanning branch fires with p <= alpha -- a positive-looking number in hand --
    so publishing 'the screen is useless' there is both wrong and harmful."""
    v, _ = _run(tmp_path, _census(tmp_path, {"17": 14, "19": 14, "23": 11}))
    assert v["VERDICT"] == "CANNOT ANSWER" and v["p_one_sided"] <= 0.05
    joined = " ".join(v["MUST_NOT_BE_SAID"])
    assert "CANNOT ANSWER is NOT a null" in joined
    assert v["MUST_NOT_BE_SAID"] != json.load(open(PR016))["MUST_NOT_BE_SAID_IF_NULL"]


def test_the_null_comes_from_the_BAND_not_a_hardcoded_ninth(tmp_path):
    v, _ = _run(tmp_path, _census(tmp_path, {"17": 14, "19": 14, "23": 7}))
    assert v["n_band_layers"] == len(json.load(open(PR016))["layers"])
    assert abs(v["null_p_per_head"] - 1.0 / v["n_band_layers"]) < 1e-15


def test_the_reader_refuses_a_census_that_did_not_pass_GATE_0(tmp_path):
    c = _census(tmp_path, {"17": 14, "19": 14, "23": 7})
    rep = json.load(open(c))
    for v in rep["GATE_0_and_identity"]["per_arm"].values():
        v["pass"] = False
    open(c, "w").write(json.dumps(rep))
    r = subprocess.run([PY, READER, "--prereg", PR016, "--census", c,
                        "--out", str(tmp_path / "x.json")], capture_output=True, text=True)
    assert r.returncode != 0 and "GATE 0" in (r.stdout + r.stderr)


def test_the_reader_refuses_a_missing_report_by_NAME_not_by_traceback(tmp_path):
    r = subprocess.run([PY, READER, "--prereg", PR016, "--census", str(tmp_path / "nope.json"),
                        "--out", str(tmp_path / "x.json")], capture_output=True, text=True)
    out = r.stdout + r.stderr
    assert r.returncode != 0 and "REFUSING" in out and "Traceback" not in out, out[-400:]


# ================================================================ R29 / S-322
# Two BLOCKERs found by RUNNING the frozen STEP 2 on a real-shaped PR-CSI-018 census, after S-321 had
# "widened" the reader by changing only its id check. Both are the same shape: a property specific to
# PR-CSI-016 left hardcoded where the widening did not look.

PR018 = os.path.join(ROOT, "configs", "dcs_csi_pr018_cell_census_button_nonL14.json")


def _census018(tmp_path, peaks, admit=None, bar=0.018, whole=-0.030):
    """A PR-CSI-018 census in the shape dcs_csi_head_census.py actually emits."""
    pr = json.load(open(PR018))
    heads, band = pr["heads"], pr["layers"]
    admit = admit or [True] * len(heads)
    inv = {}
    for arm, cells in pr["cell_sets"].items():
        if len(cells) == 1:
            inv[(int(cells[0][1]), int(cells[0][0]))] = arm
    E, CI, per = {}, {}, {"BF_BASE": {"pass": True}, "BF_KO": {"pass": True}}
    for i, h in enumerate(heads):
        src = pr["DETECTABILITY_PREREGISTERED_PER_HEAD"]["per_head"][str(h)]["bar_source_arm"]
        e = whole if admit[i] else -0.0004
        E[src] = e
        CI[src] = [e - 0.004, e + 0.004] if admit[i] else [-0.004, 0.004]
        per[src] = {"pass": True}
        for L in band:
            E[inv[(h, L)]] = -0.0005
            CI[inv[(h, L)]] = [-0.002, 0.001]
            per[inv[(h, L)]] = {"pass": True}
        E[inv[(h, peaks[h])]] = -0.025
    E["BF_KO"] = -0.29
    CI["BF_KO"] = [-0.34, -0.24]
    rep = {"prereg_id": "PR-CSI-018", "split": "validation", "ON_PROTOCOL": True,
           "GATE_0_and_identity": {"per_arm": per, "identity": {}}, "E": E, "ci95": CI,
           "CELL_FAMILY": {"bars_COMPUTED_FROM_A_FROZEN_RULE": {
               str(h): {"bar": bar, "source_arm":
                        pr["DETECTABILITY_PREREGISTERED_PER_HEAD"]["per_head"][str(h)]["bar_source_arm"]}
               for h in heads}}}
    p = tmp_path / "c018.json"
    p.write_text(json.dumps(rep))
    return str(p), pr


def _run018(tmp_path, census):
    out = tmp_path / "v018.json"
    r = subprocess.run([PY, READER, "--prereg", PR018, "--census", census, "--out", str(out)],
                       capture_output=True, text=True)
    assert r.returncode == 0, (r.stdout + r.stderr)[-700:]
    return json.load(open(out))


pytestmark018 = pytest.mark.skipif(not os.path.exists(PR018), reason="PR-CSI-018 prereg not emitted")


@pytest.mark.skipif(not os.path.exists(PR018), reason="PR-CSI-018 prereg not emitted")
def test_cell_arm_names_come_from_the_PREREG_not_a_hardcoded_prefix(tmp_path):
    """R29 BLOCKER 1. The reader built cell-arm names as "BC_H%s_L%02d" -- PR-CSI-016's prefix,
    hardcoded. PR-CSI-018 uses BF_, so the widened reader REFUSED a well-formed PR-018 census with
    "head 6's single-cell arms are absent from the census report".
    PROPERTY: the reader resolves each (head, layer) to an arm via the prereg's own cell_sets, so no
    naming convention is assumed and a family may call its arms anything."""
    pr = json.load(open(PR018))
    sp = pr["DETECTABILITY_PREREGISTERED_PER_HEAD"]["per_head"]
    peaks = {h: sp[str(h)]["screen_predicted_layer"] for h in pr["heads"]}
    c, _ = _census018(tmp_path, peaks)
    v = _run018(tmp_path, c)
    assert v["K_admitted"] == len(pr["heads"]) and v["M_matches"] == len(pr["heads"])
    assert not any(a.startswith("BC_") for a in pr["cell_sets"]), \
        "this test is vacuous unless PR-018's arms use a different prefix from PR-016's"


@pytest.mark.skipif(not os.path.exists(PR018), reason="PR-CSI-018 prereg not emitted")
def test_GATING_is_the_PREREGS_decision_and_weakest_of_three_can_FAIL_a_passing_binomial(tmp_path):
    """R29 BLOCKER 2, and the worse of the two. PR-CSI-016 froze GATING binomial_only (its
    co-primaries bound the wording); PR-CSI-018 froze weakest_of_three, because it was BUILT so the
    permutation test is answerable. The reader applied PR-016's rule to both and printed PASS on a
    PR-018 census whose weakest p was 0.21, and again at 0.33.
    PROPERTY: under weakest_of_three a large conditional or permutation p FAILS the family even when
    the binomial passes comfortably."""
    pr = json.load(open(PR018))
    assert pr["PRIMARY"]["GATING"] == "weakest_of_three"
    sp = pr["DETECTABILITY_PREREGISTERED_PER_HEAD"]["per_head"]
    heads = pr["heads"]
    peaks = {h: sp[str(h)]["screen_predicted_layer"] for h in heads}
    # break three of the six matches: binomial stays < 0.05, the conditional does not
    for h in heads[:3]:
        peaks[h] = next(L for L in pr["layers"] if L != sp[str(h)]["screen_predicted_layer"])
    v = _run018(tmp_path, _census018(tmp_path, peaks)[0])
    assert v["M_matches"] == 3
    assert v["p_one_sided"] <= 0.05, "the binomial must still pass, or this test proves nothing"
    assert v["gating_p"] > 0.05 and v["VERDICT"] == "FAIL", (
        "weakest-of-three did not gate: gating_p=%r verdict=%r" % (v.get("gating_p"), v["VERDICT"]))
    assert v["GATING"] == "weakest_of_three"


@pytest.mark.skipif(not os.path.exists(PR018), reason="PR-CSI-018 prereg not emitted")
def test_a_small_K_cannot_PASS_on_the_binomial_when_the_permutation_floor_is_high(tmp_path):
    """The damning case: with only 3 heads admitted the permutation floor is 1/3, so a perfect
    M=K=3 must FAIL under weakest_of_three -- the reader used to call it PASS at p_perm = 0.333."""
    pr = json.load(open(PR018))
    sp = pr["DETECTABILITY_PREREGISTERED_PER_HEAD"]["per_head"]
    heads = pr["heads"]
    peaks = {h: sp[str(h)]["screen_predicted_layer"] for h in heads}
    v = _run018(tmp_path, _census018(tmp_path, peaks, admit=[True, True, True, False, False, False])[0])
    assert v["K_admitted"] == 3 and v["M_matches"] == 3
    assert v["p_one_sided"] <= 0.05, "binomial must pass, or the test proves nothing"
    assert v["VERDICT"] == "FAIL" and v["gating_p_name"] == "permutation"


@pytest.mark.skipif(not os.path.exists(PR018), reason="PR-CSI-018 prereg not emitted")
def test_an_unknown_GATING_value_is_REFUSED_rather_than_silently_defaulted(tmp_path):
    pr = json.load(open(PR018))
    pr["PRIMARY"]["GATING"] = "whatever_passes"
    p = tmp_path / "bad.json"
    p.write_text(json.dumps(pr))
    sp = pr["DETECTABILITY_PREREGISTERED_PER_HEAD"]["per_head"]
    peaks = {h: sp[str(h)]["screen_predicted_layer"] for h in pr["heads"]}
    c, _ = _census018(tmp_path, peaks)
    r = subprocess.run([PY, READER, "--prereg", str(p), "--census", c, "--out", str(tmp_path / "x.json")],
                       capture_output=True, text=True)
    assert r.returncode != 0 and "GATING" in (r.stdout + r.stderr)


def test_PR016_still_gates_on_the_binomial_alone(tmp_path):
    """The companion: S-322 must not retro-apply PR-018's rule to PR-016, whose prereg explicitly says
    the co-primaries do NOT gate. Its published read had a weakest p of 1.0 and a binomial of 0.0123."""
    v = json.load(open(os.path.join(ROOT, "reports",
                                    "DCS_CSI_PR016_ARGMAX_TEST_button_validation.json")))
    assert v["VERDICT"] == "CANNOT ANSWER"
    assert v["ROBUSTNESS"]["p_conditional"] == 1.0 and v["ROBUSTNESS"]["p_permutation"] == 1.0
    pr16 = json.load(open(PR016))
    assert "GATING" not in pr16["PRIMARY"], "PR-016 must remain on the default binomial_only path"


# ================================================================ R30-B / S-332
# Three defects R30-B demonstrated on synthetic censuses built in the census's own output shape,
# each of which would have fired on the real PR-CSI-018 read.


@pytest.mark.skipif(not os.path.exists(PR018), reason="PR-CSI-018 prereg not emitted")
def test_the_claim_wording_follows_GATING_not_whether_heads_share_a_layer(tmp_path):
    """R30-B F1, a BLOCKER. `THE_CLAIM_MUST_BE_STATED_WITH` was gated on "do two ADMITTED heads
    share a predicted layer" -- PR-CSI-016's criterion -- rather than on the prereg's declared
    PRIMARY.GATING. S-323 moved the GATE onto the prereg and left the WORDING one field behind.

    Drop heads 20 (L11) and 27 (L10) at admission and the four survivors predict L11/L8/L10/L6 --
    all distinct -- so the old guard went False and the field read "the binomial p alone", inside a
    JSON whose own MUST_NOT_BE_SAID_IF_POSITIVE[0] forbids exactly that. R30-B produced a PASS
    gated on permutation = 0.041667 whose published instruction named a binomial 273x smaller.

    PROPERTY: under GATING = weakest_of_three the wording names the weakest of three, whatever the
    admitted heads' predicted layers happen to be."""
    pr = json.load(open(PR018))
    sp = pr["DETECTABILITY_PREREGISTERED_PER_HEAD"]["per_head"]
    heads = pr["heads"]                                   # [6, 11, 20, 24, 27, 29]
    peaks = {h: sp[str(h)]["screen_predicted_layer"] for h in heads}
    admit = [h not in (20, 27) for h in heads]
    v = _run018(tmp_path, _census018(tmp_path, peaks, admit=admit)[0])

    assert v["K_admitted"] == 4, v["why"]
    # `shared_predicted_layers` IS the old guard's condition, published. Empty = the branch that
    # used to emit "the binomial p alone".
    assert v["ROBUSTNESS"]["shared_predicted_layers"] == [], (
        "fixture invalid: no two ADMITTED heads may share a predicted layer, or this test does not "
        "exercise the defect: %r" % (v["ROBUSTNESS"]["shared_predicted_layers"],))
    assert v["GATING"] == "weakest_of_three"
    said = v["ROBUSTNESS"]["THE_CLAIM_MUST_BE_STATED_WITH"]
    assert "binomial p alone" not in said, (
        "the reader instructed the write-up to quote the binomial ALONE under weakest_of_three, "
        "contradicting MUST_NOT_BE_SAID_IF_POSITIVE in the same file: %r" % said)
    assert "WEAKEST" in said, said


@pytest.mark.skipif(not os.path.exists(PR018), reason="PR-CSI-018 prereg not emitted")
def test_K_below_3_is_CANNOT_ANSWER_because_the_prereg_defines_FAILURE_only_at_K_ge_3(tmp_path):
    """R30-B F3. The prereg says "FAILURE = the weakest p > 0.05 WITH K >= 3"; the code's only K
    guard was `K < 2`, so K=2 published FAIL -- 60 of R30-B's 729 reachable configurations did.
    At K=2 the permutation space holds 2 assignments, floor 0.5, so weakest > alpha is FORCED
    whatever the data: a structural non-answer exactly like K=1, and NOT a licensed FAILURE.

    Admit only heads 11 and 29 -- the two unique-layer heads -- and let both match perfectly."""
    pr = json.load(open(PR018))
    sp = pr["DETECTABILITY_PREREGISTERED_PER_HEAD"]["per_head"]
    heads = pr["heads"]
    peaks = {h: sp[str(h)]["screen_predicted_layer"] for h in heads}
    admit = [h in (11, 29) for h in heads]
    v = _run018(tmp_path, _census018(tmp_path, peaks, admit=admit)[0])

    assert v["K_admitted"] == 2 and v["M_matches"] == 2, v["why"]
    assert v["VERDICT"] == "CANNOT ANSWER", (
        "a PERFECT 2-of-2 was published as %r, below the K >= 3 the prereg requires for FAILURE: %s"
        % (v["VERDICT"], v["why"]))
    assert "K >= 3" in v["why"], v["why"]
    # and the floor must be reported whether or not it changed the verdict
    assert v["ROBUSTNESS"]["GATING_FLOOR"]["p"] > 0.05


@pytest.mark.skipif(not os.path.exists(PR018), reason="PR-CSI-018 prereg not emitted")
def test_a_TRUNCATED_gate0_record_is_refused_rather_than_self_reporting_its_own_total(tmp_path):
    """R30-B F4. The GATE 0 check iterated the record's OWN keys and used len(per_arm) as its
    denominator, so a truncated record self-reported a truncated total and ABSENCE WAS A PASS --
    the very thing the refusal two lines above it says it is not. R30-B cut per_arm to a single
    arm, left all 61 other E's in place, and the read published VERDICT PASS at K=6 M=6.

    The frozen read's claim is "GATE 0 PASS on all 62 arms"; nothing could substantiate "all 62"
    because n_arms_per_split was never read."""
    pr = json.load(open(PR018))
    sp = pr["DETECTABILITY_PREREGISTERED_PER_HEAD"]["per_head"]
    heads = pr["heads"]
    peaks = {h: sp[str(h)]["screen_predicted_layer"] for h in heads}
    path, _ = _census018(tmp_path, peaks)

    rep = json.load(open(path))
    full = dict(rep["GATE_0_and_identity"]["per_arm"])
    dropped = ["BF_H6_L11", "HD_29"]
    for k in dropped:
        assert k in full, "fixture invalid: %s absent" % k
        del full[k]
    rep["GATE_0_and_identity"]["per_arm"] = full          # every E left intact
    p2 = tmp_path / "truncated.json"
    p2.write_text(json.dumps(rep))

    out = tmp_path / "v.json"
    r = subprocess.run([PY, READER, "--prereg", PR018, "--census", str(p2), "--out", str(out)],
                       capture_output=True, text=True)
    blob = r.stdout + r.stderr
    assert r.returncode != 0, (
        "a census whose GATE 0 record is missing %s was READ:\n%s" % (dropped, blob[-700:]))
    assert "ABSENT" in blob or "n_arms_per_split" in blob, blob[-700:]
    for k in dropped:
        assert k in blob, "the refusal did not name the missing arm %s:\n%s" % (k, blob[-700:])
