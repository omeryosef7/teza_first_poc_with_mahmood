# GCG Refusal-Direction Objective Audit (Phase 6)

Traced directly from `poc_stage_gcg_early/objectives.py`, `poc_stage_gcg_early/gcg_optimizer.py`, and each run's `CONFIG.json`/`ITERATION_LOG.jsonl`. Source-of-truth rows: `6A_Q_refusal_dir`, `6A_G_refusal_dir`, `6B_gemma4_cot_target`, `6C_cot_refusal` in `outputs/stage_gcg_full/GCG_PHASE4_7_SOURCE_OF_TRUTH.csv`.

## 1. What each Phase-6 run actually is (corrects any doc implying 6A and 6C share a target)

| Run | Model | Manifest (target) | `lambda_refusal_dir` | Uses CoT-prefix target? |
|---|---|---|---|---|
| 6A-Q | Qwen3-14B | `advbench_manifest_v1.jsonl` — **standard** `"Sure, here is..."` target | 1.0 | **No** |
| 6A-G | Gemma4-E4B | `advbench_manifest_v1.jsonl` — **standard** target | 1.0 | **No** |
| 6B | Gemma4-E4B | `advbench_gemma4_cot_manifest.jsonl` — CoT-channel-aligned target | **0.0** | Yes, but **no refusal-dir term at all** |
| 6C | Qwen3-14B | `advbench_cot_target_manifest.jsonl` — same CoT-prefix target as 5A/5B/5C | 1.0 | **Yes** |

**Correction:** 6A-Q does *not* use CoT-prefix targeting — it is the standard target + refusal-direction suppression, run to test whether the refusal-direction mechanism alone (independent of the CoT-target fix) can lift Qwen3's ASR. 6C is the one that *combines* CoT-prefix targeting with refusal-direction suppression. Any doc/slide implying both are "CoT-prefix + refusal-direction" is wrong for 6A-Q specifically. 6B tests the CoT-aligned target on Gemma4 with **no** refusal-direction objective (`lambda_refusal_dir=0.0`, `refusal_dir_path=null`) — it is not a refusal-direction experiment at all, despite living in the "Phase 6" family; it belongs with 5A/5B/5C conceptually (CoT-target fix), just on Gemma4.

## 2. Composite loss definition, and a load-bearing methodological finding

From `objectives.py::composite_loss` (used for **candidate scoring/selection** in `gcg_optimizer.py::_evaluate_candidates`):

```
total_loss = task_loss + lambda_repr * repr_loss + lambda_kl * kl_loss + reg_loss + fluency_penalty_weight * fluency_loss
```

**`refusal_dir_loss` is never in this sum.** It is added only inside the *gradient* computation (`gcg_optimizer.py::_token_gradients`, line ~188: `loss = loss + lambda_refusal_dir * rd_loss`), which determines which token substitutions get *proposed* as candidates each step (via `_sample_control`). The actual *selection* among those proposed candidates — i.e., which one becomes the accepted suffix for the next step — is done by `_evaluate_candidates`, which calls `composite_loss()` **without any refusal-direction term**.

**Consequence:** for 6A-Q/6A-G/6C, the refusal-direction objective shapes *which candidate tokens are proposed* via the gradient, but has **zero direct influence on which proposed candidate is accepted** each step. The accepted suffix at every step is whichever sampled candidate has lowest task_loss (+ repr_loss, which is 0 for all Phase-6 runs since `lambda_repr=0.0` throughout). The `refusal_dir_loss` values reported in `ITERATION_LOG.jsonl` and below are therefore a **side-effect of gradient-guided proposal**, not a directly co-optimized selection criterion — this is a more precise (and weaker) claim than "GCG jointly optimizes task success and refusal-direction suppression."

