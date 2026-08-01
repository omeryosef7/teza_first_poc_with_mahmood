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

---

## NEXT5 addendum (2026-07-31) — max-depth sprint (see `NEXT5_PLAN.md` / `NEXT5_FINDINGS.md`)
All new inferential claims survive a single Holm family (`outputs/next5_holm_family.json`): W1
p_holm 0.014, W3b 0.002/0.007. Full test suite 93 passed (was 52).
- **W1 [WIN]:** per-pair-timing behavioral TOCTOU — pooled mid−late interaction +0.1375
  [+0.0375,+0.2375] n=80 p=0.015 (grenade+chlorine at their own MID depth, pre-registered from T3).
  Turns the #6 negative into a confirmation. New `INTERACTION_mid_late` in `45`; `next5_w1_pooled_toctou.py`.
- **W3-b [WIN]:** superposition supported — DS rep carries codeword + DS-specific concept component
  (DS−benign +0.55, DS−unrelated +0.46). Both §3.4 mechanisms now tested. `next5_w3b_superposition.py`.
- **W4 [NEW]:** per-head z-AtP (validated pearson 0.97) localizes to a MID band (L7–14, peak L9),
  distributed across heads; per-layer knockout = no single-layer bottleneck. New primitives
  `ZHeadPatch`/`ZHeadCapture` (`pair_common`), `49_head_attribution.py`, `next5_w4_knockout_reduce.py`.
- **W2 [scope bound]:** DeepSeek post-`</think>` readout validated (0/120 truncation) but DS hijack
  weak (n=6, CI incl 0) → transplant not run; primary claim stays on Llama+Qwen3.
  `ds_next5_deepseek_readout.slurm`; fixed 31's misleading per-cell EXCLUDED message.
- **W5 [NEGATIVE]:** mechanism-derived defense (`AllPositionAdd`) does not work — no baseline attack
  headroom (DS malicious 0.033) + additive all-position steering destabilizes generation.
  `next5_w5_defense_eval.py`.
- New tests: `test_alladd_hook_synthetic.py` (9), `test_zhead_synthetic.py` (6, incl. AtP-exactness).

---

## NEXT6 addendum (2026-07-31) — "all new directions" (see `NEXT6_PLAN.md` / `NEXT6_FINDINGS.md`)
All new positive claims survive one Holm family (`outputs/next6_holm_family.json`). Full suite still green.
- **D6 [WIN]:** unified depth timeline (TOCTOU = 22.5x concept gradient). `next6_d6_depth_story.py`.
- **D3 [WIN]:** mid-band head circuit (L7-14) replicates on grenade/chlorine (pearson .97-.99).
- **D4 [sharpening]:** NOT a sparse head circuit -- DIRECT~0 for every mid-band head, head->head
  edges don't reconstruct TOTAL -> MLP/distributed. New `50_path_patching.py` + `ZHeadPatchMulti`/
  `FreezeAllHeadsExcept`/`FreezeMLP` (linear-toy test 4/4).
- **D2 [nuanced]:** superposition bomb-specific but cross-arch (Qwen3 +8.96); other pairs NS.
- **D1 [integrity]:** grenade confirms n=60 (p=.008); chlorine NULL (committed n=40 +0.15 not robust);
  pooled grenade-driven (+.108, p=.012). W1 tempered.
- **D5 [negative]:** Phi-4 hijack absent; both reasoning models don't carry it to the answer.
- **D7 [negative]:** late/use-depth defense fails w/ headroom (compliance gated early).
- **Bug caught+fixed:** reps<->directions suffix collision (chlorine/pistol used grenade d_Direct);
  all affected runs redone with verified dirs.
- New tests: `test_path_patching.py` (4). New code: `50_path_patching.py`, `next6_d7_defense_redo.py`,
  `next6_d6_depth_story.py`, `next6_w4_knockout_reduce.py`, `next6_holm_family` computation.

---

## NEXT7 addendum (2026-08-01) — see `NEXT7_PLAN.md` / `NEXT7_FINDINGS.md`
Holm family (`outputs/next7_holm_family.json`): cocaine/pistol behavioral TOCTOU p_holm 0.001.
- **Full circuit [WIN]:** distributed mid-band attention(L7-9)→MLP(L9-14) cascade, late=passive
  carry; validated by AtP + forward-only true-patch sweep. New: `51_mlp_attribution.py`,
  `next7_layer_patch_sweep.py`, `next7_layer_patch_sweep` primitives, `--enable-thinking`/`--demo-cap`
  on 49/51.
- **TOCTOU [capstone]:** 5/5 representational depth-gating (T3 cocaine EARLY, pistol MID), 4/5
  behavioral at own depth (cocaine +0.333, pistol +0.467, both Holm-sig; only chlorine null).
- **N7-B:** reasoning doesn't resolve the codeword (anchored CoT probe; refines D5).
- **N7-G:** hijack saturates at <=4 demos.
- **Defense/detection:** intervention fails (D7/N7-F, distinct principled reasons); detection perfect
  in-domain (AUC 1.0, Llama+Qwen3) but partial cross-pair transfer.
- **Infra:** solved Qwen3 AtP OOM via forward-only sweep; Phi-4/Qwen3 metric limitations documented.
