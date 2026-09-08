#!/usr/bin/env python3
"""`DCS-PR-057` -- PHASE 9, CLAIM C: is the concept axis CAUSALLY USED?

WHAT GOVERNS
------------
`configs/dcs_ts_pr057_phase9.json`, status FROZEN, loaded through `scripts/dcs_ts_prereg.py`.
There is not one numeric gate literal in this file: alpha, `n_perm`, the seeds, the layer band,
the read layer, the declared MDE, the control draw count, the population filter, the exclusions,
the multiplicity family and the mandatory negative wording are all fetched with
`Prereg.require()`. A number in a markdown log that no program consults is a wish (`B-020`, three
times).

Mandate section 10 and the frozen config were read side by side before this file was written and
they AGREE: 10.1 upper-bound patch first, then 10.2 the surgical subspace edit, 10.3's seven
controls, 10.4's two predeclared scope levels with multiplicity correction, 10.5's conjunctive
four-condition success rule, and 10.5's closing sentence -- decodable but not causally used --
as the negative. No disagreement was found, so nothing here is a choice between them.

THE SINGLE MOST DANGEROUS FAILURE MODE IN THIS PHASE, AND WHY HALF THIS FILE IS ABOUT IT
----------------------------------------------------------------------------------------
`C-13` recorded that `pair_common.make_project_out_hook` / `AllPositionProjectOut` /
`SinglePositionProjectOut` write NO statistics of any kind. They return a tensor and record
nothing. So a hook registered on the wrong layer object, a hook whose direction is zero, a hook
whose handle was removed before the forward, or a hook that only ever sees decode steps, all
produce EXACTLY the artifact a real intervention with no effect produces: a clean null.

A DEAD HOOK SCORES AS A CLEAN NULL. That is not a hypothetical -- it is the recorded state of the
hooks this phase was told to reuse.

Therefore this module supplies INSTRUMENTED wrappers (`InstrumentedProjectOut`,
`InstrumentedComponentReplace`, `InstrumentedAdd`, `EndRelativeDonorPatch`) that record, per row
and per edited (layer, position):

    hook_fired_count, n_forward_calls, n_destination_rows, n_cells_edited_realised /_expected,
    activation_norm_pre/_post, norm_ratio, projection_removed_l2, frac_cellmean_spread_removed,
    cos_pre_post, cos_edit_vs_direction, orthogonal_residual_delta_l2, layer, rel_end,
    resolved_absolute_index, occurrence_index, n_subtokens, direction_file_sha256,
    control_draw_seed, output_sha256

and the analyzer REFUSES to emit any causal verdict -- and specifically refuses to emit a NEGATIVE
-- for an arm whose hooks did not demonstrably fire AND demonstrably change the state. A null
behind an unverified hook is VOID, not a negative (`primary.void`).

WHAT THIS FILE IS
-----------------
One module with five entry points, because the liveness contract and the statistics that consume
it must not be able to drift apart into two files that disagree:

  --plan          the arm manifest: every run, its hypothesis, scope, layers, dose, seed, expected
                  cell count and launch command. Deterministic, CPU-only, reads no outcome.
  --self-test     CPU unit tests on synthetic data for every testable piece, including a
                  DELIBERATELY DISABLED HOOK that must be detected as disabled.
  --mutate        the `Q5` mutation harness: a dead hook, a zero-magnitude edit, an identical-hash
                  control band, a broken orthogonal-residual preservation, a self-patch that
                  changes the output, a direction fitted on test, an absolute edit index, a
                  row-level permutation and a wrong bank sha must EACH produce a refusal.
  --power-q1      checklist `Q1`: measure the between-domain SD of O2 on VALIDATION DOMAINS ONLY,
                  recompute MDE and power for the declared effect, and return CANNOT ANSWER
                  WITHOUT READING TEST if power < 0.8. This is a CODE PATH, not prose.
  (default)       the analysis: bind the population, verify every arm, evaluate the conjunctive
                  four-condition success rule under Holm across the six family members, and print
                  a verdict or a refusal.

THE ARTIFACT CONTRACT THIS FILE DEFINES AND ENFORCES
----------------------------------------------------
`src/boombness/score_behavior.py` writes `results.jsonl` / `summary.json` / `DONE.json` /
`RUNMETA.json`. Those field names were read off a COMPLETED PHASE 7 run
(`outputs/boombness/score_behavior/ts116m_readout_button_bomb_20260907_133811_3183103`, 5568 rows,
`DONE.json` status ok) and are used verbatim; nothing about that schema is guessed here.

Three artifacts do NOT exist yet and are DEFINED here, because the GPU runner must write something
this analyzer can refuse on:

    PR057_ARM.json        the arm manifest echo -- what the run believed it was doing
    PR057_LIVENESS.jsonl  one record per row per edited (layer, position) -- the C-13 fix
    PR057_PROBE.jsonl     one record per row per read layer -- O1, from the FROZEN PR-048 probe

Naming a NEW artifact is not inventing a readout field. Where this module needs a field of the
EXISTING readout that the existing writer does not emit, it says so and refuses; see
`O2_REQUIRED_FIELDS` and `BLOCKER_Q9` below.

USAGE
    python3 scripts/dcs_ts_pr057_causal.py --self-test
    python3 scripts/dcs_ts_pr057_causal.py --mutate
    python3 scripts/dcs_ts_pr057_causal.py --plan
    python3 scripts/dcs_ts_pr057_causal.py --power-q1 --runs outputs/boombness/score_behavior
    python3 scripts/dcs_ts_pr057_causal.py --runs outputs/boombness/score_behavior
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import random
import sys
from collections import OrderedDict, defaultdict
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Sequence, Tuple

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "scripts"))
sys.path.insert(0, os.path.join(REPO, "src", "boombness"))
sys.path.insert(0, os.path.join(REPO, "doublespeak_causality"))

from dcs_ts_prereg import Prereg, PreregError, load  # noqa: E402

# CONVENTIONS IMPORTED FROM THE FROZEN ANALYZERS, NOT REIMPLEMENTED. A difference between this
# script's arithmetic and PR-048's is then a difference of design, never of arithmetic.
from dcs_ts_pr048_analysis import (  # noqa: E402
    _find_run,
    bind_population,
    fmt_p,
    group_permutation_p,
    load_bank_rows,
    load_split,
    sign_test_two_sided,
)
from dcs_ts_pr051_positional import Checks, ZeroBinding, holm_family  # noqa: E402
from dcs_ts_power import t_mde, t_power  # noqa: E402

PREREG_DEFAULT = "configs/dcs_ts_pr057_phase9.json"
PR_ID = "DCS-PR-057"


# ============================================================================== refusals
class Refusal(RuntimeError):
    """Anything this analyzer will not do. Every one of them is fail-closed."""


class NotMeasured(Refusal):
    """A gate was asked to rule on a quantity NOBODY RECORDED.

    C-117 / review F2. `liveness_gate` and `orthogonal_residual_gate` used to read
    `n_cells_edited_expected` and `orthogonal_residual_delta_l2` with a defaulting `.get`, so a
    field the producer never wrote arrived as `0` / `NaN` and the gate then published a
    SUBSTANTIVE SCIENTIFIC VERDICT about it -- "the arm declared no destinations", "the orthogonal
    component was NOT preserved; H2b is VOID". Both statements were false: the quantity had simply
    never been measured. That is the repo's recorded bug class (a check that reads the producer's
    own null field) with the sign flipped, and it is worse, because it manufactures a positive
    claim of a physical violation out of an absence.

    A MISSING field is therefore this exception, and a MEASURED ZERO is still a failing verdict.
    The two must never be the same thing -- which is also why this is not fixed by making the
    gates lenient: a dead hook must stay impossible to mistake for a clean null.
    """


# THE NEGATIVE'S WORDING IS A LITERAL, SO IT CANNOT DRIFT.
#
# Mandate section 32 calls this a valuable result and section 33 forbids the alternative. The
# string lives here once, is cross-checked against `primary.negative.MANDATORY_WORDING` in the
# frozen config at load time (a divergence is a refusal), and is the ONLY way this file can emit a
# negative. `things_that_must_not_be_said` is enforced by `assert_sayable` over every line of
# emitted text, so the forbidden sentence cannot reach a report even by paraphrase-free accident.
MANDATORY_NEGATIVE_WORDING = "DECODABLE BUT NOT CAUSALLY USED UNDER THIS INTERVENTION"

#: Substrings that must never appear in anything this file prints or writes. Lower-cased match.
#: Derived from `things_that_must_not_be_said` in the frozen config; the config's list is ALSO
#: loaded and merged, so adding a forbidden phrase there needs no edit here.
FORBIDDEN_SUBSTRINGS = (
    "the representation is meaningless",
    "representation is meaningless",
    "the representation means nothing",
    "probe accuracy proves causal use",
    "the whole demonstration->query pathway was removed",
    "the attack is ours",
)

# ------------------------------------------------------------------------------ O2 schema
#
# WHAT THE PHASE 7 WRITER ACTUALLY EMITS, read off a COMPLETED run rather than assumed:
#     logp_concept  p_concept  n_variants_concept
#     logp_codeword p_codeword n_variants_codeword
#     option_mass   top1_id    semantic_logodds   semantic_margin_p_diff
# and `semantic_logodds == logp_concept - logp_codeword` (score_behavior.py:2193).
#
# `concept` there is THE BANK'S OWN CONCEPT. `score_behavior` asserts ONE codeword/concept pair per
# bank and builds the answer set once from rows[0], so a bomb bank scores {bomb, button} and
# NOTHING ELSE. There is no logP(knife) on a bomb bank.
#
# The frozen config's O2 is `semantic_logodds(source_concept vs target_concept)` over candidates
# {bomb, knife, gun, the literal codeword, neither}. THAT CONTRAST IS NOT COMPUTABLE FROM THE
# INSTRUMENT AS IT STANDS. This is not a disagreement between the config and the mandate -- the
# mandate says only "does the semantic interpretation shift Bomb -> Knife" -- it is a gap between
# the config and the code, and it is BLOCKING. It is recorded as BLOCKER_Q9 and reported, never
# papered over.
#
# The required field names below are DERIVED from the writer, not invented:
# `next_token_readout` emits `logp_{name}` / `p_{name}` for each option group name
# (score_behavior.py:119-123), so an answer set whose groups are named for the concepts emits
# `logp_bomb` / `logp_knife` / `logp_gun` under exactly the existing rule.
BLOCKER_Q9 = (
    "Q9: the PHASE 7 readout scores ONE concept per bank ({concept, codeword}), so logP(source "
    "concept) does not exist on the target bank and a CROSS-CONCEPT O2 -- semantic_logodds"
    "(source vs target concept) -- is not computable from the DEFAULT instrument. RESOLVED "
    "2026-09-07 by `score_behavior --semantic-extra-words knife,gun`, which appends extra "
    "candidate words to the semantic answer set under the existing `logp_{group}` rule "
    "(next_token_readout:119) and emits word-named ALIASES of the bank's own pair, so a bomb "
    "bank yields logp_bomb / logp_knife / logp_gun / logp_codeword. The flag is DEFAULT-OFF and "
    "the one-pair-per-bank assertion is NOT relaxed: extra CANDIDATES are added, a second PAIR "
    "is not admitted, so the guard that stops a two-pair bank being scored against rows[0] "
    "stays exactly where it is. Under C-112 the PRIMARY arm no longer needs this -- see "
    "`o2_projection_out_from_rows` -- and it is the EXPLORATORY 10.1 arm that does."
)

# ------------------------------------------------------------------------------------------
# C-112 (2026-09-07): THE PRIMARY ARM CHANGED, AND WITH IT WHAT O2 HAS TO BE.
#
# R-116 (2026-09-07, ALL SIX BANKS -- supersedes R-115's four-bank figures) measured INSTALLATION
# per concept on the primary concept-free channel: bomb installs in 0.619 of 113 domains (0.522 of
# the 23 TEST domains), knife in **0.000**, gun in 0.009 (0.000 on TEST). R-115 had reported knife
# at 3/113 from four banks; on six it is ZERO. Mandate 10.1's upper-bound patch takes a
# DONOR C_knife prompt and writes it into a C_bomb target. For ~97% of domains that donor is a
# prompt in which the knife demonstrations INSTALLED NOTHING, so "the reading did not shift to
# knife" is a statement about the donor, not about the target's concept axis. That arm is
# DEMOTED TO EXPLORATORY and its null is CANNOT ANSWER BY CONSTRUCTION.
#
# Mandate 10.2 -- project v_bomb_specific out of a BOMB prompt where the concept demonstrably
# DOES install -- becomes the PRIMARY causal test. It needs no donor and no second installed
# concept, and its outcome is "does the BOMB reading fall", which IS computable today.
# ------------------------------------------------------------------------------------------
C112_PRIMARY_IS_10_2 = (
    "C-112: mandate 10.2 (surgical subspace projection-out on a BOMB prompt) is the PRIMARY "
    "causal test. Mandate 10.1 (the cross-concept upper-bound patch) is EXPLORATORY: R-115 "
    "measured (R-116, six banks) knife installing in ZERO of 113 domains and gun in 0.009, so its "
    "donor is a prompt in which the source concept NEVER installed. The arm is not merely "
    "under-powered: on this bank its population is EMPTY, so a null from it is CANNOT ANSWER BY "
    "CONSTRUCTION rather than evidence, and it must not be submitted at all."
)
O2_REQUIRED_FIELDS = ("logp_bomb", "logp_knife", "logp_gun", "logp_codeword")
#: Computable TODAY, reported as a companion, and explicitly NOT able to satisfy success
#: condition 2: it cannot distinguish "moved toward knife" from "the readout was destroyed".
O2_PARTIAL_FIELD = "semantic_logodds"

CONTRACT_ARM = "PR057_ARM.json"
CONTRACT_LIVENESS = "PR057_LIVENESS.jsonl"
CONTRACT_PROBE = "PR057_PROBE.jsonl"


def assert_sayable(text: str, extra: Sequence[str] = ()) -> str:
    """Refuse to emit a forbidden sentence. Returns `text` so it can wrap a print argument."""
    low = text.lower()
    for bad in tuple(FORBIDDEN_SUBSTRINGS) + tuple(s.lower() for s in extra):
        b = bad.lower().strip()
        # The config's list carries whole sentences with their own explanations; match on the
        # leading clause so a paraphrase of the clause is still caught.
        clause = b.split(" -- ")[0].strip().strip('"').strip("'")
        if clause and clause in low:
            raise Refusal(
                "REFUSING to emit text containing a forbidden claim %r. Mandate section 33 and "
                "`things_that_must_not_be_said` forbid it absolutely; the replacement wording is "
                "%r." % (clause, MANDATORY_NEGATIVE_WORDING))
    return text


def forbidden_from_prereg(pr: Prereg) -> List[str]:
    try:
        return [str(s) for s in pr.require("things_that_must_not_be_said")]
    except PreregError:
        raise Refusal("the preregistration declares no `things_that_must_not_be_said`; refusing "
                      "to run without the list that fixes the wording of the negative")


def check_wording_pin(pr: Prereg) -> str:
    """The literal negative wording here must equal the frozen config's. Divergence is a refusal."""
    want = str(pr.require("primary", "negative", "MANDATORY_WORDING")).strip()
    if want.upper() != MANDATORY_NEGATIVE_WORDING:
        raise Refusal(
            "primary.negative.MANDATORY_WORDING is %r but this analyzer's literal is %r. The "
            "wording of the negative is non-negotiable and must not drift between the "
            "preregistration and the code." % (want, MANDATORY_NEGATIVE_WORDING))
    return MANDATORY_NEGATIVE_WORDING


