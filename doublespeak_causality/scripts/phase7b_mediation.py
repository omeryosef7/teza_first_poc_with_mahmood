#!/usr/bin/env python3
"""Phase 7b (circuit closure): does the L14–L21 CARRY band READ the L9 MLP write? Mediation
path-patch connecting the two validated halves (L9 demo-write → L14–21 answer-carry).

Idea: neutralizing the L9 demo-codeword MLP write drops the reading (Δ_total, = Phase 6 necessity).
If that effect FLOWS THROUGH the carry heads, then FREEZING the carry heads' answer-position z to
their clean (DS) values — so they output the concept contribution regardless of the L9 change —
should BLOCK the drop (restore the reading). mediation_frac = (p_blocked − p_neutralized) /
(C1 − p_neutralized): ≈1 ⇒ the L9 effect is mediated by the carry band; ≈0 ⇒ it is not.

Arms (clean = DS FC prompt; readout = FC p_concept):
  C1              DS baseline
  A_neutralizeL9  ComponentOutSwap(L9 mlp_out ← BENIGN at demo)                     (= Phase-6 L9 necessity)
  B_L9_freezeCarry A + freeze CARRY-head z ← clean DS at the answer position         (block the mediated path)
  ctrl_freezeRand A + freeze the SAME COUNT of RANDOM non-carry heads ← clean DS      (specificity control)
  selfcheck       freeze CARRY-head z ← clean DS (no L9 change) — must ≈ C1 (no-op)
Reuses pc.ComponentOutSwap (mlp write), pc.ZHeadPatch (freeze one head's z), pc.ZHeadCapture (clean z).

Usage:
  python scripts/phase7b_mediation.py --bench data/bench/bench_curated.json \
      --carry L14H4,L14H5,L14H23,L15H8,L17H27,L18H20,L21H10 --write-layer 9 --n-prompts 4
"""
from __future__ import annotations
import argparse, json, os, re, sys, time
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
def parse_heads(s):
    return [(int(l), int(h)) for l, h in re.findall(r"[Ll](\d+)[Hh](\d+)", s)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bench", required=True)
    ap.add_argument("--model", default=dc.PRIMARY_MODEL)
    ap.add_argument("--out-root", default=os.path.join(DC, "outputs"))
    ap.add_argument("--splits", default="dev,heldout")
    ap.add_argument("--carry", required=True, help="carry heads, e.g. L14H4,L15H8,...")
    ap.add_argument("--write-layer", type=int, default=9)
    ap.add_argument("--n-prompts", type=int, default=0)
    args = ap.parse_args()

    dc.set_seed(0); rng = np.random.default_rng(0)
    bench = json.load(open(args.bench)); lm = dc.load_model(args.model)
    dev = lm.model.device; L = lm.num_layers
    nH, hd = pc._attn_head_dims(lm.model)
    cohort = bench.get("_meta", {}).get("cohort", "?")
    carry = parse_heads(args.carry)
    carry_set = set(carry)
    WL = args.write_layer

    splits = [s.strip() for s in args.splits.split(",") if s.strip()]
    rows = [r for r in bench["semantic"] if r["split"] in splits]
    by_key = {(r["condition"], r["split"], r["sid"]): r for r in rows}
    ds_by = {sp: [r for r in rows if r["condition"] == "DOUBLESPEAK" and r["split"] == sp] for sp in splits}

    ts = time.strftime("%Y%m%d_%H%M%S"); uniq = os.environ.get("SLURM_JOB_ID") or str(os.getpid())
    out_dir = os.path.join(args.out_root, f"phase7b_mediation_{cohort}_{ts}_{uniq}")
    os.makedirs(out_dir, exist_ok=True); fh = open(os.path.join(out_dir, "raw.jsonl"), "w")
    print(f"[med] cohort={cohort} carry={carry} write=L{WL} -> {out_dir}")

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
    def cap_mlp(t, pos):
        tok = lm.tokenizer(t, return_tensors="pt", add_special_tokens=False).to(dev)
        with pc.ComponentCapture(lm, ["mlp_out"], pos) as cap:
            lm.model(**tok, return_dict=True)
        return cap.stacked()["mlp_out"]

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
            ds_t, ds_tok, ds_demo = build_fc(r["prompt"], cw, co)
            b_t, b_tok, b_demo = build_fc(brow["prompt"], cw, co)
            if not ds_demo or not b_demo: continue
            m = min(len(ds_demo), len(b_demo)); ds_pos = ds_demo[-m:]
            b_mlp = cap_mlp(b_t, b_demo)[:, -m:, :]        # benign L9 donor at demo
            z_ds, ds_last = cap_headz_last(ds_tok)         # clean DS carry-head z at answer

            C1 = readout(ds_tok, cid, kid)
            pA = readout(ds_tok, cid, kid, [pc.ComponentOutSwap(lm.model, ds_pos, {WL: b_mlp[WL]}, "mlp_out")])
            # freeze carry heads to clean DS z at answer (+ neutralize L9)
            freeze_carry = [pc.ZHeadPatch(lm.model, l, h, [ds_last], z_ds[l][h]) for (l, h) in carry]
            pB = readout(ds_tok, cid, kid,
                         [pc.ComponentOutSwap(lm.model, ds_pos, {WL: b_mlp[WL]}, "mlp_out")] + freeze_carry)
            # control: freeze same count of RANDOM non-carry heads to clean DS z
            pool = [(l, h) for l in range(L) for h in range(nH) if (l, h) not in carry_set]
            ridx = rng.choice(len(pool), size=len(carry), replace=False)
            rand_heads = [pool[i] for i in ridx]
            freeze_rand = [pc.ZHeadPatch(lm.model, l, h, [ds_last], z_ds[l][h]) for (l, h) in rand_heads]
            pC = readout(ds_tok, cid, kid,
                         [pc.ComponentOutSwap(lm.model, ds_pos, {WL: b_mlp[WL]}, "mlp_out")] + freeze_rand)
            # self-check: freeze carry heads WITHOUT L9 change -> ~C1 (clean z is a no-op)
            pSelf = readout(ds_tok, cid, kid,
                            [pc.ZHeadPatch(lm.model, l, h, [ds_last], z_ds[l][h]) for (l, h) in carry])
            fh.write(json.dumps({"sid": r["sid"], "split": split, "cohort": cohort,
                                 "C1": C1, "A_neutralizeL9": pA, "B_L9_freezeCarry": pB,
                                 "ctrl_freezeRand": pC, "selfcheck": pSelf}) + "\n")
    fh.close()

    allr = [json.loads(x) for x in open(os.path.join(out_dir, "raw.jsonl"))]
    def med(rows):
        # mediation_frac = (pB - pA)/(C1 - pA), on examples where L9 neutralization actually dropped it
        v = [(r["B_L9_freezeCarry"] - r["A_neutralizeL9"]) / (r["C1"] - r["A_neutralizeL9"])
             for r in rows if (r["C1"] - r["A_neutralizeL9"]) > 0.02]
        c = [(r["ctrl_freezeRand"] - r["A_neutralizeL9"]) / (r["C1"] - r["A_neutralizeL9"])
             for r in rows if (r["C1"] - r["A_neutralizeL9"]) > 0.02]
        return v, c
    summ = {}
    for split in splits:
        sr = [r for r in allr if r["split"] == split]
        v, c = med(sr)
        selfdev = max((abs(r["C1"] - r["selfcheck"]) for r in sr), default=None)
        summ[split] = {
            "n": len(sr), "n_L9_responsive": len(v),
            "mean_C1": round(float(np.mean([r["C1"] for r in sr])), 4) if sr else None,
            "mean_A_neutralizeL9": round(float(np.mean([r["A_neutralizeL9"] for r in sr])), 4) if sr else None,
            "median_mediation_frac_carry": round(float(np.median(v)), 3) if v else None,
            "median_mediation_frac_randctrl": round(float(np.median(c)), 3) if c else None,
            "selfcheck_max_dev": round(selfdev, 5) if selfdev is not None else None,
        }
    json.dump({"cohort": cohort, "carry": args.carry, "write_layer": WL, "by_split": summ},
              open(os.path.join(out_dir, "summary.json"), "w"), indent=1)
    print(f"[med] {len(allr)} rows -> {out_dir}")
    for sp, s in summ.items():
        print(f"  [{sp}] n={s['n']} L9resp={s['n_L9_responsive']} C1={s['mean_C1']} "
              f"A(L9 neut)={s['mean_A_neutralizeL9']} med_carry={s['median_mediation_frac_carry']} "
              f"med_randctrl={s['median_mediation_frac_randctrl']} selfdev={s['selfcheck_max_dev']}")


if __name__ == "__main__":
    main()
