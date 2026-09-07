#!/usr/bin/env python3
"""Select 40 length-matched harm sentences per (domain, concept) from 60 candidates.

`DCS-C-077`, 2026-09-07. This runs because a PREREGISTERED TRIGGER FIRED, not because the
number looked inconvenient.

THE TRIGGER. `configs/dcs_ts_pr046.json` carries, written before the measurement existed:

    "deferred_decision_rule": "If N4 length-only comes out well above chance, over-generate and
     length-match the 40 kept sentences per pool -- prompt-only and outcome-blind, ~50% more API.
     THIS RULE IS RECORDED BEFORE N4 IS MEASURED so it cannot be chosen after seeing the probe."

Gate G5 then measured **N4 length-only = 0.4174 accuracy / 0.5750 macro AUROC, z = +6.62** against
chance 1/3, with mean prompt length bomb 1085.7 / gun 1074.3 / knife 1055.0 characters. That is
well above chance, so the rule fires. No probe has been run; no outcome exists.

WHY LENGTH MATTERS HERE AND NOT ELSEWHERE. The three concepts are installed by independently
generated demonstrations, so any systematic surface difference between them is a route by which a
classifier could recover the label without reading a representation at all. Length is the
crudest such route and the easiest to remove, and removing it costs nothing scientifically: the
concept is carried by the predicates, not by how many characters the sentence happens to run to.
The register difference (bomb hedges 13.4 %, knife 0.1 %) is NOT removed -- that one is part of
what the concepts are, and it is handled by being measured and published instead.

THE SELECTION IS DETERMINISTIC AND PROMPT-ONLY.
For each domain:
  1. pool the candidate sentences of all three concepts and take 40 target quantiles of that
     pooled length distribution -- one shared target, so no concept's own distribution defines
     the goal;
  2. for each concept independently, walk the targets in order and take the unused candidate
     whose length is nearest, ties broken by original index.
No RNG, no model output, no outcome. Running it twice gives the same answer, and it cannot be
steered toward a result because it never sees one.

⚠ WHAT THIS DOES NOT FIX. Matching the marginal length distribution does not make the arms
identical -- it removes a first-order confound. `N4` must be RE-MEASURED on the rebuilt bank and
reported at its new value, whatever that is. If it is still well above chance, that is a finding
about the corpus, not a reason for a third round.

USAGE
    python3 scripts/dcs_ts_length_match_pools.py --check      # report the gain, write nothing
    python3 scripts/dcs_ts_length_match_pools.py --write
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import statistics as st
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "scripts"))
DP = os.path.join(REPO, "data", "boombness_prompts")
SHARED = os.path.join(DP, "demo_pools_116dom.json")
CAND = os.path.join(DP, "ts_cand", "cand_{}.json")
OUT = os.path.join(DP, "demo_pools_116dom_tsm_{}.json")
CONCEPTS = ("bomb", "knife", "gun")
SHARED_VALENCES = ("benign", "remap", "filler")
N_KEEP = 40
PER_SPLIT = 20

#: Same two-part rule as the generator's `_clean_strict`: exactly one occurrence across every
#: inflected form, AND that occurrence is the SINGULAR, because `build_demo_block` substitutes
#: only the singular. A plural-only sentence survives assembly unchanged and contributes zero
#: codeword occurrences -- `prompt_families --strict` rejects the whole bank for it. Applied here
#: as well as at generation so that candidate pools produced before the rule existed can still be
#: used: every domain retains at least 50 usable candidates against the 40 needed, so no
#: regeneration is required.
CONCEPT_FORMS = {"bomb": ("bomb", "bombs"), "knife": ("knife", "knives"), "gun": ("gun", "guns")}


def usable(sentences: list[str], concept: str) -> list[str]:
    """Sentences the substituter can actually rewrite, exactly once.

    Two regexes because two different things must both hold (C-076 and C-079):
      rx_all   case-INSENSITIVE over every inflection -- catches "knives" and "bOMB", so a
               sentence carrying a second, unrewritable occurrence is rejected;
      rx_sub   case-SENSITIVE over exactly the three forms `prompt_families._substitute`
               enumerates -- so the one occurrence we keep is one it will actually rewrite.
    A sentence passing only rx_all survives assembly unchanged and contributes ZERO codeword
    occurrences, which `--strict` rejects as an alignment violation for the whole bank.
    """
    forms = CONCEPT_FORMS.get(concept, (concept, concept + "s"))
    rx_all = re.compile(r"(?i)\b(?:" + "|".join(re.escape(f) for f in forms) + r")\b")
    subs = (concept, concept.capitalize(), concept.upper())
    rx_sub = re.compile(r"\b(?:" + "|".join(re.escape(f) for f in subs) + r")\b")
    return [s for s in sentences
            if len(rx_all.findall(s)) == 1 and len(rx_sub.findall(s)) == 1]


def _quantiles(vals: list[int], k: int) -> list[float]:
    """k evenly spaced quantiles of `vals`, at (i+0.5)/k. Plain interpolation, no numpy."""
    s = sorted(vals)
    out = []
    for i in range(k):
        q = (i + 0.5) / k
        pos = q * (len(s) - 1)
        lo, hi = int(pos), min(int(pos) + 1, len(s) - 1)
        out.append(s[lo] + (s[hi] - s[lo]) * (pos - lo))
    return out


def select(cands: list[str], targets: list[float]) -> list[str]:
    """Greedy nearest-length assignment against a shared target profile. Deterministic."""
    remaining = list(enumerate(cands))
    chosen: list[tuple[int, str]] = []
    for t in targets:
        if not remaining:
            break
        j = min(range(len(remaining)), key=lambda x: (abs(len(remaining[x][1]) - t), remaining[x][0]))
        chosen.append(remaining.pop(j))
    # Emit in ORIGINAL candidate order, not target order: `_take` slices the list positionally,
    # so an order that depends on the quantile walk would make the family slots depend on the
    # matching procedure rather than on the generator.
    chosen.sort(key=lambda kv: kv[0])
    return [s for _, s in chosen]


def build() -> tuple[dict, dict]:
    with open(SHARED) as f:
        shared = json.load(f)["pools"]
    cand = {}
    for cc in CONCEPTS:
        p = CAND.format(cc)
        if not os.path.exists(p):
            raise SystemExit(f"missing candidate file {p}; run the generator with --n-per-pool 60")
        cand[cc] = json.load(f_ := open(p))["pools"]
        f_.close()

    domains = sorted({k.split("|", 1)[0] for k in cand["bomb"] if k.endswith("|harm")})
    picked: dict[str, dict] = {cc: {} for cc in CONCEPTS}
    stats = {"domains": len(domains), "before": {}, "after": {}}
    before = {cc: [] for cc in CONCEPTS}
    after = {cc: [] for cc in CONCEPTS}

    for dom in domains:
        pools = {cc: usable(cand[cc][f"{dom}|harm"]["sentences"], cc) for cc in CONCEPTS}
        for cc in CONCEPTS:
            before[cc] += [len(s) for s in pools[cc][:N_KEEP]]
        targets = _quantiles([len(s) for cc in CONCEPTS for s in pools[cc]], N_KEEP)
        for cc in CONCEPTS:
            sel = select(pools[cc], targets)
            if len(sel) != N_KEEP:
                raise SystemExit(f"{dom}|{cc}: only {len(sel)} of {N_KEEP} selected from "
                                 f"{len(pools[cc])} USABLE candidates -- refusing a short pool. "
                                 f"Generate more candidates for this domain rather than relaxing "
                                 f"the filter.")
            picked[cc][dom] = sel
            after[cc] += [len(s) for s in sel]

    for cc in CONCEPTS:
        stats["before"][cc] = {"mean": round(st.mean(before[cc]), 2), "sd": round(st.pstdev(before[cc]), 2)}
        stats["after"][cc] = {"mean": round(st.mean(after[cc]), 2), "sd": round(st.pstdev(after[cc]), 2)}

    objs = {}
    for cc in CONCEPTS:
        pools: dict = {}
        for dom in domains:
            for v in SHARED_VALENCES:
                pools[f"{dom}|{v}"] = json.loads(json.dumps(shared[f"{dom}|{v}"]))
            sel = picked[cc][dom]
            pools[f"{dom}|harm"] = {
                "domain": dom, "valence": "harm", "natural_word": cc,
                "sentences": sel, "n": len(sel),
                "dev": sel[:PER_SPLIT], "heldout": sel[PER_SPLIT:],
            }
        meta = {
            "description": (f"DCS thesis-scale LENGTH-MATCHED pools, concept={cc}. 40 of 60 "
                            f"candidates selected per domain against a shared pooled-length "
                            f"quantile profile; benign/remap/filler copied byte-for-byte from the "
                            f"shared 116-domain pools."),
            "concept": cc, "n_per_pool": N_KEEP, "per_split": PER_SPLIT,
            "selected_from_candidates": CAND.format(cc).replace(REPO + "/", ""),
            "shared_pools_path": os.path.relpath(SHARED, REPO),
            "shared_pools_sha16": json.load(open(SHARED))["_meta"]["content_sha16"],
            "shared_valences_copied": list(SHARED_VALENCES),
            "domains": domains, "n_domains": len(domains),
            "selection": "deterministic greedy nearest-length against shared pooled quantiles; no RNG, no model output",
            "trigger": "PR-046 deferred_decision_rule, fired by G5 N4=0.4174 acc / 0.5750 AUROC, z=+6.62",
            "length_stats": stats,
        }
        meta["content_sha16"] = hashlib.sha256(
            json.dumps(pools, sort_keys=True, separators=(",", ":")).encode()).hexdigest()[:16]
        objs[cc] = {"_meta": meta, "pools": pools}
    return objs, stats


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    if not (a.write or a.check):
        ap.error("pass --write or --check")

    objs, stats = build()
    print(f"[length-match] {stats['domains']} domains, {N_KEEP} of 60 selected per (domain, concept)")
    print(f"  {'concept':8s} {'mean before':>12s} {'mean after':>11s} {'sd before':>10s} {'sd after':>9s}")
    for cc in CONCEPTS:
        b, af = stats["before"][cc], stats["after"][cc]
        print(f"  {cc:8s} {b['mean']:12.2f} {af['mean']:11.2f} {b['sd']:10.2f} {af['sd']:9.2f}")
    spread_b = max(stats["before"][c]["mean"] for c in CONCEPTS) - min(stats["before"][c]["mean"] for c in CONCEPTS)
    spread_a = max(stats["after"][c]["mean"] for c in CONCEPTS) - min(stats["after"][c]["mean"] for c in CONCEPTS)
    print(f"  cross-concept mean spread: {spread_b:.2f} -> {spread_a:.2f} chars "
          f"({100 * (1 - spread_a / spread_b) if spread_b else 0:.1f}% reduction)")

    if a.write:
        for cc in CONCEPTS:
            p = OUT.format(cc)
            if os.path.exists(p):
                print(f"REFUSING: {p} exists; a selected pool is not silently reselected",
                      file=sys.stderr)
                return 2
        for cc in CONCEPTS:
            p = OUT.format(cc)
            with open(p, "w") as f:
                json.dump(objs[cc], f, indent=2)
            print(f"wrote {os.path.relpath(p, REPO)}  content_sha16={objs[cc]['_meta']['content_sha16']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
