# Stage AE — Implementation Audit

Written during the poc_stage_ae build session (2026-07-02). Documents code
reused vs newly added, schemas, and design decisions for each of the 7
components built in this session (Stages 1-3, part of Stage 4/5, Stage 6/7 per
the approved plan's numbering; note the file-list numbering in the task spec
differs slightly from the plan's stage numbering — this doc uses the task
spec's file numbering 1-9 to avoid ambiguity).

## 1. `poc_stage_ae/build_ae_manifest.py`

**Reused:** condition-construction logic pattern (A/D/E/G text selection,
`enable_thinking` mapping, `transformation_method` labels) from
`poc_stage4_8/build_extended_replication_prompts.py` and
`poc_stage4_8/build_manifest_condition_g.py`; `source_example_id` format from
the plan's confirmed convention (byte-for-byte match with existing
`prompt_id` usage).

**New:** full 220-row x 3-seed x {A,E} + 11-goal x 3-seed x {D,G} manifest
construction in one pass; hard assertion gate (exact 1386/model, 2772 total,
zero duplicate row_keys) that exits non-zero before any file write if counts
are wrong; sha256 verification of the canonical dataset file itself (refuses
to build from a changed/unexpected source); `resolved_run_config.json` with
git commit, model configs, and per-condition sizing recorded.

**D/G canonical-representative rule:** one row per `goal_index`, selected as
the row with the lexicographically smallest `(attack_iteration,
conversation_id)` tuple in the canonical 220-row dataset. Its real
`source_example_id` (not a synthetic `goal_index={gi}|direct_control` id) is
reused for the D/G manifest rows of that goal, keeping every row traceable to
one real canonical source row while avoiding the 10x D/G inflation the plan
explicitly flags as a risk to avoid.

**Verified output (this session, real run, CPU-only):**
TIMESTAMP=`20260702_095452`; both models exactly 1386 rows (A=660 E=660 D=33
G=33); 2772 combined; 0 duplicate row_keys. See
`outputs/stage_ae_early_token_expansion/full_20260702_095452/`.

## 2. `poc_stage_ae/thinking_position_utils.py`

**Reused:** `THINKING_MARKERS_BY_FAMILY`, `get_thinking_start_token_ids`,
`get_thinking_end_token_ids` from `poc_stage4/model_family_utils.py` — marker
strings are encoded via the live tokenizer at call time, never hardcoded as
token IDs.

**New:** sliding-window token-ID subsequence search (`_find_subsequence`);
7-position schema for thinking-enabled rows (`prefill_last`, `startofthink`,
`think_content_1/2/3`, `endofthink`, `endofresponse`); 5-position schema for
thinking-disabled rows (`prefill_last`, `answer_content_1/2/3`,
`endofresponse`); explicit non-raising error-code contract
(`start_marker_not_found`, `end_marker_not_found`,
`end_marker_before_start_marker`, `insufficient_think_content_tokens`,
`insufficient_answer_content_tokens`, `empty_generation`, `empty_prompt`) — a
missing marker always yields `None` + an error code, never an exception, so
one bad row cannot crash a shard.

## 3. `poc_stage_ae/run_ae_generation.py`

**Reused verbatim (copied, not imported, to avoid coupling to
`poc_stage4_8` internals that may change independently):**
`_get_effective_eos_ids` (Gemma scalar-EOS bug fix), the
`apply_chat_template(..., enable_thinking=...)` try/except TypeError pattern,
`_parse_gemma4_thinking`, `_parse_think_tags`, `_finish_reason` — all copied
from `poc_stage4_8/run_repeated_generations.py` and `poc_stage2b/runner.py`
with identical logic (only renamed/relocated, no behavior change).

**New:** per-row explicit RNG seeding across python `random`, `numpy`,
`torch` (CPU+CUDA), and `transformers.set_seed` (the precedent code only
called `torch.manual_seed`); span-position location + caching via
`thinking_position_utils.locate_positions` at generation time (written into
the output row so replay never re-derives spans from text); one shard file
per `(model, condition, goal_index)` under `shards/`, append-and-flush per
row, resumable via `row_key` + `status == "ok"` lookup; per-row exception
isolation (a failed row is logged with `status="error"` and full traceback,
the shard continues); SLURM/host/GPU metadata and git commit recorded per row.

**Schema (one JSON object per line in `shards/{model}_{condition}_goal{N}.jsonl`):**
`row_key, status, model, model_name_or_path, model_revision, git_commit,
goal_index, goal, source_example_id, condition, seed, enable_thinking,
do_sample, temperature, top_p, max_new_tokens, user_message_text,
formatted_input_text, input_token_ids, input_token_count,
generation_token_ids, generation_token_count, generation_text, think_text,
final_text, think_token_count, final_token_count,
thinking_segmentation_status, finish_reason, positions, position_errors,
generation_duration_seconds, eos_diagnostics, exception, hostname, gpu_name,
slurm, created_utc`.

## 4. `poc_stage_ae/replay_hidden_states.py`

**Reused:** the forward-pre-hook capture pattern from
`poc_stage4/analyze_stage6_token_dynamics.py`
(`get_residual_projection_pre_hook` / `compute_projections_for_example`) —
adapted from "project onto one direction and discard" to "detach, move to
CPU, cast fp16, keep the raw vector." The layer-lookup logic (
`model.layers`, `model.language_model.layers`, ... fallback chain) mirrors
`Qwen3Model.layers` in `poc_stage4/qwen3_model.py`.

