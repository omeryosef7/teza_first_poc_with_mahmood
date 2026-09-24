"""R31-B/S-339. The attention-mass instrument must draw the SAME control positions the arms do.

`knockout_key_set(name, demo_keys, seq_len, control_seed, ...)` derives the draw index from the
ARM NAME and applies the stride ITSELF (score_behavior.py:1518). So `control_seed` is the RUN's
seed. `retrieval_strength.py` passed `nondemo_draw_seed(args.seed, idx)` instead -- a pre-strided
value -- and the callee strided it again.

Measured consequence, for --seed 20260913:
    draw   a real arm draws with    the instrument used
    d1          28180690                36100467   <- which is a real arm's D2 seed
    d2          36100467                51940021   <- no arm uses this
    d3          44020244                67779575   <- no arm uses this
So one of the three measured draws was a genuine arm draw wearing the wrong label and two belonged
to no arm at all. The draws are exchangeable, so S-337's rho remains a valid estimate of the
DISTRIBUTION -- but the claim in S-331/S-337 that these were "the draws the real arms make" was
false, and that claim was the stated reason for passing --seed 20260913 at all.
"""
import ast
import importlib.util
import os
import random
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RETR = os.path.join(ROOT, "src", "boombness", "retrieval_strength.py")
SB = os.path.join(ROOT, "src", "boombness", "score_behavior.py")


def _sb():
    spec = importlib.util.spec_from_file_location("sb_seed_test", SB)
    m = importlib.util.module_from_spec(spec)
    sys.modules["sb_seed_test"] = m
    spec.loader.exec_module(m)
    return m


def test_the_mass_instrument_does_not_PRE_STRIDE_the_control_seed():
    """PROPERTY (static): no `knockout_key_set(...)` call in retrieval_strength.py may pass a
    `nondemo_draw_seed(...)` result as its control_seed. The stride belongs to the callee."""
    tree = ast.parse(open(RETR).read())
    offenders = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        fn = node.func
        name = getattr(fn, "attr", None) or getattr(fn, "id", None)
        if name != "knockout_key_set":
            continue
        args = list(node.args)
        seed_arg = args[3] if len(args) >= 4 else None
        if seed_arg is None:
            continue
        for sub in ast.walk(seed_arg):
            if isinstance(sub, ast.Call):
                inner = getattr(sub.func, "attr", None) or getattr(sub.func, "id", None)
                if inner == "nondemo_draw_seed":
                    offenders.append(ast.unparse(seed_arg))
    assert not offenders, (
        "retrieval_strength.py pre-strides the control seed before handing it to "
        "knockout_key_set, which strides it again -- the instrument then measures draws the arms "
        "never make: %r" % (offenders,))


def test_the_drawn_positions_are_the_ones_a_real_arm_draws():
    """PROPERTY (behavioural): with control_seed = the RUN seed, knockout_key_set reproduces
    exactly the positions an independent implementation derives from nondemo_draw_seed(seed, idx).
    Pins the convention the static test protects."""
    sb = _sb()
    seed, seq = 20260913, 223
    dk = sorted(random.Random(0).sample(range(1, 150), 56))
    prot = set(range(190, 218))
    pool = [x for x in range(1, seq - 1) if x not in set(dk) and x not in prot]
    for idx in (1, 2, 3):
        nm = "nondemo_matched_d%d" % idx
        got = sb.knockout_key_set(nm, dk, seq, seed, protected=prot)
        want_seed = sb.nondemo_draw_seed(seed, idx)
        want = sorted(random.Random(want_seed).sample(pool, len(dk)))
        assert got == want, "%s: knockout_key_set did not draw the arm's positions" % nm
        assert len(got) == len(dk), "%s: draw is not count-matched" % nm


def test_the_two_seedings_are_genuinely_different_draws():
    """The companion that makes the above non-vacuous: pre-striding really does change the
    positions, so the static guard is protecting something real."""
    sb = _sb()
    seed, seq = 20260913, 223
    dk = sorted(random.Random(0).sample(range(1, 150), 56))
    prot = set(range(190, 218))
    right = sb.knockout_key_set("nondemo_matched_d1", dk, seq, seed, protected=prot)
    wrong = sb.knockout_key_set("nondemo_matched_d1", dk, seq,
                                sb.nondemo_draw_seed(seed, 1), protected=prot)
    assert right != wrong, "pre-striding made no difference; this guard would be vacuous"
    # and the mis-seeded d1 is exactly a real arm's d2
    d2 = sb.knockout_key_set("nondemo_matched_d2", dk, seq, seed, protected=prot)
    assert wrong == d2, "the mis-seeded d1 should coincide with the arm's d2 draw"
