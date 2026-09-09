#!/usr/bin/env python3
"""`DCS-PR-059` -- PHASE 11, the query-position SCOPE FAMILY on the CONCEPT-FREE channel.

WHAT GOVERNS
------------
`configs/dcs_ts_pr059_phase11.json`, status FROZEN, loaded through `scripts/dcs_ts_prereg.py`.
There is not one numeric gate literal in this file. alpha, `n_perm`, the attainable p-floor, the
`option_mass` engagement gate, the power bar, the half-of-`S_G` reproduction rule, the resolver
failure tolerance, the installation stratification cut, the declared minimum meaningful effect,
the control-draw counts, the seeds, the read layer, the intervention band, the multiplicity family
and the mandatory negative wording are all fetched through `Prereg.require()` or PARSED out of the
frozen file's own prose. `--self-test` re-reads THIS FILE'S OWN SOURCE (`source_gate_literal_audit`)
and fails if any declared gate value appears in it as a numeric literal, so the claim in this
docstring is checked rather than asserted. That idea is `PR-058`'s and is reused verbatim.

WHAT PHASE 11 IS
----------------
Mandate section 14. It REDOES the surgical query-position experiment WITHOUT the instrument
leakage that made the old K-ladder's K=7 step uninterpretable. Two defects are designed out:

  (1) CHANNEL. The old ladder ran on `semantic_forced_choice`, whose own question NAMES the
      concept -- "...does the word button refer to a button or to a bomb?". `R-116` measured that
      on our own data: the concept word appears in `full_prompt` on 100.0% of forced-choice rows
      and 0.0% of `semantic_one_word` rows, and the SAME ROWS scored through the display channel
      take knife from 0.000 to 0.628 installing domains. The channel, not the model, decided the
      answer. So the PRIMARY channel here is `semantic_one_word` and the display channel is
      FORBIDDEN as a primary -- `refuse_display_channel_as_primary()` and
      `refuse_display_fallback()` are code paths, and a disengaged primary channel is CANNOT
      ANSWER, never a licence to fall back.
  (2) UNMAPPED ROWS. Mandate section 12.3: map every token FIRST, then define semantic regions.
      No K is swept here. Every scope is a DECLARED SET OF `rel_end` OFFSETS read off the frozen
      token-role map, and `--verify-token-map` (checklist U4) re-derives each scope's realised
      roles from `outputs/dcs_ts/token_roles_ts116m.json.gz` rather than trusting the design.

THE RISK THIS FILE IS STRUCTURED AROUND
---------------------------------------
`primary._largest_risk`: the concept-free channel is only WEAKLY ENGAGED. Median `option_mass` is
0.1138 -- the two scored options carry about a ninth of the next-token mass and the model's actual
preferred word is a THIRD word roughly 89% of the time. `semantic_logodds` is therefore an
ORDERING INSIDE A RESIDUAL, and a knockout can move that ordering while the output word never
changes. The frozen file declares three mitigations and all three are STRUCTURAL here:

  (1) `ArmReadout` (the argmax answer distribution and the full `option_mass` distribution) is a
      required constructor argument of `ScopeDelta`, and `render_delta()` REFUSES to emit a delta
      whose readout has not been rendered first. A delta cannot reach a reader ahead of the
      distribution that says how engaged the channel was when it was measured.
  (2) the argmax-switch rate is computed and reported as a CORROBORANT and is explicitly not one
      of the conjunctive success conditions (mandate 10.5 says "ideally").
  (3) `engagement_gate()` returns CANNOT ANSWER for any arm whose median `option_mass` falls below
      the declared gate.

ENTRY POINTS
------------
  --plan               the arm manifest and its launch commands. CPU, deterministic, reads no
                       outcome.
  --verify-token-map   checklist U4: every declared scope's `rel_end` set re-resolved against the
                       FROZEN token-role artifact, in all of its prompts, with counts.
  --selector-demo      checklist U1: the declared-offset selector, end-relative in every prompt
                       separately, with the realised absolute positions and decoded tokens.
  --control-draws      checklist U2: the per-scope dose-matched random-row draws, seeded,
                       reproducible, and RECORDED.
  --u3-inventory       checklist U3: what concept-free-channel knockout rows exist, and exactly
                       what is missing for the SD measurement the frozen file leaves null.
  --power-u3           U3 as a code path: measure the between-domain SD on VALIDATION domains only
                       and return CANNOT ANSWER WITHOUT READING TEST below the power bar.
  --self-test          CPU unit tests on synthetic data for every testable piece.
  --mutate             checklist U6: a dead hook, an SDPA arm, a realised row set differing from
                       the declared one, an identical-hash control band, a row-level p-value, a
                       scope reported without its dose-matched control, a dropped family member,
                       a display-channel number used as a mechanism result, an absolute index and
                       the rest must EACH produce a refusal.
  (default)            the analysis. It REFUSES when no arm has run, rather than printing an
                       empty result.

USAGE
    python3 scripts/dcs_ts_pr059_localisation.py --self-test
    python3 scripts/dcs_ts_pr059_localisation.py --mutate
    python3 scripts/dcs_ts_pr059_localisation.py --verify-token-map
    python3 scripts/dcs_ts_pr059_localisation.py --plan

ANALYZER IDENTITY
-----------------
`artifacts.analyzer` names `scripts/dcs_ts_pr059_localisation.py` and THIS FILE IS THAT PATH. On
`PR-058` the analyzer was first written under a different name and the mismatch became blocking
defect `PR058-D1`, resolved only by renaming the code afterwards. `analyzer_identity_gate()` is
kept anyway and mutation M40 injects a mismatch on a COPY of the preregistration, so the refusal
stays REACHABLE even though the conflict does not exist.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
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

PREREG_DEFAULT = "configs/dcs_ts_pr059_phase11.json"
PR_ID = "DCS-PR-059"
FAMILY_NAME = "PHASE11_LOCALISATION"
TOKEN_MAP_DEFAULT = "outputs/dcs_ts/token_roles_ts116m.json.gz"

#: Artifacts the GPU runner must write for this analyzer to have anything to refuse on.
CONTRACT_ARM = "PR059_ARM.json"
CONTRACT_LIVENESS = "PR059_LIVENESS.jsonl"


class Refusal(RuntimeError):
    """Raised instead of returning a number that should not exist."""


class CannotAnswer(RuntimeError):
    """The design cannot resolve the question. NOT a null, and never printed as one."""


#: The literal wording of the negative, pinned here and checked against the frozen file.
MANDATORY_NEGATIVE_WORDING = (
    "THE DEMONSTRATION->QUERY PATHWAY IS DISTRIBUTED ACROSS THE QUERY RATHER THAN LOCALISED TO "
    "ANY PREDECLARED SEMANTIC REGION, UNDER THIS INTERVENTION, AT THIS BAND, ON THIS BANK"
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
    want = " ".join(str(pr.require("primary", "negative", "MANDATORY_WORDING")).split()).strip()
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
    if abs(declared - derived) > 1e-8:
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


def random_row_seed(pr: Prereg) -> int:
    return int(pr.require("seeds", "random_row_draws"))


def n_random_row_draws(pr: Prereg) -> int:
    return int(pr.require("seeds", "n_random_row_draws"))


def n_nondemo_draws(pr: Prereg) -> int:
    return int(pr.require("seeds", "n_nondemo_draws"))


def installation_cut(pr: Prereg) -> float:
    """`installation.threshold_declared_here`. A STRATIFIER, never a gate, never an exclusion."""
    return float(pr.require("installation", "threshold_declared_here"))


def declared_mde(pr: Prereg) -> float:
    return float(pr.require("power", "declared_minimum_meaningful_effect",
                            "semantic_logodds_shift"))


def half_of_reference_rule(pr: Prereg) -> float:
    """`primary.success.half_of_S_G_rule` -- PR-032's own reproduction rule, inherited VERBATIM.

    `_where_the_0_5_comes_from`: inheriting a threshold from the design being replaced is the one
    way to be sure it was not picked to fit this phase's numbers. It is read from the frozen file,
    never re-typed here.
    """
    v = float(pr.require("primary", "success", "half_of_S_G_rule"))
    if not (float(0) < v <= float(1)):
        raise Refusal("primary.success.half_of_S_G_rule is %r, which is not a fraction" % v)
    return v


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

    It is stated three times -- `outcome_variables.O1_semantic_readout.cannot_answer_if`,
    `primary.cannot_answer` and `kill_condition` -- as "below the 0.0X gate". It is not carried in
    a numeric field, so it is parsed rather than re-typed; a re-typed copy is a second source of
    truth and the two can then disagree without either being wrong on its own.
    """
    texts = [pr.require("outcome_variables", "O1_semantic_readout", "cannot_answer_if"),
             pr.require("primary", "cannot_answer"),
             pr.require("kill_condition")]
    return _parse_first([r"below\s+the\s+(0?\.\d+)\s+gate",
                         r"option_mass\s+below\s+the\s+(0?\.\d+)"],
                        texts, "option_mass gate")


def power_bar(pr: Prereg) -> float:
    """The power bar, parsed out of checklist U3 / `primary.cannot_answer` / `power.*`."""
    texts = [str(i.get("item", "")) for i in pr.require("pre_extraction_checklist")
             if i.get("id") == "U3"]
    texts.append(str(pr.require("primary", "cannot_answer")))
    texts.append(str(pr.require("power", "underpowered_branch")))
    texts.append(str(pr.require("power", "design")))
    texts.append(str(pr.require("primary", "negative", "condition")))
    return _parse_first([r"power\s*<\s*(0?\.\d+)",
                         r"power\s*>=\s*(0?\.\d+)",
                         r"power\s+(?:is\s+)?below\s+(0?\.\d+)",
                         r"target\s+power\s+(0?\.\d+)"], texts, "power bar")


def resolver_failure_tolerance(pr: Prereg) -> float:
    """`primary.cannot_answer` (c): "a scope's row-set resolver fails on more than N% of rows, so
    the arms no longer share a population". Parsed, never re-typed."""
    texts = [str(pr.require("primary", "cannot_answer"))]
    return _parse_first([r"resolver\s+fails\s+on\s+more\s+than\s+(\d+(?:\.\d+)?)\s*%"],
                        texts, "row-set resolver failure tolerance") / float(100)


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


def secondary_read_position(pr: Prereg) -> str:
    """`read_site.position_SECONDARY_REPRESENTATION` -- `following`, rel_end -9. O2 only.

    The PRIMARY read site of this phase is THE OUTPUT: a whole-answer teacher-forced score after
    the full prefill, downstream of every layer and every intervened row BY CONSTRUCTION. That is
    why the mandate-12.1 "a state read at the first affected layer may only reflect the read row's
    own mask" artifact cannot touch the primary at all.
    """
    p = str(pr.require("read_site", "position_SECONDARY_REPRESENTATION")).strip()
    if not re.fullmatch(r"[a-z_]+", p):
        raise Refusal("read_site.position_SECONDARY_REPRESENTATION is not a bare position name: "
                      "%r" % p)
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
    """`intervention.attn_impl` -- eager, FORCED. Under SDPA the additive mask edit is DISCARDED
    and the knockout is a silent no-op that scores as a CLEAN NULL (C-047)."""
    txt = str(pr.require("intervention", "attn_impl"))
    tok = txt.split()[0].strip().strip("-").strip()
    if not re.fullmatch(r"[a-z_]+", tok):
        raise Refusal("intervention.attn_impl does not begin with a bare implementation name: %r"
                      % txt)
    return tok


def primary_channel(pr: Prereg) -> str:
    return str(pr.require("population", "query_kind_primary")).strip()


def display_channel(pr: Prereg) -> str:
    return str(pr.require("population", "query_kind_display")).strip()


def primary_cell(pr: Prereg) -> str:
    c = str(pr.require("population", "cell")).strip()
    if not re.fullmatch(r"[A-Z]", c):
        raise Refusal("population.cell is not a single cell letter: %r" % c)
    return c


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
        "resolver failure tolerance": resolver_failure_tolerance(pr),
        "primary.success.half_of_S_G_rule": half_of_reference_rule(pr),
        "installation.threshold_declared_here": installation_cut(pr),
        "power.declared_minimum_meaningful_effect": declared_mde(pr),
        "seeds.permutation": float(permutation_seed(pr)),
        "seeds.random_row_draws": float(random_row_seed(pr)),
        "seeds.extraction": float(pr.require("seeds", "extraction")),
    }


def source_gate_literal_audit(pr: Prereg, source_path: Optional[str] = None) -> Dict[str, Any]:
    """Does this analyzer's own source contain any DECLARED GATE VALUE as a numeric literal?

    "Every threshold via Prereg.require()" is a property of the file, so it is checked against the
    file. Without this the claim is a docstring, and a docstring is not a guard. The idea is
    `PR-058`'s `source_gate_literal_audit()`, reused rather than reinvented.
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
# 3. ANALYZER IDENTITY -- the PR058-D1 defect, designed out rather than repeated
# ============================================================================================
def analyzer_identity_gate(pr: Prereg, ack: bool = False) -> Dict[str, Any]:
    """`artifacts.analyzer` must name THIS FILE.

    On PR-058 the analyzer was written under a different name and the mismatch became blocking
    defect PR058-D1, resolved only by renaming the code afterwards. This file was written AT the
    declared path from the start, so the gate passes -- but it is kept, and mutation M40 injects a
    mismatch on a COPY of the preregistration, because a refusal that cannot fire is not a guard.
    """
    declared = str(pr.require("artifacts", "analyzer")).strip()
    mine = os.path.relpath(os.path.abspath(__file__), REPO)
    match = (os.path.normpath(declared) == os.path.normpath(mine))
    out = {"declared": declared, "actual": mine, "match": match, "acknowledged": bool(ack)}
    if not match and not ack:
        raise Refusal(
            "CONFLICT WITH THE FROZEN PREREGISTRATION: artifacts.analyzer names %r but this "
            "analyzer is %r. The config is FROZEN and is NOT edited to match. This is the PR058-D1 "
            "defect; re-run with --ack-analyzer-path-conflict only to record it, never to hide it."
            % (declared, mine))
    return out


def analyzer_exists_flag(pr: Prereg) -> Dict[str, Any]:
    """`artifacts.analyzer_exists` is the flag the loader refuses extraction on. This analyzer
    cannot flip it (the file is frozen and this session may not edit it), so it REPORTS the
    disagreement between the flag and the filesystem rather than papering over it."""
    flag = bool(pr.require("artifacts", "analyzer_exists"))
    declared = os.path.join(REPO, str(pr.require("artifacts", "analyzer")))
    return {"analyzer_exists_flag": flag,
            "declared_path_on_disk": os.path.exists(declared),
            "note": "the loader still REFUSES --for-extraction while the flag is false and while "
                    "any BLOCKING checklist item is not done; flipping either is the config "
                    "owner's edit, not the analyzer's"}


# ============================================================================================
# 4. THE SCOPE FAMILY -- rel_end SETS read off the frozen token-role map, never a K
# ============================================================================================
_RANGE_RE = re.compile(r"\[\s*(-\d+)\s*\.\.\s*(-\d+)\s*\]")
_SINGLE_RE = re.compile(r"\[\s*(-\d+)\s*\]")


def parse_rel_end_spec(spec: Any) -> List[int]:
    """A scope's `rel_end_rows`, as a sorted list of END-RELATIVE offsets.

    The frozen file carries three forms: an explicit list (`[-5,-4,-3,-2,-1]`), a range string
    (`"[-28..-6]"`) and a difference (`"[-28..-6] minus [-10]"`). All three are parsed here so the
    analyzer's notion of a scope is the file's, and an offset that is not negative is a REFUSAL:
    an absolute index reads a DIFFERENT TOKEN in each arm, and this repository's own measurement
    says the absolute codeword index is identical across the three concepts in 0/2300 triples
    while the end-relative index is identical in 2300/2300.
    """
    if isinstance(spec, (list, tuple)):
        rows = [int(x) for x in spec]
    else:
        txt = str(spec)
        parts = re.split(r"\bminus\b", txt, flags=re.IGNORECASE)
        if not parts or not parts[0].strip():
            raise Refusal("rel_end spec %r has no base term" % spec)

        def _group(t: str) -> List[int]:
            got: List[int] = []
            for m in _RANGE_RE.finditer(t):
                lo, hi = int(m.group(1)), int(m.group(2))
                if lo > hi:
                    lo, hi = hi, lo
                got.extend(range(lo, hi + 1))
            for m in _SINGLE_RE.finditer(t):
                got.append(int(m.group(1)))
            return got

        base = _group(parts[0])
        if not base:
            raise Refusal("rel_end spec %r declares no offsets; refusing to guess a row set"
                          % spec)
        drop = set()
        for p in parts[1:]:
            drop.update(_group(p))
        rows = [r for r in base if r not in drop]
    bad = [r for r in rows if r >= 0]
    if bad:
        raise Refusal(
            "rel_end spec %r contains NON-NEGATIVE offset(s) %s. Positions in this phase are "
            "ALWAYS len(input_ids)+rel_end and NEVER a constant absolute integer. An absolute "
            "index reads a different token in each arm; that is this repository's recorded "
            "absolute-position-index bug class, hit twice." % (spec, sorted(bad)))
    if len(set(rows)) != len(rows):
        raise Refusal("rel_end spec %r repeats an offset; a row cannot be cut twice" % spec)
    return sorted(rows)


def declared_scopes(pr: Prereg) -> "OrderedDict[str, Dict[str, Any]]":
    """Every scope in `scopes.family`, with its rel_end set RE-DERIVED and cross-checked.

    A scope whose parsed row count disagrees with its declared `n_rows` is a refusal: the two are
    two statements of the same thing in the frozen file, and where they disagree neither is
    trustworthy.
    """
    out: "OrderedDict[str, Dict[str, Any]]" = OrderedDict()
    fam = pr.require("scopes", "family")
    if not fam:
        raise Refusal("scopes.family is empty -- the analyzer would localise nothing")
    for s in fam:
        sid = str(s["id"])
        rows = parse_rel_end_spec(s.get("rel_end_rows", []))
        n_declared = int(s.get("n_rows", len(rows)))
        if len(rows) != n_declared:
            raise Refusal(
                "scope %s declares n_rows=%d but its rel_end_rows resolve to %d offset(s) %s. The "
                "two are the same statement made twice in the frozen file; a disagreement means "
                "neither can be trusted as the scope definition." % (sid, n_declared, len(rows),
                                                                     rows))
        out[sid] = {"id": sid, "rel_end_rows": rows, "n_rows": len(rows),
                    "status": str(s.get("status", "")),
                    "mandate_label": str(s.get("mandate_label", "")),
                    "implementation": str(s.get("implementation", "")),
                    "unconstructible": "UNCONSTRUCTIBLE" in str(s.get("status", "")).upper()}
    return out


def query_span_rel_end(pr: Prereg) -> List[int]:
    """The whole query span, as rel_end offsets, taken from the frozen token-role LAYOUT.

    Not hardcoded and not inferred from a K: `token_map.rel_end_layout` is the map this phase's
    scopes are read off, so the span is read off the same object.
    """
    rows: List[int] = []
    for key in pr.require("token_map", "rel_end_layout"):
        rows.extend(parse_rel_end_spec("[%s]" % str(key).replace("..", "..")))
    if not rows:
        raise Refusal("token_map.rel_end_layout declares no offsets")
    return sorted(set(rows))


def layout_roles(pr: Prereg) -> Dict[int, str]:
    """rel_end -> ROLE NAME, parsed out of `token_map.rel_end_layout`.

    This is the design's OWN claim about what each row is. `--verify-token-map` checks it against
    the frozen artifact rather than assuming it.
    """
    out: Dict[int, str] = {}
    for key, val in pr.require("token_map", "rel_end_layout").items():
        offs = parse_rel_end_spec("[%s]" % str(key))
        role = str(val).split()[0].strip().strip("'\"").lower()
        role = re.sub(r"[^a-z_]", "", role)
        if not role:
            raise Refusal("token_map.rel_end_layout[%r] names no role" % key)
        for o in offs:
            if o in out:
                raise Refusal("token_map.rel_end_layout assigns rel_end %d twice" % o)
            out[o] = role
    return out


def family_member_ids(pr: Prereg) -> List[str]:
    """S_A..S_F, in declaration order, parsed out of the multiplicity family's member strings."""
    for fam in pr.require("multiplicity", "families"):
        if fam.get("name") == FAMILY_NAME:
            mem = list(fam["members"])
            if not mem:
                raise Refusal("multiplicity family %r declares no members" % FAMILY_NAME)
            out = []
            for m in mem:
                mm = re.search(r"\b(S_[A-Z]\d?)\b", str(m))
                if not mm:
                    raise Refusal("family member %r does not name a scope id" % m)
                out.append(mm.group(1))
            return out
    raise Refusal("multiplicity family %r is not declared in the preregistration" % FAMILY_NAME)


def reference_scope_id(pr: Prereg) -> str:
    """The DENOMINATOR scope -- the one every narrower effect is reported as a fraction of, and
    the one the first kill condition reads. It is identified from the frozen file's own text, not
    chosen here."""
    txt = str(pr.require("kill_condition"))
    m = re.search(r"\b(S_[A-Z])\b", txt)
    if not m:
        raise Refusal("kill_condition names no reference scope")
    sid = m.group(1)
    if sid in family_member_ids(pr):
        raise Refusal(
            "the reference scope %s is also a member of family %r. `_S_G_is_not_a_member`: the "
            "denominator and the kill-condition read is not a hypothesis about localisation and "
            "must not be Holm-corrected inside the family it normalises." % (sid, FAMILY_NAME))
    return sid


def scaffold_scope_id(pr: Prereg) -> str:
    """The scaffold-only scope whose NULL is required for anything else to mean something."""
    for sid, s in declared_scopes(pr).items():
        if "scaffold" in s["mandate_label"].lower() and sid in family_member_ids(pr):
            return sid
    raise Refusal("no family member is declared as the chat-scaffold-only scope; the "
                  "scaffold-null precondition cannot be evaluated")


# ============================================================================================
# 5. U1 -- THE DECLARED-OFFSET ROW SELECTOR (rel_end set -> `surface_span`)
# ============================================================================================
#: WHERE THIS LIVES AND WHY. `artifacts._WHAT_DOES_NOT_EXIST_YET` puts the PRODUCER half of U1 in
#: `src/boombness/score_behavior.py` (two call sites that must agree by construction) and in
#: `scripts/dcs_extract_under_ko.py`. Those files are owned by a concurrent writer in this shared
#: tree and are NOT edited from here. What lives here is the DEFINITION -- one function, so the
#: pre-flight pass, the per-row resolution and the extractor can each call the same one instead of
#: restating it -- together with the audit that checks the PERSISTED row set against the declared
#: one on every row. The row set travels through the existing `surface_span` channel:
#: `pair_common.resolve_scoped_query_rows` takes it verbatim from the consumer for
#: `query_last_k_rows` and `target_surface_row_only`, so no hook, no liveness contract and no
#: artifact format changes.
def surface_span_from_rel_end(rel_end_rows: Sequence[int], seq_len: int,
                              query_span_positions: Optional[Sequence[int]] = None
                              ) -> List[int]:
    """Turn a scope's DECLARED rel_end set into absolute `surface_span` positions for ONE prompt.

    END-RELATIVE IN EVERY PROMPT SEPARATELY. `len(input_ids)` is this prompt's own length, so the
    same declared scope resolves to a different absolute set in a longer prompt -- which is the
    entire point. A non-negative offset, an offset that falls outside the sequence, or a resolved
    position outside the prompt's own query span is a REFUSAL rather than a silently wrong cut.
    """
    if seq_len <= 0:
        raise ZeroBinding("the declared-offset selector was given seq_len=%d; it binds nothing"
                          % seq_len)
    rows = list(rel_end_rows)
    if not rows:
        raise ZeroBinding(
            "the declared-offset selector was given an EMPTY rel_end set. An empty scope cuts "
            "nothing and its arm would score as a clean null; it is refused here so it cannot "
            "reach a reader as a measurement (this is scope S_B's shape, and S_B is declared "
            "UNCONSTRUCTIBLE rather than run as an empty arm).")
    bad = [r for r in rows if r >= 0]
    if bad:
        raise Refusal(
            "ABSOLUTE INDEX REFUSED: offsets %s are not negative. Every edit and read index in "
            "this phase is len(input_ids)+rel_end. The full list of ABSOLUTE codeword indices is "
            "identical across the three concepts in 0/2300 triples while the END-RELATIVE index "
            "is identical in 2300/2300, so an absolute index reads a DIFFERENT TOKEN in each arm."
            % sorted(bad))
    out = []
    for r in rows:
        pos = seq_len + int(r)
        if pos < 0 or pos >= seq_len:
            raise Refusal("rel_end %d resolves to position %d outside a sequence of length %d"
                          % (r, pos, seq_len))
        out.append(pos)
    if query_span_positions is not None:
        qs = set(int(x) for x in query_span_positions)
        if not qs:
            raise ZeroBinding("the prompt's query span is EMPTY, so no scope can be constrained "
                              "to it")
        outside = sorted(p for p in out if p not in qs)
        if outside:
            raise Refusal(
                "the declared scope resolves %d position(s) %s OUTSIDE this prompt's query span. "
                "The codeword also appears throughout the demonstrations, so a selector that is "
                "not constrained to the query span can silently cut a demonstration row and "
                "report it as a query-position result." % (len(outside), outside[:6]))
    return sorted(out)


def selector_sites_agree(rel_end_rows: Sequence[int], seq_len: int) -> Dict[str, Any]:
    """`U1`: the PRE-FLIGHT feasibility pass and the PER-ROW resolution must agree BY CONSTRUCTION.

    They agree today for last-K because both compute `sorted(query_span)[-K:]`. The declared-offset
    selector keeps that property the only way that survives editing: both sites call THIS function,
    so "the two call sites agree" is not a thing anyone has to remember.
    """
    preflight = surface_span_from_rel_end(rel_end_rows, seq_len)
    per_row = surface_span_from_rel_end(rel_end_rows, seq_len)
    ok = preflight == per_row
    return {"ok": ok, "n_rows": len(preflight), "positions": preflight,
            "_rule": "one definition, two call sites; a second implementation is how a scope "
                     "silently becomes a different intervention than the one being reported"}


def assert_realised_equals_declared(records: Sequence[Dict[str, Any]],
                                    rel_end_rows: Sequence[int],
                                    decoded_by_rel_end: Optional[Dict[int, str]] = None
                                    ) -> Dict[str, Any]:
    """L-N4 -- the check this whole phase exists to provide.

    For every row: the PERSISTED `surface_span_positions` must equal `len(input_ids)+rel_end` for
    the scope's declared offsets, and the PERSISTED decoded tokens must match the token-role map's
    modal decodings. `primary.void`: "any realised row set that does not equal its declared
    rel_end set". A scope whose realised rows are not what the design says they are is precisely
    the defect the old ladder shipped.
    """
    if not records:
        raise ZeroBinding("the realised-row-set audit bound ZERO records; a check that binds "
                          "nothing is not a check")
    want_rel = sorted(int(r) for r in rel_end_rows)
    bad_rows, bad_tokens = [], []
    for rec in records:
        if "seq_len" not in rec or "surface_span_positions" not in rec:
            raise Refusal(
                "a liveness record carries no seq_len / surface_span_positions, so the realised "
                "row set cannot be compared with the declared one and is therefore NOT assumed to "
                "match. The producer must persist the realised positions on every row (U1).")
        seq_len = int(rec["seq_len"])
        want = sorted(seq_len + o for o in want_rel)
        got = sorted(int(x) for x in rec["surface_span_positions"])
        if got != want:
            bad_rows.append({"prompt_id": rec.get("prompt_id"), "seq_len": seq_len,
                             "declared": want[:8], "realised": got[:8]})
            continue
        if decoded_by_rel_end:
            toks = rec.get("surface_span_decoded")
            if toks is None:
                raise Refusal(
                    "a liveness record carries no `surface_span_decoded`. The frozen file requires "
                    "the realised row set AND ITS DECODED TOKENS on every row (U1 / "
                    "secondary.reported_always); positions alone cannot show WHICH TOKEN was cut.")
            for o, t in zip(want_rel, list(toks)):
                exp = decoded_by_rel_end.get(o)
                if exp is not None and str(t) != str(exp):
                    bad_tokens.append({"prompt_id": rec.get("prompt_id"), "rel_end": o,
                                       "expected": exp, "realised": t})
    ok = not bad_rows and not bad_tokens
    return {"n_records": len(records), "declared_rel_end": want_rel,
            "n_row_mismatches": len(bad_rows), "n_token_mismatches": len(bad_tokens),
            "examples": (bad_rows[:3] + bad_tokens[:3]), "ok": ok,
            "reason": "" if ok else
                      "%d row(s) realised a row set differing from the declared rel_end set and "
                      "%d realised a token differing from the token-role map's modal decoding. "
                      "primary.void: any realised row set that does not equal its declared rel_end "
                      "set VOIDS the arm." % (len(bad_rows), len(bad_tokens))}


