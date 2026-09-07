#!/usr/bin/env python3
"""Generate CONCEPT-SPECIFIC HARM pools and merge them onto the SHARED 116-domain pools.

`DCS-C-074`, 2026-09-06. This script exists because of a design error, and the error is worth
stating precisely because the fix is subtle.

THE ERROR. The first thesis-scale banks were built by taking one pools file whose harm pool has
`natural_word = "bomb"` in all 116 domains and asking `prompt_families` for `--concept knife`.
That substitutes bomb->knife in the harm sentences, and every non-concept byte then matches
across concepts. It looked like perfect alignment: 22,272/22,272 rows identical up to a
case-preserving word swap.

It was perfect alignment because THE MANIPULATION WAS GONE. The primary cell C
(`natural_doublespeak`) draws the HARM pool at `demo_surface = "codeword"` -- the concept word is
replaced by `button` before the prompt is assembled. So the concept word never appears in cell C
at all, and once the harm SENTENCES are shared, the bomb, knife and gun prompts are the same
bytes. Measured: cell C x `semantic_one_word` is 1,856/1,856 byte-identical across all three
concepts; 7,424 of 22,272 rows per codeword are identical across bomb AND knife AND gun. A probe
on that population is pinned to exactly 1/3 by arithmetic -- identical inputs, balanced labels --
because a hidden state is a deterministic function of the prompt.

The verification that missed it was mine: "identical up to a swap of word W" and "identical" are
the same statement when W does not occur, and I never counted the occurrences.

WHAT ACTUALLY CARRIES CONCEPT IDENTITY. In doublespeak the codeword STANDS FOR the concept, so
the installed concept is defined by what the harm demonstrations say the codeword AFFORDS --
"a suspicious package resembling a button", "the button was defused" install BOMB; "the button
was sharpened", "the button slipped from the cutting board" would install KNIFE. Identity lives
in the PREDICATES, not in a word that gets substituted away. Mandate §6.1 says exactly this:
keep the benign pool, filler, preamble, skeleton and query byte-identical, and CHANGE ONLY the
harm demonstrations that define the installed concept. The word-swap build changed nothing at
all; the old 6-domain banks changed everything at once (benign, remap and filler were
regenerated per concept too, which is the confound that voided them). This script takes the
middle, which is the one the mandate asked for.

WHAT IT DOES.
  * harm pool        -> GENERATED FRESH for the requested concept, using the domain's own
                        concept-agnostic style hint from `demo_pools.DOMAINS[domain]["harm"]`
                        (they specify register and setting -- "flat incident-log sentences from
                        an airport ground-handling safety inspection" -- never the concept), so
                        knife and gun get naturally knife- and gun-affording sentences in the
                        same frame.
  * benign / remap / filler -> COPIED BYTE-FOR-BYTE from the shared 116-domain pools file.
                        This is what makes the contrast aligned, and it is free.

Generation reuses `prepare_demos.gen_demos` and `demo_pools._clean` unchanged -- the same
generator, the same exactly-one-whole-word filter, the same 8-round retry -- so these pools are
produced by the identical process that produced the bomb pools they will be compared against.
Nothing in `demo_pools.py` or `prompt_families.py` is modified.

⚠ RUN IT ON `cpu-killable`, NEVER THE LOGIN NODE. `import openai` has hung for >90 s under NFS
contention here, and a 0-byte log under `set -e` means HANG, not "nothing ran".

USAGE
    python3 scripts/dcs_ts_gen_concept_harm_pools.py --concept knife --out data/boombness_prompts/demo_pools_116dom_knife.json
    python3 scripts/dcs_ts_gen_concept_harm_pools.py --verify data/boombness_prompts/demo_pools_116dom_knife.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "src", "boombness"))
sys.path.insert(0, os.path.join(REPO, "doublespeak_causality"))

SHARED = os.path.join(REPO, "data", "boombness_prompts", "demo_pools_116dom.json")
SHARED_VALENCES = ("benign", "remap", "filler")   # copied, never regenerated
N_PER_POOL = 40
PER_SPLIT = 20

#: Every surface form of each concept that must be counted as an occurrence.
#:
#: `DCS-C-076`. `demo_pools._clean` keeps a sentence when it contains exactly one match of
#: `\bWORD\b`, and `build_demo_block` substitutes exactly that form. A sentence carrying BOTH
#: `knife` and `knives` therefore passes the filter with a count of one, and the substitution
#: rewrites only the singular -- shipping the literal plural into cell C, which is the one cell
#: whose whole purpose is that the concept word does NOT appear:
#:     "The button rack was overcrowded, making it difficult to access clean knives."
#: Eight such sentences reached the knife pools, 30 of 3680 primary-channel rows, four of them in
#: TEST domains. Bomb and gun happened to escape (0 each), but the defect is general, not
#: knife-specific: nothing in the filter counts `bombs` either. Irregular plurals are listed
#: explicitly rather than guessed from a suffix rule.
CONCEPT_FORMS = {
    "bomb": ("bomb", "bombs"),
    "knife": ("knife", "knives"),
    "gun": ("gun", "guns"),
}


#: The THREE case forms `prompt_families._substitute` actually rewrites. Anything else is invisible
#: to the substituter and survives assembly unchanged.
#:
#: `DCS-C-079`. The generator emitted `A container marked "bOMB" was found...`. A case-INSENSITIVE
#: occurrence check counts that as one occurrence; `_substitute` tries only `bomb`, `Bomb` and
#: `BOMB`, so it rewrote nothing and the demo contributed zero codeword occurrences. `--strict`
#: caught it as an alignment violation and refused to write the bank.
#:
#: This is the third instance of one bug class in this phase, and the pattern is worth naming:
#: THE CHECKER'S NOTION OF "AN OCCURRENCE" MUST BE EXACTLY THE TRANSFORMER'S.
#:   C-075  the finder was right-permissive where the generator was not ("basketball")
#:   C-076  the filter counted only the singular where the text carried a plural ("knives")
#:   C-079  the filter was case-insensitive where the substituter is case-ENUMERATED ("bOMB")
#: Each time the check and the transformation disagreed about what counts, and each time the
#: disagreement was silent. The filter below is written to mirror `_substitute` exactly.

#: `DCS-C-087`, the SEVENTH instance of the class, and this time it is the SUBSTITUTER.
#: `prompt_families._substitute` uses `str.replace`, which has no word-boundary notion at all. So
#: `subway_station|harm[32]` --
#:     "A witness described the gun as a large, black handgun with a silver barrel."
#: -- passes every occurrence rule (one whole-word `gun`, substitutable case) and then ships as
#:     "... a large, black handbutton with a silver barrel."
#: The inflection-aware, case-enumerated rule of C-076/C-079 is blind to COMPOUNDS, and this leaks
#: concept identity LEXICALLY -- only the gun arm contains `hand<codeword>` -- while remaining
#: invisible to any whole-word leakage check.
#:
#: The general rule, which subsumes the special cases: THE SUBSTRING COUNT MUST EQUAL THE
#: WHOLE-WORD COUNT. If `gun` appears 2 times as a substring but once as a word, something in the
#: sentence is a compound the substituter will silently eat.
def has_compound(sentence: str, concept: str) -> bool:
    """True if `concept` appears inside a longer word, where str.replace would still rewrite it."""
    n_sub = len(re.findall(re.escape(concept), sentence, flags=re.I))
    n_word = len(re.findall(r"\b" + re.escape(concept) + r"\w*\b", sentence, flags=re.I))
    return n_sub != n_word


def _substitutable_forms(concept: str):
    """Exactly the forms `_substitute` enumerates -- mirrored, not approximated."""
    return (concept, concept.capitalize(), concept.upper())


def _forms_re(concept: str):
    forms = CONCEPT_FORMS.get(concept, (concept, concept + "s"))
    return re.compile(r"(?i)\b(?:" + "|".join(re.escape(f) for f in forms) + r")\b")


def _clean_strict(sentences, concept: str):
    """Keep sentences with EXACTLY ONE occurrence, counting every inflected form, AND SINGULAR.

    TWO conditions, and the second one was learned the hard way. Requiring only "exactly one
    occurrence counting inflections" admits a sentence whose sole occurrence is the PLURAL --
    "Several bombs were found in the loading bay." `build_demo_block` substitutes only the
    singular form, so such a sentence passes the filter and then survives assembly UNCHANGED,
    contributing ZERO codeword occurrences. `prompt_families --strict` caught it as 170 alignment
    violations of the shape
        {benign_literal: 5, direct_harmful: 4, natural_doublespeak: 4, concept_in_benign_ctx: 5}
    and refused to write anything.

    So the first version of this filter (C-076) fixed one direction and opened the other: the old
    filter let plural-CONTAMINATED sentences through, mine let plural-ONLY sentences through. The
    correct rule is both at once -- exactly one occurrence across all forms, and that occurrence
    is the form the substitution actually rewrites.

    Deduplicates case-insensitively, preserving first-seen order, so selection is deterministic.
    """
    rx = _forms_re(concept)
    subs = _substitutable_forms(concept)
    rx_sing = re.compile(r"\b(?:" + "|".join(re.escape(f) for f in subs) + r")\b")  # case-SENSITIVE
    out, seen = [], set()
    for s in sentences:
        s = s.strip()
        # rx is case-insensitive across inflections (catches "knives" and "bOMB");
        # rx_sing is case-SENSITIVE over exactly the forms _substitute rewrites. Requiring both to
        # equal 1 means: one occurrence in the text, and the substituter can see it.
        if not s or len(rx.findall(s)) != 1 or len(rx_sing.findall(s)) != 1:
            continue
        if has_compound(s, concept):
            continue   # C-087: str.replace would rewrite the concept inside a longer word
        k = s.casefold()
        if k in seen:
            continue
        seen.add(k)
        out.append(s)
    return out


def _content_sha16(pools: dict) -> str:
    """Hash the pool CONTENT in a canonical order, matching the shared file's own convention."""
    blob = json.dumps(pools, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(blob).hexdigest()[:16]


def generate(concept: str, model: str, seed: int, domains: list[str] | None,
             n_per_pool: int = N_PER_POOL) -> dict:
    from openai import OpenAI
    from demo_pools import DOMAINS
    from prepare_demos import gen_demos

    with open(SHARED) as f:
        shared = json.load(f)
    shared_pools = shared["pools"]
    roster = sorted({k.split("|", 1)[0] for k in shared_pools})
    if domains:
        unknown = [d for d in domains if d not in roster]
        if unknown:
            raise SystemExit(f"unknown domain(s): {unknown}")
        roster = [d for d in roster if d in domains]

    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    out: dict = {}
    dropped: dict = {}

    for i, domain in enumerate(roster, 1):
        # Copy the shared valences BYTE-FOR-BYTE. This is the alignment guarantee, and it is a
        # copy rather than a regeneration precisely because regenerating them is what confounded
        # the old 6-domain concept banks.
        for v in SHARED_VALENCES:
            key = f"{domain}|{v}"
            if key not in shared_pools:
                raise SystemExit(f"shared pools are missing {key}; refusing to fabricate it")
            out[key] = json.loads(json.dumps(shared_pools[key]))

        hint = DOMAINS[domain]["harm"]
        kept: list[str] = []
        raw = 0
        for rnd in range(14):
            got = gen_demos(client, model, concept, int(n_per_pool * 2), seed + rnd,
                            style_hint=hint)
            raw += len(got)
            # `_clean_strict`, not `demo_pools._clean`: see CONCEPT_FORMS above (C-076).
            kept = _clean_strict(kept + got, concept)
            if len(kept) >= n_per_pool:
                break
        if len(kept) < n_per_pool:
            # Fail loudly. A short pool silently changes what `_take` returns for every family
            # slot in that domain, which would break the cross-concept row correspondence.
            raise RuntimeError(
                f"{domain}|harm reached only {len(kept)}/{n_per_pool} sentences with exactly one "
                f"whole-word {concept!r} after 8 rounds ({raw} raw). Refusing to ship a short pool."
            )
        kept = kept[:n_per_pool]
        dropped[f"{domain}|harm"] = raw - len(kept)
        rec = {"domain": domain, "valence": "harm", "natural_word": concept,
               "sentences": kept, "n": len(kept)}
        if n_per_pool == N_PER_POOL:
            # A finished pool carries its own dev/heldout cut. A CANDIDATE pool does not: the
            # split must be applied AFTER length matching selects the final 40, or the two halves
            # would be cut from a set that is about to change.
            rec["dev"] = kept[:PER_SPLIT]
            rec["heldout"] = kept[PER_SPLIT:]
        else:
            rec["candidates"] = True
        out[f"{domain}|harm"] = rec
        print(f"[{i:3d}/{len(roster)}] {domain}|harm  n={len(kept)}  dropped={raw - len(kept)}",
              flush=True)

    meta = {
        "description": (f"DCS thesis-scale pools for concept={concept}: harm regenerated with the "
                        f"domain's concept-agnostic style hint; benign/remap/filler copied "
                        f"byte-for-byte from the shared 116-domain pools so the concept contrast "
                        f"is aligned in everything except the harm demonstrations."),
        "generator": model, "openai_seed": seed, "n_per_pool": n_per_pool,
        "per_split": PER_SPLIT, "concept": concept, "codeword": "carrot",
        "shared_pools_path": os.path.relpath(SHARED, REPO),
        "shared_pools_sha16": shared["_meta"]["content_sha16"],
        "shared_valences_copied": list(SHARED_VALENCES),
        "domains": roster, "n_domains": len(roster),
        "dropped_for_occurrence_ne_1": dropped,
        "content_sha16": _content_sha16(out),
    }
    return {"_meta": meta, "pools": out}


def verify(path: str) -> int:
    """Re-derive the two properties the merge exists to guarantee. Fails on an empty set."""
    with open(path) as f:
        obj = json.load(f)
    with open(SHARED) as f:
        shared = json.load(f)["pools"]
    pools = obj["pools"]
    concept = obj["_meta"]["concept"]
    errs, n_shared_checked, n_harm_checked = [], 0, 0

    if not pools:
        errs.append("pools is EMPTY -- every check below would pass over nothing")

    for key, pool in sorted(pools.items()):
        dom, val = key.split("|", 1)
        if val in SHARED_VALENCES:
            # PROPERTY 1: the shared valences are byte-identical to the shared file.
            n_shared_checked += 1
            if key not in shared:
                errs.append(f"{key}: absent from the shared pools file")
            elif json.dumps(pool, sort_keys=True) != json.dumps(shared[key], sort_keys=True):
                errs.append(f"{key}: NOT byte-identical to the shared pools file")
        elif val == "harm":
            # PROPERTY 2: the harm pool actually carries this concept, and only this concept.
            n_harm_checked += 1
            if pool.get("natural_word") != concept:
                errs.append(f"{key}: natural_word={pool.get('natural_word')!r} != {concept!r}")
            want_n = obj["_meta"].get("n_per_pool", N_PER_POOL)
            if len(pool.get("sentences", [])) != want_n:
                errs.append(f"{key}: {len(pool.get('sentences', []))} sentences, want {want_n}")
            rx = _forms_re(concept)
            for i, s in enumerate(pool.get("sentences", [])):
                # Count EVERY inflected form (C-076). Counting only the exact form is what let
                # eight `knife`+`knives` sentences ship an unsubstituted plural into cell C.
                n = len(rx.findall(s))
                if n != 1:
                    errs.append(f"{key}[{i}]: {n} occurrence(s) of {concept!r} counting "
                                f"inflections {CONCEPT_FORMS.get(concept)}, want exactly 1: {s[:80]!r}")
            for other in ("bomb", "knife", "gun"):
                if other == concept:
                    continue
                hits = [i for i, s in enumerate(pool.get("sentences", []))
                        if re.search(rf"(?i)\b{other}s?\b", s)]
                if hits:
                    errs.append(f"{key}: {len(hits)} sentence(s) mention the OTHER concept "
                                f"{other!r} (indices {hits[:5]}) -- concept substitution")
        else:
            errs.append(f"{key}: unexpected valence {val!r}")

    if n_shared_checked == 0:
        errs.append("checked ZERO shared-valence pools -- the alignment check bound nothing")
    if n_harm_checked == 0:
        errs.append("checked ZERO harm pools -- the concept-backing check bound nothing")

    if errs:
        for e in errs[:40]:
            print(f"  FAIL {e}", file=sys.stderr)
        print(f"[gen-harm-pools] {len(errs)} failure(s) over {n_shared_checked} shared and "
              f"{n_harm_checked} harm pools", file=sys.stderr)
        return 1
    print(f"[gen-harm-pools] OK: {n_shared_checked} shared pools byte-identical to "
          f"{os.path.basename(SHARED)}; {n_harm_checked} harm pools carry exactly one "
          f"whole-word {concept!r} per sentence and no other concept")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--concept")
    ap.add_argument("--out")
    ap.add_argument("--model", default="gpt-4o-mini")
    ap.add_argument("--seed", type=int, default=20260906)
    ap.add_argument("--domains", default="", help="comma list; default all 116")
    ap.add_argument("--n-per-pool", type=int, default=N_PER_POOL,
                    help="set >40 to emit a CANDIDATE pool for scripts/dcs_ts_length_match_pools.py")
    ap.add_argument("--verify", metavar="POOLS_JSON")
    a = ap.parse_args()

    if a.verify:
        return verify(a.verify)
    if not (a.concept and a.out):
        ap.error("pass --concept and --out, or --verify")
    if os.path.exists(a.out):
        print(f"REFUSING: {a.out} exists. Generated pools are not silently regenerated -- a "
              f"second run with a different seed would change every bank joined to it.",
              file=sys.stderr)
        return 2

    doms = [d for d in a.domains.split(",") if d] or None
    obj = generate(a.concept, a.model, a.seed, doms, n_per_pool=a.n_per_pool)
    tmp = f"{a.out}.tmp.{os.getpid()}"
    with open(tmp, "w") as f:
        json.dump(obj, f, indent=2)
    os.replace(tmp, a.out)
    print(f"wrote {a.out}  content_sha16={obj['_meta']['content_sha16']}  "
          f"{obj['_meta']['n_domains']} domains")
    return verify(a.out)


if __name__ == "__main__":
    raise SystemExit(main())
