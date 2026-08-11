#!/usr/bin/env python3
"""ASYMMETRY SPRINT — PHASE 1 analysis (CPU). Turns an `asym_p1_reachability.py` run into
the GATE B and GATE C verdicts plus the §5.5 cross-prompt-coherence numbers.

  GATE B (plan §12) — does the autograd Jacobian actually predict REAL token moves?
      Pearson r, OLS slope and sign agreement between the first-order prediction
      <g_j(v), e_new - e_old> and the measured D<h,v>, per direction kind.
      PASS requires correct sign and a useful correlation for the mechanism direction.

  GATE C (plan §12) — classify the refusal direction's local reachability against the
      norm-matched random distribution: percentile of ||J^T v_refusal|| among the >=100
      random ||J^T v||, a robust z-score, and a paired-across-prompts bootstrap CI on the
      refusal-minus-median-random difference. Verdict is one of
      UNUSUALLY-LOW / NORMAL / UNUSUALLY-HIGH / UNDERPOWERED-UNSTABLE.

  §5.4 — R(v) = ||U_r^T v||^2 for the empirical local token-reachable subspace, compared
      against the isotropic null r/d_model AND against the random-direction distribution
      (the null that matters, since Dh is not isotropic).

  §5.5 — cross-prompt coherence: mean pairwise cosine between per-prompt g(v), the
      eigenspectrum of the stacked gradient matrix, and the fraction of variance in the top
      components. If refusal gradients are no more coherent across prompts than random ones,
      the failure of a UNIVERSAL suffix becomes mechanistically interpretable (H3/H5).

Reads scalars/tensors only. Writes JSON + a markdown summary.
"""
import argparse
import json
import os
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)

import numpy as np  # noqa: E402

import stats as st  # noqa: E402


def pearson(x, y):
    x, y = np.asarray(x, float), np.asarray(y, float)
    if x.size < 3 or x.std() == 0 or y.std() == 0:
        return float("nan")
    return float(np.corrcoef(x, y)[0, 1])


def ols_slope(x, y):
    x, y = np.asarray(x, float), np.asarray(y, float)
    if x.size < 3 or x.std() == 0:
        return float("nan")
    return float(np.polyfit(x, y, 1)[0])


# --------------------------------------------------------------------------- #

def analyze_jacobian(path, boot_n):
    """-> {cell: {...}} keyed by 'pos|hsRow'."""
    per = defaultdict(lambda: defaultdict(dict))     # cell -> dir -> task -> norm
    kind_of, profile = {}, defaultdict(lambda: defaultdict(list))
    with open(path) as fh:
        for line in fh:
            r = json.loads(line)
            cell = f"{r['pos']}|hs{r['hs_row']}"
            per[cell][r["dir"]][r["task_id"]] = r["grad_norm"]
            kind_of[r["dir"]] = r["kind"]
            profile[cell][r["dir"]].append(r["pos_profile"])

    out = {}
    for cell, dirs in per.items():
        tasks = sorted(set.intersection(*[set(v) for v in dirs.values()]))
        rand = [d for d in dirs if kind_of[d] == "random"]
        mech = [d for d in dirs if kind_of[d] == "mechanism"]
        frgn = [d for d in dirs if kind_of[d] == "foreign"]
        assert rand, f"no random controls in {cell}"
        # [n_random, n_tasks]
        R = np.array([[dirs[d][t] for t in tasks] for d in rand])
        rand_med_per_task = np.median(R, axis=0)
        cell_out = {"n_tasks": len(tasks), "n_random": len(rand),
                    "random_grad_norm_mean": float(R.mean()),
                    "random_grad_norm_median_of_task_medians": float(np.median(rand_med_per_task)),
                    "directions": {}}
        for d in mech + frgn + rand[:3]:
            v = np.array([dirs[d][t] for t in tasks])
            # percentile of this direction among the random distribution, per task,
            # then averaged -> "is it unusual, prompt by prompt?"
            pct = np.array([(R[:, i] < v[i]).mean() for i in range(len(tasks))])
            ci = st.paired_bootstrap_ci(v, rand_med_per_task, n_boot=boot_n, seed=0)
            mad = np.median(np.abs(R - np.median(R, axis=0)), axis=0)
            z = np.mean((v - rand_med_per_task) / (1.4826 * mad + 1e-12))
            cell_out["directions"][d] = {
                "kind": kind_of[d],
                "grad_norm_mean": float(v.mean()),
                "grad_norm_std": float(v.std()),
                "ratio_to_random_median": float(np.mean(v / (rand_med_per_task + 1e-12))),
                "mean_percentile_among_random": float(pct.mean()),
                "frac_tasks_above_random_median": float((v > rand_med_per_task).mean()),
                "robust_z_vs_random": float(z),
                "paired_diff_vs_random_median": ci,
            }
            prof = np.array(profile[cell][d])            # [n_tasks, suffix_len]
            cell_out["directions"][d]["position_profile_mean"] = \
                [float(x) for x in prof.mean(axis=0)]
        out[cell] = cell_out
    return out


