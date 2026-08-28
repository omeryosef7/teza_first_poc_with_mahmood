"""Every correction in MY plan log must reach MY deliverable's corrections table.

This failure has happened twice: DR-14 found C-32/C-33 missing, DR-16 found C-39 missing. Both
times the entry demonstrably existed where I wrote it, which is why the gap is invisible from
inside the writing session, and both times it happened during a fast cross-session exchange.

The concurrent session automated the same check for their pair of files (`ledger_propagation_check`,
check_all guard #7 as of 2026-08-28). **That guard does not cover these files** — it reads
`BOOMBNESS_RESEARCH_VALIDATION_AND_OBJECTIVE_PLAN.md` and `boombness_claim_ledger_2026-08-27.json`.
Treating its green as coverage here would be the green-on-green error they flagged: a passing check
that never looked at the thing you think it checked.

Strict by design. Unlike theirs, every `C-NN` here is a claim-level correction by construction — the
method-only fixes get `R-NN`. So silence is not merely disallowed, absence is.
"""

import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLAN = os.path.join(ROOT, "external_md",
                    "DEMONSTRATION_RETRIEVAL_BEHAVIORAL_CAUSALITY_NEXT_PHASE_PLAN_AND_PROGRESS.md")
DELIVERABLE = os.path.join(ROOT, "reports", "SPRINT_SUMMARY_2026-08-25_BEHAVIORAL_CAUSALITY.md")

#: Corrections deliberately absent from THIS deliverable, each with a stated reason.
#: Silence is the failure mode, not absence — so a correction may be omitted, but never quietly.
#: Registered 2026-08-28 after this check found seven that no by-hand count had covered: my manual
#: audits ran C-19..C-40 and so ASSUMED the range, which is why an automated check was worth writing.
EXEMPT = {
    # --- carried by the EARLIER deliverable, reports/boombness_objective_sprint_report.md ---
    1: "in boombness_objective_sprint_report.md", 5: "in boombness_objective_sprint_report.md",
    6: "in boombness_objective_sprint_report.md", 8: "in boombness_objective_sprint_report.md",
    9: "in boombness_objective_sprint_report.md", 11: "in boombness_objective_sprint_report.md",
    13: "in boombness_objective_sprint_report.md", 14: "in boombness_objective_sprint_report.md",
    # --- operational / method-only: no claim was ever stated wrongly ---
    2: "operational: concurrent pytest runs corrupted an artifact; no claim affected",
    7: "method: wrong query kind, caught by the option-mass gate BEFORE any measurement was produced",
    10: "method: DOMAINS expansion broke a bank reproduction; caught by the suite and fixed",
    17: "operational: duplicate sbatch ran two arms twice; deterministic, no scientific harm",
    3: "container: a 4-hour review whose five sub-corrections propagated individually",
    # --- claim-level, but discharged in the CLAIM'S CONSTRUCTION rather than as a table row ---
    4: "superseded: the generation-cap concern is discharged by C7's 640-cap truncation check (R-75)",
    15: "honoured in C13's construction: the re-judge it mandated IS C13 (PR-21, same judging window, "
        "drift 2-4 rows), so the corrected claim is the one in the ledger",
    # --- found only after C-45 hardened the heading match; both opened in combined `R-nn / C-nn`
    #     headings that the previous single-token pattern could not see ---
    12: "in boombness_objective_sprint_report.md (2 rows). PR-9's second outcome, which became live "
        "claim C2; it propagated, my check just could not see it was a correction.",
    16: "operational: a SLURM control-plane Protocol authentication error caused a partial judge "
        "output to be read; it happened to agree with the truth. No claim was stated wrongly.",
}


