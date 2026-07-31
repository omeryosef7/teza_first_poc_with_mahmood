# NEXT_CAUSAL_SPRINT — Handoff

**Model:** Llama-3.1-8B-Instruct · **Pair:** CARROT↔BOMB · **Branch:** behavioral-causality-sprint
**Plan:** `NEXT_CAUSAL_SPRINT_PLAN.md` · **Progress log:** `NEXT_CAUSAL_SPRINT_PROGRESS.md` · **Paper draft:** `PAPER_CONTRIBUTION.md`

## What was delivered (all committed, artifact-backed)

### Three NEW causal contributions
1. **S2 — the reading is context-carried, not locally stored** (`STAGE2_TRANSPLANT_FINDINGS.md`). State×receiver-context transplant: Neutral receiver reads 0.000 for *every* source state (h_N/h_DS/h_Direct); DS receiver reads ~0.35 for *every* source state. `IE_state ≈ 0` (equiv); `DE_context +0.347` [+0.261,+0.434] ≈ 99% of TE; self-transplant faithfulness exactly 0.0. → the causal counterpart of the paper's decoding-only evidence.
2. **S3 — not a trivial demo re-read; distributed** (`STAGE3_KV_FINDINGS.md`). Demo-K/V mediation: neutralizing the demonstration K/V removes only ~9% (`ReRead_test` +0.032 of 0.35 → 91% survives); effect distributed (outcome C).
3. **S4 — causal TOCTOU: the refusal check is depth-gated** (`STAGE4_TOCTOU_FINDINGS.md`). Concept×refusal factorial (n=40): early concept install → refusal 0.82 (concept-specific: random/orth 0.00) → ablate refusal → comply 0.53; late concept escapes (0.07). INTERACTION +0.425 [+0.25,+0.60] Holm-sig.

### Load-bearing NEGATIVE / integrity
- **B4** — CAUSAL_CORE's `d_Direct` install +0.971 does NOT reproduce (+0.03 on the reproducible pipeline; on-disk artifact 693571=+0.028); no regression; doc-vs-artifact drift. Strengthens S2 (no local intervention installs, only context).
- **S0** — 10 integrity defects (C1–C10) fixed + tests + independent review (`STAGE0_INTEGRITY_REPORT.md`); no conclusion-inverting bug.

## Key methodological notes (read before re-running)
- **Use `--readout forced_choice`, NOT cloze** — cloze floors the DIRECT positive control (0.005 vs 0.785); DS signal stable ~0.3 (B3).
- **Consistent (bench, reps, dir) triple required** — never mix reps/dirs from different builds (B1). The bench `pair_carrot_bomb.json` is the committed Jul-29 gpt-4o-mini build (generated_at 2026-07-29T21:44).
- **Refusal ablation must be multi-layer** (`AllPositionProjectOutMultiLayer`, Arditi) — single-layer barely ablates (1.0→0.93); all-layer at L18 gives 1.0→0.53.
- **Patchscope readout is unusable as configured** (late-layer read, no positive control) — dropped.

## New code (reuse-first; all tested + reviewed)
`43_transplant_mediation.py`, `44_kv_mediation.py`, `45_toctou_factorial.py`, `build_refusal_direction_llama.py`; `pair_common.DemoStateSwap` + `AllPositionProjectOut(MultiLayer)`; `ds_common.patch_layer_sweep`; specs added to `34_intervention_sweep.py::run_replace`. Tests: `tests/test_integrity_fixes.py`, `test_transplant_mediation.py`, `test_kv_mediation.py`, `test_projectout_hook_synthetic.py`, `test_toctou_analysis.py`, `test_demostateswap_synthetic.py` (all green). SLURM: `ds_transplant_mediation`, `ds_rebuild_transplant`, `ds_kv_mediation`, `ds_additive_control`, `ds_stage4_toctou` (L40S nodes n-801..805,t-806; env poc_stage2).

## Deferred (documented, off critical path)
- **S1 SHUFFLED_OR_INCONSISTENT_MAPPING** condition — not required for the primary causal claims (S2/S3/S4 use NEUTRAL/DS/DIRECT). Add via `30_build_pair_benchmark.py` if an inconsistent-mapping control is wanted.
- **S5 generalization** (≥3 pairs, +1 arch) — the strongest next step to lift S2/S3/S4 from single-pair to a property of Doublespeak. Reuse the same scripts with other `data/pair_benchmark/pair_carrot_*.json`.
- **S6 optimization** — gated on a causal variable predicting held-out behavioral ASR (prior scores anti-predicted); not pursued.
- **S4 control-D cells** — add random/orthogonal cell-D to fully close compliance-flip specificity.

