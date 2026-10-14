# DRAFT log entry (F2) — P2b TRAIN-K4 read (DESCRIPTIVE; in-sample; VALIDATION decides A–E)

## S-1xx — 2026-10-14 — P2b TRAIN-K4 read (frozen commands; descriptive)

**Setup and gating.** I ran EXACTLY the frozen TRAIN commands in `configs/heretic_csi/ANALYSIS_COMMANDS_P2B.md`
(sha256 c1b7089d…, committed at S-133). All code sha256s matched the doc: p2b_analyze c1b11327…, overlap_check
4552d70f…, deployed_residual ba2057bd…, and the three reused frozen helpers.

Preconditions met before the read:
- Main eval: basket r1 = 167 arms (1023012 n-503 + resume 1034929 n-501); basket r4 = 163 (1023508); button r1 =
  167 (1023264 + resume 1035131); button r4 = 163 (1023509). All DONE rc=0, one model load each.
- Add-on: 1036622 / 1036626, 41/43 each. The 2 non-ok arms are the expected KO/BASE_MEANBIAS rc=4.
- Overlap: all five overlap files are OVERLAP_OK, with max |Δy| = 0.0 (n-503 ≡ n-501, bitwise).

Outputs (sha256):
- `reports/heretic_csi/p2b_basket_primary_train.json` 0b871a0b…
- `p2b_button_primary_train.json` b3dd4adb…
- deployed residual: `p2b_{basket,button}_r{1,4}_deployed_train.json` (03343d2e…, 77d51605…, 8523ad2b…, 4b30cddf…)

Population after the BASE option-mass ≥0.05 key set:
- basket: 179 keys / 63 of 67 TRAIN domains
- button: 239 keys / 67 domains
- Unit = domain. TRAIN-K4 is IN-SAMPLE for CAND/DER/SHUF (fit on full TRAIN) and out-of-fit for RAND.

**Gates (all cells):**
- No shared, primary or secondary VOID.
- Manipulation KO−BASE: basket −0.253, button −0.214.
- Whole-state rescue FULL−KO: basket +0.142, button +0.109.
- KO_IDENT ≡ KO (max |dy| 0).
- No collapsed primary/secondary arm.
- Preservation BASE_CAND−BASE y: −0.042 to +0.004; option mass change ≤ 0.01.

**Primary (CAND = ΔW at all rows vs 81 norm-matched controls; Holm over {1,4}):**

| cell | CAND−KO | recovery [CI] | rank/82 (p) | Holm p | verdict | RAND /62 | DER /16 | SHUF /6 |
|---|---|---|---|---|---|---|---|---|
| basket r1 | +0.176 | 1.24 [1.09, 1.41] | 9 (0.110) | 0.110 | DOES NOT PASS | 1 | 9 | 1 |
| basket r4 | +0.206 | 1.45 [1.27, 1.69] | 2 (0.024) | 0.0488 | PASS (TRAIN, descriptive) | 1 | 2 | 1 |
| button r1 | +0.185 | 1.70 [1.53, 1.91] | 13 (0.159) | 0.317 | DOES NOT PASS | 1 | 13 | 1 |
| button r4 | +0.170 | 1.55 [1.41, 1.73] | 14 (0.171) | 0.317 | DOES NOT PASS | 1 | 14 | 1 |

**Secondary (CWONLY = CAND only at the codeword row vs 76 codeword-row controls; Holm over {1,4}):**

| cell | rank/77 | Holm p | CWONLY recovery [CI] | verdict |
|---|---|---|---|---|
| basket r1 | 1 | 0.026 | 1.40 [1.27, 1.58] | PASS |
| basket r4 | 1 | 0.026 | 1.32 [1.19, 1.49] | PASS |
| button r1 | 9 | 0.234 | 1.62 [1.49, 1.78] | DOES NOT PASS |
| button r4 | 13 | 0.234 | 1.54 [1.43, 1.67] | DOES NOT PASS |

Both secondary PASSes carry the amendment-2 forking-path disclosure and need VALIDATION replication.

