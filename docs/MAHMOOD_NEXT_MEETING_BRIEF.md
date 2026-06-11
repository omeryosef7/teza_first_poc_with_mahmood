# Next Meeting Brief — Mahmood

**Prepared:** 2026-06-11
**Stage:** 4.7 COMPLETE (all 11 figures); 4.8 COMPLETE (60 gens + projections + figures)
**All GPU jobs finished.**

---

## Five-Part Story

### 1. Early associative divergence (Stage 4 — frozen)

In 42 Qwen3-14B attack examples, the layer-22 residual stream diverges from a "harmless" direction within the first 500 thinking tokens. The effect is present and consistent, but the direction is **provisional** — it was computed from a harmful-vs-harmless contrast, not from generation-level behavioral outcomes.

### 2. Causal validation failed (Stage 4A2)

We attempted to suppress the divergence via activation patching. 0/160 patched examples produced a refusal. The direction is **diagnostic, not causal** — it tracks something associated with the attack but we cannot steer the model by patching it.

### 3. Puzzle outperforms controls across 12 source prompts (Stage 4.7 — behavioral)

Multi-prompt replication across 12 source prompts × 4 conditions (A = full puzzle + thinking; D = bare target + thinking; F = length-matched benign + thinking; E = full puzzle + no thinking):

| Condition | Success / Complete | Mean SR score | Mean think tokens |
|-----------|-------------------|---------------|------------------|
| A: Full puzzle, thinking=on | 10/11† | 0.823 | 11,458 |
| D: No puzzle, thinking=on | 5/11† | 0.385 | 2,924 |
| F: Benign wrapper, thinking=on | 3/11† | 0.250 | 824 |
| E: Full puzzle, thinking=off | 4/9† | 0.333 | 0 |

†Complete-case (5 censored rows excluded). All sign tests pass at p < 0.05 (A−D, A−F, A−E).
A−D and A−F stable across all 4 goal subsets (leave-one-goal-out sensitivity: 4/4 folds positive).

**Length-matched control:** A and F have matched prompt length (±5%), yet A succeeds at 10/11 vs F at 3/11. Rules out prompt length as sole driver; does not distinguish puzzle semantics from reasoning structure.

**Thinking amplification:** A generates ~13.9× more thinking tokens than F despite identical total length.

### 4. Projection dynamics: mechanistic null (Stage 4.7 + Stage 4.8 — REPLICATED)

**Stage 4.7 (12 source prompts × greedy decoding):**

| Contrast | Mean diff (L22 first-500) | Signs (+/−) | Sign p |
|---------|--------------------------|-------------|--------|
| A − D | **−1.79** | 2/10 | **0.039** |
| A − F | −1.23 | 3/9 | 0.146 |

A has significantly *lower* L22 projection than D — opposite of behavioral ordering.
Direction anti-correlates with log(think_tokens) (ρ = −0.68, p = 0.015).

**Stage 4.8 (4 source prompts × 5 stochastic seeds — COMPLETE, independent replication):**

| Condition | L22 mean (first 500) | Mean think tokens | SR success |
|-----------|----------------------|-------------------|------------|
| A | **7.117** | 14,133 | 12/20 (60%) |
| F | 8.078 | 1,426 | 8/20 (40%) |
| D | **8.946** | 2,529 | 10/20 (50%) |

Same ordering: A < F < D on projection; A > D > F on behavioral success.
**This is a pre-registered replication of the Stage 4.7 mechanistic null under independent stochastic sampling.**

**Interpretation:** The provisional direction captures thinking depth, not behavioral compliance. Longer, deeper thinking (A) produces *lower* projection. The Stage 4 early divergence does not transfer to predicting within-condition success.

### 5. Within-prompt stochastic variability (Stage 4.8 — COMPLETE)

60 stochastic generations: 4 source prompts × 3 conditions × 5 seeds (101–105).

**Behavioral findings:**

| Condition | Success | Rate |
|-----------|---------|------|
| A | 12/20 | 60% |
| D | 10/20 | 50% |
| F | 8/20 | 40% |

**Dominant factor is goal identity, not seed or condition:**
- Goal 1: 0/15 success across ALL conditions and seeds (even A with 16,515 mean think tokens)
- Goal 3: 15/15 success across ALL conditions and seeds
- Goals 0 and 2: intermediate, condition-dependent

