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


def git_commit_safe() -> str:
    """Provenance that cannot kill the analysis. Added 2026-08-22 after two crashes.

    `git rev-parse HEAD` raises FileNotFoundError on the batch nodes -- they have no git binary --
    and callers invoke it INSIDE the literal that builds the output dict, so the run dies before
    writing anything and the artifact on disk silently keeps its previous contents while `sacct`
    says FAILED. A stale file that reads as current is the worst failure mode available, and it
    happened twice: to analyze_qwen3_decomposition.py, then to analyze_dissociation.py after only
    the first was fixed and its siblings left alone.

    The SLURM wrappers export BOOMB_GIT_COMMIT from the submitting host, so real provenance is
    preserved; absent that this degrades to an explicit marker rather than to silence.
    """
    import os as _os
    import subprocess as _sp
    env = _os.environ.get("BOOMB_GIT_COMMIT")
    if env:
        return env.strip()
    try:
        _kw = {"capture_output": True, "text": True}
        _repo = globals().get("REPO")
        if _repo:
            _kw["cwd"] = _repo
        r = _sp.run(["git", "rev-parse", "HEAD"], **_kw)
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout.strip()
        return f"unavailable:git_rc_{r.returncode}"
    except (FileNotFoundError, OSError) as exc:
        return f"unavailable:{type(exc).__name__}"


def git_dirty_safe(*args) -> object:
    """Companion for the `git status --porcelain` dirty-flag calls. Never raises."""
    import subprocess as _sp
    try:
        _kw = {"capture_output": True, "text": True}
        _repo = globals().get("REPO")
        if _repo:
            _kw["cwd"] = _repo
        return bool(_sp.run(["git", "status", "--porcelain", *args], **_kw).stdout.strip())
    except (FileNotFoundError, OSError):
        return None



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
                          "git_commit": git_commit_safe()}}
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
