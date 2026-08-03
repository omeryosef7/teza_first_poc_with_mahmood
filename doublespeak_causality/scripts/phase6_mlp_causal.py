#!/usr/bin/env python3
"""Phase 6 CAUSAL MLP write-location: does exact MLP-OUTPUT patching at the demonstration
codeword change the harmful reading? Necessity + sufficiency, DE_context forced-choice readout.

This is the causal follow-up to scripts/phase6_mlp_projection.py (representational, which
showed the concept projection is late-dominated = readout-proximity artifact, NOT a causal
write). The master plan (Phase 6, Gate 4): "a write layer must satisfy MORE than a large
projection — exact MLP intervention must change a downstream concept or behavioral metric."

Structurally identical to scripts/phase3_demo_neutralize.py (same split, same FC readout,
same cells/CIs) but patches the MLP OUTPUT (via pc.ComponentOutSwap) instead of resid_pre
demo K/V (pc.DemoStateSwap). So the two are directly comparable: demo-KV = the retrieval
component; mlp_out = the write component, at the same demo-codeword positions.

Cells (per WINDOW and per LAYER):
  C1              DS baseline
  C3_mlpout       necessity: DS mlp_out <- matched BENIGN mlp_out at demo-codeword positions
  C1_selfswap     faithfulness: DS mlp_out <- DS OWN mlp_out (must == C1, exact no-op)
  random_control  necessity control: benign mlp_out at count-matched NON-codeword positions
  S1              BENIGN baseline
  S3_install      sufficiency: BENIGN mlp_out <- DS mlp_out at demo-codeword positions
  S1_selfswap     faithfulness (== S1)
  S_random        sufficiency control: DS mlp_out at random benign NON-codeword positions
Readout p_concept = P(concept)/(P(concept)+P(codeword)) at the FC answer position.
necessity_specific = random_control - C3   ;  sufficiency_specific = S3 - S_random  (paired CI).

Usage:
  python scripts/phase6_mlp_causal.py --bench data/bench/bench_curated.json --granularity window
"""
from __future__ import annotations
import argparse, json, os, random, sys, time
from collections import defaultdict
from contextlib import ExitStack
import numpy as np
import torch

HERE = os.path.dirname(os.path.abspath(__file__))
DC = os.path.dirname(HERE)
sys.path.insert(0, DC)
import ds_common as dc
import pair_common as pc


def _single_id(tok, word):
    return tok.encode(" " + word, add_special_tokens=False)[0]


FC_PREFIX = "Choose one label only and answer with just that label."
def fc_question(codeword, concept):
    return (f'{FC_PREFIX} In the text above, does the word "{codeword}" '
            f'refer to "{concept}" or to "{codeword}"?')


def demo_block_of(ds_prompt, marker="\n\nDo not reason, just "):
    return ds_prompt.rsplit(marker, 1)[0] if marker in ds_prompt else ds_prompt


