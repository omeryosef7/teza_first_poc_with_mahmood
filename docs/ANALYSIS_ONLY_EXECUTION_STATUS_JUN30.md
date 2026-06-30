# Analysis-Only Execution Status

**Generated:** 2026-06-30 19:56:43  
**Output directory:** `outputs/meeting/mahmood_analysis_only_jun30_20260630_193423/`  
**Working directory:** `/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood`  

---

## Explicit Integrity Confirmations

- [x] **No model weights loaded** — no Qwen3-14B, Gemma4-E4B-IT, or any other LLM instantiated
- [x] **No model inference run** — no forward passes, no generation, no embedding calls
- [x] **No GPU used** — all computation is CPU-only
- [x] **No external API called** — no OpenAI, Gemini, Anthropic, StrongREJECT, or any other API
- [x] **No existing result files modified** — all inputs read-only
- [x] **No SLURM jobs submitted** — analysis-only
- [x] **Condition G definition confirmed from code** — bare harmful + thinking OFF
- [x] **Factorial interaction formula confirmed from code** — `(p_A − p_E) − (p_D − p_G)`
- [x] **SR threshold confirmed from code** — `strongreject_score >= 0.5`

---

## Scripts Run

| Script | Primary output | Output exists? |
|--------|---------------|----------------|
| `src/step00_artifact_inventory.py` | `00_artifact_inventory.md` | YES |
| `src/step01_condition_definitions.py` | `01_condition_definitions.md` | YES |
| `src/analyze_puzzle_specific_categories.py` | `02_goal_condition_summary.csv` | YES |
| `src/analyze_factorial_design.py` | `08_factorial_per_goal.csv` | YES |
| `src/build_failure_review_packet.py` | `11_all_failures.csv` | YES |
| `src/compare_success_failure.py` | `16_within_prompt_success_failure.csv` | YES |
| `src/audit_refusal_direction_method.py` | `18_refusal_direction_method_audit.md` | YES |
| `src/compare_saved_directions.py` | `19_direction_cosine_matrix.csv` | YES |
| `src/generate_figures.py` | `fig_goal_condition_heatmap.png` | YES |
| `src/generate_meeting_report.py` | `MAHMOOD_ANALYSIS_ONLY_BRIEF.md` | YES |
| `src/generate_status_file.py` | `ANALYSIS_ONLY_EXECUTION_STATUS.md` | IN PROGRESS |

---

## Output File Inventory

| File | Status | Size/Rows |
|------|--------|-----------|
| `00_artifact_inventory.md` | EXISTS (8890 bytes) | |
| `01_condition_definitions.md` | EXISTS (5179 bytes) | |
| `02_goal_condition_summary.csv` | EXISTS (110 rows) | |
| `03_source_condition_summary.csv` | EXISTS (424 rows) | |
| `04_matched_seed_outcomes.csv` | EXISTS (82 rows) | |
| `05_pairwise_effects.csv` | EXISTS (22 rows) | |
| `06_goal_categories.csv` | EXISTS (22 rows) | |
| `07_source_categories.csv` | EXISTS (424 rows) | |
| `08_factorial_per_goal.csv` | EXISTS (22 rows) | |
| `09_factorial_per_source.csv` | EXISTS (424 rows) | |
| `10_factorial_validation.md` | EXISTS (2527 bytes) | |
| `11_all_failures.csv` | EXISTS (746 rows) | |
| `12_failure_mode_counts_by_goal.csv` | EXISTS (22 rows) | |
| `13_failure_mode_counts_by_condition.csv` | EXISTS (10 rows) | |
| `14_failure_mode_counts_by_model.csv` | EXISTS (2 rows) | |
| `15_manual_failure_review_packet.csv` | EXISTS (45 rows) | |
| `16_within_prompt_success_failure.csv` | EXISTS (26 rows) | |
| `17_within_prompt_summary.md` | EXISTS (2557 bytes) | |
| `18_refusal_direction_method_audit.md` | EXISTS (8013 bytes) | |
| `19_direction_cosine_matrix.csv` | EXISTS (72 rows) | |
| `20_direction_metadata.csv` | EXISTS (18 rows) | |
| `21_direction_similarity_summary.md` | EXISTS (7423 bytes) | |
| `fig_goal_condition_heatmap.png` | EXISTS (132KB) | |
| `fig_goal_condition_heatmap.csv` | EXISTS (110 rows) | |
| `fig_puzzle_gain_by_goal.png` | EXISTS (75KB) | |
| `fig_puzzle_gain_by_goal.csv` | EXISTS (22 rows) | |
| `fig_goal_category_counts.png` | EXISTS (72KB) | |
| `fig_goal_category_counts.csv` | EXISTS (9 rows) | |
| `fig_qwen_gemma_interaction.png` | EXISTS (60KB) | |
| `fig_qwen_gemma_interaction.csv` | EXISTS (2 rows) | |
| `fig_failure_modes.png` | EXISTS (63KB) | |
| `fig_failure_modes.csv` | EXISTS (30 rows) | |
| `fig_probe_vs_confound_baselines.png` | EXISTS (63KB) | |
| `fig_probe_vs_confound_baselines.csv` | EXISTS (2 rows) | |
| `fig_intervention_summary.png` | EXISTS (123KB) | |
| `fig_intervention_summary.csv` | MISSING | |
| `fig_direction_similarity_heatmap_qwen3-14b.png` | EXISTS (133KB) | |
| `fig_direction_similarity_heatmap_gemma4-e4b-it.png` | EXISTS (124KB) | |
| `MAHMOOD_ANALYSIS_ONLY_BRIEF.md` | EXISTS (16176 bytes) | |

