#!/usr/bin/env python3
"""ASYMMETRY SPRINT — paper figures (plan §14). CPU only, reads committed artifacts.

  FIGURE A  ACTIVATION vs CONTINUOUS vs DISCRETE — the control hierarchy.
            y1 = held-out Δ refusal projection @ L18/hs19, `decision` position, vs the
                 no-suffix baseline;  y2 = held-out Δ binary ASR (StrongREJECT ≥ 0.5).
            Quantities and arms were pre-registered in ASYMMETRY_GAP_MATRIX.md §E.6.
  FIGURE B  REACHABLE-SUBSPACE / local sensitivity — ‖Jᵀv‖ for the refusal direction against
            the full distribution of each control family (isotropic random, covariance-matched
            random, other-layer refusal, foreign mechanism).
  FIGURE B2 GATE B — the ε-scan: r(predicted, actual) vs perturbation size, per direction
            family, with ε=1.0 (one real token substitution) marked.
  FIGURE C  CROSS-PROMPT GRADIENT COHERENCE.
  FIGURE D  MULTI-CONCEPT DISSOCIATION (needs Phase 4; skipped if absent).
  FIGURE E  DEFENSE PARETO (needs Phase 5; skipped if absent).

Every panel annotates n, the split, the model and the control family, so the numbers are
recoverable from the figure alone (plan §14).
"""
import argparse
import json
import os
import sys
from collections import defaultdict

import numpy as np

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

C_MECH, C_RAND, C_ACT, C_OTHER = "#1b6ca8", "#9aa0a6", "#c65911", "#4a7c59"


def _save(fig, out_dir, name):
    os.makedirs(out_dir, exist_ok=True)
    for ext in ("png", "pdf"):
        fig.savefig(os.path.join(out_dir, f"{name}.{ext}"), dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"[fig] {os.path.join(out_dir, name)}.png")


