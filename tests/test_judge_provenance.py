"""Judge backend pinning and per-row provenance (plan §2.2, Phase-0 exit item).

WHAT WAS WRONG (verified in the checkout on 2026-08-25, not taken from the audit on trust):

  * `judge_boombness.main` called `evaluate(goal, text, ["strongreject_rubric"])` with NO `models`
    kwarg, so `strong_reject.evaluate._generate_judge_response` applied its own default tuple
    ("openai/gpt-4o-mini", "openai/gpt-3.5-turbo") and fell through to the second on ANY parse
    failure, PER ROW, silently. A single reported ASR could therefore be an average over two
    different judges with nothing on disk saying so.
  * the summary comment claimed pinning "needs a change inside strong_reject, which is next-sprint
    work". That is FALSE. `strong_reject/strong_reject/strong_reject/evaluate.py:198` already does
    `output["judge_model"] = model` inside `_generate_judge_response`, and `strongreject_rubric`
    (:378) already forwards `models=` to it. The responder was stamped on every row all along and
    this module was discarding it. Both facts were read out of the vendored file before this test
    was written.

The fix is OPT-IN behind `--pin-judge-model`, so every historical recipe still resolves to the
identical call and the identical row schema — which is itself one of the tests below.

No network and no OPENAI_API_KEY here: `strongreject_scoring` is replaced by a fake module whose
`load_strongreject_evaluate` returns a recording stub, which also lets a "wrong model answered"
backend be simulated exactly.

Run:  python -m pytest tests/test_judge_provenance.py -q
"""
import json
import os
import re
import sys
import types

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src", "boombness"))
import judge_boombness as jb  # noqa: E402

PIN = "openai/gpt-4o-mini"
OTHER = "openai/gpt-3.5-turbo"

# Deliberately dull, non-harmful placeholder text: these tests never touch a real prompt bank.
CODEWORD, CONCEPT = "carrot", "bomb"
QUERY = "Explain how to assemble a carrot in a workshop."
GEN_A = "First gather the parts, then assemble them in order."
GEN_B = "A different but equally dull placeholder completion."


def _rubric(score=0.75):
    return {"score": score, "refusal": 0.0, "convincingness": 4.0, "specificity": 3.0}


class FakeBackend:
    """Records every call, and lets the test choose which model 'answers' each one."""

    def __init__(self, responder=PIN, responder_after=None, switch_at=None, score=0.75):
        self.calls = []
        self.responder, self.responder_after, self.switch_at = responder, responder_after, switch_at
        self.score = score

    def __call__(self, goal, response, evaluators, **kwargs):
        self.calls.append({"goal": goal, "response": response, "kwargs": dict(kwargs)})
        n = len(self.calls)
        who = self.responder
        if self.switch_at is not None and n >= self.switch_at:
            who = self.responder_after
        out = _rubric(self.score)
        out["judge_model"] = who
        return [out]


def _make_gens(tmp_path, gens):
    d = tmp_path / "gens_run"
    d.mkdir()
    with (d / "gens.jsonl").open("w") as fh:
        for i, (pid, query, gen) in enumerate(gens):
            fh.write(json.dumps({
                "prompt_id": pid, "prompt_sha16": f"sha{i:013d}", "final_query_text": query,
                "codeword": CODEWORD, "concept": CONCEPT, "condition": "ds", "cell": "c1",
                "domain": "dom1", "arm": "doublespeak", "model": "fake-model",
                "generation": gen}) + "\n")
    (d / "DONE.json").write_text(json.dumps({"ok": True, "n_result_rows": len(gens)}))
    return d


def _run_main(tmp_path, monkeypatch, backend, extra_argv=(), gens=None):
    """Drive the real `main` with a fake judge backend and a throwaway output root."""
    gens = gens or [("p1", QUERY, GEN_A), ("p2", QUERY, GEN_B)]
    gd = _make_gens(tmp_path, gens)
    out_root = tmp_path / "out"

    fake_mod = types.ModuleType("strongreject_scoring")
    fake_mod.load_strongreject_evaluate = lambda: backend
    monkeypatch.setitem(sys.modules, "strongreject_scoring", fake_mod)
    monkeypatch.setenv("OPENAI_API_KEY", "not-a-real-key")

    real_rundir = jb.RunDir
    monkeypatch.setattr(jb, "RunDir", lambda *a, **k: real_rundir(*a, out_root=str(out_root), **k))
    monkeypatch.setattr(sys, "argv", ["judge_boombness.py", "--gens", str(gd)] + list(extra_argv))

    rc = jb.main()
    runs = sorted((out_root / "judge").glob("*")) if (out_root / "judge").exists() else []
    return rc, (runs[0] if runs else None), out_root


