# Stage 4.5 — Artifact Manifest

**Created:** 2026-06-08  
**Status:** Implementation complete; annotation pending  
**Sprint plan:** [`docs/STAGE4_5_HARMFUL_INTERACTION_PLAN.md`](STAGE4_5_HARMFUL_INTERACTION_PLAN.md)

---

## Frozen Input Artifacts (read-only)

| Path | Description | Row/File Count |
|------|-------------|---------------|
| `outputs/stage4/token_dynamics/full_20260604_101929/` | Stage 4 run directory (read-only) | — |
| `outputs/stage4/token_dynamics/full_20260604_101929/per_example/` | Per-example JSONs | 42 JSONs |
| `outputs/stage4/token_dynamics/full_20260604_101929/analysis/analysis_dataset.csv` | Stage 4 analysis dataset | 42 rows, 32 cols |
| `outputs/stage6/all_traces_full/` | Stage 6 generation traces | 42 JSONs + batch_summary.json |

**Raw text is NOT present in any Stage 4.5 artifact.** Final answer text and think text remain
exclusively in the Stage 6 trace JSONs. Only SHA-256 hashes of final answer text are recorded
in `review/manual_adjudication_progress.csv`.

---

## Stage 4.5 Package Files

| File | Purpose | Lines (approx) |
|------|---------|---------------|
| `poc_stage4_5/__init__.py` | Package marker; `STAGE4_5_VERSION = "stage4_5_v1"` | 3 |
| `poc_stage4_5/common.py` | Shared constants, path utilities, loading helpers, CSV helpers | ~350 |
| `poc_stage4_5/build_manual_adjudication_queue.py` | Build 42-row human adjudication queue | ~120 |
| `poc_stage4_5/review_example.py` | Interactive human adjudication CLI | ~350 |
| `poc_stage4_5/build_event_annotation_queue.py` | Build 42-row event annotation queue | ~200 |
| `poc_stage4_5/annotate_harmful_interaction.py` | Interactive token annotation CLI | ~460 |
| `poc_stage4_5/analyze_harmful_interaction_aligned_dynamics.py` | Main statistical analysis | ~700 |
| `poc_stage4_5/plot_harmful_interaction_aligned_trajectories.py` | Per-example and aggregate plots | ~600 |
| `poc_stage4_5/align_prompt_spans.py` | Prompt-span token alignment | ~230 |
| `poc_stage4_5/capture_attention_pilot.py` | Attention capture stub (BLOCKED) | ~40 |
| `poc_stage4_5/analyze_attention_pilot.py` | Attention analysis stub (BLOCKED) | ~40 |
| `poc_stage4_5/report_annotation_progress.py` | Non-interactive progress report command | ~180 |
| `poc_stage4_5/tests/__init__.py` | Test package marker | 1 |
| `poc_stage4_5/tests/test_core.py` | Smoke tests (30 tests; all pass without GPU) | ~560 |

---

## Generated Review Files (persistent, repo root)

| File | Description | Status | Rows |
|------|-------------|--------|------|
| `review/manual_adjudication_queue.csv` | 42-row review queue with metadata | Created | 42 |
| `review/queue_manifest.json` | Queue status summary | Created | 1 |
| `review/event_annotation_queue.csv` | 42-row annotation queue | Created | 42 |
| `review/manual_adjudication_progress.csv` | Human label progress | Not yet created | 0 |
| `review/harmful_interaction_annotations.csv` | Token-onset annotations | Not yet created | 0 |

**`review/manual_adjudication_queue.csv` fields (19):**  
`example_id, goal_index, attack_iteration, conversation_id, strongreject_score, sr_success, judge_score, think_token_count, right_censored, usable_for_think_analysis, thinking_segmentation_status, human_label, human_success_strict, human_success_lenient, contains_harmful_interaction, stage6_trace_path, stage4_per_example_path, review_status, review_timestamp_utc`

**`review/manual_adjudication_progress.csv` fields (12):**  
`example_id, reviewer_id, review_timestamp_utc, human_label, reviewer_confidence, human_success_strict, human_success_lenient, contains_harmful_interaction, think_shows_hijack, reviewer_notes, response_sha256, review_status`

**`review/harmful_interaction_annotations.csv` fields (13):**  
Required: `example_id, annotation_timestamp_utc, harmful_interaction_start_token, annotation_confidence, interaction_phase, annotation_notes, annotator_id, annotation_status`  
Optional (empty for basic annotations): `harmful_interaction_end_token, final_answer_start_token, decision_or_commitment_candidate_token, right_censored, segmentation_complete`

---

## Analysis Outputs (timestamped run directory)

*Path pattern:* `outputs/stage4_5/harmful_interaction_alignment/run_<YYYYMMDD_HHMMSS>/`

