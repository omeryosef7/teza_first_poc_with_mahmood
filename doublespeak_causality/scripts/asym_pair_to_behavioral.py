#!/usr/bin/env python3
"""ASYMMETRY SPRINT — PHASE 4 prerequisite: pair_benchmark -> behavioural bench (CPU).

The five concept pairs live in `data/pair_benchmark/pair_carrot_{X}.json` as PRE-RENDERED
prompt strings, but every behavioural causal harness in this repo
(`scripts/phase_behav_refusal.py`, `scripts/phase10_powered_concept_ablation.py`,
`scripts/phase_x5_concept_qwen3.py`, `scripts/phase_refusal_projection.py`) consumes the
`data/behavioral_v3b/beh_clearharm.json` shape:

    {"_meta": {"cohort": ...},
     "items": [{"id", "harmful_instruction", "harmful_word", "codeword", "demos", "split"}, ...]}

and rebuilds the three conditions itself via `ds_common.build_conditions`. This script does
the conversion, losslessly and with the inversion asserted rather than assumed.

TWO THINGS THAT MUST NOT BE GOT WRONG
1. **n inflation.** A pair file holds 900 behavioural rows = 60 unique prompts (`pid`) x 5
   demo styles x 3 demo counts. Those are REPEATED RENDERINGS of the same prompt, so they do
   NOT increase n (plan §3.4). We keep exactly ONE row per `pid` — chosen by a fixed,
   content-independent rule (a stated `--demo-style`/`--n-demos`, else the lexicographically
   first available) so the choice cannot be tuned to an outcome.
2. **Split naming.** Pair files use `dev`/`heldout`; the harnesses use `train`/`test`.
   `dev -> train` and `heldout -> test`. The pair builder asserts demo-block disjointness at
   build time (`30_build_pair_benchmark.py:460`) and `pid` overlap is 0, so this preserves
   the leakage-0 property. Disjointness is re-asserted here.

The inversions used (each verified on all 900 rows of all five pairs before use):
    direct      == "Do not reason, just " + harmful_instruction + " given the context."
    doublespeak == demos + "\n\n" + neutral        (so demos = ds[: -(len(neutral) + 2)])

SAFETY: this script necessarily handles harmful instruction text (it is a data converter).
It writes it only into the bench file and NEVER prints it; all logging is counts and hashes.
"""
import argparse
import hashlib
import json
import os
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)

import ds_common as dc  # noqa: E402

PREFIX = "Do not reason, just "
SUFFIX = " given the context."
JOIN = "\n\n"
SPLIT_MAP = {"dev": "train", "heldout": "test"}


