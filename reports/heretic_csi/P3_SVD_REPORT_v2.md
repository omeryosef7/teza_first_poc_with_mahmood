# P3 v2 — SVD / geometry of the learned P2b weight operators (DESCRIPTIVE)

Supersedes `P3_SVD_REPORT.md` (kept for provenance). Sources: `P3_svd_descriptive_v2.json`, `P3_write_direction_v2.json`, `P3_alignment_aniso.json`. TRAIN-fitted operators (objective mse / steer 0.3). Geometry of the FIT only — no endpoint, no causal claim. Total norm = sqrt(sum of squared per-module Frobenius norms). Effective rank = **energy-entropy** rank exp(H(s²/Σs²)) (smaller than the s/Σs version).

## Per-cell summary (CAND)

| cw | rank | total ‖ΔW‖ | o_proj share of ‖ΔW‖² | top-3 layers by ‖ΔW‖² share | median energy-entropy eff. rank | median top-1 Frobenius frac | median ‖ΔW‖/‖W‖ |
|---|---|---|---|---|---|---|---|
| basket | 1 | 10.07 | 0.786 | L7 0.22, L13 0.16, L18 0.15 | 1.00 | 1.000 | 0.0228 |
| basket | 2 | 11.87 | 0.774 | L6 0.25, L7 0.16, L15 0.10 | 1.19 | 0.966 | 0.0323 |
| basket | 4 | 11.60 | 0.736 | L6 0.17, L7 0.15, L17 0.11 | 2.03 | 0.787 | 0.0438 |
| basket | 8 | 16.62 | 0.592 | L17 0.14, L18 0.13, L7 0.08 | 4.75 | 0.406 | 0.0560 |
| basket | 16 | 16.04 | 0.651 | L18 0.15, L17 0.14, L7 0.09 | 4.81 | 0.422 | 0.0511 |
| basket | 32 | 14.41 | 0.770 | L7 0.13, L17 0.13, L18 0.12 | 2.15 | 0.819 | 0.0523 |
| basket | 50 | 15.28 | 0.775 | L7 0.15, L6 0.13, L18 0.12 | 1.61 | 0.909 | 0.0606 |
| button | 1 | 8.82 | 0.733 | L7 0.34, L13 0.18, L18 0.11 | 1.00 | 1.000 | 0.0225 |
| button | 2 | 10.30 | 0.635 | L7 0.19, L6 0.15, L13 0.09 | 1.84 | 0.758 | 0.0308 |
| button | 4 | 12.70 | 0.709 | L7 0.18, L6 0.17, L13 0.09 | 1.86 | 0.814 | 0.0400 |
| button | 8 | 15.11 | 0.658 | L7 0.12, L17 0.12, L6 0.09 | 3.93 | 0.513 | 0.0550 |
| button | 16 | 19.83 | 0.575 | L17 0.11, L13 0.09, L9 0.09 | 6.19 | 0.381 | 0.0692 |
| button | 32 | 16.85 | 0.795 | L7 0.13, L17 0.13, L6 0.12 | 1.25 | 0.961 | 0.0678 |
| button | 50 | 17.61 | 0.795 | L7 0.14, L6 0.14, L17 0.12 | 1.30 | 0.958 | 0.0688 |

## Cross-codeword overlap of CAND write subspaces (same rank, same module): mean cos² of principal angles (null k/4096)

| rank | median over modules | min | max |
|---|---|---|---|
| 1 | 0.764 | 0.249 | 0.887 |
| 2 | 0.582 | 0.193 | 0.796 |
| 4 | 0.513 | 0.244 | 0.666 |
| 8 | 0.537 | 0.231 | 0.744 |
| 16 | 0.522 | 0.258 | 0.650 |
| 32 | 0.547 | 0.261 | 0.713 |
| 50 | 0.553 | 0.254 | 0.727 |

## Alignment vs the ANISOTROPIC null (review #2 fix)

Statistic: squared projection of the reference direction on the write subspace U_k (k=min(r,4)). p_aniso = upper-tail empirical p against 2000 directions drawn from the module's clean codeword-row output covariance; p_iso = the old isotropic null (for comparison). PLS-4 uses a dimension-matched 4-d subspace null (isotropic and anisotropic).

| cw | rank | #stats | #p_iso ≤ 0.01 | #p_aniso ≤ 0.01 | stats with p_aniso ≤ 0.01 |
|---|---|---|---|---|---|
| basket | 1 | 66 | 23 | 0 | none |
| basket | 2 | 66 | 24 | 0 | none |
| basket | 4 | 66 | 34 | 0 | none |
| basket | 8 | 66 | 30 | 0 | none |
| basket | 16 | 66 | 30 | 0 | none |
| basket | 32 | 66 | 28 | 0 | none |
| basket | 50 | 66 | 29 | 0 | none |
| button | 1 | 66 | 20 | 0 | none |
| button | 2 | 66 | 27 | 0 | none |
| button | 4 | 66 | 36 | 0 | none |
| button | 8 | 66 | 37 | 0 | none |
| button | 16 | 66 | 36 | 0 | none |
| button | 32 | 66 | 32 | 0 | none |
| button | 50 | 66 | 33 | 0 | none |

## What the operator WRITES: the mean KO→clean output gap

