"""analyze_g11.py — plan §11's main question, at full power for the first time.

   "Does a more user-like or CoT-like presentation of the mapping increase final-carrot Boombness,
    or does it only increase ASR independently?"

WHY THIS COULD NOT BE ANSWERED BEFORE. Every role claim in this sprint rested on **6 prompts per
style per condition** — the extract run covered 120 of 720 role rows and the judge 60 of 360. The
full-coverage runs (roleblk / rolebeh) give **72 per style**, 36 per style per condition, over 6
domains.

THE DESIGN IS CROSSED, WHICH IS WHAT MAKES THIS ANSWERABLE. `family_id` embeds the style name, so a
naive stem comparison says the five styles share no families. Masking the style token out:
`final_query_text` AND `demo_block` are **byte-identical** across all five styles for 144/144 cells,
while `n_chars` differs — the role wrapper is applied at render time. That is exactly the plan's
Role-Confusion requirement ("identical neutral text snippets wrapped in different role tags/styles").

So every comparison here is WITHIN CONTENT STEM: the same demonstrations and the same final query,
differing only in the role wrapper. Prompt difficulty cancels by construction.

INFERENCE, applying this session's corrections:
  * the cluster is the DOMAIN (G=6) and the reference is t(G-1)=t(5), never normal (audit 10/11);
  * permutations are on GROUP-DEMEANED values, or they are not within-domain at all (audit A3/A11-3);
  * §9's identifiability rule applies: role is identified only AMONG the five styles, never against
    `plain`, which shares no families with any of them.
"""
from __future__ import annotations

import argparse
import collections
import json
import math
import os
import random
import statistics as st
import sys
from typing import Dict, List

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import read_jsonl, require_done  # noqa: E402
from analyze_g8 import t_sf, t_crit  # verified against six published critical values  # noqa: E402


def stem(fid: str, style: str) -> str:
    """Content identity: family_id with the style token masked out."""
    return (fid or "").replace(style or "\x00", "<STYLE>")


def cluster_mean_ci(by_cluster: Dict[str, List[float]]):
    means = [st.mean(v) for v in by_cluster.values() if v]
    G = len(means)
    if G < 2:
        return {"mean": means[0] if means else float("nan"), "se": None, "ci": None,
                "p": None, "n_clusters": G}
    m, sd = st.mean(means), st.stdev(means)
    if sd == 0:
        return {"mean": m, "se": 0.0, "ci": None, "p": None, "n_clusters": G,
                "degenerate": "between-cluster SD is 0"}
    se = sd / math.sqrt(G)
    tc = t_crit(G - 1)
    return {"mean": m, "se": se, "ci": [m - tc * se, m + tc * se],
            "p": t_sf(abs(m / se), G - 1), "n_clusters": G}


