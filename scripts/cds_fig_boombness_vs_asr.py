#!/usr/bin/env python
"""cds_fig_boombness_vs_asr.py -- `CDS-PR-005`'s figure. CPU only, no new data.

REUSES `src/boombness/analyze_phase_d.py` -- `build_metrics`, `level_of`, `within_domain_rho`,
`spearman` -- rather than re-deriving anything. A figure that recomputes its own version of a
published statistic is how a plot and a paper come to disagree.

WHAT THE FIGURE HAS TO SHOW, and why it is three panels rather than one scatter. This project has
already RETRACTED a Boombness-vs-ASR correlation (`G2`): the row set mixed sibling families, which
share demonstrations, with experimentally manipulated designed variance, and on the 90 clean prompts
the within-domain rho was -0.052, p=0.658. The `phase_d` bank exists to make the question askable.
Its answer is not "yes" or "no" -- it is that the association lives BETWEEN the designed levels and
largely not WITHIN them, and a single pooled scatter shows the opposite of that. So:

  A  pooled -- Boombness decile vs observed attack rate, with domain-cluster intervals.  The
     apparent relationship.
  B  the same, WITHIN each designed level.  Where it mostly goes.
  C  level means -- one point per manipulation level.  Where it actually lives.

Honest n is 120 INDEPENDENT FAMILIES per level (a family is domain|split|stem, 15 levels x 120),
never 1800 rows; clustering is on domain (6).
"""
from __future__ import annotations
import argparse, collections, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src", "boombness"))
import analyze_phase_d as APD  # noqa: E402

SCHEMA = "CDS_FIG_BOOMBNESS_VS_ASR/1"
#: The metric `analyze_phase_d` SELECTED ON DEV for d_surface x malicious_at_0.5. Frozen here so the
#: figure cannot become a search over 210 candidate metrics.
METRIC = "demo_max|L29|cos"
DIRECTION = "d_surface"
OUTCOME = "malicious_at_0.5"

# --- palette: sequential single hue for magnitude, two-hue categorical for outcome identity.
INK, INK2, MUTED = "#1f2328", "#4a5057", "#8b9199"
GRID, SURF = "#e6e8eb", "#ffffff"
C_POOLED = "#2f6f9f"      # one hue, the pooled series
C_LEVEL = "#c46a2f"       # the second identity: level means
C_ATTACK, C_NOATTACK = "#b4453a", "#5d7f8c"


def load(extract_dir, judge_dirs, condition):
    ex = [json.loads(l) for l in open(os.path.join(extract_dir, "results.jsonl"))]
    ex = [r for r in ex if r.get("condition") == condition]
    out, dom, lev, spl, fam = {}, {}, {}, {}, {}
    for jd in judge_dirs:
        for l in open(os.path.join(jd, "results.jsonl")):
            r = json.loads(l)
            if r.get("condition") != condition or r.get("judge_status") not in (None, "ok"):
                continue
            out[r["prompt_id"]] = int(bool(r.get(OUTCOME)))
    for r in ex:
        p = r["prompt_id"]
        dom[p] = r.get("domain"); lev[p] = APD.level_of(r); spl[p] = str(r.get("split"))
        fam[p] = "|".join(str(r.get("family_id")).split("|")[:3])
    met = APD.build_metrics(ex, DIRECTION)
    pids = sorted(set(met) & set(out))
    return pids, met, out, dom, lev, spl, fam


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / d
    return (max(0.0, c - h), min(1.0, c + h))


def cluster_ci(pairs, domains, reps=4000, seed=20260901):
    """Domain-cluster bootstrap on an attack rate. `pairs` = [(domain, outcome), ...]."""
    import random
    rng = random.Random(seed)
    by = collections.defaultdict(list)
    for d, y in pairs:
        by[d].append(y)
    keys = list(by)
    if not keys:
        return (0.0, 0.0)
    vals = []
    for _ in range(reps):
        pick = [by[rng.choice(keys)] for _ in keys]
        n = sum(len(v) for v in pick)
        if n:
            vals.append(sum(sum(v) for v in pick) / n)
    vals.sort()
    return (vals[int(0.025 * len(vals))], vals[int(0.975 * len(vals)) - 1])


