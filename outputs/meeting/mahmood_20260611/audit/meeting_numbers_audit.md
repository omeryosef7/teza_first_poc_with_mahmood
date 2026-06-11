# Meeting Numbers Audit Report

**Date:** 2026-06-11  
**Summary:** 73 PASS / 0 FAIL / 1 SKIP / 3 INFO

## Checks

| Status | Check | Actual | Expected |
|--------|-------|--------|----------|
| PASS | frozen_token_dynamics_manifest | `True` | `True` |
| PASS | refusal_direction_pt | `True` | `True` |
| PASS | frozen_manifest_readable | `True` | `True` |
| PASS | stage4_n_examples_attempted_42 | `42` | `42` |
| SKIP | stage4a2_causal_survivors | — | — |
| | *['artifact_version', 'stage', 'timestamp_utc', 'selection_status', 'selection_criterion', 'model_name', 'enable_thinking', 'input_dir', 'output_dir', 'stage4a1_candidate_directions_path']* | | |
| PASS | stage47_condition_summary_csv | `True` | `True` |
| PASS | stage47_total_rows_48 | `48` | `48` |
| PASS | stage47_n_source_prompts_12 | `12` | `12` |
| PASS | stage47_A_n_censored_0 | `0` | `0` |
| PASS | stage47_D_n_censored_1 | `1` | `1` |
| PASS | stage47_F_n_censored_1 | `1` | `1` |
| PASS | stage47_E_n_censored_3 | `3` | `3` |
| PASS | stage47_A_cc_n_12 | `12` | `12` |
| PASS | stage47_D_cc_n_11 | `11` | `11` |
| PASS | stage47_F_cc_n_11 | `11` | `11` |
| PASS | stage47_E_cc_n_9 | `9` | `9` |
| PASS | stage47_A_cc_success_10 | `10` | `10` |
| PASS | stage47_D_cc_success_5 | `5` | `5` |
| PASS | stage47_F_cc_success_3 | `3` | `3` |
| PASS | stage47_E_cc_success_4 | `4` | `4` |
| PASS | stage47_A_cc_rate_0833 | `0.8333333333333334` | `0.8333` |
| PASS | stage47_D_cc_rate_0455 | `0.45454545454545453` | `0.4545` |
| PASS | stage47_F_cc_rate_0273 | `0.2727272727272727` | `0.2727` |
| PASS | stage47_E_cc_rate_0444 | `0.4444444444444444` | `0.4444` |
| INFO | stage47_A_rate_docs_discrepancy | — | — |
| | *NOTE: some docs claim A=10/11 (91%) but artifact shows A=10/12 (83.3%, 0 censored). Corrective rerun eliminated A's censored row. Docs should be updated.* | | |
| PASS | stage47_A_mean_think_11458 | `11457.916666666666` | `11458.0` |
| PASS | stage47_D_mean_think_2924 | `2924.3333333333335` | `2924.0` |
| PASS | stage47_F_mean_think_824 | `824.0` | `824.0` |
| PASS | stage47_sign_tests_json | `True` | `True` |
| PASS | stage47_AD_sign_p_0031 | `0.03125` | `0.03125` |
| PASS | stage47_AF_sign_p_0008 | `0.0078125` | `0.0078125` |
| PASS | stage47_AF_mcnemar_p_0016 | `0.015625` | `0.015625` |
| PASS | stage47_AE_sign_p_0031 | `0.03125` | `0.03125` |
| INFO | stage47_AF_pvalue_test_note | — | — |
| | *NOTE: A-F p reported as ~0.016 in docs = McNemar exact (0.01563). Sign test p = 0.00781. These are different tests.* | | |
| PASS | stage47_paired_contrasts_csv | `True` | `True` |
| PASS | stage47_AD_score_diff_0417 | `0.4166666666666667` | `0.4167` |
| PASS | stage47_AF_score_diff_0583 | `0.5833333333333334` | `0.5833` |
| PASS | stage47_AE_score_diff_0490 | `0.4895833333333333` | `0.4896` |
| INFO | stage47_score_diff_docs_discrepancy | — | — |
| | *NOTE: some docs report A-D diff=0.438 and A-F diff=0.573. Artifacts show A-D=0.4167, A-F=0.5833 (all 12 pairs including legacy). Docs may have used an earlier or different analysis pass.* | | |
| PASS | stage47_AF_think_ratio_1397 | `13.966578826057935` | `13.97` |
| PASS | stage47_logo_json | `True` | `True` |
| PASS | stage47_AD_logo_always_positive | `True` | `True` |
| PASS | stage47_AF_logo_always_positive | `True` | `True` |
| PASS | stage47_AD_logo_n_folds_4 | `4` | `4` |
| PASS | stage47_mechanistic_summary_csv | `True` | `True` |
| PASS | stage47_A_L22_first500_mean_727 | `7.2648076159457355` | `7.26` |
| PASS | stage47_D_L22_first500_mean_906 | `9.057476881364982` | `9.06` |
| PASS | stage47_F_L22_first500_mean_850 | `8.499280427038672` | `8.5` |
| PASS | stage47_mechanistic_contrasts_csv | `True` | `True` |
| PASS | stage47_AD_L22_diff_neg179 | `-1.7926692654192447` | `-1.793` |
| PASS | stage47_L22_spearman_rho_neg068 | `-0.6783216783216784` | `-0.678` |
| PASS | stage47_L22_spearman_condA_neg068 | `-0.6783216783216783` | `-0.678` |
| PASS | stage48_condition_summary_csv | `True` | `True` |
| PASS | stage48_total_rows_60 | `60` | `60` |
| PASS | stage48_total_censored_0 | `0` | `0` |
| PASS | stage48_A_success_12 | `12` | `12` |
| PASS | stage48_D_success_10 | `10` | `10` |
| PASS | stage48_F_success_8 | `8` | `8` |
| PASS | stage48_A_rate_060 | `0.6` | `0.6` |
| PASS | stage48_D_rate_050 | `0.5` | `0.5` |
| PASS | stage48_F_rate_040 | `0.4` | `0.4` |
| PASS | stage48_analysis_summary_json | `True` | `True` |
| PASS | stage48_n_cells_12 | `12` | `12` |
| PASS | stage48_matched_cells_3 | `3` | `3` |
| PASS | stage48_variance_decomp_json | `True` | `True` |
| PASS | stage48_within_cell_var_0053 | `0.053333333333333344` | `0.0533` |
| PASS | stage48_between_cell_var_0197 | `0.19666666666666668` | `0.1967` |
| PASS | stage48_variance_ratio_369 | `3.6874999999999996` | `3.69` |
| PASS | stage48_cell_summary_csv | `True` | `True` |
| PASS | stage48_goal1_total_success_0 | `0` | `0` |
| PASS | stage48_goal3_total_success_15 | `15` | `15` |
| PASS | stage48_projection_summary_jsonl | `True` | `True` |
| PASS | stage48_A_L22_mean_712 | `7.116820836943387` | `7.12` |
| PASS | stage48_F_L22_mean_808 | `8.078315451431273` | `8.08` |
| PASS | stage48_D_L22_mean_895 | `8.946221629428864` | `8.95` |
| PASS | stage48_L22_ordering_A_lt_F (A < F < D (opposite behavioral ordering A > D > F)) | `True` | `True` |
| PASS | stage48_L22_ordering_F_lt_D | `True` | `True` |

## Key Findings

### Stage 4.7 Complete-Case Counts

| Condition | n_censored | n_complete_case | n_cc_success | cc_rate |
|-----------|-----------|----------------|-------------|--------|
| A | 0 | 12 | 10 | 83.3% |
| D | 1 | 11 | 5 | 45.5% |
| F | 1 | 11 | 3 | 27.3% |
| E | 3 | 9 | 4 | 44.4% |

**Docs discrepancy**: Multiple docs claim A=10/11 (91%). Artifact shows A=10/12 (83.3%, 0 censored).

### Stage 4.8 Results

| Condition | n_total | n_success | success_rate |
|-----------|---------|-----------|-------------|
| A | 20 | 12 | 60% |
| D | 20 | 10 | 50% |
| F | 20 | 8 | 40% |

Variance ratio (between/within): 3.69×

### Layer-22 First-500 Mean Projection

| Stage | A | F | D | Ordering |
|-------|---|---|---|----------|
| 4.7 | 7.265 | 8.499 | 9.057 | A < F < D (opposite behavioral) |
| 4.8 | 7.117 | 8.078 | 8.946 | A < F < D (replicated) |
