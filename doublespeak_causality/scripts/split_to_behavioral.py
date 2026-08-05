#!/usr/bin/env python3
"""Phase-2.1 adapter: locked split -> 14_behavioral_eval.py data format (per cohort).

14_behavioral_eval.py generates direct/neutral/doublespeak via ds_common.build_conditions and
scores each with StrongReject against the ORIGINAL harmful goal. It reads items with fields:
  id, harmful_instruction, harmful_word, codeword, demos(list|str)
This reconstructs those from the locked split; `demos` is the codeword-substituted in-context
block extracted from doublespeak_prompt (everything before the request line), so build_conditions
rebuilds byte-identical direct/neutral/doublespeak prompts.

Only single-token-primary examples are emitted, split-tagged so we can aggregate train/test.

Usage:
  python scripts/split_to_behavioral.py --split data/splits/clearharm_doublespeak_v1.json --out-dir data/behavioral
Outputs: data/behavioral/beh_<cohort>.json  ({"items":[...]})
"""
from __future__ import annotations
import argparse, json, os

REQUEST_MARKER = "\n\nDo not reason, just "  # ds_common.build_conditions default prefix


def extract_demos(doublespeak_prompt: str) -> str:
    """The demos block = everything before the (last) request line in the DS prompt."""
    if REQUEST_MARKER in doublespeak_prompt:
        return doublespeak_prompt.rsplit(REQUEST_MARKER, 1)[0]
    return doublespeak_prompt  # fallback (should not happen for our prompts)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", default="data/splits/clearharm_doublespeak_v1.json")
    ap.add_argument("--out-dir", default="data/behavioral")
    ap.add_argument("--force", action="store_true",
                    help="allow overwriting an existing beh_<cohort>.json (refused by default: "
                         "v1 and v3 both have a 'clearharm' cohort, so the default out-dir "
                         "silently clobbers the v1 bench that published results depend on)")
    args = ap.parse_args()

    obj = json.load(open(args.split))
    meta = obj.get("_meta", {})
    by_cohort = {}
    for e in obj["examples"]:
        if not e.get("single_token_primary", True):
            continue
        by_cohort.setdefault(e["cohort"], []).append(e)

    os.makedirs(args.out_dir, exist_ok=True)
    for cohort, exs in by_cohort.items():
        items = []
        for e in exs:
            demos = extract_demos(e["doublespeak_prompt"])
            # sanity: the codeword must appear in the demos block (binding present)
            if e["codeword"] not in demos:
                continue
            items.append({
                "id": e["example_id"],
                "split": e["split"],
                "harm_category": e["harm_category"],
                "harmful_instruction": e["original_request"],
                "harmful_word": e["target_concept"],
                "codeword": e["codeword"],
                "demos": demos,
            })
        out = {"_meta": {"cohort": cohort, "source_split": args.split,
                         "dataset_revision": meta.get("dataset_revision"),
                         "n_items": len(items),
                         "note": "for 14_behavioral_eval.py --templated (direct/neutral/doublespeak + StrongReject)"},
               "items": items}
        path = os.path.join(args.out_dir, f"beh_{cohort}.json")
        # GUARD (added 2026-08-05 after a near-miss): the output name is derived from the
        # COHORT, and v1 and v3 both contain a cohort called "clearharm". Running this on the
        # v3 split with the default --out-dir therefore silently overwrote the v1
        # beh_clearharm.json (86 items -> 170) that every completed behavioral result was
        # computed against. Never clobber an existing bench without an explicit --force.
        if os.path.exists(path) and not args.force:
            raise SystemExit(
                f"REFUSING to overwrite {path}\n"
                f"  It already exists and other results may depend on it.\n"
                f"  Write to a different --out-dir (e.g. data/behavioral_v3), or pass --force "
                f"if you genuinely intend to replace it.")
        json.dump(out, open(path, "w"), indent=1)
        import collections
        per = collections.Counter(i["split"] for i in items)
        print(f"{path}: {len(items)} items ({dict(per)})")


if __name__ == "__main__":
    main()
