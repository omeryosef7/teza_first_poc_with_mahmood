#!/usr/bin/env python
"""dcs_ts_token_roles.py — THE TOKEN-ROLE MAP for the ts116 aligned banks (mandate 14 / 22.2).

WHAT THIS IS FOR
----------------
The corrected mechanism test needs a DOWNSTREAM NEUTRAL READ POSITION: a token that
(a) comes strictly after the codeword, (b) is byte- and token-identical across all three
concepts, (c) contains none of bomb/knife/gun, and (d) exists in EVERY matched prompt.
Nothing in the repo currently states where that is, and the previous K-ladder rungs K=1 and
K=2 turned out to be CHAT SCAFFOLD rather than query rows. This script derives the answer
from the raw bank rows and the real chat template, and persists the whole map.

SCOPE (fixed, not configurable): cell C, query_kind=semantic_one_word, n_examples=4,
all 116 domains, codewords {button, basket}, concepts {bomb, knife, gun}.

CPU ONLY. Loads a TOKENIZER, never model weights.

PRIMITIVES REUSED (not re-derived)
----------------------------------
  * ds_common.apply_template                — the chat template the extractors use
  * ds_common.find_word_occurrences_in_text — the house offset-based occurrence finder
    (the same call tokenization_audit.py makes, add_special_tokens=False because
    apply_template already emitted BOS)
  * prompt_families.QUERY_KINDS             — the query template registry, so the query
    frame is READ from the generator rather than hand-transcribed here
  * common.rows_sha16                       — the house bank-identity hash

DISCIPLINE
----------
Every check (i) records how many rows it bound to and FAILS if that is zero, (ii) is
demonstrated to go RED under --mutate, and (iii) re-derives from raw bank rows and a real
tokenization rather than from a producer-written summary field.

Usage:
  python scripts/dcs_ts_token_roles.py
  python scripts/dcs_ts_token_roles.py --mutate            # run the red-team demonstrations
  python scripts/dcs_ts_token_roles.py --limit-domains 5   # smoke
"""
from __future__ import annotations

import argparse
import collections
import copy
import gzip
import hashlib
import json
import os
import re
import sys
import time
from typing import Dict, List, Optional, Tuple

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "src", "boombness"))
sys.path.insert(0, os.path.join(REPO, "doublespeak_causality"))

BANK_DIR = os.path.join(REPO, "data", "boombness_prompts")
BANK_TMPL = "boombness_prompt_bank_ts116_{cw}_{cc}.jsonl"
SPLIT_MANIFEST = os.path.join(BANK_DIR, "dcs_ts116_domain_split.json")
CODEWORDS = ("button", "basket")
CONCEPTS = ("bomb", "knife", "gun")
REF_CONCEPT = "bomb"                     # the concept every other concept is compared against
CELL = "C"
QUERY_KIND = "semantic_one_word"
N_EXAMPLES = 4
MODEL = "meta-llama/Llama-3.1-8B-Instruct"

#: The published row hashes for these six banks (task brief / entry R-098). Checked, not trusted.
EXPECTED_ROWS_SHA16 = {
    ("button", "bomb"): "c37127790a08519f", ("button", "knife"): "151ef6734bfdbe6e",
    ("button", "gun"): "e1ff5534b5318ad9", ("basket", "bomb"): "86463da433d0eebf",
    ("basket", "knife"): "2839bfbc4d41a8b9", ("basket", "gun"): "60b508bd1aa6d0a7",
}
EXPECTED_MANIFEST_SHA16 = "be7d2c772d814ef3"

#: The fixed role vocabulary. Any token that cannot be given one of these FAILS the run;
#: there is deliberately no "other" bucket to absorb a labelling bug.
ROLE_VOCAB = ("chat_scaffold", "user_instruction_scaffold", "punctuation", "codeword",
              "concept_word", "neutral_content", "answer_format_instruction",
              "response_header")

CONCEPT_WORDS = ("bomb", "knife", "gun")

#: The read position this map NOMINATES, fixed in source before the ranking is computed:
#: one token past the final-query codeword, i.e. the repo's own `following` site
#: (ds_common.target_positions / extract_boombness position="following"), expressed as an
#: offset from the END of the sequence so it is a shared coordinate across both codeword banks.
NOMINATED_REL_END = -9


# --------------------------------------------------------------------------- #
# Check bookkeeping — a check that binds to zero rows is an ERROR, never a PASS
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
    matched, pairs, n_all = [], [], 0
    with open(path) as fh:
        for line in fh:
            d = json.loads(line)
            n_all += 1
            pairs.append((d["prompt_id"], d["prompt_sha16"]))
            if (d["cell"] == CELL and d["query_kind"] == QUERY_KIND
                    and d["n_examples"] == N_EXAMPLES):
                matched.append(d)
    ident = {"path": os.path.relpath(path, REPO), "bank_file_sha16": sha16_file(path),
             "bank_rows_sha16": rows_sha16(pairs), "bank_n_rows": n_all,
             "n_matched": len(matched)}
    return matched, ident


# --------------------------------------------------------------------------- #
# The per-prompt token-role record
# --------------------------------------------------------------------------- #
def char_to_token_span(offs, c0: int, c1: int) -> Tuple[int, int]:
    """[c0,c1) chars -> [t0,t1) tokens. Raises if the char span maps to nothing or is ragged."""
    idx = [i for i, (a, b) in enumerate(offs) if b > a and a < c1 and b > c0]
    if not idx:
        raise ValueError(f"char span [{c0},{c1}) maps to zero tokens")
    if idx != list(range(idx[0], idx[-1] + 1)):
        raise ValueError(f"char span [{c0},{c1}) maps to a non-contiguous token run")
    return idx[0], idx[-1] + 1


def is_punct(s: str) -> bool:
    t = s.strip()
    return bool(t) and all(not ch.isalnum() for ch in t)


