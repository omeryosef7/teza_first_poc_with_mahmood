#!/usr/bin/env python3
"""Phase 4b: attention-PATTERN patching for the validated carry heads (complements the
edge-KNOCKOUT of scripts/phase4_edge_knockout.py).

The edge-knockout asks "does REMOVING the query->demo attention edges at a head drop the
Doublespeak reading?" (it edits the pre-softmax additive mask). This asks the dual, softer
question: "does REPLACING the DS attention-probability ROW at the FC answer position with the
matched BENIGN pattern drop the reading?" A carry head that reads the concept via WHERE it
attends (not just via its value content) should lose the reading when its answer-position
attention distribution is overwritten with the benign one, more than when overwritten with an
arbitrary head's pattern (specificity) and while its OWN pattern is an exact no-op.

WHY EAGER (attn_implementation="eager") IS REQUIRED
---------------------------------------------------
Pattern patching needs the post-softmax attention-probability tensor [batch, num_attention_heads,
q_len, k_len] materialized in Python so we can read a row (capture) and write a row (replace).
Under SDPA / flash-attention the softmax and the probs@V matmul are FUSED inside a kernel and no
probability tensor is ever exposed — a "replace the attention row" hook silently becomes a no-op,
exactly the footgun documented on pc.AttentionKnockout. Only the EAGER path calls the module-level
`eager_attention_forward(module, q, k, v, attention_mask, scaling, ...)`, which returns
`(attn_output, attn_weights)`. So this file, like phase4_edge_knockout, loads the model eager.

HOOK POINT (defined in-file: `_EagerAttnCapture` / `_EagerAttnPatch`)
---------------------------------------------------------------------
Rather than a forward hook on `self_attn` (which only sees the block INPUT/OUTPUT, never the probs),
we wrap the transformers modeling module's `eager_attention_forward` global — the symbol that
`LlamaAttention.forward` looks up BY NAME at call time — for the duration of the context, restoring
it on exit. The wrapper delegates every non-target module verbatim to the original function
(bit-identical), and for a target `self_attn` module it:
  * CAPTURE: reads the original's returned `attn_weights[0, head, qpos, :]` and stores it; returns
    the original outputs UNCHANGED (fully non-invasive).
  * REPLACE: overwrites `attn_weights[0, head, qpos, :]` with the donor row, then RECOMPUTES
    attn_output = (repeat_kv(value) is GQA-expanded to num_attention_heads) probs @ V with the SAME
    ops the original used, so an unmodified row reproduces the baseline to the bit.
GQA note: `attn_weights` is over `num_attention_heads` (32 for Llama-3.1-8B), NOT
`num_key_value_heads` (8) — heads index the query-head axis; value is repeat_kv-expanded to match,
mirroring the GQA note on pc.AttentionKnockout / pc.ZHeadPatch.

CONTROLS
--------
  C1        DS baseline (no wrapper).
  C_benign  necessity: candidate heads' answer-row <- matched BENIGN pattern (trailing-aligned +
            renormalized to k_ds when the DS/benign FC lengths differ; see align_row).
  C_uniform pattern-space knockout: candidate rows <- uniform over causal keys (washes out WHERE
            the head looks) — the "vs knockout" comparison inside the pattern frame.
  C_rand    specificity: candidate rows <- a random NON-candidate head's OWN DS pattern (count-matched).
  C_self    MANDATORY exact-no-op sanity: candidate rows <- their OWN captured DS pattern. Because
            capture reads the original probs and replace recomputes probs@V with identical ops,
            C_self reproduces C1 to the bit -> selfswap_max_dev is exactly 0.0.
necessity_raw = C1 - C_benign ; necessity_specific = C_rand - C_benign (paired, bootstrap CI).
dev(train)/heldout(test) summarized SEPARATELY. Forced-choice FC readout, no API text emitted.

Usage:
  python scripts/phase4b_pattern.py --bench data/bench/bench_curated.json --n-prompts 2
  python scripts/phase4b_pattern.py --bench data/bench/bench_curated.json \
      --heads L14H4_L14H5_L14H23_L15H8_L17H27_L18H20_L21H10
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
# In-file eager-attention pattern primitives (see module docstring for the eager
# requirement + the GQA note). Both wrap the modeling module's `eager_attention_forward`
# and restore it on __exit__; non-target modules are delegated verbatim (bit-identical).
# --------------------------------------------------------------------------- #
def _modeling_of(model):
    """The python module that defines this model's attention forward (holds the
    `eager_attention_forward` global that LlamaAttention.forward resolves by name)."""
    attn = dc._get_layers(model)[0].self_attn
    return sys.modules[type(attn).__module__]


def _repeat_kv(x: torch.Tensor, n_rep: int) -> torch.Tensor:
    """GQA key/value head expansion, bit-identical to HF transformers.repeat_kv."""
    if n_rep == 1:
        return x
    b, kvh, s, d = x.shape
    return x[:, :, None, :, :].expand(b, kvh, n_rep, s, d).reshape(b, kvh * n_rep, s, d)


def _require_eager(model):
    impl = getattr(model.config, "_attn_implementation", None)
    if impl != "eager":
        raise RuntimeError(
            "attention-pattern patching needs the materialized probs tensor; load with "
            f"attn_implementation='eager' (got {impl!r}). SDPA/flash fuse softmax@V and the "
            "pattern hook silently no-ops.")


class _EagerAttnCapture:
    """Capture post-softmax attention rows attn_weights[0, head, qpos, :k_len] for a list of
    (layer, head, qpos) sites, by wrapping `eager_attention_forward`. Non-invasive: the original
    outputs are returned unchanged. After the forward, `.rows[(layer, head, qpos)]` is a float32
    CPU tensor of length k_len (the current sequence length)."""

    def __init__(self, model, sites: Sequence):
        _require_eager(model)
        self.modeling = _modeling_of(model)
        self._orig = None
        layers = dc._get_layers(model)
        # id(self_attn module) -> (layer_idx, [(head, qpos), ...])
        self.targets: Dict[int, Any] = {}
        self._id2layer: Dict[int, int] = {}
        for (l, h, qp) in sites:
            mod = layers[l].self_attn
            self._id2layer[id(mod)] = l
            self.targets.setdefault(id(mod), []).append((h, qp))
        self.rows: Dict[Any, torch.Tensor] = {}

    def _wrapper(self, orig):
        def w(module, query, key, value, attention_mask, *a, **kw):
            out = orig(module, query, key, value, attention_mask, *a, **kw)
            attn_output, attn_weights = out
            spec = self.targets.get(id(module))
            if spec is not None and attn_weights is not None:
                l = self._id2layer[id(module)]
                for (h, qp) in spec:
                    if qp < attn_weights.shape[2]:
                        self.rows[(l, h, qp)] = attn_weights[0, h, qp, :].detach().float().cpu().clone()
            return out
        return w

    def __enter__(self):
        self._orig = self.modeling.eager_attention_forward
        self.modeling.eager_attention_forward = self._wrapper(self._orig)
        return self

    def __exit__(self, *exc):
        self.modeling.eager_attention_forward = self._orig
        self._orig = None
        return False


class _EagerAttnPatch:
    """Overwrite post-softmax attention rows attn_weights[0, head, qpos, :] with a donor row and
    RECOMPUTE attn_output = probs @ repeat_kv(value), by wrapping `eager_attention_forward`.

    `patches` is a list of (layer, head, qpos, donor) where donor is a 1-D tensor whose length
    equals the current k_len (the caller aligns/renormalizes; a full-length donor gives a clean
    row replacement). SELF-SWAP EXACTNESS: donor == the row the original just produced ->
    unchanged attn_weights -> the recomputed probs@V matches the original op-for-op -> exact
    no-op. Non-target modules are delegated verbatim."""

    def __init__(self, model, patches: Sequence):
        _require_eager(model)
        self.modeling = _modeling_of(model)
        self._orig = None
        layers = dc._get_layers(model)
        self.targets: Dict[int, List] = {}
        for (l, h, qp, donor) in patches:
            mod = layers[l].self_attn
            self.targets.setdefault(id(mod), []).append((h, qp, donor.detach().float()))
        self._repeat_kv = getattr(self.modeling, "repeat_kv", _repeat_kv)

    def _wrapper(self, orig):
        def w(module, query, key, value, attention_mask, *a, **kw):
            attn_output, attn_weights = orig(module, query, key, value, attention_mask, *a, **kw)
            spec = self.targets.get(id(module))
            if spec is None or attn_weights is None:
                return attn_output, attn_weights
            aw = attn_weights.clone()
            k_len = aw.shape[3]
            for (h, qp, donor) in spec:
                if qp < aw.shape[2]:
                    d = donor.to(device=aw.device, dtype=aw.dtype)
                    n = min(d.shape[0], k_len)
                    aw[0, h, qp, :] = 0
                    aw[0, h, qp, :n] = d[:n]
            n_rep = int(getattr(module, "num_key_value_groups", 1))
            value_states = self._repeat_kv(value, n_rep)
            attn_output = torch.matmul(aw, value_states).transpose(1, 2).contiguous()
            return attn_output, aw
        return w

    def __enter__(self):
        self._orig = self.modeling.eager_attention_forward
        self.modeling.eager_attention_forward = self._wrapper(self._orig)
        return self

    def __exit__(self, *exc):
        self.modeling.eager_attention_forward = self._orig
        self._orig = None
        return False


# --------------------------------------------------------------------------- #
# FC DE_context readout scaffolding (mirrors phase5 / phase7c / phase6 exactly)
# --------------------------------------------------------------------------- #
FC_PREFIX = "Choose one label only and answer with just that label."
def fc_question(cw, co):
    return f'{FC_PREFIX} In the text above, does the word "{cw}" refer to "{co}" or to "{cw}"?'
def demo_block_of(p, m="\n\nDo not reason, just "):
    return p.rsplit(m, 1)[0] if m in p else p
def _single_id(tok, w):
    return tok.encode(" " + w, add_special_tokens=False)[0]
def parse_heads(s):
    return [(int(l), int(h)) for l, h in re.findall(r"[Ll](\d+)[Hh](\d+)", s)]


def align_row(donor: torch.Tensor, k_target: int) -> torch.Tensor:
    """Map a donor attention row (length k_donor) onto a k_target-length row by TRAILING
    alignment (both prompts end at their own answer position) + renormalization to a valid
    distribution. Exact when k_donor == k_target. APPROXIMATE across lengths: key positions do
    not correspond token-for-token when the DS/benign demo text differs, so leading keys that
    the shorter prompt lacks receive 0 mass; documented as a risk."""
    d = donor.float()
    kd = d.shape[0]
    out = torch.zeros(k_target, dtype=torch.float32)
    m = min(kd, k_target)
    out[k_target - m:] = d[kd - m:]
    s = float(out.sum())
    if s > 0:
        out = out / s
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bench", required=True)
    ap.add_argument("--model", default=dc.PRIMARY_MODEL)
    ap.add_argument("--out-root", default=os.path.join(DC, "outputs"))
    ap.add_argument("--splits", default="dev,heldout")
    ap.add_argument("--heads", default="L14H4_L14H5_L14H23_L15H8_L17H27_L18H20_L21H10",
                    help="candidate carry heads, parsed via regex L<layer>H<head>")
    ap.add_argument("--n-prompts", type=int, default=0, help="0 = all DS prompts per split")
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    dc.set_seed(args.seed)
    rng = np.random.default_rng(args.seed)
    bench = json.load(open(args.bench))
    lm = dc.load_model(args.model, attn_implementation="eager")   # REQUIRED for pattern patching
    L = lm.num_layers
    nH, hd = pc._attn_head_dims(lm.model)
    dev = lm.model.device
    cohort = bench.get("_meta", {}).get("cohort", "?")
    carry = parse_heads(args.heads)
    carry_set = set(carry)
    if not carry:
        raise SystemExit("no candidate heads parsed from --heads")

    splits = [s.strip() for s in args.splits.split(",") if s.strip()]
    rows = [r for r in bench["semantic"] if r["split"] in splits]
    by_key = {(r["condition"], r["split"], r["sid"]): r for r in rows}
    ds_by = {sp: [r for r in rows if r["condition"] == "DOUBLESPEAK" and r["split"] == sp] for sp in splits}

    ts = time.strftime("%Y%m%d_%H%M%S"); uniq = os.environ.get("SLURM_JOB_ID") or str(os.getpid())
    out_dir = os.path.join(args.out_root, f"phase4b_pattern_{cohort}_{ts}_{uniq}")
    os.makedirs(out_dir, exist_ok=True); fh = open(os.path.join(out_dir, "raw.jsonl"), "w")
    print(f"[pat] cohort={cohort} L={L} nH={nH} carry={carry} -> {out_dir}")

    def build_fc(raw, cw, co):
        t = dc.apply_template(lm.tokenizer, demo_block_of(raw) + "\n\n" + fc_question(cw, co))
        tok = lm.tokenizer(t, return_tensors="pt", add_special_tokens=False).to(dev)
        return tok, tok["input_ids"].shape[1] - 1        # (tok, answer position = last token)

    @torch.no_grad()
    def readout(tok, cid, kid, ctx=()):
        with ExitStack() as st:
            for c in ctx:
                st.enter_context(c)
            out = lm.model(**tok, return_dict=True)
        p = torch.softmax(out.logits[0, -1, :].float(), -1)
        pcv, pkv = float(p[cid]), float(p[kid])
        return pcv / (pcv + pkv + 1e-12)

    @torch.no_grad()
    def capture_rows(tok, sites):
        with _EagerAttnCapture(lm.model, sites) as cap:
            lm.model(**tok, return_dict=True)
        return cap.rows

    n_written = 0
    skips = defaultdict(int)
    for split in splits:
        cand = sorted(ds_by.get(split, []), key=lambda r: r["sid"])
        if args.n_prompts:
            cand = cand[: args.n_prompts]
        for r in cand:
            co, cw = r["target_concept"], r["codeword"]
            cid, kid = _single_id(lm.tokenizer, co), _single_id(lm.tokenizer, cw)
            if cid == kid:
                skips[f"{split}:cid_eq_kid"] += 1
                continue
            brow = by_key.get(("BENIGN_REMAP", split, r["sid"]))
            if brow is None:
                skips[f"{split}:no_benign_row"] += 1
                continue
            ds_tok, ds_last = build_fc(r["prompt"], cw, co)
            b_tok, b_last = build_fc(brow["prompt"], cw, co)
            k_ds = ds_tok["input_ids"].shape[1]

            benign_p = readout(b_tok, cid, kid)
            c1 = readout(ds_tok, cid, kid)

            # random NON-candidate heads (count-matched), for the specificity control
            pool = [(l, h) for l in range(L) for h in range(nH) if (l, h) not in carry_set]
            rand_heads = [pool[i] for i in rng.choice(len(pool), size=len(carry), replace=False)]

            # capture the DS answer-row for candidate heads (self + validity) and for the random heads
            ds_sites = [(l, h, ds_last) for (l, h) in carry] + [(l, h, ds_last) for (l, h) in rand_heads]
            ds_rows = capture_rows(ds_tok, ds_sites)
            # capture the matched BENIGN answer-row for candidate heads (necessity donor)
            b_rows = capture_rows(b_tok, [(l, h, b_last) for (l, h) in carry])

            base = {"sid": r["sid"], "split": split, "cohort": cohort, "concept": co,
                    "codeword": cw, "benign_p_concept": benign_p, "C1": c1, "k_ds": k_ds,
                    "len_mismatch": bool(b_tok["input_ids"].shape[1] != k_ds)}

            # ---- build the per-arm patch lists at the DS answer position ----
            benign_patch, uniform_patch, self_patch, rand_patch = [], [], [], []
            uni = torch.full((k_ds,), 1.0 / k_ds, dtype=torch.float32)
            for j, (l, h) in enumerate(carry):
                benign_patch.append((l, h, ds_last, align_row(b_rows[(l, h, b_last)], k_ds)))
                uniform_patch.append((l, h, ds_last, uni.clone()))
                self_patch.append((l, h, ds_last, ds_rows[(l, h, ds_last)]))   # length == k_ds exactly
                rl, rh = rand_heads[j]
                rand_patch.append((l, h, ds_last, ds_rows[(rl, rh, ds_last)])) # donor length == k_ds

            def emit(cell, patch):
                nonlocal n_written
                p = readout(ds_tok, cid, kid, [_EagerAttnPatch(lm.model, patch)]) if patch else c1
                fh.write(json.dumps({**base, "cell": cell, "p_concept": p}) + "\n")
                n_written += 1

            emit("C_benign", benign_patch)
            emit("C_uniform", uniform_patch)
            emit("C_rand", rand_patch)
            emit("C_self", self_patch)
    fh.close()

    # ---- dev(train)/heldout(test) SEPARATE; paired diffs; bootstrap CI ----
    allr = [json.loads(x) for x in open(os.path.join(out_dir, "raw.jsonl"))]
    rng2 = np.random.default_rng(0)
    def bootci(v):
        if not v:
            return None
        a = np.array(v, float)
        b = [rng2.choice(a, len(a), replace=True).mean() for _ in range(2000)]
        return [round(float(a.mean()), 4), round(float(np.percentile(b, 2.5)), 4),
                round(float(np.percentile(b, 97.5)), 4)]

    summ = {}
    for split in splits:
        sr = [r for r in allr if r["split"] == split]
        def cm(cell):
            return {r["sid"]: r["p_concept"] for r in sr if r["cell"] == cell}
        c1 = {r["sid"]: r["C1"] for r in sr}
        bp = {r["sid"]: r["benign_p_concept"] for r in sr}
        cben, cuni, cran, cslf = cm("C_benign"), cm("C_uniform"), cm("C_rand"), cm("C_self")
        # validity: DS reads the concept above its matched benign baseline (mirrors phase4/6)
        valid = {s for s in c1 if bp.get(s) is not None and c1[s] > bp[s]}
        nec = [s for s in valid if s in cben and s in cran]
        selfdev = max([abs(c1[s] - cslf[s]) for s in cslf], default=0.0)
        summ[split] = {
            "n_valid": len(nec),
            "mean_C1": round(float(np.mean([c1[s] for s in nec])), 4) if nec else None,
            "mean_C_benign": round(float(np.mean([cben[s] for s in nec])), 4) if nec else None,
            "necessity_raw_ci_C1_minus_Cbenign": bootci([c1[s] - cben[s] for s in nec]),
            "necessity_specific_ci_Crand_minus_Cbenign": bootci([cran[s] - cben[s] for s in nec]),
            "knockout_uniform_raw_ci_C1_minus_Cuniform":
                bootci([c1[s] - cuni[s] for s in nec if s in cuni]),
            "selfswap_max_dev": round(float(selfdev), 6),
            "n_len_mismatch": sum(1 for r in sr if r["cell"] == "C_benign" and r["len_mismatch"]),
        }
    json.dump({"cohort": cohort, "model": args.model, "heads": args.heads, "carry": carry,
               "n_rows": n_written, "n_heads": nH, "skips": dict(skips), "by_split": summ},
              open(os.path.join(out_dir, "summary.json"), "w"), indent=1)
    print(f"[pat] {n_written} rows -> {out_dir}  skips={dict(skips)}")
    for sp, s in summ.items():
        print(f"  [{sp}] n_valid={s['n_valid']} C1={s['mean_C1']} C_benign={s['mean_C_benign']} "
              f"nec_raw={s['necessity_raw_ci_C1_minus_Cbenign']} "
              f"nec_specific={s['necessity_specific_ci_Crand_minus_Cbenign']} "
              f"selfdev={s['selfswap_max_dev']} len_mismatch={s['n_len_mismatch']}")


if __name__ == "__main__":
    main()
