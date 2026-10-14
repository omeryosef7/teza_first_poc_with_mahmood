"""PR-HCSI-S084 analysis checks (review #4 item 9): pure decide() edge cases (synthetic) + equivalence of the
unrounded recomputation with the frozen analyzer on the ALREADY-READ job 1022698 (56 controls; no new data)."""
import json, os, sys
import pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import p2a_powered_analyze as A

LOOKS = {"r1": 0.2456, "r16": 0.1754}


def _ctrls(n_rand=190, shuf_vals=None, rand_val=0.0):
    c = {f"KO_RAND_r4_{i}": rand_val - 1e-4 * i for i in range(n_rand)}
    for j, v in enumerate(shuf_vals if shuf_vals is not None else [0.001] * 10):
        c[f"KO_SHUF_r4_{j}"] = v
    return c


def test_pass_when_top_and_beats_all_shuf():
    d = A.decide(0.0129, _ctrls(), LOOKS, 0.006, True, [], 203, {})
    assert d["rank"] == 1 and d["VERDICT"] == "PASS" and d["holm"]["r4"] == pytest.approx(3 / 201)


def test_unrounded_tie_resolution():
    # candidate exceeds a control by 4e-6: equal after 5-dp rounding, strictly greater unrounded
    c = _ctrls(); c["KO_RAND_r4_0"] = 0.0129 - 4e-6
    d = A.decide(0.0129, c, LOOKS, 0.006, True, [], 203, {})
    assert d["rank"] == 1 and round(0.0129, 5) == round(0.0129 - 4e-6, 5)


def test_rank3_passes_holm_rank4_fails():
    c = _ctrls(); c["KO_RAND_r4_0"] = 0.02; c["KO_RAND_r4_1"] = 0.02
    assert A.decide(0.0129, c, LOOKS, 0.006, True, [], 203, {})["VERDICT"] == "PASS"       # 3/201=0.0149 -> Holm 0.0448
    c["KO_RAND_r4_2"] = 0.02
    assert A.decide(0.0129, c, LOOKS, 0.006, True, [], 203, {})["VERDICT"] == "DOES NOT PASS"  # 4/201 -> Holm 0.0597


def test_shuf_rule_blocks_pass():
    c = _ctrls(shuf_vals=[0.001] * 9 + [0.0130])
    d = A.decide(0.0129, c, LOOKS, 0.006, True, [], 203, {})
    assert d["rank"] == 2 and not d["beats_every_shuf"] and d["VERDICT"] == "DOES NOT PASS"


def test_ci_gates_void_block_pass():
    assert A.decide(0.0129, _ctrls(), LOOKS, -0.001, True, [], 203, {})["VERDICT"] == "DOES NOT PASS"
    assert A.decide(0.0129, _ctrls(), LOOKS, 0.006, False, [], 203, {})["VERDICT"] == "DOES NOT PASS"
    assert A.decide(0.0129, _ctrls(), LOOKS, 0.006, True, ["OVL_KO mismatch"], 203, {})["VERDICT"].startswith("VOID")


def test_row_set_deviation_names_arms():
    d = A.decide(0.0129, _ctrls(), LOOKS, 0.006, True, [], 201, {"KO_RAND_r4_77": 2, "KO_SELF": 0})
    assert d["row_set"]["deviation_from_203"] == -2 and d["row_set"]["arms_with_dropped_keys"] == ["KO_RAND_r4_77"]


REF = os.path.join(A.ROOT, "reports/heretic_csi/hcsi_p2a_button_r4_validation.json")


@pytest.mark.skipif(not os.path.exists(REF), reason="S-072 analyzer output absent")
def test_unrounded_matches_frozen_analyzer_on_1022698():
    d = json.load(open(REF))
    arms = ["BASE", "KO", "KO_SELF", "KO_FULL", "KO_CAND_r4"] + [f"KO_RAND_r4_{i}" for i in range(46)] + [f"KO_SHUF_r4_{j}" for j in range(10)]
    stat, n_common, lost = A.unrounded_stats(arms, ("1022698",))
    assert n_common == d["n_keys_common"] == 203
    ctr = d["control_recovery_distribution"]
    assert abs(round(stat["KO_CAND_r4"], 5) - ctr["candidate"]) <= 1.01e-5
    for a, v in ctr["controls"].items():
        assert abs(round(stat[a], 5) - v) <= 1.01e-5, a
    ctrls = {a: stat[a] for a in ctr["controls"]}
    dec = A.decide(stat["KO_CAND_r4"], ctrls, {"r1": 1, "r16": 1}, 0.006, True, [], n_common, lost)
    assert dec["rank"] == d["verdict_basis"]["candidate_rank"] == 1


def test_binding_combine():
    import p2a_powered_binding as Bn
    P, F, V = {"VERDICT": "PASS"}, {"VERDICT": "DOES NOT PASS"}, {"VERDICT": "VOID: x"}
    assert Bn.combine(P, P) == "PASS"
    assert Bn.combine(F, F) == "DOES NOT PASS"
    assert Bn.combine(P, F) == "DOES NOT PASS (rounding-sensitive)"
    assert Bn.combine(F, P) == "DOES NOT PASS (rounding-sensitive)"
    assert Bn.combine(V, P).startswith("VOID") and Bn.combine(P, V).startswith("VOID")


def test_rounded_tie_flips_to_rounding_sensitive():
    import p2a_powered_binding as Bn
    # rank 3 unrounded passes; rounding creates a tie with a 4th control -> rank 4 fails -> rounding-sensitive
    c = _ctrls(); c["KO_RAND_r4_0"] = 0.02; c["KO_RAND_r4_1"] = 0.02; c["KO_RAND_r4_2"] = 0.0129 - 3e-6
    u = A.decide(0.0129, c, LOOKS, 0.006, True, [], 203, {})
    r = A.decide(round(0.0129, 5), {k: round(v, 5) for k, v in c.items()}, LOOKS, 0.006, True, [], 203, {})
    assert u["VERDICT"] == "PASS" and r["VERDICT"] == "DOES NOT PASS"
    assert Bn.combine(u, r) == "DOES NOT PASS (rounding-sensitive)"
