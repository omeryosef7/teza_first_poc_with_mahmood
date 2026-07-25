"""Phase-6 §10.4 confound control for the attack-success signal.

The core C-vs-D signal (`docs/PREDICTIVE_SIGNAL_REPORT.md` §1) reaches LOGO AUC ≈ 0.90 at early
positions, but success and failure also differ in prompt/generation length (§10.4 lists both as
confounds). This script asks, per (position, layer): **does the residual-stream projection still
separate success from failure AFTER removing the linear effect of prompt length?**

Method (reuse-first: sklearn `roc_auc_score`, same as `scripts/detector_groupkfold_audit.py`):
  For each (position, layer) with an out-of-fold projection per row (from
  `phase6_signal_search.py --emit-projections`):
    raw_auc          — AUC(projection → success)                    [the headline number]
    length_auc       — AUC(−input_len → success)                    [confound-only baseline]
    resid_auc        — AUC(residual → success), residual = projection − OLS(projection ~ input_len)
    partial_auc      — grouped-LOGO AUC of a logistic model success ~ projection + input_len,
                       vs length-only success ~ input_len; the projection SURVIVES if the
                       two-feature model beats length-alone out-of-fold.

Generation length is NOT used as a confound for pre-answer positions (prefill_last, think_content_*,
startofthink, endofthink): those hidden states are computed at/before the first generated token and
cannot depend on eventual generation length. Only input (prompt) length is a valid confound there.

Usage:
  python scripts/phase6_confound_control.py \
    --projections outputs/phase5_mechanistic/phase6_CvsD_projections.jsonl \
    --run-dir outputs/phase5_mechanistic/extraction \
    --out outputs/phase5_mechanistic/phase6_CvsD_confound.csv
"""
from __future__ import annotations

import argparse
import glob
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.preprocessing import StandardScaler

# Pre-answer positions where generation length is not a valid confound (see module docstring).
PRE_ANSWER = ("prefill_last", "startofthink", "think_content_1", "think_content_2",
              "think_content_3", "endofthink")


def _row_lengths(run_dir: Path) -> dict[str, dict]:
    """row_key -> {input_len, gen_len} from the §9 generation shards."""
    out = {}
    for shard in glob.glob(str(run_dir / "generation" / "shards" / "*.jsonl")):
        with open(shard) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                r = json.loads(line)
                out[r["row_key"]] = {
                    "input_len": r.get("input_token_count") or 0,
                    "gen_len": r.get("generation_token_count") or 0,
                }
    return out


def _auc(scores: np.ndarray, y: np.ndarray) -> float | None:
    if len(np.unique(y)) < 2:
        return None
    return float(roc_auc_score(y, scores))


def _residualize(x: np.ndarray, confound: np.ndarray) -> np.ndarray:
    """Return x with the OLS linear fit on `confound` removed (both standardized first)."""
    c = (confound - confound.mean()) / (confound.std() + 1e-9)
    A = np.vstack([np.ones_like(c), c]).T
    beta, *_ = np.linalg.lstsq(A, x, rcond=None)
    return x - A @ beta


def _grouped_logo_auc(feats: np.ndarray, y: np.ndarray, groups: np.ndarray) -> float | None:
    """Out-of-fold AUC of a logistic model, grouped leave-one-goal-out (matches §10.3)."""
    oof_scores, oof_y = [], []
    for g in np.unique(groups):
        tr, te = groups != g, groups == g
        if len(np.unique(y[tr])) < 2:
            continue
        scaler = StandardScaler().fit(feats[tr])
        clf = LogisticRegression(max_iter=1000).fit(scaler.transform(feats[tr]), y[tr].astype(int))
        prob = clf.predict_proba(scaler.transform(feats[te]))[:, 1]
        oof_scores.extend(prob.tolist())
        oof_y.extend(y[te].astype(int).tolist())
    if len(np.unique(oof_y)) < 2:
        return None
    return float(roc_auc_score(oof_y, oof_scores))