def deciles(xs, q=6):
    s = sorted(xs)
    return [s[int(round(i * (len(s) - 1) / q))] for i in range(1, q)]


def binned(pids, met, out, dom, q=6):
    xs = [met[p][METRIC] for p in pids]
    cuts = deciles(xs, q)
    def which(v):
        for i, c in enumerate(cuts):
            if v <= c:
                return i
        return len(cuts)
    b = collections.defaultdict(list)
    for p in pids:
        b[which(met[p][METRIC])].append(p)
    rows = []
    for i in sorted(b):
        ps = b[i]
        k = sum(out[p] for p in ps)
        lo, hi = cluster_ci([(dom[p], out[p]) for p in ps], dom)
        rows.append({"bin": i, "n": len(ps), "attacks": k, "rate": k / len(ps),
                     "x": sum(met[p][METRIC] for p in ps) / len(ps),
                     "ci": [lo, hi], "wilson": list(wilson(k, len(ps)))})
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--extract", default="outputs/boombness/extract_boombness/"
                                         "phaseD_extract_20260820_201555_2809154")
    ap.add_argument("--judge-glob", default="outputs/boombness/judge/pdJ")
    ap.add_argument("--split", default="heldout", choices=["heldout", "dev", "both"])
    ap.add_argument("--condition", default="natural_doublespeak")
    ap.add_argument("--out-png", default="reports/CDS_FIG_boombness_vs_asr.png")
    ap.add_argument("--out-json", default="outputs/boombness/cds_analysis/"
                                          "cds_fig_boombness_vs_asr.json")
    a = ap.parse_args()
    import glob
    jds = sorted(d for d in glob.glob(os.path.join(ROOT, a.judge_glob + "*"))
                 if os.path.exists(os.path.join(d, "DONE.json")))
    if not jds:
        raise SystemExit("REFUSING: no completed judge shards matched %r" % a.judge_glob)
    pids, met, out, dom, lev, spl, fam = load(os.path.join(ROOT, a.extract), jds, a.condition)
    if a.split != "both":
        pids = [p for p in pids if spl[p] == a.split]
    pids = [p for p in pids if METRIC in met[p]]
    if not pids:
        raise SystemExit("REFUSING: 0 rows after filtering; the metric or split is wrong.")

    n_fam = len({fam[p] for p in pids})
    n_dom = len({dom[p] for p in pids})
    levels = sorted({lev[p] for p in pids})

    pooled = binned(pids, met, out, dom)
    per_level = {}
    for L in levels:
        ps = [p for p in pids if lev[p] == L]
        k = sum(out[p] for p in ps)
        per_level[L] = {
            "n": len(ps), "attacks": k, "rate": k / len(ps),
            "mean_boombness": sum(met[p][METRIC] for p in ps) / len(ps),
            "rho_within_level": APD.spearman([met[p][METRIC] for p in ps],
                                             [out[p] for p in ps]),
            "n_families": len({fam[p] for p in ps})}
    wd = APD.within_domain_rho({d: ([met[p][METRIC] for p in pids if dom[p] == d],
                                    [out[p] for p in pids if dom[p] == d])
                               for d in sorted({dom[p] for p in pids})})
    pooled_rho = APD.spearman([met[p][METRIC] for p in pids], [out[p] for p in pids])
    lv = [(v["mean_boombness"], v["rate"]) for v in per_level.values()]
    between_rho = APD.spearman([x for x, _ in lv], [y for _, y in lv])
    within_level_mean = (sum(v["rho_within_level"] for v in per_level.values()
                             if v["rho_within_level"] is not None)
                         / max(1, sum(1 for v in per_level.values()
                                      if v["rho_within_level"] is not None)))

    art = {"schema": SCHEMA, "metric": METRIC, "direction": DIRECTION, "outcome": OUTCOME,
           "split": a.split, "condition": a.condition,
           "extract": a.extract, "judge_shards": [os.path.basename(d) for d in jds],
           "n_rows": len(pids), "n_independent_families": n_fam, "n_domains": n_dom,
           "n_levels": len(levels),
           "pooled_rho": pooled_rho, "within_domain": wd,
           "between_level_rho": between_rho, "within_level_mean_rho": within_level_mean,
           "pooled_bins": pooled, "per_level": per_level}
    pj = os.path.join(ROOT, a.out_json)
    os.makedirs(os.path.dirname(pj), exist_ok=True)
    json.dump(art, open(pj, "w"), indent=1)

    print("rows=%d  independent families=%d  domains=%d  levels=%d"
          % (len(pids), n_fam, n_dom, len(levels)))
    print("pooled rho              = %+.4f" % pooled_rho)
    print("within-DOMAIN mean rho  = %+.4f  (95%% CI %s, p=%.4g)"
          % (wd["mean_rho"], [round(x, 4) for x in wd["ci95"]], wd["p_vs_0"]))
    print("BETWEEN-level rho       = %+.4f   (%d levels)" % (between_rho, len(levels)))
    print("WITHIN-level mean rho   = %+.4f" % within_level_mean)
    return art, a




