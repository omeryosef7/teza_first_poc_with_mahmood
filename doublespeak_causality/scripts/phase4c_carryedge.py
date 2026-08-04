#!/usr/bin/env python3
"""Phase 4c: do the CARRY heads (L14–21) retrieve the concept by attending to the DEMONSTRATION
codewords? Knock out specifically the carry heads' ANSWER-position → demo-codeword attention edges
(pc.AttentionKnockout, eager) and read FC p_concept. Localizes WHERE in the carry-head attention
pattern (Phase 4b showed the whole answer-row pattern is causal) the concept comes from.

Cells (receiver = DS FC prompt; readout = FC p_concept):
  C1        baseline
  KO_demo   knock out carry heads' answer→demo-codeword edges (necessity)
  KO_rand   knock out carry heads' answer→count-matched RANDOM non-demo keys (specificity control)
Necessity = C1 − KO_demo ; specific = KO_rand − KO_demo (paired, bootstrap CI). Per split.
Reuses pc.AttentionKnockout (per-layer head groups), the phase7c FC readout, dc.find_word_occurrences.

Usage:
  python scripts/phase4c_carryedge.py --bench data/bench/bench_clearharm_v2.json \
      --carry L14H4_L14H5_L14H23_L15H8_L15H11_L17H24_L17H27_L18H20_L21H10 --n-prompts 4
"""
from __future__ import annotations
import argparse, json, os, re, sys, time
from collections import defaultdict
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
    bench = json.load(open(args.bench))
    lm = dc.load_model(args.model, attn_implementation="eager")   # REQUIRED for AttentionKnockout
    dev = lm.model.device
    cohort = bench.get("_meta", {}).get("cohort", "?")
    carry = parse_heads(args.carry)
    by_layer = defaultdict(list)
    for l, h in carry:
        by_layer[l].append(h)

    splits = [s.strip() for s in args.splits.split(",") if s.strip()]
    rows = [r for r in bench["semantic"] if r["split"] in splits]
    by_key = {(r["condition"], r["split"], r["sid"]): r for r in rows}
    ds_by = {sp: [r for r in rows if r["condition"] == "DOUBLESPEAK" and r["split"] == sp] for sp in splits}

    ts = time.strftime("%Y%m%d_%H%M%S"); uniq = os.environ.get("SLURM_JOB_ID") or str(os.getpid())
    out_dir = os.path.join(args.out_root, f"phase4c_carryedge_{cohort}_{ts}_{uniq}")
    os.makedirs(out_dir, exist_ok=True); fh = open(os.path.join(out_dir, "raw.jsonl"), "w")
    print(f"[cedge] cohort={cohort} carry_layers={dict(by_layer)} -> {out_dir}")

    def build_fc(raw, cw, co):
        t = dc.apply_template(lm.tokenizer, demo_block_of(raw) + "\n\n" + fc_question(cw, co))
        q = t.rfind(FC_PREFIX); qt = len(lm.tokenizer(t[:q], add_special_tokens=False)["input_ids"])
        hit = dc.find_word_occurrences_in_text(lm.tokenizer, t, cw)
        demo = [li for span, li in zip(hit.spans, hit.last_idx) if span[0] < qt]
        tok = lm.tokenizer(t, return_tensors="pt", add_special_tokens=False).to(dev)
        return tok, demo

    @torch.no_grad()
    def readout(tok, cid, kid, ctx=()):
        with ExitStack() as st:
            for c in ctx:
                st.enter_context(c)
            out = lm.model(**tok, return_dict=True)
        p = torch.softmax(out.logits[0, -1, :].float(), -1)
        pcv, pkv = float(p[cid]), float(p[kid])
        return pcv / (pcv + pkv + 1e-12)

    def ko_ctx(ans_pos, keys):
        # one AttentionKnockout per carry layer, blocking answer→keys for that layer's carry heads
        return [pc.AttentionKnockout(lm.model, [l], [ans_pos], keys, heads=hs) for l, hs in by_layer.items()]

    for split in splits:
        cand = sorted(ds_by.get(split, []), key=lambda r: r["sid"])
        if args.n_prompts:
            cand = cand[: args.n_prompts]
        for r in cand:
            co, cw = r["target_concept"], r["codeword"]
            cid, kid = _sid(lm.tokenizer, co), _sid(lm.tokenizer, cw)
            if cid == kid:
                continue
            ds_tok, demo = build_fc(r["prompt"], cw, co)
            if not demo:
                continue
            ans = ds_tok["input_ids"].shape[1] - 1
            C1 = readout(ds_tok, cid, kid)
            KO_demo = readout(ds_tok, cid, kid, ko_ctx(ans, demo))
            # count-matched random non-demo keys before the answer position
            pool = [p for p in range(ans) if p not in set(demo)]
            rk = sorted(rng.choice(pool, size=min(len(demo), len(pool)), replace=False).tolist()) if pool else []
            KO_rand = readout(ds_tok, cid, kid, ko_ctx(ans, rk)) if rk else None
            # POSITIVE-firing control: block carry heads' answer -> ALL earlier keys (must change the
            # reading if the knockout fires AND the carry heads' attention matters at all).
            KO_all = readout(ds_tok, cid, kid, ko_ctx(ans, list(range(ans))))
            fh.write(json.dumps({"sid": r["sid"], "split": split, "cohort": cohort, "n_demo": len(demo),
                                 "C1": C1, "KO_demo": KO_demo, "KO_rand": KO_rand, "KO_all": KO_all}) + "\n")
    fh.close()

    allr = [json.loads(x) for x in open(os.path.join(out_dir, "raw.jsonl"))]
    rng2 = np.random.default_rng(0)
    def ci(v):
        v = [x for x in v if x is not None]
        if not v:
            return None
        a = np.array(v); b = [rng2.choice(a, len(a), replace=True).mean() for _ in range(2000)]
        return [round(float(a.mean()), 4), round(float(np.percentile(b, 2.5)), 4), round(float(np.percentile(b, 97.5)), 4)]
    summ = {}
    for split in splits:
        sr = [r for r in allr if r["split"] == split]
        summ[split] = {
            "n": len(sr),
            "mean_C1": round(float(np.mean([r["C1"] for r in sr])), 4) if sr else None,
            "necessity_raw_C1_minus_KOdemo": ci([r["C1"] - r["KO_demo"] for r in sr]),
            "specific_KOrand_minus_KOdemo": ci([r["KO_rand"] - r["KO_demo"] for r in sr if r["KO_rand"] is not None]),
            "posctrl_C1_minus_KOall": ci([r["C1"] - r.get("KO_all", r["C1"]) for r in sr]),
        }
    json.dump({"cohort": cohort, "carry": args.carry, "by_split": summ},
              open(os.path.join(out_dir, "summary.json"), "w"), indent=1)
    print(f"[cedge] {len(allr)} rows -> {out_dir}")
    for sp, s in summ.items():
        print(f"  [{sp}] n={s['n']} C1={s['mean_C1']} necessity(C1-KOdemo)={s['necessity_raw_C1_minus_KOdemo']} "
              f"specific={s['specific_KOrand_minus_KOdemo']} POSCTRL(C1-KOall)={s['posctrl_C1_minus_KOall']}")


if __name__ == "__main__":
    main()
