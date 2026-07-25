# Adaptive Detection and Defense Report (Phase 17, §21)

The Phase-7 causal test showed the early success direction is **not a mechanism** (neither sufficient
nor necessary; `docs/CAUSAL_VALIDATION_REPORT.md`). Per §25 Gate-3 "No", the signal's value is
**defensive**: a detector does not need causality, only prediction. This report evaluates the signal as
a **success-vs-failure jailbreak detector** (§21.1) — the honest re-framing of the AUC≈0.90 result.

## §21.1 Prediction target changed
The earlier Qwen3 detector distinguished *attacked vs clean* prompts (attack presence). Per §21.1 the
defensively meaningful target is **successful attack vs failed attack** — the §9 C∪D split
(24 success / 20 fail over 22 goals, StrongREJECT-labelled, `outputs/phase5_mechanistic/phase6_scores.jsonl`).
Detecting *which* attacks will succeed lets a defender intervene selectively.

## §21.3 Detector comparison (grouped leave-one-goal-out)
`scripts/phase17_detector.py` (reuses the §9 loaders + `detector_groupkfold_audit.make_pipe`) →
`outputs/phase17_detect/detector_CvsD.csv`. Three families, grouped LOGO by goal (no behavior in both
train and test), NaN-safe:

| detector | best pre-answer cell | out-of-fold AUC |
|---|---|---|
| Fisher difference-of-means (linear, 1-D — the Phase-6 direction) | think_content_1 L20 | 0.906 |
| Logistic regression (StandardScaler + L2) | endofthink L24 | 0.908 |
| Small MLP (64-hidden) | think_content_2 L28 | **0.923** |

The nonlinear MLP gives a **modest** lift (0.923 vs 0.906) over the linear Fisher threshold; logistic ≈
Fisher. So most of the separability is already linear — a cheap 1-D projection detector is nearly as
good as an MLP.

### Cross-condition generalization (does success-vs-failure detection depend on attack type?)
Same detector, three §9 condition pairs (best pre-answer AUC per family):

| condition pair | n (succ/fail) | fisher | logistic | MLP | file |
|---|---|---|---|---|---|
| **C∪D** (CoT-Hijacking attack) | 44 (24/20) | 0.906 | 0.908 | **0.923** | `detector_CvsD.csv` |
| **F∪G** (optimized-suffix attack) | 40 (10/30) | 0.807 | 0.810 | 0.853 | `detector_FvsG.csv` |
| **A∪B** (clean prompt) | 20 (2/18) | (degenerate) | — | — | `detector_AvsB.csv` |

**Reading:** success-vs-failure is most detectable for the **CoT-Hijacking attacks the signal was built
around (0.92)**, transfers **moderately to optimized-suffix attacks (0.85)**, and is **untestable on
clean prompts** — A∪B has only 2 successes, so its AUC (1.000) is a small-n artifact, not a real
detector (reported for completeness, not as a result). The drop C∪D→F∪G suggests the "success state" is
partly attack-family-specific rather than a single universal success representation — consistent with
the Phase-7 finding that it is a correlate, not a shared mechanism.

## §21.4 Detection timing — best AUC per (position × family)
The defensively critical question: how EARLY can a jailbreak be flagged (before harmful content)?

| position (temporal) | Fisher | logistic | MLP |
|---|---|---|---|
| `prefill_last` (last input token, **pre-generation**) | **L16 0.904** | L32 0.867 | L12 0.890 |
| `startofthink` | L28 0.879 | L24 0.860 | L28 0.860 |
| `think_content_1` (1st thinking token) | L20 0.906 | L32 0.883 | L20 0.921 |
| `think_content_2` | L32 0.902 | L20 0.842 | L28 0.923 |
| `think_content_3` | L16 0.879 | L20 0.863 | L16 0.900 |
| `endofthink` (think→answer transition) | L28 0.899 | L24 0.908 | L24 0.899 |