# --------------------------------------------------------------------------- #
def figure_A(p1c_analysis, p2_asr, p2_dirs, out_dir):
    """Control hierarchy: Δ projection and Δ ASR side by side."""
    a = json.load(open(p1c_analysis))
    t = a["absolute_drop"]["test"]
    base_proj = t["baseline_none_mean"]
    seeds = (42, 43, 44)

    def mean_drop(prefix):
        v = [t[f"{prefix}_s{s}"]["drop_vs_none"] for s in seeds if f"{prefix}_s{s}" in t]
        return (float(np.mean(v)), float(np.std(v)), len(v)) if v else (np.nan, 0.0, 0)

    arms = []
    arms.append(("GCG init suffix\n(' !'x16)", t["init"]["drop_vs_none"], 0.0, "discrete"))
    arms.append(("GCG vanilla\n(task loss)", *mean_drop("vanilla_ds")[:2], "discrete"))
    arms.append(("GCG random\ndirection", *mean_drop("refusal_rand")[:2], "discrete"))
    arms.append(("GCG refusal\n@L18", *mean_drop("refusal")[:2], "discrete"))

    # soft-prompt arms from the Phase-2 runs
    soft = []
    for d in p2_dirs:
        mp = os.path.join(d, "meta.json")
        pp = os.path.join(d, "projections.json")
        if not (os.path.exists(mp) and os.path.exists(pp)):
            continue
        m, pj = json.load(open(mp)), json.load(open(pp))
        b0 = np.mean([r["proj_decision"] for r in pj["baseline_test"]])
        b1 = np.mean([r["proj_decision"] for r in pj["final_test"]])
        soft.append({"obj": m["objective"], "param": m["param"],
                     "budget": m.get("budget_rel"), "d": float(b1 - b0), "dir": d})
        if pj.get("rounding"):
            hr = np.mean([r["proj_decision"] for r in pj["rounding"]["test"]])
            soft.append({"obj": m["objective"], "param": "rounded", "budget": None,
                         "d": float(hr - b0), "dir": d})
    for s in sorted(soft, key=lambda x: (str(x["param"]), str(x["budget"]))):
        lab = (f"soft {s['param']}\n" +
               (f"budget {s['budget']}" if s["budget"] is not None else "(token bound)"))
        if s["obj"] == "random":
            lab = "soft random dir\n" + (f"budget {s['budget']}" if s["budget"] else "")
        kind = "continuous" if s["param"] == "free" else (
            "discrete" if s["param"] == "rounded" else "simplex")
        arms.append((lab, s["d"], 0.0, kind))

    asr = {}
    if os.path.exists(p2_asr):
        for v in json.load(open(p2_asr))["runs"].values():
            if v["n"] >= 20:
                asr[(v["objective"], v["param"], str(v["budget_rel"]))] = v["asr_binary"]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    cmap = {"discrete": C_RAND, "continuous": C_MECH, "simplex": C_OTHER}
    labels = [a_[0] for a_ in arms]
    vals = [a_[1] for a_ in arms]
    errs = [a_[2] for a_ in arms]
    cols = [cmap.get(a_[3], C_RAND) for a_ in arms]
    ax1.barh(range(len(arms)), vals, xerr=errs, color=cols, height=0.7)
    ax1.set_yticks(range(len(arms)))
    ax1.set_yticklabels(labels, fontsize=8)
    ax1.axvline(0, color="k", lw=0.8)
    ax1.set_xlabel("Δ refusal projection @ L18 / hs[19], decision position\n"
                   f"(held-out n=37; no-suffix baseline = {base_proj:.3f})")
    ax1.set_title("A1  How far each medium moves the CAUSAL direction")
    ax1.invert_yaxis()

    bars, names = [], []
    for (obj, param, b), v in sorted(asr.items()):
        names.append(f"soft {param}\n{obj} b={b}")
        bars.append(v)
    for ref, lab in ((0.243, "vanilla DS (seed42)"), (0.405, "best GCG arm ever")):
        ax2.axhline(ref, ls="--", lw=1, color="k", alpha=0.6)
        ax2.text(0.02, ref, lab, fontsize=7, va="bottom")
    ax2.bar(range(len(bars)), bars,
            color=[C_MECH if "refusal" in n else C_RAND for n in names])
    ax2.set_xticks(range(len(bars)))
    ax2.set_xticklabels(names, fontsize=7, rotation=30, ha="right")
    ax2.set_ylabel("binary ASR (StrongREJECT ≥ 0.5), held-out n=37")
    ax2.set_title("A2  …and whether BEHAVIOUR follows")
    ax2.set_ylim(0, 1)
    fig.suptitle("FIGURE A — activation vs continuous vs discrete control of the refusal "
                 "direction (Llama-3.1-8B-Instruct, ClearHarm v3 leakage-0)", fontsize=11)
    _save(fig, out_dir, "FIG_A_control_hierarchy")


