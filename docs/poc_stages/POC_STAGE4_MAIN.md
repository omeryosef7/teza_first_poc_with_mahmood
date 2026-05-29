# POC Stage 4 Main Documentation

## Manager Summary

Stage 4 began the mechanistic part of the POC. It added Qwen3-14B refusal-direction extraction, intervention-based candidate selection, refusal-component dampening measurement, checkpoint/resume support, and report generation.

The main explicit Stage 4A1 result is that the current best provisional candidate in the repo is the direction at prompt-end-relative position `-3` and layer `22`. Its saved projection-diagnostic score is `14.166624327994466`, with harmful projection mean `61.89002990722656` and harmless projection mean `-3.606233596801758`.

The main scientific caveat remains unchanged: this is only a provisional winner. Stage 4A2 did not produce a final `intervention_selected` direction, so Stage 4 is still not final mechanistic evidence.

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
- Add intervention selection so the project would not mistake projection diagnostics for final scientific evidence.
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
- Ran a smoke test first, then a fuller intervention-selection pass whose metrics are now present in `intervention_selection_metrics.json`.
- Evaluated all 160 candidates in the final recorded artifact.
- Found zero candidates surviving the intervention filters.
- Did not overwrite `direction.pt` because no candidate was promoted to final.

### Stage 4B

- Added refusal-component dampening measurement.
- Ran a debug-only dampening measurement for 2 goals.
- Explicitly allowed the provisional direction for debugging.
- Wrote per-example components and a summary under `outputs/stage4/qwen3-14b/refusal_dampening_debug/`.

### Stage 4C

- Added report-building code.
- Built a debug report from provisional/debug inputs.
- Wrote JSON, Markdown, and CSV report artifacts under `outputs/stage4/qwen3-14b/report_debug/`.

## Runs And Artifacts

| Stage | Run / Artifact | Path | What It Shows |
| --- | --- | --- | --- |
| 4A1 | Stage 4 README | `poc_stage4/README.md` | Commands, guardrails, resume behavior, and stage structure. |
| 4A1 | Slurm script | `slurm_scripts/stage4a_qwen3_refusal_direction.slurm` | Candidate extraction batch configuration. |
| 4A1 | Final stdout | `logs/poc_stage4a_qwen3_refusal_381185.out` | Stage 4A1 artifact write and selected provisional position/layer. |
| 4A1 | Extraction metrics | `outputs/stage4/qwen3-14b/refusal_direction/extraction_metrics.json` | 64/64 prompts, candidate shape, model metadata. |
| 4A1 | Selected direction metadata | `outputs/stage4/qwen3-14b/refusal_direction/selected_direction.json` | Saved provisional winner and selection warning. |
| 4A1 | Projection diagnostics | `outputs/stage4/qwen3-14b/refusal_direction/projection_diagnostics.json` | Per-position, per-layer separation diagnostics for all 160 candidates. |
| 4A2 | Slurm script | `slurm_scripts/stage4a2_qwen3_intervention_selection.slurm` | Intervention-selection batch configuration. |
| 4A2 | Intervention metrics | `outputs/stage4/qwen3-14b/refusal_direction/intervention_selection_metrics.json` | Final recorded intervention-selection result: 160 evaluated, 0 survivors. |
| 4A2 | Ongoing checkpoint evidence | `outputs/stage4/qwen3-14b/refusal_direction/checkpoints/stage4a2/` | Baseline logits, manifest, and candidate-score checkpoint rows. |
| 4B | Slurm script | `slurm_scripts/stage4b_qwen3_refusal_dampening.slurm` | Debug dampening batch configuration. |
| 4B | Debug summary | `outputs/stage4/qwen3-14b/refusal_dampening_debug/refusal_dampening_summary.json` | Debug-only dampening results. |
| 4C | Slurm script | `slurm_scripts/stage4c_qwen3_report.slurm` | Report generation configuration. |
| 4C | Debug report | `outputs/stage4/qwen3-14b/report_debug/stage4_qwen_report.md` | Aggregated preliminary report. |

## Timing From Git And Logs

| Timing Evidence | Value | Confidence |
| --- | --- | --- |
| Refusal-direction upstream code added | Commit `0a21439`, `2026-05-20T19:42:02+03:00` | git-window estimate |
| Stage 4A1 code added | Commit `50558ba`, `2026-05-20T20:35:18+03:00` | git-window estimate |
| Stage 4A1 artifact timestamp | `2026-05-20T18:19:49.875450+00:00`, or `21:19:49 IDT` | exact from artifact |
| Stage 4A2 final metrics timestamp | `2026-05-22T13:44:16.530935+00:00`, or `16:44:16 IDT` | exact from artifact |
| Stage 4B debug summary timestamp | `2026-05-21T06:42:13.022752+00:00`, or `09:42:13 IDT` | exact from artifact |
| Stage 4C debug report committed | Commit `0c70f8e`, `2026-05-21T10:59:21+03:00` | git-window estimate |
| Slurm accounting | Not available from this shell because controller hostname resolution failed | unavailable |

## Results

### Stage 4A1 explicit winning candidate

The provisional winning candidate currently saved in the repo is:

- position `-3`
- layer `22`
- `selection_status = provisional_projection_diagnostic_only`
- `selected_score = 14.166624327994466`
- harmful projection mean `61.89002990722656`
- harmless projection mean `-3.606233596801758`
- `direction_norm = 1.0`

Other Stage 4A1 facts:

- Candidate tensor shape: `[4, 40, 5120]`
- Candidate count: `160`
- Positions tested: `[-1, -2, -3, -4]`
- Layers tested: `40`
- Diagnostic summary mean standardized separation: `6.664061363336008`

