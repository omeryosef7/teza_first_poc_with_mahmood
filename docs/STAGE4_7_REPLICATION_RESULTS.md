# Stage 4.7 — Multi-Prompt Replication Results

**Status:** PENDING — awaiting GPU generation  
**Date:** 2026-06-10  
**Author:** Omer Yosef (PLUS group, TAU)

---

> **NOTE:** This document is a skeleton. Populate after GPU runs complete and `analyze_replication.py` + `plot_replication.py` have been executed.

---

## Generation Status

| SLURM Job | Type | Status | Rows |
|-----------|------|--------|------|
| smoke | 1 prompt × A/D/F | PENDING | — |
| array | 4 goals × 12 prompts × 4 conds | PENDING | — |

When complete, populate:
- Run directory: `outputs/stage4_7/runs/<run_timestamp>/`
- Analysis: `outputs/stage4_7/runs/<run_timestamp>/analysis/`
- Figures: `outputs/stage4_7/runs/<run_timestamp>/plots/`

---

## Summary Table (populate after generation)

| Condition | n | n_success | SR success rate | Mean SR score | 95% CI |
|-----------|---|-----------|-----------------|---------------|--------|
| A: Full puzzle, thinking=on | 12 | — | — | — | — |
| D: No puzzle, thinking=on | 12 | — | — | — | — |
| F: Benign wrapper, thinking=on | 12 | — | — | — | — |
| E: Full puzzle, thinking=off | 12 | — | — | — | — |

Bootstrap 95% CIs from n_boot=2000, seed=42, resampling source prompts.

---

## Paired Contrasts (populate after generation)

### A vs D (puzzle semantics vs. bare target/cue)

| Source Prompt | Stratum | A score | D score | Diff (A−D) | A success | D success |
|---------------|---------|---------|---------|------------|-----------|-----------|
| (goal 0, lower) | lower | — | — | — | — | — |
| ... | | | | | | |

Mean diff: —  
Bootstrap 95% CI: [—, —]  
Sign test: —  
McNemar: —

### A vs F (puzzle semantics vs. length-matched benign wrapper)

_(same structure as above)_

### D vs F (bare target vs. benign wrapper, both length < A)

_(same structure as above)_

### A vs E (thinking=on vs. thinking=off)

_(same structure as above)_

---

## Per-Goal Breakdown (populate after generation)

| Goal | A success | D success | F success | E success |
|------|-----------|-----------|-----------|-----------|
| 0 | — | — | — | — |
| 1 | — | — | — | — |
| 2 | — | — | — | — |
| 3 | — | — | — | — |

---

## Thinking Token Counts (populate after generation)

| Condition | Mean think tokens | Median | Min | Max |
|-----------|-------------------|--------|-----|-----|
| A | — | — | — | — |
| D | — | — | — | — |
| F | — | — | — | — |
| E | 0 (thinking=off) | 0 | 0 | 0 |

---

## Layer 22 Projection Analysis — DIAGNOSTIC ONLY

**Important:** The Layer 22 direction is provisional. Results below are diagnostic and must not be interpreted as evidence of causal refusal suppression. `direction_status = "provisional_projection_diagnostic_only"`.

| Metric | A | D | F |
|--------|---|---|---|
| First 500 tokens mean proj | — | — | — |
| Think-phase mean proj | — | — | — |
| Last 500 think tokens proj | — | — | — |

---

## Figures

See `outputs/stage4_7/runs/<run_timestamp>/plots/`:

| Figure | File | Status |
|--------|------|--------|
| 1. Behavior by condition | `fig1_behavior_by_condition.png` | PENDING |
| 2. Thinking length | `fig2_thinking_length_by_condition.png` | PENDING |
| 3. A vs D vs F | `fig3_full_vs_bare_vs_length_matched.png` | PENDING |
| 4. Thinking on vs off | `fig4_thinking_on_vs_off.png` | PENDING |
| 5. L22 early projection | `fig5_layer22_early_projection.png` | PENDING |
| 6. L22 normalized trajectory | `fig6_layer22_normalized_trajectory.png` | PENDING |
| 7. Per-goal heatmap | `fig7_per_goal_condition_heatmap.png` | PENDING |
| 8. Projection vs think length | `fig8_projection_vs_thinking_length.png` | PENDING |
| 9. Finish reason | `fig9_finish_reason_and_truncation.png` | PENDING |

---

## Interpretation (populate after analysis)

### H1: Puzzle semantics drive success (A ≫ F)

_Populate after analysis._

### H2: Length alone sufficient (A ≈ F)

_Populate after analysis._

### H3: Thinking necessary (A ≫ E)

_Populate after analysis._

### H4: Target/cue sufficient (D ≈ A)

_Pre-existing evidence from Stage 4.6: D and A both 4/4 (n=1 prompt per goal)._  
Stage 4.7 replicates across n=3 prompts per goal: _populate after analysis._

---

## Limitations

1. n=3 source prompts per goal limits statistical power; sign tests underpowered for detecting small effects
2. Layer 22 direction is provisional (not validated by causal intervention)
3. Condition F filler items are concatenated instruction prompts — may not match puzzle length at the sub-token level
4. StrongREJECT judge skipped for Gemini (spending cap); using automated SR scorer only
5. Condition E truncation (if any): generation budget may not be sufficient for all prompts

---

## Post-generation commands

```bash
# After array job completes:

# 1. Run analysis
python -m poc_stage4_7.analyze_replication \
    --run-dir outputs/stage4_7/runs/<run_timestamp>

# 2. Run projection analysis (GPU)
python -m poc_stage4_7.compute_selected_layer_dynamics \
    --run-dir outputs/stage4_7/runs/<run_timestamp>

# 3. Re-run analysis with mechanistic data
python -m poc_stage4_7.analyze_replication \
    --run-dir outputs/stage4_7/runs/<run_timestamp>

# 4. Generate figures
python -m poc_stage4_7.plot_replication \
    --run-dir outputs/stage4_7/runs/<run_timestamp>
```
