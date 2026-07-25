# Cross-Model Mechanistic Report: CoT-Hijacking Is Predictive-but-Not-Causal

*A standalone, paper-ready section. Every quantitative claim cites an artifact path and, where a
run exists, a `results/EXPERIMENT_REGISTRY.csv` `run_id`. Sources: `docs/DISTILLATION_FINDINGS_SYNTHESIS.md`,
`docs/CAUSAL_VALIDATION_REPORT.md`, `docs/PREDICTIVE_SIGNAL_REPORT.md`, `results/EXPERIMENT_REGISTRY.csv`.*

---

## Summary of the contribution

We study *CoT-Hijacking*, a jailbreak that succeeds on reasoning ("thinking") language models, and we ask
the mechanistic question: **does the attack work through an identifiable, causally manipulable internal
mechanism?** We establish an early residual-stream *success direction* that is strongly **predictive** of
whether an attack will succeed — separating success from failure at grouped leave-one-goal-out (LOGO)
AUC ≈ 0.90 *before the model generates any harmful content*. We then subject this signal to the strictest
tests we can construct and reach a clean, honestly-hedged **negative**:

1. Its predictive value **beyond prompt length** is not statistically significant at our dev-set scale (the
   signal is **length-confounded**).
2. It is **not causal** — neither sufficient nor necessary — under activation-addition steering across four
   layers and three intervention timings, with model coherence intact throughout.
3. Optimizing the input to **maximize** the signal (soft-prompt attack, Gate-4) does **not** raise attack
   success; the apparent gain was an artifact of denominator inflation plus a judge false positive.
4. This whole picture **replicates across three architecturally distinct reasoning models** — Qwen3-14B,
   DeepSeek-R1-Distill-Qwen-7B, and Phi-4-mini-reasoning — and across a second signal family (attention
   concentration) and a second intervention type (attention temperature).

The central finding is therefore a rigorous, cross-model **predictive-but-not-causal** result: the internal
signature of a successful CoT-Hijack is a *detector/correlate* of success, largely downstream of
attack-prompt length, not a manipulable mechanism. The one apparent cross-model exception (DeepSeek's
length-independent signal) is shown to be a **label-distribution artifact**, not a representational
difference.

---

## 1. Setup: attack, judge, and evaluation protocol

**Attack — CoT-Hijacking.** The attack embeds a harmful goal abstractly into a puzzle/reasoning scaffold
so the model is induced to comply during or after its chain-of-thought, rather than being asked directly.
It does *not* quote the harmful goal verbatim: 46/48 prompts contain no locatable harmful span
(`scripts/phase6_attention_signal.py`), which matters later for the span-based attention analysis.

**Judge — StrongREJECT.** Success is StrongREJECT ≥ 0.5 on the answer stream (frozen judge throughout;
behavior-level ASR = any-stream ≥ 0.5). We report it alongside a secondary Gemini judge where available.

**Effectiveness of the attack (RQ1 baselines).** CoT-Hijacking is a *real* attack with genuine headroom
over the un-attacked (clean) baseline:

| target | attacked ASR | clean ASR | uplift | run_id |
|---|---|---|---|---|
| gpt-o4-mini (dev-25) | **0.917** (22/24) | — | — | `phase4_cot_gpt-o4-mini_dev25` |
| Qwen3-14B (white-box) | **0.818** (18/22) | — | — | `phase5_qwen3_cot_dev25` |
| DeepSeek-R1-Distill-Llama-8B | 0.957 (22/23) | 0.360 | +0.597 | `phase4x_cot_deepseek-r1-distill-llama-8b_dev25` |
| Phi-4-mini-reasoning | 0.773 (17/22) | 0.400 | +0.373 | `phase4x_cot_phi-4-mini-reasoning_dev25` |
| gemma-3-4b-it | 1.000 (25/25) | 0.000 | +1.000 | `phase4x_cot_gemma-3-4b-it_dev25` |

