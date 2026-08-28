"""A figure whose artifact attaches a caveat may not be quoted without it.

R-132 checked once, so it could only see the caveats present that day; the next figure added to a
deliverable would not be checked at all. The concurrent session made the same point about their V-85
and built a standing guard, which is the right shape: an artifact caveat of the form "if you quote X,
say Y" is INERT until someone quotes X, and at that moment becomes a live defect with nothing watching.

Each entry is (figure pattern, required phrase, why the caveat governs it). The patterns are
DELIBERATELY NARROW — C-47 found four loose matchers in one day, every one inside a check written to
catch imprecision and every one failing toward success. A loose pattern here would fire constantly and
be switched off; a loose REQUIRED phrase would pass on unrelated prose, which is the C-47 defect
exactly. So the required phrases are distinctive tokens the artifact itself uses.
"""

import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DELIVERABLES = [
    os.path.join(ROOT, "reports", "SPRINT_SUMMARY_2026-08-25_BEHAVIORAL_CAUSALITY.md"),
    os.path.join(ROOT, "RESEARCH_HANDOFF.md"),
]

#: (name, figure regex, required phrase, source artifact field)
CAUTIONED_FIGURES = [
    ("length-conditioned ASR",
     r"length-conditioned|conditioned on length|n_chars\s*>=",
     "POST-TREATMENT",
     "phase1_decomposition / PR4_collider_caveat — the sweep conditions on a COLLIDER"),
    ("rescue percentage",
     r"\bas % of rise\b|\bpct_of_rise\b",
     "INVERTED",
     "rescue_dissociation_table / PCT_CAVEAT — DR-5: inverts when the clean baseline is near zero"),
    ("ticket_knife installation",
     r"ticket_knife.{0,40}\b30/48\b|\b30/48\b.{0,40}ticket_knife",
     "0.331",
     "mapping_installation_verdict / power_caveat — C-32: power 0.331 at n=48, 0.399 at the ceiling"),
]


def _violations(text):
    out = []
    for name, fig, phrase, why in CAUTIONED_FIGURES:
        if re.search(fig, text, re.I) and phrase.lower() not in text.lower():
            out.append((name, phrase, why))
    return out


def test_no_deliverable_quotes_a_cautioned_figure_without_its_caveat():
    for path in DELIVERABLES:
        v = _violations(open(path, encoding="utf-8").read())
        assert not v, (
            f"{os.path.basename(path)} quotes a cautioned figure without its caveat: "
            + "; ".join(f"{n} needs {p!r} ({w})" for n, p, w in v))


def test_the_guard_fires_on_a_violating_document():
    """Their lesson twice over: a guard is worthless until shown to fail, and a guard that passes on
    the live document may be passing because the caveat happens to be discussed elsewhere."""
    bad = "the length-conditioned ASR rises to 0.31 across the sweep"
    v = _violations(bad)
    assert [n for n, _, _ in v] == ["length-conditioned ASR"], v
    assert not _violations(bad + " — note completion length is POST-TREATMENT")


def test_each_required_phrase_is_distinctive_not_generic():
    """C-47: `power` matched 6 unrelated occurrences and produced a false PASS.

    A required phrase must be rare enough that its presence means the caveat was actually stated.
    """
    corpus = "".join(open(p, encoding="utf-8").read() for p in DELIVERABLES).lower()
    for name, _, phrase, _ in CAUTIONED_FIGURES:
        assert corpus.count(phrase.lower()) <= 12, (
            f"required phrase {phrase!r} for {name} appears {corpus.count(phrase.lower())} times — "
            f"too common to evidence that the caveat was stated (the C-47 failure)")