## Suggested next actions (priority)
1. **S5 generalization** of the S2 transplant dissociation + S4 TOCTOU to grenade/pistol/chlorine/cocaine pairs (forced_choice, consistent triples) — turns single-pair results into general claims.
2. Add **control-D cells** to the TOCTOU factorial (cheap, closes a caveat).
3. Larger n / second seed for tighter CIs; a positive-control-gated patchscope readout.

## Open flags for Omer
- **B4**: CAUSAL_CORE's +0.971 `d_Direct` claim is unbacked on disk — decide whether to retract/relabel it in the older docs.
- **C10** label de-bias was signed off (kept); it affects discrete labels only, not `p_concept`.

---

## NEXT2 addendum (2026-07-31)
Low-hanging follow-ups (see `NEXT2_FINDINGS.md`, `NEXT2_PLAN.md`):
- **Strengthened:** representational dissociation is **depth-invariant** (N1: local state inert at all 32 layers; N2: 11-layer-window replacement also inert; 4/4 pairs). Depth-overlay (#1) unifies S2/S3/S4: meaning is context-supplied at every depth, refusal check acts only early.
- **Closed caveat:** TOCTOU **compliance-flip is concept-specific** (#2 cell-D: Dspec early +0.475) — both halves now controlled.
- **Honest negatives:** Qwen3 cross-arch (thinking-model readout gate fails); patchscope (N3, positive control fails for bomb — unusable); d_Direct dose (N4, small/non-monotone); TOCTOU does **not** clearly generalize beyond bomb (#6: grenade null, chlorine NS) — the representational dissociation does (4/4), the behavioral TOCTOU does not.

### Remaining deferred (future sessions)
- **Thinking-aware readout** (`enable_thinking=False` / post-`</think>` answer-position) to test cross-architecture (Qwen3, DeepSeek-R1-Distill; both cached) — the main way to lift the primary claim off single-model Llama.
- **Pair-tuned patchscope** inspection prompt that passes the bomb positive control → then cross-check IE_state=0 via the paper's own readout.
- **#4 attribution-patching map** (`47_attribution_patching.py`) to localize the distributed DE_context (deferred: gradient-approx correctness risk).
- **All-32-layer cumulative replacement** (near-certain confirmatory given N1+N2).
- A **stronger/pair-robust concept-install lever** to test TOCTOU generality behaviorally.

---

## NEXT3 addendum (2026-07-31) — executed the 4 deferred levers
See `NEXT3_PLAN.md` / `NEXT3_FINDINGS.md`.
- **T1 cross-architecture ✅ (major):** the context-carried dissociation **replicates on Qwen3-14B** (IE_state≈0 equiv; DE_context +0.70 ≈92% of TE; faithfulness 0.0; hijack stronger than Llama) via a thinking-aware readout (`--enable-thinking false`, threaded through 31/32/34/44 + a `--model`-to-34 slurm fix). The primary claim is now on **2 architectures**. DeepSeek-R1 deferred (hardcoded `<think>` → needs `31 --answer-marker '</think>'`).
- **T4 attribution patching ✅ (validated new technique, `48_attribution_patching.py`):** AtP≈true-patching (pearson 0.89); localizes the DS-context effect to the **earliest layers + demonstration-codeword positions**. Refines S3's "distributed."
- **T3 representational TOCTOU ◐ (`47_repr_toctou.py`):** refusal-direction projection is depth-gated concept-specifically for all 3 pairs but at a **pair-dependent depth** (bomb early, grenade/chlorine mid) — explains the behavioral #6 non-generalization.
- **T2 forced-choice patchscope ✗ (`46_forced_choice_patchscope.py`):** positive control fails for bomb → cannot cross-check via patchscope; consistent with IE_state=0 (concept not locally in the rep).

### Remaining deferred (future)
- DeepSeek-R1 (and other thinking models) via a post-`</think>` answer-position readout; more architectures.
- A behavioral TOCTOU per pair using that pair's OWN dominant depth (T3 predicts it should recover the interaction).
- A pair-tuned / non-safety-suppressed patchscope to positively replicate the paper's decoding.
- New code: `46/47/48_*.py` + `ds_run.slurm` (generic GPU runner); `--enable-thinking` threaded through 31/32/34/44.
