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

## Progress Logs And Resume

All Stage 4 CLIs print timestamped progress lines and, when `tqdm` is
available, progress bars. In SLURM runs these usually appear in the job `.err`
file, while the final short success summary appears in the `.out` file. The
progress lines look like:

```text
[2026-05-21T12:34:56+00:00] [stage4a2] Evaluating candidate position=-3 layer=22
```

Use these flags on all Stage 4 CLIs:

```bash
--resume
```

Resume from an existing checkpoint directory. The run validates that the
checkpoint was created with the same important configuration before reusing it.

```bash
--checkpoint-dir <path>
```

Use a custom checkpoint directory instead of the default stage-specific one.

```bash
--no-progress
```

Disable timestamped progress logs and `tqdm` progress bars. This does not
disable checkpoint writing.

Checkpoints are configuration-guarded with a fingerprint stored in
`manifest.json`. If the current command changes important settings, such as
model name, prompt counts, positions, validation settings, selected direction,
or candidate list, resume fails clearly instead of mixing incompatible partial
results.

Existing jobs that started before checkpoint support was added cannot
retroactively resume. Only jobs started with this checkpointing code can be
continued.

### Checkpoint Contents

| Stage | Default checkpoint directory | Checkpoint files | Resume key | What resume does |
| --- | --- | --- | --- | --- |
| Stage 4A1 | `outputs/stage4/qwen3-14b/refusal_direction/checkpoints/stage4a1/` | `manifest.json`, `harmful_train_batch_*.pt`, `harmless_train_batch_*.pt`, `harmful_validation_batch_*.pt`, `harmless_validation_batch_*.pt` | activation split + batch range encoded in filename | loads completed activation batches and recomputes only missing batches, then rebuilds candidate directions, diagnostics, and provisional metadata |
| Stage 4A2 | `outputs/stage4/qwen3-14b/refusal_direction/checkpoints/stage4a2/` | `manifest.json`, `baseline_harmful_logits.pt`, `baseline_harmless_logits.pt`, `intervention_candidate_scores.checkpoint.jsonl` | `(position_index, position, layer)` | loads baseline logits when present and skips completed candidate intervention evaluations, then rebuilds final candidate-score and metrics JSON files |
| Stage 4B | `outputs/stage4/qwen3-14b/refusal_dampening/checkpoints/stage4b/` or the equivalent under the debug output directory | `manifest.json`, `per_example_refusal_components.checkpoint.jsonl` | `(goal_index, condition)` | skips completed prompt-condition rows, measures missing rows, then rebuilds `per_example_refusal_components.jsonl` and `refusal_dampening_summary.json` |

### CLI Resume Examples

Stage 4A1:

```bash
python -m poc_stage4.extract_refusal_direction \
  --model-name Qwen/Qwen3-14B \
  --output-dir outputs/stage4/qwen3-14b/refusal_direction \
  --num-harmful 64 \
  --num-harmless 64 \
  --positions=-1,-2,-3,-4 \
  --batch-size 1 \
  --enable-thinking false \
  --overwrite \
  --resume
```

Stage 4A2:

```bash
python -m poc_stage4.select_refusal_direction_interventions \
  --input-dir outputs/stage4/qwen3-14b/refusal_direction \
  --output-dir outputs/stage4/qwen3-14b/refusal_direction \
  --model-name Qwen/Qwen3-14B \
  --enable-thinking false \
  --batch-size 1 \
  --resume
```

Stage 4B:

```bash
python -m poc_stage4.measure_refusal_dampening \
  --model-name Qwen/Qwen3-14B \
  --direction-dir outputs/stage4/qwen3-14b/refusal_direction \
  --output-dir outputs/stage4/qwen3-14b/refusal_dampening \
  --enable-thinking false \
  --num-goals 2 \
  --resume
```

For a debug-only Stage 4B resume with a provisional direction, keep using the
debug output directory and explicit provisional flag:

```bash
python -m poc_stage4.measure_refusal_dampening \
  --model-name Qwen/Qwen3-14B \
  --direction-dir outputs/stage4/qwen3-14b/refusal_direction \
  --output-dir outputs/stage4/qwen3-14b/refusal_dampening_debug \
  --enable-thinking false \
  --dry-run \
  --num-goals 2 \
  --allow-provisional-direction \
  --resume
```

### SLURM Resume Examples

Stage 4A1:

```bash
sbatch --export=ALL,RESUME=true slurm_scripts/stage4a_qwen3_refusal_direction.slurm
```

Stage 4A2:

```bash
sbatch --export=ALL,RESUME=true slurm_scripts/stage4a2_qwen3_intervention_selection.slurm
```

Stage 4B:

```bash
sbatch --export=ALL,RESUME=true slurm_scripts/stage4b_qwen3_refusal_dampening.slurm
```

Use a custom checkpoint directory from SLURM:

```bash
sbatch --export=ALL,RESUME=true,CHECKPOINT_DIR=/path/to/checkpoints/stage4a2 \
  slurm_scripts/stage4a2_qwen3_intervention_selection.slurm
```

Suppress progress logging from SLURM:

```bash
sbatch --export=ALL,NO_PROGRESS=true slurm_scripts/stage4a2_qwen3_intervention_selection.slurm
```

