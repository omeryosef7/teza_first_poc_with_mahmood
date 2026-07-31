# NEXT3 — Findings (executing the 4 deferred levers)

Plan: `NEXT3_PLAN.md`. Env: Llama-3.1-8B / Qwen3-14B, L40S, poc_stage2, forced_choice. Honest — negatives included.

## T1 — Cross-architecture (Qwen3-14B): the readout now WORKS with a thinking-aware template. **[partial success]**
The Qwen3 gate FAILED in NEXT2 because the next-token readout fired inside `<think>`. Threading `--enable-thinking false` through 31/32/34/44 (verified it injects an empty `<think></think>` and suppresses thinking) fixes it:
- **Qwen3 readout gate PASSES** (job 695749/695832): `DS−Neutral reads_as_concept = +0.7576` [+0.65,+0.85], `DS−Neutral p_concept = +0.6322` [+0.54,+0.73], n=66 — i.e. **the Doublespeak hijack is present on Qwen3, even STRONGER than on Llama (+0.31)**. This alone lifts the *attack* off single-model Llama.
- The transplant itself hit a latent bug (the slurm never passed `--model` to `34`, so it loaded Llama-32 against Qwen-40 reps → "layer mismatch"). Fixed (commit) and re-running (695832) — pending IE_state/DE_context on Qwen3.
- **DeepSeek-R1-Distill** hardcodes `<think>` in its template, so `enable_thinking=false` cannot suppress it; it needs the `31 --answer-marker '</think>'` path (deferred).

## T3 — Representational TOCTOU (refusal-direction projection by concept-install timing). **[bomb: strong; generalization pending]**
Forward-only (no generation): add `d_Direct` at an early/mid/late layer window on NEUTRAL prompts, read the projection onto `v_refusal` (L18) at the answer position. Bomb (job 695815, n=40):

| window | install_effect [CI] | install_above_random [CI] |
|---|---|---|
| **early** | **+1.79** [1.36, 2.24] | **+1.73** [1.29, 2.20] |
| mid | +0.62 [0.53, 0.71] | +0.60 [0.53, 0.67] |
| late | 0.0 (degenerate) | 0.0 |

- **early ≫ mid, concept-specific** (norm-matched random control: early +0.06 NS, mid +0.02 NS): the refusal direction responds far more to an EARLY-installed concept than a mid one — a *representational* version of the depth-gated check, with huge effect sizes and p=0.0005 (vs the noisy behavioral version).
- **Honest caveat:** `late = 0` is *mechanical*, not meaningful — the late window (layers >18) is causally after the L18 refusal readout, so it cannot affect it. The load-bearing comparison is **early vs mid** (both pre-readout), which is clean.
### T3 generalization (grenade + chlorine): the depth-gating is real for all 3 pairs, but the DOMINANT DEPTH is pair-dependent — and this EXPLAINS the behavioral negative.

| pair | install_above_random early | mid | dominant depth |
|---|---|---|---|
| **bomb** | **+1.79** [1.29,2.20] | +0.60 | EARLY |
| grenade | −0.19 [−0.44,+0.09] NS | **+0.57** [0.48,0.65] | MID |
| chlorine | −0.07 [−0.22,+0.09] NS | **+0.66** [0.59,0.74] | MID |

- For **all three** pairs a specific layer-window raises the refusal-direction projection concept-specifically (random control ~0) — so the refusal check *is* depth-gated in general. **But the depth it is gated at differs by pair**: bomb's check is at the earliest layers; grenade's and chlorine's are at mid layers (early install does ~nothing there).
- **This explains the behavioral #6 negative** (`STAGE4_TOCTOU_FINDINGS.md`): the behavioral TOCTOU tested *early*-vs-late timing and found early-specificity only for bomb. Now we see why — grenade/chlorine's refusal check sits at mid depth, so an *early* concept install doesn't engage it. The depth-gated-refusal phenomenon generalizes; the specific *early* gating is a bomb property.
- Honest scope: the "dominant depth" claim rests on the concept-specific window with CI-excluding-0; the pair-specific depth is a new, testable prediction (a behavioral TOCTOU using each pair's *own* dominant timing should recover the interaction — future work).

## T2 — Forced-choice patchscope: positive control FAILS again. **[honest negative that reinforces the main result]**
Job 695813: even a *forced binary* patchscope, layer-scanned, cannot decode the concept from an injected rep — the positive control (inject a clean DIRECT bomb rep, force bomb-vs-carrot) gives `pos_ctrl_max = 0.00014` (~3e-5 at every one of 32 layers), `positive_control_ok = False`. So neither the free-next-token (N3) nor the forced-choice patchscope can read "bomb" out of an injected codeword-position rep for this pair.
- **Interpretation:** this is *consistent with* the headline result — the concept is **not locally present in the codeword's residual state** (IE_state = 0). A rep that doesn't carry the concept locally cannot patchscope-decode as the concept, by construction. So T2 is a second, independent line of evidence for the local-state-inert half of the dissociation (via the paper's own readout family), rather than a failure. We still cannot *positively* replicate the paper's "CARROT→BOMB via Patchscopes" on bomb (the readout needs a non-suppressed concept or a different decoder), but the negative is informative.

## T4 — Attribution-patching map: VALIDATED, and it localizes the effect. **[NEW technique, success]**
Job 695814 (metric = logit_diff, clean = DOUBLESPEAK, corrupt = matched NEUTRAL). AtP-vs-true-patching on the top-k cells: **pearson 0.893, spearman 0.924 → trustworthy=True** (the gradient approximation faithfully tracks real activation patching here).
- **Where the DS context installs the reading:** **layer 0 dominates** (Σ|attribution| 108.7 at L0 vs 19.5 / 12.3 / 8.7 at L1/L2/L3, decaying), concentrated on the **demonstration-codeword token positions** (the four largest cells are L0 at positions 31/48/65/82 — the demo carrots) plus the query/readout region. The top cells were re-confirmed by *true* LayerPatch (that is the 0.89 correlation).
- **Refines S3:** the "distributed" context effect is not uniform — it is **concentrated in the earliest layers and on the demonstration codewords**, propagating upward. Consistent with N1 (the reading is then present at every depth) and T3 (the refusal check is most sensitive to the earliest representation).
