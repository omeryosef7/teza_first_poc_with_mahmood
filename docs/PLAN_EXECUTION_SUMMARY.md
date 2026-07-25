# Plan Execution Summary — everything we did, mapped to the plan, with verified results

**This is the single, self-contained results companion to the plan.** Read it together with
`docs/RESEARCH_PLAN_DISTILLING_JAILBREAKS.md` (the plan) and you have the whole project: what every phase
did, the result (with n, CIs, and the exact artifact), and what it means. Every headline number here was
**recomputed from the raw `outputs/` artifacts** (not copied from prior prose) — see the Verification
Appendix (§V) for the 88-check audit (0 mismatches, 0 pipeline bugs).

Supporting detail (not required to understand the project): `docs/CROSS_MODEL_MECHANISTIC_REPORT.md`
(paper-ready prose), `docs/DISTILLATION_FINDINGS_SYNTHESIS.md` (findings narrative),
`docs/RESEARCH_PLAN_PROGRESS_LOG.md` (chronological trace), `results/EXPERIMENT_REGISTRY.csv` (30 runs).

---

## 0. Headline (one paragraph)

We study **CoT-Hijacking**, a jailbreak that works on reasoning ("thinking") models by embedding a harmful
goal abstractly into a reasoning scaffold. The attack is real and strong (StrongREJECT ASR 0.77–1.00 across
five models). Inside the model, whether an attack will succeed is **linearly predictable from the residual
stream at grouped-LOGO AUC ≈ 0.90 — at the last input token, before any harmful content is generated.** But
under the strictest tests we can build, that signal is **predictive, not causal**: (1) its predictive value
*beyond prompt length* is not significant at our scale (length-confounded); (2) activation-addition steering
of the direction is neither sufficient nor necessary (4 layers × 3 timings, model coherence intact); (3)
optimizing the input to *maximize* the signal does not raise success (Gate-4 = No); and (4) this whole
picture **replicates across 4 architectures / 2 backbone families, an external harmful dataset, a second
signal family (attention concentration), and a second intervention type (attention temperature).** The one
apparent exception (DeepSeek-Qwen's length-independent signal) is a **label-distribution artifact**, not a
representational difference. Net: a rigorous, cross-validated **predictive-but-not-causal** result. The
plan's decision tree routes this (Gate-3 = No) to a **defensive detector**, which is the project's strongest
positive: the same signal flags a jailbreak *pre-generation* at AUC 0.92.

---

## 1. How to read this doc / the plan's organizing arc

The plan's central workflow (§30) is:

> **Real Attack → Predictive Signal → Causal Validation → Soft Objective → MAC Trigger → Held-Out Transfer**

and a **decision tree** (§25) with gates between stages. We executed the arc through the causal gate,
found an honest **negative at Gate 3** (signal is not causal), and followed the plan's *designated Gate-3
"No" branch* — detector + test-alternative-signals + cross-model replication — rather than forcing the
gated-off optimization phases. So the "missing" phases (10–12) are **not incomplete work**; they are
**correctly gated off** by a result the plan anticipated (§24.5 treats a clean negative as publishable).

Each phase below is: **What we did → Verified result → What it means → Artifact.**

---

## 2. Phase-by-phase

### Phase 0 — Freeze the current state (plan §4)
- **Did:** froze the pre-sprint baselines, judge, and splits so all new work compares against a fixed
  reference.
- **Result:** DONE. Baseline inventory + judge choice recorded.
- **Means:** establishes the "before" state; nothing measured yet.
- **Artifact:** `docs/CURRENT_STATE_AUDIT.md`.

### Phase 1 — Redesign the dataset split (plan §5)
- **Did:** built disjoint **dev-25** and **held-out-495** splits (plus a **held-out-25** scaling slice)
  with verified 0 overlap.
- **Result:** DONE, disjointness verified.
- **Means:** every predictive/detector AUC can be reported **out-of-fold across held-out goals**, so numbers
  are not memorized attack formatting.
- **Artifact:** `data/manifests/{dev_25,heldout_495,scale_heldout_25}.csv`.

### Phase 2 — Freeze the evaluation protocol (plan §6)
- **Did:** froze **StrongREJECT** as the judge (success = StrongREJECT ≥ 0.5 on any answer stream →
  **behavior-level ASR**), greedy decoding, and **grouped leave-one-goal-out (LOGO)** for all probes.
- **Result:** DONE. Judge validated against a hand-labeled sample.
- **Means:** one frozen definition of "success" throughout; a secondary Gemini judge is reported where
  available for cross-check.
- **Artifact:** `docs/JUDGE_VALIDATION.md`, `slurm_scripts/run_strongreject_cpu.slurm`.

### Phase 3 — Reproduce suffix-optimization baselines in TROPT (plan §7)
- **Did:** ran TROPT **GCG** and **MAC** with target-prefix-CE objective on Qwen3-14B, per-behavior,
  greedy-scored.
- **Result (verified):** GCG greedy behavior-ASR **0.450 (9/20)**, MAC **0.150 (3/20)**, no-attack baseline
  **0.100 (2/20)**. Near-zero prefix-CE loss (min 0.0002) co-occurs with only 45% behavioral success.
- **Means:** **target-prefix loss ≠ behavioral success** (a founding premise), and canonical suffix
  optimization underperforms on a reasoning model — motivating a *real* reasoning-specific attack.
- **Artifact:** `outputs/phase3_tropt/eval_greedy/FREE_GENERATION_RESULTS.jsonl`; `docs/TROPT_BASELINE_REPORT.md`;
  registry `phase3_tropt_gcg_qwen3_devtrain20`, `phase3_tropt_mac_qwen3_devtrain20`.

### Phase 4 — Establish the real attack baseline (plan §8)
- **Did:** ran **CoT-Hijacking** on the dev-25 goals against gpt-o4-mini.
- **Result (verified):** behavior-level StrongREJECT ASR **0.917 (22/24 behaviors that produced rows)**;
  secondary Gemini-judge 21 successes (0.84 over the full 25, 0.875 over the 24 with rows).
- **Means:** CoT-Hijacking is a genuine, high-success attack on a reasoning model — **Gate 1 = Yes**.
- **Artifact:** `outputs/phase4_cot_baseline/phase4_cot_gpt-o4-mini_dev25_strongreject.jsonl`; registry
  `phase4_cot_gpt-o4-mini_dev25`.

### Phase 4X — Cross-model attack benchmark (plan §31 amendment; open-source targets only)
- **Did:** ran the *same* CoT-Hijacking attack on dev-25 against **≥3 additional open-source thinking
  models**, plus a no-attack **clean** baseline for uplift. (User constraint: attack only open-weight,
  locally-run HF targets — never proprietary APIs.)
- **Result (verified, behavior-level StrongREJECT ASR; clean → uplift):**

  | target (architecture) | attacked ASR | clean ASR | uplift |
  |---|---|---|---|
  | **DeepSeek-R1-Distill-Llama-8B** (Llama) | **0.957** (22/23) | 0.360 (9/25) | **+0.597** |
  | **Phi-4-mini-reasoning** (Phi3) | **0.773** (17/22) | 0.400 (10/25) | **+0.373** |
  | **gemma-3-4b-it** | **1.000** (25/25) | 0.000 (0/25) | **+1.000** |

- **Means:** the reasoning-model vulnerability is **general**, not gpt-o4-mini-specific. gemma refuses all
  clean goals yet the attack breaks all 25 (maximal headroom). DeepSeek-Llama and Phi-4 have large real
  headroom → good white-box mechanistic targets.
- **Artifact:** `outputs/phase4_hf_local/*_dev25_strongreject.jsonl`,
  `outputs/phase4x_clean_baseline/clean_*_dev25_strongreject.jsonl`;
  `docs/CROSS_MODEL_COT_BENCHMARK_REPORT.md`; registry `phase4x_cot_*`.

### Phase 5 — Build the mechanistic dataset (plan §9)
- **Did:** ran CoT-Hijacking on the **white-box Qwen3-14B** target, labeled each generation success/failure
  by StrongREJECT, and extracted residual-stream hidden states at fixed positions (`prefill_last`,
  `startofthink`, `think_content_1/2`, `endofthink`, `endofresponse`) × all layers, forming groups
  **C (attack fail) / D (attack success)** (and suffix-control groups **F/G**).
- **Result (verified):** white-box Qwen3 attack ASR **0.818 (18/22)**; 44 attack rows (18 succ / 26 fail).
  Caveat: 27/44 responses truncated mid-`<think>` (Qwen3 reasoning is very long) but harmful content present.
- **Means:** yields the matched success/failure activation dataset the whole mechanistic analysis runs on.
- **Artifact:** `outputs/phase5_qwen3_cot/…_strongreject.jsonl`, `outputs/phase5_mechanistic/extraction/`;
  `docs/MECHANISTIC_DATASET_CARD.md`; registry `phase5_qwen3_cot_dev25`.

### Phase 6 — Search for predictive internal signals (plan §10)
- **Did:** fit a per-(position, layer) Fisher mean-difference **success direction** on C-vs-D; scored
  discriminability with grouped-LOGO AUC; ran a **length-confound control** (goal-clustered bootstrap on the
  out-of-fold gain of {projection + length} over {length alone}); and a suffix-presence control (F-vs-G).
- **Result (verified):** signal reaches **LOGO AUC ≈ 0.90 pre-answer** — `prefill_last` L16 **0.904**,
  `think_content_1` L20 **0.906**, `endofthink` L26 **0.906** — i.e. **before any token is generated**. But
  the gain *beyond prompt length* is **not significant at n=44**: length alone predicts success at AUC
  **0.827**, and the bootstrap 95% CI on the gain **includes 0 everywhere** (positive in sign, +0.03–0.06,
  P(gain>0) 0.68–0.84):

  | position | layer | raw AUC | length-only | LOGO gain | 95% CI | P(gain>0) |
  |---|---|---|---|---|---|---|
  | `prefill_last` | 13 | 0.904 | 0.827 | +0.052 | [−0.034, +0.194] | 0.82 |
  | `think_content_1` | 20 | 0.906 | 0.827 | +0.044 | [−0.052, +0.213] | 0.73 |
  | `think_content_2` | 40 | 0.912 | 0.827 | +0.060 | [−0.036, +0.213] | 0.84 |
  | `endofthink` | 26 | 0.906 | 0.829 | +0.026 | [−0.039, +0.213] | 0.68 |

  Control (F-vs-G, suffix presence not success): far weaker early (`prefill_last` L17 = 0.703 vs 0.904) →
  the C-vs-D signal is genuinely *success*-predictive, not attack-presence.
- **Means:** **Gate 2 = Yes** (a real, early, generalizing predictive signal exists) — **but** it is
  length-confounded, so a purely observational reading is ambiguous. The decisive next test is causal:
  steering holds the prompt (and its length) fixed, so it is immune to the confound.
- **Artifact:** `outputs/phase5_mechanistic/phase6_CvsD_auc.csv`, `phase6_CvsD_confound.csv`,
  `phase6_CvsD_confound_bootstrap.csv`, `phase6_FvsG_auc.csv`; `docs/PREDICTIVE_SIGNAL_REPORT.md`;
  registry `phase6_CvsD_signal_qwen3`, `phase6_FvsG_signal_qwen3`.

### Phase 7 — Causal validation (plan §11) — **NEGATIVE**
- **Did:** activation-addition `h' = h + (α·σ)·d_unit` on the success direction, StrongREJECT-scored on free
  generation. Tested **sufficiency** (add to clean harmful prompts), **necessity** (subtract from successful
  attacks), a **layer sweep** (L12/16/20/28), a **timing sweep** (generation-only vs prefill-only), and a
  **coherence/degeneracy** control.
- **Result (verified):**
  - *Sufficiency null:* `think_content_1` L20 → **0/45 at every α ∈ [−3,+3]**; `prefill_last` L16 → 2/45 at
    opposite extremes (non-monotone → judge noise).
  - *Necessity null:* subtracting from the D-success attacks keeps **ASR = 1.00 down to −3σ** (greedy α=0
    reproduces all successes → baseline valid).
  - *Layer sweep:* flat-null L12/16/20; L28 only an isolated 1/5 at α=−3 *and* α=+2 (noise).
  - *Timing sweep:* generation-only 0/35 (one isolated point), prefill-only 0/45 — all timings null.
  - *Coherence:* `think_closed`/`answer_present` **100% across the whole α range**, gen length 591–1065 tok,
    **zero degeneracy** — the null is genuine, not model breakage.
- **Means:** **Gate 3 = No.** The early success direction is a **detector/correlate, not a causal
  mechanism** — the single-direction activation-addition hypothesis (the most natural distillation target) is
  falsified across 4 layers × 3 timings. Per §25, treat as detector only; do not build it into the objective;
  test alternative signals. (Scope: does not by itself rule out attention-based or multivariate mechanisms —
  tested next.)
- **Artifact:** `outputs/phase7_causal/steer_*`, `phase7scale_*`; `docs/CAUSAL_VALIDATION_REPORT.md`;
  registry `phase7_steer_clean_*`, `phase7_necessity_Dsucc_tc1_L20`, `phase7_timing_*`.

### Phase 8 — Candidate objectives (plan §12): Gate-3 = No → test ALTERNATIVE signals instead
- **Did:** because Gate 3 = No de-prioritizes the success-direction objective, we instead tested whether a
  *different* signal family or intervention is causal — the attention mechanism (Appendix §C1) and a
  cross-model direction (§C2). See Appendix C.
- **Result:** alternatives also **NULL** (details in §Appendix-C).
- **Means:** the non-causality is not specific to one direction or one intervention type.
- **Artifact:** `outputs/phase8_attn_causal/`, `outputs/phase16_deepseek_cot_heldout25/steer_*`.

### Phase 9 — Soft optimization as an upper-bound test (plan §13) — Gate-4 = No
- **Did:** Adam-optimized a K=8 continuous **soft prefix** to *maximize* the success-direction projection
  (`prefill_last` L16) on clean harmful prompts — the optimization-side analogue of steering.
- **Result (verified):** the signal is **trivially maximizable** (projection driven far above the natural
  success mean), yet ASR does **not** follow. Honest baseline **2/25 = 0.08**; at α=1 the raw "increase" is
  **4/17 = 0.235** — an **artifact of denominator inflation** (8 empty off-manifold generations dropped from
  the denominator). Keeping the full denominator (`asr_conservative`) gives **4/25 = 0.16**; Fisher-exact
  2/25 vs 4/25 is **non-significant (p ≈ 0.67) → noise**. The off-manifold prefix even destroys the 2 natural
  baseline successes.
- **Means:** **Gate 4 = No.** Maximizing the signal does not causally raise ASR — predictive-not-causal now
  holds from the **optimization side** too, not just steering. Adversarially audited; no pipeline bug.
- **Artifact:** `outputs/phase9_softopt/pfl_L16/asr_vs_arm.csv`; registry `phase9_softopt_gate4_qwen3`.
  *(Verification note: the CSV supports baseline 0.08, raw 0.235, and `asr_conservative` 0.16; the finer
  "3/25 = 0.12 genuine" figure and the "14→470 projection" magnitude cited in the narrative reports come from
  the run's audit trace and are **not** reconstructable from the retained CSV — the Gate-4 = No conclusion
  stands on the verifiable 0.08 → 0.16, p≈0.67 numbers. See §V.)*

### Phases 10–12 — Discrete MAC / RL / Universal (plan §14–16) — GATED OFF
- **Did:** not entered. §25 Gate-4 = No explicitly says "do not spend large discrete compute yet"; Gates 5–6
  sit behind Gate 4 = Yes.
- **Result:** correctly gated off (consistent with the causal null).
- **Means:** these are not incomplete — the decision tree routes past them on a Gate-3/Gate-4 "No".

### Phase 13 — Analyze the large GCG suffix dataset (plan §17)
- **Did:** built a 336-suffix taxonomy + cross-category transfer matrix (prior sub-sprint, folded in here).
- **Result:** most-vulnerable category = misinfo (opt ASR 0.246); `cot_prefix_ce` is the best objective
  (uplift 0.090 vs 0.031); no seed overfitting (train 0.0801 vs unseen 0.0892).
- **Means:** corroborates "prefix-CE ≠ behavioral success" at dataset scale; no seed-memorization.
- **Artifact:** `docs/DATASET_ANALYSIS_REPORT.md`; `results/SUFFIX_TAXONOMY.csv`, `CATEGORY_TRANSFER_MATRIX.csv`.

### Phase 14 — Held-out evaluation (plan §18) — de-confound REPLICATES
- **Did:** replicated the Phase-6 predictive-signal + length-confound analysis on **n=48 held-out** rows
  (0 dev overlap).
- **Result (verified):** length-only AUC **0.720**; **every** detector's gain-over-length CI **includes 0**
  (replicates dev-25); raw AUCs **0.752–0.784** (< dev 0.92 → partial overfit).
- **Means:** the length confound is **not a dev-set fluke** — it holds on independent data; the detector
  transfers only weakly.
- **Artifact:** `outputs/phase7scale_qwen3_cot_heldout25/detector_CvsD_confound.csv`; registry
  `phase7scale_confound_heldout48`.

### Phase 15 — External dataset transfer (plan §19) — attack transfers, detector does NOT
- **Did:** ran CoT-Hijacking + the **advbench-fit** detector direction on **malicious_instruct** (99 prompts,
  a genuinely different harmful-behavior dataset, vendored).
- **Result (verified):** a clean **dissociation**. The *attack* transfers behaviorally — ASR **0.848
  (StrongREJECT, 84/99)** / **0.737 (Gemini judge)**. The *detector* does **not** transfer — the advbench-fit
  `prefill_last` L16 direction scores external success at **AUC 0.461 (chance)**, *below* even a weak
  external-fit signal (~0.64). Caveat: external labels are imbalanced (84 succ / 15 fail) → the external
  signal is itself weak.
- **Means:** the predictive signal is **dataset-specific**, not a general harmful-success representation —
  consistent with the length-correlate reading. (The two ASR numbers are different judges on the same run;
  earlier docs cited 0.737 next to the 84/99 StrongREJECT counts, conflating the two — corrected here.)
- **Artifact:** `outputs/phase_external/mech/ext_CvsD_auc.csv`, `ext_sr_scored.jsonl`; registry
  `external_transfer_maliciousinstruct`.

### Phase 16 — Cross-model generalization (plan §20) — the central deliverable
- **Did:** ran the **full signal → confound → causal** pipeline on **3 more reasoning models** spanning
  **4 architectures / 2 backbone families**, using the family-parameterized pipeline
  (`poc_stage4/model_family_utils.py`, `--model-family`). Found + fixed two think-position marker bugs
  (DeepSeek emits `<think>` in prefill; Phi-4 BPE-merges `<think>\n`) before extracting.
- **Result (verified):** the 4-model matrix below (§3). Every model is **predictive-but-not-causal**. The
  apparent DeepSeek-Qwen exception (its signal beats length) is a **label-distribution artifact**: it shares
  Qwen3's exact scaffolds *and* Qwen2 tokenizer → identical prompt lengths, so length separating Qwen3's
  successes but not DeepSeek's is a difference in *which attacks each model complies with*, not in how they
  encode length. DeepSeek-Llama (different tokenizer) has a *genuine* length-independent signal yet is
  **still** causally NULL (audited — its "steering effect" is a generation-length/`<think>`-termination
  artifact).
- **Means:** the predictive-not-causal finding is **robust across architectures, backbone families, and even
  to the length-confound question itself** (it holds where the confound explains the signal *and* where it
  doesn't).
- **Artifact:** `outputs/phase16_deepseek_cot_heldout25/detector_CvsD_{,think_}confound.csv`,
  `outputs/phase_phi4_cot/…confound.csv`, `outputs/phase_deepseek_llama_cot/…confound.csv`; registry
  `phase16_deepseek_*`, `phi4_crossmodel_confound`, `phi4_causal_steer`, `dsllama_causal_steer`.

### Phase 17 — Defensive interpretation (plan §21) — the strongest POSITIVE
- **Did:** trained the same C-vs-D signal as an early **success-vs-failure detector** (grouped-LOGO), across
  linear (Fisher/logistic) and MLP probes and across attack families.
- **Result (verified):** MLP **AUC 0.923–0.925** pre-answer (`think_content_1` L19 / `tc2` L28); Fisher
  0.906; `prefill_last` **0.904–0.917 at the last input token, pre-generation**. Strong on CoT attacks
  (0.92), moderate on suffix attacks (0.85) → the "success state" is partly attack-family-specific.
- **Means:** the negative on *mechanism* is a positive on *detection* — the plan's designated Gate-3 "No"
  branch. A CoT-Hijack can be flagged **before any harmful content is emitted**.
- **Artifact:** `outputs/phase17_detect/detector_CvsD*.csv`; `docs/ADAPTIVE_DETECTION_AND_DEFENSE_REPORT.md`;
  registry `phase17_detector_CvsD_qwen3`.

---

## 3. The cross-model matrix (Phase 16 — 4 models × signal / confound / causal)

| model (architecture) | signal (LOGO AUC) | confound (gain-over-length) | causal (steer) |
|---|---|---|---|
| **Qwen3-14B** | ~0.90 | CI ∋ 0 → **confounded** | **NULL** |
| **DeepSeek-R1-Distill-Qwen-7B** | 0.80–0.84 | `prefill_last` beats length (+0.337, CI[0.06,0.83]; think-fixed +0.370 CI[0.077,0.852]) **but = label artifact** | **NULL** (§C2) |
| **Phi-4-mini-reasoning** (Phi3) | 0.89–0.96 | `prefill_last` +0.036 CI[−0.02,0.19] ∋ 0 → **confounded**; `think_content_1` L29 marginal +0.098 CI[0.010,0.280] | **NULL** |
| **DeepSeek-R1-Distill-Llama-8B** (Llama) | 0.87–0.95 | +0.09–0.13, CI ∌ 0 → **genuinely beats prompt-length** (different tokenizer, so not a label artifact) | **NULL** (audited — length/termination artifact) |

Two models length-confounded (Qwen3, Phi-4); DeepSeek-Qwen's exception is a labeling effect; DeepSeek-Llama
has a *genuine* length-independent predictive signal yet is **still non-causal**. Across all four — and from
steering *and* input-optimization — the success signals are **predictive/detector-grade but not causal**.

---

## 4. Appendix C — Claude-proposed extensions (user-authorized)

Three extensions designed to attack the thesis from angles the core plan didn't cover; all adversarially
reviewed, implemented, bug-checked, and run.

- **§C1 — attention concentration is NOT a causal lever (Qwen3).** *Observational:* successful attacks have
  **more** concentrated attention (`attn_maxconc` LOGO AUC 0.739 — opposite the naive "hijacking scatters
  attention" hypothesis), but it is **length-confounded** (corr −0.79 with length; residualized 0.739→0.632;
  gain-over-length −0.007, CI ∋ 0). *Causal:* a pre-softmax attention-temperature intervention (rescale
  `self_attn.scaling` by 1/τ, holds prompt length fixed → confound-immune) is **null** — sufficiency null
  (sharpening clean prompts stays 0.08–0.12), necessity null (coherent regime τ∈[0.7,1.4] keeps ASR
  0.875–1.0; the only ASR→0 at τ=2.0 is **repetition degeneracy**, 16/17 rows, caught by a degeneracy filter
  `answer_present` alone missed). Resolves plan §11.8. `outputs/phase8_attn_causal/`; `c1_attn_temp_causal_qwen3`.
- **§C2 — the residual-direction causal null REPLICATES cross-model (DeepSeek).** Steering DeepSeek's
  *length-independent* `prefill_last` L25 direction — the single best cross-model candidate for a genuine
  mechanism — is also **null**: sufficiency null (clean baseline 0.32), necessity 1.0→0.857 (a 1/7 flip,
  within noise). `outputs/phase16_deepseek_cot_heldout25/steer_*`; `c2_deepseek_dir_causal`.
- **§C3 — the length confound is IRREDUCIBLE by matching (Qwen3).** Success vs failure attack-prompt lengths
  are near-*separated* — success mean 1012 tok (554–1615) vs failure 1388 (989–1676), AUC(length→success)
  **0.827** — so length-matched analysis is powerless: greedy caliper matching yields only **1 / 6 / 9** pairs
  at ±10 / ±25 / ±50 tokens (of 20 possible). Length and any length-correlated signal are structurally
  non-separable here. `outputs/phase5_mechanistic/phase6_length_identifiability.json`; `c3_length_identifiability`.

---

## 5. §25 Decision-tree outcome & §29 Minimum Publishable Outcome

**§25 gates:**
- **Gate 1** (attack works?) = **Yes** — 0.917 (gpt-o4-mini), 0.818 (Qwen3 white-box), 0.77–1.00 (Phase-4X).
- **Gate 2** (predictive signal?) = **Yes** — LOGO AUC ≈ 0.90 pre-answer, generalizes via grouped-LOGO.
- **Gate 3** (causal?) = **No** — sufficiency + necessity nulls, 4 layers × 3 timings, coherence intact.
  → routed to the plan's "No" branch: **detector only** (Phase 17), **test alternative signals** (§C1/§C2,
  also null), **consider multivariate** (MLP detector, still length-confounded).
- **Gate 4** (soft-opt manipulates signal *and* behavior?) = **No** — Phase 9 (0.08 → 0.16, p≈0.67).
- **Gates 5–6** — gated off behind Gate 4 = Yes; not entered (correct, not incomplete).

**§29 MPO (item-by-item):**
1. Canonical GCG underperforms on reasoning models — ✅ (Phase 3: GCG 0.450 / MAC 0.150; + suffix dataset).
2. Prefix loss poorly correlated with behavioral success — ✅ (Phase 3 near-zero loss @ 45% ASR; founding premise).
3. A real reasoning-model attack with sufficient success — ✅ (Phase 4/5: 0.917 / 0.818; Phase-4X 0.77–1.00).
4. A success-predictive internal signal that generalizes — ✅ (Phase 6: LOGO AUC 0.90), with honest confound caveat.
5. A causal intervention showing the signal affects success — **✗ delivered as a rigorous NEGATIVE** (Phase 7),
   the strongest form of the contribution (§24.5); **reframes** the story to *predictive-but-not-causal*.
6. Initial evidence that optimizing the signal improves attack search — **de-prioritized** by Gate-3 = No
   (§12.3 O4); the optimization side was instead used as a *falsification* (Gate-4 = No).

**Net:** items 1–4 delivered; item 5 as a cross-validated negative; item 6 correctly de-prioritized. The
project's strongest **positive** is the Phase-17 pre-generation detector — the plan's designated Gate-3
"No" deliverable.

**§28 paper story mapping:** (1) suffix opt misaligned with reasoning-model success — ✅; (2) attacks succeed
via an early internal signal — ✅; (3) signal predicts across held-out goals — ✅ *but length-confounded*;
(4) direct intervention changes jailbreak probability — **✗ the honest finding is the opposite** → the story
becomes *predictive-but-not-causal*; (5)–(8) objective/trigger/transfer — gated off; (9) same signal supports
early detection — ✅ (Phase 17).

---

## 6. Honest negatives & rigor

**Kept negatives (§24.5):**
- The Phase-6 signal is **length-confounded** (gain-beyond-length not significant at n=44; replicates held-out).
- The success direction is **non-causal** (sufficiency + necessity nulls across layers and timings).
- The success "state" is partly **attack-family-specific** (CoT 0.92 → suffix 0.85), not one universal rep.
- The detector is **dataset-specific** (advbench-fit → external AUC 0.461 = chance).

**Two tempting "positives" adversarially rejected as artifacts:**
- **Gate-4 soft-opt** apparent 0.235 → denominator inflation + a StrongREJECT false-positive (bare
  goal-restatement scored sr=1.0); honest → noise.
- **DeepSeek-Llama "causal" hint** → generation-length / `<think>`-termination selection bias (empty answers
  are 4096-tok truncations; +α just makes the model stop thinking sooner); Fisher p=0.567.

**Rigor:** grouped leave-one-goal-out throughout; frozen StrongREJECT judge; disjoint dev/held-out splits
(verified); degeneracy filter (unique-word-ratio) applied to all interventions; two full adversarial audits
(10 + 7 minor bugs, fixed and re-verified); two marker/tokenizer bugs found, fixed, and re-run before the
cross-model results were reported. **Small-n honesty:** the core confound analysis is n=44 (dev,
exploratory); DeepSeek gain CI [0.06, 0.83] is wide and barely excludes 0; where possible, results were
replicated held-out (n=48). **Scope of the causal null:** it closes the single-direction activation-addition
hypothesis (4 layers × 3 timings) and the *uniform* attention-temperature hypothesis; it does **not** rule
out a position/head-specific attention mechanism or a multivariate/nonlinear mechanism (genuinely open).

---

## V. Verification appendix — this doc proves its own numbers

Every headline number above was **recomputed from the raw `outputs/` artifacts** by a 10-way fan-out
(one verifier per phase-group) plus an adversarial audit pass on anything flagged. Behavior-level ASRs were
recomputed from the per-row `*_strongreject.jsonl` (grouped by goal, success = any stream ≥ 0.5) — **not**
read from the `by_hijacking_success` block of the summary JSONs, which is a different metric.

**Result: 88 checks across 10 groups — 0 MISMATCH, 0 pipeline bugs, 3 CANT_VERIFY (all documentation-precision, not bugs).**

| group | outcome |
|---|---|
| Attack ASRs (Phase 3/4/4X/5) | 10/10 reproduce exactly from per-row jsonl (0.917, 0.818, 0.957, 0.773, 1.000, GCG 0.450 / MAC 0.150, all clean baselines & uplifts) |
| Predictive signal (Phase 6) | AUC cells + length-only 0.827 + all gain CIs (∋0) reproduce from the 4 CSVs |
| Causal null (Phase 7 + timing) | all sufficiency/necessity/coherence/timing nulls reproduce (ASR 0/45, necessity 1.00, 100% coherent) |
| Gate-4 soft-opt (Phase 9) | baseline 0.08, raw 0.235, `asr_conservative` 0.16 reproduce; **CANT_VERIFY:** "3/25=0.12 genuine" + "14→470 projection" not in retained artifacts (conclusion unaffected) |
| External transfer (Phase 15) | transfer AUC 0.461 reproduces exactly; ASR clarified (StrongREJECT 0.848 / Gemini 0.737); **CANT_VERIFY:** advbench in-dist 0.90 lives in the phase7 track, out of scope of external artifacts |
| Held-out de-confound (Phase 14) | length-only 0.720, all gain CIs ∋0, raw 0.75–0.78 reproduce |
| Cross-model DeepSeek-Qwen (16-A/B) | all AUCs / gains / CIs reproduce from confound CSVs (n=35) |
| Cross-model Phi-4 & DeepSeek-Llama (16-C/D) | all AUCs / gains / CIs reproduce; both causal-steer dirs present & consistent with audited NULL |
| Detector (17) + Appendix C | 10/10 reproduce (detector AUCs, attn-temp causal, length-identifiability JSON, DeepSeek §C2) |
| Registry integrity | 30/30 rows have on-disk artifacts; all `asr = n_success/n_total` & `uplift` internally consistent; **CANT_VERIFY:** `phase16_crossmodel_lengthtest` has no dedicated file (pure re-analysis of Phase-4X inputs, which exist) |

**Corrections applied to this doc vs. earlier prose:** (1) external attack ASR now states both judges
(StrongREJECT 0.848 / Gemini 0.737) instead of citing 0.737 next to StrongREJECT counts; (2) the Phase-9
Gate-4 result is stated on its verifiable anchors (0.08 → 0.16, Fisher p≈0.67) with the unverifiable
"3/25=0.12 / 14→470" figures explicitly flagged. No number required a *value* correction; no discrepancy
indicated a real pipeline bug.

---

## 7. Artifact / registry index

- **Plan:** `docs/RESEARCH_PLAN_DISTILLING_JAILBREAKS.md` (the other of the two canonical files).
- **Registry:** `results/EXPERIMENT_REGISTRY.csv` — 30 runs, one row per experiment (columns incl. model,
  split, objective, ASRs, uplift, n, slurm_job_id, notes).
- **Per-topic reports (supporting detail):** `CROSS_MODEL_MECHANISTIC_REPORT.md` (paper prose),
  `DISTILLATION_FINDINGS_SYNTHESIS.md`, `PREDICTIVE_SIGNAL_REPORT.md`, `CAUSAL_VALIDATION_REPORT.md`,
  `ADAPTIVE_DETECTION_AND_DEFENSE_REPORT.md`, `CROSS_MODEL_COT_BENCHMARK_REPORT.md`,
  `DATASET_ANALYSIS_REPORT.md`, `TROPT_BASELINE_REPORT.md`, `MECHANISTIC_DATASET_CARD.md`.
- **Pipeline code:** `poc_stage4/{model_family_utils,phase7_steer_generate,phase8_attn_temp_generate,phase9_soft_opt}.py`,
  `poc_stage_ae/{run_ae_generation,replay_hidden_states,thinking_position_utils}.py`,
  `scripts/phase6_*.py`, `scripts/phase7_*.py`, `scripts/phase13_suffix_analysis.py`, `scripts/phase17_*.py`.
- **Note on storage:** `outputs/` (~42 GB), model weights (`.cache/`), and the `TROPT/` tool are
  **gitignored** and referenced by path here and in the progress log; all **code, docs, manifests, and the
  registry** are committed to `main`.
