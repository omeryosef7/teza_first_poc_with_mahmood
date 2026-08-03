#!/usr/bin/env python3
"""Phase 4.2: SURGICAL per-head query->demonstration attention-edge knockout (induction test).

The prior all-layer edge knockout (N7-M) was degenerate (masking everything raises p_concept as an
artifact). This does the surgical version: for EACH (layer, head), knock out ONLY the edges from the
query-codeword position(s) to the DEMONSTRATION-codeword positions, and read the forced-choice reading.
A head is a retrieval head if that knockout reduces the reading MORE than a matched random-edge control.

Eager attention required (AttentionKnockout edits the 4-D additive mask pre-softmax). Multi-concept:
per-row concept/codeword, FC DE_context readout (same as phase3_demo_neutralize). Forced-choice, no API.

Cells per (layer, head): edge_KO (query->demo edges), rand_edge (query->count-matched random source).
Plus a per-example baseline. Effect = baseline_p_concept - KO_p_concept; specific = rand_KO_drop - demo_KO...
we record raw p_concept per cell and aggregate specific = (rand_edge) - (edge_KO), paired, bootstrap CI.

Usage:
  python scripts/phase4_edge_knockout.py --bench data/bench/bench_curated.json --n-prompts 2 --layers 8,9,10,11
  python scripts/phase4_edge_knockout.py --bench data/bench/bench_curated.json --n-prompts 25   # all layers
"""
from __future__ import annotations
import argparse, json, os, random, sys, time
from collections import defaultdict
import numpy as np
import torch

HERE = os.path.dirname(os.path.abspath(__file__))
DC = os.path.dirname(HERE)
sys.path.insert(0, DC)
import ds_common as dc
import pair_common as pc

FC_PREFIX = "Choose one label only and answer with just that label."
def fc_question(cw, concept):
    return (f'{FC_PREFIX} In the text above, does the word "{cw}" refer to "{concept}" or to "{cw}"?')
