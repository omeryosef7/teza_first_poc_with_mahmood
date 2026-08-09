# Next Sprint — Execution Log (started 2026-08-09)

Append-only log for the sprint defined in `docs/NEXT_SPRINT_PLAN_2026_08_09.md`.
Plan goals (Q1–Q7): full fair GCG arm matrix (more seeds/steps), Jacobian-vs-projection
objective, any-refusal-beats-random, concept-term effect, mechanistic-validity check,
third architecture family (Phi-4-mini-reasoning), quantization extension.

Working rules in force: ≤6 concurrent L40S jobs, killable/gpu-research, nodelist
n-801..805,t-806, no SLURM deps, offline HF cache, bf16 primary, ClearHarm locked split,
train-only selection, ≥20 unique/cell, keep all nulls, commit (no push per plan — but user
explicitly asked to push for tracking → PUSH ALLOWED this sprint), TROPT-first, subagents
never read harmful text.

---

## 2026-08-09 — Phase 0: Audit

### Repo state at start
- Branch `behavioral-causality-sprint`, HEAD `67348347` (prior sprint 28/28 complete).
- No SLURM jobs running (clean slate).
- All 4 target models cached: Llama-3.1-8B-Instruct, Qwen3-14B, Phi-4-mini-reasoning,
  DeepSeek-R1-Distill-Llama-8B.
- GCG infra: `poc_stage_gcg_early/` (project root). TROPT: `TROPT/` (project root).
- Locked split: `data/splits/clearharm_doublespeak_v1.json` (n_train=44, n_test=42, n_total=86,
  sha256 ac95d864…) and a v3 split `clearharm_doublespeak_v3.json` (N=324 confirmatory, leakage 0).
- GCG manifests present: `data/gcg/clearharm_llama/{direct,doublespeak}.jsonl` (86 rows each,
  44 train / 42 test), plus `..._doublespeak_firstcut20.jsonl` (the 20-item first-cut train).
- 16-arm matrix spec frozen: `configs/manifests/phase9_gcg_mac_matrix.json` (status: NOT LAUNCHED).
  Shared hp: suffix_len=16, n_steps=200, bs=64, topk=256, no-filter-cand, suffix-placement=user,
  universal suffix, seeds [42,43,44], selection weighted, repr_in_selection auto-on for mechanism arms.

### Current scientific state (from SPRINT_SUMMARY_2026-08-02_TO_08-09.md — treated as starting point)
- representation ≠ behavior thesis established on Llama-3.1-8B.
- Concept circuit fully mapped; epiphenomenal BY SPECIFICITY (powered n=324 write+carry ΔASR
  +0.046 ns < random +0.161).
- Refusal suppression = behavioral lever (ablate stronger than DS; re-inject kills DS; decision-token
  localization L15-18; Gate B PASS forward; mediation ≈1.0; predicts AUC 0.874; Jacobian AUC 0.807).
- Gate-7 GCG objective: NEGATIVE/non-specific first-cut (refusal 0.465 ≈ random 0.464, 2 seeds,
  50 steps, 20-item train). 16-arm matrix designed, NEVER RUN.
- Cross-model: Qwen3-14B (thinking-off) reproduces dissociation. Quant bf16/8/4-bit robust for
  refusal ablation.

### Audit subagents launched (read-only, safe files only)
1. GCG/TROPT optimization infrastructure (poc_stage_gcg_early runners, refusal-dir loss wiring).
2. Jacobian (P6) math + differentiable-loss feasibility.
3. Gate-7 first-cut reconstruction + 16-arm reconciliation.

(Results appended below as they return.)
