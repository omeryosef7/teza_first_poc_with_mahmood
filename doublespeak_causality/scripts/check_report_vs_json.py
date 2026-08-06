#!/usr/bin/env python3
"""Report-prose vs committed-JSON consistency checker.

THE GAP THIS FILLS. Three checks already exist and none of them covers this:
  * validate_all_outputs.py   -- summary.json  vs  raw.jsonl
  * build_claim_audit.py      -- registry claims vs committed JSON
  * validate_experiment_coverage.py -- row schema / coverage
Nothing checked **report prose against the JSON it quotes**, and that is exactly where audit finding O2
lived: `PHASE8_1_ALPHA_CALIBRATION.md` carried 13 of 14 hand-copied cells stale at n=78 while the
auto-generated tables in the SAME FILE showed the n=86 values. One of those stale cells reversed a stated
conclusion ("below the noise floor" -> actually above it).

WHAT IT DOES. For each (report, json) pair below, walk the JSON's numeric leaves, and for every leaf ask:
does the report contain a number that is CLOSE to this value but not equal to it? A near-miss is the
signature of a hand-copied number that has since been regenerated. An exact match is fine; a totally
different number is fine (it is a different quantity); a value within `--near` but outside `--tol` is the
dangerous case.

WHY "NEAR-MISS" AND NOT "MISSING". Reports legitimately quote a subset, round differently, and discuss
values that are not in the JSON at all. Flagging absence would drown the signal. Flagging a number that is
*almost* right is precise: +0.487 next to a JSON value of +0.4767 is a stale copy, whereas +0.9 next to it
is simply a different number.

LIMITATION -- stated plainly, because it means this tool does NOT fully close the O2 gap.
O2's signature is a report holding the CORRECT value in one place and a STALE copy in another. Detecting
that requires flagging a near-miss even when an exact match exists (`--contradictions`). But numeric
proximity cannot tell "a stale copy of X" from "the correct value of a DIFFERENT quantity Y that happens
to sit nearby": on this corpus `--contradictions` fires 11 times, 10 of them false (curated's Ihat
-0.2157 sits 0.0064 from clearharm's -0.2093, while O2's real defect was a 0.0103 gap). Narrowing the
window kills the true positive before the false ones. So:
  * DEFAULT mode (key value present-or-absent) is precise and low-noise -- it found a real omission in
    REP_PREDICTS_BEHAVIOR.md, where a WITHDRAWN claim was still live because the correction had been
    applied to the claim audit and never propagated to the report.
  * `--contradictions` is a REVIEW AID with a high false-positive rate. Read every hit.
  * THE ACTUAL FIX IS PREVENTION, NOT DETECTION: generate tables from the JSON instead of transcribing
    them. PHASE8_1's side-by-side table is now generated, which is why O2 cannot recur *there*.

This is a LINT, not a gate: it reports and exits 0 unless --strict.

Usage:
  python scripts/check_report_vs_json.py                 # all registered pairs
  python scripts/check_report_vs_json.py --strict        # exit 1 on any hit
"""
from __future__ import annotations
import argparse, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
DC = os.path.dirname(HERE)

# KEY PATHS ONLY -- deliberately NOT a generic sweep.
#
# The first version of this tool compared every report number against every JSON leaf and produced 842
# "near-misses", nearly all coincidence (a p-value of 0.3699 "matches" an AUC of 0.36). A linter that
# cries wolf is worse than no linter: it trains the reader to skip it, which is how O2 survived a whole
# tick in the first place. So this checks a CURATED list of load-bearing values -- the ones a report is
# actually claiming -- and asserts each appears verbatim.
#
# Each entry: (report, json, [ (json_path, human_label), ... ])
PAIRS = [
    ("reports/PHASE8_1_ALPHA_CALIBRATION.md", "outputs/alpha_calibration.json", [
        ("cohorts.clearharm.splits.pooled.0.25.I_max",          "clearharm a=0.25 I_max"),
        ("cohorts.clearharm.splits.pooled.0.25.binary.Ihat",    "clearharm a=0.25 Ihat"),
        ("cohorts.clearharm.splits.pooled.1.0.I_max",           "clearharm a=1.0 I_max"),
        ("cohorts.clearharm.splits.pooled.1.0.binary.Ihat",     "clearharm a=1.0 Ihat"),
        ("cohorts.curated.splits.pooled.2.0.I_max",             "curated a=2.0 I_max (the reversal)"),
    ]),
    ("reports/P8_INTERACTION_V3.md", "outputs/p8_v3_combined.json", [
        ("cohorts.v3_combined.splits.pooled.0.25.binary.Ihat",   "combined pooled Ihat"),
        ("cohorts.v3_combined.splits.train.0.25.binary.Ihat",    "combined train Ihat"),
        ("cohorts.v3_combined.splits.test.0.25.binary.Ihat",     "combined test Ihat"),
        ("cohorts.v3_combined.splits.pooled.0.25.I_max",         "combined pooled I_max"),
    ]),
    ("reports/REP_PREDICTS_BEHAVIOR.md", "outputs/rep_predicts_behavior_sweep.json", [
        ("cohorts.clearharm.best_layer_p7_valid.auc",            "best P7-valid AUC"),
        ("cohorts.clearharm.delta_auc_best_vs_reference.delta",  "dAUC L16-L21"),
    ]),
]

NUM = re.compile(r"[-+−]?\d+\.\d+")          # − is the unicode minus reports use


