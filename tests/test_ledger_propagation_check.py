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
    monkeypatch.setattr(lp, "MIN_EXPECTED", 0)   # unit fixtures carry one section, not a corpus
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


def test_an_EMPTY_scan_is_refused_rather_than_reported_as_clean(tmp_path, monkeypatch):
    """The degenerate pass a peer guarded and I had not.

    If the marker convention changes or the scan breaks, every loop below is skipped and the guard
    reports success having checked NOTHING. The tell was already in the summary line, which printed
    "-5 with a required ledger trace" on an empty scan.
    """
    import json
    p = tmp_path / "plan.md"; p.write_text("## S1 - a plan with no correction markers\n")
    lg = tmp_path / "l.json"; lg.write_text(json.dumps({"entries": []}))
    monkeypatch.setattr(lp, "PLAN", str(p)); monkeypatch.setattr(lp, "LEDGER", str(lg))
    monkeypatch.setattr(lp, "MIN_EXPECTED", 10)
    assert lp.main() == 1, "a guard that checked nothing must not report success"


def test_the_shipped_floor_is_not_zero():
    assert lp.MIN_EXPECTED >= 10, "a floor of 0 restores the degenerate pass"


def test_a_correction_heading_with_NO_id_is_attributed_not_dropped():
    """The first version searched a heading for a section id and, finding none, silently skipped it.

    13 of 31 correction headings in the real plan have no id of their own -- they are sub-headings
    inside a numbered section. So the guard examined 18 of 31 and reported success, and nothing in
    its output distinguished "all corrections are classified" from "the scanner cannot see this
    shape". A peer hit the identical class in their own propagation guard.
    """
    text = "\n".join([
        "## §3.1 — an ordinary section",
        "### ⛔ CORRECTION: a sub-heading carrying no id of its own",
        "## §3.2 — another section",
        "### ⛔ WITHDRAWN: another id-less sub-heading",
    ])
    got = lp.correction_sections(text)
    assert [sid for sid, _ in got] == ["§3.1", "§3.2"], \
        "id-less correction headings must inherit their ENCLOSING section, never be dropped"


def test_a_reference_in_the_heading_does_not_steal_attribution():
    """`### ⛔ CORRECTION to §1.1` inside §9.9 is a correction TO §1.1 that lives IN §9.9."""
    text = "\n".join([
        "## §9.9 — the containing section",
        "### ⛔ CORRECTION to §1.1's framing",
    ])
    got = lp.correction_sections(text)
    # only the CORRECTION heading is collected; the plain containing heading is not a correction
    assert [sid for sid, _ in got] == ["§9.9"], "attribution must be the container, not the referent"
    assert "§1.1" not in [sid for sid, _ in got]


def test_a_correction_before_any_numbered_section_is_not_silently_dropped():
    got = lp.correction_sections("### ⛔ CORRECTION with no enclosing section at all\n")
    assert got and got[0][0] is None, "an unattributable correction must surface, not vanish"


def _ledger_fields():
    import json
    led = json.load(open(lp.LEDGER, encoding="utf-8"))

    def walk(o):
        if isinstance(o, dict):
            for v in o.values():
                yield from walk(v)
        elif isinstance(o, list):
            for v in o:
                yield from walk(v)
        else:
            yield str(o)
    return list(walk(led))


def test_every_TRACE_TOKEN_is_DISTINCTIVE_in_the_ledger():
    """⛔ THE GUARD'S UNCHECKED PREMISE: that a token match is EVIDENCE the correction arrived.

    A section passes if ANY of its tokens appears anywhere in the ledger. That is only meaningful
    if the token is rare there. Ten of 86 entries were not: 'cap' matched 74 ledger fields,
    'dose' 54, 'cell' 46, 'gate' and 'ticket_bomb' 43 each, a bare 'knife' 41. Those sections would
    have passed whether or not their correction ever reached the ledger — the same vacuity as a
    common caveat phrase, one guard over.

    Found by deliberately re-deriving each premise after a peer discovered the identical failure in
    their own guard's third premise. Nothing was testing it.
    """
    fields = _ledger_fields()
    loose = {}
    for sid, toks in lp.TRACE_TOKENS.items():
        counts = {t: sum(1 for v in fields if t.lower() in v.lower()) for t in toks}
        bad = {t: c for t, c in counts.items() if c >= 25}
        if bad:
            loose[sid] = bad
    assert not loose, (
        f"{len(loose)} section(s) rely on a token matching >=25 ledger fields, so a match is not "
        f"evidence the correction arrived: {loose}")


def test_every_TRACE_TOKEN_actually_APPEARS_in_the_ledger():
    """The complement: tightening a token must not make it unfindable.

    A token present 0 times would fail the guard for every section that needs it -- the opposite
    failure, and equally silent until a correction is added.
    """
    fields = _ledger_fields()
    absent = {sid: [t for t in toks if not any(t.lower() in v.lower() for v in fields)]
              for sid, toks in lp.TRACE_TOKENS.items()}
    absent = {k: v for k, v in absent.items() if len(v) == len(lp.TRACE_TOKENS[k])}
    assert not absent, f"section(s) whose every token is absent from the ledger: {absent}"
