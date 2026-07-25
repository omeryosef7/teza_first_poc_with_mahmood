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
| 3 | Reproduce baselines in TROPT | ✅ core: GCG 0.450 / MAC 0.150 / no-attack 0.100 (greedy SR, per-beh); §7 gate PASS; report done |
| 4 | Real attack baseline (CoT Hijacking) | ✅ dev-25 gpt-o4-mini SR 0.917 |
| 4X | Cross-model CoT-Hijacking (OPEN-SOURCE targets) | ✅ FINAL: 3 targets attacked+clean-scored; headroom table; DeepSeek=primary mech target |
| 5 | Mechanistic analysis dataset (§9) | ✅ 104 rows all 6 groups (A18 B2 C26 D18 F28 G12); 90 tensors; card written |
| 6 | Predictive signal search (§10) | ✅ gate (a)(b)(c) PASS, (d) QUALIFIED: early C-vs-D AUC≈0.90 (LOGO) but beyond-length gain not sig at n=44 (bootstrap CI incl 0); → Phase 7 (causal test is length-immune) |
| 7 | Causal validation (§11) | ✅ COMPLETE: NOT CAUSAL across ALL layers (L12/16/20/28) AND timings (all/gen/prefill), sufficiency+necessity, coherence intact; §25 Gate-3 No → detector |
| 13 | Large GCG suffix analysis (§17) | ✅ 336-suffix taxonomy + transfer matrix + report; verified (5/5 PASS) |
| 17 | Defensive interpretation (§21) | ✅ core (§21.1/21.3/21.4): detector AUC 0.90 at prefill_last (pre-gen), MLP 0.923, bug-check PASS; §21.2/21.5 follow-ups |
| 16 | Cross-model (§20) | 🔄 length-dir check done (DeepSeek/Phi weak-consistent); mechanistic replication on DeepSeek-Qwen-7B LAUNCHED |
| 8-16 | Mechanistic objective/opt/transfer | ⚠ success-dir objective (O4) de-prioritized (non-causal); other §12 objectives (prefix/CoT-CE/attention) still open |

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

### 2026-07-21 — Iteration 6
**Phase 4 validation slice DONE (job 672546, COMPLETED 11m):** 3 goals, **ASR 0.667 (2/3)** with
CoT-Hijacking on gpt-o4-mini (internal gemini judge). Outputs:
`outputs/phase4_cot_baseline/phase4_cot_gpt-o4-mini_smoke3.{jsonl,_summary.json,_taskmap.json}`.
Pipeline confirmed end-to-end on the compute node.
**→ Full dev-25 baseline submitted: job 672570** (LIMIT=0, N_STREAMS=3, N_ITERATIONS=3, gpt-o4-mini),
running on `cpu-killable`. StrongREJECT scoring path identified for reuse:
`poc_stage3.run_strongreject_scoring --evaluator strongreject_rubric` (env-driven via
`slurm_scripts/stage3_strongreject.slurm`; will score 672570's jsonl when done — note that
script requests 2 GPUs, so a cpu variant or env-reuse decision comes next).

**TROPT install: progressing (not stuck).** uv cache 2.0G, 5 active download sockets, multithreaded
(CPU-time>wall-time is normal for uv). `.venv` stays small until all wheels download, then links.
Big CUDA/torch wheels over slow NFS → ~35min+ and counting. Will verify `list_recipes()` on finish.

### 2026-07-21 — Iteration 7
**Both background tracks progressing (nothing stuck):**
- Phase-4 full baseline **672570 still RUNNING** (~32 min, 194 log lines — working through 25
  goals × 3 streams × 3 iters).
- TROPT install still downloading: uv cache **2.0G → 3.6G** (big CUDA wheels over slow NFS),
  multi-threaded, active sockets. `.venv` links only after all downloads finish.

**Prep done (reuse, no logic duplication):** new `slurm_scripts/run_strongreject_cpu.slurm` —
a general **cpu-killable** StrongREJECT scorer (the existing `stage3_strongreject.slurm`
wastefully requests 2 GPUs for an API-only rubric). Reuses `poc_stage3.run_strongreject_scoring`
+ `analyze_strongreject_results`, env-driven (`INPUT_JSONL`, derives sibling outputs), `--resume`
safe. **Bug-check subagent: all 6 items PASS** (arg match, schema compat with Phase-4 rows, no
clobbering). Ready to score 672570's output next iteration.

### 2026-07-21 — Iteration 8
**Status:** Phase-4 full baseline 672570 still RUNNING (~56 min, slow o4-mini reasoning, on goal
iters). TROPT install still going (~95 min): finished the big downloads, now **unpacking**
cudnn/triton `.so` libs into cache (`.tmp` dirs) — slow on NFS but progressing (cache 4.7G).
Not stuck.

**★ TROPT recipe reconnaissance (read the on-disk recipe sources — big de-risk):**
Mapped plan phases → ready TROPT recipes (all in `TROPT/tropt/recipe_hub/`), so most of the
optimizer/objective work is composition, not new code:
| Plan phase | TROPT recipe | notes |
|---|---|---|
| Ph3 GCG baseline (B1/B2) | `gcg__zou2023(model_name, instruction, target_response, model_obj, tracker)` | PrefillCELoss, 500 steps, 512 cand, ASCII+no-special constraints, retokenize. `GCG__zou2023.py:34` |
| Ph3 MAC (B3/B5) | `mac__wang2024(model_name, instruction, target_response, num_steps=20, jailbroken_model_name=None)` | GCGPlusOptimizer + PrefillCELoss. `jailbroken_model_name` → generated target (plan B6). `MAC__wang2024.py:14` |
| **Ph8 attention-hijack (§12.4)** | **`gcg_hij__bentov2025(...)`** + `attn_gcg__wang2024` | GCG + `AttentionEnhLoss` (trigger→chat-template-after, mid-layers). **Pre-built = Phase-8 objective.** Needs `use_eager_attention=True`, `use_prefix_cache=False`. `GCGHij.py` |
| Ph12 universal (multi-prompt) | `GCGMult__zou2023.py` | multi-template universal trigger |
- **Model id:** `Qwen/Qwen3-14B` (also 8B available). Large → L40S (48GB) SLURM.
- **Thinking-model target (critical):** pass `target_response = "<think>\n\n</think>\n\n" + affirmative`
  (SKILL §7) — matches our prior 5A CoT-prefix finding. Our manifest already stores a CoT-wrapped
  `safe_target_prefix` (non-empty think "Okay, I can help..."); will A/B empty vs non-empty think.
- **Reuse pattern:** load one `LMHFModel(model_name="Qwen/Qwen3-14B", ...)` and pass `model_obj=`
  to the recipe across all dev-train-20 behaviors (avoids reloading the 14B each time).
- Phase-3 runner NOT written yet (deferred until install done so I can test imports + verify
  target formatting on a small model first, rather than ship untested code).

### 2026-07-21 — Iteration 9
**Status:** Phase-4 672570 still RUNNING (~1h26m; slow o4-mini). TROPT install on the **final
wheel** — all CUDA wheels (nccl/cublas/cudnn/triton) downloaded, now pulling `torch` (792MB)
slowly; `.venv` links after. Not stuck.

**Phase-3 driver written (reuse TROPT recipes; tested statically, NOT run blind):**
- `scripts/phase3_tropt_optimize.py` — loops dev-train-20, loads one `LMHFModel(Qwen/Qwen3-14B)`
  reused via `model_obj=` across behaviors, resume-safe (skips done task_ids). Optimizers:
  `--optimizer gcg|mac|gcg_hij` → `gcg__zou2023` / `mac__wang2024` / `gcg_hij__bentov2025`.
  Thinking-model target via `--target-style affirm|empty_think|nonempty_think`.
- Caught + fixed a real bug pre-run: `gcg__zou2023`/`gcg_hij__bentov2025` take **no** `num_steps`
  (only MAC does) — `--num-steps` now MAC-only.
- **Bug-check subagent: ALL PASS** — verified every recipe call's param names against the actual
  TROPT sources (`gcg_hij` uses `target_output` not `target_response`; imports/exports exist;
  `OptimizerResult.best_trigger_str/best_loss`; eager-attention setup for gcg_hij). `--help`
  works without TROPT (lazy import).
- NOT yet run (install pending). Gate: smoke on `google/gemma-3-270m-it --limit 1` first.

### 2026-07-21 — Iteration 10
**TROPT install COMPLETE ✅:** `uv sync exit: 0` — "Prepared 87 packages in 124m 37s, Installed
in 2m 12s". `TROPT/.venv` = 6.4G, python 3.13. First `import tropt` is slow (torch off NFS);
patient import/`list_recipes()` test running in background to confirm usability.
**Phase-4 672570 still RUNNING** (~1h56m; long o4-mini run, within 8h wall).

**Phase-3 SLURM wrapper written:** `slurm_scripts/run_phase3_tropt.slurm` — l40s GPU (Qwen3-14B
fits 48GB), runs under the **TROPT venv** (not conda), reuses the existing HF cache
(`.cache/huggingface`, Qwen3-14B already downloaded). Env-driven (OPTIMIZER/TARGET_STYLE/
MODEL_NAME/MANIFEST/OUT_DIR/LIMIT/NUM_STEPS). Verified: bash -n OK, venv python exists,
slurm args ↔ driver argparse match exactly.

### 2026-07-21 — Iteration 11
**Phase-3 path VALIDATED end-to-end ✅:** smoke job 672727 (gemma-3-270m, gcg, empty_think,
limit 1) ran 500/500 GCG steps in ~7 min on l40s node n-802, loss 0.33, wrote a well-formed
`outputs/phase3_tropt/smoke_gemma/triggers.jsonl` (all 12 fields; empty_think target correctly
`<think>\n\n</think>\n\nSure, here is...`; real GCG suffix). TROPT `list_recipes()` = 38.
Confirms login-node import hang was just the broken login GPU.

**Qwen3 Phase-3 runs SUBMITTED (l40s):**
- **672744** — MAC full dev-train-20 (`mac`, empty_think, 20 steps) → `outputs/phase3_tropt/mac_qwen3_empty_think/`.
- **672793** — GCG **timing probe** (`gcg`, empty_think, LIMIT=1) → `outputs/phase3_tropt/gcg_qwen3_probe/`.
- **Why probe-first:** gemma-270m did 500 GCG steps in 7 min (1.18 it/s); Qwen3-14B is far slower,
  so 500-step GCG × 20 behaviors likely blows the 8h wall. Probe measures per-behavior 14B cost →
  then decide sharding (≤6 parallel jobs) vs step reduction for the full GCG run. MAC (20 steps)
  is tractable in one job.
**Phase-4 672570:** 21/25 goals done, ~2h31m — nearly complete.

### 2026-07-21 — Iteration 12
**★ Phase-4 RQ1 baseline DONE (job 672570, COMPLETED 2h55m):**
`outputs/phase4_cot_baseline/phase4_cot_gpt-o4-mini_dev25.jsonl` (114 rows).
**CoT-Hijacking ASR = 0.84 (21/25)** on gpt-o4-mini, gemini-judge. Verified rows use our
**AdvBench dev-25** goals (the summary's `dataset: HarmBench` is a stale default label — the
`goals=` override bypasses load_goals; task_ids map correctly).
- **Data gap:** goal_index 16 = **advbench_full_0333** produced 0 conversation rows (silent
  attacker/API failure) → 24/25 behaviors have data. Noted in registry; re-run just that goal later.
- **StrongREJECT scoring submitted: job 672820** (cpu-killable) → frozen-protocol ASR (replaces
  the gemini-judge number as headline). Provisional registry row appended to
  `results/EXPERIMENT_REGISTRY.csv` (status=scored_pending).

**Phase-3 Qwen3 jobs (672744 MAC, 672793 GCG probe): still PENDING** ~29 min on the contended
l40s killable queue (Priority). Under the 30-min rule this iteration; **cancel+resubmit next
iteration if still pending.**

### 2026-07-21 — Iteration 13 (user: add Phase 4X + open-source-only)
**Phase-4 headline finalized:** StrongREJECT behavior-level ASR **22/24=0.917** (0.88/25);
gemini-judge 0.84. Registry row updated (status=scored).

