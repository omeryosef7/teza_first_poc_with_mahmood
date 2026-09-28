#!/usr/bin/env python3
"""R42-F3 and R42-F4: the floor must not exempt rows from the channel guard, and NaN is ABSENT.

*** WHY THIS FILE EXISTS. ***
Review R42 found two defects in the option-mass floor that S-548 introduced, both LATENT on today's
corpus and both a divergence between two functions the record calls identical:

  F3  `load_installation`'s `keep_keys` skip sat ABOVE its duplicate-key refusal, so every key the
      floor dropped -- 84 of 230 on csi5 at floor 0.05 -- was EXEMPT from the refusal that the
      function's own comment calls "the only thing keeping the forced-choice channel out". The
      sibling `dcs_csi_subspace_analyze.py` has always checked duplicates FIRST.
  F4  `float(nan) >= floor` is False, so the census silently DROPPED a NaN readout as if it were a
      small mass; the sibling's `if om < floor: continue` is ALSO False for NaN, so it silently KEPT
      it. Opposite directions, same row. tests/test_option_mass_nan_guard.py already records why this
      matters: on 2026-08-28 a run produced NaN option_mass on 36 of 40 rows and the gate said PASS.

These tests are BEHAVIOURAL, on synthetic run directories, because R42-F10's complaint about the
existing floor tests was that 6 of 11 only assert that a literal string appears in the source. A
source-grep cannot distinguish "the refusal is above the skip" from "below" -- that is the whole bug.
"""
import importlib.util
import json
import math
import os

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


LPM = _load("lpm_ord", os.path.join(REPO, "scripts", "dcs_cont_layerpos_map.py"))
CENSUS = _load("census_ord", os.path.join(REPO, "scripts", "dcs_csi_head_census.py"))

SLOT = "dev|slot0|n4|none|consistent|near|plain"


def _row(domain, slot, om=0.5, lc=-0.2, lk=-1.4, pid="p0"):
    return {"query_kind": "semantic_one_word", "cell": "C", "domain": domain,
            "family_id": "%s|%s|semantic_one_word" % (domain, slot),
            "logp_concept": lc, "logp_codeword": lk, "option_mass": om, "prompt_id": pid}


def _run_dir(tmp_path, rows):
    d = tmp_path / "synth_run"
    d.mkdir()
    with open(d / "results.jsonl", "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")
    return str(d)


# ---------------------------------------------------------------- F3

def test_a_duplicate_among_FLOOR_DROPPED_keys_is_still_refused(tmp_path):
    """THE F3 BUG. Both rows have the same key and both are below the floor, so before the fix the
    skip fired first and the channel-substitution refusal never saw them."""
    rows = [_row("alpha", SLOT, om=0.001, pid="a"),
            _row("alpha", SLOT, om=0.001, pid="b"),
            _row("beta", SLOT, om=0.9, pid="c")]
    rd = _run_dir(tmp_path, rows)
    keep = {("beta", SLOT)}                      # the duplicated key is NOT kept
    with pytest.raises(LPM.Refusal) as e:
        LPM.load_installation(rd, keep_keys=keep)
    assert "binds two rows" in str(e.value)


def test_a_duplicate_among_KEPT_keys_is_refused_too(tmp_path):
    """The case that always worked; pinned so a fix cannot trade one for the other."""
    rows = [_row("alpha", SLOT, om=0.9, pid="a"), _row("alpha", SLOT, om=0.9, pid="b")]
    rd = _run_dir(tmp_path, rows)
    with pytest.raises(LPM.Refusal):
        LPM.load_installation(rd, keep_keys={("alpha", SLOT)})


def test_the_floor_still_actually_drops_rows_after_the_reorder(tmp_path):
    """The reorder must not turn the filter into a no-op."""
    rows = [_row("alpha", SLOT, om=0.9, pid="a"), _row("beta", SLOT, om=0.9, pid="b")]
    rd = _run_dir(tmp_path, rows)
    out_all, _, _ = LPM.load_installation(rd, keep_keys=None)
    out_one, _, _ = LPM.load_installation(rd, keep_keys={("alpha", SLOT)})
    assert len(out_all) == 2 and len(out_one) == 1
    assert ("alpha", SLOT) in out_one and ("beta", SLOT) not in out_one


def test_keep_keys_None_is_unaffected_by_the_reorder(tmp_path):
    """VOID 7: ~26 existing callers must stay byte-identical."""
    rows = [_row("alpha", SLOT, om=0.001, pid="a"), _row("beta", SLOT, om=0.9, pid="b")]
    rd = _run_dir(tmp_path, rows)
    out, n_seen, kinds = LPM.load_installation(rd, keep_keys=None)
    assert set(out) == {("alpha", SLOT), ("beta", SLOT)} and n_seen == 2


# ---------------------------------------------------------------- F4

def test_the_census_refuses_a_NaN_option_mass(tmp_path):
    """Before the fix `float(nan) >= floor` was False and the row was silently dropped."""
    rd = _run_dir(tmp_path, [_row("alpha", SLOT, om=float("nan"), pid="a")])
    with pytest.raises(SystemExit) as e:
        CENSUS._option_mass_keys(rd, 0.05)
    assert "NaN" in str(e.value)


def test_the_census_still_refuses_a_MISSING_option_mass(tmp_path):
    r = _row("alpha", SLOT, pid="a")
    r.pop("option_mass")
    rd = _run_dir(tmp_path, [r])
    with pytest.raises(SystemExit) as e:
        CENSUS._option_mass_keys(rd, 0.05)
    assert "missing is not zero" in str(e.value)


def test_a_finite_mass_below_the_floor_is_still_merely_dropped(tmp_path):
    """NaN must be distinguished from small -- not both refused, and not both kept."""
    rd = _run_dir(tmp_path, [_row("alpha", SLOT, om=0.001, pid="a"),
                             _row("beta", SLOT, om=0.9, pid="b")])
    keep, n, nk = CENSUS._option_mass_keys(rd, 0.05)
    assert keep == {("beta", SLOT)} and n == 2 and nk == 1


def test_both_implementations_refuse_NaN_rather_than_disagreeing():
    """F4's point was the DIVERGENCE: one dropped, the other kept, docs said identical."""
    a = open(os.path.join(REPO, "scripts", "dcs_csi_head_census.py"), encoding="utf-8").read()
    b = open(os.path.join(REPO, "scripts", "dcs_csi_subspace_analyze.py"), encoding="utf-8").read()
    assert "math.isnan(om)" in a, "census does not refuse NaN"
    assert "math.isnan(om)" in b, "axis analyser does not refuse NaN"


def test_nan_really_is_false_on_both_sides_of_a_floor():
    """The premise both bugs rest on, pinned so nobody 'simplifies' the guard away."""
    nan, floor = float("nan"), 0.05
    assert not (nan >= floor) and not (nan < floor)
    assert math.isnan(nan)
