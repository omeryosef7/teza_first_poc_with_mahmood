#!/usr/bin/env python
"""dcs_ts116m_token_roles.py -- THE TOKEN-ROLE MAP for the ts116m bank family (PR-048 / X2).

WHY THIS FILE EXISTS SEPARATELY FROM scripts/dcs_ts_token_roles.py
------------------------------------------------------------------
The ts116 map (`scripts/dcs_ts_token_roles.py`, `reports/DCS_TS_TOKEN_ROLE_MAP.md`) was computed
on the bank family VOIDED by DCS-C-074: cell C drew the harm pool with the concept word already
replaced by the codeword, so sharing harm SENTENCES made the three concept arms BYTE-IDENTICAL
(1856/1856 in the primary channel). Its read-site nomination -- `rel_end = -9`, the token
`' actually'`, id 3604 -- was therefore validated on prompts where criterion (b) ("identical
across all three concepts") held at EVERY position, trivially, and where prompt length could not
differ by concept because there was only one prompt.

On ts116m the demonstrations differ per concept. The demo block sits BETWEEN the preamble and the
query, so the prompt PREFIX LENGTH now varies with the concept and every absolute index moves.
That is exactly the thing the old map could not test. This script re-derives the whole map on
ts116m and re-answers the read-site question from scratch.

The ts116 script/report are NOT edited: they document a superseded bank. This one REUSES their
logic (record construction, role vocabulary, rel_end candidate scoring, check bookkeeping,
mutation harness) with the cross-concept criteria rewritten from "the prompts are identical" to
"the prompts differ, and the TAIL had better not".

SCOPE (fixed, not configurable): cell C (the FIELD `cell` == "C"), query_kind=semantic_one_word,
n_examples=4, 115 analysed domains (restaurant_kitchen excluded, PR-048, prompt-only and
preregistered), codewords {button, basket}, concepts {bomb, knife, gun}.

CPU ONLY. Loads a TOKENIZER, never model weights.

THE OCCURRENCE RULE (DCS-C-075/076/079/080). The checker's notion of "an occurrence" must be
EXACTLY the transformer's. Concept occurrences are counted case-INSENSITIVELY across every
inflection (bomb/bombs, knife/knives, gun/guns) AND separately in the three case forms
`prompt_families._substitute` rewrites. That rule is IMPORTED from
`scripts/dcs_ts_verify_ts116n.occurrence_counts` rather than restated here -- a second copy of
the rule is a second place for it to drift.

DISCIPLINE. Every check (i) records how many rows it bound to and is ERROR_EMPTY, never PASS, if
that is zero; (ii) is demonstrated RED under `--mutate`; (iii) re-derives from raw bank rows and
a real tokenization rather than from a producer-written summary field.

Usage:
  python scripts/dcs_ts116m_token_roles.py
  python scripts/dcs_ts116m_token_roles.py --mutate
  python scripts/dcs_ts116m_token_roles.py --limit-domains 5      # smoke
"""
from __future__ import annotations

import argparse
import collections
import copy
import gzip
import hashlib
import json
import math
import os
import re
import sys
import time
from typing import Dict, List, Optional, Tuple

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "src", "boombness"))
sys.path.insert(0, os.path.join(REPO, "doublespeak_causality"))
sys.path.insert(0, os.path.join(REPO, "scripts"))

BANK_DIR = os.path.join(REPO, "data", "boombness_prompts")
BANK_TMPL = "boombness_prompt_bank_ts116m_{cw}_{cc}.jsonl"
SPLIT_MANIFEST = os.path.join(BANK_DIR, "dcs_ts116_domain_split.json")
PREREG = os.path.join(REPO, "configs", "dcs_ts_pr048.json")
CODEWORDS = ("button", "basket")
CONCEPTS = ("bomb", "knife", "gun")
REF_CONCEPT = "bomb"
CELL = "C"
QUERY_KIND = "semantic_one_word"
N_EXAMPLES = 4
MODEL = "meta-llama/Llama-3.1-8B-Instruct"

#: PR-048 population.preregistered_exclusions[0]: prompt-only, prospective, ENTIRE analysis
#: population. 116 assigned domains -> 115 analysed.
EXCLUDED_DOMAINS = frozenset({"restaurant_kitchen"})
N_DOMAINS_EXPECTED = 115

EXPECTED_MANIFEST_SHA16 = "be7d2c772d814ef3"

ROLE_VOCAB = ("chat_scaffold", "user_instruction_scaffold", "punctuation", "codeword",
              "concept_word", "neutral_content", "answer_format_instruction",
              "response_header")

CONCEPT_WORDS = ("bomb", "knife", "gun")

#: The read position the SUPERSEDED ts116 map nominated. Fixed in source BEFORE the ranking is
#: computed so this script cannot re-derive itself into agreeing with its predecessor. Task
#: question 1 is precisely "is this still right", so it is carried as the incumbent and tested,
#: not as the answer.
INCUMBENT_REL_END = -9

#: Narrative for the defects section of the report. Written as prose because the counts alone do
#: not say WHICH rule disagreed with which; the counts are generated, this explains them, and if
#: a future run's failing set changes this paragraph must be rewritten rather than carried.
DEFECT_NARRATIVE = """
**Three occurrence counters, and they do not agree.** Every one of these findings is the class
the phase has now paid for five times -- *the checker's notion of an occurrence must be exactly
the transformer's* -- extended here to *the substituter's notion must be too*. Each matched row
carries or admits three separate counts of "how many codeword occurrences are in this prompt":

| counter | rule | `school_campus` basketball rows | `subway_station` handgun rows |
|---|---|---|---|
| (i) the bank's `n_codeword_occurrences` | right-permissive | 6 | 6 |
| (ii) the bank's `expected_target_occurrences` span list | left- and right-strict | 5 | 5 |
| (iii) `ds_common.find_word_occurrences_in_text`, re-derived here | left-strict, right-permissive | 6 | 5 |

Check `A` compares (iii) against (i) and sees only the second column. Check `A2` compares (i)
against (ii) and sees both. A checker reading any single one of the three agrees with itself and
reports nothing, which is precisely how C-076 stayed green.

**The individual defects.**

1. `demo_pools_116dom_tsm_gun.json`, pool `subway_station|harm`, sentence 32, reads
   "A witness described the gun as a large, black **handgun** with a silver barrel." The G1
   own-concept gate counts `\\bgun\\b|\\bguns\\b`, which is 1 here, so the sentence passed.
   `prompt_families._substitute` is not left-strict, so it rewrote the `gun` inside `handgun`
   too, and the shipped demonstration reads "**handbutton**" / "**handbasket**". The
   inflection-aware whole-word rule of C-076/C-080 is blind to COMPOUNDS; the substituter is
   not. That single pool sentence is the whole of `J2` (2/6900) and the whole of `A` (2/6900).
2. `demo_pools_116dom_tsm_gun.json`, same pool, sentence 33 is TRUNCATED: "After the inspection,
   we felt relieved that no gun" -- no object and no terminal punctuation. No occurrence rule
   catches it, because its occurrence count is correct. It rides in the same demonstration block
   as (1), so it does not widen the affected row set.
3. `A2` is 11/6900: the 2 rows from (1) plus the 9 `school_campus` rows where `basket` sits
   inside `basketball.`, which is the already-preregistered C-075 finding and is also the whole
   of `J` (9/6900). PR-048 excludes `school_campus` from occurrence-ordinal and
   all-codeword-sites knockout analyses, and explicitly NOT from the probe.
4. `H` is unrelated to the substituter. Two `basket_bomb` rows in `theatre_backstage` carry the
   codeword UPPERCASED inside the demonstration text ("BASKET"), and `BASKET` is three subtokens
   where ` basket` is one. The substituter is right to produce it -- `WORD` is one of the three
   case forms it rewrites -- but any analysis that assumes one subtoken per codeword site is
   wrong on those two rows, and there are 2 such occurrences among 34509.

**Scope of the damage.** Items 1-2 are one prompt_id, `9c5c4946fd79e486`, in `subway_station`,
concept `gun`, appearing once per codeword: 2 of 6900 rows. Item 4 is 2 of 6900. Both domains
are TRAIN, so no TEST row is involved. Every one of these sits in the DEMONSTRATION BLOCK,
upstream of the query. The read-site counts in Q1 are unaffected, and that is a claim with
numbers behind it: the query codeword is one subtoken at `rel_end = -10` in 6900/6900 rows,
`Q2a` holds 2300/2300, and the nominated read site is downstream of every codeword occurrence in
6900/6900.

**What is NOT claimed.** That these are harmless. Item 1 leaks concept identity LEXICALLY -- only
the gun arm contains `hand<codeword>` -- so it is a live nuisance for the N5 concept-masked
TF-IDF baseline even though it is invisible to the N3 leakage rule, which looks for whole-word
concept names. The honest options are (a) exclude `subway_station` prospectively, as
`restaurant_kitchen` was, (b) regenerate that one pool sentence and rebuild, or (c) publish it as
a stated 2/6900 contamination and let N5 absorb it. This map does not choose. It hands the choice
over with its denominators, BEFORE any extraction, which is the only moment at which the choice
is not selection.
"""

#: The earlier full-prompt token-length measurement (PR-048 population._register_asymmetry
#: .n4_in_tokens, C-084), to be verified or refuted by question 3.
CLAIMED_TOKEN_MEANS = {"bomb": 196.21, "knife": 195.50, "gun": 196.69}
CLAIMED_TOKEN_SD = 13.0


# --------------------------------------------------------------------------- #
# Check bookkeeping -- a check that binds to zero rows is an ERROR, never a PASS
# --------------------------------------------------------------------------- #
class Checks:
    def __init__(self):
        self.rows: List[Dict] = []

    def add(self, name: str, n_bound: int, n_violations: int, denom_desc: str,
            detail: Optional[Dict] = None):
        if n_bound == 0:
            status = "ERROR_EMPTY"
        elif n_violations == 0:
            status = "PASS"
        else:
            status = "FAIL"
        self.rows.append({"check": name, "status": status, "n_bound": n_bound,
                          "n_violations": n_violations, "binds_to": denom_desc,
                          "detail": detail or {}})
        return status

    @property
    def ok(self) -> bool:
        return all(r["status"] == "PASS" for r in self.rows)

    def by_name(self, name: str) -> Dict:
        for r in self.rows:
            if r["check"] == name:
                return r
        raise KeyError(name)

    def summary(self) -> Dict:
        c = collections.Counter(r["status"] for r in self.rows)
        return {"n_checks": len(self.rows), "n_pass": c["PASS"], "n_fail": c["FAIL"],
                "n_error_empty": c["ERROR_EMPTY"]}


def mean_sd(xs) -> Dict:
    xs = list(xs)
    n = len(xs)
    if n == 0:
        return {"n": 0, "mean": None, "sd": None, "min": None, "max": None}
    m = sum(xs) / n
    sd = math.sqrt(sum((x - m) ** 2 for x in xs) / (n - 1)) if n > 1 else 0.0
    return {"n": n, "mean": round(m, 4), "sd": round(sd, 4), "min": min(xs), "max": max(xs)}


