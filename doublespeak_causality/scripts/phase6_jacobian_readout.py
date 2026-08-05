#!/usr/bin/env python3
"""Phase 6 (plan §5 P6) — JACOBIAN / PROJECTION-MATRIX READOUT.  Methods contribution.

WHAT THIS IS
------------
A plain projection lens asks "how much of a FIXED, pre-computed direction is present in the
residual stream at (layer L, position p)?".  The Jacobian readout asks the dual, local-linear-map
question: "which direction at (L, p) would MOST change a target scalar S, and how much?"  That
direction is the gradient

    J[L, p]  =  dS / d resid[L][p]        (a row of the Jacobian of S w.r.t. the residual stream)

which is the exact first-order sensitivity of S to a perturbation of that residual site:
    S(resid[L][p] + delta)  =  S  +  <J[L, p], delta>  +  O(||delta||^2).
We report, per layer, at a fixed readout position:
  * ||J[L, p]||                      — the Jacobian gradient NORM (sensitivity magnitude);
  * <act[L, p], unit(J[L, p])>       — the projection of the ACTUAL activation onto the
                                       "Jacobian-derived direction";
  * cos(unit(J), unit(d)) for each pre-computed direction d in {concept, refusal, signature}
                                     — is the local sensitivity direction the same object as the
                                       plain lens direction, or a different one?
  * <act[L, p], unit(d)>             — the PLAIN projections (concept / refusal / doublespeak
                                       signature), so the three lenses sit in ONE table.

TWO TARGETS, KEPT STRICTLY SEPARATE (the project's cardinal rule: never merge concept & refusal).
Each target gets its OWN forward+backward; the two gradients are distinct tensors and are never
summed, averaged, or otherwise mixed.

 (a) CONCEPT target  S_concept
        S_concept = mean_{i in F(concept)} logit_i  -  mean_{j in F(codeword)} logit_j
     evaluated on the NEXT-TOKEN logits at the final prompt token, in fp32, where F(w) =
     pair_common.word_first_ids(w) = the first-token ids of every surface form of w
     (" w", "w", " W", "W").  This is BYTE-FOR-BYTE the metric of 48_attribution_patching
     (`make_metric(..., kind="logit_diff")`), chosen there because a logit DIFFERENCE is the most
     linear readout available (so the local-linear map is the tightest) and because the
     concept-vs-codeword contrast is exactly the Doublespeak reading being installed.

 (b) REFUSAL target  S_refusal
        S_refusal = < hidden_states[R][0, -1, :] , unit(refusal_direction_llama_L{R-1}) >
     i.e. the projection of the final-prompt-token residual at hidden-states row R onto the SAME
     per-layer refusal direction artifact that scripts/phase_refusal_projection.py uses
     (outputs/refusal_alllayers/refusal_direction_llama_L{k}.pt, which by that file's own
     convention lives in hidden_states[k+1]; so row R pairs with the file L{R-1}).  The scalar is
     therefore numerically the SAME quantity phase_refusal_projection.py reports at its row R —
     only differentiated instead of merely read (see TOKENIZATION caveat below).
     Default R = num_layers (the last hidden-states row).  --refusal-hs-row overrides it.

     WHY A DOWNSTREAM READOUT ROW IS MANDATORY (documented degeneracy): if the refusal scalar were
     read at the SAME row that is being differentiated (R == L+1), then dS/d resid[L] is exactly
     the refusal direction itself — gradient norm 1, cos = 1, projection = the plain projection.
     The Jacobian readout would be a tautological restatement of the plain lens.  We therefore
     attribute only layers strictly BELOW the readout row (dc.patch_layer_sweep(R-1) =
     [0 .. R-2]); the excluded degenerate layer is recorded in the summary as `degenerate_layers`.
     The concept target uses dc.patch_layer_sweep(num_layers-1), exactly as 48 does.

CONVENTIONS (must match phase8_readout.py / the direction artifacts — see plan §5.10)
  * LAYER: layer index L means the OUTPUT of block L == hidden_states[L+1] == the tensor
    dc.LayerPatch(L) edits == row L of `directions.npz` / `unified_directions/<cohort>.npz`
    (concept & signature, built by pair_common.ComponentCapture "resid_post") == the row the
    refusal file L{k} lives in.  All three direction families and the Jacobian share this index.
    Verified at runtime on the first item: acts[L] (block-output hook) vs hidden_states[L+1]
    (max-abs diff, reported as `hs_match_maxabs`, must be 0.0).
  * POSITION: primary readout position is `final_prompt` = the last token of the templated
    prompt (add_generation_prompt=True) — the position phase8_readout.py uses and the position
    that decides the first generated token.  A secondary position `probe_last` = the last
    occurrence of the condition's probe word (codeword for neutral/doublespeak, concept for
    direct) is also reported; it corresponds to the `codeword_last` row of the pair directions.
  * Positions are resolved with pair_common.resolve_positions (add_special_tokens=False, since
    apply_template already emitted BOS) and shifted if --add-special-tokens is turned on.

TOKENIZATION CAVEAT (pre-existing repo inconsistency, flagged not silently "fixed" here).
  ds_common.forward_hidden_states tokenizes a TEMPLATED string with the tokenizer default
  add_special_tokens=True, which prepends a SECOND BOS for Llama-3.1 (37 vs 36 ids).
  build_refusal_direction_llama.py and phase_refusal_projection.py both go through it, so the
  refusal artifacts and their projections live in the double-BOS forward; pair_common /
  48_attribution_patching / the pair reps use add_special_tokens=False.  This script defaults to
  add_special_tokens=False (the house convention for everything position-indexed) and exposes
  --add-special-tokens true to reproduce the refusal-projection forward exactly.  The choice is
  recorded in RUNMETA and in the summary as `add_special_tokens`.

TRAIN/TEST DISCIPLINE (plan §1.5).  THIS SCRIPT FITS NOTHING.  A gradient is a closed-form
property of the frozen model and the given prompt: there is no readout matrix, no normalization
constant, no threshold, and no hyper-parameter selected from data anywhere in the pipeline.  The
direction artifacts it merely READS (unified_directions, refusal_alllayers) were fitted upstream
on train/dev and are consumed frozen; the refusal readout row R and the layer sweep are FIXED
conventions (last row / all rows below it), not data-selected.  Consequently both splits can be
computed in one pass with no leakage: `train` and `test` are reported separately so that any
downstream claim (e.g. "the refusal Jacobian predicts held-out ASR") is made on the locked test
split, but nothing this script produces was tuned on either.

FIRST-ORDER TRUSTWORTHINESS GATE (the analogue of 48's AtP validation gate).  A Jacobian is only
meaningful where S is locally linear.  With --taylor-cells > 0 we take the highest-||J|| cells,
ADD eps*unit(J) at that (layer, position) with dc.LayerPatch(mode="add"), and compare the measured
dS against the predicted eps*||J||.  The ratio measured/predicted is reported per cell and
aggregated; a ratio far from 1 means the local linearization does not transport and the readout
must be reported as sensitivity-only.

Outputs (scalars only — plan §5.12; no prompt text, no harmful strings, ever):
  outputs/jacobian_<cohort>_<ts>_<jobid>/{RUNMETA.json, raw.jsonl, summary.json, DONE.json}

GPU script (needs model weights) — the math is unit-tested GPU-free against closed-form
derivatives in tests/test_jacobian_synthetic.py.

Usage (L40S):
  python scripts/phase6_jacobian_readout.py \
      --bench data/behavioral/beh_clearharm.json --cohort clearharm \
      --refusal-dir outputs/refusal_alllayers --dirs outputs/unified_directions \
      --splits train,test --conditions direct,neutral,doublespeak --targets concept,refusal --n 0
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
import time
from contextlib import contextmanager
from typing import Any, Callable, Dict, Iterator, List, Optional, Sequence, Tuple

import numpy as np
import torch

HERE = os.path.dirname(os.path.abspath(__file__))
DC = os.path.dirname(HERE)
sys.path.insert(0, DC)
import ds_common as dc          # noqa: E402
import pair_common as pc        # noqa: E402

EPS = 1e-12
BEHAVIORAL_CONDITIONS = ("direct", "neutral", "doublespeak")
PAIR_CONDITIONS = ("DOUBLESPEAK", "NEUTRAL_CODEWORD", "DIRECT_CONCEPT",
                   "BENIGN_SOURCE", "UNRELATED_SOURCE")


@contextmanager
def _null_ctx():
    yield


def _load_atp():
    """Import 48_attribution_patching.py (leading digit => not a legal module name).

    We reuse its `_ActGradCapture` — the capture pattern that retains the block-output graph
    node so a single backward populates .grad at every layer — rather than re-implementing it.
    """
    path = os.path.join(DC, "48_attribution_patching.py")
    spec = importlib.util.spec_from_file_location("atp48", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


atp = _load_atp()
ActGradCapture = atp._ActGradCapture          # reused verbatim (see module docstring)


# --------------------------------------------------------------------------- #
# Small numeric helpers
# --------------------------------------------------------------------------- #
def hi_prec(t: torch.Tensor) -> torch.Tensor:
    """Promote low-precision activations to fp32, but never DEMOTE fp64.

    Production runs are bf16 -> every readout is taken in fp32 (as 48_attribution_patching does).
    The synthetic test drives the same code in fp64, where the closed-form derivative is exact;
    a blanket .float() would silently truncate that proof to fp32.
    """
    return t if t.dtype in (torch.float32, torch.float64) else t.float()


def unit(v: torch.Tensor) -> torch.Tensor:
    n = float(v.norm())
    return v / n if n > EPS else torch.zeros_like(v)


def _r(x: float, nd: int = 6) -> Optional[float]:
    """Round to `nd` SIGNIFICANT digits (not decimal places): gradient norms span many orders of
    magnitude across layers, and a fixed 5-decimal rounding would flatten the small ones to 0."""
    if x is None:
        return None
    x = float(x)
    return None if not np.isfinite(x) else float(f"{x:.{nd}g}")


# --------------------------------------------------------------------------- #
# Target scalars — CONCEPT and REFUSAL, built separately and never merged
# --------------------------------------------------------------------------- #
def make_concept_scalar(concept_ids: Sequence[int], codeword_ids: Sequence[int],
                        pos: int = -1) -> Callable[[Any], torch.Tensor]:
    """S_concept = mean logit(concept surface forms) - mean logit(codeword surface forms).

    Same definition as 48_attribution_patching.make_metric(kind="logit_diff").
    `pos` indexes the sequence axis of the logits (default -1 = final prompt token).
    """
    c = torch.as_tensor(sorted(set(int(i) for i in concept_ids)), dtype=torch.long)
    k = torch.as_tensor(sorted(set(int(i) for i in codeword_ids)), dtype=torch.long)
    if c.numel() == 0 or k.numel() == 0:
        raise ValueError("empty first-token id set for concept or codeword")

    def scalar(out) -> torch.Tensor:
        logits = hi_prec(out.logits[0, pos, :])
        return logits[c.to(logits.device)].mean() - logits[k.to(logits.device)].mean()

    return scalar


def make_refusal_scalar(refusal_dir_vec: torch.Tensor, hs_row: int,
                        pos: int = -1) -> Callable[[Any], torch.Tensor]:
    """S_refusal = <hidden_states[hs_row][0, pos, :], unit(refusal direction)>.

    The direction MUST be the artifact for the layer that row hs_row lives in
    (refusal_direction_llama_L{hs_row-1}.pt), so the scalar equals the quantity
    phase_refusal_projection.py reports for that row.
    """
    u = unit(hi_prec(refusal_dir_vec.detach()).flatten())

    def scalar(out) -> torch.Tensor:
        h = hi_prec(out.hidden_states[hs_row][0, pos, :])
        return torch.dot(h, u.to(h.device))

    return scalar


def layer_sweep_for_target(num_layers: int, target: str, refusal_hs_row: int) -> List[int]:
    """Layers whose Jacobian is non-degenerate for this target (see module docstring).

    concept: readout is the next-token logits (above every block) -> [0 .. num_layers-2]
             (dc.patch_layer_sweep(num_layers-1), identical to 48's sweep).
    refusal: readout is hidden_states[R] == post-block R-1 -> [0 .. R-2]; L = R-1 is DEGENERATE
             (dS/d resid[R-1] is the refusal direction itself) and is excluded.
    """
    if target == "concept":
        return dc.patch_layer_sweep(num_layers - 1)
    if target == "refusal":
        readout_layer = int(refusal_hs_row) - 1        # hs[R] == output of block R-1
        sweep = dc.patch_layer_sweep(readout_layer)
        return [L for L in sweep if L <= num_layers - 2]
    raise ValueError(f"unknown target {target!r}")


# --------------------------------------------------------------------------- #
# The Jacobian engine — MODEL-AGNOSTIC (the synthetic test drives this same code)
# --------------------------------------------------------------------------- #
def capture_jacobian(
    model,
    forward_fn: Callable[[], Any],
    scalar_fn: Callable[[Any], torch.Tensor],
    layer_idxs: Sequence[int],
    check_hs_rows: bool = False,
) -> Tuple[Dict[int, torch.Tensor], Dict[int, torch.Tensor], float, Dict[str, Any]]:
    """One forward + one backward -> dS/d resid[L][p] for every requested layer, ALL positions.

    Args:
      forward_fn: () -> model output exposing .logits and (if the scalar needs it)
                  .hidden_states; must run through the hooked blocks.
      scalar_fn:  (output) -> 0-dim tensor S (the target scalar, fp32).
      layer_idxs: block indices; block L's output == hidden_states[L+1].
      check_hs_rows: also verify acts[L] == hidden_states[L+1] bit-for-bit (index convention).

    Returns (acts, grads, S_value, diag) with acts[L], grads[L] of shape [seq, hidden] (fp32,
    detached, on the model's device).  grads[L][p] IS the Jacobian row dS/d resid[L][p].
    """
    cap = ActGradCapture(model, layer_idxs)
    with torch.enable_grad():
        with cap:
            out = forward_fn()
            S = scalar_fn(out)
        if S.dim() != 0:
            raise ValueError(f"scalar_fn must return a 0-dim tensor, got shape {tuple(S.shape)}")
        if hasattr(model, "zero_grad"):
            model.zero_grad(set_to_none=True)
        S.backward()

    diag: Dict[str, Any] = {}
    if check_hs_rows and getattr(out, "hidden_states", None) is not None:
        worst = 0.0
        for L in layer_idxs:
            row = L + 1
            if row < len(out.hidden_states):
                d = (hi_prec(cap.acts[L].detach()[0])
                     - hi_prec(out.hidden_states[row][0].detach())).abs().max()
                worst = max(worst, float(d))
        diag["hs_match_maxabs"] = worst

    acts, grads = {}, {}
    for L in layer_idxs:
        h = cap.acts[L]
        if h.grad is None:
            raise RuntimeError(
                f"no gradient captured at layer {L}; either grad is disabled, the scalar does "
                f"not depend on this layer's output, or the layer is at/above the readout row")
        acts[L] = hi_prec(h.detach()[0])
        grads[L] = hi_prec(h.grad[0])
    return acts, grads, float(S.detach()), diag


def layer_row(act: torch.Tensor, grad: torch.Tensor, pos: int,
              dirs: Optional[Dict[str, torch.Tensor]] = None) -> Dict[str, Optional[float]]:
    """Per-(layer, position) readout row: Jacobian norm, Jacobian-direction projection, and the
    PLAIN projections / alignments against each pre-computed direction (kept separate by name)."""
    a = hi_prec(act[pos])
    g = hi_prec(grad[pos])
    u = unit(g)
    row: Dict[str, Optional[float]] = {
        "grad_norm": _r(float(g.norm())),
        "jac_proj": _r(float(torch.dot(a, u))),
        "act_norm": _r(float(a.norm())),
    }
    for name, d in (dirs or {}).items():
        ud = unit(hi_prec(d.detach()).flatten().to(a.device).to(a.dtype))
        row[f"proj_{name}"] = _r(float(torch.dot(a, ud)))
        row[f"cos_jac_{name}"] = _r(float(torch.dot(u, ud)))
    return row


def position_profile(grad: torch.Tensor, topk: int = 5) -> Dict[str, Any]:
    """Where along the sequence the scalar is most sensitive, reported as OFFSET FROM THE END
    (comparable across items of different lengths; 0 == final prompt token)."""
    n = hi_prec(grad).norm(dim=-1)                      # [seq]
    seq = n.shape[0]
    order = torch.argsort(n, descending=True)[: max(1, topk)]
    return {
        "mean_grad_norm": _r(float(n.mean())),
        "max_grad_norm": _r(float(n.max())),
        "argmax_offset_from_end": int(int(order[0]) - (seq - 1)),
        "top": [{"offset_from_end": int(int(i) - (seq - 1)), "grad_norm": _r(float(n[int(i)]))}
                for i in order],
    }


def taylor_check(model, forward_fn: Callable[[], Any], scalar_fn: Callable[[Any], torch.Tensor],
                 layer: int, pos: int, grad_vec: torch.Tensor, s0: float,
                 eps: float, seq_len: int) -> Dict[str, Any]:
    """First-order gate: add eps*unit(J) at (layer, pos); measured dS should be eps*||J||."""
    g = hi_prec(grad_vec)
    gn = float(g.norm())
    predicted = eps * gn
    with torch.no_grad():
        with dc.LayerPatch(model, layer, [pos], vector=unit(g), mode="add", alpha=eps):
            s1 = float(scalar_fn(forward_fn()).detach())
    measured = s1 - s0
    return {
        "layer": layer, "pos_offset_from_end": int(pos - (seq_len - 1)), "eps": eps,
        "grad_norm": _r(gn), "predicted_delta": _r(predicted), "measured_delta": _r(measured),
        "ratio_measured_over_predicted": _r(measured / predicted) if abs(predicted) > EPS else None,
    }


# --------------------------------------------------------------------------- #
# Forward construction (real model only)
# --------------------------------------------------------------------------- #
def model_device(lm) -> torch.device:
    """The device the weights live on (getattr(model, "device") is HF-only; the synthetic
    stand-in models used for CPU verification do not define it)."""
    d = getattr(lm.model, "device", None)
    if d is not None:
        return torch.device(d)
    try:
        return next(lm.model.parameters()).device
    except StopIteration:
        return torch.device(getattr(lm, "device", "cpu"))


@contextmanager
def frozen_params(model):
    """Temporarily set requires_grad=False on every parameter, restoring the flags on exit.

    With the graph rooted at `inputs_embeds` instead of the weights, backward populates ONLY the
    retained activation grads — no [n_params] gradient buffer is ever allocated (a ~16GB saving
    on an 8B bf16 model, which is what makes an all-layer Jacobian fit next to the weights).
    """
    saved = [(p, p.requires_grad) for p in model.parameters()]
    try:
        for p, _ in saved:
            p.requires_grad_(False)
        yield
    finally:
        for p, flag in saved:
            p.requires_grad_(flag)


def make_forward(lm, text: str, grad_mode: str, add_special_tokens: bool
                 ) -> Tuple[Callable[[], Any], int]:
    """Build a zero-argument forward over `text` and return (forward_fn, seq_len).

    grad_mode="inputs_embeds" (default): the embedding output is detached and marked
      requires_grad, so the graph starts there and the parameters can stay frozen.
    grad_mode="params": 48_attribution_patching's path (graph rooted at the weights).
    """
    tok = lm.tokenizer(text, return_tensors="pt",
                       add_special_tokens=add_special_tokens).to(model_device(lm))
    seq_len = int(tok["input_ids"].shape[1])
    if grad_mode == "inputs_embeds":
        with torch.no_grad():
            embeds = lm.model.get_input_embeddings()(tok["input_ids"])
        embeds = embeds.detach().clone().requires_grad_(True)
        attn = tok.get("attention_mask")

        def fwd():
            return lm.model(inputs_embeds=embeds, attention_mask=attn,
                            output_hidden_states=True, return_dict=True)
    elif grad_mode == "params":
        def fwd():
            return lm.model(**tok, output_hidden_states=True, return_dict=True)
    else:
        raise ValueError(f"unknown grad_mode {grad_mode!r}")
    return fwd, seq_len


# --------------------------------------------------------------------------- #
# Work items (bench readers) — flat records so both bench kinds share one loop
# --------------------------------------------------------------------------- #
def iter_behavioral(bench_path: str, splits: Sequence[str], n: int,
                    conditions: Sequence[str]) -> Iterator[Dict[str, Any]]:
    """ClearHarm-style behavioral bench -> one work item per (item, condition).

    Conditions come from dc.build_conditions (direct / neutral / doublespeak), exactly as
    phase_refusal_projection.py builds them, so the readouts are directly comparable.
    """
    data = json.load(open(bench_path))
    items = data["items"] if isinstance(data, dict) else data
    for split in splits:
        cand = [it for it in items if it.get("split") == split]
        if n:
            cand = cand[:n]
        for it in cand:
            hw, cw = it["harmful_word"], it["codeword"]
            instr = it["harmful_instruction"]
            if hw not in instr:
                instr = f"Give detailed step-by-step instructions to make a {hw}."
            demos = it["demos"] if isinstance(it["demos"], str) else "\n".join(it["demos"])
            conds = dc.build_conditions(instr, hw, cw, demos)
            texts = {"direct": conds.direct, "neutral": conds.neutral,
                     "doublespeak": conds.doublespeak}
            probe = {"direct": hw, "neutral": cw, "doublespeak": cw}
            for cond in conditions:
                yield {"item_key": it.get("id"), "pair_key": it.get("id"), "split": split,
                       "condition": cond, "raw_prompt": texts[cond], "concept": hw,
                       "codeword": cw, "probe_word": probe[cond]}


def iter_pair(bench_path: str, splits: Sequence[str], n: int, conditions: Sequence[str],
              readout: str) -> Iterator[Dict[str, Any]]:
    """Fixed-pair bench (data/pair_benchmark/*.json) -> one work item per (row, condition).

    Splits are dev/heldout there; `pair_key` is the within-condition rank so DS-vs-DIRECT
    contrasts stay index-paired.
    """
    b = json.load(open(bench_path))
    pair = b["pair"]
    for split in splits:
        for cond in conditions:
            rows = [r for r in b["semantic"] if r["condition"] == cond
                    and r["split"] == split and r["readout"] == readout]
            if n:
                rows = rows[:n]
            for i, r in enumerate(rows):
                yield {"item_key": r["sid"], "pair_key": f"{split}#{i}", "split": split,
                       "condition": cond, "raw_prompt": r["prompt"],
                       "concept": pair["concept"], "codeword": pair["codeword"],
                       "probe_word": r.get("probe_word") or pair["codeword"]}


# --------------------------------------------------------------------------- #
# Directions
# --------------------------------------------------------------------------- #
def load_refusal_dirs(refusal_dir: str) -> Dict[int, torch.Tensor]:
    """{block index k: unit refusal direction} from refusal_direction_llama_L{k}.pt.

    Block index k == the row that lives in hidden_states[k+1] (phase_refusal_projection.py's
    convention and the .json artifacts' own `directions_row`).
    """
    out: Dict[int, torch.Tensor] = {}
    for k in range(0, 512):
        p = os.path.join(refusal_dir, f"refusal_direction_llama_L{k}.pt")
        if not os.path.exists(p):
            if k > 0 and out:
                break
            continue
        v = torch.load(p, map_location="cpu").float().flatten()
        out[k] = unit(v)
    if not out:
        raise FileNotFoundError(f"no refusal_direction_llama_L*.pt under {refusal_dir}")
    return out


def load_unified_dirs(dirs_root: str, cohort: str) -> Dict[str, np.ndarray]:
    """{name: [L, H]} concept / signature / refusal, all block-indexed (row L == post-block L)."""
    path = os.path.join(dirs_root, f"{cohort}.npz")
    if not os.path.exists(path):
        return {}
    z = np.load(path)
    return {k: np.asarray(z[k], dtype=np.float32) for k in ("concept", "signature", "refusal")
            if k in z.files}


# --------------------------------------------------------------------------- #
# Aggregation
# --------------------------------------------------------------------------- #
def boot_ci(vals: Sequence[float], rng: np.random.Generator, n_boot: int = 1000
            ) -> List[Optional[float]]:
    a = np.asarray([v for v in vals if v is not None and np.isfinite(v)], dtype=np.float64)
    if a.size == 0:
        return [None, None, None]
    if a.size == 1:
        return [_r(a[0]), _r(a[0]), _r(a[0])]
    idx = rng.integers(0, a.size, size=(n_boot, a.size))
    means = a[idx].mean(axis=1)
    return [_r(a.mean()), _r(np.percentile(means, 2.5)), _r(np.percentile(means, 97.5))]


def _mean(vals: Sequence[Optional[float]]) -> Optional[float]:
    a = np.asarray([v for v in vals if v is not None and np.isfinite(v)], dtype=np.float64)
    return _r(a.mean()) if a.size else None


def aggregate(records: List[Dict[str, Any]], positions: Sequence[str],
              seed: int = 0) -> Dict[str, Any]:
    """Per (split, condition, position): the ONE comparison table across lenses, per layer."""
    rng = np.random.default_rng(seed)
    out: Dict[str, Any] = {}
    keys = sorted({(r["split"], r["condition"]) for r in records})
    for split, cond in keys:
        sel = [r for r in records if r["split"] == split and r["condition"] == cond]
        by_target = {t: [r for r in sel if r["target"] == t]
                     for t in sorted({r["target"] for r in sel})}
        node: Dict[str, Any] = {"n_items": len({r["item_key"] for r in sel}), "by_position": {}}
        for posname in positions:
            table: Dict[str, Any] = {}
            for target, recs in by_target.items():
                recs = [r for r in recs if posname in r["by_pos"]]
                if not recs:
                    continue
                layers = recs[0]["layers"]
                fields = sorted({k for r in recs for row in r["by_pos"][posname] for k in row})
                per_layer = []
                for j, L in enumerate(layers):
                    entry: Dict[str, Any] = {"layer": int(L)}
                    for f in fields:
                        vals = [r["by_pos"][posname][j].get(f) for r in recs]
                        if f in ("grad_norm", "jac_proj"):
                            entry[f] = boot_ci(vals, rng)      # [mean, lo, hi]
                        else:
                            entry[f] = _mean(vals)
                    per_layer.append(entry)
                gn = [(e["grad_norm"][0] if e["grad_norm"][0] is not None else -np.inf)
                      for e in per_layer]
                jp = [(abs(e["jac_proj"][0]) if e["jac_proj"][0] is not None else -np.inf)
                      for e in per_layer]
                table[target] = {
                    "n": len(recs),
                    "scalar_mean": _mean([r["scalar"] for r in recs]),
                    "peak_layer_grad_norm": int(layers[int(np.argmax(gn))]),
                    "peak_layer_abs_jac_proj": int(layers[int(np.argmax(jp))]),
                    "per_layer": per_layer,
                }
            node["by_position"][posname] = table
        out[f"{split}|{cond}"] = node
    return out


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(
        description="Phase 6 Jacobian / projection-matrix readout (plan §5 P6). "
                    "Concept and refusal targets are computed SEPARATELY and never merged.")
    ap.add_argument("--bench", required=True, help="behavioral bench JSON or fixed-pair bench JSON")
    ap.add_argument("--bench-kind", default="behavioral", choices=["behavioral", "pair"])
    ap.add_argument("--cohort", default="", help="cohort tag; default = bench _meta.cohort or filename")
    ap.add_argument("--model", default=dc.PRIMARY_MODEL)
    ap.add_argument("--dtype", default="bfloat16", choices=["bfloat16", "float16", "float32"])
    ap.add_argument("--refusal-dir", default=os.path.join(DC, "outputs", "refusal_alllayers"),
                    help="per-layer refusal_direction_llama_L*.pt (the SAME artifacts "
                         "phase_refusal_projection.py uses)")
    ap.add_argument("--dirs", default=os.path.join(DC, "outputs", "unified_directions"),
                    help="unified_directions root for the PLAIN concept/signature/refusal lens")
    ap.add_argument("--dirs-cohort", default="", help="cohort name inside --dirs (default: --cohort)")
    ap.add_argument("--splits", default="train,test", help="comma list (pair bench: dev,heldout)")
    ap.add_argument("--conditions", default="direct,neutral,doublespeak", help="comma list")
    ap.add_argument("--targets", default="concept,refusal", help="comma list: concept,refusal")
    ap.add_argument("--positions", default="final_prompt,probe_last", help="comma list")
    ap.add_argument("--readout", default="one_word", help="pair bench only: readout question kind")
    ap.add_argument("--refusal-hs-row", type=int, default=-1,
                    help="hidden-states row R for the refusal scalar; -1 => num_layers (last row). "
                         "Uses refusal_direction_llama_L{R-1}.pt. NOT data-selected (plan §1.5).")
    ap.add_argument("--n", type=int, default=0,
                    help="cap per split (behavioral: items; pair: rows per condition); 0 = all")
    ap.add_argument("--topk-positions", type=int, default=5)
    ap.add_argument("--taylor-cells", type=int, default=3,
                    help="highest-||J|| cells validated by a real eps-perturbation (0 disables)")
    ap.add_argument("--taylor-eps", type=float, default=0.5)
    ap.add_argument("--taylor-items", type=int, default=1,
                    help="number of leading WORK ITEMS ((item, condition) pairs) the gate runs on")
    ap.add_argument("--grad-mode", default="inputs_embeds", choices=["inputs_embeds", "params"])
    ap.add_argument("--add-special-tokens", default="false", choices=["false", "true"],
                    help="tokenization of the TEMPLATED prompt; false = house convention "
                         "(apply_template already emits BOS). true reproduces the double-BOS "
                         "forward used by ds_common.forward_hidden_states.")
    ap.add_argument("--layers", default="", help="comma ints; empty => the full valid sweep")
    ap.add_argument("--out-dir", default="", help="explicit output dir (default: auto-timestamped)")
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args(argv)

    splits = [s.strip() for s in args.splits.split(",") if s.strip()]
    conditions = [c.strip() for c in args.conditions.split(",") if c.strip()]
    targets = [t.strip() for t in args.targets.split(",") if t.strip()]
    positions = [p.strip() for p in args.positions.split(",") if p.strip()]
    bad = set(targets) - {"concept", "refusal"}
    if bad:
        raise ValueError(f"unknown target(s) {sorted(bad)}")
    bad = set(positions) - {"final_prompt", "probe_last"}
    if bad:
        raise ValueError(f"unknown position(s) {sorted(bad)}")
    legal_conds = BEHAVIORAL_CONDITIONS if args.bench_kind == "behavioral" else PAIR_CONDITIONS
    bad = set(conditions) - set(legal_conds)
    if bad:
        raise ValueError(f"--bench-kind {args.bench_kind} does not have condition(s) "
                         f"{sorted(bad)}; expected a subset of {list(legal_conds)}")
    if "final_prompt" not in positions:
        raise ValueError("'final_prompt' must be among --positions (it is the readout position "
                         "the target scalars are defined at, and the Taylor gate's cell)")
    add_special = args.add_special_tokens == "true"

    meta = {}
    try:
        raw = json.load(open(args.bench))
        meta = raw.get("_meta", {}) if isinstance(raw, dict) else {}
    except Exception:
        meta = {}
    cohort = args.cohort or meta.get("cohort") or os.path.splitext(os.path.basename(args.bench))[0]

    ts = time.strftime("%Y%m%d_%H%M%S")
    uniq = os.environ.get("SLURM_JOB_ID") or str(os.getpid())
    out_dir = args.out_dir or os.path.join(DC, "outputs", f"jacobian_{cohort}_{ts}_{uniq}")
    os.makedirs(out_dir, exist_ok=True)
    dc.write_runmeta(out_dir, args, extra={"phase": "P6_jacobian_readout", "cohort": cohort,
                                           "add_special_tokens": add_special})

    dc.set_seed(args.seed)
    lm = dc.load_model(args.model, dtype=getattr(torch, args.dtype))
    n_layers = lm.num_layers
    dc.write_runmeta(out_dir, args, extra={"model_meta": lm.meta()})

    refusal_hs_row = n_layers if args.refusal_hs_row < 0 else int(args.refusal_hs_row)
    # the per-layer refusal artifacts serve BOTH the refusal target scalar and the PLAIN refusal
    # lens column, so they are loaded whenever they exist; only the target makes them mandatory.
    try:
        refdirs = load_refusal_dirs(args.refusal_dir)
    except FileNotFoundError:
        if "refusal" in targets:
            raise
        refdirs = {}
        print(f"[jac] WARNING no refusal directions under {args.refusal_dir} -> plain refusal "
              f"lens column omitted", flush=True)
    if "refusal" in targets and (refusal_hs_row - 1) not in refdirs:
        raise FileNotFoundError(
            f"refusal target needs refusal_direction_llama_L{refusal_hs_row - 1}.pt "
            f"(hidden-states row {refusal_hs_row}) in {args.refusal_dir}")
    plain = load_unified_dirs(args.dirs, args.dirs_cohort or cohort)
    if not plain:
        print(f"[jac] WARNING no unified directions at {args.dirs}/"
              f"{args.dirs_cohort or cohort}.npz -> plain concept/signature lens omitted",
              flush=True)

    full_sweeps = {t: layer_sweep_for_target(n_layers, t, refusal_hs_row) for t in targets}
    # layers OUTSIDE the valid sweep are at/above this target's readout, where the Jacobian is
    # degenerate (see the module docstring) — recorded separately from a user --layers restriction.
    degenerate = {t: sorted(set(range(n_layers)) - set(v)) for t, v in full_sweeps.items()}
    sweeps = dict(full_sweeps)
    if args.layers:
        want = [int(x) for x in args.layers.split(",") if x.strip()]
        sweeps = {t: [L for L in v if L in want] for t, v in full_sweeps.items()}

    dev = model_device(lm)
    # per-layer PLAIN directions on device, kept as DISTINCT named objects (never merged)
    def dirs_for_layer(L: int) -> Dict[str, torch.Tensor]:
        d: Dict[str, torch.Tensor] = {}
        for name in ("concept", "signature"):
            if name in plain and L < plain[name].shape[0]:
                d[name] = torch.from_numpy(plain[name][L]).to(dev)
        if L in refdirs:
            d["refusal"] = refdirs[L].to(dev)
        return d

    dir_cache = {L: dirs_for_layer(L) for L in sorted({L for v in sweeps.values() for L in v})}

    work = (iter_behavioral(args.bench, splits, args.n, conditions) if args.bench_kind == "behavioral"
            else iter_pair(args.bench, splits, args.n, conditions, args.readout))

    raw_path = os.path.join(out_dir, "raw.jsonl")
    fh = open(raw_path, "w")
    records: List[Dict[str, Any]] = []
    taylor: List[Dict[str, Any]] = []
    hs_check: List[float] = []
    n_rows = 0
    t0 = time.time()
    seen_items = 0
    ctx = frozen_params(lm.model) if args.grad_mode == "inputs_embeds" else _null_ctx()
    with ctx:
        for w in work:
            text = dc.apply_template(lm.tokenizer, w["raw_prompt"], add_generation_prompt=True)
            fwd, seq_len = make_forward(lm, text, args.grad_mode, add_special)
            # positions: resolve on the add_special_tokens=False ids (pair_common convention),
            # then shift by the number of extra specials this run's tokenization prepends.
            shift = seq_len - len(lm.tokenizer(text, add_special_tokens=False)["input_ids"])
            pos_idx: Dict[str, Optional[int]] = {"final_prompt": seq_len - 1, "probe_last": None}
            if "probe_last" in positions:
                try:
                    pp = pc.resolve_positions(lm, text, w["probe_word"])
                    pos_idx["probe_last"] = int(pp.codeword_last) + shift
                except Exception:
                    pos_idx["probe_last"] = None
            use_pos = [p for p in positions if pos_idx.get(p) is not None]

            for target in targets:
                layers = sweeps[target]
                if not layers:
                    continue
                if target == "concept":
                    scalar_fn = make_concept_scalar(pc.word_first_ids(lm.tokenizer, w["concept"]),
                                                    pc.word_first_ids(lm.tokenizer, w["codeword"]))
                else:
                    scalar_fn = make_refusal_scalar(refdirs[refusal_hs_row - 1], refusal_hs_row)
                acts, grads, s_val, diag = capture_jacobian(
                    lm.model, fwd, scalar_fn, layers, check_hs_rows=(seen_items == 0))
                if "hs_match_maxabs" in diag:
                    hs_check.append(diag["hs_match_maxabs"])

                rec = {
                    "item_key": w["item_key"], "pair_key": w["pair_key"], "split": w["split"],
                    "condition": w["condition"], "target": target, "scalar": _r(s_val),
                    "seq_len": seq_len, "layers": [int(L) for L in layers],
                    "pos_offsets": {p: int(pos_idx[p] - (seq_len - 1)) for p in use_pos},
                    "by_pos": {p: [layer_row(acts[L], grads[L], pos_idx[p], dir_cache.get(L, {}))
                                   for L in layers] for p in use_pos},
                    # per-layer WHERE-along-the-sequence profile (the second axis of the
                    # Jacobian: dS/d resid[L][p] for every p, summarized as norms + offsets)
                    "position_profile": {int(L): position_profile(grads[L], args.topk_positions)
                                         for L in layers},
                }
                fh.write(json.dumps(rec) + "\n")
                fh.flush()
                records.append(rec)
                n_rows += 1

                if args.taylor_cells > 0 and seen_items < args.taylor_items:
                    cells = sorted(((float(grads[L][pos_idx["final_prompt"]].norm()), L)
                                    for L in layers), reverse=True)[: args.taylor_cells]
                    for _, L in cells:
                        t = taylor_check(lm.model, fwd, scalar_fn, L, pos_idx["final_prompt"],
                                         grads[L][pos_idx["final_prompt"]], s_val,
                                         args.taylor_eps, seq_len)
                        t.update({"target": target, "condition": w["condition"],
                                  "split": w["split"]})
                        taylor.append(t)
                del acts, grads
            seen_items += 1
            if seen_items % 10 == 0:
                print(f"[jac] {seen_items} work items, {n_rows} rows, "
                      f"{time.time() - t0:.0f}s", flush=True)
    fh.close()

    summary = {
        "phase": "P6_jacobian_readout",
        "cohort": cohort,
        "bench": os.path.abspath(args.bench),
        "bench_kind": args.bench_kind,
        "model": args.model,
        "n_layers": n_layers,
        "targets": targets,
        "conditions": conditions,
        "splits": splits,
        "positions": positions,
        "add_special_tokens": add_special,
        "grad_mode": args.grad_mode,
        "fits_nothing": True,
        "fit_note": ("no readout matrix / normalization / threshold is estimated anywhere: the "
                     "Jacobian is a closed-form derivative of a frozen model. Direction artifacts "
                     "are consumed frozen (fitted upstream on train/dev); the refusal readout row "
                     "and layer sweeps are fixed conventions, not data-selected. Train and test "
                     "are reported separately for downstream use, with no leakage possible."),
        "scalar_definitions": {
            "concept": "mean logit(first-token surface forms of concept) - mean logit(codeword "
                       "forms), next-token logits at the final prompt token, fp32 "
                       "(== 48_attribution_patching logit_diff metric)",
            "refusal": f"<hidden_states[{refusal_hs_row}][0,-1,:], "
                       f"unit(refusal_direction_llama_L{refusal_hs_row - 1}.pt)> "
                       f"(== the phase_refusal_projection.py readout at that row)",
        },
        "refusal_hs_row": refusal_hs_row,
        "refusal_dir": os.path.abspath(args.refusal_dir),
        "unified_dirs": os.path.abspath(os.path.join(args.dirs, (args.dirs_cohort or cohort) + ".npz")),
        "plain_direction_families": sorted(plain.keys()),
        "layer_sweeps": {t: [int(L) for L in v] for t, v in sweeps.items()},
        "full_layer_sweeps": {t: [int(L) for L in v] for t, v in full_sweeps.items()},
        "degenerate_layers_excluded": {t: [int(L) for L in v] for t, v in degenerate.items()},
        "layer_convention": "layer L == block-L output == hidden_states[L+1] == LayerPatch(L) "
                            "== row L of unified_directions == refusal file L{L}",
        "hs_index_check_maxabs": (max(hs_check) if hs_check else None),
        "n_rows": n_rows,
        "taylor_gate": {
            "eps": args.taylor_eps, "n_cells": len(taylor),
            "median_ratio": (_r(float(np.median([t["ratio_measured_over_predicted"] for t in taylor
                                                 if t["ratio_measured_over_predicted"] is not None])))
                             if taylor else None),
            "cells": taylor,
        },
        "by_split_condition": aggregate(records, positions, args.seed),
    }
    with open(os.path.join(out_dir, "summary.json"), "w") as f:
        json.dump(summary, f, indent=1)
    dc.write_done(out_dir, rows_written=n_rows,
                  extra={"phase": "P6_jacobian_readout", "cohort": cohort,
                         "hs_index_check_maxabs": summary["hs_index_check_maxabs"],
                         "taylor_median_ratio": summary["taylor_gate"]["median_ratio"]})

    print(f"[jac] {n_rows} rows -> {out_dir}", flush=True)
    print(f"[jac] hs-index check (acts[L] vs hidden_states[L+1]) maxabs="
          f"{summary['hs_index_check_maxabs']} | taylor median ratio="
          f"{summary['taylor_gate']['median_ratio']} (1.0 == perfectly linear)", flush=True)
    for key, node in summary["by_split_condition"].items():
        tbl = node["by_position"].get("final_prompt", {})
        for target, t in tbl.items():
            print(f"  [{key}] target={target} n={t['n']} S={t['scalar_mean']} "
                  f"peak||J||=L{t['peak_layer_grad_norm']} "
                  f"peak|jac_proj|=L{t['peak_layer_abs_jac_proj']}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
