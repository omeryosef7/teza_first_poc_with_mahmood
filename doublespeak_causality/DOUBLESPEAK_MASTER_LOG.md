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

### 2026-07-26 — SLURM resource triage
- Job 686481 (killable, generic --gpus=1 + nodelist n-801..805) was PENDING w/ est start ~00:44 (+2.5h): **all L40S GPUs allocated cluster-wide** (8/8 on every L40S node) — genuine contention, not misconfig.
- Tried faster routes: `--partition=gpu-sharifm,killable` → rejected ("Multiple partition job request not supported when a partition is set in the association"); `--partition=gpu-sharifm` alone → rejected ("User's group not permitted to use this partition"). So **killable is the only usable L40S partition**.
- Cancelled 686481, resubmitted as **686492** on killable with improved `--gres=gpu:l40s:1` (any L40S node incl t-806, vs original nodelist). PENDING/Priority; job id saved to outputs/.current_job_id. Wait is inherent to contention; loop will poll.

### 2026-07-26 — Align SLURM to proven house recipe (per Omer)
- Surveyed slurm_scripts: **210/216 use `--partition=killable --account=gpu-research --gpus=1` + `--nodelist=<L40S>`**; NONE use `--gres=gpu:l40s`. Even `stage6_single_sharifm.slurm` submits to killable (not partition=gpu-sharifm).
- Reverted my script from `--gres=gpu:l40s:1` to the proven `--gpus=1 --nodelist=n-801,n-802,n-803,n-804,n-805,t-806`. Cancelled 686492, resubmitted as **686494** (killable/gpu-research, PENDING/Priority). job id -> outputs/.current_job_id.

### 2026-07-26 — Job 686494 FAILED (exit 13) → root-caused → hardened → repro validates code
- **686494** got an L40S (n-802) but FAILED in 31s, **empty stderr**, ExitCode 13:0, Reason None. Died at the L40S guard (no "GPU check passed" printed).
- **Root cause:** guard used `GPU_TYPE=$(nvidia-smi --query-gpu=name ... | head -1)`. Under `set -euo pipefail`, if `nvidia-smi`'s query returns nonzero (exit 13 on that node, while still printing) the pipeline returns 13 → `set -e` aborts with 13. The earlier full `nvidia-smi` line had `|| true` (protected); the guard didn't. Locally nvidia-smi returns 0 → passed → node-specific.
- **Fix:** rewrote guard pipe-free with `|| true` + pure-bash first-line (`${GPU_ALL%%$'\n'*}`, case-match); added `PYTHONUNBUFFERED=1` and `python -u` so a future failure isn't swallowed by SLURM stdout buffering.
- **Code validated independently** (login-node repro, Llama-8B float16 across 3 TITAN Xp): `LOADED layers 32 hidden 4096 eos [128001,128008,128009]` (list-valued EOS preserved ✅), `capture ['codeword_last','following'] [33,4096] nocc 6` → **REPRO_OK**. So ds_common load/localize/capture are correct on the real model; the SLURM failure was purely the guard.
- Resubmitting hardened script to L40S for the canonical **bf16** Stage-1 run.

### 2026-07-26 — Loop iter: P3 patching script built (productive wait)
- 686553 PENDING/Priority (contention). While waiting, built **05_run_activation_patching.py** (§9): necessity (DS<-Neutral) + sufficiency (Neutral<-Direct) layer sweep with logit-lens P(harm)/P(code) readout; controls = identity (DS<-DS, must reproduce baseline) + norm-matched random. Offline-validated: compile OK; toy verifies LayerPatch indexing (reps[L+1]=layer-L hook output) + identity-replace is a no-op. Ready to submit once Stage-1 (686553) completes & trajectories are sane.
- P4 (timing §10.3) intentionally NOT built yet — it needs Stage-1's per-layer harmful direction d_harm as input.

### 2026-07-26 — 686553 ran past guard, hit real bug (smoke position mismatch) → fixed
- Guard fix worked: 686553 RAN on L40S n-802 (dev7), passed the guard, entered smoke test. Unbuffered fix worked: real traceback captured in stderr.
- **Bug (smoke_pipeline only):** `IndexError: index 100 out of bounds (size 53)` at ds_common LayerPatch. Cause: patch position `pos.codeword_last` computed on ds_text (pos 100, long w/ demos) but forward run on neu_text (53 tokens). Cross-text position mismatch.
- **Verified NOT present in 01_map_representations.py or 05_run_activation_patching.py** (both compute each position from the same text they patch/read).
- **Fix:** smoke now computes `neu_pos` from neu_text before patching; added `--dtype float16` for Pascal login-GPU validation. Compile OK. Re-validating end-to-end on login GPUs (float16) before spending another L40S slot.
- Model load + capture confirmed working on L40S bf16 (crash was after load, in the patch check).