def figure_B(p1_analysis_dirs, out_dir):
    for rd in p1_analysis_dirs:
        ap = os.path.join(rd, "ANALYSIS.json")
        jp = os.path.join(rd, "jacobian.jsonl")
        if not os.path.exists(jp):
            continue
        meta = json.load(open(os.path.join(rd, "meta.json")))
        by = defaultdict(lambda: defaultdict(dict))
        for line in open(jp):
            r = json.loads(line)
            if r["pos"] != "decision" or r["hs_row"] != 19:
                continue
            by[r["kind"]][r["dir"]][r["task_id"]] = r["grad_norm"]
        if "mechanism" not in by:
            continue
        tasks = sorted(next(iter(by["mechanism"].values())).keys())

        def arr(k):
            return np.array([[d[t] for t in tasks] for d in by[k].values()])

        mech = arr("mechanism")[0]
        fam = [(k, arr(k)) for k in ("random", "actrandom", "otherlayer", "foreign") if k in by]
        fig, ax = plt.subplots(figsize=(9, 5.5))
        colors = {"random": C_RAND, "actrandom": C_ACT, "otherlayer": C_OTHER,
                  "foreign": "#7d5ba6"}
        pretty = {"random": "isotropic random", "actrandom": "covariance-matched random\n(STRICT null)",
                  "otherlayer": "refusal @ other layers", "foreign": "concept direction"}
        for i, (k, A) in enumerate(fam):
            v = A.mean(axis=1)
            ax.scatter(np.full(len(v), i) + np.random.default_rng(0).normal(0, .05, len(v)),
                       v, s=10, alpha=.5, color=colors[k],
                       label=f"{pretty[k]} (n={A.shape[0]})")
            ax.hlines(np.median(v), i - .3, i + .3, color=colors[k], lw=2)
        ax.axhline(mech.mean(), color=C_MECH, lw=2.5,
                   label=f"refusal @ L18 = {mech.mean():.2f}")
        ax.set_xticks(range(len(fam)))
        ax.set_xticklabels([pretty[k] for k, _ in fam], fontsize=8)
        ax.set_ylabel(r"$\|J^{T}v\|$  (sensitivity of the target to suffix-token embeddings)")
        ax.set_yscale("log")
        ax.legend(fontsize=7, loc="best")
        ax.set_title(f"FIGURE B — local token reachability, {meta['split']} n={meta['n_items']}\n"
                     "refusal is the MOST reachable direction, above every control family")
        _save(fig, out_dir, f"FIG_B_reachability_{meta['split']}")

        # ---- B2: the eps-scan (Gate B) ----
        ep = os.path.join(rd, "eps_scan.jsonl")
        if not os.path.exists(ep):
            continue
        kinds = meta["fd_kept_direction_kinds"]["hs19"]
        rows = [json.loads(l) for l in open(ep)]
        rows = [r for r in rows if r["hs_row"] == 19 and r["pos"] == "decision"]
        eps = sorted({r["eps"] for r in rows})
        fig, ax = plt.subplots(figsize=(8, 5))
        for kind, col in (("mechanism", C_MECH), ("otherlayer", C_OTHER),
                          ("actrandom", C_ACT), ("random", C_RAND)):
            idx = [i for i, k in enumerate(kinds) if k == kind]
            if not idx:
                continue
            ys = []
            for e in eps:
                sub = [r for r in rows if abs(r["eps"] - e) < 1e-9]
                rs = []
                for i in idx:
                    p = np.array([r["pred"][i] for r in sub])
                    a_ = np.array([r["actual"][i] for r in sub])
                    if p.std() > 0 and a_.std() > 0:
                        rs.append(np.corrcoef(p, a_)[0, 1])
                ys.append(np.mean(rs) if rs else np.nan)
            ax.plot(eps, ys, "o-", color=col,
                    label="refusal @ L18" if kind == "mechanism" else kind)
        ax.axvline(1.0, color="k", ls="--", lw=1)
        ax.text(1.0, 0.9, " one real token\n substitution", fontsize=8, va="top")
        ax.axhline(0, color="k", lw=.8)
        ax.set_xscale("log")
        ax.set_xlabel("ε  (fraction of the way to a real token substitution)")
        ax.set_ylabel("r( first-order prediction , measured Δ⟨h,v⟩ )")
        ax.legend(fontsize=8)
        ax.set_title("FIGURE B2 — GATE B: the linear surrogate GCG relies on is valid only "
                     f"far below\nthe discrete step size ({meta['split']}, n={meta['n_items']})")
        _save(fig, out_dir, f"FIG_B2_eps_scan_{meta['split']}")


