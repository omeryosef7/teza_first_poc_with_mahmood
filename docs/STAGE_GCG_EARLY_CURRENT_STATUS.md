# Stage GCG-Early: Current Status

**Last updated:** 2026-07-05  
**Current stage:** Stage 3 — smoke job 640936 PENDING (BPE fix applied; awaiting GPU slot)

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
| `poc_stage_gcg_early/run_optimization.py` | ✅ | CLI entry point with ENVIRONMENT.json |
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
| Stage 3: task_loss decreases | ⏳ Pending cluster smoke run |
| Stage 3: same seed → same trajectory | ⏳ Pending |
| Stage 3: resume produces identical result | ⏳ Pending |
| Stage 4: hook capture ≡ output_hidden_states | ⏳ Pending GPU integration test |
| Stage 5: cache invalidation | ✅ Tested (CPU mock) |

---

## Next Actions

1. **Job 640936 is submitted (smoke_gcg_qwen3_v2) — monitor:**
   ```bash
   squeue -j 640936
   tail -f logs/gcg_smoke_qwen3_640936.out
   ```

2. **If job fails:** check err log; re-submit with new v3 RUN_ID
   ```bash
   sbatch --export=ALL,RUN_ID=smoke_gcg_qwen3_v3 slurm_scripts/smoke_gcg_qwen3.slurm
   ```

3. **After smoke passes:** check `outputs/stage_gcg_early/smoke_gcg_qwen3_v2/AUDIT_REPORT.md`

4. **If smoke passes:** proceed to Stage 8 (weighted repr objective):
   ```bash
   sbatch --export=ALL,RUN_ID=gcg_qwen3_repr_v1,LAMBDA_REPR=1.0,SUFFIX_LEN=16,N_STEPS=200 \
          slurm_scripts/run_gcg_qwen3_optimization.slurm
   ```

5. **GPU integration test** (on a cluster node with Qwen3-14B loaded):
   ```bash
   conda run -n poc_stage2 python -m pytest poc_stage_gcg_early/tests/test_state_capture.py \
       -m gpu_integration -v
   ```

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
| Cluster GPU availability | Job 640936 pending; awaiting slot |
| Qwen3-14B embedding path not confirmed at runtime | First model load will print model type; verify in smoke log |
| Stage AE `replay_hidden_states` import in cluster env | Verified importable without argparse side effects |

---

## Files Created This Session

- `docs/STAGE_GCG_EARLY_INTEGRATION_AUDIT.md`
- `docs/STAGE_GCG_EARLY_EXPERIMENT_PLAN.md`
- `docs/STAGE_GCG_EARLY_CURRENT_STATUS.md`
- `poc_stage_gcg_early/` (complete package, 14 files + 4 test files)
- `outputs/stage_gcg_early/surrogate_manifest_v1.jsonl`
- `slurm_scripts/smoke_gcg_qwen3.slurm`
- `slurm_scripts/run_gcg_qwen3_optimization.slurm`

**Untouched:** all of `llm-attacks/`, all of `poc_stage_ae/`, all existing SLURM scripts.
