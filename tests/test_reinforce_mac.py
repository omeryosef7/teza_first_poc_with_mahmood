"""
Deterministic CPU unit tests for scripts/reinforce_objective/reinforce_mac.py
(Sprint Completion Plan §D4/§D6 — the REINFORCE-MAC optimizer loop).

PURE-PYTHON / CPU-only: no torch, no GPU model, no downloads. Runs under:
    /usr/bin/python3 -m pytest tests/test_reinforce_mac.py -v

The loop is torch-free orchestration; its two torch-touching operations
(`grad_fn`, `sample_fn`) are INJECTED. Here we pass pure-Python stand-ins so the
full loop runs deterministically on CPU, and assert the §D4/§D6 contract:
  * the loop runs deterministically and records one checkpoint per step;
  * MAC momentum accumulates (m = mu*m + (1-mu)*grad);
  * candidate SELECTION picks the max behavioral-reward candidate (tie-break by
    the first-order surrogate);
  * K>=2 is enforced (raises) with a documented K=1 fallback;
  * advantages are DETACHED (grad-tainted rewards produce plain-float advantages);
  * empty/degenerate steps (no candidates) are handled (step skipped, trigger kept);
  * the module imports with NO torch.
"""

import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT))
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from reinforce_objective import reinforce_mac as M  # noqa: E402


# ---------------------------------------------------------------------------
# Mocks (no torch; deterministic)
# ---------------------------------------------------------------------------

class MockModel:
    """Deterministic TargetModel stub: generation depends only on the prompt.

    `reward_by_trigger` maps a trigger substring appearing in the prompt to a
    canned "harmful" response so a specific candidate can be made best. Any
    prompt not matching returns a benign refusal.
    """

    def __init__(self, harmful_trigger="WIN", harmful_text="HARMFUL step 1 step 2",
                 benign_text="I cannot help with that."):
        self.harmful_trigger = harmful_trigger
        self.harmful_text = harmful_text
        self.benign_text = benign_text

    def _resp(self, prompt):
        return self.harmful_text if self.harmful_trigger in prompt else self.benign_text

    def generate_one(self, prompt, *, do_sample, temperature, seed, max_new_tokens):
        return self._resp(prompt)

    def teacher_forced_logprob(self, prompt, response, *, reduction="sum"):
        # deterministic float; harmful is "more likely" -> higher logprob
        return -2.0 if response == self.harmful_text else -8.0


class MockTokenizer:
    """Minimal tokenizer exposing apply_chat_template (mirrors Qwen3 markers)."""

    def apply_chat_template(self, messages, tokenize=False, add_generation_prompt=True,
                            enable_thinking=None):
        content = messages[0]["content"]
        think = "" if (enable_thinking is None or enable_thinking) else "<think>\n\n</think>\n\n"
        return f"<|im_start|>user\n{content}<|im_end|>\n<|im_start|>assistant\n{think}"


class FakeGradTensor:
    """Stand-in torch scalar that propagates a requires_grad taint; detach clears it."""

    def __init__(self, value, requires_grad=False):
        self.value = float(value)
        self.requires_grad = bool(requires_grad)

    def detach(self):
        return FakeGradTensor(self.value, requires_grad=False)

    def __float__(self):  # torch scalars are float()-able; mirror that
        return self.value


class MockGrad:
    """A grad result with a nested-list `.grad` (torch-free) + advantages."""

    def __init__(self, grad, advantages):
        self.grad = grad
        self.advantages = advantages
        self.log = {}


def make_mock_grad_fn(grad_matrix, advantages=(1.0, -1.0)):
    """grad_fn returning a FIXED nested-list grad so momentum accumulation is checkable."""

    def _fn(model, instruction, trigger, responses, rewards, *, enable_thinking,
            reduction, baseline):
        return MockGrad([list(row) for row in grad_matrix], list(advantages))

    return _fn