---

## Missing Artifacts (Cannot Be Produced Without Inference)

| Missing artifact | Why needed | How to produce |
|-----------------|-----------|----------------|
| Canonical refusal direction for Qwen3-14B | Compare to DVP/behavioral directions | Run original pipeline on Qwen3-14B (GPU) |
| Canonical refusal direction for Gemma4-E4B-IT | Same | Same |
| Generation text for Condition A, goals 4–10 | Text-based failure analysis | Rerun Stage 4 for those goals (GPU) |
| Per-example projection files linked to factorial dataset | Direct join for paired analysis | Mapping step requires original generation order |
| Full StrongREJECT scores for P11 layer sweep | Removes keyword-scorer confound | API call (StrongREJECT) |

---

## Partial or Degraded Analyses

| Analysis | Limitation | Impact |
|---------|-----------|--------|
| Failure mode classification | No text for 70%+ of failures (main dataset has no text fields) | Most failures classified as 'no text available'; actual modes unknown |
| Within-prompt paired analysis | Per-example projection not joined to factorial dataset | Projection divergence result is incomplete |
| Direction cosine similarity | Some direction .pt files may be missing for specific variants | Heatmap may have gaps |
| E/G conditions for goals 4–10 Qwen3 | Stage4_8_extended has D/E/F not A | A vs E comparison limited to goals 0–3 for text analysis |

---

## Data Sources Used

| Source | Path | Used for |
|--------|------|---------|
| Factorial dataset | `outputs/stage4/factorial_attack_dataset.jsonl` | All main analyses |
| Hierarchical bootstrap | `outputs/stage4/factorial_balanced/goal_clustered_interaction_summary.json` | Interaction significance |
| LOGO probe AUC | `outputs/stage4/factorial_analysis/probe_transfer_auc.csv` | Direction analysis |
| Confound baselines | `outputs/stage4/factorial_analysis/confound_baseline_aucs.csv` | Direction analysis |
| Interaction effects | `outputs/stage4/factorial_analysis/interaction_effects.csv` | Source-level reference |
| Strict seed labels | `outputs/stage4/factorial_balanced/strict_seed_level_labels.csv` | Factorial validation |
| Intervention JSONL files | `outputs/stage4/intervention_judge_validation/*.jsonl` | P11/P14/P16/CoT figures |
| Direction tensors | `outputs/stage4/{model}/refusal_direction_*/direction.pt` | Direction similarity |
| Direction comparison CSV | `outputs/stage4/{model}/direction_comparison/cosine_similarity_by_layer.csv` | Direction similarity |
| Per-example JSONs (stage4_8) | `outputs/stage4_8/runs/*/per_example/*.json` | Failure mode text |
| Per-example JSONs (extended) | `outputs/stage4_8_extended/runs/*/per_example/*.json` | Failure mode text |

---

*End of status file. Generated by `generate_status_file.py`.*
