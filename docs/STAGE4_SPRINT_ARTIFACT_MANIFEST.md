# Stage 4 Token Dynamics — Sprint Artifact Freeze Manifest

**Freeze date:** 2026-06-07  
**Status:** Sprint complete. Artifacts are frozen. Do not move, rename, or delete listed files.  
**Model:** Qwen3-14B (`Qwen/Qwen3-14B`), `enable_thinking=True`

---

## Authoritative Run Directory

```
outputs/stage4/token_dynamics/full_20260604_101929/
```

Absolute path: `/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood/outputs/stage4/token_dynamics/full_20260604_101929/`

This directory is the sole authoritative source for all Stage 4 token-dynamics artifacts.  
**Total size: ~11 GB. Do not copy, move, or regenerate.**

Slurm jobs that produced this run: 476121 (initial batch), 490729 (completion batch).  
Engineering history: [`STAGE4_ENGINEERING_LOG.md`](../STAGE4_ENGINEERING_LOG.md) (do not modify).

---

## Per-Example Projection Artifacts

```
outputs/stage4/token_dynamics/full_20260604_101929/per_example/
```

- 42 JSON files, one per attack example.
- Each file contains token-level projection scalars for all 40 transformer layers (layers 0–39) across all generated tokens.
- Total: 578,759 think/final/special tokens; 24,461,040 token × layer projection rows.
- Naming convention: `goal_index=<G>|attack_iteration=<A>|conversation_id=<C>|target_model=gpt-o4-mini.json`
- All 42 files confirmed present and complete (0 token-count mismatches, 0 missing layers, 0 non-finite values).

---

## Authoritative Analysis Files

All files are in: `outputs/stage4/token_dynamics/full_20260604_101929/analysis/`

### Audit and data quality

| File | Description | Rows |
|------|-------------|------|
| `analysis_dataset.csv` | Master 42-row audit dataset; primary/secondary outcomes, token counts, segmentation status | 42 |
| `data_quality_report.json` | Machine-readable quality checks (token alignment, layer coverage, segmentation) | — |

### Fixed-window analysis (Phase 2)

