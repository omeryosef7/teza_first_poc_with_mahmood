"""dcs_rowwise.py -- DCS phase, P2/P3: PER-ROW candidate projections, the occurrence trajectory,
and the mandatory `n_examples` x `query_kind` stratification.

WHY THIS EXISTS
---------------
`dcs_cell_geometry.py` (DCS-003, DCS-R-001/R-002) measures the 2x2 geometry of the *cell means*.
Cell means are pre-aggregated: no per-family spread, no CI, no way to condition on `n_examples`,
no way to look at anything other than the final query occurrence, and therefore no way to touch
`R5`. Its own limits section says exactly that. This module is the per-row counterpart.

THE ALGEBRAIC FACT IT RESTS ON (verified numerically before this file was written; RE-ASSERTED at
runtime by `check_algebra`, which makes the process exit non-zero on failure)
---------------------------------------------------------------------------------------------
`estimate_directions` (`signals.py:334-336`) ships UNIT vectors and puts the magnitude in
`payload['gap'][name][L]`. So the RAW (dose-carrying) direction is

    raw(n, L) = payload[n][L] * payload['gap'][n][L]

and the four preregistered contrasts (plan Sec 1.4) are exact linear combinations of the four
shipped raw directions:

    cand1 (C-A) = raw(d_naive) - raw(d_surface) - 0.5*raw(d_inter)
    cand4 (B-C) = raw(d_surface) + 0.5*raw(d_inter)
    cand3 (E-A) = raw(d_surface) - 0.5*raw(d_inter)
    cand2 (B-E) = 2*raw(d_context) - cand1

`results.jsonl` stores, per row and layer, `'<name>|L<k>|proj'` = the dot product of that row's
hidden state with the shipped UNIT vector. Projection is linear, so

    h . raw(n, L) = proj_col(n, L) * gap(n, L)

and the per-row projection onto every candidate is available WITHOUT a GPU, WITHOUT the model and
WITHOUT re-extracting anything. Every metric here is a linear function of the SAME four stored
columns, which is precisely why they all sit on ONE common population (Sec 1.11 rule 1).

⚠ CROSS-FIT, NOT SELF-FIT. Every row in these runs has `is_self_fit == False`: `split='dev'` rows
are scored against directions fitted on `heldout` and vice versa (`directions_fitted_on`). This
module preserves that pairing, refuses any other, and records `directions_from` beside the numbers.

WHAT IT COMPUTES
----------------
1. per-row projections onto `cand1`..`cand4`, carrying `d_surface`/`d_context`/`d_inter`/`d_naive`
   through as RAW dots (`proj*gap`) so all eight sit in the same dose units;
2. THE OCCURRENCE TRAJECTORY (plan Sec 8): how each metric evolves across demonstration
   occurrences up to the final query occurrence, PAIRED WITHIN `family_id`, cell `C`
   (`natural_doublespeak`) against its matched cell `A` (`benign_literal`), as a
   layer x occurrence_index surface;
3. the MANDATORY stratification (plan Sec 1.7): `cand1` is KNOWN to change sign with `n_examples`
   and to depend on `query_kind`, so the layer x `n_examples` surface is emitted PER `query_kind`
   and never pooled over either axis;
4. common-population discipline: the intersection of rows on which EVERY metric is defined at
   EVERY layer, with `n_common` and the exact domains / families / cells / query_kinds present.

`occurrence_analysis_safe` (`prompt_families.py:130-192`) is FALSE for `semantic_forced_choice` and
`comprehension_mc` -- both name two candidate words in the query, so a per-position analysis there
is reading a different object. Those rows are removed from every per-position analysis and the
count removed is reported, not assumed. An unrecognised `query_kind` is a CRASH (rule 10), never a
silent keep.

READS ONLY `results.jsonl` + `directions_fit_*.pt` + `metadata.json`. No GPU, no model, no bank,
no prompt text: this module never opens a prompt string and has no field to print one from.
"""
from __future__ import annotations

import argparse
import collections
import datetime as _dt
import glob
import hashlib
import json
import os
import subprocess
import sys
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np
import torch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from boombness.rah_preflight_transport import provenance as _base_provenance  # noqa: E402

# --------------------------------------------------------------------------- #
# constants
# --------------------------------------------------------------------------- #
SHIPPED: Tuple[str, ...] = ("d_surface", "d_context", "d_inter", "d_naive")
CORE_CELLS = ("A", "B", "C", "E")

#: plan Sec 1.4, expressed over the four SHIPPED RAW directions. A coefficient table rather than
#: four expressions, so the algebra is data and `check_algebra` can loop over it.
CAND_FROM_SHIPPED: Dict[str, Dict[str, float]] = {
    "cand1_C_minus_A": {"d_naive": 1.0, "d_surface": -1.0, "d_inter": -0.5},
    "cand2_B_minus_E": {"d_context": 2.0, "d_naive": -1.0, "d_surface": 1.0, "d_inter": 0.5},
    "cand3_E_minus_A": {"d_surface": 1.0, "d_inter": -0.5},
    "cand4_B_minus_C": {"d_surface": 1.0, "d_inter": 0.5},
}
#: the same four contrasts over the CELL MEANS. Duplicated here deliberately so this module
#: imports nothing from `dcs_cell_geometry` and the two agree by re-derivation, not shared code
#: (standing rule 8: a verifier must not read the producer's own derived field).
CAND_FROM_CELLS: Dict[str, Dict[str, float]] = {
    "cand1_C_minus_A": {"C": 1.0, "A": -1.0},
    "cand2_B_minus_E": {"B": 1.0, "E": -1.0},
    "cand3_E_minus_A": {"E": 1.0, "A": -1.0},
    "cand4_B_minus_C": {"B": 1.0, "C": -1.0},
}
METRICS: Tuple[str, ...] = tuple(CAND_FROM_SHIPPED) + SHIPPED
MIDX = {m: i for i, m in enumerate(METRICS)}

