# P10.0 — Graded-score re-analysis of the behavioral nulls

**Status:** complete, CPU-only, no new data collected.
**Date:** 2026-08-05 · **Plan refs:** §0.5, §5/P10 of `reports/CAUSAL_CONTINUATION_MASTER_PLAN.md`
**Script:** `scripts/analyze_graded_reanalysis.py` (login node, no GPU, reads `raw.jsonl` only)

```
python scripts/analyze_graded_reanalysis.py --out-json <path>
# 4 run dirs, 26 s wall, seed 20260805, 10000 bootstrap resamples, 50000 sign-flip permutations
```

> ⚠ **This is a POST-HOC re-analysis of data collected for a binary endpoint.** The headline cell also
> **pools a pre-specified train/test split**, which was not the pre-registered analysis. Everything below
> is a **hypothesis for pre-registration in P10**, not a confirmation of one. Per-split numbers are
> reported for every cell precisely so the pooling can be audited.

---

## 1. What was re-analysed and why

The previous sprint concluded the concept circuit is **behaviorally inert** from **binary** McNemar tests
(MALICIOUS iff StrongREJECT ≥ 0.25). §0.5 showed those tests had post-hoc power **0.13 / 0.08** — they could
not have detected their own observed effect. The same `raw.jsonl` files already store the **graded 0–1
StrongREJECT score** that the binary label was thresholded from. This re-analysis re-runs the identical
paired design on the graded score. **No generation, no re-judging, no GPU** — only the stored scores.

Verified against the artifacts: in all four runs `label == MALICIOUS` **iff** `score ≥ 0.25` (checked on
every arm of every row), so the binary and graded endpoints are two views of one measurement. The score
takes 7–9 distinct values in {0, 0.125, …, 1.0}; the binary label discards all of that structure.

| cell | run dir | n | arms (baseline / ablation / random control) |
|---|---|---|---|
| BEHAV-CARRY / clearharm | `behav_carry_clearharm_20260804_100009_707831` | 86 (44 train, 42 test) | `baseline` / `carry_abl` / `rand_abl` |
| BEHAV-CARRY / curated | `behav_carry_curated_20260804_100428_707832` | 51 (30 / 21) | `baseline` / `carry_abl` / `rand_abl` |
| BEHAV-WRITE / clearharm | `behav_write_clearharm_L8_9_10_11_20260804_110157_707908` | 86 (44 / 42) | `baseline` / `write_abl` / `rand_pos_abl` |
| BEHAV-WRITE / curated | `behav_write_curated_L8_9_10_11_20260804_110156_707909` | 51 (30 / 21) | `baseline` / `write_abl` / `rand_pos_abl` |

Arm names were read from the raw schema, not guessed. No rows were dropped (0 `EMPTY` labels anywhere;
`n_paired` equals `n` in every cell).

---

## 2. Verdict on the expected finding

| expected (plan §0.5) | obtained | match |
|---|---|---|
| pooled clearharm carry effect ≈ **+0.074** | **+0.0741** | ✅ exact |
| permutation p ≈ **0.035** | **0.0337** | ✅ |
| random control stays null, p ≈ **0.36** | **p = 0.3588** | ✅ |
| binary McNemar for the same cell | pooled **p = 0.0923** (per split 0.289 / 0.375) | — |
| post-hoc binary power 0.129 / 0.083 | **0.135 / 0.086** (p₀ = 0.0894) · **0.133 / 0.085** (p₀ = 0.093) | ✅ within rounding |

**The §0.5 pilot numbers reproduce exactly.** But reproducing them is not the same as the claim surviving,
and three things in the full table cut against the strong reading:

1. 🔴 **The specificity contrast is null.** The random control is "null" only in the sense of *not
   significant*: its pooled point estimate is **+0.0392**, i.e. **53 % of the carry effect**. The direct
   within-item contrast `rand_abl_score − carry_abl_score` is **+0.0349, 95 % CI [−0.039, +0.110],
   permutation p = 0.382**. **The targeted ablation is not demonstrably better than a size-matched random
   one.** This is the load-bearing weakness and it is not visible in the §0.5 summary.
2. 🟠 **Neither split is significant on its own** (train p = 0.114, test p = 0.208). The p = 0.034 comes
   from pooling, which doubles n. Legitimate as an estimator, but not the pre-specified analysis.
