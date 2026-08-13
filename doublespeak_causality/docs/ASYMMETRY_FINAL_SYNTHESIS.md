# ASYMMETRY SPRINT — FINAL SYNTHESIS

*Deliverable §15.9. Written 2026-08-12. Sources every number to a run directory or an execution-log entry.*
*One experiment (the λ = 10 probe) is in flight; §6 states its reading rule and both outcomes in advance.*

---

## 0. The question the sprint was built to answer

The program had reached a puzzle. A linear refusal direction in Llama-3.1-8B is **causal in
activation space** — ablating it raises attack success, and it is the locus the whole prior arc
converged on. Yet **GCG suffixes optimized toward that same direction failed**, performing like
suffixes optimized toward a random direction. Two explanations were live:

* **H1 — reachability.** The direction is simply not reachable from input tokens: whatever the
  suffix does, it cannot move that coordinate. The failure would be geometric.
* **H2′ — optimizability.** The direction *is* reachable, but **discrete** search cannot find
  the tokens that reach it. The failure would be about the optimizer, not the geometry.

These have opposite implications for interpretability-guided security. Under H1, internal
directions are the wrong handle for input-space attacks. Under H2′, they are the right handle
and the discrete optimizer is the bottleneck.

**The sprint's result: H1 is rejected, H2′ is supported, and we measured the quantity that
draws the boundary.**

---

## 1. Headline

> The refusal direction is **unusually easy** to reach from input tokens — 4.7× a
> covariance-matched control. **Continuous** input optimization exploits this to jailbreak at
> **ASR 0.784 vs 0.153** dose-matched control. **Discrete** optimization toward the *same
> direction* gains **+0.009 ΔASR**, sign-unstable and below the judge's own noise floor. The
> medium, not the mechanism, is what fails.

Two measured causes of the discrete failure:
1. the **first-order surrogate collapses before one-token step size** (r = 0.84 at ε = 0.1 →
   ≈ 0 at ε = 1.0), and
2. a **perfect solution inside the token simplex retains 5.7 %** of its effect once rounded to
   real tokens.

---

## 2. Gate-by-gate outcomes

| gate | question | verdict | key numbers |
|---|---|---|---|
| **A** | is the published token objective correctly configured? | **NEGATIVE — defect found** | read a fixed absolute index from `train_tasks[0]`: correct for **1 of 40** prompts, silently out-of-range for another, 5 template tokens from where the axis was fitted |
| **B** | is the linear surrogate valid at token scale? | **NEGATIVE (Llama)** | r 0.84 (ε=0.1) → **−0.002 / −0.324** (ε=1.0); *worse* than a matched null |
| **C** | is the direction reachable from suffix tokens? | **POSITIVE — strongly** | ‖Jᵀv‖ **4.71× / 4.91×** (train/test) the corrected covariance-matched control, pct **0.990**; **14.1×/14.9×** isotropic |
| **D** | does continuous input control work, and specifically? | **POSITIVE** | **ASR 0.784 vs 0.153**, mean ΔASR **+0.631**, 3 seeds, **0 sign flips**, all **p < 1e-4** |
| **E** | does mechanism-derived *token* optimization work? | **NEGATIVE, and unstable** | corrected mean ΔASR **+0.009**, legacy **+0.018**; both sign-unstable across seeds; below the ±0.03–0.08 judge floor |
| **F** | does the causal locus generalize across concepts? | **POSITIVE for the actuator** | refusal ablation raises ASR on **5/5** pairs, median specific ΔASR **+0.414**, **4/5** significant after Holm |
| **E′** | does removing the UNIVERSALITY constraint rescue it? (§7.5, per Mahmood) | **NEGATIVE behaviourally, POSITIVE mechanistically** | per-prompt ΔASR sign-inconsistent at both budgets (0/3 significant); projection **3/3 consistent**, mean **−0.354**, Holm-surviving in one |
| **G** | does a mechanism-derived defense follow? | **NEGATIVE (honest)** | on test **no arm** reduces ASR; on train the gates' over-refusal saving is **matched by Bernoulli and shuffled controls** |

### What replicates beyond the primary setting
* **Gate C** replicates on **Phi-4-mini-reasoning** (5.56×, pct 1.000) and under **4-bit NF4**
  quantization (13.25×, pct 1.000). The reachability asymmetry is not a Llama artifact and not
  a bf16 artifact.
* **Gate B** does **not** fully replicate. On Phi the surrogate degrades substantially but does
  **not** collapse (0.535→0.214 train, 0.567→0.125 test). So H2′'s **qualitative core** — most
  surrogate validity is lost before one-token step size — holds in both families, while its
  **sharp form** — the mechanism ends up worse-predicted than a matched null — is
  **Llama-only.** This is stated in the paper body, not buried in limitations.

---

## 3. The three-capability picture

The sprint's organizing claim is that these are three different capabilities with three
different difficulties, and the field tends to conflate them:

| capability | works? | evidence |
|---|---|---|
| **intervene** on the direction in activation space | **yes** | Gate F, 5/5 pairs |
| **steer** it from the input, continuously | **yes** | Gate D, ΔASR +0.631 |
| **optimize discrete tokens** toward it | **no** | Gate E, +0.009, sign-unstable |

