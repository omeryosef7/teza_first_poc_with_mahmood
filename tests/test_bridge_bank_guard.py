"""`binding_behaviour_bridge` must refuse a bank that is not the runs' own population.

WHY (found 2026-08-26 by actually EXECUTING the reproduction manifest rather than trusting it).
`fam` is keyed by prompt_id and the join skips any row the bank does not know. The carrot bank's
2736 ids are a strict SUBSET of the d10 bank's 4560, so pointing the script at the carrot bank
while handing it d10 judge dirs kept **96 of 160 rows** and printed a complete-looking answer with
different numbers (7/41 became 10/38). Nothing noticed.

No published result was affected — R-16 and R-17's actual pairings were verified matched, 0 rows
outside the bank — but the instrument had no guard, which is the same silent-subset class this
sprint has already paid for more than once.
"""

from __future__ import annotations

import os

SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "src", "boombness", "binding_behaviour_bridge.py")


def _src():
    return open(SRC).read()


def test_bridge_refuses_rows_outside_the_bank():
    s = _src()
    assert "REFUSING" in s and "not in " in s
    assert 'for _name, _ids in (("beh_baseline", b0), ("probe_baseline", p0)):' in s


def test_guard_checks_both_populations_not_just_one():
    """A guard on the behavioural side alone would still let a mismatched probe bank through."""
    s = _src()
    i = s.index('for _name, _ids in ((')
    block = s[i:i + 900]
    assert '"beh_baseline", b0' in block and '"probe_baseline", p0' in block


def test_guard_runs_before_any_arm_is_read():
    """Refusing after computing arms would still emit a partial artifact."""
    s = _src()
    assert s.index("for _name, _ids in ((") < s.index("beh_arms = {")


# --------------------------------------------------------------------------- #
# C-27: everything above reads this module's SOURCE TEXT. That catches the guard being DELETED
# and NOT the guard being disabled. Measured 2026-08-27: rewriting `if _missing:` as
# `if False and _missing:` left every test in this file green — and that guard is C-13, where the
# bridge silently kept 96 of 160 rows and printed a complete-looking answer with different numbers.
#
# The test below EXECUTES the bridge against a bank that is missing ids and requires the refusal.
# It fails whatever the source text still says.
# --------------------------------------------------------------------------- #

def _write_fixture(tmp_path, bank_ids, row_ids):
    """Minimal inputs the bridge accepts: a bank, a judge dir, a probe dir."""
    import json
    bank = tmp_path / "bank.jsonl"
    with open(bank, "w") as fh:
        for p in bank_ids:
            fh.write(json.dumps({"prompt_id": p, "family_id": f"dom|cond|{p}|behavioral",
                                 "query_kind": "behavioral"}) + "\n")
    def _dir(name, payload):
        d = tmp_path / name
        d.mkdir()
        with open(d / "results.jsonl", "w") as fh:
            for p in row_ids:
                fh.write(json.dumps(dict(payload, prompt_id=p)) + "\n")
        return str(d)
    beh = _dir("beh", {"strongreject_score": 0.9})
    probe = _dir("probe", {"p_concept": 0.9, "p_codeword": 0.1})
    return str(bank), beh, probe


def _run(bank, beh, probe, tmp_path):
    import subprocess, sys, os
    repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env = dict(os.environ, BOOMB_OUTPUT_ROOT=str(tmp_path / "out"))
    return subprocess.run(
        [sys.executable, os.path.join(repo, "src", "boombness", "binding_behaviour_bridge.py"),
         "--bank", bank, "--beh-baseline", beh, "--probe-baseline", probe,
         "--tag", "guardtest"],
        capture_output=True, text=True, timeout=180, cwd=repo, env=env)


def test_bridge_REFUSES_when_the_bank_is_missing_row_ids(tmp_path):
    """C-13 executed: bank knows 2 ids, the runs carry 4. The bridge must refuse, not subset."""
    bank, beh, probe = _write_fixture(tmp_path, bank_ids=["a", "b"],
                                      row_ids=["a", "b", "c", "d"])
    proc = _run(bank, beh, probe, tmp_path)
    out = proc.stdout + proc.stderr
    assert proc.returncode != 0, (
        "the bridge RAN against a bank missing 2 of 4 row ids. That is C-13: it silently drops the "
        "unknown rows and prints a complete-looking answer over a different population.")
    assert "REFUSING" in out and "not in" in out, (
        f"it exited non-zero but not via the bank guard; output was:\n{out[-600:]}")
