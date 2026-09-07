#!/usr/bin/env python3
"""`DCS-PR-058` -- PHASE 10, the SYMMETRIC "last explicit-concept row" test.

WHAT GOVERNS
------------
`configs/dcs_ts_pr058_phase10.json`, status FROZEN, loaded through `scripts/dcs_ts_prereg.py`.
There is not one numeric gate literal in this file. alpha, `n_perm`, the attainable p-floor, the
`option_mass` gate, the power bar, the installation stratification cut, the declared minimum
meaningful effect, the control-draw count, the permutation seed, the read layer, the intervention
band, the multiplicity family and the mandatory negative wording are all fetched through
`Prereg.require()` or PARSED out of the frozen file's own prose. A number in a markdown log that
no program consults is a wish (`B-020`, committed three times); a number RE-TYPED in the analyzer
is the same defect with a different fingerprint, because the file and the code can then disagree
without either being wrong on its own. `--self-test` enforces that property against this file's
own source text (`source_gate_literal_audit`), so the claim in this docstring is checked rather
than asserted.

WHAT PHASE 10 IS, AND WHAT IT IS NOT
------------------------------------
Mandate section 13 asks for the symmetric version of the final-codeword experiment and rules the
naive form OUT: "the naive probe AT the token `bomb` is invalid: it trivially reads lexical
identity". That probe is NOT preregistered, is NOT an outcome here, and this module refuses to
compute a delta from the concept-token read position (`read_site.position_NOT_USED`). What IS
preregistered is a 2x2 already present in the bank:

    cell E  PRIMARY      benign demonstrations remapping the LITERAL ` bomb`; query names bomb
    cell C  REFERENCE    the codeword-row experiment this one mirrors (` button` / ` basket`)
    cell B  SPECIFICITY  identical query text, demonstrations that AGREE with the literal reading

One intervention, one code path, one dose: `target_surface_row_only` masks the demonstration keys
out of the FINAL `target_surface` row of the query, over the inherited band, and the readout is
DOWNSTREAM -- the semantic report (O1, primary) and a neutral position after that row (O2).

THE RISK THIS FILE IS STRUCTURED AROUND
---------------------------------------
`leakage.cell_BE_caveat` / `primary._largest_risk`: the cell-B/E query NAMES the concept by
construction -- "In the text above, what does the word bomb actually refer to?" -- so
`logp_concept` sits at a ceiling cell C does not have. A NULL in H1 is confounded with that
ceiling; a POSITIVE is confounded with the model copying a word out of its own prompt. The frozen
file declares three mitigations and all three are CODE PATHS here, not paragraphs:

  (1) `BaselineDistribution` is a required constructor argument of `PairedDelta`, and
      `render_delta()` REFUSES to emit a delta whose baseline distribution has not been rendered
      first. A delta cannot reach a reader ahead of its own baseline.
  (2) `ceiling_gate()` returns CANNOT ANSWER when the cell-E baseline's p90 sits at the top of the
      scored range, and the H1-minus-H3 contrast differences the identical cell-B ceiling out.
  (3) `copy_vs_mechanism()` evaluates the two accounts' OPPOSITE sign predictions for H1 relative
      to H2, both declared in `hypotheses[]` before any data exist.

FIVE ENTRY POINTS
-----------------
  --plan          the arm manifest and its launch commands. CPU, deterministic, reads no outcome.
  --self-test     CPU unit tests on synthetic data for every testable piece.
  --mutate        a dead hook, a zero-row bind, a row-level permutation attempt, a threshold read
                  from a literal, a delta printed without its baseline, a verdict on unclean
                  liveness, an SDPA arm, a zero realised dose, an identical-hash control band, an
                  absolute edit index, unequal per-arm populations and a delta from the
                  concept-token read site must EACH produce a refusal.
  --power-t3      checklist T3 as a CODE PATH: measure the between-domain SD on VALIDATION domains
                  only and return CANNOT ANSWER WITHOUT READING TEST below the power bar.
  (default)       the analysis. It REFUSES when no arm has run, rather than printing an empty
                  result.

USAGE
    python3 scripts/dcs_ts_pr058_symmetry.py --self-test
    python3 scripts/dcs_ts_pr058_symmetry.py --mutate
    python3 scripts/dcs_ts_pr058_symmetry.py --plan
    python3 scripts/dcs_ts_pr058_symmetry.py --runs outputs/boombness/score_behavior

A RECORDED CONFLICT WITH THE FROZEN FILE
----------------------------------------
`artifacts.analyzer` names `scripts/dcs_ts_pr058_symmetry.py`. This file is
`scripts/dcs_ts_pr058_symmetry.py`. The config is FROZEN and is NOT edited to match; the
disagreement is surfaced by `analyzer_identity_gate()`, which refuses to emit a verdict unless the
operator passes `--ack-analyzer-path-conflict`, and the acknowledgement is recorded in the run
artifact. See `reports/DCS_TS_PR058_ANALYZER.md`, defect PR058-D1.
"""
from __future__ import annotations

import argparse

import json
import math
import os
import random
import re
import sys
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "scripts"))

from dcs_ts_prereg import Prereg, PreregError, load  # noqa: E402

# CONVENTIONS IMPORTED FROM THE FROZEN ANALYZERS, NOT REIMPLEMENTED. A difference between this
# script's arithmetic and PR-048's is then a difference of design, never of arithmetic.
from dcs_ts_pr048_analysis import (  # noqa: E402
    _find_run,
    fmt_p,
    group_permutation_p,
    load_bank_rows,
    load_split,
    sign_test_two_sided,
)
from dcs_ts_pr051_positional import Checks, ZeroBinding  # noqa: E402
from dcs_ts_power import t_mde, t_power  # noqa: E402

PREREG_DEFAULT = "configs/dcs_ts_pr058_phase10.json"
PR_ID = "DCS-PR-058"
FAMILY_NAME = "PHASE10_SYMMETRY"

#: Artifacts the GPU runner must write for this analyzer to have anything to refuse on. Naming a
#: new artifact is not inventing a readout field; where this module needs a field of the EXISTING
#: readout that the existing writer does not emit, it says so and refuses.
CONTRACT_ARM = "PR058_ARM.json"
CONTRACT_LIVENESS = "PR058_LIVENESS.jsonl"


class Refusal(RuntimeError):
    """Raised instead of returning a number that should not exist."""


class CannotAnswer(RuntimeError):
    """The design cannot resolve the question. NOT a null, and never printed as one."""


#: The literal wording of the negative, pinned here and checked against the frozen file. If the
#: two ever disagree that is a refusal: the wording of a negative is not allowed to drift between
#: the preregistration and the code.
MANDATORY_NEGATIVE_WORDING = (
    "THE DEMONSTRATION->QUERY PATHWAY AT THE FINAL EXPLICIT-CONCEPT ROW IS NOT REQUIRED FOR THE "
    "MODEL'S SEMANTIC REPORT UNDER THIS INTERVENTION, AT THIS DOSE, ON THIS BANK"
)


# ============================================================================================
# 0. WORDING -- mandate section 33 as a code path
# ============================================================================================
def forbidden_from_prereg(pr: Prereg) -> List[str]:
    try:
        return [str(s) for s in pr.require("things_that_must_not_be_said")]
    except PreregError:
        raise Refusal("the preregistration declares no `things_that_must_not_be_said`; refusing "
                      "to run without the list that fixes what this phase may say")


def assert_sayable(text: str, forbidden: Sequence[str]) -> str:
    """Refuse to emit a forbidden sentence. Returns `text` so it can wrap a print argument."""
    low = text.lower()
    for bad in forbidden:
        clause = str(bad).lower().split(" -- ")[0].strip().strip('"').strip("'")
        if clause and clause in low:
            raise Refusal(
                "REFUSING to emit text containing a forbidden claim %r (mandate section 33 / "
                "things_that_must_not_be_said). The permitted wording of the negative is %r."
                % (clause, MANDATORY_NEGATIVE_WORDING))
    return text


def check_wording_pin(pr: Prereg) -> str:
    want = str(pr.require("primary", "negative", "MANDATORY_WORDING")).strip()
    if want.upper() != MANDATORY_NEGATIVE_WORDING:
        raise Refusal(
            "primary.negative.MANDATORY_WORDING is %r but this analyzer's pinned literal is %r. "
            "The wording of the negative is non-negotiable and must not drift between the "
            "preregistration and the code." % (want, MANDATORY_NEGATIVE_WORDING))
    return MANDATORY_NEGATIVE_WORDING


# ============================================================================================
# 1. PREREG ACCESSORS -- every gate, no literals
# ============================================================================================
def alpha(pr: Prereg) -> float:
    return float(pr.require("primary", "alpha"))


def n_perm(pr: Prereg) -> int:
    return int(pr.require("primary", "n_perm"))


def p_floor(pr: Prereg) -> float:
    """The DECLARED attainable floor, cross-checked against 1/(n_perm+1) it is supposed to be."""
    declared = float(pr.require("primary", "attainable_p_floor"))
    derived = 1.0 / (n_perm(pr) + 1.0)
    if abs(declared - derived) > 1e-9:
        raise Refusal(
            "primary.attainable_p_floor is %r but 1/(n_perm+1) with n_perm=%d is %r. A floor that "
            "disagrees with the design that produces it cannot be published beside a p."
            % (declared, n_perm(pr), derived))
    return declared


def independence_unit(pr: Prereg) -> str:
    u = str(pr.require("primary", "independence_unit")).strip().lower()
    if not re.fullmatch(r"[a-z_]+", u):
        raise Refusal("primary.independence_unit is not a bare identifier: %r" % u)
    return u


def permutation_seed(pr: Prereg) -> int:
    return int(pr.require("seeds", "permutation"))


def n_control_draws(pr: Prereg) -> int:
    return int(pr.require("seeds", "n_control_draws"))


def installation_cut(pr: Prereg) -> float:
    """`installation.threshold_declared_here`. A STRATIFIER, never a gate, never an exclusion."""
    return float(pr.require("installation", "threshold_declared_here"))


def declared_mde(pr: Prereg) -> float:
    return float(pr.require("power", "declared_minimum_meaningful_effect",
                            "semantic_logodds_shift"))


def _parse_first(patterns: Sequence[str], texts: Sequence[str], what: str) -> float:
    for t in texts:
        for pat in patterns:
            m = re.search(pat, str(t), flags=re.IGNORECASE)
            if m:
                return float(m.group(1))
    raise Refusal("the frozen file states no parseable %s; refusing to invent one in the "
                  "analyzer. A threshold the analyzer needs but the preregistration does not "
                  "declare in a readable form is exactly the B-020 defect." % what)


def option_mass_gate_value(pr: Prereg) -> float:
    """The `option_mass` engagement gate, PARSED out of the frozen file's own prose.

    It is stated twice -- `outcome_variables.O1_semantic_readout.cannot_answer_if` and
    `primary.cannot_answer` -- as "below the 0.0X gate". It is not carried in a numeric field, so
    it is parsed rather than re-typed; a re-typed copy is a second source of truth.
    """
    texts = [pr.require("outcome_variables", "O1_semantic_readout", "cannot_answer_if"),
             pr.require("primary", "cannot_answer"),
             pr.require("kill_condition")]
    return _parse_first([r"below\s+the\s+(0?\.\d+)\s+gate",
                         r"option_mass\s+below\s+the\s+(0?\.\d+)"],
                        texts, "option_mass gate")


def power_bar(pr: Prereg) -> float:
    """The power bar, parsed out of checklist T3 / `primary.cannot_answer` / `power.*`."""
    texts = [str(i.get("item", "")) for i in pr.require("pre_extraction_checklist")
             if i.get("id") == "T3"]
    texts.append(str(pr.require("primary", "cannot_answer")))
    texts.append(str(pr.require("power", "design")))
    texts.append(str(pr.require("power", "underpowered_branch")))
    return _parse_first([r"power\s*<\s*(0?\.\d+)",
                         r"power\s+(?:is\s+)?below\s+(0?\.\d+)",
                         r"target\s+power\s+(0?\.\d+)"], texts, "power bar")


def ceiling_quantile(pr: Prereg) -> float:
    """Which quantile of the cell-E baseline the ceiling rule reads. `primary._largest_risk` says
    p90; the level is parsed so the code and the file cannot disagree about which tail is meant."""
    txt = str(pr.require("primary", "_largest_risk"))
    m = re.search(r"\bp(\d{2})\b", txt)
    if not m:
        raise Refusal("primary._largest_risk names no quantile for the ceiling rule; refusing to "
                      "choose one in the analyzer")
    return float(m.group(1)) / float(100)


def read_layers(pr: Prereg) -> List[int]:
    grid = [int(x) for x in pr.require("read_site", "read_layer_grid")]
    if not grid:
        raise Refusal("read_site.read_layer_grid is empty")
    return grid


def primary_read_layer(pr: Prereg) -> int:
    L = int(pr.require("read_site", "primary_read_layer"))
    if L not in read_layers(pr):
        raise Refusal("read_site.primary_read_layer %d is not in the declared grid %s"
                      % (L, read_layers(pr)))
    return L


def read_position(pr: Prereg) -> str:
    p = str(pr.require("read_site", "position_PRIMARY_REPRESENTATION")).strip()
    if not re.fullmatch(r"[a-z_]+", p):
        raise Refusal("read_site.position_PRIMARY_REPRESENTATION is not a bare position name: %r" % p)
    return p


def refused_read_position(pr: Prereg) -> str:
    """`read_site.position_NOT_USED` -- the concept-token site. Reading a mechanism outcome there
    is the INVALID naive probe mandate section 13 rules out."""
    p = str(pr.require("read_site", "position_NOT_USED")).strip()
    if not re.fullmatch(r"[a-z_]+", p):
        raise Refusal("read_site.position_NOT_USED is not a bare position name: %r" % p)
    return p


