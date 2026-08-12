# RESEARCH_HANDOFF_V2 — Doublespeak Causal-Mechanism Program, after the Asymmetry sprint

*Deliverable §15.9. Written 2026-08-12. Supersedes `RESEARCH_HANDOFF.md` (2026-08-11) for
everything the Asymmetry sprint touched; that file remains correct for the pre-sprint arc
(Q1–Q7) and for background you should still read there.*

---

## 0. How to use this document

Read **§1–§3** to orient (15 min). Read **§4** before you touch any number — it lists the
measurement traps that have already produced retractions in this program. Read **§5** for what
is open. `ASYMMETRY_FINAL_SYNTHESIS.md` is the cross-gate argument; this file is the operating
manual.

**If you only remember one thing:** in this program, *a single-seed or single-split quantity
promoted to a verdict* has caused **every** retraction. Both of them. Do not do it.

---

## 1. What changed from V1

**V1's spine was a negative:** *a refusal direction is causal in activation space but is not a
usable token-space objective.* The Asymmetry sprint found that framing had two load-bearing
weaknesses:

* the token-space objective was **misconfigured** — it read a fixed absolute token index taken
  from `train_tasks[0]`, correct for **1 of 40** prompts and silently out-of-range for another;
* the negative's effect size sat **below the judge's own noise floor**, so it was never
  measurable at n = 37 regardless of mechanism.

**V2's spine is a positive with a mechanism:** *the direction is unusually reachable from the
input, and a continuous optimizer exploits it to jailbreak at ASR 0.78. The failure is specific
to **discrete** search, and we measured why.*

Critically, **fixing the misconfiguration did not change the behavioural result** (+0.009 vs
+0.018, both sign-unstable). The defect was a confound, not the cause — which is what lets the
discrete claim survive its sharpest test.

---

## 2. The result in one table

| capability | works? | evidence |
|---|---|---|
| **intervene** on the direction in activation space | **yes** | 5/5 concept pairs, median specific ΔASR **+0.414** |
| **steer** it from the input, **continuously** | **yes** | **ASR 0.784 vs 0.153**, ΔASR **+0.631**, 3 seeds, 0 sign flips, p < 1e-4 |
| **optimize discrete tokens** toward it | **no** | ΔASR **+0.009**, sign-unstable, below the ±0.03–0.08 judge floor |

Reachability is **not** the blocker: ‖Jᵀv‖ is **4.71×/4.91×** (train/test) a corrected
covariance-matched control at percentile **0.990**, and **14.1×/14.9×** an isotropic one. It
replicates on **Phi-4-mini-reasoning** (5.56×) and under **4-bit NF4** (13.25×).

Two measured causes of the discrete failure:
1. the first-order surrogate **collapses before one-token step size** — r = 0.84 at ε = 0.1,
   ≈ 0 / −0.324 at ε = 1.0 (*worse* than a matched null);
2. a token-**simplex** optimum retains **5.7 %** of its effect after rounding to real tokens,
   landing inside the range of *unoptimized* random suffixes.

**Scope caveat you must carry:** cause (1)'s **sharp form** (mechanism ends up worse-predicted
than a matched null) is **Llama-only**. On Phi the surrogate degrades substantially but does not
collapse (0.535→0.214 train, 0.567→0.125 test). The **qualitative core** — most validity lost
before one-token scale — holds in both families.

---

## 3. New instruments (what to reuse, not rewrite)

All under `doublespeak_causality/scripts/`:

| script | what it gives you |
|---|---|
| `asym_p1_reachability.py` | ‖Jᵀv‖ via batched `autograd.grad`, ε-scan, streaming empirical subspace, **4 control families** (`random`, `actrandom`, `foreign`, `otherlayer`) |
| `asym_p1c_mech_validity_ext.py` | internal-target movement of any suffix on held-out prompts + layer sweep |
| `asym_p2_softprompt.py` | `SoftSuffix`: `free` (L2-budgeted continuous) and `simplex` (softmax-over-vocab, **upper-bounds** any token sequence) + the rounding probe |
| `asym_p4_aggregate.py` | Gate-F aggregation; **requires `DONE.json`** and has a `--min-ds-base` power filter |
| `asym_p5_defense_2signal.py` | 5 conditions × 7 arms from 2 generations |
| `asym_make_figures.py` | Figures A, B, B2, C, D, E |

Config/optimizer changes in `poc_stage_gcg_early/`:
* `config.py`: `refusal_dir_position_mode ∈ {legacy_fixed, per_task_suffix, per_task_decision}`,
  registered in **`_HASH_BACKCOMPAT_DEFAULTS`** so 286 pre-existing runs still replay.
* `gcg_optimizer.py`: `_rd_positions_for(spans)`, per-task position in the gradient loop **and
  at the logging site**.

### Three landmines in that code
1. **Off-by-one.** A direction file named `L{k}` is fitted at `hidden_states[k+1]`. L18 → index
   19. Every direction arm depends on this.
2. **`legacy_fixed` must keep working.** It reproduces the published runs. The range check there
   **warns once**; it must not raise, or replay breaks.
3. **`--no-filter-cand` is required.** `filter_cand=True` silently kills all optimization with
   BPE tokenizers.

---

## 4. Measurement traps — read before trusting any number

1. **The judge flips ~3.4 % of labels between runs at `temperature = 0`** → **±0.03–0.08** on
   ASR at n = 37. **This is larger than several previously reported effects in this program.**
   Any effect below 0.08 at this n is *within noise*, not a result. This retired the published
   +0.018.
