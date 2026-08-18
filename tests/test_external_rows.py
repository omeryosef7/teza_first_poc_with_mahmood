"""Occurrence resolution for rows that legitimately carry no target word (plan §14 external sets).

Each test fails against the pre-fix code; the header records the pre-fix behaviour.
"""
import os
import sys
import types

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "boombness"))
import extract_boombness as eb  # noqa: E402


class _Tok:
    def __call__(self, text, add_special_tokens=False):
        return {"input_ids": list(range(len(text.split())))}


def _dc(hits):
    """Stand-in for the house helpers. `find_word_occurrences_in_text` returns whatever we say --
    the point of the test is that with an EMPTY needle the real helper matches everywhere."""
    return types.SimpleNamespace(
        apply_template=lambda tok, p, enable_thinking=None: p,
        find_word_occurrences_in_text=lambda tok, text, word, add_special_tokens=False:
            types.SimpleNamespace(last_idx=hits, spans=[(i, i + 1) for i in hits]),
    )


def test_row_with_no_target_resolves_cleanly():
    """PRE-FIX: raised occurrence_count_mismatch:text=0,tokens=27, because an empty target_surface
    matches at every token. That killed 179/179 rows in all three ClearHarm arms."""
    row = {"full_prompt": "a b c d e f", "target_surface": "", "n_target_occurrences": 0}
    templated, ids, last, following, n_sub = eb.resolve_occurrences(
        _dc(list(range(6))), _Tok(), row, enable_thinking=False)
    assert last == [] and following == [] and n_sub == []
    assert len(ids) == 6


def test_row_claiming_occurrences_without_a_target_still_fails():
    """The guard must not become a blanket bypass: metadata that says '3 occurrences of nothing'
    is incoherent and must still stop the run."""
    row = {"full_prompt": "a b c", "target_surface": "", "n_target_occurrences": 3}
    try:
        eb.resolve_occurrences(_dc([0, 1, 2]), _Tok(), row, enable_thinking=False)
    except ValueError as e:
        assert "no_target_surface_but_expected" in str(e)
    else:
        raise AssertionError("expected ValueError")


def test_normal_row_still_checks_the_count():
    """The original guard must keep working for bank rows: tokenizer and metadata disagreeing
    is the whole reason this function raises."""
    row = {"full_prompt": "a b c", "target_surface": "carrot", "n_target_occurrences": 2}
    try:
        eb.resolve_occurrences(_dc([1]), _Tok(), row, enable_thinking=False)
    except ValueError as e:
        assert "occurrence_count_mismatch" in str(e)
    else:
        raise AssertionError("expected ValueError")
