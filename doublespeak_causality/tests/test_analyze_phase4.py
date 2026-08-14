"""GPU-free test for the Phase-4 analysis (plan §8.4). Synthetic rows for Story A
(ablation moves readout, ASR unchanged) and Story B (ablation drops ASR)."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from src.probes import analyze_phase4 as ap  # noqa: E402

ARMS = ["ds_base", "ds_bomb_ablate", "ds_bomb_random", "ds_refusal_ablate"]
LS = [20, 24, 28, 31]


def _row(i, base, ablate, rand, refabl, ro_base=2.0, ro_ablate=-2.0):
    def ro(v): return {str(L): v for L in LS}
    return {"example_id": f"e{i}",
            "ds_base_score": base, "ds_base_label": "MALICIOUS" if base >= 0.5 else "REFUSAL",
            "ds_bomb_ablate_score": ablate, "ds_bomb_ablate_label": "MALICIOUS" if ablate >= 0.5 else "REFUSAL",
            "ds_bomb_random_score": rand, "ds_bomb_random_label": "MALICIOUS" if rand >= 0.5 else "REFUSAL",
            "ds_refusal_ablate_score": refabl, "ds_refusal_ablate_label": "MALICIOUS" if refabl >= 0.5 else "REFUSAL",
            "ds_base_bombness_readout": ro(ro_base), "ds_bomb_ablate_bombness_readout": ro(ro_ablate),
            "ds_bomb_random_bombness_readout": ro(ro_base), "ds_refusal_ablate_bombness_readout": ro(ro_base)}


def test_story_a():
    # ablation collapses readout; ASR identical base==ablate==random; refusal ablation raises ASR
    rows = []
    for i in range(40):
        s = 0.9 if i < 10 else 0.1                 # base ASR 0.25
        rows.append(_row(i, s, s, s, 0.9 if i < 30 else 0.1))  # refusal ablation ASR 0.75
    res = ap.analyze(rows, ARMS)
    assert res["verdict"]["manipulation_check_passed"] is True
    assert abs(res["verdict"]["bombness_d_asr"]) < 0.1
    assert res["verdict"]["refusal_positive_control_d_asr"] > 0.3
    assert "STORY A" in res["verdict"]["reading"]


def test_story_b():
    rows = []
    for i in range(40):
        base = 0.9 if i < 20 else 0.1              # base ASR 0.5
        ablate = 0.1                                # ablation removes all success
        rows.append(_row(i, base, ablate, base, base))
    res = ap.analyze(rows, ARMS)
    assert res["verdict"]["bombness_d_asr"] < -0.1
    assert "STORY B" in res["verdict"]["reading"]


def test_manip_fail_is_inconclusive():
    rows = [_row(i, 0.9 if i < 10 else 0.1, 0.9 if i < 10 else 0.1, 0.1, 0.1,
                 ro_base=2.0, ro_ablate=1.9) for i in range(40)]  # readout barely moves
    res = ap.analyze(rows, ARMS)
    assert res["verdict"]["manipulation_check_passed"] is False
    assert "INCONCLUSIVE" in res["verdict"]["reading"]


def test_factorial_2x2():
    """4 cells present -> main effects + interaction computed. Construct data where
    Bombness is inert regardless of refusal (interaction ~ 0, main_effect_bombness ~ 0)."""
    ARMS4 = ARMS + ["ds_bomb_and_refusal_ablate"]
    rows = []
    for i in range(60):
        base = 0.9 if i < 15 else 0.1        # bomb high, refusal intact: ASR 0.25
        refabl = 0.9 if i < 45 else 0.1      # bomb high, refusal supp:  ASR 0.75
        row = _row(i, base, base, base, refabl)   # bomb_ablate == base (bomb inert)
        # combined cell = refusal-ablate level (bomb inert even when refusal suppressed)
        row["ds_bomb_and_refusal_ablate_score"] = refabl
        row["ds_bomb_and_refusal_ablate_label"] = "MALICIOUS" if refabl >= 0.5 else "REFUSAL"
        row["ds_bomb_and_refusal_ablate_bombness_readout"] = {str(L): -2.0 for L in LS}
        rows.append(row)
    res = ap.analyze(rows, ARMS4)
    f = res["factorial_2x2"]
    assert abs(f["main_effect_bombness"]["estimate"]) < 0.1     # bomb inert
    assert f["main_effect_refusal"]["estimate"] > 0.3           # refusal drives ASR
    assert abs(f["interaction"]["estimate"]) < 0.15             # no gating
