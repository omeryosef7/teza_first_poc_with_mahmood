# Phase 8.1 — α calibration for the refusal-direction ablation

**Plan:** `reports/CAUSAL_CONTINUATION_MASTER_PLAN.md` §5 P8.1.
**Analyzer:** `scripts/analyze_alpha_calibration.py` (this report is its output plus framing).
**Machine-readable output:** `outputs/alpha_calibration.json`.
**Model:** `meta-llama/Llama-3.1-8B-Instruct`; refusal direction `outputs/stage_gcg_full/refusal_direction_llama_L18.pt` (L18).
**Snapshot:** 2026-08-05 ~20:15 IDT.

| cohort | run dir | SLURM | status | n |
|---|---|---|---|---|
| curated | `behav_refusal_curated_asweep0.0-0.25-0.5-0.75-1.0-1.5-2.0_20260805_171236_716015` | 716015 | **COMPLETE** (RUNMETA + DONE + summary + raw + gens) | 51/51 |
| clearharm | `behav_refusal_clearharm_asweep0.0-0.25-0.5-0.75-1.0-1.5-2.0_20260805_171237_716014` | 716014 | **PROVISIONAL — still running** (no `summary.json`, no `DONE.json`) | 78/86 |

Reproduce:

```
python doublespeak_causality/scripts/analyze_alpha_calibration.py \
    --md reports/_p8_1_tables.md          # both default run dirs
python doublespeak_causality/scripts/analyze_alpha_calibration.py \
    --run curated=<dir> --selection-split train
```

**The statistics are not reimplemented.** The within-item estimator
`D_i = Y_i(1,1) − Y_i(1,0) − Y_i(0,1) + Y_i(0,0)`, the 10 000-resample paired percentile bootstrap,
the 50 000-flip two-sided sign-flip permutation, the `D_i` distribution and the ceiling `I_max` are
imported from `scripts/analyze_interaction_2x2.py` (P8.0). The analyzer only rebinds that module's
`CELLS` so cells (0,1) and (1,1) point at the α-specific arms, and adds the arm table, the specificity
McNemar and the selection rule. Seed `20260805`, identical to P8.0.

Cell map at each α (all four cells measured **within item**, so the baselines cancel exactly):

| cell | arm | meaning |
|---|---|---|
| (0,0) | `direct_base` | no Doublespeak, no ablation |
| (1,0) | `ds_base` | Doublespeak alone |
| (0,1) | `direct_refabl_a<α>` | refusal-direction ablation alone, strength α |
| (1,1) | `ds_refabl_a<α>` | both |
| — | `direct_randabl_a<α>` | **specificity control**: norm-matched random direction, same α |

---

## Read this first — two facts that qualify every number below

### 1. The StrongREJECT judge noise floor is ~2 pp. Any ΔASR below it means nothing.

α = 0.0 is an **exact numerical no-op**: the hook computes `h − α·proj·d`, which at α = 0 is `h` in IEEE
arithmetic. It was confirmed empirically — the `direct_base` and `direct_refabl_a0.0` generations were
sha256-hashed (text never inspected) and **all pairs are byte-identical**. The judge nevertheless returns
different verdicts on some of them. That difference is pure StrongREJECT nondeterminism with the model,
the prompt and the generated text all held exactly constant — the cleanest possible measurement of the
floor, and stricter than the earlier 7.5 % replicate-flip estimate, which conflated judge noise with real
generation differences.

Recomputed by this analyzer on the current snapshots (α = 0 vs `direct_base`, pooled):

| cohort | n | label flips | score changes | max \|Δscore\| | ΔASR |
|---|---|---|---|---|---|
| curated | 51 | **1 (2.0 %)** | 2 (3.9 %) | 0.75 | −0.020 |
| clearharm (partial) | 78 | **1 (1.3 %)** | 5 (6.4 %) | **1.00** | +0.013 |

⇒ **A |ΔASR| below ≈ 2 pp is indistinguishable from judge nondeterminism.** On n = 51 that is one item;
on n = 78 it is 1.6 items. Cells at or under the floor are marked **‡** in the tables.

Three consequences that are easy to miss, so they are stated here and not in a footnote:

- **The floor is measured per arm. `Î` is a contrast of four judged arms**, so `Î`'s own noise floor is at
  least 2 pp and plausibly larger (errors partially cancel, but do not vanish).
- Therefore the near-zero `Î` values are **"no interaction detectable"**, not "interaction measured to be
  zero". Specifically **clearharm α = 0.25 gives `Î_binary` = −0.013 (1.3 pp) — below the floor**, and
  curated α = 0.0 gives −0.020 (2.0 pp) — exactly at it.
- Byte-identity was verified by hashing on the curated 51 and on the clearharm rows present at the time of
  that check. For the clearharm rows added since, byte-identity is *inferred* from the α = 0 arithmetic
  rather than re-hashed. The score-change rate on clearharm (6.4 %) and the max |Δscore| (1.00) are both
  higher than the previously recorded 4.5 % / 0.75, so the floor is, if anything, slightly worse than
  first measured — not better.

### 2. `Î` tracks `I_max`. That is a ceiling signature, not a mechanism.

`I_max = 1 − ASR(1,0) − ASR(0,1) + ASR(0,0)` is the largest interaction the design can arithmetically
express. It is a function of the **marginal** cells only — it contains no information whatsoever about the
joint cell (1,1), which is the only place a real interaction could live. A mechanism therefore has no
reason to move with it. **It moves with it almost perfectly.**

Pooled, across the 7-point α grid:

| cohort | Spearman(`I_max`, `Î_binary`) | Pearson | Spearman(`I_max`, `Î_score`) | Pearson |
|---|---|---|---|---|
| curated (n=51) | **+0.955** | +0.943 | +0.883 | +0.935 |
| clearharm (n=78, provisional) | **+0.991** | +0.957 | +0.937 | +0.918 |

Side by side, pooled:

| α | curated `I_max` | curated `Î_bin` | clearharm `I_max` | clearharm `Î_bin` |
|---|---|---|---|---|
| 0.0 | +0.745 | −0.020 ‡ | +0.654 | +0.000 ‡ |
| 0.25 | +0.510 | −0.176 | +0.487 | −0.013 ‡ |
| 0.5 | +0.451 | −0.216 | +0.282 | −0.103 |
| 0.75 | +0.373 | −0.294 | +0.231 | −0.128 |
| 1.0 | +0.373 | −0.333 | +0.231 | −0.154 |
| 1.5 | +0.353 | −0.353 | +0.141 | −0.205 |
| 2.0 | **+0.412 ↑** | **−0.196 ↑** | +0.051 | −0.269 |

(‡ in this table marks an `Î` whose magnitude is at or below the ~2 pp judge noise floor. In the generated
tables further down, ‡ marks the *specificity* ΔASR instead — same meaning, different column.)

The last row is the sharpest version of the point. On curated the ceiling **reverses** between α = 1.5 and
α = 2.0 (`I_max` +0.353 → +0.412), and `Î` reverses with it (−0.353 → −0.196). So this is not merely "two
quantities that both happen to be monotone in α" — `Î` follows the ceiling's non-monotonicity as well.

**What this does and does not license.** It does *not* prove that no interaction exists. It shows that at
every α where the design is saturated, `Î` is confounded with the available headroom, so the *magnitude* —
and, at high α, the *sign* — of `Î` is not interpretable as mechanism. The only doses where `Î` is worth
reading are the ones with a large `I_max`; and at exactly those doses (curated α = 0, clearharm α = 0.25)
`Î` is **at or below the judge noise floor**, i.e. additive/undetectable rather than sub-additive. This
points against the P8.0 headline ("sub-additive ⇒ shared refusal bottleneck") and towards the ceiling
explaining it, but at n = 51/78 it settles nothing on its own.

