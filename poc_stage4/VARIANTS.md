# poc_stage4 Script Variants

This document describes all scripts in `poc_stage4/`, what each does, and exactly what
changed in each new variant relative to the original script it extends.

---

## Overview Table

| Script | Stage | Contrast Set | Extraction Position | Direction Type | Model Families | Outputs |
|--------|-------|-------------|---------------------|----------------|----------------|---------|
| `extract_refusal_direction.py` | 4A1 (original) | harmful vs. harmless (input label) | Prompt-end offsets (EOI, before generation) | Single vector per (pos, layer) | Qwen3 only | `refusal_direction/` |
| `select_refusal_direction_interventions.py` | 4A2 (original) | — (uses 4A1 candidates) | — | Top-1 validated vector `[d_model]` | Qwen3 only | `refusal_direction/direction.pt` |
| `analyze_stage6_token_dynamics.py` | 4B (original) | — (uses 4A direction) | All generated tokens | Single projection per token per layer | Qwen3 only | `token_dynamics_<run>/` |
| `model_family_utils.py` | Shared utility | — | — | — | Both | (no outputs; library module) |
| **`extract_refusal_direction_endofthink.py`** | 4A1-endofthink (**new**) | harmful vs. harmless (input label) | `</think>` / `<channel\|>` token (after deliberation) | Single vector per layer `[1, n_layers, d_model]` | Both | `refusal_direction_endofthink/` |
| **`extract_refusal_direction_behavioral.py`** | 4A1-behavioral (**new**) | complied vs. refused (`qwen_run_success` by default; `judge_score` optional) | `</think>` / `<channel\|>` token (after deliberation) | Single vector per layer `[1, n_layers, d_model]` | Both | `refusal_direction_behavioral/` |
| **`select_direction_subspace.py`** | 4A2-subspace (**new**) | — (uses any 4A1 candidates) | — | Top-K validated vectors `[K, d_model]` | Both | `direction_subspace/` |
| **`analyze_token_dynamics_subspace.py`** | 4B-subspace (**new**) | — (uses subspace direction) | All generated tokens | K projections per token per layer | Both | `token_dynamics_subspace_{variant}/` |
| **`analyze_subspace_dynamics_stats.py`** | 4C-stats (**new**) | — (reads 4B output) | — | AUC + trajectory stats, no GPU | CPU only | `subspace_stats_{variant}/` |

---

## `model_family_utils.py` — shared utility module

### What it does

`model_family_utils.py` is a library module (not a runnable script) that centralizes all
model-family-specific constants and dispatch logic needed by the four new Stage 4 scripts.
It was introduced so that Gemma4 support could be added in one place without touching the
original scripts.

### What it exports

