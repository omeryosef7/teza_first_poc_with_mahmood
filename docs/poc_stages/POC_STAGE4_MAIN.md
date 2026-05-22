# POC Stage 4 Main Documentation

## Manager Summary

Stage 4 began the mechanistic part of the POC. It added Qwen3-14B refusal-direction extraction, intervention-based candidate selection, refusal-component dampening measurement, checkpoint/resume support, and report generation.

The important scientific caveat is that Stage 4 is not final evidence yet. Stage 4A1 produced a provisional projection-selected direction. Stage 4A2 smoke-tested intervention selection over 5 candidates but did not produce an `intervention_selected` final direction. Stage 4B measured dampening in debug mode with the provisional direction. Stage 4C produced a debug report clearly marked as preliminary.

## Comprehensive Detailed Summary

Stage 4 was split into four sub-stages:

- Stage 4A1: extract candidate refusal directions for `Qwen/Qwen3-14B`.
- Stage 4A2: select a direction using intervention-style metrics.
- Stage 4B: measure refusal-component dampening across prompt conditions.
- Stage 4C: aggregate Stage 4 artifacts into a report.

The work reused the vendored refusal-direction datasets under `Chain_of_Thought_Hijacking/refusal_direction/dataset/splits/` and adapted the direction workflow for Qwen3-14B. It also added run-state/checkpoint machinery so long cluster runs could resume safely.

Stage 4A1 used 64 harmful and 64 harmless prompts, split internally into 48/48 train and 16/16 validation prompts. It generated a candidate tensor with shape `[4, 40, 5120]`, representing 4 prompt-end-relative positions, 40 model layers, and hidden size 5120.

## What We Tried

- Move beyond black-box attack logs into hidden-state/refusal-direction analysis.
- Use Qwen3-14B as the open-source model target for mechanistic probing.
- Reproduce the refusal-direction idea with candidate directions across positions and layers.
- Add intervention selection to avoid treating projection diagnostics as final scientific evidence.
- Measure whether hijacked prompt variants reduce the refusal-direction component compared with direct harmful prompts.

## What We Actually Did

### Stage 4A1

- Added `poc_stage4` model loading, activation capture, candidate-direction, projection-diagnostic, and schema modules.
- Ran Qwen3-14B candidate extraction.
- Wrote Stage 4A1 artifacts under `outputs/stage4/qwen3-14b/refusal_direction/`.
- Produced a provisional direction at position `-3`, layer `22`.
- Marked that direction as `provisional_projection_diagnostic_only`.

### Stage 4A2

- Added intervention-based selection code and Slurm support.
- Ran a smoke test over the top 5 projection-ranked candidates.
- Wrote intervention candidate scores and metrics.
- Did not overwrite `direction.pt` because smoke mode did not produce a final direction.
- Longer/checkpointed Stage 4A2 work continued later, visible in checkpoint artifacts and `logs/poc_stage4a2_qwen3_select_382351.err`, but no final `intervention_selected` artifact is present.

### Stage 4B

- Added refusal-component dampening measurement.
- Ran debug-only dampening measurement for 2 goals.
- Explicitly allowed the provisional direction for debugging.
- Wrote per-example components and a summary under `outputs/stage4/qwen3-14b/refusal_dampening_debug/`.

### Stage 4C

- Added report-building code.
- Built a debug report from the provisional/debug inputs.
- Wrote JSON, Markdown, and CSV report artifacts under `outputs/stage4/qwen3-14b/report_debug/`.

## Runs And Artifacts

