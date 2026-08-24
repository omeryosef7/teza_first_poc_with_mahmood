"""
Deterministic CPU unit tests for scripts/reinforce_objective/gpu_runner.py
(Sprint Completion Plan §D4.5 / §5 Package 2).

PURE-PYTHON / CPU-only: no torch, no GPU model, no downloads. Runs under:
    /usr/bin/python3 -m pytest tests/test_gpu_runner.py -v

The runner core is exercised with a MOCK model (deterministic canned responses +
deterministic teacher-forced log-probs). We assert exactly the §D4.5 review
findings:
  * a synthetic HIGH-reward response gets a 'towards' (CE-lowering, advantage>0)
    update and a LOW-reward one gets 'away' (advantage<0);
  * the advantages / CE weights consumed by the surrogate are STOP-GRADIENT'd
    (no grad leak) — proven with a fake grad-tracking tensor;
  * K>=2 is enforced (raises) with a documented K=1 fallback;
  * enable_thinking is recorded on the built prompt / step log;
  * importing the module pulls in NO torch.
"""

import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT))
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from reinforce_objective import gpu_runner as G  # noqa: E402


# ---------------------------------------------------------------------------
# Mocks (no torch; deterministic)
# ---------------------------------------------------------------------------

class MockModel:
    """Deterministic `TargetModel` stub: canned responses + fixed log-probs.

    `responses` is the ordered list of texts `generate_one` hands out (greedy
    first, then sampled). `logprob_by_text` maps a response string to its
    teacher-forced total log-prob (a plain float — no torch).
    """

    def __init__(self, responses, logprob_by_text, default_logprob=-5.0):
        self._responses = list(responses)
        self._logprob_by_text = dict(logprob_by_text)
        self._default = default_logprob
        self._i = 0

    def generate_one(self, prompt, *, do_sample, temperature, seed, max_new_tokens):
        text = self._responses[self._i % len(self._responses)]
        self._i += 1
        return text

    def teacher_forced_logprob(self, prompt, response, *, reduction="sum"):
        return self._logprob_by_text.get(response, self._default)


class MockTokenizer:
    """Minimal tokenizer exposing apply_chat_template (mirrors Qwen3 markers)."""

    def __init__(self, supports_enable_thinking=True):
        self.supports_enable_thinking = supports_enable_thinking

    def apply_chat_template(self, messages, tokenize=False, add_generation_prompt=True,
                            enable_thinking=None):
        if enable_thinking is not None and not self.supports_enable_thinking:
            raise TypeError("enable_thinking not supported")
        content = messages[0]["content"]
        think = "" if (enable_thinking is None or enable_thinking) else "<think>\n\n</think>\n\n"
        return f"<|im_start|>user\n{content}<|im_end|>\n<|im_start|>assistant\n{think}"


class FakeGradTensor:
    """A tiny stand-in for a torch scalar that PROPAGATES a `requires_grad` taint.

    Multiplying two FakeGradTensors OR a FakeGradTensor by anything grad-tainted
    yields a grad-tainted result; `.detach()` clears the taint (like torch). Used
    to prove the advantage is detached before it multiplies the CE term.
    """

    def __init__(self, value, requires_grad=False):
        self.value = float(value)
        self.requires_grad = bool(requires_grad)

    def detach(self):
        return FakeGradTensor(self.value, requires_grad=False)

    def _taint(self, other):
        other_grad = getattr(other, "requires_grad", False)
        return self.requires_grad or other_grad

    def __mul__(self, other):
        ov = other.value if isinstance(other, FakeGradTensor) else float(other)
        return FakeGradTensor(self.value * ov, requires_grad=self._taint(other))

    __rmul__ = __mul__

    def __neg__(self):
        return FakeGradTensor(-self.value, requires_grad=self.requires_grad)

    def __add__(self, other):
        ov = other.value if isinstance(other, FakeGradTensor) else float(other)
        return FakeGradTensor(self.value + ov, requires_grad=self._taint(other))

    def __truediv__(self, other):
        ov = other.value if isinstance(other, FakeGradTensor) else float(other)
        return FakeGradTensor(self.value / ov, requires_grad=self.requires_grad)

    def item(self):
        return self.value


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
        "reinforce_objective.gpu_runner"
    ), "importing gpu_runner must not pull in torch"


# ---------------------------------------------------------------------------
# Gradient SIGN: high reward -> 'towards', low reward -> 'away'
# ---------------------------------------------------------------------------

