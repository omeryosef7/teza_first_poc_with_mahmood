# Stage 4.5B — LLM Onset Annotation Results

**Status:** `blocked_by_provider_safety_filtering`
**Date documented:** 2026-06-10

---

## Summary

Stage 4.5B attempted to use an LLM judge (Gemini 2.5-flash via LiteLLM) to annotate the token-level onset of harmful content compliance in Qwen3-14B reasoning traces. The pilot was blocked by provider-side safety filtering that truncates responses when input text contains CBRN-related content. This is an engineering limitation, not a scientific result about Qwen3-14B behavior.

Event-aligned onset analysis is **deferred**.

---

## What was attempted

The annotation pipeline:
- Input: reasoning chunks (think-phase token windows) from 42 Stage 4 / Stage 6 attack examples
- Task: identify the token index where Qwen's reasoning first shifts from hesitation toward compliance
- Model: `gemini-2.5-flash` via Google Generative Language API
- Passes: 3 annotation passes per example with consensus aggregation
- Code: `poc_stage4_5/` (exists and is functional)

---

## Evidence of provider safety filtering

**SLURM job:** 527217 (completed, no longer in queue as of 2026-06-10)

**Log files:**
- `logs/stage4_5b_llm_annotate_527217.err` — 2770 lines of LiteLLM INFO/WARNING output
- `outputs/stage4_5/llm_harmful_interaction_annotations/run_20260610_081646/logs/run.log` — 6658 lines

**Observed pattern:**
```
INFO HTTP Request: POST .../gemini-2.5-flash:generateContent "HTTP/1.1 200 OK"
WARNING JSON decode error (attempt 1/3): Unterminated string starting at: line 3 column 3 (char 40)
WARNING JSON decode error (attempt 2/3): Unterminated string starting at: line 3 column 3 (char 40)
WARNING JSON decode error (attempt 3/3): Unterminated string starting at: line 3 column 3 (char 40)
INFO   -> status=no_harmful_interaction_found idx=None confidence=0.70
```

The API returns HTTP 200 (not an error code), but the response body is truncated at ~40 characters — a signature of Gemini's output safety filter cutting off generation mid-JSON. The fallback default label `no_harmful_interaction_found` is therefore **not a valid annotation**.

**Partial output statistics:**
- Examples attempted: 20 / 42
- `raw_passes.jsonl`: 20 rows
- Rows with `annotation_status=no_harmful_interaction_found`: 20 / 20
- Rows with non-null `annotation_result`: **0 / 20**
- `consensus_annotations.json`: 0 usable consensus rows

---

## What the partial output is NOT

- Not human ground truth
- Not a usable LLM annotation
- Not evidence that harmful interaction onset does not occur in the traces
- Not a scientific result about Qwen3-14B

The 20 `no_harmful_interaction_found` labels are artifacts of the safety filter, not genuine detections.

---

## Archived partial artifacts

All partial output is archived at:
```
outputs/stage4_5/llm_harmful_interaction_annotations/run_20260610_081646/
```

Do not use these for analysis. The directory is preserved for engineering documentation purposes.

---

## What exists

- **Onset-analysis code:** `poc_stage4_5/` — the annotation pipeline is implemented and working at the infrastructure level
- **Reasoning traces:** All 42 Stage 4 think-phase traces are available
- **The pipeline would work with a provider that does not safety-filter the annotation context**

---

## Why the annotation is blocked

The annotation task requires sending Qwen's raw reasoning text (which contains procedural CBRN content) to the judge model as part of the annotation context. Standard Gemini endpoints apply output safety filtering when such content appears in the input, truncating the JSON response and preventing valid annotation.

Workarounds not attempted in this sprint (and not planned for the current phase):
- GPT-4o (requires separate API key and spending authorization)
- Claude (self-annotation; potential conflict of interest in safety research context)
- Vertex AI (same Gemini model, likely same filter)
- Local LLM judge (no suitable instruction-following model available on cluster)

---

## Impact on current research

- **Stage 4.7 (multi-prompt replication):** not blocked — uses StrongREJECT as primary behavioral evaluator
- **Meeting-ready findings:** the onset analysis was always secondary; the primary mechanistic signal is the Layer-22 projection trajectory, which does not require LLM annotation
- **Future work:** onset annotation could be revisited with a provider that supports research-exemption content policies, or with a locally-hosted judge model

---

## Next decision

Do not retry annotation providers in the current sprint. Proceed with:
1. Completing Stage 4.6 audit and meeting figures
2. Implementing Stage 4.7 multi-prompt replication
3. Computing selected-layer projection dynamics on Stage 4.7 outputs
