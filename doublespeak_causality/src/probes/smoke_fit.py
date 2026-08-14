"""smoke_fit.py -- pipeline sanity check for the Bombness probe (plan §2A.5).

Loads an extraction run dir (acts.npy + items.jsonl), fits the probe per layer at the
query-codeword position on a grouped split of whatever examples are present, and reports
per-layer held-out AUC. This is a MECHANICS check ("the pipeline runs end to end and the
signal is decodable"), NOT the Gate-1 validity result -- that needs the full train/dev/
holdout run with all controls (plan §5.4).

Pure numpy/sklearn; the load+fit logic is unit-testable with a synthetic run dir.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", ".."))
from src.probes import contextual_identity_probe as cip  # noqa: E402

POSITIONS = ("codeword_last", "final_prompt")


def load_run(run_dir):
    acts = np.load(os.path.join(run_dir, "acts.npy"))
    items = [json.loads(l) for l in open(os.path.join(run_dir, "items.jsonl"))]
    if acts.shape[0] != len(items):
        raise ValueError(f"acts/items mismatch: {acts.shape[0]} vs {len(items)}")
    return acts, items


def grouped_halves(groups, seed=0):
    """Split unique example ids into two disjoint halves (train / eval)."""
    uniq = sorted(set(groups))
    rng = np.random.default_rng(seed)
    rng.shuffle(uniq)
    cut = len(uniq) // 2
    tr = set(uniq[:cut]); ev = set(uniq[cut:])
    return tr, ev


def fit_per_layer(acts, items, position="codeword_last", seed=0):
    """Return list of dicts {layer, auc, n_train_ex, n_eval_ex} for the labelled items
    at `position`, using a grouped half/half split. Skips if a class or split is empty."""
    pos_ix = POSITIONS.index(position)
    labelled = [(i, it) for i, it in enumerate(items) if it.get("label") in (0, 1)]
    if not labelled:
        return []
    idx = np.array([i for i, _ in labelled])
    y = np.array([it["label"] for _, it in labelled])
    groups = np.array([it["example_id"] for _, it in labelled])
    tr_g, ev_g = grouped_halves(groups, seed=seed)
    tr = np.array([g in tr_g for g in groups])
    ev = ~tr
    if len(np.unique(y[tr])) < 2 or len(np.unique(y[ev])) < 2:
        return [{"error": "a split lacks both classes (slice too small/single-split)"}]
    n_layers = acts.shape[1]
    out = []
    # Fixed C on purpose: this is a mechanics check, so we do NOT tune C on the eval
    # slice (that would inflate AUC). Gate-1 tunes C on a real dev split (plan §3.5).
    C = 1.0
    for L in range(n_layers):
        X = acts[idx, L, pos_ix, :].astype(np.float64)
        clf = cip.fit_logreg(X[tr], y[tr], C)
        auc = float(cip.roc_auc_score(y[ev], clf.decision_function(X[ev])))
        out.append({"layer": L, "position": position, "auc": round(auc, 4), "C": C,
                    "n_train_ex": len(tr_g), "n_eval_ex": len(ev_g)})
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run", required=True, help="extraction run dir")
    ap.add_argument("--position", default="codeword_last", choices=POSITIONS)
    args = ap.parse_args()

    acts, items = load_run(args.run)
    print(f"[smoke] {acts.shape[0]} items, acts shape {list(acts.shape)}")
    rows = fit_per_layer(acts, items, position=args.position)
    if rows and "error" in rows[0]:
        print(f"[smoke] {rows[0]['error']}  -- mechanics OK, need a multi-split slice for AUC")
        json.dump({"status": "mechanics_only", "reason": rows[0]["error"]},
                  open(os.path.join(args.run, "smoke_fit.json"), "w"))
        return
    best = max(rows, key=lambda r: r["auc"])
    for r in rows:
        bar = "#" * int(r["auc"] * 40)
        print(f"  L{r['layer']:2d} {args.position:12s} AUC {r['auc']:.3f} {bar}")
    print(f"[smoke] best: L{best['layer']} AUC {best['auc']:.3f} "
          f"(train {best['n_train_ex']} / eval {best['n_eval_ex']} examples)")
    json.dump({"status": "ok", "position": args.position, "best": best, "per_layer": rows},
              open(os.path.join(args.run, "smoke_fit.json"), "w"), indent=2)


if __name__ == "__main__":
    main()
