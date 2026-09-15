#!/usr/bin/env python3
"""Append this sprint's norm-match-degeneracy short runs to run_completeness_check.KNOWN_SHORT.

WHY A SCRIPT RATHER THAN HAND EDITS. The sprint's control arms lose rows to ONE understood cause --
`SubspaceDonorPatch`'s degeneracy refusal (review R2-M5) declining to fabricate a control when a
control subspace is near-orthogonal to the KO->clean delta at some position. It will keep happening
across ~20 control arms. Hand-writing each entry invites a copy-paste that says something slightly
untrue about a run nobody re-checked.

This script REFUSES to document a run it has not verified: the run must be short by rows whose
ledgered failure reason is the degeneracy refusal, and the ledger's counts must agree with the file.
Anything else it leaves for a human, which is the whole point of the guard it is feeding.
"""
from __future__ import annotations
import argparse, glob, json, os, re, sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GUARD = os.path.join(REPO, "src/boombness/run_completeness_check.py")
REASON_KEY = "norm-match DEGENERATE"

TEMPLATE = (
    '    "{rid}":\n'
    '        "DCS-CSI-047: {have} of {want} rows. {nfail} row(s) ({ids}) REFUSED by the sprint\'s "\n'
    '        "own norm-match degeneracy guard (SubspaceDonorPatch, review R2-M5): the control "\n'
    '        "basis was near-orthogonal to the KO->clean delta at some position, so rescaling its "\n'
    '        "projection would have amplified float noise into an arbitrary QR-gauge direction. "\n'
    '        "The guard declines to fabricate a control rather than silently writing a meaningless "\n'
    '        "one. The loss is OUTCOME-INDEPENDENT (the angle between a fixed basis and a fixed "\n'
    '        "delta, both determined before any readout; the delta is identical across arms) and is "\n'
    '        "not domain-clustered. dcs_csi_subspace_analyze.py intersects (domain, slot) KEYS "\n'
    '        "across all arms before averaging, so every arm is compared on the same key set. "\n'
    '        "Ledger: n_attempted {want}, n_succeeded {have}, n_failed {nfail}.",\n')


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pattern", default="csi1_button_train_*")
    ap.add_argument("--apply", action="store_true", help="write; otherwise dry-run")
    a = ap.parse_args()
    src = open(GUARD).read()
    add, skipped = [], []
    for d in sorted(glob.glob(os.path.join(REPO, "outputs/boombness/score_behavior", a.pattern))):
        rid = os.path.basename(d)
        if rid in src:
            continue
        cfgp, sump, resp = (os.path.join(d, x) for x in ("config.json", "summary.json", "results.jsonl"))
        if not all(os.path.exists(x) for x in (cfgp, sump, resp)) or not os.path.exists(os.path.join(d, "DONE.json")):
            continue
        want = json.load(open(cfgp))["args"].get("expect_n")
        have = sum(1 for _ in open(resp))
        if not want or have >= want:
            continue
        f = json.load(open(sump)).get("failures", {})
        reasons = f.get("failure_reasons", {})
        if not reasons or not all(REASON_KEY in k for k in reasons):
            skipped.append((rid, "shortfall is NOT the degeneracy refusal: %s" % list(reasons)[:1])); continue
        if f.get("n_succeeded") != have or f.get("n_attempted") != want:
            skipped.append((rid, "ledger disagrees with the file")); continue
        ids = sorted({i for v in (f.get("failure_example_ids") or {}).values() for i in v})
        add.append(TEMPLATE.format(rid=rid, have=have, want=want, nfail=f.get("n_failed"),
                                   ids=", ".join(ids)))
        print("  DOCUMENT %s: %d of %d, %s" % (rid, have, want, ids))
    for rid, why in skipped:
        print("  LEFT FOR A HUMAN %s: %s" % (rid, why))
    if not add:
        print("nothing new to document"); return 0
    if not a.apply:
        print("\n(dry run; pass --apply to write %d entr(ies))" % len(add)); return 0
    src = src.replace("KNOWN_SHORT = {\n", "KNOWN_SHORT = {\n" + "".join(add), 1)
    open(GUARD, "w").write(src)
    print("\nwrote %d entr(ies) into %s" % (len(add), os.path.relpath(GUARD, REPO)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
