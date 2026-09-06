#!/usr/bin/env python
"""dcs_metadata_sidecar.py -- DCS phase 2: the DECLARED-DESIGN metadata sidecar, and the
Sec-19 PROMPT-VALIDATION TABLE.

=================================================================================================
WHAT THIS IS, AND WHAT IT REUSES RATHER THAN REWRITES
=================================================================================================
`src/boombness/dcs_metadata.py` already exists and already solves most of this problem: it emits a
per-bank-row sidecar joinable on `(bank_file_sha16, prompt_id)`, it already refuses to touch the
bank bytes, and it already carries a mechanical ambiguity-rule layer.  This module **imports it and
builds on top of it**.  It does NOT re-derive what that module derives.

  REUSED VERBATIM from `src/boombness/dcs_metadata.py`:
      load_bank()          bank + *_meta.json + pools loading, bank_file_sha16, bank_rows_sha16
      derive_row()         the whole Sec-1.3 field set (surface_word, benign_concept, template ids,
                           masked-prompt hash, ambiguity rules, ...)
      sha16() / file_sha16() / _tbl()
      AMBIGUITY_RULES, CONTEXT_KIND_MAP, BANK_DIR, REPO_ROOT
  REUSED from `src/boombness/prompt_families.py`:
      CONDITIONS (the cell/valence/surface design table), QUERY_KINDS, _surface_word,
      mapping_statement, DISTRACTOR_CODEWORD
  REUSED from `src/boombness/demo_pools.py`:
      REMAP_SOURCE_WORD  (cell F's actually-installed word: "bicycle")
  REUSED from `src/boombness/common.py`:
      read_jsonl

  WHAT IS NEW HERE, and why `dcs_metadata.py` did not already have it:
    1. The DECLARED-vs-OBSERVED split.  `dcs_metadata.derive_row` copies `concept` into
       `harmful_concept` and asserts `concept == target_semantic`.  That assertion is TRUE and
       USELESS: `prompt_families.py:572` writes `"target_semantic": concept` unconditionally, so
       the two agree on 21,888/21,888 rows BY CONSTRUCTION.  It is therefore not evidence about
       any row, and it is FALSE as a description of what the demonstrations install in cells
       A, D, E and F.  This module adds `demonstration_target_concept` and the DECLARED_CELL_DESIGN
       table, derived from `build_demo_block`'s own branches, and marks `target_semantic` as
       non-authoritative in every row it emits.
    2. The compound-key COLLISION TESTS (Sec 1 below), which must FAIL if anyone joins on
       `prompt_id` alone.
    3. The join to the R-078 installation readouts on disk, and the Sec-19 validation table.

=================================================================================================
1. THE JOIN KEY.  ⛔ `prompt_id` ALONE IS NOT A KEY.
=================================================================================================
Measured on the 8 core banks (button_/basket_ x bomb/knife/gun/club), 21,888 rows:

    distinct prompt_id                       2,736
    multiplicity of every prompt_id          EXACTLY 8   (one row per bank)
    distinct (bank_file_sha16, prompt_id)   21,888       <- unique
    duplicate-excess on prompt_sha16         5,020       <- NOT a fallback key either

`prompt_id` is a hash of the DESIGN AXES only, so the same design cell in eight different lexical
banks gets the same id.  A join on `prompt_id` alone silently produces an 8x cross-bank fan-out --
`button_bomb` rows joined to `basket_club` readouts.  `TEST_KEY_*` below fails loudly on exactly
that, and `--self-test` proves each test can go red.

=================================================================================================
2. ⛔ THE BANKS ARE NEVER OPENED FOR WRITING.
=================================================================================================
Every bank .jsonl is opened 'r' only.  Changing bank bytes changes `bank_rows_sha16` and breaks
every result-to-bank join in the repository.  This module writes at most two things, both opt-in
or explicitly requested: the markdown report at `--report-out`, and (only if `--sidecar-out` is
given) the sidecar JSONL.  It creates no RunDir and no other artifact.

=================================================================================================
3. FLOOR / CEILING, defined before any number is looked at
=================================================================================================
The forced-choice readout is a two-option contest between `p_concept` and `p_codeword` inside
`option_mass`.  Three saturation states, all mechanical:
    mass_floor    option_mass < the RUN'S OWN `min_option_mass` (read from its config.json, 0.05).
                  The readout is not reportable on that row -- R-050's phase-wide limit.
    at_ceiling    p_concept / (p_concept + p_codeword) >= 0.99   (concept side saturated)
    at_floor      p_concept / (p_concept + p_codeword) <= 0.01   (codeword side saturated)
No other constant is introduced.

Usage
-----
  python scripts/dcs_metadata_sidecar.py --self-test
  python scripts/dcs_metadata_sidecar.py --report-out reports/DCS_PROMPT_VALIDATION_TABLE.md
  python scripts/dcs_metadata_sidecar.py --sidecar-out /tmp/side.jsonl --report-out /dev/null
"""
from __future__ import annotations

import argparse
import collections
import glob
import json
import os
import statistics as st
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.dirname(_HERE)
sys.path.insert(0, os.path.join(_REPO, "src", "boombness"))

import common                                        # noqa: E402
import dcs_metadata as dm                            # noqa: E402  *** the module we build on ***
import demo_pools                                    # noqa: E402
import prompt_families as pf                         # noqa: E402

REPO_ROOT = dm.REPO_ROOT
BANK_DIR = dm.BANK_DIR

#: Sec-19's core populations, fixed here rather than discovered from disk.
CORE_BANKS = ("button_bomb", "button_knife", "button_gun", "button_club",
              "basket_bomb", "basket_knife", "basket_gun", "basket_club")
CORE_CELLS = ("A", "B", "C", "E", "F")
CORE_QUERY_KINDS = ("semantic_one_word", "semantic_forced_choice")
CORE_N_EXAMPLES = (0, 1, 2, 4, 8, 16)

#: R-078's installation readouts.  Sec 19 says: join where one ALREADY EXISTS on disk.
INST_GLOB = os.path.join(REPO_ROOT, "outputs", "boombness", "score_behavior", "inst_*")

#: Saturation constant (Sec 3 of the docstring).  The only one this file introduces.
SATURATION_Q = 0.99

MODEL_TOKENIZERS_TRIED: dict = {}


# ============================================================================================= #
# DECLARED DESIGN.  What the BANK DESIGN says each cell installs -- NOT what the model output is.
# ============================================================================================= #
# Every entry is traceable to a line of the generator, cited in `basis`.  Nothing here is inferred
# from a result, and nothing here is read off `target_semantic`.
#
#   demo_target := what the DEMONSTRATIONS teach the rendered demo-surface word to denote.
#                  Derived from `prompt_families.build_demo_block` (:375-425) branch by branch:
#                    benign_remap        -> demo_pools.REMAP_SOURCE_WORD          ("bicycle")
#                    consistency=mixed   -> AMBIGUOUS (half harm, half benign)
#                    consistency=irrelevant -> the DISTRACTOR word, not the query word
#                    otherwise           -> pools[f"{domain}|{demo_valence}"]["natural_word"]
#   remap_intended := does the DESIGN intend the demonstrations to install a NEW referent for the
#                     word the QUERY asks about?
DECLARED_CELL_DESIGN = {
    "A": dict(
        condition="benign_literal",
        remap_intended=False,
        remap_direction="none",
        installs_harmful_concept=False,
        mapping_stated_by_default=False,
        basis="prompt_families.CONDITIONS:95 + build_demo_block:419-425",
        note=("benign-valence pool sentences with the pool's natural word substituted onto the "
              "CODEWORD, so the codeword is used in its ordinary benign domain sense.  R-050 uses "
              "this cell as the genuine no-mapping reference (-5.495 vs C's +5.188).  "
              "⛔ target_semantic says 'bomb' here and that is FALSE for this cell: the "
              "demonstrations install the benign pool word (button_bomb: 'carrot')."),
    ),
    "B": dict(
        condition="direct_harmful",
        remap_intended=False,
        remap_direction="none",
        installs_harmful_concept=False,
        mapping_stated_by_default=False,
        basis="prompt_families.CONDITIONS:96 + build_demo_block:419-425",
        note=("harm-valence pool sentences, demo surface = the CONCEPT word, so `natural == want` "
              "and NO substitution happens.  The concept word is used literally.  This is the "
              "cell whose surface word IS the concept -- C-050 Sec 25.2 exempts it from the "
              "concept-word exclusion for exactly that reason."),
    ),
    "C": dict(
        condition="natural_doublespeak",
        remap_intended=True,
        remap_direction="codeword -> harmful_concept",
        installs_harmful_concept=True,
        mapping_stated_by_default=False,
        basis="prompt_families.CONDITIONS:97 + build_demo_block:419-425",
        note=("harm-valence sentences with the CONCEPT word substituted onto the CODEWORD: the "
              "demonstrations teach codeword = concept.  This is the only cell in which the "
              "phase's target mapping is DEMONSTRATED."),
    ),
    "D": dict(
        condition="direct_codeword",
        remap_intended=True,
        remap_direction="codeword -> harmful_concept (STATED, NOT DEMONSTRATED)",
        installs_harmful_concept=True,
        mapping_stated_by_default=True,
        basis="prompt_families.CONDITIONS:100 + build_prompt:459-462 (forces strength='strong')",
        note=("⛔ the DEMONSTRATIONS here are cell A's benign ones (demo_valence='benign'); only a "
              "mapping_statement sentence asserts codeword = concept.  So "
              "demonstration_target_concept is the BENIGN pool word, not the concept, and "
              "target_semantic='bomb' is FALSE as a description of this cell's demonstrations."),
    ),
    "E": dict(
        condition="concept_in_benign_ctx",
        remap_intended=False,
        remap_direction="none (but a lexical substitution IS applied: benign_word -> concept)",
        installs_harmful_concept=False,
        mapping_stated_by_default=False,
        basis="prompt_families.CONDITIONS:98 + build_demo_block:419-425",
        note=("benign-valence sentences with the BENIGN pool word substituted onto the CONCEPT "
              "word.  The 2x2 treats this as the surface x context control, not an installation. "
              "⚠ Stated honestly rather than hidden: a substitution DOES occur here, and the "
              "demonstrations describe a benign object using the concept word.  A reader who "
              "wants to call that 'a remapping of the concept word' can: "
              "demo_lexical_substitution records it row by row."),
    ),
    "F": dict(
        condition="benign_remap",
        remap_intended=True,
        remap_direction="codeword -> benign_alternative",
        installs_harmful_concept=False,
        mapping_stated_by_default=False,
        basis="prompt_families.build_demo_block:383-397 + demo_pools.py:1329 REMAP_SOURCE_WORD",
        note=("⛔ THIS CELL INSTALLS BICYCLE BY CONSTRUCTION.  The demo block is the domain's "
              "`|remap` pool -- sentences about demo_pools.REMAP_SOURCE_WORD ('bicycle') -- with "
              "that word substituted onto the codeword, so the demonstrations teach "
              "codeword = bicycle.  target_semantic='bomb' is FALSE for every row of this cell.  "
              "It is the same remapping OPERATION as cell C with a harmless taught meaning, which "
              "is what makes it the generic-remapping comparator."),
    ),
}

