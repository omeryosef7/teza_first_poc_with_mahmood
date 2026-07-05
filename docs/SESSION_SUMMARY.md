# Session Summary — Stage AE Early-Token Expansion (Qwen3-14B & Gemma4-E4B-it)

Self-contained summary of one autonomous multi-day session. Written for
handoff to a reader (human or LLM) with no other context on this repo.

## Objective

Run a paired behavioral + early-representation study across two models
(Qwen3-14B, Gemma4-E4B-it) to answer: why does condition E (bare goal,
thinking-off) fail differently than condition A (obfuscated puzzle,
thinking-on)? Is attack success already visible in the first few
generated tokens? Does that signal transfer across model families?

This required: a 2x(A/E/D/G)-condition generation run over a canonical
220-prompt jailbreak dataset at 3 new seeds (2772 rows total, 1386/model),
deterministic hidden-state replay at named token positions, StrongREJECT
scoring + a heuristic failure taxonomy, and cross-model analysis — all run
autonomously on SLURM (partition `killable`, L40S GPUs) over roughly two
days while the user was away, via a repeating `/loop` check-in every 30
minutes.

## What was built (`poc_stage_ae/` package)

- `build_ae_manifest.py` — manifest construction (1386 rows/model: 1320
  A/E + 66 D/G, one canonical bare-goal source per goal for D/G, not one
  per puzzle variant).
- `run_ae_generation.py` — generation runner (reused Stage 4's model
  loaders / thinking-toggle / EOS handling), resumable via row-key.
- `thinking_position_utils.py` — locates named token positions
  (`prefill_last`, `startofthink`, `think_content_1/2/3`, `endofthink`,
  `endofresponse` for A/D; `prefill_last`, `answer_content_1/2/3`,
  `endofresponse` for E/G) by token-ID subsequence search.
- `replay_hidden_states.py` — deterministic hidden-state replay via
  per-layer forward hooks (bounded memory vs. a monolithic
  `output_hidden_states=True` call), with a `--verify-equivalence` smoke
  check against the same hidden states.
- `score_ae_outputs.py` — StrongREJECT scoring (threshold 0.5) +
  heuristic (keyword/regex, not LLM-judge) failure-taxonomy annotation.
- `audit_ae_run.py` — expected-vs-completed row auditing, drives resume.
- **`analyze_paired_ae.py`, `analyze_early_token_signals.py`,
  `analyze_cross_model_results.py`** — built fresh this session (did not
  exist before): paired A/E taxonomy deltas by goal; grouped
  leave-one-goal-out (LOGO) AUC for per-position/per-layer separability
  of attack success (never in-sample); cross-model join by normalized
  layer depth.
- 14 SLURM scripts under `slurm_scripts/` (generation, replay, scoring,
  resume wrappers, smoke tests) for both models.

## Key bugs found and fixed during the run

1. **`finish_reason` mislabeling bug** (`run_ae_generation.py`): only
   checked `eos_ids[0]` instead of the full multi-EOS-id list Gemma4
   uses, so ~1238 Gemma rows were labeled `finish_reason="unknown"` even
   though generation completed correctly and the text was never
   truncated/corrupted — only the label was wrong. Fixed the check, then
   backfilled all affected rows' labels in place (no regeneration
   needed, verified via `eos_diagnostics.last_generated_token_id` already
   matching a valid EOS id).
2. **Hidden-state final-layer-norm bug** (`replay_hidden_states.py`,
   found during the Stage 8 Gemma smoke test): the forward-hook capture
   did not apply the model's final `LayerNorm`/`RMSNorm` before
   returning the last layer's hidden state, while
   `output_hidden_states=True` does — caused an equivalence-check FAIL
   at exactly `layer=42` on all 4 smoke conditions. Fixed via
   `_find_final_norm_module`/`_hook_capture_forward`; re-verified PASS
   for both Qwen3 and Gemma4 before full launch.
3. **Locale-collation sort-order bug** (my own monitoring methodology,
   not a pipeline bug): Python's `sorted(glob.glob(...))` disagrees with
   bash's `find ... | sort` on ordering e.g. `goal10` vs `goal1`, which
   could produce wrong "missing array index" computations. Standardized
   on bash's `sort` for any authoritative shard-index list going forward.