def resolver_failure_gate(n_failed: int, n_total: int, pr: Prereg) -> Dict[str, Any]:
    """`primary.cannot_answer` (c): if a scope's row-set resolver fails on more than the declared
    fraction of rows, the arms no longer share a population -- CANNOT ANSWER, not a null."""
    if n_total <= 0:
        raise ZeroBinding("the resolver-failure gate bound ZERO rows")
    tol = resolver_failure_tolerance(pr)
    frac = float(n_failed) / float(n_total)
    over = frac > tol
    return {"n_failed": int(n_failed), "n_total": int(n_total), "fraction": frac,
            "tolerance": tol, "cannot_answer": over,
            "reason": "" if not over else
                      "the row-set resolver failed on %d/%d rows (%.4f), above the declared "
                      "tolerance %.4f: the arms no longer share a population, so every paired "
                      "delta would compare different sets of prompts. CANNOT ANSWER."
                      % (n_failed, n_total, frac, tol)}


# ============================================================================================
# 6. U2 -- THE PER-SCOPE DOSE-MATCHED RANDOM-ROW CONTROL
# ============================================================================================
def _draw_seed(seed: int, scope_id: str, draw_index: int) -> int:
    """A stable, cross-process seed. `hash()` is salted per interpreter run and a control band
    seeded with it is not reproducible, which is how a 'control band' becomes unrepeatable
    without anyone noticing."""
    h = hashlib.sha256(("%d|%s|%d" % (int(seed), str(scope_id), int(draw_index))).encode())
    return int.from_bytes(h.digest()[:8], "big")


def random_row_control_draw(pr: Prereg, scope_id: str, scope_rel_end: Sequence[int],
                            draw_index: int,
                            query_span: Optional[Sequence[int]] = None) -> Dict[str, Any]:
    """`dose_matching.per_scope_random_row_control`: m rows drawn from the QUERY SPAN, EXCLUDING
    the scope's own rows, seeded and reproducible, WITH THE DRAW RECORDED.

    This is the control the old ladder did not have. The nondemo-KEY control asks "do the
    DEMONSTRATIONS matter, or any equal quantity of context?"; this one asks "does cutting THESE
    rows matter, or any m rows?" -- which is exactly the rows-versus-cells confound `PR-032`
    declared it could not separate.
    """
    span = sorted(set(int(x) for x in (query_span if query_span is not None
                                       else query_span_rel_end(pr))))
    own = set(int(x) for x in scope_rel_end)
    m = len(own)
    if m <= 0:
        raise ZeroBinding(
            "a dose-matched random-row control was requested for a scope of ZERO rows. There is "
            "no dose to match, and a zero-row control would 'pass' vacuously.")
    pool = [r for r in span if r not in own]
    if len(pool) < m:
        raise Refusal(
            "scope %s asks for %d control row(s) but the query span has only %d row(s) outside "
            "the scope. A dose-matched random-row control is not constructible for this scope on "
            "this template, and reporting it as passed would be a check over a set it could not "
            "build." % (scope_id, m, len(pool)))
    rng = random.Random(_draw_seed(random_row_seed(pr), scope_id, draw_index))
    rows = sorted(rng.sample(pool, m))
    return {"scope_id": scope_id, "draw_index": int(draw_index),
            "seed": random_row_seed(pr), "derived_seed": _draw_seed(random_row_seed(pr), scope_id,
                                                                    draw_index),
            "m": m, "pool_size": len(pool), "pool_rel_end": pool,
            "excluded_rel_end": sorted(own), "rel_end_rows": rows,
            "_recorded": "the draw is persisted so 'which rows did the control actually cut' is "
                         "answerable from the artifact and not from the seed"}


def random_row_control_constructible(pr: Prereg, scope_id: str, scope_rel_end: Sequence[int],
                                     query_span: Optional[Sequence[int]] = None) -> Dict[str, Any]:
    """Can this scope's dose-matched random-row control be BUILT AT ALL on this template?

    A RECORDED CONFLICT WITH THE FROZEN FILE. `dose_matching.per_scope_random_row_control` says
    "for every scope of size m, a SEEDED RANDOM m-row draw from the query span that excludes the
    scope's own rows". The query span on this template is 28 rows (verified against the frozen
    token-role map in every prompt), so a scope of m rows leaves a pool of 28-m. For the two
    largest scopes that pool is SMALLER THAN THE DOSE and the control the design requires for
    every scope does not exist for them. That is reported here, before extraction, rather than
    discovered as a "passed" control that was really a smaller draw.
    """
    span = sorted(set(int(x) for x in (query_span if query_span is not None
                                       else query_span_rel_end(pr))))
    own = set(int(x) for x in scope_rel_end)
    m = len(own)
    pool = [r for r in span if r not in own]
    ok = (m > 0) and (len(pool) >= m)
    return {"scope_id": scope_id, "m": m, "pool_size": len(pool), "span_size": len(span),
            "constructible": ok,
            "reason": "" if ok else
                      "scope %s cuts %d of the %d query-span rows, leaving a pool of %d -- fewer "
                      "than the dose it must match. A dose-matched random-row control is NOT "
                      "CONSTRUCTIBLE for this scope on this template. CONFLICT WITH THE FROZEN "
                      "FILE, which requires one for EVERY scope; the config is frozen and is not "
                      "edited, so the conflict is recorded and the scope carries no random-row "
                      "control." % (scope_id, m, len(span), len(pool))}


def random_row_control_band(pr: Prereg, scope_id: str, scope_rel_end: Sequence[int],
                            query_span: Optional[Sequence[int]] = None) -> Dict[str, Any]:
    """The declared number of draws for one scope, with the DISTINCTNESS of the draws checked.

    "This project has twice published a 'control band' that was secretly n=1 because the seed never
    reached the draw." The frozen file's gate is on the three OUTPUT hashes; this is the cheaper,
    CPU-only precondition -- if the three ROW SETS are identical the outputs cannot differ either.
    """
    n = n_random_row_draws(pr)
    if n < 2:
        raise Refusal("seeds.n_random_row_draws is %d; a band of fewer than two draws is not a "
                      "band" % n)
    draws = [random_row_control_draw(pr, scope_id, scope_rel_end, i, query_span)
             for i in range(n)]
    sets = [tuple(d["rel_end_rows"]) for d in draws]
    n_distinct = len(set(sets))
    pool_size = draws[0]["pool_size"]
    m = draws[0]["m"]
    n_possible = math.comb(pool_size, m) if pool_size >= m else 0
    ok = n_distinct == n or n_possible < n
    return {"scope_id": scope_id, "n_draws": n, "n_distinct_row_sets": n_distinct,
            "n_possible_row_sets": n_possible, "draws": draws, "ok": ok,
            "reason": "" if ok else
                      "%d draw(s) produced %d distinct row set(s); with %d possible sets the seed "
                      "did not reach the draw and the control band is secretly n=1"
                      % (n, n_distinct, n_possible),
            "_note": "" if n_possible >= n else
                     "the pool admits only %d distinct row set(s) for a dose of %d, so identical "
                     "draws here are a PROPERTY OF THE TEMPLATE and are reported as such rather "
                     "than as a seeding failure -- but the arm's three OUTPUT hashes must still "
                     "differ, and if they cannot, the control is not evidence" % (n_possible, m)}


def control_band_gate(per_draw_output_sha: Sequence[str], n_expected: int) -> Dict[str, Any]:
    """L-N7 -- three draws must produce THREE DISTINCT OUTPUT HASHES. Identical hashes VOID the
    control band."""
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


def assert_scope_has_its_control(scope_id: str, control: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """`things_that_must_not_be_said`: "a scope null reported without its realised dose and its
    dose-matched control". A scope reported without one is refused, not annotated."""
    if not control:
        raise Refusal(
            "scope %s was reported with NO dose-matched control. The frozen file's own list of "
            "things that must not be said includes a scope null reported without its realised "
            "dose and its dose-matched control -- the SCOPE-vs-ITS-OWN-CONTROL contrast IS the "
            "estimate, never a scope-vs-scope difference in raw magnitude." % scope_id)
    if not control.get("ok"):
        raise Refusal(
            "scope %s's dose-matched control did not pass its own gate (%s); a scope cannot be "
            "reported against a control that is itself void."
            % (scope_id, control.get("reason") or "no reason recorded"))
    return control


# ============================================================================================
# 7. POPULATION BINDING -- on `cell`, never on `condition`
# ============================================================================================
SELECTOR_FIELD = "cell"
FORBIDDEN_SELECTOR_FIELD = "condition"


def whole_population_exclusions(pr: Prereg) -> List[str]:
    """The three exclusions, from the config's BOOLEAN `whole_population` -- never from prose and
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


def bind_rows(pr: Prereg, bank_rows: Dict[str, Dict[str, Any]],
              assign: Dict[str, str], selector_field: str = SELECTOR_FIELD,
              cell: Optional[str] = None, query_kind: Optional[str] = None,
              n_examples: Optional[int] = None) -> Dict[str, Any]:
    """Bind the analysis population. A zero-row or zero-domain bind RAISES.

    `population._cell_note`: "Select on the field `cell` == 'C'. NOT `condition` ==
    'natural_doublespeak': that string lives in `condition`, and selecting the wrong field binds
    ZERO rows (A-039)." So selecting on anything other than `cell` is refused BEFORE the bind, and
    a bind that returns nothing is refused after it. Both, because a guard that fires on only one
    of them lets the other through.
    """
    if selector_field != SELECTOR_FIELD:
        raise Refusal(
            "population binding may only select on %r; %r was requested. Binding on %r is A-039 "
            "-- it binds ZERO rows and a zero-row population silently becomes a zero-row result."
            % (SELECTOR_FIELD, selector_field, selector_field))
    c = str(cell or primary_cell(pr))
    qk = str(query_kind or primary_channel(pr))
    dose = int(n_examples if n_examples is not None
               else pr.require("population", "n_examples_primary"))
    excluded = set(whole_population_exclusions(pr))
    rows, domains = [], set()
    for r in bank_rows.values():
        if str(r.get(SELECTOR_FIELD)) != c:
            continue
        if str(r.get("query_kind")) != qk:
            continue
        if int(r.get("n_examples")) != dose:
            continue
        dom = str(r.get("domain"))
        if dom in excluded:
            continue
        rows.append(r)
        domains.add(dom)
    if not rows:
        raise ZeroBinding(
            "cell=%r query_kind=%r n_examples=%d bound ZERO ROWS after the %d whole-population "
            "exclusions. A zero-row bind is a refusal, never an empty result (A-039 / C-074)."
            % (c, qk, dose, len(excluded)))
    if not domains:
        raise ZeroBinding("cell=%r bound rows but ZERO domains" % c)
    missing = sorted(d for d in domains if d not in assign)
    if missing:
        raise Refusal("the split manifest assigns no split to %d bound domain(s): %s"
                      % (len(missing), missing[:5]))
    return {"cell": c, "query_kind": qk, "n_examples": dose, "n_rows": len(rows),
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
    """L-N11 / `primary.void`: the ledgered prompt_ids are replayed as an exclusion into EVERY arm,
    so a delta is never computed across unequal populations."""
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


def refuse_pooling_across_banks(bank_keys: Sequence[str]) -> str:
    """`_two_codewords_are_a_transfer_pair_not_a_pool`: every estimate is reported PER CODEWORD
    BANK and NEVER pooled into one p-value. button_bomb installs in 92/113 domains and basket_bomb
    in 46/113 -- a factor of two from the lexical codeword alone."""
    keys = list(bank_keys)
    if len(keys) != 1:
        raise Refusal(
            "an estimate was requested over %d banks (%s). The two codewords are a declared "
            "TRANSFER PAIR, not a pool: every estimate is reported PER CODEWORD BANK and is NEVER "
            "pooled into one p-value." % (len(keys), keys))
    return keys[0]


def primary_banks(pr: Prereg) -> List[str]:
    concept = str(pr.require("population", "concept_primary"))
    banks = pr.require("population", "banks")
    out = sorted(k for k in banks if k.endswith("_" + concept))
    if not out:
        raise Refusal("no bank carries the primary concept %r" % concept)
    return out


def descriptive_banks(pr: Prereg) -> List[str]:
    return sorted(set(pr.require("population", "banks")) - set(primary_banks(pr)))


def refuse_descriptive_as_confirmatory(pr: Prereg, bank_key: str) -> str:
    """The knife and gun arms carry NO multiplicity membership and no p-value may be quoted from
    them as a mechanism result: knife installs in 0/113 domains on the concept-free channel and gun
    in 1/113, so an arm read as "the knockout removed the installed concept" had no installed
    concept to remove."""
    if bank_key in descriptive_banks(pr):
        raise Refusal(
            "bank %r is a REGISTERED DESCRIPTIVE arm and carries no confirmatory weight. %s"
            % (bank_key, pr.require("installation",
                                    "THE_ASYMMETRY_AND_WHAT_IT_MAKES_UNCONSTRUCTIBLE",
                                    "consequence")))
    return bank_key


# ============================================================================================
# 8. THE CHANNEL -- the leakage this phase exists to remove
# ============================================================================================
def refuse_display_channel_as_primary(pr: Prereg, query_kind: str) -> str:
    """`_CHANNEL_IS_THE_POINT_OF_THIS_PHASE`. The display channel NAMES the concept in its own
    question on 100.0% of its rows against 0.0% on the primary channel, and the same rows scored
    through it take knife from 0.000 to 0.628 installing domains. Any localisation claim from it
    is on the frozen file's forbidden list."""
    qk = str(query_kind).strip()
    if qk == display_channel(pr):
        raise Refusal(
            "REFUSED: %r is the DISPLAY channel. It names the concept in its own question on "
            "100.0%% of its rows (0.0%% on %r), so a mechanism number read from it measures the "
            "prompt as much as the model. It is scored and reported as SECONDARY DISPLAY with the "
            "leakage note attached, and NO mechanism claim may rest on it."
            % (qk, primary_channel(pr)))
    if qk != primary_channel(pr):
        raise Refusal("query_kind %r is neither the preregistered primary channel %r nor the "
                      "declared display channel %r" % (qk, primary_channel(pr),
                                                       display_channel(pr)))
    return qk


def refuse_display_fallback(pr: Prereg, primary_engaged: bool) -> None:
    """A disengaged primary channel is CANNOT ANSWER, never a licence to fall back on the display
    channel -- where `option_mass` is 0.708 precisely because the question supplies the answer."""
    if not primary_engaged:
        raise CannotAnswer(
            "the primary channel %r is DISENGAGED on this arm, so there is no y to move. That is "
            "CANNOT ANSWER. Falling back to %r is FORBIDDEN in this phase: it is exactly the "
            "leakage this phase exists to remove."
            % (primary_channel(pr), display_channel(pr)))


def concept_word_absence_gate(rows: Sequence[Dict[str, Any]], concept_forms: Sequence[str],
                              declared_field: str = "n_concept_occurrences") -> Dict[str, Any]:
    """L-N12: ZERO whole-word concept occurrences in `full_prompt` on every scored primary-channel
    row, recounted independently AND cross-checked against the bank's own declared count.
    A DISAGREEMENT BETWEEN THE TWO COUNTS IS A REFUSAL, not a tie-break."""
    if not rows:
        raise ZeroBinding("the concept-absence audit bound ZERO rows")
    pat = re.compile(r"\b(?:%s)\b" % "|".join(re.escape(str(c)) for c in concept_forms),
                     flags=re.IGNORECASE)
    n_with, disagreements = 0, []
    for r in rows:
        text = str(r.get("full_prompt", ""))
        got = len(pat.findall(text))
        if got:
            n_with += 1
        dec = r.get(declared_field)
        if dec is not None and int(dec) != got:
            disagreements.append({"prompt_id": r.get("prompt_id"), "recount": got,
                                  "declared": int(dec)})
    if disagreements:
        raise Refusal(
            "the independent whole-word recount disagrees with the bank's own %s on %d row(s) "
            "(e.g. %s). R-116's two counts agreed EXACTLY; a disagreement means one of them is "
            "measuring something else, and the honest response is a refusal rather than picking "
            "the convenient one." % (declared_field, len(disagreements), disagreements[:2]))
    ok = n_with == 0
    return {"n_rows": len(rows), "n_rows_with_concept_word": n_with, "ok": ok,
            "reason": "" if ok else
                      "%d/%d primary-channel rows contain the concept word in full_prompt. The "
                      "primary channel is defined by its ABSENCE (0 of 6780 dose-4 rows in "
                      "R-116); rows carrying it are not this channel." % (n_with, len(rows))}


# ============================================================================================
# 9. HOOK LIVENESS -- a dead hook must be impossible to mistake for a clean null
# ============================================================================================
@dataclass
class LivenessRecord:
    """One record per row per arm."""
    arm_id: str = ""
    scope_id: str = ""
    prompt_id: str = ""
    enabled: bool = True
    hook_fired_count: int = 0
    n_forward: int = 0
    n_prefill_edits: int = 0
    n_decode_edits: int = 0
    keys_masked: int = 0
    surface_span_n_tokens: int = 0          # the REALISED dose
    surface_span_positions: List[int] = field(default_factory=list)
    surface_span_decoded: List[str] = field(default_factory=list)
    n_cells_edited_expected: int = 0
    n_cells_edited_realised: int = 0
    attn_implementation: str = ""           # READ BACK from the loaded config
    seq_len: int = 0
    query_kind: str = ""
    output_sha256: str = ""

    def as_row(self) -> Dict[str, Any]:
        return dict(self.__dict__)


def liveness_gate(records: Sequence[Dict[str, Any]], arm_id: str, pr: Prereg,
                  expect_enabled: bool = True) -> Dict[str, Any]:
    """Did this arm's hook demonstrably fire, at the declared scope, under eager attention?

    `primary.void`: `hook_fired_count == 0`; `attn_implementation` not eager ON THE LOADED CONFIG;
    `n_decode_edits != 0` in this PREFILL-ONLY family; a realised dose of 0; realised != expected
    cells. Each makes a null VOID, not a negative -- and a dead hook produces EXACTLY the artifact
    a real intervention with no effect produces, which is why this runs before any outcome exists.
    """
    want_impl = required_attn_impl(pr)
    reasons: List[str] = []
    if not records:
        return {"arm_id": arm_id, "live": False, "n_rows": 0, "expect_enabled": expect_enabled,
                "reasons": ["NO LIVENESS RECORDS AT ALL -- %s is absent or empty for arm %r. A "
                            "null behind an unrecorded hook is VOID, not a negative."
                            % (CONTRACT_LIVENESS, arm_id)]}
    # ---- PR059-D4: A MISSING FIELD RAISES; IT IS NEVER READ AS A MEASURED ZERO ---------------
    # Until this block, every counter below was read with `r.get(key, 0)`. The attention-knockout
    # producer wrote NONE of `hook_fired_count` / `n_cells_edited_expected` /
    # `n_cells_edited_realised`, so on a real knockout arm this gate compared 0 against 0 and
    # called the arm dead for a SCHEMA reason -- or, with the comparison satisfied, called a
    # never-measured hook clean. Both are the C-117 shape: a check that reads the producer's own
    # absent field and asserts something about nothing.
    #
    # The producer now owns these counts (`ScopedAttentionKnockout._pre`, expected BEFORE the
    # write and realised READ BACK from the mask). The gate's job is to refuse to guess: an
    # ABSENT field is a REFUSAL, and it is a different outcome from a field that is present and
    # zero -- which is a DEAD HOOK and is reported as one.
    _required = (("attn_implementation", "n_forward", "hook_fired_count",
                  "n_prefill_edits", "n_decode_edits", "surface_span_n_tokens",
                  "n_cells_edited_expected", "n_cells_edited_realised")
                 if expect_enabled else
                 ("attn_implementation", "n_forward", "enabled", "hook_fired_count",
                  "n_cells_edited_realised"))
    for _i, _r in enumerate(records):
        _missing = [k for k in _required if k not in _r]
        if _missing:
            raise Refusal(
                "liveness record %d of arm %r is MISSING %s. The gate REFUSES to read an absent "
                "field as a measured zero: 'the producer never wrote this' and 'the hook fired "
                "zero times' are opposite verdicts, and defaulting collapses them into the one "
                "that looks like a clean scientific null. Fix the PRODUCER "
                "(score_behavior/pair_common), never this gate -- a lenient gate here is the "
                "C-117 defect with the sign flipped."
                % (_i, arm_id, ", ".join(_missing)))
    impls = {str(r.get("attn_implementation", "")) for r in records}
    if impls != {want_impl}:
        reasons.append(
            "attn_implementation on the LOADED config is %s, not %r on every record. Under SDPA "
            "the additive mask edit is DISCARDED and the knockout is a silent no-op scoring as a "
            "CLEAN NULL. Any live arm not recorded as eager ON THE LOADED CONFIG is VOID, not a "
            "negative." % (sorted(impls), want_impl))
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
            reasons.append("n_prefill_edits == %d; this prefill-only family requires > 0" % prefill)
        if decode != 0:
            reasons.append("n_decode_edits == %d; the contract requires EXACTLY 0 for every scope "
                           "in this prefill-only family. A non-zero value means the scoping LEAKED "
                           "and the mode is secretly a larger intervention than the one reported."
                           % decode)
        if not expected:
            reasons.append("n_cells_edited_expected is 0 everywhere: the arm declared no "
                           "destinations, so 'realised == expected' is vacuously true and proves "
                           "nothing (a check that binds zero is not a check)")
        elif realised != expected:
            reasons.append("n_cells_edited_realised %d != expected %d (primary.void)"
                           % (realised, expected))
        if zero_dose:
            reasons.append("%d/%d records have a REALISED DOSE of 0 tokens -- the surface span "
                           "resolved to nothing and the arm cut nothing" % (zero_dose,
                                                                            len(records)))
    else:
        # the DISABLED-HOOK BRIDGE (L-N1): the code path runs and edits nothing.
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


def audit_end_relative(records: Sequence[Dict[str, Any]], rel_end_rows: Sequence[int]
                       ) -> Dict[str, Any]:
    """L-N10: every edit index is `len(input_ids)+rel_end`, never a constant absolute int.

    The witness is structural rather than declarative: if the sequences differ in length and the
    realised positions do NOT, an absolute index was reused. That is the recorded bug class -- the
    absolute codeword index is identical across the three concepts in 0/2300 triples while the
    end-relative index is identical in 2300/2300.
    """
    if not records:
        raise ZeroBinding("the end-relative audit bound ZERO records")
    want_rel = sorted(int(r) for r in rel_end_rows)
    bad = []
    lens, firsts = set(), set()
    for r in records:
        if "seq_len" not in r or "surface_span_positions" not in r:
            raise Refusal("a liveness record is missing seq_len / surface_span_positions -- the "
                          "end-relative audit cannot be performed and is therefore NOT assumed "
                          "to pass")
        n = int(r["seq_len"])
        pos = sorted(int(x) for x in r["surface_span_positions"])
        lens.add(n)
        if pos:
            firsts.add(pos[0])
        if pos != sorted(n + o for o in want_rel):
            bad.append({"prompt_id": r.get("prompt_id"), "seq_len": n, "positions": pos[:6]})
    if len(lens) > 1 and len(firsts) == 1:
        bad.append({"witness": "one absolute position across sequences of differing length"})
    return {"n_records": len(records), "n_violations": len(bad), "ok": not bad,
            "n_distinct_seq_len": len(lens), "n_distinct_first_position": len(firsts),
            "witness_note": "the first realised position takes %d value(s) over %d sequence "
                            "length(s); a SINGLE value across differing lengths means an absolute "
                            "index was reused" % (len(firsts), len(lens))}


def disabled_bridge_gate(baseline_sha: str, bridge_sha: str, max_abs_hidden_diff: float
                         ) -> Dict[str, Any]:
    """L-N1: byte-identical greedy generations AND max|diff| == 0 hidden states."""
    same = (baseline_sha == bridge_sha) and bool(baseline_sha)
    zero = (float(max_abs_hidden_diff) == float(0))
    return {"ok": same and zero, "generations_byte_identical": same,
            "max_abs_hidden_diff": float(max_abs_hidden_diff),
            "reason": "" if (same and zero) else
                      "the disabled-hook bridge did not reproduce the untouched baseline "
                      "(byte-identical=%s, max|diff|=%r); the intervention code path changes the "
                      "result even with the hook off" % (same, max_abs_hidden_diff)}


def null_dose_arm_gate(pr: Prereg, n_ledgered: int, delta_values: Sequence[float]
                       ) -> Dict[str, Any]:
    """L-N6: at n_examples=0 there are no demonstrations to cut, so the rows are LEDGERED and the
    ledger count is the check.

    `dose_0_is_not_readable`: median option_mass at dose 0 is 0.0328, below the gate, and only
    19.0% of rows clear it -- so the dose-0 arm is a POPULATION CHECK and NO dose-0 logodds is
    interpreted. A dose-0 delta offered as an outcome is refused here rather than printed.
    """
    if int(pr.require("population", "n_examples_null")) != 0:
        raise Refusal("population.n_examples_null is not zero; the null-dose arm is not the arm "
                      "this gate was written for")
    if delta_values:
        raise Refusal(
            "a semantic_logodds delta was supplied for the n_examples=0 arm. The frozen file says "
            "in terms that the dose-0 null is a POPULATION CHECK, not a readable outcome, and "
            "that no dose-0 logodds is interpreted. Refusing to score it.")
    ok = int(n_ledgered) > 0
    return {"ok": ok, "n_ledgered": int(n_ledgered),
            "reason": "" if ok else
                      "the n_examples=0 arm ledgered ZERO rows, so it certifies nothing"}


def refuse_dose_pooling(doses: Sequence[int]) -> int:
    """`_dose_rule`: doses are separate preregistered cells and are NEVER pooled into one
    p-value."""
    ds = sorted(set(int(d) for d in doses))
    if len(ds) != 1:
        raise Refusal(
            "an estimate was requested over doses %s. Doses are separate preregistered cells and "
            "are NEVER pooled into one p-value." % ds)
    return ds[0]


# ============================================================================================
# 10. READOUT BEFORE DELTA -- the weak-engagement mitigation, structurally
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


def _median(xs: Sequence[float]) -> float:
    return _quantile(xs, float(1) / float(2))


@dataclass
class ArmReadout:
    """The full `option_mass` distribution AND the argmax answer distribution for ONE arm.

    `primary._largest_risk` mitigation (1): "the argmax decoded answer and the full option_mass
    distribution are reported for every arm BESIDE every delta, NEVER AFTER IT". Here that is
    enforced by making the readout an object a delta cannot exist without, and by `rendered` -- a
    delta refuses to render until its readout has been rendered. The median of ~0.11 means the
    model's actual preferred word is a THIRD word about 89% of the time, so semantic_logodds is an
    ORDERING INSIDE A RESIDUAL and must never reach a reader on its own.
    """
    arm_id: str
    scope_id: str
    n_rows: int
    n_domains: int
    option_mass: List[float] = field(default_factory=list)
    argmax_answers: List[str] = field(default_factory=list)
    logodds: List[float] = field(default_factory=list)
    rendered: bool = False

    def __post_init__(self):
        if not self.option_mass:
            raise ZeroBinding(
                "an ArmReadout for arm %r was constructed with NO option_mass values. On this "
                "weakly engaged channel a delta without its engagement distribution is "
                "uninterpretable in exactly the way primary._largest_risk describes."
                % self.arm_id)
        if not self.argmax_answers:
            raise ZeroBinding(
                "an ArmReadout for arm %r carries NO argmax decoded answers. The frozen file "
                "requires the argmax answer BESIDE every delta, because a knockout can move the "
                "ordering inside the residual while the model's output word never changes."
                % self.arm_id)

    def median_option_mass(self) -> float:
        return _median(self.option_mass)

    def summary(self) -> Dict[str, Any]:
        counts: "OrderedDict[str, int]" = OrderedDict()
        for a in self.argmax_answers:
            counts[str(a)] = counts.get(str(a), 0) + 1
        top = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
        deciles = {("p%d" % int(round(q * 100))): _quantile(self.option_mass, q)
                   for q in (float(1) / float(10), float(1) / float(4), float(1) / float(2),
                             float(3) / float(4), float(9) / float(10))}
        return {"arm_id": self.arm_id, "scope_id": self.scope_id, "n_rows": self.n_rows,
                "n_domains": self.n_domains, "n_scored": len(self.option_mass),
                "option_mass_median": self.median_option_mass(),
                "option_mass_quantiles": deciles,
                "option_mass_min": min(self.option_mass), "option_mass_max": max(self.option_mass),
                "argmax_answer_counts": OrderedDict(top),
                "argmax_top1": top[0][0] if top else None,
                "n_distinct_argmax_answers": len(counts)}

    def render(self, fh=sys.stdout) -> Dict[str, Any]:
        s = self.summary()
        fh.write("  READOUT %s (%s) -- reported BESIDE the delta, never after it\n"
                 % (self.arm_id, self.scope_id))
        fh.write("    n_rows=%d n_domains=%d option_mass median=%.6g quantiles=%s\n"
                 % (s["n_rows"], s["n_domains"], s["option_mass_median"],
                    json.dumps({k: round(v, 6) for k, v in s["option_mass_quantiles"].items()})))
        fh.write("    argmax answers (top %d of %d distinct): %s\n"
                 % (min(len(s["argmax_answer_counts"]), 5), s["n_distinct_argmax_answers"],
                    json.dumps(list(s["argmax_answer_counts"].items())[:5])))
        self.rendered = True
        return s


def engagement_gate(readout: ArmReadout, pr: Prereg) -> Dict[str, Any]:
    """`O1.cannot_answer_if`: median `option_mass` below the declared gate is CANNOT ANSWER for
    that arm -- never a fallback to the display channel."""
    gate = option_mass_gate_value(pr)
    med = readout.median_option_mass()
    below = med < gate
    return {"arm_id": readout.arm_id, "median_option_mass": med, "gate": gate,
            "engaged": not below, "cannot_answer": below,
            "reason": "" if not below else
                      "median option_mass %.6g in arm %r is below the declared gate %.6g: the "
                      "concept-free channel is DISENGAGED on this arm, so there is no y to move. "
                      "CANNOT ANSWER -- and falling back to the display channel is FORBIDDEN."
                      % (med, readout.arm_id, gate)}


#: The amendment DCS-PR-065 that carries `option_mass_gate_policy`. Loaded lazily and ONLY by the
#: self-test / mutation harnesses and by callers that pass it in explicitly; `below_gate_disposition`
#: never reaches for it on its own, because a stop-scope that appears by default is not declared.
P11_AMENDMENT3 = "configs/dcs_ts_pr065_phase11_amendment3.json"


def load_gate_policy_amendment(path: str = P11_AMENDMENT3) -> Dict[str, Any]:
    """Read the amendment JSON that declares `option_mass_gate_policy`. No hashing here -- the
    RUNNER's `load_amendment()` is what pins the parent sha and refuses a non-FROZEN file; this is
    only the reader."""
    fp = path if os.path.isabs(path) else os.path.join(REPO, path)
    with open(fp) as fh:
        return json.load(fh)


#: `score_behavior.py`'s tail-gate return code. It is NOT a crash: the run is fully written and
#: its healthy readouts are usable ("the run is written and its healthy readouts are usable, but
#: these are NOT reportable"). A caller that treats it as a crash discards a completed measurement.
BELOW_GATE_RC = 4

#: The three dispositions `option_mass_gate_policy` may assign. Stated here, in the analyzer, so
#: the runner does not get to invent a fourth.
BELOW_GATE_DISPOSITIONS = ("KILL_BANK", "CANNOT_ANSWER_BANK", "CANNOT_ANSWER_ARM")


def below_gate_disposition(pr: Prereg, amendment: Optional[Dict[str, Any]],
                           arm_kind: str, scope_id: str) -> Dict[str, Any]:
    """WHAT HAPPENS TO THE REST OF A STAGE when an arm falls below the option-mass gate.

    THE GATE ITSELF IS NOT DECIDED HERE AND IS NOT DECIDED BY ANY AMENDMENT. The FROZEN parent
    scopes it to EVERY ARM, four times -- `O1_semantic_readout.cannot_answer_if` ("median
    option_mass in a scope's arm falls below the [gate] -- CANNOT ANSWER"), `primary.cannot_answer`
    clause (a), `primary._largest_risk` mitigation (3), and separately, in DIFFERENT WORDS and with
    a DIFFERENT consequence, the BASELINE case in `kill_condition` ("if median option_mass in the
    S_0 baseline falls below the [gate] ... no knockout job is submitted at all"). Two rules,
    two scopes, two consequences, written together on 2026-09-07. `engagement_gate()` above is that
    rule and it is unchanged. (The literal gate value is elided as `[gate]` in these two
    quotations ONLY because this analyzer's own `no_gate_literals` check forbids a declared gate
    value appearing as a numeric literal anywhere in its source; the unelided text is quoted in
    full in DCS-PR-065 `decision_PR059_D9.the_design_already_says`.)

    What the parent never says is whether the ELEVEN OTHER ARMS of the stage are still submitted.
    That is DCS-PR-065 `option_mass_gate_policy`, and this function is the only place it is read.

    IT IS A TOTAL FUNCTION OF THE ARM'S ROLE. It reads no measured value at all -- not the median,
    not the margin. It would return the same disposition for an arm at 0.01 and an arm at 0.04999.
    A stop-scope that varied with how close the arm came to the threshold would be a stop-scope
    chosen to get a result.

    REFUSES, rather than defaulting, when: the policy block is absent (an amendment that does not
    carry it cannot license a below-gate arm); its `gate_value` or `gate_statistic` disagrees with
    the frozen parent's, which would make this a second gate; the role is unmapped; or the mapped
    disposition is not one of `BELOW_GATE_DISPOSITIONS`.
    """
    if not amendment:
        raise Refusal(
            "an arm fell below the option-mass gate and NO AMENDMENT is loaded. The frozen "
            "preregistration says the arm is CANNOT ANSWER but is silent on the rest of the "
            "stage, so there is no declared stop-scope to apply. REFUSING rather than picking "
            "one at the moment it decides a result.")
    pol = amendment.get("option_mass_gate_policy")
    if not isinstance(pol, dict):
        raise Refusal(
            "amendment %r carries no `option_mass_gate_policy`, so it does not declare what "
            "happens to the rest of a stage when an arm falls below the gate. An amendment that "
            "is silent on the question cannot be read as permitting anything."
            % amendment.get("id"))
    gate = option_mass_gate_value(pr)
    if float(pol.get("gate_value", -1.0)) != float(gate):
        raise Refusal(
            "`option_mass_gate_policy.gate_value` is %r and the FROZEN preregistration's gate is "
            "%r. An amendment that restates the gate at a different number is a SECOND GATE, and "
            "this file may not move a numeric gate." % (pol.get("gate_value"), gate))
    if pol.get("gate_statistic") != "median_true":
        raise Refusal(
            "`option_mass_gate_policy.gate_statistic` is %r; the producer's `reportable` flag and "
            "`engagement_gate()` both read the TRUE median. Two statistics is two gates."
            % (pol.get("gate_statistic"),))
    if pol.get("gate_scope") != "every_arm":
        raise Refusal(
            "`option_mass_gate_policy.gate_scope` is %r. The frozen parent scopes the gate to "
            "every arm in three fields and states the baseline case separately in a fourth; an "
            "amendment may not re-scope it." % (pol.get("gate_scope"),))
    if pol.get("baseline_gate_is_not_relaxed") is not True:
        raise Refusal("`option_mass_gate_policy` must assert `baseline_gate_is_not_relaxed`: the "
                      "baseline gate is not weakened under any reading.")
    if pol.get("stop_scope_depends_on_margin") is not False:
        raise Refusal("`option_mass_gate_policy.stop_scope_depends_on_margin` must be false. A "
                      "stop-scope that reads how far below the gate the arm landed is a rule "
                      "written to fit one number.")
    ref = reference_scope_id(pr)
    role = ("reference_scope" if (arm_kind == "scope" and scope_id == ref) else arm_kind)
    table = pol.get("below_gate_disposition_by_arm_role") or {}
    if role not in table:
        raise Refusal(
            "`option_mass_gate_policy.below_gate_disposition_by_arm_role` maps no disposition for "
            "arm role %r (known: %s). An unmapped role is an undeclared decision, not a default."
            % (role, sorted(table)))
    disp = table[role]
    if disp not in BELOW_GATE_DISPOSITIONS:
        raise Refusal("disposition %r for role %r is not one of %s"
                      % (disp, role, list(BELOW_GATE_DISPOSITIONS)))
    if not pol.get("cross_bank_isolation"):
        raise Refusal(
            "`option_mass_gate_policy.cross_bank_isolation` is not set. `primary.statistic` says "
            "results are 'reported per codeword bank and never pooled across banks'; a below-gate "
            "arm in one bank may not close another bank that was never run.")
    if not pol.get("must_travel_with_every_derived_number"):
        raise Refusal(
            "`option_mass_gate_policy.must_travel_with_every_derived_number` is not set. "
            "`primary._largest_risk` mitigation (1) requires the full option_mass distribution "
            "beside every delta; a below-gate arm reported without it reads as if it were fine.")
    return {"arm_kind": arm_kind, "scope_id": scope_id, "role": role, "disposition": disp,
            "closes_bank": disp.endswith("_BANK"),
            "gate": gate, "gate_statistic": "median_true",
            "policy_from": amendment.get("id"),
            "required_travelling_fields": list(pol.get("required_travelling_fields") or []),
            "reason": "arm role %r -> %s. %s" % (role, disp,
                                                 (pol.get("dispositions") or {}).get(disp, ""))}


def argmax_switch_rate(baseline: Sequence[str], scope: Sequence[str]) -> Dict[str, Any]:
    """A CORROBORANT, explicitly NOT one of the conjunctive success conditions (mandate 10.5 says
    "ideally"). It is reported because a delta that moves an ordering while the output word never
    changes is the honest description of what this channel can show."""
    if len(baseline) != len(scope):
        raise Refusal("the argmax-switch rate was asked to pair %d baseline answers with %d "
                      "scope answers; unequal arms cannot be paired row-for-row"
                      % (len(baseline), len(scope)))
    if not baseline:
        raise ZeroBinding("the argmax-switch rate bound ZERO paired rows")
    n_sw = sum(1 for a, b in zip(baseline, scope) if str(a) != str(b))
    return {"n_paired": len(baseline), "n_switched": n_sw,
            "rate": float(n_sw) / float(len(baseline)),
            "_status": "CORROBORANT, not required for success"}


@dataclass
class ScopeDelta:
    """A domain-level paired delta that CANNOT be constructed or rendered without its readout."""
    scope_id: str
    arm_id: str
    readout: Optional[ArmReadout]
    control: Optional[Dict[str, Any]]
    per_domain: Dict[str, float]
    stats: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.readout is None:
            raise Refusal(
                "a ScopeDelta for scope %r was constructed with NO ArmReadout. "
                "primary._largest_risk mitigation (1) is that the argmax answer and the full "
                "option_mass distribution are reported BESIDE every delta; a delta object without "
                "one cannot enforce it." % self.scope_id)
        if not self.per_domain:
            raise ZeroBinding("the paired delta for scope %r bound ZERO domains" % self.scope_id)


def render_delta(d: ScopeDelta, p_floor_value: float, fh=sys.stdout) -> str:
    """Emit a delta. REFUSES if its readout has not been rendered first, and REFUSES if the scope
    has no dose-matched control."""
    if d.readout is None or not d.readout.rendered:
        raise Refusal(
            "REFUSING to print the %s delta: its option_mass / argmax readout has not been "
            "rendered. On this channel the two scored options carry about a ninth of the "
            "next-token mass, so a delta read without its engagement distribution is an ordering "
            "inside a residual presented as an effect." % d.scope_id)
    assert_scope_has_its_control(d.scope_id, d.control)
    st = d.stats
    line = ("  DELTA  %s (%s): domain-mean paired delta = %.6g over %d domains; %s"
            % (d.scope_id, d.arm_id, st.get("observed_delta", float("nan")), len(d.per_domain),
               st.get("permutation", {}).get("formatted",
                                             "p unavailable [floor %.3e]" % p_floor_value)))
    fh.write(line + "\n")
    return line


# ============================================================================================
# 11. STATISTICS -- DOMAIN level only
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
            "Row-level permutation has a MEASURED false-positive rate of 0.2000 on this design "
            "and appears in no arm, no secondary and no diagnostic of this phase. A significant "
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
    null = [sum((x if rng.getrandbits(1) else -x) for x in deltas) / len(deltas)
            for _ in range(B)]
    p, floor, nex = group_permutation_p(abs(obs), [abs(x) for x in null])
    declared_floor = p_floor(pr)
    if abs(floor - declared_floor) > 1e-8:
        raise Refusal("the realised permutation floor %r disagrees with the preregistered "
                      "attainable_p_floor %r" % (floor, declared_floor))
    k = sum(1 for x in deltas if x > float(0))
    ties = sum(1 for x in deltas if x == float(0))
    sp, sfloor = sign_test_two_sided(max(k, len(deltas) - k), len(deltas))
    return {"unit": unit, "n_domains": len(doms), "observed_delta": obs,
            "per_domain_delta": dict(zip(doms, deltas)),
            "permutation": {"p": p, "floor": floor, "n_exceed": nex, "n_perm": B,
                            "formatted": fmt_p(p, floor, nex)},
            "sign_test": {"k_positive": k, "n": len(deltas), "n_exact_ties": ties,
                          "p": sp, "floor": sfloor, "formatted": fmt_p(sp, sfloor)}}


def control_interval(deltas: Sequence[float], a: float) -> Dict[str, Any]:
    """A control is reported WITH ITS INTERVAL, never as a bare p > alpha.
    `_control_arms_are_not_members`: "a control that fails to reach significance is not thereby a
    passed control: each is reported with its interval"."""
    n = len(deltas)
    if n < 2:
        raise ZeroBinding("control interval over n<2 domains")
    m = sum(deltas) / n
    sd = math.sqrt(sum((x - m) ** 2 for x in deltas) / (n - 1))
    se = sd / math.sqrt(n)
    try:
        from scipy import stats as _st
        tcrit = float(_st.t.isf(a / float(2), n - 1))
    except Exception:                                       # pragma: no cover
        tcrit = float(196) / float(100)
    return {"n": n, "mean": m, "sd": sd, "se": se, "alpha": a,
            "ci_low": m - tcrit * se, "ci_high": m + tcrit * se,
            "_rule": "'p > alpha' is not a passed control; the interval is the result"}


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
    """S_B is the worked example: it is DECLARED, it CANNOT BE BUILT (neutral_content is 0 in
    6900/6900 prompts), and it enters at p = 1.0 rather than being quietly dropped."""
    ids = family_member_ids(pr)
    unknown = sorted(set(observed) - set(ids))
    if unknown:
        raise Refusal("p-values supplied for non-members %s of family %r" % (unknown, FAMILY_NAME))
    pv = {h: float(observed.get(h, 1.0)) for h in ids}
    res = holm(pv, alpha(pr), m=len(ids))
    res["absent_members_at_p1"] = sorted(set(ids) - set(observed))
    res["unconstructible_members"] = sorted(sid for sid, s in declared_scopes(pr).items()
                                            if s["unconstructible"] and sid in ids)
    return res


def refuse_shrunken_family(pr: Prereg, reported_member_ids: Sequence[str]) -> int:
    """A declared member reported as ABSENT rather than entering at p = 1.0 SHRINKS the family and
    makes every surviving member easier to declare significant. That is refused."""
    ids = set(family_member_ids(pr))
    missing = sorted(ids - set(reported_member_ids))
    if missing:
        raise Refusal(
            "family %r declares %d members but only %d were carried into the correction; %s "
            "would be DROPPED. `_absent_members_enter_at_p_1`: a declared member that could not "
            "be built enters at p = 1.0 and the report says so -- it is never omitted."
            % (FAMILY_NAME, len(ids), len(reported_member_ids), missing))
    return len(ids)


# ============================================================================================
# 12. INSTALLATION -- a STRATIFIER, never a post-hoc exclusion (mandate section 15)
# ============================================================================================
def stratify_by_installation(per_domain: Dict[str, float], install_prob: Dict[str, float],
                             cut: float) -> Dict[str, Any]:
    """Split the analysed domains into the two preregistered strata. NOTHING is dropped."""
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
            "n_non_installing": len(strata["non_installing"]), "strata": strata,
            "_rule": "POOLED over all analysed domains is the headline; both strata are reported "
                     "beside it; no row is dropped for failing to install"}


