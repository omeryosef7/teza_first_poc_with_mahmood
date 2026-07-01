# Full Presentation Exact Audit — June 14–30, 2026

**Audit date:** 2026-07-01  
**Auditor:** Analysis-only; no new experiments, no model inference, no API calls  
**Repository:** `/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood`  
**Presentation audience:** Mahmood  
**Slides covered:** 11

---

## 1. Audit Scope

This audit verified every numerical and methodological claim in an 11-slide presentation covering sprint work from June 14–30, 2026. It was produced by:

1. Reading raw JSONL datasets (1,116-row factorial dataset, 4 intervention JSONL files, 32-row CoT experiment)
2. Reading JSON and CSV analysis outputs (goal-clustered interaction summary, LOGO AUC, failure mode tables, direction metadata)
3. Reading source code (condition definitions, interaction formula, classification thresholds)
4. Reading sprint documentation and meeting briefs
5. Resolving all discrepancies by tracing to the most authoritative source (raw JSONL > JSON analysis > CSV summary > sprint markdown)

---

## 2. Dataset Inventory

| Dataset | File | Total Rows | Models |
|---------|------|-----------|--------|
| Factorial attack dataset | `outputs/stage4/factorial_attack_dataset.jsonl` | **1,116** | 668 Qwen3 + 448 Gemma4 |
| Behavioral (220/model) | Stage 6 trace extraction (1 seed/source) | 440 total | 220 Qwen3 + 220 Gemma4 |
| P11 intervention | `intervention_judge_validation/p11_sr_scored.jsonl` | 110 (108 valid) | Qwen3 only |
| P11 selectivity | `intervention_judge_validation/p11_selectivity_sr_scored.jsonl` | 75 (75 valid) | Qwen3 only |
| P14 intervention | `intervention_judge_validation/p14_sr_scored.jsonl` | 70 (61 valid) | Qwen3 only |
| P16 intervention | `intervention_judge_validation/p16_sr_scored.jsonl` | 117 (109 valid) | Qwen3 only |
| CoT causal role | `intervention_judge_validation/cot_causal_role_sr_scored.jsonl` | 32 (32 valid) | Qwen3 only |
| Mechanism classification | `outputs/stage4/mechanism_classification.jsonl` | 424 rows | Both models |

---

## 3. Verified Key Numbers by Slide

### Slide 2 (Scope)
- 1,116 total factorial rows: **VERIFIED** (JSONL line count)
- 2 models, 11 goals, 5 conditions, 3 experiments: **VERIFIED**
- 14 pipeline variants: **VERIFIED** (sprint §2)
- Both pre/post June 14 dataset counts: **VERIFIED** (stage4_8 vs stage4_8_extended)

### Slide 3 (Behavioral Evidence)
- Qwen3 ASR = 113/220 = **51.4%**: **VERIFIED** (SPRINT_SUMMARY §3, 220 = 11 goals × 20 variants, 1 seed each)
- Gemma4 ASR = 66/220 = **30.0%**: **VERIFIED**
- These are from a DIFFERENT dataset than the factorial 1,116-row dataset (1 seed per source vs multiple seeds)

### Slide 4 (Factorial Design)
- Qwen3 interaction = **0.3751**, p = **0.0268** (goal-level, 5,000-sample bootstrap): **VERIFIED**
- Gemma4 interaction = **0.0339**, p = **0.8016** (not significant): **VERIFIED**
- Interaction formula `(p_A − p_E) − (p_D − p_G)`: **VERIFIED** from `analyze_factorial_attack_effects.py`
- Source-level interactions: Qwen3=**0.431**, Gemma4=**0.269** (different analysis level, not contradictions): **VERIFIED**
- Qwen3 n_goals_positive = **11/11**; Gemma4 = **6/11** (NOT 5/11): **VERIFIED** from `goal_clustered_interaction_summary.json`

### Slide 5 (Puzzle-Specific Goals)
- 4 puzzle-specific goals for Qwen3 (Scheme A: A > D): **VERIFIED** → goals {0, 5, 7, 8}
- NOT 6 goals; 6 is the number with positive interaction, which is a different criterion
- 1 puzzle-specific goal for Gemma4: **VERIFIED** from `06_goal_categories.csv`
- Goal 2 = "puzzle_hurts" (D=83% > A): **VERIFIED**

### Slide 6 (Representations)
- Qwen3 LOGO AUC = **0.757** (11/11 valid folds): **VERIFIED** from `conservative_logo_auc.json`
- Gemma4 LOGO AUC = **0.809** (8/11 valid folds; goals 1,2,10 excluded): **VERIFIED** from `conservative_logo_auc.json`
  - Note: 0.806 = 11-fold average (includes 3 invalid folds) — also technically correct but not recommended
