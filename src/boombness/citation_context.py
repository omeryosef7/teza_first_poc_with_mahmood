"""citation_context.py — is an artifact QUOTED AS EVIDENCE, or merely NAMED IN ITS OWN RETRACTION?

WHY. `empty_goal_leakage_check` and `readout_gate_check` both ask "is this tainted artifact live in a
deliverable?" and both answer by substring: does its filename appear in the report? That over-reports
badly, because the *correct* handling of a tainted artifact is to name it inside a retraction notice —
so an artifact keeps reading as LIVE precisely because it was properly withdrawn. Both scanners have
carried this as a documented limitation; this is the fix.

THE TEST. For every occurrence of the artifact's name, look at the surrounding window. If a retraction
marker sits within it, that occurrence is a *withdrawal*, not a citation. An artifact is LIVE only if
at least one occurrence has no such marker nearby.

WHAT IT DOES NOT SOLVE, established by testing it before wiring it in. A retraction notice names TWO
artifacts: the withdrawn one and its replacement. Proximity cannot tell them apart, so the live
replacements `clearharm_decomposition_regoal.json` and `qwen3_l20_regoal.json` both classify as
`withdrawn_only` — the exact opposite of the truth. That is not a tuning problem; the signal it reads
is genuinely ambiguous.

CONSEQUENCE: this is NOT wired into `empty_goal_leakage_check` or `readout_gate_check` as a
suppressor. It would have converted their over-reporting (harmless, annoying) into under-reporting
(silent, dangerous), which is the wrong trade for a scanner whose whole job is to find things nobody
noticed. It is exported for explanation only — to answer "why is this still listed?" — and both
scanners keep reporting every hit.

This repo has been explicit that a heuristic made fatal trains the reader to ignore it
(`retraction_sweep` says so about its own registry check). A heuristic made *suppressive* is worse: it
trains nobody, because there is nothing left to read.
"""
from __future__ import annotations

import re

#: Markers that make a nearby mention a WITHDRAWAL rather than a citation.
RETRACTION_MARKERS = (
    "⛔", "RETRACTED", "retracted", "WITHDRAWN", "withdrawn", "supersed", "SUPERSED",
    "not reportable", "NOT REPORTABLE", "empty goal", "empty-goal", "do not quote",
    "tainted", "R-14", "R-6", "R-15", "R-18",
)
WINDOW = 700          # characters either side; retraction notices in this report run long


def classify(name: str, text: str, window: int = WINDOW):
    """('live'|'withdrawn_only'|'absent', n_occurrences, n_in_retraction_context)."""
    stem = name.replace(".json", "")
    # BOUNDED. An unbounded stem match makes `clearharm_decomposition` match inside
    # `clearharm_decomposition_regoal` -- the retracted artifact inheriting a hit from its own
    # replacement, which is how it first classified as `live`.
    hits = [m.start() for m in re.finditer(re.escape(stem) + r"(?![\w-])", text)]
    if not hits:
        return "absent", 0, 0
    in_ctx = 0
    for i in hits:
        ctx = text[max(0, i - window): i + window]
        if any(mk in ctx for mk in RETRACTION_MARKERS):
            in_ctx += 1
    return ("withdrawn_only" if in_ctx == len(hits) else "live"), len(hits), in_ctx
