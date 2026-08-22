"""shard_citation_check.py — find numbers computed on HALF a judged run.

THE BUG CLASS, AND WHY A SCANNER RATHER THAN A FIX.

A judged run is often split across several judge directories that are DISJOINT shards of one
population: `vL12J0` + `vL12J1` = 248 + 247 = 495 distinct prompt ids, no overlap. Any analysis that
picks one of them and calls it the run is computing over half the data. This is retraction C-11, and it
has now been found three separate times:

  * C-11 itself, in the judge-pass assembly;
  * audit #13, in `unanalysed_triage.py` (12 full-strength arms triaged as "underpowered");
  * this tick, in `replicate_noise.py` -- a script written an hour earlier, where it silently dropped
    the very pairs the script existed to measure.

Fifty scripts in this repo read `results.jsonl`, most with their own shard handling, so the bug will
recur. This does not try to fix fifty scripts. It looks for where the bug has ALREADY landed: every
committed artifact that names one shard of a sharded run and does not name its siblings.

WHAT A HIT MEANS. Not automatically an error -- an artifact may legitimately reference a single shard
as provenance, or analyse shards separately on purpose. It means a number in that artifact may have
been computed over a fraction of the population, and the artifact should say which. What it removes is
the ability to not know.

Reads judge `results.jsonl` for `prompt_id` only, and artifacts as text.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from unanalysed_inventory import git_commit_safe  # noqa: E402

INDEXES = ("unanalysed_inventory.json", "unanalysed_triage.json", "shard_citation_check.json",
           "replicate_noise.json")


def ids_of(d):
    out = set()
    f = os.path.join(d, "results.jsonl")
    if not os.path.exists(f):
        return out
    for line in open(f, encoding="utf-8"):
        try:
            pid = json.loads(line).get("prompt_id")
        except Exception:
            continue
        if pid is not None:
            out.add(pid)
    return out


def gens_of(d):
    try:
        a = json.load(open(os.path.join(d, "config.json")))
        a = a.get("args", a)
        g = str(a.get("gens") or "").rstrip("/")
        return os.path.dirname(g) if g.endswith("gens.jsonl") else g
    except Exception:
        return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    by_gens = defaultdict(list)
    for d in sorted(glob.glob("outputs/boombness/judge/*")):
        if not os.path.isdir(d):
            continue
        g = gens_of(d)
        if g:
            by_gens[g].append(d)

    sharded = []
    for g, dirs in by_gens.items():
        if len(dirs) < 2:
            continue
        idsets = {d: ids_of(d) for d in dirs}
        overlap = False
        seen = set()
        for d, s in idsets.items():
            if seen & s:
                overlap = True
            seen |= s
        if overlap:
            continue                       # re-judgings, not shards
        sharded.append({"gens": os.path.basename(g),
                        "shards": [os.path.basename(d) for d in dirs],
                        "sizes": [len(idsets[d]) for d in dirs],
                        "union": len(seen)})

    findings = []
    for p in sorted(glob.glob("outputs/boombness/*.json")
                    + glob.glob("outputs/boombness/*/*.json")):
        if os.path.basename(p) in INDEXES:
            continue
        try:
            blob = open(p, encoding="utf-8").read()
        except OSError:
            continue
        for s in sharded:
            named = [x for x in s["shards"] if x in blob]
            if named and len(named) < len(s["shards"]):
                findings.append({
                    "artifact": os.path.relpath(p),
                    "gens": s["gens"],
                    "named_shards": named,
                    "missing_shards": [x for x in s["shards"] if x not in named],
                    "rows_named": sum(sz for x, sz in zip(s["shards"], s["sizes"]) if x in named),
                    "rows_total": s["union"],
                })

    out = {
        "question": "does any committed artifact cite one shard of a disjoint-sharded judged run "
                    "without its siblings?",
        "why": "C-11's bug class. Found three times: C-11 itself, audit #13 in unanalysed_triage, and "
               "replicate_noise.py an hour after it was written. 50 scripts read results.jsonl with "
               "their own shard handling, so it will recur; this finds where it has already landed.",
        "a_hit_is_not_automatically_an_error": (
            "an artifact may cite one shard as provenance, or analyse shards separately on purpose. A "
            "hit means a number in it MAY be over a fraction of the population and the artifact should "
            "say which. What this removes is the ability to not know."),
        "n_sharded_runs": len(sharded),
        "n_findings": len(findings),
        "findings": sorted(findings, key=lambda f: f["rows_named"] / max(f["rows_total"], 1)),
        "sharded_runs": sorted(sharded, key=lambda s: s["gens"]),
        "provenance": {"argv": sys.argv, "git_commit": git_commit_safe()},
    }
    with open(a.out, "w") as f:
        json.dump(out, f, indent=2)

    print(f"disjoint-sharded judged runs: {len(sharded)}")
    print(f"artifacts citing a partial shard set: {len(findings)}\n")
    for f_ in out["findings"][:20]:
        print(f"  {f_['artifact'][:52]:54s} {f_['rows_named']}/{f_['rows_total']} rows  "
              f"({len(f_['named_shards'])}/{len(f_['named_shards']) + len(f_['missing_shards'])} shards)")
        print(f"      gens={f_['gens'][:44]}  missing={f_['missing_shards']}")
    print(f"\n[shard-citation] -> {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
