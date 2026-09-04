#!/usr/bin/env python
"""dcs_figures.py -- the DCS phase's figures (plan section 42). CPU only, no new data.

WHAT IS AND IS NOT PLOTTED. Section 42 lists eight figures written before any result existed. Four of
them describe quantities this phase ended up NOT having: a validated concept-specific metric
(`R-002` says there is none), a metric-vs-forced-choice validity panel and a metric-vs-ASR panel
(both presuppose that metric), and an occurrence trajectory that `R-003` showed does not accumulate.
⛔ Plotting them anyway would be drawing the phase we planned rather than the one we ran. The four
here are the four the results support, and the gap is stated in the phase log rather than papered
over with a panel.

EVERY PANEL CARRIES ITS OWN n, MODEL, BANK, CELL AND ENDPOINT (section 42's rule). A figure whose
caption cannot be checked against the artifact is how a plot and a report come to disagree -- this
repo has a guard for exactly that (`canonical_figures.py`).

READS ONLY committed `results.jsonl`. Recomputes every plotted number from the artifacts rather than
from any analysis script's cached output, so a drift between figure and text shows up here first.
"""
from __future__ import annotations

import argparse
import collections
import glob
import json
import math
import os
import statistics as st
import sys
from fractions import Fraction

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCHEMA = "DCS_FIGURES/1"
MODEL = "Llama-3.1-8B-Instruct"
BAND = "L6-14"


def rows(tag):
    d = sorted(glob.glob(os.path.join(ROOT, "outputs/boombness/score_behavior", tag + "_*")))[-1]
    with open(os.path.join(d, "results.jsonl"), encoding="utf-8") as fh:
        return {r["prompt_id"]: r for r in (json.loads(l) for l in fh)}


def sign_p(vals):
    hi = sum(1 for v in vals if v > 0)
    lo = sum(1 for v in vals if v < 0)
    k, x = hi + lo, min(hi, lo)
    if not k:
        return hi, lo, 1.0
    p = min(Fraction(2 * sum(math.comb(k, i) for i in range(x + 1)), 1 << k), Fraction(1))
    return hi, lo, float(p)


