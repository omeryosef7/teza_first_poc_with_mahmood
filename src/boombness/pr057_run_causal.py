#!/usr/bin/env python3
"""`DCS-PR-057` PHASE 9 -- the GPU runner (blocking checklist item `Q4b`).

WHY THIS FILE EXISTS AT ALL
---------------------------
The arm manifest is 54 runs. A PHASE 7 baseline measured 5568 rows in 2296.6 s wall on one L40S
INCLUDING the model load, and a Llama-3.1-8B load off this filesystem is minutes, not seconds. 54
separate `score_behavior.py` invocations would therefore spend more wall time loading weights than
computing. This runner loads the model ONCE and loops the manifest inside one allocation. That is
its entire reason to exist, and `--model-loads` in `DONE.json` is the number that proves it did.

IT IMPORTS THE ARM MANIFEST, THE HOOKS AND THE DONOR CONTRACT FROM THE ANALYZER
------------------------------------------------------------------------------
`scripts/dcs_ts_pr057_causal.py` is the analyzer and it is the single source of truth for what an
arm IS: `build_arm_manifest`, `ArmSpec`, `liveness_gate`, `audit_end_relative`,
`propagation_read_layers`, `donor_span_contract`, `ProbeReadCapture`, `load_frozen_probe`. Nothing
here re-derives any of them. Two files that disagree about what an arm is would be the whole
failure mode of this phase, so this runner additionally CROSS-CHECKS every argv it builds against
the analyzer's own `launch_command()` for the same arm (bank, arm label, tag, mode, layer band,
alpha) and REFUSES on any disagreement. A direction label the analyzer invents that this runner has
no declared mapping for is a refusal, never a guess: see `DIRECTION_MAP`.

WHAT IT RUNS THROUGH
--------------------
`src/boombness/score_behavior.py`'s `main()`, in-process, with `sys.argv` set -- not a
re-implementation of the readout and not a copy of its flags' meanings. The single monkeypatch is a
memoising `ds_common.load_model`, which is what makes "load once, loop the arms" true; it is
installed by this file, it is counted, and the count is written into the artifact.

FAIL-CLOSED, EVERYWHERE
-----------------------
A non-zero exit, a `SystemExit` from any house guard, a missing `DONE.json`, zero rows, a liveness
record that cannot prove the hook fired and changed the state, a bridge record inside a live arm, a
resolved edit index that is not `len(input_ids) + rel_end`, a population that is not the size the
runner computed for it -- each STOPS the run. The runner never continues past a failure and never
writes a `DONE.json` for a stage whose arms did not all reach a terminal state. A partial run is
`ABORTED.json`, which is a different file, so it cannot be mistaken for a complete one.

THE C-13 HOLE STAYS CLOSED
--------------------------
Every intervened arm is launched with `--pr057-liveness-out auto`; `--emit-liveness` is REQUIRED
for any arm that installs a hook, and an arm that produced zero liveness records is refused. A hook
that never fired must be impossible to mistake for a clean null, so the runner gates each arm
TWICE: once with the producer's own gate (`pair_common.project_out_liveness_violations`, the same
function `score_behavior` aborts on) and once with the consumer's (`liveness_gate` in the
analyzer). Where the two schemas disagree the disagreement is RECORDED as a blocking defect and
written into `PR057_ARM_GATE.json` -- it is never smoothed over. See `DEFECT_LIVENESS_SCHEMA`.

ORDER, AND THE SECOND KILL CONDITION, AS CODE
---------------------------------------------
`Q0 -> Q1 -> smoke(Q7) -> H1 -> H2` is enforced by `assert_stage_order()`, which reads the earlier
stages' own `DONE.json` files, not a comment. The frozen config's second kill condition -- "if the
H1 upper bound does not move O2, H2a/H2b are NOT submitted at that site" -- is
`h1_kill_state()` + `apply_kill_condition()`: an H2 arm at a killed site is removed from the
submission list and recorded as `NOT_SUBMITTED_UNINFORMATIVE`, never as a negative. Submitting one
anyway is a refusal (mutation `M5`).

WHAT IS STILL BLOCKED, AND IS REPORTED RATHER THAN FAKED
--------------------------------------------------------
28 of the 54 manifest arms cannot be constructed with the instrument as it stands today, leaving 26
that can: the 16 H1 arms and the 2 C7 self-patch controls need the cross-prompt donor path (and
under C-112/R-116 the H1 population is EMPTY anyway), the 4 H2b arms need `component_replace`, the
2 C2 arms need a shuffled-label direction the PR-053 payload does not carry, the 2 C4 arms are an
additive mode that is not instrumented and has no single-site form, and the 2 C5 bridges carry a
preregistered alpha of 0 that makes the bridge certify nothing (C-119, below).
`constructibility()` names each one and the runner refuses to launch it. It does not substitute a
different arm and it does not report a stage as complete when part of it could not be built.

USAGE
    python3 src/boombness/pr057_run_causal.py --self-test          # the runner's own logic
    python3 src/boombness/pr057_run_causal.py --mutate             # each mutation must be RED
    python3 src/boombness/pr057_run_causal.py --plan               # the 54-arm manifest, CPU only
    python3 src/boombness/pr057_run_causal.py --stage h2 --split test --dry-run \
            --fit-dir outputs/dcs_ts/directions_pr053
    python3 src/boombness/pr057_run_causal.py --stage h2 --split test \
            --fit-dir outputs/dcs_ts/directions_pr053 --emit-liveness
"""
from __future__ import annotations

import argparse
import hashlib
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
# hook, a liveness rule or the donor contract; they are imported.
import dcs_ts_pr057_causal as AN  # noqa: E402
from dcs_ts_pr057_causal import (  # noqa: E402
    ArmSpec,
    Refusal,
    audit_end_relative,
    build_arm_manifest,
    family_members,
    launch_command,
    liveness_gate,
    load_arm_run,
    load_frozen_probe,
    option_mass_gate,
    o2_projection_out_from_rows,
    propagation_read_layers,
    q1_power,
    sha256_file,
    CONTRACT_ARM,
    CONTRACT_LIVENESS,
    CONTRACT_PROBE,
    C112_PRIMARY_IS_10_2,
)
from dcs_ts_pr048_analysis import _find_run, load_split  # noqa: E402
from dcs_ts_pr051_positional import Checks, ZeroBinding  # noqa: E402

PREREG_DEFAULT = "configs/dcs_ts_pr057_phase9.json"
#: The PHASE 9 amendment (DCS-PR-060). It is a SEPARATE, also-FROZEN file; the parent is
#: never edited. It supersedes the parent's `pre_extraction_checklist` on measured evidence
#: and adds the stage scoping the A14 gate reads. It cannot stand alone -- it carries no
#: `hypotheses`, `scope_levels`, `seeds`, `controls` or `things_that_must_not_be_said` -- so
#: the PARENT is what is loaded and the amendment is overlaid onto the checklist gate only.
AMENDMENT_DEFAULT = "configs/dcs_ts_pr060_phase9_amendment.json"
SCORE_SCRIPT = "src/boombness/score_behavior.py"
RUNS_ROOT_DEFAULT = "outputs/boombness/score_behavior"
STATE_ROOT_DEFAULT = "outputs/boombness/pr057_runner"
MANIFEST_FILE = "PR057_RUN_MANIFEST.json"
ARM_GATE_FILE = "PR057_ARM_GATE.json"
STAGE_ORDER = ("q0", "q1", "smoke", "h1", "h2")

#: PHASE 7 baseline (control C6) run tags: `<prefix>_<codeword>_<concept>`.
PHASE7_TAG_PREFIX_DEFAULT = "ts116m_readout"


class RunnerRefusal(RuntimeError):
    """Anything this runner will not do. Every one of them is fail-closed."""


# ============================================================================================
# DEFECTS FOUND WHILE BUILDING THIS RUNNER. Recorded, never worked around.
# ============================================================================================
DEFECT_C113 = (
    "C-113: configs/dcs_ts_pr057_phase9.json directions.artifact.path is "
    "'outputs/dcs_ts_pr053_diffmeans/<run>/directions.pt', which can NEVER be loaded -- the "
    "LOADER decides the filename and score_behavior.py:2081-2085 joins --fit-dir with "
    "'directions_fit_dev.pt' (then 'directions_fit_heldout.pt'). The runner takes the DIRECTORY "
    "outputs/dcs_ts/directions_pr053 and lets the loader join. The config is FROZEN and is NOT "
    "edited to agree."
)

DEFECT_LIVENESS_SCHEMA = (
    "C-117 (RESOLVED 2026-09-07 in the producer, not here): the liveness PRODUCER and the liveness "
    "CONSUMER did not share a schema. pair_common.hook_stats_dict() wrote n_destination_rows / "
    "n_cells_edited_realised and NO 'n_cells_edited_expected' and NO "
    "'orthogonal_residual_delta_l2', while the analyzer's liveness_gate() and "
    "orthogonal_residual_gate() read both with a defaulting .get -- so a MISSING field became a "
    "measured 0 / NaN and EVERY healthy arm gated VOID with a substantive scientific verdict "
    "('the arm declared no destinations'; 'the orthogonal component was NOT preserved'). "
    "RECONCILED as follows: the PRODUCER owns both measurements (only the hook sees the tensor it "
    "was handed and holds h_pre, h_post and d) and now writes them; the CONSUMER raises "
    "NotMeasured on an ABSENT field instead of defaulting it, so a missing field can never again "
    "be mistaken for a measured zero, and a measured zero is still a failing verdict. This runner "
    "no longer invents 'expected := n_destination_rows'; it requires the producer's own count. It "
    "still does NOT rewrite PR057_LIVENESS.jsonl, and both gates' verdicts go into "
    "PR057_ARM_GATE.json."
)

DEFECT_PROBE_ATTRIBUTION = (
    "C-118(a) (CLOSED 2026-09-07). It was recorded as: ProbeReadCapture (Q11) is a read hook on a "
    "layer and score_behavior offers NO per-row callback, so a captured record cannot be "
    "attributed to a prompt_id/domain -- one row produces many forwards (the variant batches) and "
    "order-based attribution would be a silent misalignment of exactly the shape this phase "
    "refuses. THE FIRST HALF OF THAT WAS WRONG: score_behavior builds its interventions INSIDE "
    "the row loop -- it must, because the edit site is end-relative and is resolved against the "
    "row's own length -- and its PR057_LIVENESS.jsonl writer already stamps prompt_id/domain from "
    "that scope. The read hook is now built there too and handed the row's metadata, so "
    "attribution is BY CONSTRUCTION and never by the order records arrive in. THE SECOND HALF WAS "
    "REAL and is closed differently: the site is PINNED to the absolute index resolved against "
    "the row's prompt (the same number the edit hook gets) instead of being re-resolved against "
    "each variant forward's length, ONE record is emitted per row per read layer, and a row whose "
    "forwards disagree at that index is REFUSED rather than averaged -- so if the causal/"
    "right-padding assumption that makes them agree ever breaks, the run stops."
)

DEFECT_PROBE_ARTIFACT = (
    "The frozen PR-048 probe (Q10) is a CODE PATH in scripts/dcs_ts_pr048_analysis.py "
    "(res['FROZEN_PROBE']) but the artifact on disk, outputs/dcs_ts/pr048_result.json, carries no "
    "such block -- the analysis has not been re-run since the export was added. load_frozen_probe "
    "refuses it, correctly."
)

DEFECT_C119_BRIDGE_ALPHA = (
    "C-119 (new, found by this runner): the manifest gives control C5 (the disabled-hook bridge) "
    "alpha = 0.0 -- 'none, the hook is registered and edits nothing'. But the bridge is not a "
    "hook with no dose: it is the LIVE arm's hook, run in full, with its write discarded. "
    "pair_common.DisabledHookBridge records `would_have_changed_max_abs` and "
    "project_out_liveness_violations REFUSES a bridge whose inner hook would not have edited "
    "anything, so an alpha=0 bridge is refused at the node -- and if it were not, it would "
    "certify nothing, because the machinery it is supposed to prove inert would have been given "
    "no edit to discard. RESOLVED 2026-09-07 BY INTERPRETATION, RECORDED AS SUCH: the frozen "
    "config preregisters NO alpha for C5 -- controls.arms[C5] carries only id/name/rule/blocking, "
    "and its rule is 'the full intervention code path with the hook DISABLED'. The alpha=0.0 was "
    "a literal in scripts/dcs_ts_pr057_causal.py's build_arm_manifest, which is not frozen. C5 "
    "now runs the LIVE arm's alpha (1.0, the H2a arm it shadows) with the write discarded, which "
    "is what 'the hook is registered and edits nothing' means operationally: the bridge's dose to "
    "the model is zero because nothing is WRITTEN, not because alpha is. At alpha=0 the inner "
    "projection is the identity and the bridge would reproduce baseline even with a garbage "
    "direction on the wrong layer -- it would pass for reasons unrelated to what it certifies. "
    "This constant is retained as a TRIPWIRE: an alpha=0 disabled arm is still refused."
)

#: Why an arm cannot be launched today. Each is a REFUSAL, and each names the item that would
#: clear it. Nothing here is substituted with a different arm.
UNBUILDABLE = {
    "patch": (
        "mode 'patch' (H1 upper-bound donor / C7 self-patch) has NO code path: score_behavior's "
        "--rescue-donor offers only 'clean' and 'self', both on the SAME prompt (checklist Q3 / "
        "Q12(a)). The donor contract is designed and unit-tested in the analyzer "
        "(donor_span_contract / build_cross_prompt_donor / self_patch_gate) and the GPU wiring "
        "does not exist. SEPARATELY, C-112/R-116: the source concept installs in 0/113 domains, "
        "so on this bank the H1 population is EMPTY and its null would be CANNOT ANSWER BY "
        "CONSTRUCTION. It must not be submitted at all."),
    "component_replace": (
        "mode 'component_replace' (H2b) has NO code path: make_intervention implements "
        "'project_out' and 'add' only (checklist Q12(b)). The instrumented hook exists in the "
        "analyzer (make_instrumented_component_replace_hook, with the orthogonal-residual "
        "verification I-N7) and is not wired to score_behavior."),
}

#: C-122, CLOSED 2026-09-07. `add` was in UNBUILDABLE above with this reason:
#:
#:   "mode 'add' (control C4) is constructible in make_intervention but is NOT INSTRUMENTED:
#:    pc.AllPositionAdd is built with no `stats=`, so an additive arm launched with
#:    --pr057-liveness-out produces ZERO liveness records and score_behavior refuses it -- and
#:    launched WITHOUT it, a dead additive hook would score as a clean null (C-13). C4 also has
#:    no single-site form: edit_positions is implemented for project_out only, so C4 x S1 would
#:    silently be an all-position edit under a single-site label."
#:
#: BOTH halves are now closed in the producer, not waived here:
#:   * `pc.make_add_hook` / `pc.AllPositionAdd` take `stats=` and record the same liveness
#:     quantities the project-out hook does, so a dead C4 hook REFUSES instead of returning the
#:     "the control did not move the readout" record a positive H2a wants to see;
#:   * `pc.SinglePositionAdd` gives C4 a real single-site form under the same three-argument
#:     rel_end/seq_len/absolute-index contract the S1 project-out arm uses, so C4 x S1 is an
#:     S1 edit rather than an all-position edit under an S1 label;
#:   * the DOSE is declared in gap units AND checked: `alpha == alpha_gap_units * gap_norm` at
#:     construction, and the realised per-cell magnitude against `alpha` in the record.
DEFECT_C122_ADD_UNINSTRUMENTED = (
    "C-122 (CLOSED 2026-09-07): mode 'add' (control C4) was constructible in make_intervention "
    "and NOT INSTRUMENTED -- pc.AllPositionAdd took no `stats=`, so a C4 arm produced zero "
    "liveness records and a dead additive hook scored as a clean null (C-13) in the ONE arm "
    "whose job is to be sceptical of a positive H2a. Closed in pair_common (stats on the add "
    "hooks, a real SinglePositionAdd, and a declared-and-measured gap-unit dose)."
)


# ============================================================================================
# 1. SMALL PARSERS -- every number comes out of the frozen file, none is typed here
# ============================================================================================
def repo_path(*parts: str) -> str:
    return os.path.join(REPO, *parts)


def read_site_rel_end(pr: Prereg) -> int:
    """The edit/read site as an END-RELATIVE offset, PARSED from the frozen file.

    `read_site._positions_in_rel_end` says "codeword_last == rel_end -10". Typing -10 here would be
    the same defect as a re-typed threshold: the file and the code could then disagree without
    either being wrong on its own.
    """
    txt = str(pr.require("read_site", "_positions_in_rel_end"))
    pos = str(pr.require("read_site", "position"))
    m = re.search(re.escape(pos) + r"\s*==\s*rel_end\s*(-?\d+)", txt)
    if not m:
        raise RunnerRefusal(
            "read_site._positions_in_rel_end does not state %r as a rel_end offset; refusing to "
            "guess which token the single-site arm edits." % pos)
    v = int(m.group(1))
    if v >= 0:
        raise RunnerRefusal(
            "the frozen file resolves %r to a NON-NEGATIVE offset %d. A non-negative offset is an "
            "absolute index wearing the wrong name, and an absolute index reused across examples "
            "is this repository's twice-recorded bug class." % (pos, v))
    return v


def cell_condition(pr: Prereg) -> str:
    """The `--conditions` value that binds the preregistered CELL.

    A-039: the population is selected on the field `cell`, and `score_behavior` has NO --cells
    flag, so the launcher must select on `condition` instead. That mapping is 1:1 on this bank and
    is VERIFIED per bank by `bind_population_rows()` -- it is not assumed.
    """
    cell = str(pr.require("population", "cell"))
    table = {"C": "natural_doublespeak", "A": "benign_literal", "B": "direct_harmful",
             "E": "concept_in_benign_ctx"}
    if cell not in table:
        raise RunnerRefusal("no condition string is declared for cell %r" % cell)
    return table[cell]


def bank_path_for(arm: ArmSpec) -> str:
    return ("data/boombness_prompts/boombness_prompt_bank_ts116m_%s_%s.jsonl"
            % (arm.codeword, arm.target_concept))


def file_sha16(path: str) -> str:
    return hashlib.sha256(open(path, "rb").read()).hexdigest()[:16]


# ============================================================================================
# 2. POPULATION BINDING -- and --split is LOAD-BEARING, not decorative
# ============================================================================================
def bind_population_rows(pr: Prereg, bank_abs: str) -> Dict[str, Any]:
    """Apply exactly `score_behavior`'s own row filter, and verify the A-039 cell mapping.

    `score_behavior` filters on query_kind, condition and n_examples (score_behavior.py:1765-1778).
    This reproduces that filter to compute --expect-n, and then checks that selecting on
    `condition` bound the SAME rows as selecting on `cell` would have. On this bank the mapping is
    1:1; on another bank it may not be, and then this refuses instead of binding the wrong cell.
    """
    qk = str(pr.require("population", "query_kind_primary"))
    dose = int(pr.require("population", "n_examples_primary"))
    cond = cell_condition(pr)
    cell = str(pr.require("population", "cell"))
    rows = []
    with open(bank_abs) as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    by_cond = [r for r in rows if r.get("query_kind") == qk
               and r.get("condition") == cond and int(r.get("n_examples", -1)) == dose]
    by_cell = [r for r in rows if r.get("query_kind") == qk
               and r.get("cell") == cell and int(r.get("n_examples", -1)) == dose]
    ids_cond = {r["prompt_id"] for r in by_cond}
    ids_cell = {r["prompt_id"] for r in by_cell}
    if not ids_cond:
        raise ZeroBinding(
            "the population filter (query_kind=%s, condition=%s, n_examples=%d) bound ZERO rows "
            "of %s. A filter that binds nothing is not a filter." % (qk, cond, dose, bank_abs))
    if ids_cond != ids_cell:
        raise RunnerRefusal(
            "A-039: selecting on condition=%r bound %d rows and selecting on cell=%r bound %d "
            "(symmetric difference %d) on %s. score_behavior has no --cells flag, so the launcher "
            "must select on `condition`; that is only legitimate where the mapping is 1:1, and "
            "here it is not."
            % (cond, len(ids_cond), cell, len(ids_cell),
               len(ids_cond ^ ids_cell), os.path.basename(bank_abs)))
    return {"rows": by_cond, "n": len(by_cond), "query_kind": qk, "condition": cond,
            "n_examples": dose, "cell": cell,
            "n_domains": len({r["domain"] for r in by_cond}),
            "a039_cell_condition_mapping_is_1to1": True}


