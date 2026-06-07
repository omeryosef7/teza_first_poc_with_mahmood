# Stage 4 Token Dynamics — Current Sprint Results

**Model:** Qwen3-14B (`Qwen/Qwen3-14B`), `enable_thinking=True`  
**Dataset:** 42 Stage 6 attack generations (4 harmful goals, gpt-o4-mini target)  
**Stage 4 run path:** `outputs/stage4/token_dynamics/full_20260604_101929/`  
**Analysis date:** 2026-06-07  
**Primary outcome:** `sr_success = strongreject_score >= 0.5`  
**Secondary outcome:** `judge_success = judge_score == 10`  
**Provisional direction:** Layer 22, prompt position −3, extracted from harmful vs. harmless prompt contrast  
**Causal-validation status:** ❌ Failed — Stage 4A2 found 0 surviving candidates out of 160 evaluated  
**Full engineering details:** [`STAGE4_ENGINEERING_LOG.md`](../STAGE4_ENGINEERING_LOG.md)  
**Sprint plan:** [`docs/STAGE4_CURRENT_SPRINT_PLAN.md`](STAGE4_CURRENT_SPRINT_PLAN.md)

---

## 1. Executive Summary

Forty-two Qwen3-14B chain-of-thought generation traces from Stage 6 were collected and analyzed. Forty-one examples were usable for think/final phase analysis (one not-separable). All 40 transformer layers were captured per token, yielding 578,759 think/final/special tokens and 24,461,040 token-layer projection rows across 42 per-example artifacts.

**Behavioral outcomes:** 19 of 42 examples achieved SR success (`strongreject_score ≥ 0.5`). Four examples achieved Gemini success (`judge_score = 10`). Strong bidirectional disagreement was observed (19 total, predominantly SR-positive/Gemini-negative).

**Main associative finding:** The projection of each token's layer-22 hidden state onto a *provisional harmful-versus-harmless contrast direction* is higher in successful examples than in failed examples from the very start of the thinking phase. This positive difference:

- Is present within the first 500 thinking tokens (before any extended reasoning can have occurred).
- Persists across all ten normalized-progress bins across all four goals.
- Survives adjustment for log thinking length, prompt length, goal, and attack iteration (Firth OR = 4.00, 95% Wald CI [1.06, 15.03]).
- Is consistent in direction across all four goals, though heterogeneous in magnitude.
- Yields an empirical within-goal permutation p = 0.033.

**Caveats:** The CI lower bound barely exceeds one; removing one right-censored example moves the CI to [0.990, 14.285], p = 0.052. Excluding Goal 2 drops the OR to 1.90 with a CI including one. Model 2 does not improve leave-one-out log loss over the covariate-only baseline. The direction failed the current causal intervention criteria (Stage 4A2, 0/160 survivors).

**Stage 4A2:** 160 candidate direction-position pairs were evaluated using ablation-based causal validation. All 160 failed to pass the required steering and KL-divergence thresholds. The direction is correlational and diagnostic only.

**Hypothesis update:** The original working hypothesis (gradual refusal dilution during extended reasoning) is not supported. The positive difference is already present in the first 10% of thinking rather than emerging late. A more consistent account is early representational divergence, though the semantic and causal interpretation of the provisional direction remains unresolved.

---

## 2. Research Question

**Central question:** When and where during extended reasoning do successful and failed chain-of-thought hijacking examples diverge in their internal representation?

**Operational subquestions addressed in this sprint:**

1. Is the representational difference already present early in the thinking phase, or does it emerge gradually?
2. Does the difference grow monotonically with reasoning progress?
3. Is it specific to layer 22, or broadly distributed across layers?
4. Does the difference survive statistical control for reasoning length and goal composition?
5. Is the effect shared across all four harmful goals, or concentrated in one?
6. Is there a sharp representational transition at the `</think>` boundary?

---

## 3. Data and Pipeline

**Dataset:**  42 adversarial attack examples targeting `gpt-o4-mini`, spanning 4 harmful goal categories and up to 2 attack iterations per goal. Conversation IDs represent distinct attack streams, not randomized experimental conditions.

**Model:** Qwen3-14B with `enable_thinking=True`. The model generates a `<think>…</think>` block before its final response. Forward pre-hooks were installed at all 40 transformer layers to capture hidden-state projections at each generated token position.

**Token counts (confirmed from per-example artifacts):**

| Statistic | Value |
|-----------|-------|
| Total per-example JSON files | 42 |
| Total generated tokens (all roles, including not-separable) | 611,526 |
| Total think + final + special tokens | **578,759** |
| Total token × layer projection rows | **24,461,040** |
| Token-count match: Stage 6 vs Stage 4 | 42/42 ✓ |

**Run:** `outputs/stage4/token_dynamics/full_20260604_101929/`  
**Compute:** Single NVIDIA L40S GPU, two Slurm jobs (476121 and 490729) covering all 42 examples.

