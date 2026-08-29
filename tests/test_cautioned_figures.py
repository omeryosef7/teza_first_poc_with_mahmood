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
     "inverted relative to the evidence",   # C-86: was "INVERTED", which my own writing
                                            # inflated to 12 occurrences — a required phrase
                                            # is only evidence while it stays rare (C-47).
     "rescue_dissociation_table / PCT_CAVEAT — DR-5: inverts when the clean baseline is near zero"),
    ("ticket_knife installation",
     r"ticket_knife.{0,40}\b30/48\b|\b30/48\b.{0,40}ticket_knife",
     "0.331",
     "mapping_installation_verdict / power_caveat — C-32: power 0.331 at n=48, 0.399 at the ceiling"),
]


#: The caveat must sit NEAR the figure, not merely somewhere in the file. Whole-file presence is
#: satisfied by the document's own explanation of the rule — the concurrent session found their
#: one-tick-old guard passing on the strength of the section that describes the caveat, and mine had
#: the same defect: `POST-TREATMENT` appears once, in the corrections table, 40+ lines from anything.
#: Distinctive phrasing (C-47) is necessary; proximity is the other half.
#: CALIBRATED, not invented. Measured figure->caveat distances where the pairing is correct, over
#: both deliverables: 0, 0, 1, 1, 1, 3, 3 — every correct placement is within 3 lines. 6 gives 2x
#: headroom. The previous 12 was 4x the largest correct distance and the `<= 40` assertion 13x,
#: both chosen by eye. V-88's rule from the concurrent session: a threshold whose fixture sits AT
#: the boundary pins one side only, so draw fixtures from the CALIBRATION RANGE — and record the
#: range beside the constant, since their SMALL_DIVERGENCE was mis-set with its own calibration
#: data written directly above it.
CAUTION_WINDOW = 6
CALIBRATION_DISTANCES = (0, 0, 1, 1, 1, 3, 3)


def _violations(text, window=CAUTION_WINDOW):
    lines = text.splitlines()
    out = []
    for name, fig, phrase, why in CAUTIONED_FIGURES:
        for i, line in enumerate(lines):
            if not re.search(fig, line, re.I):
                continue
            near = "\n".join(lines[max(0, i - window): i + window + 1])
            if phrase.lower() not in near.lower():
                out.append((name, phrase, why, i + 1))
                break
    return out


def test_no_deliverable_quotes_a_cautioned_figure_without_its_caveat():
    for path in DELIVERABLES:
        v = _violations(open(path, encoding="utf-8").read())
        assert not v, (
            f"{os.path.basename(path)} quotes a cautioned figure without its caveat: "
            + "; ".join(f"line {ln}: {n} needs {p!r} ({w})" for n, p, w, ln in v))


def test_the_guard_fires_on_a_violating_document():
    """Their lesson twice over: a guard is worthless until shown to fail, and a guard that passes on
    the live document may be passing because the caveat happens to be discussed elsewhere."""
    bad = "the length-conditioned ASR rises to 0.31 across the sweep"
    v = _violations(bad)
    assert [n for n, _, _, _ in v] == ["length-conditioned ASR"], v
    assert not _violations(bad + " — note completion length is POST-TREATMENT")


def test_each_required_phrase_is_distinctive_not_generic():
    """C-47: `power` matched 6 unrelated occurrences and produced a false PASS.

    C-87 refines what "common" means: count only occurrences AWAY from a figure, not total ones.

    A phrase can become common in two opposite ways. `INVERTED` became common because a night of
    writing used it for an unrelated verdict vocabulary; those occurrences could satisfy the guard
    without the caveat being stated, so it stopped being evidence (C-86). `0.331` is common because
    the caveat is CORRECTLY STATED every time the figure is quoted -- 7 of its 8 occurrences sit
    within the window of a figure match. A total-count test conflates the two and would have forced
    a weaker phrase on a caveat whose frequency IS compliance.

    What compromises a required phrase is its presence where the figure is NOT: exactly the set of
    places it could pass the check spuriously.
    """
    for path in DELIVERABLES:
        lines = open(path, encoding="utf-8").read().splitlines()
        for name, fig, phrase, _ in CAUTIONED_FIGURES:
            figs = [i for i, l in enumerate(lines) if re.search(fig, l, re.I)]
            if not figs:
                # C-88: a DORMANT entry has no figure in this document, so every occurrence is
                # "stray" by construction and none of them can satisfy a proximity check that never
                # runs. The budget's whole rationale is "these could pass the guard spuriously";
                # where nothing can pass, the count measures something with no consequence -- and
                # policing it would fail the suite over a phrase whose distinctiveness is moot.
                # Dormancy itself is covered by test_dormant_entries_are_recorded.
                continue
            hits = [i for i, l in enumerate(lines) if phrase.lower() in l.lower()]
            stray = [i for i in hits if not any(abs(i - f) <= CAUTION_WINDOW for f in figs)]
            assert len(stray) <= 8, (
                f"{name}: required phrase {phrase!r} appears {len(stray)} times AWAY from its "
                f"figure in {os.path.basename(path)} (of {len(hits)} total). Those occurrences can "
                f"satisfy the guard without the caveat being stated at the figure -- the C-47 "
                f"defect. Frequency AT the figure is compliance and is not counted.")



