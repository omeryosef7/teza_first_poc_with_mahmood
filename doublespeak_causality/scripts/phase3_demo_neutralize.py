#!/usr/bin/env python3
"""Phase 3/4 core (multi-concept): does NEUTRALIZING the demonstration-codeword activations
reduce the harmful reading? Necessity test with the WORKING forced-choice readout.

Unlike 44_kv_mediation.py (single global pair), this resolves concept/codeword PER ROW, so it
runs on the multi-concept ClearHarm/curated cohorts. Reuses the exact 44 primitives:
  pc.resolve_positions, pc.DemoStateSwap, pc.ComponentCapture, dc.capture_target_reps,
  07_patchscope_readout.PatchscopeDecoder (gated positive control per example).

Cells (receiver ALWAYS the DOUBLESPEAK prompt), per WINDOW and per LAYER:
  C1              baseline DS forward
  C3_demoKV       neutralize demo-codeword resid_pre <- matched Neutral (the necessity test)
  C1_selfswap     DemoStateSwap with the receiver's OWN demo resid_pre (faithfulness: == C1)
  random_control  neutralize count-matched NON-codeword demo positions (concept must NOT move)
Readouts (scalar): p_concept/p_codeword next-token mass; ps_concept_gated (patchscope at the
positive-control argmax layer, per example). ReRead_test = mean(C1 - C3_demoKV).

Usage (smoke first):
  python scripts/phase3_demo_neutralize.py --bench data/bench/bench_curated.json --n-prompts 2 --windows mid
  python scripts/phase3_demo_neutralize.py --bench data/bench/bench_clearharm.json --granularity layer
"""
from __future__ import annotations
import argparse, importlib.util, json, os, random, sys, time
from collections import defaultdict
from contextlib import ExitStack
import numpy as np
import torch

HERE = os.path.dirname(os.path.abspath(__file__))
DC = os.path.dirname(HERE)
sys.path.insert(0, DC)
import ds_common as dc
import pair_common as pc


def _load_module(name, filename):
    spec = importlib.util.spec_from_file_location(name, os.path.join(DC, filename))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _single_id(tok, word):
    ids = tok.encode(" " + word, add_special_tokens=False)
    return ids[0]


