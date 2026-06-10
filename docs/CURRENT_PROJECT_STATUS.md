# Current Project Status

**As of:** 2026-06-10

---

## Active Stage: 4.7 — Multi-Prompt Controlled Replication

**Stage 4.6** (controlled ablation) is complete and audited. **Stage 4.7** prompt construction is complete; GPU generation is the next step.

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
| Stage 4.7 (multi-prompt replication) | 🔄 In progress | Prompts built (48 rows); GPU runs pending |
| Stage 5–8 | 🔜 Deferred | Not started |

---

## Stage 4.7 Current State

**Prompt build:** `outputs/stage4_7/replication_prompts.jsonl` — 48 rows (12 prompts × 4 conditions)
**Audit:** `outputs/stage4_7/replication_prompt_audit.json` — all invariants passing
**Source selection:** `outputs/stage4_7/source_prompt_selection.csv` — 12 prompts (3 per goal, length-tertile stratified)
**GPU generation:** Not yet submitted (SLURM scripts ready)

### Pending GPU work

1. Submit smoke test: `slurm_scripts/stage4_7_replication_smoke.slurm`
2. Submit full array (after smoke passes): `slurm_scripts/stage4_7_replication_array.slurm`
3. Run projection analysis: `poc_stage4_7/compute_selected_layer_dynamics.py`
4. Run behavioral + mechanistic analysis: `poc_stage4_7/analyze_replication.py`
5. Generate 9 meeting figures: `poc_stage4_7/plot_replication.py`

---

## Key Numbers (confirmed)

| Metric | Value | Source |
|--------|-------|--------|
| Stage 4.6 Condition A success | 4/4 (100%) | `canonical_per_run_results.csv` |
| Stage 4.6 Condition D success | 4/4 (100%) | `canonical_per_run_results.csv` |
| Stage 4.6 Condition E success | 2/4 (50%) | `canonical_per_run_results.csv` |
| A vs D think-token ratio (means) | 3.47× | `condition_summary_corrected.csv` |
| A mean think tokens | 12,129 | `condition_summary_corrected.csv` |
| D mean think tokens | 3,491 | `condition_summary_corrected.csv` |
| Stage 4.7 total planned generations | 48 | `replication_prompts.jsonl` |
| Stage 4.5B usable annotations | 0 / 20 attempted | `raw_passes.jsonl` |

---

## Critical Path to Next Meeting

1. ✅ Stage 4.6 audit and meeting figures
2. ✅ Stage 4.7 prompt build (CPU work)
3. 🔄 Stage 4.7 GPU generation (48 runs × ~25 min each on L40S)
4. 🔄 Stage 4.7 projection analysis (GPU, after generation)
5. 🔄 Stage 4.7 behavioral + mechanistic analysis + plots
6. 🔄 Populate `docs/STAGE4_7_REPLICATION_RESULTS.md`

---

## Blocked / Deferred

- **Stage 4.5B onset annotation:** Blocked indefinitely by Gemini safety filtering. Do not retry in this sprint.
- **RL:** Not planned.
- **New attack generation / optimization:** Not planned.
- **Multi-GPU model splitting:** Not supported; always use single L40S.

---

## Important Constraints

- Do not modify frozen Stage 4 artifacts: `outputs/stage4/token_dynamics/full_20260604_101929/`
- Layer-22 direction is provisional (diagnostic only): `outputs/stage4/qwen3-14b/refusal_direction/direction.pt`
- Maximum 60 new Qwen3-14B generations total in Stage 4.7 (currently 48 planned)
- All GPU jobs: L40S nodes `n-802,n-803,n-804,n-805`; single GPU; no multi-GPU splitting
