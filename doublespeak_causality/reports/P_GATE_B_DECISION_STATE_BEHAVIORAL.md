# Gate B / §23 — Behavioral Causality of the Decision-Token Refusal State

**Status:** Gate B **PASS (behavioral)** on clearharm train + dev; **underpowered on the frozen test** (low
base ASR); **generated cohort DONE = NULL** (`732389`, self-explaining, below); **bidirectional §23 arm
RUNNING** (`732560`, will strengthen to Gate B STRONG if the reverse swap raises ASR). This is the arm that
converts §3's representational Gate A into a behavioral-causality claim.

**Judge-noise note:** `ds_base` ASR here (0.271 train, single judge) differs ~3.5pp from the §1.2 drift run's
DS ASR (0.306, majority-of-3) — this is entirely StrongREJECT between-run stochasticity (generation is
deterministic; §1.2 between-run floor ≈6pp), so do not quote the two baselines interchangeably. All ΔASR below
are **within-run paired** (same job/judge pass), and the significant effects have **asymmetric** McNemar
discordance (train L17 b=16/c=4) that symmetric judge noise cannot produce — the paired tests are robust.

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
L18 p=0.021), this establishes: **restoring the decision-token refusal state at L15–18 is causally sufficient to
re-engage refusal** — a specific, replicated, within-run-paired NECESSITY+specificity+locality result (plan
claim **D**, *refuse direction*). Scope (audit 2026-08-08): this is the forward direction only; the *comply*
direction — that the DS/suppressed decision state is sufficient to force compliance — is a documented **NULL**
(the reverse arm, below), so this is not bidirectional control. Effect size is a reduction to ≈`direct_base`
level (ASR 0.27→0.13 train), i.e. the jailbreak is removed to the refusing-baseline rate, not to zero.

## Result — generated cohort (NULL, and self-explaining)
`refdecpatch_generated_...732389` (154r, validated 117 vals/0 mismatch). Here **`direct_base` ASR > `ds_base`
ASR** (train 0.49 vs 0.40; dev 0.44 vs 0.36; test 0.39 vs 0.37) — i.e. Doublespeak is **net-negative** on the
generated cohort (the pre-registered non-exchangeability), so there is no refusal-suppression to restore. The
direct patch gives only small non-significant ΔASR (train L17 −0.052 p=0.52; test L15 −0.132 p=0.18); `self`
no-op ≈0 (locality holds). **Gate B NULL on generated is expected and coherent: the mechanism appears exactly
where the attack actually works (clearharm), and is absent where DS does not suppress refusal (generated).**

## Bidirectional §23 (`732560`, clearharm) — forward REPLICATES; reverse is a NULL (honest, not STRONG)
An independent run with the reverse arm added. **Forward reproduces Gate B**: `ds_dpatch_direct_L17` ΔASR
−0.153 (p=0.011) here vs −0.141 (p=0.012) in 732388 — reproducible within the judge floor; self≈0; rand +0.141.

**Reverse (insert DS decision resid into a *refusing Direct* prompt → does ASR rise?):**
| reverse arm | train ΔASR vs direct (p) | dev | test |
|---|---|---|---|
| `direct_dpatch_ds_L15/16/17` | +0.01 / +0.01 / +0.05 (all **ns**, p≥0.34) | +0.09 ns | ~0 ns |
| `direct_dpatch_rand_L17` | **+0.341 (p<1e-3, b=30/c=1)** | +0.256 (p=0.001) | +0.095 ns |
| `direct_dpatch_self_L17` | +0.012 (no-op ✓) | +0.047 | −0.024 |

**Two findings, both honest:**
1. **The DS decision state is NOT sufficient to induce compliance** — inserting it into a refusing Direct
   prompt barely moves ASR (≈ self no-op level). So the bidirectional swap is **not clean**: Gate B stays
   **PASS (forward), not STRONG.** Compliance is *not* carried by a specific "DS decision vector."
2. **Decision-state fragility:** a norm-matched *random* perturbation at the decision token **raises ASR on
   train in BOTH directions** (reverse +0.341 p<1e-3 b=30/c=1; forward rand +0.14) with empty_rate=0 (coherent,
   not garbled). *Caveat (audit 2026-08-08): the reverse-random effect is TRAIN-only — it is +0.095, p=0.39
   (ns) on the frozen test split (underpowered / low base). The train effect is large and highly significant;
   the fragility claim rests on train + the specific-vs-random asymmetry (structured DS/self donors, norm-
   identical to rand, are inert), not on the frozen test.* Refusal at the decision token is not robust to
   norm-matched noise — an adversarial fragility
   result. *Caveat:* the random vector is norm-matched to the (larger) DS residual, so part of this is a
   large in-magnitude OOD perturbation; the specific-vs-random asymmetry still holds (structured DS/self are
   inert, random is not).

**Synthesis:** refusal decision-state **restoration is specific and causal** (forward), but **breaking
refusal is generic** (any sufficient decision-state disruption complies). The mechanism is "an intact refusal
decision state is required to refuse," not "a DS compliance signal overrides it."

## Caveats
- The direct donor carries the **whole** decision-token residual, so this shows decision-**state** sufficiency;
  the refusal-**subspace-only** version is the calibrated-inject depth Panel B (also ↓ASR) — report both.
- Bidirectional §23 (insert DS residual into a refusing Direct prompt → does ASR **rise**?) **RUNNING** (`732560`).
- Generated cohort **DONE = NULL** (`732389`, see above); cohorts non-exchangeable → reported per-cohort.

## Verdict & next
- **Gate B: PASS (behavioral, clearharm train+dev); NULL on generated (DS net-negative there); test cell underpowered (low base ASR).**
- Next: §1.2 noise floor to bound the test cell; optionally the bidirectional
  Direct←DS insertion arm; feeds Figure 2 (behavior-confirmed node) + Figure 4 (decision-point causality).
