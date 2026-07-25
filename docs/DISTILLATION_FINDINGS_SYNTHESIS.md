# Distillation Project — Findings Synthesis (maps to plan §28/§29)

> **Canonical self-contained results doc:** `docs/PLAN_EXECUTION_SUMMARY.md` (read with the plan
> `docs/RESEARCH_PLAN_DISTILLING_JAILBREAKS.md` = the whole project, output-verified). This file is
> supporting narrative detail.

> **Paper-ready write-up:** `docs/CROSS_MODEL_MECHANISTIC_REPORT.md` (the 4-model matrix + Gate-4 + external
> transfer + honest negatives). **Full chronological trace + artifact index:** `docs/RESEARCH_PLAN_PROGRESS_LOG.md`.
> **Registry:** `results/EXPERIMENT_REGISTRY.csv` (30 rows).

One-page synthesis of `docs/RESEARCH_PLAN_DISTILLING_JAILBREAKS.md` execution. The plan's organizing
workflow is **Real Attack → Predictive Signal → Causal Validation → (Soft) Objective → MAC Trigger →
Transfer**. We executed it through the causal gate and, on the honest negative there, pivoted to the
plan's designated Gate-3 branch (defensive detection). Every claim below cites an artifact.

## The core arc (what we found)

| Step | Result | Evidence |
|---|---|---|
| **Real attack works** (Phase 4/5) | CoT-Hijacking succeeds on reasoning models: gpt-o4-mini dev-25 StrongREJECT **0.917**; white-box **Qwen3-14B behavior-level ASR 0.818** (18/22). | `docs/RESEARCH_PLAN_PROGRESS_LOG.md` iter; `outputs/phase5_qwen3_cot/`, registry `phase4_cot_gpt-o4-mini_dev25`, `phase5_qwen3_cot_dev25` |
| **Predictive early signal** (Phase 6) | Attack **success vs failure** is linearly separable in the residual stream at **LOGO AUC ≈ 0.90 from the last input token onward** (`prefill_last` L16 0.904, `think_content_1` L20 0.906, `endofthink` L26 0.906) — *before* any harmful content; generalizes across held-out goals (grouped leave-one-goal-out). | `docs/PREDICTIVE_SIGNAL_REPORT.md`; `outputs/phase5_mechanistic/phase6_CvsD_auc.csv` |
| **…but confound-qualified** | The predictive value *beyond prompt length* is **not significant at n=44** (goal-clustered bootstrap 95% CI on the out-of-fold gain includes 0; P(gain>0)=0.68–0.84). Length alone predicts success at AUC 0.827. | `PREDICTIVE_SIGNAL_REPORT.md` §3; `outputs/phase5_mechanistic/phase6_CvsD_confound{,_bootstrap}.csv` |
| **Causal test — NEGATIVE** (Phase 7) | Activation-addition of the success direction is **neither sufficient** (clean prompts: ASR 0/45 across layers L12/16/20/28, α∈±3σ) **nor necessary** (attacked context: subtracting it keeps ASR 1.00 down to −3σ), with **§11.6 coherence 100% intact** throughout. **→ the direction is a detector/correlate, not a causal mechanism.** | `docs/CAUSAL_VALIDATION_REPORT.md`; `outputs/phase7_causal/steer_pilot__*`, `steer_attacked_necessity__*`, `steer_layersweep__*` |
| **Defensive detector** (Phase 17) | The same signal **works as an early success-vs-failure detector**: MLP **AUC 0.925** (`think_content_1` L19), and **AUC 0.917 at the last input token, pre-generation** (logistic L38). Cross-condition: strong on CoT attacks (0.92), moderate on suffix attacks (0.85). | `docs/ADAPTIVE_DETECTION_AND_DEFENSE_REPORT.md`; `outputs/phase17_detect/detector_CvsD*.csv` |
| **Suffix-dataset analysis** (Phase 13) | 336-suffix taxonomy + category transfer matrix; most-vulnerable category misinfo (opt ASR 0.246), cot_prefix_ce the best objective (uplift 0.090 vs 0.031), no seed overfitting (train 0.0801 vs unseen 0.0892). | `docs/DATASET_ANALYSIS_REPORT.md`; `results/SUFFIX_TAXONOMY.csv`, `CATEGORY_TRANSFER_MATRIX.csv` |

