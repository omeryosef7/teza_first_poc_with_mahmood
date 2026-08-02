#!/usr/bin/env python3
"""Phase-2 adapter: locked Doublespeak split -> the bench schema 32_extract_pair_reps.py reads.

32_extract_pair_reps.py consumes bench["semantic"] rows with fields:
  condition, split, prompt, probe_word, sid, readout, demo_style, n_demos
and 33_build_directions.py then computes per-(condition,split,component,position,layer):
  d_Direct = mean(DIRECT_CONCEPT) - mean(NEUTRAL_CODEWORD)      (concept_direction)
  d_DS     = mean(DOUBLESPEAK)    - mean(NEUTRAL_CODEWORD)      (doublespeak_signature)
  d_benign/d_unrelated                                          (controls)

This emits ONE bench file per cohort (clearharm PRIMARY, curated REPLICATION) so directions are
fit per cohort. Condition/split names are mapped to the 33 vocabulary; probe_word is the swapped
token (concept for DIRECT_CONCEPT, codeword elsewhere) so reps are captured at matched positions.

Usage:
  python scripts/split_to_bench.py --split data/splits/clearharm_doublespeak_v1.json --out-dir data/bench
Outputs: data/bench/bench_<cohort>.json  (each {"_meta":..., "semantic":[...]})
"""
from __future__ import annotations
import argparse, json, os

# split condition field -> (33 condition name, probe uses concept?)
COND_MAP = {
    "doublespeak_prompt": ("DOUBLESPEAK", False),
    "neutral_prompt":     ("NEUTRAL_CODEWORD", False),
    "direct_prompt":      ("DIRECT_CONCEPT", True),
    "benign_prompt":      ("BENIGN_REMAP", False),
    "shuffled_prompt":    ("SHUFFLED_BINDING", False),
    "unrelated_prompt":   ("UNRELATED_TARGET", False),
}
SPLIT_MAP = {"train": "dev", "test": "heldout", "dev": "dev", "heldout": "heldout"}
READOUT = "fixed"  # our prompts already carry their suffix; single readout template


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", default="data/splits/clearharm_doublespeak_v1.json")
    ap.add_argument("--out-dir", default="data/bench")
    ap.add_argument("--num-demos", type=int, default=12)
    args = ap.parse_args()

    obj = json.load(open(args.split))
    examples = obj["examples"]
    meta = obj.get("_meta", {})
    by_cohort = {}
    for e in examples:
        by_cohort.setdefault(e["cohort"], []).append(e)

    os.makedirs(args.out_dir, exist_ok=True)
    written = {}
    for cohort, exs in by_cohort.items():
        rows = []
        for e in exs:
            split = SPLIT_MAP.get(e["split"], e["split"])
            for field, (cond, use_concept) in COND_MAP.items():
                if field not in e:
                    continue
                probe = e["target_concept"] if use_concept else e["codeword"]
                rows.append({
                    "sid": e["example_id"],
                    "condition": cond,
                    "split": split,
                    "prompt": e[field],
                    "probe_word": probe,
                    "readout": READOUT,
                    "demo_style": meta.get("generator", "gpt-4o-mini"),
                    "n_demos": args.num_demos,
                    "cohort": cohort,
                    "target_concept": e["target_concept"],
                    "codeword": e["codeword"],
                })
        out = {
            "_meta": {
                "source_split": args.split,
                "cohort": cohort,
                "dataset_revision": meta.get("dataset_revision"),
                "conditions": sorted({r["condition"] for r in rows}),
                "n_rows": len(rows),
                "n_examples": len(exs),
                "note": "adapter output for 32_extract_pair_reps.py --readout fixed",
            },
            "semantic": rows,
        }
        path = os.path.join(args.out_dir, f"bench_{cohort}.json")
        json.dump(out, open(path, "w"), indent=1)
        written[cohort] = (path, len(rows), len(exs))

    import collections
    for cohort, (path, nrows, nex) in written.items():
        rows = json.load(open(path))["semantic"]
        per = collections.Counter((r["condition"], r["split"]) for r in rows)
        print(f"{path}: {nrows} rows / {nex} examples")
        for k in sorted(per):
            print(f"    {k}: {per[k]}")


if __name__ == "__main__":
    main()
