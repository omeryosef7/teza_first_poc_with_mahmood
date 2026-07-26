"""
Deterministic unit tests for scripts/reinforce_objective/ (Sprint Plan §D3 + §D4).

PURE-PYTHON / CPU-only: no torch, no numpy, no GPU models. Runs under:
    /usr/bin/python3 -m pytest tests/test_reinforce_objective.py -v

Proves on toy numbers (per the §D4 task spec):
  - RLOO advantages sum ~= 0 (K>1);
  - correct signs: higher reward -> 'towards' (positive CE weight);
  - finite gradients;
  - monotonic weighting (advantage -> weight);
  - K=1 fallback documented + non-crashing.
Plus D3: the reward->selection-loss transform is strictly decreasing, config is
clean, and the module imports without torch.
"""

import math
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT))
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from reinforce_objective import reinforce as R  # noqa: E402
from reinforce_objective import proxy_ce_rerank as P  # noqa: E402


# ---------------------------------------------------------------------------
# D4 — RLOO advantages: zero-sum
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "rewards",
    [
        [0.0, 1.0],
        [0.1, 0.9, 0.5],
        [0.2, 0.2, 0.8, 0.4, 0.6],
        [1.0, 1.0, 1.0, 1.0],          # all equal -> all advantages 0
        [0.3, 0.7, 0.7, 0.1, 0.9, 0.5],
    ],
)
def test_rloo_advantages_zero_sum(rewards):
    adv = R.reinforce_advantages(rewards, baseline="rloo")
    assert len(adv) == len(rewards)
    assert abs(math.fsum(adv)) < 1e-9
    R.assert_zero_sum(adv)  # must not raise


@pytest.mark.parametrize(
    "rewards",
    [[0.0, 1.0], [0.1, 0.9, 0.5], [0.2, 0.2, 0.8, 0.4, 0.6]],
)
def test_mean_baseline_zero_sum(rewards):
    adv = R.reinforce_advantages(rewards, baseline="mean")
    assert abs(math.fsum(adv)) < 1e-9


def test_rloo_formula_matches_leave_one_out():
    rewards = [0.2, 0.8, 0.5, 0.1]
    adv = R.reinforce_advantages(rewards, baseline="rloo")
    k = len(rewards)
    s = sum(rewards)
    expected = [(r - (s - r) / (k - 1)) for r in rewards]
    for a, e in zip(adv, expected):
        assert a == pytest.approx(e)


# ---------------------------------------------------------------------------
# D4 — correct signs: higher reward -> 'towards' (positive CE weight)
# ---------------------------------------------------------------------------

def test_signs_towards_and_away():
    rewards = [0.1, 0.9]  # response 1 below-baseline, response 2 above-baseline
    adv = R.reinforce_advantages(rewards, baseline="rloo")
    assert adv[0] < 0.0  # below baseline -> away
    assert adv[1] > 0.0  # above baseline -> towards

    w = [R.signed_teacher_forced_ce_grad_weight(a) for a in adv]
    assert w[0] < 0.0  # away: minimizing loss RAISES this CE
    assert w[1] > 0.0  # towards: minimizing loss LOWERS this CE
    # weight equals the advantage (documented identity)
    assert w == pytest.approx(adv)


def test_highest_reward_gets_largest_towards_weight():
    rewards = [0.0, 0.25, 0.5, 1.0]
    adv = R.reinforce_advantages(rewards, baseline="rloo")
    weights = [R.signed_teacher_forced_ce_grad_weight(a) for a in adv]
    # argmax reward must have argmax (most positive) weight
    assert weights.index(max(weights)) == rewards.index(max(rewards))
    assert weights.index(min(weights)) == rewards.index(min(rewards))


# ---------------------------------------------------------------------------
# D4 — monotonic weighting
# ---------------------------------------------------------------------------

def test_weight_is_monotonic_in_advantage():
    advs = [-2.0, -0.5, 0.0, 0.3, 1.7, 5.0]
    weights = [R.signed_teacher_forced_ce_grad_weight(a) for a in advs]
    for i in range(len(weights) - 1):
        assert weights[i] < weights[i + 1]  # strictly increasing