def refuse_installation_as_exclusion(dropped_domains: Sequence[str]) -> None:
    if dropped_domains:
        raise Refusal(
            "%d domain(s) were about to be dropped for failing to install: %s. Mandate section 15: "
            "installation is a STRATIFICATION variable and a descriptive limit, NEVER a post-hoc "
            "exclusion." % (len(dropped_domains), list(dropped_domains)[:5]))


def empty_installing_stratum_gate(stratified: Dict[str, Any], bank_key: str) -> Dict[str, Any]:
    """`primary.cannot_answer` (d): an empty installing stratum in a bank is CANNOT ANSWER."""
    empty = int(stratified["n_installing"]) == 0
    return {"bank": bank_key, "n_installing": stratified["n_installing"],
            "cannot_answer": empty,
            "reason": "" if not empty else
                      "the installing stratum is EMPTY in bank %r, so 'the knockout removed the "
                      "installed concept' has no installed concept to remove in this bank. That "
                      "is CANNOT ANSWER on power grounds, never a mechanism null." % bank_key}


# ============================================================================================
# 13. POWER -- U3 as a code path
# ============================================================================================
def u3_power(pr: Prereg, validation_per_domain_delta: Dict[str, float],
             n_for_decision: Optional[int] = None) -> Dict[str, Any]:
    """Measure the between-domain SD on VALIDATION DOMAINS ONLY, then decide BEFORE reading test.

    `power.mde.in_semantic_logodds_nats` is deliberately null in the frozen file, and
    `_honesty_statement` says why: the old ladder's magnitudes are DISPLAY-CHANNEL numbers on a
    38-domain bank and borrowing them would import exactly the instrument this phase removes. A
    value pre-filled there is therefore a REFUSAL rather than a convenience.
    """
    if pr.require("power", "mde", "in_semantic_logodds_nats") is not None:
        raise Refusal("power.mde.in_semantic_logodds_nats is no longer null in the frozen file. U3 "
                      "MEASURES it; a value pre-filled there would be the borrowed "
                      "display-channel number the file refuses to carry.")
    vals = list(validation_per_domain_delta.values())
    if len(vals) < 2:
        raise ZeroBinding("U3 measured the SD over %d validation domain(s)" % len(vals))
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


def mde_in_sd_units_check(pr: Prereg) -> Dict[str, Any]:
    """The frozen file's own SD-unit MDEs re-derived from its own formula, so a typo in either is
    visible. `mde_formula` = (z_{1-alpha/2} + z_{1-beta}) / sqrt(n)."""
    try:
        from scipy import stats as _st
        z = float(_st.norm.isf(alpha(pr) / float(2))) + float(_st.norm.isf(float(1) - power_bar(pr)))
    except Exception:                                       # pragma: no cover
        raise Refusal("scipy is unavailable, so the declared MDE formula cannot be re-derived")
    got = {}
    for key, val in pr.require("power", "mde", "in_sd_units").items():
        m = re.search(r"n_(\d+)", str(key))
        if not m:
            continue
        n = int(m.group(1))
        got[key] = {"declared": float(val), "derived": z / math.sqrt(n),
                    "agrees": abs(float(val) - z / math.sqrt(n)) < 1e-4}
    if not got:
        raise ZeroBinding("power.mde.in_sd_units declares no n-keyed entries")
    bad = [k for k, v in got.items() if not v["agrees"]]
    return {"z_sum": z, "per_n": got, "ok": not bad, "disagreeing": bad}


# ============================================================================================
# 14. KILL CONDITIONS -- code paths, evaluated IN ORDER, before the narrow scopes are read
# ============================================================================================
def kill_baseline_channel(pr: Prereg, baseline_readout: Optional[ArmReadout]) -> Dict[str, Any]:
    """Kill 2: if median `option_mass` in the S_0 BASELINE falls below the gate on this
    population, NO knockout job is submitted at all."""
    if baseline_readout is None:
        return {"killed": False, "evaluated": False,
                "reason": "the untouched baseline arm has not been scored, so the baseline "
                          "engagement kill condition is UNEVALUATED and is reported as such "
                          "rather than as passed"}
    g = engagement_gate(baseline_readout, pr)
    return {"killed": bool(g["cannot_answer"]), "evaluated": True, "detail": g,
            "reason": g["reason"] or ""}


def kill_reference_scope(pr: Prereg, reference_moved: Optional[bool]) -> Dict[str, Any]:
    """Kill 1: if the WHOLE QUERY SPAN does not move the readout at the domain level, NO NARROWER
    SCOPE IS SUBMITTED. Running six narrower cuts to find nothing would be six chances to report a
    null that is really a dead intervention."""
    sid = reference_scope_id(pr)
    if reference_moved is None:
        return {"scope": sid, "killed": False, "evaluated": False,
                "reason": "%s has not been read, so the first kill condition is UNEVALUATED and "
                          "is reported as such rather than as passed" % sid}
    return {"scope": sid, "killed": not reference_moved, "evaluated": True,
            "reason": "" if reference_moved else
                      "%s (the whole query span) does not move the %s readout at the domain "
                      "level. There is nothing to localise, so no narrower scope is submitted. "
                      "Check hook liveness, the realised dose, the eager record and the "
                      "disabled-hook bridge: this is VOID or a kill, NOT a localisation negative."
                      % (sid, primary_channel(pr))}


def kill_scaffold_moved(pr: Prereg, scaffold_moved: Optional[bool]) -> Dict[str, Any]:
    """Kill 3: if the SCAFFOLD-ONLY arm MOVES the readout, the whole family is VOID until the
    cause is found. Scaffold rows carry ZERO query content -- confirmed against the token-role map
    in every prompt -- so a scaffold-only effect means the arms differ by something the design
    does not know about."""
    sid = scaffold_scope_id(pr)
    if scaffold_moved is None:
        return {"scope": sid, "killed": False, "evaluated": False,
                "reason": "%s has not been read, so the scaffold-null kill condition is "
                          "UNEVALUATED and is reported as such rather than as passed" % sid}
    return {"scope": sid, "killed": bool(scaffold_moved), "evaluated": True,
            "reason": "" if not scaffold_moved else
                      "the scaffold-only scope %s MOVES the readout. Its rows are chat scaffold "
                      "and response header and carry no query content, so the arms differ by "
                      "something this design does not know about. THE WHOLE FAMILY IS VOID until "
                      "the cause is found." % sid}


def gate_narrow_scopes(kill_reference: Dict[str, Any]) -> None:
    """The kill condition is evaluated BEFORE the narrow scopes are read -- as control flow, not
    as a paragraph. Calling this before reading a narrower scope is how the ordering is enforced."""
    if not kill_reference.get("evaluated"):
        raise Refusal(
            "REFUSING to read any narrower scope: the reference-scope kill condition has not been "
            "EVALUATED. The frozen file fixes the order -- %s and the baseline are submitted "
            "first and read first -- and an analyzer that reads the narrow scopes anyway has "
            "quietly removed the kill condition." % kill_reference.get("scope"))
    if kill_reference.get("killed"):
        raise Refusal(
            "REFUSING to read any narrower scope: %s" % kill_reference.get("reason"))


# ============================================================================================
# 15. THE FRACTION-OF-REFERENCE RULE, THE CONJUNCTIVE SUCCESS RULE, AND THE VERDICT
# ============================================================================================
def fraction_of_reference(pr: Prereg, delta_scope: float, delta_reference: float
                          ) -> Dict[str, Any]:
    """`|delta_scope| >= rule x |delta_reference|`, the rule inherited verbatim from the design
    being replaced. Every narrower scope's effect is reported as a FRACTION of the reference."""
    rule = half_of_reference_rule(pr)
    if float(delta_reference) == float(0):
        raise Refusal(
            "the reference scope's effect is exactly 0, so a fraction of it is undefined. If the "
            "reference does not move there is nothing to localise and the kill condition, not a "
            "fraction, is what applies.")
    frac = abs(float(delta_scope)) / abs(float(delta_reference))
    return {"delta_scope": float(delta_scope), "delta_reference": float(delta_reference),
            "fraction": frac, "rule": rule, "reproduces": frac >= rule,
            "same_sign": (delta_scope > float(0)) == (delta_reference > float(0))}


def success_conditions(pr: Prereg) -> List[str]:
    conds = pr.require("primary", "success", "conditions")
    if len(conds) < 2:
        raise Refusal("primary.success.conditions declares %d condition(s); the rule is declared "
                      "CONJUNCTIVE and cannot be evaluated from one" % len(conds))
    return [str(c) for c in conds]


# ---- PR059-D7 (a): EACH CONJUNCT AGAINST **ITS OWN** PREREGISTERED EXPECTED SIGN ------------
#
# PHASE 9 shipped `evaluate_success(..., expected_sign=o2["expected_sign"])` -- ONE scalar,
# applied to two conjuncts whose preregistered directions are OPPOSITE -- and printed a
# correct O1 as `[FAIL] 1_probe_moves_intended` for two days
# (`reports/DCS_TS_PHASE9_VERDICT_REVIEW.md`, finding 1, SERIOUS).
#
# The defence here is structural, not a comment. There is NO scalar to share: the signs arrive
# as a MAP KEYED BY CONJUNCT, every entry carries the id of the conjunct it belongs to, and
# `evaluate_success` checks that self-label against the key it looked the entry up by. Swapping
# two conjuncts' expectations is therefore caught BY NAME, and handing the function a bare
# scalar is a refusal.
CONJUNCT_IDS = (
    "1_reference_scope_moves_in_the_expected_direction",
    "2_a_narrower_scope_reproduces_the_declared_fraction",
    "3_that_scopes_OWN_random_row_control_does_NOT_reproduce",
    "4_the_scaffold_only_scope_is_NULL",
)

#: The verdict CLASSES. They are kept apart on purpose: VOID ("the instrument did not do what it
#: claims"), CANNOT_ANSWER ("the design could not address it") and NEGATIVE ("it addressed it and
#: the answer is no") are three different statements about the world, and collapsing any two of
#: them is the single most damaging thing this analyzer could do.
VERDICT_CLASSES = ("VOID", "CANNOT_ANSWER", "POSITIVE", "NEGATIVE", "NO_VERDICT")

