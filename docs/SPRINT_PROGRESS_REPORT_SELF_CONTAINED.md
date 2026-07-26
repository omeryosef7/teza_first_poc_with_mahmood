# Sprint Progress Report — Distilling Jailbreaks / Matan-Mahmood Agenda (self-contained)

**Purpose.** A single self-contained report of all progress and results, written so a reader (or another
LLM) with **no access to the code repository** can understand the project, the plan, what was done, and
every result. Snapshot: **2026-07-26 (through execution-log Iteration 47 — core questions RESOLVED).**

**One-paragraph summary.** This is red-team *research on the robustness of reasoning ("thinking") LLMs*,
run as an autonomous engineering loop. A prior project had established a strong but **negative** central
result: an internal "attack-success direction" in a model's activations is **predictive** of whether a
jailbreak will succeed (AUC ≈ 0.90, before any harmful token is generated) but is **not causal**. This
sprint extended that work along three fronts raised by collaborators Matan & Mahmood, and its core
questions are now **resolved**: it (1) reproduced the "affirmative-prefix ≠ harmful behavior" mismatch on
a new benchmark (**Gate-1 PASS**); (2) built and evaluated a behavioral **REINFORCE** attack objective
end-to-end and closed it as an honest **EXPLORATORY NEGATIVE** (**Gate-3 NO** → Gate-4 gated off); and
(3) ran a head-level mechanistic probe of the CoT-Hijacking attack and found **no clean causal mechanism**
(**Gate-5 NOT justified** — the head-level attention contrast is confound-entangled and underpowered →
the CoT signal is retained as a detector, not distilled). **⇒ All three routes into an optimizable attack
objective — the mechanistic success-direction, the behavioral reward, and the CoT head-mechanism — are now
closed by *evaluated* negatives.** **The evaluation judge is not yet frozen (needs human annotation), so
every attack-success-rate number here is EXPLORATORY, not a confirmatory claim.**

> **Note on content.** This report deliberately contains **no attack payloads, jailbreak prompts, or
> harmful generation text** — only research-level facts, methods, numbers, and conclusions. Harmful
> behaviors are referred to by neutral labels (e.g. "the USB-malware behavior").

---

## 1. Background — the original project and its negative result

The parent research plan pursued one "mechanistic spine":

> **Real Attack → Predictive Signal → Causal Validation → Soft Objective → MAC Trigger → Held-Out Transfer**

The idea: find an internal signal that separates successful from failed jailbreaks, prove it is *causal*,
turn it into an optimization objective, and use it to build stronger attacks. That spine was executed
end-to-end and produced a **strong, honest, but negative** result:

- **Predictive (Gate 2 = Yes):** a Fisher "success direction" in the residual stream separates
  successful vs failed attacks at **grouped-LOGO AUC ≈ 0.90 *before any answer is generated*** (best
  cells: `prefill_last` L16 = 0.904, `think_content_1` L20 = 0.906), replicated across **4
  architectures / 2 backbone families** (Qwen3-14B, DeepSeek-R1-Distill-Qwen-7B, DeepSeek-R1-Distill-
  Llama-8B, Phi-4-mini-reasoning).
- **NOT causal (Gate 3 = No):** every causal test is null — activation-addition steering (sufficiency
  0/45; necessity keeps ASR = 1.00 down to −3σ; layer × timing sweeps flat), a uniform
  attention-temperature intervention (null), and a soft-prompt optimization test.
- **Not a usable objective (Gate 4 = No):** soft-optimizing the signal drove its projection far up but
  did **not** raise attack success (honest ASR 0.08 → 0.16, Fisher-exact **p ≈ 0.67 = noise**).
- **Confounded:** on Qwen3 the signal is prompt-length-confounded (length alone AUC 0.827; the
  gain-over-length 95% CI includes 0 at n=44).