SURFACE_TYPE = {"codeword": "codeword", "concept": "explicit_concept"}


# ============================================================================================= #
# per-row declared-design derivation
# ============================================================================================= #
def declared_fields(row: dict, ctx: dict) -> dict:
    """Pure function of (bank row, bank context).  No I/O.  No result is consulted."""
    cell = row.get("cell")
    design = DECLARED_CELL_DESIGN.get(cell)
    codeword = row.get("codeword")
    concept = row.get("concept")
    domain = row.get("demo_pool_domain")
    n_ex = row.get("n_examples")
    demo_valence = row.get("demo_valence")
    demo_surface = row.get("demo_surface")
    consistency = row.get("consistency")
    strength = row.get("strength")

    pools = ctx.get("pools") or {}
    benign_word = (pools.get(f"{domain}|benign") or {}).get("natural_word")
    harm_word = (pools.get(f"{domain}|harm") or {}).get("natural_word")
    remap_word = (pools.get(f"{domain}|remap") or {}).get("natural_word")

    # --- what the demonstrations actually teach (build_demo_block branch order, verbatim) ------
    ambiguous_demo = []
    if not n_ex:
        demo_target = None
        demo_target_status = "NONE_NO_DEMONSTRATIONS"
    elif row.get("condition") == "benign_remap":
        demo_target = remap_word or demo_pools.REMAP_SOURCE_WORD
        demo_target_status = "REMAP_POOL"
    elif consistency == "irrelevant":
        demo_target = harm_word
        demo_target_status = "DISTRACTOR_%s_NOT_THE_QUERY_WORD" % pf.DISTRACTOR_CODEWORD
        ambiguous_demo.append("AMB-DEMO-IRRELEVANT")
    elif consistency == "mixed":
        demo_target = None
        demo_target_status = "MIXED_%s_AND_%s" % (harm_word, benign_word)
        ambiguous_demo.append("AMB-DEMO-MIXED")
    else:
        demo_target = (pools.get(f"{domain}|{demo_valence}") or {}).get("natural_word")
        demo_target_status = "POOL_NATURAL_WORD"
        if demo_target is None:
            ambiguous_demo.append("AMB-DEMO-POOL-MISSING")

    rendered = pf._surface_word(demo_surface, codeword, concept) if demo_surface else None
    subst = None
    if demo_target is not None and rendered is not None and demo_target != rendered:
        subst = f"{demo_target}->{rendered}"

    stated = bool(pf.mapping_statement(strength, str(codeword), str(concept))) if strength else False
    if row.get("condition") == "direct_codeword" and strength == "none":
        stated = True                                   # build_prompt:459-462 forces it

    spans = row.get("expected_target_occurrences") or []
    n_occ = row.get("n_target_occurrences")

    out = {
        # ---- identity / provenance -----------------------------------------------------------
        "bank_id": ctx["stem"],
        "lexical_pair": f"{codeword}_{concept}",
        "source_artifact_path": ctx["bank_path"],
        "source_artifact_sha16": ctx["bank_file_sha16"],
        "source_pools_path": ctx.get("pools_path"),
        "source_pools_sha16": ctx.get("pools_sha16"),
        # ---- surface -------------------------------------------------------------------------
        "surface_type": SURFACE_TYPE.get(row.get("query_surface")),
        "demo_surface_type": SURFACE_TYPE.get(demo_surface),
        # ---- DECLARED design (never derived from target_semantic) ------------------------------
        "declared_benign_concept": benign_word,
        "declared_harm_pool_word": harm_word,
        "demonstration_target_concept": demo_target,
        "demonstration_target_status": demo_target_status,
        "demonstration_valence": demo_valence,          # raw: benign | harm | remap | mixed
        "demo_rendered_surface_word": rendered,
        "demo_lexical_substitution": subst or "none",
        "declared_remapping_intended": None if design is None else design["remap_intended"],
        "declared_remap_direction": None if design is None else design["remap_direction"],
        "declared_installs_harmful_concept": (None if design is None
                                              else design["installs_harmful_concept"]),
        "declared_design_basis": None if design is None else design["basis"],
        "declared_mapping_statement_present": stated,
        "template_family": row.get("bank_block"),
        # ---- ⛔ target_semantic is recorded, and marked non-authoritative -----------------------
        "target_semantic_raw": row.get("target_semantic"),
        "target_semantic_is_per_row_label": False,
        "target_semantic_equals_concept": row.get("target_semantic") == concept,
        # ---- occurrence ------------------------------------------------------------------------
        "n_target_occurrences": n_occ,
        "target_occurrence_char_spans": spans,
        # the readout position is the FINAL occurrence of the target surface word.
        "target_occurrence_index_readout": (int(n_occ) - 1) if n_occ else None,
        "occurrence_analysis_safe": row.get("occurrence_analysis_safe"),
        # ---- observed (filled only by an actual run; NEVER invented) ----------------------------
        "model": None,
        "target_decoded_text": None,
        "observed_semantic_logodds": None,
        "observed_option_mass": None,
        "observed_status": "ABSENT_NO_RUN_CONTEXT",
        "readout_run_dir": None,
        "readout_run_results_sha16": None,
        "ambiguous_demo_reasons": ambiguous_demo,
    }
    return out


def build_sidecar(banks=CORE_BANKS, verbose=False) -> tuple:
    """Sidecar rows for every row of every named bank.  Banks are opened READ-ONLY."""
    rows, ctxs, missing = [], {}, []
    for stem in banks:
        ctx = dm.load_bank(stem)                     # <- REUSED
        if not ctx.get("present"):
            missing.append(stem)
            continue
        ctxs[stem] = ctx
        for r in ctx["rows"]:
            base = dm.derive_row(r, ctx)             # <- REUSED: the whole Sec-1.3 field set
            base.update(declared_fields(r, ctx))
            rows.append(base)
        if verbose:
            print(f"  {stem:16s} {ctx['n_rows']:6d} rows  file_sha16={ctx['bank_file_sha16']}")
    return rows, ctxs, missing


# ============================================================================================= #
# THE KEY TESTS.  Each returns (name, passed, detail).  Each MUST be able to fail.
# ============================================================================================= #
class KeyTestFailure(AssertionError):
    pass


def key_tests(rows: list) -> list:
    out = []

    pid = collections.Counter(r["prompt_id"] for r in rows)
    compound = collections.Counter((r["bank_file_sha16"], r["prompt_id"]) for r in rows)
    psha = collections.Counter(r["prompt_sha16"] for r in rows)
    n_banks = len({r["bank_file_sha16"] for r in rows})

    # T-KEY-1 -- prompt_id alone is NOT unique.  This test PASSES by observing the collision.
    collide = sum(1 for v in pid.values() if v > 1)
    out.append(("T-KEY-1_prompt_id_is_NOT_unique", collide > 0,
                f"{len(pid)} distinct prompt_id over {len(rows)} rows; "
                f"{collide} ids appear more than once; "
                f"multiplicity histogram={dict(collections.Counter(pid.values()))}"))

    # T-KEY-2 -- the compound key IS unique.  A duplicate here means the sidecar itself is broken.
    dup = [k for k, v in compound.items() if v > 1]
    out.append(("T-KEY-2_compound_key_IS_unique", not dup,
                f"{len(compound)} distinct (bank_file_sha16, prompt_id) over {len(rows)} rows"
                + (f"; DUPLICATES: {dup[:3]}" if dup else "")))

    # T-KEY-3 -- prompt_sha16 is NOT a fallback key.
    excess = sum(v - 1 for v in psha.values() if v > 1)
    out.append(("T-KEY-3_prompt_sha16_is_NOT_a_fallback", excess > 0,
                f"{len(psha)} distinct prompt_sha16 over {len(rows)} rows; "
                f"duplicate-excess={excess}"))

    # T-KEY-4 -- ⛔ THE LOAD-BEARING ONE.  A join on prompt_id alone fans out ACROSS BANKS.
    #            Simulate the wrong join and show it produces cross-bank contamination.
    by_pid = collections.defaultdict(set)
    for r in rows:
        by_pid[r["prompt_id"]].add(r["bank_id"])
    contaminated = sum(1 for v in by_pid.values() if len(v) > 1)
    worst = max((len(v) for v in by_pid.values()), default=0)
    out.append(("T-KEY-4_prompt_id_join_CONTAMINATES_across_banks", contaminated > 0,
                f"{contaminated}/{len(by_pid)} prompt_ids map to >1 bank; worst fan-out={worst} "
                f"banks (n_banks={n_banks}).  ⛔ joining a result to a bank on prompt_id alone "
                f"multiplies every row {worst}x and mixes lexical banks."))

    # T-KEY-5 -- within a single bank, prompt_id IS unique (so the compound key is minimal).
    per_bank = collections.Counter((r["bank_id"], r["prompt_id"]) for r in rows)
    bad = [k for k, v in per_bank.items() if v > 1]
    out.append(("T-KEY-5_prompt_id_unique_WITHIN_a_bank", not bad,
                f"max within-bank multiplicity={max(per_bank.values(), default=0)}"))

    # T-SEM-1 -- target_semantic agrees with concept on EVERY row => it carries no information.
    agree = sum(1 for r in rows if r["target_semantic_equals_concept"])
    out.append(("T-SEM-1_target_semantic_is_uninformative", agree == len(rows),
                f"target_semantic == concept on {agree}/{len(rows)} rows "
                f"(prompt_families.py:572 sets it unconditionally) => it is NOT a per-row "
                f"semantic label and no DECLARED field may be derived from it"))

    # T-SEM-2 -- and it is DEMONSTRABLY WRONG about what cells A/D/E/F install.
    wrong = [r for r in rows
             if r["cell"] in ("A", "D", "E", "F")
             and r["demonstration_target_concept"] is not None
             and r["demonstration_target_concept"] != r["target_semantic_raw"]]
    out.append(("T-SEM-2_target_semantic_is_FALSE_for_cells_A_D_E_F", len(wrong) > 0,
                f"{len(wrong)} rows in cells A/D/E/F whose demonstrations install "
                f"{sorted({r['demonstration_target_concept'] for r in wrong})} "
                f"while target_semantic says "
                f"{sorted({r['target_semantic_raw'] for r in wrong})}"))

    # T-SEM-3 -- cell F installs REMAP_SOURCE_WORD, by construction.
    fr = [r for r in rows if r["cell"] == "F" and r["n_examples"]]
    ok_f = bool(fr) and all(r["demonstration_target_concept"] == demo_pools.REMAP_SOURCE_WORD
                            for r in fr)
    out.append(("T-SEM-3_cell_F_installs_REMAP_SOURCE_WORD", ok_f,
                f"{len(fr)} cell-F rows with demonstrations; installed word(s)="
                f"{sorted({r['demonstration_target_concept'] for r in fr})}; "
                f"demo_pools.REMAP_SOURCE_WORD={demo_pools.REMAP_SOURCE_WORD!r}"))

    # T-BANK-1 -- bank_rows_sha16 as recomputed matches what the bank's own meta claims.
    return out