def intervention_band(pr: Prereg) -> Tuple[int, int]:
    txt = str(pr.require("intervention", "band"))
    m = re.search(r"(\d+)\s*-\s*(\d+)", txt)
    if not m:
        raise Refusal("intervention.band is not parseable as a block range: %r" % txt)
    lo, hi = int(m.group(1)), int(m.group(2))
    if lo >= hi:
        raise Refusal("intervention.band %r is not an increasing range" % txt)
    return lo, hi


def required_attn_impl(pr: Prereg) -> str:
    """`intervention.attn_impl` -- eager. Under SDPA the additive mask edit is DISCARDED and the
    knockout is a silent no-op that scores as a clean null (C-047)."""
    txt = str(pr.require("intervention", "attn_impl"))
    tok = txt.split()[0].strip().strip("-").strip()
    if not re.fullmatch(r"[a-z_]+", tok):
        raise Refusal("intervention.attn_impl does not begin with a bare implementation name: %r" % txt)
    return tok


def knockout_scope(pr: Prereg) -> str:
    return str(pr.require("intervention", "scope")).strip()


# ============================================================================================
# 2. THE SOURCE-LITERAL AUDIT -- "no numeric gate literal anywhere" made checkable
# ============================================================================================
#: SCOPE LIMIT, stated rather than hidden: the audit catches every FLOAT-valued gate and every
#: INTEGER gate at or above this many digits. A one- or two-digit integer gate (the read layer, the
#: control-draw count) cannot be distinguished from ordinary arithmetic by textual inspection, so
#: those are covered by the accessor unit tests instead, not by this audit.
_AUDIT_MIN_INT_DIGITS = 3

_NUMBER_RE = re.compile(r"(?<![\w.])\d+\.\d+(?:[eE][-+]?\d+)?|(?<![\w.])\d+[eE][-+]?\d+"
                        r"|(?<![\w.])\d+(?![\w.])")


def declared_gate_values(pr: Prereg) -> Dict[str, float]:
    """Every gate this analyzer consumes, by name, as fetched from the frozen file."""
    return {
        "primary.alpha": alpha(pr),
        "primary.n_perm": float(n_perm(pr)),
        "primary.attainable_p_floor": p_floor(pr),
        "option_mass gate": option_mass_gate_value(pr),
        "power bar": power_bar(pr),
        "installation.threshold_declared_here": installation_cut(pr),
        "power.declared_minimum_meaningful_effect": declared_mde(pr),
        "seeds.permutation": float(permutation_seed(pr)),
        "seeds.control_draws": float(pr.require("seeds", "control_draws")),
        "seeds.extraction": float(pr.require("seeds", "extraction")),
    }


def source_gate_literal_audit(pr: Prereg, source_path: Optional[str] = None) -> Dict[str, Any]:
    """Does this analyzer's own source contain any DECLARED GATE VALUE as a numeric literal?

    "Every threshold via Prereg.require()" is a property of the file, so it is checked against the
    file. Without this the claim is a docstring, and a docstring is not a guard.
    """
    path = source_path or os.path.abspath(__file__)
    with open(path) as f:
        src = f.read()
    gates = declared_gate_values(pr)
    violations = []
    for m in _NUMBER_RE.finditer(src):
        tok = m.group(0)
        if "." not in tok and "e" not in tok.lower():
            if len(tok.lstrip("0")) < _AUDIT_MIN_INT_DIGITS:
                continue
        try:
            val = float(tok)
        except ValueError:
            continue
        for name, gv in gates.items():
            if val == gv:
                line = src.count("\n", 0, m.start()) + 1
                violations.append({"line": line, "literal": tok, "gate": name, "value": gv})
    return {"path": path, "n_gates_checked": len(gates), "n_violations": len(violations),
            "violations": violations[:10],
            "ok": not violations,
            "scope_limit": "float gates and integer gates of >= %d digits; short integer gates are "
                           "covered by accessor unit tests, not by textual audit"
                           % _AUDIT_MIN_INT_DIGITS}


def assert_gate_from_prereg(name: str, value: float, pr: Prereg) -> float:
    """A gate must be one the frozen file declares. Handing this a hand-typed number refuses."""
    gates = declared_gate_values(pr)
    if name not in gates:
        raise Refusal("%r is not a gate this preregistration declares; the analyzer will not "
                      "consume a threshold the design does not carry" % name)
    if value != gates[name]:
        raise Refusal(
            "gate %r was supplied as %r but the frozen preregistration declares %r. A threshold "
            "read from a literal instead of from Prereg.require() is B-020 with a different "
            "fingerprint." % (name, value, gates[name]))
    return value


# ============================================================================================
# 3. ANALYZER IDENTITY -- the recorded conflict with the frozen file
# ============================================================================================
def analyzer_identity_gate(pr: Prereg, ack: bool = False) -> Dict[str, Any]:
    declared = str(pr.require("artifacts", "analyzer")).strip()
    mine = os.path.relpath(os.path.abspath(__file__), REPO)
    match = (os.path.normpath(declared) == os.path.normpath(mine))
    out = {"declared": declared, "actual": mine, "match": match, "acknowledged": bool(ack)}
    if not match and not ack:
        raise Refusal(
            "PR058-D1 CONFLICT WITH THE FROZEN PREREGISTRATION: artifacts.analyzer names %r but "
            "this analyzer is %r. The config is FROZEN and is NOT edited to match; the conflict is "
            "recorded as a defect. Re-run with --ack-analyzer-path-conflict to proceed with the "
            "acknowledgement written into the run artifact." % (declared, mine))
    return out


def analyzer_exists_flag(pr: Prereg) -> Dict[str, Any]:
    """`artifacts.analyzer_exists` is the flag the loader refuses extraction on. This analyzer
    cannot flip it (the file is frozen and this session may not edit it), so it REPORTS the
    disagreement between the flag and the filesystem rather than papering over it."""
    flag = bool(pr.require("artifacts", "analyzer_exists"))
    declared = os.path.join(REPO, str(pr.require("artifacts", "analyzer")))
    on_disk = os.path.exists(declared) or os.path.exists(os.path.abspath(__file__))
    return {"analyzer_exists_flag": flag, "an_analyzer_is_on_disk": on_disk,
            "declared_path_on_disk": os.path.exists(declared),
            "note": "the loader still REFUSES --for-extraction while the flag is false; flipping "
                    "it is the config owner's edit, not the analyzer's"}


# ============================================================================================
# 4. POPULATION BINDING -- on `cell`, never on `condition`
# ============================================================================================
def whole_population_exclusions(pr: Prereg) -> List[str]:
    """The three exclusions, from the config's boolean `whole_population` -- never from prose and
    never from a hardcoded list (the C-086 / D2-10 shape)."""
    out = []
    excl = pr.require("population", "preregistered_exclusions")
    if not excl:
        raise Refusal("population.preregistered_exclusions is empty; refusing to bind a population "
                      "behind an exclusion list that declares nothing")
    for e in excl:
        if "whole_population" not in e:
            raise Refusal(
                "exclusion %r does not declare a boolean 'whole_population'. Selecting exclusions "
                "by matching prose is exactly the C-086 defect." % e.get("domain"))
        if not isinstance(e["whole_population"], bool):
            raise Refusal("exclusion %r: whole_population must be a boolean, got %s"
                          % (e.get("domain"), type(e["whole_population"]).__name__))
        if e["whole_population"]:
            out.append(str(e["domain"]))
    if not out:
        raise Refusal("no exclusion declares whole_population=true, but the design states three. "
                      "A binding that silently keeps a contaminated domain is not the design.")
    return sorted(out)


def cell_specs(pr: Prereg) -> "OrderedDict[str, Dict[str, Any]]":
    """The three arms, keyed by their `cell` letter.

    A-039: the selector field is `cell`, NOT `condition`. Both are carried here so
    `bind_rows` can CHECK that they agree on the bank rather than trusting that they do -- but
    only `cell` ever selects.
    """
    out: "OrderedDict[str, Dict[str, Any]]" = OrderedDict()
    for key, spec in pr.require("population", "cells").items():
        c = str(spec["cell"])
        if not re.fullmatch(r"[A-Z]", c):
            raise Refusal("population.cells.%s.cell is not a single cell letter: %r" % (key, c))
        out[c] = {"key": key, "cell": c, "condition": str(spec["condition"]),
                  "demo_valence": str(spec["demo_valence"]),
                  "query_surface": str(spec["query_surface"]), "role": str(spec["role"])}
    if not out:
        raise Refusal("population.cells is empty -- the analyzer would bind to nothing")
    return out


SELECTOR_FIELD = "cell"
FORBIDDEN_SELECTOR_FIELD = "condition"


def bind_rows(pr: Prereg, bank_rows: Dict[str, Dict[str, Any]], cell: str,
              assign: Dict[str, str], selector_field: str = SELECTOR_FIELD,
              query_kind: Optional[str] = None,
              n_examples: Optional[int] = None) -> Dict[str, Any]:
    """Bind one cell's population. A zero-row or zero-domain bind RAISES.

    `_cell_note`: "Select on the field `cell`, NOT on `condition`: selecting the wrong field binds
    ZERO rows (A-039)." So selecting on anything other than `cell` is refused BEFORE the bind, and
    a bind that returns nothing is refused after it. Both, because a guard that only fires on one
    of them lets the other through.
    """
    if selector_field != SELECTOR_FIELD:
        raise Refusal(
            "population binding may only select on %r; %r was requested. Binding on %r is A-039 "
            "-- it binds ZERO rows and a zero-row population silently becomes a zero-row result."
            % (SELECTOR_FIELD, selector_field, selector_field))
    specs = cell_specs(pr)
    if cell not in specs:
        raise Refusal("cell %r is not one of the preregistered cells %s" % (cell, list(specs)))
    qk = query_kind or str(pr.require("population", "query_kind_primary"))
    dose = int(n_examples if n_examples is not None else pr.require("population",
                                                                    "n_examples_primary"))
    excluded = set(whole_population_exclusions(pr))
    want_condition = specs[cell]["condition"]

    rows, domains, mismatched = [], set(), 0
    for r in bank_rows.values():
        if str(r.get(SELECTOR_FIELD)) != cell:
            continue
        if str(r.get("query_kind")) != qk:
            continue
        if int(r.get("n_examples")) != dose:
            continue
        if str(r.get("condition")) != want_condition:
            mismatched += 1
        dom = str(r.get("domain"))
        if dom in excluded:
            continue
        rows.append(r)
        domains.add(dom)
    if mismatched:
        raise Refusal(
            "%d rows bound on cell=%r carry condition=%r disagreeing with the preregistered %r. "
            "The two fields are declared to agree in this bank; a disagreement means the bank on "
            "disk is not the bank the design was written against."
            % (mismatched, cell, "<various>", want_condition))
    if not rows:
        raise ZeroBinding(
            "cell=%r query_kind=%r n_examples=%d bound ZERO ROWS after the %d whole-population "
            "exclusions. A zero-row bind is a refusal, never an empty result (A-039 / C-074)."
            % (cell, qk, dose, len(excluded)))
    dsplit_missing = sorted(d for d in domains if d not in assign)
    if dsplit_missing:
        raise Refusal("the split manifest assigns no split to %d bound domain(s): %s"
                      % (len(dsplit_missing), dsplit_missing[:5]))
    if not domains:
        raise ZeroBinding("cell=%r bound rows but ZERO domains" % cell)
    return {"cell": cell, "query_kind": qk, "n_examples": dose, "n_rows": len(rows),
            "n_domains": len(domains), "domains": sorted(domains),
            "excluded_domains": sorted(excluded), "rows": rows,
            "by_split": dict(_count_by(assign, domains))}


def _count_by(assign: Dict[str, str], domains) -> "OrderedDict[str, int]":
    c: "OrderedDict[str, int]" = OrderedDict()
    for d in sorted(domains):
        s = assign.get(d, "<unassigned>")
        c[s] = c.get(s, 0) + 1
    return c


def assert_equal_populations(per_arm_prompt_ids: Dict[str, Sequence[str]]) -> Dict[str, Any]:
    """P-N8 / `primary.void`: the ledgered prompt_ids of the most-skipped arm are replayed into
    EVERY arm, so a delta is never computed across unequal populations."""
    if len(per_arm_prompt_ids) < 2:
        raise ZeroBinding("equal-population check over %d arm(s) -- it binds nothing"
                          % len(per_arm_prompt_ids))
    sets = {k: set(v) for k, v in per_arm_prompt_ids.items()}
    common = set.intersection(*sets.values())
    extras = {k: len(v - common) for k, v in sets.items()}
    ok = all(n == 0 for n in extras.values())
    return {"n_arms": len(sets), "n_common": len(common), "n_extra_per_arm": extras, "ok": ok,
            "reason": "" if ok else
                      "arms differ in population by %s prompt_id(s); the ledgered ids were not "
                      "replayed into every arm, so any delta compares different populations"
                      % extras}


# ============================================================================================
# 5. INSTALLATION -- a STRATIFIER, never a post-hoc exclusion (mandate section 15)
# ============================================================================================
def stratify_by_installation(per_domain: Dict[str, float],
                             install_prob: Dict[str, float], cut: float) -> Dict[str, Any]:
    """Split the analysed domains into the two preregistered strata. NOTHING is dropped.

    The pooled estimate over ALL analysed domains is the headline; the strata are the mandate-15
    requirement. A domain missing from `install_prob` is a REFUSAL, because the alternative --
    dropping it -- would be the post-hoc exclusion section 15 forbids, arriving by accident.
    """
    missing = sorted(d for d in per_domain if d not in install_prob)
    if missing:
        raise Refusal(
            "no installation statistic for %d analysed domain(s): %s. Stratification is required "
            "(mandate 15) and a domain without a stratum must not be silently dropped -- that is "
            "the post-hoc exclusion the mandate forbids, arriving by accident."
            % (len(missing), missing[:5]))
    strata = {"installing": {}, "non_installing": {}}
    for d, v in per_domain.items():
        strata["installing" if install_prob[d] >= cut else "non_installing"][d] = v
    return {"cut": cut, "n_pooled": len(per_domain),
            "n_installing": len(strata["installing"]),
            "n_non_installing": len(strata["non_installing"]),
            "strata": strata,
            "_rule": "POOLED over all analysed domains is the headline; both strata are reported "
                     "beside it; no row is dropped for failing to install"}


