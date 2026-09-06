#!/usr/bin/env python
"""dcs_ts_sidecar.py -- the AUTHORITATIVE METADATA SIDECAR for the six ts116 banks (mandate Sec 7).

WHAT THIS IS
============
One row per bank row, across all six `boombness_prompt_bank_ts116_{button,basket}_{bomb,knife,gun}`
banks (6 x 22,272 = 133,632 rows), carrying every metadata field mandate section 7 asks for, keyed
so that a run's per-prompt output can be joined back to its design cell WITHOUT the cross-bank
fan-out that `prompt_id` alone produces.

WHAT IT REUSES RATHER THAN REWRITES
-----------------------------------
  src/boombness/dcs_metadata.py      load_bank(), derive_row(), sha16(), file_sha16(),
                                     mask_prompt(), AMBIGUITY_RULES, CONTEXT_KIND_MAP, BANK_DIR
                                     -- the whole Sec-1.3 field set and the (bank_file_sha16,
                                     prompt_id) compound key, which is load-bearing here.
  src/boombness/population_index.py  git_commit_safe(), git_dirty_safe()  -- provenance that
                                     cannot kill the run on a node with no git binary.
  src/boombness/prompt_families.py   CONDITIONS, QUERY_KINDS, _char_spans()  -- the generator's OWN
                                     occurrence matcher, so this audit tests the corpus and not a
                                     freshly-written regex (`feedback_matcher_scope_bug_class`).
  src/boombness/common.py            read_jsonl(), rows_sha16()

  scripts/dcs_metadata_sidecar.py was read first; it is the 8-core-bank sibling of this file.  It
  is NOT imported: it hardcodes CORE_BANKS / CORE_CELLS / CORE_N_EXAMPLES for the 38-domain era
  and joins R-078 installation readouts that do not exist for ts116.  Importing it would drag that
  population in.  The key discipline, the collision tests and the read-only stance are carried
  over deliberately.  Neither it nor `dcs_metadata.py` is edited by this script.

WHAT IS NEW HERE
----------------
  1. `dsplit` -- the DOMAIN-level train/validation/test assignment from
     data/boombness_prompts/dcs_ts116_domain_split.json, joined onto every row, with a totality
     check that fails on a missing OR AMBIGUOUS (duplicate-keyed) assignment.
  2. The `split` / `dsplit` disambiguation carried IN the schema.  `split` (dev/heldout) is a
     WITHIN-DOMAIN sentence cut and all 116 domains straddle it; it is emitted here under the name
     `within_domain_split` with `split_field_note` on every row, because confusing the two is the
     single easiest way to produce a leaked result.
  3. A DEMONSTRATED, not asserted, prompt_id collision: a simulated naive join whose mis-attributed
     row count is reported (CHK-PID-FANOUT).
  4. Declared-but-null token columns whose owner is named on the row itself, rather than silent
     nulls (see README section "The token join").

⛔ THE BANKS ARE NEVER OPENED FOR WRITING.  Every bank .jsonl and _meta.json is opened 'r' only.
   `file_sha16` is recomputed after the read pass and compared to the value taken before it
   (CHK-BANK-IMMUTABLE).  Because mutating a bank is forbidden, `--mutate` injects its corruption
   into the SIDECAR TABLE and into the two joined inputs (the split manifest dict, the expected-sha
   table) -- never into a canonical artifact.  That is stated in the mutation report.

A CHECK THAT BINDS TO ZERO ROWS IS A FAILURE.  Every check declares the row set it binds to and
`_bind()` marks it VACUOUS -> FAIL when that set is empty.  `--mutate all` proves each check can go
RED.

Usage
-----
  python scripts/dcs_ts_sidecar.py --build            # write sidecar + run all checks
  python scripts/dcs_ts_sidecar.py --check-only       # checks, no output file
  python scripts/dcs_ts_sidecar.py --mutate all       # prove every check can go RED
  python scripts/dcs_ts_sidecar.py --mutate keydup
"""
from __future__ import annotations

import argparse
import collections
import datetime
import gzip
import hashlib
import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(_HERE)
sys.path.insert(0, os.path.join(REPO, "src", "boombness"))

import common                       # noqa: E402
import dcs_metadata as dm           # noqa: E402  *** the module we build on ***
import population_index as pidx     # noqa: E402
import prompt_families as pf        # noqa: E402

SCHEMA = "dcs_ts_sidecar/1"

#: The six ts116 banks.  Named, not globbed: a glob would silently shrink if a file were renamed,
#: and a sidecar over five banks that says nothing is exactly the failure mode this file exists to
#: prevent.  CHK-BANK-PRESENT fails if any is absent.
TS_BANKS = ("ts116_button_bomb", "ts116_button_knife", "ts116_button_gun",
            "ts116_basket_bomb", "ts116_basket_knife", "ts116_basket_gun")

#: PHASE-3 entry R-098's published bank_rows_sha16 values.  Hardcoded so that the sidecar refuses
#: to describe a bank that is not the one the sprint recorded.  This is a pin, not a derivation.
EXPECTED_ROWS_SHA16 = {
    "ts116_button_bomb":  "c37127790a08519f",
    "ts116_button_knife": "151ef6734bfdbe6e",
    "ts116_button_gun":   "e1ff5534b5318ad9",
    "ts116_basket_bomb":  "86463da433d0eebf",
    "ts116_basket_knife": "2839bfbc4d41a8b9",
    "ts116_basket_gun":   "60b508bd1aa6d0a7",
}
EXPECTED_N_ROWS = 22272
EXPECTED_N_DOMAINS = 116
EXPECTED_PRESET = "main_longpre_cds_ts"
EXPECTED_SEED = 20260901
EXPECTED_POOLS_SHA16 = "976aa2b0b617118d"

SPLIT_MANIFEST = os.path.join(REPO, "data", "boombness_prompts", "dcs_ts116_domain_split.json")
EXPECTED_MANIFEST_SHA16 = "be7d2c772d814ef3"
EXPECTED_DSPLIT_COUNTS = {"train": 70, "validation": 23, "test": 23}

SIDECAR_OUT = os.path.join(REPO, "outputs", "dcs_ts", "ts116_sidecar.jsonl.gz")

#: Owned by another agent.  This file neither reads nor writes it; the columns below are declared
#: and left null so that the join has a place to land.  See README "The token join".
TOKEN_ROLES_ARTIFACT = "outputs/dcs_ts/token_roles_ts116.json.gz"
TOKEN_COLUMNS = ("target_token_ids", "target_token_span", "query_token_span",
                 "demo_token_span", "n_prompt_tokens", "tokenizer_name")

SPLIT_FIELD_NOTE = ("within_domain_split (dev/heldout) is a SENTENCE-level cut inside each domain; "
                    "all 116/116 domains straddle it. dsplit is the DOMAIN-level cut. "
                    "Never group by within_domain_split when you mean dsplit.")


