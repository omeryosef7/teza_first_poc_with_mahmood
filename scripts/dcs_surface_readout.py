#!/usr/bin/env python
"""dcs_surface_readout.py -- what the model would ACTUALLY SAY, beside the log-odds.

WHY THIS EXISTS. The phase's headline endpoint is `semantic_logodds = logp_concept -
logp_codeword`, which is deliberately mass-invariant: it compares the two options and is blind to
everything else the model might emit. That is the right property for a clean contrast and the
wrong property for the sentence "the reading flips back to the literal meaning", which is a claim
about the model's ANSWER, not about a ratio between two candidates.

This decodes `top1_id` -- the token actually argmax at the readout position -- and reports the
surface answer distribution next to `option_mass` (how much probability the two options hold
between them). If `option_mass` collapses under an intervention, the log-odds is still valid but
it is being computed inside a shrinking slice of the distribution, and the surface answer is where
that shows up.

Stdlib + transformers tokenizer only (CPU; no model weights, no GPU, no API).
"""
from __future__ import annotations
import argparse, collections, glob, json, os, statistics as st, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCHEMA = "DCS_SURFACE_READOUT/1"


def pick(tag: str) -> str:
    ds = [d for d in glob.glob(os.path.join(ROOT, "outputs/boombness/score_behavior", tag + "_*"))
          if os.path.isfile(os.path.join(d, "DONE.json"))]
    if not ds:
        sys.exit(f"REFUSING: no completed run dir for tag {tag}")
    return sorted(ds)[-1]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", action="append", required=True,
                    help="label=tag, e.g. baseline=dcsro_C_baseline")
    ap.add_argument("--condition", default="natural_doublespeak")
    ap.add_argument("--model", default="meta-llama/Llama-3.1-8B-Instruct")
    ap.add_argument("--did", action="store_true",
                    help="also compute the DECISION-level specificity DiD: per-domain change in "
                         "the fraction of rows whose argmax answer is the CONCEPT, cell C minus "
                         "cell B. Requires exactly two arms labelled baseline and KO3, and is run "
                         "once per cell (pass --condition twice via two invocations is wrong; use "
                         "--did-both instead)")
    ap.add_argument("--did-both", action="store_true",
                    help="run both cells and emit the decision-level DiD in one artifact")
    ap.add_argument("--concept-token", default="",
                    help="substring identifying the CONCEPT answer after decoding, e.g. 'bomb' or "
                         "'poison'; matched case-insensitively on the stripped decoded token")
    ap.add_argument("--tag", default="dcs_surface_readout")
    ap.add_argument("--out", default=os.path.join(ROOT, "outputs/boombness/dcs_analysis"))
    a = ap.parse_args()

    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(a.model)

    out = {"schema": SCHEMA, "condition": a.condition, "model": a.model, "arms": {}}
    for spec in a.arm:
        label, _, tag = spec.partition("=")
        if label in ("baselineB", "KO3B"):
            # cell-B companions exist only to feed the decision-level DiD, which selects its own
            # condition per cell; the per-arm summary below is single-condition by design.
            continue
        d = pick(tag)
        rows = [json.loads(L) for L in open(os.path.join(d, "results.jsonl"))]
        rows = [r for r in rows if r["condition"] == a.condition]
        if not rows:
            sys.exit(f"REFUSING {label}: no rows with condition={a.condition}")
        om = [r["option_mass"] for r in rows]
        top = collections.Counter(r["top1_id"] for r in rows)
        surface = {tok.decode([t]): n for t, n in top.most_common()}
        winner_gt_half = sum(1 for r in rows if max(r["p_codeword"], r["p_concept"]) > 0.5)
        out["arms"][label] = {
            "tag": tag, "run_dir": os.path.basename(d), "n_rows": len(rows),
            "option_mass_median": st.median(om), "option_mass_p10": sorted(om)[len(om) // 10],
            "option_mass_min": min(om),
            "semantic_logodds_mean": st.mean([r["semantic_logodds"] for r in rows]),
            "surface_answer_counts": surface,
            "rows_where_winning_option_exceeds_half": winner_gt_half,
            "NOTE": ("winning option >0.5 is the only case where it is GUARANTEED to be the "
                     "argmax overall; below that the surface answer can be a third token"),
        }
        print(f"=== {label}  ({tag}, n={len(rows)}) ===")
        print(f"    logodds mean {out['arms'][label]['semantic_logodds_mean']:+7.3f}   "
              f"option_mass med {st.median(om):.3f}   winner>0.5 in {winner_gt_half}/{len(rows)}")
        for t, n in top.most_common(6):
            print(f"      {tok.decode([t])!r:14s} {n:4d}  ({100.0*n/len(rows):.1f}%)")

    os.makedirs(a.out, exist_ok=True)
    dst = os.path.join(a.out, f"{a.tag}.json")
    json.dump(out, open(dst, "w"), indent=2, sort_keys=True)
    print(f"-> {dst}")

    if a.did_both:
        did_both(a, tok)


def _concept_frac_by_domain(rows, tok, needle):
    """Per domain: fraction of rows whose ARGMAX answer decodes to the concept word."""
    per = collections.defaultdict(list)
    for r in rows:
        ans = tok.decode([r["top1_id"]]).strip().lower()
        per[r["domain"]].append(1.0 if needle in ans else 0.0)
    return {d: st.mean(v) for d, v in per.items()}


def did_both(a, tok) -> None:
    """DCS-R-034: specificity at the DECISION level, not the log-odds level.

    R-033 showed the log-odds DiD can fail while the surface answer is perfectly specific: in
    cell B the answer stays 100% concept and only the (already enormous) margin compresses. A DiD
    on log-odds therefore mixes 'the reading changed' with 'the margin shrank'. This endpoint asks
    only whether the ANSWER changed, which is what the specificity claim actually says.
    """
    if not a.concept_token:
        sys.exit("REFUSING --did-both without --concept-token")
    arms = dict(spec.partition("=")[::2] for spec in a.arm)
    need = {"baseline", "KO3"}
    if not need <= set(arms):
        sys.exit(f"REFUSING --did-both: need arms baseline= and KO3=, got {sorted(arms)}")
    # Cells may live in the SAME run (both conditions in one job, as PR-013 does) or in SEPARATE
    # runs (as the button/bomb headline does, one job per condition). Both are supported; which
    # applies is recorded in the artifact rather than inferred silently.
    split_cells = "baselineB" in arms and "KO3B" in arms
    loaded = {}
    for lab, tag in arms.items():
        d = pick(tag)
        loaded[lab] = [json.loads(L) for L in open(os.path.join(d, "results.jsonl"))]
    deltas = {}
    detail = {}
    for cell, cond in (("C", "natural_doublespeak"), ("B", "direct_harmful")):
        bk = "baselineB" if (split_cells and cell == "B") else "baseline"
        kk = "KO3B" if (split_cells and cell == "B") else "KO3"
        b = [r for r in loaded[bk] if r["condition"] == cond]
        k = [r for r in loaded[kk] if r["condition"] == cond]
        if not b or not k:
            sys.exit(f"REFUSING cell {cell}: no rows with condition={cond} in arms "
                     f"{bk}/{kk} -- if the cells were run as separate jobs, pass "
                     f"--arm baselineB=<tag> --arm KO3B=<tag>")
        if {r["prompt_id"] for r in b} != {r["prompt_id"] for r in k}:
            sys.exit(f"REFUSING cell {cell}: arms cover different prompt_id sets")
        fb = _concept_frac_by_domain(b, tok, a.concept_token.lower())
        fk = _concept_frac_by_domain(k, tok, a.concept_token.lower())
        if set(fb) != set(fk):
            sys.exit(f"REFUSING cell {cell}: domain sets differ")
        deltas[cell] = {d: fk[d] - fb[d] for d in fb}
        detail[cell] = {"baseline_concept_frac": st.mean(list(fb.values())),
                        "ko_concept_frac": st.mean(list(fk.values())),
                        "n_domains": len(fb), "n_rows": len(b)}
    did = {d: deltas["C"][d] - deltas["B"][d] for d in deltas["C"]}
    vals = list(did.values())
    neg = sum(1 for v in vals if v < 0); pos = sum(1 for v in vals if v > 0)
    n_inf = neg + pos
    p = _sign_p(pos, n_inf)
    res = {"schema": "DCS_SURFACE_DID/1", "concept_token": a.concept_token,
           "cells_from_separate_runs": split_cells, "arms": arms,
           "cells": detail,
           "mean_delta_concept_frac": {c: st.mean(list(v.values())) for c, v in deltas.items()},
           "did_mean": st.mean(vals), "pos": pos, "neg": neg, "ties": len(vals) - n_inf,
           "k_informative": n_inf, "sign_p": p,
           "attainable_p_floor": _sign_p(0, n_inf) if n_inf else 1.0,
           "NOTE": ("decision-level specificity: DiD on the per-domain fraction of rows whose "
                    "ARGMAX answer is the concept. Immune to margin compression in a saturated "
                    "cell, which DCS-R-033 showed can sink a log-odds DiD while the answers are "
                    "perfectly specific.")}
    print("=== decision-level specificity DiD ===")
    for c in ("C", "B"):
        print(f"  cell {c}: concept-answer frac {detail[c]['baseline_concept_frac']:.3f} -> "
              f"{detail[c]['ko_concept_frac']:.3f}   (delta {res['mean_delta_concept_frac'][c]:+.3f})")
    print(f"  DiD mean {res['did_mean']:+.3f}   {pos}+/{neg}- ({res['ties']} ties)   "
          f"p={p:.3e}  floor={res['attainable_p_floor']:.2e}")
    os.makedirs(a.out, exist_ok=True)
    dst = os.path.join(a.out, f"{a.tag}_decisionDiD.json")
    json.dump(res, open(dst, "w"), indent=2, sort_keys=True)
    print(f"  -> {dst}")


def _sign_p(x: int, n: int) -> float:
    if n == 0:
        return 1.0
    from fractions import Fraction
    def c(nn, kk):
        r = 1
        for i in range(kk):
            r = r * (nn - i) // (i + 1)
        return r
    k = min(x, n - x)
    tail = sum(Fraction(c(n, i)) for i in range(0, k + 1)) / Fraction(2) ** n
    return min(1.0, float(2 * tail))


if __name__ == "__main__":
    main()
