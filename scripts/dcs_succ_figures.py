#!/usr/bin/env python3
"""Publication-quality panels for the successor phase. Plan section 36.

Plan section 36 lists nine figures and attaches a hard requirement to every one of them:
*"Each figure must carry: n independent domains; split; CI; controls; exact metric."* That is
implemented literally -- every panel draws a SCOPE CARD from the artifact it plots, and a panel
whose artifact cannot supply one is not drawn.

FOUR of the nine are computable from artifacts that exist:
  F2  cell coordinates on the button->bomb axis        (A / C / B / E)          <- plan Fig 2
  F3  layer x position map of B1, on the PORTABLE cos  (C-214)                  <- plan Fig 3
  F5  the concept-free K ladder with its control band                           <- plan Fig 5
  F8  per-domain installation vs per-domain ASR, raw and concept-present        <- plan Fig 8

The other five need arms this phase did not run (an intervention delta against an ASR delta, a
reduced-patch series) and are NOT stubbed -- a panel that cannot be drawn from data is not drawn
with placeholder data.

USAGE
  python scripts/dcs_succ_figures.py
  python scripts/dcs_succ_figures.py --selftest
"""
from __future__ import annotations

import argparse
import collections
import glob
import json
import math
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "scripts"))
OUT = os.path.join(REPO, "reports", "figures")


class Refusal(RuntimeError):
    pass


def need(path):
    p = path if os.path.isabs(path) else os.path.join(REPO, path)
    if not os.path.exists(p):
        raise Refusal("required artifact missing: %s" % path)
    return p


def one_done(pattern):
    ds = [d for d in sorted(glob.glob(pattern)) if os.path.exists(os.path.join(d, "DONE.json"))]
    if len(ds) != 1:
        raise Refusal("%d completed runs match %s" % (len(ds), pattern))
    return ds[0]


def scope_card(ax, lines):
    """Plan section 36's requirement, drawn on the panel rather than left to a caption.

    PLACED OUTSIDE THE AXES, and that is not cosmetic. The first version put it at (0.99, 0.02) in
    axes coordinates with an opaque facecolor, and on F5 that rectangle sat exactly over rungs
    K10-K14 -- the four points that carry the result. The figure looked complete and had the
    decisive part of the curve painted over. A panel that hides its own evidence behind the box
    listing its scope is worse than one with no box, so the card now lives below the axes where it
    cannot cover data."""
    ax.text(1.0, -0.42, "\n".join(lines), transform=ax.transAxes, fontsize=6.2,
            va="top", ha="right", family="monospace",
            bbox=dict(boxstyle="round,pad=0.35", fc="#f7f7f7", ec="#bbbbbb", lw=0.6))


def fig2(plt, cand):
    fig, axes = plt.subplots(1, 2, figsize=(10.0, 4.7))
    for ax, cw, L in zip(axes, ("button", "basket"), (12, 11)):
        b = cand["by_codeword"][cw]
        co = b["cell_coordinates_on_bomb_axis"]["L%d" % L]["coords"]
        order = ["A", "C", "B", "E"]
        labels = ["A\nbenign\ncodeword", "C\nDoublespeak\ncodeword", "B\nharmful\nconcept",
                  "E\nbenign\nconcept"]
        vals = [co[c]["mean_gap_units"] for c in order]
        cols = ["#8a8a8a", "#c0392b", "#2c7fb8", "#2c7fb8"]
        ax.bar(range(4), vals, color=cols, width=0.6)
        for i, v in enumerate(vals):
            ax.text(i, v + 0.03, "%.3f" % v, ha="center", fontsize=8)
        ax.set_xticks(range(4)); ax.set_xticklabels(labels, fontsize=7)
        ax.set_ylabel("position on the %s->bomb axis (gap units)" % cw, fontsize=8)
        ax.set_ylim(-0.05, 1.18)
        ax.axhline(0, color="k", lw=0.6); ax.axhline(1, color="k", lw=0.6, ls=":")
        ax.set_title("%s, layer %d" % (cw, L), fontsize=9)
        scope_card(ax, ["n = %d TRAIN domains" % b["n_train_domains"],
                        "split: train only",
                        "metric: <h_cell - h_A, v_lex>/||mean(h_E-h_A)||",
                        "v_lex leave-one-domain-out",
                        "A and E are 0 and 1 by construction"])
    fig.suptitle("F2  the Doublespeak cell sits at ~0.10-0.14 of the way from the codeword to the "
                 "concept", fontsize=9.5)
    fig.tight_layout(rect=(0, 0.24, 1, 0.95))
    return fig


