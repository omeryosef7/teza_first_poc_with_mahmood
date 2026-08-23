"""pvalue_hygiene_check.py — is every small p-value in the deliverables qualified?

WHY THIS EXISTS. On 2026-08-22 I wrote a rule ("how to read every p-value in this report": with k
informative clusters the attainable two-sided floor is 2/2^k; a p below its design's floor is
bootstrap/parametric, not clustered evidence; quote the CI for magnitude) and then applied it to ONE
gate row. An audit found three further tables that declare themselves "domain-clustered over 6
domains" and print p-values below the resulting 0.031 floor, uncaveated.

That is the third instance in a week of the same habit -- a rule adopted under correction, applied at
the site of the correction and nowhere else. A habit cannot be fixed by intending to remember it, so
it is mechanised here.

WHAT IT CHECKS. Any p-value below THRESHOLD quoted in a deliverable must have a qualifier within the
same block: a floor mention, an explicit "bootstrap"/"parametric"/"uncorrected", a CI alongside, or a
retraction marker. This is deliberately a LINT, not a proof -- it cannot know a claim's k. It is
calibrated to catch the specific failure that has already happened three times: a small p presented
bare, in a section whose design cannot produce it.

DELIBERATELY NOISY-SIDE-SAFE. It runs on the two DELIVERABLES only, not the logs: the logs are a
record of what was believed when, and linting them would flag history. Same reasoning as
`retraction_sweep`'s LIVE_PREFIX_ENDS_AT.
"""
from __future__ import annotations

import argparse
import re
import sys

DELIVERABLES = [
    "reports/boombness_objective_sprint_report.md",
    "reports/boombness_objective_sprint_short_update.md",
    # ⛔ THREE GUARDS, THREE DIFFERENT SCOPE DECISIONS ABOUT ONE FILE (audit #11, 2026-08-22).
    # `docs/BOOMBNESS_CONTINUATION_LOG.md` is swept IN FULL by retraction_sweep (whose comment calls it
    # "the LIVE board"), checked by markdown_structure_check, and was EXCLUDED here on the grounds that
    # "the logs are a record". Both cannot be right, and the cost was real: the log's own Gate table --
    # a live surface it re-derives and cites -- carried `p=0.0109` and `p=0.0010` bare, the second
    # below the 0.031 floor a 6-domain design can attain.
    #
    # Resolved the way retraction_sweep already resolved it: sweep the LIVE HEAD, leave the dated tick
    # entries alone. One policy, stated once, for a file three guards disagreed about.
    "docs/BOOMBNESS_CONTINUATION_LOG.md",
]

#: file -> heading at which the live region ends (mirrors retraction_sweep.LIVE_PREFIX_ENDS_AT)
LIVE_PREFIX_ENDS_AT = {
    "docs/BOOMBNESS_CONTINUATION_LOG.md": "## Defect table — external critique's 31 findings",
}
# a p-value at or below this is small enough that its design's clustering matters
THRESHOLD = 0.031
# also catch "p <= 0.0004" and "p-value of 0.0004" (audit #11 P3/P4)
PVAL = re.compile(r"p(?:-value)?(?:_cl|_perm|_boot)?\s*(?:of\s*)?[=<≤]{1,2}?\s*"
                  r"\*{0,2}(\d?\.\d+|\d+\.?\d*e-\d+)", re.I)
# `\[\+?[-−]?\d` matched ANY bracketed number -- including a citation like "[3]" (audit #11). An
# interval qualifies only if it looks like one: two numbers separated by a comma inside brackets.
# ⛔ SPLIT 2026-08-23. `retract|withdraw|⛔|supersed` used to sit in this one list, so ANY retraction
# marker anywhere in a block exempted EVERY small p in it -- including live ones. Measured: 32 of 135
# blocks with a small p (24%) were riding on a retraction marker alone.
#
# The live cost was decision-gate row 3, which strikes ~~+0.056 (p=0.0077)~~ and then, in the same row,
# cites "comprehension unchanged (p=0.681)" as SUPPORT -- the R-6 figure, computed on a readout whose
# options held 4.4e-05 of next-token mass. `retraction_sweep`'s R6 pattern matches `p=0.681` exactly;
# it never fired because that row's OWN strikethrough of a different number exempted the whole row.
# This is the file-level failure mode this repo has now hit at paragraph scope (audit #11), at table
# scope (the 17-line table), and here at row scope: one marker vouching for its neighbours.
#
# Now: a retraction marker exempts a p only if THAT p is itself struck through. A live p needs a real
# floor/interval qualifier, which is what §0b actually asks for.
QUALIFIER = re.compile(
    r"floor|bootstrap|parametric|uncorrected|not clustered|attainable|"
    r"CI\s*\[|\[\s*[-−+]?\d*\.?\d+\s*,\s*[-−+]?\d*\.?\d+\s*\]|"
    r"sign-flip|permutation|delta method", re.I)

