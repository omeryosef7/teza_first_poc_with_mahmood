#!/usr/bin/env python3
"""PR-CSI-003-A VOID 6: is the score_behavior.py change INERT? (S-490)

Compares the VOID6CHK replay of KO_NEC_SHUF0 (run at blob 9562bdf9) against the committed arm
(run at blob e94258bd) ROW FOR ROW. Exit 0 only if every compared row is identical on every
numeric field the endpoint depends on.

⛔ NON-VACUITY FIRST (S-134/S-480, and R39 stream 2's whole theme): this gate REFUSES if either
   run dir is missing, if the row counts differ, if zero rows are compared, or if the two dirs
   turn out to be the same directory. A comparison over nothing must never print PASS.
"""
import json, os, sys, glob

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OLD_TAG = "csi1_basket_train_KO_NEC_SHUF0"
NEW_TAG = "csi1_basket_train_VOID6CHK_KO_NEC_SHUF0"
BASE = os.path.join(REPO, "outputs", "boombness", "score_behavior")
# every field the installation endpoint or a VOID condition reads
FIELDS = ("logp_concept", "logp_codeword", "option_mass", "domain", "family_id",
          "query_kind", "cell", "prompt_id", "hook_n_prefill_edits", "hook_n_decode_edits",
          "hook_liveness_violations", "rescue_liveness")


def one_dir(tag):
    hits = sorted(d for d in glob.glob(os.path.join(BASE, tag + "_*")) if os.path.isdir(d))
    ok = []
    for d in hits:
        p = os.path.join(d, "DONE.json")
        if os.path.exists(p):
            try:
                if json.load(open(p)).get("status") == "ok":
                    ok.append(d)
            except Exception:
                pass
    if len(ok) != 1:
        sys.exit("REFUSING: tag %r resolves to %d complete run dirs (need exactly 1): %s"
                 % (tag, len(ok), [os.path.basename(x) for x in ok]))
    return ok[0]


def rows(d):
    out = {}
    with open(os.path.join(d, "results.jsonl"), encoding="utf-8") as fh:
        for line in fh:
            r = json.loads(line)
            k = (r.get("prompt_id"), r.get("query_kind"), r.get("cell"))
            if k in out:
                sys.exit("REFUSING: duplicate row key %r in %s" % (k, d))
            out[k] = r
    return out


def main():
    old, new = one_dir(OLD_TAG), one_dir(NEW_TAG)
    if os.path.realpath(old) == os.path.realpath(new):
        sys.exit("REFUSING: both tags resolved to the SAME directory -- this would trivially pass")
    ro, rn = rows(old), rows(new)
    print("  committed : %s  (%d rows)" % (os.path.basename(old), len(ro)))
    print("  replay    : %s  (%d rows)" % (os.path.basename(new), len(rn)))
    for meta, d in (("committed", old), ("replay", new)):
        try:
            g = json.load(open(os.path.join(d, "RUNMETA.json"))).get("git_commit")
        except Exception:
            g = None
        print("  %-10s git_commit=%s" % (meta, g))
    if not ro or not rn:
        sys.exit("REFUSING: a run dir yielded ZERO rows. A comparison over nothing is not a check.")
    if set(ro) != set(rn):
        sys.exit("REFUSING: row KEY SETS differ (%d only-committed, %d only-replay) -- the two runs "
                 "did not score the same population." % (len(set(ro) - set(rn)), len(set(rn) - set(ro))))

    diffs, compared = [], 0
    for k in sorted(ro, key=lambda t: tuple(str(x) for x in t)):
        a, b = ro[k], rn[k]
        compared += 1
        for f in FIELDS:
            if a.get(f) != b.get(f):
                diffs.append((k, f, a.get(f), b.get(f)))
    if compared == 0:
        sys.exit("REFUSING: compared ZERO rows.")
    print("  compared %d rows x %d fields = %d value comparisons"
          % (compared, len(FIELDS), compared * len(FIELDS)))
    if diffs:
        print("  ROWS DIFFER: %d field mismatches" % len(diffs))
        for k, f, a, b in diffs[:10]:
            print("     %-40s %-22s %r -> %r" % (str(k)[:40], f, str(a)[:28], str(b)[:28]))
        print("\nVOID 6 IS NOT DISCHARGED: the score_behavior.py change is NOT inert on this arm.")
        return 1
    print("\nVOID 6 DISCHARGED: %d rows bit-identical across the score_behavior.py blob change "
          "(e94258bd -> 9562bdf9). The --knockout-cells edit is inert for arms that do not pass "
          "the flag, on the S-139 standard." % compared)
    return 0


if __name__ == "__main__":
    sys.exit(main())
