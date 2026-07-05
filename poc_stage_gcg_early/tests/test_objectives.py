"""
Tests for objectives.py.

All tests are CPU-only and use toy tensors.
Verifies:
  - task_loss matches GCG opt_utils formula
  - repr_loss is 0 when candidate == reference
  - repr_loss gradient w.r.t. candidate embedding is non-zero
  - kl_loss is 0 for identical distributions
  - composite_loss returns all components
  - regularization_loss returns 0 by default
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
import torch
import torch.nn.functional as F

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from poc_stage_gcg_early.objectives import (
    composite_loss,
    kl_loss,
    regularization_loss,
    repr_loss,
    task_loss,
)


# ---------------------------------------------------------------------------
# task_loss
# ---------------------------------------------------------------------------

class TestTaskLoss:

    def test_returns_scalar_for_single_example(self):
        vocab = 10
        seq_len = 6
        target_len = 3
        logits = torch.randn(seq_len, vocab)
        ids = torch.randint(0, vocab, (seq_len,))
        loss_slice = slice(2, 5)
        target_slice = slice(3, 6)
        result = task_loss(logits, ids, loss_slice, target_slice)
        assert result.shape == (), f"Expected scalar, got {result.shape}"
        assert result.item() >= 0.0

    def test_returns_batch_for_batched_input(self):
        vocab = 10
        seq_len = 6
        batch = 4
        logits = torch.randn(batch, seq_len, vocab)
        ids = torch.randint(0, vocab, (batch, seq_len))
        result = task_loss(logits, ids, slice(2, 5), slice(3, 6))
        assert result.shape == (batch,)

    def test_matches_gcg_formula(self):
        """Verify task_loss matches the GCG target_loss formula numerically."""
        import torch.nn as nn
        vocab = 8
        seq_len = 5
        target_start = 2
        target_stop = 5
        target_slice = slice(target_start, target_stop)
        loss_slice = slice(target_start - 1, target_stop - 1)

        torch.manual_seed(0)
        logits = torch.randn(seq_len, vocab)
        ids = torch.randint(0, vocab, (seq_len,))

        # Our implementation
        our_loss = task_loss(logits, ids, loss_slice, target_slice)

        # GCG formula (from opt_utils.target_loss)
        crit = nn.CrossEntropyLoss(reduction="none")
        gcg_loss = crit(
            logits.unsqueeze(0)[:, loss_slice, :].transpose(1, 2),
            ids.unsqueeze(0)[:, target_slice],
        ).mean(dim=-1).squeeze(0)

        assert torch.allclose(our_loss, gcg_loss, atol=1e-5), (
            f"task_loss mismatch: ours={our_loss.item():.6f}, gcg={gcg_loss.item():.6f}"
        )

    def test_zero_loss_for_correct_prediction(self):
        """With perfect logits, loss should be near zero.

        loss_slice logit[i] predicts target_slice token[i] (GCG shifted convention).
        logit at loss_slice position i must be one-hot at target[target_slice.start + i].
        """
        vocab = 4
        seq_len = 4
        target = torch.tensor([0, 1, 2, 3])
        target_slice = slice(1, 4)   # target tokens: [1, 2, 3]
        loss_slice = slice(0, 3)     # logit positions: 0, 1, 2

        # logits[0] should predict target[1]=1, logits[1]→target[2]=2, logits[2]→target[3]=3
        next_targets = target[target_slice]  # [1, 2, 3]
        logits = torch.zeros(seq_len, vocab)
        for i, t in enumerate(next_targets.tolist()):
            logits[loss_slice.start + i, t] = 10.0  # high logit at correct token

        result = task_loss(logits, target, loss_slice, target_slice)
        assert result.item() < 0.01, f"Expected near-zero loss, got {result.item()}"


# ---------------------------------------------------------------------------
# repr_loss
# ---------------------------------------------------------------------------

class TestReprLoss:

    def _make_hs(self, layers, positions, d_model=8, seed=0):
        torch.manual_seed(seed)
        return {
            layer: {pos: torch.randn(d_model) for pos in positions}
            for layer in layers
        }

    def test_zero_when_identical(self):
        hs = self._make_hs([0, 1], [0, 1, 2])
        loss = repr_loss(hs, hs, layers=[0, 1], positions=[0, 1, 2], metric="cosine")
        assert loss.item() < 1e-5, f"Expected 0 for identical hs, got {loss.item()}"

    def test_zero_l2_when_identical(self):
        hs = self._make_hs([0], [0])
        loss = repr_loss(hs, hs, layers=[0], positions=[0], metric="l2")
        assert loss.item() < 1e-5

    def test_nonzero_for_different_hs(self):
        cand = self._make_hs([0], [0], seed=1)
        ref = self._make_hs([0], [0], seed=2)
        loss = repr_loss(cand, ref, layers=[0], positions=[0], metric="cosine")
        assert loss.item() > 0.0

    def test_gradient_nonzero(self):
        """Gradient of repr_loss w.r.t. candidate embedding must be non-zero."""
        d_model = 8
        ref_vec = torch.randn(d_model)
        cand_vec = torch.randn(d_model, requires_grad=True)

        cand_hs = {0: {0: cand_vec}}
        ref_hs = {0: {0: ref_vec.detach()}}

        loss = repr_loss(cand_hs, ref_hs, layers=[0], positions=[0], metric="cosine")
        loss.backward()
        assert cand_vec.grad is not None
        assert cand_vec.grad.abs().sum().item() > 0.0, "Gradient is zero"

    def test_whitened_l2_requires_flag(self):
        hs = self._make_hs([0], [0])
        with pytest.raises(ValueError, match="experimental"):
            repr_loss(hs, hs, layers=[0], positions=[0], metric="whitened_l2", whitened=False)

    def test_per_layer_weights(self):
        hs_cand = self._make_hs([0, 1], [0], seed=3)
        hs_ref = self._make_hs([0, 1], [0], seed=4)
        loss_eq = repr_loss(hs_cand, hs_ref, layers=[0, 1], positions=[0],
                            metric="cosine", per_layer_weights=[1.0, 1.0])
        loss_w = repr_loss(hs_cand, hs_ref, layers=[0, 1], positions=[0],
                           metric="cosine", per_layer_weights=[2.0, 0.0])
        # When layer 1 has weight 0, it should not contribute
        assert loss_eq.item() != loss_w.item()

    def test_missing_positions_skipped(self):
        hs = {0: {0: torch.randn(8)}}  # only position 0
        loss = repr_loss(hs, hs, layers=[0], positions=[0, 5, 10])  # 5 and 10 missing
        assert loss.item() < 1e-5  # should still be ~0 since position 0 is identical

    def test_wrong_per_layer_weights_length(self):
        hs = self._make_hs([0, 1], [0])
        with pytest.raises(ValueError, match="per_layer_weights length"):
            repr_loss(hs, hs, layers=[0, 1], positions=[0], per_layer_weights=[1.0])


# ---------------------------------------------------------------------------
# kl_loss
# ---------------------------------------------------------------------------

class TestKLLoss:

    def test_zero_for_identical_distributions(self):
        seq_len = 5
        vocab = 10
        logits = torch.randn(seq_len, vocab)
        loss = kl_loss(logits, logits, positions=[1, 2, 3])
        assert loss.item() < 1e-5, f"Expected 0 for identical distributions, got {loss.item()}"

    def test_nonzero_for_different_distributions(self):
        torch.manual_seed(42)
        seq_len = 5
        vocab = 10
        cand_logits = torch.randn(seq_len, vocab)
        ref_logits = torch.randn(seq_len, vocab)
        loss = kl_loss(cand_logits, ref_logits, positions=[1, 2])
        assert loss.item() > 0.0

    def test_nonnegative(self):
        torch.manual_seed(0)
        seq_len = 4
        vocab = 8
        loss = kl_loss(
            torch.randn(seq_len, vocab),
            torch.randn(seq_len, vocab),
            positions=[0, 1, 2, 3],
        )
        assert loss.item() >= 0.0

    def test_topk_vocab_smaller_than_full(self):
        torch.manual_seed(1)
        seq_len = 3
        vocab = 20
        cand = torch.randn(seq_len, vocab)
        ref = torch.randn(seq_len, vocab)
        loss_full = kl_loss(cand, ref, positions=[0, 1], topk_vocab=None)
        loss_topk = kl_loss(cand, ref, positions=[0, 1], topk_vocab=5)
        # Both should be non-negative; they will differ in value
        assert loss_full.item() >= 0.0
        assert loss_topk.item() >= 0.0

    def test_out_of_range_positions_skipped(self):
        logits = torch.randn(3, 8)
        loss = kl_loss(logits, logits, positions=[10, 20])  # out of range
        assert loss.item() == 0.0  # no valid positions → 0


# ---------------------------------------------------------------------------
# regularization_loss
# ---------------------------------------------------------------------------

class TestRegularizationLoss:

    def test_returns_zero_by_default(self):
        suffix_ids = torch.tensor([1, 2, 3, 4])
        loss = regularization_loss(suffix_ids)
        assert loss.item() == 0.0

    def test_disallowed_tokens(self):
        suffix_ids = torch.tensor([1, 2, 3, 4])
        disallowed = torch.tensor([2, 3])  # 2 tokens are disallowed
        loss = regularization_loss(suffix_ids, disallowed_tokens=disallowed)
        assert loss.item() == 2.0

    def test_edit_penalty(self):
        suffix_ids = torch.tensor([1, 2, 3, 4])
        prev_ids = torch.tensor([1, 9, 9, 4])  # 2 positions differ
        loss = regularization_loss(
            suffix_ids, edit_penalty_weight=1.0, prev_suffix_ids=prev_ids
        )
        assert loss.item() == 2.0


# ---------------------------------------------------------------------------
# composite_loss
# ---------------------------------------------------------------------------

class TestCompositeLoss:

    def test_all_components_present(self):
        vocab = 8
        seq_len = 6
        logits = torch.randn(seq_len, vocab)
        ids = torch.randint(0, vocab, (seq_len,))
        result = composite_loss(
            logits=logits,
            ids=ids,
            loss_slice=slice(2, 5),
            target_slice=slice(3, 6),
        )
        assert "task_loss" in result
        assert "repr_loss" in result
        assert "kl_loss" in result
        assert "reg_loss" in result
        assert "total_loss" in result

    def test_task_only_total_equals_task(self):
        """When lambda_repr=0 and lambda_kl=0, total_loss == task_loss."""
        vocab = 8
        seq_len = 6
        logits = torch.randn(seq_len, vocab)
        ids = torch.randint(0, vocab, (seq_len,))
        result = composite_loss(
            logits=logits, ids=ids,
            loss_slice=slice(2, 5), target_slice=slice(3, 6),
            lambda_repr=0.0, lambda_kl=0.0,
        )
        assert torch.allclose(result["total_loss"], result["task_loss"], atol=1e-6)
        assert result["repr_loss"].item() == 0.0
        assert result["kl_loss"].item() == 0.0
