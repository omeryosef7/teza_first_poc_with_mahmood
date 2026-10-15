"""Generic powered read (PR-HCSI-S199): synthetic decide()/combine() + real-data equivalence on ALREADY-READ jobs
(basket r1 968532 vs its frozen analyzer output; button r4 S-084 jobs reproduce the S-084 PASS)."""
import json, os, sys
import pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import p2a_powered_read as G

L = {"r4": 0.0175, "r16": 0.1754}


def C(n=190, shuf=None):
    c = {f"KO_RAND_r1_{i}": -1e-4 * i for i in range(n)}
    for j, v in enumerate(shuf if shuf is not None else [0.001] * 10):
        c[f"KO_SHUF_r1_{j}"] = v
    return c


def test_decide_rules():
    ok = G.decide(0.03, C(), L, "r1", "KO_SHUF_r1_", 0.01, True, [], 133, 133, {})
    assert ok["VERDICT"] == "PASS" and ok["rank"] == 1
    # Holm with looks {r4 .0175, r16 .1754}: r1 p_ext must be smallest and *3 < .05, and r4's .0175*2 < .05 doesn't matter
    c = C(); c["KO_RAND_r1_0"] = c["KO_RAND_r1_1"] = 0.05
    assert G.decide(0.03, c, L, "r1", "KO_SHUF_r1_", 0.01, True, [], 133, 133, {})["VERDICT"] == "PASS"   # 3/201 -> .0448
    c["KO_RAND_r1_2"] = 0.05
    assert G.decide(0.03, c, L, "r1", "KO_SHUF_r1_", 0.01, True, [], 133, 133, {})["VERDICT"] == "DOES NOT PASS"
    assert G.decide(0.03, C(shuf=[0.001] * 9 + [0.031]), L, "r1", "KO_SHUF_r1_", 0.01, True, [], 133, 133, {})["VERDICT"] == "DOES NOT PASS"
    assert G.decide(0.03, C(), L, "r1", "KO_SHUF_r1_", -0.001, True, [], 133, 133, {})["VERDICT"] == "DOES NOT PASS"
    assert G.decide(0.03, C(), L, "r1", "KO_SHUF_r1_", 0.01, True, ["x"], 133, 133, {})["VERDICT"].startswith("VOID")
    d = G.decide(0.03, C(), L, "r1", "KO_SHUF_r1_", 0.01, True, [], 130, 133, {"KO_RAND_r1_99": 3})
    assert d["row_set"]["deviation"] == -3 and d["row_set"]["arms_with_dropped_keys"] == ["KO_RAND_r1_99"]


def test_combine():
    P, F, V = {"VERDICT": "PASS"}, {"VERDICT": "DOES NOT PASS"}, {"VERDICT": "VOID: z"}
    assert G.combine(P, P) == "PASS" and G.combine(F, F) == "DOES NOT PASS"
    assert G.combine(P, F) == G.combine(F, P) == "DOES NOT PASS (rounding-sensitive)"
    assert G.combine(P, V).startswith("VOID")


REF = os.path.join(G.ROOT, "reports/heretic_csi/hcsi_p2a_basket_r1.json")


@pytest.mark.skipif(not os.path.exists(REF), reason="basket r1 VAL analyzer output absent")
def test_basket_r1_original_equivalence():
    d = json.load(open(REF)); assert d["split"] == "validation" and d["require_slurm_job"] == ["968532"]
    A = G._ana()
    ctrl = [f"KO_RAND_r1_{i}" for i in range(46)] + [f"KO_SHUF_r1_{j}" for j in range(10)]
    arms = ["BASE", "KO", "KO_SELF", "KO_FULL", "KO_CAND_r1"] + ctrl
    st, n, lost, doms, diffs = G.stats(A, "basket", arms, ["968532"], "base")
    assert n == d["n_keys_common"] == 133
    ctr = d["control_recovery_distribution"]
    assert abs(round(st["KO_CAND_r1"], 5) - ctr["candidate"]) <= 1.01e-5
    for k, v in ctr["controls"].items():
        assert abs(round(st[k], 5) - v) <= 1.01e-5, k
    dec = G.decide(st["KO_CAND_r1"], {k: st[k] for k in ctrl}, {"x": 1}, "r1", "KO_SHUF_r1_", 1, True, [], n, 133, lost)
    assert dec["rank"] == d["verdict_basis"]["candidate_rank"] == 1
    # paired-floor sensitivity on the original 56 (cf. F3 S-052: 2/57): reported, not asserted
    stp, np_, _, _, _ = G.stats(A, "basket", arms, ["968532"], "paired")
    dp = G.decide(stp["KO_CAND_r1"], {k: stp[k] for k in ctrl}, {"x": 1}, "r1", "KO_SHUF_r1_", 1, True, [], np_, 133, {})
    print("paired-floor original-56 rank", dp["rank"], "rows", np_)


S084 = os.path.join(G.ROOT, "reports/heretic_csi/P2A_BUTTON_R4_POWERED.json")


