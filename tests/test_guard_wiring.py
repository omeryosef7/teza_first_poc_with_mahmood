"""Every guard's VERDICT must respond to a defect — not merely its scanner.

⛔ WHY THIS FILE EXISTS. `run_completeness_check`'s check 3 was mutation-tested with six mutants and
five died. The survivor deleted `problems += fa_problems` from `main()`: the check still ran, still
printed its findings, and **the exit code ignored them**. All 20 of that guard's tests passed,
because every one called the scan function directly and none asserted the verdict consumes it.

    TESTING THE CHECK IS NOT TESTING THE GUARD.

"Mutation-test every new guard" was already the standing rule and did not catch it — the mutant was
in the wire between scanner and exit code, and the unit tests lived on one side of that wire. A peer
ran the same probe against their three guards and found the same coverage hole (their wires were
intact; they had no evidence they were).

⛔ AND PROBING FOUND A LIVE ONE. `canonical_figures` printed a normal-looking line and returned 0
when a figure's artifact key path did not resolve: `_artifact_value` returns None for a missing
file, a renamed key and a non-numeric value alike, and check (b) was gated `if av is not None`. That
is audit #11's defect — "check (b) is gated on `allvals`" — surviving on the *other* gate. Closed,
and pinned here.

TWO PROPERTIES PER GUARD, and the second is not optional: a defect must make the verdict non-zero,
AND the clean control must pass. A wire test whose "clean" input is not clean asserts nothing — the
peer hit exactly that, drawing supposedly-clean ids from a table that classified them while the
guard still scored them as failures. Where a synthetic clean fixture cannot satisfy a guard (regex
registries matched against the real deliverables), the REAL corpus is the control.
"""
from __future__ import annotations

import contextlib
import importlib
import io
import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src", "boombness"))
sys.path.insert(0, os.path.join(ROOT, "scripts"))


#: Every guard module this file deforms. `_verdict` mutates module-level tables (FIGURES, CHECKS,
#: PLAN, METHOD_ONLY, MIN_EXPECTED) on the LIVE module object, so without restoration those
#: deformations leak into any later test that imports the same module.
_TOUCHED = ("canonical_figures", "verify_report_numbers", "ledger_propagation_check",
            "markdown_structure_check", "pvalue_hygiene_check", "retraction_sweep",
            "plan_coverage_check")


@pytest.fixture(autouse=True)
def _restore_guard_modules():
    """⛔ THIS FILE POISONED test_ledger_propagation_check.py, AND THE HOOK COULD NOT SEE IT.

    `_verdict` reloads a guard and then bends its module-level tables. The bends survived the test,
    so `ledger_propagation_check` was left with `PLAN`/`LEDGER` pointing at a tmp fixture and
    `METHOD_ONLY` holding 29 injected entries. Four tests in that file then failed -- but ONLY in
    alphabetical order, which is the full suite's order and NOT the commit hook's: the hook lists
    `test_ledger_propagation_check.py` BEFORE this file, so it ran clean while
    `pytest tests/` reported 4 failures.

    A green hook was therefore not evidence the suite was green, and the difference was file
    ORDER -- the same order-dependence that re-attributed a plan section in DR-12, in the test
    layer instead of the document layer. Restoring after every test is the fix; asserting the
    reload inside individual tests is not, because it only protects the test that remembers to.
    """
    yield
    for name in _TOUCHED:
        if name in sys.modules:
            importlib.reload(sys.modules[name])


def _verdict(module, patch=None, argv=None):
    """Reload the guard, optionally deform it, and return (exit_code, stdout)."""
    m = importlib.reload(importlib.import_module(module))
    if patch:
        patch(m)
    old = sys.argv
    sys.argv = [module] + (argv or [])
    try:
        with contextlib.redirect_stdout(io.StringIO()) as buf:
            try:
                rc = m.main()
            except SystemExit as e:
                rc = e.code
    finally:
        sys.argv = old
    return rc, buf.getvalue()


# ------------------------------------------------------------------ canonical_figures

def test_canonical_figures_clean_control_passes():
    assert _verdict("canonical_figures")[0] == 0


def test_canonical_figures_REFUSES_an_unresolvable_artifact_key():
    """⛔ THE LIVE DEFECT THIS FILE FOUND. Before the fix this printed the figure on a healthy-looking
    line and returned 0, so a renamed JSON field disabled the drift check invisibly."""
    def bend(m):
        k = "advbench_band_mean"
        rx, apat, apath, tol = m.FIGURES[k]
        m.FIGURES[k] = (rx, apat, apath + ["no_such_subkey"], tol)
    rc, out = _verdict("canonical_figures", bend)
    assert rc == 1, "an unresolvable key path must FAIL, not silently disable check (b)"
    assert "did not RESOLVE" in out and "advbench_band_mean" in out, (
        "the guard must NAME the disabled figure -- a non-zero exit with no reason is unactionable")