#: [len(METRICS), 4] over the SHIPPED order. dots = (proj*gap) @ COEF.T
COEF = np.zeros((len(METRICS), len(SHIPPED)), dtype=np.float64)
for _i, _m in enumerate(METRICS):
    if _m in CAND_FROM_SHIPPED:
        for _n, _c in CAND_FROM_SHIPPED[_m].items():
            COEF[_i, SHIPPED.index(_n)] = _c
    else:
        COEF[_i, SHIPPED.index(_m)] = 1.0

OCC_UNSAFE_QUERY_KINDS = ("semantic_forced_choice", "comprehension_mc")
OCC_SAFE_QUERY_KINDS = ("behavioral", "semantic_one_word", "comprehension_usage",
                        "mapping_use_forced_choice")

#: the population `stage_fit` averages into `cell_means` (`extract_boombness.py:403-405`, plus the
#: `codeword_last` branch at `:428` which fits at the LAST occurrence == the query occurrence).
FIT_ROW_FILTER = dict(bank_block="core2x2", query_kind="behavioral")

ALGEBRA_TOL = 1e-4
#: A dot product of two 4096-d float32 vectors carries ~1e-6 relative round-off, and the
#: candidates are DIFFERENCES, so at layers/cells where the true contrast nearly vanishes the naive
#: ratio |emp-direct|/|direct| is dominated by cancellation and not by any error in the algebra.
#: The PRIMARY gate is therefore the error in COSINE UNITS -- |emp-direct| / (||cm||*||vec||) --
#: which is scale-free and immune to cancellation. The naive ratio is ALSO gated, but only over
#: comparisons that are not degenerate (|cos| >= DEGENERATE_COS); the number skipped is reported,
#: never hidden. Both gates are fatal.
DEGENERATE_COS = 1e-2
BOOT_N = 1000
BOOT_SEED = 20260902
#: blocks that contain the matched A/C pair. `core2x2` and `core2x2_slot3` are the canonical 2x2
#: (all four cells); `role_style` and `families` carry A and C only. Default keeps the canonical
#: pair so the population matches the one `cell_means` was fitted on; widen with --blocks.
DEFAULT_BLOCKS = ("core2x2", "core2x2_slot3")


def other(split: str) -> str:
    return {"dev": "heldout", "heldout": "dev"}[split]


# --------------------------------------------------------------------------- #
# provenance
# --------------------------------------------------------------------------- #
def file_sha16(path: str) -> Optional[str]:
    try:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
        return h.hexdigest()[:16]
    except OSError:
        return None


def provenance(started: str) -> dict:
    """Standing rule 13. Reuses `rah_preflight_transport.provenance` (git sha / dirty / slurm /
    host) and adds what that helper does not carry: branch, the real argv, both timestamps, and
    this module's own content hash."""
    p = dict(_base_provenance())
    try:
        p["git_branch"] = subprocess.run(("git", "rev-parse", "--abbrev-ref", "HEAD"),
                                         cwd=os.path.dirname(os.path.abspath(__file__)),
                                         capture_output=True, text=True, timeout=20).stdout.strip()
    except BaseException:                                        # noqa: BLE001
        p["git_branch"] = None
    p["argv"] = list(sys.argv)
    p["started_utc"] = started
    p["finished_utc"] = _dt.datetime.now(_dt.timezone.utc).isoformat()
    p["module"] = os.path.abspath(__file__)
    p["module_sha16"] = file_sha16(os.path.abspath(__file__))
    p["metrics"] = list(METRICS)
    p["cand_from_shipped"] = CAND_FROM_SHIPPED
    p["algebra_tol"] = ALGEBRA_TOL
    return p


# --------------------------------------------------------------------------- #
# payloads and the per-row dot matrix
# --------------------------------------------------------------------------- #
def load_payloads(run: str) -> Dict[str, dict]:
    out = {}
    for p in sorted(glob.glob(os.path.join(run, "directions_fit_*.pt"))):
        split = os.path.basename(p)[len("directions_fit_"):-len(".pt")]
        pl = torch.load(p, map_location="cpu", weights_only=False)
        pl["__path"] = p
        pl["__sha16"] = file_sha16(p)
        out[split] = pl
    return out


def raw_dir(pl: dict, name: str, L: int) -> torch.Tensor:
    """raw(n, L) = shipped UNIT vector * gap. The ONLY place magnitude re-enters."""
    return pl[name][L].to(torch.float64) * float(pl["gap"][name][L])


def cand_vec_from_shipped(pl: dict, cand: str, L: int) -> torch.Tensor:
    out = None
    for n, c in CAND_FROM_SHIPPED[cand].items():
        v = raw_dir(pl, n, L) * c
        out = v if out is None else out + v
    return out