def make_mock_sample_fn(candidates_by_step):
    """sample_fn returning a fixed candidate list per step (index by call count)."""
    state = {"i": 0}

    def _fn(model, trigger, momentum_grad, *, B, top_k, n_replace, model_family,
            use_retokenize, token_constraints, tokenizer, rng_seed):
        cands = candidates_by_step[state["i"] % len(candidates_by_step)]
        state["i"] += 1
        # record the momentum grad norm so tests can assert accumulation happened
        _fn.last_momentum = momentum_grad
        return list(cands)

    return _fn


def reward_fn_prefers(harmful_text):
    def _fn(goal, response):
        return 1.0 if response == harmful_text else 0.0
    return _fn


# ---------------------------------------------------------------------------
# Import purity
# ---------------------------------------------------------------------------

def test_module_imports_without_torch():
    assert "torch" not in sys.modules, "importing reinforce_mac must not pull in torch"


# ---------------------------------------------------------------------------
# momentum accumulation (unit) — m = mu*m + (1-mu)*grad, mu=0.6
# ---------------------------------------------------------------------------

def test_momentum_first_step_is_raw_grad():
    g = [[1.0, 2.0], [3.0, 4.0]]
    assert M.momentum_update(None, g, mu=0.6) == g


def test_momentum_accumulates_nested_list():
    g = [[1.0, 0.0]]
    m1 = M.momentum_update(None, g, mu=0.6)          # = g
    m2 = M.momentum_update(m1, g, mu=0.6)            # 0.6*g + 0.4*g = g (constant grad)
    assert m2[0][0] == pytest.approx(1.0)
    # with a DIFFERENT second grad, accumulation is a genuine blend
    m3 = M.momentum_update([[1.0, 0.0]], [[0.0, 0.0]], mu=0.6)  # 0.6*1 + 0.4*0
    assert m3[0][0] == pytest.approx(0.6)
    assert m3[0][1] == pytest.approx(0.0)


def test_momentum_mu_zero_disables():
    assert M.momentum_update([[9.0]], [[1.0]], mu=0.0) == [[1.0]]


# ---------------------------------------------------------------------------
# detached advantages — grad-tainted rewards -> plain-float advantages
# ---------------------------------------------------------------------------

def test_detached_advantages_from_tainted_rewards():
    rewards = [FakeGradTensor(1.0, requires_grad=True), FakeGradTensor(0.0, requires_grad=True)]
    adv = M._detached_advantages(rewards, baseline="rloo", baseline_const=0.0)
    assert all(isinstance(a, float) for a in adv)
    # RLOO K=2 rewards [1,0] -> advantages [+1, -1].
    assert adv[0] == pytest.approx(1.0)
    assert adv[1] == pytest.approx(-1.0)


# ---------------------------------------------------------------------------
# candidate SELECTION picks the max-reward candidate (+ tie-break by surrogate)
# ---------------------------------------------------------------------------

def test_selection_picks_max_reward_candidate():
    model = MockModel(harmful_trigger="WIN")
    tok = MockTokenizer()
    cands = [
        M.CandidateProposal("LOSE1", proxy_score=0.0),
        M.CandidateProposal("WIN", proxy_score=5.0),   # prompt will contain WIN -> harmful
        M.CandidateProposal("LOSE2", proxy_score=-9.0),
    ]
    sel = M.select_candidate_by_reward(
        model, "goal", cands, reward_fn_prefers(model.harmful_text),
        tokenizer=tok, enable_thinking=True, model_family="qwen3",
    )
    assert sel.trigger_str == "WIN"
    assert sel.reward == pytest.approx(1.0)


def test_selection_tie_break_by_surrogate_then_index():
    # All candidates get reward 0 (none harmful) -> tie broken by lowest proxy_score.
    model = MockModel(harmful_trigger="NEVER")
    tok = MockTokenizer()
    cands = [
        M.CandidateProposal("A", proxy_score=1.0),
        M.CandidateProposal("B", proxy_score=-3.0),   # lowest surrogate -> chosen
        M.CandidateProposal("C", proxy_score=1.0),
    ]
    sel = M.select_candidate_by_reward(
        model, "goal", cands, lambda g, r: 0.0,
        tokenizer=tok, enable_thinking=True, model_family="qwen3",
    )
    assert sel.trigger_str == "B"