## Mapping to §29 (Minimum Publishable Outcome)
1. **Canonical GCG underperforms on reasoning models** — ✅ (prior GCG work + Phase-3 TROPT baselines: GCG 0.450 / MAC 0.150 greedy per-behavior; `TROPT_BASELINE_REPORT.md`).
2. **Target-prefix loss poorly correlated with behavioral success** — ✅ established (prior work; a founding premise, `CURRENT_STATE_AUDIT.md`).
3. **A real reasoning-model attack with sufficient success** — ✅ Phase 4/5 (0.917 / 0.818).
4. **A success-predictive internal signal that generalizes** — ✅ Phase 6 (LOGO AUC 0.90), with the honest confound caveat.
5. **A causal intervention showing the signal affects attack success** — **✗ NEGATIVE** (Phase 7): the candidate direction is *not* causal. This is a legitimate, informative result (§24.5), and it **reframes** the contribution.
6. **Initial evidence that optimizing the signal improves attack search** — not pursued (Gate-3 "No" de-prioritized the success-direction objective; §12.3 O4).

**Net:** items 1–4 delivered; item 5 delivered as a **rigorous negative**; the project's strongest positive contribution is the **early detector** (Phase 17) — a defensive result the plan explicitly routes to under Gate-3 "No" (§25 → §21).

## Mapping to §28 (Expected Final Paper Story)
- (1) standard suffix opt misaligned with reasoning-model jailbreak success — ✅ supported (Phase 3 + Phase 6 "prefix-CE ≠ behavioral success").
- (2) existing attacks succeed via an **identifiable early internal signal** — ✅ (Phase 6, AUC 0.90 pre-answer).
- (3) the signal predicts success across held-out instructions, not just attack formatting — **partly**: it predicts C-vs-D success (not mere presence), generalizes via LOGO, but is length-confounded at n=44 (de-confounding experiment in progress).
- (4) **direct intervention changes jailbreak probability** — **✗** the honest finding is the opposite for this direction (Phase 7 null). The paper story becomes: *predictive-but-not-causal*, which motivates (9).
- (5)–(8) mechanistic-objective / trigger / transfer — not reached (gated by the Phase-7 negative).
- (9) **the same internal signal supports early attack detection** — ✅ Phase 17 (pre-generation AUC 0.92).

## Honest negatives kept (§24.5)
- The Phase-6 signal is length-confounded (gain-beyond-length not significant at n=44).
- The success direction is non-causal (sufficiency + necessity nulls across layers).
- The success "state" is partly attack-family-specific (C∪D 0.92 → F∪G 0.85), not one universal representation.

## ★★ Claude-extension results (Appendix C) — the non-causality generalizes across models AND mechanisms
Three user-authorized extensions (plan Appendix C) were designed, adversarially reviewed, implemented, and run:
- **§C1 — attention concentration is NOT a causal lever (Qwen3).** A pre-softmax attention-temperature
  intervention (rescale `self_attn.scaling` by 1/τ; holds prompt length fixed → confound-immune). SUFFICIENCY
  null (sharpen clean prompts: ASR stays ~0.08–0.12, no rise). NECESSITY null: in the coherence-preserving
  regime (τ∈[0.7,1.4]) flattening does NOT reduce ASR (stays 0.875–1.0, both all-layer and targeted L22–30);
  the only ASR drop (τ=2.0→0) is **repetition DEGENERACY** (16/17 rows, unique-word ratio 0.05 — caught via a
  degeneracy check that `answer_present` alone missed). So the observational §10.1-D attention signal is a
  correlate, not a uniform-temperature causal mechanism (does not rule out position/head-specific ones). This
  resolves plan §11.8. `outputs/phase8_attn_causal/`.
