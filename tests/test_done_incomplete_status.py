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
