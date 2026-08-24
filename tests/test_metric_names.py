"""P0.2e — the four ambiguous metric names, and what each producer now emits beside them.

WHAT THIS PINS. Four names in the sprint log do not say what they measure. Three of them are real
code fields and are fixed here by ADDING an explicit sibling next to the historical key; the fourth
turned out not to exist in code at all. In name order:

  (a) `uniq_frac` -- HAD NO PRODUCER: `grep -rn uniq_frac src/ scripts/` returns nothing, it is a
      hand-written markdown column whose quantity is distinct completion LENGTHS. `coherence_gate`
      (the module that computes every other degeneracy statistic on the same generations) now emits
      BOTH `n_distinct_completion_lengths_frac` (the historical quantity) and
      `n_distinct_completions_frac` (distinct by sha256 of the text -- hashed, never stored).
  (b) `delta_pooled` -- three writers, TWO meanings: a mean-score delta in `analyze_external_arms`,
      an ASR delta wherever the field is the 0/1 flag. Each value now also appears as
      `delta_pooled_mean_score` or `delta_pooled_asr`, with a `delta_pooled_units` enum.
  (c) a bare `dose` that says neither variance nor norm nor residual. Every writer of the CENTRED
      cell-mean variance fraction now also emits `<prefix>_cellmean_variance_frac_centred` plus a
      `dose_units` enum. (Mixing this with the UN-CENTRED residual the hook acts on is what turned
      a real 6.60x gap into a fake 1.17x in prev-C-6, so the distinction is load-bearing.)
  (d) "a `spearman` field that is really Pearson on log2(n_examples)" -- REFUTED, see the (d) test.

BACKWARD COMPATIBILITY IS THE POINT: every historical key is retained with its value unchanged, and
each consumer prefers the explicit key with a fallback, so pre-P0.2e artifacts still read.

RED/GREEN. `_stripped()` re-executes a producer's real source with the new key removed, which is the
pre-fix behaviour; the `*_pre_fix_*` tests below run the same assertions against it and demonstrate
they fail there. Nothing is re-typed: every formula is imported from the module under test.
"""
import importlib.util
import json
import os
import sys

import pytest

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
SRCB = os.path.join(REPO, "src", "boombness")
sys.path.insert(0, SRCB)

import analyze_external_arms as X        # noqa: E402
import coherence_gate                    # noqa: E402
import insubspace_null_test as I         # noqa: E402


def _stripped(tmp_path, filename, modname, old, new):
    """The module's REAL source with one substring replaced -- used to remove a new key."""
    src = open(os.path.join(SRCB, filename)).read()
    assert old in src, f"anchor not found in {filename}: {old!r}"
    dst = tmp_path / filename
    dst.write_text(src.replace(old, new, 1))
    spec = importlib.util.spec_from_file_location(modname, str(dst))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[modname] = mod
    spec.loader.exec_module(mod)
    return mod


# --------------------------------------------------------------------------- #
# (a) uniq_frac
# --------------------------------------------------------------------------- #
LONG_OK = ("The mechanism proceeds through several distinct stages and each one contributes a "
           "different measurable quantity to the final outcome under study here today.")


def _run_dir(tmp_path, name, texts):
    d = tmp_path / name
    d.mkdir()
    with open(d / "gens.jsonl", "w") as f:
        for i, t in enumerate(texts):
            f.write(json.dumps({"prompt_id": f"p{i}", "condition": "natural_doublespeak",
                                "generation": t}) + "\n")
    with open(d / "results.jsonl", "w") as f:
        for i in range(len(texts)):
            f.write(json.dumps({"prompt_id": f"p{i}", "condition": "natural_doublespeak",
                                "readout": "generation", "gen_truncated": False}) + "\n")
    return str(d)


