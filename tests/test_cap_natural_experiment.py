"""The cap pair is only evidence if it is really a continuation, and only informative if it had power.

Two ways this analysis could lie, both of which these tests make fail:
  1. treating a pair as cap-only when the two runs actually differ in something else, so the
     "truncation effect" is really an arm effect;
  2. reporting p=1.0 at 2 discordant pairs as if it were evidence of no effect, when the design
     could not have produced a significant result in EITHER direction.
"""

from __future__ import annotations

import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src", "boombness"))

import cap_natural_experiment as cne  # noqa: E402


def _mk(tmp_path, name, cap, texts, scores, stops, extra_cfg=None):
    gens = tmp_path / "g" / name
    judge = tmp_path / "j" / name
    gens.mkdir(parents=True)
    judge.mkdir(parents=True)
    with open(gens / "gens.jsonl", "w") as fh:
        for i, (t, st) in enumerate(zip(texts, stops)):
            fh.write(json.dumps({"prompt_id": f"p{i}", "generation": t, "stop_reason": st,
                                 "n_new_tokens": cap if st == "length" else 5,
                                 "n_chars": len(t)}) + "\n")
    cfg = {"max_new": cap, "model": "m", "bank": "b", "arm": "A", "tag": name}
    cfg.update(extra_cfg or {})
    json.dump({"args": cfg}, open(gens / "config.json", "w"))
    with open(judge / "results.jsonl", "w") as fh:
        for i, s in enumerate(scores):
            fh.write(json.dumps({"prompt_id": f"p{i}", "strongreject_score": s,
                                 "judge_status": "ok"}) + "\n")
    return str(judge), str(gens)


# --------------------------------------------------------------------------- #
# the exact test itself
# --------------------------------------------------------------------------- #

def test_exact_binomial_matches_hand_computed_values():
    assert cne.exact_two_sided_binomial(0, 0) == 1.0
    assert cne.exact_two_sided_binomial(0, 1) == 1.0            # 1/1 is never significant
    assert cne.exact_two_sided_binomial(0, 5) == pytest.approx(2 / 32)
    # the sprint's actual Llama pair: 5 down of 17 discordant
    assert cne.exact_two_sided_binomial(5, 17) == pytest.approx(0.1435, abs=5e-4)


def test_the_test_is_symmetric():
    for n in (7, 12, 17):
        for k in range(n + 1):
            assert cne.exact_two_sided_binomial(k, n) == pytest.approx(
                cne.exact_two_sided_binomial(n - k, n))


# --------------------------------------------------------------------------- #
# power — the guard against quoting a null that could not have been anything else
# --------------------------------------------------------------------------- #

def test_a_pair_with_too_few_discordant_rows_is_declared_undetectable():
    """At 3 and 2 discordant pairs NO split reaches alpha=0.05. Such a p=1.0 is not evidence."""
    for n_disc in (0, 1, 2, 3, 4, 5):
        pw = cne.min_detectable_net_flips(n_disc, 80)
        assert pw["detectable"] is False, f"n_disc={n_disc} claimed detectable"
        assert pw["min_detectable_delta"] is None


def test_power_reports_the_smallest_shift_the_design_could_have_seen():
    pw = cne.min_detectable_net_flips(17, 96)
    assert pw["detectable"] is True
    # Verified INDEPENDENTLY rather than against a memorised constant -- the first draft of this
    # test asserted 14/17 from a hand computation that was simply wrong, and the code was right.
    k = int(pw["min_one_way_split"].split("/")[0])
    assert cne.exact_two_sided_binomial(k, 17) <= 0.05        # k rejects
    assert cne.exact_two_sided_binomial(k - 1, 17) > 0.05     # k-1 does not: k is the SMALLEST
    assert pw["min_detectable_delta"] == pytest.approx((2 * k - 17) / 96)
    assert pw["min_one_way_split"] == "13/17"                 # 2*P(X>=13)/2**17 = 0.04904
    assert pw["min_detectable_delta"] == pytest.approx(9 / 96)


