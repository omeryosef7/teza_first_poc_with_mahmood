# Sprint Final Synthesis — Matan / Mahmood Request Closure

> **STATUS: core questions RESOLVED (snapshot as of Iter 46, 2026-07-26).**
> Three decision gates are now RESOLVED: **Gate-1 = PASS**; **Gate-3 = EXPLORATORY NEGATIVE** (behavioral
> REINFORCE does not beat Prefix-CE in *delivered* harm at the continuous ceiling); **Gate-5 = NOT
> JUSTIFIED** (CoT head-mechanism confound-entangled/underpowered → detector-only). All three routes into a
> distilled attack objective are closed by evaluated negatives.
> The StrongREJECT judge is **not yet frozen** (Phase B4 human annotation outstanding), so every
> ClearHarm / behavioral ASR below is **EXPLORATORY** and no result is upgraded to a confirmatory
> positive. Sources of truth: `docs/SPRINT_COMPLETION_EXECUTION_LOG.md` (Iter 0–38),
> `docs/REINFORCE_OBJECTIVE_REPORT.md`, `docs/TROPT_CLEARHARM_BASELINE_REPORT.md`,
> `docs/COT_HIJACKING_EXACT_MECHANISM_REPORT.md`, `docs/REINFORCE_TROPT_IMPLEMENTATION.md`,
> `docs/PLAN_EXECUTION_SUMMARY.md`, `results/EXPERIMENT_REGISTRY.csv`.

---

## Headline findings so far

1. **Gate-1 PASS — prefix-CE likelihood ≠ harmful behavior, reproduced on ClearHarm (starker than on
   AdvBench).** GCG drove the fixed affirmative-prefix cross-entropy to **≈0.003 / 0.009** yet behavioral
   ASR was **0/3** (clean 0/3, random 0/3, MAC 0/3, GCG 0/3) at `max_new_tokens=2048`. Cleanest example:
   for the Gmail brute-force instruction the model emitted the **exact** optimized prefix then produced
   **Psalm 23 / Bible verses** instead of a script — affirmative opening delivered, behavior harmless.
   This is the dataset-level motivation for a behavioral (response-reward) objective. **EXPLORATORY
   judge; n=3 smoke.** Evidence: `docs/TROPT_CLEARHARM_BASELINE_REPORT.md`, `outputs/phase_c_clearharm_smoke/*`.

2. **Gate-3 NEGATIVE — the behavioral (soft-prompt REINFORCE) objective does NOT beat Prefix-CE in
   delivered harm.** The ceiling test (continuous soft-prompt, expected-reward policy gradient vs
   Prefix-CE, ClearHarm-5) was run better-powered (K=4, 20 steps). The call is made on **delivered
   content** via triangulation, *without generating additional operational harm*:
   (a) **§D7 truncation finding** — the runner used `max_new_tokens=256`; for a thinking model that
   truncates every generation mid-`<think>` (all 12 reward≥0.5 "successes" never reached `</think>`), so
   the Gate-3 ASR was a **256-token in-think PROXY**, not delivered harm — and both arms share it;
   (b) at the honest final-step metric the proxy edge is small (REINFORCE > Prefix-CE 2/5, tie 3/5,
   never worse) and **seed-stable** across seeds 0–1 — but still only in the proxy;
   (c) **delivered-content evidence is already 0/3** at 2048 tokens for the *stronger* discrete GCG/MAC
   attacks (Gate-1); the soft prompt is the continuous ceiling, so no delivered advantage exists;
   (d) the optimization trajectory is largely flat/noisy (REINFORCE expected-reward slope ~0.0017,
   6/11 runs positive). **⇒ Do not launch the discrete REINFORCE-MAC sweep (Gate-4 gated off).** A valid,
   reportable negative, mirroring the mechanistic-objective negative. The runner token-budget default was
   fixed (256→2048) so no future run repeats the artifact. Evidence: `docs/REINFORCE_OBJECTIVE_REPORT.md`,
   `results/GATE3_SEED_AGGREGATE.csv`, `results/GATE3_TRAJECTORY_DIAG.csv`.

3. **The prior mechanistic "success direction" remains predictive-but-not-causal** (carried from the
   cross-model project). Predictive pre-answer (grouped-LOGO AUC **0.906**) but every causal test NULL
   (steering sufficiency 0/45, necessity ASR=1.00 to −3σ, length-confounded); soft-optimizing it did not
   raise ASR (0.08→0.16, p≈0.67). Gate-1 independently corroborates that a likelihood/representation
   proxy is not the behavior. **Both routes into discrete optimization (mechanistic + behavioral) are now
   closed by EVALUATED negatives.** Evidence: `docs/PLAN_EXECUTION_SUMMARY.md`, `outputs/phase7_causal/`.