def test_canonical_figures_REFUSES_a_missing_artifact_file():
    def gone(m):
        k = "advbench_band_mean"
        rx, apat, apath, tol = m.FIGURES[k]
        m.FIGURES[k] = (rx, "outputs/boombness/nope_*.json", apath, tol)
    assert _verdict("canonical_figures", gone)[0] == 1


def test_every_artifact_declaring_figure_actually_resolves_today():
    """Anti-vacuity: the check above is only meaningful while the registry genuinely resolves.

    RELOADED deliberately: the tests above bend `FIGURES` in place, and reading the cached module
    here made this fail on a mutation another test had left behind. A test that inherits a previous
    test's deformation is testing that deformation.
    """
    m = importlib.reload(importlib.import_module("canonical_figures"))
    declared = [(k, v) for k, v in m.FIGURES.items() if v[1]]
    assert len(declared) >= 8
    unresolved = [k for k, (rx, a, p, t) in declared if m._artifact_value(a, p) is None]
    assert unresolved == [], f"these figures no longer resolve: {unresolved}"


# ------------------------------------------------------------------ verify_report_numbers

def test_verify_report_numbers_clean_control_passes():
    assert _verdict("verify_report_numbers")[0] == 0


def test_verify_report_numbers_verdict_responds_to_a_mismatched_pin():
    def perturb(m):
        c = list(m.CHECKS[0])
        c[3] = c[3] + 10.0
        m.CHECKS = [tuple(c)] + list(m.CHECKS[1:])
    rc, out = _verdict("verify_report_numbers", perturb)
    assert rc == 1 and "G1 demos_only" in out


# ------------------------------------------------------------------ ledger_propagation_check

def _plan_with_unclassified_corrections(tmp_path, n=30):
    plan = tmp_path / "plan.md"
    plan.write_text("\n".join(f"### §{i}.1 ⛔ CORRECTION: injected\n\ntext\n" for i in range(1, n)))
    ledger = tmp_path / "led.json"
    ledger.write_text(json.dumps({"entries": []}))
    return str(plan), str(ledger)


def test_ledger_propagation_verdict_responds_to_an_unclassified_correction(tmp_path):
    plan, ledger = _plan_with_unclassified_corrections(tmp_path)

    def bend(m):
        m.PLAN, m.LEDGER, m.MIN_EXPECTED = plan, ledger, 5
    rc, out = _verdict("ledger_propagation_check", bend)
    assert rc == 1 and "UNCLASSIFIED" in out


def test_ledger_propagation_clean_control_passes(tmp_path):
    """The SAME corpus, every section classified — isolating the verdict from the fixture."""
    plan, ledger = _plan_with_unclassified_corrections(tmp_path)

    def bend(m):
        m.PLAN, m.LEDGER, m.MIN_EXPECTED = plan, ledger, 5
        m.METHOD_ONLY = {f"§{i}.1": "injected control" for i in range(1, 30)}
    assert _verdict("ledger_propagation_check", bend)[0] == 0


# ------------------------------------------------------------------ path-argument guards

@pytest.mark.parametrize("guard,flag,bad,good", [
    ("markdown_structure_check", "--paths",
     "# t\n\n| a | b |\n| --- |\n| 1 | 2 |\n", "# t\n\n| a | b |\n| --- | --- |\n| 1 | 2 |\n"),
    ("pvalue_hygiene_check", "--paths",
     "# t\n\nThe effect was significant (p = 0.0301).\n", "# t\n\nno statistics here\n"),
    ("retraction_sweep", "--paths",
     "# t\n\nThe naive arm manufactures signal in every cell.\n",
     "# t\n\n⛔ RETRACTED: the claim that it manufactures signal is withdrawn.\n"),
])
def test_path_guards_fail_on_a_defect_and_pass_on_its_control(tmp_path, guard, flag, bad, good):
    b = tmp_path / "bad.md"
    b.write_text(bad)
    g = tmp_path / "good.md"
    g.write_text(good)
    assert _verdict(guard, argv=[flag, str(b)])[0] == 1, f"{guard} did not act on its own finding"
    assert _verdict(guard, argv=[flag, str(g)])[0] == 0, f"{guard}'s clean control does not pass"


def test_plan_coverage_verdict_responds_to_a_dropped_section(tmp_path):
    plan = tmp_path / "plan.md"
    plan.write_text("## 3. A research section\n\ntext\n")
    rep = tmp_path / "rep.md"
    rep.write_text("# report\n\nnothing\n")
    assert _verdict("plan_coverage_check",
                    argv=["--plan", str(plan), "--report", str(rep)])[0] == 1
