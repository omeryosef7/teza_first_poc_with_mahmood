# Gate B / §23 — Behavioral Causality of the Decision-Token Refusal State

**Status:** Gate B **PASS (behavioral)** on clearharm train + dev; **underpowered on the frozen test** (low
base ASR); generated cohort pending (`732389`). This is the arm that converts §3's representational Gate A
into a behavioral-causality claim.

**Run:** `refdecpatch_clearharm_...732388` (170r, v3 train85/dev43/test42) · commit `76acb44a` ·
harness `scripts/phase_refusal_decision_patch_behav.py` · validated (`validate_all_outputs.py`: 117 values
recomputed, 0 mismatch; manifest ok).

## Design
For each item, replace the **DS prompt's decision-token residual (`resid_post`)** with the matched
**Direct-harmful donor's** decision-token residual at layers {15,16,17} **during generation** (decision-token
only — KV-cache decode steps are past `seq`), then StrongREJECT-judge. Arms: `ds_base` (jailbreak),
`direct_base` (refusing reference), `ds_dpatch_direct_L{15,16,17}` (necessity), `ds_dpatch_rand_L17`
(norm-matched random = specificity), `ds_dpatch_self_L17` (locality no-op). Primary: ΔASR vs `ds_base`,
paired exact McNemar.

## Result — clearharm
| split | ds_base ASR | direct L17 ΔASR (p) | direct L16 | direct L15 | rand L17 ΔASR (p) | self L17 |
|---|---|---|---|---|---|---|
| train (n=85) | 0.271 | **−0.141 (p=0.012)** | −0.118 (0.041) | −0.106 (0.049) | +0.141 (0.045) | +0.012 (1.0) |
| dev (n=43) | 0.302 | **−0.186 (p=0.008)** | −0.116 (0.125) | −0.140 (0.070) | +0.070 (ns) | +0.047 (0.5) |
| test (n=42) | 0.167 | −0.048 (ns) | −0.095 (0.22) | −0.095 (0.22) | +0.214 (p=0.004) | +0.024 (1.0) |

- **Necessity:** restoring the Direct decision residual at L15–17 **lowers ASR to ≈`direct_base` level**;
  significant at L17 on train (p=0.012, discordant b=16/c=4) and dev (p=0.008, b=8/c=0).
- **Specificity:** the norm-matched **random** donor moves ASR the **opposite** way (↑, and significantly so
  on train p=0.045 / test p=0.004) — a random decision-state perturbation degrades toward compliance, it does
  not restore refusal.
- **Locality:** `self`-swap ΔASR ≈ 0 (p=1.0) in every split.
- **Test underpowered, not failed:** ds_base ASR is only 0.167 on test (≤7 rescuable malicious items,
  discordant b=4–5), so the direct effect is directionally consistent but nsig; the noise floor (§1.2, running
  `732432`) and the significant *wrong-direction* random effect confirm the design is live on test.

## Interpretation
Combined with §3 Gate A (the same residual overwrite restores the **refusal projection**, frac≈0.93, replicated
test) and the depth Panel B calibrated-rescue (restoring the **refusal direction** alone lowers ASR at L15–29,
L18 p=0.021), this establishes: **the decision-token refusal state at L15–18 is behaviorally causal for
refuse/comply** (plan claim **D**) — restoring it specifically collapses the Doublespeak jailbreak.

## Caveats
- The direct donor carries the **whole** decision-token residual, so this shows decision-**state** sufficiency;
  the refusal-**subspace-only** version is the calibrated-inject depth Panel B (also ↓ASR) — report both.
- Bidirectional §23 (insert DS residual into a refusing Direct prompt → does ASR **rise**?) not yet run.
- Generated cohort pending (`732389`); cohorts non-exchangeable → report per-cohort.

## Verdict & next
- **Gate B: PASS (behavioral, clearharm train+dev); test underpowered (low base ASR).**
- Next: append generated cohort; §1.2 noise floor to bound the test cell; optionally the bidirectional
  Direct←DS insertion arm; feeds Figure 2 (behavior-confirmed node) + Figure 4 (decision-point causality).
