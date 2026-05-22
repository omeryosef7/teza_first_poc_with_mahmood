# POC Stage 5: Refusal Projection Dynamics

Stage 5 is a read-only mechanistic analysis stage. It measures how strongly
existing examples project onto a Stage 4 refusal direction across HuggingFace
hidden-state indices and token regions.

Stage 5 does not generate new attacks and does not modify Stage 2, Stage 3, or
Stage 4 artifacts. By default it does not print or write raw prompt text, raw
response text, token strings, raw hidden states, logits, or raw model outputs.

## Inputs

- Existing Stage 2/3-style JSONL examples with a prompt-like field.
- Existing Stage 4 refusal direction artifact, for example
  `outputs/stage4/qwen3-14b/refusal_direction/direction.pt`.
- HuggingFace causal language model name or local path matching the direction.

## Outputs

- Projection JSONL: one compact row per example, sequence type, hidden-state
  index, and token region.
- Compute run summary JSON.
- Aggregate summary JSON from the summarizer.
- Optional aggregate CSV from the summarizer.

## Tiny Smoke Run

```bash
python -m poc_stage5.compute_refusal_projection_dynamics \
  --input-jsonl outputs/hijacking_baseline_gpt-o4-mini_small_strongreject.jsonl \
  --direction-path outputs/stage4/qwen3-14b/refusal_direction/direction.pt \
  --model-name-or-path Qwen/Qwen3-14B \
  --output-jsonl outputs/stage5/qwen3-14b/smoke_max1_final/per_example_layer_region_projections.jsonl \
  --summary-json outputs/stage5/qwen3-14b/smoke_max1_final/projection_summary.json \
  --error-jsonl outputs/stage5/qwen3-14b/smoke_max1_final/projection_errors.jsonl \
  --run-name stage5_qwen3_smoke_max1_final \
  --max-examples 1 \
  --max-length 128 \
  --layers -1 \
  --token-regions final_token,last_8 \
  --device auto \
  --dtype bfloat16 \
  --overwrite
```

For Slurm, use:

```bash
sbatch slurm_scripts/stage5_qwen3_projection_smoke.slurm
```

## Small Runs

Five examples:

```bash
python -m poc_stage5.compute_refusal_projection_dynamics \
  --input-jsonl outputs/hijacking_baseline_gpt-o4-mini_small_strongreject.jsonl \
  --direction-path outputs/stage4/qwen3-14b/refusal_direction/direction.pt \
  --model-name-or-path Qwen/Qwen3-14B \
  --output-jsonl outputs/stage5/qwen3-14b/max5_final/per_example_layer_region_projections.jsonl \
  --summary-json outputs/stage5/qwen3-14b/max5_final/projection_summary.json \
  --error-jsonl outputs/stage5/qwen3-14b/max5_final/projection_errors.jsonl \
  --run-name stage5_qwen3_max5_final \
  --max-examples 5 \
  --max-length 256 \
  --layers -1 \
  --token-regions final_token,last_8,last_32 \
  --device auto \
  --dtype bfloat16 \
  --overwrite
```

Twenty examples:

```bash
python -m poc_stage5.compute_refusal_projection_dynamics \
  --input-jsonl outputs/hijacking_baseline_gpt-o4-mini_small_strongreject.jsonl \
  --direction-path outputs/stage4/qwen3-14b/refusal_direction/direction.pt \
  --model-name-or-path Qwen/Qwen3-14B \
  --output-jsonl outputs/stage5/qwen3-14b/max20_final/per_example_layer_region_projections.jsonl \
  --summary-json outputs/stage5/qwen3-14b/max20_final/projection_summary.json \
  --error-jsonl outputs/stage5/qwen3-14b/max20_final/projection_errors.jsonl \
  --run-name stage5_qwen3_max20_final \
  --max-examples 20 \
  --max-length 256 \
  --layers -1 \
  --token-regions final_token,last_8,last_32 \
  --device auto \
  --dtype bfloat16 \
  --overwrite
```

Add `--include-response-context` to also analyze prompt plus response text
when a response is present.

## Summarization

```bash
python -m poc_stage5.summarize_refusal_projection_dynamics \
  --input-jsonl outputs/stage5/qwen3-14b/smoke_max1_final/per_example_layer_region_projections.jsonl \
  --output-json outputs/stage5/qwen3-14b/smoke_max1_final/projection_aggregate_summary.json \
  --output-csv outputs/stage5/qwen3-14b/smoke_max1_final/projection_aggregate_summary.csv \
  --overwrite
```

The summarizer groups by `condition`, `sequence_type`, `hidden_state_index`,
and `region`. It reports projection means, standard deviations, medians,
success rates, score means, and success-vs-failure projection differences when
`is_success` is available.

## Terms

- `prompt_only`: projection is computed on the loaded prompt text only.
- `prompt_plus_response`: projection is computed on prompt text, two newlines,
  then response text. This is only enabled with `--include-response-context`.
- `hidden_state_index`: HuggingFace `output_hidden_states` tuple index. `0` is
  embedding output, `1` is the first transformer block output, and `-1` in the
  CLI resolves to the final hidden state. Use `all` only when you really want
  every returned hidden state.
- Token regions: `final_token` is the final token, `last_8`/`last_32` are
  suffix windows, and `all` covers every token in the truncated input.

Raw text is not stored by default to keep Stage 5 outputs safe to inspect and
share. Use `--store-text-hashes` if you need SHA256 identifiers for later
joining without exposing prompt or response text.

## Troubleshooting

- Direction dimension mismatch: the direction and model hidden size differ.
  Use a direction extracted from the same model family/checkpoint as the model
  passed to `--model-name-or-path`.
- CUDA OOM: use `--layers -1`, smaller `--max-length`, `--dtype bfloat16`, and
  a high-memory GPU. CPU memory flags such as `--mem` do not increase GPU VRAM.
- Missing prompt field: the loader looks for fields such as `full_prompt`,
  `attack_prompt`, `prompt`, `input`, `messages`, or falls back to `goal`.
  Rows without content are skipped.
- Output file already exists: pass `--overwrite` or choose a new output path.
- Wrong model/checkpoint for direction: early validation should fail before
  processing examples if the hidden size does not match.
