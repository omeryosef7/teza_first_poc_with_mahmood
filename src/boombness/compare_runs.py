"""compare_runs.py — assert two runs produced the same numbers.

Used whenever an optimization or refactor is supposed to be behaviour-preserving. The whole
point of the sprint is that a silent numerical change is indistinguishable from a real result,
so "it still runs" is not evidence: this compares every shared scalar column, row by row, keyed
on the identity columns.

Exit code is non-zero if any column differs beyond --tol, so it can gate a submission.
"""
from __future__ import annotations

import argparse
import collections
import json
import math
import os
import sys
from typing import Dict, List, Tuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import read_jsonl  # noqa: E402

DEFAULT_KEYS = "prompt_id,occurrence_index"


def key_of(row: Dict, keys: List[str]) -> Tuple:
    return tuple(row.get(k) for k in keys)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--a", required=True, help="run dir A")
    ap.add_argument("--b", required=True, help="run dir B")
    ap.add_argument("--keys", default=DEFAULT_KEYS)
    ap.add_argument("--tol", type=float, default=1e-5,
                    help="absolute tolerance; float32 reductions in a different order differ "
                         "at ~1e-6, so the default is deliberately tight but not exact")
    ap.add_argument("--file", default="results.jsonl")
    ap.add_argument("--soft-cols", default="rank",
                    help="substring; columns matching are compared but do NOT fail the run. "
                         "Default 'rank': the logit-lens rank is ill-conditioned in the flat "
                         "tail of the distribution (a 1e-7 logit change moves it by ~300 of "
                         "128256), so it is a diagnostic, not a quantity to gate on.")
    args = ap.parse_args()

    keys = [k.strip() for k in args.keys.split(",") if k.strip()]
    A = read_jsonl(os.path.join(args.a, args.file))
    B = read_jsonl(os.path.join(args.b, args.file))
    ia = {key_of(r, keys): r for r in A}
    ib = {key_of(r, keys): r for r in B}

    only_a = sorted(set(ia) - set(ib))
    only_b = sorted(set(ib) - set(ia))
    shared = sorted(set(ia) & set(ib))
    print(f"[compare] A={len(A)} rows  B={len(B)} rows  shared={len(shared)}  "
          f"only_A={len(only_a)}  only_B={len(only_b)}")

    numeric_cols = sorted({k for r in A[:50] for k, v in r.items()
                           if isinstance(v, (int, float)) and not isinstance(v, bool)}
                          & {k for r in B[:50] for k, v in r.items()
                             if isinstance(v, (int, float)) and not isinstance(v, bool)})
    worst: Dict[str, float] = collections.defaultdict(float)
    n_bad = 0
    examples: Dict[str, List[str]] = collections.defaultdict(list)
    for k in shared:
        ra, rb = ia[k], ib[k]
        for c in numeric_cols:
            va, vb = ra.get(c), rb.get(c)
            if va is None or vb is None:
                continue
            if not (math.isfinite(va) and math.isfinite(vb)):
                if math.isfinite(va) != math.isfinite(vb):
                    n_bad += 1
                    if len(examples[c]) < 3:
                        examples[c].append(f"{k}: {va} vs {vb}")
                continue
            d = abs(va - vb)
            if d > worst[c]:
                worst[c] = d
            if d > args.tol:
                n_bad += 1
                if len(examples[c]) < 3:
                    examples[c].append(f"{k}: {va:.8g} vs {vb:.8g} (|d|={d:.3g})")

    def is_soft(c):
        return bool(args.soft_cols) and args.soft_cols in c

    bad_cols = {c: worst[c] for c in worst if worst[c] > args.tol and not is_soft(c)}
    soft_cols = {c: worst[c] for c in worst if worst[c] > args.tol and is_soft(c)}
    print(f"[compare] {len(numeric_cols)} numeric columns compared; "
          f"{len(bad_cols)} HARD failures, {len(soft_cols)} soft ({args.soft_cols}) "
          f"exceed tol={args.tol}; {n_bad} cell mismatches")
    for c in sorted(worst, key=lambda c: -worst[c])[:12]:
        flag = ("SOFT" if is_soft(c) else "FAIL") if worst[c] > args.tol else "ok  "
        print(f"  {flag} {c:34s} max|Δ| = {worst[c]:.3g}")
        for e in examples.get(c, []):
            print(f"        {e}")

    verdict = {"a": os.path.abspath(args.a), "b": os.path.abspath(args.b),
               "n_rows_a": len(A), "n_rows_b": len(B), "n_shared": len(shared),
               "n_only_a": len(only_a), "n_only_b": len(only_b),
               "tol": args.tol, "n_numeric_cols": len(numeric_cols),
               "n_cell_mismatches": n_bad,
               "hard_fail_columns": bad_cols, "soft_diff_columns": soft_cols,
               "max_abs_diff": {c: worst[c] for c in sorted(worst, key=lambda c: -worst[c])[:30]},
               "identical": bool(not bad_cols and not only_a and not only_b)}
    print(json.dumps({"identical": verdict["identical"]}))
    out = os.path.join(args.b, "compare_to_previous.json")
    with open(out, "w") as f:
        json.dump(verdict, f, indent=2)
    print(f"[compare] -> {out}")
    return 0 if verdict["identical"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
