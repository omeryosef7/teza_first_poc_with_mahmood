# Adversarial review #5 — P2b TRAIN-K4 read (S-135) — 2026-10-14

Reviewer: independent agent. Read-only on existing files; no commits; no GPU jobs. **No P2b VALIDATION dir or
endpoint was read** (`hcsi_p2b_*_val_*` never opened; the verifier only matches `hcsi_p2b_<cw>_k4_<ARM>_<ts>_<pid>`).

Recomputation code (my own, written from the prereg text; it does not import or copy `p2b_analyze.py`):
`research/heretic_csi/verify/verify_p2b_train.py` (sha256 `7a90de17…6648`). Output:
`<scratchpad>/review5/verify_p2b_train.json` (sha256 `931feefc…53f1`). Run with poc_stage2 python, `-I`, ~26 s CPU.

## 1. Independent recomputation — AGREES in all 8 cells

The verifier selects exactly one run dir per arm tag: DONE.json status ok and 268 rows. The two partial r1 dirs left
by the preempted jobs are skipped: basket `KO_CWRAND_r1_36_…114934` (71 rows, no DONE) and button
`KO_CWRAND_r1_58_…114856` (178 rows, no DONE). In each cell the arms come from both run-dir pid suffixes:
basket r1 2510108 + 4059094, button r1 2510383 + 4088301. The overlap dirs (k4ovl, k4aovl, k4ovln501, k4nmovl)
never match the strict prefix. Every arm's `exclude_prompt_ids` is `runargs/heretic_csi/exclude_<cw>_K4.txt`, and
every arm uses the codeword's ts116m bank (asserted).

