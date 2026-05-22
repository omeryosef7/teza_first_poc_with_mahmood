# POC Stage 1 Main Documentation

## Manager Summary

Stage 1 was the repo audit and feasibility-planning stage. We inspected the three imported codebases, identified what could be reused, and concluded that the existing Chain-of-Thought Hijacking repo could support a black-box attack baseline but not the mechanistic refusal-direction analysis by itself.

The practical outcome was a clear next step: build a thin structured wrapper around the Hijacking repo before attempting StrongREJECT scoring or hidden-state analysis. No expensive model run was performed in this stage.

## Comprehensive Detailed Summary

Stage 1 covered three local repositories:

- `Chain_of_Thought_Hijacking/Hijacking`
- `AutoInject/AutoInject`
- `strong_reject/strong_reject`

The audit found that `Chain_of_Thought_Hijacking/Hijacking` already had a usable attack workflow: it loads harmful goals, initializes attacker and target models, generates iterative adversarial prompts, queries a target model, and asks a judge model to score the result. It also had command-line support for supported API-backed target models, including `gpt-o4-mini`.

The same audit found that this repo did not provide the later mechanistic pieces we needed: no local open-source model inference pipeline, no hidden-state capture, no refusal-direction extraction, no layerwise refusal-component analysis, and no controlled CoT-prefix-length sweep.

`AutoInject/AutoInject` was considered broader but not immediately useful for the first POC path because it appeared less complete for direct reuse and had cluster-specific assumptions. `strong_reject/strong_reject` looked clean and useful for later evaluation, but not for Stage 1 execution.

## What We Tried

- Identify whether the imported repos already solved the intended research problem.
- Find an immediate reproducibility target that could be run without designing a new experiment system.
- Decide whether to adapt the existing Hijacking repo directly, build a separate wrapper, or pivot to AutoInject.

## What We Actually Did

- Audited the repo structure, entry points, supported models, prompt sources, logging behavior, and output behavior.
- Confirmed that `Chain_of_Thought_Hijacking/Hijacking/main.py` is the main executable attack entry point.
- Confirmed that the Hijacking repo logs useful data but does not emit clean research artifacts by default.
- Wrote the Stage 1 audit and next-step documents:
  - `POC_STAGE1_REPO_AUDIT.md`
  - `POC_STAGE1_NEXT_STEP.md`
- Defined the exact Stage 2 implementation target: a clean wrapper that emits normalized JSONL and summary JSON artifacts.

## Runs And Artifacts

| Item | Evidence | Notes |
| --- | --- | --- |
| Repo audit | `POC_STAGE1_REPO_AUDIT.md` | Full inspection of imported repos and their suitability. |
| Next-step design | `POC_STAGE1_NEXT_STEP.md` | Specifies the Stage 2 wrapper and result schema. |
| Imported repos | `AutoInject/AutoInject`, `Chain_of_Thought_Hijacking/Hijacking`, `strong_reject/strong_reject` | External code was brought into the project before and during this phase. |
| Stage 2 target schema | `POC_STAGE1_NEXT_STEP.md` | Defined fields such as `goal`, `attack_prompt`, `target_response`, `judge_score`, and `is_success`. |

No model run artifacts were expected from Stage 1.

## Timing From Git And Logs

| Timing Evidence | Value | Confidence |
| --- | --- | --- |
| Imported external repos | Commit `a4cec72`, `2026-05-17T19:30:48+03:00` | git-window estimate |
| Stage 1 audit plus Stage 2 wrapper seed committed | Commit `c13233f`, `2026-05-17T20:25:36+03:00` | git-window estimate |
| Approximate Stage 1 planning window | About 55 minutes between the two commits above | git-window estimate |
| Model execution time | None | exact from absence of Stage 1 run artifacts |

Slurm accounting was not used for Stage 1. Later `sacct/squeue` checks from this shell failed because the Slurm controller hostname could not be resolved, so this documentation uses git and local artifacts rather than Slurm accounting.

## Results

- Stage 1 established that a black-box baseline was feasible with the existing Hijacking repo.
- It established that mechanistic analysis would require new code rather than small edits to the existing attack harness.
- It selected StrongREJECT as a later evaluator rather than part of the first execution stage.
- It created the implementation plan that became `poc_stage2`.

## Limitations / Caveats

- The audit was static: no expensive attack run was performed in Stage 1.
- The Hijacking repo's existing logs were not enough for research-grade downstream analysis.
- The audit did not validate API keys or cluster runtime behavior; that was pushed into Stage 2.

## Handoff To Next Stage

Stage 2 should wrap the Hijacking code without changing attack logic, run a small HarmBench slice against `gpt-o4-mini`, and write structured artifacts that can be validated and later scored by StrongREJECT.
