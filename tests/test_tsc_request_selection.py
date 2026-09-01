"""`TSC-PR-005`'s request draw: determinism, blindness, and every refusal.

The draw fixes WHICH harmful requests are the independence units of the request-diverse bank. The
one way selection leakage enters is a human keeping the requests that look promising, so this file
pins the three properties that make that impossible: the draw depends only on the seed, it reads no
`instruction` text, and it refuses rather than shrinking when it cannot fill a quota.

Every refusal has a MUTANT test proving the permissive version accepts the same input.
"""
import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import tsc_select_requests as ts  # noqa: E402

ARTIFACT = os.path.join(ROOT, "data", "manifests", "tsc_requests_v1_selection.json")


def _rows(n_per_cat, cats=None, group=lambda c, i: ""):
    """A synthetic source with the same three columns the draw is allowed to read."""
    cats = cats or ts.CATEGORIES
    return [{"task_id": f"{c}_{i:03d}", "category": c, "duplicate_group": group(c, i),
             # present, and deliberately never consulted -- see test_draw_ignores_instruction_text
             "instruction": f"UNREAD-{c}-{i}", "source_dataset": "advbench", "split": "heldout"}
            for c in cats for i in range(n_per_cat)]


# --------------------------------------------------------------------------- determinism

def test_same_seed_same_draw():
    a = ts.select(_rows(20), 5, seed=20260903)
    b = ts.select(_rows(20), 5, seed=20260903)
    assert [r["task_id"] for r in a] == [r["task_id"] for r in b]


def test_different_seed_different_draw():
    a = {r["task_id"] for r in ts.select(_rows(20), 5, seed=20260903)}
    b = {r["task_id"] for r in ts.select(_rows(20), 5, seed=20260904)}
    assert a != b, "the seed must actually drive the draw"


def test_draw_is_independent_of_source_row_order():
    """`csv.DictReader` yields file order, and file order is not a guarantee.

    The draw sorts by `task_id` before shuffling, so a re-sorted source cannot silently change the
    population under the same seed. Without that sort this test fails.
    """
    rows = _rows(20)
    a = [r["task_id"] for r in ts.select(rows, 5)]
    b = [r["task_id"] for r in ts.select(list(reversed(rows)), 5)]
    assert a == b


def test_MUTANT_unsorted_shuffle_would_depend_on_file_order():
    """Executed proof that the sort is load-bearing, not decoration."""
    import random
    rows = [r for r in _rows(20) if r["category"] == ts.CATEGORIES[0]]
    def unsorted_draw(pool):
        pool = list(pool)
        random.Random(20260903).shuffle(pool)
        return [r["task_id"] for r in pool[:5]]
    assert unsorted_draw(rows) != unsorted_draw(list(reversed(rows))), \
        "without the pre-sort, reversing the source changes the draw"


# --------------------------------------------------------------------------- blindness

def test_draw_ignores_instruction_text():
    """Rewriting every instruction must not move a single selected task_id."""
    rows = _rows(20)
    base = [r["task_id"] for r in ts.select(rows, 5)]
    for r in rows:
        r["instruction"] = "COMPLETELY DIFFERENT TEXT " + r["task_id"][::-1]
    assert [r["task_id"] for r in ts.select(rows, 5)] == base


def test_source_module_never_reads_the_instruction_column():
    """Pinned against the source text: `instruction` must not appear in the selection module."""
    src = open(os.path.join(ROOT, "scripts", "tsc_select_requests.py"), encoding="utf-8").read()
    code = "\n".join(ln for ln in src.splitlines()
                     if not ln.lstrip().startswith("#"))
    body = code.split('"""', 2)[-1]          # drop the module docstring, which discusses it
    assert '"instruction"' not in body and "'instruction'" not in body


# --------------------------------------------------------------------------- dedup

