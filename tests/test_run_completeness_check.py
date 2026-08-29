"""A run that FINISHED but did not persist all its rows — the d38beh class.

WHY. `d38beh_20260829_022027_2389958` carries a DONE.json, wrote a terminal verdict and parses. It
is missing 77 of 608 rows to a disk quota. Every automated check in this repo accepted it, including
`score_behavior`'s own `--expect-n` guard, which counts BANK rows selected before generation rather
than rows persisted after it.

These tests pin the two things that make the guard worth having: that it FAILS on a short run (with
the exemption lifted, against the real corpus), and that the cell-balance check sees NON-UNIFORM
loss without needing any expectation about totals.
"""
from __future__ import annotations

import glob
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                "src", "boombness"))
import run_completeness_check as rc  # noqa: E402


def test_the_real_corpus_passes_with_its_documented_exemption():
    assert rc.main() == 0


def test_the_KNOWN_SHORT_run_really_IS_short_and_fails_without_its_exemption(monkeypatch):
    """POSITIVE CONTROL against the real artifact, not a synthetic one.

    A peer's rule after finding a guard whose only fire-test used an entry that could never fire:
    an exemption must be demonstrated to be load-bearing.
    """
    monkeypatch.setattr(rc, "KNOWN_SHORT", {})
    assert rc.main() == 1, "lifting the exemption must make the guard fail on the real short run"


def test_every_KNOWN_SHORT_entry_states_a_reason():
    assert rc.KNOWN_SHORT, "the shipped exemption table should not be empty"
    for rid, why in rc.KNOWN_SHORT.items():
        assert isinstance(why, str) and len(why.strip()) > 30, f"{rid} has no real reason"


def test_every_KNOWN_SHORT_entry_is_actually_flagged_by_the_scan():
    """An exemption for a run the scan does not flag is dead weight that hides a future defect."""
    flagged = {rid for rid, _ in rc.scan()[0]}
    for rid in rc.KNOWN_SHORT:
        assert rid in flagged, f"{rid} is exempted but the scan does not flag it"


def test_cell_imbalance_detects_NON_UNIFORM_loss():
    rows = [{"domain": f"d{i}", "n_examples": n} for i in range(4) for n in (1, 2) for _ in range(4)]
    assert rc.cell_imbalance(rows)[2] == 0
    rows = [r for i, r in enumerate(rows) if i not in (0, 1, 2)]      # gut one cell
    modal, n_cells, short = rc.cell_imbalance(rows)
    assert modal == 4 and short == 1, f"expected 1 short cell of {n_cells}, got {short}"


def test_cell_imbalance_is_blind_to_UNIFORM_loss_and_says_so():
    """Stated as a limitation rather than left for someone to discover.

    Dropping one row from EVERY cell lowers the modal count with it, so nothing looks short. That is
    acceptable because uniform loss does not bias a clustered analysis; non-uniform loss does.
    """
    rows = [{"domain": f"d{i}", "n_examples": n} for i in range(4) for n in (1, 2) for _ in range(3)]
    assert rc.cell_imbalance(rows)[2] == 0


def test_the_real_short_run_is_caught_by_BOTH_checks_independently():
    ds = sorted(glob.glob(os.path.join(rc.ROOT, "outputs", "boombness", "score_behavior",
                                       "d38beh_*")))
    if not ds:
        return                                    # artifact pruned; nothing to assert
    rows = [json.loads(l) for l in open(os.path.join(ds[-1], "results.jsonl"), encoding="utf-8")]
    assert len(rows) < 608, "the negative example is no longer short"
    modal, n_cells, short = rc.cell_imbalance(rows)
    assert short > 0, "cell balance must see the loss without knowing the expected total"


def test_the_row_file_is_named_per_root_not_assumed():
    """The guard's own first run reported four retrieval_strength runs as holding 0 rows.

    They hold 96, in retrieval.jsonl. Assuming results.jsonl everywhere is the same
    select-by-a-pattern-I-supplied failure the guard exists to catch.

    STRUCTURAL, not empirical: like the floor test, this restates the mapping a mutation changes, so
    it is not independent evidence. The behavioural proof is
    `test_the_real_corpus_passes_with_its_documented_exemption`, which goes red against the real
    corpus when the mapping is wrong.
    """
    assert rc.ROW_FILE["retrieval_strength"] == "retrieval.jsonl"
    assert rc.ROW_FILE["score_behavior"] == "results.jsonl"


def test_an_EMPTY_scan_is_refused_rather_than_reported_clean(monkeypatch):
    monkeypatch.setattr(rc, "ROW_FILE", {"nonexistent_root": "results.jsonl"})
    assert rc.main() == 1, "a guard that checked nothing must not report success"


def test_the_shipped_floor_is_not_zero():
    """STRUCTURAL, not empirical: this restates the constant a floor mutation changes, so it is not
    independent evidence that the floor WORKS. The behavioural proof is
    `test_an_EMPTY_scan_is_refused_rather_than_reported_clean`, which isolates the mutation on its
    own. Kept because it prevents a future edit lowering the floor silently."""
    assert rc.MIN_EXPECTED >= 50