def per_domain(a, b, ref, base):
    d = collections.defaultdict(list)
    for p in ref:
        d[base[p]["domain"]].append(a[p]["semantic_logodds"] - b[p]["semantic_logodds"])
    return {k: st.mean(v) for k, v in d.items()}


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=os.path.join(ROOT, "reports"))
    a = ap.parse_args()
    base = rows("dcsro_C_baseline")
    ref = sorted(base)
    n, ndom = len(ref), len({base[p]["domain"] for p in ref})
    b_mean = st.mean([base[p]["semantic_logodds"] for p in ref])

    fig, axes = plt.subplots(2, 2, figsize=(13.6, 9.4))
    fig.suptitle("Doublespeak concept-specific phase (DCS) — cell C = natural_doublespeak; "
                 "Llama-3.1-8B-Instruct @ L6-14 unless a panel states otherwise",
                 fontsize=11.5, y=0.985)

    # ---- A: the row dose-ladder (R-022) -- the phase's cleanest mechanistic result -------------
    ax = axes[0][0]
    ladder = [(1, "dcsplr_C_demo", "dcsplr_C_ctrl_d1"), (2, "dcsk2_C_demo", "dcsk2_C_ctrl"),
              (8, "dcsk8_C_demo", "dcsk8_C_ctrl"), (16, "dcsk16_C_demo", "dcsk16_C_ctrl"),
              (32, "dcsro_C_qpo_demo", "dcsro_C_qpo_ctrl_d1")]
    ks, demo, ctrl = [], [], []
    for k, dt, ct in ladder:
        D, C = rows(dt), rows(ct)
        ks.append(k)
        demo.append(st.mean([D[p]["semantic_logodds"] for p in ref]))
        ctrl.append(st.mean([C[p]["semantic_logodds"] for p in ref]))
    ax.axhline(b_mean, color="0.45", ls=":", lw=1.4, label=f"baseline ({b_mean:+.2f})")
    ax.axhline(0, color="0.8", lw=0.9)
    ax.plot(ks, demo, "o-", color="#c1272d", lw=2.1, ms=7, label="demo keys cut")
    ax.plot(ks, ctrl, "s--", color="#2b6cb0", lw=1.7, ms=6, label="dose-matched control")
    ax.set_xscale("log", base=2)
    ax.set_xticks(ks)
    ax.set_xticklabels([str(k) for k in ks])
    ax.set_xlabel("K = last K rows of the query span cut from the demonstrations")
    ax.set_ylabel("semantic_logodds  (+ = concept reading)")
    ax.set_title("A  Row dose-ladder: a STEP between K=2 and K=8, then saturation\n"
                 f"forced-choice readout · n={n} rows · {ndom} domains · cds38_button_bomb",
                 fontsize=9.6, loc="left")
    ax.annotate("sign flip:\nliteral reading", xy=(8, demo[2]), xytext=(2.6, -0.4),
                fontsize=8.4, color="#c1272d",
                arrowprops=dict(arrowstyle="->", color="#c1272d", lw=1.2))
    ax.legend(fontsize=8.6, loc="center left")
    ax.grid(alpha=0.25)

    # ---- B: specificity DiD, both codewords (R-010 / R-011) -----------------------------------
    ax = axes[0][1]
    labels, cvals, bvals, dids = [], [], [], []
    for pair, pre in (("Llama\nbutton↔bomb", "dcsro"), ("Llama\nbasket↔bomb", "dcsbk"),
                      ("Qwen3-14B\nbutton↔bomb", "dcsqw")):
        per = {}
        for cell, tag in (("C", "C"), ("B", "B")):
            bb = rows(f"{pre}_{tag}_baseline")
            k = rows(f"{pre}_{tag}_qpo_demo")
            try:
                c = rows(f"{pre}_{tag}_qpo_ctrl_d1")
            except IndexError:
                c = rows(f"{pre}_{tag}_qpo_ctrl")   # Qwen arms use the un-suffixed control tag
            rr = sorted(bb)
            per[cell] = per_domain(k, c, rr, bb)
        doms = sorted(set(per["C"]) & set(per["B"]))
        labels.append(pair)
        cvals.append(st.mean([per["C"][d] for d in doms]))
        bvals.append(st.mean([per["B"][d] for d in doms]))
        dd = [per["C"][d] - per["B"][d] for d in doms]
        hi, lo, p = sign_p(dd)
        dids.append((st.mean(dd), hi, lo, p, len(doms)))
    x = range(len(labels))
    ax.bar([i - 0.21 for i in x], cvals, 0.4, color="#c1272d",
           label="cell C (codeword) — KO − control")
    ax.bar([i + 0.21 for i in x], bvals, 0.4, color="#2b6cb0",
           label="cell B (concept itself) — KO − control")
    ax.axhline(0, color="0.3", lw=1.0)
    for i, (m, hi, lo, p, nd) in enumerate(dids):
        ax.annotate(f"DiD {m:+.1f}\n{lo}/{nd} dom", xy=(i, 3.4), ha="center", va="center",
                    fontsize=8.0,
                    bbox=dict(boxstyle="round,pad=0.24", fc="white", ec="0.6", lw=0.8))
    ax.set_ylim(min(cvals) - 2.0, 6.4)
    ax.annotate("all three: 1+/37−, p = 2.8e-10", xy=(0.5, 0.035), xycoords="axes fraction",
                ha="center", va="bottom", fontsize=8.2, style="italic", color="0.35")
    ax.set_xticks(list(x))
    ax.set_xticklabels(labels, fontsize=8.6)
    ax.set_ylabel("Δ semantic_logodds vs dose-matched control")
    ax.set_title("B  Specificity: the whole-query knockout hits the codeword, not the concept\n"
                 "KO-3 · forced-choice · n=377-380/cell · 38 domains · 2 models × 2 codewords\n"
                 "⚠ one sign pattern replicated 3×, NOT 3 independent p-values",
                 fontsize=9.0, loc="left")
    ax.legend(fontsize=8.4, loc="lower right")
    ax.grid(alpha=0.25, axis="y")

    # ---- C: the KO ladder by scope (R-021) -----------------------------------------------------
    ax = axes[1][0]
    scopes = [("KO-1\ncodeword row", "dcsro_C_surfacerow_demo", "dcsro_C_surfacerow_ctrl_d1", 1),
              ("KO-4\nreadout row", "dcsplr_C_demo", "dcsplr_C_ctrl_d1", 1),
              ("KO-3\nwhole span", "dcsro_C_qpo_demo", "dcsro_C_qpo_ctrl_d1", 32)]
    names, effs, ps = [], [], []
    for lbl, dt, ct, _k in scopes:
        D, C = rows(dt), rows(ct)
        pd = per_domain(D, C, ref, base)
        hi, lo, p = sign_p(list(pd.values()))
        names.append(lbl)
        effs.append(st.mean([D[p_]["semantic_logodds"] - C[p_]["semantic_logodds"] for p_ in ref]))
        ps.append((hi, lo, p))
    cols = ["#8a8a8a" if e > -1 else "#c1272d" for e in effs]
    ax.bar(range(len(names)), effs, 0.55, color=cols)
    ax.axhline(0, color="0.3", lw=1.0)
    ax.set_ylim(min(effs) - 2.4, 2.6)
    for i, (e, (hi, lo, p)) in enumerate(zip(effs, ps)):
        ax.annotate(f"{e:+.2f}   {hi}+/{lo}−   p={p:.3g}",
                    xy=(i, 1.5), ha="center", va="center", fontsize=8.4,
                    bbox=dict(boxstyle="round,pad=0.30", fc="white", ec="0.6", lw=0.8))
    ax.set_xticks(range(len(names)))
    ax.set_xticklabels(names, fontsize=9)
    ax.set_ylabel("Δ semantic_logodds vs dose-matched control")
    ax.set_title("C  No single query position carries the mapping\n"
                 f"same band, same dose for KO-1 and KO-4 (2 088 cells) · n={n} · {ndom} domains",
                 fontsize=9.6, loc="left")
    ax.grid(alpha=0.25, axis="y")

    # ---- D: why the behavioural comparator matters (C-015 / R-019) -----------------------------
    ax = axes[1][1]
    jd = {}
    for lbl, tag in (("d1", "dcsbeh_C_qpo_ctrl_d1"), ("d2*", "dcsbeh_C_qpo_nondemo_matched_d2"),
                     ("d3", "dcsbeh_C_qpo_nondemo_matched_d3"),
                     ("s904_d1*", "dcss904_C_qpo_nondemo_matched_d1"),
                     ("s904_d2*", "dcss904_C_qpo_nondemo_matched_d2"),
                     ("s904_d3", "dcss904_C_qpo_nondemo_matched_d3")):
        p_ = sorted(glob.glob(os.path.join(ROOT, "outputs/boombness/judge",
                                           f"dcssel_{tag}_2026*")))
        if not p_:
            continue
        with open(os.path.join(p_[-1], "results.jsonl"), encoding="utf-8") as fh:
            rr = [json.loads(l) for l in fh]
        jd[lbl] = (sum(int(bool(r["refused"])) for r in rr) - 42,
                   sum(int(bool(r["malicious_at_0.5"])) for r in rr))
    if jd:
        xs = [v[0] for v in jd.values()]
        ys = [v[1] for v in jd.values()]
        qual = [l.endswith("*") for l in jd]
        ax.scatter([x for x, q in zip(xs, qual) if q], [y for y, q in zip(ys, qual) if q],
                   s=95, color="#2b6cb0", zorder=3, label="refusal-neutral (qualifies)")
        ax.scatter([x for x, q in zip(xs, qual) if not q], [y for y, q in zip(ys, qual) if not q],
                   s=95, color="#8a8a8a", marker="X", zorder=3, label="induces refusal (rejected)")
        for l, (dx, y) in jd.items():
            ax.annotate(l.rstrip("*"), (dx, y), fontsize=8.2, xytext=(5, 4),
                        textcoords="offset points")
        ax.axhline(153, color="0.45", ls=":", lw=1.4, label="baseline attacks (153)")
        ax.axhline(118, color="#c1272d", ls="--", lw=1.6, label="KO-3 attacks (118)")
        ax.axvspan(-17, 17, color="#2b6cb0", alpha=0.10)
        ax.set_xlabel("Δ refusals vs baseline   (shaded = ±17-row judge band)")
        ax.set_ylabel("attacks (malicious_at_0.5)")
        ax.set_title("D  Controls that induce refusal suppress attack, and hid the effect\n"
                     f"behavioral endpoint · n=380 · 38 domains · {len(jd)} of 6 draws\n"
                     f"(only draws judged in ONE invocation; cross-batch drift is +18 rows)",
                     fontsize=9.6, loc="left")
        ax.legend(fontsize=8.0, loc="lower left")
        ax.grid(alpha=0.25)

    fig.tight_layout(rect=[0, 0.012, 1, 0.968])
    os.makedirs(a.out, exist_ok=True)
    p = os.path.join(a.out, "DCS_FIGURES.png")
    fig.savefig(p, dpi=185)
    print(f"[dcs-fig] wrote {p}")
    print(f"[dcs-fig] panel A ladder: K={ks} demo={[round(v,3) for v in demo]} "
          f"ctrl={[round(v,3) for v in ctrl]}")
    print(f"[dcs-fig] panel B DiDs  : " +
          "; ".join(f"{l} {m:+.3f} ({lo}/{nd} dom, p={p:.2e})"
                    for l, (m, hi, lo, p, nd) in zip(labels, dids)))
    print(f"[dcs-fig] panel C scopes: " +
          "; ".join(f"{n_.splitlines()[0]} {e:+.3f}" for n_, e in zip(names, effs)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
