# §6 — Demonstration-Count Dose Response (n_demo ∈ {0,1,2,4,6,8,10,12})

**Status:** ✅ DONE. **Refusal suppression is a near-STEP function, not a graded dose response: essentially all
of the refusal-axis drop is bought by the FIRST demonstration (n=0→1), and adding demos 2→12 barely moves it.**
The concept readout (p_concept) is **flat across demo count**, and ASR is only weakly/noisily related to demo
count. So "more demonstrations" is not a graded lever on either representation — the mechanism turns on at the
first demo and saturates.

**Run:** `dose_response_clearharm_20260808_124748_735299` (v3 clearharm, `scripts/phase6_dose_response.py`).
Per item, nested paired demo subsets at n_demo ∈ {0,1,2,4,6,8,10,12}; measured simultaneously: forced-choice
p_concept (gated per-item on a positive control), decision-token refusal-direction projection (validated anchor
L18, also L16), and StrongREJECT ASR. Reuses `build_conditions` + the validated refusal directions + behav_judge.

## Result — mean curves (train n=85 / test n=42)
| endpoint | n=0 | n=1 | n=4 | n=12 | shape |
|---|---|---|---|---|---|
| **refusal proj @L18** (train) | 4.02 | **2.98** | 3.13 | 3.24 | step down at n=1, then flat |
| **refusal proj @L18** (test) | 4.46 | **3.47** | — | 3.84 | step down at n=1, then flat |
| **p_concept** (train) | 0.360 | 0.363 | 0.361 | 0.357 | flat |
| **ASR** (train) | 0.306 | 0.294 | 0.247 | 0.298 | weak/noisy, no monotone trend |
| **ASR** (test) | 0.238 | — | 0.333 | 0.167 | noisy (n=42), no monotone trend |

Per-item slopes per added demo (median [CI]): refusal_anchor train **−0.032 [−0.058, −0.006]** (small negative,
CI excludes 0) but this is dominated by the n=0→1 step; p_concept slope ≈ **−0.001** (indistinguishable from 0);
ASR slope ≈ **−0.002 [−0.011, +0.009]** (null).

## Marginal within-item correlations (Δ per demo step)
| pair | train | test |
|---|---|---|
| dConcept vs dRefusal | −0.105 | +0.179 |
| dConcept vs dASR | −0.177 | +0.065 |
| **dRefusal vs dASR** | **−0.292** | −0.162 |

The only consistently signed coupling is **dRefusal vs dASR ≈ −0.29 (train) / −0.16 (test)**: within an item,
demo steps that suppress the refusal axis further tend to raise ASR — directionally consistent with the refusal-
suppression mechanism, but weak (|r|<0.3). Concept-change is uncorrelated (sign flips across splits).

## Interpretation
1. **Refusal suppression saturates at the first demonstration.** The 4.0→3.0 (train) / 4.5→3.5 (test) drop is
   entirely the n=0→1 transition; n=1…12 is flat within CI. Doublespeak does not need many demos to suppress
   refusal — one in-context example of the codeword→answer mapping is enough.
2. **The concept readout does not scale with demos** (p_concept flat at ~0.36) — consistent with the broader
   finding that the concept representation is not the graded behavioral lever (§10/§11).
3. **ASR has no monotone dose response** in demo count; the only signal is a weak within-item refusal↔ASR
   coupling. Demo count is therefore not a clean graded knob on behavior.

## Caveats
- The forced-choice p_concept curve is gated per item on a positive control; only 6/85 train items passed the
  control (20/42 test), so the p_concept curve is **descriptive/underpowered on train** — read the refusal-proj
  and ASR curves (n=85/42, no gating) as the load-bearing ones.
- One train item had only 6 demos available (curve truncated for that item; noted in `items_short_of_max`).

## Verdict
**Dose response is a step, not a ramp:** refusal suppression turns on at the first demonstration and saturates;
concept readout is demo-invariant; ASR shows only a weak within-item refusal-coupling. Consistent with the
refusal-suppression-not-concept-remap thesis and with the mechanism being switch-like rather than dose-graded.
