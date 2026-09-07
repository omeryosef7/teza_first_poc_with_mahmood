#!/usr/bin/env python3
"""DCS-PR-057 PHASE 9, blocker **Q2**: export the PR-053 directions to disk as a `--fit-dir`.

WHY THIS FILE EXISTS
--------------------
`configs/dcs_ts_pr057_phase9.json` names its direction artifact as
`outputs/dcs_ts_pr053_diffmeans/<run>/directions.pt` and then says, in `directions.artifact.
pin_rule`, that **the file does not exist**: PR-053's analyzer computes `v_bomb_specific` in memory,
reports its AUROC and exits. PHASE 9's primary causal test (mandate 10.2, promoted by `C-112`)
is "project `v_bomb_specific` out of a BOMB prompt", and `src/boombness/score_behavior.py
--intervene ...:project_out:...` can only do that if the direction is ON DISK in the format its
loader reads. Q2 is that gap. This file closes it.

WHAT IT DOES NOT DO
-------------------
It does not re-derive the estimator. `scripts/dcs_ts_pr053_diffmeans.py` already implements it and
is the file that produced `R-111`; every load, guard and arithmetic step here is IMPORTED from it
(`build_arm`, `verify_run`, `excluded_domains`, `load_split`, `_nonempty`, `CELL_BASELINE`) or from
`scripts/dcs_diffmeans_directions.py` (`auroc`, `unit`, `project`, `band`, `std_diff`). A second
implementation of an estimator whose result is already published would be a way to ship a direction
that does not match the number it claims to come from.

THE DIRECTIONS, exactly as `configs/dcs_ts_pr053.json` `directions` freezes them:

    v_c(l)              = mean over TRAIN domains of [ h_l(C_c) - h_l(A_shared) ], PAIRED on
                          family_id, for c in {bomb, knife, gun}
    v_remap(l)          = v_bomb(l)
    v_bomb_specific(l)  = v_bomb(l) - mean(v_knife(l), v_gun(l))          (no club -- `_no_club`)

and, because `configs/dcs_ts_pr057_phase9.json` `directions` also names it for the H3 replacement
arm, the symmetric

    v_knife_specific(l) = v_knife(l) - mean(v_bomb(l), v_gun(l))

Per layer over the frozen 6-14 band. TRAIN ONLY: 67 domains, after the three whole-population
exclusions (restaurant_kitchen, subway_station, school_campus). Validation and test never enter a
direction, and the fit set is asserted EQUAL to the frozen manifest's train split -- not merely
disjoint from test -- so a fit that quietly grew or shrank is a refusal, not a footnote.

THE FORMAT IS DERIVED FROM THE CONSUMER, NOT GUESSED
----------------------------------------------------
`score_behavior.py:2081` does

    p = os.path.join(args.fit_dir, "directions_fit_dev.pt")
    if not os.path.exists(p): p = os.path.join(args.fit_dir, "directions_fit_heldout.pt")
    payload = torch.load(p, map_location="cpu", weights_only=False)

and then `make_intervention` reads `payload[<direction name>][<int layer>] -> Tensor[H]`
(`score_behavior.py:1395`), `payload["gap"][<name>][<layer>]` for `mode=add`
(`score_behavior.py:1400`), `payload["cell_means"][<cell>][<layer>]` for the realised-dose records
(`insubspace_null_test.cellmean_dose`, `score_behavior.cell_residual_frac_removed`), and -- since
`Q13` -- `payload[<control base name>]` for a norm-matched control's base direction. So the file is
named `directions_fit_dev.pt` (the name the loader tries FIRST) and carries those keys. Everything
else lives under `meta`, which no consumer indexes.

Vectors are stored UNIT and the natural effect size is kept in `gap`, exactly as
`src/boombness/signals.py:estimate_directions` does, because `make_intervention` doses `add` in gap
units. `project_out` is scale-free and unaffected.

VERIFICATION -- the artifact must reproduce the result it claims to come from
----------------------------------------------------------------------------
`--verify` reloads the written file from disk and re-scores the 23 untouched TEST domains with it.
The band-mean domain-mean AUROC of `proj(h, v_bomb_specific)` separating `C_bomb` from
{`C_knife`, `C_gun`} must reproduce `R-111`'s published **0.9764**, CI [0.9622, 0.9906], 23/23
domains, and the per-layer profile of `reports/DCS_TS_PR053_DIFFMEANS.md` section 4.1. If it does
not, the export FAILS -- a direction that does not reproduce the result it is named after is worse
than no direction at all.

USAGE
    python3 scripts/dcs_ts_export_directions.py --export
    python3 scripts/dcs_ts_export_directions.py --verify
    python3 scripts/dcs_ts_export_directions.py --export --mutate
    python3 scripts/dcs_ts_export_directions.py --selftest      # no data needed
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone

import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "scripts"))

from dcs_ts_prereg import Prereg, PreregError, load                          # noqa: E402
from dcs_ts_pr053_diffmeans import (CELL_BASELINE, TARGET, _nonempty,        # noqa: E402
                                    build_arm, excluded_domains, load_split,
                                    verify_run)
from dcs_ts_pr048_analysis import _find_run                                  # noqa: E402
from dcs_diffmeans_directions import auroc, band, project, std_diff, unit    # noqa: E402

DEFAULT_OUT = "outputs/dcs_ts/directions_pr053"
#: `score_behavior.py:2082` tries this name first. Calling the file anything else makes the
#: `--fit-dir` silently unusable, which is the whole of Q2 all over again.
PAYLOAD_NAME = "directions_fit_dev.pt"
MANIFEST_NAME = "MANIFEST.json"
VERIFY_NAME = "VERIFY.json"

#: THE PUBLISHED NUMBERS THIS ARTIFACT MUST REPRODUCE. Not design thresholds -- they are the
#: already-reported result of `R-111`, transcribed from `reports/DCS_TS_PR053_DIFFMEANS.md`
#: sections 4 and 4.1 (primary table and per-layer profile). The artifact is checked AGAINST them;
#: nothing here is free to be tuned.
R111 = {
    "band_mean_auroc": 0.9764,
    "ci95": [0.9622, 0.9906],
    "between_domain_sd": 0.0347,
    "n_domains_above_chance": 23,
    "n_test_domains": 23,
    "cohens_d_band_lo": 2.81,
    "cohens_d_band_hi": 3.15,
    "auroc_by_layer": [0.9639, 0.9687, 0.9735, 0.9746, 0.9793, 0.9809, 0.9824, 0.9830, 0.9813],
    "source": "reports/DCS_TS_PR053_DIFFMEANS.md sections 4 and 4.1 (R-111)",
}
#: The published values are given to 4 decimals, so the reproduction must agree to 4 decimals.
#: A looser tolerance would let a materially different direction pass; a tighter one would be
#: testing the report's rounding, not the arithmetic.
DP = 4
_Z_ALPHA2 = 1.9599639845400545   # Phi^-1(0.975); the CI convention R-111 used, not a gate

#: Tolerance for the TRAIN-ONLY RECOMPUTATION check (`check_train_only_recomputation`), on UNIT
#: vectors. It is bracketed by two measured numbers, not chosen for comfort:
#:   * an HONEST fit re-derived from the TRAIN rows agrees with the shipped float32 arrays to
#:     ~5e-09 -- that is the float32 storage precision of the payload, and it is the floor;
#:   * a LEAKED fit (TRAIN + the 23 TEST domains) differs from it by ~1.1e-02 -- that is the
#:     smallest deviation the check has to catch, and it is the ceiling.
#: (Both observed in reports/DCS_TS_PR053_DIRECTION_EXPORT_ADVERSARIAL_REVIEW.md section 1b, and
#: both reproduced by this check: see the residuals printed by --verify and --mutate.)
#: 1e-06 sits ~200x above the storage floor -- so no honest export can trip it, whatever the
#: rounding of the last float32 bit -- and ~10,000x below the leak, so the smallest leakage the
#: reviewer could construct is still four orders of magnitude outside it. Anything in that window
#: would do; the window itself is six orders wide, which is why the check has resolution at all.
REFIT_ATOL = 1e-6
#: `gap` is stored as a float64 scalar, so an honest gap matches EXACTLY; the leaked fit moves it
#: by ~1e-2 relative. A relative tolerance well inside that window, loose enough for the float64
#: round-trip through torch.save.
REFIT_GAP_RTOL = 1e-9


# ================================================================================== utilities
def _sha256_hex(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def content_sha256(dirs: dict, layers) -> str:
    """A content hash of the ARRAYS, in a fixed order, so PHASE 9 can prove which direction it
    projected out. Names and layer indices are hashed alongside the bytes: hashing the numbers
    alone would let two directions swap names without changing the digest."""
    h = hashlib.sha256()
    for name in sorted(dirs):
        for i, L in enumerate(layers):
            h.update(f"{name}|{int(L)}|".encode())
            h.update(np.ascontiguousarray(dirs[name][i], dtype=np.float32).tobytes())
    return h.hexdigest()


def _file_sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


class CheckLog:
    """Every check is named, recorded, and RED-or-GREEN. A check that binds nothing is RED."""

    def __init__(self):
        self.rows = []

    def add(self, name: str, ok: bool, detail: str = "") -> bool:
        self.rows.append({"check": name, "status": "GREEN" if ok else "RED", "detail": detail})
        return bool(ok)

    @property
    def red(self):
        return [r for r in self.rows if r["status"] == "RED"]

    @property
    def ok(self):
        return not self.red and bool(self.rows)

    def show(self, prefix="  "):
        for r in self.rows:
            print(f"{prefix}[{r['status']:5s}] {r['check']}"
                  + (f"  --  {r['detail']}" if r["detail"] else ""))


# ============================================================================== the estimator
def fit_directions(Dm: dict, fit_domains, concepts) -> dict:
    """v_c = mean over `fit_domains` of the per-domain paired mean [h(C_c) - h(A_shared)].

    `Dm[c][d]` is exactly what `dcs_ts_pr053_diffmeans.build_arm` returns, and the mean over
    domains is exactly `evaluate()`'s `U[:, 0].mean(axis=0)` / `W[:, 0].mean(axis=0)`. Raw (NOT
    unit) vectors, per layer, shape (nL, H).
    """
    tr = [d for d in fit_domains if all(d in Dm[c] for c in concepts)]
    _nonempty(tr, "direction fit: domains with a paired difference in every concept")
    if len(tr) != len(set(tr)):
        raise PreregError("the fit domain list contains duplicates; a domain counted twice is a "
                          "silent reweighting of the estimator")
    v = {c: np.stack([Dm[c][d] for d in tr]).mean(axis=0).astype(np.float64) for c in concepts}
    bomb, knife, gun = (v[c] for c in concepts)
    out = {
        "v_bomb": bomb,
        "v_knife": knife,
        "v_gun": gun,
        "v_remap": bomb.copy(),                              # the raw axis, PR-053 `v_remap`
        "v_bomb_specific": bomb - 0.5 * (knife + gun),       # the residualised identity axis
        "v_knife_specific": knife - 0.5 * (bomb + gun),      # PR-057 H3's counterfactual target
    }
    return {"raw": out, "fit_domains": tr}


def train_refit(ctx: dict) -> dict:
    """Re-derive the direction arrays from the TRAIN ROWS, independently of anything the payload
    says about itself.

    The TRAIN domain set used here is `ctx["train"]`, which `prepare()` rebuilt from the FROZEN
    SPLIT MANIFEST (`load_split(pr)` minus the preregistered exclusions) -- NOT from
    `meta.fit_domains`, which is the producer's own claim about the producer. The rows are
    `ctx["arm"]["Dmean"]`, i.e. the same per-domain paired differences `build_payload` fitted from.

    Cached on `ctx` because the mutation harness calls it once per case and neither the split nor
    the arm changes between them.
    """
    if "_train_refit" not in ctx:
        Dm = {c: ctx["arm"]["Dmean"][(c, ctx["dose"])] for c in ctx["concepts"]}
        ctx["_train_refit"] = fit_directions(Dm, ctx["train"], ctx["concepts"])
    return ctx["_train_refit"]


def score_identity_auroc(v_spec_unit: np.ndarray, rows: dict, dose, test_domains, concepts):
    """R-111's PRIMARY, recomputed from a direction: per-domain per-layer AUROC of
    proj(h, v_bomb_specific) separating C_bomb from {C_knife, C_gun}, then the domain mean.

    `v_spec_unit` is (nL, H) and unit per layer. AUROC is invariant to a positive per-layer
    rescale, so scoring with the exported UNIT vector is the same statistic as R-111's.
    """
    doms = [d for d in test_domains if all(d in rows[(c, dose)] for c in concepts)]
    _nonempty(doms, "reproduction: TEST domains carrying rows in every concept")
    nL = v_spec_unit.shape[0]
    per_dom, per_dom_layers = {}, {}
    pos_all, neg_all = [], []
    for d in doms:
        pos = project(_nonempty(rows[(concepts[0], dose)][d]["C"], f"C_{concepts[0]} in {d}"),
                      v_spec_unit)
        neg = project(np.concatenate([_nonempty(rows[(c, dose)][d]["C"], f"C_{c} in {d}")
                                      for c in concepts[1:]], axis=0), v_spec_unit)
        by_layer = [auroc(pos[:, l], neg[:, l]) for l in range(nL)]
        per_dom_layers[d] = by_layer
        per_dom[d] = band(by_layer)
        pos_all.append(pos)
        neg_all.append(neg)
    vals = [per_dom[d] for d in doms]
    by_layer_mean = [float(np.mean([per_dom_layers[d][l] for d in doms])) for l in range(nL)]
    mean = float(np.mean(vals))
    sd = float(np.std(vals, ddof=1))
    half = _Z_ALPHA2 * sd / np.sqrt(len(vals))
    Pp = np.concatenate(pos_all, axis=0)
    Pn = np.concatenate(neg_all, axis=0)
    return {"n_test_domains": len(doms), "test_domains": doms,
            "auroc_by_layer": by_layer_mean, "band_mean_auroc": mean,
            "per_domain_band_auroc": per_dom, "between_domain_sd": sd,
            "ci95": [mean - half, mean + half],
            "n_domains_above_chance": int(sum(1 for x in vals if x > 0.5)),
            "cohens_d_by_layer": [std_diff(Pp[:, l], Pn[:, l]) for l in range(v_spec_unit.shape[0])]}


# ================================================================================ the checks
def check_payload(payload: dict, ctx: dict, log: CheckLog) -> CheckLog:
    """Every property PHASE 9 is entitled to assume about this artifact, checked on the LOADED
    object rather than on the in-memory one that produced it."""
    meta = payload.get("meta") or {}
    layers = list(payload.get("layers") or [])
    names = list(meta.get("direction_names") or [])

    # ---- shape / layer grid --------------------------------------------------------------
    log.add("layer grid == prereg read_site.layer_grid",
            layers == list(ctx["layer_grid"]) and len(layers) > 0,
            f"payload {layers} vs prereg {list(ctx['layer_grid'])}")
    log.add("payload carries the direction names PHASE 9 needs",
            {"v_bomb_specific", "v_remap", "v_bomb", "v_knife", "v_gun"}.issubset(set(names))
            and all(n in payload for n in names) and len(names) > 0,
            f"names={sorted(names)}")

    dirs = {}
    shape_ok, unit_ok, finite_ok = True, True, True
    for n in names:
        dmap = payload.get(n) or {}
        if sorted(dmap) != sorted(int(L) for L in layers):
            shape_ok = False
            continue
        arr = np.stack([dmap[int(L)].double().numpy() for L in layers])
        dirs[n] = arr
        if arr.shape != (len(layers), int(ctx["hidden"])):
            shape_ok = False
        if not np.isfinite(arr).all():
            finite_ok = False
        norms = np.linalg.norm(arr, axis=1)
        if not np.allclose(norms, 1.0, atol=1e-5):
            unit_ok = False
    log.add("every direction covers every layer at the model's hidden width", shape_ok,
            f"expected ({len(layers)}, {ctx['hidden']}) per direction")
    log.add("every stored vector is finite", finite_ok)
    log.add("every stored vector is UNIT (add-dosing lives in `gap`)", unit_ok)
    log.add("no direction is degenerate (raw norm > 0 at every layer)",
            bool(payload.get("gap")) and all(
                min((payload["gap"][n] or {}).values()) > 1e-9 for n in names
                if n in (payload.get("gap") or {})),
            "gap[name][L] == ||raw v|| ; a zero-norm axis would make project_out a no-op")

    # ---- TRAIN ONLY. The single most important property of the artifact. ------------------
    fit = list(meta.get("fit_domains") or [])
    log.add("fit domain set is NON-EMPTY", len(fit) > 0)
    log.add("fit domain set == the frozen manifest's TRAIN split, exactly",
            sorted(fit) == sorted(ctx["train"]),
            f"n_fit={len(fit)} n_train={len(ctx['train'])} "
            f"extra={sorted(set(fit) - set(ctx['train']))[:5]} "
            f"missing={sorted(set(ctx['train']) - set(fit))[:5]}")
    log.add("fit domain set is DISJOINT from validation",
            not (set(fit) & set(ctx["valid"])), f"{sorted(set(fit) & set(ctx['valid']))[:5]}")
    log.add("fit domain set is DISJOINT from test",
            not (set(fit) & set(ctx["test"])), f"{sorted(set(fit) & set(ctx['test']))[:5]}")
    log.add("the three whole-population exclusions are absent from the fit set",
            not (set(fit) & set(ctx["excluded"])), f"excluded={sorted(ctx['excluded'])}")
    log.add("fit domain count matches split.n_train", len(fit) == int(ctx["n_train"]),
            f"{len(fit)} vs {ctx['n_train']}")

    # ---- TRAIN ONLY, RECOMPUTED. The check that does not take the producer's word for it. ---
    check_train_only_recomputation(payload, ctx, dirs, layers, log)

    # ---- the estimator's own algebra -----------------------------------------------------
    if {"v_bomb", "v_knife", "v_gun", "v_bomb_specific", "v_remap"}.issubset(dirs):
        g = payload["gap"]
        raw = {n: dirs[n] * np.array([g[n][int(L)] for L in layers])[:, None] for n in dirs}
        spec = raw["v_bomb"] - 0.5 * (raw["v_knife"] + raw["v_gun"])
        log.add("v_bomb_specific == v_bomb - mean(v_knife, v_gun), as PR-053 froze it",
                np.allclose(raw["v_bomb_specific"], spec, rtol=1e-5, atol=1e-4),
                f"max|diff| {float(np.abs(raw['v_bomb_specific'] - spec).max()):.3e}")
        log.add("v_remap == v_bomb (the raw axis)",
                np.allclose(raw["v_remap"], raw["v_bomb"], rtol=1e-6, atol=1e-6),
                f"max|diff| {float(np.abs(raw['v_remap'] - raw['v_bomb']).max()):.3e}")
    else:
        log.add("v_bomb_specific == v_bomb - mean(v_knife, v_gun), as PR-053 froze it", False,
                "the payload does not carry the terms needed to check it")

    # ---- provenance ----------------------------------------------------------------------
    log.add("content sha256 of the arrays matches the recorded one",
            bool(dirs) and content_sha256(dirs, layers) == meta.get("content_sha256"),
            f"recomputed {content_sha256(dirs, layers)[:16] if dirs else 'n/a'} vs recorded "
            f"{str(meta.get('content_sha256'))[:16]}")
    log.add("bank shas recorded == configs/dcs_ts_pr048.json",
            (meta.get("bank_rows_sha16") or {}) == ctx["bank_rows_sha16_pr048"]
            and bool(ctx["bank_rows_sha16_pr048"]),
            "the six ts116m banks")
    log.add("split manifest sha recorded == the frozen manifest",
            meta.get("split_manifest_sha16") == ctx["split_manifest_sha16"])
    log.add("per-layer norms recorded for every direction",
            all(len(meta.get("norms", {}).get(n, [])) == len(layers) for n in names) and bool(names))
    log.add("read site recorded and equal to the preregistered one",
            meta.get("position") == ctx["position"], f"{meta.get('position')!r}")
    return log


def check_train_only_recomputation(payload: dict, ctx: dict, dirs: dict, layers, log: CheckLog):
    """RECOMPUTE the direction arrays from the TRAIN rows and compare them to the STORED arrays.

    WHY THIS EXISTS (F-1 of reports/DCS_TS_PR053_DIRECTION_EXPORT_ADVERSARIAL_REVIEW.md). Every
    other TRAIN-only check in `check_payload` reads `meta.fit_domains` -- a field the producer
    writes ABOUT ITSELF. A payload whose ARRAYS were fitted on TRAIN + TEST while its METADATA
    honestly lists the 67 TRAIN domains passes all of them: the verifier asserts the producer's
    claim, not the producer's arithmetic. That is this repo's recorded
    `feedback_check_reads_same_broken_source` failure class.

    This check touches `meta.fit_domains` for exactly one purpose -- to catch it LYING. The
    arithmetic is compared against a fit over the TRAIN set rebuilt from the frozen split
    manifest, so BOTH directions of a metadata/array disagreement are caught:

      * arrays leaked, metadata honest  -> the array comparison goes RED;
      * arrays honest, metadata lying   -> the domain-set comparison goes RED.
    """
    meta = payload.get("meta") or {}
    A_NAME = ("direction arrays RECOMPUTED from the TRAIN rows equal the stored arrays "
              f"(atol {REFIT_ATOL:g}, not trusting meta.fit_domains)")
    D_NAME = "meta.fit_domains == the TRAIN set rebuilt from the frozen split manifest"
    try:
        refit = train_refit(ctx)
    except Exception as e:                      # a recomputation that cannot run proves nothing
        log.add(A_NAME, False, f"the recomputation itself failed: {type(e).__name__}: {e}")
        log.add(D_NAME, False, "recomputation unavailable")
        return log
    tr = list(refit["fit_domains"])

    grid = [int(L) for L in ctx["layer_grid"]]
    ok, detail = bool(dirs), ""
    worst_u, worst_u_name = 0.0, None
    worst_g, worst_g_name = 0.0, None
    if not dirs:
        detail = "no direction arrays could be stacked from the payload"
    for name in sorted(refit["raw"]):
        ref = refit["raw"][name]
        if name not in dirs:
            ok = False
            detail = f"{name} is absent or malformed in the payload; nothing to compare"
            continue
        try:
            idx = [grid.index(int(L)) for L in layers]
        except ValueError:
            ok = False
            detail = f"payload layers {list(layers)} are not a subset of the fitted grid {grid}"
            break
        u_ref = unit(ref)[idx]
        du = float(np.abs(np.asarray(dirs[name], dtype=np.float64) - u_ref).max())
        if du > worst_u:
            worst_u, worst_u_name = du, name
        if not (du <= REFIT_ATOL):
            ok = False
        g = (payload.get("gap") or {}).get(name) or {}
        n_ref = np.linalg.norm(ref, axis=1)[idx]
        for i, L in enumerate(layers):
            gv = g.get(int(L))
            if gv is None:
                ok = False
                detail = f"gap[{name}][{int(L)}] is missing; the raw scale cannot be compared"
                continue
            rel = abs(float(gv) - float(n_ref[i])) / max(float(n_ref[i]), 1e-12)
            if rel > worst_g:
                worst_g, worst_g_name = rel, name
            if not (rel <= REFIT_GAP_RTOL):
                ok = False
    log.add(A_NAME, ok,
            (detail + "; " if detail else "")
            + f"max|unit diff| {worst_u:.3e} ({worst_u_name}) vs atol {REFIT_ATOL:g}; "
              f"max gap rel-diff {worst_g:.3e} ({worst_g_name}); "
              f"refit over {len(tr)} manifest TRAIN domains")
    fit = list(meta.get("fit_domains") or [])
    log.add(D_NAME, bool(tr) and sorted(fit) == sorted(tr),
            f"n_meta={len(fit)} n_manifest={len(tr)} "
            f"extra={sorted(set(fit) - set(tr))[:5]} missing={sorted(set(tr) - set(fit))[:5]}")
    return log


def check_reproduction(rep: dict, log: CheckLog) -> CheckLog:
    """The artifact must reproduce R-111. Rounded to the 4 decimals the report publishes."""
    log.add("reproduction bound a NON-EMPTY test set",
            rep["n_test_domains"] == R111["n_test_domains"] and rep["n_test_domains"] > 0,
            f"{rep['n_test_domains']} test domains")
    log.add(f"band-mean identity AUROC reproduces R-111's {R111['band_mean_auroc']}",
            round(rep["band_mean_auroc"], DP) == R111["band_mean_auroc"],
            f"got {rep['band_mean_auroc']:.6f}")
    log.add("95% CI over domains reproduces [0.9622, 0.9906]",
            [round(x, DP) for x in rep["ci95"]] == R111["ci95"],
            f"got [{rep['ci95'][0]:.6f}, {rep['ci95'][1]:.6f}]")
    log.add("between-domain SD reproduces 0.0347",
            round(rep["between_domain_sd"], DP) == R111["between_domain_sd"],
            f"got {rep['between_domain_sd']:.6f}")
    log.add("23/23 test domains above chance",
            rep["n_domains_above_chance"] == R111["n_domains_above_chance"],
            f"{rep['n_domains_above_chance']}/{rep['n_test_domains']}")
    log.add("per-layer profile reproduces section 4.1 at all nine layers",
            [round(x, DP) for x in rep["auroc_by_layer"]] == R111["auroc_by_layer"],
            "got " + " ".join(f"{x:.4f}" for x in rep["auroc_by_layer"]))
    d = [x for x in rep["cohens_d_by_layer"] if x is not None]
    log.add("Cohen's d is flat across the band at ~2.81-3.15",
            bool(d) and R111["cohens_d_band_lo"] - 0.02 <= min(d)
            and max(d) <= R111["cohens_d_band_hi"] + 0.02,
            f"min {min(d):.3f} max {max(d):.3f}" if d else "no d computed")
    return log


# ================================================================================ the export
def prepare(pr: Prereg, a) -> dict:
    """Load the split, verify every run, build the development arm at the primary dose."""
    import torch  # noqa: F401  (build_arm imports it too; fail here if it is missing)
    concepts = list(pr.require("population", "concepts"))
    if concepts[0] != TARGET:
        raise PreregError(f"population.concepts[0] is {concepts[0]!r}, expected {TARGET!r}")
    layer_grid = list(pr.require("read_site", "layer_grid"))
    dose = pr.require("population", "n_examples_primary")
    cw = pr.require("population", "codewords")["development"]

    ex = excluded_domains(pr)
    assign = load_split(pr)
    analysed = {d: s for d, s in assign.items() if d not in ex}
    train = sorted(d for d, s in analysed.items() if s == "train")
    valid = sorted(d for d, s in analysed.items() if s == "validation")
    test = sorted(d for d, s in analysed.items() if s == "test")
    for nm, dd in (("train", train), ("validation", valid), ("test", test)):
        _nonempty(dd, f"the {nm} split")
    if len(train) != pr.require("split", "n_train"):
        raise PreregError(f"{len(train)} analysed TRAIN domains, the preregistration says "
                          f"{pr.require('split', 'n_train')}. The direction's population is not "
                          f"the one that was frozen; refusing to fit.")
    if len(test) != pr.require("primary", "n_test_domains"):
        raise PreregError(f"{len(test)} test domains, preregistration says "
                          f"{pr.require('primary', 'n_test_domains')}")
    if set(train) & set(test) or set(train) & set(valid) or set(valid) & set(test):
        raise PreregError("DOMAIN LEAKAGE between splits")

    runs = {}
    for c in concepts:
        r = _find_run(a.reps, f"{a.tag_prefix}_{cw}_{c}")
        verify_run(pr, f"{cw}_{c}", r)
        runs[c] = os.path.basename(r)

    # keep_domains = every analysed domain: the TRAIN rows are needed for the `cell_means`
    # diagnostic block and the TEST rows for the reproduction. The DIRECTION is still fitted from
    # the TRAIN domain means alone -- keeping a row in memory is not the same as fitting on it,
    # and `check_payload` asserts the fit set separately.
    arm = build_arm(pr, a.reps, a.tag_prefix, cw, (dose,), ex, assign, set(analysed))

    pr048 = json.load(open(os.path.join(REPO, "configs/dcs_ts_pr048.json")))
    ctx = {
        "concepts": concepts, "layer_grid": layer_grid, "dose": dose, "codeword": cw,
        "train": train, "valid": valid, "test": test, "excluded": sorted(ex),
        "n_train": pr.require("split", "n_train"),
        "hidden": pr.require("model", "hidden"),
        "position": pr.require("read_site", "position"),
        "layer_convention": pr.require("read_site", "layer_convention"),
        "split_manifest_sha16": pr.require("split", "manifest_sha16"),
        "bank_rows_sha16_pr048": {k: v["bank_rows_sha16"]
                                  for k, v in pr048["population"]["banks"].items()},
        "runs": runs, "arm": arm,
        "prereg_sha256": _file_sha256(os.path.join(REPO, "configs/dcs_ts_pr053.json")),
    }
    if not ctx["bank_rows_sha16_pr048"]:
        raise PreregError("configs/dcs_ts_pr048.json declares NO banks; a bank binding over an "
                          "empty set binds nothing")
    return ctx


def build_payload(pr: Prereg, ctx: dict, fit_domains=None) -> dict:
    """The `--fit-dir` payload, in the format `score_behavior.py`'s loader reads."""
    import torch
    concepts, layers = ctx["concepts"], ctx["layer_grid"]
    dose, arm = ctx["dose"], ctx["arm"]
    Dm = {c: arm["Dmean"][(c, dose)] for c in concepts}
    fit = fit_directions(Dm, fit_domains if fit_domains is not None else ctx["train"], concepts)
    raw, tr = fit["raw"], fit["fit_domains"]

    payload, gap, norms, uni = {}, {}, {}, {}
    for name, v in raw.items():
        n = np.linalg.norm(v, axis=1)
        if float(n.min()) <= 1e-9:
            raise PreregError(f"{name} has a ZERO-NORM layer; projecting it out would be a no-op "
                              f"that scores as a perfectly healthy null")
        u = unit(v)
        uni[name] = u
        payload[name] = {int(L): torch.from_numpy(u[i].astype(np.float32))
                         for i, L in enumerate(layers)}
        gap[name] = {int(L): float(n[i]) for i, L in enumerate(layers)}
        norms[name] = [float(x) for x in n]

    # `cell_means` is a DIAGNOSTIC block, not part of the estimator: `score_behavior` uses it only
    # to record a realised dose (`cellmean_dose`, `cell_residual_frac_removed`). It is computed
    # over TRAIN rows of the DEVELOPMENT codeword's BOMB bank -- the population PHASE 9's primary
    # arm generates from -- and labelled as such. Cell A is byte-identical across the three banks
    # (R-111 gate V2: 3616/3616, max|diff| 0.000e+00), so "the" A mean is unambiguous.
    rows = arm["rows"]
    cell_means, n_per_cell = {}, {}
    for cell, concept in (("A", concepts[0]), ("C", concepts[0])):
        stack = [rows[(concept, dose)][d][cell] for d in tr
                 if d in rows[(concept, dose)] and cell in rows[(concept, dose)][d]]
        if not stack:
            raise PreregError(f"cell_means: ZERO train rows bound for cell {cell!r}")
        X = np.concatenate(stack, axis=0)
        n_per_cell[cell] = int(X.shape[0])
        m = X.mean(axis=0)
        cell_means[cell] = {int(L): torch.from_numpy(m[i].astype(np.float32))
                            for i, L in enumerate(layers)}
    # the per-concept C means, under names nothing auto-consumes, for the exploratory arms
    concept_cell_means = {}
    for c in concepts:
        stack = [rows[(c, dose)][d]["C"] for d in tr if d in rows[(c, dose)]]
        if not stack:
            raise PreregError(f"concept cell means: ZERO train rows bound for C_{c}")
        m = np.concatenate(stack, axis=0).mean(axis=0)
        concept_cell_means[c] = {int(L): torch.from_numpy(m[i].astype(np.float32))
                                 for i, L in enumerate(layers)}

    payload.update({
        "layers": [int(L) for L in layers],
        "layer_convention": ctx["layer_convention"],
        "gap": gap,
        "cell_means": cell_means,
        "n_per_cell": n_per_cell,
        "concept_cell_means_train": concept_cell_means,
    })
    payload["meta"] = {
        "artifact": "DCS-PR-053 directions, exported for DCS-PR-057 PHASE 9 blocker Q2",
        "produced_by": "scripts/dcs_ts_export_directions.py",
        "estimator_from": "scripts/dcs_ts_pr053_diffmeans.py (imported, not reimplemented)",
        "written_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "prereg": "configs/dcs_ts_pr053.json",
        "prereg_sha256": ctx["prereg_sha256"],
        "direction_names": sorted(raw),
        "definitions": {
            "v_c": "mean over TRAIN domains of [h(C_c) - h(A_shared)], PAIRED on family_id",
            "v_remap": "v_bomb -- the raw axis",
            "v_bomb_specific": "v_bomb - mean(v_knife, v_gun) -- the residualised identity axis",
            "v_knife_specific": "v_knife - mean(v_bomb, v_gun) -- PR-057 H3's target component",
            "_no_club": "club is NOT in the residual (configs/dcs_ts_pr053.json directions._no_club)",
            "_normalisation": "stored UNIT; the raw diff-of-means norm is in `gap` and `norms`",
        },
        "fit_domains": sorted(tr),
        "n_fit_domains": len(tr),
        "split": {"train": len(ctx["train"]), "validation": len(ctx["valid"]),
                  "test": len(ctx["test"])},
        "validation_domains": sorted(ctx["valid"]),
        "test_domains": sorted(ctx["test"]),
        "excluded_domains": sorted(ctx["excluded"]),
        "split_manifest": "data/boombness_prompts/dcs_ts116_domain_split.json",
        "split_manifest_sha16": ctx["split_manifest_sha16"],
        "layers": [int(L) for L in layers],
        "norms": norms,
        "codeword": ctx["codeword"],
        "n_examples": int(dose),
        "query_kind": pr.require("population", "query_kind_primary"),
        "position": ctx["position"],
        "model": pr.require("model", "hf_id"),
        "model_revision": pr.require("model", "revision"),
        "attn_impl": pr.require("model", "attn_impl"),
        "bank_rows_sha16": ctx["bank_rows_sha16_pr048"],
        "bank_sha_source": "configs/dcs_ts_pr048.json (identical to configs/dcs_ts_pr053.json)",
        "extraction_runs": ctx["runs"],
        "n_paired_families_per_concept": {c: int(arm["npairs"][(c, dose)]) for c in concepts},
        "cell_means_note": ("TRAIN rows of the DEVELOPMENT codeword's BOMB bank only, cells A and "
                            "C. Diagnostic: score_behavior uses it for realised-dose records "
                            "(cellmean_dose / cell_residual_frac_removed), never for the axis."),
        "content_sha256": content_sha256(uni, layers),
        "interpretation_warning": (
            "R-116: only BOMB installs (0.619 of 113 domains; knife 0.000, gun 0.009). "
            "v_bomb_specific is defined -- and was measured by R-111 -- as the residual over all "
            "three concepts, so the two SUBTRACTED terms come from demonstration sets that do not "
            "install. Projecting this axis out therefore removes the bomb remapping component "
            "MINUS an average of two non-installing contrasts; a null is not attributable to the "
            "identity content alone. See reports/DCS_TS_PHASE9_BLOCKERS_CLEARED.md section Q2."),
    }
    return payload


