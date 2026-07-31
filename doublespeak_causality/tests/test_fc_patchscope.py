"""
tests/test_fc_patchscope.py — CPU-only unit test for 46_forced_choice_patchscope.py's
pure gate/argmax helper (`patchscope_gate`). Mirrors the gate test in
tests/test_kv_mediation.py. No torch / numpy / model: the module under test defers all
heavy imports into its functions, so importing it for this test is CPU-safe.

Run:  python doublespeak_causality/tests/test_fc_patchscope.py
      pytest doublespeak_causality/tests/test_fc_patchscope.py
"""
import os
import sys
import importlib.util

HERE = os.path.dirname(os.path.abspath(__file__))
DSC = os.path.dirname(HERE)
sys.path.insert(0, DSC)


def _load_fc():
    spec = importlib.util.spec_from_file_location(
        "fc_patchscope", os.path.join(DSC, "46_forced_choice_patchscope.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_patchscope_gate_argmax_and_threshold():
    g = _load_fc().patchscope_gate
    # argmax layer, its value, pass on the 0.1 positive-control threshold
    best, mx, ok = g([0.01, 0.02, 0.55, 0.30])
    assert best == 2 and abs(mx - 0.55) < 1e-12 and ok is True
    # all below threshold -> control FAILS but argmax still returned
    best, mx, ok = g([0.01, 0.09, 0.05])
    assert best == 1 and abs(mx - 0.09) < 1e-12 and ok is False
    # empty scores -> safe default, not usable
    assert g([]) == (0, 0.0, False)
    # exactly at the threshold is NOT a pass (strict >)
    assert g([0.1])[2] is False
    # first-of-ties: argmax returns the earliest maximal layer
    best, mx, ok = g([0.4, 0.4, 0.2])
    assert best == 0 and abs(mx - 0.4) < 1e-12 and ok is True


def test_patchscope_gate_return_types():
    g = _load_fc().patchscope_gate
    best, mx, ok = g([0.2, 0.9])
    assert isinstance(best, int) and isinstance(mx, float) and isinstance(ok, bool)


def test_inspection_prompt_is_demo_free():
    m = _load_fc()
    # the forced-choice inspection prompt must NOT reference a demonstration block
    tmpl = m.FORCED_CHOICE_INSPECTION.lower()
    assert "text above" not in tmpl and "examples above" not in tmpl
    # it must carry both label slots and the probe slot
    for slot in ("{w}", "{a}", "{b}"):
        assert slot in m.FORCED_CHOICE_INSPECTION
    # a filled instance mentions the probe/labels literally (no leftover braces)
    filled = m.FORCED_CHOICE_INSPECTION.format(w="carrot", a="bomb", b="carrot")
    assert "{" not in filled and "bomb" in filled and "carrot" in filled


TESTS = [test_patchscope_gate_argmax_and_threshold,
         test_patchscope_gate_return_types,
         test_inspection_prompt_is_demo_free]

if __name__ == "__main__":
    fails = 0
    for t in TESTS:
        try:
            t(); print(f"PASS  {t.__name__}")
        except Exception as e:
            fails += 1; print(f"FAIL  {t.__name__}: {e}")
    print(f"\n{len(TESTS) - fails}/{len(TESTS)} passed")
    sys.exit(1 if fails else 0)
