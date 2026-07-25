# Predictive Signal Report (Phase 6, §10)

Searches the §9 Qwen3-14B residual-stream dataset for the **earliest / shallowest** signal that
predicts **attack success vs failure**, using grouped **leave-one-goal-out** (LOGO) out-of-fold AUC
(§10.3) with a Fisher mean-difference direction per (token-position, layer). Method reuses
`poc_stage_ae/analyze_early_token_signals.py` helpers via `scripts/phase6_signal_search.py`; labels
are StrongREJECT on the captured (AE-regenerated) outputs.

**Status: COMPLETE.** Core C-vs-D attack-success direction + F-vs-G suffix-presence control both run
on the corrected all-104-row labels (StrongREJECT job 674377). Signal searches jobs 674430 (C∪D) /
674431 (F∪G). Classification: **EXPLORATORY** (§24.4) — the confound control (§10.4) is the gating
item before this becomes a confirmatory Phase-7 input.

## Positions (§9.4) and layers
10 named positions: `prefill_last` (last input token, pre-generation), `startofthink`,
`think_content_1/2/3`, `endofthink` (think→answer transition), `answer_content_1/2/3`, `endofresponse`.
41 layer indices (embedding output + 40 Qwen3 layers); `normalized_depth = layer/40`.
`answer_content_1/2/3` are **non-applicable for every row** (all captures are `enable_thinking=True`;
`thinking_position_utils.py:157` fills those positions only when thinking is OFF) → NaN placeholders,
correctly masked out by `phase6_signal_search.py` (per-position finite mask). So **7 of 10 positions
carry usable states**; the 3 dropped are post-answer (§10.5-excluded anyway).

## 1. Core — CoT-Hijacking attack success (C ∪ D), attack-SUCCESS direction
`scripts/phase6_signal_search.py --conditions C D` → `outputs/phase5_mechanistic/phase6_CvsD_auc.csv`
(job 674430). Labels are **StrongREJECT on the AE re-generation** (sampled, 32768-tok budget), so the
success/failure split is label-driven, not shard-driven. **n=44** attack examples (**24 success /
20 fail**) over **22 goals; 16 goals carry both classes** → non-degenerate LOGO folds.

Best layer per position (position order = temporal order), grouped LOGO out-of-fold AUC:
| position (temporal) | best layer | depth | LOGO AUC | n |
|---|---|---|---|---|
| `prefill_last` (last input tok, pre-gen) | 16 | 0.40 | **0.904** | 44 |
| `startofthink` | 28 | 0.70 | 0.879 | 44 |
| `think_content_1` (1st thinking tok) | 20 | 0.50 | **0.906** | 44 |
| `think_content_2` | 40 | 1.00 | 0.912 | 44 |
| `think_content_3` | 17 | 0.42 | 0.887 | 44 |
| `endofthink` (think→answer transition) | 26 | 0.65 | 0.906 | 43\* |
| `endofresponse` (post-answer) | 1 | 0.02 | 0.887 | 44 |

\* `endofthink` n=43: the one C row that never closed `</think>` (`qwen3|458|C|…|cot2`,
`finish_reason=max_new_tokens`) has a NaN placeholder there, correctly dropped by the finite mask (the
row still contributes at all other positions).

**Reading.** Attack success is **linearly separable from failure at AUC ≈ 0.90 from the last INPUT
token onward** — i.e. *before the model generates a single token* (`prefill_last` L16 = 0.904) — and
stays ≈0.90 through the **first thinking token** (`think_content_1` L20 = 0.906) and the
**think→answer transition** (`endofthink` L26 = 0.906). Every pre-answer position is ≥0.88. Peak is
`think_content_2` L40 (0.912) but the *shallowest strong* cell is `prefill_last` L1 (AUC 0.854;
L16 = 0.904). This is exactly the plan's thesis (§28.2–3): the real CoT-Hijacking attack induces an
**early internal state** that determines whether the jailbreak will succeed, well ahead of any
harmful content.

## 2. Control — suffix success (F ∪ G), attack-PRESENCE
`scripts/phase6_signal_search.py --conditions F G` → `outputs/phase5_mechanistic/phase6_FvsG_auc.csv`
(job 674431, corrected labels). n=40 suffix examples (10 success / 30 fail) over ~20 goals.

Best layer per position:
| position (temporal) | best layer | depth | LOGO AUC |
|---|---|---|---|
| `prefill_last` | 17 | 0.43 | 0.703 |
| `startofthink` | 8 | 0.20 | 0.727 |
| `think_content_1` | 24 | 0.60 | 0.807 |
| `endofthink` | 24 | 0.60 | 0.787 |
| `endofresponse` (post-answer) | 39 | 0.97 | **0.863** |

**Contrast with the core result.** For the optimized suffix, the only strong signal is at
`endofresponse` (post-answer, **§10.5-excluded**); its earliest pre-answer cell is a weak
`prefill_last` L17 = 0.703. The **real attack (C/D) is far more early-predictable than the optimized
suffix (F/G)** at matched positions (e.g. `prefill_last`: 0.904 vs 0.703; `think_content_1`: 0.906 vs
0.807). This supports the plan's core motivation (§30): standard suffix optimization is poorly aligned
with the early success mechanism that the real attack exploits.