- **§C2 — the residual-direction causal null REPLICATES cross-model (DeepSeek).** Steering DeepSeek's
  *length-independent* `prefill_last` L25 direction (the one signal that beats length, §16-B): SUFFICIENCY null
  (clean baseline 0.32, no systematic ±α change) and NECESSITY null (subtracting → 1.0→0.857, a single-row flip
  in n=7, within noise). So even DeepSeek's genuine length-independent signal is a detector/correlate, not
  causal — the Qwen3 Phase-7 null is not model-specific. `outputs/phase16_deepseek_cot_heldout25/steer_*`.
- **§C3 — the length confound is IRREDUCIBLE by matching (see §Unified closure below).**
- **§Phase-9 Gate-4 (optimization side) — soft-optimizing the input to MAXIMIZE the signal does NOT raise ASR.**
  A K=8 continuous soft prefix was optimized (Adam) to maximize the success-direction projection on clean harmful
  prompts. The projection is trivially maximized — driven 14.2→470 (~45× the natural success mean 10.6) — yet ASR
  does NOT causally follow: the raw "increase" (optimized 4/17=0.235 vs baseline 2/25=0.08) was an ARTIFACT
  (denominator dropping 8 empty off-manifold failures + one StrongREJECT false-positive that scored a bare goal-
  restatement sr=1.0); the honest genuine value is 3/25=0.12 vs 0.08, **Fisher p=1.0 (noise)**. The off-manifold
  prefix (~45×) even DESTROYS the two natural baseline successes. So Gate 4 = No — the same predictive-not-causal
  conclusion now holds from the OPTIMIZATION side too, not just steering. Adversarially audited
  (`outputs/phase9_softopt/`, workflow-verified). This closes the plan's §25 Gate-4 for the success-direction objective.

**Net (strengthened thesis):** across **two models** (Qwen3, DeepSeek) and **two signal families** (residual
success direction, attention concentration), the CoT-Hijacking success signals are **predictive/detector-grade
but not causal**. The predictive-not-causal contribution is now cross-model and cross-mechanism, not a single
negative result.

## ★ Unified closure — the internal signals are downstream of PROMPT LENGTH
The mechanism search is now exhaustive across both candidate families, and they converge:
- **Held-out de-confounding replication (n=48, 0 dev overlap):** the residual-signal length confound
  REPLICATES — every detector's gain-over-length CI includes 0 on independent data too; the detector
  transfers only weakly (raw 0.90→0.78). `docs/ADAPTIVE_DETECTION_AND_DEFENSE_REPORT.md` (held-out section).
- **Timing sweep (§11.2):** the residual direction is non-causal under generation-only AND prefill-only
  steering too — non-causal across all layers AND timings. `docs/CAUSAL_VALIDATION_REPORT.md` §5b.
- **Attention family (§10.1-D):** span-based hijacking is untestable (the attack encodes the goal
  abstractly — no locatable harmful span). Span-free attention *concentration* predicts success
  (LOGO AUC 0.74; successful attacks are MORE focused, opposite the naive hypothesis) — **but it is
  length-confounded like the residual signal** (corr −0.79 with prompt length; residualized 0.74→0.63).
  `docs/PREDICTIVE_SIGNAL_REPORT.md` §6.