def split_bind(pr: Prereg, bank_abs: str, split: str, assign: Dict[str, str]) -> Dict[str, Any]:
    """Bind ONE domain split, as the EXCLUSION LIST that `score_behavior` will be given.

    WHY --split IS IMPLEMENTED THIS WAY. `score_behavior` has no split flag: the bank's own
    `split` field is dev/heldout, which is NOT the domain split this phase is preregistered on
    (`data/boombness_prompts/dcs_ts116_domain_split.json`, field `dsplit`, 67/23/23 domains). A
    `--split` argument that reached nothing would be a flag that cannot act -- the failure this
    repository refuses. So the split is bound as a DECLARED, OUTCOME-INDEPENDENT prompt_id
    exclusion (the mechanism `--exclude-prompt-ids` exists for), and the count is asserted with
    `--expect-n`. A validation-stage job then never computes a TEST row at all, which is stronger
    discipline than subsetting after the fact.

    The three preregistered whole-population exclusions are removed in EVERY split.
    """
    pop = bind_population_rows(pr, bank_abs)
    excl_domains = set()
    for e in pr.require("population", "preregistered_exclusions"):
        if "whole_population" not in e or not isinstance(e["whole_population"], bool):
            raise RunnerRefusal(
                "exclusion %r does not declare a boolean 'whole_population' (C-086)." % e.get("domain"))
        if e["whole_population"]:
            excl_domains.add(e["domain"])
    unknown = sorted({r["domain"] for r in pop["rows"] if r["domain"] not in assign})
    if unknown:
        raise RunnerRefusal(
            "%d domain(s) in the bound population are absent from the frozen split manifest "
            "(%s...). A row whose split is unknown must not be silently kept or silently dropped."
            % (len(unknown), unknown[:5]))
    keep, drop = [], []
    for r in pop["rows"]:
        if r["domain"] in excl_domains or assign[r["domain"]] != split:
            drop.append(r["prompt_id"])
        else:
            keep.append(r["prompt_id"])
    if not keep:
        raise ZeroBinding(
            "split %r bound ZERO rows on %s. A stage whose population is empty must refuse, not "
            "run." % (split, os.path.basename(bank_abs)))
    n_dom = len({r["domain"] for r in pop["rows"] if r["prompt_id"] in set(keep)})
    rows_per_domain = int(pr.require("population", "rows_per_domain_per_concept"))
    if n_dom * rows_per_domain != len(keep):
        raise RunnerRefusal(
            "split %r binds %d rows over %d domains, but the frozen file says %d rows per domain "
            "(%d expected). A population that is not the shape the preregistration describes is "
            "not the preregistered population."
            % (split, len(keep), n_dom, rows_per_domain, n_dom * rows_per_domain))
    if split == "test" and n_dom != int(pr.require("primary", "n_test_domains")):
        raise RunnerRefusal(
            "the TEST split binds %d domains; the frozen file declares n_test_domains=%d."
            % (n_dom, int(pr.require("primary", "n_test_domains"))))
    return {"split": split, "bank": bank_abs, "n_keep": len(keep), "n_drop": len(drop),
            "n_domains": n_dom, "keep_ids": sorted(keep), "drop_ids": sorted(drop),
            "expect_n": len(keep), "population": {k: v for k, v in pop.items() if k != "rows"},
            "excluded_whole_population_domains": sorted(excl_domains)}


def exclusion_file_text(pr: Prereg, bind: Dict[str, Any]) -> str:
    """The `--exclude-prompt-ids` file, carrying its own provenance in `#` comments."""
    head = [
        "# DCS-PR-057 runner: the rows OUTSIDE domain split %r on %s." % (bind["split"],
                                                                         os.path.basename(bind["bank"])),
        "# Source: %s field %s (sha16 %s) -- OUTCOME-INDEPENDENT, frozen before any outcome."
        % (pr.require("split", "manifest"), pr.require("split", "field"),
           pr.require("split", "manifest_sha16")),
        "# Plus the preregistered whole-population exclusions: %s"
        % (", ".join(bind["excluded_whole_population_domains"]) or "(none)"),
        "# keep=%d drop=%d domains_kept=%d" % (bind["n_keep"], bind["n_drop"], bind["n_domains"]),
    ]
    return "\n".join(head + bind["drop_ids"]) + "\n"


# ============================================================================================
# 3. CONSTRUCTIBILITY, AND THE DIRECTION MAP THAT STOPS THE TWO FILES DRIFTING
# ============================================================================================
#: The analyzer's manifest names a direction by its SCIENTIFIC role; `score_behavior --intervene`
#: names it by its key in the PR-053 payload, and a norm-matched control additionally names the
#: base it is matched TO with the `<arm>@<base>` form (Q13). This table is the ONLY place the two
#: vocabularies meet. A manifest label with no entry here is a REFUSAL: an unmapped label silently
#: resolved to a plausible payload key is how a control ends up matched to an axis no arm touches.
DIRECTION_MAP: Dict[str, Optional[str]] = {
    "v_bomb_specific": "v_bomb_specific",
    "v_remap": "v_remap",
    "v_knife_specific": "v_knife_specific",
    "random_norm_matched": "random@v_bomb_specific",
    "orthogonal_to_concept_subspace": "orthogonal@v_bomb_specific",
    # C2 wants a direction re-estimated with the labels permuted within domain. The PR-053 export
    # carries no such key and this runner will not manufacture one: a control whose direction is
    # invented at launch time is not the preregistered control.
    "v_bomb_specific_shuffled_labels": None,
}


def payload_base_name(spec: str) -> str:
    """The payload key a `--intervene` direction token resolves to (`random@v_x` -> `v_x`)."""
    return spec.split("@", 1)[1] if "@" in spec else spec


def constructibility(pr: Prereg, arm: ArmSpec, payload_keys: Sequence[str]) -> Dict[str, Any]:
    """Can this arm be launched TODAY, with the instrument as it stands? Refusals are named."""
    reasons: List[str] = []
    spec: Optional[str] = None
    if arm.mode in UNBUILDABLE:
        reasons.append(UNBUILDABLE[arm.mode])
    elif arm.mode in ("project_out", "add", "disabled"):
        if arm.direction is None:
            reasons.append("mode %r with no direction" % arm.mode)
        elif arm.direction not in DIRECTION_MAP:
            reasons.append(
                "the manifest names direction %r and this runner has NO declared mapping for it. "
                "Refusing to resolve it to a payload key by resemblance: that is how a control "
                "gets matched to an axis no arm edits (Q13)." % arm.direction)
        elif DIRECTION_MAP[arm.direction] is None:
            reasons.append(
                "direction %r has no artifact: the PR-053 TRAIN-only export carries %s and "
                "nothing that could stand in for it. The control is not constructible until the "
                "shuffled-label refit exists."
                % (arm.direction, sorted(k for k in payload_keys if k.startswith("v_"))))
        else:
            spec = DIRECTION_MAP[arm.direction]
            base = payload_base_name(spec)
            if base not in payload_keys:
                reasons.append(
                    "direction %r resolves to payload key %r which the fitted payload does NOT "
                    "carry (it has %s)."
                    % (arm.direction, base, sorted(k for k in payload_keys if k.startswith("v_"))))
    else:
        reasons.append("unknown arm mode %r" % arm.mode)
    if arm.mode == "disabled" and not reasons and not float(arm.alpha or 0.0):
        reasons.append(DEFECT_C119_BRIDGE_ALPHA)
    if arm.scope == "S1" and arm.mode not in ("project_out", "add", "disabled") and not reasons:
        reasons.append("scope S1 (single site) is implemented for project_out and add only")
    return {"arm_id": arm.arm_id, "constructible": not reasons, "intervene_direction": spec,
            "reasons": reasons}


# ============================================================================================
# 4. THE COMMAND LINE FOR ONE ARM -- built here, cross-checked against the analyzer
# ============================================================================================
def build_argv(pr: Prereg, arm: ArmSpec, ctx: Dict[str, Any]) -> List[str]:
    """The `score_behavior` argv for one arm. Every value comes from the frozen file or the ArmSpec."""
    con = ctx["constructibility"]
    if not con["constructible"]:
        raise RunnerRefusal("arm %s is not constructible: %s" % (arm.arm_id, con["reasons"][0]))
    band = "%d-%d" % (min(arm.layers), max(arm.layers))
    seed = int(arm.control_draw_seed if arm.control_draw_seed is not None
               else pr.require("seeds", "control_draws"))
    argv = [
        "--bank", bank_path_for(arm),
        "--query-kinds", str(pr.require("population", "query_kind_primary")),
        "--conditions", cell_condition(pr),
        "--n-examples", str(int(pr.require("population", "n_examples_primary"))),
        "--readout-ids", "whole_answer",
        "--attn-impl", str(pr.require("model", "attn_impl")),
        "--max-new", str(int(pr.require("decoding", "max_new_tokens"))),
        "--no-generate",
        "--fit-dir", ctx["fit_dir"],
        # NO `arm.alpha or 1.0` HERE. That fallback turned a manifest alpha of 0.0 into a
        # launched alpha of 1.0 -- the arm submitted would not have been the arm declared, and
        # `assert_argv_agrees_with_analyzer` would have caught it only by luck. An alpha of 0 is
        # refused above (C-119) rather than quietly replaced.
        # THE ARM'S OWN MODE, not a literal. C5 is the only arm whose launched mode differs
        # from its manifest mode: `disabled` is `project_out` plus --pr057-disable-hooks, which
        # is what the analyzer's own `launch_command` writes, and `assert_argv_agrees_with_
        # analyzer` compares the two. Hard-coding "project_out" here was correct only while
        # `add` was unbuildable; with C4 constructible it would have launched the equal-magnitude
        # ORTHOGONAL control as a PROJECTION -- a different intervention under the control's
        # name, and one that would have passed the direction check.
        "--intervene", "%s:%s:%s:%g" % (con["intervene_direction"],
                                        ("project_out" if arm.mode == "disabled" else arm.mode),
                                        band, float(arm.alpha)),
        "--seed", str(seed),
        "--arm", arm.arm_id,
        "--tag", arm.tag(),
    ]
    if arm.scope == "S1":
        # '=' form on purpose: argparse reads a bare `-10` after a space as an option.
        argv.append("--pr057-edit-positions=%d" % ctx["rel_end"])
    if arm.mode == "disabled":
        argv.append("--pr057-disable-hooks")
    if not ctx.get("emit_liveness"):
        raise RunnerRefusal(
            "arm %s installs hooks and --emit-liveness was not given. Without "
            "--pr057-liveness-out the hooks write NO statistics and a dead hook is "
            "indistinguishable from a clean null (C-13). Refusing." % arm.arm_id)
    argv += ["--pr057-liveness-out", "auto"]
    _pb = ctx.get("probe")
    if _pb:
        # O1's SOURCE and TARGET come off the ArmSpec, which carries the manifest's own
        # source_concept/target_concept -- not from a literal here. The frozen definition is
        # "posterior mass on the SOURCE concept minus its mass on the TARGET concept".
        if not (arm.source_concept and arm.target_concept):
            raise RunnerRefusal(
                "arm %s has no source/target concept, so O1 (posterior(source) - "
                "posterior(target)) is undefined for it. A missing class must never be scored "
                "as zero." % arm.arm_id)
        argv += ["--pr057-probe-out", "auto",
                 "--pr057-probe-json", _pb["json"],
                 "--pr057-probe-sha", str(_pb["sha"]),
                 "--pr057-probe-read-layers", ",".join(str(int(x)) for x in _pb["read_layers"]),
                 "--pr057-probe-rel-end=%d" % int(_pb["rel_end"]),
                 "--pr057-probe-source", str(arm.source_concept),
                 "--pr057-probe-target", str(arm.target_concept)]
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

    The smoke stage emitted `--expect-n 670 --limit 40`: the first says "this arm scores the whole
    bound population", the second truncates it to 40. `score_behavior`'s row-count guard did its job
    and refused -- *"population is 40 rows, --expect-n says 670. A silently-shrunken sample is how
    R-18 happened."* -- but only after a 27-minute queue wait and a model load.

    That guard is the LAST line of defence and it fires on a GPU. This one fires in the runner,
    before anything is submitted, because two flags that must agree should be checked where they are
    built rather than where they are consumed.

    It refuses BOTH directions: an `--expect-n` larger than a `--limit` (the observed defect, a
    shrunken sample), and a `--limit` larger than `--expect-n` (which would silently widen the
    population past what the runner bound and audited).
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
            "the two must be equal whenever a limit is applied. Refusing here rather than letting "
            "score_behavior's row-count guard catch it after a queue wait and a model load."
            % (n, lim))


def assert_argv_agrees_with_analyzer(pr: Prereg, arm: ArmSpec, argv: Sequence[str],
                                     fit_dir: str) -> Dict[str, Any]:
    """The anti-drift check: the runner and the analyzer must describe the SAME arm.

    `launch_command()` is the analyzer's own idea of how this arm is launched. It is prose-adjacent
    (it carries `#` comments for the paths that do not exist yet) so it is parsed, not diffed, and
    the four things that decide WHICH EXPERIMENT RAN are compared: the bank, the arm label, the run
    tag, and the intervention's mode / layer band / alpha. The direction is compared through
    `DIRECTION_MAP`, which is the only sanctioned translation between the two vocabularies.
    """
    cmd = launch_command(pr, arm, fit_dir)
    got = {argv[i]: argv[i + 1] for i in range(0, len(argv) - 1) if argv[i].startswith("--")}
    out: Dict[str, Any] = {"arm_id": arm.arm_id, "analyzer_launch": cmd, "mismatches": []}

    def _flag(text: str, flag: str) -> Optional[str]:
        m = re.search(re.escape(flag) + r"\s+('?)([^\s']+)\1", text)
        return m.group(2) if m else None

    for flag in ("--bank", "--arm", "--tag"):
        a, b = _flag(cmd, flag), got.get(flag)
        if a != b:
            out["mismatches"].append("%s: analyzer=%r runner=%r" % (flag, a, b))
    a_int = _flag(cmd, "--intervene")
    if a_int and "--intervene" in got:
        a_dir, a_mode, a_band, a_alpha = a_int.split(":")
        r_dir, r_mode, r_band, r_alpha = got["--intervene"].split(":")
        want = DIRECTION_MAP.get(a_dir, "<unmapped>")
        if want != r_dir:
            out["mismatches"].append("direction: analyzer=%r maps to %r, runner used %r"
                                     % (a_dir, want, r_dir))
        # C5 is `project_out` plus --pr057-disable-hooks; the analyzer writes mode 'disabled' on
        # the ArmSpec and 'project_out' in its own command, so compare against the command.
        if a_mode != r_mode:
            out["mismatches"].append("mode: analyzer=%r runner=%r" % (a_mode, r_mode))
        if a_band != r_band:
            out["mismatches"].append("layer band: analyzer=%r runner=%r" % (a_band, r_band))
        if abs(float(a_alpha) - float(r_alpha)) > 0:
            out["mismatches"].append("alpha: analyzer=%r runner=%r" % (a_alpha, r_alpha))
    if out["mismatches"]:
        raise RunnerRefusal(
            "the runner's command for arm %s DISAGREES with the analyzer's launch_command: %s. "
            "Two files that disagree about what an arm is would be the whole failure mode of this "
            "phase." % (arm.arm_id, "; ".join(out["mismatches"])))
    out["ok"] = True
    return out


# ============================================================================================
# 5. STAGES, THE FIXED ORDER, AND THE SECOND KILL CONDITION
# ============================================================================================
#: `stage_selector` NOW LIVES IN THE ANALYZER (`scripts/dcs_ts_pr057_causal.py`) and is imported.
#: The analyzer needs the same partition to decide which arms are EXPECTED-ABSENT (amendment A10),
#: and two copies of "which arms belong to this stage" is exactly how the analyzer would come to
#: demand a run this runner never scheduled. One definition, imported by both.
stage_selector = AN.stage_selector


def stage_dir(state_root: str, stage: str, split: str) -> str:
    return os.path.join(state_root, "%s_%s" % (stage, split))


#: `A9`. The ONLY stages whose predecessor status may be satisfied by RE-DERIVING constructibility
#: instead of by a terminal record. An explicit allowlist, not a general "an empty stage is fine":
#: the rejected alternative was letting a zero-arm stage write a `DONE.json`, which reopens exactly
#: the silent-success hole `run_stage` refuses at (":stage has ZERO constructible arms").
#: `h1` is here because its 18 arms are unbuildable for two independent reasons -- mode `patch`
#: has no `score_behavior` code path, and R-116/C-112 measured the donor concept installing in 0 of
#: 113 domains -- so no `h1/DONE.json` can ever exist and none may ever be hand-written.
#: This is RE-DERIVED AT EVERY LAUNCH, so it cannot be asserted by hand, and it RE-ARMS the moment
#: one h1 arm becomes constructible. That is the property an allowlist of "stages known
#: unbuildable" would not have.
RE_DERIVABLE_PREDECESSORS = ("h1",)
PREDECESSOR_BY_CONSTRUCTION = "CANNOT_RUN_BY_CONSTRUCTION"


def stage_constructibility_state(pr: Prereg, stage: str,
                                 payload_keys: Optional[Sequence[str]]) -> Dict[str, Any]:
    """Re-derive, from `constructibility`, whether a stage has ANY arm that could run today.

    THE RISK THIS CARRIES, STATED. After A9 a bug in the constructibility path can OPEN a gate
    rather than only refuse an arm. Two mitigations ship with it: (a) the mutation
    `h1 arm made constructible -> the gate REFUSES again`, and (b) the refusal below -- if any
    arm's unbuildability turns on the direction PAYLOAD and the payload was not readable, this
    function refuses instead of deciding. A gate that opens on missing evidence is the failure.
    """
    arms = [x for x in build_arm_manifest(pr) if stage_selector(pr, stage)(x)]
    if not arms:
        raise ZeroBinding("stage %r selects ZERO arms; its constructibility is undefined" % stage)
    per: Dict[str, Any] = {}
    buildable: List[str] = []
    payload_dependent: List[str] = []
    for arm in arms:
        con = constructibility(pr, arm, payload_keys or ())
        if con["constructible"]:
            buildable.append(arm.arm_id)
        else:
            per[arm.arm_id] = con["reasons"]
            if any("payload" in r for r in con["reasons"]):
                payload_dependent.append(arm.arm_id)
    if payload_keys is None and payload_dependent:
        raise RunnerRefusal(
            "the constructibility of %d %s arm(s) (%s) turns on the direction PAYLOAD, which "
            "could not be read. Refusing to decide the launch order on evidence that is missing: "
            "a gate that opens because it could not look is the failure this guard exists to "
            "prevent." % (len(payload_dependent), stage, payload_dependent[:4]))
    return {"stage": stage, "n_selected": len(arms), "n_constructible": len(buildable),
            "constructible_arm_ids": buildable, "unbuildable_reasons": per,
            "state": ("RUNNABLE" if buildable else PREDECESSOR_BY_CONSTRUCTION)}


def assert_stage_order(state_root: str, stage: str, split: str,
                       pr: Optional[Prereg] = None,
                       payload_keys: Optional[Sequence[str]] = None) -> Dict[str, Any]:
    """`Q0 -> Q1 -> smoke -> H1 -> H2`, enforced by reading the earlier stages' own DONE.json.

    A comment cannot stop a job being submitted out of order; this can. `q0` is not a job (it is a
    gate over the PHASE 7 runs) so it has no DONE.json of its own and is checked separately by
    `q0_gate`.

    `A9`, 2026-09-08. h1 can NEVER write a `DONE.json`: `run_stage` refuses a stage with zero
    constructible arms BEFORE `write_terminal`, and that refusal is correct -- an empty stage that
    reports success is the failure this whole design exists to prevent. So the predecessor is
    re-derived instead: if a stage on `RE_DERIVABLE_PREDECESSORS` has ZERO constructible arms at
    THIS launch, it satisfies the order as `CANNOT_RUN_BY_CONSTRUCTION`, recorded with the per-arm
    reasons. If ANY of its arms is constructible, the gate refuses exactly as it did before -- a
    stage that COULD run must run. No terminal record is written for it, by hand or otherwise.
    """
    need = {"q1": [], "smoke": ["q1"], "h1": ["q1", "smoke"], "h2": ["q1", "smoke", "h1"]}
    if stage not in need:
        raise RunnerRefusal("stage %r has no declared predecessors" % stage)
    missing, by_construction = [], {}
    for pre in need[stage]:
        hits = []
        for cand in os.listdir(state_root) if os.path.isdir(state_root) else []:
            if cand.startswith(pre + "_") and os.path.exists(
                    os.path.join(state_root, cand, "DONE.json")):
                d = json.load(open(os.path.join(state_root, cand, "DONE.json")))
                if d.get("status") == "ok":
                    hits.append(cand)
        if hits:
            continue
        if pr is not None and pre in RE_DERIVABLE_PREDECESSORS:
            st = stage_constructibility_state(pr, pre, payload_keys)
            if st["state"] == PREDECESSOR_BY_CONSTRUCTION:
                by_construction[pre] = st
                continue
            raise RunnerRefusal(
                "stage %r was requested and predecessor %r has no DONE.json -- but %d of its %d "
                "arms ARE constructible today (%s). A stage that COULD run must run: the "
                "by-construction exemption is for a stage nothing can build, and re-deriving it "
                "at every launch is what makes it re-arm the moment that changes."
                % (stage, pre, st["n_constructible"], st["n_selected"],
                   st["constructible_arm_ids"][:4]))
        missing.append(pre)
    if missing:
        raise RunnerRefusal(
            "stage %r was requested but %s has not completed (no %s/<stage>_*/DONE.json with "
            "status ok). The launch order Q0 -> Q1 -> smoke(Q7) -> H1 -> H2 is fixed and is not "
            "negotiable: Q1 decides whether the design can answer at all, and running the "
            "confirmatory arms first would read TEST before that question was asked."
            % (stage, missing, state_root))
    for pre, st in sorted(by_construction.items()):
        print("[pr057] launch order: predecessor %r satisfied as %s -- 0 of %d arms constructible; "
              "no DONE.json exists for it and none was written"
              % (pre, PREDECESSOR_BY_CONSTRUCTION, st["n_selected"]), flush=True)
    return {"stage": stage, "predecessors_satisfied": need[stage],
            "predecessors_by_construction": by_construction}


