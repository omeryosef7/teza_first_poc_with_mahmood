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
    "Q9 (BLOCKING, discovered while writing this analyzer): the PHASE 7 readout scores ONE "
    "concept per bank ({concept, codeword}), so logP(source concept) does not exist on the target "
    "bank and the preregistered O2 -- semantic_logodds(source vs target concept) -- is NOT "
    "COMPUTABLE from the instrument as it stands. score_behavior._semantic must be extended to a "
    "multi-concept answer set emitting logp_bomb / logp_knife / logp_gun / logp_codeword "
    "(the existing `logp_{group}` rule, next_token_readout:119), and the one-pair-per-bank "
    "assertion at score_behavior.py:1960 relaxed for that answer set ONLY."
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
    bad = []
    for r in records:
        need = ("seq_len", "rel_end", "resolved_absolute_index")
        miss = [k for k in need if k not in r]
        if miss:
            raise Refusal("liveness record is missing %s -- the end-relative audit cannot be "
                          "performed and is therefore not assumed to pass" % miss)
        if int(r["seq_len"]) + int(r["rel_end"]) != int(r["resolved_absolute_index"]):
            bad.append(r)
    spread = len({int(r["resolved_absolute_index"]) for r in records})
    return {"n_records": len(records), "n_absolute_index_violations": len(bad),
            "n_distinct_absolute_indices": spread,
            "ok": (not bad) and len(records) > 0,
            "witness_note": ("the absolute index takes %d distinct values over %d records; a "
                             "SINGLE value across concepts would mean an absolute index was "
                             "reused" % (spread, len(records)))}


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
    orthogonal_residual_delta_l2: float = 0.0
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


class InstrumentedHook:
    """Context manager registering an instrumented hook on one decoder layer.

    `model` may be a real HF model (resolved through `ds_common._get_layers`, the house helper) or,
    in the unit tests, any object exposing `register_forward_hook`. The tests exercise the SAME
    hook function the GPU path uses; a test against a re-implementation would test nothing.
    """

    def __init__(self, model, layer_idx: int, hook_fn, stats: LivenessStats):
        if hasattr(model, "register_forward_hook"):
            self.layer = model
        else:
            import ds_common as dc
            self.layer = dc._get_layers(model)[layer_idx]
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


def liveness_gate(stats_rows: Sequence[Dict[str, Any]], arm_id: str,
                  expect_enabled: bool = True, tol: float = 1e-6) -> Dict[str, Any]:
    """Did this arm's hooks demonstrably FIRE and demonstrably CHANGE THE STATE?

    `primary.void`: `hook_fired_count == 0`; realised != expected cells; an arm's edit magnitude
    is 0. Any of those makes a null VOID rather than a negative, which is the distinction C-13
    says nothing in the current hook stack can make.
    """
    reasons: List[str] = []
    if not stats_rows:
        return {"arm_id": arm_id, "live": False, "n_rows": 0,
                "reasons": ["NO LIVENESS RECORDS AT ALL -- %s is absent or empty. A null behind an "
                            "unrecorded hook is VOID, not a negative." % CONTRACT_LIVENESS]}
    n_fired = sum(int(r.get("hook_fired_count", 0)) for r in stats_rows)
    n_rows_fired = sum(1 for r in stats_rows if int(r.get("hook_fired_count", 0)) > 0)
    realised = sum(int(r.get("n_cells_edited_realised", 0)) for r in stats_rows)
    expected = sum(int(r.get("n_cells_edited_expected", 0)) for r in stats_rows)
    mags = [float(r.get("projection_removed_l2", 0.0)) for r in stats_rows]
    zero_mag = sum(1 for m in mags if not (m > tol))
    cos = [float(r.get("cos_pre_post", 1.0)) for r in stats_rows]
    unchanged = sum(1 for c in cos if abs(c - 1.0) <= tol)
    disabled_flags = {bool(r.get("enabled", True)) for r in stats_rows}

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
            reasons.append("%d/%d records have cos(h_pre,h_post) == 1 to %g: the state did not "
                           "change even though the hook reports firing"
                           % (unchanged, len(stats_rows), tol))
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
            "n_zero_magnitude": zero_mag, "n_unchanged_state": unchanged,
            "expect_enabled": expect_enabled, "reasons": reasons}


def orthogonal_residual_gate(stats_rows: Sequence[Dict[str, Any]],
                             tol: float = 1e-4) -> Dict[str, Any]:
    """`I-N7`, blocking: `||h_orth_pre - h_orth_post||` must be 0 to numerical tolerance."""
    if not stats_rows:
        raise ZeroBinding("orthogonal-residual gate over zero records")
    vals = [float(r.get("orthogonal_residual_delta_l2", float("nan"))) for r in stats_rows]
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
        arms.append(ArmSpec(
            arm_id="c5_disabled_bridge_%s" % scope.lower(), role="control", family_member=None,
            hypothesis="C5", scope=scope, layers=list(layers), mode="disabled",
            direction="v_bomb_specific", source_concept="knife", target_concept="bomb",
            codeword="button", dose_units="none -- the hook is registered and edits nothing",
            alpha=0.0, control_draw_seed=None, expect_enabled=False,
            note="BLOCKING: must reproduce the untouched baseline byte-for-byte and the hidden "
                 "states at max|diff| == 0.000e+00"))
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
    st = LivenessStats(arm_id="unit_live", n_cells_edited_expected=1)
    hook = make_instrumented_project_out_hook(d, st, positions=[resolve_end_relative(range(12), -3)])
    with InstrumentedHook(layer, 9, hook, st):
        y = layer(x)[0]
    live = liveness_gate([st.as_row()], "unit_live", expect_enabled=True)
    changed = float((y - x).norm()) > 0
    ck.add("live_hook", "a live project-out hook fires, edits exactly the expected cells, and "
           "changes the state", live["live"] and changed and st.hook_fired_count == 1, 1,
           "reasons=%s" % live["reasons"])

    # ---- DISABLED hook is DETECTED as disabled -----------------------------------------
    st_d = LivenessStats(arm_id="unit_bridge", n_cells_edited_expected=1, enabled=False)
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
    st_r = LivenessStats(arm_id="unit_h2b", n_cells_edited_expected=1)
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

    print("=== PR-057 mutation harness (Q5): every refusal must be REACHABLE ===")
    n_red = 0
    for name, fn in muts.items():
        try:
            passed = bool(fn())
        except (Refusal, ZeroBinding) as e:
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
        except (Refusal, ZeroBinding) as e:
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