def perm_p_styles(vals_by_style_stem: Dict[str, Dict[str, float]], domains: Dict[str, str],
                  n_perm: int = 2000, seed: int = 20260818) -> float:
    """Omnibus: is there ANY difference among styles, holding content stem fixed?

    Statistic = spread (max-min) of the style means computed on WITHIN-STEM DEMEANED values.
    Permutation shuffles the style labels WITHIN each stem, which is the exact exchangeability the
    crossed design licenses.
    """
    stems = sorted({s for d in vals_by_style_stem.values() for s in d})
    styles = sorted(vals_by_style_stem)
    full = [s for s in stems if all(s in vals_by_style_stem[k] for k in styles)]
    if len(full) < 5:
        return float("nan")

    def spread(assign):
        acc = collections.defaultdict(list)
        for s in full:
            vals = [vals_by_style_stem[k][s] for k in styles]
            m = sum(vals) / len(vals)
            for k, v in zip(assign[s], vals):
                acc[k].append(v - m)          # within-stem demeaned
        mus = [st.mean(acc[k]) for k in styles if acc[k]]
        return max(mus) - min(mus)

    base = {s: list(styles) for s in full}
    obs = spread(base)
    rng = random.Random(seed)
    hits = 0
    for _ in range(n_perm):
        perm = {}
        for s in full:
            k = list(styles)
            rng.shuffle(k)
            perm[s] = k
        if spread(perm) >= obs:
            hits += 1
    return (hits + 1) / (n_perm + 1)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--extract", required=True, help="roleblk extract run")
    ap.add_argument("--judge", required=True, help="rolebeh judge run")
    ap.add_argument("--boombness-col", default="d_surface|L12|proj")
    ap.add_argument("--condition", default="natural_doublespeak")
    ap.add_argument("--cluster-by", default="domain")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    require_done(args.extract)
    require_done(args.judge)

    E = [r for r in read_jsonl(os.path.join(args.extract, "results.jsonl"))
         if r.get("is_final_occurrence")]
    J = [r for r in read_jsonl(os.path.join(args.judge, "results.jsonl"))
         if r.get("strongreject_score") is not None]

    jrow = {r["prompt_id"]: r for r in J if r.get("condition") == args.condition}
    erow = {r["prompt_id"]: r for r in E
            if r.get("condition") == args.condition and r.get("query_kind") == "behavioral"}
    pids = sorted(set(jrow) & set(erow))
    styles = sorted({jrow[p]["role_style"] for p in pids})
    print(f"[G11] condition={args.condition}  joined prompts={len(pids)}  styles={styles}")
    print(f"[G11]   judged={len(jrow)}  with-boombness={len(erow)}  "
          f"per style: {dict(collections.Counter(jrow[p]['role_style'] for p in pids))}")
    if len(pids) < 50:
        raise SystemExit(f"[G11] only {len(pids)} joined prompts — refusing")

    # ---- content stems: verify the crossed design actually holds in THIS join --------------- #
    by_style_stem_b: Dict[str, Dict[str, float]] = collections.defaultdict(dict)
    by_style_stem_a: Dict[str, Dict[str, float]] = collections.defaultdict(dict)
    dom_of_stem: Dict[str, str] = {}
    for p in pids:
        j, e = jrow[p], erow[p]
        stl = j["role_style"]
        s = stem(j.get("family_id"), stl)
        if e.get(args.boombness_col) is not None:
            by_style_stem_b[stl][s] = e[args.boombness_col]
        by_style_stem_a[stl][s] = j["strongreject_score"]
        dom_of_stem[s] = j.get(args.cluster_by)
    stems_all = sorted({s for d in by_style_stem_a.values() for s in d})
    complete = [s for s in stems_all if all(s in by_style_stem_a[k] for k in styles)]
    print(f"[G11] content stems: {len(stems_all)} total, {len(complete)} present in ALL "
          f"{len(styles)} styles -> crossed fraction {100*len(complete)/max(len(stems_all),1):.0f}%")
    if not complete:
        raise SystemExit("[G11] no stem is present in all styles — the design is not crossed here")

    report = {"plan_section": "11", "condition": args.condition, "styles": styles,
              "boombness_col": args.boombness_col, "n_prompts": len(pids),
              "n_stems_total": len(stems_all), "n_stems_crossed": len(complete),
              "extract": os.path.abspath(args.extract), "judge": os.path.abspath(args.judge),
              "identifiability": ("role is identified AMONG these styles (content byte-identical "
                                  "within stem); it is NOT identified against `plain`, which shares "
                                  "no families with any role style (§9)")}

    # ---- per-style, within-stem demeaned, clustered by domain ------------------------------ #
    print(f"\n[G11] within-stem demeaned means (cluster = {args.cluster_by}, t(G-1) CI):")
    print(f"{'style':22s} {'Boombness dev':>28s} {'ASR dev (score)':>28s}")
    per_style = {}
    for stl in styles:
        cells = {}
        for label, src in (("boombness", by_style_stem_b), ("asr_score", by_style_stem_a)):
            acc = collections.defaultdict(list)
            for s in complete:
                if s not in src[stl]:
                    continue
                vals = [src[k][s] for k in styles if s in src[k]]
                if len(vals) < len(styles):
                    continue
                acc[dom_of_stem[s]].append(src[stl][s] - sum(vals) / len(vals))
            cells[label] = cluster_mean_ci(acc)
        per_style[stl] = cells
        def fmt(c):
            if c.get("ci") is None:
                return f"{c['mean']:+.4f} (no CI)"
            return f"{c['mean']:+.4f} [{c['ci'][0]:+.4f},{c['ci'][1]:+.4f}] p={c['p']:.3f}"
        print(f"{stl:22s} {fmt(cells['boombness']):>28s} {fmt(cells['asr_score']):>28s}")
    report["per_style_within_stem"] = per_style

    # ---- omnibus permutation on style labels within stem ----------------------------------- #
    pb = perm_p_styles(by_style_stem_b, dom_of_stem)
    pa = perm_p_styles(by_style_stem_a, dom_of_stem)
    report["omnibus_perm_p"] = {"boombness": pb, "asr_score": pa}
    print(f"\n[G11] omnibus (style labels permuted WITHIN content stem, 2000 draws):")
    print(f"   Boombness: p = {pb:.4f}")
    print(f"   ASR score: p = {pa:.4f}")

    # ---- the plan's actual question: do the two move TOGETHER across styles? --------------- #
    mb = {k: per_style[k]["boombness"]["mean"] for k in styles}
    ma = {k: per_style[k]["asr_score"]["mean"] for k in styles}
    xs = [mb[k] for k in styles]
    ys = [ma[k] for k in styles]
    mx, my = st.mean(xs), st.mean(ys)
    den = math.sqrt(sum((v - mx) ** 2 for v in xs) * sum((v - my) ** 2 for v in ys))
    r = (sum((a - mx) * (b - my) for a, b in zip(xs, ys)) / den) if den else float("nan")
    report["style_level_corr_boombness_vs_asr"] = {"pearson_r": r, "n_styles": len(styles),
                                                   "caveat": "n=5 style means; descriptive only"}
    print(f"\n[G11] across the {len(styles)} style means: corr(Boombness dev, ASR dev) = {r:+.3f} "
          f"(n=5 — descriptive, no p)")

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w") as f:
        json.dump(report, f, indent=2)
    print(f"[G11] wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
