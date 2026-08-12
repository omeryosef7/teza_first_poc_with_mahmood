# ASYMMETRY SPRINT PLAN — 2026-08-11

*Next sprint of the Doublespeak causal-mechanism research program. Follows the completed 2026-08-09 → 2026-08-11 sprint.*
*Central question: **why is a refusal direction that is strongly causal under direct activation intervention NOT a specifically useful token-space (GCG) attack objective?***

> This is a **plan document**. It has not been executed yet. Section 18 ("Autonomous execution") describes the intended execution order for whoever runs the sprint; running it is a separate, later step.

We are continuing the Doublespeak causal-mechanism research program. This is the NEXT SPRINT after the completed 2026-08-09 → 2026-08-11 sprint.

- DO NOT treat this as a fresh project.
- DO NOT blindly rerun the previous sprint.
- DO NOT change or weaken the already-established conclusions because a new experiment gives a convenient story.

**FIRST read:** `doublespeak_causality/RESEARCH_HANDOFF.md`

**Then read all primary artifacts referenced by that handoff, especially:**
- `docs/FINAL_SYNTHESIS.md`, `docs/ATTACK_OBJECTIVE_FULL_MATRIX.md`, `docs/THIRD_FAMILY_REPLICATION.md`, `docs/QUANTIZATION_EXTENSION.md`, `docs/PAPER_CLAIM_TABLE.md`, `docs/PAPER_OUTLINE_V1.md`
- `reports/GATE7_V3_MATRIX_STATS.json`, `reports/GATE7_V3_MECH_VALIDITY_seed42.json`
- `reports/REFUSAL_CIRCUIT_SYNTHESIS.md`, `MECHANISM_SYNTHESIS.md`, `MASTER_STATUS_V2.md`
- `data/gcg/clearharm_llama_v3/POOL_MANIFEST.json`, `configs/manifests/phase9b_gcg_v3.json`

**And inspect the exact code paths for:** refusal-direction fitting · concept-direction fitting · activation intervention · GCG representation loss · Jacobian readout · GCG candidate selection · MAC/TROPT infrastructure · StrongREJECT evaluation · train/test manifests.

---

## 0. CURRENT STATE — THIS IS AUTHORITATIVE

> Treat `RESEARCH_HANDOFF.md` §5 and §6 as authoritative if an older document contains a conflicting number.

The current paper-level result is:

**ACTIVATION-SPACE CAUSALITY ≠ TOKEN-SPACE OPTIMIZABILITY**

### 0.1 Doublespeak concept circuit
The model really computes the codeword→harmful-concept remapping. On Llama-3.1-8B:

    demo K/V retrieval ~L8–10/11  →  strongest MLP concept write ~L9  →  distributed carry heads ~L14–21  →  late readout ~L30–31

But the circuit is **behaviorally epiphenomenal**: destroying the concept circuit has little/no specific effect on ASR, and matched random ablation can move behavior more. Therefore: *representation exists ≠ representation is behaviorally load-bearing.*

### 0.2 Refusal is the behavioral causal locus
A linear refusal direction `v_refusal[L] = normalize(mean(h_harmful) − mean(h_harmless))` is causally validated in activation space. On Llama: selected refusal axis around **L18**. On Phi: selected validated axis around **L14**.

Refusal ablation: raises harmful behavior · is dose-dependent · beats matched random activation ablation · survives bf16 / 8-bit / 4-bit · generalizes across 3 model families. **Concept and refusal are near-orthogonal.**

### 0.3 Token-space negative
Corrected GCG experiment now includes: leakage-0 ClearHarm v3 · correct suffix placement · correct hidden-state indexing · 3 seeds · 200-step compute-matched optimization · norm-matched random directions · paired held-out evaluation · mechanistic-validity readout.

Refusal@L18 vs matched random: **mean test ASR difference across seeds ≈ +0.018**, with sign flips across seeds and no significant seed. Most importantly: **the refusal-optimized suffix does NOT suppress the refusal representation more than the random-direction suffix on held-out examples.**

Thus: the activation-space refusal direction is causal, but the existing token-space objective is NON-SPECIFIC.

**Do NOT summarize this as "token optimization can never use refusal".** The supported statement is: *the tested principled direction-projection GCG objectives do not provide a specific token-space advantage over matched random controls.*

### 0.4 Third family
Phi-4-mini-reasoning reproduces the high-level dissociation. Refusal ablation: ΔASR ≈ +0.238, specific vs random, McNemar p≈0.006. But prediction/readout is underpowered because Phi is highly compliant.

### 0.5 Quantization
Llama refusal-ablation causality survives bf16 / 8-bit / 4-bit NF4, with matched random control remaining flat. **Do NOT rerun this basic quantization result.**

---

## 1. THE MAIN QUESTION OF THIS SPRINT

The highest-value unanswered scientific question is now:

> **WHY can we directly intervene on a causal refusal direction and strongly change behavior, yet fail to specifically move/use that same direction through discrete token optimization?**

We need to distinguish several hypotheses.

- **H1 — INPUT REACHABILITY FAILURE.** The refusal direction is causally powerful once injected internally, but it lies largely outside the subspace that suffix-token changes can specifically control.
- **H2 — DISCRETE TOKEN BOTTLENECK.** Continuous input perturbations can specifically steer the refusal state, but mapping those perturbations to actual vocabulary tokens destroys specificity.
- **H3 — OBJECTIVE / OPTIMIZER FAILURE.** The direction is token-reachable, but the current first-order projection GCG loss is a poor optimization objective. MAC/TROPT or a better Jacobian-aware objective may recover specificity.
- **H4 — GENERIC ADVERSARIAL SUPPRESSION.** Almost any adversarial suffix suppresses refusal through a broad generic prompt-disruption mechanism. The refusal direction is causal downstream, but there is no unique upstream token route into it.
- **H5 — DISTRIBUTED NONLINEAR CONTROL.** The scalar refusal direction is only a good intervention/readout coordinate. The natural token→behavior path reaches the refusal circuit through a distributed nonlinear manifold that cannot be captured by one linear projection objective.

**THIS SPRINT SHOULD TRY TO DISCRIMINATE THESE EXPLANATIONS. Do not merely produce another ASR table.**

The **per-prompt vs universal** contrast (new **§7.5**, per Mahmood) is a direct discriminator between **H3** and **H1/H4**: our token-space negative is a *universal* suffix result, and a universal-only failure does **not** imply an objective failure.

