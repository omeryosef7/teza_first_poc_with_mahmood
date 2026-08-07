# Phase WRITE×REFUSAL — Are the concept-remap and refusal-suppression causally coupled?

**Question.** The demonstrations do two things that both onset in the **L8–11 band** (per the projection
result): (a) remap codeword→concept (the L8–11 MLP write) and (b) suppress the refusal axis. Are these
**causally independent**, or does the concept-write **cause** the refusal suppression? This decides the
mechanistic framing: if independent, the concept circuit is a genuine bystander and the refusal bypass rides
a separate pathway (explaining the behavioral nulls); if coupled, the remap is the *vehicle* for the bypass.

**Design (forward-only, matched to BEHAV-WRITE + the projection readout).** For each DS prompt, ablate the
concept **write** exactly as BEHAV-WRITE — zero the L8–11 MLP output at the **DEMO** codeword positions
(`pc.ComponentOutSwap`, prefill) — and measure the **refusal-axis projection** of the decision-token residual
(per-layer refusal direction), for three conditions: **direct** (harmful, high-refusal reference), **ds_base**,
**ds_writeabl**. Metric = `frac_of_direct_gap_restored = (ds_writeabl − ds_base)/(direct − ds_base)` per layer
(0 = write-ablation does nothing to refusal; 1 = it fully restores refusal to direct-harmful level).
**Positive control:** the FC `p_concept` readout under the same write-ablation must **drop** (confirms the
ablation fired). Single-BOS tokenization (cleaner than the original projection harness). Cohorts clearharm
(44/42) + curated (30/21).

## Result — CAUSALLY INDEPENDENT (write-ablation kills the concept readout, leaves refusal suppression intact)

**Positive control (write-ablation fired):** `p_concept` drops in every cell (CIs exclude 0) —
clearharm .884→.799 / .858→.817; curated .811→.751 / **.690→.457**. The demo-write ablation genuinely
degrades the concept representation (strongly on curated).

**Main readout — refusal suppression is UNMOVED by write-ablation:**

> **Ranges corrected 2026-08-06 (audit O4):** the four range endpoints previously shown were arbitrary
> interior layers, not the min/max, and curated-train was misstated as entirely negative when it
> straddles zero. Every range below is now the true min…max recomputed from `summary.json`
> (`by_split.<split>.per_layer.<L>.frac_of_direct_gap_restored`), with the argmax layer named. The
> qualitative conclusion — all |values| ≤ 0.05 — is unchanged; the spread is ~47 % wider than first
> reported.

| cohort·split | p_concept ds→wabl | refusal `frac_of_direct_gap_restored` (range over layers) |
|---|---|---|
| clearharm train | .884→.799 | **−0.023 (hs28) … +0.015 (hs12)** (≈ 0) |
| clearharm test  | .858→.817 | **−0.017 (hs30) … +0.025 (hs16)** (≈ 0) |
| curated train   | .811→.751 | **−0.050 (hs18) … +0.011 (hs12)** (≈ 0) |
| curated test    | .690→.457 | **−0.010 (hs32) … +0.019 (hs15)** (≈ 0) |

At **every layer in every cell**, `frac_restored ≈ 0` (|value| ≤ 0.05, max |.| = 0.050 at curated-train
hs18) — the refusal-axis projection under
DS+write-ablation is statistically identical to DS alone (`Δ(writeabl−ds)` CIs include 0 throughout), and
stays far below direct-harmful. E.g. clearharm test hs32: direct 65.5, ds 27.5, ds_writeabl 27.3.

**⇒ The concept-write and the refusal-suppression are causally INDEPENDENT.** Ablating the concept-write
measurably reduces the concept readout (control fires, curated .69→.46) but leaves Doublespeak's refusal
suppression **completely intact**.

## Interpretation — this is WHY the concept circuit is behaviorally epiphenomenal

The demonstrations do two things in the same L8–11 band, but via **separate pathways**:
1. **Concept remap** (L8–11 write → carry → readout) — representationally necessary+sufficient for the
   codeword→concept *readout*, but **behaviorally inert** (BEHAV-CARRY/WRITE).
2. **Refusal suppression** (the axis DS pushes the hidden state off) — the **behavioral driver**
   (necessary+sufficient; BEHAV-REFUSAL).

These are not just orthogonal in representation (cos≈0.03) and dissociated in behavior — they are
**causally decoupled at the source**: knocking out (1) does nothing to (2). That directly explains the
central dissociation — the harm-enabling refusal bypass does not depend on the concept machinery at all, so
ablating the concept circuit cannot reduce ASR. The concept remap is a genuine *bystander*, not the vehicle
for the bypass. (It also confirms the projection result with cleaner single-BOS tokenization: DS ≪ direct on
the refusal axis at every layer, both cohorts.)

**Caveat.** This shows the concept-write does not *causally sustain* the refusal suppression at the readout
position (forward pass). It does not rule out that a *shared upstream* cause (the demonstration context
itself) produces both — indeed that is the natural reading: the demos independently (i) install the remap and
(ii) push off the refusal axis. What is ruled out is the "remap → refusal-suppression" causal chain.

## Reproduce
```
sbatch --time=00:40:00 --export=ALL,DSBENCH=doublespeak_causality/data/behavioral/beh_clearharm.json,DSN=0 \
  doublespeak_causality/slurm/run_wrxintx.sh          # + beh_curated.json
```
Runs: clearharm `write_refusal_intx_clearharm_20260804_231656_711887`, curated `..._711888`.
Harness `scripts/phase_write_refusal_interaction.py` (ComponentOutSwap write-zero + per-layer refusal
projection + FC p_concept firing control).

---

## Resolution of WR-02 against the landed P7 refusal-direction validation (2026-08-07)

WR-02 ("concept-write ⊥ refusal-suppression: `frac_of_direct_gap_restored` ≈ 0, |·| < 0.05 at every layer")
was previously **PENDING** on the per-layer refusal directions being validated, because the readout is the
per-layer refusal projection and an independence result measured on a *non-refusal* axis would be vacuous.
P7 (`P7_REFUSAL_DIRECTION_VALIDATION.md`, jobs 720463 / 721957 / 722611 / 724931) has now landed: the
refusal axis is linearly decodable only from **L13 onward**, and the layers validating **in both direction
families** are **{L13–L20, L24, L28, L29}**.

**Re-reading `frac_of_direct_gap_restored` restricted to those validated layers confirms — and strengthens —
the independence:**

| cohort · split | n | max \|frac_restored\| over validated layers | L16 | L18 | L22 |
|---|---|---|---|---|---|
| clearharm train | 44 | **0.021** | +0.004 | +0.010 | −0.004 |
| clearharm test | 42 | **0.025** | +0.015 | +0.012 | +0.002 |
| curated train | 30 | **0.050** | −0.047 | −0.049 | −0.037 |
| curated test | 21 | **0.019** | −0.002 | +0.007 | +0.002 |

At **every** validated refusal layer — including the exact L16/L18/L22 anchors the behavioral rescue uses —
ablating the L8–11 concept write moves DS's refusal suppression by **≤ 5% of the direct gap** (≤ 2.5% on
clearharm). The independence is therefore **not an artifact of projecting onto an unvalidated axis**: it holds
precisely where the refusal axis is real. **WR-02 is CONFIRMED.** (The positive control still fires: the same
write ablation drops the FC `p_concept` readout by 0.06–0.23 per cell — the hook is live, it simply does
nothing to the refusal channel.)