def write_artifact(payload: dict, out_dir: str, rep: dict, checks: CheckLog) -> str:
    import torch
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, PAYLOAD_NAME)
    torch.save(payload, path)
    man = {k: v for k, v in payload["meta"].items()}
    man["payload_file"] = PAYLOAD_NAME
    man["payload_sha256"] = _file_sha256(path)
    man["reproduction"] = {"published": R111,
                           "recomputed": {k: v for k, v in rep.items()
                                          if k != "per_domain_band_auroc"},
                           "per_domain_band_auroc": rep["per_domain_band_auroc"]}
    man["checks"] = checks.rows
    man["fit_dir_argument"] = os.path.relpath(out_dir, REPO)
    with open(os.path.join(out_dir, MANIFEST_NAME), "w") as f:
        json.dump(man, f, indent=2, sort_keys=False)
    return path


# ============================================================================== the mutations
def mutate(pr: Prereg, ctx: dict, out_dir: str) -> dict:
    """A check nobody has tried to break is a comment. Each mutation below is a specific way this
    artifact could be wrong; every one MUST turn at least one check RED."""
    import torch
    base_payload = build_payload(pr, ctx)
    layers = ctx["layer_grid"]
    results = []

    def _rt(p):
        """Round-trip through torch.save/load, so a mutation is checked on a LOADED payload --
        the same object PHASE 9 will see, not the in-memory one."""
        tmp = os.path.join(out_dir, "_mutation_scratch.pt")
        torch.save(p, tmp)
        try:
            return torch.load(tmp, map_location="cpu", weights_only=False)
        finally:
            os.remove(tmp)

    def case(name, mutated_payload=None, rep=None, refit_domains=None):
        log = CheckLog()
        try:
            if refit_domains is not None:
                mutated_payload = build_payload(pr, ctx, fit_domains=refit_domains)
            p = _rt(mutated_payload)
            check_payload(p, ctx, log)
            if rep is not None:
                check_reproduction(rep, log)
            red = len(log.red)
            err = None
        except Exception as e:                     # a loud failure is also RED, and is the point
            red, err = 1, f"{type(e).__name__}: {e}"
        results.append({"mutation": name, "n_checks_red": red,
                        "caught": red > 0, "raised": err,
                        "red_checks": [r["check"] for r in log.red] if not err else [],
                        # the REASON, not just the colour: the reviewer's bar is that a mutation
                        # goes red because of the check meant for it, and the detail string is
                        # where the measured residual behind that verdict is recorded.
                        "red_details": [{"check": r["check"], "detail": r["detail"]}
                                        for r in log.red] if not err else []})
        print(f"  {'RED  ' if red > 0 else 'GREEN'}  {name}"
              + (f"   [raised {err[:90]}]" if err else f"   [{red} check(s) red]"))

    def copy(p):
        import copy as _c
        return _c.deepcopy(p)

    # 1-3. TRAIN ONLY -- the property that matters most.
    case("fit on TRAIN + the 23 TEST domains (leakage)",
         refit_domains=sorted(set(ctx["train"]) | set(ctx["test"])))
    case("fit on the VALIDATION domains instead of TRAIN", refit_domains=list(ctx["valid"]))
    case("fit on TRAIN minus one domain (a silently shrunken population)",
         refit_domains=list(ctx["train"])[:-1])
    # 4. the fit-domain record lies about which domains were used
    p = copy(base_payload); p["meta"]["fit_domains"] = sorted(ctx["test"])
    case("meta.fit_domains rewritten to the TEST domains", p)
    # 5. the estimator's algebra
    p = copy(base_payload)
    p["v_bomb_specific"] = {L: p["v_bomb"][L].clone() for L in p["v_bomb"]}
    p["gap"]["v_bomb_specific"] = dict(p["gap"]["v_bomb"])
    case("v_bomb_specific replaced by the RAW v_bomb (no residualisation)", p)
    # 6. wrong residual coefficient (v_bomb - (v_knife + v_gun), i.e. mean -> sum)
    p = copy(base_payload)
    for i, L in enumerate(layers):
        raw = (p["v_bomb"][L].double() * p["gap"]["v_bomb"][L]
               - (p["v_knife"][L].double() * p["gap"]["v_knife"][L]
                  + p["v_gun"][L].double() * p["gap"]["v_gun"][L]))
        p["gap"]["v_bomb_specific"][L] = float(raw.norm())
        p["v_bomb_specific"][L] = (raw / raw.norm()).float()
    case("residual coefficient 1.0 instead of 0.5 (sum, not mean)", p)
    # 7. v_remap silently pointed at the residual axis
    p = copy(base_payload)
    p["v_remap"] = {L: p["v_bomb_specific"][L].clone() for L in p["v_bomb_specific"]}
    case("v_remap (control C3) pointed at v_bomb_specific instead of v_bomb", p)
    # 8. a single array perturbed below any visual tolerance
    p = copy(base_payload)
    p["v_bomb_specific"][layers[0]] = p["v_bomb_specific"][layers[0]] + 1e-4
    case("one layer of v_bomb_specific perturbed by 1e-4", p)
    # 9. a non-unit vector (add-dosing would silently double-count the norm)
    p = copy(base_payload)
    p["v_bomb_specific"][layers[3]] = p["v_bomb_specific"][layers[3]] * 2.0
    case("one layer of v_bomb_specific stored at twice unit norm", p)
    # 10. a zeroed layer -- project_out becomes a no-op that scores as a clean null
    p = copy(base_payload)
    p["v_bomb_specific"][layers[5]] = torch.zeros_like(p["v_bomb_specific"][layers[5]])
    p["gap"]["v_bomb_specific"][layers[5]] = 0.0
    case("one layer of v_bomb_specific ZEROED (project_out is a no-op there)", p)
    # 11. a missing layer
    p = copy(base_payload); p["v_bomb_specific"].pop(layers[-1])
    case("v_bomb_specific missing layer 14", p)
    # 12. the recorded content sha does not describe the arrays
    p = copy(base_payload); p["meta"]["content_sha256"] = "0" * 64
    case("meta.content_sha256 does not match the arrays", p)
    # 13. a wrong bank binding
    p = copy(base_payload)
    p["meta"]["bank_rows_sha16"] = dict(p["meta"]["bank_rows_sha16"])
    p["meta"]["bank_rows_sha16"]["button_bomb"] = "0" * 16
    case("bank_rows_sha16 disagrees with configs/dcs_ts_pr048.json", p)
    # 14. a wrong split manifest binding
    p = copy(base_payload); p["meta"]["split_manifest_sha16"] = "0" * 16
    case("split_manifest_sha16 disagrees with the frozen manifest", p)
    # 15. the layer grid quietly changes
    p = copy(base_payload); p["layers"] = [int(L) for L in layers[:-2]]
    case("payload layer list truncated to L6-12", p)
    # 16-18. the REPRODUCTION arm, mutated on the scoring side
    rows, dose, concepts = ctx["arm"]["rows"], ctx["dose"], ctx["concepts"]
    uspec = np.stack([base_payload["v_bomb_specific"][int(L)].double().numpy() for L in layers])
    case("scored with the SIGN-FLIPPED v_bomb_specific", base_payload,
         rep=score_identity_auroc(-uspec, rows, dose, ctx["test"], concepts))
    uraw = np.stack([base_payload["v_bomb"][int(L)].double().numpy() for L in layers])
    case("scored with v_bomb (R-111's contrast B, 0.8856) instead of v_bomb_specific",
         base_payload, rep=score_identity_auroc(uraw, rows, dose, ctx["test"], concepts))
    uk = np.stack([base_payload["v_knife_specific"][int(L)].double().numpy() for L in layers])
    case("scored with v_knife_specific (the wrong concept's axis)", base_payload,
         rep=score_identity_auroc(uk, rows, dose, ctx["test"], concepts))
    # 19. scored on VALIDATION rows, i.e. the wrong evaluation population
    case("reproduction scored on the VALIDATION domains, not TEST", base_payload,
         rep=score_identity_auroc(uspec, rows, dose, ctx["valid"], concepts))
    # 20. layer order shuffled -- every layer is present, none is right
    p = copy(base_payload)
    rot = {int(L): base_payload["v_bomb_specific"][int(layers[(i + 1) % len(layers)])].clone()
           for i, L in enumerate(layers)}
    p["v_bomb_specific"] = rot
    case("v_bomb_specific layers rotated by one (an off-by-one layer convention)", p,
         rep=score_identity_auroc(
             np.stack([rot[int(L)].double().numpy() for L in layers]),
             rows, dose, ctx["test"], concepts))

    # 21. THE ONE THAT MATTERS (F-1): the ARRAYS are fitted on TRAIN + the 23 TEST domains while
    #     `meta.fit_domains` still honestly reports the 67 TRAIN domains. Every metadata-reading
    #     TRAIN-only check stays GREEN on this payload -- so does the algebra check (the leaked
    #     residual is still v_bomb - mean(v_knife, v_gun)) and so does the content sha (recomputed
    #     from the leaked arrays). Only `check_train_only_recomputation` can see it.
    p = build_payload(pr, ctx, fit_domains=sorted(set(ctx["train"]) | set(ctx["test"])))
    p["meta"]["fit_domains"] = sorted(ctx["train"])
    p["meta"]["n_fit_domains"] = len(ctx["train"])
    case("arrays LEAKED (fitted on TRAIN+TEST) while meta.fit_domains still reports the "
         "67 TRAIN domains", p)
    # 22. the mirror: the ARRAYS are the honest TRAIN fit, the METADATA lies -- and lies subtly,
    #     swapping one TRAIN domain for one TEST domain so the COUNT still matches split.n_train.
    p = copy(base_payload)
    claimed = sorted(ctx["train"])[:-1] + [sorted(ctx["test"])[0]]
    p["meta"]["fit_domains"] = sorted(claimed)
    case("arrays honest, meta.fit_domains swaps one TRAIN domain for a TEST domain "
         "(count unchanged)", p)

    n_red = sum(1 for r in results if r["caught"])
    print(f"\n  MUTATIONS: {n_red}/{len(results)} turned at least one check RED.")
    if n_red != len(results):
        print("  A mutation that nothing catches is a hole in the verification, not a pass.")
    return {"n_mutations": len(results), "n_caught": n_red, "cases": results}


