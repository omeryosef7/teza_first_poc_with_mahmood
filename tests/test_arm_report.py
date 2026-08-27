"""An ASR delta and its divergence must not be separable — that is the whole point of the module.

The failure this guards is concrete: a net of -1 row is a DISSOCIATION at 96/96 divergence and a
DEAD INTERVENTION at 5/96. A table carrying one without the other cannot be read.
"""

from __future__ import annotations

import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src", "boombness"))

import arm_report as ar  # noqa: E402


def _mk(tmp_path, name, n, cap, scores, texts, pinned="openai/gpt-4o-mini"):
    g = tmp_path / "g" / name
    j = tmp_path / "j" / name
    g.mkdir(parents=True)
    j.mkdir(parents=True)
    with open(g / "gens.jsonl", "w") as fh:
        for i in range(n):
            fh.write(json.dumps({"prompt_id": f"p{i}", "generation": texts[i],
                                 "n_chars": len(texts[i]), "n_new_tokens": 50,
                                 "stop_reason": "eos"}) + "\n")
    json.dump({"args": {"max_new": cap, "model": "m", "bank": "b", "arm": name}},
              open(g / "config.json", "w"))
    with open(j / "results.jsonl", "w") as fh:
        for i in range(n):
            r = {"prompt_id": f"p{i}", "strongreject_score": scores[i], "judge_status": "ok",
                 "refused": False}
            if pinned:
                r["judge_model_used"] = pinned
            fh.write(json.dumps(r) + "\n")
    json.dump({"args": {"gens": str(g), "tag": name, "pin_judge_model": pinned}},
              open(j / "config.json", "w"))
    json.dump({"judge": "strongreject_rubric", "judge_null_frac": 0.0},
              open(j / "summary.json", "w"))
    # V-20's completeness contract: a readable run has DONE.json on BOTH the judge and gens dirs.
    # These fixtures predate that guard and were fine without it; when the guard landed it correctly
    # refused all eight tests here. The guard was right and the scaffolding was stale.
    for dd in (j, g):
        json.dump({"schema": "DONE/1", "status": "ok", "rows_written": n},
                  open(dd / "DONE.json", "w"))
    return str(j)


def test_a_real_effect_with_full_divergence_reads_as_one(tmp_path):
    n = 40
    b = _mk(tmp_path, "base", n, 512, [0.9] * 20 + [0.0] * 20, [f"x{i}" for i in range(n)])
    a = _mk(tmp_path, "arm", n, 512, [0.0] * n, [f"y{i}" for i in range(n)])
    r = ar.compare_arm(b, a, "eff")
    assert r["baseline"]["asr_rows"] == 20 and r["arm"]["asr_rows"] == 0
    assert r["paired"]["net_down"] == 20 and r["paired"]["up"] == 0
    assert r["divergence"]["frac_differing"] == 1.0
    assert r["divergence"]["diagnosis"]["verdict"] == "OK"


def test_the_SAME_null_reads_differently_at_different_divergence(tmp_path):
    """The module's reason for existing, as an assertion."""
    n = 40
    scores = [0.9] * 10 + [0.0] * 30
    texts = [f"x{i}" for i in range(n)]
    b1 = _mk(tmp_path, "b1", n, 512, scores, texts)
    live = _mk(tmp_path, "a1", n, 512, scores, [f"CHANGED{i}" for i in range(n)])
    b2 = _mk(tmp_path, "b2", n, 512, scores, texts)
    dead = _mk(tmp_path, "a2", n, 512, scores, texts)          # byte-identical generations

    r_live = ar.compare_arm(b1, live, "dissociation")
    r_dead = ar.compare_arm(b2, dead, "dead")
    # identical ASR story...
    assert r_live["paired"]["net_down"] == r_dead["paired"]["net_down"] == 0
    # ...opposite readings, and only divergence says so
    assert r_live["divergence"]["diagnosis"]["verdict"] == "OK"
    assert r_dead["divergence"]["diagnosis"]["verdict"] == "NOOP_ARM"


def test_divergence_is_always_present_when_gens_exist(tmp_path):
    n = 10
    b = _mk(tmp_path, "b", n, 512, [0.0] * n, ["a"] * n)
    a = _mk(tmp_path, "a", n, 512, [0.0] * n, ["b"] * n)
    assert ar.compare_arm(b, a, "x")["divergence"] is not None


def test_per_arm_floors_are_computed_separately_not_shared(tmp_path):
    """The V-12 result: a baseline with borderline mass faces a HIGHER floor than its knockout arm."""
    n = 40
    b = _mk(tmp_path, "b", n, 512, [0.5] * n, [f"x{i}" for i in range(n)])   # all borderline
    a = _mk(tmp_path, "a", n, 512, [0.0] * n, [f"y{i}" for i in range(n)])   # all confident
    r = ar.compare_arm(b, a, "floors")
    assert r["baseline"]["effective_judge_floor"] > r["arm"]["effective_judge_floor"]


def test_both_caps_travel_and_a_bound_cap_is_labelled(tmp_path):
    n = 20
    texts = ["x"] * n
    b = _mk(tmp_path, "b", n, 192, [0.0] * n, texts)
    a = _mk(tmp_path, "a", n, 192, [0.0] * n, ["y"] * n)
    # force the cap to bind on the arm
    gp = json.load(open(os.path.join(a, "config.json")))["args"]["gens"]
    rows = [json.loads(l) for l in open(os.path.join(gp, "gens.jsonl"))]
    with open(os.path.join(gp, "gens.jsonl"), "w") as fh:
        for i, g in enumerate(rows):
            g["stop_reason"] = "length" if i < 15 else "eos"
            fh.write(json.dumps(g) + "\n")
    r = ar.compare_arm(b, a, "caps")
    assert r["arm"]["max_new"] == 192 and r["baseline"]["max_new"] == 192
    assert r["arm"]["cap_binds"] is True
    assert r["arm"]["asr_label"] == "ASR within first 192 generated tokens"


def test_only_common_prompt_ids_are_compared(tmp_path):
    b = _mk(tmp_path, "b", 20, 512, [0.0] * 20, ["x"] * 20)
    a = _mk(tmp_path, "a", 12, 512, [0.0] * 12, ["y"] * 12)
    assert ar.compare_arm(b, a, "p")["n_common"] == 12


def test_no_generation_text_is_emitted(tmp_path):
    b = _mk(tmp_path, "b", 8, 512, [0.0] * 8, ["SECRETBASE"] * 8)
    a = _mk(tmp_path, "a", 8, 512, [0.0] * 8, ["SECRETARM"] * 8)
    assert "SECRET" not in str(ar.compare_arm(b, a, "s"))


def test_reading_note_is_carried_so_the_pair_cannot_be_split(tmp_path):
    b = _mk(tmp_path, "b", 8, 512, [0.0] * 8, ["a"] * 8)
    a = _mk(tmp_path, "a", 8, 512, [0.0] * 8, ["b"] * 8)
    note = ar.compare_arm(b, a, "n")["READING_NOTE"]
    assert "DISSOCIATION" in note and "DEAD INTERVENTION" in note
