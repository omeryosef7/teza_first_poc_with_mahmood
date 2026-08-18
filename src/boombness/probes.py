"""probes.py — plan §6.3: a trained linear Boombness probe, and the test that matters.

CPU-only. Reads the cached final-occurrence representations written by `extract_boombness`
(`cache/final_occurrence_reps.pt`) and the bank, and trains a per-layer linear probe to
classify "is this target token concept-like or codeword-like".

THE STUPID-PROBE PROBLEM, AND WHY DATASET 4 IS THE ONLY ONE THAT ANSWERS THE QUESTION
------------------------------------------------------------------------------------
A probe trained to separate `bomb` tokens from `carrot` tokens will hit ~100% at layer 0 by
reading lexical identity off the embedding. That number is worthless: it says the tokenizer
works. The plan (§6.3) therefore asks for four datasets of increasing honesty, and this module
implements them as four TRAIN/TEST REGIMES over the same 2x2 bank:

  d1_simple        train and test on concept-surface (B,E) vs codeword-surface (A,C).
                   Expected to be near-ceiling and to prove nothing beyond lexical identity;
                   included because the plan asks for the comparison.
  d2_aligned       same, restricted to matched 2x2 families, so the only difference between
                   the classes is the target word.
  d3_hard_negative TRAIN on the easy diagonal A vs B only (benign carrot vs harmful bomb —
                   the very contrast the plan's naive B-A direction uses), then TEST on the
                   OFF-DIAGONAL hard cells: E = concept token in a benign context, C = codeword
                   token in a harmful context. A probe that learned CONCEPT-ness calls E
                   positive and C negative; a probe that learned HARM-CONTEXT-ness gets both
                   exactly backwards. Averaged accuracy hides that, so per-cell recall is
                   reported. This is the cleanest available separation of the two hypotheses.
  d4_heldout_ds    THE GENERALIZATION TEST. Train with cell C (natural doublespeak) REMOVED,
                   then ask the probe to score C. `mean P(concept | C)` versus its score on the
                   benign-literal control A is the learned-classifier analogue of the C-A
                   contrast in `analyze_boombness`, and it is the number the plan's hypothesis
                   actually predicts should be elevated.

SPLITTING. Train/test are split BY DOMAIN (and the bank's own dev/heldout demo-pool split is
respected), never by row, so a probe cannot memorize a template and score its twin. The domain
split is reported with every metric.

CONTROLS (plan §2.5). Every regime is also run with SHUFFLED LABELS; a shuffled-label AUROC
meaningfully above 0.5 means the split is leaking and the real number cannot be trusted.

THE NULL IS A DISTRIBUTION, NOT A DRAW (fixed 2026-08-18, external critique T9b)
-------------------------------------------------------------------------------
Until this fix the shuffled control drew ONE permutation per layer — `rng = RandomState(seed + L)`
inside the fold loop, which additionally re-seeded identically in every fold, so all folds of a
layer shared one permutation stream — and the single resulting AUROC was printed in a column headed
`shuf` next to the real number, i.e. presented as if it were a null BAND. It is a point. It carries
no draw-to-draw variance, so `auroc_lift = real - shuffled` inherited the full sampling noise of one
coin flip and every comparison against it understated the null's spread. This project had already
paid for this lesson once: the G4 steering band (retraction #7) measured a BETWEEN-DRAW sd of 0.0301
and the lesson was never propagated here.

The observable consequence is on the record. In `outputs/boombness/probes/g64full_20260818_120453_4183330/summary.json`
the single-draw shuffled AUROCs for `d5_surface_matched_codeword` are 0.5829 (L8), 0.6302 (L24),
0.5763 (L28) and 0.5812 (L31) — read by the external critique as a violation of this module's own
stopping rule at exactly those four layers. Those numbers are real, but one draw cannot distinguish
"the split leaks" from "a permutation happened to land 0.13 above chance", which is entirely ordinary
for a pooled AUROC over ~200 out-of-fold rows. The fix is to draw K >= 20 INDEPENDENT permutations
(seed derived from (seed, draw, layer, fold) so no two folds and no two draws share a stream) and to
report mean / sd / empirical quantiles / K, and to test the stopping rule against the null MEAN with
its standard error rather than against one draw. `--null-draws` sets K.

THE STOPPING RULE IS NOW ENFORCED IN CODE (2026-08-18)
------------------------------------------------------
The paragraph above states a stopping rule and, until this fix, nothing checked it: a run whose
shuffled control sat at 0.67 wrote DONE.json and printed its headline exactly like a clean one.
`check_leakage` now evaluates every (regime, layer) against `--leak-tol` (default 0.05 AUROC above
chance) using the null mean and a one-sided z on its standard error, records the verdict in
`summary.json["leak_check"]`, and — after the artifacts are written, so the evidence survives — exits
NON-ZERO with a loud banner unless `--allow-leak` is passed. `--allow-leak` is for deliberately
diagnosing a leak, never for reporting through one.

LAYER SELECTION MUST NOT BE DONE ON THE TEST SET (fixed 2026-08-18, external critique T6b)
------------------------------------------------------------------------------------------
`best_layer_by_auroc` used to be `argmax` of the per-layer TEST AUROC over the ~9-10 scanned layers,
and that layer's test AUROC was then reported as the result. That is selection on the outcome: the
maximum of ten noisy estimates is biased upward by an amount nobody had quantified, and the same
critique flags the identical shape in `g2_analysis_cwpos.json`. The keys are therefore renamed to
`best_layer_by_auroc_SELECTED_ON_TEST` / `best_layer_by_lift_SELECTED_ON_TEST` and carry
`n_layers_considered` so a reader can discount them, and they are NO LONGER the headline.

The headline is `nested_layer_selection`: for each outer domain fold the layer is chosen by an INNER
group-k-fold over the outer-training domains only, a probe is refit at that layer on the full outer
training set, and it is scored on the held-out fold. Pooling those out-of-fold predictions gives an
AUROC for the procedure "pick a layer, then apply it", with no test-set information in the choice.
The per-fold selected layers are reported too: disagreement between folds is itself the evidence
that the argmax was noise.
"""
from __future__ import annotations

