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


def rank_partial(x, y, z):
    """Spearman(x, y | z): Pearson correlation of the residuals of the RANKS.

    Added because the tick-24 audit showed the headline predictor was ~55% shared with the
    residual-stream norm at the same position: Spearman(d_surface|L8|proj, hnorm|L8) = -0.731 and
    Spearman(hnorm|L8, ASR) = -0.315, so partialling the norm out dropped the reported rho from
    +0.342 to +0.151. A quantity a GCG objective would push (position ON the axis) is not the
    same as how large the activation is, and the two must be separated before either is claimed.
    """
    import numpy as np
    from scipy.stats import rankdata, pearsonr
    rx, ry, rz = (rankdata(np.asarray(v, dtype=float)) for v in (x, y, z))
    def resid(a, b):
        b1 = np.column_stack([np.ones_like(b), b])
        beta, *_ = np.linalg.lstsq(b1, a, rcond=None)
        return a - b1 @ beta
    ex, ey = resid(rx, rz), resid(ry, rz)
    r, p = pearsonr(ex, ey)
    return float(r), float(p)


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
        # The residual-stream NORM at the same position. `d_surface|L|proj` is an unnormalised
        # inner product, so it scales with ||h||, and ||h|| is itself an ASR predictor. Without
        # this control a "Boombness" association can be mostly "how big the activation is".
        for L in layers:
            c = f"hnorm|L{L}"
            if c in r:
                d[(L, "hnorm")] = r[c]
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
            if stat == "hnorm":
                continue
            r, p = spearman(xs, y)
            name = f"d_surface|L{L}|{stat}" if stat != "ll" else f"logit_lens|L{L}"
            hn = [rep[pp].get((L, "hnorm")) for pp in kept]
            if all(v is not None for v in hn):
                rp, pp_ = rank_partial(xs, y, hn)
                rn, pn = spearman(hn, y)
            else:
                rp = pp_ = rn = pn = float("nan")
            rows.append((name, r, p, float(_sd(xs)), rp, pp_, rn))
            pv[name] = p
    # semantic predictor, on its own (different) prompt
    sem_keys = [p for p in kept if fam_key(meta[p]["family_id"]) in sem_by_fam]
    if sem_keys:
        xs = [sem_by_fam[fam_key(meta[p]["family_id"])] for p in sem_keys]
        ys = [asr[p] for p in sem_keys]
        r, p = spearman(xs, ys)
        rows.append((f"semantic_logodds (n={len(sem_keys)}, OTHER prompt)", r, p, float(_sd(xs)),
                     float("nan"), float("nan"), float("nan")))
        pv["semantic_logodds"] = p

    rej = holm(pv)
    rows.sort(key=lambda t: -abs(t[1]))
    print(f"\n{'predictor':38s} {'rho':>8s} {'p':>9s} {'Holm':>5s} "
          f"{'rho|hnorm':>10s} {'p':>9s} {'hnorm~y':>8s}  norm-share")
    for name, r, p, sd, rp, pp_, rn in rows:
        share = (1 - abs(rp) / abs(r)) if (r and math.isfinite(rp) and abs(r) > 1e-9) else float("nan")
        flag = ""
        if math.isfinite(share) and share > 0.33:
            flag = "  <-- >1/3 of this is the NORM, not the axis"
        print(f"{name:38s} {r:>+8.3f} {p:>9.2e} {str(rej.get(name.split(' ')[0], '')):>5s} "
              f"{rp:>+10.3f} {pp_:>9.2e} {rn:>+8.3f} {100*share:>8.0f}%{flag}")
    report["predictors"] = [{"name": n, "spearman": r, "p": p, "sd": sd,
                             "partial_given_hnorm": rp, "partial_p": pp_, "hnorm_vs_asr": rn,
                             "holm_rejected": bool(rej.get(n.split(" ")[0], False))}
                            for n, r, p, sd, rp, pp_, rn in rows]

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
            # SYMMETRIC HEAD-TO-HEAD. The first version pinned refusalness to L18 (near its own
            # minimum) and compared it against the argmax-selected Boombness column, then quoted
            # the resulting 40x. Given the same freedom, refusalness's best layer is L12
            # (R2 0.0386, rho +0.167 p=0.011) and the honest ratio is ~3.7x. The joint model over
            # all refusal layers is also reported, because "+0.0005 added" was one fixed column
            # against a selected one; jointly refusalness adds ~+0.039.
            refus_layers = [RL for RL in (12, 14, 16, 18, 20)
                            if f"refusalness|L{RL}|proj" in refus[rk[0]]]
            R_all = np.column_stack([[refus[p][f"refusalness|L{RL}|proj"] for p in rk]
                                     for RL in refus_layers]) if refus_layers else None
            best_rl, best_r2 = None, -1.0
            for RL in refus_layers:
                v = np.array([refus[p][f"refusalness|L{RL}|proj"] for p in rk]).reshape(-1, 1)
                r2 = LinearRegression().fit(v, yv).score(v, yv)
                if r2 > best_r2:
                    best_rl, best_r2 = RL, r2
            if R_all is not None:
                r2_joint = LinearRegression().fit(R_all, yv).score(R_all, yv)
                print(f"  refusalness: best single layer L{best_rl} R2={best_r2:.4f}; "
                      f"all {len(refus_layers)} layers jointly R2={r2_joint:.4f}")
                med["refusalness_best_layer"] = best_rl
                med["refusalness_best_r2"] = best_r2
                med["refusalness_joint_r2"] = r2_joint
                # within-arm range restriction, the reason the R2 is small at all
                for RL in refus_layers:
                    v = [refus[p][f"refusalness|L{RL}|proj"] for p in rk]
                    med[f"refusalness_L{RL}_sd_within_arm"] = float(np.std(v))
            for RL in refus_layers:
                col = f"refusalness|L{RL}|proj"
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
                    add_joint = float("nan")
                    if R_all is not None:
                        Xj = np.column_stack([R_all, xv])
                        add_joint = LinearRegression().fit(Xj, yv).score(Xj, yv) - rb
                    print(f"    R2 refusal-L{RL}-only {r1:.4f} | +{name} -> {r2:.4f} "
                          f"(Boombness adds {r2-r1:+.4f}) | {name}-only {rb:.4f} "
                          f"(this refusal layer adds {r2-rb:+.4f}; ALL refusal layers jointly add "
                          f"{add_joint:+.4f})")
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