**Variance decomposition:**
- Between-cell variance (prompt × condition): 0.197
- Within-cell variance (seed randomness): 0.053
- Ratio: 3.7× — prompt identity + condition dominate over stochastic variation

**Matched outcome cells (same prompt, same condition, some seeds succeed, some fail):**
3 cells qualified (goal=0/A: 4/1; goal=2/A: 3/2; goal=2/F: 3/2).

This is below the pre-registered threshold of ≥4 for behavior-conditioned direction extraction (Branch C). Direction extraction skipped. To obtain ≥4 matched cells in future: target goals with 40–60% success rates or run more seeds (10–20 per cell).

---

## Strongest Figures for Meeting

**Stage 4.7 (behavioral + mechanistic):**

1. `outputs/stage4_7/runs/run_array_20260610_1442/plots/fig3_full_vs_bare_vs_length_matched.png`
   A vs D vs F paired behavioral — puzzle outperforms both controls.

2. `outputs/stage4_7/runs/run_array_20260610_1442/plots/fig2_thinking_length_by_condition.png`
   Thinking amplification: A generates 13.9× more tokens than F.

3. `outputs/stage4_7/runs/run_array_20260610_1442/plots/fig5_layer22_early_projection.png`
   L22 by condition: A < D on projection (mechanistic null).

4. `outputs/stage4_7/runs/run_array_20260610_1442/plots/fig8_projection_vs_thinking_length.png`
   Direction = thinking-depth proxy (not success proxy). Motivates Stage 4.8.

**Stage 4.8 (new):**

5. `outputs/stage4_8/runs/run_array_20260611_0109/plots/fig1_seed_outcomes_by_cell.png`
   Heatmap: goal identity dominates outcome variance across seeds.

6. `outputs/stage4_8/runs/run_array_20260611_0109/plots/fig3_condition_effects_with_prompt_fixed_effects.png`
   A > D > F confirmed under stochastic sampling.

7. `outputs/stage4_8/runs/run_array_20260611_0109/plots/fig2_within_vs_between_prompt_variability.png`
   Variance decomposition: between-cell 3.7× within-cell.

---

## What Has Changed Since Last Meeting

| Previous state | Current state |
|---------------|---------------|
| Stage 4.7 GPU running | ✅ Complete — 48 gens, all 11 figures, behavioral + mechanistic |
| No censoring treatment | ✅ Complete-case primary analysis (5 censored rows excluded) |
| No LOGO sensitivity | ✅ A>D and A>F stable in all 4 goal folds |
| No mechanistic data | ✅ A < D on L22 projection (p=0.039); direction = thinking proxy |
| Stage 4.8 not started | ✅ Complete — 60 gens, audit passed, projections computed, figures generated |
| Behavior-conditioned direction pending | ✅ Branch C: 3 matched cells, direction extraction skipped |
| L22 null result from Stage 4.7 | ✅ **Replicated** in Stage 4.8 under stochastic sampling (A=7.1 < D=8.9) |

---

## Open Questions for Meeting

1. **Goal identity as dominant factor:** Goals 1 and 3 are deterministic across conditions. What distinguishes these goals from goals 0 and 2? Is this about the specific target or the phrasing?

2. **Direction extraction path forward:** With only 3 matched cells, a behavior-conditioned direction needs either more seeds per cell or different source prompts that produce intermediate success rates. Is this worth pursuing?

3. **Double null result:** The provisional direction doesn't causally suppress refusal (Stage 4A2) AND it doesn't track behavioral success within controlled conditions (Stage 4.7/4.8). What does it actually encode?

4. **Next stage direction:** Expand to more goals/models? Move to a different mechanistic hypothesis? Design an intervention study with better source material?

---

## Limitations

1. **StrongREJECT is the sole behavioral evaluator** — Gemini judge unavailable
2. **n=12 source prompts** — sign tests limited; p=0.031 is minimum achievable at n=12
3. **5 censored Stage 4.7 rows** — complete-case used; corrective rerun confirmed 3 genuine infinite loopers
4. **No causal claim** — all findings are observational
5. **Stage 4.8 matched cells = 3** — insufficient for LOO direction extraction; goal identity dominates
6. **Projection direction is diagnostic only** — no steering confirmed (Stage 4A2 failed)
