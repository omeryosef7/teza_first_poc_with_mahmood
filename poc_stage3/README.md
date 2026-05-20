# POC Stage 3: StrongREJECT Integration

Stage 3 scores the existing Stage 2 hijacking responses with StrongREJECT and compares those scores to the original Hijacking judge labels.

## Purpose

This stage evaluates the quality and harmfulness of the Stage 2 target responses without rerunning the hijacking attack and without modifying the Stage 2 artifacts in place.

## Inputs

- Stage 2 JSONL: `outputs/hijacking_baseline_gpt-o4-mini_small.jsonl`
- Stage 2 summary: `outputs/hijacking_baseline_gpt-o4-mini_small_summary.json`

Required Stage 2 fields:

- `goal`
- `target_response`
- `is_success`
- `judge_score`
- `goal_index`

## StrongREJECT integration path

The local StrongREJECT checkout is used through the rubric evaluator:

- module: `strong_reject.evaluate`
- function: `evaluate(...)`
- evaluator: `strongreject_rubric`

The local code confirms that `strongreject_rubric` expects `forbidden_prompt` and `response`, and returns `score` plus rubric fields such as `refusal`, `convincingness`, and `specificity` when available.

No editable install is required for the scripts in this repo because they insert the local checkout into `sys.path` automatically. If you prefer, you can still install it with:

```bash
pip install -e strong_reject/strong_reject
```

## Environment

- `OPENAI_API_KEY` is required for `strongreject_rubric`
- The local StrongREJECT Python dependencies must be installed

If `OPENAI_API_KEY` is missing, the scoring CLI fails fast with an actionable error and does not fabricate scores.

## Scoring command

```bash
python -m poc_stage3.run_strongreject_scoring \
  --input-jsonl outputs/hijacking_baseline_gpt-o4-mini_small.jsonl \
  --output-jsonl outputs/hijacking_baseline_gpt-o4-mini_small_strongreject.jsonl \
  --summary-json outputs/hijacking_baseline_gpt-o4-mini_small_strongreject_summary.json \
  --evaluator strongreject_rubric
```

Optional arguments:

- `--max-rows`
- `--only-successful-hijacking-rows`
- `--resume`
- `--sleep-seconds`
- `--overwrite`
- `--threshold`

## Analysis command

```bash
python -m poc_stage3.analyze_strongreject_results \
  --input-jsonl outputs/hijacking_baseline_gpt-o4-mini_small_strongreject.jsonl \
  --summary-json outputs/hijacking_baseline_gpt-o4-mini_small_strongreject_summary.json
```

Optional:

- `--output-json <path>` writes a machine-readable analysis summary

## Outputs

- `outputs/hijacking_baseline_gpt-o4-mini_small_strongreject.jsonl`
- `outputs/hijacking_baseline_gpt-o4-mini_small_strongreject_summary.json`

Each scored row preserves the original Stage 2 fields and appends `strongreject_*` fields, including:

- `strongreject_evaluator`
- `strongreject_status`
- `strongreject_score`
- `strongreject_raw_result`
- `strongreject_refusal`
- `strongreject_convincingness`
- `strongreject_specificity`
- `strongreject_error_type`
- `strongreject_error_message`

## Interpretation notes

- The default threshold for agreement-style analysis is `0.5`
- This threshold is only an analysis convenience, not a canonical StrongREJECT cutoff
- Stage 2.5 still applies: some Stage 2 failures may reflect provider/API issues rather than genuine model refusals
- StrongREJECT is an evaluator, not ground truth

## Current execution status

In this workspace, `OPENAI_API_KEY` is not set, so real StrongREJECT scoring cannot be run yet.

Use the scoring command above after configuring credentials to generate the artifacts and then rerun the analysis command.