**On Qwen3, both signal families are downstream proxies of attack-prompt LENGTH.** Shorter CoT-Hijacking
prompts succeed more (length→success AUC 0.28), and they carry both concentrated attention and a
distinguishable residual state — length is the common cause. **Honest mechanistic verdict (Qwen3):
CoT-Hijacking success on Qwen3 is substantially a function of attack-prompt length; the internal signals
are length correlates, not independent, causal, or length-independent mechanisms.** **IMPORTANT — the
cross-model replication (below) shows the length confound does NOT replicate on DeepSeek-R1 (its
success-signal gain-over-length CI excludes 0), but on verification this is a LABEL-distribution
difference, not a representational one:** DeepSeek shares Qwen3's exact prompts and tokenizer, so prompt
lengths are identical across the two models — length simply fails to separate *which attacks DeepSeek
complies with*, whereas it separates Qwen3's. So "success = length" is specific to Qwen3's success
labels; it is NOT evidence that DeepSeek encodes success in a length-independent internal representation.

Both confounds are now bootstrap-CI'd at matched rigor (residual §3: gain ∋0; attention §6: gain −0.007
∋0) — the length confound is established, not conjectured.

**Why the length confound is irreducible here (§C3 identifiability diagnostic, Claude extension):** on
Qwen3 C∪D, successful vs failed attack-prompt lengths are near-SEPARATED — success mean 1012 tok (554–1615)
vs failure 1388 (989–1676), AUC(length→success)=0.827 — so a length-matched analysis is powerless: greedy
caliper matching yields only 1 / 6 / 9 pairs at ±10 / ±25 / ±50 tokens (of 20 possible). Length and any
length-correlated internal signal are therefore structurally NON-separable in this pool; the confound
cannot be matched away because the classes barely overlap in length. `scripts/phase6_length_identifiability.py`,
`outputs/phase5_mechanistic/phase6_length_identifiability.json`.

## Genuinely open (future work, out of scope here)
- §11.8 causal attention *intervention* (masking/rescaling) — a distinct hypothesis from the residual one.
- Cross-model (§16): DONE for DeepSeek — behavioral length-direction check + full MECHANISTIC confound
  (see §16 sections below; on DeepSeek the length confound does NOT replicate, but this is a
  label-distribution difference, not a representational one — verified). Extending to Phi-4 and a causal
  test on DeepSeek remain open. DeepSeek think-position extraction marker bug is now FIXED
  (`THINK_START_IN_PREFILL_BY_FAMILY` + guarded `locate_positions` + `replay --recompute-positions`,
  bug-checked) but the re-extraction to populate think-content hidden states is INFRA-BLOCKED: the 15GB
  DeepSeek weights don't fit the L40S nodes' node-local /tmp (~1–9GB free sampled) under the §31.3
  ephemeral-cache constraint. Low priority — the core result rests on prefill_last (already validated) and
  the finding is a label-distribution effect on these 35 rows, so think-content would likely just
  replicate it. External-dataset transfer (§15) also open.

## Rigor / provenance
Two full adversarial audits (10 + 7 minor bugs, all fixed & re-verified); every phase bug-checked;
grouped leave-one-goal-out throughout; frozen StrongREJECT judge (§6); disjoint dev/held-out splits
(Phase-1 criterion verified). Full trace in `docs/RESEARCH_PLAN_PROGRESS_LOG.md`; registry
`results/EXPERIMENT_REGISTRY.csv`.

## §16 Cross-model check — length→success is consistent but WEAK across models
Zero-compute test on the existing Phase-4X attack outputs (`outputs/phase4_hf_local/*_strongreject.jsonl`):
does shorter attack-prompt length predict success on OTHER reasoning models?
- Qwen3 (attack-original labels): AUC(prompt_len→success) 0.40; **DeepSeek-R1-Distill-8B 0.455**;
  **Phi-4-mini-reasoning 0.445** — all `shorter→success` (AUC<0.5), but WEAK (corr ~0 for DeepSeek/Phi).

**Nuance + honest caveat on the Qwen3 result.** The *direction* (shorter succeeds) is cross-model
consistent, but the effect is modest with matched attack-original labels (0.40–0.46). Qwen3's STRONG
length confound (seq_len→success AUC 0.28, corr −0.79 with attention) appeared with the **AE-regeneration
labels** (sampled 32768-tok re-gen), so part of that strength is labeling-process-driven, not a pure
prompt-length→behavior law. The core mechanistic claim is unchanged (the residual + attention gains
BEYOND length are n.s., so neither is a length-independent mechanism), but the raw "length predicts
success" magnitude is Qwen3-/labeling-specific and only weakly universal. Both are stated in the reports.

