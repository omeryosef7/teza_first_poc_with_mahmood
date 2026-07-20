# Judge Validation (Phase 2 — §6.6)

Before trusting StrongREJECT as the primary judge, validate it against human labels and
freeze its version. Deliverable for `docs/RESEARCH_PLAN_DISTILLING_JAILBREAKS.md` §6.6.

## Judge under test
- **StrongREJECT** (`strong_reject/`), success threshold `strongreject_score ≥ 0.5`.
- Judge model recorded per row as `strongreject_judge_model`.
- Side-by-side lenient reference: paper string-match ASR (`scripts/paper_asr.py`), which is
  known to over-report (empty-refusal responses count as "jailbroken"). The gap between the
  two is itself a signal.

## Validation procedure
1. **Draw a stratified sample** across score bins (clear refusals, ambiguous/partial, clear
   successes) with `scripts/build_judge_validation_sample.py` — reuses EXISTING scored
   outputs, calls no judge.
   - First sheet drawn: `docs/judge_validation_sample.csv` (19 rows from the hijacking
     baselines; pool was bimodal — 219 refusals@0.0, 40 successes@1.0, only 3 partials,
     0 in the 0.01–0.5 bin). **Action:** when richer scored data exists (our own reasoning-
     model generations from Phase 4+), redraw so the `partial_lo`/`partial_hi` bins fill —
     the ambiguous band is where judge errors live.
2. **Human-annotate** the `human_label` column (`success` / `refusal` / `partial`) blind to
   the judge score.
3. **Compare** human vs. judge: confusion matrix, false-positive rate (judge=success,
   human=refusal), false-negative rate. A short script will compute these once labels exist.
4. **Freeze** the judge model + prompt version after the rates are acceptable; stamp
   `judge_version` on all subsequent rows. No judge changes after freeze without a re-run.

## Status
- ⏳ Sample drawn (`docs/judge_validation_sample.csv`); **human annotation pending** (human task).
- ⏳ Confusion-matrix script: add when labels exist (small, reuses the sample CSV).
- ⛔ Judge **not yet frozen** — do not report confirmatory ASR until it is.

## Notes / follow-ups
- The current sample is from API-model (gpt-o4-mini) hijacking baselines, not our white-box
  reasoning targets. The *judge* is model-agnostic so this still validates the scorer, but a
  redraw on Qwen3/Gemma generations is required before the confirmatory held-out evaluation
  (Phase 14).
