"""`control_feasibility` must read the draw's own record, not re-derive it.

WHY (R-46 → R-47, 2026-08-26). `nondemo_control_draw` returns a TUPLE `(positions, record)`. The
first version of this script did `len(drawn) / len(dk)` — and `len()` of that tuple is **2**, so
every ratio was `2 / n_demo_keys`: 2/18 = 0.111, 2/13 = 0.154, which is exactly what it reported.

The numbers looked plausible because the *demo* positions were always right (13/28/56/114, matching
the real arms row for row). It was caught only by comparing against a real pre-flight, and the cause
I first guessed — a templating mismatch — was **wrong**. A derived quantity must be read from the
thing that derived it.
"""

from __future__ import annotations

import os

SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "src", "boombness", "control_feasibility.py")


def _src():
    return open(SRC).read()


def _code_only(s):
    """Strip the module docstring: it QUOTES the defect on purpose, and a guard that cannot tell
    an explanation from the thing it explains would forbid documenting the bug."""
    i = s.index('"""', s.index('"""') + 3) + 3
    return s[i:]


def test_the_draw_is_unpacked_not_measured_with_len():
    s = _src()
    assert "_pos, rec = nondemo_control_draw(" in s, "the (positions, record) tuple must be unpacked"
    assert "len(drawn)" not in _code_only(s), "len() on the returned tuple is the original defect"


def test_match_ratio_is_read_from_the_record_not_recomputed():
    s = _src()
    assert 'rec.get("match_ratio"' in s
    assert "/ len(dk)" not in _code_only(s), "ratio must not be re-derived beside the function that derives it"


def test_pool_size_also_comes_from_the_record():
    s = _src()
    assert 'rec.get("n_pool"' in s


def test_the_infeasible_path_keeps_the_records_reason():
    """strict REFUSES rather than under-matching; the record rides on the exception."""
    s = _src()
    assert 'getattr(exc, "record"' in s


def test_the_quarantine_note_records_that_the_first_guess_was_wrong():
    """The docstring must not leave a wrong diagnosis standing as if it were the cause."""
    s = _src()
    assert "That guess was wrong" in s or "guess was wrong" in s