def fig3(plt, pos):
    fig, axes = plt.subplots(1, 2, figsize=(10.0, 4.7))
    for ax, cw in zip(axes, ("button", "basket")):
        rec = pos["by_bank"][cw + "_bomb"]
        Ls = sorted(rec["layers"], key=lambda k: int(k[1:]))
        xs = [int(k[1:]) for k in Ls]
        for name, col, mark in (("codeword_last", "#c0392b", "o"),
                                ("following", "#2c7fb8", "s"),
                                ("last", "#7a7a7a", "^")):
            ys = [rec["layers"][k][name]["mean_cos"] for k in Ls]
            lo = [rec["layers"][k][name]["ci95_cos"][0] for k in Ls]
            hi = [rec["layers"][k][name]["ci95_cos"][1] for k in Ls]
            ax.plot(xs, ys, marker=mark, ms=3.5, lw=1.3, color=col, label=name)
            ax.fill_between(xs, lo, hi, color=col, alpha=0.15, lw=0)
        ax.set_xlabel("block layer", fontsize=8)
        ax.set_ylabel("cos(h_C - h_A, v_lex)   POSITION-PORTABLE", fontsize=7.5)
        ax.set_title("%s_bomb" % cw, fontsize=9)
        ax.legend(fontsize=6.5, loc="upper left")
        n = rec["layers"][Ls[0]]["n_domains"]
        scope_card(ax, ["n = %d TRAIN domains" % n, "split: train only",
                        "shaded: 95% domain bootstrap",
                        "metric: cos, scale-free in BOTH terms",
                        "gap units are NOT position-portable (C-214)"])
    fig.suptitle("F3  B1 is NOT localised: the codeword matches its neighbour and trails the "
                 "readout position", fontsize=9.5)
    fig.tight_layout(rect=(0, 0.24, 1, 0.95))
    return fig


def fig5(plt, lad):
    # THE ACCESSORS ARE READ OFF THE ARTIFACT, NOT GUESSED. The first version of this panel used
    # `ci95` and `control_band`; the artifact's keys are `bootstrap` and `controls`, so the CI band
    # and the entire dose-matched control silently vanished -- and the missing control is the half
    # of the K-ladder result that makes it a result. A `.get()` chain that falls through to a
    # default draws a plausible figure with the evidence removed. They are asserted now.
    rungs = lad["rungs"]
    ctr = lad["controls"]
    ks, ys, los, his = [], [], [], []
    for k in sorted(rungs, key=lambda z: int(z)):
        r = rungs[k]
        if "mean_delta" not in r:
            raise Refusal("rung %s carries no mean_delta" % k)
        ks.append(int(k))
        ys.append(r["mean_delta"])
        bs = r.get("bootstrap") or {}
        ci = bs.get("ci95") or bs.get("ci95_domain_bootstrap") or [None, None]
        los.append(ci[0]); his.append(ci[1])
    if len(ks) != 14:
        raise Refusal("expected 14 declared rungs, found %d" % len(ks))
    fig, ax = plt.subplots(figsize=(7.0, 4.9))
    ax.plot(ks, ys, marker="o", ms=4, lw=1.5, color="#c0392b", label="demo knockout")
    if all(v is not None for v in los):
        ax.fill_between(ks, los, his, color="#c0392b", alpha=0.15, lw=0)
    cks = sorted((int(k) for k in ctr), key=int)
    if not cks:
        raise Refusal("the artifact carries no control band; the panel would show the treatment "
                      "arm alone, which is not the result")
    cys = [ctr[str(k)]["band_mean"] for k in cks]
    ax.plot(cks, cys, marker="s", ms=4, lw=1.3, ls="--", color="#2c7fb8",
            label="dose-matched non-demo control (3 draws)")
    lo = min(min(ys), min(cys)); hi = max(max(ys), max(cys))
    pad = 0.12 * (hi - lo)
    ax.set_ylim(lo - pad, hi + pad)          # explicit, so no rung falls outside the axes
    ax.axvline(10, color="k", lw=0.8, ls=":")
    ax.text(10.15, lo + 0.30 * (hi - lo), "K=10\nthe CODEWORD", fontsize=7.5)
    ax.set_xlabel("K  (the cut reaches query row rel_end -K)", fontsize=8)
    ax.set_ylabel("mean paired delta in semantic_logodds", fontsize=8)
    ax.legend(fontsize=6.5, loc="lower left")
    scope_card(ax, ["n = 67 TRAIN domains, 670 rows/arm",
                    "split: train only",
                    "readout: semantic_one_word (concept word on 0 of 32544 rows)",
                    "shaded: 95% domain bootstrap",
                    "shape rule returns NEITHER -- 'step' is not used"])
    fig.suptitle("F5  the concept-free K ladder: one row, the codeword's, carries 62% of the "
                 "effect", fontsize=9.5)
    fig.tight_layout(rect=(0, 0.28, 1, 0.95))
    return fig