## 3. Confound control (§10.4) — REQUIRED before the gate is clean
Success and failure differ in length: mean input tokens **1012 (success) vs 1388 (fail)**; mean
generation tokens **9136 vs 22531**. Length alone predicts success (in-sample C∪D):
- input-length (neg): **AUC 0.827**
- generation-length (neg): **AUC 0.863**

Interpretation:
- **Generation length cannot confound the early positions** (`prefill_last`, `think_content_1`): those
  hidden states are computed at/before the first generated token, so they cannot depend on how long the
  generation eventually is. The gen-length baseline (0.863) is therefore not a valid confound for the
  early signal.
- **Input length IS a candidate confound for `prefill_last`** (0.827 baseline vs 0.904 signal). Formal
  control run (below).
- C and D share the CoT-Hijacking attack-prompt template (matched pairs, §9.2), so prompt *format* is
  matched between classes; the length difference is goal-driven (longer harmful instructions tend to
  fail), which is the specific confound to partial out.

**Formal control — `scripts/phase6_confound_control.py`** (out-of-fold per-row projections from
`phase6_signal_search.py --emit-projections`, `outputs/phase5_mechanistic/phase6_CvsD_confound.csv`).
For each (position, layer): raw AUC; length-only AUC; **length-residualized** AUC (projection minus OLS
fit on standardized input length); and grouped-LOGO logistic AUC of {projection + input_len} vs
{input_len alone} (does the direction add signal beyond length, out-of-fold?).

| position | layer | raw | length-only | residualized† | LOGO {proj+len} | LOGO {len} | gain | gain 95% CI‡ | P(gain>0)‡ |
|---|---|---|---|---|---|---|---|---|---|
| `prefill_last` | 13 | 0.904 | 0.827 | 0.756 | 0.848 | 0.796 | +0.052 | [−0.034, +0.194] | 0.82 |
| `think_content_1` | 20 | 0.906 | 0.827 | 0.773 | 0.840 | 0.796 | +0.044 | [−0.052, +0.213] | 0.73 |
| `think_content_1` | 17 | 0.906 | 0.827 | 0.760 | 0.827 | 0.796 | +0.031 | [−0.044, +0.191] | 0.70 |
| `think_content_2` | 40 | 0.912 | 0.827 | 0.769 | 0.856 | 0.796 | +0.060 | [−0.036, +0.213] | 0.84 |
| `endofthink` | 26 | 0.906 | 0.829 | 0.741 | 0.822 | 0.796 | +0.026 | [−0.039, +0.213] | 0.68 |

† `residualized_auc` is fit-and-scored in-sample (OLS on all 44 rows) — descriptive, not out-of-fold.
‡ Goal-clustered **weighted** bootstrap (1000×, resampling the 22 goals; a goal drawn more than once is
weighted within a single fold, never split across train/test — leak-free) on the out-of-fold gain
(`outputs/phase5_mechanistic/phase6_CvsD_confound_bootstrap.csv`). CIs unchanged from the earlier
per-draw-fold version (the leakage magnitude was negligible), confirming the result is robust.

**Verdict: the signal remains PREDICTIVE of success, but its contribution BEYOND prompt length is NOT
significant at n=44.** Two facts, stated honestly:
1. **Predictive:** after removing the linear input-length effect the projection still separates
   success/failure at descriptive AUC ≈ 0.74–0.78 (above chance), and the mean out-of-fold gain of
   {projection+length} over {length} is positive at every candidate cell (+0.03 to +0.06).
2. **But not length-independent at this n:** the goal-clustered bootstrap 95% CI on that gain **includes
   0 at every cell** (P(gain>0) = 0.68–0.84). Prompt length is itself a strong success predictor here
   (length-only AUC 0.827), and we **cannot conclude at n=44 that the residual-stream direction adds
   predictive signal beyond length**. The earlier "+0.02–0.06, real" phrasing overclaimed; the gain is
   consistent in sign but within sampling noise.

**Consequence for advancing.** The *predictive* confound is genuinely ambiguous at dev-set scale
(§24.1: dev results are exploratory). The **decisive test is causal (Phase 7)**: an activation-addition
intervention holds the *prompt fixed* (hence input length fixed) and perturbs only the residual-stream
direction, so it is **immune to the length confound** that clouds the predictive analysis. That is the
scientific reason to proceed to Phase 7 rather than to keep refining the predictive number. Candidate
direction: `prefill_last` L13–16 (generation-length-immune) and/or `think_content_1` L20.

## 4. Phase-6 decision gate (§10)
A signal advances to Phase 7 (§11 causal validation) only if it: (a) predicts success not presence;
(b) generalizes to held-out behaviors; (c) appears before the final answer; (d) survives basic
confound controls.

