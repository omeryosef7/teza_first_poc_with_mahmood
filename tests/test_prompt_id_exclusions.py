"""`TSC-P1`: the declared row exclusion (`--exclude-prompt-ids`) and every way it must refuse.

WHY THIS MECHANISM EXISTS. `CDS-R-020`: four `basket<->bomb` intervention arms died on
`occurrence_count_mismatch`, on three rows named by `prompt_id` before any generation ran. The same
exception is SKIPPED by the failure ledger in a baseline arm and FATAL in an intervened one, because
the knockout pre-flight resolves every row outside any `try`. A silent skip in one arm and not
another is how two different row sets end up under one label, so the fix removes the rows from the
POPULATION -- identically and declaredly -- in every arm.

WHAT THIS FILE PINS. Not only that the loader loads: that it REFUSES on a missing file, on an EMPTY
list, and on a DUPLICATED id; that the digest is order-independent; that the real basket exclusion
file resolves to exactly the three ids the log named and leaves exactly 377 rows in 38 domains; and
-- the load-bearing one -- that an id NOT present in the population is a refusal rather than a
silent no-op. Each refusal has a MUTANT test proving the permissive version would have passed the
same input.
"""
import io
import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src", "boombness"))
import score_behavior as sb  # noqa: E402

BASKET_BANK = os.path.join(ROOT, "data", "boombness_prompts",
                           "boombness_prompt_bank_cds38_basket_bomb.jsonl")
BASKET_EXCL = os.path.join(ROOT, "data", "boombness_prompts", "exclusions",
                           "cds38_basket_bomb_occurrence_mismatch.txt")
#: The three ids `CDS-C-002` named BEFORE any basket generation existed. Hardcoded HERE, in a test,
#: and nowhere in scientific logic -- the mechanism itself must stay generic.
CDS_C_002_IDS = ["566c998c6df83a30", "56c76e11095a5d48", "f953fbbb2376f8db"]


# --------------------------------------------------------------------------- loader

def test_loads_ids_ignoring_comments_and_blanks(tmp_path):
    p = tmp_path / "x.txt"
    p.write_text("# a comment\n\n  bbb  \naaa  # trailing comment\n\n")
    assert sb.load_prompt_id_exclusions(str(p)) == ["aaa", "bbb"], "sorted, stripped, uncommented"


def test_REFUSES_missing_file(tmp_path):
    with pytest.raises(SystemExit) as e:
        sb.load_prompt_id_exclusions(str(tmp_path / "nope.txt"))
    assert "not found" in str(e.value)


def test_REFUSES_empty_list(tmp_path):
    """`CDS-C-001`: a gate that passes on an empty selection is not a gate.

    An empty exclusion file would be recorded in the artifact as an exclusion while dropping
    nothing, so two arms could carry the same `exclude_prompt_ids_file` and different row sets.
    """
    p = tmp_path / "empty.txt"
    p.write_text("# only comments\n\n   \n")
    with pytest.raises(SystemExit) as e:
        sb.load_prompt_id_exclusions(str(p))
    assert "no ids" in str(e.value)


def test_MUTANT_permissive_loader_would_accept_the_empty_file(tmp_path):
    """Executed proof that dropping the empty-list refusal changes the outcome on this input."""
    p = tmp_path / "empty.txt"
    p.write_text("# only comments\n\n   \n")
    permissive = [t for t in (l.split("#", 1)[0].strip() for l in io.open(p)) if t]
    assert permissive == [], "the permissive version returns an empty list and raises nothing"


def test_REFUSES_duplicate_id(tmp_path):
    p = tmp_path / "dupe.txt"
    p.write_text("aaa\nbbb\naaa\n")
    with pytest.raises(SystemExit) as e:
        sb.load_prompt_id_exclusions(str(p))
    assert "repeats" in str(e.value) and "aaa" in str(e.value)


# --------------------------------------------------------------------------- digest

def test_digest_is_order_independent_and_16_hex():
    a = sb.exclusion_sha16(["b", "a", "c"])
    b = sb.exclusion_sha16(["c", "b", "a"])
    assert a == b, "two arms that list the same ids in different orders must agree"
    assert len(a) == 16 and all(ch in "0123456789abcdef" for ch in a)


