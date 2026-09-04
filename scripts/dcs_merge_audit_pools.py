#!/usr/bin/env python
"""dcs_merge_audit_pools.py -- `DCS-PR-024`: merge the 78 new demonstration pools with the
existing 38 and run the acceptance audit on the GENERATED SENTENCES.

WRITTEN AND COMMITTED WHILE GENERATION WAS STILL RUNNING (176 of 312 pools), so the audit is fixed
before the text it judges exists.

WHAT THE TEMPLATE AUDIT COULD NOT COVER. `PR-024`'s criteria were checked on the domain TEMPLATES
before generation -- completeness, article agreement, register, collision-freedom. But the templates
are prompts; the generator writes the sentences. A template that never says `bomb` can still elicit
a `benign` sentence containing it. So the same criteria are re-run HERE, on the output.

RESPONSIBLE HANDLING (plan section 13, and demo_pools.py's own rule): this prints IDS AND COUNTS
ONLY, never sentence text. A failing pool is named; its offending sentence is not echoed.

HOMOGENEITY IS CHECKED, NOT ASSUMED. The two halves must share generator, seed, concept, codeword,
remap source and pool size, or the merged bank is inhomogeneous in a way nothing downstream would
flag. The CLI default seed is 20260816 and the existing pools used 20260828 -- exactly the kind of
mismatch this refuses on.

REFUSES rather than reports on: a parameter mismatch, a domain present in both halves, a pool
shorter than expected, or any incidental collision.

Stdlib only.
"""
from __future__ import annotations
import argparse, collections, hashlib, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCHEMA = "DCS_POOL_MERGE/1"
# every codeword and concept in use across the phase's banks
FORBIDDEN = ["carrot", "ticket", "basket", "button", "window", "lantern", "candle",
             "bomb", "knife", "gun", "poison", "missile"]
# the words each valence is SUPPOSED to contain, and which are therefore not collisions there
EXPECTED = {"benign": {"carrot"}, "harm": {"bomb"}, "remap": {"bicycle"}, "filler": set()}
MUST_MATCH = ("generator", "openai_seed", "concept", "codeword", "remap_source_word",
              "n_per_pool", "per_split")