For context, canonical suffix optimization underperforms on the white-box reasoning model: per-behavior
TROPT-GCG greedy ASR 0.450 and TROPT-MAC 0.150 (`phase3_tropt_gcg_qwen3_devtrain20`,
`phase3_tropt_mac_qwen3_devtrain20`), and near-zero prefix-CE loss coincides with only 45% behavioral
success — i.e. **target-prefix loss is not behavioral success**, a founding premise of this work.

**Generalization protocol.** All predictive/detection AUCs use **grouped leave-one-goal-out** (LOGO):
every fold holds out an entire goal, so reported numbers are out-of-fold across held-out behaviors, never
memorized formatting. Dev/held-out splits are disjoint (verified). Dev-set results are labeled
**exploratory** (n is small); held-out replications are reported separately.

---

## 2. The predictive early signal (AUC ≈ 0.90) — and its length confound

**The signal.** On the Qwen3-14B residual-stream dataset (`docs/MECHANISTIC_DATASET_CARD.md`;
`outputs/phase5_mechanistic/extraction/`), a per-(position, layer) Fisher mean-difference direction
separates attack **success from failure** (C∪D = CoT-Hijack success vs failure, StrongREJECT labels on
AE-regenerated outputs). Grouped-LOGO out-of-fold AUC (`scripts/phase6_signal_search.py`,
`outputs/phase5_mechanistic/phase6_CvsD_auc.csv`, `phase6_CvsD_signal_qwen3`; n=44, 24 succ / 20 fail,
22 goals, 16 both-class):

| position (temporal) | best layer | depth | LOGO AUC |
|---|---|---|---|
| `prefill_last` (last INPUT token, pre-generation) | 16 | 0.40 | **0.904** |
| `startofthink` | 28 | 0.70 | 0.879 |
| `think_content_1` (first thinking token) | 20 | 0.50 | **0.906** |
| `think_content_2` | 40 | 1.00 | 0.912 |
| `endofthink` (think→answer transition) | 26 | 0.65 | 0.906 |

The decisive point: separability reaches ≈0.90 **at the last input token, before a single token is
generated** (`prefill_last` L16 = 0.904). The attack induces an early internal state predictive of eventual
success well ahead of any harmful output.

**Control (attack presence, not success).** The optimized-suffix control (F∪G, suffix present vs absent;
`phase6_FvsG_auc.csv`, `phase6_FvsG_signal_qwen3`) is far weaker early — `prefill_last` L17 = 0.703 vs the
real attack's 0.904 — with strong signal only at the post-answer `endofresponse` position (excluded per
§10.5). So the C-vs-D signal is genuinely *success*-predictive, not a mere attack-presence detector.

**The confound.** Success and failure differ in prompt length: mean input tokens **1012 (success) vs 1388
(fail)**; length alone predicts success at **AUC 0.827** (`scripts/phase6_confound_control.py`,
`phase6_CvsD_confound.csv`). Early positions (`prefill_last`, `think_content_1`) are computed at/before the
first generated token, so generation length cannot confound them — but **input length can**. The formal
control (goal-clustered weighted bootstrap on the out-of-fold gain of {projection + length} over {length
alone}, `phase6_CvsD_confound_bootstrap.csv`):

| position | layer | raw AUC | length-only | LOGO gain | 95% CI | P(gain>0) |
|---|---|---|---|---|---|---|
| `prefill_last` | 13 | 0.904 | 0.827 | +0.052 | [−0.034, +0.194] | 0.82 |
| `think_content_1` | 20 | 0.906 | 0.827 | +0.044 | [−0.052, +0.213] | 0.73 |
| `think_content_2` | 40 | 0.912 | 0.827 | +0.060 | [−0.036, +0.213] | 0.84 |
| `endofthink` | 26 | 0.906 | 0.829 | +0.026 | [−0.039, +0.213] | 0.68 |

**Verdict: predictive but not length-independent at n=44.** The gain is positive in sign at every cell
(+0.03 to +0.06) but its bootstrap 95% CI **includes 0 everywhere** (P(gain>0) = 0.68–0.84). The Phase-6
decision gate (§10) scores criteria (a) success-not-presence, (b) held-out generalization, (c) pre-answer
as **PASS**, and (d) confound-survival as **QUALIFIED**. Because a purely predictive confound is ambiguous
at this scale, the decisive next step is causal: activation-addition holds the prompt (and its length)
**fixed**, so it is immune to the length confound the predictive analysis cannot resolve.