import argparse
import collections
import json
import math
import os
import sys
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np
import torch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import DATA_DIR, FailureLedger, RunDir, read_jsonl, seed_everything, require_done  # noqa: E402

DEFAULT_BANK = os.path.join(DATA_DIR, "boombness_prompt_bank.jsonl")

CONCEPT_CELLS = {"B", "E"}      # target token IS the concept
CODEWORD_CELLS = {"A", "C"}     # target token IS the codeword


def load_reps(cache_path: str) -> Tuple[List[int], Dict[str, np.ndarray]]:
    payload = torch.load(cache_path, map_location="cpu", weights_only=False)
    layers = list(payload["layers"])
    reps = {k: v.float().numpy() for k, v in payload["reps"].items()}
    return layers, reps


def build_table(bank_rows: List[Dict], reps: Dict[str, np.ndarray]) -> List[Dict]:
    """One entry per prompt that has a cached rep and a labellable cell."""
    out = []
    for r in bank_rows:
        if r["prompt_id"] not in reps:
            continue
        if r["cell"] not in (CONCEPT_CELLS | CODEWORD_CELLS):
            continue
        out.append({
            "prompt_id": r["prompt_id"], "cell": r["cell"], "condition": r["condition"],
            "domain": r["domain"], "split": r["split"], "family_id": r["family_id"],
            "n_examples": r["n_examples"], "bank_block": r["bank_block"],
            "query_kind": r["query_kind"],
            "y": 1 if r["cell"] in CONCEPT_CELLS else 0,
        })
    return out


def domain_folds(rows: List[Dict], n_folds: int, seed: int) -> List[Tuple[List[str], List[str]]]:
    """Group-k-fold over DOMAIN, so train and test never share a domain."""
    domains = sorted({r["domain"] for r in rows})
    rng = np.random.RandomState(seed)
    order = list(domains)
    rng.shuffle(order)
    k = min(n_folds, len(order))
    folds = [order[i::k] for i in range(k)]
    return [(sorted(set(order) - set(f)), sorted(f)) for f in folds]


def fit_probe(X_tr: np.ndarray, y_tr: np.ndarray, seed: int, C: float = 1.0,
              n_components: int = 64):
    """Standardize -> (optional) PCA -> L2 logistic regression.

    WHY THE PCA STEP EXISTS. Each fold trains on ~576 examples in 4096 dimensions. At that
    ratio the two classes are almost surely linearly separable, so an ordinary logistic fit
    drives the margin to saturation: the pilot returned AUROC = 1.0000 at EVERY layer, with
    P(concept|A) and P(concept|C) both exactly 0.0 and their difference at 1e-33 — a perfect
    classifier that carries no graded information at all. Since the whole purpose of the probe
    here is the GRADED score `p_C_minus_p_A`, a saturated probe answers nothing, and the layer
    profile becomes a flat line of 1.0 that hides whatever structure exists.

    Reducing to `n_components` principal components (fit on the TRAINING fold only, so no
    leakage — PCA is unsupervised and never sees y) removes the separability, restores graded
    probabilities, and is the standard treatment for linear probes on high-dimensional
    activations. `n_components=0` disables it and reproduces the saturated full-dimensional
    behaviour, which is kept only so the saturation can be demonstrated rather than asserted.
    """
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler
    from sklearn.decomposition import PCA
    from sklearn.pipeline import make_pipeline
    steps = [StandardScaler(with_mean=True, with_std=True)]
    if n_components and n_components > 0:
        k = int(min(n_components, X_tr.shape[0] - 1, X_tr.shape[1]))
        if k >= 2:
            steps.append(PCA(n_components=k, random_state=seed))
    steps.append(LogisticRegression(max_iter=5000, C=C, random_state=seed))
    clf = make_pipeline(*steps)
    clf.fit(X_tr, y_tr)
    return clf


def score_metrics(y: np.ndarray, p: np.ndarray) -> Dict[str, float]:
    from sklearn.metrics import roc_auc_score, average_precision_score, accuracy_score, brier_score_loss
    out: Dict[str, float] = {"n": int(len(y)), "n_pos": int(y.sum())}
    if len(set(y.tolist())) < 2:
        out.update({"auroc": float("nan"), "auprc": float("nan"),
                    "accuracy": float("nan"), "brier": float("nan")})
        return out
    out["auroc"] = float(roc_auc_score(y, p))
    out["auprc"] = float(average_precision_score(y, p))
    out["accuracy"] = float(accuracy_score(y, (p >= 0.5).astype(int)))
    out["brier"] = float(brier_score_loss(y, p))
    # Fraction of predictions pinned to 0 or 1. A saturated probe can post a perfect AUROC
    # while its graded score carries no information, so this is reported next to it, always.
    out["saturation_frac"] = float(((p < 1e-6) | (p > 1 - 1e-6)).mean())
    return out


