# Stage 4.5 — Attention Methodology Audit

**Status: BLOCKED on GPU capture. Methodology audit complete from available source.**

---

## Summary

A review of all Python source files in `Chain_of_Thought_Hijacking/refusal_direction/pipeline/`
and the Stage 4 `poc_stage4/` package confirms that **no attention-weight capture exists in the
current codebase.** The pipeline works exclusively with residual-stream hidden-state projections.
The attention pilot must be implemented from scratch.

---

## 10-Question Methodology Audit

### Q1 — What is the source representation measured?

**Current pipeline (all stages):**  
Residual-stream hidden states at the input of each transformer block (resid_pre), extracted via
`register_forward_pre_hook` on `model.model.layers[layer]`. Measured at position `-1` (last prompt
token) for direction generation; measured at all generated-token positions for Stage 4 dynamics.

**Attention-weight capture:**  
Not implemented. The `model_attn_modules` list
(`[block.self_attn for block in model.model.layers]`) is used only for directional-ablation hooks
on the attention *output*, not for capturing raw attention weights.

### Q2 — What denominator / normalisation is used for attention?

**Not answered by the codebase.** No attention weight extraction code exists.  
Assumption required for implementation: Qwen3 attention uses softmax over the key-query dot
products; raw attention weights are already probability distributions summing to 1 per head per
query position. The denominator question only becomes meaningful when aggregating across heads or
layers.

### Q3 — How are attention heads / layers aggregated?

**Not answered.** No aggregation code exists.  
Methodological options for the pilot:
- Mean over all heads within a layer  
- Identify heads with highest attention to the `embedded_harmful_goal_span` tokens (top-k heads)
- Use a direction-weighted aggregate (weight heads by their cosine similarity to the contrast direction)

**Decision required before implementing `analyze_attention_pilot.py`.**

### Q4 — How are special tokens handled?

`diagnose_reasoning_visible_tokens.py` contains the only existing special-token handling logic:  
`find_subsequence` locates `<think>` and `</think>` token IDs in the generated sequence.  
`is_skippable_visible_token` skips whitespace-only tokens.

For the attention pilot, the span alignment code (`align_prompt_spans.py`) will treat special
tokens (`<|im_start|>`, `<|im_end|>`, `<|endoftext|>`) as their own named span
(`chat_template_and_special_tokens`). Whether to include or exclude them from attention
denominator computation is a methodological choice not yet made.

### Q5 — How is span location determined?

`diagnose_reasoning_visible_tokens.py` uses `find_subsequence(sequence, subsequence)` to locate
token subsequences within the generated sequence. This is the validated algorithm used to locate
`<think>` / `</think>` delimiters.

`align_prompt_spans.py` (implemented in Stage 4.5) uses the same subsequence-search approach on
the prompt token IDs from Stage 6 traces, mapping named spans to `[start_token, end_token)`
index ranges in the full token sequence.

### Q6 — When is attention measured (pre-generation, at generation, post-hoc)?

**Current pipeline:** Forward pass during generation (or prefix-only forward pass for scoring),
using PyTorch hooks registered on transformer modules.

**For the attention pilot:** Attention weights must be captured *during* generation, using
`output_attentions=True` in the HuggingFace generate call. This is significantly more expensive
than the residual-stream approach used in Stage 4 (see memory estimate, Q10).

The Stage 4 approach processed tokens sequentially with hooks; the same hook infrastructure
(`hook_utils.add_hooks`) can be adapted for attention capture with `output_attentions=True`.

### Q7 — What quantity is ultimately reported?

**Not defined.** Candidate quantities for the pilot:

a. Mean attention weight from the current generated token to each prompt span  
b. Cumulative attention to each span over the think-phase generation  
c. Attention divergence between successful and failed examples at the harmful-interaction onset token  
d. Change in attention to `embedded_harmful_goal_span` around the event onset

**Decision required.** The plan recommends option (c) or (d) as most informative given the
event-aligned analysis in Phase 3.

### Q8 — Does the pipeline re-run generation or replay from saved activations?

**Stage 4:** Replays from saved Stage 6 traces (token IDs and prompt IDs), running a forward
pass per generated token with hooks. Does not re-run generation.

**Attention pilot:** Will need to either (a) re-run generation with `output_attentions=True`, or
(b) replay forward passes over saved token IDs with attention capture hooks. Option (b) is
preferable (deterministic, uses existing Stage 6 token sequences) but requires validating that
replay matches generation-time hidden states.