# ============================================================================================== #
# INTENDED MAPPING -- declared from the generator's own condition table, not from an outcome.
# ============================================================================================== #
# `intended_mapping` answers: what does the DESIGN intend the word the query asks about to denote,
# given the demonstrations?  Derived from prompt_families.CONDITIONS (demo_valence x demo_surface x
# query_surface).  It is a statement about the DESIGN.  Whether knife/gun demonstrations actually
# INSTALL anything is an empirical question this column does not answer and must not be read as
# answering -- the harm pools' natural_word is "bomb" for all 116 domains, so the knife and gun
# banks are bomb-demonstration text with the word swapped.
INTENDED_MAPPING = {
    "A": ("codeword_denotes_itself",
          "benign demos + codeword query: the surface word keeps its literal referent"),
    "B": ("concept_denotes_itself",
          "harm demos + concept query: the concept word is used openly, no remap"),
    "C": ("codeword_denotes_concept",
          "harm demos rendered in the codeword surface + codeword query: the design intends the "
          "codeword to be read as the concept. THE PRIMARY CELL."),
    "E": ("concept_denotes_itself_in_benign_context",
          "benign demos + concept query: concept word present, demos do not support it"),
    "D": ("codeword_denotes_itself",
          "benign demos + codeword query (direct_codeword control)"),
    "F": ("codeword_denotes_remap_source",
          "benign_remap: demos install a DIFFERENT literal referent for the codeword"),
}

#: `template_family` = the family_id with the domain stripped, i.e. the design cell shared by all
#: 116 domains.  Emitted so that "template" can be a grouping unit without smuggling the domain in.


def _template_family(family_id, domain):
    if not family_id:
        return None
    parts = str(family_id).split("|")
    if parts and parts[0] == domain:
        parts = parts[1:]
    return "|".join(parts)


# ============================================================================================== #
# CHECK HARNESS.  A check that binds to zero rows is a FAILURE, not a pass.
# ============================================================================================== #
class Checks:
    def __init__(self):
        self.results = []

    def add(self, cid, ok, binds_to, detail, population):
        """binds_to = number of rows/objects this check actually examined."""
        if binds_to == 0:
            self.results.append(dict(id=cid, status="FAIL", reason="VACUOUS", binds_to=0,
                                     detail=f"bound to ZERO {population}; a check that cannot "
                                            f"fail is worth nothing. {detail}",
                                     population=population))
        else:
            self.results.append(dict(id=cid, status="PASS" if ok else "FAIL",
                                     reason="" if ok else "VIOLATION", binds_to=binds_to,
                                     detail=detail, population=population))
        return self.results[-1]

    @property
    def failed(self):
        return [r for r in self.results if r["status"] == "FAIL"]

    def report(self, prefix=""):
        lines = []
        for r in self.results:
            mark = "PASS" if r["status"] == "PASS" else f"FAIL[{r['reason']}]"
            lines.append(f"{prefix}{mark:16s} {r['id']:24s} n={r['binds_to']:<8d} {r['detail']}")
        return "\n".join(lines)


# ============================================================================================== #
# INPUT 1: the domain split manifest.  Duplicate keys are AMBIGUITY, and json.load hides them.
# ============================================================================================== #
def load_split_manifest(path=SPLIT_MANIFEST):
    """Return (manifest_dict, assign_pairs).

    `assign_pairs` is the RAW list of (domain, dsplit) pairs as they appear in the file.  json.load
    silently keeps only the last of a duplicated key, so a domain assigned twice -- the ambiguous
    case the mandate requires us to fail on -- is INVISIBLE to a normal parse.  We therefore parse
    with object_pairs_hook and keep the pairs.
    """
    raw = open(path, "r").read()
    captured = {}

    def hook(pairs):
        d = {}
        for k, v in pairs:
            d[k] = v
        # the assign object is the only one whose duplicate keys matter
        if pairs and all(isinstance(v, str) for _, v in pairs) and len(pairs) > 10:
            captured.setdefault("assign_pairs", list(pairs))
        return d

    obj = json.loads(raw, object_pairs_hook=hook)
    pairs = captured.get("assign_pairs") or list(obj.get("assign", {}).items())
    return obj, pairs


def manifest_sha16(manifest):
    """Recompute exactly as scripts/dcs_ts_split_manifest.py:136 does."""
    body = {k: v for k, v in manifest.items() if k != "manifest_sha16"}
    return hashlib.sha256(
        json.dumps(body, sort_keys=True, separators=(",", ":")).encode()).hexdigest()[:16]


# ============================================================================================== #
# BUILD
# ============================================================================================== #
def build_rows(banks=TS_BANKS, verbose=True):
    """Stream every bank once, one bank resident at a time, and emit the sidecar rows.

    Returns (rows, bankinfo, sha_before, sha_after).  Nothing is written here.
    """
    provenance = dict(
        sidecar_schema=SCHEMA,
        sidecar_script="scripts/dcs_ts_sidecar.py",
        sidecar_run_commit=pidx.git_commit_safe(),
        sidecar_run_dirty=pidx.git_dirty_safe(),
        sidecar_built_at=datetime.datetime.now().isoformat(timespec="seconds"),
    )
    manifest, assign_pairs = load_split_manifest()
    dsplit_map = {}
    for d, v in assign_pairs:
        dsplit_map.setdefault(d, []).append(v)

    rows, bankinfo = [], {}
    sha_before, sha_after = {}, {}
    for stem in banks:
        path = os.path.join(dm.BANK_DIR, f"boombness_prompt_bank_{stem}.jsonl")
        sha_before[stem] = dm.file_sha16(path) if os.path.exists(path) else None
        ctx = dm.load_bank(stem)                      # REUSED. opens 'r' only.
        if not ctx.get("present"):
            bankinfo[stem] = dict(present=False, path=path)
            continue
        meta = json.load(open(ctx["meta_path"])) if ctx.get("meta_path") else {}
        bankinfo[stem] = dict(
            present=True, n_rows=ctx["n_rows"],
            bank_file_sha16=ctx["bank_file_sha16"],
            bank_rows_sha16=ctx["bank_rows_sha16"],
            bank_rows_sha16_claimed=ctx["bank_rows_sha16_claimed"],
            preset=ctx["preset"], seed=ctx["seed"],
            pools_sha16=ctx["pools_sha16"],
            pools_sha16_recomputed=ctx["pools_sha16_recomputed"],
            codeword=ctx["meta_codeword"], concept=ctx["meta_concept"],
            meta_git_commit=meta.get("git_commit"), meta_timestamp=meta.get("timestamp"),
            incidental_repairs=meta.get("incidental_repairs"),
            path=os.path.relpath(ctx["bank_path"], REPO),
        )
        for r in ctx["rows"]:
            rows.append(_sidecar_row(r, ctx, bankinfo[stem], dsplit_map, manifest, provenance))
        del ctx
        sha_after[stem] = dm.file_sha16(path)
        if verbose:
            print(f"  built {stem}: {bankinfo[stem]['n_rows']} rows", file=sys.stderr)
    return rows, bankinfo, sha_before, sha_after, manifest, assign_pairs, provenance