def gate_c(cellstats, mech_name):
    """Classify reachability of `mech_name` (plan Gate C)."""
    d = cellstats["directions"].get(mech_name)
    if d is None:
        return {"verdict": "MISSING"}
    pct = d["mean_percentile_among_random"]
    lo, hi = d["paired_diff_vs_random_median"]["lo"], \
        d["paired_diff_vs_random_median"]["hi"]
    consistent = d["frac_tasks_above_random_median"]
    if lo <= 0 <= hi:
        verdict = "NORMAL-REACHABILITY (CI includes 0)"
    elif hi < 0:
        verdict = "UNUSUALLY-LOW REACHABILITY"
    else:
        verdict = "UNUSUALLY-HIGH REACHABILITY"
    if 0.2 < consistent < 0.8 and not (lo <= 0 <= hi):
        verdict += " (UNSTABLE: sign flips across prompts)"
    return {"verdict": verdict, "mean_percentile_among_random": pct,
            "frac_tasks_above_random_median": consistent,
            "ratio_to_random_median": d["ratio_to_random_median"],
            "robust_z_vs_random": d["robust_z_vs_random"],
            "paired_ci": d["paired_diff_vs_random_median"]}


def analyze_fd(npz_path):
    if not os.path.exists(npz_path):
        return {}
    z = np.load(npz_path, allow_pickle=True)
    cells = sorted({k.split("|", 1)[1] for k in z.files if k.startswith("pred|")})
    out = {}
    for cell in cells:
        pred, act = z[f"pred|{cell}"], z[f"actual|{cell}"]
        names, kinds = z[f"names|{cell}"], z[f"kinds|{cell}"]
        cell_out = {"n_substitutions": int(pred.shape[0]), "directions": {}}
        for i, nm in enumerate(names):
            p, a = pred[:, i], act[:, i]
            nz = np.abs(a) > 1e-9
            cell_out["directions"][str(nm)] = {
                "kind": str(kinds[i]),
                "pearson_r": pearson(p, a),
                "ols_slope_actual_on_pred": ols_slope(p, a),
                "sign_agreement": float((np.sign(p[nz]) == np.sign(a[nz])).mean())
                if nz.any() else float("nan"),
                "mean_abs_actual": float(np.abs(a).mean()),
                "mean_abs_pred": float(np.abs(p).mean()),
                "rel_abs_error": float(np.abs(p - a).mean() / (np.abs(a).mean() + 1e-12)),
            }
        # aggregate over the random controls so the mechanism has a reference
        ridx = [i for i, k in enumerate(kinds) if str(k) == "random"]
        if ridx:
            cell_out["random_pooled"] = {
                "pearson_r_mean": float(np.mean([pearson(pred[:, i], act[:, i]) for i in ridx])),
                "sign_agreement_mean": float(np.mean([
                    (np.sign(pred[:, i]) == np.sign(act[:, i])).mean() for i in ridx])),
            }
        out[cell] = cell_out
    return out