def test_high_reward_towards_low_reward_away():
    # Two responses: greedy = HIGH reward, sampled = LOW reward.
    good, bad = "HARMFUL step 1 ... step 2 ...", "I cannot help with that."
    model = MockModel(
        responses=[good, bad],
        logprob_by_text={good: -3.0, bad: -8.0},
    )

    def reward_fn(goal, response):
        return 1.0 if response == good else 0.0

    res = G.reinforce_step(
        model, prompt="<prompt>", goal="do the harmful thing", reward_fn=reward_fn,
        K=2, baseline="rloo",
    )

    # Response 0 (high reward) is ABOVE baseline -> advantage>0 -> 'towards'.
    # Response 1 (low reward) is BELOW baseline -> advantage<0 -> 'away'.
    hi = res.responses.index(good)
    lo = res.responses.index(bad)
    assert res.estimate.advantages[hi] > 0.0
    assert res.estimate.advantages[lo] < 0.0
    assert res.directions[hi] == "towards"
    assert res.directions[lo] == "away"
    # CE weight == advantage (towards => positive weight => minimizing L lowers CE).
    assert res.ce_weights_detached[hi] > 0.0
    assert res.ce_weights_detached[lo] < 0.0
    # RLOO with K=2 => advantages are equal-and-opposite (sum ~0).
    assert res.estimate.advantages[hi] == pytest.approx(-res.estimate.advantages[lo])
    # Behavioral SELECTION picks the high-reward response.
    assert res.selection_response == good
    assert res.selection_reward == pytest.approx(1.0)


def test_surrogate_gradient_matches_reinforce_gradient_sign():
    # dL/d(logprob_i) = -A_i / K : towards => negative (raising logprob lowers L).
    good, bad = "good", "bad"
    model = MockModel([good, bad], {good: -2.0, bad: -6.0})
    res = G.reinforce_step(
        model, "<p>", "goal", lambda g, r: 1.0 if r == good else 0.0, K=2,
    )
    hi = res.responses.index(good)
    lo = res.responses.index(bad)
    assert res.estimate.grad_wrt_logprob[hi] < 0.0   # push logprob UP (towards)
    assert res.estimate.grad_wrt_logprob[lo] > 0.0   # push logprob DOWN (away)
    assert all(abs(g) < float("inf") for g in res.estimate.grad_wrt_logprob)


# ---------------------------------------------------------------------------
# Stop-gradient / detach: no grad leak through the advantage
# ---------------------------------------------------------------------------

def test_stop_gradient_detaches_tensor_like():
    tainted = FakeGradTensor(0.7, requires_grad=True)
    out = G.stop_gradient(tainted)
    assert out.requires_grad is False
    # plain floats pass straight through
    assert G.stop_gradient(0.5) == pytest.approx(0.5)


def test_surrogate_has_no_grad_leak_through_advantage():
    # logprobs carry grad (through the trigger tokens); advantages must NOT.
    logprobs = [FakeGradTensor(-2.0, requires_grad=True),
                FakeGradTensor(-6.0, requires_grad=True)]
    # Advantages arrive as grad-TAINTED tensors; build_surrogate must detach them.
    tainted_weights = [FakeGradTensor(0.5, requires_grad=True),
                       FakeGradTensor(-0.5, requires_grad=True)]
    loss = G.build_surrogate_loss(logprobs, tainted_weights)
    # The loss still carries grad (from the logprobs / model forward) ...
    assert loss.requires_grad is True
    # ... but proof the ADVANTAGE was detached: multiply a *detached* logprob by
    # the same weights via the surrogate -> no taint from the weight side.
    detached_logprobs = [lp.detach() for lp in logprobs]
    loss_no_model_grad = G.build_surrogate_loss(detached_logprobs, tainted_weights)
    assert loss_no_model_grad.requires_grad is False, (
        "advantage/CE-weight leaked gradient into the surrogate (missing stop-gradient)"
    )


def test_ce_weights_returned_are_plain_floats():
    model = MockModel(["a", "b"], {"a": -1.0, "b": -4.0})
    res = G.reinforce_step(model, "<p>", "goal",
                           lambda g, r: 1.0 if r == "a" else 0.0, K=2)
    assert all(isinstance(w, float) for w in res.ce_weights_detached)


# ---------------------------------------------------------------------------
# K>=2 enforcement + documented K=1 fallback
# ---------------------------------------------------------------------------

def test_k1_raises_by_default():
    model = MockModel(["only"], {"only": -3.0})
    with pytest.raises(ValueError, match="K>=2"):
        G.reinforce_step(model, "<p>", "goal", lambda g, r: 1.0, K=1)


