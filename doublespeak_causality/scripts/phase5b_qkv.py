#!/usr/bin/env python3
"""Phase 5b (per-head Q/K/V decomposition): for each validated CARRY head, decompose WHERE its
computation matters by patching the per-head slice of its q_proj / k_proj / v_proj OUTPUT,
DS<-BENIGN, at the answer position, and reading the FC DE_context p_concept.

Phase 5 established WHICH heads carry the Doublespeak reading (z-patch necessity on the o_proj
INPUT = the head's OUTPUT z). This asks, for each such head, WHICH PART of its computation is
load-bearing:
  Q (q_proj output slice)  -> where the head attends FROM   (its query)
  K (k_proj output slice)  -> how the attended keys are keyed
  V (v_proj output slice)  -> what value the head reads off the attended positions
Replacing DS's per-head Q/K/V with the matched BENIGN counterpart at the ANSWER position, and
watching p_concept drop, tells us which of the three the carry head's concept reading depends on.

GQA (Llama-3.1-8B: 32 attention heads, 8 KV heads, head_dim 128): q_proj emits
num_attention_heads*head_dim; k_proj/v_proj emit num_key_value_heads*head_dim. A QUERY head h
reads the KV head  h // (num_attention_heads // num_key_value_heads). So the Q cell patches query
slice h; the K/V cells patch KV slice h//group. This mapping is handled explicitly.

Two new LOCAL primitives (mirrors of pc.ZHeadCapture / pc.ZHeadPatch, but on the q/k/v_proj
OUTPUTS via forward hooks rather than the o_proj INPUT via a pre-hook):
  QKVHeadCapture  — capture per-head q/k/v_proj output rows at the last position.
  QKVHeadPatch    — replace one head's q/k/v_proj output slice at chosen positions.

Cells per (layer, query-head h):
  q / k / v            necessity: DS <proj> head-slice <- matched BENIGN slice at answer pos
  q_self/k_self/v_self self-swap: DS <proj> slice <- DS's OWN slice (MUST be an exact no-op)
  q_rand/k_rand/v_rand random-head control: BENIGN slice from a RANDOM other head (specificity)
Readout p_concept = P(concept)/(P(concept)+P(codeword)) at the FC answer position.
necessity(cell) = C1 - patched   (paired over valid examples, bootstrap CI, per split).
necessity_specific = patched_rand - patched   (paired: head-identity-specific drop).

Usage:
  python scripts/phase5b_qkv.py --bench data/bench/bench_curated.json \
      --carry L14H4_L14H5_L14H23_L15H8_L17H27_L18H20_L21H10 --n-prompts 4
"""
from __future__ import annotations
import argparse, json, os, re, sys, time
from collections import defaultdict
from contextlib import ExitStack
from typing import Dict, List, Sequence, Any
import numpy as np
import torch

HERE = os.path.dirname(os.path.abspath(__file__)); DC = os.path.dirname(HERE)
sys.path.insert(0, DC)
import ds_common as dc
import pair_common as pc


# --------------------------------------------------------------------------- #
# New primitives: per-head q/k/v_proj OUTPUT capture + patch (GQA-aware)
# --------------------------------------------------------------------------- #
# q_proj output  = [b, seq, num_attention_heads   * head_dim]  (heads-major, head_dim contiguous)
# k/v_proj output = [b, seq, num_key_value_heads   * head_dim]  (GQA: fewer heads, same head_dim)
# Layout matches pc.ZHeadPatch's reshape of the o_proj input ([b,seq,n,head_dim]). These hook the
# projection OUTPUT (a forward hook), unlike ZHeadPatch/ZHeadCapture which hook the o_proj INPUT
# (a forward_pre_hook). head_dim is shared across q and k/v; only the HEAD COUNT differs.
_PROJ_ATTR = {"q": "q_proj", "k": "k_proj", "v": "v_proj"}


