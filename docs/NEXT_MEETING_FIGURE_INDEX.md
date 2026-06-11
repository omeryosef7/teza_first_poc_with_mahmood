# Figure Index — Next Meeting

**Last updated:** 2026-06-11  
**Stages:** 4.6 complete; 4.7 ALL COMPLETE (11/11 figures); 4.8 smoke running (job 534919)

---

## Stage 4.7 Figures — AVAILABLE NOW

All figures at: `outputs/stage4_7/runs/run_array_20260610_1442/plots/`

| # | Filename | Status | Key message |
|---|----------|--------|-------------|
| 1 | `fig1_behavior_by_condition.png` | ✅ Done | SR score and success A,D,F,E (n=12 per condition) |
| 2 | `fig2_thinking_length_by_condition.png` | ✅ Done | Think-token count by condition — A generates 13.9× more than F (same length!) |
| 3 | `fig3_full_vs_bare_vs_length_matched.png` | ✅ **KEY** | A vs D vs F paired: puzzle outperforms both bare and length-matched controls |
| 4 | `fig4_thinking_on_vs_off.png` | ✅ Done | A vs E paired: thinking required |
| 5 | `fig5_layer22_early_projection.png` | ✅ **KEY** | L22 projection by condition — A < D < F (opposite of behavioral ordering) |
| 6 | `fig6_layer22_normalized_trajectory.png` | ✅ Done | 10-bin trajectory across thinking phase |
| 7 | `fig7_per_goal_condition_heatmap.png` | ✅ **KEY** | Per-goal × condition SR score heatmap |
| 8 | `fig8_projection_vs_thinking_length.png` | ✅ **KEY** | Direction tracks thinking depth not success (Spearman ρ=−0.68) |
| 9 | `fig9_finish_reason_and_truncation.png` | ✅ Done | Censoring/finish reasons by condition |
| 10 | `fig10_complete_case_vs_legacy.png` | ✅ Done | Censoring sensitivity: complete-case vs legacy rates |
| 11 | `fig11_selected_layer_condition_effects.png` | ✅ Done | Layers 13, 16, 22, 38, 39 — consistent pattern across layers |

---

## Stage 4.6 Figures — AVAILABLE (for reference)

At: `outputs/stage4_6/runs_output_full_20260610_091021/plots_meeting/`

| # | Filename | Key message |
|---|----------|-------------|
| 1 | `fig1_sr_success_by_condition.png` | A and D both 4/4; B/C at 3/4; E at 2/4 |
| 3 | `fig3_paired_A_vs_D.png` | Equal success despite divergent thinking — puzzle is expensive but not necessary (n=1/goal) |
| 5 | `fig5_goal_condition_heatmap.png` | Full 4×5 SR score matrix |
| 6 | `fig6_token_budget_effect.png` | 16k token budget produced false failures; 32k required |

---

## Stage 4.8 Figures — PENDING

After full run and analysis (smoke job 533261 → array → analysis):

| # | Filename | Description |
|---|----------|-------------|
| 1 | `fig1_seed_outcomes_by_cell.png` | Heatmap: SR success per (prompt × condition × seed) |
| 2 | `fig2_within_vs_between_prompt_variability.png` | Variance decomposition |
| 3 | `fig3_condition_effects_with_prompt_fixed_effects.png` | Condition comparison with prompt fixed effects |
| 5 | `fig5_matched_success_failure_projection.png` | Projection in matched success/failure cells |
| 6 | `fig6_heldout_direction_performance.png` | LOO AUC per held-out prompt |

---

## Recommended Figures for Next Meeting (all available now)

For a 20-minute meeting with up to 5 slides:

1. **`fig3_full_vs_bare_vs_length_matched.png` (Stage 4.7)** — core finding: puzzle beats length-matched benign control
2. **`fig2_thinking_length_by_condition.png` (Stage 4.7)** — thinking amplification: 13.9× more tokens at equal prompt length
3. **`fig8_projection_vs_thinking_length.png` (Stage 4.7)** — key dissociation: direction = thinking proxy, not success proxy
4. **`fig5_layer22_early_projection.png` (Stage 4.7)** — A < D < F on provisional direction (opposite of behavioral success)
5. **`fig7_per_goal_condition_heatmap.png` (Stage 4.7)** — stability of A > D > F across all 4 goals

**Optional if Stage 4.8 full array completes:** `fig1_seed_outcomes_by_cell.png` — stochastic variation per prompt/condition/seed.
