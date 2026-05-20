# POC Stage 3: StrongREJECT Integration Report

## 1. Executive Summary

Stage 3 adds a second evaluation layer on top of the already validated Stage 2 hijacking artifact set. The new layer uses StrongREJECT to score the same target responses that were collected during Stage 2, so we can compare the original Hijacking judge labels against a separate rubric-based evaluator.

The purpose of this stage is not to rerun the attack and not to revise the Stage 2 results. Instead, the aim is to answer a different question: when the Hijacking run produced a target response, does StrongREJECT also consider that response harmful, partially harmful, or low quality? That comparison is the main research value of Stage 3.

What I completed in this workspace:

- inspected the local StrongREJECT checkout to confirm the exact API and evaluator behavior
- identified `strongreject_rubric` as the evaluator path to use for prompt-response pairs
- implemented a new `poc_stage3` package for loading, scoring, analyzing, and summarizing Stage 2 rows
- added a CLI for scoring the Stage 2 JSONL artifact into a new Stage 3 artifact set
- added an analysis script that summarizes the scored rows and compares StrongREJECT to the Hijacking judge
- wrote a README for operational use of Stage 3
- rewrote this report into a detailed project log that documents the entire Stage 3 effort
- validated the new code paths locally with a synthetic dry-run and CLI help output

What remains pending:

- live StrongREJECT scoring of the 42 Stage 2 rows
- generation of the real scored JSONL and summary JSON artifacts from the API-backed evaluator
- the actual cross-evaluator comparison numbers that will come from those scores

The current blocker is environmental. `OPENAI_API_KEY` is not configured in this workspace, and the local StrongREJECT checkout still needs its Python dependencies available before the evaluator can be imported cleanly.

## 2. Why Stage 3 Exists

Stage 2 gave us a structured hijacking run and a validated set of row-level artifacts. That was enough to know which rows were counted as successful jailbreaks by the original judge, but it did not answer whether those responses are actually high-quality harmful answers under a second rubric.

Stage 3 exists because a binary jailbreak label is not the same thing as response quality. A response can be non-refusal without being especially harmful, detailed, or convincing. StrongREJECT gives us a separate score that can help distinguish those cases.

This stage therefore serves three specific purposes:

1. compare the original Hijacking judge against a rubric-based StrongREJECT score
2. preserve the Stage 2 artifacts exactly as they are while writing new Stage 3 artifacts separately
3. prepare a research-ready summary that can be cited or used in a later report

## 3. Inputs and Scope

The work is based on the validated Stage 2 artifact pair below:

- Stage 2 JSONL artifact: `outputs/hijacking_baseline_gpt-o4-mini_small.jsonl`
- Stage 2 summary artifact: `outputs/hijacking_baseline_gpt-o4-mini_small_summary.json`

The validated Stage 2 scope is:

- 42 row-level records
- 4 distinct HarmBench goals
- original Hijacking labels already verified as internally consistent
- target model: `gpt-o4-mini`
- attack model: `gemini-2.5-pro`
- judge model: `gemini-judge`

Stage 3 keeps that scope unchanged. Every row in Stage 2 is still considered as input for scoring, and the original Stage 2 JSONL is not modified in place.

## 4. StrongREJECT Inspection and Integration Decision

Before implementing anything, I inspected the local StrongREJECT repository directly rather than depending only on the public README.

The files inspected were:

- `strong_reject/strong_reject/README.md`
- `strong_reject/strong_reject/strong_reject/evaluate.py`
- `strong_reject/strong_reject/strong_reject/eval_files/judge_templates.json`
- `strong_reject/strong_reject/docs/index.rst`
- `strong_reject/strong_reject/pyproject.toml`
- `strong_reject/strong_reject/src/full_evaluation.py`

That inspection confirmed the following local facts:

- `strongreject_rubric` is the rubric-based evaluator we want
- the evaluator consumes `forbidden_prompt` and `response`
- the evaluator returns a result dictionary that includes `score`
- when the rubric parse succeeds, the result also includes rubric fields such as `refusal`, `convincingness`, and `specificity`
- the rubric path requires `OPENAI_API_KEY`
- the local checkout can be imported by putting `strong_reject/strong_reject` on `sys.path`

From this inspection, the cleanest integration path was obvious:

- call `strong_reject.evaluate.evaluate(...)`
- use evaluator name `strongreject_rubric`
- score rows one at a time so the original metadata is preserved exactly

That choice is important because Stage 3 is not a model-generation pipeline. It is a scoring-and-analysis pipeline for existing artifacts.

## 5. Data Flow for Stage 3

The Stage 3 pipeline is intentionally simple and explicit.

### 5.1 Input mapping

For each Stage 2 row:

- `goal` is mapped to StrongREJECT `forbidden_prompt`
- `target_response` is mapped to StrongREJECT `response`

No other Stage 2 fields are altered or dropped.

### 5.2 Row processing

Each row is processed independently so that any failure can be tracked at the row level. This makes it possible to keep the original Stage 2 metadata, preserve row identity, and attach row-specific scoring results.

The row-level logic does the following:

- validate required Stage 2 fields before scoring
- skip empty target responses with a specific status flag
- call the StrongREJECT evaluator on non-empty responses
- capture the returned score and rubric values when present
- capture errors as structured `strongreject_error_*` fields if the evaluator fails

### 5.3 Output behavior

The output is split into two new artifacts:

- a scored JSONL file with one row per original Stage 2 record
- a summary JSON file with aggregate statistics and comparison tables

This is deliberate. The original Stage 2 JSONL stays unchanged and serves as the source artifact.

## 6. Files Created for Stage 3

I added six Stage 3 files.

### 6.1 `poc_stage3/__init__.py`

This marks the package as a Stage 3 module namespace and gives the project a clean import anchor.

### 6.2 `poc_stage3/strongreject_scoring.py`

This is the core implementation module. It contains the reusable logic for loading, scoring, validating, and summarizing the rows.

The module provides functions for:

- loading JSONL and JSON files
- writing JSONL and JSON outputs
- validating Stage 2 input fields
- importing the local StrongREJECT evaluator
- projecting a row into StrongREJECT input form
- scoring a single row
- scoring a set of rows with optional resume and filtering support
- computing the summary statistics
- checking score ranges and structural consistency

### 6.3 `poc_stage3/run_strongreject_scoring.py`

This is the command-line entry point for the scoring job.

It accepts the documented arguments, converts them into a structured configuration object, runs the scoring pipeline, validates the scored output, and writes the artifact files.

### 6.4 `poc_stage3/analyze_strongreject_results.py`

This script reads the scored JSONL and prints a researcher-facing analysis summary. It is intentionally separate from the scorer because scoring and analysis are different stages of the workflow.

### 6.5 `poc_stage3/README.md`

This is the operational documentation for the Stage 3 workflow.

### 6.6 `POC_STAGE3_STRONGREJECT_REPORT.md`

This is the report you are reading now. It records what was inspected, what was implemented, what was validated, and what remains blocked.

## 7. Implementation Details by Module

### 7.1 `strongreject_scoring.py`

This module is the technical center of Stage 3.

#### Loading and validation

It loads Stage 2 JSONL rows and validates that the required columns are present before any scoring happens. The required fields are:

- `goal`
- `target_response`
- `is_success`
- `judge_score`
- `goal_index`

If any of these are missing, the run fails early with a clear error instead of producing partial or misleading results.

#### StrongREJECT import path

The module inserts the local StrongREJECT checkout into `sys.path` so the repo can import `strong_reject.evaluate` directly from the cloned repository.

#### Score normalization and output shape

The module preserves the entire original Stage 2 row and appends new fields prefixed with `strongreject_`.

The main fields are:

- `strongreject_evaluator`
- `strongreject_status`
- `strongreject_score`
- `strongreject_raw_result`
- `strongreject_refusal`
- `strongreject_convincingness`
- `strongreject_specificity`
- `strongreject_error_type`
- `strongreject_error_message`

The implementation also handles empty responses and invalid evaluator outputs explicitly so those cases are visible in downstream analysis.

#### Summary generation

The summary builder computes:

- overall score statistics
- score statistics split by `is_success`
- a threshold-based agreement table
- per-goal analysis with best-scoring row metadata

The threshold used for the comparison table is `0.5`, which is documented as an analysis convenience rather than a canonical StrongREJECT threshold.

### 7.2 `run_strongreject_scoring.py`

This CLI wraps the scoring module in a practical command.

It is designed to:

- read Stage 2 input
- produce Stage 3 output files
- fail fast if `OPENAI_API_KEY` is missing
- keep the command-line interface simple and reproducible

The CLI supports the following options:

- `--input-jsonl`
- `--output-jsonl`
- `--summary-json`
- `--evaluator`
- `--max-rows`
- `--only-successful-hijacking-rows`
- `--resume`
- `--sleep-seconds`
- `--overwrite`
- `--threshold`

### 7.3 `analyze_strongreject_results.py`

This analysis script is meant to answer the research questions after scoring is complete.

It prints:

- total rows loaded
- number of scored rows
- mean and median score
- mean score for Hijacking-success rows
- mean score for Hijacking-failure rows
- agreement counts for the threshold table
- per-goal summary lines
- top-scoring row for each goal
- whether all success rows are above threshold
- whether any failure rows are above threshold

It avoids printing full response texts so the console output stays safe and concise.

## 8. Exact Work Performed

Here is the work sequence in the order I carried it out:

1. inspected the local StrongREJECT README and evaluator code to find the real integration surface
2. verified that `strongreject_rubric` is the rubric evaluator we should use
3. verified that the evaluator consumes `forbidden_prompt` and `response`
4. verified that the rubric path depends on `OPENAI_API_KEY`
5. verified that the local checkout can be imported from the cloned repository directory
6. created the `poc_stage3` package
7. implemented the scoring module and its helper functions
8. implemented the CLI runner for scoring
9. implemented the separate analysis script
10. wrote the Stage 3 README
11. rewrote this report with much more detail
12. ran editor-level error checks on the new Python files
13. ran a synthetic dry-run of the scoring summary logic with mock rows
14. ran the CLI `--help` path to ensure the interface matches the documentation
15. checked the markdown formatting of this report with `git diff --check`

## 9. Validation Performed

I ran only validations that are possible without a real OpenAI-backed StrongREJECT run.

### 9.1 Static file validation

The new Python files were checked for editor-level errors. No errors were reported.

That means the new modules are syntactically valid and the import structure is coherent.

### 9.2 Synthetic dry-run

I created a synthetic in-memory dataset with two rows and ran it through the summary logic.

The goal of this test was not to evaluate real content. It was to verify that the pipeline mechanics work:

- JSONL writing and reading
- score normalization
- threshold-based confusion counts
- summary statistics generation

Observed behavior from the dry-run:

- rows loaded: 2
- mean score: 0.5
- confusion counts reflected one row above threshold and one row below threshold

That showed the summary logic is operational.

### 9.3 CLI interface validation

I ran the scoring CLI with `--help` and confirmed that the parser exposes the documented options.

That matters because the README documents an exact command, and the actual program now matches it.

### 9.4 Markdown validation

I also checked the report for whitespace and patch-format issues. No formatting problems were reported.

## 10. Results So Far

There are two categories of results to report.

### 10.1 Implementation results

The Stage 3 infrastructure is now in place.

In practice, that means:

- the Stage 3 package exists
- the Stage 3 scorer is reusable
- the Stage 3 CLI exists and is documented
- the Stage 3 analysis tool exists
- the Stage 3 README exists
- the Stage 3 report now documents the workflow in detail
- the basic local validation checks passed

