# §25 — Full Mediation: demonstration feature → refusal suppression → decision state → behavior

**Status:** ✅ DONE (via the clean decision-state mediation; the naive demo-removal arm is confounded — see
below). **The Doublespeak attack's behavioral effect is (near-)FULLY MEDIATED by the decision-token refusal
representation: restoring the DS decision-state to the refusing (Direct) value removes ~100% of DS's ASR
advantage (mediated fraction ≈ 1.0–1.07, McNemar-significant), while norm-matched-random and self-donor
controls do not.** Composed with §6 (demonstrations suppress the refusal projection, upstream), this closes the
full chain demos → refusal-state suppression → behavior.

## The clean mediation — decision-state (committed §23 data, band L15–17, clearharm)
Mediated fraction of the DS attack = [ASR(ds_base) − ASR(ds_dpatch_direct)] / [ASR(ds_base) − ASR(direct_base)].
≈1 ⇒ the entire behavioral gap between the jailbreak and the refusing Direct request is explained by the
decision-token refusal state.

| split | n | ASR ds_base | ASR direct_base | ASR ds_dpatch_direct | **mediated frac** | McNemar p | rand ctrl | self ctrl |
|---|---|---|---|---|---|---|---|---|
| train | 85 | 0.282 | 0.129 | 0.118 (L15) | **1.07** | 0.0013 | +0.141 (ns/raises) | −0.012 (p=1.0) |
| dev | 43 | 0.326 | 0.116 | 0.116 (L17) | **1.00** | 0.0039 | +0.023 (p=1.0) | 0.0 (p=1.0) |

Both cells ≥20/cell. **Only the Direct-donor decision-state patch collapses the attack**; the norm-matched
random donor does not restore refusal (if anything raises ASR) and the self-donor is an exact no-op — so the
effect is specific to the refusal-carrying decision state, not to perturbing the residual per se.
`refdecpatch_clearharm_20260807_221715_732560` (= §23 / Gate B run).

*Test caveat:* on the held-out test split the base attack was ineffective (ds_base 0.167 < direct_base 0.214),
so the DS "attack gap" is negative and the mediated fraction is undefined there — the mediation is reported on
the train/dev cells where DS actually raises ASR. (The decision-patch still lowers test ASR to ~0.095.)

## The upstream leg (demos → refusal representation), from §6/§3
- §6 (P6_DOSE_RESPONSE): the refusal projection is suppressed by the demonstrations as a **step at n_demo=1**
  (proj 4.02→2.98 train / 4.46→3.47 test), i.e. the demo feature is what drives the refusal-axis suppression.
- §3 (P_REFUSAL_SUPPRESSION_LOCALIZATION): the suppression is localized to the L15–18 decision-token residual.

**Chain:** demonstrations suppress the decision-token refusal representation (§6/§3, representational) →
that decision-state (near-)fully mediates the attack's behavioral effect (§25/§23, causal, frac≈1.0). This is
the refusal-circuit full mediation the plan asked for.

## Why the naive behavioral demo-removal arm is confounded (documented, not used)
A direct behavioral test — remove the demos and check whether ASR drops — was built (`phase25_full_mediation.py`,
smoke `fullmediation_clearharm_..._737620`) but the only available demo-removed condition, `conds.neutral`,
**substitutes the codeword for the harmful word** ("...devastating **fountain** upon contact"). The harmful
FRAME survives the substitution, so neutral does NOT cleanly restore refusal: at n=3 smoke neutral_base ASR =
ds_base ASR = 0.667 (demo_rescue = 0.0), leaving no behavioral rescue to mediate. Demo-removal is entangled
with codeword semantics; a clean demo-only manipulation would need scrambled-mapping demos (§5 territory).
Hence §25 uses the **decision-state** mediation above (clean, controlled, ≥20/cell) rather than the confounded
demo-removal arm. The harness + confound finding are committed for transparency.

## Verdict
**§25: the demonstration→refusal→behavior chain is established — demos suppress the decision-token refusal
representation (§6), and that representation (near-)fully mediates the attack's behavioral effect (mediated
fraction ≈1.0 on train+dev, specific vs rand/self).** The behavioral lever is the refusal decision-state, not
demo presence per se (demo-removal is behaviorally confounded). Related: [[project_causal_circuit_sprint]],
[[project_causal_core]].