def metric_vec(pl: dict, m: str, L: int) -> torch.Tensor:
    return cand_vec_from_shipped(pl, m, L) if m in CAND_FROM_SHIPPED else raw_dir(pl, m, L)


def cand_vec_from_cells(pl: dict, cand: str, L: int) -> torch.Tensor:
    cm = pl["cell_means"]
    out = None
    for cell, c in CAND_FROM_CELLS[cand].items():
        v = cm[cell][L].to(torch.float64) * c
        out = v if out is None else out + v
    return out


def gap_matrix(pl: dict, layers: Sequence[int]) -> np.ndarray:
    """[n_layers, 4] of ||raw(name, L)||, in SHIPPED order."""
    return np.array([[float(pl["gap"][n][L]) for n in SHIPPED] for L in layers], dtype=np.float64)


def build_dots(rows: List[dict], payloads: Dict[str, dict],
               layers: Sequence[int]) -> Tuple[np.ndarray, np.ndarray, dict]:
    """Returns (dots[N, nL, len(METRICS)], row_ok[N], record).

    `row_ok` is the COMMON POPULATION mask: a row is in only if all four stored `proj` columns are
    present and finite at EVERY layer. Because all eight metrics are linear functions of those same
    four columns, definedness is identical across metrics BY CONSTRUCTION -- asserted below rather
    than assumed.
    """
    N, nL = len(rows), len(layers)
    proj = np.full((N, nL, len(SHIPPED)), np.nan, dtype=np.float64)
    colnames = [[f"{n}|L{L}|proj" for n in SHIPPED] for L in layers]
    bad_pairing = collections.Counter()
    fit_of = np.empty(N, dtype=object)
    for i, r in enumerate(rows):
        g = r.get("directions_fitted_on")
        if g not in payloads or g != other(r.get("split")):
            bad_pairing[f"{r.get('split')}->{g}"] += 1
            fit_of[i] = None
            continue
        fit_of[i] = g
        for j in range(nL):
            cj = colnames[j]
            for k in range(len(SHIPPED)):
                v = r.get(cj[k])
                if v is not None:
                    proj[i, j, k] = v

    gaps = {s: gap_matrix(pl, layers) for s, pl in payloads.items()}
    gapmat = np.full((N, nL, len(SHIPPED)), np.nan, dtype=np.float64)
    for s, gm in gaps.items():
        sel = np.array([fo == s for fo in fit_of])
        if sel.any():
            gapmat[sel] = gm
    raws = proj * gapmat
    dots = raws @ COEF.T

    finite_proj = np.isfinite(raws).all(axis=(1, 2))
    row_ok = finite_proj & np.array([fo is not None for fo in fit_of])
    per_metric_defined = {m: int(np.isfinite(dots[row_ok, :, MIDX[m]]).all(axis=1).sum())
                          for m in METRICS}
    rec = {
        "n_input": N,
        "n_common": int(row_ok.sum()),
        "n_excluded": int((~row_ok).sum()),
        "exclusions": {
            "unexpected_fit_pairing": dict(bad_pairing),
            "missing_or_nonfinite_proj_column": int((~finite_proj).sum()),
        },
        "n_layers_required_defined": nL,
        "n_defined_per_metric": per_metric_defined,
        "definedness_identical_across_metrics": len(set(per_metric_defined.values())) <= 1,
        "note": ("all eight metrics are linear in the same four stored proj columns, so the common "
                 "population is identical for every metric by construction; the per-metric counts "
                 "above are emitted so that claim is checkable rather than asserted"),
    }
    return dots, row_ok, rec


