"""C9's table script must reproduce DR-5's hand audit, and must never emit a bare percentage.

C-13 showed what an untested prose instruction costs. C9 -- the strongest claim in the phase -- had
only a prose manifest row ("join the judge dirs by prompt_id"), so this script exists and these
tests pin it against the numbers DR-5 computed by hand.
"""

from __future__ import annotations

import os

SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "src", "boombness", "rescue_dissociation_table.py")


def _src():
    return open(SRC).read()


def test_margin_is_the_measured_one_not_an_invented_one():
    assert "MARGIN_VS_BASELINE = 0.0521" in _src()


def test_percentage_can_never_travel_without_rows_and_margin():
    """DR-5: the percentage is inverted relative to the evidence when the clean baseline is near
    zero. It stays in the artifact, but never alone."""
    s = _src()
    assert '"pct_of_rise_removed"' in s
    assert '"PCT_CAVEAT"' in s and "INVERTED" in s
    assert '"effect_rows"' in s and '"effect_x_margin"' in s
    # the printed line must carry rows and x-margin too, not just the percent
    assert "effect={v['effect_rows']" in s and "{v['effect_x_margin']" in s


def test_control_is_reported_per_cell_and_not_averaged_away():
    s = _src()
    assert '"control_rows_moved"' in s and '"control_inert"' in s
    assert '"n_cells_control_inert"' in s


def test_refusal_source_is_the_deterministic_detector_not_the_llm_judge():
    s = _src()
    assert '.get("refused")' in s
    assert "kw_refusal" in s and "NOT the LLM judge" in s


def test_it_refuses_duplicate_cell_names_and_malformed_specs():
    s = _src()
    assert "duplicate cell name" in s
    assert "needs 5 colon fields" in s


def test_empty_intersection_is_refused_not_reported_as_zero():
    assert "has no rows common to all four arms" in _src()
