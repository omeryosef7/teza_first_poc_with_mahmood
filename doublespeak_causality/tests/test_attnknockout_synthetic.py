"""
GPU-free synthetic tests for pair_common.AttentionKnockout (plan §P0 / §0.9 — untested
hook primitives). No model, no GPU, deterministic; the toy modules mimic the HF decoder
layer interface (self_attn called with attention_mask as a KEYWORD, returning a tuple).

Asserts:
  (a) SDPA FOOTGUN — a missing / non-4-D attention mask raises a clear RuntimeError that
      names attn_implementation='eager'. This is the critical one: ds_common.load_model
      defaults to attn_implementation='sdpa', where the mask handed to self_attn is
      typically None (causal handled internally), so a knockout that did not raise would
      silently be a NO-OP and every "knockout has no effect" number would be vacuous;
  (b) with an eager-style 4-D additive mask the hook sets EXACTLY the requested
      (query, key) cells to finfo.min and leaves every other cell bit-identical;
  (c) a head subset expands the head axis and touches ONLY those heads;
  (d) causal guard (key > query skipped), out-of-range query skipped, batch>1 raises,
      per-layer selectivity, caller's mask never mutated, handles removed on exit;
  (e) a mask passed POSITIONALLY is not seen by the hook (it reads kwargs only) and
      therefore also raises rather than silently no-op'ing.

Run:  python -m pytest doublespeak_causality/tests/test_attnknockout_synthetic.py -q
"""
import os
import sys

import pytest
import torch
import torch.nn as nn

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from pair_common import AttentionKnockout  # noqa: E402


# --------------------------------------------------------------------------- #
# Toy model: mimics the HF decoder-layer interface the hook relies on
# --------------------------------------------------------------------------- #
class ToyAttn(nn.Module):
    """Records the attention_mask it was actually called with (that IS the knockout)."""

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
        a, _ = self.self_attn(x, attention_mask=attention_mask)   # KWARG, like HF
        return (x + a, None)


class ToyBlockPositionalMask(nn.Module):
    """Pathological variant: passes the mask POSITIONALLY, so kwargs has no mask."""

    def __init__(self):
        super().__init__()
        self.self_attn = ToyAttn()

    def forward(self, x, attention_mask=None):
        a, _ = self.self_attn(x, attention_mask)                  # positional
        return (x + a, None)


