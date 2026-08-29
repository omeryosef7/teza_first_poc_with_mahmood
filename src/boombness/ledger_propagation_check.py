"""ledger_propagation_check.py — a correction written in the plan but never reaching the ledger.

THE FAILURE MODE, AND WHY IT IS INVISIBLE FROM INSIDE. A correction gets written up in the plan
document during a fast exchange, and the claim ledger — the artifact anyone auditing the claims
actually reads — never learns about it. **It is undetectable from the writing session, because the
entry demonstrably exists where you just wrote it.** Only a by-count audit across the two artifacts
finds it.

Both sessions on this sprint hit it. A peer found two occurrences (C-32/C-33, then C-39) via a
by-count audit and flagged it; running the same count here found **four** claim-bearing results
sitting in the plan and absent from the ledger:

    §5.20    the corpus batch-split audit, and that `main` moves by ZERO rows under it
    §5.20.1  the borrowed-window method correction that every adversarial bound depends on
    §6.3.1   the per-bank ICC measurements
    §6.4     domain clustering is not a codeword property

THE DESIGN, AND WHY IT IS NOT A BLANKET RULE. Not every correction changes a claim — several are
method or instrument corrections with no ledger consequence, and a guard that demanded a ledger
trace for all of them would fail constantly and be switched off. So this guard does not decide
which corrections matter. **It forces the decision to be made explicitly and recorded**: a
correction section either leaves a trace in the ledger, or it is named in `METHOD_ONLY` below with
a reason. Silence is the one thing it does not allow.

A new correction section therefore fails this guard until someone classifies it, which is the
point — the failure mode is silence, not misclassification.

Reads two files and emits counts. No model, no artifacts, no network.
"""
from __future__ import annotations

import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
PLAN = os.path.join(ROOT, "external_md", "BOOMBNESS_RESEARCH_VALIDATION_AND_OBJECTIVE_PLAN.md")
LEDGER = os.path.join(ROOT, "reports", "boombness_claim_ledger_2026-08-27.json")

#: A correction section is CLAIM-BEARING unless it is named here. The value is the reason, and it
#: is required: an unexplained exemption is the silence this guard exists to prevent.
METHOD_ONLY = {
    "§5.16": "fixes a screen's threshold, not any claim's verdict; the verdicts it re-derives are "
             "recorded on their own entries",
    "§5.18.1": "withdraws one supporting sentence; the claim it supported is recorded via "
               "SECOND_MODEL_BINDING on its entry",
    "§10.1": "design arithmetic for a bank that was never generated — no claim depends on it",
    "§10.2": "design arithmetic, superseded by §10.3/§10.3.1 before any claim rested on it",
    "§10.3": "corrects §10.2's arithmetic; the surviving claim is recorded via PER_BANK_ICC",
    "§12.15": "a commit-hygiene correction about git index semantics; no claim, figure or "
               "artifact value depends on it, and the swept files were the peer's own work "
               "which they confirmed intact",
    "§12.13": "widens a guard's path list and repairs two table rows; no figure value changed "
               "-- only cell alignment and one absent row label, and the mutation test is recorded",
}

