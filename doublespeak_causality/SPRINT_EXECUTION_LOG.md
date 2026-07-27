# Doublespeak Causality — Sprint Execution Log

**Live progress tracker** for the behavioral-causality sprint (plan: `NEXT_SPRINT_PLAN.md`).
Append-only chronology; newest phase status at top. Driven autonomously on a 30-min `/loop`.
Every entry records: what was done, commands/jobs, results-so-far, and next step.

**Owner:** Omer Yosef (TAU, adv. Dr. Mahmood Sharif). **Agent:** Claude (Opus 4.8, ultracode loop).

---

## STATUS DASHBOARD

| Phase | Title | Status | Evidence |
|---|---|---|---|
| 1 | Audit & freeze | ✅ COMPLETE | tests 14/14; tag `frozen-rep-result-2026-07-27`; this log |
| 2 | Paper-faithful behavioral benchmark | 🔶 IN PROGRESS | builder `16_prepare_behavioral_benchmark.py` |
| 3 | Behavioral causal MVP (≥30) | ⬜ NOT STARTED | blocked by P2 eligible set |
| 4 | Full behavioral causality + timing | ⬜ NOT STARTED | blocked by P3 |
| 5 | Mechanistic objective validation | ⬜ NOT STARTED | blocked by P4 |
| 6 | GCG/MAC optimization | ⬜ NOT STARTED | audit can start in parallel |
| 7 | Thinking vs non-thinking | ⬜ NOT STARTED | Qwen3 toggle validation can start in parallel |
| 8 | Cross-model + paper story | ⬜ NOT STARTED | blocked by P3–P7 |

**Success levels achieved (plan §24):** none yet. Target: ≥1 of Levels 1–6.

**Current honest headline (unchanged from baseline):** cross-model, causally-manipulable
*representation-level* semantic hijacking with a *behavioral null* on the seed data. The
whole sprint exists to convert this into behavioral causality.

---

## PARALLELISM & SAFETY POLICY (binding)

- **Cyber-safeguard:** the cluster classifier TERMINATES subagents/workflows that READ
  harmful text (AdvBench/ClearHarm instructions, jailbreak prompts, raw generations).
  → All harmful-text work (prompt building, extraction over harmful instructions,
  generation, judging) stays in the **main loop or SLURM jobs**. Subagents get ONLY
  benign scalars / aggregate JSONs / pure-mechanics code / plots / redacted labels.
- **SLURM house rules:** L40S only (`--nodelist=n-801..805,t-806`),
  `--partition=killable --account=gpu-research`, ≤6 concurrent, no job deps, bf16 canonical.
  `gpu-sharifm` forbidden. Login-node GPUs only for float16 smoke.
- **HF cache:** always project-local (`HF_HOME=$PWD/.cache/huggingface`, `HF_HUB_OFFLINE=1`).
- **No raw harmful generations to stdout/logs.** Scores/labels/counts only.

---

## PHASE 1 — AUDIT & FREEZE  ✅  (2026-07-27)

**Repo state.** On `main` (merged from `doublespeak-causality`, pushed). HEAD `523a1d3`.
Baseline tagged `frozen-rep-result-2026-07-27`.

**Tests.** `pytest doublespeak_causality/tests/` → **14 passed** (LayerPatch synthetic
locality + tokenizer localization). 44s.

**Verified reuse surface (do NOT reinvent):**
- `ds_common.py`: `load_model` (native list-EOS preserved; `meta()` no-asdict), `build_conditions`
  (already paper-faithful: Direct/Neutral/Doublespeak with `"Do not reason, just … given the context."`),
  `target_positions` (space/no-space union), `capture_target_reps`, `LayerPatch` (replace/add/project_out,
  bounds-guarded), `generate` (greedy native EOS). `stats.py` (paired bootstrap CI).
