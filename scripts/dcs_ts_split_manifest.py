#!/usr/bin/env python3
"""Build the DCS thesis-scale DOMAIN-level train/validation/test manifest.

`DCS-PR-046`, 2026-09-06.

WHAT THIS IS. One committed JSON assigning every one of the 116 demonstration domains to
exactly one of {train, validation, test}, fixed by one seed, derived from the domain roster
ALONE. It is built and committed BEFORE any hidden state, logit, installation outcome, probe
score or ASR exists, so no outcome can have influenced it.

WHY THE DOMAIN IS THE UNIT. Rows are not independent. Every template, family, `n_examples`
value, split and repetition drawn from one domain shares that domain's demonstration
sentences, so a random ROW split puts near-duplicate demonstration text on both sides of the
boundary and the probe scores its own training corpus. The domain is the independence unit
for every learned-representation claim in this phase (MANDATE §5).

WHY A NEW FIELD NAME (`dsplit`, NOT `split`). The banks already carry a field called `split`,
with values `dev` / `heldout`. That is a WITHIN-DOMAIN cut of each demonstration pool
(`demo_pools.py`, `PER_SPLIT=20`) and ALL 116 of 116 domains straddle it -- measured, dev 6496
rows / heldout 6496 rows on the `cds116` bank. Adopting it as a train/test boundary would be
precisely the demonstration-pool leakage MANDATE §5.1 forbids, while passing any validator
that merely checks "a split field exists and has two values". This repository has already been
bitten by exactly that shape once: `clearharm_doublespeak_v1.json`'s cluster key was a
per-instruction hash, so its "no intent_cluster overlap" check was vacuous and 77 of 86 rows
leaked. A differently-named field cannot be confused with the sentence cut by a human or by a
join.

PROVENANCE OF THE RATIO. No split convention anywhere in this repository is attributed to
Matan; a repo-wide hunt found every `Matan` hit to be about something else. The one prior rule
that names the right UNIT has no numbers -- `docs/BOOMBNESS_OBJECTIVE_SPRINT_PLAN.md:535`,
"Use train/val/test split by family/domain so the probe cannot memorize templates". 70/23/23
INSTANTIATES that rule rather than contradicting it, and `:535` is cited as its source. The one
prior rule that has numbers (`doublespeak_causality/scripts/build_split_v3.py:61-62`, 50/25/25)
splits normalized CONCEPT CLUSTERS for a per-concept-generalisation claim -- a different unit
for a different estimand -- and is deliberately not reused.

SEED. 202609061, not 20260906. The bare date is already `POWER_SEED` in
`scripts/dcs_pr042_mediation.py:142` and appears in `scripts/dcs_verify_pr035.py` and the
PR-028 run tags; reusing it would make two unrelated randomisations share a stream and make
any "same seed" assertion ambiguous.

DOWNSTREAM DISCIPLINE, adopted verbatim from
`doublespeak_causality/reports/DATASET_AND_SPLIT_CONTRACT.md`:

    Discovery scripts read `train` only. `test`/`heldout` used only for frozen confirmatory
    replication ... never for layer/head/path/direction/threshold selection.

That clause also settles the C3 defect: the SELECTION cell must live in `train`/`validation`,
never in `test`.

USAGE
    python3 scripts/dcs_ts_split_manifest.py --check    # verify the committed manifest
    python3 scripts/dcs_ts_split_manifest.py --write    # (re)generate it
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POOLS = os.path.join(REPO, "data", "boombness_prompts", "demo_pools_116dom.json")
OUT = os.path.join(REPO, "data", "boombness_prompts", "dcs_ts116_domain_split.json")

SEED = 202609061
N_TRAIN, N_VAL, N_TEST = 70, 23, 23


def domain_roster(pools_path: str) -> tuple[list[str], str]:
    """The 116 domain ids and the pools file's own content hash.

    Read from the POOL KEYS (`domain|valence`), not from `_meta["domains"]`. The two agree
    today, but the keys are what the generator actually iterates, and a roster that disagreed
    with the pools it claims to describe is the kind of drift this phase exists to catch.
    """
    with open(pools_path) as f:
        obj = json.load(f)
    doms = sorted({k.split("|", 1)[0] for k in obj["pools"]})
    return doms, obj["_meta"]["content_sha16"]


def build(doms: list[str], seed: int = SEED) -> dict[str, str]:
    """Assign domains to splits by one shuffle of the SORTED roster under one seed.

    Sorted first so the assignment depends only on the SET of domain ids and the seed -- never
    on the order the pools file happens to serialise them in. `random.Random(seed)` rather than
    the global RNG so nothing an importer does can perturb it.
    """
    if len(doms) != N_TRAIN + N_VAL + N_TEST:
        raise SystemExit(
            f"roster is {len(doms)} domains but the split is fixed at "
            f"{N_TRAIN}/{N_VAL}/{N_TEST} = {N_TRAIN + N_VAL + N_TEST}. Refusing to guess: "
            f"a ratio silently rescaled to fit a changed roster is not the preregistered split."
        )
    order = list(doms)
    random.Random(seed).shuffle(order)
    out = {}
    for d in order[:N_TRAIN]:
        out[d] = "train"
    for d in order[N_TRAIN:N_TRAIN + N_VAL]:
        out[d] = "validation"
    for d in order[N_TRAIN + N_VAL:]:
        out[d] = "test"
    return out


def manifest(pools_path: str = POOLS) -> dict:
    doms, pools_sha = domain_roster(pools_path)
    assign = build(doms)
    body = {
        "schema": "dcs_ts_domain_split/1",
        "field_name": "dsplit",
        "seed": SEED,
        "n_train": N_TRAIN,
        "n_validation": N_VAL,
        "n_test": N_TEST,
        "pools_path": os.path.relpath(pools_path, REPO),
        "pools_sha16": pools_sha,
        "unit": "domain",
        "provenance": (
            "ratio instantiates docs/BOOMBNESS_OBJECTIVE_SPRINT_PLAN.md:535 "
            "('split by family/domain so the probe cannot memorize templates'), which names the "
            "unit but no numbers; no split convention in this repo is attributed to Matan"
        ),
        "discipline": (
            "Discovery scripts read `train` only. `test` is used only for frozen confirmatory "
            "replication, never for layer/head/path/direction/threshold selection. The selection "
            "cell must live in train/validation."
        ),
        "assign": {d: assign[d] for d in doms},  # sorted-roster order, deterministic
    }
    # The manifest's own hash covers the body WITHOUT the hash field, so it is checkable.
    body["manifest_sha16"] = hashlib.sha256(
        json.dumps(body, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()[:16]
    return body


def verify(m: dict) -> list[str]:
    """Re-derive everything and report every disagreement. Never returns silently on an empty set."""
    errs = []
    got = dict(m["assign"])
    doms, pools_sha = domain_roster(os.path.join(REPO, m["pools_path"]))

    if pools_sha != m["pools_sha16"]:
        errs.append(f"pools_sha16 drift: manifest {m['pools_sha16']} vs on-disk {pools_sha}")
    if sorted(got) != doms:
        errs.append(f"roster drift: manifest has {len(got)} domains, pools have {len(doms)}")

    # Re-derive from the seed. This is the check that matters: it proves the manifest is a
    # function of (roster, seed) and not of anything anyone typed.
    if sorted(got) == doms:
        rebuilt = build(doms, m["seed"])
        bad = [d for d in doms if rebuilt[d] != got[d]]
        if bad:
            errs.append(f"{len(bad)} domain(s) do not match a rebuild from seed {m['seed']}: {bad[:5]}")

    counts = {s: sum(1 for v in got.values() if v == s) for s in ("train", "validation", "test")}
    if counts != {"train": N_TRAIN, "validation": N_VAL, "test": N_TEST}:
        errs.append(f"split sizes are {counts}, expected {N_TRAIN}/{N_VAL}/{N_TEST}")

    # Disjointness is trivially true for a dict, so assert the thing that is NOT trivially true:
    # every domain got exactly one label, and every label is legal. A check that cannot fail is
    # worth nothing (C-071).
    illegal = sorted({v for v in got.values()} - {"train", "validation", "test"})
    if illegal:
        errs.append(f"illegal split label(s): {illegal}")
    if not got:
        errs.append("manifest assigns NO domains -- the check would otherwise pass over an empty set")

    body = {k: v for k, v in m.items() if k != "manifest_sha16"}
    sha = hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":")).encode()).hexdigest()[:16]
    if sha != m.get("manifest_sha16"):
        errs.append(f"manifest_sha16 mismatch: stored {m.get('manifest_sha16')} vs recomputed {sha}")
    return errs


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--out", default=OUT)
    a = ap.parse_args()
    if not (a.write or a.check):
        ap.error("pass --write or --check")

    if a.write:
        if os.path.exists(a.out):
            # A split may be created once. Overwriting it after outcomes exist is the reshuffle
            # MANDATE §5.2 forbids, so refuse rather than clobber.
            print(f"REFUSING: {a.out} already exists. A committed split is not regenerated; "
                  f"delete it deliberately if the roster genuinely changed.", file=sys.stderr)
            return 2
        m = manifest()
        with open(a.out, "w") as f:
            json.dump(m, f, indent=2, sort_keys=False)
        print(f"wrote {a.out}  manifest_sha16={m['manifest_sha16']}  "
              f"{m['n_train']}/{m['n_validation']}/{m['n_test']} domains  seed={m['seed']}")

    if a.check:
        with open(a.out) as f:
            m = json.load(f)
        errs = verify(m)
        n_checks = 6
        if errs:
            for e in errs:
                print(f"  FAIL {e}", file=sys.stderr)
            print(f"[split-manifest] {len(errs)} of {n_checks} checks FAILED", file=sys.stderr)
            return 1
        counts = {s: sum(1 for v in m["assign"].values() if v == s)
                  for s in ("train", "validation", "test")}
        print(f"[split-manifest] all {n_checks} checks pass over {len(m['assign'])} domains "
              f"{counts} seed={m['seed']} manifest_sha16={m['manifest_sha16']} "
              f"pools_sha16={m['pools_sha16']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