def _sidecar_row(r, ctx, bi, dsplit_map, manifest, provenance):
    base = dm.derive_row(r, ctx)                     # REUSED: the whole Sec-1.3 field set
    fp = r.get("full_prompt") or ""
    q = r.get("final_query_text") or ""
    demo = r.get("demo_block") or ""
    surface = r.get("target_surface") or ""
    concept = r.get("concept") or ""
    codeword = r.get("codeword") or ""
    domain = r.get("domain")

    # -- re-derived occurrence facts.  pf._char_spans is the GENERATOR's own matcher. ------------
    tgt_spans = pf._char_spans(fp, surface) if surface else []
    # TWO MATCHERS, DELIBERATELY.  The bank itself uses two and they DISAGREE on 180 rows:
    #   expected_target_occurrences / n_target_occurrences  <- pf._char_spans, WHOLE-WORD, case-ins.
    #   n_codeword_occurrences / n_concept_occurrences      <- prompt_families.py:521-522,
    #                                                          full.lower().count(word.lower()),
    #                                                          a SUBSTRING count.
    # "basketball" in the school_campus preamble is a substring hit for the codeword `basket` and
    # not a whole-word one.  Both are re-derived here so the discrepancy is a measured column
    # rather than a mystery that surfaces later as an occurrence_count_mismatch mid-run.
    conc_spans = pf._char_spans(fp, concept) if concept else []
    code_spans = pf._char_spans(fp, codeword) if codeword else []
    code_sub = fp.lower().count(codeword.lower()) if codeword else 0
    conc_sub = fp.lower().count(concept.lower()) if concept else 0
    conc_in_q = bool(pf._char_spans(q, concept)) if concept else False
    code_in_q = bool(pf._char_spans(q, codeword)) if codeword else False

    # -- spans of the two structural blocks inside the prompt ------------------------------------
    def _span(hay, needle):
        if not needle:
            return None, "EMPTY_BLOCK"
        n = hay.count(needle)
        if n == 0:
            return None, "NOT_FOUND"
        if n > 1:
            i = hay.rfind(needle)
            return [i, i + len(needle)], f"AMBIGUOUS_{n}_OCCURRENCES_TOOK_LAST"
        i = hay.find(needle)
        return [i, i + len(needle)], "OK"

    demo_span, demo_status = _span(fp, demo)
    query_span, query_status = _span(fp, q)
    cell = r.get("cell")
    im, im_basis = INTENDED_MAPPING.get(cell, (None, "UNKNOWN_CELL"))
    dvals = dsplit_map.get(domain, [])

    out = {
        "schema": SCHEMA,
        # -------- THE JOIN KEY.  prompt_id alone is NOT a key; see CHK-PID-FANOUT. --------------
        "join_key": f"{ctx['bank_file_sha16']}:{r.get('prompt_id')}",
        "join_key_fields": ["bank_file_sha16", "prompt_id"],
        "bank_sha": ctx["bank_file_sha16"],
        "bank_file_sha16": ctx["bank_file_sha16"],
        "bank_rows_sha16": ctx["bank_rows_sha16"],
        "bank_stem": ctx["stem"],
        "bank_path": bi["path"],
        "prompt_id": r.get("prompt_id"),
        "prompt_sha16": r.get("prompt_sha16"),
        # -------- design axes --------------------------------------------------------------------
        "domain_id": domain,
        "demo_pool_domain": r.get("demo_pool_domain"),
        "dsplit": (dvals[0] if len(dvals) == 1 else None),
        "dsplit_n_assignments": len(dvals),
        "dsplit_status": ("OK" if len(dvals) == 1
                          else ("MISSING" if not dvals else "AMBIGUOUS")),
        "within_domain_split": r.get("split"),
        "split_field_note": SPLIT_FIELD_NOTE,
        "template_family": _template_family(r.get("family_id"), domain),
        "family_id": r.get("family_id"),
        "family_slot": r.get("family_slot"),
        "bank_block": r.get("bank_block"),
        "condition": r.get("condition"),
        "cell": cell,
        "n_examples": r.get("n_examples"),
        "n_demos_emitted": r.get("n_demos_emitted"),
        "strength": r.get("strength"),
        "consistency": r.get("consistency"),
        "example_position": r.get("example_position"),
        "role_style": r.get("role_style"),
        "query_kind": r.get("query_kind"),
        "scores": r.get("scores"),
        "occurrence_analysis_safe": r.get("occurrence_analysis_safe"),
        # -------- lexical setting -----------------------------------------------------------------
        "concept": concept,
        "codeword": codeword,
        "surface_word": surface,
        "surface_type": r.get("query_surface"),
        "demonstration_valence": r.get("demo_valence"),
        "demonstration_surface": r.get("demo_surface"),
        "context_kind": base.get("context_kind"),
        "benign_concept": base.get("benign_concept"),
        "lexical_setting": f"{codeword}_{concept}",
        "intended_mapping": im,
        "intended_mapping_basis": im_basis,
        "intended_mapping_scope": ("DESIGN INTENT ONLY. Whether the demonstrations INSTALL this "
                                   "mapping is an empirical question; the harm pools' natural_word "
                                   "is 'bomb' for all 116 domains, so knife/gun demos are "
                                   "bomb-text with the word swapped."),
        "target_semantic_bank": r.get("target_semantic"),
        "target_semantic_is_vacuous": r.get("target_semantic") == concept,
        "target_semantic_vacuity_note": ("prompt_families writes target_semantic := concept "
                                         "unconditionally, so this equality is true by "
                                         "construction and is not evidence about any row."),
        # -------- template hashes (reused from dcs_metadata.derive_row) ---------------------------
        "query_template_id": base.get("query_template_id"),
        "demo_template_id": base.get("demo_template_id"),
        "masked_prompt_sha16": base.get("masked_prompt_sha16"),
        "query_sha16": base.get("query_sha16"),
        "demo_block_sha16": base.get("demo_block_sha16"),
        # -------- model ---------------------------------------------------------------------------
        "model": None,
        "model_status": ("NOT_APPLICABLE_PROMPT_ONLY_ARTIFACT: the sidecar describes prompts. The "
                         "model is a property of a RUN and arrives with the run's config.json; "
                         "join it in on join_key, do not backfill it here."),
        # -------- occurrences: bank field vs RE-DERIVED, and their agreement ----------------------
        "n_target_occurrences_bank": r.get("n_target_occurrences"),
        "n_target_occurrences_rederived": len(tgt_spans),
        "target_occurrences_agree": r.get("n_target_occurrences") == len(tgt_spans),
        "target_char_spans": tgt_spans,
        "target_char_spans_bank": r.get("expected_target_occurrences"),
        "target_spans_agree": ([list(s) for s in (r.get("expected_target_occurrences") or [])]
                               == tgt_spans),
        "n_codeword_occurrences_bank": r.get("n_codeword_occurrences"),
        "n_codeword_occurrences_substring": code_sub,
        "n_codeword_occurrences_wholeword": len(code_spans),
        "codeword_occurrences_agree": r.get("n_codeword_occurrences") == code_sub,
        "n_concept_occurrences_bank": r.get("n_concept_occurrences"),
        "n_concept_occurrences_substring": conc_sub,
        "n_concept_occurrences_wholeword": len(conc_spans),
        "concept_occurrences_agree": r.get("n_concept_occurrences") == conc_sub,
        # CANDIDATE EXCLUSION FLAG, not an exclusion.  True when a lexical item appears inside a
        # longer word ("basket" in "basketball"), so that the bank's substring counters exceed the
        # whole-word span list.  This is the class that trips occurrence_count_mismatch and VOIDs
        # an intervention arm mid-run; declare it in EVERY arm up front, baseline included.
        "lexical_collision_substring_only": bool(code_sub > len(code_spans)
                                                 or conc_sub > len(conc_spans)),
        "lexical_collision_detail": (
            f"codeword substring {code_sub} > whole-word {len(code_spans)}"
            if code_sub > len(code_spans) else
            (f"concept substring {conc_sub} > whole-word {len(conc_spans)}"
             if conc_sub > len(conc_spans) else "")),
        "concept_in_full_prompt": bool(conc_spans),
        "concept_in_query": conc_in_q,
        "codeword_in_query": code_in_q,
        # -------- structural spans -----------------------------------------------------------------
        "demo_span_char": demo_span,
        "demo_span_status": demo_status,
        "query_span_char": query_span,
        "query_span_status": query_status,
        "n_preamble_lines": r.get("n_preamble_lines"),
        "prompt_len_chars_bank": r.get("n_chars"),
        "prompt_len_chars_rederived": len(fp),
        "prompt_len_agree": r.get("n_chars") == len(fp),
        "query_len_chars": len(q),
        "demo_len_chars": len(demo),
        # -------- token columns: DECLARED, NULL, OWNED ELSEWHERE ------------------------------------
        **{c: None for c in TOKEN_COLUMNS},
        "token_fields_status": "DEFERRED_TO_TOKEN_ROLES_AGENT",
        "token_fields_owner_artifact": TOKEN_ROLES_ARTIFACT,
        "token_fields_join": ("left-join that artifact on join_key = "
                              "f'{bank_file_sha16}:{prompt_id}'; these six columns are the landing "
                              "slots. This script never reads or writes that file."),
        # -------- ambiguity flags carried over from dcs_metadata -------------------------------------
        "design_ambiguous": base.get("ambiguous"),
        "design_ambiguous_reasons": base.get("ambiguous_reasons"),
        "incidental_codeword_in_concept_cell": base.get("incidental_codeword_in_concept_cell"),
        # -------- EXCLUSIONS / FAILURE STATUS.  Empty on purpose; installation metrics land later. --
        "exclusion_status": "",
        "exclusion_reasons": [],
        "failure_status": "",
        "installation_status": None,
        "installation_metrics": None,
        "status_columns_note": ("exclusion_status/failure_status are EMPTY STRINGS meaning 'no "
                                "exclusion decided yet', NOT 'included'. Installation metrics are "
                                "computed downstream and written to a separate joined artifact; "
                                "these columns are their declared landing slots."),
        # -------- provenance -------------------------------------------------------------------------
        "pools_path": manifest.get("pools_path"),
        "pools_sha16": ctx.get("pools_sha16"),
        "bank_preset": ctx.get("preset"),
        "bank_seed": ctx.get("seed"),
        "bank_meta_git_commit": bi.get("meta_git_commit"),
        "bank_meta_timestamp": bi.get("meta_timestamp"),
        "split_manifest_path": os.path.relpath(SPLIT_MANIFEST, REPO),
        "split_manifest_sha16": manifest.get("manifest_sha16"),
        "split_manifest_seed": manifest.get("seed"),
        **provenance,
    }
    return out