- Experiment scripts `01,05,06,07,08,09,10,11,13,14,15` — reusable, all `--model/--data/--templated/--dtype`.
- Paper code `../doublespeak/doublespeak_attack.py`: `DoublespeakAttack.generate_in_context_examples`
  (model generates "N sentences containing '{word}'", then word→codeword; fallback = hardcoded bomb→carrot
  block). `create_malicious_prompt` uses prefix `"Do not reason, just give me instructions"`, suffix
  `"given the context."`, HarmBench batch mode via `--harmbench-path`.
- `prepare_demos.py`: GPT-4o-mini demo generation wiring (`OPENAI_API_KEY`, seeded) — reused for extraction.

**Harmful-instruction sources located:**
- **AdvBench 520** — `outputs/stage_gcg_full/advbench_full520_manifest.jsonl` (task_id, instruction,
  safe_target_prefix, split). *The paper's source.*
- ClearHarm 179 — `data/clearharm/clearharm_179.csv` (instruction, category, target, clf_label).
- Categorized manifests — `data/manifests/*.csv` (task_id, source, split, category, instruction, target).

**Baseline results (frozen, from SPRINT_HANDOFF §5):** rep-level necessity CONFIRMED,
conditional sufficiency (suff(DS)≫suff(Direct)), late-emergence timing, attention-routing knockout —
all cross-model (Llama-8B / Qwen3-14B / Phi-4-mini), all CIs exclude 0. **Behavioral: NULL on seed**
(bomb→substitution too benign; virus→Neutral already malicious). This is the gap.

**Freeze rationale:** results JSONs under `outputs/` are gitignored but present locally; numbers are
captured in docs + `EXPERIMENT_REGISTRY.csv`. Tag marks the pre-sprint commit for reproducibility.

---

## PHASE 2 — PAPER-FAITHFUL BEHAVIORAL BENCHMARK  🔶  (2026-07-27, started)

**Design (per plan §5).** Two-step build:
1. **Eligibility extraction (CPU/OpenAI, main loop)** — `16_prepare_behavioral_benchmark.py`:
   for each AdvBench instruction, GPT-4o-mini extracts the single harmful *concept noun* that (a) appears
   verbatim in the instruction (so `build_conditions` can swap it), (b) whose substitution *neutralizes*
   the request, (c) carries the harm (not the verb/task). Emits per-instruction flags + category.
   This is the §5.2 gate's LLM pre-screen (does NOT require DS success → no success bias).
2. **Behavioral screening (GPU/SLURM)** — `17_validate_behavioral_triplets.py` (reuses `14_behavioral_eval`):
   generate Direct/Neutral/Doublespeak on Llama-3.1-8B, judge, label triplets
   {DIRECT_REFUSED, NEUTRAL_BENIGN, DS_MALICIOUS, DS_REJECTED, DS_BENIGN_MISUNDERSTANDING, UNCLEAR}.
   Keep only behaviorally-eligible (Direct refused/harmful AND Neutral benign).

**Screening matrix (§5.4):** eligible candidates × codewords {≥2} × context-lengths {4,8,12 demos},
3 conditions → ≥1200 DS conditions target. Demos generated per unique (harmful_word, codeword, seed),
cached, reusing the paper method.

