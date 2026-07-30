"""
33_build_directions.py — CAUSAL_CORE_PLAN §2 + §16.6 (S4). CPU-only.

Construct the causal directions and low-rank subspaces from the extracted reps, with
CROSS-FITTING: everything is fitted separately on `dev` and on `heldout`, so an
intervention can always be driven by a direction the test prompts never contributed to.

Directions, per (component, position, layer), following the plan's terminology exactly:
  d_Direct    = mean(DIRECT_CONCEPT)   - mean(NEUTRAL_CODEWORD)
  d_DS        = mean(DOUBLESPEAK)      - mean(NEUTRAL_CODEWORD)
  d_benign    = mean(BENIGN_REMAP)     - mean(NEUTRAL_CODEWORD)   [control direction]
  d_unrelated = mean(UNRELATED_TARGET) - mean(NEUTRAL_CODEWORD)   [control direction]

`d_Direct` and `d_DS` are NOT assumed equivalent (§2) — their per-layer cosine is a
first-class output, and is exactly the quantity the behavioral sufficiency dissociation
predicts should be low.

Subspaces: top-k principal directions of the per-prompt paired differences
(DS_i - mean Neutral) at resid_post/codeword_last, fitted per split. Used both as a
richer intervention basis and as the "random vector inside the same PCA subspace"
control (plan §5).

Usage:
  python 33_build_directions.py --reps-dir outputs/pair_reps_<...> --out-root outputs
"""
import os
import sys
import json
import time
import argparse

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ds_common as dc

HERE = os.path.dirname(os.path.abspath(__file__))

BASELINE = "NEUTRAL_CODEWORD"
DIRECTION_SPECS = {
    "d_Direct": "DIRECT_CONCEPT",
    "d_DS": "DOUBLESPEAK",
    "d_benign": "BENIGN_REMAP",
    "d_unrelated": "UNRELATED_TARGET",
    "d_repeated": "REPEATED_CODEWORD",
}
SPLITS = ("dev", "heldout")


def cos(a, b):
    """Cosine, or NaN when either vector is degenerate.

    NaN is EXPECTED and meaningful at resid_pre layer 0: that row is the static input
    embedding, and `d_DS` there is exactly zero because DOUBLESPEAK and NEUTRAL_CODEWORD
    contain the SAME codeword token — the hijack is purely contextual, never lexical
    (plan §2's static-embedding vs contextual-state distinction). Callers must therefore
    aggregate with nan-safe reductions rather than treating NaN as a failure.
    """
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    if na < 1e-8 or nb < 1e-8:
        return float("nan")
    return float(np.dot(a, b) / (na * nb))


