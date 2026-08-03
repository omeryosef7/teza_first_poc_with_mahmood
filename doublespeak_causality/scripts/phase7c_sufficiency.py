#!/usr/bin/env python3
"""Phase 7c (carry-head SUFFICIENCY): install the DS carry-head answer-position z into a BENIGN
receiver — does the concept reading APPEAR? Completes the necessity+sufficiency pair for the carry
band (Phase 5/7 = necessity; here = sufficiency). Mirrors phase6 S3 (which was ≈0) for heads.

Arms (receiver = BENIGN FC prompt; readout = FC p_concept):
  S1        benign baseline
  S3_carry  install DS carry-head z at benign answer position (sufficiency)
  S_rand    install DS z from the SAME COUNT of random non-carry heads (specificity control)
  S_self    install benign's OWN carry-head z (no-op check, must ≈ S1)
sufficiency_specific = S3_carry − S_rand (paired). Reuses pc.ZHeadCapture / pc.ZHeadPatch.

Usage:
  python scripts/phase7c_sufficiency.py --bench data/bench/bench_curated.json \
      --carry L14H4_L14H5_L14H23_L15H8_L17H27_L18H20_L21H10 --n-prompts 4
"""
from __future__ import annotations
import argparse, json, os, re, sys, time
from contextlib import ExitStack
import numpy as np
import torch

HERE = os.path.dirname(os.path.abspath(__file__)); DC = os.path.dirname(HERE)
sys.path.insert(0, DC)
import ds_common as dc
import pair_common as pc

FC_PREFIX = "Choose one label only and answer with just that label."
def fc_question(cw, co):
    return f'{FC_PREFIX} In the text above, does the word "{cw}" refer to "{co}" or to "{cw}"?'
def demo_block_of(p, m="\n\nDo not reason, just "):
    return p.rsplit(m, 1)[0] if m in p else p
def _sid(tok, w):
    return tok.encode(" " + w, add_special_tokens=False)[0]