**Key defensive result:** a jailbreak-success detector reaches **AUC 0.90 at the last INPUT token —
before the model generates a single token** (`prefill_last` L16, Fisher 0.904). Detection stays ≈0.90
through the first thinking tokens and the think→answer transition — i.e. **entirely before harmful
content is emitted** (§21.4's "most valuable detector … before harmful content appears"). This is the
strongest framing of the project's signal: predictive and *early*, even though non-causal.

**Dense full-depth confirmation** (`scripts/phase17_detector.py` over all 40 layers,
`outputs/phase17_detect/detector_CvsD_alllayers.csv`, 834 cells): the coarse-grid picture holds and
sharpens. Best pre-answer detector = **MLP `think_content_1` L19, AUC 0.925**. At the last input token
(`prefill_last`, pre-generation), a **logistic** detector at a late layer reaches **AUC 0.917** (L38;
the coarse [8..32] grid missed this and read 0.867), with Fisher 0.904 (L13). So a purely pre-generation
detector — reading only the prompt's final-token residual — separates will-succeed from will-fail
attacks at ≈0.92. (Same n=44 length caveat below applies.)

## Confound control (§10.4) — ALL detector families, not just Fisher
The success/failure classes differ in prompt length (input 1012 vs 1388 tokens); length alone predicts
success at AUC ≈0.827. `scripts/phase17_confound.py` extends the Phase-6 Fisher-only confound to the
logistic and MLP detectors: it takes each detector's grouped-LOGO out-of-fold probability as a 1-D
signal, residualizes it on input length, and (goal-clustered weighted bootstrap, 1000×) tests whether
{detector-prob + length} beats {length} out-of-fold. (`outputs/phase17_detect/detector_CvsD_confound.csv`;
the residualized/gain columns are *descriptive* — the OOF prob is a fair per-row score but not a fully
nested-CV estimator.)

| detector cell | raw AUC | length-only | residualized | OOF gain over length | gain 95% CI | P(gain>0) |
|---|---|---|---|---|---|---|
| MLP `think_content_1` L19 | 0.925 | 0.827 | 0.723 | **−0.050** | [−0.101, +0.120] | 0.29 |
| logistic `prefill_last` L38 | 0.910 | 0.827 | 0.810 | +0.052 | [−0.086, +0.267] | 0.73 |
| Fisher `think_content_1` L20 | 0.906 | 0.827 | 0.773 | +0.044 | [−0.074, +0.212] | 0.67 |
| Fisher `prefill_last` L16 | 0.904 | 0.827 | 0.758 | +0.044 | [−0.058, +0.218] | 0.75 |

**Verdict: NO detector family adds statistically significant signal beyond prompt length at n=44** —
every gain-over-length 95% CI includes 0, and the MLP's gain is actually *negative* (its extra raw AUC
over the linear detectors does **not** correspond to extra length-independent signal; the nonlinearity
appears to fit length-correlated structure). Residualized AUCs (0.72–0.81) stay above chance, so the
detectors carry *some* non-length signal descriptively, but it is not significant at this n.

### The length confound is CoT-attack-specific, NOT universal (F∪G contrast)
Re-running the same confound on the **suffix-attack** detector (F∪G, `detector_FvsG_confound.csv`)
tells a different story — because optimized-suffix prompts are ~constant length across success/failure,
length there is **near-chance**:

| condition | length-only AUC | best detector raw | residualized | OOF gain | P(gain>0) |
|---|---|---|---|---|---|
| **C∪D** (CoT attack) | **0.827** | mlp 0.925 | 0.72 | ≈0 (−0.05..+0.05) | 0.29–0.75 |
| **F∪G** (suffix attack) | **0.597** | mlp `endofthink` L24 0.853 | **0.85** (≈unchanged) | **+0.30** | **0.96** |

For F∪G the residual-stream detector **retains essentially all its signal after length control**
(0.853 → 0.85) and adds a large amount beyond length (gain +0.30, 95.6% of bootstraps positive; CI
[−0.02, +0.68] grazes 0 only at n=40). **So the suffix-success signal IS a genuine length-independent
internal signal, whereas the CoT-attack-success signal is largely length.**

**Consequence.** The "length-confounded" caveat applies specifically to the **CoT-Hijacking (C∪D)**
setting, where longer attack prompts tend to fail so length itself predicts success. It does **not**
generalize: the F∪G detector is a real length-independent early-warning signal. A deployed detector need
not be mechanism-pure regardless, so the ≈0.90 C∪D pre-generation AUC stays defensively useful — but the
*scientific* claim of a length-independent "success representation" is supported for suffix attacks and
not for CoT attacks.

### ★ Held-out replication (independent n=48) — the CoT-attack length confound is ROBUST
`data/manifests/scale_heldout_25.csv` (25 goals, **0 overlap with dev-25**) → CoT-Hijacking attack
(held-out ASR 0.56) → 48 C∪D examples (28 success / 20 fail) → same extraction/confound
(`outputs/phase7scale_qwen3_cot_heldout25/detector_CvsD_confound.csv`, `phase6_CvsD_auc.csv`):

