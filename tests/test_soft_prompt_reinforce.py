"""
Deterministic CPU unit tests for
scripts/reinforce_objective/soft_prompt_reinforce.py (Sprint Plan §D5 / Gate 3).

PURE-PYTHON / CPU-only: no torch, no GPU model, no downloads. Runs under:
    /usr/bin/python3 -m pytest tests/test_soft_prompt_reinforce.py -v

The soft-prompt runner core is exercised with a MOCK backend that models the
teacher-forced logprob as a LINEAR function of the soft prompt
(logprob_i = dot(soft_prompt, e_i)), so the REINFORCE surrogate has an EXACT
analytic gradient and every claim is checkable deterministically without torch:

  * expected-reward objective moves the soft prompt so the HIGH-reward response's
    logprob INCREASES and the LOW-reward one's DECREASES (correct policy-gradient
    sign / "towards"–"away");
  * the RLOO advantages entering the surrogate are STOP-GRADIENT'd (no grad leak),
    proven with a grad-taint-propagating mock scalar;
  * an Adam/SGD step actually CHANGES the soft prompt;
  * K>=2 is enforced (raises) with the documented K=1 fallback;
  * soft-prompt LENGTHS are honored (init produces L vectors);
  * the prefix_ce comparison arm runs and requires a target_prefix;
  * the Gate-3 decision reads on behavioral ASR (REINFORCE vs Prefix-CE);
  * importing the module pulls in NO torch.
"""

import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT))
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from reinforce_objective import soft_prompt_reinforce as SP  # noqa: E402


# ---------------------------------------------------------------------------
# Torch-free grad-carrying scalar with an EXACT linear gradient wrt the soft prompt
# ---------------------------------------------------------------------------

class LinearGradTensor:
    """A scalar `value` plus its exact gradient `grad` (length-L vector) wrt the
    soft prompt, and a `requires_grad` taint. Supports the arithmetic
    `build_surrogate_loss` performs: `float * (-lp)`, `+`, `/ int`, `.detach()`,
    `.item()`. This is a minimal linear autograd — enough to test sign + detach
    without torch."""

    def __init__(self, value, grad, requires_grad=True):
        self.value = float(value)
        self.grad = list(grad)              # d(value)/d(soft_prompt), length L
        self.requires_grad = bool(requires_grad)

    def detach(self):
        return LinearGradTensor(self.value, [0.0] * len(self.grad), requires_grad=False)

    def item(self):
        return self.value

    def _coerce(self, other):
        if isinstance(other, LinearGradTensor):
            return other
        return LinearGradTensor(float(other), [0.0] * len(self.grad), requires_grad=False)

    def __neg__(self):
        return LinearGradTensor(-self.value, [-g for g in self.grad], self.requires_grad)

    def __mul__(self, other):
        o = self._coerce(other)
        # linear * constant (constant has zero grad in our usage: weight is a float)
        val = self.value * o.value
        grad = [g * o.value for g in self.grad]
        return LinearGradTensor(val, grad, self.requires_grad or o.requires_grad)

    __rmul__ = __mul__

    def __add__(self, other):
        o = self._coerce(other)
        val = self.value + o.value
        grad = [a + b for a, b in zip(self.grad, o.grad)]
        return LinearGradTensor(val, grad, self.requires_grad or o.requires_grad)

    __radd__ = __add__

    def __truediv__(self, other):
        val = self.value / float(other)
        grad = [g / float(other) for g in self.grad]
        return LinearGradTensor(val, grad, self.requires_grad)