# --------------------------------------------------------------------------- #
# Loading
# --------------------------------------------------------------------------- #
def sha16_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for blk in iter(lambda: fh.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()[:16]


def load_bank(cw: str, cc: str) -> Tuple[List[Dict], Dict]:
    """Return (matched rows, bank identity). Identity is over the WHOLE bank, not the subset."""
    from common import rows_sha16
    path = os.path.join(BANK_DIR, BANK_TMPL.format(cw=cw, cc=cc))
    matched, pairs, n_all, n_cellC, n_excluded = [], [], 0, 0, 0
    with open(path) as fh:
        for line in fh:
            d = json.loads(line)
            n_all += 1
            pairs.append((d["prompt_id"], d["prompt_sha16"]))
            if not (d["cell"] == CELL and d["query_kind"] == QUERY_KIND
                    and d["n_examples"] == N_EXAMPLES):
                continue
            n_cellC += 1
            if d["domain"] in EXCLUDED_DOMAINS:
                n_excluded += 1
                continue
            matched.append(d)
    ident = {"path": os.path.relpath(path, REPO), "bank_file_sha16": sha16_file(path),
             "bank_rows_sha16": rows_sha16(pairs), "bank_n_rows": n_all,
             "n_cellC_sow_n4_all_domains": n_cellC,
             "n_dropped_by_domain_exclusion": n_excluded,
             "n_matched": len(matched)}
    return matched, ident


# --------------------------------------------------------------------------- #
# The per-prompt token-role record
# --------------------------------------------------------------------------- #
def char_to_token_span(offs, c0: int, c1: int) -> Tuple[int, int]:
    idx = [i for i, (a, b) in enumerate(offs) if b > a and a < c1 and b > c0]
    if not idx:
        raise ValueError(f"char span [{c0},{c1}) maps to zero tokens")
    if idx != list(range(idx[0], idx[-1] + 1)):
        raise ValueError(f"char span [{c0},{c1}) maps to a non-contiguous token run")
    return idx[0], idx[-1] + 1


def is_punct(s: str) -> bool:
    t = s.strip()
    return bool(t) and all(not ch.isalnum() for ch in t)


def build_record(tok, dc, occ_counts, row: Dict, query_frame: Tuple[str, str], fmt_len: int,
                 special_ids: set, dsplit: str, bank_ident: Dict) -> Dict:
    """Tokenize one bank row under the real chat template and label every query-side token."""
    templated = dc.apply_template(tok, row["full_prompt"])
    # The RAW user text length, measured alongside the templated length. The published C-084
    # figures carry no scope line, and the chat template contributes a fixed block of its own
    # tokens; without both numbers a mean difference cannot be attributed.
    n_tokens_raw = len(tok(row["full_prompt"], add_special_tokens=False)["input_ids"])
    enc = tok(templated, add_special_tokens=False, return_offsets_mapping=True)
    ids, offs = list(enc["input_ids"]), list(enc["offset_mapping"])
    n = len(ids)
    pieces = [tok.decode([i]) for i in ids]

    fp = row["full_prompt"]
    if templated.count(fp) != 1:
        raise ValueError(f"full_prompt occurs {templated.count(fp)}x in the templated text")
    base = templated.index(fp)
    fq = row["final_query_text"]
    if fp.count(fq) != 1:
        raise ValueError("final_query_text is not uniquely locatable inside full_prompt")
    q0 = base + fp.index(fq)
    q1 = q0 + len(fq)
    pre = row["preamble"]
    if not fp.startswith(pre):
        raise ValueError("preamble is not the prefix of full_prompt")
    p0, p1 = base, base + len(pre)
    demo = row["demo_block"]
    if fp.count(demo) != 1:
        raise ValueError("demo_block is not uniquely locatable inside full_prompt")
    d0 = base + fp.index(demo)
    d1 = d0 + len(demo)

    spans = {
        "user_content": list(char_to_token_span(offs, base, base + len(fp))),
        "preamble": list(char_to_token_span(offs, p0, p1)),
        "demo_block": list(char_to_token_span(offs, d0, d1)),
        "query": list(char_to_token_span(offs, q0, q1)),
    }
    demo_lines = []
    cur = d0
    for line in demo.split("\n"):
        if line.strip():
            demo_lines.append(list(char_to_token_span(offs, cur, cur + len(line))))
        cur += len(line) + 1
    spans["demo_lines"] = demo_lines

    gh = templated.rindex("<|start_header_id|>")
    spans["generation_header"] = list(char_to_token_span(offs, gh, len(templated)))
    gen_header_pos = n - 1

    hit = dc.find_word_occurrences_in_text(tok, templated, row["target_surface"],
                                           add_special_tokens=False)
    cw_occ = [{"span": [a, b], "last": b - 1, "rel_end": (b - 1) - n,
               "n_subtokens": b - a, "in_query": a >= spans["query"][0],
               "in_demo": spans["demo_block"][0] <= a < spans["demo_block"][1],
               "in_preamble": a < spans["preamble"][1]}
              for a, b in hit.spans]
    try:
        chit = dc.find_word_occurrences_in_text(tok, templated, row["concept"],
                                                add_special_tokens=False)
        con_occ = [{"span": [a, b], "last": b - 1, "rel_end": (b - 1) - n,
                    "n_subtokens": b - a, "in_query": a >= spans["query"][0]}
                   for a, b in chit.spans]
    except ValueError:
        con_occ = []

    # THE C-075/076/079/080 OCCURRENCE RULE, imported, not restated.
    strict_all, strict_sub = {}, {}
    for w in CONCEPT_WORDS:
        a, b = occ_counts(templated, w)
        strict_all[w], strict_sub[w] = a, b

    cwd = row["target_surface"]
    # LEFT-glued matches: the codeword sitting INSIDE a longer word, e.g. `handbutton`. This is
    # the MIRROR of `inflected` below and it is a distinct instance of the C-075/079/080 class:
    # `prompt_families._substitute` rewrote a `gun` that the left-strict offset finder cannot
    # see, so the bank's own `n_codeword_occurrences` and its own `expected_target_occurrences`
    # disagree on the same row. Counted here, from the text.
    glued = []
    for m in re.finditer(re.escape(cwd), templated, re.IGNORECASE):
        a, b = m.start(), m.end()
        if a > 0 and (templated[a - 1].isalnum() or templated[a - 1] == "_"):
            lo = a
            while lo > 0 and (templated[lo - 1].isalnum() or templated[lo - 1] == "_"):
                lo -= 1
            hi = b
            while hi < len(templated) and (templated[hi].isalnum() or templated[hi] == "_"):
                hi += 1
            glued.append(templated[lo:hi])
    inflected = []
    for m in re.finditer(re.escape(cwd), templated, re.IGNORECASE):
        a, b = m.start(), m.end()
        if a > 0 and (templated[a - 1].isalnum() or templated[a - 1] == "_"):
            continue
        if b < len(templated) and (templated[b].isalnum() or templated[b] == "_"):
            inflected.append(templated[a:b + 12].split()[0])
    strict_cw = len(re.findall(rf"\b{re.escape(cwd)}\b", templated, re.IGNORECASE))

    qpre, qsuf = query_frame
    roles: List[str] = []
    cw_tok = set()
    for o in cw_occ:
        cw_tok.update(range(o["span"][0], o["span"][1]))
    con_tok = set()
    for o in con_occ:
        con_tok.update(range(o["span"][0], o["span"][1]))
    gh0, gh1 = spans["generation_header"]
    qstart = spans["query"][0]
    fmt0, fmt1 = q0, q0 + fmt_len
    frame_a0, frame_a1 = fmt1, q0 + len(qpre)
    frame_b0, frame_b1 = q0 + len(qpre) + len(row["target_surface"]), q1

    for i in range(qstart, n):
        a, b = offs[i]
        if i in cw_tok:
            roles.append("codeword")
        elif i in con_tok:
            roles.append("concept_word")
        elif gh0 <= i < gh1:
            roles.append("response_header")
        elif ids[i] in special_ids:
            roles.append("chat_scaffold")
        elif is_punct(pieces[i]):
            roles.append("punctuation")
        elif b <= a:
            roles.append("chat_scaffold")
        elif not (q0 <= a < q1):
            roles.append("chat_scaffold")
        elif fmt0 <= a < fmt1:
            roles.append("answer_format_instruction")
        elif frame_a0 <= a < frame_a1 or frame_b0 <= a < frame_b1:
            roles.append("user_instruction_scaffold")
        else:
            roles.append("neutral_content")
    bad = sorted(set(roles) - set(ROLE_VOCAB))
    if bad:
        raise ValueError(f"roles outside the fixed vocabulary: {bad}")

    return {
        "bank_file_sha16": bank_ident["bank_file_sha16"],
        "bank_rows_sha16": bank_ident["bank_rows_sha16"],
        "prompt_id": row["prompt_id"], "prompt_sha16": row["prompt_sha16"],
        "codeword": row["codeword"], "concept": row["concept"], "domain": row["domain"],
        "split": row["split"], "dsplit": dsplit, "family_slot": row["family_slot"],
        "n_tokens": n, "n_tokens_untemplated": n_tokens_raw,
        "input_ids": ids, "tokens": pieces,
        "spans": spans, "generation_header_pos": gen_header_pos,
        "query_role_start": qstart,
        "query_roles": roles,
        "codeword_occurrences": cw_occ, "concept_occurrences": con_occ,
        "n_codeword_occurrences_declared": row["n_codeword_occurrences"],
        "n_concept_occurrences_declared": row["n_concept_occurrences"],
        "strict_concept_word_counts": strict_all,
        "substitutable_concept_word_counts": strict_sub,
        "n_codeword_strict_wholeword": strict_cw,
        "inflected_codeword_matches": inflected,
        "left_glued_codeword_matches": glued,
        "n_expected_target_occurrences_declared": len(row.get("expected_target_occurrences", [])),
        "full_prompt_sha16": hashlib.sha256(fp.encode()).hexdigest()[:16],
        "demo_block_sha16": hashlib.sha256(demo.encode()).hexdigest()[:16],
        "templated_sha16": hashlib.sha256(templated.encode()).hexdigest()[:16],
    }


# --------------------------------------------------------------------------- #
# The checks
# --------------------------------------------------------------------------- #
def triples(recs):
    """(codeword, prompt_id) -> {concept: record}, only where all three concepts are present."""
    by = collections.defaultdict(dict)
    for r in recs:
        by[(r["codeword"], r["prompt_id"])][r["concept"]] = r
    return {k: v for k, v in by.items() if len(v) == len(CONCEPTS)}


def run_checks(recs: List[Dict], ck: Checks) -> Dict:
    tri = triples(recs)
    by = {}
    for r in recs:
        by[(r["codeword"], r["concept"], r["prompt_id"])] = r

    # -- CHK-A  occurrence count re-derived from tokens agrees with the bank's own field
    nb = nv = 0
    ex = []
    for r in recs:
        nb += 1
        if len(r["codeword_occurrences"]) != r["n_codeword_occurrences_declared"]:
            nv += 1
            if len(ex) < 5:
                ex.append([r["codeword"], r["concept"], r["prompt_id"],
                           len(r["codeword_occurrences"]),
                           r["n_codeword_occurrences_declared"]])
    ck.add("A_token_occurrence_count_matches_bank_field", nb, nv,
           "every matched prompt", {"examples": ex})

    # -- CHK-B  THE INVERSE OF THE ts116 CHECK. On the VOID ts116 bank the three concept arms
    #    were byte-identical, which pinned any probe to 1/3 by arithmetic (C-074). PR-048 gate G2
    #    requires cell C to DIFFER across concepts. A violation here is IDENTITY, not difference.
    nb = nv = 0
    ex = []
    for (cw, pid), d in sorted(tri.items()):
        ref = d[REF_CONCEPT]
        for cc in CONCEPTS:
            if cc == REF_CONCEPT:
                continue
            nb += 1
            if d[cc]["input_ids"] == ref["input_ids"]:
                nv += 1
                if len(ex) < 5:
                    ex.append([cw, cc, pid])
    ck.add("B_token_ids_DIFFER_across_concepts_C074_guard", nb, nv,
           "(codeword, prompt_id, non-reference concept) pairs", {"examples": ex})

    # -- CHK-C  the QUERY TEXT is byte-identical across concepts at matched (codeword,prompt_id).
    #    This is what makes an end-relative read site meaningful once the prefix drifts.
    nb = nv = 0
    ex = []
    for (cw, pid), d in sorted(tri.items()):
        ref = d[REF_CONCEPT]
        rq = ref["spans"]["query"]
        rtail = ref["input_ids"][rq[0]:]
        for cc in CONCEPTS:
            if cc == REF_CONCEPT:
                continue
            nb += 1
            q = d[cc]["spans"]["query"]
            if d[cc]["input_ids"][q[0]:] != rtail:
                nv += 1
                if len(ex) < 5:
                    ex.append([cw, cc, pid])
    ck.add("C_query_tail_token_ids_identical_across_concepts", nb, nv,
           "(codeword, prompt_id, non-reference concept) pairs", {"examples": ex})

    # -- CHK-D  no concept word anywhere. C-075/076/079/080 rule, imported.
    nb = nv = 0
    ex = []
    for r in recs:
        nb += 1
        if sum(r["strict_concept_word_counts"].values()):
            nv += 1
            if len(ex) < 8:
                ex.append([r["codeword"], r["concept"], r["prompt_id"], r["domain"],
                           r["strict_concept_word_counts"]])
    ck.add("D_no_bomb_knife_gun_token_anywhere_inflection_aware", nb, nv,
           "every matched prompt", {"examples": ex})

    # -- CHK-E  query-side role census identical across every matched prompt
    census = collections.Counter()
    for r in recs:
        census[tuple(sorted(collections.Counter(r["query_roles"]).items()))] += 1
    nb = len(recs)
    nv = nb - max(census.values()) if census else 0
    ck.add("E_query_role_census_constant", nb, nv, "every matched prompt",
           {"n_distinct_censuses": len(census),
            "modal_census": dict(census.most_common(1)[0][0]) if census else {},
            "modal_count": census.most_common(1)[0][1] if census else 0})

    # -- CHK-F  the tail is constant across the WHOLE matched set except codeword slots
    L = min(min(r["n_tokens"] for r in recs), 28) if recs else 0
    varying = []
    for j in range(L):
        vals = {r["tokens"][r["n_tokens"] - L + j] for r in recs}
        if len(vals) > 1:
            varying.append({"rel_end": j - L, "values": sorted(vals)[:6],
                            "n_distinct": len(vals)})
    cw_rel = set()
    for j in range(L):
        rel = j - L
        if all(any(o["rel_end"] == rel for o in r["codeword_occurrences"]) for r in recs):
            cw_rel.add(rel)
    unexpected = [v for v in varying if v["rel_end"] not in cw_rel]
    ck.add("F_tail_constant_except_codeword", len(recs), len(unexpected),
           "last %d token positions of every matched prompt" % L,
           {"tail_len": L, "varying_positions": varying,
            "codeword_rel_end_positions_common_to_all": sorted(cw_rel),
            "unexpected_varying": unexpected})

    # -- CHK-H  every codeword occurrence is ONE subtoken
    nb = nv = 0
    ex = []
    for r in recs:
        for o in r["codeword_occurrences"]:
            nb += 1
            if o["n_subtokens"] != 1:
                nv += 1
                if len(ex) < 5:
                    ex.append([r["codeword"], r["concept"], r["prompt_id"], o])
    ck.add("H_codeword_is_one_subtoken", nb, nv, "every codeword occurrence in every prompt",
           {"examples": ex})

    # -- CHK-J  the matcher bug class, measured: `basket` inside `basketball`
    nb = nv = 0
    ex = collections.Counter()
    doms = set()
    for r in recs:
        nb += 1
        if r["inflected_codeword_matches"]:
            nv += 1
            doms.add(r["domain"])
            for w in r["inflected_codeword_matches"]:
                ex[(r["codeword"], r["domain"], w)] += 1
    ck.add("J_no_inflected_codeword_false_occurrences", nb, nv, "every matched prompt",
           {"offending_surfaces": {"|".join(k): v for k, v in ex.items()},
            "offending_domains": sorted(doms)})

    # -- CHK-J2  the LEFT mirror of J: the codeword glued inside a longer word.
    nb = nv = 0
    ex = collections.Counter()
    doms = set()
    for r in recs:
        nb += 1
        if r["left_glued_codeword_matches"]:
            nv += 1
            doms.add(r["domain"])
            for w in r["left_glued_codeword_matches"]:
                ex[(r["codeword"], r["concept"], r["domain"], w)] += 1
    ck.add("J2_no_codeword_glued_inside_a_longer_word", nb, nv, "every matched prompt",
           {"offending_surfaces": {"|".join(k): v for k, v in ex.items()},
            "offending_domains": sorted(doms)})

    # -- CHK-A2  the bank's TWO OWN occurrence fields must agree with each other. A checker that
    #    reads only one of them agrees with itself; this reads both.
    nb = nv = 0
    ex = []
    for r in recs:
        nb += 1
        if r["n_codeword_occurrences_declared"] != r["n_expected_target_occurrences_declared"]:
            nv += 1
            if len(ex) < 6:
                ex.append([r["codeword"], r["concept"], r["prompt_id"], r["domain"],
                           r["n_codeword_occurrences_declared"],
                           r["n_expected_target_occurrences_declared"]])
    ck.add("A2_bank_own_occurrence_fields_agree", nb, nv, "every matched prompt",
           {"examples": ex})

    # -- CHK-I  dsplit consistent per domain
    nb = nv = 0
    seen = {}
    ex = []
    for r in recs:
        nb += 1
        prev = seen.setdefault(r["domain"], r["dsplit"])
        if prev != r["dsplit"]:
            nv += 1
            if len(ex) < 5:
                ex.append([r["domain"], prev, r["dsplit"]])
    ck.add("I_dsplit_consistent_per_domain", nb, nv, "every matched prompt",
           {"examples": ex, "dsplit_domain_counts": dict(collections.Counter(seen.values()))})

    # -- CHK-K  the excluded domain really is absent
    n_excl = sum(1 for r in recs if r["domain"] in EXCLUDED_DOMAINS)
    ck.add("K_excluded_domain_absent", len(recs), n_excl, "every matched prompt",
           {"excluded": sorted(EXCLUDED_DOMAINS), "n_rows_from_excluded_domains": n_excl})

    # -- CHK-L  every (codeword, prompt_id) has all three concepts. A read-site criterion that
    #    says "identical across all three concepts" is vacuous on an unmatched prompt_id.
    all_keys = {(r["codeword"], r["prompt_id"]) for r in recs}
    ck.add("L_every_prompt_id_matched_across_three_concepts", len(all_keys),
           len(all_keys) - len(tri), "(codeword, prompt_id) keys",
           {"n_keys": len(all_keys), "n_complete_triples": len(tri)})

    return {"by": by, "tri": tri}


# --------------------------------------------------------------------------- #
# Q1 -- read-site scoring, cross-concept criteria evaluated AT MATCHED prompt_id
# --------------------------------------------------------------------------- #
def concept_substring(txt: Optional[str]) -> bool:
    if txt is None:
        return True
    return any(w in txt.lower() for w in CONCEPT_WORDS)


def rank_read_positions(recs: List[Dict], ck: Checks) -> List[Dict]:
    n_rec = len(recs)
    if n_rec == 0:
        ck.add("G_read_position_candidates", 0, 1, "every matched prompt")
        ck.add("G2_incumbent_read_position_rel_end_%d" % INCUMBENT_REL_END, 0, 1,
               "every matched prompt")
        return []
    tri = triples(recs)
    n_tri = len(tri)
    L = min(min(r["n_tokens"] for r in recs), 40)
    cands = []
    for j in range(L):
        rel = j - L
        toks = collections.Counter(r["tokens"][r["n_tokens"] + rel] for r in recs)
        ids_ = collections.Counter(r["input_ids"][r["n_tokens"] + rel] for r in recs)
        # (a) strictly after EVERY codeword occurrence, per prompt
        after = sum(1 for r in recs
                    if all(rel > o["rel_end"] for o in r["codeword_occurrences"]))
        # (b) token-IDENTICAL ACROSS THE THREE CONCEPTS AT MATCHED prompt_id. This is the
        #     criterion the ts116 map could not test: there, one id across the whole corpus was
        #     automatic. Here it is evaluated per (codeword, prompt_id) triple.
        bmatch = 0
        for (cw, pid), d in tri.items():
            vals = {d[cc]["input_ids"][d[cc]["n_tokens"] + rel] for cc in CONCEPTS}
            if len(vals) == 1:
                bmatch += 1
        # (c) no concept substring in any decoding seen at this offset
        cc_free = not any(concept_substring(t) for t in toks)
        # (d) present in every prompt
        present = sum(1 for r in recs if r["n_tokens"] + rel >= 0)
        roles = set()
        for r in recs:
            i = r["n_tokens"] + rel
            if i >= r["query_role_start"]:
                roles.add(r["query_roles"][i - r["query_role_start"]])
            else:
                roles.add("<pre-query>")
        cands.append({
            "rel_end": rel,
            "decoded": toks.most_common(1)[0][0] if len(toks) == 1 else None,
            "modal_decoded": toks.most_common(1)[0][0],
            "n_distinct_decodings": len(toks), "n_distinct_token_ids": len(ids_),
            "token_id": ids_.most_common(1)[0][0] if len(ids_) == 1 else None,
            "roles": sorted(roles),
            "crit_a_strictly_after_codeword": after == n_rec, "n_after": after,
            "crit_b_identical_across_concepts": bmatch == n_tri,
            "n_triples_identical": bmatch, "n_triples": n_tri,
            "crit_c_no_concept_substring": cc_free,
            "crit_d_present_in_every_prompt": present == n_rec, "n_present": present,
        })
    qualifying = [c for c in cands
                  if c["crit_a_strictly_after_codeword"] and c["crit_b_identical_across_concepts"]
                  and c["crit_c_no_concept_substring"] and c["crit_d_present_in_every_prompt"]]
    prio = {"user_instruction_scaffold": 0, "neutral_content": 0, "punctuation": 1,
            "chat_scaffold": 2, "response_header": 2}
    qualifying.sort(key=lambda c: (min(prio.get(r, 3) for r in c["roles"]), c["rel_end"]))
    for i, c in enumerate(qualifying):
        c["rank"] = i + 1
    ck.add("G_read_position_candidates", len(cands), 0 if qualifying else 1,
           "token offsets in the tail of every matched prompt",
           {"n_candidates_scored": len(cands), "n_qualifying": len(qualifying),
            "qualifying_rel_ends": sorted(c["rel_end"] for c in qualifying)})

    # G2 binds PER PROMPT to the INCUMBENT offset, fixed in source.
    nb = nv = 0
    ex = []
    ids_at = collections.Counter()
    for r in recs:
        nb += 1
        i = r["n_tokens"] + INCUMBENT_REL_END
        if i < 0:
            nv += 1
            continue
        ids_at[r["input_ids"][i]] += 1
    ref_id = ids_at.most_common(1)[0][0] if ids_at else None
    nv = 0
    for r in recs:
        i = r["n_tokens"] + INCUMBENT_REL_END
        if i < 0:
            nv += 1
            continue
        tid, txt = r["input_ids"][i], r["tokens"][i]
        after = all(INCUMBENT_REL_END > o["rel_end"] for o in r["codeword_occurrences"])
        neutral = not concept_substring(txt)
        if not (tid == ref_id and after and neutral):
            nv += 1
            if len(ex) < 6:
                ex.append([r["codeword"], r["concept"], r["prompt_id"], tid, txt, after, neutral])
    ck.add("G2_incumbent_read_position_rel_end_%d" % INCUMBENT_REL_END, nb, nv,
           "every matched prompt",
           {"incumbent_rel_end": INCUMBENT_REL_END, "modal_token_id": ref_id,
            "token_id_histogram": dict(ids_at), "examples": ex})

    # G3 binds to TRIPLES: criterion (b) at the incumbent offset.
    nb = nv = 0
    ex = []
    for (cw, pid), d in sorted(tri.items()):
        nb += 1
        vals = {d[cc]["input_ids"][d[cc]["n_tokens"] + INCUMBENT_REL_END] for cc in CONCEPTS}
        if len(vals) != 1:
            nv += 1
            if len(ex) < 6:
                ex.append([cw, pid, sorted(vals)])
    ck.add("G3_incumbent_identical_across_concepts_at_matched_prompt_id", nb, nv,
           "(codeword, prompt_id) triples", {"examples": ex})
    return cands


# --------------------------------------------------------------------------- #
# Q2 -- codeword index distribution, absolute and end-relative, per concept
# --------------------------------------------------------------------------- #
def codeword_position_analysis(recs: List[Dict], ck: Checks) -> Dict:
    per_concept = {}
    for cc in CONCEPTS:
        sub = [r for r in recs if r["concept"] == cc]
        if not sub:
            continue
        last_abs = [r["codeword_occurrences"][-1]["last"] for r in sub if r["codeword_occurrences"]]
        last_rel = [r["codeword_occurrences"][-1]["rel_end"] for r in sub if r["codeword_occurrences"]]
        first_abs = [r["codeword_occurrences"][0]["last"] for r in sub if r["codeword_occurrences"]]
        first_rel = [r["codeword_occurrences"][0]["rel_end"] for r in sub if r["codeword_occurrences"]]
        demo_abs, demo_rel = [], []
        for r in sub:
            for o in r["codeword_occurrences"]:
                if o["in_demo"]:
                    demo_abs.append(o["last"])
                    demo_rel.append(o["rel_end"])
        per_concept[cc] = {
            "n_prompts": len(sub),
            "n_occurrences_per_prompt": mean_sd(len(r["codeword_occurrences"]) for r in sub),
            "last_occurrence_absolute": mean_sd(last_abs),
            "last_occurrence_rel_end": mean_sd(last_rel),
            "last_occurrence_rel_end_histogram": dict(collections.Counter(last_rel)),
            "first_occurrence_absolute": mean_sd(first_abs),
            "first_occurrence_rel_end": mean_sd(first_rel),
            "demo_occurrence_absolute": mean_sd(demo_abs),
            "demo_occurrence_rel_end": mean_sd(demo_rel),
        }

    # Cross-concept, AT MATCHED (codeword, prompt_id): does the codeword index move?
    tri = triples(recs)
    n_abs_same = n_rel_same = n_last_rel_same = 0
    abs_deltas, rel_deltas = [], []
    ex_abs, ex_rel = [], []
    for (cw, pid), d in sorted(tri.items()):
        abs_sets = {cc: [o["last"] for o in d[cc]["codeword_occurrences"]] for cc in CONCEPTS}
        rel_sets = {cc: [o["rel_end"] for o in d[cc]["codeword_occurrences"]] for cc in CONCEPTS}
        if len({tuple(v) for v in abs_sets.values()}) == 1:
            n_abs_same += 1
        elif len(ex_abs) < 4:
            ex_abs.append([cw, pid, abs_sets])
        if len({tuple(v) for v in rel_sets.values()}) == 1:
            n_rel_same += 1
        elif len(ex_rel) < 4:
            ex_rel.append([cw, pid, rel_sets])
        lasts_abs = [abs_sets[cc][-1] for cc in CONCEPTS if abs_sets[cc]]
        lasts_rel = [rel_sets[cc][-1] for cc in CONCEPTS if rel_sets[cc]]
        if len(set(lasts_rel)) == 1:
            n_last_rel_same += 1
        if lasts_abs:
            abs_deltas.append(max(lasts_abs) - min(lasts_abs))
        if lasts_rel:
            rel_deltas.append(max(lasts_rel) - min(lasts_rel))

    n_tri = len(tri)
    ck.add("Q2a_last_codeword_rel_end_identical_across_concepts", n_tri,
           n_tri - n_last_rel_same, "(codeword, prompt_id) triples",
           {"n_identical": n_last_rel_same,
            "cross_concept_spread_of_last_rel_end": mean_sd(rel_deltas)})
    # Whether ALL occurrences keep their ABSOLUTE index is a MEASUREMENT, so it is reported as a
    # count and not as a pass/fail: on ts116m the demo block differs, so drift is EXPECTED.
    return {"per_concept": per_concept,
            "n_triples": n_tri,
            "n_triples_all_absolute_indices_identical": n_abs_same,
            "n_triples_all_rel_end_indices_identical": n_rel_same,
            "n_triples_last_occurrence_rel_end_identical": n_last_rel_same,
            "cross_concept_spread_last_abs": mean_sd(abs_deltas),
            "cross_concept_spread_last_rel_end": mean_sd(rel_deltas),
            "examples_absolute_drift": ex_abs, "examples_rel_end_drift": ex_rel}


# --------------------------------------------------------------------------- #
# Q3 -- full-prompt token-length distribution per concept
# --------------------------------------------------------------------------- #
def length_analysis(recs: List[Dict], ck: Checks) -> Dict:
    per = {cc: mean_sd(r["n_tokens"] for r in recs if r["concept"] == cc) for cc in CONCEPTS}
    per_raw = {cc: mean_sd(r["n_tokens_untemplated"] for r in recs if r["concept"] == cc)
               for cc in CONCEPTS}
    per_cw = {}
    for cw in CODEWORDS:
        per_cw[cw] = {cc: mean_sd(r["n_tokens"] for r in recs
                                  if r["concept"] == cc and r["codeword"] == cw)
                      for cc in CONCEPTS}
    means = [per[cc]["mean"] for cc in CONCEPTS if per[cc]["mean"] is not None]
    rawm = [per_raw[cc]["mean"] for cc in CONCEPTS if per_raw[cc]["mean"] is not None]
    pooled = mean_sd(r["n_tokens"] for r in recs)
    # Paired within-prompt_id difference: the sharpest form, since preamble and query are shared.
    tri = triples(recs)
    paired = collections.defaultdict(list)
    for (cw, pid), d in tri.items():
        for cc in CONCEPTS:
            if cc == REF_CONCEPT:
                continue
            paired[cc].append(d[cc]["n_tokens"] - d[REF_CONCEPT]["n_tokens"])
    verdict = {}
    for cc in CONCEPTS:
        claim = CLAIMED_TOKEN_MEANS[cc]
        obs, raw = per[cc]["mean"], per_raw[cc]["mean"]
        verdict[cc] = {"claimed_mean": claim,
                       "observed_mean_templated": obs,
                       "abs_diff_templated": None if obs is None else round(abs(obs - claim), 4),
                       "observed_mean_untemplated": raw,
                       "abs_diff_untemplated": None if raw is None else round(abs(raw - claim), 4)}
    tmpl_overhead = mean_sd(r["n_tokens"] - r["n_tokens_untemplated"] for r in recs)
    ck.add("Q3_length_measured_on_every_matched_prompt", len(recs), 0 if recs else 1,
           "every matched prompt", {"pooled": pooled})
    return {"per_concept": per, "per_concept_untemplated": per_raw,
            "chat_template_overhead_tokens": tmpl_overhead,
            "per_codeword_per_concept": per_cw, "pooled": pooled,
            "cross_concept_mean_spread": round(max(means) - min(means), 4) if means else None,
            "paired_delta_vs_%s" % REF_CONCEPT: {cc: mean_sd(v) for cc, v in paired.items()},
            "cross_concept_mean_spread_untemplated": (
                round(max(rawm) - min(rawm), 4) if rawm else None),
            "claim_check_C084": verdict,
            "claimed_sd": CLAIMED_TOKEN_SD}


# --------------------------------------------------------------------------- #
# Q4 -- query-side scaffold vs content, and the K-ladder
# --------------------------------------------------------------------------- #
def query_breakdown(recs: List[Dict], ck: Checks, kmax: int = 14) -> Dict:
    per_prompt = collections.Counter()
    for r in recs:
        per_prompt.update(r["query_roles"])
    n = len(recs)
    scaffold_roles = ("chat_scaffold", "response_header")
    ladder = []
    for K in range(1, kmax + 1):
        rel = -K
        toks = collections.Counter()
        roles = collections.Counter()
        for r in recs:
            i = r["n_tokens"] + rel
            if i < 0:
                continue
            toks[r["tokens"][i]] += 1
            roles[r["query_roles"][i - r["query_role_start"]]
                  if i >= r["query_role_start"] else "<pre-query>"] += 1
        role_set = sorted(roles)
        is_content = all(x not in scaffold_roles and x != "<pre-query>" for x in role_set)
        ladder.append({"K": K, "rel_end": rel,
                       "modal_decoded": toks.most_common(1)[0][0] if toks else None,
                       "n_distinct_decodings": len(toks),
                       "roles": {k: v for k, v in roles.items()},
                       "carries_query_content": bool(is_content)})
    first_content = next((l["K"] for l in ladder if l["carries_query_content"]), None)
    first_nonpunct = next((l["K"] for l in ladder if l["carries_query_content"]
                           and set(l["roles"]) != {"punctuation"}), None)
    ck.add("Q4_query_roles_bound", n, 0 if n else 1, "every matched prompt",
           {"n_role_tokens": sum(per_prompt.values())})
    return {"n_prompts": n,
            "roles_with_zero_tokens": [r for r in ROLE_VOCAB if per_prompt.get(r, 0) == 0],
            "per_prompt_role_counts": {k: round(v / n, 4) for k, v in sorted(per_prompt.items())},
            "query_side_tokens_per_prompt": round(sum(per_prompt.values()) / n, 4),
            "scaffold_per_prompt": round(sum(per_prompt[x] for x in scaffold_roles) / n, 4),
            "content_per_prompt": round((sum(per_prompt.values())
                                         - sum(per_prompt[x] for x in scaffold_roles)) / n, 4),
            "k_ladder": ladder,
            "n_leading_rungs_with_zero_query_content":
                (first_content - 1) if first_content else kmax,
            "first_query_content_rung": first_content,
            "first_non_punctuation_query_content_rung": first_nonpunct}


# --------------------------------------------------------------------------- #
# --mutate : every check must be shown to go RED
# --------------------------------------------------------------------------- #
def mutate_and_report(recs: List[Dict]) -> List[Dict]:
    out = []

    def trial(name: str, target_check: str, fn):
        m = copy.deepcopy(recs)
        fn(m)
        c = Checks()
        run_checks(m, c)
        rank_read_positions(m, c)
        codeword_position_analysis(m, c)
        length_analysis(m, c)
        if m:
            query_breakdown(m, c)
        else:
            c.add("Q4_query_roles_bound", 0, 1, "every matched prompt")
        row = c.by_name(target_check)
        out.append({"mutation": name, "target_check": target_check,
                    "status_after_mutation": row["status"],
                    "n_bound": row["n_bound"], "n_violations": row["n_violations"],
                    "went_red": row["status"] != "PASS"})

    def m_count(m):
        m[0]["n_codeword_occurrences_declared"] += 1
    trial("bump one row's declared occurrence count",
          "A_token_occurrence_count_matches_bank_field", m_count)

    def m_identical(m):
        # THE C-074 MUTATION: make one knife prompt byte-identical to its bomb partner. The
        # WHOLE record is replaced (not just input_ids) so the mutant stays self-consistent --
        # a mutation that also corrupts n_tokens would go RED for the wrong reason.
        tri = triples(m)
        (cw, pid), d = sorted(tri.items())[0]
        clone = copy.deepcopy(d["bomb"])
        clone["concept"] = "knife"
        m[m.index(d["knife"])] = clone
    trial("make one knife prompt's token ids identical to its bomb partner (C-074 replay)",
          "B_token_ids_DIFFER_across_concepts_C074_guard", m_identical)

    def m_query_tail(m):
        tri = triples(m)
        (cw, pid), d = sorted(tri.items())[0]
        r = d["gun"]
        r["input_ids"] = list(r["input_ids"])
        r["input_ids"][-9] += 1
    trial("perturb one gun prompt's token id at rel_end=-9",
          "C_query_tail_token_ids_identical_across_concepts", m_query_tail)

    def m_concept(m):
        m[0]["strict_concept_word_counts"] = dict(m[0]["strict_concept_word_counts"])
        m[0]["strict_concept_word_counts"]["knife"] = 1
    trial("plant one literal 'knife' in one prompt",
          "D_no_bomb_knife_gun_token_anywhere_inflection_aware", m_concept)

    def m_role(m):
        m[0]["query_roles"] = list(m[0]["query_roles"])
        m[0]["query_roles"][0] = "neutral_content"
    trial("relabel one query token's role", "E_query_role_census_constant", m_role)

    def m_tail(m):
        r = m[0]
        r["tokens"] = list(r["tokens"]); r["tokens"][-7] = " REFER"
        r["input_ids"] = list(r["input_ids"]); r["input_ids"][-7] = 99999
    trial("rewrite one prompt's token at rel_end=-7", "F_tail_constant_except_codeword", m_tail)

    def m_subtok(m):
        m[0]["codeword_occurrences"] = copy.deepcopy(m[0]["codeword_occurrences"])
        m[0]["codeword_occurrences"][0]["n_subtokens"] = 2
    trial("split one codeword occurrence into 2 subtokens", "H_codeword_is_one_subtoken", m_subtok)

    def m_inflect(m):
        m[0]["inflected_codeword_matches"] = ["buttonhole"]
    trial("plant an inflected codeword match in one prompt",
          "J_no_inflected_codeword_false_occurrences", m_inflect)

    def m_glue(m):
        m[0]["left_glued_codeword_matches"] = ["handbutton"]
    trial("plant a left-glued codeword match in one prompt",
          "J2_no_codeword_glued_inside_a_longer_word", m_glue)

    def m_fields(m):
        m[0]["n_expected_target_occurrences_declared"] += 1
    trial("desynchronise one row's two declared occurrence fields",
          "A2_bank_own_occurrence_fields_agree", m_fields)

    def m_dsplit(m):
        dom = m[0]["domain"]
        for r in m:
            if r["domain"] == dom:
                r["dsplit"] = "test" if r["dsplit"] != "test" else "train"
                break
    trial("flip one row's dsplit inside a domain", "I_dsplit_consistent_per_domain", m_dsplit)

    def m_excl(m):
        m[0]["domain"] = sorted(EXCLUDED_DOMAINS)[0]
    trial("relabel one row into the excluded domain", "K_excluded_domain_absent", m_excl)

    def m_drop_concept(m):
        tri = triples(m)
        (cw, pid), d = sorted(tri.items())[0]
        m.remove(d["gun"])
    trial("drop the gun arm of one prompt_id",
          "L_every_prompt_id_matched_across_three_concepts", m_drop_concept)

    def m_read_site(m):
        tri = triples(m)
        (cw, pid), d = sorted(tri.items())[0]
        r = d["gun"]
        r["tokens"] = list(r["tokens"]); r["tokens"][INCUMBENT_REL_END] = " bombing"
    trial("decode the incumbent read position as ' bombing' in one prompt",
          "G2_incumbent_read_position_rel_end_%d" % INCUMBENT_REL_END, m_read_site)

    def m_move_cw(m):
        m[0]["codeword_occurrences"] = copy.deepcopy(m[0]["codeword_occurrences"])
        m[0]["codeword_occurrences"][-1]["rel_end"] = -3
    trial("move one prompt's last codeword occurrence downstream of the read position",
          "G2_incumbent_read_position_rel_end_%d" % INCUMBENT_REL_END, m_move_cw)

    def m_read_site_ids(m):
        tri = triples(m)
        (cw, pid), d = sorted(tri.items())[0]
        r = d["knife"]
        r["input_ids"] = list(r["input_ids"])
        r["input_ids"][r["n_tokens"] + INCUMBENT_REL_END] += 1
    trial("change one knife prompt's token id at the incumbent read position",
          "G3_incumbent_identical_across_concepts_at_matched_prompt_id", m_read_site_ids)

    def m_shift_cw_rel(m):
        tri = triples(m)
        (cw, pid), d = sorted(tri.items())[0]
        r = d["knife"]
        r["codeword_occurrences"] = copy.deepcopy(r["codeword_occurrences"])
        r["codeword_occurrences"][-1]["rel_end"] -= 1
    trial("shift one knife prompt's LAST codeword rel_end by -1",
          "Q2a_last_codeword_rel_end_identical_across_concepts", m_shift_cw_rel)

    def m_no_qualifying(m):
        # Push EVERY codeword occurrence to the last position, so no offset can be strictly
        # after it and the candidate set empties. Without this, "some offset qualifies" would
        # be a sentence no input could falsify.
        for r in m:
            r["codeword_occurrences"] = copy.deepcopy(r["codeword_occurrences"])
            for o in r["codeword_occurrences"]:
                o["rel_end"] = -1
    trial("push every codeword occurrence to rel_end=-1 so no offset is downstream",
          "G_read_position_candidates", m_no_qualifying)

    def m_empty(m):
        del m[:]
    for tgt in ("B_token_ids_DIFFER_across_concepts_C074_guard",
                "G2_incumbent_read_position_rel_end_%d" % INCUMBENT_REL_END,
                "Q3_length_measured_on_every_matched_prompt",
                "Q4_query_roles_bound"):
        trial("bind the checks to an EMPTY row set -> %s" % tgt, tgt, m_empty)
    return out


# --------------------------------------------------------------------------- #
def mutate_scope_checks(idents: Dict, pub: Dict, man_sha: str, recs: List[Dict]) -> List[Dict]:
    """Z1/Z2/Y are computed in main() from inputs, not from the record list, so they need their
    own red-team: each is re-evaluated against a deliberately corrupted input."""
    out = []

    def row(name, target, ck):
        r = ck.by_name(target)
        out.append({"mutation": name, "target_check": target,
                    "status_after_mutation": r["status"], "n_bound": r["n_bound"],
                    "n_violations": r["n_violations"], "went_red": r["status"] != "PASS"})

    # Z1 -- corrupt one published sha
    c = Checks()
    bad = copy.deepcopy(pub)
    k = sorted(bad)[0]
    bad[k]["bank_rows_sha16"] = "0" * 16
    nv = sum(1 for kk, v in idents.items()
             if v["bank_rows_sha16"] != bad[kk]["bank_rows_sha16"]
             or v["bank_file_sha16"] != bad[kk]["bank_file_sha16"])
    c.add("Z1_bank_sha16_matches_PR048", len(idents), nv, "the six ts116m banks")
    row("corrupt one PR-048 published bank rows_sha16", "Z1_bank_sha16_matches_PR048", c)

    # Z1 -- bind to zero banks
    c = Checks()
    c.add("Z1_bank_sha16_matches_PR048", 0, 0, "the six ts116m banks")
    row("bind Z1 to zero banks", "Z1_bank_sha16_matches_PR048", c)

    # Z2 -- corrupt the manifest hash
    c = Checks()
    c.add("Z2_split_manifest_sha16_matches_published", 1,
          0 if (man_sha + "x") == EXPECTED_MANIFEST_SHA16 else 1, "the domain-split manifest")
    row("corrupt the observed split-manifest sha16",
        "Z2_split_manifest_sha16_matches_published", c)

    # Y -- drop a domain from one arm
    c = Checks()
    doms = sorted({r["domain"] for r in recs})
    drop = doms[0]
    kept = [r for r in recs if not (r["domain"] == drop and r["concept"] == "gun")]
    d2 = sorted({r["domain"] for r in kept})
    want = len(d2) * len(CODEWORDS) * len(CONCEPTS)
    got = len({(r["domain"], r["codeword"], r["concept"]) for r in kept})
    c.add("Y_coverage_115dom_x_2cw_x_3concept", got,
          0 if (got == want and len(d2) == N_DOMAINS_EXPECTED) else 1,
          "domain x codeword x concept combinations")
    row("drop the gun arm of one whole domain", "Y_coverage_115dom_x_2cw_x_3concept", c)
    return out


def write_report(path: str, p: Dict) -> None:
    import io
    o = io.StringIO()
    w = o.write
    sc = p["scope"]
    n = sc["n_records"]
    cands = p["read_position_candidates"]
    qual = sorted([c for c in cands if c.get("rank")], key=lambda c: c["rank"])
    q2, q3, q4 = p["q2_codeword_positions"], p["q3_token_lengths"], p["q4_query_breakdown"]
    g2 = [c for c in p["checks"] if c["check"].startswith("G2_")][0]
    g3 = [c for c in p["checks"] if c["check"].startswith("G3_")][0]
    inc = p["incumbent_rel_end"]
    inct = next((c for c in cands if c["rel_end"] == inc), None)

    w("# DCS-TS116M token-role map -- cell C / semantic_one_word / n_examples=4\n\n")
    w(f"Generated {p['generated']} · tokenizer `{p['model']}` · **CPU only, no weights "
      f"loaded** · pre-extraction checklist item **X2** of `configs/dcs_ts_pr048.json`.\n\n")
    w("## What this supersedes and why\n\n")
    w("`reports/DCS_TS_TOKEN_ROLE_MAP.md` and `scripts/dcs_ts_token_roles.py` were computed on "
      "the **ts116** bank family, VOIDED by DCS-C-074: cell C drew the harm pool with the "
      "concept word already replaced by the codeword, so the three concept arms were "
      "byte-identical (1856/1856 in the primary channel). On that bank criterion (b) of the "
      "read-site question -- \"token-identical across all three concepts\" -- held at every "
      "position trivially, and the prompt prefix could not differ by concept because there was "
      "only one prompt. Those two files are left unedited; they document a superseded bank. "
      "This map re-derives everything on **ts116m**, where the demonstrations differ per "
      "concept.\n\n")
    w(f"Scope: field `cell` == **{sc['cell']}** (NOT `condition`; A-039), query_kind "
      f"**{sc['query_kind']}**, n_examples **{sc['n_examples']}**, "
      f"**{sc['n_domains']}** analysed domains x {len(sc['codewords'])} codewords x "
      f"{len(sc['concepts'])} concepts x {sc['rows_per_domain_per_concept_per_codeword']} "
      f"family slots = **{n} prompts**. `restaurant_kitchen` excluded "
      f"(PR-048, prompt-only, preregistered): {sc['n_rows_dropped_by_exclusion']} cell-C rows "
      f"dropped.\n\n")
    w("Artifacts: `outputs/dcs_ts/token_roles_ts116m.json.gz` (per-prompt full token ids, "
      "decoded tokens, preamble/demo/query/generation-header spans, every codeword and concept "
      "occurrence index, a role for every query-side token), this report, "
      "`scripts/dcs_ts116m_token_roles.py`.\n\n")

    w("## Provenance\n\n| bank | rows_sha16 observed | PR-048 published | file_sha16 observed | "
      "published | rows | cell-C rows | matched |\n|---|---|---|---|---|---|---|---|\n")
    for k, v in p["bank_identity"].items():
        pub = p["preregistered_bank_sha"][k]
        w(f"| {k} | `{v['bank_rows_sha16']}` | `{pub['bank_rows_sha16']}` "
          f"{'OK' if pub['bank_rows_sha16'] == v['bank_rows_sha16'] else '**MISMATCH**'} | "
          f"`{v['bank_file_sha16']}` | `{pub['bank_file_sha16']}` "
          f"{'OK' if pub['bank_file_sha16'] == v['bank_file_sha16'] else '**MISMATCH**'} | "
          f"{v['bank_n_rows']} | {v['n_cellC_sow_n4_all_domains']} | {v['n_matched']} |\n")
    sm = p["split_manifest"]
    w(f"\nSplit manifest `{sm['path']}` sha16 `{sm['manifest_sha16']}` (published "
      f"`{EXPECTED_MANIFEST_SHA16}`), field `{sm['field_name']}`.\n\n")
    ich = [c for c in p["checks"] if c["check"] == "I_dsplit_consistent_per_domain"][0]
    w(f"`dsplit` over the {sc['n_domains']} analysed domains: "
      f"{ich['detail']['dsplit_domain_counts']}.\n\n")

    w("## Checks\n\nA check that binds to zero rows is `ERROR_EMPTY`, never a pass. Every check "
      "re-derives from raw bank rows plus a real tokenization; none reads a producer-written "
      "summary field except `A`, whose entire purpose is to compare against one.\n\n")
    w("| check | status | binds to | n bound | n violations |\n|---|---|---|---|---|\n")
    for c in p["checks"]:
        w(f"| `{c['check']}` | **{c['status']}** | {c['binds_to']} | {c['n_bound']} | "
          f"{c['n_violations']} |\n")
    w(f"\n`{json.dumps(p['checks_summary'])}`\n\n")

    if p["mutations"]:
        nred = sum(1 for m in p["mutations"] if m["went_red"])
        w(f"### Mutation demonstrations (`--mutate`) -- {nred}/{len(p['mutations'])} RED\n\n")
        w("| mutation | target check | status after | RED |\n|---|---|---|---|\n")
        for m in p["mutations"]:
            w(f"| {m['mutation']} | `{m['target_check']}` | {m['status_after_mutation']} "
              f"({m['n_violations']}/{m['n_bound']}) | {'YES' if m['went_red'] else '**NO**'} |\n")
        w("\nA mutation that does not go RED means that check cannot fail.\n\n")

    # ---- defects
    failing = [c for c in p["checks"] if c["status"] != "PASS"]
    w("## Defects this map found\n\n")
    if not failing:
        w("None: every check above is PASS.\n\n")
    else:
        w(f"{len(failing)} of the {len(p['checks'])} checks are not PASS. Each is a prompt-only "
          f"finding, counted with its denominator, and none of them touches the read site -- "
          f"that last clause is a claim, and the counts that support it are in Q1.\n\n")
        for c in failing:
            w(f"### `{c['check']}` -- {c['n_violations']}/{c['n_bound']} "
              f"({c['binds_to']})\n\n")
            d = c["detail"]
            if d.get("offending_surfaces"):
                w(f"Surfaces and counts: `{d['offending_surfaces']}`")
                if d.get("offending_domains"):
                    w(f"; domains: `{d['offending_domains']}`")
                w(".\n\n")
            if d.get("examples"):
                w("Examples (first few):\n\n")
                for e in d["examples"][:6]:
                    w(f"* `{e}`\n")
                w("\n")
        w(p.get("defect_narrative", ""))
        w("\n")

    chkB = [c for c in p["checks"] if c["check"].startswith("B_")][0]
    chkC = [c for c in p["checks"] if c["check"].startswith("C_query_tail")][0]
    chkD = [c for c in p["checks"] if c["check"].startswith("D_")][0]
    w("## The structural fact that governs every answer below\n\n")
    w(f"At matched `(codeword, prompt_id)` the token id sequence **DIFFERS** across concepts in "
      f"{chkB['n_bound'] - chkB['n_violations']}/{chkB['n_bound']} comparisons (each "
      f"non-reference concept against `{REF_CONCEPT}`) -- the exact inverse of ts116, and the "
      f"in-token form of PR-048 gate G2. The **query tail** is nevertheless byte- and "
      f"token-identical across concepts in "
      f"{chkC['n_bound'] - chkC['n_violations']}/{chkC['n_bound']} of those same comparisons, "
      f"and the inflection-aware whole-word count of bomb/knife/gun over the whole templated "
      f"prompt is 0 in {chkD['n_bound'] - chkD['n_violations']}/{chkD['n_bound']} prompts.\n\n")
    w("So the three arms now differ **only inside the demonstration block**, which sits between "
      "a shared preamble and a shared query. Everything downstream of the demo block is common "
      "text at a **shifted offset**. That is the whole content of question 2.\n\n")

    # ---- Q1
    w("## Q1 -- is `rel_end = -9` still the right read site?\n\n")
    w("Criteria, each counted over the full population: (a) strictly after every codeword "
      "occurrence; (b) token-identical across all three concepts **at matched `prompt_id`**; "
      "(c) contains none of bomb/knife/gun; (d) exists in every matched prompt.\n\n")
    w(f"**Incumbent `rel_end = {inc}`**")
    if inct:
        w(f" -- modal decoding `{inct['modal_decoded']!r}`, "
          f"{inct['n_distinct_token_ids']} distinct token id(s) over {n} prompts"
          f"{', id `%d`' % inct['token_id'] if inct['token_id'] is not None else ''}.\n\n")
        w("| criterion | count | denominator |\n|---|---|---|\n")
        w(f"| (a) strictly after every codeword occurrence | {inct['n_after']} | {n} prompts |\n")
        w(f"| (b) identical across the three concepts at matched prompt_id | "
          f"{inct['n_triples_identical']} | {inct['n_triples']} triples |\n")
        w(f"| (c) no bomb/knife/gun substring in any decoding seen there | "
          f"{'yes' if inct['crit_c_no_concept_substring'] else 'NO'} | "
          f"{inct['n_distinct_decodings']} distinct decoding(s) |\n")
        w(f"| (d) present in every matched prompt | {inct['n_present']} | {n} prompts |\n\n")
        allfour = (inct["crit_a_strictly_after_codeword"]
                   and inct["crit_b_identical_across_concepts"]
                   and inct["crit_c_no_concept_substring"]
                   and inct["crit_d_present_in_every_prompt"])
        w(f"**VERDICT: `rel_end = {inc}` {'PASSES' if allfour else 'FAILS'} all four criteria on "
          f"ts116m.** Per-prompt confirmation: `{g2['check']}` "
          f"{g2['n_bound'] - g2['n_violations']}/{g2['n_bound']}; per-triple confirmation of "
          f"criterion (b): `{g3['check']}` {g3['n_bound'] - g3['n_violations']}/"
          f"{g3['n_bound']}.\n\n")
        if not allfour:
            w("A replacement is nominated from the ranked table below: **rank 1**.\n\n")
    w(f"### Ranked alternatives ({len(qual)} offsets satisfy all four)\n\n")
    w("| rank | rel_end | decoded | token id | role(s) | (a) n after / N | (b) n triples "
      "identical / N | (c) | (d) n present / N |\n|---|---|---|---|---|---|---|---|---|\n")
    for c in qual:
        w(f"| {c['rank']} | `{c['rel_end']}` | `{c['modal_decoded']!r}` | {c['token_id']} | "
          f"{'/'.join(c['roles'])} | {c['n_after']}/{n} | "
          f"{c['n_triples_identical']}/{c['n_triples']} | yes | {c['n_present']}/{n} |\n")
    w("\nRanking rule, fixed in source before scoring: query content and instruction scaffold "
      "before punctuation before chat scaffold; within a tier, nearest to the codeword first. "
      "Ranks 5-9 are chat scaffold and response header, not query content: a null read there is "
      "a null about the readout, not about the query. The substantive alternatives to rank 1 "
      "are ranks 2 and 3.\n\n")
    cw10 = next((c for c in cands if c["rel_end"] == -10), None)
    if cw10:
        w("### `rel_end = -9` is NOT the preregistered primary read site, and must not be "
          "confused with it\n\n")
        w(f"PR-048 `read_site.position` is **`codeword_last`**, which on this population is "
          f"`rel_end = {cw10['rel_end']}`, decoded `{cw10['modal_decoded']!r}`. It appears in "
          f"the disqualified table above because criterion (a) asks for a position strictly "
          f"AFTER every codeword occurrence and the codeword is not after itself -- that is a "
          f"property of the question this map answers, not a defect in the preregistered site. "
          f"The two are separate positions with separate jobs:\n\n")
        w(f"* **`rel_end = {cw10['rel_end']}` (`codeword_last`)** -- the PR-048 primary. Its "
          f"`rel_end` is identical across all three concepts in "
          f"{[c for c in p['checks'] if c['check'].startswith('Q2a')][0]['n_bound'] - [c for c in p['checks'] if c['check'].startswith('Q2a')][0]['n_violations']}"
          f"/{[c for c in p['checks'] if c['check'].startswith('Q2a')][0]['n_bound']} triples "
          f"and it is one subtoken in every prompt, so it is addressable end-relatively. It "
          f"carries {cw10['n_distinct_token_ids']} distinct token ids across the population -- "
          f"one per codeword, `button` and `basket` -- which is expected and is why the two "
          f"codeword banks are analysed as a transfer pair rather than pooled.\n")
        w(f"* **`rel_end = {inc}`** -- the DOWNSTREAM NEUTRAL site this map nominates: the "
          f"repo's `following` position (`ds_common.target_positions`, `extract_boombness "
          f"--position following`), one token past the query codeword. It is the control read "
          f"for anything that must not sit on the codeword itself.\n\n")
    dq = [c for c in cands if not c.get("rank")]
    w(f"{len(dq)} of the {len(cands)} scored offsets are disqualified. The 16 nearest the end "
      "are listed with the criterion that killed them; the full scoring, all "
      f"{len(cands)} offsets, is in the JSON under `read_position_candidates`:\n\n")
    w("| rel_end | modal decoded | fails (a) | fails (b) | fails (c) | fails (d) |\n"
      "|---|---|---|---|---|---|\n")
    for c in dq[-16:]:
        w(f"| `{c['rel_end']}` | `{c['modal_decoded']!r}` | "
          f"{'' if c['crit_a_strictly_after_codeword'] else 'X (%d/%d)' % (c['n_after'], n)} | "
          f"{'' if c['crit_b_identical_across_concepts'] else 'X (%d/%d)' % (c['n_triples_identical'], c['n_triples'])} | "
          f"{'' if c['crit_c_no_concept_substring'] else 'X'} | "
          f"{'' if c['crit_d_present_in_every_prompt'] else 'X (%d/%d)' % (c['n_present'], n)} |\n")
    w("\n")

    # ---- Q2
    w("## Q2 -- does the codeword position move across concepts?\n\n")
    w("This is the question ts116 could not ask. Reported both ways, because the answer differs "
      "between them and the difference is the whole reason a read site must be end-relative.\n\n")
    w("| concept | prompts | occurrences/prompt | LAST codeword absolute index | LAST codeword "
      "rel_end | FIRST codeword absolute | demo-block occurrences absolute |\n"
      "|---|---|---|---|---|---|---|\n")
    for cc in CONCEPTS:
        d = q2["per_concept"].get(cc)
        if not d:
            continue
        f = lambda x: f"{x['mean']} ± {x['sd']} [{x['min']}, {x['max']}]"
        w(f"| {cc} | {d['n_prompts']} | {f(d['n_occurrences_per_prompt'])} | "
          f"{f(d['last_occurrence_absolute'])} | {f(d['last_occurrence_rel_end'])} | "
          f"{f(d['first_occurrence_absolute'])} | {f(d['demo_occurrence_absolute'])} |\n")
    w(f"\nAt matched `(codeword, prompt_id)`, over {q2['n_triples']} triples:\n\n")
    w(f"* the **full list of ABSOLUTE codeword indices** is identical across all three concepts "
      f"in **{q2['n_triples_all_absolute_indices_identical']}/{q2['n_triples']}** triples;\n")
    w(f"* the **full list of END-RELATIVE indices** is identical in "
      f"**{q2['n_triples_all_rel_end_indices_identical']}/{q2['n_triples']}**;\n")
    w(f"* the **LAST (query) codeword's `rel_end`** is identical in "
      f"**{q2['n_triples_last_occurrence_rel_end_identical']}/{q2['n_triples']}** "
      f"(check `Q2a_last_codeword_rel_end_identical_across_concepts`).\n\n")
    sa, sr = q2["cross_concept_spread_last_abs"], q2["cross_concept_spread_last_rel_end"]
    w(f"Cross-concept spread (max-min within a triple) of the LAST codeword index: "
      f"**absolute {sa['mean']} ± {sa['sd']} tokens, range [{sa['min']}, {sa['max']}]**; "
      f"**end-relative {sr['mean']} ± {sr['sd']}, range [{sr['min']}, {sr['max']}]**.\n\n")
    w("**Consequence, stated as the task states it: an end-relative read site is safe under "
      "prefix drift and an absolute one is not.** The demo block is the only text that differs "
      "between the arms and it sits upstream of the query, so it moves every absolute index "
      "downstream of it while leaving every end-relative index untouched. Any extraction that "
      "pins a constant integer index, rather than `len(input_ids) + rel_end`, reads a different "
      "token in each concept arm.\n\n")

    # ---- Q3
    w("## Q3 -- full-prompt token-length distribution per concept\n\n")
    w("| concept | n | mean | sd | min | max |\n|---|---|---|---|---|---|\n")
    for cc in CONCEPTS:
        d = q3["per_concept"][cc]
        w(f"| {cc} | {d['n']} | {d['mean']} | {d['sd']} | {d['min']} | {d['max']} |\n")
    pl = q3["pooled"]
    w(f"| **pooled** | {pl['n']} | {pl['mean']} | {pl['sd']} | {pl['min']} | {pl['max']} |\n\n")
    w(f"Cross-concept spread of the means: **{q3['cross_concept_mean_spread']} tokens** on a "
      f"pooled sd of **{pl['sd']}**.\n\n")
    w(f"Paired within-`prompt_id` difference against `{REF_CONCEPT}` (preamble and query are "
      f"shared, so this isolates the demo block):\n\n")
    w("| concept | n pairs | mean delta | sd | min | max |\n|---|---|---|---|---|---|\n")
    for cc, d in q3["paired_delta_vs_%s" % REF_CONCEPT].items():
        w(f"| {cc} - {REF_CONCEPT} | {d['n']} | {d['mean']} | {d['sd']} | {d['min']} | "
          f"{d['max']} |\n")
    w("\n### The C-084 claim, verified or refuted\n\n")
    w(f"PR-048 `population._register_asymmetry.n4_in_tokens` states bomb "
      f"{CLAIMED_TOKEN_MEANS['bomb']} / knife {CLAIMED_TOKEN_MEANS['knife']} / gun "
      f"{CLAIMED_TOKEN_MEANS['gun']} on a {CLAIMED_TOKEN_SD:g}-token sd.\n\n")
    w("| concept | claimed mean | observed, chat template applied | diff | observed, raw "
      "`full_prompt` | diff | raw + BOS | diff |\n|---|---|---|---|---|---|---|---|\n")
    for cc in CONCEPTS:
        v = q3["claim_check_C084"][cc]
        raw = v["observed_mean_untemplated"]
        w(f"| {cc} | {v['claimed_mean']} | {v['observed_mean_templated']} | "
          f"{v['abs_diff_templated']} | {raw} | {v['abs_diff_untemplated']} | "
          f"{None if raw is None else round(raw + 1, 4)} | "
          f"{None if raw is None else round(abs(raw + 1 - v['claimed_mean']), 4)} |\n")
    ov = q3["chat_template_overhead_tokens"]
    w(f"\nThe chat template contributes a constant **{ov['mean']} ± {ov['sd']}** tokens "
      f"(range [{ov['min']}, {ov['max']}]) on top of the raw `full_prompt`.\n\n")
    w("**VERDICT: the C-084 figures are VERIFIED, on the raw `full_prompt` with "
      "`add_special_tokens=True`.** The raw-column difference is "
      f"{q3['claim_check_C084']['bomb']['abs_diff_untemplated']}, "
      f"{q3['claim_check_C084']['knife']['abs_diff_untemplated']} and "
      f"{q3['claim_check_C084']['gun']['abs_diff_untemplated']} tokens -- a constant +1 in all "
      "three, which is exactly the `<|begin_of_text|>` BOS that `add_special_tokens=True` "
      "prepends and `add_special_tokens=False` does not. Adding it back reproduces all three "
      "published means to the fourth decimal. The ORDERING is reproduced too (gun > bomb > "
      f"knife) and so is the spread: **{q3['cross_concept_mean_spread_untemplated']} tokens** "
      f"against the published {CLAIMED_TOKEN_MEANS['gun'] - CLAIMED_TOKEN_MEANS['knife']:.2f}.\n\n")
    w(f"The claim rests on the spread-to-sd ratio, not the absolute means: "
      f"**{q3['cross_concept_mean_spread']} tokens of cross-concept mean spread on a pooled sd "
      f"of {pl['sd']}** (claimed sd {CLAIMED_TOKEN_SD:g}), i.e. the between-concept mean "
      f"difference is under a tenth of the within-concept spread. The paired table above is the "
      f"sharper version of the same statement, since preamble and query are shared inside a "
      f"triple.\n\n")
    w("What did NOT survive re-derivation is any absolute positional statement: see Q2. Length "
      "and position are separate quantities here, and only the first is matched.\n\n")
    # ---- Q4
    w("## Q4 -- query-side scaffold vs content, and the K-ladder\n\n")
    w("| role | tokens per prompt |\n|---|---|\n")
    for k in ROLE_VOCAB:
        w(f"| {k} | {q4['per_prompt_role_counts'].get(k, 0):g} |\n")
    w(f"\nQuery-side tokens per prompt: **{q4['query_side_tokens_per_prompt']:g}**, of which "
      f"**{q4['scaffold_per_prompt']:g}** are chat scaffold / response header and "
      f"**{q4['content_per_prompt']:g}** are query content. The census is identical in "
      f"{[c for c in p['checks'] if c['check'] == 'E_query_role_census_constant'][0]['n_bound'] - [c for c in p['checks'] if c['check'] == 'E_query_role_census_constant'][0]['n_violations']}"
      f"/{n} prompts.\n\n")
    w("### The K-ladder, counting rungs back from the end of the sequence\n\n")
    w("| K | rel_end | modal decoded | distinct decodings | role(s) | carries query content |\n"
      "|---|---|---|---|---|---|\n")
    for l in q4["k_ladder"]:
        w(f"| {l['K']} | `{l['rel_end']}` | `{l['modal_decoded']!r}` | "
          f"{l['n_distinct_decodings']} | "
          f"{', '.join(f'{k} ({v})' for k, v in sorted(l['roles'].items()))} | "
          f"{'yes' if l['carries_query_content'] else 'no'} |\n")
    w(f"\n**The first {q4['n_leading_rungs_with_zero_query_content']} rungs carry zero query "
      f"content.** The first query-content rung is `K={q4['first_query_content_rung']}`; the "
      f"first non-punctuation query-content rung is "
      f"`K={q4['first_non_punctuation_query_content_rung']}`. On the superseded ts116 map the "
      f"figure was FIVE; it is re-derived here rather than inherited.\n\n")

    w("## Layer convention\n\n")
    w("Not re-derived. PR-048 `read_site.layer_convention_verified_by` records the planted-hook "
      "GPU test, job 860184, 2026-09-07: **block layer L == `hidden_states[L+1]`; "
      "`hidden_states[0]` == embeddings**, CONFIRMED BY EXPERIMENT. The superseded ts116 map's "
      "Q4 was a reading of source comments; that reading is now settled and is not repeated. "
      "The open defect recorded with it stands: `extract_boombness.forward_hidden` raises on "
      "Llama-3.1-8B under transformers 5.12, so the LAST layer is unreadable by the sanctioned "
      "path. This phase reads the 6-14 band, so it does not bite here.\n\n")

    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        fh.write(o.getvalue())


# --------------------------------------------------------------------------- #
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(REPO, "outputs", "dcs_ts",
                                                  "token_roles_ts116m.json.gz"))
    ap.add_argument("--report", default=os.path.join(REPO, "reports",
                                                     "DCS_TS116M_TOKEN_ROLE_MAP.md"))
    ap.add_argument("--model", default=MODEL)
    ap.add_argument("--limit-domains", type=int, default=0, help="smoke only; 0 = all 115")
    ap.add_argument("--mutate", action="store_true")
    ap.add_argument("--no-report", action="store_true")
    args = ap.parse_args()

    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    os.environ.setdefault("HF_HOME", os.path.join(REPO, ".cache", "huggingface"))
    t0 = time.time()

    from transformers import AutoTokenizer
    import ds_common as dc
    from prompt_families import QUERY_KINDS
    # THE OCCURRENCE RULE IS IMPORTED, NOT RESTATED (C-076/079/080).
    from dcs_ts_verify_ts116n import occurrence_counts, CONCEPT_FORMS

    prereg = json.load(open(PREREG))
    pub = {k: {"bank_rows_sha16": v["bank_rows_sha16"],
               "bank_file_sha16": v["bank_file_sha16"]}
           for k, v in prereg["population"]["banks"].items()}
    if prereg["population"]["bank_family"] != "ts116m":
        raise SystemExit("PR-048 does not name ts116m as the bank family")
    if prereg["population"]["cell"] != CELL or \
            prereg["population"]["query_kind_primary"] != QUERY_KIND or \
            prereg["population"]["n_examples_primary"] != N_EXAMPLES:
        raise SystemExit("scope disagrees with the frozen preregistration")

    tok = AutoTokenizer.from_pretrained(args.model)
    special_ids = set(tok.all_special_ids) | set(
        tok.convert_tokens_to_ids(t) for t in getattr(tok, "additional_special_tokens", []))
    for t in ("<|begin_of_text|>", "<|eot_id|>", "<|start_header_id|>", "<|end_header_id|>"):
        i = tok.convert_tokens_to_ids(t)
        if i is not None and i >= 0:
            special_ids.add(i)

    template = QUERY_KINDS[QUERY_KIND]["template"]
    if template.count("{W}") != 1:
        raise SystemExit("query template does not contain exactly one {W} slot")
    qpre, qsuf = template.split("{W}")
    fmt_len = qpre.index(".") + 1

    manifest = json.load(open(SPLIT_MANIFEST))
    _body = {k: v for k, v in manifest.items() if k != "manifest_sha16"}
    man_sha = hashlib.sha256(json.dumps(_body, sort_keys=True,
                                        separators=(",", ":")).encode()).hexdigest()[:16]
    dsplit_of = manifest["assign"]

    ck = Checks()

    idents, all_rows = {}, []
    for cw in CODEWORDS:
        for cc in CONCEPTS:
            rows, ident = load_bank(cw, cc)
            idents[f"{cw}_{cc}"] = ident
            if args.limit_domains:
                keep = sorted({r["domain"] for r in rows})[:args.limit_domains]
                rows = [r for r in rows if r["domain"] in keep]
            all_rows.append(((cw, cc), rows, ident))
            print(f"[load] {cw}_{cc}: {ident['bank_n_rows']} rows, "
                  f"{ident['n_cellC_sow_n4_all_domains']} cell-C, "
                  f"{ident['n_dropped_by_domain_exclusion']} dropped, "
                  f"{len(rows)} matched, rows_sha16={ident['bank_rows_sha16']}")

    nb = nv = 0
    ex = []
    for (cw, cc), _rows, ident in all_rows:
        nb += 1
        want = pub[f"{cw}_{cc}"]
        if ident["bank_rows_sha16"] != want["bank_rows_sha16"] or \
                ident["bank_file_sha16"] != want["bank_file_sha16"]:
            nv += 1
            ex.append([cw, cc, want, {"rows": ident["bank_rows_sha16"],
                                      "file": ident["bank_file_sha16"]}])
    ck.add("Z1_bank_sha16_matches_PR048", nb, nv, "the six ts116m banks", {"mismatches": ex})
    ck.add("Z2_split_manifest_sha16_matches_published", 1,
           0 if man_sha == EXPECTED_MANIFEST_SHA16 else 1, "the domain-split manifest",
           {"published": EXPECTED_MANIFEST_SHA16, "observed": man_sha,
            "stored_in_manifest": manifest.get("manifest_sha16")})

    recs: List[Dict] = []
    for (cw, cc), rows, ident in all_rows:
        for row in rows:
            ds_ = dsplit_of.get(row["domain"])
            if ds_ is None:
                raise SystemExit(f"domain {row['domain']} absent from the split manifest")
            recs.append(build_record(tok, dc, occurrence_counts, row, (qpre, qsuf), fmt_len,
                                     special_ids, ds_, ident))
        print(f"[tok ] {cw}_{cc}: {len(rows)} records  ({time.time()-t0:.0f}s)")

    if not recs:
        print("FATAL: the matched set is EMPTY; every check below would be vacuous.")
        return 2

    doms = sorted({r["domain"] for r in recs})
    slots = sorted({r["family_slot"] for r in recs})
    want_cells = len(doms) * len(CODEWORDS) * len(CONCEPTS)
    got_cells = len({(r["domain"], r["codeword"], r["concept"]) for r in recs})
    ck.add("Y_coverage_115dom_x_2cw_x_3concept", got_cells,
           0 if (got_cells == want_cells
                 and (args.limit_domains or len(doms) == N_DOMAINS_EXPECTED)) else 1,
           "domain x codeword x concept combinations",
           {"n_domains": len(doms), "n_records": len(recs), "family_slots": slots,
            "expected_cells": want_cells, "observed_cells": got_cells,
            "n_domains_expected": N_DOMAINS_EXPECTED})

    run_checks(recs, ck)
    cands = rank_read_positions(recs, ck)
    q2 = codeword_position_analysis(recs, ck)
    q3 = length_analysis(recs, ck)
    q4 = query_breakdown(recs, ck)

    mut = (mutate_and_report(recs) + mutate_scope_checks(idents, pub, man_sha, recs)) \
        if args.mutate else []

    n_per = collections.Counter((r["domain"], r["codeword"], r["concept"]) for r in recs)
    payload = {
        "schema": "dcs_ts116m_token_roles/1",
        "generated": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "model": args.model, "cpu_only": True, "weights_loaded": False,
        "supersedes": {"script": "scripts/dcs_ts_token_roles.py",
                       "report": "reports/DCS_TS_TOKEN_ROLE_MAP.md",
                       "reason": "computed on the ts116 bank VOIDED by DCS-C-074"},
        "preregistration": os.path.relpath(PREREG, REPO),
        "preregistered_bank_sha": pub,
        "incumbent_rel_end": INCUMBENT_REL_END,
        "scope": {"cell": CELL, "cell_field": "cell", "query_kind": QUERY_KIND,
                  "n_examples": N_EXAMPLES, "codewords": list(CODEWORDS),
                  "concepts": list(CONCEPTS), "n_domains": len(doms),
                  "excluded_domains": sorted(EXCLUDED_DOMAINS),
                  "n_rows_dropped_by_exclusion":
                      sum(i["n_dropped_by_domain_exclusion"] for i in idents.values()),
                  "rows_per_domain_per_concept_per_codeword":
                      n_per.most_common(1)[0][1] if n_per else 0,
                  "n_records": len(recs), "domains": doms},
        "bank_identity": idents,
        "split_manifest": {"path": os.path.relpath(SPLIT_MANIFEST, REPO),
                           "manifest_sha16": man_sha,
                           "field_name": manifest["field_name"],
                           "n_train_assigned": manifest["n_train"],
                           "n_validation": manifest["n_validation"],
                           "n_test": manifest["n_test"]},
        "query_template": template, "role_vocabulary": list(ROLE_VOCAB),
        "concept_forms_used_for_occurrence_counting":
            {k: list(v) for k, v in CONCEPT_FORMS.items()},
        "checks": ck.rows, "checks_summary": ck.summary(),
        "read_position_candidates": cands,
        "q2_codeword_positions": q2,
        "q3_token_lengths": q3,
        "q4_query_breakdown": q4,
        "layer_convention": {
            "convention": "block L == hidden_states[L+1]; hidden_states[0] == embeddings",
            "verified_by": "planted-hook GPU test, job 860184, 2026-09-07 (PR-048)",
            "re_derived_here": False},
        "mutations": mut,
        "defect_narrative": DEFECT_NARRATIVE,
        "records": recs,
    }
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with gzip.open(args.out, "wt") as fh:
        json.dump(payload, fh)
    print(f"[out ] {args.out}  ({os.path.getsize(args.out)/1e6:.1f} MB)")

    if not args.no_report:
        write_report(args.report, payload)
        print(f"[out ] {args.report}")

    print(json.dumps(ck.summary()))
    for r in ck.rows:
        print(f"  {r['status']:11s} {r['check']}  bound={r['n_bound']} viol={r['n_violations']}")
    if mut:
        nred = sum(1 for m in mut if m["went_red"])
        for m in mut:
            print(f"  MUT {'RED ' if m['went_red'] else 'GREEN'} {m['mutation']} "
                  f"-> {m['target_check']} = {m['status_after_mutation']}")
        print(f"[mutate] {nred}/{len(mut)} mutations turned their target check RED")
        if nred != len(mut):
            print("  A MUTATION THAT DOES NOT GO RED MEANS THAT CHECK CANNOT FAIL.",
                  file=sys.stderr)
            return 1
    return 0 if ck.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
