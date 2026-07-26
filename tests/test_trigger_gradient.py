"""
F2 — tests for the real discrete REINFORCE trigger gradient
(`scripts/reinforce_objective/trigger_gradient.py`).

These tests exercise the GCG one-hot embedding gradient with a TINY mock:
  * a small random embedding matrix E  [V, d];
  * a differentiable stub model whose logits are a fixed linear map of the input
    embeddings (`logits = inputs_embeds @ W`), so the whole path
    onehot -> trigger_embeds -> logits -> logprob is differentiable.

They assert (matching the F2 task spec):
  (a) the returned gradient is finite and shape [trigger_len, vocab];
  (b) for a 2-response toy where response A has higher reward, `-grad` points
      toward trigger tokens that increase A's teacher-forced logprob (GCG sign);
  (c) advantages are DETACHED — no grad leaks into the reward tensors;
  (d) the empty-response guard returns a finite (non-NaN) gradient.

torch is required for autograd. `/usr/bin/python3` here has pytest but NO torch,
so pytest cleanly SKIPS via `importorskip`; run the real numeric check with a
torch-enabled interpreter, e.g.:
    TROPT/.venv/bin/python3 tests/test_trigger_gradient.py
(the `__main__` block below runs every test without needing pytest installed).
"""

import sys
from pathlib import Path

try:
    import pytest
except ModuleNotFoundError:  # standalone run on a torch-only venv (no pytest)
    pytest = None

if pytest is not None:
    torch = pytest.importorskip("torch")  # skip whole module if torch is absent
else:
    import torch  # standalone: torch must be present or this file is not run

