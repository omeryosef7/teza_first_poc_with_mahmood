"""Phase-17 §21 detector length-confound control (for logistic/MLP, not just Fisher).

The Phase-6 confound control (`scripts/phase6_confound_control.py`) length-controlled only the FISHER
difference-of-means direction (residualized ≈0.75). The Phase-17 report also reports LOGISTIC and MLP
detectors (≈0.917 / 0.925), whose length-dependence was untested — this closes that gap.

For each requested (detector, position, layer) cell it computes the detector's grouped leave-one-goal-out
OUT-OF-FOLD probability per row, then treats that OOF probability as the 1-D "signal" and reuses the
phase-6 confound machinery on it:
  raw_auc         AUC(oof_prob → success)                 (= the detector's own OOF AUC)
  length_only_auc AUC(−input_len → success)               (confound-only baseline)
  residualized    AUC(oof_prob − OLS(oof_prob~len))       (in-sample; descriptive)
  logo_gain       grouped-LOGO AUC{oof_prob+len} − {len}  (does the detector add beyond length, OOF?)
  + goal-clustered bootstrap 95% CI on logo_gain.

Reuses: `phase17_detector._assemble` (hidden states + labels + groups, same §9 loaders), the sklearn
pipelines (`detector_groupkfold_audit.make_pipe`, `phase17_detector._mlp_pipe`), and the phase-6
confound functions (`_residualize`, `_grouped_logo_auc`, `_goal_bootstrap_gain_ci`).

CPU only. Usage:
  python scripts/phase17_confound.py --cells mlp:think_content_1:19 logistic:prefill_last:38 fisher:think_content_1:20 \
    --out outputs/phase17_detect/detector_CvsD_confound.csv --bootstrap 1000
"""
from __future__ import annotations

import argparse
import glob
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

from scripts.phase17_detector import _assemble, _mlp_pipe
from scripts.phase6_signal_search import _labels_from_scores
from scripts.detector_groupkfold_audit import make_pipe
from scripts.phase6_confound_control import _residualize, _grouped_logo_auc, _goal_bootstrap_gain_ci


def _input_lengths(run_dir: Path) -> dict:
    """row_key -> input_token_count from the §9 generation shards."""
    out = {}
    for shard in glob.glob(str(run_dir / "generation" / "shards" / "*.jsonl")):
        with open(shard) as f:
            for line in f:
                line = line.strip()
                if line:
                    r = json.loads(line)
                    out[r["row_key"]] = r.get("input_token_count") or 0
    return out


