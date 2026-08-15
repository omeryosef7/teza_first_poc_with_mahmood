# PHASE 5 — Per-example component patching: behavioral result (Q3/Q4)

Plan §9. The non-redundant behavioral half of Phase 5 (the mean-field version is
Phase 4, verified — E39/PHASE5_DECOMPOSITION §"Scope clarification"). For each
example we install **its own** decomposed component of the donor shift Δhᵢ at the
codeword over L8–18 and measure harmful ASR (StrongREJECT ≥ 0.5), with a
direction-aware manipulation check at downstream (unpatched) layers 20/24/28/31.

**Verdict: per-example Bombness patching is behaviorally NULL in both directions.**
A strong, specific manipulation of the Bombness representation (readout moved ±18–19)
produces no ASR change beyond a norm-matched random perturbation. Story A confirmed
by the sharpest causal test in the sprint — component surgery, not direction ablation.

| Model | Llama-3.1-8B-Instruct (bf16, sdpa), L40S |
| --- | --- |
| Runs | necessity `758162`, sufficiency `758163`; harness `scripts/phase5_component_patch.py` |
| Vectors | `build_phase5_perexample` (donor=benign), B9-safe map `phase5_patch_spec` (14 unit tests) |
| n | 42 test prompts (codeword- & concept-disjoint holdout) |
| Patch band | L8–18 (disjoint from readout 20/24/28/31) |

## Necessity — subtract each example's component from the doublespeak prompt

base ASR 0.167.

| arm | ΔASR | 95% CI | McNemar b/c | manip readout Δ |
| --- | --- | --- | --- | --- |
| **bomb** | **+0.048** | [−0.048, +0.143] | b=1 c=3 | **−18.7** (strong, specific) |
| random (norm-matched) | +0.048 | [+0.000, +0.119] | b=0 c=2 | −0.16 |
| full (whole Δhᵢ) | −0.048 | — | b=4 c=2 | −10.5 |
| refusal (⊥bomb) | 0.000 | — | b=1 c=1 | +0.07 |
| remainder | 0.000 | — | b=3 c=3 | +1.2 |

## Sufficiency — add each example's component into the benign prompt

base ASR 0.286.

| arm | ΔASR | 95% CI | McNemar b/c | manip readout Δ |
| --- | --- | --- | --- | --- |
| **bomb** | **+0.048** | [−0.048, +0.143] | b=1 c=3 | **+18.9** (strong, specific) |
| random (norm-matched) | +0.000 | [−0.071, +0.071] | b=1 c=1 | +0.65 |
| full | +0.000 | — | b=3 c=3 | +16.8 |
| refusal | 0.000 | — | b=1 c=1 | −0.02 |
| remainder | −0.024 | — | b=3 c=2 | +4.8 |

## Reading

1. **The manipulation check passes decisively** — the bomb arm moves the downstream
   Bombness readout by −18.7 (necessity) / +18.9 (sufficiency), while the
   norm-matched random arm moves it by −0.16 / +0.65. The intervention genuinely
   and *specifically* changes the Bombness representation. This is not a failed
   manipulation.

2. **Yet behavior does not follow.** The bomb ΔASR is +0.048 in both directions —
   statistically indistinguishable from zero and from the random control (CI
   [−0.048, +0.143] both ways), and its upper bound is far below the known refusal
   lever (Phase-4 refusal ablation +0.24 / 2×2 refusal main effect +0.36). A potent,
   specific manipulation of Bombness has no behavioral consequence.

3. **The remainder carries no behavioral signal either** (ΔASR 0.000 / −0.024), so
   the ~80 % example-specific remainder energy (decomposition §Result) is not a
   hidden behavioral lever the mean direction missed. And the refusal-component arm
   is inert *by construction* here (the codeword-Δh has ~no refusal energy — E36),
   consistent with refusal being written downstream of the codeword.

4. **This is the strongest form of the epiphenomenality result.** Phase 4 ablated
   the mean Bombness direction; Phase 5 installs/removes each example's *own*
   component and still finds nothing. Representation ≠ behavior for Bombness holds
   under per-example causal surgery, with the manipulation check proving the
   representation was moved.

## Limitations

- n=42; nulls are CI bounds excluding the refusal-magnitude effect, not "exactly 0".
- Single cohort (clearharm), single band (L8–18), single donor (benign), Llama only.
- Necessity headroom is limited by base ASR 0.167; sufficiency (base 0.286, higher
  headroom) gives the same null, which is the more informative direction here.

## Reproduce

```
# vectors (CPU): python -m src.probes.build_phase5_perexample --run <extract> \
#   --v-bomb outputs/phase4_directions/v_bomb_clearharm.pt \
#   --refusal outputs/stage_gcg_full/refusal_direction_llama_L18.pt --donor benign \
#   --out outputs/phase5_perexample/comp_clearharm_benign.pt
# necessity : sbatch --constraint=l40s --export=ALL,MODE=full,OBJECTIVE=necessity  run_phase5_component.slurm
# sufficiency: sbatch --constraint=l40s --export=ALL,MODE=full,OBJECTIVE=sufficiency run_phase5_component.slurm
```
