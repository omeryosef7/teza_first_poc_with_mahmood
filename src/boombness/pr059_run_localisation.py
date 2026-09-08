#!/usr/bin/env python3
"""`DCS-PR-059` PHASE 11 -- the GPU runner / launcher (defect `PR059-D2`, checklist item `U8`).

WHY THIS FILE EXISTS AT ALL
---------------------------
`scripts/dcs_ts_pr059_localisation.py --plan` prints 78 arm commands and **not one of them can be
run**. Every line is addressed to `scripts/dcs_ts_readout_multi.py`, which accepts only
`--banks --family --tag-prefix --query-kinds --conditions --n-examples --max-new --attn-impl
--arm --intervene --fit-dir` and forwards **no** `--only-cell`, **no** `--knockout-scope`, **no**
`--knockout-rel-end-rows` and **no** row-set flag at all. That is `PR059-D2`, recorded in
`reports/DCS_TS_PR059_ANALYZER.md` appendix A.5, and it is why `U8` had no launcher.

PHASE 9 hit exactly this wall (`Q4b`: an analyzer and a manifest existed and nothing could run
them) and `src/boombness/pr057_run_causal.py` is how it was solved. This file is that solution for
PHASE 11: it loads the model ONCE and loops the arm manifest inside one allocation, driving
`src/boombness/score_behavior.py`'s `main()` in-process with `sys.argv` set -- the house readout,
the house flags, the house guards, not a re-implementation of any of them. 78 separate
`score_behavior` invocations would spend more wall time loading Llama-3.1-8B off this filesystem
than computing, and `DONE.json.model_loads` is the number that proves this one does not.

IT IMPORTS THE ARM MANIFEST, THE SCOPES AND THE GATES FROM THE ANALYZER
----------------------------------------------------------------------
`scripts/dcs_ts_pr059_localisation.py` is the single source of truth for what an arm IS:
`build_arm_manifest`, `ArmSpec`, `declared_scopes`, `query_span_rel_end`,
`random_row_control_draw`, `random_row_control_constructible`, `liveness_gate`,
`audit_end_relative`, `assert_realised_equals_declared`, `resolver_failure_gate`, `bind_rows`,
`control_band_gate`, `assert_scope_has_its_control`. **Nothing here re-derives any of them.** A
runner and an analyzer that disagreed about what an arm is would be the whole failure mode of this
phase, so this file additionally CROSS-CHECKS every argv it builds against the analyzer's own
`launch_command()` for the same arm -- bank, cell, channel, dose, attention implementation,
intervention string, knockout scope and the declared `rel_end` row set -- and REFUSES on any
disagreement. The two places the two vocabularies genuinely differ (`--only-cell` vs
`--conditions`, and the nondemo control's arm NAME vs the analyzer's non-existent
`--nondemo-matched-draws` flag) are the ONLY sanctioned translations and each lives in exactly one
table below, next to the reason it exists.

WHAT IS STILL BLOCKED, REPORTED RATHER THAN WORKED AROUND
---------------------------------------------------------
`PR059-D1` (the arithmetically impossible dose-matched control), `PR059-D4` (the analyzer's
liveness schema is the PR-057 project-out schema, which the attention-knockout producer does not
write), `PR059-D5` (the analyzer's manifest is 78 arms and the independent verifier's expected set
is 82) and `PR059-D6` (the `L-N1` disabled-hook bridge cannot be constructed for an attention
knockout at all). Each is a named refusal, none is substituted with a different arm, and every one
of them is visible from `--plan` on CPU before a queue slot is spent.

USAGE
    python3 src/boombness/pr059_run_localisation.py --self-test      # this runner's own logic
    python3 src/boombness/pr059_run_localisation.py --mutate         # each mutation must be RED
    python3 src/boombness/pr059_run_localisation.py --plan           # the manifest, CPU only
    python3 src/boombness/pr059_run_localisation.py --stage smoke --split train --dry-run
    python3 src/boombness/pr059_run_localisation.py --stage smoke --split train
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import inspect
import json
import os
import re
import socket
import sys
import time
from typing import Any, Dict, List, Optional, Sequence, Tuple

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
for _p in ("scripts", os.path.join("src", "boombness"), "doublespeak_causality"):
    _f = os.path.join(REPO, _p)
    if _f not in sys.path:
        sys.path.insert(0, _f)

from dcs_ts_prereg import Prereg, PreregError  # noqa: E402
from dcs_ts_prereg import load as load_prereg  # noqa: E402

# THE ANALYZER IS THE SOURCE OF TRUTH FOR WHAT AN ARM IS. Nothing below re-derives a manifest, a
# scope, a draw or a gate; they are imported.
import dcs_ts_pr059_localisation as AN  # noqa: E402
from dcs_ts_pr059_localisation import (  # noqa: E402
    ArmSpec,
    CannotAnswer,
    CONTRACT_ARM,
    Refusal,
    assert_realised_equals_declared,
    assert_sayable,
    assert_scope_has_its_control,
    audit_end_relative,
    bind_rows,
    build_arm_manifest,
    check_wording_pin,
    control_band_gate,
    declared_scopes,
    family_member_ids,
    forbidden_from_prereg,
    intervention_band,
    launch_command,
    liveness_gate,
    n_nondemo_draws,
    n_random_row_draws,
    primary_banks,
    primary_cell,
    primary_channel,
    query_span_rel_end,
    random_row_control_constructible,
    random_row_control_draw,
    reference_scope_id,
    required_attn_impl,
    resolver_failure_gate,
    scaffold_scope_id,
    whole_population_exclusions,
)
from dcs_ts_pr048_analysis import _find_run, load_split  # noqa: E402
from dcs_ts_pr051_positional import ZeroBinding  # noqa: E402

PREREG_DEFAULT = "configs/dcs_ts_pr059_phase11.json"
#: The PHASE 11 amendment (`DCS-PR-061`). A SEPARATE, also-FROZEN file; the parent is NEVER
#: edited. It supersedes the parent's `pre_extraction_checklist` and the parent's
#: `dose_matching.per_scope_random_row_control` clause on measured arithmetic, and it carries the
#: stage scoping the checklist gate reads. Pass an empty string to gate on the parent alone.
AMENDMENT_DEFAULT = "configs/dcs_ts_pr061_phase11_amendment.json"
SCORE_SCRIPT = "src/boombness/score_behavior.py"
RUNS_ROOT_DEFAULT = "outputs/boombness/score_behavior"
STATE_ROOT_DEFAULT = "outputs/boombness/pr059_runner"
MANIFEST_FILE = "PR059_RUN_MANIFEST.json"
ARM_GATE_FILE = "PR059_ARM_GATE.json"

#: The staged submission order the frozen `kill_condition` fixes: "S_G (query_prefill_only, the
#: whole query span) AND S_0 (baseline) are submitted FIRST and read FIRST. If S_G does not move
#: the readout at the domain level, NO NARROWER SCOPE IS SUBMITTED." `smoke` is `U8`.
STAGE_ORDER = ("smoke", "kill", "family")


class RunnerRefusal(RuntimeError):
    """Anything this runner will not do. Every one of them is fail-closed."""


# ============================================================================================
# DEFECTS. Recorded, never worked around. Each is reachable from --plan on CPU.
# ============================================================================================
DEFECT_D1_IMPOSSIBLE_CONTROL = (
    "PR059-D1: `dose_matching.per_scope_random_row_control` requires, for EVERY scope of size m, "
    "a seeded random m-row draw from the query span EXCLUDING the scope's own rows. The query "
    "span is 28 rows (re-derived in 6900/6900 prompts), so the pool for a scope of size m is "
    "28-m and the control exists only where 28-m >= m, i.e. m <= 14. Pools are 6, 5 and 0 "
    "against doses 22, 23 and 28 for S_D, S_E and S_G. The control is ARITHMETICALLY IMPOSSIBLE "
    "for three scopes, one PAIR of which -- S_D vs S_E -- is the phase's declared PRIMARY "
    "CONTRAST. No GPU time changes this. It is decided in configs/dcs_ts_pr061_phase11_"
    "amendment.json, which DEMOTES S_D/S_E/S_G from the controlled estimate rather than drawing "
    "a smaller set and calling it dose-matched."
)

DEFECT_D2_NO_LAUNCHER = (
    "PR059-D2 (CLOSED BY THIS FILE): every arm command `dcs_ts_pr059_localisation.py --plan` "
    "prints is addressed to scripts/dcs_ts_readout_multi.py, which forwards no --only-cell, no "
    "--knockout-scope and no row-set flag, so the printed line is a design statement rather than "
    "a command. This runner drives src/boombness/score_behavior.py directly, in-process, and "
    "cross-checks every argv it builds against that same launch_command(). A SECOND HALF of D2 "
    "is recorded and NOT closed: launch_command also prints `--nondemo-matched-draws N "
    "--nondemo-draw-seed S`, and NEITHER FLAG EXISTS on score_behavior either. The nondemo "
    "control is selected by the INTERVENTION ARM NAME (`nondemo_matched_d1..3`) and its draw seed "
    "is `--seed`; see NONDEMO_ARM_MAP."
)

DEFECT_D4_LIVENESS_SCHEMA = (
    "PR059-D4 (NEW, found by this runner; the C-117 class recurring for PHASE 11): the analyzer's "
    "liveness_gate() reads `hook_fired_count`, `n_cells_edited_expected`, "
    "`n_cells_edited_realised`, `n_forward`, `n_prefill_edits` and `n_decode_edits` -- the "
    "PR-057 PROJECT-OUT hook's schema (pair_common.hook_stats_dict). The ATTENTION-KNOCKOUT "
    "producer writes a different schema onto each results.jsonl row: hook_n_forward, "
    "hook_n_edits, hook_n_prefill_edits, hook_n_decode_edits, hook_n_query_rows_edited, "
    "hook_n_keys_masked, hook_n_blocked_keys -- and NO hook_fired_count and NO "
    "n_cells_edited_expected anywhere. Three of the six fields have a declared, checkable "
    "producer source (LIVENESS_FIELD_MAP); `hook_fired_count` and `n_cells_edited_expected` have "
    "NONE. This runner REFUSES to invent them -- PR-057 recorded exactly this and its runner "
    "'no longer invents expected := n_destination_rows' -- so it gates each arm with the "
    "PRODUCER's own gate plus the realised-vs-declared audit, records the analyzer's verdict "
    "beside it as NOT-EVALUABLE, and writes both into PR059_ARM_GATE.json. Reconciling the two "
    "schemas needs src/boombness/score_behavior.py or doublespeak_causality/pair_common.py, both "
    "of which are held by other work; it is REPORTED, not fixed."
)

DEFECT_D5_ARM_COUNT = (
    "PR059-D5 (NEW, found by this runner): the analyzer's build_arm_manifest() yields 78 arms "
    "over the two confirmatory banks and the INDEPENDENT verifier's expected_arms() declares 82. "
    "The difference is exactly (a) the verifier expects 3 nondemo-key control draws for the "
    "reference scope S_G and the analyzer's manifest gives S_G no controls at all ('the "
    "denominator gets no dose-matched control'), +6; and (b) the analyzer adds one disabled-hook "
    "BRIDGE arm per bank which the verifier does not know about, -2. Under the verifier's R5 a "
    "complete 78-arm run would fail BOTH ways at once: six arms 'complete on disk and absent from "
    "the output' and two 'arms nobody preregistered'. One of the two derivations is wrong and the "
    "disagreement is the finding. Neither file is edited here."
)

DEFECT_D6_BRIDGE_NOT_CONSTRUCTIBLE = (
    "PR059-D6 (NEW, found by this runner): null L-N1 -- the disabled-hook bridge -- is BLOCKING "
    "in the frozen file and is NOT CONSTRUCTIBLE for an attention knockout. "
    "pair_common.DisabledHookBridge bridges an inner context that exposes (_hook, layer) or "
    "(_hooks, layers); ScopedAttentionKnockout exposes `layers` and `_handles` and NO hook "
    "attribute, so DisabledHookBridge raises TypeError('cannot bridge ScopedAttentionKnockout: "
    "it exposes neither (_hook, layer) nor (_hooks, layers)'). Observed on CPU against the real "
    "class. The bridge arm is therefore REFUSED by name rather than launched to die at the node "
    "after a queue wait and a model load. Fixing it needs doublespeak_causality/pair_common.py, "
    "which is held by other work."
)

DEFECT_D7_NO_VERDICT_PATH = (
    "PR059-D7 (NEW, found by this runner; the same shape PR-060 recorded for PHASE 9): "
    "dcs_ts_pr059_localisation.analyse() ends at the liveness / realised-row gates and returns 0 "
    "after printing '(baseline readout, then the kill conditions, ... then the verdict -- in that "
    "order)'. There is no outcome path, no Holm call, no delta and no verdict in analyse(); "
    "evaluate_success(), holm_with_absent() and verdict() are exercised only under --self-test "
    "and --mutate. artifacts.analyzer_exists therefore stays FALSE, which keeps "
    "`dcs_ts_prereg.py --for-extraction` fail-closed, which is the correct state today."
)

ALL_DEFECTS = [DEFECT_D1_IMPOSSIBLE_CONTROL, DEFECT_D2_NO_LAUNCHER, DEFECT_D4_LIVENESS_SCHEMA,
               DEFECT_D5_ARM_COUNT, DEFECT_D6_BRIDGE_NOT_CONSTRUCTIBLE, DEFECT_D7_NO_VERDICT_PATH]


# ============================================================================================
# 1. THE TWO SANCTIONED TRANSLATIONS BETWEEN THE ANALYZER'S VOCABULARY AND score_behavior's
# ============================================================================================
#
# The analyzer's `launch_command` and `score_behavior`'s argparse do not spell the same experiment
# the same way. There are exactly TWO places they differ, and each is a table rather than an
# inline literal, for the same reason PR-057's DIRECTION_MAP is one: a vocabulary difference
# resolved by resemblance at launch time is how an arm silently becomes a different arm.

#: (1) THE CELL. The analyzer binds the population on the field `cell` and REFUSES any other
#: selector (`bind_rows`: "population binding may only select on 'cell'"). `score_behavior` has no
#: `--cells` flag at all -- it filters on `condition`. So the launcher MUST pass `--conditions`,
#: and that is only legitimate where the mapping is 1:1 ON THIS BANK. It is not assumed:
#: `cell_condition_for_bank()` binds BOTH ways and refuses on any symmetric difference (A-039).
#: Nothing is hardcoded here; the string is read off the bank.
CELL_CONDITION_IS_DERIVED_NOT_DECLARED = True

#: (2) THE NONDEMO-KEY CONTROL. `launch_command` prints
#:     --nondemo-matched-draws 3 --nondemo-draw-seed 20260909
#: and NEITHER FLAG EXISTS (the second half of PR059-D2). In `score_behavior` the nondemo control
#: is the INTERVENTION ARM NAME -- `--intervene nondemo_matched_d2:attn_knockout:<band>:1.0`,
#: `score_behavior.NONDEMO_DRAW_ARMS` -- and its per-draw seed is derived from `--seed` by
#: `nondemo_draw_seed(control_seed, idx)`. The analyzer's draw index is 0-based and the producer's
#: arm suffix is 1-based, which is exactly the kind of off-by-one that is invisible in a mean, so
#: it is written down here once and asserted in the self-test.
NONDEMO_ARM_PREFIX = "nondemo_matched_d"


def nondemo_arm_name(draw_index: int) -> str:
    """The producer's arm name for the analyzer's 0-based nondemo draw index."""
    if int(draw_index) < 0:
        raise RunnerRefusal("a nondemo control arm was asked for draw index %r" % draw_index)
    return "%s%d" % (NONDEMO_ARM_PREFIX, int(draw_index) + 1)


#: PR059-D4. Which analyzer-liveness field has a DECLARED producer source on an attention-knockout
#: row, and which has NONE. A field mapped to `None` is never invented: it is reported absent.
LIVENESS_FIELD_MAP: Dict[str, Optional[str]] = {
    "n_forward": "hook_n_forward",
    "n_prefill_edits": "hook_n_prefill_edits",
    "n_decode_edits": "hook_n_decode_edits",
    "keys_masked": "hook_n_keys_masked",
    "surface_span_n_tokens": "surface_span_n_tokens",
    "surface_span_positions": "surface_span_positions",
    "surface_span_decoded": "surface_span_decoded",
    "seq_len": "seq_len",
    # PR059-D4, RESOLVED BY THE PRODUCER. These three had NO producer source: the
    # attention-knockout hook counted edits, rows and masked keys but never a fired-count and
    # never an EXPECTED cell count, so "realised == expected cells" -- a clause of `primary.void`
    # -- could not be evaluated for a knockout arm at all.
    #
    # OWNERSHIP WENT TO THE PRODUCER, which is where PR-057's C-117 says it belongs:
    # `ScopedAttentionKnockout._pre` counts EXPECTED from the rows it resolved BEFORE the mask
    # write, and READS REALISED BACK out of the mask afterwards, so the two are measured on
    # opposite sides of the write and `realised == expected` is a real bind rather than `0 == 0`
    # on a dead hook. `score_behavior` copies them onto the row WITHOUT a default, only on the
    # declared-offset path.
    #
    # THE MAP STILL DOES NOT DEFAULT. A field absent from a row stays ABSENT in the record, and
    # the analyzer's gate RAISES on it. This runner still invents nothing.
    "hook_fired_count": "hook_fired_count",
    "n_cells_edited_expected": "n_cells_edited_expected",
    "n_cells_edited_realised": "n_cells_edited_realised",
}


def bridge_family_constructible() -> Tuple[bool, str]:
    """PR059-D6. Can `DisabledHookBridge` bridge the hook family THIS PHASE installs?

    Re-derived from `pair_common`'s own dispatch, never asserted in prose. `ScopedAttentionKnockout`
    edits the additive attention mask in a forward PRE hook and exposes `_pre` / `layers` /
    `_handles`; the bridge's original two branches wanted `(_hook, layer)` or `(_hooks, layers)`
    and refused it with a TypeError, which made BLOCKING null L-N1 unbuildable and the `kill`
    stage impossible to complete as designed.
    """
    try:
        import pair_common as pc
    except Exception as e:                                   # noqa: BLE001
        return False, "pair_common is not importable: %r" % (e,)
    fams = tuple(getattr(pc.DisabledHookBridge, "BRIDGE_FAMILIES", ()))
    if "attn_pre_kwargs" not in fams:
        return False, ("DisabledHookBridge declares bridge families %s, none of which is the "
                       "attention-mask pre-hook family that ScopedAttentionKnockout installs; "
                       "null L-N1 is NOT CONSTRUCTIBLE" % (fams,))
    if not hasattr(pc, "bridge_mask_liveness_violations"):
        return False, ("the attention-mask bridge has no liveness contract of its own, so a "
                       "bridge over a DEAD knockout would score as a perfect identity")
    # PR059-D6, SECOND HALF -- and the more dangerous one. The bridge CLASS being able to wrap a
    # knockout is not enough: `score_behavior.make_intervention` returns the knockout hooks from
    # an EARLY return, above its own disabled-hook-bridge block, so `--pr057-disable-hooks` on a
    # knockout arm used to install a FULLY LIVE knockout and record it as the C5 bridge. A live
    # arm wearing the null's name is worse than a TypeError, because it produces a number.
    try:
        import inspect as _i
        import score_behavior as _sb
        src = _i.getsource(_sb.make_intervention)
    except Exception as e:                                   # noqa: BLE001
        return False, "score_behavior.make_intervention is not readable: %r" % (e,)
    knock = src.split("attn_knockout", 1)[-1] if "attn_knockout" in src else ""
    if "_bridge_if_disabled" not in knock:
        return False, ("score_behavior.make_intervention returns the attention-knockout hooks "
                       "WITHOUT routing them through the disabled-hook bridge, so "
                       "--pr057-disable-hooks would install a LIVE knockout and label it the "
                       "L-N1 bridge")
    return True, "attn_pre_kwargs (pair_common.DisabledHookBridge) + score_behavior routing"


def analyzer_liveness_contract_report() -> Dict[str, Any]:
    """`PR059-D4` as a report rather than a sentence: which fields the analyzer's `liveness_gate`
    needs, and which of them the knockout producer has no source for."""
    missing = sorted(k for k, v in LIVENESS_FIELD_MAP.items() if v is None)
    return {"ok": not missing, "n_fields": len(LIVENESS_FIELD_MAP),
            "mapped": {k: v for k, v in LIVENESS_FIELD_MAP.items() if v},
            "unmapped": missing, "defect": DEFECT_D4_LIVENESS_SCHEMA if missing else ""}


# ============================================================================================
# 2. SMALL HELPERS -- every number comes out of the frozen file, none is typed here
# ============================================================================================
def repo_path(*parts: str) -> str:
    return os.path.join(REPO, *parts)


def file_sha16(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def bank_path_for(pr: Prereg, bank_key: str) -> str:
    return str(pr.require("population", "banks", bank_key, "path"))


def load_bank_rows(path: str) -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    with open(path) as fh:
        for line in fh:
            line = line.strip()
            if line:
                r = json.loads(line)
                out[r["prompt_id"]] = r
    return out


def rel_end_arg(rows: Sequence[int]) -> str:
    """The `--knockout-rel-end-rows=` VALUE for a declared offset set.

    A comma list of negative integers. It is always passed with `=`: argparse reads a bare
    `-28,-27,...` after a space as an OPTION, not a value, and dies with `expected one argument`
    (recorded in the flag's own --help and in DCS_TS_PR059_ANALYZER.md A.2).
    """
    r = sorted(int(x) for x in rows)
    if not r:
        raise RunnerRefusal("an empty rel_end row set was asked for; an empty scope cuts nothing "
                            "and its arm scores as a clean null (this is S_B's shape)")
    bad = [x for x in r if x >= 0]
    if bad:
        raise RunnerRefusal(
            "ABSOLUTE INDEX REFUSED: offsets %s are not negative. The absolute index of the same "
            "site agrees across concepts in 0/2300 triples and the end-relative one in 2300/2300."
            % bad)
    return ",".join(str(x) for x in r)


def rel_end_span_arg(rows: Sequence[int]) -> str:
    """The declared query span, as the `a..b` form the producer's help names."""
    r = sorted(int(x) for x in rows)
    if r != list(range(r[0], r[-1] + 1)):
        return rel_end_arg(r)
    return "%d..%d" % (r[0], r[-1])


# ============================================================================================
# 3. POPULATION BINDING -- and `--split` is LOAD-BEARING, not decorative
# ============================================================================================
def cell_condition_for_bank(pr: Prereg, bank_abs: str) -> Dict[str, Any]:
    """`A-039`. The `condition` value that binds EXACTLY the rows `cell == C` binds, or a refusal.

    The frozen file's own note: "Select on the field `cell` == 'C'. NOT `condition` ==
    'natural_doublespeak': that string lives in `condition`, and selecting the wrong field binds
    ZERO rows." The analyzer honours that by refusing any selector but `cell`. `score_behavior`
    has no cell flag, so the launcher has to select on `condition` -- which is legitimate ONLY
    where the mapping is 1:1 on this bank, and that is verified here rather than assumed. On a
    bank where it is not 1:1 this refuses instead of binding the wrong cell.
    """
    rows = load_bank_rows(bank_abs)
    cell = primary_cell(pr)
    qk = primary_channel(pr)
    dose = int(pr.require("population", "n_examples_primary"))
    by_cell = [r for r in rows.values()
               if str(r.get("cell")) == cell and str(r.get("query_kind")) == qk
               and int(r.get("n_examples", -1)) == dose]
    if not by_cell:
        raise ZeroBinding(
            "cell=%r query_kind=%r n_examples=%d bound ZERO rows of %s. A filter that binds "
            "nothing is not a filter (A-039 / C-074)." % (cell, qk, dose,
                                                          os.path.basename(bank_abs)))
    conds = sorted({str(r.get("condition")) for r in by_cell})
    if len(conds) != 1:
        raise RunnerRefusal(
            "cell %r spans %d distinct `condition` values on %s (%s), so no single --conditions "
            "value can reproduce the analyzer's bind." % (cell, len(conds),
                                                          os.path.basename(bank_abs), conds))
    cond = conds[0]
    by_cond = [r for r in rows.values()
               if str(r.get("condition")) == cond and str(r.get("query_kind")) == qk
               and int(r.get("n_examples", -1)) == dose]
    ids_cell = {r["prompt_id"] for r in by_cell}
    ids_cond = {r["prompt_id"] for r in by_cond}
    if ids_cell != ids_cond:
        raise RunnerRefusal(
            "A-039: selecting on cell=%r bound %d rows and selecting on condition=%r bound %d "
            "(symmetric difference %d) on %s. score_behavior has no --cells flag, so the launcher "
            "must select on `condition`; that is only legitimate where the mapping is 1:1, and "
            "here it is not." % (cell, len(ids_cell), cond, len(ids_cond),
                                 len(ids_cell ^ ids_cond), os.path.basename(bank_abs)))
    return {"cell": cell, "condition": cond, "n_rows": len(ids_cell),
            "query_kind": qk, "n_examples": dose, "mapping_is_1to1": True}


def split_bind(pr: Prereg, bank_abs: str, split: str, assign: Dict[str, str]) -> Dict[str, Any]:
    """Bind ONE domain split, as the EXCLUSION LIST `score_behavior` will be given.

    WHY `--split` IS IMPLEMENTED THIS WAY. `score_behavior` has no split flag; the bank's own
    `split` field is dev/heldout, which is NOT the preregistered domain split
    (`data/boombness_prompts/dcs_ts116_domain_split.json`, field `dsplit`, 67/23/23 domains). A
    `--split` argument that reached nothing would be a flag that cannot act. So the split is bound
    as a DECLARED, OUTCOME-INDEPENDENT prompt_id exclusion (which is what `--exclude-prompt-ids`
    exists for) and the surviving count is asserted with `--expect-n`. A train-split smoke
    therefore never computes a validation or test row at all.

    The population itself is bound by the ANALYZER's own `bind_rows` on `cell`, so the runner and
    the analyzer cannot disagree about which rows this phase is about, and the three
    whole-population exclusions come from the config's BOOLEAN `whole_population` field rather
    than from prose (C-086).
    """
    rows = load_bank_rows(bank_abs)
    b = bind_rows(pr, rows, assign)
    excl_domains = set(whole_population_exclusions(pr))
    keep, drop = [], []
    for pid, r in rows.items():
        in_pop = (str(r.get("cell")) == b["cell"] and str(r.get("query_kind")) == b["query_kind"]
                  and int(r.get("n_examples", -1)) == b["n_examples"])
        if not in_pop:
            continue
        dom = str(r.get("domain"))
        if dom not in assign:
            raise RunnerRefusal(
                "domain %r is in the bound population of %s and is absent from the frozen split "
                "manifest. A row whose split is unknown must not be silently kept or silently "
                "dropped." % (dom, os.path.basename(bank_abs)))
        (drop if (dom in excl_domains or assign[dom] != split) else keep).append(pid)
    if not keep:
        raise ZeroBinding(
            "split %r bound ZERO rows on %s. A stage whose population is empty must refuse, not "
            "run." % (split, os.path.basename(bank_abs)))
    kept = set(keep)
    n_dom = len({str(r["domain"]) for pid, r in rows.items() if pid in kept})
    per_dom = int(pr.require("population", "rows_per_domain_per_cell"))
    if n_dom * per_dom != len(keep):
        raise RunnerRefusal(
            "split %r binds %d rows over %d domains, but the frozen file says %d rows per domain "
            "(%d expected). A population that is not the shape the preregistration describes is "
            "not the preregistered population." % (split, len(keep), n_dom, per_dom,
                                                   n_dom * per_dom))
    # THE FROZEN FILE'S `split.n_train` IS THE **ANALYSED** COUNT, NOT THE ASSIGNED ONE. The
    # manifest on disk assigns 70 train domains and `split._exclusion_note` says so: "70 train
    # domains are ASSIGNED by the frozen manifest; 67 are ANALYSED after the THREE
    # whole-population preregistered exclusions ... Analysed split is 67/23/23 over 113 domains."
    # Both numbers are checked, and against DIFFERENT sources, so neither can drift alone.
    want = {"train": "n_train", "validation": "n_validation", "test": "n_test"}[split]
    declared_analysed = int(pr.require("split", want))
    if n_dom != declared_analysed:
        raise RunnerRefusal(
            "the %s split binds %d ANALYSED domains and the frozen file declares %d."
            % (split, n_dom, declared_analysed))
    n_assigned = len([d for d, sp in assign.items() if sp == split])
    n_excl_here = len([d for d in excl_domains if assign.get(d) == split])
    if n_assigned - n_excl_here != declared_analysed:
        raise RunnerRefusal(
            "the split manifest ASSIGNS %d domains to %r and %d of the whole-population "
            "exclusions sit in it, leaving %d -- but the frozen file declares %d ANALYSED. The "
            "manifest and the preregistration disagree about the population."
            % (n_assigned, split, n_excl_here, n_assigned - n_excl_here, declared_analysed))
    return {"split": split, "bank": bank_abs, "n_keep": len(keep), "n_drop": len(drop),
            "n_domains": n_dom, "keep_ids": sorted(keep), "drop_ids": sorted(drop),
            "expect_n": len(keep), "n_analysed_rows": b["n_rows"],
            "n_analysed_domains": b["n_domains"], "by_split": b["by_split"],
            "excluded_whole_population_domains": sorted(excl_domains)}


def exclusion_file_text(pr: Prereg, bind: Dict[str, Any]) -> str:
    """The `--exclude-prompt-ids` file, carrying its own provenance in `#` comments."""
    head = [
        "# DCS-PR-059 runner: the rows OUTSIDE domain split %r on %s."
        % (bind["split"], os.path.basename(bind["bank"])),
        "# Source: %s field %s (sha16 %s) -- OUTCOME-INDEPENDENT, frozen before any outcome."
        % (pr.require("split", "manifest"), pr.require("split", "field"),
           pr.require("split", "manifest_sha16")),
        "# Plus the preregistered whole-population exclusions: %s"
        % (", ".join(bind["excluded_whole_population_domains"]) or "(none)"),
        "# keep=%d drop=%d domains_kept=%d" % (bind["n_keep"], bind["n_drop"], bind["n_domains"]),
    ]
    return "\n".join(head + bind["drop_ids"]) + "\n"


def exclusion_file_name(bank_abs: str, split: str) -> str:
    base = os.path.basename(bank_abs).replace(".jsonl", "")
    return "exclude_%s_%s.txt" % (base, split)


# ============================================================================================
# 4. CONSTRUCTIBILITY -- every refusal is named, nothing is substituted
# ============================================================================================
def constructibility(pr: Prereg, arm: ArmSpec) -> Dict[str, Any]:
    """Can this arm be launched TODAY, with the instrument as it stands? Refusals are named."""
    reasons: List[str] = []
    scopes = declared_scopes(pr)
    span = query_span_rel_end(pr)
    s = scopes.get(arm.scope_id)
    if s is None:
        reasons.append("the manifest names scope %r and scopes.family does not declare it"
                       % arm.scope_id)
    elif s["unconstructible"] and arm.kind != "baseline":
        reasons.append("scope %s is declared UNCONSTRUCTIBLE: %s" % (arm.scope_id, s["status"]))

    if arm.kind == "bridge":
        # PR059-D6, RESOLVED -- but NOT by deleting the guard. The refusal now re-derives
        # constructibility from `pair_common`'s OWN dispatch table, so if the attention-mask
        # bridge family is ever removed this arm is refused BY NAME again, before a queue slot
        # and a model load, instead of dying at the node.
        _ok, _why = bridge_family_constructible()
        if not _ok:
            reasons.append("%s CURRENT STATE: %s" % (DEFECT_D6_BRIDGE_NOT_CONSTRUCTIBLE, _why))
    elif arm.kind == "random_row_control":
        con = random_row_control_constructible(pr, arm.scope_id, s["rel_end_rows"], span)
        if not con["constructible"]:
            reasons.append("PR059-D1: %s" % con["reason"])
        else:
            # THE PRODUCER RE-DRAWS. The runner passes the SCOPE's rows plus the draw index and
            # the seed, and `score_behavior.random_row_control_rel_end` draws the control rows at
            # the node. So the two draws must be verified EQUAL on CPU, here, or the arm that runs
            # is not the arm the analyzer planned.
            want = random_row_control_draw(pr, arm.scope_id, s["rel_end_rows"],
                                           arm.draw_index, span)["rel_end_rows"]
            got = producer_random_row_draw(pr, arm.scope_id, s["rel_end_rows"], arm.draw_index,
                                           span)
            if sorted(want) != sorted(got["rel_end_rows"]):
                reasons.append(
                    "the analyzer's draw %d for %s is %s and score_behavior's own "
                    "random_row_control_rel_end returns %s. The arm that would run is NOT the arm "
                    "that was planned." % (arm.draw_index, arm.scope_id, want,
                                           got["rel_end_rows"]))
    elif arm.kind == "nondemo_control":
        name = nondemo_arm_name(arm.draw_index)
        import score_behavior as SB
        if name not in SB.NONDEMO_DRAW_ARMS:
            reasons.append(
                "the nondemo control draw %d maps to intervention arm %r, which is not in "
                "score_behavior.NONDEMO_DRAW_ARMS (%s). Refusing to resolve it by resemblance."
                % (arm.draw_index, name, list(SB.NONDEMO_DRAW_ARMS)[:4]))
    elif arm.kind not in ("baseline", "scope"):
        reasons.append("unknown arm kind %r" % arm.kind)

    #: PR059-D1 again, at the level the design cares about: a SCOPE arm whose dose-matched
    #: control cannot exist is still RUNNABLE -- it just cannot be rendered as a controlled
    #: estimate. That is a reporting consequence, decided in the amendment, not a launch refusal;
    #: it is recorded on the arm so the artifact carries it.
    no_ctrl = ""
    if arm.kind == "scope" and s and s["rel_end_rows"] and arm.scope_id != reference_scope_id(pr):
        c = random_row_control_constructible(pr, arm.scope_id, s["rel_end_rows"], span)
        if not c["constructible"]:
            no_ctrl = c["reason"]
    return {"arm_id": arm.arm_id, "constructible": not reasons, "reasons": reasons,
            "has_no_dose_matched_control": bool(no_ctrl), "no_control_reason": no_ctrl}


def producer_random_row_draw(pr: Prereg, scope_id: str, scope_rel_end: Sequence[int],
                             draw_index: int, span: Sequence[int]) -> Dict[str, Any]:
    """`score_behavior`'s OWN draw for this scope/draw, so the plan and the node agree."""
    import score_behavior as SB
    return SB.random_row_control_rel_end(scope_id, list(scope_rel_end), list(span),
                                         int(pr.require("seeds", "random_row_draws")),
                                         int(draw_index))


# ============================================================================================
# 5. THE COMMAND LINE FOR ONE ARM -- built here, cross-checked against the analyzer
# ============================================================================================
def build_argv(pr: Prereg, arm: ArmSpec, ctx: Dict[str, Any]) -> List[str]:
    """The `score_behavior` argv for one arm. Every value comes from the frozen file or ArmSpec."""
    con = ctx["constructibility"]
    if not con["constructible"]:
        raise RunnerRefusal("arm %s is not constructible: %s" % (arm.arm_id, con["reasons"][0]))
    lo, hi = intervention_band(pr)
    scopes = declared_scopes(pr)
    span = query_span_rel_end(pr)
    argv = [
        "--bank", bank_path_for(pr, arm.bank),
        "--query-kinds", str(arm.query_kind),
        # A-039: the cell is bound on `cell` by the analyzer and reproduced here through the
        # `condition` value that binds EXACTLY the same prompt_ids on this bank. Never a literal.
        "--conditions", str(ctx["condition"]),
        "--n-examples", str(int(arm.n_examples)),
        "--readout-ids", "whole_answer",
        "--attn-impl", str(required_attn_impl(pr)),
        "--max-new", str(int(pr.require("decoding", "max_new_tokens"))),
        "--arm", arm.arm_id,
        "--tag", arm.tag(),
    ]
    # THE SEED. The frozen file declares seeds.nondemo_draws SEPARATELY from every other seed, and
    # `score_behavior` derives each nondemo draw's seed from `--seed`; a control band that quietly
    # inherits another seed is not the declared band.
    seed = int(pr.require("seeds", "nondemo_draws") if arm.kind == "nondemo_control"
               else pr.require("seeds", "extraction"))
    argv += ["--seed", str(seed)]

    if arm.kind != "baseline":
        name = (nondemo_arm_name(arm.draw_index) if arm.kind == "nondemo_control" else "demo_all")
        argv += ["--intervene", "%s:attn_knockout:%d-%d:1.0" % (name, lo, hi),
                 "--knockout-scope", "query_last_k_rows",
                 # '=' form on purpose: argparse reads a bare `-28,...` after a space as an option.
                 "--knockout-rel-end-rows=%s" % rel_end_arg(scopes[arm.scope_id]["rel_end_rows"]),
                 "--knockout-scope-id", arm.scope_id,
                 "--knockout-query-span-rel-end=%s" % rel_end_span_arg(span)]
        if arm.kind == "random_row_control":
            argv += ["--knockout-random-row-draw", str(int(arm.draw_index)),
                     "--knockout-random-row-seed",
                     str(int(pr.require("seeds", "random_row_draws")))]
        if arm.kind == "bridge":
            argv += ["--pr057-disable-hooks", "--pr057-liveness-out", "auto"]
    if ctx.get("exclude_file"):
        argv += ["--exclude-prompt-ids", ctx["exclude_file"]]
    if ctx.get("expect_n"):
        argv += ["--expect-n", str(int(ctx["expect_n"]))]
    if ctx.get("limit"):
        argv += ["--limit", str(int(ctx["limit"]))]
    for tok in argv:
        if " " in tok or '"' in tok or "'" in tok:
            raise RunnerRefusal(
                "argv token %r contains a space or a quote. BOOMB_ARGS is word-split by "
                "run_boombness.sh, so such a value is torn apart at the node (job 766661)." % tok)
    return argv


def assert_expect_n_agrees_with_limit(argv: Sequence[str]) -> None:
    """`--expect-n` and `--limit` must not contradict each other.  `C-123`, job 868569.

    PHASE 9's smoke stage emitted `--expect-n 670 --limit 40`: the first says "this arm scores the
    whole bound population", the second truncates it to 40. `score_behavior`'s row-count guard did
    its job and refused -- *"population is 40 rows, --expect-n says 670. A silently-shrunken
    sample is how R-18 happened."* -- but only after a 27-minute queue wait and a model load.

    That guard is the LAST line of defence and it fires on a GPU. This one fires in the runner,
    before anything is submitted, because two flags that must agree should be checked where they
    are built rather than where they are consumed. It refuses BOTH directions.
    """
    argv = list(argv)
    if "--expect-n" not in argv or "--limit" not in argv:
        return
    n = int(argv[argv.index("--expect-n") + 1])
    lim = int(argv[argv.index("--limit") + 1])
    if lim <= 0:
        return
    if n != lim:
        raise RunnerRefusal(
            "C-123: --expect-n %d contradicts --limit %d in the SAME argv. --expect-n must "
            "describe the population the arm will ACTUALLY score, and --limit truncates it, so "
            "the two must be EQUAL whenever a limit is applied. Refusing here rather than letting "
            "score_behavior's row-count guard catch it after a queue wait and a model load."
            % (n, lim))


_FLAG_RE_CACHE: Dict[str, Any] = {}


def _analyzer_flag(text: str, flag: str) -> Optional[str]:
    """Read one flag's value out of the analyzer's prose-adjacent launch command."""
    rx = _FLAG_RE_CACHE.get(flag)
    if rx is None:
        rx = re.compile(re.escape(flag) + r"[ =]+([^\s]+)")
        _FLAG_RE_CACHE[flag] = rx
    m = rx.search(text)
    return m.group(1) if m else None


def assert_argv_agrees_with_analyzer(pr: Prereg, arm: ArmSpec,
                                     argv: Sequence[str]) -> Dict[str, Any]:
    """The anti-drift check: the runner and the analyzer must describe the SAME arm.

    `launch_command()` is the analyzer's own idea of how this arm is launched. It is prose-adjacent
    (it carries `#` comments) so it is parsed, not diffed, and everything that decides WHICH
    EXPERIMENT RAN is compared: the bank, the cell, the channel, the dose, the attention
    implementation, the intervention's arm name / mode / band / alpha, the knockout scope and the
    DECLARED rel_end row set. The two known vocabulary differences go through the tables in
    section 1 and nowhere else.
    """
    cmd = launch_command(pr, arm)
    got = {}
    for i, tok in enumerate(argv):
        if tok.startswith("--"):
            if "=" in tok:
                k, v = tok.split("=", 1)
                got[k] = v
            elif i + 1 < len(argv) and not argv[i + 1].startswith("--"):
                got[tok] = argv[i + 1]
            else:
                got[tok] = ""
    out: Dict[str, Any] = {"arm_id": arm.arm_id, "analyzer_launch": cmd, "mismatches": []}

    def _cmp(what, a, b):
        if str(a) != str(b):
            out["mismatches"].append("%s: analyzer=%r runner=%r" % (what, a, b))

    _cmp("--bank", _analyzer_flag(cmd, "--bank"), got.get("--bank"))
    _cmp("cell/condition", _analyzer_flag(cmd, "--only-cell"), primary_cell(pr))
    _cmp("query kind", _analyzer_flag(cmd, "--only-query-kind"), got.get("--query-kinds"))
    _cmp("n_examples", _analyzer_flag(cmd, "--only-n-examples"), got.get("--n-examples"))
    _cmp("attn impl", _analyzer_flag(cmd, "--attn-impl"), got.get("--attn-impl"))

    a_no_ko = "--no-knockout" in cmd
    r_no_ko = "--intervene" not in got
    if a_no_ko != r_no_ko:
        out["mismatches"].append("baseline: analyzer --no-knockout=%s runner has no --intervene=%s"
                                 % (a_no_ko, r_no_ko))
    if not a_no_ko:
        a_int = _analyzer_flag(cmd, "--intervene")
        a_name, a_mode, a_band, a_alpha = str(a_int).split(":")
        r_name, r_mode, r_band, r_alpha = str(got.get("--intervene")).split(":")
        want_name = (nondemo_arm_name(arm.draw_index) if arm.kind == "nondemo_control" else a_name)
        _cmp("intervention arm name", want_name, r_name)
        _cmp("mode", a_mode, r_mode)
        _cmp("layer band", a_band, r_band)
        if abs(float(a_alpha) - float(r_alpha)) > 0:
            out["mismatches"].append("alpha: analyzer=%r runner=%r" % (a_alpha, r_alpha))
        _cmp("knockout scope", _analyzer_flag(cmd, "--knockout-scope"),
             got.get("--knockout-scope"))
        # THE ROW SET. For a scope / nondemo arm the analyzer prints the scope's own rows; for a
        # random-row control it prints the DRAWN rows, and the runner passes the scope's rows plus
        # the draw index because the PRODUCER redraws. Both are compared against the object the
        # analyzer itself computed -- never against a re-typed list.
        a_rows = sorted(int(x) for x in str(_analyzer_flag(cmd, "--declared-rel-end")).split(","))
        r_rows = sorted(int(x) for x in str(got.get("--knockout-rel-end-rows")).split(","))
        if arm.kind == "random_row_control":
            drawn = sorted(producer_random_row_draw(
                pr, arm.scope_id, declared_scopes(pr)[arm.scope_id]["rel_end_rows"],
                arm.draw_index, query_span_rel_end(pr))["rel_end_rows"])
            if drawn != a_rows:
                out["mismatches"].append(
                    "random-row draw %d: analyzer planned %s, the producer's own draw is %s"
                    % (arm.draw_index, a_rows, drawn))
            _cmp("scope rows behind the draw",
                 sorted(declared_scopes(pr)[arm.scope_id]["rel_end_rows"]), r_rows)
        else:
            _cmp("declared rel_end rows", a_rows, r_rows)
    if out["mismatches"]:
        raise RunnerRefusal(
            "the runner's command for arm %s DISAGREES with the analyzer's launch_command: %s. "
            "Two files that disagree about what an arm is would be the whole failure mode of this "
            "phase." % (arm.arm_id, "; ".join(out["mismatches"])))
    out["ok"] = True
    return out


# ============================================================================================
# 6. STAGES AND THE FIXED ORDER
# ============================================================================================
def stage_selector(pr: Prereg, stage: str):
    """Which arms belong to a stage.

    The staged order is the frozen `kill_condition`'s, not a convenience: the baseline `S_0` and
    the reference scope `S_G` are submitted and read FIRST, and if `S_G` does not move the readout
    no narrower scope is submitted at all. `smoke` is checklist item `U8`, which names `S_G` and
    `S_C` -- plus the baseline, because U8's own criteria are paired against it.
    """
    ref = reference_scope_id(pr)
    if stage not in STAGE_ORDER:
        raise RunnerRefusal("unknown stage %r; known: %s" % (stage, list(STAGE_ORDER)))
    if stage == "smoke":
        return lambda x: (x.kind in ("baseline", "scope")
                          and x.scope_id in ("S_0", ref, "S_C"))
    if stage == "kill":
        return lambda x: x.scope_id in ("S_0", ref)
    return lambda x: x.scope_id not in ("S_0", ref)


def assert_stages_partition(pr: Prereg) -> Dict[str, Any]:
    """`kill` and `family` must PARTITION the manifest -- no arm in both, no arm in neither."""
    arms = build_arm_manifest(pr)
    k, f = stage_selector(pr, "kill"), stage_selector(pr, "family")
    both = [x.arm_id for x in arms if bool(k(x)) == bool(f(x))]
    if both:
        raise RunnerRefusal("stages kill and family do not PARTITION the manifest: %s" % both[:5])
    return {"n_arms": len(arms), "n_kill": sum(1 for x in arms if k(x)),
            "n_family": sum(1 for x in arms if f(x)),
            "n_smoke": sum(1 for x in arms if stage_selector(pr, "smoke")(x))}


def stage_dir(state_root: str, stage: str, split: str) -> str:
    return os.path.join(state_root, "%s_%s" % (stage, split))


def assert_stage_order(state_root: str, stage: str, split: str) -> Dict[str, Any]:
    """`smoke -> kill -> family`, read off the earlier stages' own `DONE.json`, not a comment."""
    idx = STAGE_ORDER.index(stage)
    seen = []
    for earlier in STAGE_ORDER[:idx]:
        hits = []
        root = state_root
        if os.path.isdir(root):
            for d in sorted(os.listdir(root)):
                if d.startswith(earlier + "_") and os.path.exists(
                        os.path.join(root, d, "DONE.json")):
                    hits.append(d)
        if not hits:
            raise RunnerRefusal(
                "stage %r may not run: the earlier stage %r has no completed run (no "
                "%s/%s_*/DONE.json). The frozen kill_condition fixes this order before any arm "
                "runs -- the baseline and the reference scope are read FIRST, and running six "
                "narrower cuts to find nothing would be six chances to report a null that is "
                "really a dead intervention." % (stage, earlier, state_root, earlier))
        seen.append({"stage": earlier, "dirs": hits})
    return {"stage": stage, "split": split, "predecessors": seen}


def assert_stage_has_no_prior_verdict(sdir: str) -> None:
    """Refuse a stage that ALREADY carries a terminal verdict -- BEFORE any arm runs.  `C-124`.

    `write_terminal` enforces "a stage has ONE verdict", which is correct, but it enforces it at
    the END. PHASE 9's job 868702 ran BOTH smoke arms to completion (40 rows each, exactly as
    designed) and was then refused, because job 868569 -- which had died 13 seconds in on the
    C-123 `--expect-n`/`--limit` defect, having completed ZERO arms -- had already written
    `ABORTED.json` into the same stage directory. A successful run was discarded at the last step
    by a stale record from a superseded failure.

    The verdict rule is right; enforcing it only at the end is not. This checks at the START, so
    the operator is told before an allocation is spent rather than after. The remedy is
    deliberately NOT automatic: a terminal record is evidence, and silently overwriting one is how
    a failed run gets quietly reported as a success. Archive it by hand, with provenance.
    """
    for name in ("DONE.json", "ABORTED.json"):
        fp = os.path.join(sdir, name)
        if os.path.exists(fp):
            try:
                prior = json.load(open(fp))
            except Exception:
                prior = {}
            raise RunnerRefusal(
                "stage dir %s ALREADY carries %s (status=%r, failed_arm=%r, n_arms_done=%s). A "
                "stage has ONE verdict, so this run could not write its own -- and refusing here, "
                "before any arm runs, is the whole point: PHASE 9's job 868702 completed both "
                "smoke arms and was rejected at the end by a stale record from a run that had "
                "completed none.\n  If that prior verdict is superseded, ARCHIVE it with "
                "provenance (e.g. rename to %s.<jobid>.superseded.json) rather than deleting it, "
                "then re-run. Never hand-write a terminal record."
                % (sdir, name, prior.get("status"), prior.get("failed_arm"),
                   prior.get("n_arms_done"), name))


# ============================================================================================
# 7. PROVENANCE AND TERMINAL RECORDS
# ============================================================================================
def slurm_provenance() -> Dict[str, Any]:
    """`A15`. Who wrote this record: the SLURM job id, its node list, and the host.

    PHASE 9's `smoke_train/DONE.json` could not be traced to the job that wrote it: the arm run
    dirs carried `slurm_job_id` 868702 in their own `RUNMETA.json` and the stage record -- written
    later, by a different invocation -- carried nothing. A terminal record that cannot name the
    job that produced it is evidence with no provenance. Read from the environment, never typed,
    and recorded as `null` off a batch node rather than invented.
    """
    return {"slurm_job_id": os.environ.get("SLURM_JOB_ID") or None,
            "slurm_array_task_id": os.environ.get("SLURM_ARRAY_TASK_ID") or None,
            "slurm_nodelist": os.environ.get("SLURM_JOB_NODELIST")
                              or os.environ.get("SLURM_NODELIST") or None,
            "hostname": socket.gethostname(),
            "pid": os.getpid(),
            "written_at": time.strftime("%Y-%m-%d %H:%M:%S")}


def write_terminal(sdir: str, name: str, blob: Dict[str, Any]) -> None:
    """DONE.json / ABORTED.json. DIFFERENT FILES, so a partial stage can never be read as a
    complete one, and neither may overwrite the other.  `A15`: every terminal record carries the
    SLURM job id, node list and host of the invocation that wrote it."""
    blob = dict(blob)
    blob.setdefault("provenance", slurm_provenance())
    os.makedirs(sdir, exist_ok=True)
    other = "ABORTED.json" if name == "DONE.json" else "DONE.json"
    if os.path.exists(os.path.join(sdir, other)):
        raise RunnerRefusal("%s already carries %s; refusing to also write %s -- a stage has ONE "
                            "verdict." % (sdir, other, name))
    with open(os.path.join(sdir, name), "w") as fh:
        json.dump(blob, fh, indent=2, default=str)


# ============================================================================================
# 8. THE RESUMABLE MANIFEST
# ============================================================================================
def manifest_load(sdir: str) -> Dict[str, Any]:
    """Load the manifest, and RE-VERIFY every 'done' arm against the artifact on disk.

    A manifest is a claim; the run directory is the evidence. An arm recorded done whose directory
    has no `DONE.json` is reset to pending -- a partial run must never be mistaken for a complete
    one just because a driver said so (C-051 / C-012).
    """
    path = os.path.join(sdir, MANIFEST_FILE)
    if not os.path.exists(path):
        return {}
    man = json.load(open(path))
    for _arm_id, rec in list((man.get("arms") or {}).items()):
        if rec.get("status") != "done":
            continue
        d = rec.get("run_dir")
        if not (d and os.path.exists(os.path.join(d, "DONE.json"))):
            rec["status"] = "pending"
            rec["_reset_reason"] = ("the manifest claimed this arm was done but %s has no "
                                    "DONE.json; a partial run is not a complete one" % d)
    return man


def manifest_save(sdir: str, man: Dict[str, Any]) -> None:
    os.makedirs(sdir, exist_ok=True)
    man["updated"] = time.strftime("%Y-%m-%d %H:%M:%S")
    tmp = os.path.join(sdir, MANIFEST_FILE + ".tmp")
    with open(tmp, "w") as fh:
        json.dump(man, fh, indent=2, default=str)
    os.replace(tmp, os.path.join(sdir, MANIFEST_FILE))


# ============================================================================================
# 9. THE MODEL CACHE -- the reason this file exists
# ============================================================================================
class ModelCache:
    """Memoise `ds_common.load_model` so 78 arms load the weights ONCE.

    `DONE.json.model_loads` must be 1 for a single-model stage. A second load is not silently
    tolerated -- it is reported, and a stage that loaded the weights per arm has not done the one
    thing this file exists to do.
    """

    def __init__(self) -> None:
        self.n_loads = 0
        self.n_hits = 0
        self._cache: Dict[Any, Any] = {}
        self._orig = None
        self._mod = None

    def install(self, module=None):
        if module is None:
            import ds_common as module  # noqa: PLW0127
        self._mod = module
        self._orig = module.load_model
        cache = self

        def _cached(model_id, *a, **kw):
            key = (model_id, str(kw.get("dtype")), kw.get("attn_implementation"),
                   kw.get("quantize"), repr(a))
            if key in cache._cache:
                cache.n_hits += 1
                print("[pr059] model cache HIT (%d) -- weights are NOT reloaded" % cache.n_hits,
                      flush=True)
                return cache._cache[key]
            cache.n_loads += 1
            print("[pr059] model LOAD #%d %r" % (cache.n_loads, key[:3]), flush=True)
            lm = cache._orig(model_id, *a, **kw)
            cache._cache[key] = lm
            return lm

        module.load_model = _cached
        return self

    def uninstall(self):
        if self._mod is not None and self._orig is not None:
            self._mod.load_model = self._orig
        self._mod = self._orig = None


# ============================================================================================
# 10. THE STAGE-AWARE PRE-EXTRACTION CHECKLIST GATE
# ============================================================================================
#
# `scripts/dcs_ts_prereg.py:validate` enforces the `done` boolean alone and knows nothing about
# stages. This gate is STRICTLY STRONGER, never weaker. An item is scoped out of a stage ONLY if
# ALL THREE hold:
#   1. the preregistration (or its amendment) declares `applies_to_stages` for it and the running
#      stage is not in it;
#   2. THIS runner carries a predicate that RE-DERIVES the item's relevance from the run's own
#      binding and the arm manifest;
#   3. that predicate, run against this stage's OWN arms, says the item is irrelevant.
# An item with no declared scope blocks. An item whose scope this runner cannot re-derive blocks
# -- a prose scope with no code path is not a scope. An item whose scope the arms CONTRADICT
# blocks, and says so.

def _feeds_a_confirmatory_estimate(pr: Prereg, stage: str, ctx: Dict[str, Any]) -> bool:
    """Re-derived from the RUN'S OWN BINDING, not from the stage's name: an arm scored over a
    truncated population on the TRAIN split cannot enter a confirmatory estimate, because the
    primary statistic is a domain-mean over the analysed population."""
    return not (int(ctx.get("limit") or 0) > 0 and str(ctx.get("split")) == "train")


def _runs_a_family_member_for_real(pr: Prereg, stage: str, ctx: Dict[str, Any]) -> bool:
    """Re-derived from the ARM MANIFEST and the binding: does this stage produce a number that a
    Holm-corrected family member's estimate would rest on?"""
    sel = stage_selector(pr, stage)
    members = set(family_member_ids(pr))
    any_member = any(x.scope_id in members for x in build_arm_manifest(pr) if sel(x))
    return any_member and _feeds_a_confirmatory_estimate(pr, stage, ctx)


def _claims_the_complete_arm_set(pr: Prereg, stage: str, ctx: Dict[str, Any]) -> bool:
    """Re-derived from the MANIFEST: does this stage, together with its predecessors, claim the
    whole preregistered arm set? Only then does a disagreement about what that set IS matter."""
    arms = {x.arm_id for x in build_arm_manifest(pr)}
    idx = STAGE_ORDER.index(stage)
    covered: set = set()
    for s in STAGE_ORDER[:idx + 1]:
        if s == "smoke":
            continue                      # the smoke is a subset re-run, not a stage of the plan
        sel = stage_selector(pr, s)
        covered |= {x.arm_id for x in build_arm_manifest(pr) if sel(x)}
    return covered == arms


def _runs_a_bridge_arm(pr: Prereg, stage: str, ctx: Dict[str, Any]) -> bool:
    """Re-derived from the ARM MANIFEST: does this stage actually install a disabled-hook bridge?"""
    sel = stage_selector(pr, stage)
    return any(x.kind == "bridge" for x in build_arm_manifest(pr) if sel(x))


def _reads_the_test_split(pr: Prereg, stage: str, ctx: Dict[str, Any]) -> bool:
    """`V3` / `U3` is, IN ITS OWN WORDS, a precondition for READING TEST: "if power < 0.8, return
    CANNOT ANSWER WITHOUT READING TEST." The run that MEASURES it is a VALIDATION run, so an
    unmeasured V3 blocking the validation run is circular -- the same shape PHASE 9 resolved by
    letting its `q1` validation power run proceed while the checklist was still open.

    RE-DERIVED, never read off the flag's spelling: this asks whether the population THIS RUN
    WILL ACTUALLY SCORE -- the `keep_ids` of the exclusion list handed to `score_behavior`, built
    from the bank on disk -- contains any domain the FROZEN split manifest assigns to TEST. A run
    called `validation` that nonetheless bound a test domain is a TEST read and V3 blocks it.
    Anything this predicate cannot re-derive is fail-closed: it returns True and the item blocks.
    """
    split = str(ctx.get("split") or "")
    if split not in ("train", "validation", "test"):
        return True
    try:
        assign = load_split(pr)
        test_domains = {d for d, sp in assign.items() if str(sp) == "test"}
        if not test_domains:
            return True                    # a manifest with no TEST split cannot witness anything
        for bank_key in primary_banks(pr):
            bank_abs = repo_path(bank_path_for(pr, bank_key))
            rows = load_bank_rows(bank_abs)
            b = split_bind(pr, bank_abs, split, assign)
            for pid in b["keep_ids"]:
                if str((rows.get(pid) or {}).get("domain")) in test_domains:
                    return True
        return False
    except Exception:                                        # noqa: BLE001 -- fail CLOSED
        return True


def _runs_a_random_row_control_band(pr: Prereg, stage: str, ctx: Dict[str, Any]) -> bool:
    """Re-derived from the ARM MANIFEST: does this stage run a per-scope RANDOM-ROW control BAND
    at all? `U2`'s "verify the 3 draws produce 3 DISTINCT output hashes" is a statement about the
    outputs of THOSE arms, and a stage that builds none of them cannot make it true or false."""
    sel = stage_selector(pr, stage)
    return any(x.kind == "random_row_control" for x in build_arm_manifest(pr) if sel(x))


CHECKLIST_STAGE_RELEVANCE = {
    # V3's relevance is NOT "does this feed a confirmatory estimate" -- the validation run that
    # MEASURES the power is itself confirmatory-grade work, and gating it on its own result is
    # circular. Its own text scopes it to READING TEST, so that is what is re-derived.
    "V3": ("the population this stage will actually score contains a domain the frozen split "
           "manifest assigns to TEST", _reads_the_test_split),
    "V8": ("the stage produces a number that enters a confirmatory estimate (a smoke cannot "
           "require itself to have already run)", _feeds_a_confirmatory_estimate),
    "V10": ("the stage's arms carry a Holm-corrected family member's estimate, so the analyzer's "
            "liveness verdict is load-bearing for it", _runs_a_family_member_for_real),
    "V11": ("this stage claims the COMPLETE preregistered arm set, so a disagreement about what "
            "that set is decides whether the run is vacuous by omission",
            _claims_the_complete_arm_set),
    "V12": ("the stage installs a disabled-hook bridge arm (null L-N1)", _runs_a_bridge_arm),
    "V13": ("the stage produces a number an analyzer VERDICT would rest on (it is not a truncated "
            "TRAIN smoke)", _feeds_a_confirmatory_estimate),
    "V16": ("the stage runs a per-scope RANDOM-ROW control band, whose three draws are what the "
            "three-distinct-output-hashes clause is about", _runs_a_random_row_control_band),
}


def load_amendment(amendment_path: str, pr: Prereg) -> Dict[str, Any]:
    """Load an AMENDMENT and verify it amends THIS preregistration, at the sha it names.

    An amendment is a NEW file; the parent is never edited. Anything it supersedes it must SAY it
    supersedes -- `amendment.supersedes[].field` -- so a file cannot quietly replace a gate it
    never claimed to touch.
    """
    fp = amendment_path if os.path.isabs(amendment_path) else repo_path(amendment_path)
    if not os.path.exists(fp):
        raise RunnerRefusal("amendment not found: %s" % amendment_path)
    obj = json.load(open(fp))
    if obj.get("status") != "FROZEN":
        raise RunnerRefusal("amendment %s has status %r, not FROZEN"
                            % (amendment_path, obj.get("status")))
    am = obj.get("amendment") or {}
    if am.get("amends_prereg_id") != pr.require("id"):
        raise RunnerRefusal("amendment %s amends %r but the loaded preregistration is %r"
                            % (amendment_path, am.get("amends_prereg_id"), pr.require("id")))
    parent = am.get("amends") or ""
    want, got = am.get("amends_file_sha16"), file_sha16(repo_path(parent))
    if want != got:
        raise RunnerRefusal(
            "amendment %s pins its parent %s at sha16 %r and the file on disk hashes %r. An "
            "amendment to a file that has since changed amends nothing."
            % (amendment_path, parent, want, got))
    fields = {str(x.get("field", "")).split(" ")[0] for x in (am.get("supersedes") or [])}
    if "pre_extraction_checklist" not in fields:
        raise RunnerRefusal(
            "amendment %s does not declare that it supersedes `pre_extraction_checklist`, so its "
            "own checklist may not stand in for the parent's." % amendment_path)
    return obj


def checklist_gate(prereg_path: str, amendment_path: str, stage: str,
                   ctx: Dict[str, Any]) -> Dict[str, Any]:
    """The BLOCKING pre-extraction checklist, evaluated FOR ONE STAGE."""
    pr = load_prereg(prereg_path, for_extraction=False)
    base = pr.obj
    checklist = list(base.get("pre_extraction_checklist") or [])
    artifacts = dict(base.get("artifacts") or {})
    source = prereg_path
    blocking: List[str] = []
    scoped_out: List[Dict[str, Any]] = []

    if amendment_path:
        amd = load_amendment(amendment_path, pr)
        acl = list(amd.get("pre_extraction_checklist") or [])
        if not acl:
            raise RunnerRefusal("amendment %s carries an EMPTY checklist" % amendment_path)
        # Every BLOCKING parent item must be superseded BY NAME, or it still stands. An amendment
        # that quietly drops a parent blocker would be a relaxation wearing a supersession's name.
        superseded = set()
        for it in acl:
            for tok in str(it.get("supersedes", "")).replace("(", " ").replace(")", " ").split():
                superseded.add(tok.strip(",+"))
        orphan = [str(it.get("id")) for it in checklist
                  if it.get("blocking") and not it.get("done")
                  and str(it.get("id")) not in superseded]
        if orphan:
            blocking.append(
                "the amendment %s supersedes no item for BLOCKING parent checklist item(s) %s, so "
                "they still stand and are not done" % (amendment_path, orphan))
        checklist = acl
        artifacts.update(amd.get("artifacts") or {})
        source = amendment_path

    if not checklist:
        blocking.append("pre_extraction_checklist is empty -- refusing to extract behind a "
                        "checklist that declares nothing")
    for item in checklist:
        iid = str(item.get("id", "<no id>"))
        if "blocking" not in item or "done" not in item:
            blocking.append("checklist %s: must declare boolean 'blocking' and 'done' (C-086)"
                            % iid)
            continue
        if not isinstance(item["blocking"], bool) or not isinstance(item["done"], bool):
            blocking.append("checklist %s: 'blocking'/'done' must be booleans" % iid)
            continue
        if not item["blocking"] or item["done"]:
            continue
        scope = item.get("applies_to_stages")
        if not scope:
            blocking.append("%s [%s] is BLOCKING and not done, and declares no applies_to_stages: "
                            "%s" % (iid, source, str(item.get("item"))[:150]))
            continue
        if stage in scope:
            blocking.append("%s [%s] is BLOCKING, not done, and applies to stage %r: %s"
                            % (iid, source, stage, str(item.get("item"))[:150]))
            continue
        rel = CHECKLIST_STAGE_RELEVANCE.get(iid)
        if rel is None:
            blocking.append(
                "%s [%s] is BLOCKING, not done, and declares applies_to_stages=%s -- but this "
                "runner has NO predicate that re-derives its relevance, so the scope is prose. A "
                "prose scope with no code path is not a scope (C-086, the same failure with the "
                "sign flipped)." % (iid, source, scope))
            continue
        why, pred = rel
        if pred(pr, stage, ctx):
            blocking.append(
                "%s [%s] declares applies_to_stages=%s, but stage %r's OWN arms and binding "
                "contradict that: %s. The declared scope is wrong and the item blocks."
                % (iid, source, scope, stage, why))
            continue
        scoped_out.append({"id": iid, "applies_to_stages": list(scope),
                           "why": "not relevant to stage %r, RE-DERIVED at launch: NOT (%s)"
                                  % (stage, why),
                           "item": str(item.get("item"))[:200]})
    # `artifacts.analyzer_exists` is the loader's own extraction gate. It is applied here on the
    # SAME re-derivation as V13 and no other: an analyzer that cannot emit a verdict blocks a run
    # whose numbers a verdict would rest on, and does not block an instrument smoke that emits no
    # verdict and reads a truncated TRAIN population. `scripts/dcs_ts_prereg.py --for-extraction`
    # is UNCHANGED and still refuses on this flag unconditionally, so the published gate keeps its
    # code path; this one is narrower ONLY where it can re-derive that it may be.
    if not artifacts.get("analyzer_exists", False):
        if _feeds_a_confirmatory_estimate(pr, stage, ctx):
            blocking.append(
                "artifacts.analyzer_exists is false [%s] -- refusing to extract behind an analyzer "
                "that does not exist (PR059-D7: analyse() ends at the liveness gates and emits no "
                "verdict)" % source)
        else:
            scoped_out.append({"id": "artifacts.analyzer_exists",
                               "applies_to_stages": ["kill", "family"],
                               "why": "not relevant to stage %r, RE-DERIVED at launch: this run "
                                      "is a truncated TRAIN smoke and emits no verdict" % stage,
                               "item": "artifacts.analyzer_exists is false"})
    return {"ok": not blocking, "stage": stage, "source": source,
            "blocking": blocking, "scoped_out": scoped_out}


# ============================================================================================
# 11. PER-ARM VERIFICATION -- fail-closed, on the artifact, never on a claim
# ============================================================================================
def liveness_records_from_rows(pr: Prereg, arm: ArmSpec,
                               rows: Sequence[Dict[str, Any]],
                               attn_impl: str = "") -> List[Dict[str, Any]]:
    """Build the analyzer's liveness-record shape from the PRODUCER's own fields.

    Every field goes through `LIVENESS_FIELD_MAP`. A field mapped to `None` is left ABSENT rather
    than defaulted to 0: PR-057's C-117 is the record of what a defaulting `.get` does here -- a
    MISSING field becomes a measured zero and a healthy arm gates VOID with a substantive
    scientific verdict. Absent stays absent, and `PR059-D4` reports it.
    """
    out = []
    for r in rows:
        rec: Dict[str, Any] = {"arm_id": arm.arm_id, "scope_id": arm.scope_id,
                               "prompt_id": r.get("prompt_id"),
                               "enabled": (arm.kind != "bridge"),
                               "query_kind": r.get("query_kind") or arm.query_kind,
                               # READ BACK FROM THE LOADED CONFIG, which is where score_behavior
                               # records it (summary.json), not from a per-row echo. A row that
                               # carries its own value wins, so a producer that starts stamping it
                               # per row is not overridden by a run-level one.
                               "attn_implementation": (r.get("attn_implementation")
                                                       or attn_impl)}
        for want, src in LIVENESS_FIELD_MAP.items():
            if src is None:
                continue
            if src in r:
                rec[want] = r[src]
        out.append(rec)
    return out


def verify_arm_artifacts(pr: Prereg, arm: ArmSpec, run_dir: str,
                         expect_rows: int) -> Dict[str, Any]:
    """Everything that must be true of a finished arm, checked on the ARTIFACT."""
    done = os.path.join(run_dir, "DONE.json")
    if not os.path.exists(done):
        raise RunnerRefusal("arm %s: %s has no DONE.json -- a partial run is not a complete one"
                            % (arm.arm_id, run_dir))
    res = os.path.join(run_dir, "results.jsonl")
    if not os.path.exists(res):
        raise RunnerRefusal("arm %s: %s has no results.jsonl" % (arm.arm_id, run_dir))
    rows = []
    with open(res) as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    if not rows:
        raise RunnerRefusal("arm %s produced ZERO rows" % arm.arm_id)
    if len(rows) != int(expect_rows):
        raise RunnerRefusal(
            "arm %s scored %d rows and the runner bound %d. A delta computed across unequal "
            "populations is not a delta (L-N11)." % (arm.arm_id, len(rows), expect_rows))

    summary_path = os.path.join(run_dir, "summary.json")
    summary = json.load(open(summary_path)) if os.path.exists(summary_path) else {}
    # WHICH FIELD CARRIES THE LOADED BACKEND, AND WHY NOT THE OTHER ONE (DCS-TS-P11).
    # This check exists because an attention-mask knockout is a silent no-op under SDPA/flash and
    # would score as a clean null. It read `intervention.attn_implementation` then a top-level
    # `attn_implementation`, and score_behavior wrote NEITHER: the only copy in the artifact lived
    # in `knockout_liveness.attn_implementation`. The absent field became "" and a VALID eager arm
    # was refused as void -- a missing-field-reads-as-a-value bug, the mirror of PR-057's C-117.
    #
    # `knockout_liveness.attn_implementation` is DELIBERATELY NOT a fallback here. Before the
    # producer fix that field held the value score_behavior REQUESTED, not the one the model
    # LOADED, and those are exactly the two things this gate must not confuse. Accepting it would
    # let an arm whose backend silently fell back to SDPA pass on the strength of its own request.
    # score_behavior now stamps the LOADED value at the summary top level for every arm.
    _srcs = [("summary.attn_implementation", summary.get("attn_implementation")),
             ("summary.intervention.attn_implementation",
              ((summary.get("intervention") or {}) if isinstance(summary.get("intervention"), dict)
               else {}).get("attn_implementation"))]
    _found = [(k, str(v)) for k, v in _srcs if v is not None and str(v) != ""]
    impl = _found[0][1] if _found else ""
    want_impl = required_attn_impl(pr)
    if arm.kind != "baseline":
        # ABSENT AND WRONG ARE DIFFERENT FAILURES AND GET DIFFERENT MESSAGES. Both refuse: a
        # backend that cannot be established from the artifact is not evidence that it was eager.
        if not _found:
            raise RunnerRefusal(
                "arm %s: summary.json records NO loaded attn_implementation (looked at %s). The "
                "attention backend cannot be established from this artifact, and an attn_knockout "
                "is a silent no-op under SDPA/flash -- so this arm cannot be read as a null. It "
                "was produced by a score_behavior that predates the loaded-config recording; "
                "re-run the arm." % (arm.arm_id, ", ".join(k for k, _ in _srcs)))
        if impl != want_impl:
            raise RunnerRefusal(
                "arm %s records attn_implementation=%r on the LOADED config (from %s), not %r. "
                "Under SDPA the additive mask edit is DISCARDED and the knockout is a silent "
                "no-op scoring as a CLEAN NULL. This arm is VOID, not a negative."
                % (arm.arm_id, impl, _found[0][0], want_impl))

    recs = liveness_records_from_rows(pr, arm, rows, attn_impl=impl)
    gate: Dict[str, Any] = {"arm_id": arm.arm_id, "run_dir": run_dir, "n_rows": len(rows),
                            "attn_implementation": impl,
                            "output_sha256": hashlib.sha256(
                                open(res, "rb").read()).hexdigest()}

    # `primary.cannot_answer` (c): "a scope's row-set resolver fails on more than 5% of rows, so
    # the arms no longer share a population". `score_behavior` writes its FailureLedger into
    # summary.json, and the declared-offset selector's failures are ledgered under `relend:` /
    # `surfacespan:`. The TOLERANCE is the analyzer's, fetched from the frozen file -- never a
    # literal here.
    fail = (summary.get("failures") or {})
    reasons = dict(fail.get("failure_reasons") or {})
    n_resolver = sum(v for k, v in reasons.items()
                     if str(k).startswith(("relend:", "surfacespan:")))
    n_attempted = int(fail.get("n_attempted") or (len(rows) + n_resolver))
    if n_attempted:
        rg = resolver_failure_gate(n_resolver, n_attempted, pr)
        gate["resolver_failure_gate"] = rg
        if rg["cannot_answer"]:
            raise CannotAnswer(
                "arm %s: the row-set resolver failed on %d of %d rows (%s). The arms no longer "
                "share a population, which the frozen file lists as CANNOT ANSWER, not a null."
                % (arm.arm_id, n_resolver, n_attempted, rg["reason"]))

    if arm.kind == "baseline":
        gate["producer_liveness"] = {"n_prefill_edits": 0, "n_decode_edits": 0,
                                     "note": "untouched baseline; no hook is installed"}
        gate["analyzer_liveness"] = {"skipped": "baseline arm"}
        return gate

    # ---- the PRODUCER's own gate: the fields the knockout hook really writes -----------------
    viol = [v for r in rows for v in (r.get("hook_liveness_violations") or [])]
    prefill = sum(int(r.get("hook_n_prefill_edits") or 0) for r in rows)
    decode = sum(int(r.get("hook_n_decode_edits") or 0) for r in rows)
    zero_dose = sum(1 for r in rows if int(r.get("surface_span_n_tokens") or 0) <= 0)
    gate["producer_liveness"] = {"n_prefill_edits": prefill, "n_decode_edits": decode,
                                 "n_zero_dose_rows": zero_dose,
                                 "n_violations": len(viol), "violations": viol[:5]}
    if viol:
        raise RunnerRefusal("arm %s: the producer's own liveness gate reports %d violation(s): %s"
                            % (arm.arm_id, len(viol), viol[:3]))
    if arm.kind != "bridge":
        if prefill <= 0:
            raise RunnerRefusal(
                "arm %s: n_prefill_edits == %d over %d rows. THE HOOK NEVER FIRED and this arm's "
                "result is VOID, not a null." % (arm.arm_id, prefill, len(rows)))
        if decode != 0:
            raise RunnerRefusal(
                "arm %s: n_decode_edits == %d; this prefill-only family requires EXACTLY 0. A "
                "non-zero value means the scoping LEAKED and the mode is secretly a larger "
                "intervention than the one reported." % (arm.arm_id, decode))
        if zero_dose:
            raise RunnerRefusal(
                "arm %s: %d/%d rows have a REALISED DOSE of 0 tokens -- the surface span resolved "
                "to nothing and the arm cut nothing." % (arm.arm_id, zero_dose, len(rows)))

    # ---- L-N4 and L-N10, through the ANALYZER's own functions --------------------------------
    declared = (producer_random_row_draw(pr, arm.scope_id,
                                         declared_scopes(pr)[arm.scope_id]["rel_end_rows"],
                                         arm.draw_index, query_span_rel_end(pr))["rel_end_rows"]
                if arm.kind == "random_row_control" else list(arm.rel_end_rows))
    r1 = assert_realised_equals_declared(recs, declared)
    gate["realised_equals_declared"] = r1
    if not r1["ok"]:
        raise RunnerRefusal("arm %s: L-N4 -- %s" % (arm.arm_id, r1["reason"]))
    r2 = audit_end_relative(recs, declared)
    gate["end_relative_audit"] = r2
    if not r2["ok"]:
        raise RunnerRefusal("arm %s: L-N10 -- %d violation(s); %s"
                            % (arm.arm_id, r2["n_violations"], r2["witness_note"]))

    # ---- the ANALYZER's liveness gate, RECORDED and NOT used as the launch gate (PR059-D4) ----
    lg = liveness_gate(recs, arm.arm_id, pr, expect_enabled=(arm.kind != "bridge"))
    contract = analyzer_liveness_contract_report()
    gate["analyzer_liveness"] = dict(lg)
    gate["analyzer_liveness"]["evaluable"] = contract["ok"]
    if not contract["ok"]:
        gate["analyzer_liveness"]["not_evaluable_because"] = contract["unmapped"]
        gate["analyzer_liveness"]["defect"] = DEFECT_D4_LIVENESS_SCHEMA
    elif not lg["live"]:
        raise RunnerRefusal("arm %s: the analyzer's liveness gate refuses -- %s"
                            % (arm.arm_id, "; ".join(lg["reasons"])[:300]))
    return gate


# ============================================================================================
# 12. THE PLAN -- constructs and validates EVERY arm, on CPU, with no GPU and no model
# ============================================================================================
def verifier_arm_set() -> Dict[str, Any]:
    """`PR059-D5`. The INDEPENDENT verifier's expected arm set, for the disagreement report.

    Imported lazily and only here. The verifier's own independence checks (`T00a` scans its source
    for an import of the analyzer, `T00b` asserts the analyzer is absent from `sys.modules`) run
    inside the verifier's own `--self-test` process, which is never this one.
    """
    try:
        import dcs_ts_pr059_verifier as VER
        cfg = json.load(open(repo_path(PREREG_DEFAULT)))
        return {"ok": True, "tags": sorted(VER.expected_arms(cfg).keys())}
    except Exception as e:                                  # never let the cross-check kill --plan
        return {"ok": False, "error": repr(e), "tags": []}


def compare_arm_sets(mine: Sequence[str], theirs: Sequence[str]) -> int:
    """PR059-D5's SURVIVING guard, as a PURE comparator so it can be driven with a set that
    really does differ. The two derivations agreeing today is a measurement; a comparator that
    can no longer fire would make it an assumption."""
    only_a = sorted(set(mine) - set(theirs))
    only_v = sorted(set(theirs) - set(mine))
    if only_a or only_v:
        raise RunnerRefusal(
            "%s OBSERVED NOW: only_in_analyzer_manifest=%s only_in_verifier_expectation=%s"
            % (DEFECT_D5_ARM_COUNT, only_a[:6], only_v[:6]))
    return len(set(mine))


def arm_set_disagreement(pr: Prereg) -> Dict[str, Any]:
    v = verifier_arm_set()
    mine = sorted(x.tag() for x in build_arm_manifest(pr))
    if not v["ok"]:
        return {"ok": False, "n_runner": len(mine), "error": v["error"]}
    theirs = set(v["tags"])
    only_runner = sorted(set(mine) - theirs)
    only_verifier = sorted(theirs - set(mine))
    return {"agree": not (only_runner or only_verifier),
            "n_runner": len(mine), "n_verifier": len(theirs),
            "only_in_analyzer_manifest": only_runner,
            "only_in_verifier_expectation": only_verifier,
            "defect": ("" if not (only_runner or only_verifier) else DEFECT_D5_ARM_COUNT)}


def plan(pr: Prereg, a) -> Dict[str, Any]:
    arms = build_arm_manifest(pr)
    part = assert_stages_partition(pr)
    assign = load_split(pr)
    span = query_span_rel_end(pr)
    scopes = declared_scopes(pr)

    binds: Dict[str, Any] = {}
    conds: Dict[str, Any] = {}
    out_arms = []
    sel = stage_selector(pr, a.stage) if a.stage else (lambda x: True)
    for arm in arms:
        con = constructibility(pr, arm)
        rec: Dict[str, Any] = {
            "arm_id": arm.arm_id, "tag": arm.tag(), "bank": arm.bank,
            "scope_id": arm.scope_id, "kind": arm.kind, "draw_index": arm.draw_index,
            "n_rows_declared": len(arm.rel_end_rows), "family_member": arm.family_member,
            "confirmatory": arm.confirmatory, "expect_enabled": arm.expect_enabled,
            "stage": ("kill" if stage_selector(pr, "kill")(arm) else "family"),
            "in_smoke": bool(stage_selector(pr, "smoke")(arm)),
            **con,
        }
        if con["constructible"] and sel(arm):
            bank_abs = repo_path(bank_path_for(pr, arm.bank))
            if arm.bank not in conds:
                conds[arm.bank] = cell_condition_for_bank(pr, bank_abs)
            key = (arm.bank, a.split)
            if key not in binds:
                binds[key] = split_bind(pr, bank_abs, a.split, assign)
            b = binds[key]
            # C-123, the SAME clamp as the run path. `--plan` is what a human READS to decide what
            # to submit, so an unclamped expect_n here would print an argv that refuses when run.
            plan_limit = (a.smoke_limit if (a.stage == "smoke" and rec["in_smoke"]) else 0)
            plan_expect = min(b["expect_n"], plan_limit) if plan_limit else b["expect_n"]
            ctx = {"condition": conds[arm.bank]["condition"], "constructibility": con,
                   "expect_n": plan_expect, "limit": plan_limit,
                   "exclude_file": "<state-dir>/%s" % exclusion_file_name(bank_abs, a.split)}
            argv = build_argv(pr, arm, ctx)
            assert_expect_n_agrees_with_limit(argv)
            rec["argv"] = argv
            rec["expect_n"] = plan_expect
            rec["n_domains"] = b["n_domains"]
            rec["analyzer_agreement"] = assert_argv_agrees_with_analyzer(pr, arm, argv)["ok"]
        out_arms.append(rec)

    n_con = sum(1 for r in out_arms if r["constructible"])
    controls = {}
    for sid, s in scopes.items():
        if not s["rel_end_rows"] or sid == reference_scope_id(pr):
            continue
        controls[sid] = random_row_control_constructible(pr, sid, s["rel_end_rows"], span)
    return {
        "prereg": a.prereg, "amendment": a.amendment or None, "id": pr.require("id"),
        "split": a.split, "stage": a.stage or "(all)",
        "n_arms": len(arms), "stage_partition": part,
        "n_constructible_today": n_con, "n_unbuildable_today": len(arms) - n_con,
        "banks": primary_banks(pr), "cell_condition": conds,
        "family_members": family_member_ids(pr),
        "reference_scope": reference_scope_id(pr), "scaffold_scope": scaffold_scope_id(pr),
        "query_span_rel_end": [min(span), max(span)], "n_query_span_rows": len(span),
        "random_row_control_constructibility": controls,
        "rows_per_arm": {"%s:%s" % (k[1], k[0]): v["expect_n"] for k, v in binds.items()},
        "analyzer_liveness_contract": analyzer_liveness_contract_report(),
        "arm_set_disagreement": arm_set_disagreement(pr),
        "defects": ALL_DEFECTS,
        "arms": out_arms,
    }


# ============================================================================================
# 13. EXECUTION
# ============================================================================================
def run_stage(pr: Prereg, a) -> int:
    runs_root = a.runs if os.path.isabs(a.runs) else repo_path(a.runs)
    state_root = a.state_root if os.path.isabs(a.state_root) else repo_path(a.state_root)
    sdir = stage_dir(state_root, a.stage, a.split)
    t_stage = time.time()
    assign = load_split(pr)
    assert_stages_partition(pr)

    # A REAL RUN RAISES AT THE FIRST GATE. A --dry-run COLLECTS THEM ALL and exits non-zero: a dry
    # run whose whole job is to tell you what is wrong should not stop at the first thing, and it
    # cannot spend GPU time by continuing.
    blocking: List[str] = []

    def _gate(fn, label):
        try:
            return fn()
        except (RunnerRefusal, PreregError, Refusal, ZeroBinding, CannotAnswer) as e:
            if not a.dry_run:
                raise
            blocking.append("%s: %s" % (label, str(e).splitlines()[0][:400]))
            return None

    ctx_stage = {"split": a.split, "limit": (a.smoke_limit if a.stage == "smoke" else 0)}

    def _checklist():
        # EVERY STAGE, including the smoke. A gate that is skipped for the one stage anybody
        # actually runs is the "threshold published but never enforced" failure. It is STAGE-AWARE
        # and strictly stronger than the loader's: an item with no declared stage scope, or whose
        # scope this runner cannot re-derive from the arm manifest and the run's own binding,
        # still blocks every stage.
        g = checklist_gate(a.prereg, a.amendment or "", a.stage, ctx_stage)
        for s in g["scoped_out"]:
            print("[pr059] checklist %s: SCOPED OUT of stage %r -- %s"
                  % (s["id"], a.stage, s["why"]), flush=True)
        if not g["ok"]:
            for r in g["blocking"]:
                print("[pr059] CHECKLIST BLOCKS %s: %s" % (a.stage, r), flush=True)
            raise RunnerRefusal(
                "the confirmatory stage %r requires the BLOCKING pre-extraction checklist to "
                "close, and it does not (%d item(s), each printed above): %s"
                % (a.stage, len(g["blocking"]),
                   "; ".join(r.split(" [")[0] for r in g["blocking"])))
        return True

    _gate(lambda: assert_stage_order(state_root, a.stage, a.split), "launch order")
    _gate(_checklist, "pre-extraction checklist")
    if a.stage == "smoke" and a.split != "train":
        raise RunnerRefusal(
            "the U8 smoke runs on a handful of TRAIN domains by preregistration ('smoke run S_G "
            "and S_C on a handful of TRAIN domains'); got --split %r" % a.split)

    arms_all = build_arm_manifest(pr)
    sel = stage_selector(pr, a.stage)
    selected = [x for x in arms_all if sel(x)]
    if not selected:
        raise ZeroBinding("stage %r selected ZERO arms of %d" % (a.stage, len(arms_all)))

    # A DRY RUN WRITES NOTHING. It constructs and validates every arm on CPU -- the exclusion
    # files are computed and hashed, not written -- so the whole path is testable without a GPU
    # and without leaving artifacts a later reader could mistake for a run.
    if not a.dry_run:
        os.makedirs(sdir, exist_ok=True)
        # C-124: refuse a stage that ALREADY carries a verdict BEFORE any arm runs, not after.
        # Skipped on --dry-run, which writes nothing and is exactly how an operator inspects a
        # stage whose prior verdict they are still deciding what to do about.
        assert_stage_has_no_prior_verdict(sdir)
    man = manifest_load(sdir) if not a.dry_run else {}
    man.setdefault("started", time.strftime("%Y-%m-%d %H:%M:%S"))
    man.update({"stage": a.stage, "split": a.split, "prereg": a.prereg,
                "amendment": a.amendment or None, "prereg_id": pr.require("id"),
                "provenance": slurm_provenance(), "runs_root": runs_root,
                "analyzer_liveness_contract": analyzer_liveness_contract_report(),
                "arm_set_disagreement": arm_set_disagreement(pr)})
    man.setdefault("arms", {})

    todo: List[Tuple[ArmSpec, List[str], int]] = []
    unbuildable: List[Dict[str, Any]] = []
    binds: Dict[str, Any] = {}
    conds: Dict[str, Any] = {}
    for arm in selected:
        con = constructibility(pr, arm)
        if not con["constructible"]:
            unbuildable.append({"arm_id": arm.arm_id, "reasons": con["reasons"]})
            man["arms"].setdefault(arm.arm_id, {}).update(
                {"status": "UNBUILDABLE", "reasons": con["reasons"]})
            continue
        bank_abs = repo_path(bank_path_for(pr, arm.bank))
        if arm.bank not in conds:
            conds[arm.bank] = cell_condition_for_bank(pr, bank_abs)
        if arm.bank not in binds:
            b = split_bind(pr, bank_abs, a.split, assign)
            xf = os.path.join(sdir, exclusion_file_name(bank_abs, a.split))
            text = exclusion_file_text(pr, b)
            if not a.dry_run:
                with open(xf, "w") as fh:
                    fh.write(text)
            b["exclude_file"] = xf
            b["exclude_file_sha16"] = hashlib.sha256(text.encode()).hexdigest()[:16]
            binds[arm.bank] = b
        b = binds[arm.bank]
        # C-123 (PHASE 9's job 868569). CLAMP ONCE, above the ctx, and use the SAME number for the
        # argv and for the runner's own expectation. Two variables that must agree are a standing
        # invitation for exactly that defect.
        expect_rows = min(b["expect_n"], a.smoke_limit) if a.stage == "smoke" else b["expect_n"]
        ctx = {"condition": conds[arm.bank]["condition"], "constructibility": con,
               "expect_n": expect_rows, "exclude_file": b["exclude_file"],
               "limit": (a.smoke_limit if a.stage == "smoke" else 0)}
        argv = build_argv(pr, arm, ctx)
        assert_argv_agrees_with_analyzer(pr, arm, argv)
        assert_expect_n_agrees_with_limit(argv)
        todo.append((arm, argv, expect_rows))

    print("[pr059] stage=%s split=%s: %d selected, %d constructible, %d unbuildable"
          % (a.stage, a.split, len(selected), len(todo), len(unbuildable)), flush=True)
    for u in unbuildable:
        print("[pr059]   UNBUILDABLE %s: %s" % (u["arm_id"], u["reasons"][0][:180]), flush=True)
    if not todo:
        raise RunnerRefusal(
            "stage %r has ZERO constructible arms (%d were selected). Refusing to write a "
            "DONE.json for a stage that ran nothing -- an empty stage that reports success is the "
            "failure this whole design exists to prevent." % (a.stage, len(selected)))

    if a.dry_run:
        for arm, argv, _n in todo:
            print("[pr059] DRY-RUN %-44s %s" % (arm.arm_id, " ".join(argv)))
        print("[pr059] DRY-RUN: %d arm(s) constructed and validated, model NOT loaded, nothing "
              "written, nothing run." % len(todo))
        for bl in blocking:
            print("[pr059] BLOCKING %s" % bl, file=sys.stderr)
        if blocking:
            print("[pr059] DRY-RUN: %d BLOCKING gate(s) above. This stage may NOT be submitted."
                  % len(blocking), file=sys.stderr)
            return 3
        return 0

    # ---- the loop. ONE model load. ----------------------------------------------------------
    cache = ModelCache().install()
    import score_behavior as SB
    n_rows_total, n_done = 0, 0
    try:
        for i, (arm, argv, expect_rows) in enumerate(todo, 1):
            rec = man["arms"].setdefault(arm.arm_id, {})
            if rec.get("status") == "done":
                print("[pr059] [%d/%d] %s already complete at %s -- SKIPPING (resume)"
                      % (i, len(todo), arm.arm_id, rec.get("run_dir")), flush=True)
                n_rows_total += int(rec.get("rows") or 0)
                n_done += 1
                continue
            rec.update({"status": "running", "argv": argv, "tag": arm.tag(),
                        "expect_rows": expect_rows})
            manifest_save(sdir, man)
            print("\n[pr059] === [%d/%d] %s ===\n[pr059]     %s"
                  % (i, len(todo), arm.arm_id, " ".join(argv)), flush=True)
            t0 = time.time()
            old_argv = sys.argv
            sys.argv = [SCORE_SCRIPT] + list(argv)
            try:
                rc = SB.main()
            except SystemExit as e:                     # the house refusal idiom
                rc = e.code if isinstance(e.code, int) else 1
                if rc == 0:
                    rc = 1
                print("[pr059] arm %s REFUSED: %s" % (arm.arm_id, e), file=sys.stderr, flush=True)
            finally:
                sys.argv = old_argv
            wall = time.time() - t0
            if rc != 0:
                rec.update({"status": "failed", "exit_code": rc, "wall_seconds": wall})
                manifest_save(sdir, man)
                write_terminal(sdir, "ABORTED.json",
                               {"status": "aborted", "stage": a.stage, "split": a.split,
                                "failed_arm": arm.arm_id, "exit_code": rc,
                                "n_arms_done": n_done, "n_arms_total": len(todo),
                                "rows": n_rows_total, "wall_seconds": time.time() - t_stage,
                                "model_loads": cache.n_loads,
                                "detail": "STOPPED at the first failure; the remaining arms were "
                                          "NOT run and no success is reported for them."})
                raise RunnerRefusal(
                    "arm %s exited %d. STOPPING: this runner never continues past a failure and "
                    "never reports success it did not observe." % (arm.arm_id, rc))
            run_dir = _find_run(runs_root, arm.tag())
            gate = verify_arm_artifacts(pr, arm, run_dir, expect_rows)
            with open(os.path.join(run_dir, ARM_GATE_FILE), "w") as fh:
                json.dump({**gate, "provenance": slurm_provenance(),
                           "argv": argv, "prereg": a.prereg,
                           "amendment": a.amendment or None,
                           "has_no_dose_matched_control":
                               constructibility(pr, arm)["has_no_dose_matched_control"],
                           "defects_recorded": ALL_DEFECTS}, fh, indent=2, default=str)
            rec.update({"status": "done", "run_dir": run_dir, "rows": gate["n_rows"],
                        "output_sha256": gate["output_sha256"], "wall_seconds": wall,
                        "exit_code": 0})
            manifest_save(sdir, man)
            n_rows_total += gate["n_rows"]
            n_done += 1
            print("[pr059] [%d/%d] %s OK: %d rows, %.1f min"
                  % (i, len(todo), arm.arm_id, gate["n_rows"], wall / 60.0), flush=True)
            try:
                import torch
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
            except Exception:
                pass
    finally:
        cache.uninstall()

    # ---- L-N7: the random-row control bands, THREE DISTINCT OUTPUT HASHES --------------------
    # This project has TWICE published a control band that was secretly n=1 because the seed never
    # reached the draw. The gate is the ANALYZER's `control_band_gate`; the hashes are this
    # runner's per-arm output hashes. It runs at the END of the stage, so a band that is secretly
    # n=1 fails before anyone computes an interval from it.
    bands: Dict[str, List[str]] = {}
    for arm in selected:
        if arm.kind != "random_row_control":
            continue
        r = man["arms"].get(arm.arm_id) or {}
        if r.get("status") == "done" and r.get("output_sha256"):
            bands.setdefault("%s/%s" % (arm.bank, arm.scope_id), []).append(r["output_sha256"])
    n_draws = int(n_random_row_draws(pr))
    band_report = {}
    for key, shas in sorted(bands.items()):
        if len(shas) < n_draws:
            continue
        g = control_band_gate(shas, n_draws)
        band_report[key] = g
        if not g["ok"]:
            raise RunnerRefusal("control band %s: %s" % (key, g["reason"]))
    if band_report:
        print("[pr059] control band(s) verified distinct: %s"
              % {k: v["n_distinct"] for k, v in band_report.items()}, flush=True)

    done = {"status": "ok", "stage": a.stage, "split": a.split,
            "n_arms_selected": len(selected), "n_arms_done": n_done,
            "n_arms_unbuildable": len(unbuildable), "unbuildable": unbuildable,
            "rows": n_rows_total, "wall_seconds": time.time() - t_stage,
            "model_loads": cache.n_loads, "model_cache_hits": cache.n_hits,
            "control_bands": band_report,
            "analyzer_liveness_contract": analyzer_liveness_contract_report(),
            "arm_set_disagreement": arm_set_disagreement(pr),
            "defects_recorded": ALL_DEFECTS}
    write_terminal(sdir, "DONE.json", done)
    manifest_save(sdir, man)
    print("[pr059] stage %s COMPLETE: %d arm(s), %d rows, %.1f min, %d model load(s)"
          % (a.stage, n_done, n_rows_total, (time.time() - t_stage) / 60.0, cache.n_loads))
    return 0


# ============================================================================================
# 14. SELF-TEST -- CPU only, on the real functions
# ============================================================================================
class _Checks:
    def __init__(self):
        self.n = 0
        self.n_fail = 0

    def add(self, name: str, ok: bool, detail: str = "") -> None:
        self.n += 1
        if not ok:
            self.n_fail += 1
        print("  %-5s %-58s %s" % ("PASS" if ok else "FAIL", name, detail[:90]))


def _args(**kw):
    class A:
        pass
    a = A()
    d = dict(prereg=PREREG_DEFAULT, amendment="", stage="", split="train",
             runs=RUNS_ROOT_DEFAULT, state_root=STATE_ROOT_DEFAULT, smoke_limit=40,
             dry_run=False, plan=False, out="")
    d.update(kw)
    for k, v in d.items():
        setattr(a, k, v)
    return a


def _arm_by(arms, **kw) -> ArmSpec:
    for x in arms:
        if all(getattr(x, k) == v for k, v in kw.items()):
            return x
    raise AssertionError("no arm matching %s" % kw)


def selftest() -> int:
    print("=== DCS-PR-059 runner self-test (CPU only, nothing written, no model) ===")
    ck = _Checks()
    pr = load_prereg(PREREG_DEFAULT, for_extraction=False)
    arms = build_arm_manifest(pr)
    scopes = declared_scopes(pr)
    span = query_span_rel_end(pr)

    # ---- the manifest is the ANALYZER's, not a copy -------------------------------------
    ck.add("manifest is imported from the analyzer",
           build_arm_manifest.__module__ == "dcs_ts_pr059_localisation",
           build_arm_manifest.__module__)
    ck.add("liveness_gate / audit_end_relative / bind_rows are the analyzer's",
           {liveness_gate.__module__, audit_end_relative.__module__, bind_rows.__module__}
           == {"dcs_ts_pr059_localisation"}, "")
    # PR059-D5, RESOLVED: 78 -> 84. The reference scope S_G now carries the nondemo-key control
    # the frozen file requires "for every scope" (+6; its random-row control really is
    # unbuildable and it still has none), and the independent verifier now knows about the
    # disabled-hook bridge arm that BLOCKING null L-N1 requires (+2 on its side). Both
    # derivations land on 84, tag for tag.
    ck.add("the manifest has 84 arms over 2 confirmatory banks (PR059-D5 reconciled)",
           len(arms) == 84 and len({x.bank for x in arms}) == 2, "n=%d" % len(arms))
    part = assert_stages_partition(pr)
    ck.add("kill and family PARTITION the manifest",
           part["n_kill"] + part["n_family"] == part["n_arms"], json.dumps(part))
    ck.add("the smoke selects the baseline, the reference scope and S_C only",
           sorted({x.scope_id for x in arms if stage_selector(pr, "smoke")(x)})
           == sorted({"S_0", reference_scope_id(pr), "S_C"}), "")

    # ---- PR059-D1, the arithmetic -------------------------------------------------------
    imposs = sorted(sid for sid, s in scopes.items()
                    if s["rel_end_rows"] and sid != reference_scope_id(pr)
                    and not random_row_control_constructible(
                        pr, sid, s["rel_end_rows"], span)["constructible"])
    ck.add("PR059-D1: exactly S_D and S_E have no constructible control among family scopes",
           imposs == ["S_D", "S_E"], str(imposs))
    ck.add("PR059-D1: the reference scope S_G has a pool of 0",
           len([r for r in span if r not in set(scopes["S_G"]["rel_end_rows"])]) == 0, "")
    ck.add("PR059-D1: the control exists exactly where 28-m >= m",
           all((len(span) - len(scopes[s]["rel_end_rows"]) >= len(scopes[s]["rel_end_rows"]))
               == random_row_control_constructible(
                   pr, s, scopes[s]["rel_end_rows"], span)["constructible"]
               for s in ("S_A", "S_C", "S_D", "S_E", "S_F", "S_F2")), "")

    # ---- the producer and the analyzer draw the SAME control rows -----------------------
    same = True
    for sid in ("S_A", "S_C", "S_F", "S_F2"):
        for d in range(n_random_row_draws(pr)):
            w = sorted(random_row_control_draw(pr, sid, scopes[sid]["rel_end_rows"], d,
                                               span)["rel_end_rows"])
            g = sorted(producer_random_row_draw(pr, sid, scopes[sid]["rel_end_rows"], d,
                                                span)["rel_end_rows"])
            same = same and (w == g)
    ck.add("the analyzer's and score_behavior's random-row draws are IDENTICAL", same, "")
    ck.add("score_behavior REFUSES the impossible draw by name",
           _refuses(lambda: producer_random_row_draw(pr, "S_E", scopes["S_E"]["rel_end_rows"],
                                                     0, span), "PR059-D1"), "")

    # ---- the selectors agree, END-RELATIVE, per prompt ----------------------------------
    import score_behavior as SB
    ok = True
    for sid in ("S_A", "S_C", "S_D", "S_E", "S_F", "S_F2", "S_G"):
        rows = scopes[sid]["rel_end_rows"]
        for n in (60, 137, 400, 1024):
            qs = list(range(max(0, n - len(span)), n))
            a1 = sorted(AN.surface_span_from_rel_end(rows, n, qs))
            a2 = sorted(SB.surface_span_from_rel_end(rows, n, qs))
            ok = ok and a1 == a2 and a1 == sorted(n + r for r in rows)
    ck.add("producer and analyzer selectors agree at seq_len 60/137/400/1024, 0 mismatches",
           ok, "")
    ck.add("an ABSOLUTE (non-negative) offset is refused at argv build time",
           _refuses(lambda: rel_end_arg([9]), "ABSOLUTE INDEX REFUSED"), "")

    # ---- the nondemo translation --------------------------------------------------------
    ck.add("the analyzer's 0-based nondemo draw maps to the producer's 1-based arm name",
           [nondemo_arm_name(i) for i in range(n_nondemo_draws(pr))]
           == ["nondemo_matched_d1", "nondemo_matched_d2", "nondemo_matched_d3"], "")
    ck.add("every nondemo arm name exists in score_behavior.NONDEMO_DRAW_ARMS",
           all(nondemo_arm_name(i) in SB.NONDEMO_DRAW_ARMS
               for i in range(n_nondemo_draws(pr))), "")

    # ---- A-039, the cell/condition mapping ----------------------------------------------
    cc = cell_condition_for_bank(pr, repo_path(bank_path_for(pr, "button_bomb")))
    ck.add("A-039: cell C and its condition bind the SAME rows on button_bomb",
           cc["mapping_is_1to1"] and cc["n_rows"] == 1160,
           "cell=%s condition=%s n=%d" % (cc["cell"], cc["condition"], cc["n_rows"]))

    # ---- the split binding ---------------------------------------------------------------
    assign = load_split(pr)
    b = split_bind(pr, repo_path(bank_path_for(pr, "button_bomb")), "train", assign)
    ck.add("the TRAIN split binds 67 ANALYSED domains x 10 rows (70 assigned - 3 excluded)",
           b["n_domains"] == 67 and b["expect_n"] == 670,
           "domains=%d rows=%d" % (b["n_domains"], b["expect_n"]))
    bt = split_bind(pr, repo_path(bank_path_for(pr, "button_bomb")), "test", assign)
    ck.add("the TEST split binds 23 domains x 10 rows",
           bt["n_domains"] == 23 and bt["expect_n"] == 230, "rows=%d" % bt["expect_n"])
    ck.add("the exclusion file names its source manifest and its sha",
           pr.require("split", "manifest_sha16") in exclusion_file_text(pr, b), "")

    # ---- C-123 --------------------------------------------------------------------------
    ck.add("C-123: --expect-n 670 beside --limit 40 REFUSES",
           _refuses(lambda: assert_expect_n_agrees_with_limit(
               ["--expect-n", "670", "--limit", "40"]), "C-123"), "")
    ck.add("C-123: --limit larger than --expect-n also REFUSES",
           _refuses(lambda: assert_expect_n_agrees_with_limit(
               ["--expect-n", "40", "--limit", "670"]), "C-123"), "")
    ck.add("C-123: equal values pass, and an absent --limit is not an error",
           _no_raise(lambda: assert_expect_n_agrees_with_limit(
               ["--expect-n", "40", "--limit", "40"]))
           and _no_raise(lambda: assert_expect_n_agrees_with_limit(["--expect-n", "670"])), "")

    # ---- the argv, end to end -------------------------------------------------------------
    a = _args(stage="smoke", split="train")
    p = plan(pr, a)
    smoke = [r for r in p["arms"] if r.get("in_smoke") and r.get("argv")]
    ck.add("the smoke plan builds 6 arms (baseline + S_G + S_C on both banks)",
           len(smoke) == 6, "n=%d" % len(smoke))
    ck.add("every smoke argv carries --expect-n == --limit == the smoke limit",
           all(r["expect_n"] == a.smoke_limit for r in smoke), "")
    ck.add("every planned argv AGREES with the analyzer's launch_command",
           all(r.get("analyzer_agreement") for r in smoke), "")
    sc = [r for r in smoke if r["scope_id"] == "S_C"][0]
    ck.add("the S_C argv passes the rel_end row set with '=' and names its scope id",
           "--knockout-rel-end-rows=-10" in sc["argv"]
           and "--knockout-scope-id" in sc["argv"], " ".join(sc["argv"])[:80])
    ck.add("the S_C argv forces eager attention",
           sc["argv"][sc["argv"].index("--attn-impl") + 1] == required_attn_impl(pr), "")
    ck.add("no argv token contains a space or a quote (BOOMB_ARGS is word-split)",
           all(" " not in t and "'" not in t and '"' not in t
               for r in smoke for t in r["argv"]), "")

    # ---- constructibility refusals ---------------------------------------------------------
    bridge = _arm_by(arms, kind="bridge")
    _bfc = bridge_family_constructible()
    ck.add("PR059-D6 RESOLVED: the disabled-hook bridge IS constructible for the knockout family",
           _bfc[0] and constructibility(pr, bridge)["constructible"], _bfc[1])
    ck.add("PR059-D6: and the guard survives -- it re-derives the family from pair_common's own "
           "dispatch, so removing the branch refuses the arm by name again",
           "BRIDGE_FAMILIES" in inspect.getsource(bridge_family_constructible), "")
    ck.add("PR059-D6 second half: score_behavior ROUTES the knockout hooks through the bridge",
           "routing" in _bfc[1], _bfc[1])
    ck.add("PR059-D6 is a MEASURED property of pair_common, not an assertion",
           _refuses(lambda: _bridge_probe(), "cannot bridge"), "")
    sd = _arm_by(arms, scope_id="S_D", kind="scope")
    ck.add("PR059-D1: the S_D scope arm is RUNNABLE and is flagged as having no control",
           constructibility(pr, sd)["constructible"]
           and constructibility(pr, sd)["has_no_dose_matched_control"], "")
    ck.add("the manifest builds NO random-row control arm for S_D/S_E/S_G",
           not [x for x in arms if x.kind == "random_row_control"
                and x.scope_id in ("S_D", "S_E", "S_G")], "")
    ck.add("assert_scope_has_its_control REFUSES to render S_D without one",
           _refuses(lambda: assert_scope_has_its_control("S_D", None), "S_D"), "")

    ck.add("a clean run passes the arm gate end to end (the gates are not over-eager)",
           _no_raise(lambda: _fake_arm_gate(pr, arms, n_rows=40, expect=40)), "")
    # DCS-TS-P11: both accepted sources of the LOADED backend must let a valid eager arm through.
    # The regression this replaces was a refusal of a GOOD arm, so a mutation alone cannot cover
    # it -- only a positive check can.
    ck.add("an eager arm recorded at the summary TOP LEVEL passes the arm gate",
           _no_raise(lambda: _fake_arm_gate(pr, arms, impl_field="summary", stamp_rows=False)),
           "summary.attn_implementation")
    ck.add("an eager arm recorded in the INTERVENTION block passes the arm gate",
           _no_raise(lambda: _fake_arm_gate(pr, arms, impl_field="intervention",
                                            stamp_rows=False)),
           "summary.intervention.attn_implementation")
    ck.add("CANNOT ANSWER when the row-set resolver fails on more than the declared tolerance",
           _refuses(lambda: _fake_arm_gate(pr, arms, n_rows=40, expect=40,
                                           n_resolver_failed=9), "CANNOT ANSWER"),
           "tolerance=%g" % AN.resolver_failure_tolerance(pr))

    # ---- PR059-D4 and PR059-D5 --------------------------------------------------------------
    lc = analyzer_liveness_contract_report()
    ck.add("PR059-D4 RESOLVED: every analyzer-liveness field now HAS a producer source",
           lc["ok"] and not lc["unmapped"]
           and {"hook_fired_count", "n_cells_edited_expected",
                "n_cells_edited_realised"} <= set(lc["mapped"]),
           str(sorted(lc["mapped"])))
    # THE RUNNER STILL INVENTS NOTHING. The map having a source does not mean a row HAS the
    # field; a row that lacks it leaves the record without it, and the analyzer RAISES rather
    # than reading the absence as a measured zero. Both halves are checked.
    _thin = liveness_records_from_rows(
        pr, _arm_by(arms, scope_id="S_C", kind="scope"),
        [{"prompt_id": "p", "seq_len": 100, "surface_span_positions": [90],
          "hook_n_prefill_edits": 1}])[0]
    ck.add("PR059-D4: a field the ROW does not carry is still left ABSENT, never defaulted to 0",
           all(k not in _thin for k in ("hook_fired_count", "n_cells_edited_expected",
                                        "n_cells_edited_realised")), str(sorted(_thin)))
    ck.add("PR059-D4: and the analyzer's gate RAISES on that absence rather than reading it as "
           "a measured zero",
           _refuses(lambda: liveness_gate([_thin], "u", pr), "MISSING"), "")
    dis = arm_set_disagreement(pr)
    ck.add("PR059-D5 RESOLVED: the analyzer manifest and the INDEPENDENT verifier now AGREE",
           dis.get("agree") is True and dis["n_runner"] == dis["n_verifier"] == 84,
           "runner=%s verifier=%s" % (dis.get("n_runner"), dis.get("n_verifier")))
    ck.add("PR059-D5: neither set carries an arm the other does not -- tag for tag",
           not dis["only_in_analyzer_manifest"] and not dis["only_in_verifier_expectation"],
           "only_analyzer=%s only_verifier=%s" % (dis["only_in_analyzer_manifest"],
                                                  dis["only_in_verifier_expectation"]))
    ck.add("PR059-D5: the reference scope S_G carries its nondemo-key control on BOTH banks",
           len([x for x in arms if x.scope_id == "S_G"
                and x.kind == "nondemo_control"]) == 2 * n_nondemo_draws(pr),
           "n=%d" % len([x for x in arms if x.scope_id == "S_G"
                         and x.kind == "nondemo_control"]))
    ck.add("PR059-D5: and it still gets NO random-row control, because that one cannot be built",
           not [x for x in arms if x.scope_id == "S_G" and x.kind == "random_row_control"], "")

    # ---- terminal records, C-124 and A15 ----------------------------------------------------
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        write_terminal(td, "DONE.json", {"status": "ok"})
        blob = json.load(open(os.path.join(td, "DONE.json")))
        ck.add("A15: every terminal record carries the job id, nodelist and host",
               set(blob["provenance"]) >= {"slurm_job_id", "slurm_nodelist", "hostname"}, "")
        ck.add("DONE.json and ABORTED.json can never both exist",
               _refuses(lambda: write_terminal(td, "ABORTED.json", {"status": "aborted"}),
                        "ONE verdict"), "")
        ck.add("C-124: a stage that already carries a verdict REFUSES before any arm runs",
               _refuses(lambda: assert_stage_has_no_prior_verdict(td), "C-124") or
               _refuses(lambda: assert_stage_has_no_prior_verdict(td), "ALREADY carries"), "")
    with tempfile.TemporaryDirectory() as td:
        ck.add("C-124: a clean stage dir does NOT refuse",
               _no_raise(lambda: assert_stage_has_no_prior_verdict(td)), "")
        man = {"arms": {"x": {"status": "done", "run_dir": os.path.join(td, "nope")}}}
        os.makedirs(td, exist_ok=True)
        json.dump(man, open(os.path.join(td, MANIFEST_FILE), "w"))
        ck.add("a manifest arm claiming done with no DONE.json is reset to pending",
               manifest_load(td)["arms"]["x"]["status"] == "pending", "")

    # ---- the launch order -------------------------------------------------------------------
    with tempfile.TemporaryDirectory() as td:
        ck.add("the family stage refuses before the kill stage has a DONE.json",
               _refuses(lambda: assert_stage_order(td, "family", "test"), "kill"), "")
        os.makedirs(os.path.join(td, "smoke_train"))
        json.dump({"status": "ok"}, open(os.path.join(td, "smoke_train", "DONE.json"), "w"))
        os.makedirs(os.path.join(td, "kill_test"))
        json.dump({"status": "ok"}, open(os.path.join(td, "kill_test", "DONE.json"), "w"))
        ck.add("with smoke and kill complete, the family stage's order gate passes",
               _no_raise(lambda: assert_stage_order(td, "family", "test")), "")
        ck.add("the smoke stage has no predecessor and always passes the order gate",
               _no_raise(lambda: assert_stage_order(td, "smoke", "train")), "")

    # ---- the checklist gate ------------------------------------------------------------------
    amd = repo_path(AMENDMENT_DEFAULT)
    if os.path.exists(amd):
        g = checklist_gate(PREREG_DEFAULT, AMENDMENT_DEFAULT, "family",
                           {"split": "test", "limit": 0})
        ck.add("the amendment loads and the FAMILY stage is still BLOCKED, with reasons",
               not g["ok"] and g["blocking"], "%d blocking" % len(g["blocking"]))
        gs = checklist_gate(PREREG_DEFAULT, AMENDMENT_DEFAULT, "smoke",
                            {"split": "train", "limit": 40})
        ck.add("the SMOKE stage passes the stage-aware checklist gate", gs["ok"],
               "; ".join(gs["blocking"])[:80])
        ck.add("the smoke's binding scopes every open blocker OUT (re-derived, not by stage name)",
               {x["id"] for x in gs["scoped_out"]}
               >= {"V3", "V8", "V10", "V11", "V12", "V13", "artifacts.analyzer_exists"},
               str(sorted(x["id"] for x in gs["scoped_out"])))
        gk = checklist_gate(PREREG_DEFAULT, AMENDMENT_DEFAULT, "kill",
                            {"split": "test", "limit": 0})
        ck.add("the KILL stage on the full TEST population is BLOCKED by V3/V8/V10/V12/V13",
               not gk["ok"] and all(any(i in b for b in gk["blocking"])
                                    for i in ("V3", "V8", "V10", "V12", "V13")),
               "%d blocking" % len(gk["blocking"]))
        ck.add("an amendment pinned to the wrong parent sha REFUSES",
               _refuses(lambda: _amendment_wrong_sha(pr), "amends nothing"), "")
    else:
        ck.add("the amendment file exists", False, amd)

    print("\n[self-test] %d checks, %d failed" % (ck.n, ck.n_fail))
    return 1 if ck.n_fail else 0


def _refuses(fn, needle: str) -> bool:
    try:
        fn()
    except Exception as e:                                   # noqa: BLE001 -- any refusal counts
        return needle.lower() in str(e).lower()
    return False


def _no_raise(fn) -> bool:
    try:
        fn()
        return True
    except Exception:                                        # noqa: BLE001
        return False


def _bridge_probe():
    import pair_common as pc

    class Stub:
        def __init__(self):
            self.layers = [1, 2]
            self._handles = []
    pc.DisabledHookBridge(Stub())


def _amendment_wrong_sha(pr: Prereg):
    import tempfile
    obj = json.load(open(repo_path(AMENDMENT_DEFAULT)))
    obj["amendment"]["amends_file_sha16"] = "0" * 16
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fh:
        json.dump(obj, fh)
        p = fh.name
    try:
        load_amendment(p, pr)          # an ABSOLUTE path, outside the repo: a mutation must not
    finally:                           # leave a stray config behind in a shared working tree
        os.unlink(p)


# ============================================================================================
# 15. MUTATION HARNESS -- every refusal must be REACHABLE
# ============================================================================================
def mutate() -> int:
    print("=== DCS-PR-059 runner mutations: each must produce a REFUSAL ===")
    pr = load_prereg(PREREG_DEFAULT, for_extraction=False)
    arms = build_arm_manifest(pr)
    scopes = declared_scopes(pr)
    span = query_span_rel_end(pr)
    assign = load_split(pr)
    import tempfile

    muts: List[Tuple[str, Any, str]] = []

    # ---- the C-123 class: --expect-n and --limit contradicting each other -------------------
    muts.append(("M01 C-123: --expect-n survives the smoke clamp (the observed defect)",
                 lambda: assert_expect_n_agrees_with_limit(
                     ["--expect-n", "670", "--limit", "40"]), "C-123"))
    muts.append(("M02 C-123: --limit widens the population past --expect-n",
                 lambda: assert_expect_n_agrees_with_limit(
                     ["--expect-n", "40", "--limit", "670"]), "C-123"))
    muts.append(("M03 C-123 end to end: an argv built with an unclamped expect_n",
                 lambda: _argv_with(pr, arms, expect_n=670, limit=40), "C-123"))

    # ---- the C-124 class: a stage that already carries a terminal verdict --------------------
    def _prior(name):
        td = tempfile.mkdtemp()
        json.dump({"status": "aborted", "failed_arm": "x", "n_arms_done": 0},
                  open(os.path.join(td, name), "w"))
        assert_stage_has_no_prior_verdict(td)
    muts.append(("M04 C-124: a stale ABORTED.json from a run that completed nothing",
                 lambda: _prior("ABORTED.json"), "ALREADY carries"))
    muts.append(("M05 C-124: a stale DONE.json", lambda: _prior("DONE.json"), "ALREADY carries"))

    def _both():
        td = tempfile.mkdtemp()
        write_terminal(td, "DONE.json", {"status": "ok"})
        write_terminal(td, "ABORTED.json", {"status": "aborted"})
    muts.append(("M06 C-124: DONE.json and ABORTED.json in one stage dir", _both, "ONE verdict"))

    # ---- anti-drift: the runner and the analyzer describing different arms --------------------
    muts.append(("M07 argv naming a different bank from the analyzer's",
                 lambda: _drifted(pr, arms, "--bank", "data/nope.jsonl"), "DISAGREES"))
    muts.append(("M08 argv naming a different layer band",
                 lambda: _drifted(pr, arms, "--intervene", "demo_all:attn_knockout:0-31:1.0"),
                 "DISAGREES"))
    muts.append(("M09 argv cutting a different row set than the scope declares",
                 lambda: _drifted(pr, arms, "--knockout-rel-end-rows=-10",
                                  "--knockout-rel-end-rows=-9"), "DISAGREES"))
    muts.append(("M10 argv demoting the scoped knockout to another scope",
                 lambda: _drifted(pr, arms, "--knockout-scope", "legacy_all_query"), "DISAGREES"))
    muts.append(("M11 a nondemo control launched under the LIVE arm name",
                 lambda: _drifted_nondemo(pr, arms), "DISAGREES"))

    # ---- the row set itself --------------------------------------------------------------------
    muts.append(("M12 an ABSOLUTE index in the declared row set",
                 lambda: rel_end_arg([9, -10]), "ABSOLUTE INDEX REFUSED"))
    muts.append(("M13 an EMPTY scope (S_B's shape) launched as an arm",
                 lambda: rel_end_arg([]), "empty"))
    muts.append(("M14 PR059-D1: a dose-matched control asked for S_E",
                 lambda: producer_random_row_draw(pr, "S_E", scopes["S_E"]["rel_end_rows"],
                                                  0, span), "PR059-D1"))
    muts.append(("M15 PR059-D1: a dose-matched control asked for the reference scope S_G",
                 lambda: producer_random_row_draw(pr, "S_G", scopes["S_G"]["rel_end_rows"],
                                                  0, span), "PR059-D1"))
    muts.append(("M16 a scope rendered with NO dose-matched control",
                 lambda: assert_scope_has_its_control("S_E", None), "S_E"))
    # PR059-D6 is RESOLVED, so the bridge ARM is no longer the refusal. What must stay reachable
    # is the refusal underneath it: a hook object the bridge cannot bind must still raise rather
    # than register nothing and score as a perfect identity.
    muts.append(("M17 PR059-D6: a bridge over a hook family it cannot bind",
                 lambda: _bridge_probe(), "cannot bridge"))

    # ---- population and split --------------------------------------------------------------------
    muts.append(("M18 a split that binds ZERO rows",
                 lambda: split_bind(pr, repo_path(bank_path_for(pr, "button_bomb")),
                                    "nosuchsplit", assign), "ZERO rows"))
    # A domain the ANALYZER's bind_rows never sees, because it is one of the three
    # whole-population exclusions -- so this exercises the RUNNER's own guard rather than the
    # analyzer's, which would otherwise fire first and leave this one unreachable.
    muts.append(("M19 a domain absent from the frozen split manifest",
                 lambda: split_bind(pr, repo_path(bank_path_for(pr, "button_bomb")), "train",
                                    {k: v for k, v in assign.items()
                                     if k != whole_population_exclusions(pr)[0]}),
                 "absent from the frozen split manifest"))
    muts.append(("M20 A-039: binding the cell on the WRONG field",
                 lambda: bind_rows(pr, {}, assign, selector_field="condition"), "A-039"))
    muts.append(("M21 an exclusion that does not declare a boolean whole_population",
                 lambda: _prereg_without_bool_exclusion(pr), "whole_population"))

    # ---- the finished-arm gate --------------------------------------------------------------------
    muts.append(("M22 an arm whose row count is not the bound population",
                 lambda: _fake_arm_gate(pr, arms, n_rows=39, expect=40), "unequal populations"))
    muts.append(("M23 an arm that ran under SDPA",
                 lambda: _fake_arm_gate(pr, arms, impl="sdpa"), "VOID"))
    # DCS-TS-P11. The gate refused a VALID eager arm because it read
    # `intervention.attn_implementation` / a top-level `attn_implementation` and score_behavior
    # wrote neither -- the absent field became "" and "" != "eager". These three fix the shape of
    # that bug in both directions: absent must REFUSE (not be read as a value), the requested-value
    # echo must NOT be accepted as the loaded backend, and a recorded SDPA must still be VOID
    # through the second accepted source too.
    muts.append(("M23b an arm whose summary records the backend NOWHERE (absent != eager)",
                 lambda: _fake_arm_gate(pr, arms, impl_field="absent", stamp_rows=False),
                 "cannot be established"))
    muts.append(("M23c the backend recorded ONLY in knockout_liveness (the REQUESTED echo)",
                 lambda: _fake_arm_gate(pr, arms, impl_field="knockout_liveness",
                                        stamp_rows=False),
                 "cannot be established"))
    muts.append(("M23d an arm that ran under SDPA, recorded in the intervention block",
                 lambda: _fake_arm_gate(pr, arms, impl="sdpa", impl_field="intervention"),
                 "VOID"))
    muts.append(("M24 a dead hook: n_prefill_edits == 0",
                 lambda: _fake_arm_gate(pr, arms, prefill=0), "HOOK NEVER FIRED"))
    muts.append(("M25 a decode leak: n_decode_edits != 0",
                 lambda: _fake_arm_gate(pr, arms, decode=3), "prefill-only"))
    muts.append(("M26 a realised row set that is NOT the declared one (L-N4)",
                 lambda: _fake_arm_gate(pr, arms, shift=1), "L-N4"))
    muts.append(("M27 a PINNED ABSOLUTE index across sequences of differing length",
                 lambda: _fake_arm_gate(pr, arms, pin_absolute=True), "L-N"))
    muts.append(("M28 a run directory with no DONE.json",
                 lambda: _fake_arm_gate(pr, arms, no_done=True), "DONE.json"))
    muts.append(("M29 an arm that produced ZERO rows",
                 lambda: _fake_arm_gate(pr, arms, n_rows=0, expect=0), "ZERO rows"))
    muts.append(("M30 the producer's own liveness gate reporting a violation",
                 lambda: _fake_arm_gate(pr, arms, violation="knockout_never_fired"),
                 "liveness gate"))
    muts.append(("M31 a realised dose of ZERO tokens",
                 lambda: _fake_arm_gate(pr, arms, zero_dose=True), "REALISED DOSE of 0"))

    # ---- the control band ----------------------------------------------------------------------
    muts.append(("M31b CANNOT ANSWER: the row-set resolver fails on more than 5% of rows",
                 lambda: _fake_arm_gate(pr, arms, n_rows=40, expect=40, n_resolver_failed=9),
                 "CANNOT ANSWER"))
    muts.append(("M32 L-N7: a 3-draw control band whose outputs are IDENTICAL",
                 lambda: _band_or_raise(pr), "identical"))

    # ---- the checklist gate --------------------------------------------------------------------
    muts.append(("M33 an amendment pinned to the wrong parent sha",
                 lambda: _amendment_wrong_sha(pr), "amends nothing"))
    muts.append(("M34 an amendment that does not say it supersedes the checklist",
                 lambda: _amendment_no_supersede(pr), "supersedes"))
    muts.append(("M35 an amendment that silently drops a BLOCKING parent item",
                 lambda: _amendment_orphans_a_blocker(pr), "still stand"))
    muts.append(("M36 a BLOCKING item scoped out with NO re-derivable predicate",
                 lambda: _amendment_prose_scope(pr), "prose scope"))
    muts.append(("M37 the confirmatory stage run with the checklist still open",
                 lambda: _run_family_now(pr), "BLOCKING"))

    # ---- ordering ------------------------------------------------------------------------------
    muts.append(("M38 the family stage submitted before the kill stage completed",
                 lambda: assert_stage_order(tempfile.mkdtemp(), "family", "test"), "kill"))
    muts.append(("M39 the smoke stage run on TEST instead of TRAIN",
                 lambda: _run_smoke_on(pr, "test"), "TRAIN"))
    muts.append(("M40 an unknown stage name", lambda: stage_selector(pr, "h9"), "unknown stage"))

    # ---- the two schema disagreements ------------------------------------------------------------
    # PR059-D4 and PR059-D5 are RESOLVED, so "the defect is still there" is no longer a
    # reachable refusal. What replaces each is the guard that had to SURVIVE the fix.
    muts.append(("M41 PR059-D4: a liveness field the row never carried, read as a measured zero",
                 lambda: _liveness_field_dropped(pr, "n_cells_edited_expected"), "MISSING"))
    muts.append(("M42 PR059-D5: the two arm sets differing and being reported as agreeing",
                 lambda: compare_arm_sets(
                     sorted(x.tag() for x in build_arm_manifest(pr))[1:],
                     verifier_arm_set()["tags"]), "PR059-D5"))
    muts.append(("M44 PR059-D4: a hook that fired zero times, on a complete record",
                 lambda: _liveness_field_dropped_value(pr, "hook_fired_count", 0), "VOID"))
    muts.append(("M45 PR059-D4: realised cells != expected cells",
                 lambda: _liveness_field_dropped_value(pr, "n_cells_edited_realised", 1),
                 "realised"))
    muts.append(("M46 PR059-D6: the bridge family removed from pair_common's dispatch",
                 lambda: _bridge_family_gone(pr, arms), "PR059-D6"))

    n_red = 0
    for name, fn, needle in muts:
        red = _refuses(fn, needle)
        n_red += red
        print("  %-6s %-62s %s" % ("RED" if red else "GREEN", name,
                                   "" if red else "<-- UNREACHABLE REFUSAL"))
    print("[mutate] %d/%d mutations produced a refusal" % (n_red, len(muts)))
    if n_red != len(muts):
        print("  AN UNREACHABLE REFUSAL IS NOT A GUARD.", file=sys.stderr)
        return 1
    return 0


# -------- mutation helpers --------------------------------------------------------------------
def _smoke_ctx(pr: Prereg, arm: ArmSpec, **over) -> Dict[str, Any]:
    ctx = {"condition": cell_condition_for_bank(
        pr, repo_path(bank_path_for(pr, arm.bank)))["condition"],
        "constructibility": constructibility(pr, arm), "expect_n": 40, "limit": 40,
        "exclude_file": "/tmp/x.txt"}
    ctx.update(over)
    return ctx


def _argv_with(pr: Prereg, arms, expect_n: int, limit: int):
    arm = _arm_by(arms, scope_id="S_C", kind="scope")
    argv = build_argv(pr, arm, _smoke_ctx(pr, arm, expect_n=expect_n, limit=limit))
    assert_expect_n_agrees_with_limit(argv)


def _drifted(pr: Prereg, arms, flag: str, value: str):
    arm = _arm_by(arms, scope_id="S_C", kind="scope")
    argv = build_argv(pr, arm, _smoke_ctx(pr, arm))
    out = []
    i = 0
    while i < len(argv):
        if argv[i] == flag:
            out += [flag, value]
            i += 2
            continue
        if flag.startswith("--knockout-rel-end-rows=") and argv[i] == flag:
            out.append(value)
            i += 1
            continue
        if "=" in flag and argv[i] == flag:
            out.append(value)
            i += 1
            continue
        out.append(argv[i])
        i += 1
    if out == argv:                                       # the flag was absent: substitute inline
        out = [value if t == flag else t for t in argv]
    assert_argv_agrees_with_analyzer(pr, arm, out)


def _drifted_nondemo(pr: Prereg, arms):
    arm = _arm_by(arms, kind="nondemo_control", draw_index=0)
    argv = build_argv(pr, arm, _smoke_ctx(pr, arm))
    i = argv.index("--intervene")
    argv[i + 1] = argv[i + 1].replace(nondemo_arm_name(0), "demo_all")
    assert_argv_agrees_with_analyzer(pr, arm, argv)


def _build_unbuildable(pr: Prereg, arms, **kw):
    arm = _arm_by(arms, **kw)
    build_argv(pr, arm, _smoke_ctx(pr, arm))


def _prereg_without_bool_exclusion(pr: Prereg):
    obj = copy.deepcopy(pr.obj)
    for e in obj["population"]["preregistered_exclusions"]:
        e.pop("whole_population", None)
    whole_population_exclusions(Prereg(obj, "MUTANT"))


def _band_or_raise(pr: Prereg):
    g = control_band_gate(["a" * 64] * int(n_random_row_draws(pr)), int(n_random_row_draws(pr)))
    if not g["ok"]:
        raise RunnerRefusal("control band VOID: %s" % g["reason"])


def _assert_liveness_evaluable():
    r = analyzer_liveness_contract_report()
    if not r["ok"]:
        raise RunnerRefusal(r["defect"])


def _assert_arm_sets_agree(pr: Prereg):
    d = arm_set_disagreement(pr)
    compare_arm_sets(sorted(x.tag() for x in build_arm_manifest(pr)),
                     verifier_arm_set()["tags"])
    if not d.get("agree"):
        raise RunnerRefusal(d.get("defect") or "arm sets disagree")


def _liveness_field_dropped(pr: Prereg, field: str):
    """PR059-D4's SURVIVING guard. The producer now writes the three counters, so "they have no
    source" is no longer reachable -- but "a row arrived without one and the gate read it as a
    measured zero" is the defect that mattered, and it must still refuse."""
    rec = AN.LivenessRecord(arm_id="u", scope_id="S_C", prompt_id="p", enabled=True,
                            hook_fired_count=1, n_forward=1, n_prefill_edits=1, n_decode_edits=0,
                            keys_masked=4, surface_span_n_tokens=1,
                            surface_span_positions=[190], surface_span_decoded=[" button"],
                            n_cells_edited_expected=4, n_cells_edited_realised=4,
                            attn_implementation=required_attn_impl(pr), seq_len=200,
                            query_kind=primary_channel(pr), output_sha256="a").as_row()
    rec.pop(field)
    return liveness_gate([rec], "u", pr)


def _liveness_field_dropped_value(pr: Prereg, field: str, value):
    """A COMPLETE record whose field is present and carries a defect value. This is the other
    half of PR059-D4: 'the producer never wrote it' RAISES, and 'it wrote it and it is zero'
    is a DEAD HOOK -- two different verdicts, and the gate must give two different answers."""
    rec = AN.LivenessRecord(arm_id="u", scope_id="S_C", prompt_id="p", enabled=True,
                            hook_fired_count=1, n_forward=1, n_prefill_edits=1, n_decode_edits=0,
                            keys_masked=4, surface_span_n_tokens=1,
                            surface_span_positions=[190], surface_span_decoded=[" button"],
                            n_cells_edited_expected=4, n_cells_edited_realised=4,
                            attn_implementation=required_attn_impl(pr), seq_len=200,
                            query_kind=primary_channel(pr), output_sha256="a").as_row()
    rec[field] = value
    lg = liveness_gate([rec], "u", pr)
    if not lg["live"]:
        raise RunnerRefusal("arm u is VOID: %s" % "; ".join(lg["reasons"]))
    return lg


def _bridge_family_gone(pr: Prereg, arms):
    """PR059-D6's SURVIVING guard: if pair_common stops declaring the attention-mask bridge
    family, the bridge arm must be refused BY NAME again rather than launched to die."""
    import pair_common as pc
    saved = getattr(pc.DisabledHookBridge, "BRIDGE_FAMILIES", ())
    try:
        pc.DisabledHookBridge.BRIDGE_FAMILIES = ("forward_output",)
        c = constructibility(pr, _arm_by(arms, kind="bridge"))
        if not c["constructible"]:
            raise RunnerRefusal("; ".join(c["reasons"]))
        return c
    finally:
        pc.DisabledHookBridge.BRIDGE_FAMILIES = saved


def _run_smoke_on(pr: Prereg, split: str):
    run_stage(pr, _args(stage="smoke", split=split, dry_run=True))


def _run_family_now(pr: Prereg):
    import tempfile
    td = tempfile.mkdtemp()
    for s in ("smoke_train", "kill_test"):
        os.makedirs(os.path.join(td, s))
        json.dump({"status": "ok"}, open(os.path.join(td, s, "DONE.json"), "w"))
    rc = run_stage(pr, _args(stage="family", split="test", state_root=td, dry_run=True,
                             amendment=AMENDMENT_DEFAULT))
    if rc != 0:
        raise RunnerRefusal("the family stage is BLOCKING and the dry run exited %d" % rc)


def _amendment_no_supersede(pr: Prereg):
    _amendment_variant(pr, lambda o: o["amendment"].__setitem__("supersedes", []))


def _amendment_orphans_a_blocker(pr: Prereg):
    def _f(o):
        for it in o["pre_extraction_checklist"]:
            it["supersedes"] = "V0"
    _amendment_variant(pr, _f, gate=True)


def _amendment_prose_scope(pr: Prereg):
    def _f(o):
        o["pre_extraction_checklist"].append(
            {"id": "VZZ", "item": "a scope with no code path", "blocking": True, "done": False,
             "supersedes": "U1 U2 U3 U4 U5 U6 U7 U8 U9 U10",
             "applies_to_stages": ["family"]})
    _amendment_variant(pr, _f, gate=True, stage="kill")


def _amendment_variant(pr: Prereg, edit, gate: bool = False, stage: str = "family"):
    import tempfile
    obj = json.load(open(repo_path(AMENDMENT_DEFAULT)))
    edit(obj)
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fh:
        json.dump(obj, fh)
        p = fh.name
    rel = p                            # ABSOLUTE, outside the repo (shared working tree)
    try:
        if gate:
            g = checklist_gate(PREREG_DEFAULT, rel, stage, {"split": "train", "limit": 40})
            if not g["ok"]:
                raise RunnerRefusal("; ".join(g["blocking"]))
        else:
            load_amendment(rel, pr)
    finally:
        os.unlink(p)


def _fake_arm_gate(pr: Prereg, arms, n_rows: int = 40, expect: int = 40, impl: str = "",
                   prefill: int = 1, decode: int = 0, shift: int = 0, pin_absolute: bool = False,
                   no_done: bool = False, violation: str = "", zero_dose: bool = False,
                   n_resolver_failed: int = 0, impl_field: str = "summary",
                   stamp_rows: bool = True):
    """Build a real `score_behavior`-shaped run directory and push it through the arm gate.

    `impl_field` says WHERE in summary.json the attention backend is recorded, because the
    DCS-TS-P11 defect was entirely about that: the gate read two places and the producer wrote a
    third. "summary" / "intervention" are the two the gate accepts (both are the LOADED value);
    "knockout_liveness" is the place score_behavior used to write the REQUESTED value and must
    NOT be accepted; "absent" is an artifact that records the backend nowhere at all.
    `stamp_rows=False` drops the per-row echo so the summary-level field is what is under test.
    """
    import tempfile
    arm = _arm_by(arms, scope_id="S_C", kind="scope")
    rows_declared = list(declared_scopes(pr)["S_C"]["rel_end_rows"])
    td = tempfile.mkdtemp()
    if not no_done:
        json.dump({"status": "ok"}, open(os.path.join(td, "DONE.json"), "w"))
    _impl_val = impl or required_attn_impl(pr)
    _summary = {"failures": {"n_attempted": n_rows + n_resolver_failed, "n_succeeded": n_rows,
                             "n_failed": n_resolver_failed,
                             "failure_reasons": ({"relend:out_of_span": n_resolver_failed}
                                                 if n_resolver_failed else {})}}
    if impl_field == "summary":
        _summary["attn_implementation"] = _impl_val
    elif impl_field == "intervention":
        _summary["intervention"] = {"mode": "attn_knockout", "attn_implementation": _impl_val}
    elif impl_field == "knockout_liveness":
        _summary["knockout_liveness"] = {"attn_implementation": _impl_val}
    elif impl_field != "absent":
        raise ValueError("unknown impl_field %r" % impl_field)
    json.dump(_summary, open(os.path.join(td, "summary.json"), "w"))
    with open(os.path.join(td, "results.jsonl"), "w") as fh:
        for i in range(n_rows):
            # PER-ROW-VARYING seq_len on purpose: an absolute-index producer cannot pass the
            # end-relative audit by accident.
            n = 120 + i
            pos = [(100 if pin_absolute else n) + r + shift for r in rows_declared]
            fh.write(json.dumps({
                "prompt_id": "p%d" % i, "domain": "d%d" % (i // 10),
                "query_kind": primary_channel(pr), "seq_len": n,
                "surface_span_positions": pos,
                "surface_span_n_tokens": (0 if zero_dose else len(pos)),
                "surface_span_decoded": [" button"] * len(pos),
                "hook_n_forward": 1, "hook_n_prefill_edits": prefill,
                # PR059-D4: the three fields the PRODUCER now owns. Expected is counted before
                # the mask write and realised is read back from it, so a fixture that reports
                # them EQUAL is asserting the healthy case and can be made to disagree.
                "hook_fired_count": (0 if (prefill <= 0 or zero_dose) else 1),
                "n_forward_with_destinations": 1,
                "n_cells_edited_expected": (0 if zero_dose else 12 * len(pos)),
                "n_cells_edited_realised": (0 if zero_dose else 12 * len(pos)),
                "hook_n_decode_edits": decode, "hook_n_keys_masked": 12,
                "hook_liveness_violations": ([violation] if violation else []),
                **({"attn_implementation": _impl_val} if stamp_rows else {})}) + "\n")
    verify_arm_artifacts(pr, arm, td, expect)


# ============================================================================================
# 16. MAIN
# ============================================================================================
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--prereg", default=PREREG_DEFAULT)
    ap.add_argument("--amendment", default=AMENDMENT_DEFAULT,
                    help="an AMENDMENT config whose pre_extraction_checklist and artifacts flags "
                         "supersede the parent's for the stage-aware gate. It must name this "
                         "preregistration and pin its sha16; pass an empty string to gate on the "
                         "parent alone.")
    ap.add_argument("--stage", default="", choices=[""] + list(STAGE_ORDER))
    ap.add_argument("--split", default="train", choices=["train", "validation", "test"])
    ap.add_argument("--runs", default=RUNS_ROOT_DEFAULT)
    ap.add_argument("--state-root", default=STATE_ROOT_DEFAULT)
    ap.add_argument("--smoke-limit", type=int, default=40)
    ap.add_argument("--dry-run", action="store_true",
                    help="construct and validate every arm WITHOUT a GPU and without loading the "
                         "model; writes nothing")
    ap.add_argument("--plan", action="store_true", help="print the validated manifest and stop")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--mutate", action="store_true")
    ap.add_argument("--out", default="")
    a = ap.parse_args()

    if a.self_test:
        return selftest()
    if a.mutate:
        return mutate()

    try:
        pr = load_prereg(a.prereg, for_extraction=False)
    except PreregError as e:
        print("PREREG REFUSAL:\n%s" % e, file=sys.stderr)
        return 2
    check_wording_pin(pr)

    try:
        if a.plan:
            p = plan(pr, a)
            txt = json.dumps(p, indent=2, default=str)
            assert_sayable(txt, forbidden_from_prereg(pr))
            if a.out:
                open(a.out, "w").write(txt)
                print("wrote %s" % a.out)
            else:
                print(txt)
            return 0
        if not a.stage:
            print("--stage is required (one of %s), or use --plan / --self-test / --mutate"
                  % list(STAGE_ORDER), file=sys.stderr)
            return 2
        return run_stage(pr, a)
    except (RunnerRefusal, Refusal, ZeroBinding, CannotAnswer, PreregError) as e:
        print("REFUSAL:\n  %s" % e, file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
