# GCG Fixed-Optimizer Re-run Campaign — Running Ledger

**Purpose:** append-only record of *every* action in the v2 (placement-bug-fixed) re-run, so the state is always recoverable. Companion to `docs/GCG_BUGFIX_RERUN_PLAN.md` (plan) and `docs/GCG_JULY2026_MASTER_LOG.md` §13 (synthesis + v1-vs-v2 table). Driven by a 30-min loop (cron `35b00f3a`).

## Ground rules (enforced every tick)
- ≤6 jobs running, **0 PENDING** (scancel any pending tail); `--constraint=l40s`; **exclude n-804, n-602, n-301**.
- Non-destructive: v2 → `outputs/stage_gcg_full_v2_userfix/<run>/`; v1 never touched. Separate `GCG_PHASE4_7_SOURCE_OF_TRUTH_v2.csv`.
- Every opt run must record `gcg.suffix_placement=="user"` in CONFIG.json (guardrail-checked before trusting output).
- **v1 9a/9b/9c unseeded evals: do NOT restart when they finish** — reuse the freed slots for the next-priority v2 rerun (per user 2026-07-19).

## Method confirmation (the "does the article tune on the user part?" question)
**Yes.** Original GCG (`llm-attacks/llm_attacks/base/attack_manager.py:132-133` + `minimal_gcg/string_utils.py`): `SuffixManager.get_prompt` appends the control to `roles[0]` = **user** turn (`f"{goal} {control}"`), target to `roles[1]` = assistant, loss = target−1. Our fix reproduces this: suffix optimized in the **user turn** with a ` !` space-prefixed init (in-context tokens identical to the reference control `[" !"]×N`). The pre-fix bug optimized in the assistant turn. Verified byte-identical to eval on Qwen3 + Gemma4.

## Priority ("best do our research") order
1. **Gate 5A** (does the fix move ASR vs v1 10.7%?) — decision-critical.
2. Headlines + logical blockers (no reference cache, `lambda_repr=0`): Phase-8 λ0.3 (→9A), 7B-s45 (→9B), 7B-s43, 7B-s44, Phase-8-s43, 9C-s45-opt.
3. 520-scale + ensemble EVALS once their source opt is done: 7A(seeded+unseeded), 9A, 9B, 9C, 10F union.
4. Gemma4 track: 9g_emptythink_L31 (→10A, →10G transfer).
5. Reference-cache-dependent (`lambda_repr=1.0`): Standard GCG, Gemma4-4C, 5B (need v2 ref cache built first).
6. Negatives / ablations / dead-ends last (5C, multimodel, 10D/10E, 4A/4B, DeepSeek, early repr).

## Job ledger (append-only; times local)

| Date/time | Job | Run | Type | Status | Notes |
|---|---|---|---|---|---|
| 07-19 ~12:00 | 667366 | 5A cot_target | opt | CANCELLED | ran before space-init refinement; superseded |
| 07-19 ~12:20 | 667391 | 5A cot_target | opt (gate) | **DONE ~16:41** | audit PASS, placement=user; FINAL_CANDIDATES written |
| 07-19 ~12:46 | 667427 | Phase-8 λ0.3 (8_rd_lambda03) | opt | **DONE ~16:5x** | placement=user, lam_rd=0.3/L25; FINAL_CANDIDATES written |
| 07-19 ~12:46 | 667428 | 7B seed-45 | opt | **DONE ~17:00** | placement=user; FINAL_CANDIDATES → source for 9B |
| 07-19 ~17:05 | 667603 | 7A seeded 520 | free-gen eval | RUNNING | 5A v2 suffix on 520 beh, seeds 42/43/44 → v2 vs **v1 8.01%** (520-eval ~ many hrs, judge-bound) |
| 07-19 ~16:46 | 667598 | 5A cot_target | free-gen eval | RUNNING | 25-beh, seeds 42/43/44 → **gate ASR vs v1 10.7%** |
| 07-19 ~16:46 | 667599 | 7B seed-43 | opt | RUNNING | placement=user |
| 07-19 ~16:58 | 667601 | Phase-8 λ0.3 | free-gen eval | RUNNING | 25-beh → Phase-8 v2 ASR (headline) |
| (pre-session) | 667211/667277/667424 | v1 9b/9a/9c unseeded | v1 eval | 667211 done; **667277/667424 CANCELLED 17:07 (per user)** | v1 not restarted; slots reused for v2 |
| 07-19 ~17:07 | 667604 | 9C seed45 λ0.3 | opt | RUNNING | qwen3, λrd0.3/L25; blocks 9C-520 |
| 07-19 ~17:07 | 667605 | Gemma4 emptythink@L31 | opt | RUNNING | gemma4, λrd0.3/L31; blocks 10A+10G; starts Gemma4 track |

