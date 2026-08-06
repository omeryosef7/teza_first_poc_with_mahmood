# P8 — Do Doublespeak and refusal-ablation interact? No. And the apparent "yes" is a ceiling artifact.

**Status: ✅ COMPLETE** — both v3 cohorts finished (jobs `721956` clearharm n=127, `720725` generated
n=115; combined **n = 242**), run at the de-saturated dose **α = 0.25** selected by P8.1.

**Verdict: no interaction. `Î` = −0.054, 95 % CI [−0.124, +0.017], p = 0.172 at n = 242.**
**And the single most important finding here is a negative one about our own method:** the *train* split
alone shows a significant sub-additive interaction (p = 0.0098) that the **held-out test split reverses**
— which is exactly the error P8.0 made, now caught by the pre-registered split.

---

## 1. Design

Within-item 2×2. A = Doublespeak, B = refusal-direction ablation at α = 0.25.

`D_i = Y_i(1,1) − Y_i(1,0) − Y_i(0,1) + Y_i(0,0)`, `Î = mean(D_i)`, with a 10 000-resample paired
percentile bootstrap and a 50 000-flip sign-flip permutation. `I_max = 1 − ASR(1,0) − ASR(0,1) + ASR(0,0)`
is the arithmetic ceiling — the largest `Î` the design can express.

Pre-registration (plan §6, clause 3): **two-sided, no directional prediction.** After P8.0's withdrawal we
are explicitly *not* predicting sub-additivity.

## 2. The headline — combined v3, n = 242

| split | n | `I_max` | **`Î` (binary)** | 95 % CI | perm p | `Î` (graded) | p |
|---|---|---|---|---|---|---|---|
| train | 162 | +0.463 | **−0.124** | [−0.210, **−0.037**] | **0.0098** | −0.100 | 0.0140 |
| **test (held out)** | 80 | +0.588 | **+0.088** | [−0.025, +0.212] | 0.214 | +0.078 | 0.165 |
| **pooled** | **242** | +0.504 | **−0.054** | [−0.124, +0.017] | **0.172** | −0.041 | 0.214 |

Pooled cells: `(0,0)` = 0.306, `(1,0)` = 0.310, `(0,1)` = 0.492, `(1,1)` = 0.442.
`D_i` = {−2: 2, −1: 38, **0: 174**, +1: 27, +2: 1}.

**Read the test row.** Under the pre-registration the held-out split is the confirmatory one, and it does
not merely fail to reach significance — **it reverses sign.** Pooled, the CI includes zero. There is no
interaction.

## 3. ⚠️ The near-miss, stated plainly

Had we looked only at the train split — n = 162, `Î` = −0.124, CI excluding zero, **p = 0.0098** — we would
have reported *"Doublespeak and refusal-ablation combine sub-additively, consistent with a shared refusal
bottleneck."* That is verbatim the claim P8.0 made and that P8.1 withdrew. **The pre-registered split is
the only thing standing between this project and making the same error twice**, and it is worth saying so
in the paper rather than quietly reporting the pooled null.

## 4. Why train and test disagree: the ceiling, again

This is not unexplained noise. **The split with the lower ceiling has the more negative `Î`, in every
cohort:**

| dataset | split | `I_max` | saturated by one factor | `Î` |
|---|---|---|---|---|
| clearharm v3 | train | +0.447 | 57.6 % | **−0.118** |
| clearharm v3 | test | +0.619 | 50.0 % | **+0.095** |
| generated v3 | train | +0.481 | 72.7 % | **−0.130** |
| generated v3 | test | +0.553 | 65.8 % | **+0.079** |

Across the **4 independent cells** (2 cohorts × 2 splits) the **train/test separation is perfect** — both
train cells have the lower ceiling *and* a negative `Î`; both test cells have the higher ceiling *and* a
positive `Î`. Spearman(`I_max`, `Î`) = **+0.800** rather than +1.000 only because the two *train* cells
swap rank between themselves.

This is **P8.1's saturation signature reappearing along a third, independent axis.** `Î` was already shown
to track `I_max` across the α grid (Spearman +0.991, n=86) and across cohorts; it now does so across the
pre-registered split. `I_max` is a function of the **marginal** cells only — it carries no information
about the joint cell — so a real mechanism has no reason to track it. **The apparent sub-additivity is a
property of how much headroom the design has left, not of the model.**

## 5. The null has teeth — the manipulation demonstrably works