def _fake_run(tmp_path, expect, rows):
    """A finished run dir on disk, so scan() exercises its real filesystem path."""
    root = tmp_path / "outputs" / "boombness" / "fakeroot" / "r_20260829_000000_1"
    root.mkdir(parents=True)
    (root / "DONE.json").write_text("{}")
    (root / "config.json").write_text(json.dumps({"args": {"expect_n": expect}}))
    (root / "results.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    return tmp_path


def test_the_ROW_COUNT_check_fires_on_loss_the_cell_check_CANNOT_see(tmp_path, monkeypatch):
    """⛔ THE THIRD TEST OF MINE THAT FAILED ITS OWN MUTANT.

    Disabling the row-count check entirely passed all ten tests, because the real short run is ALSO
    cell-imbalanced and the positive control failed through the other check. Two checks, one
    fixture, and nothing distinguished them.

    This fixture is short by a UNIFORM amount — one row missing from every cell — which the cell
    balance is documented as blind to. Only the row-count check can see it.
    """
    rows = [{"domain": f"d{i}", "n_examples": n} for i in range(5) for n in (1, 2) for _ in range(3)]
    tp = _fake_run(tmp_path, expect=40, rows=rows)          # 30 rows against expect 40, balanced
    monkeypatch.setattr(rc, "ROOT", str(tp))
    monkeypatch.setattr(rc, "ROW_FILE", {"fakeroot": "results.jsonl"})
    monkeypatch.setattr(rc, "MIN_EXPECTED", 1)
    monkeypatch.setattr(rc, "KNOWN_SHORT", {})
    probs, checked = rc.scan()
    assert checked == 1
    assert rc.cell_imbalance(rows)[2] == 0, "fixture must be cell-BALANCED or it tests the wrong check"
    assert len(probs) == 1 and "expect-n" in probs[0][1], (
        f"a uniformly-short run must be caught by the ROW COUNT check; got {probs}")


def test_a_complete_balanced_run_passes_the_same_path(tmp_path, monkeypatch):
    """Complement, so the fixture cannot pass by failing everything."""
    rows = [{"domain": f"d{i}", "n_examples": n} for i in range(5) for n in (1, 2) for _ in range(4)]
    tp = _fake_run(tmp_path, expect=40, rows=rows)
    monkeypatch.setattr(rc, "ROOT", str(tp))
    monkeypatch.setattr(rc, "ROW_FILE", {"fakeroot": "results.jsonl"})
    monkeypatch.setattr(rc, "MIN_EXPECTED", 1)
    monkeypatch.setattr(rc, "KNOWN_SHORT", {})
    assert rc.scan()[0] == []


# ---------------------------------------------------------------------------------------------
# CHECK 3 — file agreement (§12.28.1). Complement of the row-count check, NOT a stronger version:
# it sees only ONE-SIDED losses, and its silent-degeneration mode was caught in a live sweep where
# 74 of 585 run pairs had a 0-byte gens.jsonl. Every test below is written to fail a specific
# mutant of that check in isolation.
# ---------------------------------------------------------------------------------------------

def _fake_pair(tmp_path, gens_ids, scored_ids, gens_bytes=None):
    """A DONE run with an independent gens/results id-set. `gens_bytes` writes a raw file instead."""
    root = tmp_path / "outputs" / "boombness" / "fakeroot" / "r_20260829_000000_9"
    root.mkdir(parents=True)
    (root / "DONE.json").write_text("{}")
    (root / "config.json").write_text(json.dumps({"args": {}}))
    (root / "results.jsonl").write_text(
        "".join(json.dumps({"prompt_id": i}) + "\n" for i in scored_ids))
    if gens_bytes is not None:
        (root / "gens.jsonl").write_text(gens_bytes)
    else:
        (root / "gens.jsonl").write_text(
            "".join(json.dumps({"prompt_id": i}) + "\n" for i in gens_ids))
    return tmp_path


def _fa(tmp_path, monkeypatch, gens_ids, scored_ids, gens_bytes=None):
    tp = _fake_pair(tmp_path, gens_ids, scored_ids, gens_bytes)
    monkeypatch.setattr(rc, "ROOT", str(tp))
    monkeypatch.setattr(rc, "ROW_FILE", {"fakeroot": "results.jsonl"})
    return rc.scan_file_agreement()


def test_a_generated_row_that_was_never_scored_is_FLAGGED(tmp_path, monkeypatch):
    """The corruption signature: a row exists in gens and is absent from results."""
    problems, comparable, _ = _fa(tmp_path, monkeypatch, [1, 2, 3], [1, 2])
    assert comparable == 1
    assert len(problems) == 1 and "1 generated rows were NEVER SCORED" in problems[0][1]


def test_results_EXCEEDING_gens_is_NOT_a_defect(tmp_path, monkeypatch):
    """Kills the direction-flip mutant. Partial dumping makes gens a strict subset of results --
    two runs in this corpus are exactly that -- and flagging it would fire on every such run."""
    problems, comparable, _ = _fa(tmp_path, monkeypatch, [1, 2], [1, 2, 3, 4])
    assert comparable == 1, "a strict-subset run is comparable and must be checked, not skipped"
    assert problems == [], "scored-but-not-dumped is partial dumping, not a missing row"


def test_a_ZERO_BYTE_gens_is_NOT_COMPARABLE_rather_than_passing(tmp_path, monkeypatch):
    """⛔ THE MUTANT THAT MOTIVATED CHECK 3'S SHAPE. `if gens and gens != results` passes a 0-byte
    gens file while counting it as checked; 74 of 585 real run pairs are exactly this."""
    problems, comparable, not_comparable = _fa(tmp_path, monkeypatch, [], [1, 2, 3], gens_bytes="")
    assert problems == []
    assert comparable == 0, "an empty gens file is not evidence of agreement"
    assert not_comparable == 1, "it must be COUNTED as unchecked, never silently dropped"


def test_an_absent_gens_file_is_also_NOT_COMPARABLE(tmp_path, monkeypatch):
    tp = _fake_pair(tmp_path, [1], [1])
    os.remove(os.path.join(str(tp), "outputs", "boombness", "fakeroot",
                           "r_20260829_000000_9", "gens.jsonl"))
    monkeypatch.setattr(rc, "ROOT", str(tp))
    monkeypatch.setattr(rc, "ROW_FILE", {"fakeroot": "results.jsonl"})
    problems, comparable, not_comparable = rc.scan_file_agreement()
    assert (problems, comparable, not_comparable) == ([], 0, 1)


def test_gens_rows_WITHOUT_a_prompt_id_are_NOT_COMPARABLE(tmp_path, monkeypatch):
    """A schema change must degrade to 'cannot check', never to 'everything is missing'."""
    problems, comparable, not_comparable = _fa(
        tmp_path, monkeypatch, [], [1, 2], gens_bytes=json.dumps({"other": 1}) + "\n")
    assert problems == [] and comparable == 0 and not_comparable == 1


def test_check_3_has_its_OWN_degenerate_floor_and_it_is_not_zero(monkeypatch):
    """Kills the shared-floor mutant: the comparable population is far smaller than the expect_n
    population, so one floor covering both would let check 3 collapse unnoticed."""
    assert rc.MIN_COMPARABLE > 0 and rc.MIN_COMPARABLE != rc.MIN_EXPECTED
    monkeypatch.setattr(rc, "MIN_COMPARABLE", 10 ** 9)
    assert rc.main() == 1, "a collapsed check 3 must refuse, not report success"


def test_check_3_fires_on_the_REAL_corpus_and_on_exactly_one_run():
    """Anti-vacuity on live data: the check must actually detect d38beh, whose exemption then
    suppresses it. A check that fires nowhere is indistinguishable from one that cannot fire."""
    problems, comparable, _ = rc.scan_file_agreement()
    assert comparable >= rc.MIN_COMPARABLE
    assert [p[0] for p in problems] == ["d38beh_20260829_022027_2389958"]


def test_check_3_sees_FEWER_rows_than_the_row_count_check_on_the_same_run():
    """§12.28.1 as an executable claim: file agreement understates. On d38beh it sees 4 one-sided
    rows where the designed shortfall is 81, so it must never be read as a completeness result."""
    problems, _, _ = rc.scan_file_agreement()
    d38 = [p for p in problems if p[0].startswith("d38beh_20260829")][0]
    seen = int(d38[1].split()[0])
    assert seen < 81, "file agreement cannot see rows missing from BOTH files"


def test_check_3_IS_WIRED_INTO_THE_VERDICT(tmp_path, monkeypatch):
    """⛔ THE MUTANT THAT SURVIVED THE FIRST SEVEN TESTS OF THIS BLOCK.

    Deleting `problems += fa_problems` from `main()` -- so check 3 runs, prints its counts, and its
    findings never reach the exit code -- left all 20 tests passing. Every one of them called
    `scan_file_agreement()` directly and none asserted that the VERDICT consumes it. That is the
    green-on-green shape: the check works, the guard reports success anyway.

    Isolation matters here. d38beh cannot be the fixture, because with `KNOWN_SHORT` emptied it
    fails check 1 as well and `main()` would return 1 either way. This corpus has a file-agreement
    defect and NOTHING else: no `expect_n` anywhere, so check 1 has no opinion at all.
    """
    tp = _fake_pair(tmp_path, gens_ids=[1, 2, 3], scored_ids=[1, 2])
    monkeypatch.setattr(rc, "ROOT", str(tp))
    monkeypatch.setattr(rc, "ROW_FILE", {"fakeroot": "results.jsonl"})
    monkeypatch.setattr(rc, "MIN_EXPECTED", 0)
    monkeypatch.setattr(rc, "MIN_COMPARABLE", 1)
    monkeypatch.setattr(rc, "KNOWN_SHORT", {})
    assert rc.scan()[1] == 0, "fixture must carry no expect_n, or this stops isolating check 3"
    assert rc.main() == 1, "check 3 found a defect and main() did not act on it"