@pytest.mark.skipif(not os.path.exists(S084), reason="S-084 read absent")
def test_reproduces_s084_button():
    p = json.load(open(S084))
    A = G._ana()
    ctrl = [f"KO_RAND_r4_{i}" for i in range(190)] + [f"KO_SHUF_r4_{j}" for j in range(10)]
    arms = ["BASE", "KO", "KO_SELF", "KO_FULL", "KO_CAND_r4"] + ctrl
    st, n, lost, _, _ = G.stats(A, "button", arms, ["1022698", "1027577", "1032110"], "base")
    assert n == 203 and abs(st["KO_CAND_r4"] - p["candidate_stat_unrounded"]) < 1e-12
    dec = G.decide(st["KO_CAND_r4"], {k: st[k] for k in ctrl}, {"r1": 0.2456, "r16": 0.1754}, "r4", "KO_SHUF_r4_",
                   p["candidate_minus_KO"]["ci95"][0], True, [], n, 203, lost)
    assert dec["VERDICT"] == p["decision_unrounded"]["VERDICT"] == "PASS" and dec["rank"] == p["decision_unrounded"]["rank"]


# ---- S-199 AMENDMENT 1 (review #10 M5): row-set floor => UNDERPOWERED, descriptive companions ----
def _passing(**kw):
    a = dict(cand=0.03, controls=C(), looks=L, look_key="r1", shuf_prefix="KO_SHUF_r1_", ci_lo=0.01, gates_ok=True,
             void=[], n_keys_common=133, expected_rows=133, arms_lost={}, n_domains=23, min_rows=100, min_domains=21)
    a.update(kw); return G.decide(**a)


def test_rowset_floor_blocks_pass():
    assert _passing()["VERDICT"] == "PASS"
    d = _passing(n_keys_common=90)                       # 133 -> 90 rows must NOT give PASS
    assert d["VERDICT"].startswith("UNDERPOWERED") and d["rank"] == 1 and "common rows 90 < 100" in d["VERDICT"]
    assert _passing(n_keys_common=99)["VERDICT"].startswith("UNDERPOWERED")
    assert _passing(n_keys_common=100)["VERDICT"] == "PASS"            # boundary inclusive
    d = _passing(n_domains=20)
    assert d["VERDICT"].startswith("UNDERPOWERED") and "domains 20 < 21" in d["VERDICT"]
    assert _passing(n_domains=21)["VERDICT"] == "PASS"
    both = _passing(n_keys_common=80, n_domains=18)
    assert both["VERDICT"].count("<") == 2


def test_underpowered_beats_does_not_pass_and_void_beats_underpowered():
    # a would-be FAIL on a shrunken row set is still UNDERPOWERED (not a null), a VOID stays VOID
    assert _passing(n_keys_common=90, ci_lo=-1)["VERDICT"].startswith("UNDERPOWERED")
    assert _passing(n_keys_common=90, void=["x"])["VERDICT"].startswith("VOID")


def test_combine_propagates_underpowered():
    U, P, F, V = {"VERDICT": "UNDERPOWERED (row set): x"}, {"VERDICT": "PASS"}, {"VERDICT": "DOES NOT PASS"}, {"VERDICT": "VOID: z"}
    assert G.combine(U, P).startswith("UNDERPOWERED") and G.combine(P, U).startswith("UNDERPOWERED")
    assert G.combine(F, U).startswith("UNDERPOWERED")
    assert G.combine(U, V).startswith("VOID")


def test_no_floor_default_unchanged():
    d = G.decide(0.03, C(), L, "r1", "KO_SHUF_r1_", 0.01, True, [], 90, 133, {})        # S-084 call signature
    assert d["VERDICT"] == "PASS" and d["underpowered_reasons"] == []


@pytest.mark.skipif(not os.path.exists(REF), reason="basket r1 VAL analyzer output absent")
def test_companions_on_original_job():
    A = G._ana()
    orig = [f"KO_RAND_r1_{i}" for i in range(46)] + [f"KO_SHUF_r1_{j}" for j in range(10)]
    arms = ["BASE", "KO", "KO_SELF", "KO_FULL", "KO_CAND_r1"] + orig
    st, n, lost, doms, _ = G.stats(A, "basket", arms, ["968532"], "base")
    ii, iii = G.companions(A, "basket", 1, ["968532"], st, "KO_CAND_r1", orig)
    assert ii["rank"] == 1 and ii["n_controls"] == 56 and ii["p"] == pytest.approx(1 / 57)
    assert iii["n_controls"] == 56 and 0 <= iii["n_candidate_gt_control"] <= 56
    assert iii["min_delta"] <= iii["median_delta"] <= iii["max_delta"] and iii["rows_per_control_min_max"][0] >= 100
    assert len(iii["worst_controls"]) == 5
    print("companion iii on original:", iii["n_candidate_gt_control"], "/ 56 candidate>control; rows", iii["rows_per_control_min_max"])