def _oof_probs(kind, X, y, groups, ilen=None):
    """Grouped leave-one-goal-out OOF probability (or Fisher projection) per row; returns
    (probs, y, groups, ilen) aligned to the finite rows actually predicted. When `ilen` is given, the
    per-row length vector is masked with the SAME per-fold finite/held-out mask (te & fin_te) as the
    features/labels, so a PARTIAL-NaN cell still yields a length vector aligned to the exact OOF rows
    (fixes length_only/resid/gain/CI = None whenever some rows are non-finite; e.g. Phi-4 think_content_1
    67/72 finite). For all-finite cells this reproduces ilen_all in identical goal-major order → unchanged."""
    pr, yy, gg, ll = [], [], [], []
    il = None if ilen is None else np.asarray(ilen)
    for g in np.unique(groups):
        tr, te = groups != g, groups == g
        fin_tr = np.isfinite(X[tr]).all(axis=1)
        ytr = y[tr][fin_tr]
        if len(np.unique(ytr)) < 2:
            continue
        fin_te = np.isfinite(X[te]).all(axis=1)
        if not fin_te.any():
            continue
        Xtr, Xte = X[tr][fin_tr], X[te][fin_te]
        if kind == "fisher":
            d = Xtr[ytr].mean(0) - Xtr[~ytr].mean(0)
            nrm = np.linalg.norm(d)
            if nrm == 0 or not np.isfinite(nrm):
                continue
            p = Xte @ (d / nrm)
        else:
            if kind == "mlp" and min(np.bincount(ytr.astype(int))) < 2:
                continue
            try:
                pipe = (make_pipe if kind == "logistic" else _mlp_pipe)()
                pipe.fit(Xtr, ytr)
                p = pipe.predict_proba(Xte)[:, 1]
            except ValueError:
                continue
        pr.extend(np.asarray(p).tolist())
        yy.extend(y[te][fin_te].astype(int).tolist())
        gg.extend([g] * int(fin_te.sum()))
        if il is not None:
            ll.extend(np.asarray(il[te][fin_te]).tolist())
    return (np.array(pr), np.array(yy), np.array(gg),
            (np.array(ll) if il is not None else None))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", default="outputs/phase5_mechanistic/extraction")
    ap.add_argument("--model", default="qwen3")
    ap.add_argument("--conditions", nargs="+", default=["C", "D"])
    ap.add_argument("--scores", default="outputs/phase5_mechanistic/phase6_scores.jsonl")
    ap.add_argument("--cells", nargs="+", required=True, help="detector:position:layer tuples")
    ap.add_argument("--bootstrap", type=int, default=1000)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    hidden_dir = Path(args.run_dir) / "hidden_states" / "shards"
    labels = _labels_from_scores(Path(args.scores))
    position_names, n_layers, data = _assemble(hidden_dir, args.model, args.conditions, labels)
    if data is None:
        print("[phase17-confound] no data")
        return 1
    T, y, groups = data
    lengths_by_key = _input_lengths(Path(args.run_dir))
    # Per-row input length aligned to T's row order: _assemble stacks rows in (goal, condition, meta
    # row_offset) order; recover the row_keys the same way to map lengths.
    # Simpler + robust: rebuild the aligned length vector from the metadata used by _assemble.
    from poc_stage_ae.analyze_early_token_signals import _load_goal, _rowkey_labels, _goal_shards
    goals = sorted({g for c in args.conditions for g in _goal_shards(hidden_dir, args.model, c)})
    ilen_rows = []
    for g in goals:
        for c in args.conditions:
            if not (hidden_dir / f"{args.model}_{c}_goal{g}.pt").exists():
                continue
            meta, _ = _load_goal(hidden_dir, args.model, c, g)
            rks = meta.drop_duplicates("row_key").sort_values("row_offset")["row_key"].tolist()
            ylab = _rowkey_labels(meta, labels)
            for rk, lab in zip(rks, ylab):
                if lab is None:
                    continue
                ilen_rows.append(lengths_by_key.get(rk, 0))
    ilen_all = np.array(ilen_rows, dtype=float)
    assert len(ilen_all) == len(y), f"length-vector misalignment {len(ilen_all)} vs {len(y)}"

    recs = []
    for cell in args.cells:
        kind, pos, layer = cell.split(":")
        layer = int(layer)
        if pos not in position_names:
            print(f"[phase17-confound] {cell}: unknown position '{pos}' — skip"); continue
        p = position_names.index(pos)
        X = T[:, p, layer, :]
        # _oof_probs now masks the length vector with the SAME per-fold finite mask, so `ilen` is always
        # aligned to the exact OOF rows — including PARTIAL-NaN cells (was: an all-or-nothing len check
        # that nulled the whole length-controlled block whenever any row was non-finite).
        probs, yy, gg, ilen = _oof_probs(kind, X, y, groups, ilen_all)
        if len(np.unique(yy)) < 2:
            print(f"[phase17-confound] {cell}: degenerate, skip"); continue
        raw = float(roc_auc_score(yy, probs))
        rec = {"cell": cell, "detector": kind, "position_name": pos, "layer_index": layer,
               "n": len(yy), "raw_auc": round(raw, 4)}
        if ilen is not None:
            length_only = float(roc_auc_score(yy, -ilen))
            resid = float(roc_auc_score(yy, _residualize(probs.astype(float), ilen)))
            full = _grouped_logo_auc(np.column_stack([probs, ilen]), yy.astype(bool), gg)
            leno = _grouped_logo_auc(ilen.reshape(-1, 1), yy.astype(bool), gg)
            gain = None if (full is None or leno is None) else round(full - leno, 4)
            rec.update({"length_only_auc": round(length_only, 4), "residualized_auc": round(resid, 4),
                        "logo_full_auc": None if full is None else round(full, 4),
                        "logo_lenonly_auc": None if leno is None else round(leno, 4),
                        "logo_gain_over_length": gain})
            if args.bootstrap > 0 and gain is not None:
                lo, hi, fpos = _goal_bootstrap_gain_ci(probs.astype(float), ilen, yy.astype(bool), gg,
                                                       n_boot=args.bootstrap)
                rec.update({"gain_ci_lo": None if lo is None else round(lo, 4),
                            "gain_ci_hi": None if hi is None else round(hi, 4),
                            "frac_gain_positive": fpos})
        recs.append(rec)
        print(f"[phase17-confound] {cell}: raw={rec['raw_auc']} "
              f"resid={rec.get('residualized_auc')} gain={rec.get('logo_gain_over_length')} "
              f"CI=[{rec.get('gain_ci_lo')},{rec.get('gain_ci_hi')}] P+={rec.get('frac_gain_positive')}")

    df = pd.DataFrame.from_records(recs)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.out, index=False)
    print(f"[phase17-confound] {len(df)} cells → {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