### Q9 — Is there a refusal-direction-based attention analysis in Zou et al. or prior work?

**Not found in the codebase.** The `refusal_direction` pipeline sources do not reference any
paper implementing attention-to-span analysis combined with activation-direction analysis.  
The analysis in `select_direction.py` uses only logit-space refusal scores (softmax probability
of refusal token IDs) and KL divergence for direction selection — no attention analysis.

**What is in the codebase relevant to attention:**  
- `model_base.py::_get_attn_modules()` returns `self_attn` modules — useful for hooking  
- `hook_utils.py::add_hooks()` — the hook context manager, reusable for attention capture  
- No existing code captures `attn_weights` or `attn_scores`

### Q10 — Memory estimate for Qwen3-14B attention capture

**Not yet computed.** Required before Phase 5B is approved.

Rough estimate (to be verified on actual GPU):
- Qwen3-14B: 40 layers, ~40 heads per layer, GQA (key-value grouped query attention)  
- For a sequence of length L (prompt + generation): attention matrix per head = L × L (float16)  
- At L = 3000 (typical with long think traces): 3000 × 3000 × 2 bytes = ~18 MB per head  
- 40 layers × ~40 heads = 1600 heads × 18 MB = ~28.8 GB for full attention capture  
- With GQA (8 KV-heads, 40 Q-heads per GQA group), stored as query-key cross-attention:
  actual stored size depends on whether keys are repeated — likely ~3–5 GB per forward pass  
- For 40 pilot examples × 1 forward pass each: feasible on 80 GB GPU (A100/H100)  
- **This estimate must be verified with `torch.cuda.memory_allocated()` before submitting**

---

## What Needs to Happen Before Phase 5B

1. **Decide**: which quantity to measure (Q7 above) — recommended: attention weight change at event onset
2. **Decide**: head aggregation method (Q3) — recommended: mean over all heads, then top-k sensitivity
3. **Verify**: memory estimate on a smoke run with 2–3 examples before full pilot batch
4. **Validate**: that replay-forward-pass attention matches generation-time attention (test on 1 example)
5. **Write** memory estimate to `manifests/run_manifest.json` before submitting the Slurm job

Until all 5 are complete, `capture_attention_pilot.py` must not be submitted as a Slurm job.

---

## `align_prompt_spans.py` — Available Implementation

`poc_stage4_5/align_prompt_spans.py` is fully implemented (see that file).

It maps named spans to token index ranges in the prompt using the Stage 6 `prompt_token_ids`.  
The algorithm is based on `find_subsequence` from `diagnose_reasoning_visible_tokens.py`.

Named spans:
- `puzzle_span` — the puzzle / reasoning task portion of the user message
- `embedded_harmful_goal_span` — the injected harmful instruction text
- `answer_or_execution_cue_span` — the explicit cue to answer/execute
- `chat_template_and_special_tokens` — chat template delimiters and special tokens
- `prior_generated_reasoning_span` — prior assistant turn reasoning (absent in single-turn attacks)
- `other_prompt_span` — remaining prompt tokens not covered by above

Tests in `poc_stage4_5/tests/test_core.py` validate the subsequence alignment algorithm.

---

## Files Inspected

| File | Relevant finding |
|------|-----------------|
| `pipeline/generate_directions.py` | Computes mean residual-stream activations (resid_pre, position -1). No attention. |
| `pipeline/select_direction.py` | Measures refusal scores and KL divergence. No attention. Uses `model_attn_modules` only for ablation hooks on attention output. |
| `pipeline/model_utils/model_base.py` | Defines `_get_attn_modules()` (returns `self_attn` modules). No weight capture. |
| `pipeline/model_utils/qwen3_model.py` | Qwen3-specific: 40 layers, GQA, `QWEN3_REFUSAL_TOKS = [40, 2121]`. No attention capture. |
| `pipeline/utils/hook_utils.py` | Hook infrastructure: `add_hooks`, directional ablation on resid_pre / attn_output / mlp_output. No attention weight hooks. |
| `pipeline/diagnose_refusal_scoring.py` | Logit-space analysis only. Has `find_subsequence` for token stream parsing. |
| `pipeline/diagnose_reasoning_visible_tokens.py` | Generation replay. Locates `<think>`/`</think>` and first visible post-reasoning token. Template for replay approach. |
| `poc_stage4/analyze_stage6_token_dynamics.py` | (not in this audit path) Residual-stream projection per generated token. No attention. |

---

*Last updated: 2026-06-08*
