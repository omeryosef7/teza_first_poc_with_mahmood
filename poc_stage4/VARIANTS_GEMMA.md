# Stage 4 Refusal Direction Analysis — Gemma 4 (gemma4-e4b-it)

## Model and Data

- **Model**: `google/gemma-4-E4B-it` (4B parameters, `model_family=gemma4`)
- **Architecture**: 42 layers, d_model=2560, 8 attention heads
- **Thinking markers**: `<|channel>thought` (start) → `<channel|>` (end), handled by `model_family_utils.py`
- **Stage 6 traces**: `outputs/stage6/gemma_traces_full_1_11_eos_fixed/`
  - 220 traces, **100% `eos_token` termination** (EOS-fixed run)
  - Complied: **66** (`qwen_run_success=True`), Refused: **154** (`qwen_run_success=False`)
  - Median token sequence length: ~3,222–7,501 tokens (much shorter than Qwen3's ~17K)
  - **Do NOT use** `gemma_traces_full_1_11/` — 99% hit `max_new_tokens` with repetitive padding
- **Scripts**: all in `slurm_scripts/stage4*_gemma*.slurm`, 1 GPU each

---

## Pipeline Overview

```
4A1 direction extraction (×4 variants, run in parallel)
  ├── behavioral      [stage4a1_gemma_behavioral.slurm]
  ├── endofthink      [stage4a1_gemma_endofthink.slurm]
  ├── startofthink    [stage4a1_gemma_startofthink.slurm]
  └── endofresponse   [stage4a1_gemma_endofresponse.slurm]
       ↓ (per variant)
4A2 subspace selection  [stage4a2_gemma_subspace.slurm, INPUT_VARIANT=...]
       ↓
4B token dynamics       [stage4b_gemma_token_dynamics_subspace.slurm, INPUT_VARIANT=...]
       ↓
4C AUC stats            [stage4_subspace_stats_gemma.slurm, INPUT_VARIANT=...]

After all 4A1s done:
Direction comparison    [stage4_direction_comparison_gemma.slurm]

After behavioral 4A2:
Prompt-type comparison  [stage4_prompt_type_comparison_gemma.slurm]
```

---

## Variant: behavioral

**What**: Refusal direction at `<channel|>` (end-of-thinking), contrasting complied vs. refused attack traces.

**Extraction**: `poc_stage4.extract_refusal_direction_behavioral`, forward pass on Stage 6 traces, no generation.

**Group split**: `qwen_run_success` — 66 complied / 66 refused (balanced at MAX_PER_GROUP=66)

**SLURM**: `stage4a1_gemma_behavioral.slurm` → `outputs/stage4/gemma4-e4b-it/refusal_direction_behavioral/`

| Metric | Value |
|--------|-------|
| Job ID | 597934 |
| Status | **COMPLETED** at 22:46 IDT |
| num_complied_train | 50 |
| num_refused_train | 50 |
| num_complied_val | 16 |
| num_refused_val | 16 |
| max_standardized_projection_separation | **1.71** (best_layer=30) |
| endthink_token_ids | [101] (`<channel\|>`) |
| 4A2 job | 598068 (**COMPLETED** 23:27 IDT) |
| Subspace shape | **[5, 2560]** |
| Focus layers | **L24, L21, L35, L18, L17** |
| harmful_ablation_scores | -11.92, -10.18, -9.05, -8.17, -8.02 |
| 4B job | 598142 (**COMPLETED** in 10:29) |
| 4C job | 598164 (**COMPLETED** in 2:37) |
| 4C AUC (best layer) | **0.7468** (layer=17, rank=4, p=0.0) |

**4A2 note**: KL_THRESHOLD=1000 + INDUCE_REFUSAL_THRESHOLD=-1000 (permissive) + ENABLE_THINKING=true. Gemma's directions have high harmless_ablation_KL (entangled with general LM behavior), so standard KL≤0.1 filter rejected all layers. Selection by lowest harmful_ablation_refusal_score instead.

---

## Variant: endofthink

**What**: Refusal direction at `<channel|>` (end-of-thinking), contrasting harmful vs. harmless vanilla prompts.

**Extraction**: `poc_stage4.extract_refusal_direction_endofthink`, generates 220+220 traces with thinking enabled.

**SLURM**: `stage4a1_gemma_endofthink.slurm` → `outputs/stage4/gemma4-e4b-it/refusal_direction_endofthink/`

| Metric | Value |
|--------|-------|
| Job ID | 597900 |
| Status | **COMPLETED** ~04:30 IDT (5h53m elapsed) |
| num_harmful_train_valid | 111 (54 skipped — no `<channel\|>` in 2048 max_gen_tokens) |
| num_harmless_train_valid | 111 (7 skipped) |
| num_harmful_val_valid | 35 |
| num_harmless_val_valid | 35 |
| endthink_token_ids | [101] (`<channel\|>`) |
| max_standardized_projection_separation | **9.458** (best_layer=28) |
| mean_standardized_projection_separation | 5.578 across all 42 layers |
| 4A2 job | 598578 (**COMPLETED** ~04:38 IDT, ~6 min) |
| Subspace shape | **[5, 2560]** |
| Focus layers | **L41, L16, L40, L38, L33** |
| harmful_ablation_scores | -15.16, -8.78, -8.50, -7.97, -7.91 |
| 4B job | 598579 (**COMPLETED** in 11:06) |
| 4C job | 598622 (**COMPLETED** ~05:05 IDT) |
| 4C AUC (best layer) | **0.6165** (layer=16, rank=3, p=0.0081) |

---

## Variant: startofthink

**What**: Refusal direction at `<|channel>thought` (start-of-thinking token), contrasting harmful vs. harmless.

**Extraction**: `poc_stage4.extract_refusal_direction_startofthink`, single forward pass per prompt (no generation needed).

**SLURM**: `stage4a1_gemma_startofthink.slurm` → `outputs/stage4/gemma4-e4b-it/refusal_direction_startofthink/`

| Metric | Value |
|--------|-------|
| Job ID | 597901 |
| Status | **COMPLETED** at 22:38 IDT (in ~1.5 min of computation after model load) |
| num_harmful_train | 165 |
| num_harmless_train | 165 |
| num_harmful_val | 55 |
| num_harmless_val | 55 |
| max_standardized_projection_separation | **8.87** (best_layer=26) |
| 4A2 job | 598066 (**COMPLETED** 23:27 IDT) |
| Subspace shape | **[5, 2560]** |
| Focus layers | **L30, L19, L20, L18, L21** |
| harmful_ablation_scores | -11.49, -11.03, -10.31, -10.21, -9.38 |
| 4B job | 598140 (**COMPLETED** in 7:55) |
| 4C job | 598165 (**COMPLETED** in 2:37) |
| 4C AUC (best layer) | **0.6912** (layer=18, rank=3, p=0.0) |

**Note**: score=8.87 at start-of-think is remarkably strong. Compare to Qwen3's 2.64 at this same time point. Gemma shows much stronger separation between harmful/harmless intent even before thinking begins. d_model=2560, n_layers=42.

---

## Variant: endofresponse

**What**: Refusal direction at EOS token (after full response), contrasting complied vs. refused attack traces.

**Extraction**: `poc_stage4.extract_refusal_direction_endofresponse`, forward pass on Stage 6 traces (max_seq_len=16000).

**Group split**: `qwen_run_success` — 66 complied / 66 refused (balanced at MAX_PER_GROUP=66)

**SLURM**: `stage4a1_gemma_endofresponse.slurm` → `outputs/stage4/gemma4-e4b-it/refusal_direction_endofresponse/`

| Metric | Value |
|--------|-------|
| Job ID | 597902 |
| Status | **COMPLETED** at 22:40 IDT |
| num_complied_train | 50 (66 available, used 50 for train+val=66 split) |
| num_refused_train | 50 |
| num_complied_val | 16 |
| num_refused_val | 16 |
| max_standardized_projection_separation | **2.22** (best_layer=25) |
| mean_sep | 1.43 across all layers |
| 4A2 job | 598067 (**COMPLETED** 23:27 IDT) |
| Subspace shape | **[5, 2560]** |
| Focus layers | **L16, L17, L26, L34, L31** |
| harmful_ablation_scores | -13.47, -9.68, -8.84, -8.12, -8.06 |
| 4B job | 598152 (**COMPLETED** in 9:46) |
| 4C job | 598187 (**COMPLETED** in 1:49) |
| 4C AUC (best layer) | **0.7388** (layer=16, rank=0, p=0.0) |

**Note**: score=2.22 at EOS — much stronger than Qwen3's 0.495. Gemma's post-response state clearly encodes refusal vs. compliance. Scientific caution: same 66 complied traces shared with behavioral. Provisional direction at layer 25.

---

## Direction Cosine Comparison — All Variants

Computed by `poc_stage4.compare_directions --base-dir outputs/stage4/gemma4-e4b-it`

| Pair | Selected cosine | Max cosine (best layer) | Best layer |
|------|----------------|------------------------|-----------|
| behavioral ↔ endofthink | -0.2354 | 0.6789 | L11 |
| behavioral ↔ startofthink | -0.1200 | 0.0854 | L8 |
| endofthink ↔ startofthink | 0.3102 | 0.4593 | L26 |
| endofresponse ↔ any | N/A — not included by compare_directions script | — | — |

**Direction comparison job**: 598623 (**COMPLETED** in <1 min at 05:03 IDT)

**Scientific interpretation:**
- behavioral ↔ endofthink: moderate anti-correlation at selected layers (L30 vs L28), but strongly correlated at L11 (0.679). Both capture post-thinking refusal, but from different contrast sets (attack traces vs. harmful/harmless prompts).
- behavioral ↔ startofthink: nearly orthogonal (max 0.085) — pre-thinking harmfulness signal and post-thinking behavioral split are different representational dimensions.
- endofthink ↔ startofthink: moderate correlation (0.459 at L26) — both involve the thinking phase; L26 is where both signals overlap most.

**Note**: Script auto-discovered behavioral/endofthink/startofthink from the base dir; `endofresponse` was skipped (`[compare] MISSING: refusal_direction — skipping`).

---

## Prompt-Type Comparison

**Script**: `poc_stage4.compare_prompt_projections`, behavioral subspace, gemma_traces_full_1_11_eos_fixed

**SLURM**: `stage4_prompt_type_comparison_gemma.slurm`

**Scientific question**: Does a puzzle-attack prompt project onto the harmless or direct-harmful side of Gemma's refusal subspace?

**Job**: 598163 (**COMPLETED** 01:13 IDT, 1h20m) — 48 harmless, 31 direct_harm, 220 puzzle traces; 22,425 rows written.

**EOS fix**: `compare_prompt_projections.py` `_find_eos_pos` now accepts list of EOS IDs; caller reads `model.generation_config.eos_token_id` to get all effective EOS tokens (Gemma: [1, 106, 50]).

Direction convention: `dir = mean(complied) - mean(refused)`. Positive = complied-like, negative = refused-like.

**Projections at best layer (L17, rank=4) — mean per prompt type × time point:**

| Time point | harmless | direct_harm | puzzle(complied) | puzzle(refused) |
|------------|----------|-------------|-----------------|-----------------|
| startofthink | -0.84 | -0.92 | **-6.81** | **-7.91** |
| endofthink | -12.63 | -17.15 | **-8.00** | -16.15 |
| endofresponse | -2.53 | -5.00 | -3.44 | -4.56 |

**Key findings:**
1. **startofthink**: Puzzle attacks project ~8-9× more negatively than both harmless (-0.84) and direct_harm (-0.92), suggesting the model recognises the puzzle format as a distinctive input type before reasoning begins — even more so than recognising direct harm.
2. **endofthink**: Complied puzzle attacks (-8.00) are far LESS refused-like than harmless (-12.63) or direct_harm (-17.15) after thinking. The hijacking works by shifting the model into a "task-solving" mode during CoT, away from refusal. Refused puzzle attacks (-16.15) converge toward direct_harm.
3. **endofresponse**: Complied puzzle attacks (-3.44) land between harmless (-2.53) and direct_harm (-5.00); refused attacks (-4.56) land near direct_harm.

**Interpretation**: In Gemma, CoT hijacking is visible as a large jump in behavioural subspace projection between startofthink (very refused-like) and endofthink (less refused than harmless) for traces that ultimately comply. The thinking process itself is where the "compliance drift" occurs.

---

## Comparison to Qwen3-14B Results

| Metric | Qwen3-14B | Gemma 4 E4B-it |
|--------|-----------|----------------|
| behavioral max_sep | 0.92 | **1.71** (L30) ✅ |
| endofthink max_sep | 7.44 | **9.458** (L28) ✅ |
| startofthink max_sep | 2.64 | **8.87** (L26) ✅ |
| endofresponse max_sep | 0.495 (weak) | **2.22** (L25) ✅ |
| behavioral AUC | 0.750 (L26) | **0.7468** (L17, rank=4) ✅ |
| endofthink AUC | 0.750 (L29) | **0.6165** (L16, rank=3) ✅ |
| startofthink AUC | 0.731 (L0) | **0.6912** (L18, rank=3) ✅ |
| endofresponse AUC | — | **0.7388** (L16, rank=0) ✅ |
| behavioral⊥endofthink cosine | — | — |

**Early finding**: Gemma 4 shows dramatically stronger refusal signal at both startofthink (8.87 vs 2.64) and endofresponse (2.22 vs 0.495) compared to Qwen3-14B. The pre-thinking separation being higher than Qwen3's pre-thinking score suggests Gemma has stronger a priori harmfulness detection before reasoning begins.

**Prompt-type comparison highlight**: At startofthink, puzzle attacks project ~8-9× more negatively than direct_harm in the behavioral subspace — the model recognises the puzzle format as distinctive before reasoning. Complied attacks then "drift" toward compliance during thinking (endofthink: -8.0 vs harmless -12.6), while refused attacks converge toward direct_harm (-16.1 vs -17.2).
