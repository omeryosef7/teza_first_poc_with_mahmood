# Stage 4.8 Extension Plan

_Generated: 2026-06-11T14:39:45.397867Z_

## Rationale

The original Stage 4.8 run (60 generations: 4 goals × 3 conditions × 5 seeds)
produced only 3 matched-outcome cells (cells with ≥1 success AND ≥1 failure).
The threshold for behavior-conditioned direction extraction is 4 matched cells.

Goals 0 and 2 showed intermediate success probability (0 < success_rate < 1 in at
least one condition), making them the best candidates for producing matched cells
with more seeds.

## Extension Parameters

- **Target goals:** 0, 2
- **Conditions:** A, D, F
- **New seeds:** 106–115
- **Total new generations:** 60
  (2 goals × 3 conditions × 10 seeds = 60)

## Model Configuration (unchanged from original)

- Model: `Qwen/Qwen3-14B`
- Revision: `40c069824f4251a91eefaf281ebe4c544efd3e18`
- `do_sample=True`, `temperature=0.7`, `top_p=0.95`
- `max_new_tokens=32768`, `enable_thinking=True`

## Source Examples Selected

| Goal | Source Example ID | Selection Stratum |
|------|-----------------|------------------|
| 0 | `goal_index=0|attack_iteration=1|conversation_id=5|target_model=gpt-o4-mini` | upper |
| 2 | `goal_index=2|attack_iteration=1|conversation_id=3|target_model=gpt-o4-mini` | middle |

## Extension Run Directory

`/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood/outputs/stage4_8/runs/run_array_extension_20260611_143945`

## SLURM Command

```bash
# Submit extension job (2 goals as SLURM array tasks 0 and 2)
MANIFEST="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood/outputs/stage4_8/runs/$(basename /home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood/outputs/stage4_8/runs/run_array_extension_20260611_143945)/extension_manifest.jsonl"
RUN_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood/outputs/stage4_8/runs/run_array_extension_20260611_143945"
sbatch \
  --array=0,2 \
  --export=ALL,RUN_DIR="$RUN_DIR",MANIFEST="$MANIFEST" \
  slurm_scripts/stage4_8_repeated_generations_array.slurm
```

> **Note:** The existing `run_repeated_generations.py` script is resume-safe.
> It skips any run_id already present in `run_summary.jsonl`.
> Point it at the extension manifest and the extension run dir.

## After Running

Run `analyze_stage48_extension.py` to combine original + extension and check threshold:
```bash
python -m poc_meeting.mahmood_48h_update.analyze_stage48_extension \
    --output-dir outputs/meeting/mahmood_48h_update_20260611_143740
```

## Safety Constraints

- Do NOT alter harmful target text in the prompts.
- Prompts are referenced by source_example_id only; not printed in logs.
- Output artifacts must not include raw harmful target text.