"""analyze_g2.py — does Boombness predict ASR? (plan §9). Committed, reproducible, gate-bearing.

THIS SCRIPT EXISTS BECAUSE THE FIRST G2 TABLE WAS COMPUTED AD HOC AND WAS WRONG.
The tick-16 audit found four defects in it, three of them result-corrupting, and the headline
verdict inverted once they were fixed. Every one traces to a join or a filter that was decided in
a throwaway shell heredoc and never written down:

  (1) THE PREDICTOR WAS READ OFF THE WRONG PROMPT. The join stripped `query_kind` from `family_id`,
      which is a sound key, but it silently pulled the representation from the `semantic_one_word`
      prompt while ASR came from the `behavioral` prompt. Those are different prompts with
      different final queries. The quantity that bears on a GCG objective is `d_surface` on the
      ATTACK prompt. Here the judge is joined to the extract on `prompt_id` DIRECTLY, and the
      script refuses to proceed if the query kinds disagree.

  (2) 72 OF 270 DOUBLESPEAK ROWS WERE SILENTLY DROPPED by that join, and not at random: the
      dropped set was entirely strength=none/consistent/near/plain with ASR 0.224 vs 0.176 and
      refusal 0.000 vs 0.101. Coverage is now reported explicitly and loudly.

  (3) 36 OF THE 198 ROWS HAD n_examples=0 — no demonstrations, therefore no codeword mapping,
      therefore not doublespeak prompts at all. That stratum alone had rho=+0.727 and was carrying
      the correlation. `--min-examples 1` is the default and the n=0 stratum is reported separately.

  (4) THREE OF FIVE COEFFICIENTS DID NOT REPRODUCE. Nothing in the repo could regenerate them.

Outputs a JSON report and prints the table, so the numbers in the log are traceable to a command.
"""
from __future__ import annotations

import argparse
import collections
import json
import math
import os
import sys
from typing import Dict, List, Optional, Sequence

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import read_jsonl  # noqa: E402


def spearman(x, y):
    from scipy.stats import spearmanr
    r = spearmanr(x, y)
    return float(r.statistic), float(r.pvalue)


