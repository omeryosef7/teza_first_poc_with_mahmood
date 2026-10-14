"""End-to-end regression tests for p2b_analyze.analyze_rank + finalize on SYNTHETIC run data (review #2: #2, #3, #10).
I/O is monkeypatched; the real effect_fraction / recovery bootstrap / Holm / decide run."""
import os, random, sys, types
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import p2b_analyze as pa   # noqa: E402

DOMS = [f"d{i}" for i in range(23)]
KEYS = [(d, s) for d in DOMS for s in range(10)]


GOOD_CFG = {"bank": "data/boombness_prompts/boombness_prompt_bank_ts116m_basket_bomb.jsonl",
            "exclude_prompt_ids": "runargs/dcs_cont/exclude_basket_bomb_sow_validation.txt",
            "attn_impl": "eager", "dtype": "bfloat16"}


def _install(mp, collapse_cwonly=False, cw_bad_norm=False, missing=(), cw_missing=False, collapse_meanbias=False,
             zero_hooks=(), bad_cfg=(), host_of=None, gpu="NVIDIA RTX A5000"):
    rng = random.Random(0)
    cache = {}

    def y(arm):
        if arm in cache:
            return cache[arm]
        if arm == "KO_IDENT":
            v = dict(y("KO"))
        elif arm.startswith("KO_CAPOP"):
            v = dict(y(arm.replace("CAPOP", "CAND")))
        else:
            base = {"BASE": 0.7, "KO": 0.4, "KO_FULL": 0.55}
            if arm in base:
                f = lambda: base[arm] + 0.01 * rng.random()     # noqa: E731
            elif arm.startswith("KO_CAND"):
                f = lambda: 0.43 + 0.005 * rng.random()          # noqa: E731
            elif arm.startswith("KO_CWONLY"):
                f = lambda: 0.47 + 0.005 * rng.random()          # noqa: E731
            elif arm.startswith("BASE_"):
                f = lambda: 0.7                                  # noqa: E731
            else:
                f = lambda: 0.40 + 0.02 * rng.random()           # noqa: E731
            v = {k: f() for k in KEYS}
        cache[arm] = v
        return v

    def strict(tag, n, **kw):
        arm = tag.split("PFX_")[1]
        if any(f"_r{r}" in arm for r in missing) or (cw_missing and arm.startswith("KO_CW") and "ONLY" not in arm):
            raise SystemExit("missing " + tag)
        return arm
    mp.setattr(pa, "rederive", types.SimpleNamespace(strict_run_dir=strict))
    mp.setattr(pa.sa, "reference_key_set", lambda d, f: set(KEYS))
    mp.setattr(pa.sa, "arm_key_values", lambda d, assign, split: (y(d), None))
    mp.setattr(pa, "row_fields", lambda d: {k: {"option_mass": 0.001 if ((collapse_cwonly and d.startswith("KO_CWONLY")) or
                                                                         (collapse_meanbias and d == "KO_MEANBIAS")) else 0.3,
                                                "lc": -1.0, "lk": -2.0} for k in KEYS})

    def side(d):
        if d in ("BASE", "KO", "KO_FULL"):
            return None
        r = 1 if "_r1" in d else 4
        nf = {"L6.o_proj": 5.0 if (cw_bad_norm and d.startswith("KO_CWRAND")) else 1.0}
        return {"hook_calls": 0 if d in zero_hooks else 10, "module_fro": nf, "rank": r, "positions_tokens": [" basket"]}
    mp.setattr(pa, "sidecar", side)
    mp.setattr(pa, "run_prov", lambda d: {"job": "1", "host": (host_of(d) if host_of else "n-501"), "gpu": gpu})
    mp.setattr(pa, "arm_config", lambda d: {**GOOD_CFG, "exclude_prompt_ids": "WRONG.txt"} if d in bad_cfg else dict(GOOD_CFG))


def _run(ranks=(1, 4)):
    a = types.SimpleNamespace(nrand=61, nshuf=5, nder=15, capop=True, cw_nrand=61, cw_nder=15, addon=False, addon_nm=False,
                              codeword="basket", expect_excl=None, overlap=[], prefix="PFX", expect_n=230, allow_short=0, option_mass_floor=0.05, split="validation", n_boot=300)
    rows = []
    for r in ranks:
        try:
            rows.append(pa.analyze_rank(a, r, None))
        except SystemExit as e:
            rows.append({"rank": r, "verdict": "NOT ANALYZABLE: " + str(e)})
    return {x["rank"]: x for x in pa.finalize(rows)}


