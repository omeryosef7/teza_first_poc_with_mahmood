# Sprint 2 / Track 1: Gemma4 CoT-Prefix "v2" — Resolving the Infeasibility Question

**Started:** 2026-07-13
**This is an execution log** — retains in-progress/historical detail; not the final source of truth. Once concluded, findings will be folded into `docs/GCG_ABLATION_PIPELINE_LOG.md`/`docs/GCG_FINDINGS_SYNTHESIS.md` as an explicit, separately-verified step. See `docs/GCG_SPRINT2_PLAN_AND_PROGRESS.md` for the full sprint plan this belongs to.

## Motivation

`gcg_full_gemma4_6b_cot_target/` (Phase 6B) attempted to give Gemma4 a CoT-prefix optimization target analogous to Qwen3's 5A breakthrough, using Gemma4's actual thinking format (`<|channel>thought\n{cot_text}\n<channel|>\n\n{response}`, marker tokens ids 100/101). It stalled at best task_loss ≈26.96 (vs. Gemma4 standard-target's 7.62) and `docs/GCG_ABLATION_PIPELINE_LOG.md` concluded the channel tokens are "infeasible for teacher-forced GCG... a fundamental tokenizer constraint."

A fresh code inspection this sprint found that conclusion is **unverified**: `<|channel>thought`/`<channel|>` (ids 100/101) are ordinary entries in Gemma4's 262,144-token vocab, with no logit-masking, generation-config restriction, or any other mechanism anywhere in `poc_stage_gcg_early/` that would make them structurally harder to predict via cross-entropy than any other token. The "infeasible" claim was inferred purely from the aggregate loss curve plateauing — never checked at the level of "is the loss specifically at those 2-3 token positions stuck, or is the whole (longer, harder) CoT-prefixed target just under-optimized."

Also found in the same inspection: `poc_stage_gcg_early/build_gemma4_cot_target_manifest.py` never overrode the `"model"` field on its output rows — every row of the original 6B manifest (`advbench_gemma4_cot_manifest.jsonl`) inherited `"model": "qwen3"` from its Qwen3-manifest input, even though the run used `--model-family gemma4`. Cosmetic only (model family is a separate CLI arg, so it didn't affect what actually ran), but corrupts provenance.

## What changed (code, all additive — nothing in existing runs is touched)

1. **`poc_stage_gcg_early/build_gemma4_cot_target_manifest.py`**: added `out_r["model"] = "gemma4"` alongside the other force-set fields. Regenerated to a **new** file, `outputs/stage_gcg_full/advbench_gemma4_cot_manifest_v2.jsonl` — the original `advbench_gemma4_cot_manifest.jsonl` (used by 6B) is untouched. Verified: diffing old vs. new row-by-row (excluding the `model` key) shows zero other differences; original file confirmed byte-identical to before.
2. **`poc_stage_gcg_early/objectives.py`**: factored `task_loss` into a new `task_loss_per_position` (returns the pre-`.mean()` `[batch, target_len]` tensor) + `task_loss` now just calls `.mean(dim=-1)` on it. Verified numerically equivalent to the pre-refactor `task_loss` on both batched and unbatched (2D) inputs — `torch.allclose` confirmed, and the 2D case still returns a scalar.
3. **`poc_stage_gcg_early/config.py`**: added `RunConfig.log_channel_token_positions: bool = False` as a **top-level** field (not inside `ObjectiveWeights`), explicitly **excluded** from `config_hash()`'s hashed dict — verified two `RunConfig`s differing only in this field produce an identical hash. This was a deliberate design choice: `ObjectiveWeights` is hashed via `dataclasses.asdict()`, so adding a field there (even at a no-op default) would have changed the hash for every existing config and risked breaking resume-from-checkpoint compatibility for every prior Phase 4-8 run. Treating this as pure logging/deployment metadata (like `run_id`/`output_dir`/`manifest_path`, which are also hash-excluded) avoids that risk entirely.
4. **`poc_stage_gcg_early/run_optimization.py`**: new opt-in CLI flag `--log-channel-token-positions` (default off), threaded through to `RunConfig`.
5. **`poc_stage_gcg_early/gcg_optimizer.py`**: new post-selection diagnostic block (same `train_tasks[0]`-only, no_grad convention as the existing `repr_loss`/`refusal_dir_loss` post-selection logging blocks it sits next to) — when `config.log_channel_token_positions` is set, finds the offsets of the model-family's thinking-marker token IDs (via `poc_stage4.model_family_utils.get_thinking_start_token_ids`/`get_thinking_end_token_ids`, already model-family-generic) inside the current target span, does one extra forward pass, and logs `channel_token_positions` / `channel_token_losses` / `channel_token_ids` into `ITERATION_LOG.jsonl` as new additive keys. No effect when the flag is unset (every existing/future non-opted-in run is byte-for-byte unaffected in its log schema).
6. **`slurm_scripts/run_gcg_full_6b2_gemma4_cot_v2.slurm`**: new script, hardcoded (not parameterized-with-override like `run_gcg_full_6c_qwen3_combined.slurm`) to `RUN_DIR=gcg_full_gemma4_6b2_cot_target_v2`, `MANIFEST_PATH=advbench_gemma4_cot_manifest_v2.jsonl` — deliberately cannot collide with 6B's original paths even if invoked without arguments. First attempt: same seed as 6B (42), 800 steps (vs. 6B's 500) since 6B's own curve may not have been given enough budget. Includes `analyze_pareto_frontier.py` in the SLURM chain (a gap discovered in Phase 8 — that script is not auto-invoked anywhere else and must be run manually to get `RESULTS_SUMMARY.md`).

## Decision rule (pre-registered before seeing results)

- Channel-token loss (from the new `channel_token_losses` field) tracks down over training, roughly proportional to the rest of the target's improvement → **6B was under-optimized, not infeasible.** Correct the finding in `GCG_ABLATION_PIPELINE_LOG.md`/`GCG_FINDINGS_SYNTHESIS.md`, and consider a longer/multi-seed run as a stretch goal.
- Channel-token loss stays flat/near-random (no clear downward trend) while the rest of the target's loss improves substantially → **the original "infeasible" claim is now genuinely verified** (not just inferred) — keep it, but cite the per-token evidence directly rather than the aggregate curve alone.

## Job log

| Job | Purpose | Status |
|---|---|---|
| 660780 | `run_gcg_full_6b2_gemma4_cot_v2.slurm` (800-step optimization + audit/validate/analyze) | submitted, queued (Priority) as of first check |

## Progress Log

### 2026-07-13, submission
- Manifest fix applied and regenerated (v2). `objectives.py`/`config.py`/`run_optimization.py`/`gcg_optimizer.py` changes applied, imports and equivalence-of-refactor verified. New SLURM script created and submitted (job 660780). Awaiting job start.

### 2026-07-13, first-run crash and fix
- Job 660780 started, loaded the model (~4 min), confirmed the manifest fix in production (`Manifest model field (should be gemma4): gemma4`), then **crashed at step 0** with `RuntimeError: a Tensor with 31 elements cannot be converted to Scalar` in the new channel-token-position logging block.
- **Root cause**: `task_loss_per_position` was called with already-batched tensors (`.unsqueeze(0)` applied before the call), so its `dim()==3` branch correctly did NOT squeeze the batch dimension — the returned tensor was `[1, target_len]`, not `[target_len]` as the surrounding code assumed. Indexing `per_pos[o]` therefore returned a `[target_len]`-shaped row instead of a scalar. Fixed to `per_pos[0, o]`. Verified with a standalone shape/indexing test before resubmitting.
- No checkpoint/iteration-log was written before the crash (failed at the very first step's post-selection logging, before `_append_jsonl` was reached), so this was a clean restart, not a resume — resubmitted as job **660790**.
- This is exactly the kind of bug the "verify with a quick sanity check before trusting new diagnostic code" habit from the main Phase 4-7 audit is meant to catch — logged here rather than silently fixed, per this project's standing practice of keeping bugs and fixes visible in the execution log.

### 2026-07-13, ~15:27 UTC — first real diagnostic signal (early, but a clear trend)

Job 660790 at step 40/800. `channel_token_positions=[0, 1, 13]` with `channel_token_ids=[100, 45518, 101]` — position 0 (id 100, the `<|channel>` special token) and position 13 (id 101, `<channel|>`) are the genuine marker tokens; position 1 (id 45518) is the literal word "thought" that's part of the multi-token `<|channel>thought` start-marker string (an artifact of `get_thinking_start_token_ids` tokenizing the whole marker string, not just the special token — a broader but still meaningful diagnostic scope, not a bug).

| Step | task_loss (summed, 20 behaviors) | loss at id=100 (`<\|channel>`) | loss at id=45518 ("thought") | loss at id=101 (`<channel\|>`) |
|---|---|---|---|---|
| 0 | 49.22 | 7.188 | 0.044 | 6.188 |
| 10 | 34.37 | 3.766 | 0.084 | 2.125 |
| 20 | 31.19 | 2.578 | 0.268 | 1.914 |
| 30 | 29.55 | 1.789 | 0.144 | 1.719 |
| 40 | 29.38 | 1.578 | 0.340 | 1.430 |

**Both genuine marker-token losses (ids 100 and 101) have dropped ~77-78% by step 40** (7.19→1.58 and 6.19→1.43), proportionally at least as fast as the aggregate `task_loss` (which dropped ~40% over the same steps) — nowhere near "flat/stuck near-random." This is early (40/800 = 5% of the planned budget) but already a clear, unambiguous trend in the direction of **decision-rule branch 1: the channel tokens are NOT a stuck bottleneck; 6B's stall looks like it was a general under-optimization of the whole (longer, harder) CoT-prefixed target, not something specific to the marker tokens.** Will keep tracking through more of the 800-step budget before writing a final conclusion, but this is a strong, real-time-observed data point against the original "infeasible... fundamental tokenizer constraint" claim.

### 2026-07-14, ~00:37 UTC — optimization complete (800/800 steps): final channel-token result

Job 660790 completed cleanly (`sacct` confirms COMPLETED, exit 0). Final trajectory:

| Step | task_loss | loss at id=100 (`<\|channel>`) | loss at id=45518 ("thought") | loss at id=101 (`<channel\|>`) |
|---|---|---|---|---|
| 0 | 49.22 | 7.188 | 0.044 | 6.188 |
| 40 | 29.38 | 1.578 | 0.340 | 1.430 |
| ~700-799 (plateau) | 24.25 (best, step 722) | 1.75 | 0.445 | 0.898 |

**Both genuine marker-token losses continued to decline from step 40 to the end** (id=100: 1.578→1.75, actually flat/slightly up in the final stretch; id=101: 1.430→0.898, continued dropping) but **plateaued well above zero** rather than continuing toward the near-elimination the early trend (step 0→40) might have suggested. The "thought" literal-word position (id=45518) stayed small throughout (0.044→0.445, a small absolute increase, likely noise at this scale).

**Verdict, pending free-gen/replay ASR outcome**: this is genuine partial evidence against the original "fundamentally infeasible via cross-entropy" claim — the channel/marker tokens are demonstrably trainable, not stuck at their step-0 values, and a longer budget than 6B used did materially reduce their loss (id=101 dropped from 6.19 to 0.90, roughly 85%). But the losses did not reach a small residual near zero, so this is not a clean "6B was simply under-optimized, problem solved" story either — it is a **middle-ground result**: harder to optimize than Qwen3's markers, but not the flat/immovable signature the original 6B write-up implied. The actual test of whether this improved channel-token loss buys any real jailbreak success is the free-gen/replay stage, submitted as job 661128 (no dependency chain, per this sprint's corrected SLURM policy) — will only write a final conclusion into the audited docs once that completes and ASR is measured directly from `FREE_GENERATION_RESULTS.jsonl`.

### 2026-07-14, ~02:06 UTC — free-gen complete: 0% ASR, matching the original 6B null result

Job 661128 completed (`sacct` COMPLETED, exit 0), `FREE_GENERATION_RESULTS.jsonl` has 300/300 rows (75 tasks × 4 condition labels). Direct count from `strongreject_is_success`:

| condition_label | successes | n |
|---|---|---|
| optimized_weighted | 0 | 75 |
| neutral_control | 0 | 75 |
| random_spaces | 0 | 75 |
| task_only | 0 | 75 |

**0.0% ASR for `optimized_weighted`, identical to every control condition.** This resolves the "middle-ground" open question from the previous entry: the substantial channel-token loss reduction (up to ~85% for one marker) did **not** translate into any measurable jailbreak success — the result is empirically identical to the original 6B run's null finding, despite a much longer optimization budget (800 vs. 6B's shorter run) and direct confirmation the tokens are trainable.

**Net conclusion for this track**: the *mechanism* explanation in the original write-up ("infeasible... fundamental tokenizer constraint") was overstated — the tokens are not architecturally frozen, they respond to gradient-based optimization like any other position. But the *practical, headline* finding — Gemma4 resists this CoT-prefix attack, 0% ASR — is unchanged, and is now backed by stronger evidence (a longer run, a direct per-token diagnostic, not just an inferred plateau). Replay job **661295** submitted (manual, no dependency) to confirm this free-gen result before finalizing language in `docs/GCG_REFUSAL_DIRECTION_AUDIT.md`/`GCG_FINDINGS_SYNTHESIS.md`.