See [`STAGE4_ENGINEERING_LOG.md`](../STAGE4_ENGINEERING_LOG.md) for detailed engineering failures, restarts, and fixes during data collection.

---

## 4. Dataset Audit and Outcome Definitions

**Audit script:** `poc_stage4/audit_token_dynamics_dataset.py`

| Property | Count |
|----------|-------|
| Total examples audited | **42** |
| Usable for generation analysis | 42 |
| Usable for think-phase analysis | **41** |
| Usable for final-phase analysis | 41 |
| Not-separable (think/final cannot be split) | 1 (Goal 2, iter 1, conv 5) |
| Right-censored (hit 32,768-token limit) | 2 (Goal 2, iter 1, conv 4 and conv 5) |
| Layers available per example | 40 (layers 0–39) |
| Token-count mismatches | 0 |
| Missing/non-finite projection values | 0 |

**Outcome definitions:**

| Outcome | Definition | Count |
|---------|-----------|-------|
| `sr_success` (primary) | `strongreject_score ≥ 0.5` | 19 / 42 |
| `sr_failure` | `strongreject_score < 0.5` | 23 / 42 |
| `judge_success` (secondary) | `judge_score == 10` | 4 / 42 |
| `combined_success` | `sr_success OR judge_success` | — |
| SR-positive / Gemini-negative (major disagreement type) | `sr_success=True AND judge_success=False` | 17 |
| Gemini-positive / SR-negative (evaluator disagreement) | `sr_success=False AND judge_success=True` | 2 |
| Total bidirectional disagreements | — | 19 |

`sr_success` is used as the primary outcome throughout all analyses. The cause of the evaluator disagreement (StrongREJECT vs. Gemini) is not established; hypotheses are outside the scope of this sprint.

---

## 5. Provisional Direction and Causal Status

**Extraction:** A linear contrast direction was extracted at Qwen3-14B layer 22, prompt token position −3, using the difference in mean hidden-state activations between harmful and harmless prompt representations. This is referred to throughout as the *provisional harmful-versus-harmless contrast direction*.

**Selection:** Layer 22 and position −3 were pre-specified from Stage 4A1 projection diagnostics.

**Stage 4A2 causal validation:**

| Metric | Value |
|--------|-------|
| Candidates evaluated | 160 (4 positions × 40 layers) |
| Survivors (passed all filters) | **0** |
| Selection status | `intervention_selection_failed_no_survivors` |
| Failure reason — steering below threshold | 160 / 160 |
| Failure reason — KL divergence above threshold | 92 / 160 |
| Failure reason — layer pruned | 32 / 160 |
| Best ablation steering score achieved | −17.10 (harmful direction; did not pass threshold) |
| Warning | "do not run Stage 4B scientifically from this direction" |

> **The direction is correlational and diagnostic. It has not passed the current causal intervention criteria. No causal-refusal claims are made in this document.**

All downstream analyses treat the direction as a *scalar feature* for associative analysis. Findings are associative only.

---

## 6. Initial Aggregate Observation (Motivation for Confound Control)

Before any window or confound control, successful examples have higher mean layer-22 projections over the entire think phase, and failed examples have longer reasoning chains.

| Group | Mean layer-22 think-phase projection | Mean think length |
|-------|--------------------------------------|-------------------|
| SR success (n=19) | Higher | **9,408 tokens** |
| SR failure (n=22) | Lower | **14,730 tokens** |

The projection feature has a strong negative correlation with reasoning length (Pearson r = −0.705 with log-think tokens). This creates a potential confound: longer-thinking failures may appear to have lower projections simply because they think longer, rather than because of a genuine representational difference. The fixed-window analysis addresses this by comparing projections over the same initial token window, independently of total reasoning length.

---

## 7. Fixed-Window Analysis

**Script:** `poc_stage4/analyze_fixed_windows.py`  
**Design:** Compare the mean layer-22 projection over the first *W* thinking tokens, where *W* ∈ {500, 1,000, 2,000}. Only examples with ≥ *W* thinking tokens are included. Layer 22 is the pre-specified primary layer. All 41 think-eligible examples have ≥ 500 tokens.

**Authoritative results — Layer 22, subset `all` (from `fixed_window_group_summary.csv`):**

| Window | n_suc | n_fail | Success mean | Failure mean | Difference | Cohen's d | Hedges' g | MWU p | Perm p | Bootstrap 95% CI |
|--------|------:|------:|------------:|------------:|-----------:|----------:|----------:|------:|-------:|---------------:|
| 500 tok | 19 | 22 | **4.664** | **3.119** | **+1.545** | 1.281 | 1.256 | 0.0016 | 0.0003 | [0.778, 2.313] |
| 1,000 tok | 19 | 22 | **4.874** | **3.047** | **+1.827** | 1.281 | 1.256 | 0.0019 | 0.0002 | [0.973, 2.777] |
| 2,000 tok | 16 | 22 | **4.340** | **3.004** | **+1.336** | 1.294 | 1.267 | 0.0033 | 0.0004 | [0.664, 2.018] |

