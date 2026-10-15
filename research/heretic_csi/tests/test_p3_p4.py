import os, sys, torch
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import p3_svd_analysis as p3


def test_svd_factored_matches_dense():
    torch.manual_seed(0)
    A, B = torch.randn(3, 50, dtype=torch.float64), torch.randn(40, 3, dtype=torch.float64)
    U, S, V = p3.svd_factored(A, B)
    dense = (B @ A).double()
    assert torch.allclose(U @ torch.diag(S) @ V.t(), dense, atol=1e-8)
    assert torch.allclose(S, torch.linalg.svdvals(dense)[:3], atol=1e-8)


def test_head_mass_sums_to_one_and_localizes():
    A = torch.zeros(2, 4096); A[:, 256:384] = torch.randn(2, 128)   # head 2 only
    B = torch.randn(4096, 2)
    hm = p3.head_mass(A, B)
    assert abs(sum(hm) - 1) < 1e-9 and hm[2] > 0.999999


def test_eff_rank():
    assert abs(p3.eff_rank(torch.tensor([1.0, 0, 0])) - 1) < 1e-9
    assert abs(p3.eff_rank(torch.tensor([1.0, 1.0])) - 2) < 1e-9


def test_p4_head_restriction_embeds_zero_outside_heads():
    import p4_head_fit as p4, p2b_operator as po
    torch.manual_seed(0)
    n, din, dout = 40, 4096, 16
    s_in = torch.randn(n, din); t_in = s_in.clone()
    W = torch.randn(dout, din) * 0.01
    s_out = s_in @ W.t(); t_out = s_out + torch.randn(n, dout)
    m = po.PairedIO("L10.o_proj", s_in, s_out, t_in, t_out, torch.randn(10, din))
    fac = p4.fit_variant([m], po.FitCfg(rank=2, n_steps=2), heads=[2, 5])
    A, B = fac["L10.o_proj"]
    keep = p4.cols([2, 5])
    mask = torch.ones(din, dtype=torch.bool); mask[keep] = False
    assert A.shape == (2, din) and float(A[:, mask].abs().max()) == 0.0 and float(A[:, keep].abs().max()) > 0
    assert list(keep[:3]) == [256, 257, 258] and int(keep[128]) == 640


def test_p4_random_heads_disjoint_from_top8():
    import random, p4_head_fit as p4
    for j in range(60):
        hs = random.Random(4000 + 100 + j).sample(p4.NON_TOP8, 8)
        assert not set(hs) & set(p4.TOP8) and len(set(hs)) == 8


def test_p4v2_normc_hits_target_and_beats_rescale():
    import p4_head_fit_v2 as v2, p2b_operator as po
    torch.manual_seed(1)
    n, din, dout = 60, 64, 32
    s_in = torch.randn(n, din); W = torch.randn(dout, din) * 0.1
    s_out = s_in @ W.t(); t_out = s_out + (s_in[:, :3] @ torch.randn(3, dout))
    m = po.PairedIO("L10.o_proj", s_in, s_out, s_in.clone(), t_out, torch.randn(20, din))
    cfg = po.FitCfg(rank=2, n_steps=5)
    raw = po.fit_factored([m], cfg)
    target = {"L10.o_proj": 0.5 * po.fro_norm(*raw["L10.o_proj"])}
    nc = v2.fit_normc([m], cfg, raw, target)
    assert abs(po.fro_norm(*nc["L10.o_proj"]) - target["L10.o_proj"]) < 1e-4
    resc = po.rescale_to(raw, target)
    assert po.gap_closure([m], nc)["net"] >= po.gap_closure([m], resc)["net"] - 1e-6


def _row(r, p_raw, p_nc, ci_lo=0.01):
    return {"rank": r, "primary": True, "gates": {"manipulation_ok": True, "instrument_ok": True}, "void": [],
            "recovery_TOP8": {"status": "ok", "point": 0.1, "ci95": [ci_lo, 0.2]},
            "rank_test_RAW": {"p": p_raw, "n_controls": 60}, "rank_test_NC": {"p": p_nc, "n_controls": 60},
            "p_IUT": max(p_raw, p_nc)}