| File | Description | Rows when complete |
|------|-------------|------------------|
| `analysis/harmful_interaction_annotation_audit.json` | Annotation validation summary | 1 object |
| `analysis/event_aligned_per_example.csv` | Per-example features (1 row/example/layer) | ≤ n_annotated × 7 |
| `analysis/event_aligned_group_summary.csv` | Group statistics (Hedges' g, MWU, etc.) | ≤ features × layers × subsets |
| `analysis/event_aligned_firth_coefficients.csv` | Firth model coefficients | ≤ 5 models × n_predictors |
| `analysis/event_aligned_analysis.json` | Full analysis summary (JSON) | 1 object |
| `analysis/leave_one_goal_out.csv` | LOGO sensitivity analysis | 4 rows |
| `analysis/stream_sensitivity.csv` | Stream (conversation) sensitivity analysis | ≤ 6 rows |
| `manifests/run_manifest.json` | Run provenance and input hashes | 1 object |

---

## Plot Files (timestamped run directory)

### Per-Example Plots (`plots/per_example/`, 4 per annotated example)

| Filename pattern | Description |
|-----------------|-------------|
| `<id>_full_with_event.png` | Full think-phase trajectory, all selected layers, event marker |
| `<id>_event_window.png` | Event-centered window [−500, +1000], Layer 22 emphasized |
| `<id>_layer_heatmap.png` | Layer × relative-position heatmap centered at onset |
| `<id>_outcome_comparison.png` | Pre/post comparison for this example's goal peers |

### Aggregate Plots (`plots/aggregate/`, 10 total)

| Filename | Description |
|----------|-------------|
| `layer22_aligned_by_sr_success.png` | Mean trajectory ± boot SEM by SR outcome |
| `layer22_aligned_by_judge_success.png` | Mean trajectory by Gemini outcome |
| `layer22_aligned_by_adjudicated_strict.png` | Mean trajectory by human strict label |
| `layer22_aligned_by_adjudicated_lenient.png` | Mean trajectory by human lenient label |
| `success_minus_failure_heatmap.png` | Difference heatmap across layers × relative position |
| `coverage_plot.png` | n examples contributing at each relative token position |
| `pre_event_vs_event_delta_scatter.png` | Pre-event projection vs. event delta scatter |
| `projection_vs_think_length.png` | Post-event projection vs. thinking length |
| `leave_one_goal_out_effect.png` | Effect size when each goal excluded |
| `stream_sensitivity_plot.png` | Effect size when each conversation excluded |

---

## Slurm Scripts

| File | Status | Notes |
|------|--------|-------|
| `slurm_scripts/stage4_5_attention_pilot.slurm` | Scaffold (do not submit) | Blocked on methodology audit |

---

## Documentation Files

| File | Status |
|------|--------|
| `docs/STAGE4_5_HARMFUL_INTERACTION_PLAN.md` | Complete |
| `docs/STAGE4_5_HARMFUL_INTERACTION_RESULTS.md` | Skeleton (fill after annotation) |
| `docs/STAGE4_5_MAHMOOD_MEETING_BRIEF.md` | Complete (fill numbers after annotation) |
| `docs/STAGE4_5_ARTIFACT_MANIFEST.md` | This file |
| `docs/STAGE4_5_ATTENTION_METHOD_AUDIT.md` | Complete (methodology questions answered; Q3/Q7/Q10 blocked on GPU) |

---

## Analysis Configuration

| Parameter | Value |
|-----------|-------|
| Primary layer | 22 |
| Selected layers | [13, 16, 22, 26, 30, 38, 39] |
| Exploratory layers | {13, 16, 38} |
| PRE window | [−500, −1] tokens relative to onset |
| POST_EARLY window | [0, +249] tokens |
| POST_LATE window | [+250, +999] tokens |
| Bootstrap resamples | 1000 |
| Permutation iterations | 10,000 |
| Random seed | 42 |
| Min annotations for model fitting | 5 |
| BH FDR threshold | 0.05 |
| Firth implementation | Pure NumPy/SciPy (reused from `poc_stage4.fit_confound_models`) |

---

## Exclusion Register

| example_id | Reason | Initial annotation status |
|-----------|--------|--------------------------|
| `goal_index=2\|attack_iteration=1\|conversation_id=5` | Not separable: `thinking_segmentation_status ≠ parsed_from_think_tags` | not_separable |

Note: `goal_index=2\|attack_iteration=1\|conversation_id=4` is **right-censored** (hit 32,768-token
limit) but IS separable (`thinking_segmentation_status == parsed_from_think_tags`).  It starts as
`pending` — annotators will attempt to locate the onset within the captured tokens, and may
explicitly record it as `right_censored` if no valid onset is found before the generation cutoff.

---

*Last updated: 2026-06-08*