def figure_C(p1_analysis_dirs, out_dir):
    for rd in p1_analysis_dirs:
        ap = os.path.join(rd, "ANALYSIS.json")
        if not os.path.exists(ap):
            continue
        a = json.load(open(ap))
        coh = a.get("cross_prompt_coherence", {})
        cell = next((c for k, c in coh.items() if k.startswith("decision")), None)
        if not cell:
            continue
        mech = a["mech_name"]
        d = cell["directions"]
        if mech not in d:
            continue
        rnd = [v["mean_pairwise_cosine"] for k, v in d.items() if k.startswith("random")]
        fig, ax = plt.subplots(figsize=(7, 4.5))
        ax.hist(rnd, bins=12, color=C_RAND, alpha=.7,
                label=f"random directions (n={len(rnd)})")
        ax.axvline(d[mech]["mean_pairwise_cosine"], color=C_MECH, lw=2.5,
                   label=f"{mech} = {d[mech]['mean_pairwise_cosine']:.3f}")
        ax.set_xlabel("mean pairwise cosine between per-prompt input gradients")
        ax.set_ylabel("count")
        ax.legend(fontsize=8)
        ax.set_title(f"FIGURE C — cross-prompt coherence of the required token move\n"
                     f"({a['split']}, n_prompts={cell['n_prompts']})")
        _save(fig, out_dir, f"FIG_C_coherence_{a['split']}")


def figure_D(p4_json, out_dir):
    """Per concept: refusal-specific vs concept-specific ΔASR, with the power grading that
    decides which concept nulls are interpretable at all (plan §14 Figure D)."""
    if not os.path.exists(p4_json):
        return
    d = json.load(open(p4_json))
    pc_ = d["per_concept"]
    names = sorted(pc_, key=lambda c: -(pc_[c].get("refusal_specific", {}).get("delta_ASR", 0)))
    y = np.arange(len(names))
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 4.8), sharey=True)

    panels = [
        (ax1, "refusal_specific", "refusal ablation minus matched random\n(the ACTUATOR)"),
        (ax2, "concept_specific", "concept-circuit ablation minus matched random\n(the REPRESENTATION)"),
    ]
    for ax, key, title in panels:
        vals, los, his, cols = [], [], [], []
        for c in names:
            e = pc_[c].get(key)
            if not e:
                vals.append(0.0)
                los.append(0.0)
                his.append(0.0)
                cols.append("#eeeeee")
                continue
            vals.append(e["delta_ASR"])
            los.append(max(0.0, e["delta_ASR"] - e["boot95"][0]))
            his.append(max(0.0, e["boot95"][1] - e["delta_ASR"]))
            power = str(pc_[c].get("concept_test_power", ""))
            if key == "concept_specific" and power.startswith("floor"):
                cols.append("#dddddd")
            else:
                cols.append(C_MECH if e["p_mcnemar"] < 0.05 else C_RAND)
        ax.barh(y, vals, xerr=[los, his], color=cols, height=0.62, capsize=3)
        ax.axvline(0, color="k", lw=0.9)
        ax.set_title(title, fontsize=10)
        ax.set_xlim(-0.35, 0.9)
        ax.set_xlabel("specific ΔASR (StrongREJECT >= 0.5, held-out)")

    ax1.set_yticks(y)
    ax1.set_yticklabels(
        ["{}\n(n={}, ds_base={})".format(c.replace("pair_", ""),
                                         pc_[c].get("n_test", "?"),
                                         pc_[c].get("ds_base_asr", "?"))
         for c in names], fontsize=8)
    ax1.invert_yaxis()

    for i, c in enumerate(names):
        pw = str(pc_[c].get("concept_test_power", ""))
        if pw.startswith("floor"):
            ax2.text(0.03, i, "  no attack headroom -> uninformative",
                     fontsize=7, va="center", color="#777777")
        elif pw == "informative":
            ax2.text(0.30, i, "<- the only powered test",
                     fontsize=7, va="center", color=C_MECH)

    fig.suptitle("FIGURE D — multi-concept dissociation (Llama-3.1-8B, frozen pooled L18 axis). "
                 "blue p<0.05 · grey n.s. · pale = the test had no headroom", fontsize=10)
    _save(fig, out_dir, "FIG_D_multiconcept")


