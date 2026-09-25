"""PR-CSI-021's reader: it computes no statistic of its own, and it refuses anything but the
declared measurement."""
import importlib.util
import json
import os
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PY = sys.executable
READER = os.path.join(ROOT, "scripts", "dcs_csi_pr021_rung2_read.py")
SHARED = os.path.join(ROOT, "scripts", "dcs_csi_argmax_verdict.py")
PREREG = os.path.join(ROOT, "configs", "dcs_csi_pr021_rung2_decode_basket_validation.json")
TRAIN = os.path.join(ROOT, "reports", "DCS_CSI_RUNG2_TRAIN_basket_full.json")


def _code(path):
    out = []
    for line in open(path, encoding="utf-8").read().splitlines():
        out.append("" if line.lstrip().startswith("#") else line.split("#")[0])
    return "\n".join(out)


def test_the_reader_computes_NO_statistic_of_its_own():
    """S-389/S-350: rung 2 must apply the SAME statistic to a DIFFERENT quantity."""
    c = _code(READER)
    assert "_verdict.decide(" in c, "the reader does not call the shared verdict"
    for forbidden in ("def binom_tail", "def decide", "itertools.permutations", "logsumexp"):
        assert forbidden not in c, "the reader reimplements %r; it must not (S-350)" % forbidden


def test_the_normalisation_is_the_SHARED_one():
    """🔴 S-403. The freeze computed q from the RAW argmax -- the statistic S-399 refuted -- while
    the reader used the layer-normalised one, so the emitted prereg carried a power table
    describing a different experiment (q = 0/8 against the reader's 3/8). Both must call the same
    function, which is why it lives beside decide()."""
    assert "def normalised_layer_profile" in open(SHARED, encoding="utf-8").read(), \
        "the normalisation is not in the shared module"
    # ⚠⚠ R36-A/R36-B/S-406: THIS TEST CHECKED ONLY THE FREEZE. Its own docstring said "Both must
    # call the same function", and it verified one of them -- so the reader inlined its own copy
    # for three ticks while the FROZEN PREREG asserted "Implemented ONCE ... called by BOTH".
    # Two independent reviewers found it; this test did not. Both callers are checked now.
    fc = _code(os.path.join(ROOT, "scripts", "gates", "dcs_csi_pr021_freeze.py"))
    assert "normalised_layer_profile" in fc, "the FREEZE no longer uses the shared normalisation"
    rc = _code(READER)
    assert "normalised_layer_profile" in rc, (
        "the READER does not call the shared normalisation -- it has an inlined copy again, and "
        "the prereg asserts in writing that it does not (S-406)")
    assert "statistics.fmean(others)" not in rc, (
        "the reader has re-inlined the leave-one-out baseline")


def test_leave_one_out_excludes_the_head_from_its_own_baseline():
    spec = importlib.util.spec_from_file_location("shared", SHARED)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    heads, band = [1, 2, 3], [6]
    vals = {(6, 1): 9.0, (6, 2): 1.0, (6, 3): 1.0}
    prof = m.normalised_layer_profile(lambda L, h: vals[(L, h)], heads, band, 1)
    assert abs(prof[6] - 9.0) < 1e-12, (
        "head 1 was included in its own baseline: got %r, expected 9.0/mean(1,1)=9.0" % prof[6])


def test_a_zero_baseline_raises_rather_than_producing_infinity():
    spec = importlib.util.spec_from_file_location("shared", SHARED)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    with pytest.raises(ValueError):
        m.normalised_layer_profile(lambda L, h: 0.0, [1, 2], [6], 1)


@pytest.mark.skipif(not (os.path.exists(PREREG) and os.path.exists(TRAIN)),
                    reason="prereg or train artefact absent")
def test_it_refuses_a_measurement_from_the_WRONG_SPLIT():
    """The prereg freezes validation. A train artefact is the discovery split and must not be
    read as a verdict, however convenient."""
    r = subprocess.run([PY, READER, "--prereg", PREREG, "--measurement", TRAIN,
                        "--out", "/tmp/x.json"], capture_output=True, text=True)
    both = r.stdout + r.stderr
    assert "REFUSING" in both and "split" in both, both[:300]


@pytest.mark.skipif(not os.path.exists(PREREG), reason="prereg absent")
def test_it_refuses_a_SMOKE_measurement_and_says_why(tmp_path):
    art = {"schema": "DCS_CSI_RUNG2/1", "⚠ IS_SMOKE": True, "limit_applied": 3,
           "split": "validation"}
    p = tmp_path / "smoke.json"
    p.write_text(json.dumps(art))
    r = subprocess.run([PY, READER, "--prereg", PREREG, "--measurement", str(p),
                        "--out", str(tmp_path / "o.json")], capture_output=True, text=True)
    both = r.stdout + r.stderr
    assert "REFUSING" in both and "SMOKE" in both, both[:300]
    assert "domain is the" in both, "the refusal does not say why a smoke cannot carry a verdict"


