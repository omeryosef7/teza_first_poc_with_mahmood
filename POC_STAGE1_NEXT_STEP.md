# POC Stage 1 Next Step

## Exact Next Coding Task

Build a **clean wrapper and result-capture layer around the existing `Chain_of_Thought_Hijacking` repo**, without changing its attack logic yet.

The wrapper should do four things:

1. run the existing Hijacking CLI on a very small HarmBench slice for one target model
2. capture structured per-goal outputs from logs or direct function calls
3. normalize those outputs into a tabular experiment artifact
4. prepare the artifact so StrongREJECT can later score the responses with minimal glue code

This is the correct next task because the checked-in Hijacking repo does not expose structured outputs suitable for research iteration.

## Reuse Strategy

Use the Hijacking repo **indirectly through a thin wrapper**, not as the long-term experiment framework.

Reason:

- the repo is useful for prompt generation and target-model execution
- it is not organized for controlled experiments, structured exports, or mechanistic analysis
- wrapping it now keeps your immediate work small and avoids premature rewrites

Recommendation:

- **Reuse the Hijacking repo directly for attack generation and target querying**
- **Do not** reuse its logging format as your research data model
- **Do not** start adapting AutoInject yet

## Files to Create or Modify Next

Likely new files:

- `poc_stage2/hijacking_wrapper.py`
  - thin programmatic wrapper around the Hijacking flow
- `poc_stage2/collect_hijacking_results.py`
  - runs a tiny slice and writes a structured JSONL or CSV
- `poc_stage2/schemas.py`
  - defines the experiment row schema
- `poc_stage2/README.md`
  - exact commands and assumptions

Likely minimal modifications to existing repo code:

- `Chain_of_Thought_Hijacking/Hijacking/core/workflow.py`
  - only if needed to return structured per-iteration/per-goal results instead of just logging
- `Chain_of_Thought_Hijacking/Hijacking/utils/logger.py`
  - only if needed to expose structured data without scraping logs

Preferred approach:

- first try to wrap by importing repo modules
- only patch the Hijacking repo if the current code makes structured capture impossible

## Specific First Output to Aim For

Generate one structured artifact from a tiny run, for example:

- `outputs/hijacking_baseline_gpt-o4-mini_small.jsonl`

Each row should contain at minimum:

- `goal_index`
- `goal`
- `target_model`
- `attack_iteration`
- `conversation_id`
- `attack_prompt`
- `target_response`
- `judge_score`
- `judge_raw_output`
- `is_success`
- `reasoning_effort` if applicable
- `source_repo` set to `Chain_of_Thought_Hijacking`

Also produce one aggregate summary file:

- `outputs/hijacking_baseline_gpt-o4-mini_small_summary.json`

Summary fields:

- `num_goals`
- `num_successes`
- `attack_success_rate`
- `target_model`
- `dataset`
- `dataset_slice`
- `n_iterations`
- `n_streams`

## Immediate Success Criterion

The next coding step is successful if you can produce:

1. one small structured result file for a 3-5 goal HarmBench slice
2. one summary JSON with ASR
3. a schema that can be passed into StrongREJECT later by renaming:
   - `goal` -> `forbidden_prompt`
   - `target_response` -> `response`

## Why This Should Come Before Any New Attack Code

- it verifies the actual behavior of the local Hijacking repo
- it creates the data contract for all later experiments
- it prevents you from coupling future CoT-length and StrongREJECT work to ad hoc logs
- it keeps the next step small, testable, and directly informative for the larger POC
