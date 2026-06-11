# Current Project Status

**As of:** 2026-06-11

---

## Stage 4.7 and 4.8 — BOTH COMPLETE

All GPU jobs finished. Stage 4.8 projections replicate Stage 4.7 mechanistic null.
**Next: meeting with Mahmood — see MAHMOOD_NEXT_MEETING_BRIEF.md**

---

## Stage Completion Summary

| Stage | Status | Key outputs |
|-------|--------|-------------|
| Stage 2B | ✅ Complete | 42 attack examples, Qwen3-14B generations |
| Stage 3 | ✅ Complete | StrongREJECT scores for all 42 examples |
| Stage 4 (token dynamics) | ✅ Complete, frozen | Layer-0–39 projection for 42 examples; provisional Layer-22 direction |
| Stage 4A2 (causal validation) | ✅ Complete | 0/160 survivors — direction is diagnostic, not causal |
| Stage 4.5 (attention pilot) | ✅ Complete | Attention-head analysis artifacts |
| Stage 4.5B (LLM onset) | ❌ Blocked | Safety-filter truncation; code exists but no usable annotations |
| Stage 4.6 (controlled ablation) | ✅ Complete, audited | 20 corrected generations; 6 meeting figures; canonical CSVs |
| Stage 4.7 (multi-prompt replication) | ✅ Complete | 48 gens; 11 figures; mechanistic analysis; A<D on projection |
| Stage 4.8 (repeated stochastic gens) | ✅ Complete | 60/60 gens; Branch C (3 matched cells); projections replicate 4.7 null |
| Stage 5–8 | 🔜 Deferred | Not started |

---

## Stage 4.7 — COMPLETE

**Run dir:** `outputs/stage4_7/runs/run_array_20260610_1442/`  
**Canonical dataset:** `analysis/canonical_per_run_results.csv` — 48 rows, 3 outcome definitions

### All outputs complete
- ✅ 48 generations (job 530711)
- ✅ Corrective rerun merged (job 533260, partial — 5 rows still censored, genuine infinite loopers)
- ✅ Canonical dataset: 48 rows, 5 censored, integrity audit PASSED
- ✅ Behavioral analysis: contrasts, sign tests, bootstrap CIs, LOGO sensitivity
- ✅ Projection analysis: layers 13, 16, 22, 38, 39 (job 533255)
- ✅ Mechanistic contrasts: A<D on L22 (p=0.039); direction tracks thinking depth not success
- ✅ All 11 figures generated

### Key Results

| Contrast | Mean diff | p-value | Positive signs |
|---------|-----------|---------|---------------|
| A − D | +0.438 | 0.031 | 6/0/6 |
| A − F | +0.573 | 0.016 | 7/0/5 |
| D − F | +0.135 | 0.625 | 3/1/8 |
| A − E | +0.490 | 0.031 | 6/0/6 |

---

## Stage 4.8 Current State

**Design:** 4 source prompts × 3 conditions (A, D, F) × 5 seeds (101–105) = 60 stochastic generations  
**Manifest:** `outputs/stage4_8/repeated_generation_manifest.jsonl` — 60 rows, audit PASSED

### Completed (CPU)
- ✅ Source prompt selection: 4 prompts (1 per goal)
- ✅ 60-row manifest built and validated
- ✅ All scripts: audit, analyze, extract_direction, runner, SLURM (smoke + array)
- ✅ 33/33 CPU tests passing
- ✅ Bug fixed: `_user_message_text` field name in replication_prompts.jsonl

### Completed (GPU smoke)
- ✅ Job 534919: smoke PASSED — 6/6 eos_token, 3/3 cells diverse, sampling config verified

### Completed (GPU array)
- ✅ Job 534979: 60/60 rows, 0 censored, audit PASSED, 12/12 diverse cells
- ✅ Behavioral analysis: condition summary, cell summary, variance decomposition
- ✅ **Decision gate: Branch C** — 3 matched cells (< 4 threshold), direction extraction skipped

### Key Stage 4.8 results
| Condition | Success/N | Rate |
|-----------|-----------|------|
| A | 12/20 | 60% |
| D | 10/20 | 50% |
| F | 8/20 | 40% |

Goal identity dominates: goal 1 = 0% all conditions, goal 3 = 100% all conditions.
Between-cell variance 3.7× within-cell variance.

### Completed (GPU repr)
- ✅ Job 535094: 60 projection rows, all layers 13/16/22/38/39 done
- ✅ **Mechanistic replication:** A (7.12) < F (8.08) < D (8.95) on L22 — same as Stage 4.7
- ✅ 6 figures generated (figs 1–5, 9); figs 6–7 skipped (Branch C)
- ✅ STAGE4_8_REPEATED_GENERATIONS_RESULTS.md fully populated
- ✅ MAHMOOD_NEXT_MEETING_BRIEF.md updated with full story

### No running GPU jobs — all complete

---

## Key Numbers (Stage 4.7 confirmed)

| Metric | Value |
|--------|-------|
| A success (complete-case) | 10/11 (91%) |
| D success (complete-case) | 5/11 (45%) |
| F success (complete-case) | 3/11 (27%) |
| E success (complete-case) | 4/9 (44%) |
| A mean think tokens | 11,458 |
| D mean think tokens | 2,924 |
| F mean think tokens | 824 |
| A vs F think ratio | 13.9× (same length prompt) |
| Censored rows | 5 (all in D, E, F conditions) |
| LOGO stability | A>D: 4/4, A>F: 4/4 |

---

## Critical Path

### Available now for meeting
- fig3, fig2, fig7 — core behavioral story
- fig10 — censoring sensitivity
- All sign tests, LOGO analysis

### After job 533255 (projection)
- fig5, fig6, fig8, fig11 — mechanistic story

### After Stage 4.8 full run
- matched_outcome_cells.csv — determines feasibility of behavior-conditioned direction

---

## Blocked / Deferred

- **Stage 4.5B onset annotation:** Blocked indefinitely by Gemini safety filtering
- **RL:** Not planned
- **New attack generation / optimization:** Not planned
- **Multi-GPU model splitting:** Not supported; always use single L40S

---

## Important Constraints

- Do not modify frozen Stage 4 artifacts: `outputs/stage4/token_dynamics/full_20260604_101929/`
- Layer-22 direction is provisional (diagnostic only): `outputs/stage4/qwen3-14b/refusal_direction/direction.pt`
- All GPU jobs: L40S nodes `n-802,n-803,n-804,n-805`; single GPU; no multi-GPU splitting
- No causal claims until future intervention study
