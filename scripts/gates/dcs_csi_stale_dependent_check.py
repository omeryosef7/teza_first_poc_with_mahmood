#!/usr/bin/env python3
"""Find text that still asserts what a STRUCK span retracted.

S-527 found two instances of one defect class by hand: prohibition 28 was amended,
and places depending on it went on describing the pre-amendment world. This is the
instrument for that class.

THE IDEA. In these documents a retraction is written `~~old claim~~` followed by a
marker. So the struck spans are the corpus of superseded CLAIMS. A distinctive token
appearing inside a struck span AND outside every struck span is a candidate stale
dependent: something the record retracted in one place and may still assert in another.

*** THE FALSE PREMISE THIS TOOL SHIPPED WITH, CORRECTED S-528 BEFORE ANY HIT WAS ACTED ON ***
The first version of this docstring called the struck tokens "retracted numeric
tokens". THAT IS WRONG, and the error matters more than the tool. A number inside a
struck span means THE SENTENCE WAS RETRACTED, *not* that the number was. Most numbers
survive the claim that carried them: a family is extended and the old floor becomes
correct history; a claim is rescoped and its measurement stays valid for the narrower
scope; a wrong DENOMINATOR is fixed while the numerator is untouched. On this corpus
the first run produced 82 "bare" hits and the overwhelming majority were of exactly
this kind. Read that number as the tool's PRECISION, not as a defect count.

So this is a READING AID, not a detector of errors. What it actually locates is: places
where a retracted claim and a live claim share a figure, which is where a reader must
look to decide whether the live one inherited the retraction. The decision is human
and per-occurrence; nothing here can make it.

WHAT THIS IS NOT. Not a verdict. A token legitimately appears unstruck in the
correction note that supersedes it, in a provenance citation, as the governing value
for a different family or population, or as a different quantity sharing digits (S-482
matched `4.209` against `4`+any+`209`; S-492's 0.190474 was a real value I had wrongly
dismissed). Every hit must be read before it is believed. Exit 0 always: a detector
that cannot fail cannot be trusted to gate, and this one is explicitly advisory.

DESIGN NOTES, each earned:
  - Numeric tokens only, >= MIN_SIG significant digits. Short integers ("3", "28")
    collide constantly and drown the signal.
  - Tokens are matched with escaped dots and digit boundaries, so `0.0778` cannot
    match inside `0.07781` and `4.209` cannot match `4x209` (S-482).
  - The struck-span model is explicit and tested below, because getting "inside a
    struck span" wrong silently inverts the whole result.
"""
import argparse, os, re, sys

MIN_SIG = 3
NUM = re.compile(r'(?<![\d.])\d+\.\d+(?:[eE][-+]?\d+)?(?![\d])')

def struck_spans(text):
    """[(start, end)] of ~~...~~ regions. Unpaired trailing ~~ opens nothing."""
    out, i = [], 0
    while True:
        a = text.find("~~", i)
        if a < 0: return out
        b = text.find("~~", a + 2)
        if b < 0: return out          # unpaired: not a span
        out.append((a, b + 2)); i = b + 2

def inside(spans, pos):
    return any(a <= pos < b for a, b in spans)

def sig_digits(tok):
    return len(tok.replace(".", "").replace("-", "").lstrip("0")) or 1

def selftest():
    """The detector's own correctness, checked before it reports anything."""
    t = "alpha ~~old 0.0778 here~~ new 0.0803 and 0.0778 again"
    sp = struck_spans(t)
    assert len(sp) == 1, sp
    assert inside(sp, t.index("old")), "struck text not detected as struck"
    assert not inside(sp, t.rindex("0.0778")), "unstruck text reported as struck"
    assert not inside(sp, t.index("alpha")), "text before the span reported as struck"
    # unpaired marker must not swallow the tail
    assert struck_spans("a ~~b") == [], "unpaired ~~ opened a span"
    # digit-boundary: 0.0778 must not match inside 0.07781
    assert not re.search(r'(?<![\d.])0\.0778(?![\d])', "x 0.07781 y")
    assert re.search(r'(?<![\d.])0\.0778(?![\d])', "x 0.0778 y")
    assert sig_digits("0.0778") == 3 and sig_digits("0.1146") == 4
    # PINS THE S-528 FALSE PREMISE: a number can sit in a struck span and remain
    # correct outside it. This case MUST be reported as a hit (it is a reading aid)
    # and MUST NOT be described as a retracted number.
    survivor = "~~the floor is 0.1111 so this is INCONCLUSIVE~~ the floor 0.1111 is now history"
    sp2 = struck_spans(survivor)
    live = [m.start() for m in re.finditer(r'(?<![\d.])0\.1111(?![\d])', survivor)
            if not inside(sp2, m.start())]
    assert len(live) == 1, "the surviving-number case must still be surfaced"
    return True