def test_advantages_monotone_in_rewards():
    # With a shared baseline, advantage is strictly increasing in the reward.
    rewards = [0.1, 0.2, 0.5, 0.9]
    adv = R.reinforce_advantages(rewards, baseline="rloo")
    for i in range(len(adv) - 1):
        assert adv[i] < adv[i + 1]


# ---------------------------------------------------------------------------
# D4 — reinforce_loss: finite gradients + correct gradient direction
# ---------------------------------------------------------------------------

def test_reinforce_loss_finite_and_grad_signs():
    logprobs = [-3.0, -1.0, -2.5, -0.7]   # teacher-forced log pi(y_i)
    rewards = [0.1, 0.9, 0.3, 0.8]
    res = R.reinforce_loss(logprobs, rewards, baseline="rloo")

    assert math.isfinite(res.loss)
    assert all(math.isfinite(g) for g in res.grad_wrt_logprob)
    assert all(math.isfinite(g) for g in res.grad_wrt_ce)
    assert all(math.isfinite(a) for a in res.advantages)

    # CE_i == -logprob_i
    assert res.per_response_ce == pytest.approx([-lp for lp in logprobs])
    # dL/dlogp_i == -A_i / K  ; dL/dCE_i == A_i / K
    k = len(rewards)
    assert res.grad_wrt_logprob == pytest.approx([-a / k for a in res.advantages])
    assert res.grad_wrt_ce == pytest.approx([a / k for a in res.advantages])
    # above-baseline response => negative grad wrt CE-lowering? check identity:
    # towards (adv>0) => grad_wrt_ce>0 => increasing CE increases loss => min lowers CE
    for a, g in zip(res.advantages, res.grad_wrt_ce):
        assert (a > 0) == (g > 0)


def test_reinforce_loss_zero_when_rewards_equal():
    # All-equal rewards -> zero advantages -> zero loss and zero grads.
    res = R.reinforce_loss([-1.0, -2.0, -3.0], [0.5, 0.5, 0.5], baseline="rloo")
    assert res.loss == pytest.approx(0.0)
    assert all(g == pytest.approx(0.0) for g in res.grad_wrt_logprob)


def test_reinforce_loss_matches_manual_formula():
    logprobs = [-2.0, -0.5]
    rewards = [0.2, 0.8]
    res = R.reinforce_loss(logprobs, rewards, baseline="rloo")
    adv = R.reinforce_advantages(rewards, baseline="rloo")
    ce = [2.0, 0.5]
    manual = (adv[0] * ce[0] + adv[1] * ce[1]) / 2
    assert res.loss == pytest.approx(manual)


def test_length_mismatch_raises():
    with pytest.raises(ValueError):
        R.reinforce_loss([-1.0, -2.0], [0.5], baseline="rloo")


# ---------------------------------------------------------------------------
# D4 — K=1 fallback (documented; zero-sum NOT asserted)
# ---------------------------------------------------------------------------

def test_k1_fallback():
    adv = R.reinforce_advantages([0.7], baseline="rloo")
    assert adv == [0.7]  # r - baseline_const(0.0)
    adv2 = R.reinforce_advantages([0.7], baseline="rloo", baseline_const=0.5)
    assert adv2 == pytest.approx([0.2])
    # zero-sum does NOT hold for K=1 -> assert_zero_sum should reject nonzero adv
    with pytest.raises(AssertionError):
        R.assert_zero_sum(adv)


def test_k1_reinforce_loss_runs():
    res = R.reinforce_loss([-1.5], [0.9], baseline="rloo")
    assert math.isfinite(res.loss)
    assert res.log["K"] == 1


def test_empty_inputs():
    assert R.reinforce_advantages([]) == []
    res = R.reinforce_loss([], [])
    assert res.loss == 0.0


# ---------------------------------------------------------------------------
# D4 — stabilization knobs are applied + logged
# ---------------------------------------------------------------------------