3. 🔴 **Curated does not replicate** — it goes the *wrong way* (pooled **−0.0172**, p = 0.794).

**Conclusion: the binary null on BEHAV-CARRY/clearharm was indeed underpowered, and the graded endpoint
recovers a small positive effect — but the effect is not shown to be specific to the carry heads.
"Behaviorally inert" is not established; neither is "behaviorally necessary."** The honest statement is
*undetermined*, and P10 must be run to settle it.

---

## 3. Graded results — every phase × cohort × split, plus pooled

`d = score(baseline) − score(arm)`; **positive = the ablation reduced harmfulness.**
CI = 95 % paired percentile bootstrap, 10000 resamples, `default_rng(20260805)`.
`p_perm` = two-sided sign-flip permutation, 50000 permutations, `(1+#{|perm| ≥ |obs|})/(1+B)`.

| cell | split | arm | n | μ base | μ arm | **d** | SD | 95 % CI | p Wilcoxon | p t | **p perm** | dz |
|---|---|---|---:|---:|---:|---:|---:|---|---:|---:|---:|---:|
| CARRY/clearharm | train | `carry_abl` | 44 | 0.3182 | 0.2330 | **+0.0852** | 0.3386 | [−0.011, +0.188] | 0.0925 | 0.1023 | **0.1143** | +0.252 |
| CARRY/clearharm | train | `rand_abl` ⟂ | 44 | 0.3182 | 0.2528 | +0.0653 | 0.3457 | [−0.031, +0.173] | 0.2442 | 0.2168 | 0.2442 | +0.189 |
| CARRY/clearharm | test | `carry_abl` | 42 | 0.2946 | 0.2321 | **+0.0625** | 0.2951 | [−0.024, +0.152] | 0.1376 | 0.1773 | **0.2084** | +0.212 |
| CARRY/clearharm | test | `rand_abl` ⟂ | 42 | 0.2946 | 0.2827 | +0.0119 | 0.4065 | [−0.110, +0.134] | 0.8002 | 0.8504 | 0.8908 | +0.029 |
| **CARRY/clearharm** | **POOLED** | **`carry_abl`** | **86** | **0.3067** | **0.2326** | **+0.0741** | **0.3164** | **[+0.009, +0.142]** | **0.0343** | **0.0326** | **0.0337** | **+0.234** |
| CARRY/clearharm | POOLED | `rand_abl` ⟂ | 86 | 0.3067 | 0.2674 | +0.0392 | 0.3754 | [−0.039, +0.119] | 0.2984 | 0.3350 | 0.3588 | +0.105 |
| CARRY/curated | train | `carry_abl` | 30 | 0.3083 | 0.3458 | −0.0375 | 0.4759 | [−0.208, +0.129] | 0.7055 | 0.6692 | 0.7116 | −0.079 |
| CARRY/curated | train | `rand_abl` ⟂ | 30 | 0.3083 | 0.2833 | +0.0250 | 0.4012 | [−0.117, +0.167] | 0.8581 | 0.7354 | 0.8560 | +0.062 |
| CARRY/curated | test | `carry_abl` | 21 | 0.0595 | 0.0476 | +0.0119 | 0.2649 | [−0.095, +0.119] | 1.0000 | 0.8389 | 1.0000 | +0.045 |
| CARRY/curated | test | `rand_abl` ⟂ | 21 | 0.0595 | 0.1250 | −0.0655 | 0.2001 | [−0.161, +0.000] | 0.1025 | 0.1493 | 0.2521 | −0.327 |
| CARRY/curated | POOLED | `carry_abl` | 51 | 0.2059 | 0.2230 | −0.0172 | 0.4000 | [−0.127, +0.091] | 0.7432 | 0.7606 | 0.7944 | −0.043 |
| CARRY/curated | POOLED | `rand_abl` ⟂ | 51 | 0.2059 | 0.2181 | −0.0123 | 0.3338 | [−0.105, +0.078] | 0.6354 | 0.7942 | 0.8057 | −0.037 |
| WRITE/clearharm | train | `write_abl` | 44 | 0.3295 | 0.3239 | +0.0057 | 0.3001 | [−0.085, +0.091] | 0.5064 | 0.9007 | 0.9545 | +0.019 |
| WRITE/clearharm | train | `rand_pos_abl` ⟂ | 44 | 0.3295 | 0.3494 | −0.0199 | 0.3525 | [−0.122, +0.082] | 0.7053 | 0.7101 | 0.7570 | −0.056 |
| WRITE/clearharm | test | `write_abl` | 42 | 0.2470 | 0.2619 | −0.0149 | 0.4234 | [−0.140, +0.113] | 0.7784 | 0.8210 | 0.8569 | −0.035 |
| WRITE/clearharm | test | `rand_pos_abl` ⟂ | 42 | 0.2470 | 0.3036 | −0.0565 | 0.4022 | [−0.179, +0.062] | 0.3590 | 0.3675 | 0.3966 | −0.141 |
| WRITE/clearharm | POOLED | `write_abl` | 86 | 0.2892 | 0.2936 | −0.0044 | 0.3635 | [−0.081, +0.073] | 1.0000 | 0.9117 | 0.9412 | −0.012 |
| WRITE/clearharm | POOLED | `rand_pos_abl` ⟂ | 86 | 0.2892 | 0.3270 | −0.0378 | 0.3758 | [−0.116, +0.042] | 0.3599 | 0.3536 | 0.3755 | −0.101 |
| WRITE/curated | train | `write_abl` | 30 | 0.2958 | 0.2500 | +0.0458 | 0.3793 | [−0.087, +0.183] | 0.5136 | 0.5133 | 0.5686 | +0.121 |
| WRITE/curated | train | `rand_pos_abl` ⟂ | 30 | 0.2958 | 0.2667 | +0.0292 | 0.2290 | [−0.050, +0.113] | 0.3592 | 0.4911 | 0.5711 | +0.127 |
| WRITE/curated | test | `write_abl` | 21 | 0.0655 | 0.0357 | +0.0298 | 0.2335 | [−0.065, +0.131] | 0.4982 | 0.5657 | 0.6874 | +0.127 |
| WRITE/curated | test | `rand_pos_abl` ⟂ | 21 | 0.0655 | 0.0595 | +0.0060 | 0.2808 | [−0.113, +0.125] | 0.8875 | 0.9236 | 1.0000 | +0.021 |
| WRITE/curated | POOLED | `write_abl` | 51 | 0.2010 | 0.1618 | +0.0392 | 0.3245 | [−0.049, +0.127] | 0.3957 | 0.3923 | 0.4333 | +0.121 |
| WRITE/curated | POOLED | `rand_pos_abl` ⟂ | 51 | 0.2010 | 0.1814 | +0.0196 | 0.2492 | [−0.049, +0.088] | 0.5266 | 0.5767 | 0.6273 | +0.079 |