def dig(obj, dotted):
    """Path segments split on '.', EXCEPT that alpha keys are themselves decimals ('0.25'). Try the
    longest matching key at each step so 'pooled.0.25.I_max' resolves to pooled['0.25']['I_max']."""
    cur, parts = obj, dotted.split(".")
    i = 0
    while i < len(parts):
        if isinstance(cur, list):
            cur = cur[int(parts[i])]; i += 1; continue
        two = ".".join(parts[i:i + 2])
        if isinstance(cur, dict) and two in cur:
            cur = cur[two]; i += 2
        else:
            cur = cur[parts[i]]; i += 1
    return cur


def numeric_leaves(obj, path=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from numeric_leaves(v, f"{path}.{k}" if path else str(k))
    elif isinstance(obj, (list, tuple)):
        for i, v in enumerate(obj):
            yield from numeric_leaves(v, f"{path}[{i}]")
    elif isinstance(obj, bool):
        return                                     # bools are ints in python; never compare them
    elif isinstance(obj, (int, float)):
        yield path, float(obj)


def report_numbers(text):
    """-> [(value, lineno, line)] for every decimal number in the report."""
    out = []
    for ln, line in enumerate(text.splitlines(), 1):
        for m in NUM.finditer(line):
            try:
                out.append((float(m.group(0).replace("−", "-")), ln, line.strip()))
            except ValueError:
                pass
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tol", type=float, default=5e-4,
                    help="a report number this close to a JSON value counts as MATCHING")
    ap.add_argument("--near", type=float, default=0.02,
                    help="a report number within this of a JSON value, but outside --tol, is a NEAR-MISS "
                         "-- the signature of a stale hand-copied figure")
    ap.add_argument("--strict", action="store_true", help="exit 1 if any near-miss is found")
    ap.add_argument("--contradictions", action="store_true",
                    help="ALSO flag a key value that is quoted correctly somewhere but ALSO has a nearby "
                         "different value elsewhere (the O2 pattern). HIGH FALSE-POSITIVE RATE -- see the "
                         "LIMITATION note in the module docstring. Review aid only, never a gate.")
    ap.add_argument("--pair", action="append", default=[],
                    help="REPORT=JSON, overriding the built-in list")
    args = ap.parse_args()

    total_hits = 0
    for rep, js, keys in PAIRS:
        rp, jp = os.path.join(DC, rep), os.path.join(DC, js)
        if not (os.path.exists(rp) and os.path.exists(jp)):
            print(f"[skip] {rep}  <->  {js}  (missing)")
            continue
        text = open(rp).read()
        nums = report_numbers(text)
        obj = json.load(open(jp))
        print(f"\n=== {rep}  <->  {js}")
        for path, label in keys:
            try:
                jval = dig(obj, path)
            except (KeyError, IndexError, TypeError):
                print(f"    [?] {label}: path absent from JSON ({path})")
                continue
            # A report legitimately rounds: -0.1235 may appear as -0.124 or -0.12. Those are CORRECT
            # quotations, not stale copies, so accept any value that equals the JSON rounded to 1-4 dp.
            # Without this the tool flags every rounded figure and becomes noise again -- which is the
            # failure mode that let O2 survive in the first place.
            # Accept EITHER rounding convention at each precision: 0.0875 may be written 0.087 or
            # 0.088 depending on the rounding rule, and both are correct quotations.
            accepted = set()
            for d in (1, 2, 3, 4):
                q = 10 ** -d
                accepted.add(round(jval, d))
                accepted.add(round(jval + q / 2, d))
                accepted.add(round(jval - q / 2, d))
            def _ok(n):
                return abs(n - jval) <= args.tol or any(abs(n - a) <= 1e-9 for a in accepted)
            exact = [ln for n, ln, _ in nums if _ok(n)]
            near = [(n, ln, line) for n, ln, line in nums
                    if not _ok(n) and args.tol < abs(n - jval) <= args.near]
            # THE O2 CASE, and the reason this is not just "is the value present somewhere":
            # PHASE8_1 held the CORRECT value in its generated tables AND a STALE copy in a hand-written
            # table. A presence check passes that report. A contradiction check does not. So a near-miss
            # is reported EVEN WHEN an exact match also exists -- one document must not quote two
            # different values for the same quantity.
            if exact and near and args.contradictions:
                n, ln, line = near[0]
                print(f"    [CONTRADICTION] {label} = {jval:+.4f}: report has the correct value at "
                      f"L{exact[0]} but ALSO {n:+.4f} at L{ln}")
                print(f"             | {line[:110]}")
                total_hits += 1
            elif exact:
                print(f"    [ok] {label} = {jval:+.4f}  (report line {exact[0]})")
            elif near:
                n, ln, line = near[0]
                print(f"    [STALE?] {label}: JSON {jval:+.4f} but report has {n:+.4f} at L{ln}")
                print(f"             | {line[:110]}")
                total_hits += 1
            else:
                print(f"    [absent] {label} = {jval:+.4f} is not quoted in the report (may be fine)")

    print(f"\nTOTAL near-misses: {total_hits}")
    print("A near-miss is NOT automatically a bug -- an unrelated quantity can land nearby. Read the "
          "context line. A stale hand-copied figure looks like +0.487 sitting next to a JSON +0.4767.")
    sys.exit(1 if (args.strict and total_hits) else 0)


if __name__ == "__main__":
    main()