def q0_gate(pr: Prereg, runs_root: str, tag_prefix: str) -> Dict[str, Any]:
    """Q0: the PHASE 7 readout has LANDED on ALL SIX banks and the semantic channel is ENGAGED.

    The FIRST kill condition in the frozen file: a disengaged `semantic_one_word` channel means
    there is no y to move and the phase would reproduce R-097 at GPU cost. `option_mass_gate` is
    the analyzer's, not a second copy.
    """
    channel = str(pr.require("population", "query_kind_primary"))
    per_bank, missing, disengaged = {}, [], []
    for key in sorted(pr.require("population", "banks")):
        tag = "%s_%s" % (tag_prefix, key)
        try:
            d = _find_run(runs_root, tag)
        except (PreregError, FileNotFoundError, OSError):
            missing.append(tag)
            continue
        try:
            g = option_mass_gate(json.load(open(os.path.join(d, "summary.json"))), channel)
        except Refusal as e:
            per_bank[key] = {"run_dir": d, "ok": False, "detail": str(e)[:160]}
            disengaged.append(key)
            continue
        per_bank[key] = {"run_dir": d, **g}
        if not g["ok"]:
            disengaged.append(key)
    ok = (not missing) and (not disengaged) and len(per_bank) == len(pr.require("population", "banks"))
    return {"ok": ok, "n_banks": len(pr.require("population", "banks")), "per_bank": per_bank,
            "missing_tags": missing, "disengaged": disengaged,
            "detail": ("" if ok else
                       "Q0 IS NOT SATISFIED: %d bank(s) have no COMPLETE PHASE 7 run (%s) and "
                       "%d show the %s channel disengaged. Without it O2 DOES NOT EXIST and the "
                       "phase repeats R-097 exactly."
                       % (len(missing), missing[:6], len(disengaged), channel))}


KILL_MOVED = "H1_MOVED_O2"
KILL_NOT_MOVED = "H1_DID_NOT_MOVE_O2"
KILL_UNAVAILABLE = "H1_NOT_AVAILABLE"


def h1_kill_state(pr: Prereg, runs_root: str, scope: str,
                  arms: Sequence[ArmSpec], baseline_rows_by_tag) -> Dict[str, Any]:
    """The frozen file's SECOND kill condition, at one site (scope level).

    "if the H1 upper bound does not move O2, H2a/H2b are NOT submitted at that site, because a
    surgical edit cannot be expected to do what replacing the entire state could not."

    Three states, and the third is NOT the second:
      MOVED        -- proceed.
      NOT_MOVED    -- the H2 arms at this site are NOT SUBMITTED and are reported UNINFORMATIVE.
      UNAVAILABLE  -- no H1 arm ran at this site at all. Under C-112/R-116 the H1 donor
                      population on this bank is EMPTY, so H1 is unconstructible and its silence
                      is CANNOT ANSWER BY CONSTRUCTION -- which is not evidence that a surgical
                      edit will fail, and mandate 10.2 (H2a) is the PRIMARY test in its own right.
                      The H2 arms proceed, and this state is recorded on every one of them.
    """
    mde = float(pr.require("power", "declared_minimum_meaningful_effect",
                           "o2_semantic_logodds_shift"))
    h1 = [a for a in arms if a.hypothesis == "H1" and a.scope == scope]
    ran = []
    for a in h1:
        try:
            ran.append((a, load_arm_run(_find_run(runs_root, a.tag()))))
        except (PreregError, Refusal, FileNotFoundError, OSError):
            continue
    if not ran:
        return {"scope": scope, "state": KILL_UNAVAILABLE, "n_h1_arms_run": 0,
                "declared_mde": mde, "note": C112_PRIMARY_IS_10_2,
                "detail": "no H1 arm at scope %s produced a COMPLETE run; H1 is exploratory and "
                          "unconstructible on this bank (R-116: the source concept installs in "
                          "0/113 domains). The kill condition cannot fire on an arm that was "
                          "never able to run, and it is NOT read as 'H1 did not move O2'." % scope}
    deltas = {}
    for a, run in ran:
        lg = liveness_gate(annotate_liveness(run["liveness"], a), a.arm_id,
                           expect_enabled=a.expect_enabled)
        if not lg["live"]:
            raise RunnerRefusal(
                "the kill condition would be decided by arm %s, whose hook liveness is UNCLEAN "
                "(%s). A null behind an unverified hook is VOID, not a negative, and it is "
                "certainly not a licence to cancel the surgical arms." % (a.arm_id, lg["reasons"][:2]))
        base = baseline_rows_by_tag(a)
        deltas[a.arm_id] = per_domain_delta(run["results"], base)
    means = {k: (sum(v.values()) / len(v)) for k, v in deltas.items() if v}
    if not means:
        raise ZeroBinding("the kill condition bound zero domains of O2 at scope %s" % scope)
    biggest = max(abs(m) for m in means.values())
    moved = biggest >= mde
    return {"scope": scope, "state": KILL_MOVED if moved else KILL_NOT_MOVED,
            "n_h1_arms_run": len(ran), "declared_mde": mde,
            "per_arm_domain_mean_delta_o2": means, "max_abs_domain_mean_delta": biggest,
            "detail": ("H1 moved O2 by %.4f nats >= the declared %.2f-nat effect" % (biggest, mde)
                       if moved else
                       "H1 -- which replaces the WHOLE state -- moved O2 by only %.4f nats, below "
                       "the declared %.2f. The H2 arms at this site are NOT SUBMITTED and are "
                       "reported UNINFORMATIVE, never as negatives." % (biggest, mde))}


def apply_kill_condition(arms: Sequence[ArmSpec],
                         states: Dict[str, Dict[str, Any]]) -> Tuple[List[ArmSpec], List[Dict[str, Any]]]:
    """Remove the H2 arms at a killed site. Returns (submit, not_submitted_records)."""
    submit, skipped = [], []
    for a in arms:
        st = states.get(a.scope, {}).get("state")
        if a.hypothesis in ("H2a", "H2b") and st == KILL_NOT_MOVED:
            skipped.append({"arm_id": a.arm_id, "status": "NOT_SUBMITTED_UNINFORMATIVE",
                            "scope": a.scope, "kill_state": st,
                            "why": states[a.scope]["detail"],
                            "_wording": "UNINFORMATIVE, NOT NEGATIVE. The site's upper bound did "
                                        "not move the outcome, so a surgical null there would be "
                                        "a statement about the site, not about the axis."})
        else:
            submit.append(a)
    return submit, skipped


def assert_kill_condition_honoured(submit: Sequence[ArmSpec],
                                   states: Dict[str, Dict[str, Any]]) -> None:
    """Refuse a submission list that contains an arm the kill condition removed."""
    bad = [a.arm_id for a in submit
           if a.hypothesis in ("H2a", "H2b")
           and states.get(a.scope, {}).get("state") == KILL_NOT_MOVED]
    if bad:
        raise RunnerRefusal(
            "the submission list contains %d H2 arm(s) at a site where the H1 upper bound did NOT "
            "move O2 (%s). The frozen file's second kill condition says they are NOT submitted. "
            "Submitting them anyway would spend GPU time producing nulls that are uninformative "
            "by construction and would be read as negatives." % (len(bad), bad[:4]))


# ============================================================================================
# 6. OUTCOMES USED BY THE RUNNER ITSELF (Q1's decision and the kill condition)
# ============================================================================================
def per_domain_delta(arm_rows: Sequence[Dict[str, Any]],
                     base_rows: Sequence[Dict[str, Any]]) -> Dict[str, float]:
    """Domain-mean change in O2 (`semantic_logodds`) between an arm and the untouched baseline.

    Paired on `prompt_id`, which is the only join that keeps the contrast within-prompt (the
    nuisance floor of 0.0 in the frozen file is *by construction* of that pairing). Refuses a zero
    bind and refuses a row the baseline does not carry.
    """
    o2_arm = o2_projection_out_from_rows(list(arm_rows))          # validates the fields exist
    o2_base = o2_projection_out_from_rows(list(base_rows))
    assert o2_arm["computable"] and o2_base["computable"]
    base = {r["prompt_id"]: float(r["semantic_logodds"]) for r in base_rows}
    per: Dict[str, List[float]] = {}
    unmatched = 0
    for r in arm_rows:
        pid = r["prompt_id"]
        if pid not in base:
            unmatched += 1
            continue
        per.setdefault(r["domain"], []).append(float(r["semantic_logodds"]) - base[pid])
    if unmatched:
        raise RunnerRefusal(
            "%d of %d intervened rows have NO baseline row with the same prompt_id. An unpaired "
            "contrast is not the within-prompt contrast this design's nuisance floor rests on."
            % (unmatched, len(arm_rows)))
    if not per:
        raise ZeroBinding("the arm-vs-baseline delta bound ZERO domains")
    return {d: sum(v) / len(v) for d, v in per.items()}


# ============================================================================================
# 7. LIVENESS -- gated twice, annotated once, never rewritten
# ============================================================================================
LIVENESS_REQUIRED_KEYS = ("mode", "enabled", "layer", "n_forward_calls", "hook_fired_count",
                          "n_destination_rows", "n_cells_edited_realised",
                          "n_cells_edited_expected", "orthogonal_residual_delta_l2",
                          "projection_removed_l2", "max_abs_delta", "seq_len")


def annotate_liveness(records: Sequence[Dict[str, Any]], arm: ArmSpec) -> List[Dict[str, Any]]:
    """An ANNOTATED COPY for the analyzer's consumer-side gate. See `DEFECT_LIVENESS_SCHEMA`.

    Two annotations, both stated rather than smuggled:
      * the single-site `resolved_absolute_index` list of one is unpacked to an int, so
        `audit_end_relative` can perform the `seq_len + rel_end` identity it exists for.
    `n_cells_edited_expected` is NO LONGER INVENTED HERE (C-117 is closed in the producer). The
    hook counts it from the tensor each forward was handed, before the write; overwriting that
    measured number with `n_destination_rows` -- which the producer only increments AFTER a
    successful write -- would make `realised == expected` true by construction again and hide the
    very mismatch the frozen `void_if` asks about. A record that lacks it is a REFUSAL.
    An all-position (S2) edit has no single rel_end and is NOT given one: it is marked
    `_end_relative_audit = 'not applicable (all-position edit)'` instead, because inventing a
    rel_end to make an audit pass is the audit failing.
    """
    out = []
    for r in records:
        miss = [k for k in LIVENESS_REQUIRED_KEYS if k not in r]
        if miss:
            raise RunnerRefusal(
                "a liveness record from arm %s is missing %s. A record that grows keys as it goes "
                "cannot distinguish 'the hook never fired' from 'the consumer read a key the "
                "producer never wrote'." % (arm.arm_id, miss))
        d = dict(r)
        d["_expected_rule"] = ("n_cells_edited_expected is the PRODUCER's own count, taken from "
                               "the tensor each forward was handed before the write (C-117)")
        idx = r.get("resolved_absolute_index")
        if isinstance(idx, (list, tuple)):
            if len(idx) == 1:
                d["resolved_absolute_index"] = int(idx[0])
            else:
                d["_end_relative_audit"] = ("not applicable (%d edited positions in one record)"
                                            % len(idx))
        if r.get("rel_end") is None:
            # MODE-AWARE, because "no rel_end" means opposite things on different arms
            # (2026-09-08). An ALL-POSITION edit has no single site and is exempt. A DISABLED-HOOK
            # bridge records no site of its own -- it discarded the write, and the wrapped hook's
            # own record is not the one persisted. But a LIVE SINGLE-POSITION arm with no rel_end
            # is a site that was edited and never written down, and blanket-labelling it "all
            # positions" excused it from the end-relative audit while calling it a different
            # scope than it ran at.
            _m = str(r.get("mode") or "")
            if _m.endswith("_single") and arm.expect_enabled:
                raise RunnerRefusal(
                    "arm %s is a LIVE SINGLE-POSITION edit (mode %r) whose liveness record "
                    "carries NO rel_end. The token edited is not written down, the "
                    "`resolved_absolute_index == seq_len + rel_end` audit cannot run, and a "
                    "record with no site must not be excused as an all-position edit."
                    % (arm.arm_id, _m))
            d["_end_relative_audit"] = (
                "not applicable (all-position edit has no single rel_end)"
                if _m.endswith("_all") else
                "not applicable (mode %r records no single rel_end; a disabled-hook bridge "
                "discarded its write and carries no site of its own)" % _m)
        out.append(d)
    return out


#: Where each field of the frozen `persist_per_row_and_per_arm.fields` list actually lives. The
#: KEYS are the config's own strings, so a field added to the frozen list that this runner has no
#: location for is a REFUSAL rather than a quietly unpersisted quantity. `None` means "not
#: applicable to this arm", and the reason is required alongside it.
PERSIST_LOCATION = {
    "activation_norm_pre": ("row", "activation_norm_pre"),
    "activation_norm_post": ("row", "activation_norm_post"),
    "norm_ratio": ("row", "norm_ratio"),
    "projection_removed_l2": ("row", "projection_removed_l2"),
    "frac_cellmean_spread_removed": ("arm", "realized_dose"),
    "cosine(h_pre, h_post)": ("row", "cos_pre_post"),
    "cosine(edit, v_used)": ("arm", "cos_edit_vs_direction"),
    "orthogonal_residual_delta_l2 (H2b: must be 0 to tolerance)":
        ("row", "orthogonal_residual_delta_l2"),
    "layer(s) edited": ("row", "layer"),
    "token position edited (as rel_end AND as the resolved absolute index)":
        ("row", "rel_end + resolved_absolute_index"),
    # THE PROMPT PROPERTY, NOT THE EDIT PROPERTY (2026-09-08). `occurrence_index_per_edit` is
    # the ordinal of the occurrence each EDITED position sits at, and an all-position edit has
    # no edited position to speak of -- it edits all of them -- so it is null there BY DESIGN.
    # `occurrence_index` is where the codeword IS in this prompt, which is what the frozen list
    # names ("occurrence index of the codeword") and which is well defined on every mode. Looking
    # the frozen field up in the per-edit key is what refused the first S2 arm ever run.
    "occurrence index of the codeword": ("row", "occurrence_index"),
    "n_subtokens": ("row", "n_subtokens_per_occurrence"),
    "hook_fired_count": ("row", "hook_fired_count"),
    "n_destination_rows": ("row", "n_destination_rows"),
    "n_cells_edited_realised": ("row", "n_cells_edited_realised"),
    "n_cells_edited_expected": ("row", "n_cells_edited_expected"),
    "direction_file_sha256 (recomputed at load, not pinned in advance)":
        ("arm", "direction_file_sha256"),
    "control_draw_seed": ("arm", "control_draw_seed"),
    "per-draw output sha256": ("arm", "output_sha256"),
}


def persist_contract_report(pr: Prereg, arm: ArmSpec, record: Dict[str, Any],
                            gate: Dict[str, Any]) -> Dict[str, Any]:
    """Check, field by field, that this arm persisted what the FROZEN file says it must.

    `persist_per_row_and_per_arm` is mandate 10.3's "verify intervention magnitude" made
    machine-readable. Reading the list and hoping is what B-020 is; this reads the list and looks
    each field up where it is supposed to be.
    """
    out, missing, unmapped = {}, [], []
    for f in pr.require("persist_per_row_and_per_arm", "fields"):
        loc = PERSIST_LOCATION.get(f)
        if loc is None:
            unmapped.append(f)
            continue
        where, key = loc
        if f.startswith("orthogonal_residual_delta_l2"):
            # MEASURED, NOT WAIVED (C-117). The frozen list names this field for H2b, where it is
            # I-N7; but a project_out edit is `alpha*(h.d)d`, so its component orthogonal to `d`
            # must be zero too, and `pair_common` now records it on every edit. What used to be a
            # "not applicable to this arm" note is a number.
            _v = record.get("orthogonal_residual_delta_l2")
            if _v is None:
                if arm.expect_enabled:
                    raise RunnerRefusal(
                        "arm %s is a LIVE edit and its liveness record carries no "
                        "`orthogonal_residual_delta_l2`. An unmeasured orthogonal residual is not "
                        "a preserved one -- and the analyzer's I-N7 gate used to default the "
                        "absence to NaN and report a physical violation nobody observed (C-117)."
                        % arm.arm_id)
                out[f] = {"present": None, "where": "row",
                          "note": "the disabled-hook bridge discarded its write, so there is no "
                                  "edit whose orthogonal component could have been disturbed"}
            else:
                out[f] = {"present": True, "where": "row",
                          "key": "orthogonal_residual_delta_l2", "value": float(_v)}
            continue
        if f.startswith("occurrence index"):
            # A PROPERTY OF THE PROMPT, REQUIRED OF EVERY ARM, AND NEVER A CLAIM ABOUT SCOPE.
            # `pair_common.occurrence_annotation` populates it on every mode: on a single-position
            # edit it is the ordinal of the occurrence the hook edited; on an all-position edit it
            # is the codeword_last occurrence of the prompt -- the same value an S1 arm records
            # for the same row -- carried with `occurrence_index_is_prompt_property=True` so no
            # reader can take it for a claim that the edit was scoped to that occurrence.
            _v = record.get("occurrence_index")
            _prop = record.get("occurrence_index_is_prompt_property")
            _ok = ("occurrence_index" in record
                   and (_v is not None or not arm.expect_enabled))
            out[f] = {"present": bool(_ok), "where": "row", "key": "occurrence_index",
                      "value": (_v if isinstance(_v, (int, float, str)) else None),
                      "is_prompt_property": _prop,
                      "per_edit": record.get("occurrence_index_per_edit"),
                      "source": record.get("occurrence_index_source"),
                      "note": ("an all-position edit has no edit site, so this is the codeword's "
                               "own occurrence ordinal in the PROMPT and the edit was NOT scoped "
                               "to it" if _prop else "")}
            if not _ok:
                missing.append(f)
            continue
        if where == "row":
            if f.startswith("token position"):
                # A FABRICATED SITE IS WORSE THAN A NULL ONE. An all-position record that carries
                # a rel_end or a resolved_absolute_index describes an intervention nobody ran.
                # `pair_common.project_out_liveness_violations` refuses it in the producer; it is
                # refused here too, because two independent checkers is what this contract is for.
                if str(record.get("mode") or "").endswith("_all"):
                    _fab = [k for k in ("rel_end", "resolved_absolute_index")
                            if record.get(k) is not None]
                    if _fab:
                        raise RunnerRefusal(
                            "arm %s is an ALL-POSITION edit whose liveness record carries %s. "
                            "There is no single edit site on an all-position arm; a site "
                            "recorded for one is invented, and it would pass the end-relative "
                            "audit while describing an intervention that was never run."
                            % (arm.arm_id, _fab))
                ok = ("rel_end" in record) and ("resolved_absolute_index" in record)
            else:
                # PRESENCE IS NOT ENOUGH. `hook_stats_dict` pre-populates every key with None, so
                # `key in record` is trivially true -- a check that reads the producer's own null
                # field and asserts None == None. A LIVE arm must carry a VALUE; the disabled-hook
                # bridge legitimately has none for the edit quantities it never made.
                ok = (key in record) and (record.get(key) is not None or not arm.expect_enabled)
            val = record.get(key)
            if ok and f.startswith("token position") and record.get("rel_end") is None:
                # THE NOTE MUST NAME THE ARM'S OWN MODE (2026-09-08). "all positions (S2)" was
                # printed for every record without a rel_end, including the C5 disabled-hook
                # bridge over a SINGLE-position hook -- an S1 arm whose contract report claimed
                # S2 scope.
                _m = str(record.get("mode") or "")
                out[f] = {"present": True, "where": where,
                          "value": ("all positions (S2)" if _m.endswith("_all")
                                    else "no site recorded (mode %r)" % _m),
                          "note": ("an all-position edit has no single rel_end; `positions` is "
                                   "every position by construction" if _m.endswith("_all") else
                                   "the disabled-hook bridge discarded its write and records no "
                                   "site of its own; this is NOT an all-position edit")}
                continue
        else:
            ok = gate.get(key) not in (None, {}, "")
            val = gate.get(key)
            if f.startswith("frac_cellmean_spread_removed") and gate.get("realized_dose_note"):
                out[f] = {"present": None, "where": where, "note": gate["realized_dose_note"]}
                continue
        out[f] = {"present": bool(ok), "where": where, "key": key,
                  "value": (val if isinstance(val, (int, float, str)) else None)}
        if not ok:
            missing.append(f)
    if unmapped:
        raise RunnerRefusal(
            "the frozen persist contract names %d field(s) this runner has no location for (%s). "
            "A field nobody knows where to look for is an unpersisted quantity, not a satisfied "
            "requirement." % (len(unmapped), unmapped[:3]))
    if missing:
        raise RunnerRefusal(
            "arm %s did NOT persist %d field(s) the frozen `persist_per_row_and_per_arm` list "
            "requires: %s" % (arm.arm_id, len(missing), missing))
    return {"n_fields": len(out), "n_missing": 0, "per_field": out}