def holm(pvals: Dict[str, float], alpha: float = 0.05) -> Dict[str, bool]:
    items = sorted(pvals.items(), key=lambda kv: kv[1])
    m, out, ok = len(items), {}, True
    for i, (k, p) in enumerate(items):
        ok = ok and (p <= alpha / (m - i))
        out[k] = ok
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--judge", required=True)
    ap.add_argument("--extract", required=True)
    ap.add_argument("--score", required=True, help="score_behavior run (for semantic log-odds)")
    ap.add_argument("--arm", default="natural_doublespeak")
    ap.add_argument("--min-examples", type=int, default=1,
                    help="drop n_examples<this; 0-demo prompts establish no mapping and are not "
                         "doublespeak prompts (audit finding 3)")
    ap.add_argument("--layers", default="4,8,11,12,16,18,20,24,28,31")
    ap.add_argument("--refusalness", default=None,
                    help="refusalness run dir; enables the §9 Q6/Q7 mediation analysis that "
                         "decides the §18 outcome label (A: Boombness is the story; C: refusal "
                         "suppression is the story and Boombness is a correlate)")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    J = read_jsonl(os.path.join(args.judge, "results.jsonl"))
    E = read_jsonl(os.path.join(args.extract, "results.jsonl"))
    S = read_jsonl(os.path.join(args.score, "results.jsonl"))
    layers = [int(x) for x in args.layers.split(",")]

    # ---- ASR, keyed by prompt_id (the attack prompt) --------------------------------- #
    asr = {r["prompt_id"]: r["strongreject_score"] for r in J
           if r.get("strongreject_score") is not None and r.get("condition") == args.arm}
    n_arm_total = len(asr)

    # ---- representation on the SAME prompt: join on prompt_id, assert query kind ----- #
    rep: Dict[str, Dict[int, float]] = {}
    qk_seen = collections.Counter()
    for r in E:
        if not r.get("is_final_occurrence") or r["prompt_id"] not in asr:
            continue
        qk_seen[r.get("query_kind")] += 1
        d = rep.setdefault(r["prompt_id"], {})
        for L in layers:
            for stat in ("cos", "proj"):
                c = f"d_surface|L{L}|{stat}"
                if c in r:
                    d[(L, stat)] = r[c]
        for L in layers:
            c = f"ll|L{L}|boombness"
            if c in r:
                d[(L, "ll")] = r[c]
    if set(qk_seen) - {"behavioral"}:
        raise SystemExit(
            f"representation rows came from query kinds {dict(qk_seen)} — the predictor must be "
            "read off the SAME prompt that was generated from and judged (audit finding 1)")

    # ---- semantic log-odds: only available on the semantic probe prompt -------------- #
    # Kept, but explicitly labelled as a DIFFERENT prompt, joined on the stripped family key.
    def fam_key(fid): return "|".join(fid.split("|")[:-1])
    sem_by_fam = {fam_key(r["family_id"]): r["semantic_logodds"] for r in S
                  if r.get("readout") == "semantic" and r.get("condition") == args.arm
                  and r.get("semantic_logodds") is not None}
    meta = {r["prompt_id"]: r for r in J if r["prompt_id"] in asr}

    keys = [p for p in asr if p in rep]
    n_examples = {p: meta[p].get("n_examples") for p in keys}
    kept = [p for p in keys if (n_examples[p] or 0) >= args.min_examples]
    zero = [p for p in keys if (n_examples[p] or 0) == 0]

    print(f"[G2] arm={args.arm}: {n_arm_total} judged prompts; {len(keys)} with a representation "
          f"({100*len(keys)/max(n_arm_total,1):.0f}% coverage); "
          f"{len(kept)} after --min-examples {args.min_examples}; {len(zero)} zero-demo dropped")
    if len(keys) < n_arm_total:
        print(f"[G2] WARNING: {n_arm_total - len(keys)} judged prompts have no representation row")

    y = [asr[p] for p in kept]
    report: Dict[str, object] = {
        "arm": args.arm, "judge": os.path.abspath(args.judge),
        "extract": os.path.abspath(args.extract), "score": os.path.abspath(args.score),
        "n_judged_in_arm": n_arm_total, "n_with_representation": len(keys),
        "n_analysed": len(kept), "n_zero_demo_excluded": len(zero),
        "min_examples": args.min_examples,
        "representation_query_kinds": dict(qk_seen),
    }

    rows = []
    pv = {}
    for L in layers:
        for stat in ("cos", "proj", "ll"):
            xs = [rep[p].get((L, stat)) for p in kept]
            if any(v is None for v in xs):
                continue
            r, p = spearman(xs, y)
            name = f"d_surface|L{L}|{stat}" if stat != "ll" else f"logit_lens|L{L}"
            rows.append((name, r, p, float(_sd(xs))))
            pv[name] = p
    # semantic predictor, on its own (different) prompt
    sem_keys = [p for p in kept if fam_key(meta[p]["family_id"]) in sem_by_fam]
    if sem_keys:
        xs = [sem_by_fam[fam_key(meta[p]["family_id"])] for p in sem_keys]
        ys = [asr[p] for p in sem_keys]
        r, p = spearman(xs, ys)
        rows.append((f"semantic_logodds (n={len(sem_keys)}, OTHER prompt)", r, p, float(_sd(xs))))
        pv["semantic_logodds"] = p

    rej = holm(pv)
    rows.sort(key=lambda t: -abs(t[1]))
    print(f"\n{'predictor':44s} {'rho':>8s} {'p':>10s} {'Holm':>6s} {'sd(x)':>9s}")
    for name, r, p, sd in rows:
        print(f"{name:44s} {r:>+8.3f} {p:>10.2e} {str(rej.get(name.split(' ')[0], '')):>6s} {sd:>9.4f}")
    report["predictors"] = [{"name": n, "spearman": r, "p": p, "sd": sd,
                             "holm_rejected": bool(rej.get(n.split(" ")[0], False))}
                            for n, r, p, sd in rows]

    if zero:
        yz = [asr[p] for p in zero]
        for L in (12, 31):
            xs = [rep[p].get((L, "cos")) for p in zero]
            if all(v is not None for v in xs):
                r, p = spearman(xs, yz)
                print(f"  [zero-demo stratum, n={len(zero)}] d_surface|L{L}|cos rho={r:+.3f} p={p:.2e}")

    # ---- §9 Q6/Q7: does Boombness survive controlling for refusalness? -------------- #
    if args.refusalness:
        R = read_jsonl(os.path.join(args.refusalness, "results.jsonl"))
        refus = {r["prompt_id"]: r for r in R if r["prompt_id"] in asr}
        rk = [p for p in kept if p in refus]
        print(f"\n[G2] refusalness joined on prompt_id for {len(rk)}/{len(kept)} analysed prompts")
        if rk:
            import numpy as np
            from sklearn.linear_model import LinearRegression
            yv = np.array([asr[p] for p in rk])
            med: Dict[str, object] = {"n": len(rk)}
            for RL in (12, 16, 18, 20):
                col = f"refusalness|L{RL}|proj"
                if col not in refus[rk[0]]:
                    continue
                rv = np.array([refus[p][col] for p in rk])
                r0, p0 = spearman(rv.tolist(), yv.tolist())
                print(f"  refusalness L{RL:<2d} -> ASR   rho={r0:+.3f} p={p0:.2e}  sd={float(rv.std()):.3f}")
                med[f"refusalness_L{RL}_vs_asr"] = {"spearman": r0, "p": p0}
                # does the best representation predictor add over refusalness alone?
                for name, LL, stat in (("d_surface|L8|proj", 8, "proj"),
                                       ("d_surface|L12|proj", 12, "proj"),
                                       ("d_surface|L31|cos", 31, "cos")):
                    xv = np.array([rep[p].get((LL, stat), float("nan")) for p in rk])
                    if np.isnan(xv).any():
                        continue
                    X1 = rv.reshape(-1, 1)
                    X2 = np.column_stack([rv, xv])
                    r1 = LinearRegression().fit(X1, yv).score(X1, yv)
                    r2 = LinearRegression().fit(X2, yv).score(X2, yv)
                    # and the reverse: does refusalness add over Boombness alone?
                    Xb = xv.reshape(-1, 1)
                    rb = LinearRegression().fit(Xb, yv).score(Xb, yv)
                    print(f"    R2 refusalness-only {r1:.4f} | +{name} -> {r2:.4f} "
                          f"(delta {r2-r1:+.4f}) | {name}-only {rb:.4f} "
                          f"(refusalness adds {r2-rb:+.4f})")
                    med[f"L{RL}_vs_{name}"] = {"r2_refusal_only": r1, "r2_both": r2,
                                               "delta_boombness_over_refusal": r2 - r1,
                                               "r2_boombness_only": rb,
                                               "delta_refusal_over_boombness": r2 - rb}
            report["mediation"] = med

    out = args.out or os.path.join(args.judge, "g2_analysis.json")
    with open(out, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\n[G2] -> {out}")
    return 0


def _sd(xs):
    xs = [x for x in xs if x is not None]
    if len(xs) < 2:
        return float("nan")
    m = sum(xs) / len(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1))


if __name__ == "__main__":
    raise SystemExit(main())
