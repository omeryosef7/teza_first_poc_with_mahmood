#!/usr/bin/env python3
"""Gates G1-G3 for the `ts116n` aligned concept banks.  `DCS-PR-046`.

THIS FILE EXISTS BECAUSE OF `DCS-C-074`. The previous bank family passed an alignment check of
the form *"every row is identical across concepts up to a swap of the concept word"* -- and it
passed **because the concept word did not occur**, so the three arms were literally the same
bytes and the probe was pinned to 1/3 by arithmetic. The check was true and useless.

The lesson generalises: an alignment check alone can only ever fail in one direction. It must be
paired with a check that the MANIPULATION SURVIVED. So the gates come in a matched pair, and
neither is allowed to pass alone:

  G2  cell C x semantic_one_word must **DIFFER** across concepts in **115/115 domains**
      (116 minus the one prompt-only exclusion below)
      -- the manipulation exists. This is the exact inverse of the 1856/1856 identity
      that voided R-098, and it is the gate whose absence caused that error.

  G3  cell A (benign_literal) must be **BYTE-IDENTICAL** across concepts
      -- everything that is not the manipulation is shared. Without this we are back to
      `A-034.1`, where each concept had its own freshly generated corpus and the probe could
      have been separating three corpora rather than three concepts.

  G1  the three harm pool files verify: shared valences byte-identical to the shared pools file,
      every harm sentence carrying exactly one whole-word target concept and no other concept.

G4 (concept backing) and G5 (leakage) are separate re-runs of the existing audit scripts against
the new banks; they are NOT re-implemented here.

Every check re-derives from the raw bank rows. None of them reads a producer-written summary
field -- `C-075` is this repo's live example of a checker that compared a matcher against a field
the same matcher generated, agreed with itself, and saw nothing. A check that binds zero rows is
reported RED, never as a pass over the empty set (`C-071`).

USAGE
    python3 scripts/dcs_ts_verify_ts116n.py
    python3 scripts/dcs_ts_verify_ts116n.py --mutate     # prove every gate can fail
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DP = os.path.join(REPO, "data", "boombness_prompts")
SHARED = os.path.join(DP, "demo_pools_116dom.json")
CONCEPTS = ("bomb", "knife", "gun")
CODEWORDS = ("button", "basket")
SHARED_VALENCES = ("benign", "remap", "filler")

#: Domains excluded from the analysis population, PROMPT-ONLY and PROSPECTIVELY.
#:
#: `restaurant_kitchen` is a kitchen: knives are its natural furniture, so a bomb or gun harm pool
#: generated for it keeps producing sentences that name a knife --
#:     bomb[39] "A misplaced knife on the edge of the counter was a potential bomb hazard."
#:     gun[19]  "...whether a gun or a knife is the better tool for a chef."
#: Regenerating the domain at a second seed (20260907) cleaned bomb and knife and left gun
#: contaminated again. That is the domain, not the draw, and a third bump would start to be
#: selection rather than repair.
#:
#: Excluding it makes all three ORIGINAL uniform-seed-20260906 pools fully clean (0 contaminated
#: sentences across 13,920), which is strictly better than a per-domain patchwork of seeds: every
#: surviving domain comes from one generation family with one seed. It sits in TRAIN, so
#: validation and test stay at 23/23 and the power analysis is unaffected; the split becomes
#: 69/23/23 over 115 domains.
#:
#: This is decided on prompt text alone, before any extraction, and is recorded in
#: `configs/dcs_ts_pr046.json` -- not applied after seeing an outcome.
EXCLUDED_DOMAINS = frozenset({"restaurant_kitchen"})

#: `DCS-C-080`. THIS GATE WAS ITSELF BLIND, and it is the fourth instance of the class named in
#: `C-079`: the checker's notion of "an occurrence" must be exactly the transformer's.
#:
#: G1's own-concept check counted `\bknife\b` -- singular, case-insensitive -- and therefore
#: reported "0 sentence(s) not exactly one whole-word 'knife'" over a pools file carrying EIGHT
#: `knife`+`knives` sentences. The generator's verifier reported 8 failures on the same bytes at
#: the same time. So `R-101`'s published "19/19 PASS" was green from a gate that could not see
#: `C-076`, and this gate is the one the build script names as required before extraction.
#:
#: The rule is now shared with the generator and the length matcher instead of being restated:
#:   * count case-INSENSITIVELY across every inflected form -- catches `knives` and `bOMB`;
#:   * require the surviving occurrence to be one of the three case forms `_substitute` rewrites.
CONCEPT_FORMS = {"bomb": ("bomb", "bombs"), "knife": ("knife", "knives"), "gun": ("gun", "guns")}


def occurrence_counts(sentence: str, concept: str) -> tuple[int, int]:
    """(occurrences across all inflections, occurrences the substituter can rewrite)."""
    forms = CONCEPT_FORMS.get(concept, (concept, concept + "s"))
    n_all = len(re.findall(r"(?i)\b(?:" + "|".join(re.escape(f) for f in forms) + r")\b", sentence))
    subs = (concept, concept.capitalize(), concept.upper())
    n_sub = len(re.findall(r"\b(?:" + "|".join(re.escape(f) for f in subs) + r")\b", sentence))
    return n_all, n_sub
N_DOMAINS = 116 - len(EXCLUDED_DOMAINS)


#: Which bank family to gate. ts116n is the first per-concept-harm build; ts116m adds the C-076
#: inflection filter and the C-077 length matching. Env-selected so the SAME gate code runs on
#: both -- a second copy of a verifier is a second place for the gates to drift.
BANK_TAG = os.environ.get("BANK_TAG", "ts116n")
POOLS_TAG = os.environ.get("POOLS_TAG", "ts")


def bank_path(cw: str, cc: str) -> str:
    return os.path.join(DP, f"boombness_prompt_bank_{BANK_TAG}_{cw}_{cc}.jsonl")


def pool_path(cc: str) -> str:
    return os.path.join(DP, f"demo_pools_116dom_{POOLS_TAG}_{cc}.json")


def load_bank(p: str) -> dict:
    out = {}
    with open(p) as f:
        for line in f:
            r = json.loads(line)
            out[r["prompt_id"]] = r
    return out


class Result:
    def __init__(self) -> None:
        self.rows: list[tuple[str, bool, str]] = []

    def add(self, gate: str, ok: bool, msg: str) -> None:
        self.rows.append((gate, ok, msg))

    def report(self) -> int:
        bad = [r for r in self.rows if not r[1]]
        for gate, ok, msg in self.rows:
            print(f"  {'PASS' if ok else 'FAIL'}  {gate:34s} {msg}")
        print(f"[verify-ts116n] {len(self.rows) - len(bad)}/{len(self.rows)} gates pass")
        return 1 if bad else 0


def g1_pools(res: Result, mutate: str | None = None) -> None:
    """Harm pools carry their own concept and no other; shared valences are the shared file's."""
    with open(SHARED) as f:
        shared = json.load(f)["pools"]
    for cc in CONCEPTS:
        p = pool_path(cc)
        if not os.path.exists(p):
            res.add(f"G1[{cc}] file", False, f"missing {os.path.relpath(p, REPO)}")
            continue
        with open(p) as f:
            pools = json.load(f)["pools"]

        if mutate == f"g1_share_{cc}":
            k = next(k for k in pools if k.endswith("|benign"))
            pools[k] = json.loads(json.dumps(pools[k]))
            pools[k]["sentences"] = list(pools[k]["sentences"])
            pools[k]["sentences"][0] += " MUTATED"
        if mutate == f"g1_other_{cc}":
            k = next(k for k in pools if k.endswith("|harm"))
            pools[k]["sentences"][0] = "A gun was found next to the " + cc + "."

        n_shared = n_harm = 0
        bad_shared, bad_occ, bad_other = [], [], []
        for key, pool in pools.items():
            val = key.split("|", 1)[1]
            if val in SHARED_VALENCES:
                n_shared += 1
                if key not in shared or json.dumps(pool, sort_keys=True) != json.dumps(shared[key], sort_keys=True):
                    bad_shared.append(key)
            elif val == "harm":
                if key.split("|", 1)[0] in EXCLUDED_DOMAINS:
                    continue
                n_harm += 1
                for i, s in enumerate(pool["sentences"]):
                    n_all, n_sub = occurrence_counts(s, cc)
                    if n_all != 1 or n_sub != 1:
                        bad_occ.append(f"{key}[{i}](all={n_all},sub={n_sub})")
                    for other in CONCEPTS:
                        if other != cc and re.search(rf"(?i)\b{other}s?\b", s):
                            bad_other.append(f"{key}[{i}]->{other}")

        # A gate that bound nothing is RED, not green.
        if n_shared == 0 or n_harm == 0:
            res.add(f"G1[{cc}] binding", False,
                    f"bound {n_shared} shared and {n_harm} harm pools -- ZERO BINDING")
            continue
        res.add(f"G1[{cc}] shared byte-identical", not bad_shared,
                f"{n_shared - len(bad_shared)}/{n_shared} pools identical to demo_pools_116dom.json"
                + (f"; first bad {bad_shared[:2]}" if bad_shared else ""))
        res.add(f"G1[{cc}] exactly-one-substitutable-{cc}", not bad_occ,
                f"{n_harm} harm pools, {len(bad_occ)} sentence(s) without exactly one "
                f"SUBSTITUTABLE {cc!r} (inflection-aware, case-enumerated)"
                + (f"; first {bad_occ[:2]}" if bad_occ else ""))
        res.add(f"G1[{cc}] no other concept", not bad_other,
                f"{len(bad_other)} sentence(s) mention another concept"
                + (f"; first {bad_other[:2]}" if bad_other else ""))


