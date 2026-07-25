# Plan Execution Summary — everything we did, mapped phase-by-phase to the plan, with results

One-stop map from `docs/RESEARCH_PLAN_DISTILLING_JAILBREAKS.md` (the plan) → what was executed → the result →
where it lives. Companion docs: `docs/DISTILLATION_FINDINGS_SYNTHESIS.md` (findings synthesis),
`docs/CROSS_MODEL_MECHANISTIC_REPORT.md` (paper-ready write-up), `docs/RESEARCH_PLAN_PROGRESS_LOG.md`
(full chronological trace), `results/EXPERIMENT_REGISTRY.csv` (30 rows, one per experiment).

## Headline result (one sentence)
Across **4 model architectures / 2 backbone families**, an **external harmful dataset**, and the
**optimization side**, CoT-Hijacking's predictive internal "success" signals are **detector-grade but NOT
causally manipulable** — whether or not they are length-confounded — and the detector is **dataset-specific**.
i.e. **predictive-but-not-causal**, cross-validated far beyond a single model.

## Phase-by-phase status

| Plan phase (§) | What we did | Result | Where |
|---|---|---|---|
| **Phase 0 — Freeze state** (§4) | Froze current baselines, judge, splits | DONE | `docs/CURRENT_STATE_AUDIT.md` |
| **Phase 1 — Dataset split** (§5) | Disjoint dev-25 / held-out-495 (0 overlap) | DONE | `data/manifests/{dev_25,heldout_495,scale_heldout_25}.csv` |
| **Phase 2 — Eval protocol** (§6) | Frozen StrongREJECT (any-stream ≥0.5), grouped-LOGO | DONE | `slurm_scripts/run_strongreject_cpu.slurm` |
| **Phase 3 — TROPT baselines** (§7) | Reproduced GCG / MAC prefix-CE | GCG greedy ASR **0.450**, MAC **0.150**; prefix-loss ≠ behavior | `docs/TROPT_BASELINE_REPORT.md`; registry `phase3_tropt_*` |
| **Phase 4 — Real attack** (§8) | CoT-Hijacking on reasoning models | gpt-o4-mini dev-25 **0.917**; Qwen3-14B white-box **0.818** | registry `phase4_cot_*`, `phase5_qwen3_cot_dev25` |
| **Phase 5 — Mechanistic dataset** (§9) | Extracted C(fail)/D(success) residual streams | DONE (positions × layers per row) | `outputs/phase5_mechanistic/extraction/`; `docs/MECHANISTIC_DATASET_CARD.md` |
| **Phase 6 — Predictive signal** (§10) | Grouped-LOGO Fisher AUC + length confound | signal **AUC ≈ 0.90** pre-answer; **length-confounded** (gain-over-length CI ∋ 0) | `docs/PREDICTIVE_SIGNAL_REPORT.md`; registry `phase6_CvsD_signal_qwen3` |
| **Phase 7 — Causal validation** (§11) | Activation-addition steering (sufficiency + necessity + layer + timing sweeps) | **NULL** — neither sufficient nor necessary; coherence intact → detector/correlate, **not causal** | `docs/CAUSAL_VALIDATION_REPORT.md`; registry `phase7_*` |
| **Phase 8 — Candidate objectives** (§12) | Gate-3 = No → tested ALTERNATIVE signals (attention §C1, cross-model §C2) instead of the success-dir objective | alternatives also NULL (see Appendix C) | synthesis Appendix C |
| **Phase 9 — Soft optimization** (§13) | Soft-prompt optimizer maximizing the success-dir projection (Gate-4 upper-bound test) | **Gate 4 = No** — projection driven 14→470 but ASR does not causally rise (apparent "positive" audited to denominator-inflation + judge false-positive + noise) | `outputs/phase9_softopt/pfl_L16/asr_vs_arm.csv`; registry `phase9_softopt_gate4_qwen3` |
| **Phase 10 — Discrete MAC** (§14) | NOT entered — §25 Gate-4 = No ("do not spend large discrete compute") | gated off (consistent with causal null) | — |
| **Phase 11 — RL/reward** (§15-plan) | NOT entered (gated behind Gate 4 = Yes) | gated off | — |
| **Phase 12 — Universal** (§16-plan) | NOT entered (gated) | gated off | — |
| **Phase 13 — GCG suffix analysis** (§17) | 336-suffix taxonomy + transfer matrix (prior sprint) | DONE — cot_prefix_ce best objective; no seed overfit | `docs/DATASET_ANALYSIS_REPORT.md`; `results/{SUFFIX_TAXONOMY,CATEGORY_TRANSFER_MATRIX}.csv` |
| **Phase 14 — Held-out eval** (§18) | De-confounding replication on held-out n=48 | length confound **REPLICATES**; detector transfers weakly (0.90→0.78) | registry `phase7scale_confound_heldout48` |
| **Phase 15 — External transfer** (§19) | CoT-Hijacking + advbench-fit detector on malicious_instruct (external, non-advbench) | **attack transfers** (ASR **0.737**) but **detector does NOT** (transfer AUC **0.461 = chance**) → signal is DATASET-SPECIFIC | `outputs/phase_external/`; registry `external_transfer_maliciousinstruct` |
| **Phase 16 — Cross-model** (§20) | Full mechanistic pipeline on 4 models | **all predictive-not-causal** (matrix below) | synthesis §16-A–D; `outputs/phase16_deepseek_cot_heldout25/`, `outputs/phase_phi4_cot/`, `outputs/phase_deepseek_llama_cot/` |
| **Phase 17 — Defensive detector** (§21) | Success-vs-failure detector (the Gate-3 "No" branch) | **AUC 0.92** pre-generation; strong on CoT attacks | `docs/ADAPTIVE_DETECTION_AND_DEFENSE_REPORT.md`; registry `phase17_detector_CvsD_qwen3` |
| **Phase 4X — Cross-model benchmark** (§31, amendment) | Behavioral CoT-Hijacking on open-source targets | DeepSeek-Llama-8B **0.957**, Phi-4-mini **0.773**, gemma-3-4b **1.000** | `docs/CROSS_MODEL_COT_BENCHMARK_REPORT.md`; `outputs/phase4_hf_local/` |

