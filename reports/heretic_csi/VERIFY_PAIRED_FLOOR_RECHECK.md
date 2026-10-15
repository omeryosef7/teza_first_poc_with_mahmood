# VERIFY — paired-floor re-check (per-arm survivors vs common keys)

**Verifier:** F3 (2026-10-15). **Code:** `research/heretic_csi/verify/paired_floor_recheck.py` (own; reuses only F3's
`verify_s049.py` loaders). **JSON:** `reports/heretic_csi/VERIFY_PAIRED_FLOOR_RECHECK.json`.

**F6's diagnosis is CORRECT.** `verify_s049.py` / `verify_r4_val.py` averaged each arm over the floor-kept ids *that arm
has* (A = per-arm survivors). Rank-1 controls lose 1–6 rows to the norm-match-degeneracy refusal, so in A the candidate
and those controls were averaged over **different row sets**. The correct paired computation (B = common keys:
floor-kept ids present in every arm of the pool + liveness) is the one to use. Cells with no short arms (all rank ≥ 4)
are identical under A and B.

| cell | floor | A per-arm (previously reported) | **B common keys (correct)** | changes? |
|---|---|---|---|---|
| basket r1 VAL (968532) | BASE-ref | 1/57 p=.0175, 145 rows | **1/57 p=.0175, 133 rows, rec .0359** | rows only |
| basket r1 VAL (968532) | strict | 2/57 p=.035, 135 rows | **1/57 p=.0175, 123 rows, rec .0224** | **YES** (F6 confirmed) |
| basket r1 TRAIN (966084) | BASE-ref | 1/57 p=.0175, 425 rows | **2/57 p=.035, 397 rows, rec .0275** | **YES** — now = S-049 record (2/57) |
| basket r1 TRAIN (966084) | strict | 5/57 p=.088, 387 rows | **4/57 p=.070, 359 rows, rec .0137** | rank 5→4, still FAIL |
| button r1 VAL (968534) | BASE-ref | 18/57 p=.316 | **14/57 p=.2456, 193 rows** | **YES** — now = analyzer record exactly |
| button r1 VAL (968534) | strict | 18/57 | **14/57 p=.2456** | yes (still FAIL) |
| button r1 TRAIN (966157) | BASE-ref / strict | 25/57 / 23/57 | **23/57 / 22/57** | BASE-ref now = record (23/57) |
| basket r4 VAL (1022699) | BASE-ref | 1/57, 145 rows | 1/57, 145 rows | no (no short arms) |
| basket r4 VAL (1022699) | strict | 2/57 p=.035, 135 rows | **2/57 p=.035, 135 rows** | **no — S-072/073 "strict 2/57" stands** |
| button r4 VAL (1022698) | BASE-ref / strict | 1/57, 203 rows | 1/57, 203 rows | no |

## Corrections to F3's earlier reports (supersedes the affected lines; originals left in place)
- VERIFY_S049: the "minor rank differences" in rank-1 cells (basket r1 TRAIN 1 vs 2; button r1 25 vs 23 / 18 vs 14) were
  **F3's bug** (missing cross-arm key intersection), not the analyzer's ranking statistic. Under B, F3 reproduces the
  frozen analyzer's rank-1 cells exactly (basket r1 TRAIN 2/57, VAL 1/57; button r1 TRAIN 23/57, VAL 14/57).
- VERIFY_S049 "robustness caveat" for basket r1: under the correct strict paired floor, **VAL is 1/57 (strictly largest,
  123 rows)**, not 2/57; TRAIN strict is 4/57 p=0.070 (fail), not 5/57. So: basket r1 VAL passes under every floor
  variant; basket r1 TRAIN fails under strict (and is 2/57 = borderline under BASE-ref, as S-049 recorded).
- VERIFY_S072 (basket r4 strict 2/57; button r4 all variants 1/57) and VERIFY_S084 (which already intersected keys
  across all 205 arms) are **unaffected**.
- Note: at basket r1 TRAIN BASE-ref (B) the candidate (0.003850) and KO_SHUF_r1_8 (0.003858) are within 1e-5 — the 2/57
  is a near-tie.
