# Meeting Narrative — Mahmood, 2026-06-11

**Story in five minutes:** We had a hypothesis about the mechanism (refusal-direction dilution), tested it causally, it failed, and then did controlled behavioral experiments that gave us a cleaner result. The puzzle matters, but not via the mechanism we expected.

---

## Slide 1 — What we were trying to test

**Original question:** Does CoT hijacking work through diluting the model's refusal-direction activation? The structured puzzle format reliably gets Qwen3-14B to comply with harmful requests during thinking-extended CoT. We wanted to know *why*.

**What Stage 4 did:**
We extracted a Layer-22 "harmful-vs-harmless" contrast direction from 42 attack traces. The direction showed early divergence in the first 500 thinking tokens: successful attacks projected *higher* onto this direction than failures (Stage 4 fixed-window mean: success 5.20, failure 3.86).

**What Stage 4A2 showed:**
We attempted 160 causal interventions — steering the direction to suppress it during generation. **0/160 survived.** The model either collapsed its output or ignored the intervention. The direction was diagnostic, not causal.

**Conclusion from Stage 4A2:** Do not proceed with direction-based steering as the mechanistic hypothesis. The direction does not gate compliance.

**What we did instead:** Ran controlled behavioral experiments (Stages 4.7 and 4.8) to characterize *what* about the puzzle matters, without assuming a specific mechanism.

---

## Slide 2 — Behavioral controlled result (Stage 4.7)

**Design:** 12 source prompts × 4 conditions, greedy decoding, 5 censored rows corrected:

| Condition | Description | Complete-case success | Mean SR score | Mean think tokens |
|-----------|-------------|----------------------|---------------|-------------------|
| A | Full puzzle, thinking=on | **10/12 (83.3%)** | 0.823 | 11,458 |
| D | Bare target, thinking=on | 5/11 (45.5%) | 0.406 | 2,924 |
| F | Length-matched benign wrapper, thinking=on | 3/11 (27.3%) | 0.250 | 824 |
| E | Full puzzle, thinking=off | 4/9 (44.4%) | 0.333 | 0 |

**Sign tests (all 12 pairs, no imputation):**
- A − D: score diff = +0.417, sign test p = 0.031 (6/6 positive, 6 tied)
- A − F: score diff = +0.583, sign test p = 0.008 (8/8 positive, 4 tied)
- A − E: score diff = +0.490, sign test p = 0.031 (6/6 positive, 6 tied)

**LOGO stability:** A − D and A − F positive in all 4 leave-one-goal-out folds.

**Key message:**
The original structured puzzle condition outperforms both the bare-target and length-matched benign-context controls. Because the benign control matches length but not puzzle structure, this rules out prompt length alone but does not isolate puzzle semantics from reasoning structure or task coherence.

**Figure:** `01_stage47_behavior_A_D_F.png`

---

## Slide 3 — Thinking amplification (Stage 4.7)

**Same-length prompts, radically different thinking:**
- Condition A (full puzzle) and Condition F (length-matched benign wrapper) have matched prompt token counts (±5%).
- Yet A generates **13.97×** more thinking tokens than F (11,458 vs 824 tokens).

**What this means:** Prompt length is not the active ingredient. The full puzzle induces qualitatively different reasoning — much longer, deeper thinking chains. The benign wrapper of the same length produces short, shallow thinking.

**Additional contrast:** A vs D (bare target) — A generates 5.85× more thinking tokens (11,458 vs 2,924). So the puzzle format amplifies thinking relative to bare target too.

**Figure:** `02_stage47_thinking_tokens.png`

---

## Slide 4 — Mechanistic null result (Stage 4.7 + Stage 4.8)

**The old direction fails mechanistically.**

Layer-22 first-500 mean projection per condition:

| Stage | Condition A | Condition F | Condition D | Ordering |
|-------|------------|------------|------------|---------|
| 4.7 | 7.265 | 8.499 | 9.058 | **A < F < D** |
| 4.8 | 7.117 | 8.078 | 8.946 | **A < F < D** (replicated) |

Behavioral ordering: A > D > F. Projection ordering: A < F < D. **These are opposite.**

