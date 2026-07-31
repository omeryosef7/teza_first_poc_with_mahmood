"""
48_attribution_patching.py — Attribution Patching (AtP) to LOCALIZE where the
Doublespeak in-context demonstrations install the codeword->concept reading.

NEW technique for this project (CORRECTNESS-GATED). AtP (Nanda 2023; Kramar et al.
"AtP*", 2024) is a first-order Taylor approximation to activation patching: instead of
running one patched forward PER (layer, position) cell, it estimates the effect of
patching each cell from a CLEAN forward's cached activations and their gradients in a
SINGLE backward pass:

    AtP[L, pos]  =  grad_{M}(clean_act[L, pos]) . (corrupt_act[L, pos] - clean_act[L, pos])

where M is the readout metric and `.` is the hidden-dim dot product. This linearizes M
around the clean activations, so it is only trustworthy where M is approximately linear
in the patched activation — hence the mandatory validation gate below.

CLEAN vs CORRUPT (the contrast).
  * clean   = a DOUBLESPEAK prompt (demonstrations installed; the codeword reads as the
              concept). M is measured here.
  * corrupt = the matched NEUTRAL_CODEWORD prompt (same split / demo_style / n_demos /
              readout / probe word; benign demonstrations, so the codeword reads
              literally). This is the "neutral-codeword-state" reference.

POSITION ALIGNMENT (design decision, see the header of `build_alignment`).
  DOUBLESPEAK and NEUTRAL_CODEWORD are NOT token-length-matched (the demonstration
  sentences differ in content and length), so absolute-index subtraction is invalid.
  We therefore attribute over exactly the positions that HAVE a well-defined
  token-aligned corrupt counterpart:
    (a) the shared READOUT-QUERY SUFFIX — the longest common token suffix of the two
        templated prompts (the readout question is identical across conditions); each
        clean suffix position is paired with the corrupt position at the same suffix
        offset (token-identical), and
    (b) the DEMONSTRATION CODEWORD sites — the i-th codeword occurrence in the clean
        demos is paired with the i-th codeword occurrence in the corrupt demos (the
        codeword token itself is shared: "carrot" appears in both), up to the smaller
        count.
  This is exactly the region the fixed-pair causal core already implicates (the codeword
  sites + the query); non-codeword demonstration tokens have no token-aligned neutral
  counterpart and are deliberately excluded rather than aligned by a fabricated index.

METRIC.
  M = logit(concept) - logit(codeword) at the final prompt position (mean over the
  first-token surface forms of each word), computed in fp32. A logit DIFFERENCE is used
  (not a probability) because it is the most linear readout and therefore the one for
  which the AtP Taylor approximation is tightest. `--metric p_concept` switches to
  log P(concept) for a probability-space map (expect a weaker correlation).

VALIDATION (the correctness gate — mandatory).
  For the top-k highest-|AtP| cells we run TRUE activation patching
  (ds_common.LayerPatch replace of that (layer, position) with the corrupt activation)
  and measure the real metric delta. We report Pearson AND Spearman of AtP-estimate vs
  true-delta over those cells. The AtP map is only reported as trustworthy when the
  correlation clears --min-corr (default 0.7); otherwise the script says so and the map
  must not be interpreted (fall back to reading the TRUE deltas it also records).

Reuse: ds_common.load_model / LayerPatch / _get_layers / apply_template;
pair_common.word_first_ids / resolve_positions. Scalars only are persisted (plan §5.12);
no harmful text is printed.

Deterministic. GPU script — do NOT run on CPU (needs model weights). The AtP<->true
equivalence math is unit-tested GPU-free in tests/test_attribution_patching.py on a
linear toy stack where AtP is EXACT.

Usage (L40S):
  python 48_attribution_patching.py --bench data/pair_benchmark/pair_carrot_bomb.json \
      --model meta-llama/Llama-3.1-8B-Instruct --reps-dir <unused-placeholder> \
      --topk 40 --out outputs/atp_carrot_bomb
"""
from __future__ import annotations

import os
import sys
import json
import time
import argparse
from typing import Callable, Dict, List, Optional, Sequence, Tuple

import numpy as np
import torch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ds_common as dc
import pair_common as pc