def g2_g3(res: Result, mutate: str | None = None) -> None:
    """The matched pair: the manipulation exists (G2) and everything else is shared (G3)."""
    for cw in CODEWORDS:
        banks = {}
        for cc in CONCEPTS:
            p = bank_path(cw, cc)
            if not os.path.exists(p):
                res.add(f"G2/G3[{cw}] banks", False, f"missing {os.path.basename(p)}")
                return
            banks[cc] = load_bank(p)

        ref = banks["bomb"]
        if mutate == f"g2_{cw}":
            # Make cell C identical again -- the exact C-074 shape. G2 must go RED.
            for pid, r in ref.items():
                if r["cell"] == "C" and r["query_kind"] == "semantic_one_word":
                    for cc in ("knife", "gun"):
                        banks[cc][pid] = dict(banks[cc][pid], full_prompt=r["full_prompt"])
        if mutate == f"g3_{cw}":
            # Perturb one cell-A row -- the A-034.1 shape. G3 must go RED.
            pid = next(p for p, r in ref.items() if r["cell"] == "A")
            banks["knife"][pid] = dict(banks["knife"][pid],
                                       full_prompt=banks["knife"][pid]["full_prompt"] + " X")

        # ---- G2: cell C x semantic_one_word DIFFERS, per DOMAIN ----
        diff_doms: dict[str, set] = collections.defaultdict(set)
        seen_doms: set = set()
        n_rows = 0
        for pid, r in ref.items():
            if r["cell"] != "C" or r["query_kind"] != "semantic_one_word":
                continue
            if r["domain"] in EXCLUDED_DOMAINS:
                continue
            n_rows += 1
            seen_doms.add(r["domain"])
            for cc in ("knife", "gun"):
                if banks[cc][pid]["full_prompt"] != r["full_prompt"]:
                    diff_doms[cc].add(r["domain"])
        if n_rows == 0 or not seen_doms:
            res.add(f"G2[{cw}] binding", False, "bound ZERO cell-C semantic_one_word rows")
            continue
        for cc in ("knife", "gun"):
            n = len(diff_doms[cc])
            res.add(f"G2[{cw}] bomb vs {cc} DIFFERS",
                    n == N_DOMAINS and len(seen_doms) == N_DOMAINS,
                    f"{n}/{len(seen_doms)} domains differ (need {N_DOMAINS}/{N_DOMAINS}) "
                    f"over {n_rows} rows")

        # ---- G3: cell A ----
        #
        # SPLIT INTO TWO, and this is a correction of my own gate rather than a relaxation of it.
        # The first version demanded that EVERY cell-A row be byte-identical across concepts and
        # failed at exactly 3680/5520 = 2/3. The differing third is entirely
        # `semantic_forced_choice`, whose QUESTION names the concept by construction:
        #     "does the word button refer to a button or to a bomb?"  vs  "... or to a knife?"
        # That is the readout instrument, not the demonstrations, and it is the very property that
        # makes forced-choice the DISPLAY channel and `semantic_one_word` the mechanistic one.
        # Conflating the two made G3 test something it never meant to test.
        #
        # So: G3a asserts byte-identity on the concept-free channels, which is what "everything
        # that is not the manipulation is shared" actually means; and G3b BOUNDS the forced-choice
        # difference -- demo block and preamble identical, difference confined to the query. G3b
        # is a new obligation, so the pair is strictly stronger than the single gate it replaces.
        CONCEPT_FREE = ("behavioral", "semantic_one_word")
        nA = same = 0
        for pid, r in ref.items():
            if r["cell"] != "A" or r["domain"] in EXCLUDED_DOMAINS:
                continue
            if r["query_kind"] not in CONCEPT_FREE:
                continue
            nA += 1
            if all(banks[cc][pid]["full_prompt"] == r["full_prompt"] for cc in ("knife", "gun")):
                same += 1
        if nA == 0:
            res.add(f"G3a[{cw}] binding", False, "bound ZERO concept-free cell-A rows")
            continue
        res.add(f"G3a[{cw}] cell A concept-free identical", same == nA,
                f"{same}/{nA} rows identical across all three concepts "
                f"(channels {'+'.join(CONCEPT_FREE)})")

        nF = ok_demo = ok_query = 0
        for pid, r in ref.items():
            if r["cell"] != "A" or r["domain"] in EXCLUDED_DOMAINS:
                continue
            if r["query_kind"] != "semantic_forced_choice":
                continue
            nF += 1
            if all(banks[cc][pid]["demo_block"] == r["demo_block"]
                   and banks[cc][pid]["preamble"] == r["preamble"] for cc in ("knife", "gun")):
                ok_demo += 1
            # the query must differ ONLY by the concept noun: substituting it back must restore
            # the reference exactly. Anything else means the instrument is carrying more than its
            # own label.
            good = True
            for cc in ("knife", "gun"):
                q = re.sub(rf"\b{cc}\b", "bomb", banks[cc][pid]["final_query_text"])
                if q != r["final_query_text"]:
                    good = False
            ok_query += good
        if nF == 0:
            res.add(f"G3b[{cw}] binding", False, "bound ZERO forced-choice cell-A rows")
            continue
        res.add(f"G3b[{cw}] fc demos+preamble identical", ok_demo == nF,
                f"{ok_demo}/{nF} forced-choice rows share demo_block and preamble")
        res.add(f"G3b[{cw}] fc differs ONLY by concept noun", ok_query == nF,
                f"{ok_query}/{nF} queries restore exactly under concept->bomb substitution")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mutate", action="store_true")
    a = ap.parse_args()

    print("=== ts116n gates G1-G3 ===")
    res = Result()
    g1_pools(res)
    g2_g3(res)
    rc = res.report()

    if a.mutate:
        print("\n=== mutation harness: every gate must be demonstrably falsifiable ===")
        muts = [f"g1_share_{CONCEPTS[1]}", f"g1_other_{CONCEPTS[1]}",
                f"g2_{CODEWORDS[0]}", f"g3_{CODEWORDS[0]}"]
        n_red = 0
        for m in muts:
            r2 = Result()
            g1_pools(r2, mutate=m)
            g2_g3(r2, mutate=m)
            failed = [g for g, ok, _ in r2.rows if not ok]
            red = bool(failed)
            n_red += red
            print(f"  {'RED  ' if red else 'GREEN'}  {m:22s} -> {len(failed)} gate(s) fail "
                  f"{failed[:2]}")
        print(f"[mutate] {n_red}/{len(muts)} mutations turned a gate RED")
        if n_red != len(muts):
            print("  A MUTATION THAT DOES NOT GO RED MEANS THAT GATE CANNOT FAIL.", file=sys.stderr)
            return 1
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
