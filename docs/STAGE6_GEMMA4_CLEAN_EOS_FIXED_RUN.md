# Stage 6 Gemma 4 — Clean EOS-Fixed Run

**Date:** 2026-06-19 → 2026-06-20  
**Model:** `google/gemma-4-E4B-it`  
**Output dir:** `outputs/stage6/gemma_traces_full_1_11_eos_fixed/`  
**SLURM jobs:** 595018_0 (n-601), 595018_1 (n-602)  
**Total examples:** 220  
**Thinking enabled:** yes (`enable_thinking=True`)  
**Max new tokens:** 32768  
**Strict generation validation:** yes (`--strict-generation-validation`)

---

## Background: The Bug

The previous 220-example Gemma 4 run (`outputs/stage6/gemma_traces_full_1_11/`) was invalid.
`model.generate()` was called with `eos_token_id=tokenizer.eos_token_id` (scalar `1`), which
overwrote Gemma's native `generation_config.eos_token_id = [1, 106, 50]`. Token 106 is Gemma's
`<turn|>` end-of-turn marker. Without it in the stopping conditions, generation ran past the
valid response and produced thousands of repeated `<turn|>` tokens until `max_new_tokens=32768`.

No post-hoc repair was ever applied. Those outputs were discarded entirely.

---

## The Fix

All changes are in `poc_stage6/export_qwen_token_trace.py`:

1. **`get_effective_eos_token_ids()`** — reads `model.generation_config.eos_token_id` as the
   source of truth; ensures token 106 (`<turn|>`) is always present for `model_family=gemma4`;
   raises `ValueError` if `<turn|>` resolves to the unknown-token ID.

2. **`validate_gemma_generation()`** — checks that generation ended with a valid EOS token
   (1 or 106), that `<turn|>` appears at most once and only as the final token, and that
   `finish_reason == "eos_token"`.

3. **Parser fix** — decodes `generation_token_ids[:-1]` for semantic parsing so the terminal
   EOS token never bleeds into `final_assistant_text`. The full token sequence is preserved in
   `saved_generated_text_raw` for auditing.

4. **StrongREJECT gate** — `run_allowed=generation_is_valid` ensures the judge only scores
   outputs that passed native generation validation.

5. **`--strict-generation-validation`** CLI flag — raises `RuntimeError` immediately on any
   invalid generation instead of continuing (used in both smoke and full run).

No post-hoc cleaning, no `text.split("<turn|>")`, no `final_answer_clean` field.

---

## Smoke Test Results (job 594977)

**15 examples**, output to `outputs/stage6/gemma_turn_stop_smoke/`

| Metric | Result |
|---|---|
| Files written | 14/15 (example 2 lost to transient NFS EDQUOT error; generation itself was valid) |
| `generation_is_valid=True` | 15/15 (all generation log lines) |
| `finish_reason=eos_token` | 15/15 |
| `last_token_id=106` | 15/15 |
| `max_new_tokens` finishes | 0 |
| Repeated `<turn|>` tokens | 0 |

**Assessment:** EOS fix confirmed. The missing file was an NFS write error unrelated to
generation quality.

---

## Full Run Results

**220 examples**, output to `outputs/stage6/gemma_traces_full_1_11_eos_fixed/`

### Generation Quality (all 220 must pass — hard requirements)

| Metric | Result |
|---|---|
| Total files | 220 |
| `generation_validation_status=valid` | **220/220 (100%)** |
| `finish_reason=max_new_tokens` | **0** |
| Repeated `<turn|>` tokens | **0** |
| Empty `final_assistant_text` | **0** |
| `<turn|>` present in `final_assistant_text` | **0** |
| `think_text` missing | **0** |
| StrongREJECT scored | **220/220 (100%)** |
| StrongREJECT `not_run` | **0** |

**All hard requirements satisfied.** Every example stopped natively at token 106 (`<turn|>`),
produced a non-empty thinking chain and final answer, and was scored by StrongREJECT.

### Generation Token Statistics

| | Tokens |
|---|---|
| Min | 694 |
| Max | 14,558 |
| Mean | 5,965 |

The range reflects genuine variation in Gemma's reasoning depth across goals. No example hit
the 32,768 ceiling.

### Attack Effectiveness (StrongREJECT)

| Metric | Result |
|---|---|
| Mean StrongREJECT score | 0.2892 |
| Score > 0 (partial attack success) | 67/220 (30.5%) |
| Score = 1 (full attack success) | 56/220 (25.5%) |
| Refusal = 0 (model did not refuse) | 79/220 (35.9%) |
| Refusal = 1 (model refused) | 141/220 (64.1%) |
| Gemini judge positive | 0/220 |

---

## Comparison to Previous Gemma 4 Run

| | Old run (`gemma_traces_full_1_11/`) | This run (`…_eos_fixed/`) |
|---|---|---|
| `eos_token_id` passed to `generate()` | `1` (scalar, overwrote native list) | `[1, 106, 50]` (native list) |
| Generation valid | ✗ (all ran to 32,768 tokens) | ✓ 220/220 |
| Terminal token | repeated `<turn|>` spam | single `<turn|>` (token 106) |
| `final_assistant_text` clean | ✗ | ✓ |
| StrongREJECT scored | ✗ (outputs were malformed) | ✓ 220/220 |

---

## Timing

| | |
|---|---|
| Task 0 started | 2026-06-19 ~14:06 IDT |
| Task 1 started | 2026-06-19 ~14:06 IDT |
| Task 0 finished | 2026-06-20 00:49 IDT (~10.7h) |
| Task 1 finished | 2026-06-20 02:14 IDT (~12.1h) |
| Total wall time | ~12.1h (two parallel A6000 GPUs) |

---

## Files

```
outputs/stage6/gemma_traces_full_1_11_eos_fixed/
  ├── gemma_4_e4b_it_trace_goal_index_*.json   # 220 artifact files
  ├── batch_summary.json                        # per-run summary from both tasks
  └── monitor_log.txt                           # hourly monitoring log
```

Each artifact contains:
- `saved_generated_text_raw` — full token decode including terminal EOS
- `think_text` — extracted CoT from `<|channel>thought` channel
- `final_assistant_text` — clean final response (no `<turn|>`)
- `generation_token_count`, `generation_finish_reason`
- `effective_eos_token_ids` — `[1, 106, 50]` for every example
- `last_generated_token_id` — `106` for every example
- `gemma_generation_validation` — per-example validation dict
- `generation_validation_status` — `"valid"` for all 220
- `strongreject_result` — full StrongREJECT scoring record
- `external_judge_result` — Gemini 2.5 Pro judge result

---

## Unit Tests

`poc_stage6/tests/test_gemma4_eos_fix.py` — 16 tests, all passing:

```
conda run -n poc_stage2 python -m pytest poc_stage6/tests/test_gemma4_eos_fix.py -v
```

Covers: `normalize_eos_token_ids`, `get_effective_eos_token_ids`, `validate_gemma_generation`,
StrongREJECT `run_allowed` gating, and semantic validity checks.
