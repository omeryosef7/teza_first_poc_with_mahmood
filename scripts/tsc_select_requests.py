#!/usr/bin/env python
"""tsc_select_requests.py -- `TSC-PR-005`'s request draw, as CODE, committed before it is run.

WHY AS CODE, AND WHY IT READS NO INSTRUCTION TEXT.
The single way selection leakage enters a confirmatory bank is a human looking at candidate
requests and keeping the ones that feel promising. `R-50` is this repo's instance and
`CDS-PR-001` §2.4 forbids it. So the draw is:

  * **deterministic** -- one seed, `20260903`, fixed in `TSC-PR-005` before the file existed;
  * **metadata-only** -- it consults `task_id`, `category` and `duplicate_group` and NOTHING else.
    `instruction` is never read, never printed, never sorted on. The population is fixed before
    anyone can have an opinion about which requests look easy;
  * **quota-balanced** -- 8 registered categories x `--per-category` requests, so no category can
    dominate by being over-represented in the source;
  * **refusing** -- a category that cannot fill its quota after de-duplication is a SystemExit, not
    a short draw. `CDS-C-001`: a gate that passes on an empty (or shrunken) selection is not a gate.

WHAT IT DOES NOT DO. It does not derive the `(concept, template)` pair that turns a selected
AdvBench instruction into a doublespeak request. That step reads harmful text and is done
separately, DOWNSTREAM of this file, on the 40 rows this file has already fixed -- so it cannot
change which requests are in the population, only how each one is phrased.

Emits a manifest and a `selection_sha16` over the sorted task_ids, so a later run can be proved to
have used this exact draw.
"""
from __future__ import annotations
import argparse, collections, csv, hashlib, json, os, random

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCHEMA = "TSC_REQUEST_SELECTION/1"

#: Fixed in `TSC-PR-005` before this file existed. Never re-rolled to change the draw.
SEED = 20260903

#: The 8 categories, and the two reasons a category is absent, both fixed in advance.
#:   n < MIN_CATEGORY_N            -- too few source rows for a 5-draw not to be near-exhaustive
#:   the object is a PERSON or a SPEECH ACT -- not a noun the codeword can be mapped onto, so the
#:   doublespeak frame is not constructible. ⚠ This is a SCOPE LIMIT OF THE PARADIGM and must be
#:   reported as one, never quietly omitted.
CATEGORIES = (
    "cyber_hacking_malware",
    "fraud_financial_crime",
    "weapons_explosives_mass_casualty",
    "identity_theft_personal_data_theft",
    "misinformation_disinformation",
    "violent_crime_physical_harm",
    "drugs_controlled_substances",
    "theft_property_crime",
)
EXCLUDED = {
    "other_uncategorized": "not a category",
    "child_exploitation": "n=7 below MIN_CATEGORY_N, and out of scope for anything this project publishes",
    "terrorism_extremism": "n=9 below MIN_CATEGORY_N",
    "academic_minor_dishonesty_deception": "n=8 below MIN_CATEGORY_N",
    "privacy_surveillance": "n=7 below MIN_CATEGORY_N",
    "self_harm_suicide": "object is a person, not a mappable noun -- PARADIGM SCOPE LIMIT",
    "hate_speech_discrimination": "object is a speech act, not a mappable noun -- PARADIGM SCOPE LIMIT",
    "harassment_bullying_stalking": "object is a person, not a mappable noun -- PARADIGM SCOPE LIMIT",
}
MIN_CATEGORY_N = 16
DEFAULT_SOURCE = os.path.join(ROOT, "data", "manifests", "heldout_495.csv")


def selection_sha16(task_ids) -> str:
    """Digest of the SORTED task ids, so two runs can be proved to have drawn the same population."""
    return hashlib.sha256("\n".join(sorted(task_ids)).encode("utf-8")).hexdigest()[:16]


