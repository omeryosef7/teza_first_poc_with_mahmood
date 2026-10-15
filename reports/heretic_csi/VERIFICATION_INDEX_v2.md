# Verification index (interim v2, 2026-10-15)

Supersedes `VERIFICATION_INDEX.md` (v1 kept). Applies review #9 (S-198) and the paired-floor re-check (S-200).

Every headline and every certified negative, with its independent recomputation. Verifiers wrote their own code under
`research/heretic_csi/verify/` and did not reuse the primary analyzer's logic.

| # | Claim / result | Status | Verification report | Outcome |
|---|---|---|---|---|
| 1 | P2a rank sweep S-049 (basket r1 on VAL; basket r16, button r1, button r16 fail) + K4 r4/r8 | **PASS (basket r1) → SUGGESTIVE after S-198** / certified negatives | `VERIFY_S049_independent.md/.json`, `VERIFY_S049_quarantine_check.json` (S-052); **superseded for rank-1 cells by** `VERIFY_PAIRED_FLOOR_RECHECK.md/.json` (S-200) | All verdicts reproduce. Its rank-1 counts were later corrected (common-key intersection): basket r1 VAL is 1/57 under every floor (the "floor-sensitive" caveat is WITHDRAWN), basket r1 TRAIN 2/57 BASE-ref / 4/57 strict, button r1 14/57 VAL / 23/57 TRAIN |
| 2 | P2a button r4 VAL (preregistered PR-HCSI-S051) | PASS → superseded by #3 | `VERIFY_S072_r4_validation.md/.json` (S-073); rank-1 cells superseded by `VERIFY_PAIRED_FLOOR_RECHECK.*` (S-200) | Agrees exactly; LODO 23/23; basket r4 VAL found fragile. basket r4 VAL strict-floor 2/57 is unchanged by the re-check |
| 3 | P2a button r4 powered re-test (PR-HCSI-S084 + amendment 1 + binding rule) | **CONFIRMED** | `VERIFY_S084_powered.md/.json` (S-126) | Agrees on every element: 203 rows, rank 1/201, p 0.004975, Holm 0.0149, beats all SHUF, LODO 23/23, mutations null |
| 4 | P2b weight-operator TRAIN-K4 read | DESCRIPTIVE (in-sample) | `REVIEW_ADVERSARIAL_20261014_e.md` + `research/heretic_csi/verify/verify_p2b_train.py` (S-136) | All 8 cells reproduce; wording corrections applied (fit-site untested, in-sample pairing bias, not a constant shift, "overshoot" dropped) |
| 5 | P2b weight-operator VALIDATION read (outcome D) | CONFIRMED (outcome) with marginal basket r4 | `VERIFY_P2B_VAL.md/.json` + `REVIEW_ADVERSARIAL_20261015_f.md` (S-157) | All 8 cells reproduce; basket r4 marginal (LODO loses 9/23); "P2a vs P2b disagree" wording rejected |
| 6 | P3 truncation / minimal subspace | **VOID** | `P3_TRUNC_READ_VOID.md`, `p3_basket_r4_validation.NOT_QUOTABLE.md` (S-176, S-180) | Preregistered REEXP check failed; kept VOID; no post-hoc re-preregistration |
| 7 | P6 G2 (KO liveness) for lamp, kettle, pencil, ladder | PASS | `REVIEW_ADVERSARIAL_20261015_h.md` (S-180) | Independently recomputed from raw run dirs: points match to 1e-5, CIs ≤ 0.001; population and invocation parity with the incumbent rescue |
| 8 | Inherited "basketball" occurrence-gate failures vs incumbent basket artifacts | No impact | `VERIFY_basketball_occurrence.md/.json`, `VERIFY_codeword_collision_scan.json` (S-103) | All 30 rows are in a pre-excluded domain; no certified verdict changes; button bank clean |
| 9 | P5 held-out probe quality (C1) | DESCRIPTIVE | 400-shuffle re-run inside `REVIEW_ADVERSARIAL_20261014.md` (review #1, S-065) | ρ reproduced; "equal decodability" downgraded to "no evidence of a basket advantage"; a decodability *difference* is CANNOT ANSWER |
| 10 | P0 Phase A / Phase B (native ARA control) | PASS / MEASURED | Phase-B scoping: `REVIEW_ADVERSARIAL_20261014_b.md` (review #2, S-083). Heretic source check: `REVIEW_ADVERSARIAL_20261014.md` (review #1, S-065, `model.py:313`) | Only the `lora_A` reset finding was independently confirmed in source; deployed≠optimized and the resume re-draw were confirmed by the implementer (S-062/S-077) |
| 11 | S-191 norm-matched mean-gap comparator on VALIDATION (P2b) | DESCRIPTIVE — **NOT independently verified** | — | No reviewer or verifier has read these VAL numbers; review #5 saw only the TRAIN basket NM arms |
| 12 | Paired-floor / common-key re-check of all rank-1 cells | CORRECTION | `VERIFY_PAIRED_FLOOR_RECHECK.md/.json`, `research/heretic_csi/verify/paired_floor_recheck.py` (S-200) | F6's dispute upheld: the earlier verifier skipped the cross-arm key intersection. basket r1 VAL strictly largest under every floor; S-052/S-198 "2/57 under the strict floor" WITHDRAWN. The S-198 multiplicity downgrade STANDS |

**Adversarial reviews (8):** `REVIEW_ADVERSARIAL_20261014.md`, `_b`, `_c`, `_d`, `_e`, `REVIEW_ADVERSARIAL_20261015_f.md`,
`_g`, `_h`. Each was run by a fresh reviewer with no shared context with the implementer and barred from unread endpoints.

**PENDING verification:** P4 head-restricted evaluation; P6 rescue / H6a; any P7 read; the S-199 powered basket-r1 re-test (preregistered, not yet run); the S-191 NM VAL numbers (row 11).
