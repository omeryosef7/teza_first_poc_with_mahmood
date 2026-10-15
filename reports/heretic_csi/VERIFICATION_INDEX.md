# Verification index (interim, 2026-10-15)

Every headline and every certified negative, with its independent recomputation. Verifiers wrote their own code under
`research/heretic_csi/verify/` and did not reuse the primary analyzer's logic.

| # | Claim / result | Status | Verification report | Outcome |
|---|---|---|---|---|
| 1 | P2a rank sweep S-049 (basket r1 PASS VAL; basket r16, button r1, button r16 fail) + K4 r4/r8 | CONFIRMED / certified negatives | `VERIFY_S049_independent.md/.json`, `VERIFY_S049_quarantine_check.json` (S-052) | All verdicts reproduce. Caveats surfaced: basket r1 is option-mass-floor-sensitive; button r4 TRAIN pass holds under every floor variant |
| 2 | P2a button r4 VAL (preregistered PR-HCSI-S051) | PASS → later superseded by #3 | `VERIFY_S072_r4_validation.md/.json` (S-073) | Agrees exactly; LODO 23/23; basket r4 VAL found fragile |
| 3 | P2a button r4 powered re-test (PR-HCSI-S084 + amendment 1 + binding rule) | **CONFIRMED** | `VERIFY_S084_powered.md/.json` (S-126) | Agrees on every element: 203 rows, rank 1/201, p 0.004975, Holm 0.0149, beats all SHUF, LODO 23/23, mutations null |
| 4 | P2b weight-operator TRAIN-K4 read | DESCRIPTIVE (in-sample) | `REVIEW_ADVERSARIAL_20261014_e.md` + `research/heretic_csi/verify/verify_p2b_train.py` (S-136) | All 8 cells reproduce; wording corrections applied (fit-site untested, in-sample pairing bias, not a constant shift, "overshoot" dropped) |
| 5 | P2b weight-operator VALIDATION read (outcome D) | CONFIRMED (outcome) with marginal basket r4 | `VERIFY_P2B_VAL.md/.json` + `REVIEW_ADVERSARIAL_20261015_f.md` (S-157) | All 8 cells reproduce; basket r4 marginal (LODO loses 9/23); "P2a vs P2b disagree" wording rejected |
| 6 | P3 truncation / minimal subspace | **VOID** | `P3_TRUNC_READ_VOID.md`, `p3_basket_r4_validation.NOT_QUOTABLE.md` (S-176, S-180) | Preregistered REEXP check failed; kept VOID; no post-hoc re-preregistration |
| 7 | P6 G2 (KO liveness) for lamp, kettle, pencil, ladder | PASS | `REVIEW_ADVERSARIAL_20261015_h.md` (S-180) | Independently recomputed from raw run dirs: points match to 1e-5, CIs ≤ 0.001; population and invocation parity with the incumbent rescue |
| 8 | Inherited "basketball" occurrence-gate failures vs incumbent basket artifacts | No impact | `VERIFY_basketball_occurrence.md/.json`, `VERIFY_codeword_collision_scan.json` (S-103) | All 30 rows are in a pre-excluded domain; no certified verdict changes; button bank clean |
| 9 | P5 held-out probe quality (C1) | DESCRIPTIVE | re-run with 400 shuffles inside `REVIEW_ADVERSARIAL_20261014_c.md` (S-097) | ρ reproduced; "equal decodability" downgraded to "no evidence of a basket advantage" |
| 10 | P0 Phase A / Phase B (native ARA control) | PASS / MEASURED | `REVIEW_ADVERSARIAL_20261014_c.md` (S-097) scoping; source checks in S-180 | Heretic reset finding confirmed in source; Phase-B wording scoped |

**Adversarial reviews (8):** `REVIEW_ADVERSARIAL_20261014.md`, `_b`, `_c`, `_d`, `_e`, `REVIEW_ADVERSARIAL_20261015_f.md`,
`_g`, `_h`. Each was run by a fresh reviewer with no shared context with the implementer and barred from unread endpoints.

**PENDING verification:** P4 head-restricted evaluation; P6 rescue / H6a; any P7 read.