# LABEL BY REGIME (added 2026-08-17). Until now every regime used ONE label — cell in {B,E},
# i.e. "the target token IS the concept" — which is the SURFACE WORD. That label is perfectly
# decodable from the embedding layer, so d1-d4 all returned AUROC = 1.000 at EVERY layer including
# layer 0, in every regime, with shuffled controls near chance. Those 1.000s are not evidence that
# Boombness is linearly decodable; they are evidence that "bomb" and "carrot" have different
# embeddings, which was never in question. Note d3_hard_negative is affected too: its C-vs-E test
# set is also a carrot-vs-bomb contrast.
#
# The question the sprint actually asks needs the surface word HELD CONSTANT and the meaning varied:
#   d5_surface_matched_codeword  A vs C — both surface "carrot"; does the doublespeak context change
#                                the representation AT the codeword token?
#   d6_surface_matched_concept   E vs B — both surface "bomb"; does harmful context change it?
# These are the informative contrasts, and neither is decodable from the embedding by construction.
LABEL_POS = {
    "d5_surface_matched_codeword": {"C"},
    "d6_surface_matched_concept": {"B"},
}


def regime_label(regime: str, r: Dict) -> int:
    pos = LABEL_POS.get(regime)
    return (1 if r["cell"] in pos else 0) if pos else r["y"]


def regime_rows(table: List[Dict], regime: str) -> Tuple[List[Dict], List[Dict]]:
    """Return (train_pool, eval_pool) for a regime. eval_pool may extend train_pool."""
    if regime == "d1_simple":
        pool = list(table)
        return pool, pool
    if regime == "d2_aligned":
        pool = [r for r in table if r["bank_block"] == "core2x2"]
        return pool, pool
    if regime == "d3_hard_negative":
        # TRAIN on the easy, confounded contrast only — A (benign carrot) vs B (harmful bomb),
        # which is exactly the diagonal the plan's naive B-A direction uses — then TEST on the
        # OFF-DIAGONAL hard cells E and C.
        #
        # This is the decisive test, and it is why d3 is not just d2 with extra reporting (the
        # first draft returned the same pool for both, which made d3 a duplicate computation):
        #   a probe that learned CONCEPT-ness  calls E positive (concept token, benign context)
        #                                       and C negative (codeword token, harmful context);
        #   a probe that learned HARM-CONTEXT-ness gets both exactly BACKWARDS.
        # Averaged accuracy hides that; the per-cell recall reported below separates them.
        pool = [r for r in table if r["bank_block"] == "core2x2"]
        train = [r for r in pool if r["cell"] in ("A", "B")]
        test = [r for r in pool if r["cell"] in ("E", "C")]
        return train, test
    if regime == "d4_heldout_ds":
        pool = [r for r in table if r["bank_block"] == "core2x2"]
        train = [r for r in pool if r["cell"] != "C"]
        return train, pool
    if regime == "d5_surface_matched_codeword":
        pool = [r for r in table if r["bank_block"] == "core2x2" and r["cell"] in ("A", "C")]
        return pool, pool
    if regime == "d6_surface_matched_concept":
        pool = [r for r in table if r["bank_block"] == "core2x2" and r["cell"] in ("B", "E")]
        return pool, pool
    raise ValueError(f"unknown regime {regime!r}")


def shuffle_rng(seed: int, draw: int, layer: int, fold_idx: int) -> np.random.RandomState:
    """One INDEPENDENT permutation stream per (draw, layer, fold).

    The pre-fix code did `np.random.RandomState(seed + L)` INSIDE the fold loop, which means (a)
    every fold of a layer replayed the same stream and (b) there was only ever one draw, so the
    shuffled control had no draw-to-draw variance to report. Deriving the state from a SeedSequence
    over all four coordinates keeps the run reproducible while making the K draws genuinely
    independent of each other, of the layer, and of the fold.
    """
    ss = np.random.SeedSequence([int(seed), int(draw), int(layer), int(fold_idx)])
    return np.random.RandomState(int(ss.generate_state(1)[0]))