One-sided permutation p for the headline cell (the P10 pre-registration direction) is **0.0168**; for its
random control, **0.1801**. No rows were dropped in any of the 24 cells (`n_dropped = 0` everywhere).

⟂ = random control arm. **Exactly one of the 24 tests reaches p < 0.05**, and it is the pooled
CARRY/clearharm ablation arm. All three p-value families agree in every cell (Wilcoxon / t / permutation
never disagree about the 0.05 boundary), so the result is not an artifact of a particular test.

**BEHAV-WRITE is null on the graded endpoint too** (clearharm pooled −0.0044, p = 0.94). The graded
re-analysis rescues nothing for the L8–11 concept write. Note the plan's separate objection stands
independently: that ablation was **prefill-only**, so its null is uninterpretable regardless of endpoint.

---

## 4. Specificity contrast — the check that fails

Within-item `score(control) − score(treatment)`. Positive ⇒ the targeted ablation suppresses harm *more*
than a size-matched random ablation. This is the strongest available test that the effect is about the
**carry heads** rather than about **removing that much attention**.

| cell | split | n | contrast | SD | 95 % CI | p perm (2-sided) | p perm (1-sided) | dz |
|---|---|---:|---:|---:|---|---:|---:|---:|
| CARRY/clearharm | train | 44 | +0.0199 | 0.3223 | [−0.074, +0.119] | 0.7265 | 0.3667 | +0.062 |
| CARRY/clearharm | test | 42 | +0.0506 | 0.3826 | [−0.060, +0.167] | 0.4222 | 0.2103 | +0.132 |
| **CARRY/clearharm** | **POOLED** | **86** | **+0.0349** | 0.3513 | **[−0.039, +0.110]** | **0.3819** | **0.1912** | +0.099 |
| CARRY/curated | POOLED | 51 | −0.0049 | 0.3640 | [−0.108, +0.093] | 0.9670 | 0.5538 | −0.013 |
| WRITE/clearharm | POOLED | 86 | +0.0334 | 0.3022 | [−0.029, +0.097] | 0.3328 | 0.1660 | +0.111 |
| WRITE/curated | POOLED | 51 | +0.0196 | 0.3076 | [−0.064, +0.108] | 0.7011 | 0.3511 | +0.064 |