@pytest.mark.skipif(not os.path.exists(PREREG), reason="prereg absent")
def test_VOID_13_the_reconstruction_error_must_be_PRESENT_and_within_tolerance(tmp_path):
    """The recon check is the only thing standing between this and a wrong GQA head map. Its
    ABSENCE is not a pass."""
    pr = json.load(open(PREREG))
    base = {"schema": "DCS_CSI_RUNG2/1", "⚠ IS_SMOKE": False, "split": "validation",
            "selection_n_rows": pr["population"]["validation_expect_n"],
            "selection_n_domains": pr["population"]["validation_domains"],
            "n_prompts_used": pr["population"]["validation_expect_n"], "dtype": "bfloat16"}
    for art, want in ((dict(base), "no recon_rel_err"),
                      (dict(base, recon_rel_err_first_row={"L6": 0.9}), "exceeds")):
        p = tmp_path / "a.json"
        p.write_text(json.dumps(art))
        r = subprocess.run([PY, READER, "--prereg", PREREG, "--measurement", str(p),
                            "--out", str(tmp_path / "o.json")], capture_output=True, text=True)
        both = r.stdout + r.stderr
        assert "REFUSING" in both, (want, both[:300])
        assert "VOID 13" in both, "the refusal does not cite the VOID condition it enforces"


@pytest.mark.skipif(not os.path.exists(PREREG), reason="prereg absent")
def test_the_prereg_satisfies_every_key_the_reader_HARD_SUBSCRIPTS():
    """The failure this catches is a KeyError AFTER the GPU -- twice in this sprint's history."""
    r = subprocess.run([PY, os.path.join(ROOT, "scripts", "gates", "dcs_csi_prereg_selftest.py"),
                        "--prereg", PREREG, "--reader", READER], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "0 MISSING" in r.stdout, r.stdout


@pytest.mark.skipif(not os.path.exists(PREREG), reason="prereg absent")
def test_the_prereg_CARRIES_every_disclosure_S401_requires():
    """🔴 S-404. Six of eight were MISSING from the first emission, because the freeze script
    predates S-400/S-401. This checks the EMITTED FILE, not the source that writes it -- a source
    grep would pass on a script that writes a key it never populates."""
    pr = json.load(open(PREREG))
    blob = json.dumps(pr, ensure_ascii=False)
    pw = pr["POWER_BY_SEEDED_MONTE_CARLO"]
    assert pw.get("⚠ THE_STATISTIC_WAS_CHOSEN_AFTER_SEEING_TRAIN"), "no after-train disclosure"
    d = pw["⚠ THE_STATISTIC_WAS_CHOSEN_AFTER_SEEING_TRAIN"]
    assert "THREE candidate" in d, "the candidate set is not named"
    assert "DECLINED" in d, "it does not say the better-scoring statistic was declined"
    assert "FIDELITY" in d, "it does not state the criterion the choice was made on"
    lo, hi = pw["q_exact_95CI"]
    assert abs(lo - 0.085) < 0.01 and abs(hi - 0.755) < 0.01, (lo, hi)
    assert "S-374" in blob, "it does not record that K=8 is the whole admissible population"
    assert "LEAVE-ONE-OUT" in blob.upper(), "the normalisation is not frozen into the prereg"
    assert "DIRECT-PATH" in blob.upper(), "the direct-path fence is gone"


@pytest.mark.skipif(not os.path.exists(PREREG), reason="prereg absent")
def test_the_reader_REFUSES_a_prereg_that_fails_to_disclose(tmp_path):
    """A `.get()` that returns None publishes a disclosure field carrying nothing."""
    pr = json.load(open(PREREG))
    del pr["POWER_BY_SEEDED_MONTE_CARLO"]["⚠ THE_STATISTIC_WAS_CHOSEN_AFTER_SEEING_TRAIN"]
    p = tmp_path / "pr.json"
    p.write_text(json.dumps(pr, ensure_ascii=False))
    r = subprocess.run([PY, READER, "--prereg", str(p), "--measurement", TRAIN,
                        "--out", str(tmp_path / "o.json")], capture_output=True, text=True)
    both = r.stdout + r.stderr
    assert r.returncode != 0 and "S-404" in both, both[:300]
    assert "cannot be published as null" in both, both[:300]


def test_a_NON_FINITE_cell_is_REFUSED_not_normalised():
    """🔴 R36-B/S-406. `inf > 0` is True, so the zero-baseline guard admitted it, and the
    arithmetic is DIRECTIONAL: inf/finite = inf FORCES that head's argmax to the layer, while
    finite/inf = 0.0 REMOVES the layer for every other head. R36-B set three cells to Infinity and
    turned a FAIL (M=3) into 'PASS -- permutation = 0.000694', with a clean VOID-13 recon. JSON
    round-trips bare Infinity and NaN silently."""
    c = _code(READER)
    assert 'f != f or f == float("inf")' in c, "the finiteness guard is gone"
    assert "manufactures matches" in c, "the refusal no longer says why it matters"


def test_the_BINOMIAL_is_not_given_top_billing_under_a_neutral_name():
    """🔴 R36-B/S-406. The output published `p_one_sided: <the binomial>` at top level beside
    `alpha`, with the gating co-primaries demoted to ROBUSTNESS -- and the prereg's
    MUST_NOT_BE_SAID_IF_POSITIVE forbids quoting the binomial alone. On the real numbers the
    binomial is 0.049998, BELOW alpha, in a file whose verdict is FAIL."""
    c = _code(READER)
    assert '"p_one_sided"' not in c, "the neutral name is back"
    assert '"p_binomial_NOT_THE_CLAIM"' in c, "the binomial is not named as what it is"
    assert "_always" in c and "binomial" in c, (
        "the binomial prohibition does not travel on the FAIL branch, which is exactly where the "
        "binomial is the misleadingly small number")
