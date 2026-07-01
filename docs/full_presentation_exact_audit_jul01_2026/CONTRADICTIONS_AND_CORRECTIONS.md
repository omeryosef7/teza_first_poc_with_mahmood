# Contradictions and Required Corrections

**Audit date:** 2026-07-01  
**Auditor:** Claude Code (analysis-only, no new model runs)

This document lists every factual discrepancy found between presentation documents, code, and raw data. For each contradiction the authoritative source is identified and the correction required is stated.

---

## C1 — Puzzle-Specific Goals for Qwen3

**Contradiction:**
- `MAHMOOD_ANALYSIS_ONLY_BRIEF_JUN30.md` Q1 answer: goals {0, 5, 7, 8} = 4 puzzle-specific goals
- Sprint summary §5 "puzzle-specific" analysis: goals {0, 2, 3, 5, 8, 9} = 6 goals mentioned
- Meeting analysis brief elsewhere: "4 puzzle-specific goals" vs "6 goals show interaction effect"

**Root cause:** "Puzzle-specific" is defined differently in different contexts.
- Scheme A (from `06_goal_categories.csv`): goals classified as `puzzle_specific` are those where the puzzle condition (A) has significantly higher ASR than the direct-harm condition (D) → {0, 5, 7, 8} = 4 goals
- Goal 2 (chemical weapons): D=83.3%, so it's `puzzle_hurts` (D beats A), NOT puzzle-specific
- Goal 3 (terrorism): D=94.4% → `generally_vulnerable` not puzzle-specific
- Goals {0, 2, 3, 5, 8, 9} is the set of goals where interaction term (A-E) - (D-G) > 0 (positive interaction) — DIFFERENT from puzzle-specific

**Correction required:**
- Slide 5 title and claims: "4 goals are puzzle-specific (A ≥ D)" not "6 goals"
- Clarify: "6 goals show a positive interaction effect" is a SEPARATE claim from "4 goals are puzzle-specific"
- The 6-goal claim (if used) must specify: these are goals where (A-E) > (D-G), not where A > D

**Authoritative source:** `outputs/meeting/mahmood_analysis_only_jun30_20260630_193423/06_goal_categories.csv` (Scheme A column); `outputs/stage4/factorial_balanced/qwen3/goal_level_effects.csv` (ASR_A vs ASR_D per goal)

---

## C2 — Gemma4 LOGO AUC: 0.806 vs 0.809

**Contradiction:**
- `probe_transfer_auc.csv` column means: 0.806 (arithmetic mean of all 11 fold AUCs including 3 invalid folds)
- `conservative_logo_auc.json`: 0.8094 (mean of 8 valid folds, excluding goals 1, 2, 10 where n_minority < 3)
- Sprint summary says "0.806" and "8/11 valid folds (excluding goals 1, 2, 10)"

**Root cause:** The sprint is ambiguous — it cites 0.806 but also says only 8/11 folds are valid. The 0.806 includes all 11 folds.

**Correction required:**
- Presentation should say: "Gemma4 LOGO AUC = **0.809** (8 valid folds; goals 1, 2, 10 excluded as near-one-class)"
- If 0.806 is used, must note it includes 3 invalid folds (defensively inflated by lucky AUC values in degenerate folds)
- **Recommended:** Use 0.809 as the primary number with footnote "(0.806 including 3 near-one-class folds)"

**Authoritative source:** `outputs/stage4/factorial_analysis/conservative_logo_auc.json` → 0.8094; `outputs/stage4/factorial_analysis/logo_fold_details.csv`

---

## C3 — Qwen3 Interaction: 0.3751 vs 0.431

**Contradiction:**
- `goal_clustered_interaction_summary.json`: qwen3 interaction = 0.3751, p = 0.0268
- `factorial_analysis/interaction_effects.csv`: qwen3 interaction = 0.431, n = 26 sources

**Root cause:** These are DIFFERENT analysis levels — NOT a contradiction.
- 0.3751 = **goal-level** analysis: first average ASR across sources within each goal, then compute (p_A - p_E) - (p_D - p_G) at the goal level, then average across 11 goals
- 0.431 = **source-level** analysis: compute interaction for each unique source prompt, average across 26 sources

**Correction required:**
- Presentation must clearly distinguish which number is being shown
- "The puzzle interaction effect is 0.38 (goal-level) or 0.43 (source-level)" — NOT interchangeable
- If only one is shown, label it precisely
- 0.3751 (goal-level, n=11) has formal statistical test (p=0.0268, goal-clustered bootstrap)
- 0.431 (source-level, n=26) was NOT formally tested in `interaction_effects.csv`
- **Recommended for presentation:** Use 0.38 with "p=0.027, 5,000-sample bootstrap, goal-clustered" label