Every contrast is null, including one-sided. **No cell shows the targeted ablation beating its random
control.** The apparent carry effect is compatible with a generic "ablating ~9 attention heads slightly
degrades the completion" effect — the control arm's own +0.039 on clearharm is the direct evidence for
that alternative.

---

## 5. Binary side-by-side, power, and the exact test's granularity floor

`b` = 0→1 flips (ablation *added* harm), `c` = 1→0 flips (ablation *removed* harm). `floor` = the smallest
two-sided p the exact McNemar test can produce with that many discordant pairs — with 4 discordant pairs
the test **cannot** return anything below 0.0625 and therefore **cannot reject at α = 0.05 under any
outcome**. That is a hard, data-independent ceiling on what the binary analysis could ever have shown.

Power model (exact, no normal approximation): `N_disc ~ Bin(n, p01+p10)`; given `N_disc = m`, the 1→0 count
`~ Bin(m, p10/(p01+p10))`; reject iff the two-sided exact McNemar p ≤ 0.05. **Noise anchor** `p0` = the
empirical per-direction symmetric flip rate measured on the **random-control arms only**, pooled over all
four runs: `b = 25, c = 24, n = 274` ⇒ discordance 0.1788, **p₀ = 0.0894**. (§0.5 quotes 0.093; the
difference is which control arms were pooled and is immaterial — both are shown in §6.) Convention **A**
(primary, matches §0.5): `p01 = p0`, `p10 = p0 + δ`. Convention **B** (sensitivity): `p01 = p0 − δ/2`,
`p10 = p0 + δ/2`, which holds total discordance fixed. `δ` = the **observed** |ΔASR| in that cell.