def select(rows, per_category, seed=SEED):
    """The draw. Reads `task_id`, `category`, `duplicate_group` -- and no other column."""
    by_cat = collections.defaultdict(list)
    for r in rows:
        by_cat[r["category"]].append(r)

    # THE EXCLUSION LIST IS CHECKED AGAINST THE DATA, not trusted. A category that disappeared from
    # the source, or one that grew past MIN_CATEGORY_N since the rule was written, is a changed
    # population and must be seen rather than silently honoured.
    for cat, why in EXCLUDED.items():
        n = len(by_cat.get(cat, ()))
        if "MIN_CATEGORY_N" in why and n >= MIN_CATEGORY_N:
            raise SystemExit(f"REFUSING: {cat!r} was excluded for n<{MIN_CATEGORY_N} but now has "
                             f"{n} rows. The source changed; re-register the rule, do not run it.")
    for cat in CATEGORIES:
        n = len(by_cat.get(cat, ()))
        if n < MIN_CATEGORY_N:
            raise SystemExit(f"REFUSING: registered category {cat!r} has {n} rows, below "
                             f"MIN_CATEGORY_N={MIN_CATEGORY_N}. Do not shrink the quota to fit.")

    picked, used_groups = [], set()
    for cat in CATEGORIES:
        # ORDERED BY task_id BEFORE SHUFFLING. `csv.DictReader` order is file order, and file order
        # is not a guarantee -- a re-sorted source would silently change the draw under the same
        # seed. Sorting first makes the seed, not the file, the only thing that determines it.
        pool = sorted(by_cat[cat], key=lambda r: r["task_id"])
        rng = random.Random(seed + CATEGORIES.index(cat))
        rng.shuffle(pool)
        taken = []
        for r in pool:
            g = (r.get("duplicate_group") or "").strip()
            # DEDUP RULE (a): never two rows from one duplicate_group, ACROSS categories too --
            # a shared group means the same instruction, and the same instruction twice is one
            # cluster reported as two.
            if g and g in used_groups:
                continue
            taken.append(r)
            if g:
                used_groups.add(g)
            if len(taken) == per_category:
                break
        if len(taken) != per_category:
            raise SystemExit(f"REFUSING: {cat!r} yielded {len(taken)} of {per_category} after "
                             f"de-duplication. A short category is a changed design, not a result.")
        picked.extend(taken)
    return picked


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source", default=DEFAULT_SOURCE)
    ap.add_argument("--per-category", type=int, default=5)
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--out", default=os.path.join(ROOT, "data", "manifests",
                                                  "tsc_requests_v1_selection.json"))
    a = ap.parse_args()

    with open(a.source, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    srcs = {r["source_dataset"] for r in rows}
    splits = {r["split"] for r in rows}
    if srcs != {"advbench"} or splits != {"heldout"}:
        raise SystemExit(f"REFUSING: source is not the registered AdvBench held-out manifest "
                         f"(datasets={sorted(srcs)}, splits={sorted(splits)}).")

    picked = select(rows, a.per_category, a.seed)
    ids = [r["task_id"] for r in picked]
    if len(set(ids)) != len(ids):
        raise SystemExit("REFUSING: the draw repeated a task_id.")

    doc = {
        "schema": SCHEMA,
        "source": os.path.relpath(a.source, ROOT),
        "source_n_rows": len(rows),
        "seed": a.seed,
        "per_category": a.per_category,
        "categories": list(CATEGORIES),
        "excluded_categories": EXCLUDED,
        "min_category_n": MIN_CATEGORY_N,
        "n_selected": len(picked),
        "cluster_unit": "harmful_request",
        "selection_sha16": selection_sha16(ids),
        # ⚠ METADATA ONLY. `instruction` is deliberately NOT copied here: this artifact fixes WHICH
        # requests are in the population, and it must be reviewable without reading any of them.
        "selected": [{"task_id": r["task_id"], "category": r["category"],
                      "duplicate_group": r.get("duplicate_group") or ""} for r in picked],
        "note": ("The (concept, template) derivation happens DOWNSTREAM of this file, on these "
                 "exact task_ids. It can change how a request is phrased; it cannot change which "
                 "requests are in the population."),
    }
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=1)
    print(f"[tsc] selected {len(picked)} requests over {len(CATEGORIES)} categories, "
          f"selection_sha16={doc['selection_sha16']}")
    for cat in CATEGORIES:
        print(f"    {cat:40s} {sum(1 for r in picked if r['category'] == cat)}")
    print(f"[tsc] -> {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
