"""unanalysed_inventory.py — what has this sprint GENERATED but never ANALYSED?

WHY. Three consecutive audits ended the same way: the answer to a serious objection was already in
committed data. The refusal-transition decomposition, the layer-profile scan statistic and the
disruption-matched control were all computed from runs that had been sitting on disk for days. The
sprint has over-generated evidence and under-analysed it — a far more recoverable failure than the
reverse, but only if someone looks.

This looks. It walks the pipeline stages and reports the drop-offs:

    score_behavior (gens) -> judge (scores) -> an analysis artifact that cites the judge run

A run that produced generations nobody judged, or a judge run no artifact cites, is evidence the
sprint paid GPU or API money for and never used. That is not automatically a defect — a smoke test
should not be judged, and a deliberately abandoned arm should not be either — so this prints an
inventory to read, not a pass/fail. It deliberately does NOT try to decide which gaps matter.

It also flags the opposite failure, which is worse: a run that is INCOMPLETE (no DONE.json) but has
been judged anyway, i.e. a number computed over a truncated prefix.
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



def _n(path: str) -> int:
    try:
        return sum(1 for _ in open(path))
    except OSError:
        return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default="outputs/boombness")
    ap.add_argument("--min-rows", type=int, default=100,
                    help="ignore runs smaller than this (smokes and pilots)")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    # which judge runs does any committed analysis artifact cite?
    cited = set()
    for p in glob.glob(os.path.join(args.root, "*.json")) + \
             glob.glob(os.path.join(args.root, "*", "*.json")):
        try:
            blob = open(p, encoding="utf-8").read()
        except OSError:
            continue
        if "/judge/" not in blob:
            continue
        for seg in blob.split("/judge/")[1:]:
            cited.add(seg.split('"')[0].split("/")[0])

    judged_gens = {}
    judge_rows = []
    for d in sorted(glob.glob(os.path.join(args.root, "judge", "*"))):
        if not os.path.isdir(d):
            continue
        cfg = os.path.join(d, "config.json")
        src = None
        if os.path.exists(cfg):
            try:
                a = json.load(open(cfg))
                a = a.get("args", a)
                # `--gens` may name the run DIRECTORY or the gens.jsonl inside it. The first
                # version took basename() unconditionally, so every judge run pointed at a file
                # resolved to the literal name "gens.jsonl", matched no generation run, and landed
                # in the "judged over an INCOMPLETE run" list -- the most alarming category this
                # script has. All 3 of its first-run hits were false positives; the sources were
                # DONE with 495 rows each. A checker whose worst category is wrong is worse than no
                # checker, so it is normalised here.
                g = str(a.get("gens") or "").rstrip("/")
                if g.endswith("gens.jsonl"):
                    g = os.path.dirname(g)
                src = os.path.basename(g)
            except Exception:
                pass
        n = _n(os.path.join(d, "results.jsonl"))
        if src:
            judged_gens.setdefault(src, []).append(os.path.basename(d))
        judge_rows.append({"judge": os.path.basename(d), "n": n, "source_gens": src,
                           "done": os.path.exists(os.path.join(d, "DONE.json")),
                           "cited_by_an_artifact": os.path.basename(d) in cited})

    gen_rows = []
    for d in sorted(glob.glob(os.path.join(args.root, "score_behavior", "*"))):
        if not os.path.isdir(d):
            continue
        n = _n(os.path.join(d, "gens.jsonl"))
        if n < args.min_rows:
            continue
        b = os.path.basename(d)
        gen_rows.append({"run": b, "n_gens": n,
                         "done": os.path.exists(os.path.join(d, "DONE.json")),
                         "judged_by": judged_gens.get(b, [])})

    unjudged = [g for g in gen_rows if not g["judged_by"]]
    uncited = [j for j in judge_rows if j["n"] >= args.min_rows and not j["cited_by_an_artifact"]]
    judged_incomplete = [j for j in judge_rows
                         if j["source_gens"] and j["n"] >= args.min_rows
                         and not any(g["run"] == j["source_gens"] and g["done"] for g in gen_rows)]

    out = {"root": os.path.abspath(args.root), "min_rows": args.min_rows,
           "n_generation_runs": len(gen_rows), "n_judge_runs": len(judge_rows),
           "generated_but_never_judged": unjudged,
           "judged_but_cited_by_no_artifact": uncited,
           "judged_over_an_INCOMPLETE_generation_run": judged_incomplete,
           "note": "an inventory to read, not a pass/fail. A smoke or a deliberately abandoned arm "
                   "SHOULD appear here. The third list is the one that matters most: a score "
                   "computed over a truncated prefix.",
           "provenance": {"argv": sys.argv,
                          "git_commit": git_commit_safe()}}
    with open(args.out, "w") as f:
        json.dump(out, f, indent=2)

    print(f"generation runs >= {args.min_rows} rows : {len(gen_rows)}")
    print(f"judge runs                            : {len(judge_rows)}")
    print(f"\nGENERATED BUT NEVER JUDGED ({len(unjudged)}):")
    for g in unjudged[:20]:
        print(f"   {g['run'][:52]:54s} {g['n_gens']:>5d} rows  done={g['done']}")
    print(f"\nJUDGED BUT CITED BY NO COMMITTED ARTIFACT ({len(uncited)}):")
    for j in uncited[:20]:
        print(f"   {j['judge'][:52]:54s} {j['n']:>5d} rows")
    print(f"\n*** JUDGED OVER AN INCOMPLETE GENERATION RUN ({len(judged_incomplete)}) ***")
    for j in judged_incomplete[:20]:
        print(f"   {j['judge'][:44]:46s} <- {str(j['source_gens'])[:40]}")
    print(f"\n[inventory] -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