def test_selection_empty_returns_none():
    model = MockModel()
    assert M.select_candidate_by_reward(
        model, "goal", [], lambda g, r: 0.0,
        tokenizer=MockTokenizer(), enable_thinking=True, model_family="qwen3",
    ) is None


# ---------------------------------------------------------------------------
# end-to-end loop (injected mock grad_fn + sample_fn): deterministic, checkpoints
# ---------------------------------------------------------------------------

def _run_loop(steps=3, K=2, candidates_by_step=None, checkpoint_path=None):
    model = MockModel(harmful_trigger="WIN")
    tok = MockTokenizer()
    if candidates_by_step is None:
        candidates_by_step = [[
            M.CandidateProposal("LOSE", proxy_score=0.0),
            M.CandidateProposal("WIN", proxy_score=1.0),
        ]]
    grad_fn = make_mock_grad_fn([[1.0, 0.0, 0.0]], advantages=(1.0, -1.0))
    sample_fn = make_mock_sample_fn(candidates_by_step)
    res = M.reinforce_mac_optimize(
        model, "do the harmful thing", reward_fn_prefers(model.harmful_text),
        initial_trigger="INIT", steps=steps, K=K, B=4, momentum=0.6,
        enable_thinking=True, tokenizer=tok, model_family="qwen3",
        grad_fn=grad_fn, sample_fn=sample_fn, checkpoint_path=checkpoint_path,
    )
    return res, sample_fn


def test_loop_runs_and_records_one_checkpoint_per_step():
    res, _ = _run_loop(steps=3)
    assert len(res.checkpoints) == 3
    assert [c["step"] for c in res.checkpoints] == [0, 1, 2]
    # every checkpoint has the §C3/§D6 fields
    for c in res.checkpoints:
        for key in ("trigger", "selected_trigger", "mean_reward", "best_reward",
                    "greedy_asr_proxy", "momentum_norm", "selection_reward"):
            assert key in c


def test_loop_selects_winning_trigger_and_tracks_running_best():
    res, _ = _run_loop(steps=2)
    # The WIN candidate produces the harmful response -> reward 1.0 -> selected.
    assert res.best_trigger == "WIN"
    assert res.best_reward == pytest.approx(1.0)
    assert res.final_trigger == "WIN"
    # greedy-ASR proxy fires (reward >= 0.5) at the selected trigger.
    assert res.checkpoints[0]["greedy_asr_proxy"] == 1.0


def test_loop_is_deterministic():
    r1, _ = _run_loop(steps=3)
    r2, _ = _run_loop(steps=3)
    assert [c["selection_reward"] for c in r1.checkpoints] == \
           [c["selection_reward"] for c in r2.checkpoints]
    assert r1.best_trigger == r2.best_trigger


def test_loop_momentum_accumulates_across_steps():
    # Constant grad each step -> momentum norm stays == raw grad norm; but the
    # buffer must be threaded (not None) after step 0. Use a sample_fn that stashes it.
    res, sample_fn = _run_loop(steps=3)
    # After the last step the stashed momentum is a nested list (accumulated), not None.
    assert sample_fn.last_momentum is not None
    assert isinstance(sample_fn.last_momentum, list)
    # momentum_norm recorded and finite in every checkpoint
    assert all(c["momentum_norm"] >= 0.0 for c in res.checkpoints)


def test_loop_advantages_are_plain_floats_in_checkpoints():
    res, _ = _run_loop(steps=1)
    adv = res.checkpoints[0]["advantages"]
    assert all(isinstance(a, float) for a in adv)
    # Both K responses for the INIT trigger are the same benign text (the mock
    # generation depends only on the prompt) -> equal rewards -> zero advantages
    # -> 'neutral'. The towards/away SIGN behavior is covered by
    # tests/test_gpu_runner.py and tests/test_trigger_gradient.py.
    assert res.checkpoints[0]["directions"] == ["neutral", "neutral"]
    assert set(res.checkpoints[0]["directions"]) <= {"towards", "away", "neutral"}


