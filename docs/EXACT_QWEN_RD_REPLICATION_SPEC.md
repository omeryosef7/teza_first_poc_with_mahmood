# Exact Qwen3 Refusal Direction Replication Specification

**Date:** 2026-06-25  
**Upstream paper:** Arditi et al., arXiv:2406.11717 ("Refusal in Language Models Is Mediated by a Single Direction")  
**Upstream code:** `Chain_of_Thought_Hijacking/refusal_direction/pipeline/`  
**Current (broken) replication:** `poc_stage4/replicate_standard_refusal_direction.py`  
**Fixed replication (to write):** `poc_stage4/replicate_qwen_rd_exact.py`

---

## Prior Replication Result

`replicate_standard_refusal_direction.py` swept 160 candidates (4 positions × 40 layers) and reported 0 survivors.  
**Current RESEARCH_MASTER.md label:** "hypothesis does not hold" (Gate C negative decision).  
**Correct label:** `UNRESOLVED REPLICATION DISCREPANCY — exact Arditi protocol not yet tested.`

The current script implements a different intervention than Arditi et al.  
The 0/160 result reflects the mismatch, not a null result for the actual RD method.

---

## Upstream Protocol (Arditi et al.) — Exact Steps

### 1. Dataset
- 128 harmful + 128 harmless training instructions (alpaca-style prompts)
- 32 harmful + 32 harmless validation instructions (held out)
- Sampling: `random.seed(42)`, shuffled, split 4:1 train/val
- No chat template on the instructions themselves; apply chat template at tokenization
- Thinking disabled for all RD extraction (Qwen3 `/no_thinking` or equivalent)

### 2. Direction extraction
```
positions = [-1, -2, -3, -4]   # last 4 positions in the EOI suffix
```
For each position, for each layer (0..num_hidden_layers-1):
- Extract residual stream activations at that position via `register_forward_pre_hook` on `model.model.layers[layer]`
- Accumulate mean over training split: `mean_harmful` and `mean_harmless`
- Direction: `mean_harmful - mean_harmless` (not normalized at extraction time)

Key code: `generate_directions.py:get_mean_activations()` — uses `input[0].clone()` at the **pre-hook** (residual stream before the transformer block).

Result shape: `(4, num_hidden_layers, d_model)` = `(4, 40, 5120)` for Qwen3-14B.

### 3. Direction selection — THREE criteria

For each (position, layer) candidate direction `d`:

**a) KL divergence filter** (fluency preservation)  
Apply all-layer ablation hooks (see §4) to harmless validation prompts.  
Compute KL(baseline_logits || ablated_logits) at the last token position.  
Filter out if `kl_div > kl_threshold` (Arditi: `kl_threshold=0.1`; paper also evaluates 1.0).

**b) Steering filter** (direction induces refusal)  
Apply single-layer activation-addition at source_layer only:  
  `residual += coeff * d` with `coeff = 1.0`  
Measure log-prob of refusal tokens on harmless validation prompts.  
Filter out if `steering_score < induce_refusal_threshold=0.0`.

**c) Layer pruning** (discard last 20% of layers)  
Filter out if `source_layer >= int(n_layers * 0.8)` (i.e., layers 32–39 for Qwen3-14B).

The direction that passes all 3 filters and has the **lowest ablation refusal score** (best jailbreak effect) is selected.

### 4. All-layer ablation hooks (CRITICAL)

`get_all_direction_ablation_hooks()` in `hook_utils.py:80-88`:

```python
fwd_pre_hooks = [
    (model.model.layers[layer], get_direction_ablation_input_pre_hook(direction))
    for layer in range(num_hidden_layers)          # ALL 40 layers
]
fwd_hooks = [
    (model.model.layers[layer].self_attn, get_direction_ablation_output_hook(direction))
    for layer in range(num_hidden_layers)          # ALL 40 attn modules
]
fwd_hooks += [
    (model.model.layers[layer].mlp, get_direction_ablation_output_hook(direction))
    for layer in range(num_hidden_layers)          # ALL 40 MLP modules
]
```

Total: 3 × 40 = **120 hooks per forward pass** for Qwen3-14B.

The ablation formula at each hook:
```python
direction_unit = direction / (direction.norm() + 1e-8)
activation -= (activation @ direction_unit).unsqueeze(-1) * direction_unit
```

