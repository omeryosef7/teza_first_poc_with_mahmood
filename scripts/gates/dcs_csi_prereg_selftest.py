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

⚠ WHAT IT CANNOT DO, measured rather than guessed (R33's F5, S-362). Against four one-key
mutations of PR-CSI-020 that each crash a reader, this file now catches TWO and misses TWO:

    delete PRIMARY.alpha                       CAUGHT   (nested chain, since S-362)
    delete ...PER_HEAD.per_head                CAUGHT   (nested chain, since S-362)
    delete population.validation_expect_n      MISSED   -- COMPUTED key:
                                                  pr["population"]["%s_domains" % a.split]
    delete per_head["21"].bar_source_arm       MISSED   -- HELPER ALIAS: the dict is a function
                                                  parameter, not a name this scan recognises

The computed-key sites are now REPORTED rather than silently dropped, because a blind spot nobody
can see is the R29 shape. The alias case is not detected at all.

A static scan also cannot tell which subscripts lie behind a branch the family never takes --
`head_sets` for a cell family, `cell_sets` for a head family. So absences are reported and MUST be
judged: `--require` turns a named key into a hard failure, and running this against the preregs
that have ALREADY been read successfully is how the baseline gets calibrated.

IT IS A TRIPWIRE, NOT A PROOF, and the table above is the honest measure of its reach.
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


def _chain(node):
    """If `node` is pr["a"]["b"]... return ('a','b',...); else None.

    ⚠ R33/S-362: the first version of this file looked ONLY at depth 1, so it passed at exit 0 on
    four one-key mutations that crash a reader -- `PRIMARY.alpha` and
    `DETECTABILITY_PREREGISTERED_PER_HEAD.per_head` raise KeyError in STEP 2, i.e. AFTER the GPU,
    which is the exact cost this file exists to prevent. Chains are now walked to their root."""
    keys = []
    cur = node
    computed = False
    while isinstance(cur, ast.Subscript):
        sl = cur.slice
        if isinstance(sl, ast.Constant) and isinstance(sl.value, str):
            keys.append(sl.value)
        else:
            # ⚠ A COMPUTED KEY, e.g. pr["population"]["%s_domains" % a.split]. A static scan cannot
            # resolve it. It used to make the whole chain VANISH -- a silent blind spot, which is
            # the R29 shape. Now the resolved PREFIX is reported with a marker so the operator can
            # see there is something here to check by hand.
            computed = True
            keys.append("<computed>")
        cur = cur.value
    if isinstance(cur, ast.Name) and cur.id in PREREG_NAMES:
        return tuple(reversed(keys)), computed
    return None


def subscripted_keys(path):
    """Every constant key PATH hard-subscripted off a prereg-shaped name in this file.

    Keys are returned dotted: "PRIMARY.alpha" means pr["PRIMARY"]["alpha"]."""
    out = {}
    try:
        tree = ast.parse(open(os.path.join(REPO, path)).read())
    except (OSError, SyntaxError) as e:
        return {"__unreadable__": str(e)}
    for node in ast.walk(tree):
        if not isinstance(node, ast.Subscript):
            continue
        got = _chain(node)
        if not got:
            continue
        ch, _computed = got
        # keep only the LONGEST chain at each site: pr["A"]["B"] also matches pr["A"] as its inner
        # node, and reporting the prefix separately would be noise.
        out.setdefault(".".join(ch), node.lineno)
    longest = {}
    for k, ln in out.items():
        if not any(o != k and o.startswith(k + ".") for o in out):
            longest[k] = ln
    return longest


def resolve(pr, dotted):
    """Is this dotted key path present? A path with a <computed> segment is UNRESOLVABLE -- it is
    reported separately and never counted as missing, because a static scan cannot know."""
    if "<computed>" in dotted:
        return True
    cur = pr
    for part in dotted.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return False
        cur = cur[part]
    return True


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
        miss = sorted(k for k in keys if not resolve(pr, k))
        have = len(keys) - len(miss)
        print("%-46s  %2d hard-subscripted, %2d present, %2d MISSING"
              % (r, len(keys), have, len(miss)))
        for k in miss:
            print("      MISSING  %-38s (first subscripted at %s:%d)" % (k, r, keys[k]))
            missing_all.setdefault(k, []).append("%s:%d" % (r, keys[k]))

    comp = sorted({k for r in readers for k in subscripted_keys(r)
                   if "<computed>" in k and k != "__unreadable__"})
    if comp:
        print()
        print("⚠ %d COMPUTED-KEY site(s) -- a static scan CANNOT resolve these and they are NOT"
              % len(comp))
        print("  counted above. Check them by hand:")
        for k in comp:
            print("     %s" % k)

    print("=" * 92)
    if not missing_all:
        print("OK -- every hard-subscripted CONSTANT key path is present in this prereg.")
        if comp:
            print("   (%d computed-key site(s) remain unresolvable -- see above)" % len(comp))
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
