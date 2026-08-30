#!/usr/bin/env python
"""rah_make_gatesub.py -- reproduce the `38dom_gatesub` cut on another 38-domain bank.

`RAH-PR-007` screens two lexical pairs. `carrot<->bomb` already has a pre-cut screening bank,
`boombness_prompt_bank_38dom_gatesub.jsonl` (608 rows, a strict subset of the full 38-domain bank).
`ticket<->knife` has no equivalent, and screening the two pairs on DIFFERENT axes would confound the
comparison with the cut. This reproduces the same cut, deterministically.

IT GENERATES NO PROMPTS. It filters an existing bank and copies rows verbatim, so `prompt_id`,
`prompt_sha16` and `full_prompt` are unchanged and provenance is intact. The output is a new file
with its own hash, which is what `compare_bank_hashes` will record on any run against it.

The cut, read off the committed carrot/bomb gatesub rather than assumed:
    condition        natural_doublespeak
    query_kind       behavioral
    role_style       plain
    family_slot      {0, 3}
    strength         none
    consistency      consistent
    example_position near
    n_examples       {1, 2, 4, 8}

Usage:
  python scripts/rah_make_gatesub.py \
      --src data/boombness_prompts/boombness_prompt_bank_38dom_ticket_knife.jsonl \
      --out data/boombness_prompts/boombness_prompt_bank_38dom_tk_gatesub.jsonl
"""
import argparse, collections, json, os, sys

CUT = {"condition": {"natural_doublespeak"}, "query_kind": {"behavioral"},
       "role_style": {"plain"}, "family_slot": {0, 3}, "strength": {"none"},
       "consistency": {"consistent"}, "example_position": {"near"},
       "n_examples": {1, 2, 4, 8}}
#: The carrot/bomb gatesub this cut is copied from. A mismatch means the cut drifted.
REFERENCE = "data/boombness_prompts/boombness_prompt_bank_38dom_gatesub.jsonl"


def keep(r):
    return all(r.get(k) in v for k, v in CUT.items())


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--src", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--expect-rows", type=int, default=608)
    a = ap.parse_args()

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # The cut must reproduce the reference bank EXACTLY when applied to its own source, or it has
    # drifted from the thing it claims to copy.
    ref = [json.loads(l) for l in open(os.path.join(root, REFERENCE))]
    full = [json.loads(l) for l in open(os.path.join(
        root, "data/boombness_prompts/boombness_prompt_bank_38dom.jsonl"))]
    got = {r["prompt_id"] for r in full if keep(r)}
    want = {r["prompt_id"] for r in ref}
    if got != want:
        raise SystemExit("REFUSING: the cut does not reproduce the reference gatesub "
                         "(%d vs %d rows, %d symmetric difference). It has drifted."
                         % (len(got), len(want), len(got ^ want)))
    print("[cut] verified: reproduces %s exactly (%d rows)" % (REFERENCE, len(want)))

    src = [json.loads(l) for l in open(a.src)]
    out = [r for r in src if keep(r)]
    doms = collections.Counter(r["domain"] for r in out)
    ne = collections.Counter(r["n_examples"] for r in out)
    if len(out) != a.expect_rows:
        raise SystemExit("REFUSING: got %d rows, expected %d" % (len(out), a.expect_rows))
    if len(doms) < 30:
        raise SystemExit("REFUSING: %d domains, RAH-PR-006 requires >= 30" % len(doms))
    if len(set(doms.values())) != 1:
        raise SystemExit("REFUSING: unbalanced rows per domain %r" % sorted(set(doms.values())))
    ids = [r["prompt_id"] for r in out]
    if len(set(ids)) != len(ids):
        raise SystemExit("REFUSING: duplicate prompt_ids in the cut")
    with open(a.out, "w") as fh:
        for r in out:
            fh.write(json.dumps(r) + "\n")
    print("[cut] %s -> %s" % (os.path.basename(a.src), os.path.basename(a.out)))
    print("[cut] %d rows, %d domains x %d rows, n_examples %r, pair %s<->%s"
          % (len(out), len(doms), list(doms.values())[0], dict(sorted(ne.items())),
             out[0]["codeword"], out[0]["concept"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