Method: y = σ(logp_concept − logp_codeword), with key = (domain, slot). The key set is the keys where BASE option
mass ≥ 0.05. The statistic is the mean over domains of the per-domain mean of (arm − KO). The rank p is
(1 + #controls ≥ cand)/(N+1). Holm uses m=2 over {1,4}. Recovery uses a percentile domain bootstrap
(B = 10 000, my own seeds).

| cell | keys/doms | stat | rank | Holm p | recovery [CI] (mine) | verdict (mine) | analyzer |
|---|---|---|---|---|---|---|---|
| basket prim r1 | 179/63 | 0.17620 | 9/82 | 0.1098 | 1.238 [1.090, 1.422] | not pass | same |
| basket prim r4 | 179/63 | 0.20639 | 2/82 | 0.0488 | 1.450 [1.262, 1.694] | PASS | same |
| button prim r1 | 239/67 | 0.18540 | 13/82 | 0.3171 | 1.700 [1.533, 1.918] | not pass | same |
| button prim r4 | 239/67 | 0.16957 | 14/82 | 0.3171 | 1.555 [1.410, 1.730] | not pass | same |
| basket CWONLY r1 | 179/63 | 0.19949 | 1/77 | 0.0260 | 1.402 [1.260, 1.582] | PASS | same |
| basket CWONLY r4 | 179/63 | 0.18757 | 1/77 | 0.0260 | 1.318 [1.181, 1.491] | PASS | same |
| button CWONLY r1 | 239/67 | 0.17688 | 9/77 | 0.2338 | 1.622 [1.492, 1.788] | not pass | same |
| button CWONLY r4 | 239/67 | 0.16768 | 13/77 | 0.2338 | 1.538 [1.430, 1.669] | not pass | same |

The stats, ranks and Holm p's match to every printed digit. The CIs differ only in the 3rd decimal, because the
bootstrap seeds differ. Gates reproduced:
- KO−BASE: −0.25286 basket, −0.21358 button.
- FULL−KO: +0.14233 basket, +0.10905 button.
- KO_IDENT ≡ KO: max |dy| 0.
- KO_CAPOP replays KO_CAND: max |Δlogodds| 0.0 in all 4 cells.

Sub-family ranks reproduced (RAND, SHUF, DER, DERRAW, SHUFRAW): see §2a. The descriptive add-on numbers also
reproduce: CWMEANBIAS recovery 0.703 basket and −0.074 button; CAND−CWMEANBIAS +0.076, +0.106, +0.193, +0.178.
Deployed gap closure is 0.543–0.576, so S-135's "0.55–0.58" should read 0.54–0.58 (LOW).

## 2. Attacks on the S-135 interpretation

### (a) "most of the effect is the generic KO→clean shift" — half right; "shift" is the wrong word (MED)

The ranks reproduce. CAND is 1/62 against RAND in every cell and 1/6 against SHUF (norm-matched). Against DER it
ranks 9, 2, 13 and 14 out of 16. At raw norms CAND is 16/16 against DER and 6/6 against SHUF, except basket r4,
where it is 5/16 and 5/6.

The mean recovery of the 15 DER fits nearly equals CAND's:

| | basket r1 | basket r4 | button r1 | button r4 |
|---|---|---|---|---|
| mean DER recovery | 1.20 | 1.30 | 1.73 | 1.65 |
| CAND recovery | 1.24 | 1.45 | 1.70 | 1.55 |

The paired domain difference CAND − mean(DER) is:

| cell | CAND − mean(DER) [CI] | reading |
|---|---|---|
| basket r1 | +0.006 [−0.002, +0.012] | includes 0 |
| basket r4 | +0.021 [+0.010, +0.034] | CAND ahead |
| button r1 | −0.0035 [−0.0063, −0.0009] | CAND significantly worse than the average deranged fit |
| button r4 | −0.011 [−0.019, −0.003] | CAND significantly worse than the average deranged fit |

The button result is not reported in S-135 and should be.

So "the rescue is not domain-pairing-specific" is supported. "Shift" is not, because it implies a constant offset.
The constant-offset comparators fall well short of CAND:
- KO_CWMEANBIAS (the mean gap at the codeword row) recovers 0.70 for basket and −0.07 [−0.29, 0.12] for button.
- The amendment-6 MEANBIAS_NM arms exist for basket only. Their KO overlap re-run equals the main KO (|dy| 0).
  My independent, unlogged, descriptive read gives recovery 0.39 (r1) and 0.67 (r4).
- CAND − NM is +0.120 [0.086, 0.157] at r1 and +0.111 [0.078, 0.147] at r4.
- The button NM arm is not finished (no DONE).

What the controls show is that any operator trained to map KO codeword-row states to clean ones, under any domain
pairing, does about as well. That operator is input-dependent, not a constant shift.

The "(P3: shared write direction)" link goes beyond this data and should be marked as a hypothesis.

### (b) "fit site doesn't matter" — magnitude claim OK; the Heretic sufficiency clause is untested (HIGH)

NEUT is applied at ALL rows. Its opspec is `op:…:NEUT` with no `where`, and it has hook_calls 27 872, the same as
CAND. NEUT ≈ CAND within the CI in all 4 cells. NEUT−CAND:

| cell | NEUT − CAND [CI] |
|---|---|
| basket r1 | +0.021 [−0.001, +0.046] |
| basket r4 | −0.018 [−0.042, +0.006] |
| button r1 | −0.007 [−0.019, +0.004] |
| button r4 | +0.008 [−0.005, +0.021] |

NEUT − CWONLY is also ≈ 0 in all cells.

The norm contrast "12–20 vs 39–60" uses the SUM of per-module Frobenius norms. NEUT also has 2 zero modules
(L6), so the sum overstates the gap. The output-side measure, mean last-position delta norm, is 0.11–0.12 for NEUT
vs 0.18–0.24 for CAND, a ratio of about 0.5–0.6, not about 0.3.

The CWONLY ≈ CAND / ATLAST ≈ 0 contrast was measured with **CAND's** factors only. No NEUT_CWONLY or NEUT_ATLAST
arm exists. NEUT was fit at the last row and is also applied there, so it may act at the last row directly. The
S-135 statement "Heretic's last-row fit + codeword-row action would suffice" is therefore **untested**.

One more point is unreported: on basket r1, NEUT outranks all 81 primary controls (1/82). It is not norm-matched,
so this is descriptive only. NEUT's rank against DER is 1, 7, 16 and 10 out of 16.

### (c) Recovery > 1 ("overshoot") — real, but the denominator is a partial rescue (MED wording)

The denominator is not small or noisy:
- No basket domain has FULL−KO ≤ 0; 3 button domains do.
- Dropping domains with FULL−KO < 0.05 leaves recovery at 1.19, 1.39, 1.54 and 1.43.
- A 10%-trimmed ratio gives 1.26, 1.50, 1.70 and 1.56.
- CAND exceeds FULL in 36/63, 45/63, 62/67 and 60/67 domains.

The cause is KO_FULL itself. It is a layer-18 query-position rescue (config `rescue_layer 18`,
`rescue_positions query`), and it restores only 56% (basket) and 51% (button) of the BASE−KO gap.

Measured against the BASE−KO gap, CAND restores:

| cell | CAND / (BASE−KO) [CI] |
|---|---|
| basket r1 | 0.70 [0.62, 0.76] |
| basket r4 | 0.82 [0.74, 0.89] |
| button r1 | 0.87 [0.80, 0.95] |
| button r4 | 0.79 [0.74, 0.86] |

Row-mean CAND y − BASE y is −0.03 to −0.08. **Nothing overshoots clean.** S-135 should report the BASE-gap
fraction next to "recovery" and drop the word "OVERSHOOT".

### (d) Basket r4 primary PASS (Holm 0.0488) — LODO-stable but structurally marginal and in-sample-confounded (HIGH)

The pass survives every sensitivity check except the raw-norm one:
- **LODO:** 63/63 single-domain drops keep rank 2/82, so Holm stays at 0.0488.
- **Strict paired floor:**
  - Option mass ≥ 0.05 in BASE, KO and CAND: rank 2, Holm 0.0488.
  - Floor in every family arm (150 keys / 60 domains): rank 2.
- **Row-level statistic:** rank 2.
- **Raw-norm DER:** 5/16, p = 0.31. Not distinguishable from the deranged fits.

Why it is marginal:
- PASS needs rank ≤ 2, because Holm p = 2·rank/82. One DER (DER_r4_10, 0.2098) already beats CAND (0.2064).
- The 3rd-ranked control is 0.0068 below CAND, about 3% of the statistic.
- The strict all-arms floor moves **basket r1** to rank 3 (Holm 0.0488, PASS). So the r1/r4 split itself is not
  robust to the floor rule.

The in-sample confound is not declared. CAND was fit to the exact (KO, clean) pairs being scored. DER was fit to
mismatched targets. On TRAIN, CAND therefore has a fitting advantage over DER that grows with capacity: r4 has 4×
the parameters, and its fit gap closure is 0.627 vs 0.594 at r1. "Pairing-specific only at the higher rank" is
exactly what in-sample memorisation predicts. TRAIN cannot separate the two; only VALIDATION can.

### (e) CWONLY basket PASS — robust on TRAIN, but the r4 margin is a near-tie (MED)

- LODO: 63/63 keep Holm 0.026 at both ranks.
- Strict floors: r1 stays 1/77; r4 drops to 2/77. Holm is still 0.026, because r1 = 1/77 carries the family.
- Margins over the best CWDER: r1 +0.011, r4 **+0.0004**.

The CWDER in-sample confound in (d) applies here too, as does the amendment-2 forking-path disclosure.
"CWONLY ≈ CAND" holds only loosely: CWONLY − CAND is +0.023 [0.014, 0.032] for basket r1, −0.019 [−0.036, −0.003]
for basket r4, and −0.009 [−0.016, −0.002] for button r1. These are small but nonzero.

### (f) Leakage / in-sample inflation beyond what is declared

- Declared: TRAIN-K4 is in-sample for CAND, DER and SHUF, and out-of-fit for RAND.
- **Not declared:** the asymmetry in (d)/(e). Being in-sample does not inflate CAND and DER equally, because only
  CAND's targets are the evaluated pairs. TRAIN "pairing-specificity" is therefore upward-biased.
- NEUT is in-sample too.
- No other leakage found:
  - RAND seeds are fixed.
  - CAND selection (pooled fitting-side CV) never touched y.
  - No VAL rows appear in K4: every arm's exclude file is the K4 list.
  - No duplicate or partial dirs were used.
  - Overlap-host equivalence: the NM-overlap KO equals the main KO, |dy| 0.

## 3. What TRAIN can and cannot say (amendment 5)

TRAIN can say (descriptive, in-sample):
- Fitted operators restore 70–87% of the KO gap. Random edits do nothing.
- The rescue is about equally available from deranged-pairing fits.
- The constant mean-gap bias at the codeword row does less.
- CAND's effect needs the codeword row: CWONLY carries it, ATLAST ≈ 0.
- A last-row fit reaches similar recovery magnitude.

TRAIN cannot say:
- Any outcome letter. S-135's "would map to outcome D" contradicts the draft's own MUST-NOT ("No outcome letter").
- "Pairing-specific" (confounded, see (d)).
- "Heretic's last-row fit would suffice" (untested, see (b)).
- "Shift" in the sense of a constant offset (see (a)).
- "Overshoot" (see (c)).

## Summary (≤25 lines)

1. RECOMPUTE: all 8 TRAIN cells (primary + CWONLY) are reproduced exactly from raw dirs (stat, rank, Holm,
   verdict). The bootstrap CIs agree to ±0.01. Cross-job r1 selection is correct; the 2 partial dirs were ignored.
2. HIGH — S-135 "fit site does not matter ⇒ Heretic's last-row fit + codeword-row action would suffice": the second
   half is untested, because no NEUT_CWONLY/ATLAST arm exists and NEUT is applied at all rows, including its own
   fit row. Fix: "A last-row fit (NEUT) reaches statistically indistinguishable TRAIN recovery (NEUT−CAND CI ∋ 0 in
   all cells), so codeword-row fitting is not necessary for this magnitude. Where NEUT acts was not tested."