_REPO_ROOT = Path(__file__).resolve().parent.parent
for p in (_REPO_ROOT, _REPO_ROOT / "scripts"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from reinforce_objective.trigger_gradient import (  # noqa: E402
    reinforce_trigger_gradient,
    topk_candidate_tokens,
)


# ---------------------------------------------------------------------------
# Tiny differentiable mock: embedding matrix + linear-logits stub model
# ---------------------------------------------------------------------------

VOCAB = 8
DMODEL = 6


class LinearStubModel:
    """A minimal `EmbeddingGradModel`: logits = inputs_embeds @ W (differentiable)."""

    def __init__(self, seed: int = 0):
        g = torch.Generator().manual_seed(seed)
        self._E = torch.randn(VOCAB, DMODEL, generator=g, dtype=torch.float64)
        self._W = torch.randn(DMODEL, VOCAB, generator=g, dtype=torch.float64)

    def embedding_matrix(self):
        return self._E

    def forward_logits(self, inputs_embeds):  # [1, T, d] -> [1, T, V]
        return inputs_embeds @ self._W

    # test-only helper: true teacher-forced logprob of a single-token response
    # when the trigger is the single token `trig_tok` (forward only, no grad).
    def logprob_single(self, trig_tok: int, resp_tok: int) -> float:
        trig_embed = self._E[trig_tok]                 # [d]
        logits = trig_embed @ self._W                  # [V]  (predicts next token)
        lp = torch.log_softmax(logits, dim=-1)[resp_tok]
        return float(lp)


def _base_case():
    """Trigger = 1 token; responses A,B each a single distinct token; A higher reward."""
    model = LinearStubModel(seed=1)
    prefix_ids: list[int] = []
    trigger_ids = [0]
    suffix_ids: list[int] = []
    tok_A, tok_B = 3, 5
    responses_ids = [[tok_A], [tok_B]]
    rewards = [1.0, 0.0]  # response A above baseline
    return model, prefix_ids, trigger_ids, suffix_ids, responses_ids, rewards, tok_A, tok_B


# ---------------------------------------------------------------------------
# (a) finite + correct shape
# ---------------------------------------------------------------------------

def test_grad_shape_and_finite():
    model, pre, trig, suf, resp, rew, *_ = _base_case()
    res = reinforce_trigger_gradient(model, pre, trig, suf, resp, rew)
    assert tuple(res.grad.shape) == (len(trig), VOCAB)
    assert torch.isfinite(res.grad).all()
    assert torch.isfinite(res.surrogate_loss).all()


def test_grad_shape_multi_token_trigger():
    model = LinearStubModel(seed=2)
    trig = [1, 4, 2]
    res = reinforce_trigger_gradient(
        model, [7], trig, [6], [[3, 1], [5]], [0.9, 0.1]
    )
    assert tuple(res.grad.shape) == (3, VOCAB)
    assert torch.isfinite(res.grad).all()


# ---------------------------------------------------------------------------
# (b) GCG sign: -grad points toward tokens that raise the high-reward response
# ---------------------------------------------------------------------------

def test_sign_toward_high_reward_response():
    model, pre, trig, suf, resp, rew, tok_A, tok_B = _base_case()
    res = reinforce_trigger_gradient(model, pre, trig, suf, resp, rew)

    neg_grad = -res.grad[0]  # per-token score at the single trigger position
    best_tok = int(neg_grad.argmax())   # GCG picks top-k of -grad
    worst_tok = int(neg_grad.argmin())

    # The surrogate L = (A_A*CE_A + A_B*CE_B)/2 with A_A=+1, A_B=-1 pulls TOWARDS A
    # and AWAY from B. So the trigger token favoured by -grad must, when actually
    # substituted, yield a higher (logprob_A - logprob_B) than the disfavoured one.
    def margin(t):
        return model.logprob_single(t, tok_A) - model.logprob_single(t, tok_B)

    assert margin(best_tok) > margin(worst_tok)

    # And it must actually reduce the true surrogate L relative to the worst token
    # (first-order GCG selection must not be anti-correlated with the true loss).
    def true_L(t):
        ce_A = -model.logprob_single(t, tok_A)
        ce_B = -model.logprob_single(t, tok_B)
        return (1.0 * ce_A + (-1.0) * ce_B) / 2.0

    assert true_L(best_tok) < true_L(worst_tok)

    # topk helper returns the same best token first.
    top = topk_candidate_tokens(res.grad, k=VOCAB)
    assert int(top[0, 0]) == best_tok


def test_advantages_sign_labels():
    model, pre, trig, suf, resp, rew, *_ = _base_case()
    res = reinforce_trigger_gradient(model, pre, trig, suf, resp, rew)
    # RLOO K=2, rewards [1,0] -> advantages [+1, -1].
    assert res.advantages[0] > 0 > res.advantages[1]


# ---------------------------------------------------------------------------
# (c) advantages detached — no grad leak into the reward
# ---------------------------------------------------------------------------

def test_rewards_receive_no_gradient():
    model, pre, trig, suf, resp, _rew, *_ = _base_case()
    # Pass rewards as grad-requiring tensors; the function must float()/detach them.
    r0 = torch.tensor(1.0, dtype=torch.float64, requires_grad=True)
    r1 = torch.tensor(0.0, dtype=torch.float64, requires_grad=True)
    res = reinforce_trigger_gradient(model, pre, trig, suf, resp, [r0, r1])
    assert torch.isfinite(res.grad).all()
    # No backward path reached the reward tensors.
    assert r0.grad is None and r1.grad is None


# ---------------------------------------------------------------------------
# (d) empty-response guard (F4): no NaN
# ---------------------------------------------------------------------------

def test_empty_response_guard():
    model = LinearStubModel(seed=3)
    # response 0 is empty; response 1 is a normal single token.
    res = reinforce_trigger_gradient(
        model, [], [2], [], [[], [4]], [1.0, 0.0], reduction="mean"
    )
    assert tuple(res.grad.shape) == (1, VOCAB)
    assert torch.isfinite(res.grad).all()
    assert res.log["n_empty"] == 1
    # empty response contributes CE 0.0 exactly (not NaN).
    assert res.per_response_ce[0] == 0.0


def test_all_empty_responses_finite():
    model = LinearStubModel(seed=4)
    res = reinforce_trigger_gradient(model, [], [1], [], [[], []], [1.0, 0.0])
    assert tuple(res.grad.shape) == (1, VOCAB)
    assert torch.isfinite(res.grad).all()
    # both empty -> grad is all-zero (no logprob path), still finite.
    assert torch.count_nonzero(res.grad) == 0


# ---------------------------------------------------------------------------
# standalone runner (works without pytest installed; used on the torch venv)
# ---------------------------------------------------------------------------

def _run_all() -> int:
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    passed = failed = 0
    for t in tests:
        try:
            t()
            passed += 1
            print(f"PASS {t.__name__}")
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"FAIL {t.__name__}: {type(e).__name__}: {e}")
    print(f"\n{passed} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(_run_all())