4. **CoT exact-mechanism (Phase F1) — RAN; Gate-5 causal test NOT justified → detector-only.** F1.1 span
   annotation done; a span-structure analysis surfaced a probe-correcting surprise (`injected_reasoning`
   located in **0% of successful vs 61–68% of failed** attacks — visible deliberation marks the *refusal*
   path, compliant-CoT thesis). The F1.3 attention probe RAN on both models (forward-only interpretability,
   no generation): both show a correlational contrast (successes attend MORE to the benign scaffold, LESS
   to the final-answer cue). But the §6.3a confound screen shows it does **not** meet the bar for a causal
   test — **Qwen** contrast is length-confounded (pooled r=0.68), **Phi** is not length-confounded (r=0.18)
   but positional (layer-0) and underpowered (n_success=7), and neither is isolable to the candidate head
   at current logging. **⇒ Gate 5 NOT justified: retain the CoT signal as a detector, do NOT distil into a
   TROPT loss** — consistent with the parent project's predictive-not-causal result. So **all three routes
   into a distilled attack objective are now closed** (mechanistic success-direction, behavioral REINFORCE,
   and CoT head-mechanism). Evidence: `docs/COT_HIJACKING_EXACT_MECHANISM_REPORT.md §6–7`,
   `results/COT_F13_*.csv`.

   *Integrity note (2026-07-26 bug-hunt):* the CoT-Hijacking headline ASRs were verified — thinking was ON
   for the reasoning targets, the clean baseline uses the raw goal, and the StrongREJECT judge is correctly
   grounded on the raw harmful intent (the highest-risk bug does NOT exist). One confirmed issue: the uplift
   mixed denominators; the honest **matched-set** uplift is DeepSeek **+0.565**, Phi **+0.409**, gemma
   +1.000 (≈±3–4 pp, no conclusion change). See `docs/CROSS_MODEL_COT_BENCHMARK_REPORT.md`.

5. **Engineering is complete; the remaining science is GPU/judge-gated.** The full behavioral stack
   (reward + controls, RLOO estimator, discrete trigger-gradient, GPU runner, REINFORCE-MAC loop with the
   momentum-resume fix, soft-prompt upper bound) plus the F1.3 attention-probe stack are **built,
   unit-tested (190+ tests green), and adversarially reviewed**, zero edits to upstream `TROPT/tropt/*`.
   What remains is compute + the **judge freeze** (human annotation) + GPU-gated phases (F1.3 run, F1.5
   causal, E4–E6, context-hijacking, SEMA).

---

## §12 request-closure table

Status vocabulary: **completed · partially completed · in-progress · blocked · negative**.