def gate_b(fdstats, mech_name):
    best = None
    for cell, c in fdstats.items():
        d = c["directions"].get(mech_name)
        if d is None:
            continue
        ok = (d["pearson_r"] > 0.5 and d["sign_agreement"] > 0.75
              and d["ols_slope_actual_on_pred"] > 0)
        rec = {"cell": cell, "pass": bool(ok), **d}
        if best is None or d["pearson_r"] > best["pearson_r"]:
            best = rec
    if best is None:
        return {"verdict": "MISSING"}
    return {"verdict": "PASS" if best["pass"] else "FAIL — first-order model does not "
            "predict real token moves; fix implementation before interpreting",
            **best}


def analyze_coherence(npz_path, ranks=(1, 3, 5)):
    """§5.5 — is the token move that suppresses refusal shared across prompts?"""
    if not os.path.exists(npz_path):
        return {}
    z = np.load(npz_path, allow_pickle=True)
    cells = sorted({k.split("|", 2)[2] + "|" + k.split("|", 2)[1]
                    for k in z.files if k.startswith("N|")})
    out = {}
    for key in [k for k in z.files if k.startswith("N|")]:
        _, pos, row = key.split("|")
        names = [str(x) for x in z[key]]
        gk = [k for k in z.files if k.startswith("G|") and k.endswith(f"|{pos}|{row}")]
        if len(gk) < 3:
            continue
        G = np.stack([z[k] for k in gk]).astype(np.float32)      # [n_prompts, n_dirs, L, d]
        n_p, n_d = G.shape[0], G.shape[1]
        F = G.reshape(n_p, n_d, -1)                              # [n_prompts, n_dirs, L*d]
        F = F / (np.linalg.norm(F, axis=2, keepdims=True) + 1e-12)
        cell = {"n_prompts": n_p, "directions": {}}
        for i, nm in enumerate(names):
            X = F[:, i, :]                                       # [n_prompts, L*d]
            Cm = X @ X.T                                         # cosines (rows unit)
            iu = np.triu_indices(n_p, k=1)
            cos = Cm[iu]
            sv = np.linalg.svd(X, compute_uv=False)
            ev = sv ** 2 / max(float((sv ** 2).sum()), 1e-12)
            cell["directions"][nm] = {
                "mean_pairwise_cosine": float(cos.mean()),
                "median_pairwise_cosine": float(np.median(cos)),
                "frac_pairs_positive": float((cos > 0).mean()),
                "top_k_variance": {str(r): float(ev[:r].sum()) for r in ranks
                                   if r <= len(ev)},
                "participation_ratio": float((ev.sum() ** 2) / max(float((ev ** 2).sum()), 1e-12)),
            }
        out[f"{pos}|{row}"] = cell
    return out


def analyze_subspace(path):
    if not os.path.exists(path):
        return {}
    S = json.load(open(path))
    out = {}
    for cell, e in S.items():
        cell_out = {"n_substitutions": e["n_substitutions"],
                    "explained_variance_top": {
                        str(r): float(sum(e["explained_variance_ratio"][:r]))
                        for r in (1, 4, 16, 64) if r <= len(e["explained_variance_ratio"])},
                    "R": {}}
        for rank, dd in e["R"].items():
            rand = [v for k, v in dd.items() if k.startswith("random")]
            if not rand:
                continue
            entry = {"null_isotropic": dd.get("__null_isotropic__"),
                     "random_mean": float(np.mean(rand)),
                     "random_p5": float(np.percentile(rand, 5)),
                     "random_p95": float(np.percentile(rand, 95))}
            for k, v in dd.items():
                if k.startswith("random") or k.startswith("__"):
                    continue
                entry[k] = {"R": float(v),
                            "percentile_among_random": float(np.mean(np.array(rand) < v)),
                            "ratio_to_random_mean": float(v / (np.mean(rand) + 1e-12))}
            cell_out["R"][rank] = entry
        out[cell] = cell_out
    return out