HERE = os.path.dirname(os.path.abspath(__file__))
Cell = Tuple[int, int]  # (layer_idx, position)


# --------------------------------------------------------------------------- #
# Correlation helpers (numpy-only; no scipy dependency)
# --------------------------------------------------------------------------- #
def pearson(x: Sequence[float], y: Sequence[float]) -> float:
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    if x.size < 2:
        return float("nan")
    xc, yc = x - x.mean(), y - y.mean()
    denom = np.sqrt((xc * xc).sum() * (yc * yc).sum())
    if denom <= 0:
        return float("nan")
    return float((xc * yc).sum() / denom)


def _ranks(a: np.ndarray) -> np.ndarray:
    """Average (fractional) ranks, ties shared — matches scipy's rankdata('average')."""
    order = np.argsort(a, kind="mergesort")
    ranks = np.empty(a.shape[0], dtype=np.float64)
    ranks[order] = np.arange(a.shape[0], dtype=np.float64)
    # resolve ties to their mean rank
    sa = a[order]
    i = 0
    n = a.shape[0]
    while i < n:
        j = i + 1
        while j < n and sa[j] == sa[i]:
            j += 1
        if j - i > 1:
            mean_rank = (ranks[order[i]] + ranks[order[j - 1]]) / 2.0
            for k in range(i, j):
                ranks[order[k]] = mean_rank
        i = j
    return ranks


def spearman(x: Sequence[float], y: Sequence[float]) -> float:
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    if x.size < 2:
        return float("nan")
    return pearson(_ranks(x), _ranks(y))


# --------------------------------------------------------------------------- #
# AtP engine — MODEL-AGNOSTIC so the linear toy in the unit test drives the SAME code.
# --------------------------------------------------------------------------- #
class _ActGradCapture:
    """Hook every target decoder layer's OUTPUT, retain its grad for the backward.

    The captured tensor is the block output residual == hidden_states[L+1], which is
    exactly what ds_common.LayerPatch(mode="replace") overwrites — so AtP and true
    patching operate on identical objects (the equivalence the gate checks).
    """

    def __init__(self, model, layer_idxs: Sequence[int]):
        self.layers = dc._get_layers(model)
        self.layer_idxs = list(layer_idxs)
        self.acts: Dict[int, torch.Tensor] = {}
        self._handles: List = []

    def _hook(self, li: int):
        def f(module, inputs, output):
            h = output[0] if isinstance(output, tuple) else output
            if h.requires_grad:
                h.retain_grad()
            self.acts[li] = h            # keep the graph node (do NOT detach/clone)
        return f

    def __enter__(self):
        for li in self.layer_idxs:
            self._handles.append(self.layers[li].register_forward_hook(self._hook(li)))
        return self

    def __exit__(self, *exc):
        for h in self._handles:
            h.remove()
        self._handles = []
        return False


def atp_estimate(
    model,
    forward_fn: Callable[[], object],
    metric_fn: Callable[[object], torch.Tensor],
    positions: Sequence[int],
    corrupt_acts: Dict[int, torch.Tensor],
    layer_idxs: Sequence[int],
) -> Tuple[Dict[Cell, float], float]:
    """First-order AtP estimate for every (layer, position) cell, one backward pass.

    Args:
      forward_fn:   () -> model output; runs the CLEAN forward through the hooked layers.
      metric_fn:    (output) -> scalar tensor M (fp32), the readout to attribute.
      positions:    clean-side token indices to attribute at.
      corrupt_acts: {layer_idx: Tensor[seq, hidden]} — the CORRUPT block-L output aligned
                    to the clean sequence (row `pos` is the corrupt counterpart of clean
                    position `pos`). Only the rows in `positions` are read.
      layer_idxs:   layers to attribute (block indices; output == hidden_states[L+1]).

    Returns ({(L, pos): atp_value}, M_clean).
    """
    cap = _ActGradCapture(model, layer_idxs)
    with torch.enable_grad():
        with cap:
            out = forward_fn()
            M = metric_fn(out)
        if hasattr(model, "zero_grad"):
            model.zero_grad(set_to_none=True)
        M.backward()

    est: Dict[Cell, float] = {}
    for L in layer_idxs:
        act = cap.acts[L]
        if act.grad is None:
            raise RuntimeError(f"no gradient captured at layer {L}; is grad enabled and "
                               f"does the metric depend on this layer's output?")
        a = act.detach()[0].float()          # [seq, hidden]
        g = act.grad[0].float()              # [seq, hidden]
        corr = corrupt_acts[L].float()       # [seq, hidden] (aligned rows)
        for pos in positions:
            delta = corr[pos] - a[pos]
            est[(L, pos)] = float((g[pos] * delta).sum())
    return est, float(M.detach())


