"""run_index.py — "has this already been run?", answered by CONFIGURATION rather than by tag.

WHY THIS EXISTS, and it is two demonstrated costs rather than a hypothetical:

  * §12.21 — I launched cap-640 reruns for `main`, `ticket_bomb` and `basket_gun`. Six
    configuration-identical runs (`e6A_*`/`e6C_*`) already existed. Generation is deterministic:
    384 of 384 rows came back byte-identical. Pure waste, and my "first untruncated evidence"
    claim was false because of it.
  * §23 — a peer nearly spent GPU on the Qwen3 × `main` legacy cell. It had been measured four days
    earlier. Their note tracked the gap BY TAG while the data is organised by
    `(bank, model, arm)`, so scanning for the tag could not see it.

**The defect in both is the same: the question was asked in one index and the answer was filed under
another.** Every earlier remedy in this sprint — enumerate-then-filter, reachability, distinctiveness
— assumes you know *where* to look. This one answers "does a run with THIS CONFIGURATION exist"
without needing a tag, a date, or a directory name.

It is a QUERY TOOL, not a guard. It has no pass/fail, is not in `check_all`, and cannot fail a
commit: there is no correct number of matching runs, only a fact to look at before spending GPU.

Reads `config.json` and counts rows. No model, no network.
"""
from __future__ import annotations

import argparse
import glob
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))

#: Fields that define WHAT AN ARM IS. Two runs agreeing on all of these are the same experiment, and
#: because generation is greedy/deterministic (§12.21: 384/384 byte-identical across nodes and days)
#: the second one buys nothing. `tag` is deliberately EXCLUDED -- indexing by tag is the failure.
IDENTITY = ("bank", "model", "arm", "query_kinds", "conditions", "bank_blocks",
            "n_examples", "max_new", "intervene", "knockout_scope", "dtype", "seed")

ROW_FILE = {"score_behavior": "results.jsonl", "extract_boombness": "results.jsonl",
            "retrieval_strength": "retrieval.jsonl"}


def scan(roots=None):
    out = []
    for root, rowfile in sorted(ROW_FILE.items()):
        if roots and root not in roots:
            continue
        for d in sorted(glob.glob(os.path.join(ROOT, "outputs", "boombness", root, "*/"))):
            try:
                cfg = json.load(open(os.path.join(d, "config.json"), encoding="utf-8"))["args"]
            except Exception:
                continue
            rows = 0
            rp = os.path.join(d, rowfile)
            if os.path.isfile(rp):
                rows = sum(1 for _ in open(rp, encoding="utf-8", errors="ignore"))
            out.append({
                "root": root,
                "run": os.path.basename(d.rstrip("/")),
                "done": os.path.isfile(os.path.join(d, "DONE.json")),
                "aborted": os.path.isfile(os.path.join(d, "ABORTED.json")),
                "rows": rows,
                "expect_n": cfg.get("expect_n"),
                **{k: (os.path.basename(str(cfg.get(k))) if k == "bank" else cfg.get(k))
                   for k in IDENTITY},
            })
    return out


def identity(r):
    return tuple(str(r.get(k)) for k in IDENTITY)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    for k in IDENTITY:
        ap.add_argument("--" + k.replace("_", "-"), default=None,
                        help=f"substring match on {k}")
    ap.add_argument("--root", default=None, help="score_behavior | extract_boombness | ...")
    ap.add_argument("--duplicates", action="store_true",
                    help="report CONFIGURATION-IDENTICAL run groups instead of a query")
    a = ap.parse_args()
    runs = scan([a.root] if a.root else None)

    if a.duplicates:
        groups = {}
        for r in runs:
            if r["done"]:
                groups.setdefault(identity(r), []).append(r)
        dups = {k: v for k, v in groups.items() if len(v) > 1}
        print(f"[run-index] {len(runs)} runs scanned; {len(dups)} configuration-identical groups "
              f"covering {sum(len(v) for v in dups.values())} finished runs")
        for k, v in sorted(dups.items(), key=lambda kv: -len(kv[1]))[:20]:
            d = dict(zip(IDENTITY, k))
            print(f"  {len(v)}x  bank={d['bank'][:34]} model={str(d['model'])[:16]} "
                  f"arm={d['arm']} cap={d['max_new']}")
            for r in v:
                print(f"        {r['run'][:46]:48s} rows={r['rows']}")
        return 0

    sel = [r for r in runs
           if all(getattr(a, k) is None or getattr(a, k).lower() in str(r.get(k)).lower()
                  for k in IDENTITY)]
    print(f"[run-index] {len(sel)} of {len(runs)} runs match")
    for r in sorted(sel, key=lambda r: r["run"]):
        state = "DONE" if r["done"] else ("ABORTED" if r["aborted"] else "unfinished")
        short = "" if not r["expect_n"] or r["rows"] >= r["expect_n"] else "  ⛔SHORT"
        print(f"  {r['run'][:44]:46s} {state:10s} rows={r['rows']:<6d} cap={r['max_new']} "
              f"arm={r['arm']}{short}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