# --------------------------------------------------------------------------- #
# GATE: the algebra, re-asserted at runtime
# --------------------------------------------------------------------------- #
def check_algebra(rows: List[dict], dots: np.ndarray, payloads: Dict[str, dict],
                  layers: Sequence[int]) -> dict:
    """Two independent checks; either one over `ALGEBRA_TOL` is fatal.

    CHECK-1 (vector identity). For every split and layer, the candidate built from the four shipped
    RAW directions must equal the candidate built from `cell_means` -- i.e. `CAND_FROM_SHIPPED`
    really is `C-A`, `B-E`, `E-A`, `B-C`.

    CHECK-2 (per-row mean -> shipped cell mean). The thing this module actually does. For every
    split S, cell X, layer L and metric m, the mean over the fit families of the PER-ROW dot (built
    from the stored `proj` columns of split-S rows, which are projections onto directions fitted on
    `other(S)`) must equal `cell_means_S[X] . metric_vec(payload[other(S)], m, L)` computed
    directly from the two payloads -- i.e. against `dcs_cell_geometry.py`'s object, not against
    this module's own output.
    """
    res = {"tol": ALGEBRA_TOL, "check1_vector_identity": {},
           "check2_row_mean_vs_cell_mean": {}, "worst_rel_err": 0.0, "passed": True,
           "errors": []}
    worst = 0.0
    for split, pl in payloads.items():
        w1 = 0.0
        for L in layers:
            for cand in CAND_FROM_SHIPPED:
                a = cand_vec_from_shipped(pl, cand, L)
                b = cand_vec_from_cells(pl, cand, L)
                w1 = max(w1, float((a - b).norm().item()) / max(float(b.norm().item()), 1e-30))
        res["check1_vector_identity"][split] = {
            "max_rel_err": w1, "n_layers": len(layers), "n_candidates": len(CAND_FROM_SHIPPED)}
        worst = max(worst, w1)

    fit_idx = [i for i, r in enumerate(rows)
               if r.get("bank_block") == FIT_ROW_FILTER["bank_block"]
               and r.get("query_kind") == FIT_ROW_FILTER["query_kind"]
               and int(r.get("n_examples", 0)) > 0
               and r.get("cell") in CORE_CELLS
               and bool(r.get("is_final_occurrence"))]
    for split, pl in payloads.items():
        G = other(split)
        if G not in payloads:
            res["check2_row_mean_vs_cell_mean"][split] = {"skipped": f"no payload for {G}"}
            continue
        fams = set(pl.get("families") or [])
        w2, w2_naive, ncmp, nnd, ndeg, nrows = 0.0, 0.0, 0, 0, 0, {}
        worst_naive, deg_worst = None, {}
        for X in CORE_CELLS:
            sel = [i for i in fit_idx if rows[i]["split"] == split and rows[i]["cell"] == X
                   and rows[i]["family_id"] in fams]
            nrows[X] = len(sel)
            if len(sel) != len(fams):
                res["passed"] = False
                res["errors"].append(f"CHECK-2 population mismatch: split={split} cell={X} "
                                     f"rows={len(sel)} payload_families={len(fams)}")
                continue
            emp_all = dots[sel].mean(axis=0)                      # [nL, M]
            for j, L in enumerate(layers):
                cm = pl["cell_means"][X][L].to(torch.float64)
                ncm = float(cm.norm())
                for m in METRICS:
                    v = metric_vec(payloads[G], m, L)
                    scale = ncm * float(v.norm())
                    direct = float(cm @ v)
                    err = abs(float(emp_all[j, MIDX[m]]) - direct)
                    cos_err = err / max(scale, 1e-30)
                    w2 = max(w2, cos_err)
                    ncmp += 1
                    if abs(direct) >= DEGENERATE_COS * scale:
                        rel = err / max(abs(direct), 1e-30)
                        nnd += 1
                        if rel > w2_naive:
                            w2_naive = rel
                            worst_naive = {"split": split, "cell": X, "layer": int(L),
                                           "metric": m, "abs_err": err, "direct": direct,
                                           "operand_scale": scale, "rel_err": rel}
                    else:
                        ndeg += 1
                        if cos_err > deg_worst.get("cos_err", -1.0):
                            deg_worst = {"split": split, "cell": X, "layer": int(L), "metric": m,
                                         "abs_err": err, "direct": direct,
                                         "operand_scale": scale, "cos_err": cos_err,
                                         "naive_rel_err": err / max(abs(direct), 1e-30)}
        res["check2_row_mean_vs_cell_mean"][split] = {
            "max_cos_scaled_err": w2, "max_naive_rel_err_nondegenerate": w2_naive,
            "worst_nondegenerate": worst_naive,
            "n_comparisons": ncmp, "n_nondegenerate": nnd, "n_degenerate_skipped": ndeg,
            "degenerate_rule": f"|cell_mean . vec| < {DEGENERATE_COS} * ||cell_mean||*||vec||",
            "worst_degenerate_by_cos_err": deg_worst,
            "n_rows_per_cell": nrows, "directions_from": G, "n_fit_families": len(fams)}
        worst = max(worst, w2, w2_naive)
    res["worst_rel_err"] = worst
    if worst > ALGEBRA_TOL:
        res["passed"] = False
        res["errors"].append(f"worst_rel_err {worst:.3e} > tol {ALGEBRA_TOL:.1e}")
    return res


# --------------------------------------------------------------------------- #
# statistics
# --------------------------------------------------------------------------- #
def summarise_vec(a: np.ndarray) -> dict:
    n = int(a.size)
    if n == 0:
        return {"n": 0, "mean": None, "sd": None, "sem": None, "ci95": None}
    mean = float(a.mean())
    sd = float(a.std(ddof=1)) if n > 1 else 0.0
    sem = sd / np.sqrt(n) if n > 1 else 0.0
    return {"n": n, "mean": mean, "sd": sd, "sem": float(sem),
            "ci95": [mean - 1.96 * sem, mean + 1.96 * sem]}


def cluster_bootstrap_ci(mat: np.ndarray, clusters: np.ndarray,
                         seed: int = BOOT_SEED, n_boot: int = BOOT_N):
    """Domain-clustered CI for every column of `mat` at once. Sec 1.9: the independence unit is
    DOMAIN and Wilson-iid understates ~1.9x. Returns None when there are <2 clusters -- a
    one-cluster CI is not a CI."""
    uniq = np.unique(clusters)
    if uniq.size < 2 or mat.shape[0] == 0:
        return None
    idx = [np.flatnonzero(clusters == c) for c in uniq]
    rng = np.random.default_rng(seed)
    boot = np.empty((n_boot, mat.shape[1]))
    for b in range(n_boot):
        take = np.concatenate([idx[p] for p in rng.integers(0, uniq.size, uniq.size)])
        boot[b] = mat[take].mean(axis=0)
    lo = np.percentile(boot, 2.5, axis=0)
    hi = np.percentile(boot, 97.5, axis=0)
    return [[float(lo[i]), float(hi[i])] for i in range(mat.shape[1])]


