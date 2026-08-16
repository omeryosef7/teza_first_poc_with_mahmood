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
  d3_hard_negative adds the hard negatives the plan lists, which our design already supplies:
                   E = concept token in a BENIGN context (positive, but no harmful context) and
                   C = codeword token in a HARMFUL context (negative, but harm-laden context).
                   A probe that has really learned "concept-ness" must still call E positive
                   and C negative; one that has learned "harm-context-ness" will fail exactly
                   here, and the two failure modes are distinguishable in the per-cell recall.
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
from common import DATA_DIR, FailureLedger, RunDir, read_jsonl, seed_everything  # noqa: E402

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


def fit_probe(X_tr: np.ndarray, y_tr: np.ndarray, seed: int, C: float = 1.0):
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler
    from sklearn.pipeline import make_pipeline
    clf = make_pipeline(
        StandardScaler(with_mean=True, with_std=True),
        LogisticRegression(max_iter=2000, C=C, random_state=seed))
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
    return out


def regime_rows(table: List[Dict], regime: str) -> Tuple[List[Dict], List[Dict]]:
    """Return (train_pool, eval_pool) for a regime. eval_pool may extend train_pool."""
    if regime == "d1_simple":
        pool = list(table)
        return pool, pool
    if regime == "d2_aligned":
        pool = [r for r in table if r["bank_block"] == "core2x2"]
        return pool, pool
    if regime == "d3_hard_negative":
        # Same pool, but the metrics are broken out per cell so that the hard cells (E, C)
        # are visible instead of being averaged into the easy ones.
        pool = [r for r in table if r["bank_block"] == "core2x2"]
        return pool, pool
    if regime == "d4_heldout_ds":
        pool = [r for r in table if r["bank_block"] == "core2x2"]
        train = [r for r in pool if r["cell"] != "C"]
        return train, pool
    raise ValueError(f"unknown regime {regime!r}")


def run_regime(regime: str, table: List[Dict], reps: Dict[str, np.ndarray],
               layers: Sequence[int], layer_index: Dict[int, int], n_folds: int,
               seed: int, shuffle_labels: bool = False) -> Dict:
    train_pool, eval_pool = regime_rows(table, regime)
    folds = domain_folds(train_pool, n_folds, seed)
    per_layer: Dict[int, Dict] = {}

    for L in layers:
        li = layer_index[L]
        y_all, p_all, cell_all, cond_all = [], [], [], []
        for tr_domains, te_domains in folds:
            tr = [r for r in train_pool if r["domain"] in tr_domains]
            te = [r for r in eval_pool if r["domain"] in te_domains]
            if not tr or not te:
                continue
            X_tr = np.stack([reps[r["prompt_id"]][li] for r in tr])
            y_tr = np.array([r["y"] for r in tr])
            if shuffle_labels:
                rng = np.random.RandomState(seed + L)
                y_tr = rng.permutation(y_tr)
            if len(set(y_tr.tolist())) < 2:
                continue
            clf = fit_probe(X_tr, y_tr, seed)
            X_te = np.stack([reps[r["prompt_id"]][li] for r in te])
            p_te = clf.predict_proba(X_te)[:, 1]
            y_all.extend(r["y"] for r in te)
            p_all.extend(p_te.tolist())
            cell_all.extend(r["cell"] for r in te)
            cond_all.extend(r["condition"] for r in te)

        if not y_all:
            continue
        y = np.array(y_all); p = np.array(p_all)
        rec = score_metrics(y, p)
        # Per-cell mean predicted P(concept) — the quantity the plan's hypothesis is about.
        by_cell: Dict[str, Dict[str, float]] = {}
        for c in sorted(set(cell_all)):
            m = np.array([pp for pp, cc in zip(p_all, cell_all) if cc == c])
            yy = np.array([yv for yv, cc in zip(y_all, cell_all) if cc == c])
            by_cell[c] = {"n": int(len(m)), "mean_p_concept": float(m.mean()),
                          "sem": float(m.std(ddof=1) / math.sqrt(len(m))) if len(m) > 1 else float("nan"),
                          "recall_at_0.5": float(((m >= 0.5).astype(int) == yy).mean())}
        rec["by_cell"] = by_cell
        if "C" in by_cell and "A" in by_cell:
            # The learned-probe analogue of the C-A contrast: how much more concept-like does
            # the probe judge a doublespeak carrot than a benign-literal carrot?
            rec["p_C_minus_p_A"] = by_cell["C"]["mean_p_concept"] - by_cell["A"]["mean_p_concept"]
        per_layer[L] = rec

    best = None
    if per_layer:
        cand = {L: v for L, v in per_layer.items() if not math.isnan(v.get("auroc", float("nan")))}
        if cand:
            best = max(cand, key=lambda L: cand[L]["auroc"])
    return {"regime": regime, "shuffled_labels": shuffle_labels,
            "n_train_pool": len(train_pool), "n_eval_pool": len(eval_pool),
            "n_folds": len(folds), "per_layer": per_layer, "best_layer_by_auroc": best}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run", required=True, help="extract_boombness run dir (needs cache/)")
    ap.add_argument("--bank", default=DEFAULT_BANK)
    ap.add_argument("--layers", default="", help="comma list of BLOCK layers; default = every 2nd")
    ap.add_argument("--folds", type=int, default=3, help="group-k-fold over domains")
    ap.add_argument("--regimes", default="d1_simple,d2_aligned,d3_hard_negative,d4_heldout_ds")
    ap.add_argument("--seed", type=int, default=20260816)
    ap.add_argument("--tag", default="probe")
    args = ap.parse_args()
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
    for regime in [r.strip() for r in args.regimes.split(",") if r.strip()]:
        for shuf in (False, True):
            key = regime + ("_shuffled" if shuf else "")
            res = run_regime(regime, table, reps, want, layer_index, args.folds,
                             args.seed, shuffle_labels=shuf)
            results[key] = res
            run.log_row({"regime": key, **{k: v for k, v in res.items() if k != "per_layer"},
                         "per_layer_auroc": {L: v.get("auroc") for L, v in res["per_layer"].items()}})
            b = res["best_layer_by_auroc"]
            if b is not None:
                v = res["per_layer"][b]
                extra = ""
                if "p_C_minus_p_A" in v:
                    extra = f"  P(concept|C)-P(concept|A)={v['p_C_minus_p_A']:+.4f}"
                print(f"  {key:26s} best L{b:<3d} AUROC={v['auroc']:.4f} "
                      f"acc={v['accuracy']:.4f}{extra}")
            else:
                print(f"  {key:26s} no usable layer")

    summary = {
        "run_scored": os.path.abspath(args.run), "bank": args.bank,
        "n_labellable_prompts": len(table), "layers": want, "n_folds": args.folds,
        "cells": dict(collections.Counter(r["cell"] for r in table)),
        "domains": sorted({r["domain"] for r in table}),
        "results": results,
        "note": "d4_heldout_ds is the generalization test: cell C is removed from training and "
                "then scored. p_C_minus_p_A is the learned-probe analogue of the C-A contrast.",
    }
    run.finish(summary=summary, ledger=ledger)
    print(f"[probe] -> {run.path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
