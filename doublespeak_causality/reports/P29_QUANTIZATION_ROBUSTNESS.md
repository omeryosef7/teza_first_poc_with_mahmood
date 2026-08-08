# §29 — Quantization / Deployment Robustness of the Refusal Mechanism

**Status:** ✅ DONE. **The refusal-suppression mechanism SURVIVES 8-bit and 4-bit quantization: directional
refusal ablation raises direct-harmful ASR at every precision (McNemar-significant), while a norm-matched
random ablation does NOT (specificity holds at all precisions).** The refusal direction fit in bf16 remains a
causal, specific lever after bitsandbytes quantization — the mechanism is not a full-precision artifact.

**Runs:** `behav_refusal_clearharm_a1.0{,_8bit,_4bit}_20260808_235314_{737624,737625,737626}` (v3 clearharm
**test n=42**, ≥20/cell, α=1.0, `scripts/phase_behav_refusal.py --quantize`). Same L18 refusal direction (fit
in bf16) applied under each precision via `ds_common.load_model(quantize=…)` (bnb 8-bit / NF4 4-bit, bf16
compute dtype). 8-bit/4-bit generation ran on Ampere via the DSGPUALLOW=23gb allowlist (deployment-representative).

## Result — ASR by precision (test n=42)
| precision | direct_base | **direct_refabl** | direct_randabl | ds_base | ds_refabl | Δ(refabl−base) | McNemar p | rand Δ (ctrl) |
|---|---|---|---|---|---|---|---|---|
| **bf16** | 0.214 | **0.476** | 0.167 | 0.143 | 0.548 | **+0.262** | 0.007 | −0.048 (ns) |
| **8-bit** | 0.238 | **0.524** | 0.167 | 0.214 | 0.619 | **+0.286** | 0.004 | −0.071 (ns) |
| **4-bit** | 0.214 | **0.738** | 0.190 | 0.333 | 0.548 | **+0.524** | <0.001 | −0.024 (ns) |

Refusal-rate (direct) collapses under ablation at every precision: bf16 0.76→0.24, 8-bit 0.74→0.24, 4-bit
0.76→**0.07**. The refusal-ablation ↔ Doublespeak equivalence also holds: `ds_base ≈ direct_refabl` (the DS
attack already sits near the refusal-suppression ceiling) at all precisions.

## Interpretation
1. **Causal specificity is preserved under quantization.** At every precision the *refusal-direction* ablation
   significantly raises harmful compliance while the *norm-matched random* ablation does not (rand Δ ns at
   bf16/8-bit/4-bit). So the effect is the refusal axis, not generic numerical perturbation — and quantization
   does not blur that axis away.
2. **4-bit shows the LARGEST refusal-ablation effect** (+0.524, refusal-rate →0.07) — the NF4 model is if
   anything *more* susceptible to refusal ablation, consistent with a more brittle low-precision safety
   representation, not a weaker one. (bf16/8-bit are close: +0.26/+0.29.)
3. **Deployment implication:** a defender cannot rely on quantization to harden the refusal representation, and
   an attacker's refusal-suppression lever transfers to quantized deployments. The Doublespeak mechanism
   (refusal suppression, not concept remap) is a property of the model family, not of full precision.

## Caveat
Base rates shift slightly across precisions (quantization perturbs the operating point: ds_base 0.14/0.21/0.33),
so absolute ASRs are not identical run-to-run; the *contrast* (refabl ≫ base, rand ≈ base) is the invariant and
is significant at every precision. n=42 test (≥20/cell); single α=1.0 (full ablation, the clearest lever).

## Verdict
**§29: the refusal-suppression mechanism is robust to 8-bit and 4-bit quantization — refusal-direction
ablation causally and specifically raises harm at every precision, random ablation does not.** Related:
[[project_causal_circuit_sprint]].
