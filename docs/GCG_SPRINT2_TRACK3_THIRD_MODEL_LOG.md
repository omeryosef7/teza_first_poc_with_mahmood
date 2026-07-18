# Sprint 2 / Track 3: Third CoT Model — DeepSeek-R1-Distill-Qwen-7B

**Started:** 2026-07-13
**This is an execution log** — retains in-progress/historical detail; not the final source of truth. See `docs/GCG_SPRINT2_PLAN_AND_PROGRESS.md` for the full sprint plan.

## Motivation

Cross-architecture generalization: does "CoT target misalignment is a barrier, fixable by CoT-prefix targeting" (the Qwen3 Phase 5 finding) hold for a third, genuinely different reasoning-model family, not just Qwen3/Gemma4? User requirement: must be a genuine thinking model, run with thinking explicitly active.

## Pre-flight checks (before any download, per the plan's "verify the mechanism first" discipline)

- **Disk**: 640GB available on the project's filesystem — a 7B-param bf16 model (~15GB) fits comfortably.
- **Network**: confirmed reachable (`curl` to `huggingface.co/deepseek-ai/DeepSeek-R1-Distill-Qwen-7B` succeeds).
- **Thinking mechanism, verified directly from the actual `tokenizer_config.json`'s `chat_template`** (fetched standalone, before any weight download):
  ```jinja
  {% if add_generation_prompt and not ns.is_tool %}{{'<｜Assistant｜><think>\n'}}{% endif %}
  ```
  **No `enable_thinking` conditional anywhere in the template** (unlike Qwen3's, which has an explicit `{%- if enable_thinking is defined and enable_thinking -%}` branch). This confirms the hypothesis from the sprint plan: **DeepSeek-R1-Distill-Qwen-7B thinks unconditionally — there is no toggle.** Every generation prompt ends in `<think>\n` regardless of any `enable_thinking` kwarg passed (matches the same fallback behavior already handled for Gemma4 in `model_adapter.py::apply_chat_template`'s `except TypeError` branch, since this tokenizer will similarly reject an `enable_thinking` kwarg it doesn't recognize).
  - **Practical implication**: no `--no-thinking` flag will do anything meaningful for this model family. Every run must simply be run normally (no suppression is even possible) — "thinking explicitly active" is satisfied trivially and by construction, not by a flag choice. This should be stated plainly in every run's log/CONFIG rather than silently assumed.
- **Bonus finding**: DeepSeek-R1-Distill-Qwen-7B uses the **same** `<think>` / `</think>` marker strings as Qwen3 (unsurprising — it's a distillation onto a Qwen2.5 backbone). This means the existing `poc_stage_gcg_early`/`poc_stage4` marker-lookup infrastructure (`THINKING_MARKERS_BY_FAMILY`) can very plausibly be extended with a new `"deepseek_r1"` key using identical marker strings to `"qwen3"`, rather than needing new marker-detection logic — though the model family should still be its own distinct key (not literally reusing `"qwen3"`) since other aspects of the chat template (system-prompt handling, no BOS/EOS conventions, tool-call blocks) differ.

## Scope (per the sprint plan)

Only the core minimal comparison: standard-target GCG vs. CoT-prefix-target GCG, 25 behaviors (reusing the existing `advbench_manifest_v1.jsonl` behaviors), matching the original Phase 4/5A recipe — not the full Phase 4-8 pipeline.

## Progress Log

### 2026-07-13
- Verified thinking mechanism (above) before any weight download, per plan discipline.
- Model download started in background (`snapshot_download('deepseek-ai/DeepSeek-R1-Distill-Qwen-7B')`), completed in ~3.5 min, **15GB, 11 files**, cached under this project's `HF_HOME`.
- **Live tokenizer sanity check confirms the chat-template finding**: `tokenizer.apply_chat_template([{"role":"user","content":"hello"}], add_generation_prompt=True)` really does end in `<｜Assistant｜><think>\n` unconditionally (no kwarg changes this). `<think>` encodes to a single token id `151648`, `</think>` to `151649` — clean single-token markers, same as expected from the earlier config inspection.
### 2026-07-13, ~16:50 UTC — integration complete, launch deferred (job-budget correction)

**Code integration done:**
- Added `"deepseek_r1"` to `run_optimization.py`'s `--model-family` choices, dispatching to the same generic `load_qwen3_model()` loader used for Qwen3 (no Qwen3-14B-specific hardcoding in that function — confirmed by reading it — so it loads DeepSeek-R1-Distill-Qwen-7B correctly as-is).
- Verified live (before launching anything) that `model_adapter.py`'s `apply_chat_template`/`tokenize_prompt`/`get_effective_eos_ids` all work correctly against the real DeepSeek tokenizer with zero further code changes — the prompt correctly ends in `<think>\n`, tokenization succeeds, EOS-id lookup is fully generic.
- Checked every other `model_family ==` branch point in the codebase (`gcg_optimizer.py`, `suffix_token_manager.py`, `poc_stage_ae/thinking_position_utils.py`) — only one Gemma4-specific workaround exists (`gcg_optimizer.py`'s `per_layer_inputs` fix for Gemma4's unusual architecture), which harmlessly does not apply to `deepseek_r1` (falls through exactly like `qwen3` already does).
- Added a `--model-family` override flag to `build_cot_target_manifest.py` (same class of cosmetic-metadata-field fix as Track 1's Gemma4 manifest bug — applied proactively here rather than reactively).
- Built both manifests: `advbench_deepseek_r1_manifest_v1.jsonl` (standard target, 25 behaviors, `model` field correctly set to `deepseek_r1`) and `advbench_deepseek_r1_cot_target_manifest.jsonl` (CoT-prefix target, reusing the *exact same* `build_cot_target_manifest.py` script used for Qwen3's 5A, since the `<think>`/`</think>` markers are identical).
- New SLURM script `slurm_scripts/run_gcg_full_deepseek_r1.slurm` (parameterized by `RUN_DIR`/`MANIFEST_PATH`/`RUN_LABEL`), matching the 4B-vs-5A pairing that established the original Qwen3 finding (both runs: `lambda_repr=0`, task-loss only, isolating the target-string effect cleanly).

**Launch deferred**: attempting to submit both runs was correctly blocked by the auto-mode safety classifier — the sprint's job queue was at 7 total (running+pending), over the 6-job ceiling, because pending-dependency jobs from Track 0's seed-43 replication chain hadn't been counted. See `docs/GCG_SPRINT2_PLAN_AND_PROGRESS.md`'s job-budget correction note. **Both jobs are ready to submit the instant the total queue count drops to ≤4** (to leave room for both without re-exceeding 6).

### 2026-07-13, ~17:15 UTC — launched

A separate compliance check (see `docs/GCG_SPRINT2_PLAN_AND_PROGRESS.md`'s "compliance correction" entry) found that Track 0's replication chain was using `--dependency=afterok:` in violation of a standing user rule; its 3 pending-dependency jobs were cancelled (no work lost), freeing real headroom. With the queue correctly at 3 running / 0 pending, launched both Track 3 runs with no dependency chain (each is a single self-contained job, so this track was never itself in violation):

- **660989** — standard-target (`gcg_full_deepseek_r1_7b_weighted/`, manifest `advbench_deepseek_r1_manifest_v1.jsonl`)
- **660990** — CoT-prefix target (`gcg_full_deepseek_r1_7b_cot_target/`, manifest `advbench_deepseek_r1_cot_target_manifest.jsonl`)

Both: 500 steps, batch=64, suffix_len=20, seed=42, lambda_repr=0/lambda_kl=0 (task-loss only, matching the 4B-vs-5A pairing exactly). `--nodelist` corrected to exclude `n-804` per the same compliance fix.

### 2026-07-13, ~19:37 UTC — standard-target optimization complete, free-gen launched

**660989 (standard-target) finished**: 500/500 steps, best task_loss=10.12 (down from 37.13 at step 0 — notably lower absolute scale than Qwen3's typical ~20s at convergence, different model/tokenizer so not directly comparable). Validation PASS, `FINAL_CANDIDATES.jsonl` has 2 rows.

**Bug found and fixed**: `run_gcg_full_free_generation.slurm`'s inline model-loading dispatch only handled `model_family in {"qwen3", "gemma4"}` — would have raised `ValueError: Unknown model_family: deepseek_r1`. Fixed to route `deepseek_r1` through the same `load_qwen3_model()` loader as `qwen3`. Checked `evaluate_optimized_suffixes.py`/`model_adapter.py`: already fully generic, no fix needed there.

Submitted free-gen manually, no `--dependency` flag (per the sprint's corrected no-dependency policy): job **661051**.

**660990 (CoT-target)**: still running, step 370/500 as of this check — its own free-gen submission will follow once it completes and output is verified on disk.

### 2026-07-13, ~20:37 UTC — free-gen crashed on a real bug; both DeepSeek optimizations now complete

**661051 (standard-target free-gen) FAILED**: `KeyError: 'deepseek_r1'` from `poc_stage4/model_family_utils.py`'s `THINKING_MARKERS_BY_FAMILY[model_family]` — this dict (and `DEFAULT_MODEL_BY_FAMILY`, `DEFAULT_MODEL_SLUG_BY_FAMILY`, `THINKING_SEGMENT_HINTS_BY_FAMILY`) had only ever been populated for `qwen3`/`gemma4`, never extended for `deepseek_r1` even though `run_optimization.py`/`build_cot_target_manifest.py` were. `evaluate_optimized_suffixes.py`'s `locate_positions()` hits this lookup on every evaluated task. **Fixed**: added a `deepseek_r1` entry to all four dicts in `model_family_utils.py`, reusing Qwen3's exact `<think>`/`</think>` marker strings (confirmed correct earlier this sprint from the live tokenizer/chat-template check). Verified the fix resolves the lookup with no further errors.

**660990 (CoT-target) also completed**: 500/500 steps, best task_loss=19.78 (down from 48.70 at step 0).

Resubmitted free-gen for both runs manually (no dependency, correct `MANIFEST=` env var this time): **661081** (standard-target retry) and **661080** (CoT-target, first attempt).

### 2026-07-14, ~02:37 UTC — free-gen complete for both runs: unexpectedly high, suffix-independent baseline compliance

Both **661080** (CoT-target) and **661081** (standard-target) confirmed COMPLETED (`sacct`, exit 0). Direct StrongREJECT success counts from `FREE_GENERATION_RESULTS.jsonl`:

| Run | optimized_weighted | neutral_control | random_spaces | task_only |
|---|---|---|---|---|
| CoT-target | 37/75 (49.3%) | 35/75 (46.7%) | 38/75 (50.7%) | 38/75 (50.7%) |
| standard-target | 31/75 (41.3%) | 36/75 (48.0%) | 37/75 (49.3%) | 37/75 (49.3%) |

**Key finding: DeepSeek-R1-Distill-Qwen-7B complies with harmful AdvBench requests roughly half the time with no adversarial suffix at all** (`neutral_control`/`random_spaces`/`task_only` all land in the 47-51% range). This is a dramatically weaker safety baseline than either Qwen3-14B or Gemma4-E4B-it, whose neutral-control rates were near-zero throughout every prior Phase 4-8 run in this project. Against this already-high floor, the GCG-optimized suffix shows **no clear uplift** — for the standard-target run, `optimized_weighted` (31/75) is nominally the *worst* of the four conditions, the opposite direction from every other model/run in this project.

**Implication for the cross-architecture generalization question this track was built to answer**: the original hypothesis ("CoT target misalignment is a barrier, fixable by CoT-prefix targeting") can't really be tested on a model that's already ~50% compliant without any attack — there's no safety barrier for GCG to overcome here. This is a genuinely different failure mode from Qwen3/Gemma4 and should be reported as such (a weak-baseline-safety model, not a validation or refutation of the CoT-prefix mechanism), not force-fit into the original framing.

Replay submitted for both runs to confirm (no dependency): **661327** (CoT-target), **661328** (standard-target). Will run `analyze_pareto_frontier.py` and a paired significance check (McNemar's, matching the Phase 4-7 audit methodology) before writing any final conclusion — a few-point gap at n=75 could be noise, but the *direction* (optimized ≤ controls) is worth confirming carefully rather than dismissing.

### 2026-07-14, ~03:07 UTC — replay complete; significance check confirms no effect

Both replays (661327 CoT-target, 661328 standard-target) COMPLETED cleanly. Ran `analyze_pareto_frontier.py` manually for both (per the standing Phase-8-discovered gap that this isn't auto-invoked elsewhere) — `RESULTS_SUMMARY.md` written for both, confirming best task_loss 19.78 (CoT-target) / 10.12 (standard-target), matching the optimization-stage numbers already recorded.

Ran an exact McNemar's paired significance test (`scipy.stats.binomtest`, matching the Phase 4-7 audit's own methodology) between `optimized_weighted` and `neutral_control`, paired by (task_id, seed):

| Run | optimized-only successes | control-only successes | McNemar exact p |
|---|---|---|---|
| CoT-target | 13 | 11 | 0.84 |
| standard-target | 13 | 18 | 0.47 |

**Neither reaches significance.** This confirms rather than merely suggests the conclusion: on this model, the GCG-optimized suffix has no measurable effect beyond the baseline's already-high compliance rate. **Final read for this track**: DeepSeek-R1-Distill-Qwen-7B is not a useful test of "does CoT-prefix targeting fix a CoT-target-misalignment barrier" because there is essentially no barrier to begin with (baseline ~50% compliant). This is a genuinely different result from Qwen3 (where CoT-prefix targeting produced a large, real uplift over near-zero baselines) and from Gemma4 (where the attack failed against a robust baseline) — a third, distinct outcome class: **weak-safety-baseline models where adversarial optimization has no headroom to demonstrate value.** Ready to fold into `docs/GCG_FINDINGS_SYNTHESIS.md` as an explicit, separate step.
