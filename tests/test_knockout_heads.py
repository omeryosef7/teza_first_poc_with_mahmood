"""--knockout-heads: the R-AL single-head follow-up, and the three ways it could lie.

WHY. `AllQueryAttentionKnockout` has always accepted `heads=`, but score_behavior never passed it, so
every Phase 2-4 arm blocked ALL heads. R-AL found Qwen3 L8h22 is the top demonstration-attention head
in 72 of 96 prompts, which makes "does ONE head of 40 reproduce the band effect" the next question.

The three silent failures this guards against:
  1. the flag is accepted but never reaches the hook -> an arm named "head 22" blocks all 40 heads and
     reproduces the band effect trivially;
  2. the flag is given without --intervene -> it reaches nothing at all and the run is filed under a
     head-restricted name while blocking nothing;
  3. an out-of-range head -> IndexError deep inside the per-row try, i.e. 96 silent ledger failures.

Run:  python -m pytest tests/test_knockout_heads.py -q
"""
import os
import sys
import types

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "boombness"))
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src", "boombness", "score_behavior.py")


class _FakeKO:
    def __init__(self, model, layer_idxs, blocked_keys=None, heads=None, stats=None):
        self.layers, self.blocked_keys, self.heads = list(layer_idxs), list(blocked_keys or []), heads


class _PC:
    def __init__(self):
        self.made = []

    def AllQueryAttentionKnockout(self, model, layers, blocked_keys=None, heads=None, stats=None):
        k = _FakeKO(model, layers, blocked_keys, heads, stats)
        self.made.append(k)
        return k


class _LM:
    model = types.SimpleNamespace(config=types.SimpleNamespace(hidden_size=16, num_attention_heads=40))


DEMO = [11, 12, 13, 14, 15]


def test_heads_reach_the_hook():
    """FAILURE 1. Drop knock_heads on the call and this goes red."""
    import score_behavior as sb
    pc = _PC()
    spec = {"direction": "demo_all", "mode": "attn_knockout", "layers": [8], "alpha": 1.0}
    sb.make_intervention(None, pc, _LM(), spec, None, control_seed=1,
                         demo_keys=DEMO, seq_len=64, knock_stats={}, knock_heads=[22])
    assert pc.made[0].heads == [22], (
        "the head subset did not reach AllQueryAttentionKnockout; the arm would block ALL heads "
        "while being named after one")


def test_default_is_still_all_heads():
    """Phases 2-4 must be unaffected: no heads argument means heads=None means every head."""
    import score_behavior as sb
    pc = _PC()
    spec = {"direction": "demo_all", "mode": "attn_knockout", "layers": [8], "alpha": 1.0}
    sb.make_intervention(None, pc, _LM(), spec, None, control_seed=1,
                         demo_keys=DEMO, seq_len=64, knock_stats={})
    assert pc.made[0].heads is None, "the default changed; every Phase 2-4 arm would be re-scoped"


def test_composed_arms_forward_heads_too():
    """The composed recursion has dropped a threaded argument twice on this exact line."""
    import torch  # noqa: F401
    import score_behavior as sb
    pc = _PC()
    pc.AllPositionProjectOut = lambda *a, **k: object()
    spec = {"composed": [
        {"direction": "demo_all", "mode": "attn_knockout", "layers": [8], "alpha": 1.0},
        {"direction": "demo_all", "mode": "attn_knockout", "layers": [9], "alpha": 1.0}]}
    sb.make_intervention(None, pc, _LM(), spec, None, control_seed=1,
                         demo_keys=DEMO, seq_len=64, knock_stats={}, knock_heads=[22])
    assert [k.heads for k in pc.made] == [[22], [22]], \
        "the composed recursion dropped knock_heads on one leg"


def test_flag_without_intervene_refuses():
    """FAILURE 2, asserted at source level: the check lives in main()'s arg handling."""
    src = open(SRC).read()
    assert "args.knockout_heads.strip() and not args.intervene" in src, \
        "the no-intervene guard is gone; the flag would silently do nothing"
    i = src.index("args.knockout_heads.strip() and not args.intervene")
    assert "REFUSING" in src[i:i + 300]


def test_out_of_range_head_refuses_before_the_run():
    """FAILURE 3: must die at argument time, not as 96 ledger failures inside the per-row try."""
    src = open(SRC).read()
    assert "outside 0-{_nh-1}" in src, "the head range check is gone"
    i = src.index("outside 0-{_nh-1}")
    assert "REFUSING" in src[max(0, i - 200):i + 60]
    assert "num_attention_heads" in src[max(0, i - 800):i], \
        "the range is not taken from the model's own head count"


def test_duplicate_heads_refuse():
    src = open(SRC).read()
    assert "duplicate heads in" in src


def test_the_selection_is_echoed():
    """A head-restricted run that does not say which heads is unauditable."""
    src = open(SRC).read()
    assert "knockout restricted to" in src