def refuse_installation_as_exclusion(dropped_domains: Sequence[str]) -> None:
    if dropped_domains:
        raise Refusal(
            "%d domain(s) were about to be dropped for failing to install: %s. Mandate section 15: "
            "installation is a STRATIFICATION variable and a descriptive limit, NEVER a post-hoc "
            "exclusion." % (len(dropped_domains), list(dropped_domains)[:5]))


# ============================================================================================
# 6. HOOK LIVENESS -- a dead hook must be impossible to mistake for a clean null
# ============================================================================================
@dataclass
class LivenessRecord:
    """One record per row per arm, as `intervention.liveness_contract` and
    `persist_per_row_and_per_arm` require."""
    arm_id: str = ""
    prompt_id: str = ""
    enabled: bool = True
    hook_fired_count: int = 0
    n_forward: int = 0
    n_prefill_edits: int = 0
    n_decode_edits: int = 0
    keys_masked: int = 0
    surface_span_n_tokens: int = 0          # the REALISED dose
    n_cells_edited_expected: int = 0
    n_cells_edited_realised: int = 0
    attn_implementation: str = ""           # READ BACK from the loaded config
    seq_len: int = 0
    rel_end: int = -1
    resolved_absolute_index: int = -1
    read_position: str = ""
    output_sha256: str = ""

    def as_row(self) -> Dict[str, Any]:
        return dict(self.__dict__)


def liveness_gate(records: Sequence[Dict[str, Any]], arm_id: str, pr: Prereg,
                  expect_enabled: bool = True) -> Dict[str, Any]:
    """Did this arm's hook demonstrably fire, at the declared scope, under eager attention?

    `primary.void`: `hook_fired_count == 0`; `attn_implementation` not eager; `n_decode_edits != 0`
    on a prefill-only scope; a realised dose of 0; realised != expected cells. Each of those makes
    a null VOID, not a negative -- and a dead hook produces EXACTLY the artifact a real
    intervention with no effect produces, which is why this runs before any outcome is computed.
    """
    want_impl = required_attn_impl(pr)
    reasons: List[str] = []
    if not records:
        return {"arm_id": arm_id, "live": False, "n_rows": 0, "expect_enabled": expect_enabled,
                "reasons": ["NO LIVENESS RECORDS AT ALL -- %s is absent or empty for arm %r. A "
                            "null behind an unrecorded hook is VOID, not a negative."
                            % (CONTRACT_LIVENESS, arm_id)]}
    impls = {str(r.get("attn_implementation", "")) for r in records}
    if impls != {want_impl}:
        reasons.append(
            "attn_implementation on the LOADED config is %s, not %r on every record. Under SDPA "
            "the additive mask edit is DISCARDED and the knockout is a silent no-op that scores "
            "as a clean null (C-047 / _sdpa_is_void). This arm is VOID, not a negative."
            % (sorted(impls), want_impl))
    n_fired = sum(int(r.get("hook_fired_count", 0)) for r in records)
    n_rows_fired = sum(1 for r in records if int(r.get("hook_fired_count", 0)) > 0)
    prefill = sum(int(r.get("n_prefill_edits", 0)) for r in records)
    decode = sum(int(r.get("n_decode_edits", 0)) for r in records)
    realised = sum(int(r.get("n_cells_edited_realised", 0)) for r in records)
    expected = sum(int(r.get("n_cells_edited_expected", 0)) for r in records)
    zero_dose = sum(1 for r in records if int(r.get("surface_span_n_tokens", 0)) <= 0)

    if expect_enabled:
        if n_fired == 0:
            reasons.append("hook_fired_count == 0 over all %d records: THE HOOK NEVER FIRED. This "
                           "arm's result is VOID, not a null." % len(records))
        if n_rows_fired < len(records):
            reasons.append("only %d/%d records show a firing hook -- a partially dead hook edits a "
                           "different population than the one reported"
                           % (n_rows_fired, len(records)))
        if prefill <= 0:
            reasons.append("n_prefill_edits == %d; the liveness contract for scope %r requires > 0"
                           % (prefill, knockout_scope(pr)))
        if decode != 0:
            reasons.append("n_decode_edits == %d; the contract requires exactly 0 on a "
                           "prefill-only scope. A non-zero value means the scoping LEAKED and the "
                           "mode is secretly a larger intervention than the one reported." % decode)
        if not expected:
            reasons.append("n_cells_edited_expected is 0 everywhere: the arm declared no "
                           "destinations, so 'realised == expected' is vacuously true and proves "
                           "nothing (a check that binds zero is not a check)")
        elif realised != expected:
            reasons.append("n_cells_edited_realised %d != expected %d (primary.void)"
                           % (realised, expected))
        if zero_dose:
            reasons.append("%d/%d records have a REALISED DOSE of 0 tokens -- the surface span "
                           "resolved to nothing and the arm cut nothing" % (zero_dose, len(records)))
    else:
        # the DISABLED-HOOK BRIDGE (K3): the code path runs and edits nothing.
        if any(bool(r.get("enabled", True)) for r in records):
            reasons.append("the disabled-hook bridge carries enabled=True records -- it EDITED "
                           "something, so it is not a bridge")
        if n_fired:
            reasons.append("the disabled-hook bridge reports hook_fired_count=%d" % n_fired)
        if realised:
            reasons.append("the disabled-hook bridge edited %d cells" % realised)
        if sum(int(r.get("n_forward", 0)) for r in records) == 0:
            reasons.append("the disabled-hook bridge made ZERO forward calls -- the code path was "
                           "not exercised at all, so it bridges nothing")
    return {"arm_id": arm_id, "live": (not reasons), "n_rows": len(records), "n_fired": n_fired,
            "n_prefill_edits": prefill, "n_decode_edits": decode, "n_zero_dose": zero_dose,
            "n_cells_realised": realised, "n_cells_expected": expected,
            "attn_implementations": sorted(impls), "expect_enabled": expect_enabled,
            "reasons": reasons}