## Results (v2) — filled as evals finish
| Experiment | v1 ASR | v2 ASR (user-turn fix) | Δ | source |
|---|---|---|---|---|
| 5A CoT-target (25 beh) | 10.7% | *pending 667598* | — | — |
| Phase-8 λ0.3 (25 beh) | 24.0% | *pending 667601* | — | — |

## Runbook (from subagents, 2026-07-19 ~17:00)

**Eval-only reruns** (consume a v2 opt's FINAL_CANDIDATES; `cp FINAL_CANDIDATES.jsonl + CONFIG.json` into the eval dir first — the generic free-gen launcher does NOT auto-copy). Manifests unchanged from v1. Base `V2=outputs/stage_gcg_full_v2_userfix`, manifests in `outputs/stage_gcg_full/`:

| Eval run | source v2 opt | manifest | seeds | notes |
|---|---|---|---|---|
| 7A seeded ✅submitted 667603 | cot_target ✅ | advbench_cot_full520_manifest.jsonl | 42,43,44 | flagship (v1 8.01%) |
| 7A unseeded | cot_target ✅ | advbench_cot_full520_manifest.jsonl | 100,200,300 | v1 8.92% |
| 9A (+unseeded) | **reuse 8_rd_lambda03 ✅** (identical config) | advbench_cot_full520_manifest.jsonl | 42,43,44 / 100,200,300 | v1 11.21% |
| 9B (+unseeded) | 7b_seed45 ✅ | advbench_full520_manifest.jsonl (NON-cot) | 42,43,44 / 100,200,300 | v1 8.83% |
| 9C (+unseeded) | 9c_lambda03_seed45 opt (⚠ needs v2 opt: seed45+λrd0.3) | advbench_cot_full520_manifest.jsonl | 42,43,44 / 100,200,300 | |
| 10A | gemma4_9g_emptythink_L31 opt (⚠ needs v2 opt) | advbench_gemma4_emptythink_full520_manifest.jsonl | 42,43,44 | v1 3.91% |
| 10G transfer | gemma4_9g_emptythink_L31 opt (⚠) | advbench_cot_target_manifest.jsonl | 42,43,44 | CONFIG must be **qwen3** (cross-arch) |
| 4F | qwen3_weighted opt (⚠ needs ref cache) | advbench_full520_manifest.jsonl | 42,43,44 | |
| 4E transfer | qwen3_weighted opt (⚠) | copied MANIFEST | 42 | use `run_gcg_cross_model_transfer.slurm` |

**Reference-cache-dependent opts** (λ_repr>0 → need v2 cache built first; **generic launcher gap**: it passes `--lambda-repr` but NOT `--reference-cache-dir/--repr-layers/--repr-at-cot-pos`, so a dedicated launcher or script extension is required before these run): `qwen3_weighted` (Standard GCG, →4F/4E), `gemma4_weighted` (4C), `5b_cot_repr` (repr_at_cot_pos). Build cmds in subagent report; `build_reference_cache.py` already defaults to user-turn placement so a fresh v2 cache dir is correct.

**Verified clean (placement=user, params match v1, FINAL_CANDIDATES present):** cot_target(5A), 8_rd_lambda03(Phase8). 7b_seed45 done; 7b_seed43 running.

**Scope (opt-runbook subagent):** 44 canonical OPT runs; **23 are eval-only replays** (reuse a suffix optimized elsewhere — do NOT re-optimize: all 7A dirs=5A; 9a_full520=8_rd_lambda03; 9b_full520=7b_seed45; 9c_full520=9c_seed45; cot_disabled+full520_eval=qwen3_weighted; gemma4_10a+10g=gemma4_9g_emptythink_L31). So most 520/ensemble numbers come from re-EVALS of a few suffixes.

**OPT submission order (no-cache, submit ≤6 as slots free via generic script; env = RUN_DIR=$V2/<run>, MANIFEST_PATH=$M/<manifest>, MODEL_*, SEED, +REFUSAL_DIR_* when λrd>0):**
- Done/running: cot_target✓, 8_rd_lambda03✓, 7b_seed45✓, 7b_seed43(run)
- **T1:** 9c_lambda03_seed45 (seed45+λrd0.3/L25, cot_target — Sprint3 champion, blocks 9C), 7b_seed44 (seed44 — completes 43/44/45 union ensemble), lambda0 (seed42, manifest_v1, no-rd baseline)
- **T2 Gemma4:** gemma4_9g_emptythink_L31 (λrd0.3/L31/g_L31, gemma4_cot_v2_anchor_empty_think — blocks 10A+10G), gemma4_9d2_lambda03_L31, gemma4_6b2_cot_target_v2 (800 steps), gemma4_6b_cot_target, gemma4_9d_lambda03_cot, gemma4_10b_emptythink_seed{43,44,45}, gemma4_9g_tok1/tok5_L31
- **T3 DeepSeek:** deepseek_r1_7b_cot_target, deepseek_r1_7b_weighted (model=deepseek-ai/DeepSeek-R1-Distill-Qwen-7B)
- **T4-T7:** 10c_seed{0,1,2}, qwen3 9g anchors (emptythink/tok1/tok5/nocot), 8_rd sweep (seed43/bs128/λ3/6a/6c), gemma4_6a, 7c_nothink(think=false), track4_suflen35
- Refusal .pt paths: q_L25=$M/refusal_direction_qwen3_L25.pt, g_L31=$M/refusal_direction_gemma4_L31.pt, g_L25=$M/refusal_direction_gemma4_L25.pt

**⚠ NEED USER CONFIRM before submitting:** `8_rd_layer20` & `8_rd_layer30` set refusal_dir_layer=20/30 but their v1 refusal_dir_path points at the **L25** .pt (mismatched in original CONFIG). Reproduce as-is, or fix to L20/L30 file? (deferred)

**⚠ Generic launcher can't yet do these 8 (need script extension to forward flags run_optimization already supports):** qwen3_weighted + gemma4_weighted + multimodel (need `--reference-cache-dir`; +`--multi-model-family` for multimodel), 5b_cot_repr (`--reference-cache-dir` + `--repr-at-cot-pos`), 5c_quick_asr + track4b_quickasr (`--quick-asr-every 50`), 10d_multilayer_rd (`--refusal-dir-layers/paths/lambda-per-layer`), 10e_lambda_anneal (`--lambda-refusal-dir-schedule`). TODO: extend run_gcg_full_opt_userfix_generic.slurm.

## Action log (chronological narrative)
- **07-19 (this session):** implemented fix (suffix_placement flag, user-turn path, ` !` space-init), verified byte-exact on both tokenizers + regression test; cross-checked vs llm-attacks reference; built generic launcher `run_gcg_full_opt_userfix_generic.slurm` + gate script. Submitted gate (667391) → done. Per user (don't idle for gate), filled slots in priority order: Phase-8 λ0.3 (667427, done), 7B-s45 (667428), 7B-s43 (667599). Gate opt done → submitted gate eval (667598). Phase-8 opt done → submitted Phase-8 eval (667601). Two subagents dispatched to build the complete opt/eval/ref-cache runbook (results appended next).