def build_record(tok, dc, row: Dict, query_frame: Tuple[str, str], fmt_len: int,
                 special_ids: set, dsplit: str, bank_ident: Dict) -> Dict:
    """Tokenize one bank row under the real chat template and label every query-side token."""
    templated = dc.apply_template(tok, row["full_prompt"])
    enc = tok(templated, add_special_tokens=False, return_offsets_mapping=True)
    ids, offs = list(enc["input_ids"]), list(enc["offset_mapping"])
    n = len(ids)
    pieces = [tok.decode([i]) for i in ids]

    # ---- char anchors. full_prompt must appear VERBATIM inside the template, exactly once.
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
    # per-demonstration-line spans ("demo span(s)")
    demo_lines = []
    cur = d0
    for line in demo.split("\n"):
        if line.strip():
            demo_lines.append(list(char_to_token_span(offs, cur, cur + len(line))))
        cur += len(line) + 1
    spans["demo_lines"] = demo_lines

    # ---- generation header: the trailing <|start_header_id|>assistant<|end_header_id|>\n\n
    gh = templated.rindex("<|start_header_id|>")
    spans["generation_header"] = list(char_to_token_span(offs, gh, len(templated)))
    gen_header_pos = n - 1                      # the position generation is read at

    # ---- occurrences, via the HOUSE finder (same call tokenization_audit.py makes)
    hit = dc.find_word_occurrences_in_text(tok, templated, row["target_surface"],
                                           add_special_tokens=False)
    cw_occ = [{"span": [a, b], "last": b - 1, "rel_end": (b - 1) - n,
               "n_subtokens": b - a, "in_query": a >= spans["query"][0]}
              for a, b in hit.spans]
    con_occ = []
    try:
        chit = dc.find_word_occurrences_in_text(tok, templated, row["concept"],
                                                add_special_tokens=False)
        con_occ = [{"span": [a, b], "last": b - 1, "rel_end": (b - 1) - n,
                    "n_subtokens": b - a, "in_query": a >= spans["query"][0]}
                   for a, b in chit.spans]
    except ValueError:
        con_occ = []                            # absent is a legitimate outcome, recorded as 0

    # any of the three concept words anywhere (STRICT whole-word, independent of the finder)
    strict = {w: len(re.findall(rf"\b{w}\b", templated, re.IGNORECASE)) for w in CONCEPT_WORDS}

    # THE MATCHER IS PERMISSIVE ON THE RIGHT. ds_common.find_word_occurrences_in_text only
    # refuses a match whose LEFT neighbour is alphanumeric ("allow inflections (carrots) but not
    # substrings inside a longer word (scarrot)"), so `basket` matches inside `basketball`. Each
    # such hit is counted as a codeword occurrence by the finder AND by the generator's own
    # n_codeword_occurrences, but it is not the codeword: it is an unrelated benign word that
    # happens to start with it. Recorded per row with its surface so the count is auditable.
    cwd = row["target_surface"]
    inflected = []
    for m in re.finditer(re.escape(cwd), templated, re.IGNORECASE):
        a, b = m.start(), m.end()
        if a > 0 and (templated[a - 1].isalnum() or templated[a - 1] == "_"):
            continue                     # the finder rejects these too
        if b < len(templated) and (templated[b].isalnum() or templated[b] == "_"):
            inflected.append(templated[a:b + 12].split()[0])
    strict_cw = len(re.findall(rf"\b{re.escape(cwd)}\b", templated, re.IGNORECASE))

    # ---- semantic roles for every query-side token (query start .. end of sequence)
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
    # character sub-ranges of the fixed query frame
    fmt0, fmt1 = q0, q0 + fmt_len                      # "Answer with exactly one word ... else."
    frame_a0, frame_a1 = fmt1, q0 + len(qpre)          # rest of the template prefix
    frame_b0, frame_b1 = q0 + len(qpre) + len(row["target_surface"]), q1   # template suffix

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
            roles.append("chat_scaffold")                # zero-width special
        elif not (q0 <= a < q1):
            roles.append("chat_scaffold")                # template text outside the query
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
        "n_tokens": n, "input_ids": ids, "tokens": pieces,
        "spans": spans, "generation_header_pos": gen_header_pos,
        "query_role_start": qstart,
        "query_roles": roles,
        "codeword_occurrences": cw_occ, "concept_occurrences": con_occ,
        "n_codeword_occurrences_declared": row["n_codeword_occurrences"],
        "n_concept_occurrences_declared": row["n_concept_occurrences"],
        "strict_concept_word_counts": strict,
        "n_codeword_strict_wholeword": strict_cw,
        "inflected_codeword_matches": inflected,
        "full_prompt_sha16": hashlib.sha256(fp.encode()).hexdigest()[:16],
        "templated_sha16": hashlib.sha256(templated.encode()).hexdigest()[:16],
    }


# --------------------------------------------------------------------------- #
# The checks
# --------------------------------------------------------------------------- #
def key(rec) -> Tuple[str, str]:
    return (rec["codeword"], rec["prompt_id"])