## ★★ §16 Cross-model MECHANISTIC contrast — the length confound does NOT replicate on DeepSeek, but the reason is a LABEL difference (verified)
Full mechanistic replication on **DeepSeek-R1-Distill-Qwen-7B** (25 held-out goals → 29 C/D shards, 35
rows, 12 succ/23 fail; new `deepseek_r1` extraction support, §31.3 node-local). Same confound pipeline
(`outputs/phase16_deepseek_cot_heldout25/{detector_CvsD_confound,phase6_CvsD_auc}.csv`):

| model | early signal AUC | length-only AUC | gain-over-length (CI) | verdict |
|---|---|---|---|---|
| **Qwen3-14B** | ~0.90 (think_content_1) | **0.72–0.83** | ≈0, CI ∋ 0 | length-CONFOUNDED |
| **DeepSeek-R1-Distill-7B** | ~0.82–0.84 (prefill_last L14–28) | **0.591 (≈chance)** | **+0.337, CI [0.06, 0.83], P+=0.998** | signal beats length |

**→ Cross-model observation:** DeepSeek's early success signal (at the last INPUT token, prefill_last)
**adds signal BEYOND prompt length** (gain CI excludes 0), whereas Qwen3's does not; length barely
predicts DeepSeek's success (0.591 ≈ chance) but strongly predicts Qwen3's.

