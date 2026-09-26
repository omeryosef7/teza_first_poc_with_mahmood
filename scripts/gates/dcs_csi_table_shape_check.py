#!/usr/bin/env python3
"""Check every markdown table row against ITS OWN table's header. (S-521)

WHY THIS EXISTS. These documents mix tables of 3, 4, 5 and 6 columns, and five separate
formatting defects were introduced into them in one day -- malformed rows, an unescaped
absolute-value bar, a duplicated marker, an unpaired strikethrough. Every one was caught by a
mechanical count and none by re-reading. But three ad-hoc detectors I wrote were themselves
wrong (S-508, S-521), each producing a large false count that looked like a finding:

  (a) `awk -F'|'` counts RAW pipes and cannot see markdown escapes, so `\\|` reads as a column break;
  (b) "the first pipe-row after a blank line is the header" mis-assigns headers when prose
      separates tables -- it once reported a header with 979 columns;
  (c) "nearest preceding separator" counts each NEW table's header as a row of the PREVIOUS
      table, because a header precedes its own separator. That produced "24 disagreeing rows",
      all of them headers.

THIS FILE IS THE CORRECTED DETECTOR, so the next person does not write a fourth wrong one:
  * a pipe preceded by a backslash is CONTENT, not a delimiter;
  * a line is a HEADER iff the NEXT line is a separator -- it is never a row;
  * a row belongs to the table of the most recent header, and only rows are compared.

⛔ NON-VACUITY: refuses if it finds no tables at all, so "0 bad rows" can never mean "I parsed
   nothing" (S-134/S-480's theme, applied to this checker).
"""
import re, sys

SEP = re.compile(r'^\|[\s\-:]*\|[\s\-:|]*$')

def cols(line):
    raw = len(re.findall(r'(?<!\\)\|', line))
    s = line.strip()
    return raw - 1 if s.startswith('|') and s.endswith('|') else raw

def check(path):
    lines = open(path, encoding="utf-8").read().split("\n")
    n = len(lines)
    header = None
    tables = 0
    bad = []
    for i, l in enumerate(lines):
        if not l.lstrip().startswith("|"):
            header = None
            continue
        if SEP.match(l):
            continue
        nxt = lines[i + 1] if i + 1 < n else ""
        if SEP.match(nxt):                      # this line is a HEADER, not a row
            header = (i + 1, cols(l)); tables += 1
            continue
        if header is None:                      # a pipe line with no header above it
            continue
        c = cols(l)
        if c != header[1]:
            bad.append((i + 1, c, header[0], header[1], l[:60]))
    return tables, bad

def main():
    paths = sys.argv[1:]
    if not paths:
        sys.exit("usage: dcs_csi_table_shape_check.py <file.md> [...]")
    total_tables = 0
    rc = 0
    for p in paths:
        t, bad = check(p)
        total_tables += t
        print("%s: %d tables, %d malformed row(s)" % (p, t, len(bad)))
        for ln, c, hl, hc, txt in bad:
            print("   line %-5d cols=%-3d  header(line %d)=%-3d  %s" % (ln, c, hl, hc, txt))
            rc = 1
    if total_tables == 0:
        sys.exit("REFUSING: parsed ZERO tables across %d file(s). A checker that inspected "
                 "nothing must not report success." % len(paths))
    return rc

if __name__ == "__main__":
    sys.exit(main())