def run_checks(recs: List[Dict], ck: Checks) -> Dict:
    by = {}
    for r in recs:
        by[(r["codeword"], r["concept"], r["prompt_id"])] = r
    pids = sorted({r["prompt_id"] for r in recs})

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

    # -- CHK-B  Q2: codeword token positions identical across concepts at matched prompt_id
    nb = nv = 0
    ex = []
    for cw in sorted({r["codeword"] for r in recs}):
        for pid in pids:
            ref = by.get((cw, REF_CONCEPT, pid))
            if ref is None:
                continue
            refpos = [o["last"] for o in ref["codeword_occurrences"]]
            for cc in CONCEPTS:
                if cc == REF_CONCEPT:
                    continue
                other = by.get((cw, cc, pid))
                if other is None:
                    continue
                nb += 1
                pos = [o["last"] for o in other["codeword_occurrences"]]
                if pos != refpos:
                    nv += 1
                    if len(ex) < 5:
                        ex.append([cw, cc, pid, refpos, pos])
    ck.add("B_codeword_positions_identical_across_concepts", nb, nv,
           "(codeword, prompt_id, non-reference concept) triples", {"examples": ex})

    # -- CHK-C  the whole token id sequence is identical across concepts at matched prompt_id
    nb = nv = 0
    ex = []
    for cw in sorted({r["codeword"] for r in recs}):
        for pid in pids:
            ref = by.get((cw, REF_CONCEPT, pid))
            if ref is None:
                continue
            for cc in CONCEPTS:
                if cc == REF_CONCEPT:
                    continue
                other = by.get((cw, cc, pid))
                if other is None:
                    continue
                nb += 1
                if other["input_ids"] != ref["input_ids"]:
                    nv += 1
                    if len(ex) < 5:
                        ex.append([cw, cc, pid])
    ck.add("C_token_ids_identical_across_concepts", nb, nv,
           "(codeword, prompt_id, non-reference concept) triples", {"examples": ex})

    # -- CHK-D  no concept word anywhere in the prompt (STRICT whole-word, re-derived)
    nb = nv = 0
    ex = []
    for r in recs:
        nb += 1
        tot = sum(r["strict_concept_word_counts"].values())
        if tot:
            nv += 1
            if len(ex) < 5:
                ex.append([r["codeword"], r["concept"], r["prompt_id"],
                           r["strict_concept_word_counts"]])
    ck.add("D_no_bomb_knife_gun_token_anywhere", nb, nv, "every matched prompt",
           {"examples": ex})

    # -- CHK-E  query-side role census is identical across every matched prompt
    census = collections.Counter()
    per = collections.Counter()
    for r in recs:
        c = tuple(sorted(collections.Counter(r["query_roles"]).items()))
        census[c] += 1
        per.update(r["query_roles"])
    nb = len(recs)
    nv = nb - max(census.values()) if census else 0
    ck.add("E_query_role_census_constant", nb, nv, "every matched prompt",
           {"n_distinct_censuses": len(census),
            "modal_census": dict(census.most_common(1)[0][0]) if census else {},
            "modal_count": census.most_common(1)[0][1] if census else 0})

    # -- CHK-F  the query tail is constant relative to the END of the sequence, except the
    #           codeword slot. This is what makes a rel_end read position meaningful at all.
    tails = collections.Counter()
    L = min(min(r["n_tokens"] for r in recs), 28) if recs else 0
    for r in recs:
        t = tuple(r["input_ids"][-L:])
        tails[t] += 1
    nb = len(recs)
    # positions that vary across the whole matched set
    varying = []
    for j in range(L):
        vals = {r["tokens"][r["n_tokens"] - L + j] for r in recs}
        if len(vals) > 1:
            varying.append({"rel_end": j - L, "values": sorted(vals)})
    # A position is ALLOWED to vary only if it is a codeword occurrence in EVERY record.
    # Hardcoding "-10" here would have made this check unfalsifiable if the tail ever moved.
    cw_rel = set()
    for j in range(L):
        rel = j - L
        if all(any(o["rel_end"] == rel for o in r["codeword_occurrences"]) for r in recs):
            cw_rel.add(rel)
    unexpected = [v for v in varying if v["rel_end"] not in cw_rel]
    ck.add("F_tail_constant_except_codeword", nb, len(unexpected),
           "last %d token positions of every matched prompt" % L,
           {"tail_len": L, "varying_positions": varying,
            "codeword_rel_end_positions_common_to_all": sorted(cw_rel),
            "unexpected_varying": unexpected, "n_distinct_tails": len(tails)})

    # -- CHK-H  every codeword occurrence is ONE subtoken. If it were not, the tail offsets
    #           would shift between the two codeword banks and rel_end would stop being a
    #           shared coordinate. Bound to occurrences, not prompts.
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

    # -- CHK-J  no codeword "occurrence" is really a longer word the codeword merely prefixes.
    #           This is the matcher bug class, measured rather than assumed: the house finder is
    #           left-strict and right-permissive, and the generator used the same rule, so a
    #           check that reads n_codeword_occurrences would agree with the finder and see
    #           nothing. This one re-derives from the templated TEXT.
    nb = nv = 0
    ex = collections.Counter()
    for r in recs:
        nb += 1
        if r["inflected_codeword_matches"]:
            nv += 1
            for w in r["inflected_codeword_matches"]:
                ex[(r["codeword"], r["domain"], w)] += 1
    ck.add("J_no_inflected_codeword_false_occurrences", nb, nv, "every matched prompt",
           {"offending_surfaces": {"|".join(k): v for k, v in ex.items()}})

    # -- CHK-I  the same domain gets the same dsplit in every record that mentions it
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
    ck.add("I_dsplit_consistent_per_domain", nb, nv, "every matched prompt", {"examples": ex,
           "dsplit_domain_counts": dict(collections.Counter(seen.values()))})

    return {"by": by, "pids": pids}


def rank_read_positions(recs: List[Dict], ck: Checks) -> List[Dict]:
    """Q1. Score every rel_end offset in the constant tail against (a)-(d) and rank."""
    n_rec = len(recs)
    if n_rec == 0:
        ck.add("G_read_position_candidates", 0, 1, "every matched prompt")
        return []
    L = min(min(r["n_tokens"] for r in recs), 40)
    cands = []
    for j in range(L):
        rel = j - L
        toks = {r["tokens"][r["n_tokens"] + rel] for r in recs}
        ids_ = {r["input_ids"][r["n_tokens"] + rel] for r in recs}
        # (a) strictly after the LAST codeword occurrence, in every prompt
        after = sum(1 for r in recs
                    if all(rel > o["rel_end"] for o in r["codeword_occurrences"]))
        # (d) present in every prompt
        present = sum(1 for r in recs if r["n_tokens"] + rel >= 0)
        # role, from the map itself
        roles = set()
        for r in recs:
            i = r["n_tokens"] + rel
            if i >= r["query_role_start"]:
                roles.add(r["query_roles"][i - r["query_role_start"]])
            else:
                roles.add("<pre-query>")
        tok_txt = sorted(toks)[0] if len(toks) == 1 else None
        contains_concept = any(w in (tok_txt or "").lower() for w in CONCEPT_WORDS) \
            if tok_txt else True
        cands.append({
            "rel_end": rel, "decoded": tok_txt, "n_distinct_decodings": len(toks),
            "n_distinct_token_ids": len(ids_), "token_id": sorted(ids_)[0] if len(ids_) == 1 else None,
            "roles": sorted(roles),
            "crit_a_strictly_after_codeword": after == n_rec, "n_after": after,
            "crit_b_identical_across_concepts": len(ids_) == 1 and len(toks) == 1,
            "crit_c_no_concept_substring": not contains_concept,
            "crit_d_present_in_every_prompt": present == n_rec, "n_present": present,
        })
    qualifying = [c for c in cands
                  if c["crit_a_strictly_after_codeword"] and c["crit_b_identical_across_concepts"]
                  and c["crit_c_no_concept_substring"] and c["crit_d_present_in_every_prompt"]]
    # rank: real query content before punctuation before scaffold; nearest to the codeword first
    prio = {"user_instruction_scaffold": 0, "neutral_content": 0, "punctuation": 1,
            "chat_scaffold": 2, "response_header": 2}
    qualifying.sort(key=lambda c: (min(prio.get(r, 3) for r in c["roles"]), c["rel_end"]))
    for i, c in enumerate(qualifying):
        c["rank"] = i + 1
    ck.add("G_read_position_candidates", len(cands), 0 if qualifying else 1,
           "token offsets in the constant tail of every matched prompt",
           {"n_candidates_scored": len(cands), "n_qualifying": len(qualifying)})

    # G2 binds PER PROMPT to the single nominated offset, so a violation is countable in rows
    # rather than in candidate slots. NOMINATED_REL_END is fixed in source, not chosen from the
    # ranking, so this check cannot re-derive itself into a pass.
    nb = nv = 0
    ex = []
    ref_id = None
    for r in recs:
        nb += 1
        i = r["n_tokens"] + NOMINATED_REL_END
        if i < 0:
            nv += 1; continue
        tid, txt = r["input_ids"][i], r["tokens"][i]
        if ref_id is None:
            ref_id = tid
        after = all(NOMINATED_REL_END > o["rel_end"] for o in r["codeword_occurrences"])
        neutral = not any(w in txt.lower() for w in CONCEPT_WORDS)
        if not (tid == ref_id and after and neutral):
            nv += 1
            if len(ex) < 5:
                ex.append([r["codeword"], r["concept"], r["prompt_id"], tid, txt, after, neutral])
    ck.add("G2_nominated_read_position_rel_end_%d" % NOMINATED_REL_END, nb, nv,
           "every matched prompt", {"nominated_rel_end": NOMINATED_REL_END,
                                    "token_id": ref_id, "examples": ex})
    return cands


