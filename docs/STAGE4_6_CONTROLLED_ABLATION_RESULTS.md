# Stage 4.6 — Controlled Ablation Results

**Status**: SKELETON — populate after GPU run completes

---

## Run Summary

| Field | Value |
|---|---|
| Run timestamp | TBD |
| N conditions run | TBD / 20 |
| N failed | TBD |
| Total generation tokens | TBD |

## Condition-Level Results

*Populated from `condition_summary.csv`*

| Condition | N | SR Success Rate | Mean SR Score | Mean Think Tokens |
|---|---|---|---|---|
| A (full, thinking=on) | TBD | TBD | TBD | TBD |
| B (50%, thinking=on) | TBD | TBD | TBD | TBD |
| C (25%, thinking=on) | TBD | TBD | TBD | TBD |
| D (no puzzle, thinking=on) | TBD | TBD | TBD | TBD |
| E (full, thinking=off) | TBD | TBD | TBD | TBD |

## Key Comparisons

### Puzzle Length Effect (A vs D, thinking=on)

- Mean SR score A: TBD | D: TBD | diff: TBD
- N(A > D): TBD / 4 | N(D > A): TBD / 4
- Wilcoxon signed-rank p: TBD
- Interpretation: TBD

### Thinking Mode Effect (A vs E, same prompt)

- Mean SR score A: TBD | E: TBD | diff: TBD
- N(A > E): TBD / 4 | N(E > A): TBD / 4
- Interpretation: TBD

## Per-Goal Breakdown

*Populated from `goal_condition_summary.csv`*

| Goal | Cond A SR | Cond D SR | Cond E SR |
|---|---|---|---|
| 0 (dimethylmercury) | TBD | TBD | TBD |
| 1 (biowarfare agents) | TBD | TBD | TBD |
| 2 (chemical warfare) | TBD | TBD | TBD |
| 3 (cash smuggling) | TBD | TBD | TBD |

## Figures

*See `outputs/stage4_6/runs_output_*/plots/`*

- p1: SR success rate by condition (bar)
- p2: Mean SR score by condition with 95% CI (bar + error bars)
- p3: Think tokens by condition (bar)
- p4: SR success rate by goal and condition (faceted bars)
- p5: SR score vs puzzle fraction per source (line plot)
- p6: Think tokens vs puzzle fraction per source (line plot)
- p7: Thinking mode A vs E scatter (per-source paired)
- p8: Success heatmap (condition × goal)

## Limitations

- N=4 source prompts per comparison — insufficient for statistical inference
- Puzzle token deletion may disrupt sentence structure (ablation is approximate)
- Results labeled as exploratory; do not claim causal refusal mechanism
- No cross-goal pooling (goals have different base rates)