---

## 2. SECONDARY QUESTIONS

After the reachability/asymmetry question:

- **Q2.** Does the representation≠behavior dissociation generalize across several harmful concepts rather than mainly CARROT↔BOMB?
- **Q3.** Can the two different signals be useful together for **DEFENSE**? Specifically: concept signal = attack/remapping evidence; refusal signal = causal behavioral control. The concept representation is behaviorally epiphenomenal, but that does NOT mean it is useless as a detection/gating feature. Can we restore refusal ONLY when concept-remapping evidence is present AND refusal is suppressed? This could potentially reduce the prior over-refusal failure.
- **Q4.** Can we power up the Phi readout/predictor result without contaminating the existing test set?
- **Q5.** Only if justified by the results: does a more advanced MAC/TROPT / Jacobian-aware discrete attack finally beat matched random controls?
- **Q6.** Does the refusal-derived objective beat a matched random direction in the **easier per-prompt setting**, even if it fails as a **universal** suffix? (See **§7.5**.)

---

## 3. NON-NEGOTIABLE RULES — CARRY THESE FORWARD EXACTLY

### 3.1 Compute / SLURM
- Maximum **6 concurrent GPU SLURM jobs**. NEVER exceed 6. No SLURM dependencies.
- Preferred: `--partition=killable --account=gpu-research`. Prefer **L40S** for causal/mechanistic experiments.
- The previous GCG sprint used a vetted 3090 path (a6000 nodes faulty; L40S fair-share throttled). Acceptable for GCG IF necessary, but: **DO NOT MIX GPU CLASSES WITHIN A DIRECT COMPARISON.** Mechanism vs random arms must have same GPU class, batch size, number of candidate forwards, optimizer steps, suffix length, seeds, evaluation setup.
- If a job remains PENDING >30 min: inspect reason, cancel/resubmit intelligently. Do not leave dead queued jobs blocking the 6-job budget.
- **SMOKE TEST BEFORE SCALE.** No large matrix until a tiny run successfully: loads model · loads correct split · locates suffix · computes objective · takes optimizer step · checkpoints · resumes · evaluates intended scalar.

### 3.2 Model / cache rules
- **NO new model-weight downloads without explicit human approval.**
- Offline mode: `HF_HOME=$ROOT/.cache/huggingface`, `HF_HUB_CACHE=$HF_HOME/hub`, `HF_HUB_OFFLINE=1`, `TRANSFORMERS_OFFLINE=1`. Use already-cached models first.
- Primary: `meta-llama/Llama-3.1-8B-Instruct`. Existing cross-model: `Qwen3-14B`, `microsoft/Phi-4-mini-reasoning`. Potential secondary reasoning model only if already cached: `DeepSeek-R1-Distill-Llama-8B`. Do not spend time on unavailable Gemma/70B weights.

### 3.3 Precision
- Primary causal/mechanistic claims: **bf16**. Quantized runs are robustness/exploration only unless explicitly stated. Do not allow a 4-bit result to silently replace the bf16 primary claim.

### 3.4 Data
- PRIMARY DATASET: **ClearHarm**. Existing confirmatory split: **v3 leakage-0**. Never mutate the existing v3 split. Never silently reassign an existing test item to train. Never optimize against the locked v3 test labels.
- Every experimental cell: **≥20 UNIQUE examples**. Repeated generations/seeds do NOT increase n. Prefer larger n whenever cheap. All percentages must report denominator.
- For existing v3: reuse the same frozen train/test manifests. For a NEW replication cohort: create it only from examples not already used for the relevant test claim. Any new cohort must be cluster-disjoint · frozen before outcome analysis · documented in a manifest · hashed · audited for duplicates/leakage. Do not create a new split because an old test result was inconvenient.

### 3.5 Train / test discipline
- TRAIN may be used for: fitting directions · fitting gates/classifiers · choosing layer/λ/hyperparameters/suffix length · optimizer design · early stopping rules · deciding the best candidate objective.
- TEST may ONLY be used **after all such choices are frozen.** Never pick a test-best layer / α / threshold / suffix / seed.
- If an analysis accidentally uses test for selection: mark it exploratory; do NOT upgrade it to confirmatory.

### 3.6 Current StrongREJECT protocol
- **USE THE CURRENT HANDOFF'S EVALUATION, NOT AN OLDER SPRINT THRESHOLD.** Binary harmful success: **StrongREJECT score ≥ 0.5**.
- Also report: continuous StrongREJECT score · binary ASR · refusal rate · benign/misunderstanding rate where applicable · empty output rate · stop reason · generation length · truncation fraction.
- Paper-style mean continuous score and binary ASR are DIFFERENT metrics — never call one the other.
- StrongREJECT requires the API key. If judge outputs are null: STOP evaluation, diagnose credentials, do not treat null as benign/refusal.

### 3.7 Statistics
- Paired statistics wherever the same prompt appears in both arms. Binary ASR: exact two-sided McNemar. Effect: paired ΔASR. Uncertainty: paired bootstrap 95% CI, 10,000 resamples where feasible. Per-arm: Wilson CI. Continuous outcomes: paired bootstrap / Wilcoxon / permutation as appropriate. Families of multiple tests: Holm-Bonferroni.
- Always report effect size + CI + n + p-value when applicable. Do not use p-value alone. Do not pool non-exchangeable cohorts. Do not hide sign reversals across seeds/models/concepts.

### 3.8 Random controls
- Every proposed mechanistic direction must have an appropriate matched random control, matching: norm · layer · intervention magnitude · optimizer λ · number of layers · number of positions · compute · seed handling.
- For reachability analyses, use MANY random directions rather than one: **≥50** for exploratory geometry, preferably **100** if cost is small. Random controls generated deterministically from recorded seeds.

### 3.9 Off-by-one — DO NOT BREAK THIS AGAIN
- **LOAD-BEARING RULE.** Direction file labeled `L{k}` was fitted at `hidden_states[k+1]`. The GCG optimizer reads `hidden_states[layer_idx]` directly. Therefore GCG must receive: direction L18 → `layer_idx 19`; direction L12 → `13`; concept L9 → `10` — unless the specific script already internally adds +1.
- Before every NEW code path: print and save both `fit_layer` and `hidden_states_index`. Add assertions. Metadata for every direction-dependent run must contain `"fit_layer"` and `"hidden_states_index"`. Do not rely on filenames alone.