def test_p4v2_incomplete_family_never_passes():
    import p4_analyze_v2 as v
    rows = v.finalize([_row(1, 1 / 61, 1 / 61)])
    assert rows[0]["verdict"].startswith("INCOMPLETE")
    rows = v.finalize([_row(1, 1 / 61, 1 / 61), {"rank": 4, "verdict": "NOT ANALYZABLE: x"}])
    assert rows[0]["verdict"].startswith("INCOMPLETE")


def test_p4v2_iut_requires_both_families():
    import p4_analyze_v2 as v
    rows = v.finalize([_row(1, 1 / 61, 0.5), _row(4, 1 / 61, 1 / 61)])
    v1 = [x for x in rows if x["rank"] == 1][0]["verdict"]
    v4 = [x for x in rows if x["rank"] == 4][0]["verdict"]
    assert not v1.startswith("PASS") and v4.startswith("PASS")
    rows = v.finalize([_row(1, 1 / 61, 1 / 61), _row(4, 1 / 61, 1 / 61, ci_lo=-0.01)])
    assert [x for x in rows if x["rank"] == 4][0]["verdict"].startswith("DOES NOT PASS")


def test_p4v2_void_or_gatefail_rank_counts_as_missing():
    import p4_analyze_v2 as v
    r1 = _row(1, 1 / 61, 1 / 61); r1["void"] = ["KO_TOP8: readout collapsed"]
    rows = v.finalize([r1, _row(4, 0.03, 0.03)])
    assert rows[0]["verdict"].startswith("VOID") and rows[1]["verdict"].startswith("INCOMPLETE")
    r1 = _row(1, 1 / 61, 1 / 61); r1["gates"]["instrument_ok"] = False
    rows = v.finalize([r1, _row(4, 0.03, 0.03)])
    assert rows[0]["verdict"].startswith("CANNOT") and rows[1]["verdict"].startswith("INCOMPLETE")
    r1 = _row(1, 1 / 61, 1 / 61); r1["recovery_TOP8"] = {"status": "degenerate", "reason": "den~0"}
    rows = v.finalize([r1, _row(4, 0.03, 0.03)])
    assert rows[0]["verdict"].startswith("CANNOT") and rows[1]["verdict"].startswith("INCOMPLETE")
    rows = v.finalize([_row(1, 1 / 61, 1 / 61), _row(4, 0.03, 0.03)])     # both valid: normal Holm
    assert [x for x in rows if x["rank"] == 4][0]["verdict"].startswith("PASS")


def test_p4v1_void_rank_counts_as_missing():
    import ast, inspect, p4_analyze as v1
    src = inspect.getsource(v1.main)
    assert "_valid(x)" in src and "not _valid(x)" in src


def test_p4v2_sidecar_checks_sha_and_hooks():
    import p4_analyze_v2 as v
    good = {"hook_calls": 100, "factors_sha16": "aaaa", "factors_file": "f.pt"}
    assert v.sidecar_checks({"KO_TOP8": dict(good), "KO_IDENT": dict(good)}, {"KO_TOP8": "aaaa", "KO_IDENT": "aaaa"}) == []
    # same filename, different content -> VOID
    bad = v.sidecar_checks({"KO_TOP8": {**good, "factors_sha16": "bbbb"}}, {"KO_TOP8": "aaaa"})
    assert bad and "sha16" in bad[0]
    # hooks never fired on TOP8 or on the identity arm -> VOID
    assert v.sidecar_checks({"KO_TOP8": {**good, "hook_calls": 0}}, {"KO_TOP8": "aaaa"})
    assert v.sidecar_checks({"KO_IDENT": {**good, "hook_calls": 0}}, {"KO_IDENT": "aaaa"})
    assert v.sidecar_checks({"KO_TOP8": None}, {"KO_TOP8": "aaaa"})
    assert v.sidecar_checks({"KO_X": dict(good)}, {})            # unregistered arm -> VOID


