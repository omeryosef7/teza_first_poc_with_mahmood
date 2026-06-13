"""
Post-hoc L22 diagnostic for the RL experiment.

Tests whether the RL-explored episodes where sr_success=True have lower mean
activation in the provisional harmful-vs-harmless contrast direction (Layer 22)
compared to episodes where sr_success=False.

Hypothesis: successful CoT hijacking correlates with lower L22 projection
during the thinking phase, suggesting the refusal direction is dampened when
the model processes the hidden target task.

IMPORTANT: This analysis is DIAGNOSTIC only. The L22 direction is described as
"provisional harmful-vs-harmless contrast direction" throughout. It has not been
validated as a causal refusal mechanism.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional


@dataclass
class L22DiagnosticResult:
    n_with_l22: int
    n_success_with_l22: int
    n_failure_with_l22: int
    mean_l22_success: Optional[float]
    mean_l22_failure: Optional[float]
    delta_l22: Optional[float]         # mean_success - mean_failure (negative = success has lower L22)
    interpretation: str
    warning: str


def analyze_l22_by_outcome(trace: list[dict]) -> L22DiagnosticResult:
    """
    Compare L22 projection between sr_success=True and sr_success=False episodes.

    Returns a L22DiagnosticResult with the direction of the effect and
    an interpretation string.
    """
    l22_success = [r["l22_think_phase"] for r in trace
                   if r.get("l22_think_phase") is not None and r.get("sr_success")]
    l22_failure = [r["l22_think_phase"] for r in trace
                   if r.get("l22_think_phase") is not None and not r.get("sr_success")]

    n_with_l22 = len(l22_success) + len(l22_failure)

    if not l22_success or not l22_failure:
        return L22DiagnosticResult(
            n_with_l22=n_with_l22,
            n_success_with_l22=len(l22_success),
            n_failure_with_l22=len(l22_failure),
            mean_l22_success=_mean(l22_success),
            mean_l22_failure=_mean(l22_failure),
            delta_l22=None,
            interpretation="Insufficient data: need both success and failure episodes with L22.",
            warning="L22 is provisional diagnostic direction only.",
        )

    mu_s = _mean(l22_success)
    mu_f = _mean(l22_failure)
    delta = mu_s - mu_f

    if abs(delta) < 0.1:
        direction = "negligible"
        interp = (
            f"L22 diagnostic: negligible difference between success (μ={mu_s:.2f}) "
            f"and failure (μ={mu_f:.2f}) episodes. "
            "The provisional direction does not separate outcomes in this RL run."
        )
    elif delta < 0:
        direction = "consistent with hypothesis"
        interp = (
            f"L22 diagnostic: success episodes have LOWER mean L22 projection "
            f"(μ_success={mu_s:.2f} vs μ_failure={mu_f:.2f}, Δ={delta:.2f}). "
            "Consistent with hypothesis that the provisional harmful-vs-harmless "
            "direction is dampened during successful CoT hijacking."
        )
    else:
        direction = "inconsistent with hypothesis"
        interp = (
            f"L22 diagnostic: success episodes have HIGHER mean L22 projection "
            f"(μ_success={mu_s:.2f} vs μ_failure={mu_f:.2f}, Δ={delta:.2f}). "
            "This is inconsistent with the dampening hypothesis. "
            "The provisional direction may capture something other than refusal gating."
        )

    return L22DiagnosticResult(
        n_with_l22=n_with_l22,
        n_success_with_l22=len(l22_success),
        n_failure_with_l22=len(l22_failure),
        mean_l22_success=round(mu_s, 4),
        mean_l22_failure=round(mu_f, 4),
        delta_l22=round(delta, 4),
        interpretation=interp,
        warning=(
            "L22 is labelled 'provisional harmful-vs-harmless contrast direction'. "
            "It is not a validated causal refusal mechanism. "
            "This analysis is diagnostic only."
        ),
    )


def analyze_l22_by_condition(trace: list[dict]) -> dict[str, dict]:
    """Mean L22 projection per condition across all episodes."""
    cond_l22: dict[str, list[float]] = {}
    cond_asr: dict[str, list[bool]] = {}
    for r in trace:
        c = r.get("condition", "")
        if r.get("l22_think_phase") is not None:
            cond_l22.setdefault(c, []).append(r["l22_think_phase"])
        cond_asr.setdefault(c, []).append(bool(r.get("sr_success")))

    result = {}
    for c in sorted(set(list(cond_l22.keys()) + list(cond_asr.keys()))):
        l22_vals = cond_l22.get(c, [])
        asr_vals = cond_asr.get(c, [])
        result[c] = {
            "n_episodes": len(asr_vals),
            "asr": round(sum(asr_vals) / len(asr_vals), 3) if asr_vals else None,
            "n_with_l22": len(l22_vals),
            "mean_l22": round(_mean(l22_vals), 4) if l22_vals else None,
        }
    return result


def _mean(vals: list[float]) -> float:
    return sum(vals) / len(vals) if vals else math.nan
