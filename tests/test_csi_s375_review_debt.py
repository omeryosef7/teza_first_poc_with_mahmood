"""S-375: the four R34 concerns that S-369/S-370 recorded and deferred.

Each test FAILS without its fix. Two of them guard against a failure that costs a GPU run: a
reader that dies with a bare KeyError, and a read that silently uses a resampler the prereg did
not freeze.

⚠ The fifth thing R34 asked for is NOT here, deliberately. Pinning the reference `ci95` at
`void_tolerance` was written, tested against the PUBLISHED PR-CSI-020 read, and REVERTED: it
refused all eight heads of a family that had already passed, because `E` is deterministic
(|diff| = 0.00e+00) while `ci95` is a BOOTSTRAP quantity that differs by 2.06e-05 .. 1.60e-04
between families resampled with different seeds. `test_void8_ci95_is_recorded_but_does_not_gate`
locks that decision in so nobody re-adds the refusal.
"""
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PY = sys.executable
CENSUS = os.path.join(ROOT, "scripts", "dcs_csi_head_census.py")
READER = os.path.join(ROOT, "scripts", "dcs_csi_pr016_argmax_test.py")
PR020 = os.path.join(ROOT, "configs", "dcs_csi_pr020_cell_census_basket_8heads.json")


def _run(argv):
    return subprocess.run(argv, capture_output=True, text=True)


def _census_argv(prereg, out, B=10000, seed=20260922, ci=0.95):
    return [PY, CENSUS, "--prereg", prereg, "--tag-prefix", "csi11_cell8_basket_validation",
            "--split", "validation", "--expect-n", "230", "--B", str(B), "--seed", str(seed),
            "--ci", str(ci), "--allow-short", "0", "--out", out]


# ---------------------------------------------------------------- (b) the frozen resampler
def test_census_refuses_a_bootstrap_the_prereg_did_not_freeze(tmp_path):
    """ESTIMATOR_AND_RESAMPLER was written by the freeze script and read by NOTHING (R34-B/R34-C).

    `ci` feeds ci95_excludes_0, hence ADMISSION, hence K. The near-miss is one keystroke: the
    sibling reader dcs_csi_head_analyze.py defaults to seed 20260921."""
    out = str(tmp_path / "o.json")
    for kw, bad in (("seed", 20260921), ("B", 2000), ("ci", 0.9)):
        r = _run(_census_argv(PR020, out, **{kw: bad}))
        assert r.returncode != 0, "a %s of %r was accepted" % (kw, bad)
        assert "freezes bootstrap %s=" % kw in (r.stdout + r.stderr), (kw, r.stdout, r.stderr)


def test_census_accepts_the_frozen_bootstrap(tmp_path):
    """The guard must not fire on the values the frozen read actually passes."""
    r = _run(_census_argv(PR020, str(tmp_path / "o.json")))
    assert "freezes bootstrap" not in (r.stdout + r.stderr), r.stdout + r.stderr


def test_census_bootstrap_guard_is_silent_when_the_prereg_declares_none(tmp_path):
    """Backward compatibility: a prereg without ESTIMATOR_AND_RESAMPLER must read exactly as before."""
    pr = json.load(open(PR020))
    pr.pop("ESTIMATOR_AND_RESAMPLER", None)
    p = tmp_path / "pr.json"
    p.write_text(json.dumps(pr))
    r = _run(_census_argv(str(p), str(tmp_path / "o.json"), seed=12345))
    assert "freezes bootstrap" not in (r.stdout + r.stderr), r.stdout + r.stderr