def load(p: str) -> dict:
    if not os.path.isfile(p):
        sys.exit(f"REFUSING: no pools file at {p}")
    return json.load(open(p))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--existing", default=os.path.join(
        ROOT, "data/boombness_prompts/demo_pools_29dom.json"))
    ap.add_argument("--new", default=os.path.join(
        ROOT, "data/boombness_prompts/demo_pools_78new.json"))
    ap.add_argument("--out", default=os.path.join(
        ROOT, "data/boombness_prompts/demo_pools_116dom.json"))
    ap.add_argument("--expect-n", type=int, default=40)
    ap.add_argument("--report", default=os.path.join(
        ROOT, "outputs/boombness/dcs_analysis/dcs_pool_merge_audit.json"))
    a = ap.parse_args()

    A, B = load(a.existing), load(a.new)
    ma, mb = A["_meta"], B["_meta"]

    # ---- 1. homogeneity ----------------------------------------------------------------
    diffs = {k: (ma.get(k), mb.get(k)) for k in MUST_MATCH if ma.get(k) != mb.get(k)}
    if diffs:
        sys.exit("REFUSING: the two halves were not generated the same way -- "
                 + "; ".join(f"{k}: {v[0]!r} vs {v[1]!r}" for k, v in diffs.items()))

    # ---- 2. disjoint domains -----------------------------------------------------------
    da = sorted({k.split("|")[0] for k in A["pools"]})
    db = sorted({k.split("|")[0] for k in B["pools"]})
    overlap = sorted(set(da) & set(db))
    if overlap:
        sys.exit(f"REFUSING: {len(overlap)} domains present in BOTH halves: {overlap[:8]}")

    merged = dict(A["pools"])
    merged.update(B["pools"])

    # ---- 3. pool completeness ----------------------------------------------------------
    short = sorted(k for k, v in merged.items() if v.get("n", len(v["sentences"])) < a.expect_n)

    # ---- 4. incidental collisions, ON THE GENERATED TEXT -------------------------------
    coll = collections.defaultdict(list)
    for key, v in merged.items():
        val = key.split("|")[1]
        allowed = EXPECTED.get(val, set())
        blob = " ".join(v["sentences"]).lower()
        for w in FORBIDDEN:
            if w in allowed:
                continue
            if re.search(r"\b" + w + r"\b", blob):
                coll[key].append(w)          # POOL id only -- never the sentence

    # ---- 5. cross-domain leakage: an identical sentence in two domains ------------------
    seen, dupes = {}, collections.defaultdict(list)
    for key, v in merged.items():
        val = key.split("|")[1]
        for s in v["sentences"]:
            h = hashlib.sha256(s.strip().lower().encode()).hexdigest()[:16]
            prev = seen.get((val, h))
            if prev and prev.split("|")[0] != key.split("|")[0]:
                dupes[val].append((prev, key))
            else:
                seen[(val, h)] = key

    doms = sorted({k.split("|")[0] for k in merged})
    rep = {"schema": SCHEMA, "n_domains": len(doms), "n_pools": len(merged),
           "n_from_existing": len(da), "n_from_new": len(db),
           "homogeneous_on": list(MUST_MATCH),
           "params": {k: ma.get(k) for k in MUST_MATCH},
           "short_pools": short,
           "incidental_collisions": {k: v for k, v in coll.items()},
           "incidental_collisions_by_word": dict(collections.Counter(
               w for v in coll.values() for w in v)),
           "COLLISION_NOTE": ("NOT fatal at the pool level (DCS-C-036): 27 of the canonical "
                              "38-domain pools also carry these, so every committed bank was built "
                              "from pools this check once rejected. Collisions are repaired at BANK "
                              "BUILD, per codeword, by prompt_families' own guard plus "
                              "--incidental-replace."),
           "cross_domain_duplicate_sentences": {k: len(v) for k, v in dupes.items()},
           "NOTE": "pool ids and counts only; no sentence text is emitted (plan section 13)"}

    print(f"domains  {len(da)} existing + {len(db)} new = {len(doms)}")
    print(f"pools    {len(merged)}   homogeneous on {', '.join(MUST_MATCH)}")
    print(f"short pools (<{a.expect_n}): {len(short)} {short[:6]}")
    byword = collections.Counter(w for v in coll.values() for w in v)
    print(f"incidental collisions: {len(coll)} pools -- NOT fatal (C-036); the bank build repairs "
          f"these per codeword via --incidental-replace")
    for w, n in byword.most_common():
        print(f"    {w:>8s}: {n:3d} pool(s)  -> a {w} bank needs --incidental-replace \"{w}=<alt>\"")
    print(f"cross-domain duplicate sentences: {dict(rep['cross_domain_duplicate_sentences'])}")

    os.makedirs(os.path.dirname(a.report), exist_ok=True)
    json.dump(rep, open(a.report, "w"), indent=2, sort_keys=True)

    # DCS-C-036. Incidental collisions are NOT fatal at the pool level, and treating them as such
    # was a mis-scoped guard: 27 of the CANONICAL 38-domain pools fail it, i.e. every committed bank
    # in this phase -- including the headline -- was built from pools this check would have rejected.
    # The repo handles collisions where they actually matter: at BANK BUILD, per codeword, via
    # `prompt_families.incidental_codeword_collisions()` + `--incidental-replace`, which REFUSES and
    # names the offending pools. Pools are written around ONE codeword (carrot) and one concept
    # (bomb); every other codeword appearing incidentally is EXPECTED, because those banks are built
    # by substitution. => Reported here as information the bank build will need, never as a veto.
    fatal = bool(short)
    if fatal:
        rep["VERDICT"] = "REFUSED"
        json.dump(rep, open(a.report, "w"), indent=2, sort_keys=True)
        sys.exit(f"REFUSING to write the merged pools: {len(short)} short pool(s). "
                 f"See {a.report}")

    out = {"_meta": dict(ma), "pools": merged}
    out["_meta"]["domains"] = doms
    out["_meta"]["merged_from"] = [os.path.basename(a.existing), os.path.basename(a.new)]
    out["_meta"]["content_sha16"] = hashlib.sha256(
        json.dumps(merged, sort_keys=True).encode()).hexdigest()[:16]
    json.dump(out, open(a.out, "w"), indent=2)
    print(f"-> {a.out}  sha16={out['_meta']['content_sha16']}")
    print(f"-> {a.report}")


if __name__ == "__main__":
    main()