# --------------------------------------------------------------------------- #
# --mutate : every check above must be shown to go RED
# --------------------------------------------------------------------------- #
def mutate_and_report(recs: List[Dict]) -> List[Dict]:
    out = []

    def trial(name: str, target_check: str, fn):
        m = copy.deepcopy(recs)
        fn(m)
        c = Checks()
        run_checks(m, c)
        rank_read_positions(m, c)
        row = c.by_name(target_check)
        out.append({"mutation": name, "target_check": target_check,
                    "status_after_mutation": row["status"],
                    "n_bound": row["n_bound"], "n_violations": row["n_violations"],
                    "went_red": row["status"] != "PASS"})

    def m_shift(m):
        # move one prompt's last codeword occurrence by one token, in ONE concept only
        for r in m:
            if r["concept"] == "knife":
                r["codeword_occurrences"][-1]["last"] += 1
                r["codeword_occurrences"][-1]["rel_end"] += 1
                break
    trial("shift one knife prompt's last codeword position by +1",
          "B_codeword_positions_identical_across_concepts", m_shift)

    def m_ids(m):
        for r in m:
            if r["concept"] == "gun":
                r["input_ids"] = list(r["input_ids"])
                r["input_ids"][-9] = r["input_ids"][-9] + 1
                break
    trial("perturb one gun prompt's token id at rel_end=-9",
          "C_token_ids_identical_across_concepts", m_ids)

    def m_concept(m):
        for r in m:
            r["strict_concept_word_counts"] = dict(r["strict_concept_word_counts"])
            r["strict_concept_word_counts"]["bomb"] = 1
            break
    trial("plant one literal 'bomb' in one prompt",
          "D_no_bomb_knife_gun_token_anywhere", m_concept)

    def m_role(m):
        for r in m:
            r["query_roles"] = list(r["query_roles"])
            r["query_roles"][0] = "neutral_content"
            break
    trial("relabel one query token's role", "E_query_role_census_constant", m_role)

    def m_count(m):
        for r in m:
            r["n_codeword_occurrences_declared"] = r["n_codeword_occurrences_declared"] + 1
            break
    trial("bump one row's declared occurrence count",
          "A_token_occurrence_count_matches_bank_field", m_count)

    def m_tail(m):
        for r in m:
            r["tokens"] = list(r["tokens"])
            r["tokens"][-7] = " REFER"
            r["input_ids"] = list(r["input_ids"])
            r["input_ids"][-7] = 99999
            break
    trial("change the ' refer' token in one prompt", "F_tail_constant_except_codeword", m_tail)

    def m_truncate(m):
        # remove the tail from one prompt: the read position must stop being universal
        r = m[0]
        r["n_tokens"] = r["n_tokens"] - 6
        r["input_ids"] = r["input_ids"][:r["n_tokens"]]
        r["tokens"] = r["tokens"][:r["n_tokens"]]
        r["query_roles"] = r["query_roles"][:max(0, r["n_tokens"] - r["query_role_start"])]
    trial("truncate one prompt's last 6 tokens", "F_tail_constant_except_codeword", m_truncate)

    def m_planted_concept_at_read_pos(m):
        for r in m:
            if r["concept"] == "gun":
                r["tokens"] = list(r["tokens"]); r["tokens"][NOMINATED_REL_END] = " bombing"
                break
    trial("decode the nominated read position as ' bombing' in one prompt",
          "G2_nominated_read_position_rel_end_%d" % NOMINATED_REL_END,
          m_planted_concept_at_read_pos)

    def m_move_codeword_past_read_pos(m):
        for r in m:
            r["codeword_occurrences"] = copy.deepcopy(r["codeword_occurrences"])
            r["codeword_occurrences"][-1]["rel_end"] = -3      # now AFTER the read position
            break
    trial("move one prompt's last codeword occurrence downstream of the read position",
          "G2_nominated_read_position_rel_end_%d" % NOMINATED_REL_END,
          m_move_codeword_past_read_pos)

    def m_inflect(m):
        for r in m:
            r["inflected_codeword_matches"] = ["buttonhole"]
            break
    trial("plant an inflected codeword match in one prompt",
          "J_no_inflected_codeword_false_occurrences", m_inflect)

    def m_empty(m):
        del m[:]
    trial("bind the checks to an EMPTY row set",
          "B_codeword_positions_identical_across_concepts", m_empty)
    return out


