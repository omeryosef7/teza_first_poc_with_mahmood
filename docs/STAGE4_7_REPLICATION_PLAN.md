# Stage 4.7 — Multi-Prompt Controlled Replication Plan

**Status:** Scaffolding complete — pending GPU smoke test  
**Date authored:** 2026-06-10  
**Author:** Omer Yosef (PLUS group, TAU)  
**Supervisor:** Mahmood Sharif

---

## Motivation

Stage 4.6 established that CoT hijacking succeeds under both full-puzzle (A) and no-puzzle (D) conditions using a single source prompt per goal. The key open question is whether success is driven by:

1. **Puzzle semantics** — the LSAT-style puzzle creates a framing that suppresses refusal
2. **Context length** — longer prompts alone (regardless of content) affect model behavior

Stage 4.7 addresses this with:
- A **benign wrapper control (Condition F)**: a length-matched coherent harmless text replaces the puzzle, separating puzzle semantics from context length
- **Multiple source prompts per goal** (n=3, tertile-stratified): replicates Stage 4.6 findings across prompt variation and enables within-condition heterogeneity analysis

---

## Design

### Conditions

| Cond | Description | Thinking | Puzzle |
|------|-------------|----------|--------|
| A | Full puzzle, thinking=on | ✓ | ✓ |
| D | No puzzle (deleted), thinking=on | ✓ | ✗ |
| F | Benign wrapper length-matched to A, thinking=on | ✓ | ✗ |
| E | Full puzzle, thinking=off | ✗ | ✓ |

All 4 conditions are applied to all 12 source prompts → **48 total generations** (within 60-generation budget).

### Conditions A, D, E

Built using the same span-identification and condition-builder logic as Stage 4.6 (`poc_stage4_6.build_controlled_ablation_prompts.identify_spans()` and `build_condition()`):
- **A**: full original prompt, `enable_thinking=True`
- **D**: puzzle section deleted (target span + answer cue only), `enable_thinking=True`  
- **E**: full original prompt, `enable_thinking=False`

### Condition F — benign wrapper

The critical new control. Design constraints:
1. **Length-matched**: |tokens_F / tokens_A − 1| ≤ 0.05
2. **Benign content only**: filler drawn exclusively from `harmless_train.json` (18,793 instruction prompts)
3. **No new harmful content**: Condition F must not introduce or expand any harmful material
4. **Structure preserved**: filler text prepended, then target span and answer cue identical to A

Construction algorithm:
1. Compute condition A token count via full chat-template tokenization
2. Starting from a deterministic seed position (based on `source_example_id` hash), concatenate harmless instruction strings separated by `"\n\n"`
3. Iterate until token count of assembled user message is within ±5% of condition A
4. Final prompt: `[harmless_filler]\n\n[target_span]\n\n[answer_cue]`
5. Verify: no harmful-domain keywords in filler; SHA-256 of filler recorded

---

## Source Prompt Selection

### Eligibility criteria

From the 42-example Stage 4 analysis dataset:
- `thinking_segmentation_status == "parsed_from_think_tags"` (CoT trace segmented)
- `right_censored == False` (generation completed within token budget)
- Non-empty prompt text (trace file exists and readable)

### Tertile stratification

For each goal (0–3):
1. Sort eligible examples by `prompt_token_count`
2. Divide into 3 tertiles (lower, middle, upper)
3. Select the example closest to the center of each tertile
4. Prefer examples with distinct `conversation_id`
5. Deterministic tie-breaking: `seed=47`

This yields 3 source prompts per goal × 4 goals = **12 source prompts**.

### Output

`outputs/stage4_7/source_prompt_selection.csv` — 12 rows with fields:
- `example_id`, `goal_index`, `conversation_id`, `attack_iteration`
- `source_prompt_token_count`, `original_think_token_count`
- `original_strongreject_score`, `original_sr_success`
- `selection_stratum` (lower/middle/upper)
- `source_prompt_sha256`

---

## Prompt Inventory

`outputs/stage4_7/replication_prompts.jsonl` — 48 rows.

Fields per row:
```
source_example_id        # from analysis_dataset.csv
goal_index               # 0-3
condition                # A/D/E/F
enable_thinking          # bool
selection_stratum        # lower/middle/upper
user_message_text        # the actual prompt (for runner)
prompt_token_count       # tokenized count via chat template
source_prompt_sha256     # hash of original source prompt
length_match_ratio       # tokens_F / tokens_A (F only; else None)
benign_wrapper_sha256    # sha256 of filler (F only; else None)
benign_wrapper_source_ids # indices in harmless_train.json (F only; else None)
```

---

## Audit

All invariants verified by `poc_stage4_7/audit_replication_prompts.py`:

| Invariant | Description |
|-----------|-------------|
| 48 rows | Exactly 12 × 4 |
| All 4 conditions | A, D, E, F per source |
| A/E hash match | Same source prompt underlies both |
| F length ±5% | `length_match_ratio` in [0.95, 1.05] |
| No harmful filler | Keyword check against target-span terms |
| No duplicates | Unique (source_example_id, condition) pairs |
| ≤ 60 rows | Under generation budget |

