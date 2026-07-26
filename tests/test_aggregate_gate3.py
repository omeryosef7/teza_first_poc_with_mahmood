"""Tests for scripts/aggregate_gate3.py — scalar-only Gate-3 seed aggregator (torch-free)."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts import aggregate_gate3 as ag  # noqa: E402


def _write(path: Path, recs):
    with open(path, "w", encoding="utf-8") as fh:
        for r in recs:
            fh.write(json.dumps(r) + "\n")


def _rec(instr, length, seed, obj, final_sampled, final_greedy=0.0):
    return {
        "instruction": instr,
        "length": length,
        "seed": seed,
        "objective": obj,
        "final_sampled_asr": final_sampled,
        "final_greedy_asr": final_greedy,
        "best_sampled_asr": final_sampled,
        "best_greedy_asr": final_greedy,
    }


def _make_seed(conf: Path, seed, suffix, data):
    """data: {instr: {(length,obj): final_sampled}}."""
    pfx, rfc = [], []
    for instr, cells in data.items():
        for (length, obj), val in cells.items():
            rec = _rec(instr, length, seed, obj, val)
            (pfx if obj == "prefix_ce" else rfc).append(rec)
    _write(conf / f"prefix_ce{suffix}.jsonl", pfx)
    _write(conf / f"reinforce{suffix}.jsonl", rfc)


def test_pairing_and_tally_hand_computed(tmp_path):
    conf = tmp_path
    data = {
        "A": {(5, "prefix_ce"): 0.25, (20, "prefix_ce"): 0.5,
              (5, "reinforce"): 0.5, (20, "reinforce"): 0.75},
        "B": {(5, "prefix_ce"): 0.0, (20, "prefix_ce"): 0.0,
              (5, "reinforce"): 0.0, (20, "reinforce"): 0.0},
    }
    _make_seed(conf, 0, "", data)
    records, present, absent = ag.load_records(conf)
    rows = ag.per_instruction_seed(records)
    assert len(rows) == 2
    by_instr = {r["instruction"]: r for r in rows}
    assert by_instr["A"]["verdict_sampled"] == "R>P"
    assert by_instr["A"]["prefix_ce_final_sampled"] == 0.5
    assert by_instr["A"]["reinforce_final_sampled"] == 0.75
    assert by_instr["B"]["verdict_sampled"] == "tie"
    summ = ag.summarize(rows)
    assert summ["per_seed"][0]["tally"] == {"R>P": 1, "tie": 1, "P>R": 0}
    assert any("prefix_ce_seed1.jsonl" in a for a in absent)


def test_p_greater_than_r(tmp_path):
    conf = tmp_path
    data = {
        "A": {(5, "prefix_ce"): 0.75, (20, "prefix_ce"): 0.5,
              (5, "reinforce"): 0.25, (20, "reinforce"): 0.0},
    }
    _make_seed(conf, 0, "", data)
    records, _, _ = ag.load_records(conf)
    rows = ag.per_instruction_seed(records)
    assert rows[0]["verdict_sampled"] == "P>R"


def test_missing_seed_file_no_crash(tmp_path):
    conf = tmp_path
    data = {"A": {(5, "prefix_ce"): 0.5, (5, "reinforce"): 0.5}}
    _make_seed(conf, 0, "", data)  # only seed 0
    records, present, absent = ag.load_records(conf)
    rows = ag.per_instruction_seed(records)
    assert len(absent) == 4  # 2 arms × seeds {1,2}
    out = ag.format_summary(present, absent, rows, ag.summarize(rows))
    assert "PROXY" in out


def test_multi_seed_consistency(tmp_path):
    conf = tmp_path
    _make_seed(conf, 0, "", {"A": {(5, "prefix_ce"): 0.25, (5, "reinforce"): 0.5}})
    _make_seed(conf, 1, "_seed1", {"A": {(5, "prefix_ce"): 0.5, (5, "reinforce"): 0.5}})
    records, present, absent = ag.load_records(conf)
    rows = ag.per_instruction_seed(records)
    summ = ag.summarize(rows)
    assert summ["seeds"] == [0, 1]
    assert summ["consistency"]["A"] == {"R>P": 1, "tie": 1, "P>R": 0}


def test_best_over_length_reduction(tmp_path):
    conf = tmp_path
    data = {"A": {(5, "prefix_ce"): 0.0, (20, "prefix_ce"): 0.0,
                  (5, "reinforce"): 0.0, (20, "reinforce"): 1.0}}
    _make_seed(conf, 0, "", data)
    records, _, _ = ag.load_records(conf)
    rows = ag.per_instruction_seed(records)
    assert rows[0]["reinforce_final_sampled"] == 1.0
    assert rows[0]["verdict_sampled"] == "R>P"


def test_empty_dir_no_crash(tmp_path):
    records, present, absent = ag.load_records(tmp_path)
    rows = ag.per_instruction_seed(records)
    assert rows == []
    out = ag.format_summary(present, absent, rows, {})
    assert "nothing to aggregate" in out
