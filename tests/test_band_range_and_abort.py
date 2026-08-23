"""Two guards from the 2026-08-24 adversarial review, each tested against the PRE-FIX behaviour.

S3 -- BAND RANGE. Nothing validated an `--intervene` band against the model's block count. The two
failure directions are asymmetric and only one of them is loud:

  * `hi >= num_layers` raises IndexError inside AllQueryAttentionKnockout.__init__, which sits INSIDE
    the per-row try -- so it becomes 96 silent ledger failures and a written summary.json before
    assert_knockout_live finally raises on n_rows == 0.
  * a band NARROWER than intended fails SILENTLY as a weaker intervention. Porting Llama's `0-31` to
    a 40-block Qwen3 gives an "all layers" arm covering 32/40 that scores as a clean partial null.
    No exception can catch that, which is why the guard ECHOES the resolved band rather than only
    bounds-checking it.

S2 -- ABORTED MARKER. The thinking-off probe raises SystemExit, a BaseException, so the per-row
`except Exception` does not catch it: the process dies mid-loop with ~24 rows already flushed to
gens.jsonl and no DONE.json. judge_boombness reads gens.jsonl, so that is a judgeable partial -- the
same shape as the InfeasibleControl defect already fixed once this phase. scripts/judge_p2.sh:55
refuses a dir without DONE.json, but that is the DRIVER's guard; a direct judge call bypasses it.

Run:  python -m pytest tests/test_band_range_and_abort.py -q
"""
import os
import re

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "boombness",
                   "score_behavior.py")


def _src():
    return open(SRC).read()


# --------------------------------------------------------------------------- S3
def test_band_is_validated_against_the_models_block_count():
    s = _src()
    assert "hi >= lm.num_layers" in s, "the band range check is gone"
    i = s.index("hi >= lm.num_layers")
    assert "REFUSING" in s[i:i + 300], "an out-of-range band no longer refuses"


def test_malformed_band_refuses():
    s = _src()
    assert "0 <= lo <= hi" in s, "the malformed-band check is gone"


def test_the_resolved_band_is_ECHOED_not_only_bounds_checked():
    """The dangerous direction is a band that is too NARROW, which no exception can catch."""
    s = _src()
    i = s.index("hi >= lm.num_layers")
    window = s[i:i + 900]
    assert "blocks {lo}..{hi} of {lm.num_layers}" in window or "-> blocks" in window, \
        "the resolved band is not printed, so a silently-narrow band stays invisible"
    assert "depth" in window, "the depth fraction is not echoed, so cross-model bands cannot be checked"


def test_the_check_runs_BEFORE_the_spec_is_built():
    """A check after the hook is built is a check after the IndexError."""
    s = _src()
    assert s.index("hi >= lm.num_layers") < s.index('specs.append({"direction": name'), \
        "the range check moved below spec construction, where it can no longer prevent the IndexError"


def test_the_real_ported_band_would_have_been_caught():
    """PRE-FIX REGRESSION. Llama's all-layers arm is 0-31; Qwen3 has 40 blocks.

    This is the case that motivated the guard: 0-31 on a 40-block model is not an error, it is a
    weaker knockout that scores as a clean null. Asserted as arithmetic so it documents the trap
    even if the source is refactored.
    """
    llama_all, qwen_blocks = (0, 31), 40
    assert llama_all[1] < qwen_blocks - 1, "0-31 would be in range on Qwen3 -- and cover only 32/40"
    assert (llama_all[1] + 1) / qwen_blocks == 0.8, "0-31 covers 80% of a 40-block model"


# --------------------------------------------------------------------------- S2
def test_thinking_probe_writes_an_ABORTED_marker_before_it_raises():
    s = _src()
    i = s.index('REFUSING: --enable-thinking false')
    before = s[max(0, i - 1600):i]
    assert "run.abort(" in before, (
        "the thinking-off refusal no longer writes ABORTED.json first; it would leave a partial, "
        "judgeable gens.jsonl with no DONE.json")


def test_the_abort_cannot_mask_the_real_refusal():
    """If run.abort() itself throws, the SystemExit must still happen."""
    s = _src()
    i = s.index('REFUSING: --enable-thinking false')
    before = s[max(0, i - 1600):i]
    assert "except Exception as _e" in before, "a failing abort() would swallow the refusal"
    assert "raise SystemExit" in s[i - 200:i + 200], "the refusal itself is gone"


def test_it_is_still_a_SystemExit_and_not_downgraded():
    """The run MUST die. Downgrading to a normal Exception would let the per-row handler swallow it
    and continue generating rows that contain no answer to judge -- worse than the original bug."""
    s = _src()
    i = s.index('REFUSING: --enable-thinking false')
    assert "raise SystemExit(" in s[i - 300:i], "the thinking refusal was downgraded to a catchable exception"


def test_abort_writes_no_DONE_json():
    """The whole point: common.require_done must refuse the dir afterwards."""
    common = open(os.path.join(os.path.dirname(SRC), "common.py")).read()
    i = common.index("def abort(")
    body = common[i:i + 3000]
    assert "ABORTED.json" in body
    assert re.search(r"NO DONE\.json|NOT DONE\.json", body), \
        "abort() no longer documents that it withholds DONE.json"