**Authoritative source:** `outputs/stage4/factorial_balanced/goal_clustered_interaction_summary.json` (0.3751); `outputs/stage4/factorial_analysis/interaction_effects.csv` (0.431)

---

## C4 — P16 Sprint Table Discrepancies

**Contradiction:**
- Sprint summary P16 table includes `zero_attn_L22` and `zero_mlp_L22` conditions
- `p16_sr_scored.jsonl` contains NO L22 rows (only L3, L10, L17, L26, L32, L39)
- Sprint says `zero_mlp_L26 = 4/9 = 44%` but data shows 2/8 = 25%

**Root cause:** Sprint P16 table was written from an intermediate run. The final scored file (`p16_sr_scored.jsonl`) contains results from a different (possibly final) run with L22 excluded and L26 MLP results updated.

**Correction required:**
- Drop L22 from all P16 tables in the presentation
- Correct zero_mlp_L26: use **2/8 = 25%** not 44%
- Use only the values from `p16_sr_scored.jsonl` (authoritative final file)

**Authoritative source:** `outputs/stage4/intervention_judge_validation/p16_sr_scored.jsonl`

---

## C5 — P16 Baseline ASR: 62% vs 55.6%

**Contradiction:**
- Sprint summary: "baseline = 5/9 = 55.6%"
- Data: baseline has 9 total rows, but 1 row has NaN api_score → 8 valid rows → 5/8 = 62.5%

**Root cause:** Sprint denominator counted all 9 rows; valid-only denominator gives 8 rows.

**Correction required:**
- Use **5/8 = 62.5%** as P16 baseline (valid-only counting, consistent with all other experiments)
- The 1 NaN baseline row is excluded from valid count → N_valid = 8, not 9

**Authoritative source:** `outputs/stage4/intervention_judge_validation/p16_sr_scored.jsonl` (row counting)

---

## C6 — CoT Condition Names

**Contradiction:**
- Documentation and meeting brief use: "forced_own_cot", "forced_cross_cot"
- Actual data field `condition` in `cot_causal_role_sr_scored.jsonl`: "forced_own_thinking", "forced_cross_thinking"

**Root cause:** The scripts used different names than the documentation.

**Correction required:**
- Rename in presentation: "forced_own_cot" → "forced_own_thinking"
- Rename in presentation: "forced_cross_cot" → "forced_cross_thinking"
- This affects slide 9 condition labels

**Authoritative source:** `outputs/stage4/intervention_judge_validation/cot_causal_role_sr_scored.jsonl` (condition field)

---

## C7 — sr_success Field Unreliability

**Contradiction:**
- All intervention files (p11, p14, p16, cot_causal_role) show `sr_success=True` for ALL rows
- The `sr_score` field shows `0.5` (a placeholder) for all rows in these files
- Since 0.5 ≥ 0.5, `sr_success` (= sr_score ≥ 0.5) is always True

**Correct field:** `sr_api_binary` (True when sr_api_score ≥ 0.5, where sr_api_score comes from the actual API call)

**Correction required:**
- All intervention ASR calculations must use `sr_api_binary`, NOT `sr_success`
- Any presentation claim about intervention ASR built on `sr_success` is WRONG
- Verify all final slide numbers use `sr_api_binary`

**Note:** The factorial_attack_dataset.jsonl uses `sr_success` correctly (computed from actual SR scores, not from a placeholder). The unreliability applies only to the intervention-judge-validation files.

**Authoritative source:** Code inspection; `p11_sr_scored.jsonl` field values

---

## C8 — 13.97× Token Ratio Attribution

**Contradiction:**
- Some documentation attributes the 13.97× thinking-token ratio to the CoT causal role experiment
- The actual source is Stage 4.7 (multi-prompt behavioral replication)

**Root cause:** Multiple experiments measured thinking token counts; the 13.97× number comes specifically from the 12-source greedy-decoding comparison in Stage 4.7.

**Correction required:**
- Slide 9 (CoT role): do NOT present 13.97× as a finding from the CoT causal role experiment
- Correct attribution: "Stage 4.7 (multi-prompt replication): Condition A generates 13.97× more thinking tokens than Condition F (matched-benign)"
- The CoT causal role experiment (n=32) does have token count differences but 13.97× is NOT from it

**Authoritative source:** `SPRINT_SUMMARY_JUN14_30.md` §4 (Stage 4.7)

---

## C9 — 220-per-model vs Factorial Dataset (Slide 3 vs Slide 4)