STRUCK_SPAN = re.compile(r"~~[^~\n]{1,200}?~~")

# A block whose OPENING announces a retraction is a retraction notice: the dead p is its SUBJECT, and
# demanding a floor caveat there is noise. A marker buried mid-row is a different thing -- it refers to
# some other figure and must not vouch for a live p beside it. First measurement of the split rule:
# 17 flags with no leading-announcement exemption, of which 16 were legitimate notices.
ANNOUNCE = re.compile(r"(⛔|RETRACT|WITHDRAW|SUPERSED)", re.I)


def _is_notice(blk):
    head = blk[:120]
    # skip a leading table-cell prefix like "| 5 | Random controls fail | " so the announcement is
    # still "leading" inside a row.
    return bool(ANNOUNCE.search(head))


def _struck_ranges(blk):
    return [(m.start(), m.end()) for m in STRUCK_SPAN.finditer(blk)]


def blocks(text):
    out, cur, start = [], [], 1
    for i, line in enumerate(text.split("\n"), 1):
        if line.startswith("|"):                 # table rows are their own block
            if cur:
                out.append((start, "\n".join(cur))); cur = []
            out.append((i, line)); start = i + 1
            continue
        if not line.strip():
            if cur:
                out.append((start, "\n".join(cur))); cur = []
            start = i + 1
        else:
            if not cur:
                start = i
            cur.append(line)
    if cur:
        out.append((start, "\n".join(cur)))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--paths", nargs="*", default=DELIVERABLES)
    ap.add_argument("--threshold", type=float, default=THRESHOLD)
    args = ap.parse_args()
    bad = 0
    for path in args.paths:
        try:
            text = open(path, encoding="utf-8").read()
        except OSError:
            continue
        stop = LIVE_PREFIX_ENDS_AT.get(path)
        if stop:
            m = re.search(r"^" + re.escape(stop) + r"\s*$", text, re.M)
            if not m or text[:m.start()].count("\n") < 20:
                print(f"  {path}: REFUSING — live-prefix boundary {stop!r} not found as a heading, "
                      f"or the prefix collapsed. Fix the boundary; do not trust this run.")
                bad += 1
                continue
            text = text[:m.start()]
        hits = 0
        for ln, blk in blocks(text):
            smalls, small_pos = [], []
            for m in PVAL.finditer(blk):
                try:
                    v = float(m.group(1))
                except ValueError:
                    continue
                if v <= args.threshold:
                    smalls.append(m.group(0))
                    small_pos.append(m.start())
            if smalls and not QUALIFIER.search(blk):
                # a struck p is a dead p: it needs no floor caveat.
                if _is_notice(blk):
                    continue
                struck = _struck_ranges(blk)
                # PER-OCCURRENCE, not per-block: a p described in its own immediate context as dead
                # ("the failure behind a retracted p=0.0014") needs no floor caveat, while a live p
                # elsewhere in the same block still does. Block-level exemption is what caused the
                # 24% over-exemption this rule replaced; re-introducing it here would undo the fix.
                smalls = [s for s, pos in zip(smalls, small_pos)
                          if not any(a <= pos < b for a, b in struck)
                          and not ANNOUNCE.search(blk[max(0, pos - 40):pos])]
            if smalls and not QUALIFIER.search(blk):
                hits += 1
                bad += 1
                print(f"  {path}:{ln}  UNQUALIFIED small p {smalls[:3]}")
                print(f"      {blk.strip()[:110]}")
        print(f"  {path:52s} {hits} unqualified small p-value block(s)")
    if bad:
        print(f"\n[p-hygiene] {bad} block(s) quote a p <= {args.threshold} with no floor, interval, "
              f"method or retraction marker. The rule is in report §0b.")
        return 1
    print(f"\n[p-hygiene] every p <= {args.threshold} in the deliverables carries a qualifier")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
