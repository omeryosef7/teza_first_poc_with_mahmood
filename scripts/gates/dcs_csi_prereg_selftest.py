#!/usr/bin/env python
"""Does a prereg carry every field its READERS will hard-subscript?

WHY THIS EXISTS. PR-CSI-020's first freeze (md5 9fce4bda) omitted two keys -- `CENSUS_DELIVERABLE`
and `DOSE_IDENTITY_IS_BLIND_HERE` -- that `scripts/dcs_csi_head_census.py` subscripts with `pr[...]`,
not `pr.get(...)`. The census validates them BEFORE loading any arm, so the family would have
refused to read. R32-A and R32-B both found it, and R32-A's note is the reason this file exists:

    "The freeze would have caught B1 with a single assertion that the emitted prereg satisfies
     every pr[...] subscript in head_census.py."

The failure class is older than PR-CSI-020. `head_census.py`'s own comment at its field-validation
block records that the same trap was already fixed once for `WHAT_THIS_CANNOT_DO` -- "would have
died at the last step, AFTER the GPU". A prereg is a contract with its readers, and nothing was
checking that the contract was satisfiable until the GPU had already been spent.

HOW IT WORKS. AST-parse each reader, collect every `pr["KEY"]` / `prereg["KEY"]` hard subscript,
and report which of those keys the prereg lacks. Hard subscripts only: `.get()` is an author
declaring the field optional, and this file does not second-guess that.

⚠ WHAT IT CANNOT DO. A static scan cannot tell which subscripts lie behind a branch the family
never takes -- `head_sets` for a cell family, `cell_sets` for a head family. So keys missing from a
prereg are reported and MUST be judged: `--require` turns a named key into a hard failure, and
running this against the preregs that have ALREADY been read successfully is how the baseline gets
calibrated. It is a tripwire, not a proof.
"""
import argparse, ast, json, os, sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
READERS = [
    "scripts/dcs_csi_head_census.py",
    "scripts/dcs_csi_pr016_argmax_test.py",
    "scripts/gates/dcs_csi_pr012_gate0_sweep.py",
    "scripts/gates/dcs_csi_pr010_argv.py",
]
PREREG_NAMES = {"pr", "prereg"}


def subscripted_keys(path):
    """Every string key hard-subscripted off a prereg-shaped name in this file."""
    out = {}
    try:
        tree = ast.parse(open(os.path.join(REPO, path)).read())
    except (OSError, SyntaxError) as e:
        return {"__unreadable__": str(e)}
    for node in ast.walk(tree):
        if not isinstance(node, ast.Subscript):
            continue
        val = node.value
        if not (isinstance(val, ast.Name) and val.id in PREREG_NAMES):
            continue
        sl = node.slice
        if isinstance(sl, ast.Constant) and isinstance(sl.value, str):
            out.setdefault(sl.value, node.lineno)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prereg", required=True)
    ap.add_argument("--require", action="append", default=[],
                    help="a key whose absence is a FAILURE rather than a report line")
    ap.add_argument("--reader", action="append", default=None,
                    help="override the reader list")
    a = ap.parse_args()

    pr = json.load(open(os.path.join(REPO, a.prereg)))
    readers = a.reader or READERS
    print("prereg %s   id=%s" % (a.prereg, pr.get("id")))
    print("=" * 92)

    missing_all = {}
    for r in readers:
        keys = subscripted_keys(r)
        if "__unreadable__" in keys:
            print("%-46s  UNREADABLE: %s" % (r, keys["__unreadable__"]))
            continue
        miss = sorted(k for k in keys if k not in pr)
        have = len(keys) - len(miss)
        print("%-46s  %2d hard-subscripted, %2d present, %2d MISSING"
              % (r, len(keys), have, len(miss)))
        for k in miss:
            print("      MISSING  %-38s (first subscripted at %s:%d)" % (k, r, keys[k]))
            missing_all.setdefault(k, []).append("%s:%d" % (r, keys[k]))

    print("=" * 92)
    if not missing_all:
        print("OK -- every hard-subscripted key is present in this prereg.")
        return 0

    hard = [k for k in missing_all if k in a.require]
    print("%d key(s) are subscripted by a reader and ABSENT from the prereg:" % len(missing_all))
    for k, where in sorted(missing_all.items()):
        print("   %-40s %s%s" % (k, ", ".join(where), "   <-- --require" if k in hard else ""))
    print()
    print("⚠ Some of these may sit behind a branch this family never takes (head_sets for a cell "
          "family, and so on). Judge them; do not assume.")
    if hard:
        sys.exit("REFUSING: %d REQUIRED key(s) absent: %s" % (len(hard), ", ".join(sorted(hard))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
