#!/usr/bin/env python
"""FATAL split-integrity validator for the v3 confirmatory dataset (Master Plan V2 §1.3 / §36).

Recomputes every integrity property from the examples (does NOT trust `_meta`). Exit 0 iff the v3 split
is eligible for confirmatory causal inference; exit 1 with a FATAL list otherwise. Login-node safe (no
torch): the single-token check reads the stored `single_token_primary` flag rather than re-tokenizing —
that flag was written at build time under the pinned tokenizer, and re-verifying it needs a GPU/tokenizer
run (flagged as a WARN-level provenance note, not re-done here).

Checks (FATAL unless marked):
  F1 no duplicate example_id
  F2 leakage=0: no target_concept / codeword / intent_cluster straddles any split-pair (recomputed)
  F3 ≥20 examples per (cohort × split) cell  (§0.6 global rule)
  F4 all 6 conditions present & non-empty on every example
  F5 0 placeholder demos (demo_provenance_counts has no placeholder key; 'placeholder' substring absent)
  F6 dataset_revision == pinned ClearHarm hash
  F7 behavioral files (beh_clearharm.json + beh_generated.json) ids ⊆ split ids and sum to n_examples
  W1 (warn) single_token_primary True for all examples (flag count if not; not re-tokenized here)

Usage:
  python scripts/validate_dataset_v3.py \
     --split data/splits/clearharm_doublespeak_v3.json \
     --beh data/behavioral_v3/beh_clearharm.json data/behavioral_v3/beh_generated.json
"""
import argparse, json, os, sys
from collections import Counter, defaultdict
from itertools import combinations

PINNED_REV = "clearharm@79464fb6b3c2a8ee925184f394f9636600349f88"
CONDITIONS = ["doublespeak_prompt", "neutral_prompt", "direct_prompt",
              "benign_prompt", "shuffled_prompt", "unrelated_prompt"]
MIN_PER_CELL = 20


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", default="doublespeak_causality/data/splits/clearharm_doublespeak_v3.json")
    ap.add_argument("--beh", nargs="*", default=[
        "doublespeak_causality/data/behavioral_v3/beh_clearharm.json",
        "doublespeak_causality/data/behavioral_v3/beh_generated.json"])
    a = ap.parse_args()

    d = json.load(open(a.split))
    ex = d["examples"]; meta = d.get("_meta", {})
    fatal, warn, ok = [], [], []

    # F1 duplicate ids
    ids = [e["example_id"] for e in ex]
    dup = [k for k, c in Counter(ids).items() if c > 1]
    (ok if not dup else fatal).append(f"F1 duplicate example_id: {len(dup)} dup" + (f" e.g. {dup[:3]}" if dup else ""))

    # F2 leakage recomputed per split-pair
    by_split = defaultdict(lambda: {"concept": set(), "codeword": set(), "cluster": set()})
    for e in ex:
        s = e["split"]
        by_split[s]["concept"].add(e["target_concept"])
        by_split[s]["codeword"].add(e["codeword"])
        by_split[s]["cluster"].add(e["intent_cluster"])
    leak_lines = []
    for s1, s2 in combinations(sorted(by_split), 2):
        for kind in ("concept", "codeword", "cluster"):
            straddle = by_split[s1][kind] & by_split[s2][kind]
            if straddle:
                leak_lines.append(f"{s1}/{s2} {kind}: {len(straddle)} straddle e.g. {sorted(straddle)[:3]}")
    (ok if not leak_lines else fatal).append("F2 leakage(recomputed): " + ("0 straddling across all split-pairs" if not leak_lines else "; ".join(leak_lines)))

    # F3 >=20 per cohort x split
    cell = Counter((e["cohort"], e["split"]) for e in ex)
    small = {k: v for k, v in cell.items() if v < MIN_PER_CELL}
    (ok if not small else fatal).append(f"F3 ≥20/cell: cells={dict(cell)}" + (f" UNDER20={small}" if small else " (all ≥20)"))

    # F4 all 6 conditions present & non-empty
    bad_cond = [e["example_id"] for e in ex if any(not str(e.get(c, "")).strip() for c in CONDITIONS)]
    (ok if not bad_cond else fatal).append(f"F4 6 conditions non-empty: {len(bad_cond)} bad" + (f" e.g. {bad_cond[:3]}" if bad_cond else ""))

    # F5 placeholder demos
    dpc = meta.get("demo_provenance_counts", {})
    ph_key = any("placeholder" in str(k).lower() for grp in dpc.values() for k in (grp or {}))
    ph_sub = "placeholder" in json.dumps(ex).lower()
    (ok if not (ph_key or ph_sub) else fatal).append(
        f"F5 placeholder demos: provenance_counts={dpc}" + ("" if not (ph_key or ph_sub) else " PLACEHOLDER FOUND"))

    # F6 dataset revision
    rev = meta.get("dataset_revision")
    (ok if rev == PINNED_REV else fatal).append(f"F6 dataset_revision: {rev}" + ("" if rev == PINNED_REV else f" != pinned {PINNED_REV}"))

    # F7 behavioral files
    split_ids = set(ids)
    beh_total = 0
    beh_lines = []
    for bf in a.beh:
        if not os.path.exists(bf):
            fatal.append(f"F7 beh file missing: {bf}"); continue
        bd = json.load(open(bf)); bitems = bd["items"] if isinstance(bd, dict) and "items" in bd else bd
        bids = set(x["id"] for x in bitems); beh_total += len(bitems)
        notin = bids - split_ids
        beh_lines.append(f"{os.path.basename(bf)}={len(bitems)} (⊄split:{len(notin)})")
    (ok if beh_total == len(ex) and all("⊄split:0" in l for l in beh_lines) else fatal).append(
        f"F7 behavioral files: {'; '.join(beh_lines)}; sum={beh_total} vs n_examples={len(ex)}")

    # W1 single-token flag
    nst = sum(1 for e in ex if not e.get("single_token_primary", False))
    (ok if nst == 0 else warn).append(f"W1 single_token_primary False: {nst} (flag from build-time tokenizer, not re-tokenized here)")

    print(f"=== validate_dataset_v3: {a.split} — {len(ex)} examples ===")
    for l in ok:    print("  ✅", l)
    for l in warn:  print("  ⚠️ ", l)
    for l in fatal: print("  ❌ FATAL:", l)
    if fatal:
        print(f"\nRESULT: FATAL ({len(fatal)}) — NOT eligible for confirmatory inference")
        sys.exit(1)
    print(f"\nRESULT: PASS — {len(ex)} examples eligible for confirmatory causal inference"
          + (f" ({len(warn)} warn)" if warn else ""))


if __name__ == "__main__":
    main()
