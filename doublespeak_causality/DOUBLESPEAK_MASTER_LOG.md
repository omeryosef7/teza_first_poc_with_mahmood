# Doublespeak Causality — Master Log (append-only)

Chronological. Newest at bottom. One block per meaningful action (plan §22).

---

### 2026-07-26 — Session start (env audit + scaffold)
- **git:** `f646dd4` (main)
- **Actions:**
  - Cloned official repo `1tux/doublespeak` → `doublespeak/`, detached its git, added the paper PDF (prior turn).
  - Read `doublespeak/{doublespeak_attack.py,mech_interp.py,README.md}`; identified reusable `LogitLens`/`Patchscopes` and reference bugs.
  - Audited env: `poc_stage2` (torch 2.7.1, transformers 5.12.1, CUDA ok). SLURM: account `gpu-research`, L40S nodes n-801..805, killable. Secrets: HF_TOKEN (verified gated access to Llama-3.1-8B-Instruct), OPENAI/GEMINI keys.
  - Inventoried reusable thesis code in `poc_stage4/` (causal tracing, patching, attention extraction, head ablation, refusal directions) + `strong_reject/`.
  - Wrote `ENV_AUDIT.md`, `PROGRESS.md`, `PAPER_REPRODUCTION_NOTES.md`, `EXPERIMENT_REGISTRY.csv`, this log.
- **Run:** started background download of `meta-llama/Llama-3.1-8B-Instruct` → `logs/llama_download.log` (bfloat16 loading planned).
- **Status:** P0 PARTIAL (download RUNNING).
- **Bugs found:** reference `mech_interp.main()` calls non-existent `Patchscopes.analyze_representation_shift`; `doublespeak_attack.main()` references undefined `harmful_query`, missing `batch_create_prompts`. Core class methods are sound.
- **Incident (storage):** first download launched without `HF_HOME` → wrote to `$HOME=/a/home/cc/students/math/omeryosef/.cache` which shares the `cs_sharifm` **group quota**; filled it → `Errno 122 Disk quota exceeded`, which also blocked an unrelated MD write (`EDQUOT fsync`). **Fix:** killed download, `rm -rf` the partial `models--meta-llama--Llama-3.1-8B-Instruct` from cc-home, restarted download with `HF_HOME=$PROJECT_DIR/.cache/huggingface` (sharifm project fs, roomy — already holds Qwen3-14B 32G). **Lesson for all future runs/SLURM:** always export `HF_HOME`/`HF_HUB_CACHE` to the project cache (matches `slurm_scripts` convention); never rely on default `$HOME` cache.
- **Next:** build `ds_common.py` + unit tests (GPU-free) while model downloads.

### 2026-07-26 — Core library + tests + plumbing validation
- **git:** `f646dd4` (main) — pre-commit.
- **Built:** `doublespeak_causality/ds_common.py` (model load bf16+sdpa w/ native EOS; `find_word_occurrences`/`target_positions` multi-token localization incl. following-token per §8.1; `build_conditions` Direct/Neutral/Doublespeak; `capture_target_reps`; `LayerPatch` replace/add/project_out; `generate`). Reuses vendored `doublespeak/` on sys.path.
- **Tests (13/13 PASS):**
  - `tests/test_layerpatch_synthetic.py` (6) — GPU-free synthetic proof that LayerPatch edits only the target position/layer and propagates downstream; α=0 identity; project_out; hook cleanup.
  - `tests/test_localization.py` (7) — real Llama-3.1 tokenizer: all-occurrence finding, multi-token words, following-token, chat-template round-trip position validity, condition swapping.
- **GPU plumbing validation** (`smoke_pipeline.py` on cached gemma-2b, TITAN Xp dev1): load ✅, α=0 add identity ✅ (real forward), hidden-state capture shape ✅ [19,2048], generation runs ✅. localization/patching checks INCONCLUSIVE here only because **gemma-2b's cached tokenizer is broken in this env** (encodes all text → unk id [3], seq collapses to 1 token). Not a pipeline bug (Llama tokenizer passes 7/7). gemma-2b is not a plan model.
- **Blocker (quota):** every Llama-8B download attempt → `Errno 122 Disk quota exceeded` (project cache AND $HOME). Filesystem free = 522 G, so it's a NetApp qtree quota. Found redundant 32 G Qwen3-14B duplicate in user-home cache (project-cache copy is SLURM-canonical) → proposed safe deletion, pending Omer's OK.
- **Status:** P0 ✅, P1a ✅, P1b ✅, P1c PARTIAL/BLOCKED.
- **Next:** (a) resolve quota → download Llama-8B → run `smoke_pipeline.py --model meta-llama/Llama-3.1-8B-Instruct`; (b) build Stage-1 representation-mapping script (works offline against ds_common) while waiting.

### 2026-07-26 — Quota resolved, Llama-8B down, Stage-1 built & submitted
- **Decisions (Omer):** delete redundant user-home Qwen3-14B dup (freed 32 G); add git Bash allow-rule.
- **Quota:** `rm -rf ~/.cache/huggingface/hub/models--Qwen--Qwen3-14B` (SLURM-canonical project copy intact) → restarted download → **Llama-3.1-8B-Instruct COMPLETE** (4 shards, sha `0e9e39f249a1`, project cache).
- **git blocker (unresolved, needs Omer):** classifier blocks `git commit`, `git push`, the `update-config` skill, AND editing `.claude/settings.local.json` to add the allow-rule. Cannot self-enable. Handing exact commands to Omer. Branch `doublespeak-causality` has 19 files staged.
- **Built:** `data/seed_concepts.json` (3 matched concepts, seed-variant), `01_map_representations.py` (Stage-1 §8: LOO harmful direction, DS trajectory proj/cos/norm-score, Patchscopes crossover via vendored code, logit-lens NN-decode aux, onset/AUC summary), `slurm/run_stage1_llama8b.sh` (L40S, guard, resumable). Offline checks pass (compile + build_conditions + LOO shapes).
- **Submitted:** `sbatch` job **686481** (ds_stage1_llama8b, L40S, PENDING) = smoke_pipeline + 01_map_representations on Llama-8B.
- **Status:** P0 ✅, P1a ✅, P1b ✅, P1c RUNNING (686481), P2 RUNNING (686481).
- **Loop:** 30-min cadence set; each wake: poll 686481 → on COMPLETE analyze Stage-1 (check trajectories differ, α=0 identity, localization) → build+submit Stage-2 patching (§9) → update docs.
- **Next highest-value experiment:** once 686481 completes and trajectories look sane, **P3 activation patching (necessity DS←Neutral + sufficiency Neutral←Direct)** — the first true causal test.
