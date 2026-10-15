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
    assert "candle" not in a["dev"] and len(a["dev"]) == 5
    assert not set(a["dev"]) & set(a["confirmation"])
    assert len(a["confirmation"]) == 15


def test_draw_requires_five():
    import pytest
    with pytest.raises(SystemExit):
        d.draw({"lamp": 0.1}, ["lamp"])


def test_fill_rule_when_cells_sparse():
    # all survivors in ONE cell (same tertile, all below median) -> only 1 non-empty... fill to 5
    low = [w for w, t in d.tertiles().items() if t == "low"]
    strength = {w: 0.5 for w in low}           # all equal -> all 'below' the median
    out = d.draw(strength, low)
    assert len(out["dev"]) == 5 and out["n_fill"] == 4 and "candle" not in out["dev"]
    assert len(set(out["dev"])) == 5 and not set(out["dev"]) & set(out["confirmation"])
    assert out == d.draw(strength, low)       # deterministic


def test_cutpoint_tertiles_reproduce_original_rank_assignment():
    order = sorted(d.ZIPF, key=lambda w: (d.ZIPF[w], w))
    rank_based = {w: ("low" if i < 7 else "mid" if i < 14 else "high") for i, w in enumerate(order)}
    assert d.tertiles() == rank_based


def test_replacement_gets_cutpoint_tertile():
    z = dict(d.ZIPF); z["sock"] = 3.61; z["basin"] = 4.08; z["mug"] = 3.95
    t = d.tertiles(z)
    assert (t["sock"], t["mug"], t["basin"]) == ("low", "mid", "high")
