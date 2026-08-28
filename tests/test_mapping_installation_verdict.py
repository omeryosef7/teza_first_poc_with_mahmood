"""The threshold errors C-31/C-33 made, encoded so they cannot come back silently.

These assert on BEHAVIOUR, not on source text. C-27 recorded that four guards in this repo assert on
the wording of a module and two of them miss the regression they exist for; a test that greps for
"0.500" would pass against a rewritten module that still classifies at 0.500.
"""

import glob
import json
import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                "src", "boombness"))
import mapping_installation_verdict as miv  # noqa: E402

SCRIPT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      "src", "boombness", "mapping_installation_verdict.py")


def test_the_cell_C31_got_wrong_is_not_called_installed():
    # ticket_knife: 30/48 = 0.625, above 0.500 and p=0.111. A 0.500 cut calls this INSTALLED.
    verdict, k = miv.classify(30, 48)
    assert verdict == "NOT_ESTABLISHED", verdict
    assert k == 32


def test_basket_gun_does_not_reach_the_lower_tail_either():
    # 19/48 (p=0.193) is below 0.500 but does NOT clear the inverted tail, which needs <= 16.
    # So it licenses no positive claim of absence -- only "installation not established".
    assert miv.classify(19, 48)[0] == "NOT_ESTABLISHED"
    assert miv.classify(16, 48)[0] == "INVERTED"
    assert miv.classify(17, 48)[0] == "NOT_ESTABLISHED"


def test_the_lower_tail_is_named_for_what_it_means():
    # Significantly below chance = prefers the CODEWORD = inverted. Calling it "ABSENT" would let a
    # claim of absence be read off it.
    assert miv.classify(5, 48)[0] == "INVERTED"


def test_the_decisive_verdicts_still_pass():
    assert miv.classify(39, 48)[0] == "INSTALLED"   # window_knife
    assert miv.classify(42, 48)[0] == "INSTALLED"   # basket_bomb
    assert miv.classify(40, 48)[0] == "INSTALLED"   # window_bomb


def test_the_threshold_moves_with_n_and_is_not_carried_over():
    # C-33: a screen stated once and reused at another population is the defect.
    assert miv.critical_k(48) == 32
    assert miv.critical_k(60) == 39
    assert miv.critical_k(96) == 59


def test_power_is_reported_so_an_unresolvable_cell_looks_unresolvable():
    # C-32's table. A NOT_ESTABLISHED at n=48 must not read as a null when the design would miss a
    # real 0.625 effect two times in three.
    assert abs(miv.power_at(48, 32) - 0.331) < 0.001
    assert abs(miv.power_at(60, 39) - 0.399) < 0.001
    assert miv.power_at(48, 32) < 0.5


def test_a_tie_is_not_a_win():
    # The predicate is strict `>`; ties inflate wins if read as `>=`.
    assert miv.binom_two_sided(24, 48) > 0.9


def _fixture(tmp, gate="PASS", n_failed=0):
    d = os.path.join(tmp, "run")
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "results.jsonl"), "w") as fh:
        for i in range(48):
            fh.write(json.dumps({"prompt_id": f"p{i}", "p_concept": 0.9 if i < 39 else 0.1,
                                 "p_codeword": 0.1 if i < 39 else 0.9, "n_examples": 1,
                                 "condition": "natural_doublespeak"}) + "\n")
    json.dump({"option_mass_gate": gate, "failures": {"n_failed": n_failed},
               "model": "m", "arm": "A_baseline"}, open(os.path.join(d, "summary.json"), "w"))
    return d


