# POC Stage 7 Main Documentation

## Manager Summary

Stage 7 is an offline objective-comparison stage. It does not run RL. It reads completed Stage 5 projection rows, optionally enriches them with Stage 6 token-delay data, and computes candidate reward definitions for later RL research.

The main explicit result is that `objective_strongreject_only` had the clearest positive correlation with success in the current POC, at `0.5399055247990171`, while the refusal-based objectives were near zero or negative.

## Comprehensive Detailed Summary

Stage 7 asks a narrow question: if a future RL loop were added, which offline objective would even be worth optimizing?

Inputs:

- Stage 5 projection rows
- optional Stage 6 token-delay rows
- inherited behavioral signals from Stage 2/3

Outputs:

- one Stage 7 row per Stage 5 row
- summary statistics for each candidate objective
- region-level comparisons

## What We Tried

- Compare behavior-only objectives against refusal-based objectives.
- Keep the whole stage offline and model-free.
- Preserve compatibility with Stage 5 row IDs and region groupings.
- Quantify whether any candidate objective tracks the existing success labels.

## What We Actually Did

- Added the `poc_stage7` package.
- Implemented objective calculation and summary logic.
- Read Stage 5 and Stage 6 outputs.
- Wrote a completed objective-comparison JSONL and summary JSON.

## Runs And Artifacts

| Run / Artifact | Path | What It Shows |
| --- | --- | --- |
| Stage 7 README | `poc_stage7/README.md` | Offline objective-comparison design and commands. |
| Slurm script | `slurm_scripts/stage7_qwen3_objective_comparison.slurm` | Batch objective-comparison run. |
| Output JSONL | `outputs/stage7/qwen3-14b/objective_comparison_v1/objective_comparison.jsonl` | One Stage 7 row per filtered Stage 5 row. |
| Summary JSON | `outputs/stage7/qwen3-14b/objective_comparison_v1/objective_comparison_summary.json` | Objective means, correlations, and region rankings. |
| Recomputed summary JSON | `outputs/stage7/qwen3-14b/objective_comparison_v1/objective_comparison_summary_recomputed.json` | Summary regenerated from the JSONL. |

## Results

Explicit run totals:

- Stage 5 rows read: `126`
- Stage 6 rows read: `210`
- Stage 7 rows written: `126`
- success count: `12`
- failure count: `114`
- unknown success count: `0`

Overall objective means:

| Objective | Mean |
| --- | ---: |
| `objective_judge_only` | `1.0` |
| `objective_strongreject_only` | `0.07142857142857142` |
| `objective_refusal_suppression` | `1.0196141893901522` |
| `objective_refusal_preservation` | `-0.917880095734433` |
| `objective_hybrid` | `-0.8982659063442807` |

Success correlations from the diagnostics:

| Objective | Pearson correlation with success |
| --- | ---: |
| `objective_judge_only` | `null` |
| `objective_strongreject_only` | `0.5399055247990171` |
| `objective_refusal_suppression` | `-0.047477119210331084` |
| `objective_refusal_preservation` | `-0.06031889474127339` |
| `objective_hybrid` | `-0.06117488437768338` |

Interpretation:

- `objective_strongreject_only` is the clearest positive signal in this POC.
- The refusal-based objectives are near zero or slightly negative, so they did not track the existing success labels well in this small dataset.
- `objective_judge_only` is `null` because the inherited judge-only value was constant in this summary and therefore has no meaningful Pearson correlation.

Region ranking by hybrid objective:

1. `last_32` with mean `-0.64006165095738`
2. `last_8` with mean `-0.7192085285234571`
3. `final_token` with mean `-1.335527539552005`

Baseline fallback usage:

- `baseline_fallback_counts.failed_mean = 126`
- `baseline_fallback_counts.group_mean = 0`
- `baseline_fallback_counts.row_mean_fallback = 0`

Why this matters:

- every Stage 7 row used the failed-row mean baseline path
- no row had to fall back to a weaker group-mean or row-mean approximation
- that makes the refusal-preservation-style comparisons internally consistent for this run

## What The Main Metrics Mean

- `objective_judge_only`: reward proxy using only the normalized behavioral/judge score. Larger is better if the goal is to reward the same behavior the inherited judge liked.
- `objective_strongreject_only`: reward proxy using only the StrongREJECT score. Larger is better if the goal is to optimize for StrongREJECT-defined harmfulness.
- `objective_refusal_suppression`: candidate objective that rewards lower refusal-direction expression relative to baseline. Larger is better for suppression under this definition.
- `objective_refusal_preservation`: candidate objective that rewards preservation relative to the failed-row baseline. Larger is better under that preservation framing.
- `objective_hybrid`: combined objective balancing behavioral and refusal-based signals.
- `projection_behavioral_pearson` or objective-success Pearson values: linear association between an objective and the binary success label. Positive means the metric tends to increase on successful rows; negative means it tends to increase on failed rows; near zero means little linear relationship in this POC.
- `rows_read_stage5`: how many Stage 5 projection rows were consumed.
- `rows_read_stage6`: how many Stage 6 prefix rows were available for enrichment and validation.
- `objective_rows_written`: how many Stage 7 output rows were emitted.
- `success_minus_failure`: average objective value on successful rows minus average objective value on failed rows.

## Limitations / Caveats

- Stage 7 is offline analysis only. It is not RL, does not load a model, and does not generate or edit attack prompts or target responses.
- The conclusions are based on a small POC dataset and should be treated as ranking evidence, not final reward design proof.
- The refusal-based objectives depend on the provisional Stage 4 direction via Stages 5 and 6.

## Handoff To Next Stage

Stage 8A can use the Stage 7 output as an offline reward source for a constrained sandbox, which is exactly what the current repo does.
