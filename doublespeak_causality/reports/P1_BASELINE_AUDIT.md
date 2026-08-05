# P1 prerequisite — empty-generation audit of the published Phase 2.1 baseline

**Verdict: SAFE.** The published baseline stands. No re-run is required on these grounds.

## The concern

`scripts/behav_judge.py`'s differential test (tick 2) proved that **`14_behavioral_eval.py` has no `EMPTY`
label**: its `classify` lacks the `if not completion.strip(): return None, "EMPTY"` short-circuit that all
four `phase_behav_*` harnesses have, and its summary carries no `empty_rate` guard. A blank or
whitespace-only generation is therefore sent to the StrongREJECT judge and silently folded into `BENIGN`
(or `MALICIOUS` if the judge scored it ≥ 0.25).

`14_behavioral_eval.py` produced the **published Phase 2.1 baseline** — the numbers every behavioral effect
in this project is measured against. So the exposure had to be quantified before P1 could proceed.

## Method

The Phase 2.1 run dirs retain the full `response` field, so emptiness is directly reconstructible — it did
**not** have to be inferred. Emptiness was tested programmatically (`len(str(response).strip()) == 0`);
**no generation text was read, printed or quoted.** Malicious rates were then recomputed from the
per-example `label` field and compared against `reports/PHASE2_BEHAVIORAL.md`.

Run dirs: `outputs/behavioral_split_beh_clearharm` (258 rows), `outputs/behavioral_split_beh_curated`
(153 rows) — 411 generations total, 3 conditions × 86 and 3 × 51.

## Result — zero exposure

| cohort | rows | **empty / whitespace-only** | very short (<20 chars) |
|---|---|---|---|
| clearharm | 258 | **0** | 2 |
| curated | 153 | **0** | 0 |

**Not one of the 411 generations is empty.** The missing `EMPTY` branch was never reached, so it cannot
have shifted any published number.

Label distribution — clearharm: REJECTED 166 / MALICIOUS 62 / BENIGN 30. curated: REJECTED 43 /
MALICIOUS 27 / BENIGN 83.

## Every published rate recomputes exactly

| cohort · condition | n | malicious | recomputed | published |
|---|---|---|---|---|
| clearharm · direct | 86 | 10 | **0.1163** | 0.116 ✓ |
| clearharm · neutral | 86 | 22 | **0.2558** | 0.256 ✓ |
| clearharm · doublespeak | 86 | 30 | **0.3488** | 0.349 ✓ |
| curated · direct | 51 | 13 | **0.2549** | 0.255 ✓ |
| curated · neutral | 51 | 2 | **0.0392** | 0.039 ✓ |
| curated · doublespeak | 51 | 12 | **0.2353** | 0.235 ✓ |

6 of 6 match to the published precision.

## Verdict

**SAFE — the Phase 2.1 baseline is not affected by the missing-EMPTY defect.** The defect in
`14_behavioral_eval.py` is real and should still be fixed (it is a latent trap for any future run whose
conditions *do* produce blanks — e.g. strong interventions), but it has **zero exposure** on the existing
numbers, and P1 is unblocked.

## Secondary finding worth carrying forward

**Truncation is common and is much heavier on curated.** `stop_reason` distribution:

| cohort | eos | **length (truncated at max_new_tokens=200)** |
|---|---|---|
| clearharm | 193 / 258 (75%) | **65 / 258 (25%)** |
| curated | 43 / 153 (28%) | **110 / 153 (72%)** |

Roughly **three quarters of curated generations were cut off at the token limit**, versus a quarter on
clearharm. Truncation is common-mode across the three conditions within a cohort, so it does not bias the
DS-vs-direct contrast that the baseline reports. But it is a plausible contributor to the curated cohort's
odd behavior elsewhere in the project — notably the "complied-but-benign" gap (P8.0 §2.1, where curated
compliance is 1.000 while ASR is far lower) and the concept-dilution reading in
`PHASE_REFUSAL_TRAJECTORY.md`: an answer that never reaches its harmful payload before being cut off will
score low with the judge regardless of whether refusal was suppressed.

**Recommendation for P1:** raise `max_new_tokens` for the corrected baseline (the behavioral harnesses
already use 220 vs this run's 200) and **record `stop_reason` in every future behavioral run**, so
truncation can be separated from genuine benignness. Reported here rather than acted on, because changing
the generation length changes the baseline and must be a deliberate, documented decision.

## Reproduce

Structural counts only — no generation text is emitted:
`scripts/audit_phase21_baseline.py` *(pending — this audit was run inline; the script is queued for the
next tick, when subagent capacity returns)*.
Inputs: `outputs/behavioral_split_beh_{clearharm,curated}/behavioral_raw.jsonl`.