## The cross-model matrix (Phase 16, the central deliverable)

| model (architecture) | signal AUC | confound (gain-over-length) | causal (steer) |
|---|---|---|---|
| **Qwen3-14B** | ~0.90 | CI ∋ 0 → confounded | **NULL** |
| **DeepSeek-R1-Distill-Qwen-7B** | 0.80–0.84 | beats length **but = label artifact** (same tokenizer as Qwen3) | **NULL** |
| **Phi-4-mini-reasoning** (Phi3) | 0.89–0.96 | prefill_last ∋ 0; think_content_1 marginal (+0.098) | **NULL** |
| **DeepSeek-R1-Distill-Llama-8B** (Llama) | 0.87–0.95 | **genuinely beats prompt-length** (+0.09–0.13, CI ∌ 0) | **NULL** (audited — apparent effect was a generation-length / think-termination artifact) |

Two models length-confounded (Qwen3, Phi-4); DeepSeek-Qwen's exception is a labeling effect; Llama-8B has a
*genuine* length-independent predictive signal yet is STILL non-causal → the causal null is robust even to the
length-confound question itself.

## Appendix C — Claude-proposed extensions (user-authorized)
- **§C1** attention-concentration causal intervention (Qwen3) — **NULL** (uniform attention-temperature not a
  causal lever; τ=2.0 "drop" was repetition degeneracy). `outputs/phase8_attn_causal/`.
- **§C2** cross-model causal test on DeepSeek — **NULL** (Qwen3 null replicates). `outputs/phase16_deepseek_cot_heldout25/steer_*`.
- **§C3** length identifiability — success/failure attack-prompt lengths near-disjoint (AUC(len→success)=0.827,
  ≤9 matchable pairs) → the length confound is IRREDUCIBLE by matching. `outputs/phase5_mechanistic/phase6_length_identifiability.json`.

## §25 Decision-tree outcome & §29 Minimum Publishable Outcome
- **Gate 1** (attack works?) = **Yes** (0.917/0.818). **Gate 2** (predictive signal?) = **Yes** (AUC 0.90).
  **Gate 3** (causal?) = **No** → routed to detector-only + test-alternatives (C1/C2, also null) + multivariate
  (MLP detector, length-confounded). **Gates 4–6** gated off (Gate 3 = No); Gate 4 soft-opt also = No.
- **MPO (§29):** items 1–4 delivered; item 5 delivered as a **rigorous, cross-validated NEGATIVE** (the strongest
  form of the contribution); item 6 correctly de-prioritized by Gate 3 = No.

## Rigor notes
Two tempting "positive" surprises this project — the **Gate-4 soft-opt** result and the **Llama-8B causal** hint —
were each **adversarially audited and REJECTED** as artifacts (denominator inflation / judge false-positives /
generation-length selection bias / small-n noise). Every code change was bug-checked by a subagent. Grouped
leave-one-goal-out throughout; frozen StrongREJECT judge; disjoint splits.

## Note on artifacts
Large result files (`outputs/` ~42G, model weights `.cache/`, the `TROPT/` tool) are **gitignored** and referenced
by path in this doc and the progress log — they are not stored in git. All **code, docs, manifests, and the
registry** are committed to `main`.