Separately: the logged `refusal_dir_loss` itself (in `ITERATION_LOG.jsonl`, and the post-selection evaluation at `gcg_optimizer.py:800-825`) is computed **only on `train_tasks[0]`** — a single representative behavior from the training manifest, not averaged across all 20/25 training behaviors the way `task_loss` is (task_loss is summed across all `train_tasks` at `gcg_optimizer.py:584-596`). So the refusal_dir_loss trajectory reported per run is a single-behavior proxy, not a benchmark-level measurement.

## 3. Task-loss vs refusal_dir_loss trajectories (from `ITERATION_LOG.jsonl`, deduplicated by step)

| Run | task_loss step0 → best (step) | refusal_dir_loss step0 → best/final |
|---|---|---|
| 6A-Q | 30.11 → **12.03** (step 496) | 0.0864 → **-0.0737** (steps 496-499, flat) |
| 6A-G | 49.67 → **6.79** (step 215, true dedup best — see §4) | not directly comparable across models (different `d_model`); direction sign follows same convention |
| 6C | 48.17 → **25.64** (step 443) | starts positive, ends **-0.115** |
| 6B (no refusal-dir) | 48.69 → 26.96 (step 229; best ≠ final here, run regressed after) | n/a (`lambda_refusal_dir=0.0`, not tracked as an objective) |

Reference for comparison (no refusal-dir, same target manifests): 5A/5C (Qwen3, CoT-target, no refusal-dir) best task_loss = 20.52; standard-target no-refusal-dir baseline (`gcg_full_qwen3_weighted`) best task_loss = 7.97.

**Optimizer successfully drives the (single-behavior) refusal-direction projection negative in both 6A-Q and 6C** (0.086 → -0.074 and roughly similar sign flip for 6C), consistent with the suffix pushing that one behavior's activations away from the refusal subspace. This part of the intended mechanism worked as designed.

## 4. The "507 steps" bug (6A-G)

`gcg_full_gemma4_6a_refusal_dir/RESULTS_SUMMARY.md` states "Steps completed: 507," but `CONFIG.json` specifies `n_steps: 500`. Direct inspection of `ITERATION_LOG.jsonl`: 507 raw lines, but only **500 distinct `step` values** (0-499) — steps 310-316 are each logged twice, consistent with a SLURM job restart that re-logged a handful of already-completed steps before continuing past its prior furthest point. "507" is `len(file)`, not `max(step)+1`. Using the deduplicated log (last-occurrence-wins for duplicate steps), the true best task_loss is **6.79 at (deduplicated) step 215** — not materially different from what a naive first-occurrence reading would give, since the duplicated region (310-316) is well after the actual minimum, but the "507 steps" framing itself should not be read as "this run exceeded its configured budget."

## 5. Behavioral outcome (from `outputs/stage_gcg_full/GCG_PHASE4_7_SOURCE_OF_TRUTH.csv`)

| Run | Optimized-condition ASR (dev seeds) | Baseline (task_only) ASR |
|---|---|---|
| 6A-Q | 0.0% (0/75) | ~2.7% |
| 6A-G | 1.3% (1/75) | 0.0% |
| 6B | 0.0% (0/75) | 0.0% |
| 6C | 0.0% (0/75) | ~2.7% |
| *(reference) 5A CoT-target, no refusal-dir* | 10.7% (8/75) | ~2.7% |

**Supported claim (as of the original 2026-07-13 audit, now SUPERSEDED — see §6 update below):** under the tested token-space objective (refusal-direction loss folded into the gradient but not the selection criterion, evaluated only on a single representative behavior, layer 25, one fixed token position, **one lambda value (1.0)**, one optimization seed), adding refusal-direction suppression to either the standard target (6A-Q) or the CoT-prefix target (6C) **eliminated ASR** relative to their respective no-refusal-dir counterparts (task_only baseline and 5A respectively), despite the optimizer successfully reducing the measured (single-behavior) refusal-direction projection.