Notes:
- The direction is positive (success > failure) in all three windows.
- Effect sizes are large (Hedges' g ≈ 1.26–1.27) and remarkably consistent across windows.
- The difference is present within the first 500 thinking tokens, before any extended deliberation.
- Excluding the right-censored example does not materially alter the results.
- n_success drops from 19 to 16 at the 2,000-token window because three successful examples had fewer than 2,000 thinking tokens.

**Best layer by fixed window (exploratory, post-hoc):**

| Window | Best layer | Hedges' g |
|--------|-----------|----------|
| 500 tok | Layer 13 | 1.603 |
| 1,000 tok | Layer 13 | 1.590 |
| 2,000 tok | Layer 16 | 1.571 |

Layer 22 (Hedges' g ≈ 1.256) is not the most discriminative layer in the fixed-window analysis. Layers 13 and 16 show larger standardized effects but were identified *post-hoc* and must not be treated as primary evidence.

**Figures:**
- [`fixed_window_layer22_group_comparison.png`](../outputs/stage4/token_dynamics/full_20260604_101929/plots_analysis_v2/fixed_window_layer22_group_comparison.png)
- [`fixed_window_effect_by_layer.png`](../outputs/stage4/token_dynamics/full_20260604_101929/plots_analysis_v2/fixed_window_effect_by_layer.png)

---

## 8. Normalized-Progress Analysis

**Script:** `poc_stage4/analyze_normalized_progress.py`  
**Design:** Each example's thinking tokens are divided into 10 equal-size bins (bin 0 = first 10%, bin 9 = last 10%). The mean projection within each bin is computed per example. Group comparisons use each example's bin mean as the statistical unit. Coverage: 41 examples × 40 layers × 10 bins.

**Layer-22 results across all 10 bins (n_success = 19, n_failure = 22, subset `all`):**

| Bin | Range | Diff (S−F) | Hedges' g | BH q < 0.05 | Bootstrap 95% CI |
|-----|-------|----------:|----------:|:-----------:|---------------:|
| 0 | 0–10% | +1.667 | **+1.366** | ✓ | [0.942, 2.423] |
| 1 | 10–20% | +1.366 | +1.161 | ✓ | [0.636, 2.113] |
| 2 | 20–30% | +1.120 | +0.876 | ✓ | [0.378, 1.906] |
| 3 | 30–40% | +1.530 | +0.904 | ✓ | [0.631, 2.691] |
| 4 | 40–50% | +1.407 | +0.673 | ✓ | [0.259, 2.867] |
| 5 | 50–60% | +1.776 | +0.792 | ✓ | [0.648, 3.362] |
| 6 | 60–70% | +1.026 | +0.840 | ✓ | [0.299, 1.717] |
| 7 | 70–80% | +1.145 | +1.011 | ✓ | [0.472, 1.826] |
| 8 | 80–90% | +1.058 | +0.883 | ✓ | [0.329, 1.737] |
| 9 | 90–100% | +1.321 | +1.168 | ✓ | [0.673, 2.050] |

- Layer-22 Hedges' g ranges from +0.67 (bin 4) to +1.37 (bin 0).
- BH correction based on Mann-Whitney p-values across all 400 cells (40 layers × 10 bins); 372/400 cells BH-significant at q < 0.05.
- **The difference is already present in bin 0 (first 10% of thinking)**, the earliest measurable point.
- No bin shows a negative difference; the direction is positive and consistent throughout.

> **The positive difference is not a late-emerging phenomenon. It is present from the earliest measurable point in the reasoning process, and it persists across the entire reasoning trajectory.**

**Strongest exploratory cell (post-hoc):** Layer 38, bin 7 (70–80%), Hedges' g ≈ +1.70. This was identified after examining all 400 cells; treat as hypothesis-generating only.

**Note on BH correction:** The 40 layers and 10 bins are strongly correlated (adjacent bins and adjacent layers share representations). The 372/400 BH-significant figure should be interpreted as indicating a broad, layer-spanning and bin-spanning positive association, not 372 independent tests.

**Figures:**
- [`normalized_progress_layer22.png`](../outputs/stage4/token_dynamics/full_20260604_101929/plots_analysis_v2/normalized_progress_layer22.png)
- [`normalized_progress_layer22_difference.png`](../outputs/stage4/token_dynamics/full_20260604_101929/plots_analysis_v2/normalized_progress_layer22_difference.png)
- [`normalized_progress_effect_heatmap.png`](../outputs/stage4/token_dynamics/full_20260604_101929/plots_analysis_v2/normalized_progress_effect_heatmap.png)

---

## 9. Confound-Controlled Modeling

**Script:** `poc_stage4/fit_confound_models.py`  
**Method:** Firth (1993) penalized-likelihood logistic regression, implemented from scratch in NumPy/SciPy. No external modeling packages. Fitting dataset: 41 think-eligible examples; n_success = 19, n_failure = 22.

**Primary predictor:** Layer-22, first-500-token mean projection, z-scored within the fitting subset (mean = 3.835, SD = 1.424). Standardization was pre-specified.

**Pre-specified covariates:** log(think_token_count), z-scored prompt_token_count, C(goal_index, ref=0), attack_iteration.

**Events-per-predictor:** 19 events / 8 predictors ≈ 2.4. Firth correction mitigates but does not eliminate estimation uncertainty at this ratio.

### Model comparison

| Model | Description | n | LOO log loss | LOO Brier | LOO AUC |
|-------|------------|---|:------------:|:---------:|:-------:|
| **M0** | Covariates only (7 params) | 41 | 0.778 | 0.248 | 0.644 |
| **M1** | Projection only (2 params) | 41 | **0.572** | **0.184** | **0.754** |
| **M2** | Projection + covariates (8 params) | 41 | 0.820 | 0.242 | 0.663 |

M1 (projection-only, simpler) achieves the best LOO metrics on all three measures. M2 (the primary adjusted model) performs *worse* than M0 in LOO log loss (0.820 vs 0.778), a consequence of adding 6 parameters in a dataset of n=41. This does not mean the projection adds no value — M1's superiority over M0 is consistent with the projection carrying independent predictive information — but M2's LOO penalty reflects the cost of over-parameterization at small n.

### Primary adjusted result (Model 2)

```
sr_success ~ projection_z + log1p(think_tokens) + prompt_z
             + C(goal_index, ref=0) + attack_iteration
n=41, n_success=19
```

| Predictor | Coefficient | SE | Odds Ratio | 95% Wald CI | Wald p |
|-----------|------------|-----|-----------|-------------|--------|
| **projection_z** | **+1.386** | **0.676** | **4.00** | **[1.06, 15.03]** | **0.040** |
| log_think | −1.316 | 0.987 | 0.27 | [0.04, 1.86] | 0.183 |
| prompt_z | +0.346 | 0.602 | 1.41 | [0.43, 4.60] | 0.565 |
| goal_1 | +1.464 | 1.119 | 4.32 | [0.48, 38.8] | 0.191 |
| goal_2 | +0.891 | 1.205 | 2.44 | [0.23, 25.9] | 0.460 |
| goal_3 | +0.580 | 1.324 | 1.79 | [0.13, 23.9] | 0.661 |
| attack_iter | −1.146 | 0.935 | 0.32 | [0.05, 1.99] | 0.220 |

> **The projection coefficient remains positive and potentially large after adjusting for all measured covariates (OR = 4.00). However, the CI lower bound barely exceeds one, the LOO metrics do not improve over the simpler models, and the estimate is sensitive to the goal composition of the dataset.**

### Sensitivity analyses

**Sensitivity A — Exclude right-censored example (n=40):**
- OR = 3.76, CI = [0.990, 14.285], p = 0.052
- The CI marginally crosses one; the effect direction is unchanged.

**Sensitivity B — Layer-22 bin-0 feature (first 10% of thinking, pre-specified bin from Phase 3):**
- OR = 5.15, CI = [1.33, 19.93]
- Consistent with a strong early component.

**Sensitivity C — Alternative layers (exploratory, post-hoc):**

| Layer | OR | 95% CI |
|-------|----|--------|
| Layer 13 | 4.43 | [1.53, 12.85] |
| Layer 16 | 5.98 | [1.53, 23.33] |
| Layer 22 (pre-specified) | 4.00 | [1.06, 15.03] |

All three layers yield positive ORs with CIs excluding one, consistent with a broad representational signature rather than a layer-22-specific effect.

**Sensitivity D — Leave-one-goal-out (LOGO):**

| Excl. goal | n | n_success | Projection OR | 95% CI | Wald p |
|-----------|---|----------|--------------|--------|--------|
| Goal 0 | 29 | 15 | 9.63 | [1.27, 73.0] | 0.028 |
| Goal 1 | 29 | 12 | 12.58 | [0.90, 175.5] | 0.060 |
| **Goal 2** | **30** | **14** | **1.90** | **[0.50, 7.27]** | **0.350** |
| Goal 3 | 35 | 16 | 3.02 | [0.90, 10.15] | 0.073 |

Excluding Goal 2 materially weakens the adjusted association (OR drops from 4.00 to 1.90, CI includes one). This instability reflects the partial goal-specificity of the effect at n=41 and is examined further in Section 12. It does not indicate a sign reversal — the direction remains positive in all four LOGO fits.

**Sensitivity E — Within-goal permutation test:**
- Test statistic: |projection_z coefficient| in Model 2.
- Observed statistic: 1.386.
- Null 97.5th percentile: 1.232.
- **Empirical p-value: 0.033** (10,000 permutations, seed 42).
- The observed coefficient exceeds the within-goal null at the 0.033 significance level.

**Continuous StrongREJECT analysis:**
- Spearman ρ (projection_z vs SR score): **0.531** (p = 0.0004), 95% bootstrap CI: [0.256, 0.750].
- Partial Spearman after OLS residualization on covariates: **ρ = 0.438** (p = 0.0042).
- Caution: SR scores are highly discrete. These correlations are consistent with the binary outcome associations but should not be over-interpreted.

**Figures:**
- [`confound_projection_adjusted_odds_ratio.png`](../outputs/stage4/token_dynamics/full_20260604_101929/plots_analysis_v2/confound_projection_adjusted_odds_ratio.png)
- [`confound_model_comparison.png`](../outputs/stage4/token_dynamics/full_20260604_101929/plots_analysis_v2/confound_model_comparison.png)
- [`confound_leave_one_goal_out.png`](../outputs/stage4/token_dynamics/full_20260604_101929/plots_analysis_v2/confound_leave_one_goal_out.png)

---

## 10. Reasoning Length Relationship

Successful and failed examples differ substantially in reasoning length:

| Group | Mean think length | n |
|-------|------------------|---|
| SR success | **9,408 tokens** | 19 |
| SR failure | **14,730 tokens** | 22 |

The projection feature is moderately-to-strongly anti-correlated with reasoning length (Pearson r = −0.705 with log-think tokens; Spearman ρ = −0.463, p = 0.0023). Shorter-thinking examples tend to have higher early projections and are more likely to succeed.

**Key interpretive constraint:** The projection and reasoning length are not independent. However, the adjusted Model 2 projection coefficient remains positive (OR = 4.00) after including log(think_tokens) as a covariate, and the within-goal permutation p remains significant (0.033). This indicates that the projection is not purely reducible to reasoning length, though the two cannot be cleanly separated in a dataset of n = 41.

Shorter reasoning is associated with success, but shorter reasoning also correlates with higher early projection. Whether the projection predicts outcomes *beyond* what is predicted by length alone, or whether both reflect a common upstream state, cannot be resolved in this associative analysis.

**Figure:**
- [`confound_projection_vs_think_length.png`](../outputs/stage4/token_dynamics/full_20260604_101929/plots_analysis_v2/confound_projection_vs_think_length.png)

---

## 11. Per-Prompt Trajectory Inspection

**Script:** `poc_stage4/plot_per_prompt_trajectories.py`  
**Selected layers:** 13, 16, 22, 26, 30, 38, 39. Layer 22 is the pre-specified primary layer. Layer 38 is exploratory.

| Statistic | Value |
|-----------|-------|
| Total examples | 42 |
| Full-generation plots generated | 42 |
| Think/final transition plots | 41 (1 not-separable excluded) |
| Total plots | 168 |

**Think-to-final boundary observation:**

> No abrupt sign reversal was observed in the scalar Layer-22 projection at the `</think>` boundary in any of the 41 separable examples.

The projection trajectory at the think-to-final transition was continuous in the Layer-22 scalar projection for all 41 examples with valid segmentation. This observation is specific to the scalar Layer-22 projection and should not be interpreted as ruling out a commitment-related transition more broadly.

A representational commitment or transition could:
- Occur earlier in the thinking phase (before `</think>`).
- Appear as a change in magnitude or slope rather than a sign reversal.
- Be visible in a different layer or combination of layers.
- Require a multidimensional representation not captured by a scalar projection.

**Plot index:** [`analysis/per_prompt_plot_index.md`](../outputs/stage4/token_dynamics/full_20260604_101929/analysis/per_prompt_plot_index.md)

Canonical examples (including the right-censored example and the not-separable example) are documented in [`canonical_examples.json`](../outputs/stage4/token_dynamics/full_20260604_101929/analysis/canonical_examples.json). No raw harmful prompt or output text is reproduced here.

---

## 12. Goal and Iteration Heterogeneity

**Script:** `poc_stage4/analyze_goal_iteration_effects.py`  
**All results in this section are exploratory. Group sizes are small (6–12 examples per goal).**

### 12.1 Behavioral outcomes by goal

| Goal | Successes | Total | SR rate | Wilson 95% CI |
|------|----------:|------:|--------:|:-------------:|
| 0 | 4 | 12 | 0.333 | [0.138, 0.609] |
| 1 | 7 | 12 | 0.583 | [0.320, 0.807] |
| 2 | 5 | 12 | 0.417 | [0.193, 0.680] |
| 3 | 3 | 6  | 0.500 | [0.188, 0.812] |

All Wilson CIs are wide and overlap substantially. No goal can be claimed as meaningfully different from the others in SR success rate at these sample sizes.

### 12.2 Layer-22 first-500 projection difference by goal

| Goal | Diff (S−F) | Hedges' g | Bootstrap 95% CI | nS | nF |
|------|----------:|----------|:----------------:|:--:|:--:|
| 0 | +0.855 | +0.870 | [−0.294, +1.973] | 4 | 8 |
| 1 | +0.435 | +0.273 | [−0.972, +1.908] | 7 | 5 |
| 2 | **+2.640** | **+3.034** | **[+1.757, +3.630]** | 5 | 6 |
| 3 | **+2.904** | **+1.524** | **[+1.512, +5.379]** | 3 | 3 |

All four goals show positive success-minus-failure differences. Goals 2 and 3 have large effect magnitudes with bootstrap CIs excluding zero. Goals 0 and 1 show positive differences of smaller magnitude, with CIs including zero given their subgroup sizes.

### 12.3 Normalized-progress trajectories by goal (Layer 22)

> Goals 0, 2, and 3 show positive success-minus-failure differences in all ten normalized-progress bins. Goal 1 shows a positive difference in nine of ten bins.

The positive association is directionally shared across all four goals and is not confined to a single normalized-progress window.

**Why Goal 2 matters for the LOGO instability:** Goal 2 contributes disproportionately to the adjusted overall association. When it is excluded, the remaining goals (0, 1, 3) have smaller and noisier within-goal effects, causing the OR to drop from 4.00 to 1.90 with a CI including one. Goal 2 is not a sign outlier — its direction is the same as all other goals — but it is a *magnitude* contributor to the pooled effect.

### 12.4 Attack iteration comparison (not causal)

| Iteration | n | SR successes | SR rate | Mean think length | Mean L22 first-500 |
|-----------|---|-------------|---------|:-----------------:|:------------------:|
| 1 | 24 | 12 | 0.500 | 13,023 | 3.940 |
| 2 | 18 | 7  | 0.389 | 11,292 | 3.700 |

Iteration 1 has a slightly higher success rate (0.500 vs 0.389) and higher mean L22 projection (3.940 vs 3.700). Iteration 2 prompts were generated through an iterative refinement process and may differ systematically in content from iteration 1; this comparison is descriptive and cannot be interpreted causally.

### 12.5 Conversation stream descriptives

| Conv | n | SR rate | Mean L22 first-500 |
|------|---|---------|--------------------|
| 1 | 7 | 0.857 | 6.073 |
| 2 | 7 | 0.429 | 2.427 |
| 3 | 7 | 0.857 | 4.673 |
| 4 | 7 | 0.000 | 2.641 |
| 5 | 7 | 0.429 | 4.112 |
| 6 | 7 | 0.143 | 3.123 |

There is strong descriptive heterogeneity across non-randomized attack streams. Streams 1 and 3 achieve SR rate 0.857; stream 4 achieves 0.000. This reflects differences in how the attack conversations were constructed, not an experimental treatment effect.

> Conversation IDs represent non-randomized attack streams. These differences indicate substantial prompt-stream heterogeneity and should not be interpreted as experimental treatment effects.

**Figures:**
- [`goal_success_rates.png`](../outputs/stage4/token_dynamics/full_20260604_101929/plots_analysis_v2/goal_success_rates.png)
- [`goal_layer22_first500.png`](../outputs/stage4/token_dynamics/full_20260604_101929/plots_analysis_v2/goal_layer22_first500.png)
- [`goal_normalized_layer22.png`](../outputs/stage4/token_dynamics/full_20260604_101929/plots_analysis_v2/goal_normalized_layer22.png)

---

## 13. Refined Scientific Interpretation

### What the evidence supports

1. **Early representational divergence.** The Layer-22 projection difference is visible in the first 500 thinking tokens, is present in the first 10% of normalized thinking, and persists across all 10 normalized-progress bins. The original gradual-dilution hypothesis would predict the difference to emerge or grow during reasoning; instead, it is present immediately.

2. **Positive and directionally consistent association.** Successful examples have higher projection than failed examples across all pre-specified windows, all normalized bins, all four goals, and both attack iterations.

3. **Survival of confound adjustment.** The positive association survives adjustment for log thinking length, prompt length, goal, and attack iteration (Firth OR = 4.00, permutation p = 0.033), suggesting the association is not entirely attributable to the measured covariates.

4. **Heterogeneity in effect magnitude.** Goals 2 and 3 show large within-goal effects; Goals 0 and 1 show smaller effects. The overall estimate is sensitive to goal composition.

5. **Broad layer coverage.** Layers 13, 16, and 38 show equal or larger standardized effects than layer 22. The association is not layer-22-specific; it appears distributed across multiple layers, which may indicate a global trajectory-level difference rather than a narrowly localized refusal mechanism.

### What the evidence weighs against

1. **Gradual refusal dilution.** The hypothesis that successful examples succeed because extended reasoning gradually dilutes a refusal-related representation is not supported. The difference is present at the very start of thinking, not at the end.

2. **A sharp Layer-22 sign flip at `</think>`.** No abrupt sign reversal was observed in the scalar Layer-22 projection at the think-to-final boundary in any of the 41 separable examples.

3. **Layer-22 specificity.** Layer 22 is not uniquely discriminative. Layers 13 and 16 show larger standardized effects in fixed-window analysis. The effect is broad across layers.

### What remains unresolved

1. **Semantic meaning of the direction.** The provisional direction was extracted from a harmful vs. harmless prompt contrast and has not passed causal validation. Whether it captures harmful-content engagement, risk recognition, task commitment, or another shared feature of successful attack prompts is not known.

2. **Causal role.** The direction failed Stage 4A2 causal validation (0/160 candidates survived). No causal-refusal claims are warranted.

3. **Generalization.** Only 4 harmful goals and 42 prompts were analyzed. Generalization to other goals, models, or attack strategies is unknown.

4. **Judge disagreement.** The cause of the SR/Gemini disagreement (17 SR-positive/Gemini-negative, 2 Gemini-positive/SR-negative) is not explained.

5. **Reasoning length confound.** Projection and think length are strongly anti-correlated (Pearson r = −0.705). The adjusted model retains a positive coefficient, but the two features cannot be fully separated at n = 41.

6. **Whether shorter thinkers succeed because of higher projection or because short thinking is itself causal** (e.g., because the model committed early rather than reconsidering) is not resolvable from this analysis.

---

## 14. Thesis-Safe Main Conclusion

> Successful and failed CoT-hijacking examples exhibit an early and persistent difference in projection onto a provisional harmful-versus-harmless contrast direction. The difference is visible within the first 500 thinking tokens, remains positive across the normalized reasoning trajectory, and is directionally shared across all four goals. A confound-adjusted model retains a potentially large positive association (Firth OR = 4.00, 95% Wald CI [1.06, 15.03], within-goal permutation p = 0.033), but the estimate is statistically fragile, sensitive to goal composition, and does not clearly improve leave-one-out prediction beyond measured covariates. These observations are more consistent with early representational divergence than with a purely gradual refusal-dilution account. However, because the direction failed the current causal intervention criteria (0/160 Stage 4A2 survivors), its semantic and causal relationship to refusal remains unresolved.

---

## 15. Limitations

1. **Small sample:** 42 total examples, 41 think-eligible. All effect sizes and confidence intervals are wide.
2. **Four harmful goals only.** The dataset covers a narrow slice of adversarial content.
3. **Non-randomized prompt streams.** Conversation IDs represent distinct attack streams with heterogeneous success rates; this is a source of unmeasured confounding.
4. **Single run per example.** Stage 6 generations are stochastic; a different temperature or seed could produce different outcomes.
5. **Evaluator disagreement.** StrongREJECT and Gemini agree on 23/42 examples but disagree on 19. The disagreement pattern is predominantly SR-positive/Gemini-negative and the cause is not established.
6. **Small subgroups.** Goal-level and iteration-level subgroup sizes (3–8 per group) preclude confirmatory inference.
7. **Correlated features.** 40 layers and 10 normalized bins are strongly correlated. BH corrections assume independence; the 372/400 BH-significant figure overstates the number of independent detections.
8. **Post-hoc layer exploration.** Layers 13, 16, and 38 were identified post-hoc as showing larger effects than layer 22. They cannot serve as pre-specified primary evidence.
9. **One not-separable example.** The think/final boundary could not be determined for goal=2, iter=1, conv=5. It is excluded from all think-phase analyses.
10. **Two right-censored generations.** Both goal=2 examples (conv=4 and conv=5) hit the 32,768-token generation limit.
11. **Asymptotic Wald intervals.** Wald confidence intervals are asymptotic; profile-likelihood intervals would be more appropriate at n=41.
12. **Custom Firth implementation.** The penalized-likelihood implementation has not been independently validated against a reference package.
13. **Stage 4A2 zero survivors.** The direction is not causally validated. All downstream analyses are associative.
14. **Observational design.** This is a retrospective analysis of existing attack outcomes; no causal inference is possible.

---

## 16. Recommended Next Steps

*These are research directions only. None are implemented in this document.*

**Priority 1 — Revisit the contrast direction:**
- Extract an alternative direction using matched refusal/compliance contrasts (same prompt, two responses) rather than harmful/harmless prompt pairs.
- Explore a multidimensional subspace rather than a scalar projection.
- Test whether the direction captures harmful-content engagement, reasoning difficulty, or risk recognition.

**Priority 2 — Disentangle projection from reasoning length:**
- *Puzzle-vs-length ablation:* Compare (a) original puzzle attack, (b) harmful goal without puzzle, (c) matched long benign filler, (d) puzzle-only control with varying difficulties.
- This would separate the effect of puzzle complexity from think-length and from the harmful content.

**Priority 3 — Think vs. no-think ablation:**
- Compare `enable_thinking=True` vs. `enable_thinking=False` on the same prompts.
- Establishes whether the think phase is a necessary condition or an epiphenomenon.

**Priority 4 — Small attention-percentage pilot:**
- Reproduce the paper's attention-based methodology on a small matched set (5 success, 5 failure).
- Compare to projection-based findings without conflating the two approaches.

**Priority 5 — Multiple runs per prompt:**
- Generate 3–5 outcomes per prompt to separate prompt-level from generation-level effects.

**Priority 6 — Cross-model replication:**
- Apply the same pipeline to a second model (e.g., Llama-3, Gemma) to test generalization.

**Priority 7 — Only after the above** should RL optimization, unified causal theory, or Stage 4B causal validation be reconsidered.

---

## 17. Artifact Index

| Artifact | Description | Path |
|----------|-------------|------|
| Stage 4 run directory | Root of all analysis artifacts | `outputs/stage4/token_dynamics/full_20260604_101929/` |
| Per-example projections | 42 JSON files with token-level projections | `per_example/*.json` |
| Analysis dataset | 42-row audit CSV | `analysis/analysis_dataset.csv` |
| Fixed-window per example | Per-example, per-layer, per-window means | `analysis/fixed_window_per_example.csv` |
| Fixed-window group summary | Group-level comparisons (41 examples × 3 windows × 40 layers) | `analysis/fixed_window_group_summary.csv` |
| Normalized-progress per example | Per-example, per-layer, per-bin means | `analysis/normalized_progress_per_example.csv` |
| Normalized-progress group summary | Group-level bin comparisons | `analysis/normalized_progress_group_summary.csv` |
| Confound model dataset | 41-row modeling dataset | `analysis/confound_model_dataset.csv` |
| Confound model coefficients | 87-row coefficient table | `analysis/confound_model_coefficients.csv` |
| Confound model metrics | 18-row LOO metrics table | `analysis/confound_model_metrics.csv` |
| Confound models (full) | JSON with all model results, permutation, Spearman, LOGO | `analysis/confound_models.json` |
| Per-prompt trajectory summary | 42-row per-example Phase 6 summary | `analysis/per_prompt_trajectory_summary.csv` |
| Per-prompt layer summary | 294-row per-example per-layer statistics | `analysis/per_prompt_layer_summary.csv` |
| Canonical examples | 7 canonical examples with selection rules | `analysis/canonical_examples.json` |
| Plot index (per-prompt) | Markdown table linking 168 plots | `analysis/per_prompt_plot_index.md` |
| Goal behavioral summary | 4-row goal-level outcomes (Phase 7) | `analysis/goal_behavior_summary.csv` |
| Goal projection summary | 64-row goal × feature × outcome table | `analysis/goal_projection_summary.csv` |
| Goal normalized trajectories | 120-row goal × layer × bin table | `analysis/goal_normalized_trajectories.csv` |
| Iteration summary | 12-row iteration × goal comparison | `analysis/iteration_summary.csv` |
| Conversation stream summary | 6-row stream-level descriptives | `analysis/conversation_stream_summary.csv` |
| Trajectory type summary | 16-row predefined category table | `analysis/trajectory_type_summary.csv` |
| Goal/iteration manifest | Phase 7 provenance JSON | `analysis/goal_iteration_manifest.json` |
| Main plot directory | All analysis plots | `plots_analysis_v2/` |
| Per-prompt plot directory | 168 per-example trajectory plots | `plots_analysis_v2/per_prompt/` |
| Stage 4A2 causal validation | Intervention selection failure artifact | `outputs/stage4/qwen3-14b/refusal_direction/intervention_selection_metrics.json` |
| Engineering log | Full engineering history | `STAGE4_ENGINEERING_LOG.md` |

---

## 18. Selected Figures

The following plots are recommended as the primary figures for this sprint. Full paths are relative to the `outputs/stage4/token_dynamics/full_20260604_101929/plots_analysis_v2/` directory.

| # | Filename | Content |
|---|----------|---------|
| 1 | `fixed_window_layer22_group_comparison.png` | Layer-22 group means and distributions by outcome, three windows |
| 2 | `fixed_window_effect_by_layer.png` | Hedges' g by layer and window |
| 3 | `normalized_progress_layer22.png` | Layer-22 success and failure trajectories across 10 bins |
| 4 | `normalized_progress_effect_heatmap.png` | Hedges' g heatmap across all 40 layers and 10 bins |
| 5 | `confound_projection_adjusted_odds_ratio.png` | Model 2 adjusted OR with sensitivity checks |
| 6 | `confound_model_comparison.png` | LOO metrics for M0, M1, M2 |
| 7 | `confound_leave_one_goal_out.png` | LOGO OR estimates by excluded goal |
| 8 | `goal_success_rates.png` | SR success rate by goal with Wilson CIs |
| 9 | `goal_layer22_first500.png` | L22 first-500 projection by goal and outcome |
| 10 | `goal_normalized_layer22.png` | Goal-specific normalized trajectories |
| 11 | `confound_projection_vs_think_length.png` | Projection vs. log-think correlation |

No raw harmful prompt text or harmful output text appears in any figure.

---

*Document generated 2026-06-07. All numerical values verified against authoritative CSV/JSON artifacts. Random seed 42 confirmed in both `confound_model_manifest.json` and `confound_models.json`.*
