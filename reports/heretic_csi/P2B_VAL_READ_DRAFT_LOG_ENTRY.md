# DRAFT log entry (F2) — P2b VALIDATION read (DECIDES the preregistered outcome; amendment 5)

## S-1xx — 2026-10-15 — P2b VALIDATION read: outcome D (basket specific at r4 only; button at neither)

### Setup and gating

I ran EXACTLY the frozen VAL commands in `configs/heretic_csi/ANALYSIS_COMMANDS_P2B.md` (sha256 cb145d55…,
committed S-139d). Code matched: p2b_analyze 5bafd092…, and the three reused frozen helpers.

Preconditions met:

| item | status |
|---|---|
| basket VAL r1 / r4 (1023578 / 1023579, both n-503) | 167/167, 163/163 arms |
| button VAL r1 / r4 (1036679 n-503 / 1036680 n-501) | 167/167, 163/163 arms |
| VAL add-ons 1040101 / 1040122 (n-501) | 45/47 each; the 2 others are the expected KO/BASE_MEANBIAS rc=4 |
| button VAL n-501↔n-503 overlap 1040170 | 4/4 arms |
| overlap files | all OVERLAP_OK, max \|Δy\| = 0.0 (`overlap_buttonvaln501_1040170_r0`, `overlap_addon_{basket,button}_val_*`) |

All jobs: DONE rc=0, one model load each.

Outputs (sha256): `reports/heretic_csi/p2b_basket_primary_validation.json` b16004ad…;
`p2b_button_primary_validation.json` 792bf34f….

Population (BASE option-mass key set): basket 145 keys / 23 VAL domains; button 203 / 23. TEST never used.

Gates: no shared, primary or secondary VOID; KO−BASE −0.280 / −0.302; FULL−KO +0.140 / +0.142;
identity exact; preservation |BASE_CAND−BASE| ≤ 0.038.

### Primary (CAND = ΔW at all rows vs 81 norm-matched controls; Holm over {1,4}) — VALIDATION

| cell | CAND−KO [CI] | recovery [CI] | frac BASE−KO | rank/82 | Holm p | VERDICT | RAND/62 | DER/16 | SHUF/6 | TRAIN verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| basket r1 | +0.168 [0.116, 0.228] | 1.20 [0.98, 1.45] | 0.60 | 11 | 0.134 | DOES NOT PASS | 1 | 11 | 1 | DOES NOT PASS (9/82) |
| basket r4 | +0.210 [0.143, 0.290] | 1.50 [1.22, 1.83] | 0.75 | 2 | **0.0488** | **PASS** | 1 | 2 | 1 | PASS (2/82, 0.0488) |
| button r1 | +0.246 [0.206, 0.294] | 1.73 [1.52, 1.94] | 0.81 | 14 | 0.342 | DOES NOT PASS | 1 | 14 | 1 | DOES NOT PASS |
| button r4 | +0.230 [0.191, 0.279] | 1.62 [1.44, 1.81] | 0.76 | 15 | 0.342 | DOES NOT PASS | 1 | 15 | 1 | DOES NOT PASS |

### Secondary (CWONLY vs 76 codeword-row-only controls; Holm over {1,4}) — VALIDATION

| cell | rank/77 | Holm p | CWONLY recovery [CI] | VERDICT | TRAIN |
|---|---|---|---|---|---|
| basket r1 | 1 | 0.026 | 1.43 [1.22, 1.68] | PASS | PASS |
| basket r4 | 1 | 0.026 | 1.41 [1.20, 1.66] | PASS | PASS |
| button r1 | 9 | 0.234 | 1.67 [1.51, 1.84] | DOES NOT PASS | DOES NOT PASS |
| button r4 | 12 | 0.234 | 1.64 [1.49, 1.80] | DOES NOT PASS | DOES NOT PASS |

The basket secondary PASS replicates on VALIDATION with the frozen operator, as amendment 2 requires. It still
carries the forking-path disclosure: the test was added after a 12-row smoke hinted at it.

### PREREGISTERED OUTCOME (amendment 5; VALIDATION only)

- "Specific at r" = primary PASS at r. Basket is specific at r4 and not at r1; button is specific at neither.
- **Outcome = D** ("basket specific at some r ∈ {1,4}, button at neither").
- **Minimal specific rank:** basket = 4; button = ">4 (untested beyond)".
- Every TRAIN verdict was reproduced on VALIDATION (same pass/fail in all 8 primary+secondary cells). Basket r4's
  rank 2/82 was identical on both splits.

