# Adversarial review #6 — P2b VALIDATION read (S-156) — 2026-10-15

Reviewer: independent agent. Read-only on existing files; no commits; no GPU jobs. Own code
`research/heretic_csi/verify/verify_p2b_val.py` (not derived from `p2b_analyze.py`); numbers in
`reports/heretic_csi/VERIFY_P2B_VAL.{md,json}`.

## 0. Bottom line
- **All 8 VAL cells, all gates, the VOID screens and the outcome mapping reproduce exactly ⇒ outcome D stands.**
  No leakage, wrong-population, wrong-split or provenance problem found.
- Two claims in S-156 need correction: (i) the basket r4 PASS is described as "replicated but fragile". On VAL it is
  much more fragile than it was on TRAIN. (ii) "P2a and P2b DISAGREE for button" is not a valid inference. The two
  tests use different nulls, sites and meanings of "rank".

## 1. Recomputation (agrees; details in VERIFY_P2B_VAL.md)
| cell | rank | Holm | verdict | agree |
|---|---|---|---|---|
| basket prim r1 / r4 | 11/82 / 2/82 | 0.134 / 0.0488 | no / PASS | yes / yes |
| button prim r1 / r4 | 14/82 / 15/82 | 0.342 / 0.342 | no / no | yes / yes |
| basket CWONLY r1 / r4 | 1/77 / 1/77 | 0.026 / 0.026 | PASS / PASS | yes / yes |
| button CWONLY r1 / r4 | 9/77 / 12/77 | 0.234 / 0.234 | no / no | yes / yes |

Other checks that agree:
- **Gates:** KO−BASE −0.280 / −0.302 and FULL−KO +0.140 / +0.142. IDENT and CAPOP are exact (0.0). Every arm fired
  hooks. Controls are norm-matched to ≤ 6e-8 and rank-matched. No collapse.
- **Descriptive numbers:** CAND − mean(DER), the sub-family and raw-norm ranks, the position/NEUT fractions,
  CWMEANBIAS (0.82 / 0.25) and the domain-level decomposition all match S-156 and the draft.

## 2. Robustness of the PASSes
**basket primary r4 (Holm 0.0488 at rank 2/82) — HIGH (wording).** The PASS is real under the frozen rule, but it
sits at the boundary on every axis:
- **Beaten by one control, KO_DER_r4_10, on both splits.** "Rank 2/82 identical on both splits" is partly the same
  frozen control beating the same frozen operator. It is not independent confirmation of the ordering.
- **Rank 3 is 0.00009 away.** The next control, KO_DER_r4_7, sits 0.00009 below CAND (0.21034 vs 0.21043). At rank 3
  the Holm p would be 0.073.
- **LODO is not stable.** Leaving one domain out gives rank 2 in 14/23 drops, rank 3 in 8 and rank 4 in 1. Holm is
  ≥ 0.05 in **9 of 23** drops (max 0.098). TRAIN was 63/63 stable.
- **The statistic matters.** A row-level statistic gives rank 3 (Holm 0.073). Swapping DER for raw-norm DER gives
  rank 7/82 (p 0.085). CAND − best DER, paired, is −0.010 [−0.023, +0.002]. CAND sits only +1.36 SD above the DER mean.
- **Strict paired floors keep rank 2** (Holm 0.0488).

**basket secondary CWONLY r1/r4 (PASS 1/77):** robust.
- LODO rank 1 in 23/23 and strict floors rank 1.
- CWONLY − mean(CWDER) is +0.020 / +0.019 with CI > 0.
- The margin over the best CWDER is small (+0.004), and its paired CI includes 0.
- This is the stronger basket result of P2b. It still carries the amendment-2 forking-path disclosure.

## 3. Interpretation attacks
**F1 (HIGH) "the weight-level operator does NOT reproduce the activation-space button r4 carrier; the two intervention
families disagree for button."** The two tests are not comparable:
- **(a) Different null.**
  - P2a's controls are random orthonormal subspaces plus SHUF. P2b button CAND ranks **1/62 against every random
    norm-matched edit** in both cells (p 0.016), and 1/6 against SHUF.
  - Under P2a's kind of null, P2b button would also look specific. P2b fails only against the 15 fitted
    domain-deranged operators (DER), a control class P2a never had.
  - The tests ask different questions: "better than random directions" vs "better than an equally-trained fit to
    the wrong pairing".
- **(b) Different site and scope.**
  - P2a patches a rank-4 PLS activation subspace at L18, at one query position (rel −6).
  - P2b edits ΔW on o_proj/down_proj across 26 modules (L6–18), at all rows. It acts through the codeword row
    (CWONLY ≈ CAND, ATLAST ≈ 0), upstream of and away from P2a's site.
- **(c) Different "rank".** P2a's r4 is a 4-dim activation subspace. P2b's r4 is rank 4 per module × 26 modules, up
  to about 104 write directions. "Button at r4" is not the same quantity in the two tests.