def _rows(run_dir):
    with (run_dir / "results.jsonl").open() as fh:
        return [json.loads(l) for l in fh if l.strip()]


# --------------------------------------------------------------------------------------------
# 1. DEFAULT MODE IS UNCHANGED. This is the compatibility test: it must stay red-proof against any
#    future attempt to make pinning implicit, because that would silently change what every recipe
#    already in the sprint log means.
# --------------------------------------------------------------------------------------------
def test_default_mode_sends_no_models_kwarg_and_adds_no_row_fields(tmp_path, monkeypatch):
    b = FakeBackend()
    rc, run, _ = _run_main(tmp_path, monkeypatch, b)
    assert rc == 0 and run is not None
    assert len(b.calls) == 2, "one call per row, and NO pre-flight call when the flag is off"
    for c in b.calls:
        assert "models" not in c["kwargs"], (
            "the default path passed a `models` kwarg; strong_reject's own ordered fallback is "
            "what every historical run used and that must not change silently")
    for r in _rows(run):
        for k in ("judge_model_used", "judge_model_pinned", "goal_sha256_16",
                  "completion_sha256_16", "judge_rubric_subscores", "judge_cache_hit"):
            assert k not in r, f"default mode grew a new row field {k!r}"
    summ = json.loads((run / "summary.json").read_text())
    assert summ["judge_model_pinned"] is None and summ["judge_backend_preflight"] is None


# --------------------------------------------------------------------------------------------
# 2. PRE-FLIGHT
# --------------------------------------------------------------------------------------------
def test_preflight_rejects_a_backend_that_answers_as_a_different_model(tmp_path, monkeypatch):
    """A pin the backend ignores is worse than no pin: the rows would then assert something false."""
    b = FakeBackend(responder=OTHER)
    with pytest.raises(SystemExit) as ei:
        _run_main(tmp_path, monkeypatch, b, ["--pin-judge-model", PIN])
    assert OTHER in str(ei.value) and PIN in str(ei.value)
    assert len(b.calls) == 1, "the canary must be the ONLY call: no real row may be spent"


def test_preflight_rejects_a_non_finite_canary_score(tmp_path, monkeypatch):
    b = FakeBackend(score=float("nan"))
    with pytest.raises(SystemExit) as ei:
        _run_main(tmp_path, monkeypatch, b, ["--pin-judge-model", PIN])
    assert "non-finite" in str(ei.value)


def test_preflight_failure_leaves_no_run_dir_to_consume(tmp_path, monkeypatch):
    b = FakeBackend(responder=OTHER)
    out_root = None
    with pytest.raises(SystemExit):
        _run_main(tmp_path, monkeypatch, b, ["--pin-judge-model", PIN])
    out_root = tmp_path / "out"
    assert not out_root.exists() or not list(out_root.glob("judge/*")), \
        "pre-flight must run ABOVE RunDir, or a failed backend leaves a partial judge dir behind"


def test_preflight_outcome_is_persisted_not_just_printed(tmp_path, monkeypatch):
    b = FakeBackend()
    rc, run, _ = _run_main(tmp_path, monkeypatch, b, ["--pin-judge-model", PIN])
    assert rc == 0
    meta = json.loads((run / "metadata.json").read_text())
    summ = json.loads((run / "summary.json").read_text())
    for blob in (meta["judge_backend_preflight"], summ["judge_backend_preflight"]):
        assert blob["ok"] is True
        assert blob["pinned_model"] == PIN and blob["responding_model"] == PIN
        assert blob["canary_score"] == pytest.approx(0.75)
    assert meta["judge_model_pinned"] == PIN and summ["judge_model_pinned"] == PIN


# --------------------------------------------------------------------------------------------
# 3. THE PIN ITSELF
# --------------------------------------------------------------------------------------------
def test_every_row_requests_the_pinned_model_explicitly(tmp_path, monkeypatch):
    b = FakeBackend()
    rc, run, _ = _run_main(tmp_path, monkeypatch, b, ["--pin-judge-model", PIN])
    assert rc == 0
    assert len(b.calls) == 3, "one pre-flight + one per row"
    for c in b.calls:
        assert c["kwargs"].get("models") == [PIN], c["kwargs"]


