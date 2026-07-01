# SLIDE 2 — Exact Scope Audit: What Changed Since the Last Meeting?

**Audit date:** 2026-07-01  
**Previous meeting cutoff:** June 13, 2026  
**Current sprint:** June 14–30, 2026

---

## Status-by-Date Table

| Metric | Status by June 13 | Added June 14–30 | Final Total | Authoritative Source |
|--------|-------------------|------------------|-------------|----------------------|
| Models analyzed | Qwen3-14B only | Gemma4-E4B-IT added | 2 models | SPRINT_SUMMARY_JUN14_30.md §2 |
| Harmful goals | 11 (all from HarmBench) | 0 new | 11 | factorial_attack_dataset.jsonl: 11 unique goal_index values |
| Puzzle variants per goal | 20 | 0 new | 20 per goal | SPRINT_SUMMARY_JUN14_30.md §2 |
| Source prompts (behavioral dataset) | 220 Qwen3 | 220 Gemma4 | 440 total | Stage 6 extractions; 220 unique source_example_ids per model |
| Condition A rows (factorial) | 292 Qwen3 | 232 Gemma4 | 524 total | factorial_attack_dataset.jsonl |
| Total factorial rows | 668 Qwen3 (A+D+E+F+G) | 448 Gemma4 | 1,116 | factorial_attack_dataset.jsonl |
| HVP variants | 3 (startofthink/endofthink/endofresponse) | 3 Gemma4 | 6 (3+3) | SPRINT_SUMMARY_JUN14_30.md §8 |
| DVP variants | 3 (startofthink/endofthink/endofresponse) | 3 Gemma4 | 6 (3+3) | SPRINT_SUMMARY_JUN14_30.md §8 |
| Behavioral variants | 1 (Qwen3) + subvariants | 1 Gemma4 | 2 models × (behavioral + startofthink + endofthink) | 20_direction_metadata.csv |
| Total pipeline variants | 12 HVP/DVP completed before Jun 14 | 2 Behavioral confirmed | 14 total (12 HVP/DVP + 2 Behavioral) | SPRINT_SUMMARY_JUN14_30.md §8 |
| Layers per model | Qwen3: 40 (L0–L39) | Gemma4: 42 (L0–L41) | 40 / 42 | Sprint §2 |
| Direction candidates tested (causal) | ? | 160 | 160 total | SPRINT_SUMMARY_JUN14_30.md §7 ("0 of 160") |
| Causal candidates passing | 0 | 0 | 0/160 | Stage 4A2; SPRINT_SUMMARY_JUN14_30.md §7 |
| P11 intervention rows | 0 | 110 | 110 | intervention_judge_validation/p11_sr_scored.jsonl |
| P11 selectivity rows | 0 | 75 | 75 | p11_selectivity_sr_scored.jsonl |
| P14 intervention rows | 0 | 70 | 70 | intervention_judge_validation/p14_sr_scored.jsonl |
| P16 ablation rows | 0 | 117 | 117 | intervention_judge_validation/p16_sr_scored.jsonl |
| CoT causal-role rows | 0 | 32 | 32 | intervention_judge_validation/cot_causal_role_sr_scored.jsonl |
| LOGO probe folds (Qwen3) | 0 | 11 | 11/11 valid | factorial_analysis/logo_fold_details.csv |
| LOGO probe folds (Gemma4) | 0 | 11 | 8/11 valid (goals 1,2,10 excluded) | factorial_analysis/conservative_logo_auc.json |
| Direction cosine comparisons | 0 | 72 pairs | 72 pairs (9 variants × 8 pairs per model × 2 models) | 19_direction_cosine_matrix.csv |
| StrongREJECT-scored intervention rows | 0 | 332 | 332 (110+75+70+77) | intervention_judge_validation/*.jsonl |
| Manual review packet failures | 0 | 45 | 45 | 15_manual_failure_review_packet.csv (46 rows including header) |

---

## Claims to Verify

### VERIFIED: 2 models
Qwen3-14B and Gemma4-E4B-IT. Both confirmed in factorial_attack_dataset.jsonl field `model_family`.

### VERIFIED: 11 goals
Goals 0–10, all present in factorial dataset. Source: `goal_map_for_sr.jsonl`.

### VERIFIED: 20 puzzle variants per goal
220 / 11 = 20. Confirmed in SPRINT_SUMMARY_JUN14_30.md §2 and stage 6 run design.

### VERIFIED: 220 puzzle examples per model (behavioral dataset)
The 220-per-model behavioral dataset (Slide 3) is from Stage 6 trace extraction runs, SEPARATE from the factorial dataset. These are the 220 unique source prompts (11 goals × 20 variants each), one generation per prompt.

**NOTE:** The factorial dataset Condition A has MORE rows: 292 (Qwen3) and 232 (Gemma4) because multiple seeds were run per source prompt. The "220 per model" refers only to the behavioral/representational dataset.

### VERIFIED: 440 total puzzle examples
220 Qwen3 + 220 Gemma4 = 440. Both from Stage 6 extractions.

### VERIFIED: 12 HVP/DVP variants (+ 2 Behavioral = 14 total)
- HVP × 3 positions × 2 models = 6 HVP variants
- DVP × 3 positions × 2 models = 6 DVP variants
- Behavioral × 2 models = 2 Behavioral variants
- Total: 14 pipeline variants
Sprint summary says "12 HVP/DVP + 2 Behavioral = 14 total" (SPRINT_SUMMARY_JUN14_30.md §8 and line 409).

### VERIFIED: 2 Behavioral variants
One per model (Qwen3 and Gemma4). 

### NOT VERIFIED FROM RAW DATA: 2,640 per-example JSON files
The sprint mentions "per_example/example_XXXXX.json" files in token_dynamics_subspace directories. A `find` command returned 0 results for `example_*.json` in the stage4 qwen3-14b and gemma4-e4b-it subdirectories. These files may exist under different naming or in non-indexed locations.
Source: SPRINT_SUMMARY_JUN14_30.md §4B mentions "220 examples × 12 variants = 2,640 files". This would require: 220 examples/model × (6 HVP + 6 DVP) / model + behavioral = more complex calculation. The 2,640 number is NOT independently verified from filesystem artifacts.

### VERIFIED: 0/160 causal candidates passing
Stage 4A2 found 0 of 160 direction candidates passing both KL divergence and causal steering thresholds. Source: SPRINT_SUMMARY_JUN14_30.md lines 289 and 462.
**DENOMINATOR NOTE:** The exact composition of the "160" is not explicitly decomposed in documentation. Likely: 2 models × 8 HVP/DVP direction variants × some number of layers or subspace ranks per variant. Cannot be exactly reconstructed without access to the Stage 4A2 candidate scoring checkpoint files (poc_stage4/intervention_selection.py outputs).

### NOT VERIFIED: 0 corrupted files
No corrupted-file audit was found in accessible artifacts.

---

## WHAT WAS ACTUALLY NEW THIS SPRINT (June 14–30)

1. **Gemma4-E4B-IT added** — full Stage 6 extraction (220 examples, EOS bug fix, clean rerun)
2. **Factorial G and E conditions completed** — enabling the full (A-E)-(D-G) interaction test for both models (G condition was missing before June 14)
3. **LOGO probe analysis** — goal-clustered AUC for both models
4. **Confound baseline probes** — goal_only and thinking_length controls
5. **P11 prefill patching** — 110 rows, SR-validated
6. **P11 selectivity pilot** — 75 rows, generic-disruption caveat established
7. **P14 generation-phase patching** — 70 rows, SR-validated
8. **P16 block ablation** — 117 rows, SR-validated
9. **CoT causal-role experiment** — 32 rows, SR-validated
10. **Direction cosine matrix** — 19_direction_cosine_matrix.csv (all similarities < 0.26)
11. **Meeting analysis package** — 42 structured audit files in mahmood_analysis_only_jun30_20260630_193423/
12. **Manual failure review packet** — 45 examples (15_manual_failure_review_packet.csv)

**Work completed BEFORE June 14 (should NOT be presented as new):**
- Qwen3 HVP/DVP/Behavioral direction extraction (all 3 positions)
- Stage 4.6 controlled ablation (5 conditions, Qwen3 only, 20 rows)
- Stage 4.7 multi-prompt replication (48 rows, 4 conditions)
- Stage 4.8 stochastic replication base (60 rows, 4 goals × 3 conditions × 5 seeds)
- Stage 4A2 causal validation (0/160 negative result)
- Qwen3 220-example behavioral evaluation (51.4% ASR)

---

## Notes on Model Identifiers

From `factorial_attack_dataset.jsonl` field `model_family`: `"qwen3"` and `"gemma4"`.  
From `20_direction_metadata.csv`: `"qwen3-14b"` and `"gemma4-e4b-it"`.  
Full model paths from manifests: `Qwen/Qwen3-14B` and `google/gemma-4-4b-it` (or similar).