def _unused_total_count_check():
    """Superseded by C-87; kept only to document what it used to assert."""
    corpus = "".join(open(p, encoding="utf-8").read() for p in DELIVERABLES).lower()
    for name, _, phrase, _ in CAUTIONED_FIGURES:
        assert corpus.count(phrase.lower()) <= 12, (
            f"required phrase {phrase!r} for {name} appears {corpus.count(phrase.lower())} times — "
            f"too common to evidence that the caveat was stated (the C-47 failure)")


def test_the_shipped_window_is_not_effectively_infinite():
    """The concurrent session's proximity fix was VACUOUS as first written: their tests monkeypatched
    the window, so a mutant widening it to 100000 passed everything. Proximity present in the code and
    absent in effect — and it was the same omission they had already closed for another constant two
    guards earlier, so the lesson did not transfer even within one session.

    This pins the SHIPPED value by asserting a case that passes wide and fails narrow.
    """
    assert CAUTION_WINDOW <= 2 * max(CALIBRATION_DISTANCES), (
        f"window {CAUTION_WINDOW} exceeds 2x the largest CORRECT figure-to-caveat distance "
        f"({max(CALIBRATION_DISTANCES)}) — it is permissive by construction")
    assert CAUTION_WINDOW > max(CALIBRATION_DISTANCES), (
        "window is narrower than a correct placement already in the document — it would fire on "
        "prose that is right")
    doc = ["the length-conditioned ASR is 0.31"] + ["filler"] * 30 + ["completion length is POST-TREATMENT"]
    text = "\n".join(doc)
    assert _violations(text, window=100000) == [], "sanity: a huge window should find no violation"
    assert _violations(text), "the SHIPPED window must flag a caveat 30 lines away"


def test_the_window_admits_the_calibration_range_and_rejects_the_old_one():
    """V-88: draw the fixture from the calibration range, not the threshold.

    Every correct placement in the live deliverables is within 3 lines. A caveat at 3 must pass; one
    at 12 — which the previous window admitted — must not.
    """
    def doc(gap):
        return "\n".join(["the length-conditioned ASR is 0.31"] + ["filler"] * gap
                          + ["completion length is POST-TREATMENT"])
    assert not _violations(doc(max(CALIBRATION_DISTANCES))), "a correct placement must pass"
    assert _violations(doc(12)), "the previous window's reach must now be rejected"


#: One line per entry that its OWN figure pattern must match. C-91: this makes every entry's
#: pattern REACHABLE-testable — a pattern that matches nothing can never fire, and for a DORMANT
#: entry the live-corpus check cannot tell a dormant pattern from a broken one. Their reachability
#: mechanism asks "can this ever be consulted", which for a figure pattern means "does it match
#: anything at all".
SPECIMENS = {
    "rescue percentage": "the recovery is 58% as % of rise across the four cells",
    "ticket_knife installation": "ticket_knife installs at 30/48 on the bank",
    "length-conditioned ASR": "the sweep is conditioned on length and reports 0.31",
}