def test_digest_separates_different_lists():
    assert sb.exclusion_sha16(["a", "b"]) != sb.exclusion_sha16(["a", "c"])


def test_digest_is_not_confused_by_concatenation():
    """`ab` + `c` must not digest the same as `a` + `bc`; the separator is load-bearing."""
    assert sb.exclusion_sha16(["ab", "c"]) != sb.exclusion_sha16(["a", "bc"])


# --------------------------------------------------------------------------- the real file

@pytest.mark.skipif(not os.path.exists(BASKET_EXCL), reason="basket exclusion file absent")
def test_basket_exclusion_file_is_exactly_the_three_predeclared_ids():
    assert sb.load_prompt_id_exclusions(BASKET_EXCL) == sorted(CDS_C_002_IDS)


@pytest.mark.skipif(not os.path.exists(BASKET_BANK), reason="basket bank absent")
def test_basket_exclusion_leaves_377_rows_in_38_domains():
    """The design after exclusion is 37 domains x 10 + school_campus x 7. Stated before the data."""
    import collections
    rows = [json.loads(l) for l in io.open(BASKET_BANK, encoding="utf-8")]
    sel = [r for r in rows
           if r["query_kind"] == "behavioral" and r.get("condition") == "natural_doublespeak"
           and r.get("bank_block") == "cds_n4" and int(r.get("n_examples", -1)) == 4]
    assert len(sel) == 380, "the unexcluded population must still be 380"
    drop = set(sb.load_prompt_id_exclusions(BASKET_EXCL))
    kept = [r for r in sel if r["prompt_id"] not in drop]
    assert len(kept) == 377
    per_domain = collections.Counter(r["domain"] for r in kept)
    assert len(per_domain) == 38, "no domain may be emptied by the exclusion"
    assert collections.Counter(per_domain.values()) == {10: 37, 7: 1}
    assert per_domain["school_campus"] == 7
    #: The excluded rows must all come from ONE domain. A cross-domain exclusion would change the
    #: cluster structure the primary sign test runs over, not just its balance.
    assert {r["domain"] for r in sel if r["prompt_id"] in drop} == {"school_campus"}


@pytest.mark.skipif(not os.path.exists(BASKET_BANK), reason="basket bank absent")
def test_excluded_rows_are_the_tokenisation_failures_and_nothing_else():
    """Provenance, re-derived: every excluded row carries the 5-occurrence basket surface.

    This is the check that the list is OUTCOME-INDEPENDENT: the property that selects these rows is
    a bank/tokenizer property (`n_target_occurrences`, `target_surface`), present before any
    generation, and it is the same property for all three.
    """
    rows = [json.loads(l) for l in io.open(BASKET_BANK, encoding="utf-8")]
    by_id = {r["prompt_id"]: r for r in rows}
    drop = sb.load_prompt_id_exclusions(BASKET_EXCL)
    for pid in drop:
        r = by_id[pid]
        assert r["target_surface"] == "basket"
        assert r["n_target_occurrences"] == 5
        assert r["domain"] == "school_campus"


# ------------------------------------------------- the population-membership refusal (load-bearing)

def _apply(rows, ids):
    """The exact predicate `main` applies, isolated so the refusal can be exercised without a GPU."""
    present = {r["prompt_id"] for r in rows}
    absent = [i for i in ids if i not in present]
    if absent:
        raise SystemExit(f"REFUSING: --exclude-prompt-ids lists {len(absent)} id(s) that are NOT "
                         f"in the filtered population of {len(rows)} rows: {absent[:5]}")
    return [r for r in rows if r["prompt_id"] not in set(ids)]


def test_REFUSES_an_id_absent_from_the_population():
    rows = [{"prompt_id": "a"}, {"prompt_id": "b"}]
    with pytest.raises(SystemExit) as e:
        _apply(rows, ["a", "zzz"])
    assert "NOT" in str(e.value) and "zzz" in str(e.value)