- The signal is also **dataset-specific**: on an external dataset the *attack* transfers (ASR 0.848,
  84/99) but the *detector direction* does not (AUC 0.461 = chance).

Because Gate 3 = No and Gate 4 = No, the original plan **correctly routed past** its own discrete-attack
phases (they were never entered — not tested-and-failed, but gated off).

**Why this sprint exists.** Matan & Mahmood raised items that organize into three workstreams. Crucially,
the original plan's **Phase 11 ("Distributional / Reinforcement-Style Optimization")** already specified a
*behavioral* reward objective (reward complete harmful *responses*, not just an affirmative prefix) — and
it was **never executed**, only routed past by the *mechanistic* nulls. The behavioral objective itself
was never gated. This sprint re-activates it as a first-class track (implementing a REINFORCE-style
estimator per arXiv 2502.17254), and re-opens the head/position-specific mechanism question the *uniform*
attention null did not rule out.

---

## 2. The three workstreams and the 7 decision gates

| Workstream | What it covers | State now |
|---|---|---|
| **WS1 — Attack by category** | suffix dataset, category specialization, transfer, single-vs-multi, universality | Descriptive analysis DONE; controlled category attacks NOT started (GPU-gated) |
| **WS2 — Attack reasoning/thinking models** | reproduce mechanisms, exact head/span mechanism, multi-turn, defenses, literature | CoT-Hijacking baselines DONE; **exact head/span mechanism IN PROGRESS**; context-hijacking & SEMA = design/blocked |
| **WS3 — Interpretability → optimization objective** | mechanistic *and* behavioral (REINFORCE) attack objectives | **CLOSED as NEGATIVE** (both routes) |

The sprint is governed by 7 sequential decision gates (stop at each; a NO is a valid reportable result):

| Gate | Question | If NO | If YES |
|---|---|---|---|
| **1** | Does the new benchmark reproduce the "affirmative-prefix ≠ harmful behavior" mismatch? | audit targets/prompts/judge/model | → behavioral optimization |
| **2** | Does behavior-aware reranking beat the prefix-CE baseline? | still go to true REINFORCE | continue |
| **3** | Does a REINFORCE **soft upper bound** improve behavioral ASR over prefix-CE? | audit reward+gradient; **do not** launch the discrete sweep | → REINFORCE-MAC |
| **4** | Does REINFORCE-MAC beat prefix-CE-MAC? | report valid negative | → category + held-out scaling |
| **5** | Is the CoT internal signal **causal** (head/position-specific)? | retain as detector only; **do not** distil | distil into a loss; compare to REINFORCE |
| **6** | Does the detector survive held-out families + datasets? | not a general defense | test adaptive attackers |
| **7** | Is the multi-turn method (SEMA) reproducible at available compute? | scaled reimpl + document gap | run paper-faithful track |

**Gate status:** Gate 1 = **PASS**. Gate 3 = **EXPLORATORY NEGATIVE** → Gate 4 gated off. Gate 5 = in
progress (F1.3 running). Gates 2, 6, 7 not reached.

---

## 3. Methodology / non-negotiable working rules

- **≤ 6 concurrent SLURM jobs; L40S GPUs only; no job dependencies;** cancel+resubmit if pending > 30 min;
  smoke-test before scaling; write results incrementally; never overwrite completed results.
- **No new model-weight downloads** without explicit approval; read cached weights offline. Open-weight,
  locally-controlled targets only.
- **TROPT-first:** TROPT is a shared discrete-trigger-optimization toolbox; prove it cannot express a
  need before writing new optimization infrastructure. All new code here is **project-local with ZERO
  edits to upstream TROPT.**
- **Every new module gets a unit/smoke test + an independent adversarial code-review pass** before its
  results are trusted.
- **Scientific integrity (enforced throughout):** never report an affirmative prefix as a success; never
  call a detector a "mechanism" (no causal evidence) or a "defense" (no adaptive/OOD test); keep
  negatives; report *n/denominator*, never bare %; keep empty/degenerate generations in the denominator;
  keep single- vs multi-instruction results separate; never pool AdvBench and ClearHarm denominators.