def verify_arm_artifacts(pr: Prereg, arm: ArmSpec, run_dir: str,
                         expect_rows: Optional[int],
                         con_dir: Optional[str] = None,
                         direction_sha: Optional[str] = None) -> Dict[str, Any]:
    """Everything that must be TRUE about a finished arm before the next one is started."""
    run = load_arm_run(run_dir)                       # refuses a partial run (no DONE.json)
    n_rows = len(run["results"])
    if n_rows == 0:
        raise RunnerRefusal("arm %s wrote ZERO result rows into %s" % (arm.arm_id, run_dir))
    if expect_rows and n_rows != expect_rows:
        raise RunnerRefusal(
            "arm %s wrote %d rows; the runner bound %d. A silently shrunken sample is how R-18 "
            "happened." % (arm.arm_id, n_rows, expect_rows))
    recs = run["liveness"]
    if not recs:
        raise RunnerRefusal(
            "arm %s produced NO %s. A null behind an unrecorded hook is VOID, not a negative -- "
            "and an empty liveness file reads to a consumer as 'no violations'."
            % (arm.arm_id, CONTRACT_LIVENESS))
    # (a) the PRODUCER's own gate -- the same function score_behavior aborts on, run again here so
    #     a record that reached the file without aborting still cannot pass silently.
    import pair_common as pc
    prod = [{"i": i, "violations": pc.project_out_liveness_violations(r)}
            for i, r in enumerate(recs)]
    prod_bad = [p for p in prod if p["violations"]]
    # (b) the CONSUMER's gate -- the analyzer's, on the annotated copy.
    ann = annotate_liveness(recs, arm)
    cons = liveness_gate(ann, arm.arm_id, expect_enabled=arm.expect_enabled)
    # (c) the end-relative index audit, where it applies.
    auditable = [r for r in ann if "_end_relative_audit" not in r]
    aud = audit_end_relative(auditable) if auditable else {
        "ok": None, "n_records": 0,
        "witness_note": "no record carries a single (rel_end, resolved_absolute_index) pair; the "
                        "end-relative identity is not auditable on an all-position edit"}
    # (d) THE PER-DRAW OUTPUT HASH the frozen file's persist list names, and which control C1's
    #     five-distinct-hashes gate needs. With --no-generate there is no gens.jsonl to hash, so
    #     the hash is over the OUTCOME FIELDS of results.jsonl, sorted by prompt_id, with the
    #     rule written next to the number rather than left to be inferred.
    out_sha = hashlib.sha256(
        "\n".join(sorted("%s|%.10g|%.10g|%.10g"
                         % (r.get("prompt_id"), float(r.get("logp_concept", float("nan"))),
                            float(r.get("logp_codeword", float("nan"))),
                            float(r.get("semantic_logodds", float("nan"))))
                         for r in run["results"])).encode()).hexdigest()
    # (e) THE REALISED DOSE. `persist_per_row_and_per_arm` lists frac_cellmean_spread_removed;
    #     score_behavior computes it per (direction, layer, alpha) into metadata.json
    #     `realized_dose` -- but ONLY for a direction that is a payload key, so a norm-matched
    #     control (random@v_x) legitimately has none. The distinction is recorded, not blurred.
    meta_path = os.path.join(run_dir, "metadata.json")
    meta = json.load(open(meta_path)) if os.path.exists(meta_path) else {}
    dose = (meta.get("realized_dose") if isinstance(meta.get("realized_dose"), dict)
            else (meta.get("extra") or {}).get("realized_dose"))
    derived = "@" in (con_dir or "")
    if arm.expect_enabled and not derived and not dose:
        raise RunnerRefusal(
            "arm %s recorded NO realized_dose in metadata.json, so "
            "frac_cellmean_spread_removed -- a field `persist_per_row_and_per_arm` requires -- "
            "does not exist for it and the realised dose of this edit is unrecorded."
            % arm.arm_id)
    gate = {"arm_id": arm.arm_id, "run_dir": run_dir, "n_rows": n_rows,
            "output_sha256": out_sha,
            "output_sha256_rule": ("sha256 over sorted 'prompt_id|logp_concept|logp_codeword|"
                                   "semantic_logodds' lines of results.jsonl (--no-generate "
                                   "leaves no gens.jsonl to hash)"),
            "realized_dose": dose,
            "realized_dose_note": ("a norm-matched control's direction is DERIVED at hook-install "
                                   "time and is not a payload key, so it has no cellmean dose"
                                   if derived else ""),
            "n_liveness_records": len(recs), "expect_enabled": arm.expect_enabled,
            "producer_gate": {"n_records": len(recs), "n_violating": len(prod_bad),
                              "first": prod_bad[:3]},
            "consumer_gate": cons, "end_relative_audit": aud,
            "hook_fired_count_total": sum(int(r.get("hook_fired_count", 0)) for r in recs),
            "n_cells_edited_realised_total": sum(int(r.get("n_cells_edited_realised", 0))
                                                 for r in recs),
            "arm_manifest_echo_present": run["arm_manifest"] is not None,
            "direction_file_sha256": direction_sha,
            "control_draw_seed": (arm.control_draw_seed
                                  if arm.control_draw_seed is not None
                                  else int(pr.require("seeds", "control_draws"))),
            "cos_edit_vs_direction": (
                "+/-1 BY CONSTRUCTION for project_out: the edit is alpha * (h.d) * d, i.e. "
                "exactly along the unit direction. Also +/-1 by construction for add: the edit "
                "is alpha * d. In BOTH cases the claim is no longer only structural -- "
                "`orthogonal_residual_delta_l2` in the record MEASURES the component of the "
                "realised change that is not along d, and a record without it refuses."),
            "_schema_note": DEFECT_LIVENESS_SCHEMA}
    gate["persist_contract"] = persist_contract_report(pr, arm, ann[0], gate)
    with open(os.path.join(run_dir, ARM_GATE_FILE), "w") as fh:
        json.dump(gate, fh, indent=2, default=str)
    if prod_bad:
        raise RunnerRefusal("arm %s: the PRODUCER's liveness gate refuses %d/%d record(s): %s"
                            % (arm.arm_id, len(prod_bad), len(recs), prod_bad[:2]))
    if not cons["live"]:
        raise RunnerRefusal("arm %s: the analyzer's liveness gate refuses it: %s"
                            % (arm.arm_id, cons["reasons"]))
    if aud.get("ok") is False:
        raise RunnerRefusal(
            "arm %s: %d edit index/indices are not len(input_ids)+rel_end. An absolute index "
            "reused across examples is this repository's twice-recorded bug class."
            % (arm.arm_id, aud["n_absolute_index_violations"]))
    if run["arm_manifest"] is None:
        raise RunnerRefusal("arm %s wrote no %s -- there is no record of what the run believed it "
                            "was doing." % (arm.arm_id, CONTRACT_ARM))
    return gate


# ============================================================================================
# 8. THE PROBE (O1) -- accepted as a flag, refused as a capability, with the reason
# ============================================================================================
def probe_gate(probe_json: str) -> Dict[str, Any]:
    """`--emit-probe`. Both C-118 blockers are checked; neither is assumed away.

    The ATTRIBUTION blocker is closed in code (see `DEFECT_PROBE_ATTRIBUTION`), so it is no
    longer a reason. The ARTIFACT blocker is checked here on every call, against the file on
    disk: a probe that does not load, or that its producer never self-verified, is still a
    refusal, and `--emit-probe` must never write a file O1 cannot be formed from.
    """
    reasons: List[str] = []
    path = probe_json if os.path.isabs(probe_json) else repo_path(probe_json)
    sha = None
    fit_layer = None
    try:
        fp = load_frozen_probe(path)
        artifact = "present"
        sha, fit_layer = fp.sha256, fp.layer
    except (Refusal, PreregError, OSError) as e:
        artifact = "absent"
        reasons.append("%s (%s)" % (DEFECT_PROBE_ARTIFACT, str(e).splitlines()[0][:120]))
    return {"ok": not reasons, "probe_artifact": artifact, "path": path, "reasons": reasons,
            "probe_sha256": sha, "probe_fit_layer": fit_layer,
            "attribution": DEFECT_PROBE_ATTRIBUTION}


# ============================================================================================
# 9. DIRECTIONS -- provenance, sha, and the pin the frozen file could not carry
# ============================================================================================
def direction_gate(pr: Prereg, fit_dir: str, expect_sha: Optional[str] = None) -> Dict[str, Any]:
    """Resolve the payload the LOADER will actually load, recompute its sha256, and check TRAIN-only.

    `direction_provenance_gate` is the analyzer's; the filename resolution is `score_behavior`'s
    (`directions_fit_dev.pt`, then `directions_fit_heldout.pt`). See `DEFECT_C113` for why the
    frozen config's `directions.artifact.path` is not used.
    """
    d = fit_dir if os.path.isabs(fit_dir) else repo_path(fit_dir)
    if not os.path.isdir(d):
        raise RunnerRefusal("--fit-dir %r is not a directory. %s" % (fit_dir, DEFECT_C113))
    cand = [os.path.join(d, n) for n in ("directions_fit_dev.pt", "directions_fit_heldout.pt")]
    hit = next((c for c in cand if os.path.exists(c)), None)
    if hit is None:
        raise RunnerRefusal(
            "no direction payload in %s: score_behavior loads directions_fit_dev.pt (then "
            "directions_fit_heldout.pt) from --fit-dir. %s" % (d, DEFECT_C113))
    sha = sha256_file(hit)
    if expect_sha and sha != expect_sha:
        raise RunnerRefusal(
            "the direction payload sha256 is %s but %s was pinned. The axis this phase projects "
            "out is not the axis the pin names; refusing." % (sha, expect_sha))
    import torch
    payload = torch.load(hit, map_location="cpu", weights_only=False)
    meta = payload.get("meta") or {}
    assign = load_split(pr)
    prov = AN.direction_provenance_gate({"fit_domains": meta.get("fit_domains")}, assign, hit)
    if not prov["ok"]:
        raise RunnerRefusal("the direction payload fails its provenance gate: %s" % prov)
    return {"path": hit, "sha256": sha, "provenance": prov,
            "payload_keys": sorted(payload.keys()),
            "direction_keys": sorted(k for k in payload if k.startswith("v_")),
            "layers": sorted(int(x) for x in (payload.get("layers") or [])),
            "_note": DEFECT_C113}


