# Figure Index — Next Meeting

**Status**: SKELETON — link actual output paths after runs complete

---

## Stage 4 (Frozen — Ready)

| Figure | Path | Description |
|---|---|---|
| Layer-22 divergence | `outputs/stage4/token_dynamics/full_20260604_101929/plots/` | Refusal direction projection by outcome |
| Per-layer effect sizes | same | Hedges' g across all 40 layers |
| Token trajectory heatmap | same | Per-example projection over generation |

## Stage 4.5B (Pending annotation run)

| Figure | Path | Description |
|---|---|---|
| Onset distribution | TBD | Histogram of onset token indices (think vs final) |
| Event-aligned trajectories | TBD | Layer-22 projection aligned to onset token |
| Confidence/agreement scatter | TBD | Two-pass agreement distance vs confidence |

## Stage 4.6 (Pending GPU run)

All plots at: `outputs/stage4_6/runs_output_*/plots/`

| Figure | File | Description |
|---|---|---|
| p1 | `p1_sr_success_rate_by_condition.png` | SR success rate per condition (bar) |
| p2 | `p2_mean_sr_score_by_condition.png` | Mean SR score ± 95% CI per condition |
| p3 | `p3_think_tokens_by_condition.png` | Think token count per condition |
| p4 | `p4_sr_success_by_goal_condition.png` | Success rate faceted by goal |
| p5 | `p5_sr_score_vs_puzzle_fraction.png` | SR score vs puzzle fraction (line, per source) |
| p6 | `p6_think_tokens_vs_puzzle_fraction.png` | Think tokens vs puzzle fraction |
| p7 | `p7_thinking_mode_A_vs_E_scatter.png` | A vs E paired scatter (thinking on/off) |
| p8 | `p8_success_heatmap_condition_goal.png` | Success rate heatmap: condition × goal |

## Key Numbers Table (for slides)

| Metric | Stage 4 | Stage 4.5B | Stage 4.6 |
|---|---|---|---|
| N examples | 42 | TBD annotated | 20 generations |
| Primary effect | g=1.256 (Layer 22) | TBD onset timing | TBD puzzle effect |
| Annotation source | — | LLM (o4-mini, exploratory) | — |
| Status | Frozen | Pending run | Pending GPU |
