# P3 truncation/removal read — basket r4 VALIDATION — **VOID** (2026-10-15)

Job 1041078 (A5000, n-503; 133/133 arms ok; 1 attempt). Prereg: PREREG_P3_TRUNC.json + PREREG_P3_TRUNC_ERRATUM.json
(committed S-158 / S-167b). Analyzer `research/heretic_csi/p3_analyze.py` (sha 713fe39b). Output
`reports/heretic_csi/p3_basket_r4_validation.json`.

## Verdict
**VOID** — the preregistered REEXP-reproduces-CAND check failed its per-row tolerance: max per-row
|y_REEXP − y_refCAND| = 0.072 > 0.01 (37/145 floor-kept rows > 0.01; median 0.0004, p90 0.027, p99 0.057).
Other checks passed: own KO == reference KO exactly (max |dy| 0); |stat(REEXP) − stat_ref(CAND)| = 0.0007 < 0.001;
gates ok (KO−BASE −0.280, FULL−KO +0.140); no collapsed control. No k* is reported.

**Parent decision S-176:** P3 stays VOID. No re-preregistration on the already-seen VALIDATION data (it would be
outcome-informed), and a valid read could only compare against random edits anyway.

The descriptive numbers in the JSON (TOP1/TOP2 rank 1/41 vs random edits, retention 0.94/0.99; DROP1 loss 0.95,
norm-confounded) are MEASURED from an invalid read and are **not quotable**.

## Lesson (for any future operator-surgery read)
1. **Re-express in float64 and verify bitwise-equivalence of the identity arm first.** The REEXP operator was rebuilt
   from a float32-cast SVD of the factors; the tiny factor perturbation is amplified by the y_install readout on some
   rows (up to 0.07). The identity/re-expression arm should either apply the ORIGINAL factors (bit-identical to
   KO_CAND) or be rebuilt in float64 and cast once, and its row-level agreement must be demonstrated before any
   truncation arm is read.
2. **Calibrate every tolerance on TRAIN before it is frozen.** The 0.01 per-row tolerance was chosen without
   measurement. Tolerances for replay/re-expression checks must be set from a TRAIN (or smoke) measurement of the same
   comparison, with margin, and written into the prereg with that provenance.
3. Row-level readout sensitivity to tiny weight perturbations means only DOMAIN-aggregated statistics are robust
   comparison units for operator variants; row-level replay checks should use a calibrated quantile, not a max.