def test_k1_fallback_when_allowed():
    model = MockModel(["only"], {"only": -3.0})
    res = G.reinforce_step(
        model, "<p>", "goal", lambda g, r: 0.9, K=1,
        allow_k1_fallback=True, baseline_const=0.5,
    )
    assert res.log["k1_fallback"] is True
    assert len(res.responses) == 1
    # Documented K=1 fallback: A_0 = r_0 - baseline_const = 0.9 - 0.5.
    assert res.estimate.advantages[0] == pytest.approx(0.4)


# ---------------------------------------------------------------------------
# enable_thinking recorded
# ---------------------------------------------------------------------------

def test_build_prompt_records_enable_thinking_and_user_turn_placement():
    tok = MockTokenizer(supports_enable_thinking=True)
    built = G.build_prompt(tok, "Write a tutorial", "TRIGGERXYZ",
                           enable_thinking=True, model_family="qwen3")
    assert built.enable_thinking is True
    # trigger sits in the USER turn, at the end of user content
    assert built.user_content == "Write a tutorial TRIGGERXYZ"
    assert "TRIGGERXYZ<|im_end|>" in built.text
    assert "<|im_start|>user" in built.text


def test_build_prompt_enable_thinking_false_differs():
    tok = MockTokenizer(supports_enable_thinking=True)
    t = G.build_prompt(tok, "g", "TRIG", enable_thinking=True).text
    f = G.build_prompt(tok, "g", "TRIG", enable_thinking=False).text
    assert t != f  # False injects the empty <think> block (byte-verify divergence)
    assert "<think>" in f and "<think>" not in t


def test_build_prompt_tokenizer_without_thinking_kwarg():
    tok = MockTokenizer(supports_enable_thinking=False)  # Gemma4-style
    built = G.build_prompt(tok, "g", "TRIG", enable_thinking=True, model_family="gemma4")
    assert "TRIG<|im_end|>" in built.text  # TypeError fallback still templates


def test_step_log_records_enable_thinking():
    model = MockModel(["a", "b"], {"a": -1.0, "b": -4.0})
    res = G.reinforce_step(model, "<p>", "goal",
                           lambda g, r: 1.0 if r == "a" else 0.0, K=2,
                           enable_thinking=True)
    assert res.log["enable_thinking"] is True
    assert res.log["reinforce_mac"] is True
    assert res.log["K_effective"] == 2


# ---------------------------------------------------------------------------
# sample_responses composition (§D4.1) + score_responses goal requirement
# ---------------------------------------------------------------------------

def test_sample_responses_composition_greedy_plus_sampled():
    model = MockModel(["GREEDY", "S1", "S2", "S3"], {})
    out = G.sample_responses(model, "<p>", K=4, seeds=[11, 22, 33])
    assert len(out) == 4
    assert out.provenance[0] == "greedy"
    assert out.responses[0] == "GREEDY"
    assert out.provenance[1].startswith("sampled(seed=11")


def test_sample_responses_seed_and_historical_included():
    model = MockModel(["GREEDY", "S1"], {})
    out = G.sample_responses(model, "<p>", K=4, seeds=[7],
                             seed_response="SEEDRESP", best_historical="BEST")
    assert out.responses[0] == "GREEDY"
    assert "SEEDRESP" in out.responses
    assert "BEST" in out.responses
    assert len(out) == 4


def test_sample_responses_k2_smoke_is_greedy_plus_one_sampled():
    model = MockModel(["GREEDY", "SAMP"], {})
    out = G.sample_responses(model, "<p>", K=2, seeds=[42])
    assert out.provenance == ["greedy", "sampled(seed=42)"]


def test_score_responses_requires_goal():
    with pytest.raises(ValueError, match="goal"):
        G.score_responses("", ["resp"], lambda g, r: 0.5)


def test_score_responses_passes_goal_through():
    seen = []

    def reward_fn(goal, response):
        seen.append(goal)
        return 0.3

    G.score_responses("MY-GOAL", ["a", "b"], reward_fn)
    assert seen == ["MY-GOAL", "MY-GOAL"]  # original goal passed to every call


def test_precomputed_responses_bypass_generation():
    # Package-2 condition 0: caller supplies responses, synthetic rewards.
    model = MockModel(["UNUSED"], {"good": -2.0, "bad": -7.0})
    res = G.reinforce_step(
        model, "<p>", "goal", lambda g, r: 1.0 if r == "good" else 0.0, K=2,
        precomputed_responses=["good", "bad"],
        precomputed_provenance=["greedy", "sampled"],
    )
    assert res.responses == ["good", "bad"]
    assert res.directions[0] == "towards" and res.directions[1] == "away"
