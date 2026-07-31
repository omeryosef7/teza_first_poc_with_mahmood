# NEXT5 — Findings (max-depth sprint)

Plan: `NEXT5_PLAN.md`. Env: Llama-3.1-8B / Qwen3-14B / DeepSeek-R1-Distill-8B, L40S, poc_stage2,
forced_choice. Honest — negatives included. Scalars only; no harmful text in any artifact.

---

## W1 — Per-pair-timing behavioral TOCTOU: the #6 negative becomes a POSITIVE. **[WIN]**

**Claim:** the depth-gated refusal TOCTOU (§3.3) generalizes behaviorally to grenade/chlorine when
the concept is installed at **each pair's OWN dominant depth** (MID, pre-registered from the
*independent* T3 representational probe `47_repr_toctou`), which the original early-vs-late
factorial (#6) missed.

**Method (pure CPU re-reduction of committed artifacts — no new GPU):** added a generic
`INTERACTION_mid_late = refusal_gain(mid) − refusal_gain(late)` estimand to
`45_toctou_factorial.py::analyze_rows`, alongside the untouched early−late `INTERACTION`. The
dominant depth per pair comes from T3 (bomb→early, grenade/chlorine→mid) — an independent
measurement, so this is **not** double-dipping on the behavioral data. Re-reduced the committed
runs (grenade `..._695290`, chlorine `..._695291`, bomb `..._694811`); pooled the two mid-dominant
pairs with `next5_w1_pooled_toctou.py`.

| pair | dominant (T3) | early−late INTERACTION | **mid−late INTERACTION** | note |
|---|---|---|---|---|
| **bomb** | early | **+0.425 [+0.25,+0.60]** p_holm=0.011 ✅ | +0.075 [−0.13,+0.28] NS | regression check: early−late **unchanged** from committed |
| grenade | mid | −0.025 [−0.15,+0.10] NS | +0.125 [−0.03,+0.28] p_raw=0.186 | positive trend at own depth |
| chlorine | mid | +0.150 [−0.05,+0.33] NS | +0.150 [+0.03,+0.28] p_raw=0.068 | raw CI excludes 0 at own depth |
| **POOLED (grenade+chlorine)** | mid | — | **+0.1375 [+0.0375,+0.2375] n=80 p_raw=0.0148** | **CI excludes 0** |

- **Pooled across the two independently-mid-dominant pairs: +0.1375 [+0.0375,+0.2375], n=80,
  p_raw=0.0148** — significant. Identical CI under a **cluster-robust (within-pair) bootstrap**
  (`[+0.0375,+0.2375]`, equal pair weight), so it is not an iid-pooling artifact.
- **Regression:** bomb's early−late INTERACTION reproduces bit-identically (+0.4250, Holm-sig) —
  the new estimand is purely additive.
- **Interpretation:** the behavioral compliance-flip interaction (ablate-refusal buys more malicious
  behavior when the concept is installed at the depth the refusal check *does not* cover) is
  **positive at each pair's own dominant depth** and significant when pooled per the pre-registered
  T3 assignment. The original #6 negative was an artifact of testing every pair at *early* timing;
  grenade/chlorine's refusal check sits at *mid*, so the correct depth-matched contrast recovers the
  interaction. → the depth-gated-refusal TOCTOU is a **general** property; only the specific gating
  *depth* is pair-dependent.
- **Honest scope:** individually the two pairs are underpowered at n=40 (grenade trend p=0.19,
  chlorine marginal p=0.068); the robust result is the pooled/pre-registered test. A per-pair
  Holm-robust confirmation would need larger n (tier-2 GPU rerun; bench has 60 unique pids) — noted
  as available, not required for the generalized claim.
- **Gate:** PASS — pooled CI excludes 0 with the T3-predicted sign; bomb regression unchanged.
- Code: `45_toctou_factorial.py` (new `INTERACTION_mid_late`), `next5_w1_pooled_toctou.py` (pooled +
  stratified). Artifacts: `outputs/toctou_*_695290/695291/694811/toctou_reanalysis.json`.

---

## W3-b — Superposition test: the paper's SECOND hypothesis is SUPPORTED (controlled). **[WIN]**

**Claim:** the Doublespeak codeword-position representation simultaneously encodes the codeword
identity (carrot) AND the harmful concept (bomb) — the paper's untested *semantic superposition*
hypothesis (§3.4), complementing our causal TOCTOU result. Adjudicated by direction projection —
zero new model runs, reuses committed diff-of-means axes + captured reps.

**Method (CPU):** axes built on DEV, unit-normalized per layer, anchored at the NEUTRAL mean;
reps projected on HELDOUT (clean train/test). concept axis = `d_Direct` (DIRECT−NEUTRAL); codeword
axis = `d_repeated` (REPEATED_CODEWORD−NEUTRAL). Per rep: `(r−μ_NEUTRAL)·axis_hat`. Band = layers
12–24. `next5_w3b_superposition.py`.

| condition | n | concept component [CI] | codeword component [CI] |
|---|---|---|---|
| DIRECT_CONCEPT | 15 | **+14.13** [14.03,14.22] | +4.19 [4.10,4.29] |
| REPEATED_CODEWORD | 3† | +1.92 | **+6.72** |
| **DOUBLESPEAK** | 15 | **+1.81** [+1.55,+2.08] | **+3.02** [+2.56,+3.49] |
| NEUTRAL_CODEWORD | 15 | −0.09 [−0.22,+0.04] | +0.03 [−0.18,+0.26] |
| BENIGN_REMAP (ctrl) | 15 | +1.25 [1.11,1.40] | +2.50 [2.24,2.76] |
| UNRELATED_TARGET (ctrl) | 15 | +1.35 [1.20,1.48] | +2.71 [2.47,2.92] |

- **Control separation holds:** DIRECT loads concept ≫ codeword (+14.1 vs +4.2); REPEATED loads
  codeword ≫ concept (+6.7 vs +1.9); NEUTRAL ≈ 0 on both (the anchor). Concept and codeword axes
  are **distinct** (cos = 0.28 in-band).
- **DS loads BOTH** components (both CIs exclude 0, n=15) — the superposition signature.
- **DS concept component is DS-SPECIFIC**, above the remap controls that share the codeword
  structure: DS−BENIGN = **+0.555 [+0.260,+0.866]**, DS−UNRELATED = **+0.459 [+0.173,+0.769]**
  (two-sample bootstrap, both exclude 0). The codeword component is NOT DS-specific (every
  codeword/remap condition carries it, as expected) — the DS-specific signal is the **concept
  riding on top of the retained codeword component**, which is exactly superposition.
- **Not a correlation artifact:** the concept excess (+0.56) far exceeds the leakage the 0.28
  axis-correlation could induce from DS's codeword excess (≈0.5 × 0.28 = 0.14).
- **Honest scope:** the concept component is small (+1.8 ≈ 13% of DIRECT's +14.1) — superposition
  with a *weak* concept loading, consistent with the context-carried reading (~0.35) and the small
  additive install (B4/N4). †The codeword AXIS anchor (REPEATED_CODEWORD) is n=3, so that axis is
  noisy; but the load-bearing concept-specificity test uses n=15 conditions.
- **Gate:** PASS — controls separate; DS loads both; concept component DS-specific vs both remap
  controls. Together with S4/T3, **both** of the paper's §3.4 hypothesized mechanisms (TOCTOU and
  superposition) are now empirically tested — TOCTOU causally, superposition representationally.
- Code: `next5_w3b_superposition.py`. Artifact:
  `outputs/pair_reps_..._694691/w3b_superposition.json`.

---

## W4 — Attention-head circuit localization. **[tier-A: distributed (no sparse bottleneck); tier-B pending]**

### Tier A — per-LAYER attention knockout: no single-layer bottleneck. **[negative that reinforces S3/T4]**
`36_pair_attention.py --mode knockout --granularity per_layer --readout forced_choice` (heldout,
n=10 prompts, 3220 rows, job 696227) blocks attention from the query codeword to each source set
(demos_all/first/last, prev_codewords; request_only + random_matched controls) one layer at a time,
scoring the DOUBLESPEAK forced-choice concept reading. Reduced with `next5_w4_knockout_reduce.py`
(paired bootstrap CI + Holm + random control).
- **Blocking query→demo attention at any single layer barely moves the reading** — the largest
  concept-reading drop is **+0.024** (L1), and **NO group survives Holm** (all p_holm = 1.0). The
  demonstration-blocking sets (demos_*) give ≤ ~0.014. Baseline DS reading ~0.35, so the biggest
  single-layer knockout removes < 7% relative.
- **Interpretation:** there is **no sparse single-layer attention bottleneck** carrying the
  context effect — consistent with S3 (91% of the reading survives neutralizing the demo K/V) and
  T4 (the effect is distributed, not localized to demonstrations). An honest negative for a clean
  single-layer circuit; positive evidence for distributed computation.
- Artifact: `outputs/pair_attn_knockout_..._696227/knockout_reduce.json`.

### Tier B — per-HEAD z-attribution (layer×head AtP + true-patch gate): running (job 696255).
`49_head_attribution.py` (new `ZHeadCapture`/`ZHeadPatch`) computes AtP[L,h,pos] on the per-head
attention output z, validated against real per-head z-patches. Tests whether a sparse set of HEADS
(across layers) carries the effect even though no single LAYER does. Result pending.
