#!/usr/bin/env python3
"""Analyser for PR-CSI-001: the causal SUBSPACE rescue of semantic installation.

Consumes one score_behavior run directory per arm and produces the preregistered contrasts on the
concept-free installation endpoint, at the DOMAIN unit, with the preregistration's VOID and
CANNOT-ANSWER checks applied BEFORE any contrast is reported.

WHAT IT REUSES, DELIBERATELY. `y_install` comes from `dcs_cont_layerpos_map.load_installation` --
the same definition, the same concept-free channel filter and the same duplicate-key refusal the
whole phase has used; re-implementing it would be measuring a different thing. `strict_run_dir`,
the domain bootstrap and the exact sign-flip test come from `dcs_csi_rederive_patch`, so "complete
run" and "p-floor" mean exactly one thing across this sprint.

WHAT IT REFUSES TO DO. It will not print a contrast from a run set that fails a VOID condition, it
will not report a recovery fraction on a degenerate denominator, and it will not report a p without
its attainable floor beside it.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import math
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "scripts"))


def _load(mod, path):
    s = importlib.util.spec_from_file_location(mod, os.path.join(REPO, path))
    m = importlib.util.module_from_spec(s)
    sys.modules[mod] = m
    s.loader.exec_module(m)
    return m


rederive = _load("rederive", "scripts/dcs_csi_rederive_patch.py")
lpm = _load("lpm", "scripts/dcs_cont_layerpos_map.py")


def installation_with_option_mass_keys(run_dir, floor):
    """The set of (domain, slot) keys whose option mass clears `floor` in THIS run."""
    keep = set()
    with open(os.path.join(run_dir, "results.jsonl"), encoding="utf-8") as fh:
        for line in fh:
            r = json.loads(line)
            if r.get("query_kind") != "semantic_one_word" or r.get("cell") != "C":
                continue
            om = r.get("option_mass")
            if om is None:
                raise SystemExit("row %r has no option_mass" % r.get("prompt_id"))
            if om >= floor:
                keep.add((r["domain"], lpm.family_slot(r["family_id"])))
    return keep, None


def installation_with_option_mass(run_dir, floor):
    """`load_installation` plus a per-row OPTION-MASS floor (sprint item P1-f).

    WHY THIS EXISTS. `y_install` is a two-way softmax over `logp_concept` and `logp_codeword`. On a
    row whose option mass is ~1e-4 the model's actual prediction is some third word entirely, so the
    ratio is arithmetically fine and epistemically thin. The phase's frozen gate is POOLED, so such
    rows survive it. Rather than change the protocol -- which would make these numbers incomparable
    with DR-071/A1, the very record this pipeline was validated against -- the primary contrast is
    computed on ALL rows and RE-computed above a floor, and both are reported.

    The selection logic (semantic_one_word, cell C, the (domain, family_slot) key, the duplicate-key
    refusal, the missing-field refusal) is kept identical to `lpm.load_installation`; at floor=0.0
    this function must reproduce it exactly, which `_assert_matches_loader` checks.
    """
    out, n_dropped = {}, 0
    with open(os.path.join(run_dir, "results.jsonl"), encoding="utf-8") as fh:
        for line in fh:
            r = json.loads(line)
            if r.get("query_kind") != "semantic_one_word" or r.get("cell") != "C":
                continue
            lc, lk = r.get("logp_concept"), r.get("logp_codeword")
            if lc is None or lk is None:
                raise SystemExit("row %r has no logp_concept/logp_codeword; missing != zero"
                                 % r.get("prompt_id"))
            om = r.get("option_mass")
            if om is None:
                raise SystemExit("row %r has no option_mass; cannot apply the P1-f floor"
                                 % r.get("prompt_id"))
            k = (r["domain"], lpm.family_slot(r["family_id"]))
            if k in out:
                raise SystemExit("installation key %r binds two rows" % (k,))
            if om < floor:
                n_dropped += 1
                continue
            m = max(lc, lk)
            out[k] = math.exp(lc - m) / (math.exp(lc - m) + math.exp(lk - m))
    return out, n_dropped


def _assert_matches_loader(run_dir):
    """At floor 0 the local re-implementation must equal the frozen loader, key for key."""
    a, dropped = installation_with_option_mass(run_dir, 0.0)
    b, _, _ = lpm.load_installation(run_dir)
    if dropped or set(a) != set(b) or any(abs(a[k] - b[k]) > 1e-12 for k in a):
        raise SystemExit("P1-f re-implementation disagrees with lpm.load_installation on %r -- "
                         "the sensitivity arm must measure the same thing as the primary" % run_dir)


def arm_key_values(run_dir, assign, keep_split):
    """(domain, slot) -> y_install for one arm, restricted to one split. Keys, not domain means.

    main() intersects these ACROSS ARMS before averaging. See the note on `keep_keys` below: a row
    that one arm lost (e.g. the degeneracy refusal legitimately dropping a control row) would
    otherwise make that arm's domain mean an average over FEWER SLOTS than the arms it is paired
    against -- the same defect review R2-B1 found in the option-mass path, arriving by a different
    route.
    """
    _assert_matches_loader(run_dir)
    inst, n_rows, kinds = lpm.load_installation(run_dir)
    return ({k: v for k, v in inst.items() if assign.get(k[0]) == keep_split}, n_rows, kinds)


def arm_domain_means(run_dir, assign, keep_split, keep_keys=None):
    """(domain -> mean y_install over that domain's slots) for one arm, restricted to one split.

    `keep_keys`, when given, is the SINGLE key set used for EVERY arm -- see `reference_key_set`.
    """
    _assert_matches_loader(run_dir)
    inst, n_rows, kinds = lpm.load_installation(run_dir)
    n_dropped = 0
    if keep_keys is not None:
        before = len(inst)
        inst = {k: v for k, v in inst.items() if k in keep_keys}
        n_dropped = before - len(inst)
    by = {}
    for (dom, slot), p in inst.items():
        if assign.get(dom) != keep_split:
            continue
        by.setdefault(dom, []).append(p)
    return {d: sum(v) / len(v) for d, v in by.items()}, n_rows, kinds, n_dropped


def reference_key_set(run_dir, floor):
    """The P1-f retained key set, defined from ONE reference arm and then applied to ALL arms.

    *** REVIEW R2-B1, AND IT WAS A BLOCKER. ***
    The first version applied the option-mass floor to each arm INDEPENDENTLY. `option_mass` is an
    OUTCOME of the intervention, so that is selection on a post-treatment variable -- a collider --
    and it deletes an arm-dependent, outcome-correlated slice. Because the analyser then intersected
    only DOMAINS and never slots, the paired domain means were averages over DIFFERENT slot sets.
    Measured on the real arms: at floor 0.20, BASE kept 435/670 rows and KO kept 582, and the
    manipulation contrast read -0.330 instead of -0.221 -- a **49 % inflation** manufactured
    entirely by the filter.

    The fix is to choose the key set ONCE, from the reference arm (default BASE, the un-intervened
    condition, i.e. the closest thing here to a pre-treatment measurement), and hold it fixed across
    every arm. That is still conditioning on a measured quantity and is NOT strictly pre-treatment --
    stated openly rather than hidden -- but it cannot differ between arms, which is the defect that
    mattered.
    """
    inst, _ = installation_with_option_mass_keys(run_dir, floor)
    return inst


def row_meta(run_dir):
    """Liveness, dose and basis identity, read from the rows -- never from the summary."""
    out = {"n_rows": 0, "prefill_edits_min": None, "decode_edits_total": 0,
           "rescue_fired": 0, "rescue_layers": set(), "basis_keys": set(), "rescue_basis": None,
           "norm_match_keys": set(), "written_norm": [], "captured_frac": [],
           "degenerate_positions": 0, "n_rescue_positions": set(),
           "liveness_violations": 0, "models": set(), "knockout_scopes": set(),
           "written_norm_by_pid": {}}
    pre = []
    with open(os.path.join(run_dir, "results.jsonl")) as f:
        for line in f:
            r = json.loads(line)
            out["n_rows"] += 1
            out["models"].add(r.get("model"))
            out["knockout_scopes"].add(r.get("knockout_scope"))
            if r.get("hook_liveness_violations"):
                out["liveness_violations"] += 1
            if r.get("hook_n_prefill_edits") is not None:
                pre.append(r["hook_n_prefill_edits"])
            out["decode_edits_total"] += (r.get("hook_n_decode_edits") or 0)
            rl = r.get("rescue_liveness")
            if rl:
                if rl.get("fired"):
                    out["rescue_fired"] += 1
                if rl.get("written_norm_mean") is not None:
                    out["written_norm"].append(rl["written_norm_mean"])
                    out["written_norm_by_pid"][r["prompt_id"]] = rl["written_norm_mean"]
                if rl.get("captured_energy_frac_mean") is not None:
                    out["captured_frac"].append(rl["captured_energy_frac_mean"])
                out["degenerate_positions"] += (rl.get("n_positions_norm_match_degenerate") or 0)
                out["n_rescue_positions"].add(rl.get("n_positions"))
            if r.get("rescue_layer") is not None:
                out["rescue_layers"].add(r["rescue_layer"])
            if r.get("rescue_basis_key"):
                out["basis_keys"].add(r["rescue_basis_key"])
            if r.get("rescue_basis"):
                out["rescue_basis"] = r["rescue_basis"]
            if r.get("rescue_norm_match_key"):
                out["norm_match_keys"].add(r["rescue_norm_match_key"])
            if r.get("rescue_basis_meta"):
                out.setdefault("basis_meta", set()).add(
                    json.dumps(r["rescue_basis_meta"], sort_keys=True))
    out["prefill_edits_min"] = min(pre) if pre else None
    for k in ("rescue_layers", "basis_keys", "norm_match_keys", "models", "knockout_scopes",
              "n_rescue_positions"):
        out[k] = sorted(x for x in out[k] if x is not None)
    bm = out.pop("basis_meta", None)
    if bm:
        if len(bm) != 1:
            raise SystemExit("run %r mixes %d different rescue_basis_meta values -- the arm did "
                             "not use one basis" % (run_dir, len(bm)))
        out["basis_meta"] = json.loads(list(bm)[0])
    for k in ("written_norm", "captured_frac"):
        v = out[k]
        out[k] = {"mean": round(sum(v) / len(v), 6), "min": round(min(v), 6),
                  "max": round(max(v), 6)} if v else None
    return out


def holm(pairs):
    """Holm-Bonferroni over (name, p). Returns name -> (p, adjusted_p, rejected_at_0.05)."""
    s = sorted(pairs, key=lambda kv: kv[1])
    m = len(s)
    out, running = {}, 0.0
    for i, (name, p) in enumerate(s):
        adj = min(1.0, max(running, (m - i) * p))
        running = adj
        out[name] = {"p": p, "p_holm": round(adj, 6), "rejected_at_0.05": adj < 0.05}
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--codeword", required=True)
    ap.add_argument("--tag-prefix", required=True,
                    help="run tags are <prefix>_<arm>; e.g. csi1_button -> csi1_button_KO")
    ap.add_argument("--expect-n", type=int, required=True)
    ap.add_argument("--arms", required=True,
                    help="comma list of arm names, e.g. BASE,KO,KO_SELF,KO_FULL,KO_AXIS,KO_ORTH,...")
    ap.add_argument("--candidate-arm", default="KO_AXIS")
    ap.add_argument("--comparator-arm", default="KO_ORTH")
    ap.add_argument("--full-arm", default="KO_FULL")
    ap.add_argument("--ko-arm", default="KO")
    ap.add_argument("--base-arm", default="BASE")
    ap.add_argument("--self-arm", default="KO_SELF")
    ap.add_argument("--split", default="train", choices=("train", "validation"))
    ap.add_argument("--control-prefixes", default="KO_SHUF,KO_RAND",
                    help="arm-name prefixes forming the control distribution for the specificity "
                         "test. Use KO_R5RAND,KO_R5SHUF when the candidate is the rank-5 subspace.")
    ap.add_argument("--allow-short", type=int, default=0,
                    help="accept arms short by at most N rows, provided DONE.json's count matches "
                         "the rows on disk. The cross-arm key intersection makes a short arm safe; "
                         "a ledger/file DISAGREEMENT is never accepted.")
    ap.add_argument("--n-boot", type=int, default=20000)
    ap.add_argument("--option-mass-reference", default="BASE",
                    help="P1-f: the ONE arm whose option mass defines the retained key set, then "
                         "applied identically to every arm. Never per-arm -- option_mass is an "
                         "outcome, so a per-arm filter is post-treatment selection (review R2-B1).")
    ap.add_argument("--option-mass-floor", type=float, default=0.0,
                    help="P1-f sensitivity: drop rows whose (concept, codeword) option mass is "
                         "below this before computing y_install. 0.0 = the frozen protocol, which "
                         "gates option mass POOLED and is what every number in the record used.")
    ap.add_argument("--self-inert-tol", type=float, default=0.005,
                    help="|KO_SELF - KO| above this VOIDs the run: the patch is not writing what "
                         "it read, so no rescue number is interpretable")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    assign = lpm.load_split()
    arms = [x for x in a.arms.split(",") if x]
    dirs, dmeans, meta, kv = {}, {}, {}, {}
    keep_keys = None
    if a.option_mass_floor > 0.0:
        if a.option_mass_reference not in arms:
            raise SystemExit("--option-mass-reference %r is not among --arms" % a.option_mass_reference)
        _refdir = rederive.strict_run_dir("%s_%s" % (a.tag_prefix, a.option_mass_reference),
                                          a.expect_n, row_file="results.jsonl",
                                          allow_short=a.allow_short)
        keep_keys = reference_key_set(_refdir, a.option_mass_floor)
        print("[P1-f] key set from reference arm %s at floor %g: %d keys retained"
              % (a.option_mass_reference, a.option_mass_floor, len(keep_keys)))
    for arm in arms:
        d = rederive.strict_run_dir("%s_%s" % (a.tag_prefix, arm), a.expect_n,
                                    row_file="results.jsonl", allow_short=a.allow_short)
        dirs[arm] = d
        kv[arm], n_inst, kinds = arm_key_values(d, assign, a.split)
        n_drop = 0
        meta[arm] = row_meta(d)
        # BANK IDENTITY. `prompt_id` is derived from the row's AXES, not its text, so it is 100%
        # shared between the button and basket banks (measured: 4002/4002), while `prompt_sha16`
        # overlaps only 25% (the codeword-degenerate cells). That means an arm accidentally run on
        # the wrong codeword's bank would pass every prompt_id-based check silently. The bank path
        # is therefore read from the run's own config and asserted here.
        cfg = json.load(open(os.path.join(d, "config.json")))["args"]
        meta[arm]["bank"] = cfg.get("bank")
        meta[arm]["exclude_prompt_ids"] = cfg.get("exclude_prompt_ids")
        meta[arm]["attn_impl"] = cfg.get("attn_impl")
        meta[arm]["dtype"] = cfg.get("dtype")
        meta[arm]["installation_rows_all_splits"] = n_inst
        meta[arm]["rows_dropped_by_option_mass_floor"] = n_drop
        meta[arm]["channels_present"] = kinds
        print("[dir ] %-10s %-52s  %s-keys=%d"
              % (arm, os.path.basename(d), a.split, len(kv[arm])))

    # ---- INTERSECT KEYS ACROSS ARMS, then average. Domain-only intersection was not enough:
    # an arm that lost a single row still contributed a domain whose mean was over fewer slots.
    common_keys = set.intersection(*[set(kv[x]) for x in arms])
    if keep_keys is not None:
        common_keys &= keep_keys
    if not common_keys:
        raise SystemExit("REFUSING: no (domain, slot) key common to all arms on split=%s" % a.split)
    per_arm_lost = {x: len(kv[x]) - len(common_keys) for x in arms}
    for x in arms:
        by = {}
        for k in common_keys:
            by.setdefault(k[0], []).append(kv[x][k])
        dmeans[x] = {d: sum(v) / len(v) for d, v in by.items()}
        meta[x]["keys_before_intersection"] = len(kv[x])
        meta[x]["keys_dropped_by_intersection"] = per_arm_lost[x]
    if any(per_arm_lost.values()):
        print("[keys] intersected to %d keys common to all arms; dropped per arm: %s"
              % (len(common_keys), {k: v for k, v in per_arm_lost.items() if v}))
    doms = sorted({k[0] for k in common_keys})
    if not doms:
        raise SystemExit("REFUSING: no domain common to all arms on split=%s" % a.split)

    # ---------------------------------------------------------------- VOID conditions, first
    void = []
    banks = {meta[x]["bank"] for x in arms}
    if len(banks) != 1:
        void.append("arms used DIFFERENT banks: %s" % sorted(banks))
    elif a.codeword not in (list(banks)[0] or ""):
        void.append("bank %r does not name codeword %r" % (list(banks)[0], a.codeword))
    excls = {meta[x]["exclude_prompt_ids"] for x in arms}
    if len(excls) != 1:
        void.append("arms used DIFFERENT exclusion files: %s" % sorted(excls))
    for x in arms:
        if meta[x]["attn_impl"] != "eager":
            void.append("%s: attn_impl=%r (the knockout requires eager)" % (x, meta[x]["attn_impl"]))
        if meta[x]["dtype"] != "bfloat16":
            void.append("%s: dtype=%r" % (x, meta[x]["dtype"]))
    # REVIEW R3-M6. BASE was exempt from EVERY liveness check, so a BASE arm carrying a live
    # knockout and live rescue hooks passed with VOID [] and all three gates true -- and BASE is
    # the denominator of the manipulation gate and the recovery fraction. The sibling verifier
    # (dcs_csi_rederive_patch) has this assertion; this one did not.
    _b = meta.get(a.base_arm)
    if _b is not None:
        if _b["prefill_edits_min"]:
            void.append("%s (the BASE arm) has a LIVE knockout (min prefill edits=%s) -- it must "
                        "be unintervened" % (a.base_arm, _b["prefill_edits_min"]))
        if _b["decode_edits_total"]:
            void.append("%s (the BASE arm) has %d decode-time edits" % (a.base_arm,
                                                                        _b["decode_edits_total"]))
        if _b["rescue_fired"]:
            void.append("%s (the BASE arm) fired a rescue on %d rows -- it must be unintervened"
                        % (a.base_arm, _b["rescue_fired"]))
        if _b.get("rescue_basis") or _b["basis_keys"]:
            void.append("%s (the BASE arm) declares a rescue basis %r" % (a.base_arm,
                                                                          _b["basis_keys"]))
    for arm in arms:
        m = meta[arm]
        if m["n_rows"] != a.expect_n and (a.expect_n - m["n_rows"]) > a.allow_short:
            void.append("%s: %d rows != expect_n %d (beyond --allow-short %d)"
                        % (arm, m["n_rows"], a.expect_n, a.allow_short))
        if m["liveness_violations"]:
            void.append("%s: %d rows with hook liveness violations" % (arm, m["liveness_violations"]))
        if len(m["models"]) != 1:
            void.append("%s: %d distinct model revisions" % (arm, len(m["models"])))
        if arm != a.base_arm:
            if not m["prefill_edits_min"]:
                void.append("%s: knockout not live on every row (min prefill edits=%r)"
                            % (arm, m["prefill_edits_min"]))
            if m["decode_edits_total"]:
                void.append("%s: %d decode-time edits (must be 0)" % (arm, m["decode_edits_total"]))
        # REVIEW R2-M1. The identity arm was EXEMPT from this check -- and it is precisely the arm
        # whose null IS a gate. A self-patch that never fires is byte-identical to KO, so the
        # identity gate reads exactly 0.0 and PASSES for the worst possible reason. Demonstrated by
        # the reviewer end-to-end: rescue_fired 0/100, VOID [], all gates true, "PRIMARY PASSES".
        # No arm that declares a rescue is exempt.
        if arm.startswith("KO_") and arm != a.base_arm and arm != a.ko_arm:
            if m["rescue_fired"] != m["n_rows"]:
                void.append("%s: rescue fired on %d of the %d rows it persisted"
                            % (arm, m["rescue_fired"], m["n_rows"]))
        if len({tuple(meta[x]["rescue_layers"]) for x in arms if meta[x]["rescue_layers"]}) > 1:
            pass  # reported below once, not per arm
    layers_used = {x: meta[x]["rescue_layers"] for x in arms if meta[x]["rescue_layers"]}
    if len({tuple(v) for v in layers_used.values()}) > 1:
        void.append("rescued arms used DIFFERENT layers: %s" % layers_used)
    if len({tuple(meta[x]["n_rescue_positions"]) for x in arms if meta[x]["n_rescue_positions"]}) > 1:
        void.append("rescued arms wrote DIFFERENT position counts: %s"
                    % {x: meta[x]["n_rescue_positions"] for x in arms})
    test_in = [d for d in doms if assign.get(d) == "test"]
    if test_in:
        void.append("TEST LEAK: %s" % test_in[:5])

    # ---- REVIEW R2-M2: ARM IDENTITY. The analyser trusted the arm LABEL and never checked that
    # the arms actually differ in the way their names claim. The reviewer produced a run set in
    # which the candidate and the comparator both carried `cand_rank1` and no basis at all, and it
    # emitted a full contrast table with VOID [] -- a publishable negative from an arm contrasted
    # with itself. `dcs_csi_rederive_patch.ARM_SPEC` does this job for its arms; this had no
    # equivalent. These checks are that equivalent.
    _cand, _comp = a.candidate_arm, a.comparator_arm
    if _cand in meta and _comp in meta:
        ck = meta[_cand]["basis_keys"]
        pk = meta[_comp]["basis_keys"]
        if not ck:
            void.append("%s declares no rescue_basis_key -- it is not a subspace arm" % _cand)
        if not pk:
            void.append("%s declares no rescue_basis_key -- it is not a subspace arm" % _comp)
        if ck and pk and ck == pk:
            void.append("candidate %s and comparator %s used the SAME basis key %s -- this would "
                        "contrast an arm with itself" % (_cand, _comp, ck))
        if not meta[_comp]["norm_match_keys"]:
            void.append("%s is not norm-matched (no rescue_norm_match_key) -- it cannot be the "
                        "matched-dose comparator" % _comp)
    for arm in arms:
        if meta[arm].get("rescue_basis") is None and arm not in (a.base_arm, a.ko_arm, a.self_arm,
                                                                 a.full_arm):
            void.append("%s carries rescue_basis=None but is treated as a subspace arm" % arm)
    # every arm must agree on the intervention it is NOT varying
    for fld in ("knockout_scopes",):
        vals = {tuple(meta[x][fld]) for x in arms if x != a.base_arm}
        if len(vals) > 1:
            void.append("arms disagree on %s: %s" % (fld, sorted(vals)))

    # ---- norm matching: the candidate and every norm-matched control must agree per row --------
    cand_norm = (meta.get(a.candidate_arm) or {}).get("written_norm")
    for arm in arms:
        m = meta.get(arm) or {}
        if not m.get("norm_match_keys"):
            continue
        if m["degenerate_positions"]:
            void.append("%s: %d norm-match-degenerate positions (control injected a deterministic "
                        "basis vector rather than a projection)" % (arm, m["degenerate_positions"]))
        # NORM MATCH ON COMMON ROWS. Comparing per-arm MEANS is wrong whenever two arms persisted
        # different row sets -- a short arm's mean is over a different population, so a real match
        # reads as a mismatch (and a real mismatch could read as a match). This is the same
        # "averages over non-identical key sets" defect as review R2-B1 and S-047, in a third
        # place. The comparison is therefore per prompt_id over the intersection.
        _cw = (meta.get(a.candidate_arm) or {}).get("written_norm_by_pid") or {}
        _aw = m.get("written_norm_by_pid") or {}
        # REVIEW R3-M5. If the CANDIDATE records no written_norm (e.g. --candidate-arm KO_FULL,
        # whose whole-state DonorPatch emits none), `_cw` is empty and this whole check silently
        # evaporated -- a mismatched control then passed with VOID []. A norm-matched control
        # whose reference cannot be read is not checkable, and that is a VOID, not a pass.
        if _aw and not _cw:
            void.append("%s declares a norm-match but the candidate arm %r records no written_norm "
                        "-- the match cannot be verified" % (arm, a.candidate_arm))
        if _cw and _aw:
            shared = set(_cw) & set(_aw)
            if not shared:
                void.append("%s: no prompt_id shared with the candidate for a norm check" % arm)
            else:
                worst = max(abs(_aw[p] - _cw[p]) for p in shared)
                if worst > 1e-5:
                    void.append("%s: written norm differs from the candidate by up to %.3e on "
                                "%d shared rows -- NOT norm-matched" % (arm, worst, len(shared)))

    # ---- IN-SAMPLE detection (review M4). The axis is fit on TRAIN, so a TRAIN evaluation is
    # in-sample BY DESIGN and is the gate, not the claim; VALIDATION is the claim. This makes the
    # distinction a recorded fact rather than an assumption, by reading the fit-domain fingerprint
    # off the rows and the fit-domain LIST out of the axis artifact the rows name.
    in_sample = {}
    for arm in arms:
        bmeta = meta[arm].get("basis_meta")
        if not bmeta:
            continue
        cand = os.path.join(REPO, "configs",
                            os.path.basename(str(meta[arm].get("rescue_basis") or "")).replace(".pt", ".json"))
        fit_doms = None
        if os.path.exists(cand):
            fit_doms = set((json.load(open(cand)).get("fit_population") or {}).get("domains") or [])
        n_overlap = len(set(doms) & fit_doms) if fit_doms is not None else None
        in_sample[arm] = {"fit_split": bmeta.get("fit_split"),
                          "n_fit_domains": bmeta.get("n_fit_domains"),
                          "fit_domains_sha16": bmeta.get("fit_domains_sha16"),
                          "basis_sha16": bmeta.get("basis_sha16"),
                          "scored_domains_also_in_fit": n_overlap,
                          "evaluation_is_in_sample": (None if n_overlap is None else n_overlap > 0)}

    out = {"schema": "dcs_csi_subspace/1", "prereg": "configs/dcs_csi_pr001_subspace_rescue.json",
           "in_sample": in_sample,
           "codeword": a.codeword, "split": a.split, "arms": arms,
           "option_mass_floor": a.option_mass_floor,
           "run_dirs": {k: os.path.basename(v) for k, v in dirs.items()},
           "n_domains": len(doms), "n_keys_common": len(common_keys), "arm_meta": meta,
           "installation_by_arm": {x: round(sum(dmeans[x][d] for d in doms) / len(doms), 5)
                                   for x in arms},
           "VOID": void}

    if void:
        out["VERDICT"] = "VOID -- %d condition(s) triggered; no contrast is reported" % len(void)
        _write(out, a); 
        for v in void:
            print("  VOID: %s" % v)
        print("\nVERDICT:", out["VERDICT"])
        return 2

    def contrast(x, y):
        b = rederive.boot_paired_diff(doms, dmeans[x], dmeans[y], a.n_boot, 20260915)
        e = rederive.exact_signflip(doms, dmeans[x], dmeans[y])
        b.update({"p_two_sided": e["p_two_sided"], "p_floor": e["p_floor"],
                  "p_floor_basis": e.get("p_floor_basis"),
                  "k_informative_domains": e["k_informative_domains"], "test_mode": e["mode"],
                  "p_at_its_floor": e["p_two_sided"] <= e["p_floor"] * (1 + 1e-9)})
        return b

    C = {}
    # ---- gate 1: manipulation check ------------------------------------------------------------
    C["manipulation_ko_minus_base"] = contrast(a.ko_arm, a.base_arm)
    # ---- gate 2: identity control --------------------------------------------------------------
    C["identity_self_minus_ko"] = contrast(a.self_arm, a.ko_arm)
    # ---- gate 3: instrument capability ---------------------------------------------------------
    C["positive_control_full_minus_ko"] = contrast(a.full_arm, a.ko_arm)
    # ---- the preregistered PRIMARY -------------------------------------------------------------
    C["PRIMARY_candidate_minus_comparator"] = contrast(a.candidate_arm, a.comparator_arm)
    # ---- secondary -----------------------------------------------------------------------------
    C["candidate_minus_ko"] = contrast(a.candidate_arm, a.ko_arm)
    for arm in arms:
        if arm in (a.base_arm, a.ko_arm, a.self_arm):
            continue
        C["recovery_%s_minus_ko" % arm] = contrast(arm, a.ko_arm)

    gates = {
        "manipulation_check": C["manipulation_ko_minus_base"]["point"] < 0,
        "identity_check": abs(C["identity_self_minus_ko"]["point"]) <= a.self_inert_tol,
        "instrument_capable": (C["positive_control_full_minus_ko"]["point"] > 0
                               and C["positive_control_full_minus_ko"]["ci95"][0] > 0),
    }
    out["gates"] = gates

    # ---- specificity: candidate vs EACH shuffled/random control, Holm-corrected -----------------
    ctrl_arms = [x for x in arms if x.startswith(tuple(a.control_prefixes.split(",")))]
    pairs = []
    for c in ctrl_arms:
        k = "specificity_candidate_minus_%s" % c
        C[k] = contrast(a.candidate_arm, c)
        # P1-h: specificity is ONE-SIDED. The two-sided p answers "does the candidate DIFFER from
        # this control", which in S-049 fired on a control that was unusually NEGATIVE and would
        # have been read as evidence FOR the candidate. Holm is applied to the one-sided p.
        os_ = rederive.exact_signflip_one_sided(doms, dmeans[a.candidate_arm], dmeans[c])
        C[k]["p_one_sided_candidate_beats_control"] = os_["p_one_sided"]
        C[k]["p_one_sided_floor"] = os_["p_floor"]
        pairs.append((c, os_["p_one_sided"]))
    if pairs:
        out["specificity_holm"] = holm(pairs)
        out["specificity_test"] = ("ONE-SIDED sign-flip (candidate > control), Holm-corrected "
                                   "across the control family (P1-h)")
        out["specificity_all_controls_rejected"] = all(
            v["rejected_at_0.05"] for v in out["specificity_holm"].values())
        ctrl_rec = {c: C["recovery_%s_minus_ko" % c]["point"] for c in ctrl_arms}
        cand_rec = C["candidate_minus_ko"]["point"]
        out["control_recovery_distribution"] = {
            "candidate": round(cand_rec, 5),
            "controls": {c: round(v, 5) for c, v in ctrl_rec.items()},
            "candidate_rank_among_controls": 1 + sum(1 for v in ctrl_rec.values() if v >= cand_rec),
            "n_controls": len(ctrl_rec),
            "rank_p_floor": round(1.0 / (len(ctrl_rec) + 1), 4),
        }

    # ---- recovery fraction, with the degeneracy guard -------------------------------------------
    out["recovery_fraction_candidate_of_full"] = rederive.recovery_fraction(
        doms, dmeans[a.full_arm], dmeans[a.ko_arm], dmeans[a.candidate_arm],
        a.n_boot, 20260915, min_denominator=0.01)

    out["contrasts"] = C
    out["domain_means"] = {x: {d: round(dmeans[x][d], 5) for d in doms} for x in arms}

    if not gates["manipulation_check"]:
        out["VERDICT"] = "VOID -- the knockout did not reduce installation on this bank"
    elif not gates["identity_check"]:
        out["VERDICT"] = "VOID -- the self-patch identity control is not inert"
    elif not gates["instrument_capable"]:
        out["VERDICT"] = ("CANNOT ANSWER -- the whole-state rescue itself does not recover "
                          "installation, so there is no capable instrument for the subspace "
                          "question. This is NOT a negative result.")
    else:
        p = C["PRIMARY_candidate_minus_comparator"]
        dist = out.get("control_recovery_distribution")
        single_ok = (p["point"] > 0 and p["ci95"][0] > 0 and p["p_two_sided"] < 0.05
                     and not p["p_at_its_floor"])
        if dist and dist["n_controls"] >= 2:
            # P1-i. When a control FAMILY exists, the verdict comes from the candidate's position in
            # the DISTRIBUTION, never from one named comparator. With a control spread of +-0.005
            # (S-050) the single-comparator verdict is decided by which control the caller happened
            # to name: against the most negative rank-5 control the same data said "PRIMARY PASSES"
            # (p=5e-6), against the most positive it said FAIL (p=0.869). A verdict that flips with
            # an arbitrary naming choice is not a verdict.
            rank, n = dist["candidate_rank_among_controls"], dist["n_controls"]
            rank_p = rank / float(n + 1)
            out["verdict_basis"] = {
                "rule": "candidate's rank within the control distribution (P1-i)",
                "candidate_rank": rank, "n_controls": n,
                "rank_p": round(rank_p, 4), "rank_p_floor": dist["rank_p_floor"],
                "single_comparator_verdict_SUPPRESSED": (
                    "would have said %s against --comparator-arm %s; not reported, see S-050"
                    % ("PASS" if single_ok else "FAIL", a.comparator_arm))}
            # REVIEW R3-B1. The previous rule required `rank == 1 AND rank_p < 0.05`, but
            # rank_p = rank/(n+1) bottoms out at 1/(n+1) -- so PASS needed n >= 20 controls and was
            # DEAD CODE on every run in the record (n = 10, 8, 4). Worse, the else-branch then
            # printed "It is INSIDE the controls, not above them" even at rank 1, which is simply
            # false. Two separate facts are now reported separately: WHERE the candidate sits, and
            # WHETHER the control count could certify it.
            attainable = dist["rank_p_floor"] < 0.05
            if rank == 1 and attainable:
                out["VERDICT"] = ("PRIMARY PASSES on split=%s -- candidate is strictly the largest "
                                  "of %d controls (rank p=%.4g < 0.05)" % (a.split, n, rank_p))
            elif rank == 1:
                out["VERDICT"] = (
                    "PRIMARY INCONCLUSIVE on split=%s -- the candidate is strictly the LARGEST of "
                    "its %d controls, but with only %d controls the attainable rank-p floor is "
                    "%.4g, which is above 0.05. Being top of the distribution is real; certifying "
                    "it at alpha=0.05 needs at least %d controls. NOT a pass and NOT a failure."
                    % (a.split, n, n, dist["rank_p_floor"], 19))
            else:
                out["VERDICT"] = (
                    "PRIMARY DOES NOT PASS on split=%s -- the candidate ranks %d of %d in its own "
                    "control distribution (rank p=%.4g, attainable floor %.4g): %d control(s) "
                    "recover at least as much as it does. It is INSIDE the controls, not above "
                    "them." % (a.split, rank, n + 1, rank_p, dist["rank_p_floor"], rank - 1))
        elif single_ok:
            out["VERDICT"] = ("PRIMARY PASSES on split=%s -- candidate beats its norm-matched "
                              "comparator (NOTE: only %d control(s) present; a single comparator is "
                              "an arbitrary draw when the control spread is wide -- S-050)"
                              % (a.split, (dist or {}).get("n_controls", 0)))
        else:
            out["VERDICT"] = ("PRIMARY DOES NOT PASS on split=%s -- see p, p_floor and the CI "
                              "before calling this a negative" % a.split)

    _write(out, a)
    print("\ninstallation by arm:", json.dumps(out["installation_by_arm"]))
    print("gates:", json.dumps(gates))
    for k in ("manipulation_ko_minus_base", "identity_self_minus_ko",
              "positive_control_full_minus_ko", "PRIMARY_candidate_minus_comparator",
              "candidate_minus_ko"):
        print("  %-38s %s" % (k, json.dumps(C[k])))
    print("\nVERDICT:", out["VERDICT"])
    return 0


def _write(out, a):
    outp = a.out or os.path.join(REPO, "reports/DCS_CSI_SUBSPACE_%s_%s%s.json"
                         % (a.codeword, a.split,
                            "" if a.option_mass_floor <= 0 else "_om%g" % a.option_mass_floor))
    json.dump(out, open(outp, "w"), indent=1)
    print("wrote", os.path.relpath(outp, REPO))


if __name__ == "__main__":
    raise SystemExit(main())
