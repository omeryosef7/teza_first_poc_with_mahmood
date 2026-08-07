# V3 CONFIRMATORY DATA AUDIT (plan §1.3 / Appendix B)

**Generated:** 2026-08-07 · repo commit `502325fd` · validator `scripts/validate_dataset_v3.py`
**Dataset:** `data/splits/clearharm_doublespeak_v3.json` (N=324) + `data/behavioral_v3/{beh_clearharm.json (170), beh_generated.json (154)}`
**Dataset revision:** `clearharm@79464fb6b3c2a8ee925184f394f9636600349f88`

## FATAL split-integrity checks (all PASS)

| id | check | result |
|---|---|---|
| F1 | duplicate example_id | ✅ 0 duplicates |
| F2 | leakage (concept/codeword/cluster straddle), recomputed | ✅ 0 straddling across **all** split-pairs |
| F3 | ≥20 examples per (cohort × split) cell | ✅ clearharm train85/dev43/test42; generated train77/dev39/test38 — all ≥20 |
| F4 | all 6 conditions (doublespeak, neutral, direct, benign, shuffled, unrelated) non-empty | ✅ 0 bad |
| F5 | placeholder demos | ✅ 0 placeholders — all concept/codeword/wrong-concept demos are real `gpt-4o-mini_cached` (324/324 each) |
| F6 | dataset_revision pinned | ✅ `clearharm@79464fb6…` |
| F7 | behavioral files ⊆ split, sums match | ✅ beh_clearharm=170, beh_generated=154, sum=324 = N; 0 rows outside the frozen split |
| W1 | single_token_primary flag (advisory) | ✅ 0 flagged |

## Split contract (frozen BEFORE any selection — §0.6)

- **Discovery** reads **train + dev** only. **test/heldout** is used **only** for frozen confirmatory
  replication of the *full* sweep (never best-cell-only).
- Cohorts are **not exchangeable** (generated DS is net-negative) → every confirmatory result is reported
  **per-cohort AND pooled**; per-cohort is primary.
- n per (cohort × split) cell ≥ 20 for every cell → the global data rule (§0.6) is satisfied for any
  representational per-layer/head test and for binary/graded behavioral tests within a single cell.
- Power caveat (§30): a single cell (max n=85 train clearharm) still cannot license a small-effect binary
  behavioral null; powered behavioral comparisons must pool cohorts/splits per the pre-registered n
  targets (ΔASR 0.09 → n≈275) and say so explicitly.

## VERDICT

> **These rows and conditions are eligible for confirmatory causal inference.** v3 supersedes the leaky
> v1/v2 splits for every confirmatory claim; v1/v2 remain usable only for historical replication/comparison.