| cell | split | arm | n | b | c | ΔASR | McNemar p | floor | power A | n@80 % A | power B | n@80 % B |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| CARRY/clearharm | train | `carry_abl` | 44 | 2 | 6 | +0.0909 | 0.2891 | 0.0078 | **0.135** | 270 | 0.174 | 182 |
| CARRY/clearharm | train | `rand_abl` ⟂ | 44 | 4 | 5 | +0.0227 | 1.0000 | 0.0039 | 0.027 | >4000 | 0.026 | >4000 |
| CARRY/clearharm | test | `carry_abl` | 42 | 1 | 4 | +0.0714 | 0.3750 | **0.0625** | **0.086** | 405 | 0.097 | 290 |
| CARRY/clearharm | test | `rand_abl` ⟂ | 42 | 4 | 5 | +0.0238 | 1.0000 | 0.0039 | 0.027 | >4000 | 0.025 | >4000 |
| **CARRY/clearharm** | **POOLED** | `carry_abl` | 86 | 3 | 10 | +0.0814 | **0.0923** | 0.0002 | 0.242 | 326 | 0.345 | 225 |
| CARRY/clearharm | POOLED | `rand_abl` ⟂ | 86 | 8 | 10 | +0.0233 | 0.8145 | 0.0000 | 0.047 | >4000 | 0.048 | >4000 |
| CARRY/curated | train | `carry_abl` | 30 | 6 | 3 | −0.1000 | 0.5078 | 0.0039 | 0.094 | 230 | 0.098 | 150 |
| CARRY/curated | train | `rand_abl` ⟂ | 30 | 2 | 3 | +0.0333 | 1.0000 | 0.0625 | 0.022 | 1549 | 0.017 | 1313 |
| CARRY/curated | test | `carry_abl` | 21 | 2 | 2 | +0.0000 | 1.0000 | **0.1250** | n/a | n/a | n/a | n/a |
| CARRY/curated | test | `rand_abl` ⟂ | 21 | 2 | 0 | −0.0952 | 0.5000 | **0.5000** | 0.045 | 250 | 0.030 | 166 |
| CARRY/curated | POOLED | `carry_abl` | 51 | 8 | 5 | −0.0588 | 0.5811 | 0.0002 | 0.081 | 564 | 0.091 | 429 |
| CARRY/curated | POOLED | `rand_abl` ⟂ | 51 | 4 | 3 | −0.0196 | 1.0000 | 0.0156 | 0.029 | >4000 | 0.028 | >4000 |
| WRITE/clearharm | train | `write_abl` | 44 | 3 | 2 | −0.0227 | 1.0000 | 0.0625 | 0.027 | >4000 | 0.026 | >4000 |
| WRITE/clearharm | train | `rand_pos_abl` ⟂ | 44 | 5 | 4 | −0.0227 | 1.0000 | 0.0039 | 0.027 | >4000 | 0.026 | >4000 |
| WRITE/clearharm | test | `write_abl` | 42 | 5 | 5 | +0.0000 | 1.0000 | 0.0020 | n/a | n/a | n/a | n/a |
| WRITE/clearharm | test | `rand_pos_abl` ⟂ | 42 | 5 | 3 | −0.0476 | 0.7266 | 0.0078 | 0.049 | 816 | 0.049 | 651 |
| WRITE/clearharm | POOLED | `write_abl` | 86 | 8 | 7 | −0.0116 | 1.0000 | 0.0001 | 0.033 | >4000 | 0.033 | >4000 |
| WRITE/clearharm | POOLED | `rand_pos_abl` ⟂ | 86 | 10 | 7 | −0.0349 | 0.6291 | 0.0000 | 0.070 | 1426 | 0.075 | 1201 |
| WRITE/curated | train | `write_abl` | 30 | 2 | 4 | +0.0667 | 0.6875 | 0.0312 | 0.049 | 456 | 0.043 | 333 |
| WRITE/curated | train | `rand_pos_abl` ⟂ | 30 | 1 | 2 | +0.0333 | 1.0000 | **0.2500** | 0.022 | 1549 | 0.017 | 1313 |
| WRITE/curated | test | `write_abl` | 21 | 2 | 2 | +0.0000 | 1.0000 | **0.1250** | n/a | n/a | n/a | n/a |
| WRITE/curated | test | `rand_pos_abl` ⟂ | 21 | 2 | 2 | +0.0000 | 1.0000 | **0.1250** | n/a | n/a | n/a | n/a |
| WRITE/curated | POOLED | `write_abl` | 51 | 4 | 6 | +0.0392 | 0.7539 | 0.0020 | 0.049 | 1154 | 0.049 | 953 |
| WRITE/curated | POOLED | `rand_pos_abl` ⟂ | 51 | 3 | 4 | +0.0196 | 1.0000 | 0.0156 | 0.029 | >4000 | 0.028 | >4000 |

`n/a` = observed δ is exactly 0, so "power at the observed effect" is undefined (it would be the type-I rate).
`>4000` = 80 % power is not reached within the search cap of 4000 pairs at that (tiny) effect.

**Headline power facts.**
- CARRY/clearharm train: power **0.135**; test: power **0.086**. A test with 9–14 % power did not, and could
  not, license the word "inert".
- Required n at 80 % power, convention A: **δ = 0.09 → n = 275** · **δ = 0.07 → n = 419** (at p₀ = 0.093:
  283 and 431). §0.5's "n ≈ 300 / n ≈ 450" is confirmed.
- **Four cells sit at or above the granularity floor** — CARRY/clearharm test (floor 0.0625) and both
  n = 21 curated test cells (floor 0.125–0.500) **could not have produced a significant result under any
  data whatsoever.** Reporting those as "null" was never meaningful.
- The random controls behave as controls should on the binary endpoint: **all 12 control cells have
  McNemar p ≥ 0.50**, and their pooled flip table is near-symmetric (25 up vs 24 down) — which is exactly
  what justifies using them as the p₀ noise anchor.

---

## 6. Robustness of the one positive cell

All checks on CARRY/clearharm POOLED (`d = +0.0741`, perm p = 0.0337):

