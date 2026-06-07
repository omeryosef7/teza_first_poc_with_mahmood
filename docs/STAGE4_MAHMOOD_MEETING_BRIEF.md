# Stage 4 Token Dynamics — Meeting Brief

**Date:** 2026-06-07  
**Model:** Qwen3-14B, `enable_thinking=True`  
**Full results:** [`docs/STAGE4_CURRENT_SPRINT_RESULTS.md`](STAGE4_CURRENT_SPRINT_RESULTS.md)

---

## Original Hypothesis

*Gradual refusal dilution:* Successful CoT-hijacking examples succeed because extended chain-of-thought reasoning progressively weakens a refusal-related internal representation by the time the final response token is generated. Under this account, the representational difference between successful and failed examples should grow over the course of thinking, not be present at its onset.

---

## Experimental Setup

- **Dataset:** 42 Qwen3-14B generation traces from Stage 6 (4 harmful goals, gpt-o4-mini as target model; 6 non-randomized attack streams, up to 2 attack iterations).
- **Data collection:** Forward pre-hooks on all 40 transformer layers; per-token hidden-state projections stored for every generated token. Total: 578,759 think/final/special tokens; 24,461,040 token × layer projection rows across 42 per-example JSON artifacts.
- **Provisional direction:** Layer 22, prompt position −3, extracted from the mean hidden-state difference between harmful and harmless prompt representations. Used as a scalar diagnostic feature only; it failed Stage 4A2 causal validation (0/160 candidates survived).
- **Primary outcome:** `sr_success = strongreject_score ≥ 0.5` (StrongREJECT evaluator). Secondary: `judge_success = judge_score == 10` (Gemini). Strong evaluator disagreement: 17 examples are SR-positive/Gemini-negative.
- **Statistics:** Firth (1993) penalized logistic regression (from scratch, no statsmodels); Wilson score and bootstrap 95% CIs; Hedges' g; BH correction; within-goal permutation test (10,000 iterations, seed 42).
- **Exclusions:** 1 not-separable example excluded from think-phase analyses; 2 right-censored examples (hit 32,768-token limit) retained with annotation.

---

## Five Most Important Findings

