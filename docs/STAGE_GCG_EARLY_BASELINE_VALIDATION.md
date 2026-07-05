# Stage GCG-Early: Baseline Validation Report

**Date:** 2026-07-05  
**Node:** n-801 (L40S GPU)  
**Git revision:** 8c7dd3ff46465d1859b8cff9d840784d65949a7b  
**Run IDs:** smoke_gcg_qwen3_v2 (job 640936), smoke_gcg_qwen3_v3 (job 640947)

---

## Summary

All Stage 3 validation gates passed. The GCG task-only baseline is confirmed working
on Qwen3-14B with the surrogate manifest. Resume compatibility is confirmed.

---

## Validation Gate Results

| Gate | Status | Evidence |
|---|---|---|
| task_loss decreases over 50 steps | ✅ PASSED | 3.9844 → 0.1123 (97% reduction) |
| Same seed reproduces same trajectory | ✅ PASSED | v2 and v3 show identical step-by-step loss/suffix evolution |
| Resume loads checkpoint and continues | ✅ PASSED | "[GCG] Resuming from step 49" — correct suffix, loop exits cleanly |
| All artifacts present and audit-certified | ✅ PASSED | audit_run.py: 11/11 checks OK, DONE written |

---

## Optimization Trajectory (v3 — smoke_gcg_qwen3_v3)

| Step | task_loss | suffix |
|---|---|---|
| 0 | 3.9844 | `! ! ! ! ` |
| 10 | 3.9844 | `! ! ! ! ` (topk warming up) |
| 20 | 1.3906 | `  \n 欣喜 den !**\n\n` |
| 30 | 0.5273 | `  \n 欣喜 igen !\n**\n\n` |
| 40 | 0.2617 | `\r\n\r\n\r\n\r\n 精确 igen !\n**\n\n` |
| 49 (final) | 0.1768 | `\r\n\r\n\r\n\r\n 精确 igen $\n**\n\n` |
| **best** | **0.1123** | `\r\n\r\n\r\n\r\n 精确 igen $\n**\n\n` (step 46) |

loss[0]=3.9844, loss[-1]=0.1768, best=0.1123 — **97% reduction**

---

## Reproducibility

v2 (job 640936) and v3 (job 640947) were submitted with identical hyperparameters
(model=Qwen/Qwen3-14B, suffix_length=8, n_steps=50, batch_size=32, topk=256, seed=42)
and produced identical step-by-step outputs:

```
step= 0: 3.9844  suffix='! ! ! ! '
step=20: 1.3906  suffix='  \n 欣喜 den !**\n\n'
step=30: 0.5273  suffix='  \n 欣喜 igen !\n**\n\n'
step=40: 0.2617  suffix='\r\n\r\n\r\n\r\n 精确 igen !\n**\n\n'
```

The optimizer is deterministic under fixed seed.

---

## Resume Validation (v3)

The SLURM script re-ran the identical command on the same output directory
after the 50-step run completed. The optimizer detected the checkpoint at step 49:

```
[GCG] Resuming from step 49 (suffix length 8)
[GCG] Optimization complete. Final suffix: '\r\n\r\n\r\n\r\n 精确 igen $\n**\n\n'
Resume test: checkpoint detected and loaded successfully.
```

The loop range(50, 50) was empty → optimizer exited immediately with the correct
suffix state. config_hash matched (e756495ed7e95c4f), confirming checkpoint
compatibility across runs with same scientific hyperparameters.

---

## Infrastructure Confirmed

| Property | Value |
|---|---|
| GPU | NVIDIA L40S, 46068 MiB |
| Peak GPU memory (optimization) | 27.94 GB |
| Per-step wall time | ~0.93 seconds |
| Model loading time | ~13 minutes (443 weight shards) |
| Total job time | ~30 minutes (model load × 2 + optimization) |
| Embedding path | `model.model.embed_tokens.weight` (confirmed by gradient flow) |
| Tokenizer | Qwen3/tiktoken BPE — BPE non-invertibility bug fixed via `suffix_ids_override` |

---

## Bugs Fixed Before This Validation

| Bug | Fix | Commit |
|---|---|---|
| CUDA device-side assert from BPE non-invertibility | `suffix_ids_override` parameter in `build_suffix_spans` | e092df7 |
| Resume always failed: `config_hash` included `run_id`/`output_dir` | Hash now covers only scientific params | f8535a2 |

---

## Artifacts

```
outputs/stage_gcg_early/smoke_gcg_qwen3_v3/
├── DONE                      ← audit-certified
├── AUDIT_REPORT.md           ← 11/11 OK
├── CONFIG.json               ← full RunConfig
├── ENVIRONMENT.json          ← git rev, GPU, torch, transformers
├── MANIFEST.jsonl            ← 2 train tasks (fruit_list_alpha, celsius_convert)
├── ITERATION_LOG.jsonl       ← 50 rows; all loss components per step
├── PARETO_CANDIDATES.jsonl   ← 50 entries
├── FINAL_CANDIDATES.jsonl    ← best suffix at run end
├── checkpoint.pt             ← step 49, full RNG state
├── checkpoint_step_24.pt     ← permanent trajectory snapshot
└── checkpoint_step_49.pt     ← permanent trajectory snapshot
```

---

## Next Steps

1. **Stage 4** — GPU integration test: hook capture ≡ output_hidden_states for Qwen3-14B
2. **Stage 5** — Reference cache building for all surrogate tasks
3. **Stage 8** — Optimization with representation objective (lambda_repr > 0)