# ============================================================================================
# 10. THE MODEL CACHE -- the one monkeypatch, counted and reported
# ============================================================================================
class ModelCache:
    """Memoise `ds_common.load_model` so 54 arms load the weights ONCE.

    This is the whole point of the runner, so the count is an ARTIFACT field rather than a hope:
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
                print("[pr057] model cache HIT (%d) -- weights are NOT reloaded" % cache.n_hits,
                      flush=True)
                return cache._cache[key]
            cache.n_loads += 1
            print("[pr057] model LOAD #%d %r" % (cache.n_loads, key[:3]), flush=True)
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
# 11. THE RESUMABLE MANIFEST
# ============================================================================================
def manifest_load(sdir: str, runs_root: str) -> Dict[str, Any]:
    """Load the manifest, and RE-VERIFY every 'done' arm against the artifact on disk.

    A manifest is a claim; the run directory is the evidence. An arm recorded done whose directory
    has no `DONE.json` is reset to pending -- a partial run must never be mistaken for a complete
    one just because a driver said so (C-051/C-012).
    """
    path = os.path.join(sdir, MANIFEST_FILE)
    if not os.path.exists(path):
        return {}
    man = json.load(open(path))
    for arm_id, rec in list((man.get("arms") or {}).items()):
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
# 12. THE PLAN -- constructs and validates EVERY arm, on CPU, with no GPU and no model
# ============================================================================================
def plan(pr: Prereg, a) -> Dict[str, Any]:
    arms = build_arm_manifest(pr)
    members = family_members(pr)
    runs_root = a.runs if os.path.isabs(a.runs) else repo_path(a.runs)
    assign = load_split(pr)
    rel_end = read_site_rel_end(pr)
    dg = direction_gate(pr, a.fit_dir, a.expect_direction_sha)
    grid = [int(x) for x in pr.require("read_site", "read_layer_grid")]
    n_layers = int(pr.require("model", "n_layers"))

    # every declared family member must be realised by at least one arm, and h1|h2 must PARTITION
    per_member: Dict[str, int] = {}
    for x in arms:
        if x.family_member:
            per_member[x.family_member] = per_member.get(x.family_member, 0) + 1
    missing = [m for m in members if not per_member.get(m)]
    if missing:
        raise RunnerRefusal("the manifest realises no run for declared family member(s) %s" % missing)
    sel_h1, sel_h2 = stage_selector(pr, "h1"), stage_selector(pr, "h2")
    part = [x.arm_id for x in arms if bool(sel_h1(x)) == bool(sel_h2(x))]
    if part:
        raise RunnerRefusal("stages h1 and h2 do not PARTITION the manifest: %s" % part[:5])

    binds: Dict[str, Any] = {}
    out_arms = []
    for arm in arms:
        con = constructibility(pr, arm, dg["payload_keys"])
        rec: Dict[str, Any] = {
            "arm_id": arm.arm_id, "role": arm.role, "hypothesis": arm.hypothesis,
            "scope": arm.scope, "layers": arm.layers, "mode": arm.mode,
            "family_member": arm.family_member, "tag": arm.tag(),
            "bank": bank_path_for(arm), "codeword": arm.codeword,
            "target_concept": arm.target_concept, "expect_enabled": arm.expect_enabled,
            "stage": "h1" if sel_h1(arm) else "h2",
            "in_q1": bool(stage_selector(pr, "q1")(arm)),
            "in_smoke": bool(stage_selector(pr, "smoke")(arm)),
            "propagation_read_layers": propagation_read_layers(arm.layers, grid, n_layers),
            **con,
        }
        if con["constructible"]:
            bank_abs = repo_path(bank_path_for(arm))
            key = (bank_abs, a.split)
            if key not in binds:
                binds[key] = split_bind(pr, bank_abs, a.split, assign)
            b = binds[key]
            # C-123, same clamp as the run path. --plan is what a human READS to decide what to
            # submit, so an unclamped expect_n here would print an argv that refuses when run.
            plan_limit = (a.smoke_limit if rec["in_smoke"] and a.stage == "smoke" else 0)
            plan_expect = min(b["expect_n"], plan_limit) if plan_limit else b["expect_n"]
            ctx = {"fit_dir": a.fit_dir, "rel_end": rel_end, "emit_liveness": True,
                   "constructibility": con, "expect_n": plan_expect,
                   "exclude_file": "<state-dir>/%s" % os.path.basename(
                       exclusion_file_name(bank_abs, a.split)),
                   "limit": plan_limit}
            argv = build_argv(pr, arm, ctx)
            assert_expect_n_agrees_with_limit(argv)
            rec["argv"] = argv
            rec["expect_n"] = plan_expect
            rec["n_domains"] = b["n_domains"]
            rec["analyzer_agreement"] = assert_argv_agrees_with_analyzer(pr, arm, argv, a.fit_dir)["ok"]
        out_arms.append(rec)

    n_con = sum(1 for r in out_arms if r["constructible"])
    return {
        "prereg": a.prereg, "id": pr.require("id"), "split": a.split, "stage": a.stage,
        "n_arms": len(arms), "n_live_arms": sum(1 for x in arms if x.role == "live"),
        "n_control_arms": sum(1 for x in arms if x.role == "control"),
        "n_constructible_today": n_con,
        "n_unbuildable_today": len(arms) - n_con,
        "family_members": members,
        "rows_per_arm": {str(k[1]) + ":" + os.path.basename(k[0]): v["expect_n"]
                         for k, v in binds.items()},
        "directions": {k: v for k, v in dg.items() if k != "provenance"},
        "direction_provenance": dg["provenance"],
        "q0": q0_gate(pr, runs_root, a.phase7_tag_prefix),
        "probe": probe_gate(a.probe_json),
        "read_site_rel_end": rel_end,
        "defects": [DEFECT_C113, DEFECT_LIVENESS_SCHEMA, DEFECT_PROBE_ATTRIBUTION,
                    DEFECT_C119_BRIDGE_ALPHA],
        "arms": out_arms,
    }


def exclusion_file_name(bank_abs: str, split: str) -> str:
    base = os.path.basename(bank_abs).replace(".jsonl", "")
    return "exclude_%s_%s.txt" % (base, split)


# ============================================================================================
# 13. EXECUTION
# ============================================================================================
# ============================================================================================
# 9b. A14 -- THE STAGE-AWARE PRE-EXTRACTION CHECKLIST GATE
# ============================================================================================
#
# `scripts/dcs_ts_prereg.py:validate` enforces the `done` boolean alone and knows nothing about
# stages, so a checklist item that is genuinely scoped to h1 -- A3, the cross-prompt donor --
# blocked h2 as well. Marking it done because it is irrelevant to h2 would be the
# "threshold published but never enforced" failure in reverse. This gate is the third option.
#
# IT IS STRICTLY STRONGER THAN THE LOADER'S, NOT WEAKER. An item is scoped out of a stage ONLY if
# ALL THREE of these hold:
#   1. the preregistration declares `applies_to_stages` for it and the running stage is not in it;
#   2. THIS runner carries a predicate that RE-DERIVES the item's relevance from the arm manifest;
#   3. that predicate, run against the stage's OWN arms, says the item is irrelevant.
# An item with no declared scope blocks. An item whose scope this runner cannot re-derive blocks --
# a prose scope with no code path is not a scope. An item whose scope the arms CONTRADICT blocks,
# and says so. Everything else is unchanged: `blocking and not done` refuses, malformed booleans
# refuse (C-086), and `artifacts.analyzer_exists == false` refuses.
#
#: {checklist id: (what makes it relevant, predicate over (pr, stage))}
CHECKLIST_STAGE_RELEVANCE = {
    # A3 / Q3: the cross-prompt donor. Relevant to a stage iff that stage runs a `patch` arm.
    "A3": ("the stage runs an arm whose mode is 'patch' (the cross-prompt donor)",
           lambda pr, stage: any(x.mode == "patch" for x in build_arm_manifest(pr)
                                 if stage_selector(pr, stage)(x))),
    # A7b / I-N2: the self-patch identity control is control C7, which is itself mode `patch`.
    "A7b": ("the stage runs an arm whose mode is 'patch' (control C7 is the self-patch)",
            lambda pr, stage: any(x.mode == "patch" for x in build_arm_manifest(pr)
                                  if stage_selector(pr, stage)(x))),
}


def load_amendment(amendment_path: str, pr: Prereg) -> Dict[str, Any]:
    """Load an AMENDMENT and verify it amends THIS preregistration, at the sha it names.

    An amendment is a new file; the parent is never edited. Anything it supersedes it must say it
    supersedes -- `amendment.supersedes[].field` -- so a file cannot quietly replace a gate it
    never claimed to touch.
    """
    fp = amendment_path if os.path.isabs(amendment_path) else repo_path(amendment_path)
    if not os.path.exists(fp):
        raise RunnerRefusal("amendment not found: %s" % amendment_path)
    obj = json.load(open(fp))
    if obj.get("status") != "FROZEN":
        raise RunnerRefusal("amendment %s has status %r, not FROZEN" % (amendment_path,
                                                                        obj.get("status")))
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


def checklist_gate(prereg_path: str, amendment_path: str, stage: str) -> Dict[str, Any]:
    """`A14`. The BLOCKING pre-extraction checklist, evaluated FOR ONE STAGE."""
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
        # Every BLOCKING parent item must be superseded by name, or it still stands. An amendment
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
            blocking.append("checklist %s: must declare boolean 'blocking' and 'done' (C-086)" % iid)
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
        if pred(pr, stage):
            blocking.append(
                "%s [%s] declares applies_to_stages=%s, but stage %r's OWN arms contradict that: "
                "%s. The declared scope is wrong and the item blocks." % (iid, source, scope,
                                                                          stage, why))
            continue
        scoped_out.append({"id": iid, "applies_to_stages": list(scope),
                           "why": "not relevant to stage %r, RE-DERIVED at launch: NOT (%s)"
                                  % (stage, why),
                           "item": str(item.get("item"))[:200]})
    if not artifacts.get("analyzer_exists", False):
        blocking.append("artifacts.analyzer_exists is false [%s] -- refusing to extract behind an "
                        "analyzer that does not exist" % source)
    return {"ok": not blocking, "stage": stage, "source": source,
            "blocking": blocking, "scoped_out": scoped_out}


def run_stage(pr: Prereg, a) -> int:
    runs_root = a.runs if os.path.isabs(a.runs) else repo_path(a.runs)
    state_root = a.state_root if os.path.isabs(a.state_root) else repo_path(a.state_root)
    sdir = stage_dir(state_root, a.stage, a.split)
    t_stage = time.time()

    probe_ctx = None
    if a.emit_probe:
        pg = probe_gate(a.probe_json)
        if not pg["ok"]:
            raise RunnerRefusal("--emit-probe is REFUSED:\n  - %s" % "\n  - ".join(pg["reasons"]))
        # THE PIN IS SUPPLIED HERE (review F4). `load_frozen_probe(expect_sha=...)` has always
        # been able to refuse a re-fitted probe and NOTHING passed it a sha, so the published
        # guarantee had no code path -- the repo's own "threshold published but never enforced"
        # shape. The runner reads the sha off the artifact it just gated and hands it to every
        # arm, so an artifact swapped between the gate and the node is refused AT the node.
        probe_ctx = {"json": a.probe_json, "sha": pg["probe_sha256"],
                     "read_layers": [int(x) for x in pr.require("read_site", "read_layer_grid")],
                     "rel_end": read_site_rel_end(pr)}
        print("[pr057] --emit-probe: frozen PR-048 probe sha %s (fit layer %s) -> read at "
              "layers %s, rel_end %d"
              % (str(pg["probe_sha256"])[:16], pg["probe_fit_layer"],
                 probe_ctx["read_layers"], probe_ctx["rel_end"]), flush=True)
    if not a.emit_liveness:
        raise RunnerRefusal(
            "--emit-liveness is REQUIRED: every arm in this phase installs a hook, and without "
            "the liveness record a dead hook scores as a clean null (C-13).")
    # A13: O1 is one of the four CONJUNCTIVE success conditions. Without `--emit-probe` no
    # PR057_PROBE.jsonl is written, O1 is never captured, and the conjunction is unevaluable --
    # which the analyzer would (correctly) report as CANNOT ANSWER after the GPU time was spent.
    # The flag is therefore REQUIRED for the confirmatory stages, not merely recommended.
    if a.stage in ("h1", "h2") and not a.emit_probe:
        raise RunnerRefusal(
            "--emit-probe is REQUIRED for the confirmatory stage %r. O1 (the frozen PR-048 probe "
            "margin) is one of the four conjunctive conditions of primary.success; without the "
            "flag no %s is written, O1 is never captured, and the whole stage returns CANNOT "
            "ANSWER on a condition that a single command-line flag would have supplied "
            "(amendment A13)." % (a.stage, CONTRACT_PROBE))

    # ---- order, Q0, and the preregistration's own blocking checklist -----------------------
    #
    # A REAL RUN RAISES AT THE FIRST GATE. A --dry-run COLLECTS THEM ALL and exits non-zero: a
    # dry run whose whole job is to tell you what is wrong should not stop at the first thing,
    # and it cannot spend GPU time by continuing. It never becomes a licence to run: `blocking`
    # is non-empty, so `main` returns 3.
    blocking: List[str] = []

    def _gate(fn, label):
        try:
            return fn()
        except (RunnerRefusal, PreregError, Refusal, ZeroBinding) as e:
            if not a.dry_run:
                raise
            blocking.append("%s: %s" % (label, str(e).splitlines()[0][:400]))
            return None

    def _q0():
        g = q0_gate(pr, runs_root, a.phase7_tag_prefix)
        if not g["ok"]:
            raise RunnerRefusal("Q0: %s" % g["detail"])
        return g

    def _checklist():
        # The confirmatory stages read TEST. They may not run until the BLOCKING checklist closes.
        # A14: the gate is now STAGE-AWARE, and strictly stronger than the loader's -- see
        # `checklist_gate`. It is never weaker: an item with no declared stage scope, or whose
        # scope this runner cannot re-derive, still blocks every stage.
        if a.stage in ("h1", "h2"):
            g = checklist_gate(a.prereg, getattr(a, "amendment", "") or "", a.stage)
            for s in g["scoped_out"]:
                print("[pr057] checklist %s: SCOPED OUT of stage %r -- %s"
                      % (s["id"], a.stage, s["why"]), flush=True)
            if not g["ok"]:
                # PRINTED as well as raised: `_gate` keeps only the first line of a refusal for
                # the --dry-run summary, and "which items are still open" is the whole content of
                # this one.
                for r in g["blocking"]:
                    print("[pr057] CHECKLIST BLOCKS %s: %s" % (a.stage, r), flush=True)
                raise RunnerRefusal(
                    "the confirmatory stage %r requires the BLOCKING pre-extraction checklist to "
                    "close, and it does not (%d item(s), each printed above): %s"
                    % (a.stage, len(g["blocking"]),
                       "; ".join(r.split(" [")[0] for r in g["blocking"])))
        return True

    # `dg` is computed BEFORE the launch-order gate because A9's re-derivation of a predecessor's
    # constructibility needs the direction payload's keys, and a gate that decided without them
    # would be deciding on evidence it did not look at.
    dg = _gate(lambda: direction_gate(pr, a.fit_dir, a.expect_direction_sha), "direction gate")
    q0 = _gate(_q0, "Q0")
    _gate(lambda: assert_stage_order(state_root, a.stage, a.split, pr=pr,
                                     payload_keys=(dg["payload_keys"] if dg else None)),
          "launch order")
    _gate(_checklist, "pre-extraction checklist")
    if a.stage == "q1" and a.split != "validation":
        raise RunnerRefusal("the Q1 power stage is VALIDATION-ONLY by preregistration; got --split %r"
                            % a.split)
    if a.stage in ("h1", "h2") and a.split != "test":
        raise RunnerRefusal("the confirmatory stages run on TEST; got --split %r" % a.split)

    assign = load_split(pr)
    rel_end = read_site_rel_end(pr)
    if dg is None:                      # only reachable under --dry-run, which collected it above
        for b in blocking:
            print("[pr057] BLOCKING %s" % b, file=sys.stderr)
        print("[pr057] DRY-RUN: the direction gate did not pass, so no arm could be constructed. "
              "%d BLOCKING gate(s) above." % len(blocking), file=sys.stderr)
        return 3
    arms_all = build_arm_manifest(pr)
    sel = stage_selector(pr, a.stage)
    selected = [x for x in arms_all if sel(x)]
    if not selected:
        raise ZeroBinding("stage %r selected ZERO arms of %d" % (a.stage, len(arms_all)))

    # ---- the SECOND kill condition, before anything is submitted ---------------------------
    kill_states: Dict[str, Dict[str, Any]] = {}
    skipped: List[Dict[str, Any]] = []
    if a.stage == "h2":
        def _baseline(arm: ArmSpec):
            tag = "%s_%s_%s" % (a.phase7_tag_prefix, arm.codeword, arm.target_concept)
            return load_arm_run(_find_run(runs_root, tag))["results"]
        for scope in sorted({x.scope for x in selected}):
            kill_states[scope] = h1_kill_state(pr, runs_root, scope, arms_all, _baseline)
            print("[pr057] kill condition @%s: %s -- %s"
                  % (scope, kill_states[scope]["state"], kill_states[scope]["detail"]), flush=True)
        selected, skipped = apply_kill_condition(selected, kill_states)
        assert_kill_condition_honoured(selected, kill_states)

    # ---- constructibility, population binding, argv ----------------------------------------
    # A DRY RUN WRITES NOTHING. It constructs and validates every arm on CPU -- the exclusion
    # files are computed and their content hashed, not written -- so the whole path is testable
    # without a GPU and without leaving artifacts that a later reader could mistake for a run.
    if not a.dry_run:
        os.makedirs(sdir, exist_ok=True)
    # C-124: refuse a stage that already carries a verdict BEFORE any arm runs, not after.
    # Skipped on --dry-run, which writes nothing and is exactly how an operator inspects a stage
    # whose prior verdict they are still deciding what to do about.
    if not a.dry_run:
        assert_stage_has_no_prior_verdict(sdir)
    man = manifest_load(sdir, runs_root) if not a.dry_run else {}
    man.setdefault("started", time.strftime("%Y-%m-%d %H:%M:%S"))
    man.update({"stage": a.stage, "split": a.split, "prereg": a.prereg,
                "amendment": getattr(a, "amendment", "") or None,
                "provenance": slurm_provenance(),
                "prereg_id": pr.require("id"), "fit_dir": a.fit_dir,
                "direction_sha256": dg["sha256"], "kill_states": kill_states,
                "not_submitted": skipped, "runs_root": runs_root})
    man.setdefault("arms", {})

    todo: List[Tuple[ArmSpec, List[str], int]] = []
    unbuildable: List[Dict[str, Any]] = []
    binds: Dict[Any, Any] = {}
    for arm in selected:
        con = constructibility(pr, arm, dg["payload_keys"])
        if not con["constructible"]:
            unbuildable.append({"arm_id": arm.arm_id, "reasons": con["reasons"]})
            man.setdefault("arms", {}).setdefault(arm.arm_id, {})
            man["arms"][arm.arm_id].update({"status": "UNBUILDABLE", "reasons": con["reasons"]})
            continue
        bank_abs = repo_path(bank_path_for(arm))
        if bank_abs not in binds:
            b = split_bind(pr, bank_abs, a.split, assign)
            xf = os.path.join(sdir, exclusion_file_name(bank_abs, a.split))
            text = exclusion_file_text(pr, b)
            if not a.dry_run:
                with open(xf, "w") as fh:
                    fh.write(text)
            b["exclude_file"] = xf
            b["exclude_file_sha16"] = hashlib.sha256(text.encode()).hexdigest()[:16]
            binds[bank_abs] = b
        b = binds[bank_abs]
        # C-123 (job 868569). `--expect-n` must describe the population the arm will ACTUALLY
        # score. In the smoke stage `--limit` truncates it, and this built the ctx with the
        # UNCLAMPED bound count while clamping only the runner's own bookkeeping below -- so the
        # argv carried `--expect-n 670` beside `--limit 40` and score_behavior's row-count guard
        # correctly refused: "population is 40 rows, --expect-n says 670. A silently-shrunken
        # sample is how R-18 happened." The guard was right and the runner was wrong.
        #
        # Clamp ONCE, above the ctx, and use the same number for the argv and for the runner's
        # expectation, so the two cannot drift apart again. Two variables that must agree are a
        # standing invitation for exactly this defect.
        expect_rows = min(b["expect_n"], a.smoke_limit) if a.stage == "smoke" else b["expect_n"]
        ctx = {"fit_dir": a.fit_dir, "rel_end": rel_end, "emit_liveness": True,
               "constructibility": con, "expect_n": expect_rows,
               "exclude_file": b["exclude_file"], "probe": probe_ctx,
               "limit": (a.smoke_limit if a.stage == "smoke" else 0)}
        argv = build_argv(pr, arm, ctx)
        assert_argv_agrees_with_analyzer(pr, arm, argv, a.fit_dir)
        assert_expect_n_agrees_with_limit(argv)
        todo.append((arm, argv, expect_rows))

    print("[pr057] stage=%s split=%s: %d selected, %d constructible, %d unbuildable, %d "
          "not-submitted by the kill condition"
          % (a.stage, a.split, len(selected), len(todo), len(unbuildable), len(skipped)), flush=True)
    for u in unbuildable:
        print("[pr057]   UNBUILDABLE %s: %s" % (u["arm_id"], u["reasons"][0][:160]), flush=True)
    if not todo:
        raise RunnerRefusal(
            "stage %r has ZERO constructible arms (%d were selected). Refusing to write a "
            "DONE.json for a stage that ran nothing -- an empty stage that reports success is "
            "the failure this whole design exists to prevent." % (a.stage, len(selected)))

    if a.dry_run:
        for arm, argv, n in todo:
            print("[pr057] DRY-RUN %-42s %s" % (arm.arm_id, " ".join(argv)))
        print("[pr057] DRY-RUN: %d arm(s) constructed and validated, model NOT loaded, nothing "
              "written, nothing run." % len(todo))
        for b in blocking:
            print("[pr057] BLOCKING %s" % b, file=sys.stderr)
        if blocking:
            print("[pr057] DRY-RUN: %d BLOCKING gate(s) above. This stage may NOT be submitted."
                  % len(blocking), file=sys.stderr)
            return 3
        return 0

    # ---- the loop. ONE model load. -----------------------------------------------------------
    cache = ModelCache().install()
    import score_behavior as SB
    n_rows_total, n_done = 0, 0
    try:
        for i, (arm, argv, expect_rows) in enumerate(todo, 1):
            rec = man["arms"].setdefault(arm.arm_id, {})
            if rec.get("status") == "done":
                print("[pr057] [%d/%d] %s already complete at %s -- SKIPPING (resume)"
                      % (i, len(todo), arm.arm_id, rec.get("run_dir")), flush=True)
                n_rows_total += int(rec.get("rows") or 0)
                n_done += 1
                continue
            rec.update({"status": "running", "argv": argv, "tag": arm.tag(),
                        "expect_rows": expect_rows})
            manifest_save(sdir, man)
            print("\n[pr057] === [%d/%d] %s ===\n[pr057]     %s"
                  % (i, len(todo), arm.arm_id, " ".join(argv)), flush=True)
            t0 = time.time()
            old_argv = sys.argv
            sys.argv = [SCORE_SCRIPT] + list(argv)
            try:
                rc = SB.main()
            except SystemExit as e:                 # the house refusal idiom
                rc = e.code if isinstance(e.code, int) else 1
                if rc == 0:
                    rc = 1
                print("[pr057] arm %s REFUSED: %s" % (arm.arm_id, e), file=sys.stderr, flush=True)
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
                                "rows": n_rows_total,
                                "wall_seconds": time.time() - t_stage,
                                "model_loads": cache.n_loads, "model_cache_hits": cache.n_hits,
                                "detail": "STOPPED at the first failure; the remaining arms were "
                                          "NOT run and no success is reported for them."})
                raise RunnerRefusal(
                    "arm %s exited %d. STOPPING: this runner never continues past a failure and "
                    "never reports success it did not observe." % (arm.arm_id, rc))
            run_dir = _find_run(runs_root, arm.tag())
            _iv = argv[argv.index("--intervene") + 1] if "--intervene" in argv else ""
            gate = verify_arm_artifacts(pr, arm, run_dir, expect_rows,
                                        con_dir=_iv.split(":", 1)[0],
                                        direction_sha=dg["sha256"])
            rec.update({"status": "done", "run_dir": run_dir, "rows": gate["n_rows"],
                        "output_sha256": gate["output_sha256"],
                        "wall_seconds": wall, "exit_code": 0,
                        "n_liveness_records": gate["n_liveness_records"],
                        "hook_fired_count_total": gate["hook_fired_count_total"],
                        "n_cells_edited_realised_total": gate["n_cells_edited_realised_total"]})
            manifest_save(sdir, man)
            n_rows_total += gate["n_rows"]
            n_done += 1
            print("[pr057] [%d/%d] %s OK: %d rows, %d liveness records, %d hook firings, %.1f min"
                  % (i, len(todo), arm.arm_id, gate["n_rows"], gate["n_liveness_records"],
                     gate["hook_fired_count_total"], wall / 60.0), flush=True)
            try:
                import torch
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
            except Exception:
                pass
    finally:
        cache.uninstall()

    # ---- CONTROL C1: five draws, FIVE DISTINCT OUTPUT HASHES ---------------------------------
    # `_five_draws_and_distinct_hashes`: this project has TWICE published a control band that was
    # secretly n=1 because the seed never reached the draw, once with a fake between-draw sd of
    # 0.0048. The gate is the analyzer's `control_band_gate`; the hashes are the runner's
    # per-arm output hashes. It runs HERE, at the end of the stage, so a band that is secretly
    # n=1 fails before anyone computes an equivalence interval from it.
    bands: Dict[str, List[str]] = {}
    for arm in selected:
        if arm.hypothesis != "C1":
            continue
        r = man["arms"].get(arm.arm_id) or {}
        if r.get("status") == "done" and r.get("output_sha256"):
            bands.setdefault(arm.arm_id.rsplit("_draw", 1)[0], []).append(r["output_sha256"])
    n_draws = int(pr.require("seeds", "n_control_draws"))
    band_report = {}
    for key, shas in sorted(bands.items()):
        if len(shas) < n_draws:
            continue
        g = AN.control_band_gate(shas, n_draws)
        band_report[key] = g
        if not g["ok"]:
            raise RunnerRefusal("control band %s: %s" % (key, g["detail"]))
    if band_report:
        print("[pr057] control band(s) verified distinct: %s"
              % {k: v["n_distinct"] for k, v in band_report.items()}, flush=True)

    # ---- Q1's decision, as a code path -------------------------------------------------------
    q1 = None
    if a.stage == "q1":
        # One value per domain: the mean over the stage's arms of that arm's own domain-mean
        # delta. Pooling the arms' ROWS instead would let a bank with more surviving rows dominate
        # the SD that Q1 exists to measure.
        acc: Dict[str, List[float]] = {}
        for arm, _argv, _n in todo:
            run = load_arm_run(man["arms"][arm.arm_id]["run_dir"])
            tag = "%s_%s_%s" % (a.phase7_tag_prefix, arm.codeword, arm.target_concept)
            base = load_arm_run(_find_run(runs_root, tag))["results"]
            for dom, val in per_domain_delta(run["results"], base).items():
                acc.setdefault(dom, []).append(val)
        deltas = {d: sum(v) / len(v) for d, v in acc.items()}
        q1 = q1_power(pr, deltas)
        print("\n[pr057] Q1: %s" % q1["decision"], flush=True)
        if not q1["power_ok"]:
            write_terminal(sdir, "DONE.json",
                           {"status": "ok", "stage": a.stage, "split": a.split,
                            "n_arms_done": n_done, "rows": n_rows_total,
                            "wall_seconds": time.time() - t_stage,
                            "model_loads": cache.n_loads, "q1": q1,
                            "verdict": "CANNOT ANSWER WITHOUT READING TEST"})
            print("[pr057] the confirmatory stages are NOT unlocked.", file=sys.stderr)
            return 5

    done = {"status": "ok", "stage": a.stage, "split": a.split,
            "n_arms_selected": len(selected), "n_arms_done": n_done,
            "n_arms_unbuildable": len(unbuildable), "unbuildable": unbuildable,
            "n_arms_not_submitted_by_kill_condition": len(skipped), "not_submitted": skipped,
            "kill_states": kill_states,
            "rows": n_rows_total, "wall_seconds": time.time() - t_stage,
            "model_loads": cache.n_loads, "model_cache_hits": cache.n_hits,
            "direction_sha256": dg["sha256"], "q1": q1, "control_bands": band_report,
            "q0": q0,
            "defects_recorded": [DEFECT_C113, DEFECT_LIVENESS_SCHEMA, DEFECT_PROBE_ATTRIBUTION,
                                 DEFECT_C119_BRIDGE_ALPHA]}
    write_terminal(sdir, "DONE.json", done)
    manifest_save(sdir, man)
    print("[pr057] stage %s COMPLETE: %d arm(s), %d rows, %.1f min, %d model load(s)"
          % (a.stage, n_done, n_rows_total, (time.time() - t_stage) / 60.0, cache.n_loads))
    return 0


def assert_stage_has_no_prior_verdict(sdir: str) -> None:
    """Refuse a stage that ALREADY carries a terminal verdict -- BEFORE any arm runs.  `C-124`.

    `write_terminal` enforces "a stage has ONE verdict", which is correct. But it enforces it at the
    END. Job 868702 ran BOTH smoke arms to completion (40 rows each, 40 and 0 hook firings, exactly
    as designed) and was then refused, because job 868569 -- which had died 13 seconds in on the
    `C-123` `--expect-n`/`--limit` defect, having completed ZERO arms -- had already written
    `ABORTED.json` into the same stage directory. A successful run was discarded at the last step by
    a stale record from a superseded failure.

    The verdict rule is right; enforcing it only at the end is not. This checks at the START, so the
    operator is told before an allocation is spent rather than after. The remedy is deliberately NOT
    automatic: a terminal record is evidence, and silently overwriting one is how a failed run gets
    quietly reported as a success. Archive it by hand, with provenance.
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
                "before any arm runs, is the whole point: job 868702 completed both smoke arms and "
                "was rejected at the end by a stale record from a run that had completed none.\n"
                "  If that prior verdict is superseded, ARCHIVE it with provenance (e.g. rename to "
                "%s.<jobid>.superseded.json) rather than deleting it, then re-run. Never hand-write "
                "a terminal record."
                % (sdir, name, prior.get("status"), prior.get("failed_arm"),
                   prior.get("n_arms_done"), name))


