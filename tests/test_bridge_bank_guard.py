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