#: `primary.void` clause -> the evidence key that decides it. The clause text is read from the
#: FROZEN file and matched against these patterns; a clause matching NONE of them is a refusal,
#: so a void clause added to the design can never be silently skipped by this walk.
VOID_CLAUSE_KEYS = (
    ("attn_implementation", "eager_on_loaded_config"),
    ("hook_fired_count", "hook_fired"),
    ("n_decode_edits", "no_decode_leak"),
    ("realised != expected cell count", "realised_equals_expected_cells"),
    ("realised row set", "realised_row_set_equals_declared"),
    ("disabled-hook bridge", "bridge_reproduces_baseline"),
    ("identical output hashes", "control_draws_distinct"),
    ("absolute index", "no_absolute_index"),
    ("row-level p-value", "no_row_level_p"),
    ("unequal per-arm populations", "equal_populations"),
)

#: `primary.cannot_answer` clause -> the evidence key that decides it. Same rule: an unmatched
#: clause refuses.
CANNOT_ANSWER_CLAUSE_KEYS = (
    ("option_mass", "option_mass_above_gate"),
    ("realised power", "power_at_or_above_bar"),
    ("resolver fails", "resolver_within_tolerance"),
    ("installation stratification", "installing_stratum_non_empty"),
)


def _sgn(x) -> int:
    return 0 if float(x) == float(0) else (1 if float(x) > float(0) else -1)


def o1_expected_sign(pr: Prereg) -> Dict[str, Any]:
    """O1's OWN preregistered direction, PARSED OUT OF THE FROZEN FILE -- never chosen here.

    The frozen file does not carry a machine-readable `direction_expected` for O1; it states the
    direction in prose, twice, in two different sections, both as "a knockout predicted to LOWER
    the installed reading". BOTH statements are read and they must AGREE. Zero statements, or two
    that disagree, is a REFUSAL -- not a default, and not a sign this analyzer picks for itself.
    Hardcoding `-1` here would be the analyzer choosing the direction of its own primary conjunct
    after the design was frozen.
    """
    obj = getattr(pr, "obj", None)
    if not isinstance(obj, dict):
        raise Refusal("the preregistration exposes no object to parse the expected direction "
                      "from; O1's sign may not be assumed")
    lower_pat = "knockout predicted to lower"
    raise_pat = "knockout predicted to raise"
    hits: List[Dict[str, Any]] = []

    def _walk(node, path):
        if isinstance(node, dict):
            for k, v in node.items():
                _walk(v, "%s.%s" % (path, k))
        elif isinstance(node, list):
            for i, v in enumerate(node):
                _walk(v, "%s[%d]" % (path, i))
        elif isinstance(node, str):
            low = node.lower()
            if lower_pat in low:
                hits.append({"path": path, "sign": -1, "quote": node.strip()[:160]})
            elif raise_pat in low:
                hits.append({"path": path, "sign": 1, "quote": node.strip()[:160]})

    _walk(obj, "")
    if not hits:
        raise Refusal(
            "the frozen preregistration states NO expected direction for O1 anywhere. "
            "`primary.success.conditions[0]` requires the reference scope to move 'in the "
            "EXPECTED direction', and this analyzer REFUSES to supply the expectation itself: "
            "an analyzer that picks the direction of its own primary conjunct after freeze has "
            "removed the conjunct.")
    signs = sorted({h["sign"] for h in hits})
    if len(signs) != 1:
        raise Refusal(
            "the frozen preregistration states CONTRADICTORY expected directions for O1: %s. "
            "A conjunct cannot be scored against two opposite expectations."
            % [(h["path"], h["sign"]) for h in hits])
    return {"outcome": "O1_semantic_readout", "sign": signs[0], "n_statements": len(hits),
            "sources": hits,
            "_meaning": "the demonstration->query knockout is preregistered to LOWER the "
                        "installed semantic reading, so a delta with sign %+d is the EXPECTED "
                        "direction and a delta with sign %+d is a movement the design did not "
                        "predict" % (signs[0], -signs[0])}


def conjunct_expected_signs(pr: Prereg) -> "OrderedDict[str, Dict[str, Any]]":
    """Each conjunct's OWN expectation, keyed by conjunct, each carrying its own id.

    They are NOT the same expectation and there is no scalar that could serve all four:

      conjunct 1  a FIXED sign -- O1's preregistered direction, parsed from the frozen file.
      conjunct 2  SAME AS THE REFERENCE'S OBSERVED sign. "Reproduces a fraction of the S_G
                  effect" is a statement about agreement with the DENOMINATOR, not about O1's
                  absolute direction, and it is not knowable before the run. Scoring it against
                  conjunct 1's fixed sign is EXACTLY the PHASE 9 defect.
      conjunct 3  EXPECTED NULL. A control's preregistered expectation is that it does NOT
                  reproduce; it has no direction to match.
      conjunct 4  EXPECTED NULL. `S_A` is a null by design; a scaffold-only arm that moves in
                  the "expected" direction is not a pass, it is the family being VOID (kill 3).
    """
    o1 = o1_expected_sign(pr)
    conds = success_conditions(pr)
    out: "OrderedDict[str, Dict[str, Any]]" = OrderedDict()
    out[CONJUNCT_IDS[0]] = {
        "conjunct": CONJUNCT_IDS[0], "kind": "fixed_sign", "sign": int(o1["sign"]),
        "outcome": "O1_semantic_readout", "condition_text": conds[0],
        "source": o1["sources"]}
    out[CONJUNCT_IDS[1]] = {
        "conjunct": CONJUNCT_IDS[1], "kind": "same_sign_as_reference", "sign": None,
        "outcome": "fraction of the reference scope's OWN observed effect",
        "condition_text": conds[1],
        "source": "primary.success.half_of_S_G_rule + fraction_of_reference().same_sign"}
    out[CONJUNCT_IDS[2]] = {
        "conjunct": CONJUNCT_IDS[2], "kind": "expected_null", "sign": 0,
        "outcome": "the scope's OWN dose-matched random-row control",
        "condition_text": conds[2], "source": "nulls_required L-N7"}
    out[CONJUNCT_IDS[3]] = {
        "conjunct": CONJUNCT_IDS[3], "kind": "expected_null", "sign": 0,
        "outcome": "the scaffold-only scope %s" % scaffold_scope_id(pr),
        "condition_text": conds[3], "source": "nulls_required L-N5 + kill_condition (third)"}
    return out


def assert_conjunct_signs_are_their_own(signs: Any) -> "OrderedDict[str, Dict[str, Any]]":
    """The structural defence against the PHASE 9 defect. Called by `evaluate_success`."""
    if not isinstance(signs, dict):
        raise Refusal(
            "evaluate_success was handed a SINGLE expected sign (%r) to score ALL FOUR conjuncts "
            "against. That is the PHASE 9 defect verbatim: one outcome's preregistered direction "
            "applied to another outcome's test, which mislabelled a correct result as FAIL for "
            "two days. Each conjunct is scored against ITS OWN expectation or not at all."
            % (signs,))
    missing = [c for c in CONJUNCT_IDS if c not in signs]
    if missing:
        raise Refusal("the per-conjunct expected signs are missing %s" % missing)
    for cid in CONJUNCT_IDS:
        got = signs[cid].get("conjunct")
        if got != cid:
            raise Refusal(
                "conjunct %r was handed the expectation preregistered for %r. The two conjuncts "
                "do not share a direction -- %r is scored against %s and %r against %s -- and "
                "applying one to the other is how PHASE 9 printed a correct outcome as FAIL."
                % (cid, got, cid, signs[cid].get("kind"), got,
                   signs.get(got, {}).get("kind") if got in signs else "(unknown)"))
    return signs


def control_status_for_scope(pr: Prereg, scope_id: str, control_ok: Any,
                             span: Optional[Sequence[int]] = None) -> Dict[str, Any]:
    """Conjunct 3 for ONE scope: PASS / FAIL / **UNEVALUABLE**.

    `PR059-D1`: for `S_D` (m=22), `S_E` (m=23) and the reference `S_G` (m=28) the dose-matched
    random-row control needs an m-row draw from a pool of `28 - m` and therefore DOES NOT EXIST.
    Those scopes are DEMOTED: they still run, they are still reported, and they still enter Holm
    at their own p -- but conjunct 3 has no value for them.

    UNEVALUABLE IS NOT A PASS. `primary.success._conjunctive_on_purpose` says "any three of four
    is not a localisation result", and an unevaluable condition is a HOLE IN THE VALIDITY
    ARGUMENT, not a satisfied one (the lesson PHASE 9's C5 clause taught). A scope in this state
    can never contribute a POSITIVE; it forces CANNOT ANSWER.
    """
    scopes = declared_scopes(pr)
    if scope_id not in scopes:
        raise Refusal("conjunct 3 was asked about scope %r, which this design does not declare"
                      % scope_id)
    sp = list(span) if span is not None else query_span_rel_end(pr)
    con = random_row_control_constructible(pr, scope_id, scopes[scope_id]["rel_end_rows"], sp)
    if not con["constructible"]:
        return {"scope": scope_id, "status": "UNEVALUABLE", "passed": False,
                "constructible": False,
                "reason": "PR059-D1: the dose-matched random-row control for %s is NOT "
                          "CONSTRUCTIBLE (%s). Success condition 3 has NO VALUE for this scope. "
                          "It is reported as UNEVALUABLE and it REFUSES a verdict for this "
                          "scope -- an unevaluable condition is a hole in the validity argument, "
                          "never a satisfied one."
                          % (scope_id, con.get("reason", "").strip() or "empty draw pool")}
    if control_ok is None:
        return {"scope": scope_id, "status": "UNEVALUATED", "passed": False,
                "constructible": True,
                "reason": "the control for %s IS constructible but has not been read; that is "
                          "UNEVALUATED, and it is reported as such rather than as passed"
                          % scope_id}
    ok = bool(control_ok)
    return {"scope": scope_id, "status": "PASS" if ok else "FAIL", "passed": ok,
            "constructible": True,
            "reason": "" if ok else
                      "the dose-matched random-row control for %s REPRODUCED the scope's effect, "
                      "so the effect is a property of cutting m rows and not of cutting THESE "
                      "rows" % scope_id}


def evaluate_success(pr: Prereg, reference_moved: bool,
                     reproducing: Sequence[Tuple[str, Dict[str, Any]]],
                     holm_res: Dict[str, Any],
                     control_ok_by_scope: Dict[str, Any],
                     scaffold_null: bool,
                     expected_signs: Optional[Dict[str, Any]] = None,
                     reference_delta: Optional[float] = None,
                     scaffold_delta: Optional[float] = None) -> Dict[str, Any]:
    """All four conditions TOGETHER, EACH SCORED AGAINST ITS OWN PREREGISTERED EXPECTATION.

    `primary.success._conjunctive_on_purpose`: "Any three of four is not a localisation result."
    """
    conds = success_conditions(pr)
    signs = assert_conjunct_signs_are_their_own(
        conjunct_expected_signs(pr) if expected_signs is None else expected_signs)
    rej = holm_res["per_member"]

    # ---- conjunct 1 -- O1's OWN fixed direction --------------------------------------------
    s1 = signs[CONJUNCT_IDS[0]]
    c1_pass = bool(reference_moved)
    c1_detail = "reference scope %s moved=%s" % (reference_scope_id(pr), reference_moved)
    if reference_delta is not None:
        got = _sgn(reference_delta)
        c1_pass = bool(reference_moved) and got == int(s1["sign"])
        c1_detail = ("reference scope %s delta=%.6g sign=%+d; O1's OWN preregistered expected "
                     "sign is %+d (parsed from the frozen file, not chosen here)"
                     % (reference_scope_id(pr), float(reference_delta), got, int(s1["sign"])))

    # ---- conjunct 2 -- agreement with the REFERENCE, not with O1's absolute sign ------------
    winners = [sid for sid, fr in reproducing
               if fr.get("reproduces") and fr.get("same_sign", True)
               and rej.get(sid, {}).get("reject", False)]

    # ---- conjunct 3 -- each winner's OWN control, with UNEVALUABLE kept distinct ------------
    span = query_span_rel_end(pr)
    c3_rows = [control_status_for_scope(pr, s, (control_ok_by_scope or {}).get(s), span)
               for s in winners]
    c3_unevaluable = [r["scope"] for r in c3_rows if r["status"] == "UNEVALUABLE"]
    c3_unevaluated = [r["scope"] for r in c3_rows if r["status"] == "UNEVALUATED"]
    c3_pass = bool(winners) and all(r["status"] == "PASS" for r in c3_rows)

    # ---- conjunct 4 -- EXPECTED NULL; a scaffold arm that "moves as expected" is VOID -------
    c4_pass = bool(scaffold_null)
    c4_detail = "scaffold-only scope %s is null=%s" % (scaffold_scope_id(pr), scaffold_null)
    if scaffold_delta is not None:
        c4_detail += " (delta=%.6g; the preregistered expectation is a NULL, so there is no "
        c4_detail = (c4_detail % float(scaffold_delta)) + \
            "direction for it to match -- movement in EITHER direction fails this conjunct)"

    rows = [
        {"conjunct": CONJUNCT_IDS[0], "condition": conds[0], "passed": c1_pass,
         "status": "PASS" if c1_pass else "FAIL",
         "expected": signs[CONJUNCT_IDS[0]]["kind"],
         "expected_sign": signs[CONJUNCT_IDS[0]]["sign"], "detail": c1_detail},
        {"conjunct": CONJUNCT_IDS[1], "condition": conds[1], "passed": bool(winners),
         "status": "PASS" if winners else "FAIL",
         "expected": signs[CONJUNCT_IDS[1]]["kind"],
         "expected_sign": signs[CONJUNCT_IDS[1]]["sign"],
         "detail": "scopes reaching the declared fraction WITH THE REFERENCE'S OWN SIGN and "
                   "surviving Holm: %s" % winners},
        {"conjunct": CONJUNCT_IDS[2], "condition": conds[2], "passed": c3_pass,
         "status": ("UNEVALUABLE" if c3_unevaluable else
                    "UNEVALUATED" if c3_unevaluated else
                    "PASS" if c3_pass else "FAIL"),
         "expected": signs[CONJUNCT_IDS[2]]["kind"],
         "expected_sign": signs[CONJUNCT_IDS[2]]["sign"],
         "per_scope": c3_rows,
         "detail": "dose-matched random-row control, per winning scope: %s"
                   % {r["scope"]: r["status"] for r in c3_rows}},
        {"conjunct": CONJUNCT_IDS[3], "condition": conds[3], "passed": c4_pass,
         "status": "PASS" if c4_pass else "FAIL",
         "expected": signs[CONJUNCT_IDS[3]]["kind"],
         "expected_sign": signs[CONJUNCT_IDS[3]]["sign"], "detail": c4_detail},
    ]
    n_pass = sum(1 for r in rows if r["passed"])
    ca: List[str] = []
    for s in c3_unevaluable:
        ca.append("scope %s reached the declared fraction but its dose-matched random-row "
                  "control is NOT CONSTRUCTIBLE (PR059-D1), so success condition 3 is "
                  "UNEVALUABLE for it. A conjunctive rule with an unevaluable conjunct returns "
                  "CANNOT ANSWER, never a positive and never a null" % s)
    for s in c3_unevaluated:
        ca.append("scope %s reached the declared fraction and its control IS constructible but "
                  "was not read; condition 3 is UNEVALUATED and is not assumed to pass" % s)
    return {"conditions": rows, "n_conditions": len(rows), "n_passed": n_pass,
            "winners": winners, "success": n_pass == len(rows),
            "unevaluable_scopes": c3_unevaluable, "unevaluated_scopes": c3_unevaluated,
            "cannot_answer_reasons": ca,
            "_expected_signs": {c: signs[c]["sign"] for c in CONJUNCT_IDS},
            "_expected_kinds": {c: signs[c]["kind"] for c in CONJUNCT_IDS},
            "_conjunctive": "all %d are required TOGETHER; %d of %d is not a localisation result"
                            % (len(rows), n_pass, len(rows))}


# ---- PR059-D7 (b): EVERY `void` AND `cannot_answer` CLAUSE WALKED, EACH WITH A STATUS -------
def _split_clauses(text: str) -> List[str]:
    return [c.strip(" .") for c in str(text).split(";") if c.strip(" .")]


def _clause_walk(clauses: Sequence[str], table: Sequence[Tuple[str, str]],
                 evidence: Dict[str, Any], what: str) -> Dict[str, Any]:
    rows = []
    for c in clauses:
        low = c.lower()
        key = next((k for pat, k in table if pat.lower() in low), None)
        if key is None:
            raise Refusal(
                "`primary.%s` carries the clause %r and this analyzer has NO evidence key for "
                "it. A clause the walk cannot decide must not be walked past: it would be a "
                "declared way for this phase to be %s that nothing ever checks." % (what, c, what))
        if key not in (evidence or {}):
            rows.append({"clause": c, "key": key, "status": "UNEVALUATED", "triggered": False})
        else:
            ok = bool(evidence[key])
            rows.append({"clause": c, "key": key,
                         "status": "CLEAN" if ok else what.upper(), "triggered": not ok})
    return {"what": what, "clauses": rows, "n": len(rows),
            "n_triggered": sum(1 for r in rows if r["triggered"]),
            "n_unevaluated": sum(1 for r in rows if r["status"] == "UNEVALUATED"),
            "triggered": [r["clause"] for r in rows if r["triggered"]],
            "clean": all(r["status"] == "CLEAN" for r in rows)}


def void_walk(pr: Prereg, evidence: Dict[str, Any]) -> Dict[str, Any]:
    """Every clause of `primary.void`, each with a status. UNEVALUATED is NOT clean."""
    return _clause_walk(_split_clauses(pr.require("primary", "void")),
                        VOID_CLAUSE_KEYS, evidence, "void")


def cannot_answer_walk(pr: Prereg, evidence: Dict[str, Any]) -> Dict[str, Any]:
    """Every clause of `primary.cannot_answer`, each with a status."""
    return _clause_walk(_split_clauses(pr.require("primary", "cannot_answer")),
                        CANNOT_ANSWER_CLAUSE_KEYS, evidence, "cannot_answer")


# ---- PR059-D7 (c): THE VERDICT, WITH A CLASS THAT CANNOT COLLAPSE --------------------------
def verdict_record(pr: Prereg, success: Dict[str, Any], liveness_clean: bool,
                   cannot_answer_reasons: Sequence[str], reference_moved: bool,
                   forbidden: Sequence[str]) -> Dict[str, Any]:
    """The verdict AND its CLASS. `verdict()` is this, reduced to its sentence."""
    reasons = list(cannot_answer_reasons or []) + list(success.get("cannot_answer_reasons") or [])
    if not liveness_clean:
        return {"class": "VOID", "sentence": None, "refuses": True, "reasons": reasons,
                "reason": "hook liveness is UNCLEAN. A dead hook, an SDPA arm, a leaked decode "
                          "edit, a zero realised dose or a realised row set differing from the "
                          "declared one produces EXACTLY the artifact a real intervention with "
                          "no effect produces. That is VOID, not a negative."}
    if reasons:
        return {"class": "CANNOT_ANSWER", "refuses": False, "reasons": reasons,
                "sentence": assert_sayable(
                    "CANNOT ANSWER -- %s. This is reported as CANNOT ANSWER and explicitly NOT "
                    "as a mechanism null." % "; ".join(reasons), forbidden)}
    if not reference_moved:
        return {"class": "VOID", "sentence": None, "refuses": True, "reasons": reasons,
                "reason": "the reference scope did not move. `primary.negative."
                          "_the_other_negative`: the intervention did not do what it claims -- "
                          "check liveness, dose, the eager record and the disabled-hook bridge. "
                          "That is VOID or a kill, NOT a localisation negative."}
    if success.get("success"):
        return {"class": "POSITIVE", "refuses": False, "reasons": reasons,
                "sentence": assert_sayable(
                    "POSITIVE -- all %d conjunctive conditions passed; the reproducing scope(s) "
                    "are %s. Scope of the claim: this intervention, this band, this bank, this "
                    "channel, Llama-3.1-8B-Instruct only, one query template."
                    % (success.get("n_conditions", 0), success.get("winners")), forbidden)}
    if not success.get("winners"):
        # THE MANDATED WORDING, EMITTED AS A LITERAL. `check_wording_pin` returns the pinned
        # constant only after asserting it still equals the frozen file's MANDATORY_WORDING
        # word for word; nothing here paraphrases it or appends to it.
        return {"class": "NEGATIVE", "refuses": False, "reasons": reasons,
                "sentence": assert_sayable(check_wording_pin(pr), forbidden)}
    return {"class": "NO_VERDICT", "refuses": False, "reasons": reasons,
            "sentence": assert_sayable(
                "NO VERDICT -- %d of %d conjunctive conditions passed. A scope reached the "
                "declared fraction but at least one other required condition did not hold, and "
                "the declared negative's precondition (no narrower scope reaches the fraction) "
                "is not met either."
                % (success.get("n_passed", 0), success.get("n_conditions", 0)), forbidden)}


def verdict(pr: Prereg, success: Dict[str, Any], liveness_clean: bool,
            cannot_answer_reasons: Sequence[str], reference_moved: bool,
            forbidden: Sequence[str]) -> str:
    """The verdict SENTENCE. REFUSES on unclean liveness before it can produce any outcome."""
    rec = verdict_record(pr, success, liveness_clean, cannot_answer_reasons, reference_moved,
                         forbidden)
    if rec["class"] not in VERDICT_CLASSES:
        raise Refusal("verdict class %r is not one of the declared %s"
                      % (rec["class"], list(VERDICT_CLASSES)))
    if rec.get("refuses"):
        raise Refusal("REFUSING to emit any verdict: %s" % rec["reason"])
    return rec["sentence"]
def verdict(pr: Prereg, success: Dict[str, Any], liveness_clean: bool,
            cannot_answer_reasons: Sequence[str], reference_moved: bool,
            forbidden: Sequence[str]) -> str:
    """The verdict. REFUSES on unclean liveness before it can produce any outcome at all."""
    if not liveness_clean:
        raise Refusal(
            "REFUSING to emit any verdict: hook liveness is UNCLEAN. A dead hook, an SDPA arm, a "
            "leaked decode edit, a zero realised dose or a realised row set differing from the "
            "declared one produces EXACTLY the artifact a real intervention with no effect "
            "produces. That is VOID, not a negative, and a verdict here would be the strongest "
            "possible wrong answer.")
    if cannot_answer_reasons:
        return assert_sayable(
            "CANNOT ANSWER -- %s. This is reported as CANNOT ANSWER and explicitly NOT as a "
            "mechanism null." % "; ".join(cannot_answer_reasons), forbidden)
    if not reference_moved:
        raise Refusal(
            "the reference scope did not move. `primary.negative._the_other_negative`: the "
            "intervention did not do what it claims -- check liveness, dose, the eager record and "
            "the disabled-hook bridge. That is VOID or a kill, NOT a localisation negative.")
    if success.get("success"):
        return assert_sayable(
            "POSITIVE -- all %d conjunctive conditions passed; the reproducing scope(s) are %s. "
            "Scope of the claim: this intervention, this band, this bank, this channel, "
            "Llama-3.1-8B-Instruct only, one query template."
            % (success.get("n_conditions", 0), success.get("winners")), forbidden)
    if not success.get("winners"):
        return assert_sayable(check_wording_pin(pr), forbidden)
    return assert_sayable(
        "NO VERDICT -- %d of %d conjunctive conditions passed. A scope reached the declared "
        "fraction but at least one other required condition did not hold, and the declared "
        "negative's precondition (no narrower scope reaches the fraction) is not met either."
        % (success.get("n_passed", 0), success.get("n_conditions", 0)), forbidden)


# ============================================================================================
# 16. U4 -- EVERY DECLARED SCOPE RE-RESOLVED AGAINST THE FROZEN TOKEN-ROLE ARTIFACT
# ============================================================================================
def load_token_map(path: str = TOKEN_MAP_DEFAULT) -> Dict[str, Any]:
    fp = path if os.path.isabs(path) else os.path.join(REPO, path)
    if not os.path.exists(fp):
        raise Refusal("the frozen token-role artifact %r is absent. Every scope in this phase is "
                      "a set of rel_end offsets READ OFF THAT MAP; without it the scopes are "
                      "unverifiable and nothing may be claimed about which tokens were cut." % path)
    with gzip.open(fp, "rt") as f:
        obj = json.load(f)
    if not obj.get("records"):
        raise ZeroBinding("the token-role artifact carries ZERO records")
    return obj


def verify_scopes_against_token_map(pr: Prereg, tm: Dict[str, Any]) -> Dict[str, Any]:
    """Checklist U4. For EVERY prompt in the frozen map and EVERY declared scope, re-resolve the
    scope's rel_end set to a role and a decoded token, and compare with what the config says.

    This is the check the whole phase exists to provide: "a scope whose realised rows are not what
    this file says they are is the defect this whole phase exists to fix". Nothing is imported
    from the design's own summary -- the roles are re-derived from the per-prompt `query_roles`
    arrays and counted.
    """
    recs = tm["records"]
    scopes = declared_scopes(pr)
    layout = layout_roles(pr)
    span = query_span_rel_end(pr)
    census_declared = {k: v for k, v in
                       pr.require("token_map", "query_role_census_constant_in_6900_of_6900").items()
                       if not k.startswith("_")}

    per_scope = {sid: {"roles": {}, "decoded": {}, "n_prompts": 0, "n_out_of_span": 0}
                 for sid in scopes}
    layout_mismatch = OrderedDict()
    census_seen = OrderedDict()
    n_span_wrong = 0
    n_neutral = 0
    n_last_k_equals_scaffold = 0
    scaffold_id = scaffold_scope_id(pr)
    scaffold_rows = scopes[scaffold_id]["rel_end_rows"]

    for r in recs:
        n = int(r["n_tokens"])
        qs = int(r["query_role_start"])
        roles = list(r["query_roles"])
        toks = list(r["tokens"])
        if len(roles) != n - qs:
            raise Refusal("a token-map record's query_roles length %d disagrees with its own "
                          "query span %d; the artifact is internally inconsistent"
                          % (len(roles), n - qs))
        role_at = {qs + i - n: roles[i] for i in range(len(roles))}
        if sorted(role_at) != span:
            n_span_wrong += 1
        c: Dict[str, int] = {}
        for role in roles:
            c[role] = c.get(role, 0) + 1
        census_seen[json.dumps(c, sort_keys=True)] = census_seen.get(
            json.dumps(c, sort_keys=True), 0) + 1
        n_neutral += c.get("neutral_content", 0)
        if set(sorted(range(qs, n))[-len(scaffold_rows):]) == set(n + o for o in scaffold_rows):
            n_last_k_equals_scaffold += 1
        for sid, s in scopes.items():
            rows = s["rel_end_rows"]
            if not rows:
                continue
            per_scope[sid]["n_prompts"] += 1
            for o in rows:
                role = role_at.get(o)
                if role is None:
                    per_scope[sid]["n_out_of_span"] += 1
                    continue
                per_scope[sid]["roles"][role] = per_scope[sid]["roles"].get(role, 0) + 1
                if len(rows) == 1:
                    t = toks[n + o]
                    per_scope[sid]["decoded"][t] = per_scope[sid]["decoded"].get(t, 0) + 1
                want = layout.get(o)
                if want is not None and want != role:
                    k = "rel_end %d: layout says %s, artifact says %s" % (o, want, role)
                    layout_mismatch[k] = layout_mismatch.get(k, 0) + 1

    n = len(recs)
    census_ok = len(census_seen) == 1
    seen_census = json.loads(next(iter(census_seen))) if census_seen else {}
    census_agrees = all(int(seen_census.get(k, 0)) == int(v)
                        for k, v in census_declared.items() if isinstance(v, int))
    out = {
        "n_prompts": n,
        "query_span_rel_end": [min(span), max(span)], "n_query_side_tokens": len(span),
        "n_prompts_whose_span_differs": n_span_wrong,
        "role_census_constant": census_ok,
        "role_census_observed": seen_census,
        "role_census_declared": census_declared,
        "role_census_agrees_with_config": bool(census_agrees),
        "n_neutral_content_tokens_total": n_neutral,
        "S_B_is_genuinely_empty": n_neutral == 0,
        "last_k_equals_scaffold_scope": {"scope": scaffold_id, "K": len(scaffold_rows),
                                         "n_matching": n_last_k_equals_scaffold, "n_prompts": n},
        "layout_mismatches": dict(layout_mismatch),
        "per_scope": {sid: {"n_rows": scopes[sid]["n_rows"],
                            "rel_end_rows": scopes[sid]["rel_end_rows"],
                            "roles": dict(sorted(v["roles"].items())),
                            "roles_per_prompt": {k: (float(x) / float(n)) for k, x in
                                                 sorted(v["roles"].items())} if n else {},
                            "decoded": dict(sorted(v["decoded"].items(), key=lambda kv: -kv[1])),
                            "n_out_of_span": v["n_out_of_span"],
                            "unconstructible": scopes[sid]["unconstructible"]}
                      for sid, v in per_scope.items()},
    }
    problems = []
    if n_span_wrong:
        problems.append("%d/%d prompts have a query span differing from the declared layout"
                        % (n_span_wrong, n))
    if not census_ok:
        problems.append("the query role census is NOT constant: %d distinct censuses observed"
                        % len(census_seen))
    if not census_agrees:
        problems.append("the observed role census disagrees with token_map."
                        "query_role_census_constant_in_6900_of_6900")
    if layout_mismatch:
        problems.append("the config's rel_end_layout disagrees with the artifact at %d offset(s)"
                        % len(layout_mismatch))
    if any(v["n_out_of_span"] for v in per_scope.values()):
        problems.append("a declared scope resolves outside the query span in some prompts")
    if n_last_k_equals_scaffold != n:
        problems.append("query_last_k_rows K=%d equals the scaffold scope in only %d/%d prompts"
                        % (len(scaffold_rows), n_last_k_equals_scaffold, n))
    for sid, s in scopes.items():
        if s["unconstructible"] and s["rel_end_rows"]:
            problems.append("scope %s is declared UNCONSTRUCTIBLE but carries %d rel_end row(s)"
                            % (sid, len(s["rel_end_rows"])))
        if s["unconstructible"] and n_neutral:
            problems.append("scope %s is declared UNCONSTRUCTIBLE because neutral_content is 0, "
                            "but the artifact carries %d neutral_content token(s)"
                            % (sid, n_neutral))
    out["problems"] = problems
    out["ok"] = not problems
    return out


