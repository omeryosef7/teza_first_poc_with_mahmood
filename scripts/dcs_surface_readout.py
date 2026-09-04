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
    ap.add_argument("--tag", default="dcs_surface_readout")
    ap.add_argument("--out", default=os.path.join(ROOT, "outputs/boombness/dcs_analysis"))
    a = ap.parse_args()

    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(a.model)

    out = {"schema": SCHEMA, "condition": a.condition, "model": a.model, "arms": {}}
    for spec in a.arm:
        label, _, tag = spec.partition("=")
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


if __name__ == "__main__":
    main()