### 2026-07-26 — Smoke FIX validated on Llama-8B; canonical run resubmitted
- Fixed smoke on login GPUs (fp16): **all 5 checks PASS** — load(32L,hidden4096,EOS[128001,128008,128009]), localization(cw@100,following@101,seqlen110), capture[33,4096]+following, patching(α0-identity✅, replace Δ=6.42 @L16), generation(23 tok, stop=eos). smoke_llama_login.json.
- **Known limitation logged:** find_word_occurrences returned 5 codeword occurrences here but repro counted 6 — it matches only ONE tokenization variant (space vs no-space), can undercount when the same word appears both sentence-initial and mid-sentence. codeword_LAST is still correct (used by Stage-1/2), so this does NOT affect P2/P3. **Must fix before P6 attention-knockout** (which needs ALL previous codeword occurrences). TODO in ds_common.find_word_occurrences: union matches across variants.
- Resubmitted canonical bf16 L40S run as **686635** (PENDING/Resources).

### 2026-07-26 — Stage-1 (P2) COMPLETE on L40S bf16; observational mechanism confirmed; P3 submitted
- **686635 COMPLETE**: smoke all-pass (bf16), Stage-1 wrote stage1_repmap_Llama-3.1-8B-Instruct_20260726_231610. Model load ~5min (slow NetApp on n-804), not a hang.
- **Observational findings (NOT causal — see CAUSAL_RESULTS_SUMMARY.md §1):** cos(DS,Direct) rises 0.06→~0.6 across layers (cos-to-Neutral stays ~0.85 = superposition); Patchscopes P(harm) crosses P(code) at L17/20/21, peaks late (L30-31); NN-decode aux: poison_mango codeword→" poison"/" deadly" at L24/28/31, bomb_potato→" makeshift"/" ingredients" L24. potato(0.125)≫carrot(0.009) for bomb (RQ6 signal). Effect directionally matches paper; absolute probs modest (hand-written seed demos).
- **§25 gates passed** → advanced to P3.
- **Built** slurm/run_stage2_llama8b.sh (from proven stage1 template), submitted **686643** (05_run_activation_patching.py: necessity DS<-Neutral + sufficiency Neutral<-Direct + identity/random controls). PENDING/Resources.
- **Caveat logged:** strengthen with GPT-4o-mini demos + more items before quantitative claims.

### 2026-07-26 — P3 patching: device+identity bugs fixed, PRELIMINARY necessity result, canonical submitted
- git works now (user added allow-rule): committed cd8a3fc (stage1+2 scaffold), 5e3c847 (device+union fixes), + identity-tol tweak. NOTE: `git push` is classifier-blocked (distributes harmful content to remote); Omer must `!git push`.
- **Ran benign parallel Workflow** (2 agents, 0 kills): stats.py (paired bootstrap/McNemar/permutation/Holm — spot-verified correct) + plots.py (4 PNG fns). Confirms benign-only delegation is safe under cyber-safeguard.
- **Bugs fixed in 05:** (1) CPU/GPU device mismatch in random-control vector (job 686643 exit-1); (2) identity control too-tight tol → now noise-aware relative gate; added --dtype. Also fixed ds_common.find_word_occurrences variant-undercount (union across space/no-space) + regression test (14/14 pass).
- **PRELIMINARY causal necessity (fp16 login):** DS←Neutral patch has ~no effect early (L0-4) but collapses P(harm) from mid-layers (potato 0.128→0.04@L6→0; mango 0.207→0@~L12). Identity id_max_dev≪effect; random control doesn't mimic. = codeword's ACQUIRED harmful component is necessary from mid-layers. Sufficiency null but readout-limited (logit-lens = next-token, not meaning) → refine with Patchscopes readout.
- **Submitted canonical bf16** P3 = **686723** (PENDING/Resources).
- **Next:** confirm 686723; refine sufficiency via Patchscopes readout; build P4 timing (§10.3) using Stage-1 d_harm + necessity-informed layers.

### 2026-07-26 — P4 timing script built+validated; needs stronger attack baseline
- Added generation-safe bounds guard to LayerPatch (persistent injection hook survives KV-decode); 14/14 tests + toy check.
- Built 06_run_timing.py (§10.3): inject held-out d_harm at early/mid/late layers, measure semantic (Patchscopes) + behavioral (refusal). Validated code path on login GPU (float16).
- **Finding (not a bug):** seed gives NO timing signal — baseline neutral prompt already "refuses" (nonsensical "build a potato" + keyword-detector false positives), early=late=100%. Timing needs a SUCCESSFUL Doublespeak baseline => paper-faithful GPT-4o-mini demos + StrongReject judge. Logged as CAUSAL_RESULTS_SUMMARY F1.
- **Decision for next iterations:** promote demo-generation (GPT-4o-mini over AdvBench, plan §6) to the critical path — it strengthens P2/P3 magnitudes AND unblocks P4 behavioral. Harmful-text generation => main loop only (cyber-safeguard).
- Committed cd8a3fc..3f690db (7 commits). git push remains classifier-blocked (Omer: !git push).
- P3 canonical bf16 (686723) still PENDING/Resources.
