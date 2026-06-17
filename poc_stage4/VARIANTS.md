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
| **`extract_refusal_direction_behavioral.py`** | 4A1-behavioral (**new**) | complied vs. refused (`judge_score`) | `</think>` / `<channel\|>` token (after deliberation) | Single vector per layer `[1, n_layers, d_model]` | Both | `refusal_direction_behavioral/` |
| **`select_direction_subspace.py`** | 4A2-subspace (**new**) | — (uses any 4A1 candidates) | — | Top-K validated vectors `[K, d_model]` | Both | `direction_subspace/` |
| **`analyze_token_dynamics_subspace.py`** | 4B-subspace (**new**) | — (uses subspace direction) | All generated tokens | K projections per token per layer | Both | `token_dynamics_subspace_<run>/` |

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

**Run commands**:
```bash
# Qwen3 (default)
python -m poc_stage4.extract_refusal_direction_endofthink \
    --output-dir outputs/stage4/qwen3-14b/refusal_direction_endofthink \
    --max-generation-tokens 2048

# Gemma4
python -m poc_stage4.extract_refusal_direction_endofthink \
    --model-family gemma4 \
    --output-dir outputs/stage4/gemma4-e4b-it/refusal_direction_endofthink \
    --max-generation-tokens 2048
```

---

### `extract_refusal_direction_behavioral.py` — new, does NOT modify original

**Diff from `extract_refusal_direction.py`**:

- **Contrast set**: harmful/harmless (input label) → complied/refused (behavioral outcome,
  `source_judge.judge_score == 10` vs. `== 1`)
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
- **CLI**: adds `--model-family`, `--model-name`; `--stage6-input` is a required argument;
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

**Run commands**:
```bash
# Qwen3 (default)
python -m poc_stage4.extract_refusal_direction_behavioral \
    --stage6-input outputs/stage6/all_traces_full_1_11 \
    --output-dir outputs/stage4/qwen3-14b/refusal_direction_behavioral

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