### Descriptive context (VALIDATION; does not change the outcome)

1. **Specificity comes only from the fitted controls.** Every operator recovers strongly and overshoots the
   whole-state rescue (recovery 1.2–1.7; 0.60–0.81 of the BASE−KO gap). Random norm-matched edits never compete
   (CAND 1/62 everywhere). Only the FITTED deranged-pairing controls (DER) discriminate.
   - CAND − mean(DER) [CI]: basket r4 +0.018 [0.009, 0.028] (the only clearly positive cell); basket r1
     −0.004 [−0.027, 0.011]; button r1 −0.005 [−0.014, 0.001]; button r4 −0.017 [−0.033, −0.005].
   - At RAW fitted norms DER beats CAND in 3/4 cells (CAND 16/16); basket r4 is 7/16.
2. **Where the edit acts (amendment 7; replicates TRAIN).**
   - CAND acts THROUGH the codeword row: CWONLY ≈ CAND (0.70–0.79 of the gap), ATLAST ≈ 0 (≤ 0.008).
   - NEUT (fit at the last row) recovers as much only when applied at ALL rows (0.69–0.75 of the gap). At the
     codeword row only it gives 0.03–0.07; at the last row only, 0.01–0.05.
   - So the fit site determines WHERE the operator acts, not HOW MUCH it rescues.
3. **Decomposition.** Basket's gain is mostly concept-up (Δlogp_concept +1.24 / +1.59; codeword −0.70 / −0.77).
   Button's is mostly codeword-down (concept +0.95 / +0.81; codeword −1.17 / −1.17).
4. **Input-independent comparators.**
   - KO_MEANBIAS collapsed the readout again (median option mass 1.1e-3 basket, 2.5e-6 button), so it is VOID:
     the all-rows input-independent comparison is CANNOT ANSWER and the "input-conditional" wording stays
     SUSPENDED (amendments 4/6; eligible flag False).
   - KO_CWMEANBIAS recovers 0.82 (basket) / 0.25 (button).
   - CAND − CWMEANBIAS: basket r1 +0.053 [0.030, 0.079], r4 +0.095 [0.055, 0.151]; button +0.21 / +0.19.
     This is descriptive only.
5. **Not computed on VALIDATION:** the deployed-vs-fitted residual, because there are no VAL captures
   (TRAIN only, stated). The amendment-6 MEANBIAS_NM VAL arms were not run (plans/addon_nm_val.sh is ready).
   Descriptive ranks {2,8,16,32,50} are running on TRAIN-K4 (evalB 1040759 / 1040766, evalC 1040700 / 1040701).

### WHAT WE CAN DEFEND (P2b)

- A learned rank-4 weight-space operator (ΔW = BA on o_proj/down_proj, layers 6–18) for basket rescues semantic
  installation under the codeword-row knockout, and ranks 2/82 against 81 rank- and norm-matched controls on
  held-out VALIDATION (Holm p = 0.0488). The same is true on TRAIN.
- Basket: the operator's effect is carried at the codeword row. Applied there alone it ranks first of 76
  codeword-row controls at r1 and r4 (Holm p = 0.026). This is the secondary test, with its disclosure.
- Button: no rank-1 or rank-4 weight operator in this family is specific beyond fitted controls.
- Preregistered outcome D: dimensionality (up to rank 4) does not make button specific.

### WHAT WE MUST NOT SAY

- No "input-conditional", "semantic operator" or "mechanism" wording: the MEANBIAS comparator collapsed, so the
  wording is suspended.
- No "button is uninstallable": button operators rescue strongly but not specifically.
- No "basket r1 operator works": it doesn't PASS, unlike the P2a rank-1 PLS axis.
- No claim beyond rank 4: ranks 2/8/16/32/50 are descriptive curve shape only.
- No "position-aware fitting is required": a last-row fit rescues equally, acting elsewhere.
- Basket r4's PASS is at the second-best attainable Holm p (0.0488 < 0.05). Fragile, though replicated.
- Recovery > 1 means overshoot relative to the whole-state rescue, not "more causal".
- Contrast with P2a: P2a's activation-space button r4 passed VAL, but P2b's weight operator at button r4 does not;
  they are different intervention families and must not be merged.