**Not supported by this evidence and should not be claimed:** "the objectives are fundamentally incompatible" (this is one lambda, one layer, one token position, one optimization seed — a broader incompatibility claim would need the sweep described in §6, which has now been run — see the update below); "refusal-direction suppression definitively triggers alternative safety pathways" (no mechanistic evidence collected here that isolates *why* ASR dropped, only that it did).

## 6. Layer/lambda sweep — RUN (2026-07-13, Sprint 2 / Phase 8) — the "eliminates ASR" claim was lambda-specific, not general

The layer/lambda sweep flagged as unresolved future work below was executed same-day as a follow-up (`docs/GCG_PHASE8_REFUSAL_DIR_SWEEP_LOG.md`, full detail and raw job IDs there). **Result: the effect is strongly lambda-dependent, not a general incompatibility.**

| Configuration | Optimized ASR | vs. neutral |
|---|---|---|
| layer=25, λ=1.0 (original 6C) | 0% (0/75) | 0%, net-negative |
| layer=20, λ=1.0 | 5.33% (4/75) | +1.3pp |
| layer=30, λ=1.0 | 0% (0/75) | −4.0pp (net-neg) |
| **layer=25, λ=0.3** | **24.0% (18/75)** | **+21.3pp** |
| layer=25, λ=3.0 | 2.67% (2/75) | −1.3pp (net-neg) |

**At the originally-tested λ=1.0 (any of the 3 layers tried) or at λ=3.0, the CoT-prefix ASR gain stays eliminated or negligible — consistent with the original 6C finding.** But **at a weaker λ=0.3, same layer 25, ASR jumps to 24.0% — more than double the no-refusal-dir 5A/6C reference's 10.7%.**

**Corrected claim, superseding the "eliminated ASR" line above**: under the tested token-space objective, refusal-direction suppression's effect on the CoT-prefix ASR gain is **lambda-dependent** — strong suppression (λ≥1.0) eliminates or reverses it, while weak suppression (λ=0.3) at the same layer can substantially *amplify* it. "The two objectives are incompatible" is now demonstrably false as a general statement; it only holds in the strong-lambda regime tested originally.

### 6.1 Seed-robustness follow-up (Sprint 2, 2026-07-14)

The λ=0.3 result above was flagged as single-seed and not yet replicated. Ran the identical recipe (layer=25, λ=0.3, CoT-prefix target) at a second optimization seed (43) — full pipeline, jobs 660927/661079/661357, see `docs/GCG_SPRINT2_PLAN_AND_PROGRESS.md` for raw job IDs/timing.

| Seed | Optimized ASR | Neutral control | vs. neutral |
|---|---|---|---|
| 42 (original) | 24.0% (18/75) | ~0% | +21.3pp |
| 43 (replication) | 12.0% (9/75) | 4.0% (3/75) | +8.0pp |

**Replicates directionally, not in exact magnitude.** Both seeds show a clear, real uplift over their own neutral-control baseline, and both meet-or-exceed the no-refusal-dir 10.7% reference — this is not a single-seed fluke. But the magnitude differs by roughly 2x between seeds (24.0% vs. 12.0%), consistent with this project's already-documented seed-variance issue (Finding 6 in `GCG_FINDINGS_SYNTHESIS.md`: up to 11x ASR swings between nearly-tied-loss seeds on unrelated runs) rather than evidence against the effect. **Corrected framing**: report λ=0.3's effect as a range (12-24% ASR across 2 tested seeds), not a single point estimate. A 3rd seed would further tighten this estimate if pursued.

Nearby layers around 25 (tried: 20, 30 — both still λ=1.0, layer alone did not recover ASR the way weaker lambda did), multiple lambda_refusal_dir values (tried: 0.3, 3.0), 2 optimization seeds at λ=0.3 — done. **Still not done**: multiple token positions, a 3rd seed at λ=0.3 (would further tighten the 12-24% range), and the same sweep for 6A-Q (standard target, not CoT-prefix) or for Gemma4.