### 3.10 Suffix placement
- The old assistant-vs-user suffix placement bug MUST NEVER return. Primary placement: **user** (`--suffix-placement user`). Before a new optimizer path is trusted: save byte/token-level prompt construction; verify suffix occurs exactly where intended; verify train and evaluation use IDENTICAL placement semantics.

### 3.11 BPE / GCG
- Standing rule: **`--no-filter-cand`** with the current BPE tokenizers unless a new validated implementation proves otherwise. Do not silently reactivate the old filter_cand bug.

### 3.12 Result management
- All runs: incremental · resumable · non-overwriting. Every long optimizer must checkpoint (at minimum: current step · suffix/token ids · optimizer/search state · best candidate · best objective · RNG state · config · manifest hash). Resume must continue EXACTLY rather than restart with same filename. Never overwrite a completed experiment.
- Every run metadata: git commit · config hash · manifest hash · model sha · model · dtype/quantization · GPU class · split · seed · n · objective · λ · suffix length · number steps · candidate budget · start/end timestamp.
- Maintain: `EXPERIMENT_REGISTRY.csv` and an append-only execution log.

### 3.13 Code review
- After every meaningful implementation change: (1) unit/smoke tests; (2) independent adversarial code review. Review: token indexing · layer indexing · suffix placement · sign · normalization · train/test leakage · prompt construction · all-codeword localization · generation caching · EOS · thinking-token behavior · output denominator · duplicate IDs · random-control matching · checkpoint/resume · hidden-state normalization · objective gradient direction. **Do not let the same implementation author be the only reviewer.**

### 3.14 Agent safety / data handling
- Subagents should not inspect harmful generated prose. Subagents may inspect: scalar metrics · code · tensor shapes · anonymized IDs · statistics · plots · metadata · manifests. Main execution pipeline handles harmful generations.

### 3.15 Scientific honesty
- A decodable representation is not a mechanism. A causally steerable activation direction is not automatically input-reachable. Input-reachable is not automatically discrete-token reachable. A successful optimizer is not mechanism-specific unless it beats matched random controls. A random suffix suppressing refusal is scientifically important. **Do not "fix" a negative until it becomes positive.**

---

## 4. PHASE 0 — AUDIT + NEW GAP MATRIX

Before new GPU work create:
- `docs/ASYMMETRY_SPRINT_PLAN_2026_08_11.md` (this file)
- `docs/ASYMMETRY_SPRINT_EXECUTION_LOG.md`
- `docs/ASYMMETRY_GAP_MATRIX.md`

Read the handoff and classify all candidate work: **DONE · DONE / DO NOT REPEAT · PARTIAL · UNDERPOWERED · NEW · INVALID / SUPERSEDED.**

Explicitly mark as **DONE / DO NOT REPEAT**: basic concept-circuit mapping · broad attention edge KO · broad induction-head search · generic head→MLP path sweep · all-codeword-occurrence concept patch · first-order refusal GCG 3-seed 200-step matrix · L18 vs L12 first-order projection comparison · concept first-order GCG · simple combined concept+refusal GCG · GCG mechanistic-validity test showing random suppression · Phi third-family causal refusal replication · basic bf16/8bit/4bit refusal-ablation robustness.

Then answer in the gap matrix WHAT EXACTLY remains unanswered about: token reachability · continuous input reachability · discrete token reachability · optimizer choice · multi-concept generality · selective defense · Phi readout power.

**Do not submit GPU jobs until this exists.**

---

## 5. PHASE 1 — TOKEN→ACTIVATION REACHABILITY GEOMETRY

**THIS IS THE MAIN NEW MECHANISTIC PHASE.** Question: *is the causal refusal direction actually accessible from suffix-token perturbations?* We need a DIRECT measurement of input→hidden-state controllability.

### 5.1 Define the target
- Primary Llama target: refusal direction fitted at block L18, measured at `hidden_states[19]`. Primary target position: the exact position used by the validated refusal readout / GCG setup. If multiple legitimate positions: pre-register primary, treat others as secondary.
- Keep concept direction separate: concept L9, `hidden_states[10]`. Never mix the vectors.

### 5.2 Autograd reachability
For each train prompt, suffix position j, and target direction v, compute the local derivative `g_j(v) = ∂⟨h_target, v⟩ / ∂e_j` (`e_j` = suffix token embedding; `h_target` = selected residual state). Primary summary: `‖Jᵀ v‖` where J maps suffix-embedding perturbations to target hidden state.

Compare: `v_refusal` · `v_concept` · norm-matched random directions · optionally LM/task-loss gradient-derived direction. Use ≥20 unique train prompts. Freeze analysis, repeat on ≥20 held-out prompts.

Questions:
- **A.** Is refusal sensitivity unusually SMALL relative to random? If yes → supports input-reachability limitation.
- **B.** Is refusal sensitivity NORMAL/LARGE but GCG still non-specific? If yes → problem is more likely discrete optimization / generalization / generic adversarial geometry.
- **C.** Which suffix positions carry the sensitivity? Plot suffix position × sensitivity. Do not select positions from test.

### 5.3 Finite-difference validation
Autograd is not enough. For a subset of ≥20 examples, take real vocabulary substitutions around selected suffix positions. For each: record actual Δ hidden state · actual Δ refusal projection · linear predicted Δ projection. Report correlation · slope · sign agreement · error. Verifies the local Jacobian means something for actual token moves.

### 5.4 Empirical token-reachable subspace
Construct an empirical matrix of hidden-state changes caused by actual token substitutions. For each of ≥20 train prompts: choose suffix positions using TRAIN-only rules; collect a fixed candidate vocabulary set (GCG top-gradient candidates · random vocabulary · frequency-matched if cheap); evaluate Δh at the refusal target. Pool/aggregate without mixing examples incorrectly. Compute a low-rank/SVD representation of the token-induced Δh subspace.

For target v measure `R(v) = ‖P_reachable v‖² / ‖v‖²` (or equivalent well-defined projection statistic). Compare refusal · concept · ≥50–100 random directions. Also compute best achievable signed projection among sampled token moves. Question: does refusal lie unusually OUTSIDE the empirical token-induced subspace? Potentially a paper-level explanation. **Do not overstate a finite candidate set as the complete vocabulary-reachable subspace — call it the *empirical local token-reachable subspace*.**