# --------------------------------------------------------------------------- #
# validity — continuation proof and confound detection
# --------------------------------------------------------------------------- #

def test_a_true_continuation_is_recognised(tmp_path):
    lo = _mk(tmp_path, "lo", 4, ["abcd", "hi"], [0.0, 0.9], ["length", "eos"])
    hi = _mk(tmp_path, "hi", 8, ["abcdefgh", "hi"], [0.9, 0.9], ["eos", "eos"])
    r = cne.compare(lo[0], lo[1], hi[0], hi[1], "t")
    cp = r["continuation_proof"]
    assert cp["is_exact_continuation"] is True
    assert cp["n_byte_identical"] == 1 and cp["n_verbatim_prefix"] == 1
    assert r["cap_only"] is True and r["row_level_valid"] is True
    assert r["paired"]["flips_up"] == 1 and r["paired"]["flips_down"] == 0


def test_a_non_continuation_is_refused(tmp_path):
    """If the high-cap text does not extend the low-cap text, something other than the cap changed."""
    lo = _mk(tmp_path, "lo", 4, ["abcd"], [0.0], ["length"])
    hi = _mk(tmp_path, "hi", 8, ["ZZZZefgh"], [0.9], ["eos"])       # not a prefix
    r = cne.compare(lo[0], lo[1], hi[0], hi[1], "t")
    assert r["continuation_proof"]["is_exact_continuation"] is False
    assert r["row_level_valid"] is False


def test_an_eos_row_that_changed_text_is_refused(tmp_path):
    """A row that ENDED under the small cap must be byte-identical under the large one."""
    lo = _mk(tmp_path, "lo", 4, ["done"], [0.0], ["eos"])
    hi = _mk(tmp_path, "hi", 8, ["done!!"], [0.9], ["eos"])
    r = cne.compare(lo[0], lo[1], hi[0], hi[1], "t")
    assert r["continuation_proof"]["n_byte_identical"] == 0
    assert r["row_level_valid"] is False


def test_a_config_confound_is_flagged_but_row_level_validity_can_still_hold(tmp_path):
    """The Qwen pairs, exactly: n_examples differs because the low-cap run generated a superset,
    yet the common rows are provably the same prompts. Conservative flag, stronger rescue."""
    lo = _mk(tmp_path, "lo", 4, ["abcd"], [0.0], ["length"], {"n_examples": "1,2,4,8"})
    hi = _mk(tmp_path, "hi", 8, ["abcdefgh"], [0.9], ["eos"], {"n_examples": "4,8"})
    r = cne.compare(lo[0], lo[1], hi[0], hi[1], "t")
    assert r["cap_only"] is False
    assert "n_examples" in r["confounding_differences"]
    assert r["row_level_valid"] is True


def test_a_real_arm_difference_is_a_confound_not_an_exemption(tmp_path):
    lo = _mk(tmp_path, "lo", 4, ["abcd"], [0.0], ["length"], {"intervene": ""})
    hi = _mk(tmp_path, "hi", 8, ["abcdefgh"], [0.9], ["eos"], {"intervene": "project_out:L8"})
    r = cne.compare(lo[0], lo[1], hi[0], hi[1], "t")
    assert "intervene" in r["confounding_differences"]


def test_flips_are_counted_in_both_directions(tmp_path):
    """Truncation is not a one-way suppressor; an analysis that only counted 0->1 would lie."""
    lo = _mk(tmp_path, "lo", 4, ["aa", "bb"], [0.0, 0.9], ["length", "length"])
    hi = _mk(tmp_path, "hi", 8, ["aaXX", "bbYY"], [0.9, 0.0], ["eos", "eos"])
    r = cne.compare(lo[0], lo[1], hi[0], hi[1], "t")
    assert r["paired"]["flips_up"] == 1 and r["paired"]["flips_down"] == 1
    assert r["paired"]["delta"] == 0.0
    assert r["among_truncated_rows"] == {"n": 2, "flipped_up": 1, "flipped_down": 1}