def _goal_bootstrap_gain_ci(x, ilen, y, groups, n_boot=1000, seed_offset=0):
    """Goal-clustered bootstrap 95% CI for the OOF gain of {proj+len} over {len} (§24.2/§6.7).
    Resample GOALS with replacement (not rows) so the CI respects the LOGO grouping; recompute the
    grouped-LOGO gain on each resample. Deterministic RNG (no Date/random-module dependence).
    Returns (lo, hi, frac_positive)."""
    uniq = np.unique(groups)
    gains = []
    for b in range(n_boot):
        rng = np.random.default_rng(1234567 + seed_offset + b)
        pick = rng.choice(len(uniq), size=len(uniq), replace=True)
        chosen = uniq[pick]
        # Build the resampled row set (goals may repeat). Keep ONE fold per ORIGINAL goal id, so a
        # goal drawn k times contributes its rows k× (weighting) but is NEVER split across the train
        # and held-out sides of the same LOGO fold — relabeling repeats as distinct folds would put
        # byte-identical rows in both train and test and leak the out-of-fold AUC upward.
        xs, ls, ys, gs = [], [], [], []
        for og in chosen:
            m = groups == og
            xs.append(x[m]); ls.append(ilen[m]); ys.append(y[m])
            gs.append(np.full(m.sum(), og))  # original goal id → single fold per goal
        xb = np.concatenate(xs); lb = np.concatenate(ls); yb = np.concatenate(ys); gb = np.concatenate(gs)
        full = _grouped_logo_auc(np.column_stack([xb, lb]), yb, gb)
        leno = _grouped_logo_auc(lb.reshape(-1, 1), yb, gb)
        if full is not None and leno is not None:
            gains.append(full - leno)
    if len(gains) < 20:
        return None, None, None
    gains = np.array(gains)
    return (float(np.percentile(gains, 2.5)), float(np.percentile(gains, 97.5)),
            float((gains > 0).mean()))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--projections", required=True)
    ap.add_argument("--run-dir", default="outputs/phase5_mechanistic/extraction")
    ap.add_argument("--out", required=True)
    ap.add_argument("--top", type=int, default=25, help="report the N highest-raw-AUC cells")
    ap.add_argument("--bootstrap", type=int, default=0,
                    help="if >0, goal-clustered bootstrap CI on the OOF gain for the top-raw pre-answer cells")
    ap.add_argument("--bootstrap-cells", type=int, default=5, help="how many top pre-answer cells to bootstrap")
    args = ap.parse_args()

    lengths = _row_lengths(Path(args.run_dir))
    proj = pd.read_json(args.projections, lines=True)
    proj["input_len"] = proj["row_key"].map(lambda k: lengths.get(k, {}).get("input_len"))
    proj = proj.dropna(subset=["input_len"])

    recs = []
    for (pos, lay), grp in proj.groupby(["position_name", "layer_index"]):
        y = grp["label"].to_numpy()
        if len(np.unique(y)) < 2:
            continue
        x = grp["projection"].to_numpy(dtype=float)
        ilen = grp["input_len"].to_numpy(dtype=float)
        groups = grp["goal_index"].to_numpy()

        raw = _auc(x, y)
        length_only = _auc(-ilen, y)
        resid = _auc(_residualize(x, ilen), y)
        partial_full = _grouped_logo_auc(np.column_stack([x, ilen]), y, groups)
        partial_lenonly = _grouped_logo_auc(ilen.reshape(-1, 1), y, groups)
        recs.append({
            "position_name": pos, "layer_index": int(lay), "n": len(y),
            "raw_auc": raw, "length_only_auc": length_only, "residualized_auc": resid,
            "logo_full_auc": partial_full, "logo_lenonly_auc": partial_lenonly,
            "logo_gain_over_length": (None if partial_full is None or partial_lenonly is None
                                      else round(partial_full - partial_lenonly, 4)),
            "pre_answer": pos in PRE_ANSWER,
        })

    df = pd.DataFrame.from_records(recs).sort_values("raw_auc", ascending=False)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.out, index=False)
    print(f"[confound] {len(df)} (position,layer) cells → {args.out}")

    pre = df[df["pre_answer"]].dropna(subset=["raw_auc"]).head(args.top)
    print("[confound] pre-answer cells (raw | length-only | residualized | LOGO full | LOGO len-only | gain):")
    for _, r in pre.iterrows():
        def fmt(v):
            return "  n/a" if v is None or (isinstance(v, float) and np.isnan(v)) else f"{v:.3f}"
        print(f"    {r['position_name']:16s} L{r['layer_index']:>2}  "
              f"{fmt(r['raw_auc'])} | {fmt(r['length_only_auc'])} | {fmt(r['residualized_auc'])} | "
              f"{fmt(r['logo_full_auc'])} | {fmt(r['logo_lenonly_auc'])} | {fmt(r['logo_gain_over_length'])}")

    if args.bootstrap > 0:
        # §24.2/§6.7: goal-clustered bootstrap CI on the OOF gain for the top pre-answer cells.
        cells = pre.head(args.bootstrap_cells)[["position_name", "layer_index"]].values.tolist()
        print(f"[confound] goal-clustered bootstrap ({args.bootstrap}×) 95% CI on OOF gain {{proj+len}}−{{len}}:")
        boot_recs = []
        for pos, lay in cells:
            grp = proj[(proj["position_name"] == pos) & (proj["layer_index"] == lay)]
            lo, hi, fpos = _goal_bootstrap_gain_ci(
                grp["projection"].to_numpy(dtype=float), grp["input_len"].to_numpy(dtype=float),
                grp["label"].to_numpy(), grp["goal_index"].to_numpy(), n_boot=args.bootstrap)
            boot_recs.append({"position_name": pos, "layer_index": int(lay),
                              "gain_ci_lo": lo, "gain_ci_hi": hi, "frac_gain_positive": fpos})
            s = (f"[{lo:+.3f}, {hi:+.3f}]  P(gain>0)={fpos:.2f}"
                 if lo is not None else "n/a")
            print(f"    {pos:16s} L{int(lay):>2}  {s}")
        boot_out = Path(args.out).with_name(Path(args.out).stem + "_bootstrap.csv")
        pd.DataFrame.from_records(boot_recs).to_csv(boot_out, index=False)
        print(f"[confound] bootstrap CIs → {boot_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