The first two working is what makes the third's failure informative. If the direction were not
reachable, "GCG failed" would say nothing about optimizers. Because it *is* reachable — and
demonstrably exploitable by a continuous optimizer with the *same* objective on the *same*
coordinate — the discrete failure isolates the discreteness itself.

---

## 4. Methodological findings that stand on their own

Three measurement hazards were found and fixed, each general enough to matter outside this
paper:

1. **A representation objective reading one absolute token index.** Taken from the first
   training example; correct for 1/40 prompts, silently contributing zero for another, and
   5 template tokens from the position where the axis was fitted and causally validated. It
   produced a published negative. **The corrected re-run changed the behavioural result by
   +0.009 vs +0.018 — i.e. essentially nothing** — which is itself the finding: the defect was
   a confound, not the cause.
2. **Two ASR thresholds (0.25 / 0.5) reported under one name.** Recomputable from stored
   continuous scores; conclusion-neutral here (27 contrasts, **0 sign flips**), but only
   because it was checked.
3. **A judge that flips ~3.4 % of labels between runs at `temperature = 0`**, giving
   **±0.03–0.08** on ASR at n = 37. **This is larger than several previously reported effects
   in this program, including the +0.018 it retired.** Any n≈37 ASR paper without a measured
   judge noise floor is reporting effects it cannot distinguish from resampling.

A fourth, from control design: **the naive covariance-matched random control is rank-1
degenerate** — E[pairwise |cos|] of 0.97–0.998, i.e. ~1 effective direction rather than 100,
because the activation covariance is dominated by one mode. Dropping the top components gives
mean |cos| 0.094 and moved the headline Gate-C ratio from an inflated 6.74× to **4.71×**. Anyone
building an "in-distribution random" control in activation space will hit this.

---

## 5. What we did NOT establish (stated plainly)

* **No cross-family H2′.** The sharp form is Llama-only (§2).
* **No defense.** Gate G is a clean negative; the mechanism did not yield a usable detector.
* **No generality for the dissociation.** Concept-circuit ablation is null everywhere, **but
  only 1 of 5 pairs had enough attack headroom for that null to mean anything.** We claim
  generality for the *actuator* (refusal) and explicitly **not** for the representation ≠
  behavior dissociation.
* **No scope-matched activation arm.** The activation intervention is all-position/all-layer
  while the soft prompt is 16 input positions, so the "continuous < activation" ordering is not
  budget-matched. Recorded as NOT RUN with reason.
* **The optimal continuous dose was read on test** and is exploratory, not a locked estimate.
* **One base point** for the reachability geometry.

---

## 6. The λ probe — RESOLVED: the negative survives a meaningful λ

Gate E's negative carried one caveat the sprint had to remove. At the published **λ = 0.25** the
refusal term is only **0.370 % mean / 1.495 % max** of the `total_loss` GCG's candidate selection
minimizes, so the negative could only mean *"the position fix alone does not rescue the
objective"*, **not** *"a mechanism-weighted token objective cannot work."*

**That probe is now run at λ = 10 (≈40× published), 3 seeds, and the caveat is closed.**

| seed | mechanism | matched random | ΔASR | exact McNemar p |
|---|---|---|---|---|
| 42 | 0.6757 | 0.0541 | **+0.6216** | 1.55e-06 |
| **43** | 0.1081 | 0.2703 | **−0.1622** | 0.109 |
| 44 | 0.5405 | 0.3514 | **+0.1892** | 0.065 |

**Sign consistency 2/3 → FAILS. Not a Gate-E positive. The negative STANDS**, and is now stronger
than the one it replaces:

* **The objective works internally.** At λ=10 the mechanism term carries **24–34 %** of the
  selection loss and drives the held-out projection **past zero in all three seeds**. Behaviour
  still does not follow stably.
* **The instability is real, not judge noise.** All three |ΔASR| **exceed** the ±0.03–0.08 judge
  floor yet disagree in sign.
* **ΔASR alone would have misled.** The random arms span **0.054–0.351 (6.5×)**; seed 42's +0.622
  owes as much to a weak random arm as to a strong mechanism arm.

**Do not quote the mean (+0.216).** The range spans −0.162 to +0.622; the mean of three seeds that
disagree in sign estimates nothing.

