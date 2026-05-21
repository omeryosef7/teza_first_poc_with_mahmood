# Stage 4 Qwen3 Mechanistic Report

- Model: `Qwen/Qwen3-14B`
- Report status: `debug_preliminary`

**Warning:** DEBUG/PRELIMINARY REPORT: inputs are not final scientific evidence.

## Warnings
- Selected direction is not intervention_selected; report is debug/preliminary.
- Stage 4A2 intervention metrics are not intervention_selected; selection may be smoke/debug only.
- Stage 4B summary has debug_only_run=true.
- Stage 4B scientific_status is debug_only_not_final_evidence.

## Stage 4A1 Candidate Summary

- Candidate tensor shape: `[4, 40, 5120]`
- Number of candidates: 160
- Positions: `[-1, -2, -3, -4]`
- Number of layers: 40

## Stage 4A2 Selection Summary

- Selection status: `intervention_smoke_test_only`
- Selected position: -3
- Selected layer: 22
- Candidates evaluated: 5
- Candidates surviving filters: 0

## Stage 4B Dampening Summary

- Number of goals: 2
- Mean delta medium: -58.8799
- Mean delta long: -58.2284
- Fraction negative delta medium: 1
- Fraction negative delta long: 1

### Refusal Component By Condition

| Condition | Mean | Median | Count |
| --- | ---: | ---: | ---: |
| `direct_harmful` | 61.4333 | 61.4333 | 2 |
| `hijacked_medium` | 2.55341 | 2.55341 | 2 |
| `hijacked_long` | 3.20493 | 3.20493 | 2 |

## Interpretation

- Negative delta means refusal-direction dampening: `hijacked_component - direct_harmful_component < 0`.
- This report is debug/preliminary and cannot be used as final scientific evidence.