#: Tokens that evidence a section reached the ledger. A section passes if ANY of its own distinctive
#: tokens appears there — deliberately loose, because the guard is against SILENCE and not against
#: imperfect wording.
TRACE_TOKENS = {
    "§0.4": ["truncation", "cap"],
    "§0.12": ["not_sprint_grade", "sprint-grade"],
    "§5.14": ["phase 3", "controllab"],
    "§6.1": ["composition", "dose"],
    "§7": ["gate"],
    "§7.2": ["g2"],
    "§7.6": ["degenerate"],
    "§10.5": ["reportab", "option_mass"],
    "§10.6.1": ["single-slot", "1.24"],
    "§11": ["complied", "kw_refusal"],
    "§0.2.3": ["truncation", "cap"],
    "§0.2.5": ["partial", "excluded"],
    "§4.1": ["liveness", "divergence"],
    "§5.2": ["population-dependent", "ticket_bomb"],
    "§5.4": ["legacy_all_query", "unscoped"],
    "§5.7": ["unscoped mask", "demo_processing_only"],
    "§5.9": ["window_knife"],
    "§5.13": ["knife"],
    "§5.20": ["42/48 -> 42/48", "batch_split_audit"],
    "§5.20.1": ["borrowed", "0.4616"],
    "§5.21": ["unmeasurable", "attrit"],
    "§5.22": ["unmeasurable", "attrit"],
    "§10.3.1": ["per_bank_icc", "0.190"],
    "§10.4": ["codeword property", "0.381"],
    "§11.1": ["admissibility_correction", "0.617"],
    "§11.2": ["guard_class_correction", "admissibility"],
    "§11.3": ["cadence", "self-audit"],
    "§11.5": ["cited_artifact", "guard"],
    "§11.6": ["cited_with_failures", "attrited"],
    "§11.7": ["superseded_by", "598"],
    "§11.7.1": ["582", "over-corrected"],
    "§11.7.2": ["scoped to the analysis", "aggregate"],
    "§11.8": ["18 of 31", "attribut"],
    "§11.9": ["clustering unit", "cell"],
    "§11.10": ["exempt", "downstream usage"],
    "§11.11": ["unmechanisable", "config_confounded"],
    "§11.12": ["adjacent", "paraphrase"],
    "§11.13": ["omitted-caveat", "term overlap"],
    "§11.14": ["cautioned", "loose matcher"],
    "§11.15": ["CAUTION_WINDOW", "artifact files"],
    "§11.16": ["SMALL_DIVERGENCE", "vacuous value"],
    "§11.17": ["pre-commit", "guard tests"],
    "§11.18": ["CALIBRATION_DISTANCES", "recomputed"],
    "§12": ["pools_not_prose", "43 domains"],
    "§12.1": ["k=38", "119"],
    "§12.3": ["overprecise", "29 - 63"],
    "§12.5": ["subsample ladder", "0.9-row"],
    "§12.6": ["0.080", "473"],
    "§12.7": ["incidental-replace", "6080"],
    "§12.8": ["0.291", "130.4"],
    "§12.9": ["asymptote", "66 rows"],
    "§12.10": ["fcslots", "2508"],
    "§12.11": ["3.16", "142.9"],
    "§12.2": ["silently overwrit", "38 unique"],
    "§12.12": ["0.2443", "pooled-vs-balanced"],
    "§12.16": ["96/96", "pre-registered", "truncation"],
    "§12.17": ["grew", "29/96", "masking"],
    "§12.18": ["3 rows", "judge noise", "27/96"],
    "§12.19": ["masking", "bidirectional", "stop_reason"],
    "§12.20": ["dynamic range", "6.5%", "basket_gun"],
    "§12.21": ["already existed", "384", "7.0%"],
    "§12.22": ["non-monotonic", "9/12", "n=16"],
    "§12.23": ["0.9627", "gate", "288"],
    "§12.24": ["incremental", "+0.1924", "dev and heldout"],
    "§12.25": ["prompt-level", "query occurrence", "dose + 1"],
    "§12.26": ["0.9038", "not quotable", "n_eff"],
    "§12.27": ["38 domain", "unseen", "pre-registered"],
    "§12.27.1": ["wild cluster", "positive control", "0.042"],
    "§12.27.2": ["fit-set-dependent", "downgraded", "6 seen"],
    "§12.28": ["12.7", "inadmissible", "quota"],
    "§12.29": ["run_completeness", "modal", "retrieval.jsonl"],
}


#: Floor for the degenerate-pass check; module-level so unit fixtures can scale it down while the
#: shipped guard keeps the real value.
MIN_EXPECTED = 10


