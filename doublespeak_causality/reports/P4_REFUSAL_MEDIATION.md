# §4 — Refusal CARRY-vs-READOUT Mediation (direct-vs-total decomposition)

**Status:** ✅ DONE. **The §7 refusal-carry heads act mostly as CARRY, not readout: their effect on the
decision-token refusal projection is 72–88% MEDIATED (recomputed by downstream components), with a clean
DEPTH GRADIENT — early-band L13 heads are ~88% mediated (pure carry), late-band L16 heads become progressively
readout-proximal (L16H10 ≈ 50/50).** This is the refusal-circuit analogue of the concept-circuit mediation
(~75–83% mediated) and confirms the refusal evidence is *carried forward and re-derived*, not read out locally
by any single head. Separates B(carry) from C(readout); the A(demo-origin) sub-question is deferred to §5
(position-aligned) because DIRECT lacks the demo tokens.

**Run:** `refusal_mediation_clearharm_20260808_233827_737608` (v3 clearharm **test n=42**, ≥20/cell ✓,
`scripts/phase4_refusal_mediation.py`). Reuses the VALIDATED freeze primitives verbatim
(`pp50.capture_clean_all` / `FreezeAllHeadsExcept` / `FreezeMLP`, `pc.ZHeadPatch` / `ZHeadCapture`) and copies
`phase7_direct_total.py`'s freeze-consistency + self-swap sanity gates. Metric M = decision-token refusal-axis
projection at hidden_states[L19] (validated L18 direction). clean = DS (refusal suppressed); donor = DIRECT
decision-token per-head z (the LAST prompt token, aligned between DS and DIRECT).

## Result — per §7 head (test n=42; TOTAL/DIRECT = restoration of refusal proj; median_gap=1.75)
| head | TOTAL | DIRECT | direct_frac | **mediated_frac** | trust |
|---|---|---|---|---|---|
| L13H9  | 0.130 | 0.021 | 0.122 | **0.878** | ✓ (selfdev 0, freezedev 0) |
| L13H11 | 0.086 | 0.010 | 0.117 | **0.883** | ✓ |
| L13H18 | 0.144 | 0.024 | 0.116 | **0.884** | ✓ |
| L15H7  | 0.298 | 0.063 | 0.201 | **0.799** | ✓ |
| L16H4  | 0.228 | 0.068 | 0.277 | **0.723** | ✓ |
| L16H10 | 0.111 | 0.064 | 0.494 | **0.506** | ✓ |

**Every head passes both sanity gates exactly** (self-swap dev = 0.0 → patching DS's own z is a perfect no-op;
freeze-consistency dev = 0.0 → freeze-all-clean + clean-sender reproduces M(DS) to the digit), so the freeze
machinery is not compromised and the fractions are trustworthy.

## Interpretation
1. **Refusal is carried, not locally read.** For the L13 heads only ~12% of their effect on the decision-token
   refusal projection reaches the readout via the residual skip; ~88% is recomputed by downstream heads/MLPs.
   No head is a readout bottleneck — consistent with §7's head-distributed / L13-concentrated picture and with
   the concept-circuit's ~75–83% mediation.
2. **Depth gradient (carry → readout).** mediated_frac falls monotonically with sender depth: L13 (~0.88) →
   L15 (0.80) → L16H4 (0.72) → L16H10 (0.51). The later a head sits in the L13–20 band, the more of its effect
   is direct-to-readout — exactly what a carry-then-read pipeline predicts (early heads write the "do-not-refuse"
   evidence into the stream; later heads increasingly *are* the readout).
3. **Load-bearing sender = L15H7** (largest TOTAL restoration, 0.298) and it is still 80% mediated — even the
   strongest single restorer is mostly carry.

## Scope / caveats
- This is the **B(carry)-vs-C(readout)** separation at the aligned decision token. The **A(demo-origin)** part
  ("where in the demos DS originates the suppression") requires patching demo-side positions, which DIRECT lacks
  → position-alignment-confounded here; that question is addressed by §5's matched demo-variant analysis.
- Effect sizes are on the refusal-projection scale (median gap DS→DIRECT ≈ 1.75); the *fractions* are the
  invariant quantity and are what the mediation claim rests on.

## Verdict
**§4: the refusal-carry heads are predominantly CARRY (72–88% mediated) with a clean depth gradient toward
readout at the late band.** The refusal-suppression evidence is distributed and re-derived downstream, not
read out by a local head — the refusal-circuit analogue of the concept-circuit mediation, and consistent with
§3/§7. Related: [[project_causal_circuit_sprint]].
