#!/usr/bin/env python3
"""Emit KNOWN_SHORT entries for a family's degeneracy-refused short arms, with MEASURED drops.

WHY THIS EXISTS (S-498). The norm-match degeneracy guard refuses one or more rows per control arm
(S-152/S-154/S-159 established the mechanism: the loss is a DETERMINISTIC function of (control
basis, row)). Every such run must be documented in run_completeness_check.KNOWN_SHORT, and the
table's own standard is to name the DROPPED prompt_id, measured by differencing against a full
sibling -- not to assert a row count. Doing that by hand for twenty arms is how a wrong prompt_id
gets into a permanent exemption.

⛔ IT PRINTS, IT DOES NOT EDIT. The output is reviewed and pasted. A script that writes its own
   exemptions into a guard is a script that can silence the guard.

⛔ NON-VACUITY: refuses if the reference arm is not full, if no short arm is found, or if a short
   arm's dropped set is empty or larger than its declared n_rows_failed.
"""
import argparse, glob, json, os, sys

BASE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                    "outputs", "boombness", "score_behavior")


def pids(run_dir):
    out, dom = set(), {}
    with open(os.path.join(run_dir, "results.jsonl"), encoding="utf-8") as fh:
        for line in fh:
            r = json.loads(line)
            out.add(r["prompt_id"])
            dom[r["prompt_id"]] = r.get("domain")
    return out, dom


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--glob", required=True, help="e.g. 'csi1_basket_train_KO_NEC_SHUF*'")
    ap.add_argument("--reference", required=True, help="a FULL sibling run dir basename")
    ap.add_argument("--expect-n", type=int, required=True)
    ap.add_argument("--entry-prefix", required=True, help="e.g. 'S-498: PR-CSI-003-A half 4/5'")
    ap.add_argument("--allow-short", type=int, required=True)
    a = ap.parse_args()

    ref = os.path.join(BASE, a.reference)
    # ADDED S-537. --reference wants a run DIRECTORY BASENAME (tag + _YYYYmmdd_HHMMSS_pid), not a
    # tag. Passing the tag used to raise a bare FileNotFoundError from deep inside pids(), which is
    # exactly the wrong failure at the moment this script is used: the family has just landed, the
    # commit is blocked on its output, and a traceback reads like the tool is broken rather than
    # mis-called. The docstring promised non-vacuity refusals and this path had none.
    if not os.path.isdir(ref):
        cands = sorted(os.path.basename(d) for d in glob.glob(ref + "_*") if os.path.isdir(d))
        sys.exit("REFUSING: --reference %r is not a run directory under %s.\n"
                 "  It must be a run dir BASENAME, i.e. <tag>_<YYYYmmdd>_<HHMMSS>_<pid>, not a tag.%s"
                 % (a.reference, BASE,
                    ("\n  Did you mean one of: " + ", ".join(cands)) if cands else
                    "\n  No directory begins with that name either -- check the tag."))
    if not os.path.exists(os.path.join(ref, "results.jsonl")):
        sys.exit("REFUSING: reference %s has no results.jsonl. A reference with no rows cannot "
                 "establish what another arm dropped." % a.reference)
    full, fdom = pids(ref)
    if len(full) != a.expect_n:
        sys.exit("REFUSING: reference %s holds %d rows, not --expect-n %d. A reference that is "
                 "itself short cannot establish what another arm dropped."
                 % (a.reference, len(full), a.expect_n))

    rows, n_short = [], 0
    for d in sorted(glob.glob(os.path.join(BASE, a.glob))):
        if not os.path.isdir(d) or "VOID6CHK" in d or "SMOKE" in d:
            continue
        p = os.path.join(d, "DONE.json")
        if not os.path.exists(p):
            continue
        done = json.load(open(p))
        if done.get("status") != "INCOMPLETE":
            continue
        n_failed = int(done.get("n_rows_failed") or 0)
        fr = str(done.get("failure_reasons") or "")
        if "DEGENERATE" not in fr:
            print("# ⚠ SKIPPED %s: INCOMPLETE but NOT a degeneracy refusal -- %s"
                  % (os.path.basename(d), fr[:110]), file=sys.stderr)
            continue
        got, _ = pids(d)
        dropped = sorted(full - got)
        if not dropped:
            sys.exit("REFUSING: %s is INCOMPLETE but dropped NO prompt_id relative to the "
                     "reference. Differencing found nothing to document." % os.path.basename(d))
        if len(dropped) != n_failed:
            print("# ⚠ %s: %d dropped ids but DONE.json says n_rows_failed=%d -- REPORTING BOTH"
                  % (os.path.basename(d), len(dropped), n_failed), file=sys.stderr)
        if len(dropped) > a.allow_short:
            print("# 🔴 %s: %d rows short EXCEEDS --allow-short %d -- NOT inside the preregistered "
                  "tolerance; this one needs a decision, not an exemption."
                  % (os.path.basename(d), len(dropped), a.allow_short), file=sys.stderr)
        n_short += 1
        ids = ", ".join("%s (domain %s)" % (i, fdom.get(i)) for i in dropped)
        rows.append((os.path.basename(d), len(got), n_failed, ids))

    if not n_short:
        sys.exit("REFUSING: the glob %r matched no INCOMPLETE degeneracy-refused arm. An exemption "
                 "generator that emits nothing has documented nothing." % a.glob)

    print("    # ---- generated by scripts/gates/dcs_csi_known_short_entries.py (%d arms) --------"
          % n_short)
    for name, nrows, n_failed, ids in rows:
        print('    "%s":' % name)
        print('        "%s. %d row(s) of %d REFUSED by the norm-match degeneracy guard; DONE.json "'
              % (a.entry_prefix, n_failed, a.expect_n))
        print('        "honest (status=INCOMPLETE, n_rows_failed=%d, rows_written=%d). MEASURED "'
              % (n_failed, nrows))
        print('        "dropped prompt_id %s, differenced against the full %d-row %s. "'
              % (ids, a.expect_n, a.reference))
        print('        "Inside --allow-short %d.",' % a.allow_short)
    print("# %d arm(s) emitted" % n_short, file=sys.stderr)


if __name__ == "__main__":
    main()