def test_a_failing_run_level_gate_alone_does_NOT_refuse_but_IS_recorded():
    """REPLACES a test that asserted the C-44 defect.

    The old test required a refusal whenever `option_mass_gate != PASS`. That gate aggregates every
    query kind in the run, so it vetoed three real banks whose forced-choice readout was healthy
    (`p5A_main` 0.5414, `p5_window_bomb` 0.5156, `p5_window_knife` 0.7783). The veto is wrong; the
    information is not, so it must survive into the artifact rather than be discarded.
    """
    with tempfile.TemporaryDirectory() as tmp:
        d = _fixture(tmp, gate="OVERRIDDEN — NOT REPORTABLE: semantic/semantic_one_word")
        out = os.path.join(tmp, "out")
        proc = subprocess.run([sys.executable, SCRIPT, "--probe", f"x={d}", "--out-root", out],
                              capture_output=True, text=True)
        assert proc.returncode == 0, proc.stdout + proc.stderr
        assert "INSTALLED" in proc.stdout
        art = glob.glob(os.path.join(out, "**", "mapping_installation_verdict.json"), recursive=True)
        assert art, "no artifact written"
        rec = json.load(open(art[0]))["per_probe"]["x"]
        assert "NOT REPORTABLE" in str(rec["run_level_option_mass_gate"])
        assert rec["median_option_mass_of_scored_rows"] >= 0.05


def test_it_REFUSES_a_run_with_failed_rows():
    with tempfile.TemporaryDirectory() as tmp:
        d = _fixture(tmp, n_failed=3)
        proc = subprocess.run([sys.executable, SCRIPT, "--probe", f"x={d}",
                               "--out-root", os.path.join(tmp, "out")],
                              capture_output=True, text=True)
        assert proc.returncode != 0
        assert "failed to generate" in (proc.stdout + proc.stderr)


def test_it_REFUSES_a_silently_attrited_population():
    # The dangerous case: no recorded failures and a PASS gate, but fewer rows than the bank held.
    # critical_k would quietly adapt to the smaller n and the verdict would look valid.
    with tempfile.TemporaryDirectory() as tmp:
        d = _fixture(tmp)
        sm = json.load(open(os.path.join(d, "summary.json")))
        sm["n_bank_rows"], sm["n_result_rows"] = 160, 48
        json.dump(sm, open(os.path.join(d, "summary.json"), "w"))
        proc = subprocess.run([sys.executable, SCRIPT, "--probe", f"x={d}",
                               "--out-root", os.path.join(tmp, "out")],
                              capture_output=True, text=True)
        assert proc.returncode != 0
        assert "survived" in (proc.stdout + proc.stderr)


def test_a_complete_population_is_accepted():
    # The guard must not refuse a healthy run: n_result_rows == n_bank_rows.
    with tempfile.TemporaryDirectory() as tmp:
        d = _fixture(tmp)
        sm = json.load(open(os.path.join(d, "summary.json")))
        sm["n_bank_rows"], sm["n_result_rows"] = 48, 48
        json.dump(sm, open(os.path.join(d, "summary.json"), "w"))
        proc = subprocess.run([sys.executable, SCRIPT, "--probe", f"x={d}",
                               "--out-root", os.path.join(tmp, "out")],
                              capture_output=True, text=True)
        assert proc.returncode == 0, proc.stdout + proc.stderr
        assert "INSTALLED" in proc.stdout


def test_it_REFUSES_nan_rather_than_counting_them_as_losses():
    # V-54: NaN escapes both sides of a threshold, so the upstream gate can say PASS. Here the
    # danger is the strict-> predicate: NaN > x is False, so NaN rows would silently become
    # "not a win" and depress the fraction instead of failing.
    with tempfile.TemporaryDirectory() as tmp:
        d = _fixture(tmp)
        lines = open(os.path.join(d, "results.jsonl")).read().splitlines()
        rows = [json.loads(l) for l in lines]
        rows[0]["p_concept"] = float("nan")
        with open(os.path.join(d, "results.jsonl"), "w") as fh:
            for r in rows:
                fh.write(json.dumps(r) + "\n")
        proc = subprocess.run([sys.executable, SCRIPT, "--probe", f"x={d}",
                               "--out-root", os.path.join(tmp, "out")],
                              capture_output=True, text=True)
        assert proc.returncode != 0
        assert "non-finite" in (proc.stdout + proc.stderr)