This is applied to:
- The **input** to every transformer block (pre-hook)
- The **output** of every attention sub-layer (post-hook)  
- The **output** of every MLP sub-layer (post-hook)

---

## Four Bugs in the Current Replication Script

### Bug 1 — Single-layer ablation (CRITICAL)

**Current code** (`replicate_standard_refusal_direction.py:395-398`):
```python
ablate_fn = _make_ablate_hook(layer_i, direction, device)
h = layer.register_forward_hook(ablate_fn)   # ONE hook, ONE layer
ablation_score = _score_refusal(...)
h.remove()
```

**Upstream requirement:** 120 hooks across all layers (see §4 above).

**Why this causes 0/160:** Ablating a single layer barely changes refusal behavior — the other 39 layers still contain the direction. Most candidates will show near-zero ablation effect and fail the `kl < threshold` filter (or appear to have low KL because the intervention is so weak).

**Fix:**
```python
fwd_pre_hooks, fwd_hooks = get_all_direction_ablation_hooks(model_base, direction)
with add_hooks(fwd_pre_hooks, fwd_hooks):
    ablation_score = _score_refusal(...)
```

### Bug 2 — KL computed with addition hooks, not ablation hooks

**Current code** (`replicate_standard_refusal_direction.py:409-410`):
```python
add_fn2 = _make_add_hook(layer_i, direction, steer_alpha, device)   # ADDITION
kl = _compute_kl_divergence(model, ..., add_fn2)
```

**Upstream requirement:** KL is computed using the same **all-layer ablation** hooks (not addition hooks). See `select_direction.py:186-203`:
```python
fwd_pre_hooks = [(model_base.model_block_modules[layer],
                  get_direction_ablation_input_pre_hook(direction=ablation_dir))
                 for layer in range(model_base.model.config.num_hidden_layers)]
fwd_hooks = [(model_base.model_attn_modules[layer],
              get_direction_ablation_output_hook(direction=ablation_dir))
             for layer in range(model_base.model.config.num_hidden_layers)]
fwd_hooks += ...
```

**Why this matters:** Using addition hooks for KL measures something entirely different — the KL from pushing the distribution toward refusal (activates refusal behavior on harmless). The correct KL measures the fluency impact of *removing* the direction (if removing the refusal direction breaks fluency, that direction is too entangled with general representations).

### Bug 3 — Steering coefficient α=20.0 instead of coeff=1.0

**Current code** (`replicate_standard_refusal_direction.py:363`):
```python
steer_alpha: float = 20.0
```
Used in both steering score computation and KL computation.

**Upstream requirement** (`select_direction.py:220-221`):
```python
coeff = torch.tensor(1.0)
fwd_pre_hooks = [(model_base.model_block_modules[source_layer],
                  get_activation_addition_input_pre_hook(vector=refusal_vector, coeff=coeff))]
```

**Why this matters:** α=20.0 is a 20× amplification of the direction. The refusal token log-probs under this perturbation are dominated by the large coefficient, making almost any direction appear to steer refusal. The KL is also 20× larger than it should be, causing many directions to fail the KL filter.

### Bug 4 — Layer pruning direction is inverted

**Current code** (`replicate_standard_refusal_direction.py:369, 382-388`):
```python
n_skip = int(n_layers * prune_layer_pct)   # = 8 for 40 layers
...
if layer_i < n_skip:  # skips layers 0..7 (FIRST 20%)
    results.append({..., "skip_reason": "layer_pruned"})
```

**Upstream requirement** (`select_direction.py:109`):
```python
if prune_layer_percentage is not None and layer >= int(n_layer * (1.0 - prune_layer_percentage)):
    return True  # filters layers 32..39 (LAST 20%)
```

**Why this matters:** The early layers (0–7) are less likely to contain useful refusal directions; the final layers (32–39) are known to be less generalizable. Pruning the wrong end means directions that should be evaluated (early layers) are skipped, and directions that should be pruned (last layers) are evaluated.

---

## Required Implementation: `poc_stage4/replicate_qwen_rd_exact.py`

### Phase A — Exact single target (run first)

The paper reports a specific best direction for Llama-2-7B-Chat at position -1, layer 13.  
For Qwen3-14B, no validated (position, layer) is known from the original paper.  
The diagnostic sweep in Stage 4A2 found the behavioral direction at **L26** for Qwen3-14B.