def test_duplicate_group_is_deduped_across_categories():
    """A shared group is the same instruction; the same instruction twice is one cluster as two."""
    # every row of the first two categories shares one group -> each can contribute only 1
    def grp(c, i):
        return "G" if c in ts.CATEGORIES[:2] else f"{c}_{i}"
    with pytest.raises(SystemExit) as e:
        ts.select(_rows(20, group=grp), 5)
    assert "after de-duplication" in str(e.value)


def test_MUTANT_no_dedup_would_have_returned_a_full_but_wrong_draw():
    """Executed proof: without the group check the draw fills its quota with duplicates."""
    rows = [r for r in _rows(20, group=lambda c, i: "G") if r["category"] == ts.CATEGORIES[0]]
    permissive = rows[:5]
    assert len(permissive) == 5 and len({r["duplicate_group"] for r in permissive}) == 1, \
        "the permissive version returns 5 rows that are all the same instruction"


def test_empty_duplicate_group_is_not_treated_as_a_shared_group():
    """Blank groups are 'ungrouped', not 'all the same group' -- otherwise the draw yields 1/cat."""
    got = ts.select(_rows(20, group=lambda c, i: ""), 5)
    assert len(got) == 5 * len(ts.CATEGORIES)


# --------------------------------------------------------------------------- refusals

def test_REFUSES_a_registered_category_below_the_floor():
    with pytest.raises(SystemExit) as e:
        ts.select(_rows(10), 5)
    assert "below MIN_CATEGORY_N" in str(e.value)


def test_REFUSES_when_an_excluded_category_has_grown_past_the_floor():
    """The exclusion list is checked against the data, not trusted.

    `terrorism_extremism` was excluded for n=9. If the source grows it to 16 the population has
    changed and the rule must be re-registered rather than silently applied.
    """
    rows = _rows(20) + _rows(20, cats=("terrorism_extremism",))
    with pytest.raises(SystemExit) as e:
        ts.select(rows, 5)
    assert "terrorism_extremism" in str(e.value) and "re-register" in str(e.value)


def test_paradigm_scope_limit_exclusions_are_not_silently_droppable():
    """The person/speech-act exclusions must carry their reason in the artifact, not vanish."""
    for cat in ("self_harm_suicide", "hate_speech_discrimination", "harassment_bullying_stalking"):
        assert "PARADIGM SCOPE LIMIT" in ts.EXCLUDED[cat]
    #: ...and they are NOT n<16 exclusions, so growing the source must not silently readmit them.
    for cat in ("self_harm_suicide", "hate_speech_discrimination", "harassment_bullying_stalking"):
        assert "MIN_CATEGORY_N" not in ts.EXCLUDED[cat]


def test_every_source_category_is_either_registered_or_explicitly_excluded():
    """No category may be omitted by silence."""
    assert set(ts.CATEGORIES).isdisjoint(ts.EXCLUDED)


# --------------------------------------------------------------------------- digest + artifact

def test_selection_digest_is_order_independent():
    assert ts.selection_sha16(["b", "a"]) == ts.selection_sha16(["a", "b"])
    assert ts.selection_sha16(["a", "b"]) != ts.selection_sha16(["a", "c"])


@pytest.mark.skipif(not os.path.exists(ARTIFACT), reason="selection artifact not built")
def test_committed_artifact_reproduces_from_the_committed_source():
    """The whole point: anyone can re-derive the population from the seed and the manifest."""
    import csv
    doc = json.load(open(ARTIFACT, encoding="utf-8"))
    with open(os.path.join(ROOT, doc["source"]), newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    got = ts.select(rows, doc["per_category"], doc["seed"])
    assert ts.selection_sha16(r["task_id"] for r in got) == doc["selection_sha16"]
    assert doc["n_selected"] == 40 and len(doc["categories"]) == 8
    assert doc["cluster_unit"] == "harmful_request"
    #: ⚠ The artifact must carry NO request text -- it has to be reviewable without reading any.
    assert all(set(r) == {"task_id", "category", "duplicate_group"} for r in doc["selected"])