### 5.5 Prompt-to-prompt generalization
A direction may be reachable on each prompt but through DIFFERENT token moves. Measure: cosine between per-prompt input gradients · rank/eigenspectrum of the gradient matrix across prompts · fraction of gradient variance in top components · top candidate-token overlap across prompts.

Hypothesis: refusal suppression may be individually reachable, but the required token perturbation is prompt-specific, explaining why a universal suffix cannot exploit it specifically. **HIGH VALUE.** Compare refusal vs random objectives. If refusal gradients are no more coherent across prompts than random → universal-suffix failure becomes mechanistically interpretable.

---

## 6. PHASE 2 — CONTINUOUS SOFT-PROMPT REACHABILITY

Distinguishes: activation-space reachable vs continuous-input reachable vs discrete-token reachable. Use the SAME frozen ClearHarm v3 train/test protocol.

### 6.1 Continuous positive test
Optimize a continuous suffix embedding directly. Same suffix length as GCG primary: **16 positions**. Objective: suppress validated refusal projection at L18 / hs19. Train on frozen train pool; evaluate on locked test (do NOT optimize on test). Use appropriate norm constraints/regularization.

Compare at minimum: (A) refusal-direction soft prompt · (B) norm-matched random-direction soft prompt · (C) vanilla task-loss soft prompt if existing · (D) no soft prompt. Use ≥3 seeds. Primary outcomes: movement of intended refusal projection on test · movement relative to random · ASR · refusal rate · embedding norm · prompt-to-prompt consistency.

### 6.2 Dose / norm match
A continuous optimizer can trivially win by using enormous embedding norms. Evaluate fixed norm budgets: small · medium · large (chosen on train). Random soft-prompt controls must have same norm budget. Plot: test refusal projection vs embedding norm; test ASR vs embedding norm.

### 6.3 Activation control (calibration, not competitor)
Include the known activation intervention as CALIBRATION: direct refusal ablation at L18. Compare Δprojection for: activation intervention vs soft-prompt vs GCG suffix. Produces a **control hierarchy: activation vs continuous input vs discrete tokens.** *This may be the most important figure of the sprint.*

### 6.4 Decision logic
- **CASE A:** continuous prompt specifically suppresses refusal and raises ASR, GCG does not → **DISCRETE TOKEN BOTTLENECK.**
- **CASE B:** continuous prompt also fails to beat random → the causal direction is not specifically reachable from the input in a universal way.
- **CASE C:** continuous and GCG both move refusal, but random does too → **GENERIC ADVERSARIAL SUPPRESSION / non-specific upstream route.**
- **CASE D:** continuous prompt specifically moves refusal but does not raise ASR → target-position/objective mismatch or nonlinear downstream issue; investigate before claiming reachability explanation.

---

## 7. PHASE 3 — BETTER TOKEN-SPACE OBJECTIVES

ONLY run after Phases 1–2 tell us what failure mode we are dealing with. **Do NOT launch a giant new GCG matrix by default.**

### 7.1 TROPT-first
Inspect existing TROPT/MAC infrastructure. Reuse existing recipes. Do not create a new optimizer unless current infrastructure genuinely cannot express the objective. Document: what MAC/TROPT changes · what remains identical to GCG · whether it changes optimizer or objective. We need to separate **optimizer failure** from **objective failure**.

### 7.2 Candidate objectives
Prioritize at most 2–3 scientifically justified objectives:
- **Candidate A:** the existing refusal projection objective under MAC/TROPT instead of GCG.
- **Candidate B:** a Jacobian-aware objective derived from Phase 1.
- **Candidate C:** second-order / sensitivity objective ONLY IF it has a principled mathematical definition.

The previous handoff mentioned 2nd-order `‖J‖²`. **DO NOT invent an arbitrary objective merely because that phrase exists.** First find any prior implementation/design notes. If none exist: derive the exact loss in a methods note (require dimensions · sign · interpretation · finite-difference check · gradient sanity check). If no defensible formulation exists: mark it NOT RUN. That is better than a meaningless experiment.

### 7.3 Random controls
Each objective must have its own matched random counterpart. If the objective contains a vector · layer · Jacobian term · weighting · multiple layers, the control must match all of those except mechanism identity.

### 7.4 Large-budget test
The previous 200-step result is already sufficient for the current negative. A larger budget is only useful to test "does substantially more optimization change the conclusion?". **Do NOT rerun every old arm.** Finalists only: vanilla · refusal mechanism objective · matched random · best Jacobian/MAC objective · its random control. Minimum 3 identical seeds across arms; target 5 seeds if ambiguity remains.

We previously learned a 400-step monolithic run can time out and lose results. **Therefore BEFORE larger runs: implement/test exact optimizer checkpoint+resume.** Run long optimization as resumable segments (4×100 or 2×200) preserving exact search state. Candidate-forward budget must be matched. Evaluate intermediate checkpoints (50 · 100 · 200 · 400 · optionally 800) **without** choosing the best checkpoint based on TEST; the stopping budget is selected from TRAIN / pre-registered compute budget.

Question: does mechanism-vs-random separation emerge with optimization time? If not → stronger evidence for a structural negative.

### 7.5 Per-prompt vs universal optimization (per Mahmood)