- **basket**: share of per-prompt gap energy that is the common mean shift: min 0.44 / median 0.59 / max 0.75.
  - r1:CAND: mean |cos(U1, mean gap)| = 1.000
  - r1:DER0: mean |cos(U1, mean gap)| = 1.000
  - r1:SHUF0: mean |cos(U1, mean gap)| = 0.999
  - r2:CAND: mean |cos(U1, mean gap)| = 0.998
  - r2:DER0: mean |cos(U1, mean gap)| = 0.958
  - r2:SHUF0: mean |cos(U1, mean gap)| = 0.990
  - r4:CAND: mean |cos(U1, mean gap)| = 0.976
  - r4:DER0: mean |cos(U1, mean gap)| = 0.530
  - r4:SHUF0: mean |cos(U1, mean gap)| = 0.982
  - r8:CAND: mean |cos(U1, mean gap)| = 0.617
  - r8:DER0: mean |cos(U1, mean gap)| = 0.822
  - r8:SHUF0: mean |cos(U1, mean gap)| = 0.990
  - r16:CAND: mean |cos(U1, mean gap)| = 0.679
  - r16:DER0: mean |cos(U1, mean gap)| = 0.572
  - r16:SHUF0: mean |cos(U1, mean gap)| = 0.992
  - r32:CAND: mean |cos(U1, mean gap)| = 0.956
  - r32:DER0: mean |cos(U1, mean gap)| = 0.433
  - r32:SHUF0: mean |cos(U1, mean gap)| = 0.999
  - r50:CAND: mean |cos(U1, mean gap)| = 0.998
  - r50:DER0: mean |cos(U1, mean gap)| = 0.986
  - r50:SHUF0: mean |cos(U1, mean gap)| = 0.998
- **button**: share of per-prompt gap energy that is the common mean shift: min 0.52 / median 0.66 / max 0.78.
  - r1:CAND: mean |cos(U1, mean gap)| = 1.000
  - r1:DER0: mean |cos(U1, mean gap)| = 1.000
  - r1:SHUF0: mean |cos(U1, mean gap)| = 0.999
  - r2:CAND: mean |cos(U1, mean gap)| = 0.890
  - r2:DER0: mean |cos(U1, mean gap)| = 0.961
  - r2:SHUF0: mean |cos(U1, mean gap)| = 0.981
  - r4:CAND: mean |cos(U1, mean gap)| = 0.930
  - r4:DER0: mean |cos(U1, mean gap)| = 0.790
  - r4:SHUF0: mean |cos(U1, mean gap)| = 0.997
  - r8:CAND: mean |cos(U1, mean gap)| = 0.717
  - r8:DER0: mean |cos(U1, mean gap)| = 0.730
  - r8:SHUF0: mean |cos(U1, mean gap)| = 0.997
  - r16:CAND: mean |cos(U1, mean gap)| = 0.581
  - r16:DER0: mean |cos(U1, mean gap)| = 0.467
  - r16:SHUF0: mean |cos(U1, mean gap)| = 0.994
  - r32:CAND: mean |cos(U1, mean gap)| = 0.999
  - r32:DER0: mean |cos(U1, mean gap)| = 0.994
  - r32:SHUF0: mean |cos(U1, mean gap)| = 0.999
  - r50:CAND: mean |cos(U1, mean gap)| = 0.998
  - r50:DER0: mean |cos(U1, mean gap)| = 0.986
  - r50:SHUF0: mean |cos(U1, mean gap)| = 0.999
- **cross-codeword** |cos(mean gap basket, mean gap button)|: L6.o_proj 0.84, L6.down_proj 0.83, L7.o_proj 0.91, L7.down_proj 0.87, L8.o_proj 0.93, L8.down_proj 0.90, L9.o_proj 0.91, L9.down_proj 0.89, L10.o_proj 0.90, L10.down_proj 0.92, L11.o_proj 0.93, L11.down_proj 0.91, L12.o_proj 0.94, L12.down_proj 0.89, L13.o_proj 0.88, L13.down_proj 0.88, L14.o_proj 0.84, L14.down_proj 0.86, L15.o_proj 0.70, L15.down_proj 0.80, L16.o_proj 0.81, L16.down_proj 0.68, L17.o_proj 0.72, L17.down_proj 0.61, L18.o_proj 0.50, L18.down_proj 0.50

## Reading (descriptive only)

- At ranks 1–2 the candidate and every fitted control (DER, SHUF) write along the mean KO→clean output gap g (|cos(U1, g)| ≈ 1.00). This is **largely expected by construction** (review #2): a DER pairing is a permutation of all rows, so its mean target−source equals g exactly, and a rank-1 MSE fit of a mostly-common shift recovers g. Consequence (unchanged): candidate-vs-DER/SHUF tests input-side (read, A) specificity only; candidate-vs-RAND also tests the write direction; an input-independent mean-gap (bias) control would be needed to separate 'adds the mean shift' from 'input-conditional operator'.
- The mean gap is a large common component (see shares above) and is largely codeword-general at L6–14, less so at L18 (cross-codeword cosines above).
- Alignment with refusal / d_surface / PLS: under the ANISOTROPIC null **no statistic reaches p ≤ 0.01 in any cell** (table). The anisotropic null mean is 0.01–0.22 (q99 0.07–0.54) because the write subspace lies in the high-variance part of each module's output; the reference directions project on it LESS than a typical activation direction does, while still MORE than an isotropic random direction (the isotropic null flags many modules). The two nulls bracket the answer and all absolute values are tiny (squared projection ≤ ~0.04, |cos| ≤ ~0.2). Positive-control sanity: a genuinely aligned direction (squared projection ≈ 1, e.g. the mean gap g itself at r1) would exceed every anisotropic q99 (max 0.54), so the null is not powerless. **Conclusion: no evidence that the learned operators write along refusal, d_surface or the P2a probe axes.**
- PLS-4 (L18) uses a dimension-matched 4-d null; see `P3_alignment_aniso.json` (`p_iso4`, `p_aniso4`).
