"""population_index.py — what population is each committed artifact actually about?

WHY. Three defects in one week came from the same move: a quantity measured on population X used to
support a statement about population Y.

  * R-21 — R-13's style artifact was measured on **Qwen3** and I exempted "the Llama results".
  * §18 point 3 — a **bank** effect was cited to §7c, the **external-set** evidence, which N13 says
    cannot answer the question.
  * the judge noise floor — measured on the **bank** (1.9 pp) and quoted against the **AdvBench**
    headline, whose own floor is **0.2 pp**, a 10x error in the reader's favour or against depending
    on which way it is read.

The direction of the error differed every time, so this is a shortcut rather than a bias, and the fix
is mechanical: make each artifact state its population loudly enough that a mismatch is visible when
someone cites it. This builds that index — one row per artifact, with the fields a reader needs to
tell whether two numbers are about the same thing.

It deliberately does NOT try to parse the report and match citations: that is a semantic problem, and
a checker that guesses would be worse than a table a human can scan.
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


BANK_HINTS = (("advbench", "AdvBench-495"), ("clearharm", "ClearHarm-179"),
              ("button", "bank(button)"), ("apple", "bank(apple)"),
              ("boombness_prompt_bank", "bank(carrot)"))


def _bank_of(blob: str):
    low = blob.lower()
    for needle, label in BANK_HINTS:
        if needle in low:
            return label
    return None


def fingerprint(path: str):
    try:
        d = json.load(open(path))
    except Exception:
        return None
    if not isinstance(d, dict):
        return None
    blob = json.dumps(d)[:200000]
    fp = {"artifact": os.path.relpath(path),
          "bank": _bank_of(blob),
          "model": None, "condition": d.get("condition") or d.get("arm"),
          "n": None, "n_clusters": None, "has_provenance": bool(d.get("provenance")),
          "plan_section": d.get("plan_section")}
    for k in ("model", "models"):
        if isinstance(d.get(k), str):
            fp["model"] = d[k]
    if fp["model"] is None:
        for m, lab in (("qwen", "Qwen3-14B"), ("llama", "Llama-3.1-8B")):
            if m in blob.lower():
                fp["model"] = lab
                break
    for k in ("n", "n_common", "n_judged", "n_rows"):
        if isinstance(d.get(k), int):
            fp["n"] = d[k]
            break
    for k in ("n_clusters", "n_domains"):
        if isinstance(d.get(k), int):
            fp["n_clusters"] = d[k]
            break
    return fp


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default="outputs/boombness")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    rows = []
    for p in sorted(glob.glob(os.path.join(args.root, "*.json"))):
        fp = fingerprint(p)
        if fp:
            rows.append(fp)
    out = {"note": "one row per top-level committed artifact. A citation that pairs two rows with "
                   "different `bank` or `model` is a population transfer and needs a stated reason.",
           "n_artifacts": len(rows), "rows": rows,
           "provenance": {"argv": sys.argv,
                          "git_commit": git_commit_safe()}}
    with open(args.out, "w") as f:
        json.dump(out, f, indent=2)
    miss = [r for r in rows if not r["bank"]]
    print(f"{'artifact':52s} {'bank':16s} {'model':16s} {'n':>6s} {'G':>4s} {'prov':>5s}")
    for r in rows:
        print(f"{r['artifact'][-52:]:52s} {str(r['bank'])[:16]:16s} {str(r['model'])[:16]:16s} "
              f"{str(r['n']):>6s} {str(r['n_clusters']):>4s} {'yes' if r['has_provenance'] else 'NO':>5s}")
    print(f"\n[popindex] {len(rows)} artifacts; {len(miss)} state no identifiable bank")
    print(f"[popindex] -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
