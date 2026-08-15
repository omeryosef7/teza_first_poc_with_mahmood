# PHASE 5 — Donor-shift energy decomposition (representational precondition)

Plan §9. **Zero-GPU / zero-generation** first slice of component-restricted
patching: before spending GPU on component patch-and-generate runs (Q3/Q4), we
partition the donor activation shift itself and ask *how much of it even lives
along the Bombness and refusal axes*. Computed entirely from artifacts already on
disk (`acts.npy`, `v_bomb_clearharm.pt`, `refusal_direction_llama_L18.pt`);
scalar-only.

**Model / run:** Llama-3.1-8B-Instruct, extraction `757886`, clearharm cohort,
`resid_post` (D1). 170 complete (doublespeak, benign, neutral) triples.
**Method:** for each matched triple, Δh(L) = h_doublespeak(L) − h_donor(L) at the
**codeword** position. Partition ‖Δh‖² into the component along per-layer
`v_bomb[L]`, the component along the (fixed L18) refusal direction, and the
orthogonal remainder. Because v_bomb ⟂ refusal only approximately (§4), the
plane/remainder split uses an orthonormalised QR basis of span(v_bomb, refusal).

**Index-alignment guard (B9 class).** The analysis recomputes the benign-donor
diff-of-means from `acts` and checks it against stored `v_bomb`: **cos = 1.000 at
every layer**, confirming the acts layer axis is aligned with the v_bomb keys.
The guard also correctly *rejected* an invalid configuration — applying the
codeword-built `v_bomb` at the `final_prompt` position (cos → 0.004–0.18), which
is why only the `codeword_last` decomposition (where v_bomb is defined) is
reported.

## Result (codeword position, mean energy fraction per band)

**Bombness contrast — donor = benign** (same codeword, harmful vs benign binding):

| band | frac along v_bomb | frac along refusal | orthogonal remainder | cos(Δh, v_bomb) | cos(Δh, refusal) |
| --- | --- | --- | --- | --- | --- |
| concept-write L8–11 | **0.216** | 0.002 | 0.784 | +0.44 | +0.03 |
| refusal-onset L13–18 | 0.174 | 0.005 | 0.824 | +0.40 | +0.05 |
| decision L18–22 | 0.133 | 0.003 | 0.865 | +0.35 | +0.03 |

**donor = neutral** (neutral→doublespeak shift):

| band | frac along v_bomb | frac along refusal | orthogonal remainder |
| --- | --- | --- | --- |
| concept-write L8–11 | 0.142 | 0.003 | 0.856 |
| refusal-onset L13–18 | 0.143 | 0.011 | 0.853 |
| decision L18–22 | 0.098 | 0.009 | 0.897 |

## Reading

1. **The refusal axis carries essentially zero energy in the codeword-position
   donor shift** (frac_refusal ≤ 0.011, cos ≤ 0.10 in every band, both donors).
   This upgrades the §4 *direction* orthogonality (cos ≈ 0.09) to an *energy*
   statement about the actual shift: at the codeword, the doublespeak binding is
   installed with no measurable movement along refusal. Consistent with refusal
   being a *downstream/decision-region* variable, not something written at the
   codeword — exactly why refusal, not Bombness, is the behavioral lever.

2. **`v_bomb` is a coherent but minority summary of the shift** — it captures
   ~14–22 % of ‖Δh‖² at the concept-write band, falling toward the decision
   region; ~80 % is orthogonal remainder (codeword/topic-specific content).
   So the Bombness direction is the dominant *named* axis of the codeword shift
   but not the bulk of it — which is why whole-Δh patching and pure `v_bomb`
   patching are not interchangeable, and why a component decomposition (this
   phase) is the right lens rather than another generic residual patch.

3. **Q1/Q2 precondition met, honestly bounded.** Among the two named axes, the
   Bombness component dominates the codeword-position `p_concept`-relevant shift
   and the refusal component is absent there. This is a statement about
   *representation energy*, **not** behavioral mediation (Q3) — that still
   requires the GPU component-patch-and-generate runs. It is fully consistent
   with the established headline (Bombness decodable & refusal-orthogonal at the
   codeword, yet behaviorally epiphenomenal; refusal — which lives downstream — is
   the causal lever).

## Cross-family (zero-GPU, same method on existing artifacts)