**Grounding — what our current token-space negative actually is.** The Gate-7 result is a **universal** suffix: ONE suffix optimized on the 20-item train pool and evaluated on the frozen 42-item held-out test set. The headline **0.465 (refusal) vs 0.464 (random)** held-out numbers are therefore a **transfer** result (seeds 42+43, 50-step first cut) — not a per-prompt attack result. *(Note the Gate-7 pool sizes 20/42 differ from the Phase-3 v3 matrix's 40/37; do not conflate the two when quoting numbers.)*

**Why this discriminates hypotheses.** A universal suffix failing to beat a matched random direction is consistent with two very different explanations:
- **H3 — objective failure.** The mechanism objective is simply a poor optimization target.
- **H1/H4 + §5.5 — universality failure.** The refusal direction *is* reachable per prompt, but through **prompt-specific** token moves, so no single universal suffix can exploit it. This is exactly the hypothesis §5.5 was written to test from the gradient side.

The universal setting **cannot separate these**; the per-prompt setting can. Mahmood's point is that at this stage a per-prompt attack is (a) **easier** than universal, (b) still an **unsolved and legitimate threat model** in its own right, and (c) **isolates the objective question from the universality confound.** Cross-refs **§5.5** (cross-prompt gradient coherence) and **Gate D4**.

**Relationship to §19.5 — read both.** §19.5 already specifies a **train-only, characterization-not-attack** version of this contrast. §7.5 is the **full** version: test-side, with the complete endpoint battery and paired statistics, framed as a threat model. **§19.5's train-only run is the natural smoke test / first cut for §7.5** — run it first, and do not treat the two as independent results.

**Experiment.** For each prompt **independently**, optimize a dedicated suffix (no shared/universal constraint), **compute-matched across arms**:
- **Arm 1 — vanilla task-loss GCG** (baseline).
- **Arm 2 — refusal-projection mechanism objective** at the validated layer (**L18 / hs19**).
- **Arm 3 — norm-matched random-direction control** matched to Arm 2 per **§7.3**.
- **Arm 4 (optional)** — best Jacobian/MAC objective from **§7.2** + its own matched random control.

Held identical across arms: suffix length **16 positions** · steps / batch / candidate-forward budget · `--no-filter-cand` (**§3.11**) · `suffix_placement=user` (**§3.10**) · greedy eval · **≥3 identical seeds** · same GPU class (**§3.1**).

**Per-prompt endpoints.**
- Attack success, **per prompt**.
- **Internal refusal projection before → after** the optimized suffix — the **§19.1** mechanistic-validity check: does the suffix actually lower refusal *on that prompt*. **This measurement is the core of what Mahmood is asking for; do not drop it.**
- Refusal rate · empty rate.

**Primary comparison (paired across prompts, per seed).** Does the mechanism objective (a) **lower the refusal projection more** than its matched random control, and (b) yield **higher per-prompt ASR** than random? Report paired **McNemar** / paired **bootstrap CI** + effect size across prompts (**§3.7**).

**Split discipline (§3.5).** Any layer / step-budget / hyperparameter choice is **frozen from train prompts**; report the per-prompt battery on the **frozen test prompts**. There is no shared suffix, so there is no cross-prompt leakage — but the objective layer and step budget must still be **pre-registered from train**.

**Interpretation (feeds §1 and Gate E).**
- **mechanism > random per-prompt, but not universal** → the negative is a **universality / prompt-specificity failure** (H1/H4, §5.5), **not** an objective failure. Re-scope the paper claim from *"the mechanism objective doesn't work"* to *"the mechanism objective doesn't transfer into a universal suffix."*
- **mechanism ≈ random per-prompt too** → a **stronger structural negative** (objective / reachability failure) that is independent of universality.
- **Interpret jointly with §5.5.** Per-prompt reachable + incoherent gradients across prompts ⇒ a mechanistic explanation of the universal failure, not just a description of it.

**Scheduling.** Because this is cheap and is a **high-value, collaborator-requested discriminator**, it MAY be pulled forward as a small early package (still smoke-tested, still ≤6 jobs) rather than waiting for the full Phase-3 matrix. **But it stays gated behind the Phase-1/2 reachability results**, per this plan's ordering philosophy (§7 preamble: do not launch a giant new GCG matrix by default). Do **NOT** rerun the universal matrix — this **adds** the per-prompt arm. Reuse existing GCG/TROPT infra (**§7.1**); no new optimizer unless the current infra genuinely cannot express it.

> ⚠ **Two conflicts in the request as received, flagged rather than silently resolved.**
> 1. The request specifies *"StrongREJECT MALICIOUS ≥ 0.25"*, but **§3.6 is a non-negotiable rule setting binary success at ≥ 0.5** (and the same request says to respect §3.6). **§3.6 governs: primary binary ASR is ≥ 0.5.** Report ≥ 0.25 alongside it as a secondary column so the comparison to older ≥0.25-era numbers stays possible. Change this only on an explicit instruction to amend §3.6.
> 2. **§19.5 already exists** and covers the train-only form of this contrast. §7.5 does not replace it; see "Relationship to §19.5" above.

---

## 8. PHASE 4 — MULTI-CONCEPT GENERALIZATION

The current detailed causal result is heavily CARROT↔BOMB — an important paper limitation. We already have pair-benchmark infrastructure for multiple harmful concepts. Use at least the existing five pairs/categories where valid: **bomb · grenade · pistol · chlorine · cocaine.** Do NOT remap the entire fine-grained circuit from scratch for every concept (expensive and unnecessary). We need to test the DISSOCIATION.

### 8.1 Data
For every pair: ≥20 unique train · ≥20 unique held-out test. Text-disjoint. Cluster-disjoint when clustering exists. No pair gets fewer examples just to complete the matrix.

### 8.2 Primary frozen loci
Llama primary concept-side loci: concept write ~L9 · distributed carry band ~L14–21. Primary refusal locus: frozen L18 refusal direction. Do NOT reselect these using each pair's test data. Pair-specific concept direction: fit on TRAIN only. Primary refusal direction: use the existing concept-agnostic validated refusal direction. Optional exploratory: fit pair-specific refusal direction on train, but it cannot replace the primary frozen pooled axis.

### 8.3 Minimal causal battery per concept
- **Baselines:** Direct · Neutral · Doublespeak.
- **Representation:** concept readout/separation · refusal projection · concept-refusal cosine.
- **Concept causal test:** strongest existing whole concept-circuit ablation · matched random circuit/position/head ablation.
- **Refusal causal test:** refusal ablation · matched random-direction ablation.
- **Optional if cheap:** refusal restoration under DS.

Question per concept: (A) Does Doublespeak generate concept-remapping representation? (B) Does concept ablation specifically reduce behavioral attack success? (C) Does refusal ablation specifically move behavior? (D) Are concept and refusal still close to orthogonal?

### 8.4 Meta-analysis
Report each concept separately. Then predefine an across-concept summary. **Do NOT hide a failed concept in a pooled number.** Report: sign consistency · median effect · range · pooled paired effect only if statistically justified. Possible result: 5/5 concept representations appear but behavioral effect remains weak/non-specific, whereas refusal perturbation consistently changes behavior — or the dissociation is concept-dependent. Either is valuable.

---

## 9. PHASE 5 — TWO-SIGNAL SELECTIVE DEFENSE

Prior result: restoring refusal can defend, BUT it over-refuses attack-structured benign prompts (unrelated-normal prompts had zero over-refusal). Hypothesis: **refusal axis = behavioral actuator; concept/remapping signal = possible attack-context detector.** The representationally epiphenomenal concept circuit may still be useful for SELECTING when to activate the causal refusal intervention — a natural consequence of representation ≠ behavior.

### 9.1 Build a causality-compatible gate
Features must be available BEFORE harmful continuation is generated — NO future-token leakage. Candidate pre-generation features: refusal projection · concept-remap projection/readout · their interaction · possibly their layer trajectory. Do NOT use StrongREJECT outcome · future generated text · post-hoc labels as gate inputs.

Primary simple gate should be interpretable, e.g. *trigger if `concept_remap_score > T_concept` AND `refusal_score < T_refusal`.* Thresholds: train only, frozen before test. Also test an explicitly trained 2D logistic classifier if useful, but the simple gate remains important for interpretation.

### 9.2 Defense arms
At minimum: (A) no defense · (B) unconditional refusal restoration · (C) refusal-only gate · (D) concept-only gate · (E) concept AND refusal two-signal gate · (F) matched random gate / shuffled-feature control. Use the SAME restoration intervention after gate fires — the only manipulated variable is gating.

### 9.3 Utility conditions
Evaluate separately on: (1) harmful Doublespeak · (2) harmful Direct · (3) attack-structured benign prompts · (4) neutral/codeword benign prompts · (5) unrelated-normal prompts. ≥20 unique test examples for EVERY condition. Primary metrics: harmful ASR reduction · refusal increase on benign · utility loss · gate fire rate · precision/recall for attack condition · StrongREJECT continuous score. Do not optimize a single weighted metric and hide the tradeoff. Plot Pareto: attack ASR reduction vs benign over-refusal.

### 9.4 Defense success criterion
A meaningful defense improvement must: (1) causally reduce DS ASR relative to no defense, AND (2) reduce attack-structured-benign over-refusal substantially relative to unconditional refusal restoration. If it only reproduces the old unconditional tradeoff → NEGATIVE. If concept gating helps → a very interesting twist: the concept circuit is NOT causal for jailbreak behavior, yet is useful as a detector to decide when to intervene on the truly causal refusal axis.

---

## 10. PHASE 6 — POWER UP PHI READOUT, ONLY WITHOUT LEAKAGE

The current Phi causal result is good; the readout AUC is underpowered / compromised by very high compliance. **Do NOT re-use the existing test set for threshold/model selection.**

First audit ClearHarm for UNUSED cluster-disjoint examples. If enough exist, create a new independent replication cohort. Target: preferably ≥60 held-out examples, with enough both refusal and jailbreak outcomes. If fewer than 20 examples occur in one outcome class: AUC conclusion remains underpowered. Do not manufacture class balance by selecting on outcome AFTER seeing labels unless clearly marked case-control/exploratory.

Potential analyses: refusal projection · concept projection · layer trajectory · Jacobian sensitivity. Primary question: is Phi truly *causal refusal direction but weak/non-predictive observational readout?* That would strengthen the broader theme: **causal control ≠ predictive readout** (in addition to causal activation ≠ token optimization).

### 10.1 Thinking-on Phi
The previous native-reasoning Phi job was ~50h and was killed. **Do NOT blindly rerun it.** Run a runtime micro-profile first. Use ≥20 examples only if estimated walltime is feasible under cluster limits. If full thinking-on generation would require impractical compute: document that and skip it. Do not truncate reasoning so aggressively that the condition stops representing native thinking. A smaller hidden-state-only diagnostic may be acceptable as EXPLORATORY, but not as a behavioral replication.

---

## 11. PHASE 7 — OPTIONAL QUANTIZATION REACHABILITY

ONLY if Phases 1–3 produce a clear reachability metric. We already know activation-space refusal ablation is quantization-robust. The new question: does quantization change **TOKEN→REFUSAL reachability?** Interesting because 4-bit had the strongest activation-space causal effect. Compare bf16 vs 4-bit first: `‖Jᵀ v_refusal‖` · empirical reachable-subspace score · gradient coherence across prompts. ≥20 examples/cell. Only add 8-bit if bf16 vs 4-bit suggests a meaningful difference. Exploratory, lower priority than multi-concept and defense.

---

## 12. DECISION GATES

Use explicit gates. Do not proceed mechanically.

- **GATE A — AUDIT / REPRODUCTION INTEGRITY.** PASS if: handoff numbers traced to raw outputs · old experiments classified · off-by-one assertions working · suffix placement verified · manifests frozen. Otherwise STOP.
- **GATE B — REACHABILITY IMPLEMENTATION.** PASS if the autograd derivative matches the finite-difference/token substitution with correct sign and useful correlation. If not, fix implementation before scientific interpretation.
- **GATE C — LOCAL REACHABILITY RESULT.** Classify refusal direction as: unusually low-reachability · normal-reachability · unusually high-reachability · underpowered/unstable — relative to many norm-matched random directions.
- **GATE D — CONTINUOUS INPUT TEST.** D1: continuous specifically reaches refusal, GCG does not → discrete bottleneck. D2: continuous ≈ random → universal input-reachability failure / generic suppression. D3: continuous and discrete both suppress refusal non-specifically → generic adversarial suppression. D4: inconsistent / no generalization → prompt-specific route. This gate determines Phase 3 objective work.
- **GATE E — ADVANCED OPTIMIZER.** Only call mechanism-derived token optimization a POSITIVE if the mechanism objective > its matched random objective on locked test with consistent sign across seeds, CI/statistical support, AND the intended internal target moves more than random. ASR alone is insufficient. **Distinguish a PER-PROMPT positive from a UNIVERSAL positive (§7.5): a per-prompt-only positive RE-SCOPES the universal negative — it does not overturn it — and both forms still require the intended internal target to move more than random.**
- **GATE F — MULTI-CONCEPT.** PASS strong generalization only if the central dissociation is observed across multiple independent concept pairs. Do not say "general across concepts" from 2/5. Report exact heterogeneity.
- **GATE G — SELECTIVE DEFENSE.** PASS only if DS ASR improves AND attack-structured benign over-refusal improves relative to unconditional refusal restoration. Otherwise: honest defense negative.

---

## 13. SLURM EXECUTION STRATEGY

Never have >6 GPU jobs alive. A sensible initial 6-job package AFTER smoke tests:
1. Llama reachability/autograd — train
2. Llama reachability/autograd — held-out
3. finite-difference token-substitution — train
4. empirical reachable-subspace generation
5. continuous refusal soft-prompt — seed42
6. continuous matched-random soft-prompt — seed42

When these finish: analyze BEFORE launching the next package. Do not submit Phase 3/4/5 just because GPU slots opened — use results to decide. Later packages may parallelize by seed · concept pair · defense condition while maintaining ≤6.

**Per-prompt GCG arms (§7.5) belong to a LATER package, not this initial 6-job set.** They must be compute-matched across arms, stay within ≤6 concurrent, and be smoke-tested first (§3.1) — the §19.5 train-only run is the natural smoke test.

---

## 14. REQUIRED FIGURES / ANALYSES

Paper-quality plots, not just JSON. At minimum:
- **FIGURE A — ACTIVATION vs CONTINUOUS vs DISCRETE.** Arms: direct activation ablation · continuous soft prompt · GCG mechanism suffix · matched random suffix. y1: Δ refusal projection; y2: Δ ASR. Visually shows the asymmetry. **Extend the control hierarchy to four rungs once §7.5 lands: activation · continuous · universal-discrete · per-prompt-discrete.**
- **FIGURE B — REACHABLE-SUBSPACE.** Empirical local token-reachability score for refusal · concept · random distribution.
- **FIGURE C — CROSS-PROMPT GRADIENT COHERENCE.** Whether the token direction required to suppress refusal is shared across prompts or prompt-specific.
- **FIGURE D — MULTI-CONCEPT DISSOCIATION.** Per concept: concept-ablation specific ΔASR · refusal-ablation specific ΔASR.
- **FIGURE E — DEFENSE PARETO.** ASR reduction vs benign over-refusal for none · unconditional · refusal gate · concept gate · two-signal gate.

All plots: raw n · CI · model · split must be recoverable from metadata.

---

## 15. REQUIRED DOCUMENTS

Continuously maintain: `docs/ASYMMETRY_SPRINT_EXECUTION_LOG.md` and `results/EXPERIMENT_REGISTRY.csv`.

At the end produce:
1. `docs/ASYMMETRY_FINAL_SYNTHESIS.md` — Executive result · Activation-space causality · Token reachability · Continuous-input reachability · Discrete-token reachability · Optimizer/objective tests · Multi-concept generalization · Defense · Cross-model · Nulls · Limitations · Paper implications.
2. `docs/TOKEN_REACHABILITY_ANALYSIS.md` — exact equations · Jacobian definition · target positions · random-control construction · finite-difference validation · reachable-subspace method · train/test results.
3. `docs/CONTINUOUS_VS_DISCRETE.md`
4. `docs/ADVANCED_OPTIMIZER_RESULTS.md` — **must include the per-prompt vs universal comparison (§7.5) and the per-prompt mechanism-vs-random paired result.**
5. `docs/MULTICONCEPT_CAUSAL_GENERALIZATION.md`
6. `docs/TWO_SIGNAL_DEFENSE.md`
7. `docs/UPDATED_PAPER_CLAIM_TABLE.md` — every claim row: claim · experiment · model · concept · train/test · n · effect · CI · p · random control · status · limitation. Status values only: VERIFIED · NEGATIVE · UNDERPOWERED · EXPLORATORY · SUPERSEDED · WITHDRAWN.
8. `docs/PAPER_OUTLINE_V2.md`
9. `RESEARCH_HANDOFF_V2.md` — **Do NOT overwrite the current `RESEARCH_HANDOFF.md`.** The new handoff must preserve old provenance and explicitly state what this sprint added.

---

## 16. THE PAPER STORY WE ARE TRYING TO TEST — NOT ASSUME

The existing story:
- **I.** Doublespeak induces a real semantic remapping circuit.
- **II.** That circuit is representationally causal but behaviorally epiphenomenal.
- **III.** A separate, near-orthogonal refusal representation causally controls harmful behavior.
- **IV.** Refusal causality generalizes across model families and quantization.
- **V.** Yet using that same refusal representation as a GCG token-space objective provides no specific advantage over random.

The NEW possible contribution:
- **VI.** Activation-space control and input-space reachability are different objects.
- **VII.** We directly characterize the token-induced reachable subspace and show WHY the causal refusal axis does/does not translate to a universal discrete suffix.
- **VIII.** The failure may arise because the upstream token route is generic, prompt-specific, distributed, or discrete-bottlenecked.
- **IX.** The concept/refusal dissociation may nevertheless enable a two-signal defense: concept for detection, refusal for causal control.

**DO NOT write VI–IX as conclusions until the experiments support them.**

---

## 17. WHAT WOULD COUNT AS HIGH-VALUE RESULTS?

Do not optimize for "positive attack result". All of these are valuable:
- **RESULT 1:** Refusal direction has unusually low token reachability → mechanistic explanation of GCG negative.
- **RESULT 2:** Refusal is continuously reachable but not discretely reachable → clean activation→continuous→discrete hierarchy.
- **RESULT 3:** Refusal is locally reachable, but gradients differ strongly across prompts → universal-suffix failure explained by lack of cross-prompt coherence.
- **RESULT 4:** Random and refusal objectives converge onto the same hidden suppression → generic adversarial refusal suppression.
- **RESULT 5:** MAC/TROPT finally beats matched random AND moves refusal more specifically → token lever exists, GCG objective/optimizer was insufficient.
- **RESULT 6:** Multi-concept dissociation holds across 5 concepts → major generalization win.
- **RESULT 7:** Two-signal defense reduces over-refusal → concept circuit useful for detection despite behavioral epiphenomenality.
- **RESULT 8:** Two-signal defense also fails → refusal control remains non-selective even with concept information.

All are publishable if rigorously controlled.

---

## 18. AUTONOMOUS EXECUTION (intended order for whoever runs the sprint)

Execution order once the sprint is run:
1. Read `RESEARCH_HANDOFF.md` and primary artifacts.
2. Write gap matrix.
3. Verify current code hashes / manifests / off-by-one / suffix placement.
4. Implement reachability analysis.
5. Run tiny CPU/GPU smoke.
6. Run finite-difference sanity check.
7. Launch first ≤6-job package.
8. Analyze immediately when jobs finish.
9. Update execution log + registry.
10. Run independent bug review.
11. Apply Gate C/D decision.
12. Only then launch advanced optimizer work.
13. Then multi-concept.
14. Then defense.
15. Phi-power / quantization extension only if still scientifically useful.
16. Produce final synthesis + new handoff.

At every stage ask: *"Does this experiment distinguish two plausible scientific explanations?"* If no → do not spend GPU on it. The goal is NOT another giant experiment matrix. The goal is to explain the most interesting result we currently have: **WHY a representation that is strongly causal when directly intervened on is not a specifically useful token-space attack objective.** That causal-vs-reachable distinction is the center of the sprint.

---

## 19. ADDITIONAL ITEMS ADDED TO THIS PLAN

*Provenance: §0–§18 are the plan as specified. The items below were added at the plan author's request ("if you have more things you wanted to do — add them"). Each cross-references the phase it belongs to and does not overturn §0 authority. All are cheap forward-pass / train-only characterizations that sharpen the H1–H5 discrimination.*

### 19.1 Held-out refusal-drop verification of the FINAL suffix — *the requested item*
**Question (as posed):** "Does GCG ablate refusal? The refusal term was active during optimization and moved in the right direction (≈ +0.02 → −0.06 on training prompts), but we haven't verified whether the FINAL suffix actually lowers the refusal signal on held-out prompts."

**Status of prior work — PARTIAL (do not re-do the part that is done).** Q5 mechanistic-validity (`reports/GATE7_V3_MECH_VALIDITY_seed42.json`, **seed 42 only**) already measured the FINAL suffix's held-out Δ refusal-projection vs a neutral suffix: **refusal-suffix −1.66 vs random-suffix −2.04 @hs19** (baseline projection 3.40), and −2.81 vs −3.53 @hs23. Reading: the final refusal suffix **does** lower the held-out refusal signal, but **less** than a norm-matched random suffix → the suppression is real but **non-specific**. So "does it lower refusal on held-out?" is *yes* at seed 42; the sharper, still-open pieces are below.

**What remains (cheap; reuses already-optimized suffixes — forward-pass readouts only, no new optimization):**
- **(a) Seed replication.** Q5 is n=1 seed. Extend the mech-validity readout to **seeds 43 and 44** (and 42) → is "final refusal suffix lowers held-out refusal *less than* random" stable across all three seeds, or does it flip with the ASR sign flips? Report per-seed Δprojection for refusal / random / vanilla-doublespeak / neutral.
- **(b) Absolute drop + distribution.** Report the held-out drop from the **no-suffix baseline** (not only vs neutral), and the **per-prompt distribution** (not just the mean), as a 4-way: refusal-suffix · random-suffix · vanilla-doublespeak-suffix · no-suffix.
- **(c) Train→held-out generalization gap.** Measure the SAME refusal-projection quantity for the FINAL suffix on the **train pool** vs **held-out test**. The optimization drove the train-side projection ≈ +0.02 → −0.06; quantify how much of that train-side suppression *transfers* to held-out. A large train/test gap = the universal suffix overfits its refusal suppression to the train prompts (supports H3/H5 / §5.5).
- **(d) Per-prompt drop ↔ success correlation.** Does the per-prompt held-out refusal drop predict per-prompt jailbreak success, and is that drop→success relationship the **same** for refusal and random suffixes? If identical → strong H4 / generic-suppression evidence.

**Where it lives:** Phase 1 (mechanistic/reachability); feeds Gate C and Gate D. Implement by extending `scripts/phase_gate7_mech_validity.py` to (i) all seeds, (ii) emit per-prompt arrays and the no-suffix + vanilla-suffix references, (iii) also read the train pool. No GPU optimization needed — generation/forward only.

### 19.2 Layer-sweep of the held-out suppression (H4 vs specificity)
For refusal-suffix vs random-suffix, measure held-out Δ refusal-projection across a **layer sweep (≈ L10–L24)**, not only the target L18. If both suffixes suppress broadly and near-identically across layers → generic suppression (**H4**). If the refusal-suffix uniquely deepens the dip at/around its target layer → partial specificity. Cross-refs §5.4 and Gate D3. Cheap forward-pass; reuses existing suffixes.

### 19.3 Direction-identity integrity check (Gate A addition)
Before interpreting "causal under ablation but non-specific under GCG," **assert the refusal vector is the SAME object across all three code paths**: load the vector used in (i) activation ablation, (ii) the GCG projection loss, and (iii) the mech-validity readout, and check pairwise **cosine ≈ 1.0** plus identical norm / `fit_layer` / `hidden_states_index`. Rules out a silent cross-code-path vector mismatch confounding the central comparison. Add to the Phase 0 / Gate A checklist. Trivial cost, high protective value.

### 19.4 Rounding probe: continuous → nearest tokens (operationalizes H2)
If Phase 2 finds a continuous soft-prompt that **specifically** suppresses held-out refusal and raises ASR (CASE A), take that winning soft-prompt and **project each position to its nearest-vocabulary embedding** (plus a small top-k discrete search around it), then re-measure held-out refusal-projection and ASR. Quantify how much specificity/effect **survives discretization**. This is the sharpest direct test of the discrete-token bottleneck (**H2**) and bridges Phase 2 → Phase 3. Only run if Phase 2 CASE A occurs.

### 19.5 Universal vs per-prompt suffix (cross-prompt coherence; H3/H5)
The GCG matrix optimizes a **universal** suffix over the train pool. Add a **train-only** control: optimize **per-prompt** suffixes (one per train prompt) with the same refusal objective + matched random, and measure — on those same train prompts — whether per-prompt suffixes achieve specific refusal suppression / higher ASR that the universal suffix cannot. If per-prompt succeeds specifically but universal does not → the failure is **universality / lack of cross-prompt coherence** (supports §5.5 / H5), not per-example unreachability. Kept strictly train-only (no test-selection); report as mechanism characterization, not an attack. Cross-refs §5.5 and Gate D4.

### 19.6 Pre-register the control-hierarchy figure (Figure A)
Figure A (activation vs continuous vs discrete) is the centerpiece. **Before running Phase 2**, pre-register the exact plotted quantity (held-out Δ refusal-projection at L18/hs19 and Δ ASR), the norm-matching rule, and the random-control construction, so the hierarchy figure cannot be shaped post-hoc. Formalizes §6.3 + §14 Figure A.

---

*End of plan. This document is not yet executed; §4 (Phase 0 audit + gap matrix) is the first step whenever the sprint begins.*