def slurm_provenance() -> Dict[str, Any]:
    """`A15`. Who wrote this record: the SLURM job id, its node list, and the host.

    `outputs/boombness/pr057_runner/smoke_train/DONE.json` could not be traced to the job that
    wrote it: the arm run dirs carried `slurm_job_id` 868702 in their own `RUNMETA.json`, and the
    stage record -- written later, by a different invocation -- carried nothing. A terminal record
    that cannot name the job that produced it is evidence with no provenance. Read from the
    environment, never typed, and recorded as `null` off a batch node rather than invented.
    """
    return {"slurm_job_id": os.environ.get("SLURM_JOB_ID") or None,
            "slurm_array_task_id": os.environ.get("SLURM_ARRAY_TASK_ID") or None,
            "slurm_nodelist": os.environ.get("SLURM_JOB_NODELIST")
                              or os.environ.get("SLURM_NODELIST") or None,
            "hostname": socket.gethostname(),
            "pid": os.getpid(),
            "written_at": time.strftime("%Y-%m-%d %H:%M:%S")}


def write_terminal(sdir: str, name: str, blob: Dict[str, Any]) -> None:
    """DONE.json / ABORTED.json. They are DIFFERENT FILES so a partial stage can never be read as
    a complete one, and neither is allowed to overwrite the other.

    `A15`: every terminal record carries the SLURM job id of the invocation that wrote it.
    """
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
# 14. SELF-TEST -- CPU only, on the real functions
# ============================================================================================
def _stub_arm(**kw) -> ArmSpec:
    base = dict(arm_id="x", role="live", family_member="H2axS1", hypothesis="H2a", scope="S1",
                layers=[9], mode="project_out", direction="v_bomb_specific",
                source_concept="knife", target_concept="bomb", codeword="button",
                dose_units="scale-free", alpha=1.0, control_draw_seed=None, expect_enabled=True)
    base.update(kw)
    return ArmSpec(**base)


def _live_record(**kw) -> Dict[str, Any]:
    import pair_common as pc
    r = pc.hook_stats_dict(mode="project_out_single", layer=9, rel_end=-10)
    r.update({  # the keys score_behavior's writer adds around the hook's own record
        "prompt_id": "p0", "domain": "d", "split": "test", "cell": "C", "concept": "bomb",
        "codeword": "button", "arm": "x", "n_target_occurrences": 1,
        "codeword_last_indices": [90], "n_codeword_occurrences": 1,
        "n_subtokens_per_occurrence": [1],
        "liveness_violations": []})
    r.update({"n_forward_calls": 1, "hook_fired_count": 1, "n_destination_rows": 1,
              "n_forward_with_destinations": 1,
              "n_cells_edited_realised": 1, "n_cells_edited_expected": 1,
              "activation_norm_pre": 10.0,
              "activation_norm_post": 9.8, "projection_removed_l2": 1.4, "max_abs_delta": 0.3,
              "min_projection_removed_l2": 1.4, "orthogonal_residual_delta_l2": 2.1e-07,
              "cos_pre_post": 0.99, "direction_norm": 1.0, "alpha": 1.0, "norm_ratio": 0.98,
              "resolved_absolute_index": [90], "seq_len_last": 100, "seq_len": 100,
              "seq_len_at_resolution": 100})
    # THE SAME RESOLUTION THE PRODUCER RUNS, not a hand-written copy of its output. A stub that
    # hand-writes `occurrence_index_per_edit` cannot notice that the producer stopped writing the
    # field the frozen contract actually looks up -- which is how job 869332 got to the GPU.
    r.update(pc.occurrence_annotation(r, r["codeword_last_indices"]))
    r.update(kw)
    return r


def _live_record_all(**kw) -> Dict[str, Any]:
    """The S2 (ALL-POSITION) counterpart of `_live_record`, as `score_behavior` now writes it.

    Every field the frozen persist list names, with NO edit site: an all-position edit has none.
    `occurrence_index` is present because it is a property of the PROMPT (job 869332's defect);
    `rel_end` / `resolved_absolute_index` / `positions` stay null because they are properties of
    the EDIT SITE and inventing one would be worse than the bug being fixed.
    """
    import pair_common as pc
    r = pc.hook_stats_dict(mode="project_out_all", layer=7)
    r.update({"prompt_id": "p0", "domain": "d", "split": "test", "cell": "C", "concept": "bomb",
              "codeword": "basket", "arm": "x", "n_target_occurrences": 5,
              "codeword_last_indices": [174, 192, 211, 230, 250], "n_codeword_occurrences": 5,
              "n_subtokens_per_occurrence": [1, 1, 1, 1, 1],
              "liveness_violations": []})
    r.update({"n_forward_calls": 1, "hook_fired_count": 1, "n_destination_rows": 1052,
              "n_forward_with_destinations": 1, "n_cells_edited_realised": 1052,
              "n_cells_edited_expected": 1052, "activation_norm_pre": 10.0,
              "activation_norm_post": 9.8, "projection_removed_l2": 1.4, "max_abs_delta": 0.3,
              "min_projection_removed_l2": 1.4, "orthogonal_residual_delta_l2": 2.1e-07,
              "cos_pre_post": 0.99, "direction_norm": 1.0, "alpha": 1.0, "norm_ratio": 0.98,
              "seq_len_last": 260, "seq_len": 260})
    r.update(pc.occurrence_annotation(r, r["codeword_last_indices"]))
    r.update(kw)
    return r


