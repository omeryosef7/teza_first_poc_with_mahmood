"""
D3 — proxy-CE behavioral reranking assembly  (**NOT REINFORCE**).

Sprint Completion Plan §D3 / original plan §15.4 ("Efficient proxy strategy")
and §15.6 ("Hybrid method": differentiable proxy proposal + generation-reward
selection).

============================================================================
THIS IS **NOT** REINFORCE.  It is the §15.4 hybrid: a differentiable Prefix-CE
(optionally MAC-momentum) PROPOSAL loss proposes candidate token flips, and a
behavioral reward over ACTUAL FREE GENERATIONS SELECTS among them. There is no
policy gradient, no sampled-response log-prob term, no advantage. The true
REINFORCE estimator is the separate D4 module (`reinforce.py`).
============================================================================

HOW IT MAPS ONTO TROPT `GCGPlusOptimizer` (two-stage design)
------------------------------------------------------------
See TROPT/tropt/optimizer/gcgplus_optimizer.py. GCGPlus already separates:
  * Stage 1 — candidate PROPOSAL: `proxy_loss` (must be differentiable when
    candidate_selection='gradient'); gradient-ranked top-k token flips.
  * Stage 2 — candidate SELECTION: the main `loss`, evaluated on the target
    model to rank the proposed candidates (may be non-differentiable).

So D3 is a pure *wiring*, no new optimizer:
  * proxy_loss = PrefillCELoss()            # differentiable proposal (§15.6)
  * momentum   = 0.6 (optional, MAC)        # MAC__wang2024 proposal momentum
  * loss       = BehavioralRewardSelectionLoss(...)   # §15.4 reward SELECTION
                 (a project-local GeneratedResponseBasedLoss: require_generation
                  =True, is_differentiable=False; NOT an upstream TROPT edit)

The behavioral selection loss scores each candidate's FREE GENERATION with a
reward from `scripts/jailbreak_rewards.py` and returns `-reward` (TROPT
minimizes, so minimizing loss == maximizing reward). This realizes §15.6's
"Hybrid method: differentiable proxy proposal + generation reward selection".

CPU/IMPORT NOTE
---------------
TROPT and torch are imported LAZILY inside the assembly / factory functions so
this module (and its config + the pure-Python reward->loss transform) import and
unit-test under `/usr/bin/python3` where torch is absent. Actually building the
optimizer/loss needs the model wrappers and is a GPU-package concern; those
call-sites are marked. No model is loaded or run here.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional


# ---------------------------------------------------------------------------
# Pure-Python reward -> selection-loss transform (unit-testable, no torch)
# ---------------------------------------------------------------------------

def behavioral_reward_to_selection_loss(reward: float) -> float:
    """Map a behavioral reward in [0, 1] to a SELECTION loss (lower == better).

    Returns `-reward`: TROPT ranks candidates by ascending loss, so the highest
    behavioral reward becomes the lowest (best) loss. Strictly decreasing in the
    reward => the candidate ranking equals the reward ranking (reversed).
    """
    return -float(reward)


# ---------------------------------------------------------------------------
# D3 config (pure Python; the assembly reads this)
# ---------------------------------------------------------------------------

@dataclass
class ProxyCEBehavioralRerankConfig:
    """Config for the §15.4/§15.6 hybrid wiring (NOT REINFORCE).

    proposal_temperature applies to the Prefix-CE proposal loss; `momentum`
    turns the proposal into MAC (paper mu=0.6). `reward_variant` names which
    `jailbreak_rewards` scorer selects candidates. `num_generate_candidates`
    is how many top proposals are free-generated + reward-scored per step
    (§15.4 step 2: "free-generate from the top candidate subset").
    """

    # Proposal (Stage 1, differentiable Prefix-CE / MAC):
    momentum: float = 0.0                 # set 0.6 for MAC-momentum proposals
    proposal_temperature: float = 1.0
    clamp_min_nll: Optional[float] = None
    # GCG search params (mirror MAC__wang2024 defaults):
    num_steps: int = 20
    n_candidates: int = 256
    sample_topk: int = 256
    suffix_len: int = 20
    # Selection (Stage 2, behavioral reward over free generations):
    reward_variant: str = "strong_reject_rubric"
    num_generate_candidates: int = 16     # §15.4: only reward-score top subset
    # Bookkeeping:
    seed: Optional[int] = None

    def as_dict(self) -> dict:
        return {
            "objective": "proxy_ce_behavioral_rerank",
            "is_reinforce": False,          # explicit: NOT REINFORCE
            "momentum": self.momentum,
            "proposal_temperature": self.proposal_temperature,
            "clamp_min_nll": self.clamp_min_nll,
            "num_steps": self.num_steps,
            "n_candidates": self.n_candidates,
            "sample_topk": self.sample_topk,
            "suffix_len": self.suffix_len,
            "reward_variant": self.reward_variant,
            "num_generate_candidates": self.num_generate_candidates,
            "seed": self.seed,
        }


# ---------------------------------------------------------------------------
# Project-local behavioral SELECTION loss factory (lazy TROPT import)
# ---------------------------------------------------------------------------

def make_behavioral_selection_loss(
    reward_fn: Callable[[str, str], float],
    goals: list[str],
):
    """Build a project-local TROPT loss that SELECTS candidates by behavioral reward.

    Subclasses TROPT `GeneratedResponseBasedLoss` (require_generation=True,
    is_differentiable=False) WITHOUT editing upstream TROPT (hard-rule
    compliant): the class is defined here, in the project package.

    `reward_fn(goal, response) -> float in [0,1]` is injected (e.g. a
    `scripts/jailbreak_rewards.py` scorer bound to a frozen judge). `goals` are
    the per-template original instructions, aligned with the batch order TROPT
    passes to the loss.

    Returns an INSTANCE of the loss. Import is lazy so this module stays
    importable without torch; instantiation needs torch + the GPU package.
    """
    # GPU/torch CALL-SITE: importing tropt pulls in torch. Deferred to runtime.
    from tropt.loss import GeneratedResponseBasedLoss  # noqa: PLC0415
    import torch  # noqa: PLC0415
    from dataclasses import dataclass as _dc

    @_dc
    class BehavioralRewardSelectionLoss(GeneratedResponseBasedLoss):
        """§15.4 selection scorer: -reward over each candidate's free generation.

        NOT REINFORCE — this is candidate SELECTION only (no policy gradient).
        """

        def __call__(self, generated_response_strs):  # type: ignore[override]
            # `goals` aligns with the template/batch order; one reward per response.
            vals = [
                behavioral_reward_to_selection_loss(
                    reward_fn(goals[i % len(goals)], resp)
                )
                for i, resp in enumerate(generated_response_strs)
            ]
            return torch.tensor(vals, dtype=torch.float32)

    return BehavioralRewardSelectionLoss()


# ---------------------------------------------------------------------------
# D3 assembly (lazy TROPT import; NOT run here)
# ---------------------------------------------------------------------------

def assemble_proxy_ce_behavioral_rerank(
    model_obj,
    goals: list[str],
    reward_fn: Callable[[str, str], float],
    config: Optional[ProxyCEBehavioralRerankConfig] = None,
    tracker=None,
):
    """Assemble a `GCGPlusOptimizer` for §15.4/§15.6 hybrid reranking (**NOT REINFORCE**).

    Wiring (see module docstring): differentiable Prefix-CE(+MAC momentum)
    PROPOSAL loss as `proxy_loss`, project-local behavioral-reward SELECTION loss
    as `loss`. Returns the constructed optimizer (does NOT call
    `optimize_trigger`; running it needs a GPU + loaded `model_obj`).

    `model_obj` must be a TROPT `LMHFModel`-like white-box model
    (GradientTokenAccessMixin for gradient proposals AND generation for the
    selection loss). Building it and running the optimizer is the GPU package.
    """
    cfg = config or ProxyCEBehavioralRerankConfig()

    # GPU/torch CALL-SITE: imports require torch; model_obj must already exist.
    from tropt.loss import PrefillCELoss  # noqa: PLC0415
    from tropt.optimizer.gcgplus_optimizer import GCGPlusOptimizer  # noqa: PLC0415
    from tropt.optimizer.utils.token_constraints import TokenConstraints  # noqa: PLC0415

    proposal_loss = PrefillCELoss(
        temperature=cfg.proposal_temperature, clamp_min_nll=cfg.clamp_min_nll
    )
    selection_loss = make_behavioral_selection_loss(reward_fn=reward_fn, goals=goals)

    optimizer = GCGPlusOptimizer(
        model=model_obj,
        loss=selection_loss,            # Stage 2: behavioral reward SELECTION
        proxy_model=model_obj,
        proxy_loss=proposal_loss,       # Stage 1: differentiable Prefix-CE PROPOSAL
        tracker=tracker,
        candidate_selection="gradient",
        num_steps=cfg.num_steps,
        n_candidates=cfg.n_candidates,
        sample_topk=cfg.sample_topk,
        sample_n_replace=(1, 1),
        momentum=cfg.momentum,          # 0.6 => MAC-momentum proposals
        candidate_oversample_factor=1.1,
        token_constraints=TokenConstraints(),
        use_retokenize=True,
        seed=cfg.seed,
    )
    return optimizer


__all__ = [
    "behavioral_reward_to_selection_loss",
    "ProxyCEBehavioralRerankConfig",
    "make_behavioral_selection_loss",
    "assemble_proxy_ce_behavioral_rerank",
]
