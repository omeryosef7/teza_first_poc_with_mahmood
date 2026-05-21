# POC Stage 5: Refusal Projection Dynamics Skeleton

Stage 5 is intended to become a read-only mechanistic analysis stage for
measuring refusal-direction projections across examples, layers, and token
regions.

Current status: skeleton only.

It does not:

- generate new attacks
- modify Stage 2, Stage 3, or Stage 4 artifacts
- load a model
- load refusal-direction tensors with `torch.load`
- run activation capture or projection computation
- write output JSONL or summary artifacts

## Compute Stub

```bash
python -m poc_stage5.compute_refusal_projection_dynamics \
  --input-jsonl outputs/hijacking_baseline_gpt-o4-mini_small_strongreject.jsonl \
  --direction-path outputs/stage4/qwen3-14b/refusal_direction/direction.pt \
  --model-name-or-path Qwen/Qwen3-14B \
  --output-jsonl outputs/stage5/qwen3-14b/refusal_projection_dynamics/per_example_layer_region_projections.jsonl \
  --summary-json outputs/stage5/qwen3-14b/refusal_projection_dynamics/projection_summary.json \
  --layers all \
  --token-regions prompt,response
```

The command validates that the input JSONL and direction artifact exist, then
prints the planned configuration. Output paths are accepted as future
destinations but are not created by this skeleton.

## Summary Stub

```bash
python -m poc_stage5.summarize_refusal_projection_dynamics \
  --input-jsonl outputs/stage5/qwen3-14b/refusal_projection_dynamics/per_example_layer_region_projections.jsonl \
  --summary-json outputs/stage5/qwen3-14b/refusal_projection_dynamics/projection_summary.json
```

The command validates that the input JSONL exists, then prints the planned
summary configuration. Real aggregation and summary writing are TODOs.

## TODO

- Define the Stage 5 projection row schema.
- Normalize Stage 2/3 JSONL records into direct and hijacked prompt examples.
- Load model/tokenizer and direction tensors read-only.
- Capture activations for configured layers and token regions.
- Project activations onto refusal directions.
- Write JSONL and summary artifacts under a Stage 5 output directory.
