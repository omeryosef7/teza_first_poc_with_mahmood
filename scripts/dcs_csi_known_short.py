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

# REVIEW R3-M7. The first template ASSERTED two things this script never checked -- that the loss
# is "outcome-independent" and "not domain-clustered" -- and rendered `failure_example_ids` as if it
# were the complete list, when common.py caps that field at 10 per reason. Both are now either
# MEASURED (the domain spread is counted below) or stated as a mechanism rather than a verified
# property, and the id list is labelled as a sample whenever it may be truncated.
TEMPLATE = (
    '    "{rid}":\n'
    '        "DCS-CSI-047: {have} of {want} rows. {nfail} row(s) REFUSED by the sprint\'s own "\n'
    '        "norm-match degeneracy guard (SubspaceDonorPatch, review R2-M5): the control basis was "\n'
    '        "near-orthogonal to the KO->clean delta at some position, so rescaling its projection "\n'
    '        "would have amplified float noise into an arbitrary QR-gauge direction. The guard "\n'
    '        "declines to fabricate a control rather than silently writing a meaningless one. "\n'
    '        "MECHANISM (not a verified property of this run): degeneracy is the angle between a "\n'
    '        "fixed basis and a fixed delta, both determined before any readout, and the delta is "\n'
    '        "identical across arms -- so the loss is expected to be outcome-independent. MEASURED "\n'
    '        "here: the {nfail} lost row(s) fall in {ndom} distinct domain(s) ({domfrac}), and "\n'
    '        "dcs_csi_subspace_analyze.py intersects (domain, slot) KEYS across all arms before "\n'
    '        "averaging, so every arm is compared on the same key set regardless. Ledger: "\n'
    '        "n_attempted {want}, n_succeeded {have}, n_failed {nfail}. Failing prompt_ids {idnote}: "\n'
    '        "{ids}.",\n')



def _domains_for(run_dir, prompt_ids):
    """Domains of the LOST rows, recovered from the bank the run selected from.

    Measured rather than asserted (review R3-M7): a clustered loss would be a different problem
    from a scattered one, and the earlier template claimed "not domain-clustered" without looking.
    """
    import json as _json
    cfg = _json.load(open(os.path.join(run_dir, "config.json")))["args"]
    # REVIEW R8-m9. `bank` is stored RELATIVE, so `os.path.exists(bank)` is false from any cwd but
    # the repo root and this returned [] -- which the caller's `or len(ids)` fallback then turned
    # into a fabricated "1 row per domain at most". Resolve against REPO, and RAISE rather than
    # return a silent empty list: this function feeds a sentence that says "MEASURED", so being
    # unable to measure must stop the run, not soften the wording. (This is review R3-M7 recurring
    # in the one clause the R3 fix was written for.)
    bank = cfg.get("bank")
    if not bank:
        raise SystemExit("REFUSING: run %s records no bank, so the domain spread of its lost rows "
                         "cannot be MEASURED -- and the entry template claims it was" % run_dir)
    if not os.path.isabs(bank):
        bank = os.path.join(REPO, bank)
    if not os.path.exists(bank):
        raise SystemExit("REFUSING: bank %r (from run %s) does not exist, so the domain spread of "
                         "its lost rows cannot be MEASURED" % (bank, run_dir))
    want = set(prompt_ids)
    doms = []
    with open(bank) as fh:
        for line in fh:
            r = _json.loads(line)
            if r.get("prompt_id") in want:
                doms.append(r.get("domain"))
    return doms

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
        nfail = int(f.get("n_failed") or 0)
        # `failure_example_ids` is CAPPED (common.py); say so unless we can see the whole list.
        idnote = "(complete)" if len(ids) >= nfail else "(SAMPLE -- the ledger caps this list)"
        # MEASURE the domain spread rather than asserting it. The lost rows are the ones present in
        # the bank selection but absent from results.jsonl.
        # REVIEW R8-m9. `lost_doms` was dead (built and never read) and `ndom`'s `or len(ids)`
        # fallback made an unmeasurable case indistinguishable from a maximally-spread one. The
        # fallback is gone: `_domains_for` now raises if it cannot measure, so a zero here means
        # the lost ids genuinely are not in the bank, which is itself a refusal.
        _doms = _domains_for(d, ids)
        if not _doms:
            raise SystemExit("REFUSING %s: none of the %d lost prompt_id(s) %s appear in the bank, "
                             "so the domain spread cannot be MEASURED" % (rid, len(ids), ids))
        ndom = len(set(_doms))
        domfrac = "1 row(s) per domain at most" if ndom >= len(ids) else "clustered"
        add.append(TEMPLATE.format(rid=rid, have=have, want=want, nfail=nfail, ids=", ".join(ids),
                                   idnote=idnote, ndom=ndom, domfrac=domfrac))
        print("  DOCUMENT %s: %d of %d, %s %s, %d domain(s)" % (rid, have, want, ids, idnote, ndom))
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
