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

## 6. The open experiment: λ (in flight)

Gate E's negative carries a caveat the sprint could not remove in time. At the published
**λ = 0.25**, the refusal term is **0.370 % mean / 1.495 % max** of the `total_loss` GCG's
candidate selection actually minimizes (post-audit corrected value; the first pass understated
it ~14× by reading the legacy position). Candidates are chosen overwhelmingly on task loss.

So **Gate E's negative means "the position fix alone does not rescue the objective", NOT "a
mechanism-weighted token objective cannot work."** A λ at which the mechanism term carries real
weight had never been run — not by this sprint and not by the published work.

It is running now: **λ = 10 × {mechanism, random} × seeds {42, 43, 44}**. Early (step-matched
k = 29/200, **all 3 seeds**, diagnostic only): the mechanism term reaches **~24 % (mean, full 200-step run)** of the
selection loss and drives the projection **past zero in all three seeds** (λ = 0.25 never did in
a full 200 steps) — **but the mechanism arm makes 1.45×–3.02× less task-loss progress** than its
matched random arm, 3/3 sign-consistent.

*Statistic is best-so-far task loss; `task_loss` is non-monotonic (GCG selects on total loss,
~40 % up-steps) and single-endpoint readings of it proved unstable — see execution log 12:42.*

**Pre-registered reading:**
* **The internal-target number gets no verdict.** Single-seed quantities of that type produced
  this sprint's one retraction (§7). Only **ΔASR consistent across all 3 seeds** is evidence.
* **If ASR rises**: Gate E's negative was a λ artifact, and the strong discrete claim must be
  weakened to "at the λ the literature uses."
* **If ASR does not rise while task loss degrades**: the result is the more general one — **no
  λ both preserves the attack and gives the mechanism meaningful weight.** That is a structural
  statement about this objective family, stronger than a negative at any single λ.

That the two arms already diverge in *this* way is consistent with Gate C rather than
independent of it: the refusal direction is *reachable*, so the optimizer profitably spends
budget moving it; the random direction is not, so its λ term yields little gradient and the
optimizer defaults to the task loss. The reachability asymmetry showing up in optimizer
behaviour.

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
