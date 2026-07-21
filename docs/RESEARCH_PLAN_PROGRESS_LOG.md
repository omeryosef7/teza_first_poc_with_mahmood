# Research Plan — Progress Log

Tracks execution of `docs/RESEARCH_PLAN_DISTILLING_JAILBREAKS.md` (the plan; **do not edit the plan**).
Driven by a 30-min `/loop` (cron `e2698d62`). Every entry cites concrete paths.

Working rules (from the plan's operational section):
- ≤6 SLURM runs at once; reuse known-good configs; anything PENDING >30m → cancel & resubmit.
- No unnecessary code; no duplication (reuse existing scripts/artifacts).
- After every change, fan out a bug-check subagent.
- Document every step here with path references.

Legend: ✅ done · 🔄 in progress · ⏳ queued · ⛔ blocked

---

## Phase status overview
| Phase | Title | Status |
|-------|-------|--------|
| 0 | Freeze current state | 🔄 |
| 1 | Redesign dataset split | ✅ (external_transfer deferred to Ph15) |
| 2 | Freeze evaluation protocol | ✅ (judge freeze pending human annotation) |
| 3 | Reproduce baselines in TROPT | ⛔ TROPT now in-repo but uninstalled — awaiting go |
| 4 | Real attack baseline (CoT Hijacking) | 🔄 wiring done; smoke running |
| 5+ | Mechanistic / objectives / transfer | ⏳ |

---

## Iteration log

### 2026-07-21 — Iteration 1 (loop start)
**Setup**
- Scheduled recurring loop: cron `e2698d62`, `*/30 * * * *` (session-only, 7-day expiry).
- Repo orientation. Key reusable assets identified (avoid duplication):
  - Behaviors + CoT targets: `outputs/stage_gcg_full/advbench_cot_full520_manifest.jsonl` (520 rows).
  - Category taxonomy: `scripts/gcg_advbench_llm_taxonomy.py` → `categorize()` (15 cats).
  - Canonical historical dev-25 rows: `scripts/detector_extended_audit.py:32` (`DEV_25_ADVBENCH_ROWS`).
  - Real attack ref impl: `Chain_of_Thought_Hijacking/Hijacking/` (API-based: GPT/Gemini/Claude/Grok).
  - GCG ref: `llm-attacks/`; refusal-direction ref: `Chain_of_Thought_Hijacking/refusal_direction/`.
  - StrongREJECT judge: `strong_reject/`, `scripts/paper_asr.py`, `scripts/staged_asr_rerank.py`.
  - Master synthesis of prior GCG work: `docs/GCG_JULY2026_MASTER_LOG.md` (triple-verified).

**Phase 1 — dataset split ✅**
- New script (no existing equivalent): `scripts/build_dataset_split.py`.
  Reuses the full-520 manifest + taxonomy; reuses the exact historical dev-25 so the
  held-out 495 stays genuinely unseen (plan §5.1 hard criterion).
- Outputs (plan §5.4 deliverables):
  - `data/manifests/dev_25.csv`, `dev_train_20.csv`, `dev_val_5.csv`, `heldout_495.csv`
  - `data/manifests/split_audit.md`
- Disjointness verified: exact-text overlap = 0, target-prefix overlap = 0,
  cross-split lexical near-dup clusters (Jaccard≥0.85) = 0.
- Dev-25 spans 11 categories; `dev_val_5` = {0001 cyber, 0021 violent, 0063 misinfo,
  0084 identity-theft, 0105 fraud} — one per top-5 category.
- Deferred (documented in split_audit.md): embedding-based semantic near-dup check
  (needs a sentence model); `external_transfer.csv` → Phase 15 (licensing/download decision).

**Phase 0 — freeze current state 🔄**
- `research_snapshots/2026-07-post-mahmood-meeting/` created with `code_commit.txt`
  (records HEAD; artifacts preserved in-place under git rather than byte-copied to
  avoid multi-GB duplication).
- `docs/CURRENT_STATE_AUDIT.md` — facts/hypotheses table (plan §4.4), sourced from
  `docs/GCG_JULY2026_MASTER_LOG.md`.

### 2026-07-21 — Iteration 2
**Reorient:** SLURM queue empty; TROPT **not installed** (no files, `import tropt` fails).
Phase 3 depends on it → blocked pending a decision (which TROPT — likely an external/Mahmood
repo). Phase 2 comes first in order and is CPU/API-only, so progressed that.

**Phase 2 — freeze evaluation protocol ✅** (plan §6; judge freeze still pending human labels)
- Inspected the real judge output fields first (no duplication): GCG pipeline uses
  `strongreject_score` + `strongreject_is_success` (threshold ≥0.5, per
  `scripts/compute_canonical_asr.py`), sub-scores refusal/convincingness/specificity.
- New files:
  - `configs/evaluation/greedy.yaml` (primary, deterministic) + `sampled.yaml` (secondary).
  - `schemas/evaluation_result.schema.json` — row contract, field names matched to the
    GCG pipeline; documents the legacy `is_success` mismatch in hijacking baselines.
  - `results/EXPERIMENT_REGISTRY.csv` — append-only header (plan §22.5 columns).
  - `scripts/validate_eval_results.py` — §22.4 result validator (required fields, dup rows,
    train/test split leakage, judge-score range incl. bool-reject, enum validation,
    denominator/commit consistency). Smoke-tested pass+fail paths.
  - `scripts/build_judge_validation_sample.py` — stratified judge-annotation sampler,
    reuses existing scored outputs. Produced `docs/judge_validation_sample.csv` (19 rows).
  - `docs/EVALUATION_PROTOCOL.md`, `docs/JUDGE_VALIDATION.md`.
- **Bug-check subagent** found 3 real defects → all fixed & re-verified: all-empty-pool crash
  in sampler (now clean SystemExit); `is_success` vs `strongreject_is_success` field mismatch
  (sampler now falls back across both; schema docstring corrected); bool-score accepted by
  validator (now rejected); added schema-enum validation for condition/decoding_config.
- **Deferred (documented):** judge freeze needs human annotation of the sample (human task);
  the bimodal baseline pool has ~no `partial` cases → redraw on our own Qwen3/Gemma
  generations in Phase 4+. Remaining §22.4 checks (expected row count, config-hash-matches-
  run-dir) need a run-directory context that doesn't exist yet → add with the Phase-3+ harness.
- Determinism completion criterion (§6): configured (greedy `do_sample=false`) but not yet
  GPU-verified; assert on first generation run.

**USER DECISIONS (2026-07-21, end of iter 2):**
1. **TROPT: skip for now** — reuse the in-repo GCG (`llm-attacks/`) as the discrete optimizer.
   Phase 3 will reproduce baselines with llm-attacks GCG instead of TROPT; revisit TROPT/MAC
   only if the user later supplies the repo. Plan is unchanged (do not edit it) — this is an
   execution substitution recorded here.
2. **Phase 4: the CoT-Hijacking attack is ALREADY implemented + wrapped** in-repo; API keys are
   in `.env` (OPENAI_API_KEY, GEMINI_API_KEY, HF_TOKEN). External API runs are authorized.
   → **Reuse, do not rebuild.**

**Phase 4 recon (located the existing wrapper):**
- Wrapper: `poc_stage2/hijacking_wrapper.py` (+ `poc_stage2/schemas.py`,
  `poc_stage2/validate_hijacking_artifacts.py`). Calls `Chain_of_Thought_Hijacking/Hijacking/`.
- Defaults: attacker `gemini-2.5-flash`, judge `gemini-judge`, dataset `walledai/HarmBench`
  (`standard` split), target = an **API** model (o4-mini / gpt-5-mini / claude-4-sonnet /
  gemini / grok). Prior outputs exist: `outputs/hijacking_baseline_gpt-o4-mini_*`.
- **Open design point for Phase 4 (to resolve next fire):** this wrapper is **black-box API**;
  the mechanistic distillation (Phases 5–7) needs **white-box Qwen3** activations. So either
  (a) run the RQ1 baseline on API models as-is (reproduces the paper, but can't be dissected),
  and/or (b) target local Qwen3/Gemma for the version we mechanistically analyze. Need to
  check whether the wrapper/attack can target our local HF models + accept AdvBench dev-25
  goals (`data/manifests/dev_25.csv`) instead of HarmBench. Read the wrapper's goal-loading +
  target-model path next.

### 2026-07-21 — Iteration 3
**User correction:** CoT-Hijacking is a **black-box check on the 25 examples** — it does NOT
need white-box. I over-thought the white-box/API split (white-box is only for the separate
mechanistic phases). Corrected course.

**Phase 4 — clearly located + wired the existing pipeline (reuse, no rebuild):**
- Runner already exists: `poc_stage2/collect_hijacking_results.py` → `poc_stage2/hijacking_wrapper.py:run_hijacking_slice`
  (attacker `gemini-2.5-flash`, judge `gemini-judge`, target = API model). Core attack lives in
  `Chain_of_Thought_Hijacking/Hijacking/core/` (`run_for_goal` is generic over a goal string).
  Prior outputs = HarmBench examples 1–11 only (`outputs/hijacking_baseline_gpt-o4-mini_1_11*`);
  the 25-run was **not** done yet.
- Minimal reuse extension: added optional `goals: list[str]` kwarg to `run_hijacking_slice`
  (backward-compatible; skips HF `load_goals`, reuses identical attacker/target/judge machinery).
- New driver: `poc_stage2/run_phase4_cot_baseline.py` — feeds our **dev-25 AdvBench goals**
  (`data/manifests/dev_25.csv`) through the pipeline, preserves `task_id`, writes
  `outputs/phase4_cot_baseline/phase4_cot_<model>_dev25.{jsonl,_summary.json,_taskmap.json}`.
- **Bug-check subagent: all functional checks PASS**; flagged one cosmetic off-by-one in the
  slice label → fixed (`end_example = (start_example-1)+len(goals)`).
- **Smoke** (2 goals, n_streams=1, n_iter=1, target gpt-o4-mini) launched in background to
  validate end-to-end before the full 25. litellm import is slow (~1–2 min) — expected.

### 2026-07-21 — Iteration 4
**Phase-4 smoke HUNG → killed.** The 2-goal smoke (`outputs/` never written) ran ~13 min at
**~100% CPU with 1 open fd** (CPU-bound, not waiting on API) and printed nothing → killed
(PID 2152439). Likely a compute/retry hang (litellm or huge `max_n_tokens=65535` string
handling), not productive. Re-run needs: `python -u` (unbuffered), no `| tail` (so we see
progress), a hard timeout, and probably smaller max-token settings. **Phase 4 paused** pending
that fix — and pending the TROPT decision below (which may change the whole approach).

**★ TROPT appeared in the repo** (`TROPT/`, matanbt's Textual Trigger Optimization Toolbox
v0.1.1) — was NOT present in iter 2. This is the plan's backbone. Read `TROPT/CLAUDE.md` +
`TROPT/skills/tropt/SKILL.md` (mandated entry point). Key implications for our plan (execution
notes — plan itself unchanged):
- **Phase 3**: one-call recipes `gcg__zou2023(model_name, instruction, target_response)` +
  a MAC recipe. Real TROPT, not the llm-attacks substitute.
- **Phase 8 objectives are largely PRE-BUILT** (major reuse win, minimal new code):
  `AttentionBasedLoss`/`AttentionEnhLoss` (attention-hijacking §12.4), `HiddenStateBasedLoss`/
  `SteeringActivationLoss` (success/representation direction §12.3/12.5), LM-as-judge text
  losses (semantic reward §12.6), `CombinedLoss` (composite §12.7), and
  `compute_refusal_directions(model, n_samples=128)` (refusal-dir §12.2).
- **Thinking-model target fix is a known TROPT pitfall**: Qwen3 target must be
  `"<think>\n\n</think>\n\n" + affirmative` — matches our prior 5A CoT-prefix finding.
- Black-box (API) vs white-box: `FirstTokenNLLLoss` for API targets, `PrefillCELoss` for HF.
- Budget control (`set_budget`), `TokenConstraints(disallow_non_ascii, disallow_special_tokens)`.
- Install: uses `uv`. Installed `uv 0.11.15` into poc_stage2. TROPT pins `transformers==5.8.1`
  (conflicts with poc_stage2) so it needs its own `TROPT/.venv` via `uv sync`.

**⛔ Install BLOCKED (correctly):** `uv sync` in `TROPT/` was denied by the auto-mode classifier
because the user earlier said "skip TROPT for now." TROPT appearing since then is ambiguous
(user may be setting it up, or wants it used). **Asked the user** whether to install + adopt
TROPT now. No install performed.

### 2026-07-21 — Iteration 4b (user answers: install+adopt TROPT; Phase 3 & 4 in parallel)
**TROPT install RUNNING:** `uv sync` in `TROPT/` (dedicated `TROPT/.venv`) — downloading torch
(cu126)/CUDA/transformers==5.8.1 (multi-GB), background job. Verify `list_recipes()` when done.

**Phase-4 hang ROOT-CAUSED + a regression fixed:**
- Ran the user-suggested `test_api_access.py`: it **timed out at 120s printing nothing** — it
  stalls on `import litellm` at the top. Confirmed separately: `import litellm` exceeds 90s on
  this **login node** even with `LITELLM_LOCAL_MODEL_COST_MAP=True`. This is the root cause of
  the earlier CPU-pinned "hang" (the smoke got past the guard, then stalled importing litellm /
  loading models). The prior `hijacking_baseline` outputs prove the pipeline works on a **compute
  node**, so **Phase-4 API runs must go through SLURM**, not the login node. (Also means API-key
  validity is still unconfirmed — the test never reached the API calls; SLURM run will confirm.)
- **Regression fixed:** my iter-3 off-by-one "fix" made `end_example == start_example` for
  `len(goals)==1`, tripping the `end>start` guard. Made that guard `elif` (goals path skips it —
  end_example is a label only there). `poc_stage2/hijacking_wrapper.py`. Verified by the failing
  diagnostic that exposed it; fix is a conditional guard (self-evident correctness).

### 2026-07-21 — Iteration 5 (both-in-parallel)
**Phase 4 — VALIDATED end-to-end on SLURM ✅ (RQ1 pipeline live):**
- New `slurm_scripts/run_phase4_cot_baseline.slurm` — API-only → **`cpu-killable`** partition
  (no GPU wasted, doesn't touch the 6×L40S budget). Reuses `run_phase4_cot_baseline.py`.
  Env-overridable (TARGET_MODEL/LIMIT/N_STREAMS/N_ITERATIONS/MANIFEST). Sets
  `LITELLM_LOCAL_MODEL_COST_MAP=True` defensively.
- Submitted validation slice **job 672546** (LIMIT=3, target gpt-o4-mini) → **running on a
  compute node, litellm imports fine, API keys WORK**: log shows attacker generating adversarial
  prompts + TargetLM (o4-mini) processing them. **Confirms the earlier hang was purely the
  login-node litellm import.** So: all Phase-4 CoT-Hijacking runs go via `cpu-killable` SLURM.
- Bug-check subagent on the guard fix + SLURM script + driver: **all PASS**.

**TROPT install — still downloading** (torch/CUDA wheels, slow NFS; `.venv` not yet populated).
`uv sync` (PID under btm79nmd6) still alive. Verify `list_recipes()` when it completes.

**Next iterations (in order)**
- When 672546 done → inspect its rows, confirm StrongREJECT scoring path, then submit **full
  dev-25** CoT-Hijacking baseline (LIMIT=0) + record §8.5 headroom in the registry.
- When TROPT `.venv` ready → `list_recipes()`, read `gcg__zou2023` + MAC recipe sources, then
  Phase 3 SLURM (GPU/l40s) GCG+MAC on Qwen3 dev-train-20 with the thinking-model target.
- §8.4 controls (length-/structure-matched scaffolds) as separate conditions.
- Judge confusion-matrix script once human labels exist.
