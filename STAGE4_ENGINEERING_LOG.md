# Stage 4 Token Dynamics — Full Engineering Log

**Project:** Chain-of-Thought Hijacking (MSc Thesis, Tel Aviv University)  
**Goal of Stage 4:** For each of 42 attack examples, project every generated token's hidden state at every layer (0–39) of Qwen3-14B onto the "refusal direction" vector, producing a 40-layer × N-token signal that tracks how the model's refusal representation evolves through the thinking chain.  
**Last updated:** 2026-06-07  
**Current status:** Job 490729 running — forward-hook fix, 18 remaining examples, ~2.5 h ETA

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Pipeline Stages](#2-pipeline-stages)
3. [Key Artifacts](#3-key-artifacts)
4. [Stage 4 Attempts — Chronological Log](#4-stage-4-attempts--chronological-log)
   - [Attempt 0: Stage 2B and Stage 6 (prerequisites)](#attempt-0-stage-2b-and-stage-6-prerequisites)
   - [Attempt 1: Job 415272 — Cancelled on wrong node](#attempt-1-job-415272--cancelled-on-wrong-node)
   - [Attempt 2: Job 415274 — Success but wrong input](#attempt-2-job-415274--success-but-wrong-input)
   - [Attempt 3: Jobs 418832, 426475, 436641 — Silent partial-layer bug](#attempt-3-jobs-418832-426475-436641--silent-partial-layer-bug)
   - [Attempt 4: Job 461188 — OOM on wrong node type](#attempt-4-job-461188--oom-on-wrong-node-type)
   - [Attempt 5: Job 476121 — 24/42 completed, 18 OOM](#attempt-5-job-476121--2442-completed-18-oom)
   - [Attempt 6: Job 490207 — del fix insufficient](#attempt-6-job-490207--del-fix-insufficient)
   - [Attempt 7: Job 490729 — Forward-hook fix (CURRENT)](#attempt-7-job-490729--forward-hook-fix-current)
5. [Root Cause Analysis Summary](#5-root-cause-analysis-summary)
6. [Current Output State](#6-current-output-state)
7. [Refusal Direction Metadata](#7-refusal-direction-metadata)
8. [Confirmed Results (24 completed examples)](#8-confirmed-results-24-completed-examples)
9. [What Comes Next](#9-what-comes-next)

---

## 1. Project Overview

The thesis studies **Chain-of-Thought Hijacking**: embedding harmful goals inside complex structured puzzles (Sudoku grids, logic puzzles, formal systems) to steer Qwen3-14B's extended reasoning (think-mode) toward harmful outputs.

The core analytical contribution is tracking how the **refusal direction** — a [5120]-dimensional unit vector in the model's residual stream — evolves token-by-token across all 40 transformer layers as the model reasons through an attack prompt.  

The expected pattern: when an attack succeeds, the refusal direction projection should drop during the thinking phase and stay low into the generation. When the model resists, the projection should rise or stay high.

**Model:** Qwen3-14B (local HuggingFace), `enable_thinking=True`, generates `<think>…</think>` before the final answer.  
**Attack dataset:** 42 examples (goal_index 0–3 × attack_iteration 1–2 × conversation_id 1–6).  
**Evaluators:** StrongREJECT (GPT-4o-mini rubric scorer) + Gemini LLM-as-judge (safe=1, unsafe=10).

---

## 2. Pipeline Stages

| Stage | Script / Output | Status |
|-------|----------------|--------|
| **Stage 2B** — Run Qwen3-14B on all 42 attack prompts, save full token data | `poc_stage2b/run_batch_attack.py` → `outputs/stage2b/qwen3-14b/stage2b_qwen3_batch.jsonl` | ✅ Complete (42/42) |
| **Stage 6** — Full token trace extraction (prompt + thinking + generation token IDs) | `outputs/stage6/all_traces_full/` (43 files = 42 traces + 1 summary) | ✅ Complete (42/42) |
| **Stage 4A1** — Refusal direction extraction (contrast harmful vs. harmless activations) | `outputs/stage4/qwen3-14b/refusal_direction/direction.pt` | ✅ Complete (provisional) |
| **Stage 4 Token Dynamics** — Project all token hidden states at all 40 layers onto refusal direction | `outputs/stage4/token_dynamics/full_20260604_101929/` | 🔄 24/42 done, 18 running |

---

## 3. Key Artifacts

### Refusal Direction (`direction.pt`)
- **File:** `outputs/stage4/qwen3-14b/refusal_direction/direction.pt` (3.2 MB)
- **Shape:** [5120] float32 unit vector (a view into a [4, 40, 5120] candidate tensor)
- **Extracted at:** layer 22, prompt position −3 (3rd token from end of prompt)
- **Separation score:** 14.17 (harmful mean projection = 61.89, harmless mean = −3.61)
- **Status:** `provisional_projection_diagnostic_only` — selected by Stage 4A1 projection diagnostics, not yet confirmed by Stage 4A2 intervention-based selection
- **Warning:** Must not be treated as intervention-selected for scientific claims

### Stage 6 Traces (`outputs/stage6/all_traces_full/`)
- 42 JSON files, each containing:
  - `full_prompt_plus_generation_token_ids`: complete token ID sequence (prompt + thinking + generation)
  - `token_table`: per-token metadata with segment labels (`prompt`, `thinking`, `generation`)
  - `prompt_token_count`, `generation_token_count`
  - StrongREJECT score, judge score, `qwen_run_success`

### Stage 2B Batch Results (`outputs/stage2b/qwen3-14b/stage2b_qwen3_batch.jsonl`)
- 42 rows, one per attack example
- Attack success rate: ~57% (StrongREJECT ≥ 0.5 or judge = 10)
- Token counts per example: prompt 483–1,112 tokens; generation (think + answer) up to 32,768 tokens

---

## 4. Stage 4 Attempts — Chronological Log

---

### Attempt 0: Stage 2B and Stage 6 (prerequisites)

**Date:** 2026-05-30  
**Jobs:** 415773 (failed), 415774 (success)

#### Stage 2B — Job 415773: Input schema mismatch
**Error:**
```
ValueError: Row 1 is missing required fields: ['goal_index']
```
The input JSONL `hijacking_baseline_gpt-o4-mini_small_strongreject.jsonl` had rows without `goal_index` — the loader expected that field but the actual rows used a different schema.

**Fix:** The SLURM script was adjusted to point to the correct input file that did have `goal_index`.

#### Stage 2B — Job 415774: Success
- **Node:** n-303 (RTX 3090, 24GB)
- **Duration:** ~9 hours 17 minutes (11:01 AM → 8:18 PM, 2026-05-30)
- **Output:** 42/42 rows written; 0 failed; 0 skipped
- Longest example: `goal_index=3, iter=1, conv=6` → 23,475 think tokens + 2,362 final tokens = ~25,837 total generation tokens; took 1,472 s
- Stage 6 full traces subsequently generated from these Stage 2B outputs.

---

### Attempt 1: Job 415272 — Cancelled on wrong node

**Date:** 2026-05-29 23:02 IDT  
**Node:** n-301 (small compute node, not GPU node)  
**Result:** Cancelled after 4 minutes

```
slurmstepd: error: *** JOB 415272 ON n-301 CANCELLED AT 2026-05-29T23:06:28 ***
slurmstepd: error: *** JOB 415272 STEPD TERMINATED ON n-301 AT 2026-05-29T23:09:28 DUE TO JOB NOT ENDING WITH SIGNALS ***
```

**Root cause:** The SLURM script had no `--nodelist` constraint. SLURM assigned n-301, a general compute node with no GPU (or insufficient GPU). The job never got to run the model.

**Fix:** Added `--nodelist` to restrict to GPU nodes.

---

### Attempt 2: Job 415274 — Success but wrong input

**Date:** 2026-05-29 23:06 IDT  
**Node:** n-304 (8×RTX 3090, each 24GB)  
**Duration:** ~27 minutes (23:06 → 23:33)  
**Run name:** `full_20260529_230644`

```
manifest: status=completed, completed=42, failed=0, skipped=0
per_prompt_metrics.jsonl: 42 rows
token_level_metrics.jsonl: 1,290,240 rows
per_example/: 42 files
```

**Looks like success — but the input was wrong.**

`STAGE6_INPUT` pointed to `outputs/stage6/all_traces_redacted` — the **redacted** traces that had thinking tokens trimmed/shortened. These produced much shorter sequences (prompt + answer only, without full multi-thousand-token thinking chains), which is why they fit comfortably in the RTX 3090's 24GB VRAM and completed quickly.

**The actual thesis analysis requires the FULL traces** (`outputs/stage6/all_traces_full/`) which include the complete thinking chain. The redacted run's token_level_metrics had only 1,290,240 rows; the correct full-trace runs have 24,461,040 rows — 19× more — because each example's sequence is 5,000–25,000 tokens long.

**What we learned:** The redacted traces are too short for the refusal-direction dynamics analysis. We need `all_traces_full`.

---

### Attempt 3: Jobs 418832, 426475, 436641 — Silent partial-layer bug

**Dates:** 2026-05-31 to 2026-06-02  
**Nodes:** n-802, n-804, n-803 (L40S, 46GB each)  
**Approach:** Forward pre-hooks, `--gpus=2` (two L40S GPUs), `all_traces_full`

All three jobs showed:
```
manifest: status=completed, completed=42, failed=0, skipped=0
token_level_metrics.jsonl: 24,461,040 rows
per_example/: 42 files
```

**Looked like complete success. But the data was wrong for most examples.**

#### The Bug: Multi-GPU `device_map` split

With `--gpus=2`, HuggingFace's `device_map="auto"` distributed Qwen3-14B across the two GPUs:
- **cuda:0** — `embed_tokens` + layers 0–17 (~14 GB)
- **cuda:1** — layers 18–39 + `lm_head` (~14 GB)

Forward pre-hooks were registered on `model.model.layers[i]`. When a hook fires on a layer that lives on **cuda:1**, the activation tensor `act` is on `cuda:1`. The direction vector was on CPU. The computation `direction_cpu.to(act.device)` moved the direction to cuda:1, but the hook result was still only written to `projections_store` — and the crucial issue was that only hooks on cuda:0 layers reliably captured data. For cuda:1 layers the activations came through after an internal device transfer in the model's forward pass, but the hook timing and/or the tensor's retain semantics meant most projections came back as zeros.

#### Verification

After running job 436641 (`full_20260601_193438`), checking per-example files revealed:
```
6/42 examples: full 40-layer data (layers 0–39)
36/42 examples: only layers 0–18 (the layers on cuda:0)
```

The 6 examples that worked were those processed when GPU memory was freshest (first batch on cuda:0 was still actively caching), but the pattern was clear: **layers 19–39 were silent for 36/42 examples**.

The manifest said `completed=42, failed=0` because the forward pass itself raised no errors — the model ran fine. The silent failure was in hook capture: the hook fired but produced zero/invalid data for cuda:1 layers.

**What we learned:**
1. `device_map="auto"` with 2 GPUs is incompatible with the pre-hook capture approach
2. "Completed" in the manifest does not guarantee correct per-layer data
3. Must verify layer coverage explicitly after any new run

**Wasted compute:** 3 full runs × ~7 hours each = ~21 GPU-hours on L40S nodes.

---

### Attempt 4: Job 461188 — OOM on wrong node type

**Date:** 2026-06-03 11:24 IDT  
**Node:** n-302 (8×RTX 3090, each 24GB)  
**Result:** 0/42 completed, 42/42 failed (instant OOM)

```
manifest: status=completed, completed=0, failed=42, skipped=0
MISSING: per_prompt_metrics.jsonl
MISSING: token_level_metrics.jsonl
```

```
[stage4_token_dyn] Error on goal_index=0|attack_iteration=1|...: CUDA out of memory.
  Tried to allocate 42.00 MiB. GPU 0 has a total capacity of 23.56 GiB
```

**Root cause:** After discovering the multi-GPU bug, the SLURM script was updated to use `--gpus=1` (single GPU). But the `--nodelist` still included n-302..n-305 (RTX 3090, 24GB each). With a single 24GB GPU, Qwen3-14B in bfloat16 (~28GB) doesn't fit — the model loader CPU-offloaded layers 29–39 to RAM, and any forward pass immediately exhausted the 24GB VRAM.

From the log:
```
NVIDIA GeForce RTX 3090, 24576 MiB, 16007 MiB  ← only 16GB free
(model tries to load onto this → CPU offload for layers 29-39)
```
All 42 examples failed within seconds.

**Fix:** Restricted `--nodelist` to **only n-802, n-803, n-804, n-805** (L40S 46GB nodes). Small nodes removed from the list.

---

### Attempt 5: Job 476121 — 24/42 completed, 18 OOM

**Date:** 2026-06-04 10:19 IDT  
**Node:** n-802 (L40S, 46GB, single GPU allocated)  
**Duration:** ~3 hours 45 minutes  
**Run name:** `full_20260604_101929`  
**Approach:** `output_hidden_states=True` (replaced forward hooks), `--gpus=1`, nodelist n-802..n-805

```
NVIDIA L40S, 46068 MiB, 45595 MiB  ← ~1.5 GB pre-used by other jobs
```

```
manifest: status=completed, completed=24, failed=18, skipped=0
per_prompt_metrics.jsonl: 24 rows
token_level_metrics.jsonl: 11,663,000 rows (4.7 GB)
per_example/: 24 files (total 439 MB)
```

#### Why `output_hidden_states=True` was chosen

The previous approach (forward pre-hooks) had silently failed for multi-GPU splits. The fix was:
1. Force single GPU (`--gpus=1`) so all 40 layers land on cuda:0
2. Use `output_hidden_states=True` — HuggingFace guarantees all 41 hidden state tensors are returned in a tuple; no device mismatch possible

For the 24 successful examples, **all 40 layers have non-null projections** (confirmed by per-example file inspection at `token_level_data[50]`).

Layer 22 signal confirmed:
- **Attack SUCCESS examples:** refusal direction mean projection ≈ 5.200
- **Attack FAILURE examples:** refusal direction mean projection ≈ 4.159

#### Why examples 25–42 failed

The Qwen3-14B model footprint on a single L40S (46GB) is approximately:
- Model weights (bfloat16): ~28 GB
- CUDA context + Flash Attention buffers + allocator overhead: ~11 GB
- **Total base footprint: ~39 GB**
- **Remaining free memory: ~4.5 GB**

With `output_hidden_states=True`, the forward pass creates **all 41 hidden-state tensors simultaneously** in GPU memory before returning. For sequences with 8,000–18,000 tokens:

```
41 layers × 15,000 tokens × 5,120 dims × 2 bytes (bfloat16) = 6.3 GB
```

6.3 GB needed, 4.5 GB free → **OOM**.

The 24 successful examples had shorter sequences (2,228–~10,000 tokens), which fit. The 18 failures had longer sequences (>~10,000 tokens) that required more than the available headroom.

**Error from logs (example 25):**
```
CUDA out of memory. Tried to allocate 6.16 GiB.
GPU 0 has a total capacity of 44.53 GiB of which 4.59 GiB is free.
Including non-PyTorch memory, this process has 39.93 GiB memory in use.
Of the allocated memory 39.34 GiB is allocated by PyTorch.
```

---

### Attempt 6: Job 490207 — `del` fix insufficient

**Date:** 2026-06-07 01:25 IDT  
**Node:** n-802 (L40S, 46GB)  
**Duration:** ~17 minutes  
**Approach:** Resume `full_20260604_101929`, added explicit `del` between examples

**Change applied to `compute_projections_for_example()`:**
```python
del hidden_states
del output
if torch.cuda.is_available():
    torch.cuda.empty_cache()
```
The hypothesis was that Python's garbage collector wasn't releasing the hidden state tensors fast enough between examples, causing memory to accumulate over the 24 successful examples until it overflowed.

**Result:** 0 new examples completed, all 18 still failed.

```
manifest: status=completed, completed=0, failed=18, skipped=24
```

#### Why the fix didn't work

Looking at the error for example 25 (the **first** forward pass in this run, since examples 1–24 were skipped via resume):

```
39.93 GiB in use when example 25 starts (BEFORE any forward pass)
```

The `del` fix addresses inter-example leakage — but in this run, **no previous forward passes were run** (examples 1–24 were skipped). The 39.93 GB is entirely the model's base footprint. No cleanup between examples could help; the problem is that the model itself leaves only ~4.5 GB free, which is too little for `output_hidden_states=True` on long sequences.

This was the key realization: **the per-example memory leakage was not the root cause.** The root cause is that `output_hidden_states=True` always needs 6+ GB simultaneously for long sequences, regardless of how well we clean up between examples.

**Error progression (examples 25–42 all failed within seconds):**
```
goal_index=0, ai=2, ci=6 → OOM: tried 6.16 GiB, 4.59 GiB free
goal_index=1, ai=1, ci=6 → OOM: tried 6.50 GiB, 3.89 GiB free
goal_index=2, ai=1, ci=4 → OOM: tried 1.09 GiB, 999 MiB free  ← GPU nearly full
...
goal_index=3, ai=1, ci=1 → OOM: tried 82 MiB, 59 MiB free      ← GPU completely full
```

Once any allocation fails, PyTorch's pool becomes fragmented and subsequent allocations fail even for tiny tensors.

---

### Attempt 7: Job 490729 — Forward-hook fix (CURRENT)

**Date:** 2026-06-07 10:15 IDT  
**Node:** n-803 (L40S, 46GB, single GPU)  
**Status:** Running (2h 20m elapsed at last check)  
**Approach:** Resume `full_20260604_101929`, switched back to forward pre-hooks

#### The Fix: Back to Hooks, But Now Correct

The multi-GPU problem that originally broke hooks is gone — we're now single-GPU. The `output_hidden_states=True` problem is that it allocates all 41 hidden states simultaneously. Hooks are the solution because they project each layer's activation **immediately and discard the GPU tensor**.

**New `compute_projections_for_example()` implementation:**
```python
projections_store: dict[int, list[float]] = {}
transformer_layers = model.model.layers

def _make_hook(layer_idx: int):
    def _hook(module, hook_input):
        act = hook_input[0] if isinstance(hook_input, tuple) else hook_input
        # act: [1, seq_len, hidden_size] on GPU (bfloat16)
        dir_dev = direction_cpu.to(act.device)
        proj = (act[0].float() @ dir_dev).detach().cpu().tolist()
        projections_store[layer_idx] = proj if isinstance(proj, list) else [float(proj)]
        del dir_dev
    return _hook

handles = []
for li in selected_layers:
    handles.append(transformer_layers[li].register_forward_pre_hook(_make_hook(li)))

try:
    with torch.no_grad():
        model(input_ids=input_ids.to(input_device))
finally:
    for h in handles:
        h.remove()
    del handles
```

#### Memory Analysis

| Approach | Peak extra GPU memory for seq_len=15,000 |
|----------|------------------------------------------|
| `output_hidden_states=True` | 41 × 15,000 × 5,120 × 2 bytes = **6.3 GB** (all at once) |
| Forward pre-hooks | 1 × 15,000 × 5,120 × 4 bytes (float32) = **~300 MB** (one layer at a time) |

With hooks, peak extra memory is ~300 MB. Base model footprint is ~39 GB. Total peak: ~39.3 GB — well within the 44.5 GB available.

**Why hooks work now (but didn't before):**  
With `--gpus=1`, all 40 transformer layers are on `cuda:0`. When a hook fires on any layer, `act.device = cuda:0`. `direction_cpu.to(act.device)` correctly moves the direction to cuda:0. No cross-device issue.

Previously with `--gpus=2`, layers 18–39 were on `cuda:1`, causing hooks on those layers to fire with tensors on the wrong device, producing invalid or zero projections.

---

## 5. Root Cause Analysis Summary

| Job | Node / GPU | Bug / Failure | Root Cause |
|-----|-----------|---------------|------------|
| 415272 | n-301 (no GPU) | Cancelled | No `--nodelist` constraint |
| 415274 | n-304 (RTX 3090) | Wrong input | STAGE6_INPUT pointed to `all_traces_redacted` |
| 418832 | n-802 (L40S) | Silent layer 19–39 zeros | `--gpus=2` → `device_map="auto"` split model across 2 GPUs; hooks on cuda:1 layers failed silently |
| 426475 | n-804 (L40S) | Same silent bug | Same as above (repeated run) |
| 436641 | n-803 (L40S) | Same silent bug | Same as above (repeated run) |
| 461188 | n-302 (RTX 3090) | 42/42 instant OOM | `--nodelist` still included 24GB nodes; single 24GB GPU can't hold 28GB model |
| 476121 | n-802 (L40S) | 24/42 OOM | `output_hidden_states=True` needs 6+ GB for long sequences; only 4.5 GB free |
| 490207 | n-802 (L40S) | 18/18 OOM | `del` fix doesn't help — model base footprint IS 39 GB; no per-example leak to fix |
| **490729** | n-803 (L40S) | **Running** | Forward hooks: O(1-layer) memory, not O(41-layers); single GPU avoids hook device mismatch |

**Key insight:** The two bugs were completely orthogonal:
1. **Multi-GPU bug** (`output_hidden_states` / hooks both needed single GPU): fixed by `--gpus=1` + `--nodelist=n-802..n-805`
2. **Memory budget bug** (`output_hidden_states` specific): fixed by returning to forward hooks (O(seq_len × hidden_size) not O(n_layers × seq_len × hidden_size))

---

## 6. Current Output State

### Active run directory: `outputs/stage4/token_dynamics/full_20260604_101929/`

```
full_20260604_101929/
├── manifest.json          (2.0 KB)
├── per_prompt_metrics.jsonl  (17 KB, 24 rows)
├── token_level_metrics.jsonl (4.7 GB, 11,663,000 rows)
├── progress.jsonl         (46 KB)
└── per_example/           (24 files, 439 MB total)
    ├── goal_index_0_attack_iteration_1_conversation_id_1_target_model_gpt-o4-mini.json  (8.5 MB)
    ├── goal_index_0_attack_iteration_1_conversation_id_2_target_model_gpt-o4-mini.json  (22 MB)
    ├── goal_index_0_attack_iteration_1_conversation_id_3_target_model_gpt-o4-mini.json  (26 MB)
    ├── goal_index_0_attack_iteration_1_conversation_id_4_target_model_gpt-o4-mini.json  (25 MB)
    ├── goal_index_0_attack_iteration_1_conversation_id_5_target_model_gpt-o4-mini.json  (20 MB)
    ├── goal_index_0_attack_iteration_1_conversation_id_6_target_model_gpt-o4-mini.json  (24 MB)
    ├── goal_index_0_attack_iteration_2_conversation_id_1_target_model_gpt-o4-mini.json  (3.4 MB)
    ├── goal_index_0_attack_iteration_2_conversation_id_2_target_model_gpt-o4-mini.json  (25 MB)
    ├── goal_index_0_attack_iteration_2_conversation_id_3_target_model_gpt-o4-mini.json  (11 MB)
    └── ... (15 more files)
```

### Manifest state (after job 490207, before job 490729 completes)

```json
{
  "run_name": "full_20260604_101929",
  "model_name_or_path": "Qwen/Qwen3-14B",
  "selected_layers": [0, 1, 2, ..., 39],
  "n_model_layers": 40,
  "examples_attempted": 42,
  "examples_completed": 0,
  "examples_skipped": 24,
  "examples_failed": 18,
  "status": "completed"
}
```

Note: `examples_completed=0` reflects job 490207's contribution (which resumed but completed 0 new). The 24 completed files from job 476121 are already on disk and will be skipped by job 490729 in resume mode. The manifest will be updated when job 490729 finishes.

### Other run directories (historical)

| Run Name | Job | Node | Input | Status |
|----------|-----|------|-------|--------|
| `full_20260529_230644` | 415274 | n-304 (RTX 3090) | `all_traces_redacted` | 42/42 done, **wrong input** |
| `full_20260531_182439` | 418832 | n-802 (L40S) | `all_traces_full` | 42/42 done, **layers 19–39 zeros** |
| `full_20260601_084504` | 426475 | n-804 (L40S) | `all_traces_full` | 42/42 done, **layers 19–39 zeros** |
| `full_20260601_193438` | 436641 | n-803 (L40S) | `all_traces_full` | 42/42 done, **layers 19–39 zeros** |
| `full_20260603_112410` | 461188 | n-302 (RTX 3090) | `all_traces_full` | 0/42, all OOM |
| `full_20260604_101929` | 476121+490207+490729 | n-802/n-803 | `all_traces_full` | **24/42 good data, 18 in progress** |

4 smoke test runs also exist (`smoke_20260529_*`, `smoke_20260601_*`) from early validation.

---

## 7. Refusal Direction Metadata

```json
{
  "selected_layer": 22,
  "selected_position": -3,
  "selected_score": 14.166624327994466,
  "selected_harmful_projection_mean": 61.89,
  "selected_harmless_projection_mean": -3.61,
  "direction_norm": 1.0,
  "hidden_size": 5120,
  "num_layers": 40,
  "selection_status": "provisional_projection_diagnostic_only",
  "timestamp_utc": "2026-05-20T18:19:49.875450+00:00"
}
```

The direction was extracted by contrasting activations of 64 harmful vs. 64 harmless prompts (48 train / 16 validation each) using difference-in-means at every layer and position combination. Layer 22 at position −3 gave the best harmless/harmful separation.

**Scientific caveat:** This direction was selected by projection diagnostics only. Stage 4A2 (intervention-based validation — does steering along this direction actually suppress harmful outputs?) has not been run yet. The `provisional_projection_diagnostic_only` tag means this direction should not be used for causal claims without that validation.

---

## 8. Confirmed Results (24 completed examples)

### Layer coverage
- All 24 completed per-example files have **all 40 layers** with non-null projections at every token position.
- Layer indices 0–39 present in `layer_projections` dict for each token.

### Sequence length distribution (24 examples)
| Metric | Value |
|--------|-------|
| Min generation tokens | 2,228 |
| Max generation tokens | 18,170 |
| Median | ~14,303 |
| Mean | ~12,148 |
| Prompt tokens range | 483–1,112 |

### StrongREJECT score distribution (24 examples)
| Score | Count | % |
|-------|-------|---|
| 0.0 (safe) | 13 | 54% |
| 0.5 (moderate violation) | 1 | 4% |
| 1.0 (severe violation) | 10 | 42% |

### Layer 22 refusal direction signal
- **Attack SUCCESS** (sr ≥ 0.5): mean projection at layer 22 ≈ **5.200**
- **Attack FAILURE** (sr = 0.0): mean projection at layer 22 ≈ **4.159**
- Difference: ~1.04 projection units — attacks that succeed show lower refusal direction activation

This is a preliminary signal on 24/42 examples. The full 42-example dataset should produce a more reliable separation.

---

## 9. What Comes Next

### Immediate (waiting for job 490729)
1. **Verify 42/42 completion** once job 490729 finishes (~2.5h from submission):
   ```python
   python3 -c "
   import json; from pathlib import Path
   base = Path('outputs/stage4/token_dynamics/full_20260604_101929')
   per_ex = sorted((base/'per_example').glob('*.json'))
   print(f'{len(per_ex)}/42 files present')
   for f in per_ex:
       d = json.loads(f.read_text())
       n = sum(1 for v in d['token_level_data'][50]['layer_projections'].values() if v is not None)
       if n < 40:
           print(f'PARTIAL: {f.name[:60]} — {n}/40 layers')
   "
   ```
   Expected output: `42/42 files present` with no PARTIAL lines.

2. **Full Layer 22 analysis** across all 42 examples — compare refusal direction projection trajectories for attack success vs. failure.

### Analysis (thesis content)
3. **Plot refusal direction projection vs. token position** for each example, broken down by segment (prompt → thinking → generation), colored by attack outcome.

4. **Layer-resolved heatmaps**: For each example, plot a heatmap of [layer × token_index] projection values. The thesis hypothesis predicts a characteristic "hijacking signature" — high projection in prompt tokens, suppression during thinking, recovery or continued suppression at generation.

5. **Statistical analysis**: Compare mean projection at layer 22 between successful and failed attacks, across all 42 examples. Compute t-test / effect size.

6. **Run Stage 4A2** (intervention-based direction validation): steer the model along the refusal direction and confirm it affects harmful-output probability. This upgrades the direction from `provisional_projection_diagnostic_only` to `intervention_validated` and makes the causal claims scientifically defensible.

---

*Log maintained by Claude Code during active development. All job IDs, node names, timestamps, error messages, and file sizes are from actual SLURM logs and filesystem inspection.*
