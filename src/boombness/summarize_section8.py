"""summarize_section8.py — plan §8's five named plots, none of which existed.

Plan §8 requires `boombness_vs_n_examples`, `asr_vs_n_examples`, `refusal_vs_n_examples`,
`comprehension_vs_n_examples` and `boombness_and_asr_by_strength`. This produces all five from
committed artifacts, with domain-clustered error bars throughout (the unit of inference is the
DOMAIN, not the prompt).

TWO THINGS IT DOES DIFFERENTLY FROM THE COMMITTED §8 ARTIFACT
-------------------------------------------------------------
1. **Comprehension comes from the WHOLE-ANSWER run.** `g8_comprehension_by_nexamples.json` is
   computed from `score_behavior/base_20260816_203355_3985444`, whose comprehension readout scored
   two single tokens holding a median 4.4e-05 of the next-token mass (R-6). Any curve drawn from it
   is a curve through a 1e-5 tail. This script reads the `--wa-score` run instead, where the options
   hold ~30% of the answer probability, and REFUSES to plot comprehension if that run's median
   `option_mass` is below `--min-option-mass`.

2. **The `strength` panel is drawn with its own disclaimer baked into the figure.** Plan §8 asks for
   `boombness_and_asr_by_strength`, but `strength` is one of the three §4.1 factors that N12 shows
   cannot support inference: 12 behavioural rows per level, and every non-default level moves prompt
   length, codeword-occurrence count and `n_examples` simultaneously (`strength` takes `n_examples`
   from 4.91 to 2.00, and `n_examples` is itself an ASR predictor). Drawing it silently would put a
   confounded, underpowered comparison in a report figure. It is drawn, labelled, and annotated.

REUSE: `cluster_mean_ci` from analyze_g8; the judge/extract join validated in summarize_section9.
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import statistics as st
import subprocess
import sys
from typing import Dict, List

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from analyze_g8 import cluster_mean_ci  # noqa: E402
from summarize_section9 import HEADLINE, load_rows, verify_join  # noqa: E402

LEVELS = [0, 1, 2, 4, 8, 16]


def curve(rows: List[dict], value_key: str, level_key: str = "n_examples",
          cond: str = None) -> Dict[int, dict]:
    out = {}
    for lv in LEVELS:
        sel = [r for r in rows
               if r.get(level_key) == lv and r.get(value_key) is not None
               and (cond is None or r.get("condition") == cond)]
        if not sel:
            continue
        byd = collections.defaultdict(list)
        for r in sel:
            byd[r.get("domain")].append(float(r[value_key]))
        s = cluster_mean_ci({k: v for k, v in byd.items() if v})
        out[lv] = {"n": len(sel), "mean": s["mean"], "ci": s["ci"],
                   "n_domains": s["n_clusters"], "degenerate": s.get("degenerate", False)}
    return out


def _errbar(ax, cur, label, color):
    xs = sorted(cur)
    ys = [cur[x]["mean"] for x in xs]
    lo = [cur[x]["mean"] - (cur[x]["ci"][0] if cur[x]["ci"] else cur[x]["mean"]) for x in xs]
    hi = [(cur[x]["ci"][1] if cur[x]["ci"] else cur[x]["mean"]) - cur[x]["mean"] for x in xs]
    ax.errorbar(range(len(xs)), ys, yerr=[lo, hi], marker="o", capsize=3, label=label, color=color)
    ax.set_xticks(range(len(xs)))
    ax.set_xticklabels([str(x) for x in xs])
    for i, x in enumerate(xs):
        ax.annotate(f"n={cur[x]['n']}", (i, ys[i]), textcoords="offset points",
                    xytext=(0, -12), fontsize=6, ha="center", color="#666")
    return xs


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--judge", required=True)
    ap.add_argument("--extract", required=True)
    ap.add_argument("--wa-score", required=True,
                    help="a whole-answer score_behavior run, for the comprehension curve")
    ap.add_argument("--min-option-mass", type=float, default=0.05)
    ap.add_argument("--outdir", default="outputs/boombness/section8")
    a = ap.parse_args()

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    rows = load_rows(a.judge, a.extract)
    check = verify_join(rows)
    print(f"[s8] join check: n={check['n']} rho={check['rho']!r} "
          f"reproduces={check['reproduces_g2_artifact']}")
    if not check["reproduces_g2_artifact"]:
        raise SystemExit("[s8] REFUSING: the join does not reproduce g2_analysis_cwpos.json.")

    wa = [json.loads(l) for l in open(os.path.join(a.wa_score, "results.jsonl"))]
    # The comprehension rows carry `comprehension_logodds`, NOT `semantic_logodds` -- the two query
    # kinds write different keys. The first version of this filter asked for the wrong one and got
    # zero rows, which the option-mass gate then dutifully reported as "median 0.0000 -> REFUSED".
    # A guard that fires because the data was not found is indistinguishable from one that fires
    # because the data is bad, so the emptiness is now checked and named separately.
    COMP_KEY = "comprehension_logodds"
    comp = [r for r in wa if r.get("query_kind") == "comprehension_usage"
            and r.get(COMP_KEY) is not None]
    if not comp:
        raise SystemExit(
            f"[s8] no comprehension_usage rows carrying {COMP_KEY!r} in {a.wa_score}. "
            f"Refusing to report 'option mass 0.0' for an empty set -- that is a missing-data "
            f"error, not an instrument verdict.")
    masses = sorted(float(r["option_mass"]) for r in comp if r.get("option_mass") is not None)
    med_mass = masses[len(masses) // 2] if masses else 0.0
    comp_ok = med_mass >= a.min_option_mass
    print(f"[s8] comprehension rows={len(comp)} median option_mass={med_mass:.4f} "
          f"-> {'PLOTTING' if comp_ok else 'REFUSED'}")

    plots = os.path.join(a.outdir, "plots")
    os.makedirs(plots, exist_ok=True)
    made, res = [], {"plan_section": "8", "join_check": check,
                     "comprehension_median_option_mass": med_mass,
                     "comprehension_plotted": comp_ok, "curves": {}}
    ARM = "natural_doublespeak"

    for key, ylab, fname, colour in (
            ("boombness", f"Boombness ({HEADLINE})", "boombness_vs_n_examples.png", "#2f6f9f"),
            ("asr_score", "StrongReject score", "asr_vs_n_examples.png", "#b5442e"),
            ("refused", "refusal rate", "refusal_vs_n_examples.png", "#6a7f4f")):
        r2 = [dict(r, refused=(1.0 if r.get("refused") else 0.0)) for r in rows] \
            if key == "refused" else rows
        cur = curve(r2, key, cond=ARM)
        res["curves"][key] = cur
        fig, ax = plt.subplots(figsize=(6, 4))
        _errbar(ax, cur, ARM, colour)
        ax.set_xlabel("number of demonstrations (`n_examples`)")
        ax.set_ylabel(ylab)
        ax.set_title(f"{ylab} vs demonstration count — {ARM}\n"
                     "error bars are DOMAIN-clustered (6 clusters), not iid")
        fig.tight_layout(); p = os.path.join(plots, fname)
        fig.savefig(p, dpi=150); plt.close(fig); made.append(p)

    # comprehension, from the whole-answer run only
    fig, ax = plt.subplots(figsize=(6, 4))
    if comp_ok:
        cur = curve(comp, COMP_KEY)
        res["curves"]["comprehension"] = cur
        _errbar(ax, cur, "comprehension log-odds", "#7a5aa0")
        ax.set_ylabel("comprehension log-odds (coded vs literal)")
        ax.set_title("Comprehension vs demonstration count — WHOLE-ANSWER readout\n"
                     f"median option mass {med_mass:.3f} (the superseded readout was 4.4e-05)")
    else:
        ax.text(0.5, 0.5, "REFUSED\nmedian option mass %.2g < %.2g\nthe readout is not a forced choice"
                % (med_mass, a.min_option_mass), ha="center", va="center", fontsize=11, color="#b5442e")
        ax.set_axis_off()
    ax.set_xlabel("number of demonstrations (`n_examples`)")
    fig.tight_layout(); p = os.path.join(plots, "comprehension_vs_n_examples.png")
    fig.savefig(p, dpi=150); plt.close(fig); made.append(p)

    # strength panel, drawn with its disclaimer in the figure
    byst = collections.defaultdict(lambda: {"b": [], "a": []})
    for r in rows:
        stg = r.get("strength")
        if stg and r.get("boombness") is not None and r.get("asr_score") is not None:
            byst[stg]["b"].append(r["boombness"]); byst[stg]["a"].append(r["asr_score"])
    order = [s for s in ("none", "weak", "medium", "strong", "aggressive") if s in byst]
    res["curves"]["by_strength"] = {k: {"n": len(v["b"]),
                                        "boombness_mean": st.mean(v["b"]) if v["b"] else None,
                                        "asr_mean": st.mean(v["a"]) if v["a"] else None}
                                    for k, v in byst.items()}
    fig, axes = plt.subplots(1, 2, figsize=(9, 4))
    for ax, k, lab, c in ((axes[0], "b", f"Boombness ({HEADLINE})", "#2f6f9f"),
                          (axes[1], "a", "StrongReject score", "#b5442e")):
        ax.bar(range(len(order)), [st.mean(byst[s][k]) for s in order], color=c)
        ax.set_xticks(range(len(order))); ax.set_xticklabels(order, rotation=20, fontsize=8)
        ax.set_ylabel(lab)
        for i, s in enumerate(order):
            ax.annotate(f"n={len(byst[s][k])}", (i, 0), textcoords="offset points",
                        xytext=(0, 4), fontsize=7, ha="center", color="white")
    fig.suptitle("Boombness and ASR by `strength` — ⚠ NOT AN INFERENCE (see N12)\n"
                 "12 behavioural rows per non-default level; `strength` also moves prompt length, "
                 "codeword-occurrence count\nand n_examples (4.91→2.00) simultaneously. Drawn because "
                 "plan §8 names it; not to be read as an effect.", fontsize=8)
    fig.tight_layout(rect=(0, 0, 1, 0.86))
    p = os.path.join(plots, "boombness_and_asr_by_strength.png")
    fig.savefig(p, dpi=150); plt.close(fig); made.append(p)

    try:
        git = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
        dirty = bool(subprocess.run(["git", "status", "--porcelain"], capture_output=True,
                                    text=True).stdout.strip())
    except Exception:
        git, dirty = None, None
    res["plots"] = [os.path.abspath(x) for x in made]
    res["sources"] = {"judge": os.path.abspath(a.judge), "extract": os.path.abspath(a.extract),
                      "wa_score": os.path.abspath(a.wa_score)}
    res["provenance"] = {"argv": sys.argv, "git_commit": git, "git_dirty": dirty,
                         "python": sys.executable}
    with open(os.path.join(a.outdir, "section8_summary.json"), "w") as f:
        json.dump(res, f, indent=1)
    for x in made:
        print(f"[s8] plot -> {x}")
    print(f"[s8] -> {os.path.join(a.outdir, 'section8_summary.json')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