def canonical_windows(L):
    return {"early": list(range(0, L // 3)),
            "mid": list(range(L // 3, 2 * L // 3)),
            "late": list(range(2 * L // 3, L))}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bench", required=True)
    ap.add_argument("--model", default=dc.PRIMARY_MODEL)
    ap.add_argument("--out-root", default=os.path.join(DC, "outputs"))
    ap.add_argument("--splits", default="dev,heldout")
    ap.add_argument("--windows", default="early,mid,late")
    ap.add_argument("--granularity", default="window", choices=["window", "layer"])
    ap.add_argument("--n-prompts", type=int, default=0, help="0 = all DS prompts per split")
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    dc.set_seed(args.seed)
    rng = random.Random(args.seed)
    bench = json.load(open(args.bench))
    lm = dc.load_model(args.model)
    L = lm.num_layers
    dev = lm.model.device
    cohort = bench.get("_meta", {}).get("cohort", "?")

    splits = [s.strip() for s in args.splits.split(",") if s.strip()]
    rows = [r for r in bench["semantic"] if r["split"] in splits]
    by_key = {(r["condition"], r["split"], r["sid"]): r for r in rows}
    ds_rows = defaultdict(list)
    for r in rows:
        if r["condition"] == "DOUBLESPEAK":
            ds_rows[r["split"]].append(r)

    wmap = canonical_windows(L)
    if args.granularity == "layer":
        windows = [(f"L{l}", [l]) for l in range(L)]
    else:
        windows = [(w, wmap[w]) for w in args.windows.split(",") if w.strip() in wmap]

    ts = time.strftime("%Y%m%d_%H%M%S")
    uniq = os.environ.get("SLURM_JOB_ID") or str(os.getpid())
    out_dir = os.path.join(args.out_root, f"phase6_mlpKO_{cohort}_{args.granularity}_{ts}_{uniq}")
    os.makedirs(out_dir, exist_ok=True)
    fh = open(os.path.join(out_dir, "raw.jsonl"), "w")
    n_rows = [0]
    print(f"[mlpKO] cohort={cohort} L={L} gran={args.granularity} "
          f"windows={[w for w,_ in windows][:4]}{'...' if len(windows)>4 else ''} -> {out_dir}")

    def build_fc(raw_prompt, codeword, concept):
        fc_raw = demo_block_of(raw_prompt) + "\n\n" + fc_question(codeword, concept)
        templated = dc.apply_template(lm.tokenizer, fc_raw)
        q_off = templated.rfind(FC_PREFIX)
        hit = dc.find_word_occurrences_in_text(lm.tokenizer, templated, codeword)
        demo_pos = [li for span, li in zip(hit.spans, hit.last_idx) if span[0] < q_off]
        tok = lm.tokenizer(templated, return_tensors="pt", add_special_tokens=False).to(dev)
        return templated, tok, demo_pos

    @torch.no_grad()
    def readout(fc_tok, cid, kid, contexts):
        with ExitStack() as stack:
            for c in contexts:
                stack.enter_context(c)
            out = lm.model(**fc_tok, return_dict=True)
        probs = torch.softmax(out.logits[0, -1, :].float(), dim=-1)
        pc_, pk_ = float(probs[cid]), float(probs[kid])
        denom = pc_ + pk_ + 1e-12
        return pc_ / denom, pc_, pk_

    @torch.no_grad()
    def capture_mlp(templated, positions):
        tok = lm.tokenizer(templated, return_tensors="pt", add_special_tokens=False).to(dev)
        with pc.ComponentCapture(lm, ["mlp_out"], positions) as cap:
            lm.model(**tok, return_dict=True)
        return cap.stacked()["mlp_out"]                 # [L, n_pos, H]

    def swap(positions, src_by_layer):
        return pc.ComponentOutSwap(lm.model, positions, src_by_layer, component="mlp_out")

    def emit(base, window, cell, n_sw, res):
        pnorm, pc_, pk_ = res
        fh.write(json.dumps({**base, "window": window, "cell": cell, "n_pos_swapped": n_sw,
                             "p_concept": pnorm, "raw_concept": pc_, "raw_codeword": pk_}) + "\n")
        n_rows[0] += 1

    for split in splits:
        cand = sorted(ds_rows.get(split, []), key=lambda r: r["sid"])
        if args.n_prompts:
            cand = cand[: args.n_prompts]
        for r in cand:
            concept, codeword = r["target_concept"], r["codeword"]
            cid, kid = _single_id(lm.tokenizer, concept), _single_id(lm.tokenizer, codeword)

            ds_tmpl, ds_tok, ds_demo_cw = build_fc(r["prompt"], codeword, concept)
            if not ds_demo_cw:
                continue
            brow = by_key.get(("BENIGN_REMAP", split, r["sid"]))
            if brow is None:
                continue
            b_tmpl, b_tok, b_demo_cw = build_fc(brow["prompt"], codeword, concept)
            if not b_demo_cw:
                continue
            benign_pconc = readout(b_tok, cid, kid, [])[0]
            base = {"sid": r["sid"], "split": split, "cohort": cohort, "concept": concept,
                    "codeword": codeword, "benign_p_concept": benign_pconc}

            m = min(len(ds_demo_cw), len(b_demo_cw))
            ds_cwset, b_cwset = set(ds_demo_cw), set(b_demo_cw)
            ds_pool = [p for p in range(max(ds_demo_cw)) if p not in ds_cwset]
            b_pool = [p for p in range(max(b_demo_cw)) if p not in b_cwset]
            rlen = min(m, len(ds_pool), len(b_pool))
            ds_rand = sorted(rng.sample(ds_pool, rlen)) if rlen else []
            b_rand = sorted(rng.sample(b_pool, rlen)) if rlen else []

            ds_swap_pos = ds_demo_cw[-m:] if m else []
            b_swap_pos = b_demo_cw[-m:] if m else []
            ds_cap = capture_mlp(ds_tmpl, ds_demo_cw + ds_rand)
            b_cap = capture_mlp(b_tmpl, b_demo_cw + b_rand)
            ds_out_demo, ds_out_rand = ds_cap[:, :len(ds_demo_cw), :], ds_cap[:, len(ds_demo_cw):, :]
            b_out_demo, b_out_rand = b_cap[:, :len(b_demo_cw), :], b_cap[:, len(b_demo_cw):, :]

            c1 = readout(ds_tok, cid, kid, [])
            s1 = readout(b_tok, cid, kid, [])
            for wname, ells in windows:
                # ---- NECESSITY (DS receiver): DS mlp_out <- BENIGN at demo codewords ----
                emit(base, wname, "C1", 0, c1)
                if m:
                    src3 = {l: b_out_demo[l, -m:, :] for l in ells}
                    emit(base, wname, "C3_mlpout", m,
                         readout(ds_tok, cid, kid, [swap(ds_swap_pos, src3)]))
                emit(base, wname, "C1_selfswap", len(ds_demo_cw),
                     readout(ds_tok, cid, kid,
                             [swap(ds_demo_cw, {l: ds_out_demo[l] for l in ells})]))
                if ds_rand:
                    emit(base, wname, "random_control", len(ds_rand),
                         readout(ds_tok, cid, kid,
                                 [swap(ds_rand, {l: b_out_rand[l] for l in ells})]))
                # ---- SUFFICIENCY (BENIGN receiver): install DS mlp_out ----
                emit(base, wname, "S1", 0, s1)
                if m:
                    srci = {l: ds_out_demo[l, -m:, :] for l in ells}
                    emit(base, wname, "S3_install", m,
                         readout(b_tok, cid, kid, [swap(b_swap_pos, srci)]))
                emit(base, wname, "S1_selfswap", len(b_demo_cw),
                     readout(b_tok, cid, kid,
                             [swap(b_demo_cw, {l: b_out_demo[l] for l in ells})]))
                if b_rand:
                    emit(base, wname, "S_random", len(b_rand),
                         readout(b_tok, cid, kid,
                                 [swap(b_rand, {l: ds_out_rand[l] for l in ells})]))
    fh.close()

    all_rows = [json.loads(x) for x in open(os.path.join(out_dir, "raw.jsonl"))]
    def cellmap(cell, w):
        return {r["sid"]: r["p_concept"] for r in all_rows if r["cell"] == cell and r["window"] == w}
    valid = {r["sid"] for r in all_rows if r["cell"] == "C1"
             and r.get("benign_p_concept") is not None and r["p_concept"] > r["benign_p_concept"]}
    rng2 = np.random.default_rng(0)
    def bootci(vals):
        if not vals:
            return None
        a = np.array(vals)
        boot = [rng2.choice(a, len(a), replace=True).mean() for _ in range(2000)]
        return [round(float(a.mean()), 4), round(float(np.percentile(boot, 2.5)), 4),
                round(float(np.percentile(boot, 97.5)), 4)]
    summ = {}
    for w in sorted({r["window"] for r in all_rows}):
        c1, c3 = cellmap("C1", w), cellmap("C3_mlpout", w)
        rc, ss = cellmap("random_control", w), cellmap("C1_selfswap", w)
        s1, s3 = cellmap("S1", w), cellmap("S3_install", w)
        sr, sss = cellmap("S_random", w), cellmap("S1_selfswap", w)
        nec = [s for s in valid if s in c1 and s in c3 and s in rc]
        suf = [s for s in valid if s in s1 and s in s3 and s in sr]
        summ[w] = {
            "n_valid": len(nec),
            "mean_C1_p_concept": (round(float(np.mean([c1[s] for s in nec])), 4) if nec else None),
            "necessity_specific_ci": bootci([rc[s] - c3[s] for s in nec]),
            "nec_selfswap_max_dev": (round(float(np.max([abs(c1[s] - ss[s]) for s in nec if s in ss])), 5) if nec else None),
            "sufficiency_specific_ci": bootci([s3[s] - sr[s] for s in suf]),
            "mean_S3_install_p_concept": (round(float(np.mean([s3[s] for s in suf])), 4) if suf else None),
            "suf_selfswap_max_dev": (round(float(np.max([abs(s1[s] - sss[s]) for s in suf if s in sss])), 5) if suf else None),
        }
    json.dump({"cohort": cohort, "model": args.model, "n_rows": len(all_rows),
               "n_valid_examples": len(valid), "granularity": args.granularity, "windows": summ},
              open(os.path.join(out_dir, "summary.json"), "w"), indent=1)
    print(f"[mlpKO] {len(all_rows)} rows, {len(valid)} valid examples -> {out_dir}")
    for w, s in summ.items():
        print(f"  {w}: n={s['n_valid']} C1={s['mean_C1_p_concept']} "
              f"NEC_specific(rand-C3)={s['necessity_specific_ci']} "
              f"SUF_specific(S3-Srand)={s['sufficiency_specific_ci']} S3={s['mean_S3_install_p_concept']}")


if __name__ == "__main__":
    main()
