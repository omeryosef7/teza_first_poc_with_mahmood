"""Every statement of button's L18 failure must name its SPLIT.

PR-CSI-007's decision branch, fired at R47 = 6, obliges: "Every sentence in the sprint that states
button's L18 failure without naming the split is amended to name it." The obligation exists because
the TRAIN and VALIDATION cells of that claim are now DIFFERENT -- rank 36 of 47 on TRAIN, rank 6 of 47
on held-out, with non-overlapping exceedance CIs -- so an unqualified "button's L18 failure" no longer
picks out a single fact.

This checker keeps that true going forward. It flags any line asserting button + L18 + a failure word
without naming TRAIN / VALIDATION / held-out nearby.

The sprint log is APPEND-ONLY, so three pre-existing lines cannot be edited. They are listed in
AMENDED_BY_RESTATEMENT with the amended wording recorded in S-165, which is how an append-only record
discharges an amendment obligation. Exit 1 on anything NOT on that list -- so the exemption is a
ledger of history, never a licence for new text.
"""
import re, sys, os

REPO = "/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
os.chdir(REPO)
LOG = "external_md/DCS_CAUSAL_SEMANTIC_INSTALLATION_MECHANISM_AND_REPLICATION_PLAN_AND_PROGRESS_20260915.md"
TABLE = "reports/DCS_CSI_CLAIM_TABLE.md"

# Pre-existing, in the append-only log, amended by restatement in S-165 rather than by edit.
# Keyed by (LINE NUMBER, stripped text). REVIEW R13 found the text-only key FAIL-OPEN: a NEW entry
# that re-quotes S-137's table row would have been auto-exempted, so the checker built to stop
# unqualified claims would not have stopped the likeliest one. The line number is the right second
# key HERE and would be wrong almost anywhere else: THE LOG IS APPEND-ONLY, so the line numbers of
# existing content are immutable. Both must match, and the staleness check asserts the pair still
# holds -- a key that no longer sits at its line is a FAILURE, not a silent re-exemption.
AMENDED_BY_RESTATEMENT = {
    (6208, '- We may say *"button\'s failure is not explained by its layer."* \u2705'):
        "S-104 context: the L18-vs-L20 layer swap, 10-control family, floor 0.0909, TRAIN only. "
        "Amended form in S-165.",
    (6211, "excluded by this entry; it is only excluded for button, which is the codeword that fails."):
        "Same S-104 context; subordinate clause. Amended form in S-165.",
    (10176, "| **button @ L18, 46 controls** | **36 of 47** | 0.766 | 0.0213 | **DOES NOT PASS**, certified |"):
        "S-137's dissociation table. The basket row beside it already named its splits "
        "('TRAIN *and* VALIDATION') while this one did not, which hid the asymmetry from a reader "
        "scanning the table. Amended form in S-165.",
}

BUTTON = re.compile(r"button", re.I)
FAIL = re.compile(r"does not pass|fails?\b|failure|certifiable|certified|rank 36|36 of 47|floor-limited", re.I)
L18 = re.compile(r"L18|layer 18", re.I)
SPLIT = re.compile(r"TRAIN|VALIDATION|held-out|heldout|both splits", re.I)
# Lines that QUOTE the obligation, describe this checker, or quote a deliberately-unqualified
# example are not ASSERTIONS of the claim. Found the hard way: appending S-165 -- the entry that
# discharges the obligation -- made this checker fail on its own prose, twice. A checker that
# scans prose will always flag prose ABOUT the checker, so the meta vocabulary is named here
# rather than left to chance. It is deliberately NARROW: each token describes talking about the
# claim, never making it. D90-D99 are RESERVED as mutation-test sentinels and are never real
# claim-table rows, so quoting one is always talk about the check (found by using D98 after
# META already knew D99 -- chasing sentinels one at a time is the wrong fix).
META = re.compile(r"without naming the split|amended to name it|AMENDED_BY_RESTATEMENT|split_naming|a failure word|Mutation-tested|unqualified|\bD9[0-9]\b|^\s*original:|^\s*amended  ", re.I)
W = 3


def scan(path, window=True):
    lines = open(path, encoding="utf-8").read().splitlines()
    n = len(lines)
    out = []
    for i, l in enumerate(lines):
        if not (BUTTON.search(l) and FAIL.search(l)):
            continue
        if META.search(l):
            continue
        # STRUCTURAL RULE, and the one that should have been written first: text inside backticks is a
        # QUOTATION, not an assertion. Three rounds of sentinel whack-a-mole (D99, then D98, then D31)
        # all had the same shape -- the entry documenting this checker quotes rows it must not assert --
        # and every one of those quotations was inside inline code, while the real offender L10176 is a
        # RAW table row that is not. Strip code spans first and the whole class disappears.
        bare = re.sub(r"`[^`]*`", " ", l)
        if not (BUTTON.search(bare) and FAIL.search(bare)):
            continue
        # A TABLE ROW is quoted on its own, so a split named three lines away does not travel with
        # it. That is exactly how L10176 read: the basket row beside it named "TRAIN *and*
        # VALIDATION" while the button row named nothing, and the windowed test called that
        # compliant. Rows are judged on their OWN text.
        is_row = l.lstrip().startswith("|")
        ctx = "\n".join(lines[max(0, i - W):min(n, i + W + 1)]) if (window and not is_row) else l
        if not L18.search(ctx) and not (is_row and L18.search(l)):
            continue
        if SPLIT.search(ctx):
            continue
        out.append((i + 1, l.strip()))
    return len(lines), out


def main():
    fail = []
    nl, log_hits = scan(LOG)
    nt, tab_hits = scan(TABLE, window=False)
    print("[split-naming] SIZE  log %d lines | claim table %d lines" % (nl, nt))
    if nl == 0 or nt == 0:
        sys.exit("VACUOUS: a file scanned to 0 lines -- refusing to report a pass")

    print("[split-naming] log hits %d | claim-table hits %d" % (len(log_hits), len(tab_hits)))
    for ln, txt in log_hits:
        if (ln, txt) in AMENDED_BY_RESTATEMENT:
            print("   exempt (append-only, amended in S-165)  L%-6d %s" % (ln, txt[:90]))
        else:
            fail.append("%s:%d states button's L18 failure without naming the split: %s" % (LOG, ln, txt[:140]))
    for ln, txt in tab_hits:
        fail.append("%s:%d states button's L18 failure without naming the split: %s" % (TABLE, ln, txt[:140]))

    # the exemption ledger must not rot: every key must still be present in the log
    loglines = open(LOG, encoding="utf-8").read().splitlines()
    for (kln, ktxt) in AMENDED_BY_RESTATEMENT:
        got = loglines[kln - 1].strip() if kln <= len(loglines) else "<past EOF>"
        if got != ktxt:
            fail.append("AMENDED_BY_RESTATEMENT key (%d, %r) NO LONGER MATCHES the log at that line "
                        "(found %r). The log is append-only, so an existing line cannot move: this "
                        "means the key is wrong." % (kln, ktxt[:60], got[:70]))
    print("[split-naming] exemption ledger: %d (line, text) pairs, all still matching the log" % len(AMENDED_BY_RESTATEMENT))

    if fail:
        print("\nSPLIT-NAMING FAILURES:")
        for f in fail:
            print("   -", f)
        sys.exit(1)
    print("\nPASS -- every button/L18 failure statement names its split, or is a documented pre-existing line")


if __name__ == "__main__":
    main()
