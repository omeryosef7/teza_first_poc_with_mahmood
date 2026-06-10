# Figure Index — Next Meeting

**Last updated:** 2026-06-10
**Stages:** 4.6 complete (figures available); 4.7 pending GPU execution

---

## Stage 4.6 Meeting Figures

All figures at: `outputs/stage4_6/runs_output_full_20260610_091021/plots_meeting/`

| # | Filename | Description | Key message |
|---|----------|-------------|-------------|
| 1 | `fig1_sr_success_by_condition.png` | Bar chart: SR success rate by condition (A–E), exact n/N labels, n=4 per condition | A and D both 4/4; E drops to 2/4; B and C at 3/4 |
| 2 | `fig2_thinking_tokens_by_condition.png` | Strip+mean: think-token count by condition (A–D), per-goal connecting lines | Puzzle (A) produces more thinking, but goal 2 reverses |
| 2b | `fig2b_thinking_tokens_by_condition_logscale.png` | Same, log scale — reveals large dynamic range | Range spans ~600 to ~20,000 tokens |
| 3 | `fig3_paired_A_vs_D.png` | **KEY:** Paired A vs D by goal — two panels: SR score (left), think tokens (right) | Equal success, divergent thinking; heterogeneous ratios |
| 4 | `fig4_paired_A_vs_E.png` | Paired A vs E by goal — SR score, dashed lines mark success loss | Goals 1, 3 lose success without thinking |
| 5 | `fig5_goal_condition_heatmap.png` | **KEY:** 4×5 heatmap of SR scores — full picture in one view | D column is perfect 1.000; single failures visible |
| 6 | `fig6_token_budget_effect.png` | **KEY:** Token-budget artifact for goals 1, 3 condition A | 16k budget → false failure; 32k → true success |

Also available (from original analysis run, less polished):
- `plots/p1_sr_success_rate_by_condition.png`
- `plots/p2_mean_sr_score_by_condition.png`
- `plots/p3_think_tokens_by_condition.png`
- `plots/p4_sr_success_by_goal_condition.png`
- `plots/p5_sr_score_vs_puzzle_fraction.png`
- `plots/p6_think_tokens_vs_puzzle_fraction.png`
- `plots/p7_thinking_mode_A_vs_E_scatter.png`
- `plots/p8_success_heatmap_condition_goal.png`

---

## Stage 4.7 Figures (pending — paths listed for reference)

After GPU generation completes, figures will appear at:
`outputs/stage4_7/runs/<run_timestamp>/plots/`

| # | Filename | Description |
|---|----------|-------------|
| 1 | `fig1_behavior_by_condition.png` | SR score and success A,D,F,E with per-prompt points+lines (n=12 or per-goal n=3) |
| 2 | `fig2_thinking_length_by_condition.png` | Think-token count A,D,F — log scale, paired lines |
| 3 | `fig3_full_vs_bare_vs_length_matched.png` | Direct comparison A vs D vs F — key figure for length-vs-semantics question |
| 4 | `fig4_thinking_on_vs_off.png` | Paired A vs E across 12 prompts |
| 5 | `fig5_layer22_early_projection.png` | First-500 and first-2000 Layer-22 projection by A,D,F |
| 6 | `fig6_layer22_normalized_trajectory.png` | 10 normalized reasoning bins, A/D/F lines |
| 7 | `fig7_per_goal_condition_heatmap.png` | Behavioral outcomes by goal, prompt, condition |
| 8 | `fig8_projection_vs_thinking_length.png` | Scatter: Layer-22 projection vs log(think_tokens) by condition |
| 9 | `fig9_finish_reason_and_truncation.png` | Finish reasons by condition |

---

## Figures for Presentation (recommended selection)

For a 20-minute meeting slot, use:

1. `fig3_paired_A_vs_D.png` — main Stage 4.6 finding
2. `fig5_goal_condition_heatmap.png` — full result overview
3. `fig6_token_budget_effect.png` — methodological lesson
4. (After 4.7) `fig3_full_vs_bare_vs_length_matched.png` — key new experiment result
5. (After 4.7) `fig5_layer22_early_projection.png` — mechanistic link
