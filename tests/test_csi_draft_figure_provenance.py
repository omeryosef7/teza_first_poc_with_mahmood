"""Every figure in the results draft traces to a source, and the allowlist cannot hide one silently.

S-431. The draft's figure check used to ask only "is this number in the claim table". The draft now
cites artefact fields, code comments and derivations, so that question produced FALSE POSITIVES --
the failure mode this sprint hit five times with ad-hoc detectors, each caught only by reading the
values by hand. The check is widened here and gated, and the ALLOWLIST (an author assertion, not a
check) is forced to carry reasons.
"""
import importlib.util
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GATE = os.path.join(ROOT, "scripts", "gates", "dcs_csi_draft_figure_provenance.py")
DRAFT = os.path.join(ROOT, "reports", "DCS_CSI_RESULTS_DRAFT.md")


def _mod():
    spec = importlib.util.spec_from_file_location("_figprov", GATE)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_every_allowlist_entry_carries_a_reason():
    """The allowlist is where an unverified number would hide. Empty reasons are refused."""
    m = _mod()
    assert m.ALLOWLIST, "the allowlist is empty -- if that is real, delete it and this test"
    for fig, why in m.ALLOWLIST.items():
        assert isinstance(why, str) and len(why.strip()) >= 20, (
            "allowlisted figure %r has no usable reason: %r" % (fig, why))
        assert any(t in why for t in ("S-4", "S-3", "computed", "measured", "executing")), (
            "allowlisted figure %r does not say WHERE it came from: %r" % (fig, why))


def test_the_draft_has_no_unaccounted_figures():
    if not os.path.exists(DRAFT):
        import pytest
        pytest.skip("draft absent in this checkout")
    r = subprocess.run([sys.executable, GATE, "--strict"], capture_output=True, text=True, cwd=ROOT)
    assert r.returncode == 0, "unaccounted figures in the draft:\n" + r.stdout[-2000:]
    assert "unaccounted: 0" in r.stdout


def test_the_gate_states_what_it_cannot_do():
    """⚠ A checker that does not publish its blind spots is the R29 shape. These are measured
    limits, not hedges: existence is not correctness, and small integers are invisible (the 70-vs-67
    error of S-417 would pass this gate)."""
    src = open(GATE, encoding="utf-8").read()
    for marker in ("WHAT THIS CANNOT DO", "Existence is not correctness",
                   "small integers", "BY COINCIDENCE"):
        assert marker in src, "the gate no longer states its limit: %r" % marker


def test_it_actually_detects_an_unaccounted_figure(tmp_path):
    """The gate must FAIL on a figure that exists nowhere -- otherwise it is decorative."""
    fake = tmp_path / "draft.md"
    fake.write_text("# x\n\nA result of 0.31415926535897 appears here.\n", encoding="utf-8")
    r = subprocess.run([sys.executable, GATE, "--draft", str(fake), "--strict"],
                       capture_output=True, text=True, cwd=ROOT)
    assert r.returncode == 1, "the gate passed a figure that exists in no source:\n" + r.stdout
    assert "UNACCOUNTED" in r.stdout