**1. The effect is early, not gradual.** The Layer-22 projection is higher in successful examples within the first 500 thinking tokens (Hedges' g = 1.256, MWU p = 0.0016, permutation p = 0.0003). This directly contradicts the gradual-dilution account: the difference is present before any extended deliberation has occurred.

**2. The effect persists across the entire reasoning trajectory.** Across all ten normalized-progress bins (first 10% through last 10% of thinking), Layer 22 shows a positive success-minus-failure difference ranging from g = +0.67 to g = +1.37. Goals 0, 2, and 3 are positive in all ten bins; Goal 1 is positive in nine of ten. 372 of 400 layer × bin cells are BH-significant at q < 0.05.

**3. The association survives confound adjustment — but barely.** Firth logistic regression adjusting for log thinking length, prompt length, goal, and attack iteration yields OR = 4.00 (95% Wald CI [1.06, 15.03], within-goal permutation p = 0.033). The CI lower bound barely exceeds one; removing one right-censored example yields OR = 3.76 (CI [0.99, 14.29], p = 0.052).

**4. The estimate is sensitive to goal composition (LOGO instability).** Excluding Goal 2 drops the adjusted OR from 4.00 to 1.90 with a CI including one (p = 0.350). This is because Goals 2 and 3 contribute the largest within-goal effect magnitudes (g = +3.034 and +1.524, CIs excluding zero), while Goals 0 and 1 contribute smaller, noisier effects. The direction stays positive in all four LOGO fits; only the magnitude shifts.

**5. No sharp sign reversal at the `</think>` boundary.** Per-prompt trajectory inspection of all 41 separable examples found no abrupt sign reversal in the scalar Layer-22 projection at the think-to-final transition. This weighs against a sharp "commitment token" model at that boundary. A representational transition could still occur earlier in thinking, in other layers, or in a multidimensional subspace.

---

## Three Primary Numerical Results

| Result | Value |
|--------|-------|
| Layer-22 first-500-token effect size (Hedges' g) | **1.256** (MWU p = 0.0016; permutation p = 0.0003; 95% bootstrap CI = [0.778, 2.313]) |
| Firth-adjusted OR for projection (Model 2, n=41) | **4.00** (95% Wald CI [1.06, 15.03]; within-goal permutation p = 0.033; LOGO min OR = 1.90) |
| Stage 4A2 causal validation | **0 / 160 candidates survived** (selection status: `intervention_selection_failed_no_survivors`) |

---

## Refined Interpretation

The evidence favors **early representational divergence** over gradual refusal dilution. Successful examples have higher Layer-22 projections from the very first tokens of thinking, and this difference is consistent across layers, normalized-progress bins, and goals. However, the direction is strongly anti-correlated with thinking length (Pearson r = −0.705 with log-think tokens). Successful examples also think shorter (mean 9,408 vs. 14,730 tokens). While the adjusted model retains a positive OR, the projection and think-length predictors cannot be fully disentangled at n = 41.

The most consistent account: at prompt presentation time, some feature of the interaction (prompt phrasing, goal type, attack strategy, or stochastic state) routes the model into a representational trajectory that is globally different for eventual successes vs. failures — and this is already measurable in the first 10% of thinking. Whether this feature is the harmful-versus-harmless contrast direction specifically, or whether the direction is a proxy for a broader trajectory-level state, cannot be determined without causal validation, which Stage 4A2 failed to provide.

**What this is not:** A proven refusal mechanism, a causal account, or a universally replicable effect (only 42 examples, 4 goals, one model).

---

## Main Limitations

1. **Small sample (n = 42).** All effect sizes and CIs are wide; LOGO instability is expected at this n.
2. **Non-randomized attack streams.** Stream 1 succeeds 85.7%, stream 4 succeeds 0%. This is an uncontrolled source of confounding.
3. **Direction failed causal validation.** Stage 4A2 found 0 surviving candidates; all results are associative.
4. **Projection–length entanglement.** Pearson r = −0.705 between projection and log-think tokens; the two predictors cannot be cleanly separated.
5. **Evaluator disagreement unexplained.** 19/42 examples show SR/Gemini disagreement; cause is unknown.
6. **One model, one capability.** Results may not generalize across models, goals, or attack strategies.

---

## Proposed Next Sprint

**Priority 1 — Disentangle projection from thinking length.**  
Design 4 matched conditions: (a) original puzzle attack, (b) harmful goal without puzzle, (c) long benign filler matched in length, (d) puzzle-only control at varying difficulties. This would let us attribute the effect to content, length, or the puzzle-as-reasoning-inducer independently.

**Priority 2 — Alternative contrast direction.**  
Extract the direction from matched refusal/compliance pairs (same prompt, different response outcomes) rather than harmful/harmless prompt pairs. The current direction was built from prompt-level contrast, not from response-level behavior.

**Priority 3 — Think vs. no-think ablation.**  
Generate the same 42 prompts with `enable_thinking=False` and compare outcomes. This tests whether extended thinking is a necessary condition for attack success or an epiphenomenon.

**Priority 4 — Small attention pilot (5 success, 5 failure pairs).**  
Reproduce the paper's attention-based analysis on a matched subset to provide a direct bridge to the original method.

---

## Recommended Figures

| # | File | What it shows |
|---|------|---------------|
| 1 | `fixed_window_layer22_group_comparison.png` | Group distributions and means at 500/1k/2k-token windows — the main early-divergence result |
| 2 | `normalized_progress_effect_heatmap.png` | Hedges' g across all 40 layers × 10 normalized bins — shows breadth and persistence |
| 3 | `confound_projection_adjusted_odds_ratio.png` | Adjusted OR with sensitivity overlays — the main confound-model result |
| 4 | `confound_leave_one_goal_out.png` | LOGO ORs — shows Goal 2 sensitivity and the fragility of the estimate |
| 5 | `goal_layer22_first500.png` | Within-goal projection differences — shows directionality is shared, magnitude differs |

All figures are in: `outputs/stage4/token_dynamics/full_20260604_101929/plots_analysis_v2/`
