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
- Grenade + chlorine running (695836/695837) — tests whether this depth-gradient generalizes representationally even though the *behavioral* TOCTOU did not (S4 #6).

## T2 — Forced-choice patchscope — RUNNING (695813). Check `positive_control_ok` before citing.
## T4 — Attribution-patching map — RUNNING (695814). Report AtP-vs-true correlation + `trustworthy` before citing.