def test_a_uniq_frac_still_has_no_producer_anywhere_in_the_tree():
    """The premise of (a): nothing in src/ or scripts/ EMITS or READS a `uniq_frac` field.

    Prose mentions are fine (this repo documents the defect); what must not exist is the field, so
    the scan looks for the name as a dict key, an identifier or an index rather than as text.
    """
    hits = []
    for root in ("src", "scripts"):
        for dirpath, _dirs, files in os.walk(os.path.join(REPO, root)):
            for fn in files:
                if not fn.endswith(".py"):
                    continue
                p = os.path.join(dirpath, fn)
                with open(p, errors="ignore") as fh:
                    src = fh.read()
                if any(t in src for t in ('"uniq_frac"', "'uniq_frac'", "uniq_frac =",
                                          "uniq_frac=", "uniq_frac[", "uniq_frac(")):
                    hits.append(os.path.relpath(p, REPO))
    assert hits == []


def test_a_both_uniqueness_names_are_emitted_and_are_different_quantities():
    # 4 completions: two share a LENGTH but differ in TEXT. Lengths: 3 distinct of 4; texts: 4 of 4.
    u = coherence_gate.completion_uniqueness(["aaa", "aab", "cccc", "ddddd"])
    assert u["n_distinct_completion_lengths_frac"] == 3 / 4
    assert u["n_distinct_completions_frac"] == 4 / 4


def test_a_lengths_frac_never_exceeds_completions_frac():
    """Documented relationship: different length implies different text, so lengths <= completions."""
    for texts in (["a", "bb", "ccc"], ["x"] * 9, ["aa", "ab", "ba", "bb", "c"], []):
        u = coherence_gate.completion_uniqueness(texts)
        if not texts:
            assert u["n_distinct_completion_lengths_frac"] is None
            assert u["n_distinct_completions_frac"] is None
            continue
        assert u["n_distinct_completion_lengths_frac"] <= u["n_distinct_completions_frac"]


def test_a_the_hash_is_not_the_text():
    """The content-uniqueness key must be derived from a hash: no generation may be stored."""
    u = coherence_gate.completion_uniqueness(["secret text one", "secret text two"])
    assert all(isinstance(v, float) for v in u.values())


def test_a_assess_reports_both_keys_on_a_real_run(tmp_path):
    d = _run_dir(tmp_path, "healthy", [LONG_OK + f" run {i}" for i in range(40)])
    a = coherence_gate.assess(d, condition="natural_doublespeak")
    assert a["n_distinct_completions_frac"] == 1.0
    assert a["n_distinct_completion_lengths_frac"] <= 1.0
    # denominator is the reported population, not the scorable subset
    assert a["n_considered"] == 40
    # NOT gated: these are reported only, so no committed verdict can move.
    assert a["coherent"] is True
    assert "n_distinct_completions_frac" not in " ".join(a["checks_applied"])


def test_a_pre_fix_source_emits_neither_key(tmp_path):
    """RED: with the new emission removed, the assertions above fail."""
    old = _stripped(tmp_path, "coherence_gate.py", "pre_p02e_coherence_gate",
                    "**completion_uniqueness(texts),", "")
    d = _run_dir(tmp_path, "healthy_prefix", [LONG_OK + f" run {i}" for i in range(40)])
    a = old.assess(d, condition="natural_doublespeak")
    assert "n_distinct_completions_frac" not in a
    assert "n_distinct_completion_lengths_frac" not in a
    with pytest.raises(KeyError):
        a["n_distinct_completions_frac"]


# --------------------------------------------------------------------------- #
# (b) delta_pooled
# --------------------------------------------------------------------------- #
def test_b_score_delta_gets_the_mean_score_sibling():
    r = X.delta_pooled_fields(0.2401, X.SCORE)
    assert r["delta_pooled"] == 0.2401                      # historical key, unchanged
    assert r["delta_pooled_mean_score"] == r["delta_pooled"]
    assert r["delta_pooled_units"] == "mean_score"
    assert "delta_pooled_asr" not in r                      # exactly one explicit key