def test_p4_incomplete_verdicts_never_contain_pass():
    import p4_analyze_v2 as v
    r1 = _row(1, 1 / 61, 1 / 61); r1["void"] = ["x"]
    rows = v.finalize([r1, _row(4, 0.01, 0.01)])
    inc = [x["verdict"] for x in rows if x["verdict"].startswith("INCOMPLETE")]
    assert inc and all("PASS" not in s for s in inc)
    rows = v.finalize([_row(4, 0.01, 0.01)])
    assert "PASS" not in rows[0]["verdict"]
    import inspect, p4_analyze as v1
    for line in inspect.getsource(v1.main).splitlines():
        if "INCOMPLETE FAMILY" in line:
            assert "PASS" not in line


def test_p3_minimal_k_rule_and_boot_ratio():
    import p3_analyze as p
    t = {1: {"holm_p": 0.04, "retention": {"ci95": [0.4, 0.9]}}, 2: {"holm_p": 0.03, "retention": {"ci95": [0.6, 1.1]}}}
    assert p.minimal_k(t) == 2
    t[1]["retention"]["ci95"] = [0.55, 0.9]
    assert p.minimal_k(t) == 1
    t = {1: {"holm_p": 0.2, "retention": {"ci95": [0.9, 1.0]}}}
    assert p.minimal_k(t) is None
    doms = [f"d{i}" for i in range(10)]
    r = p.boot_ratio(doms, {d: 1.0 for d in doms}, {d: 2.0 for d in doms}, n=200)
    assert abs(r["point"] - 0.5) < 1e-12 and abs(r["ci95"][0] - 0.5) < 1e-12


def test_p3_reexp_and_sha_checks():
    import p3_analyze as p
    keys = [(f"d{i}", s) for i in range(5) for s in range(2)]
    ko = {k: 0.2 for k in keys}; cand = {k: 0.3 for k in keys}
    r, v = p.reexp_check(keys, dict(cand), dict(ko), dict(cand), dict(ko), "A5000", "A5000")
    assert v == [] and abs(r["stat_REEXP"] - 0.1) < 1e-12
    bad = dict(cand); bad[keys[0]] = 0.35                      # one row off by 0.05 > ROW_TOL
    assert p.reexp_check(keys, bad, dict(ko), dict(cand), dict(ko), "A5000", "A5000")[1]
    shifted = {k: 0.302 for k in keys}                          # stat off by 0.002 > STAT_TOL
    assert any("stat diff" in x for x in p.reexp_check(keys, shifted, dict(ko), dict(cand), dict(ko), "A5000", "A5000")[1])
    ko2 = dict(ko); ko2[keys[3]] = 0.2001                       # own KO differs from reference KO
    assert p.reexp_check(keys, dict(cand), ko2, dict(cand), dict(ko), "A5000", "A5000")[1]
    assert p.reexp_check(keys, dict(cand), dict(ko), dict(cand), dict(ko), "A5000", "L40S")[1]   # GPU mismatch -> VOID
    good = {"hook_calls": 5, "factors_sha16": "t"}
    assert p.sidecar_sha_checks({"KO_TOP1": dict(good)}, {"KO_TOP1": "t"}) == []
    assert p.sidecar_sha_checks({"KO_TOP1": {**good, "factors_sha16": "u"}}, {"KO_TOP1": "t"})
    assert p.sidecar_sha_checks({"KO_IDENT": {**good, "hook_calls": 0}}, {"KO_IDENT": "t"})


# ---- PREREG_P4_AMENDMENT_6 (review #10 M6, M7) -- mutation tests on synthetic data ----
def _stat(cand, ctrl):
    s = {"KO_TOP8": cand}
    s.update({f"c{i}": v for i, v in enumerate(ctrl)})
    return s, [f"c{i}" for i in range(len(ctrl))]


