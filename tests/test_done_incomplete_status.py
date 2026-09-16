"""BLOCKER-S084: a run that loses rows must SAY SO in its own DONE.json.

The defect these lock down: csi1_button_train_KO_CW_SHUF3 persisted 276 of 670 rows after a GPU
fault and wrote `status: "ok"`. Nothing in the artifact said it was incomplete; a pre-commit guard
caught it hours later. These tests assert the artifact is self-describing.
"""
import json, os, sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "src", "boombness"))
sys.path.insert(0, os.path.join(REPO, "doublespeak_causality"))

import common as C  # noqa: E402


def _finish(tmp_path, n_fail):
    """Drive a REAL RunDir through finish() with `n_fail` failed rows; return its DONE.json."""
    run = C.RunDir("unit_test", tag="s084", out_root=str(tmp_path))
    led = C.FailureLedger()
    led.ok(3)
    for i in range(n_fail):
        led.fail("cuda_error", "bad%d" % i)
    run._n_rows = 3
    path = run.finish(summary={}, ledger=led)
    return json.load(open(os.path.join(path, "DONE.json")))


def test_finish_marks_a_lossy_run_INCOMPLETE(tmp_path):
    """THE regression. A run that lost rows must not call itself ok."""
    d = _finish(tmp_path, n_fail=394)
    assert d["status"] == "INCOMPLETE"
    assert d["n_rows_failed"] == 394
    assert d["rows_written"] == 3
    assert "cuda_error" in d["failure_reasons"]


def test_finish_leaves_a_clean_run_ok(tmp_path):
    d = _finish(tmp_path, n_fail=0)
    assert d["status"] == "ok"
    assert d["n_rows_failed"] == 0


def test_ledger_shape_is_what_the_fix_reads():
    """The fix reads n_failed / n_attempted / failure_reasons off the ledger. Lock the contract."""
    led = C.FailureLedger()
    led.fail("cuda_error", "x1")
    d = led.as_dict()
    assert d["n_failed"] == 1
    assert "cuda_error" in d["failure_reasons"]
    assert "n_attempted" in d


def test_extra_overrides_status_in_write_done(tmp_path):
    """The whole fix rests on write_done letting `extra` override `status`. If that ever changes,
    the fix silently stops working and every incomplete run goes back to claiming ok."""
    import ds_common as dc
    d = str(tmp_path / "r")
    rec = dc.write_done(d, rows_written=5, extra={"status": "INCOMPLETE", "n_rows_failed": 2})
    on_disk = json.load(open(os.path.join(d, "DONE.json")))
    assert rec["status"] == "INCOMPLETE"
    assert on_disk["status"] == "INCOMPLETE"
    assert on_disk["rows_written"] == 5
    assert on_disk["n_rows_failed"] == 2


def test_clean_run_still_says_ok(tmp_path):
    import ds_common as dc
    d = str(tmp_path / "r2")
    dc.write_done(d, rows_written=7, extra={"experiment": "x", "n_rows_failed": 0})
    on_disk = json.load(open(os.path.join(d, "DONE.json")))
    assert on_disk["status"] == "ok", "a run that lost nothing must not be marked INCOMPLETE"


def test_strict_run_dir_admits_documented_short_INCOMPLETE(tmp_path, monkeypatch):
    """DCS-CSI-100 regression: the S-084 fix must not make documented-short runs inadmissible.

    Before S-084 every run said status="ok", so `strict_run_dir`'s status gate was inert. After it,
    a run that legitimately declined 1 row says "INCOMPLETE" -- and this gate began rejecting the
    very runs `allow_short` exists to admit, silently shrinking a control family.
    """
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "rp", os.path.join(REPO, "scripts", "dcs_csi_rederive_patch.py"))
    rp = importlib.util.module_from_spec(spec); spec.loader.exec_module(rp)
    root = tmp_path / "score"
    run = root / "arm_A_20260916_120000_1"
    run.mkdir(parents=True)
    (run / "results.jsonl").write_text("".join('{"i":%d}\n' % i for i in range(669)))
    with open(run / "DONE.json", "w") as fh:
        json.dump({"status": "INCOMPLETE", "rows_written": 669, "n_rows_failed": 1}, fh)
    monkeypatch.setattr(rp, "SCORE_DIR", str(root))
    got = rp.strict_run_dir("arm_A", 670, "results.jsonl", allow_short=3)
    assert got == str(run)

    # ... but a DISHONEST ledger is still refused, which is the check that actually protects us.
    with open(run / "DONE.json", "w") as fh:
        json.dump({"status": "INCOMPLETE", "rows_written": 670, "n_rows_failed": 1}, fh)
    try:
        rp.strict_run_dir("arm_A", 670, "results.jsonl", allow_short=3)
    except SystemExit:   # strict_run_dir refuses via SystemExit, which is NOT an Exception
        pass
    else:
        raise AssertionError("a ledger claiming more rows than the file holds must be refused")