**Why the confound is irreducible here (identifiability diagnostic).** A length-matched analysis is
powerless because the classes are near-*separated* in length: AUC(length→success) = 0.827, and greedy
caliper matching yields only 1 / 6 / 9 pairs at ±10 / ±25 / ±50 tokens out of 20 possible
(`scripts/phase6_length_identifiability.py`, `phase6_length_identifiability.json`, `c3_length_identifiability`).
Length and any length-correlated internal signal are structurally non-separable in this pool.

---

## 3. Causal validation is NULL (Qwen3, Phase 7)

We test whether the success direction is *causally* responsible via activation addition
`h_L' = h_L + (α·σ)·d_unit`, α in projection-std units, StrongREJECT-scored on free generation
(`poc_stage4/phase7_steer_generate.py`, `scripts/phase7_analyze_causal.py`).

**Sufficiency (clean harmful prompts).** Adding the direction to un-attacked harmful prompts does not
induce success (`outputs/phase7_causal/steer_pilot__*`):
- `think_content_1` L20: **0/45 at every α ∈ [−3, +3]** (`phase7_steer_clean_tc1_L20`).
- `prefill_last` L16: 2/45, at α=+3 and α=−3 (opposite extremes, different goals, no monotone trend →
  judge noise) (`phase7_steer_clean_pfl_L16`).

**Necessity (attacked context).** Subtracting the direction from the 6 D-condition *success* attacks does
not suppress them — ASR stays **1.00 down to −3σ** (`steer_attacked_necessity__tc1_L20/asr_vs_alpha.csv`,
`phase7_necessity_Dsucc_tc1_L20`). Greedy α=0 reproduces success on all 6, so the greedy-vs-sampled
baseline confound did not floor the test.

**Layer sweep** (`steer_layersweep__tc1_L{12,28}` + L16/L20 pilots): baseline and max ASR are flat-null at
L12, L16, L20; L28 shows only an isolated 1/5 at α=−3 *and* α=+2 (opposite directions → non-monotone
noise). Shallow→deep, no layer rescues causality.

**Timing sweep** (`--timing`, `steer_timing_{gen,prefill}__tc1_L20`): "generation-only" gives 0/35 except
one isolated α=+2 point (`phase7_timing_gen_tc1_L20`); "prefill-only" gives 0/45 at every α
(`phase7_timing_prefill_tc1_L20`). All three timings null.

**Degeneracy / coherence control (specificity).** Format integrity (`think_closed`, `answer_present`) is
**100% across the entire α ∈ [−3, +3] range**, generation length stays 591–1065 tokens, and a
unique-word-ratio degeneracy flag confirms zero degeneracy in all activation-addition runs
(`scripts/phase7_analyze_causal.py`). Steering to ±3σ along an AUC-0.90 direction leaves behavior *and*
coherence unchanged — the null is genuine, not model breakage.

**→ The early success direction is non-causal — neither sufficient nor necessary — under every
residual-stream intervention we can construct (4 layers × 3 timings), coherence intact.** Per the §25
decision tree this is **Gate-3 = No**: treat the signal as a detector only, do not build it into the
mechanistic objective. Scope: this falsifies the single-direction activation-addition hypothesis (the most
natural distillation target); it does not by itself rule out attention-based or multivariate mechanisms —
tested next.

---

## 4. Optimization side is also NULL: Gate-4 = No (soft-prompt attack)

The steering tests perturb activations directly; the complementary question is whether *optimizing the
input to maximize the signal* raises success. A K=8 continuous soft prefix was Adam-optimized to maximize
the success-direction projection (`prefill_last` L16) on clean harmful prompts
(`outputs/phase9_softopt/`, `phase9_softopt_gate4_qwen3`):

- **The signal is trivially maximizable:** projection driven **14.2 → 470** (~45× the natural success mean
  of 10.6). If maximizing the signal caused success, ASR should rise sharply.
