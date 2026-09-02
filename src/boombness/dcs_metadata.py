"""dcs_metadata.py -- DCS phase, P1 (plan Sec 3 + Sec 4): concept metadata backfill as a SIDECAR,
plus the structural prompt audit, as mechanical assertions over structure only.

=============================================================================================
WHY A SIDECAR AND NOT NEW BANK FIELDS
=============================================================================================
The P0 audit (reports/DCS_P0_AUDIT_BRIEF.md Sec 2) is explicit: adding keys to a bank row
unconditionally breaks `tests/test_bank_regenerates_byte_identically.py` AND changes
`bank_rows_sha16`, which every result-to-bank join in this repo is keyed on. Adding them
conditionally (the `prompt_families.py:530-543` pattern) avoids the byte-identity break but still
requires regenerating 14k rows and re-hashing every downstream artifact.

Neither is necessary. Everything Sec 1.3 asks for is a FUNCTION of the row plus two bank-level
files (`*_meta.json`, the pools JSON) plus one code table (`prompt_families.QUERY_KINDS`). So this
module emits a **sidecar table**, one row per bank row, joinable on the phase's mandated join key
`(bank_file_sha16, prompt_id)` and carrying `prompt_sha16` so a stale join is detectable. The banks
are never opened for writing. `prompt_families.py` is never modified.

=============================================================================================
WHAT IS DERIVED, WHAT IS DEFINED  (plan Sec 1.3 -- implemented, not re-litigated)
=============================================================================================
DERIVED (alias or pure function of committed data):
    surface_word        := row['target_surface']
    surface_kind        := row['query_surface']            (demo twin: demo_surface_kind)
    harmful_concept     := row['concept'],  ASSERTED == row['target_semantic']
    benign_concept      := pools['pools'][f"{demo_pool_domain}|benign"]['natural_word'] out of the
                           pools file named by the bank's *_meta.json['pools_path'].  NOT row-local.
    query_template_id   := sha16(QUERY_KINDS[query_kind]['template'])   (template_id is its alias)

DEFINED BY THIS PHASE (0 hits repo-wide before it; the plan says so and so does this file):
    lexical_bank        := f"{codeword}_{concept}".  `pools_sha16` stays a SEPARATE field, because
                           `ticket_knife` and `38dom` share pools_sha16=4cfc70c8688e4a3a while
                           differing in pair -- the two identities are not interchangeable.
    context_kind        := demo_valence in {benign, harmful}.  The bank spells the harmful level
                           'harm'; the mapping is the one-line table CONTEXT_KIND_MAP below and it
                           is total on {benign, harm} and undefined elsewhere -- 'mixed' and
                           'remap' are NOT silently folded into either level, they are marked
                           ambiguous and excluded by rule AMB-CONTEXT.
    demo_template_id    := sha16 of (demo_pool_domain, demo_valence, split, family_slot,
                           n_examples, pools_sha16)
    request_id          := (run_id, prompt_id, arm) -- constructible only for runs this phase
                           produces. For an existing BANK there is no run and no arm, so it is
                           emitted as null with request_id_status='ABSENT_NO_RUN_CONTEXT'.
                           It is never invented.

=============================================================================================
AMBIGUITY IS MECHANICAL (plan Sec 1.3, "backfill is mechanical or it is nothing")
=============================================================================================
Every exclusion is a named rule in AMBIGUITY_RULES, evaluated on every row of every bank in the
same order, before any audit outcome is computed. A row that trips one gets ambiguous=true, the
list of rule ids in `ambiguous_reasons`, and null in the field(s) that rule governs. Nothing is
excluded by hand and nothing is excluded after seeing a result. The attrition/composition table
is an artifact (`attrition.json`, printed to stdout), not a sentence.

=============================================================================================
THE SEC 4 STRUCTURAL AUDIT -- STRUCTURE ONLY
=============================================================================================
No prompt text is read, printed, logged or hashed into anything human-readable. Prompt strings are
touched in exactly three ways: (1) hashed, (2) length-measured, (3) passed through
`prompt_families._substitute` / `_char_spans` to produce a hash or a count. Every audit verdict is
a boolean over hashes and integers.

  AUD-SURFACE     A and C carry the same surface codeword; E and B carry the explicit concept word.
  AUD-ALIGN       A/E aligned under benign demonstrations, C/B aligned under harmful ones --
                  delegated to `prompt_families.check_alignment`, the bank's own invariant checker
                  (its two pairs are exactly E->A and B->C), so the audit cannot drift from the
                  generator's definition of "aligned".
  AUD-CONTRAST    the intended contrast changes only the intended factor:
                    context contrast (A|C, E|B): final_query_text sha EQUAL, demo_block sha DIFFER
                    surface contrast (A|E, C|B): masked-prompt sha EQUAL
                  where masked-prompt = full_prompt with BOTH codeword and concept mapped to a
                  placeholder by the house case-aware substituter.
  AUD-OCCUR       codeword / concept / target occurrences RE-DERIVED from full_prompt and compared
                  to the row's own counts (standing rule 8: a verifier must not read the producer's
                  own field), then compared against `n_occurrences` in matching
                  extract_boombness results.jsonl runs where one exists.
  AUD-CROSSBANK   *** the load-bearing one *** for the same prompt_id, cells B and E are
                  BYTE-IDENTICAL across lexical banks, because those cells contain no codeword.
                  Counted exactly, broken out by cell x query_kind x n_examples, for
                  button_bomb vs basket_bomb (and the cds38_* pair). This bounds what the P6
                  lexical replication can claim: B and E are SHARED, not independent.

`--self-test` runs a mutation harness: each audit family is fed a deliberately corrupted copy and
must go RED. A verifier that has never been observed failing is not a verifier.

Reads: bank jsonl, bank *_meta.json, the pools json, prompt_families' tables, and (optionally)
extract_boombness results.jsonl. Writes: one RunDir under outputs/boombness/dcs_meta/. No GPU, no
model, no network, no bank mutation.
"""
from __future__ import annotations

import argparse
import collections
import glob
import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import common                                        # noqa: E402
import prompt_families as pf                         # noqa: E402

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BANK_DIR = os.path.join(REPO_ROOT, "data", "boombness_prompts")

