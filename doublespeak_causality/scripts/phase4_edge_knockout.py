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
    ap.add_argument("--mode", default="perhead", choices=["perhead", "band"],
                    help="perhead = scan each (layer,head); band = all heads across all --layers jointly")
    # P3 (plan §5 P3) DESTINATION COVERAGE. Defaults reproduce the historical fused destination set
    # exactly, so every previously-published edge-knockout number is unchanged unless a flag is passed.
    ap.add_argument("--destinations", default="query_cw,answer",
                    help="comma list of destination sets: query_cw (codeword in the request line), "
                         "answer (final FC position). NOTE 'final_prompt' is an ALIAS of 'answer' in the "
                         "forced-choice form -- they are the same index -- so it is deliberately NOT offered "
                         "here; use --prompt-form decision for the genuinely different decision point.")
    ap.add_argument("--prompt-form", default="fc", choices=["fc", "decision"],
                    help="fc = forced-choice question (historical). decision = the bare templated prompt with "
                         "add_generation_prompt, whose final position IS the first-generated-token decision "
                         "point -- the destination plan §5 P3 says was never covered.")
    ap.add_argument("--readout", default="fc", choices=["fc", "refusal_proj"],
                    help="fc = forced-choice p_concept (needs the FC question). refusal_proj = last-token "
                         "residual projected on the per-layer refusal direction; REQUIRED for --prompt-form "
                         "decision, where no concept/codeword label exists at that position.")
    ap.add_argument("--proj-layer", type=int, default=18,
                    help="hidden_states row for --readout refusal_proj. Default 18. P7 "
                         "(reports/P7_REFUSAL_DIRECTION_VALIDATION.md §4c) generation-validated the per-layer "
                         "refusal directions: only DECODER layers 13-20,24,28,29 validate in BOTH direction "
                         "families, and hs row h == decoder layer h-1. hs18 = decoder L17, inside that set. "
                         "Do NOT point this at an unvalidated layer -- projecting on a direction that neither "
                         "ablates nor induces refusal is not a refusal measurement.")
    ap.add_argument("--refusal-dir", default=os.path.join(DC, "outputs", "refusal_alllayers"))
    ap.add_argument("--n-prompts", type=int, default=0)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    # NOT-YET-WIRED GUARD. --prompt-form decision and --readout refusal_proj are declared above (they are
    # the genuinely new P3 cell: the first-generated-token decision point, which has no concept/codeword
    # label and therefore needs the refusal projection as its readout). They are NOT implemented yet.
    # Failing loudly beats accepting the flag and silently running the forced-choice cell instead --
    # that would produce a plausible-looking number for an experiment that never ran, which is the exact
    # failure class this project has already had to retract twice (prefill-only ablations, silent no-ops).
    if args.prompt_form != "fc" or args.readout != "fc":
        raise SystemExit(
            f"--prompt-form {args.prompt_form} / --readout {args.readout} are NOT IMPLEMENTED yet.\n"
            f"  Currently supported: --prompt-form fc --readout fc (with --destinations selection).\n"
            f"  The decision-point cell needs (a) a bare add_generation_prompt build and (b) a\n"
            f"  refusal-projection readout at a P7-validated layer. Refusing rather than silently\n"
            f"  running the forced-choice cell under a decision-point label.")

    dc.set_seed(args.seed)
    rng = random.Random(args.seed)
    bench = json.load(open(args.bench))
    lm = dc.load_model(args.model, attn_implementation="eager")   # REQUIRED for AttentionKnockout
    # Plan §5 P3 says "Eager attention, asserted". The caller PASSES eager but nothing verified it stuck;
    # under SDPA/flash the softmax@V product is fused, the knockout hook silently no-ops, and the run
    # would report a clean null that means nothing. Same assertion phase4b_pattern.py:92 already uses.
    _impl = getattr(lm.model.config, "_attn_implementation", None)
    if _impl != "eager":
        raise RuntimeError(f"AttentionKnockout needs attn_implementation='eager', got {_impl!r}. "
                           f"SDPA/flash fuse softmax@V and the knockout silently no-ops.")
    print(f"[edgeko] attn_implementation={_impl!r} (asserted)", flush=True)
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

    REQ_MARKER = "Do not reason, just "
    def build_fc(raw_prompt, cw, concept):
        # KEEP the full DS prompt (demos + request-line QUERY codeword) and append the FC question,
        # so the retrieval destination is the actual query codeword (space-prefixed, findable), not
        # the quote-wrapped codeword inside the question. demo = before request; query = request..question.
        fc_raw = raw_prompt + "\n\n" + fc_question(cw, concept)
        templated = dc.apply_template(lm.tokenizer, fc_raw)
        # find_word_occurrences_in_text returns TOKEN indices; convert the request/question char
        # boundaries to token indices via prefix tokenization (occurrences sit clearly on one side).
        req_off = templated.rfind(REQ_MARKER)
        q_off = templated.rfind(FC_PREFIX)
        req_tok = len(lm.tokenizer(templated[:req_off], add_special_tokens=False)["input_ids"])
        q_tok = len(lm.tokenizer(templated[:q_off], add_special_tokens=False)["input_ids"])
        hit = dc.find_word_occurrences_in_text(lm.tokenizer, templated, cw)
        demo_pos = [li for li in hit.last_idx if li < req_tok]
        query_pos = [li for li in hit.last_idx if req_tok <= li < q_tok]  # request-line query codeword
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
            # DESTINATION SELECTION (plan §5 P3). Historically this was the FUSED set
            # query_pos + [seqlen-1], so a query-codeword effect and an answer-position effect could
            # not be told apart. --destinations now selects them, and `destination` is emitted as a row
            # field so the aggregator can group on it. Default reproduces the fused set byte-for-byte.
            _dsets = {"query_cw": list(query_pos), "answer": [seqlen - 1]}
            _want = [d.strip() for d in args.destinations.split(",") if d.strip()]
            _unknown = [d for d in _want if d not in _dsets]
            if _unknown:
                raise SystemExit(f"--destinations: unknown {_unknown}; want a subset of {sorted(_dsets)}")
            qdest = sorted({p for d in _want for p in _dsets[d]})
            dest_tag = ",".join(_want)
            if not qdest:
                continue
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
                        "benign_p_concept": benign_pc, "n_demo_edges": k,
                        "destination": dest_tag, "prompt_form": args.prompt_form,
                        "readout": args.readout, "n_dest_positions": len(qdest)}

            if args.mode == "band":
                # ALL heads across ALL specified layers, query->demo edges only (the retrieval PATHWAY).
                # Single-head KO is negligible (distributed); this tests the pathway's necessity without
                # the global degradation of masking all attention (which made N7-M degenerate).
                ko = pc.AttentionKnockout(lm.model, layers, qdest, demo_pos, heads=None)
                fh.write(json.dumps({**brow_row, "layer": -1, "head": -1, "cell": "edge_KO",
                                     "p_concept": readout(tok, cid, kid, [ko])}) + "\n"); n_rows += 1
                if rand_src:
                    rk = pc.AttentionKnockout(lm.model, layers, qdest, rand_src, heads=None)
                    fh.write(json.dumps({**brow_row, "layer": -1, "head": -1, "cell": "rand_edge",
                                         "p_concept": readout(tok, cid, kid, [rk])}) + "\n"); n_rows += 1
                # broad-degradation control: knock out ALL outgoing query edges (query->everything causal)
                allsrc = list(range(min(qdest)))
                if allsrc:
                    ak = pc.AttentionKnockout(lm.model, layers, qdest, allsrc, heads=None)
                    fh.write(json.dumps({**brow_row, "layer": -1, "head": -1, "cell": "all_query_edges",
                                         "p_concept": readout(tok, cid, kid, [ak])}) + "\n"); n_rows += 1
                continue

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

    if args.mode == "band":
        def cm(cell):
            return {sid: p for (l, h, c), d in cells.items() if c == cell for sid, p in d.items()}
        ko, rk, aq = cm("edge_KO"), cm("rand_edge"), cm("all_query_edges")
        sids = set(ko) & set(rk)
        def ci(vals):
            a = np.array(vals); b = [rng2.choice(a, len(a), replace=True).mean() for _ in range(2000)]
            return [round(float(a.mean()), 4), round(float(np.percentile(b, 2.5)), 4), round(float(np.percentile(b, 97.5)), 4)]
        band = {"n": len(sids), "layers": layers,
                "raw_KO_drop": ci([base[s] - ko[s] for s in sids]) if sids else None,
                "specific_vs_random": ci([rk[s] - ko[s] for s in sids]) if sids else None,
                "mean_base_p": round(float(np.mean([base[s] for s in sids])), 4) if sids else None,
                "all_query_edges_drop": (ci([base[s] - aq[s] for s in set(base) & set(aq)]) if aq else None)}
        json.dump({"cohort": cohort, "mode": "band", "layers": layers, "band": band},
                  open(os.path.join(out_dir, "summary.json"), "w"), indent=1)
        print(f"[edgeKO band L{layers[0]}-{layers[-1]}] n={band['n']} base_p={band['mean_base_p']} "
              f"raw_KO_drop={band['raw_KO_drop']} specific_vs_random={band['specific_vs_random']} "
              f"all_query_edges_drop={band['all_query_edges_drop']}")
        return

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
