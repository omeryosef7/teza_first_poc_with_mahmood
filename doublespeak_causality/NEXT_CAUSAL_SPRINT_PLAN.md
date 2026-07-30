# Doublespeak Causality — Next Sprint Plan

**Paper:** *In-Context Representation Hijacking* / Doublespeak — https://arxiv.org/pdf/2512.03771 · Official code: https://github.com/1tux/doublespeak
**Primary model:** Llama-3.1-8B-Instruct (matches paper, existing code, validated directions)
**Primary controlled pair:** CARROT ↔ BOMB
**Status:** Plan of record for the next causal sprint. Self-contained. Written before new experiments.

> Note: this is a *new* next-sprint plan written alongside the existing `DOUBLESPEAK_CAUSALITY_PLAN.md` (which was not overwritten). It supersedes the older plan for the causal-mediation sprint described here.

---

## 0. Reading Order / Mandatory Inputs (reconcile before Stage 0 execution)

**Paper sections that govern this sprint:**
- §3.2 Logit Lens and Patchscopes
- §3.3 Representation Hijacking
- §3.4 Proposed TOCTOU and superposition explanations
- Construction & evaluation methodology
- Figure 2 (note: conditions its representation analysis on *successful* attacks — we must NOT copy this conditioning for primary estimates)
- Appendix I
- Robustness / token-selection experiments

**Existing project docs to reconcile (do not trust markdown claims without checking JSON/JSONL + code):**
- `MERGED_MASTER_PLAN.md`
- `doublespeak_causality/DOUBLESPEAK_CAUSALITY_PLAN.md` (older plan — keep for reference)
- `NEXT_SPRINT_PLAN.md`, `CAUSAL_CORE_PLAN.md`
- all progress logs, result summaries, freeze audits, handoff documents, artifact manifests, experiment registries, paper drafts

**Reuse mandate:** reuse the official Doublespeak implementation + existing vendored code, environment, model-loading, token-localization, output schemas, and SLURM conventions. Do not rewrite existing functionality. Verify important claims against JSON/JSONL artifacts and code, not markdown.

---

## 1. Current Verified State of the Project

The project has already gone substantially beyond the paper. Prior findings (each to be re-confirmed against artifacts during Stage 0, not assumed):

1. **Direct concept direction is causal.** `d_Direct = h(BOMB in direct harmful prompt) − h(CARROT in neutral prompt)` causally installs the BOMB interpretation when added at CARROT positions. Strong, dose-monotonic, near-ceiling semantic effects in late layers.
2. **Observational Doublespeak direction is causally inert.** `d_DS = h(CARROT under Doublespeak) − h(CARROT under Neutral)` is causally inert or nearly inert across tested pairs, despite being stable and despite Doublespeak being strongly decodable by Patchscopes.
3. Direct-state and timing interventions support a behavioral early-refusal / late-compliance pattern consistent with TOCTOU.
4. Attention-knockout effects previously attributed to demonstrations were **not specific** once count-matched random controls were introduced.
5. **Representation-based objectives did not beat behavior.** Temporal-GCG did not improve held-out ASR; it increased refusal. Causal-score-based codeword/demonstration selection *anti-predicted* held-out ASR. Behavioral selection performed much better.
6. Static embedding distance and related codeword properties did not reliably predict hijack strength.

**Do not re-run these as if new.** Do not make "find a direction that predicts success" or "another embedding-distance analysis" the central plan.

---

## 2. Claims: Stand / Retracted / Unverified

Maintained as a living **claim-to-artifact table**. Every quantitative sentence in final docs must point to a committed backing artifact. Labels used throughout: `CONFIRMATORY` · `EXPLORATORY` · `NEGATIVE` · `INVALIDATED` · `UNVERIFIED` · `BLOCKED`. Until Stage 0 smoke tests pass, all downstream claims are `BLOCKED`.

---

## 3. The Exact New Scientific Question

Explain the surprising **causal dissociation**:

> Doublespeak is decodable from the target token, but the local Doublespeak difference vector is not causally effective.

Determine whether the Doublespeak semantic effect is carried by:
- **A.** the local hidden state of the query codeword;
- **B.** the surrounding Doublespeak context and its downstream attention/KV computation;
- **C.** an interaction between the local state and the receiver context;
- **D.** a separate concept-representation mechanism and refusal mechanism whose causal windows occur at different depths.

