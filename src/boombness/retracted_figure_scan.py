"""Scan live deliverables for RETRACTED figures, deriving the figure list from the retraction
registry itself rather than from a hand-maintained pattern list.

WHY THIS EXISTS (2026-08-23). `retraction_sweep.py` matches hand-written patterns. On 2026-08-23 its
R-20 rule required the literal string "arm F" within 60 chars of the figure, and the report stated the
same retracted claim three times WITHOUT the label -- including in decision-gate row 2, which was
scored YES on it. The sweep reported CLEAN for three days.

The structural problem is that the pattern list is a SECOND record of what was retracted, maintained by
hand, and it can silently fall behind the registry. This scanner has no list: it reads the registry
table and takes the retracted claim's own figures as the patterns. A new retraction is covered the
moment its row is written.

⚠ NOT WIRED INTO `check_all.py`, AND THAT IS A MEASURED DECISION, NOT AN OVERSIGHT (2026-08-23).
Measured precision on the real documents: **139 flags, 1 genuine**. The premise -- that a retracted
figure's VALUE identifies it -- is false in this corpus, for two reasons found by running it:

  * striking a PHRASE strikes every number inside it, including numbers that are still live elsewhere.
    `0.0305` is "struck" only because it sits inside a struck comparator at report:671, while +0.0305
    is a live §14-B result. The harvest cannot tell those apart.
  * a bare value collides. R-20's effect size `+0.305` matched two unrelated p-values of 0.305 in a
    layer table.

This is the third time this repo has learned that a number is not an identity (the §19 sourcing check
v1/v2 learned it twice, and its artifact still carries the note "with ~200 artifacts holding tens of
thousands of floats, numeric coverage carries no information"). Wiring this in as a blocking guard
would train its reader to ignore it, which is worse than not having it.

Kept as a DIAGNOSTIC because the one genuine hit was worth the run: it found that report §4b -- a whole
section whose stated job is "what it does to every intervention claim" -- was built on the readout R-6
withdrew, with only 1 of its 7 table rows marked. Run it by hand when the registry changes; read the
output as leads, not findings.

It does NOT replace the sweep. The sweep catches PROSE restatements that carry no figure at all (R-20's
third site was exactly that). This catches figures the sweep's author never encoded. They fail
differently on purpose.
"""
import re
import sys

from retraction_sweep import MARKER, DELIVERABLES, LIVE_PREFIX_ENDS_AT

REGISTRY = "reports/boombness_objective_sprint_report.md"
ROW = re.compile(r"^\|\s*\*{0,2}(R-\d+(?:\s*…\s*R-\d+)?)\b")

# A figure is only usable as a fingerprint if it is DISTINCTIVE. Bare "0.5" or "2" appear on hundreds
# of unrelated lines. Require >=3 decimal places, or a percent, or an N-fold ratio.
#
# ⛔ THE UNIT IS PART OF THE FINGERPRINT. A first draft stored the percent "84%" as bare `84` and then
# searched for `84`, which matches a line number, an n, a layer index and a year. Percents and ratios
# keep their unit or they are not distinctive at all -- the whole premise of this file is that a
# fingerprint is specific enough to accuse a line with.
FIG = re.compile(r"(?<![\d.])([+\-−]?\d+\.\d{3,})(?![\d])"
                 r"|(?<![\d.])(\d{2,3}%)"
                 r"|(?<![\d.])(\d+(?:\.\d+)?\s*[×x])(?![a-z])")


def figures(cell):
    out = set()
    for m in FIG.finditer(cell):
        raw = next(g for g in m.groups() if g)
        out.add(re.sub(r"\s+", "", raw.lstrip("+").replace("−", "-")))
    return out


STRUCK = re.compile(r"~~([^~\n]{1,120})~~")


def struck_figures(paths):
    """Figures the author explicitly STRUCK THROUGH -- an authorial 'this number is dead'.

    This is the registry's real figure source. The registry table's CLAIM column turned out to be
    mostly prose ("Boombness predicts attack success"); only 8 rows of 23 carry a distinctive number
    there, so a claim-cell-only parser refused to run. The struck spans carry the rest.

    Span bounded to ONE line and 120 chars on purpose: `~~(.+?)~~` with DOTALL over a document with an
    unpaired `~~` swallows whole tables between two distant markers -- measured at 824 spurious
    figures before this bound.
    """
    out = {}
    for p in paths:
        try:
            text = open(p, encoding="utf-8").read()
        except OSError:
            continue
        for m in STRUCK.finditer(text):
            for f in figures(m.group(1)):
                out.setdefault(f, set()).add("struck")
    return out


def registry_figures(path=REGISTRY):
    """Return {figure: [R-ids]} taken from each row's CLAIM cell only."""
    claims, disposition = {}, set()
    for line in open(path, encoding="utf-8"):
        if not ROW.match(line.strip()):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 3:
            continue
        rid, claim, disp = cells[0], cells[1], " ".join(cells[2:])
        # The disposition cell holds the REPLACEMENT numbers -- the corrected values a live document
        # is SUPPOSED to quote. Flagging those would invert the guard, so they are collected and
        # subtracted below. This is the single most important line in the file.
        disposition |= figures(disp)
        for f in figures(claim):
            claims.setdefault(f, []).append(re.sub(r"\*", "", rid))
    for f, srcs in struck_figures([REGISTRY] + list(DELIVERABLES)).items():
        claims.setdefault(f, []).extend(sorted(srcs))
    return {f: ids for f, ids in claims.items() if f not in disposition}, disposition


def blocks(text):
    """Same scoping as retraction_sweep: a table ROW is a self-contained assertion."""
    line_no, para, start, out = 1, [], 1, []

    def flush():
        nonlocal para, start
        if para:
            out.append((start, "\n".join(para)))
            para = []

    for line in text.split("\n"):
        s = line.strip()
        if s.startswith("|"):
            flush()
            out.append((line_no, line))
            start = line_no + 1
        elif not s:
            flush()
            start = line_no + 1
        else:
            if not para:
                start = line_no
            para.append(line)
        line_no += 1
    flush()
    return out


def main() -> int:
    figs, disp = registry_figures()
    if len(figs) < 10:
        print(f"[retracted-figures] REFUSING: only {len(figs)} figures parsed from the registry -- "
              f"the table format probably changed. Fix the parser; do not trust a green run.",
              file=sys.stderr)
        return 2
    bad = []
    for path in DELIVERABLES:
        try:
            text = open(path, encoding="utf-8").read()
        except OSError:
            continue
        stop = LIVE_PREFIX_ENDS_AT.get(path)
        if stop:
            m = re.search(r"^" + re.escape(stop) + r"\s*$", text, re.M)
            if m:
                text = text[:m.start()]
        for ln, block in blocks(text):
            if MARKER.search(block):
                continue
            if ROW.match(block.strip()):      # the registry's own rows
                continue
            for f in figs:
                tail = r"(?![\d])" if f[-1].isdigit() else ""
                if re.search(r"(?<![\d.])" + re.escape(f) + tail, block):
                    bad.append((path, ln, f, ",".join(figs[f])))
    print(f"[retracted-figures] {len(figs)} distinctive figures from the registry "
          f"({len(disp)} replacement figures excluded)")
    for path, ln, f, ids in bad:
        print(f"  UNQUALIFIED  {path}:{ln}  quotes {f}  [{ids}]")
    if bad:
        print(f"[retracted-figures] {len(bad)} unqualified occurrence(s)")
        return 1
    print("[retracted-figures] clean")
    return 0


if __name__ == "__main__":
    sys.exit(main())
