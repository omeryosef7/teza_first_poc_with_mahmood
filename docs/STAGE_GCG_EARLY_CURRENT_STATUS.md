# Stage GCG-Early: Current Status

**Last updated:** 2026-07-05  
**Current stage:** Stage 8c (lexicographic, lambda_repr=5.0, job 641092) + Stage 9 eval (job 641091) both running

---

## Implementation Status

| Component | Status | Notes |
|---|---|---|
| `docs/STAGE_GCG_EARLY_INTEGRATION_AUDIT.md` | ✅ Written | Full GCG audit + Stage AE mapping |
| `docs/STAGE_GCG_EARLY_EXPERIMENT_PLAN.md` | ✅ Written | Stages 3–10 + causal claims table |
| `poc_stage_gcg_early/__init__.py` | ✅ | Package docstring |
| `poc_stage_gcg_early/config.py` | ✅ | SurrogateTask, GCGHyperparams, ObjectiveWeights, RunConfig |
| `poc_stage_gcg_early/model_adapter.py` | ✅ | Embedding access, EOS, chat template |
| `poc_stage_gcg_early/suffix_token_manager.py` | ✅ | SuffixSpans, build_suffix_spans, replace_suffix, get_filtered_cands |
| `poc_stage_gcg_early/selected_state_capture.py` | ✅ | Wrapper over Stage AE hooks |
| `poc_stage_gcg_early/reference_cache.py` | ✅ | Config-keyed cache with invalidation |
| `poc_stage_gcg_early/objectives.py` | ✅ | task_loss, repr_loss, kl_loss, regularization_loss, composite_loss |
| `poc_stage_gcg_early/gcg_optimizer.py` | ✅ | Full loop: gradient → sample → filter → evaluate → select → checkpoint |
| `poc_stage_gcg_early/build_safe_surrogate_manifest.py` | ✅ | 4-task harmless manifest |
| `poc_stage_gcg_early/run_optimization.py` | ✅ | CLI entry point with --reference-cache-dir, --repr-layers, --no-filter-cand |
| `poc_stage_gcg_early/evaluate_optimized_suffixes.py` | ✅ stub | Stage 9 — pending Stage 3 gate |
| `poc_stage_gcg_early/audit_run.py` | ✅ | Run completeness audit + DONE flag |
| `poc_stage_gcg_early/analyze_pareto_frontier.py` | ✅ Full impl | Writes RESULTS_SUMMARY.md; Pareto frontier, trajectory stats, Stage 3 gate check |
| `poc_stage_gcg_early/analyze_detection_delay.py` | ✅ Full impl | Writes DETECTION_DELAY_ANALYSIS.md; condition table from FREE_GENERATION_RESULTS.jsonl |
| `poc_stage_gcg_early/tests/test_suffix_manager.py` | ✅ 17 tests | All passing |
| `poc_stage_gcg_early/tests/test_objectives.py` | ✅ 12 tests | All passing |
| `poc_stage_gcg_early/tests/test_state_capture.py` | ✅ 3 CPU tests | All passing; GPU integration test marked |
| `poc_stage_gcg_early/tests/test_reference_cache.py` | ✅ 7 tests | All passing |
| `outputs/stage_gcg_early/surrogate_manifest_v1.jsonl` | ✅ | 4 tasks, SHA256=4e38c5306546 |
| `slurm_scripts/smoke_gcg_qwen3.slurm` | ✅ | Stage 3 smoke: 50 steps, suffix_length=8 |
| `slurm_scripts/run_gcg_qwen3_optimization.slurm` | ✅ | Stage 8 main run (do not submit yet) |

---

## Test Results (CPU-only, 2026-07-05)

```
49 passed, 0 failed (verified 2026-07-05)
  test_objectives.py:      29/29
  test_suffix_manager.py:  17/17
  test_state_capture.py:    3/3  (gpu_integration deselected)
  test_reference_cache.py:  7/7
```

---

## Validation Gates

