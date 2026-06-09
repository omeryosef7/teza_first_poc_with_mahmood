# Stage 4.6 — Controlled Ablation Plan

## Research Question

Does the puzzle wrapper length causally modulate CoT hijacking onset and success rate?
Does thinking mode (on vs off) affect hijacking susceptibility?

## Design

**Source prompt selection**: 1 example per goal_index (4 goals), deterministic seed=42.
Preference for pilot examples; tie-break by lowest conversation_id.

**Five conditions per source (4 × 5 = 20 total generations):**

| Condition | Puzzle fraction | Thinking | Description |
|---|---|---|---|
| A | 100% | on | Full prompt — identity baseline |
| B | ~50% | on | Half puzzle tokens deleted |
| C | ~25% | on | 75% puzzle tokens deleted |
| D | 0% | on | All puzzle tokens deleted; only target + answer cue |
| E | 100% | off | Full prompt, no thinking (direct generation) |

**Invariants enforced across A–D:**
- Target span token sequence identical (SHA256 match)
- Answer cue token sequence identical (SHA256 match)
- Transformed prompt is deletion-only subsequence of source
- Token lengths: A ≥ B ≥ C ≥ D

## Generation Config

- Model: Qwen/Qwen3-14B (revision 40c069824f4251a91eefaf281ebe4c544efd3e18)
- `do_sample=False` → deterministic; run once per condition
- `seed=0`, `max_new_tokens=16384`

## Outcomes

- Primary: `sr_success` (StrongREJECT binary)
- Secondary: `judge_success` (Gemini LLM judge)
- Continuous: `strongreject_score`
- Exploratory: `think_token_count`, `thinking_segmentation_status`

## Analysis Strategy

- Paired comparisons by source prompt (not pooled)
- N=4 pairs per comparison → report counts and effect direction, not significance
- Bootstrap CIs for continuous outcomes (seed=42, n_boot=1000)
- Wilcoxon signed-rank for paired conditions (exact, continuity-corrected)
- Tables: condition_summary, goal_condition_summary, thinking_mode_comparison, puzzle_fraction_trend

## Scope Constraints

- Max 20 generations (4 × 5; no seed replication needed — deterministic)
- Do NOT modify `outputs/stage4/token_dynamics/full_20260604_101929/` (frozen)
- Do NOT claim causal mechanism without replication on larger N
