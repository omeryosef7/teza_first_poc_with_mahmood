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
}


def corrections_in_plan(text):
    """`### ... C-NN ...` headings — how a correction is opened in the plan log."""
    return {int(m) for m in re.findall(r"^###\s+\S*\s*C-(\d+)\b", text, re.M)}


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