| cell | dev-25 raw / gain (CI) | **held-out raw / gain (CI)** |
|---|---|---|
| length-only | 0.827 | **0.720** |
| mlp `think_content_1` L19 | 0.925 / −0.05 (∋0) | **0.784 / −0.061 ([−0.14,+0.45])** |
| logistic `prefill_last` L38 | 0.910 / +0.05 (∋0) | **0.754 / −0.007 ([−0.07,+0.25])** |
| fisher `think_content_1` L20 | 0.906 / +0.04 (∋0) | **0.775 / +0.023 ([−0.07,+0.44])** |
| fisher `prefill_last` L16 | 0.904 / +0.04 (∋0) | **0.752 / +0.030 ([−0.06,+0.41])** |

**Two clean replication findings:**
1. **The length confound REPLICATES.** On independent held-out data, every detector's gain-over-length
   95% CI again includes 0 (P(gain>0) 0.56–0.82). No detector family adds significant signal beyond
   prompt length at n=48 either → the confound is robust, not a dev-25 artifact.
2. **The detector transfers only weakly.** Held-out raw AUCs (0.75–0.78) are markedly below dev-25's
   0.90–0.92. Part of this drop is that the held-out set is simply *less length-separable* (length-only
   0.720 vs 0.827), not pure weight overfit — the cleaner cross-dataset metric is the length-independent
   margin (detector-raw − length-only): **0.098 on dev-25 → 0.064 on held-out**, a modest shrinkage, not
   a collapse. The early Fisher signal remains real (held-out pre-answer AUC ~0.85–0.87,
   `phase6_CvsD_auc.csv`) but a bit weaker than dev-25's 0.90.

**Final verdict:** the CoT-attack success detector is a **predictive, early, but substantially
length-driven** signal that does **not** demonstrate a length-independent internal "success
representation" — confirmed on two independent datasets (dev-25 n=44 + held-out n=48). It remains
defensively usable (a deployed detector may exploit length), but the *mechanistic* claim is not
supported. The suffix-attack (F∪G) detector, by contrast, IS length-independent (above).

## §21.2 Adaptive attacks (scoped, not yet run)
An adaptive attacker optimizes `L_attack + β·L_detector` to trade attack success against detectability.
With TROPT/GCG deprioritized (Phase-3 substitution) this needs the discrete optimizer wired to the
detector logit as an auxiliary loss — a follow-up. The relevant question: can an attack stay successful
while moving the residual state off the detector's decision boundary? If yes, the detector is evadable;
if the detector tracks a genuine success prerequisite, evasion should cost attack success.

## §21.5 Defense intervention (constrained by the Phase-7 null)
The plan's suggested defense — detect suspicious state → **increase refusal-direction activation** →
re-run/redirect — is limited here: Phase 7 showed activation-addition along the success direction is not
a causal lever (steering ±3σ did not change ASR). So a *steering*-based defense on THIS direction is not
supported. A viable defense that IS supported: use the early detector (prefill_last, pre-generation) as
a **gate** — when the success-detector fires above threshold, refuse or route to a more conservative
decode — and compare its cost/benefit against simply refusing flagged requests. The detector's early
timing (before generation) makes such gating cheap.

## Reproducibility
Detector AUCs computed with **scikit-learn 1.9.0** (conda env `poc_stage2`). The committed
`scripts/phase17_detector.py` reproduces the reported cells deterministically across re-runs
(fisher/MLP exact; logistic `prefill_last` L38 = 0.9167 on two independent runs). LogisticRegression
uses the default lbfgs solver; AUC tie-ordering can drift ±~0.006 across sklearn versions, so numbers
are reported to 3 decimals and conclusions rely on the ≈0.90 magnitude, not the third decimal.
`detector_CvsD_alllayers.csv` regenerated under the fixed code (no L0 embedding cells; identical
(position,layer) grid across all three families: 273 cells each).

## Deliverable status
- Detector comparison + timing: DONE (`outputs/phase17_detect/detector_CvsD.csv`,
  `detector_CvsD_alllayers.csv`).
- §21.2 adaptive attack, §21.5 quantified defense: scoped as follow-ups.
- Reuse: `scripts/phase17_detector.py`, `slurm_scripts/run_phase17_detector.slurm`,
  `detector_groupkfold_audit.make_pipe`, the §9 dataset.