def run_regime(regime: str, table: List[Dict], reps: Dict[str, np.ndarray],
               layers: Sequence[int], layer_index: Dict[int, int], n_folds: int,
               seed: int, shuffle_labels: bool = False, C: float = 1.0,
               n_components: int = 64, emit_scores: Optional[dict] = None,
               null_draw: int = 0) -> Dict:
    """`emit_scores`, when a dict, collects OUT-OF-FOLD per-prompt margins keyed by
    (regime, layer, prompt_id). Plan §6.4 asks for `probe_boombness` as a third metric alongside
    `logit_lens_boombness` and `direction_boombness`, compared against ASR / refusal /
    comprehension / n_examples / role-style. That comparison needs a PER-PROMPT score, and this
    module previously emitted only per-regime aggregates, so `probe_boombness` was simply absent
    from the §6.4 table. The margin is used (not the probability) for the reason given below: the
    sigmoid saturates and cannot resolve a shift between two same-surface cells.

    These are out-of-fold scores from domain-grouped folds, so a prompt is always scored by a probe
    that never saw its domain."""
    train_pool, eval_pool = regime_rows(table, regime)
    folds = domain_folds(train_pool, n_folds, seed)
    per_layer: Dict[int, Dict] = {}

    for L in layers:
        li = layer_index[L]
        y_all, p_all, m_all, cell_all, cond_all = [], [], [], [], []
        for fold_idx, (tr_domains, te_domains) in enumerate(folds):
            tr = [r for r in train_pool if r["domain"] in tr_domains]
            te = [r for r in eval_pool if r["domain"] in te_domains]
            if not tr or not te:
                continue
            X_tr = np.stack([reps[r["prompt_id"]][li] for r in tr])
            y_tr = np.array([regime_label(regime, r) for r in tr])
            if shuffle_labels:
                # T9b fix: independent per (draw, layer, fold) — see shuffle_rng.
                y_tr = shuffle_rng(seed, null_draw, L, fold_idx).permutation(y_tr)
            if len(set(y_tr.tolist())) < 2:
                continue
            clf = fit_probe(X_tr, y_tr, seed, C=C, n_components=n_components)
            X_te = np.stack([reps[r["prompt_id"]][li] for r in te])
            p_te = clf.predict_proba(X_te)[:, 1]
            # The MARGIN (signed distance to the hyperplane) is the graded score, not the
            # probability. The sigmoid compresses everything on one side of a well-separated
            # boundary into p ~ 0, so P(concept|C) - P(concept|A) came back as +0.0000 even
            # after PCA removed the numerical saturation: both are codeword-surface rows, both
            # land far on the negative side, and the probability scale cannot resolve a shift
            # between them. The margin can, and it is the direct analogue of the cosine along
            # d_surface that analyze_boombness reports.
            m_te = clf.decision_function(X_te)
            y_all.extend(regime_label(regime, r) for r in te)
            p_all.extend(p_te.tolist())
            m_all.extend(np.asarray(m_te).ravel().tolist())
            cell_all.extend(r["cell"] for r in te)
            cond_all.extend(r["condition"] for r in te)
            if emit_scores is not None and not shuffle_labels:
                for r, mv, pv in zip(te, np.asarray(m_te).ravel().tolist(), p_te.tolist()):
                    emit_scores[(regime, L, r["prompt_id"])] = {
                        "regime": regime, "layer": L, "prompt_id": r["prompt_id"],
                        "cell": r["cell"], "condition": r["condition"], "domain": r["domain"],
                        "probe_margin": float(mv), "probe_p_concept": float(pv),
                        "label": int(regime_label(regime, r))}

        if not y_all:
            continue
        y = np.array(y_all); p = np.array(p_all)
        rec = score_metrics(y, p)
        # Per-cell mean predicted P(concept) — the quantity the plan's hypothesis is about.
        by_cell: Dict[str, Dict[str, float]] = {}
        for c in sorted(set(cell_all)):
            pp = np.array([v for v, cc in zip(p_all, cell_all) if cc == c])
            mm = np.array([v for v, cc in zip(m_all, cell_all) if cc == c])
            yy = np.array([v for v, cc in zip(y_all, cell_all) if cc == c])
            by_cell[c] = {
                "n": int(len(pp)),
                "mean_p_concept": float(pp.mean()),
                "mean_margin": float(mm.mean()),
                "sem_margin": float(mm.std(ddof=1) / math.sqrt(len(mm))) if len(mm) > 1 else float("nan"),
                "recall_at_0.5": float(((pp >= 0.5).astype(int) == yy).mean()),
            }
        rec["by_cell"] = by_cell
        # The learned-probe analogue of the C-A contrast, on the MARGIN scale.
        if "C" in by_cell and "A" in by_cell:
            rec["p_C_minus_p_A"] = by_cell["C"]["mean_p_concept"] - by_cell["A"]["mean_p_concept"]
            rec["margin_C_minus_A"] = by_cell["C"]["mean_margin"] - by_cell["A"]["mean_margin"]
            # Expressed as a fraction of the full codeword->concept margin gap, so it is
            # comparable across layers whose margins have different scales.
            if "B" in by_cell:
                span = by_cell["B"]["mean_margin"] - by_cell["A"]["mean_margin"]
                rec["margin_frac_C"] = (rec["margin_C_minus_A"] / span) if abs(span) > 1e-9 else float("nan")
        # d3 evaluates only on {E, C}; report the same movement there.
        if "C" in by_cell and "E" in by_cell and "A" not in by_cell:
            rec["margin_C_minus_E"] = by_cell["C"]["mean_margin"] - by_cell["E"]["mean_margin"]
            rec["recall_E"] = by_cell["E"]["recall_at_0.5"]
            rec["recall_C"] = by_cell["C"]["recall_at_0.5"]
        per_layer[L] = rec

    # SELECTED ON TEST — deliberately named so it cannot be quoted as a clean estimate.
    # This is the argmax of the per-layer TEST AUROC over `n_layers_considered` layers, i.e. the
    # maximum of that many noisy estimates, and it is upward-biased by an amount this function
    # cannot measure. It is retained because the full layer profile in `per_layer` is the honest
    # report and a reader wants to know where its peak is; the headline number is produced by
    # `nested_layer_selection` instead. See the module docstring (T6b).
    best = None
    cand = {L: v for L, v in per_layer.items()
            if not math.isnan(v.get("auroc", float("nan")))} if per_layer else {}
    if cand:
        best = max(cand, key=lambda L: cand[L]["auroc"])
    return {"regime": regime, "shuffled_labels": shuffle_labels, "C": C,
            "n_components": n_components, "null_draw": null_draw if shuffle_labels else None,
            "n_train_pool": len(train_pool), "n_eval_pool": len(eval_pool),
            "n_folds": len(folds), "per_layer": per_layer,
            "best_layer_by_auroc_SELECTED_ON_TEST": best,
            "n_layers_considered": len(cand),
            "selection_warning": (
                "best_layer_by_auroc_SELECTED_ON_TEST is the argmax of the TEST AUROC over "
                f"{len(cand)} layers with no validation split; it is optimistically biased and is "
                "NOT the headline. Use nested_layer_selection.")}


