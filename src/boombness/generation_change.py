"""generation_change.py — what fraction of generations an intervention actually changes.

WHY. The report argued that an intervention outside the causal band is not a *failed* intervention:
it changes a large share of generations while changing compliance on none. That argument needs the
share, and the 2026-08-21 audit found the two figures it quotes ("34.9%", "29.5%") appear in **no
artifact** — a sweep of every float under `outputs/` at 1e-6 found neither. They were prose.

They are, however, computable from the committed `gens.jsonl` in seconds, which is the right response:
source the number rather than withdraw it. This script does that and writes the result, so the claim
is regenerable instead of remembered.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import subprocess
import sys


def _gens(pat: str):
    hits = sorted(glob.glob(pat))
    if not hits:
        raise SystemExit(f"[genchange] no run matching {pat!r}")
    d = hits[-1]
    p = os.path.join(d, "gens.jsonl")
    if not os.path.exists(p):
        raise SystemExit(f"[genchange] {d} has no gens.jsonl")
    return d, {json.loads(l)["prompt_id"]: json.loads(l).get("generation", "")
               for l in open(p)}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--baseline", required=True)
    ap.add_argument("--arm", action="append", required=True, metavar="NAME:GLOB")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    bd, base = _gens(args.baseline)
    out = {"baseline": os.path.abspath(bd), "n_baseline": len(base), "arms": {},
           "note": "a changed generation is a byte difference against the baseline completion for "
                   "the same prompt_id; generation is deterministic here (verified 660/660 identical "
                   "across two runs of the same config), so a difference is the intervention, not noise",
           "provenance": {"argv": sys.argv,
                          "git_commit": subprocess.run(["git", "rev-parse", "HEAD"],
                                                       capture_output=True, text=True).stdout.strip()}}
    for spec in args.arm:
        name, pat = spec.split(":", 1)
        d, g = _gens(pat)
        common = sorted(set(base) & set(g))
        diff = sum(1 for p in common if base[p] != g[p])
        out["arms"][name] = {"run": os.path.abspath(d), "n_common": len(common),
                             "n_changed": diff,
                             "frac_changed": diff / len(common) if common else None}
        print(f"  {name:24s} {diff:>4d}/{len(common):<4d} = {100*diff/max(len(common),1):.1f}%  "
              f"{os.path.basename(d)[:34]}")
    with open(args.out, "w") as f:
        json.dump(out, f, indent=2)
    print(f"[genchange] -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