def test_a6_collapsed_controls_are_never_a_free_win():
    import p4_analyze_v2 as v, p2b_analyze as pa
    # TOP8 beats 10 healthy controls (strictly first) and 10 COLLAPSED controls with absurdly low stats
    stat, fam = _stat(0.10, [0.01] * 10 + [-0.90] * 10)
    collapsed = fam[10:]
    plain = pa.rank_p(stat, "KO_TOP8", fam)
    cons = v.conservative_rank_p(stat, "KO_TOP8", fam, collapsed)
    assert plain["p"] == 1 / 21                       # old rule: collapsed controls hand TOP8 a free win
    assert cons["p"] == 11 / 21 and cons["n_collapsed_in_family"] == 10   # new rule: they count as >= candidate
    assert cons["p_plain"] == 1 / 21 and cons["p_without_collapsed"] == 1 / 11
    # mutation: with NO collapsed controls the conservative p equals the plain p
    assert v.conservative_rank_p(stat, "KO_TOP8", fam, [])["p"] == plain["p"]
    # mutation: a collapsed control that would have been >= candidate anyway is not double counted
    stat2, fam2 = _stat(0.10, [0.5, 0.01, 0.01])
    assert v.conservative_rank_p(stat2, "KO_TOP8", fam2, [fam2[0]])["p"] == 2 / 4


def test_a6_collapsed_family_over_10pct_is_void_and_decisive_p_cannot_pass():
    import p4_analyze_v2 as v
    stat, fam = _stat(0.10, [0.01] * 54 + [-0.9] * 6)               # 6/60 = 10% (boundary: allowed)
    t = v.conservative_rank_p(stat, "KO_TOP8", fam, fam[54:])
    assert v.collapse_void("RAW", t, 60) is None
    t = v.conservative_rank_p(stat, "KO_TOP8", fam, fam[53:])       # 7/60 > 10%
    assert v.collapse_void("RAW", t, 60) is not None
    # the conservative decisive p can no longer reach a PASS when many controls collapsed
    stat, fam = _stat(0.10, [0.01] * 30 + [-0.9] * 30)
    t = v.conservative_rank_p(stat, "KO_TOP8", fam, fam[30:])
    rows = v.finalize([_row(1, t["p"], t["p"]), _row(4, t["p"], t["p"])])
    assert not any(x["verdict"].startswith("PASS") for x in rows)


def test_a6_verdict_labels_carry_split_and_role():
    import p4_analyze_v2 as v
    tr = v.split_label("train", "basket"); va = v.split_label("validation", "basket"); bu = v.split_label("validation", "button")
    assert "TRAIN-K4 (in-sample)" in tr and "SOLE confirmatory" in tr
    assert "VALIDATION" in va and "SOLE confirmatory" in va and "in-sample" not in va
    assert "SECONDARY" in bu and "DESCRIPTIVE" in bu and "SOLE" not in bu
    rows = v.finalize([_row(1, 1 / 61, 1 / 61), _row(4, 1 / 61, 1 / 61)], tr)
    assert all(x["verdict"].startswith("[TRAIN-K4 (in-sample)") and "PASS" in x["verdict"] for x in rows)
    # labels never smuggle 'PASS' into INCOMPLETE / non-pass verdicts
    r1 = _row(1, 1 / 61, 1 / 61); r1["void"] = ["x"]
    rows = v.finalize([r1, _row(4, 0.01, 0.01)], bu)
    assert all("PASS" not in x["verdict"] for x in rows) and all(x["verdict"].startswith("[VALIDATION; SECONDARY") for x in rows)
    # default (no label) behaviour unchanged for older callers
    rows = v.finalize([_row(1, 1 / 61, 1 / 61), _row(4, 1 / 61, 1 / 61)])
    assert all(x["verdict"].startswith("PASS") for x in rows)


def test_a6_main_applies_split_label():
    import inspect, p4_analyze_v2 as v
    src = inspect.getsource(v.main)
    assert "finalize(rows, split_label(a.split, a.codeword))" in src
