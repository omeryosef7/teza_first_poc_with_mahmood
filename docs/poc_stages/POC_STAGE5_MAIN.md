# POC Stage 5 Main Documentation

## Manager Summary

Stage 5 added a read-only projection-dynamics analysis. It measures how Stage 2/3 examples project onto the saved Stage 4 refusal direction across hidden-state indices and token regions, while avoiding storage of raw prompt text, raw response text, token strings, hidden states, logits, or model outputs by default.

The stage is no longer just a smoke test in the current repo. There are now three completed artifact sets:

- smoke max-1: `1` example, `2` rows
- max-20 final: `20` examples, `60` rows
- max-100 final: `42` examples, `126` rows

The scientific caveat is unchanged: all Stage 5 runs still depend on the provisional Stage 4 direction.

## Comprehensive Detailed Summary

Stage 5 is a derived-analysis layer on top of existing artifacts:

- input examples come from the Stage 3 StrongREJECT-scored JSONL
- the direction comes from Stage 4
- the model is `Qwen/Qwen3-14B`
- outputs are compact numeric projection summaries only

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
- Run a small Qwen3 smoke test before scaling.
- Keep outputs shareable by default by excluding raw text and raw model internals.

## What We Actually Did

- Added the `poc_stage5` package.
- Added a generic smoke test Slurm script.
- Added core projection validation.
- Added Qwen3 max-1, max-20, and max-100 run paths.
- Ran the completed max-1 Qwen3 smoke job `384046`.
- Ran the completed max-20 Qwen3 job `384052`.
- Ran the completed max-100 Qwen3 job `384058`.
- Ran aggregate summarization for the completed outputs.

## Runs And Artifacts

| Run / Artifact | Path | What It Shows |
| --- | --- | --- |
| Stage 5 README | `poc_stage5/README.md` | Purpose, commands, safety policy, output schema, and troubleshooting. |
| Generic smoke script | `slurm_scripts/stage5_smoke_test.slurm` | Early Stage 5 smoke test configuration. |
| Core validation script | `slurm_scripts/stage5_projection_core_validation.slurm` | Projection utility validation. |
| Qwen3 smoke script | `slurm_scripts/stage5_qwen3_projection_smoke.slurm` | Completed max-1 Qwen3 smoke configuration. |
| Qwen3 max-20 script | `slurm_scripts/stage5_qwen3_max20_final.slurm` | Completed max-20 Qwen3 configuration. |
| Qwen3 max-100 script | `slurm_scripts/stage5_qwen3_max100_final.slurm` | Completed max-100 Qwen3 configuration. |
| Smoke summary | `outputs/stage5/qwen3-14b/smoke_max1_final/projection_summary.json` | 1 processed example, 2 rows, 0 failures. |
| Max-20 summary | `outputs/stage5/qwen3-14b/max20_final/projection_summary.json` | 20 processed examples, 60 rows, 0 failures. |
| Max-100 summary | `outputs/stage5/qwen3-14b/max100_final/projection_summary.json` | 42 processed examples, 126 rows, 0 failures. |
| Max-100 aggregate JSON | `outputs/stage5/qwen3-14b/max100_final/projection_aggregate_summary.json` | Region-level aggregate statistics over all 42 examples. |

## Timing From Git And Logs

| Timing Evidence | Value | Confidence |
| --- | --- | --- |
| Initial Stage 5 code committed | Commit `63ce2c0`, `2026-05-21T18:30:44+03:00` | git-window estimate |
| Stage 5 validation/smoke improvements committed | Commit `49067fb`, `2026-05-21T23:52:56+03:00` | git-window estimate |
| Additional Stage 5 work committed | Commit `5159fab`, `2026-05-22T08:30:48+03:00` | git-window estimate |
| Completed max-1 smoke end | `2026-05-22T06:01:26.257018+00:00` in `projection_summary.json` | exact from artifact |
| Completed max-20 end | `2026-05-22T06:31:28.152333+00:00` in `projection_summary.json` | exact from artifact |
| Completed max-100 end | `2026-05-22T07:13:37.231703+00:00` in `projection_summary.json` | exact from artifact |
| Slurm accounting | Not available from this shell because controller hostname resolution failed | unavailable |

## Results

### Smoke max-1