def correction_sections(text: str):
    """Headings marked as corrections, EVERY one attributed to a section — none silently dropped.

    ⛔ THE FIRST VERSION DROPPED ANY CORRECTION HEADING THAT CARRIED NO `§` ID. It searched the
    heading for an id and, finding none, simply did not append it — no count, no warning. **13 of
    31 correction-marked headings in this plan have no id of their own**, because they are
    sub-headings inside a numbered section ("### ⛔ CORRECTION: I applied a Qwen3-derived window").
    So the guard examined 18 of 31 and reported success, and nothing in its output distinguished
    "the corrections are all classified" from "the scanner cannot see this shape".

    A peer hit the identical class in their own propagation guard — a heading pattern requiring
    exactly one token before the id, which silently missed bolded ids, two-word prefixes and
    four-hash headings — and named the signature: **nothing distinguishes clean inputs from inputs
    the check cannot see, and it is invisible to a guard AND to a reader, because the guard passes
    and the argument reads correctly.** The only way to find it is to feed the check shapes it has
    never seen.

    Fixed by tracking the enclosing section: a correction heading without its own id is attributed
    to the most recent heading that had one, and the attribution count is REPORTED so the guard can
    never again be silent about what it could not parse. A correction before any numbered section
    is returned under `None` and refused by the caller rather than dropped.
    """
    out, current = [], None
    for line in text.splitlines():
        if not line.startswith("#"):
            continue
        own = re.match(r"#+\s*(?:[^A-Za-z0-9§]*\s*)?(§[0-9]+(?:\.[0-9]+)*)", line)
        if own:
            current = own.group(1)
        if "⛔" in line or re.search(r"\bCORRECTION\b|\bWITHDRAW", line):
            sid = own.group(1) if own else current
            out.append((sid, line.strip()))
    return out


def main() -> int:
    if not (os.path.isfile(PLAN) and os.path.isfile(LEDGER)):
        print("[ledger-prop] plan or ledger missing; nothing to check")
        return 0
    plan = open(PLAN, encoding="utf-8").read()
    blob = json.dumps(json.load(open(LEDGER))).lower()

    secs = correction_sections(plan)

    # DEGENERATE-PASS FLOOR. A peer guarded this on their own version and I had not: if the marker
    # convention changes, or a path breaks, or the regex stops matching, `secs` is EMPTY and every
    # loop below is skipped -- so the guard reports success having checked nothing. That is the
    # green-on-green failure one level up from the mutation-test mistake, and the tell was already
    # visible in the summary line, which printed "-5 with a required ledger trace" on an empty scan.
    # The corpus has never had fewer than this many correction sections; a real drop means the
    # SCANNER broke, not that the corrections vanished.
    if len(secs) < MIN_EXPECTED:
        print(f"[ledger-prop] FAIL — only {len(secs)} correction sections found, expected at least "
              f"{MIN_EXPECTED}. The scanner or the marker convention has broken; a guard that "
              f"checks nothing must not report success.")
        return 1
    seen, unclassified, untraced = set(), [], []
    for sid, heading in secs:
        if sid in seen:
            continue
        seen.add(sid)
        if sid in METHOD_ONLY:
            continue
        toks = TRACE_TOKENS.get(sid)
        if toks is None:
            unclassified.append((sid, heading))
            continue
        if not any(t.lower() in blob for t in toks):
            untraced.append((sid, toks))

    print(f"[ledger-prop] {len(seen)} correction sections; "
          f"{len(METHOD_ONLY)} classified method-only; "
          f"{len([x for x in seen if x in TRACE_TOKENS])} with a required ledger trace")
    ok = True
    for sid, heading in unclassified:
        ok = False
        print(f"  UNCLASSIFIED {sid}: {heading[:88]}")
        print(f"      -> add {sid} to TRACE_TOKENS (claim-bearing) or METHOD_ONLY (with a reason)")
    for sid, toks in untraced:
        ok = False
        print(f"  NOT IN LEDGER {sid}: none of {toks} appears in the claim ledger")
    if not ok:
        print("[ledger-prop] FAIL — a correction is in the plan and unaccounted for in the ledger. "
              "This is invisible from the writing session; only the count finds it.")
        return 1
    print("[ledger-prop] every correction section is either traced to the ledger or classified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
