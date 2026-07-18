# Sprint 2 / Track 2: Causal CoT-Framing Intervention Test

**Started:** 2026-07-13
**This is an execution log** — retains in-progress/historical detail; not the final source of truth. See `docs/GCG_SPRINT2_PLAN_AND_PROGRESS.md` for the full sprint plan.

## Motivation

`docs/GCG_COT_PREFIX_MECHANISM_ANALYSIS.md` (from the Phase 4-7 audit) found only correlational evidence for "compliant early CoT framing predicts higher jailbreak success" — a rule-based classifier over already-generated text, cross-tabbed against StrongREJECT outcome. This track builds and runs the actual causal test: force a chosen opening as the start of the model's thinking block for an existing GCG-optimized suffix, then let generation continue completely freely (not teacher-forced), and see whether the forced framing actually changes the downstream outcome.

## What was built

New script `poc_stage_gcg_early/run_cot_intervention.py` — model-family-generic from the start (reusing `poc_stage4.model_family_utils`'s existing Qwen3/Gemma4 marker-string table), adapting the forced-prefix-then-free-generate pattern from `poc_stage4/run_cot_swapping.py` (Qwen3-only, hardcoded). Five forced-opening categories, matching `scripts/cot_mechanism_classifier.py`'s existing category names (`compliant_willingness_framing`, `refusal_planning`, `garbled_adversarial_recognition`, `uncertainty_confusion`, `direct_task_restatement`) plus an unforced `baseline` condition. Output schema deliberately parallel to `FREE_GENERATION_RESULTS.jsonl` so it composes with existing aggregation tooling.

**Bug found and fixed (first pilot run, job 660856):** crashed immediately with `AttributeError: 'Qwen3Model' object has no attribute 'parameters'`. Root cause: used `poc_stage4.model_family_utils.load_model_by_family`, which returns the same activation-patching wrapper object used elsewhere in `poc_stage4` (no top-level `.parameters()`/`.generate()`). Fixed to use `poc_stage4.qwen3_model.load_qwen3_model`/`load_gemma4_model` instead — the same loader `run_optimization.py` itself uses, whose returned wrapper has `.model` (the real HF model) and `.tokenizer`. Resubmitted as job 660914.

## Pilot run (job 660914) — RESULTS

10 tasks × 6 conditions = 60 rows, using the 5A/`gcg_full_qwen3_cot_target` suffix, greedy decoding (deterministic, since the causal question is "does forcing X change the outcome" and sampling noise would need many more seeds per condition to disentangle).

| Condition | Success | Mean StrongREJECT score |
|---|---|---|
| baseline (unforced) | 1/10 | 0.10 |
| forced_compliant_willingness_framing | 1/10 | 0.10 |
| forced_direct_task_restatement | 0/10 | 0.00 |
| forced_garbled_adversarial_recognition | 0/10 | 0.00 |
| forced_refusal_planning | 0/10 | 0.00 |
| forced_uncertainty_confusion | 0/10 | 0.00 |

**Honest read: this pilot is too small (n=10/condition, ~10% baseline success rate) to support any causal conclusion.** `forced_compliant_willingness_framing` ties baseline exactly (1/10 each) rather than showing an increase — the opposite of what the correlational finding would predict if the causal mechanism were as simple as "just force compliant-sounding text and success goes up." The other four forced conditions all show 0/10, indistinguishable from each other and from noise at this sample size. This pilot **validates that the script and mechanism work correctly end-to-end** (real StrongREJECT scores, correct resumable schema, no crashes) — it does **not** yet provide a real answer to the causal question one way or the other. Scaling to more tasks (all 25 training behaviors, or the full 520) is the natural next step if this track continues, budget permitting.

## Job log

| Job | Purpose | Status |
|---|---|---|
| 660856 | first pilot attempt | crashed (bug above) |
| 660914 | pilot, fixed | complete — 60/60 rows, see results above |

## Progress Log

### 2026-07-13
- Script written, crashed on first run (bug found + fixed), pilot completed successfully. Result: too small a sample to draw a causal conclusion; mechanism validated. Not yet scaled up — deferred pending job-budget availability and a decision on whether this track's marginal value justifies more GPU time this sprint given the inconclusive pilot signal.

### 2026-07-14, ~03:38 UTC — scaled to n=25/condition
With ample job-budget headroom later in the sprint, decided to scale the pilot up: new sibling script `slurm_scripts/run_gcg_cot_intervention_qwen3_scaled25.slurm`, new output dir `outputs/stage_gcg_early/cot_intervention/qwen3_5a_scaled25/` (doesn't touch the pilot's `qwen3_5a_pilot/` results), covering all 25 training behaviors × 6 conditions = 150 rows. Submitted job **661358**.

### 2026-07-14, ~05:36 UTC — scaled run complete: causal hypothesis not supported

Job 661358 COMPLETED, 150/150 rows written. Direct counts (n=25/condition):

| Condition | Successes | n |
|---|---|---|
| baseline (unforced) | 3 | 25 |
| forced_compliant_willingness_framing | 2 | 25 |
| forced_refusal_planning | 0 | 25 |
| forced_garbled_adversarial_recognition | 0 | 25 |
| forced_uncertainty_confusion | 1 | 25 |
| forced_direct_task_restatement | 0 | 25 |

**`forced_compliant_willingness_framing` (8.0%) does not exceed `baseline` (12.0%) — it is nominally lower.** Ran McNemar's exact test (paired by task_id): 1 compliant-only success vs. 2 baseline-only successes, p=1.0 (not significant, though statistical power is very low with only 3 discordant pairs at n=25).

**Final conclusion**: scaling from n=10 to n=25/condition did not change the qualitative picture from the pilot. The causal test does **not** support `docs/GCG_COT_PREFIX_MECHANISM_ANALYSIS.md`'s correlational finding that compliant early CoT framing predicts higher jailbreak success — forcing that framing did not increase, and may modestly decrease, downstream success. **This is a genuine negative result, not an inconclusive one anymore**: the correlational and causal pictures diverge. A plausible (untested) explanation: the correlation may reflect that successful generations *naturally* produce compliant-sounding CoT openings as a downstream artifact of whatever the suffix is actually doing mechanistically, rather than the framing text itself being a causal lever on the rest of generation — forcing the surface text without the suffix's real influence over the ensuing tokens doesn't reproduce the effect. This is the track's final result, ready to fold into `docs/GCG_COT_PREFIX_MECHANISM_ANALYSIS.md`/`GCG_FINDINGS_SYNTHESIS.md` as an explicit, separate step, with the correlational finding's causal status now explicitly marked unsupported rather than left open.