def shuffled_null_distribution(
        regime: str, table: List[Dict], reps: Dict[str, np.ndarray], layers: Sequence[int],
        layer_index: Dict[int, int], n_folds: int, seed: int, C: float = 1.0,
        n_components: int = 64, n_draws: int = 20,
        quantiles: Sequence[float] = (0.05, 0.5, 0.95)) -> Dict:
    """K INDEPENDENT shuffled-label runs -> a per-layer null DISTRIBUTION (T9b fix).

    Returns {"n_draws", "per_layer": {L: {mean, sd, se, quantiles, draws, ...}}, "draws": [...]}.
    `sd` is the between-draw sd — the quantity the single-draw control could not produce and the
    quantity retraction #7 (G4 steering band, between-draw sd 0.0301) says must be reported. `se`
    is sd/sqrt(K), the uncertainty on the null MEAN, which is what the leakage test uses: a leak
    displaces the whole null, a lucky permutation displaces one draw.
    """
    if n_draws < 1:
        raise ValueError("n_draws must be >= 1")
    per_draw: List[Dict] = []
    for d in range(n_draws):
        per_draw.append(run_regime(regime, table, reps, layers, layer_index, n_folds, seed,
                                   shuffle_labels=True, C=C, n_components=n_components,
                                   null_draw=d))
    per_layer: Dict[int, Dict] = {}
    for L in layers:
        vals = [dr["per_layer"][L]["auroc"] for dr in per_draw
                if L in dr["per_layer"] and not math.isnan(dr["per_layer"][L].get("auroc", float("nan")))]
        if not vals:
            continue
        a = np.asarray(vals, dtype=float)
        per_layer[L] = {
            "n_draws": int(a.size),
            "mean": float(a.mean()),
            "sd": float(a.std(ddof=1)) if a.size > 1 else float("nan"),
            "se": float(a.std(ddof=1) / math.sqrt(a.size)) if a.size > 1 else float("nan"),
            "min": float(a.min()), "max": float(a.max()),
            "quantiles": {f"q{q:g}": float(np.quantile(a, q)) for q in quantiles},
            "draws": [float(v) for v in a],
        }
    return {"regime": regime, "n_draws": n_draws, "requested_draws": n_draws,
            "quantiles_used": [float(q) for q in quantiles], "per_layer": per_layer,
            "single_draw_note": "mean/sd/quantiles are over independent permutations; a single "
                                "draw (the pre-2026-08-18 behaviour) is a point, not a band."}


def check_leakage(null_dist: Dict, tol: float = 0.05, z_crit: float = 2.0) -> Dict:
    """Enforce this module's own stopping rule: shuffled AUROC must not sit above chance.

    Pre-fix, the rule existed only as a sentence in the docstring; a run could post a shuffled
    control of 0.67 and still write DONE.json. It is tested on the null MEAN (over K draws) with a
    one-sided z on the mean's standard error, because a single draw above 0.5 is expected and
    uninformative. A layer is flagged only when BOTH the effect (mean - 0.5 > tol) and the
    significance (z > z_crit) fire, so K large enough to make se tiny cannot flag a 0.505 null and
    a single wild draw cannot flag anything at all.
    """
    layers_flagged, rows = [], []
    for L, v in sorted(null_dist.get("per_layer", {}).items()):
        excess = v["mean"] - 0.5
        se = v.get("se", float("nan"))
        z = (excess / se) if (isinstance(se, float) and se == se and se > 0) else float("nan")
        leak = bool(excess > tol and (z == z and z > z_crit))
        rows.append({"layer": L, "null_mean": v["mean"], "null_sd": v["sd"], "null_se": se,
                     "excess_over_chance": float(excess), "z": float(z), "n_draws": v["n_draws"],
                     "leak": leak})
        if leak:
            layers_flagged.append(L)
    return {"regime": null_dist.get("regime"), "tol": float(tol), "z_crit": float(z_crit),
            "n_draws": null_dist.get("n_draws"), "layers_flagged": layers_flagged,
            "leak": bool(layers_flagged), "per_layer": rows}


def _fit_score(regime: str, reps: Dict[str, np.ndarray], li: int, tr: List[Dict],
               te: List[Dict], seed: int, C: float, n_components: int):
    """Fit on `tr`, return (y_true, p_pos) on `te`. None if the fold is degenerate."""
    if not tr or not te:
        return None
    y_tr = np.array([regime_label(regime, r) for r in tr])
    if len(set(y_tr.tolist())) < 2:
        return None
    X_tr = np.stack([reps[r["prompt_id"]][li] for r in tr])
    clf = fit_probe(X_tr, y_tr, seed, C=C, n_components=n_components)
    X_te = np.stack([reps[r["prompt_id"]][li] for r in te])
    return np.array([regime_label(regime, r) for r in te]), clf.predict_proba(X_te)[:, 1]