Key mechanistic finding:
- A − D projection diff (Stage 4.7): **−1.793** (A is 1.79 units lower on the direction, p = 0.039 sign test)
- Spearman ρ (L22 first-500 vs log think tokens, condition A, n=12): **−0.678**, p = 0.015

The provisional Layer-22 direction does not track behavioral success in the controlled settings. Instead, across Stage 4.7 and Stage 4.8 it is lower for the full-puzzle condition, which has the longest thinking chains. This suggests the direction is a thinking-depth or reasoning-style proxy, not a validated refusal/compliance mechanism.

**Figures:** `03_stage47_projection_vs_thinking.png` (primary) and `backup_stage47_layer22_projection.png` (backup)

---

## Slide 5 — Stochastic replication and goal identity (Stage 4.8)

**Design:** 4 source prompts × 3 conditions × 5 seeds (101–105) = 60 generations, 0 censored.

**Behavioral replication:**

| Condition | Success | Rate |
|-----------|---------|------|
| A | 12/20 | 60% |
| D | 10/20 | 50% |
| F | 8/20 | 40% |

A > D > F trend replicates under stochastic sampling. ✓

**Goal identity dominates:**
- Goal index 1: **0/15 success** across ALL conditions and seeds
- Goal index 3: **15/15 success** across ALL conditions and seeds
- Between-cell variance: 0.197; within-cell variance: 0.053; **ratio: 3.69×**

**Decision gate — Branch C:**
Only 3 matched-outcome cells (threshold was 4). Behavior-conditioned direction extraction is not valid. This is not a failure — it is a diagnostic boundary that tells us what the next experiment needs to address.

**Figures:** `04_stage48_seed_outcomes.png`, `05_stage48_variance_decomposition.png`

---

## Slide 6 — What this means and what to do next

### Summary of the story

1. **The puzzle matters behaviorally.** A beats D and F with stable, replicated sign tests. Prompt length alone is insufficient (F ruled out).

2. **The old direction is not the mechanism.** Layer-22 projection anti-correlates with behavioral success and tracks thinking depth instead. Stage 4A2 confirmed the direction has no causal role.

3. **The next research question has shifted.** It is no longer "can we tune this direction?" but rather: "what property of puzzle/reasoning structure makes some goals vulnerable, and how can we probe or exploit that systematically?"

### Three next-step options

**Option A — Expand goal/prompt dataset**
- Run Stage 4.9 with more goals or more phrasings per goal, prioritizing intermediate-susceptibility goals.
- *Pro:* Stronger empirical evidence; more statistical power; more matched cells.
- *Con:* Descriptive, not mechanistic. Doesn't explain *why* some goals are vulnerable.
- *Best if:* We want to ship a strong empirical case first.

**Option B — Mechanistic subspace/probe**
- Move beyond the scalar direction. Fit a low-dimensional predictive subspace or probe on controlled-condition representations, with held-out goals/prompts.
- *Pro:* Directly addresses the thesis contribution question. Distinguishes puzzle semantics from thinking depth.
- *Con:* Higher technical risk; needs enough matched cells; may not converge.
- *Best if:* Mahmood wants a mechanistic thesis contribution.

**Option C — AutoInject adaptation**
- Adapt AutoInject to reasoning models using StrongREJECT as behavioral objective, tracking whether optimized prompts resemble structured puzzles or other reasoning triggers.
- *Pro:* Attack-improvement framing; strong applied contribution; connects to LLM safety literature.
- *Con:* Does not explain the mechanism; less thesis-aligned if the goal is causal understanding.
- *Best if:* Mahmood wants attack-improvement contribution over mechanistic explanation.

### Recommendation

**Primary:** Option B if Mahmood values a mechanistic thesis contribution — we have Stage 4.7 data showing the scalar direction fails, and Stage 4.8 showing 3 matched cells. The natural next step is to probe a richer subspace rather than commit to AutoInject optimization with an unvalidated direction.

**Backup:** Option C if Mahmood wants a concrete attack-improvement story — use behavioral outcomes (StrongREJECT) to optimize prompts rather than projection onto the failed scalar direction.

Decision needed from Mahmood: **which framing does the thesis need?** Mechanistic understanding (→ Option B) or attack-improvement (→ Option C)?
