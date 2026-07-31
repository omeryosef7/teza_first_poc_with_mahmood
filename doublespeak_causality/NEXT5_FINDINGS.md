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