def bank_integrity_tests(ctxs: dict) -> list:
    out = []
    bad = []
    for stem, c in ctxs.items():
        claimed = c.get("bank_rows_sha16_claimed")
        if claimed is not None and claimed != c["bank_rows_sha16"]:
            bad.append((stem, claimed, c["bank_rows_sha16"]))
    out.append(("T-BANK-1_bank_rows_sha16_matches_meta", not bad,
                f"{len(ctxs)} banks checked" + (f"; MISMATCH {bad}" if bad else "")))
    return out


def assert_tests(tests, label="tests"):
    failed = [t for t in tests if not t[1]]
    if failed:
        raise KeyTestFailure(f"{label}: {len(failed)} FAILED -> "
                             + "; ".join(f"{n}: {d}" for n, _, d in failed))


# ============================================================================================= #
# JOIN to the R-078 installation readouts that already exist on disk
# ============================================================================================= #
def _decode_top1(model_name: str, ids: list) -> dict:
    """top1_id -> text, offline.  Returns {} (and says so) if the tokenizer is unreachable."""
    if model_name in MODEL_TOKENIZERS_TRIED:
        tok = MODEL_TOKENIZERS_TRIED[model_name]
    else:
        tok = None
        try:
            os.environ.setdefault("HF_HUB_OFFLINE", "1")
            for root in ("/home/sharifm/students/omeryosef/.cache/huggingface",
                         os.path.expanduser("~/.cache/huggingface")):
                if os.path.isdir(os.path.join(root, "hub")):
                    os.environ.setdefault("HF_HOME", root)
                    break
            from transformers import AutoTokenizer
            tok = AutoTokenizer.from_pretrained(model_name)
        except Exception as e:                                       # never fatal
            print(f"  [decode] tokenizer for {model_name} UNAVAILABLE ({type(e).__name__}); "
                  f"target_decoded_text will be null and reported as such")
            tok = None
        MODEL_TOKENIZERS_TRIED[model_name] = tok
    if tok is None:
        return {}
    return {int(i): tok.decode([int(i)]) for i in sorted({int(x) for x in ids if x is not None})}


def load_inst_runs(pattern=INST_GLOB) -> list:
    """Every R-078 gate run on disk, with its bank resolved to a bank_file_sha16."""
    runs = []
    for d in sorted(glob.glob(pattern)):
        cfg_p = os.path.join(d, "config.json")
        res_p = os.path.join(d, "results.jsonl")
        if not (os.path.exists(cfg_p) and os.path.exists(res_p)):
            continue
        cfg = json.load(open(cfg_p))
        a = cfg.get("args", {})
        bank_path = a.get("bank") or ""
        runs.append({
            "run_dir": os.path.abspath(d),
            "run_id": cfg.get("run_id"),
            "arm": a.get("arm"),
            "model": a.get("model"),
            "bank_path": bank_path,
            "bank_stem": os.path.basename(bank_path).replace(
                "boombness_prompt_bank_", "").replace(".jsonl", ""),
            "bank_file_sha16": dm.file_sha16(bank_path) if os.path.exists(bank_path) else None,
            "results_sha16": dm.file_sha16(res_p),
            "min_option_mass": a.get("min_option_mass"),
            "query_kinds": a.get("query_kinds"),
            "conditions": a.get("conditions"),
            "n_examples": a.get("n_examples"),
            "bank_blocks": a.get("bank_blocks"),
            "intervene": a.get("intervene") or "",
            "done": os.path.exists(os.path.join(d, "DONE.json")),
            "rows": common.read_jsonl(res_p),                        # <- REUSED
        })
    return runs


def join_readouts(side_rows: list, runs: list) -> dict:
    """⛔ Joins ONLY on (bank_file_sha16, prompt_id).  Returns join diagnostics."""
    index = {(r["bank_file_sha16"], r["prompt_id"]): r for r in side_rows}
    if len(index) != len(side_rows):
        raise KeyTestFailure("sidecar compound key is not unique -- refusing to join")

    all_ids = [rr.get("top1_id") for run in runs for rr in run["rows"]]
    models = {run["model"] for run in runs}
    decoded = {}
    for m in models:
        decoded.update(_decode_top1(m, all_ids))

    diag = {"runs": [], "n_joined": 0, "n_unmatched": 0, "decoder_available": bool(decoded)}
    for run in runs:
        if not run["done"]:
            diag["runs"].append({"run_id": run["run_id"], "status": "SKIPPED_NOT_DONE"})
            continue
        if run["bank_file_sha16"] is None:
            diag["runs"].append({"run_id": run["run_id"], "status": "SKIPPED_BANK_MISSING"})
            continue
        matched = unmatched = 0
        for rr in run["rows"]:
            key = (run["bank_file_sha16"], rr.get("prompt_id"))
            side = index.get(key)
            if side is None:
                unmatched += 1
                continue
            matched += 1
            side["model"] = run["model"]
            side["observed_semantic_logodds"] = rr.get("semantic_logodds")
            side["observed_option_mass"] = rr.get("option_mass")
            side["observed_p_concept"] = rr.get("p_concept")
            side["observed_p_codeword"] = rr.get("p_codeword")
            side["observed_top1_id"] = rr.get("top1_id")
            side["target_decoded_text"] = decoded.get(int(rr["top1_id"])) \
                if rr.get("top1_id") is not None else None
            side["observed_status"] = "JOINED"
            side["readout_run_dir"] = run["run_dir"]
            side["readout_run_results_sha16"] = run["results_sha16"]
            side["readout_arm"] = run["arm"]
            side["readout_min_option_mass"] = run["min_option_mass"]
            # saturation flags, Sec 3 of the docstring
            pc, pw = rr.get("p_concept"), rr.get("p_codeword")
            frac = (pc / (pc + pw)) if (pc is not None and pw is not None and (pc + pw) > 0) else None
            side["observed_concept_share"] = frac
            side["observed_at_ceiling"] = (frac is not None and frac >= SATURATION_Q)
            side["observed_at_floor"] = (frac is not None and frac <= (1.0 - SATURATION_Q))
            side["observed_mass_floor"] = (rr.get("option_mass") is not None
                                           and run["min_option_mass"] is not None
                                           and rr["option_mass"] < run["min_option_mass"])
        diag["n_joined"] += matched
        diag["n_unmatched"] += unmatched
        diag["runs"].append({"run_id": run["run_id"], "arm": run["arm"],
                             "bank": run["bank_stem"], "model": run["model"],
                             "bank_file_sha16": run["bank_file_sha16"],
                             "results_sha16": run["results_sha16"],
                             "n_rows": len(run["rows"]), "matched": matched,
                             "unmatched": unmatched, "status": "OK"})
    return diag


# ============================================================================================= #
# R-078 REPRODUCTION.  The published table must come back out of the same files, to the digit.
# ============================================================================================= #
#: R-078 Sec 21, as published.  bank -> (cellA_mean, cellC_mean, delta, domains_plus, omA, omC)
R078_PUBLISHED = {
    "button_bomb":  (-7.272, +5.812, +13.084, 6, 0.146, 0.836),
    "button_club":  (-1.941, +4.494, +6.435, 6, 0.125, 0.388),
    "button_knife": (-2.022, +2.068, +4.089, 6, 0.296, 0.752),
    "button_gun":   (-3.692, +0.406, +4.098, 4, 0.136, 0.451),
}
#: ⚠ Discovered, not assumed: R-078's "domains +" column is the count of domains whose PAIRED
#: per-domain (C - A) mean is > 0, and its option_mass column is the MEDIAN, not the mean.  Both
#: were established by reproducing all four published rows exactly; the alternative rule
#: "domain cell-C mean > 0" gives 6/5/5/3 and does NOT reproduce the published 6/6/6/4.
R078_DOMAINS_RULE = "count of domains with paired per-domain mean(C) - mean(A) > 0"
R078_OM_RULE = "MEDIAN option_mass per cell (not the mean)"


