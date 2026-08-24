"""Tests for the excluded-runs manifest (plan §2.2).

Every assertion here goes through the real implementation in src/boombness/excluded_runs.py -- the
classification rules are NOT restated. A test that re-implemented "aborted beats no_done_json" would
pass against a scanner that had forgotten the rule entirely.
"""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.boombness import excluded_runs as ex  # noqa: E402


# --------------------------------------------------------------------------- #
# fixture: a fake outputs tree with one of each shape
# --------------------------------------------------------------------------- #
def _mkrun(exp_dir, run_id, files):
    d = os.path.join(exp_dir, run_id)
    os.makedirs(os.path.join(d, "plots"), exist_ok=True)
    for name, payload in files.items():
        with open(os.path.join(d, name), "w") as f:
            f.write(payload)
    return d


@pytest.fixture
def tree(tmp_path):
    """outputs_root/fakeexp/ with: complete, no-DONE-with-results, empty skeleton, aborted."""
    root = str(tmp_path / "outputs" / "boombness")
    exp = os.path.join(root, "fakeexp")
    os.makedirs(exp)
    boiler = {"config.json": "{}", "RUNMETA.json": '{"schema": "RUNMETA/1"}'}

    complete = _mkrun(exp, "tagA_20260824_120500_111", dict(
        boiler, **{"crossbank_test.json": '{"rows": [1, 2, 3]}',
                   "metadata.json": "{}", "summary.json": "{}",
                   "DONE.json": '{"schema": "DONE/1", "status": "ok"}'}))
    # the dangerous shape: a plausible full results file that finish() never blessed
    nodone = _mkrun(exp, "tagA_20260824_120000_222", dict(
        boiler, **{"crossbank_test.json": '{"rows": [1, 2, 3]}'}))
    skeleton = _mkrun(exp, "tagA_20260824_115000_333", dict(boiler))
    aborted = _mkrun(exp, "tagB_20260824_090000_444", dict(
        boiler, **{"results.jsonl": '{"row": 1}\n', "summary.json": "{}",
                   "ABORTED.json": '{"reason": "gate tripped"}'}))
    return {"root": root, "exp": exp, "complete": complete, "nodone": nodone,
            "skeleton": skeleton, "aborted": aborted}


# --------------------------------------------------------------------------- #
def test_classifies_all_three_shapes(tree):
    assert ex.classify_run(tree["complete"]) is None, "a finished run must not be excluded"

    nod = ex.classify_run(tree["nodone"])
    assert nod["reason"] == "no_done_json"
    assert nod["has_partial_results"] is True
    assert "crossbank_test.json" in nod["detail"]

    skel = ex.classify_run(tree["skeleton"])
    assert skel["reason"] == "empty_skeleton"
    assert skel["has_partial_results"] is False


def test_aborted_beats_no_done_json(tree):
    """A dir carrying ABORTED.json is 'aborted', not 'no_done_json' -- it announced its own death."""
    row = ex.classify_run(tree["aborted"])
    assert row["reason"] == "aborted"
    assert row["has_partial_results"] is True  # it did write rows before aborting


def test_aborted_beats_done_when_both_present(tmp_path):
    """The T12 abort-after-finish shape (real on disk in extract_boombness): the abort wins."""
    exp = str(tmp_path / "outputs" / "boombness" / "fakeexp")
    os.makedirs(exp)
    d = _mkrun(exp, "tagC_20260824_100000_555", {
        "DONE.json": "{}", "ABORTED.json": "{}", "results.jsonl": '{"row": 1}\n'})
    row = ex.classify_run(d)
    assert row is not None and row["reason"] == "aborted"


def test_superseded_by_is_nearest_later_completed_same_tag(tree):
    res = ex.scan_experiment(tree["exp"])
    assert res["n_dirs"] == 4
    assert res["n_missing_done"] == 3
    by_id = {r["run_id"]: r for r in res["rows"]}
    assert set(by_id) == {"tagA_20260824_120000_222", "tagA_20260824_115000_333",
                          "tagB_20260824_090000_444"}
    # both tagA failures are superseded by the one completed tagA run
    assert by_id["tagA_20260824_120000_222"]["superseded_by"] == "tagA_20260824_120500_111"
    assert by_id["tagA_20260824_115000_333"]["superseded_by"] == "tagA_20260824_120500_111"
    # tagB has no completed sibling -> null, not a guess
    assert by_id["tagB_20260824_090000_444"]["superseded_by"] is None


def test_no_successor_when_completed_run_is_earlier(tmp_path):
    exp = str(tmp_path / "outputs" / "boombness" / "fakeexp")
    os.makedirs(exp)
    _mkrun(exp, "t_20260824_080000_1", {"DONE.json": "{}", "results.jsonl": "x\n"})
    _mkrun(exp, "t_20260824_090000_2", {"results.jsonl": "x\n"})
    rows = ex.scan_experiment(exp)["rows"]
    assert len(rows) == 1 and rows[0]["superseded_by"] is None


def test_parse_run_id_handles_underscored_tags():
    assert ex.parse_run_id("ctrl_rand_s20260820_20260817_042112_3090178")["tag"] == \
        "ctrl_rand_s20260820"
    assert ex.parse_run_id("not_a_run_dir")["stamp"] is None


