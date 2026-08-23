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
import argparse, glob, os, re, sys

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
    # R-7 DISCHARGED 2026-08-19. The retracted object was never the CLAIM ("6.25% of demo edges does
    # nothing however distributed") -- it was that claim computed from a ranking measured at the
    # final codeword occurrence rather than at `readout_pos`. The 24-family re-run at `--dst both`
    # re-derives it correctly, so the claim is now live and must NOT be flagged. What stays retracted
    # is the superseded ARITHMETIC: the 84% recovery, the 56,832/3,552 edge counts and the 6-family
    # run they came from. Matching the claim text here would flag the corrected section, which is
    # how a sweep starts costing more than it saves.
    ("R7  G3 numbers from the 6-family wrong-token run",
     r"cutting 100%[^\n]{0,40}84%|"
     r"56,?832|3,?552\s*edges|"
     r"recovers\s*\*{0,2}84%|84%,\s*CI\s*\[62%"),
    ("R8  G1 superseded +84% on n=8 / 2 domains",
     r"\+?84%\s*of span|CI\s*\[\+?57%,\s*\+?105%\]|"
     # MARKDOWN EMPHASIS CAN SIT ANYWHERE. The first version required the bold markers to follow
     # the digit (`2 **domains**`) and the report writes `**2 domains**`, so the sweep reported
     # CLEAN while "G1 is a pilot: n=8 families from **2 domains**" sat live in the limits list
     # (found 2026-08-20). Strip-insensitive: allow `*` and `_` freely between the tokens.
     r"n\s*=\s*8\s*[*_]{0,2}families[^\n]{0,40}[*_]{0,2}2\s*[*_]{0,2}domains|"
     r"G1 is a pilot"),
    ("R9  §18=B asserted as a settled label",
     r"outcome\s+B\b[^\n]{0,60}mechanistic but not causal|"
     r"§18\s*(?:label\s*)?(?:is|=)\s*\*{0,2}B\b"),
    # ---- R-20 / R-21 (2026-08-20; renumbered 08-21 — R-14/R-15 were already taken): arm F's behavioural gain is ~94% answer style. Added the same
    # day, because the two previous times this sweep reported CLEAN the pattern list was the weak
    # link, not the documents.
    # BROADENED 2026-08-23 (self-found while chasing sourcing flags -- NOT an audit finding;
    # an earlier draft of this comment credited a nonexistent "audit #18"). The first version keyed on the LABEL "arm F" within 60 chars of
    # the figure. But an arm's identity is its INTERVENTION -- add d_surface + remove refusalness -- and
    # the report states that claim three times WITHOUT ever writing "arm F": "Composing the two takes ASR
    # 0.243 -> 0.548", the same pair inside decision-gate row 2, and a purely prose form ("a second,
    # refusal-independent channel raises judged harmfulness once refusal is removed") carrying no figure
    # at all. The sweep reported CLEAN on all three. This is the repo's own rule -- address things by
    # identity, not by an incidental property -- violated inside the guard meant to enforce it, and it is
    # the same narrowness failure the R23 comment above already records.
    ("R20 arm F behavioural gain (judge artifact)",
     r"\+?0\.863|more than doubl\w+[^\n]{0,30}ASR|"
     r"arm F[^\n]{0,60}\+?0\.(?:548|305|417)|"
     r"\+?0\.(?:548|417)[^\n]{0,40}arm F|"
     # content-keyed: the composition stated without the label
     r"0\.243[^\n]{0,20}(?:→|->|to)[^\n]{0,10}\*{0,2}0\.548|"
     # \b matters: "deCOMPOSED ... refusal-removal arms" is the DISRUPTION decomposition, a different
     # claim, and the first draft of this alternative flagged it twice.
     r"\bcomposed with[^\n]{0,40}refusal[- ]removal|"
     r"Composing the two[^\n]{0,40}ASR|"
     r"refusal-independent channel[^\n]{0,60}rais\w+"),
    ("R21 Llama exempted from the style artifact",
     r"Llama results are (?:not|un)affected|inflation did not fire"),
    # ---- R-23 / R-24 (2026-08-21): E12 retracted in full. Added in the SAME tick as the retraction,
    # because the sweep had just reported "clean" on a run where it carried no pattern for either --
    # a guard that has never been pointed at a claim cannot vouch for it, and I nearly took that
    # "clean" as evidence. Both patterns carry CLAIM context, not bare numbers: "0.50" and "0.61"
    # alone would fire on dozens of unrelated lines in a document full of two-digit ratios.
    ("R23 E12 effect ratio / concept-general consequence",
     r"0\.0182\s*/\s*0\.0364|"
     r"(?:delivers|delivering)[^\n]{0,30}50%[^\n]{0,30}effect|"
     r"61%[^\n]{0,40}(?:delivers|half|50%)|"
     r"shared component is the caus\w+ active|"
     r"concept-general in consequence|"
     # ANY band-sd count, not just "7". The first version pinned the literal 7 and the report's
     # most-read block said "~16 band-sds" -- a THIRD narrowness failure in this file, and in the one
     # paragraph a reader is most likely to quote. Match any number of band-sds: every such claim is
     # scored against the 4096-d random band that R-23 discredited.
     r"~?\d+(?:\.\d+)?\s*band-sds"),
    ("R24 cos 0.61 read as the concept-general fraction",
     r"substantially but not wholly concept-general|"
     r"concept-general (?:fraction|component)[^\n]{0,40}0\.61|"
     r"0\.61\d{0,2}[^\n]{0,50}concept-general|"
     r"`?d_surface`?[^\n]{0,40}does what its name claims|"
     # PUNCTUATION BETWEEN THE TOKENS. The first version required "transfer at"; the report wrote
     # "shown to transfer, AT roughly half strength" -- one comma, and the pattern missed a LIVE
     # retracted claim sitting in the report's scope statement, the single sentence a reader is most
     # likely to quote. Third time a pattern here has been too narrow. Allow punctuation/words
     # between the verb and the phrase.
     r"transfers?[^\n]{0,20}(?:roughly )?half strength|"
     r"shown to transfer(?![^\n]{0,12}\bnot\b)"),
    # ---- C-12 (2026-08-21): the SECOND estimand switch inside the §14-D cell. The cell corrected
    # d_context's pooled "exactly 0.0000" to the clustered +0.0045, and then its own closing sentence
    # re-asserted the pooled zero three sentences later -- next to "+0.0425", which is in NO artifact
    # (pooled 0.0422, clustered 0.0305; 0.0425 traces to a superseded L8 table). A correction that
    # leaves the same claim standing elsewhere in the same cell is the two-deliverables bug at
    # paragraph scale, so it gets a pattern rather than a one-time edit.
    ("C12 the +0.0425 / +0.0000 specificity pair",
     r"\+?0\.0425[^\n]{0,40}\+?0\.0000|"
     r"\+?0\.0000[^\n]{0,40}\+?0\.0425|"
     # MATCH THE WORD "zero", NOT ONLY THE NUMERAL. The short update said `d_context` "moves ASR by
     # **zero**" and this pattern -- pinned to `exactly 0.0000` -- sailed past it for four days, in a
     # bullet that ALSO asserted R-26's retracted specificity claim. FOURTH narrowness failure in
     # this file, and the same root cause every time: I write the pattern against the phrasing in
     # front of me instead of the class of claim. Numeral OR word, and specificity phrasing too.
     r"`?d_context`?[^\n]{0,60}(?:exactly\s+)?\*{0,2}(?:0\.0000|zero)\b|"
     r"specific to this direction|"
     r"effect tracks the cosine"),
    # ---- R-25 (2026-08-21): the in-subspace null was never dose-matched. The NUMBERS are fine, so
    # the pattern must catch the INFERENCE, not a figure. Phrases that assert the null establishes
    # content/specificity, or that treat the four layers as independent replications.
    ("R25 in-subspace null read as establishing content",
     r"beats?[^\n]{0,40}(?:every|any) (?:other )?direction[^\n]{0,30}subspace|"
     r"exceeds all[^\n]{0,30}controls?[^\n]{0,40}(?:so|therefore|hence)|"
     r"replicated at (?:all )?four layers|"
     r"hard null[^\n]{0,40}(?:establish|prove|confirm)"),
    ("R11 Holm backstop stated without L1",
     r"only at \*{0,2}L4 and L31|holm_rejected[^\n]{0,40}only at L4"),
    # ---- 2026-08-19 SESSION 2. Added the same day they were declared, per the rule above.
    # R-13: the incremental-R2 table that gave refusalness 5 predictors against Boombness's 1. The
    # withdrawn NUMBERS are the four cells; the withdrawn CLAIM is "matched footing"/"done correctly"
    # attached to them, which is what actually misleads, since the numbers alone look unremarkable.
    # NARROWED 2026-08-19 (second time this has been needed -- see R-7). A BARE `0.144` matched a
    # bootstrap range in an unrelated R-18 paragraph. A retracted-figure pattern must carry enough
    # context to identify the CLAIM; matching a three-digit number alone guarantees false positives
    # in a document full of three-digit numbers, and a sweep that flags correct text gets ignored.
    ("R13 incremental R2 at unmatched df",
     r"(?:refusaln|Boombness)[^\n]{0,60}\+?0\.144|"
     r"\+?0\.144[^\n]{0,60}(?:refusaln|Boombness|over Boombness)|"
     r"\|\s*@ codeword_last\s*\|\s*\+?0\.028\s*\|"
     r"|increment comparison, done correctly"
     r"|Boombness is close to redundant"),
    # R-14: every external-set ASR judged against an empty goal. The withdrawn numbers are the
    # ClearHarm arm ASRs as first published; the withdrawn CLAIM is that the bank-artifact
    # explanation is excluded, which was the whole point of the arm.
    ("R14 ClearHarm ASR from an empty goal",
     r"0\.101\s*(?:→|->|to)\s*\*{0,2}0\.542|"
     r"ASR\s*0\.1006|\b0\.2067\b|\b0\.3408\b|\b0\.5419\b|"
     r"bank-artifact explanation is \*{0,2}excluded"),
    # R-15: "harmful yes, benign no" -- one significant cell of six. The claim pattern is the target;
    # the deltas themselves are NOT retracted (they reproduce exactly), only the reading of them.
    # R-17: the cross-model CAUSAL replication claim, made on pooled estimates and withdrawn when
    # Qwen3/AdvBench came back null against a 0.8% baseline. The Llama-only claim is live; only the
    # "both models" phrasing is retracted.
    # R-18: G2 as published. The retracted objects are the FIGURES and the claim; the clean-set
    # numbers (-0.0518, +0.0860) are live and must not be flagged.
    ("R18 G2 rho over the unfiltered 234-row set",
     r"\+0\.3067|\+?0\.2618|rho\s*=\s*\+?0\.307|"
     r"n\s*=\s*234[^\n]{0,40}(?:6/6 domains|p\s*<\s*5e-4)|"
     r"Boombness (?:modestly )?predicts (?:attack success|ASR)"),
    ("R17 cross-model d_surface replication",
     r"raises external-set ASR in \*{0,2}BOTH models|"
     r"cross-model replication of the .{0,20}d_surface.{0,20} causal effect|"
     r"the causal intervention[^\n]{0,30}does\b(?![^\n]{0,40}not)"),
    ("R15 harm-general profile as fact",
     r"harm-general, not\s*\n?doublespeak-specific|"
     r"wherever there is an\s*\n?>?\s*attack|"
     r"clean split|"
     r"[≈~]0 on every benign condition|"
     r"generalises across three attack types"),
]
#: file -> heading at which the LIVE region ends. Everything before it is swept; everything after is
#: treated as dated record. A file with no entry here is swept in full.
LIVE_PREFIX_ENDS_AT = {
    # BOOMBNESS_SPRINT_PROGRESS.md was excluded entirely as a "historical record". That is right for
    # its tick log and wrong for its HEAD: the phase board and the DECISION GATES are live status,
    # and the loop's standing instruction is to keep them current. The cost of the blanket exclusion
    # was measured on 2026-08-22 -- FOUR rows were found stale, two asserting the OPPOSITE of the
    # report (G2 read YES after R-18 retracted it; G4 read YES while report §0 said do not build).
    # They sat there for days because no guard covered the one part of that file a reader trusts.
    # Sweep the live prefix, leave the record alone.
    "docs/BOOMBNESS_SPRINT_PROGRESS.md": "## Bug / integrity audit log",
}