def true_patch_delta(
    model,
    forward_fn: Callable[[], object],
    metric_fn: Callable[[object], torch.Tensor],
    layer: int,
    pos: int,
    corrupt_vec: torch.Tensor,
    m_clean: float,
) -> float:
    """Measured metric delta from a REAL replace-patch of one (layer, pos) cell."""
    with torch.no_grad():
        with dc.LayerPatch(model, layer, [pos], vector=corrupt_vec, mode="replace"):
            out = forward_fn()
            m = float(metric_fn(out).detach())
    return m - m_clean


# --------------------------------------------------------------------------- #
# Prompt / condition selection from the fixed-pair bench
# --------------------------------------------------------------------------- #
def _select_pair_rows(bench: dict, readout: str, split: str
                      ) -> Tuple[dict, dict]:
    """Pick a matched (DOUBLESPEAK clean, NEUTRAL_CODEWORD corrupt) row pair.

    Matched on (split, demo_style, n_demos, readout, probe_word) so the only intended
    difference is whether the demonstrations install the reading.
    """
    sem = bench["semantic"]
    ds = [r for r in sem if r["condition"] == "DOUBLESPEAK"
          and r["readout"] == readout and r["split"] == split and r.get("has_demos")]
    neu = {(r["demo_style"], r["n_demos"], r["probe_word"]): r
           for r in sem if r["condition"] == "NEUTRAL_CODEWORD"
           and r["readout"] == readout and r["split"] == split and r.get("has_demos")}
    for r in ds:
        key = (r["demo_style"], r["n_demos"], r["probe_word"])
        if key in neu:
            return r, neu[key]
    raise ValueError(f"no matched DOUBLESPEAK/NEUTRAL_CODEWORD pair for readout="
                     f"{readout!r} split={split!r}")


def build_alignment(
    lm, clean_text: str, corrupt_text: str, codeword: str,
) -> Tuple[List[int], Dict[int, int], Dict[str, object]]:
    """Positions to attribute on the CLEAN prompt + a clean->corrupt index map.

    Two token-aligned regions (see module header):
      (a) shared readout-query SUFFIX: the longest common token suffix of the two
          TEMPLATED, tokenized prompts. clean position -> corrupt position at the same
          suffix offset (token-identical).
      (b) DEMONSTRATION CODEWORD sites (outside the suffix): the i-th clean codeword
          occurrence paired with the i-th corrupt codeword occurrence (same token), up
          to min(count).

    Returns (clean_positions, clean_pos -> corrupt_pos, diagnostics).
    """
    ci = lm.tokenizer(clean_text, add_special_tokens=False)["input_ids"]
    ni = lm.tokenizer(corrupt_text, add_special_tokens=False)["input_ids"]

    # (a) longest common suffix
    s = 0
    while s < len(ci) and s < len(ni) and ci[-1 - s] == ni[-1 - s]:
        s += 1
    suffix_clean = list(range(len(ci) - s, len(ci)))
    mapping: Dict[int, int] = {}
    for off in range(s):
        mapping[len(ci) - 1 - off] = len(ni) - 1 - off

    # (b) demo codeword occurrences OUTSIDE the shared suffix
    suffix_start_clean = len(ci) - s
    suffix_start_corr = len(ni) - s
    cw_clean = [p for p in dc.find_word_occurrences(lm.tokenizer, ci, codeword).last_idx
                if p < suffix_start_clean]
    cw_corr = [p for p in dc.find_word_occurrences(lm.tokenizer, ni, codeword).last_idx
               if p < suffix_start_corr]
    n_demo = min(len(cw_clean), len(cw_corr))
    for i in range(n_demo):
        mapping[cw_clean[i]] = cw_corr[i]

    positions = sorted(mapping)
    diag = {
        "clean_len": len(ci), "corrupt_len": len(ni),
        "suffix_len": s, "n_suffix_positions": len(suffix_clean),
        "n_demo_codeword_clean": len(cw_clean), "n_demo_codeword_corrupt": len(cw_corr),
        "n_demo_codeword_paired": n_demo, "n_positions": len(positions),
    }
    return positions, mapping, diag


