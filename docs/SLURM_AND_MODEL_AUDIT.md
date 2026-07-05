# Stage AE — SLURM and Model Audit

Written during the poc_stage_ae build session (2026-07-02). Documents the exact
SLURM configuration and model-loading conventions reused from prior stages,
and any deviations made.

## Model configuration (verified against repo, used directly — no re-derivation)

| Field | Qwen3-14B | Gemma4-E4B-it |
|---|---|---|
| HF model id | `Qwen/Qwen3-14B` | `google/gemma-4-E4B-it` |
| Revision | `40c069824f4251a91eefaf281ebe4c544efd3e18` | (unpinned) |
| n_layers | 40 | 42 |
| d_model | 5120 | 2560 |
| Loader | `poc_stage4.qwen3_model.load_qwen3_model` | `poc_stage4.qwen3_model.load_gemma4_model` |
| dtype | `torch_dtype="auto"` (bf16) | `torch_dtype="auto"` (bf16) |
| device_map | `"auto"` | `"auto"` |
| attn_implementation | `"sdpa"` | `"sdpa"` |
| Thinking start marker | `<think>` | `<\|channel>thought` |
| Thinking end marker | `</think>` | `<channel\|>` |

Both loaders return a shared `Qwen3Model` wrapper (`poc_stage4/qwen3_model.py`);
`replay_hidden_states.py` and `run_ae_generation.py` call these loaders
unmodified — no new loading code was written.

## SLURM configuration reused verbatim

Base templates: `slurm_scripts/stage4_8_cond_g_goals4_10_qwen3_l40s.slurm` and
`..._gemma4.slurm`.

Reused as-is in all 7 new `.slurm` scripts:
- `--account=gpu-research --partition=killable`
- `--nodelist=n-801,n-802,n-803,n-805` (all confirmed L40S 46GB)
- Runtime GPU-type guard: aborts if `nvidia-smi` reports A5000/A4000/A2000
  (prevents the CPU-offload pathology previously hit on n-501/n-601).
- `conda activate poc_stage2`
- `HF_HOME` / `HF_HUB_CACHE` / `TORCH_HOME` / `TRITON_CACHE_DIR` under
  `$PROJECT_DIR/.cache/...`
- `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True`
- `source $PROJECT_DIR/.env` for `OPENAI_API_KEY` (scoring jobs only)

## New array-indexing scheme

Generation and hidden-replay/scoring arrays use different indexing conventions
because they operate over different units of work:

- **Generation** (`submit_{qwen,gemma}_ae.sh`): `task_id = goal_index*4 + cond_idx`,
  `cond_idx` in `{0:A, 1:D, 2:E, 3:G}`. 11 goals x 4 conditions = 44 tasks/model.
  This differs from the D/G row *count* per goal (33 rows total across D+G for
  11 goals) because one array task processes **all seeds for one
  (goal_index, condition) cell** in a single process (matches the existing
  `run_repeated_generations.py`-style "load model once per array task, loop
  over seeds" convention) — so D and G cells still get their own array slot
  even though they only contain 3 rows each (vs 60 for A/E cells).
- **Hidden replay / scoring** (`submit_{qwen,gemma}_hidden_replay.sh`,
  `submit_{qwen,gemma}_scoring_analysis.sh`): array over **sorted generation
  shard files** (`find shards/*.jsonl | sort`), so `task_id` indexes directly
  into the list of shard files that generation actually produced. This is more
  robust than a fixed goal/condition formula because it naturally skips any
  cell that produced zero rows (e.g. all rows in a G-cell failed) without a
  dedicated "no shard" branch beyond the existing bounds check.

Throttle values (`%N`) — Qwen `%4`, Gemma `%3` — copied directly from the
`stage4_8_cond_g_goals4_10_*` precedent scripts' proven-safe concurrency.

## Wall-time choices

| Script | Wall time | Rationale |
|---|---|---|
| `submit_{qwen,gemma}_ae.sh` | 3h | matches `stage4_8_cond_g_*` precedent (generation-only, no hidden-state work) |
| `submit_{qwen,gemma}_hidden_replay.sh` | 4h | conservative starting point per plan; full-sequence (up to 32768-token) forward passes at 40-42 layers are the dominant unknown cost — **must be tuned after the Stage 8 smoke test**, not yet empirically validated (no GPU access in this build session) |
| `submit_{qwen,gemma}_scoring_analysis.sh` | 1h | CPU-only, StrongREJECT API calls dominate; matches plan's 1h estimate |
| `submit_combined_analysis.sh` | 1h | CPU-only audit pass |

## `RUN_DIR` / `MANIFEST_PATH` propagation

All generation and hidden-replay/scoring scripts require `RUN_DIR` (and
generation additionally requires `MANIFEST_PATH`) passed via
`sbatch --export=ALL,RUN_DIR=...,MANIFEST_PATH=...` — scripts hard-fail with a
clear error message if these are unset, rather than silently defaulting to a
stale path (a deliberate deviation from the older scripts, which computed
`RUN_DIR` internally with a `${RUN_DIR:-default}` fallback; the AE run's
single-frozen-timestamp requirement across many sessions makes an implicit
default riskier here).

## Deviations from plan / precedent

1. The plan describes "3h for generation... 4h for hidden replay... 1h for
   scoring/analysis" — implemented exactly as specified.
2. `run_ae_generation.py` uses `max_new_tokens=32768` uniformly for A/D/E/G
   (the plan says "32768 for A/D, model-appropriate default for E/G — reuse
   whatever run_repeated_generations.py uses for E"). Audited: every
   condition-E and condition-G manifest builder in `poc_stage4_8/` (
   `build_extended_replication_prompts.py`, `build_manifest_condition_g.py`,
   `build_repeated_generation_manifest.py`) sets `max_new_tokens=32768`
   uniformly across all conditions — there is no smaller E/G-specific default
   anywhere in the reused code. Using 32768 for all four conditions is
   therefore the correct application of "reuse whatever run_repeated_generations.py
   uses for E," not a deviation from it.