- **It does not.** The raw "increase" (optimized 4/17 = 0.235 vs baseline 2/25 = 0.08) was an **artifact**:
  the denominator dropped 8 empty off-manifold failures, and one StrongREJECT **false positive** scored a
  bare goal-restatement sr = 1.0. The honest genuine value is 3/25 = 0.12 vs 0.08, **Fisher p = 1.0
  (noise)**.
- The off-manifold prefix even **destroys** the two natural baseline successes.

**→ Gate-4 = No.** Maximizing the signal does not causally raise ASR. The predictive-not-causal conclusion
now holds from the optimization side as well as the steering side. Adversarially audited; no pipeline bug.

---

## 5. The cross-model matrix (Qwen3 / DeepSeek-Qwen / Phi-4 / DeepSeek-Llama × signal / confound / causal)

We replicated the full signal → confound → causal pipeline on two additional, architecturally distinct
reasoning models, reusing the family-parameterized pipeline (`poc_stage4/model_family_utils.py`,
`poc_stage_ae/*`, `--model-family`).

| model (architecture) | signal (AUC) | confound (gain-over-length) | causal (steer) |
|---|---|---|---|
| **Qwen3-14B** | ~0.90 | CI ∋ 0 → **confounded** | **NULL** |
| **DeepSeek-R1-Distill-Qwen-7B** | 0.80–0.84 | `prefill_last` beats length **but = label artifact** | **NULL** |
| **Phi-4-mini-reasoning** (Phi3ForCausalLM) | 0.89–0.96 | +0.036, CI ∋ 0 → **confounded** | **NULL** |
| **DeepSeek-R1-Distill-Llama-8B** (LlamaForCausalLM) | 0.87–0.95 | +0.09–0.13, CI ∌ 0 → **genuinely beats prompt-length** | **NULL** (audited — length/termination artifact) |

**Phi-4-mini-reasoning** — a different architecture (Microsoft math reasoner, hidden 3072 / 32 layers).
Strong signal (`prefill_last` L7 AUC 0.890, `think_content_1` L29 0.960); length-confounded
(`prefill_last` gain +0.036, CI [−0.02, +0.19] ∋ 0; length-only 0.837; `phi4_crossmodel_confound`); causal
NULL (steer `prefill_last` L7: sufficiency null with baseline 0.44 the highest, necessity rise has the
*opposite sign* to the sufficiency arm → inconsistent-sign noise on an n=20 ceiling; `phi4_causal_steer`).
So Qwen3's picture replicates exactly on a completely different architecture.

**DeepSeek-R1-Distill-Qwen-7B** — the apparent exception, resolved. On the held-out sample, DeepSeek's
`prefill_last` signal (0.80–0.84) *beats* length (gain +0.337, CI [0.06, 0.83] barely excludes 0;
length-only 0.591 ≈ chance; `phase16_deepseek_confound_heldout`), and with the marker bug fixed (below) the
localization sharpens: `prefill_last` L25 gain +0.370, CI [0.077, 0.852], P+ = 1.00, while the *generated*
`think_content_1` positions have gains whose CIs all include 0 — i.e. the length-independent component sits
at the **input token**, not the reasoning content (`phase16_deepseek_think_confound`; extraction_fixed
29/29 shards).

**Why this is NOT a real exception (label artifact, verified).** DeepSeek-R1-Distill-Qwen uses the **same
25 held-out attack scaffolds and the same Qwen2 tokenizer** as Qwen3 → the two models' **prompt-length
distributions are identical**. Length can therefore separate Qwen3's successes but not DeepSeek's **only
because their success labels differ** (which attacks each model happens to comply with), not because the
models encode length differently. So "success = length" is a property of *Qwen3's success labels*, not
evidence that DeepSeek carries a length-independent internal success *representation*. The earlier
"mechanism is model-dependent" framing overclaimed and is **retracted**. Decisively, DeepSeek's
length-independent `prefill_last` L25 direction — the single best cross-model candidate for a genuine
mechanism — is **also causally NULL** under steering (sufficiency null, baseline 0.32; necessity 1.0→0.857
= a 1/7 flip within noise; `c2_deepseek_dir_causal`).

