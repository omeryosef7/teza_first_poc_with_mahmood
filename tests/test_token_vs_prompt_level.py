"""Single-occurrence prompts must be excluded, or the answer is manufactured.

With one codeword occurrence the token-level and prompt-level readings are literally the same
number. Including such prompts would push every correlation toward 1 and produce the conclusion
"they are one object" as an artifact of the denominator.
"""

from __future__ import annotations

import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src", "boombness"))

import token_vs_prompt_level as tvp  # noqa: E402

F = "d_surface|L12|proj"


def _row(pid, occ, val, n_occ, final=False, query=False, ne=4):
    return {"prompt_id": pid, "occurrence_index": occ, F: val, "n_occurrences": n_occ,
            "is_final_occurrence": final, "is_query_occurrence": query, "n_examples": ne,
            "domain": "d", "condition": "natural_doublespeak", "split": "dev", "family_id": "f"}


def test_spearman_matches_known_values():
    assert tvp.spearman([1, 2, 3, 4], [1, 2, 3, 4]) == pytest.approx(1.0)
    assert tvp.spearman([1, 2, 3, 4], [4, 3, 2, 1]) == pytest.approx(-1.0)
    assert tvp.spearman([1, 2], [1, 2]) is None            # n < 3
    assert tvp.spearman([1, 1, 1, 1], [1, 2, 3, 4]) is None  # zero variance


def test_single_occurrence_prompts_are_EXCLUDED(tmp_path):
    rows = [_row("solo", 0, 1.0, 1, final=True, query=True)]
    for i in range(4):
        rows += [_row(f"m{i}", 0, float(i), 2), _row(f"m{i}", 1, float(i) * 2, 2, final=True, query=True)]
    r = tvp.analyse(rows, F)
    assert r["n_single_occurrence_EXCLUDED"] == 1
    assert r["n_multi_occurrence"] == 4
    assert r["correlations_multi_occurrence_only"]["token_final~prompt_mean"]["n"] == 4


def test_token_and_prompt_are_identical_on_a_single_occurrence_prompt():
    """The reason for the exclusion, asserted rather than described."""
    m = tvp.build_prompt_metrics([_row("solo", 0, 7.0, 1, final=True, query=True)], F)["solo"]
    assert m["token_final"] == m["prompt_mean"] == m["prompt_max"] == 7.0


def test_demo_mean_excludes_the_query_occurrence():
    rows = [_row("p", 0, 1.0, 3), _row("p", 1, 3.0, 3),
            _row("p", 2, 100.0, 3, final=True, query=True)]
    m = tvp.build_prompt_metrics(rows, F)["p"]
    assert m["prompt_demo_mean"] == 2.0        # (1+3)/2, the query's 100 excluded
    assert m["token_final"] == 100.0
    assert m["prompt_mean"] == pytest.approx(104 / 3)


def test_a_perfectly_redundant_aggregate_reports_correlation_one():
    """Positive control: if the aggregate really were the final token, the analysis must say so."""
    rows = []
    for i in range(10):
        v = float(i)
        rows += [_row(f"p{i}", 0, v, 2), _row(f"p{i}", 1, v, 2, final=True, query=True)]
    r = tvp.analyse(rows, F)
    assert r["correlations_multi_occurrence_only"]["token_final~prompt_mean"]["spearman"] == pytest.approx(1.0)


def test_an_independent_aggregate_reports_low_correlation():
    rows = []
    fin = [5, 1, 4, 2, 3, 9, 7, 6, 8, 0]
    dem = [0, 8, 6, 7, 9, 3, 2, 4, 1, 5]
    for i in range(10):
        rows += [_row(f"p{i}", 0, float(dem[i]), 2),
                 _row(f"p{i}", 1, float(fin[i]), 2, final=True, query=True)]
    s = tvp.analyse(rows, F)["correlations_multi_occurrence_only"]["token_final~prompt_mean"]["spearman"]
    assert abs(s) < 0.8


def test_rows_missing_the_field_are_skipped_not_zeroed():
    rows = [_row("p", 0, 1.0, 2), _row("p", 1, None, 2, final=True, query=True)]
    m = tvp.build_prompt_metrics(rows, F)
    assert m["p"]["n_occurrences"] == 1        # the None row is absent, not counted as 0.0