**New:** captures ALL layers in a single forward pass (one hook per layer,
not one hook per selected layer as in the token-dynamics precedent, since
this stage needs the full residual stream, not a scalar projection); adds a
forward *hook* (not pre-hook) on the last layer to capture the final hidden
state (index `n_layers`), giving the full `[n_layers+1, d_model]` stack
matching `output_hidden_states=True` semantics; `--verify-equivalence` flag
runs both the hook path and a reference `output_hidden_states=True` forward
pass on up to `--verify-n-examples` rows and asserts `torch.allclose` (bf16
tolerance rtol=1e-2, atol=1e-2) at a sample of cached positions across all
layers, printing PASS/FAIL per row and an overall summary — **not yet run**
in this session (no GPU access); this is the mandatory Stage 8 smoke-test
gate per the plan and must be executed and confirmed PASS before trusting
hidden-state output at scale.

**Layer-0 convention (stated explicitly per plan requirement):** hidden-state
index 0 = embedding output (captured as the *input* to decoder layer 0 via
forward pre-hook); index `i` for `1 <= i <= n_layers-1` = output of decoder
layer `i-1` = input to decoder layer `i`; index `n_layers` = output of the
final decoder layer (captured via forward hook, not pre-hook, since there is
no "layer n_layers" to pre-hook on). This is consistent for both Qwen3 (41
total: 0-40) and Gemma4 (43 total: 0-42).

**Output schema:** per-shard tensor
`hidden_states/shards/{model}_{condition}_goal{N}.pt`, shape
`[n_rows, n_positions=10, n_layers+1, d_model]` fp16, where the 10 position
slots are the union of all A/D/E/G position names
(`_ALL_POSITION_NAMES_UNION`); slots not applicable to a given row's
condition (e.g. `startofthink` for an E/G row) or with a `None`/errored
position are filled with NaN so tensor shape stays uniform across mixed-
condition shards. Metadata index
(`hidden_states/shards/{model}_{condition}_goal{N}_metadata.{parquet,csv}`)
has one row per `(row_key, position_name)` with shard path, row/position
offsets, token id/string, layer_count, hidden_dim — written as parquet if
`pyarrow` is importable, else CSV (this dev environment has neither pandas
nor pyarrow installed; the SLURM `poc_stage2` conda env was not checked in
this session — the CSV fallback path was exercised implicitly via the
`ImportError` branch's static structure, not run end-to-end, since no GPU/
model access was available to produce real hidden states here).

## 5. `poc_stage_ae/score_ae_outputs.py`

**Reused:** `poc_stage3/strongreject_scoring.py` (`load_strongreject_evaluate`,
`score_single_row`) unmodified, called the same way
`run_repeated_generations.py._score_strongreject` calls it; `_REFUSAL_KW` /
`_score_text` pattern copied verbatim from
`poc_stage4/run_p11_controlled_patching.py` for the `explicit_refusal` field.

**New:** the remaining 9 taxonomy fields
(`puzzle_solved`, `harmful_goal_identified`, `implicit_refusal`,
`harmful_compliance`, `safe_but_relevant_answer`, `irrelevant_or_confused`,
`truncated`, `empty_or_malformed`, `marker_parsing_error`) as deterministic
keyword/regex heuristics — full design rationale and known limitations are
documented in the module docstring of `score_ae_outputs.py` itself (not
duplicated here; see that file). All heuristic fields are tagged
`annotation_confidence="heuristic"`, `annotation_method="keyword_heuristic_v1"`
per spec, explicitly flagging this as a v1 pass, not an LLM judge.
Resumable by `row_key` against `scoring/{model}_scores.jsonl`.

## 6. `poc_stage_ae/audit_ae_run.py`

**Reused:** the general row_key-based completed-set pattern from
`poc_stage4/run_state.py` (`completed_rows_by_key`), generalized here to scan
across shard files rather than a single checkpoint file.

**New:** three independent scan functions
(`_scan_generation_shards`, `_scan_hidden_states`, `_scan_scoring`) so the
audit can report generation/replay/scoring completion independently per
`(model, condition, goal_index)` cell; writes `resume_targets.jsonl` (one row
per incomplete cell with `n_missing`) and `completion_audit.json` (full
table + global totals); prints a human-readable stdout table. Verified in
this session against the real 20260702_095452 manifests (see report) —
correctly reports all 88 cells / 2772 rows as pending pre-launch.

## 7-9. SLURM + resume/status wrapper scripts

See `docs/SLURM_AND_MODEL_AUDIT.md` for full detail on array indexing,
wall-time choices, and reuse of the `stage4_8_cond_g_*` precedent scripts.

## What was NOT run in this session (explicitly out of scope per constraints)

- No SLURM jobs submitted.
- No GPU code executed (model loading, generation, hidden-state replay).
- No StrongREJECT/OpenAI API calls made.
- `--verify-equivalence` in `replay_hidden_states.py` has not been executed —
  this is the Stage 8 smoke-test gate and must run (and PASS) before the
  hidden-state pipeline is trusted at scale, per the plan's explicit risk
  callout on layer-0 convention drift.