class ToyCfg:
    def __init__(self, n_heads, hidden):
        self.num_attention_heads = n_heads
        self.num_key_value_heads = max(1, n_heads // 2)           # GQA: irrelevant here
        self.hidden_size = hidden


class ToyModel(nn.Module):
    def __init__(self, n_layers=3, n_heads=4, hidden=8, block_cls=ToyBlock):
        super().__init__()
        self.config = ToyCfg(n_heads, hidden)
        self.model = nn.Module()
        self.model.layers = nn.ModuleList(block_cls() for _ in range(n_layers))

    def forward(self, x, attention_mask=None):
        for blk in self.model.layers:
            x, _ = blk(x, attention_mask=attention_mask)
        return x


def _causal_mask(seq, batch=1, heads=1, dtype=torch.float32):
    """eager-style 4-D ADDITIVE mask: 0 where allowed, finfo.min above the diagonal."""
    m = torch.zeros(batch, heads, seq, seq, dtype=dtype)
    minv = torch.finfo(dtype).min
    for q in range(seq):
        for k in range(q + 1, seq):
            m[:, :, q, k] = minv
    return m


def _run(model, seq=6, mask=None, hidden=8):
    x = torch.zeros(1, seq, hidden)
    model(x, attention_mask=mask)
    return [blk.self_attn.seen for blk in model.model.layers]


# --------------------------------------------------------------------------- #
# (a) the SDPA footgun
# --------------------------------------------------------------------------- #
def test_none_mask_raises_named_eager():
    """SDPA path: self_attn gets attention_mask=None -> must RAISE, never no-op."""
    m = ToyModel(n_layers=1)
    with pytest.raises(RuntimeError) as e:
        with AttentionKnockout(m, [0], query_positions=[3], blocked_keys=[1]):
            _run(m, mask=None)
    assert "eager" in str(e.value), str(e.value)
    assert "4-D" in str(e.value) or "4-d" in str(e.value).lower()


@pytest.mark.parametrize("shape", [(1, 6), (1, 6, 6), (1, 1, 6, 6, 1)])
def test_non_4d_mask_raises(shape):
    """2-D padding mask / 3-D mask / 5-D nonsense: all rejected loudly."""
    m = ToyModel(n_layers=1)
    bad = torch.zeros(*shape)
    with pytest.raises(RuntimeError):
        with AttentionKnockout(m, [0], query_positions=[3], blocked_keys=[1]):
            _run(m, mask=bad)


def test_positional_mask_is_invisible_to_the_hook():
    """DOCUMENTS a second footgun: the hook reads kwargs['attention_mask'] only. A layer
    that passes the mask positionally looks exactly like SDPA to the hook -> RuntimeError
    (loud), which is the safe failure mode."""
    m = ToyModel(n_layers=1, block_cls=ToyBlockPositionalMask)
    mask = _causal_mask(6)
    with pytest.raises(RuntimeError):
        with AttentionKnockout(m, [0], query_positions=[3], blocked_keys=[1]):
            _run(m, mask=mask)


# --------------------------------------------------------------------------- #
# (b) exact cell semantics under an eager 4-D mask
# --------------------------------------------------------------------------- #
def test_blocks_exactly_the_requested_cells():
    seq = 6
    m = ToyModel(n_layers=1)
    base = _causal_mask(seq)
    with AttentionKnockout(m, [0], query_positions=[4], blocked_keys=[1, 2]):
        seen = _run(m, seq=seq, mask=base)[0]
    minv = torch.finfo(base.dtype).min
    assert seen.shape == base.shape, seen.shape
    diff = (seen != base)
    assert int(diff.sum()) == 2, f"expected exactly 2 edited cells, got {int(diff.sum())}"
    assert seen[0, 0, 4, 1] == minv and seen[0, 0, 4, 2] == minv
    # everything else bit-identical
    keep = base.clone()
    keep[0, 0, 4, 1] = minv
    keep[0, 0, 4, 2] = minv
    assert torch.equal(seen, keep)


def test_multiple_query_positions():
    seq = 5
    m = ToyModel(n_layers=1)
    base = _causal_mask(seq)
    with AttentionKnockout(m, [0], query_positions=[2, 4], blocked_keys=[0]):
        seen = _run(m, seq=seq, mask=base)[0]
    minv = torch.finfo(base.dtype).min
    assert seen[0, 0, 2, 0] == minv and seen[0, 0, 4, 0] == minv
    assert int((seen != base).sum()) == 2


def test_causal_guard_skips_future_keys_and_keeps_self():
    """kp is applied only when 0 <= kp <= qp (a future key is already -inf anyway)."""
    seq = 5
    m = ToyModel(n_layers=1)
    base = _causal_mask(seq)
    with AttentionKnockout(m, [0], query_positions=[2], blocked_keys=[3, 4, -1, 2]):
        seen = _run(m, seq=seq, mask=base)[0]
    minv = torch.finfo(base.dtype).min
    assert seen[0, 0, 2, 2] == minv, "kp == qp (self-attention) IS blockable"
    # keys 3,4 were already min (causal) and -1 is skipped -> only the (2,2) cell changed
    assert int((seen != base).sum()) == 1


def test_out_of_range_query_is_skipped_silently():
    """A query index past the current seq (e.g. a decode step) is skipped, not an error."""
    seq = 4
    m = ToyModel(n_layers=1)
    base = _causal_mask(seq)
    with AttentionKnockout(m, [0], query_positions=[99], blocked_keys=[0]):
        seen = _run(m, seq=seq, mask=base)[0]
    assert torch.equal(seen, base), "out-of-range query must leave the mask untouched"


def test_out_of_range_key_is_skipped_silently():
    seq = 4
    m = ToyModel(n_layers=1)
    base = _causal_mask(seq)
    with AttentionKnockout(m, [0], query_positions=[3], blocked_keys=[7]):
        seen = _run(m, seq=seq, mask=base)[0]
    assert torch.equal(seen, base)


# --------------------------------------------------------------------------- #
# (c) head subset
# --------------------------------------------------------------------------- #
def test_head_subset_touches_only_those_heads():
    seq, n_heads = 5, 4
    m = ToyModel(n_layers=1, n_heads=n_heads)
    base = _causal_mask(seq)                                  # head dim 1
    with AttentionKnockout(m, [0], query_positions=[3], blocked_keys=[1], heads=[1, 3]):
        seen = _run(m, seq=seq, mask=base)[0]
    minv = torch.finfo(base.dtype).min
    assert seen.shape == (1, n_heads, seq, seq), seen.shape
    for h in (1, 3):
        assert seen[0, h, 3, 1] == minv, f"head {h} must be blocked"
    for h in (0, 2):
        assert seen[0, h, 3, 1] == base[0, 0, 3, 1], f"head {h} must be untouched"
    # exactly two edited cells across the whole expanded mask
    assert int((seen != base.expand(1, n_heads, seq, seq)).sum()) == 2


def test_heads_none_blocks_every_head_of_an_already_expanded_mask():
    seq, n_heads = 4, 3
    m = ToyModel(n_layers=1, n_heads=n_heads)
    base = _causal_mask(seq, heads=n_heads)                   # already per-head
    with AttentionKnockout(m, [0], query_positions=[2], blocked_keys=[0], heads=None):
        seen = _run(m, seq=seq, mask=base)[0]
    minv = torch.finfo(base.dtype).min
    assert torch.all(seen[0, :, 2, 0] == minv), "heads=None must block every head"
    assert int((seen != base).sum()) == n_heads


def test_head_subset_on_already_expanded_mask_is_not_re_expanded():
    seq, n_heads = 4, 3
    m = ToyModel(n_layers=1, n_heads=n_heads)
    base = _causal_mask(seq, heads=n_heads)
    with AttentionKnockout(m, [0], query_positions=[2], blocked_keys=[0], heads=[0]):
        seen = _run(m, seq=seq, mask=base)[0]
    assert seen.shape == base.shape
    assert int((seen != base).sum()) == 1


# --------------------------------------------------------------------------- #
# (d) safety / hygiene
# --------------------------------------------------------------------------- #
def test_batch_gt_one_raises():
    seq = 4
    m = ToyModel(n_layers=1)
    base = _causal_mask(seq, batch=2)
    with pytest.raises(NotImplementedError):
        with AttentionKnockout(m, [0], query_positions=[2], blocked_keys=[0]):
            x = torch.zeros(2, seq, 8)
            m(x, attention_mask=base)


def test_only_selected_layers_are_hooked():
    seq = 5
    m = ToyModel(n_layers=3)
    base = _causal_mask(seq)
    with AttentionKnockout(m, [0, 2], query_positions=[3], blocked_keys=[1]):
        seen = _run(m, seq=seq, mask=base)
    minv = torch.finfo(base.dtype).min
    assert seen[0][0, 0, 3, 1] == minv and seen[2][0, 0, 3, 1] == minv
    assert torch.equal(seen[1], base), "unhooked layer must see the ORIGINAL mask"


def test_callers_mask_tensor_is_never_mutated():
    seq = 5
    m = ToyModel(n_layers=2)
    base = _causal_mask(seq)
    before = base.clone()
    with AttentionKnockout(m, [0, 1], query_positions=[3], blocked_keys=[1]):
        _run(m, seq=seq, mask=base)
    assert torch.equal(base, before), "the hook must clone, never edit the caller's mask"


def test_handles_removed_on_exit():
    seq = 4
    m = ToyModel(n_layers=2)
    base = _causal_mask(seq)
    with AttentionKnockout(m, [0, 1], query_positions=[2], blocked_keys=[0]) as ko:
        pass
    assert ko._handles == [], "handles must be emptied on __exit__"
    seen = _run(m, seq=seq, mask=base)
    assert all(torch.equal(s, base) for s in seen), "hooks must be gone"


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
