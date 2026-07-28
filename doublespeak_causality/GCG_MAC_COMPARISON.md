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

## 6. Next concrete steps
1. Build the mixed reference cache for a dev set of eligible Doublespeak prompts (early=Neutral reps,
   late=Direct reps) via a Doublespeak-adapted `build_reference_cache`.
2. Smoke Temporal-GCG (few steps, 1 behavior) to validate the objective wiring end-to-end.
3. Matched-budget C vs E on a dev set; then held-out ASR.