# --------------------------------------------------------------------------- plotting
def render(art, out_png):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update({
        "figure.facecolor": SURF, "axes.facecolor": SURF,
        "font.size": 9, "axes.titlesize": 10, "axes.labelsize": 9,
        "axes.edgecolor": GRID, "axes.labelcolor": INK2,
        "xtick.color": MUTED, "ytick.color": MUTED,
        "text.color": INK, "axes.grid": True, "grid.color": GRID,
        "grid.linewidth": 0.6, "axes.axisbelow": True})

    fig, axes = plt.subplots(1, 3, figsize=(15.0, 4.9),
                             gridspec_kw={"width_ratios": [1.0, 1.05, 1.0]})
    fig.subplots_adjust(left=0.052, right=0.988, top=0.795, bottom=0.175, wspace=0.42)

    # ---- A: pooled, binned
    ax = axes[0]
    b = art["pooled_bins"]
    xs = [r["x"] for r in b]; ys = [r["rate"] for r in b]
    lo = [max(0, r["rate"] - r["ci"][0]) for r in b]
    hi = [max(0, r["ci"][1] - r["rate"]) for r in b]
    ax.errorbar(xs, ys, yerr=[lo, hi], fmt="o", ms=8, lw=0, elinewidth=2,
                capsize=0, color=C_POOLED, ecolor=C_POOLED, alpha=0.95,
                markeredgecolor=SURF, markeredgewidth=2, zorder=3)
    ax.plot(xs, ys, lw=2, color=C_POOLED, alpha=0.35, zorder=2)
    for i, r in enumerate(b):
        ha = "left" if i == 0 else ("right" if i == len(b) - 1 else "center")
        dx = 6 if i == 0 else (-6 if i == len(b) - 1 else 0)
        dy = 5 if i % 2 == 0 else 15          # stagger: adjacent bins sit close on x
        ax.annotate("%d/%d" % (r["attacks"], r["n"]), (r["x"], r["ci"][1]),
                    textcoords="offset points", xytext=(dx, dy), ha=ha,
                    fontsize=7.5, color=MUTED)
    ax.set_title("A  Pooled: the apparent relationship", loc="left", color=INK, pad=8)
    ax.set_xlabel("Boombness  (%s, %s)" % (art["direction"], art["metric"]))
    ax.set_ylabel("observed attack rate")
    ax.set_ylim(-0.03, max(r["ci"][1] for r in b) * 1.30 + 0.04)
    ax.margins(x=0.10)
    ax.text(0.02, 0.95, "pooled $\\rho$ = %+.3f\nwithin-domain $\\rho$ = %+.3f  [%.2f, %.2f]"
            % (art["pooled_rho"], art["within_domain"]["mean_rho"],
               art["within_domain"]["ci95"][0], art["within_domain"]["ci95"][1]),
            transform=ax.transAxes, va="top", ha="left", fontsize=8, color=INK2)

    # ---- B: within-level rho, one dot per designed level
    ax = axes[1]
    items = sorted(((k, v) for k, v in art["per_level"].items()
                    if v["rho_within_level"] is not None),
                   key=lambda kv: kv[1]["rho_within_level"])
    yy = list(range(len(items)))
    ax.axvline(0, color=INK2, lw=1.2, zorder=1)
    ax.scatter([v["rho_within_level"] for _, v in items], yy, s=64, color=C_POOLED,
               edgecolor=SURF, linewidth=2, zorder=3)
    ax.axvline(art["within_level_mean_rho"], color=C_LEVEL, lw=2, ls="--", zorder=2)
    ax.set_yticks(yy); ax.set_yticklabels([k for k, _ in items], fontsize=8)
    ax.yaxis.tick_right()
    ax.set_ylim(-0.8, len(items) - 0.2)
    ax.set_title("B  Within each designed level: it mostly goes away",
                 loc="left", color=INK, pad=8)
    ax.set_xlabel("Spearman $\\rho$ (Boombness, attack) inside one level")
    ax.set_xlim(-0.75, 0.75)
    ax.text(0.02, 0.97, "mean = %+.3f\n%d of %d levels have outcome variance"
            % (art["within_level_mean_rho"], len(items), art["n_levels"]),
            transform=ax.transAxes, ha="left", va="top", fontsize=8, color=C_LEVEL)

    # ---- C: between levels
    ax = axes[2]
    lx = [v["mean_boombness"] for v in art["per_level"].values()]
    ly = [v["rate"] for v in art["per_level"].values()]
    names = list(art["per_level"].keys())
    ax.scatter(lx, ly, s=76, color=C_LEVEL, edgecolor=SURF, linewidth=2, zorder=3)
    order = sorted(range(len(ly)), key=lambda i: ly[i])
    for i in order[-3:]:
        ax.annotate(names[i], (lx[i], ly[i]), textcoords="offset points",
                    xytext=(-9, 2), ha="right", fontsize=7.5, color=INK2)
    ax.margins(x=0.16, y=0.14)
    ax.set_title("C  Between the levels: where it actually lives",
                 loc="left", color=INK, pad=8)
    ax.set_xlabel("mean Boombness of the level")
    ax.set_ylabel("attack rate of the level")
    ax.text(0.98, 0.05, "between-level $\\rho$ = %+.3f\n%d designed levels"
            % (art["between_level_rho"], art["n_levels"]),
            transform=ax.transAxes, va="bottom", ha="right", fontsize=8, color=INK2)

    fig.suptitle("Boombness and attack success are associated BETWEEN designed levels, "
                 "not within them", x=0.052, ha="left", y=0.958, fontsize=13.5, color=INK)
    fig.text(0.052, 0.900,
             "Llama-3.1-8B-Instruct · phase_d bank · natural_doublespeak · %s split · "
             "%d prompts = %d independent families over %d domains · judge pinned. "
             "Bars are domain-cluster bootstrap 95%% intervals."
             % (art["split"], art["n_rows"], art["n_independent_families"], art["n_domains"]),
             ha="left", fontsize=8.5, color=MUTED)
    fig.text(0.052, 0.055,
             "NOT a causal claim and NOT an objective. An earlier version of this correlation was "
             "RETRACTED (G2) for pooling sibling families that share demonstrations; only "
             "independent families are plotted here.",
             ha="left", fontsize=7.5, color=MUTED)
    fig.text(0.052, 0.020,
             "d_naive and d_context match or beat d_surface on the same data, so nothing here is "
             "specific to d_surface, and the 38-domain gate finds no transfer to unseen domains.",
             ha="left", fontsize=7.5, color=MUTED)
    for ax in axes:
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
    p = os.path.join(ROOT, out_png)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    fig.savefig(p, dpi=190)
    print("wrote", out_png)


if __name__ == "__main__":
    _art, _a = main()
    render(_art, _a.out_png)