# ---------------------------------------------------------------- (d) the unguarded alias
def test_reader_names_a_head_missing_from_per_head_instead_of_KeyError(tmp_path):
    """R34-D: `per_head[h]` was the one unguarded alias subscript in the read path, while the
    identical guard sat four lines below. A head in `heads` but absent from `per_head` was a bare
    KeyError in STEP 2 -- after the GPU. R33 used exactly this mutation and the prereg self-test
    still cannot see it, because `per_head` is a LOCAL ALIAS the static scan does not follow."""
    pr = json.load(open(PR020))
    victim = str(pr["heads"][0])   # first, so the guard fires before the absent-arm refusal
    del pr["DETECTABILITY_PREREGISTERED_PER_HEAD"]["per_head"][victim]
    p = tmp_path / "pr.json"
    p.write_text(json.dumps(pr))
    # a census report is not needed: the refusal must come before any endpoint is read, but the
    # reader opens the census first, so give it one that exists and is well-formed enough.
    rep = {"prereg_id": pr["id"], "ON_PROTOCOL": True, "split": pr["split"],
           "GATE_0_and_identity": {"per_arm": {a: {"pass": True} for a in
                                               list(pr["base_arms"]) + list(pr["cell_sets"])}},
           "E": {}, "ci95": {},
           "CELL_FAMILY": {"bars_COMPUTED_FROM_A_FROZEN_RULE": {}}}
    c = tmp_path / "c.json"
    c.write_text(json.dumps(rep))
    r = _run([PY, READER, "--prereg", str(p), "--census", str(c), "--out", str(tmp_path / "o.json")])
    both = r.stdout + r.stderr
    assert "Traceback" not in both, "died with a traceback instead of a named refusal:\n" + both
    assert "KeyError" not in both, both
    assert "declares no DETECTABILITY_PREREGISTERED_PER_HEAD.per_head entry" in both, both
    assert "head %s" % victim in both, both


# ---------------------------------------------------------------- (c) the vacuous TEST check
def test_vacuous_test_leak_check_is_disclosed_not_silently_passed():
    """R34-B: no prereg this sprint has frozen declares population.test_domain_ids, so the leak
    check could never fire -- the file's own R20-6 rule violated at a site it never revisited.
    It is NOT promoted to a refusal (that would make every published family unreadable); the
    NON-CHECK is disclosed. The old message also cited 'VOID 5', which is the screen md5."""
    src = open(CENSUS, encoding="utf-8").read()
    assert "TEST-LEAK CHECK NOT RUN" in src
    assert "This is a NON-CHECK, not a pass" in src
    assert 'sys.exit("REFUSING: TEST domain(s) present: %s (VOID 5)" % leaked)' not in src
    assert json.load(open(PR020))["population"].get("test_domain_ids") is None, (
        "PR-CSI-020 now declares test_domain_ids -- this test's premise has changed")


# ---------------------------------------------------------------- (a) the REVERTED refusal
def test_void8_ci95_is_recorded_but_does_not_gate():
    """S-375 wrote a ci95 refusal, measured it against the PUBLISHED PR-CSI-020 read, and reverted
    it. E reproduces at |diff| = 0.00e+00 because it is deterministic; ci95 differs by
    2.06e-05 .. 1.60e-04 because it is a BOOTSTRAP quantity and the two families used different
    seeds. void_tolerance is 1e-6, calibrated for determinism -- applying it to a resampled
    statistic refused all 8 heads of a family that had already passed."""
    src = open(CENSUS, encoding="utf-8").read()
    assert '"ci95_abs_diff": _ci_d' in src, "the disclosure was removed"
    assert "VOID CONDITION 8 -- head %s's arm %r reproduces the frozen mean" not in src, (
        "the ci95 refusal was re-added; it refuses PUBLISHED reads -- see S-375")


def test_published_pr020_verdict_still_reproduces():
    """The strongest regression available: the four fixes must not move a published result."""
    v = os.path.join(ROOT, "reports",
                     "DCS_CSI_PR020_ARGMAX_TEST_basket_8heads_validation.json")
    if not os.path.exists(v):
        return
    d = json.load(open(v))
    assert d["VERDICT"] == "PASS"
    assert (d["K_admitted"], d["M_matches"]) == (8, 6)
    assert d["gating_p_name"] == "conditional"
    assert abs(d["gating_p"] - 0.005029721079103794) < 1e-15
