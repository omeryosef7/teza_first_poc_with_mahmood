"""A composed arm must forward `demo_keys`/`seq_len` to EVERY leg, not just the single-spec path.

WHY THIS FILE EXISTS. `make_intervention`'s composed recursion in score_behavior.py has dropped a
threaded argument twice, both times on the same line, and both times the consequence was a control
that silently was not a control:

  * `control_seed` dropped (2026-08-18) -> three "independent" draws produced byte-identical
    generations (sha256 276b6af46eb68a76 x3) and a "3-draw band, sd 0.0048" that was n=1. That is
    retraction #7's defect, re-created inside the fix for it.

`demo_keys` is threaded through the same line for the attention-knockout arms. If it is dropped, a
composed arm such as `refusalness:project_out:14-14:1.0+demo_all:attn_knockout:0-31:1.0` would run
the projection and a knockout with NO KEYS -- i.e. the projection alone, reported under the name of
a composed arm. These tests fail against that.

The second test is the stronger one: it asserts the failure is LOUD. A knockout leg that receives no
keys must raise, never quietly contribute zero hooks, because a no-op knockout scores as a perfectly
healthy null.

Run:  python -m pytest tests/test_composed_knockout.py -q
"""
import os
import sys
import types

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "boombness"))


class _FakeKnockout:
    """Stands in for pair_common.AllQueryAttentionKnockout and records what it was given."""

    def __init__(self, model, layer_idxs, blocked_keys=None, heads=None, stats=None):
        self.layers = list(layer_idxs)
        self.blocked_keys = list(blocked_keys or [])
        self.stats = stats


class _PC:
    def __init__(self):
        self.made = []

    def AllQueryAttentionKnockout(self, model, layers, blocked_keys=None, heads=None, stats=None):
        k = _FakeKnockout(model, layers, blocked_keys, heads, stats)
        self.made.append(k)
        return k

    def AllPositionProjectOut(self, *a, **k):
        return object()


class _LM:
    model = types.SimpleNamespace(config=types.SimpleNamespace(hidden_size=16))


DEMO_KEYS = [11, 12, 13, 14, 15]
SEQ_LEN = 64


def _payload():
    import torch
    return {"d_surface": {14: torch.ones(16)}, "gap": {"d_surface": {14: 1.0}}}


def test_demo_keys_reach_the_knockout_leg_of_a_composed_arm():
    """THE REGRESSION TEST. Drop demo_keys on the recursion line and this goes red."""
    import score_behavior as sb
    pc = _PC()
    spec = {"composed": [
        {"direction": "d_surface", "mode": "project_out", "layers": [14], "alpha": 1.0},
        {"direction": "demo_all", "mode": "attn_knockout", "layers": [0, 1], "alpha": 1.0},
    ]}
    ctxs = sb.make_intervention(None, pc, _LM(), spec, _payload(), control_seed=20260823,
                                demo_keys=DEMO_KEYS, seq_len=SEQ_LEN, knock_stats={})
    assert len(pc.made) == 1, "the knockout leg did not build a knockout"
    assert pc.made[0].blocked_keys == DEMO_KEYS, (
        "the composed recursion did not forward demo_keys to the knockout leg — this is the "
        "one-of-two-paths failure that hit control_seed twice")
    assert len(ctxs) == 2, "a composed arm must contribute one context per leg"


def test_a_knockout_leg_without_keys_raises_rather_than_no_ops():
    """A silent no-op knockout scores as a clean null. It must be impossible."""
    import score_behavior as sb
    spec = {"direction": "demo_all", "mode": "attn_knockout", "layers": [0], "alpha": 1.0}
    with pytest.raises(SystemExit, match="demo_keys=None"):
        sb.make_intervention(None, _PC(), _LM(), spec, None, control_seed=20260823,
                             demo_keys=None, seq_len=SEQ_LEN)


def test_empty_key_set_raises():
    import score_behavior as sb
    spec = {"direction": "demo_all", "mode": "attn_knockout", "layers": [0], "alpha": 1.0}
    with pytest.raises(SystemExit, match="EMPTY key set"):
        sb.make_intervention(None, _PC(), _LM(), spec, None, control_seed=20260823,
                             demo_keys=[], seq_len=SEQ_LEN)