**Second signal family and second intervention type (Qwen3), both NULL.** To rule out that the null is
specific to the residual direction or to activation addition:
- *Attention concentration* predicts success (`attn_maxconc` LOGO AUC 0.739; successful attacks are *more*
  concentrated — the opposite of the naive "hijacking scatters attention" hypothesis) but is
  length-confounded (corr −0.79 with length; residualized 0.739→0.632; gain-over-length −0.007, CI ∋ 0;
  `phase6_attention_signal_heldout`). Span-based hijacking is untestable — the attack has no locatable
  harmful span.
- *Attention-temperature* intervention (rescale `self_attn.scaling` by 1/τ; holds prompt length fixed →
  confound-immune): sufficiency null (sharpening clean prompts does not raise ASR above the τ=1 baseline
  0.08–0.12); necessity null (in the coherence-preserving regime τ∈[0.7,1.4], ASR stays 0.875–1.0; the only
  ASR→0 point at τ=2.0 is **repetition degeneracy**, 16/17 rows at unique-word ratio 0.05, caught by the
  degeneracy filter that `answer_present` alone missed; `c1_attn_temp_causal_qwen3`).

**DeepSeek-R1-Distill-Llama-8B** — the strongest test, and it strengthens the thesis. On a *second backbone
family* (Llama, hidden 4096 / 32 layers), the success signal (`prefill_last` 0.87, `think_content_1` 0.90)
**genuinely beats prompt-length**: gain-over-length +0.09 to +0.13, CIs exclude 0 (`think_content_1` L32 P+=1.0).
Unlike DeepSeek-Qwen, Llama-8B has a *different tokenizer*, so the identical-lengths / label-artifact explanation
does not apply — this is a real length-independent predictive component (n=68, modest, re-scored labels). **Yet the
causal test is still NULL.** Steering the direction *appeared* to raise ASR with +α in both arms, but an adversarial
audit rejected it: every "empty" answer is a 4096-token truncation still inside `<think>`, so `answer_present` (which
rises 0.00→1.00 with α, mean tokens collapsing 4096→873) tracks *think-termination, not compliance* — +α makes the
model emit its already-harmful answer sooner, −α makes it truncate. The necessity "rise" is a pure denominator effect;
the sufficiency bump (0.375→0.48) is Fisher **p=0.567 (noise)**, non-monotone, with judge false-positives at α=+3.
`asr_conservative` flattens it. So steering here **modulates generation length — the length confound re-expressed
causally**. Even the model whose predictive signal beats prompt-length is not causally manipulable.

## 5b. External-dataset transfer (does the detector generalize beyond advbench?)
CoT-Hijacking + the advbench-fit detector were tested on **malicious_instruct** (99 prompts, a genuinely different
harmful-behavior dataset). A clean **dissociation**: the *attack* transfers behaviorally (ASR **0.737**, comparable to
advbench), but the *detector* does not transfer mechanistically — the advbench-fit `prefill_last` L16 direction scores
external success at **AUC 0.461 (chance)**, *below* even a weak external-fit signal (0.64, vs advbench in-distribution
0.90). So the predictive signal is **dataset-specific**, not a general harmful-success representation — consistent with
the length-correlate reading. (Caveat: external labels are imbalanced — 84 success / 15 failure after re-scoring — so
the external signal is itself weak; a solid-but-caveated negative.)

**Net.** Across **four architectures / two backbone families** (Qwen3-14B, DeepSeek-R1-Distill-Qwen-7B,
Phi-4-mini-reasoning, DeepSeek-R1-Distill-Llama-8B) **and an external harmful dataset**, **two
signal families** (residual success direction, attention concentration), and **two intervention types**
(activation addition, attention temperature), the CoT-Hijacking success signals are uniformly
**predictive/detector-grade but not causal**. The DeepSeek "exception" is a labeling effect, not a
length-independent mechanism. On Qwen3 specifically, the honest mechanistic verdict is that CoT-Hijacking
success is substantially a function of **attack-prompt length**, with the internal signals as length
correlates rather than independent causal mechanisms.

---

## 6. What the signal IS good for: an early defensive detector

