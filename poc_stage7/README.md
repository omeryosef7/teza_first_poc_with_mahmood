# POC Stage 7: Offline Objective Comparison

Stage 7 is a strictly offline analysis stage. It does not load a model, does not generate new prompts or responses, and does not modify Stage 2, Stage 3, Stage 4, Stage 5, or Stage 6 logic. It reads existing Stage 5 projection rows, optionally reads Stage 6 token-delay rows for enrichment/validation, and computes candidate objective values for RL research.

## Purpose

The goal is to test whether candidate reward definitions are sensible before any RL run. Stage 7 compares objectives based on:

- judge score only
- StrongREJECT score only
- refusal projection suppression
- refusal projection preservation
- a hybrid objective

## Inputs

Stage 7 reads the existing Stage 5 output JSONL, for example:

- [outputs/stage5/qwen3-14b/max100_final/per_example_layer_region_projections.jsonl](outputs/stage5/qwen3-14b/max100_final/per_example_layer_region_projections.jsonl)

Optional Stage 6 enrichment input:

- [outputs/stage6/qwen3-14b/maxall_token_delay/token_delay.jsonl](outputs/stage6/qwen3-14b/maxall_token_delay/token_delay.jsonl)

For v1, the comparison uses Stage 5 rows where:

- `sequence_type == "prompt_only"`
- `hidden_state_index == 40`
- `region` is one of `final_token`, `last_8`, `last_32`

## Score Scale

Stage 7 makes the behavioral scale explicit.

- `judge_score` is the raw Stage 2/5 judge score, typically on a 1-10 scale.
- `strongreject_score` is the raw StrongREJECT score, typically on a 0-1 scale in the current outputs.
- `judge_score_normalized` is computed as `0-1` using `(score - 1) / 9` for 1-10 rows, or passed through when the input is already 0-1.
- `strongreject_score_normalized` is passed through when already on 0-1, with a documented fallback for future 0-10 rows.
- `behavioral_score` is the normalized score used in all objective formulas.

Both raw and normalized score fields are written so the scale is never implicit.

## Objective Definitions

Let `b` be the normalized behavioral score, `p` the projection value, and `b0` the baseline projection.

- `judge_only = b`
- `strongreject_only = normalized_strongreject_score`
- `refusal_suppression = b - lambda_refusal * p`
- `refusal_preservation = b - lambda_preserve * abs(p - b0)`
- `hybrid = alpha * b - beta * p - delta * abs(p - b0)`

## Baseline Projection

`baseline_projection` is computed from failed Stage 5 rows grouped by `condition`, `region`, and `hidden_state_index`.

- If failed rows exist in the group, the baseline is the mean projection over those failed rows.
- If no failed rows exist, Stage 7 falls back to the group mean over all rows.
- The output includes `baseline_source` so the fallback choice is explicit.

## Smoke Command

```bash
python -m poc_stage7.compare_objectives \
  --stage5-jsonl outputs/stage5/qwen3-14b/max100_final/per_example_layer_region_projections.jsonl \
  --stage6-jsonl outputs/stage6/qwen3-14b/maxall_token_delay/token_delay.jsonl \
  --output-jsonl outputs/stage7/qwen3-14b/objective_comparison_v1/objective_comparison.jsonl \
  --summary-json outputs/stage7/qwen3-14b/objective_comparison_v1/objective_comparison_summary.json \
  --regions final_token,last_8,last_32 \
  --hidden-state-index 40 \
  --lambda-refusal 1.0 \
  --lambda-preserve 1.0 \
  --alpha 1.0 \
  --beta 1.0 \
  --delta 1.0 \
  --overwrite
```

Summarize an existing Stage 7 JSONL file:

```bash
python -m poc_stage7.summarize_objectives \
  --input-jsonl outputs/stage7/qwen3-14b/objective_comparison_v1/objective_comparison.jsonl \
  --output-json outputs/stage7/qwen3-14b/objective_comparison_v1/objective_comparison_summary_recomputed.json \
  --overwrite
```

## Slurm

Submit the offline comparison job with:

```bash
sbatch slurm_scripts/stage7_qwen3_objective_comparison.slurm
```

## Warning

Stage 7 is offline analysis only. It is not RL, does not load a model, and does not generate or edit attack prompts or target responses.