class LinearMockBackend:
    """Mock `SoftPromptModel`: logprob_i = dot(soft_prompt, e_i) (standard basis),
    responses fixed, rewards decide the direction. A gradient-DESCENT step on the
    surrogate then provably raises the high-reward logprob."""

    def __init__(self, responses, lr=1.0):
        self.responses = list(responses)
        self.lr = float(lr)
        self.last_grad_norm = 0.0

    def init_soft_prompt(self, L, *, seed, learning_rate):
        # deterministic init; L honored -> length-L zero vector. Store it so tests
        # can read the mutated soft prompt after a run.
        self.L = int(L)
        self.soft = [0.0] * int(L)
        return self.soft, {"lr": learning_rate}     # optimizer is just a config bag

    def generate_one(self, soft_prompt, instruction, *, do_sample, temperature, seed, max_new_tokens):
        # greedy -> responses[0]; sampled -> cycle through the rest
        if not do_sample:
            return self.responses[0]
        idx = 1 + (0 if seed is None else int(seed)) % max(1, len(self.responses) - 1)
        return self.responses[idx % len(self.responses)]

    def _feature(self, response):
        i = self.responses.index(response)
        e = [0.0] * self.L
        e[i % self.L] = 1.0
        return e

    def response_logprob(self, soft_prompt, instruction, response, *, reduction="sum"):
        feat = self._feature(response)
        val = sum(s * f for s, f in zip(soft_prompt, feat))
        return LinearGradTensor(val, feat, requires_grad=True)

    def prefix_ce(self, soft_prompt, instruction, target_prefix, *, reduction="sum"):
        feat = [1.0] * self.L
        val = sum(s * f for s, f in zip(soft_prompt, feat))
        return LinearGradTensor(-val, [-f for f in feat], requires_grad=True)

    def optimizer_step(self, optimizer, soft_prompt, loss):
        # gradient DESCENT on the surrogate: soft_prompt -= lr * dLoss/dsoft_prompt
        grad = loss.grad
        for i in range(len(soft_prompt)):
            soft_prompt[i] -= self.lr * grad[i]
        self.last_grad_norm = sum(g * g for g in grad) ** 0.5
        return self.last_grad_norm

    def soft_prompt_norm(self, soft_prompt):
        return sum(s * s for s in soft_prompt) ** 0.5


# ---------------------------------------------------------------------------
# Import purity
# ---------------------------------------------------------------------------

def _import_pulls_in_torch(*module_names):
    """Import ``module_names`` in a FRESH interpreter; return True iff that
    import pulled ``torch`` into the CHILD's ``sys.modules``.

    This probe must run out-of-process. pytest imports every collected test
    module before running any test, and several sibling test modules import
    torch at module scope, so an in-process ``"torch" in sys.modules`` check
    would assert a property of the SESSION rather than of the module under
    test. The child gets the repo root and ``scripts/`` on PYTHONPATH, exactly
    like the in-process import above. Any child failure that is not the
    torch question itself is raised loudly, so an ImportError can never be
    silently read as "torch-free".
    """
    import os
    import subprocess

    _root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    _child = (
        "import importlib, sys\n"
        "for _name in sys.argv[1:]:\n"
        "    importlib.import_module(_name)\n"
        "print('TORCH' if 'torch' in sys.modules else 'NOTORCH')\n"
    )
    _env = dict(os.environ)
    _pp = [_root, os.path.join(_root, "scripts")]
    if _env.get("PYTHONPATH"):
        _pp.append(_env["PYTHONPATH"])
    _env["PYTHONPATH"] = os.pathsep.join(_pp)
    _proc = subprocess.run(
        [sys.executable, "-c", _child, *module_names],
        capture_output=True,
        text=True,
        env=_env,
    )
    _lines = _proc.stdout.strip().splitlines()
    _verdict = _lines[-1].strip() if _lines else ""
    if _proc.returncode != 0 or _verdict not in ("TORCH", "NOTORCH"):
        raise AssertionError(
            "torch-free probe subprocess failed for {!r} (returncode={})\n"
            "--- child stdout ---\n{}\n--- child stderr ---\n{}".format(
                list(module_names), _proc.returncode, _proc.stdout, _proc.stderr
            )
        )
    return _verdict == "TORCH"


def test_module_imports_without_torch():
    assert not _import_pulls_in_torch(
        "reinforce_objective.soft_prompt_reinforce"
    ), "importing soft_prompt_reinforce must not pull in torch"


# ---------------------------------------------------------------------------
# Sign: expected-reward objective moves toward the high-reward response
# ---------------------------------------------------------------------------

def _run_reinforce_one_step(lr=1.0):
    good, bad = "HARMFUL step 1 step 2", "I cannot help with that."
    backend = LinearMockBackend([good, bad], lr=lr)
    res = SP.soft_prompt_upper_bound(
        backend, "do the harmful thing",
        reward_fn=lambda g, r: 1.0 if r == good else 0.0,
        objective="reinforce", L=2, seed=0, steps=1, K=2,
    )
    return backend, res, good, bad