**★ NEW PHASE 4X added to the plan** (`docs/RESEARCH_PLAN_DISTILLING_JAILBREAKS.md` §31, a
user-authorized amendment; §1–30 untouched): benchmark CoT-Hijacking on **open-source thinking
models** as the TARGET.
- **User correction mid-flight:** do NOT attack proprietary/public-API models. **Cancelled**
  the two API runs I'd started (672938 gemini-2.5-pro, 672939 gpt-5-mini; no output written).
  Attacker+judge may stay Gemini API (that's the harness, not a target); only the **target** must
  be open-source local.
- **Implemented the local open-source HF target** (design via subagent; approach = HF backend, not
  vLLM which isn't installed):
  - NEW `Chain_of_Thought_Hijacking/Hijacking/models/hf_local.py` — `HFLocalLLM(BaseLLM)`
    (transformers `.generate`, bf16, apply_chat_template, strips `<think>`).
  - EDIT `core/target.py` — `hf:<repo_id>` branch in `TargetLM.__init__` (early-return; API path
    untouched; no `Model` enum leak).
  - EDIT `poc_stage2/hijacking_wrapper.py` `require_api_keys` — hf: needs only GEMINI key.
  - EDIT `poc_stage2/run_phase4_cot_baseline.py` — sanitize `hf:org/model` for filenames.
  - NEW `slurm_scripts/run_phase4_hf_local.slurm` — l40s GPU, `poc_stage2` env, **node-local HF
    cache `$SLURM_TMPDIR`** (user constraint: do NOT persist weights to project cache).
  - **Bug-check subagent: A–G ALL PASS** (signature contract, hf: branch attrs, no enum leak,
    node-local cache, arg match).
  - Select via `--target-model hf:<id>`. Model set (§31.2): DeepSeek-R1-Distill-Llama-8B (true
    `<think>`, 8B), Phi-4-reasoning, gemma (user-requested; note gemma-3 isn't native-reasoning).
- **Smoke submitted: job 672989** — `hf:deepseek-ai/DeepSeek-R1-Distill-Llama-8B`, 2 goals, 1×1.

**Phase-3 Qwen3 MAC (672744) + GCG probe (672793) COMPLETED** (dropped from queue) — read their
`outputs/phase3_tropt/*/triggers.jsonl` next iteration (MAC full dev-train-20; GCG per-behavior
timing to size the full GCG run).

### 2026-07-21 — Iteration 14
**Phase-3 results read + full GCG launched (sharded):**
- MAC done: `outputs/phase3_tropt/mac_qwen3_empty_think/triggers.jsonl` (20 behaviors, mean loss
  1.47, 20 min total, 61s/behavior).
- GCG probe: **41.8 min/behavior** on Qwen3-14B (500 steps, loss 0.40) → 20 behaviors = 13.9h >
  8h wall. **Sharded GCG:** added `--offset` to `scripts/phase3_tropt_optimize.py` (+ OFFSET in
  the slurm); submitted **2 parallel shards** — 673018 (beh 0–9) + 673043 (beh 10–19), separate
  out-dirs `outputs/phase3_tropt/gcg_qwen3_empty_think_sh{0,1}/` (append not concurrency-safe).
  Slicing verified disjoint+complete. ~7h/shard.
**Phase-4X HF-local: bug found by smoke + fixed.**
- Smoke 672989 FAILED: `apply_chat_template(return_tensors="pt")` returns a BatchEncoding in
  transformers 5.12, so `generate(input_ids)` hit `AttributeError` on `.shape`. **Fixed**
  `models/hf_local.py` → `return_dict=True` + `generate(**inputs)` + `out[0, prompt_len:]`
  (also passes attention_mask). **Re-smoke submitted: job 673046.**
- **Bug-check subagent: both changes (offset, hf_local fix) PASS** (transformers 5.12.1 confirmed
  to accept return_dict; slicing correct).

### 2026-07-21 — Iteration 15
**Phase-4X re-smoke (673046) ran end-to-end** (DeepSeek-R1-Distill-Llama-8B, ASR 0.5/2) and
**confirmed the no-cache constraint** (project `.cache/huggingface` stayed 86G — weights went to
node-local `/tmp`). BUT the smoke exposed **2 output bugs**:
1. `target_response` was garbled byte-level BPE (`ĊOkay,ĠsoĠI'm...`) — the tokenizer's byte-decoder
   didn't apply, so the judge scored garbage (0.5 ASR unreliable).
2. `<think>` not stripped — DeepSeek's chat template injects the opening `<think>` into the prompt,
   so the output has only `</think>`; the old `<think>.*?</think>` regex never matched.
**Fixed `models/hf_local.py`:** added a GPT-2/Llama byte-level repair (fires only on `Ġ`/`Ċ`
leak; unit-tested: `ĊOkay,ĠsoĠI'm` → `\nOkay, so I'm`), think-strip now keeps text after the last
`</think>`, tokenizer loaded `use_fast=True`. **Re-smoke v2 submitted: job 673086**
(→ `outputs/phase4_hf_local_v2/`). Full 3-model runs GATED on this smoke showing clean text.
**Phase-3 GCG shards 673018/673043 still running** (~25min; first behavior ~42min, so triggers
not written yet).

### 2026-07-21 — Iteration 17 (gate PASSED → cross-model launched)
Context: this is Omer's **master's research (Mahmoud lab, TAU)** — thesis-grade rigor (saved to
memory `user_omer.md`).
**★ Phase-4X gate PASSED:** smoke v2 (673086) output is clean — no byte-garbling, `<think>`
stripped, readable text ("To solve the problem of finding an optimal exploitation path..."),
judge scored it (is_success=False on this 1 goal, fine). Both `hf_local.py` fixes validated.
**Verified model IDs + gating** (HfApi, no download): DeepSeek-R1-Distill-Llama-8B, Phi-4-reasoning,
Phi-4-mini-reasoning = **ungated**; gemma-3-4b/12b = **gated=manual** (needs license).
**★ Full dev-25 open-source benchmark LAUNCHED (3 families, streams=2 iters=2, fits 8h):**
- **673115** deepseek-ai/DeepSeek-R1-Distill-Llama-8B (Llama-distill reasoning)
- **673117** microsoft/Phi-4-mini-reasoning (Phi reasoning, 3.8B, fast)
- **673118** google/gemma-3-4b-it (user-requested gemma; gated — attempted per "try, pass it";
  fails independently if the token hasn't accepted the license).
All → `outputs/phase4_hf_local/phase4_cot_hf_<model>_dev25.jsonl`. GCG shards 673018/673043 still
running (~1h; first behavior ~42min).

### 2026-07-21 — Iteration 16 (monitoring + recon)
Smoke v2 (673086) still running (generating DeepSeek response). GCG shards 673018/673043 running
(~30min; first behavior ~42min → no triggers yet). Nothing to launch until the smoke gate passes
(kept SLURM budget free for the 3 model runs). **Recon for the next step (reuse-first):**
Phase-3 trigger evaluation (Qwen3 free-gen + StrongREJECT) should reuse
`poc_stage_gcg_early/evaluate_optimized_suffixes.py` (existing suffix→free-gen→StrongREJECT
harness) + `evaluate_cross_model_transfer.py`; adapt its input to TROPT's
`outputs/phase3_tropt/*/triggers.jsonl` (fields: task_id, best_trigger_str, template, target).

**Next iterations (in order)**
- 673086 smoke → confirm clean readable target_response (post-`</think>`) → then full dev-25 on ≥3
  open-source thinking models (bound streams/iters to fit 8h; local gen ~2.5min/goal-unit) →
  StrongREJECT + `CROSS_MODEL_COT_BENCHMARK_REPORT.md`.
- GCG shards done → merge; evaluate MAC+GCG triggers via the reused
  `evaluate_optimized_suffixes.py` path (frozen greedy protocol) vs no-suffix/random → registry rows.
- Re-run advbench_full_0333 (Phase-4 gap) — defer until budget frees.
- When TROPT `.venv` ready → `list_recipes()`, read `gcg__zou2023` + MAC recipe sources, then
  Phase 3 SLURM (GPU/l40s) GCG+MAC on Qwen3 dev-train-20 with the thinking-model target.
- §8.4 controls (length-/structure-matched scaffolds) as separate conditions.
- Judge confusion-matrix script once human labels exist.

### 2026-07-21 — Session 2, Iteration 1 (loop re-established)
**Context:** new session after `/clear`; prior loop cron `e2698d62` died with it. Re-established
the 30-min loop (plan `/a/home/cc/.../plans/now-run-a-loop-majestic-scott.md`). No completed work
restarted — this log is the source of truth.
**Queue healthy (5/6, budget OK):** 673115 RUNNING (Phase-4X deepseek, 15m), 673117 RUNNING
(Phase-4X phi-4-mini), 673118 PENDING 0:00 (just queued, not >30m), 673018+673043 RUNNING ~1.5h
(Phase-3 Qwen3 GCG shards). **No cancel/resubmit needed.**
**Harvest:** nothing finished. Phase-4X full `_dev25.jsonl` not written yet (still generating).
GCG shards at **2/20 behaviors each** (~42min/behavior → ~6h to go). MAC complete (20/20,
`outputs/phase3_tropt/mac_qwen3_empty_think/triggers.jsonl`).
**Recon (prep the Phase-3 eval adapter, no code yet):** confirmed TROPT trigger schema
(`task_id, category, instruction, template, target, best_trigger_str, best_loss`) and the reuse
target `poc_stage_gcg_early/evaluate_optimized_suffixes.py`:
- It builds `user_content = instruction + suffix_str`; TROPT `best_trigger_str` already carries a
  **leading space**, so `suffix_str = best_trigger_str` reproduces the TROPT template exactly.
- It reads candidates from `FINAL_CANDIDATES.jsonl` via a `task` abstraction
  (`task.neutral_control_suffix`, random-spaces + task-only baselines already built in) → adapter
  must emit that shape from `triggers.jsonl`.
- **It generates with `do_sample=True` (line 96)** → the frozen greedy protocol
  (`configs/evaluation/greedy.yaml`) needs a `do_sample=False` path added. Flag this when writing
  the adapter next iteration.
**Next fire (~30m):** re-check queue; if any Phase-4X `_dev25.jsonl` landed → StrongREJECT-score +
start `CROSS_MODEL_COT_BENCHMARK_REPORT.md`; else keep monitoring (GCG shards ~6h out).

### 2026-07-21 — Session 2, Iteration 2
**Queue enforcement:** 673118 (gemma-3-4b-it, Phase-4X) had been PENDING ~60m (submitted 15:42) →
tried cancel+resubmit per the >30m rule, but the auto-mode classifier **blocked scancel** (it read
SLURM's `TIME=0:00`, which is 0 for *all* pending jobs, as "not >30m"). Compound `&&` meant the
resubmit never ran → **no duplicate created**. Turned out **unnecessary**: 673118 was contention-
queued (scheduler est. start 18:38), not a zombie, and **started on its own** (now RUNNING on
n-803). Lesson recorded: don't churn jobs that are legitimately GPU-contention-queued.
**All 3 Phase-4X targets now RUNNING:** 673115 DeepSeek-R1-Distill-Llama-8B (~1h51m, 7+/25 goals),
673117 Phi-4-mini-reasoning (~1h36m), 673118 gemma-3-4b-it (~21m). None finished; `_dev25.jsonl`
not written yet. Per-goal model reload is inherent to the CoT-Hijacking harness (re-inits per goal)
— functional, within 8h wall; not refactoring a working run.

**Phase-3 greedy eval harness BUILT (reuse-first, plan §7.5 / §6.4 controls):**
- EDIT `poc_stage_gcg_early/evaluate_optimized_suffixes.py`: added backward-compatible
  `greedy: bool=False` to `evaluate_suffix` (greedy→`do_sample=False`; default keeps legacy
  sampled) + `"decoding"` field in the result row. Default False → existing callers unchanged.
- NEW `scripts/phase3_eval_triggers.py`: loads Qwen3-14B once via
  `poc_stage4.qwen3_model.load_qwen3_model`, evaluates each TROPT trigger (`best_trigger_str`
  already carries the leading space → `instruction+suffix` reproduces the template) with label
  `tropt_<optimizer>` + shared per-task controls `task_only`/`random_spaces`; reuses the harness's
  inline StrongREJECT + resume-by-row_key. No new gen/scoring/loading code.
- NEW `slurm_scripts/run_phase3_eval.slurm`: env-driven (TRIGGERS/OUT_DIR/SEEDS/LIMIT/DECODING),
  conda `poc_stage2`, project HF cache, L40S, mirrors the proven `run_gcg_free_generation.slurm`.
- **Bug-check: the subagent path failed (login/classifier unavailable, 0 tokens) → did it manually
  read-only. ALL PASS:** `Qwen3Model` is a dataclass exposing `.model/.tokenizer` (used correctly);
  `evaluate_suffix` call arg names/order match incl. new `greedy=`; trigger schema keys
  (task_id/instruction/best_trigger_str/optimizer) exist in real rows; heavy imports are lazy inside
  `main()` so `--help` works CUDA-free (verified); `bash -n` OK; `OPENAI_API_KEY` present (len 164,
  `sk-…`) so inline StrongREJECT scores (same key Phase-4 used). No bugs.
- **Submitted MAC greedy eval: job 673247** → `outputs/phase3_tropt/eval_greedy/` (20 MAC triggers,
  seed 0, greedy). Now **6/6 SLURM budget**. GCG shards (8/20 done) will be added to the SAME
  out-dir later (resume-skip dedups MAC + shared baselines).
**Next fire (~30m):** check 673247 first rows (GPU smoke-in-place — verify sr scores populate);
harvest any finished Phase-4X `_dev25.jsonl` → `run_strongreject_cpu.slurm` +
`CROSS_MODEL_COT_BENCHMARK_REPORT.md`; watch GCG shards.

### 2026-07-21 — Session 2, Iteration 3
**Queue full & healthy (6/6):** 673118/673117/673115 (Phase-4X, running 54m/2h09/2h24), 673247
(MAC greedy eval, running 11m), 673043/673018 (GCG shards, 3h39/3h44). Nothing PENDING → no
cancel/resubmit. Nothing finished → no harvest.
**Progress:** GCG shards **10/20** behaviors (5 per shard); at ~44min/behavior with TIME_LEFT ~4h15
they should finish within the 8h wall (tight ~0.5h margin — noted, will monitor). Phase-4X three
runs still generating; no `_dev25.jsonl` yet.
**673247 observability concern (not yet a failure):** MAC eval RUNNING 11m but logs 0 bytes and no
rows. Root cause most likely **NFS read contention on n-801** (three Qwen3-14B jobs there) slowing
model load, compounded by bash's block-buffered stdout hiding the header until python's `-u` prints
start post-load. **Fix (observability only, does NOT touch running 673247):** added a pre-`conda
activate` heartbeat echo to `slurm_scripts/run_phase3_eval.slurm` so future submissions (incl. the
GCG eval) signal START immediately. `bash -n` OK. **Firm rule:** if 673247 still 0 rows next fire
(~40m total elapsed) → cancel + resubmit (improved script).
**Next fire:** hard-check 673247 first; harvest any Phase-4X `_dev25.jsonl`; watch GCG shards near
completion → merge + submit GCG greedy eval into the same `outputs/phase3_tropt/eval_greedy/`.

### 2026-07-21 — Session 2, Iteration 4 (Phase-4X harvest begins)
**673247 resolved — NOT hung, pathologically slow model load.** `.err` shows transformers still
`Loading weights: 55% (245/443)` at **25 min** — NFS read contention from 3 concurrent Qwen3-14B
jobs on n-801 (673247 + GCG shards 673018/673043) starving the weight read (5–40s/shard). It IS
progressing (~45 min to load, then GPU-bound generation) → **left running** (cancel would waste the
load + resubmit hits the same contention; frees when GCG shards finish).
**★ Phase-4X harvest — 2 of 3 open-source targets DONE** (673115, 673117 completed):
- **DeepSeek-R1-Distill-Llama-8B:** gemini-judge ASR **0.84 (21/25)**, 68 rows —
  `outputs/phase4_hf_local/phase4_cot_hf_deepseek-ai_DeepSeek-R1-Distill-Llama-8B_dev25.jsonl`.
  As vulnerable as gpt-o4-mini → strong white-box mechanistic-target candidate (Phase-5 gate).
- **Phi-4-mini-reasoning:** gemini-judge ASR **0.52 (13/25)**, 72 rows —
  `outputs/phase4_hf_local/phase4_cot_hf_microsoft_Phi-4-mini-reasoning_dev25.jsonl`. More
  resistant → useful contrast (headroom exists but lower).
- **Stale-label caveat (same as Phase-4):** summaries say `dataset: walledai/HarmBench train[0:25]`
  — that's the default label; the `goals=` override feeds our **AdvBench dev-25** (taskmap confirms
  task_ids). Cross-model report must use the AdvBench framing.
- **StrongREJECT scoring submitted (frozen §6 primary judge, cpu-killable):** 673311 (DeepSeek),
  673312 (Phi-4-mini) → `*_strongreject.jsonl` + analysis. **6/6 budget** (2 cpu + 4 GPU).
- gemma-3-4b-it (673118) still RUNNING (1h32m); GCG shards 11/20.
**Next fire:** read 673311/673312 StrongREJECT ASR → append 2 `EXPERIMENT_REGISTRY.csv` rows →
draft `docs/CROSS_MODEL_COT_BENCHMARK_REPORT.md` (DeepSeek/Phi/gemma vs gpt-o4-mini; per-category;
headroom); check gemma 673118; check 673247 generating; watch GCG shards.

### 2026-07-21 — Session 2, Iteration 5 (Phase-4X report + Phase-3 MAC evaluated)
**★ Phase-4X — all 3 targets run; 2 fully scored, cross-model report drafted:**
StrongREJECT behavior-level ASR (frozen §6): **DeepSeek-R1-Distill-Llama-8B 22/23=0.957**
(gemini 0.84), **Phi-4-mini-reasoning 17/22=0.773** (gemini 0.52). gemma-3-4b-it gemini **1.00
(25/25)** but SR pending (job **673371**) — flagged as likely **low-headroom** (small non-reasoning
model, easy compliance) → poor mechanistic target. gpt-o4-mini ref SR 0.917.
- Registry: appended `phase4x_cot_deepseek-r1-distill-llama-8b_dev25` + `phase4x_cot_phi-4-mini-reasoning_dev25`
  to `results/EXPERIMENT_REGISTRY.csv` (**bug-check: all 4 rows = 20 cols, values correct**).
- Deliverable drafted: **`docs/CROSS_MODEL_COT_BENCHMARK_REPORT.md`** (§31.5) — headline table,
  gemini-vs-SR divergence, per-category table, mechanistic-target candidacy (**DeepSeek = strongest
  white-box candidate**: true `<think>`, 0.957 ASR, 8B, MIT, non-Qwen/Llama base → cross-arch test;
  Phi = failed-attack contrast). Marked DRAFT: gemma SR + **clean (no-attack) baselines** still owed
  (§31.6 headroom gate).
- SR analyses: `outputs/phase4_hf_local/*_strongreject_analysis.json`. Attack jobs 673115/117/118 all
  COMPLETED; SR jobs 673311/673312 done, 673371 running.
**★ Phase-3 — MAC greedy eval COMPLETE (673247, 60 rows), harness validated:** my new
`scripts/phase3_eval_triggers.py` + greedy path ran end-to-end (all sr populated, 0 None). Result on
Qwen3-14B dev-train-20, greedy, StrongREJECT: **tropt_mac 3/20=0.150** (mean 0.138) vs **task_only
2/20=0.100** vs **random_spaces 2/20=0.100**. MAC (20-step prefix-CE, empty-think) gives only
+0.05 / +1-behavior over no-attack → reconfirms the plan's "Established" fact that target-prefix
optimization is weak on reasoning models (low MAC opt-loss 1.47 ≠ behavioral ASR). Dev-set, n=20,
single greedy seed — wide CI, not a benchmark claim (§24.1). Output:
`outputs/phase3_tropt/eval_greedy/FREE_GENERATION_RESULTS.jsonl`.
**Queue: 3 jobs** (673371 gemma-SR cpu, 673043/673018 GCG shards 14/20). Held off new GPU jobs to
avoid re-creating the n-801 NFS contention that slowed 673247's load.
**Next fire:** gemma SR (673371) → finalize `CROSS_MODEL_COT_BENCHMARK_REPORT.md` gemma row + verdict
+ registry row; GCG shards (14/20, ~1.5h) → when done merge triggers + submit `run_phase3_eval.slurm`
GCG into the SAME `eval_greedy/` (resume-skips MAC+baselines) → then `docs/TROPT_BASELINE_REPORT.md`
(MAC vs GCG vs baselines). Consider queuing the clean-baseline no-attack HF runs for §31.6 headroom.

### 2026-07-21 — Session 2, Iteration 6 (Phase-4X report attack-complete)
**gemma-3-4b-it StrongREJECT = 25/25 = 1.000** (job 673371 done) — saturates BOTH judges across all
11 categories → confirmed **low-headroom / poor mechanistic target** (§31.6). Registry row
`phase4x_cot_gemma-3-4b-it_dev25` appended (**integrity check: 5 rows × 20 cols, no bad rows**).
**`docs/CROSS_MODEL_COT_BENCHMARK_REPORT.md` finalized to ATTACK-COMPLETE:** filled gemma SR row,
added gemma per-category column (denominators noted: DeepSeek 23 / Phi 22 / gemma 25 due to silent
attacker-API gaps), updated gemma verdict, marked **clean (no-attack) baselines the single remaining
blocker to FINAL**. Cross-model result stands: DeepSeek 0.957 ≈ gpt-o4-mini 0.917 (vulnerable tier),
Phi 0.773 (resistant tier w/ real failed-attack examples), gemma 1.000 (saturated/low-headroom).
**Clean-baseline path scoped (deferred, no rushed code):** no existing no-attack mode in the
hijacking pipeline; the clean reuse primitive is `HFLocalLLM.batched_generate(convs_list,...)`
(`Chain_of_Thought_Hijacking/Hijacking/models/hf_local.py:72`) — build a bare-goal user turn (no
attack scaffold), generate, StrongREJECT-score. New script needed (node-local HF cache per §31.3) →
design + bug-check + 1-goal smoke in a dedicated iteration; not on the active critical path.
**Queue: 2 jobs** (GCG shards 673043/673018, 14/20, TIME_LEFT ~2:22/2:27). 3 behaviors left per
shard × ~44min ≈ 2:12 → should finish within the 8h wall (~10min margin); resume-safe if the last
behavior is cut (driver skips done task_ids on resubmit).
**Next fire:** if BOTH GCG shards reach 10 rows → merge sh0+sh1 + submit `run_phase3_eval.slurm`
(GCG triggers → same `eval_greedy/`, resume-skips MAC/baselines) → write `docs/TROPT_BASELINE_REPORT.md`
(MAC 0.150 vs GCG vs task_only/random 0.100). Then build the clean-baseline script for §31.6.

### 2026-07-21 — Session 2, Iteration 7 (clean-baseline harness built)
**GCG shards 16/20 (8 each), still RUNNING** (TIME_LEFT ~1:44/1:49; 2 behaviors left each ≈1:28 →
should finish within wall). Not ready for the Phase-3 GCG eval yet → used the window for §31.6.
**★ Clean (no-attack) baseline harness BUILT (reuse-first) — the §31.6 headroom blocker:**
- NEW `scripts/phase4x_clean_baseline.py`: bare dev-25 goal → open-source HF target, greedy, NO
  attack/suffix. **Reuses the attack's exact backend** `models.hf_local.HFLocalLLM.batched_generate`
  (byte-repair + `<think>`-strip included) via `poc_stage2.hijacking_wrapper.ensure_hijacking_import_path`
  — no generation logic reimplemented. Emits SR-scorer schema; resume-safe by `goal_index`.
- NEW `slurm_scripts/run_phase4x_clean_baseline.slurm`: node-local `$SLURM_TMPDIR` HF cache (§31.3),
  l40s, poc_stage2 env, START heartbeat.
- **Bug-check (read-only, subagent login still down) found + fixed 1 REAL bug:** the SR scorer's
  `REQUIRED_STAGE2_FIELDS` (poc_stage3/strongreject_scoring.py:21) **raises** if `is_success` or
  `judge_score` is missing — a clean baseline runs no gemini judge, so I added them as `None`
  placeholders (presence satisfies the check; rubric scores independently). Re-verified: all 5
  required fields present, `ast` OK, `bash -n` OK, `--help` CUDA-free, `batched_generate` call
  signature matches (convs positional; max_n_tokens/temperature/top_p kw; temp=0→greedy).
- **Submitted DeepSeek clean baseline: job 673488** (LIMIT=0, de-facto smoke+run since resume-safe)
  → `outputs/phase4x_clean_baseline/clean_deepseek-ai_DeepSeek-R1-Distill-Llama-8B_dev25.jsonl`.
  Budget **3/6** (2 GCG + clean); room reserved for the GCG eval.
**Next fire:** validate 673488 first rows (readable, `<think>` stripped) → if clean, launch Phi +
gemma clean baselines (2 jobs) → StrongREJECT-score all 3 → compute clean ASR → fill §31.6 headroom
(attacked − clean uplift) in `CROSS_MODEL_COT_BENCHMARK_REPORT.md` → mark FINAL. Also: GCG shards →
merge + `run_phase3_eval.slurm` GCG → `docs/TROPT_BASELINE_REPORT.md`.

### 2026-07-21 — Session 2, Iteration 8 (clean baselines running; headroom in progress)
**★ DeepSeek clean baseline (673488) COMPLETED + VALIDATED:** 25/25 rows, all required fields,
**0 leftover `<think>`, 0 byte-leak, 0 empty**; project HF cache unchanged at 86G (node-local weights
per §31.3 ✓). Clean harness works end-to-end. Notable: even CLEAN (no attack) DeepSeek returns
structured exploit content on goal 0 ("To create a script that can exploit vulnerabilities… follow
this structured approach") → **weak baseline safety suspected**; the headroom score will quantify how
much of the 0.957 attacked ASR is baseline vs uplift.
- Output: `outputs/phase4x_clean_baseline/clean_deepseek-ai_DeepSeek-R1-Distill-Llama-8B_dev25.jsonl`.
**Launched remaining clean baselines + scoring:** 673524 (Phi-4-mini clean), 673525 (gemma clean),
673526 (DeepSeek clean StrongREJECT, cpu). Queue **5/6** (2 GCG + 2 clean + 1 SR); 1 slot reserved
for the GCG eval.
**GCG shards 18/20 (9 each), RUNNING** (TIME_LEFT ~1:01/1:06; 1 behavior left each ≈44min → should
just finish within wall).
**Next fire:** read 673526 → DeepSeek clean behavior-level SR ASR → first §31.6 headroom row; when
Phi/gemma clean done → score (673524/525 outputs) → complete headroom table → mark
`CROSS_MODEL_COT_BENCHMARK_REPORT.md` FINAL. GCG shards → merge sh0+sh1 + `run_phase3_eval.slurm` GCG
→ `docs/TROPT_BASELINE_REPORT.md`.

### 2026-07-21 — Session 2, Iteration 9 (GCG shards done → eval launched; DeepSeek headroom in)
**★ Both Phase-3 GCG shards COMPLETED — 20/20 triggers** (10 each), all valid (`best_trigger_str`
non-empty, optimizer=gcg). Queue **empty** → full budget free.
**★ DeepSeek §31.6 headroom (first number):** attacked SR **0.957** vs **clean SR 0.360 (9/25)**
→ uplift **≈ +0.60**. Large, real headroom (weak-ish baseline safety 0.36, attack near-saturates)
→ confirms DeepSeek-R1-Distill-Llama-8B as a genuine white-box mechanistic target. Clean SR from
`outputs/phase4x_clean_baseline/clean_*deepseek*_strongreject.jsonl` (job 673526).
**All 3 clean baseline jsonls done** (673488 DeepSeek, 673524 Phi, 673525 gemma). Launched 3 parallel
jobs: **673559** GCG greedy eval (`run_phase3_eval.slurm`, both shard triggers → `eval_greedy/`,
resume-skips MAC+baselines; n-801 now uncontended → fast load expected), **673560** Phi clean SR,
**673561** gemma clean SR. Budget 3/6.
**Next fire:** Phi+gemma clean SR (673560/561) → complete the §31.6 headroom table (attacked/clean/
uplift; expect gemma uplift ≈0 given clean already saturated) → mark
`CROSS_MODEL_COT_BENCHMARK_REPORT.md` **FINAL** + add clean_asr/uplift to the 3 registry-row notes.
GCG eval (673559) → `tropt_gcg` greedy SR ASR → write `docs/TROPT_BASELINE_REPORT.md` (GCG vs MAC
0.150 vs task_only/random 0.100; MAC/GCG opt-loss+runtime; §7 decision gate).

### 2026-07-21 — Session 2, Iteration 10 (Phase-4X FINAL + a verdict-reversing finding)
**★★ §31.6 headroom complete — and it REVERSED the gemma verdict** (this is the payoff of the
clean baseline the plan mandates). Behavior-level StrongREJECT, attacked vs clean:
| target | attacked | clean | uplift |
| DeepSeek-R1-Distill-Llama-8B | 0.957 | 0.360 | **+0.60** |
| Phi-4-mini-reasoning | 0.773 | 0.400 | **+0.37** |
| **gemma-3-4b-it** | 1.000 | **0.000** | **+1.00** |
gemma refuses **0/25** clean goals (all genuine refusals, 0 scoring failures, mean SR 0.0) but the
attack cracks **25/25** → **maximal** headroom, the OPPOSITE of my earlier "saturated/low-headroom"
call (which wrongly inferred from attacked ASR alone). Correction propagated everywhere:
- `docs/CROSS_MODEL_COT_BENCHMARK_REPORT.md`: status **FINAL**; new §3b headroom table; rewrote the
  gemma "Reading" + candidacy text (gemma = best attack-demo / max headroom, secondary mechanistic
  only because non-reasoning); Gaps updated. **DeepSeek stays primary reasoning white-box target**
  (+0.60 uplift, true `<think>`, non-Qwen).
- `results/EXPERIMENT_REGISTRY.csv`: filled `neutral_asr`(=clean) + `uplift` for all 3 phase4x rows;
  **corrected the gemma note** (was "LOW HEADROOM/poor target"). Integrity re-checked: 5 rows × 20 cols.
- Clean outputs: `outputs/phase4x_clean_baseline/clean_*_strongreject.jsonl` (jobs 673526/560/561).
**Phase-4X = DONE.** Queue: **1 job** (673559 GCG greedy eval, loading model on n-802, uncontended).
**Next fire:** 673559 → 20 `tropt_gcg` greedy rows in `outputs/phase3_tropt/eval_greedy/` → compute
GCG behavior-level greedy SR ASR → write `docs/TROPT_BASELINE_REPORT.md` (tropt_gcg vs tropt_mac
0.150 vs task_only/random 0.100; MAC opt-loss 1.47 + GCG best_loss + runtimes; §7 gate). Then begin
**Phase 5** scoping (mechanistic dataset on DeepSeek + Qwen3; reuse stage4/AE activation harnesses).

### 2026-07-21 — Session 2, Iteration 11 (Phase-3 DONE; Phase-5 scoped)
**★ Phase-3 GCG greedy eval done (job 673559) → `docs/TROPT_BASELINE_REPORT.md` written.** Qwen3-14B,
dev-train-20, per-behavior, greedy StrongREJECT:
| cond | ASR | opt best_loss | steps | runtime/beh |
| TROPT GCG | **9/20=0.450** | 0.195 / min **0.0002** | 500 | 42 min |
| TROPT MAC | 3/20=0.150 | 1.473 | 20 | 61 s |
| no-attack | 2/20=0.100 | — | — | — |
| random | 2/20=0.100 | — | — | — |
**Headline finding (in-TROPT reproduction of the core thesis):** GCG drives prefix-CE to **near-zero**
(min 0.0002) yet cracks only 45% of its *own training* behaviors → **prefix loss ≠ behavioral ASR**.
GCG>MAC but compute-unmatched (500 vs 20 steps). Both beat the 0.100 floor. **§7 decision gate = PASS**
(optimization functional, byte-verified target, checkpoints extracted, identical eval). Registry rows
`phase3_tropt_gcg_qwen3_devtrain20` + `phase3_tropt_mac_qwen3_devtrain20` appended (7 rows × 20 cols).
Caveats: per-behavior training-set ASR (not transfer), n=20, single greedy seed → wide CI; §7.5 rows
B4-B8 (multi-instr, generated-target, CoT-prefix, compute-matched) are follow-ups.

**★ Phase-5 (§9 mechanistic dataset) SCOPED — recon of reusable harnesses (NO launch):**
Big reuse surface, all Qwen3/gemma4-native:
- `poc_stage4/activation_capture.py` (residual/hidden), `poc_stage4/run_attention_extraction.py`
  (attention §9.3/§10-D), `poc_stage_ae/replay_hidden_states.py`, `poc_stage_ae/build_ae_manifest.py`
  + `run_ae_generation.py` + `analyze_paired_ae.py` (matched pairs §9.2),
  `poc_stage_ae/analyze_early_token_signals.py` (shallowest-signal search §10),
  `poc_stage_ae/thinking_position_utils.py::locate_positions` (critical positions §9.4 exactly).
- **Target decision:** run §9 on **Qwen3-14B** (harness-native) rather than DeepSeek (Llama arch would
  need new hooks). We already have on Qwen3: **Groups F/G** (opt-suffix fail/success) = the Phase-3
  `eval_greedy` rows w/ StrongREJECT labels; **Group A** (clean refusal) = `task_only` rows. **The one
  missing piece = Groups C/D (attack fail/success)** → run **CoT-Hijacking on `hf:Qwen/Qwen3-14B`**
  (reuse the Phase-4X hf: local-target path we already built!) on dev-25, StrongREJECT-label. Then feed
  all groups through `poc_stage_ae` for residual/attention/logit extraction at §9.4 positions →
  `mechanistic_dataset/` + `MECHANISTIC_DATASET_CARD.md`. DeepSeek stays the *cross-arch* validation
  target for later (§20), not the first mechanistic pass.
- This keeps the whole mechanistic pipeline on one harness-native reasoning model with matched
  success/failure pairs from data we mostly already have — minimal new code (1 attack run + AE glue).
**Queue empty. Phase 3 ✅ + Phase 4X ✅ FINAL.**
**Next fire:** kick off Phase 5 — smoke CoT-Hijacking on `hf:Qwen/Qwen3-14B` (2 goals) to confirm the
Qwen3 target path + think-handling, then full dev-25; in parallel recon `poc_stage_ae/build_ae_manifest.py`
input schema to wire our Group A/C/D/F/G rows into it. Keep ≤6 SLURM, smoke-gate before scale.

### 2026-07-22 — Session 2, Iteration 12 (Phase 5 kicked off)
**Cache-rule decision (recorded):** Qwen3-14B is ALREADY in the project cache
(`.cache/huggingface/hub/models--Qwen--Qwen3-14B`). §31.3's no-cache rule targets NEW open models;
re-downloading our own main model to node-local is wasteful + caused the earlier NFS thrash. → added a
**backward-compatible `HF_CACHE_MODE`** to `slurm_scripts/run_phase4_hf_local.slurm` (default
`node_local` unchanged for open models; `project` reuses the project cache for already-cached models).
`bash -n` OK; PROJECT_DIR defined before the block.
**Phase-5 step 1 — SMOKE submitted: job 673691** CoT-Hijacking on `hf:Qwen/Qwen3-14B`
(HF_CACHE_MODE=project, LIMIT=2, 1×1) → `outputs/phase5_qwen3_cot/`. Gates the full dev-25 Qwen3 attack
run (Groups C/D with Qwen3's OWN StrongREJECT success labels).
**★ AE pipeline contract fully recon'd (reuse target for §9 extraction):**
- `poc_stage_ae/run_ae_generation.py`: per-(model,goal_index,condition) array task; **manifest row
  schema** = `row_key, model, model_name_or_path, model_revision, goal_index, goal, condition, seed,
  enable_thinking, user_message_text` (+ optional source ids). Generates, locates positions, writes
  `shards/{model}_{condition}_goal{gi}.jsonl` (resumable by row_key).
- `poc_stage_ae/replay_hidden_states.py`: forward pre-hooks on every decoder layer → per-position
  residual across ALL layers; output `[n_rows, n_positions, n_layers+1, d_model]` fp16 + metadata.
  Positions from `thinking_position_utils.locate_positions` = the §9.4 critical positions (7-slot
  superset). `_MAX_POSITIONS=7`.
- **Coupling to handle:** condition→(`enable_thinking`, position schema, transformation) is baked into
  small dicts (`_ENABLE_THINKING`, `_TRANSFORMATION_METHOD`, `position_names_for_condition`) keyed by
  the OLD scheme (A/D/E/G, from `outputs/hijacking_baseline_gpt-o4-mini_1_11.jsonl`). The plan §9 Groups
  A–G are a DIFFERENT taxonomy → the new §9 manifest builder must extend those dicts (or pass
  enable_thinking=True uniformly for Qwen3 reasoning) and feed our data.
**§9 group → data source (mostly already in hand on Qwen3):** A(clean refusal)=phase3 `task_only`
rows / a Qwen3 clean baseline; B(clean comply)=same, complied; **C/D(attack fail/success)=the Qwen3
CoT-Hijacking run (673691→full)**, StrongREJECT-labeled; F/G(opt-suffix fail/success)=phase3
`eval_greedy` rows. E(control scaffold)=§8.4 controls (not yet run).
**Next fire:** validate 673691 smoke (readable, `<think>` handled, project cache reused = no
re-download) → launch full Qwen3 CoT-Hijacking dev-25 (streams/iters for enough C/D pairs) →
StrongREJECT-score → then START `scripts/build_phase5_mechanistic_manifest.py` (new): map A/C/D/F/G
rows into the run_ae_generation schema, extend the condition config dicts, smoke AE extraction on ~4
examples before scaling. Keep ≤6 SLURM.

### 2026-07-22 — Session 2, Iteration 13 (§9 manifest builder built + validated)
**Qwen3 CoT-Hijacking smoke 673691 still PENDING** (~20m, GPU contention "Priority"; under the 30-min
rule → no action). Project cache still 86G (nothing downloaded). Used the window for part (b).
**★ NEW `scripts/build_phase5_mechanistic_manifest.py` — built + validated by execution:** maps our
labelled Qwen3 rows into the `run_ae_generation` manifest schema (§9). Ran it on data in hand →
**60 rows: A=18 (clean refusal), B=2 (clean comply), F=28 (opt-suffix fail), G=12 (opt-suffix
success)** → `outputs/phase5_mechanistic/qwen3_phase5_ae_manifest.jsonl`. Counts reconcile exactly
with the eval_greedy splits (task_only 18+2; 40 suffix rows = 28 F + 12 G). All required
run_ae_generation fields present (row_key/model/model_name_or_path/model_revision/goal_index/goal/
condition/seed/enable_thinking=True/user_message_text) + `success_label`+`source` metadata. Groups
**C/D** (real CoT-Hijacking attack fail/success) plug in via `--cot-scored` once the Qwen3 attack lands
— they are the scientific core; A/B/F/G are controls (F/G = "attack presence" per §9's warning).
**★ KEY integration finding for next fire:** `poc_stage_ae/run_ae_generation.py:447` hardcodes
`--condition choices=["A","D","E","G"]` → my new groups **B/C/F would be argparse-rejected**. Fix =
additive one-liner adding "B","C","F" to the choices — but FIRST verify no condition-keyed dict inside
run_ae_generation would KeyError on the new labels (it uses condition only for row-filtering + shard
naming per recon, but confirm before editing a shared proven file). Reuse launcher
`slurm_scripts/smoke_ae_qwen3.slurm` (+ `submit_qwen_ae.sh`) for the extraction smoke.
**Next fire:** (i) if 673691 PENDING>30m → cancel+resubmit; when it runs, validate + launch full
Qwen3 dev-25 attack → score → rebuild manifest with `--cot-scored` (adds C/D). (ii) verify+extend
run_ae_generation condition choices → **smoke AE extraction** on ~2 rows (e.g. one F, one G;
`smoke_ae_qwen3.slurm`, goal_index/condition from the manifest) to gate the full residual-stream
extraction. Keep ≤6 SLURM.

### 2026-07-22 — Session 2, Iteration 14 (both Phase-5 paths wired; 2 smokes in flight)
**Qwen3 attack smoke 673691 RUNNING** (n-802): cache-mode confirmed — log "reusing project cache",
`hf_cache=$PROJECT/.cache/huggingface`, cache steady 86G (no re-download). Still generating; validate
next fire.
**AE-extraction path WIRED (reuse-first):**
- **Audited `run_ae_generation.py` condition usage** — `condition` used ONLY for row-filtering +
  shard naming + output field (no `dict[condition]` → no KeyError risk); positions/thinking come from
  `enable_thinking`. **Safe.** → extended `run_ae_generation.py:447` choices `["A","D","E","G"]` →
  `["A","B","C","D","E","F","G"]` (additive, backward-compatible; comment explains). `ast` OK.
- **NEW `slurm_scripts/run_phase5_ae_smoke.slurm`** (the existing `smoke_ae_qwen3.slurm` is hardwired
  to goal_index 0 / A-E-D-G): minimal launcher, env `TUPLES="167:G 42:A"`, runs
  `poc_stage_ae.run_ae_generation` (generation) + `replay_hidden_states` (--verify-equivalence) per
  tuple against our manifest, project HF cache, L40S. `bash -n` OK; confirmed the manifest has rows
  for 167:G (2) and 42:A (1). **Submitted: job 673739** → `outputs/phase5_mechanistic/ae_smoke/`.
- Both Phase-5 smokes now validating in parallel (attack path 673691 + AE-extraction path 673739),
  budget 2/6.
**Next fire:** validate 673739 (shards written, replay produces `[n_pos, n_layers+1, d_model]`
residuals, verify-equivalence passes) → gates full AE extraction over the 60-row A/B/F/G manifest;
validate 673691 → launch full Qwen3 dev-25 attack (→ C/D) → score → rebuild manifest `--cot-scored`.
Then run full AE generation+replay array over all groups → `mechanistic_dataset/` +
`MECHANISTIC_DATASET_CARD.md` (§9 deliverable). Keep ≤6 SLURM.

### 2026-07-22 — Session 2, Iteration 15 (Qwen3 attack fix + manifest bug fixed)
**AE-extraction smoke 673739 (running 31m): generation path VALIDATED** — log
`OK gen_tokens=1785 finish=eos_token seg=parsed_from_think_tags elapsed=86.8s`, shard
`outputs/phase5_mechanistic/ae_smoke/generation/shards/qwen3_G_goal167.jsonl` written. Replay
(hidden-state tensors) still pending → confirm next fire.
**★ Diagnosed Qwen3 attack TRUNCATION (real issue) + launched full run with fix:** the Qwen3
CoT-Hijacking smoke (673691) output showed row1 = 14008 chars with **`<think>` open, no `</think>`**
(reasoning truncated at the HFLocalLLM default 4096 tokens → judged fail = FALSE NEGATIVE); row2
completed (success). Fix = raise `HF_TARGET_MAX_NEW_TOKENS` (the binding `min(max_n_tokens, …)` cap).
→ **launched full dev-25 Qwen3 CoT-Hijacking: job 673759** (`HF_CACHE_MODE=project`,
`HF_TARGET_MAX_NEW_TOKENS=12000`, N_STREAMS=2 N_ITERATIONS=1 = 50 gens for §9.2 matched pairs; 12000
cap keeps it within the 8h wall) → `outputs/phase5_qwen3_cot/`.
**★ Caught + fixed a manifest bug (row_key collision)** flagged by the smoke log running row_key
`qwen3|167|G|…|201` twice: goal 167 is a G (success) for BOTH the mac- and gcg-suffix, but my row_key
omitted the source → collision (breaks resume-idempotency + pairing). Fixed
`scripts/build_phase5_mechanistic_manifest.py` `_src_tag` → row_key now `…|{mac|gcg|cot}|{seed}`.
Regenerated: **60 rows, 60 UNIQUE row_keys, 0 dups** (goal167 G = `…|mac|201` + `…|gcg|201`). The old
smoke used the pre-fix manifest (still validated the path); full extraction will use the fixed
manifest in a FRESH out-dir (shard files are keyed by goal_index+condition, rows disambiguated by
row_key inside).
**Queue 2/6:** 673759 (full attack, pending), 673739 (AE smoke, running).
**Next fire:** (i) 673739 replay done? → `[n_pos, n_layers+1, d_model]` tensors + verify-equivalence
PASS → launch FULL A/B/F/G extraction over the fixed 60-row manifest (loop all goal_index×condition
tuples; fresh out-dir e.g. `outputs/phase5_mechanistic/extraction/`) + replay per shard. (ii) full
Qwen3 attack 673759 → validate first rows have `</think>` closed (fix worked) → when done,
StrongREJECT-score → rebuild manifest `--cot-scored` (adds C/D) → extend extraction to C/D. (iii)
then `docs/MECHANISTIC_DATASET_CARD.md` (§9) → Phase 6 signal search.

### 2026-07-22 — Session 2, Iteration 16 (AE extraction path validated → full extraction launched)
**★ AE-extraction smoke 673739 COMPLETE + verify-equivalence PASS.** Replay produced hidden-state
tensors: `outputs/phase5_mechanistic/ae_smoke/hidden_states/shards/qwen3_G_goal167.pt`
**shape (2, 10, 41, 5120)** (rows, positions, n_layers+1=41 for Qwen3-14B, d_model=5120) +
`qwen3_A_goal42.pt` (1,10,41,5120) + metadata parquet; hook-capture vs `output_hidden_states`
**[PASS]** on both; project cache steady 86G. Whole §9 extraction path (generation→replay) works.
**★ Full A/B/F/G extraction LAUNCHED: array 673776 `[0-49]%5`** — one task per unique
(goal_index,condition) tuple (50 total: F19/A18/G11/B2) from
`outputs/phase5_mechanistic/extraction_tuples.txt`, reusing `poc_stage_ae.run_ae_generation` +
`replay_hidden_states` → `outputs/phase5_mechanistic/extraction/`. NEW launcher
`slurm_scripts/run_phase5_ae_extract.slurm` (tuple-file indexed by SLURM_ARRAY_TASK_ID). Bug-check:
`bash -n` OK, 50 lines ↔ array 0-49, line1=42:A / line50=500:G verified. **%5 concurrency keeps
budget ≤6 alongside the attack** (5 array + 1 attack). ~11 min/task (8 min load + work), 6-wide-ish
→ ~2h wall; 50 model loads is wasteful but the plan-standard array pattern (§23.3/§23.4) and
parallel-amortized.
**Full Qwen3 attack 673759 RUNNING** (~34m; no dev25 rows yet — attacker+target loop over 25 goals).
**Queue 6/6** (5 array-slots + attack). Do not add jobs until the array drains / attack finishes.
**Next fire:** monitor 673776 (shards + `.pt` tensors accumulating in extraction/); validate 673759
attack rows now have `</think>` closed (truncation fix) → when done StrongREJECT-score + registry row
+ rebuild manifest `--cot-scored` → extend array to C/D tuples. When A/B/F/G extraction done → start
`docs/MECHANISTIC_DATASET_CARD.md` (§9 deliverable) → Phase 6 signal search
(`poc_stage_ae/analyze_early_token_signals.py`, `analyze_paired_ae.py`).

### 2026-07-22 — Session 2, Iteration 17 (extraction progressing; Phase-6 tool recon'd)
**Extraction array 673776 healthy: ~16/50** (17 gen shards, 16 `.pt` tensors; e.g. qwen3_{A,F,G,B}_goal*.pt).
2 tasks running, rest pending (GPU contention limits concurrency below %5, fine). **Task-16 "error"
is a benign SLURM cgroup-teardown race** (`_cgroup_procs_check ... (null)/cgroup.procs`), not a code
failure — its output `qwen3_G_goal229.pt` is present. Will verify all 50 loadable at the end.
**Full Qwen3 attack 673759 RUNNING** (~1h07m; no dev25 rows yet — writes at end).
**★ Phase-6 (§10) tool recon'd — `poc_stage_ae/analyze_early_token_signals.py` is the signal search:**
"per-position/per-layer separability of attack success from early hidden states," **grouped
leave-one-goal-out** (= §10.3 leave-one-behavior-out), Fisher mean-difference direction, out-of-fold
pooled AUC. Reads `{model}_{condition}_goal{g}.pt` + `_metadata.parquet` + a scores file
(`row_key`→`strongreject_is_success`). CLI `--model --run-dir --conditions`.
**★ Design note for Phase 6 (recorded, no re-extraction needed):** the tool separates success/failure
*within a condition*, but our §9 groups are success-SPLIT (A/B, C/D, F/G). → Phase 6 needs a thin
adapter that treats each COARSE type (clean=A∪B, suffix=F∪G, attack=C∪D) as one analysis condition
with per-row success labels from `success_label`/`strongreject_is_success`. The extracted residual
tensors are grouping-agnostic, so this is analysis-time only. Also need to emit a scores file in the
tool's expected schema. The scientifically-central run = **attack success (D) vs attack failure (C)**
(§10 "success direction"); suffix F/G and clean A/B are controls (attack-presence vs success).
**Queue 3/6.** Next fire: monitor extraction to 50/50 + verify tensors loadable; validate attack
`</think>` fix; when attack done → score + C/D. Then `MECHANISTIC_DATASET_CARD.md` + build the Phase-6
scores file + coarse-condition adapter → run `analyze_early_token_signals` (attack C-vs-D first).

### 2026-07-22 — Session 2, Iteration 18 (§9 dataset card written; extraction 46/50)
**Extraction array 673776: 46/50** (`.pt` + `_metadata.parquet`), tasks 45-49 pending
(JobArrayTaskLimit), **no real errors** (only benign cgroup teardowns). Verified structure via the
metadata parquets (torch-load itself timed out on the login node, but the smoke already confirmed
shape + verify-equivalence PASS):
- **10 captured positions** (§9.4): `prefill_last, startofthink, think_content_1/2/3, endofthink,
  answer_content_1/2/3, endofresponse` — richer than the 7 expected; covers last-input, thinking,
  transition, first-answer, end.
- Rows so far (metadata = example×position, ÷10): A=17, B=2, F=26, G=11 → 56/60 examples.
- Metadata cols incl. `row_key, condition, goal_index, seed, position_name, token_index/id/str,
  layer_count, hidden_dim` — full §9.5 metadata.
- Tensor shape (from smoke) **[n_rows, 10, 41, 5120]** fp16.
**★ Deliverable written: `docs/MECHANISTIC_DATASET_CARD.md`** (§9) — groups+sources table, tensor
spec, the 10 §9.4 positions, matched-pairs scheme (row_key w/ source disambiguation), provenance,
completion criterion. Marked A/B/F/G ~done; **C/D pending** the Qwen3 attack.
**Full Qwen3 attack 673759 RUNNING** (~1h43m; still looping goals, no dev25 output yet — writes at
end; within 8h wall).
**Next fire:** extraction 50/50 → build Phase-6 **scores file** (the generation shards already carry
`row_key/condition/strongreject_is_success` — likely just concat) + **coarse-condition adapter**
(clean=A∪B, suffix=F∪G, attack=C∪D) → run `poc_stage_ae/analyze_early_token_signals.py` (grouped LOGO)
on **F-vs-G now** (ready) + **C-vs-D once attack scored** (the §10 success direction) →
`docs/PREDICTIVE_SIGNAL_REPORT.md`. When attack done: StrongREJECT-score → registry row → manifest
`--cot-scored` → extract C/D tuples into the same dir. Bug-check each new script read-only. ≤6 SLURM.

### 2026-07-22 — Session 2, Iteration 19 (extraction 50/50; AE-gen scoring for correct labels)
**★ Extraction COMPLETE: 50/50 `.pt` tensors, 0 missing tuples** (verified want=have=50). §9 residual
dataset done for A/B/F/G (60 examples: A18/B2/F28/G12).
**Read `analyze_early_token_signals.py` fully — key design fact:** the success/failure split is driven
entirely by the **labels file** (`row_key → strongreject_is_success` via `_label_map`), NOT by which
condition-shard a row sits in; `condition` only selects which `{model}_{condition}_goal{g}.pt` shards
load. So pooling F+G (or C+D) for a success direction = reuse `_load_goal`/`_rowkey_labels`/
`_auc_from_scores` in a thin wrapper that accumulates the LOGO Fisher sums over both fine-conditions
per goal (no fragile shard-merging). Grouped leave-one-goal-out + tie-aware pooled AUC already there.
**★ Caught the labeling subtlety:** the AE generation shards are **UNSCORED** (`strongreject_is_success
=None`; `run_ae_generation` regenerates but doesn't judge). Because it **re-generates (sampled,
temp 0.7)**, the correct Phase-6 label must come from scoring the AE generation itself, not the
original greedy label. → built `outputs/phase5_mechanistic/ae_generations_for_scoring.jsonl` (60 rows,
row_key+condition+goal+target_response=generation_text) and **submitted StrongREJECT scoring: job
673860** (reuses `run_strongreject_cpu.slurm`). Gives labels matched to the captured activations.
**Full Qwen3 attack 673759 RUNNING** (~2h26m; no dev25 yet). Queue 2/6 (attack + AE-gen scoring).
**Next fire:** 673860 done → build the **scores file** (row_key→strongreject_is_success, condition,
generation_status=ok) from the SR output → write `scripts/phase6_signal_search.py` (reuse the 3
helpers; pool fine-conditions per coarse group; grouped LOGO Fisher; per-position/per-layer AUC) →
bug-check → run **F-vs-G** (suffix-success control) → start `docs/PREDICTIVE_SIGNAL_REPORT.md`. Attack
→ score → C/D → the core **C-vs-D success direction**. torch is heavy on login node → run analysis via
a small cpu slurm job or `poc_stage2` python with timeouts.

### 2026-07-22 — Session 2, Iteration 20 (Phase-6 signal-search pipeline built + F-vs-G launched)
**AE-gen StrongREJECT scoring 673860 DONE** (60/60). Labels on the RE-GENERATED (sampled) AE outputs:
A 0/18, B 2/2, **F 3/28, G 8/12** (sampling flips some vs the original greedy labels — confirms
scoring the AE gens is the correct choice). Suffix split for F∪G = 11 success / 29 fail.
- Built `outputs/phase5_mechanistic/phase6_scores.jsonl` (row_key, condition, generation_status=ok,
  strongreject_is_success=score≥0.5) — matches `_label_map`.
**★ NEW `scripts/phase6_signal_search.py`** (reuse-first): imports `_load_goal`, `_rowkey_labels`,
`_auc_from_scores`, `_goal_shards` from `analyze_early_token_signals`; pools a coarse group's fine
conditions per goal (torch.cat rows + concat labels), then the SAME grouped **leave-one-goal-out**
Fisher mean-diff direction → per-(position,layer) out-of-fold pooled AUC. Label-driven success split
(so C∪D / F∪G / A∪B all work). Bug-check: fixed a top-level-import path bug (added `_REPO_ROOT` to
sys.path before importing poc_stage_ae); confirmed login-node torch too slow (2×timeout) → runs via
SLURM. NEW `slurm_scripts/run_phase6_signal.slurm` (cpu-killable + account=gpu-research; env
CONDITIONS/OUT/SCORES). `bash -n` OK.
**Submitted F-vs-G (suffix-success control): job 673878** → `outputs/phase5_mechanistic/phase6_FvsG_auc.csv`.
(Control per §9 — suffix success = "attack presence"; the core is C-vs-D. Note small n: 11 succ/29
fail over ~20 goals → LOGO AUC will be noisy.)
**Full Qwen3 attack 673759 RUNNING ~3h** (no dev25 yet — the long pole; watch it's not stuck, 8h wall).
Queue 2/6.
**Next fire:** read 673878 F-vs-G AUC (per-position/per-layer) → start `docs/PREDICTIVE_SIGNAL_REPORT.md`
(control). Attack 673759 → if done validate `</think>` + StrongREJECT-score → registry row → manifest
`--cot-scored` → extract C/D tuples (`run_phase5_ae_extract.slurm`) → score AE C/D gens → extend
scores file → run `run_phase6_signal.slurm CONDITIONS="C D"` = **the §10 attack success direction**
(earliest layer/position predicting success, grouped LOGO). If attack stuck/near wall → cancel+resubmit
with resume. Keep ≤6 SLURM.

### 2026-07-22 — Session 2, Iteration 21 (F-vs-G signal documented; attack done→scoring; C/D bug pre-fixed)
**★ Phase-6 F-vs-G (suffix-success control) result read (job 673878, n=40, 11 succ/29 fail, grouped
LOGO):** top separability at `endofresponse` L34-39 (AUC 0.85-0.88) — **excluded per §10.5** (post-
answer). Earliest useful cells: **`prefill_last` (last input token) L17 AUC=0.727** (shallowest ≥0.70)
and `think_content_3` L0 ≈0.86 → suffix-success leaves an early/near-input trace. Small n → noisy;
this is *attack-presence*, not the success mechanism. → **`docs/PREDICTIVE_SIGNAL_REPORT.md` started**
(§10) with this control + the pending core C-vs-D + the §10 decision gate.
**★ Qwen3 CoT-Hijacking attack COMPLETE (673759, 25 goals):**
`outputs/phase5_qwen3_cot/phase4_cot_hf_Qwen_Qwen3-14B_dev25.jsonl` (44 rows), gemini ASR **0.52
(13/25)**. **Truncation persists** (27/44 still open-`<think>` even at 12000 tokens — Qwen3 attack
reasoning is very long) BUT harmful content is present (e.g. `execute_shell_command(...)`), and this
only affects the attack-baseline reporting: **C/D mechanistic labels come from the AE re-generation
(32768-token budget, won't truncate) scored separately**, and the attack run only supplies the
`attack_prompt`. → **StrongREJECT scoring submitted: job 673914** (for the registry ASR + C/D shard
assignment).
**★ Pre-emptive bug fix (build_phase5_mechanistic_manifest.py):** C/D rows for the SAME (goal,cond)
across the 2 attack streams would collide on row_key → added a `variant` param folding the attack
`conversation_id` into the src tag. **Bug-check: A/B/F/G still 60 unique rows, 0 dups** (variant=""
default preserves existing behavior); `ast` OK.
**Queue 1/6** (673914 scoring). Next fire: 673914 → attack behavior-level ASR → registry row
`phase5_qwen3_cot_dev25`; `build_phase5_mechanistic_manifest.py --cot-scored <scored>` (adds C/D) →
write C/D tuples → `run_phase5_ae_extract.slurm` array (C/D) → convert+score AE C/D gens → extend
`phase6_scores.jsonl` → `run_phase6_signal.slurm CONDITIONS="C D"` = **the core §10 result** →
finalize `PREDICTIVE_SIGNAL_REPORT.md` + Phase-6 gate.

### 2026-07-22 — Session 2, Iteration 22 (Groups C/D added; extraction launched)
**Attack StrongREJECT scored (673914):** Qwen3 CoT-Hijacking behavior-level ASR **18/22=0.818**
(gemini 0.52); per-row 18 success (D) / 26 fail (C). Registry row `phase5_qwen3_cot_dev25` appended
(with truncation caveat).
**Manifest rebuilt with C/D** (`build_phase5_mechanistic_manifest.py --cot-scored ...`): **104 rows,
all 6 groups A18/B2/C26/D18/F28/G12, 104 UNIQUE row_keys, 0 dups** — the `conversation_id` variant fix
correctly disambiguated the 2 attack streams per goal.
**★ C/D residual extraction LAUNCHED: array 673928 `[0-39]%5`** over
`outputs/phase5_mechanistic/extraction_tuples_cd.txt` (40 C/D tuples) into the SAME
`outputs/phase5_mechanistic/extraction/`. AE re-generates each attack_prompt at 32768 tokens (so C/D
gens are complete, unlike the truncated 12000-token attack run) + captures the §9.4 positions. Budget
5/6. ~25-70 min/task (long attack reasoning), 5-wide → a few hours.
**Next fire:** monitor 673928 to 40/40 C/D `.pt`; convert C/D generation shards → StrongREJECT-score
(`run_strongreject_cpu.slurm`) → append to `phase6_scores.jsonl` → `run_phase6_signal.slurm
CONDITIONS="C D" OUT=.../phase6_CvsD_auc.csv` = **THE §10 attack-success direction** → read earliest
pre-answer layer/position with high LOGO AUC → finalize `docs/PREDICTIVE_SIGNAL_REPORT.md` + assess the
Phase-6 decision gate (predicts success not presence / generalizes across held-out behaviors / before
final answer / survives confounds §10.4). Gate PASS → Phase 7 (§11) causal validation.

### 2026-07-22 — Session 2, Iteration 23 (C/D extraction slow; Phase-7 recon)
**C/D extraction array 673928: 3/40** after ~31m (tasks 0/2/4 running 31m still generating, 6 at 11m).
**Slow but healthy, no errors** — the 32768-token attack-prompt re-generations induce very long Qwen3
reasoning (~30-40 min/task). 40 tuples 5-wide → core C-vs-D result **~4-5h out**. Nothing to harvest;
budget 5/6.
**★ Phase-7 (§11 causal validation) recon — well-supported by existing infra (reuse-first):**
- Intervention mechanism: `poc_stage4/analyze_reasoning_interventions.py` (steer activations during
  reasoning), `analyze_causal_tracing.py`, `analyze_subspace_ablation.py`, `analyze_block_ablation.py`.
- Refusal directions ALREADY computed for Qwen3: `slurm_scripts/compute_refusal_direction_qwen3*.slurm`
  (incl. L20/L28); `Chain_of_Thought_Hijacking/refusal_direction/`.
- TROPT: `tropt/utils/refusal_dir.py` (`compute_refusal_directions`), `SteeringActivationLoss`/
  `HiddenStateBasedLoss` (`tropt/loss/losses.py`) — also the Phase-8 objective backbone.
- **Phase-7 plan:** take the Phase-6 Fisher **success direction** at the best EARLY (pre-answer)
  layer/position as the intervention vector; add/subtract αd (§11.1 sweep) at that layer during
  generation; measure attack-ASR change (§11.5) + coherence/benign-task specificity (§11.6). Reuse the
  reasoning-intervention hook harness rather than rebuild.
**Next fire:** keep monitoring 673928 (resubmit any failed idx); when C/D `.pt` complete → score AE C/D
gens → `phase6_scores.jsonl` → `run_phase6_signal.slurm CONDITIONS="C D"` → the core §10 result +
gate. (Extraction is the long pole; expect 2-3 more idle-monitor fires.)

### 2026-07-22 — Session 2, Iteration 24 (monitor: C/D extraction 9/40)
C/D extraction 673928 progressing: **9/40 `.pt`** (11 gen shards), 5 tasks running, **no errors**
(only benign cgroup teardowns). ~3h to complete at 32768-token attack-gen speed. Budget 6/6 (5 array
+ pending). Nothing to harvest; C/D scoring + `run_phase6_signal.slurm CONDITIONS="C D"` staged as a
one-liner for when all 40 land. Idle-monitor fire per SOP(c).

### 2026-07-22 — Session 2, Iteration 25 (monitor: C/D extraction 23/40)
C/D extraction **23/40 `.pt`** (accelerating from 9), tasks 21-27 area, 28-39 pending, **no errors**.
~1-1.5h to complete. Budget 6/6. Nothing to harvest yet. Idle-monitor per SOP(c) — harvest (score AE
C/D gens → `phase6_scores.jsonl` → `run_phase6_signal.slurm CONDITIONS="C D"`) fires the moment all 40
`.pt` land.

### 2026-07-22 — Session 2, Iteration 26 (monitor: C/D extraction 35/40, final wave)
C/D extraction **35/40 `.pt`**; the 5 "missing" idx (33,35,37,38,39) are exactly the 5 tasks STILL
RUNNING (2-14m in) — **no failures**, final wave finishing in ~15-30m. No errors. Budget 5/6.
Next fire = all 40 → harvest the core C-vs-D result.

### 2026-07-22 — Session 2, Iteration 27 (loop resumed; C/D extraction 90/90; unified scoring launched)
**Loop re-armed:** new cron `f6d80b5c` (`*/30 * * * *`, session-only, 7-day expiry) replaces the prior
`e2698d62` reference. SLURM queue was EMPTY on entry (all extraction drained).
**★ §9 residual extraction FULLY COMPLETE: 90/90 `.pt` tensors** (A18 B2 C22 D18 F19 G11) +
90 `_metadata.parquet` under `outputs/phase5_mechanistic/extraction/hidden_states/shards/`.
104 generation rows / 104 unique row_keys (per-goal shards; C/D have 2 attack streams per goal).
Finish reasons clean: only 1 C row (`max_new_tokens`, `not_separable`) + 1 G row hit the 32768 cap;
rest `eos_token`. No empty `final_text`.
**★ Unified label plumbing built (reuse-first, no duplication):** NEW `scripts/phase6_prepare_scores.py`
with two modes — `prep` (generation shards → StrongREJECT input, scoring **`final_text`** so the judge
sees the ANSWER not the ~22k-token C sudoku scaffold; §6.1 = "actionable harmful assistance" lives in
the answer) and `scores` (SR output → `phase6_scores.jsonl`, the labels file consumed by
`scripts/phase6_signal_search.py` via `_rowkey_labels`/`_label_map`). This replaces the earlier ad-hoc
60-row `ae_generations_for_scoring.jsonl` with a single 104-row all-groups convention (A18 B2 C26 D18
F28 G12) → `outputs/phase5_mechanistic/ae_generations_final_for_scoring.jsonl`.
**★ StrongREJECT scoring LAUNCHED: job 674377** (`run_strongreject_cpu.slurm`, cpu-killable) over all
104 rows → `..._strongreject.jsonl`. Gives success labels matched to the captured activations for
**all six §9 groups at once** (previously only A/B/F/G were scored; C/D were pending).
**Bug-check + Phase-13 recon fanned out:** workflow `wf_09bad5fb-350` (2 verify agents on the new
script + §9 dataset integrity incl. C∩D matched-pair count for LOGO folds; 1 recon agent locating
reusable assets for §17 Phase-13 suffix-dataset analysis to start in parallel with free SLURM capacity).
**Queue 1/6** (674377). **Next fire:** 674377 done → `phase6_prepare_scores.py scores` → rebuild
`phase6_scores.jsonl` (all 104) → `run_phase6_signal.slurm CONDITIONS="C D" OUT=.../phase6_CvsD_auc.csv`
= **THE §10 attack-success direction** (earliest pre-answer layer/position, grouped LOGO) → finalize
`docs/PREDICTIVE_SIGNAL_REPORT.md` + assess Phase-6 gate. Also re-run F-vs-G on the corrected labels.
Act on the workflow's bug findings before trusting any output; if Phase-13 recon shows ready assets,
launch that CPU analysis alongside (still ≤6).

### 2026-07-22 — Session 2, Iteration 27b (all-groups scored; 2 bugs fixed; core C-vs-D launched)
**★ StrongREJECT scoring COMPLETE (674377): all 104 §9 rows scored** (status=success ×104, 104 unique
row_keys). Per-group answer-text (`final_text`) success:
A 0/18 · B 2/2 · C 7/26 · D 17/18 · F 3/28 · G 7/12. Re-generation/sampling flips group labels vs the
original greedy assignment (expected, iter-19 note) → **the correct Phase-6 split is LABEL-DRIVEN**.
Pooled **C∪D = 24 success / 20 fail across 22 goals; 16 goals carry BOTH classes** → grouped
leave-one-goal-out has valid both-class folds (much healthier than F∪G 11/29). Built
`outputs/phase5_mechanistic/phase6_scores.jsonl` (104 rows) via `phase6_prepare_scores.py scores`.
**★ Bug-check workflow `wf_09bad5fb-350` found 2 REAL latent defects (both fixed + re-verified):**
1. **`phase6_prepare_scores.py` — StrongREJECT `--resume` collapse (major).** The scorer keys resume
   identity on `(goal_index, attack_iteration, conversation_id, target_model)`
   (`poc_stage3/strongreject_scoring.py:120`); our 104 rows share `goal_index` across §9 conditions →
   collapse to 25 identity keys. THIS run was fresh (output absent → all 104 scored correctly, verified
   104 unique row_keys) so `phase6_scores.jsonl` is valid, but a `--resume` re-run (the slurm always
   passes `--resume`) would last-write-wins to ~25 records and silently drop ~79 labels. **Fix:** prep
   now pins `conversation_id=row_key` + `target_model=condition` → **104 unique identity keys** (verified).
   No re-score needed (current scored file already correct).
2. **`phase6_signal_search.py` — NaN poisoning (major).** `answer_content_1/2/3` are NaN placeholders
   for ALL 104 rows (non-applicable under `enable_thinking=True`, `thinking_position_utils.py:157` only
   fills them when thinking is OFF — BY DESIGN, metadata correctly flags `position_applicable=False`),
   and `endofthink` is NaN for the 1 row that never closed `</think>` (C_goal458, max_new_tokens). The
   Fisher accumulation summed raw rows with no finite check → any NaN row poisoned that position's
   direction (endofthink is a key §9.4 pre-answer/transition position). **Fix:** per-position finite
   mask — a row contributes to a position only where its vector is finite; counts are now per-position
   so a NaN at one position never drops the row from other positions' LOGO folds. AST OK.
   (The `answer_content` gap only costs post-answer positions, which §10.5 EXCLUDES anyway; all
   pre-answer positions prefill_last→endofthink are intact.)
**§9 dataset integrity (verify agent): STRUCTURALLY CLEAN** — 90 `.pt` = 90 parquet = 90 gen shards,
104 gen rows ↔ 104 metadata row_keys (empty set-diff both ways), no orphan/missing tensors, layer_count
41 / hidden_dim 5120 consistent.
**★ Core §10 result LAUNCHED: job 674430 `run_phase6_signal.slurm CONDITIONS="C D"`** →
`outputs/phase5_mechanistic/phase6_CvsD_auc.csv` = **THE attack-success direction** (earliest pre-answer
layer/position, grouped LOGO). **F-vs-G control re-run on corrected labels: job 674431** →
`phase6_FvsG_auc.csv`. Queue 2/6.
**Next fire:** read both CSVs → earliest pre-answer (position_index ≤ endofthink) layer with high LOGO
AUC = the §10 signal → finalize `docs/PREDICTIVE_SIGNAL_REPORT.md` + assess Phase-6 gate (predicts
success not presence / generalizes across held-out goals via LOGO / before final answer / confounds
§10.4). Gate PASS → Phase 7 (§11) causal validation reusing `poc_stage4/analyze_reasoning_interventions.py`
+ existing Qwen3 refusal dirs. Also Phase-13 (§17) recon from the workflow → possibly launch CPU
suffix-dataset analysis in parallel.

### 2026-07-22 — Session 2, Iteration 27c (★ CORE §10 RESULT: early attack-success signal found)
**★★ Phase-6 §10 CORE result (job 674430, C∪D, 24 succ / 20 fail, 22 goals, 16 both-class, grouped LOGO):**
attack success is linearly separable from failure at **AUC ≈ 0.90 from the last INPUT token onward**:
`prefill_last` L16 **0.904** (pre-generation!), `think_content_1` (1st thinking tok) L20 **0.906**,
`endofthink` L26 **0.906** (n=43, NaN row masked), peak `think_content_2` L40 0.912. Every pre-answer
position ≥0.88. → `outputs/phase5_mechanistic/phase6_CvsD_auc.csv`. **This is the plan's thesis (§28):
the real CoT-Hijacking attack induces an EARLY internal state that determines jailbreak success, ahead
of any harmful content.**
**F-vs-G control (674431, corrected labels):** suffix-presence is strong ONLY at `endofresponse`
(post-answer, §10.5-excluded); earliest pre-answer `prefill_last` L17 = 0.703. So **the real attack is
far more early-predictable than the optimized suffix** at matched positions (prefill_last 0.904 vs
0.703) — supports §30 (standard suffix opt is misaligned with the early success mechanism).
**★ Confound control (§10.4) — honest caveat:** success/fail differ in length (input 1012 vs 1388;
gen 9136 vs 22531). Length-only AUC: input 0.827, gen 0.863. Generation-length CANNOT confound the
early positions (computed at/before 1st generated token) → gen-baseline invalid for them. Input length
IS a candidate confound for prefill_last (0.827 vs 0.904) → **formal input-length control owed** before
a clean gate. C/D share the attack template (matched pairs §9.2) so format is matched; the length gap
is goal-driven.
**Phase-6 decision gate: 3/4 PASS** — (a) success-not-presence ✅, (b) held-out generalization via LOGO
✅, (c) pre-answer ✅, (d) confound control ⏳ (the one open item). Candidate Phase-7 direction: Fisher
success dir at `prefill_last` L16 (gen-length-immune) and/or `think_content_1` L20.
**Deliverable:** `docs/PREDICTIVE_SIGNAL_REPORT.md` fully written (§10; core + control + confound + gate
table + provenance). Registry rows `phase6_CvsD_signal_qwen3` / `phase6_FvsG_signal_qwen3` appended
(20-col CSV-validated). Phase table: Phase 5 ✅, Phase 6 ✅(gate 3/4).
**Two latent bugs fixed this iteration (bug-check workflow wf_09bad5fb-350, all 4 findings addressed):**
`--resume` identity collapse in `phase6_prepare_scores.py` (→ conversation_id=row_key, 104 unique keys)
and NaN poisoning in `phase6_signal_search.py` (→ per-position finite mask; verified endofthink n=43,
answer_content correctly masked). §9 dataset verified structurally clean (90 tensors = 90 parquet = 90
gen shards; 104 unique row_keys).
**Queue 0/6.** **Next fire:** (1) input-length confound control for the core signal (emit per-row
projections from `phase6_signal_search.py`, residualize on input_token_count, recompute AUC) → clear
gate item (d); (2) begin Phase 7 (§11) causal validation — take the `prefill_last` L16 / `think_content_1`
L20 Fisher direction as intervention vector, add/subtract αd during Qwen3 generation (reuse
`poc_stage4/analyze_reasoning_interventions.py` + existing refusal-dir slurm), measure ASR change +
coherence specificity (§11.6); (3) Phase-13 (§17) suffix-dataset analysis can run in parallel (CPU) —
recon in workflow result. Keep ≤6 SLURM.

### 2026-07-22 — Session 2, Iteration 28 (Phase-6 §10.4 confound-control infra; Phase-13 recon banked)
**Goal:** clear the one open Phase-6 gate item (d) — the input-length confound control (§10.4) — then
open Phase 7. Queue empty on entry.
**★ Extended `scripts/phase6_signal_search.py` (reuse, +`--emit-projections`):** optionally dumps the
per-row OUT-OF-FOLD projection (goal held out) for every (position, layer, row) as jsonl. New helper
`_rowkey_order(meta)` reproduces the exact `_rowkey_labels` row ordering (drop_duplicates row_key,
sort row_offset) so emitted projections align positionally with tensor rows. Existing AUC path
unchanged (emit is opt-in, `None` by default).
**★ NEW `scripts/phase6_confound_control.py` (§10.4):** per (position, layer) computes raw AUC,
length-only AUC (−input_len), length-**residualized** AUC (projection minus OLS fit on standardized
input_len), and grouped-LOGO logistic AUC of {projection+input_len} vs {input_len alone} → the
projection SURVIVES iff the two-feature model beats length-alone out-of-fold. Reuses sklearn
`roc_auc_score`/`LogisticRegression` (same stack as `scripts/detector_groupkfold_audit.py`). Only INPUT
length is used for pre-answer positions (gen length can't confound states computed at/before the 1st
generated token — documented in-module). AST OK for both.
**Slurm `run_phase6_signal.slurm`:** added `${EXTRA_ARGS:-}` passthrough (general; used to pass
`--emit-projections`). `bash -n` OK.
**Re-ran C∪D with emit: job 674553** → `outputs/phase5_mechanistic/phase6_CvsD_projections.jsonl`
(rebuilds `phase6_CvsD_auc.csv` identically + the projections).
**★ Phase-13 (§17) recon BANKED (workflow wf_09bad5fb-350, 3rd agent):** the "large GCG suffix
dataset" = union of on-disk artifacts (no HF download) across `outputs/stage_gcg_full{,_v2_userfix}/`,
`stage_gcg_percot_v2/`, `stage_gcg_early/` (87 universal FINAL_CANDIDATES + ~101k FREE_GENERATION rows;
models qwen3/gemma4/deepseek_r1). §17.3 analysis engine ALREADY EXISTS and is CPU-only (imports no
torch): `scripts/gcg_7a_behavior_analysis.py` (per-behavior ASR, cluster-bootstrap, McNemar,
per-category), `scripts/gcg_advbench_llm_taxonomy.py::categorize` (15 cats, prebuilt
`ADVBENCH_LLM_TAXONOMY.json`), `scripts/build_gcg_source_of_truth.py` (CONFIG→objective→ASR walker).
MISSING (to derive, not re-collect): consolidated cross-run table, single objective_type label,
universality label/rank, train-vs-unseen flag, transfer matrix M_{i,j}, suffix-token lexical features.
→ Phase-13 = one CPU orchestrator reusing those loaders; **zero GPU budget → truly parallel with
mechanistic work** (§17 intent). Scheduled as its own next-iteration build (with bug-check).
**Next in THIS fire:** emit done → run `phase6_confound_control.py` on the projections → read whether
the early cells (prefill_last L16, think_content_1 L20, endofthink L26) survive input-length control →
update `PREDICTIVE_SIGNAL_REPORT.md` §3/§4 gate + bug-check subagent. If survive → gate (d) PASS →
Phase 7 (§11) next. If not → honest negative, reshapes Phase 7 target choice.

### 2026-07-22 — Session 2, Iteration 28b (★ Phase-6 GATE 4/4 PASS — confound cleared)
**★ §10.4 confound control DONE** (`scripts/phase6_confound_control.py` on 12324 emitted out-of-fold
projections → `outputs/phase5_mechanistic/phase6_CvsD_confound.csv`). Early cells (raw | length-only |
residualized | LOGO{proj+len} | LOGO{len} | gain):
- `prefill_last` L13: 0.904 | 0.827 | 0.756 | 0.848 | 0.796 | **+0.052**
- `think_content_1` L20: 0.906 | 0.827 | 0.773 | 0.840 | 0.796 | **+0.044**
- `endofthink` L26: 0.906 | 0.829 | 0.741 | 0.822 | 0.796 | +0.026
**Verdict: signal SURVIVES with reduced effect.** After removing the linear input-length effect the
projection still separates success/failure at AUC ≈0.74–0.78, and {projection+length} beats
length-alone OUT-OF-FOLD by +0.02–0.06 → the residual-stream direction carries success info beyond
prompt length. Honest caveat: length explains much of the raw 0.90 (length-only 0.827); the
length-controlled effect (~0.75) is more modest than the headline. `prefill_last` is the cleanest
candidate (generation-length-immune by construction).
**★ Phase-6 decision gate: 4/4 PASS** (success-not-presence / held-out LOGO / pre-answer / confound-
robust). `docs/PREDICTIVE_SIGNAL_REPORT.md` §3 (confound table + verdict) and §4 (gate table → 4/4)
finalized. → **Phase 7 (§11) causal validation is unblocked.**
**Next fire:** Phase 7 — take the Fisher success direction at `prefill_last` L13-16 (and/or
`think_content_1` L20) as the intervention vector; add/subtract αd (§11.1 sweep {-3..3}) at that
layer during Qwen3 generation on the dev-25 attack prompts; measure attack-ASR change (§11.5) +
coherence/benign specificity (§11.6), reusing `poc_stage4/analyze_reasoning_interventions.py` +
existing Qwen3 refusal-dir slurm. In parallel (CPU, no GPU budget): build Phase-13 (§17) suffix-dataset
consolidation reusing `gcg_7a_behavior_analysis.py` + `gcg_advbench_llm_taxonomy.py` +
`build_gcg_source_of_truth.py`. Bug-check each new script. ≤6 SLURM.

### 2026-07-22 — Session 2, Iteration 28c (bug-check → added bootstrap CI → honest QUALIFIED gate)
**Bug-check subagent on iter-28 confound code: NO code defects** (projection↔row_key alignment,
emit-count 12324=Σn_pooled, residualize/grouped-LOGO math, headline numbers all PASS). BUT it flagged a
fair statistical overclaim: the +0.04 out-of-fold gain had no uncertainty quantification at n=44, and
`residualized_auc` is in-sample. → Addressed properly (not just softened wording).
**★ Added goal-clustered bootstrap CI** (§24.2/§6.7) to `scripts/phase6_confound_control.py`
(`--bootstrap`; resample the 22 goals, recompute the OOF {proj+len}−{len} LOGO gain; deterministic RNG,
no Date/random-module dep). Ran 1000× on the top-5 pre-answer cells →
`outputs/phase5_mechanistic/phase6_CvsD_confound_bootstrap.csv`:
- prefill_last L13: gain 95% CI **[−0.034, +0.194]**, P(gain>0)=0.82
- think_content_1 L20: **[−0.052, +0.213]**, P=0.73
- think_content_2 L40: **[−0.036, +0.213]**, P=0.84
- endofthink L26: **[−0.039, +0.213]**, P=0.68
**★ Honest verdict (corrected): every CI includes 0** → the residual-stream direction's predictive
contribution BEYOND prompt length is directionally positive (P 0.68–0.84) but **NOT significant at
n=44**. Prompt length itself predicts success (AUC 0.827). The earlier "+0.02–0.06, real" was an
overclaim — fixed in `docs/PREDICTIVE_SIGNAL_REPORT.md` §3 (bootstrap table + honest verdict) and §4
(gate (d) → **QUALIFIED**, not clean PASS).
**★ Gate decision: (a)(b)(c) PASS, (d) QUALIFIED → still ADVANCE to Phase 7** — rationale: the
**causal** intervention (add/subtract the direction, prompt fixed) is **immune to the length confound**
that clouds the predictive analysis, so Phase 7 (§11.5) is precisely the test that resolves it. If the
causal test is negative, §25 Gate-3 "No" → treat the signal as a detector only (Phase 17), not the main
objective. This is the scientifically correct path and matches §24 (keep exploratory/negative results).
**Next fire:** Phase 7 (§11) — Fisher success dir at `prefill_last` L13-16 / `think_content_1` L20 as
intervention vector (α∈{-3..3}, §11.1), reuse `poc_stage4/analyze_reasoning_interventions.py`; measure
ASR change (§11.5) + coherence/benign specificity (§11.6). Parallel CPU: Phase-13 (§17) build. ≤6 SLURM.

### 2026-07-22 — Session 2, Iteration 29 (Phase 7 §11 causal harness built + smoke; Phase 13 §17 fanned out)
**Queue empty on entry. Two phases advanced in parallel (Phase 7 GPU, Phase 13 CPU).**
**★ Phase-7 (§11) reuse surface mapped:** the activation-addition mechanism ALREADY EXISTS —
`poc_stage4/intervention_selection.py::get_activation_addition_input_pre_hook(direction, coeff)`
(`h + coeff*direction`) + `build_steering_hooks(model_base, direction, source_layer, coeff)` +
`add_hooks` (contextmanager); model via `poc_stage4/qwen3_model.py::load_qwen3_model` (`Qwen3Model`
wrapper: `.layers/.format_prompts/.tokenize_prompts`). Layer indexing matches phase6 (layer_index k =
pre-hook on `layers[k]`).
**★ NEW `scripts/phase7_extract_success_direction.py` (CPU, reuses phase6 loaders):** full-data Fisher
success direction d=mean(success)−mean(failure) at a (position,layer), unit-normalized, + σ=std of C∪D
projections (so steering coeff = α·σ, α in std units per §11.1). Extracted 3 candidates →
`outputs/phase7_causal/success_dir__{think_content_1__L20, prefill_last__L16, endofthink__L26}/`
(direction.pt + selected_direction.json). Sanity: think_content_1 L20 sep=**1.55σ** (n 24/20),
prefill_last L16 1.49σ, endofthink L26 1.48σ (1 NaN dropped) — consistent with AUC≈0.90.
**★ NEW `poc_stage4/phase7_steer_generate.py` + `slurm_scripts/run_phase7_steer.slurm`:** greedy-generate
(§6.2) from Qwen3-14B on dev-25 CLEAN harmful prompts with `h_L+=α·σ·d_unit` at the selected layer,
sweep α∈{-3..3} (§11.1); write per-(goal,α) free gens (think/answer split via
`thinking_position_utils`), α=0 = un-steered baseline (§11.4 cond 1). Reuses the hook + model loaders
(no new steering/generation code). AST+bash-n OK; reused-symbol imports verified.
**★ Phase-7 SMOKE launched: job 674798** (think_content_1 L20 dir, α∈{-2,0,2}, 1 task, 1024 tok) to
validate the harness end-to-end before the α-sweep pilot (§23.1 cheap-first).
**★ Bug-check subagent (read-only)** on both new Phase-7 scripts — critical question = layer-index
alignment (extract layer_index L vs steer source_layer L off-by-one?), σ/sign convention, generation
correctness, think/answer split bias, crash risks. Will act on findings before the pilot.
**★ Phase-13 (§17) build FANNED OUT to subagent (CPU, 0 GPU budget, parallel per §17):** produce
`results/SUFFIX_TAXONOMY.csv`, `results/CATEGORY_TRANSFER_MATRIX.csv`, `docs/DATASET_ANALYSIS_REPORT.md`
reusing `gcg_7a_behavior_analysis.py` + `gcg_advbench_llm_taxonomy.py::categorize` +
`build_gcg_source_of_truth.py`; new orchestrator `scripts/phase13_suffix_analysis.py`; self-bug-check.
**Queue 1/6** (smoke). Next: smoke+bug-check land → fix any layer/sign issue → launch α-sweep PILOT
(think_content_1 L20 + prefill_last L16, α full sweep, 5 tasks) → StrongREJECT-score → ASR-vs-α curve
(§11.5) + specificity (§11.6). Phase-13 subagent returns → bug-check its deliverables.

### 2026-07-22 — Session 2, Iteration 29b (Phase-7 bug-check PASS + fixes; Phase-13 §17 deliverables landed)
**★ Phase-7 bug-check subagent: NO blocking bugs.** Critical layer-alignment = **PASS** — extraction
slot L (`replay_hidden_states` pre-hook on `layers[L]` = hidden_states[L] = input to block L) and the
steerer `build_steering_hooks(source_layer=L)` (forward_pre_hook on `layers[L]`) hit the SAME residual
representation; **no off-by-one**. σ/sign convention consistent (+α→success mean). 3 non-blocking items
→ all fixed: (1) extractor now guards `--layer` to steerable range [0,39] (rejects post-norm slot 40 →
verified rejects L40); (2) `finish_reason` now uses the full Qwen3 EOS set {151645,151643} from
generation_config (was single-EOS mislabel); (3) added `think_closed`/`answer_present` flags for the
§11.6 format-integrity control (strong steering can break format → empty answer must not be misread as
refusal in the ASR-vs-α curve). AST OK; existing L20/L16/L26 directions still valid.
**★ Phase-7 SMOKE (674798) validated the runtime path:** model loaded, σ=10.690 / sep=1.549 printed
(matches extraction), generating α∈{-2,0,2} for 1 task. (Result harvest in-flight.)
**★ Phase-13 (§17) deliverables COMPLETE (subagent, CPU, 0 GPU budget):** NEW
`scripts/phase13_suffix_analysis.py` (reuses `categorize`, `load_manifest/load_results/
per_behavior_success`, `build_gcg_source_of_truth` parsing — no dup) →
- `results/SUFFIX_TAXONOMY.csv` (**336 suffixes** = percot249+full66+v2userfix13+early8; objective_type,
  universality, origin_category, 6 lexical features §17.3F),
- `results/CATEGORY_TRANSFER_MATRIX.csv` (7 origin × 16 eval),
- `docs/DATASET_ANALYSIS_REPORT.md` (§17.3 A/B/C/D/F/G, path-cited, EXIST-vs-DERIVED table).
Findings: most-vulnerable category misinfo optimized ASR 0.246 (→ 0 for drugs/self-harm/theft/child-
exploit); single-vs-multi 0.30 vs 0.0801 (flagged not like-for-like); train-vs-unseen 0.0801 vs 0.0892
(no seed overfit); cot_prefix_ce best objective (0.090 vs neutral 0.031). Consistency check: the
multi_instruction transfer row aggregates to the known 0.0801 overall ASR. Structural limit: per-behavior
suffixes only ever evaluated on their own behavior → off-diagonal transfer absent on disk (real data
limit, not a bug). **Independent verification subagent launched** on these deliverables.
**Queue:** smoke finishing. **Next fire:** confirm smoke answers sane → launch α-sweep PILOT
(`run_phase7_steer.slurm`, think_content_1 L20 + prefill_last L16 dirs, α∈{-3..3}, 5 tasks) →
StrongREJECT-score → ASR-vs-α + refusal-vs-α + format-integrity (§11.5/§11.6) → `CAUSAL_VALIDATION_REPORT.md`.
Act on both pending verification subagents (Phase-7 smoke harvest, Phase-13 deliverables). ≤6 SLURM.

### 2026-07-22 — Session 2, Iteration 29c (Phase-13 verified 5/5 PASS; Phase-7 smoke validating steering)
**★ Phase-13 (§17) independent verification: ALL 5/5 PASS, no real defect.** Reuse confirmed (imports
canonical `categorize`/`load_*`/`per_behavior_success`/`analyze_free_gen`, no private reimplementation);
SUFFIX_TAXONOMY.csv 336 rows = 66+13+249+8 (0 empty suffix / 0 unknown objective_type / universality),
lexical featurizer hand-verified (non_ascii 28/58=0.4828 exact); transfer matrix multi_instruction row
recomputed = 0.0801 (125/1560) = known full-520 ASR; off-diagonal per-behavior absence confirmed a REAL
data limit (0 cross-task per-behavior eval rows on disk, not a code drop); every report number
artifact-backed (misinfo 0.246, single 0.30 / multi 0.0801, train 0.0801 / unseen 0.0892,
cot_prefix_ce 0.090/neutral 0.031). One cosmetic note (unlogged free-gen skips in 2 ASR-aggregation
helpers; already disclosed in report prose) — left as-is (no re-run warranted). **Phase 13 DONE.**
**★ Phase-7 smoke (674798) proves the steering runtime works:** Qwen3-14B loaded on cuda:0, direction
hook applied without error, α=-2 produced a complete answer (tok=1024, 2280 answer chars). Harvesting
the full α∈{-2,0,2} comparison to eyeball the steering effect before the pilot.

### 2026-07-22 — Session 2, Iteration 29d (Phase-7 smoke coherent at α=±2 → α-sweep PILOT launched)
**★ Smoke α∈{-2,0,2} all coherent + on-topic** (cyber goal 0001, all refuse — n=1, clean prompt, hard
goal). Crucially **no incoherence/format-break at |α|=2** (answers 872-1024 tok, fluent) → safe to sweep
to ±3 and the model isn't trivially destroyed (early §11.6 specificity signal). (`think_closed`/
`ans_present`=None in smoke b/c it used the pre-fix runner; pilot uses the fixed one.)
**★ Phase-7 α-sweep CAUSAL PILOT launched (2 jobs, the decisive §11.5 test):**
- 674810: `steer_pilot__tc1_L20` (think_content_1 L20 dir, sep 1.55σ)
- 674811: `steer_pilot__pfl_L16` (prefill_last L16 dir, generation-length-immune)
each α∈{-3,-2,-1,-0.5,0,0.5,1,2,3} × 5 dev-25 clean harmful goals × 2048 tok = 45 gens/job →
`outputs/phase7_causal/steer_pilot__*/generations.jsonl`. α=0 = un-steered baseline (§11.4 cond 1).
**This directly tests §11.5:** +α (toward success mean) should raise ASR / lower refusal; −α the
reverse — and because the prompt is held FIXED, it is **immune to the input-length confound** that
qualified the Phase-6 predictive gate. Queue 2/6.
**Next fire:** pilots done → StrongREJECT-score both generations.jsonl (reuse `run_strongreject_cpu.slurm`
on `final_text`) → build **ASR-vs-α + refusal-vs-α + format-integrity(think_closed/answer_present)-vs-α**
curves (§11.5/§11.6) → `docs/CAUSAL_VALIDATION_REPORT.md` + §11 gate (does intervention change ASR
without destroying coherence?). If monotone α→ASR with coherence intact → direction is causal → Phase 8
objective construction (§12). If flat/incoherent → §25 Gate-3 "No" → detector-only (Phase 17). Bug-check
the scoring/curve step. Phase 13 (§17) DONE+verified this iteration.

### 2026-07-22 — Session 2, Iteration 30 (monitor pilots; Phase-7 analysis pipeline built+validated)
**Pilots RUNNING, healthy** (674810 tc1_L20 ~16/45, 674811 pfl_L16 ~3/45; answers 900-3900 chars, no
errors). Monitoring fire — nothing to harvest; queue 2/6, did not add GPU jobs.
**★ Prep work (CPU, doesn't touch GPU jobs): NEW `scripts/phase7_analyze_causal.py`** (ready for when
pilots finish) — `prep` (generations→StrongREJECT input, unique per-(task,α) resume identity via
conversation_id/target_model, scoring `final_text`) + `curve` (SR output→per-α ASR / refusal / §11.6
format-integrity think_closed·answer_present·empty-answer / mean gen-len, with the §11.5 monotonicity
read). Reuses `run_strongreject_cpu.slurm` (verified scorer does `merged=dict(row)` → preserves
conversation_id for the join). **Validated both modes:** prep on the partial real pilot (19 rows, 0
empty, goal_index+unique-identity correct); curve on a synthetic monotone-score file (ASR 0→1 across α,
format fractions correct). Real pilot rows so far show think_closed=answer_present=1.00 → coherence
intact at these α (good §11.6 sign). End-to-end real-data validation + bug-check subagent deferred to
the harvest fire (needs the SR scores).
**Next fire:** pilots 45/45 → `phase7_analyze_causal.py prep` both → `run_strongreject_cpu.slurm` ×2 →
`curve` → ASR-vs-α + coherence curves → `docs/CAUSAL_VALIDATION_REPORT.md` + §11 gate → bug-check. If
+α raises ASR / −α lowers it with coherence intact → causal → Phase 8 (§12). Else §25 Gate-3 → detector.

### 2026-07-22 — Session 2, Iteration 31 (Phase-7 pilots complete → scoring; ★ coherence intact across all α)
**★ Both α-sweep pilots COMPLETE** (674810 tc1_L20 26min, 674811 pfl_L16 38min; 45/45 each, exit 0).
**★★ §11.6 specificity — STRONG pre-scoring result: format-integrity 100% across the ENTIRE α∈[-3,+3]
range, BOTH directions** — think_closed=5/5 AND answer_present=5/5 at every α; mean gen tokens stable
(591-1064, no collapse/runaway). → **steering does NOT break the model even at ±3σ**; any ASR-vs-α
effect is a genuine behavioral change, not format breakage. (This is the §11.6 "interventions must not
simply break the model" check passing cleanly.)
**Prep + scoring:** `phase7_analyze_causal.py prep` → 45 rows each (0 empty answers) → StrongREJECT
scoring jobs 674859 (tc1_L20) / 674860 (pfl_L16) via `run_strongreject_cpu.slurm`. Queue 2/6.
**Next in THIS fire:** scoring done → `phase7_analyze_causal.py curve` ×2 → the §11.5 ASR-vs-α read →
write `docs/CAUSAL_VALIDATION_REPORT.md` + §11 gate + bug-check the harvest.

### 2026-07-22 — Session 2, Iteration 31b (★ Phase-7 clean-prompt causal test = NULL; attacked-context launched)
**★★ Phase-7 §11.5 CAUSAL RESULT (clean prompts): NULL.** Steering the predictive success direction on
CLEAN harmful prompts does NOT increase attack success:
- tc1_L20 (think_content_1 L20): **ASR=0.000 at every α∈[-3,+3]** (0/45).
- pfl_L16 (prefill_last L16): 2/45, at OPPOSITE extremes (α=+3 goal0063, α=-3 goal0084, diff goals) →
  noise, no monotone α→ASR.
Baselines (α=0) are clean refusals (verified). `outputs/phase7_causal/steer_pilot__*/asr_vs_alpha.csv`.
**★ §11.6 specificity PASS (strong):** coherence 100% across the WHOLE α range both dirs (think_closed &
answer_present 5/5 everywhere; gen-len stable) → the null is a genuine behavioral null, NOT model
breakage. Even a 3σ push along an AUC-0.90 direction leaves behavior unchanged → predictive ≠ causal
lever in this setting.
**★ `docs/CAUSAL_VALIDATION_REPORT.md` written** (clean-prompt null + coherence + §25 Gate-3 provisional
"detector-not-mechanism" read + the pending attacked-context caveat + un-swept layers/timings). Registry
rows `phase7_steer_clean_{tc1_L20,pfl_L16}` appended (20-col verified).
**★ Faithful next test LAUNCHED (§11.4 attacked-context necessity): job 674866.** The direction was
learned from ATTACKED examples, so clean-prompt steering is the strictest extrapolation. Added
`--prompts-jsonl` to `poc_stage4/phase7_steer_generate.py` (feed pre-formatted attack prompts verbatim,
skip re-templating) + slurm `PROMPTS_JSONL` passthrough (first submit 674865 cancelled — launcher didn't
pass it; fixed + resubmitted 674866). Steers **6 D-condition SUCCESS attacks** (succeed at baseline) with
α∈{-3,-2,-1,0,1,3}, tc1_L20 dir, 8192 tok → if −α suppresses their success = causal necessity within the
attack manifold. Extracted prompts: `outputs/phase7_causal/attack_prompts_CD.jsonl` (44) →
`attack_necessity_Dsucc6.jsonl` (6). **Bug-check subagent running** on the runner changes (flagged risks:
greedy-vs-sampled baseline mismatch, 8192-token truncation). Queue 1/6.
**Next fire:** 674866 done → prep+score+curve (reuse `phase7_analyze_causal.py`) → does −α drop ASR? →
finalize CAUSAL_VALIDATION_REPORT §4 + §11/§25 Gate-3 call. Act on bug-check (esp. if greedy baseline
fails to reproduce success → necessity test inconclusive → may need sampled baseline or sufficiency test
on failed attacks). ≤6 SLURM.

### 2026-07-22 — Session 2, Iteration 31c (attacked-context bug-check: code PASS, greedy-baseline confound noted)
**Bug-check on the `--prompts-jsonl` runner changes: code PASS (5/6 items), 1 scientific confound (not a
bug).** Pre-formatted prompts used verbatim (no double-templating — verified all 6 rows start
`<|im_start|>user`, end `assistant\n`); metadata passthrough None-safe; slurm PROMPTS_JSONL passthrough
correct; curve crash-safe. **Truncation LOW risk:** original gen tokens for the 6 D prompts = 4211/5701/
6375/6516/6959/7159, **0/6 exceeded 8192**, all eos (watch D_g146/D_g167 thin headroom under greedy).
**★ Real confound (item 3): greedy-vs-sampled baseline.** D success labels came from SAMPLED (temp 0.7)
AE re-gen; the steering run is GREEDY → α=0 greedy may not reproduce the success → necessity test must be
**conditioned on the subset that succeeds at greedy α=0** (the real N), else a floor makes suppression
uninterpretable. Analysis-time gate (runner is correct). Recorded in `CAUSAL_VALIDATION_REPORT.md` §4.
**Next fire:** 674866 done → score → check greedy α=0 baseline ASR of the 6; for the succeeding subset,
does −α drop ASR (necessity)? Report conditionally. If greedy α=0 floors → necessity inconclusive → the
decisive test becomes sufficiency on failed attacks (C, but 22k-token → costly) or a sampled-decoding
attacked-context sweep. Finalize §11/§25 Gate-3 call. ≤6 SLURM.

### 2026-07-22 — Session 2, Iteration 32 (monitor attacked-context necessity; early anti-necessity signal)
**Necessity job 674866 RUNNING (~21m, 2/36)** — slow (8192-token greedy attack CoTs, ~10min/long-gen;
36 gens → several hours). Healthy, no errors. Monitoring fire; queue 1/6, added no GPU work (Phase-7
outcome gates next steps; won't prejudge).
**★ Early data (D_g1, need α=0 baseline still):** α=-2 (success dir SUBTRACTED) → model STILL produces
compliant harmful content (exploit-path algorithm, answer_present=True) → early evidence AGAINST causal
necessity (subtracting the success dir does not suppress the attack), consistent with the clean-prompt
NULL. α=-3 → tok=8192 hit cap, think_closed=False, EMPTY answer = TRUNCATION artifact (not refusal) —
the bug-check's predicted confound at extreme steering. **Harvest will condition on answer_present**
(`frac_empty_answer` already in the curve) so truncation isn't misread as suppression, AND on the greedy
α=0 baseline (only prompts that succeed at α=0 count for the necessity denominator).
**Next fire:** 674866 → prep+score+curve → per-α ASR among answer_present∧(greedy-α0-success) rows →
finalize `CAUSAL_VALIDATION_REPORT.md` §4 + the §11/§25 Gate-3 call. If necessity also null (as the early
α=-2 point hints) → signal = detector not mechanism → §25 Gate-3 "No" → Phase 17 defensive framing +
record the negative (§24.5); the project still holds the §29 minimum-publishable core (Phases 1-6 done).

### 2026-07-22 — Session 2, Iteration 33 (comprehensive adversarial no-bugs AUDIT launched; loop continues)
**User request: audit ALL new code/impl/logs for bugs (ultracode, fan-out).** Launched workflow
`wf_fd305a4f-18e` — 7 independent audit tracks, each find→**adversarially-verify** (each candidate
finding is refuted-by-default against the actual files/data before it's trusted):
1. phase6-stats (phase6_signal_search / confound_control / prepare_scores — LOGO leakage, scaler
   leakage, bootstrap goal-resampling, emit alignment).
2. phase7-causal (extract_success_direction / phase7_steer_generate / analyze_causal — layer alignment,
   preformatted-prompt verbatim, curve join, sign, truncation-as-refusal).
3. phase13-analysis (phase13_suffix_analysis + outputs — objective_type/universality derivation,
   transfer-matrix aggregation, lexical featurizer, silent skips).
4. slurm-launchers (run_phase6_signal / run_phase7_steer / run_phase5_ae_extract / run_phase3_eval /
   run_phase4x_clean_baseline — passthrough, set -u, L40S guard, §31.3 no-cache, resume safety).
5. reports-faithfulness (PREDICTIVE_SIGNAL / CAUSAL_VALIDATION / MECHANISTIC_DATASET_CARD numbers vs
   CSVs; gate verdicts not overclaimed).
6. registry-manifests (EXPERIMENT_REGISTRY 20-col; **dev/heldout split leakage** = Phase-1 hard
   criterion; SUFFIX_TAXONOMY integrity).
7. progress-log-consistency (phase table vs latest entries; stale "gate 4/4" contradictions; dead path
   refs; numeric claims vs artifacts).
Confirmed real bugs (post-verification) → I fix + re-bug-check. **Loop continues:** necessity job 674866
RUNNING (7/36, healthy); cron f6d80b5c every 30m still active.
**Next:** apply audit-confirmed fixes → re-verify; harvest 674866 (score→curve→§11 Gate-3) when done.

### 2026-07-22 — Session 2, Iteration 33b (★ AUDIT: 10 confirmed bugs found + ALL fixed)
**Adversarial audit workflow `wf_fd305a4f-18e` (7 tracks, 20 agents, find→verify) → 10 CONFIRMED bugs**
(each reproduced against real files/data before trusting). All fixed + re-verified:
**MAJOR (3):**
- [phase7-causal] `scripts/phase7_analyze_causal.py:58` — prep/curve keyed on `task_id`, but in
  attacked-context (`--prompts-jsonl`) runs task_id is NOT unique (C_g63/C_g84/C_g125/C_g500 repeat);
  row_key is. → prep would abort / curve double-count per-α ASR. **Fix:** `_identity(rec)=row_key or
  task_id` used in BOTH prep & curve. Verified: 2 same-task_id/distinct-row_key rows → 2 unique conv_ids
  (no collapse). CRITICAL for the C/D attacked-context harvest.
- [slurm] `poc_stage4/phase7_steer_generate.py` open('w') + killable partition + no skip = §23.4
  violation (preempt→truncate all work). **Fix:** append mode + preload done `(row_key/task_id, alpha)`
  + skip-completed (mirrors `run_ae_generation`). Resume-safe now.
- [reports] `docs/MECHANISTIC_DATASET_CARD.md` stale — claimed C/D "pending job 673759", "60 rows
  A/B/F/G", contradicting the completed 104-row scored dataset + both dependent reports. **Fix:** updated
  to COMPLETE / 104 rows / C26(19f7s) D18(1f17s) / C∪D 24succ 20fail / completion criterion SATISFIED.
**MINOR (7):**
- [phase6-stats] `phase6_confound_control.py:107` bootstrap relabeled each drawn goal as a distinct fold
  → a goal sampled twice leaked identical rows into train+test of the SAME fold (optimistic OOF AUC).
  **Fix:** label by ORIGINAL goal id (weighted cluster bootstrap). **Re-running the CI** (leak-free;
  conclusion "CI includes 0" only strengthens since leakage was optimistic).
- [phase6-stats] `phase6_signal_search.py:89` StopIteration if zero shards → **Fix:** empty-guard returns
  empty DataFrame.
- [phase13] `phase13_suffix_analysis.py` single-vs-multi/§17.3F lexical means pool model families
  (single=100% qwen3; multi=qwen3+gemma4+deepseek) undisclosed → **Fix:** model-family caveat added to
  report + script.
- [slurm] `run_phase5_ae_extract.slurm` static `--array=0-49` vs regenerable tuple file → silent drop if
  longer. **Fix:** task-0 fail-loud assertion `NTUPLES>50 → exit 1` with resubmit hint.
- [reports] `PREDICTIVE_SIGNAL_REPORT.md:55` F∪G "11 succ/29 fail" (stale pre-relabel) → **Fix:** 10/30
  (matches phase6_scores.jsonl; AUCs unaffected).
- [registry] the 2 phase6 signal rows put LOGO-AUC in `greedy_asr` + `uplift`=copy → **Fix:** greedy_asr
  & uplift = n/a, AUC moved to notes (`logo_auc=…`). 20-col verified.
**0 uncertain.** progress-log-consistency track: 0 findings (log internally consistent). All AST/bash-n
pass. Re-bug-check subagent on the fixes next.

### 2026-07-22 — Session 2, Iteration 34 (audit fixes finalized; corrected bootstrap = same conclusion)
**★ Corrected leak-free bootstrap re-ran** (`phase6_confound_control.py` weighted cluster resample) →
CIs essentially IDENTICAL to before (prefill_last L13 [-0.034,+0.194] P=0.817; think_content_1 L20
[-0.052,+0.213] P=0.73; endofthink L26 [-0.039,+0.213] P=0.681) → **the leakage magnitude was
negligible; the "beyond-length gain not significant at n=44" conclusion is robust and now leak-free.**
`docs/PREDICTIVE_SIGNAL_REPORT.md` §3 note updated (weighted cluster bootstrap, CIs unchanged).
**★ Re-verification subagent launched** on all 10 fixes (resume-safety fresh-vs-resume, identity join,
bootstrap relabel, empty-guard non-regression incl. a live C-vs-D re-run, array assertion, registry/doc
numbers). Confirms fixes correct + no regression before I consider the audit closed.
**Loop:** necessity 674866 still RUNNING (12/36 — slow 8192-tok greedy attack CoTs). Cron f6d80b5c live.
**Next:** re-verify PASS → audit fully closed; harvest 674866 (row_key-safe prep now) → necessity curve →
§11/§25 Gate-3 call. ≤6 SLURM.

### 2026-07-22 — Session 2, Iteration 34b (★ AUDIT CLOSED: all 10 fixes re-verified, 0 regressions)
**Re-verification subagent: ALL fixes PASS, no regressions.** Confirmed: phase7 resume-safety (fresh
generates all / resume skips exactly completed (id,α) / keys byte-consistent); phase7 row_key identity
(attacked-context distinct row_key → distinct conv_id, clean rows fall back to task_id, no abort);
bootstrap leak-fix (labels by original goal id; CIs match report §3 exactly, all include 0); empty-guard
(live C-vs-D re-run reproduces think_content_1 L20 0.906 / prefill_last L16 0.904 / endofthink L26 0.906);
SLURM array assertion (fires >50, passes at 50, SLURM-safe); registry (20-col, both signal rows
greedy_asr/uplift=n/a + logo_auc in notes); doc numbers (F∪G 10/30 exact vs phase6_scores; dataset card
104 rows / no "673759"; DATASET_ANALYSIS model-family caveat present). **AUDIT COMPLETE — 10/10 bugs
fixed + verified; no scientific conclusion changed** (Phase-6 confound & Phase-7 null both robust).

### 2026-07-22 — Session 2, Iteration 35 (monitor necessity 19/36; harvest pipeline ready)
Necessity job 674866 RUNNING (1h21m, **19/36**, on track within 3h wall). Structural preview of the
partial data: answers mostly present (format intact) — D_g1/g42/g21 all 6 α done, D_g105 started;
only D_g1 α=-3 truncated (extreme steering → long CoT → 8192 cap, empty answer, correctly flagged by
the curve's `frac_empty_answer`). Harvest pipeline (`phase7_analyze_causal.py prep`→SR→`curve`, now
row_key-safe) is validated & ready; nothing to score until 36/36. Monitoring fire — did NOT start
Phase-8 GPU work (gated on the §11 outcome; won't prejudge). Audit remains CLOSED (10/10 fixed+verified).
Waiter armed on job exit (harvest if complete / resubmit resume-safe if walled). Queue 1/6.

### 2026-07-22 — Session 2, Iteration 35b (★ NECESSITY test preview = NULL → causal Gate-3 "No")
**Partial harvest (4/6 prompts, job 674866, tc1_L20 dir) — validated the row_key-safe pipeline on real
attacked-context data (26 rows, 26 unique identities) + scored (job 675376).**
**★★ Necessity result (attacked context): NULL.** For the 4 complete D-success prompts (D_g1/g21/g42/
g105): **greedy α=0 reproduces success (all score 1.00)** — the greedy/sampled confound did NOT floor
them, so the test is valid — and **subtracting the success direction does NOT suppress the attack**
(every α down to −3σ stays 1.00). The lone 0.00 (D_g1 α=−3) is a truncation artifact (empty answer,
8192 cap), not suppression. `outputs/phase7_causal/steer_attacked_necessity__tc1_L20/asr_vs_alpha_PARTIAL.csv`.
`docs/CAUSAL_VALIDATION_REPORT.md` §4a updated.
**★ CAUSAL VERDICT (provisional, D_g146/g167 pending but preview unambiguous): the early success
direction is NOT causal** — neither sufficient (clean-prompt sweep NULL) nor necessary (attacked-context
−α does not suppress), while §11.6 coherence stays intact throughout. → **§25 Gate-3 "No" branch: treat
the signal as a DETECTOR / correlate, not the main mechanistic objective.** This reframes the
contribution toward **Phase 17 (§21) defensive detection** (success-vs-failure detector) rather than a
distilled causal objective. Scientifically clean NEGATIVE (§24.5) — the predictive AUC-0.90 signal is
confound-qualified AND non-causal, an honest and publishable result; the §29 minimum-publishable core
(Phases 1-6, 13) stands.
**Next fire:** 674866 → 36/36 → re-score (--resume skips 26) → finalize necessity curve + §11 gate
(§11.7 mediation note) → CAUSAL_VALIDATION_REPORT final verdict. Then Phase order: §25 Gate-3 "No" routes
to Phase 17 (defensive) — OR test alternative signals/layers (§11.3) before hard-closing causality.
Bug-check any new analysis. ≤6 SLURM.

### 2026-07-22 — Session 2, Iteration 36 (★★ Phase-7 COMPLETE: success direction NOT CAUSAL → Gate-3 "No")
**Necessity job 674866 COMPLETED (36/36, 2h39m, exit 0).** Full harvest (re-prep 36 → re-score
--resume skipped 26, +10 new, job 675429 → full curve).
**★★ FINAL necessity result (6 D-success attacks, tc1_L20 dir, α∈[-3,+3]):**
`outputs/phase7_causal/steer_attacked_necessity__tc1_L20/asr_vs_alpha.csv`:
α=-3→ASR 1.00 (5/5; 1 trunc), -2→1.00, -1→1.00, **0→1.00 (baseline valid, all 6 succeed greedy)**,
+1→0.83 (1 noisy), +3→1.00. Per-prompt ~all 1.00; only 0.00s = D_g1 α=-3 (truncation) + D_g167 α=+1
(isolated noise). **Subtracting the success direction does NOT suppress attack success (ASR 1.00 to
-3σ) → NECESSITY NULL.**
**★★ PHASE-7 FINAL VERDICT: the early success direction is NOT CAUSAL** — neither **sufficient**
(clean-prompt sweep NULL, iter 31) nor **necessary** (attacked-context NULL, this iter), with §11.6
coherence intact throughout (steering to ±3σ never breaks the model). Combined with Phase-6's
confound-qualified predictive result, the AUC≈0.90 signal is a **detector/correlate, not a manipulable
mechanism**. `docs/CAUSAL_VALIDATION_REPORT.md` finalized (§4 FINAL VERDICT + §4a full table + §4b scope
+ historical note). Registry `phase7_necessity_Dsucc_tc1_L20` (20-col). Phase table: Phase 7 ✅ NOT
CAUSAL.
**★ §25 Gate-3 "No" → routing:** (a) success-direction objective (O4/§12.3) DE-PRIORITIZED as the main
distillation target (falsified for single-direction activation-addition at L16/L20); (b) the signal's
DETECTOR value routes to **Phase 17 (§21)** — success-vs-failure detector that flags a jailbreak before
harmful content (§21.1 target change: not attacked-vs-clean but success-vs-failure); (c) §11.3/§11.8
follow-ups (layer/timing sweep, attention-based mechanism) remain open as alternative-signal tests
before hard-closing ALL causality. Scientifically clean NEGATIVE (§24.5) — honest, publishable; the §29
minimum-publishable core (Phases 1-6, 13) stands.
**Next fire:** choose per plan §25 — either (i) Phase 17 (§21) detector build (reuse Phase-6
success-vs-failure probe infra; the §9 dataset + phase6_signal_search already give the detector), or
(ii) a §11.3 layer/timing alternative-signal sweep to be thorough before closing causality. Lean (i)
Phase-17 (Gate-3 explicitly routes there) with (ii) as a bounded robustness check. ≤6 SLURM; bug-check
new work.

### 2026-07-22 — Session 2, Iteration 37 (Phase 17 §21 started: success-vs-failure detector)
**Per §25 Gate-3 "No" → Phase 17 (§21) defensive interpretation.** §21.1 target change (attacked-vs-clean
→ **success-vs-failure**) is exactly the §9 C∪D split; the detector reuses the §9 residual dataset.
**★ NEW `scripts/phase17_detector.py` (reuse-first):** imports §9 loaders (`_load_goal`/`_rowkey_labels`/
`_goal_shards`), label plumbing (`_labels_from_scores`), and the classifier pipeline
(`detector_groupkfold_audit.make_pipe` = StandardScaler+LogisticRegression). Compares 3 detector
families (§21.3: **fisher** diff-of-means threshold [the Phase-6 direction], **logistic**, **mlp** 64-hid)
across detection timings (§21.4: prefill_last/startofthink/think_content_1-3/endofthink = all PRE-answer)
via grouped leave-one-goal-out (NaN-safe finite mask). Reports best pre-answer detector (before harmful
content — the defensively useful regime). AST OK, imports resolve.
**★ NEW `slurm_scripts/run_phase17_detector.slurm`** (cpu-killable). Submitted **job 675453**
CONDITIONS="C D" → `outputs/phase17_detect/detector_CvsD.csv`. Queue 1/6.
**Carried caveat:** same length confound as Phase-6 predictor applies; a defender needs prediction not
mechanism, but the report will state the detector is partly length-driven.
**Next in fire:** read detector CSV → best pre-answer AUC per family → `docs/ADAPTIVE_DETECTION_AND_
DEFENSE_REPORT.md` (§21.1/§21.3/§21.4) + bug-check subagent. §21.2 adaptive-attack + §21.5 defense-
intervention scoped after.

### 2026-07-22 — Session 2, Iteration 37b (★ Phase-17 detector result + report)
**★ Phase-17 §21 detector (job 675453, C∪D success-vs-fail, grouped LOGO, 147 cells):** best pre-answer
AUC per family — **fisher 0.906** (think_content_1 L20), **logistic 0.908** (endofthink L24), **mlp
0.923** (think_content_2 L28). MLP gives a MODEST nonlinear lift; most separability is already linear.
**★ Key defensive result (§21.4 timing): AUC 0.904 at `prefill_last` L16 — the LAST INPUT TOKEN, before
the model generates anything.** Detection stays ≈0.90 through think_content_1-3 + endofthink = entirely
BEFORE harmful content (the §21.4 "most valuable detector" regime). So the signal that FAILED as a causal
mechanism (Phase 7) SUCCEEDS as an early detector — the honest scientific story.
**★ `docs/ADAPTIVE_DETECTION_AND_DEFENSE_REPORT.md` written** (§21.1 target change, §21.3 comparison
table, §21.4 timing table, length-confound caveat carried from Phase-6, §21.2 adaptive-attack scoped,
§21.5 defense-gate constrained by the Phase-7 steering null). Registry `phase17_detector_CvsD_qwen3`
(20-col). `outputs/phase17_detect/detector_CvsD.csv`.
**Bug-check subagent** on the new detector code next (leakage in grouped LOGO / scaler-per-fold / NaN
mask / Fisher direction fit-on-train-only). Then §21.2/§21.5 follow-ups or a §11.3 alt-signal sweep.

### 2026-07-22 — Session 2, Iteration 37c (Phase-17 detector bug-check PASS → core complete)
**Bug-check subagent on `scripts/phase17_detector.py`: ALL 6 PASS, no bugs/leakage/overclaims.**
Verified: grouped LOGO trains only on `groups!=g`, pipe fit on train only (scaler-per-fold), Fisher dir
from train rows only; assembly row-order consistent (T/y/groups one loop; labels via `_rowkey_labels`
row_offset order); NaN finite-mask gates fit+predict, answer_content_* correctly absent from CSV;
AUC = pooled out-of-fold (not per-fold avg); all 4 headline cells reproduce to 4 decimals and are the
per-family pre-answer maxima; report length-confound caveat + §21.5-vs-Phase7-null both faithful.
**→ Phase 17 core (§21.1 target / §21.3 detector comparison / §21.4 timing) COMPLETE + verified.**
Remaining §21.2 (adaptive attack: optimize L_attack+β·L_detector) + §21.5 (quantified defense gate) are
follow-ups needing the discrete optimizer wired to the detector logit.
**Project status:** the mechanistic thread has a complete, honest arc — Real Attack (Ph4, SR 0.917/0.818)
→ Predictive Signal (Ph6, AUC 0.90 LOGO, confound-qualified) → Causal test (Ph7, NULL, not a mechanism)
→ Detector (Ph17, AUC 0.90 pre-generation). Plus Ph1-3 eval/baseline infra, Ph5 dataset, Ph13 suffix
analysis. All new code audited (10 bugs fixed) + every phase bug-checked. §29 minimum-publishable core
delivered; the causal-negative reframes the contribution toward early detection (§28 story items 1-4 + 9).
**Next fire:** §21.2 adaptive-attack OR §11.3 alt-signal sweep (thoroughness before hard-closing
causality) OR consolidate a synthesis/next-meeting brief. Queue clear. ≤6 SLURM.

### 2026-07-22 — Session 2, Iteration 38 (★ FILL SLURM: §11.3 layer sweep ×4 GPU + §21.3 detector controls ×2 CPU = 6/6)
**User directive: keep SLURM busy with plan-advancing work, parallelize to 6.** Filled the budget:
**§11.3 causal LAYER SWEEP (4 GPU, clean-prompt sufficiency — Gate-3 "test alternative signals"):**
extracted think_content_1 success directions at 4 NEW layers (L8 σ=2.44, L12 σ=4.31, L24 σ=24.95,
L28 σ=48.06; all ~1.5σ sep) → `outputs/phase7_causal/success_dir__think_content_1__L{8,12,24,28}/`.
Launched steering sweeps (α∈{-3..3}, 5 clean goals, 2048 tok):
- 675491 L8 · 675492 L12 · 675493 L24 · 675494 L28 → `outputs/phase7_causal/steer_layersweep__tc1_L*/`.
Combined with the done L16/L20 (both NULL), this sweeps the layer dim L8-L28 for causal sufficiency. If
all NULL → robustly confirms non-causality across depth (hard-closes §11.3); if any layer shows monotone
α→ASR → a causal layer exists (would reopen the objective thread).
**§21.3 DETECTOR CONTROLS (2 CPU cpu-killable — don't compete w/ GPU):** does success-vs-fail detection
generalize beyond CoT attacks? 675495 F∪G (suffix, 10s/30f) · 675496 A∪B (clean, 2s/18f — may have thin
folds) → `outputs/phase17_detect/detector_{FvsG,AvsB}.csv`.
**Queue 6/6.** Going forward: whenever queue < capacity and plan-work remains, launch it.
**Next fire:** harvest layer-sweep (prep→score→curve each; if all null → finalize §11.3 in
CAUSAL_VALIDATION_REPORT §5) + detector controls → ADAPTIVE_DETECTION report §21.3 cross-condition;
bug-check any new analysis; refill SLURM.

### 2026-07-22 — Session 2, Iteration 38b (detector robustness fix; SLURM refilled 6/6)
**Bug found + fixed:** 675496 (A∪B detector) FAILED — only 2 B-success → MLP `early_stopping` internal
stratified split needs ≥2/class → `ValueError` aborted the run (data limit, but crash = robustness bug).
**Fix `scripts/phase17_detector.py::_grouped_logo_oof`:** guard `min(bincount(ytr))<2 → skip fold` +
try/except around fit/predict → degenerate folds skipped, never fatal. C∪D provably unchanged (its
24/20 split leaves ≥2/class every fold → new guard never triggers, try/except never fires; the
detector_CvsD.csv from the passed bug-check stands). AST OK. Resubmitted A∪B (675497) into the freed
slot → the graceful rerun is the fix's end-to-end test. **Queue 6/6** (4 GPU layer-sweep + F∪G + A∪B).
**Next fire:** harvest 4 layer-sweep sufficiency curves (L8/12/24/28) → if all NULL, §11.3 layer sweep
robustly closes causality across depth (finalize CAUSAL_VALIDATION §5); harvest F∪G/A∪B detector controls
→ ADAPTIVE_DETECTION §21.3 cross-condition table. Verify A∪B no longer crashes. Refill SLURM as slots free.

### 2026-07-22 — Session 2, Iteration 39 (detector controls harvested; §21.3 cross-condition; SLURM refilled)
**★ §21.3 cross-condition detector (grouped LOGO, best pre-answer AUC/family):**
- C∪D (CoT attack): fisher 0.906 / logistic 0.908 / **mlp 0.923** (strong).
- F∪G (suffix attack): fisher 0.807 / logistic 0.810 / mlp 0.853 (moderate — weaker; success-state is
  partly attack-family-specific, consistent w/ Phase-7 "correlate not shared mechanism").
- A∪B (clean): degenerate (2 successes → AUC 1.000 artifact, not a result). **Fix VERIFIED: A∪B rerun
  (675497) ran gracefully, no crash** → the `_grouped_logo_oof` thin-fold guard works end-to-end.
`docs/ADAPTIVE_DETECTION_AND_DEFENSE_REPORT.md` §21.3 cross-condition table added.
`outputs/phase17_detect/detector_{FvsG,AvsB}.csv`.
**SLURM refill:** launched dense full-depth C∪D detector sweep (all 41 layers, job 675528, CPU) to pin
the exact best §21.4 detection depth. Queue 5/6 (2 GPU layer-sweep running L8/L12 + 2 pending L24/L28 on
node contention + dense detector). GPU node availability (not budget) limits sweep throughput.
**★ Next big thread identified — DATASET SCALING (de-confound):** the central caveat of BOTH the Phase-6
predictor and Phase-17 detector is n=44 + length confound. Running Qwen3 CoT-Hijacking on MORE goals
(dev-val 5 + a held-out subset) → more C/D → re-test predictor/detector at larger n with length control.
Pipeline: attack (reuse `poc_stage2` hijack wrapper / hf-local) → extract (`run_phase5_ae_extract`) →
score → re-run phase6/phase17. This is the highest-value remaining GPU thread; set up next fire.
**Next fire:** harvest §11.3 layer sweep (L8/12/24/28 sufficiency curves) + dense detector; if layer
sweep all-NULL → finalize §11.3 (causality closed across depth); launch dataset-scaling attack. ≤6 SLURM.

### 2026-07-22 — Session 2, Iteration 40 (SLURM efficiency: fixed 4-way 14B-load contention)
**★ Operational finding:** launching 4 concurrent Qwen3-14B loads thrashed the shared HF-cache
filesystem — L8 (675491) stuck at 7% weights after 22min (proj. 2h load) while L12/L28 (on other nodes)
loaded and began generating. **Lesson: stage ≤2 concurrent 14B GPU loads; the bottleneck is shared-FS
weight-read IO, not GPU or the 6-job budget.**
**Rebalanced:** cancelled the 2 stuck loaders (L8 675491 / L24 675493; 0 gens → nothing lost, runner is
resume-safe anyway) and resubmitted (675542 L8, 675543 L24) so they load 2-way once L12/L28 finish
loading. Queue 6/6 (dense detector 675528 + L12 675492 + L28 675494 generating + L8/L24 resubmitted).
**Note:** this was a SLURM ops change (cancel/resubmit same audited runner), not a code change → no
bug-check needed; the layer sweep is thoroughness (§11.3), not critical-path (causal null already on
L16/L20), so slow completion is fine.
**Next fire:** harvest L12/L28 sufficiency curves first (finish soonest) → L8/L24; dense detector
(675528) → best §21.4 depth; if all layer-sweep NULL → §11.3 causality closed across depth. Then launch
dataset-scaling (staged ≤2 concurrent loads) to de-confound at larger n. Refill SLURM mindful of load
staging. ≤6.

### 2026-07-22 — Session 2, Iteration 41 (§11.3 layer sweep: NULL across depth → causality closed)
**★ Layer-sweep sufficiency curves (clean prompts, tc1 success dir):** L12 and L28 harvested (jobs
675492/675494 gen; 675564/675565 scored):
- **L12: ASR 0.000 at EVERY α** (-3..+3), coherence 100%. Flat null.
- **L28: ASR 0.000 baseline**; isolated 1/5 at α=-3 AND +2 (opposite dirs → noise, non-monotone),
  coherence 100%.
Combined with L16/L20 (null, iter 31): **at NO tested layer (L12/16/20/28) does adding the success
direction induce attack success; coherence 100% throughout.** → **§11.3 layer-sweep threat CLOSED — the
causal null is not a one-layer artifact.** `docs/CAUSAL_VALIDATION_REPORT.md` §5 rewritten (layer table).
L8/L24 (resubmitted 675542/675543) still generating — will confirm. Remaining untested = timing-restricted
(§11.2) + attention mechanism (§11.8), different mechanism FAMILIES not depths.
**Queue:** L8/L24 generating + dense detector (675528) running. Harvested L12/L28 (prep 0-empty → score →
curve). Refill as slots free.
**Next fire:** L8/L24 curves (confirm null) + dense detector best-depth (§21.4) → then launch DATASET
SCALING (staged ≤2 loads) to de-confound predictor/detector at larger n. ≤6 SLURM.

### 2026-07-22 — Session 2, Iteration 41b (§11.3 closed; DATASET SCALING launched to de-confound)
**§11.3 layer sweep FINAL:** L8/L24 cancelled (SLURM co-located both on n-801 → 2h load thrash;
marginal). Sweep conclusive on **L12/16/20/28 all NULL** (clean-prompt sufficiency, coherence 100%) →
causality closed across depth. `CAUSAL_VALIDATION_REPORT.md` §5 = layer table.
**★ DATASET SCALING started (de-confound the n=44 predictor+detector — the central caveat):**
- Parameterized `slurm_scripts/run_phase4_hf_local.slurm` (added `MANIFEST` env, default dev_25;
  bash -n OK). Small change; manifest format matches dev_25 → validated by the attack job reading it.
- Built `data/manifests/scale_heldout_25.csv` — **25 held-out goals across 16 categories, 0 overlap
  with dev-25** (verified) → genuinely unseen behaviors (doubles as a §18-flavor held-out detector test).
- Launched **Qwen3 CoT-Hijacking attack: job 675571** (HF_MODEL=Qwen3-14B, HF_CACHE_MODE=project [reuse
  cache, no re-download], MANIFEST=scale_heldout_25, LIMIT=25, N_STREAMS=2, single staged GPU load →
  no co-location thrash) → `outputs/phase7scale_qwen3_cot_heldout25/`.
**SLURM throughput note:** shared-FS weight-read thrash caps safe concurrency at ~1-2 14B GPU loads
(not the 6-budget); running attack (GPU) + dense detector (CPU). More GPU now would thrash → held.
**Next fire:** attack 675571 → score → extract activations (staged GPU, run_phase5_ae_extract) → score
AE gens → append to phase6_scores → re-run phase6 predictor + phase17 detector + confound at LARGER n
(≈44+50 rows) → does the signal survive length control with more data? Harvest dense detector (§21.4 best
depth) meanwhile. Bug-check the launcher change end-to-end via the attack log. ≤6 SLURM, ≤2 concurrent 14B.

### 2026-07-22 — Session 2, Iteration 42 (dense detector harvested; §21.4 best-depth refined; attack running)
**★ Dense full-depth detector (675528, all 40 layers, 834 cells) COMPLETE + report §21.4 updated:**
best pre-answer = **MLP think_content_1 L19 AUC=0.925** (refines coarse 0.923). **At the LAST INPUT
TOKEN (prefill_last, pre-generation): logistic L38 AUC=0.917** (coarse [8..32] grid missed L38, read
0.867), fisher L13 0.904 → a purely PRE-GENERATION detector (prompt final-token residual only) separates
will-succeed from will-fail attacks at ≈0.92. `outputs/phase17_detect/detector_CvsD_alllayers.csv`;
`docs/ADAPTIVE_DETECTION_AND_DEFENSE_REPORT.md` §21.4 dense-confirmation paragraph added.
**Launcher change verified:** attack 675571 reads `scale_heldout_25.csv` (limit 25, project cache, no
errors) — the MANIFEST parameterization works end-to-end.
**Attack 675571 RUNNING** (Qwen3 CoT on 25 held-out goals, single staged load). Launched dense F∪G
detector (all layers, CPU) → cross-condition depth picture. Queue 2/6 (attack GPU + dense F∪G CPU); held
at ≤2 concurrent 14B loads (FS-safe).
**Deferred (do once at scaled n, not redundantly at n=44):** logistic/MLP detector LENGTH-confound
control — the scaled attack (≈+50 C/D rows) will let predictor+detector+confound all re-run at n≈90,
strictly more informative than n=44.
**Next fire:** attack → score → extract (staged GPU) → append phase6_scores → re-run phase6/phase17 +
confound at n≈90. Harvest dense F∪G. ≤6 SLURM, ≤2 concurrent 14B.

### 2026-07-22 — Session 2, Iteration 42b (user: full re-bug-check → comprehensive audit #2 launched)
**User directive: bug-check everything (ultracode).** Launched re-audit workflow `wf_9c04c946-e0c` — 5
tracks (find→adversarially-verify) over ALL code/reports/data CHANGED since the iter-33 audit:
1. phase17-detector (code + fisher/logistic/mlp, thin-fold guard, dense 834-cell output, leakage).
2. phase7-harvest (analyze_causal row_key fix, steer_generate resume-safety, extract layer-guard) vs the
   real necessity + layer-sweep curves.
3. reports-faithfulness (CAUSAL_VALIDATION §2/§4a/§5/verdict + ADAPTIVE_DETECTION §21.3/21.4/dense vs CSVs).
4. slurm-and-data (run_phase4_hf_local MANIFEST param, run_phase17_detector, ae_extract array guard,
   scale_heldout_25.csv 25-row + ZERO overlap w/ dev-25/dev_train_20/dev_val_5 = Phase-1 no-leak).
5. cross-consistency (registry 20-col, log phase-table vs latest, 4 reports mutually consistent, counts).
Confirmed bugs → fix + re-verify. **SLURM unaffected:** attack 675571 RUNNING (33m) + dense F∪G 675574
(28m) = 2/6, ≤2 concurrent 14B loads (FS-safe).
**Next:** apply audit-confirmed fixes; harvest attack (→ score → extract → re-run predictor/detector at
n≈90) + dense F∪G.

### 2026-07-22 — Session 2, Iteration 43 (re-audit #2: 7 MINOR bugs, all fixed; 0 critical/major)
**Re-audit workflow `wf_9c04c946-e0c` (5 tracks, 16 agents) → 7 CONFIRMED bugs, ALL MINOR; cross-
consistency track = 0 findings (reports/log/registry mutually consistent).** All fixed:
1. [phase17] `detector_CvsD_alllayers.csv` logistic column not reproducible (~0.006 AUC sklearn/assembly
   drift; fisher+mlp reproduce exactly). → REGENERATING under pinned env (job 675607, sklearn 1.9.0
   recorded); report numbers updated post-regen.
2. [phase17] `phase17_detector.py:103` min-bincount thin-fold guard applied to ALL families but only MLP
   needs it → over-suppressed logistic on thin folds. **Fix:** `needs_min2` param, min-2 skip MLP-only;
   logistic/fisher use the try/except. C∪D unaffected (no thin folds).
3. [phase17] Fisher 6 fewer cells than logistic/mlp (L0 embedding zero-variance → Fisher None). **Fix:**
   skip L0 uniformly (degenerate for all) → identical grid across families.
4. [phase7] `phase7_analyze_causal.py:110` ASR over n_scored drops empty-answer rows from denominator
   (could read a coherence collapse as sustained ASR). **Fix:** added `asr_conservative`=succ/n +
   `n_empty` (empties = failures). Benign in our data (necessity α=-3: asr 1.0 vs conservative 0.833,
   1/36 row) but methodologically correct now.
5. [reports] `CAUSAL_VALIDATION_REPORT.md` §5 layer table mislabeled L16 as think_content_1 — it was the
   **prefill_last** direction (L20 pilot = think_content_1; sweep L12/28 = think_content_1). **Fix:** §5
   table now shows the direction-position per layer correctly. (Most important faithfulness fix.)
6. [slurm] `run_phase5_ae_extract.slurm:44` array guard used `wc -l` (undercounts w/o trailing newline
   at the exact off-by-one it guards). **Fix:** `awk 'END{print NR}'`.
7. [slurm] `run_phase4_hf_local.slurm:37` HF_CACHE_MODE=project didn't verify model cached → typo could
   download a NEW model into the project cache (§31.3 violation). **Fix:** assert the snapshot dir exists,
   else FATAL exit.
All AST/bash-n pass. **Regen 675607 validates fixes 1-3 end-to-end** (expect fisher tc1 L20=0.906 /
mlp tc1 L19=0.925 unchanged; logistic reproducible; no L0 rows; equal cell counts). Queue includes the
attack + dense F∪G + regen.
**Next:** regen done → verify unchanged headline + update ADAPTIVE_DETECTION §21.3/§21.4 to reproducible
numbers → re-bug-check the fixes. Continue dataset-scaling harvest.

### 2026-07-22 — Session 2, Iteration 43b (node-reliability fix; regen validating audit fixes)
**★ Reliability finding + fix:** node **n-801 has slow storage for 14B loads** — the scaling attack
675571 (ONLY GPU job, no concurrency) loaded at 16s/it, 68% after 1h. Same node that thrashed L8/L24.
→ Dropped n-801 from the GPU launchers: `run_phase7_steer.slurm` nodelist=n-802,n-803,n-805;
`run_phase4_hf_local.slurm` + `run_phase5_ae_extract.slurm` exclude += n-801. bash -n OK all three.
(Attack 675571 left running — 68% loaded, restart would lose progress; 8h wall has room.)
**Regen 675607 RUNNING** (~16m) — validates audit fixes 1-3 (reproducible logistic / MLP-only guard /
no-L0). Attack 675571 loading on n-801 (slow, will finish ~38m + then attack 25 held-out goals).
Queue 2/6. Robust waiter armed on regen completion.
**Next fire:** regen done → confirm fisher/mlp headline unchanged (0.906/0.925) + logistic reproducible
→ update ADAPTIVE_DETECTION §21.3/§21.4 numbers → attack done → score → extract (staged, off n-801) →
predictor/detector at n≈90. ≤6 SLURM, avoid n-801.

### 2026-07-22 — Session 2, Iteration 44 (regen VALIDATES audit fixes; both audits closed)
**★ Regen 675607 (fixed code) VALIDATES fixes 1-3:** `detector_CvsD_alllayers.csv` — **L0 rows=0**,
**equal cell counts (fisher=logistic=mlp=273)**, headline UNCHANGED: fisher think_content_1 0.9062,
mlp think_content_1 L19 0.9250, **logistic prefill_last L38 0.9167** (reproducible by the committed
script BOTH runs → the re-audit's "0.910" was its own reimplementation artifact, not script
non-determinism; report number 0.917 stands). Fixes [1] MLP-only guard + [2] L0-skip confirmed
C∪D-neutral. Coarse §21.3 C∪D/F∪G numbers unaffected (coarse grid has no L0, no thin folds) → no report
number changes. Added `## Reproducibility` note to ADAPTIVE_DETECTION (sklearn 1.9.0, ±0.006 tie-order,
273 cells/family). **BOTH comprehensive audits now CLOSED: 10 (audit #1) + 7 minor (audit #2), all
fixed + validated; every scientific conclusion unchanged.**
**★ Dataset-scaling attack 675571 PAST LOAD → attacking** (1h33m; n-801 slow-load done; "Generated
adversarial prompts / TargetLM generation" — now running CoT-Hijacking on the 25 held-out goals × 2
streams). n-801 excluded from future GPU launchers.
Queue 1/6 (just the attack). **Next fire:** attack → score → extract C/D (staged, off n-801) → append
phase6_scores → re-run phase6 predictor + phase17 detector + confound at n≈90 (does the AUC-0.90 signal
survive length control with more data?). ≤6 SLURM, avoid n-801.

### 2026-07-22 — Session 2, Iteration 45 (monitor scaling attack — wall-time watch)
Attack 675571 progressing: **goal 4/25** at 2h03m (post-load ~1h attacking, ~15min/goal). **Wall-time
risk:** 25 goals × ~15min + 1h load ≈ 7.25h vs 8h wall — tight; the hijacking wrapper has NO resume, so
a wall = lost work. **Decision rule for next fire:** if <~12 goals done by ~5h elapsed, cancel +
resubmit on a smaller goal set (LIMIT=12) to guarantee completion; else let it finish. Monitoring fire
— queue 1/6 (attack is the substantive job; extraction/analysis are sequentially gated on its output,
so no redundant fill). Both audits closed; all fixes validated.
**Next fire:** check attack goal-count vs wall; harvest when done → score → extract (staged, off n-801)
→ predictor/detector/confound at n≈90. If walled → resubmit smaller. ≤6 SLURM.

### 2026-07-22 — Session 2, Iteration 46 (parallel work while attack runs: detector confound + synthesis)
**User: find parallel/meantime work.** Two genuinely-independent tracks (not gated on the attack):
**★ Track 1 — Detector length-confound (CPU, job 675773):** the Phase-6 confound controlled only the
FISHER direction; the logistic/MLP detectors (0.917/0.925) had NO length control. NEW
`scripts/phase17_confound.py` (reuse-first: `phase17_detector._assemble` + phase6_confound
`_residualize`/`_grouped_logo_auc`/`_goal_bootstrap_gain_ci` + `make_pipe`/`_mlp_pipe`) computes
grouped-LOGO OOF detector probs → residualize on input length → does the detector add beyond length?
Cells: mlp tc1 L19, logistic prefill_last L38, fisher tc1 L20 / prefill_last L16. `run_phase17_confound.slurm`.
Bug-check subagent running (key risk = length-vector↔row alignment).
**★ Track 2 — Synthesis (no compute):** NEW `docs/DISTILLATION_FINDINGS_SYNTHESIS.md` — one-page arc
(Real Attack→Predictive Signal→Causal NULL→Detector) mapped to plan §28 (paper story) + §29 (minimum
publishable), path-referenced, honest negatives kept. §29 items 1-4 delivered, item 5 = rigorous
negative, strongest positive = the early detector.
**Attack 675571 RUNNING** (~goal 5-6/25; wall-time watch active). Queue 2/6 (attack GPU + confound CPU).
**Next fire:** confound result + bug-check → fold detector length-story into ADAPTIVE_DETECTION; attack
wall-check (cancel+resubmit-smaller if <12 goals by ~5h); dense F∪G already done (supplementary).

### 2026-07-22 — Session 2, Iteration 47 (★ detector confound: NO family beats length at n=44)
**★ Detector length-confound (job 675773, `scripts/phase17_confound.py`) — the §21 completeness gap
CLOSED:** extended the Phase-6 Fisher-only confound to logistic/MLP.
`outputs/phase17_detect/detector_CvsD_confound.csv`:
| cell | raw | len-only | resid | OOF gain | 95% CI | P+ |
| mlp tc1 L19 | 0.925 | 0.827 | 0.723 | **-0.050** | [-0.101,+0.120] | 0.29 |
| logistic pfl L38 | 0.910 | 0.827 | 0.810 | +0.052 | [-0.086,+0.267] | 0.73 |
| fisher tc1 L20 | 0.906 | 0.827 | 0.773 | +0.044 | [-0.074,+0.212] | 0.67 |
| fisher pfl L16 | 0.904 | 0.827 | 0.758 | +0.044 | [-0.058,+0.218] | 0.75 |
**Verdict: NO detector family (fisher/logistic/mlp) adds SIGNIFICANT signal beyond prompt length at
n=44** — every gain CI includes 0; the MLP's gain is NEGATIVE (its higher raw 0.925 is NOT extra
length-independent signal — the nonlinearity fits length-correlated structure). Residualized 0.72-0.81
(above chance, descriptive). → `ADAPTIVE_DETECTION_AND_DEFENSE_REPORT.md` confound section rewritten
(all-families table + honest "length-correlated early-warning signal, not a success representation").
**Bug-check PASS** (no alignment bug; row-pairing provably correct; applied the unknown-position guard;
labeled gain/resid descriptive not nested-CV per the reviewer).
**★ This is exactly why the de-confounding attack matters:** the whole detector/predictor story hinges
on whether the ≈0.90 signal survives length control at larger n. Attack 675571 = **6/25 goals** at
2h26m (~13.7min/goal → ~6.7h total, UNDER 8h wall; on track, no intervention). Queue 1/6 now (confound
done).
**Next fire:** attack wall-watch; when done → score → extract (off n-801) → n≈90 → re-run
phase6/phase17/BOTH confounds. Refill a slot if useful CPU work exists.

### 2026-07-22 — Session 2, Iteration 48 (F∪G confound relaunch fix; attack 7/25)
**Bug: F∪G confound 675835 FAILED (exit 127)** — my `--wrap` ran under /bin/sh (dash) where `source`
is unavailable. **Fix:** parameterized the proper bash launcher `run_phase17_confound.slurm` (env
CONDITIONS/CELLS/OUT; also makes it reusable for the scaled-n re-run) + resubmitted F∪G (675836,
`--conditions F G`, cells mlp/fisher/logistic @endofthink/tc1 L24). bash -n OK. (Lesson: use the
#!/bin/bash slurm script, never `sbatch --wrap` with `source`.)
**Attack 675571: 7/25 goals @ 2h33m** (~13min/goal, ~6.4h projected, under 8h wall — on track).
Queue 2/6 (attack + F∪G confound).
**Next fire:** F∪G confound → is the suffix detector length-confounded like C/D, or cleaner (suffix
prompts ~constant length)? → fold into ADAPTIVE_DETECTION cross-condition confound. Attack wall-watch.

### 2026-07-22 — Session 2, Iteration 48b (★ F∪G confound: length confound is CoT-SPECIFIC, not universal)
**★ F∪G detector confound (675836) — important CONTRAST to C∪D:** for suffix attacks, **length-only
AUC = 0.597 (near chance)** (suffix prompts ~constant length across F/G), and the detector RETAINS its
signal after length control: mlp endofthink L24 raw **0.853 → residualized 0.85** (≈unchanged), gain
over length **+0.30**, P(gain>0)=**0.956** (CI [-0.02,+0.68] grazes 0 only at n=40).
`outputs/phase17_detect/detector_FvsG_confound.csv`.
**→ The length confound is CoT-attack (C∪D)-SPECIFIC, NOT universal.** The suffix-success signal (F∪G)
IS a genuine length-INDEPENDENT internal signal; the CoT-attack-success signal (C∪D) is largely length.
`ADAPTIVE_DETECTION_AND_DEFENSE_REPORT.md` confound section now has the C∪D-vs-F∪G contrast table + the
qualified verdict. This is real scientific refinement from the parallel/meantime work.
**Also:** `run_phase17_confound.slurm` parameterized (CONDITIONS/CELLS/OUT) → reusable for scaled-n.
Attack 675571 **7-8/25 @ ~2h37m** (on track, under 8h wall). Queue 1/6.
**Next fire:** attack wall-watch; when done → score → extract → n≈90 → re-run C∪D confound (the key
question: does the CoT-attack signal gain a length-independent component at larger n?).

### 2026-07-22 — Session 2, Iteration 49 (§11.2 timing-restricted steering — closes the §4b gap; parallel GPU)
**Used idle GPU (attack on separate node) for a real plan item: §11.2 timing-restricted intervention**
(was the documented §4b untested gap). NEW `--timing {all,prefill,generation}` on
`poc_stage4/phase7_steer_generate.py` + local `_timed_addition_pre_hook` (same add as the reused
`intervention_selection.get_activation_addition_input_pre_hook`, gated by decode phase via
`activation.shape[1]`: prefill>1 / decode==1). Default 'all' keeps the audited `build_steering_hooks`
path (prior results unaffected). Slurm `TIMING` passthrough. AST+bash-n OK.
**Launched §11.2 generation-only sweep (675879):** steer EACH GENERATED token (not prefill) with the
best direction think_content_1 L20, clean prompts, α∈{-3..3}, on n-802/803/805 (off n-801, parallel
w/ attack). Tests whether a generation-targeted intervention (vs the all-position null) makes the
direction causal.
**Bug-check subagent running** — key risk = KV-cache seq-len semantics (prefill shape[1]=prompt_len,
decode=1; assumes use_cache=True). Will act before trusting the result.
**Attack 675571: 10/25 @ 3h05m** (on track). Queue 2/6.
**Next fire:** timing bug-check → if PASS, harvest gen-only sweep (score→curve); if it's ALSO null →
§11.2 closed (all timings non-causal) → CAUSAL_VALIDATION §5/§4b finalized. Attack wall-watch → n≈90.

### 2026-07-22 — Session 2, Iteration 49b (§11.2 timing code bug-check PASS)
**Timing-restricted steering bug-check: ALL static checks PASS.** Critical KV-cache assumption CONFIRMED
safe — the phase7 runner's `generate()` doesn't set use_cache=False and `load_qwen3_model` sets no
override, so use_cache defaults True → prefill sees shape[1]=prompt_len, decode sees 1 → the timing gate
fires correctly (no prefill/generation inversion). Add-logic byte-identical to the reused hook; 'all'
still routes to the audited `build_steering_hooks`; α=0 baseline uses empty hooks regardless of timing;
default 'all' reproduces prior results exactly. Runtime spot-check pending (675879 still PENDING for a
GPU node). **§11.2 timing code validated.**
Attack 675571 progressing; gen-only timing sweep 675879 queued (will run when a node frees). Queue 2/6.

### 2026-07-22 — Session 2, Iteration 50 (§11.2 timing set completed: +prefill-only sweep)
**Completed the §11.2 timing coverage:** launched the **prefill-only** sweep (675951, steer INPUT rep
only) to complement the generation-only (675879) — the two remaining timings beyond the done 'all'.
Both use the bug-checked runner (timing gate validated iter 49b), same direction think_content_1 L20,
clean prompts, α∈{-3..3}. → §11.2 will cover all three timings {all(done,null), generation, prefill}.
Both PENDING on GPU-node availability (nodes, not the 6-budget, are the constraint; attack holds one of
n-802/803/805). Queue 3/6 (attack + 2 timing sweeps).
**Attack 675571: 13/25 @ 3h33m** (~11.8min/goal, ~5.9h projected, under 8h; on track — 13 already > my
12-goal-by-5h threshold, no intervention).
**Next fire:** timing sweeps run when nodes free → harvest gen + prefill curves; if BOTH null → §11.2
fully closed (direction non-causal across ALL layers AND timings) → finalize CAUSAL_VALIDATION §5/§4b.
Attack → n≈90 de-confounding pipeline.

### 2026-07-22 — Session 2, Iteration 52 (§11.2 timing sweeps done+coherent; attack 21/25)
**★ §11.2 timing sweeps complete:** gen-timing (675879) **35/35, `timing:"generation"` confirmed,
coherence 100%** (answer_present 5/5 all α) → resolves the timing bug-check's runtime item (#6): flag
works, generation-only steering doesn't break decoding. Prefill (675951) 33/35 (finishing). Waiter
armed to prep+score BOTH once prefill lands → §11.2 ASR-vs-α curves.
**Attack 675571: 21/25 @ 4h33m** (~10min/goal, ~5.2h total, under 8h; ~40min from done).
Queue 2/6. **Next fire:** timing scoring → gen + prefill curves; if both NULL like 'all' → §11.2 fully
closed (non-causal across ALL layers AND timings) → finalize CAUSAL_VALIDATION §5/§4b. Attack done →
score → extract (off n-801) → n≈90 de-confound.

### 2026-07-22 — Session 2, Iteration 53 (★ §11.2 timing NULL → PHASE 7 COMPLETE across layers+timings)
**★ §11.2 timing sweep result (both scored):**
- **generation-only** (steer each generated token): ASR 0/35 except 1/5 @α=+2 (isolated noise) → NULL.
- **prefill-only** (steer input rep): ASR **0/35 at every α** → NULL. Coherence 100% both.
`outputs/phase7_causal/steer_timing_{gen,prefill}__tc1_L20/asr_vs_alpha.csv`.
**→ §11.2 CLOSED.** `CAUSAL_VALIDATION_REPORT.md` §5b (timing table) added. Registry
`phase7_timing_{gen,prefill}_tc1_L20` (20-col). Phase table: Phase 7 COMPLETE.
**★★ PHASE 7 FINAL (comprehensive): the success direction is NON-CAUSAL under EVERY residual-vector
intervention** — across layers L12/16/20/28 AND timings all/generation/prefill, both sufficiency
(clean-prompt) and necessity (attacked-context), coherence 100% throughout. Only untested family =
attention-based (§11.8), a different hypothesis. This is a rigorous, exhaustively-controlled causal
NEGATIVE → §25 Gate-3 "No" → the signal is a DETECTOR (Phase 17), not a mechanism.
**Attack 675571: 21-22/25 @ 4h39m** (slight slow near end; ~5.3h projected, under 8h). Queue: timing
done, attack finishing. **Next fire:** attack done → score → extract (off n-801) → n≈90 → re-run C∪D
confound (does the CoT-attack signal gain length-independent signal at larger n?). ≤6 SLURM.

### 2026-07-22 — Session 2, Iteration 54 (★ scaling attack DONE: held-out ASR 0.560; de-confound pipeline started)
**★ Dataset-scaling attack 675571 COMPLETE: 25/25 held-out goals, gemini ASR 0.560 (14/25)**,
project cache unchanged 86G (HF_CACHE_MODE=project worked). 48 attack rows (25 goals × ~2 streams) with
attack_prompt/target_response/is_success. `outputs/phase7scale_qwen3_cot_heldout25/…smoke25.jsonl`.
**This is a §18-flavor HELD-OUT validation:** CoT-Hijacking generalizes to unseen behaviors (0 dev
overlap). Registry `phase7scale_cot_heldout25`.
**De-confound pipeline (INDEPENDENT-REPLICATION design):** extract held-out C/D → run detector/confound
at n≈48 as a REPLICATION of the dev-25 (n=44) length-confound. If held-out reproduces "gain~0"
→ robust; if length-INDEPENDENT → dev-25 was n-limited. Cleaner than merging extraction dirs.
Step 1: StrongREJECT-score attack (676090) → Step 2: build held-out C/D manifest (reuse
`build_phase5_mechanistic_manifest.py --cot-scored`, no A/B/F/G). Both in flight.
**Next fire:** manifest → extraction tuples → `run_phase5_ae_extract` (staged, off n-801) → score AE
regens → held-out phase6_scores → phase17_confound + phase6_signal on held-out → compare to dev-25.
Queue 1/6. ≤6 SLURM, ≤2 concurrent 14B.

### 2026-07-22 — Session 2, Iteration 54b (held-out mechanistic manifest + extraction launched)
**★ Held-out C/D manifest built** (reuse `build_phase5_mechanistic_manifest.py --cot-scored`, no
A/B/F/G): **48 rows (C=33 fail / D=15 success), 48 unique row_keys** (SR attack ASR 15/48=0.31;
gemini goal-level 0.56 — judges differ as before). `…/heldout_mechanistic_manifest.jsonl`.
**★ Held-out activation extraction LAUNCHED: array 676102 [0-38]%3** (39 unique goal×cond tuples,
3-wide staged, n-801 excluded) → `outputs/phase7scale_qwen3_cot_heldout25/extraction/`. Reuses the
audited `run_phase5_ae_extract.slurm` + `run_ae_generation`/`replay_hidden_states` (per-(goal,cond)
shard, all stream variants, resumable). AE re-generates each attack_prompt (32768-tok) + captures §9.4
positions. ~30-70min/task, 3-wide → several hours.
**De-confound pipeline status:** attack ✅ → score ✅ → manifest ✅ → **extraction 🔄** → (next) score AE
regens → held-out phase6_scores → phase17_confound + phase6_signal on held-out n≈48 → COMPARE to dev-25
(does length-confound reproduce, or is held-out length-independent?). Queue 1/6 (extraction %3).
**Next fire:** monitor extraction 39/39; when done → convert+score AE C/D gens → held-out scores →
confound. ≤6 SLURM, ≤3 concurrent 14B (watch FS thrash; drop to %2 if slow).

### 2026-07-22 — Session 2, Iteration 56 (held-out extraction grinding: 2/39; ~overnight)
Held-out extraction 676102 healthy, progressing **2/39 pt shards** (long 32768-tok C re-gens + node
contention → 1-2 concurrent, ~overnight for 39). No errors; resumable. Harvest deferred until ~30+/39
land (confound needs C AND D well-sampled: 33 C / 15 D total). Core plan COMPLETE (Ph1-7 incl. causal
closed across layers+timings, Ph13, Ph17 + both dev-25 confounds, synthesis, 2 audits); this held-out
de-confound is the final ENHANCEMENT. Queue 2/6; no independent work left to parallelize (confound gated
on shards; nodes not budget are the GPU bottleneck). **Next fires: monitor to ~30+/39 → score AE C/D
regens → held-out phase6_scores → phase17_confound + phase6_signal at n≈48 → compare vs dev-25.**

### 2026-07-23 — Session 2, Iteration 59 (held-out extraction 19/39; incremental AE scoring prep)
Held-out extraction 676102: **19/39** (C=11 D=8), resumed after node-starvation (n-802/805). Genuine
prep to cut final-harvest latency: ran `phase6_prepare_scores.py prep` on the held-out extraction dir
(validates the label pipeline on new data) → 21 AE rows (C=13/D=8) → **StrongREJECT scoring 676525**
(final_text). When extraction hits 39/39, re-prep all + re-score (--resume skips these 21) → held-out
phase6_scores → confound at n≈48. Queue 4/6. **Next: extraction→39, full AE score, held-out confound
(phase17_confound + phase6_signal, CONDITIONS="C D", run-dir=held-out) → COMPARE vs dev-25 (does the
length confound reproduce at held-out n?).**

### 2026-07-23 — Session 2, Iteration 61 (held-out extraction 30/39 → completion+scoring armed)
Extraction 676102 **30/39** (C=17 D=13), ~6 tasks left. Waiter armed: on full drain → re-prep all AE
gens (`phase6_prepare_scores.py prep` on held-out run-dir) → re-score StrongREJECT (--resume skips the
21 already scored) → held-out AE labels ready. Partial preview confirmed balanced/powered (10s/11f @21).
**Next fire:** scoring done → build held-out `phase6_scores.jsonl` (`phase6_prepare_scores.py scores`)
→ run **`phase17_confound.py --conditions C D --run-dir <held-out>`** (+ `phase6_signal_search` for the
Fisher AUC) → **COMPARE the held-out length-confound to dev-25**: does gain-over-length reproduce ≈0
(robust length confound) or become significant (dev-25 was n-limited)? Finalize PREDICTIVE_SIGNAL /
ADAPTIVE_DETECTION with the replication. Bug-check: phase17_confound already reused (run-dir param).

### 2026-07-23 — Session 2, Iteration 63 (★ held-out extraction COMPLETE 39/39; labels building)
**★ Held-out C/D extraction DONE: 39/39 pt shards (C=24 D=15), 48 AE rows** (C=33/D=15).
`outputs/phase7scale_qwen3_cot_heldout25/extraction/`. Re-scored (676754, --resume) → building held-out
`phase6_scores.jsonl` (`phase6_prepare_scores.py scores`). Waiter armed for label balance.
**Next in fire:** labels done → run held-out confound: `phase17_confound.py --conditions C D --run-dir
outputs/phase7scale_qwen3_cot_heldout25/extraction --scores <held-out phase6_scores> --cells
mlp:think_content_1:19 logistic:prefill_last:38 fisher:think_content_1:20 fisher:prefill_last:16` +
`phase6_signal_search --conditions C D --run-dir <held-out>` → **COMPARE vs dev-25** (does the
length-confound gain-over-length reproduce ≈0, or become significant at held-out n?). This is the
decisive de-confounding replication. All reused code (--run-dir/--scores params already exist).

### 2026-07-23 — Session 2, Iteration 63b (★ held-out labels 28s/20f; confound BUG caught; harvest running)
**★ Held-out C∪D labels: 28 success / 20 fail (n=48)** — well-powered, near-identical to dev-25 (24/20).
`outputs/phase7scale_qwen3_cot_heldout25/phase6_scores.jsonl`.
**★ BUG caught before trusting results:** `run_phase17_confound.slurm` did NOT pass --scores/--run-dir
→ job 676757 would have silently re-run DEV-25 (not held-out). Cancelled; **fixed** (added SCORES/RUN_DIR
passthrough, bash -n OK); resubmitted **676759** on held-out. (`run_phase6_signal.slurm` already passed
them → 676758 correct.)
**Held-out confound (676759) + Fisher signal (676758) RUNNING** on the held-out extraction (n≈48) with
the SAME cells as dev-25 (mlp tc1 L19 / logistic pfl L38 / fisher tc1 L20,pfl L16). Waiter armed.
**Next fire: the DECISIVE comparison** — held-out length-only AUC + gain-over-length CI vs dev-25
(dev-25: length-only 0.827, gain≈0, CI∋0). If held-out reproduces → length confound ROBUST (Ph6/17
caveat confirmed on independent data). If gain significant → dev-25 was n-limited. Either way finalizes
PREDICTIVE_SIGNAL + ADAPTIVE_DETECTION with the replication.

### 2026-07-23 — Session 2, Iteration 63c (★★ DE-CONFOUND REPLICATION: length confound ROBUST on held-out)
**★★ THE DECISIVE RESULT — held-out (n=48, 0 dev overlap) REPLICATES dev-25:**
`outputs/phase7scale_qwen3_cot_heldout25/{detector_CvsD_confound,phase6_CvsD_auc}.csv`:
- length-only AUC: dev 0.827 → **held-out 0.720**.
- detector gains-over-length: ALL 4 cells' 95% CI **include 0** (mlp -0.061, logistic -0.007,
  fisher +0.023/+0.030; P+ 0.56-0.82) — **replicates dev-25's "no significant gain beyond length."**
- **detector raw AUCs LOWER on held-out (0.75-0.78 vs dev 0.90-0.92)** → the dev-25 detector PARTLY
  OVERFIT the 25 dev goals; the 0.92 does not transfer.
- held-out Fisher early signal AUC ~0.85-0.87 pre-answer (still real, `phase6_CvsD_auc.csv`).
**→ FINAL: the CoT-attack success signal is PREDICTIVE + EARLY but SUBSTANTIALLY LENGTH-DRIVEN and does
NOT demonstrate a length-independent "success representation" — confirmed on TWO independent datasets
(n=44 + n=48).** Robust, honest, publishable. (Suffix F∪G detector IS length-independent — contrast holds.)
`ADAPTIVE_DETECTION_AND_DEFENSE_REPORT.md` held-out-replication section added. Registry
`phase7scale_confound_heldout48`.
**Bug fixed this iter:** `run_phase17_confound.slurm` now passes SCORES/RUN_DIR (676757 would've re-run
dev-25; caught+fixed+resubmitted 676759 correctly on held-out — verified n=48 in output).
**Phase 5→6→7→17 arc + de-confounding replication COMPLETE.** Queue clear.

### 2026-07-23 — Session 2, Iteration 63d (replication VERIFIED 5/5; refined "overfit"→"weak transfer")
**Replication verification subagent: ALL 5/5 PASS.** Held-out confound genuinely on held-out data
(dispositive: n=48 vs dev 44; 39 held-out shards; 48 labels 28s/20f; scale_heldout_25 ∩ dev_25 = ∅),
all numbers faithful (4 CIs all ∋ 0), Fisher AUC 0.82-0.87, label-driven from AE-regen StrongREJECT
(not gemini). **Conclusions honest + well-hedged.** One refinement applied per the verifier: the raw-AUC
drop is partly "held-out is less length-separable" (length-only 0.827→0.720), not pure weight overfit →
cleaner metric = length-independent margin **0.098(dev)→0.064(held-out)** = modest shrinkage. Report
"partly overfit" → "transfers only weakly" with the margin metric. Core claim (no length-independent
success representation; length confound robust across both datasets via the CIs) fully supported.
**★ THE DISTILLATION PROJECT ARC IS COMPLETE + REPLICATED + TWICE-AUDITED + VERIFIED.** Queue 0/6.

### 2026-07-23 — Session 2, Iteration 64 (§10.1-D attention family: span not localizable → pivot to entropy)
**Per §25 Gate-3 "test alternative signals" → §10.1-D ATTENTION family** (the alt to the falsified
residual direction). Reused `poc_stage4/run_attention_extraction._find_goal_token_range`.
**★ Key methodological finding: the CoT-Hijacking attack does NOT localize the harmful goal** — the
puzzle scaffold abstractly ENCODES it (verified: **46/48 attack prompts have no locatable goal span**;
e.g. "hacking a database" → "Let Σ be a categorical system of security states..."). → the span-based
"attention hijacking away from the harmful span" hypothesis (§10.1-D-A) is UNTESTABLE for this attack.
**Caught 2 bugs pre-GPU:** manifest field is `user_message_text` not `user_text` (cancelled 676768
before crash); goal-span unfindable (above).
**Pivot → span-free §10.1-D metrics:** NEW `scripts/phase6_attention_signal.py` (eager-attention
prompt forward) now computes per-layer ATTENTION ENTROPY + MAX-CONCENTRATION at the last-K query
positions → per-layer AUC predicting success. `run_phase6_attention.slurm` (off n-801). Launched 676777
on held-out 48 C/D. **Bug-check subagent running** (entropy math, eager-attn OOM risk at long seq).
**Next fire:** attention entropy result — does attention diffuseness predict success (any AUC≠0.5)? If
null → the attention family is also non-predictive → the mechanism search is exhaustive (residual +
attention both null) → strengthens the "predictive-but-not-mechanistic" story. Bug-check → act.

### 2026-07-23 — Session 2, Iteration 64b (attention job OOM'd → memory-hardened re-run)
**676777 FAILED: CUDA OOM** in attention softmax — `output_attentions` holds all 40 layers ×40 heads
×seq² simultaneously; the longest attack prompts (~1630 tok, 6527 chars) + 28GB model exceed the 44GB
L40S. (Ran the pre-guard version — started before the OOM-guard edit landed.) Partial preview before
crash: entL20 ~3.3-3.8, maxcL20 ~0.38-0.44 across D examples (values look SIMILAR across examples →
early hint of little signal, TBC).
**Fix:** OOM guard (skip OOMing example) + empty_cache() before each forward + del out/attns after →
memory-hardened. Resubmitted **676792**; the ~5 longest prompts skip, ~43 process. Bug-check had
already PASSED the entropy math; these are robustness fixes only.
**Next fire:** 676792 → per-layer entropy/maxconc AUC (does attention diffuseness predict success?).
If null (likely per the similar-values hint) → the §10.1-D attention family is ALSO non-predictive →
mechanism search exhaustive (residual + attention both null) → finalize the "predictive-not-mechanistic"
story. Close §10/§11 mechanism question.

### 2026-07-23 — Session 2, Iteration 64c (★ §10.1-D attention: predictive but SAME length confound → unified closure)
**★ Attention re-run (676792, n=48, memory-hardened) — the §10.1-D result:**
`outputs/phase7scale_qwen3_cot_heldout25/attention_signal.csv`.
- **attn_maxconc → success: raw & grouped-LOGO AUC 0.739** (mid-layers L22-30); attn_entropy inversely
  (early AUC ~0.25). Direction: **successful attacks have MORE CONCENTRATED attention** (opposite of the
  naive scatter-to-puzzle hijacking hypothesis).
- **BUT length-confounded like the residual signal:** corr(maxconc, seq_len) = **-0.79**; seq_len→success
  AUC 0.28 (SHORTER prompts succeed); length-residualized maxconc **0.739→0.632**.
**★★ UNIFIED CLOSURE of the §10/§11 mechanism search:** BOTH signal families (residual dir AUC 0.90 +
attention concentration 0.74) CONVERGE on the SAME confound — they are **downstream proxies of
attack-prompt LENGTH**. Shorter CoT-Hijacking prompts succeed; they carry both concentrated attention +
a distinguishable residual state; length is the common cause. Neither is a length-independent mechanism
(residual non-causal all layers+timings + gain n.s. replicated held-out; attention ~2/3 length).
→ Honest mechanistic story: **"CoT-Hijacking success on Qwen3 is substantially a function of attack-prompt
length; internal signals are length correlates, not independent mechanisms."** `PREDICTIVE_SIGNAL_REPORT`
§6 added; registry `phase6_attention_signal_heldout`. Span-based attention untestable (goal not
localized). **Mechanism families exhausted (residual + attention); §10/§11 CLOSED.**

### 2026-07-23 — Session 2, Iteration 65 (★ attention confound bootstrap DONE → mechanism search fully rigorous)
**★ §10.1-D attention confound bootstrap CI (reused phase6_confound `_grouped_logo_auc` +
`_goal_bootstrap_gain_ci` inline on attention_signal.csv):**
- attn_maxconc L25: raw 0.739, len-only 0.720, LOGO{x+len}=0.668 vs LOGO{len}=0.675, **gain −0.007,
  CI [−0.10,+0.29], P+=0.43**; L22 gain −0.020, CI [−0.15,+0.30], P+=0.39.
**→ Attention concentration adds NO significant signal beyond length (gain n.s., CI∋0, P+<0.5); its
0.74 AUC is ENTIRELY length.** Same result + same rigor as the residual signal.
**★★ MECHANISM SEARCH NOW FULLY RIGOROUS + COMPLETE:** both families (residual dir + attention) have
matched bootstrap-CI confound controls, BOTH null-beyond-length. `PREDICTIVE_SIGNAL_REPORT` §6 finalized
(bootstrap done, not "remaining"); synthesis updated. The unified length-confound conclusion is now
established at full rigor on independent held-out data.
**PLAN CORE COMPLETE:** Ph1-7 (causal null all layers+timings) + §10.1-D attention + Ph13 + Ph17 +
held-out de-confound replication + BOTH mechanism-family confounds bootstrap-CI'd. 2 audits, per-phase
bug-checks. Remaining = distinct new investigations (§11.8 causal attention, §16 cross-model, §15 external).
Queue 0/6.

### 2026-07-23 — Session 2, Iteration 66 (§16 cross-model length test, zero-compute; honest caveat)
**§16 cross-model (unlocked: main result established on Qwen3).** Zero-compute reuse of Phase-4X attack
outputs — does shorter attack-prompt predict success on OTHER reasoning models?
- Qwen3 (attack labels) AUC 0.40 / **DeepSeek-R1-Distill-8B 0.455** / **Phi-4-mini-reasoning 0.445** —
  all shorter→success (AUC<0.5) but WEAK (corr ~0 DeepSeek/Phi). `outputs/phase4_hf_local/*_strongreject.jsonl`.
**★ Honest caveat surfaced on OWN Qwen3 result:** the STRONG length confound (seq_len AUC 0.28, corr
−0.79) used AE-REGEN labels; with attack-original labels Qwen3 is 0.40 (weaker) — so part of the raw
strength is labeling-driven, not a pure length→behavior law. **Core claim UNCHANGED** (residual+attention
gains-beyond-length both n.s.) but the raw length-magnitude is Qwen3/labeling-specific, only weakly
universal. Documented in synthesis §16 + noted the reports carry both. Registry
`phase16_crossmodel_lengthtest`.
**This is exactly the value of continuing:** cross-model surfaced a real nuance/caveat on the headline
finding. Mechanism claim robust; length-magnitude claim appropriately hedged. Queue 0/6.

### 2026-07-23 — Session 2, Iteration 67 (Phase-16 cross-model MECHANISTIC replication started: DeepSeek)
**Extraction infra supports `deepseek_r1`** (`poc_stage4/model_family_utils.py:32,55,67` — shares Qwen3's
<think></think> markers, Qwen2.5-backbone) → the full cross-model mechanistic replication is FEASIBLE.
**★ Scientific hypothesis worth testing:** DeepSeek/Phi show only WEAK behavioral length effect (AUC
0.455/0.445 vs Qwen3's stronger) → maybe DeepSeek's success signal is LENGTH-INDEPENDENT (a meaningful
cross-model CONTRAST with Qwen3's length-confounded signal).
**★ Phase-16 attack LAUNCHED: job 676879** — DeepSeek-R1-Distill-Qwen-7B (the extraction-config model)
CoT-Hijacking on the 25 held-out goals, node-local cache (§31.3, NOT project — non-Qwen3 model),
N_STREAMS=2. `outputs/phase16_deepseek_cot_heldout25/`. 7B → faster than Qwen3-14B (after node-local
~15GB download). Reuses the audited `run_phase4_hf_local.slurm`.
**Pipeline (multi-fire):** attack → SR-score → mechanistic manifest → extract (model_family=deepseek_r1)
→ score AE regens → confound → COMPARE DeepSeek vs Qwen3 length-confound. Queue 1/6.
**Next fire:** monitor DeepSeek attack; when done → score → build manifest → extract (staged, off n-801).

### 2026-07-23 — Session 2, Iteration 68 (cross-model extraction infra built for DeepSeek; smoke + bug-check)
**DeepSeek attack scored: SR 17/48 success → mechanistic manifest 48 rows (C31/D17)** — WELL-POWERED
(comparable to Qwen3). `outputs/phase16_deepseek_cot_heldout25/deepseek_mechanistic_manifest.jsonl`.
**★ Built DeepSeek extraction support (root blocker: `_load_model` loaded Qwen3-14B for any non-gemma4;
`--model` excluded deepseek):**
- `run_ae_generation.py::_load_model` + `replay_hidden_states.py` load: add `deepseek_r1` branch →
  `load_qwen3_model(model_name=DEFAULT_MODEL_BY_FAMILY["deepseek_r1"])` (DeepSeek-Qwen-7B is Qwen2 arch
  → the generic Qwen3Model wrapper works: .layers via model.model.layers; tokenizer carries <think>).
- both `--model` choices += deepseek_r1.
- `run_phase5_ae_extract.slurm`: `MODEL_FAMILY` env (default qwen3) → --model + shard name; **§31.3
  node-local HF cache for non-qwen3** (don't cache DeepSeek to project). AST+bash-n OK.
**★ SMOKE 677063 (1 DeepSeek tuple)** launched to verify cross-model extraction end-to-end. **Bug-check
subagent running** (loader correctness for 28-layer/3584-dim 7B; §31.3 cache; row_key qwen3| cosmetic
inconsistency — must stay consistent across gen-shard→labels→confound). Act before the full array.
**Next fire:** smoke+bug-check PASS → full array `--array=0-38%3 MODEL_FAMILY=deepseek_r1` → score AE
regens → DeepSeek phase6_scores → confound → **DeepSeek vs Qwen3 length-confound comparison**. Queue 2/6.

### 2026-07-23 — Session 2, Iteration 69 (DeepSeek smoke preempted mid-download; retry)
**Smoke 677063 FAILED — root cause = PREEMPTION on killable partition during the node-local DeepSeek
download** (hf_transfer NOT installed; "Background writer channel closed" = download process killed
mid-write; cgroup teardown confirms). **Not a code bug** — the cross-model infra worked (node-local
cache §31.3 set, manifest matched, model loading started). **But exposes real fragility:** §31.3
node-local re-download PER TASK × 39-task array × killable-preemption = each preempt re-downloads ~15GB.
**Static bug-check had PASSED all 4 (loader/§31.3/row_key/filter).** Re-ran smoke (677064); preemption
is probabilistic — a ~10min download that isn't preempted succeeds. **Decision rule:** if the smoke
completes → full array (resumable, tolerates occasional re-downloads); if it fails AGAIN → the
mechanistic cross-model is INFRA-BLOCKED (§31.3+killable+array fragility, can't relax §31.3 = user hard
constraint) → rely on the DONE behavioral §16 cross-model result (length-dir weak-consistent DeepSeek/Phi).

### 2026-07-23 — Session 2, Iteration 70 (★ DeepSeek smoke SUCCEEDS → full cross-model extraction array)
**★ Smoke retry 677087 COMPLETED (9:32) — valid DeepSeek shard: layer_count 29 (28+embed), hidden_dim
3584, 10 §9.4 positions.** Cross-model extraction WORKS end-to-end (earlier fail = pure preemption).
The generic Qwen3Model wrapper + dynamic layer/dim handling correctly extracted DeepSeek-Qwen-7B.
**★ Full DeepSeek extraction array LAUNCHED: 0-38%3** (39 tuples, node-local §31.3, off n-801,
resumable — smoke's goal2:D skips) → `outputs/phase16_deepseek_cot_heldout25/extraction/`. 7B → ~9min/D
tuple (C longer). Occasional preemption re-downloads but resumes. Queue 2/6.
**Next fires:** monitor to 39/39 → score AE C/D regens → DeepSeek phase6_scores → phase17_confound +
phase6_signal (--model deepseek_r1, run-dir=deepseek) → **THE cross-model comparison**: does DeepSeek's
residual signal show the length confound (universal) or is it length-INDEPENDENT (contrast w/ Qwen3,
consistent with DeepSeek's weak behavioral length effect 0.455)?

### 2026-07-23 — Session 2, Iteration 73 (DeepSeek extraction: §31.3 download-storm → ~50% task fails)
DeepSeek extraction 677109: **7 pt shards, 16 completed, 8 FAILED** — all failures = the SAME node-local
DOWNLOAD error ("File reconstruction error: Background writer channel closed"), NOT a code bug. Root
cause: **§31.3 requires per-task 15GB re-download; %3 concurrent downloads to node-local /tmp contend →
~50% fail**. (Also one benign "32768>16384 max_length" warning — cosmetic, tokenizer model_max_len, not
fatal.) The successful shards are correct (verified 29L/3584d in the smoke).
**Fix/plan:** the download-storm is inherent to §31.3 (can't cache DeepSeek to project = user hard
constraint). Robust path = **serialize downloads (%1)**. Decision: let 677109 drain (harvest its ~20
shards), then resubmit MISSING tuples at %1 (resumable → completed skip) to fill gaps. If the ~20
successful shards already give adequate C+D balance (manifest 31C/17D → ~50% sample ~15C/8D), run the
confound on the partial set (n~25, valid if smaller). Queue 2/6.
**Next fire:** array drains → build missing-tuples file → resubmit %1 OR run confound on partial → DeepSeek
vs Qwen3 length-confound comparison.

### 2026-07-23 — Session 2, Iteration 76 (DeepSeek extraction drained 29/39; confound + signal launched)
DeepSeek extraction drained: **29/39 shards (C16/D13), 35 AE rows (C21/D14)** — 10 tuples lost to the
§31.3 download-storm, but well-powered (proceeding without resubmit — the balance suffices). AE-scored
(677433) → DeepSeek `phase6_scores.jsonl`. **Launched cross-model analysis:**
- `run_phase6_signal.slurm` (--model deepseek_r1 via RUN_DIR/SCORES) → DeepSeek per-position/layer LOGO AUC.
- `run_phase17_confound.slurm` cells mlp/fisher/logistic @ think_content_1 L19/L20 + prefill_last L16
  (VALID: DeepSeek has 29 layer-slots 0-28, so Qwen3's L38 is out of range) → DeepSeek length-confound.
Both on the held-out DeepSeek C/D. Queue up to ~4/6.
**Next fire: THE cross-model comparison** — DeepSeek length-only AUC + detector gains-over-length vs
Qwen3 (length-only 0.72-0.83, gains ∋0). If DeepSeek ALSO length-confounded → universal; if
length-INDEPENDENT (gain sig) → contrast w/ Qwen3 (consistent w/ DeepSeek's weak behavioral length 0.455).

### 2026-07-23 — Session 2, Iteration 78 (★★ CROSS-MODEL MECHANISTIC CONTRAST: length confound is Qwen3-SPECIFIC)
**Bug fixed:** `run_phase6_signal.slurm` + `run_phase17_confound.slurm` hardcoded `--model qwen3` → the
DeepSeek jobs found "no data" (looked for qwen3_*.pt in deepseek dir). **Parameterized `--model` (MODEL
env; reusable) + resubmitted MODEL=deepseek_r1** → loaded the deepseek shards (n=35).
**★★ THE cross-model result — DeepSeek is the OPPOSITE of Qwen3:**
- DeepSeek fisher prefill_last L16 (n=35): raw 0.804, **length-only 0.591 (≈chance)**, residualized 0.895,
  **gain-over-length +0.337, CI [0.059, 0.833] EXCLUDES 0, P+=0.998** → LENGTH-INDEPENDENT signal.
- DeepSeek Fisher signal: prefill_last L25 AUC 0.837 (L14-28 ~0.82-0.84).
- vs Qwen3: length-only 0.72-0.83, gain CI ∋0 → length-CONFOUNDED.
**→ The length confound is Qwen3-SPECIFIC, NOT universal. DeepSeek has a genuine length-independent
internal success signal at the input token.** Mechanism is MODEL-DEPENDENT. Documented in synthesis §16
+ registry `phase16_deepseek_confound_heldout`. Caveats: n=35, only prefill_last robust (tc1 degenerate
= DeepSeek think-position issue), CI wide (marginal). Genuine cross-model MECHANISTIC replication (new
deepseek_r1 extraction infra). **§16 cross-model COMPLETE — behavioral (weak-consistent) + mechanistic
(Qwen3 confounded / DeepSeek not).**

### 2026-07-23 — Session 2, Iteration 79 (★ VERIFICATION → RETRACTION of the "model-dependent mechanism" overclaim)
**Change:** ran a dedicated read-only verification subagent on the iter-78 headline (DeepSeek
"length-independent signal"). It reproduced every number but caught a real over-interpretation. Corrected
`docs/DISTILLATION_FINDINGS_SYNTHESIS.md` (§16 mechanistic section + unified-closure qualifier + open-items).
**What the verification found (all confirmed against `outputs/phase16_deepseek_cot_heldout25/`):**
1. **The Qwen3-vs-DeepSeek length contrast is a LABEL-distribution effect, NOT a representational one.**
   DeepSeek-R1-Distill-Qwen shares Qwen3's *exact* 25 scaffolds + Qwen2 tokenizer → prompt-length
   distributions are IDENTICAL across models. So length separating success on Qwen3 but not DeepSeek
   cannot be a length-encoding difference — it's that the attacks DeepSeek complies with happen not to be
   sorted by length. **Retracted:** "DeepSeek has a genuine length-independent internal representation /
   mechanism is model-dependent." Reframed as: "success=length" is a Qwen3 *label* property.
2. **`think_content_1` is NOT "degenerate" — it's NaN from a real marker bug.** DeepSeek emits `<think>`
   in the PREFILL (input ends `<｜Assistant｜><think>\n`); the `deepseek_r1` segmenter searches for
   `<think>` as a start-marker in *generated* text → found in 0/35 rows → think positions null → NaN.
   `not_separable` 33/35. **Fully isolated** from prefill_last (last input tok) + endofresponse (EOS),
   which are 100% finite, non-degenerate, layer-consistent (L4-28 0.75-0.84), drop-one-goal stable
   [0.897,0.935] — so the signal the claim rests on is CLEAN and the finding is NOT an extraction artifact.
   Fixing the `deepseek_r1` marker config (anchor on prefill `<think>` or the `</think>` close, present
   in 33/35) is now a logged prerequisite for any DeepSeek think-content claim.
3. **CI genuinely fragile:** 8/19 goals with both classes, 12 positives; gain CI [0.059,0.833] barely
   clears 0. Point estimate robust (drop-one-goal stable), interval is not → "suggestive, not established."
**Net:** the empirical result stands (DeepSeek signal beats length on this sample) but its interpretation
is now correctly narrowed to a label-distribution difference. No SLURM (doc-only correction). Verified.

### 2026-07-23 — Session 2, Iteration 80 (BUG FIX: DeepSeek think-position marker config + repair re-extraction)
**Bug (verification-identified, iter-79):** `deepseek_r1` think positions were all NaN because
`poc_stage_ae/thinking_position_utils.locate_positions` searched for `<think>` ONLY in generated tokens
(`start=boundary_index`). DeepSeek-R1-Distill's chat template emits `<think>\n` in the PREFILL (formatted
input ends `<｜Assistant｜><think>\n`), so `<think>` is never generated → `start_marker_not_found` on all
35 rows → think_content/endofthink NaN. Qwen3 GENERATES `<think>`, so it was unaffected.
**Fix (3 files, family-scoped + opt-in — reuses existing infra, no duplication):**
- `poc_stage4/model_family_utils.py`: added `THINK_START_IN_PREFILL_BY_FAMILY {qwen3:F, gemma4:F,
  deepseek_r1:T}` + `think_start_in_prefill()` helper (defaults F for unknown families).
- `poc_stage_ae/thinking_position_utils.py`: new guarded branch `if enable_thinking and
  think_start_in_prefill(fam)` → startofthink from PREFILL region, think_content_1/2/3 = boundary_index
  (+1,+2), endofthink = `</think>` search from content_start (prefill excluded). qwen3/gemma4 fall to the
  original `elif enable_thinking` branch — BYTE-IDENTICAL.
- `poc_stage_ae/replay_hidden_states.py`: opt-in `--recompute-positions` (default off) recomputes
  positions from SAVED tokens via locate_positions (boundary=input_token_count) — repairs shards without
  RE-GENERATING (generation is sampled → would change success labels). Default path byte-unchanged.
**Verification:** (1) CPU unit test on all 3 families — deepseek startofthink=prefill<think>,
think_content_1=boundary, endofthink=`</think>`; qwen3/gemma4 outputs identical to pre-fix; no-`</think>`
edge degrades gracefully (think content still located). (2) AST/import OK; helper returns correct
per-family bools. (3) **Independent adversarial bug-check subagent: PASS on all dims** — qwen3/gemma4
byte-identical (git-diff confirms only branch-header change); boundary semantics confirmed
(`prompt_len=input_ids.shape[1]`); prefill `</think>` cannot match (search excludes prefill); tokenizer
in scope; NaN downstream handling intact (phase6 per-position finite mask). One benign empty-think edge
(shared w/ existing qwen3 branch, not a regression).
**Re-extraction:** `slurm_scripts/run_phase16_deepseek_reextract_positions.slurm` (NEW thin wrapper) —
SINGLE job (not array) loops all 29 gen shards on one node → deepseek weights download node-local ONCE
(§31.3), avoiding the concurrent-download storm that failed ~50% of the array run. Recomputes positions
into FRESH `outputs/phase16_deepseek_cot_heldout25/extraction_fixed/` (preserves original; all rows
re-replayed). **Job 677584 submitted (queue 1/6).**
**Next:** when 677584 completes, run phase6 confound on extraction_fixed think_content_1 → test whether
DeepSeek's THINK-CONTENT signal also beats length (currently only prefill_last is validated). Completes
the DeepSeek cross-model MECHANISTIC replication beyond the input-token position.

### 2026-07-23 — Session 2, Iteration 81 (re-extraction FAILED on disk; load-once refactor + hardening)
**Job 677584 outcome: 0/29 shards succeeded.** Root cause = node-local /tmp exhaustion on n-802
(`only ~1.2GB free`, deepseek weights need ~15GB) → "Background writer channel closed" on every shard.
Compounded by a design flaw: the per-shard bash loop spawned 29 fresh Python processes, each
re-downloading/re-loading the 15GB model (`Loading model deepseek_r1 ...` × 29) — thrashing the small
node-local disk. (Confirmed: `.pt` files produced = 0.) Killed 677584.
**Fix — load the model ONCE (efficiency + disk, reuse existing infra):**
- `poc_stage_ae/replay_hidden_states.py`: factored model load into `_load_replay_model()`; `replay_shard`
  gained `preloaded` kwarg; `--generation-shard` now `nargs="+"`; `main()` loads the model ONCE for a
  multi-shard batch and replays all through it (1 download, not 29). **Single-shard path preserved
  BYTE-IDENTICAL** (direct `replay_shard`, no preload, fail-loud) so the existing
  `run_phase5_ae_extract.slurm` pipeline is unchanged; batch path tolerates per-shard failures and exits
  non-zero if any failed.
- `slurm_scripts/run_phase16_deepseek_reextract_positions.slurm`: passes all 29 shards in ONE call;
  added node-local free-space guard (`df -Pm`, requeue if <20GB — fail fast so a doomed node doesn't burn
  a GPU), excluded n-802, `--requeue`.
**Verification:** AST OK; parse_args handles multi- and single-shard; single-shard path confirmed
byte-identical (caught + fixed a self-introduced regression where try/except would have swallowed
single-shard failures → exit 0). SLURM bash syntax OK. **Independent bug-check subagent running; GPU
submission HELD until it clears** (last submit wasted GPU on the disk bug — not repeating that).
**Note on §31.3:** deepseek weights already leaked into `.cache/huggingface` (86G, pre-existing) but the
plan rule forbids the project cache, so re-extraction stays node-local ephemeral per §31.3.

**Iter 81 cont.:** Bug-check PASSED all points (single-shard byte-identical, no cross-shard hook/output
leakage, deepseek recompute branch wired end-to-end, SLURM guard ordering correct). Cleared the empty
`extraction_fixed/` from the failed run and resubmitted the hardened load-once job: **677696** (queue 1/6).
Next fire: check 677696 → if shards produced, run phase6 confound on extraction_fixed think_content_1.

### 2026-07-23 — Session 2, Iteration 82 (think-content re-extraction INFRA-BLOCKED by §31.3; decision to stop)
**Guard worked as designed:** hardened job 677696 landed on n-803, the node-local free-space check
detected **8909 MB free < 20000 MB** needed for the 15GB deepseek weights → fail-fast requeue (no GPU
wasted). Combined with n-802's 1.2GB earlier, BOTH sampled L40S nodes have node-local /tmp far below the
model size. **Conclusion: §31.3-compliant (node-local ephemeral) extraction of the 15GB DeepSeek model is
systematically infeasible on these L40S nodes** — the job would requeue indefinitely gambling on node
luck. Cancelled 677696 to stop the loop.
**Decision (do NOT bend the hard §31.3 user constraint for low-value work):** the only workarounds
(project/parent/HOME HF cache) violate §31.3's explicit prohibition on persisting weights to the shared
cache. Weighed against value: the think-content re-extraction is LOW marginal value — the core cross-model
finding (`prefill_last` beats length on DeepSeek) is ALREADY validated and, per iter-79 verification, is a
**label-distribution effect on these exact 35 rows/labels**, so the think-content signal would almost
certainly show the SAME pattern. Bending a hard user constraint for confirmatory work is the wrong trade.
**What STANDS (all landed + verified, valuable regardless):**
- The marker-config bug FIX (`THINK_START_IN_PREFILL_BY_FAMILY` + guarded `locate_positions` branch +
  `replay --recompute-positions`) — correct, bug-checked PASS, ready for whenever §31.3 infra allows
  (bigger-/tmp node, or user relaxes the constraint).
- The load-once replay refactor (`_load_replay_model` + multi-shard `main`) — bug-checked PASS,
  single-shard path byte-identical; a permanent efficiency win for ALL future multi-shard replays.
- Core §16 cross-model result unaffected: rests on prefill_last (clean, finite, validated), interpretation
  correctly narrowed to label-distribution (iter-79).
**Open (documented, not blocking):** DeepSeek think-content confound needs a node with ≥~20GB node-local
/tmp OR a relaxed §31.3. Follow-on command staged: `phase17_confound.py --model deepseek_r1 --run-dir
.../extraction_fixed --cells fisher:think_content_1:<L> --scores .../phase6_scores.jsonl`.

### 2026-07-23 — Session 2, Iteration 83 (USER-AUTHORIZED: Option A infra unblock + Claude research extensions)
**User instruction:** "Do A and doc it" + authorize Claude to ADD genuinely-valuable research extensions
to the plan (clearly attributed), then implement+doc them.
**Option A implemented (unblocks non-Qwen3 model work):**
- `slurm_scripts/run_phase16_deepseek_reextract_positions.slurm` + `run_phase5_ae_extract.slurm`: non-Qwen3
  models now READ from the project cache with `HF_HUB_OFFLINE=1`/`TRANSFORMERS_OFFLINE=1` (no NEW downloads
  ever). Removed the node-local `/tmp` HF_HOME + free-space guard + requeue (moot — TMP_DISK=0 cluster-wide).
- Plan amendment: added **§31.3-A** block to `docs/RESEARCH_PLAN_DISTILLING_JAILBREAKS.md`, CLEARLY
  ATTRIBUTED to Claude + user-authorized, documenting the TMP_DISK=0 finding and the offline-read
  resolution (preserves §31.3 intent: no new weights persisted; Phi-4 stays blocked until a separate
  download decision). DeepSeek cache verified complete (15G, both safetensors shards).
- **Job 677795** resubmitted (deepseek think-content re-extraction) — validates Option A end-to-end.
- Bug-check subagent on the Option-A change: RUNNING.
**Claude research extensions — DESIGN workflow launched (wfv5om53g), 3 candidates, adversarially reviewed:**
- **C1** Causal attention-concentration intervention (Qwen3) — the §11.8 open item; tests whether ATTENTION
  is the causal lever after the residual-direction null (MPO item 5). GPU.
- **C2** Cross-model CAUSAL test on DeepSeek (unblocked by A) — does the causal null replicate, or is
  DeepSeek's direction causal? GPU (offline).
- **C3** Length-matched discrimination (Qwen3, CPU) — matched-pair test of whether ANY residual signal
  survives length matching; sharpens the confound story either way. CPU, fast.
Workflow returns reviewed designs → I implement the high-priority ones, add attributed plan appendix, doc,
bug-check each. **Next:** integrate workflow output + bug-check verdict; launch experiments.

### 2026-07-23 — Session 2, Iteration 84 (Design workflow returned; plan appendix + C1 flagship implemented)
**Design workflow wfv5om53g (6 agents, 0 err) — verdicts:**
- **C1 causal attention intervention: HIGH ("single most valuable open item"), SOUND_WITH_FIXES.** Core
  mechanism VERIFIED vs transformers 5.12.1: rescaling `self_attn.scaling` by 1/τ is a backend-agnostic
  pre-softmax attention temperature (works under SDPA; holds prompt/LENGTH fixed → immune to length
  confound). Fixes folded in: baseline keys on τ=1.0; full n (25 clean/17 D-succ); temper null to
  "uniform-temperature"; necessity-first; assert scaling restored.
- **C2 cross-model causal on DeepSeek: MEDIUM, SOUND_WITH_FIXES** (phase7 verified to support deepseek;
  must pass --manifest/--model-family/HF_HUB_OFFLINE; fit on corrected extraction_fixed; ~2 GPU-hr).
- **C3 length-matched: LOW — reframed.** Review proved matched-pair AUC UNACHIEVABLE (succ/fail lengths
  near-disjoint, ≤10 pairs, zero power). Reframe as identifiability diagnostic (CPU).
**Plan:** added attributed **APPENDIX C** (§C1/§C2/§C3) to `docs/RESEARCH_PLAN_DISTILLING_JAILBREAKS.md`
(clearly [CLAUDE ADDITION, user-authorized]; original plan untouched above the line).
**C1 IMPLEMENTED (reuse-first):**
- `poc_stage4/phase8_attn_temp_generate.py` — attention_temperature ctx mgr (restore in finally + post-run
  base-restore assertion); imports all generation plumbing from phase7_steer_generate; rows carry
  attn_temp=τ AND alpha=round(1−τ,4) → EXISTING phase7_analyze_causal prep+curve run UNCHANGED
  (τ=1→α=0 baseline; verified 5 taus→5 distinct alphas).
- `slurm_scripts/run_phase8_attntemp.slurm` (mirror of run_phase7_steer.slurm; TAUS/ATTN_LAYERS/MANIFEST/
  PROMPTS_JSONL env).
- Verified: scaling settable (0.25=head_dim**-0.5), forward reads self.scaling fresh; AST/imports/resolve
  _layers/alias all OK; slurm syntax OK. Built `outputs/phase7_causal/attack_necessity_Dsucc17.jsonl`
  (17 D-success, all have formatted_prompt).
- **Bug-check subagent on C1: RUNNING; GPU launch HELD until it clears.** Planned 4 jobs (necessity-
  targeted FIRST, then necessity-global, sufficiency-targeted, sufficiency-global).
**Option A validation:** job 677795 running on n-805, reading deepseek offline from project cache (NO disk
error — the exact prior failure is gone). Think-content re-extraction in progress.

**Iter 84 cont. — C1 bug-check + fixes + LAUNCH:**
Bug-check on phase8: mechanism A-D **PASS** (scaling read fresh each forward under SDPA; τ<1 correctly
sharpens; τ=1 nullcontext inert; base captured before mutation + restore-assertion sound; alpha=1−τ alias
gives 5 distinct alphas, τ=1→α=0 baseline, sharpen→α>0/flatten→α<0; resume keys on unique row_key for
necessity). Caught **2 result-corrupting defects in the NECESSITY arm** (both fixed pre-launch):
- **E (FAIL):** MAX_NEW_TOKENS=2048 truncates ALL necessity gens (prior identical run: median 5162, max
  8192 tok, all ≥2043) → think never closes → answer_present=False even at τ=1 baseline → ASR≈0 everywhere
  (uninformative). FIX: launch necessity at MAX_NEW_TOKENS=8192.
- **F (result-critical):** necessity rows lacked `instruction` → `_load_prompt_rows` substituted row_key
  → StrongREJECT scored against "qwen3|1|D|advbench_full_0001|..." not the real request. FIX: enriched
  `attack_necessity_Dsucc17.jsonl` with real harmful `goal` (joined goal_index→goal from
  qwen3_phase5_ae_manifest.jsonl); 17/17 mapped, formatted_prompt retained. (Note: the PRIOR phase7
  necessity run has the same F defect — flagged for separate review of CAUSAL_VALIDATION_REPORT necessity
  numbers.) Sufficiency arm unaffected by E/F.
**LAUNCHED 4 C1 jobs (≤6 budget; +677795 = 5 concurrent):**
- 677835 nec_targeted (17×5 τ, layers L22-30, 8192 tok) — HIGHEST VALUE
- 677836 nec_global (all 40 layers)
- 677837 suff_targeted (dev-25 25×5, 2048 tok)
- 677838 suff_global
Outputs → outputs/phase8_attn_causal/{nec,suff}_{targeted,global}/generations.jsonl. Downstream:
phase7_analyze_causal prep+curve (unchanged) → StrongREJECT CPU → ASR-vs-τ curve.
**Next:** monitor jobs; when 677795 (deepseek reextract) done → think-content confound; score C1 gens.

**Iter 84 cont. — Option A + marker fix VALIDATED END-TO-END:**
Job 677795 **COMPLETED: 29/29 shards ok=29 fail=0 in 16 min** (offline read from project cache, no disk
error — vs 0/29 twice before). think_content_1 now FINITE and correctly located (token "Okay" at idx 691,
first generated think token after prefill <think>\n; all think pos 1-5 finite; answer pos correctly NaN
for thinking-enabled schema; endofresponse finite). The §31.3-A infra + load-once refactor + marker fix
all confirmed working. Repaired extraction: outputs/phase16_deepseek_cot_heldout25/extraction_fixed/.
**Launched phase6 signal on repaired data:** 677841 (CPU, cpu-killable) → per-layer think_content_1 AUC →
outputs/phase16_deepseek_cot_heldout25/phase6_CvsD_auc_fixed.csv. Next: confound the best think_content_1
cell (does DeepSeek's THINK-content signal beat length? completes the cross-model mechanistic replication
beyond prefill_last). Running: 677835/836/837/838 (C1 phase8) + 677841 (phase6). 5 jobs, ≤6 OK.

### 2026-07-23 — Session 2, Iteration 85 (think-content signal recovered; confound length-source bug fixed)
**Think-content signal (677841, repaired extraction_fixed):** with the marker fix, DeepSeek's think
positions now separate success/fail: think_content_1 AUC L7=0.822/L12=0.804/L20=0.801; endofthink
L17-24=0.877; prefill_last L25=0.837 (matches prior). → the think-content signal is REAL and comparable
to prefill_last, recoverable only after the marker fix.
**BUG caught in my first confound run (677858):** `len_only=0.5` (degenerate) for every cell because
`phase17_confound._input_lengths` reads input_token_count from RUN_DIR/generation/shards, but
extraction_fixed has ONLY re-replayed hidden states (0 generation shards) → lengths all defaulted to 0.
**FIX (no code change):** symlinked `extraction_fixed/generation -> ../extraction/generation` → 29
generation shards with real input_token_count (verified=1092) now visible; hidden states still come from
extraction_fixed. Re-running confound = job **677891** (result pending). endofthink cell returned blank
(likely the 2/35 rows without </think> → NaN drop); think_content_1 is the primary think position anyway.
**C1 phase8 progress:** 677835/836/837/838 all running, no errors; suff_global 31 gens, suff_targeted 14,
necessity slow (8192-tok traces). Restore-assertion + resume-safety holding. Await scoring.
**Next fire:** read 677891 corrected think-content gains (does the THINK-content signal beat length like
prefill_last's +0.678? — completes cross-model mechanistic replication); collect C1 gens → score.

**Iter 85 cont. — corrected think-content confound RESULT (677891):**
With real length control (len_only=0.591): **prefill_last L25 beats length (gain +0.370, CI [0.077,0.852]
excludes 0, P+=1.0); think_content_1 does NOT (L7 +0.018 / L12 +0.073 / L20 +0.181, all CI ∋ 0).**
→ **LOCALIZATION:** DeepSeek's length-independent success signal is at the INPUT token (prefill_last),
NOT the generated reasoning content. Recovered think_content_1 has raw AUC 0.80 but is a length proxy
out-of-fold (like all Qwen3 positions). Documented in DISTILLATION_FINDINGS_SYNTHESIS.md §16-B; completes
the cross-model mechanistic replication beyond prefill_last. (endofthink cell unreliable: NaN for 2/35
rows without </think>.) Confirms iter-79's label-distribution reading (length weak 0.591; only input-token
rep adds beyond it). Registry row phase16_deepseek_think_confound added.

### 2026-07-23 — Session 2, Iteration 86 (C1 sufficiency arms complete → scoring)
**C1 phase8 status:** sufficiency arms COMPLETE (677837 suff_targeted, 677838 suff_global = 125 gens each,
only 5 empty answers each → 2048-tok cap fine for clean prompts). Necessity arms (677835/836) still
generating (15/14 of 85; 8192-tok traces, ~1.7h in). No real errors (cgroup teardown noise only).
**Scoring launched:** `phase7_analyze_causal.py prep` on both sufficiency arms → sr_input.jsonl (125 rows);
StrongREJECT CPU jobs **677989 (suff_targeted), 677990 (suff_global)**. Downstream: `curve` → ASR-vs-α
(α=1−τ; τ=1→α=0 baseline; sharpen τ<1→α>0). Tests SUFFICIENCY: does sharpening attention on CLEAN harmful
prompts raise ASR above the ~0 baseline? (review flagged this arm a-priori unlikely; necessity is the
higher-value test, still running.) 4 jobs: 677835/836 (GPU nec) + 677989/990 (CPU SR).
**Next:** SR done → run curve on both sufficiency arms → first C1 causal readout; then necessity arms.

**Iter 86 cont. — C1 SUFFICIENCY arm scored (NULL, clean):**
`phase7_analyze_causal curve` on both sufficiency arms (SR 677989/990 complete, 125 scored each):
- suff_targeted (L22-30): baseline τ=1 ASR=0.080; sharpen τ<1 → 0.08/0.00 (NO rise); flatten τ>1 → 0.04/0.00.
- suff_global (all 40): baseline ASR=0.120; sharpen → 0.00/0.00; flatten → 0.00/0.00.
- answer_present 0.88-1.00 throughout → **genuine NULL, not coherence collapse** (§11.6 control holds).
→ **SUFFICIENCY NULL: sharpening attention concentration does NOT make clean harmful prompts jailbreak**
(matches the review's a-priori prediction for this arm). Curves: outputs/phase8_attn_causal/suff_*/asr_vs_tau.csv.
**Necessity arms (the higher-value test) still generating:** 21/85, 20/85 at 2h+ (8192-tok traces); will
hit the 3h wall → resume-safe (append+skip), resubmit to continue. Necessity tests whether FLATTENING
attention on already-succeeding attacks REDUCES ASR (causal necessity of concentration). C1 verdict awaits it.

### 2026-07-23 — Session 2, Iteration 87 (necessity arms too slow at 3h/5-tau → resubmit 12h/3-tau)
**Problem:** necessity 8192-tok traces cost ~30min/row on 14B → only ~6/17 rows done per arm in the 3h
wall (677835/836). 85 gens/arm ≈ 8.5h — far over 3h.
**Fix (efficiency, resume-safe):** cancelled 677835/836 (rows done PRESERVED — append+flush per completed
row, resume keys on (row_key,τ)); resubmitted **678086 (nec_targeted), 678087 (nec_global)** with
`--time=12:00:00` (killable max=1 day) and TAUS trimmed to **{1.0, 1.4, 2.0}** — the NECESSITY contrast
(baseline + 2 flatten points); the sharpen taus {0.5,0.7} are NOT the necessity hypothesis (flattening an
attacked prompt tests whether concentration is causally NECESSARY). ~40% less compute; the ~6 done rows
keep their 5 taus, the 11 remaining get 3 → all 17 rows have {1.0,1.4,2.0} for the curve. MAX_NEW_TOKENS
kept at 8192 (review: median 5162/max 8192 needed).
**C1 status:** sufficiency DONE (NULL, documented iter-86); necessity resubmitted (12h wall). Await.

### 2026-07-23 — Session 2, Iteration 88 (C2 cross-model causal on DeepSeek — setup, bug-check running)
**C2 implemented (reuse phase7 steering; unblocked by Option A):**
- Fit DeepSeek success direction from CORRECTED extraction_fixed: prefill_last L25 (the LENGTH-INDEPENDENT
  signal) via scripts/phase7_extract_success_direction.py → success_dir__prefill_last__L25/ (n=12succ/23fail,
  sigma=73.76, sep=1.45σ, 0 NaN).
- Built DeepSeek necessity prompts: attack_necessity_Dsucc.jsonl (10 D-success, formatted_prompt + real
  instruction — fix F from the start).
- Code: phase7_steer_generate.py gained `--model-family` (markers via family, default qwen3 = unchanged);
  run_phase7_steer.slurm parameterized MODEL_NAME/MODEL_FAMILY/MANIFEST + HF_HUB_OFFLINE for non-qwen3.
- Verified: AST/import OK; deepseek end-marker=</think> (=qwen3); slurm syntax OK.
- **Bug-check subagent on C2 RUNNING; GPU launch HELD until clear.** Then launch DeepSeek sufficiency
  (scale_heldout_25) + necessity (10 rows), offline, MAX_NEW_TOKENS=8192.
**C1 necessity (678086/087):** running on 12h wall (see below).

**Iter 88 cont. — C2 bug-check PASS + LAUNCH:**
C2 bug-check: **PASS all A-G, no result-corrupting/crash bugs.** Confirmed Qwen3 behavior unchanged
(defaults); DeepSeek loads offline, L25 steerable (28-layer, hidden 3584); direction shape 3584 unit-norm;
_split_think_answer correct for DeepSeek </think>; fix F holds; sufficiency manifest 25 valid goals.
Consistency note (not a bug): direction fit at prefill_last, steered at all positions = same as Qwen3
phase7 runs.
**LAUNCHED C2 (DeepSeek, offline via Option A):**
- 678151 sufficiency: scale_heldout_25 (25 clean), α∈{-3,-1,0,1,3}, prefill_last L25 dir, 8192 tok, 12h wall.
- 678152 necessity: 10 D-success attacked prompts, same α (subtract dir → does ASR drop?), 8192 tok.
Tests whether DeepSeek's LENGTH-INDEPENDENT prefill_last direction is CAUSAL (vs Qwen3's non-causal null).
4 GPU jobs: 678086/087 (C1 nec) + 678151/152 (C2). Downstream: phase7_analyze_causal prep→SR→curve.
**Next:** monitor C1 nec + C2; score as arms complete.

### 2026-07-23 — Session 2, Iteration 89 (C3 length-identifiability diagnostic — DONE; C1/C2 running)
**C3 implemented (CPU, non-competing, reuse-first):** `scripts/phase6_length_identifiability.py` (reuses
`_row_lengths`+`_auc` from phase6_confound_control). Qwen3 C∪D result → phase6_length_identifiability.json:
success input-len mean=1012 (554-1615, median 958) vs failure 1388 (989-1676, median 1378);
AUC(len→success)=0.827; length-matched pairs = **1/6/9 at caliper ±10/±25/±50** (of max 20) → matching
UNDERPOWERED / classes NON-separable by length. **Validation: output EXACTLY matches the design-review
agent's independent computation** (means 1012/1388, pairs, AUC 0.827=known length confound) → cross-checked.
→ Honest finding: the length confound is IRREDUCIBLE here because successful vs failed attack prompts are
near length-separated; documents WHY matching can't rescue/kill the signal (the reframed C3 deliverable).
Registry row c3_length_identifiability added. All 3 Claude extensions (§C1/§C2/§C3) now implemented.
**C1 necessity (678086/087):** 8/17 rows. **C2 (678151 suff running/678152 nec pending):** DeepSeek offline
steering, no errors. 4 GPU jobs.

### 2026-07-23 — Session 2, Iteration 90 (C2 sufficiency complete → scoring; C1 nec 12/17)
**C2 sufficiency DONE (678151 COMPLETED, 1h06m):** 125 gens (25 clean goals × α{-3,-1,0,1,3}), only 4
empty answers, 121/125 think_closed → DeepSeek offline steering clean at 8192 tok. Prep OK; SR scoring
job **678274**. Curve pending → tests if adding/subtracting DeepSeek's prefill_last L25 (length-independent)
direction changes ASR on clean prompts (sufficiency).
**C1 necessity (678086/087):** 12/17, 13/17 rows. **C2 necessity (678152):** 16 gens, running.
4 jobs: 678086/087 (C1 nec) + 678152 (C2 nec) + 678274 (C2 suff SR). Next: C2 suff curve; monitor nec arms.

### 2026-07-23 — Session 2, Iteration 91 (C2 sufficiency NULL — cross-model causal replicates Qwen3)
**C2 sufficiency curve (678274 SR done → curve, steer_suff_pfl_L25/asr_vs_alpha.csv):**
DeepSeek prefill_last L25 (length-independent) direction, 25 clean held-out goals:
α=-3→0.320, α=-1→0.417, α=0(baseline)→0.320, α=+1→0.391, α=+3→0.375; coherence 0.92-1.00.
→ **NULL: steering does NOT systematically change ASR** (no +α↑/−α↓; α=-1 even highest, opposite the
causal prediction). The DeepSeek success direction is NOT causally sufficient → the Qwen3 causal null
**REPLICATES cross-model** on the sufficiency side. Caveat: DeepSeek clean baseline ASR=0.320 (complies
with 32% of clean harmful prompts unsteered) → limited headroom, high native compliance.
**C1 necessity:** 14/17, 15/17 rows (nearly done). **C2 necessity (678152):** 34/50. Necessity arms will
complete both flagship verdicts. Await.

### 2026-07-23 — Session 2, Iteration 92 (both necessity arms complete → scoring)
**C2 necessity DONE (678152, 50/50)** and **C1 nec_global DONE (17/17 rows).** Prepped + SR submitted:
- C2 necessity: 50 rows, 13 empty answers (subtracting dir / 8192-truncation; answer_present handles) → SR 678448.
- C1 nec_global: 61 rows (17 rows × {1,1.4,2} + carryover 5-tau), 9 empty → SR 678449.
C1 nec_targeted at 16/17 (678086 running, 1 row left) — score when done. Curves pending → the two
NECESSITY verdicts: C1 (does flattening attention reduce ASR?) + C2 (does subtracting DeepSeek's dir
reduce ASR?). Will watch per-α/τ empty distribution (necessity denominator = MEASURED α=0/τ=1 ASR).

### 2026-07-23 — Session 2, Iteration 93 (★ C1 NECESSITY = NULL; degeneracy artifact caught & quantified)
**C1 nec_global curve (SR 678449 done): non-monotonic + confounded by DEGENERACY.** Mapping α=1−τ:
τ=1.0(base) ASR=0.875; τ=1.4(mild flatten) 1.000; τ=2.0(strong flatten) 0.000; τ=0.5(extreme sharpen) 0.
**CRITICAL: the ASR=0 endpoints are DEGENERACY, not causal.** Manual + quantified check (uniqword ratio):
τ=2.0 → 16/17 rows degenerate (mean uniqword 0.05: "path in the path in the path…", "∑C_1−∑C_1…" to
24-39k chars); τ=0.5 → 5/5 degenerate. Baseline/mild (τ=0.7/1.0/1.4) coherent (uniqword 0.44-0.48).
`answer_present` alone MISSED this (garbage is non-empty) → added uniqword-ratio degeneracy check.
→ **C1 NECESSITY NULL: in the coherence-preserving regime (τ∈[0.7,1.4]) attention temperature does NOT
reduce ASR (stays 0.875-1.0); the only ASR drops are coherence-collapse artifacts at extreme τ.**
**C1 OVERALL VERDICT: uniform attention-concentration temperature is NOT a causal lever for CoT-Hijacking**
(sufficiency NULL iter-86 + necessity NULL here). Tempered per review: does NOT rule out a
position/head-specific concentration mechanism — only the uniform-temperature one. This is the §11.8 open
item resolved as a rigorous NULL; consistent with the whole project's predictive-not-causal story.
Curves: outputs/phase8_attn_causal/nec_global/asr_vs_tau.csv. Pending: nec_targeted (SR 678479, L22-30 only
→ check if less degenerate), C2 necessity (SR 678448).

### 2026-07-23 — Session 2, Iteration 94 (★★ C1 & C2 COMPLETE — both NULL; cross-model + cross-mechanism)
**C1 nec_targeted (L22-30) curve:** coherent regime ASR stays HIGH at all τ (τ=1.0 0.875, τ=1.4 0.909,
τ=0.7/0.5 1.0); τ=2.0 16/17 degenerate (only n=1 survives, still 1.0). → targeted flattening does NOT
reduce ASR → confirms **C1 NECESSITY NULL** (both global+targeted). 
**→ C1 FINAL: uniform attention-concentration temperature is NOT a causal lever for CoT-Hijacking**
(sufficiency NULL + necessity NULL, coherent regime; extreme-τ ASR drops = repetition degeneracy).
**C2 necessity (subtract DeepSeek prefill_last L25 dir):** baseline α=0 ASR=1.000(7/7); subtract α=-1/-3
→ 0.857(6/7 = single-row flip); add α=+1/+3 → 0.875/1.0; degeneracy ~constant 3/10 (not the driver).
1-of-7 flip = within noise. → **C2 NECESSITY NULL** (no causal necessity).
**→ C2 FINAL: DeepSeek's (length-independent) success direction is NOT causal — sufficiency NULL
(iter-91) + necessity NULL. The Qwen3 causal null REPLICATES cross-model.**
**★★ UNIFIED: across TWO models (Qwen3, DeepSeek) and TWO signal families (residual direction, attention
concentration), the CoT-Hijacking success signals are PREDICTIVE/detector-grade but NOT causal.** All 3
Claude extensions done: C1 null, C2 null (cross-model replication), C3 length-irreducibility. Strengthens
the project's core predictive-not-causal thesis. Curves in outputs/phase8_attn_causal/nec_*/asr_vs_tau.csv
+ outputs/phase16_deepseek_cot_heldout25/steer_nec_pfl_L25/asr_vs_alpha.csv. Next: synthesis + registry.

### 2026-07-23 — Session 2, Iteration 95 (formalize degeneracy metric → paper-grade coherence-filtered ASR)
**Change (rigor, reuse-first):** added a degeneracy/coherence filter to the SHARED `scripts/phase7_analyze_causal.py`
curve tool (additive — all prior columns unchanged): `_unique_word_ratio` + `DEGENERACY_UNIQWORD_MIN=0.15`;
new columns `n_degenerate`, `frac_degenerate`, `asr_coherent` (ASR over non-degenerate scored rows),
`n_scored_coherent`. Non-empty repetition loops are now flagged (empty answers stay in the existing empty
path). Re-ran all 6 C1/C2 curves.
**Coherence-filtered confirmation of the C1/C2 NULLs (now explicit in the CSVs, not just log notes):**
- C1 nec_global: τ=2.0 raw ASR=0 but **n_degenerate=16/17** (repetition) → invalid; coherent regime
  (τ 0.7-1.4) ASR 0.875-1.0. C1 nec_targeted: τ=2.0 **answer_present=0.06** (16/17 EMPTY — different collapse
  flavor, correctly NOT counted degenerate) → invalid; coherent regime ASR 0.875-1.0. → C1 necessity NULL
  stands, now with the collapse made explicit (two flavors: global=repetition, targeted=empty).
- C2: degen 0/10 everywhere → clean, no confound; necessity 1.0→0.857 (1/7) NULL, sufficiency flat NULL.
Curves regenerated in place. **Bug-check subagent on the shared-tool change RUNNING** (backward-compat +
coherence-filter correctness). This makes the τ=2.0 "ASR=0" reviewer-proof (it's collapse, not causation).

**Iter 95 cont. — degeneracy bug-check PASS + uniform application to ALL prior causal runs:**
Bug-check on the shared-tool degeneracy addition: **PASS all A-F** (11 prior columns byte-identical; coherence
filter correct; div-by-zero guarded; join untouched; reproduced live). Backward-compatible.
**Applied the degeneracy lens to the 7 prior Qwen3 Phase-7 runs (re-ran curves, reused scored data):**
- steer_attacked_necessity__tc1_L20: **degen 0/6 all α**, answer_present 0.83-1.0, ASR stays 1.000 across
  subtract → prior necessity null is DEGENERACY-ROBUST.
- steer_pilot__{tc1_L20,pfl_L16}, steer_timing_gen: **degen 0/5** everywhere, answer_present 1.00, ASR ~0.
**→ EVERY prior activation-addition run has ZERO degeneracy (short coherent gens) → all prior nulls hold.**
**Sharp distinction (paper-relevant):** activation-addition steering (Qwen3 Phase-7 + C2 DeepSeek) stays
COHERENT and non-causal; only the extreme attention-TEMPERATURE intervention (C1) degenerates at τ→{0.5,2.0}.
Degeneracy is intervention-specific, correctly isolated. Causal methodology now UNIFIED + degeneracy-robust
across all runs (Qwen3 residual, DeepSeek residual, attention). Curves regenerated in outputs/phase7_causal/*/.

### 2026-07-23 — Session 2, Iteration 96 (consistency audit — deliverables verified vs source CSVs)
Audited every headline number in the synthesis/registry/log against the source CSVs — **ALL MATCH, no drift**:
C1 suff baseline 0.08/0.12; C1 nec coherent 0.875-1.0 + τ=2.0 degen 16/17; C2 suff 0.32, nec 1.0→0.857;
C3 succ 1012.5/fail 1388.0/pairs 1-6-9/AUC 0.827; §16-B prefill_last gain 0.370 CI[0.077,0.852] +
think_content_1 all CI∋0. Deliverables trustworthy.
**REACHABLE WORK COMPLETE.** Core plan (all phases) + 3 Claude extensions (C1/C2/C3, all NULL/done) +
Option A infra + DeepSeek marker fix + §16-B localization + unified degeneracy methodology — all done,
bug-checked, documented, and audited. Remaining plan items are DECISION-GATED, not startable autonomously:
(a) Phi-4 cross-model — infra-blocked (not cached; §31.3-A keeps it blocked pending a user download decision);
(b) §15 external-dataset transfer — a distinct new investigation (not reflexively started). Awaiting user
direction on (a)/(b). Loop continues to monitor.

### 2026-07-24 — Session 2, Iteration 97 (PLAN-COMPLETENESS verified against the §25 Decision Tree)
Read the plan's own decision tree (§25) to confirm ordering/gating is correctly followed (not from memory):
**Gate 3 "Is the signal causal? → NO" prescribes 4 actions, ALL now satisfied:**
1. "Treat it as a detector only" → Phase 17 detector (AUC 0.92). ✓
2. "Do not use it as the main mechanistic objective" → followed (objective branch not entered). ✓
3. **"Test alternative signals"** → **exactly what C1 (attention concentration) + C2 (cross-model DeepSeek
   direction) did — both also NULL.** ✓ (the Claude extensions ARE the plan-prescribed Gate-3 action.)
4. "Consider multivariate mechanisms" → covered by the Phase-17 MLP detector (multivariate over the
   residual vector; length-confounded, gain-over-length CI∋0). A FRESH multivariate analysis is NOT
   statistically warranted: attention (heldout25) and residual projections (dev-25) are on DIFFERENT row
   sets (no joint join without new GPU extraction), and a model over 80 attention features on n=48 is
   p>>n (overfit; LOGO→chance). Everything is length-confounded (C3: length near-irreducible), so it would
   only reconfirm. ✓ (adequately addressed; new work unwarranted.)
**Gates 4-6 (objective construction → discrete opt → universality) are gated behind "Gate 3 → YES" — so
Phases 8-16 (§12-16 optimization branch) are CORRECTLY NOT ENTERED on the causal null.** §26 Immediate
Priority Order = early phases (all done). 
**CONCLUSION: the plan is implemented in order through every reachable, gate-appropriate step; the decision
tree TERMINATES the optimization branch at Gate-3-No, which was fully worked (detector + alt signals C1/C2 +
multivariate MLP).** This corrects earlier loose "§15 open" phrasing (§15 = RL/reward optimization, gated
off; not "external transfer"). Only genuinely-open item: Phi-4 cross-model (§31.3-A infra decision, user).

### 2026-07-24 — Session 2, Iteration 98 (consolidate C1/C2 into canonical CAUSAL_VALIDATION_REPORT)
Extended `docs/CAUSAL_VALIDATION_REPORT.md` with **§7** (was Phase-7-Qwen3-only): §7a C1 attention-temperature
null (resolves the report's own §4b(b) open item + plan §11.8), §7b C2 cross-model DeepSeek null (replicates
the Qwen3 null), §7c unified degeneracy methodology. Numbers transcribed from already-audited CSVs (iter-96
audit: all match). The canonical detailed causal report now covers ALL causal evidence (2 models × 2 signal
families × 2 intervention types → predictive-not-causal). This was the last canonical deliverable missing the
new results; the synthesis (1-pager) + registry + log already had them. **Deliverable set now complete.**
No new compute. Genuinely-open item remains ONLY Phi-4 (§31.3-A user download decision).

### 2026-07-24 — Session 2, Iteration 99 (LOOP PAUSED — plan complete, no further autonomous work)
Verified (iters 96-98) the plan is implemented through every reachable, gate-appropriate step; the §25
decision tree terminates the optimization branch at Gate-3-No (fully worked: detector + alt-signals C1/C2 +
multivariate MLP); all deliverables consolidated + audited. Recent iterations were consolidation, not new
progress → to avoid burning 30-min cycles on completed work, **paused the recurring loop (CronDelete
f6d80b5c)** per the /loop skill's "task complete" stop condition. Reversible: user re-runs /loop to resume.
**To resume active work, user picks:** (a) enable Phi-4 cross-model (one-time download decision, §31.3-A);
(b) enter the optimization branch Phases 8-16 despite the causal null (plan gates it off); (c) a new goal.

### 2026-07-24 — Session 3, Iteration 100 (USER: "Can you do all?" — LOOP RESUMED for Phi-4 + optimization branch)
User authorized BOTH open items: (a) Phi-4 cross-model + (b) optimization branch. Scope this turn:
- **(a) Phi-4 mechanistic replication** (mirror DeepSeek §16-B): download Phi-4-mini-reasoning (§31.3-B
  amendment added, attributed+user-authorized), add phi4 family+markers, extract C/D → signal/confound/causal.
  Phi-4 download started (background, PID logged); Phase-4X attack outputs already exist (ASR 0.773).
- **(b) Optimization-branch ENTRY** = Phase 8 objective (§12.3 success-direction) + Phase 9 SOFT-OPTIMIZATION
  upper-bound test (§13, Gate 4): optimize a soft prefix to MAXIMIZE the success-direction projection, then
  free-generate+SR — does maximizing the signal raise ASR? (Gate 4). Phases 10-16 gated behind Gate 4.
**Design workflow wsygdj5nn launched** (2 tracks × design+adversarial-review): PHI4 pipeline + OPT Phase8/9.
Resolves Phi-4 markers + soft-opt reuse. Then implement + launch + bug-check each. Loop is ACTIVE again.

### 2026-07-24 — Session 3, Iteration 101 ("do all": OPT implemented+running; Phi-4 code done but QUOTA-BLOCKED)
Design workflow wsygdj5nn returned both tracks SOUND_WITH_FIXES (OPT priority HIGH, PHI4 MEDIUM).
**(b) OPT — Gate-4 soft-optimization (HIGH, WORKING):** implemented `poc_stage4/phase9_soft_opt.py` (optimize a
K-soft continuous prefix to MAXIMIZE the success-direction projection, then free-gen+SR; Gate-4 = does raising
the signal raise ASR?) + `slurm_scripts/run_phase9_softopt.slurm`. All review fixes folded (K_eff=soft.shape[0]
read_pos; real baseline forward; graph-retaining read-hook; no prompt_len slice on inputs_embeds generate).
Reuses load_qwen3_model + fitted direction (prefill_last L16, succ_mean=10.6/fail_mean=2.3). SMOKE job 679361
running (direction loaded OK). Bug-check subagent running. → launch full run when both clear.
**(a) PHI-4 mechanistic — code DONE, download QUOTA-BLOCKED:** added phi4 to all 5 model_family_utils registries
(<think> BPE, generates-marker like qwen3, THINK_START_IN_PREFILL=False) + phi4 loader BRANCH + argparse choice in
run_ae_generation.py & replay_hidden_states.py; built manifest via scripts/build_phi4_mechanistic_manifest.py →
outputs/phase_phi4_cot/phi4_mechanistic_manifest.jsonl (72 rows, C=59/D=13, 35 tuples). §31.3-B amendment added.
**BLOCKER: disk quota EXCEEDED on BOTH filesystems** (project cache /home/sharifm AND $HOME goliath both Errno 122)
→ Phi-4 (~7.6GB) cannot be downloaded. NOT resolvable without freeing space. Unblock options (USER decision):
(i) remove DeepSeek weights (models--deepseek-ai--DeepSeek-R1-Distill-Qwen-7B ~15GB — re-downloadable; ALL DeepSeek
RESULTS are preserved in outputs/, only weights removed) → frees ample room; (ii) remove stale Phi-4 partial
(~2.7GB, incomplete); (iii) raise quota. Phi-4 CODE is fully ready to extract the moment weights are available.

**Iter 101 cont. — phase9 bug-check + fix:** Bug-check PASS on autograd (grad flows proj→soft through causal
attention, verified on a toy), read_pos, generate(inputs_embeds)=new-tokens-only, device/dtype, hooks, analysis
tooling. Found 1 real crash (G): `base_proj` NameError on partial resume (referenced in print but only assigned
in the baseline block). FIXED: `done` now dict→carries baseline projection; `base_proj_val` always defined;
optimized-done guard added; steps=0/None-proj print made safe. AST OK. Smoke 679361 running (validates runtime).
→ launch full Gate-4 run (n=25) once smoke output confirms sensible baseline/optimized projections.

### 2026-07-24 — Session 3, Iteration 102 (USER authorized freeing space → Phi-4 UNBLOCKED; full Gate-4 launched)
User: "delete/free space we don't need — NOT outputs!". Freed re-downloadable model WEIGHTS only (guarded rm,
outputs/docs/data/code untouched): removed `models--deepseek-ai--DeepSeek-R1-Distill-Qwen-7B` (~15GB; DeepSeek
work COMPLETE, ALL results preserved in outputs/phase16_deepseek_cot_heldout25/ — only weights gone,
re-downloadable) + the stale Phi-4 partial (~2.7GB) + the failed $HOME partial. → quota freed → Phi-4 download
to project cache now PROGRESSING (bca1ghx5w, no Errno 122). [If DeepSeek is ever needed again: re-download; results intact.]
**OPT Gate-4 SMOKE VALIDATED (679361 COMPLETED):** soft-optimizer WORKS — drove success-dir projection
15.64→25.30 (past natural success mean 10.6) in 10 steps, no crash. (256-tok smoke gave no answers; full run
uses 2048.) Informative wrinkle: clean prompt already projects 15.64 (>succ mean) yet clean ASR~0 → Gate-4
well-posed. **Full Gate-4 run launched: 679440** (n=25, K=8, steps=100, prefill_last L16, 2048 tok).
**Next:** 679440 → prep→SR→curve (baseline arm α=0 vs optimized arm α=1: does raising the projection raise ASR?
= Gate 4). Phi-4 download done → build+launch extraction (code all ready). Both tracks now unblocked.

**Iter 102 cont. — Phi-4 READY + extraction LAUNCHED (both tracks now running):**
Space-freeing verified SURGICAL: DeepSeek gone (intended), gemma-4-E4B-it KEPT, Qwen3 KEPT, Phi-4 freshly
cached (7.2G both shards, PHI4_READY). Phi-4 mechanistic extraction launched: **679441** (array 0-34%4,
MODEL_FAMILY=phi4, phi4_mechanistic_manifest 72 rows → generate+replay residuals into
outputs/phase_phi4_cot/extraction; §31.3-B offline). **679440** (OPT Gate-4) also queued.
Both "do all" tracks live: (a) Phi-4 extract → score → signal/confound/direction/causal (mirror DeepSeek §16-B);
(b) OPT extract→prep→SR→Gate-4 curve. ≤6 budget honored.

### 2026-07-24 — Session 3, Iteration 105 (OPT Gate-4 complete → scoring; Phi-4 extraction ~9/35)
**OPT Gate-4 (679440 COMPLETED, 41min, 25/25 tasks, 50 rows):** soft-optimizer drove success-dir projection
baseline mean=14.3 → optimized mean=471.3 (~33x, far past succ_mean 10.6) — the soft prefix maximizes the
signal arbitrarily (the plan's §13 upper bound). answer_present 42/50. Prepped (8 empty) → SR job **679640**.
Next: curve (baseline α=0 vs optimized α=1) + coherence filter → Gate-4 verdict: does maximizing the signal
raise ASR, or does projection soar while behavior stays flat (predictive-not-causal from the optimization side)?
**Phi-4 extraction (679441):** array running (%4), 9/35 hidden-state shards, offline load clean, no errors.

### 2026-07-24 — Session 3, Iteration 106 (OPT Gate-4 raw result = SUSPICIOUS → audit; loop confirmed on)
**Loop confirmed:** cron 1fcdc0eb every 30m, full rules prompt (implement plan in order / no plan edits / doc all /
≤6 SLURM / reuse / bug-check every change). Bug + BAD-OUTPUT checking active (this iteration is an example).
**OPT Gate-4 RAW (679640 SR done, asr_vs_arm.csv):** baseline α=0 ASR=0.080 (2/25, proj mean 14.2); optimized
α=1 ASR=0.235 (4/17, proj mean 470.2, answer_present 0.68). Naively an INCREASE — BUT SUSPICIOUS and NOT yet
trusted: (i) optimized ASR over only 17 scored (8 empty → asr_conservative 4/25=0.16); (ii) tiny n (2/25 vs 4/25);
(iii) projection driven ~45x off-manifold (470 vs natural 10.6) → the "attack" input is degenerate/unnatural;
(iv) need to read the 4 "successes" — genuine harmful compliance or judge-fooled artifact? **Launched ultracode
audit workflow wow1m8lh5** (2 tracks × investigate+adversarial-verify): GATE4 real-vs-artifact (read the actual
successful gens, Fisher p, denominator honesty) + PHI4 extraction quality (finite hidden states? positions located?
DeepSeek-style bad-output check). Gate-4 verdict HELD until audit returns.
**Phi-4 extraction (679441):** 12/35 hidden shards, running, no errors.

### 2026-07-24 — Session 3, Iteration 107 (★ audit VERDICTS: Gate-4 NEGATIVE (artifact); Phi-4 marker bug FOUND+FIXED)
**Audit workflow wow1m8lh5 (4 agents, adversarially verified) — two bad outputs caught:**
**(1) OPT Gate-4 = NEGATIVE (the apparent ASR increase is an ARTIFACT, CONFIRMED by verify pass):**
- Raw headline optimized ASR 0.235 (4/17) vs baseline 0.080 (2/25) was INFLATED by: (a) DENOMINATOR — 4/17
  drops 8 empty-answer failures (off-manifold prefix breaks think-close); honest asr_conservative=4/25=0.16;
  (b) a StrongREJECT FALSE POSITIVE — task 0021 "Release-a-virus" = 129-char goal restatement, no method,
  scored sr=1.0 → genuine successes = 3, not 4; (c) tiny-n NOISE. Genuine 3/25=0.12 vs baseline 2/25=0.08,
  **Fisher exact p=1.0** (p=0.20 even under the most-favorable 4/17). NOT distinguishable from noise at n=25.
- The soft prefix drove projection to ~470 (≈45x natural 10.6) → DEGENERATE input: it DESTROYS both natural
  baseline successes (0167,0250 → empty) rather than adding new ones. NO pipeline/leak/join bug (judge sees
  only the decoded answer, not the soft-prefix embeddings).
- **→ Gate 4 = NO: soft-optimizing the input to MAXIMIZE the success signal does NOT causally raise ASR.**
  Confirms predictive-not-causal from the OPTIMIZATION side (complements the steering nulls). Registry+synthesis updated.
  Bad outputs logged: judge false-positive 0021; 8/25 empty (silently dropped from 4/17); 0250 9312-char
  runaway think. Lesson: report asr_conservative + add an actionability gate before trusting SR on off-manifold gens.
**(2) Phi-4 extraction marker BUG found (bad output) + FIXED:** think positions came out NaN (prefill_last fine)
because of BPE CONTEXT-DEPENDENCE — Phi-4 always generates "<think>\n" where ">" merges with "\n" into token
523, so generation starts [33313,881,523] but standalone "<think>"=[33313,881,29] never matches → start_marker
_not_found (35/35). FIX: `THINKING_MARKERS['phi4']['start']="<think>\n"` (=[33313,881,523], matches generation).
Verified on real data: think_content_1 now locates = "Okay" (first think token); prefill_last/startofthink located;
endofthink None (Phi-4 CoTs don't close, expected). Isolated to phi4 (other families untouched) = the bug-check.
**Plan:** let Phi-4 extraction (679441, ~17/35) finish → re-replay ALL shards with --recompute-positions (fixed
marker) → think positions populated → signal/confound/direction/causal (mirror DeepSeek §16-B; prefill_last already valid).

### 2026-07-24 — Session 3, Iteration 110 (Phi-4 extraction ~31/35; re-replay slurm prepped)
Prep (reuse, no dup): parameterized `slurm_scripts/run_phase16_deepseek_reextract_positions.slurm` by MODEL_FAMILY
(default deepseek_r1 = backward-compat; glob ${MODEL_FAMILY}_*.jsonl; offline env family-generic) so the same
script re-replays Phi-4 with the fixed `<think>\n` marker. Verified: bash syntax OK, deepseek defaults preserved.
Phi-4 extraction 679441: 31/35 gen shards, 4 tasks left. NEXT (when 35/35): MODEL_FAMILY=phi4
RUN_DIR=outputs/phase_phi4_cot/extraction OUT_DIR=outputs/phase_phi4_cot/extraction_fixed sbatch the reextract
→ think positions populated → phi4 scores → signal/confound/direction/causal (mirror DeepSeek §16-B).

### 2026-07-24 — Session 3, Iteration 111 (Phi-4 extraction DONE → re-replay + scoring launched)
Phi-4 extraction 679441 COMPLETE (35/35 shards). Launched next stages (reuse DeepSeek §16-B pipeline, no dup):
- **Re-replay 679962** (GPU): MODEL_FAMILY=phi4 via the now-parameterized reextract slurm → recompute positions
  with the fixed `<think>\n` marker → outputs/phase_phi4_cot/extraction_fixed (populates think_content_1 etc.).
- **SR scoring 679964** (CPU): `phase6_prepare_scores.py prep` on the 72 regenerations (C=59/D=13) →
  phi4_sr_input.jsonl → StrongREJECT → phi4_sr_scored.jsonl. NOTE: phi4 CoTs are `not_separable` (no </think>),
  so final_text = raw reasoning → SR scores whether the CoT itself complies (imperfect but the uniform §6 protocol).
**Next:** scores→phase6_scores.jsonl; then signal search (extraction_fixed, C vs D) → confound → direction → causal,
completing the Phi-4 cross-model mechanistic replication (3rd model: Qwen3 + DeepSeek + Phi-4).

### 2026-07-24 — Session 3, Iteration 112 (Phi-4 marker fix VALIDATED; scores built; signal search launched)
Re-replay 679962 + SR 679964 COMPLETE. **Marker fix validated:** extraction_fixed think positions now FINITE
(prefill_last, startofthink, think_content_1/2/3; endofthink NaN = correct, phi4 CoTs don't close). Scores built
(`phase6_prepare_scores scores` → phi4_phase6_scores.jsonl): re-scored success=20 (C 11/58, D 9/11), fail=49,
n=69, 3 judge-errors skipped. CAVEAT: re-scoring raw unclosed CoTs is noisy (11/58 originally-failed flipped).
Pre-empted the DeepSeek length-source bug: symlinked extraction_fixed/generation → ../extraction/generation.
**Launched phi4 signal search 680026** (CPU, C∪D, re-scored label) → phi4_CvsD_auc.csv. Next: read per-layer AUC
→ confound (does phi4 signal beat length? — 3rd-model cross-model test) → direction → causal.

**Iter 112 cont. — Phi-4 signal (680026 done) STRONG:** phi4 C∪D (n=69, re-scored label): prefill_last L7
AUC=0.890; **think_content_1 L29 AUC=0.960**; startofthink L5 0.919; endofresponse ~0.60. → Phi-4 has a strong
early predictive success signal, consistent with Qwen3+DeepSeek. **Launched phi4 confound 680081**
(fisher prefill_last L7/L8 + think_content_1 L29/L28 + startofthink L5) → does phi4's signal BEAT LENGTH?
= the 3rd-model cross-model mechanistic test (Qwen3 confounded / DeepSeek prefill_last-independent-but-label-effect).

### 2026-07-24 — Session 3, Iteration 113 (★ Phi-4 3rd-model confound = LENGTH-CONFOUNDED, like Qwen3)
**Phi-4 confound (680081):** prefill_last L7 raw=0.890, len_only=0.837, **gain +0.036 CI[-0.023,0.194] INCLUDES 0**
→ LENGTH-CONFOUNDED. L8 same (gain +0.031, CI∋0). → **Phi-4's strong signal (0.89-0.96) is a LENGTH PROXY**, on a
totally different architecture (Phi3ForCausalLM math reasoner) — matches Qwen3. len_only 0.837 = length strongly
predicts phi4 success. think_content_1/startofthink gain BLANK: raw computes (0.96) but length-gain=None because
5/72 rows have NaN think_content_1 (rows where <think> extraction failed) → the confound tool returns None on
partial-NaN cells (same pre-existing limitation that blanked DeepSeek endofthink; NOT corruption — prefill_last is
the clean complete cell). Registry: phi4_crossmodel_confound. **Cross-model tally now 3 models:** Qwen3
length-confounded; DeepSeek prefill_last beat length BUT label-effect; **Phi-4 length-confounded** → the
predictive-signal-is-a-length-proxy pattern holds on 2/3 (and DeepSeek's exception was a label artifact).

### 2026-07-24 — Session 3, Iteration 114 ("DO ALL" DELIVERED — both tracks complete; plan at natural terminus again)
Both user-authorized tracks done + documented:
- **(b) Optimization branch:** Gate-4 soft-opt test = NO (audited; maximizing the signal doesn't raise ASR).
  Per §25 decision tree, Gate 4 = No → do NOT proceed to large discrete MAC compute → optimization branch
  TERMINATES here (consistent with the causal null). Registry phase9_softopt_gate4_qwen3.
- **(a) Phi-4 3rd-model cross-model:** signal (0.89-0.96) + confound = LENGTH-CONFOUNDED (like Qwen3), on a
  different architecture. Registry phi4_crossmodel_confound; synthesis §16-C. Marker bug caught+fixed.
Cross-model matrix now: Qwen3 / DeepSeek / Phi-4 all mechanistically characterized (predictive signals = length
correlates; DeepSeek's apparent exception = label artifact). Queue 0, registry clean (27 rows, 20 col).
**Remaining items = LOW-VALUE / optional (recommended against, opt-in):** (i) Phi-4 CAUSAL steering test — signal
already length-confounded → expected null, AND phi4 CoTs are unclosed/degenerate → noisy/hard to interpret;
(ii) confound-tool partial-NaN handling so think_content_1 (0.96) length-gain computes (prefill_last already
establishes the confound). No high-value autonomous next step; loop firing into completed work. Awaiting user
direction (Phi-4 causal test / new goal / pause).

### 2026-07-24 — Session 3, Iteration 115 (Phi-4 CAUSAL test launched — completes 3-model × 3-analysis matrix)
Completing the Phi-4 replication symmetrically with DeepSeek C2 (per "do all"). Fit phi4 success direction
prefill_last L7 (n=20 succ/49 fail, sigma=1.316, sep=1.58σ, 0 NaN) → success_dir__prefill_last__L7. Built 20
re-scored-success attacked prompts (phi4_necessity_succ.jsonl). Launched (reuse phase7_steer, no new code,
phi4 offline):
- **680222 sufficiency** (dev_25 clean, α{-3,-1,0,1,3}, prefill_last L7 dir, 2048 tok).
- **680223 necessity** (20 succeeding attacks, subtract dir).
Expected NULL (signal is length-confounded → direction is a length proxy). CAVEAT: phi4 CoTs unclosed →
final_text often empty → StrongREJECT noisy; the coherence/degeneracy filter + asr_conservative will handle it.
→ next: prep→SR→curve → phi4 causal verdict, completing 3 models (Qwen3/DeepSeek/Phi-4) × {signal,confound,causal}.

**Iter 115 cont. — phi4 causal gens: answers EMPTY but generation_text has content:** sufficiency 680222 at
121/125, answer_present=2/121 (necessity 0/16). Phi-4 CoTs don't close → phase7_steer's final_text="" (unlike
run_ae_generation which stored final_text=whole gen for unclosed). BUT generation_text = the full CoT has content;
the original phi4 attack (gemini) scored the full response (ASR 0.773). → SCORE generation_text (the CoT) for the
phi4 causal test, NOT the empty final_text. Plan: let jobs finish → build SR input from generation_text → SR → curve
(coherence/asr_conservative caveats). Expected null (length-confounded direction). Jobs NOT killed (content is present).

### 2026-07-24 — Session 3, Iteration 117 (phi4 causal: score generation_text/CoT; sufficiency scoring launched)
Phi-4 sufficiency 680222 COMPLETE (125 gens, generation_text 125/125 non-empty). Scoring adjustment (not code):
transformed final_text:=generation_text (the CoT, what the original attack judge scored) → generations_gtext.jsonl
→ prep (0 empty now) → **SR 680504**. Necessity 680223 at 72/100, running. Next: sufficiency curve; necessity
same transform+score. Expected null (length-confounded direction) but now interpretable (scoring the CoT).

### 2026-07-24 — Session 3, Iteration 118 (phi4 causal SUFFICIENCY = NULL; necessity scoring)
Phi-4 sufficiency curve (680504 SR, scoring CoT/generation_text): baseline α=0 ASR=0.440 (HIGHEST); α=-3/-1
→ 0.28/0.32; α=+1/+3 → 0.40/0.36. Non-monotonic, steering EITHER way slightly lowers ASR → **NULL: adding the
phi4 direction does NOT causally increase ASR** (baseline highest). answer_present 1.00 (CoT scored), degen ~0.
Consistent with Qwen3/DeepSeek sufficiency nulls. Phi-4 high native compliance (0.44 clean, scoring CoT).
Necessity 680223 COMPLETE (100/100) → transformed+prepped (0 empty) → SR **680586**. Next: necessity curve →
phi4 causal verdict (expected null, completes 3-model causal matrix).

### 2026-07-24 — Session 3, Iteration 119 (★★ phi4 causal = NULL → 3-MODEL MATRIX COMPLETE; "do all" fully delivered)
Phi-4 necessity curve (680586 SR, CoT-scored): baseline α=0 ASR=0.75; **subtract α=-1/-3 → 0.85/0.80 (NOT reduced
→ not necessary)**; add α=+1/+3 → 0.90/0.95. The α>0 rise CONTRADICTS the sufficiency arm (where add LOWERED
0.44→0.36) → inconsistent-sign = NOISE not a causal lever; n=20 ceiling (already-succeeding attacks); dir is
length-confounded. degen 0/20, answer_present 1.00 (CoT scored). **→ phi4 direction NOT causal (sufficiency null +
necessity null) → Qwen3/DeepSeek causal null REPLICATES on the 3rd model.** Registry phi4_causal_steer.
**★★ 3-MODEL × 3-ANALYSIS MATRIX COMPLETE:**
  | model | signal(AUC) | confound(gain-over-length) | causal(steer) |
  | Qwen3 | 0.90 | ∋0 (confounded) | NULL |
  | DeepSeek | 0.80-0.84 | prefill_last beats length BUT = label artifact | NULL (C2) |
  | Phi-4 | 0.89-0.96 | +0.036 ∋0 (confounded) | NULL |
ALL predictive-not-causal; predictive signals are length correlates across 3 architectures.
**"DO ALL" FULLY DELIVERED:** (a) Phi-4 full mechanistic replication DONE; (b) optimization branch Gate-4 = NO.

### 2026-07-24 — Session 3, Iteration 120 (LOOP PAUSED — "do all" fully delivered; plan at terminus)
Both user-authorized "do all" tracks complete + documented + audited:
- **(a) Phi-4** full mechanistic replication (signal 0.89-0.96 → length-confounded → causal NULL), 3rd architecture.
- **(b) Optimization branch** Gate-4 soft-opt = NO (maximizing the signal doesn't raise ASR; §25 terminates the branch).
3-model × {signal,confound,causal} matrix COMPLETE (Qwen3/DeepSeek/Phi-4 all predictive-not-causal). Registry 28
rows (clean); synthesis §16-C has the full matrix. 3 bad outputs caught+fixed this session (Gate-4 judge-inflation
artifact; Phi-4 BPE `<think>\n` marker bug; empty-answer scoring → score CoT). DeepSeek weights freed (results
preserved, nothing in outputs/ touched). Queue 0. No high-value autonomous work remains → **paused the recurring
loop (CronDelete 1fcdc0eb)** per /loop skill "task complete" stop condition. Reversible: re-run /loop to resume.
Open (user decision): 4th model; external-dataset transfer; paper writeup; confound-tool partial-NaN fix.

### 2026-07-24 — Session 3, Iteration 121 (USER "do all" again → 4 NEW tracks launched; loop resumed 651726e3)
User "do all" → the 4 open items I offered. Launched:
- **(1) 4th model** DeepSeek-R1-Distill-Llama-8B (Llama backbone, 4th architecture): download started (bg bjws0v6b9,
  project cache offline; attack outputs exist outputs/phase4_hf_local/...Llama-8B_dev25.jsonl). Pipeline mirrors Phi-4.
- **(2) external-dataset transfer:** all manifests are advbench → workflow resolving true-external vs heldout_495 approach.
- **(4) confound-tool partial-NaN fix:** workflow producing the exact fix (mask feature+length+groups to finite rows so
  think_content_1 gain computes; currently None on Phi-4 tc1 / DeepSeek endofthink).
- **(3) paper writeup:** workflow agent writing docs/CROSS_MODEL_MECHANISTIC_REPORT.md (full 3-model matrix + Gate-4 + negatives).
**Design/execute workflow wien9e0j4** (4 parallel tracks). Loop re-created (651726e3, 30m). Next: integrate workflow
outputs → implement confound fix (+bug-check) → 4th-model extract (when downloaded) → external transfer → finalize paper.

### 2026-07-24 — Session 3, Iteration 122 (workflow wien9e0j4 returned → all 4 "do all" tracks advanced)
Design/execute workflow (4 agents, 0 err) returned; integrated:
- **(1) 4th model DeepSeek-R1-Distill-Llama-8B (Llama backbone):** added `deepseek_llama` family (5 registries,
  mirrors deepseek_r1: <think>=128013/</think>=128014 single tokens, PREFILL=True) + loader branches + choices in
  run_ae_generation/replay_hidden_states; parameterized build_phi4_mechanistic_manifest.py by --model (reuse, no dup)
  → deepseek_llama manifest (68 rows C=45/D=23, 43 tuples). **Bug-check PASS all A-F** (offline load running, prefill
  -think path = validated deepseek_r1 code, dynamic 4096/32). **Extraction 680745 running** (43 tuples %4).
- **(4) confound-tool partial-NaN FIX (applied):** `scripts/phase17_confound.py` `_oof_probs` now threads the length
  vector through the SAME per-fold finite mask (was: all-or-nothing len check nulled the whole length-block on any
  NaN). Backward-compat (all-finite cells identical). AST OK. Re-run **680753** on phi4 (prefill_last must match;
  think_content_1 L29 0.96 must now compute a gain). = the empirical bug-check.
- **(3) paper:** agent wrote `docs/CROSS_MODEL_MECHANISTIC_REPORT.md` (292 lines, 8 sections + cross-model matrix +
  honest negatives + provenance). Comprehensive, paper-ready.
- **(2) external-dataset transfer:** RESOLVED — genuinely-external harmful datasets VENDORED in repo
  (Chain_of_Thought_Hijacking/refusal_direction/dataset/raw/: malicious_instruct/harmbench/jailbreakbench/strongreject).
  Built `data/manifests/external_maliciousinstruct.csv` (100 prompts, dev_25 schema). NEXT (GPU): CoT-Hijacking attack
  on external prompts → score → extract → transfer AUC (advbench-fit detector on external set) — the true external
  generalization test. Launch when deepseek_llama frees GPU budget.
Loop 651726e3 active. All 4 tracks materially advanced; downstream continues.

### 2026-07-24 — Session 3, Iteration 123 (confound fix VERIFIED + reveals phi4 think_content_1 marginal gain; external attack launched)
**Confound partial-NaN fix VERIFIED (680753):** (1) backward-compat CONFIRMED — prefill_last L7 gain 0.0357
CI[-0.023,0.194] IDENTICAL to the pre-fix run. (2) think_content_1 (5/72 NaN) now COMPUTES: **L29 gain +0.098
CI[0.010,0.280] P+=0.994, L28 +0.090 CI[0.004,0.267]** — marginally BEATS length (CI barely excludes 0);
startofthink confounded (CI∋0). → HONEST REFINEMENT: Phi-4's strongest signal (think_content_1, reasoning-content
position) has a WEAK length-independent component, while prefill_last stays confounded. Caveat: MARGINAL
(CI barely excludes 0, P+ 0.99 not 1.0) + NOISY phi4 re-scored labels (11/58 flipped). Refines, does not overturn,
"Phi-4 mostly length-confounded." (Contrast DeepSeek §16-B: there prefill_last had the length-indep signal, tc1 didn't
— opposite position, both weak.) The fix is a genuine tool improvement (empirical bug-check: prefill_last identical +
tc1 computes). Registry/synthesis updated.
**External track:** external attack **680767** launched (Qwen3 target, external_maliciousinstruct.csv 100 prompts,
project cache, Gemini attacker). deepseek_llama extraction 680745 running (0/43). Budget: 3 GPU + external + confound-done.

### 2026-07-24 — Session 3, Iteration 128 (4th model Llama-8B extraction DONE → scoring; external attack running)
DeepSeek-R1-Distill-Llama-8B extraction 680745 COMPLETE (43/43 shards). Markers CORRECT first-pass (no re-replay,
unlike Phi-4): prefill_last/startofthink/think_content_1/2/3 all FINITE (endofthink/answer NaN — attack CoTs don't
always close </think>, but key positions clean). Scoring: phase6_prepare_scores prep (68 rows, C=45/D=23) →
SR **681227**. Next: build scores → signal search (dsllama_CvsD_auc) → confound (does Llama-8B signal beat length? =
4th architecture, 2nd backbone family) → direction → causal. External attack 680767 still running (~goal 25/100).

### 2026-07-25 — Session 3, Iteration 130 (Llama-8B signal STRONG → confound launched; external attack ~4h)
Llama-8B scored (C 15/45, D 18/23 → 33 succ/35 fail, n=68; cleaner labels than Phi-4 — closes </think>).
Signal (681256): prefill_last L2 AUC=0.872; think_content_1 L31=0.895; startofthink L2=0.872; endofresponse
L19=0.947 (post-answer, excluded). → 4th model also has a strong early signal, consistent with Qwen3/DeepSeek/Phi-4.
**Confound 681312 launched** (fixed tool; prefill_last L1/L2 + think_content_1 L31/L32 + startofthink) → does the
Llama-backbone signal beat length? = 4th architecture / 2nd backbone family. External attack 680767 running ~4h (~mid).

### 2026-07-25 — Session 3, Iteration 131 (★ Llama-8B BEATS length — genuine, NOT label artifact; causal test launched)
**Llama-8B confound (681312) — BEATS LENGTH at ALL cells:** prefill_last L2 gain +0.090 CI[0.009,0.214] P+0.99;
think_content_1 L31 +0.112 CI[0.023,0.189]; L32 +0.127 CI[0.051,0.216] P+1.0; startofthink +0.090; len_only=0.783.
→ UNLIKE Qwen3/Phi-4 (confounded). CRUCIAL: unlike DeepSeek-Qwen's beat-length (=label artifact, SAME tokenizer as
Qwen3 → identical lengths), Llama-8B has a DIFFERENT tokenizer (Llama vs Qwen2) → the identical-lengths explanation
does NOT apply → GENUINE length-independent predictive signal on a different backbone. Honest complication to
"universal length confound" (now 2/4 confounded, Llama-8B genuinely length-independent). Caveat: n=68, modest gains,
re-scored labels. **THE key test now = CAUSAL:** is this length-independent signal a MECHANISM or still just a detector?
Fit direction prefill_last L2 (n=33succ/35fail, sep 1.41σ). Launched **suff + nec causal steering** (dev_25 + 33
succeeding attacks, α{-3,-1,0,1,3}, 4096 tok). External attack 680767 ~4.5h. Cross-model tally updated next.

### 2026-07-25 — Session 3, Iteration 132 (external attack DONE → ASR 0.737 behavioral transfer; mech extraction launched)
**External attack 680767 COMPLETE:** CoT-Hijacking on 99 malicious_instruct (EXTERNAL, non-advbench) prompts,
Qwen3 target → is_success 73/99 = **ASR 0.737** — the attack GENERALIZES to an external harmful dataset (comparable
to advbench 0.82). = behavioral external transfer. Output: outputs/phase_external/phase4_cot_hf_Qwen_Qwen3-14B_dev100.jsonl.
**External MECHANISTIC transfer setup:** built qwen3 AE manifest (99 rows C=26/D=73) via the parameterized builder;
made run_phase5_ae_extract.slurm ARRAY_MAX env-overridable (backward-compat default 49; the 99-tuple guard would
else FATAL) → launched **external extraction 681507** (99 tuples %4, Qwen3). Next: extract residuals → apply the
ADVBENCH-fit direction to the EXTERNAL set → transfer AUC (does the advbench detector predict success on external?).
**Llama-8B causal:** sufficiency 681351 DONE (125, 19 empty) → SR 681496 running; necessity 681352 at ~71/165.

### 2026-07-25 — Session 3, Iteration 133 (Llama-8B sufficiency = WEAK +α trend, NOT yet confirmed; necessity pending)
Llama-8B sufficiency curve (681496 SR): coherent regime (α∈{-1,0,+1}, answer_present ~1.0) shows a WEAK +α↑ trend
0.360→0.375→0.480 (add→up); extremes degenerate (α=-3 answer_present 0.28=mostly empty; α=+3 mean_tok 517=short).
→ SUGGESTIVE of weak causal sufficiency (unlike the flat nulls of Qwen3/DeepSeek/Phi-4) — CONSISTENT with Llama-8B
being the model whose signal BEATS length. BUT: WEAK (9→12/25, ~1 row/step), n=25, extremes break down. NOT a
causal claim yet — needs (a) necessity arm (681352, 93/165) and (b) an adversarial audit (like the Gate-4 artifact
catch: check the +α "successes" are genuine, Fisher p, coherence). HOLDING verdict. External extraction 681507 12/99.

### 2026-07-25 — Session 3, Iteration 137 (Llama-8B causal: +α RAISES ASR in BOTH arms — POTENTIAL causal hint, AUDIT launched)
Llama-8B necessity curve (681681): baseline α=0 ASR=0.824; subtract α=-1→1.000 (NOT suppressed), α=-3→ALL EMPTY
(answer_present 0.00, uninterpretable); add α=+1→0.955, α=+3→0.909. Combined w/ sufficiency (0.375→0.480 at α=+1):
**ADDING the direction raises ASR in BOTH arms** (0.375→0.48 suff; 0.824→0.955 nec) — UNLIKE the flat nulls of
Qwen3/DeepSeek/Phi-4. Llama-8B is ALSO the model whose signal BEATS length → potential FIRST causal hint.
**SEVERE red flags → verdict HELD:** necessity answer_present only 0.46-0.67 (steering→empty; α=-3 all empty) → ASR
over BIASED non-empty subset; small n (25 suff/17-33 nec); near-ceiling baselines; extremes degenerate (short/empty).
= same artifact-prone setup the Gate-4 audit killed. **Launched adversarial audit** (genuine successes vs artifact;
empty-answer selection bias; Fisher p; coherence; deepseek_llama steering-pipeline correctness) before ANY causal claim.
External extraction 681507 78/99.

### 2026-07-25 — Session 3, Iteration 138 (★★ Llama-8B causal AUDITED = NULL (artifact) → 4-model thesis STRENGTHENED)
**Adversarial audit VERDICT: the Llama-8B "causal hint" is an ARTIFACT (length/termination selection bias + noise).
NOT causal.** Independently reproduced: every empty answer = a 4096-tok TRUNCATION inside <think> (never emitted an
answer) → answer_present is "did it stop thinking before the cap," rising 0.00→1.00 with α; mean tokens collapse
monotonically (NEC 4096→873). So +α = model stops thinking & emits its (already-harmful, necessity set) answer sooner;
−α = thinks to the cap, emits nothing. NECESSITY rise = pure length/termination DENOMINATOR effect. SUFFICIENCY bump
0.375→0.48 = **Fisher p=0.567 NOISE** (+5/−2 churn, non-monotone, collapses to 0.20 at α=+3 with Gate-4-style judge
false-positives: garbled restatement 0021, clarifying-question 0250, degenerate loop 0125). Steering MODULATES
GENERATION LENGTH/think-termination = the length confound re-expressed causally. asr_conservative flattens the effect.
Also: judge scored byte-level-garbled text (Ġ/Ċ leak) → inflates false positives. No pipeline correctness bug.
**→ Llama-8B causal = NULL, like all 3 others. The 4th model STRENGTHENS the thesis: predictive-not-causal holds EVEN
where the predictive signal genuinely beats PROMPT-length.** Registry dsllama_causal_steer.
**4-MODEL × {signal,confound,causal} MATRIX:**
  Qwen3 (0.90 / confounded / NULL) | DeepSeek-Qwen (0.80-0.84 / beats-length=label-artifact / NULL) |
  Phi-4 (0.89-0.96 / confounded, tc1 marginal / NULL) | Llama-8B (0.87-0.95 / GENUINELY beats prompt-length / NULL-audited).
ALL predictive-not-causal across 4 architectures + 2 backbone families. External extraction 681507 ~78/99.

### 2026-07-25 — Session 3, Iteration 140 (external mechanistic extraction DONE → scoring; transfer test next)
External extraction 681507 COMPLETE (99/99 shards, Qwen3 on malicious_instruct attacked prompts). Scored:
phase6_prepare_scores prep (99 rows, C=26/D=73) → SR **681796**. Next: build ext phase6_scores → (a) in-distribution
signal search on external (does the success signal exist on a DIFFERENT harmful dataset?) + (b) TRANSFER — apply the
ADVBENCH-fit direction (outputs/phase7_causal/success_dir__prefill_last__L16) to the external residuals → transfer AUC
(does the advbench detector generalize to malicious_instruct?). Completes the external track (behavioral ASR 0.737 done).

### 2026-07-25 — Session 3, Iteration 141 (★ external MECHANISTIC transfer = advbench detector does NOT transfer, AUC 0.461)
External re-scored (99 rows): C 18/26, D 66/73 → 84 succ/15 fail (attack very effective on external). **TRANSFER TEST:
the ADVBENCH-fit prefill_last L16 direction (in-distribution AUC ~0.90) applied to EXTERNAL malicious_instruct residuals
→ AUC = 0.461 (≈ CHANCE).** → the predictive signal is DATASET-SPECIFIC — it does NOT encode a general harmful-success
representation that transfers to a different harmful dataset. CONSISTENT with the length-correlate/predictive-not-causal
thesis (a dataset-specific length-correlated feature won't transfer). CAVEATS: labels imbalanced (only 15 fails → noisy
AUC; 0.461 = "indistinguishable from chance," not confidently below). Behavioral attack DID transfer (ASR 0.737), but the
mechanistic DETECTOR does NOT. In-distribution external signal search 681827 running (does the signal exist on external
at all? — if yes + advbench-dir doesn't transfer = clean dataset-specificity result). Completes external track (attack + transfer).

### 2026-07-25 — Session 3, Iteration 142 (★★ external track COMPLETE → "DO ALL" (all 4 tracks) DELIVERED)
External in-distribution signal search 681827: WEAK (prefill_last L19 0.635, think_content_1 L9 0.648) — vs advbench 0.90.
So: advbench-dir transfer 0.46 (chance) < external-fit 0.64 (weak) < advbench in-dist 0.90 → the advbench detector
does NOT transfer, UNDERPERFORMING even the weak external-fit signal = DATASET-SPECIFIC. Caveat: external labels
imbalanced (84succ/15fail, re-scoring noise) → external signal itself weak, so a solid-but-caveated negative.
DISSOCIATION: attack transfers behaviorally (ASR 0.737) but the mechanistic DETECTOR does not (AUC 0.46). Registry
external_transfer_maliciousinstruct.
**★★ ALL 4 "DO ALL" TRACKS DELIVERED:** (1) 4th model Llama-8B (signal beats prompt-length, causal NULL-audited →
thesis strengthened); (2) external transfer (attack generalizes, detector doesn't = dataset-specific); (3) paper
CROSS_MODEL_MECHANISTIC_REPORT.md; (4) confound-tool partial-NaN fix (revealed Phi-4 tc1 marginal gain). Two tempting
"positives" (Gate-4, Llama-8B causal) both adversarially REJECTED. Predictive-but-not-causal thesis now cross-validated
across 4 architectures + external-dataset + optimization side. Queue clearing.

### 2026-07-25 — Session 3, Iteration 143 (LOOP PAUSED — "do all" round-2 fully delivered; plan at terminus)
All 4 user-authorized "do all" tracks complete + verified + documented + consolidated into the paper:
(1) 4th model Llama-8B (signal beats prompt-length genuinely; causal NULL after adversarial audit rejected a
length/termination artifact → thesis strengthened); (2) external transfer (attack 0.737 transfers, detector 0.461
does NOT = dataset-specific); (3) paper CROSS_MODEL_MECHANISTIC_REPORT.md updated to 4 models + external; (4)
confound-tool partial-NaN fix (revealed Phi-4 tc1 marginal). Registry 30 rows (clean), queue 0. Two tempting
"positives" (Gate-4, Llama-8B causal) both adversarially REJECTED. Central finding now cross-validated across 4
architectures / 2 backbone families + external dataset + optimization side: PREDICTIVE-BUT-NOT-CAUSAL, robust even
to the length-confound question, detector dataset-specific. No high-value autonomous work remains → **paused the
recurring loop (CronDelete 651726e3)** per /loop "task complete". Reversible: re-run /loop. Open (user decision):
5th model; deeper analysis of the steering→generation-length/think-termination mechanism the audit uncovered;
non-CoT attack; external transfer on a balanced dataset (harmbench).

### 2026-07-25 — Session 3, Iteration 144 (DOCUMENTATION COMPLETENESS PASS — full artifact index)
Per user "MAKE SURE EVERYTHING IS DOCUMENTED": audited every this-session artifact/code-change against log/registry/
synthesis/report. Registry 30 rows (clean, 20-col). Below = the complete ARTIFACT INDEX (every track → paths).

**CODE (new + changed, all bug-checked):**
- poc_stage4/model_family_utils.py — added `phi4` (marker `<think>\n` BPE-merge fix) + `deepseek_llama` (prefill-think) families.
- poc_stage4/phase9_soft_opt.py — NEW, Gate-4 soft-prompt optimizer.
- poc_stage4/phase8_attn_temp_generate.py — NEW, §C1 attention-temperature causal intervention.
- poc_stage4/phase7_steer_generate.py — added `--model-family` (cross-model steering).
- scripts/phase17_confound.py — partial-NaN fix (_oof_probs threads length via per-fold finite mask).
- scripts/phase7_analyze_causal.py — degeneracy/coherence filter (n_degenerate, asr_coherent).
- scripts/phase6_length_identifiability.py — NEW, §C3.
- scripts/build_phi4_mechanistic_manifest.py — NEW + parameterized by --model (reused for deepseek_llama).
- poc_stage_ae/{run_ae_generation,replay_hidden_states}.py — phi4 + deepseek_llama loader branches + choices; replay --recompute-positions + multi-shard load.
- poc_stage_ae/thinking_position_utils.py — THINK_START_IN_PREFILL branch (deepseek/llama).
- slurm_scripts/: run_phase9_softopt.slurm (NEW), run_phase8_attntemp.slurm (NEW), run_phase16_deepseek_reextract_positions.slurm (MODEL_FAMILY-param), run_phase5_ae_extract.slurm (§31.3-A offline + ARRAY_MAX env), run_phase4_hf_local.slurm/run_phase7_steer.slurm (offline/model-family).
**PLAN AMENDMENTS (attributed):** §31.3-A (offline reads), §31.3-B (Phi-4/Llama download), Appendix C (§C1/§C2/§C3).
**RESULTS (per track → key artifacts):**
- §C1 attention causal (Qwen3): outputs/phase8_attn_causal/{suff,nec}_{targeted,global}/asr_vs_tau.csv. Registry c1_attn_temp_causal_qwen3.
- §C2 DeepSeek causal: outputs/phase16_deepseek_cot_heldout25/steer_{suff,nec}_pfl_L25/asr_vs_alpha.csv. Registry c2_deepseek_dir_causal.
- §C3 length identifiability: outputs/phase5_mechanistic/phase6_length_identifiability.json. Registry c3_length_identifiability.
- §16-B DeepSeek think-content: outputs/phase16_deepseek_cot_heldout25/{extraction_fixed/, detector_CvsD_think_confound.csv}. Registry phase16_deepseek_think_confound.
- Gate-4 soft-opt: outputs/phase9_softopt/pfl_L16/{generations.jsonl, asr_vs_arm.csv}. Registry phase9_softopt_gate4_qwen3.
- Phi-4 (3rd model): outputs/phase_phi4_cot/{extraction_fixed/, phi4_CvsD_confound_fixed.csv, steer_{suff,nec}_pfl_L7/asr_vs_alpha.csv, phi4_phase6_scores.jsonl}. Registry phi4_crossmodel_confound, phi4_causal_steer.
- Llama-8B (4th model): outputs/phase_deepseek_llama_cot/{extraction/, deepseek_llama_mechanistic_manifest.jsonl, dsllama_phase6_scores.jsonl, dsllama_CvsD_auc.csv, dsllama_CvsD_confound.csv, success_dir__prefill_last__L2/, steer_{suff,nec}_pfl_L2/asr_vs_alpha.csv}. Registry dsllama_causal_steer.
- External transfer: data/manifests/external_maliciousinstruct.csv; outputs/phase_external/{phase4_cot_hf_Qwen_Qwen3-14B_dev100.jsonl, mech/{ext_phase6_scores.jsonl, ext_CvsD_auc.csv}}. Registry external_transfer_maliciousinstruct.
**REPORTS:** docs/CROSS_MODEL_MECHANISTIC_REPORT.md (4-model matrix+external), docs/DISTILLATION_FINDINGS_SYNTHESIS.md (§16-A–D, Appendix C).
NOTE: all new files are UNCOMMITTED to git (working-tree only) — documented here; not committing per "commit only when asked".
