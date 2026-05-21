# POC Stage 5: Refusal Projection Dynamics

Stage 5 is intended to become a read-only mechanistic analysis stage for
measuring refusal-direction projections across examples, layers, and token
regions.

Current status: conservative compute runner plus summary skeleton.

The compute runner does not:

- generate new attacks
- modify Stage 2, Stage 3, or Stage 4 artifacts
- print or write raw prompt text, response text, token strings, raw hidden
  states, or raw model outputs
- run multi-input comparison mode

## Compute

```bash
python -m poc_stage5.compute_refusal_projection_dynamics \
  --input-jsonl outputs/hijacking_baseline_gpt-o4-mini_small_strongreject.jsonl \
  --direction-path outputs/stage4/qwen3-14b/refusal_direction/direction.pt \
  --model-name-or-path Qwen/Qwen3-14B \
  --output-jsonl outputs/stage5/qwen3-14b/refusal_projection_dynamics/per_example_layer_region_projections.jsonl \
  --summary-json outputs/stage5/qwen3-14b/refusal_projection_dynamics/projection_summary.json \
  --max-examples 1 \
  --max-length 512 \
  --layers -1 \
  --token-regions final_token
```

`--layers` uses HuggingFace hidden-state indices: `0` is embeddings, `1` is
the first transformer block output, and `-1` is the final hidden state.
Omitted/`auto` defaults to `-1` only. Use `all` explicitly to project every
hidden-state index.

## Summary Stub

```bash
python -m poc_stage5.summarize_refusal_projection_dynamics \
  --input-jsonl outputs/stage5/qwen3-14b/refusal_projection_dynamics/per_example_layer_region_projections.jsonl \
  --summary-json outputs/stage5/qwen3-14b/refusal_projection_dynamics/projection_summary.json
```

The command validates that the input JSONL exists, then prints the planned
summary configuration. Real aggregation and summary writing are TODOs.

## TODO

- Implement full Stage 5 summary aggregation.
- Add multi-input comparison mode if needed.