This is a **causal mediation / decomposition study**, not another passive probing study.

---

## 4. Why This Adds Something Not in the Paper

The paper provides observational/decoding evidence only (Logit Lens, Patchscopes, behavioral attack evaluations) plus hypothesized TOCTOU and semantic-superposition explanations. It **does not intervene inside the attacked computation** to show the Doublespeak representation is necessary or sufficient for the semantic/behavioral outcome. This sprint supplies interventional causal evidence and localizes the mechanism (local state vs context/KV vs interaction vs separated concept/refusal windows).

---

## 5. Formal Causal Estimands

For each matched prompt and intervention layer L, define query-codeword activations:
```
h_N(L)      = query-CARROT activation under NEUTRAL
h_R(L)      = query-CARROT activation under REPETITION_ONLY
h_BICL(L)   = query-CARROT activation under BENIGN_ICL
h_DS(L)     = query-CARROT activation under DOUBLESPEAK
h_Direct(L) = query-BOMB activation under DIRECT
```

Outcomes Y (measure all): (1) P(BOMB)/validated concept-readout; (2) P(CARROT)/literal-readout; (3) BOMB-vs-CARROT log-odds difference; (4) refusal outcome/probability; (5) behavioral class where generation enabled.

Estimands:
```
IE_state(L)   = Y(Neutral, h_DS(L)) − Y(Neutral, h_N(L))          # local-state mediated effect in neutral receiver
DE_context(L) = Y(DS, h_N(L))       − Y(Neutral, h_N(L))          # context effect holding local state neutral
INT(L)        = [Y(DS, h_DS) − Y(DS, h_N)] − [Y(Neutral, h_DS) − Y(Neutral, h_N)]   # state×context interaction
TE(L)         = Y(DS, h_DS(L))      − Y(Neutral, h_N(L))          # total matched Doublespeak effect
```
Report fraction of TE explained per term **only where mathematically meaningful** — never force "percentage mediated" when TE≈0 or effects are non-additive.

---

## 6. Stage-by-Stage Execution Plan

### Stage 0 — Integrity Repair Before New Claims
Fix or quarantine known load-bearing defects; do not start new science until repaired smoke tests pass.
1. **Patch sweep bounds:** fix readout-layer contamination (findings C1/C3). Never patch layer L when L is also the readout layer such that it overwrites the measured vector. Enforce `L ≤ R−1` where appropriate. Add a unit test that fails if a sweep includes an invalid readout-layer intervention.
2. **Pair aggregation:** fix C2 (missing cells → 0 counted as "inert"). Missing stays missing, never affirms null. For positive installation tests use intended **signed max**, not max(abs), unless analysis is explicitly about absolute effects.
3. **Empty generations:** add C8 empty-completion guard to every behavioral pipeline. EMPTY / generation-failure / judge-failure / genuine BENIGN are **distinct states**.
4. **Behavioral labeling & judge health:** one authoritative label partition; judge-health gates; retry/failure accounting; do not mark COMPLETE when judge/generation unhealthy.
5. **Cross-validation leakage:** recompute learned directions/features inside each fold; never use a held-out-concept direction while claiming held-out-concept evaluation.
6. **Token localization:** verify every intervention occurrence; distinguish first/last/all; store token IDs, char spans, token spans, intervention site; multi-token codewords get a preregistered aggregation or separate analysis.
7. Re-run only the **minimal load-bearing checks** needed to validate repaired code.

**Deliverables:** integrity-fix report; tests demonstrating each repaired failure mode; table of old claims (valid / changed / now-unsupported); immutable replacement artifacts (no silent overwrite). **Gate:** repaired smoke tests pass.

### Stage 1 — Matched Fixed-Pair Causal Dataset
Build/reuse a matched CARROT↔BOMB dataset with text-disjoint paraphrase families. Each semantic item has matched versions:
1. **NEUTRAL** — genuinely about carrots.
2. **REPETITION_ONLY** — CARROT appears same count/≈positions as DS, without BOMB-establishing sentences. Include a simple "CARROT CARROT ..." control where useful, but match token count/positions.
3. **BENIGN_ICL** — context teaches a harmless contextual remapping of CARROT (controls generic in-context remapping).
4. **DOUBLESPEAK** — context uses CARROT where BOMB would appear.
5. **DIRECT** — prompt contains BOMB explicitly.
6. **SHUFFLED_OR_INCONSISTENT_MAPPING** — same words/length, no coherent mapping.