**What the numbers say (descriptive, TRAIN, in-sample):**
1. **Every fitted operator moves installation strongly.** Recovery is 1.2–1.7× the whole-state rescue, i.e. it
   OVERSHOOTS KO_FULL. Random norm-matched rank-r edits never come close: CAND ranks 1 of 62 against RAND in every cell.
2. **The discriminating controls are the FITTED ones.**
   - DER = domain-deranged pairing, no role swap, so it keeps the KO→clean direction. Mean control recovery is
     0.27–0.37 overall, and several DER fits beat CAND.
   - At their RAW fitted norms, DER/SHUF beat CAND in 3 of 4 cells (CAND last of 16/6); basket r4 is the exception
     (CAND 5/16 vs DER).
   - So most of the effect is carried by "write the generic KO→clean shift", which ANY KO→clean fit learns,
     whatever the domain pairing.
   - Basket r4 is the only cell where the paired fit is specifically better than the deranged fits under the
     preregistered norm-matched family (DER 2/16).
3. **Application site matters; fit site does not.**
   - Position contrast, with both arms using CAND's factors (norm-matched by construction): CWONLY ≈ CAND, while
     ATLAST ≈ 0 (recovery −0.01 to +0.02) in all cells.
   - NEUT (fit at the LAST row, own norm 12–20 vs CAND 39–60, applied at all rows) recovers as much as CAND
     (1.32–1.63).
   - So the operator acts THROUGH the codeword row, but fitting at the codeword row is not needed to obtain an
     operator that does so. "Position-aware fitting" is NOT supported; "acts at the codeword row" is
     (descriptive).
4. **Decomposition.** The y gain is concept-up plus codeword-down for basket (Δlogp_concept +1.32/+1.60,
   Δlogp_codeword −0.90/−1.04). For button it is mostly codeword-down (+0.61/+0.43 vs −1.00/−0.98).
5. **Input-independent comparators.**
   - KO_MEANBIAS (full-norm, all rows) COLLAPSED the readout (median option mass 1.4e-3 basket, 3e-6 button), so
     it is VOID; the all-rows input-independent comparison is CANNOT ANSWER and the "input-conditional" wording
     stays SUSPENDED (amendments 4/6). The eligible flag is False, as on any TRAIN split.
   - KO_CWMEANBIAS (the full mean gap at the codeword row only): recovery 0.70 basket, −0.07 button.
   - CAND − CWMEANBIAS is positive with CI-lo > 0 in all cells (basket +0.076 / +0.106, button +0.193 / +0.178).
   - CWONLY − CWMEANBIAS is likewise positive.
   - This is descriptive and does not unlock any wording.
6. **Deployed vs fitted (codeword row).** Gap closure 0.55–0.58 deployed vs 0.60–0.68 fitted. Upstream edits shift
   module inputs by 0.43–0.59 of the clean−KO input gap, and about 0.36 of it toward clean. Compounding is modest.
7. **TRAIN pattern (descriptive only, not an outcome):**
   - basket: primary specific at r4 only; secondary specific at r1 and r4.
   - button: not specific at either rank, primary or secondary.
   - On TRAIN this would map to D. **Outcomes A–E are decided ONLY on VALIDATION (amendment 5).**

**MUST NOT SAY (from this read):**
- No outcome letter.
- No "button lacks a carrier" beyond TRAIN.
- No "position-aware operator" (the fit site doesn't matter).
- No "input-conditional" wording (suspended).
- No "mechanism".
- Recovery >1 means overshoot relative to the whole-state rescue, NOT "better than causal".
- The basket r4 primary PASS sits at Holm p = 0.0488, just under α, at rank 2/82, in-sample: fragile until VALIDATION.

**Next:** the VALIDATION read after the parent logs this entry. That needs basket val 1023578/9, button val
1036679/80, the add-on val jobs and their overlap files. Amendment-6 NM TRAIN arms (job 1040065) are running;
analyse them with `--addon-nm`, descriptive, in a separate output.
