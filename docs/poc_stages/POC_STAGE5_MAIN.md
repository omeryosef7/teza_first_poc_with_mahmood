# POC Stage 5 Main Documentation

## Manager Summary

Stage 5 added a read-only projection-dynamics analysis. It measures how Stage 2/3 examples project onto an existing Stage 4 refusal direction across HuggingFace hidden-state indices and token regions, while avoiding storage of raw prompt text, raw response text, token strings, hidden states, logits, or model outputs by default.

The completed Qwen3 smoke run processed 1 example, wrote 2 projection rows, and passed output validation. A later max-20 run was started but did not complete in the available artifacts; its temporary output files are empty and should be treated as incomplete.

## Comprehensive Detailed Summary

Stage 5 was designed to be a safe, derived-analysis layer on top of existing artifacts:

- Input examples come from the Stage 3 StrongREJECT-scored JSONL.
- The direction comes from Stage 4.
- The model is `Qwen/Qwen3-14B`.
- Outputs are compact numeric projection summaries only.

The key implementation modules are:

- `poc_stage5/data_loading.py`
- `poc_stage5/direction_loading.py`
- `poc_stage5/projection.py`
- `poc_stage5/compute_refusal_projection_dynamics.py`
- `poc_stage5/summarize_refusal_projection_dynamics.py`

The compute step writes one row per example, sequence type, hidden-state index, and token region. The summarizer groups by condition, sequence type, hidden-state index, and region.

## What We Tried

- Build a read-only mechanistic projection stage that does not mutate Stage 2, Stage 3, or Stage 4 artifacts.
- Validate data loading, direction loading, projection math, and output safety constraints.
- Run a small Qwen3 smoke test before scaling to a max-20 analysis.
- Keep outputs shareable by default by excluding raw text and raw model internals.

## What We Actually Did

- Added the `poc_stage5` package.
- Added a generic smoke test Slurm script.
- Added core projection validation.
- Added a Qwen3 max-1 smoke Slurm script.
- Added a Qwen3 max-20 Slurm script.
- Ran the completed max-1 Qwen3 smoke job `384046`.
- Ran the aggregate summarizer for the max-1 smoke output.
- Started max-20 job `384052`, which did not complete in the current artifacts.

## Runs And Artifacts

| Run / Artifact | Path | What It Shows |
| --- | --- | --- |
| Stage 5 README | `poc_stage5/README.md` | Purpose, commands, safety policy, output schema, and troubleshooting. |
| Generic smoke script | `slurm_scripts/stage5_smoke_test.slurm` | Early Stage 5 smoke test configuration. |
| Core validation script | `slurm_scripts/stage5_projection_core_validation.slurm` | Projection utility validation. |
| Qwen3 smoke script | `slurm_scripts/stage5_qwen3_projection_smoke.slurm` | Completed max-1 Qwen3 smoke configuration. |
| Qwen3 max-20 script | `slurm_scripts/stage5_qwen3_max20_final.slurm` | Larger analysis attempt configuration. |
| Completed smoke stdout | `logs/poc_stage5_qwen3_smoke_384046.out` | Help check, compute run, output validation, clean Stage 2/3/4 diff check. |
| Completed smoke stderr | `logs/poc_stage5_qwen3_smoke_384046.err` | Direction/model loading, one processed example, completion line. |
| Completed smoke JSONL | `outputs/stage5/qwen3-14b/smoke_max1_final/per_example_layer_region_projections.jsonl` | 2 compact projection rows. |
| Completed smoke summary | `outputs/stage5/qwen3-14b/smoke_max1_final/projection_summary.json` | 1 processed example, 2 rows, 0 failures. |
| Completed smoke aggregate JSON | `outputs/stage5/qwen3-14b/smoke_max1_final/projection_aggregate_summary.json` | 2 grouped summaries. |
| Completed smoke aggregate CSV | `outputs/stage5/qwen3-14b/smoke_max1_final/projection_aggregate_summary.csv` | CSV version of aggregate groups. |
| Max-20 stdout | `logs/poc_stage5_qwen3_max20_384052.out` | Started max-20 job and reached compute launch. |
| Max-20 stderr | `logs/poc_stage5_qwen3_max20_384052.err` | Model loading and first progress line. |
| Max-20 temporary outputs | `outputs/stage5/qwen3-14b/max20_final/*.tmp` | Currently empty; incomplete run evidence only. |

## Timing From Git And Logs

| Timing Evidence | Value | Confidence |
| --- | --- | --- |
| Initial Stage 5 code committed | Commit `63ce2c0`, `2026-05-21T18:30:44+03:00` | git-window estimate |
| Stage 5 validation/smoke improvements committed | Commit `49067fb`, `2026-05-21T23:52:56+03:00` | git-window estimate |
| Additional Stage 5 work committed | Commit `5159fab`, `2026-05-22T08:30:48+03:00` | git-window estimate |
| Completed max-1 smoke start | `2026-05-22T05:56:17.270965+00:00` in `projection_summary.json` | exact from artifact |
| Completed max-1 smoke end | `2026-05-22T06:01:26.257018+00:00` in `projection_summary.json` | exact from artifact |
| Completed max-1 smoke duration | About 5 minutes 9 seconds | exact from artifact |
| Aggregate summarizer duration | `2026-05-22T06:06:50.447415+00:00` to `2026-05-22T06:06:50.448060+00:00` | exact from artifact |
| Max-20 attempt progress | First progress line at `2026-05-22T06:25:01.719742+00:00` in stderr | estimated from logs |
| Slurm accounting | Not available from this shell because controller hostname resolution failed | unavailable |

## Results

Completed max-1 smoke:

- Input JSONL: `outputs/hijacking_baseline_gpt-o4-mini_small_strongreject.jsonl`.
- Direction path: `outputs/stage4/qwen3-14b/refusal_direction/direction.pt`.
- Model: `Qwen/Qwen3-14B`.
- Loaded examples: 1.
- Processed examples: 1.
- Failed examples: 0.
- Failed sequences: 0.
- Rows written: 2.
- Hidden-state index selected from `--layers -1`: 40.
- Token regions: `final_token`, `last_8`.
- Raw text stored: no.
- Text hashes stored: no.
- Response context included: no.

Aggregate max-1 smoke:

- Input rows: 2.
- Groups: 2.
- Group fields: `condition`, `sequence_type`, `hidden_state_index`, `region`.
- Final-token projection mean for the single example: `1.703125`.
- Last-8 projection mean for the single example: `-0.129150390625`.

Max-20 attempt:

- Configured for 20 examples, final hidden state, and regions `final_token,last_8,last_32`.
- Log shows model loading and processing started.
- Current `.tmp` projection and error files are empty.
- No completed summary JSON, aggregate JSON, or aggregate CSV exists for max-20 in the current artifact set.

## Limitations / Caveats

- Stage 5 currently uses the Stage 4 provisional direction. That is acceptable for smoke testing but not final mechanistic evidence.
- The completed Qwen3 smoke run is intentionally tiny: one example.
- The max-20 run is incomplete in the current workspace.
- One completed smoke log reports CUDA initialization warning and apparent CPU fallback behavior; this should be considered when interpreting timing and scalability.
- Stage 5 output safety is deliberate: raw prompts, raw responses, token strings, hidden states, logits, and raw model outputs are not written by default.

## Handoff To Next Stage

The immediate next useful step is to complete or rerun the max-20 Stage 5 analysis after confirming GPU availability, then repeat Stage 5 with a final Stage 4A2 `intervention_selected` direction once that exists.