| Stage | Run / Artifact | Path | What It Shows |
| --- | --- | --- | --- |
| 4A1 | Stage 4 README | `poc_stage4/README.md` | Commands, guardrails, resume behavior, and stage structure. |
| 4A1 | Slurm script | `slurm_scripts/stage4a_qwen3_refusal_direction.slurm` | Candidate extraction batch configuration. |
| 4A1 | Final stdout | `logs/poc_stage4a_qwen3_refusal_381185.out` | Stage 4A1 artifact write and selected provisional position/layer. |
| 4A1 | Extraction metrics | `outputs/stage4/qwen3-14b/refusal_direction/extraction_metrics.json` | 64/64 prompts, shape `[4, 40, 5120]`, model metadata. |
| 4A1 | Selected direction metadata | `outputs/stage4/qwen3-14b/refusal_direction/selected_direction.json` | `selection_status = provisional_projection_diagnostic_only`. |
| 4A2 | Slurm script | `slurm_scripts/stage4a2_qwen3_intervention_selection.slurm` | Intervention-selection batch configuration. |
| 4A2 | Smoke stdout | `logs/poc_stage4a2_qwen3_select_381263.out` | Smoke mode wrote metrics and did not overwrite direction. |
| 4A2 | Intervention metrics | `outputs/stage4/qwen3-14b/refusal_direction/intervention_selection_metrics.json` | 5 candidates evaluated, 0 surviving filters, smoke mode. |
| 4A2 | Ongoing checkpoint evidence | `outputs/stage4/qwen3-14b/refusal_direction/checkpoints/stage4a2/` | Baseline logits, manifest, and candidate-score checkpoint rows. |
| 4B | Slurm script | `slurm_scripts/stage4b_qwen3_refusal_dampening.slurm` | Debug dampening batch configuration. |
| 4B | Debug stdout | `logs/poc_stage4b_qwen3_dampen_382303.out` | Measured 2 goals and wrote debug summary. |
| 4B | Debug summary | `outputs/stage4/qwen3-14b/refusal_dampening_debug/refusal_dampening_summary.json` | Debug-only dampening results. |
| 4C | Slurm script | `slurm_scripts/stage4c_qwen3_report.slurm` | Report generation configuration. |
| 4C | Debug report | `outputs/stage4/qwen3-14b/report_debug/stage4_qwen_report.md` | Aggregated preliminary report. |

## Timing From Git And Logs

| Timing Evidence | Value | Confidence |
| --- | --- | --- |
| Refusal-direction upstream code added | Commit `0a21439`, `2026-05-20T19:42:02+03:00` | git-window estimate |
| Stage 4A1 code added | Commit `50558ba`, `2026-05-20T20:35:18+03:00` | git-window estimate |
| Stage 4A1 artifact timestamp | `2026-05-20T18:19:49.875450+00:00`, or `21:19:49 IDT` | exact from artifact |
| Stage 4A2 smoke metrics timestamp | `2026-05-20T19:40:10.120846+00:00`, or `22:40:10 IDT` | exact from artifact |
| Stage 4B debug summary timestamp | `2026-05-21T06:42:13.022752+00:00`, or `09:42:13 IDT` | exact from artifact |
| Stage 4C debug report committed | Commit `0c70f8e`, `2026-05-21T10:59:21+03:00` | git-window estimate |
| Longer Stage 4A2 checkpoint work | Commit `90f71aa` at `2026-05-21T18:02:04+03:00` and later dirty log/checkpoint updates | git-window estimate |
| Slurm accounting | Not available from this shell because controller hostname resolution failed | unavailable |

## Results

Stage 4A1 results:

- Model: `Qwen/Qwen3-14B`.
- Candidate shape: `[4, 40, 5120]`.
- Positions: `[-1, -2, -3, -4]`.
- Layers: 40.
- Provisional selected position: `-3`.
- Provisional selected layer: `22`.
- Selection status: `provisional_projection_diagnostic_only`.

Stage 4A2 smoke results:

- Candidates available: 160.
- Candidates evaluated: 5.
- Candidates surviving filters: 0.
- Selection status: `intervention_smoke_test_only`.
- Direction was not promoted to final.

Stage 4B debug results:

- Goals measured: 2.
- Direct harmful mean refusal component: `61.433319091796875`.
- Hijacked medium mean component: `2.553408205509186`.
- Hijacked long mean component: `3.2049278020858765`.
- Mean medium delta: `-58.87991088628769`.
- Mean long delta: `-58.228391289711`.
- Scientific status: `debug_only_not_final_evidence`.

Stage 4C result:

- Generated debug report with explicit warnings.
- Report status: `debug_preliminary`.

## Limitations / Caveats

- No final `intervention_selected` direction exists yet.
- Stage 4B used `--allow-provisional-direction`, so it validates the measurement path but is not final evidence.
- Stage 4C report is intentionally marked debug/preliminary.
- Some Stage 4A2 checkpoint artifacts and logs are still dirty/uncommitted in the working tree and should not be overwritten.
- Qwen3-14B runs are resource-heavy and some layers were placed on CPU according to the extraction metrics.

## Handoff To Next Stage

Stage 5 can use the existing Stage 4 direction for read-only projection-dynamics smoke tests, but final mechanistic claims should wait for a completed Stage 4A2 `intervention_selected` direction and a non-debug Stage 4B run.
