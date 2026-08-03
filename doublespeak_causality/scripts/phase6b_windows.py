#!/usr/bin/env python3
"""Phase 6b (MLP-write GRANULARITY WINDOWS): the mandatory sliding + cumulative window sweep
for the L9 MLP write. Reuses phase6_mlp_causal.py machinery VERBATIM — same FC DE_context
readout, same demo-codeword position selection, same pc.ComponentOutSwap(component="mlp_out")
patching (DS mlp_out <- matched BENIGN mlp_out at demo-codeword positions) — but applies the
SAME per-position benign donor JOINTLY across a LAYER-SET window instead of a single layer.

The plan asks: is the L9 MLP write localized to one layer, or is it distributed across a band
that only shows up when several layers are patched together? To answer that we enumerate:
  - SLIDING windows of width 2, 4, 8 over L0..L-1 (every valid start),
  - CUMULATIVE-PREFIX  L0..k   (k = 0..L-1),
  - CUMULATIVE-SUFFIX  Lk..L-1 (k = 0..L-1),
  - CANONICAL early / mid / late (thirds).
The ONLY new logic vs phase6 is (i) building the window layer-set list and (ii) the per-layer
source dict {l: benign_mlp[l] for l in window}. Everything else — capture, swap, readout,
validity gate, paired bootstrap CI, train/test separation — is copied from phase6.

Cells (per WINDOW), necessity side only (sufficiency is phase6's job):
  C1              DS baseline
  C3              necessity: DS mlp_out <- matched BENIGN mlp_out at demo-codeword positions,
                  applied at EVERY layer in the window with the per-layer benign donor
  C1_selfswap     faithfulness: DS mlp_out <- DS OWN mlp_out across the window (EXACT no-op)
  random_control  necessity control: benign mlp_out at count-matched NON-codeword positions
Readout p_concept = P(concept)/(P(concept)+P(codeword)) at the FC answer position.
necessity_specific = random_control - C3  (paired, bootstrap CI, per split, per window).

Usage:
  python scripts/phase6b_windows.py --bench data/bench/bench_curated.json --widths 2,4,8
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


def build_windows(L, widths):
    """Enumerate the plan's mandatory window layer-sets as [(name, [layers...]), ...].

    Names are unique + self-describing so the summary/raw rows never collide:
      slideW{w}_L{a}-{b}  sliding width-w window starting at a (b=a+w-1)
      cumpre_L0-{k}       cumulative prefix L0..k
      cumsuf_L{k}-{L-1}   cumulative suffix Lk..L-1
      early / mid / late  canonical thirds
    """
    wins = []
    for w in widths:
        if w <= 0 or w > L:
            continue
        for start in range(0, L - w + 1):                       # every valid start
            ells = list(range(start, start + w))
            wins.append((f"slideW{w}_L{start}-{start + w - 1}", ells))
    for k in range(0, L):                                       # cumulative prefix L0..k
        wins.append((f"cumpre_L0-{k}", list(range(0, k + 1))))
    for k in range(0, L):                                       # cumulative suffix Lk..L-1
        wins.append((f"cumsuf_L{k}-{L - 1}", list(range(k, L))))
    for name, ells in canonical_windows(L).items():             # canonical thirds
        wins.append((name, ells))
    # de-dup on the exact layer-set (e.g. cumpre_L0-{L-1} == cumsuf_L0-{L-1}); keep first name.
    seen, uniq = set(), []
    for name, ells in wins:
        key = tuple(ells)
        if key in seen:
            continue
        seen.add(key)
        uniq.append((name, ells))
    return uniq


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bench", required=True)
    ap.add_argument("--model", default=dc.PRIMARY_MODEL)
    ap.add_argument("--out-root", default=os.path.join(DC, "outputs"))
    ap.add_argument("--splits", default="dev,heldout")
    ap.add_argument("--widths", default="2,4,8", help="sliding-window widths (comma list)")
    ap.add_argument("--component", default="mlp_out", choices=["mlp_out", "attn_out"],
                    help="which sub-block OUTPUT to patch across the window (write=mlp_out)")
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
    widths = [int(x) for x in args.widths.split(",") if x.strip()]

    splits = [s.strip() for s in args.splits.split(",") if s.strip()]
    rows = [r for r in bench["semantic"] if r["split"] in splits]
    by_key = {(r["condition"], r["split"], r["sid"]): r for r in rows}
    ds_rows = defaultdict(list)
    for r in rows:
        if r["condition"] == "DOUBLESPEAK":
            ds_rows[r["split"]].append(r)

    windows = build_windows(L, widths)

    ts = time.strftime("%Y%m%d_%H%M%S")
    uniq = os.environ.get("SLURM_JOB_ID") or str(os.getpid())
    out_dir = os.path.join(args.out_root, f"phase6b_windows_{cohort}_{args.component}_{ts}_{uniq}")
    os.makedirs(out_dir, exist_ok=True)
    fh = open(os.path.join(out_dir, "raw.jsonl"), "w")
    n_rows = [0]
    print(f"[win] cohort={cohort} L={L} comp={args.component} widths={widths} "
          f"n_windows={len(windows)} -> {out_dir}")

    def build_fc(raw_prompt, codeword, concept):
        """DEMO-block codeword positions only (the write site), with the token-index-vs-char
        offset FIX copied from phase6: hit.spans are TOKEN indices, so the question boundary
        must also be a TOKEN index (rfind gives a CHAR offset)."""
        fc_raw = demo_block_of(raw_prompt) + "\n\n" + fc_question(codeword, concept)
        templated = dc.apply_template(lm.tokenizer, fc_raw)
        q_char = templated.rfind(FC_PREFIX)
        q_tok = len(lm.tokenizer(templated[:q_char], add_special_tokens=False)["input_ids"])
        hit = dc.find_word_occurrences_in_text(lm.tokenizer, templated, codeword)
        demo_pos = [li for span, li in zip(hit.spans, hit.last_idx) if span[0] < q_tok]
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
    def capture_comp(templated, positions):
        tok = lm.tokenizer(templated, return_tensors="pt", add_special_tokens=False).to(dev)
        with pc.ComponentCapture(lm, [args.component], positions) as cap:
            lm.model(**tok, return_dict=True)
        return cap.stacked()[args.component]            # [L, n_pos, H]

    def swap(positions, src_by_layer):
        return pc.ComponentOutSwap(lm.model, positions, src_by_layer, component=args.component)

    def emit(base, window, cell, n_sw, res):
        pnorm, pc_, pk_ = res
        fh.write(json.dumps({**base, "window": window, "cell": cell, "n_pos_swapped": n_sw,
                             "p_concept": pnorm, "raw_concept": pc_, "raw_codeword": pk_}) + "\n")
        n_rows[0] += 1

    skips = defaultdict(int)
    for split in splits:
        cand = sorted(ds_rows.get(split, []), key=lambda r: r["sid"])
        if args.n_prompts:
            cand = cand[: args.n_prompts]
        for r in cand:
            concept, codeword = r["target_concept"], r["codeword"]
            cid, kid = _single_id(lm.tokenizer, concept), _single_id(lm.tokenizer, codeword)

            ds_tmpl, ds_tok, ds_demo_cw = build_fc(r["prompt"], codeword, concept)
            if not ds_demo_cw:
                skips[f"{split}:no_ds_demo_pos"] += 1
                continue
            brow = by_key.get(("BENIGN_REMAP", split, r["sid"]))
            if brow is None:
                skips[f"{split}:no_benign_row"] += 1
                continue
            b_tmpl, b_tok, b_demo_cw = build_fc(brow["prompt"], codeword, concept)
            if not b_demo_cw:
                skips[f"{split}:no_benign_demo_pos"] += 1
                continue
            benign_pconc = readout(b_tok, cid, kid, [])[0]
            base = {"sid": r["sid"], "split": split, "cohort": cohort, "concept": concept,
                    "codeword": codeword, "benign_p_concept": benign_pconc}

            if cid == kid:                       # degenerate FC readout (shared first subtoken)
                skips[f"{split}:cid_eq_kid"] += 1
                continue
            if len(ds_demo_cw) != len(b_demo_cw):
                skips[f"{split}:demo_cw_count_mismatch"] += 1
            m = min(len(ds_demo_cw), len(b_demo_cw))
            ds_cwset, b_cwset = set(ds_demo_cw), set(b_demo_cw)
            # pool = in-demo-text non-codeword positions (FIRST..LAST codeword span), excluding
            # BOS/system/template tokens before the first occurrence (phase6 audit finding 8).
            ds_pool = [p for p in range(min(ds_demo_cw), max(ds_demo_cw)) if p not in ds_cwset]
            b_pool = [p for p in range(min(b_demo_cw), max(b_demo_cw)) if p not in b_cwset]
            rlen = min(m, len(ds_pool), len(b_pool))
            ds_rand = sorted(rng.sample(ds_pool, rlen)) if rlen else []
            b_rand = sorted(rng.sample(b_pool, rlen)) if rlen else []

            ds_swap_pos = ds_demo_cw[-m:] if m else []
            ds_cap = capture_comp(ds_tmpl, ds_demo_cw + ds_rand)
            b_cap = capture_comp(b_tmpl, b_demo_cw + b_rand)
            ds_out_demo, ds_out_rand = ds_cap[:, :len(ds_demo_cw), :], ds_cap[:, len(ds_demo_cw):, :]
            b_out_demo, b_out_rand = b_cap[:, :len(b_demo_cw), :], b_cap[:, len(b_demo_cw):, :]

            c1 = readout(ds_tok, cid, kid, [])
            for wname, ells in windows:
                # ---- NECESSITY (DS receiver): DS mlp_out <- BENIGN, jointly across window ----
                emit(base, wname, "C1", 0, c1)
                if m:
                    # SAME per-position benign donor applied at EVERY layer in the window.
                    src3 = {l: b_out_demo[l, -m:, :] for l in ells}
                    emit(base, wname, "C3", m,
                         readout(ds_tok, cid, kid, [swap(ds_swap_pos, src3)]))
                # C1_selfswap: DS OWN mlp_out across the window -> EXACT no-op (must == C1).
                emit(base, wname, "C1_selfswap", len(ds_demo_cw),
                     readout(ds_tok, cid, kid,
                             [swap(ds_demo_cw, {l: ds_out_demo[l] for l in ells})]))
                if ds_rand:
                    emit(base, wname, "random_control", len(ds_rand),
                         readout(ds_tok, cid, kid,
                                 [swap(ds_rand, {l: b_out_rand[l] for l in ells})]))
    fh.close()

    if skips:
        print(f"[win] skipped examples by reason: {dict(skips)}")
    all_rows = [json.loads(x) for x in open(os.path.join(out_dir, "raw.jsonl"))]
    rng2 = np.random.default_rng(0)
    def bootci(vals):
        if not vals:
            return None
        a = np.array(vals)
        boot = [rng2.choice(a, len(a), replace=True).mean() for _ in range(2000)]
        return [round(float(a.mean()), 4), round(float(np.percentile(boot, 2.5)), 4),
                round(float(np.percentile(boot, 97.5)), 4)]

    # PLAN train/test separation: aggregate dev (train) and heldout (test) SEPARATELY, never
    # pooled. Key on sid within a split (F2).
    def summarize(split):
        srows = [r for r in all_rows if r["split"] == split]
        def cellmap(cell, w):
            return {r["sid"]: r["p_concept"] for r in srows if r["cell"] == cell and r["window"] == w}
        valid = {r["sid"] for r in srows if r["cell"] == "C1"
                 and r.get("benign_p_concept") is not None and r["p_concept"] > r["benign_p_concept"]}
        out = {}
        for w in sorted({r["window"] for r in srows}):
            c1, c3 = cellmap("C1", w), cellmap("C3", w)
            rc, ss = cellmap("random_control", w), cellmap("C1_selfswap", w)
            nec = [s for s in valid if s in c1 and s in c3 and s in rc]
            out[w] = {
                "n_valid": len(nec),
                "mean_C1_p_concept": (round(float(np.mean([c1[s] for s in nec])), 4) if nec else None),
                "mean_C3_p_concept": (round(float(np.mean([c3[s] for s in nec])), 4) if nec else None),
                "necessity_specific_ci": bootci([rc[s] - c3[s] for s in nec]),
                "nec_selfswap_max_dev": (round(float(np.max([abs(c1[s] - ss[s]) for s in nec if s in ss])), 5) if nec else None),
            }
        return {"n_valid_examples": len(valid), "windows": out}

    by_split = {sp: summarize(sp) for sp in splits}
    json.dump({"cohort": cohort, "model": args.model, "n_rows": len(all_rows),
               "component": args.component, "widths": widths, "n_windows": len(windows),
               "skips": dict(skips), "by_split": by_split},
              open(os.path.join(out_dir, "summary.json"), "w"), indent=1)
    print(f"[win] {len(all_rows)} rows -> {out_dir}")
    for sp in splits:
        wns = by_split[sp]["windows"]
        # top windows by necessity_specific mean (rand - C3), largest first
        ranked = sorted(((w, s) for w, s in wns.items() if s["necessity_specific_ci"]),
                        key=lambda kv: -kv[1]["necessity_specific_ci"][0])[:10]
        print(f"  == split={sp} (n_valid={by_split[sp]['n_valid_examples']}) top-10 necessity ==")
        for w, s in ranked:
            print(f"    {w}: n={s['n_valid']} C1={s['mean_C1_p_concept']} C3={s['mean_C3_p_concept']} "
                  f"NEC_specific(rand-C3)={s['necessity_specific_ci']} selfdev={s['nec_selfswap_max_dev']}")


if __name__ == "__main__":
    main()