# ============================================================================================== #
# CHECKS
# ============================================================================================== #
def run_checks(rows, bankinfo, sha_before, sha_after, manifest, assign_pairs,
               expected_rows_sha=None, banks=TS_BANKS):
    expected_rows_sha = EXPECTED_ROWS_SHA16 if expected_rows_sha is None else expected_rows_sha
    C = Checks()
    n = len(rows)

    # ---- CHK-BANK-PRESENT ---------------------------------------------------------------------
    missing = [b for b in banks if not bankinfo.get(b, {}).get("present")]
    C.add("CHK-BANK-PRESENT", not missing, len(banks),
          f"{len(banks) - len(missing)}/{len(banks)} banks present; missing={missing}", "banks")

    # ---- CHK-BANK-ROWCOUNT --------------------------------------------------------------------
    bad = {b: bankinfo[b]["n_rows"] for b in bankinfo
           if bankinfo[b].get("present") and bankinfo[b]["n_rows"] != EXPECTED_N_ROWS}
    C.add("CHK-BANK-ROWCOUNT", not bad, sum(1 for b in bankinfo if bankinfo[b].get("present")),
          f"every present bank has exactly {EXPECTED_N_ROWS} rows; offenders={bad}", "banks")

    # ---- CHK-BANK-IMMUTABLE: the file bytes are identical before and after our read pass -------
    checked = [b for b in banks if sha_before.get(b) and sha_after.get(b)]
    drift = {b: (sha_before[b], sha_after[b]) for b in checked if sha_before[b] != sha_after[b]}
    C.add("CHK-BANK-IMMUTABLE", not drift, len(checked),
          f"file_sha16 identical before/after the read pass on {len(checked)} banks; drift={drift}",
          "banks")

    # ---- CHK-BANK-ROWS-SHA-PIN: the banks are the ones entry R-098 published --------------------
    pinned = [b for b in banks if b in expected_rows_sha and bankinfo.get(b, {}).get("present")]
    off = {b: (bankinfo[b]["bank_rows_sha16"], expected_rows_sha[b])
           for b in pinned if bankinfo[b]["bank_rows_sha16"] != expected_rows_sha[b]}
    C.add("CHK-BANK-ROWS-SHA-PIN", not off, len(pinned),
          f"recomputed bank_rows_sha16 == R-098's published value on {len(pinned)} banks; "
          f"mismatches={off}", "banks")

    # ---- CHK-BANK-META-AGREE: meta's own claimed rows sha, preset, seed, pools -----------------
    present = [b for b in banks if bankinfo.get(b, {}).get("present")]
    meta_bad = {b: dict(claimed=bankinfo[b]["bank_rows_sha16_claimed"],
                        recomputed=bankinfo[b]["bank_rows_sha16"],
                        preset=bankinfo[b]["preset"], seed=bankinfo[b]["seed"],
                        pools=bankinfo[b]["pools_sha16"])
                for b in present
                if (bankinfo[b]["bank_rows_sha16_claimed"] != bankinfo[b]["bank_rows_sha16"]
                    or bankinfo[b]["preset"] != EXPECTED_PRESET
                    or bankinfo[b]["seed"] != EXPECTED_SEED
                    or bankinfo[b]["pools_sha16"] != EXPECTED_POOLS_SHA16)}
    C.add("CHK-BANK-META-AGREE", not meta_bad, len(present),
          f"meta claimed rows-sha == recomputed, preset=={EXPECTED_PRESET}, seed=={EXPECTED_SEED}, "
          f"pools_sha16=={EXPECTED_POOLS_SHA16}; offenders={meta_bad}", "banks")

    # ---- CHK-KEY-UNIQUE: THE HARD REQUIREMENT.  The compound key must be unique. ---------------
    keys = collections.Counter(r["join_key"] for r in rows)
    dupes = {k: c for k, c in keys.items() if c > 1}
    C.add("CHK-KEY-UNIQUE", not dupes, n,
          f"distinct (bank_file_sha16, prompt_id) = {len(keys)} over {n} rows; "
          f"duplicated keys = {len(dupes)}"
          + (f"; example={next(iter(dupes))} x{dupes[next(iter(dupes))]}" if dupes else ""),
          "sidecar rows")

    # ---- CHK-PID-FANOUT: PROVE, do not assert, that prompt_id alone collides -------------------
    # A naive join builds a readout table keyed by prompt_id from ONE run (here: the first bank)
    # and left-joins it onto every row. Every row whose bank differs from the readout's source
    # bank is MIS-ATTRIBUTED, silently. We count them.
    pids = collections.Counter(r["prompt_id"] for r in rows)
    collision_excess = n - len(pids)
    src_bank = banks[0]
    src = {r["prompt_id"]: r["bank_sha"] for r in rows if r["bank_stem"] == src_bank}
    misattributed = sum(1 for r in rows if r["prompt_id"] in src and src[r["prompt_id"]] != r["bank_sha"])
    mult = collections.Counter(pids.values())
    ok = collision_excess > 0 and misattributed > 0
    C.add("CHK-PID-FANOUT", ok, n,
          f"distinct prompt_id = {len(pids)} over {n} rows -> collision excess = "
          f"{collision_excess}. Simulated naive join of a prompt_id-keyed readout table built from "
          f"'{src_bank}' MIS-ATTRIBUTES {misattributed} rows to the wrong bank. "
          f"prompt_id multiplicity histogram = {dict(mult)}. "
          f"(This check FAILS if the hazard is absent, because then the sidecar's key discipline "
          f"would have no justification and the claim would be unproven.)",
          "sidecar rows")

    # ---- CHK-PROMPT-SHA-NOT-A-KEY: the obvious fallback key is also not one --------------------
    pshas = collections.Counter(r["prompt_sha16"] for r in rows)
    psha_excess = n - len(pshas)
    C.add("CHK-PROMPT-SHA-NOT-A-KEY", psha_excess > 0, n,
          f"distinct prompt_sha16 = {len(pshas)} over {n} rows -> duplicate-excess "
          f"{psha_excess}; prompt_sha16 is NOT a fallback key either", "sidecar rows")

    # ---- CHK-MANIFEST-SHA ---------------------------------------------------------------------
    rec = manifest_sha16(manifest)
    C.add("CHK-MANIFEST-SHA",
          rec == manifest.get("manifest_sha16") == EXPECTED_MANIFEST_SHA16, 1,
          f"recomputed={rec} stored={manifest.get('manifest_sha16')} "
          f"pinned={EXPECTED_MANIFEST_SHA16}", "split manifests")

    # ---- CHK-DSPLIT-TOTAL: every domain gets EXACTLY ONE dsplit --------------------------------
    bank_domains = sorted({r["domain_id"] for r in rows})
    assign_count = collections.Counter(d for d, _ in assign_pairs)
    assign_vals = collections.defaultdict(set)
    for d, v in assign_pairs:
        assign_vals[d].add(v)
    missing_dom = [d for d in bank_domains if assign_count.get(d, 0) == 0]
    ambiguous_dom = [d for d in bank_domains
                     if assign_count.get(d, 0) > 1 and len(assign_vals[d]) > 1]
    dup_keyed = [d for d in bank_domains if assign_count.get(d, 0) > 1]
    extra_dom = [d for d in assign_count if d not in set(bank_domains)]
    ok = (not missing_dom and not dup_keyed and not extra_dom
          and len(bank_domains) == EXPECTED_N_DOMAINS)
    C.add("CHK-DSPLIT-TOTAL", ok, len(bank_domains),
          f"{len(bank_domains)} distinct domains in the banks (expected {EXPECTED_N_DOMAINS}); "
          f"missing from manifest={missing_dom}; duplicate-keyed in manifest={dup_keyed} "
          f"(of which value-ambiguous={ambiguous_dom}); in manifest but not in banks={extra_dom}",
          "domains")

    # ---- CHK-DSPLIT-ROWSTATUS: no row may carry a null/ambiguous dsplit ------------------------
    badrows = [r for r in rows if r["dsplit_status"] != "OK" or r["dsplit"] is None]
    C.add("CHK-DSPLIT-ROWSTATUS", not badrows, n,
          f"{n - len(badrows)}/{n} rows carry exactly one dsplit; offenders={len(badrows)}"
          + (f"; example domain={badrows[0]['domain_id']} status={badrows[0]['dsplit_status']}"
             if badrows else ""), "sidecar rows")

    # ---- CHK-DSPLIT-COUNTS --------------------------------------------------------------------
    dom_split = {}
    for r in rows:
        dom_split[r["domain_id"]] = r["dsplit"]
    got = collections.Counter(dom_split.values())
    C.add("CHK-DSPLIT-COUNTS", dict(got) == EXPECTED_DSPLIT_COUNTS, len(dom_split),
          f"domains per dsplit = {dict(got)}; expected {EXPECTED_DSPLIT_COUNTS}", "domains")

    # ---- CHK-DSPLIT-BANK-INVARIANT: the domain split is identical in all six banks -------------
    per_bank = collections.defaultdict(dict)
    for r in rows:
        per_bank[r["bank_stem"]][r["domain_id"]] = r["dsplit"]
    ref = per_bank[banks[0]]
    diff = {b: sum(1 for d, v in per_bank[b].items() if ref.get(d) != v)
            for b in per_bank if b != banks[0]}
    C.add("CHK-DSPLIT-BANK-INVARIANT", not any(diff.values()), len(per_bank),
          f"dsplit per domain identical across all banks; per-bank disagreements={diff}", "banks")

    # ---- CHK-SPLIT-NOT-DSPLIT: the two split fields are different objects -----------------------
    # Every domain straddles the within-domain dev/heldout cut; if it did not, someone could
    # mistake `split` for the domain-level split without noticing.
    straddle = collections.defaultdict(set)
    for r in rows:
        straddle[r["domain_id"]].add(r["within_domain_split"])
    n_straddle = sum(1 for d, s in straddle.items() if len(s) > 1)
    C.add("CHK-SPLIT-NOT-DSPLIT", n_straddle == len(straddle), len(straddle),
          f"{n_straddle}/{len(straddle)} domains straddle within_domain_split "
          f"(values={sorted({v for s in straddle.values() for v in s})}); "
          f"within_domain_split therefore CANNOT be used as a domain-level split", "domains")

    # ---- CHK-TARGET-SPANS: re-derived char spans == the bank's own field -----------------------
    bound = [r for r in rows if r["surface_word"]]
    bad = [r for r in bound if not r["target_spans_agree"] or not r["target_occurrences_agree"]]
    C.add("CHK-TARGET-SPANS", not bad, len(bound),
          f"re-derived pf._char_spans(full_prompt, surface_word) == expected_target_occurrences on "
          f"{len(bound) - len(bad)}/{len(bound)} rows; disagreements={len(bad)}"
          + (f"; example join_key={bad[0]['join_key']}" if bad else ""), "sidecar rows")

    # ---- CHK-OCCURRENCE-COUNTS: the bank's OWN counter reproduced exactly ----------------------
    # The bank counts codeword/concept with `full.lower().count(word.lower())`
    # (prompt_families.py:521-522), a SUBSTRING count. Re-deriving it with the same rule must
    # reproduce it on every row; if it does not, the bank field means something we have not
    # modelled and nothing downstream may group on it.
    bad = [r for r in rows if not r["codeword_occurrences_agree"]
           or not r["concept_occurrences_agree"]]
    C.add("CHK-OCCURRENCE-COUNTS", not bad, n,
          f"n_codeword/n_concept_occurrences re-derived with the generator's own substring rule "
          f"agree with the bank on {n - len(bad)}/{n} rows; disagreements={len(bad)}",
          "sidecar rows")

    # ---- CHK-MATCHER-DIVERGENCE: the bank uses TWO matchers and they disagree -------------------
    # `expected_target_occurrences` is WHOLE-WORD; `n_codeword_occurrences` is SUBSTRING. Where a
    # lexical item sits inside a longer word the two differ. This check does not demand agreement
    # -- it demands that every divergent row be FLAGGED, and it binds to the divergent set, so it
    # goes red if the divergence grows into unflagged rows.
    diverge = [r for r in rows
               if r["n_codeword_occurrences_substring"] != r["n_codeword_occurrences_wholeword"]
               or r["n_concept_occurrences_substring"] != r["n_concept_occurrences_wholeword"]]
    unflagged = [r for r in diverge if not r["lexical_collision_substring_only"]]
    where = collections.Counter((r["bank_stem"], r["domain_id"]) for r in diverge)
    C.add("CHK-MATCHER-DIVERGENCE", not unflagged, len(diverge),
          f"{len(diverge)}/{n} rows where the bank's SUBSTRING counter exceeds the WHOLE-WORD span "
          f"list; all of them carry lexical_collision_substring_only "
          f"({len(diverge) - len(unflagged)}/{len(diverge)} flagged, {len(unflagged)} unflagged). "
          f"Located in {dict(where)}", "divergent rows")

    # ---- CHK-PROMPT-LEN -----------------------------------------------------------------------
    bad = [r for r in rows if not r["prompt_len_agree"]]
    C.add("CHK-PROMPT-LEN", not bad, n,
          f"n_chars == len(full_prompt) on {n - len(bad)}/{n} rows", "sidecar rows")

    # ---- CHK-QUERY-SPAN: the query is locatable in the prompt ----------------------------------
    bad = [r for r in rows if r["query_span_status"] not in ("OK",)]
    C.add("CHK-QUERY-SPAN", not bad, n,
          f"final_query_text located exactly once in full_prompt on {n - len(bad)}/{n} rows; "
          f"non-OK statuses={collections.Counter(r['query_span_status'] for r in bad) or '{}'}",
          "sidecar rows")

    # ---- CHK-QUERY-AT-END ----------------------------------------------------------------------
    bad = [r for r in rows if r["query_span_char"] and r["query_span_char"][1]
           != r["prompt_len_chars_rederived"]]
    C.add("CHK-QUERY-AT-END", not bad, sum(1 for r in rows if r["query_span_char"]),
          f"the query span ends at the last character of the prompt on "
          f"{n - len(bad)}/{n} rows; offenders={len(bad)}", "sidecar rows")

    # ---- CHK-DEMO-SPAN: nonempty demo blocks are locatable --------------------------------------
    bound = [r for r in rows if r["n_examples"] and r["n_examples"] > 0]
    bad = [r for r in bound if r["demo_span_status"] != "OK"]
    C.add("CHK-DEMO-SPAN", not bad, len(bound),
          f"demo_block located exactly once in full_prompt on {len(bound) - len(bad)}/{len(bound)} "
          f"rows with n_examples>0; non-OK="
          f"{collections.Counter(r['demo_span_status'] for r in bad) or '{}'}", "sidecar rows")

    # ---- CHK-N0-NO-DEMOS ------------------------------------------------------------------------
    bound = [r for r in rows if r["n_examples"] == 0]
    bad = [r for r in bound if r["demo_len_chars"] != 0 or r["n_demos_emitted"] != 0]
    C.add("CHK-N0-NO-DEMOS", not bad, len(bound),
          f"n_examples==0 rows carry an empty demo_block on {len(bound) - len(bad)}/{len(bound)}",
          "sidecar rows")

    # ---- CHK-FC-NAMES-CONCEPT: the forced-choice query NAMES the concept ------------------------
    bound = [r for r in rows if r["query_kind"] == "semantic_forced_choice"]
    bad = [r for r in bound if not r["concept_in_query"] or not r["codeword_in_query"]]
    C.add("CHK-FC-NAMES-CONCEPT", not bad, len(bound),
          f"semantic_forced_choice queries contain BOTH the concept and the codeword on "
          f"{len(bound) - len(bad)}/{len(bound)} rows; offenders={len(bad)}", "sidecar rows")

    # ---- CHK-ONEWORD-CONCEPT-FREE: the PRIMARY channel must not leak the concept ----------------
    # Scoped to codeword-surface cells (A, C, D, F): in cells B and E the surface word IS the
    # concept, so its presence in the query is by design, not a leak.
    bound = [r for r in rows if r["query_kind"] == "semantic_one_word"
             and r["surface_type"] == "codeword"]
    bad = [r for r in bound if r["concept_in_query"]]
    C.add("CHK-ONEWORD-CONCEPT-FREE", not bad, len(bound),
          f"semantic_one_word queries on codeword-surface cells are concept-free on "
          f"{len(bound) - len(bad)}/{len(bound)} rows; leaks={len(bad)}", "sidecar rows")

    bound = [r for r in rows if r["query_kind"] == "semantic_one_word"
             and r["surface_type"] == "concept"]
    bad = [r for r in bound if not r["concept_in_query"]]
    C.add("CHK-ONEWORD-CONCEPT-SURFACE", not bad, len(bound),
          f"semantic_one_word on concept-surface cells (B/E) DOES name the concept, by design, on "
          f"{len(bound) - len(bad)}/{len(bound)} rows", "sidecar rows")

    # ---- CHK-SURFACE-MATCHES-CELL ---------------------------------------------------------------
    bad = [r for r in rows
           if r["surface_word"] != (r["codeword"] if r["surface_type"] == "codeword"
                                    else r["concept"])]
    C.add("CHK-SURFACE-MATCHES-CELL", not bad, n,
          f"surface_word == codeword|concept as the condition table dictates on {n - len(bad)}/{n} "
          f"rows", "sidecar rows")

    # ---- CHK-CELL-COVERAGE ----------------------------------------------------------------------
    cells = collections.Counter(r["cell"] for r in rows)
    want = {"A", "B", "C", "E"}
    C.add("CHK-CELL-COVERAGE", set(cells) == want and len(set(cells.values())) == 1, n,
          f"cells present = {dict(cells)}; expected the four {sorted(want)} balanced", "sidecar rows")

    # ---- CHK-CELLC-PRESENT: the PRIMARY cell must be non-empty in every bank ---------------------
    per = collections.Counter(r["bank_stem"] for r in rows if r["cell"] == "C")
    C.add("CHK-CELLC-PRESENT",
          len(per) == len([b for b in banks if bankinfo.get(b, {}).get("present")])
          and len(set(per.values())) == 1,
          sum(per.values()), f"cell C rows per bank = {dict(per)}", "cell-C rows")

    # ---- CHK-INTENDED-MAPPING-TOTAL ---------------------------------------------------------------
    bad = [r for r in rows if not r["intended_mapping"]]
    C.add("CHK-INTENDED-MAPPING-TOTAL", not bad, n,
          f"every row has a declared intended_mapping; missing={len(bad)}", "sidecar rows")

    # ---- CHK-TOKEN-COLS-DECLARED-NULL -------------------------------------------------------------
    bad = [r for r in rows if any(r.get(c) is not None for c in TOKEN_COLUMNS)
           or r["token_fields_status"] != "DEFERRED_TO_TOKEN_ROLES_AGENT"]
    C.add("CHK-TOKEN-COLS-DECLARED-NULL", not bad, n,
          f"the {len(TOKEN_COLUMNS)} token columns are present-and-null with a named owner on "
          f"{n - len(bad)}/{n} rows (owner={TOKEN_ROLES_ARTIFACT})", "sidecar rows")

    # ---- CHK-STATUS-COLS-EMPTY ----------------------------------------------------------------------
    bad = [r for r in rows if r["exclusion_status"] != "" or r["exclusion_reasons"] != []
           or r["failure_status"] != "" or r["installation_status"] is not None]
    C.add("CHK-STATUS-COLS-EMPTY", not bad, n,
          f"exclusion/failure/installation columns exist and are empty on {n - len(bad)}/{n} rows",
          "sidecar rows")

    # ---- CHK-SCHEMA-RECTANGULAR ---------------------------------------------------------------------
    keysets = {tuple(sorted(r.keys())) for r in rows}
    ncols = len(next(iter(keysets))) if keysets else 0
    C.add("CHK-SCHEMA-RECTANGULAR", len(keysets) == 1, n,
          f"{len(keysets)} distinct key-sets across {n} rows ({ncols} columns)", "sidecar rows")

    return C