### Operational Notes

- Final scientific outputs are written or rebuilt only after successful
  completion of the stage.
- Stage 4A2 full mode still updates `direction.pt` and `selected_direction.json`
  only after all required candidates complete and at least one candidate
  survives the filters.
- Stage 4B still rejects provisional Stage 4A1 directions by default. Resume
  does not bypass this guardrail; debug runs still need
  `--allow-provisional-direction`.
- Deleting a checkpoint directory forces a fresh run for that stage.
- If you intentionally change run settings, use a fresh checkpoint directory or
  delete the old one. Otherwise the fingerprint check will stop the run.
- Checkpoint files are intermediate state. The main scientific artifacts remain
  the stage outputs documented below.


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

## Stage 4B Refusal Dampening

Stage 4B measures the internal refusal-direction component for direct harmful
prompts versus CoT-hijacked variants. It requires a Stage 4A2 final direction by
default:

```json
"selection_status": "intervention_selected"
```

Provisional Stage 4A1 directions are rejected unless explicitly allowed for
debugging:

```bash
--allow-provisional-direction
```

Do not use provisional runs as scientific results.

Stage 4B uses existing Stage 2 artifacts by default:

```text
outputs/hijacking_baseline_gpt-o4-mini_small.jsonl
```

For each goal it measures:

- `direct_harmful`: the Stage 2 `goal`
- `hijacked_medium`: a middle-length Stage 2 `attack_prompt`
- `hijacked_long`: the longest Stage 2 `attack_prompt`

If medium and long resolve to the same attack prompt, the outputs record:

```json
"hijacked_medium_equals_long": true
```

Negative deltas mean dampening:

```text
delta = hijacked_component - direct_component
```

Stage 4B measures an internal refusal signal, not final behavioral jailbreak
success.

Dry-run command, after Stage 4A2 succeeds:

```bash
python -m poc_stage4.measure_refusal_dampening \
  --model-name Qwen/Qwen3-14B \
  --direction-dir outputs/stage4/qwen3-14b/refusal_direction \
  --output-dir outputs/stage4/qwen3-14b/refusal_dampening \
  --enable-thinking false \
  --dry-run \
  --num-goals 2
```

Debug-only provisional command:

```bash
python -m poc_stage4.measure_refusal_dampening \
  --model-name Qwen/Qwen3-14B \
  --direction-dir outputs/stage4/qwen3-14b/refusal_direction \
  --output-dir outputs/stage4/qwen3-14b/refusal_dampening \
  --enable-thinking false \
  --dry-run \
  --num-goals 2 \
  --allow-provisional-direction
```

SLURM dry run:

```bash
sbatch slurm_scripts/stage4b_qwen3_refusal_dampening.slurm
```

For `--num-goals 30`, provide a larger Stage 2 JSONL artifact:

```bash
python -m poc_stage4.measure_refusal_dampening \
  --model-name Qwen/Qwen3-14B \
  --direction-dir outputs/stage4/qwen3-14b/refusal_direction \
  --output-dir outputs/stage4/qwen3-14b/refusal_dampening \
  --enable-thinking false \
  --num-goals 30 \
  --stage2-jsonl <larger-stage2-artifact>.jsonl
```

## Stage 4C Qwen Report

Stage 4C aggregates Qwen3-14B Stage 4A1, Stage 4A2, and Stage 4B artifacts into
a derived report. It does not modify refusal directions, intervention metrics,
or dampening measurements.

Outputs:

```text
stage4_qwen_report.json
stage4_qwen_report.md
refusal_components_by_condition.csv
refusal_dampening_by_goal.csv
```

If `matplotlib` is available, Stage 4C also writes:

```text
refusal_component_by_condition.png
dampening_delta_by_goal.png
```

Debug or provisional inputs are rejected by default. Use
`--allow-debug-inputs` only for preliminary reports; those reports are clearly
marked as not final scientific evidence.

Debug report command:

```bash
python -m poc_stage4.build_stage4_report \
  --model-name Qwen/Qwen3-14B \
  --refusal-direction-dir outputs/stage4/qwen3-14b/refusal_direction \
  --refusal-dampening-dir outputs/stage4/qwen3-14b/refusal_dampening_debug \
  --output-dir outputs/stage4/qwen3-14b/report_debug \
  --allow-debug-inputs
```

Final report command, after Stage 4A2 and Stage 4B are final:

```bash
python -m poc_stage4.build_stage4_report \
  --model-name Qwen/Qwen3-14B \
  --refusal-direction-dir outputs/stage4/qwen3-14b/refusal_direction \
  --refusal-dampening-dir outputs/stage4/qwen3-14b/refusal_dampening \
  --output-dir outputs/stage4/qwen3-14b/report
```

SLURM debug report:

```bash
sbatch --export=ALL,ALLOW_DEBUG_INPUTS=true,REFUSAL_DAMPENING_DIR=/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood/outputs/stage4/qwen3-14b/refusal_dampening_debug,OUTPUT_DIR=/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood/outputs/stage4/qwen3-14b/report_debug \
  slurm_scripts/stage4c_qwen3_report.slurm
```

SLURM final report:

```bash
sbatch slurm_scripts/stage4c_qwen3_report.slurm
```
