# Environment & Repository Audit — Doublespeak Causality

**Date:** 2026-07-26
**Auditor:** Claude (main loop), for Omer Yosef
**Repo:** `/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood`
**Git HEAD at audit:** `f646dd4` (branch `main`)

This document satisfies plan §4 (inspect before changing) and §29.1–29.3. All entries are verified by direct inspection, not assumption.

## 1. Python environment

| Item | Value |
|---|---|
| Conda env to use | `poc_stage2` (the plan's `poc_stage2` env is present and current) |
| Python | 3.11 (env) / base is 3.13 |
| torch | 2.7.1+cu126 |
| transformers | **5.12.1** (⚠ major v5 — reference code written for 4.35; validate API in smoke test) |
| CUDA available | yes |
| Activate | `source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh && conda activate poc_stage2` |

## 2. Secrets (in `.env`, loaded via `set -a; source .env; set +a`)

- `HF_TOKEN` — **verified working**, has manual-gated access to `meta-llama/Llama-3.1-8B-Instruct` (4 safetensors shards, sha `0e9e39f249a1`).
- `OPENAI_API_KEY` — present (usable for StrongReject rubric judge / GPT-4o-mini context generation).
- `GEMINI_API_KEY` — present.

## 3. Models

| Model | Cached? | Notes |
|---|---|---|
| `meta-llama/Llama-3.1-8B-Instruct` | **NO — downloading** (bg PID logged in `logs/llama_download.log`) | PRIMARY mechanistic model. Confirmed as the paper's / official-repo default (`example_usage.py --model-name meta-llama/Llama-3.1-8B-Instruct`). |
| `google/gemma-2b` | yes (4.7G) | not a plan target (base, not IT, not gemma-3) |
| `google/gemma-4-E4B-it` | yes (31M — metadata only?) | plan lists **Gemma-3** family; this is gemma-4/3n E4B. **Discrepancy to resolve** (see PAPER_REPRODUCTION_NOTES). |
| `Qwen/Qwen3-14B` | yes (32G) | prior CoT/GCG work; not a Doublespeak target |
| `qylu4156/strongreject-15k-v1` | yes | StrongReject fine-tuned judge — reusable for eval |

**Blocker note:** none of the plan's Gemma-3 checkpoints (270M/1B/4B/27B-IT) nor Llama-3.3-70B are cached. Only Llama-3.1-8B is being fetched now (primary). Secondary models deferred per plan §3/§14 (establish 8B effect first).

## 4. Cluster / SLURM (verified via `sinfo`, `sacctmgr`)

- **Account:** `gpu-research` (also have `gpu-students`).
- **Partitions available to me:** `killable`, `cpu-killable`, `gpu-sharifm`, `studentkillable`.
- **L40S nodes** (house standard per memory — "L40S only"): `n-801, n-802, n-803, n-804, n-805`, `t-806` (8×l40s each) on `killable`.
- Other GPUs on killable: 2080/3090/a5000/a6000/v100/quadro; h100/b200/h200 on dedicated partitions.
- **User hard rules (from memory, must honor):** no SLURM job deps; **max 6 concurrent jobs**; no trimming/subsampling of data silently; **L40S only** for mechanistic runs (a5000/a4000 abort guard in template); bfloat16 + default SDPA (do not disable flash).

### Reusable SLURM template conventions (`slurm_scripts/submit_qwen_ae.sh`)
- `#SBATCH --account=gpu-research --partition=killable --nodelist=n-801,n-802,n-803,n-805 --gpus=1 --cpus-per-task=8 --mem=64G`
- Array throttle `%3` to stay ≤6 concurrent.
- `set -euo pipefail`; GPU-type guard aborts if not L40S.
- Env setup: `HF_HOME=$PROJECT_DIR/.cache/huggingface`, `HF_HUB_CACHE`, `TORCH_HOME`, `TRITON_CACHE_DIR`, `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True`.
- Sources `.env`, activates `poc_stage2`, prints hostname/date/nvidia-smi/git.

## 5. Reusable code (plan §4.3 — reuse over reimplement)

### From official paper repo `doublespeak/` (detached clone)
- `doublespeak_attack.py` — `DoublespeakAttack`: builds in-context demo sentences + substituted query. **Has bugs** in `main()`/CLI (`harmful_query` undefined, missing `batch_create_prompts`, wrong kwargs) but the core `create_malicious_prompt` / `generate_in_context_examples` are usable. Does **NOT** apply chat template (raw text) — deviation to fix.
- `mech_interp.py` — `LogitLens` (hidden→vocab projection w/ final norm) and `Patchscopes` (extract rep at source layer/token → forward-hook patch into inspection prompt → read benign/malicious prob). **Reuse directly.** Note: `main()` calls a non-existent `analyze_representation_shift` (broken path); use the class methods, not the CLI.
- `example_usage.py`, `test_script.py` — end-to-end driver + tests (reference for expected outputs).

### From existing thesis repo `poc_stage4/` (mechanistic toolkit — high reuse value)
- `run_causal_tracing.py`, `run_p11_controlled_patching.py`, `run_generation_phase_patching.py` — activation patching patterns + hooks.
- `run_attention_extraction.py`, `run_head_ablation.py` — attention capture + knockout.
- `run_subspace_ablation.py`, `replicate_standard_refusal_direction.py`, `replicate_qwen_rd_exact.py` — refusal-direction machinery (for §10.4 factorial).
- `audit_model_architecture.py` — layer/module introspection.
- Model-load house standard: `AutoModelForCausalLM.from_pretrained(..., torch_dtype=torch.bfloat16, device_map="auto", attn_implementation="sdpa")`, `pad_token_id=tokenizer.eos_token_id` for generation.
- `strong_reject/` — StrongReject evaluation (plan §16 metric).

## 6. Key deviations from reference to record (plan §5.14)

1. **dtype:** reference uses `float16`; house standard + memory = **bfloat16 + SDPA** on L40S. Using bfloat16 for consistency with prior mechanistic work and numerical stability. (Impact: minor rep-value differences vs paper's fp16; both non-quantized so representation comparisons valid.)
2. **Chat template:** reference feeds raw text to the tokenizer. Paper models are instruction-tuned chat models; plan §5.9/§5.11 require the official chat template. We will apply `apply_chat_template` and re-validate target-token positions *after* templating.
3. **EOS handling:** reference `generate` sets `max_length=200, do_sample=False` and does not preserve list-valued EOS. We preserve native `generation_config.eos_token_id` (memory: prior severe bug from EOS overwrite).
4. **transformers 5.x:** reference targets 4.35; verify `output_hidden_states`, `.model.layers`, `.model.norm`, hook output tuple shape still hold (smoke test).

## 7. Constraint that shapes orchestration (memory: cyber-safeguard)

Subagents that read jailbreak/harmful **text** get terminated by the cluster cyber classifier. Therefore: all harmful-text-touching work (prompt construction, generations, attack code) stays in the **main loop**; only benign/structural/scalar-numeric tasks are delegated to subagents. This limits naive parallel fan-out for this project — documented so the choice is not mistaken for under-use of parallelism.