def test_a_nan_row_would_otherwise_have_been_counted_as_a_loss():
    # Pins WHY the guard is needed: without it the row silently changes the count, it does not error.
    assert (float("nan") > 0.5) is False
    assert (float("nan") < 0.5) is False


def test_duplicate_probe_labels_are_refused():
    with tempfile.TemporaryDirectory() as tmp:
        d = _fixture(tmp)
        proc = subprocess.run([sys.executable, SCRIPT, "--probe", f"x={d}", "--probe", f"x={d}",
                               "--out-root", os.path.join(tmp, "out")],
                              capture_output=True, text=True)
        assert proc.returncode != 0
        assert "duplicate" in (proc.stdout + proc.stderr).lower()


def _mixed_fixture(tmp, gate, fc_mass, ow_mass):
    """A run whose run-level gate FAILS on one_word while forced_choice is healthy — the real shape
    of p5A_main / p5_window_bomb / p5_window_knife (C-44)."""
    d = os.path.join(tmp, "mixed")
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "results.jsonl"), "w") as fh:
        for i in range(48):                                   # forced choice: healthy mass
            win = i < 39
            hi, lo = (fc_mass * 0.9, fc_mass * 0.1) if win else (fc_mass * 0.1, fc_mass * 0.9)
            fh.write(json.dumps({"prompt_id": f"fc{i}", "query_kind": "semantic_forced_choice",
                                 "p_concept": hi, "p_codeword": lo}) + "\n")
        for i in range(96):                                   # one_word: tail-bound
            fh.write(json.dumps({"prompt_id": f"ow{i}", "query_kind": "semantic_one_word",
                                 "p_concept": ow_mass * 0.6, "p_codeword": ow_mass * 0.4}) + "\n")
    json.dump({"option_mass_gate": gate, "failures": {"n_failed": 0},
               "n_bank_rows": 144, "n_result_rows": 144,
               "model": "m", "arm": "A_baseline"}, open(os.path.join(d, "summary.json"), "w"))
    return d


def test_a_failing_RUN_LEVEL_gate_does_not_veto_a_healthy_scored_readout():
    """C-44: the gate aggregates query kinds this tool never reads.

    Refusing here is a FALSE REFUSAL, and that is the dangerous direction: nothing downstream
    complains about a missing arm, because a smaller population reads as a cleaner one.
    """
    with tempfile.TemporaryDirectory() as tmp:
        d = _mixed_fixture(tmp, "OVERRIDDEN — NOT REPORTABLE: semantic/semantic_one_word", 0.78, 0.02)
        proc = subprocess.run([sys.executable, SCRIPT, "--probe", f"x={d}",
                               "--out-root", os.path.join(tmp, "out")],
                              capture_output=True, text=True)
        assert proc.returncode == 0, proc.stdout + proc.stderr
        assert "39/48" in proc.stdout, proc.stdout          # scored the forced-choice rows only
        assert "INSTALLED" in proc.stdout


def test_a_tail_bound_SCORED_readout_is_still_refused():
    with tempfile.TemporaryDirectory() as tmp:
        d = _mixed_fixture(tmp, "PASS", 0.78, 0.02)
        proc = subprocess.run([sys.executable, SCRIPT, "--probe", f"x={d}",
                               "--query-kind", "semantic_one_word",
                               "--out-root", os.path.join(tmp, "out")],
                              capture_output=True, text=True)
        assert proc.returncode != 0
        assert "median option mass" in (proc.stdout + proc.stderr)


def test_the_query_kind_filter_actually_selects():
    """Without it the tool pools readouts whose mass regimes differ by an order of magnitude."""
    with tempfile.TemporaryDirectory() as tmp:
        d = _mixed_fixture(tmp, "PASS", 0.78, 0.02)
        proc = subprocess.run([sys.executable, SCRIPT, "--probe", f"x={d}",
                               "--out-root", os.path.join(tmp, "out")],
                              capture_output=True, text=True)
        assert "/48" in proc.stdout and "/144" not in proc.stdout, proc.stdout