# ================================================================================== selftest
def selftest() -> int:
    """No data needed. Exercises the arithmetic and the failure modes of the checks themselves."""
    ok = [0, 0]

    def chk(cond, what):
        ok[1] += 1
        ok[0] += bool(cond)
        print(f"  [{'PASS' if cond else 'FAIL'}] {what}")

    rng = np.random.default_rng(0)
    Dm = {c: {f"d{i}": rng.normal(size=(3, 8)) for i in range(5)}
          for c in ("bomb", "knife", "gun")}
    f = fit_directions(Dm, [f"d{i}" for i in range(5)], ["bomb", "knife", "gun"])["raw"]
    chk(np.allclose(f["v_bomb_specific"], f["v_bomb"] - 0.5 * (f["v_knife"] + f["v_gun"])),
        "v_bomb_specific = v_bomb - mean(v_knife, v_gun)")
    chk(np.allclose(f["v_remap"], f["v_bomb"]), "v_remap = v_bomb")
    chk(np.allclose(f["v_knife_specific"], f["v_knife"] - 0.5 * (f["v_bomb"] + f["v_gun"])),
        "v_knife_specific = v_knife - mean(v_bomb, v_gun)")
    chk(np.allclose(f["v_bomb"], np.stack([Dm["bomb"][f"d{i}"] for i in range(5)]).mean(axis=0)),
        "v_c is the mean over fit domains of the per-domain paired difference")

    try:
        fit_directions(Dm, [], ["bomb", "knife", "gun"])
        chk(False, "a ZERO-domain fit raises")
    except PreregError:
        chk(True, "a ZERO-domain fit raises")
    try:
        fit_directions(Dm, ["d0", "d0"], ["bomb", "knife", "gun"])
        chk(False, "a duplicated fit domain raises")
    except PreregError:
        chk(True, "a duplicated fit domain raises")

    # AUROC path: a perfectly separating direction and an inert one
    layers = [6, 7]
    v = np.array([[1.0, 0.0], [1.0, 0.0]])
    rows = {("bomb", 4): {"t1": {"C": np.array([[[3.0, 0.0]] * 2, [[4.0, 0.0]] * 2])}},
            ("knife", 4): {"t1": {"C": np.array([[[0.0, 1.0]] * 2])}},
            ("gun", 4): {"t1": {"C": np.array([[[-1.0, 1.0]] * 2])}}}
    r = score_identity_auroc(v, rows, 4, ["t1"], ["bomb", "knife", "gun"])
    chk(abs(r["band_mean_auroc"] - 1.0) < 1e-12, "a separating direction scores AUROC 1.0")
    r2 = score_identity_auroc(-v, rows, 4, ["t1"], ["bomb", "knife", "gun"])
    chk(abs(r2["band_mean_auroc"] - 0.0) < 1e-12, "the flipped direction scores AUROC 0.0")
    try:
        score_identity_auroc(v, rows, 4, [], ["bomb", "knife", "gun"])
        chk(False, "a ZERO-domain reproduction raises")
    except PreregError:
        chk(True, "a ZERO-domain reproduction raises")
    try:
        score_identity_auroc(v, rows, 4, ["nope"], ["bomb", "knife", "gun"])
        chk(False, "a reproduction over domains with no rows raises")
    except PreregError:
        chk(True, "a reproduction over domains with no rows raises")

    # content sha is sensitive to a name swap as well as to the numbers
    a = {"x": np.ones((2, 3), dtype=np.float32), "y": np.zeros((2, 3), dtype=np.float32)}
    b = {"y": np.ones((2, 3), dtype=np.float32), "x": np.zeros((2, 3), dtype=np.float32)}
    chk(content_sha256(a, [6, 7]) != content_sha256(b, [6, 7]),
        "content sha distinguishes a NAME swap")
    c = {"x": np.ones((2, 3), dtype=np.float32) * (1 + 1e-6),
         "y": np.zeros((2, 3), dtype=np.float32)}
    chk(content_sha256(a, [6, 7]) != content_sha256(c, [6, 7]),
        "content sha distinguishes a 1e-6 array change")

    # the check log itself: empty == not ok
    L = CheckLog()
    chk(not L.ok, "a CheckLog that bound NO checks is not GREEN")
    L.add("x", True)
    chk(L.ok and not L.red, "a passing check is GREEN")
    L.add("y", False)
    chk(not L.ok and len(L.red) == 1, "a failing check is RED and makes the log not GREEN")

    # the reproduction check must reject a value that is merely close
    L2 = CheckLog()
    fake = {"n_test_domains": 23, "band_mean_auroc": 0.9700, "ci95": [0.96, 0.99],
            "between_domain_sd": 0.0347, "n_domains_above_chance": 23,
            "auroc_by_layer": R111["auroc_by_layer"], "cohens_d_by_layer": [3.0] * 9}
    check_reproduction(fake, L2)
    chk(len(L2.red) >= 1, "an AUROC of 0.9700 does NOT pass as 0.9764")

    # the TRAIN-only RECOMPUTATION check: honest arrays pass, leaked arrays go RED, and a lying
    # metadata field goes RED the other way. Built on a toy arm so no data is needed.
    toy_layers = [6, 7]
    toy_train = [f"d{i}" for i in range(4)]
    toy_all = toy_train + ["d4"]                          # d4 stands in for a TEST domain
    toy_Dm = {c: {d: rng.normal(size=(2, 8)) for d in toy_all} for c in ("bomb", "knife", "gun")}
    toy_ctx = {"concepts": ["bomb", "knife", "gun"], "layer_grid": toy_layers, "dose": 4,
               "train": list(toy_train),
               "arm": {"Dmean": {(c, 4): toy_Dm[c] for c in ("bomb", "knife", "gun")}}}

    def _toy_payload(fit_on):
        raw = fit_directions(toy_Dm, fit_on, toy_ctx["concepts"])["raw"]
        d = {n: unit(v) for n, v in raw.items()}
        gap = {n: {int(L): float(np.linalg.norm(raw[n][i]))
                   for i, L in enumerate(toy_layers)} for n in raw}
        return d, {"gap": gap, "meta": {"fit_domains": sorted(fit_on)}}

    d_ok, p_ok = _toy_payload(toy_train)
    L3 = CheckLog()
    check_train_only_recomputation(p_ok, dict(toy_ctx), d_ok, toy_layers, L3)
    chk(not L3.red, "recomputation check: an honest TRAIN fit is GREEN on both arms")

    d_leak, _ = _toy_payload(toy_all)                     # arrays leaked ...
    L4 = CheckLog()
    check_train_only_recomputation(p_ok, dict(toy_ctx), d_leak, toy_layers, L4)   # ... metadata honest
    chk(len(L4.red) == 1 and "RECOMPUTED" in L4.red[0]["check"],
        "recomputation check: LEAKED arrays + honest metadata go RED on the array arm")

    L5 = CheckLog()
    p_lie = {"gap": p_ok["gap"], "meta": {"fit_domains": sorted(toy_all)}}
    check_train_only_recomputation(p_lie, dict(toy_ctx), d_ok, toy_layers, L5)
    chk(len(L5.red) == 1 and "meta.fit_domains" in L5.red[0]["check"],
        "recomputation check: honest arrays + LYING metadata go RED on the domain-set arm")

    L6 = CheckLog()
    d_eps = {n: v.copy() for n, v in d_ok.items()}
    d_eps["v_bomb_specific"] = d_eps["v_bomb_specific"] + 2 * REFIT_ATOL
    check_train_only_recomputation(p_ok, dict(toy_ctx), d_eps, toy_layers, L6)
    chk(len(L6.red) == 1, f"recomputation check: a {2 * REFIT_ATOL:g} array shift is RED")
    chk(REFIT_ATOL > 5e-9 * 100 and REFIT_ATOL < 1.1e-2 / 100,
        "REFIT_ATOL sits between the float32 storage floor (5e-09) and a leaked fit (1.1e-02)")

    print(f"\n  selftest {ok[0]}/{ok[1]}")
    return 0 if ok[0] == ok[1] else 1


