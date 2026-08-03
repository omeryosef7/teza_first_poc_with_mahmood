#!/usr/bin/env python3
"""Phase 9 (dose-response): is the L9 (mid-band) demo-codeword MLP write a GRADED causal lever,
or an on/off artifact? Interpolate the demo-position mlp_out patch DS→BENIGN at increasing alpha
and read the FC concept probability. A monotone dose-response (p_concept falling with alpha) is
the plan's evidence for a genuine handle; one isolated successful coefficient is not.

Reuses the audited phase6 machinery: same FC DE_context readout, same demo-codeword positions,
same pc.ComponentOutSwap (patched with an INTERPOLATED donor (1-a)*DS + a*BENIGN per position).
alpha=0 == DS baseline (exact no-op check); alpha=1 == full benign swap (== phase6 C3 necessity).

Usage:
  python scripts/phase9_dose.py --bench data/bench/bench_curated.json --layers 9 --n-prompts 4
"""
from __future__ import annotations
import argparse, json, os, sys, time
from contextlib import ExitStack
import numpy as np
import torch

HERE = os.path.dirname(os.path.abspath(__file__))
DC = os.path.dirname(HERE)
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bench", required=True)
    ap.add_argument("--model", default=dc.PRIMARY_MODEL)
    ap.add_argument("--out-root", default=os.path.join(DC, "outputs"))
    ap.add_argument("--splits", default="dev,heldout")
    ap.add_argument("--layers", default="9", help="dash-range or single layer(s), applied jointly")
    ap.add_argument("--alphas", default="0,0.25,0.5,0.75,1.0,1.5,2.0")
    ap.add_argument("--n-prompts", type=int, default=0)
    args = ap.parse_args()

    dc.set_seed(0)
    bench = json.load(open(args.bench))
    lm = dc.load_model(args.model)
    dev = lm.model.device
    cohort = bench.get("_meta", {}).get("cohort", "?")
    if "-" in args.layers:
        a, b = args.layers.split("-"); ells = list(range(int(a), int(b) + 1))
    else:
        ells = [int(x) for x in args.layers.split(",") if x.strip()]
    alphas = [float(x) for x in args.alphas.split(",")]

    splits = [s.strip() for s in args.splits.split(",") if s.strip()]
    rows = [r for r in bench["semantic"] if r["split"] in splits]
    by_key = {(r["condition"], r["split"], r["sid"]): r for r in rows}
    ds_by = {sp: [r for r in rows if r["condition"] == "DOUBLESPEAK" and r["split"] == sp] for sp in splits}

    ts = time.strftime("%Y%m%d_%H%M%S"); uniq = os.environ.get("SLURM_JOB_ID") or str(os.getpid())
    out_dir = os.path.join(args.out_root, f"phase9_dose_{cohort}_L{'_'.join(map(str,ells))}_{ts}_{uniq}")
    os.makedirs(out_dir, exist_ok=True)
    fh = open(os.path.join(out_dir, "raw.jsonl"), "w")
    print(f"[dose] cohort={cohort} layers={ells} alphas={alphas} -> {out_dir}")

    def build_fc(raw, cw, co):
        t = dc.apply_template(lm.tokenizer, demo_block_of(raw) + "\n\n" + fc_question(cw, co))
        q = t.rfind(FC_PREFIX); qt = len(lm.tokenizer(t[:q], add_special_tokens=False)["input_ids"])
        hit = dc.find_word_occurrences_in_text(lm.tokenizer, t, cw)
        demo = [li for span, li in zip(hit.spans, hit.last_idx) if span[0] < qt]
        return t, lm.tokenizer(t, return_tensors="pt", add_special_tokens=False).to(dev), demo

    @torch.no_grad()
    def readout(tok, cid, kid, ctx=()):
        with ExitStack() as st:
            for c in ctx: st.enter_context(c)
            out = lm.model(**tok, return_dict=True)
        p = torch.softmax(out.logits[0, -1, :].float(), -1)
        pcv, pkv = float(p[cid]), float(p[kid])
        return pcv / (pcv + pkv + 1e-12)

    @torch.no_grad()
    def capture(t, pos):
        tok = lm.tokenizer(t, return_tensors="pt", add_special_tokens=False).to(dev)
        with pc.ComponentCapture(lm, ["mlp_out"], pos) as cap:
            lm.model(**tok, return_dict=True)
        return cap.stacked()["mlp_out"]                     # [L, n_pos, H]

    for split in splits:
        cand = sorted(ds_by.get(split, []), key=lambda r: r["sid"])
        if args.n_prompts: cand = cand[:args.n_prompts]
        for r in cand:
            co, cw = r["target_concept"], r["codeword"]
            cid, kid = _sid(lm.tokenizer, co), _sid(lm.tokenizer, cw)
            if cid == kid: continue
            brow = by_key.get(("BENIGN_REMAP", split, r["sid"]))
            if brow is None: continue
            ds_t, ds_tok, ds_demo = build_fc(r["prompt"], cw, co)
            b_t, b_tok, b_demo = build_fc(brow["prompt"], cw, co)
            if not ds_demo or not b_demo: continue
            bench_p = readout(b_tok, cid, kid)
            m = min(len(ds_demo), len(b_demo))
            ds_pos, b_pos = ds_demo[-m:], b_demo[-m:]
            ds_cap = capture(ds_t, ds_demo)[:, -m:, :]      # [L,m,H] DS donor
            b_cap = capture(b_t, b_demo)[:, -m:, :]         # [L,m,H] BENIGN donor
            for a in alphas:
                src = {l: (1 - a) * ds_cap[l] + a * b_cap[l] for l in ells}   # interpolated donor
                p = readout(ds_tok, cid, kid,
                            [pc.ComponentOutSwap(lm.model, ds_pos, src, component="mlp_out")])
                fh.write(json.dumps({"sid": r["sid"], "split": split, "cohort": cohort, "alpha": a,
                                     "p_concept": p, "benign_p_concept": bench_p}) + "\n")
    fh.close()

    allr = [json.loads(x) for x in open(os.path.join(out_dir, "raw.jsonl"))]
    summ = {}
    for split in splits:
        sr = [r for r in allr if r["split"] == split]
        valid = {r["sid"] for r in sr if r["alpha"] == 0.0 and r["p_concept"] > r["benign_p_concept"]}
        curve = {}
        for a in alphas:
            vals = [r["p_concept"] for r in sr if r["alpha"] == a and r["sid"] in valid]
            curve[a] = round(float(np.mean(vals)), 4) if vals else None
        # monotone-decreasing check (dose response)
        seq = [curve[a] for a in alphas if curve[a] is not None]
        mono = all(seq[i] >= seq[i + 1] - 1e-6 for i in range(len(seq) - 1)) if len(seq) > 1 else None
        summ[split] = {"n_valid": len(valid), "p_concept_by_alpha": curve, "monotone_decreasing": mono}
    json.dump({"cohort": cohort, "layers": ells, "alphas": alphas, "by_split": summ},
              open(os.path.join(out_dir, "summary.json"), "w"), indent=1)
    print(f"[dose] {len(allr)} rows -> {out_dir}")
    for sp, s in summ.items():
        print(f"  [{sp}] n={s['n_valid']} monotone={s['monotone_decreasing']} p(alpha)={s['p_concept_by_alpha']}")


if __name__ == "__main__":
    main()