def test_expected_reward_sign_towards_high_reward():
    backend, res, good, bad = _run_reinforce_one_step()
    step = res.steps[0]
    # RLOO K=2 rewards [1,0] -> advantages [+1,-1]; response 0 (greedy=good) towards.
    assert step.advantages[0] > 0.0 > step.advantages[1]
    assert step.directions[0] == "towards"
    assert step.directions[1] == "away"
    # After the descent step the soft prompt moved so good's logprob went UP (from 0)
    # and bad's went DOWN — that IS gradient ASCENT on the expected reward.
    final_soft = backend.soft                       # mutated in place during the run
    lp_good_after = sum(s * f for s, f in zip(final_soft, backend._feature(good)))
    lp_bad_after = sum(s * f for s, f in zip(final_soft, backend._feature(bad)))
    assert lp_good_after > 0.0      # high-reward logprob increased above the init 0
    assert lp_bad_after < 0.0       # low-reward logprob decreased below the init 0


# ---------------------------------------------------------------------------
# Adam/SGD step changes the soft prompt
# ---------------------------------------------------------------------------

def test_step_changes_soft_prompt():
    good, bad = "good", "bad"
    backend = LinearMockBackend([good, bad], lr=1.0)
    soft, opt = backend.init_soft_prompt(3, seed=0, learning_rate=0.1)
    before = list(soft)
    res = SP.soft_prompt_upper_bound(
        backend, "goal", reward_fn=lambda g, r: 1.0 if r == good else 0.0,
        objective="reinforce", L=3, seed=0, steps=1, K=2,
    )
    # the run created its own soft prompt internally; assert the logged norm > 0
    # (started at 0, so any nonzero norm proves the step moved it).
    assert res.steps[0].soft_prompt_norm > 0.0
    assert res.steps[0].grad_norm > 0.0
    # and directly: a manual step mutates the vector in place.
    loss = SP.build_surrogate_loss(
        [backend.response_logprob(soft, "goal", good),
         backend.response_logprob(soft, "goal", bad)],
        [1.0, -1.0],
    )
    backend.optimizer_step(opt, soft, loss)
    assert soft != before


# ---------------------------------------------------------------------------
# Advantages detached — no grad leak through the reward/advantage
# ---------------------------------------------------------------------------

def test_advantages_detached_no_grad_leak():
    # logprobs carry grad (through the soft prompt); the advantage weights must not.
    lp = [LinearGradTensor(-2.0, [1.0, 0.0]), LinearGradTensor(-6.0, [0.0, 1.0])]
    # ce weights are plain floats out of reinforce_loss (already detached scalars);
    # build_surrogate_loss must still stop-gradient them.
    loss = SP.build_surrogate_loss(lp, [0.5, -0.5])
    assert loss.requires_grad is True                 # grad still flows from logprobs
    # detach the logprobs -> if the weight leaked grad, loss would still require grad
    detached = [x.detach() for x in lp]
    loss2 = SP.build_surrogate_loss(detached, [0.5, -0.5])
    assert loss2.requires_grad is False


def test_step_log_advantages_and_reward_variance():
    good, bad = "good", "bad"
    backend = LinearMockBackend([good, bad], lr=1.0)
    res = SP.soft_prompt_upper_bound(
        backend, "goal", reward_fn=lambda g, r: 1.0 if r == good else 0.0,
        objective="reinforce", L=2, seed=0, steps=1, K=2, asr_threshold=0.5,
    )
    s = res.steps[0]
    assert s.rewards == [1.0, 0.0]
    assert s.expected_reward == pytest.approx(0.5)
    assert s.reward_variance == pytest.approx(0.25)   # pvar([1,0]) = 0.25
    assert s.greedy_asr_proxy == 1.0                  # greedy = good, reward 1 >= 0.5
    assert s.sampled_asr == pytest.approx(0.5)        # 1 of 2 >= 0.5


# ---------------------------------------------------------------------------
# K>=2 enforcement + documented K=1 fallback
# ---------------------------------------------------------------------------

def test_k1_raises_by_default():
    backend = LinearMockBackend(["only"], lr=1.0)
    with pytest.raises(ValueError, match="K>=2"):
        SP.soft_prompt_upper_bound(
            backend, "goal", reward_fn=lambda g, r: 1.0,
            objective="reinforce", L=2, steps=1, K=1,
        )