- loaded examples: `1`
- processed examples: `1`
- failed examples: `0`
- failed sequences: `0`
- rows written: `2`
- selected hidden-state index: `40`
- token regions: `final_token`, `last_8`

Aggregate max-1 values:

- final-token projection mean: `1.703125`
- last-8 projection mean: `-0.129150390625`

### Max-20 final

- loaded examples: `20`
- processed examples: `20`
- failed examples: `0`
- failed sequences: `0`
- rows written: `60`
- selected hidden-state index: `40`
- token regions: `final_token`, `last_8`, `last_32`

### Max-100 final

- loaded examples: `42`
- processed examples: `42`
- failed examples: `0`
- failed sequences: `0`
- rows written: `126`
- selected hidden-state index: `40`
- token regions: `final_token`, `last_8`, `last_32`

Max-100 aggregate summary by region:

| Region | Count | Mean projection | Success rate | Mean StrongREJECT |
| --- | ---: | ---: | ---: | ---: |
| `final_token` | 42 | `-0.05113002232142857` | `0.09523809523809523` | `0.07142857142857142` |
| `last_8` | 42 | `-0.023778279622395832` | `0.09523809523809523` | `0.07142857142857142` |
| `last_32` | 42 | `0.016065733773367747` | `0.09523809523809523` | `0.07142857142857142` |

Explicit readout:

- the largest positive region-level mean in the completed max-100 run is `last_32` at `0.016065733773367747`
- the most negative region-level mean is `final_token` at `-0.05113002232142857`
- these values are small because Stage 5 is measuring attack-prompt rows against a direction learned in Stage 4A1 from a separate harmful-versus-harmless extraction dataset

## What The Main Metrics Mean

- `selected_hidden_state_indices = [40]`: the run measured only the final hidden-state index that corresponds to `--layers -1` for this model.
- `token_regions = final_token,last_8,last_32`: where in the prompt representation the direction projection is aggregated. `final_token` uses just the last token; `last_8` and `last_32` average over the final 8 or 32 tokens available in the prompt window.
- `projection_value` / `projection_mean`: signed projection of the hidden representation onto the Stage 4 refusal direction. More positive means more aligned with the harmful-side direction discovered in Stage 4A1; more negative means more aligned with the opposite direction.
- `projection_abs_mean`: average magnitude of the projection regardless of sign.
- `failed_sequences`: number of sequence-level computations that failed even if the example itself loaded successfully.
- `rows_written`: number of per-example, per-region output rows emitted by the run.
- `success_rate`: fraction of rows in a group whose inherited Stage 2/3 label is successful.
- `mean_strongreject_score`: average Stage 3 StrongREJECT score for the rows in a group.

## Limitations / Caveats

- Stage 5 currently uses the Stage 4 provisional direction. That is acceptable for derived analysis but not final mechanistic evidence.
- Stage 5 output safety is deliberate: raw prompts, raw responses, token strings, hidden states, logits, and raw model outputs are not written by default.
- Projection sign should be interpreted relative to the Stage 4A1 extraction convention, not as a universal notion of refusal on its own.

## Relation to Goal Pipeline (Qwen3-14B Full Token Capture)

Stage 5 is the first projection-analysis stage after the behavioral pipeline. Its role once Stage 2B completes:

- Stage 5 currently projects **gpt-o4-mini attack prompts** onto Qwen3-14B's refusal direction. This measures how Qwen3-14B's hidden state responds to attack prompts designed for a different model.
- After Stage 2B runs, Stage 5 can be re-run with Stage 2B's JSONL as input. That run would project **Qwen3-14B's own responses** onto the refusal direction — a tighter pairing.
- No code changes are required: the `--input-jsonl` and `--condition` flags already support new input sources.

Current Stage 5 data (42 examples from gpt-o4-mini attack prompts) is still valid for its original purpose — it shows how Qwen3-14B's internal representation responds to those attack texts at the prompt level.

## Handoff To Next Stage

Stage 6 can now work from a completed Stage 5 base rather than only a smoke run, while later scientific interpretation should still wait for a final Stage 4A2 `intervention_selected` direction. Once Stage 2B completes, re-run Stage 5 with Stage 2B JSONL to align behavioral and mechanistic data on the same model.