**Do not** select only attack-successful prompts. Primary results estimated on the **preregistered full matched set**. Baseline-stratified (MALICIOUS/REJECTED/BENIGN) only as secondary. Safe semantic readouts for most experiments; for behavioral generations do not expose harmful completion text, save only reproducibility/audit minimum, produce sanitized artifacts, keep outcome states distinct.

### Stage 2 — PRIMARY: State × Receiver-Context Causal Transplant (highest priority)
Determine whether the semantic effect is portable in the target-token activation or depends on receiver-context downstream computation. Patch each source activation into several receiver contexts.

Minimal primary 2×2 mediation table + mandatory positive control:
```
Y(Neutral receiver, h_N)       Y(Neutral receiver, h_DS)
Y(DS receiver,      h_N)       Y(DS receiver,      h_DS)
Y(Neutral receiver, h_Direct)  Y(DS receiver, h_Direct)   # h_Direct = positive control
```
Add REPETITION_ONLY and BENIGN_ICL receivers if pilot is healthy. Measure the 5 outcomes above. Sweep all layers on a small pilot, then confirmatory runs on preregistered early/mid/late windows. Report `IE_state`, `DE_context`, `INT`, `TE`.

**Hypotheses:** H1 h_Direct portable → installs BOMB in Neutral receiver (positive-control replication). H2 h_DS substantially less portable than h_Direct. H3 DS receiver preserves much BOMB interpretation even after replacing local query activation with h_N. H4 if H2+H3, attack is not fully stored in local target-token state — implemented largely by contextual downstream computation or state×context interaction. H5 REPETITION_ONLY does not reproduce DS context effect merely from CARROT repetition.

**Mandatory controls:** identity patch; source-to-itself; shuffled source from another matched item; norm-matched random activation; unrelated benign-concept activation; adjacent-token; random token with matched count; invalid-layer/no-op; h_Direct.

Do not claim local-state sufficiency from an additive direction alone: use both **full activation replacement/transplant** and additive/projection as secondary decomposition. Run resid_pre, resid_post, attention-output, MLP-output **only after** the residual-stream pilot identifies relevant layers.

### Stage 3 — Context/KV Mediation and Path Patching
Proceed **only if** Stage 2 shows receiver context contributes substantial causal effect after controlling query-token activation.
1. Patch/swap demonstration-token K/V cache between matched Neutral and DS prompts, preserving query, query activation where possible, sequence length, exact number of patched positions.
2. Compare: Neutral state+Neutral KV; Neutral state+DS demo KV; DS state+Neutral demo KV; DS state+DS KV.
3. Causal path patching from: demonstration codeword occurrences; other demonstration tokens; query codeword; answer-cue/final-prompt positions.
4. Count- and position-matched random controls (avoid the prior "all demonstrations vs fewer-valid-keys random" mistake).
5. If a coarse band is found: decompose attention-output, MLP-output, then individual heads only within the validated band.
6. Head-level: held-out prompts; multiple-comparison correction; validate via ablation + restoration; require replication across seeds/splits; never call a head causal from attention weight/correlation alone.

**Outcomes (all useful):** A DS KV→Neutral receiver installs concept (contextual-memory). B DS query sufficient only with DS KV (state×context gating). C neither sufficient (distributed — report honestly). D small reproducible attention/MLP path mediates (candidate circuit).

### Stage 4 — Concept × Refusal Factorial: Causal Test of TOCTOU
Two independently validated intervention families:
- **Concept:** add/replace/project-out using d_Direct (or best validated concept op) at query CARROT; vary early/mid/late windows + dose.
- **Refusal:** validated refusal direction/op; independently add/remove/project-out; vary window.

