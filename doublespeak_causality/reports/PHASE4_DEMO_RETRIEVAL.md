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

## Result — necessity SIG in the mid band (both cohorts); NOT sufficient

Matched-control design (jobs **703237/703238**, full data, unified harness): necessity specific effect
= (random − C3) paired per example; the random control uses the SAME benign donor as C3 at random
NON-codeword positions (an earlier version sourced random from DS-own activations — a near-no-op that
inflated the effect; caught and fixed).

**Necessity** (neutralize DS demo-codeword K/V ← benign; specific = random−C3, 95% CI):

| cohort (n) | early | mid | late |
|---|---|---|---|
| curated (51) | **+0.258 [0.146, 0.372] SIG** | **+0.177 [0.087, 0.278] SIG** | −0.037 [−0.097, 0.015] ns |
| clearharm (85) | +0.017 [−0.054, 0.087] ns | **+0.081 [0.012, 0.151] SIG** | −0.009 [−0.023, 0.004] ns |

**Sufficiency** (install DS demo-codeword K/V into the BENIGN receiver; specific = S3−S_random, 95% CI):
robust **null** — installing does NOT create the reading. S3 `p_concept`: curated ≈ **0.0001** (all
windows), clearharm 0.05–0.12 (small, non-specific: SUF_specific CIs include/below 0 at every window).

**Per-layer localization** (from the corrected-control layer runs 703248/703249): peaks in the
**L9–L11 mid-band on both cohorts** (updating; earlier L9–11 peak was from the inflated control).

Self-swap faithfulness (DS demo K/V ← DS own): max deviation **0.0** both directions (exact no-op).

## Interpretation — necessary but not sufficient (distributed, context-bound)
The demonstration-codeword K/V is **causally necessary** for the hijacked reading in the **mid band**:
neutralizing it reduces the reading significantly more than the matched random control — **significant on
BOTH cohorts at mid** (curated also at early; curated effects ~3× larger, as expected for the cleaner
harm-in-one-noun cohort). But it is **NOT sufficient**: transplanting the DS demo-codeword K/V into a
benign receiver does not install the reading (S3 ≈ 0 at all depths incl. late).

This necessity-without-sufficiency is the signature of a **distributed, context-bound** binding: the
codeword K/V participates in the retrieval (removing it hurts) but the reading requires that K/V *within*
its surrounding harmful demonstration context — the local activations alone don't carry it. This is the
direct multi-concept, matched-control confirmation of the prior **IE_state ≈ 0 / DE_context ≈ 99%**
dissociation, and it rules out a naive "the codeword state stores the concept" account.

## Honest notes
- The corrected matched control lowered the necessity effect vs an earlier inflated version; ClearHarm
  early dropped to ns (only mid survives), curated stayed strongly SIG at early+mid. Reported values are
  the corrected ones.
- Necessity leg only (position set = demo occurrences, location = resid_pre / K-V). The exact per-head
  query→demo edge knockout (surgical induction test) and the other locations are subsequent cells.