# ---------------------------------------------------------------------------
# K>=2 enforcement + documented K=1 fallback
# ---------------------------------------------------------------------------

def test_k1_raises_by_default():
    model = MockModel()
    with pytest.raises(ValueError, match="K>=2"):
        M.reinforce_mac_optimize(
            model, "goal", lambda g, r: 1.0, K=1, steps=1,
            grad_fn=make_mock_grad_fn([[1.0]]), sample_fn=make_mock_sample_fn([[]]),
        )


def test_k1_fallback_allowed():
    model = MockModel(harmful_trigger="WIN")
    tok = MockTokenizer()
    res = M.reinforce_mac_optimize(
        model, "goal", reward_fn_prefers(model.harmful_text),
        initial_trigger="INIT", steps=1, K=1, B=2, allow_k1_fallback=True,
        tokenizer=tok, grad_fn=make_mock_grad_fn([[1.0]]),
        sample_fn=make_mock_sample_fn([[M.CandidateProposal("WIN", proxy_score=0.0)]]),
    )
    assert len(res.checkpoints) == 1


# ---------------------------------------------------------------------------
# degenerate / empty handling
# ---------------------------------------------------------------------------

def test_empty_candidate_pool_skips_step_and_keeps_trigger():
    res, _ = _run_loop(steps=2, candidates_by_step=[[]])  # sample_fn returns no candidates
    assert all(c["skipped"] for c in res.checkpoints)
    assert all(c["selected_trigger"] == "INIT" for c in res.checkpoints)
    # no behavioral selection happened -> best trigger falls back to the initial one
    assert res.final_trigger == "INIT"


def test_zero_steps_returns_initial_trigger():
    model = MockModel()
    res = M.reinforce_mac_optimize(
        model, "goal", lambda g, r: 0.0, initial_trigger="INIT", steps=0, K=2,
        grad_fn=make_mock_grad_fn([[1.0]]), sample_fn=make_mock_sample_fn([[]]),
    )
    assert res.checkpoints == []
    assert res.best_trigger == "INIT"
    assert res.final_trigger == "INIT"


# ---------------------------------------------------------------------------
# resume-safe checkpoint JSONL
# ---------------------------------------------------------------------------

def test_checkpoint_jsonl_written_and_resumes(tmp_path):
    ckpt = tmp_path / "checkpoints.jsonl"
    res1, _ = _run_loop(steps=2, checkpoint_path=ckpt)
    assert ckpt.exists()
    n_lines = sum(1 for line in ckpt.read_text().splitlines() if line.strip())
    assert n_lines == 2
    # resume: re-run for 3 steps; steps 0,1 already present -> only step 2 added.
    res2, _ = _run_loop(steps=3, checkpoint_path=ckpt)
    n_lines2 = sum(1 for line in ckpt.read_text().splitlines() if line.strip())
    assert n_lines2 == 3
    assert [c["step"] for c in res2.checkpoints] == [0, 1, 2]


# ---------------------------------------------------------------------------
# F2 regression: RESUME must reproduce the single-shot MAC momentum trajectory.
#
# Momentum is m = mu*m + (1-mu)*grad. Before the fix, a resumed run re-seeded the
# buffer from None so the first resumed step used the RAW grad instead of the
# accumulated blend, diverging from an equivalent single-shot run. With a
# step-varying grad the momentum genuinely accumulates, so a resume that does NOT
# persist/reload the buffer produces a different momentum_norm at (and after) the
# resume boundary. This test asserts the FIXED behavior: resumed == single-shot.
# ---------------------------------------------------------------------------

def make_stepwise_grad_fn(grads, start=0):
    """grad_fn returning grads[step] with an internal counter seeded at `start`.

    Seeding at `start` lets a resumed segment (which only executes steps
    start..N) return the SAME per-step grad the single-shot run saw at those
    steps — the resume-fidelity test needs the grad sequence to be a function of
    the absolute step, not of the per-invocation call count."""
    state = {"i": start}

    def _fn(model, instruction, trigger, responses, rewards, *, enable_thinking,
            reduction, baseline):
        g = grads[state["i"] % len(grads)]
        state["i"] += 1
        return MockGrad([list(row) for row in g], [1.0, -1.0])

    return _fn