Same decomposition re-run on Phi-4-mini-reasoning (extraction 758022,
`refusal_phi/…L18`) and Qwen3-14B (758030, `refusal_qwen3/…L24`), 170 triples each,
benign donor, codeword position. Index guard cos=1.000 every layer for both (the
module adapted to Qwen's 40-layer stack automatically).

| model | frac v_bomb L8–11 | frac v_bomb L18–22 | **frac refusal (max over bands)** | cos refusal (max) |
| --- | --- | --- | --- | --- |
| Llama-3.1-8B | 0.216 | 0.133 | 0.005 | 0.05 |
| Phi-4-mini | 0.190 | 0.075 | **0.0004** | 0.009 |
| Qwen3-14B | 0.167 | 0.253 | **0.0017** | 0.032 |

**Invariant:** the refusal axis carries ~zero energy in the codeword-position donor
shift in **all three families** (frac ≤ 0.002, cos ≤ 0.05 everywhere). The
"refusal is written downstream, not at the codeword" geometry is family-invariant —
the same mechanistic-invariance signature seen for the representation itself
(§9 synthesis).

**Honest nuance:** the *Bombness* share is not identical across families. In Llama
and Phi `v_bomb`'s energy fraction **falls** with depth (0.22→0.13, 0.19→0.07),
whereas in Qwen it **rises** (0.17→0.25). So the Bombness direction becomes a
larger part of the shift deeper in Qwen — a genuine cross-family difference in the
*concept* axis, on top of the invariant refusal-absence. (Bands are absolute layer
indices; depth is not normalized across the 32- vs 40-layer stacks, so read the
trajectory qualitatively.)

## Scope clarification — the mean-field behavioral Q3 is already Phase 4 (verified)

Before spending GPU on Q3/Q4 it is worth being precise about what is *new*. The
per-layer Bombness direction `v_bomb[L]` is built as the **unit mean diff-of-means**
`unit(mean_doublespeak − mean_benign)`. We verified numerically that the mean
full-shift direction equals `v_bomb` at **cos = 1.00000 at every band layer**
(L8/L11/L14/L18/L21).

Consequently a **mean-field** Q3 — "install the mean bomb component as a fixed
add-direction and measure ΔASR" — is *identical* to the Phase-4 **sufficiency**
arm (add `v_bomb`), which already ran and returned a **null** (ΔASR +0.05, manip
check confirmed). Likewise the mean "full-donor" add is the same fixed direction.
So a fixed-direction Q3/Q4 built on the existing harness would **re-run Phase 4**,
not add evidence.

The only behavioral content Phase 5 adds beyond Phase 4 is therefore **per-example
component patching**: for each example install *its own* Δh_bomb =
(Δhᵢ·v_bomb)·v_bomb (and Δh_refusal, Δh_remainder, complement, random) rather than
the population mean. That tests whether the ~80 % example-specific *remainder*
(§Result) or the per-example Bombness component carries behavioral signal the mean
direction misses. This requires a genuinely new harness capability — a patch keyed
per generation example — plus GPU. It is the honest, non-redundant next step.

## Behavioral half — DONE (see PHASE5_BEHAVIORAL.md)

The per-example component patch (arms {full, bomb, refusal, remainder, random},
necessity + sufficiency) was built, smoke-gated, and run on L40S (runs 758162 /
758163). **Result: behaviorally NULL.** The bomb arm moves the downstream Bombness
readout ±18–19 (strong, specific vs norm-matched random ≈ 0) yet ΔASR is +0.048 in
both directions (95% CI [−0.048, +0.143], indistinguishable from random and from 0,
upper bound far below the refusal lever). The ~80 % remainder carries no behavioral
signal either. Per-example causal surgery confirms Bombness is behaviorally
epiphenomenal — the sharpest form of Story A.

## Reproduce

```
python -m src.probes.phase5_decompose \
  --run outputs/probe_bombness_full_clearharm_20260814_150624_757886 \
  --v-bomb outputs/phase4_directions/v_bomb_clearharm.pt \
  --refusal outputs/stage_gcg_full/refusal_direction_llama_L18.pt \
  --donor benign --position codeword_last     # and --donor neutral
```
Outputs: `phase5_decompose_{benign,neutral}_codeword_last.json` in the run dir.