| File | Description | Rows |
|------|-------------|------|
| `fixed_window_per_example.csv` | Per-example, per-layer, per-window mean projections | 42 × 40 × 3 = 5,040 |
| `fixed_window_group_summary.csv` | Group-level comparisons (Hedges' g, MWU p, permutation p, bootstrap CI) | 40 × 3 = 120 |
| `fixed_window_manifest.json` | Provenance: script version, parameters, random seed | — |

### Normalized-progress analysis (Phase 3)

| File | Description | Rows |
|------|-------------|------|
| `normalized_progress_per_example.csv` | Per-example, per-layer, per-bin (10 bins) mean projections | 41 × 40 × 10 = 16,400 |
| `normalized_progress_group_summary.csv` | Group-level bin comparisons (Hedges' g, BH q, bootstrap CI) | 40 × 10 = 400 |
| `normalized_progress_manifest.json` | Provenance: script version, parameters, random seed | — |

### Confound-controlled modeling (Phases 4–5)

| File | Description | Rows |
|------|-------------|------|
| `confound_model_dataset.csv` | 41-row modeling dataset (projection features + covariates) | 41 |
| `confound_model_coefficients.csv` | Coefficients for M0, M1, M2 and all sensitivity models | 87 |
| `confound_model_metrics.csv` | LOO log loss, Brier score, AUC for M0, M1, M2 | 18 |
| `confound_models.json` | Full model results, sensitivity analyses, permutation test, Spearman, LOGO | — |
| `confound_model_manifest.json` | Provenance: script version, parameters, `random_seed: 42` | — |

`random_seed: 42` confirmed present directly in `confound_models.json` (top-level key).

### Per-prompt trajectory analysis (Phase 6)

| File | Description | Rows |
|------|-------------|------|
| `per_prompt_trajectory_summary.csv` | Per-example summary statistics (think length, L22 means, segmentation) | 42 |
| `per_prompt_layer_summary.csv` | Per-example, per-layer statistics across think and final phases | 294 |
| `canonical_examples.json` | 7 canonical examples with selection rules (no harmful text) | 7 |
| `per_prompt_plot_index.md` | Markdown table linking all 168 per-prompt trajectory plots | — |
| `per_prompt_trajectory_manifest.json` | Provenance: script version, parameters, layers, random seed | — |

### Goal and iteration exploratory analysis (Phase 7)

| File | Description | Rows |
|------|-------------|------|
| `goal_behavior_summary.csv` | Goal-level outcome rates with Wilson CIs | 4 |
| `goal_projection_summary.csv` | Goal × feature × outcome (L22 first-500, Hedges' g, bootstrap CI) | 64 |
| `goal_normalized_trajectories.csv` | Goal × layer × bin normalized-progress comparisons | 120 |
| `iteration_summary.csv` | Iteration × goal outcome and projection descriptives | 12 |
| `conversation_stream_summary.csv` | Stream-level SR rates and L22 means | 6 |
| `trajectory_type_summary.csv` | Predefined trajectory-type categories | 16 |
| `goal_iteration_manifest.json` | Provenance: script version, parameters, random seed | — |

---

## Authoritative Plot Directory

```
outputs/stage4/token_dynamics/full_20260604_101929/plots_analysis_v2/
```

**Total plots: 22 analysis-level PNGs + 168 per-prompt PNGs = 190 total.**

### Analysis plots (22 files)

| File | Phase | Pre-specified? |
|------|-------|----------------|
| `fixed_window_layer22_group_comparison.png` | 2 | ✓ Pre-specified |
| `fixed_window_effect_by_layer.png` | 2 | ✓ Pre-specified |
| `fixed_window_mean_difference_by_layer.png` | 2 | ✓ Pre-specified |
| `fixed_window_sr_correlation_layer22.png` | 2 | ✓ Pre-specified |
| `normalized_progress_layer22.png` | 3 | ✓ Pre-specified |
| `normalized_progress_layer22_difference.png` | 3 | ✓ Pre-specified |
| `normalized_progress_effect_heatmap.png` | 3 | ✓ Pre-specified |
| `normalized_progress_mean_difference_heatmap.png` | 3 | ✓ Pre-specified |
| `normalized_progress_selected_layers.png` | 3 | ✓ Pre-specified |
| `earliest_divergence_by_layer.png` | 3 | ✓ Pre-specified |
| `confound_projection_adjusted_odds_ratio.png` | 4/5 | ✓ Pre-specified |
| `confound_model_comparison.png` | 4/5 | ✓ Pre-specified |
| `confound_leave_one_goal_out.png` | 4/5 | ✓ Pre-specified |
| `confound_partial_effect_projection.png` | 4/5 | ✓ Pre-specified |
| `confound_projection_vs_think_length.png` | 4/5 | ✓ Pre-specified |
| `goal_success_rates.png` | 7 | Exploratory |
| `goal_layer22_first500.png` | 7 | Exploratory |
| `goal_normalized_layer22.png` | 7 | Exploratory |
| `goal_selected_layer_effects.png` | 7 | Exploratory |
| `goal_think_length_by_outcome.png` | 7 | Exploratory |
| `iteration_behavior_projection.png` | 7 | Exploratory |
| `trajectory_type_outcomes.png` | 7 | Exploratory |

### Per-prompt plots (168 files)

Location: `plots_analysis_v2/per_prompt/`  
Format: 4 plots per example × 42 examples (full-generation, early-think zoom, late-think zoom, think-to-final transition).  
One not-separable example (Goal 2, iter 1, conv 5) has zoom and transition plots replaced with placeholder placeholders annotated "NOT SEPARABLE".  
Both right-censored examples (Goal 2, iter 1, conv 4 and conv 5) are annotated "RIGHT-CENSORED AT MAX_NEW_TOKENS".  
Index: `analysis/per_prompt_plot_index.md`

**All 190 plots confirmed present as of 2026-06-07.**

---

## Script Files

All scripts are in `poc_stage4/`. The following scripts were executed for this sprint (in order):

| Script | Phase | Purpose |
|--------|-------|---------|
| `audit_token_dynamics_dataset.py` | 1 | Dataset audit; produces `analysis_dataset.csv`, `data_quality_report.json` |
| `analyze_fixed_windows.py` | 2 | Fixed-window group comparison; primary confound control |
| `analyze_normalized_progress.py` | 3 | Per-bin normalized-progress analysis |
| `fit_confound_models.py` | 4/5 | Firth regression, sensitivity analyses, LOGO, permutation test |
| `plot_per_prompt_trajectories.py` | 6 | 168-plot per-example trajectory visualization |
| `analyze_goal_iteration_effects.py` | 7 | Exploratory goal- and iteration-level analysis |

Additional scripts in the module (data collection, direction extraction, Stage 4A2 causal validation) are documented in `STAGE4_ENGINEERING_LOG.md`.

---

## Documentation Files

| File | Description |
|------|-------------|
| `docs/STAGE4_CURRENT_SPRINT_PLAN.md` | Phase-by-phase implementation plan with corrected numerical tables |
| `docs/STAGE4_CURRENT_SPRINT_RESULTS.md` | Authoritative scientific results document (18 sections, all verified numbers) |
| `docs/STAGE4_MAHMOOD_MEETING_BRIEF.md` | One-page meeting brief with 5 key findings and recommended figures |
| `docs/STAGE4_SPRINT_ARTIFACT_MANIFEST.md` | This file |
| `STAGE4_ENGINEERING_LOG.md` | Historical engineering record — **do not modify** |

---

## Data Quality Status

| Check | Result |
|-------|--------|
| Expected example count | 42 |
| Stage 6 trace files found | 42 / 42 |
| Stage 4 projection files found | 42 / 42 |
| Token-count mismatches | 0 |
| Missing layers | 0 |
| Non-finite projection values | 0 |
| Duplicate example IDs | 0 |
| Think/final segmentation complete | 41 / 42 |
| Figure path validation (12 referenced figures) | 12 / 12 OK |
| Per-prompt PNGs | 168 / 168 OK |
| `random_seed: 42` in `confound_models.json` | ✓ Confirmed |

---

## Known Exclusions and Censoring

| Category | Example ID | Notes |
|----------|-----------|-------|
| Not-separable | `goal_index=2\|attack_iteration=1\|conversation_id=5` | `</think>` tag not found; all think-phase analyses exclude this example (n becomes 41). Think token count = 0. |
| Right-censored (parsed) | `goal_index=2\|attack_iteration=1\|conversation_id=4` | Hit 32,768-token limit; `</think>` found at token 19,428; think/final split possible. Retained in analyses; flagged in sensitivity A. |
| Right-censored (not-separable) | `goal_index=2\|attack_iteration=1\|conversation_id=5` | Hit 32,768-token limit AND not separable. Excluded from all think-phase analyses. |

Both right-censored examples are Goal 2, iteration 1 — the same goal and iteration. This is a concentration of data-quality issues in one goal/iteration subgroup that should be noted when interpreting Goal 2 results.

---

## Stage 4A2 Causal Validation Status

| Metric | Value |
|--------|-------|
| Selection status | `intervention_selection_failed_no_survivors` |
| Candidates evaluated | 160 (4 prompt positions × 40 layers) |
| Candidates surviving all filters | **0** |
| Failure: steering below threshold | 160 / 160 |
| Failure: KL divergence above threshold | 92 / 160 |
| Failure: layer pruned | 32 / 160 |
| Best ablation steering score | −17.10 (far below required threshold) |
| Recommendation from Stage 4A2 | "Do not run Stage 4B scientifically from this direction" |
| Consequence for this sprint | All findings are **associative only**. No causal claims. |

Artifact: `outputs/stage4/qwen3-14b/refusal_direction/intervention_selection_metrics.json`

---

## Package Versions (conda env `poc_stage2`)

| Package | Version |
|---------|---------|
| Python | 3.12.13 |
| NumPy | 2.4.6 |
| SciPy | 1.17.1 |
| Matplotlib | 3.9.0 |
| Pandas | 2.3.1 |
| statsmodels | **not available** |
| scikit-learn | **not available** |

Full Python path: `/home/sharifm/students/omeryosef/miniconda3/envs/poc_stage2/bin/python3`

All statistical methods (Firth penalized logistic regression, Wilson score CI, bootstrap CI, Hedges' g, BH correction, permutation test) were implemented from scratch using NumPy and SciPy only.

---

## What Is NOT in This Manifest

The following are **not** part of the frozen sprint artifacts and should not be referenced as authoritative:

- Any outputs from previous, failed, or partial Stage 4 runs (other run timestamps under `outputs/stage4/token_dynamics/`).
- Stage 2B labels (`qwen_run_success_raw`) — these are not the primary outcome.
- Slurm job logs (contain intermediate state).
- Any per-example outputs from the Stage 4A2 intervention pipeline (not frozen here; see engineering log).

---

*Manifest generated 2026-06-07. This document is a reference pointer only — it does not move or copy the 11 GB artifact tree.*