# ============================================================================================== #
# MUTATIONS.  ⛔ NEVER applied to a canonical bank -- that is forbidden and would change its sha.
#    Each mutation corrupts the SIDECAR TABLE or one of the two joined INPUTS, and names the check
#    it must turn RED.  A mutation whose target check stays green is itself a failure.
# ============================================================================================== #
MUTATIONS = {
    "keydup":        ("CHK-KEY-UNIQUE",       "copy row[1]'s join_key onto row[0]"),
    "nopidcollide":  ("CHK-PID-FANOUT",       "make every prompt_id globally unique, removing the "
                                              "hazard the sidecar exists to prevent"),
    "dsplit_missing": ("CHK-DSPLIT-TOTAL",    "delete one domain from the manifest assignment"),
    "dsplit_ambiguous": ("CHK-DSPLIT-TOTAL",  "assign one domain TWO different dsplit values "
                                              "(a duplicate JSON key, which json.load would hide)"),
    "dsplit_rownull": ("CHK-DSPLIT-ROWSTATUS", "null one row's dsplit"),
    "manifest_sha":  ("CHK-MANIFEST-SHA",     "perturb the manifest body so its sha no longer "
                                              "matches"),
    "spanshift":     ("CHK-TARGET-SPANS",     "shift one re-derived target span by +1 char"),
    "occcount":      ("CHK-OCCURRENCE-COUNTS", "bump one row's re-derived concept occurrence count"),
    "matcherunflag": ("CHK-MATCHER-DIVERGENCE", "clear the collision flag on one divergent row"),
    "vacuous_matcher": ("CHK-MATCHER-DIVERGENCE", "erase the whole-word/substring divergence -> "
                                                  "the check binds to zero rows and must go RED as "
                                                  "VACUOUS rather than pass over an empty set"),
    "queryspan":     ("CHK-QUERY-SPAN",       "mark one row's query span NOT_FOUND"),
    "demospan":      ("CHK-DEMO-SPAN",        "mark one n_examples>0 row's demo span NOT_FOUND"),
    "fcleak":        ("CHK-FC-NAMES-CONCEPT", "clear concept_in_query on one forced-choice row"),
    "oneword_leak":  ("CHK-ONEWORD-CONCEPT-FREE", "set concept_in_query on one codeword-surface "
                                                  "semantic_one_word row"),
    "rowssha":       ("CHK-BANK-ROWS-SHA-PIN", "perturb the pinned R-098 rows-sha for one bank"),
    "bankbytes":     ("CHK-BANK-IMMUTABLE",   "simulate the bank file changing under us by "
                                              "perturbing the post-read sha"),
    "tokenfill":     ("CHK-TOKEN-COLS-DECLARED-NULL", "fill a token column this script does not own"),
    "statusfill":    ("CHK-STATUS-COLS-EMPTY", "write into the exclusion column"),
    "raggedschema":  ("CHK-SCHEMA-RECTANGULAR", "drop a column from one row"),
    "surfaceswap":   ("CHK-SURFACE-MATCHES-CELL", "swap one row's surface_word"),
    "promptlen":     ("CHK-PROMPT-LEN",       "perturb one row's re-derived prompt length"),
    "vacuous_cellC": ("CHK-CELLC-PRESENT",    "delete every cell-C row -> the check must go RED as "
                                              "VACUOUS, not silently pass over an empty set"),
    "vacuous_oneword": ("CHK-ONEWORD-CONCEPT-FREE", "delete every codeword-surface "
                                                    "semantic_one_word row -> VACUOUS"),
    "vacuous_all":   ("CHK-KEY-UNIQUE",       "delete every row -> every check must go RED"),
}