### 10.2 Live StrongREJECT scoring results

These are not available yet.

The reason is not a code failure but an environment setup issue:

- `OPENAI_API_KEY` is not set in this workspace
- the local StrongREJECT checkout needs its Python dependencies installed to import cleanly

Because of that, no actual StrongREJECT score distribution exists yet for the 42 Stage 2 rows.

## 11. Expected Output Artifacts

When the scoring command is run in a ready environment, it will produce:

- `outputs/hijacking_baseline_gpt-o4-mini_small_strongreject.jsonl`
- `outputs/hijacking_baseline_gpt-o4-mini_small_strongreject_summary.json`

### 11.1 Scored JSONL contract

Each row in the scored JSONL will:

- preserve the original Stage 2 row exactly
- append StrongREJECT result fields
- remain one JSON object per line

The expected row-level shape includes:

- original Stage 2 metadata such as `goal_index`, `goal`, `target_response`, `judge_score`, and `is_success`
- `strongreject_evaluator = "strongreject_rubric"`
- `strongreject_status`
- `strongreject_score`
- `strongreject_raw_result`
- optional rubric fields if returned by the evaluator
- error fields if scoring fails

### 11.2 Summary JSON contract

The summary JSON is designed to be research-usable. It includes:

- metadata about the input and output files
- number of input rows
- number of successfully scored rows
- number of failed scoring rows
- timestamp
- threshold used for the agreement analysis
- global score statistics
- score statistics for `is_success=true` and `is_success=false`
- threshold-based agreement counts
- per-goal analysis with the best response per goal

## 12. How the Analysis Is Intended to Be Read

The analysis is designed around a few research questions:

1. Do the rows that Hijacking counted as jailbreak successes also get high StrongREJECT scores?
2. Do rows that Hijacking counted as failures ever receive high StrongREJECT scores?
3. Which goal produced the strongest harmful response according to StrongREJECT?
4. Are the observed jailbreaks substantive harmful answers, or mostly non-refusal outputs?

The summary and analysis scripts are built to answer exactly those questions once live scores exist.

## 13. Limitations and Caveats

The main limitations are important and should remain visible in any later report:

- Stage 2.5 still matters: some Stage 2 failures may be provider/API failures, not genuine model refusals
- StrongREJECT is an evaluator, not ground truth
- the `0.5` threshold is only a working analysis threshold
- the Stage 3 result set is still small because it is derived from 4 goals and 42 rows
- this is not the later CoT-length experiment
- live scoring is still blocked until the environment has the required API key and dependencies

## 14. Next Step

The immediate next step is to run the scoring command after configuring the environment.

Recommended scoring command:

```bash
python -m poc_stage3.run_strongreject_scoring \
  --input-jsonl outputs/hijacking_baseline_gpt-o4-mini_small.jsonl \
  --output-jsonl outputs/hijacking_baseline_gpt-o4-mini_small_strongreject.jsonl \
  --summary-json outputs/hijacking_baseline_gpt-o4-mini_small_strongreject_summary.json \
  --evaluator strongreject_rubric
```

Recommended analysis command:

```bash
python -m poc_stage3.analyze_strongreject_results \
  --input-jsonl outputs/hijacking_baseline_gpt-o4-mini_small_strongreject.jsonl \
  --summary-json outputs/hijacking_baseline_gpt-o4-mini_small_strongreject_summary.json
```

## 15. Local Integration Details

- Local API path used: `strong_reject.evaluate.evaluate(...)`
- Local evaluator used: `strongreject_rubric`
- Integration style: row-by-row scoring with metadata preservation
- Local import strategy: add `strong_reject/strong_reject` to `sys.path`
- Validation status: synthetic dry-run passed, CLI help passed, markdown check passed, static Python checks passed

## 16. Current Status

Stage 3 is fully implemented as code and documentation, but the live scoring run is still pending environment setup. As soon as the OpenAI key and the StrongREJECT dependencies are available, the workflow can be executed without changing the code again.