| Gate | Status |
|---|---|
| Stage 3: task_loss decreases | ✅ PASSED — 3.9844→0.1123 (97% reduction, 50 steps, jobs 640936/640947) |
| Stage 3: same seed → same trajectory | ✅ PASSED — v2 and v3 identical step-by-step, audit DONE |
| Stage 3: resume produces identical result | ✅ PASSED — job 640947: "[GCG] Resuming from step 49", clean exit |
| Stage 4: hook capture ≡ output_hidden_states | ✅ PASSED — job 640954: 1 passed in 43s on L40S |
| Stage 5: reference cache built | ✅ PASSED — job 640959: 4 tasks cached in 1:26 |
| Stage 5: cache invalidation | ✅ Tested (CPU mock) |
| Stage 8a: v1 (filter_cand=True) | ❌ FAILED — suffix frozen for all 200 steps (BPE filter rejects all candidates when suffix_length=16) |
| Stage 8 v2: filter_cand=False, 200 steps | ✅ PASSED — job 640983: task_loss 2.52→0.05 (98% reduction); repr_loss ≈ 0 (expected — wrong positions) |
| Stage 8b: reference cache v2 build | ✅ PASSED — job 641046: 4 tasks, positions task-specific (suffix-relative) |
| Stage 8b: optimization run | ✅ PASSED — job 641047: task_loss 2.81→0.012, repr_loss 0.20→0.51 (active gradient confirmed) |
| Stage 8c: lexicographic + lambda_repr=5.0 | ⏳ Running — job 641092 (explore lower repr_loss region) |
| Stage 9: free-generation evaluation | ⏳ Running — job 641091 (Stage 8b candidates) |

---

## Stage 8b Findings (2026-07-05)

| Metric | Step 0 | Final (step 199) |
|---|---|---|
| task_loss | 2.81 | 0.012 |
| repr_loss | 0.205 | 0.514 |
| total_loss | 3.02 | 0.526 |

**Interpretation:** With lambda_repr=1.0 (weighted mode), task_loss objective dominates the gradient. The optimizer successfully reduces task_loss by 99%, but repr_loss actually INCREASES from ~0.20 (initial "! ! !" suffix) to ~0.51 (optimized suffix). This means the optimized suffix makes early hidden states MORE different from the neutral reference, not less — the two objectives are in conflict. The lexicographic and higher-lambda runs (Stage 8c) explore whether repr_loss can be kept low while still achieving task success.

## Next Actions

1. **Monitor job 641091** (Stage 9 free-generation): Wait for FREE_GENERATION_RESULTS.jsonl. Key metric: do optimized suffixes cause the model to generate the target task correctly in free-generation mode?

2. **Monitor job 641092** (Stage 8c lexicographic + lambda_repr=5.0): Does heavier repr weighting or lexicographic selection achieve lower repr_loss while keeping task_loss < 0.1?

3. **Analyze Pareto frontier**: Run `analyze_pareto_frontier.py` after Stage 9 to compare repr_loss vs task_loss across conditions.

4. **Stage 10 — Gemma4 extension**: After Stage 9 analysis completes.

## Stage 8b Reference Cache v2 — Verified Positions (2026-07-05)

| Task | suffix_slice | positions (last 3 suffix tokens) |
|---|---|---|
| fruit_list_alpha | slice(15, 31) | [28, 29, 30] |
| celsius_convert | slice(30, 46) | [43, 44, 45] |
| capital_france | slice(21, 37) | [34, 35, 36] |
| count_vowels | slice(23, 39) | [36, 37, 38] |

These positions are within the suffix region (not before it), so causal attention flows from them back through all suffix tokens → non-zero repr gradient.

## Bugs Found and Fixed (2026-07-05, Stage 8)