def test_k1_fallback_when_allowed():
    backend = LinearMockBackend(["only"], lr=1.0)
    res = SP.soft_prompt_upper_bound(
        backend, "goal", reward_fn=lambda g, r: 0.9,
        objective="reinforce", L=2, steps=1, K=1,
        allow_k1_fallback=True, baseline_const=0.5,
    )
    # K=1 fallback advantage A_0 = r_0 - baseline_const = 0.9 - 0.5.
    assert res.steps[0].advantages[0] == pytest.approx(0.4)


# ---------------------------------------------------------------------------
# Lengths honored
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("L", [5, 10, 20, 40])
def test_lengths_honored(L):
    backend = LinearMockBackend(["a", "b"], lr=0.1)
    soft, _ = backend.init_soft_prompt(L, seed=0, learning_rate=0.1)
    assert len(soft) == L
    res = SP.soft_prompt_upper_bound(
        backend, "goal", reward_fn=lambda g, r: 1.0 if r == "a" else 0.0,
        objective="reinforce", L=L, seed=0, steps=1, K=2,
    )
    assert res.length == L


# ---------------------------------------------------------------------------
# prefix_ce comparison arm
# ---------------------------------------------------------------------------

def test_prefix_ce_requires_target_prefix():
    backend = LinearMockBackend(["a", "b"], lr=0.1)
    with pytest.raises(ValueError, match="target_prefix"):
        SP.soft_prompt_upper_bound(
            backend, "goal", reward_fn=lambda g, r: 0.5,
            objective="prefix_ce", L=2, steps=1, K=2,
        )


def test_prefix_ce_arm_runs_and_logs_behavior():
    good, bad = "good", "bad"
    backend = LinearMockBackend([good, bad], lr=0.1)
    res = SP.soft_prompt_upper_bound(
        backend, "goal", reward_fn=lambda g, r: 1.0 if r == good else 0.0,
        objective="prefix_ce", L=2, steps=2, K=2, target_prefix="Sure, here is",
    )
    assert res.objective == "prefix_ce"
    assert len(res.steps) == 2
    # prefix_ce arm has no advantages/directions but still logs behavioral ASR.
    assert res.steps[0].advantages == []
    assert res.steps[0].directions == []
    assert res.steps[0].sampled_asr == pytest.approx(0.5)


# ---------------------------------------------------------------------------
# Gate-3 decision reads on behavioral ASR (REINFORCE vs Prefix-CE)
# ---------------------------------------------------------------------------

def test_gate3_decision_asr_improves():
    r_rein = SP.SoftPromptRunResult(objective="reinforce", length=5, seed=0,
                                    instruction="g", best_sampled_asr=0.6, best_greedy_asr=1.0)
    r_pref = SP.SoftPromptRunResult(objective="prefix_ce", length=5, seed=0,
                                    instruction="g", best_sampled_asr=0.2, best_greedy_asr=0.0)
    d = SP.gate3_decision([r_rein, r_pref])
    assert d.asr_improves is True
    assert d.reinforce_best_sampled_asr == pytest.approx(0.6)
    assert d.prefix_ce_best_sampled_asr == pytest.approx(0.2)


def test_gate3_decision_asr_does_not_improve():
    r_rein = SP.SoftPromptRunResult(objective="reinforce", length=5, seed=0,
                                    instruction="g", best_sampled_asr=0.0, best_greedy_asr=0.0)
    r_pref = SP.SoftPromptRunResult(objective="prefix_ce", length=5, seed=0,
                                    instruction="g", best_sampled_asr=0.0, best_greedy_asr=0.0)
    d = SP.gate3_decision([r_rein, r_pref])
    assert d.asr_improves is False


# ---------------------------------------------------------------------------
# score-goal requirement is honored (delegates to gpu_runner.score_responses)
# ---------------------------------------------------------------------------

def test_empty_goal_rejected():
    backend = LinearMockBackend(["a", "b"], lr=0.1)
    with pytest.raises(ValueError):
        SP.soft_prompt_upper_bound(
            backend, "   ", reward_fn=lambda g, r: 0.5,
            objective="reinforce", L=2, steps=1, K=2,
        )