def test_b_flag_delta_gets_the_asr_sibling():
    r = X.delta_pooled_fields(-0.125, X.FLAG)
    assert r["delta_pooled"] == -0.125
    assert r["delta_pooled_asr"] == r["delta_pooled"]
    assert r["delta_pooled_units"] == "asr"
    assert "delta_pooled_mean_score" not in r
    assert set(X.DELTA_POOLED_UNITS) == {"mean_score", "asr"}


def test_b_the_two_writers_that_take_a_field_route_it_through_the_same_helper():
    """consolidate_deliverables and analyze_control_recheck must not re-type the rule."""
    for fn in ("consolidate_deliverables.py", "analyze_control_recheck.py"):
        src = open(os.path.join(SRCB, fn)).read()
        assert "from analyze_external_arms import delta_pooled_fields" in src
        assert "delta_pooled_fields(" in src


def test_b_real_paired_delta_carries_both_names():
    common = ["p1", "p2"]
    arm = {p: {X.SCORE: 0.8, "domain": "d1"} for p in common}
    base = {p: {X.SCORE: 0.2, "domain": "d1"} for p in common}
    out = X.paired_delta(arm, base, common)
    assert out["delta_pooled"] == pytest.approx(0.6)
    assert out["delta_pooled_mean_score"] == pytest.approx(0.6)
    assert out["delta_pooled_units"] == "mean_score"


def test_b_consumer_prefers_the_explicit_key():
    rec = {"delta_pooled": 0.1, "delta_pooled_mean_score": 0.2, "delta_pooled_units": "mean_score"}
    assert X.read_delta_pooled(rec, "mean_score") == 0.2
    assert X.read_delta_pooled(rec) == 0.2


def test_b_consumer_falls_back_for_pre_p02e_artifacts():
    assert X.read_delta_pooled({"delta_pooled": 0.1}) == 0.1
    assert X.read_delta_pooled({"delta_pooled": 0.1}, "mean_score") == 0.1


def test_b_consumer_refuses_to_return_a_number_in_the_other_units():
    rec = X.delta_pooled_fields(0.3, X.FLAG)
    assert X.read_delta_pooled(rec, "asr") == 0.3
    assert X.read_delta_pooled(rec, "mean_score") is None


def test_b_pre_fix_source_emits_only_the_ambiguous_key(tmp_path):
    """RED: strip the siblings and the consumer can no longer tell the two meanings apart."""
    old = _stripped(tmp_path, "analyze_external_arms.py", "pre_p02e_external_arms",
                    'return {"delta_pooled": value, f"delta_pooled_{units}": value,\n'
                    '            "delta_pooled_units": units, "delta_pooled_field": field}',
                    'return {"delta_pooled": value}')
    score = old.delta_pooled_fields(0.24, old.SCORE)
    flag = old.delta_pooled_fields(0.24, old.FLAG)
    assert score == flag == {"delta_pooled": 0.24}
    assert "delta_pooled_mean_score" not in score and "delta_pooled_asr" not in flag
    # and the consumer, given the pre-fix record, cannot refuse the wrong units
    assert old.read_delta_pooled(flag, "mean_score") == 0.24


# --------------------------------------------------------------------------- #
# (c) dose
# --------------------------------------------------------------------------- #
def test_c_dose_fields_names_the_units_beside_the_bare_key():
    r = I.dose_fields(0.8402)
    assert r["dose"] == 0.8402                              # historical key, unchanged
    assert r["dose_cellmean_variance_frac_centred"] == r["dose"]
    assert r["dose_units"] == I.DOSE_UNITS_CELLMEAN == "cellmean_variance_frac_centred"


def test_c_prefixed_writers_get_their_own_explicit_name():
    r = I.dose_fields(0.1003, "max_complement_dose")
    assert r["max_complement_dose"] == 0.1003
    assert r["max_complement_dose_cellmean_variance_frac_centred"] == 0.1003
    assert r["dose_units"] == I.DOSE_UNITS_CELLMEAN
    assert "dose" not in r          # the bare ambiguous name is not invented where it never existed