#: The bank spells the harmful demonstration level 'harm'. Sec 1.3 defines `context_kind` over
#: {benign, harmful}. This table is the whole definition; it is TOTAL on the two levels the 2x2
#: uses and DELIBERATELY PARTIAL elsewhere -- 'mixed' (the consistency arm) and 'remap' (cell F)
#: are neither benign nor harmful demonstrations of the target mapping, and folding them into
#: either level would be a judgement call wearing a derivation's clothes.
CONTEXT_KIND_MAP = {"benign": "benign", "harm": "harmful"}

#: Placeholder for the masked-prompt hash. Chosen to be a word `_substitute` will not collide with.
MASK_TOKEN = "Wzzz"

CORE_2X2 = tuple(pf.CORE_2X2)                        # 4 condition names
COND_TO_CELL = {c: pf.CONDITIONS[c]["cell"] for c in pf.CONDITIONS}
CELL_TO_COND = {v: k for k, v in COND_TO_CELL.items() if k in CORE_2X2}

DEFAULT_BANKS = ["button_bomb", "basket_bomb", "cds38_button_bomb", "cds38_basket_bomb"]


# --------------------------------------------------------------------------- #
# hashing / io helpers
# --------------------------------------------------------------------------- #
def sha16(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()[:16]


def file_sha16(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def mask_prompt(text: str, codeword: str, concept: str) -> str:
    """full_prompt with BOTH lexical items replaced by one placeholder, case-aware.

    Uses the generator's own `_substitute` (prompt_families:352) so the masking follows exactly the
    same casing/article rules the prompts were BUILT with. Reimplementing it here is how an audit
    ends up testing its own regex instead of the corpus (`feedback_matcher_scope_bug_class`).
    """
    out = pf._substitute([text], concept, MASK_TOKEN)[0]
    out = pf._substitute([out], codeword, MASK_TOKEN)[0]
    return out


# --------------------------------------------------------------------------- #
# Ambiguity rules -- declared as running code, before any outcome (standing rule 5)
# --------------------------------------------------------------------------- #
#: (rule_id, predicate(row, ctx) -> True when the row IS ambiguous, [fields it nulls])
AMBIGUITY_RULES = [
    ("AMB-SURFACE-EMPTY",
     lambda r, c: not str(r.get("target_surface") or "").strip(),
     ["surface_word"]),
    ("AMB-SURFACE-KIND",
     lambda r, c: r.get("query_surface") not in ("codeword", "concept"),
     ["surface_kind"]),
    ("AMB-CONCEPT-DISAGREE",
     lambda r, c: r.get("concept") != r.get("target_semantic"),
     ["harmful_concept"]),
    ("AMB-BANK-PAIR-DISAGREE",
     lambda r, c: (r.get("codeword") != c["meta_codeword"]
                   or r.get("concept") != c["meta_concept"]),
     ["lexical_bank"]),
    ("AMB-CONTEXT",
     lambda r, c: r.get("demo_valence") not in CONTEXT_KIND_MAP,
     ["context_kind"]),
    ("AMB-BENIGN-CONCEPT",
     lambda r, c: (f"{r.get('demo_pool_domain')}|benign") not in c["pools"],
     ["benign_concept"]),
    ("AMB-QUERY-TEMPLATE",
     lambda r, c: r.get("query_kind") not in pf.QUERY_KINDS,
     ["query_template_id", "template_id"]),
]


def derive_row(row: dict, ctx: dict) -> dict:
    """The whole of Sec 1.3, as a pure function of (row, bank context). No I/O, no state."""
    reasons, nulled = [], set()
    for rid, pred, fields in AMBIGUITY_RULES:
        if pred(row, ctx):
            reasons.append(rid)
            nulled.update(fields)

    qk = row.get("query_kind")
    qspec = pf.QUERY_KINDS.get(qk) or {}
    demo_dom = row.get("demo_pool_domain")
    benign_pool = ctx["pools"].get(f"{demo_dom}|benign") or {}

    out = {
        # -- identity / join keys (plan Sec 1.9: join on (bank_file_sha16, prompt_id)) ----------
        "bank_stem": ctx["stem"],
        "bank_path": ctx["bank_path"],
        "bank_file_sha16": ctx["bank_file_sha16"],
        "bank_rows_sha16": ctx["bank_rows_sha16"],
        "prompt_id": row.get("prompt_id"),
        "prompt_sha16": row.get("prompt_sha16"),
        # -- Sec 1.3 field set ------------------------------------------------------------------
        "surface_word": row.get("target_surface"),
        "surface_kind": row.get("query_surface"),
        "demo_surface_kind": row.get("demo_surface"),
        "harmful_concept": row.get("concept"),
        "benign_concept": benign_pool.get("natural_word"),
        "lexical_bank": f"{row.get('codeword')}_{row.get('concept')}",
        "pools_sha16": ctx["pools_sha16"],
        "context_kind": CONTEXT_KIND_MAP.get(row.get("demo_valence")),
        "template_id": sha16(str(qspec.get("template"))) if qspec else None,
        "query_template_id": sha16(str(qspec.get("template"))) if qspec else None,
        "demo_template_id": sha16("|".join(str(x) for x in (
            demo_dom, row.get("demo_valence"), row.get("split"),
            row.get("family_slot"), row.get("n_examples"), ctx["pools_sha16"]))),
        "request_id": None,
        "request_id_status": "ABSENT_NO_RUN_CONTEXT",
        # -- passthrough axes the analyses group on (copied, not re-derived) --------------------
        "family_id": row.get("family_id"),
        "family_slot": row.get("family_slot"),
        "domain": row.get("domain"),
        "demo_pool_domain": demo_dom,
        "split": row.get("split"),
        "condition": row.get("condition"),
        "cell": row.get("cell"),
        "query_kind": qk,
        "n_examples": row.get("n_examples"),
        "n_demos_emitted": row.get("n_demos_emitted"),
        "strength": row.get("strength"),
        "consistency": row.get("consistency"),
        "example_position": row.get("example_position"),
        "role_style": row.get("role_style"),
        "bank_block": row.get("bank_block"),
        "codeword": row.get("codeword"),
        "concept": row.get("concept"),
        "occurrence_analysis_safe": row.get("occurrence_analysis_safe"),
        "scores": row.get("scores"),
        # -- structure-only measurements of the opaque prompt blob ------------------------------
        "n_chars": row.get("n_chars"),
        "prompt_len_chars_recomputed": len(row.get("full_prompt") or ""),
        "query_sha16": sha16(row.get("final_query_text") or ""),
        "demo_block_sha16": sha16(row.get("demo_block") or ""),
        "demo_block_empty": not (row.get("demo_block") or ""),
        "masked_prompt_sha16": sha16(mask_prompt(row.get("full_prompt") or "",
                                                 str(row.get("codeword") or MASK_TOKEN),
                                                 str(row.get("concept") or MASK_TOKEN))),
        # -- membership -------------------------------------------------------------------------
        "in_core_2x2": row.get("condition") in CORE_2X2,
        # STRUCTURAL HAZARD FLAG, not an exclusion by itself. A concept-surface cell (B/E) whose
        # query kind does NOT deliberately name the codeword, yet whose prompt still contains the
        # codeword as a substring, is an INCIDENTAL lexical collision (e.g. `basket` inside the
        # `school_campus` vocabulary). This is the class that trips `occurrence_count_mismatch` and
        # VOIDs intervention arms mid-run. Emitted as a candidate exclusion list so the next run
        # can declare it in EVERY arm up front via --exclude-prompt-ids, baseline included.
        "incidental_codeword_in_concept_cell": bool(
            row.get("cell") in ("B", "E")
            and row.get("occurrence_analysis_safe", True)
            and (row.get("n_codeword_occurrences") or 0) > 0),
        "ambiguous": bool(reasons),
        "ambiguous_reasons": reasons,
    }
    for f in nulled:
        out[f] = None
    return out


# --------------------------------------------------------------------------- #
# bank loading
# --------------------------------------------------------------------------- #
def load_bank(stem: str) -> dict:
    bank_path = os.path.join(BANK_DIR, f"boombness_prompt_bank_{stem}.jsonl")
    meta_path = os.path.join(BANK_DIR, f"boombness_prompt_bank_{stem}_meta.json")
    if not os.path.exists(bank_path):
        return {"stem": stem, "present": False, "bank_path": bank_path}
    meta = json.load(open(meta_path)) if os.path.exists(meta_path) else {}

    pools_path = meta.get("pools_path") or ""
    if pools_path and not os.path.isabs(pools_path):
        pools_path = os.path.join(REPO_ROOT, pools_path)
    pools_obj, pools_present = {}, os.path.exists(pools_path)
    if pools_present:
        pools_obj = json.load(open(pools_path))

    rows = [json.loads(l) for l in open(bank_path) if l.strip()]
    ctx = {
        "stem": stem,
        "present": True,
        "bank_path": os.path.abspath(bank_path),
        "meta_path": meta_path if os.path.exists(meta_path) else None,
        "bank_file_sha16": file_sha16(bank_path),
        "bank_rows_sha16": common.rows_sha16(
            [(str(r["prompt_id"]), str(r["prompt_sha16"])) for r in rows]),
        "bank_rows_sha16_claimed": (meta.get("stats") or {}).get("bank_rows_sha16"),
        "meta_codeword": meta.get("codeword"),
        "meta_concept": meta.get("concept"),
        "preset": meta.get("preset"),
        "seed": meta.get("seed"),
        "pools_path": pools_path or None,
        "pools_present": pools_present,
        "pools_sha16": meta.get("pools_sha16"),
        "pools_sha16_recomputed": ((pools_obj.get("_meta") or {}).get("content_sha16")
                                   if pools_present else None),
        "pools": (pools_obj.get("pools") or {}) if pools_present else {},
        "rows": rows,
        "n_rows": len(rows),
    }
    return ctx


# --------------------------------------------------------------------------- #
# Sec 4 audit -- per bank
# --------------------------------------------------------------------------- #
def audit_bank(ctx: dict, meta_rows: list) -> dict:
    """Every check is a boolean over hashes / integers. No prompt text leaves this function."""
    rows = ctx["rows"]
    by_pid = {r["prompt_id"]: r for r in rows}
    mrow = {m["prompt_id"]: m for m in meta_rows}
    codeword, concept = ctx["meta_codeword"], ctx["meta_concept"]

    # ---- AUD-OCCUR : re-derive from full_prompt, never trust the row's own counts -------------
    occ = {"n_checked": 0, "codeword_mismatch": 0, "concept_mismatch": 0,
           "target_mismatch": 0, "mismatch_ids": []}
    for r in rows:
        full = r["full_prompt"]
        n_code = full.lower().count(str(codeword).lower())
        n_conc = full.lower().count(str(concept).lower())
        n_tgt = len(pf._char_spans(full, str(r["target_surface"]))) if r["target_surface"] else 0
        occ["n_checked"] += 1
        bad = False
        if n_code != r["n_codeword_occurrences"]:
            occ["codeword_mismatch"] += 1; bad = True
        if n_conc != r["n_concept_occurrences"]:
            occ["concept_mismatch"] += 1; bad = True
        if n_tgt != r["n_target_occurrences"]:
            occ["target_mismatch"] += 1; bad = True
        if bad and len(occ["mismatch_ids"]) < 20:
            occ["mismatch_ids"].append(r["prompt_id"])
    occ["pass"] = (occ["codeword_mismatch"] == 0 and occ["concept_mismatch"] == 0
                   and occ["target_mismatch"] == 0)

    # ---- family-level checks over complete core 2x2 families ---------------------------------
    fams = collections.defaultdict(dict)
    for r in rows:
        if r["condition"] in CORE_2X2:
            fams[r["family_id"]][r["condition"]] = r

    surface = {"n_families": 0, "A_C_same_codeword": 0, "E_B_same_concept": 0, "violations": []}
    align = {"n_families": 0, "clean": 0, "violation_kinds": collections.Counter()}
    contrast = {"n_families": 0,
                "ctx_query_identical_AC": 0, "ctx_query_identical_EB": 0,
                "ctx_demo_differs_AC": 0, "ctx_demo_differs_EB": 0,
                "ctx_demo_degenerate_zero_demo_AC": 0, "ctx_demo_degenerate_zero_demo_EB": 0,
                "surf_masked_identical_AE": 0, "surf_masked_identical_CB": 0,
                "query_template_id_uniform": 0,
                "violations": []}
    n_incomplete = 0
    for fid, d in fams.items():
        if len(d) != 4:
            n_incomplete += 1
            continue
        A, B, C, E = (d[CELL_TO_COND[x]] for x in ("A", "B", "C", "E"))
        mA, mB, mC, mE = (mrow[x["prompt_id"]] for x in (A, B, C, E))

        # AUD-SURFACE
        surface["n_families"] += 1
        ok_ac = (str(A["target_surface"]).casefold() == str(codeword).casefold()
                 and str(C["target_surface"]).casefold() == str(codeword).casefold())
        ok_eb = (str(E["target_surface"]).casefold() == str(concept).casefold()
                 and str(B["target_surface"]).casefold() == str(concept).casefold())
        surface["A_C_same_codeword"] += int(ok_ac)
        surface["E_B_same_concept"] += int(ok_eb)
        if not (ok_ac and ok_eb) and len(surface["violations"]) < 20:
            surface["violations"].append({"family_id": fid, "A_C": ok_ac, "E_B": ok_eb})

        # AUD-ALIGN -- delegated to the generator's own invariant checker
        align["n_families"] += 1
        bad = pf.check_alignment(d, str(codeword), str(concept))
        if not bad:
            align["clean"] += 1
        for b in bad:
            align["violation_kinds"][b.split(":")[0]] += 1

        # AUD-CONTRAST
        contrast["n_families"] += 1
        contrast["query_template_id_uniform"] += int(
            len({m["query_template_id"] for m in (mA, mB, mC, mE)}) == 1)
        for tag, lo, hi, mlo, mhi in (("AC", A, C, mA, mC), ("EB", E, B, mE, mB)):
            contrast[f"ctx_query_identical_{tag}"] += int(mlo["query_sha16"] == mhi["query_sha16"])
            if mlo["demo_block_empty"] and mhi["demo_block_empty"]:
                contrast[f"ctx_demo_degenerate_zero_demo_{tag}"] += 1
            elif mlo["demo_block_sha16"] != mhi["demo_block_sha16"]:
                contrast[f"ctx_demo_differs_{tag}"] += 1
        for tag, mlo, mhi in (("AE", mA, mE), ("CB", mC, mB)):
            same = mlo["masked_prompt_sha16"] == mhi["masked_prompt_sha16"]
            contrast[f"surf_masked_identical_{tag}"] += int(same)
            if not same and len(contrast["violations"]) < 20:
                contrast["violations"].append({"family_id": fid, "pair": tag})

    n = surface["n_families"]
    return {
        "n_core_2x2_families_seen": len(fams),
        "n_core_2x2_families_incomplete": n_incomplete,
        "n_core_2x2_families_complete": n,
        "AUD_SURFACE": {**surface, "pass": n > 0 and surface["A_C_same_codeword"] == n
                        and surface["E_B_same_concept"] == n},
        "AUD_ALIGN": {"n_families": align["n_families"], "clean": align["clean"],
                      "violation_kinds": dict(align["violation_kinds"]),
                      "pass": align["n_families"] > 0 and align["clean"] == align["n_families"]},
        "AUD_CONTRAST": {**contrast, "pass": n > 0 and all(
            contrast[k] == n for k in ("ctx_query_identical_AC", "ctx_query_identical_EB",
                                       "surf_masked_identical_AE", "surf_masked_identical_CB",
                                       "query_template_id_uniform"))},
        "AUD_OCCUR_selfderived": occ,
        "_by_pid": by_pid,
    }


# --------------------------------------------------------------------------- #
# AUD-OCCUR against an external results.jsonl (where one exists)
# --------------------------------------------------------------------------- #
def occurrence_crosscheck(ctx: dict, run_globs: list) -> list:
    """Compare `n_occurrences` in extract_boombness result rows to the bank's own occurrence count.

    The join is attested, not assumed: the run's metadata.json must name THIS bank file, and every
    result row carries `prompt_sha16`, which must equal the bank row's. `prompt_id` alone collides
    across lexical banks (plan Sec 1.9), so a prompt_id-only join here would silently compare the
    wrong bank.
    """
    out = []
    seen = set()
    for g in run_globs:
        for meta_path in sorted(glob.glob(g)):
            run_dir = os.path.dirname(meta_path)
            res = os.path.join(run_dir, "results.jsonl")
            if run_dir in seen or not os.path.exists(res):
                continue
            try:
                m = json.load(open(meta_path))
            except Exception:
                continue
            argv = m.get("argv") or []
            bank_arg = ""
            for i, a in enumerate(argv):
                if a == "--bank" and i + 1 < len(argv):
                    bank_arg = argv[i + 1]
            if os.path.basename(bank_arg) != os.path.basename(ctx["bank_path"]):
                continue
            seen.add(run_dir)

            rec = {"run_dir": os.path.relpath(run_dir, REPO_ROOT),
                   "run_bank_file_sha16": m.get("bank_file_sha16"),
                   "run_bank_rows_sha16": m.get("bank_rows_sha16"),
                   "bank_file_sha16": ctx["bank_file_sha16"],
                   "bank_rows_sha16": ctx["bank_rows_sha16"],
                   "n_result_rows": m.get("n_result_rows"),
                   "n_joined": 0, "n_sha_mismatch": 0, "n_no_such_prompt_id": 0,
                   "n_occ_field_absent": 0, "n_occ_agree": 0, "n_occ_disagree": 0,
                   "n_skipped_occurrence_unsafe": 0, "disagree_ids": []}
            by_pid = {r["prompt_id"]: r for r in ctx["rows"]}
            with open(res) as f:
                for line in f:
                    if not line.strip():
                        continue
                    rr = json.loads(line)
                    pid = rr.get("prompt_id")
                    br = by_pid.get(pid)
                    if br is None:
                        rec["n_no_such_prompt_id"] += 1
                        continue
                    if rr.get("prompt_sha16") and rr["prompt_sha16"] != br["prompt_sha16"]:
                        rec["n_sha_mismatch"] += 1
                        continue
                    rec["n_joined"] += 1
                    if "n_occurrences" not in rr:
                        rec["n_occ_field_absent"] += 1
                        continue
                    if not br.get("occurrence_analysis_safe", True):
                        rec["n_skipped_occurrence_unsafe"] += 1
                        continue
                    if int(rr["n_occurrences"]) == int(br["n_target_occurrences"]):
                        rec["n_occ_agree"] += 1
                    else:
                        rec["n_occ_disagree"] += 1
                        if len(rec["disagree_ids"]) < 20:
                            rec["disagree_ids"].append(pid)
            rec["pass"] = (rec["n_sha_mismatch"] == 0 and rec["n_occ_disagree"] == 0
                           and rec["n_occ_agree"] > 0)
            out.append(rec)
    return out


# --------------------------------------------------------------------------- #
# AUD-CROSSBANK : the B/E byte-identity count
# --------------------------------------------------------------------------- #
def crossbank_identity(c1: dict, c2: dict) -> dict:
    """For the same prompt_id, how many rows are BYTE-IDENTICAL across two lexical banks?

    Identity is `prompt_sha16` equality, which is sha256 of `full_prompt` (prompt_families:534) --
    a content hash, so "identical" here means the two banks contain literally the same prompt.
    The expectation (audit brief item 1, plan Sec 1.9) is that these are exactly cells B and E,
    which contain no codeword; this function does not assume that, it counts and then reports
    which cells the identical set actually covers.
    """
    a = {r["prompt_id"]: r for r in c1["rows"]}
    b = {r["prompt_id"]: r for r in c2["rows"]}
    shared = sorted(set(a) & set(b))
    ident_by = collections.Counter()
    diff_by = collections.Counter()
    ident_cells = collections.Counter()
    ident_by_cell_qk_ne = collections.Counter()
    n_ident = 0
    # WHY THE RESIDUAL IS CLASSIFIED AND NOT ROUNDED AWAY. "B and E contain no codeword" is a
    # claim about the corpus, and the corpus does not fully honour it. Every B/E row that is NOT
    # byte-identical is assigned to exactly one mechanical class, in this fixed order, so the
    # shortfall is explained rather than absorbed. `n_codeword_occurrences` is the row's own
    # substring count (prompt_families:520) and is re-derived by AUD_OCCUR before it is used here.
    resid = collections.Counter()
    resid_domain = collections.defaultdict(collections.Counter)
    demo_len_delta = collections.Counter()
    ident_with_codeword = collections.Counter()
    for pid in shared:
        ra, rb = a[pid], b[pid]
        key = (ra["cell"], ra["query_kind"], ra["n_examples"])
        if ra["prompt_sha16"] == rb["prompt_sha16"]:
            n_ident += 1
            ident_by[key] += 1
            ident_cells[ra["cell"]] += 1
            ident_by_cell_qk_ne[key] += 1
            if ra["n_codeword_occurrences"] or rb["n_codeword_occurrences"]:
                # INCIDENTAL codeword collision: the prompt text is the same in both banks, yet one
                # bank's codeword occurs in it by accident of vocabulary. This is the class that
                # VOIDed four `basket` intervention arms on `school_campus` ids under
                # `occurrence_count_mismatch`; it is counted here so the next run can exclude it
                # structurally via --exclude-prompt-ids instead of discovering it as a crash.
                ident_with_codeword[f"{ra['cell']}|{ra['domain']}"] += 1
        else:
            diff_by[key] += 1
            if ra["cell"] in ("B", "E"):
                if ra["n_codeword_occurrences"] or rb["n_codeword_occurrences"]:
                    cls = "contains_codeword"
                elif (ra.get("preamble") or "") != (rb.get("preamble") or ""):
                    cls = "preamble_differs"
                elif ra["demo_block"] != rb["demo_block"]:
                    cls = "demo_block_differs_only"
                    demo_len_delta[len(ra["demo_block"]) - len(rb["demo_block"])] += 1
                elif ra["final_query_text"] != rb["final_query_text"]:
                    cls = "query_differs_only"
                else:
                    cls = "UNEXPLAINED"
                resid[f"{ra['cell']}|{cls}"] += 1
                resid_domain[cls][ra["demo_pool_domain"]] += 1

    # per-cell totals over the shared id space, so the fraction has a stated denominator
    tot_by_cell = collections.Counter(a[p]["cell"] for p in shared)
    return {
        "bank_a": c1["stem"], "bank_b": c2["stem"],
        "bank_a_file_sha16": c1["bank_file_sha16"], "bank_b_file_sha16": c2["bank_file_sha16"],
        "bank_a_rows_sha16": c1["bank_rows_sha16"], "bank_b_rows_sha16": c2["bank_rows_sha16"],
        "n_rows_a": c1["n_rows"], "n_rows_b": c2["n_rows"],
        "n_prompt_ids_shared": len(shared),
        "n_prompt_ids_only_a": len(set(a) - set(b)),
        "n_prompt_ids_only_b": len(set(b) - set(a)),
        "n_byte_identical": n_ident,
        "n_byte_different": len(shared) - n_ident,
        "identical_by_cell": dict(ident_cells),
        "identical_cells_covered": sorted(ident_cells),
        "total_shared_by_cell": dict(tot_by_cell),
        "frac_identical_within_cell": {c: round(ident_cells.get(c, 0) / tot_by_cell[c], 6)
                                       for c in sorted(tot_by_cell)},
        "identical_by_cell_x_query_kind_x_n_examples": {
            f"{c}|{q}|n{n}": v for (c, q, n), v in sorted(ident_by_cell_qk_ne.items(), key=str)},
        "different_by_cell_x_query_kind_x_n_examples": {
            f"{c}|{q}|n{n}": v for (c, q, n), v in sorted(diff_by.items(), key=str)},
        "identical_set_is_exactly_cells_B_and_E": sorted(ident_cells) == ["B", "E"],
        # why the B/E rows that are NOT shared are not shared -- one mechanical class each
        "BE_nonidentical_by_class": dict(sorted(resid.items())),
        "BE_nonidentical_class_by_demo_pool_domain": {k: dict(sorted(v.items()))
                                                      for k, v in sorted(resid_domain.items())},
        "BE_demo_block_char_length_delta_histogram": {str(k): v for k, v
                                                      in sorted(demo_len_delta.items())},
        "BE_identical_though_codeword_present_by_cell_domain": dict(sorted(
            ident_with_codeword.items())),
        "n_BE_unexplained": sum(v for k, v in resid.items() if k.endswith("UNEXPLAINED")),
    }


# --------------------------------------------------------------------------- #
# mutation harness (standing rule 8: pair every verifier with a proof it goes red)
# --------------------------------------------------------------------------- #
def self_test(ctx: dict, meta_rows: list) -> dict:
    """Corrupt one thing at a time; the corresponding audit family must FAIL. Structure only."""
    import copy
    res = {}

    def rerun(mut_rows, mut_meta):
        c = dict(ctx); c["rows"] = mut_rows
        a = audit_bank(c, mut_meta); a.pop("_by_pid", None)
        return a

    base = rerun(ctx["rows"], meta_rows)
    res["baseline_all_pass"] = all(base[k]["pass"] for k in
                                   ("AUD_SURFACE", "AUD_ALIGN", "AUD_CONTRAST",
                                    "AUD_OCCUR_selfderived"))

    # M1: break an occurrence count on one row -> AUD_OCCUR must fail
    rows = copy.deepcopy(ctx["rows"])
    rows[0]["n_codeword_occurrences"] = int(rows[0]["n_codeword_occurrences"]) + 1
    res["M1_occurrence_count_goes_red"] = not rerun(rows, meta_rows)["AUD_OCCUR_selfderived"]["pass"]

    # M2: swap a surface word into the wrong cell -> AUD_SURFACE must fail
    rows = copy.deepcopy(ctx["rows"])
    for r in rows:
        if r["condition"] == "natural_doublespeak":
            r["target_surface"] = str(ctx["meta_concept"])
            break
    res["M2_surface_identity_goes_red"] = not rerun(rows, meta_rows)["AUD_SURFACE"]["pass"]

    # M3: perturb one full_prompt -> masked-prompt contrast must fail
    rows = copy.deepcopy(ctx["rows"])
    mm = copy.deepcopy(meta_rows)
    tgt = next((r for r in rows if r["condition"] == "benign_literal"), None)
    if tgt is not None:
        for m in mm:
            if m["prompt_id"] == tgt["prompt_id"]:
                m["masked_prompt_sha16"] = "0" * 16
    res["M3_masked_contrast_goes_red"] = not rerun(rows, mm)["AUD_CONTRAST"]["pass"]

    # M4: perturb a query hash -> context contrast must fail
    mm = copy.deepcopy(meta_rows)
    for m in mm:
        if m["condition"] == "natural_doublespeak":
            m["query_sha16"] = "1" * 16
            break
    res["M4_query_identity_goes_red"] = not rerun(ctx["rows"], mm)["AUD_CONTRAST"]["pass"]

    res["all_mutations_detected"] = all(v for k, v in res.items() if k.startswith("M"))
    return res


# --------------------------------------------------------------------------- #
# printing
# --------------------------------------------------------------------------- #
def _tbl(headers, rows):
    w = [len(h) for h in headers]
    srows = [[("" if c is None else str(c)) for c in r] for r in rows]
    for r in srows:
        for i, c in enumerate(r):
            w[i] = max(w[i], len(c))
    line = "  ".join(h.ljust(w[i]) for i, h in enumerate(headers))
    print(line)
    print("  ".join("-" * x for x in w))
    for r in srows:
        print("  ".join(c.ljust(w[i]) for i, c in enumerate(r)))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--banks", nargs="*", default=DEFAULT_BANKS,
                    help="bank stems, i.e. boombness_prompt_bank_<stem>.jsonl")
    ap.add_argument("--tag", default="dcsmeta")
    ap.add_argument("--results-glob", nargs="*",
                    default=[os.path.join(REPO_ROOT, "outputs", "boombness",
                                          "extract_boombness", "*", "metadata.json")],
                    help="metadata.json globs of runs to cross-check n_occurrences against")
    ap.add_argument("--self-test", action="store_true",
                    help="run the mutation harness on the first present bank")
    args = ap.parse_args(argv)

    run = common.RunDir("dcs_meta", args, tag=args.tag)
    ledger = common.FailureLedger()
    try:
        import subprocess
        branch = subprocess.run(["git", "-C", REPO_ROOT, "rev-parse", "--abbrev-ref", "HEAD"],
                                capture_output=True, text=True, timeout=30).stdout.strip()
    except Exception as e:                                            # never fatal
        branch = f"UNKNOWN:{type(e).__name__}"
    run.note(git_branch=branch)

    ctxs, attrition, audits = {}, [], {}
    for stem in args.banks:
        ctx = load_bank(stem)
        if not ctx.get("present"):
            ledger.fail("bank_file_absent", stem)
            attrition.append({"bank": stem, "present": False})
            continue
        if not ctx["pools_present"]:
            # Not fatal for the rest of the fields, but benign_concept becomes unresolvable for
            # every row -- which is exactly what AMB-BENIGN-CONCEPT will record, row by row.
            ledger.fail("pools_file_absent", stem)

        meta_rows = [derive_row(r, ctx) for r in ctx["rows"]]

        # ---- sidecar table -------------------------------------------------------------------
        side = run.p(f"dcs_meta__{stem}.jsonl")
        with open(side, "w") as f:
            for m in meta_rows:
                f.write(json.dumps(m) + "\n")

        # ---- structural exclusion CANDIDATES (declared, not applied) --------------------------
        excl = sorted(m["prompt_id"] for m in meta_rows
                      if m["incidental_codeword_in_concept_cell"])
        excl_path = run.p(f"exclude_candidates__incidental_codeword__{stem}.txt")
        with open(excl_path, "w") as f:
            for pid in excl:
                f.write(pid + "\n")

        # ---- attrition / composition ----------------------------------------------------------
        rc = collections.Counter()
        for m in meta_rows:
            for rid in m["ambiguous_reasons"]:
                rc[rid] += 1
        n_amb = sum(1 for m in meta_rows if m["ambiguous"])
        n_core = sum(1 for m in meta_rows if m["in_core_2x2"])
        n_core_ok = sum(1 for m in meta_rows if m["in_core_2x2"] and not m["ambiguous"])
        cov = {k: sum(1 for m in meta_rows if m[k] is not None)
               for k in ("surface_word", "surface_kind", "harmful_concept", "benign_concept",
                         "lexical_bank", "context_kind", "query_template_id", "demo_template_id")}
        a = {
            "bank": stem, "present": True,
            "bank_path": ctx["bank_path"], "bank_file_sha16": ctx["bank_file_sha16"],
            "bank_rows_sha16": ctx["bank_rows_sha16"],
            "bank_rows_sha16_claimed_by_meta": ctx["bank_rows_sha16_claimed"],
            "bank_rows_sha16_matches_meta": (ctx["bank_rows_sha16"]
                                             == ctx["bank_rows_sha16_claimed"]),
            "preset": ctx["preset"], "seed": ctx["seed"],
            "pools_path": ctx["pools_path"], "pools_present": ctx["pools_present"],
            "pools_sha16": ctx["pools_sha16"],
            "pools_sha16_matches_file": (ctx["pools_sha16"] == ctx["pools_sha16_recomputed"]),
            "lexical_bank": f"{ctx['meta_codeword']}_{ctx['meta_concept']}",
            "n_rows_in_bank": ctx["n_rows"],
            "n_metadata_rows_emitted": len(meta_rows),
            "n_ambiguous": n_amb,
            "n_analysable": len(meta_rows) - n_amb,
            "ambiguous_by_rule": dict(sorted(rc.items())),
            "n_core_2x2": n_core,
            "n_core_2x2_analysable": n_core_ok,
            "n_core_2x2_excluded": n_core - n_core_ok,
            "field_coverage_non_null": cov,
            "benign_concept_values": dict(collections.Counter(
                m["benign_concept"] for m in meta_rows).most_common()),
            "context_kind_values": dict(collections.Counter(
                m["context_kind"] for m in meta_rows).most_common()),
            "n_distinct_query_template_id": len({m["query_template_id"] for m in meta_rows}),
            "n_distinct_demo_template_id": len({m["demo_template_id"] for m in meta_rows}),
            "request_id_status": "ABSENT_NO_RUN_CONTEXT",
            "n_incidental_codeword_in_concept_cell": len(excl),
            "incidental_codeword_by_domain": dict(collections.Counter(
                m["domain"] for m in meta_rows
                if m["incidental_codeword_in_concept_cell"]).most_common()),
            "exclusion_candidates_file": os.path.basename(excl_path),
            "exclusion_candidates_note": ("CANDIDATES ONLY -- this run applies no exclusion. "
                                          "Declare them in every arm or in none."),
            "sidecar": os.path.basename(side),
        }
        attrition.append(a)
        ledger.ok(len(meta_rows) - n_amb)
        if n_amb:
            ledger.fail("ambiguous_excluded", stem, n=n_amb)

        aud = audit_bank(ctx, meta_rows)
        aud.pop("_by_pid", None)
        aud["AUD_OCCUR_vs_results_jsonl"] = occurrence_crosscheck(ctx, args.results_glob)
        audits[stem] = aud
        ctxs[stem] = ctx
        ctx["_meta_rows"] = meta_rows

    # ---- AUD-CROSSBANK : pair banks that differ ONLY in codeword ------------------------------
    cross = []
    stems = list(ctxs)
    for i in range(len(stems)):
        for j in range(i + 1, len(stems)):
            a, b = ctxs[stems[i]], ctxs[stems[j]]
            same_design = (a["preset"] == b["preset"] and a["seed"] == b["seed"]
                           and a["pools_sha16"] == b["pools_sha16"]
                           and a["meta_concept"] == b["meta_concept"]
                           and a["meta_codeword"] != b["meta_codeword"])
            if same_design:
                cross.append(crossbank_identity(a, b))

    _prov_keys = ("stem", "bank_path", "bank_file_sha16", "bank_rows_sha16",
                  "bank_rows_sha16_claimed", "pools_path", "pools_sha16", "preset", "seed",
                  "n_rows")
    run.note(banks=[{k: c[k] for k in _prov_keys} for c in ctxs.values()])

    st = {}
    if args.self_test and ctxs:
        s0 = ctxs[stems[0]]
        st = self_test(s0, s0["_meta_rows"])

    summary = {
        "phase": "DCS P1 (plan Sec 3 metadata backfill + Sec 4 structural prompt audit)",
        "plan": ("external_md/DOUBLESPEAK_CONCEPT_SPECIFIC_BOOMBNESS_AND_SURGICAL_CAUSALITY_"
                 "PLAN_AND_PROGRESS_20260902.md"),
        "audit_brief": "reports/DCS_P0_AUDIT_BRIEF.md",
        "definitions": {
            "context_kind": "demo_valence -> {benign:'benign', harm:'harmful'}; else ambiguous",
            "lexical_bank": "f'{codeword}_{concept}'; pools_sha16 kept as a separate field",
            "demo_template_id": ("sha16(demo_pool_domain|demo_valence|split|family_slot|"
                                 "n_examples|pools_sha16)"),
            "query_template_id": "sha16(prompt_families.QUERY_KINDS[query_kind]['template'])",
            "request_id": "(run_id, prompt_id, arm) -- not constructible for an existing bank",
            "benign_concept": "pools[f'{demo_pool_domain}|benign']['natural_word'] (NOT row-local)",
        },
        "ambiguity_rules": [r[0] for r in AMBIGUITY_RULES],
        "banks_written": {k: os.path.basename(run.p(f"dcs_meta__{k}.jsonl")) for k in ctxs},
        "attrition": attrition,
        "audit": audits,
        "crossbank_byte_identity": cross,
        "self_test": st,
        "banks_never_modified": True,
        "note": ("sidecar-only: no bank file, no prompt_families.py, and no bank_rows_sha16 was "
                 "touched, so tests/test_bank_regenerates_byte_identically.py is unaffected."),
    }
    run.write_json("attrition.json", {"attrition": attrition})
    run.write_json("audit.json", {"audit": audits, "crossbank_byte_identity": cross,
                                  "self_test": st})
    for a in attrition:
        run.log_row({"kind": "bank_composition", **{k: v for k, v in a.items()
                                                    if not isinstance(v, dict)}})
    path = run.finish(summary=summary, ledger=ledger)

    # ------------------------------------------------------------------ printed report -------
    print(f"\n=== DCS P1 metadata sidecar + structural audit ===\nrun dir: {path}\n")
    print("-- ATTRITION / COMPOSITION (rows, not percentages) --")
    _tbl(["bank", "lexical_bank", "rows", "meta_rows", "ambiguous", "analysable",
          "core2x2", "core2x2_analysable", "rows_sha16==meta"],
         [[a["bank"], a.get("lexical_bank"), a.get("n_rows_in_bank"),
           a.get("n_metadata_rows_emitted"), a.get("n_ambiguous"), a.get("n_analysable"),
           a.get("n_core_2x2"), a.get("n_core_2x2_analysable"),
           a.get("bank_rows_sha16_matches_meta")] for a in attrition])
    print("\n-- EXCLUSIONS BY MECHANICAL RULE (rows) --")
    rules = sorted({r for a in attrition for r in (a.get("ambiguous_by_rule") or {})})
    if rules:
        _tbl(["bank"] + rules,
             [[a["bank"]] + [(a.get("ambiguous_by_rule") or {}).get(r, 0) for r in rules]
              for a in attrition])
    else:
        print("(none: no row tripped any ambiguity rule in any bank)")
    print("\n-- FIELD COVERAGE (non-null rows) --")
    keys = ["surface_word", "surface_kind", "harmful_concept", "benign_concept", "lexical_bank",
            "context_kind", "query_template_id", "demo_template_id"]
    _tbl(["bank"] + keys,
         [[a["bank"]] + [(a.get("field_coverage_non_null") or {}).get(k) for k in keys]
          for a in attrition if a.get("present")])

    print("\n-- STRUCTURAL EXCLUSION CANDIDATES (incidental codeword in a B/E cell; NOT applied) --")
    _tbl(["bank", "n_candidates", "by_domain", "file"],
         [[a["bank"], a.get("n_incidental_codeword_in_concept_cell"),
           json.dumps(a.get("incidental_codeword_by_domain")),
           a.get("exclusion_candidates_file")] for a in attrition if a.get("present")])

    print("\n-- SEC 4 STRUCTURAL AUDIT (complete core-2x2 families) --")
    _tbl(["bank", "families_complete", "families_incomplete", "AUD_SURFACE", "AUD_ALIGN",
          "AUD_CONTRAST", "AUD_OCCUR(self)"],
         [[k, v["n_core_2x2_families_complete"], v["n_core_2x2_families_incomplete"],
           v["AUD_SURFACE"]["pass"],
           v["AUD_ALIGN"]["pass"], v["AUD_CONTRAST"]["pass"],
           v["AUD_OCCUR_selfderived"]["pass"]] for k, v in audits.items()])
    print("\n-- AUD_OCCUR vs results.jsonl (n_occurrences), occurrence-safe rows only --")
    rowsx = [[k, r["run_dir"].split("/")[-1], r["n_joined"], r["n_occ_agree"],
              r["n_occ_disagree"], r["n_skipped_occurrence_unsafe"], r["n_sha_mismatch"],
              r["pass"]]
             for k, v in audits.items() for r in v["AUD_OCCUR_vs_results_jsonl"]]
    if rowsx:
        _tbl(["bank", "run", "joined", "agree", "disagree", "skipped_unsafe", "sha_mismatch",
              "pass"], rowsx)
    else:
        print("(no matching results.jsonl found for these banks under the given globs)")

    print("\n-- AUD_CROSSBANK: byte-identical rows for the same prompt_id --")
    for c in cross:
        print(f"\n{c['bank_a']}  vs  {c['bank_b']}   "
              f"(shared prompt_ids: {c['n_prompt_ids_shared']} of {c['n_rows_a']}/{c['n_rows_b']})")
        print(f"  BYTE-IDENTICAL: {c['n_byte_identical']}   different: {c['n_byte_different']}")
        print(f"  cells covered by the identical set: {c['identical_cells_covered']}  "
              f"(exactly B and E: {c['identical_set_is_exactly_cells_B_and_E']})")
        _tbl(["cell", "identical", "shared_total", "frac"],
             [[k, c["identical_by_cell"].get(k, 0), c["total_shared_by_cell"][k],
               c["frac_identical_within_cell"][k]] for k in sorted(c["total_shared_by_cell"])])
        print("  identical, by cell|query_kind|n_examples:")
        _tbl(["cell|query_kind|n_examples", "n"],
             [[k, v] for k, v in c["identical_by_cell_x_query_kind_x_n_examples"].items()])
        print("  B/E rows that are NOT byte-identical, by mechanical class "
              f"(unexplained: {c['n_BE_unexplained']}):")
        _tbl(["cell|class", "n"], [[k, v] for k, v in c["BE_nonidentical_by_class"].items()])
        if c["BE_identical_though_codeword_present_by_cell_domain"]:
            print("  identical yet the other bank's codeword occurs incidentally "
                  "(occurrence_count_mismatch hazard), by cell|domain:")
            _tbl(["cell|domain", "n"],
                 [[k, v] for k, v in
                  c["BE_identical_though_codeword_present_by_cell_domain"].items()])
    if st:
        print("\n-- MUTATION HARNESS --")
        _tbl(["check", "result"], [[k, v] for k, v in st.items()])
    print(f"\nwrote: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