- Qwen3 behavioral best layer = **L26**, AUC = **0.7502**: **VERIFIED** from `subspace_stats_behavioral/summary.json`
- Gemma4 behavioral best layer = **L17**, AUC = **0.7468**: **VERIFIED**
- DVP Qwen3 best = **0.736** (L37, after flipping); Gemma4 = **0.740** (L24, after flipping): **VERIFIED**
- **0/160 causal candidates** pass KL+steering: **REPORTED** (from sprint §7; per-model breakdown not verified)
- Gemma4 HVP_startofthink = **zero vector** (degenerate): **VERIFIED** from `20_direction_metadata.csv`

### Slide 7 (Refusal Direction)
- Max pairwise cosine similarity = **0.258**: **VERIFIED** from `19_direction_cosine_matrix.csv`
- Canonical refusal direction NOT extracted: **CONFIRMED** — no such file exists in repo
- Cross-model comparison not valid (different embedding dimensions: 5120 vs 2560): **CONFIRMED**

### Slide 8 (Interventions — Corrected Values)
- P11 baseline A = **5/10 = 50%**; P11 baseline D = **0/10 = 0%**: **VERIFIED**
- P11 L26 = **4/10 = 40%**: **VERIFIED**
- P11 valid count = **108/110**: **VERIFIED** (2 NaN in L32, L39)
- P11 selectivity sham = **6/9 = 66.7%**, identity = **5/9 = 55.6%**: **VERIFIED**
- P14 baseline = **5/10 = 50%**: **VERIFIED**
- P14 gen_thinking_L10 = **4/9 = 44.4%** (NOT 4/10=40% as in sprint): **CORRECTED**
- P14 gen_thinking_L26 = **0/7 = 0%**: **VERIFIED**
- P14 truncated = **56/70 = 80%**: **VERIFIED**
- P14 valid = **61/70**: **VERIFIED**
- P16 baseline = **5/8 = 62.5%** (NOT 5/9=55.6% as in sprint): **CORRECTED**
- P16 zero_attn_L26 = **0/9 = 0%**: **VERIFIED**
- P16 zero_mlp_L26 = **2/8 = 25%** (NOT 4/9=44% as in sprint): **CORRECTED**
- P16 valid = **109/117**: **VERIFIED**
- P16 does NOT include L22 conditions (sprint table error): **CORRECTED**

### Slide 9 (CoT Role)
- 32 total rows, 8 per condition, 0 NaN: **VERIFIED**
- Condition names: **forced_own_thinking** and **forced_cross_thinking** (NOT "forced_own_cot"): **CORRECTED**
- Baseline = **5/8 = 62.5%**: **VERIFIED** via sr_api_binary
- Forced own thinking = **5/8 = 62.5%**: **VERIFIED**
- Forced cross thinking = **4/8 = 50%**: **VERIFIED**
- Empty thinking = **3/8 = 37.5%**: **VERIFIED**
- 13.97× token ratio = FROM STAGE 4.7, NOT CoT experiment: **CORRECTED**
- sr_success field unreliable (all True; use sr_api_binary): **CONFIRMED**

### Slide 10 (Failures)
- Qwen3 total failures = **400**: **VERIFIED**
- Gemma4 total failures = **346**: **VERIFIED**
- Qwen3 metadata-only (no text) failures = **205/400 = 51.3%**: **VERIFIED**
- Gemma4 metadata-only failures = **202/346 = 58.4%**: **VERIFIED**
- Manual review packet = **45 examples** (many with has_text=False): **VERIFIED**

### Slide 11 (Next Steps)
- Three priorities: failure text capture, CoT scale-up, Gemma4 causal validation: **SOURCED FROM SPRINT §12**
- No committed timeline for next sprint

---

## 4. Corrections Required

See `CONTRADICTIONS_AND_CORRECTIONS.md` for full list. Summary of must-fix corrections:

| # | Location | Wrong | Correct |
|---|----------|-------|---------|
| C1 | Slide 5 | 6 puzzle-specific goals | **4** (Scheme A: A>D) |
| C2 | Slide 6 | Gemma4 LOGO AUC = 0.806 | **0.809** (8 valid folds) |
| C3 | Slide 4 | Mix 0.38 and 0.43 for same claim | **Distinguish** goal-level (0.38) vs source-level (0.43) |
| C4 | Slide 8 | P16 includes L22; mlp_L26=44% | **No L22**; mlp_L26=**25%** |
| C5 | Slide 8 | P16 baseline = 55.6% | **62.5%** (1 NaN excluded) |
| C6 | Slide 8 | P14 gen_thinking_L10 = 40% | **44.4%** (valid-only) |
| C7 | Slide 9 | forced_own_cot | **forced_own_thinking** |
| C8 | Slide 9 | 13.97× from CoT experiment | **From Stage 4.7** |
| C9 | Slide 4 | Gemma4 n_goals_positive = 5 | **6** |
| C10 | All | sr_success used for interventions | **Use sr_api_binary** |