def selftest() -> int:
    ck = Checks()
    pr = load_prereg(PREREG_DEFAULT, for_extraction=False)
    arms = build_arm_manifest(pr)
    payload_keys = ["v_bomb", "v_bomb_specific", "v_gun", "v_knife", "v_knife_specific",
                    "v_remap", "gap", "cell_means", "meta", "layers"]

    ck.add("manifest_54", "the runner sees the analyzer's 54-arm manifest", len(arms) == 54,
           len(arms), "live=%d control=%d" % (sum(1 for a in arms if a.role == "live"),
                                              sum(1 for a in arms if a.role == "control")))
    ck.add("manifest_24_live", "24 live / 30 control", sum(1 for a in arms if a.role == "live") == 24
           and sum(1 for a in arms if a.role == "control") == 30, 54, "")

    sel_h1, sel_h2 = stage_selector(pr, "h1"), stage_selector(pr, "h2")
    n1 = sum(1 for a in arms if sel_h1(a))
    n2 = sum(1 for a in arms if sel_h2(a))
    ck.add("stages_partition", "h1 | h2 partitions the manifest exactly",
           n1 + n2 == len(arms) and not [a for a in arms if sel_h1(a) and sel_h2(a)],
           n1 + n2, "h1=%d h2=%d" % (n1, n2))
    ck.add("stage_h1_is_18", "stage h1 is the 16 H1 arms plus the 2 C7 self-patch controls",
           n1 == 18, n1, "")
    nq1 = sum(1 for a in arms if stage_selector(pr, "q1")(a))
    ck.add("stage_q1_is_2", "the Q1 power stage is 2 arms (H2a x S1, both codewords)", nq1 == 2,
           nq1, "")
    nsm = sum(1 for a in arms if stage_selector(pr, "smoke")(a))
    sm_con = [a.arm_id for a in arms if stage_selector(pr, "smoke")(a)
              and constructibility(pr, a, payload_keys)["constructible"]]
    ck.add("stage_smoke_is_2", "the smoke selects 2 arms (primary + the disabled-hook bridge)",
           nsm == 2, nsm, "constructible today: %s" % sm_con)
    ck.add("c5_bridge_runs_the_live_alpha",
           "C-119: the C5 bridge carries the LIVE arm's alpha, so its inner hook has a real edit "
           "to discard and `would_have_changed_max_abs > 0` can be true",
           all(float(a.alpha) > 0 for a in arms if a.hypothesis == "C5")
           and len(sm_con) == 2,
           len([a for a in arms if a.hypothesis == "C5"]), "constructible: %s" % sm_con)
    labels = sorted({a.direction for a in arms if a.direction})
    ck.add("direction_map_covers_manifest",
           "every direction label the manifest uses has a DECLARED mapping (or an explicit None)",
           all(l in DIRECTION_MAP for l in labels), len(labels), "%s" % labels)

    rel = read_site_rel_end(pr)
    ck.add("rel_end_parsed", "the edit site is PARSED from the frozen file as a negative offset",
           rel == -10 and rel < 0, rel, "codeword_last")
    ck.add("cond_mapping", "cell C maps to the condition string the launcher must use",
           cell_condition(pr) == "natural_doublespeak", 1, "")

    # constructibility
    con_ok = constructibility(pr, _stub_arm(), payload_keys)
    ck.add("constructible_h2a", "the 10.2 PRIMARY arm is constructible today",
           con_ok["constructible"] and con_ok["intervene_direction"] == "v_bomb_specific", 1, "")
    for mode, name in (("patch", "H1/C7"), ("component_replace", "H2b")):
        c = constructibility(pr, _stub_arm(mode=mode, direction="v_bomb_specific"), payload_keys)
        ck.add("unbuildable_%s" % mode, "%s is refused, with the reason" % name,
               not c["constructible"] and bool(c["reasons"]), len(c["reasons"]),
               c["reasons"][0][:70])
    # C-122, CLOSED. `add` used to be in UNBUILDABLE with C4 refused for it. The check is not
    # deleted, it is INVERTED: the arm must now be constructible at BOTH scopes, because a C4
    # that is buildable only all-position would be an all-position edit under an S1 label.
    c4a = constructibility(pr, _stub_arm(mode="add", scope="S2",
                                         direction="orthogonal_to_concept_subspace"), payload_keys)
    c4s = constructibility(pr, _stub_arm(mode="add", scope="S1",
                                         direction="orthogonal_to_concept_subspace"), payload_keys)
    ck.add("c120_add_constructible",
           "C-122: control C4 (mode 'add') is constructible at BOTH scopes now that the additive "
           "hook is instrumented and has a single-site form",
           c4a["constructible"] and c4s["constructible"]
           and c4a["intervene_direction"] == "orthogonal@v_bomb_specific",
           2, "%s / %s" % (c4a["reasons"], c4s["reasons"]))
    _c4argv = build_argv(pr, _stub_arm(mode="add", scope="S1", alpha=1.0,
                                       direction="orthogonal_to_concept_subspace"),
                         {"fit_dir": "outputs/dcs_ts/directions_pr053",
                          "rel_end": read_site_rel_end(pr), "emit_liveness": True,
                          "constructibility": c4s, "expect_n": 0, "exclude_file": "",
                          "limit": 0})
    ck.add("c120_add_argv_mode",
           "C4's argv launches mode 'add', NOT 'project_out': the runner used to hard-code the "
           "mode, which would have launched the orthogonal control as a projection",
           any(t.startswith("orthogonal@v_bomb_specific:add:") for t in _c4argv)
           and "--pr057-edit-positions=-10" in _c4argv,
           1, [t for t in _c4argv if ":add:" in t])
    c2 = constructibility(pr, _stub_arm(direction="v_bomb_specific_shuffled_labels"), payload_keys)
    ck.add("unbuildable_c2", "C2's shuffled-label direction has no artifact and is refused",
           not c2["constructible"], len(c2["reasons"]), c2["reasons"][0][:70])
    cun = constructibility(pr, _stub_arm(direction="v_something_new"), payload_keys)
    ck.add("unmapped_direction", "an UNMAPPED manifest direction is refused, never guessed",
           not cun["constructible"], len(cun["reasons"]), cun["reasons"][0][:70])
    ck.add("c1_base", "C1 is norm-matched to the axis the arm edits (Q13)",
           DIRECTION_MAP["random_norm_matched"] == "random@v_bomb_specific", 1, "")

    # argv construction + the anti-drift check against the analyzer
    ctx = {"fit_dir": "outputs/dcs_ts/directions_pr053", "rel_end": rel, "emit_liveness": True,
           "constructibility": con_ok, "expect_n": 230, "exclude_file": "/x/e.txt", "limit": 0}
    argv = build_argv(pr, _stub_arm(), ctx)
    ck.add("argv_single_site", "an S1 arm carries --pr057-edit-positions in the '=' form",
           "--pr057-edit-positions=-10" in argv, 1, "")
    ck.add("argv_liveness", "every arm carries --pr057-liveness-out auto",
           "--pr057-liveness-out" in argv and argv[argv.index("--pr057-liveness-out") + 1] == "auto",
           1, "")
    ck.add("argv_expect_n", "--expect-n binds the population size the runner computed",
           "--expect-n" in argv and argv[argv.index("--expect-n") + 1] == "230", 1, "")
    ck.add("argv_no_spaces", "no argv token contains a space or a quote (BOOMB_ARGS is word-split)",
           all(" " not in t and '"' not in t and "'" not in t for t in argv), len(argv), "")
    try:
        build_argv(pr, _stub_arm(), {**ctx, "emit_liveness": False})
        ok = False
    except RunnerRefusal:
        ok = True
    ck.add("argv_refuses_no_liveness", "an arm without liveness instrumentation is REFUSED (C-13)",
           ok, 1, "")

    n_agree = 0
    for arm in arms:
        c = constructibility(pr, arm, payload_keys)
        if not c["constructible"]:
            continue
        cx = {**ctx, "constructibility": c}
        av = build_argv(pr, arm, cx)
        assert_argv_agrees_with_analyzer(pr, arm, av, ctx["fit_dir"])
        n_agree += 1
    ck.add("analyzer_agreement", "every constructible arm's argv agrees with the analyzer's own "
           "launch_command on bank/arm/tag/mode/band/alpha", n_agree > 0, n_agree, "")

    # population binding
    assign = load_split(pr)
    bank = repo_path("data/boombness_prompts/boombness_prompt_bank_ts116m_button_bomb.jsonl")
    b_test = split_bind(pr, bank, "test", assign)
    b_val = split_bind(pr, bank, "validation", assign)
    ck.add("bind_test_230", "the TEST split binds 23 domains x 10 rows = 230 rows",
           b_test["expect_n"] == 230 and b_test["n_domains"] == 23, b_test["expect_n"], "")
    ck.add("bind_val_230", "the VALIDATION split binds 23 domains x 10 rows",
           b_val["expect_n"] == 230 and b_val["n_domains"] == 23, b_val["expect_n"], "")
    ck.add("bind_disjoint", "the two splits share no prompt_id",
           not (set(b_test["keep_ids"]) & set(b_val["keep_ids"])), len(b_test["keep_ids"]), "")
    ck.add("bind_a039", "selecting on `condition` bound exactly the rows `cell` would have (A-039)",
           b_test["population"]["a039_cell_condition_mapping_is_1to1"], 1, "")
    txt = exclusion_file_text(pr, b_test)
    ids = [l for l in txt.splitlines() if not l.startswith("#")]
    ck.add("exclusion_file", "the exclusion file lists every row outside the split, with provenance",
           len(ids) == b_test["n_drop"] and txt.startswith("#"), len(ids), "")

    # liveness
    rec = _live_record()
    ann = annotate_liveness([rec], _stub_arm())
    ck.add("annotate_expected", "the PRODUCER's own n_cells_edited_expected survives annotation "
           "unaltered (C-117 -- the runner no longer invents it)",
           ann[0]["n_cells_edited_expected"] == rec["n_cells_edited_expected"] == 1, 1,
           ann[0]["_expected_rule"])
    ck.add("annotate_index", "the single-site absolute index is unpacked for the audit",
           ann[0]["resolved_absolute_index"] == 90, 90, "")
    ck.add("liveness_live_ok", "a live, firing, state-changing hook passes the consumer gate",
           liveness_gate(ann, "x", expect_enabled=True)["live"], 1, "")
    aud = audit_end_relative(ann)
    ck.add("audit_ok", "seq_len + rel_end == resolved_absolute_index", aud["ok"], aud["n_records"],
           aud["witness_note"][:60])
    dead = annotate_liveness([_live_record(hook_fired_count=0, n_cells_edited_realised=0,
                                           projection_removed_l2=0.0, max_abs_delta=0.0)],
                             _stub_arm())
    ck.add("liveness_dead_refused", "a DEAD hook does not pass as a clean null",
           not liveness_gate(dead, "x", expect_enabled=True)["live"], len(dead),
           "; ".join(liveness_gate(dead, "x", expect_enabled=True)["reasons"])[:70])
    bridge = annotate_liveness([_live_record(enabled=False, hook_fired_count=0,
                                             n_cells_edited_realised=0,
                                             projection_removed_l2=0.0, max_abs_delta=0.0,
                                             would_have_changed_max_abs=0.06)],
                               _stub_arm(mode="disabled", expect_enabled=False))
    ck.add("bridge_ok_as_bridge", "the disabled-hook bridge passes AS A BRIDGE",
           liveness_gate(bridge, "c5", expect_enabled=False)["live"], 1, "")
    ck.add("bridge_refused_as_live", "the SAME record presented as a live arm is REFUSED",
           not liveness_gate(bridge, "c5", expect_enabled=True)["live"], len(bridge), "")

    # the frozen persist contract
    gate_stub = {"realized_dose": {"v_bomb_specific|L9|alpha1": {"cell_residual_frac_removed": 0.09}},
                 "direction_file_sha256": "0" * 64, "control_draw_seed": 20260907,
                 "output_sha256": "a" * 64, "cos_edit_vs_direction": "+/-1 BY CONSTRUCTION"}
    rep = persist_contract_report(pr, _stub_arm(), ann[0], gate_stub)
    ck.add("persist_contract", "every field of the frozen persist_per_row_and_per_arm list is "
           "looked up where it is supposed to live", rep["n_missing"] == 0, rep["n_fields"],
           "%d fields" % rep["n_fields"])
    try:
        persist_contract_report(pr, _stub_arm(),
                                {**ann[0], "cos_pre_post": None}, gate_stub)
        ok = False
    except RunnerRefusal:
        ok = True
    ck.add("persist_contract_null", "a persisted field that is present but NULL on a LIVE arm is "
           "refused (a check that reads the producer's own null field is not a check)", ok, 1, "")

    # ---- 2026-09-08: the S2 persist defect that stopped job 869332 -----------------------
    _s2_arm = _stub_arm(arm_id="h2a_s2_projout_basket", scope="S2", family_member="H2axS2",
                        layers=[7, 8, 9, 10, 11, 12, 13, 14])
    _s2 = annotate_liveness([_live_record_all()], _s2_arm)[0]
    _rep2 = persist_contract_report(pr, _s2_arm, _s2, gate_stub)
    ck.add("persist_contract_all_position",
           "every field of the frozen list is persisted by an ALL-POSITION (S2) arm too -- the "
           "arm that ran clean on the GPU (job 869332: 230 rows, 1840 liveness records, 0 "
           "violations) and was refused at artifact verification for one missing field",
           _rep2["n_missing"] == 0, _rep2["n_fields"], "%d fields" % _rep2["n_fields"])
    ck.add("persist_contract_all_position_occurrence_is_the_prompt_property",
           "the S2 occurrence index is the CODEWORD's occurrence in the prompt (the same value "
           "an S1 record carries for the same row), labelled as a prompt property, with no "
           "per-edit ordinal and no invented edit site",
           _rep2["per_field"]["occurrence index of the codeword"]["value"] == 4
           and _rep2["per_field"]["occurrence index of the codeword"]["is_prompt_property"] is True
           and _s2["rel_end"] is None and _s2["resolved_absolute_index"] is None,
           _rep2["per_field"]["occurrence index of the codeword"]["value"],
           str(_rep2["per_field"]["token position edited (as rel_end AND as the resolved "
                                  "absolute index)"]["value"]))
    try:
        persist_contract_report(pr, _s2_arm, {**_s2, "occurrence_index": None}, gate_stub)
        ok = False
    except RunnerRefusal:
        ok = True
    ck.add("persist_contract_all_position_null_occurrence_refused",
           "an all-position arm that leaves the occurrence index null is REFUSED -- this is the "
           "exact refusal job 869332 hit, and it must survive the fix", ok, 1)
    for _k, _v in (("rel_end", -10), ("resolved_absolute_index", [250])):
        try:
            persist_contract_report(pr, _s2_arm, {**_s2, _k: _v}, gate_stub)
            ok = False
        except RunnerRefusal:
            ok = True
        ck.add("persist_contract_all_position_fabricated_%s_refused" % _k,
               "an all-position arm that FABRICATES a %s is refused: there is no single edit "
               "site, and inventing one would describe an intervention nobody ran" % _k, ok, 1)
    try:
        annotate_liveness([_live_record(rel_end=None, resolved_absolute_index=None)], _stub_arm())
        ok = False
    except RunnerRefusal:
        ok = True
    ck.add("live_single_position_without_a_site_refused",
           "a LIVE SINGLE-position record with no rel_end is refused rather than excused as an "
           "all-position edit (the note used to say 'all positions (S2)' for every record "
           "without one, including the C5 bridge over a single-position hook)", ok, 1)

    # kill condition
    states_nm = {"S1": {"state": KILL_NOT_MOVED, "detail": "d"},
                 "S2": {"state": KILL_MOVED, "detail": "d"}}
    sub, skip = apply_kill_condition([a for a in arms if sel_h2(a)], states_nm)
    ck.add("kill_removes_h2", "H2 arms at a killed site are NOT SUBMITTED",
           all(s["status"] == "NOT_SUBMITTED_UNINFORMATIVE" for s in skip) and len(skip) > 0,
           len(skip), "")
    ck.add("kill_keeps_other_site", "the other site's H2 arms are untouched",
           any(x.scope == "S2" and x.hypothesis == "H2a" for x in sub), len(sub), "")
    ck.add("kill_wording", "the skipped arms are UNINFORMATIVE, never negative",
           all("NEGATIVE" in s["_wording"] for s in skip), len(skip), "")
    try:
        assert_kill_condition_honoured([a for a in arms if a.hypothesis == "H2a"], states_nm)
        ok = False
    except RunnerRefusal:
        ok = True
    ck.add("kill_enforced", "submitting a killed arm anyway is a REFUSAL", ok, 1, "")
    states_un = {"S1": {"state": KILL_UNAVAILABLE, "detail": "d"}}
    sub2, skip2 = apply_kill_condition([a for a in arms if a.hypothesis == "H2a" and a.scope == "S1"],
                                       states_un)
    ck.add("kill_unavailable_is_not_notmoved",
           "an H1 that could not run does NOT kill the primary arm (C-112)",
           len(sub2) > 0 and not skip2, len(sub2), "")

    # order
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        try:
            assert_stage_order(td, "h2", "test")
            ok = False
        except RunnerRefusal:
            ok = True
        ck.add("order_enforced", "stage h2 refuses while q1/smoke/h1 have no DONE.json", ok, 1, "")
        for s in ("q1", "smoke", "h1"):
            os.makedirs(os.path.join(td, "%s_x" % s))
            json.dump({"status": "ok"}, open(os.path.join(td, "%s_x" % s, "DONE.json"), "w"))
        ck.add("order_satisfied", "with all three complete, stage h2 proceeds",
               assert_stage_order(td, "h2", "test")["stage"] == "h2", 1, "")

    # ---- A9: the launch-order gate, RE-DERIVED -------------------------------------------
    _keys = list(direction_gate(pr, "outputs/dcs_ts/directions_pr053")["payload_keys"])
    with tempfile.TemporaryDirectory() as td:
        for s in ("q1", "smoke"):
            os.makedirs(os.path.join(td, "%s_x" % s))
            json.dump({"status": "ok"}, open(os.path.join(td, "%s_x" % s, "DONE.json"), "w"))
        try:
            assert_stage_order(td, "h2", "test")
            ok = False
        except RunnerRefusal:
            ok = True
        ck.add("a9_without_pr_the_gate_is_unchanged",
               "with no `pr` the gate still demands an h1 DONE.json -- the old behaviour is the "
               "default and the exemption is opt-in", ok, 1)
        r = assert_stage_order(td, "h2", "test", pr=pr, payload_keys=_keys)
        st = r["predecessors_by_construction"].get("h1") or {}
        ck.add("a9_h1_satisfied_by_construction",
               "h1 has ZERO constructible arms at this launch, so the h2 predecessor is satisfied "
               "as CANNOT_RUN_BY_CONSTRUCTION -- and NO DONE.json was written for it",
               st.get("state") == PREDECESSOR_BY_CONSTRUCTION and st.get("n_constructible") == 0
               and not os.path.exists(os.path.join(td, "h1_test", "DONE.json")),
               st.get("n_selected", 0),
               "%d/%d constructible" % (st.get("n_constructible", -1), st.get("n_selected", -1)))
        ck.add("a9_reasons_are_persisted",
               "the per-arm reasons the gate re-derived are carried in the record, not discarded",
               len(st.get("unbuildable_reasons") or {}) == st.get("n_selected"),
               len(st.get("unbuildable_reasons") or {}))
        # THE MITIGATION THE AMENDMENT REQUIRED: make ONE h1 arm constructible and the gate must
        # REFUSE again. Without this, a bug in the constructibility path could OPEN the gate.
        _real = globals()["constructibility"]

        def _one_h1_buildable(_pr, arm, keys):
            if arm.arm_id.startswith("h1_s1_bomb_from_knife"):
                return {"arm_id": arm.arm_id, "constructible": True,
                        "intervene_direction": None, "reasons": []}
            return _real(_pr, arm, keys)
        globals()["constructibility"] = _one_h1_buildable
        try:
            assert_stage_order(td, "h2", "test", pr=pr, payload_keys=_keys)
            ok = False
        except RunnerRefusal as e:
            ok = "COULD run must run" in str(e)
        finally:
            globals()["constructibility"] = _real
        ck.add("a9_re_arms_when_an_h1_arm_becomes_constructible",
               "with ONE h1 arm constructible the gate REFUSES again -- the exemption is "
               "re-derived at every launch, never asserted", ok, 1)

    # ---- A14: the stage-aware checklist gate ----------------------------------------------
    g_h2 = checklist_gate(PREREG_DEFAULT, AMENDMENT_DEFAULT, "h2")
    g_h1 = checklist_gate(PREREG_DEFAULT, AMENDMENT_DEFAULT, "h1")
    ck.add("a14_h1_scoped_item_is_scoped_out_of_h2",
           "A3 (the cross-prompt donor) declares applies_to_stages=[h1] and NO h2 arm has mode "
           "'patch', so it is scoped out of h2 -- re-derived, not read off the prose",
           "A3" in {s["id"] for s in g_h2["scoped_out"]}, 1,
           str(sorted(s["id"] for s in g_h2["scoped_out"])))
    ck.add("a14_h1_scoped_item_still_blocks_h1",
           "the SAME item still blocks the stage it applies to",
           any(r.startswith("A3 ") for r in g_h1["blocking"]), 1)
    ck.add("a14_unscoped_blockers_still_block",
           "every BLOCKING item that declares no applies_to_stages still blocks h2",
           all(any(r.startswith(i["id"] + " ") for r in g_h2["blocking"])
               for i in json.load(open(repo_path(AMENDMENT_DEFAULT)))["pre_extraction_checklist"]
               if i["blocking"] and not i["done"] and not i.get("applies_to_stages")), 1,
           "%d blocking reason(s)" % len(g_h2["blocking"]))
    # C-127. This asserted that "analyzer_exists" appears in the LIVE config's blocking list -- i.e.
    # it encoded the then-current state (analyzer_exists == false) as an invariant. When DCS-R-130
    # legitimately flipped the flag to true, having built the verdict path, this check FAILED. A
    # check that hardcodes the present defect state fails exactly when the defect is repaired, which
    # is the opposite of what a check is for. This is the THIRD occurrence of that class in two days
    # (PR-058's identity_gate self-test, mutation M47, and now this one), so it is fixed the same
    # way: assert the GATE'S BEHAVIOUR against an injected false, not the live value.
    _mut = json.load(open(repo_path(AMENDMENT_DEFAULT)))
    _mut["artifacts"]["analyzer_exists"] = False
    import tempfile as _tf
    with _tf.NamedTemporaryFile("w", suffix=".json", delete=False) as _fh:
        json.dump(_mut, _fh)
        _mut_path = _fh.name
    try:
        _g_false = checklist_gate(PREREG_DEFAULT, _mut_path, "h2")
        _blocks_when_false = any("analyzer_exists" in r for r in _g_false["blocking"])
    finally:
        os.unlink(_mut_path)
    ck.add("a14_analyzer_exists_still_gates",
           "artifacts.analyzer_exists == false still refuses, stage-aware or not -- proven by "
           "INJECTING false into a copy, so the check survives the real flag being true",
           _blocks_when_false, 1,
           "live value=%r; injected-false blocks=%r"
           % (json.load(open(repo_path(AMENDMENT_DEFAULT)))["artifacts"]["analyzer_exists"],
              _blocks_when_false))
    _forged = {"id": "ZZ9", "item": "a fabricated blocker", "blocking": True, "done": False,
               "applies_to_stages": ["h1"]}
    ck.add("a14_a_scope_with_no_code_path_is_not_a_scope",
           "an item scoped away from h2 for which this runner has NO re-derivation predicate "
           "BLOCKS -- prose is not enforcement",
           "ZZ9" not in CHECKLIST_STAGE_RELEVANCE and _forged["applies_to_stages"] == ["h1"], 1)

    # ---- A15: provenance on every terminal record -------------------------------------------
    with tempfile.TemporaryDirectory() as td:
        os.environ["SLURM_JOB_ID"] = "999999"
        try:
            write_terminal(td, "DONE.json", {"status": "ok"})
            blob = json.load(open(os.path.join(td, "DONE.json")))
        finally:
            os.environ.pop("SLURM_JOB_ID", None)
        ck.add("a15_terminal_record_names_its_job",
               "every terminal record carries the SLURM job id, node list and host of the "
               "invocation that wrote it",
               blob["provenance"]["slurm_job_id"] == "999999"
               and blob["provenance"]["hostname"] and "written_at" in blob["provenance"], 3,
               str(blob["provenance"])[:110])
    with tempfile.TemporaryDirectory() as td:
        write_terminal(td, "ABORTED.json", {"status": "aborted"})
        ck.add("a15_provenance_is_null_off_a_batch_node",
               "off SLURM the job id is recorded as null rather than invented",
               json.load(open(os.path.join(td, "ABORTED.json")))["provenance"]["slurm_job_id"]
               is None, 1)

    with tempfile.TemporaryDirectory() as td:
        # terminal files
        write_terminal(td, "DONE.json", {"status": "ok"})
        try:
            write_terminal(td, "ABORTED.json", {"status": "aborted"})
            ok = False
        except RunnerRefusal:
            ok = True
        ck.add("one_verdict", "a stage has ONE verdict: DONE and ABORTED cannot coexist", ok, 1, "")
        # resume
        sd = os.path.join(td, "man")
        os.makedirs(sd)
        json.dump({"arms": {"a": {"status": "done", "run_dir": os.path.join(td, "nope")}}},
                  open(os.path.join(sd, MANIFEST_FILE), "w"))
        m = manifest_load(sd, td)
        ck.add("resume_verifies", "a 'done' arm with no DONE.json on disk is reset to pending",
               m["arms"]["a"]["status"] == "pending", 1, m["arms"]["a"]["_reset_reason"][:60])

    # model cache
    class _Stub:
        n = 0

        @staticmethod
        def load_model(model_id, **kw):
            _Stub.n += 1
            return ("model", model_id, _Stub.n)

    c = ModelCache().install(_Stub)
    a1 = _Stub.load_model("m", dtype="bf16", attn_implementation="eager")
    a2 = _Stub.load_model("m", dtype="bf16", attn_implementation="eager")
    c.uninstall()
    ck.add("model_cache", "the model is loaded ONCE and reused -- the reason this file exists",
           a1 is a2 and c.n_loads == 1 and c.n_hits == 1, c.n_loads, "hits=%d" % c.n_hits)

    # probe
    pg = probe_gate("outputs/dcs_ts/pr048_result.json")
    ck.add("probe_attribution_closed",
           "C-118(a): the per-row attribution blocker is CLOSED, so it is no longer a reason to "
           "refuse --emit-probe; the ARTIFACT is the only gate left, and it is checked against "
           "the file on disk rather than assumed",
           not any("attribut" in r.lower() for r in pg["reasons"])
           and (pg["ok"] == (pg["probe_artifact"] == "present")), 1,
           "artifact=%s ok=%s reasons=%d"
           % (pg["probe_artifact"], pg["ok"], len(pg["reasons"])))
    _pg_missing = probe_gate("outputs/dcs_ts/__no_such_pr048_result__.json")
    ck.add("probe_artifact_refused",
           "a MISSING or unverified probe artifact still refuses --emit-probe by name",
           (not _pg_missing["ok"]) and bool(_pg_missing["reasons"]), 1,
           _pg_missing["reasons"][0][:60])
    if pg["ok"]:
        _pargv = build_argv(pr, _stub_arm(),
                            {"fit_dir": "outputs/dcs_ts/directions_pr053",
                             "rel_end": read_site_rel_end(pr), "emit_liveness": True,
                             "constructibility": constructibility(pr, _stub_arm(), payload_keys),
                             "expect_n": 0, "exclude_file": "", "limit": 0,
                             "probe": {"json": "outputs/dcs_ts/pr048_result.json",
                                       "sha": pg["probe_sha256"],
                                       "read_layers": pr.require("read_site", "read_layer_grid"),
                                       "rel_end": read_site_rel_end(pr)}})
        ck.add("probe_argv_pins_the_sha",
               "review F4: the probe argv carries --pr057-probe-sha, so `load_frozen_probe`'s "
               "pin -- published since the export was written and never supplied by any caller "
               "-- is finally enforced at the node",
               "--pr057-probe-sha" in _pargv
               and _pargv[_pargv.index("--pr057-probe-sha") + 1] == pg["probe_sha256"]
               and "--pr057-probe-rel-end=-10" in _pargv, 1,
               str(pg["probe_sha256"])[:16])

    # directions
    try:
        dg = direction_gate(pr, "outputs/dcs_ts/directions_pr053")
        ok = bool(dg["sha256"]) and dg["provenance"]["ok"]
        detail = "sha=%s fit_domains=%d" % (dg["sha256"][:16], dg["provenance"]["n_fit_domains"])
    except (RunnerRefusal, Refusal, PreregError, ImportError) as e:
        ok, detail = False, str(e)[:80]
    ck.add("direction_gate", "the PR-053 payload loads, its sha is recomputed and it is TRAIN-only",
           ok, 1, detail)
    try:
        direction_gate(pr, "outputs/dcs_ts/directions_pr053", expect_sha="0" * 64)
        ok = False
    except RunnerRefusal:
        ok = True
    ck.add("direction_sha_pin", "a direction file whose sha does not match the pin is REFUSED",
           ok, 1, "")

    ck.report()
    print("\n[pr057-runner] self-test: %d check(s), %d FAILED" % (len(ck.rows), ck.n_fail))
    return 1 if ck.n_fail else 0


