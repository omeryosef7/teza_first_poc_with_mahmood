"""
next7_attention_retrieval.py — N7-L: is the codeword→concept binding retrieved by TOKEN-IDENTITY
attention? Motivated by N7-K (the install is codeword-specific — a novel query word does NOT inherit
the mapping). Prediction: the query codeword attends preferentially to the DEMO CODEWORD positions
(same token identity) vs count-matched random positions, in the mid-band (L7-14) where the concept
is written.

Method: eager forward with output_attentions on DOUBLESPEAK prompts; for the query codeword position,
average attention mass to each source set over mid-band heads. Compare demo-codeword (prev_codewords)
vs random_matched (count-matched control). demo ≫ random => token-identity retrieval.

Scalars only (attention masses); no prompt text persisted.

Run (GPU, L40S; eager):
  python next7_attention_retrieval.py --bench data/pair_benchmark/pair_carrot_bomb.json --n-items 12
"""
import os, sys, json, time, random, argparse, importlib.util
import numpy as np, torch

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import ds_common as dc
import pair_common as pc

_s = importlib.util.spec_from_file_location("atp36", os.path.join(HERE, "36_pair_attention.py"))
atp36 = importlib.util.module_from_spec(_s); _s.loader.exec_module(atp36)

KEY_SETS = ("prev_codewords", "demos_all", "random_matched")


@torch.no_grad()
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bench", required=True)
    ap.add_argument("--model", default=dc.PRIMARY_MODEL)
    ap.add_argument("--readout", default="forced_choice")
    ap.add_argument("--split", default="heldout")
    ap.add_argument("--band-lo", type=int, default=7)
    ap.add_argument("--band-hi", type=int, default=14)
    ap.add_argument("--n-items", type=int, default=12)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out-root", default=os.path.join(HERE, "outputs"))
    args = ap.parse_args()
    dc.set_seed(args.seed); rng = random.Random(args.seed)

    bench = json.load(open(args.bench)); pair = bench["pair"]
    lm = dc.load_model(args.model, attn_implementation="eager")
    band = list(range(args.band_lo, args.band_hi + 1))
    rows = [r for r in bench["semantic"] if r["readout"] == args.readout and r["split"] == args.split
            and r["condition"] == "DOUBLESPEAK"][:args.n_items]

    agg = {k: [] for k in KEY_SETS}         # per-prompt band-mean attention mass (count-normalized)
    n_used = 0
    for r in rows:
        templated = dc.apply_template(lm.tokenizer, r["prompt"])
        pos = pc.resolve_positions(lm, templated, r["probe_word"])
        q = pos.codeword_last
        keysets = {}
        for name in KEY_SETS:
            keys, located = atp36.source_positions(lm, templated, r["probe_word"], name, rng,
                                                   raw_prompt=r["prompt"])
            keysets[name] = [k for k in keys if 0 <= k < q]     # only causal (before query)
        if not keysets["prev_codewords"] or not keysets["random_matched"]:
            continue
        tok = lm.tokenizer(templated, return_tensors="pt", add_special_tokens=False).to(lm.model.device)
        out = lm.model(**tok, output_attentions=True)
        n_used += 1
        for name in KEY_SETS:
            K = keysets[name]
            if not K:
                agg[name].append(None); continue
            masses = []
            for L in band:
                a = out.attentions[L][0, :, q, :]              # [heads, seq]
                masses.append(float(a[:, K].sum(dim=-1).mean() / len(K)))  # per-key, head-avg
            agg[name].append(float(np.mean(masses)))

    def summ(name):
        v = [x for x in agg[name] if x is not None]
        return {"mean_attn_per_key": round(float(np.mean(v)), 6) if v else None, "n": len(v)}

    res = {"model": args.model, "pair": pair, "band": [args.band_lo, args.band_hi],
           "n_prompts": n_used, "per_keyset": {k: summ(k) for k in KEY_SETS}}
    # ratio: demo-codeword vs random-matched (both count-normalized per key)
    dc_m = res["per_keyset"]["prev_codewords"]["mean_attn_per_key"]
    rnd = res["per_keyset"]["random_matched"]["mean_attn_per_key"]
    res["demo_codeword_over_random"] = round(dc_m / rnd, 3) if (dc_m and rnd) else None

    tag = args.model.split("/")[-1]; uniq = os.environ.get("SLURM_JOB_ID") or str(os.getpid())
    out_dir = os.path.join(args.out_root, f"attn_retrieval_{tag}_{time.strftime('%Y%m%d_%H%M%S')}_{uniq}")
    os.makedirs(out_dir, exist_ok=True)
    json.dump(res, open(os.path.join(out_dir, "attn_retrieval.json"), "w"), indent=2)
    print(f"[attn_retrieval] {pair['codeword']}->{pair['concept']} band L{args.band_lo}-{args.band_hi} "
          f"n={n_used}")
    for k in KEY_SETS:
        print(f"  {k:16s} mean_attn_per_key={res['per_keyset'][k]['mean_attn_per_key']}")
    print(f"  demo_codeword / random_matched = {res['demo_codeword_over_random']}x")
    print(f"[attn_retrieval] -> {out_dir}")


if __name__ == "__main__":
    main()
