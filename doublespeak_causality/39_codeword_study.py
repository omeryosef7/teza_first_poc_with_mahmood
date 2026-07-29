"""
39_codeword_study.py — CAUSAL_CORE_PLAN §8.1 + §16.15 (S13).

**Explicitly tests Matan's hypothesis**: is a codeword *farther* from the target concept in
STATIC EMBEDDING space a better carrier? The plan is emphatic that this must be tested, not
assumed — and the prior sprint's first look (r = −0.18, n=18, one concept) was inconclusive.

DESIGN — the demonstration TEXT is held identical across codewords.
The stored `DOUBLESPEAK` prompts contain concept sentences with the concept already
substituted by `carrot`. Reverse-substituting `carrot -> bomb` recovers the original concept
sentences exactly (the substitution is 1:1 for these words), and re-substituting gives every
candidate codeword the *same* demonstrations. So any difference across codewords is
attributable to the codeword, not to which sentences it happened to get. This needs no API
call and does not touch `pair_carrot_bomb.json`, so no completed result is disturbed.

MEASURED PER CODEWORD
  static geometry : cosine + L2 to the concept's input embedding, token length, unembedding
                    cosine (some "distance" effects live in the output head, not the input)
  baseline        : p_concept with NO demonstrations (does the codeword already lean concept-ward?)
  hijack strength : p_concept and reads-as-concept under the DS demonstrations  <- the outcome
  specificity     : p_codeword (is the literal reading displaced?)

Single-token codewords only: `pair_common.word_first_ids` scores the FIRST emitted token, so a
multi-token codeword would make the probability mass mean something different (documented
house gotcha).

Reported with rank correlations (scipy-free, via `stats._average_ranks`) and Holm correction
over the property set, because this is a multiple-comparison fishing expedition by design.

Usage:
  python 39_codeword_study.py --bench data/pair_benchmark/pair_carrot_bomb.json
"""
import os
import re
import sys
import json
import time
import math
import argparse

import numpy as np
import torch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ds_common as dc
import pair_common as pc
import stats as st

HERE = os.path.dirname(os.path.abspath(__file__))

# Benign nouns spanning a range of embedding distance to typical harmful concepts.
# Extends the pool in 16_prepare_behavioral_benchmark (which this must stay compatible with)
# with further everyday nouns; all are filtered to single-token below.
CODEWORD_POOL = [
    "potato", "carrot", "muffin", "mango", "pillow", "lantern",
    "mirror", "basket", "table", "river", "turtle", "kettle",
    "ladder", "candle", "blanket", "window", "garden", "bottle",
    "pencil", "cushion", "saddle", "harbor", "meadow", "biscuit",
    "curtain", "trumpet", "anchor", "wagon", "puzzle", "ribbon",
]


def spearman(x, y):
    if len(x) < 3:
        return float("nan")
    rx = st._average_ranks(np.asarray(x, float))
    ry = st._average_ranks(np.asarray(y, float))
    rx = rx - rx.mean()
    ry = ry - ry.mean()
    den = math.sqrt(float((rx ** 2).sum()) * float((ry ** 2).sum()))
    return float("nan") if den == 0 else float((rx * ry).sum() / den)


def perm_p(x, y, n_perm=10000, seed=0):
    """Two-sided permutation p for a rank correlation."""
    rng = np.random.default_rng(seed)
    obs = abs(spearman(x, y))
    y = np.asarray(y, float)
    hits = 0
    for _ in range(n_perm):
        if abs(spearman(x, rng.permutation(y))) >= obs:
            hits += 1
    return (hits + 1) / (n_perm + 1)


