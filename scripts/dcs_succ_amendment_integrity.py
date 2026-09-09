#!/usr/bin/env python3
"""Does an AMENDMENT really leave its parent's clauses alone? A machine check, as a SCRIPT.

WHY THIS FILE EXISTS. `ENTRY 037` claimed *"a machine check asserting byte-identity across 13
blocks"* for `configs/dcs_ts_pr066_amendment1.json`. `REVIEW-2` finding **C1** established that the
claim was false in three ways, and the first one is the one that matters: **the check was run inline
in a throwaway shell heredoc and exists nowhere.** It could not be re-run, so it could not be
wrong in public. That is the same shape as `C-134` (a constant printed as a measurement) and `D-007`
(a grep matching a pre-existing string): a check whose failure mode is invisible.

It also missed real drift, because I hand-wrote `pre_extraction_checklist` in the amendment instead
of copying the parent's, so X1 lost its arithmetic (*"1160 -> 1130 rows over 113 domains at dose 4;
232 -> 226 at dose 0, per cell"* became *"arithmetic verified"*), X2 lost the bank name, X3 lost
*"from an existing, DIFFERENT-bank ASR artifact"* and X4 lost `.env`. None of that was itemised.

WHAT IT DOES. Diffs every top-level block of an amendment against its parent and classifies each as
IDENTICAL, ANNOTATED (identical once keys matching `--annotation-prefix` are stripped), DECLARED
(named in the amendment's own `_blocks_this_amendment_changes` with a reason) or **UNDECLARED DRIFT**.
Undeclared drift is a non-zero exit. It prints a unified diff for every drifted block so the change
is visible rather than summarised.

USAGE
  python scripts/dcs_succ_amendment_integrity.py --amendment configs/dcs_ts_pr066_amendment2.json
  python scripts/dcs_succ_amendment_integrity.py --selftest
"""
from __future__ import annotations

import argparse
import difflib
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def canon(o, prefixes):
    if isinstance(o, dict):
        return {k: canon(v, prefixes) for k, v in o.items()
                if not any(k.startswith(p) for p in prefixes)}
    if isinstance(o, list):
        return [canon(x, prefixes) for x in o]
    return o


def dump(o):
    return json.dumps(o, indent=1, sort_keys=True).splitlines()


def classify(par, am, prefixes, declared):
    rows = []
    for k in sorted(set(par) | set(am)):
        if k.startswith("_"):
            continue
        if k not in par:
            rows.append((k, "AMENDMENT-ONLY", ""))
            continue
        if k not in am:
            rows.append((k, "MISSING FROM AMENDMENT", "the analyzer would refuse on it"))
            continue
        if json.dumps(par[k], sort_keys=True) == json.dumps(am[k], sort_keys=True):
            rows.append((k, "IDENTICAL", ""))
        elif json.dumps(canon(par[k], prefixes), sort_keys=True) == \
                json.dumps(canon(am[k], prefixes), sort_keys=True):
            rows.append((k, "ANNOTATED", "identical once %s keys are stripped" % list(prefixes)))
        elif k in declared:
            rows.append((k, "DECLARED", declared[k]))
        else:
            rows.append((k, "UNDECLARED DRIFT", "not named in _blocks_this_amendment_changes"))
    return rows


def selftest() -> int:
    ok = True

    def chk(n, c):
        nonlocal ok
        print("  %-52s %s" % (n, "PASS" if c else "FAIL"))
        ok = ok and bool(c)

    par = {"a": {"x": 1}, "b": [1, 2], "c": "keep", "d": {"p": 1}}
    am = {"a": {"x": 1}, "b": [1, 2, 3], "c": "keep", "d": {"p": 1, "_note": "hi"}, "e": 5}
    r = dict((k, s) for k, s, _ in classify(par, am, ("_note",), {}))
    chk("identical block is IDENTICAL", r["a"] == "IDENTICAL")
    chk("annotated block is ANNOTATED", r["d"] == "ANNOTATED")
    chk("drifted block is UNDECLARED DRIFT", r["b"] == "UNDECLARED DRIFT")
    chk("new block is AMENDMENT-ONLY", r["e"] == "AMENDMENT-ONLY")
    r2 = dict((k, s) for k, s, _ in classify(par, am, ("_note",), {"b": "on purpose"}))
    chk("declared drift is DECLARED", r2["b"] == "DECLARED")
    r3 = dict((k, s) for k, s, _ in classify(par, {"a": {"x": 1}}, ("_note",), {}))
    chk("a dropped block is caught", r3["b"] == "MISSING FROM AMENDMENT")
    chk("canon strips only the named prefix",
        canon({"k": 1, "_n": 2}, ("_n",)) == {"k": 1})
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--amendment", required=True)
    ap.add_argument("--annotation-prefix", default="_amendment_note,_added_by_amendment")
    ap.add_argument("--show-diff", action="store_true", default=True)
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        print("=== selftest ===")
        return selftest()

    am = json.load(open(a.amendment, encoding="utf-8"))
    ppath = os.path.join(REPO, am["amends"])
    par = json.load(open(ppath, encoding="utf-8"))
    prefixes = tuple(x.strip() for x in a.annotation_prefix.split(",") if x.strip())
    declared = {d["block"]: d["why"] for d in am.get("_blocks_this_amendment_changes", [])}

    rows = classify(par, am, prefixes, declared)
    print("amendment %s\nparent    %s\nannotation prefixes %s\n"
          % (os.path.basename(a.amendment), am["amends"], list(prefixes)))
    bad = []
    for k, s, note in rows:
        print("  %-30s %-22s %s" % (k, s, note))
        if s in ("UNDECLARED DRIFT", "MISSING FROM AMENDMENT"):
            bad.append(k)
    if a.show_diff:
        for k in bad:
            if k in par and k in am:
                print("\n--- diff for UNDECLARED block %r ---" % k)
                for line in difflib.unified_diff(dump(par[k]), dump(am[k]),
                                                 "parent." + k, "amendment." + k, lineterm=""):
                    print("  " + line)
    print("\n%d block(s) compared; %d IDENTICAL, %d ANNOTATED, %d DECLARED, %d UNDECLARED/MISSING"
          % (len(rows), sum(1 for _, s, _ in rows if s == "IDENTICAL"),
             sum(1 for _, s, _ in rows if s == "ANNOTATED"),
             sum(1 for _, s, _ in rows if s == "DECLARED"), len(bad)))
    if bad:
        print("REFUSING: undeclared drift in %s" % bad)
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