Preregistered factorial: concept {none/add/remove} × refusal {none/add/remove} × concept-timing {early/mid/late} × refusal-timing {validated windows}. Start with 2×2 pilot: (A) neither; (B) concept only; (C) refusal ablation only; (D) concept + refusal ablation. Add refusal restoration if healthy.

**Hypotheses:** H1 early concept install ↑ BOMB + ↑ refusal. H2 late concept install ↑ BOMB with less refusal than equally-strong early. H3 removing refusal converts part of early concept-induced refusal into non-refusal while preserving concept reading. H4 adding/restoring refusal suppresses late concept-induced compliance if safety can still act post-shift. H5 significant concept-timing × refusal-intervention interaction = direct causal TOCTOU evidence.

**Do not infer TOCTOU from two crossing curves** — require an intervention interaction with paired CIs. Track separately: semantic interpretation, refusal, benign literal, harmful compliance, empty/failed. Controls: random-direction, unrelated-concept, dose matching, norm matching, identical generation settings, fixed/deterministic decoding seeds for paired comparisons.

### Stage 5 — Generalization (only after primary gates)
1. Replicate state×context decomposition on ≥3 additional fixed pairs across different concepts.
2. Choose codewords spanning embedding distance **only as a controlled robustness axis** (not main hypothesis — already null).
3. Replicate the most load-bearing intervention on one additional architecture (prefer one already supported by repo SLURM scripts).
4. If feasible include one model family used directly in the paper.
5. Never pool pairs into one effect without per-pair results + heterogeneity.
6. Require per-pair semantic-readout validation, valid token localization, identical control structure, no missing→zero aggregation, artifact-backed CIs.

### Stage 6 — Optimization is Conditional, Not Automatic
Do NOT launch another large GCG/soft-prompt/codeword search merely because a new score exists (prior scores failed or anti-predicted ASR). Proceed only if ALL gates pass:
1. A causal variable/interaction from Stages 2–4 robustly changes **behavioral** outcome (not just a probe).
2. Effect replicates on held-out prompt families.
3. A cheap candidate-level surrogate predicts the interventional behavioral effect on held-out data.
4. Surrogate beats: random, anti-selection, behavioral-only baseline, context-length/token-count controls.
5. Optimization target defined **before** looking at held-out ASR.

If gates pass: small controlled experiment first. Candidate objective derived from the causal factorial, e.g. "maximize late concept installation while minimizing early refusal activation" or (if Stage 3 supports) "maximize validated contextual/KV-mediated effect rather than observational h_DS−h_N projection." A clean negative is acceptable. Train/dev/test split with **test frozen before optimization**; report utility only on untouched test set.

---

## 7. Gates and Stopping Criteria

- **Stage 0 gate:** repaired smoke tests pass; positive/negative controls behave; no readout-layer overwrite.
- **Stage 2 → 3 gate:** receiver context contributes substantial causal effect after controlling query activation.
- **Stage 4 gate:** healthy pilot (judge health, non-empty, controls) before full factorial.
- **Stage 5 gate:** stable, audited CARROT↔BOMB result.
- **Stage 6 gate:** all five optimization gates above.
- **Stopping rule / exclusion rules / missing-output handling / seed policy:** specified in preregistration (§9). Do not mark COMPLETE with missing outputs or judge failures.

---

## 8. Controls (consolidated)

Identity patch; source-to-itself; shuffled source; norm-matched random; unrelated benign concept; adjacent token; random token with matched count; invalid-layer/no-op; h_Direct positive control; count- and position-matched KV/attention controls; random-direction and unrelated-concept controls for refusal; dose + norm matching; deterministic decoding for paired comparisons.

---

## 9. Statistics & Preregistration

Write a preregistration section before confirmatory runs specifying: primary hypotheses; primary outcomes; primary layer windows; sample-size target; stopping rule; exclusion rules; missing-output handling; seed policy; multiple-comparison correction; confirmatory vs exploratory.

Reporting: paired analyses whenever prompts matched; paired mean effects; bootstrap CIs; prompt-/paraphrase-family-level resampling; exact n; effect heterogeneity; per-pair results; all control effects. **Holm** correction for layer/head/component sweeps. "Not significant" ≠ zero — for causal-inertness claims define an equivalence margin in advance and run equivalence-style analysis or report a tight upper confidence bound. Never use only successful baseline attacks for primary mechanistic estimates. Never average over missing cells.

