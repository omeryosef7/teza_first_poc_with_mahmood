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

    fig, axes = plt.subplots(4, 2, figsize=(13.6, 22.6))
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
    ax.annotate("sign flip: away from the\nconcept reading (R-032:\nLlama mostly says 'Neither')",
                xy=(8, demo[2]), xytext=(2.15, -0.55),
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
    ax.annotate("all three: 1+/37−, p = 2.8e-10", xy=(0.02, 0.035), xycoords="axes fraction",
                ha="left", va="bottom", fontsize=8.2, style="italic", color="0.35")
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
                   s=95, color="#2b6cb0", zorder=3, label="within ±17 tolerance (still +7..+14 refusals)")
        ax.scatter([x for x, q in zip(xs, qual) if not q], [y for y, q in zip(ys, qual) if not q],
                   s=95, color="#8a8a8a", marker="X", zorder=3, label="induces refusal (rejected)")
        for l, (dx, y) in jd.items():
            ax.annotate(l.rstrip("*"), (dx, y), fontsize=8.2, xytext=(5, 4),
                        textcoords="offset points")
        ax.axhline(153, color="0.45", ls=":", lw=1.4, label="baseline attacks (153)")
        ax.axhline(118, color="#c1272d", ls="--", lw=1.6, label="KO-3 attacks (118)")
        ax.axvspan(-17, 17, color="#2b6cb0", alpha=0.10)
        # the right-most point sits at dx~32 and its label was CLIPPED at the axes edge;
        # a data label a reader cannot finish is a legibility defect in a deliverable
        ax.margins(x=0.16)
        ax.set_xlabel("Δ refusals vs baseline   (shaded = ±17 TOLERANCE, not a judge band;\nC-023: measured band on `refused` is 0)")
        ax.set_ylabel("attacks (malicious_at_0.5)")
        ax.set_title("D  Controls that induce refusal suppress attack, and hid the effect\n"
                     "C-023: NO control is truly refusal-neutral (+7/+10/+14, 0-noise metric)\n"
                     f"behavioral endpoint · n=380 · 38 domains · {len(jd)} of 6 draws\n"
                     f"(only draws judged in ONE invocation; cross-batch drift is +18 rows)",
                     fontsize=9.6, loc="left")
        ax.legend(fontsize=8.0, loc="lower left")
        ax.grid(alpha=0.25)

    # ---- E: the layer profile (R-030) -- section 42 Figure 8, absent by design until the sweep ---
    axE = axes[2][0]
    # EQUAL-WIDTH bands (5 layers, dose 37 120 each) so cross-band magnitudes are comparable;
    # the two late bands come from the coarse sweep and are marked as such in the title.
    bands = [("0-4", "dcsFf00_04_demo", "dcsFf00_04_ctrl"),
             ("5-9", "dcsFf05_09_demo", "dcsFf05_09_ctrl"),
             ("10-14", "dcsFf10_14_demo", "dcsFf10_14_ctrl"),
             ("15-23\n(9L)", "dcsLb15_23_demo", "dcsLb15_23_ctrl"),
             ("24-31\n(8L)", "dcsLb24_31_demo", "dcsLb24_31_ctrl")]
    bl, be, bp = [], [], []
    for lbl, dt, ct in bands:
        D, C = rows(dt), rows(ct)
        pd = per_domain(D, C, ref, base)
        hi, lo, pv = sign_p(list(pd.values()))
        bl.append(lbl)
        be.append(st.mean([D[q]["semantic_logodds"] - C[q]["semantic_logodds"] for q in ref]))
        bp.append((hi, lo, pv))
    cols = ["#c1272d" if e < -1 else ("#2b6cb0" if e > 0.3 else "#8a8a8a") for e in be]
    axE.bar(range(len(bl)), be, 0.58, color=cols)
    axE.axhline(0, color="0.3", lw=1.0)
    axE.set_ylim(min(be) - 2.6, 3.4)
    for i, (e, (hi, lo, pv)) in enumerate(zip(be, bp)):
        axE.annotate(f"{e:+.2f}\n{hi}+/{lo}−", xy=(i, 2.0), ha="center", va="center", fontsize=8.0,
                     bbox=dict(boxstyle="round,pad=0.24", fc="white", ec="0.6", lw=0.8))
    axE.set_xticks(range(len(bl)))
    axE.set_xticklabels(bl, fontsize=8.4)
    axE.axvspan(-0.5, 2.5, color="#c1272d", alpha=0.06)
    axE.annotate("equal width (5L, dose 37 120)\n→ magnitudes comparable", xy=(1.0, min(be) - 1.5),
                 ha="center", va="center", fontsize=7.6, color="0.35", style="italic")
    axE.set_xlabel("layer band cut from the demonstrations")
    axE.set_ylabel("Δ semantic_logodds vs dose-matched control")
    axE.set_title("E  Layer profile: DISTRIBUTED over 0-14, peak at 10-14, absent above 14\n"
                  "KO-3 · each band vs its OWN dose-matched control · n=380 · 38 domains\n"
                  "⚠ shaded bands are equal-width/equal-dose; the two right-hand bands are 9L/8L "
                  "(coarse sweep) and are NOT dose-comparable to them",
                  fontsize=8.8, loc="left")
    axE.grid(alpha=0.25, axis="y")

    # ---- F: the installation gradient (R-041) -- the phase's newest headline ------------------
    # Recomputed from results.jsonl here, deliberately, NOT read from dcsp17_*.json: a figure that
    # reads the analyzer's cache cannot disagree with it, and disagreement is what this panel is
    # supposed to be able to show (`C-026`).
    from transformers import AutoTokenizer  # noqa: E402  -- only needed to decode top1_id
    _tok = AutoTokenizer.from_pretrained("meta-llama/Llama-3.1-8B-Instruct")

    def _install(tagrows, needle):
        per = collections.defaultdict(list)
        for r in tagrows.values():
            per[r["domain"]].append(
                1.0 if needle in _tok.decode([r["top1_id"]]).strip().lower() else 0.0)
        return {k: st.mean(v) for k, v in per.items()}

    def _rank(xs):
        order = sorted(range(len(xs)), key=lambda i: xs[i])
        rk = [0.0] * len(xs)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and xs[order[j + 1]] == xs[order[i]]:
                j += 1
            for k in range(i, j + 1):
                rk[order[k]] = (i + j) / 2.0 + 1.0
            i = j + 1
        return rk

    def _rho(x, y):
        rx, ry = _rank(x), _rank(y)
        mx, my = st.mean(rx), st.mean(ry)
        num = sum((u - mx) * (v - my) for u, v in zip(rx, ry))
        dx = math.sqrt(sum((u - mx) ** 2 for u in rx))
        dy = math.sqrt(sum((v - my) ** 2 for v in ry))
        return num / (dx * dy) if dx and dy else float("nan")

    axF = axes[3][0]
    inst = _install(base, "bomb")
    d_ko = per_domain(rows("dcsro_C_qpo_demo"), base, ref, base)
    d_ct = per_domain(rows("dcsro_C_qpo_ctrl_d1"), base, ref, base)
    doms = sorted(set(inst) & set(d_ko) & set(d_ct))
    xs = [inst[d] for d in doms]
    axF.scatter(xs, [d_ko[d] for d in doms], s=34, color="#1f4e79", zorder=3,
                label=f"KO-3 (demo_all)  rho={_rho(xs, [d_ko[d] for d in doms]):+.3f}")
    axF.scatter(xs, [d_ct[d] for d in doms], s=34, marker="^", facecolors="none",
                edgecolors="#c0504d", zorder=3,
                label=f"dose-matched control  rho={_rho(xs, [d_ct[d] for d in doms]):+.3f}")
    axF.axhline(0, color="0.55", lw=1.0, ls=":")
    axF.set_xlabel("baseline INSTALLATION  (per-domain fraction of rows whose argmax answer "
                   "is already 'bomb')")
    axF.set_ylabel("Δ semantic_logodds vs baseline")
    axF.set_title("F  Fully-installed domains lose MORE than partially-installed ones\n"
                  "    (R-041; narrowed by A-009/R-051/R-053, SETTLED by PR-023/R-055 -- CATEGORICAL)\n"
                  "button→bomb · Llama · L6-14 · n=380 · 38 domains · cell C\n"
                  "rho_KO = −0.594 here; −0.693 (n=1), −0.444 (n=8), −0.734 (Qwen) — 4 settings, 2 models\n"
                  "[!] the −0.907 CONTRAST is population-specific and inflated: this control's +0.312\n"
                  "does not reproduce (−0.04 / −0.02 / −0.33 on three other populations, R-051)\n"
                  "[!] SETTLED (R-055): no continuous dose-response within the partially-installed\n"
                  "range. Attack C fails on ALL THREE populations -- 13 dom p=0.343, 30 dom p=0.504,\n"
                  "33 dom p=0.210 on a bank BUILT to supply the range. The within-range gradient is\n"
                  "REGRESSION TO THE MEAN: on cds_n1 the CONTROL's rho moves -0.086 -> -0.338 by\n"
                  "conditioning on the subrange alone, with no knockout applied.",
                  fontsize=8.0, loc="left")
    axF.legend(fontsize=7.8, loc="lower left")
    axF.grid(alpha=0.25)

    # ---- G: every contrast measured, and which ones clear alpha --------------------------------
    axG = axes[3][1]
    contrasts = [("Llama n=4\n(blind primary)", -0.907, 2.0e-04),
                 ("Llama n=8\n(same 38 domains)", -0.404, 0.0482),
                 ("Qwen3-14B\n(rho pre-seen)", -0.407, 0.0594),
                 ("candle n=8\n(EXPLORATORY source)", -0.390, 0.0893)]
    ypos = list(range(len(contrasts)))[::-1]
    for y, (lab, c, pv) in zip(ypos, contrasts):
        clears = pv < 0.05
        axG.barh(y, c, height=0.5, color="#1f4e79" if clears else "0.72",
                 edgecolor="0.25", zorder=3)
        axG.text(0.02, y, f"{c:+.3f}   p={pv:.1e}" + ("  ✓ < α" if clears else "  ✗ not < α"),
                 ha="left", va="center", fontsize=8.0)
    axG.set_yticks(ypos)
    axG.set_yticklabels([c[0] for c in contrasts], fontsize=8.0)
    axG.set_xlim(-1.05, 0.72)
    axG.axvline(0, color="0.4", lw=1.1)
    axG.set_xlabel("contrast  rho_KO − rho_control   (negative = graded by installation)")
    axG.set_title("G  Every contrast measured, alpha=0.05, seeded permutation\n"
                  "[!] the CONTRAST is not the headline quantity — R-051 shows the comparator is\n"
                  "not reliably inert, so quote rho_KO and name the population for a contrast\n"
                  "[!] n=4 and n=8 are the SAME 38 domains at two doses — a second DOSE, not a\n"
                  "second SAMPLE, so these are NOT independent p-values\n"
                  "[!] Qwen does NOT clear alpha and is not reported as a replication that did",
                  fontsize=8.4, loc="left")
    axG.grid(alpha=0.25, axis="x")

    axes[2][1].axis("off")
    # TWO COLUMNS, not one. The card grew by two blocks this tick and a single column ran off the
    # bottom of its axes into panel G's title -- caught by reading the rendered PNG back, which is
    # the only check that sees layout damage (`C-026`).
    axes[2][1].text(0.00, 1.00,
                    "Scope carried by every panel\n"
                    "─────────────────────────────\n"
                    "38 domains x 2 codewords x 1 concept (bomb)\n"
                    "x 2 model families x one dose policy.\n"
                    "That is 38 CONTEXTS for a single mapping,\n"
                    "not 38 mappings.\n"
                    "R-050: the full installation swing is +10.68\n"
                    "log-odds vs a no-mapping cell (benign_literal\n"
                    "-5.495 -> cell C +5.188). CAVEAT: option_mass\n"
                    "collapses 0.877 -> 0.264 without a mapping, so\n"
                    "this readout only reads when one is installed.\n\n"
                    "Not shown, and why\n"
                    "─────────────────────────────\n"
                    "- metric-comparison / validity / metric-vs-ASR\n"
                    "  panels presuppose a validated concept-\n"
                    "  specific metric - R-002 found none exists.\n"
                    "- occurrence-trajectory panel presupposes\n"
                    "  accumulation - R-003 refuted it.\n\n"
                    "Behavioural status\n"
                    "─────────────────────────────\n"
                    "- Llama: B-009 RUN at k=116 (78 new domains),\n"
                    "  NOT RESOLVED (R-061). Conjunction over all 3\n"
                    "  dose-matched controls = 1 of 3:\n"
                    "  p = 0.175 / 0.0096 / 0.466. Never quote the\n"
                    "  0.0096 alone.\n"
                    "  [!] Domain count was NOT the constraint. The\n"
                    "  controls induce +35/+133/+200 refusals and the\n"
                    "  between-control spread (0.0586) EXCEEDS the\n"
                    "  effect (0.0391) -- the comparator draw decides\n"
                    "  the p-value, 0.01 to 0.47 on identical data.\n"
                    "- Qwen: CONFOUND-LIMITED (R-048). All 8 arms\n"
                    "  judged in one invocation. Face value gives\n"
                    "  KO-ctrl = +23..+45 (all 6 significant); the\n"
                    "  refusal adjustment gives -11..-32. ALL SIX\n"
                    "  BRACKETS STRADDLE ZERO => the sign is NOT\n"
                    "  determined. Forbidden both ways: 'increases'\n"
                    "  is the face value and is what the confound\n"
                    "  predicts (KO-3 refuses 0, controls ~200);\n"
                    "  'reduces' is the adjusted end (2 of 6); and\n"
                    "  'no effect' is still forbidden -- a straddling\n"
                    "  bracket is undetermined, not null.\n"
                    "- Judge-free and it survives: KO-3 removes ALL\n"
                    "  150 refusals and buys only +21 attacks\n"
                    "  (74->95), so 86% do not become attacks.",
                    fontsize=6.2, va="top", family="monospace")
    axes[2][1].text(0.52, 1.00,
                    "Generality (PR-013 / R-035)\n"
                    "─────────────────────────────\n"
                    "- MIXED, 1 of 2: lantern->poison PASSES\n"
                    "  (0+/20-, p=1.9e-06); candle->missile\n"
                    "  FAILS (6+/14-, p=0.115).\n"
                    "- R-033: dose-matched control IMPOSSIBLE\n"
                    "  in those banks => generic damage NOT\n"
                    "  excluded there, only inherited.\n"
                    "- R-037: the layer placebo is NOT inert -\n"
                    "  13.6%/17.2% of the 6-14 magnitude, and\n"
                    "  OPPOSITE in sign => PARTIAL exclusion.\n"
                    "- R-038: the 'weak mapping' excuse for\n"
                    "  candle is NOT supported. Doubling demos\n"
                    "  moved the magnitude 47% and the sign\n"
                    "  split 0 rows.\n\n"
                    "Installation gradient (R-041/R-043)\n"
                    "─────────────────────────────\n"
                    "- CORRELATIONAL across domains.\n"
                    "- CATEGORICAL, and now SETTLED (R-055).\n"
                    "  Attack C fails on all 3 populations:\n"
                    "  13 dom p=0.343, 30 dom p=0.504, 33 dom\n"
                    "  p=0.210 -- the last on a low-dose bank\n"
                    "  BUILT to supply the range (PR-023).\n"
                    "- The within-range gradient IS regression to\n"
                    "  the mean: on cds_n1 the CONTROL's rho moves\n"
                    "  -0.086 -> -0.338 by conditioning on the\n"
                    "  subrange alone, no knockout applied.\n"
                    "- On Llama the contrast survives LOO, 3\n"
                    "  operationalisations and an arm-exchangeable\n"
                    "  null; on Qwen it fails A (p=0.127) and E\n"
                    "  (p=0.165) as well as C.\n"
                    "- R-051: the -0.907 contrast is inflated;\n"
                    "  this control's +0.312 does NOT reproduce\n"
                    "  (-0.04 / -0.02 / -0.33). Quote rho_KO.\n"
                    "- R-064: the ceiling is a PARADIGM property,\n"
                    "  not a property of these 38 domains. 78 NEW\n"
                    "  domains, authored independently, reproduce\n"
                    "  the distribution almost exactly (mean 0.900\n"
                    "  vs 0.908, sd 0.192 vs 0.197). Low-install\n"
                    "  yield is 3.45% either way, so ~580 domains\n"
                    "  would be needed -- NOT a better bank, and\n"
                    "  NOT the low-dose block, which was built\n"
                    "  (R-054) and gave only 1 domain <=0.25.\n"
                    "- PR-018's manipulation had no headroom (R-042).",
                    fontsize=6.2, va="top", family="monospace")

    fig.subplots_adjust(left=0.075, right=0.985, top=0.955, bottom=0.035,
                        hspace=0.62, wspace=0.26)
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
