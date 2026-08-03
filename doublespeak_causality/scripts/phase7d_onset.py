#!/usr/bin/env python3
"""Phase 7d (sufficiency ONSET): WHERE does the concept become transplantable? Phase 7c showed the
L14–21 carry head-SET is (partially) sufficient. This installs CUMULATIVE carry subsets (L14 only,
L14–15, L14–17, L14–18, L14–21) DS→benign and reads p_concept, to locate the context-bound →
transplantable transition. One z-capture per example, reused across all groups (cheap).

Each group: p_concept(install DS group-z into benign). Controls per example: benign baseline S1,
random-head install S_rand (same count as the FULL set), self-install S_self (no-op). Reuses the
phase7c machinery verbatim (ZHeadCapture/ZHeadPatch, FC readout).

Usage: python scripts/phase7d_onset.py --bench data/bench/bench_curated.json --n-prompts 4
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
def ph(s):
    return [(int(l), int(h)) for l, h in re.findall(r"[Ll](\d+)[Hh](\d+)", s)]

# cumulative carry subsets (validated carry heads, added by layer)
GROUPS = {
    "L14":        "L14H4_L14H5_L14H23",
    "L14-15":     "L14H4_L14H5_L14H23_L15H8",
    "L14-17":     "L14H4_L14H5_L14H23_L15H8_L17H27",
    "L14-18":     "L14H4_L14H5_L14H23_L15H8_L17H27_L18H20",
    "L14-21":     "L14H4_L14H5_L14H23_L15H8_L17H27_L18H20_L21H10",
}
FULL = ph(GROUPS["L14-21"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bench", required=True)
    ap.add_argument("--model", default=dc.PRIMARY_MODEL)
    ap.add_argument("--out-root", default=os.path.join(DC, "outputs"))
    ap.add_argument("--splits", default="dev,heldout")
    ap.add_argument("--n-prompts", type=int, default=0)
    args = ap.parse_args()

    dc.set_seed(0); rng = np.random.default_rng(0)
    bench = json.load(open(args.bench)); lm = dc.load_model(args.model)
    dev = lm.model.device; L = lm.num_layers
    nH, hd = pc._attn_head_dims(lm.model)
    cohort = bench.get("_meta", {}).get("cohort", "?")
    groups = {k: ph(v) for k, v in GROUPS.items()}
    full_set = set(FULL)

    splits = [s.strip() for s in args.splits.split(",") if s.strip()]
    rows = [r for r in bench["semantic"] if r["split"] in splits]
    by_key = {(r["condition"], r["split"], r["sid"]): r for r in rows}
    ds_by = {sp: [r for r in rows if r["condition"] == "DOUBLESPEAK" and r["split"] == sp] for sp in splits}

    ts = time.strftime("%Y%m%d_%H%M%S"); uniq = os.environ.get("SLURM_JOB_ID") or str(os.getpid())
    out_dir = os.path.join(args.out_root, f"phase7d_onset_{cohort}_{ts}_{uniq}")
    os.makedirs(out_dir, exist_ok=True); fh = open(os.path.join(out_dir, "raw.jsonl"), "w")
    print(f"[onset] cohort={cohort} groups={list(groups)} -> {out_dir}")

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

    def install(zsrc, heads, pos):
        return [pc.ZHeadPatch(lm.model, l, h, [pos], zsrc[l][h]) for (l, h) in heads]

    for split in splits:
        cand = sorted(ds_by.get(split, []), key=lambda r: r["sid"])
        if args.n_prompts: cand = cand[:args.n_prompts]
        for r in cand:
            co, cw = r["target_concept"], r["codeword"]
            cid, kid = _sid(lm.tokenizer, co), _sid(lm.tokenizer, cw)
            if cid == kid: continue
            brow = by_key.get(("BENIGN_REMAP", split, r["sid"]))
            if brow is None: continue
            ds_tok = build_fc(r["prompt"], cw, co); b_tok = build_fc(brow["prompt"], cw, co)
            z_ds, _ = cap_headz_last(ds_tok); z_b, b_last = cap_headz_last(b_tok)
            rec = {"sid": r["sid"], "split": split, "cohort": cohort,
                   "S1": readout(b_tok, cid, kid)}
            for g, heads in groups.items():
                rec[g] = readout(b_tok, cid, kid, install(z_ds, heads, b_last))
            pool = [(l, h) for l in range(L) for h in range(nH) if (l, h) not in full_set]
            rand_heads = [pool[i] for i in rng.choice(len(pool), size=len(FULL), replace=False)]
            rec["S_rand"] = readout(b_tok, cid, kid, install(z_ds, rand_heads, b_last))
            rec["S_self"] = readout(b_tok, cid, kid, install(z_b, FULL, b_last))
            fh.write(json.dumps(rec) + "\n")
    fh.close()

    allr = [json.loads(x) for x in open(os.path.join(out_dir, "raw.jsonl"))]
    rng2 = np.random.default_rng(0)
    def ci(v):
        if not v: return None
        a = np.array(v); b = [rng2.choice(a, len(a), replace=True).mean() for _ in range(2000)]
        return [round(float(a.mean()), 4), round(float(np.percentile(b, 2.5)), 4), round(float(np.percentile(b, 97.5)), 4)]
    summ = {}
    for split in splits:
        sr = [r for r in allr if r["split"] == split]
        srand = float(np.mean([r["S_rand"] for r in sr])) if sr else 0.0
        summ[split] = {"n": len(sr), "S1": round(float(np.mean([r["S1"] for r in sr])), 4) if sr else None,
                       "S_rand": round(srand, 4),
                       "self_dev": round(float(np.max([abs(r["S_self"] - r["S1"]) for r in sr])), 5) if sr else None,
                       "cumulative_p_concept": {g: (round(float(np.mean([r[g] for r in sr])), 4) if sr else None) for g in groups},
                       "specific_over_rand": {g: ci([r[g] - r["S_rand"] for r in sr]) for g in groups}}
    json.dump({"cohort": cohort, "groups": GROUPS, "by_split": summ},
              open(os.path.join(out_dir, "summary.json"), "w"), indent=1)
    print(f"[onset] {len(allr)} rows -> {out_dir}")
    for sp, s in summ.items():
        print(f"  [{sp}] n={s['n']} S1={s['S1']} S_rand={s['S_rand']} selfdev={s['self_dev']}")
        print(f"     cumulative p_concept: {s['cumulative_p_concept']}")


if __name__ == "__main__":
    main()
