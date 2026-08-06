#!/usr/bin/env python3
"""Phase 5 (all-head activation patching): per-(layer,head) z-patch NECESSITY at the answer
position, FC DE_context readout, dev/heldout separate, Holm across the 32x32 head family.

Which attention HEADS carry the Doublespeak reading? For every (layer, head), replace the DS
per-head attention output z[head] at the FC ANSWER position (last token) with the matched
BENIGN z[head] (necessity: does removing that head's contribution drop the concept reading?).
Patching at the last position measures the head's TOTAL effect on the final logit via the
remaining layers at the answer position (no other position attends to the last token; this is
a total/carry effect, NOT a strict direct-path contribution — Phase 7 separates direct vs mediated).
Authoritative significance is recomputed by scripts/phase5_analyze.py (Wilcoxon + Holm).

Reuses pc.ZHeadCapture (per-head z, o_proj input) + pc.ZHeadPatch (replace one head's z at a
position) + the phase6 FC readout. Controls: self-swap (DS's own z -> exact no-op, sampled),
norm-matched random vector (must be ~0). Necessity(L,h) = C1 - patched_benign (paired, CI,
Holm-corrected across all layer x head cells per split).

Usage:
  python scripts/phase5_head_zpatch.py --bench data/bench/bench_curated.json --layers 0-31 --n-prompts 2
"""
from __future__ import annotations
import argparse, json, os, sys, time
from collections import defaultdict
import numpy as np
import torch

HERE = os.path.dirname(os.path.abspath(__file__))
DC = os.path.dirname(HERE)
sys.path.insert(0, DC)
import ds_common as dc
import pair_common as pc
import importlib.util as _ilu
_pp = _ilu.spec_from_file_location("pp50", os.path.join(DC, "50_path_patching.py"))
_pp50 = _ilu.module_from_spec(_pp); _pp.loader.exec_module(_pp50)


def _single_id(tok, word):
    return tok.encode(" " + word, add_special_tokens=False)[0]


FC_PREFIX = "Choose one label only and answer with just that label."
def fc_question(codeword, concept):
    return (f'{FC_PREFIX} In the text above, does the word "{codeword}" '
            f'refer to "{concept}" or to "{codeword}"?')


def demo_block_of(ds_prompt, marker="\n\nDo not reason, just "):
    return ds_prompt.rsplit(marker, 1)[0] if marker in ds_prompt else ds_prompt


