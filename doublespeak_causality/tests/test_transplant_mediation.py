"""
tests/test_transplant_mediation.py — positive control for 43_transplant_mediation.py
(NEXT_CAUSAL_SPRINT Stage 2). CPU-only, no model.

Writes a synthetic interv_raw.jsonl with KNOWN p_concept per arm/item and checks that
the analyzer recovers the hand-computed estimands exactly, pairs correctly across the
Neutral/DS receivers, computes the self-transplant faithfulness check, and sets the
directional verdicts. Guards against pairing/column/sign bugs before any GPU run.

Run:  python doublespeak_causality/tests/test_transplant_mediation.py
      pytest doublespeak_causality/tests/test_transplant_mediation.py
"""
import os
import sys
import json
import subprocess
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
DSC = os.path.dirname(HERE)

# arm -> per-item p_concept for items 0,1,2 (matched Neutral/DS versions share item key)
ARMS = {
    "Neutral_from_Neutral": [0.02, 0.03, 0.01],   # Y(Neu, h_N)  self-transplant baseline
    "Neutral_from_DS":      [0.04, 0.05, 0.03],   # Y(Neu, h_DS) -> IE_state = +0.02
    "Neutral_from_Direct":  [0.92, 0.93, 0.91],   # Y(Neu, h_Direct) -> PORT_Direct ~ +0.90
    "DS_from_Neutral":      [0.70, 0.72, 0.68],   # Y(DS, h_N)  -> DE_context ~ +0.68
    "DS_from_DS":           [0.88, 0.90, 0.86],   # Y(DS, h_DS) -> TE ~ +0.86, RESID_ctx ~ +0.18
    "DS_from_Direct":       [0.95, 0.96, 0.94],
}
NEU_ARMS = {"Neutral_from_Neutral", "Neutral_from_DS", "Neutral_from_Direct"}
GROUP = "early"


def _receiver_cond(arm):
    return "NEUTRAL_CODEWORD" if arm in NEU_ARMS else "DOUBLESPEAK"


def _write_raw():
    d = tempfile.mkdtemp()
    lines = []
    for i in range(3):
        readout = f"probe{i}"                     # encodes the item; shared Neu<->DS
        for arm, vals in ARMS.items():
            cond = _receiver_cond(arm)
            sid = f"{cond}|dev|s|4|{readout}"
            lines.append({"sid": sid, "condition": cond, "split": "dev",
                          "demo_style": "s", "n_demos": 4, "readout": readout,
                          "arm": arm, "group": GROUP, "layer": None, "alpha": 1.0,
                          "site": "codeword_last", "p_concept": vals[i],
                          "p_codeword": 1 - vals[i]})
        # identity baseline per receiver == self-transplant value (=> faithful ~ 0)
        for cond, base in (("NEUTRAL_CODEWORD", ARMS["Neutral_from_Neutral"][i]),
                           ("DOUBLESPEAK", ARMS["DS_from_DS"][i])):
            sid = f"{cond}|dev|s|4|probe{i}"
            lines.append({"sid": sid, "condition": cond, "split": "dev",
                          "demo_style": "s", "n_demos": 4, "readout": f"probe{i}",
                          "arm": "identity", "group": "none", "layer": None,
                          "alpha": 0.0, "site": "codeword_last",
                          "p_concept": base, "p_codeword": 1 - base})
    with open(os.path.join(d, "interv_raw.jsonl"), "w") as f:
        for r in lines:
            f.write(json.dumps(r) + "\n")
    return d


def _run(d):
    out = os.path.join(d, "med.json")
    r = subprocess.run(
        [sys.executable, os.path.join(DSC, "43_transplant_mediation.py"),
         "--interv-dir", d, "--metric", "p_concept", "--out", out],
        capture_output=True, text=True, cwd=DSC)
    assert r.returncode == 0, f"mediation failed:\n{r.stderr}"
    return json.load(open(out))


def _eff(res, name):
    return res["estimands"][f"{name}|{GROUP}"]["effect"]


def test_estimands_match_hand_computed():
    res = _run(_write_raw())
    exp = {"PORT_Direct": 0.90, "IE_state": 0.02, "DE_context": 0.68,
           "RESID_ctx": 0.18, "TE": 0.86, "INT": 0.16}
    for name, e in exp.items():
        got = _eff(res, name)
        assert abs(got - e) < 1e-6, f"{name}: expected {e}, got {got}"
        assert res["estimands"][f"{name}|{GROUP}"]["n"] == 3


def test_faithfulness_near_zero():
    res = _run(_write_raw())
    for arm in ("Neutral_from_Neutral", "DS_from_DS"):
        f = res["faithfulness"][arm]
        assert abs(f["effect"]) < 1e-6, f"self-transplant {arm} must equal identity"
        assert f["faithful"] is True


def test_verdicts_directional():
    res = _run(_write_raw())
    v = res["verdicts"][GROUP]
    assert v["H1_direct_portable"] is True          # PORT_Direct 0.90 >= 0.05
    assert v["H2_ds_state_less_portable"] is True    # IE 0.02 < PORT and |IE|<0.05
    assert v["H4_context_or_interaction_dominant"] is True  # |DE 0.68| > |IE 0.02|


def test_equivalence_flag_on_inert_estimand():
    res = _run(_write_raw())
    ie = res["estimands"][f"IE_state|{GROUP}"]
    assert "within_equivalence" in ie
    assert ie["within_equivalence"] is True          # [~0.02,0.02] within +-0.05


TESTS = [test_estimands_match_hand_computed, test_faithfulness_near_zero,
         test_verdicts_directional, test_equivalence_flag_on_inert_estimand]

if __name__ == "__main__":
    fails = 0
    for t in TESTS:
        try:
            t(); print(f"PASS  {t.__name__}")
        except Exception as e:
            fails += 1; print(f"FAIL  {t.__name__}: {e}")
    print(f"\n{len(TESTS)-fails}/{len(TESTS)} passed")
    sys.exit(1 if fails else 0)