The negative on *mechanism* is a positive on *detection* — the plan's designated Gate-3 "No" branch. The
same signal works as an early success-vs-failure detector: MLP **AUC 0.925** (`think_content_1` L19) and
**AUC 0.917 at the last input token, pre-generation** (`phase17_detector_CvsD_qwen3`,
`outputs/phase17_detect/`), i.e. a jailbreak can be flagged *before* harmful content is emitted. It is
strong on CoT attacks (0.92) and moderate on suffix attacks (0.85), so the "success state" is partly
attack-family-specific rather than one universal representation — stated as an honest limitation, not a
universal claim.

---

## 7. Honest negatives and limitations

- **Small n.** The core confound analysis is n=44 (dev); the DeepSeek gain CI [0.06, 0.83] is wide and
  *barely* excludes 0 (only 8/19 goals carry both classes; the length LOGO baseline is itself noisy).
  Dev-set results are exploratory; where possible we replicated held-out (n=48: every detector's
  gain-over-length CI still includes 0; raw AUC drops 0.90→0.78 = partial overfit; `phase7scale_confound_heldout48`).
- **Re-scoring noise.** Labels depend on StrongREJECT re-scoring of sometimes-truncated CoTs (27/44 Qwen3
  responses truncated mid-`<think>`; 11/58 Phi-4 C rows flipped on re-score). A StrongREJECT **false
  positive** (scoring a bare goal-restatement as success) inflated the Gate-4 raw number until audited.
- **Off-manifold degeneracy.** Aggressive interventions (soft-prompt ~45×, attention temperature τ→{0.5,2.0})
  push the model off-manifold into empty or repetition-loop output that a naive `answer_present`/ASR check
  misreads. A unique-word-ratio degeneracy filter was added and applied uniformly; the activation-addition
  nulls have zero degeneracy, so they are not degeneracy artifacts.
- **Marker / tokenizer bugs found and fixed.** (i) DeepSeek's segmenter searched for `<think>` as a
  *generated* start marker, but DeepSeek emits it in the **prefill** → think positions were NaN in 0/35
  generations; fixed via `THINK_START_IN_PREFILL_BY_FAMILY` + a guarded `locate_positions` +
  `replay --recompute-positions` (re-extracted 29/29 shards). (ii) Phi-4 emits `<think>\n` where BPE merges
  `>`+`\n` into one token, so the standalone `<think>` marker never matched → NaN think positions; fixed by
  matching `<think>\n` (`poc_stage4/model_family_utils.py`). Both were caught, fixed, and re-run; the
  reported Phi-4/DeepSeek think-content results are post-fix.
- **Scope of the causal null.** It closes the single-direction activation-addition hypothesis (4 layers ×
  3 timings) and the *uniform* attention-temperature hypothesis. It does not rule out a **position/head-specific**
  attention mechanism or a **multivariate/nonlinear** mechanism — genuinely open, out of scope here.
- **Partial-NaN cells.** Phi-4 `think_content_1` gain-over-length is not computable (5/72 NaN rows → the
  confound tool returns None on partial-NaN cells); `prefill_last` is the clean cell reported. `endofthink`
  is unreliable for the 2/35 DeepSeek rows that never close `</think>`.

## Provenance

Reports: `docs/DISTILLATION_FINDINGS_SYNTHESIS.md` (§16-A/B/C, Appendix C), `docs/CAUSAL_VALIDATION_REPORT.md`,
`docs/PREDICTIVE_SIGNAL_REPORT.md`, `docs/ADAPTIVE_DETECTION_AND_DEFENSE_REPORT.md`. Registry:
`results/EXPERIMENT_REGISTRY.csv`. Pipeline: `poc_stage4/model_family_utils.py`,
`poc_stage_ae/{run_ae_generation,replay_hidden_states,thinking_position_utils}.py`,
`scripts/{phase6_signal_search,phase6_confound_control,phase7_extract_success_direction,phase7_analyze_causal,phase6_length_identifiability}.py`,
`poc_stage4/phase7_steer_generate.py`. Two full adversarial audits (10 + 7 minor bugs, all fixed and
re-verified); grouped LOGO throughout; frozen StrongREJECT judge; disjoint dev/held-out splits (verified).
