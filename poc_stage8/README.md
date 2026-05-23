# POC Stage 8A: Controlled RL Sandbox Skeleton

Stage 8A is a strictly offline, synthetic sandbox for future RL-style suffix optimization. It does not load a model, does not call any API, does not require a GPU, and does not generate new attacks or use real harmful goals.

The purpose of this stage is to define the controlled environment, finite structural action space, reward interfaces, and smoke-test wiring before any real RL work exists.

## What Stage 8A Does

- Exposes a finite structural action space only.
- Keeps all action values symbolic and bounded.
- Updates environment metadata only; no text generation happens.
- Computes rewards from offline numeric observations only.
- Supports optional reuse of Stage 7 offline objective rows for reward observations.

## Action Space

Allowed action types:

- `choose_template_variant`
- `choose_reasoning_block_length_bucket`
- `choose_neutral_delimiter`
- `choose_safe_placeholder_order`
- `choose_include_harmless_puzzle_block`
- `choose_suffix_length_bucket`

The sandbox rejects arbitrary free-text action values. Only the finite values defined in `poc_stage8/actions.py` are accepted.

Safe placeholder strings used by the sandbox include:

- `[BENIGN_TASK_PLACEHOLDER]`
- `[SAFE_REASONING_BLOCK]`
- `[NEUTRAL_DELIMITER]`
- `[HARMLESS_PUZZLE_BLOCK]`

## Reward Modes

Stage 8A mirrors the Stage 7 objective vocabulary:

- `strongreject_only`
- `judge_only`
- `refusal_suppression`
- `refusal_preservation`
- `hybrid`

Default reward mode: `strongreject_only`.

The refusal-based modes are experimental and should be treated as candidate research interfaces only. They are not a recommendation to train a model with real harmful objectives.

## CLI

Run the sandbox:

```bash
python -m poc_stage8.run_sandbox \
  --output-jsonl outputs/stage8/sandbox_smoke/sandbox.jsonl \
  --summary-json outputs/stage8/sandbox_smoke/sandbox_summary.json \
  --num-episodes 3 \
  --max-steps 5 \
  --reward-mode strongreject_only \
  --overwrite
```

If the Stage 7 objective-comparison JSONL exists, you may optionally reuse it as the offline observation source:

```bash
python -m poc_stage8.run_sandbox \
  --output-jsonl outputs/stage8/sandbox_smoke/sandbox.jsonl \
  --summary-json outputs/stage8/sandbox_smoke/sandbox_summary.json \
  --num-episodes 3 \
  --max-steps 5 \
  --reward-mode strongreject_only \
  --stage7-jsonl outputs/stage7/qwen3-14b/objective_comparison_v1/objective_comparison.jsonl \
  --overwrite
```

Summarize an existing sandbox JSONL:

```bash
python -m poc_stage8.summarize_sandbox \
  --input-jsonl outputs/stage8/sandbox_smoke/sandbox.jsonl \
  --output-json outputs/stage8/sandbox_smoke/sandbox_aggregate_summary.json \
  --output-csv outputs/stage8/sandbox_smoke/sandbox_aggregate_summary.csv \
  --overwrite
```

## Smoke SLURM

An optional CPU-only smoke script is provided at `slurm_scripts/stage8_sandbox_smoke.slurm`.

## Warning

Stage 8A is not real RL yet. A later model-in-the-loop stage must remain constrained, offline where possible, and reviewed carefully before any expansion beyond this sandbox skeleton.