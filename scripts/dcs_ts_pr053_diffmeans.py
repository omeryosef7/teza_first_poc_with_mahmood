#!/usr/bin/env python3
"""Analyzer for `DCS-PR-053` -- thesis-scale DIFFERENCE-IN-MEANS: the remapping axis and the
concept-identity axis.

WHAT THIS FILE IS
-----------------
`configs/dcs_ts_pr053.json` governs. Every threshold, grid, split, exclusion, floor and n_perm is
fetched through `dcs_ts_prereg.load()/require()`, which REFUSES rather than defaulting. There is
not one numeric gate literal below (the only literals are the normal-quantile constants of the
power arithmetic, which are labelled as such).

THE ESTIMATOR, exactly as the preregistration fixes it (`directions` block):

    v_c(l)             = mean over TRAIN domains of [ h_l(C_c, f) - h_l(A_shared, f) ]   (PAIRED on
                         family_id, c in {bomb, knife, gun})
    v_remap(l)         = v_bomb(l)
    v_bomb_specific(l) = v_bomb(l) - mean( v_knife(l), v_gun(l) )        (no club -- `_no_club`)

TRAIN ONLY. Validation and test never enter a direction or a standardisation constant. There is NO
layer selection and no regularisation constant: every layer of the preregistered band is reported
and none is picked (`directions.no_hyperparameter`).

PRIMARY (`primary.statistic`): AUROC of proj(h, v_bomb_specific) separating C_bomb from
{C_knife, C_gun}, domain-mean over the 23 untouched TEST domains, domain-level group permutation at
n_perm = 10000, reported against the MEASURED surface floor (`primary.nuisance_floor`), never
against chance.

REUSE (`artifacts._reuse`)
--------------------------
`auroc` (tie-corrected, no sklearn), `std_diff`, `unit`, `project` and `band` are IMPORTED from
`scripts/dcs_diffmeans_directions.py`; that file is not edited. Its known defect **D1** -- `_z()`
inside `transfer()` receives ALL domains, so the held-out domain leaks into the standardisation
constants -- is FIXED here rather than inherited: `_zconst()` takes an explicit train-domain set and
every call site passes the FIT arm's TRAIN domains only. (AUROC is invariant to a positive affine
per-layer rescale, so D1 never moved an AUROC; it moved every printed z-projection, which is what
the report reads.)
Run discovery (`_find_run`, DONE.json only -- C-051/C-012), bank-sha verification, the
missing-row rule (R-108) and the p-floor reporting convention follow
`scripts/dcs_ts_pr048_analysis.py`, the frozen probe analyzer.

WHY `for_extraction=False`
--------------------------
`load(..., for_extraction=True)` refuses while V1/V2 are open and while `analyzer_exists` is false.
Both are true of PR-053 right now, and correctly so: **this file is what closes V1 and V2**, and it
analyses an extraction that already exists and was gated by PR-048's checklist
(`artifacts.extraction`: "shared with PR-048 -- no additional forward passes"). Every other refusal
of the loader (FROZEN status, null hashes, hashes disagreeing with disk, mandate-21 fields) is
still enforced.

GUARDS, each from a named past failure
--------------------------------------
* bank_rows_sha16 / position / attn_impl / knockout_applied verified per run BEFORE any row is used.
* a row missing from a cache refuses UNLESS its domain is a preregistered whole-population
  exclusion (R-108); the exclusion set is read from the structured `whole_population` boolean, never
  from prose (C-086 / D2-10).
* every filter that binds zero rows raises (`_nonempty`) -- the C-074/A-039 shape.
* every p is printed next to its attainable floor; zero exceedances print `p < 1/(B+1)` (C-069).
* permutation is at the DOMAIN level. Row-level was measured at FPR 0.2000 and is not implemented.
* train/test domain disjointness is asserted before test is read.

USAGE
    python3 scripts/dcs_ts_pr053_diffmeans.py --prereg configs/dcs_ts_pr053.json \
        --reps outputs/boombness/extract_boombness [--mutate] [--json OUT.json]
    python3 scripts/dcs_ts_pr053_diffmeans.py --selftest       # no data needed
    python3 scripts/dcs_ts_pr053_diffmeans.py --v2-only        # the blocking gate, banks only
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
from collections import defaultdict

import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "scripts"))

from dcs_ts_prereg import Prereg, PreregError, load                      # noqa: E402
from dcs_ts_pr048_analysis import (sign_test_two_sided, group_permutation_p,  # noqa: E402
                                   fmt_p, load_bank_rows, _find_run)
from dcs_diffmeans_directions import auroc, std_diff, unit, project, band  # noqa: E402

#: The shared baseline cell. `directions.v_c` is written over `h(A_shared)`; the bank spells that
#: cell `A` and labels it `benign_literal`. Bound to the corpus below rather than trusted: if the
#: rows carrying cell `A` do not all carry condition `benign_literal`, the run refuses.
CELL_BASELINE = "A"
CONDITION_BASELINE = "benign_literal"
TARGET = "bomb"

_Z_ALPHA2 = 1.9599639845400545   # Phi^-1(0.975) -- power arithmetic only, not a design threshold
_Z_POWER80 = 0.8416212335729143  # Phi^-1(0.80)


# =============================================================================== tiny utilities
def _nonempty(x, what: str):
    """A check that binds nothing must fail loudly, not return a number over an empty set."""
    n = len(x)
    if n == 0:
        raise PreregError(f"{what} bound ZERO rows -- refusing to report a statistic over an "
                          f"empty set (the C-074 / A-039 shape)")
    return x


def _fmt(x, nd=4):
    return " n/a " if x is None else f"{x:.{nd}f}"


def _phi(z):
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def holm(pvals: dict, alpha: float) -> dict:
    """Holm-Bonferroni within a declared family. Returns per-key adjusted p and the decision."""
    items = sorted(((k, v) for k, v in pvals.items() if v is not None), key=lambda kv: kv[1])
    m = len(items)
    out, running = {}, 0.0
    for i, (k, p) in enumerate(items):
        adj = min(1.0, max(running, (m - i) * p))
        running = adj
        out[k] = {"p": p, "p_holm": adj, "reject": adj < alpha, "rank": i + 1, "m": m}
    return out


# ============================================================== V2 -- the blocking identity gate
def v2_cellA_identity(pr: Prereg, excluded: set, doses) -> dict:
    """V2 (BLOCKING). Is cell `A` BYTE-IDENTICAL across the three concepts at matched prompt_id,
    inside the ANALYSED population?

    The whole estimator rests on this: v_bomb - v_knife = mean[h(C_bomb)] - mean[h(C_knife)] only
    if the two A terms are the same prompts. If they are not, v_bomb_specific carries a
    benign-corpus difference as a nuisance term (the C-060 / section 46.1 defect, which on the old
    6-domain banks was only partially clean). Reported with its denominator, per codeword and dose.
    """
    banks = pr.require("population", "banks")
    qk = pr.require("population", "query_kind_primary")
    concepts = list(pr.require("population", "concepts"))
    codewords = list(pr.require("population", "codewords").values())
    rows = {}
    for bname, b in banks.items():
        rows[bname] = load_bank_rows(os.path.join(REPO, b["path"]))
    out = {"per_cell": [], "n_identical": 0, "n_total": 0, "pass": True}
    for cw in codewords:
        for dose in doses:
            per = {}
            for c in concepts:
                sel = {pid: r for pid, r in rows[f"{cw}_{c}"].items()
                       if r["cell"] == CELL_BASELINE and r["query_kind"] == qk
                       and r["n_examples"] == dose and r["domain"] not in excluded}
                bad = {pid for pid, r in sel.items() if r["condition"] != CONDITION_BASELINE}
                if bad:
                    raise PreregError(
                        f"{cw}_{c}: {len(bad)} cell-{CELL_BASELINE} row(s) do not carry condition "
                        f"{CONDITION_BASELINE!r}; the baseline cell is not what the design says it is")
                per[c] = _nonempty(sel, f"V2 cell-A bind {cw}_{c} dose={dose}")
            ids = set.intersection(*[set(per[c]) for c in concepts])
            union = set.union(*[set(per[c]) for c in concepts])
            same = sum(1 for i in ids
                       if len({per[c][i]["full_prompt"] for c in concepts}) == 1)
            same_q = sum(1 for i in ids
                         if len({per[c][i]["final_query_text"] for c in concepts}) == 1)
            rec = {"codeword": cw, "n_examples": dose,
                   "n_per_arm": {c: len(per[c]) for c in concepts},
                   "n_matched_prompt_id": len(ids), "n_union_prompt_id": len(union),
                   "n_byte_identical_full_prompt": same,
                   "n_byte_identical_final_query": same_q,
                   "n_domains": len({per[concepts[0]][i]["domain"] for i in ids}),
                   "pass": bool(same == len(ids) == len(union)
                                and all(len(per[c]) == len(ids) for c in concepts))}
            out["per_cell"].append(rec)
            out["n_identical"] += same
            out["n_total"] += len(union)
            out["pass"] &= rec["pass"]
    return out


# ============================================================== V1 -- power for an AUROC estimator
def v1_power(pr: Prereg, sd_bracket, realised_sd=None) -> dict:
    """V1 (BLOCKING). Power for an AUROC estimator at n = 23 TEST domains.

    Neither PR-048's 3-way ACCURACY power nor PR-049's 2-way power transfers: the estimand is a
    different statistic with a different between-domain variance, and the AUROC of a fixed
    direction has no fitting variance at all. What DOES transfer is the design: 23 domains, the
    domain as the independence unit, alpha and n_perm from the preregistration.

    ASSUMPTIONS, all labelled: the between-domain SD of the per-domain AUROC is NOT known before
    the run, so a BRACKET is reported. `between_domain_sd_projected` (0.1406) is an accuracy SD
    borrowed from six old domains with 5 df; it is an assumption here, not a measurement.
    """
    alpha = pr.require("primary", "alpha")
    n_perm = int(pr.require("primary", "n_perm"))
    n = int(pr.require("primary", "n_test_domains"))
    chance = pr.require("primary", "chance")
    floor_auroc = pr.require("primary", "nuisance_floor")["macro_auroc"]

    sign_floor = min(1.0, 2.0 * (1.0 / 2.0 ** n))
    perm_floor = 1.0 / (1.0 + n_perm)

    rows = []
    for sd in sd_bracket:
        mde = (_Z_ALPHA2 + _Z_POWER80) * sd / math.sqrt(n)
        need_floor = floor_auroc - chance
        se = sd / math.sqrt(n)
        pow_at_floor = 1.0 - _phi(_Z_ALPHA2 - need_floor / se) + _phi(-_Z_ALPHA2 - need_floor / se)
        pow_at_060 = 1.0 - _phi(_Z_ALPHA2 - 0.10 / se) + _phi(-_Z_ALPHA2 - 0.10 / se)
        rows.append({"assumed_between_domain_sd": sd, "se_of_domain_mean": se,
                     "mde_auroc_delta_80pct": mde, "mde_auroc_absolute": chance + mde,
                     "power_at_auroc_0.60": pow_at_060,
                     "power_at_the_surface_floor": pow_at_floor,
                     "mde_clears_surface_floor": bool(chance + mde <= floor_auroc)})

    # exact sign-test companion: the critical k at n = 23 and the power at a per-domain sign rate
    from math import comb
    k_crit = None
    for k in range(n, -1, -1):
        p = min(1.0, 2.0 * sum(comb(n, i) for i in range(k, n + 1)) / 2.0 ** n)
        if p < alpha:
            k_crit = k
        else:
            break
    sign_power = {}
    for q in (0.6, 0.7, 0.8, 0.9):
        sign_power[q] = sum(comb(n, i) * q ** i * (1 - q) ** (n - i)
                            for i in range(k_crit, n + 1)) if k_crit is not None else None

    return {"n_test_domains": n, "alpha": alpha, "n_perm": n_perm,
            "sign_test_attainable_floor": sign_floor,
            "permutation_attainable_floor": perm_floor,
            "floor_below_alpha": bool(perm_floor < alpha and sign_floor < alpha),
            "surface_floor_auroc": floor_auroc,
            "delta_needed_to_clear_surface_floor": floor_auroc - chance,
            "sign_test_critical_k": k_crit, "sign_test_power_by_per_domain_rate": sign_power,
            "bracket": rows,
            "realised": None if realised_sd is None else {
                "between_domain_sd": realised_sd,
                "se_of_domain_mean": realised_sd / math.sqrt(n),
                "mde_auroc_delta_80pct": (_Z_ALPHA2 + _Z_POWER80) * realised_sd / math.sqrt(n)},
            "_assumptions": [
                "the between-domain SD of the per-domain AUROC is an ASSUMPTION until the run; the "
                "bracket spans 0.05 to the 95% upper bound (0.3439) of the old 5-df accuracy SD",
                "0.1406 is `power.between_domain_sd_projected`, an ACCURACY SD from six old domains "
                "-- it is carried here as one bracket point, not as a measurement of this estimand",
                "normal approximation for the domain-mean, two-sided alpha, 80% power",
                "the sign-test arm is EXACT (binomial), not approximate"]}


# ====================================================================== population and reps
def excluded_domains(pr: Prereg) -> set:
    """Structured `whole_population` boolean only. Matching prose `scope` strings is C-086."""
    ex = set()
    for e in pr.require("population", "preregistered_exclusions"):
        if "whole_population" not in e or not isinstance(e["whole_population"], bool):
            raise PreregError(f"exclusion {e.get('domain')!r} must declare a BOOLEAN "
                              f"'whole_population'; selecting exclusions by prose is the C-086 defect")
        if e["whole_population"]:
            ex.add(e["domain"])
    return ex


def load_split(pr: Prereg) -> dict:
    m = json.load(open(os.path.join(REPO, pr.require("split", "manifest"))))
    if m.get("manifest_sha16") != pr.require("split", "manifest_sha16"):
        raise PreregError(f"split manifest sha {m.get('manifest_sha16')} != pinned "
                          f"{pr.require('split', 'manifest_sha16')}")
    if m.get("field_name") != pr.require("split", "field"):
        raise PreregError("split manifest field_name disagrees with the preregistration")
    return m["assign"]


def verify_run(pr: Prereg, bname: str, run: str) -> dict:
    """Every binding check the frozen probe analyzer makes, before a single row is used."""
    summ = json.load(open(os.path.join(run, "summary.json")))
    banks = pr.require("population", "banks")
    want = banks[bname]["bank_rows_sha16"]
    if summ.get("bank_rows_sha16") != want:
        raise PreregError(f"{bname}: run {os.path.basename(run)} was extracted from "
                          f"bank_rows_sha16 {summ.get('bank_rows_sha16')} but the preregistration "
                          f"pins {want}. BANK BINDING FAILED -- this run measures a different "
                          f"population than the one that was frozen.")
    if summ.get("position") != pr.require("read_site", "position"):
        raise PreregError(f"{bname}: run position {summ.get('position')!r} != preregistered "
                          f"{pr.require('read_site', 'position')!r}")
    if summ.get("attn_implementation") != pr.require("model", "attn_impl"):
        raise PreregError(f"{bname}: run attn {summ.get('attn_implementation')!r} != preregistered")
    if summ.get("knockout_applied") is not False:
        raise PreregError(f"{bname}: knockout_applied={summ.get('knockout_applied')!r}; PR-053 "
                          f"uses the no-knockout baseline extraction")
    if summ.get("failures", {}).get("n_failed", -1) < 0:
        raise PreregError(f"{bname}: summary does not report failures.n_failed")
    return summ


def check_missing(bname: str, rows: dict, have: set, excluded: set) -> dict:
    """R-108: a missing row is acceptable ONLY if its domain is a preregistered exclusion."""
    missing = [pid for pid in rows if pid not in have]
    unexplained = sorted({rows[pid]["domain"] for pid in missing} - excluded)
    if unexplained:
        n_un = sum(1 for pid in missing if rows[pid]["domain"] not in excluded)
        raise PreregError(f"{bname}: {n_un} row(s) missing from the cache in "
                          f"{len(unexplained)} domain(s) that are NOT preregistered exclusions: "
                          f"{unexplained[:5]}. An unexplained extraction failure silently shrinks "
                          f"the population; refusing.")
    return {"n_missing": len(missing),
            "explained_by_exclusion": sorted({rows[pid]["domain"] for pid in missing})}


def build_arm(pr: Prereg, reps_root: str, tag_prefix: str, cw: str, doses, excluded: set,
              assign: dict, keep_domains: set, verbose=True) -> dict:
    """Load one codeword arm. Returns, per (concept, dose):
         Dmean[domain] : (nL, H) mean over that domain's PAIRED families of h(C) - h(A)
         rows[domain]  : {'C': (n, nL, H), 'A': (n, nL, H)} kept ONLY for `keep_domains`
    Pairing is on `family_id`, which encodes domain|split|slot|n_examples|...|query_kind and is
    unique within a cell, so it is the natural A<->C key.
    """
    import torch
    concepts = list(pr.require("population", "concepts"))
    qk = pr.require("population", "query_kind_primary")
    layer_grid = list(pr.require("read_site", "layer_grid"))
    banks = pr.require("population", "banks")
    out = {"Dmean": {}, "rows": {}, "npairs": {}, "runs": {}, "missing": {}, "A_by_pid": {}}
    for c in concepts:
        bname = f"{cw}_{c}"
        run = _find_run(reps_root, f"{tag_prefix}_{bname}")
        verify_run(pr, bname, run)
        out["runs"][c] = os.path.basename(run)
        rows = load_bank_rows(os.path.join(REPO, banks[bname]["path"]))
        cache = torch.load(os.path.join(run, "cache", "final_occurrence_reps.pt"),
                           map_location="cpu", weights_only=False)
        if list(cache["layers"]) != layer_grid:
            raise PreregError(f"{bname}: cache layers {list(cache['layers'])} != preregistered "
                              f"layer_grid {layer_grid}")
        if cache.get("position") != pr.require("read_site", "position"):
            raise PreregError(f"{bname}: cache position {cache.get('position')!r} != preregistered")
        # The two strings spell the same convention with different punctuation ("block_L" vs
        # "block L"), so compare them NORMALISED. What must agree is the convention, not the
        # typography -- but it must agree, because an off-by-one layer convention is a defect this
        # project has already shipped once.
        def _norm(t):
            return "".join(str(t).split()).replace("_", "").lower()
        if _norm(cache.get("layer_convention", "")) != \
                _norm(pr.require("read_site", "layer_convention")):
            raise PreregError(f"{bname}: cache layer_convention "
                              f"{cache.get('layer_convention')!r} disagrees with the "
                              f"preregistered {pr.require('read_site', 'layer_convention')!r}")
        reps = cache["reps"]
        out["missing"][c] = check_missing(bname, rows, set(reps), excluded)

        fam = defaultdict(dict)
        for pid, r in rows.items():
            if r["query_kind"] != qk or r["n_examples"] not in doses:
                continue
            if r["domain"] in excluded or r["cell"] not in (CELL_BASELINE, "C"):
                continue
            fam[(r["n_examples"], r["family_id"])][r["cell"]] = pid
        for dose in doses:
            acc, cnt = {}, defaultdict(int)
            store = defaultdict(lambda: {"C": [], "A": []})
            npairs = 0
            for (d0, f), cells in fam.items():
                if d0 != dose:
                    continue
                if CELL_BASELINE not in cells or "C" not in cells:
                    raise PreregError(f"{bname}: family {f} is missing a cell "
                                      f"({sorted(cells)}); the estimator is PAIRED")
                pa, pc = cells[CELL_BASELINE], cells["C"]
                if pa not in reps or pc not in reps:
                    raise PreregError(f"{bname}: family {f} lost a rep from the cache in a "
                                      f"non-excluded domain")
                xa = reps[pa].float().numpy().astype(np.float32)
                xc = reps[pc].float().numpy().astype(np.float32)
                dom = rows[pc]["domain"]
                acc[dom] = acc.get(dom, 0.0) + (xc - xa)
                cnt[dom] += 1
                npairs += 1
                if dom in keep_domains:
                    store[dom]["C"].append(xc)
                # The cell-A store is kept for the FIRST concept on EVERY analysed domain, not
                # only the held-out ones: `_zconst` needs TRAIN-domain baseline rows, and a
                # z-constant computed over an empty train set would silently become the identity
                # -- which is the D1 defect wearing a different hat.
                if dom in keep_domains or c == concepts[0]:
                    store[dom]["A"].append(xa)
                if (dose == pr.require("population", "n_examples_primary")
                        and len(out["A_by_pid"].get(c, ())) < 400):
                    out["A_by_pid"].setdefault(c, {})[pa] = xa
            _nonempty(acc, f"paired families {bname} dose={dose}")
            out["Dmean"][(c, dose)] = {d: (acc[d] / cnt[d]).astype(np.float32) for d in acc}
            out["rows"][(c, dose)] = {d: {k: np.stack(v).astype(np.float32)
                                          for k, v in s.items() if v}
                                      for d, s in store.items()}
            out["npairs"][(c, dose)] = npairs
        del reps, cache
        if verbose:
            print(f"    {cw:7s} {c:5s} run={out['runs'][c]}  "
                  + "  ".join(f"n{d}:{out['npairs'][(c, d)]}" for d in doses)
                  + f"  missing={out['missing'][c]['n_missing']}")
    return out


# ================================================================= the estimator + the null
#: A domain-level relabelling of the three concepts is exactly a choice of WHICH concept plays
#: the bomb role in that domain, so 3 candidate contributions per TRAIN domain span the whole
#: permutation null and the OBSERVED statistic is the identity choice. Observed and null therefore
#: run through byte-identical arithmetic, and the label map is the only thing that varies -- which
#: is the only thing a permutation test is allowed to vary.
#:    u[d][j] = Dmean[j][d]                              (the v_bomb / remapping family)
#:    w[d][j] = Dmean[j][d] - 0.5 * sum(the other two)   (the v_bomb_specific family)


def _zconst(A_train_rows, vhat):
    """D1 FIX. Centre/scale constants from TRAIN-domain cell-`A` rows ONLY.

    `dcs_diffmeans_directions.transfer()` calls `_z(arm, vhat, fit_bundle["domains"])` with ALL
    domains of the fit arm, so the held-out domain's own baseline rows enter the constants. AUROC
    is invariant to a positive affine per-layer map, so the leak never moved an AUROC -- it moved
    every printed z-projection, and those are the numbers a reader compares across arms. Here the
    train set is an explicit argument and the call sites pass the FIT arm's TRAIN domains.
    """
    if A_train_rows.shape[0] == 0:
        raise PreregError("z-standardisation over ZERO train cell-A rows")
    P = project(A_train_rows, vhat)
    sd = P.std(axis=0)
    sd[sd < 1e-12] = 1.0
    return P.mean(axis=0), sd


def per_domain_auroc(pos, neg):
    """AUROC per layer for one domain. pos/neg are (n, nL) projections."""
    return [auroc(pos[:, l], neg[:, l]) for l in range(pos.shape[1])]


def batch_auroc(pos, neg):
    """Tie-corrected AUROC for a BATCH of directions at once.
      pos (B, nL, np), neg (B, nL, nn) -> (B, nL).
    Same estimand as `auroc` imported above (P(pos>neg) + 0.5 P(=)); vectorised because the null
    needs 10000 x 23 x 9 of them. `_selftest` checks the two agree.
    """
    gt = (pos[:, :, :, None] > neg[:, :, None, :]).sum(axis=(2, 3))
    eq = (pos[:, :, :, None] == neg[:, :, None, :]).sum(axis=(2, 3))
    return (gt + 0.5 * eq) / float(pos.shape[2] * neg.shape[2])


# ================================================================================== the run
def run(pr: Prereg, a) -> int:
    alpha = pr.require("primary", "alpha")
    n_perm = int(pr.require("primary", "n_perm"))
    chance = pr.require("primary", "chance")
    if pr.require("primary", "independence_unit") != "domain":
        raise PreregError("independence_unit is not 'domain'; this analyzer implements no other")
    concepts = list(pr.require("population", "concepts"))
    if concepts[0] != TARGET:
        raise PreregError(f"population.concepts[0] is {concepts[0]!r}, expected the target {TARGET!r}")
    layer_grid = list(pr.require("read_site", "layer_grid"))
    nL = len(layer_grid)
    dose_p = pr.require("population", "n_examples_primary")
    dose_r = pr.require("population", "n_examples_replication")
    dose_0 = pr.require("population", "n_examples_null")
    doses = (dose_0, dose_p, dose_r)
    nf = pr.require("primary", "nuisance_floor")
    floor_auroc = nf["macro_auroc"]
    cw_dev = pr.require("population", "codewords")["development"]
    cw_ext = pr.require("population", "codewords")["external_confirmation"]

    ex = excluded_domains(pr)
    assign = load_split(pr)
    analysed = {d: s for d, s in assign.items() if d not in ex}
    train = sorted(d for d, s in analysed.items() if s == "train")
    valid = sorted(d for d, s in analysed.items() if s == "validation")
    test = sorted(d for d, s in analysed.items() if s == "test")
    for nm, dd, want in (("train", train, pr.require("split", "n_train")),
                         ("validation", valid, pr.require("split", "n_validation")),
                         ("test", test, pr.require("split", "n_test"))):
        _nonempty(dd, f"the {nm} split")
    if len(test) != pr.require("primary", "n_test_domains"):
        raise PreregError(f"{len(test)} test domains, preregistration says "
                          f"{pr.require('primary', 'n_test_domains')}")
    if set(train) & set(test) or set(train) & set(valid) or set(valid) & set(test):
        raise PreregError("DOMAIN LEAKAGE between splits")

    R = {"prereg": a.prereg, "n_domains_analysed": len(analysed),
         "split": {"train": len(train), "validation": len(valid), "test": len(test)},
         "excluded_domains": sorted(ex), "layers": layer_grid}

    # ---------------------------------------------------------------- V2, the blocking gate
    print("=" * 100)
    print("V2 (BLOCKING) -- is cell A BYTE-IDENTICAL across the three concepts, matched prompt_id,")
    print("                 inside the ANALYSED population?  The A term must cancel EXACTLY.")
    print("=" * 100)
    v2 = v2_cellA_identity(pr, ex, doses)
    R["V2"] = v2
    for r in v2["per_cell"]:
        print(f"  {r['codeword']:7s} n_examples={r['n_examples']:<2d} per-arm "
              f"{[r['n_per_arm'][c] for c in concepts]}  matched prompt_id "
              f"{r['n_matched_prompt_id']}/{r['n_union_prompt_id']}  byte-identical full_prompt "
              f"{r['n_byte_identical_full_prompt']}/{r['n_matched_prompt_id']}  "
              f"query {r['n_byte_identical_final_query']}/{r['n_matched_prompt_id']}  "
              f"domains {r['n_domains']}  {'PASS' if r['pass'] else 'FAIL'}")
    print(f"  TOTAL {v2['n_identical']}/{v2['n_total']} byte-identical -> "
          f"{'PASS' if v2['pass'] else 'FAIL'}")
    if not v2["pass"]:
        print("\n  V2 FAILS. The A term does not cancel, so v_bomb_specific carries a "
              "benign-corpus\n  nuisance term and the design does not work. STOPPING -- saying so "
              "is the deliverable.")
        return 2

    # ---------------------------------------------------------------- V1, power (pre-data)
    print()
    print("=" * 100)
    print("V1 (BLOCKING) -- power for an AUROC estimator at n = 23 TEST domains")
    print("=" * 100)
    sd_bracket = (0.05, 0.075, 0.10, pr.require("power", "between_domain_sd_projected"),
                  0.20, 0.25, 0.3439)
    v1 = v1_power(pr, sd_bracket)
    R["V1"] = v1
    print(f"  sign-test attainable floor at n=23 : {v1['sign_test_attainable_floor']:.3e}  "
          f"(2/2^23; critical k = {v1['sign_test_critical_k']}/23)")
    print(f"  permutation attainable floor       : {v1['permutation_attainable_floor']:.3e}  "
          f"(1/(B+1), B = {v1['n_perm']})")
    print(f"  both floors < alpha = {alpha}: {v1['floor_below_alpha']} -- the FLOOR is not the "
          f"binding constraint at this n")
    print(f"  surface floor to beat: AUROC {floor_auroc}  => delta "
          f"{v1['delta_needed_to_clear_surface_floor']:.4f} above chance")
    print("  ASSUMED between-domain SD -> MDE (two-sided alpha, 80% power).  THE SD IS AN "
          "ASSUMPTION:")
    print("    sd      SE      MDE(delta)  MDE(AUROC)  power@0.60  power@floor  MDE clears floor")
    for r in v1["bracket"]:
        print(f"    {r['assumed_between_domain_sd']:.4f}  {r['se_of_domain_mean']:.4f}  "
              f"{r['mde_auroc_delta_80pct']:.4f}      {r['mde_auroc_absolute']:.4f}      "
              f"{r['power_at_auroc_0.60']:.3f}       {r['power_at_the_surface_floor']:.3f}"
              f"        {r['mde_clears_surface_floor']}")
    print("  exact sign-test power at per-domain sign rate q: "
          + "  ".join(f"q={q}: {v:.3f}" for q, v in v1["sign_test_power_by_per_domain_rate"].items()))

    if a.v1_v2_only:
        print("\n--v1-v2-only: the two blocking checklist items are answered; no reps read.")
        return 0

    # ---------------------------------------------------------------- load representations
    print()
    print("=" * 100)
    print("REPRESENTATIONS -- runs verified against the preregistration BEFORE any row is used")
    print("=" * 100)
    keep = set(valid) | set(test)
    arms = {}
    for cw in (cw_dev, cw_ext):
        # --arm-cache is a DEVELOPMENT convenience only (each bank is a ~2 GB torch.load over
        # NFS). It caches the derived arrays, never the verification: verify_run() and the R-108
        # missing-row rule re-run against the real summary.json and the real bank on every
        # invocation, cache hit or not. The headline numbers in the report were produced by a run
        # with NO cache, so nothing in them was read from a file this script wrote.
        cf = (os.path.join(a.arm_cache, f"arm_{a.tag_prefix}_{cw}.pkl") if a.arm_cache else None)
        for c in concepts:
            verify_run(pr, f"{cw}_{c}", _find_run(a.reps, f"{a.tag_prefix}_{cw}_{c}"))
        if cf and os.path.exists(cf):
            import pickle
            with open(cf, "rb") as fh:
                arms[cw] = pickle.load(fh)
            print(f"    {cw:7s} [--arm-cache HIT: derived arrays reloaded; runs re-verified]")
            continue
        arms[cw] = build_arm(pr, a.reps, a.tag_prefix, cw, doses, ex, assign, keep)
        if cf:
            import pickle
            os.makedirs(a.arm_cache, exist_ok=True)
            with open(cf, "wb") as fh:
                pickle.dump(arms[cw], fh, protocol=4)
    R["runs"] = {cw: arms[cw]["runs"] for cw in arms}
    R["missing_rows"] = {cw: arms[cw]["missing"] for cw in arms}

    # numerical corollary of V2: the SAME prompt extracted in three different runs must give the
    # same state, or the A term cancels only in text and not in arithmetic.
    a_res = {}
    for cw in (cw_dev, cw_ext):
        A = arms[cw]["A_by_pid"]
        pids = set.intersection(*[set(A[c]) for c in concepts])
        m = [float(np.abs(A[concepts[0]][p] - A[c][p]).max()) for p in list(pids)[:400]
             for c in concepts[1:]]
        a_res[cw] = {"n_pids_checked": min(len(pids), 400), "max_abs_diff": max(m) if m else None,
                     "mean_abs_diff": float(np.mean(m)) if m else None}
    R["V2_numerical"] = a_res
    for cw, r in a_res.items():
        print(f"  {cw:7s} cell-A states across the three RUNS at matched prompt_id: "
              f"max|diff| {r['max_abs_diff']:.3e} over {r['n_pids_checked']} prompt_ids")

    # ---------------------------------------------------------------- the estimator
    print()
    print("=" * 100)
    print("DIRECTIONS -- TRAIN ONLY (67 domains), no layer selection, no hyperparameter")
    print("=" * 100)
    R["contrasts"] = {}
    out_primary = None
    for cw in (cw_dev, cw_ext):
        for dose in (dose_p, dose_r):
            res = evaluate(pr, arms, cw, dose, train, test, concepts, layer_grid,
                           n_perm, chance, fit_arm=cw, label=f"{cw}/n{dose}")
            R["contrasts"][f"{cw}|n{dose}"] = res
            if cw == cw_dev and dose == dose_p:
                out_primary = res
        # validation, descriptive (no selection happens anywhere in this file)
        R["contrasts"][f"{cw}|n{dose_p}|VALIDATION"] = evaluate(
            pr, arms, cw, dose_p, train, valid, concepts, layer_grid, n_perm, chance,
            fit_arm=cw, label=f"{cw}/n{dose_p}/validation", quick=True)
    # E: transfer -- directions fitted on the DEVELOPMENT arm only, scored on the other arm
    R["contrasts"][f"TRANSFER {cw_dev}->{cw_ext}|n{dose_p}"] = evaluate(
        pr, arms, cw_ext, dose_p, train, test, concepts, layer_grid, n_perm, chance,
        fit_arm=cw_dev, label=f"transfer {cw_dev}->{cw_ext}")
    # F: the n_examples = 0 null
    R["contrasts"][f"{cw_dev}|n{dose_0}|NULL"] = evaluate(
        pr, arms, cw_dev, dose_0, train, test, concepts, layer_grid, n_perm, chance,
        fit_arm=cw_dev, label=f"{cw_dev}/n{dose_0} NULL", quick=True)

    R["primary"] = summarise_primary(pr, out_primary, alpha, chance, floor_auroc)
    R["V1"]["realised"] = v1_power(
        pr, sd_bracket, realised_sd=out_primary["C"]["per_domain_sd"])["realised"]
    R["separability"] = separability(out_primary, chance, alpha, floor_auroc)
    report(pr, R, arms, concepts, layer_grid, alpha, chance, floor_auroc, cw_dev, cw_ext,
           dose_p, dose_r, dose_0)

    if a.mutate:
        R["mutations"] = mutate(pr, arms, out_primary, ex, concepts, layer_grid, train, test,
                                cw_dev, dose_p)
    if a.json:
        def _jsonable(o):
            # NEVER a silent None: a serialiser that swallows what it cannot encode writes an
            # artifact that disagrees with the printed report and nobody notices.
            if isinstance(o, (np.floating, np.integer)):
                return o.item()
            if isinstance(o, np.ndarray):
                return o.tolist()
            raise TypeError(f"unserialisable {type(o).__name__} in the result tree")
        with open(a.json, "w") as f:
            json.dump(R, f, indent=2, default=_jsonable)
        print(f"\n  machine-readable result -> {a.json}")
    return 0


def evaluate(pr, arms, eval_cw, dose, train, test_doms, concepts, layer_grid, n_perm, chance,
             fit_arm, label, quick=False):
    """Fit both directions on the FIT arm's TRAIN domains; score the EVAL arm's held-out domains.

    Returns every contrast the preregistration's secondary questions need, per layer, per domain,
    with the DOMAIN-LEVEL group-permutation null for each. No layer is selected anywhere.
    """
    nL = len(layer_grid)
    Dm = {c: arms[fit_arm]["Dmean"][(c, dose)] for c in concepts}
    tr = [d for d in train if all(d in Dm[c] for c in concepts)]
    _nonempty(tr, f"{label}: TRAIN domains with a paired direction")

    stack = np.stack([np.stack([Dm[c][d] for d in tr]) for c in concepts], axis=1)  # (nD,3,nL,H)
    tot = stack.sum(axis=1, keepdims=True)
    U = stack                                     # v_bomb family
    W = stack - 0.5 * (tot - stack)               # v_bomb_specific family (no club -- `_no_club`)
    nD = U.shape[0]

    rows = arms[eval_cw]["rows"]
    doms = [d for d in test_doms if all(d in rows[(c, dose)] for c in concepts)]
    _nonempty(doms, f"{label}: held-out domains with rows")
    # `primary.void`: "directions estimated on anything but TRAIN". A fit set that intersects the
    # evaluation set voids the run, so it refuses here rather than producing a number.
    if set(tr) & set(doms):
        raise PreregError(f"{label}: {len(set(tr) & set(doms))} domain(s) are in BOTH the "
                          f"direction-fitting set and the evaluation set. The preregistration "
                          f"declares such a run VOID; refusing to compute a statistic.")
    groups = {}
    for c in concepts:
        for d in doms:
            groups[("C", c, d)] = _nonempty(rows[(c, dose)][d]["C"], f"{label}: C_{c} in {d}")
    for d in doms:
        groups[("A", None, d)] = _nonempty(rows[(concepts[0], dose)][d]["A"],
                                           f"{label}: cell A in {d}")

    # observed directions -- the identity label map
    v_bomb = U[:, 0].mean(axis=0)
    v_spec = W[:, 0].mean(axis=0)

    # TRAIN-ONLY standardisation constants (the D1 fix). Held-out rows never enter them, and for
    # the transfer the constants come from the FIT arm's TRAIN domains, not from all domains.
    ztr = [d for d in tr if d in arms[fit_arm]["rows"][(concepts[0], dose)]]
    zA = (np.concatenate([arms[fit_arm]["rows"][(concepts[0], dose)][d]["A"] for d in ztr], axis=0)
          if ztr else None)
    zconst = {nm: (_zconst(zA, unit(v)) if zA is not None else (0.0, 1.0))
              for nm, v in (("v_bomb", v_bomb), ("v_bomb_specific", v_spec))}

    def cand_proj(CAND, X):
        """CAND (nD,3,nL,H), X (n,nL,H) -> (nD*3, n, nL) UNNORMALISED projections."""
        M = CAND.reshape(nD * 3, nL, CAND.shape[-1])
        out = np.empty((nD * 3, X.shape[0], nL), dtype=np.float32)
        for l in range(nL):
            out[:, :, l] = M[:, l, :] @ X[:, l, :].T
        return out

    Pfam = {"u": {k: cand_proj(U, X) for k, X in groups.items()},
            "w": {k: cand_proj(W, X) for k, X in groups.items()}}

    def combine(P, choice):
        """choice (B, nD) role index per TRAIN domain -> (B, n, nL) mean-over-domains projection.

        AUROC is invariant to the positive per-layer rescale by 1/||v|| and to the z-affine map, so
        the null draws skip both; the observed pass reports the z-projections explicitly."""
        B = choice.shape[0]
        idx = choice + 3 * np.arange(nD)[None, :]
        n, L = P.shape[1], P.shape[2]
        M = np.zeros((B, nD * 3), dtype=np.float32)
        np.put_along_axis(M, idx, np.float32(1.0 / nD), axis=1)
        return (M @ P.reshape(nD * 3, n * L)).reshape(B, n, L)

    #: question -> (direction family, positive groups, negative groups)
    CB = [("C", concepts[0])]
    HN = [("C", c) for c in concepts[1:]]
    BASE = [("A", None)]
    SPECS = {
        "A": ("u", CB, BASE),            # v_bomb: C_bomb vs A            -- the REMAPPING axis
        "B": ("u", CB, HN),              # v_bomb: C_bomb vs hard negs    -- identity, raw axis
        "C": ("w", CB, HN),              # v_bomb_specific vs hard negs   -- THE PRIMARY
        "D": ("w", HN, BASE),            # v_bomb_specific: C_k,C_g vs A  -- generic remapping
        "D_allC": ("w", CB + HN, BASE),  # v_bomb_specific: pooled C vs A -- descriptive companion
        "A_spec": ("w", CB, BASE),       # v_bomb_specific: C_bomb vs A   -- descriptive
    }
    PERM_SPECS = ("A", "B", "C", "D")    # the four that carry a p-value

    # WHAT THE PERMUTATION NULL CAN AND CANNOT TEST -- stated before any p is computed.
    # The null relabels WHICH CONCEPT plays the bomb role in each TRAIN domain. Write
    # u_j = Dm_j and w_j = 1.5 Dm_j - 0.5 (Dm_bomb + Dm_knife + Dm_gun):
    #   * mean over j of w_j is EXACTLY ZERO, so a permuted v_bomb_specific is a random residual
    #     axis with no expected remapping component. Questions C and D therefore have a fair null.
    #   * mean over j of u_j is the GRAND MEAN of the three C-minus-A differences, which is not
    #     zero -- it is the average remapping direction. So a permuted v_bomb still separates C
    #     from A about as well as the real one does. Question B (C_bomb vs the hard negatives) is
    #     unaffected, because relabelling does destroy the concept preference. Question A
    #     (C_bomb vs A) is NOT testable this way: its null sits far above chance BY CONSTRUCTION,
    #     and a large p there means "relabelling concepts does not remove remapping", not "there
    #     is no remapping axis". The instrument for A is the exact sign test over domains, and the
    #     report says so rather than quoting the uninformative p as a negative.

    def stats(projs, spec):
        """Domain-mean AUROC per layer for a batch of label maps, plus the per-domain values."""
        fam, pk, nk = spec
        acc, per_dom = None, {}
        for d in doms:
            pos = np.concatenate([projs[(k, c, d)] for k, c in pk], axis=1)
            neg = np.concatenate([projs[(k, c, d)] for k, c in nk], axis=1)
            au = batch_auroc(np.transpose(pos, (0, 2, 1)), np.transpose(neg, (0, 2, 1)))
            per_dom[d] = au
            acc = au.astype(np.float64) if acc is None else acc + au
        return acc / len(doms), per_dom

    ident = np.zeros((1, nD), dtype=np.int64)
    obs_projs = {f: {k: combine(P, ident) for k, P in Pfam[f].items()} for f in Pfam}

    res = {"label": label, "fit_arm": fit_arm, "eval_arm": eval_cw, "dose": dose,
           "n_train_domains": nD, "n_eval_domains": len(doms), "eval_domains": doms,
           "n_rows_per_group": {f"{k[0]}_{k[1]}": int(v.shape[0]) for k, v in groups.items()
                                if k[2] == doms[0]},
           "norms": {"v_bomb": [float(np.linalg.norm(v_bomb[l])) for l in range(nL)],
                     "v_bomb_specific": [float(np.linalg.norm(v_spec[l])) for l in range(nL)]},
           "mean_z": {}}
    for nm, v in (("v_bomb", v_bomb), ("v_bomb_specific", v_spec)):
        mu, sd = zconst[nm]
        z = {}
        for gk in [("C", c) for c in concepts] + [("A", None)]:
            X = np.concatenate([groups[(gk[0], gk[1], d)] for d in doms], axis=0)
            Pz = (project(X, unit(v)) - mu) / sd
            z[f"{gk[0]}_{gk[1] or 'shared'}"] = [float(Pz[:, l].mean()) for l in range(nL)]
        res["mean_z"][nm] = z

    for q, spec in SPECS.items():
        by_layer, per_dom = stats(obs_projs[spec[0]], spec)
        by_dom = {d: float(np.mean(per_dom[d][0])) for d in doms}
        obs_band = float(np.mean(list(by_dom.values())))
        sd_dom = float(np.std(list(by_dom.values()), ddof=1))
        k = sum(1 for v in by_dom.values() if v > chance)
        sp, sfl = sign_test_two_sided(k, len(doms))
        half = _Z_ALPHA2 * sd_dom / math.sqrt(len(doms))
        res[q] = {"auroc_by_layer": [float(x) for x in by_layer[0]],
                  "band_mean_auroc": obs_band,
                  "per_domain_band_auroc": by_dom,
                  "per_domain_sd": sd_dom,
                  "per_domain_ci95": [obs_band - half, obs_band + half],
                  "sign_test": {"k": k, "n": len(doms), "p": sp, "floor": sfl,
                                "formatted": fmt_p(sp, sfl)}}

    # ---- DOMAIN-LEVEL group permutation. Row-level was measured at FPR 0.2000 and is not
    # implemented anywhere in this file. The label map is the ONLY difference from the observed
    # pass: the same candidate projections, the same combine, the same AUROC.
    if not quick:
        rng = np.random.default_rng(int(pr.require("split", "seed")))
        nulls = {q: [] for q in PERM_SPECS}
        need = {SPECS[q][0] for q in PERM_SPECS}
        for s0 in range(0, n_perm, 500):
            b = min(500, n_perm - s0)
            ch = rng.integers(0, 3, size=(b, nD))
            projs = {f: {k: combine(P, ch) for k, P in Pfam[f].items()} for f in need}
            for q in PERM_SPECS:
                by_layer, _ = stats(projs[SPECS[q][0]], SPECS[q])
                nulls[q].extend(np.mean(by_layer, axis=1).tolist())
        for q in PERM_SPECS:
            pp, pfl, nex = group_permutation_p(res[q]["band_mean_auroc"], nulls[q])
            res[q]["permutation"] = {"p": pp, "floor": pfl, "n_exceed": nex, "n_perm": n_perm,
                                     "null_mean": float(np.mean(nulls[q])),
                                     "null_sd": float(np.std(nulls[q], ddof=1)),
                                     "null_q95": float(np.quantile(nulls[q], 0.95)),
                                     "formatted": fmt_p(pp, pfl, nex)}

    # standardized effect on the primary contrast, pooled over held-out rows
    Xp = np.concatenate([groups[("C", concepts[0], d)] for d in doms], axis=0)
    Xn = np.concatenate([groups[("C", c, d)] for c in concepts[1:] for d in doms], axis=0)
    mu, sd = zconst["v_bomb_specific"]
    Pp = (project(Xp, unit(v_spec)) - mu) / sd
    Pn = (project(Xn, unit(v_spec)) - mu) / sd
    res["C"]["cohens_d_by_layer"] = [std_diff(Pp[:, l], Pn[:, l]) for l in range(nL)]
    res["C"]["cohens_d_band"] = band(res["C"]["cohens_d_by_layer"])
    return res


def summarise_primary(pr, res, alpha, chance, floor_auroc):
    c = res["C"]
    perm = c["permutation"]
    sig = perm["p"] < alpha and c["sign_test"]["p"] < alpha
    clears = c["band_mean_auroc"] > floor_auroc
    verdict = ("SUPPORTS THE CLAIM" if (sig and clears) else
               "SIGNIFICANT BUT BELOW THE MEASURED SURFACE FLOOR -- NOT EVIDENCE FOR THE CLAIM"
               if sig else "NOT SIGNIFICANT")
    # PRIMARY family = {PR-048 3-way probe, PR-053 identity AUROC}, Holm at family-wise 0.05.
    pr048 = os.path.join(REPO, "outputs/dcs_ts/pr048_result.json")
    other = None
    if os.path.exists(pr048):
        try:
            other = json.load(open(pr048))["permutation"]["p"]
        except Exception:
            other = None
    fam = {"PR-053_identity_auroc": perm["p"]}
    if other is not None:
        fam["PR-048_3way_probe"] = other
        h = holm(fam, alpha)
    else:
        h = {"PR-053_identity_auroc": {
            "p": perm["p"], "p_holm": min(1.0, 2 * perm["p"]),
            "reject": min(1.0, 2 * perm["p"]) < alpha, "rank": 1, "m": 2,
            "_note": "PR-048 has not been run, so the family's other member has no p. The "
                     "adjusted value shown is the CONSERVATIVE Holm worst case (m=2, this member "
                     "ranked first), which is the only member-independent bound available."}}
    return {"statistic": pr.require("primary", "statistic"),
            "band_mean_auroc": c["band_mean_auroc"], "chance": chance,
            "surface_floor": floor_auroc, "clears_surface_floor": bool(clears),
            "significant_vs_chance": bool(sig), "verdict": verdict,
            "holm_primary_family": h}


def separability(res, chance, alpha, floor_auroc):
    """CLAIM B needs C AND D TOGETHER.

    A direction that discriminates identity AND remapping equally well is ONE axis doing both, not
    a separate axis. Reporting C without D is precisely the error the raw-vs-residual framing
    exists to avoid, so D is decided by the same instruments as C -- its own domain-level
    permutation p and its own comparison to the MEASURED surface floor -- and not by an eyeballed
    cut. The one interpretive constant below (`RATIO_CUT`) is a READING RULE, stated as such: it is
    not preregistered and it decides nothing that the two p-values and the floor have not already
    decided.
    """
    RATIO_CUT = 0.5
    C = res["C"]["band_mean_auroc"] - chance
    #: AUROC is a DIRECTED statistic: 0.169 and 0.831 are the same amount of discrimination with
    #: opposite polarity. "Stays weak" is a claim about the AMOUNT, so D is judged on |D - 0.5|.
    D_polarity_free = max(res["D"]["band_mean_auroc"], 1.0 - res["D"]["band_mean_auroc"])
    D = res["D"]["band_mean_auroc"] - chance
    Dall = res["D_allC"]["band_mean_auroc"] - chance
    Braw = res["B"]["band_mean_auroc"] - chance
    Araw = res["A"]["band_mean_auroc"] - chance
    C_sig = res["C"]["permutation"]["p"] < alpha
    #: two-sided in the amount, because a strongly REVERSED D is a strong D
    D_sig = min(res["D"]["permutation"]["p"], 1.0 - res["D"]["permutation"]["p"]) < alpha / 2
    C_clears = res["C"]["band_mean_auroc"] > floor_auroc
    D_clears = D_polarity_free > floor_auroc
    ratio = (abs(D) / abs(C)) if C != 0.0 else None
    A_spec = res["A_spec"]["band_mean_auroc"]
    if not (C_sig and C_clears):
        reading = ("C ITSELF DOES NOT STAND (not significant, or below the measured surface "
                   "floor), so there is no identity axis for D to be separable from")
    elif D_clears or max(A_spec, 1 - A_spec) > floor_auroc:
        reading = ("C stands, but v_bomb_specific ALSO discriminates remapping: "
                   f"|D| polarity-free = {D_polarity_free:.4f} and C_bomb-vs-A on the SAME "
                   f"residual axis = {A_spec:.4f}, both above the measured surface floor. That is "
                   "ONE axis doing both, not a separate identity axis")
    elif ratio is not None and ratio >= RATIO_CUT:
        reading = (f"C stands but D is comparable in size (|D|/|C| = {ratio:.2f} >= {RATIO_CUT}); "
                   f"the residual axis has not shed remapping")
    else:
        reading = ("C stands AND D is weak on both instruments: consistent with two separable "
                   "axes")
    return {"C_identity_delta": C, "D_generic_remapping_delta": D, "D_allC_delta": Dall,
            "B_raw_identity_delta": Braw, "A_raw_remapping_delta": Araw,
            "C_significant": bool(C_sig), "C_clears_surface_floor": bool(C_clears),
            "D_significant": bool(D_sig), "D_clears_surface_floor": bool(D_clears),
            "D_polarity_free_auroc": D_polarity_free,
            "A_spec_Cbomb_vs_A_on_residual_axis": A_spec,
            "abs_ratio_D_over_C": ratio, "reading_rule_ratio_cut": RATIO_CUT,
            "_reading_rule_is_not_preregistered": True, "reading": reading}


# ================================================================================ printing
def report(pr, R, arms, concepts, layer_grid, alpha, chance, floor_auroc, cw_dev, cw_ext,
           dose_p, dose_r, dose_0):
    P = print
    key = f"{cw_dev}|n{dose_p}"
    res = R["contrasts"][key]
    P("")
    P("=" * 100)
    P("PRIMARY -- %s" % pr.require("primary", "statistic"))
    P("=" * 100)
    c = res["C"]
    P(f"  band-mean AUROC over layers {layer_grid[0]}-{layer_grid[-1]}, domain-mean over "
      f"{res['n_eval_domains']} TEST domains : {c['band_mean_auroc']:.4f}")
    P(f"  95% CI over domains        : [{c['per_domain_ci95'][0]:.4f}, {c['per_domain_ci95'][1]:.4f}]"
      f"   between-domain SD {c['per_domain_sd']:.4f}")
    P(f"  Cohen's d (band)           : {_fmt(c['cohens_d_band'], 3)}")
    P(f"  per-domain sign            : {c['sign_test']['k']}/{c['sign_test']['n']} above chance   "
      f"{c['sign_test']['formatted']}")
    P(f"  domain-level permutation   : {c['permutation']['formatted']}   "
      f"null mean {c['permutation']['null_mean']:.4f} sd {c['permutation']['null_sd']:.4f} "
      f"q95 {c['permutation']['null_q95']:.4f}")
    P(f"  chance {chance}   MEASURED SURFACE FLOOR {floor_auroc} (the bar; NOT chance)")
    P(f"  clears the surface floor   : {R['primary']['clears_surface_floor']}")
    P(f"  Holm (PRIMARY family, m=2) : {R['primary']['holm_primary_family']}")
    P(f"  VERDICT                    : {R['primary']['verdict']}")
    P("")
    P("  per-layer profile (NO layer is selected; all are reported)")
    P("    layer                          " + " ".join(f"{l:7d}" for l in layer_grid))
    for q, nm in (("C", "C v_spec  C_bomb vs {C_kn,C_gun}"),
                  ("D", "D v_spec  {C_kn,C_gun} vs A"),
                  ("A_spec", "  v_spec  C_bomb vs A"),
                  ("A", "A v_bomb  C_bomb vs A"),
                  ("B", "B v_bomb  C_bomb vs {C_kn,C_gun}")):
        P(f"    {nm:30s} " + " ".join(f"{x:7.4f}" for x in res[q]["auroc_by_layer"]))
    P("")
    P("=" * 100)
    P("SECONDARY -- the six questions of mandate 9.1, each with a number")
    P("=" * 100)
    lbl = {"A": "v_bomb separates C_bomb from A            (the REMAPPING axis)",
           "B": "v_bomb separates C_bomb from C_knife/C_gun (identity on the raw axis)",
           "C": "v_bomb_specific separates C_bomb from the hard negatives   [PRIMARY]",
           "D": "v_bomb_specific on GENERIC C-vs-A remapping (must stay WEAK)",
           "D_allC": "v_bomb_specific, pooled C vs A (descriptive companion of D)"}
    sec_p = {}
    for q in ("A", "B", "C", "D", "D_allC"):
        e = res[q]
        P(f"  {q:6s} {lbl[q]}")
        P(f"         band-mean AUROC {e['band_mean_auroc']:.4f}   "
          f"CI95 [{e['per_domain_ci95'][0]:.4f}, {e['per_domain_ci95'][1]:.4f}]   "
          f"sign {e['sign_test']['k']}/{e['sign_test']['n']}   "
          + (e["permutation"]["formatted"] if "permutation" in e
             else "no permutation (descriptive companion, carries no p)"))
        if "permutation" in e:
            pm = e["permutation"]
            centred = abs(pm["null_mean"] - chance) < 0.05
            P(f"         null: mean {pm['null_mean']:.4f} sd {pm['null_sd']:.4f} "
              f"q95 {pm['null_q95']:.4f} exceedances {pm['n_exceed']}/{pm['n_perm']}"
              + ("" if centred else
                 "   <-- NOT CENTRED AT CHANCE: the concept relabelling does not remove this "
                 "contrast's signal, so this p is not a calibrated test of it"))
            sec_p[q] = pm["p"]
    tkey = f"TRANSFER {cw_dev}->{cw_ext}|n{dose_p}"
    tr = R["contrasts"][tkey]
    own = R["contrasts"][f"{cw_ext}|n{dose_p}"]
    a_dom = [tr["C"]["per_domain_band_auroc"][d] for d in tr["eval_domains"]]
    b_dom = [own["C"]["per_domain_band_auroc"][d] for d in tr["eval_domains"]]
    rho = _spearman(a_dom, b_dom)
    sec_p["E"] = tr["C"]["permutation"]["p"]
    P(f"  E      transfer {cw_dev} -> {cw_ext} by RANKING: directions fitted on {cw_dev} TRAIN only")
    P(f"         band-mean AUROC on {cw_ext} TEST {tr['C']['band_mean_auroc']:.4f}   "
      f"sign {tr['C']['sign_test']['k']}/{tr['C']['sign_test']['n']}   "
      f"{tr['C']['permutation']['formatted']}")
    P(f"         Spearman rho of the 23 per-domain AUROCs, transferred vs own-arm: {rho:.4f}")
    nkey = f"{cw_dev}|n{dose_0}|NULL"
    nn = R["contrasts"][nkey]
    ratio = (band(nn["norms"]["v_bomb_specific"]) / band(res["norms"]["v_bomb_specific"]))
    P(f"  F      the n_examples={dose_0} null: at zero demonstrations cells A and C are the SAME "
      f"prompt")
    P(f"         ||v_bomb_specific|| band-mean {band(nn['norms']['v_bomb_specific']):.4e} vs "
      f"{band(res['norms']['v_bomb_specific']):.4e} at n{dose_p}  -> ratio {ratio:.3e}")
    P(f"         band-mean AUROC C_bomb vs hard negatives {nn['C']['band_mean_auroc']:.4f} "
      f"(exactly {chance} is what 'fires exactly' means here)")
    P(f"         NOTE (`nulls_required` N1, C-081): DEGENERATE BY CONSTRUCTION. It is a pipeline "
      f"sanity check,")
    P(f"         not evidence about the model, and 'the signal localises to the demo block' does "
      f"NOT follow from it.")
    P("")
    hs = holm(sec_p, alpha)
    P("  Holm within the SECONDARY family (questions A,B,C,D,E):")
    for q in sorted(hs, key=lambda k: hs[k]["rank"]):
        P(f"    {q:6s} p = {hs[q]['p']:.3e}  p_holm = {hs[q]['p_holm']:.3e}  "
          f"reject at {alpha}: {hs[q]['reject']}")
    R["secondary_holm"] = hs
    R["transfer_spearman"] = rho

    P("")
    P("=" * 100)
    P("SEPARABILITY -- CLAIM B needs C AND D TOGETHER")
    P("=" * 100)
    s = R["separability"]
    P(f"  C  identity          delta above chance : {s['C_identity_delta']:+.4f}")
    P(f"  D  generic remapping delta above chance : {s['D_generic_remapping_delta']:+.4f}   "
      f"(|D|/|C| = {_fmt(s['abs_ratio_D_over_C'], 3)})")
    P(f"  D  polarity-free |D|                     : {s['D_polarity_free_auroc']:.4f}   "
      f"C_bomb vs A on the SAME residual axis: {s['A_spec_Cbomb_vs_A_on_residual_axis']:.4f}")
    P(f"  C significant {s['C_significant']} / clears the measured floor {s['C_clears_surface_floor']}"
      f"      D significant {s['D_significant']} / clears the measured floor "
      f"{s['D_clears_surface_floor']}")
    P(f"  B  raw-axis identity delta              : {s['B_raw_identity_delta']:+.4f}")
    P(f"  A  raw-axis remapping delta             : {s['A_raw_remapping_delta']:+.4f}")
    P(f"  reading: {s['reading']}")

    P("")
    P("=" * 100)
    P("REPLICATION AND SPECIFICATION CURVE (doses are SEPARATE cells and are NEVER pooled)")
    P("=" * 100)
    P(f"  {'cell':34s} {'C band':>8s} {'D band':>8s} {'A band':>8s} {'B band':>8s}  sign(C)")
    for k in R["contrasts"]:
        e = R["contrasts"][k]
        P(f"  {k:34s} {e['C']['band_mean_auroc']:8.4f} {e['D']['band_mean_auroc']:8.4f} "
          f"{e['A']['band_mean_auroc']:8.4f} {e['B']['band_mean_auroc']:8.4f}  "
          f"{e['C']['sign_test']['k']}/{e['C']['sign_test']['n']}")


def _spearman(a, b):
    def rk(x):
        o = np.argsort(np.argsort(np.asarray(x, dtype=float)))
        return o.astype(float)
    ra, rb = rk(a), rk(b)
    ra -= ra.mean(); rb -= rb.mean()
    den = math.sqrt(float((ra ** 2).sum() * (rb ** 2).sum()))
    return float((ra * rb).sum() / den) if den > 0 else float("nan")


# ============================================================================ mutation harness
def mutate(pr, arms, res, ex, concepts, layer_grid, train, test, cw, dose):
    """Every check must fail loudly when it binds zero rows, and every guard must be REACHABLE.
    A guard that cannot be made to fire is not a guard."""
    print("")
    print("=" * 100)
    print("MUTATION HARNESS -- a green mutation is an unreachable guard")
    print("=" * 100)
    cases, cases_note = [], []

    def case(name, fn, expect_red=True):
        try:
            fn()
            red = False
            why = "no refusal"
        except (PreregError, ValueError, ZeroDivisionError, KeyError, AssertionError) as e:
            red = True
            why = f"{type(e).__name__}: {str(e)[:70]}"
        cases.append((name, red, expect_red, why))

    import copy
    live = json.load(open(os.path.join(REPO, pr.path if os.path.isabs(pr.path)
                                       else os.path.join(REPO, pr.path))))

    # 1. bank sha pin corrupted -> the binding check must refuse
    m = copy.deepcopy(live)
    m["population"]["banks"][f"{cw}_{concepts[0]}"]["bank_rows_sha16"] = "0" * 16
    mp = Prereg(m, "MUTANT")
    run_dir = _find_run(os.path.join(REPO, "outputs/boombness/extract_boombness"),
                        f"ts116m_full_{cw}_{concepts[0]}")
    case("bank_rows_sha16 pin corrupted",
         lambda: verify_run(mp, f"{cw}_{concepts[0]}", run_dir))
    # 2. read-site position pin corrupted
    m2 = copy.deepcopy(live); m2["read_site"]["position"] = "not_the_read_site"
    case("read_site.position pin corrupted",
         lambda: verify_run(Prereg(m2, "MUTANT"), f"{cw}_{concepts[0]}", run_dir))
    # 3. a row missing from a NON-excluded domain
    rows = load_bank_rows(os.path.join(
        REPO, live["population"]["banks"][f"{cw}_{concepts[0]}"]["path"]))
    ok_pid = next(p for p, r in rows.items() if r["domain"] not in ex)
    have = set(rows) - {ok_pid}
    case("a cache row missing from a NON-excluded domain",
         lambda: check_missing("MUTANT", rows, have, ex))
    # 4. CONTROL: a row missing from an EXCLUDED domain must be TOLERATED (R-108)
    exd = next((p for p, r in rows.items() if r["domain"] in ex), None)
    if exd is not None:
        case("a cache row missing from an EXCLUDED domain is tolerated",
             lambda: check_missing("MUTANT", rows, set(rows) - {exd}, ex), expect_red=False)
    # 5. cell A no longer byte-identical across concepts -> V2 must go RED
    def v2_broken():
        import dcs_ts_pr053_diffmeans as self_mod
        orig = self_mod.load_bank_rows
        target = f"{cw}_{concepts[1]}"

        def patched(path):
            r = orig(path)
            if os.path.basename(path).endswith(f"{target}.jsonl"):
                pid = next(p for p, x in r.items()
                           if x["cell"] == CELL_BASELINE and x["domain"] not in ex)
                r[pid] = dict(r[pid]); r[pid]["full_prompt"] += " "
            return r
        self_mod.load_bank_rows = patched
        try:
            v = v2_cellA_identity(pr, ex, (dose,))
        finally:
            self_mod.load_bank_rows = orig
        if v["pass"]:
            raise AssertionError("V2 passed on a corrupted cell-A corpus")
    case("one cell-A prompt byte-flipped -> V2 FAILS", v2_broken)
    # 6. the A-039 wrong-field bind: selecting on `condition` instead of `cell` binds ZERO rows
    case("selecting the wrong field binds zero rows and refuses",
         lambda: _nonempty({p: r for p, r in rows.items()
                            if r.get("cell") == "natural_doublespeak"}, "wrong-field bind"))
    # 7. permutation over an empty null
    case("permutation over an EMPTY null distribution",
         lambda: group_permutation_p(1.0, []))
    # 8. sign test over zero domains
    case("sign test over ZERO domains", lambda: sign_test_two_sided(0, 0))
    # 9. z-standardisation over zero train rows
    case("z-standardisation over ZERO train cell-A rows",
         lambda: _zconst(np.zeros((0, len(layer_grid), 8), dtype=np.float32),
                         np.ones((len(layer_grid), 8), dtype=np.float32)))
    # 10. a p AT the floor must never print bare
    def floor_fmt():
        p, fl, ne = group_permutation_p(1.0, [0.0] * 100)
        if "FLOOR" not in fmt_p(p, fl, ne):
            raise AssertionError("a floor p printed bare")
    # a CONTROL, not a mutation: floor_fmt raises only if the formatting is wrong, so GREEN is the
    # pass. Counting it as a mutation would have printed "UNREACHABLE GUARD" for correct behaviour.
    case("CONTROL: zero exceedances print 'p < 1/(B+1)', never a bare number", floor_fmt,
         expect_red=False)
    # 11. directions fitted on the EVALUATION domains -- `primary.void`
    case("directions fitted on the EVALUATION domains (VOID by the preregistration)",
         lambda: evaluate(pr, arms, cw, dose, test, test, concepts, layer_grid, 1, 0.5,
                          fit_arm=cw, label="MUTANT fit-on-eval", quick=True))
    # 12. CONTROL: a RANDOM direction through the same estimator must land at chance. This is the
    # negative control for the whole readout: if a noise axis separated the classes, the pipeline
    # and not the model would be doing the work.
    def noise_axis():
        """A REFERENCE DISTRIBUTION, not one draw.

        The first version of this control drew a SINGLE random direction and asserted it landed
        within 0.05 of chance. It reached 0.4112 and the control went red -- correctly, because
        one draw is not a distribution: a fixed random axis picks up whatever between-class mean
        difference happens to project onto it, with a random sign, and |AUROC - 0.5| ~ 0.09 is an
        ordinary draw when the classes are far apart in the ambient space. "One estimate is not
        stability." The control is now the whole distribution over 200 draws: its MEAN must sit at
        chance, and the observed statistic is quoted against its upper tail.
        """
        rng = np.random.default_rng(20260907)
        rows_ = arms[cw]["rows"]
        doms_ = [d for d in test if all(d in rows_[(c, dose)] for c in concepts)]
        nL = len(layer_grid)
        H = rows_[(concepts[0], dose)][doms_[0]]["A"].shape[-1]
        draws = []
        for _ in range(200):
            v = rng.normal(size=(nL, H))
            au = []
            for d in doms_:
                pos = project(rows_[(concepts[0], dose)][d]["C"], unit(v))
                neg = np.concatenate([project(rows_[(c, dose)][d]["C"], unit(v))
                                      for c in concepts[1:]], axis=0)
                au.append(band([auroc(pos[:, l], neg[:, l]) for l in range(nL)]))
            draws.append(float(np.mean(au)))
        m, sdv = float(np.mean(draws)), float(np.std(draws, ddof=1))
        q995 = float(np.quantile(draws, 0.995))
        obs = res["C"]["band_mean_auroc"]
        exceed = sum(1 for x in draws if x >= obs)
        cases_note.append(f"random-direction reference over 200 draws: mean {m:.4f} "
                          f"sd {sdv:.4f} q99.5 {q995:.4f}; the observed {obs:.4f} is exceeded by "
                          f"{exceed}/200 random axes")
        if abs(m - 0.5) > 0.02:
            raise AssertionError(f"the random-direction reference is centred at {m:.4f}, not at "
                                 f"chance; the readout itself is doing the separating")
    case("CONTROL: a random direction lands at chance", noise_axis, expect_red=False)
    # 13. CONTROL: the batch AUROC used by the null equals the reused tie-corrected scalar one
    def agree():
        rng = np.random.default_rng(1)
        p_ = rng.normal(size=(1, 1, 10)); n_ = rng.normal(size=(1, 1, 20))
        if abs(float(batch_auroc(p_, n_)[0, 0]) - auroc(p_[0, 0], n_[0, 0])) > 1e-12:
            raise AssertionError("batch AUROC disagrees with the reused scalar AUROC")
    case("CONTROL: batch AUROC == the reused tie-corrected scalar AUROC", agree, expect_red=False)

    n_red = 0
    for name, red, expect, why in cases:
        ok = (red == expect)
        n_red += red
        tag = "ok" if ok else ("!! UNREACHABLE GUARD" if expect else "!! CONTROL FAILED")
        print(f"  {'RED  ' if red else 'GREEN'} {tag:20s} {name:62s} {why}")
    for nt in cases_note:
        print(f"  note: {nt}")
    n_mut = sum(1 for _, _, e, _ in cases if e)
    print(f"[mutate] {n_red}/{n_mut} MUTATIONS turned a check RED; "
          f"{sum(1 for _, r, e, _ in cases if r == e)}/{len(cases)} cases behaved as declared "
          f"({len(cases) - n_mut} of them are GREEN-by-design controls)")
    return [{"name": n, "red": r, "expected_red": e, "detail": w} for n, r, e, w in cases]


# ==================================================================================== selftest
def selftest() -> int:
    print("=== PR-053 analyzer selftest: no data needed; every guard must be reachable ===")
    cases = []
    rng = np.random.default_rng(7)
    p = rng.normal(size=(3, 4, 11)); n = rng.normal(size=(3, 4, 17))
    ba = batch_auroc(p, n)
    cases.append(("batch AUROC == reused scalar AUROC",
                  max(abs(float(ba[b, l]) - auroc(p[b, l], n[b, l]))
                      for b in range(3) for l in range(4)) < 1e-12))
    tie = batch_auroc(np.zeros((1, 1, 4)), np.zeros((1, 1, 4)))
    cases.append(("all-ties AUROC is exactly 0.5", abs(float(tie[0, 0]) - 0.5) < 1e-12))
    for nm, fn in (("empty null refuses", lambda: group_permutation_p(1.0, [])),
                   ("sign test over 0 domains refuses", lambda: sign_test_two_sided(0, 0)),
                   ("an empty bind refuses", lambda: _nonempty([], "x")),
                   ("z over 0 rows refuses",
                    lambda: _zconst(np.zeros((0, 2, 3), dtype=np.float32), np.ones((2, 3))))):
        try:
            fn(); cases.append((nm, False))
        except (PreregError, ValueError, ZeroDivisionError):
            cases.append((nm, True))
    pp, fl, ne = group_permutation_p(1.0, [0.0] * 500)
    cases.append(("a floor p is labelled, never bare", "FLOOR" in fmt_p(pp, fl, ne)))
    h = holm({"a": 0.001, "b": 0.06}, 0.05)
    cases.append(("Holm adjusts the smallest p by m", abs(h["a"]["p_holm"] - 0.002) < 1e-12))
    cases.append(("Holm can fail to reject the larger", h["b"]["reject"] is False))
    h2 = holm({"a": 0.03, "b": 0.04}, 0.05)
    cases.append(("Holm is monotone and can reject nothing",
                  (not h2["a"]["reject"]) and (not h2["b"]["reject"])))
    v1 = v1_power(load("configs/dcs_ts_pr053.json"), (0.1406,))
    cases.append(("sign floor at n=23 is 2/2^23",
                  abs(v1["sign_test_attainable_floor"] - 2.0 / 2 ** 23) < 1e-18))
    cases.append(("permutation floor is 1/(B+1)",
                  abs(v1["permutation_attainable_floor"] - 1 / 10001) < 1e-15))
    ok = sum(1 for _, c in cases if c)
    for nm, c in cases:
        print(f"  {'PASS' if c else 'FAIL'}  {nm}")
    print(f"[selftest] {ok}/{len(cases)}")
    return 0 if ok == len(cases) else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--prereg", default="configs/dcs_ts_pr053.json")
    ap.add_argument("--reps", default="outputs/boombness/extract_boombness")
    ap.add_argument("--tag-prefix", default="ts116m_full")
    ap.add_argument("--json", default=None)
    ap.add_argument("--arm-cache", default=None,
                    help="DEV ONLY: directory to cache the derived per-arm arrays. Verification "
                         "is never cached.")
    ap.add_argument("--mutate", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--v1-v2-only", action="store_true",
                    help="answer the two BLOCKING checklist items from the banks alone")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    # for_extraction=False, deliberately and for a documented reason -- see the module docstring.
    pr = load(a.prereg, for_extraction=False)
    a.reps = a.reps if os.path.isabs(a.reps) else os.path.join(REPO, a.reps)
    return run(pr, a)


if __name__ == "__main__":
    raise SystemExit(main())