# --------------------------------------------------------------------------- #
def test_manifest_schema_validates(tree):
    m = ex.build_manifest(tree["root"], ["fakeexp"])
    ex.validate_manifest(m)  # raises on any violation
    assert m["schema"] == ex.SCHEMA
    assert m["n_excluded"] == 3
    assert m["per_experiment"]["fakeexp"]["n_dirs"] == 4
    assert all(r["safe_to_delete"] is False for r in m["runs"])
    assert all(r["reason"] in ex.REASONS for r in m["runs"])


def test_validate_rejects_safe_to_delete_true(tree):
    m = ex.build_manifest(tree["root"], ["fakeexp"])
    m["runs"][0]["safe_to_delete"] = True
    with pytest.raises(ValueError, match="never authorises deletion"):
        ex.validate_manifest(m)


def test_validate_rejects_unknown_reason(tree):
    m = ex.build_manifest(tree["root"], ["fakeexp"])
    m["runs"][0]["reason"] = "looked_wrong"
    with pytest.raises(ValueError, match="outside"):
        ex.validate_manifest(m)


def test_validate_rejects_wrong_schema():
    with pytest.raises(ValueError, match="expected"):
        ex.validate_manifest({"schema": "EXCLUDED_RUNS/0", "written_at": None,
                              "written_by_commit": None, "runs": []})


# --------------------------------------------------------------------------- #
def test_is_excluded_agrees_with_manifest(tree, tmp_path, monkeypatch):
    monkeypatch.setattr(ex, "REPO_ROOT", str(tmp_path))
    ex._CACHE.clear()
    path = str(tmp_path / "EXCLUDED_RUNS.json")
    ex.write_manifest(ex.build_manifest(tree["root"], ["fakeexp"]), path)

    listed = {r["run_dir"] for r in json.load(open(path))["runs"]}
    for d in (tree["nodone"], tree["skeleton"], tree["aborted"]):
        assert os.path.relpath(d, str(tmp_path)) in listed
        assert ex.is_excluded(d, path) is True
    assert ex.is_excluded(tree["complete"], path) is False

    # repo-relative input must resolve the same way as absolute input
    assert ex.is_excluded(os.path.relpath(tree["nodone"], str(tmp_path)), path) is True


def test_filter_run_dirs_drops_only_excluded(tree, tmp_path, monkeypatch):
    monkeypatch.setattr(ex, "REPO_ROOT", str(tmp_path))
    ex._CACHE.clear()
    path = str(tmp_path / "EXCLUDED_RUNS.json")
    ex.write_manifest(ex.build_manifest(tree["root"], ["fakeexp"]), path)

    globbed = [tree["complete"], tree["nodone"], tree["skeleton"], tree["aborted"]]
    assert ex.filter_run_dirs(globbed, path) == [tree["complete"]]


def test_missing_manifest_excludes_nothing(tmp_path):
    ex._CACHE.clear()
    path = str(tmp_path / "nope.json")
    assert ex.load_manifest(path, use_cache=False)["runs"] == []
    assert ex.is_excluded(str(tmp_path), path) is False


# --------------------------------------------------------------------------- #
def test_scanner_never_deletes(tree, tmp_path, monkeypatch):
    """The skeletons are evidence of a debugging sequence. Scanning must not perturb the tree."""
    def snapshot():
        seen = {}
        for dirpath, dirnames, filenames in os.walk(tree["root"]):
            dirnames.sort()
            for fn in sorted(filenames):
                p = os.path.join(dirpath, fn)
                seen[os.path.relpath(p, tree["root"])] = os.path.getsize(p)
            for dn in dirnames:
                seen[os.path.relpath(os.path.join(dirpath, dn), tree["root"]) + "/"] = -1
        return seen

    before = snapshot()
    monkeypatch.setattr(ex, "REPO_ROOT", str(tmp_path))
    ex._CACHE.clear()
    out = str(tmp_path / "EXCLUDED_RUNS.json")
    ex.main(["--outputs-root", tree["root"], "--experiments", "fakeexp", "--out", out, "--write"])
    ex.is_excluded(tree["nodone"], out)
    ex.filter_run_dirs([tree["nodone"], tree["complete"]], out)
    assert snapshot() == before, "the scanner altered the run tree"


def test_committed_manifest_is_valid_and_matches_disk():
    """The artifact in outputs/boombness/ must still describe the tree it claims to describe."""
    path = ex.DEFAULT_MANIFEST
    if not os.path.exists(path):
        pytest.skip("manifest not generated in this checkout")
    m = ex.load_manifest(path, use_cache=False)
    ex.validate_manifest(m)
    assert m["runs"], "the manifest is empty; the known no-DONE dirs are missing from it"
    for row in m["runs"]:
        full = os.path.join(ex.REPO_ROOT, row["run_dir"])
        if not os.path.isdir(full):
            continue
        assert ex.classify_run(full)["reason"] == row["reason"], row["run_dir"]
    # the specific dangerous directory the audit flagged: full results payload, no DONE, no summary
    danger = ("outputs/boombness/crossbank_knockout_test/xb8_20260824_192125_1606107")
    if os.path.isdir(os.path.join(ex.REPO_ROOT, danger)):
        row = next(r for r in m["runs"] if r["run_dir"] == danger)
        assert row["reason"] == "no_done_json" and row["has_partial_results"] is True
        assert ex.is_excluded(danger, path) is True