def test_c_every_bare_dose_writer_routes_through_the_helper():
    for fn in ("dose_curve.py", "dose_vs_effect.py", "pooled_cellmean_spectrum.py"):
        src = open(os.path.join(SRCB, fn)).read()
        assert "from insubspace_null_test import" in src and "dose_fields" in src
        assert '"dose": ' not in src, f"{fn} still writes a bare dose key directly"


def test_c_the_units_name_the_centred_variance_not_the_residual():
    """The prev-C-6 confusion: this family is the CENTRED cell-mean variance, not the residual."""
    assert "variance" in I.DOSE_UNITS_CELLMEAN and "centred" in I.DOSE_UNITS_CELLMEAN
    assert "residual" not in I.DOSE_UNITS_CELLMEAN
    doc = I.dose_fields.__doc__
    assert "UN-CENTRED" in doc and "residual" in doc


def test_c_consumer_prefers_the_explicit_key_and_falls_back():
    assert I.read_dose(I.dose_fields(0.5)) == 0.5
    assert I.read_dose({"dose": 0.4, "dose_cellmean_variance_frac_centred": 0.9}) == 0.9
    assert I.read_dose({"dose": 0.4}) == 0.4                                  # pre-P0.2e
    assert I.read_dose({"dose_cellmean_frac": 0.7}, legacy="dose_cellmean_frac") == 0.7
    assert I.read_dose(I.dose_fields(0.6, "arm_dose"), "arm_dose") == 0.6


def test_c_pre_fix_source_emits_only_the_bare_key(tmp_path):
    """RED: strip the sibling and the consumer silently reads the un-annotated number."""
    old = _stripped(tmp_path, "insubspace_null_test.py", "pre_p02e_insubspace",
                    'return {prefix: value, f"{prefix}_{DOSE_UNITS_CELLMEAN}": value,\n'
                    '            "dose_units": DOSE_UNITS_CELLMEAN}',
                    'return {prefix: value}')
    r = old.dose_fields(0.8402)
    assert r == {"dose": 0.8402}
    assert "dose_cellmean_variance_frac_centred" not in r
    assert "dose_units" not in r


# --------------------------------------------------------------------------- #
# (d) spearman — the audit's claim, tested rather than believed
# --------------------------------------------------------------------------- #
def test_d_no_spearman_key_in_code_holds_a_non_spearman_quantity():
    """REFUTED: every `spearman`-named field in src/ and scripts/ is a real Spearman rho.

    The claim under test was that a field called `spearman` holds a Pearson on log2(n_examples).
    The two code fields with that name are analyze_g2 (`spearman()` = scipy `spearmanr`) and
    analyze_subspace_prediction (`spearman()` = analyze_phase_d's Pearson-on-RANKS, which is the
    definition of Spearman). The log2 quantity exists but is an OLS SLOPE and analyze_g8 already
    calls it `slope_log2` -- so (d) is a documentation fix, with nothing to rename in code.
    """
    import analyze_g2
    import analyze_phase_d
    xs = [1.0, 2.0, 3.0, 4.0, 10.0]
    ys = [1.0, 4.0, 9.0, 16.0, 25.0]                # monotone but very non-linear
    rho_g2, _ = analyze_g2.spearman(xs, ys)
    rho_pd = analyze_phase_d.spearman(xs, ys)
    assert rho_g2 == pytest.approx(1.0)             # a Spearman is 1.0 on any monotone relation
    assert rho_pd == pytest.approx(1.0)
    assert analyze_phase_d.pearson(xs, ys) < 0.999  # a Pearson is not
    src = open(os.path.join(SRCB, "analyze_g8.py")).read()
    assert '"slope_log2"' in src and "spearman" not in src