def parse_layers(spec, L):
    if "-" in spec:
        a, b = spec.split("-")
        return list(range(int(a), int(b) + 1))
    return [int(x) for x in spec.split(",") if x.strip() != ""] if spec else list(range(L))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bench", required=True)
    ap.add_argument("--model", default=dc.PRIMARY_MODEL)
    ap.add_argument("--out-root", default=os.path.join(DC, "outputs"))
    ap.add_argument("--splits", default="dev,heldout")
    ap.add_argument("--layers", default="0-31", help="dash-range or comma list (dodge --export comma)")
    ap.add_argument("--positions", default="answer",
                    choices=["answer", "demo", "query", "all"],
                    help="WHERE to patch head z (plan P4b-1). answer = FC last token (historical TOTAL "
                         "effect). demo/query/all = the codeword occurrences where the L8-11 retrieval "
                         "heads ACT, patched with occurrence-order trailing-aligned BENIGN donors via "
                         "50_path_patching.ZHeadPatchMulti. answer reproduces the old runs exactly.")
    ap.add_argument("--n-prompts", type=int, default=0)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    dc.set_seed(args.seed)
    rng = np.random.default_rng(args.seed)
    bench = json.load(open(args.bench))
    lm = dc.load_model(args.model)
    L = lm.num_layers
    dev = lm.model.device
    cohort = bench.get("_meta", {}).get("cohort", "?")
    layers = [l for l in parse_layers(args.layers, L) if 0 <= l < L]
    n_heads, head_dim = pc._attn_head_dims(lm.model)

    splits = [s.strip() for s in args.splits.split(",") if s.strip()]
    rows = [r for r in bench["semantic"] if r["split"] in splits]
    by_key = {(r["condition"], r["split"], r["sid"]): r for r in rows}
    ds_rows = defaultdict(list)
    for r in rows:
        if r["condition"] == "DOUBLESPEAK":
            ds_rows[r["split"]].append(r)

    ts = time.strftime("%Y%m%d_%H%M%S")
    uniq = os.environ.get("SLURM_JOB_ID") or str(os.getpid())
    out_dir = os.path.join(args.out_root, f"phase5_headz_{cohort}_{args.positions}_{ts}_{uniq}")
    os.makedirs(out_dir, exist_ok=True)
    fh = open(os.path.join(out_dir, "raw.jsonl"), "w")
    print(f"[headz] cohort={cohort} L={L} heads={n_heads} layers={layers[0]}-{layers[-1]} -> {out_dir}")

    def build_fc(raw_prompt, codeword, concept, want_templated=False):
        fc_raw = demo_block_of(raw_prompt) + "\n\n" + fc_question(codeword, concept)
        templated = dc.apply_template(lm.tokenizer, fc_raw)
        tok = lm.tokenizer(templated, return_tensors="pt", add_special_tokens=False).to(dev)
        return (tok, templated) if want_templated else tok

    def codeword_positions(templated, codeword):
        """demo vs query codeword token positions -- the same resolver as phase6_mlp_causal.py:127-131,
        which fixed the char-offset-vs-token-index bug. Returns (demo_pos, query_pos), trailing-ordered."""
        q_char = templated.rfind(FC_PREFIX)
        q_tok = len(lm.tokenizer(templated[:q_char], add_special_tokens=False)["input_ids"])
        hit = dc.find_word_occurrences_in_text(lm.tokenizer, templated, codeword)
        demo_pos = [li for span, li in zip(hit.spans, hit.last_idx) if span[0] < q_tok]
        query_pos = [li for span, li in zip(hit.spans, hit.last_idx) if span[0] >= q_tok]
        return demo_pos, query_pos

    def capture_z_at(tok, positions):
        """{L: {pos: Tensor[n_heads, head_dim]}} of per-head z at each requested position."""
        with pc.ZHeadCapture(lm.model, layers) as cap:
            lm.model(**tok, return_dict=True)
        return {l: {pp: cap.acts[l][0, pp].view(n_heads, head_dim).float().cpu() for pp in positions}
                for l in layers}

    @torch.no_grad()
    def readout(tok, cid, kid, ctx=()):
        from contextlib import ExitStack
        with ExitStack() as st:
            for c in ctx:
                st.enter_context(c)
            out = lm.model(**tok, return_dict=True)
        p = torch.softmax(out.logits[0, -1, :].float(), dim=-1)
        pc_, pk_ = float(p[cid]), float(p[kid])
        return pc_ / (pc_ + pk_ + 1e-12)

    @torch.no_grad()
    def capture_z_last(tok):
        """{L: Tensor[n_heads, head_dim]} of per-head z at the LAST position."""
        last = tok["input_ids"].shape[1] - 1
        with pc.ZHeadCapture(lm.model, layers) as cap:
            lm.model(**tok, return_dict=True)
        return {l: cap.acts[l][0, last].view(n_heads, head_dim).float().cpu() for l in layers}, last

    n_written = 0
    skips = defaultdict(int)
    for split in splits:
        cand = sorted(ds_rows.get(split, []), key=lambda r: r["sid"])
        if args.n_prompts:
            cand = cand[: args.n_prompts]
        for r in cand:
            concept, codeword = r["target_concept"], r["codeword"]
            cid, kid = _single_id(lm.tokenizer, concept), _single_id(lm.tokenizer, codeword)
            brow = by_key.get(("BENIGN_REMAP", split, r["sid"]))
            if brow is None:
                skips[f"{split}:no_benign"] += 1
                continue
            ds_tok, ds_templ = build_fc(r["prompt"], codeword, concept, want_templated=True)
            b_tok, b_templ = build_fc(brow["prompt"], codeword, concept, want_templated=True)
            benign_p = readout(b_tok, cid, kid)
            c1 = readout(ds_tok, cid, kid)
            base = {"sid": r["sid"], "split": split, "cohort": cohort, "concept": concept,
                    "codeword": codeword, "benign_p_concept": benign_p, "C1": c1,
                    "positions": args.positions}

            if args.positions == "answer":
                # HISTORICAL PATH -- unchanged. Single last-token donor via pc.ZHeadPatch.
                z_ds, ds_last = capture_z_last(ds_tok)
                z_b, _ = capture_z_last(b_tok)
                patch_pos = [ds_last]
                def _donor_ctx(l, h):
                    return pc.ZHeadPatch(lm.model, l, h, [ds_last], z_b[l][h].to(dev))
                self_layer_z = z_ds
            else:
                # P4b-1 PATH: patch at the codeword occurrences where the retrieval heads act.
                ds_demo, ds_query = codeword_positions(ds_templ, codeword)
                b_demo, b_query = codeword_positions(b_templ, codeword)
                sel = {"demo": (ds_demo, b_demo), "query": (ds_query, b_query),
                       "all": (ds_demo + ds_query, b_demo + b_query)}[args.positions]
                ds_pos, b_pos = sel
                # occurrence-order TRAILING alignment: DS and benign can have different occurrence
                # counts; align from the end and use the last k of each (plan P4b-1).
                k = min(len(ds_pos), len(b_pos))
                if k == 0:
                    skips[f"{split}:no_{args.positions}_pos"] += 1
                    continue
                ds_pos, b_pos = ds_pos[-k:], b_pos[-k:]
                base["n_patch_pos"] = k
                z_ds = capture_z_at(ds_tok, ds_pos)
                z_b = capture_z_at(b_tok, b_pos)
                patch_pos = ds_pos
                def _donor_ctx(l, h):
                    vecs = [z_b[l][bp][h].to(dev) for bp in b_pos]   # benign donor per aligned position
                    return _pp50.ZHeadPatchMulti(lm.model, l, h, ds_pos, vecs)
                self_layer_z = None   # self-swap uses DS's OWN z at the same positions (built below)

            for l in layers:
                for h in range(n_heads):
                    p_patched = readout(ds_tok, cid, kid, [_donor_ctx(l, h)])
                    fh.write(json.dumps({**base, "layer": l, "head": h, "cell": "benign",
                                         "p_concept": p_patched}) + "\n")
                    n_written += 1
            # controls at one probe (layer, head) = (layers[len//2], 0): self-swap + norm-random.
            # self-swap MUST be an exact no-op: patch DS's own z at the SAME positions being tested.
            lp = layers[len(layers) // 2]
            if args.positions == "answer":
                self_vecs = [z_ds[lp][0].to(dev)]
                p_self = readout(ds_tok, cid, kid, [pc.ZHeadPatch(lm.model, lp, 0, patch_pos, self_vecs[0])])
                ref_norm = self_vecs[0].norm().item()
            else:
                self_vecs = [z_ds[lp][pp][0].to(dev) for pp in patch_pos]
                p_self = readout(ds_tok, cid, kid,
                                 [_pp50.ZHeadPatchMulti(lm.model, lp, 0, patch_pos, self_vecs)])
                ref_norm = self_vecs[0].norm().item()
            rand_v = torch.tensor(rng.standard_normal(head_dim), dtype=torch.float32)
            rand_v = rand_v / (rand_v.norm() + 1e-8) * ref_norm
            if args.positions == "answer":
                p_rand = readout(ds_tok, cid, kid, [pc.ZHeadPatch(lm.model, lp, 0, patch_pos, rand_v.to(dev))])
            else:
                p_rand = readout(ds_tok, cid, kid,
                                 [_pp50.ZHeadPatchMulti(lm.model, lp, 0, patch_pos,
                                                        [rand_v.to(dev)] * len(patch_pos))])
            fh.write(json.dumps({**base, "layer": lp, "head": 0, "cell": "selfswap", "p_concept": p_self}) + "\n")
            fh.write(json.dumps({**base, "layer": lp, "head": 0, "cell": "normrand", "p_concept": p_rand}) + "\n")
            n_written += 2
    fh.close()

    # ---- per-split + Holm across (layer,head) family ----
    all_rows = [json.loads(x) for x in open(os.path.join(out_dir, "raw.jsonl"))]
    def perm_p(vals):
        # Wilcoxon signed-rank (robust to right-skew, deterministic, resolves below the 1024-cell
        # Holm threshold). A sign-flip permutation at feasible nperm returns p=0 artifacts here;
        # a t-test is over-conservative. Matches scripts/phase5_analyze.py (authoritative).
        from scipy import stats
        a = np.array(vals, float)
        if a.size < 6 or np.allclose(a, 0):
            return 1.0
        try:
            return float(stats.wilcoxon(a).pvalue)
        except ValueError:
            return 1.0
    def holm(pv, alpha=0.05):
        order = sorted(pv, key=lambda k: pv[k]); m = len(order); rej = {}; ok = True
        for i, k in enumerate(order):
            if ok and pv[k] <= alpha / (m - i):
                rej[k] = True
            else:
                ok = False; rej[k] = False
        return rej
    summ = {}
    for split in splits:
        sr = [r for r in all_rows if r["split"] == split]
        valid = {r["sid"] for r in sr if r["cell"] == "benign" and r["benign_p_concept"] is not None
                 and r["C1"] > r["benign_p_concept"]}
        # necessity per (l,h) = C1 - patched_benign, paired over valid examples
        pv, mean = {}, {}
        selfdev = 0.0
        for r in sr:
            if r["cell"] == "selfswap":
                selfdev = max(selfdev, abs(r["C1"] - r["p_concept"]))
        for l in layers:
            for h in range(n_heads):
                diffs = [r["C1"] - r["p_concept"] for r in sr
                         if r["cell"] == "benign" and r["layer"] == l and r["head"] == h and r["sid"] in valid]
                if diffs:
                    pv[(l, h)] = perm_p(diffs); mean[(l, h)] = float(np.mean(diffs))
        rej = holm(pv)
        holm_heads = sorted([(f"L{l}H{h}", round(mean[(l, h)], 4), round(pv[(l, h)], 5))
                             for (l, h) in pv if rej.get((l, h)) and mean[(l, h)] > 0],
                            key=lambda x: -x[1])
        top = sorted([((l, h), mean[(l, h)]) for (l, h) in mean], key=lambda x: -x[1])[:10]
        summ[split] = {"n_valid": len(valid), "selfswap_max_dev": round(selfdev, 6),
                       "n_holm_sig_heads": len(holm_heads), "holm_sig_heads": holm_heads[:25],
                       "top10_by_mean": [(f"L{l}H{h}", round(m, 4)) for (l, h), m in top]}
    json.dump({"cohort": cohort, "model": args.model, "n_rows": n_written, "n_heads": n_heads,
               "layers": layers, "skips": dict(skips), "by_split": summ},
              open(os.path.join(out_dir, "summary.json"), "w"), indent=1)
    print(f"[headz] {n_written} rows -> {out_dir}")
    for split, s in summ.items():
        print(f"  [{split}] n_valid={s['n_valid']} selfswap_dev={s['selfswap_max_dev']} "
              f"Holm-sig heads={s['n_holm_sig_heads']}: {s['holm_sig_heads'][:8]}")
        print(f"     top10 by necessity: {s['top10_by_mean']}")


if __name__ == "__main__":
    main()