# ============================================================================== hashing
def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_text(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


# ============================================================================================
# 1. INDEX RESOLUTION -- end-relative, never absolute
# ============================================================================================
#
# `_read_site_note` in the frozen config: the ABSOLUTE codeword index is identical across concepts
# in 0/2300 triples (mean cross-concept spread 9.36 +/- 5.90 tokens, range 0-50). A position
# computed on one example and reused as an absolute index on another is this repository's
# documented bug class and has hit it twice. Every read and every edit index in this phase is
# `len(input_ids) + rel_end`, resolved per row.
def resolve_end_relative(input_ids: Sequence[int], rel_end: int) -> int:
    if rel_end >= 0:
        raise Refusal("rel_end must be NEGATIVE (end-relative); got %r. A non-negative offset is "
                      "an absolute index wearing the wrong name." % (rel_end,))
    idx = len(input_ids) + rel_end
    if idx < 0 or idx >= len(input_ids):
        raise Refusal("rel_end %d does not resolve inside a sequence of length %d"
                      % (rel_end, len(input_ids)))
    return idx


def audit_end_relative(records: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    """`I-N9`: every persisted edit/read index must equal len(input_ids)+rel_end, and the absolute
    index must VARY across concepts (it is a witness, never an input)."""
    bad, seen, n_na = [], [], 0
    for r in records:
        # SCHEMA (C-117). `pair_common` writes the length the site was resolved against as
        # `seq_len_at_resolution`, `score_behavior`'s row wrapper writes the same number as
        # `seq_len`, and `resolved_absolute_index` is a LIST (one entry per edited position),
        # which is the honest shape. `seq_len_last` is NOT accepted here: it is the length of
        # the last forward, and the readout's variant forwards have different lengths, so
        # auditing against it would fail on correct rows.
        _sl = (r["seq_len"] if r.get("seq_len") is not None
               else r.get("seq_len_at_resolution"))
        _abs = r.get("resolved_absolute_index")
        _rel = r.get("rel_end")
        if _abs is None and _rel is None:
            # an ALL-POSITION (S2) edit: every position is edited, so there is no single site to
            # audit. Counted and reported as such -- never given an invented rel_end.
            n_na += 1
            continue
        need = {"seq_len (or seq_len_at_resolution)": _sl, "rel_end": _rel,
                "resolved_absolute_index": _abs}
        miss = sorted(k for k, v in need.items() if v is None)
        if miss:
            raise NotMeasured(
                "liveness record is missing %s -- the end-relative audit cannot be performed and "
                "is therefore NOT assumed to pass" % miss)
        idxs = list(_abs) if isinstance(_abs, (list, tuple)) else [_abs]
        for a in idxs:
            seen.append(int(a))
            if int(_sl) + int(_rel) != int(a):
                bad.append(r)
    n_aud = len(records) - n_na
    spread = len(set(seen))
    if n_na and not n_aud:
        return {"n_records": 0, "n_not_applicable": n_na, "not_applicable": True,
                "n_absolute_index_violations": 0, "n_distinct_absolute_indices": 0,
                "ok": True,
                "witness_note": ("all %d record(s) are ALL-POSITION edits: every position is "
                                 "edited, so there is no single site whose index could be a "
                                 "reused absolute one. Not applicable, not passed." % n_na)}
    return {"n_records": n_aud, "n_not_applicable": n_na,
            "n_absolute_index_violations": len(bad),
            "n_distinct_absolute_indices": spread,
            "ok": (not bad) and n_aud > 0,
            "witness_note": ("the absolute index takes %d distinct values over %d records; a "
                             "SINGLE value across concepts would mean an absolute index was "
                             "reused" % (spread, n_aud))}


# ============================================================================================
# 2. HOOK LIVENESS -- the C-13 fix
# ============================================================================================
@dataclass
class LivenessStats:
    """Everything `persist_per_row_and_per_arm` demands, recorded by the hook itself.

    `enabled=False` is the DISABLED-HOOK BRIDGE (control C5): the hook is registered, runs, and
    edits nothing. It is recorded as `enabled=False` so the analyzer can tell a bridge from a dead
    hook -- a distinction nothing in `pair_common` can currently make, which is the whole of C-13.
    """
    arm_id: str = ""
    layer: int = -1
    enabled: bool = True
    n_forward_calls: int = 0
    hook_fired_count: int = 0
    n_destination_rows: int = 0
    n_cells_edited_realised: int = 0
    n_cells_edited_expected: int = 0
    activation_norm_pre: float = 0.0
    activation_norm_post: float = 0.0
    projection_removed_l2: float = 0.0
    cos_pre_post: float = 1.0
    cos_edit_vs_direction: float = float("nan")
    # None, NOT 0.0 (C-117). A default of 0.0 is a MEASURED PERFECT PRESERVATION -- exactly the
    # I-N7 verdict -- handed out to a hook that never computed it. `orthogonal_residual_gate`
    # raises `NotMeasured` on None and only rules when a hook actually wrote a number.
    orthogonal_residual_delta_l2: Optional[float] = None
    frac_cellmean_spread_removed: Optional[float] = None
    rel_end: Optional[int] = None
    seq_len: Optional[int] = None
    resolved_absolute_index: Optional[int] = None
    occurrence_index: Optional[int] = None
    n_subtokens: Optional[int] = None
    direction_file_sha256: Optional[str] = None
    control_draw_seed: Optional[int] = None

    @property
    def norm_ratio(self) -> float:
        return (self.activation_norm_post / self.activation_norm_pre
                if self.activation_norm_pre else float("nan"))

    def as_row(self) -> Dict[str, Any]:
        d = asdict(self)
        d["norm_ratio"] = self.norm_ratio
        return d


def _unit(v):
    import torch
    v = v.detach().float().reshape(-1)
    n = float(v.norm())
    if n == 0.0:
        raise Refusal("a direction of ZERO NORM reached the hook. A zero direction edits nothing "
                      "and would score as a clean null -- refusing (primary.void: an arm's edit "
                      "magnitude is 0).")
    return v / n


def make_instrumented_project_out_hook(direction, stats: LivenessStats, positions=None,
                                       alpha: float = 1.0, enabled: bool = True):
    """`h' = h - alpha * proj_d(h)`, with liveness recorded.

    Same arithmetic as `pair_common.make_project_out_hook` (which this deliberately mirrors rather
    than replaces), plus the statistics that file does not write. `positions=None` means every
    position, matching `AllPositionProjectOut`; a list of positions means those positions only,
    matching `SinglePositionProjectOut` -- and the positions are supplied ALREADY RESOLVED by
    `resolve_end_relative`, never recomputed inside the hook.
    """
    import torch
    d_cpu = _unit(direction)

    def hook(module, inputs, output):
        is_tuple = isinstance(output, tuple)
        h = output[0] if is_tuple else output
        stats.n_forward_calls += 1
        d = d_cpu.to(device=h.device, dtype=h.dtype)
        if positions is None:
            sel = slice(None)
            n_dest = int(h.shape[1])
        else:
            live = [p for p in positions if 0 <= p < h.shape[1]]
            if not live:
                return output                      # decode step: nothing to edit here
            sel = live
            n_dest = len(live)
        h = h.clone()
        pre = h[:, sel, :].reshape(-1, h.shape[-1]).float()
        proj = (pre @ d.float().reshape(-1, 1))            # [n, 1]
        edit = alpha * proj * d.float().reshape(1, -1)
        post = pre - edit
        # EXPECTED, from the tensor this forward was handed, BEFORE the write (C-117). The
        # producer side of this schema does the same thing in `pair_common`; the two now agree.
        stats.n_cells_edited_expected += n_dest * int(h.shape[0])
        # I-N7 for a project_out edit: the change is `alpha*(h.d)d`, so its component orthogonal
        # to `d` must be zero to float error. MEASURED, so the gate has something to rule on.
        _dv = d.float().reshape(-1)
        _delta = pre - post
        _orth = float((_delta - (_delta @ _dv.reshape(-1, 1)) * _dv.reshape(1, -1)).norm())
        stats.orthogonal_residual_delta_l2 = (
            _orth if stats.orthogonal_residual_delta_l2 is None
            else max(float(stats.orthogonal_residual_delta_l2), _orth))
        if enabled:
            h[:, sel, :] = post.to(h.dtype).reshape(h[:, sel, :].shape)
            stats.hook_fired_count += 1
            stats.n_cells_edited_realised += n_dest * int(h.shape[0])
        stats.n_destination_rows += n_dest * int(h.shape[0])
        stats.activation_norm_pre = float(pre.norm())
        stats.activation_norm_post = float(post.norm()) if enabled else float(pre.norm())
        stats.projection_removed_l2 = float(edit.norm()) if enabled else 0.0
        if enabled and float(pre.norm()) > 0 and float(post.norm()) > 0:
            stats.cos_pre_post = float((pre * post).sum()
                                       / (pre.norm() * post.norm()))
            if float(edit.norm()) > 0:
                stats.cos_edit_vs_direction = float(
                    (edit.reshape(-1) @ d.float().repeat(edit.shape[0]))
                    / (edit.norm() * math.sqrt(edit.shape[0])))
        return (h,) + tuple(output[1:]) if is_tuple else h

    return hook


def make_instrumented_component_replace_hook(v_out, v_in, c_in: float, stats: LivenessStats,
                                             positions=None, enabled: bool = True):
    """H2b: `h' = h - proj_{v_out}(h) + c_in * v_in`, orthogonal residual preserved EXACTLY.

    The preservation is VERIFIED NUMERICALLY on every edited cell and written to
    `orthogonal_residual_delta_l2`; `nulls_required.I-N7` is blocking and the arm is VOID if it is
    not zero to tolerance. Asserting preservation in a comment is what this project keeps being
    burned by; measuring it costs one projection.
    """
    import torch
    d_out = _unit(v_out)
    d_in = _unit(v_in)

    def hook(module, inputs, output):
        is_tuple = isinstance(output, tuple)
        h = output[0] if is_tuple else output
        stats.n_forward_calls += 1
        if positions is None:
            sel = slice(None)
            n_dest = int(h.shape[1])
        else:
            live = [p for p in positions if 0 <= p < h.shape[1]]
            if not live:
                return output
            sel = live
            n_dest = len(live)
        do = d_out.to(device=h.device, dtype=torch.float32)
        di = d_in.to(device=h.device, dtype=torch.float32)
        h = h.clone()
        pre = h[:, sel, :].reshape(-1, h.shape[-1]).float()
        removed = (pre @ do.reshape(-1, 1)) * do.reshape(1, -1)
        added = float(c_in) * di.reshape(1, -1).expand_as(pre)
        post = pre - removed + added
        # The orthogonal residual: the part of the state outside span{v_out, v_in}.
        basis = torch.stack([do, di])                               # [2, hidden]
        q, _ = torch.linalg.qr(basis.T)                             # [hidden, k]
        orth_pre = pre - (pre @ q) @ q.T
        orth_post = post - (post @ q) @ q.T
        stats.n_cells_edited_expected += n_dest * int(h.shape[0])
        stats.orthogonal_residual_delta_l2 = float((orth_pre - orth_post).norm())
        if enabled:
            h[:, sel, :] = post.to(h.dtype).reshape(h[:, sel, :].shape)
            stats.hook_fired_count += 1
            stats.n_cells_edited_realised += n_dest * int(h.shape[0])
        stats.n_destination_rows += n_dest * int(h.shape[0])
        stats.activation_norm_pre = float(pre.norm())
        stats.activation_norm_post = float(post.norm()) if enabled else float(pre.norm())
        stats.projection_removed_l2 = float(removed.norm()) if enabled else 0.0
        if enabled and float(pre.norm()) > 0 and float(post.norm()) > 0:
            stats.cos_pre_post = float((pre * post).sum() / (pre.norm() * post.norm()))
        return (h,) + tuple(output[1:]) if is_tuple else h

    return hook


def gap_unit_alpha(alpha: float, gap: Optional[float]) -> float:
    """`Q6`: an ADD is dosed in GAP UNITS (alpha=1 == one difference-of-means), never bare alpha.

    `score_behavior.make_intervention` refuses an additive dose on a direction with no `gap`
    entry, for the reason its docstring gives: at L18 the gap is 14.8, so a bare alpha=1 is ~7% of
    one diff-of-means. That bug was fixed in `aggressive_patching` and MISSED at the second call
    site once already. This is the third call site; it does not get to repeat it.
    """
    if gap is None:
        raise Refusal("refusing to dose an additive edit on a unit vector with no `gap`: a bare "
                      "alpha injects an absolute magnitude unrelated to the natural effect size "
                      "(the aggressive_patching bug, missed once at a second call site).")
    g = float(gap)
    if not math.isfinite(g) or g <= 0:
        raise Refusal("gap must be a positive finite diff-of-means magnitude, got %r" % (gap,))
    return float(alpha) * g


def _resolve_hook_target(model, layer_idx: int):
    """The module to hook: block `layer_idx` of a real model, or a bare test module.

    ORDER MATTERS AND IT IS NOT COSMETIC. An HF model IS an `nn.Module` and therefore HAS
    `register_forward_hook`, so a `hasattr` check FIRST would hook the WHOLE MODEL instead of
    block L -- editing (or reading) the final hidden state while every log said "layer 9". That
    is the same silent wrong-scope shape as Q12's all-position/single-position defect, one level
    down, and it was present in this file's first draft. `ds_common._get_layers` is tried FIRST
    and only an object it cannot resolve is treated as being itself the layer -- which is what
    lets these hooks be unit-tested on CPU against the real hook functions.
    """
    try:
        import ds_common as dc
        layers = dc._get_layers(model)
    except Exception:
        layers = None
    if layers is not None:
        return layers[layer_idx]
    if hasattr(model, "register_forward_hook"):
        return model
    raise Refusal("cannot resolve a decoder layer from %s" % type(model).__name__)


class InstrumentedHook:
    """Context manager registering an instrumented hook on one decoder layer.

    `model` may be a real HF model (resolved through `ds_common._get_layers`, the house helper) or,
    in the unit tests, any object exposing `register_forward_hook`. The tests exercise the SAME
    hook function the GPU path uses; a test against a re-implementation would test nothing.
    """

    def __init__(self, model, layer_idx: int, hook_fn, stats: LivenessStats):
        self.layer = _resolve_hook_target(model, layer_idx)
        self.stats = stats
        self.stats.layer = int(layer_idx)
        self._fn = hook_fn
        self._h = None

    def __enter__(self):
        self._h = self.layer.register_forward_hook(self._fn)
        return self

    def __exit__(self, *exc):
        if self._h is not None:
            self._h.remove()
            self._h = None
        return False


# ============================================================================================
# 5b. THE FROZEN PR-048 PROBE, AND O1 CAPTURED INSIDE THE INTERVENTION RUN (Q10 / Q11)
# ============================================================================================
#: Where `dcs_ts_pr048_analysis.py` writes the frozen estimator (added 2026-09-07 for Q10).
FROZEN_PROBE_KEY = "FROZEN_PROBE"

BLOCKER_Q11 = (
    "Q11: `extract_boombness.py` has no --intervene, so O1 CANNOT be captured by a separate "
    "extraction: an un-intervened extraction measures the un-intervened state, which is O1's "
    "baseline and not its outcome. O1 is therefore captured INSIDE the intervention run by "
    "`ProbeReadCapture`, which registers a READ hook (it returns `output` unchanged) at the "
    "primary read layer and at every `propagation_read_layers()` layer, applies the FROZEN "
    "PR-048 probe on the fly, and writes PR057_PROBE.jsonl."
)


class FrozenProbe:
    """The PR-048 estimator, loaded and NEVER refitted.

    `Q10` used to be blocking because `dcs_ts_pr048_analysis.py` persisted `SELECTION_TRACE`, the
    selected (layer, C) and the per-domain accuracies but NOT the coefficients. With no frozen
    estimator, the only way to compute O1 under intervention would have been to REFIT -- which
    lets the probe chase the edit and makes O1 unfalsifiable by construction. That is why
    `refit` is not a parameter here: there is no code path in this class that fits anything.

    Scoring is reconstructed from the exported numbers alone (mean/scale/coef/intercept), which
    is the same arithmetic `dcs_ts_pr048_analysis.py` self-verifies against its own sklearn
    objects on every test row before it will write the artifact. Two implementations of one rule
    that are checked against each other beat one implementation nobody checked.
    """

    def __init__(self, blob: Dict[str, Any], source: str = "<memory>"):
        import numpy as np
        need = ("selected_layer", "classes", "estimator", "scaler", "feature_dim", "sha256")
        miss = [k for k in need if k not in blob]
        if miss:
            raise Refusal("the frozen probe is missing %s. %s" % (miss, BLOCKER_Q9_PROBE))
        self.raw = blob
        self.source = source
        self.layer = int(blob["selected_layer"])
        self.C = float(blob.get("selected_C", float("nan")))
        self.classes = [str(c) for c in blob["classes"]]
        self.sha256 = str(blob["sha256"])
        self.mean = np.asarray(blob["scaler"]["mean"], dtype=float)
        self.scale = np.asarray(blob["scaler"]["scale"], dtype=float)
        self.coef = np.asarray(blob["estimator"]["coef"], dtype=float)
        self.intercept = np.asarray(blob["estimator"]["intercept"], dtype=float)
        self.feature_dim = int(blob["feature_dim"])
        self.sk_classes = [int(c) for c in blob.get("sklearn_classes_", range(len(self.classes)))]
        if self.mean.shape[0] != self.feature_dim or self.scale.shape[0] != self.feature_dim:
            raise Refusal("frozen probe scaler width %d != feature_dim %d"
                          % (self.mean.shape[0], self.feature_dim))
        if self.coef.shape[1] != self.feature_dim:
            raise Refusal("frozen probe coefficient width %d != feature_dim %d"
                          % (self.coef.shape[1], self.feature_dim))
        if float(np.abs(self.coef).max()) == 0.0:
            raise Refusal("frozen probe coefficients are ALL ZERO. A probe that reads nothing "
                          "returns the same posterior under every intervention and would score "
                          "as a clean O1 null.")
        if float(np.min(self.scale)) <= 0.0:
            raise Refusal("frozen probe scaler has a non-positive scale entry; refusing.")

    def posterior(self, x) -> Dict[str, float]:
        """Posterior probability per concept for ONE hidden-state vector."""
        import numpy as np
        v = np.asarray(x, dtype=float).reshape(-1)
        if v.shape[0] != self.feature_dim:
            raise Refusal("the read site produced a %d-vector but the frozen probe was fitted on "
                          "%d features. This is a READ-SITE MISMATCH, not a small difference: "
                          "refusing rather than truncating." % (v.shape[0], self.feature_dim))
        z = (v - self.mean) / self.scale
        logits = self.coef @ z + self.intercept
        if logits.shape[0] == 1:                       # sklearn's binary parameterisation
            p1 = 1.0 / (1.0 + math.exp(-float(logits[0])))
            probs = [1.0 - p1, p1]
            order = self.sk_classes if len(self.sk_classes) == 2 else [0, 1]
        else:
            m = float(np.max(logits))
            e = np.exp(logits - m)
            probs = list(e / e.sum())
            order = self.sk_classes
        out = {}
        for i, ci in enumerate(order):
            out[self.classes[int(ci)]] = float(probs[i])
        return out

    def margin(self, x, source: str, target: str) -> float:
        """O1: posterior mass on the SOURCE concept minus mass on the TARGET concept.

        Exactly `outcome_variables.O1_probe.definition`. A concept the probe was never fitted on
        is a refusal, not a zero -- silently scoring an absent class as 0.0 would make every
        intervention look like it moved the margin toward the other class.
        """
        post = self.posterior(x)
        for c in (source, target):
            if c not in post:
                raise Refusal("the frozen probe has no class %r (it knows %s); O1 cannot be "
                              "formed and must not be defaulted to zero." % (c, self.classes))
        return float(post[source] - post[target])


BLOCKER_Q9_PROBE = (
    "Run `scripts/dcs_ts_pr048_analysis.py` at or after commit 2026-09-07: it writes the "
    "FROZEN_PROBE block (coefficients, scaler statistics, selected layer and C, a content "
    "sha256, and a self-verification that re-scoring the test rows from the exported numbers "
    "reproduces the estimator on every row). An earlier result JSON has no probe to load."
)


def load_frozen_probe(path: str, expect_sha: Optional[str] = None) -> FrozenProbe:
    """Load the frozen PR-048 probe from a PR-048 result JSON, refusing on every absence.

    `expect_sha` PINS the probe. PHASE 9's O1 is only interpretable against the estimator that
    produced R-113; a probe that has been re-selected or re-fitted between the phases is a
    different instrument wearing the same name, and this is where that is caught.
    """
    if not os.path.exists(path):
        raise Refusal("no PR-048 result at %s; O1 has no frozen probe. %s"
                      % (path, BLOCKER_Q9_PROBE))
    blob = json.load(open(path))
    if FROZEN_PROBE_KEY not in blob:
        raise Refusal("%s carries no %r block, so the fitted coefficients were never persisted "
                      "and O1 has nothing to score against. %s"
                      % (path, FROZEN_PROBE_KEY, BLOCKER_Q9_PROBE))
    fp = FrozenProbe(blob[FROZEN_PROBE_KEY], source=path)
    sv = blob[FROZEN_PROBE_KEY].get("self_verification") or {}
    if not sv.get("reproduced_from_exported_numbers"):
        raise Refusal("%s exports a probe that was never self-verified: the producer did not "
                      "prove that re-scoring from the exported coefficients reproduces its own "
                      "estimator. An unverified export is a check that reads the producer's own "
                      "null field." % path)
    if int(sv.get("n_disagreements", -1)) != 0:
        raise Refusal("%s exports a probe whose self-verification disagreed on %s rows."
                      % (path, sv.get("n_disagreements")))
    if expect_sha and fp.sha256 != expect_sha:
        raise Refusal("frozen probe sha %s != pinned %s. The probe has changed since the run "
                      "this phase's O1 is defined against; refusing." % (fp.sha256, expect_sha))
    return fp


class ProbeReadCapture:
    """Q11: capture O1 INSIDE the intervention run, with a READ-ONLY hook.

    `extract_boombness.py` has no `--intervene`, so there is no way to get an intervened
    representation out of a separate extraction job -- and capturing O1 in an UN-INTERVENED job
    would measure the baseline and report it as the outcome. The fix is not a new extractor: it
    is to read the state where it already exists, during the intervened forward.

    This hook RETURNS `output` UNCHANGED. That is load-bearing and it is unit-tested: a read
    hook that accidentally edits would contaminate the very arm it is measuring, and the edit
    would be invisible because the arm is *supposed* to be edited.

    It records, per row per read layer: the posterior over concepts, the O1 margin, the
    resolved absolute index, the sequence length, and the number of forward calls seen -- so a
    capture that never ran is `n_forward_calls == 0` rather than an absent file.

    C-118(a), 2026-09-07: ATTRIBUTION AND THE MANY-FORWARDS PROBLEM.

    O1 is a DOMAIN-LEVEL statistic, so a record that cannot name its domain cannot form it. The
    attribution point is `row_meta`, which the caller fills IN THE ROW LOOP -- `score_behavior`
    constructs its interventions per row (it must: the edit site is end-relative and is resolved
    against THIS row's length), and its own `PR057_LIVENESS.jsonl` writer already stamps
    `prompt_id`/`domain` from exactly there. So attribution is by CONSTRUCTION, never by the
    order in which records arrive.

    That leaves the second half, which is the one that could still misalign silently: ONE ROW
    PRODUCES MANY FORWARDS (`string_option_readout` scores each answer variant, in batches), and
    those forwards have DIFFERENT sequence lengths. Resolving `seq_len + rel_end` inside the hook
    therefore reads a DIFFERENT TOKEN on every variant forward, and averaging them would be the
    exact silent misalignment this phase refuses. Two changes close it:

      * `abs_index=` PINS the site to the index the caller resolved against the ROW's prompt --
        the same number, computed the same way, that the edit hook is given. Read and edit are
        then at the same token by construction rather than by a coincidence of lengths. The
        end-relative contract is the same three-argument one `SinglePositionProjectOut` carries:
        the offset is the record, the absolute index is the input, and
        `seq_len_at_resolution + rel_end == abs_index` is asserted at construction.
      * the state at that index is IDENTICAL on every forward of the row -- the model is causal
        and `string_option_readout` RIGHT-pads over a shared context prefix, so a prompt position
        cannot see the variant appended after it. That is an INVARIANT, so it is CHECKED: every
        capture is hashed, ONE record is emitted per row per layer, and a row whose captures
        DISAGREE is refused instead of averaged. If the assumption ever breaks -- a left-padding
        change, a template that inserts rather than appends -- the run stops rather than
        reporting a mean over several different tokens.
    """
    def __init__(self, model, layer_idx: int, probe: FrozenProbe, rel_end: int,
                 source: str, target: str, records: List[Dict[str, Any]],
                 row_meta: Optional[Dict[str, Any]] = None,
                 abs_index: Optional[int] = None,
                 seq_len_at_resolution: Optional[int] = None):
        if rel_end >= 0:
            raise Refusal("ProbeReadCapture takes an END-RELATIVE index (negative); got %d. An "
                          "absolute index reused across examples is this repository's "
                          "twice-recorded bug class." % rel_end)
        if abs_index is not None:
            if seq_len_at_resolution is None:
                raise Refusal(
                    "ProbeReadCapture was pinned to absolute index %d with no "
                    "seq_len_at_resolution. Without the length it was resolved against, "
                    "`abs_index == seq_len + rel_end` cannot be checked and the pin is an "
                    "unaudited absolute index -- the bug class it exists to prevent."
                    % abs_index)
            if int(seq_len_at_resolution) + int(rel_end) != int(abs_index):
                raise Refusal(
                    "ProbeReadCapture: abs_index=%d but seq_len_at_resolution(%d) + rel_end(%d) "
                    "= %d. The token read and the token RECORDED are not the same token."
                    % (int(abs_index), int(seq_len_at_resolution), int(rel_end),
                       int(seq_len_at_resolution) + int(rel_end)))
        self.layer = _resolve_hook_target(model, layer_idx)
        self.layer_idx = int(layer_idx)
        self.probe = probe
        self.rel_end = int(rel_end)
        self.abs_index = None if abs_index is None else int(abs_index)
        self.seq_len_at_resolution = (None if seq_len_at_resolution is None
                                      else int(seq_len_at_resolution))
        self.source, self.target = source, target
        self.records = records
        self.row_meta = dict(row_meta or {})
        self.n_forward_calls = 0
        self.n_captured = 0
        self._shas: List[str] = []
        self._record: Optional[Dict[str, Any]] = None
        self._h = None

    def _hook(self, module, inputs, output):
        h = output[0] if isinstance(output, tuple) else output
        self.n_forward_calls += 1
        if int(h.shape[1]) <= 1:            # decode step: the prompt site is not in this tensor
            return output
        seq_len = int(h.shape[1])
        # PINNED, when the caller resolved the site against the row's prompt; otherwise
        # end-relative against THIS forward, which is the historical behaviour and is correct
        # only when the row makes exactly one forward.
        idx = self.abs_index if self.abs_index is not None else seq_len + self.rel_end
        if idx < 0 or idx >= seq_len:
            return output
        v = h[0, idx, :].detach().float().cpu().contiguous().numpy()
        _sha = hashlib.sha256(v.tobytes()).hexdigest()[:16]
        self.n_captured += 1
        self._shas.append(_sha)
        if self._record is not None:
            # ONE RECORD PER ROW PER LAYER. A second capture is the SAME token on a later
            # variant forward and must be bit-identical; if it is not, the assumption that a
            # prompt position cannot see the variant appended after it has broken, and that is
            # a refusal rather than something to average over.
            if _sha != self._shas[0]:
                raise Refusal(
                    "ProbeReadCapture at layer %d, row %r: forward %d read a DIFFERENT state at "
                    "the SAME pinned index %d (%s != %s). One row's forwards must agree at a "
                    "prompt position -- the model is causal and the readout right-pads a shared "
                    "context -- so this means the site moved between forwards. Refusing: an O1 "
                    "averaged over several different tokens is the silent misalignment this "
                    "phase exists to refuse."
                    % (self.layer_idx, self.row_meta.get("prompt_id"), self.n_forward_calls,
                       idx, _sha, self._shas[0]))
            self._record["n_forward_calls"] = self.n_forward_calls
            self._record["n_captures"] = self.n_captured
            return output
        post = self.probe.posterior(v)
        self._record = {
            **self.row_meta,
            "read_layer": self.layer_idx, "rel_end": self.rel_end,
            "seq_len": seq_len, "resolved_absolute_index": idx,
            "seq_len_at_resolution": self.seq_len_at_resolution,
            "index_pinned_to_row_prompt": self.abs_index is not None,
            "capture_sha16": _sha,
            "probe_sha256": self.probe.sha256, "probe_fit_layer": self.probe.layer,
            "posterior": post,
            "o1_margin_source_minus_target": float(post[self.source] - post[self.target]),
            "o1_source": self.source, "o1_target": self.target,
            "hidden_norm": float((v ** 2).sum() ** 0.5),
            "n_forward_calls": self.n_forward_calls, "n_captures": self.n_captured}
        self.records.append(self._record)
        return output                        # READ-ONLY. Never returns an edited tensor.

    def __enter__(self):
        self._h = self.layer.register_forward_hook(self._hook)
        return self

    def __exit__(self, *exc):
        if self._h is not None:
            self._h.remove()
            self._h = None
        return False

    def liveness_violations(self) -> List[str]:
        bad = []
        if self.n_forward_calls == 0:
            bad.append("probe_read_hook_never_ran")
        if self.n_captured == 0:
            bad.append("probe_read_captured_zero_rows")
        if len(set(self._shas)) > 1:
            bad.append("probe_read_site_moved_between_forwards:%d distinct states at one index"
                       % len(set(self._shas)))
        if self.abs_index is not None and self._record is not None and (
                int(self._record["resolved_absolute_index"]) != int(self.abs_index)):
            bad.append("probe_read_index_is_not_the_pinned_one")
        return bad


def o1_from_probe_rows(rows: Sequence[Dict[str, Any]], read_layer: int) -> Dict[str, Any]:
    """O1 per row at ONE read layer, refusing a zero bind.

    Reading O1 at the layer that was edited is legitimate FOR O1 -- it is the same tensor, by
    design -- but it is not evidence of propagation, which is what `assert_read_sees_edit`
    enforces separately.
    """
    sel = [r for r in rows if int(r.get("read_layer", -1)) == int(read_layer)]
    if not sel:
        raise ZeroBinding("O1 at read layer %d bound ZERO probe records (of %d). A check that "
                          "binds nothing is not a check." % (read_layer, len(rows)))
    vals = [float(r["o1_margin_source_minus_target"]) for r in sel]
    shas = sorted({str(r.get("probe_sha256")) for r in sel})
    if len(shas) != 1:
        raise Refusal("the probe records at layer %d were produced by %d DIFFERENT probes %s. "
                      "O1 is defined against ONE frozen estimator." % (read_layer, len(shas), shas))
    return {"read_layer": int(read_layer), "n": len(vals), "values": vals,
            "probe_sha256": shas[0],
            "definition": "frozen PR-048 posterior(source) - posterior(target)"}


def liveness_gate(stats_rows: Sequence[Dict[str, Any]], arm_id: str,
                  expect_enabled: bool = True, tol: float = 1e-6) -> Dict[str, Any]:
    """Did this arm's hooks demonstrably FIRE and demonstrably CHANGE THE STATE?

    `primary.void`: `hook_fired_count == 0`; realised != expected cells; an arm's edit magnitude
    is 0. Any of those makes a null VOID rather than a negative, which is the distinction C-13
    says nothing in the current hook stack can make.

    MISSING IS NOT ZERO (C-117). Every field this gate rules on must be PRESENT in the record; a
    record that lacks one raises `NotMeasured` instead of being defaulted into a verdict. The
    producer -- `pair_common.hook_stats_dict` and the hooks around it -- now writes all of them,
    including `n_cells_edited_expected`, which it counts from the tensor each forward was handed
    BEFORE the write. A present-but-zero expected count is still a failure (a check that binds
    zero is not a check); an ABSENT one is not a failure at all, it is an unanswered question.
    """
    reasons: List[str] = []
    if not stats_rows:
        return {"arm_id": arm_id, "live": False, "n_rows": 0,
                "reasons": ["NO LIVENESS RECORDS AT ALL -- %s is absent or empty. A null behind an "
                            "unrecorded hook is VOID, not a negative." % CONTRACT_LIVENESS]}
    # NO DEFAULTS ON THE QUANTITIES THIS GATE RULES ON. `.get(k, 0)` is what turned an
    # unwritten field into "the arm declared no destinations" (C-117).
    # Each branch requires exactly what it RULES ON, and nothing else. A disabled-hook bridge
    # legitimately has no `cos_pre_post` and no `projection_removed_l2`: it never edited anything,
    # which is the point of it, and demanding those would refuse the control for being correct.
    _required = (("hook_fired_count", "n_cells_edited_realised", "projection_removed_l2",
                  "cos_pre_post", "activation_norm_pre", "n_cells_edited_expected", "enabled")
                 if expect_enabled else
                 ("hook_fired_count", "n_cells_edited_realised", "n_forward_calls", "enabled"))
    for _i, r in enumerate(stats_rows):
        _miss = [k for k in _required if k not in r or r[k] is None]
        if _miss:
            raise NotMeasured(
                "arm %s: liveness record %d/%d does not carry %s. This gate will not turn an "
                "UNRECORDED quantity into a scientific verdict about the arm; the record is "
                "incomplete and the arm is unjudged, which is a different thing from failing."
                % (arm_id, _i + 1, len(stats_rows), _miss))
    n_fired = sum(int(r["hook_fired_count"]) for r in stats_rows)
    n_rows_fired = sum(1 for r in stats_rows if int(r["hook_fired_count"]) > 0)
    realised = sum(int(r["n_cells_edited_realised"]) for r in stats_rows)
    expected = sum(int(r.get("n_cells_edited_expected") or 0) for r in stats_rows)
    mags = [float(r.get("projection_removed_l2") or 0.0) for r in stats_rows]
    zero_mag = sum(1 for m in mags if not (m > tol))
    # REVIEW F9: the two components used to encode OPPOSITE cosine policies. `pair_common`
    # deliberately does not gate `cos_pre_post == 1.0`, and its reason is right: at float32 a
    # genuine small edit rounds the cosine to 1.0, so gating on it refuses LIVE hooks. This gate
    # did the opposite at tol=1e-6, and at a reduced dose or a narrower band it would have voided
    # healthy arms. The state-changed question is answered instead by the SCALE-FREE relative
    # magnitude -- the same rule the producer applies -- and the cosine is required to be
    # RECORDED (mandate 10.3 persists it) rather than gated on a value.
    _rel_mag = [(float(r["projection_removed_l2"]) / float(r["activation_norm_pre"]))
                for r in stats_rows if expect_enabled and float(r["activation_norm_pre"]) > 0]
    unchanged = sum(1 for x in _rel_mag if x < 1.19e-7)
    disabled_flags = {bool(r["enabled"]) for r in stats_rows}

    if expect_enabled:
        if n_fired == 0:
            reasons.append("hook_fired_count == 0 over all %d records: THE HOOK NEVER FIRED. "
                           "This arm's result is VOID, not a null." % len(stats_rows))
        if n_rows_fired < len(stats_rows):
            reasons.append("only %d/%d records show a firing hook -- a partially dead hook edits a "
                           "different population than the one reported"
                           % (n_rows_fired, len(stats_rows)))
        if expected and realised != expected:
            reasons.append("n_cells_edited_realised %d != expected %d (primary.void)"
                           % (realised, expected))
        if not expected:
            reasons.append("n_cells_edited_expected is 0 everywhere: the arm declared no "
                           "destinations, so 'realised == expected' is vacuously true and proves "
                           "nothing (a check that binds zero is not a check)")
        if zero_mag:
            reasons.append("%d/%d records have projection_removed_l2 <= %g: a ZERO-MAGNITUDE EDIT "
                           "scores as a clean null" % (zero_mag, len(stats_rows), tol))
        if unchanged:
            reasons.append("%d/%d records have an edit below float32 resolution relative to the "
                           "state (||removed||/||h_pre|| < 1.19e-07): an under-dosed edit that "
                           "the readout cannot distinguish from no edit at all"
                           % (unchanged, len(stats_rows)))
        if False in disabled_flags:
            reasons.append("some records carry enabled=False in an arm that is supposed to be "
                           "LIVE -- the disabled-hook bridge leaked into a live arm")
    else:
        # the DISABLED-HOOK BRIDGE (C5): it must run the code path and edit nothing.
        if True in disabled_flags:
            reasons.append("the disabled-hook bridge carries enabled=True records -- it EDITED "
                           "something, so it is not a bridge")
        if n_fired:
            reasons.append("the disabled-hook bridge reports hook_fired_count=%d: it edited the "
                           "state and cannot certify anything" % n_fired)
        if realised:
            reasons.append("the disabled-hook bridge edited %d cells" % realised)
        if sum(int(r.get("n_forward_calls", 0)) for r in stats_rows) == 0:
            reasons.append("the disabled-hook bridge made ZERO forward calls -- the code path was "
                           "not exercised at all, so it bridges nothing")
    return {"arm_id": arm_id, "live": (not reasons), "n_rows": len(stats_rows),
            "n_fired": n_fired, "n_cells_realised": realised, "n_cells_expected": expected,
            "n_zero_magnitude": zero_mag, "n_under_dosed": unchanged,
            "n_unchanged_state": unchanged,
            "expect_enabled": expect_enabled, "reasons": reasons}


def orthogonal_residual_gate(stats_rows: Sequence[Dict[str, Any]],
                             tol: float = 1e-4) -> Dict[str, Any]:
    """`I-N7`, blocking: `||h_orth_pre - h_orth_post||` must be 0 to numerical tolerance.

    A RECORD THAT LACKS THE FIELD IS `NotMeasured`, NOT A VIOLATION (C-117). The previous version
    defaulted the absent field to NaN, `abs(nan) <= tol` is False, so every row counted as a
    violation and the gate asserted "the orthogonal component was NOT preserved; H2b is VOID" --
    a positive claim about the physics of the edit whose actual content was that the producer had
    never written the number. `pair_common` now measures it on every project_out edit (the change
    is `alpha*(h.d)d`, so its component orthogonal to `d` must be 0 to float error) and the
    analyzer's own component-replace hook measures it against `span{v_out, v_in}`.
    """
    if not stats_rows:
        raise ZeroBinding("orthogonal-residual gate over zero records")
    missing = [i for i, r in enumerate(stats_rows)
               if r.get("orthogonal_residual_delta_l2") is None]
    if missing:
        raise NotMeasured(
            "%d/%d liveness record(s) do not carry `orthogonal_residual_delta_l2` (first: index "
            "%d). I-N7 asks whether the orthogonal component was PRESERVED; an unrecorded "
            "quantity cannot answer it, and defaulting it to NaN would make this gate report a "
            "physical violation that nobody observed."
            % (len(missing), len(stats_rows), missing[0]))
    vals = [float(r["orthogonal_residual_delta_l2"]) for r in stats_rows]
    if any(v != v for v in vals):
        raise NotMeasured("an `orthogonal_residual_delta_l2` of NaN reached the I-N7 gate. NaN is "
                          "not a measurement and must not be read as a violation.")
    bad = [v for v in vals if not (abs(v) <= tol)]
    return {"n": len(vals), "max_abs": max(abs(v) for v in vals), "tol": tol,
            "n_violations": len(bad), "ok": not bad,
            "detail": ("the orthogonal component was NOT preserved; H2b is VOID (I-N7 is "
                       "blocking)" if bad else "")}


# ============================================================================================
# 3. THE CROSS-PROMPT DONOR (H1) -- `Q3`
# ============================================================================================
#
# `_WHAT_DOES_NOT_EXIST_YET` in the frozen config: `--rescue-donor` offers only `clean` and `self`,
# both on the SAME prompt. H1 needs a donor from a DIFFERENT prompt (C_knife) written into C_bomb.
#
# `DonorPatch(strict_ids=True)` compares `recipient_ids[p]` against `donor.input_ids[p]` at the
# SAME absolute index p. Across concepts the two prompts have DIFFERENT LENGTHS (mean cross-concept
# spread of the codeword's absolute index is 9.36 +/- 5.90 tokens, identical in 0/2300 triples), so
# one shared absolute position list is already wrong before any relaxation. Positions must be
# resolved END-RELATIVE in each prompt separately and PAIRED by offset.
#
# And the token-identity re-verification must be SCOPED: over a wide span the concept word itself
# ('bomb' vs 'knife') necessarily differs, and DonorPatch will refuse there. The contract below
# exempts EXACTLY that span and asserts identity everywhere else -- and refuses an exemption that
# is over-broad (an exempted offset whose tokens actually agree is a relaxation that bought
# nothing and hid something) or total (exempting the whole span turns strict_ids off).
def donor_span_contract(donor_ids: Sequence[int], recip_ids: Sequence[int],
                        rel_offsets: Sequence[int],
                        exempt_rel_offsets: Sequence[int] = ()) -> Dict[str, Any]:
    """Pair the patched span by end-relative offset and verify token identity off the exempt set."""
    rel = sorted(set(int(r) for r in rel_offsets))
    ex = sorted(set(int(r) for r in exempt_rel_offsets))
    if not rel:
        raise Refusal("the patched span is EMPTY. A patch over zero positions is a no-op that "
                      "would score as a clean null.")
    if not set(ex) <= set(rel):
        raise Refusal("exempt offsets %s are not a subset of the patched span %s"
                      % (sorted(set(ex) - set(rel)), rel))
    if ex and set(ex) == set(rel):
        raise Refusal("the exemption covers the ENTIRE patched span, which is strict_ids turned "
                      "off with extra steps. Refusing.")
    pairs, mism_nonexempt, exempt_but_identical = [], [], []
    for r in rel:
        dp = resolve_end_relative(donor_ids, r)
        rp = resolve_end_relative(recip_ids, r)
        same = donor_ids[dp] == recip_ids[rp]
        pairs.append({"rel_end": r, "donor_index": dp, "recipient_index": rp,
                      "donor_token": int(donor_ids[dp]), "recipient_token": int(recip_ids[rp]),
                      "identical": bool(same), "exempt": r in ex})
        if r in ex:
            if same:
                exempt_but_identical.append(r)
        elif not same:
            mism_nonexempt.append(r)
    if mism_nonexempt:
        raise Refusal(
            "REFUSING to patch: %d of %d NON-EXEMPT offsets do not carry the same token in donor "
            "and recipient (first offenders %s). Donor and recipient must be token-identical over "
            "the patched span outside the declared concept-word exemption, or the patch writes "
            "the right activations to the wrong places."
            % (len(mism_nonexempt), len(rel), mism_nonexempt[:5]))
    if exempt_but_identical:
        raise Refusal(
            "REFUSING: offsets %s were declared EXEMPT from the token-identity check but their "
            "tokens are identical anyway. An exemption that is not needed is an over-broad "
            "relaxation of the one guard that stops a misaligned patch -- declare exactly the "
            "concept-word span and nothing else." % exempt_but_identical)
    return {"pairs": pairs, "n_positions": len(rel), "n_exempt": len(ex),
            "n_strict": len(rel) - len(ex),
            "donor_indices": [p["donor_index"] for p in pairs],
            "recipient_indices": [p["recipient_index"] for p in pairs]}


def build_cross_prompt_donor(model, layer_idx: int, donor_ids: Sequence[int],
                             recip_ids: Sequence[int], rel_offsets: Sequence[int],
                             exempt_rel_offsets: Sequence[int] = (), capture=None):
    """Capture at the donor's resolved indices; return a DonorBlock addressed in RECIPIENT indices.

    `strict_ids=True` is kept ON. The `input_ids` handed to the DonorBlock are the DONOR's tokens
    at the paired donor indices, placed at the RECIPIENT indices -- so `DonorPatch`'s check
    (`recipient_ids[p] == donor.input_ids[p]`) re-verifies, for every strictly-checked position,
    that the token whose activation is being written matches the token being written over. That is
    the real safety property; it is not weakened, it is correctly addressed.

    Exempt positions are carried in a SEPARATE, LABELLED block so that the count of positions
    written without an identity check appears in the artifact instead of hiding inside a relaxed
    predicate.
    """
    from donor_patch import ActivationCapture, DonorBlock  # noqa: F401  (contract, imported here)
    contract = donor_span_contract(donor_ids, recip_ids, rel_offsets, exempt_rel_offsets)
    strict = [p for p in contract["pairs"] if not p["exempt"]]
    exempt = [p for p in contract["pairs"] if p["exempt"]]
    if capture is None:
        raise Refusal("build_cross_prompt_donor needs the donor's captured activations; capturing "
                      "them is the caller's job (ActivationCapture over the donor forward) so the "
                      "capture and the patch cannot silently use different position lists.")
    idx_of = {p["donor_index"]: i for i, p in enumerate(contract["pairs"])}
    strict_rows = capture[[idx_of[p["donor_index"]] for p in strict]] if strict else None
    exempt_rows = capture[[idx_of[p["donor_index"]] for p in exempt]] if exempt else None
    blocks = []
    if strict:
        synthetic_ids = list(recip_ids)
        for p in strict:
            synthetic_ids[p["recipient_index"]] = p["donor_token"]
        blocks.append(("strict", DonorBlock(layer_idx=layer_idx,
                                            positions=[p["recipient_index"] for p in strict],
                                            acts=strict_rows, input_ids=synthetic_ids)))
    if exempt:
        blocks.append(("exempt_concept_word_span",
                       DonorBlock(layer_idx=layer_idx,
                                  positions=[p["recipient_index"] for p in exempt],
                                  acts=exempt_rows, input_ids=list(recip_ids))))
    return {"contract": contract, "blocks": blocks,
            "n_written_with_identity_check": len(strict),
            "n_written_without_identity_check": len(exempt)}


def self_patch_gate(baseline_sha: str, selfpatch_sha: str) -> Dict[str, Any]:
    """`C7` / `I-N2`, blocking. Patch the target with ITS OWN activations: the output MUST be
    EXACTLY reproduced. If `self` changes the output, the patch is not writing what it read and no
    patch number downstream means anything."""
    ok = (baseline_sha == selfpatch_sha) and bool(baseline_sha)
    return {"ok": ok, "baseline_sha256": baseline_sha, "self_patch_sha256": selfpatch_sha,
            "detail": ("" if ok else
                       "THE SELF-PATCH CHANGED THE OUTPUT. The patch is not writing what it read; "
                       "every H1 number is VOID until this reproduces.")}


def disabled_bridge_gate(baseline_sha: str, bridge_sha: str,
                         max_abs_hidden_diff: Optional[float]) -> Dict[str, Any]:
    """`C5` / `I-N1`, blocking: byte-identical greedy generations AND max|diff| == 0.000e+00."""
    same_text = bool(baseline_sha) and baseline_sha == bridge_sha
    same_state = (max_abs_hidden_diff is not None and float(max_abs_hidden_diff) == 0.0)
    return {"ok": bool(same_text and same_state), "baseline_sha256": baseline_sha,
            "bridge_sha256": bridge_sha, "max_abs_hidden_diff": max_abs_hidden_diff,
            "detail": ("" if (same_text and same_state) else
                       "the disabled-hook bridge did not reproduce the untouched baseline "
                       "(text_identical=%s, hidden_max_diff=%r). The intervention code path "
                       "changes the result even with the hook off, so no arm run through it is "
                       "interpretable." % (same_text, max_abs_hidden_diff))}


def control_band_gate(per_draw_sha: Sequence[str], n_expected: int) -> Dict[str, Any]:
    """`C1` / `I-N4`: the 5 draws must produce 5 DISTINCT output hashes.

    This project has TWICE published a control band that was secretly n=1 because the seed never
    reached the draw -- once producing byte-identical gens.jsonl across three nominal seeds and a
    fake between-draw sd of 0.0048. Identical hashes VOID the control band. The tell, both times,
    was arms agreeing to four decimals.
    """
    shas = list(per_draw_sha)
    uniq = len(set(shas))
    ok = (len(shas) == n_expected) and (uniq == n_expected) and all(shas)
    return {"n_draws": len(shas), "n_expected": n_expected, "n_distinct": uniq, "ok": ok,
            "detail": ("" if ok else
                       "the control band has %d draws with %d distinct output hashes (expected %d "
                       "of each). A band whose draws agree byte-for-byte is n=1 and cannot measure "
                       "draw-to-draw variance." % (len(shas), uniq, n_expected))}


# ============================================================================================
# 4. DIRECTION PROVENANCE -- TRAIN ONLY, and the sha is recomputed at load
# ============================================================================================
def direction_provenance_gate(fit_manifest: Dict[str, Any], assign: Dict[str, str],
                              direction_path: Optional[str] = None) -> Dict[str, Any]:
    """`I-N10` / `Q2`. Directions come from PR-053, TRAIN ONLY. `primary.void`: a direction fitted
    on validation or test voids the arm. The direction file could not be pinned in the frozen
    config (it did not exist), so its sha256 is RECOMPUTED here and written into the artifact."""
    doms = fit_manifest.get("fit_domains")
    if doms is None:
        raise Refusal("the direction fit manifest does not name its fit domains. A direction whose "
                      "provenance cannot be checked is not usable: `primary.void` names 'a "
                      "direction fitted on validation or test' explicitly.")
    unknown = sorted(d for d in doms if d not in assign)
    leaked = sorted(d for d in doms if assign.get(d) in ("validation", "test"))
    sha = sha256_file(direction_path) if direction_path and os.path.exists(direction_path) else None
    return {"n_fit_domains": len(doms), "n_unknown_domains": len(unknown),
            "leaked_domains": leaked, "direction_file_sha256": sha,
            "ok": (not leaked) and (not unknown) and bool(doms),
            "detail": ("" if not leaked else
                       "VOID: the direction was fitted on %d validation/test domains (%s)"
                       % (len(leaked), leaked[:5]))}


# ============================================================================================
# 5. THE READ SITE MUST BE ABLE TO SEE THE INTERVENTION (C-068)
# ============================================================================================
def propagation_read_layers(edit_layers: Sequence[int], grid: Sequence[int],
                            n_layers: int) -> List[int]:
    """Layers at which a PROPAGATION claim may be read: strictly above the edited band.

    `C-068`: at the band floor the arms are bit-identical, so a read inside (or below) the edited
    band cannot see the intervention and its null is a statement about the read site. The frozen
    config says the same in `_read_must_be_at_or_above_the_edit`: reading the probe at block 9 for
    an edit at block 9 is legitimate FOR O1 (it is the same tensor, deliberately) but is NOT
    evidence of propagation; propagation uses blocks 10-14 or the downstream neutral position.
    """
    if not edit_layers:
        raise Refusal("propagation_read_layers called with no edited layers")
    hi = max(int(x) for x in edit_layers)
    out = [int(L) for L in grid if int(L) > hi]
    if not out:
        out = [L for L in range(hi + 1, int(n_layers)) if L < int(n_layers)][:1]
    if not out:
        raise Refusal("no read layer exists above the edited band %s in a %d-layer model; a "
                      "propagation claim cannot be made from this edit." % (sorted(edit_layers),
                                                                           n_layers))
    return out


def assert_read_sees_edit(read_layer: int, edit_layers: Sequence[int], purpose: str) -> None:
    if purpose == "propagation" and int(read_layer) <= max(int(x) for x in edit_layers):
        raise Refusal(
            "read layer %d is not above the edited band %s. A propagation claim read at or below "
            "the edit is C-068: at the band floor the arms are bit-identical and the null is a "
            "statement about the read site, not about the model."
            % (read_layer, sorted(int(x) for x in edit_layers)))


# ============================================================================================
# 6. THE ARM MANIFEST (mandate 10.1 -> 10.2 -> 10.3, in that order)
# ============================================================================================
@dataclass
class ArmSpec:
    arm_id: str
    role: str                      # "live" | "control"
    family_member: Optional[str]   # H1xS1 ... H2bxS2, or None for a control
    hypothesis: str                # H1 | H2a | H2b | C1..C7
    scope: str                     # S1 | S2
    layers: List[int]
    mode: str                      # patch | project_out | component_replace | add | disabled
    direction: Optional[str]
    source_concept: Optional[str]
    target_concept: str
    codeword: str
    dose_units: str
    alpha: float
    control_draw_seed: Optional[int]
    expect_enabled: bool
    note: str = ""

    def tag(self) -> str:
        return "ts116m_pr057_%s" % self.arm_id


def build_arm_manifest(pr: Prereg) -> List[ArmSpec]:
    """Every run this phase submits, in mandate section 10 order. Declared BEFORE any outcome."""
    s1 = pr.require("scope_levels", "S1")
    s2 = pr.require("scope_levels", "S2")
    read_layer = int(pr.require("read_site", "primary_read_layer"))
    band = [int(x) for x in pr.require("read_site", "read_layer_grid")]
    codewords = pr.require("population", "codewords")
    seed = int(pr.require("seeds", "control_draws"))
    n_draws = int(pr.require("seeds", "n_control_draws"))

    # S1 is BLOCK 9 only (the site the frozen PR-048 selection named on VALIDATION); S2 is the
    # band the probe reads. Both are parsed from the frozen file rather than typed here.
    if str(read_layer) not in str(s1.get("site", "")):
        raise Refusal("scope_levels.S1.site %r does not name the primary read layer %d; refusing "
                      "to guess which block the single-site arm edits." % (s1.get("site"), read_layer))
    s1_layers = [read_layer]
    s2_layers = band
    if not s2_layers:
        raise Refusal("read_site.read_layer_grid is empty; S2 would edit nothing")

    arms: List[ArmSpec] = []

    # ---- 10.1 UPPER-BOUND ACTIVATION PATCH, FIRST. The four directed pairs are strata; they are
    # declared here so running one later cannot be a post-hoc rescue.
    h1 = next(h for h in pr.require("hypotheses") if h["id"] == "H1")
    pairs = [("knife", "bomb"), ("gun", "bomb"), ("bomb", "knife"), ("bomb", "gun")]
    for scope, layers in (("S1", s1_layers), ("S2", s2_layers)):
        for src, tgt in pairs:
            for cw in sorted(codewords.values()):
                arms.append(ArmSpec(
                    arm_id="h1_%s_%s_from_%s_%s" % (scope.lower(), tgt, src, cw),
                    role="live", family_member="H1x%s" % scope, hypothesis="H1", scope=scope,
                    layers=list(layers), mode="patch", direction=None,
                    source_concept=src, target_concept=tgt, codeword=cw,
                    dose_units="n/a (whole-state replacement)", alpha=1.0,
                    control_draw_seed=None, expect_enabled=True,
                    note=h1["_it_is_an_upper_bound_on_purpose"]))

    # ---- 10.2 SURGICAL SUBSPACE INTERVENTION, SECOND.
    v_spec = "v_bomb_specific"
    v_in = "v_knife_specific"
    for scope, layers in (("S1", s1_layers), ("S2", s2_layers)):
        for cw in sorted(codewords.values()):
            arms.append(ArmSpec(
                arm_id="h2a_%s_projout_%s" % (scope.lower(), cw), role="live",
                family_member="H2ax%s" % scope, hypothesis="H2a", scope=scope,
                layers=list(layers), mode="project_out", direction=v_spec,
                source_concept="knife", target_concept="bomb", codeword=cw,
                dose_units="scale-free; realised dose = frac_cellmean_spread_removed",
                alpha=1.0, control_draw_seed=None, expect_enabled=True))
            arms.append(ArmSpec(
                arm_id="h2b_%s_replace_%s" % (scope.lower(), cw), role="live",
                family_member="H2bx%s" % scope, hypothesis="H2b", scope=scope,
                layers=list(layers), mode="component_replace", direction=v_spec,
                source_concept="knife", target_concept="bomb", codeword=cw,
                dose_units="c_knife = TRAIN-mean component of C_knife along %s" % v_in,
                alpha=1.0, control_draw_seed=None, expect_enabled=True,
                note="orthogonal residual preserved EXACTLY and VERIFIED (I-N7, blocking)"))

    # ---- 10.3 CONTROLS, all seven, all predeclared. C6 is the PHASE 7 run itself: no new job.
    for scope, layers in (("S1", s1_layers), ("S2", s2_layers)):
        for matched in ("h2a", "h2b"):
            for k in range(n_draws):
                arms.append(ArmSpec(
                    arm_id="c1_random_%s_%s_draw%d" % (scope.lower(), matched, k),
                    role="control", family_member=None, hypothesis="C1", scope=scope,
                    layers=list(layers), mode="project_out", direction="random_norm_matched",
                    source_concept="knife", target_concept="bomb", codeword="button",
                    dose_units="norm- and dose-matched to %s" % matched, alpha=1.0,
                    control_draw_seed=seed + k, expect_enabled=True,
                    note="THE DECISIVE CONTROL: success requires that it does NOT move O2, and the "
                         "%d draws must have %d DISTINCT output hashes" % (n_draws, n_draws)))
        arms.append(ArmSpec(
            arm_id="c2_shuffled_%s" % scope.lower(), role="control", family_member=None,
            hypothesis="C2", scope=scope, layers=list(layers), mode="project_out",
            direction="v_bomb_specific_shuffled_labels", source_concept="knife",
            target_concept="bomb", codeword="button", dose_units="same estimator, same norm",
            alpha=1.0, control_draw_seed=seed, expect_enabled=True))
        arms.append(ArmSpec(
            arm_id="c3_vremap_%s" % scope.lower(), role="control", family_member=None,
            hypothesis="C3", scope=scope, layers=list(layers), mode="project_out",
            direction="v_remap", source_concept="knife", target_concept="bomb", codeword="button",
            dose_units="scale-free", alpha=1.0, control_draw_seed=None, expect_enabled=True,
            note="declared as 'the raw axis', NOT as the remapping-only axis: R-111's question D "
                 "FAILED and no arm in this design isolates remapping"))
        arms.append(ArmSpec(
            arm_id="c4_samenorm_orth_%s" % scope.lower(), role="control", family_member=None,
            hypothesis="C4", scope=scope, layers=list(layers), mode="add",
            direction="orthogonal_to_concept_subspace", source_concept="knife",
            target_concept="bomb", codeword="button",
            dose_units="GAP UNITS, L2-matched to the concept edit (Q6)", alpha=1.0,
            control_draw_seed=seed, expect_enabled=True,
            note="separates 'the concept direction matters' from 'perturbing this site by this "
                 "much matters'"))
        # ---- C-119, RESOLVED BY INTERPRETATION, AND THE INTERPRETATION IS RECORDED ---------
        # This arm used to carry `alpha=0.0` with the gloss "none -- the hook is registered and
        # edits nothing". That reading makes the control CERTIFY NOTHING, and it is refused
        # twice over: `pair_common.project_out_liveness_violations` refuses a bridge whose inner
        # hook `would_have_changed_max_abs == 0`, and the frozen config lists "the disabled-hook
        # bridge not reproducing baseline" under `primary.void`, so an UNEVALUABLE void condition
        # is a hole in the validity argument rather than a satisfied one.
        #
        # WHAT THE FROZEN FILE ACTUALLY SAYS. `controls.arms[C5].rule` is: "the full intervention
        # code path with the hook DISABLED. MUST reproduce the untouched baseline generations
        # byte-for-byte ... and the untouched hidden states at max|diff| == 0.000e+00". It states
        # NO alpha for C5 and no dose for it anywhere -- `alpha=0.0` was a literal typed into
        # THIS file, not a preregistered quantity, and this file is not frozen. The
        # interpretation adopted is therefore the operational reading of its own words: "the full
        # intervention code path" is the LIVE arm's path, at the LIVE arm's dose, and "the hook
        # DISABLED" is `DisabledHookBridge` -- the hook registered on the same layer objects,
        # RUN IN FULL, and its write discarded. `alpha` is what the code path is run AT; the
        # bridge's dose-to-the-model is zero because nothing is written, not because alpha is.
        #
        # WHY IT MUST BE THE LIVE ALPHA AND NOT ANY ALPHA. What C5 certifies is that the
        # machinery AROUND the edit -- layer resolution, direction load, dtype/device cast,
        # projection -- is inert. Run at alpha=0 the projection is `h - 0*(h.d)d`, an identity:
        # the bridge would reproduce the baseline even if the direction were garbage, the layer
        # wrong and the hook installed on the whole model. It would pass for reasons that have
        # nothing to do with what it is asked. At the live alpha the inner hook computes the real
        # edit, `would_have_changed_max_abs > 0` proves the machinery ran, and the byte-identical
        # output then means what C5 says it means. `alpha` is matched to the H2a arm this bridge
        # shadows (`v_bomb_specific`, scale-free project_out, alpha=1.0) so the discarded write
        # is exactly the arm's write.
        arms.append(ArmSpec(
            arm_id="c5_disabled_bridge_%s" % scope.lower(), role="control", family_member=None,
            hypothesis="C5", scope=scope, layers=list(layers), mode="disabled",
            direction="v_bomb_specific", source_concept="knife", target_concept="bomb",
            codeword="button",
            dose_units="the LIVE arm's dose, RUN IN FULL and DISCARDED -- the bridge's dose to "
                       "the model is zero because nothing is written, not because alpha is",
            alpha=1.0, control_draw_seed=None, expect_enabled=False,
            note="BLOCKING: must reproduce the untouched baseline byte-for-byte and the hidden "
                 "states at max|diff| == 0.000e+00. C-119: alpha is the H2a arm's alpha, not 0; "
                 "an alpha=0 bridge is an identity that would pass with a garbage direction on "
                 "the wrong layer. The frozen file preregisters no alpha for C5."))
        arms.append(ArmSpec(
            arm_id="c7_selfpatch_%s" % scope.lower(), role="control", family_member=None,
            hypothesis="C7", scope=scope, layers=list(layers), mode="patch",
            direction=None, source_concept="bomb", target_concept="bomb", codeword="button",
            dose_units="n/a", alpha=1.0, control_draw_seed=None, expect_enabled=True,
            note="BLOCKING: patch the target with ITS OWN activations; the output must be EXACTLY "
                 "reproduced or no patch number means anything"))
    return arms


def family_members(pr: Prereg) -> List[str]:
    fam = holm_family(pr, PR_ID)
    if fam["family"] != "PHASE9_CAUSAL":
        raise Refusal("%s does not sit in PHASE9_CAUSAL but in %r; the correction this analyzer "
                      "applies would be over the wrong family (C-106)." % (PR_ID, fam["family"]))
    if len(fam["members"]) != 6:
        raise Refusal("PHASE9_CAUSAL declares %d members, not the six H1/H2a/H2b x S1/S2 this "
                      "analyzer corrects across" % len(fam["members"]))
    out = []
    for m in fam["members"]:
        h = "H1" if " H1 " in m else "H2a" if "H2a" in m else "H2b" if "H2b" in m else None
        s = "S1" if "S1" in m else "S2" if "S2" in m else None
        if not h or not s:
            raise Refusal("cannot parse hypothesis/scope out of family member %r" % m)
        out.append("%sx%s" % (h, s))
    return out


# ============================================================================================
# 7. STATISTICS
# ============================================================================================
def holm(pvals: Dict[str, float], alpha: float, m: Optional[int] = None) -> Dict[str, Any]:
    """Holm-Bonferroni over a DECLARED family. A declared member that was not run enters at p=1.0
    (`_absent_members_enter_at_p_1`), never dropped -- dropping it would shrink the family and make
    every surviving member easier to declare significant."""
    if not pvals:
        raise ZeroBinding("Holm over an EMPTY family")
    m = int(m or len(pvals))
    order = sorted(pvals.items(), key=lambda kv: kv[1])
    out, rejected = {}, True
    for i, (k, p) in enumerate(order):
        thr = alpha / (m - i)
        if rejected and p <= thr:
            out[k] = {"p": p, "threshold": thr, "reject": True}
        else:
            rejected = False
            out[k] = {"p": p, "threshold": thr, "reject": False}
    return {"m": m, "alpha": alpha, "per_member": out,
            "n_rejected": sum(1 for v in out.values() if v["reject"])}


def domain_group_permutation(per_domain_pre: Dict[str, List[float]],
                             per_domain_post: Dict[str, List[float]],
                             n_perm: int, seed: int) -> Dict[str, Any]:
    """Arm-label flip WITHIN DOMAIN, at the DOMAIN level. Never row-level.

    `I-N8` / `_row_level_warning`: the measured row-level FPR on this design is 0.2000, and a
    row-level p prints 1.02e-06 where the honest domain-level p is 0.05. The unit of independence
    is the domain and the permutation respects it: the whole domain's paired sign flips together.
    """
    doms = sorted(set(per_domain_pre) & set(per_domain_post))
    if not doms:
        raise ZeroBinding("permutation bound ZERO domains -- the two arms share no domain")
    deltas = []
    for d in doms:
        a, b = per_domain_pre[d], per_domain_post[d]
        if not a or not b:
            raise ZeroBinding("domain %r contributes an empty arm to the paired contrast" % d)
        deltas.append(sum(b) / len(b) - sum(a) / len(a))
    obs = sum(deltas) / len(deltas)
    rng = random.Random(seed)
    null = []
    for _ in range(int(n_perm)):
        null.append(sum(x if rng.random() < 0.5 else -x for x in deltas) / len(deltas))
    p, floor, nex = group_permutation_p(abs(obs), [abs(x) for x in null])
    k = sum(1 for x in deltas if x > 0)
    ties = sum(1 for x in deltas if x == 0.0)
    sp, sfloor = sign_test_two_sided(max(k, len(deltas) - k), len(deltas))
    return {"n_domains": len(doms), "observed_delta": obs, "per_domain_delta": dict(zip(doms, deltas)),
            "permutation": {"p": p, "floor": floor, "n_exceed": nex, "n_perm": int(n_perm),
                            "formatted": fmt_p(p, floor, nex)},
            "sign_test": {"k_positive": k, "n": len(deltas), "n_exact_ties": ties,
                          "p": sp, "floor": sfloor, "formatted": fmt_p(sp, sfloor)},
            "majority_moved_intended": None}


def equivalence_interval(deltas: Sequence[float], alpha: float) -> Dict[str, Any]:
    """A control must be shown NOT to move O2. That is an equivalence question and is reported
    with its interval, NEVER as a bare p > 0.05 (`_control_arms_are_not_members`)."""
    n = len(deltas)
    if n < 2:
        raise ZeroBinding("equivalence interval over n<2 domains")
    m = sum(deltas) / n
    sd = math.sqrt(sum((x - m) ** 2 for x in deltas) / (n - 1))
    se = sd / math.sqrt(n)
    try:
        from scipy import stats as _st
        tcrit = float(_st.t.isf(alpha / 2.0, n - 1))
    except Exception:
        tcrit = 1.96
    return {"n": n, "mean": m, "sd": sd, "se": se,
            "ci_low": m - tcrit * se, "ci_high": m + tcrit * se, "alpha": alpha}


# ============================================================================================
# 8. THE CONJUNCTIVE SUCCESS RULE (mandate 10.5) -- all four, separately
# ============================================================================================
@dataclass
class ConditionResult:
    name: str
    passed: bool
    detail: str
    value: Any = None


def evaluate_success(o1: Dict[str, Any], o2: Dict[str, Any], control: Dict[str, Any],
                     across_domains: Dict[str, Any], alpha: float,
                     expected_sign: float = 1.0) -> Dict[str, Any]:
    """Mandate 10.5: FOUR conditions, conjunctively. Any three of four is NOT a causal result.

    Each condition alone has a cheap way to be satisfied -- (1) by construction, (2) by a large
    enough perturbation of anything, (3) by an under-dosed control, (4) by a lucky pooling.
    Together they do not, which is why this design can return a clean negative.
    """
    conds: List[ConditionResult] = []

    c1_ok = (o1 is not None and o1.get("p") is not None
             and o1["p"] < alpha and _sign(o1.get("delta", 0.0)) == _sign(expected_sign))
    conds.append(ConditionResult(
        "1_probe_moves_intended", bool(c1_ok),
        "O1 (frozen PR-048 probe posterior margin) moves in the intended direction, "
        "significantly, at the DOMAIN level", o1))

    c2_ok = (o2 is not None and o2.get("p") is not None
             and o2["p"] < alpha and _sign(o2.get("delta", 0.0)) == _sign(expected_sign))
    conds.append(ConditionResult(
        "2_semantic_readout_moves_intended", bool(c2_ok),
        "O2 (the semantic readout -- the MODEL-INTERPRETATION variable) moves in the intended "
        "direction, significantly, at the DOMAIN level", o2))

    # A control that "fails to reach significance" is NOT a passed control.
    c3_ok = bool(control is not None and control.get("distinct_hashes_ok")
                 and control.get("equivalence") is not None
                 and control.get("moved") is False)
    conds.append(ConditionResult(
        "3_matched_random_control_does_not_move", c3_ok,
        "C1 norm-matched random control does NOT move O2, reported with its equivalence interval "
        "rather than a bare p>alpha, and its draws have distinct output hashes", control))

    c4_ok = bool(across_domains is not None and across_domains.get("majority_moved_intended")
                 and across_domains.get("sign_p") is not None
                 and across_domains["sign_p"] < alpha)
    conds.append(ConditionResult(
        "4_holds_across_domains", c4_ok,
        "the effect HOLDS ACROSS DOMAINS by a domain-level sign test, not as a pooled-row result",
        across_domains))

    all_ok = all(c.passed for c in conds)
    return {"conditions": [asdict(c) for c in conds], "n_passed": sum(c.passed for c in conds),
            "success": all_ok,
            "_conjunctive_on_purpose": "any three of four is NOT a causal result"}


def _sign(x: float) -> int:
    return (x > 0) - (x < 0)


def verdict(success: Dict[str, Any], liveness_ok: bool, o1_moved: bool, o2_moved: bool,
            power_ok: bool, wording: str) -> str:
    """The ONLY place a verdict string is produced.

    Order matters and is fixed by the frozen file:
      * an unclean hook is VOID FIRST -- `_and_the_other_negative`: a null with an unverified hook
        is VOID, not a negative;
      * then underpowered is CANNOT ANSWER;
      * then the conjunction;
      * then the mandated negative wording, which is a literal and cannot drift.
    """
    if not liveness_ok:
        return ("VOID -- HOOK LIVENESS UNCLEAN. This arm's hooks did not demonstrably fire and "
                "demonstrably change the state, so its null is a statement about the hook and not "
                "about the model. Check hook liveness, dose, and the disabled-hook bridge FIRST.")
    if not power_ok:
        return ("CANNOT ANSWER -- power below the declared bar at the realised between-domain SD "
                "of O2. Reported without a causal claim in either direction.")
    if success.get("success"):
        return ("SUPPORTS CLAIM C UNDER THIS INTERVENTION -- all four of mandate 10.5's conditions "
                "hold together at these sites, this dose and this population.")
    if o1_moved and not o2_moved:
        return wording
    if (not o1_moved) and (not o2_moved):
        return ("VOID PENDING DIAGNOSIS -- neither O1 nor O2 moved, which means the arm may not "
                "have done what it claimed. Check hook liveness, dose and the disabled-hook "
                "bridge before calling this a negative.")
    return ("NOT A CAUSAL RESULT -- the conjunctive criterion is not met (%d/4 conditions). "
            "Reported as such, per condition." % success.get("n_passed", 0))


# ============================================================================================
# 9. ARTIFACT LOADING AND POPULATION BINDING
# ============================================================================================
def bank_sha_gate(pr: Prereg, bank_key: str, rows_sha16: Optional[str]) -> Dict[str, Any]:
    """Verify a run's bank sha against the pin. A wrong bank sha is `primary.void`."""
    want = pr.require("population", "banks", bank_key, "bank_rows_sha16")
    ok = (rows_sha16 == want)
    return {"bank": bank_key, "pinned": want, "observed": rows_sha16, "ok": ok,
            "detail": "" if ok else "VOID: run bank sha disagrees with the pin"}


def missing_row_gate(expected_ids: Sequence[str], present_ids: Sequence[str],
                     id_domain: Dict[str, str], excluded: Sequence[str]) -> Dict[str, Any]:
    """A missing row is acceptable ONLY if its domain is a preregistered exclusion (R-108)."""
    miss = sorted(set(expected_ids) - set(present_ids))
    unexplained = sorted({i for i in miss if id_domain.get(i) not in set(excluded)})
    return {"n_expected": len(set(expected_ids)), "n_present": len(set(present_ids)),
            "n_missing": len(miss), "n_unexplained": len(unexplained),
            "unexplained_examples": unexplained[:5], "ok": not unexplained,
            "detail": ("" if not unexplained else
                       "%d missing rows are NOT explained by a preregistered exclusion; refusing "
                       "to analyse a silently truncated population (R-108)" % len(unexplained))}


def load_jsonl(path: str) -> List[Dict[str, Any]]:
    out = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def load_arm_run(run_dir: str) -> Dict[str, Any]:
    """Load one arm's artifacts, refusing on anything absent that the contract requires."""
    need = ("DONE.json", "results.jsonl", "summary.json", "RUNMETA.json")
    for n in need:
        if not os.path.exists(os.path.join(run_dir, n)):
            raise Refusal("%s is missing from %s. A directory without %s is a PARTIAL run and is "
                          "not analysed (C-051/C-012)." % (n, run_dir, n))
    done = json.load(open(os.path.join(run_dir, "DONE.json")))
    if done.get("status") != "ok":
        raise Refusal("%s reports status %r" % (run_dir, done.get("status")))
    out = {"run_dir": run_dir, "done": done,
           "summary": json.load(open(os.path.join(run_dir, "summary.json"))),
           "runmeta": json.load(open(os.path.join(run_dir, "RUNMETA.json"))),
           "results": load_jsonl(os.path.join(run_dir, "results.jsonl"))}
    for key, fn in (("arm_manifest", CONTRACT_ARM),):
        p = os.path.join(run_dir, fn)
        out[key] = json.load(open(p)) if os.path.exists(p) else None
    for key, fn in (("liveness", CONTRACT_LIVENESS), ("probe", CONTRACT_PROBE)):
        p = os.path.join(run_dir, fn)
        out[key] = load_jsonl(p) if os.path.exists(p) else []
    return out


def option_mass_gate(summary: Dict[str, Any], channel: str) -> Dict[str, Any]:
    """`cannot_answer`: a DISENGAGED primary channel is CANNOT ANSWER, not a licence to fall back
    on the 3-way forced-choice display channel (mandate section 11)."""
    om = (summary.get("option_mass") or {}).get("semantic/%s" % channel)
    if om is None:
        raise Refusal("summary.json carries no option_mass for semantic/%s; the channel's "
                      "engagement is unmeasured and cannot be assumed" % channel)
    return {"channel": channel, "median_true": om.get("median_true"),
            "reportable": bool(om.get("reportable")), "n": om.get("n"),
            "gate": summary.get("option_mass_gate"),
            "ok": bool(om.get("reportable")) and summary.get("option_mass_gate") == "PASS"}


#: The fields the 10.2 PRIMARY outcome is built from. All THREE already exist on every PHASE 7
#: `results.jsonl` row (`score_behavior.py`, the semantic branch), plus `option_mass_core_pair`
#: which was added alongside the Q9 flag and is identical to `option_mass` when the flag is off.
O2_10_2_FIELDS = ("logp_concept", "logp_codeword", "semantic_logodds")

#: Gates that MUST accompany the 10.2 primary. `semantic_logodds` alone cannot separate "the
#: bomb reading fell" from "the readout was destroyed" -- these are what separate them, and the
#: outcome is not reportable without them. Named here so the requirement is a data structure and
#: not a sentence in a report nobody re-reads.
O2_10_2_REQUIRED_COMPANION_GATES = (
    "option_mass_gate: the semantic_one_word channel must still be ENGAGED after the edit. A "
    "destroyed readout collapses option_mass; a moved readout does not.",
    "C1 norm-matched random control (5 distinct draws): a fall that the random control "
    "reproduces is 'this much perturbation', not 'this axis'.",
    "C4 same-norm edit orthogonal to the concept subspace, dosed in gap units: same separation, "
    "from the other side.",
    "C5 disabled-hook bridge: reproduces the untouched baseline byte-for-byte.",
    "hook liveness clean (liveness_gate): a fall measured through an unverified hook is VOID.",
)


def o2_projection_out_from_rows(rows: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    """O2 for the C-112 PRIMARY (mandate 10.2): does the TARGET CONCEPT reading fall?

    THE Q9(a) ANSWER, WITH THE FIELD NAMES.

    Mandate 10.2 projects `v_bomb_specific` out of a BOMB prompt. The intervention and the
    prompt carry the SAME concept, so the outcome needs no source-concept log-odds and no second
    installed concept: the question is whether the model's semantic reading of the codeword
    moves AWAY from that concept. That contrast is
    `semantic_logodds = logp_concept - logp_codeword`, computed on every PHASE 7 row today by
    `score_behavior.py`'s semantic branch, where on a bomb bank `concept == "bomb"` and
    `codeword == "button"`. Concretely, per row:

        logp_concept            log P(the concept word | prompt), whole-answer, variant-summed
        logp_codeword           log P(the literal codeword | prompt), same rule
        semantic_logodds        logp_concept - logp_codeword          <-- THE OUTCOME
        option_mass_core_pair   P(concept) + P(codeword)              <-- the engagement gate
        top1_id / gens.jsonl    the free one-word answer               <-- O3, corroborant only

    and the statistic is the domain-mean change in `semantic_logodds` between the intervened arm
    and the untouched PHASE 7 baseline, on TEST domains, exactly as `primary.statistic` defines
    it for the cross-concept case.

    WHY IT IS SUFFICIENT HERE AND WAS NOT THERE. The objection to `semantic_logodds` recorded
    against the 10.1 arm is that a fall cannot be told from a destroyed readout -- for a CLAIM
    THAT THE ANSWER MOVED TOWARD KNIFE, which needs logP(knife) and therefore needed Q9's flag.
    The 10.2 primary makes no such claim. Its claim is directional and one-sided: removing the
    bomb component reduces the bomb reading. "Destroyed" is not an alternative interpretation of
    that claim, it is a RIVAL CAUSE for the same observation, and rival causes are what the
    preregistered controls are for -- which is why they are returned here as
    `required_companion_gates` rather than left to a reader's memory. Without them this number
    is not reportable, and `reportable_alone` says so.

    Refuses a zero bind and a missing field; never substitutes one field for another.
    """
    if not rows:
        raise ZeroBinding("O2 (10.2 primary) over ZERO rows")
    have = set(rows[0].keys())
    missing = [f for f in O2_10_2_FIELDS if f not in have]
    if missing:
        raise Refusal(
            "the 10.2 PRIMARY outcome needs %s and the rows carry none of %s. These are PHASE 7 "
            "fields that every semantic row has emitted since 2026-08-18; their absence means "
            "this is not a semantic_one_word readout, not that the outcome should be "
            "substituted." % (list(O2_10_2_FIELDS), missing))
    vals = [float(r["semantic_logodds"]) for r in rows]
    mass_field = ("option_mass_core_pair" if "option_mass_core_pair" in have
                  else ("option_mass" if "option_mass" in have else None))
    if mass_field is None:
        raise Refusal("no option_mass on these rows, so channel engagement is UNMEASURED. A "
                      "forced choice decided inside a 1e-5 tail is not a forced choice.")
    return {
        "computable": True, "values": vals, "n": len(vals),
        "mandate": "10.2", "primary_under": C112_PRIMARY_IS_10_2,
        "definition": "semantic_logodds = logp_concept - logp_codeword (target concept vs the "
                      "literal codeword), domain-mean delta vs the untouched baseline",
        "fields_used": list(O2_10_2_FIELDS),
        "engagement_field": mass_field,
        "engagement_values": [float(r[mass_field]) for r in rows],
        "direction_expected": "FALLS under projection-out of v_bomb_specific",
        "reportable_alone": False,
        "required_companion_gates": list(O2_10_2_REQUIRED_COMPANION_GATES),
        "_what_it_cannot_say": "It cannot say the answer moved TOWARD another concept. That is "
                               "the exploratory 10.1 claim and it needs logp_knife, which "
                               "requires --semantic-extra-words (Q9).",
    }


def o2_from_rows(rows: Sequence[Dict[str, Any]], source: str, target: str) -> Dict[str, Any]:
    """O2 = semantic log-odds of the SOURCE concept against the TARGET concept, per row.

    Requires the multi-concept answer set (BLOCKER_Q9). If only the single-concept PHASE 7 schema
    is present, this returns `computable=False` and the caller must emit CANNOT ANSWER: the
    companion `semantic_logodds` (target concept vs the literal codeword) is REPORTED but cannot
    satisfy success condition 2, because it cannot distinguish 'the answer moved toward knife'
    from 'the readout was destroyed'.
    """
    if not rows:
        raise ZeroBinding("O2 over ZERO rows")
    have = set(rows[0].keys())
    missing = [f for f in O2_REQUIRED_FIELDS if f not in have]
    if missing:
        partial = [r[O2_PARTIAL_FIELD] for r in rows if O2_PARTIAL_FIELD in r]
        return {"computable": False, "missing_fields": missing,
                "blocker": BLOCKER_Q9,
                "companion_name": "delta semantic_logodds(target concept vs literal codeword)",
                "companion_values": partial,
                "companion_note": "REPORTED ONLY. It cannot satisfy success condition 2."}
    vals = [float(r["logp_%s" % source]) - float(r["logp_%s" % target]) for r in rows]
    return {"computable": True, "values": vals, "n": len(vals),
            "definition": "logp_%s - logp_%s (source minus target), natural log odds"
                          % (source, target)}


# ============================================================================================
# 10. Q1 -- POWER ON VALIDATION ONLY, AS A CODE PATH
# ============================================================================================
def power_bar(pr: Prereg) -> float:
    """The power bar, PARSED OUT OF THE FROZEN FILE rather than typed as 0.80 here.

    `pre_extraction_checklist` Q1 states it in prose -- "if power < 0.8, return CANNOT ANSWER
    WITHOUT READING TEST" -- and `primary.cannot_answer` repeats it. A threshold published in prose
    that no code path reads is B-020, which this project has now committed three times; a
    threshold RE-TYPED in the analyzer is the same defect with a different fingerprint, because
    the file and the code can then disagree without either being wrong on its own.
    """
    import re as _re
    texts = [str(i.get("item", "")) for i in pr.require("pre_extraction_checklist")
             if i.get("id") == "Q1"]
    texts.append(str(pr.require("primary", "cannot_answer")))
    for t in texts:
        m = _re.search(r"power\s*<\s*(0?\.\d+)", t)
        if m:
            return float(m.group(1))
    raise Refusal("neither checklist Q1 nor primary.cannot_answer states a parseable power bar; "
                  "refusing to invent 0.8 in the analyzer.")


def q1_power(pr: Prereg, per_domain_delta: Dict[str, float]) -> Dict[str, Any]:
    """Measure the between-domain SD of O2 on VALIDATION DOMAINS ONLY and decide, BEFORE TEST.

    `power.o2_semantic_readout.between_domain_sd` is deliberately `null` in the frozen file --
    "NOT MEASURED, NOT ASSUMED TO A NUMBER" -- because none of the three SDs in the record is the
    same variance component. `underpowered_branch` says the phase returns WITHOUT READING TEST if
    power < 0.8, and that this MUST exist as a code path rather than only as prose. It does: this
    function, and `main`'s `--power-q1` return.
    """
    mde_declared = float(pr.require("power", "declared_minimum_meaningful_effect",
                                    "o2_semantic_logodds_shift"))
    alpha = float(pr.require("primary", "alpha"))
    n_test = int(pr.require("primary", "n_test_domains"))
    if pr.require("power", "o2_semantic_readout", "between_domain_sd") is not None:
        raise Refusal("power.o2_semantic_readout.between_domain_sd is no longer null in the frozen "
                      "file. Q1 measures it; a value pre-filled there would be the borrowed number "
                      "the file explicitly refuses to carry.")
    vals = list(per_domain_delta.values())
    if len(vals) < 2:
        raise ZeroBinding("Q1 measured the SD over %d validation domains" % len(vals))
    m = sum(vals) / len(vals)
    sd = math.sqrt(sum((x - m) ** 2 for x in vals) / (len(vals) - 1))
    if sd <= 0:
        raise Refusal("the measured between-domain SD of O2 is %r on validation. A zero SD means "
                      "every domain returned the identical value, which is the byte-identical-arms "
                      "signature, not a measurement." % sd)
    bar = power_bar(pr)
    power = t_power(n_test, mde_declared, sd, alpha=alpha)
    mde = t_mde(n_test, sd, alpha=alpha, power=bar)
    ok = power >= bar
    return {"n_validation_domains": len(vals), "measured_between_domain_sd": sd,
            "validation_mean_delta": m,
            "declared_mde": mde_declared, "alpha": alpha, "n_test_domains": n_test,
            "power_at_declared_mde": power, "power_bar": bar, "mde_at_power_bar": mde,
            "power_ok": ok,
            "decision": ("PROCEED -- power >= %.2f for the declared %.2f-nat effect"
                         % (bar, mde_declared)
                         if ok else
                         "CANNOT ANSWER WITHOUT READING TEST -- power %.3f < the declared bar for "
                         "the declared "
                         "%.2f-nat effect at the measured SD %.4f. Mandate section 20: do not "
                         "knowingly run a major confirmatory experiment whose likely negative "
                         "would be uninterpretable. Return a costed fix (more domains, or a more "
                         "informative estimator chosen BEFORE data)."
                         % (power, mde_declared, sd))}


# ============================================================================================
# 11. SELF-TEST -- CPU only, synthetic data, exercising the REAL functions
# ============================================================================================
def _toy_layer(hidden: int = 8):
    import torch
    import torch.nn as nn

    class Blk(nn.Module):
        def forward(self, x):
            return (x,)
    return Blk()


def selftest() -> int:
    import torch
    ck = Checks()
    ok_all = True

    # ---- end-relative index resolution -------------------------------------------------
    ids_a = list(range(100))
    ids_b = list(range(137))
    ia = resolve_end_relative(ids_a, -10)
    ib = resolve_end_relative(ids_b, -10)
    ck.add("end_relative", "len(ids)+rel_end, and the ABSOLUTE index differs between two prompts "
           "of different length (0/2300 triples agree)", ia == 90 and ib == 127 and ia != ib, 2)
    caught = False
    try:
        resolve_end_relative(ids_a, 90)
    except Refusal:
        caught = True
    ck.add("absolute_index_refused", "a non-negative (absolute) index is REFUSED", caught, 1)
    aud = audit_end_relative([{"seq_len": 100, "rel_end": -10, "resolved_absolute_index": 90},
                              {"seq_len": 137, "rel_end": -10, "resolved_absolute_index": 127}])
    ck.add("index_audit", "the end-relative audit passes on correct records", aud["ok"], aud["n_records"])
    bad = audit_end_relative([{"seq_len": 100, "rel_end": -10, "resolved_absolute_index": 90},
                              {"seq_len": 137, "rel_end": -10, "resolved_absolute_index": 90}])
    ck.add("index_audit_mutant", "an ABSOLUTE index reused across prompts is caught",
           not bad["ok"] and bad["n_absolute_index_violations"] == 1, bad["n_records"])

    # ---- LIVE hook fires and changes the state -----------------------------------------
    torch.manual_seed(20260907)
    hidden = 8
    x = torch.randn(1, 12, hidden)
    d = torch.randn(hidden)
    layer = _toy_layer(hidden)
    st = LivenessStats(arm_id="unit_live")
    hook = make_instrumented_project_out_hook(d, st, positions=[resolve_end_relative(range(12), -3)])
    with InstrumentedHook(layer, 9, hook, st):
        y = layer(x)[0]
    live = liveness_gate([st.as_row()], "unit_live", expect_enabled=True)
    changed = float((y - x).norm()) > 0
    ck.add("live_hook", "a live project-out hook fires, edits exactly the expected cells, and "
           "changes the state", live["live"] and changed and st.hook_fired_count == 1, 1,
           "reasons=%s" % live["reasons"])

    # ---- DISABLED hook is DETECTED as disabled -----------------------------------------
    st_d = LivenessStats(arm_id="unit_bridge", enabled=False)
    hook_d = make_instrumented_project_out_hook(d, st_d, positions=[9], enabled=False)
    with InstrumentedHook(layer, 9, hook_d, st_d):
        y_d = layer(x)[0]
    bridge = liveness_gate([st_d.as_row()], "unit_bridge", expect_enabled=False)
    as_live = liveness_gate([st_d.as_row()], "unit_bridge", expect_enabled=True)
    ck.add("disabled_hook_detected",
           "a DELIBERATELY DISABLED hook reproduces the input exactly, PASSES as a bridge, and is "
           "REFUSED when presented as a live arm -- the C-13 failure mode, caught",
           bool(torch.equal(y_d, x)) and bridge["live"] and not as_live["live"], 1,
           "as_live_reasons=%s" % as_live["reasons"][:1])

    # ---- a hook that never runs (dead) --------------------------------------------------
    st_dead = LivenessStats(arm_id="unit_dead", n_cells_edited_expected=1)
    dead = liveness_gate([st_dead.as_row()], "unit_dead", expect_enabled=True)
    ck.add("dead_hook_refused", "a hook with hook_fired_count == 0 is VOID, not a null",
           not dead["live"] and any("never fired" in r.lower() or "hook_fired_count == 0" in r
                                    for r in dead["reasons"]), 1)

    # ---- zero-norm direction ------------------------------------------------------------
    caught = False
    try:
        make_instrumented_project_out_hook(torch.zeros(hidden), LivenessStats())
    except Refusal:
        caught = True
    ck.add("zero_direction_refused", "a zero-norm direction is refused before it can score a null",
           caught, 1)

    # ---- H2b orthogonal residual preservation ------------------------------------------
    v_out = torch.randn(hidden)
    v_in = torch.randn(hidden)
    st_r = LivenessStats(arm_id="unit_h2b")
    hook_r = make_instrumented_component_replace_hook(v_out, v_in, 0.7, st_r, positions=[9])
    with InstrumentedHook(layer, 9, hook_r, st_r):
        _ = layer(x)
    g = orthogonal_residual_gate([st_r.as_row()])
    ck.add("h2b_orthogonal_preserved",
           "counterfactual component replacement preserves the orthogonal residual, VERIFIED "
           "numerically rather than asserted", g["ok"], g["n"], "max_abs=%.3e" % g["max_abs"])
    bad_g = orthogonal_residual_gate([{"orthogonal_residual_delta_l2": 0.031}])
    ck.add("h2b_orthogonal_mutant", "a broken orthogonal-residual preservation is caught (I-N7)",
           not bad_g["ok"], 1)

    # ---- gap-unit dosing (Q6) ------------------------------------------------------------
    ck.add("gap_units", "an ADD is dosed in GAP UNITS: alpha=2 at gap=14.65 injects 29.31",
           abs(gap_unit_alpha(2.0, 14.653462) - 29.306924) < 1e-9, 1)
    caught = False
    try:
        gap_unit_alpha(1.0, None)
    except Refusal:
        caught = True
    ck.add("bare_alpha_refused", "a bare alpha with no gap is REFUSED (the aggressive_patching bug, "
           "missed once at a second call site)", caught, 1)

    # ---- cross-prompt donor contract (Q3) ------------------------------------------------
    donor = [5, 5, 5, 11, 700, 22, 33, 44]          # len 8
    recip = [7, 7, 9, 9, 9, 11, 900, 22, 33, 44]    # len 10; the last three tokens agree, and
    #                                                 rel_end -4 is the CONCEPT WORD (700 vs 900)
    c = donor_span_contract(donor, recip, rel_offsets=[-3, -2, -1])
    ck.add("donor_span_identical", "over a token-identical tail the contract pairs by END-RELATIVE "
           "offset across prompts of DIFFERENT length and asserts identity",
           c["n_positions"] == 3 and c["n_strict"] == 3
           and c["donor_indices"] == [5, 6, 7] and c["recipient_indices"] == [7, 8, 9], 3)
    caught = False
    try:
        donor_span_contract(donor, recip, rel_offsets=[-4, -3, -2, -1])
    except Refusal as e:
        caught = "NON-EXEMPT" in str(e)
    ck.add("donor_span_mismatch_refused",
           "the concept word inside the patched span REFUSES unless it is declared exempt -- this "
           "is the rejection DonorPatch(strict_ids=True) makes even on the aligned bank", caught, 1)
    c2 = donor_span_contract(donor, recip, rel_offsets=[-4, -3, -2, -1],
                             exempt_rel_offsets=[-4])
    ck.add("donor_span_exemption", "the concept-word span is exempted EXACTLY and identity is "
           "asserted everywhere else", c2["n_exempt"] == 1 and c2["n_strict"] == 3, 4)
    caught = False
    try:
        donor_span_contract(donor, recip, rel_offsets=[-3, -2, -1], exempt_rel_offsets=[-2])
    except Refusal as e:
        caught = "not needed" in str(e) or "over-broad" in str(e)
    ck.add("donor_exemption_overbroad_refused",
           "an exemption over a token that is identical anyway is refused as over-broad", caught, 1)
    caught = False
    try:
        donor_span_contract(donor, recip, rel_offsets=[-4], exempt_rel_offsets=[-4])
    except Refusal as e:
        caught = "ENTIRE" in str(e)
    ck.add("donor_exemption_total_refused",
           "exempting the whole span is strict_ids turned off and is refused", caught, 1)

    # ---- self-patch and disabled bridge --------------------------------------------------
    ck.add("self_patch_gate", "a self-patch that reproduces the output passes; one that does not, "
           "fails", self_patch_gate("aa", "aa")["ok"] and not self_patch_gate("aa", "bb")["ok"], 2)
    ck.add("bridge_gate", "the disabled-hook bridge must match text AND hidden states exactly",
           disabled_bridge_gate("aa", "aa", 0.0)["ok"]
           and not disabled_bridge_gate("aa", "aa", 1e-9)["ok"]
           and not disabled_bridge_gate("aa", "bb", 0.0)["ok"], 3)

    # ---- control band distinctness --------------------------------------------------------
    ck.add("control_band", "5 distinct draw hashes pass; a secretly-n=1 band is VOID",
           control_band_gate(list("abcde"), 5)["ok"]
           and not control_band_gate(["a"] * 5, 5)["ok"], 2)

    # ---- direction provenance --------------------------------------------------------------
    assign = {"d%d" % i: ("train" if i < 5 else "test") for i in range(8)}
    good = direction_provenance_gate({"fit_domains": ["d0", "d1", "d2"]}, assign)
    bad_p = direction_provenance_gate({"fit_domains": ["d0", "d7"]}, assign)
    ck.add("direction_provenance", "a TRAIN-only fit passes; a fit touching test is VOID",
           good["ok"] and not bad_p["ok"], 2)

    # ---- read site sees the edit (C-068) ----------------------------------------------------
    grid = [7, 8, 9, 10, 11, 12, 13, 14]
    ck.add("propagation_read_S1", "for an edit at block 9 the propagation read is 10-14",
           propagation_read_layers([9], grid, 32) == [10, 11, 12, 13, 14], 1)
    ck.add("propagation_read_S2", "for a 7-14 band edit the propagation read is above 14",
           propagation_read_layers(grid, grid, 32) == [15], 1)
    caught = False
    try:
        assert_read_sees_edit(9, [9], "propagation")
    except Refusal:
        caught = True
    ck.add("read_at_edit_refused", "a PROPAGATION claim read at the edited layer is refused (C-068)",
           caught, 1)

    # ---- domain-level permutation, never row-level -------------------------------------------
    rng = random.Random(1)
    pre = {"d%d" % i: [rng.gauss(0, 1) for _ in range(10)] for i in range(23)}
    post = {k: [x + 0.9 for x in v] for k, v in pre.items()}
    r = domain_group_permutation(pre, post, n_perm=2000, seed=7)
    ck.add("perm_domain_level", "the permutation flips WHOLE DOMAINS and recovers a planted shift",
           r["n_domains"] == 23 and r["observed_delta"] > 0.5
           and r["permutation"]["p"] <= 0.05, r["n_domains"],
           "delta=%.3f %s" % (r["observed_delta"], r["permutation"]["formatted"]))
    null_post = {k: list(v) for k, v in pre.items()}
    r0 = domain_group_permutation(pre, null_post, n_perm=2000, seed=7)
    ck.add("perm_null_centred", "with no effect the permutation null is centred at 0 (I-N8)",
           abs(r0["observed_delta"]) < 1e-12 and r0["permutation"]["p"] > 0.05, r0["n_domains"])
    caught = False
    try:
        domain_group_permutation({}, {}, n_perm=10, seed=1)
    except ZeroBinding:
        caught = True
    ck.add("perm_zero_bind", "a permutation that binds ZERO domains fails loudly", caught, 1)

    # ---- p printed beside its floor -----------------------------------------------------------
    ck.add("p_floor", "a p at the floor is never printed bare",
           "FLOOR" in fmt_p(1.0 / 10001, 1.0 / 10001, 0), 1)

    # ---- Holm across the six family members ----------------------------------------------------
    h = holm({"H1xS1": 0.001, "H1xS2": 0.02, "H2axS1": 0.30, "H2axS2": 0.40,
              "H2bxS1": 0.50, "H2bxS2": 1.0}, alpha=0.05)
    ck.add("holm", "Holm over the SIX declared members; an absent member enters at p=1.0",
           h["m"] == 6 and h["per_member"]["H1xS1"]["reject"]
           and not h["per_member"]["H2axS1"]["reject"], 6)

    # ---- the conjunctive success rule -----------------------------------------------------------
    good_o1 = {"p": 0.001, "delta": 0.8}
    good_o2 = {"p": 0.002, "delta": 0.9}
    good_ctl = {"distinct_hashes_ok": True, "equivalence": {"ci_low": -0.05, "ci_high": 0.05},
                "moved": False}
    good_dom = {"majority_moved_intended": True, "sign_p": 0.004}
    s_all = evaluate_success(good_o1, good_o2, good_ctl, good_dom, alpha=0.05)
    ck.add("success_all_four", "all four conditions together = success", s_all["success"], 4)
    for drop, label in ((("o1",), "probe"), (("o2",), "readout"), (("ctl",), "control"),
                        (("dom",), "across-domains")):
        a1, a2, a3, a4 = good_o1, good_o2, good_ctl, good_dom
        if "o1" in drop:
            a1 = {"p": 0.5, "delta": 0.0}
        if "o2" in drop:
            a2 = {"p": 0.5, "delta": 0.0}
        if "ctl" in drop:
            a3 = {"distinct_hashes_ok": True, "equivalence": {}, "moved": True}
        if "dom" in drop:
            a4 = {"majority_moved_intended": False, "sign_p": 0.9}
        s = evaluate_success(a1, a2, a3, a4, alpha=0.05)
        ok_all &= (not s["success"]) and s["n_passed"] == 3
        ck.add("success_needs_%s" % label, "three of four is NOT a causal result",
               (not s["success"]) and s["n_passed"] == 3, 4)

    # ---- the mandated negative wording -----------------------------------------------------------
    s_neg = evaluate_success({"p": 0.001, "delta": 0.8}, {"p": 0.7, "delta": 0.0},
                             good_ctl, good_dom, alpha=0.05)
    v = verdict(s_neg, liveness_ok=True, o1_moved=True, o2_moved=False, power_ok=True,
                wording=MANDATORY_NEGATIVE_WORDING)
    ck.add("negative_wording", "probe moves + readout does not => the literal mandated wording",
           v == MANDATORY_NEGATIVE_WORDING, 1, v)
    v_void = verdict(s_neg, liveness_ok=False, o1_moved=True, o2_moved=False, power_ok=True,
                     wording=MANDATORY_NEGATIVE_WORDING)
    ck.add("negative_refused_without_liveness",
           "the SAME numbers with unclean hook liveness return VOID, never a negative",
           v_void.startswith("VOID"), 1)
    caught = False
    try:
        assert_sayable("in short, the representation is meaningless")
    except Refusal:
        caught = True
    ck.add("forbidden_wording", "the forbidden sentence cannot be emitted, by construction", caught, 1)

    # ---- O2 schema ---------------------------------------------------------------------------------
    todays_row = {"logp_concept": -2.5, "logp_codeword": -0.95, "semantic_logodds": -1.545,
                  "option_mass": 0.47}
    r_today = o2_from_rows([todays_row], "knife", "bomb")
    ck.add("o2_schema_refuses_today",
           "the PHASE 7 schema as it stands cannot express O2 (source vs target concept); the "
           "analyzer says so instead of substituting the companion",
           r_today["computable"] is False and r_today["missing_fields"], 1)
    ext = {"logp_bomb": -2.5, "logp_knife": -1.2, "logp_gun": -4.0, "logp_codeword": -0.95}
    r_ext = o2_from_rows([ext], "knife", "bomb")
    ck.add("o2_schema_extended", "with the multi-concept answer set O2 is the source-minus-target "
           "log-odds", r_ext["computable"] and abs(r_ext["values"][0] - 1.3) < 1e-9, 1)

    # ---- missing rows / bank sha -------------------------------------------------------------------
    mg = missing_row_gate(["a", "b", "c"], ["a", "b"], {"c": "restaurant_kitchen"},
                          ["restaurant_kitchen"])
    mg2 = missing_row_gate(["a", "b", "c"], ["a", "b"], {"c": "art_gallery"},
                           ["restaurant_kitchen"])
    ck.add("missing_rows", "a missing row is acceptable ONLY inside a preregistered exclusion (R-108)",
           mg["ok"] and not mg2["ok"], 2)

    # ---- Q1: the underpowered branch is a CODE PATH, not prose -------------------------------------
    try:
        _pr = load(PREREG_DEFAULT)
        bar = power_bar(_pr)
        rng2 = random.Random(3)
        tight = {"d%d" % i: rng2.gauss(0.4, 0.9) for i in range(23)}
        wide = {"d%d" % i: rng2.gauss(0.1, 3.0) for i in range(23)}
        q_ok = q1_power(_pr, tight)
        q_bad = q1_power(_pr, wide)
        ck.add("q1_power_bar_parsed", "the power bar is PARSED out of the frozen file, never typed "
               "as a literal here", abs(bar - 0.8) < 1e-12, 1, "bar=%r" % bar)
        ck.add("q1_underpowered_branch",
               "Q1 returns PROCEED at a tight validation SD and CANNOT ANSWER WITHOUT READING TEST "
               "at a wide one -- mandate section 20 as a code path",
               q_ok["power_ok"] and (not q_bad["power_ok"])
               and "CANNOT ANSWER WITHOUT READING TEST" in q_bad["decision"], 2,
               "power %.3f vs %.3f" % (q_ok["power_at_declared_mde"],
                                       q_bad["power_at_declared_mde"]))
        caught = False
        try:
            q1_power(_pr, {"only": 1.0})
        except ZeroBinding:
            caught = True
        ck.add("q1_needs_domains", "Q1 over fewer than two validation domains fails loudly",
               caught, 1)
        # the arm manifest and the family it is corrected in
        arms = build_arm_manifest(_pr)
        mem = family_members(_pr)
        realised = {a.family_member for a in arms if a.family_member}
        ck.add("manifest_covers_family",
               "the arm manifest schedules a run for EVERY declared family member, and both scope "
               "levels are present as DISTINCT arms (mandate 10.4)",
               set(mem) == realised and len(mem) == 6, len(arms),
               "members=%s" % sorted(realised))
        ck.add("manifest_controls",
               "all seven of mandate 10.3's controls are declared (C6 is the PHASE 7 baseline "
               "itself and needs no new job)",
               {a.hypothesis for a in arms} >= {"C1", "C2", "C3", "C4", "C5", "C7"}, len(arms))
        ck.add("manifest_h1_before_h2",
               "H1 (the upper bound) is scheduled before H2 -- mandate section 10 fixes the order",
               arms[0].hypothesis == "H1", len(arms))
    except PreregError as e:
        ck.add("prereg_loads", "the frozen preregistration loads", False, 0, str(e)[:120])

    # ================================================================================
    # BLOCKERS Q9 / Q10 / Q11 / Q12 / Q13 -- cleared 2026-09-07. Every check below drives
    # the REAL shared-file code, never a re-implementation of it.
    # ================================================================================
    import pair_common as _pc
    import score_behavior as _sb

    # ---- Q9: the C-112 primary outcome, on a PHASE 7-shaped row --------------------------
    _row7 = {"logp_concept": -1.0, "logp_codeword": -3.0, "semantic_logodds": 2.0,
             "option_mass": 0.09, "option_mass_core_pair": 0.09, "domain": "d1"}
    _o2p = o2_projection_out_from_rows([_row7])
    ck.add("q9_10_2_primary_computable",
           "the C-112 PRIMARY outcome (mandate 10.2) is computable from the PHASE 7 fields that "
           "exist TODAY -- logp_concept / logp_codeword / semantic_logodds -- with no donor and "
           "no second installed concept",
           _o2p["computable"] and _o2p["values"] == [2.0]
           and _o2p["fields_used"] == list(O2_10_2_FIELDS), 1,
           _o2p["definition"][:70])
    ck.add("q9_10_2_not_reportable_alone",
           "and it is NOT reportable alone: the companion gates that separate 'the reading fell' "
           "from 'the readout was destroyed' are returned as data, not left in prose",
           (_o2p["reportable_alone"] is False)
           and len(_o2p["required_companion_gates"]) >= 5, 1)
    _caught = False
    try:
        o2_projection_out_from_rows([{"option_mass": 0.1}])
    except Refusal:
        _caught = True
    ck.add("q9_10_2_missing_field_refused",
           "a row without semantic_logodds is REFUSED, never substituted", _caught, 1)

    # ---- Q10: the frozen probe, exported, loaded, and never refitted ---------------------
    import numpy as _np
    _hid = 6
    _blob = {"selected_layer": 9, "selected_C": 0.01,
             "classes": ["bomb", "knife", "gun"], "sklearn_classes_": [0, 1, 2],
             "feature_dim": _hid,
             "estimator": {"coef": [[1.0] + [0.0] * (_hid - 1),
                                    [0.0, 1.0] + [0.0] * (_hid - 2),
                                    [0.0, 0.0, 1.0] + [0.0] * (_hid - 3)],
                           "intercept": [0.0, 0.0, 0.0]},
             "scaler": {"mean": [0.0] * _hid, "scale": [1.0] * _hid},
             "sha256": "deadbeef",
             "self_verification": {"reproduced_from_exported_numbers": True,
                                   "n_disagreements": 0}}
    _fp = FrozenProbe(_blob)
    _post = _fp.posterior(_np.array([3.0, 0.0, 0.0, 0.0, 0.0, 0.0]))
    ck.add("q10_frozen_probe_scores",
           "the frozen probe reconstructs a posterior from the EXPORTED numbers alone (coef, "
           "intercept, scaler) -- the same rule dcs_ts_pr048_analysis self-verifies against its "
           "own sklearn objects before it will write the artifact",
           abs(sum(_post.values()) - 1.0) < 1e-9 and _post["bomb"] > _post["knife"], 3,
           "P(bomb)=%.4f" % _post["bomb"])
    ck.add("q10_o1_margin",
           "O1 is posterior(source) - posterior(target), exactly outcome_variables.O1_probe",
           abs(_fp.margin(_np.array([3.0, 0, 0, 0, 0, 0]), "knife", "bomb")
               - (_post["knife"] - _post["bomb"])) < 1e-12, 1)
    _caught = False
    try:
        _fp.margin(_np.zeros(_hid), "hammer", "bomb")
    except Refusal:
        _caught = True
    ck.add("q10_absent_class_refused",
           "a concept the probe was never fitted on is a REFUSAL, not a silent 0.0 (which would "
           "make every intervention look like it moved the margin)", _caught, 1)
    _caught = False
    try:
        _z = json.loads(json.dumps(_blob))
        _z["estimator"]["coef"] = [[0.0] * _hid] * 3
        FrozenProbe(_z)
    except Refusal:
        _caught = True
    ck.add("q10_zero_coefficient_probe_refused",
           "an ALL-ZERO probe is refused: it returns the same posterior under every intervention "
           "and would score as a clean O1 null", _caught, 1)
    _caught = False
    try:
        _z = json.loads(json.dumps(_blob))
        _z.pop("self_verification")
        import tempfile as _tf
        with _tf.NamedTemporaryFile("w", suffix=".json", delete=False) as _f:
            json.dump({FROZEN_PROBE_KEY: _z}, _f)
            _pth = _f.name
        load_frozen_probe(_pth)
    except Refusal:
        _caught = True
    ck.add("q10_unverified_export_refused",
           "an export whose producer never proved it reproduces its own estimator is refused -- "
           "an unverified export is a check that reads the producer's own null field", _caught, 1)
    _caught = False
    try:
        import tempfile as _tf
        with _tf.NamedTemporaryFile("w", suffix=".json", delete=False) as _f:
            json.dump({"selected_layer": 9}, _f)
            _pth2 = _f.name
        load_frozen_probe(_pth2)
    except Refusal:
        _caught = True
    ck.add("q10_missing_probe_block_refused",
           "a PR-048 result JSON with no FROZEN_PROBE block is refused and NAMES the fix; O1 has "
           "nothing to score against without it", _caught, 1)

    # ---- Q11: O1 captured INSIDE the intervention run, read-only -------------------------
    _layer = _toy_layer(_hid)
    _recs: List[Dict[str, Any]] = []
    _x = torch.randn(1, 11, _hid)
    with ProbeReadCapture(_layer, 9, _fp, -3, "knife", "bomb", _recs,
                          row_meta={"prompt_id": "p1"}) as _prc:
        _y = _layer(_x)[0]
    ck.add("q11_probe_read_is_read_only",
           "the O1 capture hook returns the state UNCHANGED -- a read hook that edited would "
           "contaminate the very arm it measures, invisibly, because that arm is supposed to be "
           "edited",
           float((_y - _x).abs().max()) == 0.0, len(_recs))
    ck.add("q11_probe_read_captures_o1",
           "and it captures O1 at the END-RELATIVE site, recording seq_len + rel_end",
           len(_recs) == 1 and _recs[0]["resolved_absolute_index"] == 11 - 3
           and _recs[0]["seq_len"] == 11 and not _prc.liveness_violations(), 1,
           "o1=%.4f" % _recs[0]["o1_margin_source_minus_target"])
    _caught = False
    try:
        ProbeReadCapture(_layer, 9, _fp, 8, "knife", "bomb", [])
    except Refusal:
        _caught = True
    ck.add("q11_absolute_read_index_refused",
           "a NON-NEGATIVE (absolute) read index is refused -- the twice-recorded bug class",
           _caught, 1)
    _dead = ProbeReadCapture(_layer, 9, _fp, -3, "knife", "bomb", [])
    ck.add("q11_capture_that_never_ran_is_detected",
           "a capture that never ran reports n_forward_calls == 0 rather than an absent file",
           _dead.liveness_violations() == ["probe_read_hook_never_ran",
                                           "probe_read_captured_zero_rows"], 1)
    _caught = False
    try:
        o1_from_probe_rows([], 15)
    except ZeroBinding:
        _caught = True
    ck.add("q11_o1_zero_bind_refused", "O1 over ZERO probe records is a refusal", _caught, 1)

    # ---- C-118(a): ATTRIBUTION, AND THE MANY-FORWARDS PROBLEM ----------------------------
    # One row makes MANY forwards of DIFFERENT lengths (the readout scores each answer variant).
    # Unpinned, `seq_len + rel_end` reads a different token on each of them; pinned, all of them
    # read the site resolved against the ROW's prompt, ONE record is emitted, and the caller's
    # row_meta names the DOMAIN -- which is what makes a domain-level O1 formable at all.
    _prow: List[Dict[str, Any]] = []
    _lp = _toy_layer(_hid)
    _xp = torch.randn(1, 11, _hid)
    _xp2 = torch.cat([_xp, torch.randn(1, 4, _hid)], dim=1)     # the same prompt + a variant
    with ProbeReadCapture(_lp, 9, _fp, -3, "knife", "bomb", _prow,
                          row_meta={"prompt_id": "p1", "domain": "warehouse"},
                          abs_index=8, seq_len_at_resolution=11) as _prc2:
        _lp(_xp); _lp(_xp2)
    ck.add("c118a_probe_records_name_their_domain",
           "C-118(a): O1 is a DOMAIN-LEVEL statistic, and the record carries the row's domain "
           "because the hook is built in the row loop and handed the row's metadata -- "
           "attribution by CONSTRUCTION, never by the order records arrive in",
           len(_prow) == 1 and _prow[0]["domain"] == "warehouse"
           and _prow[0]["prompt_id"] == "p1", 1, str(_prow[0]["domain"]))
    ck.add("c118a_site_is_pinned_across_forwards",
           "TWO forwards of DIFFERENT lengths produce ONE record at the SAME pinned index. "
           "Unpinned this hook would have read index 8 on the 11-token forward and index 12 on "
           "the 15-token one, and O1 would have been a mean over two different tokens",
           _prc2.n_forward_calls == 2 and _prc2.n_captured == 2 and len(_prow) == 1
           and _prow[0]["resolved_absolute_index"] == 8
           and _prow[0]["index_pinned_to_row_prompt"] is True
           and not _prc2.liveness_violations(), 2,
           "forwards=%d records=%d idx=%d" % (_prc2.n_forward_calls, len(_prow),
                                              _prow[0]["resolved_absolute_index"]))
    for _kw, _lbl in ((dict(abs_index=8), "no seq_len_at_resolution"),
                      (dict(abs_index=9, seq_len_at_resolution=11), "abs != seq + rel_end")):
        _caught = False
        try:
            ProbeReadCapture(_lp, 9, _fp, -3, "knife", "bomb", [], **_kw)
        except Refusal:
            _caught = True
        ck.add("c118a_pin_audited_%s" % _lbl.split()[0],
               "a pinned read index that cannot be checked against `seq_len + rel_end` (%s) is "
               "REFUSED: an unaudited absolute index is the bug class the pin exists to avoid"
               % _lbl, _caught, 1)

    # ---- Q12: single-position scoping and the DISABLED-HOOK BRIDGE -----------------------
    # Driven against the REAL pair_common classes, on a toy layer, with the REAL stats dicts.
    _d = torch.randn(_hid)
    _xa = torch.randn(1, 9, _hid)
    _sa = _pc.hook_stats_dict(mode="project_out_all", layer=3)
    _la = _toy_layer(_hid)
    with _pc.AllPositionProjectOut(_la, 3, _d, alpha=1.0, stats=_sa):
        _ya = _la(_xa)[0]
    _n_moved_all = int(((_ya - _xa).abs().amax(dim=-1) > 1e-6).sum())

    # rel_end=-3 against a 9-token row RESOLVES to absolute 6, and all three numbers are handed
    # to the hook so that `resolved_absolute_index == seq_len_at_resolution + rel_end` is an
    # assertion the constructor makes rather than a comment (review F3).
    _ss = _pc.hook_stats_dict(mode="project_out_single", layer=3, rel_end=-3,
                              seq_len_at_resolution=9)
    _ls = _toy_layer(_hid)
    with _pc.SinglePositionProjectOut(_ls, 3, _d, alpha=1.0, pos=6, stats=_ss, rel_end=-3,
                                      seq_len_at_resolution=9):
        _ys = _ls(_xa)[0]
    _n_moved_one = int(((_ys - _xa).abs().amax(dim=-1) > 1e-6).sum())
    ck.add("q12_single_vs_all_position_scope",
           "S1 (single site) and S2 (band-wide) are now DISTINCT edits: the all-position hook "
           "moves every position and the single-position hook moves exactly one. Before this, "
           "make_intervention only ever built AllPositionProjectOut, so an S1 arm would silently "
           "have been an all-position edit -- a LARGER intervention under the smaller arm's name",
           _n_moved_all == 9 and _n_moved_one == 1, _n_moved_all,
           "all=%d one=%d" % (_n_moved_all, _n_moved_one))
    ck.add("q12_live_hooks_record_liveness",
           "both hooks now RECORD what C-13 says they recorded nothing of: fired count, "
           "destinations, pre/post norm, projection removed, cosine, layer, resolved index",
           _pc.project_out_liveness_violations(_sa) == []
           and _pc.project_out_liveness_violations(_ss) == []
           and _sa["hook_fired_count"] == 1 and _ss["projection_removed_l2"] > 0
           and _ss["resolved_absolute_index"] == [6], 2,
           "cos=%.6f removed=%.4f" % (_sa["cos_pre_post"], _sa["projection_removed_l2"]))
    # ---- C-117: the PRODUCER writes the two fields the CONSUMER reads, and the consumer's own
    #      gates now pass on REAL producer records rather than voiding them. This is the exact
    #      reproduction the 2026-09-07 review ran and got live=False / ok=False / max_abs=nan on.
    _row_all = dict(_sa, seq_len=9, arm="selftest")
    _row_one = dict(_ss, seq_len=9, arm="selftest")
    _lg = liveness_gate([_row_all, _row_one], "selftest", expect_enabled=True)
    _og = orthogonal_residual_gate([_row_all, _row_one])
    _aud = audit_end_relative([_row_all, _row_one])
    ck.add("c117_producer_records_pass_the_consumer_gates",
           "REAL pair_common records -- the ones the producer itself calls clean -- pass "
           "liveness_gate and orthogonal_residual_gate. Before C-117 both fields were absent, so "
           "the defaulting .get made every healthy arm VOID and made the I-N7 gate assert a "
           "physical violation nobody had measured",
           _lg["live"] and _og["ok"] and _aud["ok"], 2,
           "expected=%d realised=%d orth_max=%.3e n_audited=%d reasons=%s"
           % (_lg["n_cells_expected"], _lg["n_cells_realised"], _og["max_abs"],
              _aud["n_records"], _lg["reasons"]))
    ck.add("c117_expected_is_not_vacuous",
           "the expected cell count is COUNTED from the tensor each forward was handed (9 cells "
           "for the all-position edit on a 1x9 row, 1 for the single site), so "
           "`realised == expected` is a real bind and not 0 == 0",
           _sa["n_cells_edited_expected"] == 9 and _ss["n_cells_edited_expected"] == 1
           and _sa["n_cells_edited_realised"] == 9 and _ss["n_cells_edited_realised"] == 1, 2,
           "all: %d/%d  one: %d/%d" % (_sa["n_cells_edited_realised"],
                                       _sa["n_cells_edited_expected"],
                                       _ss["n_cells_edited_realised"],
                                       _ss["n_cells_edited_expected"]))
    _missing = {k: v for k, v in _row_one.items() if k != "n_cells_edited_expected"}
    _caught = ""
    try:
        liveness_gate([_missing], "selftest", expect_enabled=True)
    except NotMeasured as e:
        _caught = str(e)
    _zero = liveness_gate([dict(_row_one, n_cells_edited_expected=0)], "selftest",
                          expect_enabled=True)
    ck.add("c117_missing_is_not_zero",
           "a record MISSING n_cells_edited_expected RAISES NotMeasured (the arm is UNJUDGED), "
           "while a record whose expected count is a MEASURED ZERO returns live=False (the arm "
           "is judged and it FAILED). Collapsing these two was the whole of C-117",
           bool(_caught) and not _zero["live"], 2,
           "raised=%r | measured-zero reasons=%s" % (_caught[:48], _zero["reasons"][:1]))
    ck.add("f3_end_relative_invariant_holds_and_is_checked",
           "the persisted site satisfies resolved_absolute_index == seq_len + rel_end, and the "
           "producer's own gate now REFUSES a record where it does not",
           _ss["rel_end"] == -3 and _ss["seq_len_at_resolution"] == 9
           and _ss["resolved_absolute_index"] == [6]
           and any("absolute_index_is_not_end_relative" in v for v in
                   _pc.project_out_liveness_violations(dict(_ss, rel_end=-4))), 1,
           "rel_end=%d seq_len=%d abs=%s" % (_ss["rel_end"], _ss["seq_len_at_resolution"],
                                             _ss["resolved_absolute_index"]))

    _lb = _toy_layer(_hid)
    _inner = _pc.SinglePositionProjectOut(_lb, 3, _d, alpha=1.0, pos=6)
    _bst = _pc.hook_stats_dict(mode="bridge", layer=3, enabled=False)
    with _pc.DisabledHookBridge(_inner, stats=_bst):
        _yb = _lb(_xa)[0]
    ck.add("q12_disabled_bridge_is_a_real_code_path",
           "the C5 bridge REGISTERS and RUNS the real hook and discards only its write: the "
           "output is bit-identical to the untouched forward, and what the edit WOULD have been "
           "is recorded",
           float((_yb - _xa).abs().max()) == 0.0
           and _bst["would_have_changed_max_abs"] > 0.0
           and _bst["n_cells_edited_realised"] == 0
           and _pc.project_out_liveness_violations(_bst) == [], 1,
           "would_have_moved=%.5f" % _bst["would_have_changed_max_abs"])
    _as_live = dict(_bst); _as_live["enabled"] = True
    ck.add("q12_bridge_presented_as_live_is_DETECTED",
           "and the SAME record presented as a LIVE arm is REFUSED, not tolerated: a "
           "deliberately disabled hook must never pass as a clean null",
           _pc.project_out_liveness_violations(_as_live) != [], 1,
           str(_pc.project_out_liveness_violations(_as_live))[:60])
    _dead_bridge = _pc.hook_stats_dict(mode="bridge", layer=3, enabled=False)
    _dead_bridge["n_forward_calls"] = 4
    ck.add("q12_bridge_over_a_dead_hook_refused",
           "a bridge whose inner hook would not have changed anything bridges NOTHING and is "
           "refused rather than scoring as a perfect identity",
           "bridge_over_a_dead_hook:would_have_changed_max_abs==0"
           in _pc.project_out_liveness_violations(_dead_bridge), 1)
    _never = _pc.hook_stats_dict(mode="project_out_all", layer=3, enabled=True)
    ck.add("q12_hook_that_never_ran_refused",
           "a hook that never ran at all is refused on n_forward_calls == 0",
           "hook_never_ran:n_forward_calls==0"
           in _pc.project_out_liveness_violations(_never), 1)

    # ---- C-122: CONTROL C4, the ADDITIVE arm, INSTRUMENTED -------------------------------
    # C4 is the equal-magnitude orthogonal control -- the arm that separates "this DIRECTION
    # matters" from "this much PERTURBATION at this site matters". Until 2026-09-07
    # `pc.AllPositionAdd` took no `stats=`, so it was the LAST place in the intervention stack
    # where a dead hook produced exactly the "the control did not move the readout" record a
    # POSITIVE H2a wants to see: a false confirmation in the one arm whose job is scepticism.
    # Driven here against the REAL pair_common classes on a toy layer, exactly as Q12 is.
    _gap = 2.5                       # stands for payload["gap"][v_bomb_specific][L]
    _a4 = _pc.hook_stats_dict(mode="add_all", layer=3)
    _l4 = _toy_layer(_hid)
    with _pc.AllPositionAdd(_l4, 3, _d, alpha=1.0 * _gap, stats=_a4,
                            alpha_gap_units=1.0, gap_norm=_gap):
        _y4 = _l4(_xa)[0]
    _n_moved_add = int(((_y4 - _xa).abs().amax(dim=-1) > 1e-6).sum())
    ck.add("c120_add_hook_records_liveness",
           "the additive hook now records the same liveness quantities the project-out hook "
           "does -- fired count, expected vs realised cells, magnitude, cosine and the "
           "ORTHOGONAL RESIDUAL -- so a dead C4 can no longer score as a clean null",
           _pc.project_out_liveness_violations(_a4) == []
           and _a4["hook_fired_count"] == 1 and _n_moved_add == 9
           and _a4["n_cells_edited_realised"] == _a4["n_cells_edited_expected"] == 9
           and _a4["orthogonal_residual_delta_l2"] is not None, 3,
           "moved=%d cells=%d/%d orth=%.3e" % (_n_moved_add, _a4["n_cells_edited_realised"],
                                               _a4["n_cells_edited_expected"],
                                               _a4["orthogonal_residual_delta_l2"]))
    ck.add("c120_add_dose_is_in_GAP_UNITS",
           "alpha=1 at this call site means ONE difference-of-means: the hook is handed "
           "alpha*gap, records both numbers, and the magnitude it actually WROTE per cell "
           "equals that product",
           _a4["dose_units"] == "gap" and abs(_a4["alpha"] - _gap) < 1e-9
           and _a4["alpha_gap_units"] == 1.0 and _a4["gap_norm"] == _gap
           and abs(_a4["realised_dose_l2_per_cell"] - _gap) < 1e-3, 4,
           "alpha=%.4f realised/cell=%.4f" % (_a4["alpha"],
                                              _a4["realised_dose_l2_per_cell"]))
    _caught = ""
    try:
        _pc.AllPositionAdd(_toy_layer(_hid), 3, _d, alpha=1.0,
                           stats=_pc.hook_stats_dict(mode="add_all", layer=3),
                           alpha_gap_units=1.0, gap_norm=_gap)
    except ValueError as _e:
        _caught = str(_e)
    ck.add("c120_bare_alpha_absolute_dose_REFUSED",
           "a BARE alpha at this call site -- an ABSOLUTE residual magnitude under a gap-unit "
           "label -- is refused at CONSTRUCTION. That is RETRACTION F-3's arithmetic (a 14.65x "
           "overdose from an identical-looking flag) and this repo has written it at this exact "
           "second call site before",
           "ABSOLUTE magnitude" in _caught, 1, _caught[:70])
    _a4s = _pc.hook_stats_dict(mode="add_single", layer=3, rel_end=-3, seq_len_at_resolution=9)
    _l4s = _toy_layer(_hid)
    with _pc.SinglePositionAdd(_l4s, 3, _d, alpha=1.0 * _gap, pos=6, stats=_a4s, rel_end=-3,
                               seq_len_at_resolution=9, alpha_gap_units=1.0, gap_norm=_gap):
        _y4s = _l4s(_xa)[0]
    _n_moved_add1 = int(((_y4s - _xa).abs().amax(dim=-1) > 1e-6).sum())
    ck.add("c120_add_has_a_real_single_site_form",
           "C4 x S1 is a SINGLE-SITE edit, not an all-position edit under a single-site label: "
           "the additive hook moves exactly one position and its resolved index satisfies "
           "seq_len_at_resolution + rel_end",
           _n_moved_add1 == 1 and _pc.project_out_liveness_violations(_a4s) == []
           and _a4s["resolved_absolute_index"] == [6] and _a4s["rel_end"] == -3, 1,
           "all=%d one=%d abs=%s" % (_n_moved_add, _n_moved_add1,
                                     _a4s["resolved_absolute_index"]))
    _dead4 = _pc.hook_stats_dict(mode="add_all", layer=3, enabled=True)
    ck.add("c120_dead_add_hook_refused",
           "a C4 hook that never ran is REFUSED rather than reported as a control that did not "
           "move the readout",
           "hook_never_ran:n_forward_calls==0"
           in _pc.project_out_liveness_violations(_dead4), 1)

    # ---- Q13: the norm-matched control's BASE DIRECTION ----------------------------------
    ck.add("q13_default_base_unchanged",
           "with no '@' and no control_base=, the base is d_surface -- EXACTLY the historical "
           "behaviour, so no existing caller changes",
           _sb.split_control_base("random") == ("random", "d_surface")
           and _sb.split_control_base("d_surface") == ("d_surface", "d_surface"), 2)
    ck.add("q13_base_travels_with_the_arm",
           "'<arm>@<base>' names the base in the spec, so it travels with the arm instead of "
           "being assumed",
           _sb.split_control_base("random@v_bomb_specific")
           == ("random", "v_bomb_specific"), 1)
    _caught = False
    try:
        _sb.split_control_base("random@a", control_base="b")
    except SystemExit:
        _caught = True
    ck.add("q13_two_answers_refused",
           "two different answers to 'which axis is this a control for' is refused", _caught, 1)
    _caught = False
    try:
        _sb.split_control_base("d_surface@v_bomb_specific")
    except SystemExit:
        _caught = True
    ck.add("q13_at_on_a_non_control_refused",
           "'@base' on a NON-control direction is refused; it would mean nothing", _caught, 1)
    _base = {7: torch.tensor([3.0, 4.0]), 8: torch.tensor([0.0, 5.0])}
    _good = {7: torch.tensor([5.0, 0.0]), 8: torch.tensor([5.0, 0.0])}
    _echo = _sb.assert_control_norm_matched("random", "v_bomb_specific", _base, _good, [7, 8])
    ck.add("q13_norm_match_asserted_at_install",
           "a correctly norm-matched control passes and its per-layer norms are ECHOED into the "
           "arm manifest, so a reader can see WHICH axis was controlled for",
           _echo["n_layers_checked"] == 2
           and _echo["control_base_direction"] == "v_bomb_specific", 2,
           "L7 base=%.4f ctl=%.4f" % (_echo["per_layer"]["L7"]["base_norm"],
                                      _echo["per_layer"]["L7"]["control_norm"]))
    _caught = False
    try:
        _sb.assert_control_norm_matched("random", "d_surface", _base,
                                        {7: torch.tensor([50.0, 0.0])}, [7])
    except SystemExit:
        _caught = True
    ck.add("q13_wrong_base_is_DETECTED",
           "a control norm-matched to a DIFFERENT base direction is refused AT HOOK-INSTALL "
           "TIME. This is the eighth instance in this project of a checker disagreeing with the "
           "thing it checks, and it is the one that looks correct in every log", _caught, 1)
    _caught = False
    try:
        _sb.assert_control_norm_matched("random", "d_surface", _base, _good, [30, 31])
    except SystemExit:
        _caught = True
    ck.add("q13_zero_layer_bind_refused",
           "a norm check that binds ZERO layers asserts nothing and is refused", _caught, 1)

    ck.report()
    ok_all &= (ck.n_fail == 0)
    print("\n[selftest] %d checks, %d FAILED" % (len(ck.rows), ck.n_fail))
    return 0 if ok_all else 1


# ============================================================================================
# 12. MUTATION HARNESS -- Q5. Every refusal must be REACHABLE.
# ============================================================================================
def mutate() -> int:
    """`Q5`: a dead hook, a zero-magnitude edit, an identical-hash control band, a broken
    orthogonal-residual preservation, a self-patch that changes the output, a direction fitted on
    test, and an absolute edit index must EACH produce a refusal. An unreachable refusal is not a
    guard (the phrase is this repository's, and it has been earned)."""
    muts: "OrderedDict[str, Any]" = OrderedDict()

    muts["M1 dead hook (fired=0)"] = lambda: liveness_gate(
        [LivenessStats(arm_id="m", n_cells_edited_expected=1).as_row()], "m")["live"]
    muts["M2 zero-magnitude edit"] = lambda: liveness_gate(
        [dict(LivenessStats(arm_id="m", n_cells_edited_expected=1, hook_fired_count=1,
                            n_cells_edited_realised=1, projection_removed_l2=0.0,
                            cos_pre_post=1.0).as_row())], "m")["live"]
    muts["M3 identical control-band hashes"] = lambda: control_band_gate(["z"] * 5, 5)["ok"]
    muts["M4 broken orthogonal residual"] = lambda: orthogonal_residual_gate(
        [{"orthogonal_residual_delta_l2": 0.5}])["ok"]
    muts["M5 self-patch changes the output"] = lambda: self_patch_gate("aa", "bb")["ok"]
    muts["M6 direction fitted on test"] = lambda: direction_provenance_gate(
        {"fit_domains": ["tr", "te"]}, {"tr": "train", "te": "test"})["ok"]
    muts["M7 absolute edit index reused"] = lambda: audit_end_relative(
        [{"seq_len": 100, "rel_end": -10, "resolved_absolute_index": 90},
         {"seq_len": 137, "rel_end": -10, "resolved_absolute_index": 90}])["ok"]
    muts["M8 disabled bridge does not reproduce"] = lambda: disabled_bridge_gate(
        "aa", "bb", 0.0)["ok"]
    muts["M9 bridge presented as a live arm"] = lambda: liveness_gate(
        [LivenessStats(arm_id="m", enabled=False, n_forward_calls=3,
                       n_cells_edited_expected=1).as_row()], "m", expect_enabled=True)["live"]
    muts["M10 missing row outside an exclusion"] = lambda: missing_row_gate(
        ["a", "b"], ["a"], {"b": "art_gallery"}, ["restaurant_kitchen"])["ok"]
    muts["M11 O2 schema absent -> not computable"] = lambda: o2_from_rows(
        [{"semantic_logodds": -1.5}], "knife", "bomb")["computable"]
    muts["M12 three of four conditions"] = lambda: evaluate_success(
        {"p": 0.001, "delta": 0.8}, {"p": 0.5, "delta": 0.0},
        {"distinct_hashes_ok": True, "equivalence": {}, "moved": False},
        {"majority_moved_intended": True, "sign_p": 0.01}, alpha=0.05)["success"]

    # Refusals raised as exceptions rather than returned as a flag.
    raisers: "OrderedDict[str, Any]" = OrderedDict()
    raisers["M13 propagation read at the edited layer"] = \
        lambda: assert_read_sees_edit(9, [9], "propagation")
    raisers["M14 row-level (non-negative) index"] = lambda: resolve_end_relative([1, 2, 3], 2)
    raisers["M15 bare alpha with no gap"] = lambda: gap_unit_alpha(1.0, None)
    raisers["M16 zero-norm direction"] = lambda: _unit(__import__("torch").zeros(4))
    raisers["M17 empty patched span"] = lambda: donor_span_contract([1], [1], [])
    raisers["M18 whole-span exemption"] = lambda: donor_span_contract(
        [1, 2], [1, 3], [-2, -1], [-2, -1])
    raisers["M19 forbidden wording"] = lambda: assert_sayable("the representation is meaningless")
    raisers["M20 permutation over zero domains"] = lambda: domain_group_permutation({}, {}, 10, 1)
    raisers["M21 Holm over an empty family"] = lambda: holm({}, 0.05)

    # ---- Q9-Q13, cleared 2026-09-07. Every new guard must ALSO be shown RED. ----------
    import pair_common as _pc
    import score_behavior as _sb
    import torch as _t

    def _dead_stats():
        st = _pc.hook_stats_dict(mode="project_out_all", layer=3, enabled=True)
        st["n_forward_calls"] = 5          # it ran...
        return st                           # ...and edited nothing

    def _bridge_as_live():
        st = _pc.hook_stats_dict(mode="bridge", layer=3, enabled=False)
        st.update({"n_forward_calls": 5, "would_have_changed_max_abs": 0.9})
        st["enabled"] = True                # presented as a LIVE arm
        return st

    def _under_dosed():
        st = _pc.hook_stats_dict(mode="project_out_all", layer=3, enabled=True)
        st.update({"n_forward_calls": 1, "hook_fired_count": 1,
                   "n_cells_edited_realised": 9, "activation_norm_pre": 100.0,
                   "activation_norm_post": 100.0, "projection_removed_l2": 1e-9,
                   "max_abs_delta": 1e-12, "cos_pre_post": 1.0})
        return st

    muts["M22 pair_common: hook that never ran"] = lambda: not _pc.\
        project_out_liveness_violations(
            _pc.hook_stats_dict(mode="project_out_all", layer=3, enabled=True))
    muts["M23 pair_common: hook ran and edited nothing"] = lambda: not _pc.\
        project_out_liveness_violations(_dead_stats())
    muts["M24 disabled bridge presented as a live arm"] = lambda: not _pc.\
        project_out_liveness_violations(_bridge_as_live())
    muts["M25 bridge over a hook that would not have edited"] = lambda: not _pc.\
        project_out_liveness_violations(
            dict(_pc.hook_stats_dict(mode="bridge", layer=3, enabled=False),
                 n_forward_calls=4))
    muts["M26 edit below float32 resolution"] = lambda: not _pc.\
        project_out_liveness_violations(_under_dosed())
    muts["M27 liveness record missing keys"] = lambda: not _pc.\
        project_out_liveness_violations({"enabled": True, "hook_fired_count": 1})

    raisers["M28 control matched to the WRONG base direction"] = lambda: \
        _sb.assert_control_norm_matched(
            "random", "d_surface", {7: _t.tensor([3.0, 4.0])},
            {7: _t.tensor([50.0, 0.0])}, [7])
    raisers["M29 control norm check binding zero layers"] = lambda: \
        _sb.assert_control_norm_matched(
            "random", "d_surface", {7: _t.tensor([3.0, 4.0])},
            {7: _t.tensor([5.0, 0.0])}, [30])
    raisers["M30 zero-norm base direction"] = lambda: _sb.assert_control_norm_matched(
        "random", "d_surface", {7: _t.zeros(2)}, {7: _t.zeros(2)}, [7])
    raisers["M31 two answers for the control base"] = lambda: _sb.split_control_base(
        "random@a", control_base="b")
    raisers["M32 '@base' on a non-control direction"] = lambda: _sb.split_control_base(
        "d_surface@v_bomb_specific")
    raisers["M33 10.2 primary over ZERO rows"] = lambda: o2_projection_out_from_rows([])
    raisers["M34 10.2 primary with no semantic_logodds"] = lambda: \
        o2_projection_out_from_rows([{"option_mass": 0.1}])
    raisers["M35 frozen probe with all-zero coefficients"] = lambda: FrozenProbe(
        {"selected_layer": 9, "classes": ["a", "b"], "feature_dim": 2, "sha256": "x",
         "estimator": {"coef": [[0.0, 0.0]], "intercept": [0.0]},
         "scaler": {"mean": [0.0, 0.0], "scale": [1.0, 1.0]}})
    raisers["M36 probe read at an ABSOLUTE index"] = lambda: ProbeReadCapture(
        _toy_layer(4), 9, FrozenProbe(
            {"selected_layer": 9, "classes": ["a", "b"], "feature_dim": 4, "sha256": "x",
             "sklearn_classes_": [0, 1],
             "estimator": {"coef": [[1.0, 0.0, 0.0, 0.0]], "intercept": [0.0]},
             "scaler": {"mean": [0.0] * 4, "scale": [1.0] * 4}}),
        7, "a", "b", [])
    raisers["M37 O1 over zero probe records"] = lambda: o1_from_probe_rows([], 15)
    raisers["M38 probe records from two DIFFERENT probes"] = lambda: o1_from_probe_rows(
        [{"read_layer": 15, "o1_margin_source_minus_target": 0.1, "probe_sha256": "a"},
         {"read_layer": 15, "o1_margin_source_minus_target": 0.2, "probe_sha256": "b"}], 15)

    # ---- C-117 / F2 / F3, fixed 2026-09-07. The three new fixes, each shown RED. ----------
    # THE POINT OF THE FIRST PAIR: a MISSING field and a MEASURED ZERO must produce DIFFERENT
    # outcomes. M39 (missing) must RAISE -- the arm is unjudged. M40 (measured zero) must return
    # live=False -- the arm is judged and it failed. If either collapsed into the other, the fix
    # would be undone: defaulting missing->0 is the C-117 bug, and excusing a measured 0 would be
    # the leniency that lets a dead hook pass as a clean null.
    def _live_row(**kw):
        r = _pc.hook_stats_dict(mode="project_out_single", layer=9, rel_end=-10,
                                seq_len_at_resolution=100)
        r.update({"n_forward_calls": 1, "n_forward_with_destinations": 1, "hook_fired_count": 1,
                  "n_destination_rows": 1, "n_cells_edited_realised": 1,
                  "n_cells_edited_expected": 1, "activation_norm_pre": 10.0,
                  "activation_norm_post": 9.8, "projection_removed_l2": 1.4,
                  "min_projection_removed_l2": 1.4, "orthogonal_residual_delta_l2": 2e-7,
                  "max_abs_delta": 0.3, "cos_pre_post": 0.99, "seq_len": 100,
                  "resolved_absolute_index": [90]})
        r.update(kw)
        return r

    muts["M40 expected cell count MEASURED and genuinely 0"] = lambda: liveness_gate(
        [_live_row(n_cells_edited_expected=0)], "m", expect_enabled=True)["live"]
    muts["M41 realised != expected cell count"] = lambda: liveness_gate(
        [_live_row(n_cells_edited_expected=8)], "m", expect_enabled=True)["live"]
    muts["M42 pair_common: absolute index recorded as rel_end"] = lambda: not _pc.        project_out_liveness_violations(_live_row(rel_end=90, seq_len_at_resolution=100))
    muts["M43 pair_common: partially dead hook (fired 1 of 4 forwards)"] = lambda: not _pc.        project_out_liveness_violations(_live_row(n_forward_calls=4,
                                                  n_forward_with_destinations=4,
                                                  hook_fired_count=1))
    muts["M44 pair_common: some forward removed exactly zero"] = lambda: not _pc.        project_out_liveness_violations(_live_row(min_projection_removed_l2=0.0))
    muts["M45 pair_common: orthogonal residual never measured"] = lambda: not _pc.        project_out_liveness_violations(_live_row(orthogonal_residual_delta_l2=None))

    raisers["M39 liveness record MISSING n_cells_edited_expected"] = lambda: liveness_gate(
        [{k: v for k, v in _live_row().items() if k != "n_cells_edited_expected"}], "m",
        expect_enabled=True)
    raisers["M46 orthogonal residual MISSING (not zero)"] = lambda: orthogonal_residual_gate(
        [{k: v for k, v in _live_row().items() if k != "orthogonal_residual_delta_l2"}])
    raisers["M47 orthogonal residual recorded as NaN"] = lambda: orthogonal_residual_gate(
        [_live_row(orthogonal_residual_delta_l2=float("nan"))])
    raisers["M48 end-relative audit on a record with no seq_len"] = lambda: audit_end_relative(
        [{"rel_end": -10, "resolved_absolute_index": 90}])
    raisers["M49 single-site hook whose rel_end names another token"] = lambda:         _pc.SinglePositionProjectOut(_toy_layer(4), 3, _t.ones(4), pos=90, rel_end=-10,
                                     seq_len_at_resolution=137)
    raisers["M50 single-site hook given a NON-NEGATIVE rel_end"] = lambda:         _pc.SinglePositionProjectOut(_toy_layer(4), 3, _t.ones(4), pos=90, rel_end=90,
                                     seq_len_at_resolution=100)
    raisers["M51 score_behavior: edit index that is not seq_len+rel_end"] = lambda:         _sb.make_intervention(None, _pc, None, {"direction": "v", "mode": "project_out",
                                                "layers": [9], "alpha": 1.0},
                              {"v": {9: _t.ones(4)}}, edit_positions=[90],
                              edit_positions_rel_end=[-10], edit_positions_seq_len=137)
    raisers["M52 score_behavior: absolute index passed as rel_end"] = lambda:         _sb.make_intervention(None, _pc, None, {"direction": "v", "mode": "project_out",
                                                "layers": [9], "alpha": 1.0},
                              {"v": {9: _t.ones(4)}}, edit_positions=[90],
                              edit_positions_rel_end=[90], edit_positions_seq_len=100)

    # ---- C-122, control C4's ADDITIVE hook, fixed 2026-09-07 -----------------------------
    # The three defects the C4 instrumentation must be able to convict, each shown RED. M53 is
    # the one that matters most: a C4 hook that never fired must REFUSE, because the record it
    # would otherwise produce -- no cells edited, no state change -- is EXACTLY the record a
    # working control that legitimately did not move the readout produces, and C4 is the arm
    # whose whole job is to be sceptical of a positive H2a.
    def _add_row(**kw):
        r = _pc.hook_stats_dict(mode="add_all", layer=9)
        r.update({"n_forward_calls": 1, "n_forward_with_destinations": 1, "hook_fired_count": 1,
                  "n_destination_rows": 1, "n_cells_edited_realised": 1,
                  "n_cells_edited_expected": 1, "activation_norm_pre": 10.0,
                  "activation_norm_post": 10.3, "projection_removed_l2": 2.5,
                  "min_projection_removed_l2": 2.5, "orthogonal_residual_delta_l2": 2e-7,
                  "max_abs_delta": 0.3, "cos_pre_post": 0.99, "seq_len": 100,
                  "alpha": 2.5, "alpha_gap_units": 1.0, "gap_norm": 2.5, "dose_units": "gap",
                  "realised_dose_l2_per_cell": 2.5})
        r.update(kw)
        return r

    muts["M53 C4: an add hook that never fired (dead C4)"] = lambda: not _pc.        project_out_liveness_violations(_add_row(n_forward_calls=0, hook_fired_count=0,
                                                n_cells_edited_realised=0,
                                                n_cells_edited_expected=0,
                                                projection_removed_l2=0.0, max_abs_delta=0.0,
                                                realised_dose_l2_per_cell=0.0))
    muts["M54 C4: add dosed in ABSOLUTE not gap units"] = lambda: not _pc.        project_out_liveness_violations(_add_row(alpha=1.0, realised_dose_l2_per_cell=1.0))
    muts["M55 C4: add whose dose units were never declared"] = lambda: not _pc.        project_out_liveness_violations(_add_row(dose_units=None))
    muts["M56 C4: realised per-cell magnitude != declared alpha"] = lambda: not _pc.        project_out_liveness_violations(_add_row(realised_dose_l2_per_cell=1.0))
    muts["M57 C4: realised per-cell magnitude NEVER MEASURED"] = lambda: not _pc.        project_out_liveness_violations(_add_row(realised_dose_l2_per_cell=None))
    raisers["M58 C4: AllPositionAdd handed a BARE (absolute) alpha"] = lambda:         _pc.AllPositionAdd(_toy_layer(4), 3, _t.ones(4), alpha=1.0,
                          stats=_pc.hook_stats_dict(mode="add_all", layer=3),
                          alpha_gap_units=1.0, gap_norm=2.5)
    raisers["M59 C4: SinglePositionAdd whose rel_end names another token"] = lambda:         _pc.SinglePositionAdd(_toy_layer(4), 3, _t.ones(4), pos=90, rel_end=-10,
                              seq_len_at_resolution=137)
    raisers["M60 C4: SinglePositionAdd given a NON-NEGATIVE rel_end"] = lambda:         _pc.SinglePositionAdd(_toy_layer(4), 3, _t.ones(4), pos=90, rel_end=90,
                              seq_len_at_resolution=100)
    raisers["M61 C4: half a dose declaration (gap_norm with no alpha_gap_units)"] = lambda:         _pc.AllPositionAdd(_toy_layer(4), 3, _t.ones(4), alpha=2.5,
                          stats=_pc.hook_stats_dict(mode="add_all", layer=3),
                          gap_norm=2.5)

    # ---- C-118(a), the O1 read site. The mutations that matter are the ones about WHICH
    # TOKEN was read, because a misattributed O1 is worse than no O1 at all. ---------------
    _mp = FrozenProbe(
        {"selected_layer": 9, "classes": ["knife", "bomb"], "feature_dim": 4,
         "sklearn_classes_": [0, 1],
         "estimator": {"coef": [[1.0, 0.0, 0.0, 0.0]], "intercept": [0.0]},
         "scaler": {"mean": [0.0] * 4, "scale": [1.0] * 4},
         "self_verification": {"reproduced_from_exported_numbers": True, "n_disagreements": 0},
         "sha256": "deadbeef"}, source="mutate")
    raisers["M62 O1 read pinned to an index with no seq_len_at_resolution"] = lambda:         ProbeReadCapture(_toy_layer(4), 9, _mp, -10, "knife", "bomb", [], abs_index=90)
    raisers["M63 O1 read pin that is not seq_len + rel_end"] = lambda:         ProbeReadCapture(_toy_layer(4), 9, _mp, -10, "knife", "bomb", [], abs_index=90,
                         seq_len_at_resolution=137)

    def _o1_site_moves():
        # A layer whose output at a position DEPENDS ON THE SEQUENCE LENGTH -- i.e. exactly the
        # world in which "every forward of a row agrees at a prompt position" is FALSE (a
        # left-padding change, or a template that inserts rather than appends). The hook must
        # REFUSE rather than emit a mean over two different states.
        import torch as _tt

        class _LenDependent(_tt.nn.Module):
            def forward(self, x):
                return (x * float(x.shape[1]),)
        lay = _LenDependent()
        cap = ProbeReadCapture(lay, 9, _mp, -3, "knife", "bomb", [],
                               row_meta={"prompt_id": "p"}, abs_index=8,
                               seq_len_at_resolution=11)
        with cap:
            lay(_t.randn(1, 11, 4))
            lay(_t.randn(1, 15, 4))
    raisers["M64 O1 read site MOVED between a row's forwards"] = _o1_site_moves

    print("=== PR-057 mutation harness (Q5): every refusal must be REACHABLE ===")
    n_red = 0
    # `score_behavior`'s house refusal idiom is SystemExit, not an exception class of ours, so a
    # mutation against a guard that lives in that shared file raises SystemExit. Catching it here
    # is what lets those guards be shown RED alongside the analyzer's own.
    # `pair_common`'s own construction-time guards raise ValueError (its house idiom -- see
    # `DisabledHookBridge` "bound ZERO hooks"), so a mutation against one of those lands here too.
    _REFUSALS = (Refusal, ZeroBinding, SystemExit, ValueError)
    for name, fn in muts.items():
        try:
            passed = bool(fn())
        except _REFUSALS as e:
            passed = False
            print("  RED    %-42s -> refusal: %s" % (name, str(e)[:70]))
            n_red += 1
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
            print("  RED    %-42s -> refusal: %s" % (name, str(e)[:70]))
    total = len(muts) + len(raisers)
    print("[mutate] %d/%d mutations produced a refusal" % (n_red, total))
    if n_red != total:
        print("  AN UNREACHABLE REFUSAL IS NOT A GUARD.", file=sys.stderr)
        return 1
    return 0


# ============================================================================================
# 13. LAUNCH PLAN
# ============================================================================================
def launch_command(pr: Prereg, arm: ArmSpec, fit_dir: str) -> str:
    """The exact `score_behavior` invocation for one arm.

    `--intervene '<direction>:<mode>:<lo>-<hi>:<alpha>' --fit-dir <PR-053 direction dir>` is the
    EXISTING path (`artifacts.readout_and_intervention`); nothing here reimplements it. The two
    modes it does not yet have -- `patch` (H1, the cross-prompt donor) and `component_replace`
    (H2b) -- are marked, because a command that pretends they exist would be the worst kind of
    plan: one that looks runnable.
    """
    band = "%d-%d" % (min(arm.layers), max(arm.layers))
    cell = pr.require("population", "cell")
    qk = pr.require("population", "query_kind_primary")
    dose = pr.require("population", "n_examples_primary")
    cond = "natural_doublespeak" if cell == "C" else "benign_literal"
    base = ("python3 src/boombness/score_behavior.py"
            " --bank data/boombness_prompts/boombness_prompt_bank_ts116m_%s_%s.jsonl"
            " --query-kinds %s --conditions %s --n-examples %d"
            " --max-new %d --attn-impl %s --arm %s --tag %s"
            % (arm.codeword, arm.target_concept, qk, cond, int(dose),
               int(pr.require("decoding", "max_new_tokens")),
               pr.require("model", "attn_impl"), arm.arm_id, arm.tag()))
    if arm.mode in ("project_out", "add"):
        return base + (" --fit-dir %s --intervene '%s:%s:%s:%g' --seed %d"
                       % (fit_dir, arm.direction, arm.mode, band, arm.alpha,
                          arm.control_draw_seed or int(pr.require("seeds", "control_draws"))))
    if arm.mode == "disabled":
        return base + (" --fit-dir %s --intervene '%s:project_out:%s:%g' "
                       "--pr057-disable-hooks   # C5 bridge: NEW FLAG, does not exist yet"
                       % (fit_dir, arm.direction, band, arm.alpha))
    if arm.mode == "patch":
        return base + (" --pr057-patch-source %s --pr057-patch-layers %s   "
                       "# H1 cross-prompt donor: NEW PATH (Q3), does not exist yet"
                       % (arm.source_concept, band))
    if arm.mode == "component_replace":
        return base + (" --fit-dir %s --intervene '%s:component_replace:%s:%g'   "
                       "# H2b: NEW MODE, does not exist yet"
                       % (fit_dir, arm.direction, band, arm.alpha))
    raise Refusal("unknown arm mode %r" % arm.mode)


def plan(pr: Prereg, fit_dir: str) -> Dict[str, Any]:
    arms = build_arm_manifest(pr)
    members = family_members(pr)
    per_member = defaultdict(int)
    for a in arms:
        if a.family_member:
            per_member[a.family_member] += 1
    missing = [m for m in members if per_member.get(m, 0) == 0]
    if missing:
        raise Refusal("the arm manifest realises no run for declared family member(s) %s. An "
                      "unrun member enters Holm at p=1.0 -- it is never dropped -- but a PLAN "
                      "that forgets to schedule it is a design error, not a p-value." % missing)
    n_test = int(pr.require("primary", "n_test_domains"))
    rows_per_domain = int(pr.require("population", "rows_per_domain_per_concept"))
    rows_per_arm = n_test * rows_per_domain
    return {
        "prereg": PREREG_DEFAULT, "id": pr.require("id"),
        "family": holm_family(pr, PR_ID),
        "n_arms": len(arms),
        "n_live_arms": sum(1 for a in arms if a.role == "live"),
        "n_control_arms": sum(1 for a in arms if a.role == "control"),
        "rows_per_arm_test": rows_per_arm,
        "arms": [{**asdict(a), "tag": a.tag(), "launch": launch_command(pr, a, fit_dir),
                  "propagation_read_layers": propagation_read_layers(
                      a.layers, [int(x) for x in pr.require("read_site", "read_layer_grid")],
                      int(pr.require("model", "n_layers")))}
                 for a in arms],
    }


# ============================================================================================
# 14. MAIN
# ============================================================================================
def analyse(pr: Prereg, runs_root: str, a) -> int:
    """The confirmatory analysis. Refuses long before it can produce a number it should not."""
    wording = check_wording_pin(pr)
    forbidden = forbidden_from_prereg(pr)
    ck = Checks()

    # Q0 -- the outcome variable must exist at all.
    dep = pr.require("_DEPENDENCY_ON_PHASE_7_AND_WHY_IT_IS_BLOCKING")
    print("  Q0 dependency: %s (blocking=%s)" % (dep["depends_on"], dep["blocking"]))
    if not os.path.isdir(runs_root):
        raise Refusal("no run root at %r -- there is nothing to analyse. %s"
                      % (runs_root, dep["statement"]))

    assign = load_split(pr)
    spec = bind_population(pr)
    arms = build_arm_manifest(pr)
    members = family_members(pr)

    found, absent = {}, []
    for arm in arms:
        try:
            d = _find_run(runs_root, arm.tag())
        except PreregError:
            absent.append(arm.arm_id)
            continue
        found[arm.arm_id] = load_arm_run(d)
    ck.add("arms_present", "every declared arm has a COMPLETE run directory",
           not absent, len(arms), "absent=%s" % absent[:6])

    if not found:
        # This is the expected state before the GPU work exists, and it is a REFUSAL rather than
        # an empty report: a report over zero arms is exactly the C-074 shape.
        raise Refusal(
            "NO PR-057 arm has produced a COMPLETE run under %s.\n"
            "  Nothing is analysable yet, and an analysis over zero arms would be a statistic over "
            "a set it bound zero rows from (C-074).\n"
            "  Blocking checklist items outstanding: %s"
            % (runs_root, ", ".join(i["id"] for i in pr.require("pre_extraction_checklist")
                                    if i.get("blocking") and not i.get("done"))))

    # Every arm is gated on liveness BEFORE any outcome is computed, so a number for an arm whose
    # hook did not fire is never produced in the first place.
    live_report = {}
    for arm in arms:
        run = found.get(arm.arm_id)
        if run is None:
            continue
        lg = liveness_gate(run["liveness"], arm.arm_id, expect_enabled=arm.expect_enabled)
        live_report[arm.arm_id] = lg
        ck.add("liveness_%s" % arm.arm_id,
               "hooks demonstrably fired and demonstrably changed the state",
               lg["live"], lg["n_rows"], "; ".join(lg["reasons"])[:160])
        if run["liveness"]:
            aud = audit_end_relative(run["liveness"])
            ck.add("index_%s" % arm.arm_id, "every edit index is len(input_ids)+rel_end (I-N9)",
                   aud["ok"], aud["n_records"], aud["witness_note"])

    ck.report()
    print("\n[pr057] %d arm(s) loaded, %d check failure(s)" % (len(found), ck.n_fail))
    if ck.n_fail:
        print(assert_sayable(
            "REFUSING to emit any causal verdict: %d gate(s) failed above. A null behind an "
            "unverified hook is VOID, not a negative -- the replacement wording for a genuine "
            "negative is %r and it is not available to an arm that has not passed liveness."
            % (ck.n_fail, wording), forbidden), file=sys.stderr)
        return 1
    print("  (outcome computation continues only for arms that passed every gate above)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--prereg", default=PREREG_DEFAULT)
    ap.add_argument("--runs", default="outputs/boombness/score_behavior",
                    help="root under which each arm's run directory lives")
    ap.add_argument("--fit-dir", default="outputs/dcs_ts_pr053_diffmeans/<run>",
                    help="the PR-053 TRAIN-ONLY direction directory (Q2)")
    ap.add_argument("--plan", action="store_true", help="print the arm manifest and stop")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--mutate", action="store_true")
    ap.add_argument("--power-q1", action="store_true",
                    help="measure the between-domain SD of O2 on VALIDATION ONLY and decide")
    ap.add_argument("--for-extraction", action="store_true",
                    help="load the preregistration with the BLOCKING checklist enforced")
    ap.add_argument("--out", default=None, help="optional path for the JSON result")
    a = ap.parse_args()

    if a.self_test:
        return selftest()
    if a.mutate:
        return mutate()

    # The loader REFUSES this file today, on `analyzer_exists == false` and on the blocking
    # checklist. That refusal is the design working. `--check` without `--for-extraction` loads
    # cleanly, which is the state a FROZEN-but-not-yet-runnable preregistration should be in.
    try:
        pr = load(a.prereg, for_extraction=a.for_extraction)
    except PreregError as e:
        print("PREREG REFUSAL:\n%s" % e, file=sys.stderr)
        return 2

    check_wording_pin(pr)

    if a.plan:
        p = plan(pr, a.fit_dir)
        txt = json.dumps(p, indent=2, default=str)
        assert_sayable(txt, forbidden_from_prereg(pr))
        if a.out:
            with open(a.out, "w") as f:
                f.write(txt)
            print("wrote %s" % a.out)
        else:
            print(txt)
        return 0

    if a.power_q1:
        raise SystemExit(
            "Q1 needs the VALIDATION-ONLY arm run to exist. Launch the validation power arms "
            "first (see reports/DCS_TS_PR057_DESIGN.md, 'Q1 first'), then re-run with --runs "
            "pointing at them; `q1_power()` is the code path and it returns CANNOT ANSWER "
            "WITHOUT READING TEST when power < 0.80.")

    try:
        return analyse(pr, os.path.join(REPO, a.runs) if not os.path.isabs(a.runs) else a.runs, a)
    except (Refusal, ZeroBinding) as e:
        print("REFUSAL:\n  %s" % e, file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