A null is only interesting if the intervention did something. It did:

| cohort | ΔASR (refusal-ablation − random-ablation) | McNemar b/c | p |
|---|---|---|---|
| clearharm v3 | **+0.244** | 32 / 1 | 7.9 × 10⁻⁹ |
| generated v3 | **+0.139** | 16 / 0 | 3.1 × 10⁻⁵ |
| **combined** | **+0.194** | 48 / 1 | < 10⁻¹² |

Ablating the refusal direction beats its own **count-matched random direction** by 19.4 pp — an order of
magnitude above the ~2 pp judge noise floor. So Doublespeak and refusal-ablation each move behaviour; they
simply **add** rather than interact.

## 6. Cohort differences that matter for "can we stack interventions to raise ASR?"

The two cohorts answer this **oppositely**, which is itself the finding:

| | direct (0,0) | DS alone (1,0) | refusal-abl alone (0,1) | both (1,1) |
|---|---|---|---|---|
| clearharm v3 | 0.173 | **0.268** (+9.5 pp) | 0.402 | **0.449** (best) |
| generated v3 | 0.452 | **0.357** (−9.6 pp) | **0.591** (best) | 0.435 (−15.6 pp) |

- On **clearharm**, Doublespeak is net-positive and stacking helps a little: `(1,1)` = 0.449 is the best
  cell, +4.7 pp over refusal-ablation alone.
- On **generated**, Doublespeak is **net-negative** (concept dilution) and stacking actively **hurts**:
  refusal-ablation *alone* (0.591) beats the combination (0.435) by **15.6 pp**.

**Conclusion for the attack-strength question: "refusal-direction down + Doublespeak" does not reliably
stack.** Its sign depends on whether Doublespeak helps on that cohort at all, and the interaction term is
zero either way — so the combination buys you the *sum* of two effects at best, never a synergy, and on a
cohort where Doublespeak dilutes the concept it buys you less than the single best lever.

## 7. Honest limitations

- **α = 0.25 qualifies on neither v3 cohort.** The pre-registered operating rule is
  `ASR(0,1) ∈ [0.20, 0.40]` **and** `I_max ≥ +0.33`. clearharm lands at `ASR(0,1)` = **0.402** (outside by
  0.002 — a hair, but outside) and generated at **0.591** (badly outside). The dose was calibrated on
  clearharm **v1** and does not transfer. `I_max` ≈ +0.50 on both, so the interaction estimate is *not*
  ceiling-limited and remains readable — but **these ASR levels must not be quoted as a chosen operating
  point**, and a v3-native low-α calibration is the clean follow-up.
- **62 % of items are already saturated by one factor alone** (`sat_by_one` = 0.624 pooled). That is what
  compresses `I_max` and, per §4, drives the residual negative drift on train.
- The pooled null is at n = 242 with CI half-width ≈ 0.07, so **effects smaller than ~7 pp remain
  undetectable**. This is "no interaction at this resolution", not "exactly zero".
- The judge contributes ~2 pp of irreducible label-flip noise on byte-identical text.
- The two cohorts are **not** exchangeable (§6 shows opposite Doublespeak signs), so the pooled row is
  reported alongside — never instead of — the per-cohort rows.

## 8. Reproduce

```
sbatch --time=03:00:00 --nodelist=n-801,n-802,n-804,n-805,t-806 \
  --export=ALL,DSBENCH=doublespeak_causality/data/behavioral_v3/beh_clearharm.json,DSALPHAS=0.25,DSMAXNEW=220,DSN=0 \
  doublespeak_causality/slurm/run_behav_refusal.sh     # and beh_generated.json for the other cohort

python scripts/analyze_alpha_calibration.py \
  --run clearharm_v3=outputs/behav_refusal_clearharm_asweep0.25_20260806_051610_721956 \
  --out outputs/p8_clearharm_v3.json
```
Combined: concatenate the two `raw.jsonl` (ids are disjoint — verified 242 rows / 242 distinct ids) and
run the same analyzer. Outputs: `outputs/p8_clearharm_v3.json`, `outputs/p8_generated_v3.json`,
`outputs/p8_v3_combined.json`.

`analyze_interaction_2x2.py` has its run dirs hardcoded and no `--run` flag;
`analyze_alpha_calibration.py` is the correct analyzer for α-suffixed arm names (it rebinds the 2×2 cells
and imports the estimator from `analyze_interaction_2x2` rather than reimplementing it).
