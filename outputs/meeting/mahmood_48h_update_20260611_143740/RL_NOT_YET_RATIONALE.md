# Why RL Is Not Yet the Right Immediate Experiment

_Generated: 2026-06-11T14:39:55.028761Z_

## Summary

RL is the natural next step **after** we have:
(a) validated measurable reward components,
(b) understood the timing/onset mechanism, and
(c) confirmed the behavior-conditioned direction extraction.

None of these three pre-conditions are fully met yet.

## Pre-Condition 1: Validated Reward Components

We have a primary reward (StrongREJECT score) that is valid and well-calibrated.
However:
- The onset proxy reward is provisional and needs manual validation
- The Layer-22 projection is **not** a valid reward (anti-correlates with behavior)
- Secondary reward weights (think length, onset delay) are not calibrated

**Status:** Primary reward ready; secondary rewards partial

## Pre-Condition 2: Understood Timing/Onset Mechanism

The central hypothesis is 'delayed safety commitment': attacks succeed when the model
commits to a long reasoning trajectory before safety decisions are triggered.

We have behavioral evidence (A > D > F in thinking length and ASR) but not yet:
- Mechanistic evidence that onset timing *causes* success (vs correlates with it)
- Validated onset measurements at scale
- Understanding of why condition F generates less thinking than A despite same length

**Status:** Behavioral evidence strong; mechanistic understanding incomplete

## Pre-Condition 3: Behavior-Conditioned Direction

Stage 4.8 produced only 3 matched-outcome cells (need ≥4).
The extension plan is prepared but not yet run.

**Status:** Blocked; extension ready to submit

## What to Do Instead (Immediate Contribution)

The immediate research contribution is defining and validating measurable reward
components from existing experiments. This is itself a novel contribution:

1. **Behavioral ASR report** (paper-style): A > D > F confirmed at 48-prompt scale
2. **Onset timing analysis**: first systematic attempt to measure timing in CoT hijacking
3. **RL readiness table**: first explicit mapping of reward components to data readiness

This frames the path to RL in a principled way for the paper.

## Timeline

| Step | Status | ETA |
|------|--------|-----|
| Validate onset proxy (20+ manual annotations) | TODO | 1–2 days |
| Run Stage 4.8 extension (60 gens) | Ready to submit | 4–8 hours on cluster |
| Behavior-conditioned direction extraction | Blocked | After extension |
| RL reward function design | This document | Ready for Mahmood review |
| RL implementation (GRPO prototype) | Not started | 1–2 weeks |

## Decision Request for Mahmood

1. Approve the reward function design above, or suggest modifications
2. Decide whether onset timing is worth the manual annotation effort
3. Approve submission of Stage 4.8 extension job
4. Confirm research framing: 'RL is next after onset validation' vs 'RL in parallel'