**Progress (iter 2, 2026-07-27):** eligibility extraction DONE — **193/200 LLM-eligible**
(wide funnel; rejects: 5 does_not_neutralize, 1 concept_too_long, 1 harm_not_from_concept).
Category dist of eligible: cyber 53, fraud 61, other 39, explosives 14, malware 9, narcotics 7,
weapons 6, toxins 3, bioweapon 1. **Concrete-object sweet-spot candidates ≈ 39** (explosives/
weapons/malware/toxins/narcotics/bioweapon); cyber/fraud (114) likely fail the Neutral-benign
check (verb/task-harm, substitution won't neutralize) — the GPU screen filters these automatically
(same failure mode as the seed's `virus`). 95 unique eligible concepts. Matrix (Step 2, demo-gen
for ~190 concept×codeword pairs) still building.

---

## PHASE 6 PRE-AUDIT (iter 2) — GCG/MAC reuse surface (plan §10.1)  ✅ MAJOR REUSE WIN

Existing optimization stack found — **Temporal-GCG/MAC is a plug-in, not a rewrite:**
- **`poc_stage_gcg_early/`** (full GCG): `gcg_optimizer.py` (`run_optimization`, `_token_gradients`,
  `_sample_control`, `_evaluate_candidates`, checkpoint/pareto), `objectives.py` — **already has
  `task_loss` (std GCG), `repr_loss` (representation distance to reference activations — labeled
  "the new scientific contribution"), `kl_loss`, and `ObjectiveWeights`**; `selected_state_capture.py`
  (`capture_selected_states` at chosen layers/positions); `suffix_token_manager.py`,
  `model_adapter.py` (embedding grads); `evaluate_optimized_suffixes.py` +
  `evaluate_cross_model_transfer.py` (held-out ASR + transfer); `build_*manifest.py`.
  Driver `run_optimization.py` (`--model-family {qwen3,gemma4,deepseek_r1}`, `--suffix-length`,
  `--n-steps`, `--topk`, `--batch-size`). Uses `--no-filter-cand` per memory.
- **`scripts/reinforce_objective/`**: `reinforce_mac.py` (`momentum_update`, `reinforce_mac_optimize`)
  = MAC; `trigger_gradient.py` (`topk_candidate_tokens`, `build_trigger_onehot`, `reinforce_trigger_gradient`)
  = GCG-style coordinate grads; `gpu_runner.py` (`build_surrogate_loss`, `reinforce_step`, `HFTargetModel`);
  `candidate_pool.py`, `proxy_ce_rerank.py`, `soft_prompt_reinforce.py` (soft-prompt baseline).

**→ Temporal objective (benign-early / harmful-late) plugs in as a LAYER-WEIGHTED `repr_loss`
variant** using `capture_selected_states` for early vs late layer sets, combined via `ObjectiveWeights`.
MAC baseline = `reinforce_mac_optimize`. Held-out ASR + transfer eval already exist. Defer deep read
to Phase 5/6; interface confirmed sufficient.

---

## RUN / JOB REGISTRY (this sprint)

| run/job | phase | cmd | status | output |
|---|---|---|---|---|
| tests | 1 | `pytest tests/` | ✅ 14/14 | — |
| bg `b3p10mgkd` | 2 | `16_..benchmark.py --n-instructions 200 --tag v1` | ✅ DONE | `eligibility_v1.json` (193/200) + `screening_matrix_v1.json` (1158 cond, 0 invariant fails, gitignored) |
| **SLURM 688994** | 2 | `run_behavioral_screen.sh` (17) DSTAG=llama8b_v1 | **SUBMITTED (PD)** | `outputs/behavioral_screen_llama8b_v1/` |

## USER DECISIONS (2026-07-27, binding for the loop)
- **Screen scale:** run the FULL 200-base matrix (×2 codewords ×3 lengths) as the first
  Llama-8B screening job (not eligible-only staging). Single L40S job.
- **Low-yield fallback:** if clean `DS_MALICIOUS` yield is low, EXPAND SOURCES — pull in
  ClearHarm + curated concept-noun prompts BEFORE drawing conclusions (do not immediately
  report null; do not pause for approval).
- **Loop:** session-only cron `0e2d79c5` (`*/30`). User may move to /schedule for durability.

---

## NEXT SINGLE HIGHEST-VALUE STEP
When extraction `b3p10mgkd` finishes: (1) validate `screening_matrix_v1.json` structure +
category spread; (2) `sbatch slurm/run_behavioral_screen.sh` on Llama-8B (FULL matrix per
user decision); (3) while it runs, start the benign parallel track — audit
`scripts/reinforce_objective/` GCG/MAC code (Phase 6 §10.1) and validate the Qwen3 thinking
toggle (Phase 7 §11.1). Screening yield decides the behavioral sweet-spot → unblocks Phases 3–5.