| Bug | Root Cause | Fix | Status |
|---|---|---|---|
| repr_loss ≈ 0.0001 always (no gradient) | Positions 0,1,2 are before suffix in causal LM → no attention from them to suffix tokens | `gcg_optimizer.py`: compute repr_pos per-task as `[suffix_slice.stop - N + i for i in range(N)]`; `build_reference_cache.py`: `--repr-positions N --suffix-length 16` builds v2 cache | ✅ FIXED — job 641046 building cache v2 |
| Stage 8 v1: suffix frozen 200 steps | `get_filtered_cands(filter_cand=True)` rejects all 64 candidates when suffix_length=16 (BPE non-invertibility with tiktoken); fallback = current suffix repeated | `--no-filter-cand` (safe since `suffix_ids_override` bypasses BPE in optimizer) | ✅ FIXED — job 640983 PASSED (task_loss 2.52→0.05) |

---

## Bugs Fixed (2026-07-05)

| Bug | Fix |
|---|---|
| `nvidia-smi --query-gpu=name \| head -1` SIGPIPE under `set -o pipefail` | Changed to `awk 'NR==1{print;exit}'` in both SLURM scripts |
| Python heredoc `${OUTPUT_DIR}` inside single-quoted `'PYEOF'` unexpanded | Changed to `python - "$OUTPUT_DIR" <<'PYEOF'` + `sys.argv[1]` |
| **BPE non-invertibility → CUDA device-side assert** (job 640912) | `build_suffix_spans` was re-tokenizing `suffix_str` via decode→encode, giving fewer tokens than `suffix_ids`. Qwen3 tiktoken: `"! "` → `[0,220]`, decode → `"! ! ! ! "`, re-encode → `[0,753,753,753,220]` (5 tokens not 8). Fix: added `suffix_ids_override` param to `build_suffix_spans`; optimizer now passes actual IDs directly. |
| `preserve_grad=True` in `selected_state_capture` doesn't work (hooks always detach) | Documented; Stage 6 must use `output_hidden_states=True` with `inputs_embeds` instead |

## Known Limitations

| Limitation | Impact | Workaround |
|---|---|---|
| `preserve_grad=True` in `capture_selected_states` doesn't propagate gradients | Stage 6+ repr-loss gradients broken if using hook path | Use `output_hidden_states=True` with `inputs_embeds` during gradient step |
| Single-task evaluation for candidate selection (uses train_tasks[0] only) | Multi-task averaging is only for gradients | Acceptable for smoke study; multi-task eval batch too expensive |

## Blockers

| Blocker | Resolution |
|---|---|
| BPE non-invertibility CUDA assert (was blocking all runs) | **FIXED** — `suffix_ids_override` added to `build_suffix_spans`, commit e092df7 |
| `config_hash` included `run_id`/`output_dir` → resume always failed | **FIXED** — commit f8535a2: hash now covers only scientific params |
| Stage 4 hook capture equivalence | **CONFIRMED** — job 640954 PASSED |
| Stage 5 layer index error (0,6,12,...,47 OOR) | **FIXED** — layers corrected to 0,5,10,15,20,25,30,35,40 in build_reference_cache.py |
| Stage 8 v1: suffix frozen (BPE filter) | **FIXED** — commit 172146f: `--no-filter-cand` added; job 640983 running |
| repr_loss ≈ 0 (causal masking, wrong positions) | **DIAGNOSED** — next: rebuild cache with suffix-relative positions |

---

## Files Created This Session

- `docs/STAGE_GCG_EARLY_INTEGRATION_AUDIT.md`
- `docs/STAGE_GCG_EARLY_EXPERIMENT_PLAN.md`
- `docs/STAGE_GCG_EARLY_CURRENT_STATUS.md`
- `poc_stage_gcg_early/` (complete package, 14 files + 4 test files)
- `outputs/stage_gcg_early/surrogate_manifest_v1.jsonl`
- `slurm_scripts/smoke_gcg_qwen3.slurm`
- `slurm_scripts/run_gcg_qwen3_optimization.slurm`
- `slurm_scripts/build_gcg_reference_cache_v2.slurm`
- `slurm_scripts/run_gcg_free_generation.slurm`
- `slurm_scripts/run_gcg_analysis.slurm`
- `slurm_scripts/run_gcg_replay.slurm`

**Untouched:** all of `llm-attacks/`, all of `poc_stage_ae/`, all existing SLURM scripts.