def monotone_report(xs: Sequence[int], ys: Sequence[float]) -> dict:
    """"does cand1 grow monotonically across demonstration occurrences" -- answered with a STEP
    LEDGER, not only a correlation: one large jump plus flat noise gives a high rho and is not
    monotone growth."""
    order = np.argsort(np.asarray(xs))
    x = np.asarray(xs)[order]
    y = np.asarray(ys, float)[order]
    if y.size < 2:
        return {"n_points": int(y.size), "n_steps": 0, "n_steps_up": 0, "frac_steps_up": None,
                "strictly_increasing": None, "spearman_rho": None, "spearman_p": None,
                "first": None, "last": None, "total_change": None}
    d = np.diff(y)
    rho = p = None
    if y.size >= 3:
        from scipy import stats
        r = stats.spearmanr(x, y)
        rho = None if np.isnan(r.statistic) else float(r.statistic)
        p = None if np.isnan(r.pvalue) else float(r.pvalue)
    return {"n_points": int(y.size), "n_steps": int(d.size), "n_steps_up": int((d > 0).sum()),
            "frac_steps_up": float((d > 0).mean()),
            "strictly_increasing": bool((d > 0).all()),
            "spearman_rho": rho, "spearman_p": p,
            "first": float(y[0]), "last": float(y[-1]),
            "total_change": float(y[-1] - y[0])}


# --------------------------------------------------------------------------- #
# population bookkeeping
# --------------------------------------------------------------------------- #
def census(rows: Sequence[dict]) -> dict:
    def cnt(k):
        return dict(sorted(collections.Counter(r.get(k) for r in rows).items(),
                           key=lambda kv: str(kv[0])))
    return {"n_rows": len(rows), "split": cnt("split"), "cell": cnt("cell"),
            "condition": cnt("condition"), "query_kind": cnt("query_kind"),
            "n_examples": cnt("n_examples"), "bank_block": cnt("bank_block"),
            "domain": cnt("domain"), "n_domains": len({r.get("domain") for r in rows}),
            "n_families": len({r.get("family_id") for r in rows}),
            "n_prompt_ids": len({r.get("prompt_id") for r in rows}),
            "directions_fitted_on": cnt("directions_fitted_on"),
            "is_self_fit": cnt("is_self_fit"),
            "is_final_occurrence": cnt("is_final_occurrence"),
            "is_query_occurrence": cnt("is_query_occurrence")}


# --------------------------------------------------------------------------- #
# paired C - A machinery
# --------------------------------------------------------------------------- #
def build_pairs(rows: Sequence[dict], idxs: Sequence[int]):
    """Pair cell `C` (natural_doublespeak) against cell `A` (benign_literal) within
    (`family_id`, `occurrence_index`). `family_id` encodes domain, split, slot, n_examples,
    strength, consistency, example_position, role_style and query_kind but NOT the condition, so
    it is exactly the matched-family key the 2x2 needs."""
    slot: Dict[Tuple[str, int], Dict[str, int]] = collections.defaultdict(dict)
    for i in idxs:
        r = rows[i]
        if r.get("cell") in ("A", "C"):
            slot[(r["family_id"], int(r["occurrence_index"]))][r["cell"]] = i
    pairs, unmatched = [], collections.Counter()
    for key, d in slot.items():
        if len(d) == 2:
            pairs.append((d["C"], d["A"]))
        else:
            unmatched[f"only_{''.join(sorted(d))}"] += 1
    return pairs, dict(unmatched)


def group_pairs(rows: Sequence[dict], pairs, key_fn, dots: np.ndarray, layers: Sequence[int],
                with_ci: bool) -> dict:
    buckets: Dict[Tuple, List[Tuple[int, int]]] = collections.defaultdict(list)
    for ic, ia in pairs:
        buckets[key_fn(rows[ic])].append((ic, ia))
    out = {}
    for key, lst in buckets.items():
        ic = np.array([a for a, _ in lst])
        ia = np.array([b for _, b in lst])
        dom = np.array([rows[i].get("domain") for i in ic])
        entry = {"n_pairs": int(ic.size), "n_domains": int(len(set(dom.tolist()))),
                 "domains": sorted(set(dom.tolist())),
                 "per_layer": {}}
        for j, L in enumerate(layers):
            C = dots[ic, j, :]
            A = dots[ia, j, :]
            D = C - A
            ci = cluster_bootstrap_ci(D, dom) if with_ci else None
            entry["per_layer"][str(L)] = {
                m: {"C": summarise_vec(C[:, MIDX[m]]),
                    "A": summarise_vec(A[:, MIDX[m]]),
                    "C_minus_A_paired": summarise_vec(D[:, MIDX[m]]),
                    "ci95_domain_clustered": (ci[MIDX[m]] if ci else None)}
                for m in METRICS}
        out[key] = entry
    return out