def test_every_entry_pattern_is_reachable_matches_its_own_specimen():
    """C-91, ported from their reachability mechanism.

    C-72b's check asks whether an entry is currently LIVE. That cannot distinguish a dormant entry
    (correct — its figure is simply not quoted yet) from a BROKEN one whose pattern could never match
    anything. A dormant-and-broken entry looks exactly like a dormant-and-correct one, forever.

    Every entry therefore declares a specimen its own pattern must match. That is decidable from the
    entry alone, so a typo'd or over-narrowed pattern fails at authorship rather than sitting inert.
    """
    missing = [n for n, _, _, _ in CAUTIONED_FIGURES if n not in SPECIMENS]
    assert not missing, f"entries with no specimen, so their reachability is untested: {missing}"
    for name, fig, _, _ in CAUTIONED_FIGURES:
        assert re.search(fig, SPECIMENS[name], re.I), (
            f"{name}: the figure pattern {fig!r} does not match its own specimen "
            f"{SPECIMENS[name]!r} — the entry can never fire on any document.")


def _figure_match_counts():
    """How many times each entry's FIGURE pattern actually occurs in the live deliverables."""
    corpus = [open(p, encoding="utf-8").read() for p in DELIVERABLES]
    return {name: sum(len(re.findall(fig, c, re.I)) for c in corpus)
            for name, fig, _, _ in CAUTIONED_FIGURES}


def test_at_least_one_entry_is_live_in_the_deliverables():
    """C-72b: an entry whose figure pattern matches NOTHING can never fire, and a guard made only of
    such entries passes forever while watching nothing.

    Found by mutation: removing every occurrence of `POST-TREATMENT` left the suite green, because
    `length-conditioned ASR` matches zero times in either deliverable. That entry is inert BY DESIGN
    — an "if you quote X, say Y" caveat is dormant until someone quotes X — so it is kept. What was
    wrong is that the suite could not tell dormant-and-correct from broken.
    """
    counts = _figure_match_counts()
    live = {k: v for k, v in counts.items() if v > 0}
    assert live, (
        "NO cautioned figure is quoted in any deliverable — every entry is dormant, so this guard "
        f"cannot fail regardless of what the documents say. Counts: {counts}")


def test_the_guard_fires_on_a_LIVE_entry_not_only_a_dormant_one():
    """C-72b, the sharper half: every synthetic fixture in this file was built on `length-conditioned
    ASR`, the ONE entry that matches nothing in production. The guard's only proof of life exercised
    the only thing that was not alive.

    This rebuilds the fire-test from whichever entry is actually live, so the mechanism is
    demonstrated on an entry that operates.

    ⛔ C-76 — READ THIS BEFORE COUNTING THIS TEST AS MUTATION-VERIFIED. No CONFIG mutation can
    isolate this check. Configuring only the dormant entry fails it, but fails
    `test_at_least_one_entry_is_live_in_the_deliverables` through the SAME precondition, and
    mutating `_violations` fails all four mechanism tests. What this test uniquely asserts is
    that the fixture is DERIVED from the live set (`live[0]`) rather than hardcoded to the
    dormant entry — a property of how the test is written, not of the data it reads. Its
    guarantee is STRUCTURAL, not empirical: it stops a future edit regressing the fixture, and
    that is real, but it is not a killed mutant and must not be tallied as one.
    """
    counts = _figure_match_counts()
    live = [(n, f, p) for n, f, p, _ in CAUTIONED_FIGURES if counts[n] > 0]
    assert live, "no live entry to exercise (see test_at_least_one_entry_is_live_in_the_deliverables)"
    name, fig, phrase = live[0]
    # a violating document built from the entry's OWN pattern, so the fixture cannot drift from it
    specimen = SPECIMENS[name]
    assert re.search(fig, specimen, re.I), f"specimen for {name!r} does not match its own figure pattern"
    v = _violations(specimen)
    assert [n for n, _, _, _ in v] == [name], f"guard failed to flag a live entry {name!r}: {v}"
    assert not _violations(specimen + " — " + phrase), (
        f"guard still flags {name!r} after its required phrase {phrase!r} is supplied")


def test_dormant_entries_are_recorded_so_going_dormant_is_visible():
    """A live entry that goes dormant — because the figure stopped being quoted — silently stops
    watching. Recording the counts makes that a visible change rather than an invisible one.
    """
    counts = _figure_match_counts()
    dormant = sorted(k for k, v in counts.items() if v == 0)
    assert dormant == ["length-conditioned ASR"], (
        "the set of DORMANT cautioned figures changed. This is not necessarily a defect — an entry "
        "is dormant when its figure is not currently quoted — but it changes what this guard is "
        f"actually watching, so it must be acknowledged. Now dormant: {dormant}; counts: {counts}")
