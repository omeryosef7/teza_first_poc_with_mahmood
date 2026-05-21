# POC Stage 4A1: Qwen3-14B Candidate Refusal Directions

Stage 4A1 extracts candidate refusal directions for `Qwen/Qwen3-14B` over
`position x layer`, matching the tensor structure used by the upstream
refusal-direction pipeline: `[n_positions, n_layers, d_model]`.

This stage does **not** perform the final intervention-based selection from the
published methodology. It only writes projection diagnostics and a provisional
`direction.pt` for smoke tests.

Stage 4A2 performs intervention-based selection over the Stage 4A1 candidates.
It is the first Stage 4 step that can produce a scientifically usable refusal
direction with:

```json
"selection_status": "intervention_selected"
```

## Important Guardrail

Any `direction.pt` produced by Stage 4A1 is provisional. Use
`poc_stage4.direction_loader.load_direction(...)` for downstream code. It
rejects provisional directions by default and only loads them when explicitly
called with:

```python
load_direction(path, allow_provisional_direction=True)
```

Future CLIs should expose this as:

```bash
--allow-provisional-direction
```

The default must remain false.

## Requirements

Qwen3 requires a recent Hugging Face Transformers release. The vendored
`Chain_of_Thought_Hijacking/refusal_direction/requirements.txt` pins an older
version, so use an environment with:

```bash
pip install "transformers>=4.51.0" accelerate torch
```

`Qwen/Qwen3-14B` may require substantial GPU memory even for dry runs.

## Dry Run

```bash
python -m poc_stage4.extract_refusal_direction \
  --dry-run \
  --batch-size 1 \
  --enable-thinking false \
  --overwrite
```

## Larger Stage 4A1 Run

```bash
python -m poc_stage4.extract_refusal_direction \
  --model-name Qwen/Qwen3-14B \
  --num-harmful 64 \
  --num-harmless 64 \
  --positions=-1,-2,-3,-4 \
  --batch-size 1 \
  --enable-thinking false
```

`--enable-thinking` is configurable and recorded in every metadata artifact.
The default is `false` for shorter, stable prompt formatting.

## Outputs

Default output directory:

```text
outputs/stage4/qwen3-14b/refusal_direction/
```

Files:

```text
candidate_directions.pt
candidate_metadata.json
projection_diagnostics.json
direction.pt
selected_direction.json
extraction_metrics.json
```

`selected_direction.json` uses:

```json
"selection_status": "provisional_projection_diagnostic_only"
```

Stage 4A2 must replace this with intervention-based selection:

```json
"selection_status": "intervention_selected"
```

## What Stage 4A2 Still Needs

Stage 4A2 adds intervention-based candidate selection aligned with the upstream
`select_direction.py` logic:

- harmful validation refusal ablation
- harmless validation activation-addition/refusal steering
- KL-divergence or similar sanity filtering
- final direction selected by intervention behavior, not projection diagnostics

## Stage 4A2 Smoke Test

This evaluates the top 5 candidates according to Stage 4A1 projection
diagnostics. It writes intervention metrics but does not overwrite
`direction.pt` or `selected_direction.json`.

```bash
python -m poc_stage4.select_refusal_direction_interventions \
  --input-dir outputs/stage4/qwen3-14b/refusal_direction \
  --output-dir outputs/stage4/qwen3-14b/refusal_direction \
  --model-name Qwen/Qwen3-14B \
  --enable-thinking false \
  --top-k-projection 5 \
  --batch-size 1
```

SLURM smoke test:

```bash
sbatch --export=TOP_K_PROJECTION=5 slurm_scripts/stage4a2_qwen3_intervention_selection.slurm
```

## Stage 4A2 Full Selection

This evaluates all 160 Stage 4A1 candidates by default and updates
`direction.pt` plus `selected_direction.json` only if at least one candidate
survives the intervention filters.

```bash
python -m poc_stage4.select_refusal_direction_interventions \
  --input-dir outputs/stage4/qwen3-14b/refusal_direction \
  --output-dir outputs/stage4/qwen3-14b/refusal_direction \
  --model-name Qwen/Qwen3-14B \
  --enable-thinking false \
  --batch-size 1
```

SLURM full run:

```bash
sbatch slurm_scripts/stage4a2_qwen3_intervention_selection.slurm
```

By default, Stage 4A2 uses the upstream dedicated validation splits:

```text
Chain_of_Thought_Hijacking/refusal_direction/dataset/splits/harmful_val.json
Chain_of_Thought_Hijacking/refusal_direction/dataset/splits/harmless_val.json
```

The Stage 4A1 internal held-out split is available only for smoke/debug mode
with `--use-stage4a1-heldout-validation`.

## Qwen3 Refusal Tokens

The vendored upstream Qwen wrapper defines:

```python
QWEN_REFUSAL_TOKS = [40, 2121] # ['I', 'As']
```

There is no vendored Qwen3 wrapper, so Stage 4A2 uses the closest documented
approximation by default: it resolves the same surface forms, `I,As`, with the
Qwen3 tokenizer at runtime. The resolved token IDs and decoded strings are saved
in `intervention_selection_metrics.json`.

Override when needed:

```bash
--refusal-token-strings I,As
```

or:

```bash
--refusal-token-ids 40,2121
```