def test_baseline_passes_both(monkeypatch):
    _install(monkeypatch)
    out = _run()
    for r in (1, 4):
        assert out[r]["verdict"].startswith("PASS"), out[r]["verdict"]
        assert out[r]["verdict_secondary_CWONLY"].startswith("PASS"), out[r]["verdict_secondary_CWONLY"]


def test_incomplete_holm_family_is_not_a_pass(monkeypatch):
    _install(monkeypatch, missing=(4,))
    out = _run()
    assert out[4]["verdict"].startswith("NOT ANALYZABLE")
    assert out[1]["verdict"].startswith("INCOMPLETE FAMILY"), out[1]["verdict"]
    assert abs(out[1]["holm_p"] - 2 / 82) < 1e-12                     # missing rank entered as p=1, m=2
    assert out[1]["verdict_secondary_CWONLY"].split("[")[0].startswith("INCOMPLETE FAMILY")


def test_collapsed_cwonly_voids_secondary_only(monkeypatch):
    _install(monkeypatch, collapse_cwonly=True)
    out = _run()
    for r in (1, 4):
        assert out[r]["verdict_secondary_CWONLY"].startswith("VOID"), out[r]["verdict_secondary_CWONLY"]
        assert out[r]["verdict"].startswith("PASS")                    # primary unaffected


def test_cw_controls_wrong_norm_void_secondary_only(monkeypatch):
    _install(monkeypatch, cw_bad_norm=True)
    out = _run()
    for r in (1, 4):
        assert out[r]["verdict_secondary_CWONLY"].startswith("VOID")
        assert "norm not matched" in out[r]["verdict_secondary_CWONLY"]
        assert out[r]["verdict"].startswith("PASS")


def test_missing_cw_family_voids_secondary_not_primary(monkeypatch):
    _install(monkeypatch, cw_missing=True)
    out = _run()
    for r in (1, 4):
        assert out[r]["verdict"].startswith("PASS")
        assert out[r]["verdict_secondary_CWONLY"].startswith("VOID")


def test_addon_comparators(monkeypatch):
    _install(monkeypatch)
    a = types.SimpleNamespace(nrand=61, nshuf=5, nder=15, capop=True, cw_nrand=61, cw_nder=15, addon=True, addon_nm=False,
                              codeword="basket", expect_excl=None, overlap=[], prefix="PFX", expect_n=230, allow_short=0, option_mass_floor=0.05, split="validation", n_boot=300)
    row = pa.analyze_rank(a, 1, None)
    ad = row["addon"]
    assert "status" not in ad, ad
    assert ad["CAND_minus_MEANBIAS"]["point"] > 0                    # synthetic CAND 0.43 > control-like MEANBIAS ~0.41
    assert ad["rank_test_DER_raw_norm"]["n_controls"] == 15 and ad["rank_test_SHUF_raw_norm"]["n_controls"] == 5
    assert set(ad["KO_MEANBIAS"]) == {"stat", "recovery"}


def test_addon_collapsed_meanbias_suspends_wording(monkeypatch):
    _install(monkeypatch, collapse_meanbias=True)
    a = types.SimpleNamespace(nrand=61, nshuf=5, nder=15, capop=True, cw_nrand=61, cw_nder=15, addon=True, addon_nm=False,
                              codeword="basket", expect_excl=None, overlap=[], prefix="PFX", expect_n=230, allow_short=0, option_mass_floor=0.05, split="validation", n_boot=300)
    ad = pa.analyze_rank(a, 1, None)["addon"]
    assert any("KO_MEANBIAS: readout collapsed" in v for v in ad["void"])
    assert ad["input_conditional_wording_eligible_on_this_split"] is False


