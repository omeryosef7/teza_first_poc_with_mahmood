#!/usr/bin/env python
"""Build a judge manifest (tag:gens_dir) for one RBD bank, from COMPLETED runs only.

WHY THIS IS A SCRIPT AND NOT A SHELL ONE-LINER. `judge_boombness` reads `gens.jsonl`, NOT
`DONE.json`, and `score_behavior` flushes that file every row -- so a killed job leaves a partial,
silently judgeable `gens.jsonl`. `judge_p2.sh` checks completeness only on its OWN outputs, never on
its inputs. This script therefore refuses any run without a `DONE.json` whose `rows_written`
matches the expected count, and refuses a tag that resolves to more than one run directory.

All arms of a contrast must land in ONE manifest: the judge takes one bank per invocation, and ~5%
of binary ASR labels flip between invocations on byte-identical text, which does NOT cancel in an
arm-vs-arm contrast.
"""
from __future__ import annotations
import argparse, glob, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def resolve(tag: str, expect_rows: int) -> str:
    hits = sorted(glob.glob(os.path.join(ROOT, "outputs/boombness/score_behavior", tag + "_2026*")))
    if not hits:
        raise SystemExit(f"REFUSING: no run directory for tag {tag!r}")
    done = [d for d in hits if os.path.exists(os.path.join(d, "DONE.json"))]
    if len(done) != 1:
        raise SystemExit(f"REFUSING: tag {tag!r} resolves to {len(done)} COMPLETED run(s) "
                         f"{[os.path.basename(d) for d in done]}; a manifest entry must be "
                         f"unambiguous")
    d = done[0]
    if os.path.exists(os.path.join(d, "ABORTED.json")):
        raise SystemExit(f"REFUSING: {d} is ABORTED")
    rw = json.load(open(os.path.join(d, "DONE.json"))).get("rows_written")
    if rw != expect_rows:
        raise SystemExit(f"REFUSING: {os.path.basename(d)} wrote {rw} rows, expected {expect_rows}")
    n_gen = sum(1 for line in open(os.path.join(d, "gens.jsonl")) if line.strip())
    if n_gen != expect_rows:
        raise SystemExit(f"REFUSING: {os.path.basename(d)} gens.jsonl has {n_gen} rows, "
                         f"expected {expect_rows}")
    return d


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--tag", action="append", required=True)
    ap.add_argument("--expect-rows", type=int, required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    lines = []
    for t in a.tag:
        d = resolve(t, a.expect_rows)
        lines.append(f"{t}:{d}")
        print(f"  ok {t} -> {os.path.basename(d)}")
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w") as f:
        f.write("\n".join(lines) + "\n")
    print(f"wrote {a.out} with {len(lines)} arms (expect_rows={a.expect_rows})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