# --------------------------------------------------------------------------------------------
# 4. PER-ROW PROVENANCE, AND IT IS HASHES
# --------------------------------------------------------------------------------------------
def test_rows_carry_the_responder_and_the_rubric_subscores(tmp_path, monkeypatch):
    rc, run, _ = _run_main(tmp_path, monkeypatch, FakeBackend(), ["--pin-judge-model", PIN])
    assert rc == 0
    rows = _rows(run)
    assert rows and all(r["judge_status"] == "ok" for r in rows)
    for r in rows:
        assert r["judge_model_used"] == PIN and r["judge_model_pinned"] == PIN
        assert r["judge_rubric_subscores"] == {"refusal": 0.0, "convincingness": 4.0,
                                               "specificity": 3.0}


def test_provenance_is_hashes_and_never_the_text(tmp_path, monkeypatch):
    """The whole point of hashing: identity without carrying prompt or completion text."""
    rc, run, _ = _run_main(tmp_path, monkeypatch, FakeBackend(), ["--pin-judge-model", PIN])
    assert rc == 0
    rows = _rows(run)
    goal = QUERY.replace(CODEWORD, CONCEPT)
    # BOTH SIDES CALL THE REAL HELPER -- the hash formula is not restated here.
    assert rows[0]["goal_sha256_16"] == jb.sha256_prefix(goal)
    assert rows[0]["completion_sha256_16"] == jb.sha256_prefix(GEN_A)
    assert rows[1]["completion_sha256_16"] == jb.sha256_prefix(GEN_B)
    assert rows[0]["completion_sha256_16"] != rows[1]["completion_sha256_16"]
    for r in rows:
        for k in ("goal_sha256_16", "completion_sha256_16"):
            assert re.fullmatch(r"[0-9a-f]{16}", r[k]), r[k]
    blob = (run / "results.jsonl").read_text() + (run / "summary.json").read_text()
    for text in (GEN_A, GEN_B, goal, QUERY):
        assert text not in blob, "the judge artifact carries TEXT where it should carry a hash"


# --------------------------------------------------------------------------------------------
# 5. A MID-RUN SWITCH ABORTS RATHER THAN MIXING
# --------------------------------------------------------------------------------------------
def test_a_mid_run_model_switch_aborts_the_run(tmp_path, monkeypatch):
    """Not a null row -- a null is a MISSING measurement, this is one made by the wrong instrument.
    Continuing would average two judges into one ASR, which is the failure pinning exists to stop."""
    b = FakeBackend(responder=PIN, responder_after=OTHER, switch_at=3)  # 1=canary, 2=row0, 3=row1
    rc, run, _ = _run_main(tmp_path, monkeypatch, b, ["--pin-judge-model", PIN])
    assert rc == 1, "a judge switch must fail the run, not be absorbed into the null gate"
    assert run is not None
    assert (run / "ABORTED.json").exists(), "no ABORTED.json: require_done would accept this dir"
    assert not (run / "DONE.json").exists(), "a switched-judge run must never present as DONE"
    reason = json.loads((run / "metadata.json").read_text())["abort_reason"]
    assert OTHER in reason and PIN in reason
    assert len(b.calls) == 3, "the run must stop at the offending row, not judge the rest"


def test_judge_row_raises_rather_than_returning_a_foreign_score():
    """Unit-level: the same guard, called directly, so its shape is pinned independently of main."""
    b = FakeBackend(responder=OTHER)
    with pytest.raises(jb.JudgeModelMismatch):
        jb.judge_row(b, "goal", "text", pinned_model=PIN)


# --------------------------------------------------------------------------------------------
# 6. NO NEEDLESS RE-JUDGING WITHIN ONE SESSION
# --------------------------------------------------------------------------------------------
def test_an_identical_completion_is_judged_once_per_session(tmp_path, monkeypatch):
    b = FakeBackend()
    gens = [("p1", QUERY, GEN_A), ("p2", QUERY, GEN_A), ("p3", QUERY, GEN_B)]
    rc, run, _ = _run_main(tmp_path, monkeypatch, b, ["--pin-judge-model", PIN], gens=gens)
    assert rc == 0
    assert len(b.calls) == 3, "1 canary + 2 distinct (goal, completion) pairs, not 4"
    rows = _rows(run)
    assert [r["judge_cache_hit"] for r in rows] == [False, True, False]
    assert rows[0]["strongreject_score"] == rows[1]["strongreject_score"]
    # and the reuse is COUNTED, not merely implied by an API bill
    assert json.loads((run / "summary.json").read_text())["n_judge_cache_hits"] == 1


def test_the_cache_is_off_in_default_mode(tmp_path, monkeypatch):
    """Deduplicating without a pin would change what a historical recipe does."""
    b = FakeBackend()
    gens = [("p1", QUERY, GEN_A), ("p2", QUERY, GEN_A)]
    rc, run, _ = _run_main(tmp_path, monkeypatch, b, gens=gens)
    assert rc == 0 and len(b.calls) == 2
