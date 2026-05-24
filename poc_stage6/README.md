# POC Stage 6: Token-Level Delayed Detection

Stage 6 is a read-only analysis stage for measuring how refusal-direction
projection changes as progressively more prompt-prefix tokens are revealed.
The research question is: how late does the model internally show refusal or
harmful-intent signal?

Stage 6 reuses Stage 5 example loading, refusal-direction loading, model
loading, and projection summaries where safe. Direct prefix execution from
`input_ids` and `attention_mask` lives in `poc_stage6` so Stage 5 scientific
logic stays unchanged.

Stage 6 does not generate new attacks and does not modify Stage 2, Stage 3,
Stage 4, or Stage 5 logic. By default it does not print or write raw prompt
text, raw response text, token strings, logits, hidden states, or raw model
outputs. Use `--store-text-hashes` only when SHA256 prompt hashes are needed
for joining outputs.

## Qwen Token Trace Export

`poc_stage6.export_qwen_token_trace` writes one JSON artifact for a selected
hijack example. The supervisor-facing default is a real rerun on
`Qwen/Qwen3-14B` with `enable_thinking=True`; `--existing-only` is reserved for
prompt-reconstruction debugging.

Example output path:

`outputs/stage6/qwen3-14b/token_trace/qwen_token_trace.json`

The artifact records the formatted chat prompt, prompt and generation token
IDs, token strings, single-token decodes, round-trip checks, generation
config, and the available success-evaluation fields.

## Prefix Behavior

Prefixes are created by tokenizing the full prompt once, slicing token IDs, and
passing the sliced tensors to the model. Requested prefix labels are preserved
in `prefix_length`.

For short prompts, multiple requested prefixes may resolve to the same actual
token count. For example, a 40-token prompt with `--prefix-lengths 64,128,full`
will produce separate rows for `64`, `128`, and `full`, each with `num_tokens`
equal to 40. This keeps the output aligned with the requested schedule.

`full_prompt_num_tokens` is the full prompt token count before the Stage 6
`--max-length` cap. `num_tokens` is the actual prefix length passed to the
model after applying the requested prefix, prompt length, and `--max-length`.

## Tiny Smoke Run

```bash
python -m poc_stage6.compute_token_delay \
  --input-jsonl outputs/hijacking_baseline_gpt-o4-mini_small_strongreject.jsonl \
  --direction-path outputs/stage4/qwen3-14b/refusal_direction/direction.pt \
  --model-name-or-path Qwen/Qwen3-14B \
  --output-jsonl outputs/stage6/qwen3-14b/smoke_token_delay/token_delay.jsonl \
  --summary-json outputs/stage6/qwen3-14b/smoke_token_delay/token_delay_summary.json \
  --error-jsonl outputs/stage6/qwen3-14b/smoke_token_delay/token_delay_errors.jsonl \
  --max-examples 1 \
  --max-length 256 \
  --prefix-lengths 16,32,64,128,full \
  --layers -1 \
  --token-region final_token \
  --device auto \
  --dtype bfloat16 \
  --condition cot_hijack \
  --run-name stage6_qwen3_token_delay_smoke \
  --overwrite
```

For Slurm, submit the smoke script manually:

```bash
sbatch slurm_scripts/stage6_qwen3_token_delay_smoke.slurm
```

## Summarization

```bash
python -m poc_stage6.summarize_token_delay \
  --input-jsonl outputs/stage6/qwen3-14b/smoke_token_delay/token_delay.jsonl \
  --output-json outputs/stage6/qwen3-14b/smoke_token_delay/token_delay_aggregate_summary.json \
  --output-csv outputs/stage6/qwen3-14b/smoke_token_delay/token_delay_aggregate_summary.csv \
  --overwrite
```

The summarizer groups by `condition`, `hidden_state_index`, `prefix_length`,
and `token_region`. It reports projection means, standard deviations, medians,
success rates, and score means when available.

## Safety And Scope

- Stage 6 only analyzes existing examples.
- Stage 6 writes compact numeric projection summaries only.
- Output paths are protected by default; pass `--overwrite` to replace them.
- Per-example or per-prefix failures can be written to `--error-jsonl` without
  stopping the whole run.
- Model, tokenizer, direction loading, and direction/model dimension failures
  stop the run.

