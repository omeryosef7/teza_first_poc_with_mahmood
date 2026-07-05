"""
Differentiable objectives for Stage GCG-Early.

All losses return scalar tensors (or [batch] tensors where noted).
Batching across candidates happens in gcg_optimizer.py.

Loss functions:
  task_loss       — NLL of safe target continuation (identical to GCG baseline)
  repr_loss       — representation distance between candidate and reference activations
  kl_loss         — KL divergence between reference and candidate next-token distributions
  regularization_loss — optional suffix regularization (inactive by default)

The repr_loss and kl_loss objectives are the new scientific contribution.
task_loss replicates the GCG formula from opt_utils.target_loss.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

import torch
import torch.nn as nn
import torch.nn.functional as F


# ---------------------------------------------------------------------------
# Task loss (identical to GCG opt_utils.target_loss)
# ---------------------------------------------------------------------------

def task_loss(
    logits: torch.Tensor,
    ids: torch.Tensor,
    loss_slice: slice,
    target_slice: slice,
) -> torch.Tensor:
    """
    Cross-entropy loss over the target token positions.

    Implements the GCG loss_slice convention:
      loss_slice = slice(target_start - 1, target_stop - 1)
    so that logit at position i predicts token at position i+1.

    Args:
        logits:       [batch, seq_len, vocab] or [seq_len, vocab]
        ids:          [batch, seq_len] or [seq_len]
        loss_slice:   logit positions (target_start-1 : target_stop-1)
        target_slice: token positions (target_start : target_stop)

    Returns:
        [batch] tensor of per-example losses (or scalar if batch dim absent).
    """
    if logits.dim() == 2:
        logits = logits.unsqueeze(0)
        ids = ids.unsqueeze(0)
        squeeze = True
    else:
        squeeze = False

    crit = nn.CrossEntropyLoss(reduction="none")
    # logits[:, loss_slice, :] has shape [batch, target_len, vocab]
    # ids[:, target_slice] has shape [batch, target_len]
    loss = crit(
        logits[:, loss_slice, :].transpose(1, 2),  # [batch, vocab, target_len]
        ids[:, target_slice],                       # [batch, target_len]
    )  # [batch, target_len]
    result = loss.mean(dim=-1)  # [batch]
    return result.squeeze(0) if squeeze else result


# ---------------------------------------------------------------------------
# Representation loss
# ---------------------------------------------------------------------------

def _normalize(x: torch.Tensor, eps: float = 1e-8) -> torch.Tensor:
    """L2-normalize along the last dimension."""
    return x / (x.norm(dim=-1, keepdim=True) + eps)


def repr_loss(
    candidate_hs: Dict[int, Dict[int, torch.Tensor]],
    reference_hs: Dict[int, Dict[int, torch.Tensor]],
    layers: List[int],
    positions: List[int],
    metric: str = "cosine",
    per_layer_weights: Optional[List[float]] = None,
    per_token_weights: Optional[List[float]] = None,
    whitened: bool = False,
) -> torch.Tensor:
    """
    Representation distance between candidate and reference hidden states.

    Args:
        candidate_hs:  {layer: {pos: Tensor[d_model]}} — from current suffix forward pass
        reference_hs:  {layer: {pos: Tensor[d_model]}} — from reference cache (detached)
        layers:        which layers to compare
        positions:     which token positions to compare
        metric:        "cosine" | "l2" | "whitened_l2" (experimental, requires whitened=True)
        per_layer_weights: optional per-layer weight list (len == len(layers))
        per_token_weights: optional per-position weight list (len == len(positions))
        whitened:      must be True to activate "whitened_l2" (safety gate for experimental path)

    Returns:
        scalar tensor (weighted mean over all (layer, position) pairs)
    """
    if metric == "whitened_l2" and not whitened:
        raise ValueError(
            "metric='whitened_l2' requires whitened=True to be explicitly set. "
            "This is an experimental feature."
        )

    if per_layer_weights is not None and len(per_layer_weights) != len(layers):
        raise ValueError(
            f"per_layer_weights length {len(per_layer_weights)} != len(layers) {len(layers)}"
        )
    if per_token_weights is not None and len(per_token_weights) != len(positions):
        raise ValueError(
            f"per_token_weights length {len(per_token_weights)} != len(positions) {len(positions)}"
        )

    total = torch.tensor(0.0)
    weight_sum = 0.0

    for li, layer_idx in enumerate(layers):
        lw = per_layer_weights[li] if per_layer_weights else 1.0
        cand_layer = candidate_hs.get(layer_idx, {})
        ref_layer = reference_hs.get(layer_idx, {})

        for pi, pos in enumerate(positions):
            pw = per_token_weights[pi] if per_token_weights else 1.0
            w = lw * pw

            cand_vec = cand_layer.get(pos)
            ref_vec = ref_layer.get(pos)
            if cand_vec is None or ref_vec is None:
                continue

            # Move to same device/dtype
            ref_vec = ref_vec.to(dtype=cand_vec.dtype, device=cand_vec.device).detach()

            if metric == "cosine":
                dist = 1.0 - F.cosine_similarity(
                    cand_vec.unsqueeze(0), ref_vec.unsqueeze(0)
                ).squeeze()
            elif metric == "l2":
                dist = (_normalize(cand_vec) - _normalize(ref_vec)).norm()
            elif metric == "whitened_l2":
                # Experimental: whitening would require a pre-computed covariance.
                # For now, fall back to l2 with a warning logged by the caller.
                dist = (_normalize(cand_vec) - _normalize(ref_vec)).norm()
            else:
                raise ValueError(f"Unknown metric: {repr(metric)}. Use 'cosine' or 'l2'.")

            total = total + w * dist
            weight_sum += w

    if weight_sum == 0.0:
        return torch.tensor(0.0)
    return total / weight_sum


# ---------------------------------------------------------------------------
# Early-logit KL loss
# ---------------------------------------------------------------------------

def kl_loss(
    candidate_logits: torch.Tensor,
    reference_logits: torch.Tensor,
    positions: List[int],
    topk_vocab: Optional[int] = None,
) -> torch.Tensor:
    """
    KL divergence between reference and candidate next-token distributions
    at each of the specified positions.

    KL(reference || candidate) averaged over positions.

    Args:
        candidate_logits:  [seq_len, vocab] or [batch, seq_len, vocab]
        reference_logits:  [seq_len, vocab] (single reference)
        positions:         token positions at which to compute KL
        topk_vocab:        if set, compute KL only over the top-k tokens
                           by reference probability (memory-efficient).
                           None = exact KL over full vocabulary.

    Returns:
        scalar tensor
    """
    if candidate_logits.dim() == 3:
        # Batched: average over batch
        per_batch = torch.stack([
            kl_loss(candidate_logits[b], reference_logits, positions, topk_vocab)
            for b in range(candidate_logits.shape[0])
        ])
        return per_batch.mean()

    total = torch.tensor(0.0, device=candidate_logits.device)
    n_valid = 0

    ref_probs_full = F.softmax(reference_logits, dim=-1)  # [seq_len, vocab]

    for pos in positions:
        if pos >= candidate_logits.shape[0] or pos >= reference_logits.shape[0]:
            continue

        cand_logit = candidate_logits[pos]  # [vocab]
        ref_prob = ref_probs_full[pos]       # [vocab]

        if topk_vocab is not None:
            # Restrict to top-k tokens by reference probability
            _, topk_idx = ref_prob.topk(min(topk_vocab, ref_prob.shape[0]))
            cand_logit = cand_logit[topk_idx]
            ref_prob_topk = ref_prob[topk_idx]
            ref_prob_topk = ref_prob_topk / ref_prob_topk.sum()  # renormalize
            cand_log_prob = F.log_softmax(cand_logit, dim=-1)
            kl = F.kl_div(cand_log_prob, ref_prob_topk, reduction="sum")
        else:
            cand_log_prob = F.log_softmax(cand_logit, dim=-1)
            kl = F.kl_div(cand_log_prob, ref_prob, reduction="sum")

        total = total + kl
        n_valid += 1

    return total / n_valid if n_valid > 0 else torch.tensor(0.0)


# ---------------------------------------------------------------------------
# Regularization (inactive by default)
# ---------------------------------------------------------------------------

def regularization_loss(
    suffix_ids: torch.Tensor,
    disallowed_tokens: Optional[torch.Tensor] = None,
    printable_only: bool = False,
    edit_penalty_weight: float = 0.0,
    prev_suffix_ids: Optional[torch.Tensor] = None,
    tokenizer: Optional[Any] = None,
) -> torch.Tensor:
    """
    Optional suffix regularization. Returns 0.0 unless explicitly configured.

    Args:
        suffix_ids:           [suffix_len] current suffix token IDs
        disallowed_tokens:    optional mask tensor of token IDs to penalize
        printable_only:       if True, penalize non-printable-ASCII tokens
        edit_penalty_weight:  weight for edit distance penalty vs prev_suffix_ids
        prev_suffix_ids:      [suffix_len] previous suffix (for edit penalty)
        tokenizer:            needed for printable_only check

    Returns:
        scalar tensor (0.0 if no regularization is active)
    """
    loss = torch.tensor(0.0)

    if disallowed_tokens is not None and len(disallowed_tokens) > 0:
        mask = torch.isin(suffix_ids, disallowed_tokens.to(suffix_ids.device))
        loss = loss + mask.float().sum()

    if printable_only and tokenizer is not None:
        for tok_id in suffix_ids.tolist():
            decoded = tokenizer.decode([tok_id], skip_special_tokens=True)
            if not decoded.isprintable():
                loss = loss + torch.tensor(1.0)

    if edit_penalty_weight > 0.0 and prev_suffix_ids is not None:
        n_changed = (suffix_ids != prev_suffix_ids.to(suffix_ids.device)).float().sum()
        loss = loss + edit_penalty_weight * n_changed

    return loss


# ---------------------------------------------------------------------------
# Composite loss (used in gradient computation)
# ---------------------------------------------------------------------------

def composite_loss(
    logits: torch.Tensor,
    ids: torch.Tensor,
    loss_slice: slice,
    target_slice: slice,
    candidate_hs: Optional[Dict] = None,
    reference_hs: Optional[Dict] = None,
    candidate_logits_for_kl: Optional[torch.Tensor] = None,
    reference_logits_for_kl: Optional[torch.Tensor] = None,
    layers: Optional[List[int]] = None,
    repr_positions: Optional[List[int]] = None,
    kl_positions: Optional[List[int]] = None,
    lambda_repr: float = 0.0,
    lambda_kl: float = 0.0,
    repr_metric: str = "cosine",
    kl_topk_vocab: Optional[int] = None,
    suffix_ids: Optional[torch.Tensor] = None,
    prev_suffix_ids: Optional[torch.Tensor] = None,
    regularization_kwargs: Optional[dict] = None,
) -> dict:
    """
    Compute all objective components and return them as a dict.

    Returns:
        {
          "task_loss": scalar,
          "repr_loss": scalar,
          "kl_loss": scalar,
          "reg_loss": scalar,
          "total_loss": scalar,
        }
    """
    t_loss = task_loss(logits, ids, loss_slice, target_slice)

    r_loss = torch.tensor(0.0)
    if lambda_repr > 0.0 and candidate_hs is not None and reference_hs is not None:
        r_loss = repr_loss(
            candidate_hs, reference_hs,
            layers=layers or [],
            positions=repr_positions or [],
            metric=repr_metric,
        )

    k_loss = torch.tensor(0.0)
    if lambda_kl > 0.0 and candidate_logits_for_kl is not None and reference_logits_for_kl is not None:
        k_loss = kl_loss(
            candidate_logits_for_kl, reference_logits_for_kl,
            positions=kl_positions or repr_positions or [],
            topk_vocab=kl_topk_vocab,
        )

    reg_kwargs = regularization_kwargs or {}
    reg_loss_val = regularization_loss(
        suffix_ids=suffix_ids if suffix_ids is not None else torch.tensor([]),
        prev_suffix_ids=prev_suffix_ids,
        **reg_kwargs,
    )

    total = t_loss + lambda_repr * r_loss + lambda_kl * k_loss + reg_loss_val

    return {
        "task_loss": t_loss,
        "repr_loss": r_loss,
        "kl_loss": k_loss,
        "reg_loss": reg_loss_val,
        "total_loss": total,
    }
