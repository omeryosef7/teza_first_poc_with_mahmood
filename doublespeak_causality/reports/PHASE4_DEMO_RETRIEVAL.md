# reports/PHASE4_DEMO_RETRIEVAL.md — Demonstration-Codeword K/V Necessity (Phase 4.2 core)

**Question:** are the DEMONSTRATION-codeword activations causally necessary for the hijacked reading?
Neutralize the demo-codeword resid_pre (K/V) by transplanting matched BENIGN demo activations, and
measure the reading with the DE_context forced-choice readout. If the binding is retrieved from the
demos, neutralizing them collapses the reading — above random-position controls.

- Harness: `scripts/phase3_demo_neutralize.py` (multi-concept; reuses `pc.DemoStateSwap`,
  `pc.ComponentCapture`). Readout: append `'…does the word "{cw}" refer to "{concept}" or to "{cw}"?'`
  to the demo block, read `p_concept = P(concept)/(P(concept)+P(codeword))` at the answer.
- Jobs: window **703151** (clearharm) / **703153** (curated); per-layer **703152** / **703154**.
  Llama-3.1-8B-Instruct bf16, forced-choice (no API). n_valid = 85/86 clearharm, 51/51 curated
  (valid = DS C1 discriminates from benign).

## Readout validity (built-in)
DS C1 `p_concept`: clearharm mean **0.882**, curated **0.761** (strong hijacked reading). BENIGN
baseline `p_concept` = **0.0 for every example** (codeword reads as itself). Self-swap (DS demo K/V ←
DS own demo K/V) deviation = **0.0** (faithfulness exact). The readout cleanly separates the concept
reading from the codeword reading and does not perturb under a no-op transplant.

## Cells
- **C1** baseline · **C3_demoKV** neutralize demo-codeword resid_pre ← BENIGN demo activations
  (necessity) · **C1_selfswap** ← DS own (faithfulness, ==C1) · **random_control** neutralize
  count-matched NON-codeword positions.
- `ReRead(C1−C3)` = drop in reading from neutralizing demo K/V. **Specific effect = (ReRead) −
  (C1−random)**, paired per example, bootstrap 95% CI (2000 resamples), by canonical window.

## Result — significant on curated, same direction on ClearHarm

| cohort (n) | window | ReRead(C1−C3) | random | **specific (demoKV−random)** | 95% CI | verdict |
|---|---|---|---|---|---|---|
| curated (51) | early | 0.258 | 0.079 | **+0.180** | [+0.026, +0.328] | **SIG** |
| curated (51) | mid | 0.233 | 0.100 | **+0.133** | [+0.053, +0.217] | **SIG** (survives Holm/3) |
| curated (51) | late | −0.014 | 0.016 | −0.030 | [−0.084, +0.018] | ns |
| clearharm (85) | early | 0.116 | 0.072 | +0.044 | [−0.034, +0.132] | ns (same sign) |
| clearharm (85) | mid | 0.108 | 0.069 | +0.039 | [−0.026, +0.105] | ns |
| clearharm (85) | late | −0.015 | 0.008 | −0.022 | [−0.056, +0.009] | ns |

**Per-layer localization (specific effect, ReRead−random):** peaks at **L9–L11 on BOTH cohorts**
(curated L10 +0.128, L9 +0.070, L11 +0.036; clearharm L10 +0.065, L9 +0.026, L8 +0.017), ~0 elsewhere.

## Interpretation
On the **clean curated cohort** the demonstration-codeword activations are **causally necessary** for
the hijacked reading: neutralizing them at early+mid layers reduces the reading significantly more than
neutralizing random positions (early +0.18, mid +0.13; both CIs exclude 0; mid survives Holm across the
3 windows). The single-layer localization concentrates at **L9–L11** — the same mid-band the prior
carrot↔bomb work identified for the attention write / MLP consolidation. This **replicates the
mid-band retrieval mechanism on a multi-concept dataset** with a matched-control necessity test.

On the **ClearHarm cohort** the effect is the **same direction** (positive early/mid, ~0 late, peak
L10) but **not significant** — consistent with ClearHarm's concept noisiness (harm not always in the
single swapped noun), which widens variance and also muddied its behavioral baseline (PHASE2_BEHAVIORAL
Limitation). So the mechanism claim rests on the curated cohort; ClearHarm corroborates the direction.

## Honest caveats
- Neutralization SOURCE is the BENIGN demo activations (same codeword, benign meaning). The DemoStateSwap
  is at resid_pre of demo-codeword positions (K/V into attention), last-`m` aligned across DS/benign.
- Window neutralization > any single-layer effect (distributed within L8–12); the per-layer peak
  identifies the critical layers, not a single bottleneck (matches prior "distributed mid-band").
- Late-window ReRead is slightly negative (neutralizing late demo K/V if anything raises the reading) —
  consistent with late layers being passive carriers, not where retrieval happens.
- This is the NECESSITY leg (position set = demo occurrences, location = resid_pre/K-V). Sufficiency
  (install DS demo K/V into a benign context) and the other 3 locations are the next cells.