# ---------------------------------------------------------------------------
# Verifiability logging: the EXACT generation text is stored per step (§D3/§D7)
# ---------------------------------------------------------------------------

def test_generation_text_logged_per_step():
    good, bad = "HARMFUL step-by-step content", "I cannot help with that."
    backend = LinearMockBackend([good, bad], lr=1.0)
    res = SP.soft_prompt_upper_bound(
        backend, "goal", reward_fn=lambda g, r: 1.0 if r == good else 0.0,
        objective="reinforce", L=2, seed=0, steps=2, K=2,
    )
    for s in res.steps:
        # greedy text == responses[0]; both greedy + best-response text are recorded.
        assert s.greedy_text == good
        assert s.best_response_text == good          # good has the max reward
        assert s.response_texts == [good, bad]       # aligned with s.rewards == [1,0]
        assert len(s.response_texts) == len(s.rewards)
    # as_dict (the JSONL record) carries the text fields for a human to read.
    d = res.steps[0].as_dict()
    assert d["greedy_text"] == good
    assert d["best_response_text"] == good
    assert d["response_texts"] == [good, bad]


def test_generation_text_truncated_to_max_chars():
    long_good = "H" * 5000
    backend = LinearMockBackend([long_good, "no"], lr=1.0)
    res = SP.soft_prompt_upper_bound(
        backend, "goal", reward_fn=lambda g, r: 1.0 if r == long_good else 0.0,
        objective="reinforce", L=2, seed=0, steps=1, K=2, log_text_max_chars=100,
    )
    txt = res.steps[0].greedy_text
    assert len(txt) < 5000 and txt.startswith("H" * 100) and "chars]" in txt


# ---------------------------------------------------------------------------
# Best soft prompt is saved (torch save mocked) on a NEW running-best only
# ---------------------------------------------------------------------------

def test_best_softprompt_saved_on_new_best(monkeypatch):
    saves = []
    monkeypatch.setattr(SP, "_save_soft_prompt", lambda sp, path: saves.append((list(sp), path)))
    good, bad = "good", "bad"
    # reward improves over steps: step0 expected 0.5, so best set at step0 only here
    backend = LinearMockBackend([good, bad], lr=1.0)
    res = SP.soft_prompt_upper_bound(
        backend, "goal", reward_fn=lambda g, r: 1.0 if r == good else 0.0,
        objective="reinforce", L=2, seed=0, steps=3, K=2,
        best_softprompt_path="/tmp/does-not-matter/best.pt",
    )
    # At least one save happened (the first step is always a new best from -inf).
    assert len(saves) >= 1
    assert saves[0][1] == "/tmp/does-not-matter/best.pt"
    assert res.best_softprompt_path == "/tmp/does-not-matter/best.pt"
    assert res.best_step >= 0


def test_no_softprompt_save_without_path(monkeypatch):
    saves = []
    monkeypatch.setattr(SP, "_save_soft_prompt", lambda sp, path: saves.append(path))
    backend = LinearMockBackend(["good", "bad"], lr=1.0)
    SP.soft_prompt_upper_bound(
        backend, "goal", reward_fn=lambda g, r: 1.0 if r == "good" else 0.0,
        objective="reinforce", L=2, seed=0, steps=2, K=2,   # no best_softprompt_path
    )
    assert saves == []       # guarded: no path -> no save invoked


# ---------------------------------------------------------------------------
# FINAL-step ASR reported alongside BEST-over-steps ASR (honest vs optimistic)
# ---------------------------------------------------------------------------

def test_run_reports_final_and_best_asr():
    good, bad = "good", "bad"
    backend = LinearMockBackend([good, bad], lr=1.0)
    res = SP.soft_prompt_upper_bound(
        backend, "goal", reward_fn=lambda g, r: 1.0 if r == good else 0.0,
        objective="reinforce", L=2, seed=0, steps=2, K=2,
    )
    # both reads present on the run + in as_dict + in the asr_summary helper.
    assert res.final_sampled_asr == pytest.approx(0.5)
    assert res.final_greedy_asr == 1.0
    d = res.as_dict()
    for k in ("final_sampled_asr", "final_greedy_asr", "best_sampled_asr", "best_greedy_asr"):
        assert k in d
    summ = SP.asr_summary(res)
    assert summ["final_sampled_asr"] == pytest.approx(0.5)
    assert summ["best_sampled_asr"] == pytest.approx(0.5)