# --------------------------------------------------------------------------- #

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--mech-name", default="refusal_L18")
    ap.add_argument("--boot", type=int, default=10000)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    rd = args.run_dir
    meta = json.load(open(os.path.join(rd, "meta.json")))
    jac = analyze_jacobian(os.path.join(rd, "jacobian.jsonl"), args.boot)
    fd = analyze_fd(os.path.join(rd, "fd.npz"))
    coh = analyze_coherence(os.path.join(rd, "grads.npz"))
    sub = analyze_subspace(os.path.join(rd, "subspace.json"))

    primary = f"decision|hs{meta['hidden_states_index_rows'][-1]}"
    for c in jac:
        if c.startswith("decision") and args.mech_name in jac[c]["directions"]:
            primary = c
            break

    result = {
        "run_dir": rd, "split": meta["split"], "n_items": meta["n_items"],
        "model": meta.get("model_id", meta.get("model")),
        "mech_name": args.mech_name,
        "primary_cell": primary,
        "GATE_B_finite_difference": gate_b(fd, args.mech_name),
        "GATE_C_local_reachability": gate_c(jac[primary], args.mech_name) if primary in jac else {},
        "jacobian": jac, "finite_difference": fd,
        "cross_prompt_coherence": coh, "subspace": sub,
        "meta_echo": {k: meta[k] for k in
                      ("hidden_states_index_rows", "fit_layers_refusal", "fit_layers_concept",
                       "suffix_placement", "n_random", "n_substitutions_per_cell")
                      if k in meta},
    }
    out = args.out or os.path.join(rd, "ANALYSIS.json")
    json.dump(result, open(out, "w"), indent=2)

    print(f"=== P1 ANALYSIS  {rd}  split={meta['split']} n={meta['n_items']} ===")
    print(f"primary cell: {primary}")
    print(f"GATE B: {result['GATE_B_finite_difference'].get('verdict')}")
    b = result["GATE_B_finite_difference"]
    if "pearson_r" in b:
        print(f"        r={b['pearson_r']:.3f} slope={b['ols_slope_actual_on_pred']:.3f} "
              f"sign_agree={b['sign_agreement']:.3f} cell={b['cell']}")
    print(f"GATE C: {result['GATE_C_local_reachability'].get('verdict')}")
    g = result["GATE_C_local_reachability"]
    if "ratio_to_random_median" in g:
        ci = g["paired_ci"]
        print(f"        ratio_to_random_median={g['ratio_to_random_median']:.4f} "
              f"pct_among_random={g['mean_percentile_among_random']:.3f} "
              f"paired_diff CI=[{ci["lo"]:+.4g},{ci["hi"]:+.4g}]")
    for cell, c in sub.items():
        for rank in ("16", "64"):
            if rank in c["R"] and args.mech_name in c["R"][rank]:
                e = c["R"][rank][args.mech_name]
                print(f"  R(rank={rank}) {cell}: refusal={e['R']:.4f} "
                      f"random_mean={c['R'][rank]['random_mean']:.4f} "
                      f"null={c['R'][rank]['null_isotropic']:.4g} "
                      f"pct={e['percentile_among_random']:.3f}")
    for cell, c in coh.items():
        d = c["directions"].get(args.mech_name)
        if d:
            rmean = np.mean([v["mean_pairwise_cosine"] for k, v in c["directions"].items()
                             if k.startswith("random")])
            print(f"  coherence {cell}: refusal mean_cos={d['mean_pairwise_cosine']:+.4f} "
                  f"vs random {rmean:+.4f}  top1_var={d['top_k_variance'].get('1')}")
    print(f"[out] {out}")


if __name__ == "__main__":
    main()