# --------------------------------------------------------------------------- #
# main per-run driver
# --------------------------------------------------------------------------- #
def analyse_run(run: str, blocks: Sequence[str] = DEFAULT_BLOCKS) -> dict:
    meta_path = os.path.join(run, "metadata.json")
    meta = json.load(open(meta_path)) if os.path.exists(meta_path) else {}
    res_path = os.path.join(run, "results.jsonl")
    rows = [json.loads(l) for l in open(res_path)]
    payloads = load_payloads(run)
    if not payloads:
        return {"run_id": os.path.basename(os.path.normpath(run)),
                "error": "no directions_fit_*.pt"}
    any_pl = next(iter(payloads.values()))
    layers = [int(x) for x in sorted(any_pl["layers"])]

    entry = {
        "run_dir": os.path.abspath(run),
        "run_id": os.path.basename(os.path.normpath(run)),
        "results_jsonl_sha16": file_sha16(res_path),
        "metadata_sha16": file_sha16(meta_path),
        "bank_path": meta.get("bank_path"),
        "bank_file_sha16": meta.get("bank_file_sha16"),
        "bank_rows_sha16": meta.get("bank_rows_sha16"),
        "model": meta.get("model"),
        "seed": meta.get("seed"),
        "position": meta.get("position") or (any_pl.get("meta") or {}).get("position"),
        "producer_git_sha": meta.get("git_sha"),
        "producer_git_dirty": meta.get("git_dirty"),
        "producer_argv": meta.get("argv"),
        "layers": layers,
        "layer_convention": any_pl.get("layer_convention"),
        "payloads": {s: {"path": p["__path"], "sha16": p["__sha16"],
                         "n_per_cell": p.get("n_per_cell"),
                         "n_families": len(p.get("families") or []),
                         "family_set_sha16": (p.get("meta") or {}).get("family_set_sha16"),
                         "fit_dtype": (p.get("meta") or {}).get("fit_dtype"),
                         "fit_bank_rows_sha16": (p.get("meta") or {}).get("bank_rows_sha16"),
                         "scores_rows_of_split": s,
                         "used_to_score_split": other(s)}
                     for s, p in payloads.items()},
        "census_all_rows": census(rows),
    }

    # unrecognised query kind => crash, never a silent keep (rule 10)
    unknown = sorted({r.get("query_kind") for r in rows}
                     - set(OCC_SAFE_QUERY_KINDS) - set(OCC_UNSAFE_QUERY_KINDS))
    if unknown:
        raise SystemExit(f"[dcs-rowwise] unknown query_kind(s) {unknown}: "
                         "occurrence_analysis_safe is undefined for them. Refusing (rule 10).")

    dots, row_ok, comm = build_dots(rows, payloads, layers)
    entry["algebra_check"] = check_algebra(rows, dots, payloads, layers)
    comm["composition"] = census([r for r, ok in zip(rows, row_ok) if ok])
    entry["common_population"] = comm

    common_idx = [i for i in range(len(rows)) if row_ok[i]]
    safe_idx = [i for i in common_idx if rows[i]["query_kind"] not in OCC_UNSAFE_QUERY_KINDS]
    removed_idx = [i for i in common_idx if rows[i]["query_kind"] in OCC_UNSAFE_QUERY_KINDS]
    entry["occurrence_safety_filter"] = {
        "rule": "prompt_families.QUERY_KINDS[...]['occurrence_analysis_safe'] is False",
        "unsafe_query_kinds": list(OCC_UNSAFE_QUERY_KINDS),
        "n_removed": len(removed_idx),
        "removed_by_query_kind": dict(collections.Counter(rows[i]["query_kind"]
                                                          for i in removed_idx)),
        "removed_by_cell": dict(collections.Counter(rows[i]["cell"] for i in removed_idx)),
        "n_after": len(safe_idx),
        "composition_after": census([rows[i] for i in safe_idx]),
    }

    blocks = tuple(blocks)
    core_idx = [i for i in safe_idx
                if rows[i].get("bank_block") in blocks and rows[i].get("cell") in CORE_CELLS]
    entry["analysis_blocks"] = list(blocks)
    entry["core2x2_population"] = census([rows[i] for i in core_idx])

    # --- (1) per-row metric distribution per cell x layer, final occurrence, common population ---
    fin_core = [i for i in core_idx if rows[i].get("is_final_occurrence")]
    cellsum = {}
    for j, L in enumerate(layers):
        per_cell = {}
        for c in CORE_CELLS:
            sel = [i for i in fin_core if rows[i]["cell"] == c]
            if not sel:
                continue
            arr = dots[sel, j, :]
            per_cell[c] = {m: summarise_vec(arr[:, MIDX[m]]) for m in METRICS}
        cellsum[str(L)] = per_cell
    entry["cell_summary_final_occurrence"] = cellsum

    # --- (3) MANDATORY stratification: layer x n_examples PER query_kind, final occurrence ---
    pairs_fin, unmatched_fin = build_pairs(rows, fin_core)
    g = group_pairs(rows, pairs_fin,
                    lambda r: (r["query_kind"], int(r["n_examples"])),
                    dots, layers, with_ci=True)
    strat: dict = {}
    for (qk, ne), v in g.items():
        strat.setdefault(qk, {})[str(ne)] = v
    entry["stratified_layer_x_nexamples_per_query_kind"] = strat
    entry["stratification_note"] = (
        "cand1 changes sign with n_examples and depends on query_kind (plan Sec 1.7); these "
        "surfaces are NEVER pooled over either axis. Pairing is C vs A within family_id at the "
        "final (query) occurrence, which is the position the directions were fitted at.")
    entry["stratification_unmatched"] = unmatched_fin

    # --- (2) OCCURRENCE TRAJECTORY: layer x occurrence_index, per (query_kind, n_examples) ---
    pairs_all, unmatched_all = build_pairs(rows, core_idx)
    gt = group_pairs(rows, pairs_all,
                     lambda r: (r["query_kind"], int(r["n_examples"]),
                                int(r["occurrence_index"]), int(r["n_occurrences"]),
                                bool(r["is_final_occurrence"])),
                     dots, layers, with_ci=False)
    traj: dict = {}
    for (qk, ne, occ, nocc, isfin), v in gt.items():
        v = dict(v)
        v["n_occurrences"] = nocc
        v["is_final_occurrence"] = isfin
        v["rel_from_final"] = occ - (nocc - 1)
        traj.setdefault(qk, {}).setdefault(str(ne), {})[str(occ)] = v
    entry["occurrence_trajectory"] = traj
    entry["occurrence_trajectory_unmatched"] = unmatched_all

    # --- monotonicity ledger over the trajectory ---
    mono: dict = {}
    for qk, per_ne in traj.items():
        for ne, per_occ in per_ne.items():
            occs = sorted(int(o) for o in per_occ)
            if len(occs) < 3:
                continue
            # DEMO-ONLY is the series the plan Sec 8 question is actually about ("across
            # DEMONSTRATION occurrences"): the final occurrence is the QUERY occurrence, a
            # different kind of position, and including it turns a trajectory question into a
            # trajectory-plus-one-jump question. Both are emitted, named apart.
            demo_occs = [o for o in occs if not per_occ[str(o)]["is_final_occurrence"]]
            for L in layers:
                for m in METRICS:
                    for series in ("C_minus_A_paired", "C", "A"):
                        for tag, oo in (("", occs), ("__demos_only", demo_occs)):
                            xs, ys = [], []
                            for o in oo:
                                st = per_occ[str(o)]["per_layer"][str(L)][m][series]
                                if st["mean"] is None:
                                    continue
                                xs.append(o)
                                ys.append(st["mean"])
                            if len(ys) < 3:
                                continue
                            (mono.setdefault(qk, {}).setdefault(ne, {}).setdefault(m, {})
                             .setdefault(series + tag, {})[str(L)]) = monotone_report(xs, ys)
    entry["occurrence_monotonicity"] = mono
    return entry


