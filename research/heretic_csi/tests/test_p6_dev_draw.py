import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import p6_dev_draw as d


def test_tertiles_frozen_sizes():
    t = d.tertiles()
    assert sorted(t.values()).count("low") == 7 and list(t.values()).count("mid") == 7 and list(t.values()).count("high") == 6
    assert t["kettle"] == "low" and t["chair"] == "high"


def test_draw_deterministic_and_disjoint():
    strength = {w: (i * 0.037) % 0.9 for i, w in enumerate(sorted(d.ZIPF))}
    surv = sorted(d.ZIPF)
    a = d.draw(strength, surv); b = d.draw(strength, surv)
    assert a == b
    assert a["dev"][0] == "candle" and len(a["dev"]) == 6
    assert not set(a["dev"]) & set(a["confirmation"])
    assert len(a["confirmation"]) == 15


def test_draw_requires_five():
    import pytest
    with pytest.raises(SystemExit):
        d.draw({"lamp": 0.1}, ["lamp"])
