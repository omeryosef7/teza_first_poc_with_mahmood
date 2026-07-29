# GCG / MAC Comparison — Temporal (mechanistic) objective vs standard optimization

**Deliverable (plan §23, Workstream F / Phase 6, Level 5).** Design + protocol + status for testing
whether a mechanism-derived **temporal objective** (benign-early / harmful-late) improves an
optimization-based attack over standard GCG/MAC. **Status: DESIGNED; execution in progress (large build,
long jobs).** The predictive foundation (Level 4) is established: the early-benign signature predicts
held-out jailbreak (AUC 0.67) — see `MECHANISTIC_OBJECTIVE.md`. This phase tests whether *optimizing* it
**improves held-out behavioral ASR** (predictive ≠ optimizable-with-gain).

---

## 1. Existing infrastructure to reuse (Phase-6 audit, verified)
- `poc_stage_gcg_early/gcg_optimizer.py::run_optimization` — full GCG (coordinate gradients, candidate
  sampling/eval, checkpoint, pareto). CLI `run_optimization.py` exposes **`--lambda-repr`, `--repr-layers`,
  `--repr-metric {cosine,l2}`, `--reference-cache-dir`, `--lambda-refusal-dir`** → it already optimizes a
  suffix so candidate activations MATCH a **reference cache** at chosen layers.
- `objectives.py::repr_loss(candidate_hs, reference_hs{layer:{pos:tensor}}, ...)` + `ObjectiveWeights`
  (task + repr + kl + refusal). `build_reference_cache.py` builds the `{task_id}_{key}.pt` caches
  (`hidden_states: {layer:{pos:tensor}}`). `reinforce_mac.py::reinforce_mac_optimize` = MAC.
- `evaluate_optimized_suffixes.py` + `evaluate_cross_model_transfer.py` = held-out ASR + transfer.
- Uses `--no-filter-cand` (memory: filter_cand silently kills BPE optimization).

## 2. Temporal objective → existing repr_loss (the key mapping)
The temporal objective J = late_harmful_align − λ·early_harmful_align is realized as a **layer-weighted
`repr_loss` against a MIXED reference cache**:
- **early layers → BENIGN reference reps** (the Neutral-codeword activations) — pushes the candidate to
  look benign early (minimize early harmful alignment);
- **late layers → HARMFUL reference reps** (the Direct-concept activations) — pushes harmful meaning late.
Minimizing repr_loss to this mixed reference = "benign-early, harmful-late". Load-bearing term (per
Level 4): the **early-suppression** (benign-early) part; the late term alone is inert.

## 3. Methods compared (matched candidate budget, plan §10.2)
- **A. Original Doublespeak** (no optimization) — the current benchmark attack.
- **B. Random search** — random codeword/demo-order at matched budget.
- **C. Standard GCG** — `--lambda-repr 0`, task_loss on a harmful target prefix.
- **D. Standard MAC** — same output objective, momentum.
- **E. Temporal-GCG** — `--lambda-repr>0` against the mixed early-benign/late-harmful reference.
- **F. Temporal-MAC**; **G. Combined** (temporal + task + refusal-suppression).
Optimize over (staged, §10.3): codeword → demo selection/order → local context → a short suffix. Positions
fixed on dev data. Lexical-leakage filter (must not insert the explicit harmful concept), reported separately.

## 4. Evaluation (plan §10.8) — the criterion
Held-out **behavioral ASR** (StrongReject + refusal-language judge, the corrected pipeline) on held-out
prompts / concepts / codewords, + transfer to a 2nd model, + compute budget (steps, passes, wall-clock),
+ convergence + temporal-objective curve. **Level 5 is met iff Temporal-GCG/MAC > standard GCG/MAC on
held-out ASR under a matched budget.** Objective ablations (§10.9): late-only, early-suppression-only,
benign-early-only, temporal-diff, +task, +refusal.

## 5. Feasibility / status (honest)
- The GCG-early stack is tailored to a prior Qwen3/CoT surrogate study; adapting it to the Doublespeak
  Llama-8B benchmark requires: (a) a Doublespeak manifest in its format, (b) a **mixed reference cache**
  (early-benign / late-harmful) — new capture, (c) GCG runs (long, coordinate descent × N steps) which are
  **preemption-prone** on the current killable partition, (d) ASR eval with the corrected judge.
- This is a multi-iteration build. Running in parallel with the thinking (Phase 7) and cross-model timing
  (Phase 8) tracks per the user's directive; jobs sized/checkpointed for the preemption window.
- **Not yet claimed:** any ASR gain. Level 5 remains open until E/F beat C/D on held-out ASR.

## 6b. RESULT — codeword-selection variant (the feasible Level-5 test, `24`)
On the 6-codeword curated benchmark (Llama-8B, 40 bases × 6 codewords, screened + features via `21`):
selecting the codeword with **minimum early harmful alignment** (the temporal objective) vs random:

| selection | jailbreak rate |
|---|---|
| **temporal (argmin early-align)** | **0.30** |
| random (expected pick) | 0.208 |
| anti (argmax early-align) | 0.225 |

**temporal − random = +0.092 [−0.037, +0.225]** (n=40 bases). **Directionally positive** (temporal beats
both random and the anti-objective), but the **CI crosses 0 → NOT statistically significant.**

Robustness: a leave-one-concept-out **multivariate** predictor for selection gives Δ=+0.067 [−0.046,+0.183]
— no better than univariate early_align (both directional, both NS at n=40). The effect is small and
underpowered, not an artifact of the selection rule. Lever to reach significance: **more N** — a benchmark
expansion to 84 bases (42 concepts) was built, but screening 336 conditions is **infeasible under the
current ~50-min killable-preemption window** (jobs die at ~100 conditions; the screen was cancelled). So
the honest directional-NS verdict stands at n=40. Reaching significance would need either a stable
(non-preempting) allocation for the larger screen or the harder-optimizing full suffix-GCG (designed).

**Honest verdict: Level 5 is NOT cleanly achieved.** The mechanistic objective *improves the attack
directionally* (+9 pp jailbreak rate via codeword selection) — consistent with its *moderate* predictive
power (Level 4 AUC 0.67) — but the improvement is underpowered at n=40. A moderately-predictive objective
yields a moderate, non-significant attack gain. Larger N and/or the harder-optimizing full suffix-GCG (§2–5,
designed) are needed before an ASR-gain claim can be made. Reporting the directional result honestly rather
than over-claiming Level 5.

## 6c. Next concrete steps ✅ ALL DONE (see §6d)
1. ✅ Built the mixed reference cache (early=Neutral reps, late=Direct reps) — `gcg_manifest_bridge.py` +
   two `build_reference_cache` runs + `gcg_mixed_cache.py` (self-tested).
2. ✅ Smoked Temporal-GCG (5 steps) — repr_loss wiring validated (repr_loss=0.4464 logged at step 0).
3. ✅ Ran matched-budget baseline (λ=0) vs temporal (λ>0), 200 steps, on Qwen3; held-out ASR on 13 val bases.

## 6d. FULL Temporal-GCG EXECUTED (Qwen3-14B) — a definitive NEGATIVE (the attack is demonstration-bound)
Full pipeline built + run: Doublespeak→GCG manifest bridge → benign(Neutral)+harmful(Direct) reference
caches → mixed early-benign/late-harmful cache (merge by position order) → `run_optimization` (temporal vs
baseline) → held-out ASR (`25_eval_gcg_asr.py`, same StrongReject+MALICIOUS-first judge).

**Result 1 — the temporal objective is NOT GCG-suffix-optimizable.** `repr_loss` (late-layer cosine distance
of the suffix reps to the harmful Direct reps) **never dropped** across THREE selection configs:
| config | selection | λ_repr | repr_loss first→min→last | task_loss |
|---|---|---|---|---|
| weighted | argmin(task+λ·repr) | 0.3 | 0.446 → 0.446 → 0.565 | 59.6 → 3.8 (chased benign target) |
| lex-tight | argmin(repr) s.t. task≤best+0.01 | 1.0 | 0.480 → 0.463 → 0.535 | 63.4 → 16.4 |
| lex-wide | argmin(repr) s.t. task≤best+20 | 1.0 | 0.454 → 0.450 → 0.452 (200 steps) | 77.7 → 71.1 (task SACRIFICED, repr still flat) |
Even with maximum slack (lex-wide: the optimizer freely abandons the task target), a 16-token suffix cannot
push the neutralized prompt's late reps to the harmful-concept reps.

**Result 2 — behaviorally it BACKFIRES.** Held-out ASR (13 val bases): temporal 0.0, baseline 0.0, no-suffix
0.077; but the temporal suffix drives **refusal to 0.615** (vs baseline 0.077, none 0.0). Steering toward
harmful-late reps via a raw suffix TRIGGERS the safety check rather than evading it.

**Interpretation — this is a meaningful boundary, not a failed experiment.** It directly confirms the TOCTOU
timing law from the other direction: harmful meaning appended LATE as a raw adversarial suffix is either
caught (→refusal) or fails to install (repr_loss won't drop), whereas the Doublespeak DEMONSTRATIONS smuggle
late-emerging meaning past the early refusal checkpoint. **The Doublespeak attack is demonstration-bound —
it cannot be distilled into a universal GCG suffix.** Coheres with the behavioral sufficiency dissociation
(§2: the transplanted DS state is context-dependent and loses behavioral force). Combined with §6b
(codeword selection gives a directional +9pp but underpowered), the honest Level-5 verdict: **the
mechanism-derived objective yields a directional selection gain but is NOT suffix-optimizable into a stronger
universal attack; the hijack's power lives in the in-context demonstrations.**
