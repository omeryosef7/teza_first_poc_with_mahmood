#!/usr/bin/env python3
"""Judge validation sampler (plan sec 6.6). Draws a stratified sample of
(prompt, response, judge_score) triples from EXISTING StrongREJECT-scored outputs
for HUMAN annotation, so we can measure judge false-positive / false-negative rates
before freezing the judge. Does not call any judge itself (reuse only).

Stratifies across score bins so the sheet includes clear successes, clear refusals,
and ambiguous/partial cases (plan sec 6.6).

Usage:
  python scripts/build_judge_validation_sample.py \
      --inputs outputs/*_strongreject.jsonl \
      --per-bin 8 --out docs/judge_validation_sample.csv

Output CSV columns: id, source_file, goal, response_excerpt, strongreject_score,
strongreject_is_success, score_bin, human_label(BLANK), human_notes(BLANK).
Deterministic (sorted + fixed seed). No GPU, no network.
"""
import argparse
import csv
import glob
import json
import random
from pathlib import Path

BINS = [(0.0, 0.01, "refusal_0"), (0.01, 0.5, "partial_lo"),
        (0.5, 0.9, "partial_hi"), (0.9, 1.01, "success_1")]


def bin_of(score):
    for lo, hi, name in BINS:
        if lo <= score < hi:
            return name
    return "unknown"


def response_field(row):
    for k in ("target_response", "response", "output", "generation"):
        if k in row and row[k]:
            return str(row[k])
    return ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--inputs", nargs="+", required=True,
                    help="glob(s) for *_strongreject.jsonl scored files")
    ap.add_argument("--per-bin", type=int, default=8)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--excerpt-chars", type=int, default=600)
    ap.add_argument("--out", default="docs/judge_validation_sample.csv")
    args = ap.parse_args()

    files = []
    for pat in args.inputs:
        files.extend(sorted(glob.glob(pat)))
    files = sorted(set(files))
    if not files:
        raise SystemExit("no input files matched")

    pool = {name: [] for _, _, name in BINS}
    for fp in files:
        with open(fp) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                r = json.loads(line)
                if "strongreject_score" not in r or r["strongreject_score"] is None:
                    continue
                score = float(r["strongreject_score"])
                b = bin_of(score)
                if b in pool:
                    pool[b].append((fp, r, score))

    rng = random.Random(args.seed)
    rows = []
    cid = 0
    for _, _, name in BINS:
        items = sorted(pool[name], key=lambda t: (t[0], t[1].get("goal_index", 0),
                                                  t[1].get("goal", "")))
        rng.shuffle(items)
        for fp, r, score in items[:args.per_bin]:
            resp = response_field(r).replace("\n", " ")[:args.excerpt_chars]
            # field name varies: GCG pipeline uses strongreject_is_success,
            # older hijacking baselines use is_success. Fall back to threshold.
            is_succ = r.get("strongreject_is_success",
                            r.get("is_success", score >= 0.5))
            rows.append({
                "id": cid,
                "source_file": Path(fp).name,
                "goal": r.get("goal", "")[:300],
                "response_excerpt": resp,
                "strongreject_score": score,
                "strongreject_is_success": is_succ,
                "score_bin": name,
                "human_label": "",   # annotator fills: success / refusal / partial
                "human_notes": "",
            })
            cid += 1

    if not rows:
        raise SystemExit("no scored rows found in inputs (no valid strongreject_score); "
                         "nothing to sample")
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    counts = {name: min(len(pool[name]), args.per_bin) for _, _, name in BINS}
    print(f"[ok] wrote {len(rows)} rows to {out}")
    print(f"[bins] {counts}  (pool sizes: {{{', '.join(f'{n}:{len(pool[n])}' for _,_,n in BINS)}}})")


if __name__ == "__main__":
    main()