def test_gate3_decision_exposes_final_and_best():
    # BEST improves (reinforce best_sampled 0.6 > 0.2) but FINAL does NOT (both 0.0).
    r_rein = SP.SoftPromptRunResult(
        objective="reinforce", length=5, seed=0, instruction="g",
        best_sampled_asr=0.6, best_greedy_asr=1.0,
        final_sampled_asr=0.0, final_greedy_asr=0.0,
    )
    r_pref = SP.SoftPromptRunResult(
        objective="prefix_ce", length=5, seed=0, instruction="g",
        best_sampled_asr=0.2, best_greedy_asr=0.0,
        final_sampled_asr=0.0, final_greedy_asr=0.0,
    )
    d = SP.gate3_decision([r_rein, r_pref])
    assert d.asr_improves is True                 # optimistic best-over-steps
    assert d.asr_improves_final is False          # honest final-step (primary)
    dd = d.as_dict()
    assert dd["gate3_asr_improves_over_prefix_ce__FINAL_primary"] is False
    assert dd["gate3_asr_improves_over_prefix_ce__BEST_optimistic"] is True


# ---------------------------------------------------------------------------
# extract_high_reward_examples returns top-N rows sorted by reward (review artifact)
# ---------------------------------------------------------------------------

def test_extract_high_reward_examples_sorted(tmp_path):
    import json

    runs = [
        SP.SoftPromptRunResult(objective="reinforce", length=5, seed=0, instruction="inst-A"),
        SP.SoftPromptRunResult(objective="prefix_ce", length=5, seed=0, instruction="inst-B"),
    ]
    runs[0].steps.append(SP.SoftPromptStepLog(
        step=0, objective="reinforce", expected_reward=0.3, greedy_asr_proxy=0.0,
        sampled_asr=0.0, reward_variance=0.0, soft_prompt_norm=0.0,
        empty_degenerate_rate=0.0, grad_norm=0.0, surrogate_loss=0.0,
        best_reward=0.3, rewards=[0.3, 0.1], advantages=[], directions=[], provenance=[],
        greedy_text="low-A", best_response_text="low-A-best", response_texts=["low-A", "x"],
    ))
    runs[0].steps.append(SP.SoftPromptStepLog(
        step=1, objective="reinforce", expected_reward=0.9, greedy_asr_proxy=1.0,
        sampled_asr=1.0, reward_variance=0.0, soft_prompt_norm=0.0,
        empty_degenerate_rate=0.0, grad_norm=0.0, surrogate_loss=0.0,
        best_reward=0.95, rewards=[0.95, 0.85], advantages=[], directions=[], provenance=[],
        greedy_text="HIGH-greedy", best_response_text="HIGH-best", response_texts=["HIGH-greedy", "y"],
    ))
    runs[1].steps.append(SP.SoftPromptStepLog(
        step=0, objective="prefix_ce", expected_reward=0.6, greedy_asr_proxy=1.0,
        sampled_asr=1.0, reward_variance=0.0, soft_prompt_norm=0.0,
        empty_degenerate_rate=0.0, grad_norm=0.0, surrogate_loss=0.0,
        best_reward=0.6, rewards=[0.6], advantages=[], directions=[], provenance=[],
        greedy_text="mid-B", best_response_text="mid-B-best", response_texts=["mid-B"],
    ))

    p = tmp_path / "runs.jsonl"
    with open(p, "w", encoding="utf-8") as fh:
        for r in runs:
            fh.write(json.dumps(r.as_dict(), ensure_ascii=False) + "\n")

    top = SP.extract_high_reward_examples(str(p), top_n=2)
    assert len(top) == 2
    # sorted by reward DESC: 0.95 (step1, inst-A) then 0.6 (inst-B).
    assert top[0]["reward"] == pytest.approx(0.95)
    assert top[0]["instruction"] == "inst-A"
    assert top[0]["step"] == 1
    assert top[0]["greedy_text"] == "HIGH-greedy"
    assert top[0]["best_sampled_text"] == "HIGH-best"
    assert top[1]["reward"] == pytest.approx(0.6)
    assert top[1]["instruction"] == "inst-B"
