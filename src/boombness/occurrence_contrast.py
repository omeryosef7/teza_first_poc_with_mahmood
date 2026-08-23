"""occurrence_contrast.py — Δ(final occurrence − earlier occurrences), the analysis §19 Q2 quotes.

WHY THIS EXISTS. Q2 answers "does the final `carrot` become more `bomb`-like?" with a definite NO and
specific figures (L16 −0.154, t_cl −10.5; L8 −0.082; L31 −0.080; a `benign_literal` control at −0.105
and −0.131). On 2026-08-23 the §19 sourcing audit found those figures trace to **no committed
artifact**: every apparent numeric match was a float collision inside an unrelated large file, and the
nearest script (`followup_token_level.py`) computes per-ROLE means, not this paired contrast.

The answer was almost certainly right — its load-bearing part is a *control* argument, separately
supported in §7 — but "almost certainly right" is not the standard this report sets. So the contrast is
recomputed here from the committed extract run, and committed as an artifact.

THE ESTIMAND. Within prompt, same word, only position differs: mean(final occurrence) −
mean(earlier occurrences), for prompts with at least two occurrences. Prompt-level deltas are then
aggregated to DOMAIN cluster means and tested with t(G−1), because prompts within a domain share
material. Reported per layer, for the doublespeak condition and for `benign_literal` — the control that
settles the interpretation, since there is no bomb meaning there to be approached.

Numeric fields only.
"""
from __future__ import annotations

import argparse
import collections
import json
import math
import os
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from unanalysed_inventory import git_commit_safe  # noqa: E402

try:
    from scipy import stats as _st
except Exception:
    _st = None


def cluster_t(vals):
    """Mean of domain cluster means, with t(G-1) and a two-sided p."""
    g = len(vals)
    if g < 2:
        return None
    m = statistics.mean(vals)
    sd = statistics.stdev(vals)
    se = sd / math.sqrt(g)
    if se == 0:
        return {"mean": m, "se": 0.0, "t": None, "p": None, "n_domains": g}
    t = m / se
    p = (2 * _st.t.sf(abs(t), g - 1)) if _st is not None else None
    return {"mean": m, "se": se, "t": t, "p": p, "n_domains": g,
            "ci95": [m - 1.96 * se, m + 1.96 * se]}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run", required=True)
    ap.add_argument("--metric", default="d_surface")
    ap.add_argument("--readout", default="cos", choices=["cos","proj"],
                    help="cos is scale-normalised; the t is identical either way, the DELTA is not")
    ap.add_argument("--conditions", default="natural_doublespeak,benign_literal")
    ap.add_argument("--layers", default="8,16,31")
    # QUERY KIND IS NOT OPTIONAL. Pooling behavioral / comprehension_usage / semantic_one_word mixes
    # three different tasks, which is correction C7's complaint. §19 Q2 reports n=246 doublespeak
    # prompts, and `behavioral` alone gives exactly 246 -- pooling gives 480. Matching the stated n is
    # how the filter was identified.
    ap.add_argument("--query-kind", default="behavioral")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    layers = [int(x) for x in a.layers.split(",")]
    conds = a.conditions.split(",")
    # prompt -> condition/domain -> per-layer lists for final and earlier occurrences
    fin = collections.defaultdict(lambda: collections.defaultdict(list))
    ear = collections.defaultdict(lambda: collections.defaultdict(list))
    meta = {}
    n_rows = 0
    for line in open(os.path.join(a.run, "results.jsonl"), encoding="utf-8"):
        try:
            r = json.loads(line)
        except Exception:
            continue
        c = r.get("condition")
        if c not in conds:
            continue
        if a.query_kind and r.get("query_kind") != a.query_kind:
            continue
        if not r.get("n_occurrences") or r["n_occurrences"] < 2:
            continue          # a single-occurrence prompt has no within-prompt contrast
        n_rows += 1
        pid = r.get("prompt_id")
        meta[pid] = (c, r.get("domain"))
        tgt = fin if r.get("is_final_occurrence") else ear
        for L in layers:
            v = r.get(f"{a.metric}|L{L}|{a.readout}")
            if v is not None:
                tgt[pid][L].append(float(v))

    out_conds = {}
    for c in conds:
        per_layer = {}
        pids = [p for p in fin if meta.get(p, (None,))[0] == c and p in ear]
        for L in layers:
            by_dom = collections.defaultdict(list)
            used = 0
            for p in pids:
                f, e = fin[p].get(L), ear[p].get(L)
                if not f or not e:
                    continue
                by_dom[meta[p][1]].append(statistics.mean(f) - statistics.mean(e))
                used += 1
            dom_means = [statistics.mean(v) for v in by_dom.values() if v]
            st = cluster_t(dom_means)
            if st:
                st["n_prompts"] = used
            per_layer[f"L{L}"] = st
        out_conds[c] = {"n_prompts_with_2plus_occurrences": len(pids), "layers": per_layer}

    out = {
        "question": "does the FINAL occurrence of the codeword sit further along d_surface than "
                    "EARLIER occurrences of the same word in the same prompt?",
        "why": "§19 Q2 quotes this contrast, and the 2026-08-23 sourcing audit found its figures in no "
               "committed artifact. Recomputed here so the answer is verifiable rather than merely "
               "probably right.",
        "estimand": "within prompt: mean(final) - mean(earlier), prompts with >=2 occurrences; "
                    "prompt deltas aggregated to DOMAIN cluster means; t(G-1), two-sided",
        "control_logic": "benign_literal is the control that settles it -- there is no bomb meaning "
                         "there for a final occurrence to approach, so an effect of the same sign and "
                         "size means the contrast is positional, not semantic",
        "run": a.run, "metric": a.metric, "readout": a.readout, "query_kind": a.query_kind, "rows_used": n_rows,
        "conditions": out_conds,
        "provenance": {"argv": sys.argv, "git_commit": git_commit_safe()},
    }
    with open(a.out, "w") as f:
        json.dump(out, f, indent=2)

    for c, d in out_conds.items():
        print(f"== {c}  (prompts with >=2 occurrences: {d['n_prompts_with_2plus_occurrences']})")
        for L, st in d["layers"].items():
            if not st:
                print(f"   {L:<5} (insufficient clusters)")
                continue
            p = "n/a" if st["p"] is None else f"{st['p']:.4g}"
            print(f"   {L:<5} delta={st['mean']:+.4f}  t_cl={st['t']:+.2f}  p={p}  "
                  f"domains={st['n_domains']}  prompts={st['n_prompts']}")
    print(f"\n[occurrence] -> {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