# ====================================================================================== main
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--prereg", default="configs/dcs_ts_pr053.json")
    ap.add_argument("--reps", default="outputs/boombness/extract_boombness")
    ap.add_argument("--tag-prefix", default="ts116m_full")
    ap.add_argument("--out", default=DEFAULT_OUT)
    ap.add_argument("--export", action="store_true", help="fit, verify and WRITE the artifact")
    ap.add_argument("--verify", action="store_true",
                    help="reload the written artifact from disk and re-run every check")
    ap.add_argument("--mutate", action="store_true", help="run the mutation harness")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not (a.export or a.verify or a.mutate):
        ap.error("choose --export, --verify, --mutate or --selftest")
    a.reps = a.reps if os.path.isabs(a.reps) else os.path.join(REPO, a.reps)
    out_dir = a.out if os.path.isabs(a.out) else os.path.join(REPO, a.out)

    # for_extraction=False: this file runs no forward passes. It reads an extraction PR-048 already
    # gated, exactly as scripts/dcs_ts_pr053_diffmeans.py does and for the same recorded reason.
    pr = load(a.prereg, for_extraction=False)

    import torch
    print("=" * 100)
    print("DCS-PR-057 PHASE 9 / Q2 -- exporting the PR-053 directions as a --fit-dir payload")
    print("=" * 100)
    ctx = prepare(pr, a)
    print(f"  codeword={ctx['codeword']}  n_examples={ctx['dose']}  layers={ctx['layer_grid']}")
    print(f"  split: train {len(ctx['train'])} / validation {len(ctx['valid'])} / "
          f"test {len(ctx['test'])}   excluded {ctx['excluded']}")
    print(f"  runs: {ctx['runs']}")

    rc = 0
    if a.export:
        payload = build_payload(pr, ctx)
        # score with the vector as it will be stored (float32, unit), before writing anything
        uspec = np.stack([payload["v_bomb_specific"][int(L)].double().numpy()
                          for L in ctx["layer_grid"]])
        rep = score_identity_auroc(uspec, ctx["arm"]["rows"], ctx["dose"], ctx["test"],
                                   ctx["concepts"])
        print("\n  REPRODUCTION of R-111's primary, from the direction about to be written:")
        print("    per-layer " + " ".join(f"{x:.4f}" for x in rep["auroc_by_layer"]))
        print(f"    band-mean {rep['band_mean_auroc']:.6f}  (published {R111['band_mean_auroc']})"
              f"  CI [{rep['ci95'][0]:.4f}, {rep['ci95'][1]:.4f}]"
              f"  sd {rep['between_domain_sd']:.4f}"
              f"  {rep['n_domains_above_chance']}/{rep['n_test_domains']} domains above chance")
        log = CheckLog()
        check_payload(payload, ctx, log)         # on the in-memory object
        check_reproduction(rep, log)
        print(f"\n  PRE-WRITE CHECKS ({len(log.rows)} checks: {len(log.rows) - len(log.red)} "
              f"GREEN, {len(log.red)} RED)")
        log.show()
        if log.red:
            print("\n  REFUSING TO WRITE. The direction does not reproduce the result it is "
                  "named after, or fails a binding check. Reporting the discrepancy is the "
                  "deliverable; shipping the file is not.")
            return 2
        path = write_artifact(payload, out_dir, rep, log)
        print(f"\n  wrote {os.path.relpath(path, REPO)}  "
              f"(sha256 {_file_sha256(path)[:16]}..., content sha "
              f"{payload['meta']['content_sha256'][:16]}...)")

    if a.verify:
        path = os.path.join(out_dir, PAYLOAD_NAME)
        if not os.path.exists(path):
            print(f"  no artifact at {path}; run --export first")
            return 2
        payload = torch.load(path, map_location="cpu", weights_only=False)
        uspec = np.stack([payload["v_bomb_specific"][int(L)].double().numpy()
                          for L in payload["layers"]])
        rep = score_identity_auroc(uspec, ctx["arm"]["rows"], ctx["dose"], ctx["test"],
                                   ctx["concepts"])
        log = CheckLog()
        check_payload(payload, ctx, log)
        check_reproduction(rep, log)
        print(f"\n  VERIFY (payload reloaded from disk) -- {len(log.rows)} checks")
        log.show()
        v = {"n_checks": len(log.rows),
             "n_checks_green": len(log.rows) - len(log.red), "n_checks_red": len(log.red),
             "verified_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
             "payload_file": PAYLOAD_NAME, "payload_sha256": _file_sha256(path),
             "content_sha256": payload["meta"]["content_sha256"],
             "reproduction": {k: val for k, val in rep.items() if k != "per_domain_band_auroc"},
             "published": R111, "checks": log.rows,
             "verdict": "GREEN" if log.ok else "RED"}
        with open(os.path.join(out_dir, VERIFY_NAME), "w") as f:
            json.dump(v, f, indent=2)
        print(f"  {v['n_checks_green']}/{v['n_checks']} checks GREEN, {v['n_checks_red']} RED")
        print(f"  verdict {v['verdict']} -> {os.path.relpath(os.path.join(out_dir, VERIFY_NAME), REPO)}")
        rc = rc or (0 if log.ok else 2)

    if a.mutate:
        print("\n  MUTATION HARNESS -- every case below MUST turn at least one check RED")
        m = mutate(pr, ctx, out_dir)
        mp = os.path.join(out_dir, "MUTATIONS.json")
        with open(mp, "w") as f:
            json.dump(m, f, indent=2)
        print(f"  -> {os.path.relpath(mp, REPO)}")
        rc = rc or (0 if m["n_caught"] == m["n_mutations"] else 3)

    if rc == 0:
        print(f"\n  PHASE 9 should pass:  --fit-dir {os.path.relpath(out_dir, REPO)}")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