def r078_reproduce(runs: list) -> list:
    out = []
    for run in runs:
        if not run["done"]:
            continue
        by_cell = collections.defaultdict(list)
        by_cell_dom = collections.defaultdict(lambda: collections.defaultdict(list))
        om = collections.defaultdict(list)
        for r in run["rows"]:
            by_cell[r["cell"]].append(r["semantic_logodds"])
            om[r["cell"]].append(r["option_mass"])
            by_cell_dom[r["cell"]][r["domain"]].append(r["semantic_logodds"])
        if "A" not in by_cell or "C" not in by_cell:
            continue
        a, c = st.mean(by_cell["A"]), st.mean(by_cell["C"])
        doms = sorted(set(by_cell_dom["C"]) & set(by_cell_dom["A"]))
        plus = sum(1 for d in doms
                   if st.mean(by_cell_dom["C"][d]) - st.mean(by_cell_dom["A"][d]) > 0)
        rec = {"bank": run["bank_stem"], "run_id": run["run_id"], "n_rows": len(run["rows"]),
               "A_mean": a, "C_mean": c, "delta": c - a,
               "domains_plus": plus, "n_domains": len(doms),
               "omA_median": st.median(om["A"]), "omC_median": st.median(om["C"]),
               "omA_mean": st.mean(om["A"]), "omC_mean": st.mean(om["C"])}
        pub = R078_PUBLISHED.get(run["bank_stem"])
        if pub:
            rec["published"] = pub
            rec["reproduces"] = (round(a, 3) == pub[0] and round(c, 3) == pub[1]
                                 and round(c - a, 3) == pub[2] and plus == pub[3]
                                 and round(rec["omA_median"], 3) == pub[4]
                                 and round(rec["omC_median"], 3) == pub[5])
        else:
            rec["published"] = None
            rec["reproduces"] = None
        out.append(rec)
    return out


# ============================================================================================= #
# Sec 19 -- THE PROMPT-VALIDATION TABLE
# ============================================================================================= #
def in_core_population(r: dict) -> bool:
    return (r["bank_id"] in CORE_BANKS
            and r["cell"] in CORE_CELLS
            and r["query_kind"] in CORE_QUERY_KINDS
            and r["n_examples"] in CORE_N_EXAMPLES)


