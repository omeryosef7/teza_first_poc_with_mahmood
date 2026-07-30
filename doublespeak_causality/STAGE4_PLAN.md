# Stage 4 — Concept × Refusal TOCTOU Factorial: Build Plan

**Gate:** Stage 2/3 done. Goal: causally test the paper's TOCTOU hypothesis (refusal fires while the codeword is still benign; harmful semantics emerge later). Primary Llama-3.1-8B. Source: recon agent (2026-07-30), file:line verified.

**All primitives exist.** Stage 4 = a thin ~120-line orchestrator `45_toctou_factorial.py` composing them. Net-new: (1) a Llama refusal `.pt`; (2) lift one all-position ablation hook.

## (a) Refusal direction for Llama (minimal — no artifact exists, only gemma4/qwen3)
Diff-of-means (method from `poc_stage_gcg_early/compute_refusal_direction.py:162-164`, but run in the ds_common/Llama stack — its own loaders are qwen3/gemma4-only):
`v_refusal[L] = normalize(mean(h_harmful) − mean(h_harmless))` at last input-token position.
- Harmful set: the bench `behavioral[i]["direct"]` field (genuinely harmful instructions; pool across all 6 pairs for a **concept-agnostic** axis), or `outputs/stage_gcg_full/advbench_manifest_v1.jsonl` (split==train).
- Harmless set: the 20 benign items at `compute_refusal_direction.py:35-56` (import them). **Do NOT** use matched `neutral` prompts — direct↔neutral differ only by concept↔codeword, that's the *concept* axis, not refusal.
- Capture via `dc.forward_hidden_states(lm, dc.apply_template(...))[L+1][0,-1,:]`.
- Sweep L∈{12,14,16,18,20}; **validate** each by generation: project-out should RAISE compliance on held-out `direct`; add +α should INDUCE refusal on benign `neutral`. Pick largest sign-correct swing. Persist `outputs/stage_gcg_full/refusal_direction_llama_L{best}.pt`+`.json`.

## (b) Reusable primitives
- Concept install: `dc.LayerPatch(mode="add")` of `d_Direct[L+1]` at codeword_last across a timing window (generation-safe; add baked into prefill KV). `d_Direct` already built by `33_build_directions.py:105` (key `d_Direct|split|resid_post|codeword_last` in a `pair_directions_*/directions.npz`).
- Refusal ablate: **`make_project_out_hook`** from `poc_stage4/run_reasoning_intervention_experiments.py:175-191` — all-position/all-timestep projection (LayerPatch project_out only edits fixed prompt positions and skips decode steps, so it CANNOT ablate refusal from generated tokens — must use this hook). Model-agnostic, safe to lift.
- Generation + labeling: `patched_generate`, `classify`, `kw_refusal`, `layer_windows`, the `judge()` closure with the C8 EMPTY guard + judge-health gate — all from `18_run_behavioral_necessity.py` / `19_run_behavioral_sufficiency.py` (import via importlib idiom `19:42-51`). StrongReject via `poc_stage3/strongreject_scoring.py`.
- Semantic readout (5th state): `pc.semantic_score` → p_concept/p_codeword (was the concept installed regardless of refusal).
- Stats: `stats.paired_bootstrap_ci / permutation_test_paired / holm_bonferroni`; INT difference-of-differences pattern from `43_transplant_mediation.py:192-204`.

## (c) 2×2×timing cells (receiver = benign `neutral` items that are BENIGN at baseline)
CONCEPT∈{none, install d_Direct}; REFUSAL∈{none, ablate v_refusal (all positions)}; concept-timing∈{early,mid,late} (`layer_windows`). Refusal window = the single validated refusal layer (fixed).
- **A** none/none (1 gen, baseline BENIGN); **B** concept-only × timing (3); **C** refusal-only (1); **D** concept+refusal × timing (3). Combine LayerPatch(concept)+ablation-hook(refusal) in one ExitStack.
- Controls (plan §8): concept arm with `pc.norm_matched_random`/`orthogonal_random`; refusal arm with norm-matched random direction. Dose (α) sweep + norm-match to avoid additive-sufficiency overclaim.

## (d) 5 distinct outcome states (never fold together; C8 lesson)
`EMPTY` (empty gen), `MALICIOUS` (SR≥0.25), `REJECTED` (kw_refusal), `BENIGN` (else) via `judge()`; + `p_concept` (semantic interpretation) via semantic_score. So "concept read but refused" vs "concept read and complied" are distinguishable — the crux of TOCTOU.

## (e) Interaction test (H5 = TOCTOU)
Y=P(MALICIOUS) (secondary P(REJECTED), p_concept), paired on item:
```
concept_effect_noablate(t) = Y(B_t) − Y(A)
concept_effect_ablate(t)   = Y(D_t) − Y(C)
refusal_gain(t)            = concept_effect_ablate(t) − concept_effect_noablate(t)
INTERACTION = refusal_gain(early) − refusal_gain(late)   # H5
```
Per-item difference-of-differences → `ci_block(int_items, zeros)` paired-bootstrap CI vs 0; Holm across timings/outcomes. **H5 requires this CI to exclude 0** — do NOT infer TOCTOU from crossing B-vs-A curves. Guard tiny-n with `ci_reliable`.

## (f) Compute
Generation-dominated: ~12 greedy gens/item @200 tok ≈ 1 min/item on L40S. Pilot ~40 eligible bases ≈ 40-50 min + judging + one model load = 1 L40S job. Refusal-dir build+validation ≈ 15 min separate job. Order: unit-test composed hook → 1-item smoke → 40-item pilot.

## (g) Blockers
Only real gap = the Llama refusal `.pt` (build+validate per (a)). Refusal ablation MUST be all-position (`make_project_out_hook`, not LayerPatch). Harmless set must be genuinely benign (not `neutral`). `45_toctou_factorial.py` imports: `ds_common`, `pair_common`, 18's gen/label helpers via importlib, `stats`, lifted `make_project_out_hook`, `d_Direct` from directions.npz, `v_refusal` from the new .pt, StrongReject.