# --------------------------------------------------------------------------- #
# Corrupt-activation capture, aligned to the clean sequence
# --------------------------------------------------------------------------- #
@torch.no_grad()
def capture_layer_outputs(lm, text: str, layer_idxs: Sequence[int]) -> Dict[int, torch.Tensor]:
    """{layer_idx: Tensor[seq, hidden] fp32 CPU} of block outputs for one forward."""
    tok = lm.tokenizer(text, return_tensors="pt", add_special_tokens=False).to(lm.model.device)
    cap = _ActGradCapture(lm.model, layer_idxs)
    with cap:
        lm.model(**tok, return_dict=True)
    return {L: cap.acts[L].detach()[0].float().cpu() for L in layer_idxs}


def align_corrupt(
    corrupt_out: Dict[int, torch.Tensor], clean_seq_len: int,
    mapping: Dict[int, int], layer_idxs: Sequence[int],
) -> Dict[int, torch.Tensor]:
    """Reindex corrupt block outputs onto the CLEAN sequence via `mapping`.

    Row `clean_pos` of the result holds the corrupt activation at `mapping[clean_pos]`;
    unmapped rows are zeros (never read — `positions` only contains mapped indices).
    """
    hidden = next(iter(corrupt_out.values())).shape[-1]
    aligned: Dict[int, torch.Tensor] = {}
    for L in layer_idxs:
        buf = torch.zeros(clean_seq_len, hidden, dtype=torch.float32)
        src = corrupt_out[L]
        for cpos, npos in mapping.items():
            buf[cpos] = src[npos]
        aligned[L] = buf
    return aligned