Run Phase A targeting (position=-1, layer=26) exactly, with all 4 bugs fixed:
1. All-layer ablation for ablation score
2. All-layer ablation for KL (not addition)
3. coeff=1.0 for steering
4. Prune last 20% of layers (32–39 for Qwen3-14B)

Expected behavior: if the RD method works on Qwen3-14B, L26 or nearby should survive.

### Phase B — Diagnostic sweep ±2 layers (only if A fails)

Sweep layers 24–28, positions -1 to -4.  
This is a 5×4=20 candidate sweep, not 160.

### Phase C — Full sweep (only if B fails)

Full 4×40=160 candidate sweep with all bugs fixed.

---

## Exact Parameters for `replicate_qwen_rd_exact.py`

| Parameter | Value | Source |
|-----------|-------|--------|
| Model | `Qwen/Qwen3-14B` | Stage 4 |
| Model revision | `40c069824f4251a91eefaf281ebe4c544efd3e18` | Stage 4A1 |
| n_train_harmful | 128 | Arditi §3 |
| n_train_harmless | 128 | Arditi §3 |
| n_val_harmful | 32 | Arditi §3 |
| n_val_harmless | 32 | Arditi §3 |
| EOI positions | [-1, -2, -3, -4] | Arditi §3 |
| Hook type for direction extraction | `register_forward_pre_hook` on `model.model.layers[l]` | `generate_directions.py` |
| Hook type for KL | all-layer ablation (3 × num_layers hooks) | `select_direction.py:186-201` |
| Hook type for steering | single-layer `activation_addition` at source_layer | `select_direction.py:222` |
| Steering coeff | 1.0 | `select_direction.py:220` |
| KL threshold | 0.1 (also test 1.0) | Stage 4A2 uses 0.1; paper evaluates 1.0 |
| Steering threshold | 0.0 | `select_direction.py:162` |
| Prune last % | 20% (layers ≥ 32 for 40-layer model) | `select_direction.py:109` |
| Thinking | DISABLED | Matches inference condition in puzzle attack |
| Chat template | `apply_chat_template(add_generation_prompt=True)` | `qwen3_model.py:28` |
| Refusal tokens | [40, 2121] = ['I', 'As'] | `qwen3_model.py:13` |
| dtype | bfloat16 | L40S constraint (no fp16 overflow) |
| Batch size | 8 | GPU memory safety |

---

## What `validate_intervention_hooks.py` Must Verify (for RD jobs)

Before running Phase A:
1. **All 120 hooks fire**: verify hook counter incremented 3×40=120 times per forward pass
2. **Direction component removed**: after ablation, `(activation @ direction_unit).abs().max() < 1e-5`
3. **Hooks removed after context exit**: no hooks remain on model modules
4. **Pre-hook fires on input tuple**: `input[0]` shape is `(batch, seq, d_model)`
5. **Attn and MLP post-hooks receive output tuples**: handled correctly (return `(modified, *rest)`)
6. **Single-layer addition (steering) uses correct hook type**: `register_forward_pre_hook` not forward hook

Note: G-condition generation jobs do NOT require `validate_intervention_hooks.py` to pass (no hooks involved).

---

## What the Replication Can/Cannot Prove

If Phase A succeeds (direction at L26 survives all filters):
- The Arditi et al. method finds a refusal direction in Qwen3-14B
- Gate C should become: "REPLICATION SUCCEEDED at (pos=-1, layer=26)"
- This still does NOT establish that the puzzle-attack hijacks this specific direction

If all phases fail (0 survivors):
- Either Qwen3-14B has no single-direction refusal (plausible given architecture differences vs Llama-2)
- Or the dataset (alpaca harmful prompts vs our puzzle-wrapped goals) doesn't activate the same direction
- Gate C should become: "REPLICATION FAILED — refusal direction method not applicable to Qwen3-14B with this dataset"
- Neither outcome is evidence for or against the puzzle-attack mechanism

---

## Files to Create/Modify

| File | Action |
|------|--------|
| `poc_stage4/replicate_qwen_rd_exact.py` | Write with 4 bugs fixed |
| `poc_stage4/validate_intervention_hooks.py` | Write unit tests |
| `docs/RESEARCH_MASTER.md` Section 3 Gate C | Change "does not hold" → "UNRESOLVED" |
| `slurm_scripts/stage4_standard_rd_exact.slurm` | Submit after hook validation passes |