- **The judge is NOT frozen.** Evaluation uses the **StrongREJECT** automated grader (success = score
  ≥ 0.5). Its human-annotation validation (Phase B4) is **pending**, so **every attack-success number in
  this report is EXPLORATORY**, not a confirmatory claim.
- **Autonomy + safety:** the loop runs on a 30-minute cron with subagent fan-out. A real-time
  cyber-safeguard terminates any subagent that reads harmful *generation text*, so all text-touching work
  (report writing, generation inspection) is done in the main agent; only scalar/structural analysis is
  delegated.

---

## 4. WS3 — the behavioral REINFORCE attack objective (CLOSED = NEGATIVE)

### 4.1 The benchmark: ClearHarm
The sprint added **ClearHarm** (HF `AlignmentResearch/ClearHarm`, the exact source cited by the TROPT
paper; 179 harmful instructions) as a primary benchmark, vendored under explicit user authorization
(the dataset ships no license). Built into four disjoint manifests
(opt15 / val15 / universal100 / reserve) plus a 5-instruction Gate-3 panel.

### 4.2 Gate 1 = PASS — affirmative-prefix likelihood ≠ harmful behavior (on ClearHarm)
Setup: Qwen3-14B, greedy, `max_new_tokens=2048`, StrongREJECT judge, 3 ClearHarm instructions (a smoke).

| Condition | best prefix-CE loss (per behavior) | Behavioral ASR |
|---|---|---|
| no attack (baseline) | — | **0/3** |
| length-matched random | — | 0/3 |
| MAC + prefix-CE | 1.72 / 2.44 / 2.43 | **0/3** |
| GCG + prefix-CE (500 steps) | **0.0030 / 0.0092 / 1.1112** | **0/3** |

**GCG drove the fixed affirmative-prefix cross-entropy to ≈ 0.003** — the "Sure, here is…" opening made
essentially certain — **yet produced 0/3 harmful compliance.** The model emitted the exact affirmative
prefix and then produced harmless, unrelated content. This reproduces (more starkly than on AdvBench, where
GCG got 9/20) that **optimizing for a fixed affirmative prefix is not the same as optimizing for harmful
behavior** — the motivation for a *behavioral* reward. **Key fact reused later:** at the full 2048-token
budget, even the stronger discrete attacks deliver **zero** harm on these hardened instructions.

### 4.3 The built stack (project-local, 0 upstream edits, ~110 tests for this track)
A complete behavioral-optimization stack was implemented and independently reviewed:
- **D2** reward interface (judge-logit + StrongREJECT rewards; reward-hacking controls) — 30 tests.
- **D4** a true **REINFORCE estimator** (RLOO leave-one-out baseline, signed teacher-forced cross-entropy,
  stop-gradient advantages) with formally verified sign/zero-sum/identity properties.
- **D4** a discrete **trigger-gradient** (one-hot@embedding, advantage-weighted CE → GCG-style token swaps).
- **D3** a proxy-CE *reranking* hybrid, explicitly labelled **NOT REINFORCE**.
- A GPU runner, a **REINFORCE-MAC optimizer loop**, and a **soft-prompt upper-bound runner**.
Pre-GPU review caught and fixed 5 reward-module false-positive bugs, a gather-shape bug, and a
momentum-resume persistence bug.

### 4.4 Gate 3 = EXPLORATORY NEGATIVE — the decisive story
**Design.** The soft prompt is the *strongest continuous input intervention* (unconstrained embeddings,
clean gradients). If it cannot beat the prefix-CE baseline, the strictly-weaker discrete REINFORCE-MAC
cannot either — **Gate 3 gates Gate 4.** Two arms (REINFORCE expected-reward policy gradient vs prefix-CE)
on a 5-instruction ClearHarm panel, K=4, 20 steps, same StrongREJECT judge.