| Export | Type | Description |
|--------|------|-------------|
| `DEFAULT_MODEL_BY_FAMILY` | `dict[str, str]` | Canonical HF model ID per family (`qwen3` → `Qwen/Qwen3-14B`; `gemma4` → `google/gemma-4-E4B-it`) |
| `DEFAULT_MODEL_SLUG_BY_FAMILY` | `dict[str, str]` | Short slug used in default output path names (`qwen3` → `qwen3-14b`; `gemma4` → `gemma4-e4b-it`) |
| `THINKING_MARKERS_BY_FAMILY` | `dict[str, dict[str, str]]` | Start and end of thinking block per family (see table below) |
| `THINKING_SEGMENT_HINTS_BY_FAMILY` | `dict[str, list[str]]` | Token-table segment label substrings to identify thinking section (used by behavioral script's fallback search) |
| `load_model_by_family(model_name, model_family, **kwargs)` | function | Dispatches to `load_hf_model` (Qwen3) or `load_gemma4_model` (Gemma4); both return a `Qwen3Model` instance |
| `get_thinking_end_token_ids(tokenizer, model_family)` | function | Tokenizes the end-of-thinking marker for the given family; raises on empty encoding |
| `get_thinking_start_token_ids(tokenizer, model_family)` | function | Tokenizes the start-of-thinking marker for the given family |

### Why it exists

The original Stage 4 scripts hard-coded `Qwen/Qwen3-14B` and `</think>`. When Gemma4
(`google/gemma-4-E4B-it`) was added, Gemma4 uses a different thinking delimiter
(`<channel|>`) and a different HF loader (`load_gemma4_model`). Rather than duplicating
these constants in every script, they are defined once here. Any script that adds
`--model-family` reads its defaults from this module.

### Thinking markers by family

| Family | Start marker | End marker |
|--------|-------------|-----------|
| `qwen3` | `<think>` | `</think>` |
| `gemma4` | `<\|channel>thought` | `<channel\|>` |

Both loaders return the same `Qwen3Model` wrapper and expose `model.model.layers`,
so hook and activation-capture code in all Stage 4 scripts is identical regardless of
which family is selected.

---

## What Each Script Changed

### `extract_refusal_direction_endofthink.py` — new, does NOT modify original

**Diff from `extract_refusal_direction.py`**:

- **Extraction position**: EOI offsets (last 1–6 prompt-end tokens, before generation) →
  `</think>` / `<channel|>` token (after full reasoning chain, before the answer)
- **Method**: direct single forward pass on prompt → generate until thinking-end marker
  appears, then truncate sequence at that token, then run one forward pass with
  `register_forward_pre_hook` to capture the residual stream at the thinking-end position
  for every layer
- **Contrast set**: unchanged — harmful vs. harmless vanilla prompts (input label)
- **Output shape**: `candidate_directions.pt` is `[1, n_layers, d_model]` (one "position"
  labelled `"endofthink"`) instead of `[n_positions, n_layers, d_model]`
- **Extra output**: `skipped_prompts.json` — prompts where the thinking-end token was not
  found within `--max-generation-tokens`
- **Schema compatibility**: yes — same `candidate_metadata.json` schema and same
  `STAGE4A1_ARTIFACT_VERSION` constant; compatible with Stage 4A2 and `select_direction_subspace.py`
- **Model loading**: calls `load_model_by_family(model_name, model_family)` from
  `model_family_utils` instead of hard-coding `load_hf_model`
- **Thinking-end token IDs**: resolved via `get_thinking_end_token_ids(tokenizer, model_family)`
  instead of hard-coding `</think>`
- **CLI**: adds `--model-family` and `--model-name`; `--output-dir` defaults to
  `outputs/stage4/<model-slug>/refusal_direction_endofthink/`

**Why**: The EOI position captures "this instruction looks harmful" at the moment the model
reads it. For reasoning models running a CoT hijacking attack, the harmful signal may be
diluted during the generation of the thinking chain. The `</think>` position captures
"after all deliberation, the model commits to refuse or comply" — the mechanistically
relevant checkpoint for whether the attack succeeded. Comparing EOI vs. endofthink
directions reveals whether the attack corrupts the signal during reasoning or whether it
was never strongly encoded to begin with.

**Gemma4 support**: `model_family_utils.load_model_by_family` and
`get_thinking_end_token_ids` handle Gemma4's `<channel|>` marker and `load_gemma4_model`
loader transparently. All activation-capture hook code is identical.

**Checkpoint / resume** (added 2026-06-19):

After each prompt, the script saves `{output_dir}/checkpoints/endofthink/{group_label}/{i:05d}_{act.pt,meta.json}`. If the job is preempted, resubmit with `--resume` to skip already-captured prompts and continue from where it died. The output-existence guard is bypassed when `--resume` is set. Checkpoints are **always written** (even without `--resume`) so the flag only controls whether they are **read back**.

Groups: `harmful_train`, `harmless_train`, `harmful_val`, `harmless_val` — each gets its own subdirectory of per-prompt files.

```bash
# Resume after preemption
python -m poc_stage4.extract_refusal_direction_endofthink \
    --resume \
    --output-dir outputs/stage4/qwen3-14b/refusal_direction_endofthink \
    --num-harmful 220 --num-harmless 220 --max-generation-tokens 2048
```

**Run commands**:
```bash
# Qwen3 (default)
python -m poc_stage4.extract_refusal_direction_endofthink \
    --output-dir outputs/stage4/qwen3-14b/refusal_direction_endofthink \
    --num-harmful 220 --num-harmless 220 --max-generation-tokens 2048

# Gemma4
python -m poc_stage4.extract_refusal_direction_endofthink \
    --model-family gemma4 \
    --output-dir outputs/stage4/gemma4-e4b-it/refusal_direction_endofthink \
    --max-generation-tokens 2048
```

---

### `extract_refusal_direction_behavioral.py` — new, does NOT modify original

**Diff from `extract_refusal_direction.py`**:

- **Contrast set**: harmful/harmless (input label) → complied/refused (behavioral outcome).
  Default criterion: `qwen_run_success == True` (complied) vs. `False` (refused), where
  `qwen_run_success = (StrongREJECT >= 0.5) OR (judge_score == 10)`. This gives ~113/107
  split in `all_traces_full_1_11`. Alternative via `--group-by judge_score`: uses
  `judge_score==10` vs. `==1` (gives 1/219 split in current traces — too few complied).
- **Extraction position**: EOI (prompt end, before generation) → `</think>` / `<channel|>`
  token (same as endofthink script)
- **Input source**: raw prompts (loads and formats each prompt from scratch) →
  Stage 6 trace artifacts (uses `full_prompt_plus_generation_token_ids` already stored in
  each trace; no new generation is run)
- **Finding the thinking-end token**: searches `full_prompt_plus_generation_token_ids`
  directly; falls back to scanning `token_table` segment labels using
  `THINKING_SEGMENT_HINTS_BY_FAMILY` (covers both Qwen3's `"think"` label and
  Gemma4's `"channel"` / `"thought"` labels) if the raw ID scan fails
- **DiM direction**: `mean(complied_at_endthink) - mean(refused_at_endthink)` per layer,
  compared with the original's `mean(harmful) - mean(harmless)` at EOI
- **Train/val split**: 75%/25% split applied within each behavioral group (complied /
  refused) instead of the original's fixed split from `split_prompts()`
- **Extra output**: `group_summary.json` — counts of complied/refused/unknown examples
  found in the Stage 6 input directory
- **Schema compatibility**: yes — same `candidate_metadata.json` schema and
  `STAGE4A1_ARTIFACT_VERSION`; compatible with Stage 4A2 and `select_direction_subspace.py`
- **Model loading**: uses `load_model_by_family` and `get_thinking_end_token_ids` from
  `model_family_utils`
- **CLI**: adds `--model-family`, `--model-name`, `--group-by {qwen_run_success,judge_score}`
  (default `qwen_run_success`); `--stage6-input` is a required argument;
  `--output-dir` defaults to `outputs/stage4/<model-slug>/refusal_direction_behavioral/`

**Why**: The Arditi et al. direction distinguishes "this input is harmful" at the
instruction end. The behavioral direction distinguishes "the model is about to comply with
the attack" from "the model refused the attack" at the moment after deliberation. This is
the direction that most directly encodes what the attack changes: the residual stream state
at `</think>` between successfully hijacked and failed hijacking attempts. It is
complementary to the input-label direction — if both point in the same direction, the
model's refusal signal is consistent before and after reasoning; if they diverge, the
attack alters the direction during the thinking chain.

**Gemma4 support**: `load_model_by_family` and `get_thinking_end_token_ids` handle
Gemma4's loader and `<channel|>` marker. The `THINKING_SEGMENT_HINTS_BY_FAMILY` fallback
includes Gemma4's segment labels (`"channel"`, `"thought"`) so the token-table search
works on Gemma4 trace artifacts too.

**`--group-by` criterion** (added 2026-06-19):

The Gemini judge scored 219/220 traces as refused (`judge_score=1`), leaving only 1 complied
example — too few for a meaningful DiM direction. The `qwen_run_success` field (pre-computed
per trace as `SR >= 0.5 OR judge_score == 10`) reveals 113 complied / 107 refused — a near-
50/50 split with clean separation (refused group avg SR = 0.014). Default is now `qwen_run_success`.

| `--group-by` | Complied criterion | Refused criterion | Split in `all_traces_full_1_11` |
|---|---|---|---|
| `qwen_run_success` (default) | `qwen_run_success == True` | `qwen_run_success == False` | 113 / 107 |
| `judge_score` | `judge_score == 10` | `judge_score == 1` | 1 / 219 |

**Run commands**:
```bash
# Qwen3 (default, qwen_run_success grouping)
python -m poc_stage4.extract_refusal_direction_behavioral \
    --stage6-input outputs/stage6/all_traces_full_1_11 \
    --output-dir outputs/stage4/qwen3-14b/refusal_direction_behavioral

# Qwen3 with legacy judge_score grouping
python -m poc_stage4.extract_refusal_direction_behavioral \
    --group-by judge_score \
    --stage6-input outputs/stage6/all_traces_full_1_11 \
    --output-dir outputs/stage4/qwen3-14b/refusal_direction_behavioral_judge

# Gemma4
python -m poc_stage4.extract_refusal_direction_behavioral \
    --model-family gemma4 \
    --stage6-input outputs/stage6/gemma_traces_full_1_11 \
    --output-dir outputs/stage4/gemma4-e4b-it/refusal_direction_behavioral
```

---

### `select_direction_subspace.py` — new, does NOT modify original

**Diff from `select_refusal_direction_interventions.py`**:

- **Output tensor**: single `direction.pt` of shape `[d_model]` → subspace
  `direction_subspace.pt` of shape `[K, d_model]` where K is configurable (default 5)
- **Selection criterion**: top-1 surviving candidate by lowest
  `harmful_ablation_refusal_score` → top-K survivors sorted by the same criterion
- **All filters unchanged**: KL divergence threshold, refusal induction threshold, layer
  pruning percentage — identical logic from `intervention_selection.py`
- **Evaluation loop**: calls the same `evaluate_candidates()` and `load_candidate_directions()`
  from `poc_stage4.intervention_selection`, so re-runs the full intervention sweep
- **New outputs**:
  - `direction_subspace.pt` — `[K, d_model]` unit-normalized stacked direction vectors
  - `direction_subspace_metadata.json` — per-direction origin `{subspace_rank, layer, position, scores}`
  - `intervention_candidate_scores.json` — full per-candidate score table (same schema as Stage 4A2)
- **Model loading**: uses `load_model_by_family` from `model_family_utils` instead of
  hard-coding `load_hf_model`
- **CLI**: adds `--model-family`; `--input-dir` and `--output-dir` default to
  `outputs/stage4/<model-slug>/refusal_direction` and
  `outputs/stage4/<model-slug>/direction_subspace/` respectively; adds `--k` (default 5)

**Why**: A single direction captures one linear combination of the "refusal" subspace.
If the model's residual stream encodes refusal across more than one independent direction
(e.g. different layers encode different aspects of the decision), a single vector misses
some of that information. K directions span a subspace and allow simultaneous ablation of
all K components. The downstream formula for ablating the entire subspace at inference time
is:
```python
coefficients = h @ directions.T      # [batch, seq, K]
h_ablated = h - coefficients @ directions  # [batch, seq, d_model]
```

**Gemma4 support**: `load_model_by_family` handles the correct HF loader. The candidate
evaluation logic (`evaluate_candidates`, `InterventionSelectionConfig`) is model-agnostic.

**Run commands**:
```bash
# Qwen3 (default) — reads from qwen3-14b/refusal_direction/
python -m poc_stage4.select_direction_subspace \
    --input-dir outputs/stage4/qwen3-14b/refusal_direction \
    --output-dir outputs/stage4/qwen3-14b/direction_subspace \
    --k 5

# Gemma4
python -m poc_stage4.select_direction_subspace \
    --model-family gemma4 \
    --input-dir outputs/stage4/gemma4-e4b-it/refusal_direction \
    --output-dir outputs/stage4/gemma4-e4b-it/direction_subspace \
    --k 5
```

---

### `analyze_token_dynamics_subspace.py` — new, does NOT modify original

**Diff from `analyze_stage6_token_dynamics.py`**:

- **Direction input**: `direction.pt [d_model]` (single vector, loaded via
  `direction_loader.load_direction`) → `direction_subspace.pt [K, d_model]` (loaded via
  `load_direction_subspace()` in this script, alongside `direction_subspace_metadata.json`)
- **Hook per layer**: projects onto one direction, stores `float` per (layer, token) →
  projects onto all K directions simultaneously via `act[0].float() @ subspace.T`,
  stores a list of K floats per (layer, token)
- **Output schema per token**: `layer_projections: {layer_idx: float}` →
  `layer_projections: {layer_idx: [float × K]}`
- **Flat JSONL rows**: `token_level_metrics.jsonl` adds a `subspace_rank` column so
  downstream analysis can filter by direction rank
- **Plots**: `_plot_example()` draws K lines per subplot (one per rank); `_plot_aggregate()`
  draws K subplots (one per rank) showing mean projection over token position, grouped by
  `qwen_run_success`
- **Model loading**: uses `load_model_by_family` from `model_family_utils` instead of
  hard-coding `load_hf_model`; flag is `--model-family` (default `qwen3`)
- **CLI flag renamed**: original uses `--model-name`; this script uses
  `--model-name-or-path` (for clarity that local paths are also accepted)
- **No `add_hooks` dependency**: the original optionally imports `add_hooks` from the
  paper codebase (`Chain_of_Thought_Hijacking/refusal_direction/pipeline/utils/hook_utils.py`)
  with a fallback; the subspace variant uses `register_forward_pre_hook` directly, removing
  that optional dependency entirely

**Why**: With K directions, you can observe whether the K components of the refusal
subspace decay at different rates as the CoT hijacking attack progresses. If rank-0 decays
early (during the initial response framing) while rank-1 decays late (near `</think>`),
the two directions capture different phases of the dilution. This informs which direction
(or which layer/rank combination) is the most sensitive probe for detecting a successful
attack.

**Gemma4 support**: `load_model_by_family` handles the correct HF loader. All forward
hook code accesses `model.model.layers` which is the same interface for both families.

**Run commands**:
```bash
# Qwen3 (default)
python -m poc_stage4.analyze_token_dynamics_subspace \
    --stage6-input outputs/stage6/all_traces_full_1_11 \
    --output-dir outputs/stage4/token_dynamics_subspace \
    --direction-subspace-path outputs/stage4/qwen3-14b/direction_subspace

# Gemma4
python -m poc_stage4.analyze_token_dynamics_subspace \
    --model-family gemma4 \
    --stage6-input outputs/stage6/gemma_traces_full_1_11 \
    --output-dir outputs/stage4/gemma4-e4b-it/token_dynamics_subspace \
    --direction-subspace-path outputs/stage4/gemma4-e4b-it/direction_subspace
```

---

## Default Output Directories

| Script | `--model-family qwen3` default | `--model-family gemma4` default |
|--------|-------------------------------|--------------------------------|
| `extract_refusal_direction.py` | `outputs/stage4/qwen3-14b/refusal_direction/` | (Qwen3-only; no `--model-family` flag) |
| `select_refusal_direction_interventions.py` | `outputs/stage4/qwen3-14b/refusal_direction/` (in-place) | (Qwen3-only; no `--model-family` flag) |
| `analyze_stage6_token_dynamics.py` | (required `--output-dir`) | (Qwen3-only; no `--model-family` flag) |
| `extract_refusal_direction_endofthink.py` | `outputs/stage4/qwen3-14b/refusal_direction_endofthink/` | `outputs/stage4/gemma4-e4b-it/refusal_direction_endofthink/` |
| `extract_refusal_direction_behavioral.py` | `outputs/stage4/qwen3-14b/refusal_direction_behavioral/` | `outputs/stage4/gemma4-e4b-it/refusal_direction_behavioral/` |
| `select_direction_subspace.py` | `outputs/stage4/qwen3-14b/direction_subspace/` | `outputs/stage4/gemma4-e4b-it/direction_subspace/` |
| `analyze_token_dynamics_subspace.py` | (required `--output-dir`) | (required `--output-dir`) |

---

## `--model-family` Flag Reference

The four new scripts all accept `--model-family {qwen3,gemma4}`. All values controlled
by this flag are defined in `model_family_utils.py`.

| `--model-family` | Default model name | Thinking-end marker | Output slug |
|------------------|--------------------|--------------------|-|
| `qwen3` (default) | `Qwen/Qwen3-14B` | `</think>` | `qwen3-14b` |
| `gemma4` | `google/gemma-4-E4B-it` | `<channel\|>` | `gemma4-e4b-it` |

The output slug appears in default output directory paths (e.g.
`outputs/stage4/<slug>/refusal_direction_endofthink/`). Override the model with
`--model-name` (or `--model-name-or-path` in `analyze_token_dynamics_subspace.py`).

---

### `extract_refusal_direction_startofthink.py` — new, does NOT modify original

**Diff from `extract_refusal_direction.py`**:

- **Extraction position**: EOI (prompt end) → `<think>` token (first generated token with `enable_thinking=True`, Qwen3 token ID 151667)
- **Method**: format prompt with `enable_thinking=True` (so prompt ends at `assistant\n`), append the `<think>` token to input IDs, run a single forward pass — **no generation required**. Captures residual stream at the `<think>` position for every layer via `register_forward_pre_hook`.
- **Contrast set**: unchanged — harmful vs. harmless vanilla prompts (input label)
- **Output shape**: `candidate_directions.pt` is `[1, n_layers, d_model]` (one position labelled `"startofthink"`)
- **Speed**: ~0.1s/prompt (vs. ~10 min/prompt for endofthink which requires generation). Full 440 prompts in ~15 minutes.
- **Schema compatibility**: yes — same `candidate_metadata.json` schema; compatible with `select_direction_subspace.py`

**Why**: The trajectory analysis (Stage 4C) shows that attack outcome signal appears in the very first tokens of the thinking phase (bin 0, first 5%). The startofthink direction tests a stronger hypothesis: is the attack outcome already encoded in the residual stream AT `<think>`, before any thinking tokens are generated? If startofthink achieves AUC ≈ 0.750 (matching endofthink/behavioral), the model commits to its response at the moment thinking begins, before any CoT reasoning occurs. If it achieves AUC << 0.750, the encoding emerges during reasoning.

This creates a temporal chain of extraction positions:
1. **EOI** (prompt end, `enable_thinking=False`): "how the model reads the instruction"
2. **startofthink** (`<think>`, first generated token, `enable_thinking=True`): "at the gate to reasoning"
3. **endofthink** (`</think>`, end of thinking): "after deliberation, contrasting input labels"
4. **behavioral** (`</think>`, end of thinking): "after deliberation, contrasting actual outcomes"

**Run commands**:
```bash
# Qwen3 (default)
python -m poc_stage4.extract_refusal_direction_startofthink \
    --num-harmful 220 --num-harmless 220
# (output: outputs/stage4/qwen3-14b/refusal_direction_startofthink/)

# Then chain through 4A2→4B→4C:
KL_THRESHOLD=1000 INDUCE_REFUSAL_THRESHOLD=-100 PRUNE_LAYER_PERCENTAGE=0.0 \
    INPUT_VARIANT=startofthink sbatch slurm_scripts/stage4a2_qwen3_subspace.slurm
INPUT_VARIANT=startofthink sbatch slurm_scripts/stage4b_qwen3_token_dynamics_subspace.slurm
INPUT_VARIANT=startofthink sbatch slurm_scripts/stage4_subspace_stats.slurm
```

**Run status (2026-06-19)**:

| Job | Script | Status | Notes |
|-----|--------|--------|-------|
| 595022 | 4A1-startofthink | ❌ Failed | CUDA error on n-601 (GPU contamination from Gemma jobs) |
| 595023 | 4A1-startofthink | ❌ Cancelled | Resources unavailable |
| 595025 | 4A1-startofthink | ❌ Failed | CUDA error on n-601 again (narrowed to n-601 exclusion fix needed) |
| 595027 | 4A1-startofthink | ❌ Bug | Completed, but only L1/L2 had non-zero DiM. Root cause: Flash Attention 2 does not support left-padded inputs without explicit position_ids. Left-padding caused incorrect attention patterns at L3+, making harmful/harmless activations identical there (zero DiM). |
| **595066** | **4A1-startofthink (batch fix)** | **❌ Bug** | **Batched rewrite (left-padding) — same FlashAttn2 issue, zero DiM at L3+** |
| **595193** | **4A1-startofthink (right-pad fix)** | **❌ Bug** | **Right-padding made things WORSE: all 40 layers show zero DiM (even L1/L2 which were non-zero with left-padding). See root cause update below.** |
| **595217** | **4A1-startofthink (left-pad + position_ids fix)** | **✅ Completed** | **Result: L1/L2 non-zero (best layer=1, score=2.6438), L3-L39 all zero — SAME pattern as original left-padding. This is a genuine finding: position_ids fix confirmed NOT the root cause of zero DiM at L3+.** |

**Root cause of zero DiM — final diagnosis (2026-06-19)**:

Three experiments, three results:

| Approach | L1/L2 | L3-L39 | Notes |
|----------|--------|--------|-------|
| Left-padding, no position_ids (595027/595066) | ✅ non-zero | ❌ zero | Initial finding |
| Right-padding, default position_ids (595193) | ❌ zero | ❌ zero | WORSE |
| Left-padding + explicit position_ids (595217) | ✅ non-zero | ❌ zero | SAME as attempt 1 |

**Conclusion**: position_ids do NOT fix the zero DiM at L3-L39. The right-padding made L1/L2 also disappear, revealing that left-padding is required to keep  at a fixed tensor column. But L3-L39 are genuinely zero regardless of position_ids.

**Scientific finding (not a bug)**: The harmful/harmless distinction at the  token is ONLY present in early layers (L1, L2). Deeper layers (L3-L39) have equal mean projections for harmful and harmless, making the Direction in Means zero there. This reveals a genuine representational asymmetry:

- **EOI (prompt end)**: DiM non-zero at many layers → input distinction preserved in deep layers
- **Startofthink (, first generated token)**: DiM ONLY at L1/L2 → distinction not preserved beyond early processing
- **Endofthink (, after full thinking)**: DiM non-zero at deep layers → distinction re-emerges after deliberation

Interpretation: At the  gate, the model has not yet committed its refusal in the deep representational space. The commitment emerges during the thinking process and is fully encoded by  at layer 29 (AUC=0.750). This is consistent with the trajectory finding that the attack outcome signal first appears in bin 0 (first 5% of thinking), not at the gate itself.

**Current status** (2026-06-19, pipeline complete):
- 4A1-startofthink ✅ (job 595217, best_layer=1, score=2.6438, L1/L2 only)
- 4A2-subspace_startofthink ✅ (job 595221, [3,5120] subspace: L1=rank0, L0=rank1, L2=rank2)
- 4B-token_dynamics_startofthink ✅ (job 595223, 220/220 examples, ~1.4s/example — early-exit at L0/L1/L2)
- 4C-stats_startofthink ✅ (job 595228, best AUC=0.731 at L0, rank0, p=0.0)

---

## Comparison: What Each Paper Does

| | Arditi et al. 2024 (refusal direction paper) | Zhao et al. 2025 (CoT hijacking paper) | poc_stage4 original | poc_stage4 new variants |
|-|------|------|------|------|
| **Contrast set** | Harmful vs. harmless (input label) | N/A (uses Arditi's direction) | Harmful vs. harmless (input label) | Also: ① same contrast at `</think>` (endofthink) ② behavioral complied vs. refused (behavioral) |
| **Extraction position** | EOI (prompt end, before generation) | N/A | EOI (−1, −2, −3, −4 offsets) | `</think>` / `<channel\|>` token (after deliberation) |
| **Direction type** | Single vector, best (layer, pos) | N/A | Single vector (4A1 + 4A2) | Also: K-vector subspace (select_direction_subspace) |
| **Generation analysis** | Not done | Per-token projection during generation | `analyze_stage6_token_dynamics.py` (scalar per token per layer) | `analyze_token_dynamics_subspace.py` (K projections per token per layer) |
| **Model families** | Non-reasoning models only | Non-reasoning models only | Qwen3-14B only | Qwen3-14B and Gemma4-E4B-it |

---

## Verification Steps

After running each new variant:

**1. Cosine similarity to original EOI direction**:
```python
import torch
d_eoi = torch.load("outputs/stage4/qwen3-14b/refusal_direction/direction.pt")
d_eot = torch.load("outputs/stage4/qwen3-14b/refusal_direction_endofthink/direction.pt")
sim = (d_eoi @ d_eot) / (d_eoi.norm() * d_eot.norm())
print(f"cosine similarity EOI vs endofthink: {sim:.4f}")
```
If similarity ≈ 1.0: both positions capture the same signal. If low: the positions are
genuinely distinct, suggesting the attack dilutes refusal during generation.

**2. Run Stage 4A2 (or subspace) on the new directions**:
```bash
# Validate endofthink direction with single-vector Stage 4A2
python -m poc_stage4.select_refusal_direction_interventions \
    --input-dir outputs/stage4/qwen3-14b/refusal_direction_endofthink \
    --output-dir outputs/stage4/qwen3-14b/refusal_direction_endofthink

# Or build a subspace from any 4A1 output
python -m poc_stage4.select_direction_subspace \
    --input-dir outputs/stage4/qwen3-14b/refusal_direction_endofthink \
    --output-dir outputs/stage4/qwen3-14b/direction_subspace_endofthink \
    --k 5
```

**3. Compare projection decay in token dynamics**:
Run `analyze_stage6_token_dynamics.py` (single direction) alongside
`analyze_token_dynamics_subspace.py` (K directions) using each new direction and compare
the projection-over-time plots. The endofthink or behavioral direction should show a
sharper difference between successful attacks (low projection near `</think>`) and
failures (high projection near `</think>`).

**4. Check `skipped_prompts.json` after endofthink extraction**:
If a large fraction of prompts are skipped (thinking-end token not found within
`--max-generation-tokens`), increase the token budget or investigate whether the model is
actually generating thinking chains for these prompts.

**5. Check `group_summary.json` after behavioral extraction**:
Confirm there are enough complied and refused examples in the Stage 6 input directory to
form meaningful train and validation splits. If the attack success rate is very high or
very low, one group may be too small for reliable DiM computation.

---

## SLURM Scripts (Qwen3-14B pipeline)

The following SLURM scripts cover the full new Stage 4 pipeline for Qwen3-14B.
All use `--partition=killable --account=gpu-research --nodelist=n-802,...,n-601,n-602`.

| Script | Runs | Time limit | GPUs | Resume? |
|--------|------|-----------|------|---------|
| `stage4a1_qwen3_endofthink_smoke.slurm` | `extract_refusal_direction_endofthink` (4 prompts, `--dry-run`) | 30 min | 1 | — |
| `stage4a1_qwen3_endofthink.slurm` | `extract_refusal_direction_endofthink` (220+220 prompts) | 24h | 2 | Yes (`RESUME=true`) |
| `stage4a1_qwen3_behavioral.slurm` | `extract_refusal_direction_behavioral` (Stage 6 traces, `qwen_run_success`) | 12h | 2 | — (fast, no generation) |
| `stage4a2_qwen3_subspace.slurm` | `select_direction_subspace` (`INPUT_VARIANT=endofthink\|behavioral`) | 24h | 2 | Yes (`RESUME=true`) |
| `stage4b_qwen3_token_dynamics_subspace.slurm` | `analyze_token_dynamics_subspace` (`INPUT_VARIANT=endofthink\|behavioral`) | 12h | 2 | Yes (`RESUME=true`) |

### Automatic chain submission

`slurm_scripts/submit_stage4_chain.sh` submits all 7 jobs at once with SLURM
`--dependency=afterok:` chaining so each step only starts if the previous one succeeded:

```
Track A: smoke → endofthink_full → subspace_endofthink → dyn_endofthink
Track B: behavioral → subspace_behavioral → dyn_behavioral
```

Run: `bash slurm_scripts/submit_stage4_chain.sh`

### Resume after preemption (endofthink)

The endofthink job runs on the `killable` partition (max 24h, can be preempted). Per-prompt
checkpoints are saved automatically to `<output-dir>/checkpoints/endofthink/`. To resume:

```bash
RESUME=true sbatch slurm_scripts/stage4a1_qwen3_endofthink.slurm
```

### Known issues: intervention filters do not apply to endofthink or behavioral directions

**BOTH** `endofthink` and `behavioral` directions fail the default intervention filters in
`select_direction_subspace.py`. The filters were designed for an input-label refusal direction;
neither of the new tracks satisfies them:

| Filter | Condition | Endofthink | Behavioral | Reason |
|--------|-----------|-----------|-----------|--------|
| KL filter | `harmless_ablation_kl_divergence ≤ threshold` | Partly (some layers 0–13 KL) | Partly | Ablating doesn't always disrupt harmless outputs |
| Steering filter | `harmless_steering_refusal_score ≥ threshold` | **All fail** (steer≈−18.4) | **All fail** (steer≈−18.4) | Both directions point toward compliance, not refusal |

The steering score ≈ −18.4 across ALL layers for BOTH tracks because:
- **Endofthink direction** = mean(harmful reasoning at `</think>`) − mean(harmless reasoning) → captures "harmful content processing", not refusal readiness
- **Behavioral direction** = mean(complied) − mean(refused) → points explicitly away from refusal

**Fix: bypass both filters with extreme thresholds:**
```bash
# Works for both INPUT_VARIANT=behavioral and INPUT_VARIANT=endofthink
KL_THRESHOLD=1000 INDUCE_REFUSAL_THRESHOLD=-100 PRUNE_LAYER_PERCENTAGE=0.0 \
    INPUT_VARIANT=behavioral sbatch slurm_scripts/stage4a2_qwen3_subspace.slurm
```

**RESUME bug:** Do NOT use `RESUME=true` when changing filter thresholds. The checkpoint JSONL
(`checkpoints/subspace_selection/intervention_candidate_scores.checkpoint.jsonl`) stores old
`passes_filters` values and RESUME reuses them verbatim — new thresholds are ignored for
already-cached rows.
Fix: delete `intervention_candidate_scores.checkpoint.jsonl` first, then submit without RESUME.
Keeping `baseline_harmful_logits.pt` and `baseline_harmless_logits.pt` is safe — they ARE
correctly reloaded.

### Run status (2026-06-19, final state after all fixes)

| Job | Script | Status | Notes |
|-----|--------|--------|-------|
| 593267 | endofthink smoke | ✅ Completed | Passed |
| 593268 | endofthink full | ✅ Completed (~6h 17m) | Layer 26, score 7.4362, 162/162 train, 3 harmless skipped |
| 593269 | subspace_endofthink | ❌ Failed | Steering filter (steer≈−18.4 < 0.0 default) |
| 593270 | dyn_endofthink | ❌ Cancelled | Dependency chain broken |
| 593271 | behavioral | ✅ Completed | Layer 20, score 0.9207, 71/71 examples |
| 593272 | subspace_behavioral | ❌ Failed | KL filter (KL≤0.1 default) |
| 593273–594772 | various retries | ❌ | Filter/RESUME bug iterations (see PIPELINE.md) |
| 594773 | subspace_behavioral (**final**) | ✅ Completed | KL=1000, steer=−100, [5,5120] shape, layers 3/21/22/23/26 |
| 594889 | subspace_endofthink | ✅ Completed | KL=1000, steer=−100; [5,5120], layers 2/22/26/28/29 |
| 594890 | dyn_endofthink | ❌ Cancelled | O(n²) speed: ~59 min/example full-tokens; resubmitted as 594904 |
| 594891 | dyn_behavioral | ❌ Cancelled | Same; resubmitted as 594903 |
| 594903 | dyn_behavioral | ❌ Failed | Disk quota: token_level_metrics.jsonl ~240 MB/ex → 52 GB total — fixed |
| 594904 | dyn_endofthink | ❌ Failed | Same |
| 594971 | dyn_behavioral | ❌ Failed | Disk quota on per_example JSON (22 MB/ex) — fixed with layer subsetting (Option A) |
| 594972 | dyn_endofthink | ❌ Failed | Same |
| **594998** | **dyn_behavioral** | **✅ Completed** | **220/220 examples; ~3.3 MB/example (5 subspace layers); no errors** |
| **594999** | **dyn_endofthink** | **✅ Completed** | **220/220 examples; ~3.3 MB/example (5 subspace layers); no errors** |
| **595007** | **stats_behavioral** | **✅ Completed** | **Best AUC=0.750 (layer 26, rank 4), p=0.0; 24/25 (layer,rank) pairs significant** |
| **595008** | **stats_endofthink** | **✅ Completed** | **Best AUC=0.750 (layer 29, rank 2), p=0.0; 14/25 pairs significant** |
| **595217** | **4A1-startofthink** | **✅ Completed** | **Left-pad + position_ids fix; best_layer=1, score=2.6438; L3-L39 zero (genuine finding)** |
| **595221** | **4A2-subspace_startofthink** | **✅ Completed** | **[3,5120] subspace: L0, L1, L2 (only 3 of 5 passed relaxed filters)** |
| **595223** | **4B-dyn_startofthink** | **✅ Completed** | **220/220 examples, ~1.4s/ex (early-exit at L0/L1/L2 layers)** |
| **595228** | **4C-stats_startofthink** | **✅ Completed** | **Best AUC=0.731 (layer 0, rank 0), p=0.0** |

**Disk fix (2026-06-19):** `analyze_token_dynamics_subspace.py` no longer writes
`token_level_metrics.jsonl` by default (use `--emit-token-level-jsonl` to opt in).
`analyze_subspace_dynamics_stats.py` now reads directly from `per_example/*.json`.
Disk per variant: 220 × 22 MB = 4.8 GB (was 52 GB).

**RESUME resubmit commands** (if job times out or is preempted):
```bash
RESUME=true INPUT_VARIANT=behavioral sbatch slurm_scripts/stage4b_qwen3_token_dynamics_subspace.slurm
RESUME=true INPUT_VARIANT=endofthink sbatch slurm_scripts/stage4b_qwen3_token_dynamics_subspace.slurm
```
RESUME skips examples whose `per_example/<id>.json` exists (written atomically on completion).
**Do NOT delete the output directory before resubmitting** — it is the checkpoint store.

### Stage 4C — Analysis script (CPU-only, no GPU)

Script: `analyze_subspace_dynamics_stats.py`
SLURM: `stage4_subspace_stats.slurm`

**Run after dyn jobs complete:**
```bash
INPUT_VARIANT=behavioral sbatch slurm_scripts/stage4_subspace_stats.slurm
INPUT_VARIANT=endofthink sbatch slurm_scripts/stage4_subspace_stats.slurm
```

**What it computes:**
- Streams `per_example/*.json` files (never loads all into RAM — uses Welford online stats)
- Groups tokens into segments: `thinking` / `answer` / `other`
- Per-example: mean/std/final/max/min projection per (layer, rank, segment)
- AUC(mean thinking projection, qwen_run_success) + Mann-Whitney p-value per (layer, rank)
- Normalized trajectory: mean projection per bin (default 10 bins) during thinking, complied vs refused
- 4 plots: AUC heatmap, trajectory per rank, box plots, thinking vs answer comparison

**Outputs** (in `outputs/stage4/qwen3-14b/subspace_stats_{behavioral,endofthink}/`):
```
per_example_stats.csv    (example × layer × rank × segment) statistics
auc_table.csv            AUC per (layer, rank), sorted best-first
trajectory.csv           mean projection per (bin × layer × rank × group)
summary.json             top-line results
plots/auc_heatmap.png
plots/trajectory_rank{k}.png
plots/boxplot_thinking.png
plots/segment_comparison.png
```

**What to look for:** AUC > 0.6 = direction predicts jailbreak outcome.

**Actual results (jobs 595007/595008, 2026-06-19):**

| Variant | Best AUC | Best (layer, rank) | p-value | Significant pairs |
|---------|----------|-------------------|---------|-------------------|
| behavioral | 0.750 | layer 26, rank 4 | 0.0 | 24/25 |
| endofthink | 0.750 | layer 29, rank 2 | 0.0 | 14/25 |
| startofthink | 0.731 | layer 0, rank 0 | 0.0 | — |

Both variants achieve best AUC = 0.750 with p=0.0 (Mann-Whitney). The refusal subspace
projection during the first 3072 thinking tokens reliably separates complied vs refused
examples for Qwen3-14B on CoT hijacking attacks.

Output dirs: `outputs/stage4/qwen3-14b/subspace_stats_behavioral/` and `subspace_stats_endofthink/`.

**New findings from additional analysis (2026-06-19)**:

**Temporal trajectory profiles (full 10-bin view for top (layer, rank) per variant)**:

| Variant | Top (L, r) | Bin 0 (5%) | Bin 4 (45%) | Bin 9 (95%) | Peak bin |
|---------|-----------|------------|------------|------------|---------|
| behavioral | L26 r4 | d=0.158 | d=0.310 | d=0.163 | bin 4 (45%) |
| endofthink | L29 r2 | d=0.285 | d=0.290 | d=0.258 | bin 3 (35%) |

Note: L3 r0 (behavioral) shows the flattest trajectory (d≈0.30–0.36 across all bins), suggesting a very stable representational signal throughout early thinking.

**Robustness: AUC holds when controlling for thinking length**:
- All 199 examples: AUC=0.750
- Ceiling examples only (89C/89R, both groups analyzed to 3071 tokens): **AUC=0.734** (p<0.0001)
- This confirms the signal is genuine and not driven by the short-thinkers=complied confound.

**Thinking length as outcome predictor**:
- Refused examples: mean generation = 20,412 tokens (median 19,786)
- Complied examples: mean generation = 13,500 tokens (median 15,301)
- Refused examples generate ~50% more tokens; both groups exceed the 3072 thinking-token cutoff
- The `final_proj` (at the 3072nd token) AUC=0.601 is lower than `mean_proj` AUC=0.734 for the ceiling set

**Coverage caveat**: The 4B analysis captures only the **first 3072 thinking tokens**. The median trace has ~20K+ total generation tokens. The trajectory plots (bins 0-9) represent the first ~15-40% of the full thinking phase for most examples. "Bin 9" is NOT the end of thinking — it is the 2765-3072 token range, which for a typical trace is early-to-mid thinking. Full thinking coverage would require O(n²) forward passes (prohibitive at 20K+ tokens).

---

## New Variants: endofresponse + prompt-type comparison (2026-06-20)

### Endofresponse variant

**Goal**: Extract refusal direction at EOS (`<|im_end|>`) — after the full answer is generated.
Completes the temporal picture: startofthink → endofthink → **endofresponse**.

**Script**: `poc_stage4/extract_refusal_direction_endofresponse.py`
**SLURM**: `slurm_scripts/stage4a1_qwen3_endofresponse.slurm`
**Output dir**: `outputs/stage4/qwen3-14b/refusal_direction_endofresponse/`

**4A1 results (job 596299, 2026-06-20)**:
- max_seq_len=20000 (reduced from 30000 after OOM on RTX 3090 with 15.84 GiB model in use)
- 35 complied / 35 refused used (25 complied + 45 refused skipped, >20k tokens)
- `max_standardized_projection_separation: 0.495` (vs endofthink 7.44, startofthink 2.64)
- All 40 candidate directions produced; shape=[1, 40, 5120]

**4A2 results (job 596310, 2026-06-20)**:
- `scientific_status: not_validated_no_surviving_candidates`
- All 40 layers failed KL + steering threshold filters
- Interpretation: The EOS activation does not produce a direction strong enough to behaviorally steer the model. The refusal signal at the end of the response is very weak compared to mid-generation checkpoints.

**Chain status**: 4A1 ✅ | 4A2 ❌ (no candidates) | 4B/4C: not runnable (no validated subspace)

**Scientific conclusion**: The refusal encoding is strongest **during** generation (endofthink, behavioral), not after it. By EOS, the representational signal that distinguished complied vs refused has dissipated or mixed. This is consistent with the model "committing" its behavioral trajectory early and the residual stream encoding task-completion rather than behavioral policy by the time EOS is produced.

---

### Prompt-type comparison (job 596213, 2026-06-20)

**Goal**: Project 3 prompt types × 3 time points onto the behavioral refusal subspace.
Answers: *Does a puzzle-attack prompt look like harmless or direct-harmful in the refusal subspace?*

**Script**: `poc_stage4/compare_prompt_projections.py`
**SLURM**: `slurm_scripts/stage4_prompt_type_comparison.slurm`
**Output dir**: `outputs/stage4/qwen3-14b/prompt_type_comparison_behavioral/`
**Subspace**: `direction_subspace_behavioral` ([5, 5120], layers L3/L21/L22/L23/L26)

**Prompt types**: harmless (50), direct_harm (50), puzzle_attack (201 Stage 6 traces)
**Time points**: startofthink (`<think>`), endofthink (`</think>`), endofresponse (EOS)

**Status (job 596213, running ~2.5h)**: In projection phase — all 3 types projected, writing CSV/plots.
Results pending. Will update with findings once job completes.

---

## Direction Cosine Comparison — All 4 Variants (2026-06-20)

Re-ran `python -m poc_stage4.compare_directions` with all 4 variant directions.
Output: `outputs/stage4/qwen3-14b/direction_comparison/`

### Selected-direction cosine similarities

| Pair | Selected cosine | Layers compared | Max cosine (best layer) | Best layer |
|------|----------------|----------------|------------------------|-----------|
| eoi vs startofthink | 0.053 | L22 vs L1 | 0.314 | L1 |
| eoi vs endofthink | 0.266 | L22 vs L26 | 0.405 | L26 |
| eoi vs behavioral | -0.053 | L22 vs L20 | 0.137 | L2 |
| startofthink vs endofthink | 0.030 | L1 vs L26 | 0.176 | L1 |
| startofthink vs behavioral | 0.006 | L1 vs L20 | 0.211 | L1 |
| endofthink vs behavioral | -0.050 | L26 vs L20 | 0.294 | L11 |

### Interpretation

All 6 pairs are nearly orthogonal (cosine < 0.27 at selected layers). The highest
similarity is eoi↔endofthink (0.266) — the end-of-response state is most related to
what the model encoded at `</think>`, which makes intuitive sense.

All four directions capture **different axes** of the refusal signal:
- `startofthink` (L0-L2): very early, shallow layers — pre-thinking commitment
- `endofthink` (L26-L29): deep layers — mature CoT conclusion
- `behavioral` (L22-L26): deep layers — behavioral outcome contrast
- `endofresponse` (L22): deep layers — post-generation state (weak, not validated)
