#!/usr/bin/env python3
"""VOID 7: is an ANALYSER change inert on a landed family? (leaf-for-leaf artefact diff)

*** WHY THIS EXISTS. ***
VOID 7 fires when an analyser moves COMPUTATIONALLY (as opposed to I/O-only) between a prereg's
freeze and its read. The way to discharge it is not to argue from the diff -- it is to re-run the
FROZEN recipe under the new code and show that every published number is unchanged. That was done
by hand at S-490 (VOID 7, 80 leaves, zero differing) and again at S-533 (the R41 CRITICAL-1 sign
guard). Twice is enough to stop retyping it.

WHAT IT REPORTS, and the distinction that matters:
  * CHANGED leaves  -- a published number moved. This is what VOID 7 is about. Non-zero => FAIL.
  * REMOVED leaves  -- a field the old artefact had and the new one does not. Also a FAIL: a read
                       that stops reporting something is not inert.
  * ADDED leaves    -- new fields. NOT a failure by itself: a guard that records its own decision
                       (`candidate_sign_ok`) adds a leaf without moving a number. They are listed
                       in full so "disclosure only" is a claim the reader can check, not take.

⛔ NON-VACUITY FIRST (S-134, and R39 stream 2's whole theme): REFUSE if either file is missing, if
   either parses to zero leaves, if the two paths are the same file, or if the two artefacts are
   byte-identical (which would mean the re-run did not actually happen). A comparison over nothing
   must never print PASS.

Volatile fields (timestamps, output paths, argv) are excluded by name, and the exclusion list is
printed so it cannot quietly grow to cover a real difference.
"""
import argparse, json, os, sys

VOLATILE = ("generated_at", "timestamp", "out", "output_path", "argv", "sys_argv",
            "wrote", "written_at", "elapsed_s", "host", "hostname", "pid")


def leaves(obj, pre=""):
    """Flatten to {dotted.path: scalar}. Lists are indexed so order changes are visible."""
    out = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            out.update(leaves(v, "%s.%s" % (pre, k) if pre else str(k)))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            out.update(leaves(v, "%s[%d]" % (pre, i)))
    else:
        out[pre] = obj
    return out


def volatile(path):
    return any(seg in VOLATILE for seg in path.split("."))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--old", required=True, help="the COMMITTED artefact (before the change)")
    ap.add_argument("--new", required=True, help="the re-run under the new code")
    ap.add_argument("--allow-added", action="store_true",
                    help="treat ADDED leaves as inert (disclosure-only fields). Added leaves are "
                         "listed either way; this only decides the exit code.")
    a = ap.parse_args()

    for lab, p in (("--old", a.old), ("--new", a.new)):
        if not os.path.exists(p):
            sys.exit("REFUSING: %s %r does not exist. A comparison against a missing file is not "
                     "a passing comparison." % (lab, p))
    if os.path.realpath(a.old) == os.path.realpath(a.new):
        sys.exit("REFUSING: --old and --new resolve to the SAME file (%s). That comparison cannot "
                 "fail." % os.path.realpath(a.old))
    ob, nb = open(a.old, "rb").read(), open(a.new, "rb").read()
    if ob == nb:
        sys.exit("REFUSING: the two artefacts are BYTE-IDENTICAL. Either the re-run did not "
                 "happen or it overwrote the committed file -- both make this check vacuous.")

    L, R = leaves(json.load(open(a.old))), leaves(json.load(open(a.new)))
    Lk = {k: v for k, v in L.items() if not volatile(k)}
    Rk = {k: v for k, v in R.items() if not volatile(k)}
    if not Lk or not Rk:
        sys.exit("REFUSING: %d old / %d new comparable leaves. Zero leaves is not agreement."
                 % (len(Lk), len(Rk)))

    common = sorted(set(Lk) & set(Rk))
    changed = [(k, Lk[k], Rk[k]) for k in common if Lk[k] != Rk[k]]
    removed = sorted(set(Lk) - set(Rk))
    added = sorted(set(Rk) - set(Lk))

    print("[void7] excluded-as-volatile: %s" % ", ".join(VOLATILE))
    print("[void7] old leaves %d | new leaves %d | compared %d"
          % (len(Lk), len(Rk), len(common)))
    print("[void7] CHANGED %d | REMOVED %d | ADDED %d" % (len(changed), len(removed), len(added)))
    for k, o, n in changed[:40]:
        print("   CHANGED %-58s %r -> %r" % (k, o, n))
    for k in removed[:40]:
        print("   REMOVED %-58s %r" % (k, Lk[k]))
    for k in added[:40]:
        print("   ADDED   %-58s %r" % (k, Rk[k]))

    bad = len(changed) + len(removed) + (0 if a.allow_added else len(added))
    if bad == 0:
        print("[void7] INERT on this family: every compared leaf identical"
              + (", %d added leaf(s) are disclosure-only" % len(added) if added else ""))
        return 0
    print("[void7] NOT INERT: %d disqualifying difference(s)" % bad)
    return 1


if __name__ == "__main__":
    sys.exit(main())