**Honest final-step result (seed 0, best over prompt-lengths {5,20}):** REINFORCE ≥ prefix-CE on all 5
instructions, strictly greater on **2/5** (tie 3/5, never worse); means ≈ prefix-CE 0.15 / REINFORCE 0.25.
The advantage was **seed-stable** across seeds 0–1 (R>P 2/5 each).

**THE DECISIVE FINDING — the metric was a truncation artifact.** A systematic inspection of **all 12**
reward-≥0.5 "successes" (both arms) found that **every one was cut off mid-`<think>`** (~1214 characters);
**none reached `</think>` / a final answer.** Root cause: the soft-prompt runner defaulted to
`max_new_tokens=256`, but a thinking model's `<think>` block alone exceeds that, so it never finished
reasoning or produced an answer. Gate-1 used **2048**. So Gate-3 scored the judge on *truncated in-think
methodology* — a judge-dependent proxy the judge was never validated on — while Gate-1 scored *delivered*
content. The artifact hits both arms equally (so the *comparison* is internally valid), but the **absolute
Gate-3 numbers are not delivered-harm rates.** The flagship "greedy success" was genuine harmful
*methodology reasoning*, but truncated before any runnable output.

**Decision by triangulation (without generating more harm).** Rather than re-run at 2048 tokens (which
would deliberately generate *fuller* operational harmful content to chase a marginal delta — dropped on
integrity + safety grounds), the call was made from existing evidence: (1) the proxy edge is small and
lives entirely in the shared 256-token truncation band; (2) delivered-content evidence already exists and
is **zero** — even the stronger discrete attacks were 0/3 at 2048 tokens (Gate 1); (3) the soft prompt is
the continuous *ceiling*. A flat/noisy per-step trajectory diagnostic (REINFORCE reward-slope ~9× prefix-CE
but only 6/11 runs positive; 3 of 4 greedy "successes" transient) corroborated.

**⇒ Gate 3 = NO (EXPLORATORY NEGATIVE) → the discrete REINFORCE-MAC sweep (Gate 4) is NOT launched.** The
behavioral objective is honestly closed as a negative at the continuous ceiling, alongside the previously-
closed mechanistic objective. **Both discrete-optimization routes are now closed by evaluated negatives.**
Does NOT claim the estimator is wrong (it is verified correct) or that ClearHarm is unbreakable in general
— only that neither objective produces a delivered-harm advantage on this 5-behavior hardened panel with
Qwen3-14B at this budget/judge. (The token-budget default was fixed 256→2048 so no future run repeats the
artifact.)

---

## 5. WS2 — attacking thinking/reasoning models

### 5.1 CoT-Hijacking attack baselines (established; DO NOT rerun)
CoT-Hijacking hides a harmful goal inside a long benign reasoning scaffold, diluting the model's refusal.
Behavior-level StrongREJECT ASR on 25 dev goals:

| Target model | StrongREJECT ASR | clean ASR | uplift |
|---|---|---|---|
| gpt-o4-mini (API reference) | 0.917 (22/24) | — | — |
| DeepSeek-R1-Distill-Llama-8B | **0.957 (22/23)** | 0.360 (9/25) | +0.597 |
| Phi-4-mini-reasoning (3.8B) | 0.773 (17/22) | 0.400 (10/25) | +0.373 |
| gemma-3-4b-it (non-reasoning) | 1.000 (25/25) | 0.000 (0/25) | +1.000 |
| Qwen3-14B (white-box) | 0.818 (18/22) | — | — |

External transfer (MaliciousInstruct, 99 different harmful prompts): attack ASR **0.848 (84/99)** — the
*attack* generalizes even though the *detector direction* does not.