**Deliberately absent: the headroom-vs-saturated decomposition of `Î`.** Splitting items into those where
neither factor alone jailbreaks and those already saturated *looks* like it would adjudicate this. It
cannot. In the headroom subgroup `Y(1,0) = Y(0,1) = 0` by construction, so
`D_i = Y(1,1) + Y(0,0) ≥ 0` **mechanically**; in the saturated subgroup the algebra forces `D_i ≤ 0` just as
mechanically. Both halves are determined by the selection, not by the model, so the split is evidence in
neither direction. It nearly produced a reported "+0.83 synergy among headroom items" — a serious error.
The analyzer does not compute it, on purpose (see `CONTINUATION_PROGRESS.md`, tick-15 self-correction; the
plan's own §P8.4 requires such a subgroup to be defined on a *separate, pre-registered* calibration split).

---

## Headline answers

**curated (COMPLETE, n = 51): NO α qualifies.** The dose response is too steep — `ASR(0,1)` jumps from
0.294 at α = 0 (the no-op) straight to 0.529 at α = 0.25, stepping clean over the 0.20–0.40 band. Landing
in the band would need roughly α ≈ 0.1, which was not run. Every α > 0 has `I_max` ≥ +0.35 (so the *ceiling*
criterion is satisfied throughout) but none has an in-band ASR. Same answer selecting on train, on test, or
pooled. Independently of α, curated is a poor cohort for an interaction test: `ds_base` ASR = 0.275 is
*below* `direct_base` ASR = 0.314, i.e. the attack is **net-negative by ASR** here (the known
concept-dilution effect), and its random control is the less flat of the two (ASR 0.235–0.333 against a
0.314 baseline).

**clearharm (PROVISIONAL, n = 78/86): α = 0.25 is the operating point** — `ASR(0,1)` = 0.295 (band
0.20–0.40 ✓) and `I_max` = +0.487 (≥ +0.33 ✓, and 2.1× the +0.231 available at α = 1.0). It is the *only*
qualifying dose, so the tie-break never fires, and train, test and pooled all select it. **This cohort is
still running; re-run the analyzer when `summary.json` appears before citing any clearharm number.**

**Specificity holds across the whole dose range on both cohorts** — this is the first time the project has
had the random-direction control at anything other than α = 1.0. At α = 0 the refusal- and random-ablation
arms agree to within the judge noise floor (ΔASR −0.020 ‡ curated, +0.000 ‡ clearharm), exactly as a no-op
must. At every α > 0 the gap is +0.179 to +0.641 with paired exact McNemar p ≤ 0.0042 (curated) and
p ≤ 0.0005 (clearharm) — 9× to 32× the noise floor. The random direction is essentially inert on refusal:
`refusal_rate` 0.667–0.725 against a 0.686 baseline (curated) and 0.846–0.872 against 0.846 (clearharm),
while the true refusal direction drives it down to 0.216 (curated, α = 1.5) and 0.141 (clearharm, α = 2.0).

---

## Full tables

Generated verbatim by `scripts/analyze_alpha_calibration.py`. Column key: `d+refabl` =
`direct_refabl_a<α>` = cell (0,1); `d+randabl` = `direct_randabl_a<α>` = specificity control;
`ds+refabl` = `ds_refabl_a<α>` = cell (1,1). `Ihat bin` / `Ihat score` are the same estimator on the
binary MALICIOUS label and on the graded 0–1 StrongREJECT score. `sat. by 1 factor` counts items already
jailbroken by Doublespeak alone **or** ablation alone — the items with no headroom left.

### curated — FINAL  (n=51)
run_dir: `behav_refusal_curated_asweep0.0-0.25-0.5-0.75-1.0-1.5-2.0_20260805_171236_716015`

**Judge noise floor (measured on THIS cohort, alpha=0 no-op, byte-identical generations): 1/51 labels flipped (2.0%), 2/51 scores changed (3.9%), max |dscore| = 0.75, dASR = -0.0196. Any |dASR| below ~2 pp is indistinguishable from judge nondeterminism.**

#### curated / train (n=30)

| alpha | ASR d+refabl | refusal d+refabl | ASR d+randabl | refusal d+randabl | ASR ds+refabl | refusal ds+refabl | **I_max** | **Ihat bin** | CI95 bin | p bin | **Ihat score** | CI95 score | p score | D=+2 | D=-2 | sat. by 1 factor | dASR ref-rand | McNemar p |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0.0 | 0.267 | 0.700 | 0.300 | 0.700 | 0.333 | 0.000 | **+0.633** | **-0.033** | [-0.133,+0.067] | 1.0000 | **-0.013** | [-0.108,+0.075] | 0.8573 | 0 | 0 | 15/30 | -0.033 | 1.0000 |
| 0.25 | 0.567 | 0.367 | 0.233 | 0.700 | 0.400 | 0.000 | **+0.333** | **-0.267** | [-0.467,-0.067] | 0.0393 | **-0.188** | [-0.350,-0.021] | 0.0367 | 0 | 0 | 22/30 | +0.333 | 0.0129 |
| 0.5 | 0.667 | 0.267 | 0.300 | 0.700 | 0.400 | 0.000 | **+0.233** | **-0.367** | [-0.600,-0.133] | 0.0119 | **-0.304** | [-0.512,-0.096] | 0.0111 | 0 | 1 | 23/30 | +0.367 | 0.0010 |
| 0.75 | 0.733 | 0.200 | 0.267 | 0.700 | 0.467 | 0.000 | **+0.167** | **-0.367** | [-0.600,-0.133] | 0.0125 | **-0.263** | [-0.446,-0.075] | 0.0134 | 0 | 1 | 24/30 | +0.467 | 0.0001 |
| 1.0 | 0.633 | 0.233 | 0.267 | 0.700 | 0.367 | 0.000 | **+0.267** | **-0.367** | [-0.700,-0.067] | 0.0515 | **-0.267** | [-0.546,+0.004] | 0.0733 | 0 | 4 | 23/30 | +0.367 | 0.0127 |
| 1.5 | 0.700 | 0.167 | 0.267 | 0.700 | 0.367 | 0.000 | **+0.200** | **-0.433** | [-0.700,-0.133] | 0.0133 | **-0.325** | [-0.579,-0.058] | 0.0225 | 1 | 2 | 23/30 | +0.433 | 0.0010 |
| 2.0 | 0.667 | 0.233 | 0.167 | 0.767 | 0.500 | 0.000 | **+0.233** | **-0.267** | [-0.600,+0.067] | 0.1704 | **-0.212** | [-0.458,+0.042] | 0.1151 | 1 | 3 | 21/30 | +0.500 | 0.0003 |

‡ = |dASR| below the ~2 pp judge noise floor, i.e. not distinguishable from judge nondeterminism.
Shared baselines (alpha-independent): direct_base ASR = 0.300, ds_base ASR = 0.400.

Full binary D_i distribution per alpha:
  - alpha=0.0: {'-2': 0, '-1': 2, '0': 27, '1': 1, '2': 0}  (score D: {'neg': 4, 'zero': 22, 'pos': 4})
  - alpha=0.25: {'-2': 0, '-1': 10, '0': 18, '1': 2, '2': 0}  (score D: {'neg': 14, 'zero': 13, 'pos': 3})
  - alpha=0.5: {'-2': 1, '-1': 11, '0': 16, '1': 2, '2': 0}  (score D: {'neg': 16, 'zero': 9, 'pos': 5})
  - alpha=0.75: {'-2': 1, '-1': 11, '0': 16, '1': 2, '2': 0}  (score D: {'neg': 16, 'zero': 7, 'pos': 7})
  - alpha=1.0: {'-2': 4, '-1': 7, '0': 15, '1': 4, '2': 0}  (score D: {'neg': 14, 'zero': 10, 'pos': 6})
  - alpha=1.5: {'-2': 2, '-1': 12, '0': 14, '1': 1, '2': 1}  (score D: {'neg': 16, 'zero': 7, 'pos': 7})
  - alpha=2.0: {'-2': 3, '-1': 7, '0': 16, '1': 3, '2': 1}  (score D: {'neg': 14, 'zero': 8, 'pos': 8})

**Ihat tracks the ceiling across the 7-point alpha grid: Spearman(I_max, Ihat_binary) = +0.746 (Pearson +0.933); Spearman(I_max, Ihat_score) = +0.667 (Pearson +0.934). Ihat is most negative exactly where the design has least headroom — a ceiling signature, not a mechanism.**

#### curated / test (n=21)

| alpha | ASR d+refabl | refusal d+refabl | ASR d+randabl | refusal d+randabl | ASR ds+refabl | refusal ds+refabl | **I_max** | **Ihat bin** | CI95 bin | p bin | **Ihat score** | CI95 score | p score | D=+2 | D=-2 | sat. by 1 factor | dASR ref-rand | McNemar p |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0.0 | 0.333 | 0.667 | 0.333 | 0.667 | 0.095 | 0.000 | **+0.905** | **+0.000** | [+0.000,+0.000] | 1.0000 | **-0.006** | [-0.018,+0.000] | 1.0000 | 0 | 0 | 8/21 | +0.000 ‡ | 1.0000 |
| 0.25 | 0.476 | 0.524 | 0.381 | 0.619 | 0.190 | 0.000 | **+0.762** | **-0.048** | [-0.286,+0.190] | 1.0000 | **-0.095** | [-0.280,+0.071] | 0.3481 | 0 | 0 | 11/21 | +0.095 | 0.5000 |
| 0.5 | 0.476 | 0.429 | 0.381 | 0.619 | 0.238 | 0.000 | **+0.762** | **+0.000** | [-0.286,+0.286] | 1.0000 | **+0.036** | [-0.202,+0.298] | 0.8198 | 1 | 0 | 11/21 | +0.095 | 0.6250 |
| 0.75 | 0.571 | 0.286 | 0.381 | 0.619 | 0.143 | 0.000 | **+0.667** | **-0.190** | [-0.524,+0.095] | 0.4001 | **-0.137** | [-0.393,+0.101] | 0.3277 | 0 | 1 | 13/21 | +0.190 | 0.2188 |
| 1.0 | 0.714 | 0.286 | 0.333 | 0.619 | 0.190 | 0.000 | **+0.524** | **-0.286** | [-0.619,+0.048] | 0.2114 | **-0.232** | [-0.518,+0.048] | 0.1340 | 0 | 1 | 15/21 | +0.381 | 0.0078 |
| 1.5 | 0.667 | 0.286 | 0.381 | 0.619 | 0.190 | 0.000 | **+0.571** | **-0.238** | [-0.571,+0.095] | 0.2707 | **-0.196** | [-0.476,+0.083] | 0.2026 | 0 | 1 | 15/21 | +0.286 | 0.0703 |
| 2.0 | 0.571 | 0.333 | 0.333 | 0.667 | 0.238 | 0.000 | **+0.667** | **-0.095** | [-0.476,+0.286] | 0.8094 | **-0.048** | [-0.351,+0.244] | 0.7904 | 1 | 1 | 12/21 | +0.238 | 0.1250 |

‡ = |dASR| below the ~2 pp judge noise floor, i.e. not distinguishable from judge nondeterminism.
Shared baselines (alpha-independent): direct_base ASR = 0.333, ds_base ASR = 0.095.

Full binary D_i distribution per alpha:
  - alpha=0.0: {'-2': 0, '-1': 0, '0': 21, '1': 0, '2': 0}  (score D: {'neg': 1, 'zero': 20, 'pos': 0})
  - alpha=0.25: {'-2': 0, '-1': 4, '0': 14, '1': 3, '2': 0}  (score D: {'neg': 5, 'zero': 10, 'pos': 6})
  - alpha=0.5: {'-2': 0, '-1': 4, '0': 14, '1': 2, '2': 1}  (score D: {'neg': 6, 'zero': 8, 'pos': 7})
  - alpha=0.75: {'-2': 1, '-1': 5, '0': 12, '1': 3, '2': 0}  (score D: {'neg': 6, 'zero': 9, 'pos': 6})
  - alpha=1.0: {'-2': 1, '-1': 8, '0': 8, '1': 4, '2': 0}  (score D: {'neg': 9, 'zero': 4, 'pos': 8})
  - alpha=1.5: {'-2': 1, '-1': 6, '0': 11, '1': 3, '2': 0}  (score D: {'neg': 8, 'zero': 7, 'pos': 6})
  - alpha=2.0: {'-2': 1, '-1': 5, '0': 11, '1': 3, '2': 1}  (score D: {'neg': 7, 'zero': 6, 'pos': 8})

**Ihat tracks the ceiling across the 7-point alpha grid: Spearman(I_max, Ihat_binary) = +0.963 (Pearson +0.918); Spearman(I_max, Ihat_score) = +0.855 (Pearson +0.834). Ihat is most negative exactly where the design has least headroom — a ceiling signature, not a mechanism.**

#### curated / pooled (n=51)

| alpha | ASR d+refabl | refusal d+refabl | ASR d+randabl | refusal d+randabl | ASR ds+refabl | refusal ds+refabl | **I_max** | **Ihat bin** | CI95 bin | p bin | **Ihat score** | CI95 score | p score | D=+2 | D=-2 | sat. by 1 factor | dASR ref-rand | McNemar p |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0.0 | 0.294 | 0.686 | 0.314 | 0.686 | 0.235 | 0.000 | **+0.745** | **-0.020** | [-0.078,+0.039] | 1.0000 | **-0.010** | [-0.064,+0.042] | 0.8010 | 0 | 0 | 23/51 | -0.020 ‡ | 1.0000 |
| 0.25 | 0.529 | 0.431 | 0.294 | 0.667 | 0.314 | 0.000 | **+0.510** | **-0.176** | [-0.333,-0.020] | 0.0648 | **-0.150** | [-0.272,-0.032] | 0.0212 | 0 | 0 | 33/51 | +0.235 | 0.0042 |
| 0.5 | 0.588 | 0.333 | 0.333 | 0.667 | 0.333 | 0.000 | **+0.451** | **-0.216** | [-0.412,-0.020] | 0.0517 | **-0.164** | [-0.328,+0.002] | 0.0665 | 1 | 1 | 34/51 | +0.255 | 0.0010 |
| 0.75 | 0.667 | 0.235 | 0.314 | 0.667 | 0.333 | 0.000 | **+0.373** | **-0.294** | [-0.490,-0.118] | 0.0067 | **-0.211** | [-0.360,-0.064] | 0.0087 | 0 | 2 | 37/51 | +0.353 | 0.0000 |
| 1.0 | 0.667 | 0.255 | 0.294 | 0.667 | 0.294 | 0.000 | **+0.373** | **-0.333** | [-0.569,-0.098] | 0.0123 | **-0.252** | [-0.449,-0.059] | 0.0166 | 0 | 5 | 38/51 | +0.373 | 0.0002 |
| 1.5 | 0.686 | 0.216 | 0.314 | 0.667 | 0.294 | 0.000 | **+0.353** | **-0.353** | [-0.569,-0.137] | 0.0042 | **-0.272** | [-0.456,-0.081] | 0.0085 | 1 | 3 | 38/51 | +0.373 | 0.0001 |
| 2.0 | 0.627 | 0.275 | 0.235 | 0.725 | 0.392 | 0.000 | **+0.412** | **-0.196** | [-0.431,+0.039] | 0.1666 | **-0.145** | [-0.336,+0.047] | 0.1558 | 2 | 4 | 33/51 | +0.392 | 0.0000 |

‡ = |dASR| below the ~2 pp judge noise floor, i.e. not distinguishable from judge nondeterminism.
Shared baselines (alpha-independent): direct_base ASR = 0.314, ds_base ASR = 0.275.

Full binary D_i distribution per alpha:
  - alpha=0.0: {'-2': 0, '-1': 2, '0': 48, '1': 1, '2': 0}  (score D: {'neg': 5, 'zero': 42, 'pos': 4})
  - alpha=0.25: {'-2': 0, '-1': 14, '0': 32, '1': 5, '2': 0}  (score D: {'neg': 19, 'zero': 23, 'pos': 9})
  - alpha=0.5: {'-2': 1, '-1': 15, '0': 30, '1': 4, '2': 1}  (score D: {'neg': 22, 'zero': 17, 'pos': 12})
  - alpha=0.75: {'-2': 2, '-1': 16, '0': 28, '1': 5, '2': 0}  (score D: {'neg': 22, 'zero': 16, 'pos': 13})
  - alpha=1.0: {'-2': 5, '-1': 15, '0': 23, '1': 8, '2': 0}  (score D: {'neg': 23, 'zero': 14, 'pos': 14})
  - alpha=1.5: {'-2': 3, '-1': 18, '0': 25, '1': 4, '2': 1}  (score D: {'neg': 24, 'zero': 14, 'pos': 13})
  - alpha=2.0: {'-2': 4, '-1': 12, '0': 27, '1': 6, '2': 2}  (score D: {'neg': 21, 'zero': 14, 'pos': 16})

**Ihat tracks the ceiling across the 7-point alpha grid: Spearman(I_max, Ihat_binary) = +0.955 (Pearson +0.943); Spearman(I_max, Ihat_score) = +0.883 (Pearson +0.935). Ihat is most negative exactly where the design has least headroom — a ceiling signature, not a mechanism.**

#### Operating point — curated (rule: ASR(direct_refabl) in [0.20,0.40] AND I_max >= +0.33, larger I_max wins ties; selection split = pooled)

| alpha | ASR direct_refabl | in band | I_max | ceiling ok | no-op | qualifies |
|---|---|---|---|---|---|---|
| 0.0 | 0.294 | yes | +0.745 | yes | YES | no |
| 0.25 | 0.529 | no | +0.510 | yes | - | no |
| 0.5 | 0.588 | no | +0.451 | yes | - | no |
| 0.75 | 0.667 | no | +0.373 | yes | - | no |
| 1.0 | 0.667 | no | +0.373 | yes | - | no |
| 1.5 | 0.686 | no | +0.353 | yes | - | no |
| 2.0 | 0.627 | no | +0.412 | yes | - | no |

**NO alpha qualifies on curated.** No dose satisfies both criteria simultaneously (excluding the alpha=0 no-op).

---

### clearharm — PROVISIONAL  (n=78)
run_dir: `behav_refusal_clearharm_asweep0.0-0.25-0.5-0.75-1.0-1.5-2.0_20260805_171237_716014`
> **PROVISIONAL — summary.json absent, the run is still writing `raw.jsonl`. 78 complete rows read. Do not cite.**

**Judge noise floor (measured on THIS cohort, alpha=0 no-op, byte-identical generations): 1/78 labels flipped (1.3%), 5/78 scores changed (6.4%), max |dscore| = 1.00, dASR = +0.0128. Any |dASR| below ~2 pp is indistinguishable from judge nondeterminism.**

#### clearharm / train (n=44)

| alpha | ASR d+refabl | refusal d+refabl | ASR d+randabl | refusal d+randabl | ASR ds+refabl | refusal ds+refabl | **I_max** | **Ihat bin** | CI95 bin | p bin | **Ihat score** | CI95 score | p score | D=+2 | D=-2 | sat. by 1 factor | dASR ref-rand | McNemar p |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0.0 | 0.136 | 0.841 | 0.159 | 0.841 | 0.364 | 0.477 | **+0.659** | **+0.023** | [+0.000,+0.068] | 1.0000 | **+0.020** | [-0.017,+0.071] | 0.5948 | 0 | 0 | 17/44 | -0.023 | 1.0000 |
| 0.25 | 0.341 | 0.636 | 0.136 | 0.864 | 0.523 | 0.250 | **+0.455** | **-0.023** | [-0.205,+0.136] | 1.0000 | **-0.054** | [-0.199,+0.091] | 0.5014 | 0 | 0 | 22/44 | +0.205 | 0.0039 |
| 0.5 | 0.545 | 0.364 | 0.091 | 0.864 | 0.636 | 0.091 | **+0.250** | **-0.114** | [-0.341,+0.114] | 0.4441 | **-0.122** | [-0.330,+0.080] | 0.2649 | 0 | 2 | 28/44 | +0.455 | 0.0000 |
| 0.75 | 0.568 | 0.227 | 0.136 | 0.864 | 0.682 | 0.045 | **+0.227** | **-0.091** | [-0.364,+0.159] | 0.6107 | **-0.060** | [-0.284,+0.162] | 0.6199 | 0 | 3 | 28/44 | +0.432 | 0.0001 |
| 1.0 | 0.614 | 0.273 | 0.114 | 0.864 | 0.682 | 0.045 | **+0.182** | **-0.136** | [-0.364,+0.091] | 0.3481 | **-0.148** | [-0.341,+0.045] | 0.1518 | 0 | 1 | 30/44 | +0.500 | 0.0000 |
| 1.5 | 0.705 | 0.182 | 0.114 | 0.864 | 0.795 | 0.023 | **+0.091** | **-0.114** | [-0.318,+0.091] | 0.4086 | **-0.125** | [-0.290,+0.037] | 0.1520 | 0 | 1 | 35/44 | +0.591 | 0.0000 |
| 2.0 | 0.841 | 0.091 | 0.114 | 0.864 | 0.727 | 0.023 | **-0.045** | **-0.318** | [-0.523,-0.091] | 0.0122 | **-0.375** | [-0.543,-0.199] | 0.0002 | 0 | 1 | 38/44 | +0.727 | 0.0000 |

‡ = |dASR| below the ~2 pp judge noise floor, i.e. not distinguishable from judge nondeterminism.
Shared baselines (alpha-independent): direct_base ASR = 0.136, ds_base ASR = 0.341.

Full binary D_i distribution per alpha:
  - alpha=0.0: {'-2': 0, '-1': 0, '0': 43, '1': 1, '2': 0}  (score D: {'neg': 3, 'zero': 38, 'pos': 3})
  - alpha=0.25: {'-2': 0, '-1': 8, '0': 29, '1': 7, '2': 0}  (score D: {'neg': 14, 'zero': 22, 'pos': 8})
  - alpha=0.5: {'-2': 2, '-1': 10, '0': 23, '1': 9, '2': 0}  (score D: {'neg': 18, 'zero': 13, 'pos': 13})
  - alpha=0.75: {'-2': 3, '-1': 10, '0': 19, '1': 12, '2': 0}  (score D: {'neg': 19, 'zero': 7, 'pos': 18})
  - alpha=1.0: {'-2': 1, '-1': 14, '0': 19, '1': 10, '2': 0}  (score D: {'neg': 22, 'zero': 10, 'pos': 12})
  - alpha=1.5: {'-2': 1, '-1': 11, '0': 24, '1': 8, '2': 0}  (score D: {'neg': 21, 'zero': 8, 'pos': 15})
  - alpha=2.0: {'-2': 1, '-1': 18, '0': 19, '1': 6, '2': 0}  (score D: {'neg': 29, 'zero': 6, 'pos': 9})

**Ihat tracks the ceiling across the 7-point alpha grid: Spearman(I_max, Ihat_binary) = +0.883 (Pearson +0.900); Spearman(I_max, Ihat_score) = +0.929 (Pearson +0.846). Ihat is most negative exactly where the design has least headroom — a ceiling signature, not a mechanism.**

#### clearharm / test (n=34)

| alpha | ASR d+refabl | refusal d+refabl | ASR d+randabl | refusal d+randabl | ASR ds+refabl | refusal ds+refabl | **I_max** | **Ihat bin** | CI95 bin | p bin | **Ihat score** | CI95 score | p score | D=+2 | D=-2 | sat. by 1 factor | dASR ref-rand | McNemar p |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0.0 | 0.118 | 0.853 | 0.088 | 0.853 | 0.324 | 0.441 | **+0.647** | **-0.029** | [-0.118,+0.059] | 1.0000 | **-0.026** | [-0.121,+0.066] | 0.7351 | 0 | 0 | 13/34 | +0.029 | 1.0000 |
| 0.25 | 0.235 | 0.706 | 0.088 | 0.853 | 0.471 | 0.324 | **+0.529** | **+0.000** | [-0.206,+0.206] | 1.0000 | **-0.004** | [-0.232,+0.210] | 1.0000 | 0 | 1 | 15/34 | +0.147 | 0.1250 |
| 0.5 | 0.441 | 0.441 | 0.088 | 0.853 | 0.588 | 0.118 | **+0.324** | **-0.088** | [-0.324,+0.147] | 0.6272 | **-0.099** | [-0.309,+0.110] | 0.3787 | 0 | 0 | 18/34 | +0.353 | 0.0005 |
| 0.75 | 0.529 | 0.324 | 0.118 | 0.824 | 0.588 | 0.118 | **+0.235** | **-0.176** | [-0.412,+0.059] | 0.2075 | **-0.158** | [-0.349,+0.026] | 0.1201 | 0 | 0 | 21/34 | +0.412 | 0.0001 |
| 1.0 | 0.471 | 0.294 | 0.088 | 0.853 | 0.529 | 0.118 | **+0.294** | **-0.176** | [-0.412,+0.029] | 0.2119 | **-0.132** | [-0.327,+0.055] | 0.1979 | 0 | 1 | 20/34 | +0.382 | 0.0002 |
| 1.5 | 0.559 | 0.353 | 0.118 | 0.853 | 0.471 | 0.118 | **+0.206** | **-0.324** | [-0.588,-0.059] | 0.0409 | **-0.298** | [-0.537,-0.070] | 0.0206 | 0 | 2 | 21/34 | +0.441 | 0.0001 |
| 2.0 | 0.588 | 0.206 | 0.059 | 0.882 | 0.618 | 0.029 | **+0.176** | **-0.206** | [-0.441,+0.029] | 0.1688 | **-0.232** | [-0.449,-0.029] | 0.0411 | 0 | 1 | 24/34 | +0.529 | 0.0000 |

‡ = |dASR| below the ~2 pp judge noise floor, i.e. not distinguishable from judge nondeterminism.
Shared baselines (alpha-independent): direct_base ASR = 0.088, ds_base ASR = 0.324.

Full binary D_i distribution per alpha:
  - alpha=0.0: {'-2': 0, '-1': 2, '0': 31, '1': 1, '2': 0}  (score D: {'neg': 5, 'zero': 27, 'pos': 2})
  - alpha=0.25: {'-2': 1, '-1': 4, '0': 23, '1': 6, '2': 0}  (score D: {'neg': 8, 'zero': 17, 'pos': 9})
  - alpha=0.5: {'-2': 0, '-1': 10, '0': 17, '1': 7, '2': 0}  (score D: {'neg': 14, 'zero': 12, 'pos': 8})
  - alpha=0.75: {'-2': 0, '-1': 11, '0': 18, '1': 5, '2': 0}  (score D: {'neg': 13, 'zero': 12, 'pos': 9})
  - alpha=1.0: {'-2': 1, '-1': 8, '0': 21, '1': 4, '2': 0}  (score D: {'neg': 12, 'zero': 15, 'pos': 7})
  - alpha=1.5: {'-2': 2, '-1': 12, '0': 15, '1': 5, '2': 0}  (score D: {'neg': 17, 'zero': 10, 'pos': 7})
  - alpha=2.0: {'-2': 1, '-1': 10, '0': 18, '1': 5, '2': 0}  (score D: {'neg': 17, 'zero': 9, 'pos': 8})

**Ihat tracks the ceiling across the 7-point alpha grid: Spearman(I_max, Ihat_binary) = +0.919 (Pearson +0.846); Spearman(I_max, Ihat_score) = +0.929 (Pearson +0.872). Ihat is most negative exactly where the design has least headroom — a ceiling signature, not a mechanism.**

#### clearharm / pooled (n=78)

| alpha | ASR d+refabl | refusal d+refabl | ASR d+randabl | refusal d+randabl | ASR ds+refabl | refusal ds+refabl | **I_max** | **Ihat bin** | CI95 bin | p bin | **Ihat score** | CI95 score | p score | D=+2 | D=-2 | sat. by 1 factor | dASR ref-rand | McNemar p |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0.0 | 0.128 | 0.846 | 0.128 | 0.846 | 0.346 | 0.462 | **+0.654** | **+0.000** | [-0.051,+0.051] | 1.0000 | **+0.000** | [-0.048,+0.048] | 1.0000 | 0 | 0 | 30/78 | +0.000 ‡ | 1.0000 |
| 0.25 | 0.295 | 0.667 | 0.115 | 0.859 | 0.500 | 0.282 | **+0.487** | **-0.013** | [-0.141,+0.128] | 1.0000 | **-0.032** | [-0.159,+0.095] | 0.6402 | 0 | 1 | 37/78 | +0.179 | 0.0005 |
| 0.5 | 0.500 | 0.397 | 0.090 | 0.859 | 0.615 | 0.103 | **+0.282** | **-0.103** | [-0.269,+0.064] | 0.2912 | **-0.112** | [-0.256,+0.034] | 0.1457 | 0 | 2 | 46/78 | +0.410 | 0.0000 |
| 0.75 | 0.551 | 0.269 | 0.128 | 0.846 | 0.641 | 0.077 | **+0.231** | **-0.128** | [-0.308,+0.038] | 0.2040 | **-0.103** | [-0.248,+0.045] | 0.1920 | 0 | 3 | 49/78 | +0.423 | 0.0000 |
| 1.0 | 0.551 | 0.282 | 0.103 | 0.859 | 0.615 | 0.077 | **+0.231** | **-0.154** | [-0.321,+0.013] | 0.0954 | **-0.141** | [-0.274,-0.003] | 0.0503 | 0 | 2 | 50/78 | +0.449 | 0.0000 |
| 1.5 | 0.641 | 0.256 | 0.115 | 0.859 | 0.654 | 0.064 | **+0.141** | **-0.205** | [-0.372,-0.038] | 0.0288 | **-0.200** | [-0.340,-0.061] | 0.0065 | 0 | 3 | 56/78 | +0.526 | 0.0000 |
| 2.0 | 0.731 | 0.141 | 0.090 | 0.872 | 0.679 | 0.026 | **+0.051** | **-0.269** | [-0.423,-0.103] | 0.0028 | **-0.312** | [-0.444,-0.178] | 0.0000 | 0 | 2 | 62/78 | +0.641 | 0.0000 |

‡ = |dASR| below the ~2 pp judge noise floor, i.e. not distinguishable from judge nondeterminism.
Shared baselines (alpha-independent): direct_base ASR = 0.115, ds_base ASR = 0.333.

Full binary D_i distribution per alpha:
  - alpha=0.0: {'-2': 0, '-1': 2, '0': 74, '1': 2, '2': 0}  (score D: {'neg': 8, 'zero': 65, 'pos': 5})
  - alpha=0.25: {'-2': 1, '-1': 12, '0': 52, '1': 13, '2': 0}  (score D: {'neg': 22, 'zero': 39, 'pos': 17})
  - alpha=0.5: {'-2': 2, '-1': 20, '0': 40, '1': 16, '2': 0}  (score D: {'neg': 32, 'zero': 25, 'pos': 21})
  - alpha=0.75: {'-2': 3, '-1': 21, '0': 37, '1': 17, '2': 0}  (score D: {'neg': 32, 'zero': 19, 'pos': 27})
  - alpha=1.0: {'-2': 2, '-1': 22, '0': 40, '1': 14, '2': 0}  (score D: {'neg': 34, 'zero': 25, 'pos': 19})
  - alpha=1.5: {'-2': 3, '-1': 23, '0': 39, '1': 13, '2': 0}  (score D: {'neg': 38, 'zero': 18, 'pos': 22})
  - alpha=2.0: {'-2': 2, '-1': 28, '0': 37, '1': 11, '2': 0}  (score D: {'neg': 46, 'zero': 15, 'pos': 17})

**Ihat tracks the ceiling across the 7-point alpha grid: Spearman(I_max, Ihat_binary) = +0.991 (Pearson +0.957); Spearman(I_max, Ihat_score) = +0.937 (Pearson +0.918). Ihat is most negative exactly where the design has least headroom — a ceiling signature, not a mechanism.**

#### Operating point — clearharm (rule: ASR(direct_refabl) in [0.20,0.40] AND I_max >= +0.33, larger I_max wins ties; selection split = pooled)

| alpha | ASR direct_refabl | in band | I_max | ceiling ok | no-op | qualifies |
|---|---|---|---|---|---|---|
| 0.0 | 0.128 | no | +0.654 | yes | YES | no |
| 0.25 | 0.295 | yes | +0.487 | yes | - | **YES** |
| 0.5 | 0.500 | no | +0.282 | no | - | no |
| 0.75 | 0.551 | no | +0.231 | no | - | no |
| 1.0 | 0.551 | no | +0.231 | no | - | no |
| 1.5 | 0.641 | no | +0.141 | no | - | no |
| 2.0 | 0.731 | no | +0.051 | no | - | no |

**Selected operating point: alpha = 0.25** (ASR(direct_refabl) = 0.295, I_max = +0.487; sole qualifying alpha)
---

## Decision and what carries into P8

| question | answer |
|---|---|
| Selection rule | `ASR(direct_refabl_a<α>)` ∈ [0.20, 0.40] **and** `I_max` ≥ +0.33; larger `I_max` breaks ties |
| α = 0 treated how? | **Excluded from candidacy.** It is an exact numerical no-op (byte-identical generations), so it can satisfy the arithmetic while applying no intervention. Reported and flagged, never selected. |
| Selection split | pooled by default; `--selection-split train` reproduces the same answer on both cohorts |
| **curated** | **no α qualifies.** Needs its own finer grid near α ≈ 0.1 if this cohort is to be used at all — and it should probably not be, since its DS arm is net-negative by ASR |
| **clearharm** | **α = 0.25** (PROVISIONAL, n = 78/86) — sole qualifying dose, unanimous across train/test/pooled |
| Does clearharm's α transfer to curated? | **No.** At α = 0.25 curated's `ASR(0,1)` is 0.529, far outside the band. A curated arm of Phase 8 would need separate calibration. |

**Consequences for the Phase 8 factorial.**

1. Run the primary interaction estimate on **clearharm at α = 0.25**, and re-confirm the choice once the
   sweep completes — 8 of 86 items are still missing and the α = 0.25 `I_max` has already moved from
   +0.472 (n = 36) to +0.481 (n = 77) to +0.487 (n = 78) as rows landed.
2. Do **not** run a curated arm at a borrowed α. Either calibrate curated separately on a finer low-α grid,
   or drop it from the interaction test and keep it as a secondary cohort.
3. `I_max` = +0.487 is the *arithmetic* ceiling, not the achievable effect. Plan §P8.5 puts a properly
   powered interaction test at n = 324 for I = 0.15; at n = 86 clearharm is under-powered for anything
   smaller, and the confidence intervals in the tables above make that concrete — at α = 0.25 the binary
   CI is roughly ±0.13 wide on each side of zero.
4. Report ASR **and** compliance as separate outcomes in P8 (plan §P8.3). Note the `ds_base` refusal rates
   in the tables: 0.000 on curated but **0.462** on clearharm — Doublespeak alone still leaves nearly half
   of clearharm items refused, which is where the ablation has room to act and part of why clearharm is the
   better interaction cohort.

## What this report does not claim

- It does not claim the interaction is zero. At the only doses where the design has headroom, `Î` is
  **below the judge noise floor** — undetectable, which is not the same as absent.
- It does not claim the ceiling explains all of the P8.0 sub-additivity. It shows `Î` and `I_max` move
  together (ρ = +0.955 / +0.991, including through a reversal), which makes the ceiling a sufficient
  explanation of the pattern, and shifts the burden onto any mechanistic reading. Settling it needs the
  completed clearharm sweep at the sub-saturating dose, at n large enough to matter.
- It does not use the headroom-vs-saturated decomposition, for the reason given above.
- clearharm numbers are **PROVISIONAL** until `summary.json` exists in that run dir.

## Verification log

Everything below was run, not asserted.

1. **Completeness.** curated: 51 rows in `raw.jsonl`, 51 usable, 0 dropped, 0 truncated lines,
   `summary.json` present ⇒ labelled FINAL. clearharm: 78 rows read live, 78 usable, 0 dropped,
   no `summary.json` ⇒ labelled **PROVISIONAL** with a "do not cite" banner on the output.
2. **Partial-file robustness.** A synthetic run dir was built from the first 40 curated rows plus a
   deliberately truncated 41st record. The analyzer reported
   `PROVISIONAL — ... 40 complete rows read, 1 truncated line(s) skipped` and produced a full table
   rather than crashing.
3. **Cross-check against an independent code path.** Every per-arm `ASR` and `refusal_rate` the analyzer
   produces for curated train and test — **140 cell values across all 7 α and all 5 arms** — was compared
   against the corresponding entries in the run's own `summary.json`, which is written by
   `scripts/phase_behav_refusal.py` and shares no code with this analyzer. **0 mismatches** (tolerance
   5e-4, the rounding in `summary.json`).
4. **Independent from-scratch recount.** Six cells were recounted with a hand-written loop using no numpy
   and none of the analyzer's helpers:

   | cohort | split | arm | n | MALICIOUS | ASR (recount) | ASR (table) |
   |---|---|---|---|---|---|---|
   | curated | pooled | `direct_refabl_a0.25` | 51 | 27 | 0.5294 | 0.529 ✓ |
   | curated | pooled | `ds_refabl_a1.0` | 51 | 15 | 0.2941 | 0.294 ✓ |
   | curated | train | `direct_randabl_a2.0` | 30 | 5 | 0.1667 | 0.167 ✓ |
   | clearharm | pooled | `direct_refabl_a0.25` | 77 | 23 | 0.2987 | 0.299 ✓ (n=77 snapshot) |
   | clearharm | pooled | `ds_base` | 77 | 25 | 0.3247 | 0.325 ✓ (n=77 snapshot) |
   | clearharm | test | `direct_refabl_a2.0` | 33 | 20 | 0.6061 | 0.606 ✓ (n=77 snapshot) |

5. **`I_max` by hand.** curated pooled α = 1.0: `1 − 0.2745 − 0.6667 + 0.3137 = 0.3725`, matching the
   table's +0.373.
6. **`Î` by hand.** curated pooled from the raw labels: α = 0.25 → −0.1765 and α = 1.0 → −0.3333, matching
   the table's −0.176 and −0.333.
7. **McNemar against `scipy`.** The hand-rolled exact binomial McNemar was checked against
   `scipy.stats.binomtest(min(b,c), b+c, 0.5, alternative="two-sided")`: curated α = 0.25 (b=14, c=2)
   → 0.004181 vs 0.004181; α = 1.0 (b=22, c=3) → 0.000157 vs 0.000157. Exact agreement to 1e-12. (`scipy`
   is used only for this check; the analyzer itself depends on nothing beyond numpy.)
8. **Spearman against `scipy`.** The numpy rank correlation matches `scipy.stats.spearmanr` on the pooled
   grids: curated +0.955, clearharm +0.991.
9. **Continuity with the earlier partial reads.** The curated table reproduces the tick-16 numbers exactly
   (α = 0.25: ASR 0.529, `I_max` +0.510, `Î` −0.176; α = 1.0: 0.667 / +0.373 / −0.333; α = 2.0: 0.627 /
   +0.412 / −0.196), confirming the rebind-`CELLS` reuse of `analyze_interaction_2x2.py` computes the same
   estimator as P8.0.

**Safety.** No generation text was read, printed or quoted at any point; the analyzer touches only the
`*_label`, `*_score`, `*_refused`, `id`, `split` and `cohort` fields of `raw.jsonl`, and `gens.jsonl` is
never opened.