---

## 5. Data Still Missing (Cannot Be Filled Without New Experiments)

See `MISSING_DATA_FOR_PRESENTATION.md` for full list. Critical gaps:

1. **M1** — Text for Condition A failures (>51% of failures are metadata-only)
2. **M2** — Per-model breakdown of 0/160 causal candidates
3. **M3** — Goal identities for CoT causal role experiment
4. **M4** — Canonical refusal direction for both models
5. **M5** — CoT causal role results at sufficient scale (N=8 → need N≥50)
6. **M6** — P11/P14/P16 for Gemma4

---

## 6. Data Integrity Assessment

| Category | Assessment |
|----------|-----------|
| Total row counts | VERIFIED from raw JSONL |
| Factorial interaction (goal-level) | VERIFIED from analysis JSON |
| LOGO AUC values | VERIFIED from conservative_logo_auc.json |
| Best-layer AUC values | VERIFIED from subspace_stats summaries |
| Intervention ASRs (P11/P14/P16) | VERIFIED from sr_scored.jsonl files (using sr_api_binary) |
| CoT role ASRs | VERIFIED from cot_causal_role_sr_scored.jsonl |
| Failure mode counts | VERIFIED from mahmood_analysis outputs |
| Sprint table consistency | INCONSISTENT for P16 (corrected above) |
| CoT experiment attribution | INCONSISTENT (corrected: Stage 4.7 for 13.97×) |
| Condition naming | INCONSISTENT (corrected: forced_own_thinking not cot) |

---

## 7. Output File Index

All files are in: `outputs/meeting/full_presentation_exact_audit_jul01_2026/`

| File | Content |
|------|---------|
| `PRESENTATION_NUMBERS_MASTER.csv` | Every presentation number: value, numerator, denominator, status, source |
| `aggregate_model_condition_counts.csv` | Model×condition row counts, successes, ASR |
| `per_goal_factorial_counts.csv` | Per-goal counts for both models (22 rows) |
| `per_source_factorial_counts.csv` | Source-level factorial summary |
| `intervention_results_master.csv` | P11/P11-SEL/P14/P16/CoT results table |
| `representation_results_master.csv` | All direction variants with AUC and metadata |
| `seed_coverage_by_condition.csv` | Seed counts per source per condition |
| `failure_mode_master.csv` | Failure modes by model and condition |
| `SLIDE2_SCOPE_EXACT.md` | Slide 2 audit: before/after June 14, pipeline variants |
| `SLIDE3_BEHAVIORAL_EXACT.md` | Slide 3 audit: 220-per-model dataset, per-goal ASR |
| `SLIDE4_FACTORIAL_EXACT.md` | Slide 4 audit: factorial design, interaction formula and values |
| `SLIDE5_PUZZLE_SPECIFIC_EXACT.md` | Slide 5 audit: goal classification, Scheme A/B |
| `SLIDE6_REPRESENTATIONS_EXACT.md` | Slide 6 audit: LOGO AUC, best-layer AUC, 0/160 causal |
| `SLIDE7_REFUSAL_DIRECTION_AUDIT.md` | Slide 7 audit: direction methods, cosine matrix |
| `SLIDE8_INTERVENTIONS_EXACT.md` | Slide 8 audit: P11/P14/P16 with corrections |
| `SLIDE9_COT_ROLE_EXACT.md` | Slide 9 audit: CoT experiment, condition names, attribution |
| `SLIDE10_FAILURES_EXACT.md` | Slide 10 audit: failure modes, missing text |
| `SLIDE11_NEXT_STEPS_EXACT.md` | Slide 11 audit: priority order for next sprint |
| `CONTRADICTIONS_AND_CORRECTIONS.md` | All 12 contradictions with authoritative sources |
| `MISSING_DATA_FOR_PRESENTATION.md` | 10 data gaps that require new experiments |
| `PRESENTATION_SPEAKER_SCRIPT_EXACT.md` | Corrected speaker notes for all 11 slides |
| `FULL_PRESENTATION_EXACT_AUDIT.md` | This file — master audit document |
