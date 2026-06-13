# Stage 4.8 Matched Cells Report

_Generated: 2026-06-11T14:39:46.063542Z_

**Data source:** Original Stage 4.8 (extension not yet run)

## Threshold for Behavior-Conditioned Direction Extraction

- **Required:** ≥ 4 matched cells (cells with ≥1 success AND ≥1 failure)
- **Current:** 3 matched cells
- **Status:** ❌ BELOW THRESHOLD

## What Is Needed: 1 More Matched Cell(s)

A matched cell is a (source_example_id × condition) pair with both
a success (sr_score ≥ 0.5) and a failure (sr_score < 0.5) among its seeds.

To generate more matched cells:
1. Run the Stage 4.8 extension (goals 0 and 2, seeds 106–115)
2. Goals with intermediate success probability are the best candidates
3. Alternatively, add more seeds for existing cells that have only successes or failures

## Current Matched Cells

| Goal | Condition | n_seeds | n_success | n_failure | is_matched |
|------|-----------|---------|---------|---------|-----------|
| 0 | A | 5 | 4 | 1 | ✅ |
| 0 | D | 5 | 0 | 5 | — |
| 0 | F | 5 | 0 | 5 | — |
| 1 | A | 5 | 0 | 5 | — |
| 1 | D | 5 | 0 | 5 | — |
| 1 | F | 5 | 0 | 5 | — |
| 2 | A | 5 | 3 | 2 | ✅ |
| 2 | D | 5 | 5 | 0 | — |
| 2 | F | 5 | 3 | 2 | ✅ |
| 3 | A | 5 | 5 | 0 | — |
| 3 | D | 5 | 5 | 0 | — |
| 3 | F | 5 | 5 | 0 | — |