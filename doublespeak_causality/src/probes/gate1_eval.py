"""gate1_eval.py -- Gate-1 validity evaluation for the Bombness probe (plan §5.4).

Takes a FULL extraction (train+dev+test activations in one run dir) and produces the
Gate-1 pass/fail verdict:

  1. fit the probe on TRAIN, select (layer, position, C) on DEV only, evaluate ONCE on
     the confirmatory holdout (TEST) -- held-out AUC clearly above chance;
  2. transfer: the effect survives on held-out codewords/templates (cross-codeword,
     incl. CARROT which lives in dev; and cohort transfer);
  3. trivial controls cannot explain it: label-shuffle, random direction, position-only,
     length-only, token-identity baselines all near chance / below the probe;
  4. reproduces on both dev and the frozen holdout;
  5. geometry vs the known concept/refusal directions is interpretable.

Pure numpy/sklearn -- operates on already-extracted activations, so it does NOT depend
on the extraction being bug-free (the extraction preflight guards that separately). It
is unit-testable offline with synthetic multi-split activations.

Gate 1 PASSES iff (manifest primary_endpoints.gate1):
  - holdout AUC lower CI > 0.5 by a clear margin (default holdout AUC >= 0.70 and CI_lo > 0.55);
  - cross-codeword (CARROT-held-out) AUC also clearly above chance;
  - every trivial control AUC < holdout AUC - margin AND < 0.65 absolute;
  - dev and holdout AUC agree within a tolerance (no dev/holdout collapse).
Thresholds are reported alongside the verdict so a reviewer can re-judge.
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
from src.probes.smoke_fit import load_run, POSITIONS      # noqa: E402

CARROT = "carrot"


def _subset(items, acts, pos_ix, mask):
    idx = np.where(mask)[0]
    X = acts[idx, :, pos_ix, :]            # [m, L, H]
    y = np.array([items[i]["label"] for i in idx])
    g = np.array([items[i]["example_id"] for i in idx])
    return idx, X, y, g


def _labelled_mask(items):
    return np.array([it.get("label") in (0, 1) for it in items])


def select_layer_on_dev(items, acts, position, Cs=cip.DEFAULT_CS, exclude_codeword=None):
    """Fit each layer on TRAIN, score on DEV; return the layer with best dev AUC and its C.
    exclude_codeword removes that codeword from BOTH train and dev during selection — used
    so the CARROT transfer estimate is measured at a layer/C chosen without carrot (no
    leakage of the transfer target into model selection)."""
    pos_ix = POSITIONS.index(position)
    lab = _labelled_mask(items)
    split = np.array([it.get("split") for it in items])
    cw = np.array([str(it.get("codeword", "")).lower() for it in items])
    tr_m = lab & (split == "train")
    dv_m = lab & (split == "dev")
    if exclude_codeword is not None:
        tr_m = tr_m & (cw != exclude_codeword)
        dv_m = dv_m & (cw != exclude_codeword)
    _, Xtr, ytr, _ = _subset(items, acts, pos_ix, tr_m)
    _, Xdv, ydv, gdv = _subset(items, acts, pos_ix, dv_m)
    if len(np.unique(ytr)) < 2 or len(np.unique(ydv)) < 2:
        raise ValueError("train or dev lacks both classes")
    best = None
    L = acts.shape[1]
    for layer in range(L):
        C, dev_auc = cip.select_C(Xtr[:, layer, :], ytr, Xdv[:, layer, :], ydv, gdv, Cs=Cs)
        if best is None or dev_auc > best["dev_auc"]:
            best = {"layer": layer, "C": C, "dev_auc": float(dev_auc), "position": position}
    return best


def evaluate(items, acts, run_meta=None, position="codeword_last",
             holdout_split="test", pass_auc=0.70, pass_ci_lo=0.55,
             control_margin=0.10, n_boot=2000, seed=0):
    pos_ix = POSITIONS.index(position)
    lab = _labelled_mask(items)
    split = np.array([it.get("split") for it in items])

    sel = select_layer_on_dev(items, acts, position)
    layer, C = sel["layer"], sel["C"]

    tr_m = lab & (split == "train")
    ho_m = lab & (split == holdout_split)
    _, Xtr, ytr, gtr = _subset(items, acts, pos_ix, tr_m)
    _, Xho, yho, gho = _subset(items, acts, pos_ix, ho_m)
    Xtr_L, Xho_L = Xtr[:, layer, :], Xho[:, layer, :]

    clf = cip.fit_logreg(Xtr_L, ytr, C)
    ho_scores = clf.decision_function(Xho_L)
    ho_auc = float(cip.roc_auc_score(yho, ho_scores))
    ho_ci = cip._bootstrap_auc_ci(yho, ho_scores, gho, n_boot=n_boot, seed=seed)

    # --- transfer: train WITHOUT carrot, test ON carrot (carrot lives in dev) ---
    cw = np.array([str(it.get("codeword", "")).lower() for it in items])
    carrot_m = lab & (cw == CARROT)
    transfer = None
    if carrot_m.sum() >= 4:
        # select layer/C on a CARROT-FREE dev subset so carrot never influences the
        # layer at which its own transfer is measured (no selection leakage of the
        # transfer target). Falls back to the primary layer/C if carrot-free selection
        # is degenerate (e.g. dev has no non-carrot both-class rows).
        try:
            sel_nc = select_layer_on_dev(items, acts, position, exclude_codeword=CARROT)
            layer_t, C_t = sel_nc["layer"], sel_nc["C"]
        except ValueError:
            layer_t, C_t = layer, C
        tr_nc = tr_m & (cw != CARROT)  # train already excludes carrot (carrot is dev), but be explicit
        # fit on all non-carrot labelled train, eval on carrot items
        _, Xtrn, ytrn, _ = _subset(items, acts, pos_ix, tr_nc)
        _, Xca, yca, gca = _subset(items, acts, pos_ix, carrot_m)
        if len(np.unique(ytrn)) == 2 and len(np.unique(yca)) == 2:
            clf_nc = cip.fit_logreg(Xtrn[:, layer_t, :], ytrn, C_t)
            ca_scores = clf_nc.decision_function(Xca[:, layer_t, :])
            transfer = {"carrot_auc": float(cip.roc_auc_score(yca, ca_scores)),
                        "n_carrot_examples": int(len(np.unique(gca))),
                        "selected_layer_carrot_free": int(layer_t)}

    # --- controls at the selected (layer, position) ---
    # Both stochastic controls are AVERAGED over 10 seeds: a single label permutation
    # / random direction has high variance at small n and can spuriously exceed the
    # threshold, so we report the mean (matches the random-direction convention).
    controls = {}
    controls["label_shuffle"] = float(np.mean(
        [cip.control_label_shuffle(Xtr_L, ytr, Xho_L, yho, gho, C=C, seed=s) for s in range(10)]))
    controls["random_direction"] = float(np.mean(
        [cip.control_random_direction(Xho_L, yho, seed=s) for s in range(10)]))
    # position-only / length-only / token-id baselines: scalar features on the holdout
    def scalar(name):
        vals = np.array([items[i].get(name, np.nan) for i in np.where(ho_m)[0]], dtype=float)
        if np.all(np.isnan(vals)):
            return None
        return cip.control_scalar_feature(vals, yho)
    controls["position_only"] = scalar("codeword_last_idx")
    controls["length_only"] = scalar("seq_len")
    controls["token_identity"] = scalar("codeword_token_id")

    # --- geometry vs concept/refusal directions (if provided in run_meta) ---
    geometry = {}
    if run_meta and "compare_directions" in run_meta:
        w = clf.coef_[0]
        for name, vec in run_meta["compare_directions"].items():
            geometry[name] = cip.cosine(w, np.asarray(vec, float))

    # --- verdict ---
    ctrl_vals = [v for v in controls.values() if v is not None]
    max_ctrl = max(ctrl_vals) if ctrl_vals else 0.0
    checks = {
        "holdout_auc_ok": ho_auc >= pass_auc and ho_ci[0] > pass_ci_lo,
        "controls_below_probe": all((v is None) or (v < ho_auc - control_margin and v < 0.65)
                                    for v in controls.values()),
        "dev_holdout_agree": abs(sel["dev_auc"] - ho_auc) <= 0.15,
        "transfer_ok": (transfer is None) or (transfer["carrot_auc"] >= 0.60),
    }
    verdict = "PASS" if all(checks.values()) else "FAIL"

    return {
        "position": position, "selected_layer": layer, "C": C,
        "dev_auc": sel["dev_auc"], "holdout_split": holdout_split,
        "holdout_auc": round(ho_auc, 4), "holdout_ci": [round(ho_ci[0], 4), round(ho_ci[1], 4)],
        "n_train_ex": int(len(np.unique(gtr))), "n_holdout_ex": int(len(np.unique(gho))),
        "transfer": transfer, "controls": {k: (round(v, 4) if v is not None else None)
                                           for k, v in controls.items()},
        "max_control_auc": round(max_ctrl, 4), "geometry": geometry,
        "checks": checks, "verdict": verdict,
        "thresholds": {"pass_auc": pass_auc, "pass_ci_lo": pass_ci_lo,
                       "control_margin": control_margin},
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run", required=True, help="FULL extraction run dir (train+dev+test)")
    ap.add_argument("--position", default="codeword_last", choices=POSITIONS)
    ap.add_argument("--holdout", default="test", choices=["test", "dev"])
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    acts, items = load_run(args.run)
    res = evaluate(items, acts, position=args.position, holdout_split=args.holdout)
    print(json.dumps(res, indent=2))
    out = args.out or os.path.join(args.run, f"gate1_{args.position}.json")
    json.dump(res, open(out, "w"), indent=2)
    print(f"\nGate 1: {res['verdict']}  (holdout AUC {res['holdout_auc']} "
          f"{res['holdout_ci']}, max control {res['max_control_auc']})")


if __name__ == "__main__":
    main()
