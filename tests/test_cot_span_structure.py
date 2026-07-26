"""Torch-free unit tests for cot_span_structure_analysis.

Fixtures embed sentinel `goal` / `preview` text fields; the tests confirm the
analysis output NEVER depends on them (the loader drops them, and setting them to
different sentinels does not change any computed number). Tests use only synthetic,
non-harmful placeholder strings for those sentinels.
"""
import importlib.util
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SCRIPT = os.path.join(ROOT, "scripts", "cot_span_structure_analysis.py")

spec = importlib.util.spec_from_file_location("cssa", SCRIPT)
cssa = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cssa)


def _inst(cs, ce, ts, te, preview="SENTINEL_PREVIEW_DO_NOT_READ"):
    return {
        "char_start": cs, "char_end": ce, "tok_start": ts, "tok_end": te,
        "preview": preview,
    }


def _comp(located, instances):
    return {"located": located, "instances": instances}


def _record(is_success, n_tokens, spans, coverage_misses=None,
            goal="SENTINEL_GOAL_DO_NOT_READ"):
    full = {c: _comp(False, []) for c in cssa.COMPONENTS}
    full.update(spans)
    return {
        "is_success": is_success,
        "n_tokens": n_tokens,
        "judge_score": 10 if is_success else 1,
        "content_char_len": 100,
        "coverage_misses": coverage_misses or [],
        "goal": goal,
        "spans": full,
    }


def _write_jsonl(path, records):
    with open(path, "w") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")


def _build(tmp_path):
    """Two records: one success, one fail, with known geometry."""
    # SUCCESS: injected_reasoning located at tok 50..100 of n=100 -> norm 0.5..1.0,
    # len 50; final_answer_cue located; harmful_instruction NOT located.
    succ = _record(
        True, 100,
        {
            "injected_reasoning": _comp(True, [_inst(0, 0, 50, 100)]),
            "final_answer_cue": _comp(True, [_inst(0, 0, 90, 95)]),
        },
        coverage_misses=["harmful_instruction"],
    )
    # FAIL: injected_reasoning NOT located; final_answer_cue located at 0..10 of n=200
    # -> norm 0..0.05, len 10; two instances of benign_puzzle_scaffold.
    fail = _record(
        False, 200,
        {
            "final_answer_cue": _comp(True, [_inst(0, 0, 0, 10)]),
            "benign_puzzle_scaffold": _comp(
                True, [_inst(0, 0, 0, 20), _inst(0, 0, 40, 60)]
            ),
        },
        coverage_misses=["injected_reasoning", "final_answer_cue"],
    )
    p = os.path.join(tmp_path, "TestModel_spans.jsonl")
    _write_jsonl(p, [succ, fail])
    return p


def test_presence_and_positions(tmp_path):
    tmp = str(tmp_path)
    _build(tmp)
    files = cssa.discover_spans(tmp)
    assert len(files) == 1
    records = list(cssa.load_records(files[0]))
    results, denom = cssa.analyze_model(records)

    assert denom[True] == 1 and denom[False] == 1

    # injected_reasoning presence: 1.0 in success, 0.0 in fail.
    assert results[("injected_reasoning", True)]["presence_rate"] == 1.0
    assert results[("injected_reasoning", False)]["presence_rate"] == 0.0

    # final_answer_cue present in both splits.
    assert results[("final_answer_cue", True)]["presence_rate"] == 1.0
    assert results[("final_answer_cue", False)]["presence_rate"] == 1.0

    # Normalized position for injected_reasoning success: 50/100 .. 100/100.
    ir = results[("injected_reasoning", True)]
    assert abs(ir["mean_norm_tok_start"] - 0.5) < 1e-9
    assert abs(ir["mean_norm_tok_end"] - 1.0) < 1e-9
    assert abs(ir["mean_tok_len"] - 50) < 1e-9

    # final_answer_cue fail: 0/200 .. 10/200.
    fc = results[("final_answer_cue", False)]
    assert abs(fc["mean_norm_tok_start"] - 0.0) < 1e-9
    assert abs(fc["mean_norm_tok_end"] - 0.05) < 1e-9
    assert abs(fc["mean_tok_len"] - 10) < 1e-9


def test_counts_and_misses(tmp_path):
    tmp = str(tmp_path)
    _build(tmp)
    files = cssa.discover_spans(tmp)
    results, _ = cssa.analyze_model(list(cssa.load_records(files[0])))

    # benign_puzzle_scaffold has 2 instances in the fail record.
    assert results[("benign_puzzle_scaffold", False)]["mean_count"] == 2.0
    assert results[("benign_puzzle_scaffold", True)]["mean_count"] == 0.0

    # coverage_misses: harmful_instruction missed once in success (rate 1/1=1.0).
    assert results[("harmful_instruction", True)]["miss_rate"] == 1.0
    # injected_reasoning + final_answer_cue missed in the fail record.
    assert results[("injected_reasoning", False)]["miss_rate"] == 1.0
    assert results[("final_answer_cue", False)]["miss_rate"] == 1.0
    # not missed in success.
    assert results[("injected_reasoning", True)]["miss_rate"] == 0.0


def test_output_independent_of_forbidden_fields(tmp_path):
    """Changing `goal` / `preview` sentinels must not change any computed number."""
    tmp = str(tmp_path)
    p = _build(tmp)
    files = cssa.discover_spans(tmp)
    baseline, _ = cssa.analyze_model(list(cssa.load_records(files[0])))

    # Rewrite the same records but with different forbidden-field sentinels.
    with open(p) as f:
        recs = [json.loads(line) for line in f]
    for r in recs:
        r["goal"] = "COMPLETELY_DIFFERENT_SENTINEL_GOAL"
        for comp in r["spans"].values():
            for inst in comp["instances"]:
                inst["preview"] = "COMPLETELY_DIFFERENT_SENTINEL_PREVIEW"
    _write_jsonl(p, recs)
    perturbed, _ = cssa.analyze_model(list(cssa.load_records(files[0])))

    assert baseline == perturbed

    # Also confirm the loader never surfaces forbidden fields downstream.
    for rec in cssa.load_records(files[0]):
        assert "goal" not in rec
        for comp in rec["spans"].values():
            for inst in comp["instances"]:
                assert "preview" not in inst


def test_csv_and_md_written(tmp_path):
    tmp = str(tmp_path)
    _build(tmp)
    per_model = {}
    files = cssa.discover_spans(tmp)
    for path in files:
        model = cssa.model_name_from_path(path)
        per_model[model] = cssa.analyze_model(list(cssa.load_records(path)))
    out_csv = os.path.join(tmp, "out.csv")
    out_md = os.path.join(tmp, "out.md")
    cssa.write_csv(out_csv, per_model)
    cssa.write_md(out_md, per_model)
    assert os.path.exists(out_csv) and os.path.exists(out_md)
    with open(out_csv) as f:
        header = f.readline().strip().split(",")
    assert header == [
        "model", "component", "success_bool", "presence_rate",
        "mean_norm_tok_start", "mean_norm_tok_end", "mean_tok_len",
        "mean_count", "miss_rate", "n",
    ]
    # md must not leak sentinel forbidden text.
    with open(out_md) as f:
        md = f.read()
    assert "SENTINEL_GOAL" not in md
    assert "SENTINEL_PREVIEW" not in md