def _q(vals, p):
    if not vals:
        return None
    s = sorted(vals)
    if len(s) == 1:
        return s[0]
    i = p * (len(s) - 1)
    lo, hi = int(i), min(int(i) + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (i - lo)


def summarise(rows: list) -> dict:
    joined = [r for r in rows if r["observed_status"] == "JOINED"]
    lo = [r["observed_semantic_logodds"] for r in joined
          if r["observed_semantic_logodds"] is not None]
    om = [r["observed_option_mass"] for r in joined if r["observed_option_mass"] is not None]
    out = {"n_rows": len(rows), "n_readout": len(joined)}
    if lo:
        out.update({
            "lo_mean": st.mean(lo), "lo_median": st.median(lo),
            "lo_p10": _q(lo, 0.10), "lo_p90": _q(lo, 0.90),
            "lo_min": min(lo), "lo_max": max(lo),
            "lo_frac_pos": sum(1 for v in lo if v > 0) / len(lo),
            "om_median": st.median(om) if om else None,
            "om_p10": _q(om, 0.10), "om_p90": _q(om, 0.90),
            "frac_mass_floor": sum(1 for r in joined if r.get("observed_mass_floor")) / len(joined),
            "frac_at_ceiling": sum(1 for r in joined if r.get("observed_at_ceiling")) / len(joined),
            "frac_at_floor": sum(1 for r in joined if r.get("observed_at_floor")) / len(joined),
        })
        dec = [r["target_decoded_text"] for r in joined if r.get("target_decoded_text")]
        if dec:
            top = collections.Counter(d.strip() for d in dec).most_common(4)
            out["argmax_top"] = top
            out["argmax_n"] = len(dec)
    return out


def _fmt(v, nd=3):
    if v is None:
        return "--"
    if isinstance(v, float):
        return f"{v:+.{nd}f}" if abs(v) < 1e6 else str(v)
    return str(v)


def _pct(v):
    return "--" if v is None else f"{100.0 * v:.0f}%"


def build_report(side_rows, ctxs, tests, bank_tests, join_diag, runs, repro, out_path):
    core = [r for r in side_rows if in_core_population(r)]
    L = []
    A = L.append

    A("# DCS — PROMPT-VALIDATION TABLE (plan §14.5 / brief §19)")
    A("")
    A("Generated by `scripts/dcs_metadata_sidecar.py`. Every number below is recomputed from the "
      "bank `.jsonl` files and the run artifacts named in §5; nothing is copied from the log.")
    A("")
    A("> ⛔ **No bank file was opened for writing.** This is a sidecar. Changing bank bytes would "
      "change `bank_rows_sha16` and break every result-to-bank join in the repository.")
    A("")

    # ---------------- 0. the join key ---------------------------------------------------------
    A("## §0 — ⛔ THE JOIN KEY IS COMPOUND. `prompt_id` ALONE IS NOT A KEY.")
    A("")
    A("| test | verdict | detail |")
    A("|---|---|---|")
    for name, ok, detail in tests + bank_tests:
        A(f"| `{name}` | {'✅ PASS' if ok else '⛔ **FAIL**'} | {detail} |")
    A("")
    A("**The rule, stated so it can be violated loudly:** every join between a result row and a "
      "bank row in this phase MUST key on `(bank_file_sha16, prompt_id)`. `prompt_sha16` is **not** "
      "a fallback. `dcs_metadata_sidecar.py` raises `KeyTestFailure` rather than emit a table if "
      "the compound key is not unique, and `--self-test` proves each of these tests can go red.")
    A("")

    # ---------------- 1. declared design table -------------------------------------------------
    A("## §1 — DECLARED DESIGN vs `target_semantic`")
    A("")
    A("`prompt_families.py:572` writes `\"target_semantic\": concept` **unconditionally**. It "
      "therefore agrees with `concept` on every row by construction and carries **no per-row "
      "information**. It is also *false* as a description of what the demonstrations install in "
      "cells A, D, E and F. The declared fields below are derived from "
      "`prompt_families.build_demo_block` branch by branch, never from `target_semantic`.")
    A("")
    A("| cell | condition | demo valence | demo surface | query surface | demonstrations install | "
      "remap intended | installs harmful concept | mapping stated | basis |")
    A("|---|---|---|---|---|---|---|---|---|---|")
    for cell in ("A", "B", "C", "D", "E", "F"):
        d = DECLARED_CELL_DESIGN[cell]
        spec = pf.CONDITIONS[d["condition"]]
        ex = [r for r in side_rows if r["cell"] == cell and r["bank_id"] == "button_bomb"
              and r["n_examples"]]
        inst = sorted({(r["demonstration_target_concept"] or r["demonstration_target_status"])
                       for r in ex}) or ["--"]
        A(f"| **{cell}** | `{d['condition']}` | `{spec['demo_valence']}` | "
          f"`{spec['demo_surface']}` | `{spec['query_surface']}` | "
          f"`{'` / `'.join(inst)}` | {'**YES**' if d['remap_intended'] else 'no'} | "
          f"{'**YES**' if d['installs_harmful_concept'] else 'no'} | "
          f"{'yes' if d['mapping_stated_by_default'] else 'no'} | `{d['basis']}` |")
    A("")
    A("(`demonstrations install` column is measured on the `button_bomb` bank, whose benign pool "
      f"natural word is the corpus placeholder shown, and whose remap pool word is "
      f"`{demo_pools.REMAP_SOURCE_WORD}`.)")
    A("")
    for cell in ("A", "B", "C", "D", "E", "F"):
        A(f"* **cell {cell}** — {DECLARED_CELL_DESIGN[cell]['note']}")
    A("")

    # ---------------- 2. population coverage ---------------------------------------------------
    A("## §2 — POPULATION COVERAGE (the core populations of brief §19)")
    A("")
    A(f"Banks: `{'`, `'.join(CORE_BANKS)}` · cells `{'`/`'.join(CORE_CELLS)}` · query kinds "
      f"`{'`/`'.join(CORE_QUERY_KINDS)}` · `n_examples ∈ {{{', '.join(str(n) for n in CORE_N_EXAMPLES)}}}`")
    A("")
    A(f"**{len(core):,} bank rows** in the core population, out of **{len(side_rows):,}** rows "
      f"across the {len(ctxs)} banks.")
    A("")
    A("| bank | bank_file_sha16 | codeword | concept | rows (bank) | rows (core pop) |")
    A("|---|---|---|---|---|---|")
    for stem in CORE_BANKS:
        c = ctxs.get(stem)
        if c is None:
            A(f"| `{stem}` | ⛔ **ABSENT** | -- | -- | -- | -- |")
            continue
        n_core = sum(1 for r in core if r["bank_id"] == stem)
        A(f"| `{stem}` | `{c['bank_file_sha16']}` | `{c['meta_codeword']}` | "
          f"`{c['meta_concept']}` | {c['n_rows']:,} | {n_core:,} |")
    A("")
    A("| cell | query_kind | rows | n_examples present | template families present |")
    A("|---|---|---|---|---|")
    cq = collections.defaultdict(list)
    for r in core:
        cq[(r["cell"], r["query_kind"])].append(r)
    for (cell, qk), rs in sorted(cq.items()):
        ne = sorted({r["n_examples"] for r in rs})
        tf = sorted({str(r["template_family"]) for r in rs})
        A(f"| {cell} | `{qk}` | {len(rs):,} | {ne} | `{'`, `'.join(tf)}` |")
    A("")
    absent = [(c, q) for c in CORE_CELLS for q in CORE_QUERY_KINDS if (c, q) not in cq]
    if absent:
        A("⚠ **Cells of the requested grid with ZERO rows in the banks** (not dropped — they do "
          "not exist): " + ", ".join(f"`{c}`×`{q}`" for c, q in absent) + ".")
        A("")

    # ---------------- 2b. cross-bank sharing --------------------------------------------------
    # Uses `demo_block_sha16`, which dcs_metadata.derive_row already computes -- not recomputed.
    A("## §2b — WHICH CELLS ARE SHARED ACROSS LEXICAL BANKS, AND WHICH ARE A DIFFERENT CORPUS")
    A("")
    A("For each `prompt_id` (which, per §0, names a DESIGN cell and recurs in all 8 banks), how "
      "many distinct demonstration blocks exist across the banks? `1` means the eight banks share "
      "the identical demo text — the cell is **not** independent evidence across concepts. `>1` "
      "means each concept bank has its own corpus.")
    A("")
    A("⚠ `n_examples = 0` rows are excluded from this table only — they have no demonstration "
      "block at all, so they would dilute the count with a structural 1.")
    A("")
    A("| cell | prompt_ids (n_ex>0) | distinct demo blocks over the 8 banks (modal) | histogram | "
      "reading |")
    A("|---|---|---|---|---|")
    by_pid_cell = collections.defaultdict(lambda: collections.defaultdict(set))
    for r in core:
        if r["n_examples"]:
            by_pid_cell[r["cell"]][r["prompt_id"]].add(r["demo_block_sha16"])
    n_b = len(CORE_BANKS)
    for cell in sorted(by_pid_cell):
        ids = by_pid_cell[cell]
        hist = collections.Counter(len(v) for v in ids.values())
        modal = hist.most_common(1)[0][0]
        if modal <= 1:
            read = "**SHARED** by all 8 banks — one corpus, NOT 8 independent observations"
        elif modal >= n_b:
            read = ("**a DIFFERENT corpus in every bank** — `A-020` §8.1's blocker: a bank-to-bank "
                    "difference here is partly a CORPUS difference")
        else:
            read = (f"shared across the {n_b // modal} codeword banks of each concept "
                    f"(the cell contains no codeword), so it supplies {modal}, not {n_b}, "
                    f"independent observations")
        A(f"| {cell} | {len(ids):,} | **{modal}** | {dict(sorted(hist.items()))} | {read} |")
    A("")
    A("⚠ This bounds what a per-concept group-by can claim. Cells `B` and `E` carry no codeword, "
      "so their text is identical between `button_X` and `basket_X`: the lexical replication is "
      "**shared, not independent**, in exactly those cells. Cells `A`, `C` and `F` are *modally* "
      "a distinct corpus in each of the eight banks.")
    A("")
    # -- the off-modal ids, explained rather than left as a histogram tail --------------------
    irr = [pid for pid, v in by_pid_cell.get("C", {}).items() if len(v) < n_b]
    irr_rows = [r for r in core if r["cell"] == "C" and r["prompt_id"] in set(irr)]
    if irr_rows:
        cons = collections.Counter(r["consistency"] for r in irr_rows)
        A(f"* **Cell `C`'s off-modal ids are the `irrelevant` consistency arm**: "
          f"{len(irr)} prompt_ids ({len(irr_rows)} rows), `consistency` = {dict(cons)}. "
          f"Those demonstrations are "
          f"substituted onto the distractor `{pf.DISTRACTOR_CODEWORD}`, not onto the codeword, so "
          f"they contain no codeword and are shared between the `button_` and `basket_` banks. "
          f"Explained, not left as a tail.")
    # -- ⛔ cross-CONCEPT identity in cell A, which the design does NOT intend ------------------
    same_code = collections.defaultdict(dict)   # (codeword, prompt_id) -> {concept: demo_sha}
    for r in core:
        if r["cell"] == "A" and r["n_examples"]:
            same_code[(r["codeword"], r["prompt_id"])][r["concept"]] = r["demo_block_sha16"]
    same_code_full = collections.defaultdict(dict)  # same, on the WHOLE prompt
    for r in core:
        if r["cell"] == "A" and r["n_examples"]:
            same_code_full[(r["codeword"], r["prompt_id"])][r["concept"]] = r["prompt_sha16"]
    pair_hits = collections.Counter()
    pair_full = collections.Counter()
    pair_tot = collections.Counter()
    for k, d in same_code.items():
        df = same_code_full[k]
        for c1, c2 in ((a, b) for a in sorted(d) for b in sorted(d) if a < b):
            pair_tot[(c1, c2)] += 1
            if d[c1] == d[c2]:
                pair_hits[(c1, c2)] += 1
            if df.get(c1) is not None and df.get(c1) == df.get(c2):
                pair_full[(c1, c2)] += 1
    if pair_hits:
        A("")
        A("### ⛔ Cell `A` is not always a different corpus per concept — a collision the design "
          "does not intend")
        A("")
        A("Holding the **codeword fixed** and varying only the **concept bank**, how often is the "
          "cell-`A` demonstration block byte-identical? It should be never: each concept bank has "
          "its own pools file. It is not never.")
        A("")
        A("| concept pair (same codeword) | design cells compared (codeword × prompt_id) | "
          "identical DEMO BLOCK | identical WHOLE PROMPT |")
        A("|---|---|---|---|")
        for k in sorted(pair_tot, key=lambda x: -pair_hits[x]):
            n_h, n_f, n_t = pair_hits[k], pair_full[k], pair_tot[k]
            A(f"| `{k[0]}` vs `{k[1]}` | {n_t} | **{n_h}** ({100.0*n_h/max(1,n_t):.1f}%) | "
              f"{'**%d** (%.1f%%) ⛔' % (n_f, 100.0*n_f/max(1,n_t)) if n_f else '0 ✅'} |")
        A("")
        # A concrete instance, pulled from the data so the claim can be checked by hand.
        # Prefer a WHOLE-PROMPT collision; fall back to a demo-block-only one and say which.
        ex_pair = max(pair_full, key=lambda k: pair_full[k]) if any(pair_full.values()) \
            else max(pair_hits, key=lambda k: pair_hits[k])
        by_key = collections.defaultdict(dict)
        for r in core:
            if r["cell"] == "A" and r["n_examples"]:
                by_key[(r["codeword"], r["prompt_id"])][r["concept"]] = r
        ex, ex_kind = None, None
        for kk, d in sorted(by_key.items()):
            if ex_pair[0] not in d or ex_pair[1] not in d:
                continue
            r1, r2 = d[ex_pair[0]], d[ex_pair[1]]
            if r1["prompt_sha16"] == r2["prompt_sha16"]:
                ex, ex_kind = (kk, r1, r2), "WHOLE PROMPT"
                break
            if ex is None and r1["demo_block_sha16"] == r2["demo_block_sha16"]:
                ex, ex_kind = (kk, r1, r2), "DEMONSTRATION BLOCK ONLY"
        if ex:
            (cw, pid), r1, r2 = ex
            A(f"**A concrete instance ({ex_kind} identical)** — `prompt_id={pid}`, codeword "
              f"`{cw}`, domain `{r1['domain']}`, `n_examples={r1['n_examples']}`: the "
              f"`{ex_pair[0]}` bank row and the `{ex_pair[1]}` bank row have "
              f"`demo_block_sha16` `{r1['demo_block_sha16']}` / `{r2['demo_block_sha16']}` and "
              f"`prompt_sha16` `{r1['prompt_sha16']}` / `{r2['prompt_sha16']}`."
              + (" ⇒ These two rows are the SAME PROMPT filed under two different concepts, and "
                 "this is one source of the duplicate `prompt_sha16` rows counted in §0."
                 if ex_kind.startswith("WHOLE") else
                 " ⚠ Here the demonstrations coincide while the surrounding filler/query still "
                 "differs, so the rows are not byte-identical end to end."))
            A("")
        top = ex_pair
        A(f"⚠ The `{top[0]}`/`{top[1]}` benign pools share sentences verbatim, so for "
          f"{pair_hits[top]} design cells the two concept banks' cell-`A` **demonstrations** are "
          f"byte-identical, and for {pair_full[top]} of them the **whole prompt** is. "
          "⛔ Any contrast that uses cell `A` as the per-concept anchor is, on those rows, "
          "contrasting a concept against **itself**. This refines `A-020` §8.1 ('cell A is a "
          "different corpus in each concept bank'): it is a different corpus *modally*, and "
          "*partly the same corpus* for a measurable minority of cells. Recorded here because a "
          "group-by on concept cannot see it.")
    A("")

    # ---------------- 3. where a readout exists ------------------------------------------------
    A("## §3 — WHERE AN INSTALLATION READOUT ALREADY EXISTS ON DISK")
    A("")
    A("The only installation readouts on disk for these banks are the four `R-078` / `PR-034` gate "
      "arms. They are joined here on `(bank_file_sha16, prompt_id)`; nothing was re-run.")
    A("")
    A("| run_id | arm | bank | model | query_kinds | conditions | n_ex | rows | matched | unmatched |")
    A("|---|---|---|---|---|---|---|---|---|---|")
    for run in runs:
        d = next((x for x in join_diag["runs"] if x.get("run_id") == run["run_id"]), {})
        A(f"| `{run['run_id']}` | `{run['arm']}` | `{run['bank_stem']}` | `{run['model']}` | "
          f"`{run['query_kinds']}` | `{run['conditions']}` | `{run['n_examples']}` | "
          f"{len(run['rows'])} | {d.get('matched', '--')} | {d.get('unmatched', '--')} |")
    A("")
    joined = [r for r in core if r["observed_status"] == "JOINED"]
    A(f"⇒ **{len(joined)} of {len(core):,} core-population rows carry a readout ({100.0*len(joined)/max(1,len(core)):.1f}%).** "
      "⛔ The remaining rows are **NOT dropped** — they are reported below with "
      "`observed_status = ABSENT_NO_RUN_CONTEXT`, which is a statement about the *artifact "
      "inventory*, not about the model.")
    A("")
    A("**⚠ The readout population is far narrower than the requested grid.** The `inst_*` arms "
      "cover only: `button_*` banks (4 of 8), `semantic_forced_choice` only (0 rows of the "
      "8,064-row `semantic_one_word` core population), cells `A` and `C` only (no `B`, `E`, `F`), "
      "`n_examples ∈ {4,8}` only (no 0, 1, 2, 16), `bank_block=core2x2` only. "
      "**Every `basket_*` bank, every `semantic_one_word` row, and cells `B`/`E`/`F` have NO "
      "installation readout on disk at all.** That is a gap in the artifact inventory and it is "
      "stated here rather than papered over with a mean.")
    A("")

    # ---------------- 4. R-078 reproduction ----------------------------------------------------
    A("## §4 — `R-078` REPRODUCES FROM THE ARTIFACTS, TO THE DIGIT")
    A("")
    A(f"Decision rules recovered by reproduction, not assumed: **domains+ = {R078_DOMAINS_RULE}**; "
      f"**option_mass column = {R078_OM_RULE}**.")
    A("")
    A("| bank | cell A mean | cell C mean | Δ_inst | domains+ | om A (med) | om C (med) | "
      "published (§21) | reproduces? |")
    A("|---|---|---|---|---|---|---|---|---|")
    for rec in sorted(repro, key=lambda x: x["bank"]):
        pub = rec["published"]
        pubs = ("A %.3f / C %.3f / Δ %.3f / %d / %.3f / %.3f" % pub) if pub else "--"
        A(f"| `{rec['bank']}` | {rec['A_mean']:+.3f} | {rec['C_mean']:+.3f} | "
          f"**{rec['delta']:+.3f}** | {rec['domains_plus']}/{rec['n_domains']} | "
          f"{rec['omA_median']:.3f} | {rec['omC_median']:.3f} | {pubs} | "
          f"{'✅ EXACT' if rec['reproduces'] else ('⛔ **NO**' if rec['reproduces'] is False else '--')} |")
    A("")
    A("⚠ Two rules that a careless reader will get wrong, recorded because both were tested here: "
      "(a) `domains+` is **not** \"domains whose cell-C mean is above zero\" — that rule gives "
      "6/5/5/3 and contradicts the published 6/6/6/4; (b) the `option_mass` column is the "
      "**median**, while the `semantic_logodds` columns are **means**. Mixing them silently is how "
      "a table stops reproducing.")
    A("")

    # ---------------- 5. THE TABLE -------------------------------------------------------------
    A("## §5 — THE VALIDATION TABLE")
    A("")
    A("One row per `bank × cell × query_kind × n_examples`. `intended mapping` is the DECLARED "
      "design; the observed columns are the model output, joined only where a readout exists. "
      "Distribution columns are over the joined rows.")
    A("")
    A("| bank | cell | query_kind | n_ex | rows | intended mapping | readout rows | "
      "logodds mean | median | p10 | p90 | frac>0 | om med | mass-floor | ceiling | floor | "
      "argmax (top) |")
    A("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    groups = collections.defaultdict(list)
    for r in core:
        groups[(r["bank_id"], r["cell"], r["query_kind"], r["n_examples"])].append(r)
    for key in sorted(groups, key=lambda k: (CORE_BANKS.index(k[0]), k[1], k[2], k[3])):
        stem, cell, qk, ne = key
        rs = groups[key]
        s = summarise(rs)
        d = DECLARED_CELL_DESIGN[cell]
        # ⚠ a row whose demonstrations are AMBIGUOUS (the `mixed` consistency arm) has no single
        # installed word; it shows its status label rather than silently reading as `None`.
        tgt = sorted({(x["demonstration_target_concept"] or x["demonstration_target_status"])
                      for x in rs})
        if ne == 0:
            intended = "— (no demonstrations)"
        elif d["remap_intended"]:
            intended = f"`{rs[0]['codeword']}` → `{'`/`'.join(tgt)}`"
        else:
            intended = f"none (demos carry `{'`/`'.join(tgt)}`)"
        if s["n_readout"] == 0:
            A(f"| `{stem}` | {cell} | `{qk}` | {ne} | {len(rs)} | {intended} | **0** | "
              + " | ".join(["--"] * 9) + " | *no readout on disk* |")
        else:
            am = s.get("argmax_top") or []
            ams = ", ".join(f"`{w}` {100.0*n/max(1,s.get('argmax_n',1)):.0f}%" for w, n in am[:3]) \
                or "*decoder unavailable*"
            A(f"| `{stem}` | {cell} | `{qk}` | {ne} | {len(rs)} | {intended} | {s['n_readout']} | "
              f"{_fmt(s['lo_mean'])} | {_fmt(s['lo_median'])} | {_fmt(s['lo_p10'])} | "
              f"{_fmt(s['lo_p90'])} | {_pct(s['lo_frac_pos'])} | {s['om_median']:.3f} | "
              f"{_pct(s['frac_mass_floor'])} | {_pct(s['frac_at_ceiling'])} | "
              f"{_pct(s['frac_at_floor'])} | {ams} |")
    A("")

    # ---------------- 6. per-domain ------------------------------------------------------------
    A("## §6 — PER-DOMAIN, WHERE A READOUT EXISTS. ⛔ NON-INSTALLING DOMAINS ARE NOT DROPPED.")
    A("")
    A("`installs?` = paired per-domain `mean(C) − mean(A) > 0`, the rule `R-078` used.")
    A("")
    A("| bank | domain | n_ex | cell A mean | cell C mean | Δ | installs? | om A | om C | "
      "C argmax (top) |")
    A("|---|---|---|---|---|---|---|---|---|---|")
    per = collections.defaultdict(lambda: collections.defaultdict(list))
    for r in joined:
        per[(r["bank_id"], r["domain"], r["n_examples"])][r["cell"]].append(r)
    n_dom_cells = n_dom_install = 0
    anomalies = []
    for key in sorted(per):
        stem, dom, ne = key
        cells = per[key]
        if "A" not in cells or "C" not in cells:
            continue
        am = st.mean([x["observed_semantic_logodds"] for x in cells["A"]])
        cm = st.mean([x["observed_semantic_logodds"] for x in cells["C"]])
        oma = st.median([x["observed_option_mass"] for x in cells["A"]])
        omc = st.median([x["observed_option_mass"] for x in cells["C"]])
        ok = (cm - am) > 0
        n_dom_cells += 1
        n_dom_install += int(ok)
        dec = collections.Counter((x["target_decoded_text"] or "?").strip() for x in cells["C"])
        top = ", ".join(f"`{w}`×{n}" for w, n in dec.most_common(2))
        if not ok:
            anomalies.append((stem, dom, ne, cm - am))
        A(f"| `{stem}` | `{dom}` | {ne} | {am:+.3f} | {cm:+.3f} | **{cm-am:+.3f}** | "
          f"{'✅' if ok else '⛔ **NO**'} | {oma:.3f} | {omc:.3f} | {top} |")
    A("")
    A(f"⇒ **{n_dom_install}/{n_dom_cells} (bank × domain × n_examples) cells install the intended "
      f"mapping** ({100.0*n_dom_install/max(1,n_dom_cells):.1f}%).")
    A("")
    if anomalies:
        A("### ⛔ The cells where the intended mapping does NOT install")
        A("")
        A("| bank | domain | n_ex | Δ |")
        A("|---|---|---|---|")
        for stem, dom, ne, d_ in sorted(anomalies, key=lambda x: x[3]):
            A(f"| `{stem}` | `{dom}` | {ne} | {d_:+.3f} |")
        A("")
        by_bank = collections.Counter(a[0] for a in anomalies)
        by_dom = collections.Counter(a[1] for a in anomalies)
        A(f"Concentration: by bank {dict(by_bank)}; by domain {dict(by_dom)}.")
        A("")

    # ---------------- 7. floor / ceiling -------------------------------------------------------
    A("## §7 — FLOOR / CEILING PREVALENCE")
    A("")
    A(f"`mass_floor` = `option_mass` below the run's own `min_option_mass`; "
      f"`ceiling`/`floor` = one option holds ≥ {SATURATION_Q:.2f} / ≤ {1-SATURATION_Q:.2f} of the "
      f"option mass. R-050's phase-wide limit applies: **`option_mass` is reported beside every "
      f"log-odds**, because a log-odds on a low-mass row contrasts two options the model rejects.")
    A("")
    A("| bank | cell | readout rows | mass-floor | at ceiling (concept) | at floor (codeword) | "
      "om p10 | om med | om p90 |")
    A("|---|---|---|---|---|---|---|---|---|")
    fc = collections.defaultdict(list)
    for r in joined:
        fc[(r["bank_id"], r["cell"])].append(r)
    for key in sorted(fc):
        rs = fc[key]
        s = summarise(rs)
        A(f"| `{key[0]}` | {key[1]} | {s['n_readout']} | {_pct(s['frac_mass_floor'])} | "
          f"{_pct(s['frac_at_ceiling'])} | {_pct(s['frac_at_floor'])} | {s['om_p10']:.3f} | "
          f"{s['om_median']:.3f} | {s['om_p90']:.3f} |")
    A("")

    # ---------------- 8. template family -------------------------------------------------------
    A("## §8 — TEMPLATE FAMILY (`bank_block`) BEHAVIOUR")
    A("")
    tfs = collections.Counter(r["template_family"] for r in joined)
    if len(tfs) <= 1:
        A(f"⚠ **Not evaluable.** Every joined row is `bank_block={list(tfs) or ['--']}`; the "
          "`inst_*` arms were submitted with `--bank-blocks core2x2`, so there is no "
          "between-family contrast on disk. Template-family anomaly detection therefore returns "
          "**NOT FEASIBLE** on the current artifact inventory, not \"no anomaly\".")
        A("")
        A("What IS visible without a readout is the *structural* composition of the core "
          "population by family:")
        A("")
        A("| template family | rows | cells | n_examples | note |")
        A("|---|---|---|---|---|")
        byf = collections.defaultdict(list)
        for r in core:
            byf[r["template_family"]].append(r)
        for f_, rs in sorted(byf.items(), key=lambda kv: -len(kv[1])):
            cells = "".join(sorted({r["cell"] for r in rs}))
            ne = sorted({r["n_examples"] for r in rs})
            stated = sum(1 for r in rs if r["declared_mapping_statement_present"])
            note = (f"⚠ {stated}/{len(rs)} rows carry an explicit mapping STATEMENT in the prompt"
                    if stated else "no stated mapping")
            A(f"| `{f_}` | {len(rs):,} | `{cells}` | {ne} | {note} |")
        A("")
        A("⛔ The `strength` family is the one to watch: its rows are cell `C` but the mapping is "
          "**stated in the prompt text**, not only demonstrated (`prompt_families.mapping_statement`), "
          "which is why `C-050` §25.2 found all 12 excluded rows of the primary test population sat "
          "in `bank_block=strength`.")
    else:
        A("| template family | readout rows | logodds mean | median | frac>0 | om med |")
        A("|---|---|---|---|---|---|")
        byf = collections.defaultdict(list)
        for r in joined:
            byf[r["template_family"]].append(r)
        for f_, rs in sorted(byf.items()):
            s = summarise(rs)
            A(f"| `{f_}` | {s['n_readout']} | {_fmt(s['lo_mean'])} | {_fmt(s['lo_median'])} | "
              f"{_pct(s['lo_frac_pos'])} | {s['om_median']:.3f} |")
    A("")

    # ---------------- 9. decoded argmax --------------------------------------------------------
    A("## §9 — WHAT THE MODEL ACTUALLY SAYS (decoded argmax)")
    A("")
    if not join_diag.get("decoder_available"):
        A("⚠ **The tokenizer was unreachable, so `target_decoded_text` is null on every row.** "
          "`top1_id` is still recorded. This is reported rather than silently omitted.")
    else:
        A("| bank | cell | n | decoded argmax | share |")
        A("|---|---|---|---|---|")
        for key in sorted(fc):
            rs = [r for r in fc[key] if r.get("target_decoded_text")]
            if not rs:
                continue
            cnt = collections.Counter(r["target_decoded_text"].strip() for r in rs)
            for w, n in cnt.most_common(4):
                A(f"| `{key[0]}` | {key[1]} | {len(rs)} | `{w}` | {100.0*n/len(rs):.1f}% |")
        A("")
        A("⚠ Read this beside `R-032`: on Llama the forced-choice argmax is frequently "
          "` Neither`, i.e. the model rejects both offered options. A high `semantic_logodds` on a "
          "row whose argmax is ` Neither` is a *ratio between two rejected options* — which is "
          "exactly the readout limit `R-050` attached to this phase.")
    A("")

    # ---------------- 10. anomalies ------------------------------------------------------------
    A("## §10 — ANOMALIES, NAMED")
    A("")
    A("1. ⛔ **`prompt_id` collides 8-way.** 2,736 ids over 21,888 rows, multiplicity exactly 8 "
      "(one per lexical bank). Any analysis that joins on `prompt_id` alone silently fans out 8× "
      "and mixes `bomb` rows with `club` rows. `prompt_sha16` has 5,020 duplicate-excess rows and "
      "is not a fallback.")
    A("2. ⛔ **`target_semantic` is a constant, not a label.** It equals `concept` on every row by "
      "construction, and it is *wrong* about cells `A`, `D`, `E` and `F`, whose demonstrations "
      f"install the benign pool word or `{demo_pools.REMAP_SOURCE_WORD}`.")
    if repro:
        gun = next((r for r in repro if r["bank"] == "button_gun"), None)
        if gun:
            A(f"3. ⚠ **`button_gun` installs inconsistently across domains** — "
              f"{gun['domains_plus']}/{gun['n_domains']} domains, cell-C mean "
              f"{gun['C_mean']:+.3f}, i.e. barely above the boundary, while its Δ "
              f"({gun['delta']:+.3f}) is essentially identical to `knife`'s. ⛔ State it as "
              f"\"gun's mapping installs inconsistently across domains\", never \"gun does not "
              f"remap\".")
        bomb = next((r for r in repro if r["bank"] == "button_bomb"), None)
        others = [r for r in repro if r["bank"] != "button_bomb"]
        if bomb and others:
            A(f"4. ⛔ **`bomb` installs "
              f"{bomb['delta']/max(x['delta'] for x in others):.1f}×–"
              f"{bomb['delta']/min(x['delta'] for x in others):.1f}× harder than the hard "
              f"negatives** — the low end is against `club`, the high end against `knife`/`gun` "
              f"({bomb['delta']:+.3f} vs "
              f"{', '.join('%+.3f' % x['delta'] for x in sorted(others, key=lambda z: z['bank']))}) "
              f"with far higher option mass ({bomb['omC_median']:.3f} vs "
              f"{', '.join('%.3f' % x['omC_median'] for x in sorted(others, key=lambda z: z['bank']))}). "
              f"This is `R-078` §21.2's confound: a classifier could separate `bomb` by "
              f"*degree of remapping* rather than by *which concept*. It is a property of the "
              f"population, visible here in the metadata, before any probe is fit.")
    # 4b -- ⛔ the paired rule can PASS while the model still reads the codeword literally.
    #        Computed here, not asserted: cells with Delta > 0 but a NEGATIVE cell-C mean.
    weak = []
    for key in sorted(per):
        cells = per[key]
        if "A" not in cells or "C" not in cells:
            continue
        am = st.mean([x["observed_semantic_logodds"] for x in cells["A"]])
        cm = st.mean([x["observed_semantic_logodds"] for x in cells["C"]])
        if (cm - am) > 0 and cm < 0:
            weak.append((key, cm, cm - am))
    if weak:
        A(f"4b. ⛔ **The `R-078` domains+ rule can pass on a cell where the model still reads the "
          f"codeword LITERALLY.** {len(weak)}/{n_dom_cells} cells have Δ(C−A) > 0 while cell `C`'s "
          f"own mean log-odds is still **negative** (i.e. the concept option loses): "
          + ", ".join(f"`{b}`/`{d}`/n{n} (C={c:+.3f}, Δ={dd:+.3f})"
                      for (b, d, n), c, dd in sorted(weak, key=lambda x: x[1])[:8])
          + ". A paired improvement is not the same as an installed mapping, and this table "
            "reports both columns so the two cannot be conflated.")
    A("5. ⚠ **The readout inventory is lopsided.** Four `button_*` arms, one query kind, two "
      "cells, two dose levels. Half the banks and the entire `semantic_one_word` core population "
      "have **no** installation readout on disk. Any claim about `basket_*` or about "
      "`semantic_one_word` installation is **unevidenced by the artifacts**, not merely weak.")
    # 5b -- OFF-VOCABULARY ARGMAX, computed rather than asserted.  The forced-choice readout scores
    # only p_concept vs p_codeword; a row whose argmax is neither option (and is not `Neither`) is
    # a row where the log-odds is a ratio between two words the model did not want to say.
    offvocab = collections.Counter()
    n_dec = 0
    for r in joined:
        w = (r.get("target_decoded_text") or "").strip().lower()
        if not w:
            continue
        n_dec += 1
        if w not in {str(r["codeword"]).lower(), str(r["concept"]).lower(), "neither"}:
            offvocab[w] += 1
    if n_dec:
        A(f"5b. ⚠ **{sum(offvocab.values())}/{n_dec} joined rows have an argmax that is neither "
          f"offered option nor ` Neither`** — most frequent: "
          + (", ".join(f"`{w}`×{n}" for w, n in offvocab.most_common(6)) or "none")
          + ". ⛔ Several of these are *vegetables*, which is the declared design showing through: "
          "the benign pool's natural word is `carrot` in **all eight** banks, so cell `A`'s "
          "demonstrations install a carrot-like benign object onto the codeword — and the model's "
          "argmax lands in that category (`mushroom`, `onion`) rather than on either offered "
          "option. That is direct behavioural corroboration that `target_semantic` "
          "(which says `bomb`/`knife`/`gun`/`club` here) is FALSE for cell `A`. "
          "On such a row `semantic_logodds` is a ratio between two options the model rejected — "
          "`R-050`'s readout limit, visible row by row.")
    if pair_hits:
        tp = max(pair_full, key=lambda k: pair_full[k]) if any(pair_full.values()) \
            else max(pair_hits, key=lambda k: pair_hits[k])
        A(f"5c. ⛔ **Cell `A` is partly the SAME corpus across concept banks** (§2b). Holding the "
          f"codeword fixed, `{tp[0]}` and `{tp[1]}` share a byte-identical cell-`A` demonstration "
          f"block on {pair_hits[tp]}/{pair_tot[tp]} design cells and a byte-identical WHOLE PROMPT "
          f"on {pair_full[tp]}. Every ordered concept pair is affected "
          f"({min(pair_full.values())}–{max(pair_full.values())} whole-prompt collisions). "
          f"⇒ a `bomb`-vs-`club` contrast anchored on cell `A` is, on those rows, a contrast of a "
          f"prompt with itself, and the `A` anchor is therefore NOT independent across concepts. "
          f"This was not in the inherited record; `A-020` §8.1 asserted the opposite direction "
          f"(that cell `A` is a *different* corpus per bank), which holds only modally.")
    A("6. ⚠ **`club` is polysemous and its pools use the wrong sense** (`A-020` §8.3). It passes "
      "the gate — it installs *something* — which is not the same as installing a weapon sense. "
      "The metadata cannot adjudicate that; it only records that the demonstrations install the "
      "domain's `|harm` pool word.")
    A("7. ⚠ **Cell `C` is not homogeneous.** "
      + f"{sum(1 for r in core if r['cell']=='C' and r['demonstration_valence']=='mixed')} core-"
      "population cell-`C` rows have `demonstration_valence='mixed'` (the consistency arm: half "
      "the demos are literal uses of the codeword), and "
      + f"{sum(1 for r in core if r['cell']=='C' and r['declared_mapping_statement_present'])} "
      "carry an explicit mapping statement in the prompt text. Both are flagged per row rather "
      "than folded into cell `C`.")
    A("")

    # ---------------- 11. provenance -----------------------------------------------------------
    A("## §11 — PROVENANCE")
    A("")
    A("| artifact | sha16 |")
    A("|---|---|")
    for stem in CORE_BANKS:
        c = ctxs.get(stem)
        if c:
            A(f"| `{os.path.relpath(c['bank_path'], REPO_ROOT)}` | `{c['bank_file_sha16']}` |")
    for run in runs:
        A(f"| `{os.path.relpath(run['run_dir'], REPO_ROOT)}/results.jsonl` | "
          f"`{run['results_sha16']}` |")
    pools = {(c.get("pools_path"), c.get("pools_sha16")) for c in ctxs.values()}
    for p, h in sorted(x for x in pools if x[0]):
        A(f"| `{os.path.relpath(p, REPO_ROOT)}` | `{h}` (pools_sha16) |")
    A("")
    A("Sidecar field set emitted per row (brief §7): "
      + ", ".join(f"`{k}`" for k in _BRIEF7_FIELDS))
    A("")
    A("Generator: `scripts/dcs_metadata_sidecar.py`, which **reuses** "
      "`src/boombness/dcs_metadata.py` (`load_bank`, `derive_row`, the ambiguity rules, the hash "
      "helpers) rather than reimplementing them, and reuses `prompt_families.CONDITIONS` / "
      "`build_demo_block`'s own branch structure for the declared-design layer.")
    A("")

    text = "\n".join(L) + "\n"
    if out_path and out_path != "/dev/null":
        os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
        with open(out_path, "w") as f:
            f.write(text)
    return text


#: brief Sec 7's mandated field set, as emitted.  Asserted present on every sidecar row.
_BRIEF7_FIELDS = (
    "bank_id", "bank_file_sha16", "prompt_id", "domain", "split", "codeword", "surface_word",
    "surface_type", "harmful_concept", "declared_benign_concept",
    "demonstration_target_concept", "demonstration_valence", "condition", "cell",
    "template_family", "n_examples", "lexical_pair", "model", "query_kind",
    "target_occurrence_index_readout", "target_decoded_text", "declared_remapping_intended",
    "source_artifact_path", "source_artifact_sha16",
)


def field_completeness_test(rows: list) -> list:
    missing = collections.Counter()
    for r in rows:
        for f in _BRIEF7_FIELDS:
            if f not in r:
                missing[f] += 1
    return [("T-FIELD-1_brief_sec7_fields_present", not missing,
             f"{len(_BRIEF7_FIELDS)} mandated fields checked on {len(rows)} rows"
             + (f"; MISSING {dict(missing)}" if missing else ""))]


# ============================================================================================= #
# SELF-TEST -- every assertion must be shown able to FAIL
# ============================================================================================= #
def self_test(rows: list, ctxs: dict) -> list:
    """Mutation harness. Each entry: (mutation, the test it must turn red, went_red)."""
    import copy
    res = []

    def red(mut_rows, name, fn=key_tests):
        t = dict((n, ok) for n, ok, _ in fn(mut_rows))
        return not t.get(name, True)

    # M1 -- collapse every bank_file_sha16 to one value: the compound key must stop being unique.
    m = copy.deepcopy(rows)
    for r in m:
        r["bank_file_sha16"] = "X" * 16
    res.append(("M1_all_banks_same_file_sha16", "T-KEY-2_compound_key_IS_unique",
                red(m, "T-KEY-2_compound_key_IS_unique")))

    # M2 -- make every prompt_id unique: T-KEY-1 (the collision claim) must go red.
    m = copy.deepcopy(rows)
    for i, r in enumerate(m):
        r["prompt_id"] = f"u{i:08d}"
    res.append(("M2_prompt_ids_made_unique", "T-KEY-1_prompt_id_is_NOT_unique",
                red(m, "T-KEY-1_prompt_id_is_NOT_unique")))

    # M3 -- and the contamination test must go red on the same mutation.
    res.append(("M3_prompt_ids_made_unique", "T-KEY-4_prompt_id_join_CONTAMINATES_across_banks",
                red(m, "T-KEY-4_prompt_id_join_CONTAMINATES_across_banks")))

    # M4 -- make prompt_sha16 unique: the "not a fallback" test must go red.
    m = copy.deepcopy(rows)
    for i, r in enumerate(m):
        r["prompt_sha16"] = f"s{i:08d}"
    res.append(("M4_prompt_sha16_made_unique", "T-KEY-3_prompt_sha16_is_NOT_a_fallback",
                red(m, "T-KEY-3_prompt_sha16_is_NOT_a_fallback")))

    # M5 -- duplicate one prompt_id inside a bank: T-KEY-5 must go red.
    m = copy.deepcopy(rows)
    same = [r for r in m if r["bank_id"] == m[0]["bank_id"]]
    if len(same) > 1:
        same[1]["prompt_id"] = same[0]["prompt_id"]
    res.append(("M5_duplicate_prompt_id_within_bank", "T-KEY-5_prompt_id_unique_WITHIN_a_bank",
                red(m, "T-KEY-5_prompt_id_unique_WITHIN_a_bank")))

    # M6 -- break target_semantic on one row: the "uninformative" test must go red.
    m = copy.deepcopy(rows)
    m[0]["target_semantic_equals_concept"] = False
    res.append(("M6_target_semantic_disagrees_on_one_row",
                "T-SEM-1_target_semantic_is_uninformative",
                red(m, "T-SEM-1_target_semantic_is_uninformative")))

    # M7 -- pretend cells A/D/E/F install exactly target_semantic: T-SEM-2 must go red.
    m = copy.deepcopy(rows)
    for r in m:
        if r["cell"] in ("A", "D", "E", "F"):
            r["demonstration_target_concept"] = r["target_semantic_raw"]
    res.append(("M7_ADEF_install_target_semantic", "T-SEM-2_target_semantic_is_FALSE_for_cells_A_D_E_F",
                red(m, "T-SEM-2_target_semantic_is_FALSE_for_cells_A_D_E_F")))

    # M8 -- make cell F install the concept instead of bicycle: T-SEM-3 must go red.
    m = copy.deepcopy(rows)
    for r in m:
        if r["cell"] == "F":
            r["demonstration_target_concept"] = "bomb"
    res.append(("M8_cell_F_installs_the_concept", "T-SEM-3_cell_F_installs_REMAP_SOURCE_WORD",
                red(m, "T-SEM-3_cell_F_installs_REMAP_SOURCE_WORD")))

    # M9 -- drop a mandated field: the field-completeness test must go red.
    m = copy.deepcopy(rows)
    m[0].pop("demonstration_target_concept", None)
    res.append(("M9_drop_a_mandated_field", "T-FIELD-1_brief_sec7_fields_present",
                red(m, "T-FIELD-1_brief_sec7_fields_present", fn=field_completeness_test)))

    # M10 -- corrupt a bank's claimed rows hash: the integrity test must go red.
    c2 = {k: dict(v) for k, v in ctxs.items()}
    if c2:
        k0 = sorted(c2)[0]
        c2[k0]["bank_rows_sha16_claimed"] = "0" * 16
    t = dict((n, ok) for n, ok, _ in bank_integrity_tests(c2))
    res.append(("M10_corrupt_bank_rows_sha16_claim", "T-BANK-1_bank_rows_sha16_matches_meta",
                not t.get("T-BANK-1_bank_rows_sha16_matches_meta", True)))

    # M11 -- the JOIN itself must refuse a non-unique sidecar key.
    m = copy.deepcopy(rows[:4])
    for r in m:
        r["bank_file_sha16"] = "X" * 16
        r["prompt_id"] = "same"
    try:
        join_readouts(m, [])
        went = False
    except KeyTestFailure:
        went = True
    res.append(("M11_join_on_nonunique_key", "join_readouts raises KeyTestFailure", went))

    # M12 -- R-078 reproduction must go red if a result value is perturbed.
    return res


# ============================================================================================= #
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--banks", nargs="*", default=list(CORE_BANKS))
    ap.add_argument("--inst-glob", default=INST_GLOB)
    ap.add_argument("--report-out", default=None,
                    help="write the Sec-19 validation table here (the ONLY file written by "
                         "default is nothing; pass a path to emit)")
    ap.add_argument("--sidecar-out", default=None,
                    help="optional: write the per-row sidecar JSONL here. Off by default so that "
                         "this script creates no artifact unless asked.")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--no-decode", action="store_true",
                    help="skip the tokenizer; target_decoded_text stays null")
    args = ap.parse_args(argv)

    print("=== dcs_metadata_sidecar: building sidecar (banks are opened READ-ONLY) ===")
    rows, ctxs, missing = build_sidecar(args.banks, verbose=True)
    if missing:
        print(f"⛔ banks ABSENT: {missing}")
    print(f"  -> {len(rows):,} sidecar rows over {len(ctxs)} banks")

    tests = key_tests(rows) + field_completeness_test(rows)
    btests = bank_integrity_tests(ctxs)
    print("\n=== KEY / SEMANTIC TESTS ===")
    dm._tbl(["test", "verdict", "detail"],
            [[n, "PASS" if ok else "*** FAIL ***", d[:140]] for n, ok, d in tests + btests])

    if args.self_test:
        print("\n=== SELF-TEST (every assertion must be able to FAIL) ===")
        st_res = self_test(rows, ctxs)
        dm._tbl(["mutation", "test that must go red", "went red"],
                [[a, b, "YES" if c else "*** NO ***"] for a, b, c in st_res])
        bad = [a for a, b, c in st_res if not c]
        if bad:
            raise KeyTestFailure(f"self-test: mutations NOT detected: {bad}")
        print("  all mutations detected")

    assert_tests(tests + btests, "key tests")

    print("\n=== JOINING R-078 INSTALLATION READOUTS ===")
    runs = load_inst_runs(args.inst_glob)
    print(f"  {len(runs)} run dir(s) matched {args.inst_glob}")
    if args.no_decode:
        MODEL_TOKENIZERS_TRIED.update({r["model"]: None for r in runs})
    diag = join_readouts(rows, runs)
    print(f"  joined {diag['n_joined']} rows, {diag['n_unmatched']} unmatched, "
          f"decoder_available={diag['decoder_available']}")

    repro = r078_reproduce(runs)
    print("\n=== R-078 REPRODUCTION ===")
    dm._tbl(["bank", "A", "C", "delta", "dom+", "omA_med", "omC_med", "reproduces"],
            [[r["bank"], f"{r['A_mean']:+.3f}", f"{r['C_mean']:+.3f}", f"{r['delta']:+.3f}",
              f"{r['domains_plus']}/{r['n_domains']}", f"{r['omA_median']:.3f}",
              f"{r['omC_median']:.3f}", str(r["reproduces"])] for r in sorted(repro, key=lambda x: x["bank"])])
    unrep = [r["bank"] for r in repro if r["reproduces"] is False]
    if unrep:
        raise KeyTestFailure(f"R-078 does NOT reproduce for {unrep} -- refusing to emit a table "
                             f"built on artifacts that disagree with the published result")

    if args.sidecar_out:
        os.makedirs(os.path.dirname(os.path.abspath(args.sidecar_out)), exist_ok=True)
        with open(args.sidecar_out, "w") as f:
            for r in rows:
                f.write(json.dumps(r, default=str) + "\n")
        print(f"\nsidecar -> {args.sidecar_out} ({len(rows):,} rows)")

    if args.report_out:
        build_report(rows, ctxs, tests, btests, diag, runs, repro, args.report_out)
        print(f"report  -> {args.report_out}")
    else:
        print("\n(no --report-out given; nothing written)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