def nested_layer_selection(regime: str, table: List[Dict], reps: Dict[str, np.ndarray],
                           layers: Sequence[int], layer_index: Dict[int, int], n_folds: int,
                           seed: int, C: float = 1.0, n_components: int = 64,
                           inner_folds: int = 2) -> Dict:
    """HONEST layer selection (T6b fix): choose the layer INSIDE the training folds.

    For each outer domain fold: run an inner group-k-fold over the outer-TRAINING domains only,
    score every candidate layer there, take the inner argmax, refit at that layer on the whole outer
    training set, and predict the held-out fold. Pooling those predictions gives the AUROC of the
    PROCEDURE "select a layer, then apply it" — the number `best_layer_by_auroc` was standing in for
    while quietly reading the answer off the test set.

    `selected_layers` is reported per outer fold on purpose: if the folds disagree, the argmax was
    noise and the selected-on-test peak was a coin toss dressed as a finding.
    """
    train_pool, eval_pool = regime_rows(table, regime)
    outer = domain_folds(train_pool, n_folds, seed)
    y_all, p_all, picks, fold_rows = [], [], [], []
    for oi, (tr_domains, te_domains) in enumerate(outer):
        tr_rows = [r for r in train_pool if r["domain"] in tr_domains]
        te_rows = [r for r in eval_pool if r["domain"] in te_domains]
        if not tr_rows or not te_rows:
            continue
        inner = domain_folds(tr_rows, inner_folds, seed + 1000 + oi)
        inner_auroc: Dict[int, float] = {}
        for L in layers:
            li = layer_index[L]
            iy, ip = [], []
            for itr_d, ite_d in inner:
                itr = [r for r in tr_rows if r["domain"] in itr_d]
                ite = [r for r in eval_pool if r["domain"] in ite_d and r["domain"] in tr_domains]
                got = _fit_score(regime, reps, li, itr, ite, seed, C, n_components)
                if got is None:
                    continue
                iy.extend(got[0].tolist()); ip.extend(got[1].tolist())
            if iy and len(set(iy)) > 1:
                inner_auroc[L] = score_metrics(np.array(iy), np.array(ip))["auroc"]
        cand = {L: v for L, v in inner_auroc.items() if not math.isnan(v)}
        if not cand:
            continue
        L_sel = max(cand, key=lambda L: cand[L])
        got = _fit_score(regime, reps, layer_index[L_sel], tr_rows, te_rows, seed, C, n_components)
        if got is None:
            continue
        y_all.extend(got[0].tolist()); p_all.extend(got[1].tolist())
        picks.append(L_sel)
        fold_rows.append({"outer_fold": oi, "test_domains": te_domains, "selected_layer": L_sel,
                          "inner_auroc_at_selected": float(cand[L_sel]),
                          "inner_auroc_profile": {int(k): float(v) for k, v in sorted(cand.items())},
                          "n_test": len(te_rows)})
    out = {"regime": regime, "n_outer_folds": len(outer), "inner_folds": inner_folds,
           "n_layers_considered": len(list(layers)),
           "selected_layers": picks,
           "selection_is_stable": bool(picks) and len(set(picks)) == 1,
           "folds": fold_rows,
           "note": "AUROC of the procedure (select layer on inner folds, apply to held-out fold). "
                   "No test-set information enters the layer choice."}
    if y_all and len(set(y_all)) > 1:
        out["pooled"] = score_metrics(np.array(y_all), np.array(p_all))
        out["auroc_nested"] = out["pooled"]["auroc"]
    else:
        out["pooled"] = None
        out["auroc_nested"] = float("nan")
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run", required=True, help="extract_boombness run dir (needs cache/)")
    ap.add_argument("--bank", default=DEFAULT_BANK)
    ap.add_argument("--layers", default="", help="comma list of BLOCK layers; default = every 2nd")
    ap.add_argument("--folds", type=int, default=3, help="group-k-fold over domains")
    ap.add_argument("--regimes", default="d1_simple,d2_aligned,d3_hard_negative,d4_heldout_ds,"
                                    "d5_surface_matched_codeword,d6_surface_matched_concept")
    ap.add_argument("--C", type=float, default=1.0, help="L2 inverse strength")
    ap.add_argument("--emit-scores", action="store_true",
                    help="also write probe_scores.jsonl with OUT-OF-FOLD per-prompt margins, "
                         "which is what plan §6.4's three-way metric comparison needs")
    ap.add_argument("--pca", type=int, default=64,
                    help="PCA components fit on the TRAIN fold only; 0 disables (and the probe "
                         "then saturates at this n/d ratio — see fit_probe)")
    ap.add_argument("--null-draws", type=int, default=20,
                    help="K independent label shuffles used to build the null DISTRIBUTION "
                         "(mean/sd/quantiles). K=1 reproduces the pre-2026-08-18 single-draw "
                         "control, which is a point and not a band — see the module docstring.")
    ap.add_argument("--leak-tol", type=float, default=0.05,
                    help="stopping rule: null-mean AUROC may not exceed 0.5 by more than this")
    ap.add_argument("--leak-z", type=float, default=2.0,
                    help="one-sided z on the null mean's standard error required to call a leak")
    ap.add_argument("--allow-leak", action="store_true",
                    help="do not exit non-zero when the stopping rule fires (diagnosis only; "
                         "output must not be reported)")
    ap.add_argument("--inner-folds", type=int, default=2,
                    help="inner group-k-fold used to SELECT the layer without touching the test "
                         "fold (see nested_layer_selection)")
    ap.add_argument("--seed", type=int, default=20260816)
    ap.add_argument("--tag", default="probe")
    ap.add_argument("--allow-partial", action="store_true",
                    help="analyse a run with no DONE.json (output must not be reported)")

    args = ap.parse_args()
    if args.run:
        require_done(args.run, allow_partial=args.allow_partial)
    seed_everything(args.seed)

    cache_path = os.path.join(args.run, "cache", "final_occurrence_reps.pt")
    if not os.path.exists(cache_path):
        raise SystemExit(f"no cached reps at {cache_path} (rerun extract without --no-cache-reps)")
    layers, reps = load_reps(cache_path)
    layer_index = {L: i for i, L in enumerate(layers)}
    want = ([int(x) for x in args.layers.split(",") if x.strip()]
            if args.layers else [L for L in layers if L % 2 == 0 or L == layers[-1]])
    want = [L for L in want if L in layer_index]

    bank = read_jsonl(args.bank)
    table = build_table(bank, reps)

    run = RunDir("probes", args, tag=args.tag)
    ledger = FailureLedger()
    missing = sum(1 for r in bank if r["cell"] in (CONCEPT_CELLS | CODEWORD_CELLS)
                  and r["prompt_id"] not in reps)
    for _ in range(missing):
        ledger.fail("no_cached_rep")
    for _ in range(len(table)):
        ledger.ok()

    print(f"[probe] {len(table)} labellable prompts "
          f"({collections.Counter(r['cell'] for r in table)}), layers {want[0]}..{want[-1]}, "
          f"{args.folds}-fold over domains, {missing} missing reps")

    results: Dict[str, Dict] = {}
    leak_checks: Dict[str, Dict] = {}
    leaked: List[str] = []
    score_sink = {} if args.emit_scores else None
    for regime in [r.strip() for r in args.regimes.split(",") if r.strip()]:
        real = run_regime(regime, table, reps, want, layer_index, args.folds, args.seed,
                          shuffle_labels=False, C=args.C, n_components=args.pca,
                          emit_scores=score_sink)
        null = shuffled_null_distribution(regime, table, reps, want, layer_index, args.folds,
                                          args.seed, C=args.C, n_components=args.pca,
                                          n_draws=args.null_draws)
        # Kept for continuity with the pre-fix artifacts: draw 0 of the same family. It is ONE
        # point of the distribution above and must never be quoted as the control on its own.
        shuf = run_regime(regime, table, reps, want, layer_index, args.folds, args.seed,
                          shuffle_labels=True, C=args.C, n_components=args.pca, null_draw=0)
        results[regime] = real
        results[regime + "_shuffled_single_draw_DO_NOT_QUOTE"] = shuf
        results[regime + "_null_distribution"] = null

        # HONEST layer selection (T6b): the layer is chosen inside the training folds.
        nested = nested_layer_selection(regime, table, reps, want, layer_index, args.folds,
                                        args.seed, C=args.C, n_components=args.pca,
                                        inner_folds=args.inner_folds)
        real["nested_layer_selection"] = nested

        # STOPPING RULE, ENFORCED.
        lk = check_leakage(null, tol=args.leak_tol, z_crit=args.leak_z)
        leak_checks[regime] = lk
        if lk["leak"]:
            leaked.append(regime)

        # PER-LAYER, REAL vs SHUFFLED AT THE SAME LAYER.
        # The pilot reported argmax-over-layers for the real arm and argmax-over-layers for the
        # shuffled arm and compared the two. Both are maxima of 9 noisy estimates, so both are
        # biased upward and the comparison is not a comparison — it is how a shuffled control
        # came back at 0.58-0.64 and looked like leakage. The honest quantity is the paired
        # per-layer difference, and the headline layer is chosen on THAT.
        paired = {}
        for L in real["per_layer"]:
            if L not in null["per_layer"]:
                continue
            a = real["per_layer"][L].get("auroc")
            nd = null["per_layer"][L]
            b = nd["mean"]
            if a is None or math.isnan(a) or math.isnan(b):
                continue
            draws = np.asarray(nd["draws"], dtype=float)
            rl = real["per_layer"][L]
            paired[L] = {"auroc_real": a,
                         # The null as a DISTRIBUTION (T9b). `auroc_shuffled` is now the MEAN of K
                         # draws, not one draw, and it never travels without sd/quantiles/K.
                         "auroc_shuffled": b, "auroc_lift": a - b,
                         "null_mean": b, "null_sd": nd["sd"], "null_se": nd["se"],
                         "null_n_draws": nd["n_draws"], "null_quantiles": nd["quantiles"],
                         "null_min": nd["min"], "null_max": nd["max"],
                         # One-sided empirical p: how often a shuffled draw matched the real number.
                         "p_perm_ge_real": float((draws >= a).mean()),
                         "z_vs_null": (float((a - b) / nd["sd"])
                                       if isinstance(nd["sd"], float) and nd["sd"] == nd["sd"]
                                       and nd["sd"] > 0 else float("nan")),
                         "above_null_q95": bool(a > nd["quantiles"].get("q0.95", float("inf"))),
                         "saturation_frac": rl.get("saturation_frac"),
                         "p_C_minus_p_A": rl.get("p_C_minus_p_A"),
                         "margin_C_minus_A": rl.get("margin_C_minus_A"),
                         "margin_frac_C": rl.get("margin_frac_C"),
                         "margin_C_minus_E": rl.get("margin_C_minus_E"),
                         "recall_E": rl.get("recall_E"), "recall_C": rl.get("recall_C")}
        real["paired_vs_shuffled"] = paired
        # STILL SELECTED ON TEST — the lift is computed from test-fold AUROCs, so its argmax is a
        # maximum over `len(paired)` noisy estimates exactly like the plain AUROC argmax was. It is
        # named accordingly and reported next to `n_layers_considered`; the headline is `nested`.
        best = max(paired, key=lambda L: paired[L]["auroc_lift"]) if paired else None
        real["best_layer_by_lift_SELECTED_ON_TEST"] = best
        real["n_layers_considered"] = len(paired)

        run.log_row({"regime": regime, "C": args.C, "n_components": args.pca,
                     "n_train_pool": real["n_train_pool"], "n_eval_pool": real["n_eval_pool"],
                     "best_layer_by_lift_SELECTED_ON_TEST": best,
                     "n_layers_considered": len(paired),
                     "auroc_nested_selection": nested.get("auroc_nested"),
                     "nested_selected_layers": nested.get("selected_layers"),
                     "null_draws": args.null_draws,
                     "leak_check": lk,
                     "paired_vs_shuffled": paired})

        print(f"  {regime}   [null: {args.null_draws} independent shuffles]")
        print(f"    {'L':>3} {'AUROC':>7} {'null_mu':>7} {'null_sd':>7} {'q95':>6} {'p_perm':>6} "
              f"{'sat':>5} {'margC-A':>9} {'fracC':>7} {'margC-E':>9} {'recE':>5} {'recC':>5}")
        for L in sorted(paired):
            v = paired[L]
            def f(k, w, p=4):
                x = v.get(k)
                return f"{x:>+{w}.{p}f}" if isinstance(x, float) and not math.isnan(x) else " " * (w - 1) + "-"
            # The full layer profile is printed in full, every layer, precisely so the peak is read
            # as a peak in a profile and not as "the" result.
            mark = " <-max(test)" if L == best else ""
            q95 = v["null_quantiles"].get("q0.95", float("nan"))
            sd = v["null_sd"]
            print(f"    {L:>3} {v['auroc_real']:>7.4f} {v['null_mean']:>7.4f} "
                  f"{sd:>7.4f} {q95:>6.3f} {v['p_perm_ge_real']:>6.3f} "
                  f"{v['saturation_frac']:>5.2f} {f('margin_C_minus_A', 9)} "
                  f"{f('margin_frac_C', 7, 3)} {f('margin_C_minus_E', 9)} "
                  f"{f('recall_E', 5, 2)} {f('recall_C', 5, 2)}{mark}")
        print(f"    max-AUROC layer SELECTED ON TEST over {len(paired)} layers "
              f"(biased, not the headline): L={real['best_layer_by_auroc_SELECTED_ON_TEST']}, "
              f"max-lift layer L={best}")
        print(f"    HEADLINE nested (layer chosen on inner folds): "
              f"AUROC={nested.get('auroc_nested'):.4f} "
              f"selected_layers={nested.get('selected_layers')} "
              f"stable={nested.get('selection_is_stable')}")
        if lk["leak"]:
            print(f"    !! STOPPING RULE VIOLATED at layers {lk['layers_flagged']} "
                  f"(null mean > 0.5 + {args.leak_tol})")

    summary = {
        "run_scored": os.path.abspath(args.run), "bank": args.bank,
        "n_labellable_prompts": len(table), "layers": want, "n_folds": args.folds,
        "cells": dict(collections.Counter(r["cell"] for r in table)),
        "domains": sorted({r["domain"] for r in table}),
        "results": results,
        "null_draws": args.null_draws,
        "leak_check": {"tol": args.leak_tol, "z_crit": args.leak_z,
                       "regimes_flagged": leaked, "by_regime": leak_checks,
                       "rule": "shuffled-label AUROC meaningfully above 0.5 means the split is "
                               "leaking; tested on the mean of --null-draws independent shuffles"},
        "note": "d4_heldout_ds is the generalization test: cell C is removed from training and "
                "then scored. p_C_minus_p_A is the learned-probe analogue of the C-A contrast.",
        "headline_note": "The headline per regime is results[<regime>]['nested_layer_selection']"
                         "['auroc_nested'] — the layer is selected on inner training folds. Keys "
                         "ending in _SELECTED_ON_TEST are argmaxes over n_layers_considered test "
                         "AUROCs and are optimistically biased.",
    }
    if score_sink is not None:
        sp = run.p("probe_scores.jsonl")
        with open(sp, "w") as f:
            for rec in score_sink.values():
                f.write(json.dumps(rec) + "\n")
        print(f"[probes] wrote {len(score_sink)} out-of-fold per-prompt scores -> {sp}")
        summary["probe_scores_rows"] = len(score_sink)

    run.finish(summary=summary, ledger=ledger)
    print(f"[probe] -> {run.path}")

    # STOPPING RULE, ENFORCED — after finish(), so the evidence is on disk before we abort.
    if leaked:
        banner = "=" * 78
        print(banner)
        print("STOPPING RULE VIOLATED — SHUFFLED-LABEL CONTROL IS ABOVE CHANCE")
        for rg in leaked:
            for row in leak_checks[rg]["per_layer"]:
                if row["leak"]:
                    print(f"  {rg} L{row['layer']}: null mean AUROC {row['null_mean']:.4f} "
                          f"(sd {row['null_sd']:.4f}, se {row['null_se']:.4f}, "
                          f"z={row['z']:.2f}, K={row['n_draws']}) "
                          f"exceeds 0.5 + {args.leak_tol}")
        print("The split is leaking; the real AUROCs in this run CANNOT be reported.")
        print(banner)
        if not args.allow_leak:
            return 2
        print("[probe] --allow-leak set: exiting 0 anyway. Output must not be reported.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