# --------------------------------------------------------------------------- #
# console table
# --------------------------------------------------------------------------- #
def print_tables(entry: dict, focus_metric: str, focus_layers: Sequence[int]) -> None:
    ac = entry["algebra_check"]
    print(f"\n=== {entry['run_id']}")
    print(f"  model={entry['model']}  position={entry['position']}  "
          f"bank_rows_sha16={entry['bank_rows_sha16']}  layers={len(entry['layers'])}")
    print(f"  ALGEBRA GATE passed={ac['passed']}  worst_rel_err={ac['worst_rel_err']:.3e} "
          f"(tol {ac['tol']:.0e})  "
          f"[check1 {max(v['max_rel_err'] for v in ac['check1_vector_identity'].values()):.2e}, "
          f"check2 cos-scaled {max(v.get('max_cos_scaled_err', 0) for v in ac['check2_row_mean_vs_cell_mean'].values()):.2e}, "
          f"check2 naive-nondegenerate {max(v.get('max_naive_rel_err_nondegenerate', 0) for v in ac['check2_row_mean_vs_cell_mean'].values()):.2e} "
          f"(skipped {sum(v.get('n_degenerate_skipped', 0) for v in ac['check2_row_mean_vs_cell_mean'].values())} degenerate "
          f"of {sum(v.get('n_comparisons', 0) for v in ac['check2_row_mean_vs_cell_mean'].values())})]")
    cp = entry["common_population"]
    print(f"  COMMON POPULATION n_input={cp['n_input']} n_common={cp['n_common']} "
          f"excluded={cp['n_excluded']} {cp['exclusions']}  "
          f"identical_across_metrics={cp['definedness_identical_across_metrics']}")
    print(f"    composition: domains={cp['composition']['n_domains']} "
          f"families={cp['composition']['n_families']} cells={cp['composition']['cell']} "
          f"query_kinds={cp['composition']['query_kind']}")
    osf = entry["occurrence_safety_filter"]
    print(f"  OCCURRENCE-SAFETY FILTER removed {osf['n_removed']} rows "
          f"{osf['removed_by_query_kind']} by cell {osf['removed_by_cell']} -> n={osf['n_after']}")
    print(f"  blocks={entry['analysis_blocks']} A/B/C/E after filter: n={entry['core2x2_population']['n_rows']} "
          f"cells={entry['core2x2_population']['cell']}")

    print(f"\n  [STRATIFIED] paired C-A on {focus_metric}, FINAL (query) occurrence "
          f"-- mean [domain-clustered 95% CI]")
    for qk, per_ne in sorted(entry["stratified_layer_x_nexamples_per_query_kind"].items()):
        print(f"   query_kind={qk}")
        print("     n_ex  " + "".join(f"{('L%d' % L):>24s}" for L in focus_layers)
              + "   n_pairs n_dom")
        for ne in sorted(per_ne, key=int):
            v = per_ne[ne]
            cells = []
            for L in focus_layers:
                pl = v["per_layer"].get(str(L))
                if pl is None:
                    cells.append(f"{'--':>24s}")
                    continue
                s = pl[focus_metric]["C_minus_A_paired"]
                ci = pl[focus_metric]["ci95_domain_clustered"]
                t = f"{s['mean']:+.2f}" if s["mean"] is not None else "na"
                if ci:
                    t += f"[{ci[0]:+.2f},{ci[1]:+.2f}]"
                cells.append(f"{t:>24s}")
            print(f"     {ne:>4s}  " + "".join(cells)
                  + f"   {v['n_pairs']:5d} {v['n_domains']:4d}")

    print(f"\n  [OCCURRENCE TRAJECTORY] {focus_metric}: paired C-A mean by occurrence_index")
    for qk in sorted(entry["occurrence_trajectory"]):
        for ne in sorted(entry["occurrence_trajectory"][qk], key=int):
            per_occ = entry["occurrence_trajectory"][qk][ne]
            occs = sorted(int(o) for o in per_occ)
            if len(occs) < 2:
                continue
            nocc = per_occ[str(occs[0])]["n_occurrences"]
            print(f"   query_kind={qk} n_examples={ne}  n_occurrences={nocc}  "
                  f"occ_indices={occs} (final={occs[-1]})")
            print("     layer  " + "".join(f"{('o%d' % o):>9s}" for o in occs)
                  + "     rho  up/steps   n_pairs")
            mo = entry["occurrence_monotonicity"].get(qk, {}).get(ne, {}).get(focus_metric, {})
            mono = mo.get("C_minus_A_paired", {})
            monod = mo.get("C_minus_A_paired__demos_only", {})
            for L in focus_layers:
                cells, npair = [], 0
                for o in occs:
                    s = per_occ[str(o)]["per_layer"][str(L)][focus_metric]["C_minus_A_paired"]
                    npair = max(npair, per_occ[str(o)]["n_pairs"])
                    cells.append(f"{s['mean']:>+9.2f}" if s["mean"] is not None else f"{'na':>9s}")
                mm = mono.get(str(L))
                tail = ""
                if mm and mm["spearman_rho"] is not None:
                    tail = (f"  {mm['spearman_rho']:+.2f}  {mm['n_steps_up']}/{mm['n_steps']}"
                            f"{'  MONO' if mm['strictly_increasing'] else ''}")
                md = monod.get(str(L))
                if md and md["spearman_rho"] is not None:
                    tail += (f" | demos-only rho {md['spearman_rho']:+.2f} "
                             f"{md['n_steps_up']}/{md['n_steps']}"
                             f"{' MONO' if md['strictly_increasing'] else ''}")
                print(f"     {L:5d}  " + "".join(cells) + f"  {tail}   n={npair}")