def parse_heads(s):
    return [(int(l), int(h)) for l, h in re.findall(r"[Ll](\d+)[Hh](\d+)", s)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bench", required=True)
    ap.add_argument("--model", default=dc.PRIMARY_MODEL)
    ap.add_argument("--out-root", default=os.path.join(DC, "outputs"))
    ap.add_argument("--splits", default="dev,heldout")
    ap.add_argument("--carry", required=True)
    ap.add_argument("--n-prompts", type=int, default=0)
    args = ap.parse_args()

    dc.set_seed(0); rng = np.random.default_rng(0)
    bench = json.load(open(args.bench)); lm = dc.load_model(args.model)
    dev = lm.model.device; L = lm.num_layers
    nH, hd = pc._attn_head_dims(lm.model)
    cohort = bench.get("_meta", {}).get("cohort", "?")
    carry = parse_heads(args.carry); carry_set = set(carry)

    splits = [s.strip() for s in args.splits.split(",") if s.strip()]
    rows = [r for r in bench["semantic"] if r["split"] in splits]
    by_key = {(r["condition"], r["split"], r["sid"]): r for r in rows}
    ds_by = {sp: [r for r in rows if r["condition"] == "DOUBLESPEAK" and r["split"] == sp] for sp in splits}

    ts = time.strftime("%Y%m%d_%H%M%S"); uniq = os.environ.get("SLURM_JOB_ID") or str(os.getpid())
    out_dir = os.path.join(args.out_root, f"phase7c_suffic_{cohort}_{ts}_{uniq}")
    os.makedirs(out_dir, exist_ok=True); fh = open(os.path.join(out_dir, "raw.jsonl"), "w")
    print(f"[suf] cohort={cohort} carry={carry} -> {out_dir}")

    def build_fc(raw, cw, co):
        t = dc.apply_template(lm.tokenizer, demo_block_of(raw) + "\n\n" + fc_question(cw, co))
        return lm.tokenizer(t, return_tensors="pt", add_special_tokens=False).to(dev)

    @torch.no_grad()
    def readout(tok, cid, kid, ctx=()):
        with ExitStack() as st:
            for c in ctx: st.enter_context(c)
            out = lm.model(**tok, return_dict=True)
        p = torch.softmax(out.logits[0, -1, :].float(), -1)
        pcv, pkv = float(p[cid]), float(p[kid])
        return pcv / (pcv + pkv + 1e-12)

    @torch.no_grad()
    def cap_headz_last(tok):
        last = tok["input_ids"].shape[1] - 1
        with pc.ZHeadCapture(lm.model, list(range(L))) as c:
            lm.model(**tok, return_dict=True)
        return {l: c.acts[l][0, last].view(nH, hd).float().to(dev) for l in range(L)}, last

    for split in splits:
        cand = sorted(ds_by.get(split, []), key=lambda r: r["sid"])
        if args.n_prompts: cand = cand[:args.n_prompts]
        for r in cand:
            co, cw = r["target_concept"], r["codeword"]
            cid, kid = _sid(lm.tokenizer, co), _sid(lm.tokenizer, cw)
            if cid == kid: continue
            brow = by_key.get(("BENIGN_REMAP", split, r["sid"]))
            if brow is None: continue
            ds_tok = build_fc(r["prompt"], cw, co)
            b_tok = build_fc(brow["prompt"], cw, co)
            z_ds, _ = cap_headz_last(ds_tok)              # DS carry-head donor
            z_b, b_last = cap_headz_last(b_tok)           # benign own (for self-check) + position

            S1 = readout(b_tok, cid, kid)
            inst_carry = [pc.ZHeadPatch(lm.model, l, h, [b_last], z_ds[l][h]) for (l, h) in carry]
            S3 = readout(b_tok, cid, kid, inst_carry)
            pool = [(l, h) for l in range(L) for h in range(nH) if (l, h) not in carry_set]
            rand_heads = [pool[i] for i in rng.choice(len(pool), size=len(carry), replace=False)]
            inst_rand = [pc.ZHeadPatch(lm.model, l, h, [b_last], z_ds[l][h]) for (l, h) in rand_heads]
            Sr = readout(b_tok, cid, kid, inst_rand)
            inst_self = [pc.ZHeadPatch(lm.model, l, h, [b_last], z_b[l][h]) for (l, h) in carry]
            Ss = readout(b_tok, cid, kid, inst_self)
            fh.write(json.dumps({"sid": r["sid"], "split": split, "cohort": cohort,
                                 "S1": S1, "S3_carry": S3, "S_rand": Sr, "S_self": Ss}) + "\n")
    fh.close()

    allr = [json.loads(x) for x in open(os.path.join(out_dir, "raw.jsonl"))]
    rng2 = np.random.default_rng(0)
    def bootci(v):
        if not v: return None
        a = np.array(v); b = [rng2.choice(a, len(a), replace=True).mean() for _ in range(2000)]
        return [round(float(a.mean()), 4), round(float(np.percentile(b, 2.5)), 4), round(float(np.percentile(b, 97.5)), 4)]
    summ = {}
    for split in splits:
        sr = [r for r in allr if r["split"] == split]
        summ[split] = {
            "n": len(sr),
            "mean_S1_benign": round(float(np.mean([r["S1"] for r in sr])), 4) if sr else None,
            "mean_S3_carry_install": round(float(np.mean([r["S3_carry"] for r in sr])), 4) if sr else None,
            "sufficiency_raw_ci_S3_minus_S1": bootci([r["S3_carry"] - r["S1"] for r in sr]),
            "sufficiency_specific_ci_S3_minus_Srand": bootci([r["S3_carry"] - r["S_rand"] for r in sr]),
            "self_install_max_dev": round(float(np.max([abs(r["S_self"] - r["S1"]) for r in sr])), 5) if sr else None,
        }
    json.dump({"cohort": cohort, "carry": args.carry, "by_split": summ},
              open(os.path.join(out_dir, "summary.json"), "w"), indent=1)
    print(f"[suf] {len(allr)} rows -> {out_dir}")
    for sp, s in summ.items():
        print(f"  [{sp}] n={s['n']} S1={s['mean_S1_benign']} S3={s['mean_S3_carry_install']} "
              f"suf_raw={s['sufficiency_raw_ci_S3_minus_S1']} suf_specific={s['sufficiency_specific_ci_S3_minus_Srand']} "
              f"selfdev={s['self_install_max_dev']}")


if __name__ == "__main__":
    main()