- **(d) Different effect regime and multiplicity.**
  - P2a rescues about 9% of the whole-state rescue (recovery 0.09). P2b overshoots (1.6).
  - P2a: Holm over {1,16,4} with 200 controls. P2b: Holm over {1,4} with 81 controls.
- The population is the same (203 button keys / 23 VAL domains in both), so that is not the difference.
- **Correct wording:** "Under P2b's stricter fitted-control null, the weight operator does not detect a
  button-specific carrier: button CAND beats every random edit but not fits trained on deranged pairings. This
  neither confirms nor contradicts P2a's L18 activation-subspace result, which was tested against random/SHUF
  subspaces at a different site."
- Basket has the same non-comparability: P2a r1 specific vs P2b r4 only.

**F2 (MED) "pairing-specific" on VAL.**
- VAL domains are unseen by both CAND and DER. Both are frozen TRAIN fits, and there is no VAL-domain pairing for
  DER to derange.
- So CAND − mean(DER) > 0 on VAL (basket r4 only, +0.018 [0.009, 0.028]) means this: **an operator fit to the correct
  TRAIN targets generalizes to new domains slightly better than operators fit to deranged TRAIN targets.** It says
  nothing about domain-pair information for the VAL domains.
- For button the paired fit is significantly worse than the average deranged fit at r4 (−0.017 [−0.032, −0.005]).
  At r1 the CI includes 0.

**F3 (MED) NEUT / position claims.**
- "NEUT acts distributed" is an inference. NEUT at all rows restores 0.69–0.75 of the gap, NEUT at the codeword row
  restores 0.03–0.07, and NEUT at the last row 0.01–0.05. That shows only that NEUT's effect is **not carried by the
  codeword row or the last row alone**. Which rows carry it, and whether the effect is additive, was not tested.
- "Fit site determines WHERE, not HOW MUCH" needs qualifying. On VAL, basket r1 NEUT − CAND = **+0.040
  [0.013, 0.067]**, so NEUT is larger. Button r1 = −0.020 [−0.042, −0.0002], so NEUT is smaller. Correct: "comparable
  magnitude (within ±0.04 of the gap), differing significantly in both directions by cell".
- Unreported: basket r1 NEUT (not norm-matched, ~0.43× CAND's summed module norm) ranks 1/82 against the basket r1
  primary family. The same holds for CWONLY > CAND at basket r1 (+0.032 [0.017, 0.051]): applying CAND off the
  codeword row slightly hurts. That is consistent with r1 failing primary while passing secondary.

**F4 (LOW).**
- "Button gain mostly codeword-down": −1.17 vs +0.95 / +0.81 nats, about 55–59%. Say "more codeword-down than
  concept-up".
- The MEANBIAS arms are complete 230-row dirs (DONE ok). The rc=4 is the post-write tail gate, so "45/47" is
  bookkeeping only.

## 4. Leakage / population / provenance
**No row or domain leakage:**
- 0/23 VAL domains in TRAIN-K4 or in the fit captures; 0 VAL prompt_ids in the captures.
- Factor sha16 is identical across TRAIN and VAL arms; no refit.
- One complete dir per arm; overlap dirs excluded; button cross-host covered by OVERLAP_OK (|Δy| 0).

**Keying.** VAL has `dev|slotN` and `heldout|slotN` per domain. The analyzer's `family_slot` keys them correctly, and
a naive slot key would collide.

**VAL-informed choices: none found in P2b.**
- Amendments 5–7 predate the read by their text.
- Outcome D is identical under the base-prereg D definition, so it is robust to the amendment-5 remap.
- Caveats (LOW–MED):
  - The VAL split had already been read in P2a (S-049/S-072/S-126). P2b VAL is held out from the *fit*, but it is
    not a virgin split.
  - The button overlap job (21:xx) necessarily read per-row VAL y (equality only).
  - NFS atime cannot independently prove no earlier peek: the overlap read did not update atime.

## 5. Wording fixes for S-156 (append as corrections; S-156 text stands)
1. Replace "replicated but fragile" with: "basket r4 passes on VAL at the boundary: one control (the same KO_DER_r4_10
   as TRAIN) beats it, and rank 3 is 9e-5 away. On VAL it is not LODO-stable (Holm ≥ 0.05 in 9/23 single-domain
   drops), and it does not pass under a row-level statistic or raw-norm DER. Treat it as a marginal pass under the
   frozen rule."
2. Replace "the two intervention families disagree for button" with the F1 wording ("does not detect …; neither
   confirms nor contradicts P2a").
3. Replace "pairing-specific" (basket r4, VAL) with: "the correctly-paired TRAIN fit generalizes to held-out domains
   slightly better than deranged-pairing fits (+0.018 [0.009, 0.028]; basket r4 only)".
4. Replace "NEUT acts distributed" with: "NEUT's effect is not carried by the codeword or last row alone; where it acts
   is untested". Also add basket r1 NEUT > CAND and CWONLY > CAND.
5. Name basket CWONLY (LODO 23/23) as P2b's most robust basket result, with its forking-path disclosure.