**Consequence for the paper:** §5.2's explanation stands, and §5.3's alternative ("the discrete
negative was substantially an implementation artifact") is **ruled out on two independent
grounds** — the position fix changed nothing (+0.009 vs +0.018), and a 40× λ increase does not
produce a seed-stable gain.

## 6b. §7.5 — per-prompt vs universal (added mid-sprint, per Mahmood)

**The question.** Our token-space negative is a **universal** suffix result. A universal failure
is consistent with *two* explanations the universal setting cannot separate: the objective is bad
(**H3**), or the direction is reachable only through **prompt-specific** token moves (**H1/H4 +
§5.5**). A per-prompt attack is easier, is a legitimate threat model, and isolates the objective
question from the universality confound.

**Design.** One suffix optimized **per prompt** on the 37 frozen test prompts; 3 arms (vanilla,
mechanism, matched random) × 3 seeds; **two budgets** — full (200 steps/prompt) and
**compute-matched** (~5 steps/prompt, matched to the universal arm's total).

**Result — the two endpoints dissociate.**
| endpoint (full budget) | per seed | sign | significance |
|---|---|---|---|
| projection (internal target) | −0.198 / −0.450 / −0.415 | **3/3 consistent**, mean **−0.354** | 1/3, Holm-surviving |
| behaviour (ΔASR, graded) | −0.003 / +0.095 / +0.024 | **inconsistent** | 0/3 |

> **The mechanism objective moves its intended coordinate consistently further than a matched
> random direction; the behaviour does not follow.**

This is **a cleaner instance of representation ≠ behaviour than §3's** — identical optimizer,
budget and prompts, differing only in which direction the objective names — and it **rules out
"the objective is inert."** The failure sits **downstream of the representation**.

**Answer to the question §7.5 was added for: NO.** Three independent endpoints agree the universal
negative is *not* a universality/prompt-specificity failure:
1. no reliable per-prompt behavioural advantage at either budget;
2. per-prompt suffixes **transfer** (off-diagonal ASR 0.173–0.200 ≥ the universal arm's own
   held-out 0.162), and their specificity is **matched by a random direction**;
3. the projection moves — so the objective is not inert.

**A methodological result that outlives it: compute dominates direction.** The matched-**random**
arm alone gains **+0.216 ASR** from 5→200 steps/prompt, larger than every direction effect in the
sprint. Had §7.5 been run only at full budget — the obvious way — "per-prompt beats universal"
would have followed, produced entirely by compute, using a random direction. The compute-matched
arm was added pre-registration on this exact reasoning.

---

## 7. Process record — the sprint's own errors

Kept because a synthesis that reports only its successes is not a record.

| error | consequence | fix |
|---|---|---|
| **Published a Gate-E clause-(ii) POSITIVE on one seed (08:52)** | **RETRACTED 10:05** when seed 43 reversed it; 3 seeds show it unstable in *both* configurations | I had written the warning against exactly this 15 minutes earlier and published anyway. **The sprint's main judgment error.** |
| Read partial `raw.jsonl` from a running job | published a Gate-F verdict on incomplete data | withdrew it; aggregator now **requires `DONE.json`** |
| Claimed Phi Gate-B ordering "inverts" | based on the train split alone | retracted — unstable across splits |
| Covariance control degenerate | headline ratio inflated 6.74× | `--actcov-drop-top`; corrected to **4.71×** |
| λ diagnostic read at the legacy position (audit BUG A) | understated mechanism weight **~14×**; 900× extrapolation was wrong | fixed; logging-only, no resubmission needed |
| New config field changed `config_hash` of 286 existing runs (audit BUG B) | `_load_checkpoint` would **raise** on replay | `_HASH_BACKCOMPAT_DEFAULTS`; 34 pairs verified to agree |
| `LAMTAG` ignored `LAMBDA_C`; `ENVIRONMENT.json` overwritten before the guard (BUG C) | provenance loss / run-ID collision | fixed |

The pattern in the two retractions is the same: **a single-seed or single-split quantity was
promoted to a verdict.** Every gate in §2 that survived did so on ≥3 seeds or both splits. That
is the rule the λ probe in §6 is bound by.

---

## 8. Bottom line

Interpretability gave a genuine causal handle. It survives changes of concept (5/5 pairs),
model family, and numerical precision, and a continuous optimizer turns it into a working
attack at ASR 0.78. It still does not become a discrete attack, and it did not become a
defense.

**The gap is not that the mechanism is wrong. It is that the optimizers red-teaming actually
runs are discrete, and the surrogate they rely on is already invalid at the size of one token.**

---

## Artifact index

| deliverable | content |
|---|---|
| `ASYMMETRY_SPRINT_EXECUTION_LOG.md` | append-only chronological record (authoritative for supersessions) |
| `ASYMMETRY_GAP_MATRIX.md` | Phase 0 audit, defects D1/D2 |
| `TOKEN_REACHABILITY_ANALYSIS.md` | Gate B/C, ‖Jᵀv‖, ε-scan, control families |
| `CONTINUOUS_VS_DISCRETE.md` | Gate D, soft prompts, rounding probe |
| `ADVANCED_OPTIMIZER_RESULTS.md` | Gate E, position-corrected arms, λ probe |
| `MULTICONCEPT_CAUSAL_GENERALIZATION.md` | Gate F, 5 concept pairs |
| `TWO_SIGNAL_DEFENSE.md` | Gate G, defense negative + controls |
| `UPDATED_PAPER_CLAIM_TABLE.md` | claim → evidence mapping |
| `PAPER_OUTLINE_V2.md` | paper structure |
| **this file** | cross-gate synthesis |
| `RESEARCH_HANDOFF_V2.md` | orientation for a fresh researcher |

Figures A, B, B2, C, D, E in `outputs/asym_figures/`.
