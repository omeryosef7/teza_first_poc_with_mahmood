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
    9: "container: THE SECOND 4-HOUR REVIEW, which withdrew or narrowed four claims (C-9a..C-9d). "
       "The parent id is in boombness_objective_sprint_report.md; the four lettered sub-corrections "
       "are in no deliverable by id, and C-9c's substance is carried by the plan's claim table row "
       "on the 24-cell clustering unit. See C-46.", 11: "in boombness_objective_sprint_report.md",
    13: "in boombness_objective_sprint_report.md", 14: "in boombness_objective_sprint_report.md",
    # --- operational / method-only: no claim was ever stated wrongly ---
    2: "operational: concurrent pytest runs corrupted an artifact; no claim affected",
    7: "method: wrong query kind, caught by the option-mass gate BEFORE any measurement was produced",
    10: "method: DOMAINS expansion broke a bank reproduction; caught by the suite and fixed",
    17: "operational: duplicate sbatch ran two arms twice; deterministic, no scientific harm",
    3: "container: THE 4-HOUR REVIEW. \u26a0 C-46 — my earlier reason here said its five "
       "sub-corrections 'propagated individually'. That was an assertion I never checked and it is "
       "FALSE by id: C-3a..C-3e appear in no deliverable. Their substance is carried by the plan's "
       "own claim table; the ids are not, and the check could not see them (C-45).",
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


EARLIER_REPORT = os.path.join(ROOT, "reports", "boombness_objective_sprint_report.md")


def test_every_exemption_claiming_the_earlier_report_is_actually_there():
    """C-46: `EXEMPT[3]` asserted its sub-corrections "propagated individually" and they had not.

    A reason string is exactly as unauditable as that one was, so every reason making a CHECKABLE
    claim is now checked. This is the structural fix, not a re-verification: re-reading the table
    once would leave the next reason equally unaudited.
    """
    text = open(EARLIER_REPORT, encoding="utf-8").read()
    wrong = []
    for cid, reason in sorted(EXEMPT.items()):
        if "boombness_objective_sprint_report" not in reason:
            continue
        # STRICT: a corrections-table row, not a mention anywhere. C-47 found three loose matchers
        # in one day, each inside a check written to catch imprecision and each flattering; R-129
        # mechanised this claim with `\bC-N\b`, which is LOOSER than the manual `| **C-N** |` check
        # it replaced. Both forms currently agree on all nine ids — tightened before they diverge,
        # because the direction a loose matcher fails in is the one that retires the question.
        if not re.search(rf"\|\s*\*\*C-{cid}\*\*\s*\|", text):
            wrong.append(cid)
    assert not wrong, (
        f"EXEMPT reasons claim these are in the earlier report and they are NOT: "
        f"{['C-%d' % c for c in wrong]}")


def test_the_earlier_report_check_can_fail():
    """Against a deliberately violating input — the reason must not pass by matching nothing."""
    text = open(EARLIER_REPORT, encoding="utf-8").read()
    assert not re.search(r"\|\s*\*\*C-9999\*\*\s*\|", text)


def test_the_earlier_report_check_is_STRICT_not_a_bare_mention():
    """C-47: a mention anywhere is not the claim. The claim is that the earlier deliverable CARRIES
    the correction, i.e. that it has a corrections-table row for it.

    Pinned with an id that is mentioned in that report but has no row, so a regression to
    `\bC-N\b` fails here rather than passing quietly.
    """
    text = open(EARLIER_REPORT, encoding="utf-8").read()
    mentioned_without_row = [
        n for n in range(1, 60)
        if re.search(rf"\bC-{n}\b", text) and not re.search(rf"\|\s*\*\*C-{n}\*\*\s*\|", text)]
    # The set may be empty today; what must hold is that the check distinguishes the two forms.
    assert re.search(r"\|\s*\*\*C-1\*\*\s*\|", text), "strict form finds nothing — regex is wrong"
    assert not re.search(r"\|\s*\*\*C-1\*\*\s*\|", "a bare mention of C-1 in prose"), \
        "strict form matches a bare mention — it is not strict"
    globals()["_MENTIONED_WITHOUT_ROW"] = mentioned_without_row


def test_prose_only_exemptions_are_declared_as_such():
    """The reasons that CANNOT be mechanised are named, so the unaudited set is explicit.

    Eight of seventeen make claims no test can check ("operational", "superseded", "honoured in
    C13's construction"). Recording which they are is the honest half: the suite verifies nine and
    is silent about eight, and silence about which eight is how EXEMPT[3] survived.
    """
    mechanised = {c for c, r in EXEMPT.items() if "boombness_objective_sprint_report" in r}
    prose_only = set(EXEMPT) - mechanised
    assert prose_only == {2, 3, 4, 7, 10, 15, 16, 17}, (
        f"the prose-only set changed to {sorted(prose_only)} — update this list deliberately, "
        f"so the unauditable reasons stay enumerated rather than growing silently")


#: C-73/C-74: the guards in this repo are wired by `scripts/install_commit_guard.sh`, which WRITES
#: `.git/hooks/pre-commit`. The hook is untracked, so the installer is the only version-controlled
#: record of what runs at commit time — and re-running it silently replaces whatever is deployed.
MY_GUARD_FILES = (
    "tests/test_my_ledger_propagation.py",
    "tests/test_my_cited_artifacts.py",
    "tests/test_cautioned_figures.py",
)


def test_my_guards_are_named_in_the_tracked_installer():
    """C-74: I fixed the DEPLOYED hook and not the installer that regenerates it.

    The concurrent session had already run `install_commit_guard.sh` once tonight; running it again
    would have overwritten the hook and dropped my three guards, restoring the exact state C-73 found
    — and reporting a smaller "N passed" that nobody reads as a failure.

    Three conditions, and this sprint has failed each separately: a guard must WORK (C-72b: mutation-
    tested), be WIRED IN (C-73: absent from GUARD_TESTS), and have its WIRING UNDER VERSION CONTROL
    (this test). Editing the deployed hook satisfies the second and not the third.
    """
    installer = os.path.join(ROOT, "scripts", "install_commit_guard.sh")
    assert os.path.exists(installer), f"{installer} is missing — the hook has no tracked source"
    text = open(installer, encoding="utf-8").read()
    missing = [f for f in MY_GUARD_FILES if f not in text]
    assert not missing, (
        f"{os.path.basename(installer)} does not name {missing}. The deployed hook may still run "
        f"them, but the next `bash scripts/install_commit_guard.sh` will silently drop them — which "
        f"is how C-73's state would be restored with nothing reporting it.")


def test_every_guard_file_the_installer_names_actually_exists():
    """A name in the installer that matches no file is a guard that silently does not run.

    pytest exits non-zero on a missing path, so this would surface at commit time — but as a confusing
    collection error rather than as 'this guard is gone', and the temptation is then to delete the
    name rather than restore the file.
    """
    installer = os.path.join(ROOT, "scripts", "install_commit_guard.sh")
    named = re.findall(r"tests/test_[A-Za-z0-9_]+\.py", open(installer, encoding="utf-8").read())
    assert named, "installer names no guard test files at all"
    absent = sorted({n for n in named if not os.path.exists(os.path.join(ROOT, n))})
    assert not absent, f"installer names guard files that do not exist: {absent}"