def test_cand_or_ident_zero_hooks_void(monkeypatch):
    _install(monkeypatch, zero_hooks=("KO_CAND_r1",))
    out = _run()
    assert out[1]["verdict"].startswith("VOID") and "never fired" in out[1]["verdict"]
    assert out[4]["verdict"].startswith("INCOMPLETE") and "PASS" not in out[4]["verdict"]
    monkeypatch.undo()
    _install(monkeypatch, zero_hooks=("KO_IDENT",))
    out = _run()
    assert all(out[r]["verdict"].startswith("VOID") for r in (1, 4))


def test_wrong_population_file_voids(monkeypatch):
    _install(monkeypatch, bad_cfg=("KO_RAND_r4_3",))
    out = _run()
    assert out[4]["verdict"].startswith("VOID") and "exclude file" in out[4]["verdict"]
    assert out[1]["verdict"].startswith("INCOMPLETE") and "PASS" not in out[1]["verdict"]
    monkeypatch.undo()
    _install(monkeypatch, bad_cfg=("KO",))
    out = _run()
    assert out[1]["verdict"].startswith("VOID") and out[1]["verdict_secondary_CWONLY"].startswith("VOID")


def test_wording_never_eligible_on_train(monkeypatch):
    _install(monkeypatch)
    a = types.SimpleNamespace(nrand=61, nshuf=5, nder=15, capop=True, cw_nrand=61, cw_nder=15, addon=True, addon_nm=False,
                              codeword="basket", expect_excl="runargs/dcs_cont/exclude_basket_bomb_sow_validation.txt", overlap=[],
                              prefix="PFX", expect_n=230, allow_short=0, option_mass_floor=0.05, split="train", n_boot=300)
    ad = pa.analyze_rank(a, 1, None)["addon"]
    assert ad["CAND_minus_MEANBIAS"]["ci95"][0] > 0 and ad["input_conditional_wording_eligible_on_this_split"] is False


def _run_ov(overlap):
    a = types.SimpleNamespace(nrand=61, nshuf=5, nder=15, capop=True, cw_nrand=61, cw_nder=15, addon=False, addon_nm=False,
                              codeword="basket", expect_excl=None, overlap=overlap, prefix="PFX", expect_n=230,
                              allow_short=0, option_mass_floor=0.05, split="validation", n_boot=300)
    return {x["rank"]: x for x in pa.finalize([pa.analyze_rank(a, r, None) for r in (1, 4)])}


def test_cross_host_cell_needs_overlap(monkeypatch, tmp_path):
    _install(monkeypatch, host_of=lambda d: "n-503" if d in ("BASE", "KO", "KO_FULL", "KO_IDENT") else "n-501")
    out = _run_ov([])
    assert all(out[r]["verdict"].startswith("VOID") and "without an OVERLAP_OK" in out[r]["verdict"] for r in (1, 4))
    ok = tmp_path / "ov.json"
    ok.write_text('{"verdict": "OVERLAP_OK", "pairs": [{"orig": {"host": "n-503"}, "overlap": {"host": "n-501"}}]}')
    bad = tmp_path / "ovbad.json"
    bad.write_text('{"verdict": "OVERLAP_FAIL", "pairs": [{"orig": {"host": "n-503"}, "overlap": {"host": "n-501"}}]}')
    assert _run_ov([str(bad)])[1]["verdict"].startswith("VOID")
    out = _run_ov([str(ok)])
    assert out[1]["verdict"].startswith("PASS") and out[1]["arm_provenance"]["KO"]["host"] == "n-503"


def test_non_a5000_voids(monkeypatch):
    _install(monkeypatch, gpu="NVIDIA L40S")
    assert _run_ov([])[1]["verdict"].startswith("VOID")


def test_addon_nm_descriptive(monkeypatch):
    _install(monkeypatch)
    a = types.SimpleNamespace(nrand=61, nshuf=5, nder=15, capop=True, cw_nrand=61, cw_nder=15, addon=False, addon_nm=True,
                              codeword="basket", expect_excl=None, overlap=[], prefix="PFX", expect_n=230,
                              allow_short=0, option_mass_floor=0.05, split="validation", n_boot=300)
    row = pa.analyze_rank(a, 4, None)
    nm = row["addon_nm"]
    assert "status" not in nm and nm["never_unlocks_wording"] is True and nm["void"] == []
    assert "CAND_minus_MEANBIAS_NM" in nm and "addon" not in row
