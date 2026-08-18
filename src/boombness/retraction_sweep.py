"""retraction_sweep.py — find retracted figures still stated as fact in the deliverables.

WHY THIS EXISTS. Retracting a number in the progress log does NOT remove it from the documents it was
already copied into. That happened four times in this sprint before anyone noticed, and three of those
were found only after the retraction had been recorded elsewhere:
  * the §19 role answer kept the pooled F=0.175 as fact underneath its own retraction paragraph;
  * the steering table kept the fake band's mean/sd as a row;
  * the short update asserted that band as "highly reproducible" in prose;
  * the known-issues list still called the role null "tight".

PARAGRAPH SCOPE, NOT LINE SCOPE. The first version of this check was line-based and produced two false
positives, because a `⛔ RETRACTED` marker sits on the line *above* the figure it retracts. Markdown
context is a paragraph, so the scope here is the blank-line-delimited block.

SCOPE = THE DELIVERABLES ONLY. Default paths are the two reports plus the sanity check. Deliberately
NOT swept:
  * `docs/BOOMBNESS_SPRINT_PROGRESS.md` — an append-only journal. Its early entries are SUPPOSED to
    contain the original claim as originally stated; a retraction there is a later entry, not an edit
    to history. Sweeping it flags the historical record as a defect.
  * every other `docs/*.md` — legacy GCG / stage-4 logs where a bare number like `0.474` is an
    unrelated quantity. That produced 20+ false positives on the first run.

Exit code is 1 if any unqualified occurrence is found, so this can gate a commit.
"""
from __future__ import annotations
import argparse, glob, re, sys