def figure_E(p5_summary, out_dir):
    """Defense Pareto: attack ASR reduction vs attack-structured-benign over-refusal, per arm,
    on BOTH splits, with the random/shuffled controls plotted so a non-specific 'fires less
    often' saving cannot be mistaken for a mechanism win (plan §14 Figure E)."""
    if not os.path.exists(p5_summary):
        return
    s = json.load(open(p5_summary))
    style = {
        "uncond": ("unconditional restoration", "#c0392b", "s"),
        "gate_refusal": ("gate: refusal only", "#e67e22", "^"),
        "gate_concept": ("gate: concept only", "#1b6ca8", "o"),
        "gate_two": ("gate: concept AND refusal", "#16a085", "D"),
        "gate_random": ("control: Bernoulli, matched fire-rate", "#9aa0a6", "x"),
        "gate_shuffled": ("control: shuffled features", "#7f8c8d", "+"),
    }
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.4))
    for ax, split in zip(axes, ("train", "test")):
        blk = s.get("by_split", {}).get(split, {})
        ds, ben = blk.get("ds"), blk.get("benign_attack")
        if not ds or not ben:
            ax.set_visible(False)
            continue
        for arm, (lab, col, mk) in style.items():
            if arm not in ds.get("vs_none", {}):
                continue
            x = ben["vs_none"][arm]["delta"]      # over-refusal cost (want small)
            y = -ds["vs_none"][arm]["delta"]      # ASR REDUCTION (want large)
            sig = ds["vs_none"][arm]["p_mcnemar"] < 0.05
            ax.scatter(x, y, s=120 if sig else 70, c=col, marker=mk,
                       label=lab if split == "train" else None,
                       edgecolors="k" if sig else "none", linewidths=0.8, zorder=3)
        ax.axhline(0, color="k", lw=0.8)
        ax.axvline(0, color="k", lw=0.8)
        ax.set_xlabel("attack-structured-BENIGN over-refusal increase  (lower is better)")
        ax.set_ylabel("harmful-Doublespeak ASR REDUCTION  (higher is better)")
        ax.set_title(f"{split}  (n={ds['n']}; DS baseline ASR = {ds['ASR']['none']:.3f})",
                     fontsize=10)
        ax.annotate("better", xy=(0.05, 0.92), xycoords="axes fraction", fontsize=9,
                    color="#16a085")
        ax.annotate("↑ / ←", xy=(0.05, 0.86), xycoords="axes fraction", fontsize=9,
                    color="#16a085")
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=3, fontsize=8, frameon=False,
               bbox_to_anchor=(0.5, -0.06))
    fig.suptitle("FIGURE E — defense Pareto. Filled black edge = ASR reduction significant "
                 "(p<0.05).\n'concept only' is INVISIBLE because it lands exactly under "
                 "'concept AND refusal' — the refusal half of the AND contributes nothing "
                 "(it fires on 87-100% of inputs).\nOn TEST no arm reduces ASR: the DS "
                 "baseline is already at a floor. On TRAIN the gates' over-refusal saving is "
                 "matched by the Bernoulli and shuffled controls.", fontsize=9)
    _save(fig, out_dir, "FIG_E_defense_pareto")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--p1c-analysis", default=None)
    ap.add_argument("--p1-dir", action="append", default=[])
    ap.add_argument("--p2-asr", default=os.path.join(HERE, "reports/ASYM_P2_ASR.json"))
    ap.add_argument("--p2-dir", action="append", default=[])
    ap.add_argument("--p4-json", default=os.path.join(HERE, "reports/ASYM_P4_MULTICONCEPT.json"))
    ap.add_argument("--p5-summary", default="")
    ap.add_argument("--out-dir", default=os.path.join(HERE, "figures/asymmetry"))
    args = ap.parse_args()

    if args.p1c_analysis and os.path.exists(args.p1c_analysis):
        figure_A(args.p1c_analysis, args.p2_asr, args.p2_dir, args.out_dir)
    if args.p1_dir:
        figure_B(args.p1_dir, args.out_dir)
        figure_C(args.p1_dir, args.out_dir)
    figure_D(args.p4_json, args.out_dir)
    if args.p5_summary:
        figure_E(args.p5_summary, args.out_dir)
    print("[done]")


if __name__ == "__main__":
    main()