def test_reward_clipping_logged():
    res = R.reinforce_loss(
        [-1.0, -1.0], [5.0, -3.0], baseline="rloo", clip_reward=(0.0, 1.0)
    )
    assert res.log["clip_reward"] == (0.0, 1.0)
    # clipped rewards are [1.0, 0.0]; RLOO K=2: adv_i = r_i - (S-r_i)/(K-1) = [1.0, -1.0]
    assert res.advantages == pytest.approx([1.0, -1.0])


def test_zscore_normalization_logged_and_guarded():
    res = R.reinforce_loss([-1.0, -1.0, -1.0], [0.5, 0.5, 0.5],
                           baseline="mean", normalize="zscore")
    assert res.log["normalize"] == "zscore"
    assert res.log["zscore_std_guarded"] is True   # zero-variance guard fired
    assert all(math.isfinite(a) for a in res.advantages)


def test_unknown_baseline_and_normalize_raise():
    with pytest.raises(ValueError):
        R.reinforce_advantages([0.1, 0.2], baseline="bogus")
    with pytest.raises(ValueError):
        R.reinforce_loss([-1.0, -1.0], [0.1, 0.2], normalize="bogus")


# ---------------------------------------------------------------------------
# D4 — adapter interface (no model; call-sites must raise)
# ---------------------------------------------------------------------------

def test_adapter_estimate_pure_python():
    ad = R.ReinforceGCGAdapter(K=3, baseline="rloo")
    res = ad.estimate([-1.0, -2.0, -0.5], [0.2, 0.4, 0.9])
    assert math.isfinite(res.loss)
    assert abs(math.fsum(res.advantages)) < 1e-9


def test_adapter_gpu_callsites_raise():
    ad = R.ReinforceGCGAdapter()
    with pytest.raises(NotImplementedError):
        ad.sample_responses()
    with pytest.raises(NotImplementedError):
        ad.teacher_forced_logprobs()


# ---------------------------------------------------------------------------
# D3 — proxy-CE behavioral reranking (NOT REINFORCE): pure pieces
# ---------------------------------------------------------------------------

def test_reward_to_selection_loss_strictly_decreasing():
    rewards = [0.0, 0.25, 0.5, 0.75, 1.0]
    losses = [P.behavioral_reward_to_selection_loss(r) for r in rewards]
    for i in range(len(losses) - 1):
        assert losses[i] > losses[i + 1]  # higher reward -> lower (better) loss
    # best reward -> min loss (TROPT picks argmin)
    assert losses.index(min(losses)) == rewards.index(max(rewards))


def test_d3_config_defaults_and_flag():
    cfg = P.ProxyCEBehavioralRerankConfig()
    d = cfg.as_dict()
    assert d["is_reinforce"] is False        # explicit: D3 is NOT REINFORCE
    assert d["objective"] == "proxy_ce_behavioral_rerank"
    assert d["momentum"] == 0.0
    mac = P.ProxyCEBehavioralRerankConfig(momentum=0.6)
    assert mac.as_dict()["momentum"] == 0.6  # MAC-momentum proposal variant


def test_d3_module_imports_without_torch():
    # torch must not be pulled in merely by importing the D3 module.
    # F1 fix: assert D3 import does NOT pull in torch, in a FRESH interpreter so the
    # check is real (the old `or True` was a tautology). torch is imported lazily
    # inside proxy_ce_rerank's assembly functions, never at module import.
    import subprocess
    code = (
        "import sys; sys.path.insert(0, 'scripts'); "
        "import reinforce_objective.proxy_ce_rerank as m; "
        "assert 'torch' not in sys.modules, 'torch imported at module load'; "
        "print('ok')"
    )
    r = subprocess.run(
        [sys.executable, "-c", code], cwd=str(_REPO_ROOT),
        capture_output=True, text=True,
    )
    assert r.returncode == 0 and "ok" in r.stdout, f"D3 import pulled in torch: {r.stderr}"
    # The lazy factories exist but are not called (would need torch/model).
    assert callable(P.assemble_proxy_ce_behavioral_rerank)
    assert callable(P.make_behavioral_selection_loss)
