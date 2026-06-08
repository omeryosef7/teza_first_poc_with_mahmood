# Stage 4.5 — Human-Grounded Harmful-Interaction-Aligned Token Dynamics
## Results

**Model:** Qwen3-14B (`Qwen/Qwen3-14B`), `enable_thinking=True`  
**Dataset:** 42 Stage 6 attack generations (4 harmful goals, gpt-o4-mini target)  
**Stage 4 run path:** `outputs/stage4/token_dynamics/full_20260604_101929/`  
**Primary outcome priority:** adjudicated_strict → adjudicated_lenient → sr_success → judge_success  
**Status:** SKELETON — awaiting human annotation and analysis run

> **Scientific analysis pending completion of manual adjudication and harmful-interaction annotation.**
> Infrastructure is complete; human behavioral adjudication: 0/42 examples reviewed;
> harmful-interaction event annotation: 0/42 examples annotated; event-aligned statistical
> analysis: not yet run.  Attention-weight pilot: BLOCKED pending method verification.  

---

## 1. Completed Facts (from Stage 4 frozen run)

These facts are not subject to change by Stage 4.5 analysis:

- **42** per-example JSONs; **41** separable; **2** right-censored; **19** SR/Gemini disagreements
- **578,759** think/final/special tokens; **24,461,040** token × layer rows
- SR success (score ≥ 0.5): **19/42** examples
- Gemini success (judge = 10): **4/42** examples
- SR-positive/Gemini-negative: **17** examples
- Layer-22 Stage 4 effect (first 500 think tokens): Hedges' g = 1.256, MWU p = 0.0016
- Firth OR (Model 2, n=41): 4.00 [95% CI 1.06–15.03], permutation p = 0.033
- Stage 4A2 causal validation: **0/160 candidates survived**

---

## 2. Pending: Human Adjudication

**Status:** `manual_adjudication_progress.csv` — 0/42 examples reviewed as of 2026-06-08.

*To fill after review is complete:*

### 2a. Label Distribution

| Human Label | Count |
|------------|-------|
| full_refusal | — |
| partial_refusal_with_unsafe_leakage | — |
| irrelevant_or_nonresponsive | — |
| superficial_harmful_mention | — |
| substantive_compliance | — |
| highly_actionable_compliance | — |
| truncated_or_invalid | — |
| uncertain | — |
| **Total** | 42 |

### 2b. Evaluator Agreement (after review)

| Comparison | Agreement Rate | Cohen's κ |
|-----------|---------------|----------|
| Human strict vs. SR | — | — |
| Human strict vs. Gemini | — | — |
| Human lenient vs. SR | — | — |

### 2c. Outcome Counts

| Outcome | n (True) | n (False) | n (uncertain/excluded) |
|---------|---------|---------|----------------------|
| human_success_strict | — | — | — |
| human_success_lenient | — | — | — |
| sr_success | 19 | 23 | 0 |
| judge_success | 4 | 38 | 0 |

---

## 3. Pending: Event Annotation

**Status:** `harmful_interaction_annotations.csv` — 0 annotations as of 2026-06-08.

*To fill after annotation is complete:*

### 3a. Annotation Outcome

| Status | Count |
|--------|-------|
| annotated (think-phase onset) | — |
| annotated (final-phase onset) | — |
| no_harmful_interaction_found | — |
| not_separable | 1 |
| right_censored | 1 |
| uncertain | — |
| **Total** | 42 |

### 3b. Onset Position Distribution (annotated subset)

- Median relative onset (tokens before end of think): —
- Range: —
- High-confidence annotations: —

---

## 4. Pending: Event-Aligned Projection Analysis

**Status:** Not yet run (insufficient annotations).

*To fill after analysis:*

### 4a. Primary Result (Layer 22, think-phase events)

**Research question:** Does the provisional direction projection *change* at the harmful-interaction onset, or is the Stage 4 effect already present before the onset?

*Conclusion will be one of:*
- **A.** Effect is pre-existing: pre-event projection is already higher in successful examples; no additional change at onset
- **B.** Effect emerges at onset: post-event projection diverges; pre-event projection is similar between groups
- **C.** Results differ by outcome definition: consistent under one label scheme but not another
- **D.** Evidence is inconclusive: confidence intervals overlap substantially under all labels

**Conclusion: PENDING**

### 4b. Key Group Statistics (Layer 22, post-event early mean, primary analysis)

| Statistic | Value |
|-----------|-------|
| n success | — |
| n failure | — |
| Hedges' g | — |
| MWU p | — |
| Permutation p | — |
| Bootstrap 95% CI | — |
| BH q-value | — |

### 4c. Firth Model Results

| Model | Predictor | OR | 95% CI | p |
|-------|-----------|-----|--------|---|
| M1_pre_event | pre_event_mean_z | — | — | — |
| M2_post_event | post_event_early_z | — | — | — |
| M3_post_event_adj | post_event_early_z | — | — | — |
| M4_delta | event_delta_early_z | — | — | — |

---

## 5. Exploratory Findings

*To fill: Layers 13, 16, 38 (marked post-hoc/exploratory in all output CSVs).*

---

## 6. Attention Pilot Status

**Status:** BLOCKED. See [`docs/STAGE4_5_ATTENTION_METHOD_AUDIT.md`](STAGE4_5_ATTENTION_METHOD_AUDIT.md).

No attention weights have been captured. The `capture_attention_pilot.py` stub will not be
executed until methodology questions Q3, Q7, and Q10 are answered and a memory estimate is
verified.

---

## 7. Limitations

1. **Same 42 examples as Stage 4.** Event-aligned analysis is performed on the same dataset used to motivate this stage; no independent validation set.
2. **Single annotator.** All human labels and onset annotations are from a single reviewer. Inter-rater reliability is not assessed.
3. **n = 41 pending annotation** (after excluding 1 not-separable example). The 1 right-censored-but-separable example is included in the annotation queue; annotators decide whether a valid onset is captured. With 4 harmful goals this is still under-powered for goal-stratified analysis.
4. **Provisional direction not causally validated.** Projections onto this direction are diagnostic features only (Stage 4A2: 0/160 candidates survived).
5. **Non-randomized design.** The 42 examples span 4 goals × up to 2 iterations × 6 conversation streams. Stream identity is partially confounded with goal and iteration history.

---

## 8. Recommended Next Sprint

*To fill based on which conclusion (A/B/C/D) is reached.*

| Conclusion | Recommended next experiment |
|-----------|----------------------------|
| A: Pre-existing | Repeated generations per prompt to isolate prompt-level vs. generation-level variance |
| B: Change at onset | Targeted causal intervention at the event token (activation patching) |
| C: Label-dependent | Repair evaluator definitions; collect independent ground truth |
| D: Inconclusive | More examples per goal; consider hierarchical model |

---

*Last updated: 2026-06-08 (skeleton)*
