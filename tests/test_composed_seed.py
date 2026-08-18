"""A composed control arm must draw INDEPENDENT directions per --seed.

Fails against the pre-fix code: the recursion dropped control_seed, so every sub-spec used the
default 20260816 and three "independent" draws produced byte-identical generations
(sha256 276b6af46eb68a76 x3). That is retraction #7's defect, re-created.
"""
import os
import sys
import types

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "boombness"))


def _capture(monkey_seeds):
    """Drive make_intervention with stubs and record the seed each control draw actually receives."""
    import score_behavior as sb
    import signals as sg
    seen = []
    real = sg.random_control_direction
    sg.random_control_direction = lambda d, seed: (seen.append(seed), real(d, seed))[1]
    try:
        import torch
        payload = {"d_surface": {8: torch.ones(16), 18: torch.ones(16)},
                   "gap": {"d_surface": {8: 1.0, 18: 1.0}}}

        class _PC:
            def AllPositionProjectOut(self, *a, **k): return object()

        class _LM:
            model = types.SimpleNamespace(config=types.SimpleNamespace(hidden_size=16))
        spec = {"composed": [{"direction": "random", "mode": "project_out", "layers": [8], "alpha": 1.0},
                             {"direction": "random", "mode": "project_out", "layers": [18], "alpha": 1.0}]}
        out = {}
        for s in monkey_seeds:
            seen.clear()
            sb.make_intervention(None, _PC(), _LM(), spec, payload, control_seed=s)
            out[s] = list(seen)
        return out
    finally:
        sg.random_control_direction = real


def test_seed_reaches_every_leg_of_a_composed_arm():
    got = _capture([20260901, 20260902, 20260903])
    # every --seed must produce a DIFFERENT set of draw seeds
    assert len({tuple(v) for v in got.values()}) == 3, got


def test_the_two_legs_of_a_double_random_arm_are_independent_draws():
    got = _capture([20260901])[20260901]
    assert len(set(got)) == len(got), (
        "both legs drew the same seed: that composes a vector with itself at two layers, "
        "which is not what 'double random' means")