DELIVERABLES = [
    "reports/boombness_objective_sprint_report.md",
    "reports/boombness_objective_sprint_short_update.md",
    "docs/BOOMBNESS_SPRINT_PROGRESS.md",   # live prefix only -- see LIVE_PREFIX_ENDS_AT
    # ADDED 2026-08-23 (review finding S7). The d_surface next-phase log calls itself "the
    # authoritative live research log for this phase" and every result of that phase lives ONLY
    # there -- so until now the phase's entire output was invisible to every guard in this repo. A
    # retracted figure could resurface in it and nothing would notice, which is the exact defect
    # this sweep exists for, applied to the one file it did not cover.
    # Verified BEFORE wiring in, not after: a --paths dry-run over it reports 0 unqualified
    # occurrences, so this addition does not turn the build red on arrival.
    "external_md/BOOMBNESS_DSURFACE_NEXT_PHASE_PLAN_AND_PROGRESS.md",
    # NOT swept (2026-08-21): the two mid-session sanity checks are DATED SNAPSHOTS of what was
    # believed on 2026-08-17/18, superseded in full by the continuation log. Sweeping them flags the
    # historical record as a defect -- the same reason BOOMBNESS_SPRINT_PROGRESS.md is excluded.
    # They were in scope while they were current; they are not current.
    #   "docs/BOOMBNESS_MIDSESSION_SANITY_CHECK.md",
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
# ⛔ WORD BOUNDARIES ARE LOad-BEARING HERE (audit #10, 2026-08-22). `corrected` had no left boundary,
# so **UNCORRECTED** matched it -- the word that means "not corrected" DISARMED the guard. That is how
# the §14-B gate row kept asserting the retracted "≈16 band-sds" while the sweep reported clean: the
# row says its own p is "uncorrected", and that one word exempted the whole block. Same hazard for
# `corrected` inside `uncorrected`/`incorrected`, and for bare `was` inside `washed`/`wasted`.
#
# This is the file's OWN documented failure mode ("a 17-line table hid four retracted headlines behind
# one word") recurring through a regex detail rather than through block scoping.
# ⛔ WEAK MARKERS WHITELISTED A THIRD OF EVERY DOCUMENT (audit #11, 2026-08-22). `MARKER` exempts a
# whole block, and it used to accept `was`, `rather than`, `earlier`, `previously`, `instead of`,
# `corrected` and `revision N` -- ordinary English, not retraction vocabulary. Measured on the real
# documents: 29-31% of blocks were exempt, and 13-14% on a WEAK marker alone (`was` 78x in the report,
# `rather than` 40x).
#
# The live cost was report §0's paragraph asserting the RETRACTED -0.0062 control and the RETRACTED
# specificity conclusion as fact. `retraction_sweep`'s own C-12 pattern matched it; the block was
# exempted because the sentence happened to contain "rather than".
#
# Now: only STRONG markers exempt -- vocabulary that cannot appear by accident in a live claim. This
# is the third narrowing of this mechanism (bare `0.070`, then `corrected` inside `uncorrected`, now
# the weak set) and the first that removes a whole class rather than patching one word.
# Kept: vocabulary that marks a claim as dead. Dropped: `was`, `rather than`, `instead of`, and bare
# `earlier`/`previously`/`revision N` -- ordinary English that appears inside live claims. `corrected`
# stays (with the left-boundary guard, so "uncorrected" does not match) because a registry row reading
# "**CORRECTED** to L1, L4 and L31" is a genuine marker; a first pass that dropped it flagged 26
# legitimate correction paragraphs, which is how I learned the line sits between "weak" and "strong"
# rather than between "long" and "short".
MARKER = re.compile(
    r"retract|withdraw|supersed|⛔|~~|struck|fake|not reportable|no longer|"
    r"(?<![a-z])corrected|\bwrong\b|"
    r"previously (?:said|read|quoted|stated)|earlier (?:revision|draft|version)|an earlier", re.I)


def sweep(paths):
    bad = []
    for f in paths:
        try:
            text = open(f, encoding="utf-8").read()
        except OSError:
            continue
        stop = LIVE_PREFIX_ENDS_AT.get(f)
        if stop:
            # ⛔ `text.index(stop)` took the FIRST occurrence anywhere, including inside prose or a
            # table cell (audit #11). One line above the boundary mentioning the heading by name would
            # silently collapse the live prefix to a few lines and the guard would still print "clean".
            # BOOMBNESS_SPRINT_PROGRESS.md already contains that exact string inside a table cell.
            # Require a real HEADING, and refuse to run on an implausibly short prefix rather than
            # passing vacuously.
            m2 = re.search(r"^" + re.escape(stop) + r"\s*$", text, re.M)
            if m2:
                prefix = text[:m2.start()]
                if prefix.count("\n") < 20:
                    print(f"[sweep] REFUSING to sweep {f}: the live prefix collapsed to "
                          f"{prefix.count(chr(10))} lines -- the boundary heading "
                          f"{stop!r} was matched too early. Fix the boundary, do not trust this run.",
                          file=sys.stderr)
                    return [(f, 0, "live-prefix collapsed", "boundary matched too early")]
                text = prefix
        # BLOCKS ARE BLANK-LINE PARAGRAPHS, EXCEPT THAT EVERY TABLE ROW **AND EVERY LIST ITEM** IS
        # ITS OWN BLOCK. List items were added 2026-08-22 (audit #11): a run of bullets with no blank
        # line between them is one block, so ONE bullet saying "was" whitelisted all of its siblings --
        # the table-row bug recurring verbatim in a construct nobody had scoped.
        #
        # WHY (audit 2026-08-21, and it is the worst miss this checker has had). The exemption is
        # paragraph-scoped: a block containing any MARKER word is treated as marking its own
        # retraction. A markdown TABLE is one blank-line-delimited block, so the §13 "scored
        # honestly" table -- 17 lines, six criteria -- was whitelisted in its entirety because ONE
        # cell contained the word "was". Inside that whitelist sat FOUR retracted headlines: G2's
        # rho=+0.307 (R-18), arm F's 0.243->0.548 (R-20), comprehension p=0.681 (R-6) and "the §18
        # label is B" (R-9). The sweep reported "clean". The module docstring has warned since
        # 2026-08-18 that the marker exemption is "a heuristic, not a proof"; this is that heuristic
        # failing at the largest possible scale, because the bigger the table the more likely some
        # cell contains an innocuous "was".
        #
        # A table row is a self-contained assertion and is now scoped as one. A row that states a
        # retracted figure must therefore mark it IN THAT ROW, which is also what a reader scanning
        # a table needs.
        line_no, para, start = 1, [], 1
        blocks = []

        def _flush():
            nonlocal para
            if para:
                blocks.append((start, "\n".join(para)))
                para = []

        for line in text.split("\n"):
            stripped = line.strip()
            if stripped.startswith("|"):
                _flush()
                blocks.append((line_no, line))     # each table row stands alone
                start = line_no + 1
            elif re.match(r"^(?:[-*+]|\d+[.)])\s", stripped):
                # each LIST ITEM stands alone too -- see the block comment above. A bullet run has no
                # blank lines, so without this one sibling's marker exempted the whole run.
                _flush()
                blocks.append((line_no, line))
                start = line_no + 1
            elif stripped == "":
                _flush()
                start = line_no + 1
            else:
                if not para:
                    start = line_no
                para.append(line)
            line_no += 1
        _flush()
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



def registry_check(path):
    """Every retraction ID CITED in the body must have a ROW in the registry table.

    WHY (2026-08-21). The table listed R-6..R-11 while the body cited R-12, R-13, R-16, R-17, R-18 and
    R-19 more than 300 times between them, and the header still said "5 retractions, 5 corrections".
    Anyone looking for the next free ID reads the TABLE -- which is how this session filed two new
    retractions as R-14/R-15 when both were already taken by defects the body had been discussing for
    days. The collision was the symptom; an unverifiable registry was the cause, and a registry nobody
    can check is not a registry.

    A row is `| R-N |` or `| **R-N** |` at the start of a line; anything else mentioning R-N is a
    citation. Returns a list of problems, empty when the table is complete.
    """
    text = open(path, encoding="utf-8").read()
    tabled, cited = set(), set()
    for line in text.split("\n"):
        # A row label may cover a RANGE ("| R-1 … R-5 |"), which tables every id in it. Without
        # this, closing the registry with a range row leaves the checker reporting the very ids the
        # row exists to cover.
        # C-SERIES TOO (audit #11, 2026-08-22). Nine C-ids were cited in this report and NOT ONE had
        # a registry row -- the same unverifiable state that produced the R-14/R-15 collision, in the
        # series nobody had checked. Both series are now covered by the same code.
        m = re.match(r"\s*\|\s*\*{0,2}([RC]-\d+)\*{0,2}\s*(?:[.…]{1,3}|-|to)\s*\*{0,2}([RC]-\d+)\*{0,2}\s*\|", line)
        if m:
            pfx = m.group(1).split("-")[0]
            for i in range(int(m.group(1).split("-")[1]), int(m.group(2).split("-")[1]) + 1):
                tabled.add(f"{pfx}-{i}")
            continue
        m = re.match(r"\s*\|\s*\*{0,2}([RC]-\d+)\*{0,2}\s*\|", line)
        if m:
            tabled.add(m.group(1))
            continue
        cited.update(re.findall(r"\b[RC]-\d+\b", line))
    key = lambda x: (x.split("-")[0], int(x.split("-")[1]))
    problems = [f"{r} is cited in the body but has NO ROW in the registry table"
                for r in sorted(cited - tabled, key=key)]

    # MEANING COLLISION. Having a row does not mean the citations are about the SAME THING. R-8 was
    # cited for BOTH G1's "+84% of span" supersession AND arm F's "capability channel" -- two
    # retractions, one ID, in one document -- and the has-a-row check passed it, because it verifies
    # existence and not identity. Detect it mechanically: collect the QUOTED gloss that follows each
    # citation, and flag an ID carrying two or more distinct ones. Quoted glosses are the convention
    # this report already uses ("R-8, the \"capability channel\""), so this is low-noise, and it is
    # deliberately conservative -- it cannot catch an ID whose two meanings are both unquoted.
    glosses = {}
    for m in re.finditer(r"\b(R-\d+)\b([^\n]{0,80})", text):
        rid, tail = m.group(1), m.group(2)
        for q in re.findall(r"[\"\u201c]([^\"\u201d\n]{6,60})[\"\u201d]", tail):
            glosses.setdefault(rid, set()).add(re.sub(r"\s+", " ", q).strip().lower())
    # Merge glosses that are the same meaning worded differently: "+84% of span" and
    # "+84% of span, CI [...]" are one figure quoted at two lengths, not two retractions.
    advisories = []
    for rid, gs in sorted(glosses.items(), key=lambda kv: key(kv[0])):
        merged = []
        for g in sorted(gs, key=len, reverse=True):
            if not any(g in m or m in g for m in merged):
                merged.append(g)
        if len(merged) > 1:
            advisories.append(f"{rid} is cited with {len(merged)} distinct quoted glosses "
                              f"{merged[:3]} -- check they are one retraction, not two")
    return problems, advisories
    # A tabled-but-uncited ID is NOT a defect -- the table IS the record, and a retraction whose
    # claim was excised entirely will correctly have no other mention. Only the reverse direction
    # breaks the registry, so only that direction fails the check.

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

    # SECOND CHECK: is the registry itself complete? See registry_check for what this cost.
    reg, adv = registry_check(DELIVERABLES[0])
    if adv:
        print(f"\n[sweep] registry ADVISORY ({len(adv)}) — heuristic, does not fail the build:")
        for a in adv:
            print(f"   {a}")
        print("[sweep] this is a HEURISTIC and is advisory on purpose. Over-trusting a heuristic is "
              "exactly what let a 17-line table hide four retracted headlines behind one word; a "
              "fuzzy check made fatal would train the next reader to ignore it.")
    if reg:
        print(f"\n[sweep] REGISTRY: {len(reg)} problem(s) in {os.path.basename(DELIVERABLES[0])}")
        for r in reg:
            print(f"   {r}")
        print("[sweep] a retraction ID that is cited but not tabled makes the table unusable for "
              "picking the next free ID — which is exactly how R-14/R-15 were assigned twice.")
    else:
        print("[sweep] registry OK — every cited retraction ID has a row in the table")
    return 1 if (bad or reg) else 0


if __name__ == "__main__":
    raise SystemExit(main())