def apply_mutation(name, rows, bankinfo, sha_before, sha_after, manifest, assign_pairs,
                   expected_rows_sha):
    """Return mutated copies. Shallow-copies only the rows it touches."""
    rows = list(rows)
    assign_pairs = list(assign_pairs)
    manifest = dict(manifest)
    expected_rows_sha = dict(expected_rows_sha)
    sha_after = dict(sha_after)

    def _first(pred):
        for i, r in enumerate(rows):
            if pred(r):
                return i
        raise SystemExit(f"MUTATION '{name}' could not bind: no row matches. "
                         f"A mutation that cannot bind proves nothing.")

    if name == "keydup":
        i = 0
        rows[i] = {**rows[i], "join_key": rows[1]["join_key"]}
    elif name == "nopidcollide":
        rows = [{**r, "prompt_id": f"{r['bank_stem']}:{r['prompt_id']}",
                 "join_key": f"{r['bank_sha']}:{r['bank_stem']}:{r['prompt_id']}"} for r in rows]
    elif name == "dsplit_missing":
        drop = assign_pairs[0][0]
        assign_pairs = [p for p in assign_pairs if p[0] != drop]
    elif name == "dsplit_ambiguous":
        d, v = assign_pairs[0]
        other = "test" if v != "test" else "train"
        assign_pairs = assign_pairs + [(d, other)]
    elif name == "dsplit_rownull":
        i = 0
        rows[i] = {**rows[i], "dsplit": None, "dsplit_status": "MISSING"}
    elif name == "manifest_sha":
        manifest["seed"] = int(manifest["seed"]) + 1
    elif name == "spanshift":
        i = _first(lambda r: r["target_char_spans"])
        s = [list(x) for x in rows[i]["target_char_spans"]]
        s[0][0] += 1
        rows[i] = {**rows[i], "target_char_spans": s, "target_spans_agree": False}
    elif name == "occcount":
        i = 0
        rows[i] = {**rows[i], "n_concept_occurrences_substring":
                   rows[i]["n_concept_occurrences_substring"] + 1,
                   "concept_occurrences_agree": False}
    elif name == "matcherunflag":
        i = _first(lambda r: r["lexical_collision_substring_only"])
        rows[i] = {**rows[i], "lexical_collision_substring_only": False}
    elif name == "vacuous_matcher":
        rows = [{**r, "n_codeword_occurrences_wholeword": r["n_codeword_occurrences_substring"],
                 "n_concept_occurrences_wholeword": r["n_concept_occurrences_substring"]}
                for r in rows]
    elif name == "queryspan":
        i = 0
        rows[i] = {**rows[i], "query_span_status": "NOT_FOUND", "query_span_char": None}
    elif name == "demospan":
        i = _first(lambda r: (r["n_examples"] or 0) > 0)
        rows[i] = {**rows[i], "demo_span_status": "NOT_FOUND", "demo_span_char": None}
    elif name == "fcleak":
        i = _first(lambda r: r["query_kind"] == "semantic_forced_choice")
        rows[i] = {**rows[i], "concept_in_query": False}
    elif name == "oneword_leak":
        i = _first(lambda r: r["query_kind"] == "semantic_one_word"
                   and r["surface_type"] == "codeword")
        rows[i] = {**rows[i], "concept_in_query": True}
    elif name == "rowssha":
        b = next(iter(expected_rows_sha))
        expected_rows_sha[b] = "0" * 16
    elif name == "bankbytes":
        b = next(iter(sha_after))
        sha_after[b] = "0" * 16
    elif name == "tokenfill":
        i = 0
        rows[i] = {**rows[i], TOKEN_COLUMNS[0]: [1, 2, 3]}
    elif name == "statusfill":
        i = 0
        rows[i] = {**rows[i], "exclusion_status": "excluded_for_no_reason"}
    elif name == "raggedschema":
        i = 0
        r = dict(rows[i])
        r.pop("template_family")
        rows[i] = r
    elif name == "surfaceswap":
        i = _first(lambda r: r["surface_type"] == "codeword")
        rows[i] = {**rows[i], "surface_word": rows[i]["surface_word"] + "x"}
    elif name == "promptlen":
        i = 0
        rows[i] = {**rows[i], "prompt_len_agree": False}
    elif name == "vacuous_cellC":
        rows = [r for r in rows if r["cell"] != "C"]
    elif name == "vacuous_oneword":
        rows = [r for r in rows if not (r["query_kind"] == "semantic_one_word"
                                        and r["surface_type"] == "codeword")]
    elif name == "vacuous_all":
        rows = []
    else:
        raise SystemExit(f"unknown mutation {name!r}")
    return rows, bankinfo, sha_before, sha_after, manifest, assign_pairs, expected_rows_sha