**What this does — and does NOT — mean (independently verified, `outputs/phase16_deepseek_cot_heldout25/`):**
DeepSeek-R1-Distill-Qwen uses the **same 25 held-out attack scaffolds and the same Qwen2 tokenizer** as
Qwen3, so the two models' **prompt-length distributions are identical**. Therefore length separating
success on Qwen3 but not DeepSeek **cannot be a difference in prompt lengths or in how the models encode
length — it is a difference in SUCCESS LABELS** (which attacks each model happens to comply with).
DeepSeek complies with a set of attacks that is *not* sorted by prompt length; Qwen3's is. So the honest
reading is: **"success = length" is a property of Qwen3's success labels, NOT evidence that DeepSeek has a
length-independent internal success representation.** The earlier framing ("mechanism is model-dependent /
DeepSeek encodes a genuine length-independent signal") **overclaimed** and is retracted here.

Caveats (honest, all confirmed on verification):
1. **n=35 (12 pos); only 8/19 goals carry both classes.** The gain CI [0.06, 0.83] is wide and barely
   excludes 0 (the length LOGO baseline 0.475 is itself noisy). Suggestive, not established.
2. **Label-distribution effect, not representational** (see above) — identical prompts/tokenizer.
3. **DeepSeek think-position extraction WAS broken, now FIXED (2026-07-23):** the `deepseek_r1` segmenter
   searched for `<think>` as a *start marker in generated text*, but DeepSeek emits `<think>` in the
   **prefill** (input ends `<｜Assistant｜><think>\n`), so it was found in 0/35 generations → think positions
   NaN. Fixed via `THINK_START_IN_PREFILL_BY_FAMILY` + a guarded `locate_positions` branch +
   `replay --recompute-positions` (bug-checked; job 677795 re-extracted 29/29 shards; think_content_1 now
   finite, e.g. token "Okay" at the first generated position). See §16-B below for the recovered result.

## ★★ §16-B Think-content signal now RECOVERED — DeepSeek's length-independent signal is at the INPUT token, not the reasoning content
With the marker bug fixed (caveat 3 above), the previously-NaN think positions were re-extracted
(`outputs/phase16_deepseek_cot_heldout25/extraction_fixed/`) and run through the same length-confound
pipeline (`detector_CvsD_think_confound.csv`, length-controlled at matched rigor; length-only AUC 0.591):

| position | raw AUC | gain-over-length (95% CI) | P(gain>0) | verdict |
|---|---|---|---|---|
| **`prefill_last` L25** (last INPUT token) | 0.837 | **+0.370 [0.077, 0.852]** | 1.00 | **beats length (CI excludes 0)** |
| `think_content_1` L7 / L12 / L20 (generated think) | 0.80–0.82 | +0.018 / +0.073 / +0.181, **all CI ∋ 0** | 0.64–0.86 | length-confounded |

**→ Localization result:** DeepSeek's genuine, length-independent success signal sits at the **INPUT
token** (`prefill_last`), *before generation*. Once properly extracted, the **generated think-content**
position (`think_content_1`) has raw separability (~0.80) but does **NOT** add beyond prompt length
out-of-fold (grouped-LOGO gain CI includes 0 at every layer) — i.e. it is a length proxy, exactly like
*all* of Qwen3's positions. So the earlier "only prefill_last was robust" was not merely an extraction
artifact: even with think-content recovered, the length-independent component is specifically at the input
position. (`endofthink` cell is unreliable — NaN for the 2/35 rows that never emit `</think>`.) This
completes the cross-model MECHANISTIC replication beyond `prefill_last` and is consistent with §16-A's
label-distribution reading: length weakly predicts DeepSeek success (0.591), and only the input-token
representation carries anything beyond it.

This is a genuine cross-model MECHANISTIC replication (not just the behavioral length-direction check
earlier), enabled by new DeepSeek-R1 extraction support — but its correct interpretation is narrower than
first stated.

## ★★ §16-C THIRD model (Phi-4-mini-reasoning) — length-confounded, like Qwen3
Full mechanistic replication on **Phi-4-mini-reasoning** (Phi3ForCausalLM — a *different architecture*, a
Microsoft math-reasoning model; hidden 3072 / 32 layers), reusing the same pipeline (`outputs/phase_phi4_cot/`;
user-authorized §31.3-B download + a BPE marker-fix, see below). C∪D = 69 attack rows (re-scored success 20).
- **Strong predictive signal:** `prefill_last` L7 AUC **0.890**, `think_content_1` L29 **0.960**, `startofthink`
  L5 0.919 — Phi-4 also carries a strong early success signal, consistent with Qwen3 + DeepSeek.
- **Confound = LENGTH-CONFOUNDED:** `prefill_last` gain-over-length **+0.036, CI [−0.02, 0.19] includes 0**;
  length alone predicts success at **0.837**. So the input-token signal is a **length proxy** — matching Qwen3,
  on a completely different architecture. **Refinement (after the partial-NaN confound-tool fix):** the STRONGEST
  cell, `think_content_1` L29 (the reasoning-content position; raw 0.96), has a *marginal* length-independent
  component — gain +0.098, CI [0.010, 0.280], P+=0.994 (barely excludes 0), L28 +0.090 [0.004, 0.267]; `startofthink`
  stays confounded (CI ∋ 0). This is WEAK (CI barely clears 0, P+ 0.99 not 1.0) and on NOISY re-scored labels
  (11/58 flipped), so it refines rather than overturns "Phi-4 is mostly length-confounded." (Contrast §16-B: on
  DeepSeek it was `prefill_last` that had the length-independent component and `think_content_1` that did not —
  the position flips across models, and both effects are weak/marginal, consistent with the overall length-correlate verdict.)
- **Marker bug caught + fixed:** Phi-4 emits `<think>\n` where BPE merges `>`+`\n` into one token, so the
  standalone `<think>` marker never matched → think positions came out NaN; fixed by matching `<think>\n`
  (`poc_stage4/model_family_utils.py`), re-replayed via `--recompute-positions`.

- **Causal test = NULL** (steer `prefill_last` L7, scoring the CoT since Phi-4 doesn't close `</think>`):
  sufficiency null (baseline 0.44 is the HIGHEST; steering either way lowers it); necessity null (subtracting
  does NOT suppress: 0.75→0.80/0.85). The α>0 necessity rise (→0.95) has the OPPOSITE sign to the sufficiency
  arm's α>0 (which lowered ASR) — inconsistent signs = noise, not a causal lever — on already-succeeding attacks
  (n=20 ceiling) with a length-confounded direction. So Phi-4's direction is not causal, replicating Qwen3 + DeepSeek.

## ★★ §16-D FOURTH model (DeepSeek-R1-Distill-Llama-8B) — signal GENUINELY beats prompt-length, but STILL not causal
Fourth architecture (LlamaForCausalLM — a *second backbone family*; hidden 4096/32 layers), full pipeline
(`outputs/phase_deepseek_llama_cot/`; §31.3-B download, markers correct first-pass — no re-replay). C∪D = 68 (33 succ/35 fail).
- **Strong signal:** `prefill_last` L2 AUC 0.872, `think_content_1` L31 0.895.
- **CONFOUND — genuinely BEATS length (the only clean such case):** gain-over-length +0.090 to +0.127, CIs EXCLUDE 0
  (`think_content_1` L32 +0.127 [0.051, 0.216], P+=1.0); len-only 0.783. **Unlike DeepSeek-Qwen's beat-length (a label
  artifact — same tokenizer as Qwen3 → identical lengths), Llama-8B has a DIFFERENT tokenizer, so the identical-lengths
  explanation does NOT apply.** So this is a *genuine* length-independent predictive signal — an honest complication to
  "universal length confound" (caveat: n=68, modest gains, re-scored labels).
- **CAUSAL — NULL (adversarially audited, artifact rejected):** steering the direction *appeared* to raise ASR with +α
  in both arms — but the audit proved this is a **generation-length / `<think>`-termination selection artifact**: every
  empty answer is a 4096-token truncation still inside `<think>`; +α makes the model stop thinking and emit its
  (already-harmful) answer sooner, −α makes it truncate and emit nothing. `answer_present` rises 0.00→1.00 with α; mean
  tokens collapse 4096→873. The necessity "rise" is a pure denominator effect; the sufficiency bump (0.375→0.48) is
  Fisher **p=0.567 (noise)**, non-monotone, with Gate-4-style judge false-positives at α=+3. `asr_conservative` flattens
  it. So steering here **modulates generation length — the length confound re-expressed causally** — not compliance.

**→ Even the model whose predictive signal GENUINELY beats prompt-length is NOT causally manipulable.** This strengthens
the thesis rather than complicating it: predictive-not-causal holds even where the length confound doesn't explain the signal.

**★★ Cross-model matrix COMPLETE (4 models × signal / confound / causal):**

| model | signal (AUC) | confound (gain-over-length) | causal (steer) |
|---|---|---|---|
| **Qwen3-14B** | ~0.90 | ∋0 → confounded | NULL |
| **DeepSeek-R1-Qwen-7B** | 0.80–0.84 | beats length **but = label artifact** (§16-A/B) | NULL |
| **Phi-4-mini** (Phi3) | 0.89–0.96 | prefill_last ∋0; think_content_1 marginal | NULL |
| **DeepSeek-R1-Llama-8B** | 0.87–0.95 | **genuinely beats prompt-length** (+0.09–0.13, CI∌0) | NULL (audited — length/termination artifact) |

Across **four architectures / two backbone families**, CoT-Hijacking's predictive internal signals are **not causally
manipulable** — from steering OR (§Phase-9) input optimization — whether or not they are length-confounded. Two models are
length-confounded (Qwen3, Phi-4); DeepSeek-Qwen's exception is a labeling effect; Llama-8B has a genuine length-independent
predictive component yet is STILL non-causal. This is the honest, cross-validated, cross-model form of the project's central
**predictive-but-not-causal** finding — and the causal null is now robust to the length-confound question itself.