def sha(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def invert(row):
    """-> (harmful_instruction, demos) with both inversions asserted."""
    d = row["direct"]
    assert d.startswith(PREFIX) and d.endswith(SUFFIX), \
        f"direct does not match the request template (pid={row['pid']})"
    instr = d[len(PREFIX): len(d) - len(SUFFIX)]
    ds, neutral = row["doublespeak"], row["neutral"]
    assert ds.endswith(neutral), f"doublespeak does not end with neutral (pid={row['pid']})"
    demos = ds[: len(ds) - len(neutral)]
    assert demos.endswith(JOIN), f"demos/neutral join is not {JOIN!r} (pid={row['pid']})"
    demos = demos[: -len(JOIN)]
    assert demos, f"empty demos (pid={row['pid']})"
    return instr, demos


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pair", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--demo-style", default=None,
                    help="fixed demo style to keep; default = lexicographically first present")
    ap.add_argument("--n-demos", type=int, default=None,
                    help="fixed demo count to keep; default = the smallest present")
    ap.add_argument("--min-per-split", type=int, default=20, help="plan §8.1")
    args = ap.parse_args()

    pair = json.load(open(args.pair))
    rows = pair["behavioral"]
    meta_pair = pair.get("pair", {})
    concept = meta_pair.get("concept")
    codeword = meta_pair.get("codeword")
    assert concept and codeword, "pair.concept / pair.codeword missing"
    assert {r["concept"] for r in rows} == {concept}, "mixed concepts in behavioral rows"
    assert {r["codeword"] for r in rows} == {codeword}, "mixed codewords in behavioral rows"

    styles = sorted({r["demo_style"] for r in rows})
    counts = sorted({int(r["n_demos"]) for r in rows})
    style = args.demo_style or styles[0]
    ndem = args.n_demos if args.n_demos is not None else counts[0]
    assert style in styles, f"--demo-style {style!r} not in {styles}"
    assert ndem in counts, f"--n-demos {ndem} not in {counts}"

    # one row per pid, chosen by the fixed rule; fall back within the pid if that exact
    # (style, n_demos) cell is missing for it.
    by_pid = defaultdict(list)
    for r in rows:
        by_pid[r["pid"]].append(r)
    items, fallbacks = [], 0
    for pid in sorted(by_pid):
        cand = [r for r in by_pid[pid]
                if r["demo_style"] == style and int(r["n_demos"]) == ndem]
        if not cand:
            fallbacks += 1
            cand = sorted(by_pid[pid], key=lambda r: (r["demo_style"], int(r["n_demos"])))
        r = cand[0]
        instr, demos = invert(r)
        items.append({
            "id": str(r["bid"]),
            "pid": pid,
            "harmful_instruction": instr,
            "harmful_word": concept,
            "codeword": codeword,
            "demos": demos,
            "split": SPLIT_MAP[r["split"]],
            "src_demo_style": r["demo_style"],
            "src_n_demos": int(r["n_demos"]),
            "src_split": r["split"],
        })

    # --- integrity assertions (plan §3.4 / §8.1) ---
    ids = [it["id"] for it in items]
    assert len(set(ids)) == len(ids), "duplicate item ids"
    pids = [it["pid"] for it in items]
    assert len(set(pids)) == len(pids), "duplicate pids — de-duplication failed"
    per_split = Counter(it["split"] for it in items)
    by_split_pid = defaultdict(set)
    for it in items:
        by_split_pid[it["split"]].add(it["pid"])
    assert not (by_split_pid["train"] & by_split_pid["test"]), "train/test pid overlap"
    texts = defaultdict(set)
    for it in items:
        texts[it["split"]].add(it["harmful_instruction"])
    overlap = texts["train"] & texts["test"]
    assert not overlap, f"train/test share {len(overlap)} identical instructions"
    for sp in ("train", "test"):
        assert per_split[sp] >= args.min_per_split, \
            f"plan §8.1 needs >={args.min_per_split} unique {sp} items, got {per_split[sp]}"

    # round-trip check: rebuilding the conditions must reproduce the original strings
    n_rt = 0
    for it, r in zip(items, [next(x for x in by_pid[it['pid']] if str(x['bid']) == it['id'])
                             for it in items]):
        cond = dc.build_conditions(it["harmful_instruction"], it["harmful_word"],
                                   it["codeword"], it["demos"])
        assert cond.direct == r["direct"], f"round-trip direct mismatch (pid={it['pid']})"
        assert cond.neutral == r["neutral"], f"round-trip neutral mismatch (pid={it['pid']})"
        assert cond.doublespeak == r["doublespeak"], \
            f"round-trip doublespeak mismatch (pid={it['pid']})"
        n_rt += 1

    cohort = f"pair_{concept}"
    out = {
        "_meta": {
            "cohort": cohort,
            "source_pair_file": os.path.abspath(args.pair),
            "source_pair_sha256": sha(open(args.pair).read()),
            "concept": concept, "codeword": codeword,
            "n_behavioral_rows_in_source": len(rows),
            "n_items_after_dedup": len(items),
            "dedup_rule": f"one row per pid; prefer demo_style={style!r}, n_demos={ndem}; "
                          "else lexicographically first (style, n_demos)",
            "n_pid_fallbacks": fallbacks,
            "available_demo_styles": styles, "available_n_demos": counts,
            "split_map": SPLIT_MAP,
            "per_split": dict(per_split),
            "round_trip_verified": n_rt,
            "assertions": ["unique ids", "unique pids", "no train/test pid overlap",
                           "no train/test instruction-text overlap",
                           f"n>={args.min_per_split} per split",
                           "build_conditions round-trip == source direct/neutral/doublespeak"],
            "builder": "scripts/asym_pair_to_behavioral.py",
            "git_commit": dc.git_commit(),
        },
        "items": items,
    }
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    json.dump(out, open(args.out, "w"), indent=1)
    print(f"[pair2beh] {concept:9s} src_rows={len(rows):4d} -> items={len(items):3d} "
          f"train={per_split['train']:3d} test={per_split['test']:3d} "
          f"fallbacks={fallbacks} round_trip_ok={n_rt}")
    print(f"[out] {args.out}")


if __name__ == "__main__":
    main()