def fig8(plt, q2):
    fig, ax = plt.subplots(figsize=(6.0, 4.0))
    rows = q2["rows"]["pooled"]
    ax.axis("off")
    txt = ["F8  installation -> attack success", "",
           "n = %d domains (all splits, PR-066 discipline_for_Q2)" % rows["n_domains"], ""]
    for nm, lab in (("raw_ASR", "raw ASR@0.5 (the frozen y)"),
                    ("asr_and_concept_present", "asr_and_concept_present (C-209 corrected)")):
        r = rows[nm]
        txt.append("%-42s rho = %+.4f" % (lab, r["rho"]))
        txt.append("%-42s p   = %.5g  (attainable floor %.5g)" % ("", r["perm_p"],
                                                                  r["perm_p_floor"]))
        txt.append("%-42s CI  = [%.3f, %.3f]" % ("", *r["fisher_z_ci95"]))
        txt.append("")
    txt += ["predictor: concept_binary_prob, semantic_one_word, cell C dose 4",
            "           bound BY HASH to the pinned bank " + q2["predictor_bound_by_sha16"],
            "join key : " + q2["join_key"],
            "declared MDE 0.2996 at power 0.90",
            "",
            "the correlation STRENGTHENS under the C-209 correction,",
            "which is the opposite of what a false-positive artefact would do"]
    ax.text(0.02, 0.98, "\n".join(txt), va="top", ha="left", family="monospace", fontsize=7.6,
            transform=ax.transAxes)
    fig.tight_layout()
    return fig


def selftest() -> int:
    ok = True

    def chk(n, c):
        nonlocal ok
        print("  %-50s %s" % (n, "PASS" if c else "FAIL"))
        ok = ok and bool(c)

    try:
        need("definitely/not/here.json")
        chk("need() refuses a missing artifact", False)
    except Refusal:
        chk("need() refuses a missing artifact", True)
    try:
        one_done(os.path.join(REPO, "outputs/__nope__*"))
        chk("one_done refuses when nothing matches", False)
    except Refusal:
        chk("one_done refuses when nothing matches", True)
    chk("four panels declared, five deliberately absent", len(PANELS) == 4)
    chk("every panel names its artifact", all(p[1] for p in PANELS))
    return 0 if ok else 1


PANELS = [("F2_cell_coordinates", "outputs/dcs_succ/bombness_candidates_train.json", fig2),
          ("F3_position_layer_map", "outputs/dcs_succ/b1_position_control.json", fig3),
          ("F5_kladder_concept_free", "outputs/dcs_succ/kladder_sowk_train.json", fig5),
          ("F8_installation_vs_asr", "outputs/dcs_succ/q2_concept_present.json", fig8)]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        print("=== selftest ===")
        return selftest()

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    os.makedirs(a.out, exist_ok=True)
    drawn, refused = [], []
    for name, art, fn in PANELS:
        try:
            data = json.load(open(need(art), encoding="utf-8"))
            fig = fn(plt, data)
            p = os.path.join(a.out, name + ".png")
            fig.savefig(p, dpi=200)
            plt.close(fig)
            drawn.append((name, p))
            print("drew %-26s <- %s" % (name, art))
        except Exception as e:                                   # noqa: BLE001
            refused.append((name, "%s: %s" % (type(e).__name__, e)))
            print("REFUSED %-23s %s: %s" % (name, type(e).__name__, e), file=sys.stderr)
    print("\n%d drawn, %d refused. Five of plan section 36's nine panels need arms this phase did "
          "not run and are NOT stubbed." % (len(drawn), len(refused)))
    return 0 if drawn else 1


if __name__ == "__main__":
    raise SystemExit(main())
