# VERIFY_S072 — independent re-computation of PR-HCSI-S051 (rank-4 VALIDATION)

**Verifier:** F3 (2026-10-14). **Code:** `research/heretic_csi/verify/verify_r4_val.py` (+ F3's own `verify_s049.py`; frozen
analyzer NOT used). **Prereg:** `configs/heretic_csi/prereg_S051_rank4_validation.json` (primary = button r4 VAL; basket r4 VAL
descriptive). **JSON:** `reports/heretic_csi/VERIFY_S072_r4_validation.json`.
Method as in VERIFY_S049: y_install = logistic(logp_concept − logp_codeword), domain means, rank statistic = mean_d(arm − KO),
rank = 1 + #controls strictly greater, p = rank/57. Primary floor = BASE-referenced 0.05; sensitivity = strict paired floor
(BASE ∧ KO ∧ KO_FULL) and no floor. LODO = drop each domain in turn and recompute the rank.

## PRIMARY — button r4 VALIDATION (job 1022698, n-501, single attempt, 61/61 dirs = log-referenced set)
| quantity | value |
|---|---|
| rows / domains | 230 / 23, all `validation` per split file; **TEST absent**; 203 rows after BASE-ref floor |
| rank / p (BASE-ref) | **1/57, p = 0.0175** (strictly largest; 0 ties) |
| rank / p (strict floor) | 1/57 p=0.0175 (strict keeps the same 203 rows) · no floor: 1/57 |
| recovery (BASE-ref) | **0.0909 [0.051, 0.126]** (domain bootstrap) · no floor 0.087 |
| candidate − KO | 0.0129 [0.0063, 0.0192]; **20/23 domains positive** |
| best control / margin | KO_SHUF_r4_9 = 0.0092; margin +0.0037 (1.16 control-SD); control mean 0.0016 |
| sub-families | rank 1/47 among 46 RAND (RAND max 0.0068) and 1/11 among 10 SHUF |
| LODO | rank 1 for **all 23** drop-one-domain recomputations — no single domain drives it |
| liveness | KO−BASE −0.302; FULL−KO +0.142; SELF−KO −0.0005 (inert) |
| matching | all 57 arms rank 4 (pt matrix_rank + row liveness); norm-match rel.err ≤ 5e-16; keys distinct; seed 20260913; all DONE ok, no short arms |
| mutations | swap candidate→control: median p 0.45; shuffle arm identity within domain: median p 0.39 |

**Verdict: AGREES with the frozen analyzer** (PASS, rank 1/57, recovery 0.0909, cand−KO 0.0129 [0.0065, 0.0190], 20/23).
Robust to floor variant and to LODO. Caveat: margin over the best (shuffled-PLS) control is modest (≈1.2 SD of the control
distribution); p is at the attainable floor, so the strength of evidence is capped at 0.0175 by the 56-control design.

## DESCRIPTIVE — basket r4 VALIDATION (job 1022699, n-503, single attempt, 61/61 dirs)
| quantity | value |
|---|---|
| rows / domains | 230 / 23 validation, TEST absent; 145 rows after BASE-ref floor (basket option-mass-degraded, as known) |
| rank / p (BASE-ref) | 1/57, p = 0.0175 |
| strict floor / no floor | **2/57 p=0.035** (135 rows) / 1/57 |
| recovery | 0.141 [0.077, 0.233] (strict 0.111; no floor 0.151) |
| candidate − KO | 0.0198 [0.0104, 0.0310]; 19/23 domains positive |
| best control / margin | KO_SHUF_r4_9 = 0.0183; margin **+0.0015 (0.3 control-SD)**; strict floor margin −0.0020 |
| LODO | ranks {1, 2}: dropping `airport_apron` or `botanic_glasshouse` alone demotes it to rank 2 |
| liveness / matching / mutations | KO−BASE −0.280, FULL−KO +0.140, SELF−KO +0.0007; rank 4 all arms; norm rel.err ≤ 5e-16; mutation medians 0.55 / 0.50 |

**Reading:** basket r4 is top-of-distribution on VAL but **fragile** (tiny margin over one shuffled-PLS control; flips to
rank 2 under the strict floor or after dropping a single domain). Descriptive only, per prereg; do not quote as a pass.
Contrast with button r4, which is robust on every check.