## Operating rules established this session (also saved to persistent memory)

- Max 6 SLURM jobs in parallel, ever (hard user rule, pre-existing).
- **New this session**: never leave SLURM jobs sitting PENDING for long
  — check actual node GPU occupancy (`scontrol show node ... | grep
  AllocTRES`) before submitting, not just squeue counts; cancel and
  resubmit later if a job gets stuck pending behind real cluster
  contention (a `PENDING (Priority)` job with `StartTime=Unknown` right
  after submission usually resolves on its own within a scheduler cycle;
  one with a day(s)-out `StartTime` estimate means real contention —
  cancel it rather than waiting).
- Two benign, non-actionable SLURM failure signatures observed
  repeatedly and documented so they wouldn't be mistaken for pipeline
  bugs: (1) a transient cgroup race (exit 13, empty `.err`, ~2-4s
  runtime, output cuts off right after the nvidia-smi listing); (2)
  preemption on the `killable` partition (task drops from
  RUNNING back to PENDING, `.err` shows "CANCELLED ... DUE TO
  PREEMPTION", auto-requeues).

## Final results

| Model | Generation rows | Replay shards | Scored rows |
|---|---|---|---|
| Qwen3-14B | 1386/1386 | 44/44 | 1386/1386 (1385 with a valid StrongREJECT score — see Known Issues) |
| Gemma4-E4B-it | 1386/1386 | 44/44 | 1386/1386 |

**Analysis findings** (descriptive/predictive only — no causal claims):
- Puzzle-framing (condition A) raises attack success vs. bare goal
  (condition E) for both models: mean success-rate delta (A − E) =
  **+0.206 (Qwen3)**, **+0.064 (Gemma4)**, same direction.
- **Cross-model sign agreement on that A-vs-E success delta = 100%
  across all 11 goals** — the goals where puzzle-framing helps are the
  same goals in both models.
- Using grouped leave-one-goal-out AUC (never in-sample), **attack
  success is predictable from hidden states within the first 1-3
  generated tokens**, before the visible text resolves the puzzle/answer
  — e.g. Qwen3 condition-A `think_content_1` AUC ≈0.78-0.81; both
  models' condition-E `answer_content_1` AUC ≈0.72-0.77. The two model
  families differ in *when* (which depth) this becomes visible, not
  *whether* it does.

## Known issues (not fixed, intentionally left for the user)

- **1 of 2772 scored rows has a StrongREJECT API error**
  (`qwen3|4|goal_index=4|...|E|203`, `strongreject_score=null`). Found
  during a post-completion verification pass. Retrying requires editing
  the completed scoring output file in place; this was attempted and
  correctly blocked as an unreviewed destructive edit to finished
  research data, so it was left as-is and documented rather than forced
  through. It does not corrupt any analysis result (both analysis
  scripts skip null-labeled rows), but the affected cell is technically
  1385/1386 rather than 1386/1386.

## Where everything lives

- **This file** — one-shot session summary (you're reading it).
- `docs/STAGE_AE_EARLY_TOKEN_PROGRESS.md` — the full incremental log:
  every SLURM job ID, every check-in, every failure diagnosis, in
  chronological order. Use this if you need the blow-by-blow, not just
  the summary.
- `outputs/stage_ae_early_token_expansion/full_20260702_095452/RUN_STATUS.md`
  — compact final snapshot of just the pipeline run (job IDs, row
  counts, analysis results) — narrower scope than this file, no session
  narrative. Same directory also has `EXPERIMENT_PLAN.md` (the approved
  plan), `SLURM_AND_MODEL_AUDIT.md`, `IMPLEMENTATION_AUDIT.md`,
  `SMOKE_TEST_REPORT_{QWEN,GEMMA}.md`, and a `DONE` marker.
- `poc_stage_ae/` — all pipeline code (generation, replay, scoring,
  analysis, audit).
- `slurm_scripts/` — all SLURM submission/resume scripts for this stage.
- Git: commits `5c5246a` (pipeline code + docs), `3c4253f` and `39d0247`
  (progress-log updates). `outputs/` is gitignored — not committed.
