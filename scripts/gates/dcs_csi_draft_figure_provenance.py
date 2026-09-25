#!/usr/bin/env python
"""Every figure in the results draft must be traceable to a SOURCE, or be allow-listed with a reason.

WHY THIS EXISTS. The draft's figure check began as "does this number appear in the claim table".
That was right while the draft only restated claim-table rows. It is no longer: the draft now cites
ARTEFACT FIELDS (`4.9999750001249995e-06`), CODE COMMENTS (`1.4999999999999998`) and MY OWN
DERIVATIONS (`1.355e-20` = 2/2**67). S-430 measured six such figures and the old check called all
six unaccounted -- a detector that reports false positives is the failure mode this sprint has hit
five times (S-422 md5-vs-git-blob, S-423 prereg-id, S-425 .jsonl truncation, S-426 limit:0 and the
donor/positions grouping). Each was caught only by reading the underlying values by hand.

So the check is widened to the sources the draft actually cites, and what it CANNOT do is stated
rather than implied.

⚠ WHAT THIS CANNOT DO, and none of it is hypothetical:
  * It proves a figure EXISTS in some source. It does NOT prove the draft uses it CORRECTLY -- a
    number attached to the wrong family, split or codeword passes here. S-428's "on button the
    ceiling is K = 2" was a correct figure with a missing antecedent and would pass.
  * A short figure can appear in a source BY COINCIDENCE. `0.0778` would match any file containing
    it for any reason. Longer figures are effectively unique; short ones are weak evidence.
  * It reads only the figures its regex finds: decimals with >= 3 fractional digits, scientific
    notation, and n/m fractions. Small integers -- the class that produced the 70-vs-67 error in
    S-417 -- are INVISIBLE to it, and that error is exactly why this docstring says so.
  * The ALLOWLIST is an assertion by the author, not a check. It is where an unverified number
    would hide, so each entry carries a reason and the test asserts the reasons are non-empty.
"""
import argparse, glob, os, re, sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FIG = re.compile(r'(?<![\w.])(\d+\.\d{3,}(?:e-?\d+)?|\d+\.?\d*e-\d+|\d{3,}/\d{4,})')

# figures the draft DERIVES or reads from a place no corpus file holds. Each needs a reason.
ALLOWLIST = {
    "1.355e-20": "2/2**67, the exact sign-flip floor; computed in S-430, held by no file",
    "0.99999":   "the p of a constructed M=0 read, from executing decide() in S-421",
    "1.1e-16":   "max |softmax - sigmoid(logodds)| over 670 rows, measured in S-427",
}

def sources():
    out = {}
    for p in (["reports/DCS_CSI_CLAIM_TABLE.md"]
              + sorted(glob.glob("configs/dcs_csi_pr*.json"))
              + sorted(glob.glob("runargs/dcs_csi_pr*_read.txt"))
              + sorted(glob.glob("reports/DCS_CSI_*.json"))
              + sorted(glob.glob("scripts/dcs_csi_*.py"))
              + sorted(glob.glob("scripts/gates/dcs_csi_*.py"))):
        f = os.path.join(REPO, p)
        if os.path.isfile(f):
            try:
                out[p] = open(f, encoding="utf-8", errors="ignore").read()
            except OSError:
                pass
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--draft", default="reports/DCS_CSI_RESULTS_DRAFT.md")
    ap.add_argument("--strict", action="store_true",
                    help="exit 1 if any figure is unaccounted (default: report only)")
    a = ap.parse_args()
    text = open(os.path.join(REPO, a.draft), encoding="utf-8").read()
    # the editor's checklist quotes FORBIDDEN figures on purpose; it is not a claim surface
    body = text.split("## Editor's checklist")[0] + text.split("# M. Methods")[-1]
    figs = sorted({m.group(1) for m in FIG.finditer(body)})
    src = sources()
    print("draft %s -- %d distinct figures, %d source files" % (a.draft, len(figs), len(src)))
    print("=" * 96)
    bad = []
    for f in figs:
        if f in ALLOWLIST:
            print("  %-26s ALLOWLISTED  %s" % (f, ALLOWLIST[f]))
            continue
        hit = [p for p, t in src.items() if f in t]
        if not hit:
            bad.append(f)
            print("  %-26s *** UNACCOUNTED ***" % f)
        else:
            # prefer the AUTHORITATIVE source when several match, rather than the first
            # alphabetically -- `1.36e-20` matched an unrelated 2025 report before this.
            pref = ([p for p in hit if "CLAIM_TABLE" in p]
                    or [p for p in hit if p.startswith(("configs/", "runargs/"))]
                    or [p for p in hit if p.startswith("reports/")]
                    or hit)
            kind = ("claim table" if "CLAIM_TABLE" in pref[0]
                    else "prereg/read" if pref[0].startswith(("configs/", "runargs/"))
                    else "artefact" if pref[0].startswith("reports/") else "code")
            # ⚠ a figure present in MANY files is probably there by coincidence in most of them, so
            # "it exists somewhere" is weak evidence. Short figures are the ones this bites.
            weak = "  ⚠ in %d files -- existence is WEAK evidence here" % len(hit) if len(hit) > 8 else (
                   "  (+%d more)" % (len(hit) - 1) if len(hit) > 1 else "")
            print("  %-26s %-12s %s%s" % (f, kind, pref[0], weak))
    print("=" * 96)
    print("unaccounted: %d" % len(bad))
    if bad:
        print("  %s" % ", ".join(bad))
        print("  Each must be traced to a source or added to ALLOWLIST WITH A REASON.")
    print("⚠ Existence is not correctness: this cannot see a right number attached to the wrong "
          "family, and it cannot see small integers at all.")
    if bad and a.strict:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