def test_MUTANT_silent_filter_would_have_dropped_a_different_count():
    """Executed proof of the failure this refusal prevents.

    Both arms are handed the SAME two-id exclusion and both artifacts would record
    `n_excluded = 2`. Silently, arm_x removes ONE row and arm_y removes TWO -- so the recorded
    exclusion describes arm_y and not arm_x, and the two arms no longer share a denominator. That
    is the shape `CDS-R-020` produced by accident, with the skip happening in the failure ledger
    instead of in a filter.
    """
    arm_x = [{"prompt_id": "a"}, {"prompt_id": "b"}, {"prompt_id": "c"}]
    arm_y = [{"prompt_id": "a"}, {"prompt_id": "b"}, {"prompt_id": "c"}, {"prompt_id": "zzz"}]
    ids = {"a", "zzz"}
    silent_x = [r for r in arm_x if r["prompt_id"] not in ids]
    silent_y = [r for r in arm_y if r["prompt_id"] not in ids]
    dropped_x = len(arm_x) - len(silent_x)
    dropped_y = len(arm_y) - len(silent_y)
    assert (dropped_x, dropped_y) == (1, 2), "one declared exclusion, two different removals"
    #: The provenance is what breaks first: arm_x's artifact would record `n_excluded = 2` while
    #: only one row left the population, so `n_before - n_excluded != n_after` and no later check
    #: can tell that the two arms were built from different row sets.
    assert len(arm_x) - len(ids) != len(silent_x), "arm_x's recorded exclusion misdescribes it"
    assert len(arm_y) - len(ids) == len(silent_y), "arm_y's happens to be honest -- that is the trap"
    #: The checked version refuses arm_x outright rather than producing the smaller row set.
    with pytest.raises(SystemExit):
        _apply(arm_x, sorted(ids))
    #: ...and still accepts the arm where every listed id really is present.
    assert len(_apply(arm_y, sorted(ids))) == 2


def test_exclusion_is_applied_before_limit_in_the_source():
    """ORDERING, pinned against the source text.

    If `--limit` ran first, a smoke's exclusion would depend on which rows the stratifier happened
    to pick, and `--expect-n` would mean a different thing in two arms. The order is not
    incidental, so it is asserted rather than trusted.
    """
    src = io.open(os.path.join(ROOT, "src", "boombness", "score_behavior.py"),
                  encoding="utf-8").read()
    i_excl = src.index("if args.exclude_prompt_ids:")
    i_limit = src.index("    if args.limit:\n        # STRATIFIED")
    i_expect = src.index("if args.expect_n and len(rows) != args.expect_n:")
    assert i_excl < i_limit < i_expect, "exclusion must precede --limit, which precedes --expect-n"


def _apply_with_count_check(rows, ids):
    """`main`'s full predicate, including the exactly-once check the membership test cannot make."""
    kept = _apply(rows, ids)
    if len(kept) != len(rows) - len(ids):
        raise SystemExit(f"REFUSING: excluding {len(ids)} declared prompt_id(s) removed "
                         f"{len(rows) - len(kept)} rows, not {len(ids)}.")
    return kept


def test_REFUSES_when_the_bank_repeats_a_prompt_id():
    """One listed id, two rows removed -- and `n_excluded = 1` would misdescribe the population."""
    rows = [{"prompt_id": "a"}, {"prompt_id": "a"}, {"prompt_id": "b"}]
    with pytest.raises(SystemExit) as e:
        _apply_with_count_check(rows, ["a"])
    assert "removed 2 rows, not 1" in str(e.value)


def test_MUTANT_membership_check_alone_would_pass_the_duplicated_bank():
    """Executed proof that the two checks are not the same check.

    `_apply` -- membership only -- accepts the duplicated bank and silently returns one row fewer
    than the recorded exclusion count implies. This is why the count assertion is a refusal in its
    own right rather than a redundant `assert`.
    """
    rows = [{"prompt_id": "a"}, {"prompt_id": "a"}, {"prompt_id": "b"}]
    assert len(_apply(rows, ["a"])) == 1, "membership-only passes and drops two rows for one id"


@pytest.mark.skipif(not os.path.exists(BASKET_BANK), reason="basket bank absent")
def test_the_real_basket_bank_has_no_duplicate_prompt_ids():
    """The refusal above must not be the thing that fires on the run we are about to launch."""
    import collections
    rows = [json.loads(l) for l in io.open(BASKET_BANK, encoding="utf-8")]
    dupes = [k for k, v in collections.Counter(r["prompt_id"] for r in rows).items() if v > 1]
    assert dupes == [], f"duplicated prompt_ids in the basket bank: {dupes[:5]}"