*Integrity verification (2026-07-26 adversarial bug-hunt).* These numbers were audited: **thinking was ON**
for the reasoning targets (verified), the **clean baseline uses the raw harmful goal**, and the
**StrongREJECT judge is correctly grounded on the raw harmful intent** (not the puzzle-scaffold) — the
highest-risk potential bug does **not** exist. One denominator-consistency issue was found and fixed: the
uplift above mixed denominators (attacked /23 or /22 vs clean /25) because a few behaviors produced no
delivered attack (attacker-API non-delivery, *not* refusals — a refusal yields a low-*scored* row). The
honest **matched-set uplift** (same behaviors both arms) is **DeepSeek +0.565, Phi +0.409, gemma +1.000**
(≈±3–4 pp of the table; no conclusion changes). Tool: `scripts/cot_hijacking_denominator_audit.py`.

### 5.2 Exact head/span mechanism (Phase F1) — COMPLETED (negative → detector-only)
**F1.1 span annotation (done):** each attacked prompt was annotated into 7 structural components (benign
scaffold, injected reasoning, final-answer cue, harmful instruction, system, chat-template, generation
marker) with character- and token-index spans, for Qwen3-14B (44 examples) and Phi-4-mini (72). All
components live inside the attack *prompt*, so the mechanism probe is a forward-pass measurement at
generation start — **no new generation**.

**A design-correcting surprise (span-structure analysis):** the "injected_reasoning" span is located in
**0% of successful attacks but 61–68% of failed attacks** (both models); failures also carry a *longer*
benign scaffold. This **inverts** the naïve hypothesis: a visible deliberation span marks the **refusal**
path, not the hijack — consistent with the project's "compliant-CoT" thesis (a successful hijack complies
*without* a distinct deliberation step). This redirected the attention probe **before any GPU was spent**
(the cross-outcome contrast now uses components present in both success and failure).

**F1.3 attention probe (ran on both models):** for every (layer, head), measure the attention mass from the
generation/cue positions into each span, contrasting successes vs failures (forward-only, no generation).
Both models show the **same correlational contrast**: successes attend **more** to the benign scaffold and
**less** to the final-answer cue (Phi Δ±0.29 at layer 0; Qwen Δ±0.18, top scaffold head at layer 5).
Attention into the harmful-instruction and injected-reasoning spans shows only tiny contrasts.