def _qkv_head_counts(model):
    cfg = model.config
    n_q = int(cfg.num_attention_heads)
    n_kv = int(getattr(cfg, "num_key_value_heads", n_q))
    hidden = int(getattr(cfg, "hidden_size", None) or cfg.n_embd)
    head_dim = int(getattr(cfg, "head_dim", 0) or (hidden // n_q))
    return n_q, n_kv, head_dim


def _proj_n_heads(proj, n_q, n_kv):
    return n_q if proj == "q" else n_kv


class QKVHeadCapture:
    """Capture per-head q/k/v_proj OUTPUT rows at a set of layers, at the LAST position.

    Registers a forward hook on each of `layers[li].self_attn.{q,k,v}_proj`. After a forward,
    `q[li]` is [n_q, head_dim]; `k[li]` / `v[li]` are [n_kv, head_dim] (GQA) — float32 CPU rows
    at the last sequence position. The q/k/v OUTPUT analogue of pc.ZHeadCapture (o_proj input)."""

    def __init__(self, model, layer_idxs: Sequence[int]):
        layers = dc._get_layers(model)
        self.projs = {(li, p): getattr(layers[li].self_attn, _PROJ_ATTR[p])
                      for li in layer_idxs for p in ("q", "k", "v")}
        self.n_q, self.n_kv, self.head_dim = _qkv_head_counts(model)
        self.q: Dict[int, torch.Tensor] = {}
        self.k: Dict[int, torch.Tensor] = {}
        self.v: Dict[int, torch.Tensor] = {}
        self._store = {"q": self.q, "k": self.k, "v": self.v}
        self._handles: List[Any] = []

    def _hook(self, li, p):
        n_heads = _proj_n_heads(p, self.n_q, self.n_kv)
        store = self._store[p]

        def f(module, inp, out):
            h = out[0] if isinstance(out, tuple) else out
            last = h.shape[1] - 1
            store[li] = h[0, last].view(n_heads, self.head_dim).float().cpu()
            return None
        return f

    def __enter__(self):
        for (li, p), proj in self.projs.items():
            self._handles.append(proj.register_forward_hook(self._hook(li, p)))
        return self

    def __exit__(self, *exc):
        for h in self._handles:
            h.remove()
        self._handles = []
        return False


class QKVHeadPatch:
    """Replace the per-head q/k/v_proj OUTPUT slice `head` at `positions` with `vec` [head_dim].

    Registers a forward hook on `layers[layer_idx].self_attn.{q,k,v}_proj` that reshapes the
    projection OUTPUT to [b, seq, n_heads, head_dim] (n_heads = num_attention_heads for q,
    num_key_value_heads for k/v), overwrites head `head` at each in-range position, and flattens
    back. The q/k/v OUTPUT analogue of pc.ZHeadPatch (which patches the o_proj INPUT). batch>1
    fails loud (mirrors ZHeadPatch, audit finding 5); out-of-range positions are skipped
    (decode-step safe). vec is cast to the module dtype so a self-swap (bf16<->fp32 round-trip)
    is an EXACT no-op."""

    def __init__(self, model, layer_idx: int, proj: str, head: int,
                 positions: Sequence[int], vec: torch.Tensor):
        if proj not in _PROJ_ATTR:
            raise ValueError(f"proj must be one of {sorted(_PROJ_ATTR)}")
        self.module = getattr(dc._get_layers(model)[layer_idx].self_attn, _PROJ_ATTR[proj])
        n_q, n_kv, head_dim = _qkv_head_counts(model)
        self.n_heads = _proj_n_heads(proj, n_q, n_kv)
        self.head_dim = head_dim
        if not (0 <= head < self.n_heads):
            raise IndexError(f"{proj} head {head} out of range for {self.n_heads} heads")
        self.head = head
        self.positions = list(positions)
        self.vec = vec.detach().float()
        self._handle = None

    def _hook(self, module, inp, out):
        is_tuple = isinstance(out, tuple)
        h = out[0] if is_tuple else out
        b, seq, hh = h.shape
        if b != 1:
            raise NotImplementedError("QKVHeadPatch supports batch size 1 only")
        hr = h.view(b, seq, self.n_heads, self.head_dim).clone()
        v = self.vec.to(device=h.device, dtype=h.dtype)
        for p in self.positions:
            if 0 <= p < seq:
                hr[0, p, self.head, :] = v
        hr = hr.view(b, seq, hh)
        return (hr,) + tuple(out[1:]) if is_tuple else hr

    def __enter__(self):
        self._handle = self.module.register_forward_hook(self._hook)
        return self

    def __exit__(self, *exc):
        if self._handle is not None:
            self._handle.remove()
            self._handle = None
        return False


# --------------------------------------------------------------------------- #
# FC DE_context readout (identical to phase5 / phase7c)
# --------------------------------------------------------------------------- #
def _single_id(tok, word):
    return tok.encode(" " + word, add_special_tokens=False)[0]


FC_PREFIX = "Choose one label only and answer with just that label."
def fc_question(codeword, concept):
    return (f'{FC_PREFIX} In the text above, does the word "{codeword}" '
            f'refer to "{concept}" or to "{codeword}"?')


def demo_block_of(ds_prompt, marker="\n\nDo not reason, just "):
    return ds_prompt.rsplit(marker, 1)[0] if marker in ds_prompt else ds_prompt


def parse_heads(s):
    return [(int(l), int(h)) for l, h in re.findall(r"[Ll](\d+)[Hh](\d+)", s)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bench", required=True)
    ap.add_argument("--model", default=dc.PRIMARY_MODEL)
    ap.add_argument("--out-root", default=os.path.join(DC, "outputs"))
    ap.add_argument("--splits", default="dev,heldout")
    ap.add_argument("--carry", default="L14H4_L14H5_L14H23_L15H8_L17H27_L18H20_L21H10",
                    help="validated carry heads as L{l}H{h}_... (regex parsed)")
    ap.add_argument("--n-prompts", type=int, default=0, help="0 = all DS prompts per split")
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    dc.set_seed(args.seed)
    rng = np.random.default_rng(args.seed)
    bench = json.load(open(args.bench))
    lm = dc.load_model(args.model)
    L = lm.num_layers
    dev = lm.model.device
    cohort = bench.get("_meta", {}).get("cohort", "?")
    n_q, n_kv, head_dim = _qkv_head_counts(lm.model)
    group = n_q // n_kv                       # GQA group size: query heads per KV head
    carry = [(l, h) for (l, h) in parse_heads(args.carry) if 0 <= l < L and 0 <= h < n_q]

    splits = [s.strip() for s in args.splits.split(",") if s.strip()]
    rows = [r for r in bench["semantic"] if r["split"] in splits]
    by_key = {(r["condition"], r["split"], r["sid"]): r for r in rows}
    ds_rows = defaultdict(list)
    for r in rows:
        if r["condition"] == "DOUBLESPEAK":
            ds_rows[r["split"]].append(r)
    carry_layers = sorted({l for (l, _) in carry})

    ts = time.strftime("%Y%m%d_%H%M%S")
    uniq = os.environ.get("SLURM_JOB_ID") or str(os.getpid())
    out_dir = os.path.join(args.out_root, f"phase5b_qkv_{cohort}_{ts}_{uniq}")
    os.makedirs(out_dir, exist_ok=True)
    fh = open(os.path.join(out_dir, "raw.jsonl"), "w")
    print(f"[qkv] cohort={cohort} L={L} n_q={n_q} n_kv={n_kv} group={group} "
          f"carry={carry} -> {out_dir}")

    def build_fc(raw_prompt, codeword, concept):
        fc_raw = demo_block_of(raw_prompt) + "\n\n" + fc_question(codeword, concept)
        templated = dc.apply_template(lm.tokenizer, fc_raw)
        tok = lm.tokenizer(templated, return_tensors="pt", add_special_tokens=False).to(dev)
        return tok

    @torch.no_grad()
    def readout(tok, cid, kid, ctx=()):
        with ExitStack() as st:
            for c in ctx:
                st.enter_context(c)
            out = lm.model(**tok, return_dict=True)
        p = torch.softmax(out.logits[0, -1, :].float(), dim=-1)
        pc_, pk_ = float(p[cid]), float(p[kid])
        return pc_ / (pc_ + pk_ + 1e-12)

    @torch.no_grad()
    def cap_qkv_last(tok):
        """{proj: {layer: Tensor[n_heads, head_dim]}} of per-head q/k/v_proj output at last pos."""
        with QKVHeadCapture(lm.model, carry_layers) as cap:
            lm.model(**tok, return_dict=True)
        return {"q": dict(cap.q), "k": dict(cap.k), "v": dict(cap.v)}

    n_written = 0
    skips = defaultdict(int)
    for split in splits:
        cand = sorted(ds_rows.get(split, []), key=lambda r: r["sid"])
        if args.n_prompts:
            cand = cand[: args.n_prompts]
        for r in cand:
            concept, codeword = r["target_concept"], r["codeword"]
            cid, kid = _single_id(lm.tokenizer, concept), _single_id(lm.tokenizer, codeword)
            if cid == kid:
                skips[f"{split}:cid_eq_kid"] += 1
                continue
            brow = by_key.get(("BENIGN_REMAP", split, r["sid"]))
            if brow is None:
                skips[f"{split}:no_benign"] += 1
                continue
            ds_tok = build_fc(r["prompt"], codeword, concept)
            b_tok = build_fc(brow["prompt"], codeword, concept)
            ds_last = ds_tok["input_ids"].shape[1] - 1     # answer position (DS receiver)
            benign_p = readout(b_tok, cid, kid)
            c1 = readout(ds_tok, cid, kid)
            qkv_ds = cap_qkv_last(ds_tok)                  # DS own (self-swap donor)
            qkv_b = cap_qkv_last(b_tok)                    # matched BENIGN donor
            base = {"sid": r["sid"], "split": split, "cohort": cohort, "concept": concept,
                    "codeword": codeword, "benign_p_concept": benign_p, "C1": c1}

            for (l, h) in carry:
                kv = h // group                            # GQA: query head h -> KV head kv
                head_of = {"q": h, "k": kv, "v": kv}
                nheads_of = {"q": n_q, "k": n_kv, "v": n_kv}
                for proj in ("q", "k", "v"):
                    ph = head_of[proj]
                    # ---- necessity: DS <proj> slice <- matched BENIGN slice ----
                    donor = qkv_b[proj][l][ph].to(dev)
                    p_nec = readout(ds_tok, cid, kid,
                                    [QKVHeadPatch(lm.model, l, proj, ph, [ds_last], donor)])
                    fh.write(json.dumps({**base, "layer": l, "head": h, "proj": proj,
                                         "cell": proj, "p_concept": p_nec}) + "\n")
                    # ---- self-swap: DS <proj> slice <- DS OWN slice (exact no-op) ----
                    self_v = qkv_ds[proj][l][ph].to(dev)
                    p_self = readout(ds_tok, cid, kid,
                                     [QKVHeadPatch(lm.model, l, proj, ph, [ds_last], self_v)])
                    fh.write(json.dumps({**base, "layer": l, "head": h, "proj": proj,
                                         "cell": proj + "_self", "p_concept": p_self}) + "\n")
                    # ---- random-head control: BENIGN slice from a random OTHER head ----
                    others = [j for j in range(nheads_of[proj]) if j != ph]
                    rh = int(rng.choice(others)) if others else ph
                    rand_v = qkv_b[proj][l][rh].to(dev)
                    p_rand = readout(ds_tok, cid, kid,
                                     [QKVHeadPatch(lm.model, l, proj, ph, [ds_last], rand_v)])
                    fh.write(json.dumps({**base, "layer": l, "head": h, "proj": proj,
                                         "cell": proj + "_rand", "rand_head": rh,
                                         "p_concept": p_rand}) + "\n")
                    n_written += 3
    fh.close()

    # ---- per-split paired necessity + bootstrap CI ----
    all_rows = [json.loads(x) for x in open(os.path.join(out_dir, "raw.jsonl"))]
    rng2 = np.random.default_rng(0)
    def bootci(vals):
        if not vals:
            return None
        a = np.array(vals, float)
        b = [rng2.choice(a, len(a), replace=True).mean() for _ in range(2000)]
        return [round(float(a.mean()), 4), round(float(np.percentile(b, 2.5)), 4),
                round(float(np.percentile(b, 97.5)), 4)]

    summ = {}
    for split in splits:
        sr = [r for r in all_rows if r["split"] == split]
        valid = {r["sid"] for r in sr if r["cell"] in ("q", "k", "v")
                 and r["benign_p_concept"] is not None and r["C1"] > r["benign_p_concept"]}
        # self-swap faithfulness: max |C1 - p| across ALL *_self cells (must be ~0)
        selfdev = 0.0
        for r in sr:
            if r["cell"].endswith("_self"):
                selfdev = max(selfdev, abs(r["C1"] - r["p_concept"]))
        heads = {}
        for (l, h) in carry:
            cell = {}
            for proj in ("q", "k", "v"):
                nec = {r["sid"]: r["p_concept"] for r in sr
                       if r["cell"] == proj and r["layer"] == l and r["head"] == h}
                rnd = {r["sid"]: r["p_concept"] for r in sr
                       if r["cell"] == proj + "_rand" and r["layer"] == l and r["head"] == h}
                keep = [s for s in valid if s in nec]
                keep_r = [s for s in valid if s in nec and s in rnd]
                c1m = {r["sid"]: r["C1"] for r in sr}
                cell[proj] = {
                    "necessity_ci": bootci([c1m[s] - nec[s] for s in keep]),
                    "mean_patched": (round(float(np.mean([nec[s] for s in keep])), 4)
                                     if keep else None),
                    "necessity_specific_ci": bootci([rnd[s] - nec[s] for s in keep_r]),
                }
            heads[f"L{l}H{h}"] = cell
        summ[split] = {"n_valid": len(valid), "selfswap_max_dev": round(selfdev, 6),
                       "heads": heads}
    json.dump({"cohort": cohort, "model": args.model, "n_rows": n_written,
               "n_q": n_q, "n_kv": n_kv, "group": group, "head_dim": head_dim,
               "carry": args.carry, "skips": dict(skips), "by_split": summ},
              open(os.path.join(out_dir, "summary.json"), "w"), indent=1)
    print(f"[qkv] {n_written} rows -> {out_dir}")
    for split, s in summ.items():
        print(f"  [{split}] n_valid={s['n_valid']} selfswap_dev={s['selfswap_max_dev']}")
        for hd, cell in s["heads"].items():
            print(f"     {hd}: "
                  f"Q_nec={cell['q']['necessity_ci']} "
                  f"K_nec={cell['k']['necessity_ci']} "
                  f"V_nec={cell['v']['necessity_ci']}")


if __name__ == "__main__":
    main()
