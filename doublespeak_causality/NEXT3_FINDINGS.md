# NEXT3 — Findings (executing the 4 deferred levers)

Plan: `NEXT3_PLAN.md`. Env: Llama-3.1-8B / Qwen3-14B, L40S, poc_stage2, forced_choice. Honest — negatives included.

## NEXT3 SUMMARY (2026-07-31)
Executed the 4 deferred high-value levers with new techniques. **Two clear wins, one nuanced win that explains a prior negative, one honest negative that reinforces the headline.**
- **T1 cross-architecture ✅ (the big one):** the context-carried dissociation **replicates on Qwen3-14B** (IE_state≈0 equiv; DE_context +0.70 ≈92% of TE; faithfulness 0.0) — the primary claim is no longer single-model Llama. Required a thinking-aware readout (`enable_thinking=false`) + a `--model` threading fix. DeepSeek-R1 deferred (hardcoded `<think>` → needs `--answer-marker`).
- **T4 attribution patching ✅ (validated new technique):** AtP tracks true patching (pearson 0.89) and localizes the DS-context effect to the **earliest layers + demonstration-codeword positions** — refines S3's "distributed."
- **T3 representational TOCTOU ◐ (nuanced):** the refusal check is depth-gated concept-specifically for all 3 pairs, but at a **pair-dependent depth** (bomb early, grenade/chlorine mid) — which **explains** why the behavioral TOCTOU (#6) only generalized to bomb.
- **T2 forced-choice patchscope ✗ (honest negative that helps):** fails its positive control (a clean DIRECT bomb rep won't decode) — consistent with IE_state=0 (the concept isn't locally in the rep); a second line of evidence via the paper's own readout family.

Bugs caught+fixed mid-flight: bench-path prefix (ds_run cd), `--model` not threaded to 34 (cross-arch), output-dir globs.

---

## T1 — Cross-architecture (Qwen3-14B): the readout now WORKS with a thinking-aware template. **[partial success]**
The Qwen3 gate FAILED in NEXT2 because the next-token readout fired inside `<think>`. Threading `--enable-thinking false` through 31/32/34/44 (verified it injects an empty `<think></think>` and suppresses thinking) fixes it:
- **Qwen3 readout gate PASSES** (job 695749/695832): `DS−Neutral reads_as_concept = +0.7576` [+0.65,+0.85], `DS−Neutral p_concept = +0.6322` [+0.54,+0.73], n=66 — i.e. **the Doublespeak hijack is present on Qwen3, even STRONGER than on Llama (+0.31)**. This alone lifts the *attack* off single-model Llama.
- **The full dissociation REPLICATES on Qwen3-14B** (job 695832, after fixing a latent bug where the slurm never passed `--model` to `34`): 2×3 (mid) — Neutral receiver 0.00 for all sources (h_N/h_DS/h_Direct), DS receiver **0.70 / 0.77 / 0.70**. `IE_state ≈ 0` (equivalence, every window); `DE_context = +0.703` [0.551, 0.846] (mid), +0.774 (early), +0.748 (late) ≈ **92% of TE (+0.765)**; self-transplant faithfulness exactly **0.0**. Same structure as Llama, stronger hijack (DS ~0.7 vs Llama ~0.35). → **the context-carried, local-state-inert dissociation is cross-architecture** (Qwen3-14B, a different family and size), not a Llama artifact.
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