**The confound screen decided it (§6.3a): Gate-5 NOT justified.** Before spending GPU on the causal test,
the candidate contrast was screened for the length/structure confound (failed prompts have longer
scaffolds — the same confound that made the parent project's signal predictive-not-causal). Result, per
model: **Qwen** — the scaffold contrast is **strongly length-confounded** (pooled r=0.68; within-success
r=0.95); **Phi** — **not** strongly length-confounded (r=0.18) **but** its top heads are at **layer 0**
(positional/interpretively weak) and it rests on only **n=7 successes**. Neither meets the bar for a causal
test, and neither is isolable to the candidate head at the current logging granularity.

**⇒ Gate 5 = NOT JUSTIFIED → the CoT internal signal is retained as a *detector*, NOT distilled into an
attack loss** — consistent with the parent project's predictive-not-causal result. This does *not* prove
no mechanism exists; it says the available dev-25 evidence (n=6–7 successes, confound-entangled) is too
weak to justify the expensive causal intervention. A properly-powered per-head probe on a larger success
set could revisit it. **This closes the last of the three routes into an optimizable attack objective.**
(A CUDA-OOM in the first Qwen run — fp32 upcast of the stacked 40-layer attention — was fixed with a
per-layer CPU offload and re-run; not a scientific result.)

### 5.3 Literature disambiguation (four distinct "hijacking" attacks — not to be conflated)
| Name | arXiv | What is hijacked |
|---|---|---|
| **CoT-Hijacking** | 2510.26418 | the model's attention budget during long reasoning |
| **H-CoT** | 2502.12893 | the displayed safety-reasoning trace (needs visible CoT) |
| **Doublespeak / In-Context Representation Hijacking** | 2512.03771 | a token's internal representation (in-context keyword substitution) |
| **Universal Attention Hijackers (Ben-Tov)** | 2506.12880 | attention from an adversarial suffix (a GCG variant) |

### 5.4 Context-hijacking (Doublespeak) and SEMA (multi-turn)
- **Doublespeak (Phase F2):** design complete; released code located and verified (github.com/1tux/
  doublespeak, MIT). **Reference is UNCONFIRMED** (pending Matan confirming which paper "context hijacking"
  means — leading candidate arXiv 2512.03771). No reproduction run yet.
- **SEMA (Phase G, multi-turn):** **BLOCKED on academic code access** (public repo exists but executable
  code is under Microsoft Research review, gated behind a signed access agreement). A reusable multi-turn
  simulator skeleton was built but not run.

---

## 6. WS1 — attack-by-category, and the defense work

**Category (descriptive, done).** 336 final suffixes were reconciled from **102,897** evaluation rows
across 136 result files (all GCG-optimized; 305 distinct). A strengthened taxonomy and a category-transfer
matrix were built with **goal- and suffix-clustered bootstrap CIs** (rows are not independent). Key
findings (a single universal suffix, 520 behaviors, goal-clustered CI):
- Most vulnerable category: **misinformation, ASR 0.246 [0.167, 0.333]**; least vulnerable (n≥15):
  **drugs, 0.0**. Category coverage 16/16.
- **No seed-memorization** (unseen-generation-seed ASR 0.089 ≥ train-seed 0.080).
- Single- vs multi-instruction kept strictly separate (the raw gap is model-family-confounded and not
  like-for-like).
- Corroborates at scale that **prefix-CE loss ≠ behavioral success** (a fully-optimized universal suffix
  reaches only ~0.08 ASR over 520 behaviors).
- Controlled category-specific attacks and off-diagonal transfer are **NOT started** (GPU-gated).

**Defense (detector).** An early success-vs-failure detector reaches in-distribution AUC ≈ 0.90–0.925 at
the *last input token* (before any generation). But: (a) it does **not** generalize — external/OOD
transfer AUC = **0.461 (chance)**; (b) after controlling for prompt length, **no detector family adds
significant signal at n=44** (every gain-over-length CI includes 0); (c) it is a *detector*, not a
*defense* — no adaptive-attacker test has been run, and steering-based defense is unsupported (the
mechanism is non-causal). Honest position: usable only as a pre-generation *gate*, cost/benefit
unquantified.

---

## 7. Engineering, bugs found, and current state

**Test coverage:** ~200+ new-code unit/smoke tests green across the behavioral-objective stack, the
Gate-3 analysis tools, the F1.3 attention-probe stack, and the integrity-audit tools. Every module was
independently adversarially reviewed before its results were trusted.

**Notable bugs found & fixed during execution** (illustrates the review discipline):
- A SLURM GPU-banner command crashed jobs via a SIGPIPE under `set -euo pipefail` (made non-fatal).
- The reward-scoring environment lacked the judge library (repointed to the correct conda env, which also
  guaranteed judge consistency with Gate-1).
- The REINFORCE-MAC momentum buffer wasn't persisted across job resume (fixed + regression test).
- **`max_new_tokens=256` truncation artifact** (the methodologically decisive one — see §4.4; fixed to 2048).
- **`sbatch --export` comma bug:** `LENGTHS=5,20` silently truncated to `LENGTHS=5`, so seed jobs ran half
  the intended rows yet exited "COMPLETED". (No impact on the negative conclusion.)
- **F1.3 CUDA-OOM** (fp32 upcast of stacked 40-layer attention) — fixed with per-layer CPU offload, re-ran.
- **CoT-Hijacking denominator asymmetry** (bug-hunt) — uplift mixed /23-vs-/25; corrected to matched-set
  uplifts (§5.1); reusable audit script added.
- **stage-4 `enable_thinking=False` silent no-op** (bug-hunt) — Qwen3-only; fixed + tested; severity
  **MISLABELS** (no reported number invalidated; the headline phase5-9 pipeline is thinking-ON and
  unaffected) — see `docs/SPRINT_COMPLETION_AUDIT.md`.

**Current state (Iter 47 — core questions RESOLVED):**
- WS3 behavioral objective: **CLOSED (EXPLORATORY NEGATIVE).**
- Phase F1 CoT mechanism: **CLOSED** — probe ran both models; confound screen ⇒ **Gate-5 NOT justified** →
  detector-only.
- **All three routes into an optimizable attack objective are now closed by evaluated negatives.**
- Integrity closeouts from the bug-hunt: done. Remaining work is externally blocked or optional (below).

---

## 8. What remains, and on whom it is blocked

- **Judge freeze (Phase B4) — blocked on a HUMAN (the user).** The validation sample, agreement tooling
  (Cohen's κ, confusion, per-stratum), and freeze protocol (κ ≥ 0.6, FPR ≤ 0.10) are prepared; a human
  must annotate blind. **This is the single most pervasive blocker — until it clears, every ASR is
  EXPLORATORY.** (It would re-confirm the negatives under a frozen judge, not overturn them.)
- **Context-hijacking (Doublespeak)** — blocked on Matan confirming the reference paper; then a GPU
  reproduction (design + located MIT code ready).
- **SEMA (multi-turn)** — blocked on academic code access; scaled-reimpl simulator skeleton ready.
- **Optional GPU attack-scaling, not required to answer the core questions** (needs an explicit go-ahead
  because it generates new harmful attacks): Phase E4–E6 controlled category attacks; a confirmatory
  ClearHarm baseline matrix; cross-family/adaptive defense. (The discrete REINFORCE-MAC sweep is
  permanently gated OFF by the Gate-3 negative.)

---

## 9. Honest bottom line

- **Three clean, evaluated NEGATIVES** are the headline scientific results: (1) the mechanistic
  success-direction is predictive-but-not-causal; (2) the behavioral REINFORCE objective shows no
  delivered-harm advantage over the prefix-CE baseline at the continuous ceiling (Gate-3 NO); (3) the
  CoT-Hijacking head-level attention contrast is confound-entangled and underpowered, so no causal
  mechanism is demonstrated (Gate-5 not justified → detector-only). **All three routes into an
  optimizable attack objective are therefore closed by evidence, not assumption.**
- **One PASS:** the affirmative-prefix ≠ harmful-behavior mismatch is reproduced on ClearHarm (Gate 1),
  which is *why* a behavioral objective was worth testing.
- **The CoT-Hijacking *attack* itself remains strong and generalizes** (ASR 0.77–1.00 across reasoning
  models; 0.848 external transfer) — what is negative is the attempt to distil an *internal mechanism or
  optimizable objective* from it; the attack works, the mechanism is not causally pinned.
- **All attack-success numbers are EXPLORATORY** pending the human judge-freeze; the freeze would
  re-confirm the negatives, not overturn them. Provisional results are labelled as such throughout and
  are never presented as positive findings.

*Source documents (in the repository): `docs/SPRINT_COMPLETION_PLAN_MATAN_MAHMOOD.md` (the plan),
`docs/SPRINT_COMPLETION_EXECUTION_LOG.md` (Iters 0–47, full running record),
`docs/REINFORCE_OBJECTIVE_REPORT.md`, `docs/TROPT_CLEARHARM_BASELINE_REPORT.md`,
`docs/COT_HIJACKING_EXACT_MECHANISM_REPORT.md`, `docs/SPRINT_FINAL_SYNTHESIS.md`,
`docs/PLAN_EXECUTION_SUMMARY.md`, and `results/EXPERIMENT_REGISTRY.csv`. Every number in this report
traces to one of these on-disk artifacts; none is fabricated.*
