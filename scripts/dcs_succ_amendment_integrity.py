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


def canon(o, prefixes, _top=True):
    """Retained only for the selftest. THE CLASSIFIER NO LONGER USES IT -- see below.

    REVIEW-3 C2 (CRITICAL). This used to recurse, stripping `_amendment_note*` and
    `_added_by_amendment*` at EVERY depth of EVERY block -- so anything hidden inside an annotation
    key was invisible to the comparison. The reviewer forged a copy that reverted C-213c's
    corrected floor back to 0.0221 *inside* `classifier._added_by_amendment_measured_floors` and
    injected a `kill_condition` override, and this script reported **0 UNDECLARED, EXIT 0**. A
    check that can be defeated by putting the change in a key whose name begins with an underscore
    is not a check; it is a naming convention.

    The repair is NOT a better stripping rule -- it is DELETING THE CATEGORY. `ANNOTATED` existed
    to excuse a block that differs from its parent "only by an annotation", and any rule for
    deciding that is a rule an author can write around: the parent never contains the annotation
    key, so whatever is hidden inside it is invisible to any comparison that strips it. There are
    now exactly three outcomes -- IDENTICAL, DECLARED (itemised in the amendment, with its diff
    PRINTED), or UNDECLARED DRIFT (a refusal). A block that differs at all must be declared, and
    declaring it shows it. A2 passes unchanged under this rule: 0 blocks were ANNOTATED once
    `declared` was tested first, so nothing was relying on the hatch.
    """
    if isinstance(o, dict):
        return {k: v for k, v in o.items()
                if not (_top and any(k.startswith(p) for p in prefixes))}
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
        # REVIEW-3 C2: `declared` is tested FIRST. Testing IDENTICAL/ANNOTATED first made a block
        # the amendment explicitly claims to change print as "ANNOTATED" whenever its only visible
        # difference was an annotation key -- which is exactly what A2's `classifier` block did,
        # the block carrying the entire C-213c repair. A declared change reported as an annotation
        # is C-213b's failure mode (a change the amendment says it made, invisible in the output).
        if k in declared:
            rows.append((k, "DECLARED", declared[k]))
        elif json.dumps(par[k], sort_keys=True) == json.dumps(am[k], sort_keys=True):
            rows.append((k, "IDENTICAL", ""))
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
    chk("an undeclared annotation-only change is DRIFT", r["d"] == "UNDECLARED DRIFT")
    # REVIEW-3 C2 regression: a change NESTED INSIDE an annotation key must be visible.
    par2 = {"c": {"keep": 1, "_amendment_note": {"floor": 0.1372}}}
    am2 = {"c": {"keep": 1, "_amendment_note": {"floor": 0.0221}}}
    r_nest = dict((k, s) for k, s, _ in classify(par2, am2, ("_amendment_note",), {}))
    chk("a change INSIDE an annotation key is caught", r_nest["c"] == "UNDECLARED DRIFT")
    chk("there is no ANNOTATED category left",
        not any(st == "ANNOTATED" for _, st, _ in classify(par2, am2, ("_amendment_note",), {})))
    r_first = dict((k, s) for k, s, _ in classify(par, am, ("_note",), {"d": "declared"}))
    chk("declared beats annotated in classification", r_first["d"] == "DECLARED")
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
    ap.add_argument("--amendment", default="")
    ap.add_argument("--annotation-prefix", default="_amendment_note,_added_by_amendment")
    ap.add_argument("--show-diff", action="store_true", default=True)
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        print("=== selftest ===")
        return selftest()
    if not a.amendment:
        raise SystemExit("REFUSING: --amendment is required unless --selftest")

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
        # Print a diff for EVERY block that is not byte-identical, not only the refusing ones.
        # REVIEW-3 C2: diffs used to print only for `bad`, so all nine DECLARED/ANNOTATED changes
        # were suppressed -- including the one carrying the C-213c repair. A declared change whose
        # content is never shown is a declaration, not a disclosure.
        for k, st, _ in rows:
            if st == "DECLARED" and k in par and k in am:
                print("\n--- diff for %s block %r ---" % (st, k))
                for line in difflib.unified_diff(dump(par[k]), dump(am[k]),
                                                 "parent." + k, "amendment." + k, lineterm=""):
                    print("  " + line)
        for k in bad:
            if k in par and k in am:
                print("\n--- diff for UNDECLARED block %r ---" % k)
                for line in difflib.unified_diff(dump(par[k]), dump(am[k]),
                                                 "parent." + k, "amendment." + k, lineterm=""):
                    print("  " + line)
    print("\n%d block(s) compared; %d IDENTICAL, %d (no annotated category), %d DECLARED, "
          "%d UNDECLARED/MISSING"
          % (len(rows), sum(1 for _, s, _ in rows if s == "IDENTICAL"),
             0,
             sum(1 for _, s, _ in rows if s == "DECLARED"), len(bad)))
    if bad:
        print("REFUSING: undeclared drift in %s" % bad)
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
