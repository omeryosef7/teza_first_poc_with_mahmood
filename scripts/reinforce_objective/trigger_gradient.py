"""
F2 — Real discrete REINFORCE TRIGGER-GRADIENT (Sprint Plan §D4.5, REINFORCE-MAC).

WHAT THIS CLOSES
----------------
Review finding F2: `gpu_runner.teacher_forced_logprob` feeds INTEGER `input_ids`
to frozen params (grad-free) and `_main` never calls `.backward()`, so no trigger
gradient is ever produced — REINFORCE-MAC could only VALIDATE signs (via the
pure-Python `reinforce.py` estimator), never OPTIMIZE end-to-end. This module adds
the missing piece: the gradient of the REINFORCE surrogate loss w.r.t. a
DIFFERENTIABLE one-hot representation of the trigger tokens, i.e. the exact
GCG/GCGPlus token-selection signal, but weighted by RLOO advantages.

THE GCG ONE-HOT EMBEDDING TRICK (what we mirror, and why a local mirror)
----------------------------------------------------------------------
TROPT computes the token-selection gradient in
`TROPT/tropt/model/huggingface/base.py::compute_grad_from_tokens` (lines ~730-820):

    onehot = F.one_hot(trigger_ids, vocab).to(device, dtype)   # [t, V]
    onehot.requires_grad_()
    trigger_embeds = onehot @ embedding_matrix                 # [t, d]   (base.py:772)
    ... build model_input with trigger_embeds, forward, loss ...
    grad = torch.autograd.grad(loss, [onehot])[0]              # [t, V]   (base.py:816)

`GCGPlusOptimizer._sample_ids_from_grad` (gcgplus_optimizer.py:395-397) then takes
the top-k of `-grad` per position as candidate token swaps. We reuse that EXACT
construction (one-hot @ effective-embedding-matrix, autograd.grad w.r.t. the
one-hot, top-k of -grad = candidates).

WHY A LOCAL MIRROR AND NOT A DIRECT `compute_grad_from_tokens` CALL:
`compute_grad_from_tokens` is bound to (a) a SINGLE `BaseLoss` resolved against a
SINGLE target-prefill via the `InputsManager`, and (b) one candidate-trigger batch
sharing one target. REINFORCE-MAC instead needs K DIFFERENT sampled-response
continuations, each teacher-forced and weighted by its OWN detached advantage
A_i, all sharing ONE trigger one-hot so gradients accumulate into a single
`[t, V]` signal. That is a weighted SUM of K per-response CEs, which the
single-loss/single-target `compute_grad_from_tokens` API cannot express without
editing upstream (forbidden by the hard rules). So we mirror only the ~5 load-
bearing lines of the one-hot construction (cited above) locally, and keep the rest
(teacher-forcing, advantage weighting, backward) here. See
`docs/REINFORCE_TROPT_IMPLEMENTATION.md` §"trigger-gradient (F2 closed)".

IMPORT STAYS TORCH-FREE
-----------------------
Every torch touch is lazy (inside a function body), matching `gpu_runner.py` /
`proxy_ce_rerank.py`. Importing this module pulls in NO torch, so it is importable
under `/usr/bin/python3` where the pure-Python estimator tests run. The core
gradient itself is exercised with a tiny mock embedding matrix + a differentiable
stub model in `tests/test_trigger_gradient.py` (run with a torch-enabled
interpreter; skipped under a torch-free one via `importorskip`).

MATH (sign-consistent with GCG, derived from `reinforce.py`)
------------------------------------------------------------
For K sampled responses y_1..y_K with rewards r_i, RLOO advantages A_i = r_i - b_i
(from `reinforce.reinforce_advantages`, DETACHED — a stop-gradient constant), and
per-response teacher-forced CE_i = -log pi(y_i | prompt-with-trigger):

    L = (1/K) * sum_i  sg(A_i) * CE_i        (the surrogate to MINIMIZE)

`L.backward()` populates `onehot.grad` of shape [trigger_len, vocab]. Because
A_i > 0 (above-baseline reward) contributes +A_i*CE_i, minimizing L LOWERS CE_i
(pulls TOWARDS y_i); A_i < 0 pushes AWAY. Hence the top-k of `-onehot.grad` are the
trigger-token swaps that most reduce L == most raise expected reward — identical in
sign/consumption to GCG's `-trigger_grad` top-k. No gradient flows through the
reward or the sampling (A_i is a stop-gradient float).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional, Sequence

from .reinforce import reinforce_advantages


# ---------------------------------------------------------------------------
# Differentiable model adapter (duck-typed; real GPU model + test stub implement)
# ---------------------------------------------------------------------------

class EmbeddingGradModel:  # documentation-only protocol (no torch at import)
    """Contract a model must satisfy to produce the trigger one-hot gradient.

    Only these two hooks are used, which is what keeps the core CPU-mockable:

    embedding_matrix() -> Tensor [vocab, d_model]
        The EFFECTIVE embedding matrix (mirrors `base.py::embedding_matrix`: for
        models that scale/enrich embeddings, e.g. Gemma3, this must be the matrix
        such that `onehot @ M` equals the real per-token embedding). A constant
        w.r.t. autograd here — the grad variable is the one-hot, not this matrix.

    forward_logits(inputs_embeds) -> Tensor [1, T, vocab]
        A differentiable forward pass over INPUT EMBEDDINGS (not ids), returning
        next-token logits. On the real model this is `model(inputs_embeds=...).logits`
        under grad; the stub returns a differentiable function of `inputs_embeds`.
    """

    def embedding_matrix(self):  # pragma: no cover - protocol
        raise NotImplementedError

    def forward_logits(self, inputs_embeds):  # pragma: no cover - protocol
        raise NotImplementedError


# ---------------------------------------------------------------------------
# Result container
# ---------------------------------------------------------------------------

@dataclass
class TriggerGradientResult:
    """The REINFORCE trigger one-hot gradient plus everything to audit it.

    grad: torch tensor [trigger_len, vocab] = dL/d(onehot). `-grad` top-k per
        position are the GCGPlus Stage-1 PROPOSAL candidate swaps.
    surrogate_loss: the scalar torch L that was backpropagated.
    advantages: the DETACHED RLOO advantages A_i used as CE weights (plain floats).
    per_response_ce: CE_i = -logprob_i (plain floats, for logging/selection ties).
    log: config + provenance (reduction, K, baseline, empty-response count).
    """

    grad: Any
    surrogate_loss: Any
    advantages: list[float]
    per_response_ce: list[float]
    log: dict = field(default_factory=dict)


# ---------------------------------------------------------------------------
# One-hot construction (LOCAL MIRROR of base.py:733-772) — torch lazy
# ---------------------------------------------------------------------------

def build_trigger_onehot(trigger_ids, vocab_size, *, device, dtype):
    """Differentiable one-hot [trigger_len, vocab] with `requires_grad_()`.

    Mirrors `TROPT/tropt/model/huggingface/base.py:733-758`:
        onehot = F.one_hot(ids, vocab).to(device, dtype); onehot.requires_grad_()
    """
    import torch  # noqa: PLC0415  (lazy: module import stays torch-free)
    import torch.nn.functional as F  # noqa: PLC0415

    ids = torch.as_tensor(trigger_ids, device=device, dtype=torch.long).view(-1)
    onehot = F.one_hot(ids, num_classes=vocab_size).to(device=device, dtype=dtype)
    onehot.requires_grad_()
    return onehot


def _embed_ids(embedding_matrix, ids, *, device):
    """Non-differentiable context/response embeddings via matrix index-select."""
    import torch  # noqa: PLC0415

    idx = torch.as_tensor(ids, device=device, dtype=torch.long).view(-1)
    if idx.numel() == 0:
        d = embedding_matrix.shape[1]
        return embedding_matrix.new_zeros((0, d))
    return embedding_matrix.index_select(0, idx)


# ---------------------------------------------------------------------------
# Per-response teacher-forced CE that CARRIES grad to the trigger one-hot
# ---------------------------------------------------------------------------

def _teacher_forced_ce(
    model: "EmbeddingGradModel",
    embedding_matrix,
    prefix_embeds,
    trigger_embeds,
    suffix_embeds,
    response_ids,
    *,
    reduction: str,
    device,
):
    """CE_i = -logprob(response | prefix+trigger+suffix), differentiable in trigger.

    Builds `inputs_embeds = [prefix, trigger, suffix, response]` (the trigger part
    carries grad), forwards once, and scores ONLY the response tokens by teacher
    forcing (predict token t from position t-1). Returns (ce_tensor, n_resp_tokens).

    F4 empty-response guard: a zero-length response contributes CE = 0.0 (a real
    torch zero, no NaN) — both 'sum' and 'mean' are safe.
    """
    import torch  # noqa: PLC0415
    import torch.nn.functional as F  # noqa: PLC0415

    resp_embeds = _embed_ids(embedding_matrix, response_ids, device=device)
    n_resp = resp_embeds.shape[0]
    if n_resp == 0:
        # F4: empty response -> CE 0.0 (differentiable-safe zero, not NaN).
        # Keep it connected to the graph so summation dtype/shape is consistent.
        return trigger_embeds.sum() * 0.0, 0

    full = torch.cat([prefix_embeds, trigger_embeds, suffix_embeds, resp_embeds], dim=0)
    logits = model.forward_logits(full.unsqueeze(0))  # [1, T, V]
    if logits.dim() == 2:  # tolerate a stub that returns [T, V]
        logits = logits.unsqueeze(0)

    n_ctx = prefix_embeds.shape[0] + trigger_embeds.shape[0] + suffix_embeds.shape[0]
    # Predict response token t from the hidden state at position (n_ctx + t - 1).
    shift_logits = logits[:, n_ctx - 1 : n_ctx - 1 + n_resp, :]  # [1, n_resp, V]
    labels = torch.as_tensor(response_ids, device=device, dtype=torch.long).view(-1)
    logprobs = F.log_softmax(shift_logits, dim=-1)
    tok_lp = logprobs.gather(-1, labels.view(1, -1, 1)).squeeze(-1).squeeze(0)  # [n_resp]
    total_lp = tok_lp.sum()
    logprob = total_lp / n_resp if reduction == "mean" else total_lp
    return -logprob, n_resp  # CE_i = -logprob


# ---------------------------------------------------------------------------
# The F2 deliverable: the real discrete REINFORCE trigger gradient
# ---------------------------------------------------------------------------

def reinforce_trigger_gradient(
    model: "EmbeddingGradModel",
    prefix_ids: Sequence[int],
    trigger_ids: Sequence[int],
    suffix_ids: Sequence[int],
    responses_ids: Sequence[Sequence[int]],
    rewards: Sequence[float],
    *,
    reduction: str = "sum",
    baseline: str = "rloo",
    baseline_const: float = 0.0,
) -> TriggerGradientResult:
    """Gradient of the REINFORCE surrogate w.r.t. the trigger one-hot [t, V].

    Args:
      model: an `EmbeddingGradModel` (embedding_matrix + forward_logits).
      prefix_ids / trigger_ids / suffix_ids: token ids of the prompt split around
        the trigger span (prefix before, suffix after — either may be empty). The
        trigger span is the ONLY part carrying gradient.
      responses_ids: K token-id sequences (the sampled free generations, FIXED).
      rewards: K behavioral rewards r_i (from `scripts/jailbreak_rewards.py`).
      reduction: 'sum' (total logprob, REINFORCE default) or 'mean' (per-token).
      baseline / baseline_const: forwarded to `reinforce.reinforce_advantages`.

    Returns a `TriggerGradientResult`. The gradient is sign-consistent with GCG:
    top-k of `-result.grad` per position are the candidate token swaps that raise
    expected reward (GCGPlus Stage-1 proposal). Advantages are DETACHED floats — no
    gradient flows through the reward or the sampling (true REINFORCE).
    """
    if reduction not in ("sum", "mean"):
        raise ValueError(f"reduction must be 'sum' or 'mean', got {reduction!r}")
    K = len(responses_ids)
    if K != len(rewards):
        raise ValueError(f"length mismatch: {K} responses vs {len(rewards)} rewards")

    import torch  # noqa: PLC0415

    embedding_matrix = model.embedding_matrix()
    device = embedding_matrix.device
    dtype = embedding_matrix.dtype
    vocab_size = int(embedding_matrix.shape[0])

    # --- One-hot trigger (LOCAL MIRROR of GCG; the grad variable) ---
    onehot = build_trigger_onehot(trigger_ids, vocab_size, device=device, dtype=dtype)
    trigger_embeds = onehot @ embedding_matrix  # base.py:772  [t, d]

    prefix_embeds = _embed_ids(embedding_matrix, prefix_ids, device=device)
    suffix_embeds = _embed_ids(embedding_matrix, suffix_ids, device=device)

    # --- DETACHED RLOO advantages (stop-gradient; pure-Python floats) ---
    # Explicitly .detach() any tensor reward before float() so NO grad path can
    # ever reach the reward / sampling (this is what makes the objective REINFORCE
    # and not a differentiable-reward objective).
    def _as_float(r: Any) -> float:
        det = getattr(r, "detach", None)
        return float(det()) if callable(det) else float(r)

    adv = reinforce_advantages(
        [_as_float(r) for r in rewards], baseline=baseline, baseline_const=baseline_const
    )

    # --- K teacher-forced CEs, weighted by detached advantages, summed ---
    per_response_ce: list[float] = []
    n_empty = 0
    surrogate = None
    for i in range(K):
        ce_i, n_resp = _teacher_forced_ce(
            model, embedding_matrix, prefix_embeds, trigger_embeds, suffix_embeds,
            responses_ids[i], reduction=reduction, device=device,
        )
        if n_resp == 0:
            n_empty += 1
        per_response_ce.append(float(ce_i.detach().item()))
        term = float(adv[i]) * ce_i  # sg(A_i) * CE_i  (A_i already a float)
        surrogate = term if surrogate is None else surrogate + term

    if surrogate is None:  # K == 0
        grad = torch.zeros((0, vocab_size), device=device, dtype=dtype)
        return TriggerGradientResult(
            grad=grad, surrogate_loss=torch.zeros((), device=device, dtype=dtype),
            advantages=[], per_response_ce=[],
            log={"K": 0, "reduction": reduction, "baseline": baseline, "n_empty": 0},
        )

    surrogate = surrogate / K  # L = (1/K) sum_i sg(A_i) * CE_i

    # --- Backward -> the trigger one-hot gradient (the REINFORCE selection signal) ---
    grad = torch.autograd.grad(
        outputs=surrogate, inputs=[onehot],
        grad_outputs=torch.ones_like(surrogate),
    )[0]  # [t, V]  (mirrors base.py:816)

    return TriggerGradientResult(
        grad=grad,
        surrogate_loss=surrogate.detach(),
        advantages=[float(a) for a in adv],
        per_response_ce=per_response_ce,
        log={
            "K": K,
            "reduction": reduction,
            "baseline": baseline,
            "baseline_const": baseline_const,
            "n_empty": n_empty,
            "reinforce_mac": True,
        },
    )


def topk_candidate_tokens(grad, k: int):
    """GCGPlus Stage-1 proposal helper: top-k of `-grad` per position.

    Mirrors `gcgplus_optimizer.py:395-397` (`(-trigger_grad).topk(...)`). Returns a
    LongTensor [trigger_len, k] of candidate token ids per position. This is the
    only place the sign convention matters: candidates that most REDUCE the
    surrogate (raise expected reward) rank first.
    """
    import torch  # noqa: PLC0415  (unused import guard for torch-free static import)

    return (-grad).topk(k, dim=-1).indices


__all__ = [
    "EmbeddingGradModel",
    "TriggerGradientResult",
    "build_trigger_onehot",
    "reinforce_trigger_gradient",
    "topk_candidate_tokens",
]
