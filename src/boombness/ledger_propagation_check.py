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
    "§6.1": "design arithmetic for a bank that was never generated — no claim depends on it",
    "§6.2": "design arithmetic, superseded by §6.3/§6.3.1 before any claim rested on it",
    "§6.3": "corrects §6.2's arithmetic; the surviving claim is recorded via PER_BANK_ICC",
}

#: Tokens that evidence a section reached the ledger. A section passes if ANY of its own distinctive
#: tokens appears there — deliberately loose, because the guard is against SILENCE and not against
#: imperfect wording.
TRACE_TOKENS = {
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
    "§6.3.1": ["per_bank_icc", "0.190"],
    "§6.4": ["codeword property", "0.381"],
}


def correction_sections(text: str):
    """Headings marked as corrections: the ⛔ marker, or CORRECTION/WITHDRAWN in the heading."""
    out = []
    for line in text.splitlines():
        if not line.startswith("#"):
            continue
        if "⛔" in line or re.search(r"\bCORRECTION\b|\bWITHDRAW", line):
            m = re.search(r"(§[0-9]+(?:\.[0-9]+)*)", line)
            if m:
                out.append((m.group(1), line.strip()))
    return out


def main() -> int:
    if not (os.path.isfile(PLAN) and os.path.isfile(LEDGER)):
        print("[ledger-prop] plan or ledger missing; nothing to check")
        return 0
    plan = open(PLAN, encoding="utf-8").read()
    blob = json.dumps(json.load(open(LEDGER))).lower()

    secs = correction_sections(plan)
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
          f"{len(seen) - len(METHOD_ONLY) - len(unclassified)} with a required ledger trace")
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