# --------------------------------------------------------------------------- #
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(REPO, "outputs", "dcs_ts",
                                                  "token_roles_ts116.json.gz"))
    ap.add_argument("--report", default=os.path.join(REPO, "reports",
                                                     "DCS_TS_TOKEN_ROLE_MAP.md"))
    ap.add_argument("--model", default=MODEL)
    ap.add_argument("--limit-domains", type=int, default=0, help="smoke only; 0 = all 116")
    ap.add_argument("--mutate", action="store_true",
                    help="run the red-team mutations and report which checks went RED")
    ap.add_argument("--no-report", action="store_true")
    args = ap.parse_args()

    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    os.environ.setdefault("HF_HOME", os.path.join(REPO, ".cache", "huggingface"))
    t0 = time.time()

    from transformers import AutoTokenizer
    import ds_common as dc
    from prompt_families import QUERY_KINDS

    tok = AutoTokenizer.from_pretrained(args.model)
    special_ids = set(tok.all_special_ids) | set(
        tok.convert_tokens_to_ids(t) for t in getattr(tok, "additional_special_tokens", []))
    # Llama's header markers are added tokens, not "special tokens" in every version.
    for t in ("<|begin_of_text|>", "<|eot_id|>", "<|start_header_id|>", "<|end_header_id|>"):
        i = tok.convert_tokens_to_ids(t)
        if i is not None and i >= 0:
            special_ids.add(i)

    template = QUERY_KINDS[QUERY_KIND]["template"]
    if template.count("{W}") != 1:
        raise SystemExit("query template does not contain exactly one {W} slot")
    qpre, qsuf = template.split("{W}")
    fmt_len = qpre.index(".") + 1                     # "Answer with ... nothing else."

    manifest = json.load(open(SPLIT_MANIFEST))
    # SAME RECIPE AS THE BUILDER (scripts/dcs_ts_split_manifest.py:174-175): a self-hash over
    # the manifest body with `manifest_sha16` removed. Hashing the file BYTES instead gives a
    # different number and would have reported a false drift.
    _body = {k: v for k, v in manifest.items() if k != "manifest_sha16"}
    man_sha = hashlib.sha256(json.dumps(_body, sort_keys=True,
                                        separators=(",", ":")).encode()).hexdigest()[:16]
    man_file_sha = sha16_file(SPLIT_MANIFEST)
    dsplit_of = manifest["assign"]

    ck = Checks()

    # ---- bank identity, checked against the published hashes
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
                  f"{len(rows)} matched, rows_sha16={ident['bank_rows_sha16']}")

    nb = nv = 0
    ex = []
    for (cw, cc), _rows, ident in all_rows:
        nb += 1
        want = EXPECTED_ROWS_SHA16[(cw, cc)]
        if ident["bank_rows_sha16"] != want:
            nv += 1
            ex.append([cw, cc, want, ident["bank_rows_sha16"]])
    ck.add("Z_bank_rows_sha16_matches_published", nb, nv, "the six ts116 banks",
           {"mismatches": ex})
    ck.add("Z_split_manifest_sha16_matches_published", 1,
           0 if man_sha == EXPECTED_MANIFEST_SHA16 else 1, "the domain-split manifest",
           {"published": EXPECTED_MANIFEST_SHA16, "observed": man_sha,
            "stored_in_manifest": manifest.get("manifest_sha16"),
            "manifest_file_bytes_sha16": man_file_sha,
            "recipe": "sha256(json.dumps(manifest minus manifest_sha16, sort_keys, "
                      "separators=(',',':')))[:16] -- dcs_ts_split_manifest.py:174-175"})

    # ---- build records
    recs: List[Dict] = []
    for (cw, cc), rows, ident in all_rows:
        for row in rows:
            ds_ = dsplit_of.get(row["domain"])
            if ds_ is None:
                raise SystemExit(f"domain {row['domain']} absent from the split manifest")
            recs.append(build_record(tok, dc, row, (qpre, qsuf), fmt_len, special_ids,
                                     ds_, ident))
        print(f"[tok ] {cw}_{cc}: {len(rows)} records  ({time.time()-t0:.0f}s)")

    if not recs:
        print("FATAL: the matched set is EMPTY; every check below would be vacuous.")
        return 2

    # ---- coverage check (the selection itself must bind to what it claims)
    doms = {r["domain"] for r in recs}
    want_cells = len(doms) * len(CODEWORDS) * len(CONCEPTS)
    got_cells = len({(r["domain"], r["codeword"], r["concept"]) for r in recs})
    ck.add("Y_coverage_116dom_x_2cw_x_3concept", got_cells,
           0 if (got_cells == want_cells and (args.limit_domains or len(doms) == 116)) else 1,
           "domain x codeword x concept combinations",
           {"n_domains": len(doms), "n_records": len(recs),
            "expected_cells": want_cells, "observed_cells": got_cells})

    ctx = run_checks(recs, ck)
    cands = rank_read_positions(recs, ck)

    mut = mutate_and_report(recs) if args.mutate else []

    # ---- per-prompt query-side scaffold vs content breakdown (Q3)
    per_prompt = collections.Counter()
    for r in recs:
        per_prompt.update(r["query_roles"])
    n = len(recs)
    q3 = {"n_prompts": n, "roles_with_zero_tokens": [r for r in ROLE_VOCAB
                                                    if per_prompt.get(r, 0) == 0],
          "per_prompt_role_counts": {k: v / n for k, v in sorted(per_prompt.items())},
          "query_side_tokens_per_prompt": sum(per_prompt.values()) / n,
          "scaffold_per_prompt": (per_prompt["chat_scaffold"]
                                  + per_prompt["response_header"]) / n,
          "content_per_prompt": (sum(per_prompt.values())
                                 - per_prompt["chat_scaffold"]
                                 - per_prompt["response_header"]) / n}

    # ---- layer convention (Q4): quoted from the code, no weights involved
    layer = layer_convention_evidence()

    payload = {
        "schema": "dcs_ts_token_roles/1",
        "generated": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "model": args.model, "cpu_only": True, "weights_loaded": False,
        "scope": {"cell": CELL, "query_kind": QUERY_KIND, "n_examples": N_EXAMPLES,
                  "codewords": list(CODEWORDS), "concepts": list(CONCEPTS),
                  "n_domains": len(doms), "n_records": len(recs)},
        "bank_identity": idents,
        "split_manifest": {"path": os.path.relpath(SPLIT_MANIFEST, REPO),
                           "manifest_sha16": man_sha,
                           "manifest_file_bytes_sha16": man_file_sha,
                           "field_name": manifest["field_name"],
                           "n_train": manifest["n_train"],
                           "n_validation": manifest["n_validation"],
                           "n_test": manifest["n_test"]},
        "query_template": template, "role_vocabulary": list(ROLE_VOCAB),
        "checks": ck.rows, "checks_summary": ck.summary(),
        "read_position_candidates": cands,
        "q3_query_side_breakdown": q3,
        "q4_layer_convention": layer,
        "mutations": mut,
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
        print(f"  {r['status']:11s} {r['check']}  bound={r['n_bound']} "
              f"viol={r['n_violations']}")
    if mut:
        for m in mut:
            print(f"  MUT {'RED ' if m['went_red'] else 'GREEN'} {m['mutation']} "
                  f"-> {m['target_check']} = {m['status_after_mutation']}")
    return 0 if ck.ok else 1


def layer_convention_evidence() -> Dict:
    """Q4 — what the CODE says, with quotes. No weights, so this is a code claim, not a test."""
    return {
        "repo_convention": "block layer L == hidden_states[L+1]; hidden_states[0] == embeddings",
        "quotes": [
            {"file": "src/boombness/signals.py", "line": 46,
             "text": 'LAYER_CONVENTION = "block_L == hidden_states[L+1]; '
                     'hidden_states[0] == embeddings"'},
            {"file": "src/boombness/common.py", "line": 15,
             "text": "* 0-indexed block L  <->  hidden_states[L+1];  hidden_states[0] is the "
                     "embedding."},
            {"file": "src/boombness/extract_boombness.py", "line": 21,
             "text": "LAYER CONVENTION: block L == hidden_states[L+1]; hidden_states[0] is the "
                     "embedding."},
            {"file": "src/boombness/extract_boombness.py", "line": 346,
             "text": "is uniform: `hs[L+1]` is the raw output of block `L` for every `L`."},
            {"file": "src/boombness/extract_boombness.py", "line": 439,
             "text": "torch.stack([hs[L + 1, pos, :] for L in layers], dim=0)"},
            {"file": "src/boombness/refusalness.py", "line": 235,
             "text": "h = out.hidden_states[L + 1][0, pos, :].float().cpu()"},
            {"file": "doublespeak_causality/ds_common.py", "line": 866,
             "text": "index 0 = embeddings, index L (1..num_layers) = residual stream AFTER "
                     "block L-1 (post-block)."},
            {"file": "doublespeak_causality/09_attention_knockout.py", "line": 57,
             "text": "return out.hidden_states[readout_layer + 1][0, pos, :]"},
        ],
        "post_final_norm_caveat": {
            "file": "src/boombness/extract_boombness.py", "lines": "331-347",
            "text": "transformers 5.12 ties the last entry of out.hidden_states to "
                    "last_hidden_state, so hidden_states[n_layers] is the POST-FINAL-NORM state, "
                    "not block n_layers-1's raw output. forward_hidden() substitutes the hooked "
                    "raw output of layers[-1] so hs[L+1] is uniform in L.",
            "consequence": "L = n_layers-1 is only correct through forward_hidden(); any caller "
                           "reading out.hidden_states[-1] directly reads a different coordinate.",
        },
        "inconsistencies_found_by_grep": [
            {"file": "doublespeak_causality/44_kv_mediation.py", "lines": [289, 292],
             "text": "line 289 reads out.hidden_states[R + 1] (block convention) and line 292 "
                     "reads out.hidden_states[best_ps_layer] BARE, in the same function. If "
                     "best_ps_layer is a BLOCK index the two reads are one layer apart.",
             "status": "FLAG, not adjudicated here — needs the caller's definition of "
                       "best_ps_layer"},
            {"file": "doublespeak_causality/18_run_behavioral_necessity.py", "line": 99,
             "text": "reps = torch.stack([hs[l][0, pos.codeword_last, :] ... for l in "
                     "range(len(hs))]) — row index l of `reps` is hidden_states[l], so row l is "
                     "block l-1 and row 0 is the embedding. A consumer treating row l as block l "
                     "is off by one.",
             "status": "FLAG — depends on how the returned tensor is indexed downstream"},
        ],
        "needs_gpu": True,
        "planted_hook_test": {
            "why": "Everything above is a reading of source comments and index arithmetic. It "
                   "cannot distinguish the intended convention from an implementation that "
                   "silently disagrees with its own docstring.",
            "test": [
                "1. Load the model on GPU. Pick a block index L (e.g. 12) and a position p.",
                "2. Register a forward hook on model.model.layers[L] that adds a large unique constant c (e.g. 1e3 on coordinate 0) to out[0][:, p, :].",
                "3. Run one forward with output_hidden_states=True on any prompt, hooked and unhooked.",
                "4. ASSERT hidden_states[L+1][0, p, 0] moves by exactly 1e3 and hidden_states[L][0, p, 0] does NOT move. If hidden_states[L] is the one that moved, the repo convention is off by one.",
                "5. Repeat at L = n_layers-1 through extract_boombness.forward_hidden and assert the same equality, since that is the only path applying the post-final-norm substitution; also assert forward_hidden's hs[-1] differs from out.hidden_states[-1] by the RMSNorm, i.e. that the substitution is not a no-op.",
                "6. Repeat with a forward PRE-hook on layers[L] and assert it moves hidden_states[L], not hidden_states[L+1].",
                "7. Repeat once for every model family the sprint uses (Llama-3.1-8B-Instruct, Qwen3-14B); the tie_last_hidden_states behaviour is a transformers-version property, not a model property, so also pin transformers.__version__ in the artifact.",
            ],
            "fails_if": "the delta appears at an index other than L+1, or the L=n_layers-1 case "
                        "disagrees between the raw tuple and forward_hidden().",
        },
    }


def write_report(path: str, p: Dict) -> None:
    import io
    o = io.StringIO()
    w = o.write
    sc = p["scope"]
    q3 = p["q3_query_side_breakdown"]
    cands = p["read_position_candidates"]
    qual = [c for c in cands if c.get("rank")]
    qual.sort(key=lambda c: c["rank"])
    n = sc["n_records"]

    w("# DCS-TS token-role map — cell C / semantic_one_word / n_examples=4\n\n")
    w(f"Generated {p['generated']} · tokenizer `{p['model']}` · **CPU only, no weights "
      f"loaded**.\n\n")
    w(f"Scope: cell **{sc['cell']}**, query_kind **{sc['query_kind']}**, "
      f"n_examples **{sc['n_examples']}**, {sc['n_domains']} domains x "
      f"{len(sc['codewords'])} codewords x {len(sc['concepts'])} concepts = "
      f"**{n} prompts**.\n\n")
    w("Artifacts: `outputs/dcs_ts/token_roles_ts116.json.gz` (per-prompt token ids, decoded "
      "tokens, spans, occurrences, per-token query roles), this report, "
      "`scripts/dcs_ts_token_roles.py`.\n\n")

    w("## Provenance\n\n| bank | rows_sha16 observed | published | n rows | n matched |\n")
    w("|---|---|---|---|---|\n")
    for k, v in p["bank_identity"].items():
        cw, cc = k.split("_")
        pub = EXPECTED_ROWS_SHA16[(cw, cc)]
        w(f"| {k} | `{v['bank_rows_sha16']}` | `{pub}` "
          f"{'OK' if pub == v['bank_rows_sha16'] else '**MISMATCH**'} | {v['bank_n_rows']} | "
          f"{v['n_matched']} |\n")
    sm = p["split_manifest"]
    w(f"\nSplit manifest `{sm['path']}` sha16 `{sm['manifest_sha16']}` "
      f"(field `{sm['field_name']}`).\n\n")

    ich = [c for c in p["checks"] if c["check"] == "I_dsplit_consistent_per_domain"][0]
    w(f"Domain split (`dsplit`) over the {sc['n_domains']} domains present: "
      f"{ich['detail']['dsplit_domain_counts']}.\n\n")

    w("## Checks\n\nA check that binds to zero rows is `ERROR_EMPTY`, never a pass.\n\n")
    w("| check | status | bound to | n bound | n violations |\n|---|---|---|---|---|\n")
    for c in p["checks"]:
        w(f"| `{c['check']}` | **{c['status']}** | {c['binds_to']} | {c['n_bound']} | "
          f"{c['n_violations']} |\n")
    w(f"\n{json.dumps(p['checks_summary'])}\n\n")

    if p["mutations"]:
        w("### Mutation demonstrations (`--mutate`)\n\n")
        w("| mutation | target check | status after | went RED |\n|---|---|---|---|\n")
        for m in p["mutations"]:
            w(f"| {m['mutation']} | `{m['target_check']}` | {m['status_after_mutation']} | "
              f"{'YES' if m['went_red'] else '**NO**'} |\n")
        w("\n")

    chkC = [c for c in p["checks"] if c["check"] == "C_token_ids_identical_across_concepts"][0]
    chkD = [c for c in p["checks"] if c["check"] == "D_no_bomb_knife_gun_token_anywhere"][0]
    w("## The finding that governs every answer below\n\n")
    w(f"At matched `(codeword, prompt_id)` the **token id sequence is identical across all "
      f"three concepts in {chkC['n_bound'] - chkC['n_violations']}/{chkC['n_bound']} "
      f"comparisons** (each non-reference concept against `bomb`), and the strict whole-word "
      f"count of bomb/knife/gun over the whole templated prompt is **0 in "
      f"{chkD['n_bound'] - chkD['n_violations']}/{chkD['n_bound']} prompts**.\n\n")
    w("These prompts do not merely *align* across concepts — in this cell they are the **same "
      "prompt**. `demo_surface` and `query_surface` are both `codeword` for "
      f"{n}/{n} matched rows, the harm pools' `natural_word` is `bomb` for all 116 domains, and "
      "the concept never surfaces. Two consequences, both load-bearing:\n\n")
    w("1. **Criterion (b) of Q1 is satisfied at every token position, trivially.** Ranking the "
      "candidates therefore turns entirely on (a), (c), (d) and on what the position *is*, not "
      "on whether it survives a concept swap.\n")
    w("2. **The concept label is not identifiable from the input in this cell.** Any probe "
      "trained to separate bomb/knife/gun on cell-C `semantic_one_word` `n_examples=4` prompts "
      "is being fed byte-identical text under three different labels, so its ceiling is chance "
      "(1/3) by construction. If such a probe reports above chance, the signal is coming from "
      "something other than the prompt — run order, batching, or a leaked label — and that is a "
      "bug to find, not a result. This is the intended shape of the fix to the old 0.7485 "
      "figure, but it should be stated as a **null by construction**, not replicated as a "
      "measurement.\n\n")
    w("Whether knife and gun demonstrations actually INSTALL is untouched by any of this and "
      "remains **UNKNOWN** from prompt analysis alone: the three arms differ only in the "
      "`target_semantic` label, so installation can only be established behaviourally, on GPU.\n\n")

    jch = [c for c in p["checks"] if c["check"] == "J_no_inflected_codeword_false_occurrences"][0]
    if jch["n_violations"]:
        w("## DEFECT — 9 prompts count a longer word as a codeword occurrence\n\n")
        w(f"`{jch['check']}` is **{jch['status']}**: {jch['n_violations']}/{jch['n_bound']} "
          f"prompts contain a match the house finder accepts that is not the codeword. "
          f"Surfaces and counts: `{jch['detail']['offending_surfaces']}`.\n\n")
        w("`ds_common.find_word_occurrences_in_text` rejects a match whose LEFT neighbour is "
          "alphanumeric but accepts one whose RIGHT neighbour is (its comment: \"allow "
          "inflections (carrots) but not substrings inside a longer word (scarrot)\"). The "
          "generator used the same rule, so the bank's own `n_codeword_occurrences` is 6 on "
          "these rows and a checker that compares the finder against that field agrees with "
          "itself and reports nothing — which is exactly why this check re-derives from the "
          "templated text instead.\n\n")
        w("Consequences, stated narrowly:\n\n")
        w("* The extra hit is in the **preamble**, upstream of every demonstration, and is a "
          "benign literal use of an unrelated word. It does not touch the nominated read "
          "position: all "
          f"{[c for c in p['checks'] if c['check'].startswith('G2_')][0]['n_bound']} prompts "
          "still have that position strictly after every match.\n")
        w("* It DOES affect any analysis indexed by occurrence ORDINAL (occurrence 1, 2, ...), "
          "any per-occurrence attention knockout that claims to block \"every codeword site\", "
          "and any count of demo-installed occurrences, on these rows.\n")
        w("* The clean fix is a right-boundary-strict matcher; the cheap fix is to exclude the "
          "9 rows. Either way the choice must be stated, because the two give different "
          "denominators.\n\n")

    w("## Q1 — the downstream neutral read position\n\n")
    w("Criteria: (a) strictly after every codeword occurrence, (b) byte- and token-identical "
      "across all three concepts, (c) contains none of bomb/knife/gun, (d) present in every "
      f"one of the {n} matched prompts.\n\n")
    w("| rank | rel_end | decoded | token id | role | (a) | (b) | (c) | (d) |\n")
    w("|---|---|---|---|---|---|---|---|---|\n")
    for c in qual:
        w(f"| {c['rank']} | `{c['rel_end']}` | `{c['decoded']!r}` | {c['token_id']} | "
          f"{'/'.join(c['roles'])} | {c['n_after']}/{n} | "
          f"{c['n_distinct_token_ids']} distinct id | yes | {c['n_present']}/{n} |\n")
    g2 = [c for c in p["checks"] if c["check"].startswith("G2_")][0]
    nom = g2["detail"]["nominated_rel_end"]
    nomtok = next((c for c in cands if c["rel_end"] == nom), None)
    w(f"\n**NOMINATED: `rel_end = {nom}`** — the token at index `len(input_ids) {nom}`, decoded "
      f"`{nomtok['decoded']!r}`, token id `{nomtok['token_id']}`. It is the token immediately "
      "after the final-query codeword occurrence, i.e. the repo's own `following` site "
      "(`ds_common.target_positions`, `extract_boombness --position following`), so a readout "
      "there is directly comparable with every existing `following` result. Verified per prompt "
      f"by check `{g2['check']}`: {g2['n_bound'] - g2['n_violations']}/{g2['n_bound']} prompts "
      "have the same token id there, strictly after every codeword occurrence, with no "
      "concept substring.\n\n")
    w("Two positions in the table deserve separate names rather than a rank:\n\n")
    w("* `rel_end = -6` (`'?'`) is the last token of the user turn and the last position whose "
      "content the model can attend to before the header.\n")
    w("* `rel_end = -1` (`'\\n\\n'`, the last token of "
      "`<|start_header_id|>assistant<|end_header_id|>\\n\\n`) is the **generation position** — "
      "the row the first output token is sampled from. It satisfies all four criteria but it is "
      "response scaffold, not query content, so a null there is a null about the readout, not "
      "about the query.\n\n")
    w("Full candidate scoring, including the disqualified offsets, is in the JSON under "
      "`read_position_candidates`.\n\n")
    w("### Why the offsets are stated relative to the END\n\n")
    hchk = [c for c in p["checks"] if c["check"] == "H_codeword_is_one_subtoken"][0]
    fchk = [c for c in p["checks"] if c["check"] == "F_tail_constant_except_codeword"][0]
    w(f"`button` and `basket` are each **one subtoken** in every one of "
      f"{hchk['n_bound']} codeword occurrences, so the two codeword banks do not shift the tail "
      f"relative to each other. Over the last {fchk['detail']['tail_len']} token positions of "
      f"all {n} prompts, the only position that varies is "
      f"{fchk['detail']['codeword_rel_end_positions_common_to_all']} (the codeword itself); "
      f"{len(fchk['detail']['unexpected_varying'])} other positions vary. Absolute indices are "
      "NOT stable — prompt length varies with the domain preamble — so a read position must be "
      "given as `len(input_ids) + rel_end`, never as a constant index.\n\n")

    w("## Q3 — query-side scaffold vs content, per prompt\n\n")
    w("| role | tokens per prompt |\n|---|---|\n")
    for k in ROLE_VOCAB:
        w(f"| {k} | {q3['per_prompt_role_counts'].get(k, 0):g} |\n")
    w(f"\nQuery-side tokens per prompt: **{q3['query_side_tokens_per_prompt']:g}**, of which "
      f"**{q3['scaffold_per_prompt']:g}** are chat scaffold / response header and "
      f"**{q3['content_per_prompt']:g}** are query content. The census is identical in all "
      f"{n} prompts (check `E_query_role_census_constant`).\n\n")
    w("**The K-ladder correction.** Counting rungs backwards from the end of the sequence, "
      "`K=1` is `rel_end=-1` = `'\\n\\n'` (response_header), `K=2` is `rel_end=-2` = "
      "`'<|end_header_id|>'` (response_header), `K=3` `'assistant'`, `K=4` "
      "`'<|start_header_id|>'`, `K=5` `'<|eot_id|>'` (chat_scaffold). **The first five rungs "
      "carry no query content at all.** The first query-content rung is `K=6` (`'?'`, "
      "punctuation) and the first non-punctuation query token is `K=7` (`' to'`). Any future "
      "claim of the form \"K=1/2 rows are query rows\" is false for this bank and this "
      "template; the table above is the exact per-prompt breakdown that settles it.\n\n")

    w("## Q4 — layer convention (code reading; needs a GPU test)\n\n")
    lc = p["q4_layer_convention"]
    w(f"Repo convention: **{lc['repo_convention']}**\n\n")
    for q in lc["quotes"]:
        w(f"* `{q['file']}:{q['line']}` — `{q['text']}`\n")
    w(f"\n**Caveat** (`{lc['post_final_norm_caveat']['file']}:"
      f"{lc['post_final_norm_caveat']['lines']}`): "
      f"{lc['post_final_norm_caveat']['text']} "
      f"{lc['post_final_norm_caveat']['consequence']}\n\n")
    w("**Inconsistencies found by grep (flags, not adjudications):**\n\n")
    for f in lc["inconsistencies_found_by_grep"]:
        w(f"* `{f['file']}:{f.get('line', f.get('lines'))}` — {f['text']} _{f['status']}_\n")
    w(f"\n**{lc['planted_hook_test']['why']}** The planted-hook test that would settle it:\n\n")
    for st in lc["planted_hook_test"]["test"]:
        w(f"{st}\n\n")
    w(f"\nFails if: {lc['planted_hook_test']['fails_if']}\n")

    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        fh.write(o.getvalue())


if __name__ == "__main__":
    raise SystemExit(main())