| Matan/Mahmood request | status | artifact | evidence | remaining dependency |
|---|---|---|---|---|
| **use-TROPT** | completed | `docs/TROPT_PIN_AND_BYTEVERIFY.md`, `scripts/reinforce_objective/*` | TROPT pinned; prompt construction byte/token-id-identical; all REINFORCE extensions project-local (0 upstream edits). | none. |
| **use-MAC** (primary, fair vs GCG) | partially completed | `outputs/phase_c_clearharm_smoke/eval/*`, `outputs/phase3_tropt/eval_greedy/*` | MAC ran (ClearHarm smoke 0/3; AdvBench 3/20) but compute-UNMATCHED vs GCG. | compute-matched GCG-vs-MAC matrix (GPU). |
| **avoid-relying-only-on-AdvBench** | partially completed | `data/clearharm/`, `data/manifests/clearharm_*`, `docs/CLEARHARM_STATUS.md §4` | ClearHarm (exact TROPT-paper rev) vendored; 4 disjoint manifests; Gate-1 smoke. MaliciousInstruct 84/99 prior. | confirmatory baselines + frozen judge. |
| **use-greedy-evaluation** | partially completed | `docs/JUDGE_VALIDATION.md`, `scripts/judge_agreement.py` | Greedy primary throughout; freeze protocol + κ tooling + 50-row sample prepared. | **human annotation** to freeze the judge. |
| **soft-opt-first** (continuous upper bound) | **negative** | `outputs/phase_d_soft_prompt_gate3_conf/*`, `scripts/reinforce_objective/soft_prompt_reinforce.py`, `docs/REINFORCE_OBJECTIVE_REPORT.md §3` | Ceiling test done (K=4/20 steps + seeds). Delivered-harm advantage over Prefix-CE = **none** (proxy edge only, in a 256-token truncation artifact both arms share). | none — closed negative. Optional: re-confirm under frozen judge. |
| **investigate-REINFORCE-objective** | **negative** (built + evaluated) | `docs/REINFORCE_OBJECTIVE_REPORT.md`, `scripts/reinforce_objective/*` | Objective fully BUILT + reviewed (SAME §2.7 judge). Gate-1 PASS = motivation; **Gate-3 NEGATIVE** by delivered-content triangulation → Gate-4 gated off. **Not a positive result.** | none for the ceiling; frozen judge would re-confirm. |
| **extract-an-objective** (interp → objective) | **negative (both routes)** | `outputs/phase9_softopt/*`, `docs/REINFORCE_OBJECTIVE_REPORT.md` | Mechanistic route NEGATIVE (soft-opt 0.08→0.16, p≈0.67); behavioral route NEGATIVE (Gate-3). Both discrete-opt routes closed by evaluated negatives. | a causal head-mechanism (Phase F1.5) is the only remaining live route. |
| **interpret-a-real-attack** (causal?) | completed (rigorous negative) + **F1 reopening** | `outputs/phase7_causal/`, `docs/COT_HIJACKING_EXACT_MECHANISM_REPORT.md` | Predictive (AUC 0.906) not causal (uniform-temp null). Phase F1 head/position-specific probe (running) is the targeted test the uniform null did NOT rule out. | F1.3 result → F1.5 causal (GPU). |
| **attack-reasoning-models** | completed | `outputs/phase4_*`, `docs/CROSS_MODEL_COT_BENCHMARK_REPORT.md` | CoT-Hijacking on 5 models: 0.773–1.000; gemma-3-4b-it clean 0.000→1.000. | optional ClearHarm final / 5th non-CoT target. |
| **study-literature-gaps** | completed | `docs/THINKING_ATTACK_LITERATURE_MATRIX.md` | 9×17 matrix; CoT-Hijacking ≠ H-CoT ≠ Doublespeak ≠ Ben-Tov, each with arXiv id. | confirm Doublespeak-as-"context-hijacking" with Matan. |
| **attack-by-category** | partially completed | `results/SUFFIX_TAXONOMY_V2.csv`, `results/CATEGORY_TRANSFER_MATRIX_V2.csv` | E1–E3 descriptive done (goal/suffix-clustered bootstrap; misinfo universal ASR 0.246). E4–E6 controlled NOT started. | GPU (un-gated now Gate-3 resolved, but competes). |
| **use-suffix-dataset** | completed (descriptive) | `results/SUFFIX_TAXONOMY_V2.csv`, `scripts/phase_e_dataset_audit.py` | 336 suffixes reconciled from 102,897 rows/136 files; corroborates prefix-CE ≠ behavior at scale. | optional HF-direct audit (deferred). |
| **separate-single-vs-multi-instruction** | partially completed | `results/CATEGORY_TRANSFER_MATRIX_V2.csv` | Single vs multi kept strictly separate (denominators never merged) everywhere. | matched comparison on one protocol (GPU). |
| **test-CoT-Hijacking** (exact head/span mechanism) | **completed (negative — detector-only)** | `docs/COT_HIJACKING_EXACT_MECHANISM_REPORT.md §6–7`, `results/COT_F13_*.csv`, `results/COT_SPAN_STRUCTURE.csv`, `scripts/phase_f_*` | F1.1 spans + F1.2–F1.5 design done; span-structure inversion; F1.3 attention probe RAN both models. §6.3a confound screen ⇒ **Gate-5 NOT justified** (Qwen length-confounded r=0.68; Phi positional L0 + underpowered n=7) → retain **detector-only**, no distillation. | none for the call; a powered per-head probe (larger success set) could revisit. |
| **test-context-hijacking** (Doublespeak) | partially completed (design) / blocked (reference) | `docs/CONTEXT_HIJACKING_REPRODUCTION_REPORT.md`, `configs/context_hijacking/*` | Design done; released code verified (github.com/1tux/doublespeak, MIT). Reference (2512.03771) UNCONFIRMED; no run. | confirm reference; GPU reproduction. |
| **investigate-SEMA/multi-turn** | blocked (access) | `docs/SEMA_REPRODUCTION_STATUS.md`, `scripts/multiturn_simulator.py` | Access status documented; reusable simulator skeleton built (not run). | academic code access. |
| **find-a-defense** | partially completed / negative (OOD) | `outputs/phase17_detect/`, `outputs/phase_external/mech/ext_CvsD_auc.csv` | In-dist detector AUC 0.925; external transfer AUC **0.461 (chance)** → no generalization. Detector ≠ defense. | cross-family/OOD + adaptive test (GPU). |

---

## Where the sprint stands (both central hypotheses resolved — NEGATIVE)

The three routes into a distilled/optimizable attack objective are **all closed by evaluated negatives**:
the mechanistic success-direction (predictive-not-causal), the behavioral REINFORCE objective (Gate-3 NO),
and now the CoT head-mechanism (Gate-5 not justified → detector-only). The sprint's core scientific
questions are answered. What remains is either **human-blocked**, **access-blocked**, or **optional
attack-scaling**:

1. **Freeze the judge** (Phase B4 human annotation) — the single pervasive blocker; until then every
   ClearHarm/behavioral ASR is EXPLORATORY. Re-confirm the Gate-3 negative under the frozen judge.
2. **Integrity closeouts** (from the 2026-07-26 bug-hunt): report CoT-Hijacking ASRs on a consistent
   denominator + add a refusal-vs-infra provenance flag; fix the stage-4 `enable_thinking=False` silent
   no-op (confounds stage-4 refusal-direction extraction, not the headline results).
3. **Optional GPU attack-scaling** (un-gated but not required to answer the core questions): Phase E4–E6
   controlled category attacks; context-hijacking (Doublespeak) reproduction — **blocked on Matan
   confirming the reference**; SEMA — **blocked on academic code access**; cross-family/adaptive defense.

*No number in this document is fabricated. Every figure traces to a cited on-disk artifact or to
`docs/SPRINT_COMPLETION_EXECUTION_LOG.md`. Provisional/pending results are labelled as such and are not
presented as positive findings.*
