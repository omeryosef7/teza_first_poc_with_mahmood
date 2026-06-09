# Stage 4.5B — LLM Onset Annotation Results

**Status**: SKELETON — populate after running annotation pipeline

**CAUTION**: All results in this document are based on LLM-annotated onset indices (o4-mini).
These are exploratory findings only, not human ground truth.

---

## Pipeline Summary

| Field | Value |
|---|---|
| Annotator model | o4-mini (via OpenAI API) |
| Prompt version | `gemini_onset_v1` |
| Run timestamp | TBD |
| N examples attempted | 42 |
| Annotation rate | TBD |
| Two-pass consensus rate | TBD |
| Median agreement distance (tokens) | TBD |

## Quality Gate

```
parse_success_rate >= 0.95: TBD
provider_error_rate <= 0.05: TBD
two_pass_consensus_rate >= 0.70: TBD
median_agreement_distance <= 128: TBD

Gate result: TBD (PASS / FAIL)
```

## Onset Distribution

| Phase | Count | % |
|---|---|---|
| think | TBD | TBD |
| final | TBD | TBD |
| special | TBD | TBD |
| no_harmful_interaction_found | TBD | TBD |
| uncertain | TBD | TBD |

## Event-Aligned Dynamics (Layer 22)

*Populated after running `analyze_harmful_interaction_aligned_dynamics.py --annotation-source o4mini --allow-llm-annotations`*

- Onset-aligned refusal direction projection: TBD
- Effect size at onset (Hedges' g): TBD
- N examples contributing to event-aligned analysis: TBD

## Spotcheck Notes

*Populated after reviewing spotcheck_queue.csv*

---
*All results labeled as automated LLM annotation — not human ground truth.*