| check | result | reading |
|---|---|---|
| items that moved at all | **22 / 86** (16 down-scored, 6 up-scored) | 74 % of items are exactly tied; the effect rests on 22 rows |
| leave-one-out permutation p | range **0.0085 – 0.0624** | dropping **one** item can push p above 0.05 |
| leave-one-out mean | range **+0.0632 – +0.0868** | the point estimate is stable |
| drop the 5 largest positive diffs | d = +0.0216, p = **0.4656** | 5 of 86 rows carry most of the signal |
| p₀ anchor = 0.0894 (all controls) vs 0.093 (§0.5) | power 0.135/0.086 vs 0.133/0.085 | anchor choice is immaterial |
| p₀ anchor = same-dir (0.1047 for this run) | power 0.127 / 0.082, n@80 % = 301 / 453 | reproduces §0.5's rounded "0.129/0.083, n ≈ 300/450" |
| Wilcoxon vs t vs permutation | 0.0343 / 0.0326 / 0.0337 | test choice is immaterial |

The effect is real *in this dataset* but **fragile**: it is a small shift carried by ~20 items, it is
between 0.03 and 0.06 away from the boundary, and its specificity control is not significant.

---

## 7. What this changes, and what to pre-register

**Corrections to the current claim set:**

1. ❌ **Retract** "the concept circuit is behaviorally inert" as a supported claim. It rests on binary tests
   with 8–14 % power, four of which were arithmetically incapable of rejecting.
2. ❌ **Do not** replace it with "the carry heads are behaviorally necessary." That would rest on a
   post-hoc endpoint switch, a post-hoc pooling of a pre-specified split, a failed specificity contrast, and
   a cohort that goes the other way.
3. ✅ **State:** *the behavioral necessity of the concept circuit is currently undetermined; the existing
   data are consistent with a small (≈ 0.07 graded, ≈ 0.08 ASR) carry-head effect and with zero, and the
   study lacked the power to separate them.*
4. ✅ **BEHAV-WRITE is null on both endpoints** — but its ablation was prefill-only, so this is
   uninterpretable and must be re-run decode-safe before any statement is made.

**Pre-registration for P10 (derived from, and therefore not testable on, these data):**

- **Primary endpoint:** graded StrongREJECT, paired difference `baseline − ablation`, **one-sided**
  (H₁ > 0), sign-flip permutation, 50000 perms, α = 0.05.
- **Primary comparison:** the **specificity contrast** `random_control − targeted`, not
  `baseline − targeted`. The baseline-vs-targeted test cannot distinguish "the carry heads matter" from
  "removing 9 heads matters", and in this data it does not.
- **Point estimate to power against:** +0.074 graded / +0.081 ΔASR. **n ≥ 275** for the binary endpoint at
  80 % power (δ = 0.09), **n ≥ 419** at δ = 0.07. The graded endpoint at the observed dz = 0.234 needs
  **n = 115** (one-sided) / **n = 146** (two-sided, paired t) for 80 % power — a **2.4× saving in n** at
  δ = 0.09 and **3.6×** at δ = 0.07. That, not the p-value, is the real argument for switching endpoint.
- **Splits:** analyse train and test separately and report both; pooling is permitted only as a
  pre-declared secondary estimator.
- **Cohorts:** clearharm and curated are **not** interchangeable here (opposite signs). Pre-register
  clearharm as primary and curated as an independent replication, and report a failure to replicate as a
  failure.
- **Must fix first:** the §0.4 split leakage (per-instruction `intent_cluster` ⇒ 64 % of rows straddle
  train/test at the concept level) — otherwise train/test agreement means nothing.

---

## 8. Reproduction

```
cd doublespeak_causality
/home/sharifm/students/omeryosef/miniconda3/envs/poc_stage2/bin/python \
    scripts/analyze_graded_reanalysis.py --out-json outputs_scratch/p10_0.json
# sensitivity on the noise anchor:
... scripts/analyze_graded_reanalysis.py --p0-source same-dir
```

Deterministic: a fresh `default_rng(20260805)` is constructed per statistic, so every number reproduces in
isolation and is independent of evaluation order. `mcnemar_power` was validated against a brute-force
`O(n²)` enumeration of the exact test's rejection region at four (n, p01, p10) settings — agreement to
8 decimal places. All arm means, SDs, dz values and discordant counts in §3/§5 for CARRY/clearharm were
independently recomputed from `raw.jsonl` with a separate pure-stdlib script (no numpy, no scipy), deriving
the binary labels from the raw scores rather than the stored labels; all matched to 6 decimals.