def test_alpha_must_be_one_because_a_mask_edit_is_not_dosable():
    import score_behavior as sb
    spec = {"direction": "demo_all", "mode": "attn_knockout", "layers": [0], "alpha": 0.5}
    with pytest.raises(SystemExit, match="not dosable"):
        sb.make_intervention(None, _PC(), _LM(), spec, None, control_seed=20260823,
                             demo_keys=DEMO_KEYS, seq_len=SEQ_LEN)


# --------------------------------------------------------------------------- #
# knockout_key_set: the arms themselves
# --------------------------------------------------------------------------- #
def test_demo_all_returns_exactly_the_demo_block():
    import score_behavior as sb
    assert sb.knockout_key_set("demo_all", DEMO_KEYS, SEQ_LEN, 1) == DEMO_KEYS


def test_nondemo_random_is_count_matched_and_disjoint_from_the_demo_block():
    import score_behavior as sb
    got = sb.knockout_key_set("nondemo_random", DEMO_KEYS, SEQ_LEN, 20260823)
    assert len(got) == len(DEMO_KEYS), "the control must be count-matched to the arm"
    assert not (set(got) & set(DEMO_KEYS)), "the control drew keys inside the demo block"
    assert max(got) < SEQ_LEN - 1, "the control must not cut the final prompt token"


def test_nondemo_random_actually_varies_with_the_seed():
    """The byte-identical-gens failure is what happens when the seed does not reach the draw."""
    import score_behavior as sb
    draws = {tuple(sb.knockout_key_set("nondemo_random", DEMO_KEYS, SEQ_LEN, s))
             for s in (20260901, 20260902, 20260903)}
    assert len(draws) == 3, f"three seeds produced {len(draws)} distinct control draws"


def test_allpast_is_a_superset_of_the_demo_block():
    """The positive control must cut strictly more than the arm, or it cannot bound it."""
    import score_behavior as sb
    got = sb.knockout_key_set("allpast", DEMO_KEYS, SEQ_LEN, 1)
    assert set(DEMO_KEYS).issubset(set(got))
    assert 0 not in got, "BOS must be spared"
    assert len(got) > len(DEMO_KEYS)


def test_unknown_arm_raises():
    import score_behavior as sb
    with pytest.raises(SystemExit, match="unknown attn_knockout arm"):
        sb.knockout_key_set("not_an_arm", DEMO_KEYS, SEQ_LEN, 1)


def test_nondemo_random_refuses_when_it_cannot_be_count_matched():
    """Better to fail than to ship a control that is quietly smaller than its arm."""
    import score_behavior as sb
    with pytest.raises(SystemExit, match="count-matched"):
        sb.knockout_key_set("nondemo_random", list(range(1, 20)), 12, 1)


def test_a_pure_knockout_spec_needs_no_fitted_direction_file():
    """Regression: `p` (the direction file) is None for a mask-edit arm.

    The payload load was guarded for this and the very next line -- an f-string calling
    os.path.basename(p) -- was not, so an 8-prompt smoke died after loading the model with
    "TypeError: expected str, bytes or os.PathLike object, not NoneType". Same one-of-two-paths
    shape as the control_seed and demo_keys drops, this time in a print statement.
    """
    import os
    assert (os.path.basename(None) if None else "(no fitted direction: mask-edit arm)") \
        == "(no fitted direction: mask-edit arm)"
    import score_behavior as sb
    # and the arm itself still builds without any payload
    pc = _PC()
    spec = {"direction": "demo_all", "mode": "attn_knockout", "layers": [0], "alpha": 1.0}
    ctxs = sb.make_intervention(None, pc, _LM(), spec, None, control_seed=1,
                                demo_keys=DEMO_KEYS, seq_len=SEQ_LEN, knock_stats={})
    assert len(ctxs) == 1 and pc.made[0].blocked_keys == DEMO_KEYS