3. HIGH — basket r4 "pairing-specific": the CAND-vs-DER comparison is in-sample-asymmetric (CAND fit on the scored
   pairs, DER on mismatched targets). This bias was not declared. Fix: "basket r4 CAND outranks 14/15 deranged fits
   in-sample, where the paired fit has a built-in fitting advantage; pairing-specificity is untested until
   VALIDATION."
4. MED — basket r4 PASS fragility: LODO 63/63 and the strict floors keep rank 2, but rank 2 is the pass boundary,
   one DER already beats CAND, and the raw-norm DER rank is 5/16. The strict all-arms floor also makes basket r1
   pass (rank 3, Holm 0.0488). Fix: "LODO-stable but at the pass boundary; the r1/r4 split is floor-sensitive."
5. MED — "generic KO→clean shift": the constant-offset arms do less (CWMEANBIAS 0.70 / −0.07; basket MEANBIAS_NM
   0.39 / 0.67). In button, CAND is significantly BELOW the mean deranged fit (−0.004, −0.011, CI < 0); this is
   unreported. Fix: "most of the rescue is reproduced by any KO→clean-fitted operator regardless of domain pairing
   (not pairing-specific); it is not a constant shift". Mark P3 as a hypothesis.
6. MED — "OVERSHOOT": the denominator KO_FULL (L18 query rescue) restores only 51–56% of BASE−KO. CAND restores
   0.70–0.87 of the KO gap and stays below clean. Fix: report the BASE-gap fraction and drop "overshoot".
7. MED — "TRAIN pattern would map to outcome D" violates the read's own no-outcome-letter rule. Delete it.
8. MED — CWONLY basket r4 margin over the best CWDER is +0.0004 (a tie), and the floor drops it to 2/77. The PASS is
   carried by r1 = 1/77. "CWONLY ≈ CAND" differs by a small but nonzero amount (CIs exclude 0 in 3/4 cells).
9. LOW — NEUT norm contrast uses the sum of module Frobenius norms; the output delta ratio is about 0.5–0.6. Deployed
   gap closure is 0.54–0.58, not 0.55–0.58.
10. No VAL data read. No other leakage found: K4 exclude files are correct, CAPOP replay is exact, and the overlap
    and NM-overlap KO are bit-equal.