**Contradiction:**
- Slide 3 claims "220 source prompts per model" (11 goals × 20 variants)
- Factorial Condition A has: 292 Qwen3 rows + 232 Gemma4 rows (more than 220 due to multiple seeds)
- Slide 4 uses the 1,116-row factorial dataset

**Root cause:** These are DIFFERENT datasets:
- Slide 3 uses the Stage 6 behavioral dataset: 220 unique source prompts per model, 1 seed each
- Slide 4 uses the full factorial dataset: same source prompts but with multiple seeds per source (≥ 4 seeds)

**Correction required:**
- Never mix Slide 3 ASRs (220-prompt, 1 seed) with Slide 4 ASRs (factorial, multiple seeds)
- Slide 3 ASR: Qwen3 = 113/220 = 51.4%, Gemma4 = 66/220 = 30.0%
- Slide 4 ASR (Condition A): Qwen3 = 250/668 = 37.4% (full factorial, all conditions), or if Condition A only: different denominator
- The 37.4% full-factorial ASR is NOT the Slide 3 number; Slide 3 uses one seed = one-shot ASR

**Authoritative source:** `SPRINT_SUMMARY_JUN14_30.md` §3 (220-per-model table); `outputs/stage4/factorial_attack_dataset.jsonl` (1,116 rows)

---

## C10 — 0/160 Causal Candidates: Per-Model Breakdown

**Contradiction:**
- Sprint summary: "0/160 causal direction candidates pass KL + steering thresholds"
- Unclear whether 160 = 80 Qwen3 + 80 Gemma4, or 160 Qwen3 only, or another split

**Status:** NOT FULLY RESOLVABLE from current artifacts. The Stage 4A2 checkpoint files (`outputs/stage4/*/intervention_candidate_scores.checkpoint.jsonl`) were not read in this audit.

**Correction required:**
- Do not state "0/160 for both models combined" unless the 80+80 split is confirmed
- Safe language: "0 direction candidates passed causal validation across all tested directions"
- If only Qwen3 was validated causally, say "0/80 for Qwen3; Gemma4 causal validation pending"

**Authoritative source:** `SPRINT_SUMMARY_JUN14_30.md` §7 (the primary claim); Stage 4A2 checkpoint files (not read)

---

## C11 — P14 NaN Handling Inconsistency

**Contradiction:**
- Sprint P14 table: gen_thinking_L10 shows N=10, ASR=40% (4/10) — counting NaN row as failure in denominator
- Sprint P14 table: gen_thinking_L26 shows N=7, ASR=0% (0/7) — excluding NaN rows from denominator
- This is INCONSISTENT policy within the same table

**Correction required:**
- Use consistent NaN policy: EXCLUDE NaN rows from denominator ("valid-only counting")
- Corrected gen_thinking_L10: N_valid=9 (1 NaN excluded), 4/9 = 44.4% NOT 40%
- Corrected gen_thinking_L26: N_valid=7 (3 NaN excluded), 0/7 = 0% (no change)

**Authoritative source:** `outputs/stage4/intervention_judge_validation/p14_sr_scored.jsonl`

---

## C12 — Gemma4 n_goals_positive in Interaction Summary

**Contradiction:**
- Task specification stated: "Gemma4 n_goals_positive = 5"
- `goal_clustered_interaction_summary.json` field `n_goals_positive`: 6 (for Gemma4)

**Correction required:**
- Use 6 (from the JSON file), NOT 5
- Gemma4 has 6 goals with positive interaction direction (not 5)

**Authoritative source:** `outputs/stage4/factorial_balanced/goal_clustered_interaction_summary.json`

---

## Summary: Numbers That Change in the Presentation

| Location | Wrong value | Correct value | Source |
|----------|-------------|---------------|--------|
| Slide 5: # puzzle-specific goals (Qwen3) | 6 | **4** (Scheme A) | goal_categories.csv |
| Slide 6: Gemma4 LOGO AUC | 0.806 | **0.809** (8 valid folds) | conservative_logo_auc.json |
| P16 zero_mlp_L26 | 44% | **25%** | p16_sr_scored.jsonl |
| P16 baseline | 55.6% (5/9) | **62.5%** (5/8) | p16_sr_scored.jsonl |
| P14 gen_thinking_L10 | 40% (4/10) | **44.4%** (4/9) | p14_sr_scored.jsonl |
| Slide 9: CoT condition names | forced_own_cot | **forced_own_thinking** | cot_causal_role data |
| Slide 9: 13.97× attribution | CoT experiment | **Stage 4.7** | SPRINT_SUMMARY |
| Gemma4 n_goals_positive | 5 | **6** | interaction_summary.json |
| Slide 5: goals called "puzzle-specific" | {0,2,3,5,8,9} | **{0,5,7,8}** | goal_categories.csv |