# ============================================================================================
# 15. MUTATION HARNESS -- every mutation must produce a REFUSAL
# ============================================================================================
def mutate() -> int:
    pr = load_prereg(PREREG_DEFAULT, for_extraction=False)
    payload_keys = ["v_bomb", "v_bomb_specific", "v_remap", "v_knife_specific"]
    assign = load_split(pr)
    bank = repo_path("data/boombness_prompts/boombness_prompt_bank_ts116m_button_bomb.jsonl")
    rel = read_site_rel_end(pr)
    con = constructibility(pr, _stub_arm(), payload_keys)
    ctx = {"fit_dir": "outputs/dcs_ts/directions_pr053", "rel_end": rel, "emit_liveness": True,
           "constructibility": con, "expect_n": 230, "exclude_file": "/x/e.txt", "limit": 0}
    results: List[Tuple[str, str, bool, str]] = []

    def m(name: str, why: str, fn):
        try:
            fn()
        except (RunnerRefusal, Refusal, ZeroBinding, PreregError, SystemExit, AssertionError) as e:
            results.append((name, why, True, ("%s: %s" % (type(e).__name__, e)).splitlines()[0][:110]))
            return
        except Exception as e:                                      # noqa: BLE001
            results.append((name, why, False, "WRONG EXCEPTION %s: %s" % (type(e).__name__, e)))
            return
        results.append((name, why, False, "NO REFUSAL -- the mutation passed"))

    # ---- the five the task names -----------------------------------------------------------
    m("M1_dead_hook", "a hook that never fired must not score as a clean null",
      lambda: _assert_live(annotate_liveness(
          [_live_record(hook_fired_count=0, n_cells_edited_realised=0,
                        projection_removed_l2=0.0, max_abs_delta=0.0)], _stub_arm())))
    m("M2_zero_magnitude_edit", "a hook that fired and changed nothing must not pass",
      lambda: _assert_live(annotate_liveness(
          [_live_record(projection_removed_l2=0.0, max_abs_delta=0.0, cos_pre_post=1.0)],
          _stub_arm())))
    m("M3_direction_sha_mismatch", "an arm whose direction file sha != the pin must be refused",
      lambda: direction_gate(pr, "outputs/dcs_ts/directions_pr053", expect_sha="deadbeef" * 8))
    m("M4a_absolute_edit_index", "an ABSOLUTE (non end-relative) edit index must be refused",
      lambda: _audit_or_raise(annotate_liveness(
          [_live_record(rel_end=10, resolved_absolute_index=[10])], _stub_arm())))
    m("M4b_absolute_index_in_config", "a non-negative rel_end parsed from the file must be refused",
      lambda: _fake_rel_end(pr))
    m("M5_skipped_kill_condition", "an H2 arm at a killed site must not be submitted",
      lambda: assert_kill_condition_honoured(
          [a for a in build_arm_manifest(pr) if a.hypothesis == "H2a" and a.scope == "S1"],
          {"S1": {"state": KILL_NOT_MOVED, "detail": "d"}}))

    # ---- and the ones this runner's own shape makes possible --------------------------------
    m("M6_bridge_as_live", "a DISABLED-hook bridge presented as a live arm must be refused",
      lambda: _assert_live(annotate_liveness(
          [_live_record(enabled=False, hook_fired_count=0, n_cells_edited_realised=0,
                        projection_removed_l2=0.0, max_abs_delta=0.0)], _stub_arm())))
    m("M7_liveness_record_missing_keys", "a record missing a producer key must be refused",
      lambda: annotate_liveness([{k: v for k, v in _live_record().items() if k != "hook_fired_count"}],
                                _stub_arm()))
    m("M8_no_liveness_at_all", "an arm launched without liveness instrumentation must be refused",
      lambda: build_argv(pr, _stub_arm(), {**ctx, "emit_liveness": False}))
    m("M9_unmapped_direction", "an unmapped manifest direction must not resolve by resemblance",
      lambda: build_argv(pr, _stub_arm(direction="v_looks_right"),
                         {**ctx, "constructibility": constructibility(
                             pr, _stub_arm(direction="v_looks_right"), payload_keys)}))
    m("M10_unbuildable_mode_launched", "an arm whose mode has no code path must not be launched",
      lambda: build_argv(pr, _stub_arm(mode="component_replace"),
                         {**ctx, "constructibility": constructibility(
                             pr, _stub_arm(mode="component_replace"), payload_keys)}))
    m("M11_argv_disagrees_with_analyzer", "a runner argv that names a different bank must be refused",
      lambda: assert_argv_agrees_with_analyzer(
          pr, _stub_arm(), _swap(build_argv(pr, _stub_arm(), ctx), "--bank",
                                 "data/boombness_prompts/boombness_prompt_bank_ts116m_button_knife.jsonl"),
          ctx["fit_dir"]))
    m("M12_argv_with_a_space", "a value with a space would be torn apart by BOOMB_ARGS word-splitting",
      lambda: build_argv(pr, _stub_arm(arm_id="a b"), ctx))
    m("M13_partial_run_as_complete", "a run directory with no DONE.json must not be analysed",
      lambda: load_arm_run(repo_path("outputs")))
    m("M14_zero_bind_population", "a split that binds zero rows must refuse",
      lambda: split_bind(pr, bank, "nonexistent_split", assign))
    m("M15_unknown_domain_in_split", "a domain absent from the frozen split manifest must refuse",
      lambda: split_bind(pr, bank, "test", {k: v for k, v in list(assign.items())[:5]}))

    # C-123, job 868569. The smoke stage emitted `--expect-n 670 --limit 40` and score_behavior's
    # row-count guard refused on the GPU after a 27-minute queue wait. assert_expect_n_agrees_with_
    # limit now catches it in the runner. A guard with no mutation is not a proven guard (the M47
    # lesson), so both directions are exercised: a shrunken sample AND a widened one.
    m("M65_expect_n_gt_limit",
      "an --expect-n LARGER than --limit (a silently-shrunken sample) must refuse in the runner",
      lambda: assert_expect_n_agrees_with_limit(
          ["--bank", "b.jsonl", "--expect-n", "670", "--limit", "40"]))
    m("M66_limit_gt_expect_n",
      "a --limit LARGER than --expect-n (a silently-widened population) must refuse too",
      lambda: assert_expect_n_agrees_with_limit(
          ["--bank", "b.jsonl", "--expect-n", "40", "--limit", "670"]))
    import tempfile
    with tempfile.TemporaryDirectory() as _td:
        m("M16_expect_n_mismatch", "a run whose row count is not the bound population must refuse",
          lambda: verify_arm_artifacts(
              pr, _stub_arm(), _fake_run_dir(os.path.join(_td, "a"), 41, [_live_record()]), 230,
              con_dir="v_bomb_specific"))
        m("M17_dead_hook_end_to_end",
          "a COMPLETE-looking run whose hooks never fired must be refused by verify_arm_artifacts",
          lambda: verify_arm_artifacts(
              pr, _stub_arm(),
              _fake_run_dir(os.path.join(_td, "b"), 230,
                            [_live_record(hook_fired_count=0, n_cells_edited_realised=0,
                                          projection_removed_l2=0.0, max_abs_delta=0.0)]), 230,
              con_dir="v_bomb_specific"))
        m("M18_empty_liveness_file",
          "a run with an EMPTY liveness file must not read as 'no violations'",
          lambda: verify_arm_artifacts(
              pr, _stub_arm(), _fake_run_dir(os.path.join(_td, "c"), 230, []), 230,
              con_dir="v_bomb_specific"))
        m("M19_no_arm_manifest_echo",
          "a run with no PR057_ARM.json has no record of what it believed it was doing",
          lambda: verify_arm_artifacts(
              pr, _stub_arm(),
              _fake_run_dir(os.path.join(_td, "d"), 230, [_live_record()], arm_manifest=False),
              230, con_dir="v_bomb_specific"))
        m("M20_no_realized_dose",
          "an arm with no realized_dose has no frac_cellmean_spread_removed and must be refused",
          lambda: verify_arm_artifacts(
              pr, _stub_arm(),
              _fake_run_dir(os.path.join(_td, "e"), 230, [_live_record()], realized_dose=False),
              230, con_dir="v_bomb_specific"))
        # ---- 2026-09-08: the S2 (all-position) persist defect and its two honest limits ----
        _s2arm = _stub_arm(arm_id="h2a_s2_projout_basket", scope="S2", family_member="H2axS2")
        m("M67_all_position_without_the_occurrence_index",
          "an ALL-POSITION arm that does not persist the occurrence index of the codeword must "
          "REFUSE -- it is a property of the PROMPT, required of every arm, and this is the "
          "exact refusal that stopped job 869332 after a clean 230-row run",
          lambda: verify_arm_artifacts(
              pr, _s2arm,
              _fake_run_dir(os.path.join(_td, "s2a"), 230,
                            [_live_record_all(occurrence_index=None,
                                              occurrence_index_is_prompt_property=None,
                                              occurrence_index_source="never computed")]),
              230, con_dir="v_bomb_specific", direction_sha="0" * 64))
        # DIRECT, not end-to-end: with only a rel_end fabricated the end-relative audit refuses
        # FIRST (a rel_end with no resolved index is unauditable), which is a correct refusal for
        # a different reason. The fabrication gate itself is exercised here, and again against
        # `pair_common`'s producer gate as M83-M85 of the analyzer's harness.
        m("M68_all_position_fabricates_a_rel_end",
          "an ALL-POSITION arm that INVENTS a rel_end must refuse: there is no single edit site, "
          "and a fabricated one describes an intervention nobody ran",
          lambda: persist_contract_report(
              pr, _s2arm,
              annotate_liveness([_live_record_all()], _s2arm)[0] | {"rel_end": -10},
              {"realized_dose": {"x": 1}, "direction_file_sha256": "s", "control_draw_seed": 1,
               "output_sha256": "o", "cos_edit_vs_direction": "c"}))
        m("M69_all_position_fabricates_an_absolute_index",
          "an ALL-POSITION arm that INVENTS a resolved_absolute_index must refuse for the same "
          "reason",
          lambda: verify_arm_artifacts(
              pr, _s2arm,
              _fake_run_dir(os.path.join(_td, "s2c"), 230,
                            [_live_record_all(rel_end=-10, seq_len_at_resolution=260,
                                              resolved_absolute_index=[250])]),
              230, con_dir="v_bomb_specific", direction_sha="0" * 64))
        m("M70_live_single_position_with_no_site",
          "a LIVE SINGLE-POSITION arm whose record carries NO rel_end must refuse rather than be "
          "excused as an all-position edit",
          lambda: verify_arm_artifacts(
              pr, _stub_arm(),
              _fake_run_dir(os.path.join(_td, "s2d"), 230,
                            [_live_record(rel_end=None, resolved_absolute_index=None,
                                          seq_len_at_resolution=None)]),
              230, con_dir="v_bomb_specific", direction_sha="0" * 64))
    m("M21_out_of_order_stage", "a confirmatory stage with no completed Q1 must refuse",
      lambda: assert_stage_order(repo_path("outputs", "no_such_state_root_"), "h2", "test"))
    m("M22_zero_domain_delta", "an arm-vs-baseline delta that pairs nothing must refuse",
      lambda: per_domain_delta(
          [{"prompt_id": "a", "domain": "d", "semantic_logodds": 1.0, "logp_concept": 1.0,
            "logp_codeword": 0.0, "option_mass": 0.1}],
          [{"prompt_id": "b", "domain": "d", "semantic_logodds": 0.0, "logp_concept": 1.0,
            "logp_codeword": 1.0, "option_mass": 0.1}]))
    m("M23_persisted_field_is_null",
      "a required persisted quantity that is present but NULL must be refused",
      lambda: persist_contract_report(
          pr, _stub_arm(),
          {**annotate_liveness([_live_record()], _stub_arm())[0], "projection_removed_l2": None},
          {"realized_dose": {"x": 1}, "direction_file_sha256": "s", "control_draw_seed": 1,
           "output_sha256": "o", "cos_edit_vs_direction": "c"}))
    m("M24_identical_control_band", "a 5-draw control band with identical outputs is n=1",
      lambda: _band_or_raise(pr))
    m("M25_probe_without_artifact", "--emit-probe must refuse rather than write an unattributable file",
      lambda: _probe_or_raise())
    # C-119, after the fix. The tripwire stays: an alpha=0 bridge is an IDENTITY, so it would
    # reproduce the baseline with a garbage direction on the wrong layer and certify nothing.
    m("M26_alpha_zero_bridge_certifies_nothing",
      "a disabled-hook bridge at alpha=0 must be REFUSED, not silently certified",
      lambda: _constructible_or_raise(pr, _stub_arm(mode="disabled", expect_enabled=False,
                                                    alpha=0.0), payload_keys))
    m("M27_liveness_record_missing_the_producer_expected_count",
      "a record missing the PRODUCER's n_cells_edited_expected must refuse, and must NOT be "
      "repaired by the runner inventing one (C-117)",
      lambda: annotate_liveness(
          [{k: v for k, v in _live_record().items() if k != "n_cells_edited_expected"}],
          _stub_arm()))

    # ---- A9 / A13 / A14 / A15, 2026-09-08 ---------------------------------------------------
    def _order_with_a_buildable_h1():
        """The mitigation A9's risk section requires: if the constructibility path ever says an
        h1 arm IS buildable, the launch-order gate must REFUSE again rather than open."""
        import tempfile as _tf
        _real = globals()["constructibility"]

        def _fake(_pr, arm, keys):
            if arm.hypothesis == "H1":
                return {"arm_id": arm.arm_id, "constructible": True,
                        "intervene_direction": None, "reasons": []}
            return _real(_pr, arm, keys)
        globals()["constructibility"] = _fake
        try:
            with _tf.TemporaryDirectory() as td:
                for s in ("q1", "smoke"):
                    os.makedirs(os.path.join(td, "%s_x" % s))
                    json.dump({"status": "ok"},
                              open(os.path.join(td, "%s_x" % s, "DONE.json"), "w"))
                assert_stage_order(td, "h2", "test", pr=pr, payload_keys=payload_keys)
        finally:
            globals()["constructibility"] = _real
        raise AssertionError("NOT REFUSED")

    m("M28_h1_becomes_constructible_reopens_the_order_gate",
      "A9 lets a re-derivation OPEN a gate; if any h1 arm is constructible it must refuse again",
      _order_with_a_buildable_h1)

    def _order_on_a_stage_not_allowlisted():
        import tempfile as _tf
        with _tf.TemporaryDirectory() as td:
            # q1 is NOT on RE_DERIVABLE_PREDECESSORS: a missing q1 may never be excused by
            # constructibility, however few arms it turns out to have.
            assert_stage_order(td, "smoke", "train", pr=pr, payload_keys=payload_keys)
        raise AssertionError("NOT REFUSED")

    m("M29_by_construction_exemption_is_allowlisted",
      "only the stages on RE_DERIVABLE_PREDECESSORS may be excused; a missing q1 still refuses",
      _order_on_a_stage_not_allowlisted)

    def _checklist_scope_with_no_predicate():
        g = checklist_gate(PREREG_DEFAULT, AMENDMENT_DEFAULT, "h2")
        saved = dict(CHECKLIST_STAGE_RELEVANCE)
        CHECKLIST_STAGE_RELEVANCE.clear()
        try:
            g2 = checklist_gate(PREREG_DEFAULT, AMENDMENT_DEFAULT, "h2")
        finally:
            CHECKLIST_STAGE_RELEVANCE.update(saved)
        if len(g2["scoped_out"]) or len(g2["blocking"]) <= len(g["blocking"]):
            raise AssertionError("NOT REFUSED")
        raise RunnerRefusal("a stage scope with no re-derivation predicate BLOCKS: %s"
                            % [r[:70] for r in g2["blocking"] if r.startswith("A3 ")][:1])

    m("M30_a_prose_stage_scope_with_no_code_path",
      "an item scoped away from the stage that this runner cannot RE-DERIVE must still block",
      _checklist_scope_with_no_predicate)

    def _checklist_scope_contradicted_by_the_arms():
        saved = CHECKLIST_STAGE_RELEVANCE.get("A3")
        CHECKLIST_STAGE_RELEVANCE["A3"] = ("the stage runs any arm at all",
                                           lambda _pr, _stage: True)
        try:
            g = checklist_gate(PREREG_DEFAULT, AMENDMENT_DEFAULT, "h2")
        finally:
            if saved is not None:
                CHECKLIST_STAGE_RELEVANCE["A3"] = saved
        if any(s["id"] == "A3" for s in g["scoped_out"]):
            raise AssertionError("NOT REFUSED")
        raise RunnerRefusal("the arms contradict the declared scope, so A3 blocks h2")

    m("M31_stage_scope_contradicted_by_the_stages_own_arms",
      "if the stage's OWN arms need the item, the declared applies_to_stages does not excuse it",
      _checklist_scope_contradicted_by_the_arms)

    def _amendment_pinned_to_a_different_parent():
        import tempfile as _tf
        obj = json.load(open(repo_path(AMENDMENT_DEFAULT)))
        obj["amendment"]["amends_file_sha16"] = "0" * 16
        with _tf.NamedTemporaryFile("w", suffix=".json", delete=False,
                                    dir=repo_path("outputs")) as fh:
            json.dump(obj, fh)
            p = fh.name
        try:
            checklist_gate(PREREG_DEFAULT, p, "h2")
        finally:
            os.unlink(p)
        raise AssertionError("NOT REFUSED")

    m("M32_amendment_whose_parent_sha_does_not_match",
      "an amendment that pins a parent sha the file on disk does not have amends nothing",
      _amendment_pinned_to_a_different_parent)

    def _amendment_that_drops_a_parent_blocker():
        import tempfile as _tf
        obj = json.load(open(repo_path(AMENDMENT_DEFAULT)))
        for it in obj["pre_extraction_checklist"]:
            it.pop("supersedes", None)
            it["done"] = True
            it["blocking"] = False
        obj["artifacts"]["analyzer_exists"] = True
        with _tf.NamedTemporaryFile("w", suffix=".json", delete=False,
                                    dir=repo_path("outputs")) as fh:
            json.dump(obj, fh)
            p = fh.name
        try:
            g = checklist_gate(PREREG_DEFAULT, p, "h2")
        finally:
            os.unlink(p)
        if g["ok"]:
            raise AssertionError("NOT REFUSED")
        raise RunnerRefusal("the amendment supersedes no item for the parent's BLOCKING items, so "
                            "they still stand: %s" % g["blocking"][0][:110])

    m("M33_amendment_that_silently_drops_a_parent_blocker",
      "an amendment that closes every item without SUPERSEDING the parent's blockers by name is "
      "a relaxation wearing a supersession's name",
      _amendment_that_drops_a_parent_blocker)

    class _A:
        pass

    def _h2_without_emit_probe():
        a = _A()
        for k, v in dict(prereg=PREREG_DEFAULT, amendment=AMENDMENT_DEFAULT, stage="h2",
                         split="test", fit_dir="outputs/dcs_ts/directions_pr053",
                         runs=RUNS_ROOT_DEFAULT, state_root=STATE_ROOT_DEFAULT,
                         phase7_tag_prefix=PHASE7_TAG_PREFIX_DEFAULT,
                         probe_json="outputs/dcs_ts/pr048_result.json",
                         expect_direction_sha=None, smoke_limit=40, emit_liveness=True,
                         emit_probe=False, dry_run=False, out="").items():
            setattr(a, k, v)
        run_stage(pr, a)
        raise AssertionError("NOT REFUSED")

    m("M34_confirmatory_stage_without_emit_probe",
      "O1 is one of the four conjunctive conditions; an h2 launch without --emit-probe captures "
      "no PR057_PROBE.jsonl and must be refused BEFORE the allocation (A13)",
      _h2_without_emit_probe)

    red = sum(1 for r in results if r[2])
    print("MUTATION HARNESS -- each mutation must produce a REFUSAL")
    for name, why, ok, detail in results:
        print("  [%s] %-32s %s\n        %s" % ("RED" if ok else "GREEN(BAD)", name, why, detail))
    print("\n[pr057-runner] mutations: %d/%d RED" % (red, len(results)))
    return 0 if red == len(results) else 1


def _constructible_or_raise(pr: Prereg, arm: ArmSpec, payload_keys) -> None:
    con = constructibility(pr, arm, payload_keys)
    if con["constructible"]:
        raise AssertionError("NOT REFUSED")
    raise RunnerRefusal("arm %s is not constructible: %s" % (arm.arm_id, con["reasons"][0][:120]))


def _assert_live(ann) -> None:
    lg = liveness_gate(ann, "mutant", expect_enabled=True)
    if not lg["live"]:
        raise RunnerRefusal("liveness gate refuses: %s" % lg["reasons"][:2])


def _audit_or_raise(ann) -> None:
    aud = audit_end_relative([r for r in ann if "_end_relative_audit" not in r])
    if not aud["ok"]:
        raise RunnerRefusal("end-relative audit failed: %s violation(s)"
                            % aud["n_absolute_index_violations"])


def _fake_rel_end(pr: Prereg) -> None:
    obj = json.loads(json.dumps(pr.obj))
    obj["read_site"]["_positions_in_rel_end"] = "codeword_last == rel_end 10 (absolute)"
    read_site_rel_end(Prereg(obj, "<mutant>"))


def _fake_run_dir(td: str, n_rows: int, records: Sequence[Dict[str, Any]],
                  arm_manifest: bool = True, realized_dose: bool = True) -> str:
    """A minimal but REAL score_behavior-shaped run directory, so verify_arm_artifacts is
    exercised end to end rather than a re-typed copy of its arithmetic."""
    d = os.path.join(td, "run")
    os.makedirs(d, exist_ok=True)
    json.dump({"status": "ok", "rows_written": n_rows}, open(os.path.join(d, "DONE.json"), "w"))
    json.dump({"option_mass": {}}, open(os.path.join(d, "summary.json"), "w"))
    json.dump({"model": "stub"}, open(os.path.join(d, "RUNMETA.json"), "w"))
    json.dump({"realized_dose": ({"v_bomb_specific|L9|alpha1": {"cell_residual_frac_removed": 0.09}}
                                 if realized_dose else {})},
              open(os.path.join(d, "metadata.json"), "w"))
    with open(os.path.join(d, "results.jsonl"), "w") as fh:
        for i in range(n_rows):
            fh.write(json.dumps({"prompt_id": "p%d" % i, "domain": "d", "semantic_logodds": 0.0,
                                 "logp_concept": 0.0, "logp_codeword": 0.0,
                                 "option_mass": 0.1}) + "\n")
    with open(os.path.join(d, CONTRACT_LIVENESS), "w") as fh:
        for r in records:
            fh.write(json.dumps(r) + "\n")
    if arm_manifest:
        json.dump({"arm": "stub"}, open(os.path.join(d, CONTRACT_ARM), "w"))
    return d


def _probe_or_raise(path: str = "outputs/dcs_ts/__no_such_pr048_result__.json") -> None:
    """The ARTIFACT half of C-118, which is still a live refusal.

    It used to point at the real result file, where it was reachable only because that file had
    no FROZEN_PROBE block. Now that the block exists, pointing it there would have made the
    mutation GREEN -- an unreachable refusal dressed as a passing test. It points at an absent
    artifact instead, which is the condition the guard is actually for.
    """
    pg = probe_gate(path)
    if not pg["ok"]:
        raise RunnerRefusal("--emit-probe refused: %s" % pg["reasons"][0][:100])


def _band_or_raise(pr: Prereg) -> None:
    n = int(pr.require("seeds", "n_control_draws"))
    g = AN.control_band_gate(["same"] * n, n)
    if not g["ok"]:
        raise RunnerRefusal("control band: %s" % g["detail"])


def _swap(argv: List[str], flag: str, value: str) -> List[str]:
    out = list(argv)
    out[out.index(flag) + 1] = value
    return out


# ============================================================================================
# 16. MAIN
# ============================================================================================
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--prereg", default=PREREG_DEFAULT)
    ap.add_argument("--amendment", default=AMENDMENT_DEFAULT,
                    help="an AMENDMENT config whose pre_extraction_checklist and artifacts "
                         "flags supersede the parent's for the stage-aware gate (A14). It "
                         "must name this preregistration and pin its sha16; pass an empty "
                         "string to gate on the parent alone.")
    ap.add_argument("--stage", default="", choices=["", "q1", "smoke", "h1", "h2"])
    ap.add_argument("--split", default="test", choices=["train", "validation", "test"])
    ap.add_argument("--fit-dir", default="outputs/dcs_ts/directions_pr053",
                    help="the PR-053 TRAIN-ONLY direction DIRECTORY. The loader joins "
                         "directions_fit_dev.pt itself; see C-113 in this file's header.")
    ap.add_argument("--runs", default=RUNS_ROOT_DEFAULT)
    ap.add_argument("--state-root", default=STATE_ROOT_DEFAULT)
    ap.add_argument("--phase7-tag-prefix", default=PHASE7_TAG_PREFIX_DEFAULT)
    ap.add_argument("--probe-json", default="outputs/dcs_ts/pr048_result.json")
    ap.add_argument("--expect-direction-sha", default="")
    ap.add_argument("--smoke-limit", type=int, default=40)
    ap.add_argument("--emit-liveness", action="store_true")
    ap.add_argument("--emit-probe", action="store_true")
    ap.add_argument("--dry-run", action="store_true",
                    help="construct and validate every arm WITHOUT a GPU and without loading the "
                         "model; writes nothing")
    ap.add_argument("--plan", action="store_true", help="print the validated manifest and stop")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--mutate", action="store_true")
    ap.add_argument("--out", default="")
    a = ap.parse_args()
    a.expect_direction_sha = a.expect_direction_sha or None

    if a.self_test:
        return selftest()
    if a.mutate:
        return mutate()

    try:
        pr = load_prereg(a.prereg, for_extraction=False)
    except PreregError as e:
        print("PREREG REFUSAL:\n%s" % e, file=sys.stderr)
        return 2
    AN.check_wording_pin(pr)

    try:
        if a.plan:
            p = plan(pr, a)
            txt = json.dumps(p, indent=2, default=str)
            AN.assert_sayable(txt, AN.forbidden_from_prereg(pr))
            if a.out:
                open(a.out, "w").write(txt)
                print("wrote %s" % a.out)
            else:
                print(txt)
            return 0
        if not a.stage:
            print("--stage is required (one of q1, smoke, h1, h2), or use --plan / --self-test / "
                  "--mutate", file=sys.stderr)
            return 2
        if a.dry_run:
            # the CPU path: everything except invoking score_behavior.
            return run_stage(pr, a)
        return run_stage(pr, a)
    except (RunnerRefusal, Refusal, ZeroBinding, PreregError) as e:
        print("REFUSAL:\n  %s" % e, file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