def demo_block_of(p, marker="\n\nDo not reason, just "):
    return p.rsplit(marker, 1)[0] if marker in p else p


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bench", required=True)
    ap.add_argument("--model", default=dc.PRIMARY_MODEL)
    ap.add_argument("--out-root", default=os.path.join(DC, "outputs"))
    ap.add_argument("--splits", default="dev,heldout")
    ap.add_argument("--layers", default="", help="comma list; empty = all layers")
    ap.add_argument("--n-prompts", type=int, default=0)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    dc.set_seed(args.seed)
    rng = random.Random(args.seed)
    bench = json.load(open(args.bench))
    lm = dc.load_model(args.model, attn_implementation="eager")   # REQUIRED for AttentionKnockout
    L = lm.num_layers
    Hn = int(lm.model.config.num_attention_heads)
    dev = lm.model.device
    cohort = bench.get("_meta", {}).get("cohort", "?")
    layers = [int(x) for x in args.layers.split(",") if x.strip()] or list(range(L))

    splits = [s.strip() for s in args.splits.split(",") if s.strip()]
    rows = [r for r in bench["semantic"] if r["split"] in splits]
    by_key = {(r["condition"], r["split"], r["sid"]): r for r in rows}
    ds_rows = defaultdict(list)
    for r in rows:
        if r["condition"] == "DOUBLESPEAK":
            ds_rows[r["split"]].append(r)

    ts = time.strftime("%Y%m%d_%H%M%S")
    uniq = os.environ.get("SLURM_JOB_ID") or str(os.getpid())
    out_dir = os.path.join(args.out_root, f"phase4_edgeKO_{cohort}_{ts}_{uniq}")
    os.makedirs(out_dir, exist_ok=True)
    fh = open(os.path.join(out_dir, "raw.jsonl"), "w")
    print(f"[edgeKO] cohort={cohort} L={L} Hn={Hn} layers={layers[:6]}{'...' if len(layers)>6 else ''} -> {out_dir}")

    def build_fc(raw_prompt, cw, concept):
        fc_raw = demo_block_of(raw_prompt) + "\n\n" + fc_question(cw, concept)
        templated = dc.apply_template(lm.tokenizer, fc_raw)
        q_off = templated.rfind(FC_PREFIX)
        hit = dc.find_word_occurrences_in_text(lm.tokenizer, templated, cw)
        demo_pos = [li for span, li in zip(hit.spans, hit.last_idx) if span[0] < q_off]
        query_pos = [li for span, li in zip(hit.spans, hit.last_idx) if span[0] >= q_off]
        tok = lm.tokenizer(templated, return_tensors="pt", add_special_tokens=False).to(dev)
        seqlen = tok["input_ids"].shape[1]
        return tok, demo_pos, query_pos, seqlen

    @torch.no_grad()
    def readout(tok, cid, kid, ctx=()):
        from contextlib import ExitStack
        with ExitStack() as st:
            for c in ctx:
                st.enter_context(c)
            out = lm.model(**tok, return_dict=True)
        probs = torch.softmax(out.logits[0, -1, :].float(), dim=-1)
        pc_, pk_ = float(probs[cid]), float(probs[kid])
        return pc_ / (pc_ + pk_ + 1e-12)

    n_rows = 0
    for split in splits:
        cand = sorted(ds_rows.get(split, []), key=lambda r: r["sid"])
        if args.n_prompts:
            cand = cand[: args.n_prompts]
        for r in cand:
            concept, cw = r["target_concept"], r["codeword"]
            cid = lm.tokenizer.encode(" " + concept, add_special_tokens=False)[0]
            kid = lm.tokenizer.encode(" " + cw, add_special_tokens=False)[0]
            tok, demo_pos, query_pos, seqlen = build_fc(r["prompt"], cw, concept)
            if not demo_pos or not query_pos:
                continue
            # destinations = codeword mentions in the question + the final (answer) position
            qdest = sorted(set(query_pos + [seqlen - 1]))
            # validity: DS must read concept; benign must not
            brow = by_key.get(("BENIGN_REMAP", split, r["sid"]))
            btok, _, _, _ = build_fc(brow["prompt"], cw, concept) if brow else (None, None, None, None)
            benign_pc = readout(btok, cid, kid) if btok is not None else None
            base_pc = readout(tok, cid, kid)
            valid = benign_pc is not None and base_pc > benign_pc

            # count-matched random source keys (non-demo, causal, before the first destination)
            first_dest = min(qdest)
            demoset = set(demo_pos)
            pool = [p for p in range(first_dest) if p not in demoset]
            k = len(demo_pos)
            rand_src = sorted(rng.sample(pool, min(k, len(pool)))) if pool else []

            brow_row = {"sid": r["sid"], "split": split, "cohort": cohort, "concept": concept,
                        "codeword": cw, "valid": valid, "base_p_concept": base_pc,
                        "benign_p_concept": benign_pc, "n_demo_edges": k}
            for lyr in layers:
                for h in range(Hn):
                    ko = pc.AttentionKnockout(lm.model, [lyr], qdest, demo_pos, heads=[h])
                    p_ko = readout(tok, cid, kid, [ko])
                    rec = {**brow_row, "layer": lyr, "head": h, "cell": "edge_KO", "p_concept": p_ko}
                    fh.write(json.dumps(rec) + "\n"); n_rows += 1
                    if rand_src:
                        rk = pc.AttentionKnockout(lm.model, [lyr], qdest, rand_src, heads=[h])
                        p_rk = readout(tok, cid, kid, [rk])
                        fh.write(json.dumps({**brow_row, "layer": lyr, "head": h,
                                             "cell": "rand_edge", "p_concept": p_rk}) + "\n"); n_rows += 1
    fh.close()

    # aggregate: per (layer, head) specific effect = mean over valid examples of (rand_edge - edge_KO)
    all_rows = [json.loads(x) for x in open(os.path.join(out_dir, "raw.jsonl"))]
    rng2 = np.random.default_rng(0)
    base = {r["sid"]: r["base_p_concept"] for r in all_rows}
    cells = defaultdict(dict)   # (layer,head,cell) -> {sid: p}
    for r in all_rows:
        if r["valid"]:
            cells[(r["layer"], r["head"], r["cell"])][r["sid"]] = r["p_concept"]
    results = []
    for lyr in layers:
        for h in range(Hn):
            ko = cells.get((lyr, h, "edge_KO"), {})
            rk = cells.get((lyr, h, "rand_edge"), {})
            sids = set(ko) & set(rk)
            if len(sids) < 3:
                continue
            spec = np.array([rk[s] - ko[s] for s in sids])       # >0 => demo-edge KO drops more than random
            drop = np.array([base[s] - ko[s] for s in sids])     # raw KO drop
            boot = [rng2.choice(spec, len(spec), replace=True).mean() for _ in range(1000)]
            lo, hi = np.percentile(boot, [2.5, 97.5])
            results.append({"layer": lyr, "head": h, "n": len(sids),
                            "specific_mean": round(float(spec.mean()), 4),
                            "specific_ci": [round(float(lo), 4), round(float(hi), 4)],
                            "raw_KO_drop": round(float(drop.mean()), 4),
                            "sig": bool(lo > 0)})
    results.sort(key=lambda x: -x["specific_mean"])
    json.dump({"cohort": cohort, "model": args.model, "n_valid": len({r["sid"] for r in all_rows if r["valid"]}),
               "layers": layers, "n_heads": Hn, "top_heads": results[:30],
               "n_sig_heads": sum(1 for r in results if r["sig"])},
              open(os.path.join(out_dir, "summary.json"), "w"), indent=1)
    print(f"[edgeKO] {n_rows} rows -> {out_dir}; {sum(1 for r in results if r['sig'])} sig heads")
    for r in results[:10]:
        print(f"  L{r['layer']}H{r['head']}: specific={r['specific_mean']} CI={r['specific_ci']} "
              f"rawdrop={r['raw_KO_drop']} n={r['n']} {'SIG' if r['sig'] else ''}")


if __name__ == "__main__":
    main()