def degenerate_layers(vecs):
    """Layers where a direction is (numerically) the zero vector."""
    return [l for l, v in enumerate(vecs) if float(np.linalg.norm(v)) < 1e-8]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps-dir", required=True)
    ap.add_argument("--out-root", default=os.path.join(HERE, "outputs"))
    ap.add_argument("--subspace-rank", type=int, default=8)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    dc.set_seed(args.seed)
    reps_dir = args.reps_dir
    summary = json.load(open(os.path.join(reps_dir, "reps_summary.json")))
    means = np.load(os.path.join(reps_dir, "means.npz"))
    L = summary["n_layers"]
    comps, poss = summary["components"], summary["positions"]

    uniq = os.environ.get("SLURM_JOB_ID") or str(os.getpid())
    out_dir = os.path.join(args.out_root,
                           f"pair_directions_{time.strftime('%Y%m%d_%H%M%S')}_{uniq}")
    os.makedirs(out_dir, exist_ok=True)

    # ---- mean-difference directions ----
    store, missing = {}, []
    for split in SPLITS:
        for c in comps:
            for p in poss:
                base_key = f"{BASELINE}|{split}|{c}|{p}"
                if base_key not in means:
                    missing.append(base_key)
                    continue
                base = means[base_key]                     # [L, H]
                for dname, cond in DIRECTION_SPECS.items():
                    k = f"{cond}|{split}|{c}|{p}"
                    if k not in means:
                        missing.append(k)
                        continue
                    store[f"{dname}|{split}|{c}|{p}"] = (means[k] - base).astype(np.float32)

    # ---- PCA subspaces from per-prompt paired differences ----
    pp = np.load(os.path.join(reps_dir, "per_prompt.npz"))["resid_post_codeword"]
    rows = summary["rows"]
    idx = {}
    for r in rows:
        idx.setdefault((r["condition"], r["split"]), []).append(r["row"])

    subspaces, evr = {}, {}
    for split in SPLITS:
        base_rows = idx.get((BASELINE, split), [])
        ds_rows = idx.get(("DOUBLESPEAK", split), [])
        if not base_rows or not ds_rows:
            continue
        for ell in range(L):
            # This is the WITHIN-DOUBLESPEAK centered-variance subspace: subtracting base_mu
            # then re-centering (X - X.mean) cancels base_mu, so the SVD basis is the
            # eigenbasis of cov(DOUBLESPEAK reps) with the mean (d_DS) axis REMOVED. The
            # `rand_in_pca_subspace` control therefore samples the directions of DS-internal
            # variation, NOT the d_DS mean-difference axis. That is the intended stringent
            # control (random vectors in the space the hijacked reps actually spread over);
            # note it does NOT contain d_DS itself. (Clarified in the 2026-07-30 review — the
            # base_mu subtraction on the next line is mathematically redundant and kept only
            # for readability of intent.)
            base_mu = pp[base_rows, ell, :].astype(np.float32).mean(axis=0)
            X = pp[ds_rows, ell, :].astype(np.float32) - base_mu      # [n, H]
            X = X - X.mean(axis=0, keepdims=True)
            k = min(args.subspace_rank, X.shape[0] - 1, X.shape[1])
            if k < 1:
                continue
            # right singular vectors = principal directions in rep space
            _, S, Vt = np.linalg.svd(X, full_matrices=False)
            subspaces[f"pca_DS|{split}|{ell}"] = Vt[:k].astype(np.float32)
            tot = float((S ** 2).sum())
            evr[f"{split}|{ell}"] = [round(float(s ** 2 / tot), 5) for s in S[:k]] if tot > 0 else []

    np.savez_compressed(os.path.join(out_dir, "directions.npz"), **store, **subspaces)

    # ---- diagnostics: are d_Direct and d_DS the same thing? ----
    diag = {}
    for c in comps:
        for p in poss:
            for split in SPLITS:
                dd = store.get(f"d_Direct|{split}|{c}|{p}")
                ds = store.get(f"d_DS|{split}|{c}|{p}")
                if dd is None or ds is None:
                    continue
                diag[f"cos_Direct_DS|{split}|{c}|{p}"] = [round(cos(dd[l], ds[l]), 4)
                                                          for l in range(L)]
                diag[f"degenerate_layers_d_DS|{split}|{c}|{p}"] = degenerate_layers(ds)
                diag[f"degenerate_layers_d_Direct|{split}|{c}|{p}"] = degenerate_layers(dd)
                diag[f"norm_Direct|{split}|{c}|{p}"] = [round(float(np.linalg.norm(dd[l])), 4)
                                                        for l in range(L)]
                diag[f"norm_DS|{split}|{c}|{p}"] = [round(float(np.linalg.norm(ds[l])), 4)
                                                    for l in range(L)]
                for ctrl in ("d_benign", "d_unrelated", "d_repeated"):
                    cv = store.get(f"{ctrl}|{split}|{c}|{p}")
                    if cv is not None:
                        diag[f"cos_DS_{ctrl}|{split}|{c}|{p}"] = [
                            round(cos(ds[l], cv[l]), 4) for l in range(L)]
            # cross-fit stability of each direction between splits
            for dname in DIRECTION_SPECS:
                a = store.get(f"{dname}|dev|{c}|{p}")
                b = store.get(f"{dname}|heldout|{c}|{p}")
                if a is not None and b is not None:
                    diag[f"crossfit_cos_{dname}|{c}|{p}"] = [round(cos(a[l], b[l]), 4)
                                                             for l in range(L)]

    out = {
        "plan": "CAUSAL_CORE_PLAN §2 + §16.6 (S4)",
        "reps_dir": os.path.abspath(reps_dir), "pair": summary["pair"],
        "model": summary["model"], "env": dc.env_metadata(),
        "n_layers": L, "components": comps, "positions": poss,
        "baseline_condition": BASELINE, "direction_specs": DIRECTION_SPECS,
        "subspace_rank": args.subspace_rank,
        "n_direction_keys": len(store), "n_subspace_keys": len(subspaces),
        "missing_condition_cells": sorted(set(missing)),
        "explained_variance_ratio": evr,
        "diagnostics": diag,
        "status": "COMPLETE",
    }
    with open(os.path.join(out_dir, "directions_summary.json"), "w") as f:
        json.dump(out, f, indent=1)

    # headline: the plan's central question about direction equivalence
    for c in comps:
        for p in poss:
            key = f"cos_Direct_DS|dev|{c}|{p}"
            if key in diag:
                v = np.asarray(diag[key], dtype=float)
                deg = diag.get(f"degenerate_layers_d_DS|dev|{c}|{p}", [])
                if np.all(np.isnan(v)):
                    print(f"[dir] cos(d_Direct, d_DS) {c}/{p} dev: all-degenerate")
                    continue
                print(f"[dir] cos(d_Direct, d_DS) {c}/{p} dev: "
                      f"min={np.nanmin(v):.3f} max={np.nanmax(v):.3f} "
                      f"argmax_layer={int(np.nanargmax(v))} mean={np.nanmean(v):.3f}"
                      + (f"  [d_DS degenerate at layers {deg} — expected at "
                         f"resid_pre L0: identical static embedding]" if deg else ""))
    print(f"[dir] {len(store)} directions + {len(subspaces)} subspaces -> {out_dir}")
    if missing:
        print(f"[dir] WARNING missing cells: {sorted(set(missing))[:5]}")


if __name__ == "__main__":
    main()