def count_mode(files, tokens, context=0):
    """Count a literal the way this file has always counted, and the way ad-hoc greps do not.

    ADDED S-546. The detector below has used digit-bounded matching since it was written, and
    S-528's figures reproduce exactly against it. The error this mode exists to prevent was never
    in the instrument -- it was in reaching PAST the instrument for a bare `grep -o`, which matches
    INSIDE longer numbers. S-544 counted `0.0778` that way and reported "at least 24 files"; the
    bounded count is 51 occurrences in 7, because these artefacts are full of per-domain floats
    like 0.07786075415465653. That is the S-482 error committed a second time, in the very entry
    whose subject was an uncounted number.

    Measured phantom rates over the three primary documents, loose minus bounded:
        0.0014   67 %      0.00400  38 %      0.0323   30 %      0.0778   11 %
        0.1111    5 %      0.0400    5 %      1/31      5 %      0.0213    1 %
        0.0769, 0.201, 0.888, 0.10306, 0.12131, 0.00852, 1/35 -- all 0 %
    A token's phantom rate is not guessable from its shape, which is the argument for never
    eyeballing it: `0.0014` is 67 % phantom and `0.00852` is 0 %.

    Prints BOTH counts, always, so the gap is visible rather than silently corrected.
    """
    for tok in tokens:
        esc = re.escape(tok)
        loose = re.compile(esc)
        bound = re.compile(r'(?<![\d.])' + esc + r'(?![\d])')
        tl = tb = 0
        rows = []
        for f in files:
            t = open(f, encoding="utf-8", errors="ignore").read()
            spans = struck_spans(t)
            L = len(loose.findall(t))
            B = [m for m in bound.finditer(t)]
            live = [m for m in B if not inside(spans, m.start())]
            tl += L; tb += len(B)
            if L or B:
                rows.append((f, L, len(B), len(live)))
        print("\n[count] %r  loose=%d  BOUNDED=%d  phantom=%d%s"
              % (tok, tl, tb, tl - tb,
                 "  <== %d%% of the loose count is INSIDE longer numbers" % round(100.0 * (tl - tb) / tl)
                 if tl and tl != tb else ""))
        for f, L, B, live in rows:
            print("    %-58s loose %-5d bounded %-5d live(unstruck) %d"
                  % (os.path.basename(f), L, B, live))
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--count", metavar="TOKEN", action="append", default=None,
                    help="Count this literal across the files with DIGIT BOUNDARIES, and print the "
                         "unbounded count beside it. Repeatable. Use this instead of `grep -o` for "
                         "any number: a bare grep matches inside longer numbers and has produced a "
                         "wrong committed figure twice (S-482, S-544).")
    ap.add_argument("--min-sig", type=int, default=MIN_SIG)
    ap.add_argument("--context", type=int, default=90)
    a = ap.parse_args()
    selftest()
    print("[stale-dep] self-test PASSED")
    if a.count:
        return count_mode(a.files, a.count, a.context)

    docs = {f: open(f).read() for f in a.files}
    spans = {f: struck_spans(t) for f, t in docs.items()}

    # corpus of retracted numeric tokens, with where each was struck
    in_retracted = {}
    for f, t in docs.items():
        for m in NUM.finditer(t):
            if inside(spans[f], m.start()) and sig_digits(m.group()) >= a.min_sig:
                in_retracted.setdefault(m.group(), set()).add(f)
    print("[stale-dep] %d distinct numeric token(s) appearing in RETRACTED TEXT, across %d file(s)"
          % (len(in_retracted), len(docs)))

    hits = 0
    for tok in sorted(in_retracted, key=lambda x: -sig_digits(x)):
        pat = re.compile(r'(?<![\d.])' + re.escape(tok) + r'(?![\d])')
        live = []
        for f, t in docs.items():
            for m in pat.finditer(t):
                if not inside(spans[f], m.start()):
                    ln = t.count("\n", 0, m.start()) + 1
                    s = max(0, m.start() - a.context); e = m.end() + a.context
                    live.append((f, ln, " ".join(t[s:e].split())))
        if live:
            hits += 1
            print("\n  IN-RETRACTED-TEXT %s  (struck in: %s)  -- %d live occurrence(s)"
                  % (tok, ", ".join(sorted(x.split('/')[-1] for x in in_retracted[tok])), len(live)))
            for f, ln, ctx in live[:6]:
                print("      %s:%d  ...%s..." % (f.split('/')[-1], ln, ctx))
            if len(live) > 6:
                print("      (+%d more)" % (len(live) - 6))

    print("\n[stale-dep] %d token(s) from retracted text also appear unstruck somewhere." % hits)
    print("[stale-dep] Most such hits are LEGITIMATE (the number outlived the retracted claim).")
    print("[stale-dep] ADVISORY ONLY -- every hit must be read. Exit 0 by design.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