def audit_end_relative(records: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    """P-N7: every edit and read index is `len(input_ids)+rel_end`, never a constant absolute int.

    `_absolute_index_is_void`: the ABSOLUTE index is identical across the three concepts in
    0/2300 triples while the END-RELATIVE index is identical in 2300/2300. An absolute index reads
    a DIFFERENT TOKEN in each arm. This repository's documented bug class, hit twice.
    """
    if not records:
        raise ZeroBinding("the end-relative audit bound ZERO records")
    bad = []
    for r in records:
        need = ("seq_len", "rel_end", "resolved_absolute_index")
        miss = [k for k in need if k not in r]
        if miss:
            raise Refusal("a liveness record is missing %s -- the end-relative audit cannot be "
                          "performed and is therefore not assumed to pass" % miss)
        if int(r["rel_end"]) >= 0:
            bad.append(("non-negative rel_end", r))
            continue
        if int(r["seq_len"]) + int(r["rel_end"]) != int(r["resolved_absolute_index"]):
            bad.append(("index != len(input_ids)+rel_end", r))
    lens = {int(r["seq_len"]) for r in records}
    abs_idx = {int(r["resolved_absolute_index"]) for r in records}
    if len(lens) > 1 and len(abs_idx) == 1:
        bad.append(("one absolute index across sequences of differing length", records[0]))
    return {"n_records": len(records), "n_violations": len(bad), "ok": not bad,
            "n_distinct_absolute_indices": len(abs_idx), "n_distinct_seq_len": len(lens),
            "witness_note": "the absolute index takes %d value(s) over %d sequence length(s); a "
                            "SINGLE value across differing lengths means an absolute index was "
                            "reused" % (len(abs_idx), len(lens))}


def read_site_gate(records: Sequence[Dict[str, Any]], pr: Prereg) -> Dict[str, Any]:
    """A mechanism outcome may not be computed from the concept-token row.

    Mandate section 13 in terms: "the naive probe AT the token bomb is invalid: it trivially reads
    lexical identity". `read_site.position_NOT_USED` names it; a delta whose read position is that
    site is refused rather than labelled.
    """
    want = read_position(pr)
    refused = refused_read_position(pr)
    seen = {str(r.get("read_position", "")) for r in records if r.get("read_position")}
    if refused in seen:
        raise Refusal(
            "an outcome was computed at read position %r, which the frozen file lists as "
            "position_NOT_USED. Reading a mechanism outcome at the concept token is the INVALID "
            "naive probe (mandate section 13); it is persisted as a DIAGNOSTIC and may not be "
            "described as evidence about the mechanism." % refused)
    unknown = seen - {want}
    if unknown:
        raise Refusal("outcome records carry unpreregistered read position(s) %s; the declared "
                      "downstream site is %r" % (sorted(unknown), want))
    return {"read_position": want, "refused_position": refused, "n_records": len(records),
            "ok": True}


def control_band_gate(per_draw_output_sha: Sequence[str], n_expected: int) -> Dict[str, Any]:
    """K2 / P-N5: three nondemo draws must produce THREE DISTINCT output hashes.

    "This project has twice published a 'control band' that was secretly n=1 because the seed never
    reached the draw." IDENTICAL HASHES VOID THE CONTROL BAND.
    """
    if not per_draw_output_sha:
        return {"ok": False, "n_draws": 0, "n_distinct": 0,
                "reason": "the control band recorded ZERO draws -- a band over no draws is not a "
                          "band, and its 'agreement' is vacuous"}
    n_distinct = len(set(per_draw_output_sha))
    ok = (len(per_draw_output_sha) == int(n_expected)) and (n_distinct == int(n_expected))
    return {"ok": ok, "n_draws": len(per_draw_output_sha), "n_expected": int(n_expected),
            "n_distinct": n_distinct,
            "reason": "" if ok else
                      "%d draw(s) produced %d distinct output hash(es), expected %d distinct. "
                      "Identical hashes mean the seed never reached the draw and the control band "
                      "is secretly n=1." % (len(per_draw_output_sha), n_distinct, int(n_expected))}


def disabled_bridge_gate(baseline_sha: str, bridge_sha: str, max_abs_hidden_diff: float
                         ) -> Dict[str, Any]:
    """K3 / P-N1: byte-identical greedy generations AND max|diff| == 0 hidden states."""
    same = (baseline_sha == bridge_sha) and bool(baseline_sha)
    zero = (float(max_abs_hidden_diff) == float(0))
    return {"ok": same and zero, "generations_byte_identical": same,
            "max_abs_hidden_diff": float(max_abs_hidden_diff),
            "reason": "" if (same and zero) else
                      "the disabled-hook bridge did not reproduce the untouched baseline "
                      "(byte-identical=%s, max|diff|=%r); the intervention code path changes the "
                      "result even with the hook off" % (same, max_abs_hidden_diff)}


def null_arm_gate(delta_values: Sequence[float], n_ledgered: int) -> Dict[str, Any]:
    """K4 / P-N4: at n_examples=0 there are no demonstrations to cut, so delta MUST be exactly 0
    (or the rows ledgered and absent, with the ledger count as the check)."""
    nonzero = [d for d in delta_values if float(d) != float(0)]
    if not delta_values and n_ledgered <= 0:
        return {"ok": False, "n": 0, "n_nonzero": 0,
                "reason": "the n_examples=0 arm produced NEITHER a delta NOR a ledger count; it "
                          "certifies nothing"}
    ok = not nonzero
    return {"ok": ok, "n": len(delta_values), "n_nonzero": len(nonzero),
            "n_ledgered": int(n_ledgered),
            "reason": "" if ok else
                      "%d/%d rows in the n_examples=0 arm carry a NON-ZERO delta. There are no "
                      "demonstrations to knock out, so a non-zero delta VOIDS the run."
                      % (len(nonzero), len(delta_values))}


# ============================================================================================
# 7. BASELINE BEFORE DELTA -- the ceiling mitigation, structurally
# ============================================================================================
def _quantile(xs: Sequence[float], q: float) -> float:
    if not xs:
        raise ZeroBinding("quantile over an EMPTY sample")
    s = sorted(float(x) for x in xs)
    if len(s) == 1:
        return s[0]
    pos = q * (len(s) - 1)
    lo = int(math.floor(pos))
    hi = min(lo + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (pos - lo)


@dataclass
class BaselineDistribution:
    """The FULL baseline distribution of the outcome, in the arm's own units.

    `primary._largest_risk` mitigation (1): "the baseline distribution of semantic_logodds in cell
    E is reported in full BEFORE any delta is interpreted". Here that is enforced by making the
    baseline an object a delta cannot exist without, and by `rendered` -- a delta refuses to render
    until its baseline has been rendered.
    """
    cell: str
    n_rows: int
    n_domains: int
    values: List[float] = field(default_factory=list)
    scored_range: Optional[Tuple[float, float]] = None
    option_mass_median: Optional[float] = None
    rendered: bool = False

    def __post_init__(self):
        if not self.values:
            raise ZeroBinding(
                "a BaselineDistribution for cell %r was constructed over ZERO values. The delta "
                "cannot be interpreted without the baseline it moves from." % self.cell)

    def summary(self, qs: Sequence[float]) -> Dict[str, Any]:
        n = len(self.values)
        m = sum(self.values) / n
        sd = math.sqrt(sum((x - m) ** 2 for x in self.values) / (n - 1)) if n > 1 else float("nan")
        return {"cell": self.cell, "n_rows": self.n_rows, "n_domains": self.n_domains,
                "n_values": n, "mean": m, "sd": sd,
                "min": min(self.values), "max": max(self.values),
                "quantiles": {("p%d" % int(round(q * 100))): _quantile(self.values, q)
                              for q in qs},
                "scored_range": self.scored_range,
                "option_mass_median": self.option_mass_median}

    def render(self, qs: Sequence[float], fh=sys.stdout) -> Dict[str, Any]:
        s = self.summary(qs)
        fh.write("  BASELINE cell %s -- reported IN FULL before any delta (primary._largest_risk)\n"
                 % self.cell)
        fh.write("    n_rows=%d n_domains=%d mean=%.6g sd=%.6g min=%.6g max=%.6g\n"
                 % (s["n_rows"], s["n_domains"], s["mean"], s["sd"], s["min"], s["max"]))
        fh.write("    quantiles: %s\n" % json.dumps(
            {k: round(v, 6) for k, v in s["quantiles"].items()}))
        fh.write("    scored_range=%s option_mass_median=%s\n"
                 % (s["scored_range"], s["option_mass_median"]))
        self.rendered = True
        return s


def ceiling_gate(baseline: BaselineDistribution, q: float) -> Dict[str, Any]:
    """`primary.cannot_answer` / kill condition 3: if the cell-E baseline's pQ sits at the top of
    the scored range, the arm is CANNOT ANSWER on CEILING grounds -- not a mechanism null.

    THE FROZEN FILE DECLARES NO NUMERIC CEILING CRITERION (defect PR058-D2 in the report). "At the
    top of the scored range" is only evaluable against a scored range the ARM must supply. If the
    arm does not supply one, this refuses rather than inventing a cut in the analyzer.
    """
    if baseline.scored_range is None:
        raise Refusal(
            "the cell-%s baseline carries no scored_range, so 'p%d at the top of the scored range' "
            "cannot be evaluated. The frozen file states the ceiling rule in prose without a "
            "numeric criterion (defect PR058-D2); the analyzer will not invent one. The producing "
            "arm must persist the scored range of semantic_logodds."
            % (baseline.cell, int(round(q * 100))))
    lo, hi = baseline.scored_range
    if not (hi > lo):
        raise Refusal("scored_range %r is not an increasing interval" % (baseline.scored_range,))
    val = _quantile(baseline.values, q)
    at_ceiling = val >= hi
    return {"cell": baseline.cell, "quantile": q, "value": val, "scored_range": [lo, hi],
            "at_ceiling": at_ceiling,
            "verdict": ("CANNOT ANSWER (ceiling): the p%d of the cell-%s baseline is at the top of "
                        "the scored range, so there is no headroom for the declared positive and a "
                        "null here is confounded with the ceiling"
                        % (int(round(q * 100)), baseline.cell)) if at_ceiling else "no ceiling"}


@dataclass
class PairedDelta:
    """A domain-level paired delta that CANNOT be constructed or rendered without its baseline."""
    cell: str
    hypothesis: str
    baseline: Optional[BaselineDistribution]
    per_domain: Dict[str, float]
    stats: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.baseline is None:
            raise Refusal(
                "a PairedDelta for cell %r was constructed with NO baseline distribution. "
                "`primary._largest_risk` mitigation (1) is that the full baseline is reported "
                "before any delta is interpreted; a delta object without one cannot enforce it."
                % self.cell)
        if not self.per_domain:
            raise ZeroBinding("the paired delta for cell %r bound ZERO domains" % self.cell)


def render_delta(d: PairedDelta, p_floor_value: float, fh=sys.stdout) -> str:
    """Emit a delta. REFUSES if its baseline has not been rendered first."""
    if d.baseline is None or not d.baseline.rendered:
        raise Refusal(
            "REFUSING to print the cell-%s delta: its baseline distribution has not been rendered. "
            "In cells B and E the query NAMES the concept, so logp_concept sits at a ceiling; a "
            "delta read without its baseline is uninterpretable in exactly the way "
            "primary._largest_risk describes." % d.cell)
    st = d.stats
    line = ("  DELTA  %s cell %s: domain-mean paired delta = %.6g over %d domains; %s"
            % (d.hypothesis, d.cell, st.get("observed_delta", float("nan")),
               len(d.per_domain),
               st.get("permutation", {}).get("formatted",
                                             "p unavailable [floor %.3e]" % p_floor_value)))
    fh.write(line + "\n")
    return line


# ============================================================================================
# 8. STATISTICS -- DOMAIN level only
# ============================================================================================
def forbid_non_domain_unit(unit: str, pr: Prereg) -> None:
    """Row-level permutation has a MEASURED FPR of 0.2000 on this design and does not exist here.

    There is no row-level code path to disable: the only permutation implemented is the
    domain-level one, and asking it for any other unit refuses.
    """
    want = independence_unit(pr)
    if str(unit) != want:
        raise Refusal(
            "permutation was requested at unit %r; the preregistered independence unit is %r. "
            "Row-level permutation has a MEASURED false-positive rate of 0.2000 on this design and "
            "appears in no arm, no secondary and no diagnostic of this phase. A significant "
            "row-level p-value does not establish a domain-level claim (mandate section 33)."
            % (unit, want))


def domain_group_permutation(per_domain_baseline: Dict[str, List[float]],
                             per_domain_ko: Dict[str, List[float]],
                             pr: Prereg, unit: str = "domain") -> Dict[str, Any]:
    """Arm-label flip WITHIN DOMAIN, at the DOMAIN level. The whole domain's paired sign flips
    together, so the unit of independence is respected by construction."""
    forbid_non_domain_unit(unit, pr)
    doms = sorted(set(per_domain_baseline) & set(per_domain_ko))
    if not doms:
        raise ZeroBinding("permutation bound ZERO domains -- the two arms share no domain")
    deltas = []
    for d in doms:
        a, b = per_domain_baseline[d], per_domain_ko[d]
        if not a or not b:
            raise ZeroBinding("domain %r contributes an empty arm to the paired contrast" % d)
        deltas.append(sum(b) / len(b) - sum(a) / len(a))
    obs = sum(deltas) / len(deltas)
    rng = random.Random(permutation_seed(pr))
    B = n_perm(pr)
    null = []
    for _ in range(B):
        null.append(sum((x if rng.getrandbits(1) else -x) for x in deltas) / len(deltas))
    p, floor, nex = group_permutation_p(abs(obs), [abs(x) for x in null])
    declared_floor = p_floor(pr)
    if abs(floor - declared_floor) > 1e-9:
        raise Refusal("the realised permutation floor %r disagrees with the preregistered "
                      "attainable_p_floor %r" % (floor, declared_floor))
    k = sum(1 for x in deltas if x > 0)
    ties = sum(1 for x in deltas if x == float(0))
    sp, sfloor = sign_test_two_sided(max(k, len(deltas) - k), len(deltas))
    return {"unit": unit, "n_domains": len(doms), "observed_delta": obs,
            "per_domain_delta": dict(zip(doms, deltas)),
            "permutation": {"p": p, "floor": floor, "n_exceed": nex, "n_perm": B,
                            "formatted": fmt_p(p, floor, nex)},
            "sign_test": {"k_positive": k, "n": len(deltas), "n_exact_ties": ties,
                          "p": sp, "floor": sfloor, "formatted": fmt_p(sp, sfloor)}}


def equivalence_interval(deltas: Sequence[float], a: float) -> Dict[str, Any]:
    """H3 / P-N9: a specificity control is reported WITH ITS INTERVAL, never as a bare p>alpha."""
    n = len(deltas)
    if n < 2:
        raise ZeroBinding("equivalence interval over n<2 domains")
    m = sum(deltas) / n
    sd = math.sqrt(sum((x - m) ** 2 for x in deltas) / (n - 1))
    se = sd / math.sqrt(n)
    try:
        from scipy import stats as _st
        tcrit = float(_st.t.isf(a / 2.0, n - 1))
    except Exception:                                       # pragma: no cover
        tcrit = float(196) / float(100)
    return {"n": n, "mean": m, "sd": sd, "se": se, "alpha": a,
            "ci_low": m - tcrit * se, "ci_high": m + tcrit * se,
            "_rule": "'p > alpha' is not a passed specificity control; the interval is the result"}


def family_members(pr: Prereg) -> List[str]:
    for fam in pr.require("multiplicity", "families"):
        if fam.get("name") == FAMILY_NAME:
            mem = list(fam["members"])
            if not mem:
                raise Refusal("multiplicity family %r declares no members" % FAMILY_NAME)
            return mem
    raise Refusal("multiplicity family %r is not declared in the preregistration" % FAMILY_NAME)


def member_ids(pr: Prereg) -> List[str]:
    """H1..H4, in declaration order, parsed out of the family membership strings."""
    out = []
    for m in family_members(pr):
        mm = re.search(r"\b(H\d+)\b", m)
        if not mm:
            raise Refusal("family member %r does not name a hypothesis id" % m)
        out.append(mm.group(1))
    return out


def holm(pvals: Dict[str, float], a: float, m: Optional[int] = None) -> Dict[str, Any]:
    """Holm-Bonferroni over the DECLARED family. A declared member that was not run enters at
    p = 1.0 (`_absent_members_enter_at_p_1`), never dropped: dropping it would shrink the family
    and make every surviving member easier to declare significant."""
    if not pvals:
        raise ZeroBinding("Holm over an EMPTY family")
    m = int(m or len(pvals))
    if m < len(pvals):
        raise Refusal("Holm was given %d p-values for a family of %d members" % (len(pvals), m))
    order = sorted(pvals.items(), key=lambda kv: kv[1])
    out, still = {}, True
    for i, (k, p) in enumerate(order):
        thr = a / (m - i)
        if still and p <= thr:
            out[k] = {"p": p, "threshold": thr, "reject": True}
        else:
            still = False
            out[k] = {"p": p, "threshold": thr, "reject": False}
    return {"m": m, "alpha": a, "per_member": out,
            "n_rejected": sum(1 for v in out.values() if v["reject"])}


def holm_with_absent(pr: Prereg, observed: Dict[str, float]) -> Dict[str, Any]:
    ids = member_ids(pr)
    unknown = sorted(set(observed) - set(ids))
    if unknown:
        raise Refusal("p-values supplied for non-members %s of family %r" % (unknown, FAMILY_NAME))
    pv = {h: float(observed.get(h, 1.0)) for h in ids}
    res = holm(pv, alpha(pr), m=len(ids))
    res["absent_members_at_p1"] = sorted(set(ids) - set(observed))
    return res


# ============================================================================================
# 9. POWER -- T3 as a code path
# ============================================================================================
def t3_power(pr: Prereg, validation_per_domain_delta: Dict[str, float],
             n_for_decision: Optional[int] = None) -> Dict[str, Any]:
    """Measure the between-domain SD on VALIDATION DOMAINS ONLY, then decide BEFORE reading test.

    `power.mde.in_semantic_logodds_nats` is deliberately null in the frozen file. A value
    pre-filled there would be the borrowed number the file explicitly refuses to carry, so finding
    one is a refusal rather than a convenience.
    """
    if pr.require("power", "mde", "in_semantic_logodds_nats") is not None:
        raise Refusal("power.mde.in_semantic_logodds_nats is no longer null in the frozen file. T3 "
                      "MEASURES it; a value pre-filled there would be the borrowed number the "
                      "file refuses to carry.")
    vals = list(validation_per_domain_delta.values())
    if len(vals) < 2:
        raise ZeroBinding("T3 measured the SD over %d validation domain(s)" % len(vals))
    m = sum(vals) / len(vals)
    sd = math.sqrt(sum((x - m) ** 2 for x in vals) / (len(vals) - 1))
    if sd <= float(0):
        raise Refusal("the measured between-domain SD is %r on validation. A zero SD means every "
                      "domain returned the identical value, which is the byte-identical-arms "
                      "signature, not a measurement." % sd)
    n = int(n_for_decision or pr.require("primary", "n_domains_analysed"))
    a, bar, mde = alpha(pr), power_bar(pr), declared_mde(pr)
    pw = t_power(n, mde, sd, alpha=a)
    realised_mde = t_mde(n, sd, alpha=a, power=bar)
    ok = pw >= bar
    return {"n_validation_domains": len(vals), "validation_mean_delta": m,
            "measured_between_domain_sd": sd, "declared_mde": mde, "alpha": a,
            "n_domains_for_decision": n, "power_at_declared_mde": pw, "power_bar": bar,
            "mde_at_power_bar": realised_mde, "power_ok": ok,
            "decision": ("PROCEED -- realised power %.4f >= the declared bar for the declared "
                         "effect" % pw) if ok else
                        ("CANNOT ANSWER WITHOUT READING TEST -- realised power %.4f is below the "
                         "declared bar for the declared %.4g-nat effect at the measured SD %.4f. "
                         "The realised MDE is %.4f nats. Mandate section 20: do not run a "
                         "confirmatory experiment whose likely negative would be uninterpretable."
                         % (pw, mde, sd, realised_mde))}


# ============================================================================================
# 10. KILL CONDITIONS -- code paths, not comments
# ============================================================================================
def kill_condition_channel(pr: Prereg, median_option_mass_by_cell: Dict[str, float]
                           ) -> Dict[str, Any]:
    """Kill 1 (T2): a DISENGAGED primary channel on cells B/E means no y to move. NO knockout job
    is submitted, and this is CANNOT ANSWER -- never a licence to fall back on the display
    channel, whose question names the concept on 100% of its rows."""
    gate = option_mass_gate_value(pr)
    if not median_option_mass_by_cell:
        raise Refusal("no option_mass was measured on any cell; the channel's engagement is "
                      "unmeasured and cannot be assumed (checklist T2)")
    below = {c: v for c, v in median_option_mass_by_cell.items() if float(v) < gate}
    return {"gate": gate, "measured": dict(median_option_mass_by_cell),
            "killed": bool(below), "cells_below_gate": sorted(below),
            "reason": "" if not below else
                      "median option_mass on cell(s) %s is below the %.4g gate: the "
                      "semantic_one_word channel is DISENGAGED, so there is no y to move. NO "
                      "knockout job is submitted. CANNOT ANSWER -- and falling back on the "
                      "display channel is FORBIDDEN in this phase."
                      % (sorted(below), gate)}


def kill_condition_whole_query(whole_query_moved: Optional[bool]) -> Dict[str, Any]:
    """Kill 2 (K6): if the WHOLE-QUERY knockout does not move the cell-E readout, the surgical
    single-row scope is NOT submitted -- a one-row cut cannot be expected to do what cutting the
    entire query span could not."""
    if whole_query_moved is None:
        return {"killed": False, "evaluated": False,
                "reason": "the legacy_all_query comparison has not been run; the second kill "
                          "condition is UNEVALUATED and is reported as such rather than as passed"}
    return {"killed": not whole_query_moved, "evaluated": True,
            "reason": "" if whole_query_moved else
                      "the WHOLE-QUERY knockout does not move the cell-E readout, so there is "
                      "nothing for the surgical one-row scope to localise. The surgical arm is "
                      "NOT submitted."}


def kill_condition_ceiling(baseline_E: BaselineDistribution, pr: Prereg) -> Dict[str, Any]:
    g = ceiling_gate(baseline_E, ceiling_quantile(pr))
    return {"killed": g["at_ceiling"], "detail": g,
            "reason": g["verdict"] if g["at_ceiling"] else ""}


# ============================================================================================
# 11. THE CONJUNCTIVE SUCCESS RULE, THE COPY ACCOUNT, AND THE VERDICT
# ============================================================================================
def success_conditions(pr: Prereg) -> List[str]:
    conds = pr.require("primary", "success", "conditions")
    if len(conds) < 2:
        raise Refusal("primary.success.conditions declares %d condition(s); the rule is declared "
                      "CONJUNCTIVE and cannot be evaluated from one" % len(conds))
    return [str(c) for c in conds]


def _sign(x: float) -> int:
    return (x > float(0)) - (x < float(0))


def copy_vs_mechanism(delta_E: float, delta_C: float) -> Dict[str, Any]:
    """`primary._largest_risk` mitigation (3): the copy account and the mechanism account predict
    OPPOSITE SIGNS for H1 relative to H2, and both were declared before any data exist.

    MECHANISM: cutting the demonstrations off the final row RESTORES the literal reading in cell E
    (delta_E > 0) and DESTROYS the installed reading in cell C (delta_C < 0) -- opposite signs.
    COPY: the cell-E readout is driven by the concept word being present in the query, which the
    intervention does not remove, so cell E should not move with cell C's sign structure; a cell-E
    delta that tracks cell C's sign is the copy account's signature, not the mechanism's.
    """
    sE, sC = _sign(delta_E), _sign(delta_C)
    if sE == 0 or sC == 0:
        account = "UNDETERMINED -- a zero delta discriminates nothing"
    elif sE > 0 and sC < 0:
        account = ("MECHANISM-CONSISTENT -- opposite signs, as H1 and H2 declared before any data "
                   "existed")
    elif sE == sC:
        account = ("COPY-CONSISTENT -- cell E moves with the same sign as cell C, which the "
                   "mechanism account did not predict; the model copying a word out of its own "
                   "prompt is not excluded")
    else:
        account = ("NEITHER -- the observed sign pair (%+d, %+d) matches neither declared account"
                   % (sE, sC))
    return {"sign_E": sE, "sign_C": sC, "delta_E": delta_E, "delta_C": delta_C,
            "opposite_signs": bool(sE and sC and sE == -sC), "account": account}


def evaluate_success(pr: Prereg, h1: Dict[str, Any], h2: Dict[str, Any], h3: Dict[str, Any],
                     k2: Dict[str, Any], holm_res: Dict[str, Any]) -> Dict[str, Any]:
    """All four conditions TOGETHER. Any three of four is not a symmetry result."""
    conds = success_conditions(pr)
    a = alpha(pr)
    rows = []
    rej = holm_res["per_member"]
    rows.append({
        "condition": conds[0],
        "passed": bool(h1.get("observed_delta", float(0)) > float(0)
                       and rej.get("H1", {}).get("reject", False)),
        "detail": "delta_E=%r Holm-reject=%s" % (h1.get("observed_delta"),
                                                 rej.get("H1", {}).get("reject"))})
    rows.append({
        "condition": conds[1],
        "passed": bool(h2.get("observed_delta", float(0)) < float(0)
                       and rej.get("H2", {}).get("reject", False)),
        "detail": "delta_C=%r Holm-reject=%s" % (h2.get("observed_delta"),
                                                 rej.get("H2", {}).get("reject"))})
    eq = h3.get("equivalence") or {}
    rows.append({
        "condition": conds[2],
        "passed": bool(eq) and not bool(h3.get("moved_beyond_control", True)),
        "detail": "equivalence CI=[%s, %s] (a bare p > %g is NOT a passed control)"
                  % (eq.get("ci_low"), eq.get("ci_high"), a)})
    rows.append({
        "condition": conds[3],
        "passed": bool(k2.get("ok")) and not bool(k2.get("reproduces_h1", True)),
        "detail": "distinct_hashes_ok=%s reproduces_H1=%s"
                  % (k2.get("ok"), k2.get("reproduces_h1"))})
    n_pass = sum(1 for r in rows if r["passed"])
    return {"conditions": rows, "n_conditions": len(rows), "n_passed": n_pass,
            "success": n_pass == len(rows),
            "_conjunctive": "all %d are required TOGETHER; %d of %d is not a symmetry result"
                            % (len(rows), n_pass, len(rows))}


def verdict(pr: Prereg, success: Dict[str, Any], liveness_clean: bool,
            cannot_answer_reasons: Sequence[str], h1_moved: bool, h2_moved: bool,
            forbidden: Sequence[str]) -> str:
    """The verdict. REFUSES on unclean liveness before it can produce any of the four outcomes."""
    if not liveness_clean:
        raise Refusal(
            "REFUSING to emit any verdict: hook liveness is UNCLEAN. A dead hook, an SDPA arm, a "
            "leaked decode edit or a zero realised dose produces EXACTLY the artifact a real "
            "intervention with no effect produces. That is VOID, not a negative, and a verdict "
            "here would be the strongest possible wrong answer.")
    if cannot_answer_reasons:
        return assert_sayable(
            "CANNOT ANSWER -- %s. This is reported as CANNOT ANSWER and explicitly NOT as a "
            "mechanism null." % "; ".join(cannot_answer_reasons), forbidden)
    # The VOID branch is evaluated BEFORE the success branch on purpose. A "success" reported over
    # two arms that did not move is incoherent, and the incoherent case must refuse rather than
    # take whichever branch happens to be tested first.
    if not h2_moved and not h1_moved:
        raise Refusal(
            "NEITHER H1 NOR H2 moved. `primary.negative._the_other_negative`: the intervention did "
            "not do what it claims -- check hook liveness, the realised dose, the disabled-hook "
            "bridge and the eager-attention record. That is VOID, not a negative.")
    if success.get("success"):
        return assert_sayable(
            "POSITIVE -- all %d conjunctive conditions passed. Scope: one row's incoming "
            "demonstration attention was masked over the declared band, on this bank, at this "
            "dose, on Llama-3.1-8B-Instruct only." % success.get("n_conditions", 0), forbidden)
    if h2_moved and not h1_moved:
        return assert_sayable(check_wording_pin(pr), forbidden)
    return assert_sayable(
        "NO VERDICT -- %d of %d conjunctive conditions passed and the declared negative's "
        "precondition (H2 reproduces, H1 does not move) is not met."
        % (success.get("n_passed", 0), success.get("n_conditions", 0)), forbidden)


# ============================================================================================
# 12. ARM MANIFEST AND PLAN
# ============================================================================================
def primary_banks(pr: Prereg) -> List[str]:
    """The banks carrying the CONFIRMATORY concept. knife and gun are REGISTERED DESCRIPTIVE."""
    concept = str(pr.require("population", "concept_primary"))
    banks = pr.require("population", "banks")
    out = sorted(k for k in banks if k.endswith("_" + concept))
    if not out:
        raise Refusal("no bank carries the primary concept %r" % concept)
    return out


def descriptive_banks(pr: Prereg) -> List[str]:
    return sorted(set(pr.require("population", "banks")) - set(primary_banks(pr)))


def refuse_pooling_across_banks(bank_keys: Sequence[str]) -> str:
    """`_two_codewords_are_a_transfer_pair_not_a_pool` and `primary.statistic`: every estimate is
    reported PER CODEWORD BANK and never pooled into one p-value.

    On the primary channel button_bomb installs in 92/113 domains and basket_bomb in 46/113 -- a
    factor of two from the lexical codeword alone -- so a pooled estimate is an average over two
    populations that differ in the thing being measured.
    """
    keys = list(bank_keys)
    if len(keys) != 1:
        raise Refusal(
            "an estimate was requested over %d banks (%s). The two codewords are a declared "
            "TRANSFER PAIR, not a pool: every estimate is reported PER CODEWORD BANK and is NEVER "
            "pooled into one p-value." % (len(keys), keys))
    return keys[0]


def refuse_descriptive_as_confirmatory(pr: Prereg, bank_key: str) -> str:
    """The knife and gun arms carry NO multiplicity membership and no p-value may be quoted from
    them as a mechanism result: knife installs in 0/113 domains and gun in 1/113, so an arm read as
    'the knockout removed the installed concept' had no installed concept to remove."""
    if bank_key in descriptive_banks(pr):
        raise Refusal(
            "bank %r is a REGISTERED DESCRIPTIVE arm and carries no confirmatory weight. %s"
            % (bank_key, pr.require("installation",
                                    "THE_ASYMMETRY_AND_WHAT_IT_MAKES_UNCONSTRUCTIBLE",
                                    "consequence")))
    return bank_key


@dataclass
class ArmSpec:
    arm_id: str
    bank: str
    cell: str
    control_id: str
    name: str
    expect_enabled: bool
    blocking: bool
    n_examples: int
    query_kind: str
    confirmatory: bool

    def tag(self) -> str:
        return "pr058_%s_%s_%s_n%d" % (self.bank, self.control_id.lower(), self.cell.lower(),
                                       self.n_examples)


def build_arm_manifest(pr: Prereg, banks: Optional[Sequence[str]] = None) -> List[ArmSpec]:
    cells = list(cell_specs(pr))
    bank_keys = list(banks) if banks is not None else primary_banks(pr)
    conf = set(primary_banks(pr))
    qk = str(pr.require("population", "query_kind_primary"))
    dose = int(pr.require("population", "n_examples_primary"))
    null_dose = int(pr.require("population", "n_examples_null"))
    arms: List[ArmSpec] = []
    for c in pr.require("controls", "arms"):
        cid, name, blocking = str(c["id"]), str(c["name"]), bool(c["blocking"])
        expect_enabled = cid not in ("K1", "K3")
        if cid == "K4":
            doses = [null_dose]
        elif cid == "K7":
            doses = [int(pr.require("population", "n_examples_replication"))]
        else:
            doses = [dose]
        targets = [cells[cells.index("B")]] if cid == "K5" else cells
        for bk in bank_keys:
            for cell in targets:
                for d in doses:
                    arms.append(ArmSpec(
                        arm_id="%s_%s_%s_n%d" % (bk, cid, cell, d), bank=bk, cell=cell,
                        control_id=cid, name=name, expect_enabled=expect_enabled,
                        blocking=blocking, n_examples=d, query_kind=qk,
                        confirmatory=(bk in conf)))
    if not arms:
        raise Refusal("the arm manifest is empty -- controls.arms declares nothing")
    return arms


def launch_command(pr: Prereg, arm: ArmSpec) -> str:
    lo, hi = intervention_band(pr)
    parts = ["python3 scripts/dcs_ts_readout_multi.py",
             "--bank %s" % pr.require("population", "banks", arm.bank, "path"),
             "--only-cell %s" % arm.cell,
             "--only-query-kind %s" % arm.query_kind,
             "--only-n-examples %d" % arm.n_examples,
             "--attn-impl %s" % required_attn_impl(pr)]
    if arm.control_id != "K1":
        parts.append("--knockout-scope %s" % knockout_scope(pr))
        parts.append("--intervene demo_all:attn_knockout:%d-%d:1.0" % (lo, hi))
    if arm.control_id == "K3":
        parts.append("--disable-hook")
    if arm.control_id == "K2":
        parts.append("--nondemo-matched-draws %d --nondemo-draw-seed %d"
                     % (n_control_draws(pr), int(pr.require("seeds", "control_draws"))))
    if arm.control_id == "K6":
        parts.append("--knockout-scope legacy_all_query")
    return " ".join(parts)


def plan(pr: Prereg) -> int:
    arms = build_arm_manifest(pr)
    lo, hi = intervention_band(pr)
    print("=== %s PHASE 10 arm manifest ===" % PR_ID)
    print("  scope=%s band=blocks %d-%d attn=%s read_position=%s primary_read_layer=%d grid=%s"
          % (knockout_scope(pr), lo, hi, required_attn_impl(pr), read_position(pr),
             primary_read_layer(pr), read_layers(pr)))
    print("  selector field=%r (NEVER %r -- A-039); whole-population exclusions=%s"
          % (SELECTOR_FIELD, FORBIDDEN_SELECTOR_FIELD, whole_population_exclusions(pr)))
    print("  alpha=%g n_perm=%d p_floor=%.4e option_mass_gate=%g power_bar=%g mde=%g "
          "installation_cut=%g" % (alpha(pr), n_perm(pr), p_floor(pr), option_mass_gate_value(pr),
                                   power_bar(pr), declared_mde(pr), installation_cut(pr)))
    print("  multiplicity family %s members=%s" % (FAMILY_NAME, member_ids(pr)))
    print("  CONFIRMATORY banks=%s; REGISTERED DESCRIPTIVE (no confirmatory weight, no p-value "
          "quotable as a mechanism result)=%s; the two codewords are a TRANSFER PAIR and are "
          "NEVER pooled into one p-value"
          % (primary_banks(pr), descriptive_banks(pr)))
    for a in arms:
        print("  %-26s bank=%s cell=%s blocking=%s expect_hook=%s confirmatory=%s tag=%s"
              % (a.arm_id, a.bank, a.cell, a.blocking, a.expect_enabled, a.confirmatory, a.tag()))
        print("      %s" % launch_command(pr, a))
    print("[plan] %d arm(s)" % len(arms))
    return 0


# ============================================================================================
# 13. SELF-TEST
# ============================================================================================
def _lr(**kw) -> Dict[str, Any]:
    """A liveness record that is clean unless a field is overridden."""
    base = LivenessRecord(arm_id="u", prompt_id="p", enabled=True, hook_fired_count=1, n_forward=1,
                          n_prefill_edits=1, n_decode_edits=0, keys_masked=4,
                          surface_span_n_tokens=1, n_cells_edited_expected=1,
                          n_cells_edited_realised=1, attn_implementation="eager",
                          seq_len=100, rel_end=-10, resolved_absolute_index=90,
                          read_position="following", output_sha256="a").as_row()
    base.update(kw)
    return base


def _fake_bank(cells=("B", "C", "E"), n_dom=4, qk="semantic_one_word", dose=4,
               condition_map=None) -> Dict[str, Dict[str, Any]]:
    cond = condition_map or {"B": "direct_harmful", "C": "natural_doublespeak",
                             "E": "concept_in_benign_ctx"}
    out = {}
    for c in cells:
        for i in range(n_dom):
            pid = "%s_%d" % (c, i)
            out[pid] = {"prompt_id": pid, "cell": c, "condition": cond[c],
                        "query_kind": qk, "n_examples": dose, "domain": "dom%d" % i,
                        "concept": "bomb", "codeword": "button"}
    return out


def selftest(pr: Prereg) -> int:
    ck = Checks()

    # ---- gates come from the frozen file, and the file's own arithmetic agrees ----------
    ck.add("p_floor_consistent", "attainable_p_floor == 1/(n_perm+1), re-derived not quoted",
           abs(p_floor(pr) - 1.0 / (n_perm(pr) + 1.0)) < 1e-12, 1,
           "floor=%.6e n_perm=%d" % (p_floor(pr), n_perm(pr)))
    ck.add("gates_parsed", "the option_mass gate, the power bar and the ceiling quantile are "
           "PARSED out of the frozen file's prose, not re-typed",
           option_mass_gate_value(pr) > 0 and power_bar(pr) > 0 and 0 < ceiling_quantile(pr) < 1,
           3, "om=%g bar=%g q=%g" % (option_mass_gate_value(pr), power_bar(pr),
                                     ceiling_quantile(pr)))
    aud = source_gate_literal_audit(pr)
    ck.add("no_gate_literals", "this analyzer's own source contains NO declared gate value as a "
           "numeric literal", aud["ok"], aud["n_gates_checked"],
           "violations=%s" % aud["violations"])
    caught = False
    try:
        assert_gate_from_prereg("primary.alpha", alpha(pr) * 2.0, pr)
    except Refusal:
        caught = True
    ck.add("literal_gate_refused", "a threshold supplied as a literal instead of from the prereg "
           "is refused", caught, 1)

    # ---- wording ------------------------------------------------------------------------
    ck.add("wording_pin", "the mandatory negative wording in the code equals the frozen file's",
           check_wording_pin(pr) == MANDATORY_NEGATIVE_WORDING, 1)
    forb = forbidden_from_prereg(pr)
    caught = False
    try:
        assert_sayable("this shows k=7 proves the bomb token is the mechanism", forb)
    except Refusal:
        caught = True
    ck.add("forbidden_wording", "a mandate-33 forbidden claim cannot be emitted", caught,
           len(forb))

    # ---- population binding --------------------------------------------------------------
    assign = {"dom%d" % i: ("train" if i < 2 else "test") for i in range(4)}
    bank = _fake_bank()
    b = bind_rows(pr, bank, "E", assign)
    ck.add("bind_cell", "binding on `cell` returns rows and domains", b["n_rows"] > 0
           and b["n_domains"] > 0, b["n_rows"], "domains=%d" % b["n_domains"])
    caught = False
    try:
        bind_rows(pr, bank, "E", assign, selector_field=FORBIDDEN_SELECTOR_FIELD)
    except Refusal:
        caught = True
    ck.add("selector_field", "binding on `condition` is refused before it can bind zero (A-039)",
           caught, 1)
    caught = False
    try:
        bind_rows(pr, {}, "E", assign)
    except ZeroBinding:
        caught = True
    ck.add("zero_row_bind", "a zero-row bind RAISES, never returns an empty result", caught, 1)
    excl = whole_population_exclusions(pr)
    ck.add("exclusions_structured", "the whole-population exclusions come from the boolean field",
           len(excl) == 3 and all(isinstance(x, str) for x in excl), len(excl), "%s" % excl)

    # ---- installation is a stratifier ----------------------------------------------------
    per_dom = {"a": 1.0, "b": -1.0}
    st = stratify_by_installation(per_dom, {"a": installation_cut(pr) + 0.1,
                                            "b": installation_cut(pr) - 0.1},
                                  installation_cut(pr))
    ck.add("stratification", "installation splits into two strata and drops NOTHING",
           st["n_pooled"] == 2 and st["n_installing"] == 1 and st["n_non_installing"] == 1, 2)
    caught = False
    try:
        stratify_by_installation(per_dom, {"a": 1.0}, installation_cut(pr))
    except Refusal:
        caught = True
    ck.add("stratum_missing", "a domain with no installation statistic refuses rather than being "
           "silently dropped (mandate 15)", caught, 1)
    caught = False
    try:
        refuse_installation_as_exclusion(["dom0"])
    except Refusal:
        caught = True
    ck.add("install_not_exclusion", "installation used as a post-hoc exclusion is refused", caught, 1)

    # ---- liveness -------------------------------------------------------------------------
    lg = liveness_gate([_lr()], "u", pr)
    ck.add("liveness_clean", "a clean prefill-only knockout record passes", lg["live"], 1,
           "; ".join(lg["reasons"])[:120])
    dead = liveness_gate([_lr(hook_fired_count=0)], "u", pr)
    ck.add("dead_hook", "hook_fired_count == 0 is VOID, not a null", not dead["live"], 1)
    sdpa = liveness_gate([_lr(attn_implementation="sdpa")], "u", pr)
    ck.add("sdpa_void", "an arm whose LOADED config is not eager is VOID (C-047)",
           not sdpa["live"], 1)
    leak = liveness_gate([_lr(n_decode_edits=2)], "u", pr)
    ck.add("decode_leak", "a non-zero n_decode_edits on a prefill-only scope refuses",
           not leak["live"], 1)
    dose0 = liveness_gate([_lr(surface_span_n_tokens=0)], "u", pr)
    ck.add("zero_dose", "a zero realised dose refuses", not dose0["live"], 1)
    nolive = liveness_gate([], "u", pr)
    ck.add("no_liveness_records", "an arm with no liveness records at all is VOID", not
           nolive["live"], 1)
    bridge = liveness_gate([_lr(enabled=False, hook_fired_count=0, n_prefill_edits=0,
                                n_cells_edited_realised=0, n_forward=3)], "K3", pr,
                           expect_enabled=False)
    as_live = liveness_gate([_lr(enabled=False, hook_fired_count=0, n_prefill_edits=0,
                                 n_cells_edited_realised=0, n_forward=3)], "K3", pr)
    ck.add("bridge", "the disabled-hook bridge passes as a bridge and REFUSES as a live arm",
           bridge["live"] and not as_live["live"], 1)

    # ---- indices --------------------------------------------------------------------------
    a1 = audit_end_relative([_lr(seq_len=100, rel_end=-10, resolved_absolute_index=90),
                             _lr(seq_len=137, rel_end=-10, resolved_absolute_index=127)])
    ck.add("end_relative", "len(input_ids)+rel_end passes and the absolute index VARIES",
           a1["ok"] and a1["n_distinct_absolute_indices"] == 2, a1["n_records"])
    a2 = audit_end_relative([_lr(seq_len=100, rel_end=-10, resolved_absolute_index=90),
                             _lr(seq_len=137, rel_end=-10, resolved_absolute_index=90)])
    ck.add("absolute_index", "an ABSOLUTE index reused across differing lengths is caught",
           not a2["ok"], a2["n_records"])

    # ---- read site -------------------------------------------------------------------------
    rs = read_site_gate([_lr(read_position=read_position(pr))], pr)
    ck.add("read_site", "the declared downstream site passes", rs["ok"], rs["n_records"])
    caught = False
    try:
        read_site_gate([_lr(read_position=refused_read_position(pr))], pr)
    except Refusal:
        caught = True
    ck.add("concept_token_site", "an outcome at the concept-token site is REFUSED (mandate 13)",
           caught, 1)

    # ---- controls ---------------------------------------------------------------------------
    n_draws = n_control_draws(pr)
    ck.add("control_band", "%d distinct draw hashes pass; identical hashes VOID the band" % n_draws,
           control_band_gate([str(i) for i in range(n_draws)], n_draws)["ok"]
           and not control_band_gate(["z"] * n_draws, n_draws)["ok"], n_draws)
    ck.add("bridge_gate", "the disabled-hook bridge must reproduce byte-for-byte",
           disabled_bridge_gate("aa", "aa", float(0))["ok"]
           and not disabled_bridge_gate("aa", "bb", float(0))["ok"], 2)
    ck.add("null_arm", "a non-zero delta at n_examples=0 voids the run",
           null_arm_gate([float(0), float(0)], 0)["ok"]
           and not null_arm_gate([float(0), 0.3], 0)["ok"], 2)

    # ---- baseline before delta ----------------------------------------------------------------
    bl = BaselineDistribution(cell="E", n_rows=10, n_domains=5, values=[0.1, 0.2, 0.3, 0.4, 0.45],
                              scored_range=(-2.0, 2.0), option_mass_median=0.2)
    pd_ok = PairedDelta(cell="E", hypothesis="H1", baseline=bl, per_domain={"a": 0.2, "b": 0.4},
                        stats={"observed_delta": 0.3})
    caught = False
    try:
        render_delta(pd_ok, p_floor(pr), fh=open(os.devnull, "w"))
    except Refusal:
        caught = True
    ck.add("delta_needs_baseline", "a delta REFUSES to print before its baseline is rendered",
           caught, 1)
    bl.render([ceiling_quantile(pr)], fh=open(os.devnull, "w"))
    ck.add("delta_after_baseline", "the same delta prints once the baseline has been rendered",
           bool(render_delta(pd_ok, p_floor(pr), fh=open(os.devnull, "w"))), 1)
    caught = False
    try:
        PairedDelta(cell="E", hypothesis="H1", baseline=None, per_domain={"a": 0.2})
    except Refusal:
        caught = True
    ck.add("no_baseline_object", "a delta cannot be constructed without a baseline at all",
           caught, 1)

    # ---- ceiling ------------------------------------------------------------------------------
    hi_bl = BaselineDistribution(cell="E", n_rows=10, n_domains=5, values=[1.9, 2.0, 2.0, 2.0, 2.0],
                                 scored_range=(-2.0, 2.0))
    ck.add("ceiling", "a baseline whose upper quantile sits at the top of the scored range is "
           "CANNOT ANSWER on ceiling grounds",
           ceiling_gate(hi_bl, ceiling_quantile(pr))["at_ceiling"]
           and not ceiling_gate(bl, ceiling_quantile(pr))["at_ceiling"], 2)
    caught = False
    try:
        ceiling_gate(BaselineDistribution(cell="E", n_rows=1, n_domains=1, values=[0.1]),
                     ceiling_quantile(pr))
    except Refusal:
        caught = True
    ck.add("ceiling_no_range", "with no scored range the ceiling rule REFUSES rather than "
           "inventing a cut (defect PR058-D2)", caught, 1)

    # ---- statistics ---------------------------------------------------------------------------
    base = {("d%d" % i): [0.0] for i in range(20)}
    ko_pos = {("d%d" % i): [0.6 + 0.01 * i] for i in range(20)}
    perm = domain_group_permutation(base, ko_pos, pr)
    ck.add("domain_permutation", "domain-level permutation on a clear positive effect",
           perm["observed_delta"] > 0 and perm["permutation"]["p"] <= alpha(pr),
           perm["n_domains"], perm["permutation"]["formatted"])
    ck.add("p_beside_floor", "every p is formatted beside its attainable floor",
           "floor" in perm["permutation"]["formatted"].lower()
           and "floor" in perm["sign_test"]["formatted"].lower(), 2)
    caught = False
    try:
        domain_group_permutation(base, ko_pos, pr, unit="row")
    except Refusal:
        caught = True
    ck.add("row_level_forbidden", "a row-level permutation attempt is REFUSED; no row-level code "
           "path exists", caught, 1)
    caught = False
    try:
        domain_group_permutation({}, {}, pr)
    except ZeroBinding:
        caught = True
    ck.add("perm_zero_domains", "permutation over zero domains raises", caught, 1)
    nul = domain_group_permutation(base, {("d%d" % i): [0.0] for i in range(20)}, pr)
    ck.add("perm_null_centred", "P-N6: the domain-level null is centred at 0 on a null input",
           abs(nul["observed_delta"]) < 1e-12, nul["n_domains"])

    eq = equivalence_interval([0.01, -0.02, 0.0, 0.03, -0.01], alpha(pr))
    ck.add("equivalence", "H3 is reported with an interval, not a bare p", "ci_low" in eq
           and "ci_high" in eq and eq["ci_low"] < eq["ci_high"], eq["n"])

    ids = member_ids(pr)
    hres = holm_with_absent(pr, {"H1": 0.001, "H2": 0.002})
    ck.add("holm_absent", "a declared member that did not run enters Holm at p=1.0, never dropped",
           hres["m"] == len(ids) and set(hres["absent_members_at_p1"]) == set(ids) - {"H1", "H2"},
           hres["m"], "absent=%s" % hres["absent_members_at_p1"])
    caught = False
    try:
        holm({}, alpha(pr))
    except ZeroBinding:
        caught = True
    ck.add("holm_empty", "Holm over an empty family raises", caught, 1)

    # ---- equal populations --------------------------------------------------------------------
    ep = assert_equal_populations({"K1": ["a", "b"], "K2": ["a", "b"]})
    ep_bad = assert_equal_populations({"K1": ["a", "b"], "K2": ["a"]})
    ck.add("equal_populations", "unequal per-arm populations are caught (P-N8)",
           ep["ok"] and not ep_bad["ok"], 2)

    # ---- kill conditions and power --------------------------------------------------------------
    g = option_mass_gate_value(pr)
    k1 = kill_condition_channel(pr, {"E": g / 2.0, "B": g * 2.0})
    ck.add("kill_channel", "a disengaged primary channel kills the phase and is CANNOT ANSWER",
           k1["killed"] and k1["cells_below_gate"] == ["E"], 2)
    ck.add("kill_whole_query", "the K6 kill condition is UNEVALUATED, not passed, when K6 has not "
           "run", not kill_condition_whole_query(None)["killed"]
           and not kill_condition_whole_query(None)["evaluated"]
           and kill_condition_whole_query(False)["killed"], 2)
    ck.add("kill_ceiling", "the ceiling kill condition fires on a ceilinged baseline",
           kill_condition_ceiling(hi_bl, pr)["killed"], 1)

    pw_ok = t3_power(pr, {("d%d" % i): (declared_mde(pr) + 0.001 * i) for i in range(30)})
    pw_bad = t3_power(pr, {("d%d" % i): (declared_mde(pr) * (1 if i % 2 else -1) * (i + 1))
                           for i in range(30)})
    ck.add("t3_power", "T3 measures the SD on validation and returns CANNOT ANSWER WITHOUT READING "
           "TEST below the bar as a CODE PATH",
           pw_ok["power_ok"] and not pw_bad["power_ok"]
           and "CANNOT ANSWER WITHOUT READING TEST" in pw_bad["decision"], 2,
           "sd_ok=%.4f sd_bad=%.4f" % (pw_ok["measured_between_domain_sd"],
                                       pw_bad["measured_between_domain_sd"]))

    # ---- copy vs mechanism, success, verdict ------------------------------------------------------
    cvm = copy_vs_mechanism(0.4, -0.3)
    cvm_copy = copy_vs_mechanism(0.4, 0.3)
    ck.add("copy_vs_mechanism", "the copy account and the mechanism account are discriminated by "
           "the SIGN pair, both declared before the data",
           cvm["opposite_signs"] and "MECHANISM" in cvm["account"]
           and "COPY" in cvm_copy["account"], 2)

    good = {"observed_delta": 0.55}
    bad = {"observed_delta": -0.55}
    hr = holm_with_absent(pr, {"H1": 0.001, "H2": 0.001, "H3": 0.9, "H4": 0.001})
    succ4 = evaluate_success(pr, good, bad, {"equivalence": eq, "moved_beyond_control": False},
                             {"ok": True, "reproduces_h1": False}, hr)
    succ3 = evaluate_success(pr, good, bad, {"equivalence": eq, "moved_beyond_control": True},
                             {"ok": True, "reproduces_h1": False}, hr)
    ck.add("conjunctive", "all conditions together pass; any one failing does not",
           succ4["success"] and not succ3["success"]
           and succ3["n_passed"] == succ4["n_conditions"] - 1, succ4["n_conditions"])

    caught = False
    try:
        verdict(pr, succ4, False, [], True, True, forb)
    except Refusal:
        caught = True
    ck.add("verdict_unclean_liveness", "no verdict is emitted on unclean hook liveness", caught, 1)
    v_neg = verdict(pr, succ3, True, [], False, True, forb)
    ck.add("negative_wording", "the declared negative is emitted in its MANDATORY wording",
           v_neg == MANDATORY_NEGATIVE_WORDING, 1)
    caught = False
    try:
        verdict(pr, succ3, True, [], False, False, forb)
    except Refusal:
        caught = True
    ck.add("neither_moved_is_void", "if NEITHER H1 nor H2 moves the run is VOID, not a negative",
           caught, 1)
    v_ca = verdict(pr, succ3, True, ["the primary channel is disengaged"], False, True, forb)
    ck.add("cannot_answer_branch", "CANNOT ANSWER is an explicit branch and says it is not a null",
           v_ca.startswith("CANNOT ANSWER") and "NOT as a mechanism null" in v_ca, 1)

    # ---- arm manifest ---------------------------------------------------------------------------
    arms = build_arm_manifest(pr)
    ck.add("arm_manifest", "every declared control arm produces at least one arm spec, per bank",
           len({a.control_id for a in arms}) == len(pr.require("controls", "arms"))
           and {a.bank for a in arms} == set(primary_banks(pr)), len(arms),
           "banks=%s" % sorted({a.bank for a in arms}))
    caught = False
    try:
        refuse_pooling_across_banks(primary_banks(pr))
    except Refusal:
        caught = True
    ck.add("no_bank_pooling", "the two codeword banks are a TRANSFER PAIR and pooling them into "
           "one p-value is refused", caught and
           refuse_pooling_across_banks(primary_banks(pr)[:1]) == primary_banks(pr)[0], 2)
    caught = False
    try:
        refuse_descriptive_as_confirmatory(pr, descriptive_banks(pr)[0])
    except Refusal:
        caught = True
    ck.add("descriptive_not_confirmatory", "a knife/gun arm cannot be quoted as a mechanism "
           "result (installs in 0/113 and 1/113 domains)", caught, len(descriptive_banks(pr)))
    # PR058-D1 RESOLVED 2026-09-07 by RENAMING THIS FILE to the path the FROZEN config declares
    # (dcs_ts_pr058_symmetry.py), rather than by amending the frozen field. The config is frozen;
    # the code is not, so the code moved.
    #
    # This check previously asserted `match is False` -- it encoded the CONFLICT as an invariant,
    # so resolving the conflict broke the test. A check that hardcodes the current defect state
    # fails exactly when the defect is fixed, which is the opposite of what a check is for. It now
    # asserts the GATE'S BEHAVIOUR: that it reports whether the two paths genuinely agree. The
    # refusal path (a real mismatch, unacknowledged) is covered separately by mutation M47.
    _ident = analyzer_identity_gate(pr, ack=True)
    _really_agree = (os.path.normpath(str(pr.require("artifacts", "analyzer")))
                     == os.path.normpath(os.path.relpath(os.path.abspath(__file__), REPO)))
    ck.add("identity_gate", "the analyzer's own path is checked against artifacts.analyzer, and "
           "the gate's verdict matches the filesystem either way",
           _ident["match"] is _really_agree, 1,
           "declared %r; match=%s (PR058-D1 resolved by rename)"
           % (pr.require("artifacts", "analyzer"), _ident["match"]))

    ck.report()
    print("\n[self-test] %d checks, %d failed" % (len(ck.rows), ck.n_fail))
    return 1 if ck.n_fail else 0


# ============================================================================================
# 14. MUTATION HARNESS
# ============================================================================================
def mutate(pr: Prereg) -> int:
    """Every refusal must be REACHABLE. An unreachable refusal is not a guard."""
    forb = forbidden_from_prereg(pr)
    bl = BaselineDistribution(cell="E", n_rows=4, n_domains=4, values=[0.1, 0.2, 0.3, 0.4],
                              scored_range=(-2.0, 2.0))
    good_delta = PairedDelta(cell="E", hypothesis="H1", baseline=bl,
                             per_domain={"a": 0.2, "b": 0.4}, stats={"observed_delta": 0.3})
    base = {("d%d" % i): [0.0] for i in range(10)}
    ko = {("d%d" % i): [0.55] for i in range(10)}
    hr = holm_with_absent(pr, {"H1": 0.001, "H2": 0.001, "H3": 0.9, "H4": 0.001})
    eq = equivalence_interval([0.01, -0.02, 0.0, 0.03], alpha(pr))
    succ_ok = evaluate_success(pr, {"observed_delta": 0.55}, {"observed_delta": -0.55},
                               {"equivalence": eq, "moved_beyond_control": False},
                               {"ok": True, "reproduces_h1": False}, hr)

    # Gates that RETURN a flag: the mutation must make that flag False.
    muts: "OrderedDict[str, Any]" = OrderedDict()
    muts["M1  dead hook (fired=0)"] = lambda: liveness_gate([_lr(hook_fired_count=0)], "m", pr)["live"]
    muts["M2  SDPA on the loaded config"] = lambda: liveness_gate(
        [_lr(attn_implementation="sdpa")], "m", pr)["live"]
    muts["M3  zero realised dose"] = lambda: liveness_gate(
        [_lr(surface_span_n_tokens=0)], "m", pr)["live"]
    muts["M4  decode edits leaked"] = lambda: liveness_gate([_lr(n_decode_edits=1)], "m", pr)["live"]
    muts["M5  realised != expected cells"] = lambda: liveness_gate(
        [_lr(n_cells_edited_realised=2)], "m", pr)["live"]
    muts["M6  no liveness records at all"] = lambda: liveness_gate([], "m", pr)["live"]
    muts["M7  bridge presented as a live arm"] = lambda: liveness_gate(
        [_lr(enabled=False, hook_fired_count=0, n_prefill_edits=0,
             n_cells_edited_realised=0, n_forward=3)], "m", pr)["live"]
    muts["M8  identical control-band hashes"] = lambda: control_band_gate(
        ["z"] * n_control_draws(pr), n_control_draws(pr))["ok"]
    muts["M9  control band with zero draws"] = lambda: control_band_gate([], n_control_draws(pr))["ok"]
    muts["M10 bridge does not reproduce"] = lambda: disabled_bridge_gate("aa", "bb", float(0))["ok"]
    muts["M11 bridge moves the hidden state"] = lambda: disabled_bridge_gate("aa", "aa", 1e-3)["ok"]
    muts["M12 non-zero delta at n_examples=0"] = lambda: null_arm_gate([0.3], 0)["ok"]
    muts["M13 absolute edit index reused"] = lambda: audit_end_relative(
        [_lr(seq_len=100, rel_end=-10, resolved_absolute_index=90),
         _lr(seq_len=137, rel_end=-10, resolved_absolute_index=90)])["ok"]
    muts["M14 unequal per-arm populations"] = lambda: assert_equal_populations(
        {"K1": ["a", "b"], "K2": ["a"]})["ok"]
    muts["M15 three of four conditions"] = lambda: evaluate_success(
        pr, {"observed_delta": 0.55}, {"observed_delta": -0.55},
        {"equivalence": eq, "moved_beyond_control": True},
        {"ok": True, "reproduces_h1": False}, hr)["success"]
    muts["M16 H1 with the wrong sign"] = lambda: evaluate_success(
        pr, {"observed_delta": -0.55}, {"observed_delta": -0.55},
        {"equivalence": eq, "moved_beyond_control": False},
        {"ok": True, "reproduces_h1": False}, hr)["success"]
    muts["M17 control reproduces H1"] = lambda: evaluate_success(
        pr, {"observed_delta": 0.55}, {"observed_delta": -0.55},
        {"equivalence": eq, "moved_beyond_control": False},
        {"ok": True, "reproduces_h1": True}, hr)["success"]
    muts["M18 disengaged channel not killed"] = lambda: not kill_condition_channel(
        pr, {"E": option_mass_gate_value(pr) / 2.0})["killed"]
    muts["M19 ceilinged baseline not caught"] = lambda: not ceiling_gate(
        BaselineDistribution(cell="E", n_rows=4, n_domains=4, values=[2.0] * 4,
                             scored_range=(-2.0, 2.0)), ceiling_quantile(pr))["at_ceiling"]
    muts["M20 copy account read as mechanism"] = lambda: copy_vs_mechanism(
        0.4, 0.3)["opposite_signs"]
    muts["M21 underpowered T3 proceeds"] = lambda: t3_power(
        pr, {("d%d" % i): (declared_mde(pr) * (1 if i % 2 else -1) * (i + 1))
             for i in range(30)})["power_ok"]
    muts["M22 K6 unevaluated read as passed"] = lambda: kill_condition_whole_query(None)["evaluated"]

    # Gates that RAISE.
    raisers: "OrderedDict[str, Any]" = OrderedDict()
    raisers["M23 row-level permutation attempt"] = lambda: domain_group_permutation(
        base, ko, pr, unit="row")
    raisers["M24 permutation over zero domains"] = lambda: domain_group_permutation({}, {}, pr)
    raisers["M25 zero-row population bind"] = lambda: bind_rows(pr, {}, "E", {})
    raisers["M26 bind on `condition` (A-039)"] = lambda: bind_rows(
        pr, _fake_bank(), "E", {"dom%d" % i: "train" for i in range(4)},
        selector_field=FORBIDDEN_SELECTOR_FIELD)
    raisers["M27 bind on an undeclared cell"] = lambda: bind_rows(
        pr, _fake_bank(), "A", {"dom%d" % i: "train" for i in range(4)})
    raisers["M28 threshold from a literal"] = lambda: assert_gate_from_prereg(
        "primary.alpha", alpha(pr) * 2.0, pr)
    raisers["M29 undeclared gate name"] = lambda: assert_gate_from_prereg(
        "primary.made_up_gate", 1.0, pr)
    raisers["M30 delta printed without its baseline"] = lambda: render_delta(
        PairedDelta(cell="E", hypothesis="H1", baseline=BaselineDistribution(
            cell="E", n_rows=4, n_domains=4, values=[0.1, 0.2]),
            per_domain={"a": 0.1}, stats={}), p_floor(pr), fh=open(os.devnull, "w"))
    raisers["M31 delta constructed with no baseline"] = lambda: PairedDelta(
        cell="E", hypothesis="H1", baseline=None, per_domain={"a": 0.1})
    raisers["M32 baseline over zero values"] = lambda: BaselineDistribution(
        cell="E", n_rows=0, n_domains=0, values=[])
    raisers["M33 verdict on unclean liveness"] = lambda: verdict(
        pr, succ_ok, False, [], True, True, forb)
    raisers["M34 verdict when NEITHER arm moved"] = lambda: verdict(
        pr, succ_ok, True, [], False, False, forb)
    raisers["M35 outcome at the concept-token site"] = lambda: read_site_gate(
        [_lr(read_position=refused_read_position(pr))], pr)
    raisers["M36 outcome at an unpreregistered site"] = lambda: read_site_gate(
        [_lr(read_position="last")], pr)
    raisers["M37 installation as a post-hoc exclusion"] = lambda: \
        refuse_installation_as_exclusion(["dom0"])
    raisers["M38 a domain with no stratum dropped"] = lambda: stratify_by_installation(
        {"a": 1.0, "b": 2.0}, {"a": 1.0}, installation_cut(pr))
    raisers["M39 forbidden mandate-33 wording"] = lambda: assert_sayable(
        "the demonstration->query pathway was removed", forb)
    raisers["M40 Holm over an empty family"] = lambda: holm({}, alpha(pr))
    raisers["M41 p-value for a non-member"] = lambda: holm_with_absent(pr, {"H9": 0.01})
    raisers["M42 equivalence over n<2"] = lambda: equivalence_interval([0.1], alpha(pr))
    raisers["M43 T3 over <2 validation domains"] = lambda: t3_power(pr, {"d0": 0.1})
    raisers["M44 T3 with a zero measured SD"] = lambda: t3_power(
        pr, {("d%d" % i): 0.1 for i in range(10)})
    raisers["M45 option_mass never measured"] = lambda: kill_condition_channel(pr, {})
    raisers["M46 ceiling rule with no scored range"] = lambda: ceiling_gate(
        BaselineDistribution(cell="E", n_rows=2, n_domains=2, values=[0.1, 0.2]),
        ceiling_quantile(pr))
    # M47 must INJECT the mismatch rather than rely on one existing. Until PR058-D1 was resolved
    # (2026-09-07, by renaming this file to the path the frozen config declares) this mutation fired
    # simply because the paths genuinely disagreed -- so fixing the defect made the mutation
    # UNREACHABLE and it silently went GREEN. An unreachable refusal is not a guard. It now mutates
    # a COPY of the preregistration so the conflict is manufactured on demand and the refusal path
    # stays exercised no matter what this file is called.
    def _m47():
        import copy as _copy
        _bad = _copy.deepcopy(pr.obj)
        _bad["artifacts"]["analyzer"] = "scripts/a_path_this_analyzer_certainly_is_not.py"
        return analyzer_identity_gate(Prereg(_bad, pr.path + "#M47"))
    raisers["M47 analyzer path conflict unacknowledged"] = _m47
    raisers["M48 equal-population check over one arm"] = lambda: assert_equal_populations(
        {"K1": ["a"]})
    raisers["M49 exclusion with no whole_population flag"] = lambda: whole_population_exclusions(
        _PrereqStub(pr, [{"domain": "x", "reason": "prose only"}]))
    raisers["M50 an analyzer source with a gate literal"] = lambda: _audit_or_raise(pr)
    raisers["M51 two banks pooled into one p-value"] = lambda: refuse_pooling_across_banks(
        primary_banks(pr))
    raisers["M52 a descriptive arm quoted as mechanism"] = lambda: \
        refuse_descriptive_as_confirmatory(pr, descriptive_banks(pr)[0])

    print("=== %s mutation harness: every refusal must be REACHABLE ===" % PR_ID)
    _REFUSALS = (Refusal, ZeroBinding, PreregError, CannotAnswer)
    n_red = 0
    for name, fn in muts.items():
        try:
            passed = bool(fn())
        except _REFUSALS as e:
            n_red += 1
            print("  RED    %-42s -> refusal: %s" % (name, str(e)[:64].replace("\n", " ")))
            continue
        red = not passed
        n_red += red
        print("  %s  %-42s -> gate says ok=%s%s"
              % ("RED  " if red else "GREEN", name, passed,
                 "" if red else "   <-- THIS REFUSAL IS UNREACHABLE"))
    for name, fn in raisers.items():
        try:
            fn()
            print("  GREEN  %-42s -> NO REFUSAL RAISED   <-- UNREACHABLE" % name)
        except _REFUSALS as e:
            n_red += 1
            print("  RED    %-42s -> refusal: %s" % (name, str(e)[:64].replace("\n", " ")))
    total = len(muts) + len(raisers)
    print("[mutate] %d/%d mutations produced a refusal" % (n_red, total))
    if n_red != total:
        print("  AN UNREACHABLE REFUSAL IS NOT A GUARD.", file=sys.stderr)
        return 1
    return 0


class _PrereqStub(object):
    """A Prereg whose exclusion list has been corrupted, for M49. Nothing else changes."""

    def __init__(self, pr: Prereg, exclusions):
        self._pr = pr
        self._ex = exclusions

    def require(self, *keys):
        if keys == ("population", "preregistered_exclusions"):
            return self._ex
        return self._pr.require(*keys)


def _audit_or_raise(pr: Prereg):
    """M50: an analyzer source carrying a declared gate value as a numeric literal must refuse."""
    import tempfile
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
        f.write("ALPHA = %r  # a hand-typed gate\n" % alpha(pr))
        tmp = f.name
    try:
        res = source_gate_literal_audit(pr, source_path=tmp)
        if not res["ok"]:
            raise Refusal("the analyzer source carries %d declared gate value(s) as numeric "
                          "literal(s): %s" % (res["n_violations"], res["violations"]))
        return res
    finally:
        os.unlink(tmp)


# ============================================================================================
# 15. THE ANALYSIS
# ============================================================================================
def analyse(pr: Prereg, runs_root: str, ack_path_conflict: bool) -> int:
    forb = forbidden_from_prereg(pr)
    check_wording_pin(pr)
    ident = analyzer_identity_gate(pr, ack=ack_path_conflict)
    ck = Checks()

    print("=== %s PHASE 10 analysis ===" % PR_ID)
    print("  analyzer identity: declared=%r actual=%r match=%s acknowledged=%s"
          % (ident["declared"], ident["actual"], ident["match"], ident["acknowledged"]))
    print("  loader state: %s" % json.dumps(analyzer_exists_flag(pr)))
    aud = source_gate_literal_audit(pr)
    ck.add("no_gate_literals", "no declared gate value appears as a numeric literal in this "
           "analyzer", aud["ok"], aud["n_gates_checked"], str(aud["violations"])[:120])

    outstanding = [i["id"] for i in pr.require("pre_extraction_checklist")
                   if i.get("blocking") and not i.get("done")]

    if not os.path.isdir(os.path.join(REPO, runs_root)) and not os.path.isdir(runs_root):
        raise Refusal(
            "no run root at %r. NO cell-B or cell-E row has ever been scored by any run, on any "
            "channel (checklist T2), so there is nothing to analyse. An analysis over zero arms "
            "would be a statistic over a set it bound zero rows from (C-074).\n"
            "  Blocking checklist items outstanding: %s" % (runs_root, ", ".join(outstanding)))

    root = runs_root if os.path.isdir(runs_root) else os.path.join(REPO, runs_root)
    assign = load_split(pr)
    arms = build_arm_manifest(pr)

    found, absent = OrderedDict(), []
    for arm in arms:
        try:
            d = _find_run(root, arm.tag())
        except PreregError:
            absent.append(arm.arm_id)
            continue
        found[arm.arm_id] = d

    if not found:
        raise Refusal(
            "NO %s arm has produced a COMPLETE run under %r (%d arm tags searched, %d absent).\n"
            "  Refusing to print an empty result: cells B and E have never been scored on any "
            "channel by any run, so every number this analyzer could print would be over a set it "
            "bound zero rows from (C-074).\n"
            "  Blocking checklist items outstanding: %s"
            % (PR_ID, root, len(arms), len(absent), ", ".join(outstanding)))

    ck.add("arms_present", "every declared arm has a COMPLETE run directory", not absent,
           len(arms), "absent=%s" % absent[:6])
    ck.add("split_bound", "the split manifest assigns every analysed domain", bool(assign),
           len(assign))

    # The population is bound HERE, on `cell`, from the pinned banks -- so a zero-row or
    # zero-domain bind refuses before any outcome is read (A-039 / C-074).
    for bank_key in sorted({a.bank for a in arms}):
        bank_path = os.path.join(REPO, pr.require("population", "banks", bank_key, "path"))
        rows = load_bank_rows(bank_path)
        for cell in cell_specs(pr):
            b = bind_rows(pr, rows, cell, assign)
            ck.add("bind_%s_%s" % (bank_key, cell),
                   "cell %s binds on the `cell` field after the %d whole-population exclusions"
                   % (cell, len(b["excluded_domains"])), True, b["n_rows"],
                   "n_domains=%d by_split=%s" % (b["n_domains"], b["by_split"]))

    for arm_id, d in found.items():
        ck.add("arm_manifest_echo_%s" % arm_id,
               "the run echoed %s -- what it BELIEVED it was doing" % CONTRACT_ARM,
               os.path.exists(os.path.join(d, CONTRACT_ARM)), 1, d)

    # Liveness BEFORE any outcome, so a number for an arm whose hook did not fire never exists.
    all_clean = True
    for arm in arms:
        d = found.get(arm.arm_id)
        if d is None:
            continue
        lp = os.path.join(d, CONTRACT_LIVENESS)
        recs = []
        if os.path.exists(lp):
            with open(lp) as f:
                recs = [json.loads(x) for x in f if x.strip()]
        lg = liveness_gate(recs, arm.arm_id, pr, expect_enabled=arm.expect_enabled)
        all_clean = all_clean and lg["live"]
        ck.add("liveness_%s" % arm.arm_id, "the hook demonstrably fired at the declared scope, "
               "under eager attention, with no decode leak", lg["live"], lg["n_rows"],
               "; ".join(lg["reasons"])[:160])
        if recs:
            a = audit_end_relative(recs)
            ck.add("index_%s" % arm.arm_id, "every index is len(input_ids)+rel_end (P-N7)",
                   a["ok"], a["n_records"], a["witness_note"])
            read_site_gate(recs, pr)

    ck.report()
    print("\n[%s] %d/%d arm(s) loaded, %d check failure(s)" % (PR_ID, len(found), len(arms),
                                                              ck.n_fail))
    if ck.n_fail or not all_clean:
        print(assert_sayable(
            "REFUSING to emit any verdict: %d gate(s) failed above. A null behind an unverified "
            "hook is VOID, not a negative, and the mandatory wording of the declared negative is "
            "not available to an arm that has not passed liveness." % ck.n_fail, forb),
            file=sys.stderr)
        return 1
    print("  (baseline distributions, then deltas, then Holm, then the verdict -- in that order; "
          "no delta is rendered before its baseline)")
    return 0


# ============================================================================================
# 16. MAIN
# ============================================================================================
def main() -> int:
    ap = argparse.ArgumentParser(description="DCS-PR-058 PHASE 10 analyzer",
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--prereg", default=PREREG_DEFAULT)
    ap.add_argument("--runs", default="outputs/boombness/score_behavior")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--mutate", action="store_true")
    ap.add_argument("--plan", action="store_true")
    ap.add_argument("--power-t3", action="store_true")
    ap.add_argument("--validation-deltas", default=None,
                    help="JSON {domain: paired_delta} measured on VALIDATION DOMAINS ONLY (T3)")
    ap.add_argument("--ack-analyzer-path-conflict", action="store_true",
                    help="acknowledge PR058-D1: this file's path differs from artifacts.analyzer")
    a = ap.parse_args()

    try:
        pr = load(a.prereg, for_extraction=False)
    except PreregError as e:
        print("REFUSED: %s" % e, file=sys.stderr)
        return 1

    try:
        if a.self_test:
            return selftest(pr)
        if a.mutate:
            return mutate(pr)
        if a.plan:
            return plan(pr)
        if a.power_t3:
            if not a.validation_deltas:
                raise Refusal("--power-t3 needs --validation-deltas: T3 MEASURES the between-domain "
                              "SD on validation domains and the frozen file deliberately carries "
                              "no value for it")
            with open(a.validation_deltas) as f:
                d = json.load(f)
            res = t3_power(pr, {str(k): float(v) for k, v in d.items()})
            print(json.dumps(res, indent=2))
            return 0 if res["power_ok"] else 2
        return analyse(pr, a.runs, a.ack_analyzer_path_conflict)
    except (Refusal, ZeroBinding, CannotAnswer, PreregError) as e:
        print("REFUSED: %s" % e, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
