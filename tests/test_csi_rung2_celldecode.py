"""The RUNG 2 instrument's direction and its refusals, tested without a GPU.

⚠ WHY THE REFUSAL TESTS MATTER MORE THAN THEY LOOK. The token ids are REQUIRED ARGUMENTS with no
defaults for one reason: `scripts/dcs_cont_logitlens_control.py` hardcodes ' button'/' Button'
while the entire CSI cell line is BASKET (S-380). Run unchanged it computes a well-formed,
plausible number for a question nobody asked. That is this sprint's most persistent defect class --
a family-specific literal surviving a widening (R29/S-322, S-308, S-357) -- and a default here
would reintroduce it.
"""
import importlib.util
import json
import os
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PY = sys.executable
SCRIPT = os.path.join(ROOT, "scripts", "dcs_csi_rung2_celldecode.py")


def _mod():
    spec = importlib.util.spec_from_file_location("rung2", SCRIPT)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_direction_is_the_frozen_formula():
    """u = g_final * (mean(concept rows) - mean(codeword rows)), frozen in S-382 BEFORE any
    measurement so a later choice cannot masquerade as the original one."""
    torch = pytest.importorskip("torch")
    m = _mod()
    g = torch.tensor([2.0, 3.0, 4.0])
    rows = {1: torch.tensor([1.0, 0.0, 0.0]), 2: torch.tensor([3.0, 0.0, 0.0]),
            3: torch.tensor([0.0, 1.0, 0.0]), 4: torch.tensor([0.0, 3.0, 0.0])}
    u = m.build_direction(g, rows, (1, 2), (3, 4))
    # mean(concept) = [2,0,0]; mean(codeword) = [0,2,0]; diff = [2,-2,0]; * g = [4,-6,0]
    assert torch.allclose(u, torch.tensor([4.0, -6.0, 0.0])), u


def test_direction_is_LINEAR_which_is_what_makes_the_decomposition_exact():
    """S-380 measured linear |diff| 7.58e-15 vs logsumexp |diff| 6.89e-01. The whole design rests
    on the readout being linear, so the direction must be a fixed vector -- not a function of the
    activation it will be dotted with."""
    torch = pytest.importorskip("torch")
    m = _mod()
    g = torch.rand(64) + 0.5
    rows = {i: torch.randn(64) for i in range(4)}
    u = m.build_direction(g, rows, (0, 1), (2, 3))
    h1, h2 = torch.randn(64), torch.randn(64)
    assert torch.allclose((h1 + h2) @ u, (h1 @ u) + (h2 @ u), atol=1e-5)


def test_mean_of_casings_not_one_casing():
    """S-382 chose the MEAN over lowercase-only because both are linear but the latter adds a free
    choice a reader could not distinguish from tuning. If someone silently switches to the first
    row, this fails."""
    torch = pytest.importorskip("torch")
    m = _mod()
    g = torch.ones(3)
    rows = {1: torch.tensor([1.0, 0.0, 0.0]), 2: torch.tensor([5.0, 0.0, 0.0]),
            3: torch.zeros(3), 4: torch.zeros(3)}
    u = m.build_direction(g, rows, (1, 2), (3, 4))
    assert float(u[0]) == 3.0, "not the mean of the two concept rows: %r" % u


def _run(extra):
    base = [PY, SCRIPT, "--bank", "/nonexistent", "--split", "train",
            "--exclude-prompt-ids", "/nonexistent", "--model", "/m",
            "--snapshot-glob", "/s/*", "--heads", "4,6", "--out", "/tmp/x.json"]
    return subprocess.run(base + extra, capture_output=True, text=True)


def test_token_ids_have_NO_DEFAULTS():
    """A default is how ' button' ends up in a basket family (S-380)."""
    r = _run([])
    both = r.stdout + r.stderr
    assert r.returncode != 0
    assert "--concept-ids" in both and "required" in both.lower(), both


def test_overlapping_concept_and_codeword_ids_are_refused():
    r = _run(["--concept-ids", "13054,33909", "--codeword-ids", "33909,14351"])
    both = r.stdout + r.stderr
    assert r.returncode != 0
    assert "overlap" in both and "degenerate" in both, both


def test_empty_id_list_is_refused_not_defaulted():
    r = _run(["--concept-ids", "", "--codeword-ids", "14351"])
    both = r.stdout + r.stderr
    assert r.returncode != 0
    assert "is empty" in both, both


def test_TEST_split_is_not_even_a_choice():
    """PART I: TEST is never touched. It is not an option the operator can pass."""
    r = subprocess.run([PY, SCRIPT, "--help"], capture_output=True, text=True)
    assert "--split" in r.stdout
    seg = r.stdout.split("--split")[1][:200]
    assert "test" not in seg.split("}")[0], "TEST appears in the --split choices: %r" % seg


def test_the_exclusion_file_is_REQUIRED():
    """S-381 measured that this FILE, not the prereg, is what actually keeps TEST out -- the
    prereg's own leak check is vacuous (S-375). So it cannot be optional."""
    r = subprocess.run([PY, SCRIPT, "--help"], capture_output=True, text=True)
    assert "--exclude-prompt-ids" in r.stdout
    src = open(SCRIPT, encoding="utf-8").read()
    assert '"--exclude-prompt-ids", required=True' in src


def test_the_script_refuses_to_emit_a_verdict():
    """It is an INSTRUMENT. A preregistered reader decides what a measurement means."""
    src = open(SCRIPT, encoding="utf-8").read()
    assert "EXPLORATORY" in src
    # ⚠ NOT a grep for the WORD -- the docstring says "COMPUTES NO VERDICT", which a naive search
    # flags as a violation of itself. Look for verdict-EMITTING code instead: a JSON key, or a
    # comparison against a significance threshold.
    for forbidden in ('"VERDICT"', '"p_one_sided"', '"PASS"', '"FAIL"', "<= alpha", "> alpha"):
        assert forbidden not in src, "the instrument emits/decides %r; it must not" % forbidden


def test_it_records_that_this_is_NOT_the_endpoint():
    """y_install aggregates casings with logsumexp; this direction is linear. The artefact must
    carry that, because the distinction is invisible in the numbers (S-381/S-382)."""
    src = open(SCRIPT, encoding="utf-8").read()
    assert "NOT_THE_ENDPOINT" in src
    assert "does NOT decompose y_install" in src or "decomposes y_install" in src
