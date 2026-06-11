# One-Page Advisor Brief — Mahmood, 2026-06-11

## Question

Does the structured puzzle format of CoT hijacking attacks work through a specific mechanistic property (refusal-direction dilution in Layer 22), or is its effectiveness purely behavioral and explainable by other means?

---

## What changed since last meeting

1. **Stage 4A2 result confirmed (already known):** 0/160 causal interventions survived. The Layer-22 direction is diagnostic, not causal.

2. **Stage 4.7 complete (new):** 12-prompt × 4-condition controlled experiment. Full puzzle (A) outperforms bare target (D) and length-matched benign control (F) on StrongREJECT. Sign tests: A−D p=0.031, A−F p=0.008, A−E p=0.031. Result stable across all 4 goals (LOGO 4/4).

3. **Stage 4.8 complete (new):** 60 stochastic generations across 4 prompts × 3 conditions × 5 seeds. A > D > F trend replicates. Goal identity dominates variance (between/within ratio 3.69×). Only 3 matched-outcome cells; direction extraction not valid (Branch C).

4. **Mechanistic null replicated:** Layer-22 projection ordering A < F < D is opposite to behavioral ordering A > D > F in both Stage 4.7 and Stage 4.8. Direction anti-correlates with thinking depth (ρ = −0.68), not with behavioral success.

---

## Three results

| # | Result | Strength |
|---|--------|---------|
| 1 | Puzzle outperforms length-matched benign control (A > F): behavioral effect is not explained by prompt length alone | Replicated across 12 prompts (p=0.008) and 4×5 stochastic seeds |
| 2 | Layer-22 scalar direction tracks thinking depth, not behavioral compliance; fails in both controlled and stochastic settings | Mechanistic null replicated in two independent experiments |
| 3 | Goal identity dominates stochastic variance: some goals are near-deterministically vulnerable, others near-deterministically resistant | Observed in Stage 4.8; Goal 1=0/15, Goal 3=15/15 |

---

## Main limitation

Behavioral results are restricted to 4 goal indices and 12 source prompts (Qwen3-14B, gpt-o4-mini). The mechanistic null is specific to this scalar Layer-22 direction — a richer representational structure (subspace, probe) may still capture a valid mechanism. LLM-onset annotation is blocked. No human behavioral labels.

---

## Recommended next sprint

**Primary recommendation: Option B — Mechanistic subspace/probe**

*Why now:* We have confirmed a behavioral effect (puzzle > controls) and a mechanistic null (scalar direction fails). The natural next question is whether a *richer* representation — a low-dimensional subspace or a learned probe — can predict compliance in controlled conditions. This is a publishable mechanistic contribution if it succeeds.

*What it involves:* Using Stage 4.7 and 4.8 representations, fit a low-dimensional probe on condition-stratified activations. Test whether the probe predicts within-condition success on held-out goals/prompts. If it does, this provides a validated (or partially validated) mechanistic story. If it fails, that too is informative.

*What it needs:* 4–8 additional goals with intermediate susceptibility to provide matched-outcome cells. This may require running a targeted Stage 4.9 first (≈20 generations, <1 GPU-hour) to identify candidate goals before committing to full representation extraction.

**Backup: Option C — AutoInject behavioral adaptation**

*Why consider it:* If Mahmood's thesis priority is attack-improvement rather than mechanistic understanding, AutoInject can be adapted to use StrongREJECT as behavioral objective instead of the failed scalar direction. This bypasses the mechanistic question and directly optimizes attacks.

*Tradeoff:* Strong applied contribution, but weaker mechanistic thesis. Does not explain *why* the puzzle works.

**Decision needed from Mahmood:** Which framing — mechanistic understanding (→ Option B) or attack-improvement (→ Option C)?