| Criterion | Verdict | Evidence |
|---|---|---|
| (a) success not presence | **PASS** | C-vs-D is success/fail within attack-present; control F-vs-G (presence) is weaker early |
| (b) generalizes to held-out behaviors | **PASS** | grouped LOGO out-of-fold AUC ≈0.90 across 22 goals |
| (c) before the final answer | **PASS** | strongest cells are `prefill_last`/`think_content_1`/`endofthink`, all pre-answer |
| (d) survives confound controls | **QUALIFIED** | remains predictive (residualized ≈0.75); but the contribution beyond prompt length is not significant at n=44 (bootstrap 95% CI on OOF gain includes 0; P(gain>0)=0.68–0.84). Prompt length itself predicts success (AUC 0.827). |

**Gate status: (a)(b)(c) PASS, (d) QUALIFIED.** The early residual-stream state is strongly
success-predictive (raw LOGO AUC ≈0.90), generalizes across held-out goals, and is pre-answer — but at
dev-set scale (n=44) we cannot separate the direction's predictive value from a prompt-length confound.
Rather than treat this as a hard block, we advance to Phase 7 because **causal intervention is immune to
the length confound**: adding/subtracting the direction holds the prompt (and its length) fixed and
perturbs only the residual stream, directly testing mechanistic responsibility (§11.5) — the question
the predictive confound cannot answer. Candidate direction: the Fisher success direction at
**`prefill_last` L13–16** (earliest, generation-length-immune) and/or **`think_content_1` L20**. If the
causal test is negative, §11 gate treats the signal as a detector only (Gate 3 "No" branch, §25) and we
do not build it into the main mechanistic objective.

## 5. Provenance
- Dataset: `docs/MECHANISTIC_DATASET_CARD.md`; tensors `outputs/phase5_mechanistic/extraction/`.
- Labels: `outputs/phase5_mechanistic/phase6_scores.jsonl` (StrongREJECT on AE generations, job 674377).
- Code: `scripts/phase6_signal_search.py` (per-position finite mask; NaN-safe),
  `scripts/phase6_prepare_scores.py` (unique-identity prep; §22 traceable),
  `slurm_scripts/run_phase6_signal.slurm`.
- Results: `outputs/phase5_mechanistic/phase6_CvsD_auc.csv` (core), `phase6_FvsG_auc.csv` (control).

## 6. §10.1-D Attention-allocation signal — converges on the SAME length confound
The residual direction being non-causal (Phase 7) motivated testing the plan's alternative signal family
(§10.1-D, attention). Two findings:

**Span-based attention is untestable for this attack.** The CoT-Hijacking attack does NOT quote the
harmful goal — it abstractly encodes it into the puzzle scaffold (46/48 prompts have no locatable goal
span), so "attention diverted away from the harmful span" cannot be measured. → pivoted to span-free
metrics (`scripts/phase6_attention_signal.py`, eager-attention prompt forward, held-out n=48).

**Span-free attention (entropy / max-concentration) predicts success — but is length-confounded.**
`outputs/phase7scale_qwen3_cot_heldout25/attention_signal.csv`:
- `attn_maxconc` (attention concentration) at the last prompt tokens → success: **raw AUC 0.739,
  grouped-LOGO AUC 0.739** (mid-layers ~L22–30); `attn_entropy` inversely (early-layer AUC ~0.25).
  Direction: **successful attacks have MORE CONCENTRATED (less diffuse) attention** — the *opposite* of
  the naive "hijacking scatters attention to the puzzle" hypothesis.
- **But `corr(maxconc, seq_len) = −0.79`** and length itself predicts success (seq_len AUC 0.28 →
  **shorter attack prompts succeed**). Length-residualizing maxconc drops it **0.739 → 0.632**, and the
  goal-clustered bootstrap on the out-of-fold gain of {maxconc+length} over {length} is **−0.007,
  95% CI [−0.10, +0.29], P(gain>0)=0.43** (same rigor as the residual signal §3) — i.e. attention
  concentration adds **NO significant signal beyond length**; its 0.74 raw AUC is entirely length.

**Unified conclusion (closes the §10/§11 mechanism search).** Both candidate signal families converge
on the SAME confound: the residual success direction (AUC ~0.90) AND attention concentration (0.74) are
largely **downstream proxies of prompt length**. Shorter CoT-Hijacking attack prompts succeed more, and
they carry both more concentrated attention and a distinguishable residual state — length is the common
cause. Neither family demonstrates a length-independent success *mechanism*: the residual direction is
non-causal (Phase 7, all layers+timings) and its predictive gain-beyond-length is n.s. (§3, replicated
held-out); the attention signal is predictive but ~2/3 of it is length (0.74→0.63 residualized). The
honest mechanistic story is **"CoT-Hijacking success on Qwen3 is substantially a function of attack-prompt
length, with internal signals as length correlates, not independent mechanisms."** (Exploratory, n=48;
the bootstrap-CI on the attention gain-over-length is now DONE — gain −0.007, CI ∋ 0, P+=0.43 — so the
attention family, like the residual family, has no significant length-independent component. Both
mechanism-family confounds are complete at the same rigor.)