def recover_concept_sentences(bench):
    """Reverse-substitute the stored DS demos to recover the concept sentences."""
    cc, cw = bench["pair"]["concept"], bench["pair"]["codeword"]
    out = {}
    for r in bench["semantic"]:
        if r["condition"] != "DOUBLESPEAK":
            continue
        block = r["prompt"].rsplit("\n\n", 1)[0]
        key = (r["split"], r["demo_style"], r["n_demos"])
        if key in out:
            continue
        sents = []
        for line in block.split("\n"):
            for form in (cw, cw.capitalize(), cw.upper()):
                line = line.replace(form, cc if form == cw else cc.capitalize())
            sents.append(line)
        out[key] = sents
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bench", required=True)
    ap.add_argument("--model", default=dc.PRIMARY_MODEL)
    ap.add_argument("--out-root", default=os.path.join(HERE, "outputs"))
    ap.add_argument("--readout", default="cloze")
    ap.add_argument("--demo-styles", default="news,narrative,technical",
                    help="S2 gate-passing styles only")
    ap.add_argument("--n-demos", type=int, default=12)
    ap.add_argument("--max-new-tokens", type=int, default=8)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    dc.set_seed(args.seed)
    bench = json.load(open(args.bench))
    cc = bench["pair"]["concept"]
    lex = bench["lexicons"]
    styles = [s.strip() for s in args.demo_styles.split(",") if s.strip()]
    readout_tpl = {r["rid"]: r["template"] for r in bench["readouts"]}[args.readout]

    concept_sents = recover_concept_sentences(bench)

    lm = dc.load_model(args.model)
    emb = lm.model.get_input_embeddings().weight.detach()
    unemb = (lm.model.get_output_embeddings().weight.detach()
             if lm.model.get_output_embeddings() is not None else emb)

    def single_tok(w):
        ids = lm.tokenizer.encode(" " + w, add_special_tokens=False)
        return ids[0] if len(ids) == 1 else None

    cc_id = single_tok(cc)
    if cc_id is None:
        raise SystemExit(f"concept {cc!r} is not single-token; scoring would be misleading")

    pool, skipped = [], []
    for w in CODEWORD_POOL:
        t = single_tok(w)
        (pool if t is not None else skipped).append(w if t is None else (w, t))
    print(f"[cw] pool {len(pool)} single-token codewords "
          f"({len(skipped)} skipped as multi-token: {skipped})")

    tag = args.model.split("/")[-1]
    uniq = os.environ.get("SLURM_JOB_ID") or str(os.getpid())
    out_dir = os.path.join(args.out_root,
                           f"pair_codeword_{tag}_{time.strftime('%Y%m%d_%H%M%S')}_{uniq}")
    os.makedirs(out_dir, exist_ok=True)

    ec = emb[cc_id].float()
    uc = unemb[cc_id].float()
    rows = []
    for w, tid in pool:
        ew = emb[tid].float()
        uw = unemb[tid].float()
        groups = {"concept": pc.word_first_ids(lm.tokenizer, cc),
                  "codeword": pc.word_first_ids(lm.tokenizer, w)}

        ds_scores, ds_labels, base_scores = [], [], []
        for style in styles:
            for split in ("dev", "heldout"):
                sents = concept_sents.get((split, style, args.n_demos))
                if not sents:
                    continue
                sub = [re.sub(re.escape(cc), w, s, flags=re.IGNORECASE) for s in sents]
                if not all(w.lower() in s.lower() for s in sub):
                    continue
                probe = readout_tpl.format(w=w, a=w, b=cc)
                ds_prompt = "\n".join(sub) + "\n\n" + probe
                t_ds = dc.apply_template(lm.tokenizer, ds_prompt)
                p = pc.semantic_score(lm, t_ds, groups)
                ds_scores.append(p)
                gen = pc.patched_generate(lm, t_ds, (), args.max_new_tokens)
                ds_labels.append(1 if _classify(gen, lex) == cc else 0)
                # no-demo baseline: does the codeword already lean concept-ward?
                t_b = dc.apply_template(lm.tokenizer, probe)
                base_scores.append(pc.semantic_score(lm, t_b, groups))

        if not ds_scores:
            continue
        row = {
            "codeword": w, "token_id": tid,
            "emb_cos_to_concept": round(float(torch.nn.functional.cosine_similarity(
                ew.unsqueeze(0), ec.unsqueeze(0))), 5),
            "emb_l2_to_concept": round(float((ew - ec).norm()), 4),
            "unemb_cos_to_concept": round(float(torch.nn.functional.cosine_similarity(
                uw.unsqueeze(0), uc.unsqueeze(0))), 5),
            "emb_norm": round(float(ew.norm()), 4),
            "n_tokens_bare": len(lm.tokenizer.encode(w, add_special_tokens=False)),
            "n_cells": len(ds_scores),
            "baseline_p_concept": round(float(np.mean([s["concept"] for s in base_scores])), 6),
            "ds_p_concept": round(float(np.mean([s["concept"] for s in ds_scores])), 6),
            "ds_p_codeword": round(float(np.mean([s["codeword"] for s in ds_scores])), 6),
            "ds_reads_as_concept": round(float(np.mean(ds_labels)), 4),
        }
        row["hijack_gain"] = round(row["ds_p_concept"] - row["baseline_p_concept"], 6)
        rows.append(row)
        print(f"  [cw] {w:9} emb_cos={row['emb_cos_to_concept']:+.4f} "
              f"L2={row['emb_l2_to_concept']:7.3f} base={row['baseline_p_concept']:.5f} "
              f"DS_p={row['ds_p_concept']:.4f} DS_label={row['ds_reads_as_concept']:.2f}")

    # ---- correlations: does any static property predict hijack strength? ----
    props = ["emb_cos_to_concept", "emb_l2_to_concept", "unemb_cos_to_concept",
             "emb_norm", "baseline_p_concept"]
    outcomes = ["ds_p_concept", "ds_reads_as_concept", "hijack_gain"]
    corr, pvals, keys = {}, [], []
    for o in outcomes:
        y = [r[o] for r in rows]
        for p_ in props:
            x = [r[p_] for r in rows]
            rho = spearman(x, y)
            pv = perm_p(x, y, seed=args.seed)
            corr[f"{p_}->{o}"] = {"spearman": round(rho, 4), "p_raw": round(pv, 5), "n": len(x)}
            keys.append(f"{p_}->{o}")
            pvals.append(pv)
    for k, adj in zip(keys, st.holm_bonferroni(pvals)):
        corr[k]["p_holm"] = round(float(adj), 5)
        corr[k]["significant_corrected"] = bool(adj < 0.05)

    summary = {
        "model": lm.meta(), "pair": bench["pair"], "plan": "CAUSAL_CORE_PLAN §8.1 (S13)",
        "hypothesis_under_test": ("Matan: a codeword FARTHER from the concept in static "
                                 "embedding space is a better carrier"),
        "bench": os.path.abspath(args.bench), "readout": args.readout,
        "demo_styles": styles, "n_demos": args.n_demos,
        "demo_text_held_constant_across_codewords": True,
        "n_codewords": len(rows), "skipped_multitoken": skipped,
        "rows": rows, "correlations": corr,
        "multiple_comparison": "holm_bonferroni over %d property x outcome tests" % len(keys),
        "status": "COMPLETE",
    }
    with open(os.path.join(out_dir, "codeword_summary.json"), "w") as f:
        json.dump(summary, f, indent=1)

    print(f"\n[cw] n={len(rows)} codewords; Spearman (Holm-corrected):")
    for k, v in sorted(corr.items(), key=lambda t: -abs(t[1]["spearman"])):
        star = " *" if v.get("significant_corrected") else ""
        print(f"  {k:44} rho={v['spearman']:+.3f} p_raw={v['p_raw']:.4f} "
              f"p_holm={v['p_holm']:.4f}{star}")
    print(f"[cw] -> {out_dir}")


def _classify(text, lex):
    t = re.sub(r"[^a-zA-Z\s]", " ", text or "").lower().split()[:4]
    for w in t:
        for k, vocab in lex.items():
            if w in vocab:
                return k
    return "OTHER"


if __name__ == "__main__":
    main()