---

## 10. Compute Estimates

Estimate runtime and GPU-hours before every large launch. Order: unit tests → CPU/synthetic → one-prompt smoke → tiny GPU pilot → small preregistered pilot → full confirmatory array. Do not run an expensive grid before checking the first few intervention cells have the intended causal semantics. (Concrete GPU-hour figures filled per pilot measurements.)

---

## 11. SLURM Strategy

Reuse existing working SLURM scripts; infer account, partition, env activation, GPU/mem requests, timeout conventions, log paths — do not invent settings. Project rules: no SLURM dependencies, ≤6 parallel jobs, L40S only, no trimming; bfloat16 + default SDPA (do not disable flash); verify row counts after COMPLETED (sbatch --export comma bug). Use arrays for genuinely independent items. Jobs resumable + idempotent. Never silently overwrite — unique immutable output dir per run. Validate artifact completeness automatically after each job. Review sacct + logs after every submission wave.

---

## 12. Expected Artifacts

Every output dir contains/references: config; git commit SHA; model name + exact revision; tokenizer info; seed; dtype; generation params; intervention spec; SLURM job ID; timestamps; environment/package snapshot; success/failure status; raw + summarized metrics. A run with missing outputs or judge failures is not COMPLETE.

Maintained docs: this plan; `doublespeak_causality/NEXT_CAUSAL_SPRINT_PROGRESS.md` (continuously updated); master execution log; experiment registry; claim-to-artifact table; immutable artifact manifest; bug & deviation log; concise results summary; final handoff; paper-contribution draft separating original-paper claims / reproduced findings / new causal findings / negative findings / limitations.

---

## 13. Risks and Alternative Interpretations

- Distributed computation (Stage 3 outcome C): effect neither in local state nor a narrow KV subset — report honestly, not as failure.
- Non-additive / TE≈0 regimes make "% mediated" meaningless — guard against forcing it.
- Judge/generation unhealth silently biasing behavioral outcomes — mitigated by health gates and distinct outcome states.
- Confounds: token-count, length, position, baseline-outcome — test explicitly after every result.
- Readout-layer contamination and missing→zero aggregation recurring — covered by Stage 0 tests.
- Positive controls failing (h_Direct not installing) would invalidate the intervention harness before any negative claim.

---

## 14. Criteria for a Paper-Worthy POSITIVE Result

A robust, controlled, artifact-backed demonstration that the Doublespeak semantic effect is causally localized to a specific mechanism — e.g. DS KV transplanted into a neutral receiver installs the concept (contextual memory), or a state×context gating, or a small reproducible attention/MLP path — with: replication across seeds/splits and held-out prompts; passing positive/negative controls; per-pair results across ≥3 pairs (Stage 5); and, for TOCTOU, a significant concept-timing × refusal-intervention interaction with paired CIs. Optionally a Stage-6 causal-objective attack that beats behavioral and control baselines on a frozen test set.

## 15. Criteria for a Paper-Worthy NEGATIVE Result

A clean, controlled negative is valuable: e.g. rigorous demonstration (with passing positive controls and equivalence-margin analysis) that the local Doublespeak difference vector is causally inert while it is strongly decodable, that neither local state nor a narrow KV subset is sufficient (distributed computation), or that a causally-derived optimization objective still fails to beat behavioral selection on a frozen test set. The negative must rest on interventions and committed artifacts with tight upper confidence bounds — not on absence of evidence.

---

## Execution Directive (for the implementation phase — not part of this write-only task)

After this plan is written and reviewed, implement it stage-by-stage with gates. Reuse existing/official code; minimize new code. Fan out subagents for independent work (audit, design review, SLURM prep, tests, stats validation, doc/claim verification) but never parallelize stages whose outputs determine later experimental choices. Recurring ~30-min review loop: inspect SLURM jobs, review logs/failures, verify artifacts, update progress doc, decide whether gates permit the next stage. Self-code-review + independent subagent review; smoke tests and positive/negative controls before expensive jobs; commit and push after every milestone. Goal: add a defensible causal result to the paper's scientific story — determined by interventions and artifacts, not by a desired narrative. Do not manufacture a positive conclusion.