2. **Two ASR thresholds (0.25 / 0.5) were reported under one name.** Use **≥ 0.5**. Old numbers
   are recomputable from stored continuous scores; re-checking was conclusion-neutral here
   (27 contrasts, 0 sign flips) — but only because someone checked.
3. **The naive covariance-matched control is rank-1 degenerate.** E[pairwise |cos|] 0.97–0.998
   — ~1 effective direction, not 100, because activation covariance is dominated by one mode.
   Use `--actcov-drop-top`. This inflated the headline Gate-C ratio from 4.71× to 6.74×.
4. **Never read `raw.jsonl` from a running job.** It cost a withdrawn Gate-F verdict; the
   aggregator now requires `DONE.json`.
5. **`wall_time_sec` in `ITERATION_LOG.jsonl` is per-step, not cumulative.** Arms that appear
   to run at different rates are usually just staggered by concurrent weight-load contention
   (~16× penalty when jobs load simultaneously on one node).
6. **Backticks in `git commit -m` under tcsh execute and silently delete a word.** Use a heredoc.

---

## 5. What is open

### 5.1 In flight: the λ probe — **the one caveat on the headline negative**
At the published **λ = 0.25**, the refusal term is only **0.370 % mean / 1.495 % max** of the
`total_loss` GCG's candidate selection minimizes. So the discrete negative means *"the position
fix alone does not rescue the objective"*, **not** *"a mechanism-weighted token objective cannot
work."*

Running: **λ = 10 × {mechanism, random} × seeds {42, 43, 44}.** Early (seed 42, step 27/200,
**diagnostic only**): mechanism term reaches **22.7 %** of the loss and drives the projection
**past zero** (+0.169 → −0.074), **but the task loss nearly stops improving** (moved 4.3 vs the
random arm's 27.9).

**Pre-registered reading — do not deviate:**
* The **internal-target number gets no verdict.** Only **ΔASR consistent across all 3 seeds**
  is evidence.
* **ASR rises** → Gate E's negative was a λ artifact; weaken the discrete claim to "at the λ the
  literature uses."
* **ASR flat while task loss degrades** → the stronger, more general result: **no λ both
  preserves the attack and gives the mechanism meaningful weight.**

Note the corrected diagnostic also made this cheap: ~50 % mechanism weight needs **λ ≈ 34**, not
the λ ≈ 900 estimated from the pre-audit (understated) share.

### 5.2 NOT RUN, with reasons
* **Scope-matched activation arm.** The activation intervention is all-position/all-layer while
  the soft prompt is 16 input positions, so the "continuous < activation" ordering is **not
  budget-matched**. This is the single cleanest missing control.
* **Full λ sweep** {0.25, 5, 50} with task-loss degradation reported alongside ASR.
* **Cross-family H2′** — needs a third family to say whether the sharp form is Llama-specific.

### 5.3 Claims deliberately **not** made
* **No defense.** Gate G is a clean negative: on test no arm reduces ASR, and on train the
  gates' over-refusal saving is **matched by Bernoulli and shuffled-feature controls**.
* **No generality for the representation ≠ behavior dissociation.** Concept-circuit ablation is
  null in all 5 pairs, **but only 1 pair had enough attack headroom for that null to mean
  anything.** Generality is claimed for the **actuator** (refusal) only.
* The optimal continuous dose was **read on test** — exploratory, not a locked estimate.

---

## 6. Suggested next steps, ranked

1. **Finish and read the λ probe** under §5.1's rule. It is the last thing gating the paper's
   central negative.
2. **Run the scope-matched activation arm** (§5.2) — it is the control a reviewer will ask for
   first, and it is cheap relative to what it defends.
3. **Third model family for H2′.** The sprint's honesty about Llama-specificity is currently a
   limitation; one more family converts it into a scope claim.
4. **Raise n or average judges.** With a ±0.03–0.08 floor at n = 37, several open questions in
   this program are simply unmeasurable at current n. This is a cheaper win than any new
   mechanism.
5. **Do not** invest further in the two-signal defense without a new idea; the controls closed
   that route.

---

## 7. Artifact index

| file | content |
|---|---|
| `ASYMMETRY_FINAL_SYNTHESIS.md` | cross-gate argument, gate table, process record |
| `ASYMMETRY_SPRINT_EXECUTION_LOG.md` | **append-only** chronological record; authoritative for supersessions/retractions |
| `ASYMMETRY_GAP_MATRIX.md` | Phase 0 audit, defects D1/D2 |
| `TOKEN_REACHABILITY_ANALYSIS.md` | Gates B/C |
| `CONTINUOUS_VS_DISCRETE.md` | Gate D, soft prompts, rounding probe |
| `ADVANCED_OPTIMIZER_RESULTS.md` | Gate E, position-corrected arms, λ probe |
| `MULTICONCEPT_CAUSAL_GENERALIZATION.md` | Gate F |
| `TWO_SIGNAL_DEFENSE.md` | Gate G |
| `UPDATED_PAPER_CLAIM_TABLE.md` | claim → evidence mapping |
| `PAPER_OUTLINE_V2.md` | paper structure |
| `RESEARCH_HANDOFF.md` | **pre-sprint** arc (Q1–Q7), background, glossary — still current for those |

Figures in `outputs/asym_figures/`. Run directories under `outputs/stage_gcg_full/asym_p3_*`
(⚠ `*_SMOKE3STEP` carries `DO_NOT_SCORE.txt` and matches naive globs).

**Security note for whoever picks this up:** a GitHub personal access token is stored in
plaintext in `.git/config` (embedded in the `origin` URL). It should be rotated; it was left
untouched during the sprint.