def refuse_on_scope_map_disagreement(res: Dict[str, Any]) -> Dict[str, Any]:
    if not res.get("ok"):
        raise Refusal(
            "U4 FAILED: the declared scopes do not resolve to what the frozen token-role map "
            "says. %s. A scope whose realised rows are not what the design says they are is the "
            "defect this whole phase exists to fix; no arm may be submitted behind it."
            % "; ".join(res.get("problems", [])))
    return res


# ============================================================================================
# 17. U3 -- WHAT EXISTS ON THE CONCEPT-FREE CHANNEL, AND EXACTLY WHAT IS MISSING
# ============================================================================================
def u3_inventory(pr: Prereg, runs_root: str) -> Dict[str, Any]:
    """Checklist U3, honestly: can the SD be measured from rows that already exist?

    The requirement is specific -- the between-domain SD of the PAIRED knockout delta in
    `semantic_logodds`, on the CONCEPT-FREE channel, on the preregistered banks, over the
    preregistered VALIDATION domains. This walks the completed runs and reports what is present
    and what is missing, INSTEAD OF ESTIMATING. Borrowing the old ladder's magnitudes is
    explicitly forbidden and a run on another bank is not this population.
    """
    root = runs_root if os.path.isdir(runs_root) else os.path.join(REPO, runs_root)
    if not os.path.isdir(root):
        raise Refusal("no run root at %r" % runs_root)
    banks = {os.path.basename(str(v["path"])): k
             for k, v in pr.require("population", "banks").items()}
    qk = primary_channel(pr)
    dose = int(pr.require("population", "n_examples_primary"))
    assign = load_split(pr)
    validation = sorted(d for d, s in assign.items() if s == "validation")
    on_population, off_population = [], []
    for d in sorted(os.listdir(root)):
        p = os.path.join(root, d)
        cfg = os.path.join(p, "config.json")
        if not os.path.exists(cfg) or not os.path.exists(os.path.join(p, "DONE.json")):
            continue
        try:
            a = json.load(open(cfg))["args"]
        except Exception:
            continue
        if qk not in str(a.get("query_kinds", "")):
            continue
        if not str(a.get("intervene") or ""):
            continue
        bank = os.path.basename(str(a.get("bank", "")))
        rec = {"run": d, "bank": bank, "scope": a.get("knockout_scope"),
               "intervene": a.get("intervene"), "n_examples": a.get("n_examples")}
        (on_population if bank in banks else off_population).append(rec)
    sufficient = bool(on_population)
    missing = []
    if not on_population:
        missing.append(
            "NO knockout run on the concept-free channel %r exists on ANY of the %d preregistered "
            "%s banks. Every concept-free knockout in the repository is on a different bank, so "
            "its domains are not this population and its SD is not this design's SD."
            % (qk, len(banks), pr.require("population", "bank_family")))
        missing.append(
            "the measurement U3 asks for needs, at minimum: the untouched baseline arm (S_0) and "
            "the reference scope arm, both on a preregistered bank, cell %s, %r, n_examples=%d, "
            "over the %d VALIDATION domains -- paired within prompt_id. That is GPU work and this "
            "session is CPU-only." % (primary_cell(pr), qk, dose, len(validation)))
    return {"query_kind": qk, "n_validation_domains": len(validation),
            "n_runs_on_preregistered_banks": len(on_population),
            "runs_on_preregistered_banks": on_population[:10],
            "n_runs_off_population": len(off_population),
            "runs_off_population": off_population[:10],
            "sufficient": sufficient, "missing": missing,
            "_rule": "if the existing rows do not suffice, say exactly what is missing rather "
                     "than estimating. power.mde.in_semantic_logodds_nats stays null and U3 stays "
                     "BLOCKING."}


# ============================================================================================
# 18. ARM MANIFEST AND PLAN
# ============================================================================================
@dataclass
class ArmSpec:
    arm_id: str
    bank: str
    scope_id: str
    rel_end_rows: List[int]
    kind: str                  # baseline | scope | random_row_control | nondemo_control | bridge
    draw_index: int
    n_examples: int
    query_kind: str
    expect_enabled: bool
    confirmatory: bool
    family_member: bool

    def tag(self) -> str:
        return "pr059_%s_%s_%s%s_n%d" % (self.bank, self.scope_id.lower(), self.kind,
                                         ("" if self.draw_index < 0 else "%d" % self.draw_index),
                                         self.n_examples)


def build_arm_manifest(pr: Prereg, banks: Optional[Sequence[str]] = None) -> List[ArmSpec]:
    """The staged manifest. The reference scope and the baseline come FIRST because the kill
    condition reads them."""
    scopes = declared_scopes(pr)
    members = set(family_member_ids(pr))
    ref = reference_scope_id(pr)
    qk = primary_channel(pr)
    dose = int(pr.require("population", "n_examples_primary"))
    bank_keys = list(banks) if banks is not None else primary_banks(pr)
    conf = set(primary_banks(pr))
    span = query_span_rel_end(pr)
    arms: List[ArmSpec] = []

    def _add(bank, sid, rows, kind, draw, enabled=True):
        arms.append(ArmSpec(arm_id="%s_%s_%s%s" % (bank, sid, kind,
                                                   "" if draw < 0 else "_d%d" % draw),
                            bank=bank, scope_id=sid, rel_end_rows=list(rows), kind=kind,
                            draw_index=draw, n_examples=dose, query_kind=qk,
                            expect_enabled=enabled, confirmatory=(bank in conf),
                            family_member=(sid in members)))

    ordered = ([sid for sid in scopes if sid.endswith("_0")]
               + [ref]
               + [sid for sid in scopes if sid not in (ref,) and not sid.endswith("_0")])
    for bank in bank_keys:
        for sid in ordered:
            s = scopes.get(sid)
            if s is None:
                continue
            if s["unconstructible"]:
                continue                       # declared absent; it enters Holm at p = 1.0
            if not s["rel_end_rows"]:
                _add(bank, sid, [], "baseline", -1)
                continue
            _add(bank, sid, s["rel_end_rows"], "scope", -1)
            # ---- PR059-D5, RESOLVED HERE (the analyzer was the wrong one, for the +6) --------
            # This used to be `if sid == ref: continue  # the denominator gets no dose-matched
            # control`, which skipped BOTH declared controls for the reference scope. That was one
            # refusal doing duty for two, and the two are not the same refusal:
            #
            #   per_scope_random_row_control  -- needs an m-row draw from the query span EXCLUDING
            #       the scope's own rows. For the reference m == len(span), so the pool is EMPTY.
            #       It is genuinely unbuildable, it is refused by `random_row_control_constructible`
            #       three lines below, and PR059-D1 already decided what that costs.
            #   per_scope_nondemo_key_control -- draws NON-DEMONSTRATION KEYS, and the frozen file
            #       says its pool "EXCLUDES query_span_positions". The 28-row query span therefore
            #       does not constrain it AT ALL, at any m. The frozen text is "for EVERY scope"
            #       and names no exemption.
            #
            # Skipping the second because the first is impossible left the DENOMINATOR OF EVERY
            # FRACTION THIS PHASE REPORTS with no control of any kind, and made the analyzer's
            # manifest disagree with the independent verifier by exactly these 6 arms (3 draws x
            # 2 confirmatory banks). The verifier was right; this file was wrong. The reference
            # still gets no random-row control, because that one really cannot be built.
            if random_row_control_constructible(pr, sid, s["rel_end_rows"],
                                                span)["constructible"]:
                for i in range(n_random_row_draws(pr)):
                    _add(bank, sid, random_row_control_draw(pr, sid, s["rel_end_rows"], i,
                                                            span)["rel_end_rows"],
                         "random_row_control", i)
            for i in range(n_nondemo_draws(pr)):
                _add(bank, sid, s["rel_end_rows"], "nondemo_control", i)
        _add(bank, ref, scopes[ref]["rel_end_rows"], "bridge", -1, enabled=False)
    if not arms:
        raise Refusal("the arm manifest is empty -- scopes.family declares nothing constructible")
    return arms


def launch_command(pr: Prereg, arm: ArmSpec) -> str:
    lo, hi = intervention_band(pr)
    parts = ["python3 scripts/dcs_ts_readout_multi.py",
             "--bank %s" % pr.require("population", "banks", arm.bank, "path"),
             "--only-cell %s" % primary_cell(pr),
             "--only-query-kind %s" % arm.query_kind,
             "--only-n-examples %d" % arm.n_examples,
             "--attn-impl %s" % required_attn_impl(pr)]
    if arm.kind == "baseline":
        parts.append("--no-knockout")
        return " ".join(parts)
    parts.append("--intervene demo_all:attn_knockout:%d-%d:1.0" % (lo, hi))
    parts.append("--knockout-scope query_last_k_rows   # the surface_span channel, row set below")
    parts.append("--declared-rel-end %s   # U1 selector (producer-side patch outstanding)"
                 % ",".join(str(x) for x in arm.rel_end_rows))
    if arm.kind == "nondemo_control":
        parts.append("--nondemo-matched-draws %d --nondemo-draw-seed %d"
                     % (n_nondemo_draws(pr), int(pr.require("seeds", "nondemo_draws"))))
    if arm.kind == "bridge":
        parts.append("--disable-hook")
    return " ".join(parts)


def plan(pr: Prereg) -> int:
    scopes = declared_scopes(pr)
    arms = build_arm_manifest(pr)
    lo, hi = intervention_band(pr)
    print("=== %s PHASE 11 arm manifest ===" % PR_ID)
    print("  PRIMARY channel=%r (concept word present on 0.0%% of its rows); DISPLAY channel=%r "
          "is SECONDARY DISPLAY ONLY and is FORBIDDEN as a mechanism result"
          % (primary_channel(pr), display_channel(pr)))
    print("  band=blocks %d-%d attn=%s (FORCED) secondary_read=%s primary_read_layer=%d grid=%s"
          % (lo, hi, required_attn_impl(pr), secondary_read_position(pr),
             primary_read_layer(pr), read_layers(pr)))
    print("  selector field=%r (NEVER %r -- A-039); whole-population exclusions=%s"
          % (SELECTOR_FIELD, FORBIDDEN_SELECTOR_FIELD, whole_population_exclusions(pr)))
    print("  alpha=%g n_perm=%d p_floor=%.4e option_mass_gate=%g power_bar=%g mde=%g nats "
          "fraction_rule=%g installation_cut=%g resolver_tolerance=%g"
          % (alpha(pr), n_perm(pr), p_floor(pr), option_mass_gate_value(pr), power_bar(pr),
             declared_mde(pr), half_of_reference_rule(pr), installation_cut(pr),
             resolver_failure_tolerance(pr)))
    print("  family %s members=%s ; reference (denominator, NOT a member)=%s ; scaffold-null=%s"
          % (FAMILY_NAME, family_member_ids(pr), reference_scope_id(pr), scaffold_scope_id(pr)))
    print("  CONFIRMATORY banks=%s ; REGISTERED DESCRIPTIVE (no confirmatory weight)=%s ; the two "
          "codewords are a TRANSFER PAIR and are NEVER pooled"
          % (primary_banks(pr), descriptive_banks(pr)))
    for sid, s in scopes.items():
        print("  scope %-5s n_rows=%-2d rel_end=%s%s"
              % (sid, s["n_rows"], s["rel_end_rows"] if s["rel_end_rows"] else "(none)",
                 "   UNCONSTRUCTIBLE -- enters Holm at p = 1.0 as an absent member"
                 if s["unconstructible"] else ""))
    print("  -- staged submission order: the baseline and %s first; the kill condition reads them "
          "before any narrower scope is submitted --" % reference_scope_id(pr))
    for a in arms:
        print("  %-34s bank=%s scope=%s kind=%-18s dose=%d member=%s tag=%s"
              % (a.arm_id, a.bank, a.scope_id, a.kind, a.n_examples, a.family_member, a.tag()))
        print("      %s" % launch_command(pr, a))
    print("[plan] %d arm(s) over %d bank(s)" % (len(arms), len(set(a.bank for a in arms))))
    return 0


def selector_demo(pr: Prereg) -> int:
    """U1 as a demonstration: the same declared scope resolving DIFFERENTLY in prompts of
    different length, which is the property an absolute index does not have."""
    scopes = declared_scopes(pr)
    tm = load_token_map()
    recs = tm["records"]
    by_len: "OrderedDict[int, Dict[str, Any]]" = OrderedDict()
    for r in recs:
        by_len.setdefault(int(r["n_tokens"]), r)
        if len(by_len) >= 3:
            break
    print("=== %s U1: the DECLARED-OFFSET row selector ===" % PR_ID)
    print("  one definition, called by the pre-flight pass, the per-row resolution and the "
          "extractor; END-RELATIVE in every prompt separately")
    for sid, s in scopes.items():
        if not s["rel_end_rows"]:
            print("  %-5s (no rows -- %s)" % (sid, s["status"] or "baseline"))
            continue
        print("  %-5s rel_end=%s" % (sid, s["rel_end_rows"]))
        for n, r in by_len.items():
            qs = int(r["query_role_start"])
            pos = surface_span_from_rel_end(s["rel_end_rows"], n, list(range(qs, n)))
            toks = [r["tokens"][p] for p in pos]
            print("      seq_len=%-4d -> positions %s%s decoded %s%s"
                  % (n, pos[:6], " ..." if len(pos) > 6 else "",
                     toks[:6], " ..." if len(toks) > 6 else ""))
        ag = selector_sites_agree(s["rel_end_rows"], max(by_len))
        print("      pre-flight == per-row: %s" % ag["ok"])
    print("[selector] the same declared scope resolves to a DIFFERENT absolute set in each "
          "sequence length; an absolute index would not.")
    return 0


def control_draws(pr: Prereg) -> int:
    """U2 as a demonstration: the per-scope dose-matched random-row draws, seeded and RECORDED."""
    scopes = declared_scopes(pr)
    span = query_span_rel_end(pr)
    print("=== %s U2: per-scope dose-matched RANDOM-ROW controls ===" % PR_ID)
    print("  pool = the query span %s minus the scope's OWN rows; %d draws; seed from "
          "seeds.random_row_draws" % ([min(span), max(span)], n_random_row_draws(pr)))
    n_fail = 0
    for sid, s in scopes.items():
        if not s["rel_end_rows"] or sid == reference_scope_id(pr):
            continue
        con = random_row_control_constructible(pr, sid, s["rel_end_rows"], span)
        if not con["constructible"]:
            print("  %-5s NOT CONSTRUCTIBLE -- %s" % (sid, con["reason"]))
            n_fail += 1
            continue
        band = random_row_control_band(pr, sid, s["rel_end_rows"], span)
        print("  %-5s m=%d pool=%d distinct_row_sets=%d/%d possible=%d ok=%s%s"
              % (sid, band["draws"][0]["m"], band["draws"][0]["pool_size"],
                 band["n_distinct_row_sets"], band["n_draws"], band["n_possible_row_sets"],
                 band["ok"], ("   " + band["_note"]) if band["_note"] else ""))
        for d in band["draws"]:
            print("      draw %d -> rel_end %s" % (d["draw_index"], d["rel_end_rows"]))
        n_fail += 0 if band["ok"] else 1
    print("[controls] %d scope(s) with a non-constructible or collapsed band" % n_fail)
    return 1 if n_fail else 0


# ============================================================================================
# 19. SELF-TEST
# ============================================================================================
def _lr(**kw) -> Dict[str, Any]:
    """A liveness record that is clean unless a field is overridden. seq_len 200, scope {-10}."""
    base = LivenessRecord(arm_id="u", scope_id="S_C", prompt_id="p", enabled=True,
                          hook_fired_count=1, n_forward=1, n_prefill_edits=1, n_decode_edits=0,
                          keys_masked=4, surface_span_n_tokens=1,
                          surface_span_positions=[190], surface_span_decoded=[" button"],
                          n_cells_edited_expected=1, n_cells_edited_realised=1,
                          attn_implementation="eager", seq_len=200,
                          query_kind="semantic_one_word", output_sha256="a").as_row()
    base.update(kw)
    return base


def _readout(arm_id="u", scope_id="S_C", om=None, ans=None) -> ArmReadout:
    om = om if om is not None else [0.11, 0.12, 0.13, 0.2]
    ans = ans if ans is not None else [" Button", " Bomb", " Button", " Basket"]
    return ArmReadout(arm_id=arm_id, scope_id=scope_id, n_rows=len(om), n_domains=2,
                      option_mass=list(om), argmax_answers=list(ans),
                      logodds=[float(0)] * len(om))


def _obs_scope(pr: Prereg, sid: str, delta: float, p: float,
               control_deltas: Optional[Sequence[float]] = None,
               distinct: bool = True, n_dom: int = 8) -> Dict[str, Any]:
    per = OrderedDict((("d%d" % i), delta) for i in range(n_dom))
    st = {"unit": "domain", "n_domains": n_dom, "observed_delta": delta,
          "per_domain_delta": dict(per),
          "permutation": {"p": p, "floor": p_floor(pr), "n_exceed": 0, "n_perm": n_perm(pr),
                          "formatted": fmt_p(p, p_floor(pr), 0)}}
    rec: Dict[str, Any] = {
        "scope_id": sid, "arm_id": "a_" + sid, "readout": _readout(arm_id="a_" + sid,
                                                                   scope_id=sid),
        "per_domain": {k: [v] for k, v in per.items()}, "stats": st, "delta": delta,
        "p": p, "floor": p_floor(pr), "formatted": st["permutation"]["formatted"],
        "control": None}
    if control_deltas is not None:
        shas = [("%064x" % (i + 1)) for i in range(len(control_deltas))]
        if not distinct:
            shas = [shas[0]] * len(control_deltas)
        rec["control"] = {"n_draws": len(control_deltas), "deltas": list(control_deltas),
                          "output_sha256": shas,
                          "band": control_interval(list(control_deltas), alpha(pr))
                          if len(control_deltas) > 1 else None,
                          "distinct": control_band_gate(shas, n_random_row_draws(pr))}
    return rec