# --------------------------------------------------------------------------- #
# Metric (readout) construction
# --------------------------------------------------------------------------- #
def make_metric(lm, concept: str, codeword: str, kind: str
                ) -> Callable[[object], torch.Tensor]:
    concept_ids = pc.word_first_ids(lm.tokenizer, concept)
    code_ids = pc.word_first_ids(lm.tokenizer, codeword)
    if not concept_ids or not code_ids:
        raise ValueError("empty first-token id set for concept or codeword")
    c_idx = torch.tensor(concept_ids)
    k_idx = torch.tensor(code_ids)

    def metric(out) -> torch.Tensor:
        logits = out.logits[0, -1, :].float()          # next-token logits, fp32
        if kind == "logit_diff":
            return logits[c_idx].mean() - logits[k_idx].mean()
        if kind == "p_concept":
            logp = torch.log_softmax(logits, dim=-1)
            return torch.logsumexp(logp[c_idx], dim=0)  # log P(concept surface forms)
        raise ValueError(f"unknown metric {kind!r}")

    return metric


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def run(lm, bench: dict, args) -> dict:
    pair = bench["pair"]
    concept, codeword = pair["concept"], pair["codeword"]
    clean_row, corrupt_row = _select_pair_rows(bench, args.readout, args.split)

    clean_text = dc.apply_template(lm.tokenizer, clean_row["prompt"])
    corrupt_text = dc.apply_template(lm.tokenizer, corrupt_row["prompt"])

    n_layers = lm.num_layers
    # Readout is the final-position next-token logits (post-final-block). Patching AT the
    # last block would overwrite nothing downstream of the readout, so attribute strictly
    # below it — reuse the single-source-of-truth sweep from ds_common.
    layer_idxs = dc.patch_layer_sweep(n_layers - 1) if args.layers == "" else \
        [int(x) for x in args.layers.split(",") if x.strip()]

    positions, mapping, diag = build_alignment(lm, clean_text, corrupt_text, codeword)
    if not positions:
        raise ValueError("no token-aligned positions between clean and corrupt prompts")

    metric = make_metric(lm, concept, codeword, args.metric)

    clean_seq_len = len(lm.tokenizer(clean_text, add_special_tokens=False)["input_ids"])
    corrupt_out = capture_layer_outputs(lm, corrupt_text, layer_idxs)
    corrupt_aligned = align_corrupt(corrupt_out, clean_seq_len, mapping, layer_idxs)
    corrupt_dev = {L: v.to(lm.model.device) for L, v in corrupt_aligned.items()}

    def clean_forward():
        tok = lm.tokenizer(clean_text, return_tensors="pt",
                           add_special_tokens=False).to(lm.model.device)
        return lm.model(**tok, return_dict=True)

    est, m_clean = atp_estimate(lm.model, clean_forward, metric,
                                positions, corrupt_dev, layer_idxs)

    # ---- validation gate: TRUE patching on the top-k |AtP| cells ----
    ranked = sorted(est.items(), key=lambda kv: abs(kv[1]), reverse=True)
    topk = ranked[: args.topk]
    val_atp, val_true, val_cells = [], [], []
    for (L, pos), a in topk:
        vec = corrupt_dev[L][pos]
        td = true_patch_delta(lm.model, clean_forward, metric, L, pos, vec, m_clean)
        val_atp.append(a)
        val_true.append(td)
        val_cells.append({"layer": L, "pos": int(pos), "atp": a, "true_delta": td})

    p_r = pearson(val_atp, val_true)
    s_r = spearman(val_atp, val_true)
    trustworthy = bool(np.isfinite(p_r) and np.isfinite(s_r)
                       and min(p_r, s_r) >= args.min_corr)

    return {
        "model": args.model,
        "meta": lm.meta(),
        "pair": pair,
        "readout": args.readout,
        "split": args.split,
        "metric": args.metric,
        "m_clean": m_clean,
        "layers": layer_idxs,
        "alignment": diag,
        "clean_sid": clean_row["sid"],
        "corrupt_sid": corrupt_row["sid"],
        "topk": args.topk,
        "min_corr": args.min_corr,
        "pearson_atp_vs_true": p_r,
        "spearman_atp_vs_true": s_r,
        "trustworthy": trustworthy,
        "validation_cells": val_cells,
        # full map: list of {layer,pos,atp} so downstream can render layer x position
        "atp_map": [{"layer": L, "pos": int(pos), "atp": a}
                    for (L, pos), a in ranked],
        "positions": positions,
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bench", required=True, help="fixed-pair bench JSON")
    ap.add_argument("--model", default=dc.PRIMARY_MODEL)
    ap.add_argument("--reps-dir", default="",
                    help="accepted for CLI parity with the sweep scripts; AtP recomputes "
                         "activations on the fly and does not read it")
    ap.add_argument("--topk", type=int, default=40,
                    help="number of highest-|AtP| cells validated by true patching")
    ap.add_argument("--out", required=True, help="output directory")
    ap.add_argument("--readout", default="one_word")
    ap.add_argument("--split", default="dev")
    ap.add_argument("--metric", default="logit_diff", choices=["logit_diff", "p_concept"])
    ap.add_argument("--layers", default="", help="comma ints; empty => all below readout")
    ap.add_argument("--min-corr", type=float, default=0.7,
                    help="AtP is reported trustworthy only if min(pearson,spearman) >= this")
    ap.add_argument("--dtype", default="bfloat16", choices=["bfloat16", "float16", "float32"])
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    dc.set_seed(args.seed)
    os.makedirs(args.out, exist_ok=True)
    lm = dc.load_model(args.model, dtype=getattr(torch, args.dtype))
    bench = json.load(open(args.bench))

    result = run(lm, bench, args)

    with open(os.path.join(args.out, "atp_results.json"), "w") as f:
        json.dump(result, f, indent=2)
    # console: numbers only, no prompt text
    print(f"[atp] pair={result['pair']['codeword']}->{result['pair']['concept']} "
          f"metric={args.metric} m_clean={result['m_clean']:.3f} "
          f"n_pos={result['alignment']['n_positions']} "
          f"topk={args.topk} pearson={result['pearson_atp_vs_true']:.3f} "
          f"spearman={result['spearman_atp_vs_true']:.3f} "
          f"trustworthy={result['trustworthy']}")
    print(f"[atp] -> {args.out}")


if __name__ == "__main__":
    main()