# (label, regex) for every figure this sprint has retracted or superseded.
RETRACTED = [
    ("R4  naive 'manufactures signal'",      r"manufactures signal"),
    ("R5  3.7x Boombness-beats-refusalness", r"(?:3\.7|3\.66)\s*[×x][^\n]{0,60}(?:refusal|better|more)|(?:beats|outperforms)[^\\n]{0,40}refusaln"),
    ("R6  role 'tight null'",                r"F\s*=\s*0\.175|p\s*=\s*0\.972|sd of style means at \*\*3\.6%"),
    ("R7  fake 4-draw control band",         r"sd\s*0\.0049|between-draw sd \*\*0\.0049"),
    # CLAIM patterns, not figure patterns. The 08-17 sweep missed the stalest sentence in the short
    # update -- "the band is highly reproducible across four independent draws" -- because it asserted
    # the retracted result without quoting any number. Paraphrase cannot be caught in general; the
    # specific retracted CLAIM can be, and that is what actually misleads a reader.
    ("R7  4-draw band asserted as prose",    r"(?:four|4)\s+independent\s+draws|"
                                             r"reproducib[^\n]{0,40}(?:four|4)\s+draws"),
    # The 2026-08-18 audit found the retracted band's DERIVED statistics still tabled as fact in
    # both reports, one of them directly beneath the paragraph retracting it. My sweep missed them
    # because I had enumerated the band's mean and sd but not the t/p/CI computed FROM it. A
    # retraction must enumerate every number downstream of the withdrawn one, not just the headline.
    # NARROWED after the first version flagged the CORRECTED table: "clears the band" is a
    # legitimate verdict phrase, not a retracted claim. Match only the withdrawn NUMBERS.
    ("R7  band-derived t/p/CI",              r"0\.0014|0\.0778\s*±\s*0\.0241|[−-]3\.23|"
                                             r"[−-]0\.0375\s*±\s*0\.0206"),  # NOT bare 0.070:
    # that value also appears as an unrelated cosine in the d_surface table -> false positive.
    ("R9  §6.4 'metric of record'",          r"metric of record|direction_boombness[^\n]{0,40}survives"),
    ("R6  role 'definitively does not'",     r"role definitively does not change"),
    ("R6  role null called tight (prose)",   r"tight null|null is tight"),
    ("R8  capability channel as prose",      r"capability channel"),
    ("R8  'capability channel' as fact",     r"supplies content that makes a completion actually harmful"),
    ("C2  refusalness ratio 40x/14x",        r"(?:Boombness|boombness)[^\n]{0,60}\b40\s*[×x]|14\s*[×x]\s*more"),
    ("C3  sign-blind '2-3x the controls'",   r"2[–-]3\s*[×x]\s*the\s*controls"),
    ("C6  wrong-population figures",         r"refusal rate[^|\n]*0\.583|\+7\.30\s*pp"),
    ("C9  depth-mismatched L31 claim",       r"L31 effect replicates"),
    ("G1  chimera CI",                       r"\+23%\s*to\s*\+?135%"),
    ("superseded arm-F value",               r"arm F[^\n]{0,80}0\.474|0\.474[^\n]{0,40}arm F"),
    # ---- 2026-08-18 CONTINUATION SESSION. Five new retractions/corrections, added the SAME DAY
    # they were declared. A sweep whose pattern list lags its own retraction table reports "clean"
    # for precisely the claims most likely to be stale, which is worse than not running it at all:
    # it converts an unchecked document into a checked-looking one.
    ("R6  §2.6 verdicts from a 1e-5 tail",
     r"only arm that leaves comprehension unchanged|"
     r"comprehension (?:is )?preserved \(p\s*=\s*0\.68|p\s*=\s*0\.681"),
    ("R7  G3 edge null ranked at the retracted token",
     r"6\.25\s*%[^\n]{0,60}(?:does nothing|no effect)|however distributed|"
     r"cutting 100%[^\n]{0,40}84%"),
    ("R8  G1 superseded +84% on n=8 / 2 domains",
     r"\+?84%\s*of span|CI\s*\[\+?57%,\s*\+?105%\]|"
     r"n\s*=\s*8\s*families[^\n]{0,40}2\s*\*{0,2}domains"),
    ("R9  §18=B asserted as a settled label",
     r"outcome\s+B\b[^\n]{0,60}mechanistic but not causal|"
     r"§18\s*(?:label\s*)?(?:is|=)\s*\*{0,2}B\b"),
    ("R11 Holm backstop stated without L1",
     r"only at \*{0,2}L4 and L31|holm_rejected[^\n]{0,40}only at L4"),
    # ---- 2026-08-19 SESSION 2. Added the same day they were declared, per the rule above.
    # R-13: the incremental-R2 table that gave refusalness 5 predictors against Boombness's 1. The
    # withdrawn NUMBERS are the four cells; the withdrawn CLAIM is "matched footing"/"done correctly"
    # attached to them, which is what actually misleads, since the numbers alone look unremarkable.
    ("R13 incremental R2 at unmatched df",
     r"\+?0\.144\b|\+?0\.091\b[^\n]{0,40}refusaln|"
     r"refusaln[^\n]{0,40}adds[^\n]{0,20}\+?0\.144|"
     r"increment comparison, done correctly|"
     r"Boombness is close to redundant"),
    # R-14: every external-set ASR judged against an empty goal. The withdrawn numbers are the
    # ClearHarm arm ASRs as first published; the withdrawn CLAIM is that the bank-artifact
    # explanation is excluded, which was the whole point of the arm.
    ("R14 ClearHarm ASR from an empty goal",
     r"0\.101\s*(?:→|->|to)\s*\*{0,2}0\.542|"
     r"ASR\s*0\.1006|\b0\.2067\b|\b0\.3408\b|\b0\.5419\b|"
     r"bank-artifact explanation is \*{0,2}excluded"),
    # R-15: "harmful yes, benign no" -- one significant cell of six. The claim pattern is the target;
    # the deltas themselves are NOT retracted (they reproduce exactly), only the reading of them.
    ("R15 harm-general profile as fact",
     r"harm-general, not\s*\n?doublespeak-specific|"
     r"wherever there is an\s*\n?>?\s*attack|"
     r"clean split|"
     r"[≈~]0 on every benign condition|"
     r"generalises across three attack types"),
]
DELIVERABLES = [
    "reports/boombness_objective_sprint_report.md",
    "reports/boombness_objective_sprint_short_update.md",
    "docs/BOOMBNESS_MIDSESSION_SANITY_CHECK.md",
    # added 2026-08-18: the continuation log is the LIVE board, so a retracted figure asserted there
    # unqualified misleads exactly the reader this sweep exists to protect.
    "docs/BOOMBNESS_CONTINUATION_LOG.md",
]
# KNOWN LIMITATION (found 2026-08-18). A paragraph is exempted if it contains ANY marker word, but a
# paragraph can legitimately contain "corrected"/"was" while still ASSERTING a retracted claim in a
# later sentence. That happened in the §11 answer: "role definitively does not change Boombness" sat
# four lines below its own retraction, inside a paragraph containing "Corrected", so this sweep passed
# it and an independent audit caught it instead. The exemption is a heuristic, not a proof; claim-level
# patterns (below) are the defence, because they match the assertion rather than the number.
MARKER = re.compile(
    r"retract|withdraw|supersed|⛔|previously|earlier|revision \d|was\b|fake|not reportable|"
    r"instead of|rather than|naive one-way|no longer|corrected", re.I)


def sweep(paths):
    bad = []
    for f in paths:
        try:
            text = open(f, encoding="utf-8").read()
        except OSError:
            continue
        # paragraph = blank-line-delimited block; track starting line number
        line_no, para, start = 1, [], 1
        blocks = []
        for line in text.split("\n"):
            if line.strip() == "":
                if para:
                    blocks.append((start, "\n".join(para))); para = []
                start = line_no + 1
            else:
                if not para:
                    start = line_no
                para.append(line)
            line_no += 1
        if para:
            blocks.append((start, "\n".join(para)))
        for ln, block in blocks:
            if MARKER.search(block):
                continue                      # the paragraph marks it as retracted -> fine
            for label, pat in RETRACTED:
                m = re.search(pat, block)
                if m:
                    # report the offending LINE, not the paragraph head, or the output is unreadable
                    off = block[:m.start()].count("\n")
                    bad.append((f, ln + off, label, block.split("\n")[off].strip()[:120]))
    return bad


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--paths", nargs="*", default=DELIVERABLES,
                    help="default = the deliverables only; see the module docstring for what is "
                         "deliberately excluded and why")
    args = ap.parse_args()
    bad = sweep(args.paths)
    for f, ln, label, snippet in bad:
        print(f"  UNQUALIFIED  {f}:{ln}  [{label}]\n      {snippet}")
    print(f"\n[sweep] {len(args.paths)} file(s); {len(bad)} unqualified occurrence(s) of a retracted figure")
    if not bad:
        print("[sweep] clean — every retracted figure appears only inside a paragraph that marks it as such")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