def _fake_obs(pr: Prereg, ref_delta: float = -6.0, ref_p: float = 0.0001,
              winner: str = "S_C", winner_delta: float = -4.0, winner_p: float = 0.0001,
              control_deltas: Optional[Sequence[float]] = (-0.1, -0.2, -0.15),
              scaffold_delta: float = 0.0, scaffold_p: float = 0.9,
              liveness_clean: bool = True,
              void_evidence: Optional[Dict[str, Any]] = None,
              cannot_answer_evidence: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """A COMPLETE synthetic observation, so `decide()` runs END TO END with no run directory.

    Every quantity here is a number a real run would MEASURE; nothing about the decision is
    encoded. That is the point of the observe/decide split: the verdict logic is exercised on a
    CPU with no GPU, which is exactly what PR059-D7 (and PHASE 9's A4) says never happened.
    """
    ref, scaf = reference_scope_id(pr), scaffold_scope_id(pr)
    scopes = OrderedDict()
    scopes[ref] = _obs_scope(pr, ref, ref_delta, ref_p)
    scopes[scaf] = _obs_scope(pr, scaf, scaffold_delta, scaffold_p,
                              control_deltas=list(control_deltas or []) or None)
    if winner not in (ref, scaf):
        scopes[winner] = _obs_scope(pr, winner, winner_delta, winner_p,
                                    control_deltas=control_deltas)
    ve = {k: True for _pat, k in VOID_CLAUSE_KEYS}
    ve.update(void_evidence or {})
    ce = {k: True for _pat, k in CANNOT_ANSWER_CLAUSE_KEYS}
    ce.update(cannot_answer_evidence or {})
    return {"liveness_clean": bool(liveness_clean),
            "void_evidence": ve, "cannot_answer_evidence": ce,
            "banks": OrderedDict([(primary_banks(pr)[0], {
                "baseline_readout": _readout(arm_id="a_base", scope_id="S_0"),
                "scopes": scopes, "reference": scopes[ref], "scaffold": scopes[scaf]})])}


def _fake_bank(pr: Prereg, n_dom=4) -> Dict[str, Dict[str, Any]]:
    out = {}
    for i in range(n_dom):
        pid = "p_%d" % i
        out[pid] = {"prompt_id": pid, "cell": primary_cell(pr),
                    "condition": "natural_doublespeak",
                    "query_kind": primary_channel(pr),
                    "n_examples": int(pr.require("population", "n_examples_primary")),
                    "domain": "dom%d" % i, "concept": "bomb", "codeword": "button",
                    "full_prompt": "the button was left on the bench.",
                    "n_concept_occurrences": 0}
    return out


def selftest(pr: Prereg) -> int:
    ck = Checks()
    scopes = declared_scopes(pr)
    span = query_span_rel_end(pr)
    ref = reference_scope_id(pr)
    scaf = scaffold_scope_id(pr)

    # ---- gates come from the frozen file, and the file's own arithmetic agrees ----------
    ck.add("p_floor_consistent", "attainable_p_floor == 1/(n_perm+1), re-derived not quoted",
           abs(p_floor(pr) - 1.0 / (n_perm(pr) + 1.0)) < 1e-9, 1,
           "floor=%.6e n_perm=%d" % (p_floor(pr), n_perm(pr)))
    ck.add("gates_parsed", "the option_mass gate, the power bar and the resolver tolerance are "
           "PARSED out of the frozen file's prose, not re-typed",
           option_mass_gate_value(pr) > 0 and power_bar(pr) > 0
           and 0 < resolver_failure_tolerance(pr) < 1, 3,
           "om=%g bar=%g tol=%g" % (option_mass_gate_value(pr), power_bar(pr),
                                    resolver_failure_tolerance(pr)))
    ck.add("fraction_rule_inherited", "the reproduction rule is read from the frozen file, not "
           "chosen here", 0 < half_of_reference_rule(pr) <= 1, 1,
           "rule=%g" % half_of_reference_rule(pr))
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
    mde = mde_in_sd_units_check(pr)
    ck.add("mde_sd_units", "the frozen file's SD-unit MDEs agree with its own declared formula",
           mde["ok"], len(mde["per_n"]), "disagreeing=%s" % mde["disagreeing"])

    # ---- wording ------------------------------------------------------------------------
    ck.add("wording_pin", "the mandatory negative wording in the code equals the frozen file's",
           check_wording_pin(pr) == MANDATORY_NEGATIVE_WORDING, 1)
    forb = forbidden_from_prereg(pr)
    caught = False
    try:
        assert_sayable("this run shows K=7 proves the bomb token is the mechanism", forb)
    except Refusal:
        caught = True
    ck.add("forbidden_wording", "a mandate-33 forbidden claim cannot be emitted", caught,
           len(forb))
    ck.add("negative_is_sayable", "the mandatory negative itself is not blocked by the forbidden "
           "list", assert_sayable(MANDATORY_NEGATIVE_WORDING, forb) ==
           MANDATORY_NEGATIVE_WORDING, 1)

    # ---- the scope family ---------------------------------------------------------------
    ck.add("scopes_parsed", "every scope's rel_end set is re-derived and agrees with its declared "
           "n_rows", all(len(s["rel_end_rows"]) == s["n_rows"] for s in scopes.values()),
           len(scopes), "%s" % {k: v["n_rows"] for k, v in scopes.items()})
    ck.add("range_and_difference_parsed", "the '[-a..-b] minus [-c]' form parses to the declared "
           "difference", parse_rel_end_spec("[-28..-6] minus [-10]") ==
           sorted(set(range(-28, -5)) - {-10}), 22)
    caught = False
    try:
        parse_rel_end_spec([5, 6])
    except Refusal:
        caught = True
    ck.add("absolute_offsets_refused", "a NON-NEGATIVE offset is refused: positions are always "
           "len(input_ids)+rel_end", caught, 1)
    ck.add("query_span_from_layout", "the query span is read off the frozen token-role layout, "
           "never hardcoded and never inferred from a K",
           len(span) == int(pr.require("token_map", "query_role_census_constant_in_6900_of_6900",
                                       "_total_query_side_tokens")), len(span),
           "rel_end %d..%d" % (min(span), max(span)))
    ck.add("reference_not_a_member", "the denominator scope is NOT a member of the corrected "
           "family", ref not in family_member_ids(pr), 1, "reference=%s" % ref)
    unc = [sid for sid, s in scopes.items() if s["unconstructible"]]
    ck.add("unconstructible_declared", "the unconstructible scope is declared, carries zero rows, "
           "and is a family member so it can enter Holm at p = 1.0",
           len(unc) == 1 and not scopes[unc[0]]["rel_end_rows"]
           and unc[0] in family_member_ids(pr), len(unc), "%s" % unc)

    # ---- U1 the declared-offset selector -------------------------------------------------
    pos = surface_span_from_rel_end(scopes[scaf]["rel_end_rows"], 200)
    pos2 = surface_span_from_rel_end(scopes[scaf]["rel_end_rows"], 237)
    ck.add("selector_end_relative", "the same declared scope resolves to a DIFFERENT absolute set "
           "in a different-length prompt", pos != pos2 and len(pos) == len(pos2), len(pos),
           "%s vs %s" % (pos[:3], pos2[:3]))
    ck.add("selector_sites_agree", "the pre-flight pass and the per-row resolution share ONE "
           "definition", selector_sites_agree(scopes[scaf]["rel_end_rows"], 200)["ok"], 1)
    caught = False
    try:
        surface_span_from_rel_end([-10], 200, query_span_positions=list(range(0, 100)))
    except Refusal:
        caught = True
    ck.add("selector_outside_query_span", "a scope resolving outside the prompt's query span is "
           "refused (the codeword also appears in the demonstrations)", caught, 1)
    caught = False
    try:
        surface_span_from_rel_end([], 200)
    except ZeroBinding:
        caught = True
    ck.add("selector_empty_scope", "an EMPTY scope is refused rather than run as an arm that cuts "
           "nothing and scores as a clean null", caught, 1)
    good = assert_realised_equals_declared(
        [_lr(seq_len=200, surface_span_positions=[190]),
         _lr(seq_len=237, surface_span_positions=[227])], [-10],
        decoded_by_rel_end={-10: " button"})
    bad = assert_realised_equals_declared(
        [_lr(seq_len=200, surface_span_positions=[191])], [-10])
    ck.add("realised_equals_declared", "L-N4: a realised row set differing from the declared "
           "rel_end set is caught", good["ok"] and not bad["ok"], good["n_records"],
           bad["reason"][:100])
    badtok = assert_realised_equals_declared(
        [_lr(seq_len=200, surface_span_positions=[190], surface_span_decoded=[" basket"])],
        [-10], decoded_by_rel_end={-10: " button"})
    ck.add("realised_token_checked", "a realised DECODED TOKEN differing from the token-role "
           "map's modal decoding is caught", not badtok["ok"], 1)
    rf = resolver_failure_gate(1, 100, pr)
    rf_bad = resolver_failure_gate(50, 100, pr)
    ck.add("resolver_tolerance", "a row-set resolver failing on more than the declared fraction of "
           "rows is CANNOT ANSWER", not rf["cannot_answer"] and rf_bad["cannot_answer"], 2)

    # ---- U2 the random-row control -------------------------------------------------------
    d0 = random_row_control_draw(pr, "S_C", [-10], 0, span)
    d0b = random_row_control_draw(pr, "S_C", [-10], 0, span)
    d1 = random_row_control_draw(pr, "S_C", [-10], 1, span)
    ck.add("control_draw_reproducible", "the same seed and draw index reproduce the same rows "
           "across processes (hashlib, never salted hash())",
           d0["rel_end_rows"] == d0b["rel_end_rows"], len(d0["rel_end_rows"]))
    ck.add("control_draw_excludes_scope", "the draw pool EXCLUDES the scope's own rows and the "
           "draw is dose-matched",
           (-10 not in d0["rel_end_rows"]) and len(d0["rel_end_rows"]) == 1
           and d0["pool_size"] == len(span) - 1, d0["pool_size"])
    ck.add("control_draws_differ", "different draw indices give different rows",
           d0["rel_end_rows"] != d1["rel_end_rows"], 2)
    ck.add("control_draw_recorded", "the draw is RECORDED -- seed, pool and chosen rows",
           all(k in d0 for k in ("seed", "derived_seed", "pool_rel_end", "rel_end_rows",
                                 "excluded_rel_end")), 5)
    con_big = random_row_control_constructible(pr, "S_E", scopes["S_E"]["rel_end_rows"], span)
    ck.add("control_not_constructible_recorded", "a scope whose dose exceeds the remaining pool is "
           "reported as NOT CONSTRUCTIBLE, not as a passed control",
           not con_big["constructible"] and bool(con_big["reason"]), 1,
           "m=%d pool=%d" % (con_big["m"], con_big["pool_size"]))
    caught = False
    try:
        random_row_control_draw(pr, "S_E", scopes["S_E"]["rel_end_rows"], 0, span)
    except Refusal:
        caught = True
    ck.add("control_draw_refuses_when_impossible", "asking for a draw larger than the pool "
           "refuses rather than silently drawing fewer rows", caught, 1)
    n_dr = n_random_row_draws(pr)
    ck.add("control_band_hashes", "%d distinct output hashes pass; identical hashes VOID the band"
           % n_dr, control_band_gate([str(i) for i in range(n_dr)], n_dr)["ok"]
           and not control_band_gate(["z"] * n_dr, n_dr)["ok"], n_dr)
    caught = False
    try:
        assert_scope_has_its_control("S_C", None)
    except Refusal:
        caught = True
    ck.add("scope_needs_control", "a scope reported without its dose-matched control is refused",
           caught, 1)

    # ---- population binding --------------------------------------------------------------
    assign = {"dom%d" % i: ("train" if i < 2 else "validation") for i in range(4)}
    bank = _fake_bank(pr)
    b = bind_rows(pr, bank, assign)
    ck.add("bind_cell", "binding on `cell` returns rows and domains",
           b["n_rows"] > 0 and b["n_domains"] > 0, b["n_rows"], "domains=%d" % b["n_domains"])
    caught = False
    try:
        bind_rows(pr, bank, assign, selector_field=FORBIDDEN_SELECTOR_FIELD)
    except Refusal:
        caught = True
    ck.add("selector_field", "binding on `condition` is refused before it can bind zero (A-039)",
           caught, 1)
    caught = False
    try:
        bind_rows(pr, {}, assign)
    except ZeroBinding:
        caught = True
    ck.add("zero_row_bind", "a zero-row bind RAISES, never returns an empty result", caught, 1)
    excl = whole_population_exclusions(pr)
    ck.add("exclusions_structured", "the whole-population exclusions come from the BOOLEAN field, "
           "never a hardcoded list", len(excl) == 3 and all(isinstance(x, str) for x in excl),
           len(excl), "%s" % excl)
    ep = assert_equal_populations({"a": ["x", "y"], "b": ["x", "y"]})
    ep_bad = assert_equal_populations({"a": ["x", "y"], "b": ["x"]})
    ck.add("equal_populations", "unequal per-arm populations are caught (L-N11)",
           ep["ok"] and not ep_bad["ok"], 2)

    # ---- the channel ----------------------------------------------------------------------
    ck.add("primary_channel_ok", "the concept-free channel is accepted as the primary",
           refuse_display_channel_as_primary(pr, primary_channel(pr)) == primary_channel(pr), 1)
    caught = False
    try:
        refuse_display_channel_as_primary(pr, display_channel(pr))
    except Refusal:
        caught = True
    ck.add("display_channel_refused", "the display channel is REFUSED as a primary -- it names "
           "the concept in its own question on 100.0%% of its rows", caught, 1)
    caught = False
    try:
        refuse_display_fallback(pr, False)
    except CannotAnswer:
        caught = True
    ck.add("no_display_fallback", "a disengaged primary channel is CANNOT ANSWER, never a "
           "fallback to the display channel", caught, 1)
    cw = concept_word_absence_gate(list(_fake_bank(pr).values()), ["bomb", "knife", "gun"])
    ck.add("concept_absent", "L-N12: zero whole-word concept occurrences on primary-channel rows, "
           "recounted independently", cw["ok"], cw["n_rows"])
    leaky = list(_fake_bank(pr).values())
    leaky[0] = dict(leaky[0], full_prompt="a bomb was on the bench", n_concept_occurrences=1)
    ck.add("concept_present_caught", "a primary-channel row carrying the concept word is caught",
           not concept_word_absence_gate(leaky, ["bomb", "knife", "gun"])["ok"], len(leaky))
    caught = False
    try:
        bad_rows = [dict(list(_fake_bank(pr).values())[0], full_prompt="a bomb here",
                         n_concept_occurrences=0)]
        concept_word_absence_gate(bad_rows, ["bomb"])
    except Refusal:
        caught = True
    ck.add("count_disagreement_refuses", "a disagreement between the independent recount and the "
           "bank's own count is a REFUSAL, not a tie-break", caught, 1)

    # ---- liveness ---------------------------------------------------------------------------
    lg = liveness_gate([_lr()], "u", pr)
    ck.add("liveness_clean", "a clean prefill-only knockout record passes", lg["live"], 1,
           "; ".join(lg["reasons"])[:120])
    ck.add("dead_hook", "hook_fired_count == 0 is VOID, not a null",
           not liveness_gate([_lr(hook_fired_count=0)], "u", pr)["live"], 1)
    ck.add("sdpa_void", "an arm whose LOADED config is not eager is VOID (the additive mask edit "
           "is discarded under SDPA)",
           not liveness_gate([_lr(attn_implementation="sdpa")], "u", pr)["live"], 1)
    ck.add("decode_leak", "a non-zero n_decode_edits in this prefill-only family refuses",
           not liveness_gate([_lr(n_decode_edits=2)], "u", pr)["live"], 1)
    ck.add("zero_dose", "a zero realised dose refuses",
           not liveness_gate([_lr(surface_span_n_tokens=0)], "u", pr)["live"], 1)
    ck.add("no_liveness_records", "an arm with no liveness records at all is VOID",
           not liveness_gate([], "u", pr)["live"], 1)
    bridge_rec = _lr(enabled=False, hook_fired_count=0, n_prefill_edits=0,
                     n_cells_edited_realised=0, n_forward=3)
    ck.add("bridge", "the disabled-hook bridge passes as a bridge and REFUSES as a live arm",
           liveness_gate([bridge_rec], "b", pr, expect_enabled=False)["live"]
           and not liveness_gate([bridge_rec], "b", pr)["live"], 1)
    a1 = audit_end_relative([_lr(seq_len=200, surface_span_positions=[190]),
                             _lr(seq_len=237, surface_span_positions=[227])], [-10])
    a2 = audit_end_relative([_lr(seq_len=200, surface_span_positions=[190]),
                             _lr(seq_len=237, surface_span_positions=[190])], [-10])
    ck.add("end_relative", "len(input_ids)+rel_end passes and an ABSOLUTE index reused across "
           "differing lengths is caught", a1["ok"] and not a2["ok"], a1["n_records"],
           a1["witness_note"])
    ck.add("bridge_gate", "the disabled-hook bridge must reproduce the baseline byte-for-byte",
           disabled_bridge_gate("aa", "aa", float(0))["ok"]
           and not disabled_bridge_gate("aa", "bb", float(0))["ok"]
           and not disabled_bridge_gate("aa", "aa", 1e-3)["ok"], 3)
    ck.add("null_dose_arm", "the n_examples=0 arm is a LEDGERED population check",
           null_dose_arm_gate(pr, 10, [])["ok"] and not null_dose_arm_gate(pr, 0, [])["ok"], 2)
    caught = False
    try:
        null_dose_arm_gate(pr, 10, [0.3])
    except Refusal:
        caught = True
    ck.add("dose0_not_readable", "a dose-0 logodds offered as an outcome is refused -- median "
           "option_mass at dose 0 is below the gate", caught, 1)
    caught = False
    try:
        refuse_dose_pooling([4, 8])
    except Refusal:
        caught = True
    ck.add("no_dose_pooling", "doses are separate preregistered cells and are never pooled",
           caught and refuse_dose_pooling([4]) == 4, 2)

    # ---- readout before delta ----------------------------------------------------------------
    ro = _readout()
    delta = ScopeDelta(scope_id="S_C", arm_id="u", readout=ro,
                       control={"ok": True}, per_domain={"a": -0.3, "b": -0.4},
                       stats={"observed_delta": -0.35})
    caught = False
    try:
        render_delta(delta, p_floor(pr), fh=open(os.devnull, "w"))
    except Refusal:
        caught = True
    ck.add("delta_needs_readout", "a delta REFUSES to print before its option_mass / argmax "
           "readout is rendered", caught, 1)
    ro.render(fh=open(os.devnull, "w"))
    ck.add("delta_after_readout", "the same delta prints once the readout has been rendered",
           bool(render_delta(delta, p_floor(pr), fh=open(os.devnull, "w"))), 1)
    caught = False
    try:
        ScopeDelta(scope_id="S_C", arm_id="u", readout=None, control={"ok": True},
                   per_domain={"a": 0.1})
    except Refusal:
        caught = True
    ck.add("no_readout_object", "a delta cannot be constructed without a readout at all", caught, 1)
    gate_ok = engagement_gate(ro, pr)
    dis = engagement_gate(_readout(om=[option_mass_gate_value(pr) / 2.0] * 4), pr)
    ck.add("engagement_gate", "an arm whose median option_mass falls below the declared gate is "
           "CANNOT ANSWER", gate_ok["engaged"] and dis["cannot_answer"], 2,
           "median=%.4f gate=%.4f" % (gate_ok["median_option_mass"], gate_ok["gate"]))
    # ---- DCS-PR-065: the stop-scope of a below-gate arm --------------------------------------
    # The GATE is the parent's and is checked immediately above. THIS checks only what the parent
    # left open: how many OTHER arms one below-gate arm takes down. Role in, disposition out --
    # no measured value is read, so the answer is the same at 0.01 and at one tick under the gate.
    _am3 = load_gate_policy_amendment()
    _refs = reference_scope_id(pr)
    _d_ref = below_gate_disposition(pr, _am3, "scope", _refs)
    _d_nar = below_gate_disposition(pr, _am3, "scope", "S_C")
    _d_ctl = below_gate_disposition(pr, _am3, "nondemo_control", _refs)
    _d_bas = below_gate_disposition(pr, _am3, "baseline", "S_0")
    ck.add("below_gate_reference_closes_bank",
           "the REFERENCE scope below the gate closes its own bank -- every narrower number is a "
           "fraction of S_G, so an unreadable denominator makes them undefined",
           _d_ref["disposition"] == "CANNOT_ANSWER_BANK" and _d_ref["closes_bank"], 2,
           _d_ref["reason"][:60])
    ck.add("below_gate_narrow_scope_is_arm_only",
           "a NARROWER scope below the gate is CANNOT ANSWER for itself and the stage continues",
           _d_nar["disposition"] == "CANNOT_ANSWER_ARM" and not _d_nar["closes_bank"], 2)
    ck.add("below_gate_control_is_arm_only",
           "a control arm below the gate is CANNOT ANSWER for itself, never for the stage",
           _d_ctl["disposition"] == "CANNOT_ANSWER_ARM" and not _d_ctl["closes_bank"], 2)
    ck.add("below_gate_baseline_unchanged",
           "the BASELINE below the gate still KILLS the bank -- the parent's SECOND kill "
           "condition, not weakened under any reading",
           _d_bas["disposition"] == "KILL_BANK" and _d_bas["closes_bank"], 2)
    ck.add("below_gate_is_role_only_never_margin",
           "the stop-scope is a total function of the arm's ROLE and reads no measured value, so "
           "it is identical at 0.01 and at one tick under the gate",
           _am3["option_mass_gate_policy"]["stop_scope_depends_on_margin"] is False
           and _am3["option_mass_gate_policy"]["stop_scope_depends_on_arm_role_only"] is True, 2)
    ck.add("below_gate_never_crosses_banks",
           "a below-gate arm in one bank never closes a bank that was never run -- "
           "`primary.statistic` reports per bank and never pools",
           _am3["option_mass_gate_policy"]["cross_bank_isolation"] is True, 1)
    ck.add("below_gate_carries_its_option_mass",
           "a below-gate arm's option mass must travel with every number derived from it",
           bool(_d_ref["required_travelling_fields"])
           and "median_option_mass" in _d_ref["required_travelling_fields"], 1)
    _caught = 0
    for _bad in ({}, {"id": "X"},
                 {"id": "X", "option_mass_gate_policy": dict(
                     _am3["option_mass_gate_policy"],
                     gate_value=option_mass_gate_value(pr) * 3.0)},
                 {"id": "X", "option_mass_gate_policy": dict(
                     _am3["option_mass_gate_policy"], gate_scope="baseline_only")},
                 {"id": "X", "option_mass_gate_policy": dict(
                     _am3["option_mass_gate_policy"], stop_scope_depends_on_margin=True)},
                 {"id": "X", "option_mass_gate_policy": dict(
                     _am3["option_mass_gate_policy"],
                     below_gate_disposition_by_arm_role={"baseline": "KILL_BANK"})}):
        try:
            below_gate_disposition(pr, _bad or None, "scope", _refs)
        except Refusal:
            _caught += 1
    ck.add("below_gate_policy_refuses_rather_than_defaults",
           "no amendment / no policy block / a re-scoped gate / a moved gate value / a "
           "margin-dependent stop-scope / an unmapped role each REFUSE", _caught == 6, 6,
           "caught %d/6" % _caught)

    sw = argmax_switch_rate([" Button", " Button"], [" Bomb", " Button"])
    ck.add("argmax_switch", "the argmax-switch rate is computed as a CORROBORANT, not a success "
           "condition", sw["n_switched"] == 1 and "CORROBORANT" in sw["_status"], sw["n_paired"])

    # ---- statistics ---------------------------------------------------------------------------
    base = {("d%d" % i): [float(0)] for i in range(20)}
    ko = {("d%d" % i): [-0.6 - 0.01 * i] for i in range(20)}
    perm = domain_group_permutation(base, ko, pr)
    ck.add("domain_permutation", "domain-level permutation on a clear effect",
           perm["observed_delta"] < 0 and perm["permutation"]["p"] <= alpha(pr),
           perm["n_domains"], perm["permutation"]["formatted"])
    ck.add("p_beside_floor", "every p is formatted beside its attainable floor",
           "floor" in perm["permutation"]["formatted"].lower()
           and "floor" in perm["sign_test"]["formatted"].lower(), 2)
    caught = False
    try:
        domain_group_permutation(base, ko, pr, unit="row")
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
    nul = domain_group_permutation(base, {("d%d" % i): [float(0)] for i in range(20)}, pr)
    ck.add("perm_null_centred", "L-N9: the domain-level null is centred at 0 on a null input",
           abs(nul["observed_delta"]) < 1e-12, nul["n_domains"])
    ci = control_interval([0.01, -0.02, float(0), 0.03, -0.01], alpha(pr))
    ck.add("control_interval", "a control is reported with its INTERVAL, not a bare p > alpha",
           ci["ci_low"] < ci["ci_high"], ci["n"])

    ids = family_member_ids(pr)
    hres = holm_with_absent(pr, {ids[0]: 0.001, ids[2]: 0.002})
    ck.add("holm_absent", "a declared member that could not be built enters Holm at p = 1.0, "
           "never dropped", hres["m"] == len(ids)
           and set(hres["absent_members_at_p1"]) == set(ids) - {ids[0], ids[2]}, hres["m"],
           "absent=%s unconstructible=%s" % (hres["absent_members_at_p1"],
                                             hres["unconstructible_members"]))
    caught = False
    try:
        holm({}, alpha(pr))
    except ZeroBinding:
        caught = True
    ck.add("holm_empty", "Holm over an empty family raises", caught, 1)
    caught = False
    try:
        refuse_shrunken_family(pr, ids[:-1])
    except Refusal:
        caught = True
    ck.add("family_not_shrunk", "dropping a declared member from the correction is refused",
           caught and refuse_shrunken_family(pr, ids) == len(ids), len(ids))

    # ---- installation is a stratifier ----------------------------------------------------------
    per_dom = {"a": -1.0, "b": -0.2}
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
    ck.add("install_not_exclusion", "installation used as a post-hoc exclusion is refused",
           caught, 1)
    empt = empty_installing_stratum_gate(stratify_by_installation(
        per_dom, {"a": installation_cut(pr) - 0.1, "b": installation_cut(pr) - 0.2},
        installation_cut(pr)), "basket_knife")
    ck.add("empty_stratum", "an empty installing stratum in a bank is CANNOT ANSWER",
           empt["cannot_answer"], 1)

    # ---- kill conditions and power ---------------------------------------------------------------
    k_base = kill_baseline_channel(pr, _readout(om=[option_mass_gate_value(pr) / 2.0] * 4))
    k_base_ok = kill_baseline_channel(pr, ro)
    ck.add("kill_baseline_channel", "a disengaged BASELINE kills the phase before any knockout "
           "job is submitted", k_base["killed"] and not k_base_ok["killed"], 2)
    ck.add("kill_baseline_unevaluated", "an unscored baseline is UNEVALUATED, not passed",
           not kill_baseline_channel(pr, None)["evaluated"], 1)
    ck.add("kill_reference", "if the whole query span does not move, no narrower scope is "
           "submitted", kill_reference_scope(pr, False)["killed"]
           and not kill_reference_scope(pr, True)["killed"]
           and not kill_reference_scope(pr, None)["evaluated"], 3)
    ck.add("kill_scaffold", "a MOVING scaffold-only arm VOIDS the whole family",
           kill_scaffold_moved(pr, True)["killed"]
           and not kill_scaffold_moved(pr, False)["killed"], 2)
    caught = False
    try:
        gate_narrow_scopes(kill_reference_scope(pr, None))
    except Refusal:
        caught = True
    ck.add("order_enforced_unevaluated", "reading a narrower scope before the kill condition has "
           "been EVALUATED is refused", caught, 1)
    caught = False
    try:
        gate_narrow_scopes(kill_reference_scope(pr, False))
    except Refusal:
        caught = True
    ck.add("order_enforced_killed", "reading a narrower scope after the kill condition FIRED is "
           "refused", caught, 1)
    gate_narrow_scopes(kill_reference_scope(pr, True))
    ck.add("order_allows_when_clear", "the narrow scopes are readable once the reference moved",
           True, 1)

    fr = fraction_of_reference(pr, -3.0, -6.0)
    fr_no = fraction_of_reference(pr, -1.0, -6.0)
    ck.add("fraction_rule", "a scope reaching the declared fraction of the reference reproduces; "
           "one below it does not", fr["reproduces"] and not fr_no["reproduces"], 2,
           "%.4f vs %.4f at rule %.4f" % (fr["fraction"], fr_no["fraction"], fr["rule"]))
    caught = False
    try:
        fraction_of_reference(pr, -1.0, float(0))
    except Refusal:
        caught = True
    ck.add("fraction_of_zero", "a fraction of a zero reference is refused -- the kill condition "
           "applies, not a fraction", caught, 1)

    pw_ok = u3_power(pr, {("d%d" % i): (declared_mde(pr) + 0.001 * i) for i in range(30)})
    pw_bad = u3_power(pr, {("d%d" % i): (declared_mde(pr) * (1 if i % 2 else -1) * (i + 1))
                           for i in range(30)})
    ck.add("u3_power", "U3 measures the SD on VALIDATION domains and returns CANNOT ANSWER "
           "WITHOUT READING TEST below the bar as a CODE PATH",
           pw_ok["power_ok"] and not pw_bad["power_ok"]
           and "CANNOT ANSWER WITHOUT READING TEST" in pw_bad["decision"], 2,
           "sd_ok=%.4f sd_bad=%.4f" % (pw_ok["measured_between_domain_sd"],
                                       pw_bad["measured_between_domain_sd"]))

    # ---- success and verdict ------------------------------------------------------------------
    ids = family_member_ids(pr)
    # `ids[3]` is S_D, one of the three scopes PR059-D1 DEMOTED: its dose-matched random-row
    # control is not constructible, so conjunct 3 is UNEVALUABLE for it and it can NEVER produce
    # a POSITIVE. The four-conjunct fixture therefore uses a scope whose control EXISTS; the
    # demoted case is asserted separately, below, as the thing it now is.
    win, other = ids[2], ids[0]
    hr = holm_with_absent(pr, {win: 0.0001, other: 0.9})
    succ4 = evaluate_success(pr, True, [(win, fr)], hr, {win: True}, True)
    succ3 = evaluate_success(pr, True, [(win, fr)], hr, {win: False}, True)
    succ_none = evaluate_success(pr, True, [(win, fr_no)], hr, {win: True}, True)
    ck.add("conjunctive", "all four conditions together pass; any one failing does not",
           succ4["success"] and not succ3["success"]
           and succ3["n_passed"] == succ4["n_conditions"] - 1, succ4["n_conditions"])
    caught = False
    try:
        verdict(pr, succ4, False, [], True, forb)
    except Refusal:
        caught = True
    ck.add("verdict_unclean_liveness", "no verdict is emitted on unclean hook liveness", caught, 1)
    v_neg = verdict(pr, succ_none, True, [], True, forb)
    ck.add("negative_wording", "the declared negative is emitted in its MANDATORY wording",
           v_neg == MANDATORY_NEGATIVE_WORDING, 1)
    caught = False
    try:
        verdict(pr, succ_none, True, [], False, forb)
    except Refusal:
        caught = True
    ck.add("reference_did_not_move_is_void", "if the reference scope did not move the run is VOID "
           "or a kill, NOT a localisation negative", caught, 1)
    v_ca = verdict(pr, succ_none, True, ["the primary channel is disengaged"], True, forb)
    ck.add("cannot_answer_branch", "CANNOT ANSWER is an explicit branch and says it is not a null",
           v_ca.startswith("CANNOT ANSWER") and "NOT as a mechanism null" in v_ca, 1)
    v_pos = verdict(pr, succ4, True, [], True, forb)
    ck.add("positive_branch", "the positive verdict states its scope limits",
           v_pos.startswith("POSITIVE") and "Llama" in v_pos, 1)

    # ---- PR059-D7: THE VERDICT PATH, DRIVEN END TO END ON A CPU WITH NO RUN DIRECTORY -------
    _null = open(os.devnull, "w")

    def _cls(**kw):
        import contextlib
        with contextlib.redirect_stdout(_null), contextlib.redirect_stderr(_null):
            return decide(pr, _fake_obs(pr, **kw), forb)["verdict"]["class"]

    def _raises(fn):
        try:
            fn()
            return False
        except (Refusal, ZeroBinding, CannotAnswer, PreregError):
            return True

    os1 = o1_expected_sign(pr)
    ck.add("o1_expected_sign_is_PARSED_not_chosen",
           "O1's expected direction is READ OUT of the frozen file (it states it in prose, and "
           "this analyzer refuses to supply it)", os1["sign"] == -1 and os1["n_statements"] >= 2,
           os1["n_statements"], "sources=%s" % [h["path"] for h in os1["sources"]])
    csigns = conjunct_expected_signs(pr)
    ck.add("each_conjunct_has_ITS_OWN_expected_sign",
           "the four conjuncts do NOT share an expectation: a fixed sign, agreement with the "
           "reference, and two expected-NULLs -- so there is no scalar PHASE 9's defect could "
           "be repeated with",
           [csigns[c]["kind"] for c in CONJUNCT_IDS]
           == ["fixed_sign", "same_sign_as_reference", "expected_null", "expected_null"], 4)
    _swapped = OrderedDict(csigns)
    _swapped[CONJUNCT_IDS[0]] = csigns[CONJUNCT_IDS[2]]
    ck.add("a_conjunct_scored_against_ANOTHERS_sign_REFUSES",
           "conjunct 1 handed conjunct 3's expectation is caught BY NAME -- the PHASE 9 defect "
           "designed out rather than commented on",
           _raises(lambda: evaluate_success(pr, True, [], hr, {}, True,
                                            expected_signs=_swapped)), 1)
    ck.add("a_SHARED_scalar_expected_sign_REFUSES",
           "handing evaluate_success one sign for all four conjuncts is a refusal",
           _raises(lambda: evaluate_success(pr, True, [], hr, {}, True, expected_signs=-1)), 1)

    ck.add("verdict_path_reaches_POSITIVE", "decide() runs end to end and can emit a POSITIVE",
           _cls() == "POSITIVE", 1)
    ck.add("verdict_path_reaches_NEGATIVE",
           "no narrower scope reaching the fraction emits the MANDATORY negative wording",
           _cls(winner_delta=-1.0) == "NEGATIVE", 1)
    ck.add("verdict_path_reaches_CANNOT_ANSWER",
           "a disengaged primary channel is CANNOT ANSWER, never a mechanism null",
           _cls(cannot_answer_evidence={"option_mass_above_gate": False}) == "CANNOT_ANSWER", 1)
    ck.add("verdict_path_reaches_VOID_on_unclean_liveness",
           "no verdict is emitted on unclean liveness; the class is VOID and stays distinct "
           "from CANNOT_ANSWER and from NEGATIVE",
           _cls(liveness_clean=False) == "VOID", 1)
    ck.add("a_triggered_void_CLAUSE_is_also_VOID",
           "every `primary.void` clause is walked with a status, and a triggered one refuses "
           "the verdict just as unclean liveness does",
           _cls(void_evidence={"hook_fired": False}) == "VOID", 1)
    ck.add("VOID_CANNOT_ANSWER_NEGATIVE_are_three_distinct_classes",
           "the three cannot collapse into one another",
           len({_cls(), _cls(winner_delta=-1.0), _cls(liveness_clean=False),
                _cls(cannot_answer_evidence={"option_mass_above_gate": False})}) == 4, 4)

    # PR059-D1: a DEMOTED scope reaching the fraction is CANNOT ANSWER, never a positive.
    ck.add("a_DEMOTED_scope_cannot_pass_condition_3",
           "S_D/S_E/S_G have no constructible random-row control, so success condition 3 is "
           "UNEVALUABLE for them -- and unevaluable REFUSES a verdict rather than passing",
           _cls(winner="S_D", winner_delta=-4.0) == "CANNOT_ANSWER", 1)
    _cs = control_status_for_scope(pr, "S_D", True)
    ck.add("UNEVALUABLE_is_not_a_PASS_even_when_told_the_control_passed",
           "handing condition 3 a True for a demoted scope does NOT make it pass",
           _cs["status"] == "UNEVALUABLE" and not _cs["passed"], 1, _cs["reason"][:80])
    _cs_ok = control_status_for_scope(pr, "S_C", True)
    ck.add("a_scope_whose_control_EXISTS_is_still_evaluated",
           "the demotion is scoped to the three scopes that cannot build one, not applied "
           "wholesale", _cs_ok["status"] == "PASS" and _cs_ok["passed"], 1)
    ck.add("a_constructible_control_left_UNREAD_is_UNEVALUATED_not_passed",
           "'not measured' and 'measured and clean' are different verdicts",
           control_status_for_scope(pr, "S_C", None)["status"] == "UNEVALUATED", 1)

    # every clause of both declared lists is walked, and UNEVALUATED is not clean
    _vw = void_walk(pr, {k: True for _p, k in VOID_CLAUSE_KEYS})
    _cw = cannot_answer_walk(pr, {k: True for _p, k in CANNOT_ANSWER_CLAUSE_KEYS})
    ck.add("every_void_and_cannot_answer_clause_is_walked",
           "each clause of `primary.void` and `primary.cannot_answer` gets a status of its own",
           _vw["clean"] and _cw["clean"] and _vw["n"] >= 9 and _cw["n"] >= 4,
           _vw["n"] + _cw["n"])
    ck.add("an_UNEVALUATED_clause_is_NOT_clean",
           "a clause with no evidence is UNEVALUATED, and UNEVALUATED is not a satisfied clause",
           void_walk(pr, {})["n_unevaluated"] == _vw["n"] and not void_walk(pr, {})["clean"], 1)

    # Holm: a structurally absent member enters at p = 1.0 and m never shrinks
    _hr1 = holm_with_absent(pr, {ids[2]: 0.0001})
    ck.add("absent_members_enter_at_p_1_and_m_does_NOT_shrink",
           "S_B is DECLARED and UNCONSTRUCTIBLE; it enters Holm at p = 1.0 and the family size "
           "stays %d -- dropping it would make every surviving member easier to declare "
           "significant" % len(ids),
           _hr1["m"] == len(ids) and "S_B" in _hr1["absent_members_at_p1"]
           and _hr1["per_member"]["S_B"]["p"] == float(1), _hr1["m"])
    ck.add("a_shrunken_family_REFUSES",
           "reporting fewer members than the family declares is refused",
           _raises(lambda: refuse_shrunken_family(pr, ids[:-1])), 1)

    # PR059-D4, the consumer half
    _thin = _lr()
    _thin.pop("n_cells_edited_expected")
    ck.add("a_MISSING_liveness_field_RAISES_and_is_not_a_measured_zero",
           "PR059-D4: 'the producer never wrote this' and 'the hook edited zero cells' are "
           "opposite verdicts; the gate refuses to collapse them",
           _raises(lambda: liveness_gate([_thin], "u", pr)), 1)
    ck.add("a_field_PRESENT_and_zero_is_a_DEAD_HOOK_not_a_refusal",
           "the other half of the same distinction: present-and-zero is measured, and it is VOID",
           not liveness_gate([_lr(hook_fired_count=0)], "u", pr)["live"], 1)

    # PR059-D5, both derivations
    ck.add("PR059-D5_the_reference_scope_now_carries_its_nondemo_control",
           "`per_scope_nondemo_key_control` is declared 'for EVERY scope' and its draw pool "
           "excludes the query span entirely, so the reference is not exempt from it",
           len([a for a in build_arm_manifest(pr)
                if a.scope_id == ref and a.kind == "nondemo_control"])
           == n_nondemo_draws(pr) * len(primary_banks(pr)), 1)
    ck.add("PR059-D5_and_it_still_has_NO_random_row_control",
           "that one really is unbuildable at m == len(span), and PR059-D1 stands",
           not [a for a in build_arm_manifest(pr)
                if a.scope_id == ref and a.kind == "random_row_control"], 1)

    # ---- banks, arms, identity ------------------------------------------------------------------
    caught = False
    try:
        refuse_pooling_across_banks(primary_banks(pr))
    except Refusal:
        caught = True
    ck.add("no_bank_pooling", "the two codeword banks are a TRANSFER PAIR and pooling them into "
           "one p-value is refused",
           caught and refuse_pooling_across_banks(primary_banks(pr)[:1]) == primary_banks(pr)[0],
           2)
    caught = False
    try:
        refuse_descriptive_as_confirmatory(pr, descriptive_banks(pr)[0])
    except Refusal:
        caught = True
    ck.add("descriptive_not_confirmatory", "a knife/gun arm cannot be quoted as a mechanism "
           "result (installs in 0/113 and 1/113 domains on this channel)", caught,
           len(descriptive_banks(pr)))
    arms = build_arm_manifest(pr)
    ck.add("arm_manifest", "the manifest carries a baseline, the reference, every constructible "
           "family member and a bridge, per bank",
           {a.kind for a in arms} >= {"baseline", "scope", "bridge"}
           and {a.bank for a in arms} == set(primary_banks(pr)), len(arms),
           "kinds=%s" % sorted({a.kind for a in arms}))
    ck.add("manifest_order", "the baseline and the reference scope are ordered FIRST -- the kill "
           "condition reads them", arms[0].kind == "baseline" and arms[1].scope_id == ref, 2)
    _ident = analyzer_identity_gate(pr)
    ck.add("identity_gate", "artifacts.analyzer names THIS FILE -- the PR058-D1 defect designed "
           "out rather than repeated", _ident["match"], 1,
           "declared=%r actual=%r" % (_ident["declared"], _ident["actual"]))

    ck.report()
    print("\n[self-test] %d checks, %d failed" % (len(ck.rows), ck.n_fail))
    return 1 if ck.n_fail else 0


# ============================================================================================
# 20. MUTATION HARNESS -- checklist U6
# ============================================================================================
class _PreregStub(object):
    """A Prereg with ONE field corrupted. Nothing else changes."""

    def __init__(self, pr: Prereg, keys: Tuple[str, ...], value):
        self._pr = pr
        self._keys = tuple(keys)
        self._val = value
        self.obj = pr.obj
        self.path = pr.path + "#MUTANT"

    def require(self, *keys):
        if tuple(keys) == self._keys:
            return self._val
        return self._pr.require(*keys)


def _audit_or_raise(pr: Prereg):
    """An analyzer source carrying a declared gate value as a numeric literal must refuse."""
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


class _ObjStub(object):
    """A Prereg whose OBJECT is edited -- `_PreregStub` only intercepts `require()`, and
    `o1_expected_sign` deliberately reads the whole tree so it cannot be fooled by one key."""

    def __init__(self, pr: Prereg, drop: str = "", add: str = ""):
        import copy
        obj = copy.deepcopy(pr.obj)

        def _strip(node):
            if isinstance(node, dict):
                return {k: _strip(v) for k, v in node.items()}
            if isinstance(node, list):
                return [_strip(v) for v in node]
            if isinstance(node, str) and drop and drop in node.lower():
                return node.lower().replace(drop, "[direction statement removed]")
            return node

        self.obj = _strip(obj) if drop else obj
        if add:
            self.obj["_mutation"] = add
        self.path = pr.path + "#OBJ-MUTANT"
        self._pr = pr

    def require(self, *keys):
        return self._pr.require(*keys)


def _drop(rec: Dict[str, Any], key: str) -> Dict[str, Any]:
    out = dict(rec)
    out.pop(key, None)
    return out


def _decide_quiet(pr: Prereg, obs: Dict[str, Any], forb: Sequence[str],
                  require: str) -> Dict[str, Any]:
    """Run `decide()` with its printing suppressed and REFUSE unless the class is `require`.

    The mutation is "this observation still produced a verdict"; the refusal is what proves it
    did not.
    """
    import contextlib
    null = open(os.devnull, "w")
    with contextlib.redirect_stdout(null), contextlib.redirect_stderr(null):
        res = decide(pr, obs, forb)
    got = res["verdict"]["class"]
    if got != require:
        raise Refusal("the verdict class is %r, not %r -- the observation was REFUSED a %r "
                      "verdict" % (got, require, require))
    return res


def _assert_condition3_passes(pr: Prereg, scope_id: str) -> Dict[str, Any]:
    st = control_status_for_scope(pr, scope_id, True)
    if st["status"] != "PASS":
        raise Refusal("success condition 3 for scope %s is %s, not PASS: %s"
                      % (scope_id, st["status"], st["reason"]))
    return st


def _assert_walk_clean(walk: Dict[str, Any]) -> Dict[str, Any]:
    if not walk["clean"]:
        raise Refusal("%d of %d `%s` clause(s) are UNEVALUATED or triggered, and an UNEVALUATED "
                      "clause is not a satisfied one"
                      % (walk["n_unevaluated"] + walk["n_triggered"], walk["n"], walk["what"]))
    return walk


def mutate(pr: Prereg) -> int:
    """Every refusal must be REACHABLE, and each must fire for ITS OWN reason."""
    forb = forbidden_from_prereg(pr)
    scopes = declared_scopes(pr)
    span = query_span_rel_end(pr)
    ids = family_member_ids(pr)
    ref = reference_scope_id(pr)
    ro = _readout()
    ro.render(fh=open(os.devnull, "w"))
    base = {("d%d" % i): [float(0)] for i in range(10)}
    ko = {("d%d" % i): [-0.6] for i in range(10)}
    fr = fraction_of_reference(pr, -3.0, -6.0)
    fr_no = fraction_of_reference(pr, -1.0, -6.0)
    hr = holm_with_absent(pr, {ids[2]: 0.0001, ids[0]: 0.9})
    succ_ok = evaluate_success(pr, True, [(ids[2], fr)], hr, {ids[2]: True}, True)

    # Gates that RETURN a flag: the mutation must make that flag False.
    muts: "OrderedDict[str, Any]" = OrderedDict()
    muts["M1  dead hook (fired=0)"] = lambda: liveness_gate(
        [_lr(hook_fired_count=0)], "m", pr)["live"]
    muts["M2  SDPA on the loaded config"] = lambda: liveness_gate(
        [_lr(attn_implementation="sdpa")], "m", pr)["live"]
    muts["M3  zero realised dose"] = lambda: liveness_gate(
        [_lr(surface_span_n_tokens=0)], "m", pr)["live"]
    muts["M4  decode edits leaked"] = lambda: liveness_gate(
        [_lr(n_decode_edits=1)], "m", pr)["live"]
    muts["M5  realised != expected cells"] = lambda: liveness_gate(
        [_lr(n_cells_edited_realised=2)], "m", pr)["live"]
    muts["M6  no liveness records at all"] = lambda: liveness_gate([], "m", pr)["live"]
    muts["M7  bridge presented as a live arm"] = lambda: liveness_gate(
        [_lr(enabled=False, hook_fired_count=0, n_prefill_edits=0, n_cells_edited_realised=0,
             n_forward=3)], "m", pr)["live"]
    muts["M8  realised rows != declared rel_end"] = lambda: assert_realised_equals_declared(
        [_lr(seq_len=200, surface_span_positions=[191])], [-10])["ok"]
    muts["M9  realised token != map decoding"] = lambda: assert_realised_equals_declared(
        [_lr(surface_span_decoded=[" basket"])], [-10],
        decoded_by_rel_end={-10: " button"})["ok"]
    muts["M10 absolute index reused"] = lambda: audit_end_relative(
        [_lr(seq_len=200, surface_span_positions=[190]),
         _lr(seq_len=237, surface_span_positions=[190])], [-10])["ok"]
    muts["M11 identical control-band hashes"] = lambda: control_band_gate(
        ["z"] * n_random_row_draws(pr), n_random_row_draws(pr))["ok"]
    muts["M12 control band with zero draws"] = lambda: control_band_gate(
        [], n_random_row_draws(pr))["ok"]
    muts["M13 bridge does not reproduce"] = lambda: disabled_bridge_gate(
        "aa", "bb", float(0))["ok"]
    muts["M14 bridge moves the hidden state"] = lambda: disabled_bridge_gate(
        "aa", "aa", 1e-3)["ok"]
    muts["M15 unequal per-arm populations"] = lambda: assert_equal_populations(
        {"a": ["x", "y"], "b": ["x"]})["ok"]
    muts["M16 disengaged arm not caught"] = lambda: engagement_gate(
        _readout(om=[option_mass_gate_value(pr) / 2.0] * 4), pr)["engaged"]
    muts["M17 disengaged baseline not killed"] = lambda: not kill_baseline_channel(
        pr, _readout(om=[option_mass_gate_value(pr) / 2.0] * 4))["killed"]
    muts["M18 unscored baseline read as passed"] = lambda: kill_baseline_channel(
        pr, None)["evaluated"]
    muts["M19 dead reference read as passed"] = lambda: not kill_reference_scope(
        pr, False)["killed"]
    muts["M20 moving scaffold not VOID"] = lambda: not kill_scaffold_moved(pr, True)["killed"]
    muts["M21 below-fraction scope reproduces"] = lambda: fraction_of_reference(
        pr, -1.0, -6.0)["reproduces"]
    muts["M22 three of four conditions"] = lambda: evaluate_success(
        pr, True, [(ids[2], fr)], hr, {ids[2]: False}, True)["success"]
    muts["M23 control reproduces the scope"] = lambda: evaluate_success(
        pr, True, [(ids[2], fr)], hr, {ids[2]: True}, False)["success"]
    muts["M24 no scope reaches the fraction"] = lambda: evaluate_success(
        pr, True, [(ids[2], fr_no)], hr, {ids[2]: True}, True)["success"]
    muts["M25 reference did not move"] = lambda: evaluate_success(
        pr, False, [(ids[2], fr)], hr, {ids[2]: True}, True)["success"]
    muts["M26 underpowered U3 proceeds"] = lambda: u3_power(
        pr, {("d%d" % i): (declared_mde(pr) * (1 if i % 2 else -1) * (i + 1))
             for i in range(30)})["power_ok"]
    muts["M27 resolver failure tolerated"] = lambda: not resolver_failure_gate(
        50, 100, pr)["cannot_answer"]
    muts["M28 empty installing stratum ok"] = lambda: not empty_installing_stratum_gate(
        {"n_installing": 0}, "basket_knife")["cannot_answer"]
    muts["M29 leaky primary-channel rows"] = lambda: concept_word_absence_gate(
        [{"prompt_id": "x", "full_prompt": "a bomb here", "n_concept_occurrences": 1}],
        ["bomb"])["ok"]
    muts["M30 non-constructible control passes"] = lambda: random_row_control_constructible(
        pr, "S_E", scopes["S_E"]["rel_end_rows"], span)["constructible"]
    muts["M31 null-dose arm ledgered nothing"] = lambda: null_dose_arm_gate(pr, 0, [])["ok"]

    # Gates that RAISE.
    raisers: "OrderedDict[str, Any]" = OrderedDict()
    raisers["M32 row-level permutation attempt"] = lambda: domain_group_permutation(
        base, ko, pr, unit="row")
    raisers["M33 permutation over zero domains"] = lambda: domain_group_permutation({}, {}, pr)
    raisers["M34 zero-row population bind"] = lambda: bind_rows(pr, {}, {})
    raisers["M35 bind on `condition` (A-039)"] = lambda: bind_rows(
        pr, _fake_bank(pr), {"dom%d" % i: "train" for i in range(4)},
        selector_field=FORBIDDEN_SELECTOR_FIELD)
    raisers["M36 threshold from a literal"] = lambda: assert_gate_from_prereg(
        "primary.alpha", alpha(pr) * 2.0, pr)
    raisers["M37 undeclared gate name"] = lambda: assert_gate_from_prereg(
        "primary.made_up_gate", 1.0, pr)
    raisers["M38 an analyzer source with a gate literal"] = lambda: _audit_or_raise(pr)
    raisers["M39 delta printed without its readout"] = lambda: render_delta(
        ScopeDelta(scope_id="S_C", arm_id="u", readout=_readout(), control={"ok": True},
                   per_domain={"a": 0.1}, stats={}), p_floor(pr), fh=open(os.devnull, "w"))
    raisers["M40 analyzer path conflict"] = lambda: analyzer_identity_gate(
        _PreregStub(pr, ("artifacts", "analyzer"), "scripts/not_this_analyzer.py"))
    raisers["M41 scope without its control"] = lambda: render_delta(
        ScopeDelta(scope_id="S_C", arm_id="u", readout=ro, control=None,
                   per_domain={"a": 0.1}, stats={}), p_floor(pr), fh=open(os.devnull, "w"))
    raisers["M42 scope against a VOID control"] = lambda: assert_scope_has_its_control(
        "S_C", {"ok": False, "reason": "identical hashes"})
    raisers["M43 dropped family member"] = lambda: refuse_shrunken_family(pr, ids[:-1])
    raisers["M44 p-value for a non-member"] = lambda: holm_with_absent(pr, {"S_Z": 0.01})
    raisers["M45 Holm over an empty family"] = lambda: holm({}, alpha(pr))
    raisers["M46 display channel as primary"] = lambda: refuse_display_channel_as_primary(
        pr, display_channel(pr))
    raisers["M47 display-channel fallback"] = lambda: refuse_display_fallback(pr, False)
    raisers["M48 descriptive arm as mechanism"] = lambda: refuse_descriptive_as_confirmatory(
        pr, descriptive_banks(pr)[0])
    raisers["M49 two banks pooled"] = lambda: refuse_pooling_across_banks(primary_banks(pr))
    raisers["M50 doses pooled"] = lambda: refuse_dose_pooling([4, 8])
    raisers["M51 dose-0 logodds interpreted"] = lambda: null_dose_arm_gate(pr, 10, [0.3])
    raisers["M52 verdict on unclean liveness"] = lambda: verdict(
        pr, succ_ok, False, [], True, forb)
    raisers["M53 verdict when the reference did not move"] = lambda: verdict(
        pr, succ_ok, True, [], False, forb)
    # ---- PR059-D7: the five new refusals the verdict path had to grow ---------------------
    _sw = OrderedDict(conjunct_expected_signs(pr))
    _sw[CONJUNCT_IDS[0]] = conjunct_expected_signs(pr)[CONJUNCT_IDS[2]]
    raisers["M81 a conjunct scored against ANOTHER outcome's sign"] = \
        lambda: evaluate_success(pr, True, [(ids[2], fr)], hr, {ids[2]: True}, True,
                                 expected_signs=_sw)
    raisers["M82 ONE shared expected_sign for all four conjuncts"] = \
        lambda: evaluate_success(pr, True, [(ids[2], fr)], hr, {ids[2]: True}, True,
                                 expected_signs=-1)
    raisers["M83 a verdict emitted on unclean liveness (via decide)"] = \
        lambda: _decide_quiet(pr, _fake_obs(pr, liveness_clean=False), forb, require="POSITIVE")
    raisers["M84 a triggered `void` clause emitting a verdict anyway"] = \
        lambda: _decide_quiet(pr, _fake_obs(pr, void_evidence={"hook_fired": False}), forb,
                              require="POSITIVE")
    raisers["M85 an absent Holm member DROPPED, shrinking the family"] = \
        lambda: refuse_shrunken_family(pr, ids[:-1])
    raisers["M86 Holm run over a family SMALLER than the declared one"] = \
        lambda: holm({i: 0.001 for i in ids}, alpha(pr), m=len(ids) - 1)
    raisers["M87 a DEMOTED scope passing success condition 3"] = \
        lambda: _assert_condition3_passes(pr, "S_D")
    raisers["M88 a demoted scope's win reported as a POSITIVE"] = \
        lambda: _decide_quiet(pr, _fake_obs(pr, winner="S_D", winner_delta=-4.0), forb,
                              require="POSITIVE")
    raisers["M89 a MISSING liveness field read as a measured zero"] = \
        lambda: liveness_gate([_drop(_lr(), "n_cells_edited_expected")], "m", pr)
    raisers["M90 a MISSING hook_fired_count read as a measured zero"] = \
        lambda: liveness_gate([_drop(_lr(), "hook_fired_count")], "m", pr)
    raisers["M91 a `void` clause with NO evidence key in this analyzer"] = \
        lambda: _clause_walk(["a brand new way for this phase to be void"], VOID_CLAUSE_KEYS,
                             {}, "void")
    raisers["M92 an UNEVALUATED cannot_answer clause treated as clean"] = \
        lambda: _assert_walk_clean(cannot_answer_walk(pr, {}))
    raisers["M93 O1's expected direction supplied by the analyzer instead of the file"] = \
        lambda: o1_expected_sign(_ObjStub(pr, drop="knockout predicted to lower"))
    raisers["M94 the frozen file stating TWO OPPOSITE expected directions for O1"] = \
        lambda: o1_expected_sign(_ObjStub(pr, add="a knockout predicted to RAISE the installed "
                                                  "reading"))
    raisers["M54 forbidden mandate-33 wording"] = lambda: assert_sayable(
        "our K=7 proves the bomb token is the mechanism", forb)
    raisers["M55 absolute (non-negative) offsets"] = lambda: parse_rel_end_spec([5, 6])
    raisers["M56 selector outside the query span"] = lambda: surface_span_from_rel_end(
        [-10], 200, query_span_positions=list(range(0, 100)))
    raisers["M57 empty scope run as an arm"] = lambda: surface_span_from_rel_end([], 200)
    raisers["M58 control draw larger than the pool"] = lambda: random_row_control_draw(
        pr, "S_E", scopes["S_E"]["rel_end_rows"], 0, span)
    raisers["M59 dose-matched control for a 0-row scope"] = lambda: random_row_control_draw(
        pr, "S_B", [], 0, span)
    raisers["M60 installation as a post-hoc exclusion"] = lambda: \
        refuse_installation_as_exclusion(["dom0"])
    raisers["M61 a domain with no stratum dropped"] = lambda: stratify_by_installation(
        {"a": 1.0, "b": 2.0}, {"a": 1.0}, installation_cut(pr))
    raisers["M62 narrow scope read before the kill"] = lambda: gate_narrow_scopes(
        kill_reference_scope(pr, None))
    raisers["M63 narrow scope read after the kill fired"] = lambda: gate_narrow_scopes(
        kill_reference_scope(pr, False))
    raisers["M64 fraction of a zero reference"] = lambda: fraction_of_reference(
        pr, -1.0, float(0))
    raisers["M65 U3 over <2 validation domains"] = lambda: u3_power(pr, {"d0": 0.1})
    raisers["M66 U3 with a zero measured SD"] = lambda: u3_power(
        pr, {("d%d" % i): 0.1 for i in range(10)})
    raisers["M67 U3 SD pre-filled in the frozen file"] = lambda: u3_power(
        _PreregStub(pr, ("power", "mde", "in_semantic_logodds_nats"), 1.0),
        {("d%d" % i): 0.1 * i for i in range(10)})
    raisers["M68 scope n_rows disagrees with rel_end"] = lambda: declared_scopes(
        _PreregStub(pr, ("scopes", "family"),
                    [{"id": "S_X", "rel_end_rows": [-1, -2], "n_rows": 5}]))
    raisers["M69 exclusion with no whole_population flag"] = lambda: whole_population_exclusions(
        _PreregStub(pr, ("population", "preregistered_exclusions"),
                    [{"domain": "x", "reason": "prose only"}]))
    raisers["M70 reference scope inside its own family"] = lambda: reference_scope_id(
        _PreregStub(pr, ("multiplicity", "families"),
                    [{"name": FAMILY_NAME, "members": ["%s x" % ref]}]))
    raisers["M71 count disagreement in the leakage recount"] = lambda: concept_word_absence_gate(
        [{"prompt_id": "x", "full_prompt": "a bomb here", "n_concept_occurrences": 0}], ["bomb"])
    raisers["M72 argmax rate over unequal arms"] = lambda: argmax_switch_rate(["a"], ["a", "b"])
    raisers["M73 readout with no option_mass"] = lambda: ArmReadout(
        arm_id="m", scope_id="S_C", n_rows=0, n_domains=0, option_mass=[], argmax_answers=["a"])
    raisers["M74 readout with no argmax answers"] = lambda: ArmReadout(
        arm_id="m", scope_id="S_C", n_rows=1, n_domains=1, option_mass=[0.2], argmax_answers=[])
    raisers["M75 delta with no readout object"] = lambda: ScopeDelta(
        scope_id="S_C", arm_id="u", readout=None, control={"ok": True}, per_domain={"a": 0.1})
    raisers["M76 delta over zero domains"] = lambda: ScopeDelta(
        scope_id="S_C", arm_id="u", readout=ro, control={"ok": True}, per_domain={})
    raisers["M77 realised-row audit over zero records"] = lambda: \
        assert_realised_equals_declared([], [-10])
    raisers["M78 realised rows not persisted at all"] = lambda: \
        assert_realised_equals_declared([{"prompt_id": "x"}], [-10])
    raisers["M79 decoded tokens not persisted"] = lambda: assert_realised_equals_declared(
        [{"prompt_id": "x", "seq_len": 200, "surface_span_positions": [190]}], [-10],
        decoded_by_rel_end={-10: " button"})
    raisers["M80 resolver gate over zero rows"] = lambda: resolver_failure_gate(0, 0, pr)
    # DCS-PR-065: the stop-scope policy REFUSES rather than defaulting. Six ways to make an
    # amendment silently permit something, each of which must fire for its own reason.
    _a3 = load_gate_policy_amendment()
    _p3 = _a3["option_mass_gate_policy"]
    _rf = reference_scope_id(pr)
    raisers["M91 a below-gate arm with NO amendment loaded"] = lambda: below_gate_disposition(
        pr, None, "scope", _rf)
    raisers["M92 an amendment with no option_mass_gate_policy"] = lambda: below_gate_disposition(
        pr, {"id": "X"}, "scope", _rf)
    raisers["M93 the policy restates the gate at a DIFFERENT value"] = lambda: (
        below_gate_disposition(pr, {"id": "X", "option_mass_gate_policy":
                                    dict(_p3, gate_value=option_mass_gate_value(pr) * 3.0)},
                               "scope", _rf))
    raisers["M94 the policy RE-SCOPES the gate to the baseline"] = lambda: (
        below_gate_disposition(pr, {"id": "X", "option_mass_gate_policy":
                                    dict(_p3, gate_scope="baseline_only")}, "scope", _rf))
    raisers["M95 the policy reads the MARGIN"] = lambda: (
        below_gate_disposition(pr, {"id": "X", "option_mass_gate_policy":
                                    dict(_p3, stop_scope_depends_on_margin=True)}, "scope", _rf))
    raisers["M96 the policy relaxes the BASELINE gate"] = lambda: (
        below_gate_disposition(pr, {"id": "X", "option_mass_gate_policy":
                                    dict(_p3, baseline_gate_is_not_relaxed=False)}, "scope", _rf))
    raisers["M97 an arm role with no declared disposition"] = lambda: (
        below_gate_disposition(pr, {"id": "X", "option_mass_gate_policy":
                                    dict(_p3, below_gate_disposition_by_arm_role={})},
                               "scope", _rf))
    raisers["M98 a below-gate arm may close ANOTHER bank"] = lambda: (
        below_gate_disposition(pr, {"id": "X", "option_mass_gate_policy":
                                    dict(_p3, cross_bank_isolation=False)}, "scope", _rf))
    raisers["M99 a below-gate arm reported without its option mass"] = lambda: (
        below_gate_disposition(pr, {"id": "X", "option_mass_gate_policy":
                                    dict(_p3, must_travel_with_every_derived_number=False)},
                               "scope", _rf))
    raisers["M100 the policy uses a DIFFERENT gate statistic"] = lambda: (
        below_gate_disposition(pr, {"id": "X", "option_mass_gate_policy":
                                    dict(_p3, gate_statistic="mean")}, "scope", _rf))

    print("=== %s mutation harness (U6): every refusal must be REACHABLE ===" % PR_ID)
    _REFUSALS = (Refusal, ZeroBinding, PreregError, CannotAnswer)
    n_red = 0
    for name, fn in muts.items():
        try:
            passed = bool(fn())
        except _REFUSALS as e:
            n_red += 1
            print("  RED    %-46s -> refusal: %s" % (name, str(e)[:64].replace("\n", " ")))
            continue
        red = not passed
        n_red += red
        print("  %s  %-46s -> gate says ok=%s%s"
              % ("RED  " if red else "GREEN", name, passed,
                 "" if red else "   <-- THIS REFUSAL IS UNREACHABLE"))
    for name, fn in raisers.items():
        try:
            fn()
            print("  GREEN  %-46s -> NO REFUSAL RAISED   <-- UNREACHABLE" % name)
        except _REFUSALS as e:
            n_red += 1
            print("  RED    %-46s -> refusal: %s" % (name, str(e)[:64].replace("\n", " ")))
    total = len(muts) + len(raisers)
    print("[mutate] %d/%d mutations produced a refusal" % (n_red, total))
    if n_red != total:
        print("  AN UNREACHABLE REFUSAL IS NOT A GUARD.", file=sys.stderr)
        return 1
    return 0


# ============================================================================================
# 21. THE ANALYSIS
# ============================================================================================
# ============================================================================================
# 21b. PR059-D7 -- THE VERDICT PATH
#
# Split in two ON PURPOSE. `observe()` does the I/O -- it reads run directories and measures.
# `decide()` is PURE: it takes measured quantities and emits the conjunct table, the clause
# walks, Holm and the verdict. Only `decide()` can turn numbers into a claim, and because it
# touches no disk it is driven END TO END by --self-test and --mutate on a machine with no GPU
# and no run directories. An analyzer whose verdict logic can only be exercised by a completed
# GPU run is an analyzer whose verdict logic is never exercised (PR059-D7, and PHASE 9's A4).
# ============================================================================================
ARM_RESULTS = "results.jsonl"


def read_arm_rows(run_dir: str, pr: Prereg) -> Dict[str, Dict[str, Any]]:
    """One arm's scored rows, keyed by prompt_id. REFUSES on an incomplete or empty run."""
    p = os.path.join(run_dir, ARM_RESULTS)
    if not os.path.exists(os.path.join(run_dir, "DONE.json")):
        raise Refusal("%s carries no DONE.json; a partial run is not a result" % run_dir)
    if not os.path.exists(p):
        raise Refusal("%s carries no %s, so this arm scored nothing" % (run_dir, ARM_RESULTS))
    out: Dict[str, Dict[str, Any]] = {}
    want_kind = primary_channel(pr)
    with open(p) as f:
        for line in f:
            if not line.strip():
                continue
            d = json.loads(line)
            if str(d.get("query_kind") or want_kind) != want_kind:
                continue
            out[str(d["prompt_id"])] = d
    if not out:
        raise ZeroBinding("%s bound ZERO rows on the primary channel %r" % (run_dir, want_kind))
    return out


def paired_domain_delta(treat: Dict[str, Dict[str, Any]], base: Dict[str, Dict[str, Any]],
                        assign: Dict[str, str]) -> Dict[str, List[float]]:
    """Per-domain lists of the PAIRED per-row delta, within prompt_id. `L-N11`: the two arms must
    cover EXACTLY the same prompt_ids, or they are not the same population and the pairing is a
    comparison of two different sets wearing one name."""
    only_t, only_b = sorted(set(treat) - set(base)), sorted(set(base) - set(treat))
    if only_t or only_b:
        raise Refusal(
            "UNEQUAL PER-ARM POPULATIONS (primary.void): %d prompt_id(s) only in the scope arm "
            "and %d only in the baseline. `L-N11` requires the ledgered exclusions replayed into "
            "EVERY arm; a paired delta over a differing set is not a paired delta."
            % (len(only_t), len(only_b)))
    per: "OrderedDict[str, List[float]]" = OrderedDict()
    for pid, tr in sorted(treat.items()):
        dom = assign.get(pid) or tr.get("domain")
        if dom is None:
            raise Refusal("row %r carries no domain and the split manifest does not assign one; "
                          "the independence unit is the DOMAIN and cannot be bound" % pid)
        per.setdefault(str(dom), []).append(
            float(tr["semantic_logodds"]) - float(base[pid]["semantic_logodds"]))
    if not per:
        raise ZeroBinding("the paired delta bound ZERO domains")
    return per


def _readout_from_rows(arm_id: str, scope_id: str, rows: Dict[str, Dict[str, Any]],
                       assign: Dict[str, str]) -> ArmReadout:
    """The engagement distribution for ONE arm. Fields are read WITHOUT defaults: an arm whose
    rows carry no `option_mass` has not measured engagement, and on this channel that is not a
    detail -- `primary._largest_risk` makes the readout the precondition of every delta."""
    vals, ans = [], []
    for pid, r in sorted(rows.items()):
        for k in ("option_mass", "argmax_answer"):
            if k not in r:
                raise Refusal("row %r of arm %r carries no %r. The readout is the precondition "
                              "of every delta on this weakly engaged channel and is never "
                              "defaulted." % (pid, arm_id, k))
        vals.append(float(r["option_mass"]))
        ans.append(str(r["argmax_answer"]))
    doms = {str(assign.get(pid) or rows[pid].get("domain")) for pid in rows}
    return ArmReadout(arm_id=arm_id, scope_id=scope_id, n_rows=len(vals), n_domains=len(doms),
                      option_mass=vals, argmax_answers=ans,
                      logodds=[float(r["semantic_logodds"]) for r in rows.values()])


def observe(pr: Prereg, arms: Sequence[ArmSpec], found: Dict[str, str],
            assign: Dict[str, str], liveness_clean: bool) -> Dict[str, Any]:
    """Measure everything `decide()` needs, from the run directories. NOTHING is decided here."""
    by_id = {a.arm_id: a for a in arms}
    ref, scaf = reference_scope_id(pr), scaffold_scope_id(pr)
    banks = sorted({a.bank for a in arms if a.confirmatory})
    out: Dict[str, Any] = {"liveness_clean": bool(liveness_clean), "banks": OrderedDict()}
    for bank in banks:
        base_id = next((a.arm_id for a in arms
                        if a.bank == bank and a.kind == "baseline"), None)
        if base_id is None or base_id not in found:
            raise Refusal("bank %r has no COMPLETE untouched baseline arm. Every number this "
                          "phase reports is a PAIRED delta against it; without it there is "
                          "nothing to subtract and no readout to gate on." % bank)
        base_rows = read_arm_rows(found[base_id], pr)
        b: Dict[str, Any] = {
            "baseline_readout": _readout_from_rows(base_id, "S_0", base_rows, assign),
            "scopes": OrderedDict(), "reference": None, "scaffold": None}
        for a in arms:
            if a.bank != bank or a.kind not in ("scope",) or a.arm_id not in found:
                continue
            rows = read_arm_rows(found[a.arm_id], pr)
            per = paired_domain_delta(rows, base_rows, assign)
            base_per = paired_domain_delta(base_rows, base_rows, assign)
            st = domain_group_permutation(base_per, per, pr)
            rec = {"scope_id": a.scope_id, "arm_id": a.arm_id,
                   "readout": _readout_from_rows(a.arm_id, a.scope_id, rows, assign),
                   "per_domain": st["per_domain_delta"], "stats": st,
                   "delta": st["observed_delta"],
                   "p": st["permutation"]["p"], "floor": st["permutation"]["floor"],
                   "formatted": st["permutation"]["formatted"]}
            # each scope's OWN dose-matched random-row control, where one exists
            ctrl = [c for c in arms if c.bank == bank and c.scope_id == a.scope_id
                    and c.kind == "random_row_control"]
            shas, cdel = [], []
            for c in ctrl:
                if c.arm_id not in found:
                    continue
                crows = read_arm_rows(found[c.arm_id], pr)
                shas.append(hashlib.sha256(
                    json.dumps(sorted((k, v.get("argmax_answer"))
                                      for k, v in crows.items())).encode()).hexdigest())
                cst = domain_group_permutation(base_per,
                                               paired_domain_delta(crows, base_rows, assign), pr)
                cdel.append(cst["observed_delta"])
            rec["control"] = ({"n_draws": len(cdel), "deltas": cdel, "output_sha256": shas,
                               "band": control_interval(cdel, alpha(pr)) if len(cdel) > 1
                               else None,
                               "distinct": control_band_gate(shas, n_random_row_draws(pr))
                               if shas else None}
                              if ctrl else None)
            b["scopes"][a.scope_id] = rec
            if a.scope_id == ref:
                b["reference"] = rec
            if a.scope_id == scaf:
                b["scaffold"] = rec
        out["banks"][bank] = b
    return out


def decide(pr: Prereg, obs: Dict[str, Any], forbidden: Sequence[str]) -> Dict[str, Any]:
    """PURE. Emit the conjunct table, both clause walks, Holm, and the verdict -- per bank.

    `refuse_pooling_across_banks`: the two codeword banks are a TRANSFER PAIR and are never
    pooled, so this loops banks and produces one verdict each rather than one verdict.
    """
    ref, scaf = reference_scope_id(pr), scaffold_scope_id(pr)
    rule = half_of_reference_rule(pr)
    floor = p_floor(pr)
    out: Dict[str, Any] = {"banks": OrderedDict()}
    verdicts = []
    for bank, b in obs["banks"].items():
        print("\n=== %s -- BANK %s (never pooled with any other bank) ===" % (FAMILY_NAME, bank))

        # ---- 1. THE READOUT COMES FIRST, ALWAYS ------------------------------------------
        b["baseline_readout"].render()
        eg = engagement_gate(b["baseline_readout"], pr)
        ca_ev = dict(b.get("cannot_answer_evidence") or {})
        ca_ev.setdefault("option_mass_above_gate", not eg["cannot_answer"])
        ca_ev.update(obs.get("cannot_answer_evidence") or {})
        void_ev = dict(obs.get("void_evidence") or {})
        void_ev.setdefault("no_row_level_p", True)          # only a domain-level test exists here
        void_ev.setdefault("equal_populations", True)       # bound by paired_domain_delta

        # ---- 2. THE KILL CONDITIONS, IN THE FROZEN ORDER, EACH WITH A STATUS -------------
        k2 = kill_baseline_channel(pr, b["baseline_readout"])
        refm = None if b["reference"] is None else bool(
            b["reference"]["p"] <= alpha(pr)
            and _sgn(b["reference"]["delta"]) == int(o1_expected_sign(pr)["sign"]))
        k1 = kill_reference_scope(pr, refm)
        scafm = None if b["scaffold"] is None else bool(b["scaffold"]["p"] <= alpha(pr))
        k3 = kill_scaffold_moved(pr, scafm)
        for tag, k in (("kill1_reference", k1), ("kill2_baseline_engagement", k2),
                       ("kill3_scaffold_moved", k3)):
            print("  KILL  %-26s evaluated=%s killed=%s %s"
                  % (tag, k.get("evaluated"), k.get("killed"), (k.get("reason") or "")[:110]))
        gate_narrow_scopes(k1)                      # CONTROL FLOW, not a paragraph

        # ---- 3. EVERY DELTA, BESIDE ITS READOUT, WITH ITS p AND ITS FLOOR ----------------
        if b["reference"] is not None:
            r = b["reference"]
            print("  REF   %s delta=%+.6g  %s  [attainable floor %.4e]"
                  % (ref, r["delta"], r["formatted"], floor))
        fracs, pvals, reported = [], {}, []
        members = set(family_member_ids(pr))
        for sid, rec in b["scopes"].items():
            if sid == ref:
                continue
            rec["readout"].render()
            d = ScopeDelta(scope_id=sid, arm_id=rec["arm_id"], readout=rec["readout"],
                           control=rec.get("control"), per_domain=rec["per_domain"],
                           stats=rec["stats"])
            try:
                render_delta(d, floor)
            except Refusal as e:
                print("  DELTA %s NOT RENDERED: %s" % (sid, e))
            if sid in members:
                pvals[sid] = float(rec["p"])
                reported.append(sid)
            if b["reference"] is not None:
                fr = fraction_of_reference(pr, rec["delta"], b["reference"]["delta"])
                rec["fraction"] = fr
                print("        fraction of %s = %.4f (rule %.4g) reproduces=%s same_sign=%s "
                      "p=%s [floor %.4e]"
                      % (ref, fr["fraction"], rule, fr["reproduces"], fr["same_sign"],
                         rec["formatted"], floor))
                if sid in members:
                    fracs.append((sid, fr))

        # ---- 4. HOLM OVER THE DECLARED FAMILY; ABSENT MEMBERS ENTER AT p = 1.0 ----------
        # S_B is the worked example: DECLARED, UNCONSTRUCTIBLE, and it enters at p = 1.0. It is
        # never dropped -- dropping it would shrink m and make every surviving member easier to
        # declare significant.
        holm_res = holm_with_absent(pr, pvals)
        refuse_shrunken_family(pr, list(holm_res["per_member"]))
        print("  HOLM  family=%s m=%d alpha=%g; absent-at-p=1.0: %s"
              % (FAMILY_NAME, holm_res["m"], holm_res["alpha"],
                 holm_res["absent_members_at_p1"]))
        for mid, mv in holm_res["per_member"].items():
            print("        %-6s p=%-12s threshold=%.6g reject=%s [attainable floor %.4e]"
                  % (mid, ("%.6g" % mv["p"]), mv["threshold"], mv["reject"], floor))

        # ---- 5. THE CONJUNCTIVE RULE, EACH CONDITION SCORED SEPARATELY ------------------
        # Conjunct 3's INPUT: did this scope's OWN dose-matched random-row control reproduce it?
        # Measured on the SAME rule the scope was measured on -- the control's own mean delta as
        # a fraction of the reference -- so "reproduces" means the same thing for both. `None`
        # here is NOT a pass: it becomes UNEVALUATED (or, for a demoted scope, UNEVALUABLE) in
        # `control_status_for_scope`, and either one refuses a verdict for that scope.
        ctrl_ok = {}
        for sid, rec in b["scopes"].items():
            c = rec.get("control")
            if (not c) or (not c.get("deltas")) or b["reference"] is None:
                ctrl_ok[sid] = None
                continue
            distinct = bool((c.get("distinct") or {}).get("ok"))
            cmean = sum(c["deltas"]) / len(c["deltas"])
            cfr = fraction_of_reference(pr, cmean, b["reference"]["delta"])
            rec["control_fraction"] = cfr
            ctrl_ok[sid] = bool(distinct and not cfr["reproduces"])
            print("        CONTROL %s: %d draw(s), mean delta=%+.6g, fraction of %s = %.4f "
                  "(rule %.4g), %d DISTINCT output hash(es) required by L-N7 = %s -> %s"
                  % (sid, len(c["deltas"]), cmean, ref, cfr["fraction"], rule,
                     n_random_row_draws(pr), distinct,
                     "does NOT reproduce" if ctrl_ok[sid] else "REPRODUCES / not distinct"))
            if c.get("band"):
                print("        CONTROL %s interval: mean=%+.6g CI=[%+.6g, %+.6g] -- "
                      "'p > alpha' is not a passed control; the interval is the result"
                      % (sid, c["band"]["mean"], c["band"]["ci_low"], c["band"]["ci_high"]))
        succ = evaluate_success(
            pr, bool(refm), fracs, holm_res, ctrl_ok, not bool(scafm),
            reference_delta=(None if b["reference"] is None else b["reference"]["delta"]),
            scaffold_delta=(None if b["scaffold"] is None else b["scaffold"]["delta"]))
        print("  SUCCESS RULE (CONJUNCTIVE -- %s):" % succ["_conjunctive"])
        for row in succ["conditions"]:
            print("    [%s] %-58s expected=%s(sign=%s)"
                  % (row["status"].ljust(11), row["conjunct"], row["expected"],
                     row["expected_sign"]))
            print("            %s" % row["condition"])
            print("            %s" % row["detail"])

        # ---- 6. EVERY `void` AND `cannot_answer` CLAUSE, WALKED, EACH WITH A STATUS -----
        vw = void_walk(pr, void_ev)
        cw = cannot_answer_walk(pr, ca_ev)
        for w in (vw, cw):
            print("  %s CLAUSES (%d; %d triggered, %d UNEVALUATED -- UNEVALUATED IS NOT CLEAN):"
                  % (w["what"].upper(), w["n"], w["n_triggered"], w["n_unevaluated"]))
            for row in w["clauses"]:
                print("    [%-11s] %s" % (row["status"], row["clause"][:104]))

        # ---- 7. THE VERDICT, WITH ITS CLASS ---------------------------------------------
        reasons = list(cw["triggered"]) + [
            "a `%s` clause is UNEVALUATED (%s), and an unevaluated clause is not a satisfied one"
            % (cw["what"], r["clause"][:70])
            for r in cw["clauses"] if r["status"] == "UNEVALUATED"]
        rec = verdict_record(pr, succ, bool(obs["liveness_clean"]) and vw["clean"],
                             reasons, bool(refm), forbidden)
        print("  VERDICT CLASS: %s   (VOID / CANNOT_ANSWER / NEGATIVE are three different "
              "statements about the world and are never collapsed)" % rec["class"])
        if rec.get("refuses"):
            print("  REFUSING TO EMIT A VERDICT: %s" % rec["reason"], file=sys.stderr)
        else:
            print("  VERDICT: %s" % rec["sentence"])
        out["banks"][bank] = {"success": succ, "holm": holm_res, "void_walk": vw,
                              "cannot_answer_walk": cw, "verdict": rec,
                              "kills": {"reference": k1, "baseline": k2, "scaffold": k3}}
        verdicts.append(rec)
    classes = sorted({v["class"] for v in verdicts})
    out["verdict"] = {"class": classes[0] if len(classes) == 1 else "NO_VERDICT",
                      "per_bank": classes,
                      "_never_pooled": refuse_pooling_across_banks(list(obs["banks"]))
                      if len(obs["banks"]) < 2 else
                      "the two codeword banks are a TRANSFER PAIR: each carries its own verdict "
                      "and they are NEVER pooled into one p-value"}
    print("\n[%s] verdict class per bank: %s" % (PR_ID, [v["class"] for v in verdicts]))
    return out


def analyse(pr: Prereg, runs_root: str, ack_path_conflict: bool) -> int:
    forb = forbidden_from_prereg(pr)
    check_wording_pin(pr)
    ident = analyzer_identity_gate(pr, ack=ack_path_conflict)
    ck = Checks()

    print("=== %s PHASE 11 analysis ===" % PR_ID)
    print("  analyzer identity: declared=%r actual=%r match=%s"
          % (ident["declared"], ident["actual"], ident["match"]))
    print("  loader state: %s" % json.dumps(analyzer_exists_flag(pr)))
    print("  PRIMARY channel=%r; %r is SECONDARY DISPLAY and may not carry a mechanism claim"
          % (primary_channel(pr), display_channel(pr)))
    aud = source_gate_literal_audit(pr)
    ck.add("no_gate_literals", "no declared gate value appears as a numeric literal in this "
           "analyzer", aud["ok"], aud["n_gates_checked"], str(aud["violations"])[:120])

    outstanding = [i["id"] for i in pr.require("pre_extraction_checklist")
                   if i.get("blocking") and not i.get("done")]

    root = runs_root if os.path.isdir(runs_root) else os.path.join(REPO, runs_root)
    if not os.path.isdir(root):
        raise Refusal(
            "no run root at %r. No PHASE 11 arm has ever been scored, so there is nothing to "
            "analyse; an analysis over zero arms would be a statistic over a set it bound zero "
            "rows from (C-074).\n  Blocking checklist items outstanding: %s"
            % (runs_root, ", ".join(outstanding)))

    assign = load_split(pr)
    arms = build_arm_manifest(pr)
    found, absent = OrderedDict(), []
    for arm in arms:
        try:
            found[arm.arm_id] = _find_run(root, arm.tag())
        except PreregError:
            absent.append(arm.arm_id)

    if not found:
        raise Refusal(
            "NO %s arm has produced a COMPLETE run under %r (%d arm tags searched, %d absent).\n"
            "  REFUSING to print an empty result: no scope in this family has been scored on the "
            "concept-free channel on this bank family by any run, so every number this analyzer "
            "could print would be over a set it bound zero rows from (C-074).\n"
            "  The two arms the kill condition reads -- the untouched baseline and %s -- are "
            "submitted and read FIRST; no narrower scope may be read before them.\n"
            "  Blocking checklist items outstanding: %s"
            % (PR_ID, root, len(arms), len(absent), reference_scope_id(pr),
               ", ".join(outstanding)))

    ck.add("arms_present", "every declared arm has a COMPLETE run directory", not absent,
           len(arms), "absent=%s" % absent[:6])
    ck.add("split_bound", "the split manifest assigns every analysed domain", bool(assign),
           len(assign))

    # U4 BEFORE anything else: if the scopes are not what the design says they are, no arm means
    # anything. The map is CPU-only and always available, so there is no excuse for reading an
    # outcome first.
    u4 = refuse_on_scope_map_disagreement(verify_scopes_against_token_map(pr, load_token_map()))
    ck.add("u4_scopes_verified", "every declared scope resolves to the declared roles in every "
           "prompt of the frozen token-role map", u4["ok"], u4["n_prompts"],
           "neutral_content=%d" % u4["n_neutral_content_tokens_total"])

    # The population is bound HERE, on `cell`, from the pinned banks -- so a zero-row or
    # zero-domain bind refuses before any outcome is read (A-039 / C-074).
    for bank_key in sorted({a.bank for a in arms}):
        rows = load_bank_rows(os.path.join(REPO, pr.require("population", "banks", bank_key,
                                                            "path")))
        b = bind_rows(pr, rows, assign)
        ck.add("bind_%s" % bank_key,
               "cell %s binds on the `cell` field after the %d whole-population exclusions"
               % (b["cell"], len(b["excluded_domains"])), True, b["n_rows"],
               "n_domains=%d by_split=%s" % (b["n_domains"], b["by_split"]))

    # Liveness BEFORE any outcome, so a number for an arm whose hook did not fire never exists.
    all_clean = True
    scopes = declared_scopes(pr)
    for arm in arms:
        d = found.get(arm.arm_id)
        if d is None:
            continue
        ck.add("arm_manifest_echo_%s" % arm.arm_id,
               "the run echoed %s -- what it BELIEVED it was doing" % CONTRACT_ARM,
               os.path.exists(os.path.join(d, CONTRACT_ARM)), 1, d)
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
        if recs and arm.rel_end_rows:
            r1 = assert_realised_equals_declared(recs, arm.rel_end_rows)
            all_clean = all_clean and r1["ok"]
            ck.add("realised_%s" % arm.arm_id, "L-N4: the realised row set EQUALS the declared "
                   "rel_end set on every row", r1["ok"], r1["n_records"], r1["reason"][:160])
            r2 = audit_end_relative(recs, arm.rel_end_rows)
            ck.add("index_%s" % arm.arm_id, "L-N10: every index is len(input_ids)+rel_end",
                   r2["ok"], r2["n_records"], r2["witness_note"])
            for rec in recs:
                refuse_display_channel_as_primary(pr, rec.get("query_kind")
                                                  or primary_channel(pr))

    ck.report()
    print("\n[%s] %d/%d arm(s) loaded, %d check failure(s)" % (PR_ID, len(found), len(arms),
                                                              ck.n_fail))
    if ck.n_fail or not all_clean:
        print(assert_sayable(
            "REFUSING to emit any verdict: %d gate(s) failed above. A null behind an unverified "
            "hook, or behind a realised row set that is not the declared one, is VOID -- not a "
            "negative -- and the mandatory wording of the declared negative is not available to "
            "an arm that has not passed liveness." % ck.n_fail, forb), file=sys.stderr)
        return 1
    print("  (baseline readout, then the kill conditions, then the reference scope, then the "
          "narrow scopes with their controls, then Holm, then the verdict -- in that order; no "
          "delta is rendered before its option_mass / argmax readout)")
    # ---- PR059-D7: THE VERDICT PATH. Reached ONLY with every gate above it clean. -----------
    obs = observe(pr, arms, found, assign, liveness_clean=all_clean)
    res = decide(pr, obs, forb)
    return 0 if res["verdict"]["class"] in ("POSITIVE", "NEGATIVE") else 2


# ============================================================================================
# 22. MAIN
# ============================================================================================
def main() -> int:
    ap = argparse.ArgumentParser(description="DCS-PR-059 PHASE 11 localisation analyzer",
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--prereg", default=PREREG_DEFAULT)
    ap.add_argument("--runs", default="outputs/boombness/score_behavior")
    ap.add_argument("--token-map", default=TOKEN_MAP_DEFAULT)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--mutate", action="store_true")
    ap.add_argument("--plan", action="store_true")
    ap.add_argument("--verify-token-map", action="store_true", help="checklist U4")
    ap.add_argument("--selector-demo", action="store_true", help="checklist U1")
    ap.add_argument("--control-draws", action="store_true", help="checklist U2")
    ap.add_argument("--u3-inventory", action="store_true", help="checklist U3, what is missing")
    ap.add_argument("--power-u3", action="store_true", help="checklist U3, as a code path")
    ap.add_argument("--validation-deltas", default=None,
                    help="JSON {domain: paired_delta} measured on VALIDATION DOMAINS ONLY (U3)")
    ap.add_argument("--ack-analyzer-path-conflict", action="store_true")
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
        if a.selector_demo:
            return selector_demo(pr)
        if a.control_draws:
            return control_draws(pr)
        if a.verify_token_map:
            res = verify_scopes_against_token_map(pr, load_token_map(a.token_map))
            print(json.dumps(res, indent=2, sort_keys=True))
            refuse_on_scope_map_disagreement(res)
            print("[U4] CONFIRMED over %d prompts: every declared scope resolves to the declared "
                  "roles; neutral_content=%d so scope B is genuinely empty; the last-%d-rows "
                  "scope equals the scaffold set in %d/%d prompts."
                  % (res["n_prompts"], res["n_neutral_content_tokens_total"],
                     res["last_k_equals_scaffold_scope"]["K"],
                     res["last_k_equals_scaffold_scope"]["n_matching"], res["n_prompts"]))
            return 0
        if a.u3_inventory:
            res = u3_inventory(pr, a.runs)
            print(json.dumps(res, indent=2, sort_keys=True))
            if not res["sufficient"]:
                print("[U3] NOT CLOSABLE. %s" % " ".join(res["missing"]), file=sys.stderr)
                return 2
            return 0
        if a.power_u3:
            if not a.validation_deltas:
                raise Refusal("--power-u3 needs --validation-deltas: U3 MEASURES the "
                              "between-domain SD on VALIDATION domains and the frozen file "
                              "deliberately carries no value for it")
            with open(a.validation_deltas) as f:
                d = json.load(f)
            res = u3_power(pr, {str(k): float(v) for k, v in d.items()})
            print(json.dumps(res, indent=2))
            return 0 if res["power_ok"] else 2
        return analyse(pr, a.runs, a.ack_analyzer_path_conflict)
    except (Refusal, ZeroBinding, CannotAnswer, PreregError) as e:
        print("REFUSED: %s" % e, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