Comparison note:

- The saved provisional winner is the best candidate by standardized projection separation.
- The strongest raw `projection_separation` in the diagnostics appears later in the same position family, at position `-3`, layer `39`, with raw separation `600.2092590332031`.
- That layer `39` candidate was not selected because its standardized separation `13.375142479999504` is lower than the saved layer `22` winner's `14.166624327994466`.

### Stage 4A2 explicit intervention result

The latest recorded Stage 4A2 artifact says:

- `selection_status = intervention_selection_failed_no_survivors`
- candidates available: `160`
- candidates evaluated: `160`
- candidates surviving filters: `0`
- baseline harmful refusal score mean: `3.962426360306912`
- baseline harmless refusal score mean: `-15.66423998503984`

Failure counts by reason:

- `steering_below_threshold = 160`
- `kl_above_threshold = 92`
- `layer_pruned = 32`

Best tradeoff candidate recorded by Stage 4A2:

- position `-1`, layer `9`
- harmful ablation refusal score `3.7349283246606917`
- harmless steering refusal score `-15.627660489174787`
- harmless ablation KL divergence `0.04825110056550176`
- still failed the steering threshold, so it was not promoted

### Stage 4B explicit debug result

- goals measured: `2`
- direct harmful mean refusal component: `61.433319091796875`
- hijacked medium mean refusal component: `2.553408205509186`
- hijacked long mean refusal component: `3.2049278020858765`
- mean medium delta: `-58.87991088628769`
- mean long delta: `-58.228391289711`
- fraction of negative medium deltas: `1.0`
- fraction of negative long deltas: `1.0`
- scientific status: `debug_only_not_final_evidence`

### Stage 4C explicit report result

- report status: `debug_preliminary`
- output report path: `outputs/stage4/qwen3-14b/report_debug/stage4_qwen_report.md`

## What The Main Metrics Mean

- `projection_separation`: the raw difference between harmful and harmless projection means for one candidate direction. Larger absolute separation means the candidate distinguishes the two prompt classes more in raw units.
- `pooled_projection_std`: the pooled spread of the harmful and harmless projections. Larger values mean the classes are more internally noisy.
- `standardized_projection_separation`: separation normalized by spread. Larger is better if the goal is to find a clean separator rather than just a large raw difference.
- `selected_score`: the actual selection score for the saved candidate. In Stage 4A1 it is the standardized projection separation used by the provisional diagnostic.
- `direction_norm`: norm of the saved direction vector. `1.0` means the stored direction was normalized.
- `selection_status = provisional_projection_diagnostic_only`: the candidate won the Stage 4A1 diagnostic, but it was not validated by intervention selection.
- `harmful_projection_mean`: mean projection of harmful validation prompts onto the candidate direction.
- `harmless_projection_mean`: mean projection of harmless validation prompts onto the candidate direction.
- `harmful_ablation_refusal_score`: Stage 4A2's intervention metric on harmful prompts after ablating a candidate direction. Lower is intended to mean less refusal after ablation.
- `harmless_steering_refusal_score`: Stage 4A2's intervention metric on harmless prompts after steering in the candidate direction. The filter expects this not to induce refusal-like behavior.
- `harmless_ablation_kl_divergence`: how much the harmless output distribution moved under ablation. Lower is safer.
- `mean_delta_medium` / `mean_delta_long`: average difference between the direct harmful refusal component and the hijacked refusal component. Negative means dampening relative to direct harmful prompts.

Interpretation rule for this stage:

- Larger positive projection on the selected Stage 4A1 direction means stronger alignment with the harmful-side direction found during extraction.
- More negative or smaller values mean weaker alignment with that harmful-side direction.

## Limitations / Caveats

- The current best candidate is explicit, but it is still only provisional.
- No final `intervention_selected` direction exists yet.
- Stage 4A2's latest recorded artifact says no candidate survived the scientific filters.
- Stage 4B used `--allow-provisional-direction`, so it validates the measurement path but is not final evidence.
- Stage 4C report is intentionally marked debug/preliminary.
- Qwen3-14B runs are resource-heavy and some layers were placed on CPU according to the extraction metrics.

## Relation to Goal Pipeline (Qwen3-14B Full Token Capture)

Stage 4 is the mechanistic backbone of the pipeline. Its role in relation to the goal pipeline:

- **Model loading infrastructure** (`poc_stage4/qwen3_model.py`): directly reused in Stage 2B's `runner.py` via `from poc_stage4.qwen3_model import load_qwen3_model`. Stage 2B does NOT depend on the refusal direction.
- **Refusal direction** (`direction.pt`, status: provisional): used by Stages 5/6/7 for projection analysis but NOT required for Stage 2B's behavioral measurement.
- **Stage 4B dampening result** (mean delta ~−58 points for hijacked prompts): this is a mechanistic signal that CoT hijacking reduces Qwen3-14B's internal refusal component. Stage 2B will measure the behavioral counterpart: does the model actually produce harmful output when internally dampened?

Key open issue: Stage 4A2 found 0 candidates surviving intervention filters. The provisional direction from Stage 4A1 (position −3, layer 22) is still the only saved direction. Projection analysis in Stages 5/6/7 is based on this provisional direction and should be treated as exploratory.

## Handoff To Next Stage

Stage 5 can use the existing Stage 4 direction for read-only projection-dynamics analysis, but final mechanistic claims should wait for a completed Stage 4A2 `intervention_selected` direction. Stage 2B is independent of Stage 4 and can run in parallel.