#: A correction heading is any markdown heading whose SUBJECT is C-NN — i.e. the id appears before
#: the em-dash that separates the heading's title from its summary.
#:
#: The previous pattern required exactly one whitespace-delimited token before the id, so it silently
#: MISSED `### <marker> **C-49**`, `### <marker> CORRECTION C-52` and `#### <marker> C-53`. It passed
#: only because every correction written so far happened to use a shape it handled — a check whose
#: correctness was contingent on an accident of its inputs, which is the failure class the concurrent
#: session named from C-44. A miss here is invisible: the correction is simply never checked.
#:
#: Matching C-NN anywhere in the heading would over-match instead, because R-entry headings cite
#: corrections after the dash (`### R-103 — C-31/C-33 corrected readings...`). Hence: before the dash.
HEADING = re.compile(r"^#{2,6}[^\n]*?$", re.M)


def corrections_in_plan(text):
    """Correction ids opened by a heading, robust to marker, emphasis, wording and heading depth."""
    out = set()
    for line in HEADING.findall(text):
        subject = re.split(r"\s+[—-]{1,2}\s+", line, maxsplit=1)[0]
        out |= {int(m) for m in re.findall(r"\bC-(\d+)\b", subject)}
    return out


def corrections_in_deliverable(text):
    """`| **C-NN** |` — a row of the deliverable's corrections table."""
    return {int(m) for m in re.findall(r"\|\s*\*\*C-(\d+)\*\*\s*\|", text)}


def missing(plan_text, deliverable_text, exempt=()):
    return sorted(corrections_in_plan(plan_text)
                  - corrections_in_deliverable(deliverable_text)
                  - set(exempt))


def test_every_correction_reached_the_deliverable():
    plan = open(PLAN, encoding="utf-8").read()
    deliv = open(DELIVERABLE, encoding="utf-8").read()
    gaps = missing(plan, deliv, EXEMPT)
    assert not gaps, (
        f"corrections in the plan log but NOT in the deliverable's table: "
        f"{['C-%d' % g for g in gaps]}. Add the row, or register an EXEMPT entry with a reason.")


def test_the_heading_match_is_not_contingent_on_my_formatting():
    """C-45: the previous pattern passed only because every correction happened to fit its shape.

    A miss here is invisible — the correction is simply never checked for propagation — so the
    match must survive marker, emphasis, wording and heading depth. It must ALSO not over-match:
    R-entry headings cite corrections after the dash and are not themselves corrections.
    """
    for text in ("### C-90 — no marker",
                 "### \u26d4 C-91 (12:00) — marker",
                 "### \u26d4\u26d4 C-92 — double marker",
                 "### \u26d4 **C-93** — bold id",
                 "### \u26d4 CORRECTION C-94 — two words before the id",
                 "#### \u26d4 C-95 — four hashes",
                 "### \u26d4 R-99 / C-96 (12:00) — combined heading"):
        assert corrections_in_plan(text), f"heading not recognised: {text}"
    # must NOT count a correction merely cited in an R-entry's summary
    assert not corrections_in_plan("### R-103 (07:15) — **C-31/C-33 corrected readings**")


def test_the_check_can_actually_fail():
    """Their lesson, taken: a mutation test against an all-green input measures nothing.

    So this asserts on a DELIBERATELY VIOLATING input. Without it, the test above passes equally
    well if `corrections_in_plan` silently returns the empty set.
    """
    plan = "### C-41 something went wrong\n### C-42 something else\n"
    deliv = "| **C-41** | a | b |\n"
    assert missing(plan, deliv) == [42]
    assert missing(plan, deliv, exempt={42}) == []


def test_it_finds_the_real_corrections_and_not_zero_of_them():
    """Guards against the degenerate pass: a regex that matches nothing also reports no gaps."""
    plan = open(PLAN, encoding="utf-8").read()
    deliv = open(DELIVERABLE, encoding="utf-8").read()
    found_plan = corrections_in_plan(plan)
    found_deliv = corrections_in_deliverable(deliv)
    assert len(found_plan) >= 20, f"only found {len(found_plan)} corrections in the plan"
    assert len(found_deliv) >= 20, f"only found {len(found_deliv)} rows in the deliverable"
    assert 39 in found_plan and 39 in found_deliv       # the DR-16 gap, now closed
    assert 32 in found_plan and 33 in found_plan        # the DR-14 gaps