def patchscope_gate(scores, thresh=0.1):
    if not scores:
        return 0, 0.0, False
    best = int(max(range(len(scores)), key=lambda l: scores[l]))
    return best, float(scores[best]), bool(scores[best] > thresh)


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
    R = L - 4
    dev = lm.model.device
    dec = _load_module("ps07", "07_patchscope_readout.py").PatchscopeDecoder(lm)
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
    out_dir = os.path.join(args.out_root, f"phase3_demoKO_{cohort}_{args.granularity}_{ts}_{uniq}")
    os.makedirs(out_dir, exist_ok=True)
    fh = open(os.path.join(out_dir, "raw.jsonl"), "w")
    n_rows = [0]
    print(f"[demoKO] cohort={cohort} L={L} R={R} gran={args.granularity} "
          f"windows={[w for w,_ in windows][:4]}{'...' if len(windows)>4 else ''} -> {out_dir}")

    @torch.no_grad()
    def eval_cell(ds_tok, ds_query, contexts, cid, kid, gate_layer):
        with ExitStack() as stack:
            for c in contexts:
                stack.enter_context(c)
            out = lm.model(**ds_tok, output_hidden_states=True, return_dict=True)
        probs = torch.softmax(out.logits[0, -1, :].float(), dim=-1)
        p_conc, p_code = float(probs[cid]), float(probs[kid])
        rep_g = out.hidden_states[gate_layer][0, ds_query, :]
        ps_hg, ps_cg = dec.decode(rep_g.to(dev), R, cid, kid)
        return p_conc, p_code, float(ps_hg), float(ps_cg)

    @torch.no_grad()
    def capture_pre(templated, positions):
        tok = lm.tokenizer(templated, return_tensors="pt", add_special_tokens=False).to(dev)
        with pc.ComponentCapture(lm, ["resid_pre"], positions) as cap:
            lm.model(**tok, return_dict=True)
        return cap.stacked()["resid_pre"]           # [L, n_pos, H]

    def emit(base, window, cell, n_sw, res):
        p_conc, p_code, ps_hg, ps_cg = res
        fh.write(json.dumps({**base, "window": window, "cell": cell, "n_demo_swapped": n_sw,
                             "p_concept": p_conc, "p_codeword": p_code,
                             "ps_concept_gated": ps_hg, "ps_codeword_gated": ps_cg}) + "\n")
        n_rows[0] += 1

    for split in splits:
        cand = sorted(ds_rows.get(split, []), key=lambda r: r["sid"])
        if args.n_prompts:
            cand = cand[: args.n_prompts]
        for r in cand:
            concept, codeword = r["target_concept"], r["codeword"]
            cid, kid = _single_id(lm.tokenizer, concept), _single_id(lm.tokenizer, codeword)
            templated = dc.apply_template(lm.tokenizer, r["prompt"])
            pos = pc.resolve_positions(lm, templated, codeword)
            ds_query = pos.codeword_last
            ds_demo_cw = list(pos.codeword_all[:-1])          # demo codeword occurrences
            cwset = set(pos.codeword_all)
            ds_tok = lm.tokenizer(templated, return_tensors="pt", add_special_tokens=False).to(dev)

            # per-example positive control: decode the matched DIRECT-concept rep, gate
            drow = by_key.get(("DIRECT_CONCEPT", split, r["sid"]))
            gate_layer, pos_ok = R + 1, False
            if drow is not None:
                try:
                    dtmpl = dc.apply_template(lm.tokenizer, drow["prompt"])
                    reps_all = dc.capture_target_reps(lm, dtmpl, drow["probe_word"])["reps"]["codeword_last"]
                    scores = [dec.decode(reps_all[l].to(dev), R, cid, kid)[0]
                              for l in range(reps_all.shape[0])]
                    gate_layer, _, pos_ok = patchscope_gate(scores)
                except Exception as e:
                    print(f"  [demoKO] pos-ctrl fail {r['sid']}: {e}")

            base = {"sid": r["sid"], "split": split, "cohort": cohort, "concept": concept,
                    "codeword": codeword, "positive_control_ok": pos_ok, "gate_layer": gate_layer}

            # matched BENIGN prompt (same codeword used in BENIGN demo sentences — the correct
            # non-harmful-binding source; NEUTRAL has no demos so it carries no demo-codeword K/V).
            # Capture its resid_pre at demo codewords + count-matched random non-cw positions.
            nrow = by_key.get(("BENIGN_REMAP", split, r["sid"]))
            neu_pre_demo = neu_pre_rand = None
            ds_rand = []
            if nrow is not None and ds_demo_cw:
                ntmpl = dc.apply_template(lm.tokenizer, nrow["prompt"])
                npos = pc.resolve_positions(lm, ntmpl, codeword)
                neu_demo_cw = list(npos.codeword_all[:-1])
                m = min(len(ds_demo_cw), len(neu_demo_cw))
                ds_pool = [p for p in range(ds_query) if p not in cwset]
                rlen = min(m, len(ds_pool))
                ds_rand = sorted(rng.sample(ds_pool, rlen)) if rlen else []
                neu_rand = sorted(rng.sample(range(npos.codeword_last), rlen)) if rlen else []
                cap_pos = neu_demo_cw[:m] + neu_rand
                ncap = capture_pre(ntmpl, cap_pos) if cap_pos else None
                if ncap is not None:
                    neu_pre_demo = ncap[:, :m, :]
                    neu_pre_rand = ncap[:, m:m + rlen, :]
                ds_swap_pos = ds_demo_cw[-m:] if m else []
            else:
                m, ds_swap_pos = 0, []

            ds_pre_demo = capture_pre(templated, ds_demo_cw) if ds_demo_cw else None
            c1 = eval_cell(ds_tok, ds_query, [], cid, kid, gate_layer)

            for wname, ells in windows:
                emit(base, wname, "C1", 0, c1)
                if m and neu_pre_demo is not None:
                    src3 = {l: neu_pre_demo[l, -m:, :] for l in ells}
                    emit(base, wname, "C3_demoKV", m,
                         eval_cell(ds_tok, ds_query, [pc.DemoStateSwap(lm.model, ds_swap_pos, src3)],
                                   cid, kid, gate_layer))
                if ds_pre_demo is not None:
                    srcs = {l: ds_pre_demo[l] for l in ells}
                    emit(base, wname, "C1_selfswap", len(ds_demo_cw),
                         eval_cell(ds_tok, ds_query, [pc.DemoStateSwap(lm.model, ds_demo_cw, srcs)],
                                   cid, kid, gate_layer))
                if ds_rand and neu_pre_rand is not None:
                    srcr = {l: neu_pre_rand[l] for l in ells}
                    emit(base, wname, "random_control", len(ds_rand),
                         eval_cell(ds_tok, ds_query, [pc.DemoStateSwap(lm.model, ds_rand, srcr)],
                                   cid, kid, gate_layer))
    fh.close()

    # aggregate ReRead_test = mean(C1 - C3_demoKV) per window (gated readout, positive-control-ok only)
    all_rows = [json.loads(x) for x in open(os.path.join(out_dir, "raw.jsonl"))]
    def by(cell, w, metric="ps_concept_gated"):
        return {r["sid"]: r[metric] for r in all_rows
                if r["cell"] == cell and r["window"] == w and r["positive_control_ok"]}
    windows_seen = sorted({r["window"] for r in all_rows})
    summ = {}
    for w in windows_seen:
        c1 = by("C1", w); c3 = by("C3_demoKV", w); rc = by("random_control", w); ss = by("C1_selfswap", w)
        common = set(c1) & set(c3)
        rr = float(np.mean([c1[s] - c3[s] for s in common])) if common else None
        rcv = ([c1[s] - rc[s] for s in set(c1) & set(rc)] or [None])
        ssv = ([abs(c1[s] - ss[s]) for s in set(c1) & set(ss)] or [None])
        summ[w] = {"n": len(common), "ReRead_test_mean": rr,
                   "random_control_mean": (float(np.mean(rcv)) if rcv[0] is not None else None),
                   "selfswap_max_abs_dev": (float(np.max(ssv)) if ssv[0] is not None else None)}
    json.dump({"cohort": cohort, "model": args.model, "n_rows": len(all_rows),
               "granularity": args.granularity, "windows": summ}, open(os.path.join(out_dir, "summary.json"), "w"), indent=1)
    print(f"[demoKO] {len(all_rows)} rows -> {out_dir}")
    for w, s in summ.items():
        print(f"  {w}: n={s['n']} ReRead(C1-C3)={s['ReRead_test_mean']} "
              f"random={s['random_control_mean']} selfswap_dev={s['selfswap_max_abs_dev']}")


if __name__ == "__main__":
    main()
