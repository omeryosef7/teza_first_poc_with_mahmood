"""verify_bank_join.py — re-check bank identity for runs that predate the bank's `_meta.json`.

WHY. Audit #8 flagged that all five headline judge runs record
`summary.json.bank_join.hash_verdict.ok = false` with reason "no *_meta.json for the bank" -- so the
AdvBench-495 bank version behind every headline number is unverified.

That message was ACCURATE WHEN WRITTEN and the judge code is not at fault: the runs executed
2026-08-19 between 01:17 and 07:23, and `advbench_heldout_495_meta.json` was created at 12:36 the same
day. The check looked for a file that did not exist yet.

But it exists now, and the join is checkable retrospectively -- the run's own `metadata.json` recorded
whatever bank hashes it had. So the standing caveat is replaceable by an answer, which is strictly
better than carrying "unverified" forever in a report. This does that, using the same
`compare_bank_hashes` the judge would have used, with `strict=False` so a genuine mismatch is REPORTED
rather than raised (the point is to learn the state of the artifacts, not to abort).

A verdict of `unknown` here still means unknown -- a run that recorded no hash cannot certify a join,
and this script will not pretend otherwise.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import compare_bank_hashes  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--runs", nargs="*", default=[
        "outputs/boombness/judge/abg_base_*", "outputs/boombness/judge/abg_B_*",
        "outputs/boombness/judge/abgL6_B_*", "outputs/boombness/judge/abgL10_B_*",
        "outputs/boombness/judge/abgL12_B_*"])
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    out = {}
    for pat in args.runs:
        hits = sorted(glob.glob(pat))
        if not hits:
            out[pat] = {"status": "no run matches"}
            continue
        d = hits[-1]
        name = os.path.basename(d)
        cfg = os.path.join(d, "config.json")
        bank = None
        if os.path.exists(cfg):
            a = json.load(open(cfg))
            bank = (a.get("args", a) or {}).get("bank")
        # the judge run points at a gens dir; the BANK hashes live in the gens run's metadata
        gens = (json.load(open(cfg)).get("args", {}) or {}).get("gens") if os.path.exists(cfg) else None
        meta_path = None
        for cand in ([os.path.join(gens, "metadata.json")] if gens else []) + \
                    [os.path.join(d, "metadata.json")]:
            if cand and os.path.exists(cand):
                meta_path = cand
                break
        if not bank or not meta_path:
            out[name] = {"status": "cannot check", "bank": bank, "meta": meta_path}
            continue
        bmeta = bank.replace(".jsonl", "_meta.json")
        if not os.path.exists(bmeta):
            out[name] = {"status": "bank _meta.json still absent", "bank": bank}
            continue
        verdict = compare_bank_hashes(json.load(open(meta_path)), json.load(open(bmeta)),
                                      strict=False)
        out[name] = {"status": "checked", "bank": os.path.basename(bank),
                     "meta_source": os.path.relpath(meta_path), "verdict": verdict}

    n_ok = sum(1 for v in out.values() if (v.get("verdict") or {}).get("ok"))
    n_unknown = sum(1 for v in out.values()
                    if v.get("status") == "checked" and not (v.get("verdict") or {}).get("ok"))
    doc = {"why": "the headline runs predate the bank's _meta.json (runs 01:17-07:23, meta 12:36 on "
                  "2026-08-19), so their recorded verdict is 'no *_meta.json' -- accurate then, "
                  "checkable now",
           "runs": out, "n_ok": n_ok, "n_not_certified": n_unknown,
           "reading": "an 'unknown' verdict still means unknown: a run that recorded no bank hash "
                      "cannot certify a join, and this script does not pretend otherwise",
           "provenance": {"argv": sys.argv, "git_commit": subprocess.run(
               ["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()}}
    with open(args.out, "w") as f:
        json.dump(doc, f, indent=2)

    for k, v in out.items():
        ver = v.get("verdict") or {}
        print(f"  {k[:34]:36s} {v.get('status'):12s} ok={ver.get('ok')} "
              f"agree={ver.get('agree') or ''} unknown={ver.get('unknown') or ''}")
    print(f"\n[bank-join] certified {n_ok}, not certified {n_unknown} -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