# --------------------------------------------------------------------------- #
def main(argv: Optional[Sequence[str]] = None) -> int:
    started = _dt.datetime.now(_dt.timezone.utc).isoformat()
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--runs", nargs="+", required=True,
                    help="extract_boombness run dirs (results.jsonl + directions_fit_*.pt)")
    ap.add_argument("--out", required=True,
                    help="output JSON path. With --per-run-out, the literal token BANK in the "
                         "path is replaced by each run's bank slug.")
    ap.add_argument("--per-run-out", action="store_true")
    ap.add_argument("--focus-metric", default="cand1_C_minus_A", choices=list(METRICS))
    ap.add_argument("--focus-layers", nargs="+", type=int, default=[0, 6, 8, 12, 18, 24, 31])
    ap.add_argument("--blocks", nargs="+", default=list(DEFAULT_BLOCKS),
                    help="bank_block values admitted to the A/B/C/E analyses")
    ap.add_argument("--bank-slugs", nargs="+", default=["button_bomb", "basket_bomb"],
                    help="substrings used to name per-run output files")
    args = ap.parse_args(list(argv) if argv is not None else None)

    entries, failed = {}, []
    for run in args.runs:
        e = analyse_run(run, args.blocks)
        entries[e.get("run_id", run)] = e
        if "error" in e or not e.get("algebra_check", {}).get("passed", False):
            failed.append(e.get("run_id", run))

    for rid, e in entries.items():
        if "error" in e:
            print(f"  {rid}: ERROR {e['error']}")
        else:
            print_tables(e, args.focus_metric, args.focus_layers)

    prov = provenance(started)
    if args.per_run_out:
        for rid, e in entries.items():
            slug = rid
            for tag in args.bank_slugs:
                if tag in rid:
                    slug = tag
            path = args.out.replace("BANK", slug)
            os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
            with open(path, "w") as f:
                json.dump({"provenance": prov, "runs": {rid: e}}, f, indent=1)
            print(f"[dcs-rowwise] wrote {path}")
    else:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)) or ".", exist_ok=True)
        with open(args.out, "w") as f:
            json.dump({"provenance": prov, "runs": entries}, f, indent=1)
        print(f"[dcs-rowwise] wrote {args.out}  ({len(entries)} runs)")

    if failed:
        print(f"[dcs-rowwise] ALGEBRA GATE / LOAD FAILED for: {failed}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