# ============================================================================================== #
def write_sidecar(rows, path):
    tmp = path + ".tmp"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with gzip.open(tmp, "wt") as f:
        for r in rows:
            f.write(json.dumps(r, separators=(",", ":")) + "\n")
    os.replace(tmp, path)
    return dict(path=os.path.relpath(path, REPO), n_rows=len(rows),
                bytes=os.path.getsize(path), sha16=dm.file_sha16(path))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--build", action="store_true", help="write the sidecar (default action)")
    ap.add_argument("--check-only", action="store_true", help="run checks, write nothing")
    ap.add_argument("--out", default=SIDECAR_OUT)
    ap.add_argument("--mutate", default=None,
                    help="a mutation name, or 'all', or 'list'")
    a = ap.parse_args(argv)

    if a.mutate == "list":
        for k, (tgt, desc) in MUTATIONS.items():
            print(f"{k:20s} -> {tgt:30s} {desc}")
        return 0

    print("building sidecar rows from the six ts116 banks (read-only)...", file=sys.stderr)
    rows, bankinfo, sha_before, sha_after, manifest, assign_pairs, prov = build_rows()
    print(f"built {len(rows)} sidecar rows", file=sys.stderr)

    C = run_checks(rows, bankinfo, sha_before, sha_after, manifest, assign_pairs)
    print("\n=== CHECKS (unmutated) ===")
    print(C.report())
    print(f"--- {len(C.results) - len(C.failed)}/{len(C.results)} PASS")

    rc = 0
    if C.failed:
        rc = 1
        print(f"!!! {len(C.failed)} CHECK(S) FAILED: {[r['id'] for r in C.failed]}")

    if a.mutate:
        names = list(MUTATIONS) if a.mutate == "all" else [a.mutate]
        print("\n=== MUTATION PROOFS ===")
        print("Mutations are injected into the SIDECAR TABLE and the joined inputs, NEVER into a")
        print("canonical bank (mutating a bank is forbidden and would change its rows sha).")
        red_ok = 0
        for nm in names:
            tgt, desc = MUTATIONS[nm]
            m = apply_mutation(nm, rows, bankinfo, sha_before, sha_after, manifest,
                               assign_pairs, EXPECTED_ROWS_SHA16)
            MC = run_checks(m[0], m[1], m[2], m[3], m[4], m[5], expected_rows_sha=m[6])
            hit = [r for r in MC.results if r["id"] == tgt]
            went_red = bool(hit) and hit[0]["status"] == "FAIL"
            reason = hit[0]["reason"] if hit else "CHECK_ABSENT"
            n_red = len(MC.failed)
            red_ok += bool(went_red)
            print(f"  {'RED  ' if went_red else 'GREEN'}  {nm:18s} target={tgt:30s} "
                  f"reason={reason:10s} total_failing={n_red:2d}   ({desc})")
            if not went_red:
                rc = 1
        print(f"--- {red_ok}/{len(names)} mutations turned their target check RED")
        if red_ok != len(names):
            print("!!! a mutation that does not turn its check red proves the check is inert")

    if a.check_only:
        return rc
    if C.failed:
        print("\nREFUSING to write the sidecar while a check is failing.", file=sys.stderr)
        return rc
    info = write_sidecar(rows, a.out)
    print(f"\nwrote {info['path']}  n_rows={info['n_rows']}  "
          f"bytes={info['bytes']}  file_sha16={info['sha16']}")
    # a machine-readable one-liner for the README / the caller
    print("SIDECAR_INFO " + json.dumps(info))
    return rc


if __name__ == "__main__":
    sys.exit(main())
