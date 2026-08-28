"""A correction in the plan that never reaches the claim ledger must fail the guard.

WHY. The gap is invisible from the writing session — the entry demonstrably exists where you just
wrote it — so only a by-count audit across the two artifacts finds it. A peer found two occurrences
that way and flagged it; the same count here found four claim-bearing results sitting in the plan
and absent from the ledger (the batch-split audit, the borrowed-window correction, the per-bank ICC
measurements, and "clustering is not a codeword property").

WHAT THESE TESTS PIN. Not the classification of any particular section — that is a judgement, and
it lives in the module's two tables. They pin that **silence fails**: a correction section that is
neither traced nor classified must make the guard exit non-zero. A guard that cannot fail is worth
nothing, and the first mutation attempt on this module mutated it against an all-passing input and
learned nothing, which is exactly the mistake these tests exist to prevent repeating.
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                "src", "boombness"))
import ledger_propagation_check as lp  # noqa: E402


def test_correction_sections_are_detected_by_marker():
    text = "\n".join([
        "## §1.1 — an ordinary section",
        "## §1.2 — ⛔ CORRECTION to something",
        "### §1.3 — WITHDRAWN: a claim",
        "## §1.4 — CORRECTION in the heading",
        "some ⛔ body text that is not a heading",
    ])
    got = {sid for sid, _ in lp.correction_sections(text)}
    assert got == {"§1.2", "§1.3", "§1.4"}, "markers in body text must not count as headings"


def test_an_ordinary_section_is_not_a_correction():
    assert lp.correction_sections("## §2.1 — results\ntext\n") == []


def _run_guard(tmp_path, monkeypatch, plan_text, ledger_obj):
    import json
    p = tmp_path / "plan.md"
    p.write_text(plan_text, encoding="utf-8")
    lg = tmp_path / "ledger.json"
    lg.write_text(json.dumps(ledger_obj))
    monkeypatch.setattr(lp, "PLAN", str(p))
    monkeypatch.setattr(lp, "LEDGER", str(lg))
    return lp.main()


def test_UNCLASSIFIED_correction_FAILS(tmp_path, monkeypatch):
    """The core property: silence is not allowed."""
    monkeypatch.setattr(lp, "METHOD_ONLY", {})
    monkeypatch.setattr(lp, "TRACE_TOKENS", {})
    rc = _run_guard(tmp_path, monkeypatch, "## §9.99 — ⛔ CORRECTION: unclassified\n", {"entries": []})
    assert rc == 1


def test_a_claim_bearing_section_MISSING_from_the_ledger_FAILS(tmp_path, monkeypatch):
    monkeypatch.setattr(lp, "METHOD_ONLY", {})
    monkeypatch.setattr(lp, "TRACE_TOKENS", {"§9.99": ["per_bank_icc"]})
    rc = _run_guard(tmp_path, monkeypatch, "## §9.99 — ⛔ CORRECTION: claim-bearing\n",
                    {"entries": [{"claim": "unrelated"}]})
    assert rc == 1


def test_a_claim_bearing_section_PRESENT_in_the_ledger_passes(tmp_path, monkeypatch):
    monkeypatch.setattr(lp, "METHOD_ONLY", {})
    monkeypatch.setattr(lp, "TRACE_TOKENS", {"§9.99": ["per_bank_icc"]})
    rc = _run_guard(tmp_path, monkeypatch, "## §9.99 — ⛔ CORRECTION: claim-bearing\n",
                    {"entries": [{"claim": "x", "PER_BANK_ICC": "measured"}]})
    assert rc == 0


def test_METHOD_ONLY_exempts_but_must_carry_a_reason(tmp_path, monkeypatch):
    monkeypatch.setattr(lp, "METHOD_ONLY", {"§9.99": "instrument fix, no claim depends on it"})
    monkeypatch.setattr(lp, "TRACE_TOKENS", {})
    rc = _run_guard(tmp_path, monkeypatch, "## §9.99 — ⛔ CORRECTION: method only\n", {"entries": []})
    assert rc == 0
    assert all(isinstance(v, str) and v.strip() for v in lp.METHOD_ONLY.values())


def test_every_shipped_METHOD_ONLY_entry_states_a_reason():
    """An unexplained exemption is the silence the guard exists to prevent."""
    assert lp.METHOD_ONLY, "the shipped exemption table should not be empty"
    for sid, why in lp.METHOD_ONLY.items():
        assert isinstance(why, str) and len(why.strip()) > 20, f"{sid} has no real reason"


def test_the_real_repo_passes():
    """The shipped plan and ledger must be consistent right now."""
    assert lp.main() == 0