def make_recording_sample_fn(candidates):
    """sample_fn returning a FIXED candidate list every step and recording the
    momentum buffer it was handed (deep-copied) so the momentum trajectory can be
    compared across single-shot vs resumed runs."""
    import copy

    recorded = []

    def _fn(model, trigger, momentum_grad, *, B, top_k, n_replace, model_family,
            use_retokenize, token_constraints, tokenizer, rng_seed):
        recorded.append(copy.deepcopy(momentum_grad))
        return list(candidates)

    _fn.recorded = recorded
    return _fn


# step-varying grads so momentum accumulates to DIFFERENT values each step
_F2_GRADS = [
    [[1.0, 0.0, 0.0]],
    [[0.0, 2.0, 0.0]],
    [[0.0, 0.0, 3.0]],
    [[4.0, 0.0, 0.0]],
]


def _run_stepwise(steps, checkpoint_path, start_offset):
    model = MockModel(harmful_trigger="WIN")
    tok = MockTokenizer()
    grad_fn = make_stepwise_grad_fn(_F2_GRADS, start=start_offset)
    sample_fn = make_recording_sample_fn([M.CandidateProposal("WIN", proxy_score=1.0)])
    res = M.reinforce_mac_optimize(
        model, "do the harmful thing", reward_fn_prefers(model.harmful_text),
        initial_trigger="INIT", steps=steps, K=2, B=4, momentum=0.6,
        enable_thinking=True, tokenizer=tok, model_family="qwen3",
        grad_fn=grad_fn, sample_fn=sample_fn, checkpoint_path=checkpoint_path,
    )
    return res, sample_fn


def _flatten(x):
    out = []
    stack = [x]
    while stack:
        y = stack.pop()
        if isinstance(y, (list, tuple)):
            stack.extend(reversed(y))
        else:
            out.append(float(y))
    return out


def test_resume_reproduces_singleshot_momentum_trajectory(tmp_path):
    N = 4
    k = 2  # resume boundary

    # 1. Single-shot: run all N steps at once, record the momentum trajectory.
    single_ckpt = tmp_path / "single.jsonl"
    res_single, sf_single = _run_stepwise(N, single_ckpt, start_offset=0)
    single_norms = [c["momentum_norm"] for c in res_single.checkpoints]
    single_buffers = sf_single.recorded
    assert len(single_norms) == N

    # 2. Resumed: steps 0..k in one call, then k..N with the SAME checkpoint_path.
    resume_ckpt = tmp_path / "resume.jsonl"
    _run_stepwise(k, resume_ckpt, start_offset=0)                 # segment 1: steps 0,1
    res_resumed, sf_resumed = _run_stepwise(N, resume_ckpt, start_offset=k)  # segment 2: steps 2,3

    # Full trajectory reloaded from the JSONL + finished in segment 2.
    resumed_norms = [c["momentum_norm"] for c in res_resumed.checkpoints]
    assert [c["step"] for c in res_resumed.checkpoints] == [0, 1, 2, 3]

    # The momentum accumulates to DISTINCT norms (otherwise the test proves nothing).
    assert single_norms[k] != pytest.approx(single_norms[k - 1])

    # THE FIX: resumed momentum_norm trace matches the single-shot trace EXACTLY,
    # including at the resume boundary (step k) and after.
    for s, r in zip(single_norms, resumed_norms):
        assert r == pytest.approx(s)

    # And the actual momentum BUFFER handed to sample_fn on the first resumed step
    # equals the single-shot buffer at that step (== mu*m + (1-mu)*grad, NOT raw grad).
    # segment 2 recorded steps k..N-1 -> its first entry is the resume-boundary buffer.
    assert _flatten(sf_resumed.recorded[0]) == pytest.approx(_flatten(single_buffers[k]))
    # a raw-grad re-seed (the OLD buggy behavior) would instead equal grads[k]:
    assert _flatten(sf_resumed.recorded[0]) != pytest.approx(_flatten(_F2_GRADS[k]))


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
