"""C9's table script must reproduce DR-5's hand audit, and must never emit a bare percentage.

C-13 showed what an untested prose instruction costs. C9 -- the strongest claim in the phase -- had
only a prose manifest row ("join the judge dirs by prompt_id"), so this script exists and these
tests pin it against the numbers DR-5 computed by hand.
"""

from __future__ import annotations

import os

SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "src", "boombness", "rescue_dissociation_table.py")


def _src():
    return open(SRC).read()


def test_margin_is_the_measured_one_not_an_invented_one():
    assert "MARGIN_VS_BASELINE = 0.0521" in _src()


def test_percentage_can_never_travel_without_rows_and_margin():
    """DR-5: the percentage is inverted relative to the evidence when the clean baseline is near
    zero. It stays in the artifact, but never alone."""
    s = _src()
    assert '"pct_of_rise_removed"' in s
    assert '"PCT_CAVEAT"' in s and "INVERTED" in s
    assert '"effect_rows"' in s and '"effect_x_margin"' in s
    # the printed line must carry rows and x-margin too, not just the percent
    assert "effect={v['effect_rows']" in s and "{v['effect_x_margin']" in s


def test_control_is_reported_per_cell_and_not_averaged_away():
    s = _src()
    assert '"control_rows_moved"' in s and '"control_inert"' in s
    assert '"n_cells_control_inert"' in s


def test_refusal_source_is_the_deterministic_detector_not_the_llm_judge():
    s = _src()
    assert '.get("refused")' in s
    assert "kw_refusal" in s and "NOT the LLM judge" in s


def test_it_refuses_duplicate_cell_names_and_malformed_specs():
    s = _src()
    assert "duplicate cell name" in s
    assert "needs 5 colon fields" in s


def test_empty_intersection_is_refused_not_reported_as_zero():
    assert "has no rows common to all four arms" in _src()


# --------------------------------------------------------------------------- #
# R-88: everything above reads this module's SOURCE TEXT, which catches the rule being DELETED and
# not DISABLED. R-87 deprioritised converting this file on the grounds that "a disabled REPORTING
# rule produces a number that looks wrong to a reader". That reasoning is WRONG for this guard, and
# DR-5 is the proof: the published "% of rise removed" figures were 92.3% and 69.2% and they RANKED
# THE CELLS BACKWARDS -- 92.3% was 12 rows / 1.44x margin, 69.2% was 18 rows / 2.16x. Those numbers
# looked entirely right. The failure is invisible, exactly like C-13's, so it earns an executing test.
#
# The invariant: no cell may carry `pct_of_rise_removed` without `effect_rows` and `effect_x_margin`
# beside it. Asserted on real output, not on the source.
# --------------------------------------------------------------------------- #

def _judge_dir(tmp_path, name, ids, score):
    import json, os
    d = tmp_path / name
    d.mkdir()
    with open(d / "results.jsonl", "w") as fh:
        for p in ids:
            fh.write(json.dumps({"prompt_id": p, "strongreject_score": score,
                                 "refused": score < 0.5, "n_examples": 8}) + "\n")
    return str(d)


def test_a_percentage_never_appears_without_its_rows_and_margin(tmp_path):
    """DR-5 executed: run the real script and require rows + x-margin beside every percentage."""
    import json, os, glob, subprocess, sys
    ids = [f"p{i}" for i in range(8)]
    base = _judge_dir(tmp_path, "base", ids, 0.9)     # jailbroken, not refusing
    knock = _judge_dir(tmp_path, "knock", ids, 0.1)   # attack removed, refusing
    resc = _judge_dir(tmp_path, "resc", ids, 0.9)
    ctrl = _judge_dir(tmp_path, "ctrl", ids, 0.1)
    repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out = tmp_path / "out"
    proc = subprocess.run(
        [sys.executable, os.path.join(repo, "src", "boombness", "rescue_dissociation_table.py"),
         "--cell", f"cellA:{base}:{knock}:{resc}:{ctrl}", "--tag", "c9guard"],
        capture_output=True, text=True, timeout=180, cwd=repo,
        env=dict(os.environ, BOOMB_OUTPUT_ROOT=str(out)))
    assert proc.returncode == 0, f"script failed:\n{(proc.stderr or proc.stdout)[-800:]}"
    hits = glob.glob(os.path.join(repo, "outputs", "boombness", "rescue_dissociation_table",
                                  "c9guard_*", "*.json")) + \
           glob.glob(os.path.join(str(out), "**", "c9guard_*", "*.json"), recursive=True)
    payloads = []
    for h in hits:
        try:
            payloads.append(json.load(open(h)))
        except Exception:
            pass
    cells = {}
    for pl in payloads:
        if isinstance(pl, dict):
            cells.update(pl.get("per_cell") or pl.get("cells") or {})
    assert cells, f"no cell payload found; searched {len(hits)} json files"
    for name, v in cells.items():
        if not isinstance(v, dict) or "pct_of_rise_removed" not in v:
            continue
        assert v.get("effect_rows") is not None, (
            f"cell {name} carries a percentage with NO effect_rows. That is DR-5: 92.3% was the "
            f"WEAKEST cell (12 rows / 1.44x) and 69.2% the strongest (18 rows / 2.16x).")
        assert v.get("effect_x_margin") is not None, (
            f"cell {name} carries a percentage with NO effect_x_margin")
