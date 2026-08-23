"""
GPU-free synthetic tests for pair_common.AllQueryAttentionKnockout — the knockout that must
stay live during autoregressive DECODING (Phase 2 of the d_surface next phase).

THE POINT OF THIS FILE. The pre-existing `AttentionKnockout` addresses query rows by ABSOLUTE
prompt position, so on a KV-cached decode step (mask shape [1, H, 1, kv_len], i.e.
`am.shape[2] == 1`) its guard `if qp >= am.shape[2]: continue` skips every query position and the
knockout silently switches itself off for the whole generation. That is correct for the
teacher-forced readout it was built for and fatal for a behavioural experiment: the run still
emits rows, still reports n_edges_cut, still exits 0, and produces "the knockout does not change
ASR" — a statement about a hook, not about the model.

Per the repo's standing rule (every guard ships with a test that FAILS the pre-fix code),
`test_old_class_is_dead_at_decode_THIS_IS_THE_REGRESSION_GUARD` asserts the OLD class's failure
directly. If someone ever "fixes" AttentionKnockout in place, that test goes red and tells them
they have just re-scored G1/G3.

Run:  python -m pytest doublespeak_causality/tests/test_allquery_attnknockout.py -q
"""
import os
import sys

import pytest
import torch
import torch.nn as nn

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from pair_common import AllQueryAttentionKnockout, AttentionKnockout  # noqa: E402


class ToyAttn(nn.Module):
    def __init__(self):
        super().__init__()
        self.seen = None

    def forward(self, hidden_states, attention_mask=None, **kw):
        self.seen = None if attention_mask is None else attention_mask.clone()
        return (hidden_states, None)


class ToyBlock(nn.Module):
    def __init__(self):
        super().__init__()
        self.self_attn = ToyAttn()

    def forward(self, x, attention_mask=None):
        a, _ = self.self_attn(x, attention_mask=attention_mask)
        return (x + a, None)


