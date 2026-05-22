# POC Stage 2.5 Main Documentation

## Manager Summary

Stage 2.5 was a validation and schema-design stage. It verified that the Stage 2 JSONL and summary JSON were internally consistent, clarified that the 50 percent attack success rate is goal-level rather than row-level, and documented the main limitation in the Stage 2 schema: failures are not categorized by API/provider/model cause.

This stage did not rerun the attack. It increased confidence in the Stage 2 artifacts and prepared the handoff to StrongREJECT scoring.

## Comprehensive Detailed Summary

The Stage 2.5 work had four linked parts:

- Inspect the Stage 2 JSONL and summary artifacts.
- Build an automated validator.
- Write a validation report.
- Design a backward-compatible error-accounting schema for future runs.

The validator confirmed:

- 42 JSONL rows loaded.
- 4 distinct goals.
- Summary `num_goals`, `num_successes`, and `attack_success_rate` match recomputed values.
- Early stopping explains the row count reduction from 48 possible rows to 42 actual rows.
- All 20 required Stage 2 fields are present in every row.

The key interpretation change was metric clarity. Stage 2's `attack_success_rate = 0.5` means `2 successful goals / 4 total goals`, not `4 successful rows / 42 rows`.

## What We Tried

- Determine whether the final Stage 2 summary was mathematically correct.
- Check whether early stopping caused missing data or explained row counts.
- Determine whether the artifacts were clean enough for Stage 3 StrongREJECT scoring.
- Design a better schema for future robustness analysis.

## What We Actually Did

- Created `poc_stage2/validate_hijacking_artifacts.py`.
- Validated `outputs/hijacking_baseline_gpt-o4-mini_small.jsonl`.
- Validated `outputs/hijacking_baseline_gpt-o4-mini_small_summary.json`.
- Wrote:
  - `POC_STAGE2_5_ARTIFACT_VALIDATION.md`
  - `POC_STAGE2_5_SCHEMA_ENHANCEMENT.md`
  - `POC_STAGE2_5_COMPLETE_SUMMARY.md`
  - `POC_STAGE2_5_QUICK_REFERENCE.md`
- Proposed optional future fields such as attack, target, and judge call status.

## Runs And Artifacts

| Run / Artifact | Path | What It Shows |
| --- | --- | --- |
| Validator script | `poc_stage2/validate_hijacking_artifacts.py` | Automated validation of Stage 2 row and summary artifacts. |
| Validation report | `POC_STAGE2_5_ARTIFACT_VALIDATION.md` | Full proof that metrics and row counts are internally consistent. |
| Schema enhancement design | `POC_STAGE2_5_SCHEMA_ENHANCEMENT.md` | Backward-compatible error-status fields for future runs. |
| Complete summary | `POC_STAGE2_5_COMPLETE_SUMMARY.md` | Manager-level and technical summary of the validation work. |
| Quick reference | `POC_STAGE2_5_QUICK_REFERENCE.md` | Short operational guide and metric clarification. |
| Validated input JSONL | `outputs/hijacking_baseline_gpt-o4-mini_small.jsonl` | 42 rows validated. |
| Validated summary JSON | `outputs/hijacking_baseline_gpt-o4-mini_small_summary.json` | Summary values verified. |

## Timing From Git And Logs

| Timing Evidence | Value | Confidence |
| --- | --- | --- |
| Stage 2 final log mtime | Around `2026-05-20 17:29 IDT` for `logs/poc_stage2_hijacking_378951.out` | estimated from logs |
| Stage 2.5 commit | Commit `f5cfe23`, `2026-05-20T18:08:28+03:00` | git-window estimate |
| Approximate validation/documentation window | About 40 minutes after the final Stage 2 run log | git-window estimate |
| Validator runtime | Less than 1 second per `POC_STAGE2_5_QUICK_REFERENCE.md` | estimated from report |
| Slurm accounting | Not used for Stage 2.5; no model run was performed | exact from workflow |

## Results

| Validation Check | Result |
| --- | --- |
| Goal count consistency | Passed |
| Summary metric recomputation | Passed |
| Early stopping explanation | Passed |
| Required field validation | Passed |
| Data corruption / missing rows | No issue found |

Validated metric meanings:

- Goal-level success: 2 of 4 goals, or 50 percent.
- Row-level success: 4 of 42 rows, about 9.5 percent.
- Early stopping: the financial-crime/cash-smuggling goal stopped after iteration 1, reducing the total row count by 6.

## Limitations / Caveats

- Stage 2.5 did not fix the schema limitation in existing rows; it documented and designed the fix for future runs.
- Existing Stage 2 rows still cannot reliably separate provider safety filters, model refusals, judge unavailability, and other exceptions.
- Any later robustness claim should mention this limitation unless Stage 2 is rerun with the proposed error fields.

## Handoff To Next Stage

Stage 3 can safely use the Stage 2 artifacts for StrongREJECT scoring because the artifacts are internally consistent. Future scaled attack runs should implement the Stage 2.5 error-accounting schema before drawing stronger robustness conclusions.