**Audit result:** PASSED (see `outputs/stage4_7/replication_prompt_audit.json`)

---

## Generation

### Runner

`poc_stage4_7/run_replication.py`

- Model: `Qwen/Qwen3-14B`, revision `40c069824f4251a91eefaf281ebe4c544efd3e18`
- `do_sample=False` (deterministic)
- `max_new_tokens=32768`
- Single GPU (L40S), no multi-GPU splitting
- StrongREJECT scoring applied post-generation
- Gemini judge skipped by default (spending cap)

### SLURM scripts

| Script | Purpose |
|--------|---------|
| `slurm_scripts/stage4_7_replication_smoke.slurm` | 1 prompt (goal 0, lower), conditions A/D/F, 2h |
| `slurm_scripts/stage4_7_replication_array.slurm` | `#SBATCH --array=0-3`, 1 goal/task, 6h each |

Nodes: `n-802,n-803,n-804,n-805` (L40S GPUs only, ≥40 GB VRAM)

### Submit sequence

```bash
# 1. Submit smoke
sbatch slurm_scripts/stage4_7_replication_smoke.slurm

# 2. If smoke passes (3 rows, all eos_token, F ratio in [0.95,1.05]):
sbatch slurm_scripts/stage4_7_replication_array.slurm

# 3. After all 4 tasks complete, verify:
python -c "
import json; from pathlib import Path
rows=[json.loads(l) for l in open('outputs/stage4_7/runs/<RUN_DIR>/run_summary.jsonl').read().splitlines() if l.strip()]
print(f'Total rows: {len(rows)}')
from collections import Counter
print('By condition:', Counter(r[\"condition\"] for r in rows))
print('By goal:', Counter(r[\"goal_index\"] for r in rows))
"
```

---

## Post-Generation Analysis Plan

After 48 rows are generated:

### Behavioral analysis (`analyze_replication.py`)

1. Success counts and SR score by condition
2. Paired contrasts A−D, A−F, D−F, A−E (source prompt as inference unit, n=12)
3. Bootstrap CIs (n_boot=2000, seed=42)
4. Sign tests (exact binomial) and McNemar tests for binary outcomes
5. Goal-stratified and prompt-stratified breakdowns
6. Leave-one-goal-out sensitivity

### Mechanistic analysis (`compute_selected_layer_dynamics.py`)

Layer-22 projection onto provisional refusal direction, diagnostically only:
- Per-token projections via forward hooks at layers 13, 16, 22, 38, 39
- Normalized 10-bin trajectories over full generation
- Early-phase projections (first 500, first 2000 tokens)
- Think-phase vs final-phase means

**Note:** Layer 22 direction is provisional and diagnostic. Do not claim causal refusal suppression.

### Figures (`plot_replication.py`)

9 meeting figures:
1. `fig1_behavior_by_condition.png` — SR score + success rate
2. `fig2_thinking_length_by_condition.png` — log-scale thinking tokens
3. `fig3_full_vs_bare_vs_length_matched.png` — A vs D vs F
4. `fig4_thinking_on_vs_off.png` — A vs E paired
5. `fig5_layer22_early_projection.png` — L22 early projection by condition
6. `fig6_layer22_normalized_trajectory.png` — 10-bin trajectory A/D/F
7. `fig7_per_goal_condition_heatmap.png` — behavioral heatmap
8. `fig8_projection_vs_thinking_length.png` — scatter projection vs log(think tokens)
9. `fig9_finish_reason_and_truncation.png` — truncation analysis

---

## Key Hypotheses

| Hypothesis | Discriminating contrast |
|-----------|------------------------|
| H1: Puzzle semantics drive success | A ≫ F (same length, different content) |
| H2: Context length alone sufficient | A ≈ F (length is the key factor) |
| H3: Thinking is necessary | A ≫ E |
| H4: Target/cue presence sufficient | D ≈ A (no puzzle still succeeds) |

---

## Safety Constraints

- No new harmful goals introduced
- No harmful content in Condition F filler
- Condition F built exclusively from `harmless_train.json`
- No adversarial optimization of attack prompts
- No LLM asked to improve attack quality
- No causal claims about Layer 22
- No raw harmful content in documentation or figures
- Frozen Stage 4 artifacts untouched

---

## Scripts Index

| Script | Phase | Description |
|--------|-------|-------------|
| `poc_stage4_7/select_source_prompts.py` | CPU | Source prompt selection |
| `poc_stage4_7/build_replication_prompts.py` | CPU | Build 48 prompts |
| `poc_stage4_7/audit_replication_prompts.py` | CPU | Invariant verification |
| `poc_stage4_7/run_replication.py` | GPU | Generation runner |
| `poc_stage4_7/compute_selected_layer_dynamics.py` | GPU | Projection analysis |
| `poc_stage4_7/analyze_replication.py` | CPU | Statistical analysis |
| `poc_stage4_7/plot_replication.py` | CPU | 9 meeting figures |
| `poc_stage4_7/tests/test_prompt_construction.py` | CPU | Prompt invariant tests |