class ToyCfg:
    def __init__(self, n_heads, hidden):
        self.num_attention_heads = n_heads
        self.num_key_value_heads = max(1, n_heads // 2)
        self.hidden_size = hidden


class ToyModel(nn.Module):
    def __init__(self, n_layers=3, n_heads=4, hidden=8):
        super().__init__()
        self.config = ToyCfg(n_heads, hidden)
        self.model = nn.Module()
        self.model.layers = nn.ModuleList(ToyBlock() for _ in range(n_layers))

    def forward(self, x, attention_mask=None):
        for blk in self.model.layers:
            x, _ = blk(x, attention_mask=attention_mask)
        return x


def _prefill_mask(seq, heads=1, dtype=torch.float32):
    """eager-style 4-D additive mask at prefill: [1, heads, seq, seq]."""
    m = torch.zeros(1, heads, seq, seq, dtype=dtype)
    minv = torch.finfo(dtype).min
    for q in range(seq):
        for k in range(q + 1, seq):
            m[:, :, q, k] = minv
    return m


def _decode_mask(past, heads=1, dtype=torch.float32):
    """eager-style 4-D additive mask at a decode step: [1, heads, 1, past+1], all allowed."""
    return torch.zeros(1, heads, 1, past + 1, dtype=dtype)


def _run(model, mask, seq, hidden=8):
    x = torch.zeros(1, seq, hidden)
    model(x, attention_mask=mask)
    return [blk.self_attn.seen for blk in model.model.layers]


MIN = torch.finfo(torch.float32).min


# --------------------------------------------------------------------------- #
# THE REGRESSION GUARD — the old class must be dead at decode
# --------------------------------------------------------------------------- #
def test_old_class_is_dead_at_decode_THIS_IS_THE_REGRESSION_GUARD():
    """AttentionKnockout applies NOTHING on a decode step. This is why the new class exists.

    If this test ever fails, someone has changed AttentionKnockout's semantics in place — which
    silently re-scores every committed G1/G3 artifact. Fix the caller, not this test.
    """
    model = ToyModel()
    past = 6
    mask = _decode_mask(past)
    # query positions expressed the way surgical_knockout.py expresses them: absolute
    with AttentionKnockout(model, [0], query_positions=[past], blocked_keys=[2, 3]):
        seen = _run(model, mask, seq=1)
    assert seen[0] is not None
    assert not (seen[0] == MIN).any(), (
        "AttentionKnockout unexpectedly edited a decode-step mask; its documented behaviour is "
        "to skip it (tests/test_attnknockout_synthetic.py:185-192).")


# --------------------------------------------------------------------------- #
# The new class: alive at decode
# --------------------------------------------------------------------------- #
def test_new_class_blocks_keys_at_decode():
    model = ToyModel()
    past = 6
    stats = {}
    with AllQueryAttentionKnockout(model, [0], blocked_keys=[2, 3], stats=stats):
        seen = _run(model, _decode_mask(past), seq=1)
    m = seen[0]
    assert m[0, 0, 0, 2] == MIN and m[0, 0, 0, 3] == MIN, "blocked keys not masked at decode"
    for k in (0, 1, 4, 5, 6):
        assert m[0, 0, 0, k] == 0, f"key {k} should be untouched, got {m[0,0,0,k]}"
    assert stats["n_decode_forward"] == 1
    assert stats["n_decode_edits"] > 0, "liveness counter did not register a decode-step edit"


def test_new_class_blocks_keys_at_prefill_respecting_causality():
    model = ToyModel()
    seq = 6
    stats = {}
    with AllQueryAttentionKnockout(model, [0], blocked_keys=[2], stats=stats):
        seen = _run(model, _prefill_mask(seq), seq=seq)
    m = seen[0]
    # every query row at or after key 2 is blocked from key 2 ...
    for q in range(2, seq):
        assert m[0, 0, q, 2] == MIN, f"row {q} should be blocked from key 2"
    # ... and rows before it were already causally masked, never un-masked
    for q in range(0, 2):
        assert m[0, 0, q, 2] == MIN, "upper triangle must remain causally masked"
    assert stats["n_prefill_forward"] == 1
    assert stats["n_decode_forward"] == 0


def test_key_beyond_cache_is_skipped_not_an_error():
    """A demo key not yet in the cache must be skipped silently, not raise."""
    model = ToyModel()
    stats = {}
    with AllQueryAttentionKnockout(model, [0], blocked_keys=[99], stats=stats):
        seen = _run(model, _decode_mask(3), seq=1)
    assert not (seen[0] == MIN).any()
    assert stats["n_decode_edits"] == 0


def test_head_subset_touches_only_those_heads():
    model = ToyModel(n_heads=4)
    with AllQueryAttentionKnockout(model, [0], blocked_keys=[1], heads=[2]):
        seen = _run(model, _decode_mask(4, heads=1), seq=1)
    m = seen[0]
    assert m.shape[1] == 4, "head axis was not expanded"
    assert m[0, 2, 0, 1] == MIN
    for h in (0, 1, 3):
        assert m[0, h, 0, 1] == 0, f"head {h} should be untouched"


def test_sdpa_footgun_raises_named_eager():
    """A missing/non-4-D mask must RAISE, never silently no-op."""
    model = ToyModel()
    with pytest.raises(RuntimeError, match="eager"):
        with AllQueryAttentionKnockout(model, [0], blocked_keys=[1]):
            _run(model, None, seq=4)


def test_batch_gt_one_raises():
    model = ToyModel()
    mask = torch.zeros(2, 1, 1, 5)
    with pytest.raises(NotImplementedError):
        with AllQueryAttentionKnockout(model, [0], blocked_keys=[1]):
            x = torch.zeros(2, 1, 8)
            model(x, attention_mask=mask)


def test_layer_selectivity_and_handle_removal():
    model = ToyModel(n_layers=3)
    with AllQueryAttentionKnockout(model, [1], blocked_keys=[1]):
        seen = _run(model, _decode_mask(4), seq=1)
    assert not (seen[0] == MIN).any(), "layer 0 must be untouched"
    assert (seen[1] == MIN).any(), "layer 1 must be edited"
    assert not (seen[2] == MIN).any(), "layer 2 must be untouched"
    # after exit the hook is gone
    seen2 = _run(model, _decode_mask(4), seq=1)
    assert not (seen2[1] == MIN).any(), "handle was not removed on __exit__"


def test_callers_mask_is_never_mutated():
    model = ToyModel()
    mask = _decode_mask(5)
    before = mask.clone()
    with AllQueryAttentionKnockout(model, [0], blocked_keys=[2]):
        _run(model, mask, seq=1)
    assert torch.equal(mask, before), "the caller's mask tensor was mutated in place"


def test_liveness_counters_accumulate_across_a_simulated_generation():
    """Simulate prefill + 5 decode steps; every decode step must register an edit."""
    model = ToyModel()
    stats = {}
    seq = 8
    with AllQueryAttentionKnockout(model, [0], blocked_keys=[2, 3, 4], stats=stats):
        _run(model, _prefill_mask(seq), seq=seq)
        for step in range(5):
            _run(model, _decode_mask(seq + step), seq=1)
    assert stats["n_prefill_forward"] == 1
    assert stats["n_decode_forward"] == 5, "one edit-eligible forward per generated token"
    assert stats["n_decode_edits"] >= 5 * 3, "each decode step must block all three keys"
