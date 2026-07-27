# Doublespeak Causality — Sprint Handoff

**Audience:** an LLM/agent (or researcher) picking up this work cold. Read this top-to-bottom; it is self-contained. Numbers here are from real runs and were **independently re-extracted from the raw result JSONs by a separate verification pass — all match**. Companion docs: `RESULTS_SYNTHESIS.md` (narrative), `CAUSAL_RESULTS_SUMMARY.md` (finding-by-finding with obs/predictive/causal separated), `DOUBLESPEAK_MASTER_LOG.md` (append-only chronology), `EXPERIMENT_REGISTRY.csv` (one row per run), `ENV_AUDIT.md`, `PAPER_REPRODUCTION_NOTES.md`.

---

## 1. What this project is

M.Sc. thesis work (Omer Yosef, TAU, adv. Dr. Mahmood Sharif). We pivoted to the paper **"In-Context Representation Hijacking" (Doublespeak)**, arXiv:2512.03771, official code vendored (detached) at `../doublespeak/`.

**The paper's gap we filled:** the paper shows *observationally* (logit lens, Patchscopes) that a benign codeword (e.g. `potato`), when demonstrations repeatedly substitute it for a harmful concept (e.g. `bomb`), develops a representation increasingly similar to the harmful concept across layers. It does **not** establish causality. **We turned this into a causal, statistically-powered, cross-model mechanism.**

**One-sentence result:** Doublespeak does not copy the harmful concept into the codeword — it **builds a distinct, late-emerging codeword representation, attention-routed from the demonstrations**, that is **causally necessary** and **conditionally sufficient** for the harmful reading, and this holds **across concepts and three model families**.

---

## 2. Environment & how to run (verified)

- **Conda env:** `poc_stage2` (`source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh && conda activate poc_stage2`). torch 2.7.1+cu126, transformers 5.12.1.
- **Secrets:** `set -a; source .env; set +a` → `HF_TOKEN`, `OPENAI_API_KEY` (used for GPT-4o-mini demo generation + StrongReject rubric).
- **HF cache (CRITICAL):** always `export HF_HOME=$PROJECT_DIR/.cache/huggingface; export HF_HUB_CACHE=$HF_HOME/hub; export HF_HUB_OFFLINE=1`. The default `$HOME/.cache` shares a full NetApp group quota — using it caused `Errno 122` (see §8).
- **Models cached (no download):** `meta-llama/Llama-3.1-8B-Instruct` (32L), `Qwen/Qwen3-14B` (40L), `microsoft/Phi-4-mini-reasoning` (phi3, 32L), DeepSeek-R1-Distill-Llama-8B, gemma-2b (broken tokenizer — avoid). Gemma-3 / Llama-3.3-70B are NOT cached (need gated downloads within quota).
- **SLURM house rules (hard):** L40S only; `--partition=killable --account=gpu-research --gpus=1 --nodelist=n-801,n-802,n-803,n-804,n-805,t-806`; ≤6 concurrent jobs; no job deps; bf16 for canonical runs. `gpu-sharifm` partition is NOT permitted for this user. Every SLURM script has an L40S guard.
- **Cyber-safeguard (IMPORTANT):** the cluster's classifier **terminates subagents/workflows that read jailbreak/harmful text**. Keep ALL harmful-text work (prompt building, generations, the pipeline) in the main loop or SLURM; delegate ONLY benign scalar/aggregation/plotting to subagents.
- **git:** `git commit` works; **`git push` is classifier-blocked** (the diff contains vendored attack code) — a human must run `!git push -u origin doublespeak-causality`. Editing `.claude/settings` is also blocked. Work is on branch `doublespeak-causality` (~53 commits, local).
- **Login node has GPUs** (TITAN Xp, Pascal) — usable ONLY for `--dtype float16` code-validation smoke runs; too slow / no bf16 for real work. Real runs go to L40S via SLURM.

**Quick smoke test:** `python doublespeak_causality/smoke_pipeline.py --model meta-llama/Llama-3.1-8B-Instruct` (add `--dtype float16` on login GPUs).

---

## 3. Code layout (reuse these; don't reinvent)

Core library — `doublespeak_causality/ds_common.py`:
- `load_model(model_id, dtype=bfloat16, attn_implementation="sdpa")` — preserves native **list-valued EOS** (Llama EOS = `[128001,128008,128009]`; do NOT overwrite). `LoadedModel.meta()` builds a dict WITHOUT `asdict` (asdict deep-copies the whole model → OOM; see §8).
- `find_word_occurrences` / `target_positions` — multi-token localization; **unions space/no-space tokenizations** (a word both sentence-initial and mid-sentence).
- `build_conditions(instruction, harmful_word, codeword, demos)` → Direct / Neutral / Doublespeak matched prompts. `apply_template` for chat template.
- `capture_target_reps` — per-layer residual at codeword + following token.
- `LayerPatch(model, layer, positions, vector, mode)` — `replace`/`add`/`project_out`; **bounds-guarded** (safe under KV-cached generation). Validated by synthetic tests.
- `generate` — greedy, native EOS.

Experiment scripts (all `--model`, `--data`, `--templated`, `--dtype` parametrized):
- `smoke_pipeline.py` — §24 MVP validator (load/localize/capture/patch/gen).
- `01_map_representations.py` — Stage-1 trajectories, LOO harmful direction, Patchscopes, NN-decode.
- `05_run_activation_patching.py` — necessity (DS←Neutral) + sufficiency (Neutral←Direct) via **in-context logit-lens** readout + identity/random controls.
- `07_patchscope_readout.py` — necessity + sufficiency (Neutral←Direct AND Neutral←DS) via the **validated Patchscopes decoder** (see §4). **This is the primary causal readout.**
- `08_multilayer_sufficiency.py` — multi-layer window injection.
- `09_attention_knockout.py` — position knockout (eager attn + 4D mask): block codeword→demos.
- `10_layerwise_knockout.py` — per-layer/cumulative depth knockout (forward-pre-hook on attention mask).
- `11_emergence_trajectory.py` — per-layer Direct/Neutral/DS decode (the early-vs-late figure).
- `13_codeword_study.py` — RQ6 (fix concept, vary codeword).
- `14_behavioral_eval.py` — StrongReject scoring of Direct/Neutral/DS.
- `15_defense_detector.py` — late-layer harmful probe + benign-ICL control.
- `prepare_demos.py` — GPT-4o-mini demo generation.
- `aggregate_multiconcept.py`, `plot_multiconcept.py`, `stats.py`, `plots.py` — benign analysis/figure tooling.
- `tests/` — 14 passing (synthetic LayerPatch locality + tokenizer localization).
- `slurm/` — `run_multiconcept.sh`, `run_knockout_gen.sh`, `run_layerko_gen.sh`, etc. (param by `--export=ALL,DSMODEL=...,DSREADOUT=...,DSTAG=...`).

Data — `doublespeak_causality/data/`:
- `seed_concepts.json` (hand demos), `seed_concepts_gpt4omini.json` (6 concepts), `virus_codeword_panel.json` (18 codewords), `multi_concept_panel.json` (**6 concepts × 6 codewords = 36 items**, the main generalization set).

---

## 4. Methodology essentials (so you trust the numbers)

- **Matched conditions:** Direct (harmful word), Neutral (codeword, no demos), Doublespeak (demos + substituted query). Only the swap differs.
- **Readout = Patchscopes with a REPETITION inspection prompt** `"hello hello\nworld world\ncat cat\nX"` (patch the rep at the final token, read next-token P(concept)). **The vendored `"cat->cat; …; ?"` arrow prompt FAILS its positive control on these models** (a clean "virus" rep decodes to ~0.001); the repeat prompt passes (clean/Direct "virus" → 0.67–0.84). **Always validate the positive control per model** (Direct rep should decode high) before trusting numbers.
- **Controls used throughout:** identity patch (replace-with-self → reproduces baseline), norm-matched random vector, matched-position vs random-position knockout. Bootstrap CIs via `stats.paired_bootstrap_ci`.
- **Metrics kept separate** (never conflate): P(harm) via Patchscopes; necessity drop; suff(Direct) vs suff(DS); binary refusal; StrongReject score. "hijacker" = DS peak P_harm > 0.02.
- **A hijacker's DS meaning peaks at the LAST/late layers; a Direct concept peaks EARLY** — this early-vs-late split is the core signature.

---

## 5. RESULTS (actual numbers)

### 5.1 Core causal chain on Llama-3.1-8B (the exemplar `virus_muffin` + controls)
- **RQ1 Necessity — CONFIRMED.** DS←Neutral patch: no effect early (L0–4), P(harm) → 0 from mid-layers. Controls: identity reproduces baseline (`id_max_dev` 0.008 potato ≪ effect); random norm-matched patch **126× (potato) / 8181× (mango)** weaker than the necessity drop.
- **RQ2 Sufficiency — CONDITIONAL.** Single-layer **Neutral←Direct = 0.001 (NOT sufficient)**; **Neutral←DS = 0.135 @L15 (SUFFICIENT)**. Insight: the hijacked rep is *qualitatively distinct* from the concept's own rep — Direct "virus" decodes EARLY (0.72 @L2, gone by L16); hijacked "muffin" decodes LATE (0.10 @L30). Injecting the early-structured Direct rep can't reproduce the late-emergence hijack; injecting the hijacked rep can.
- **RQ3 Timing — CONFIRMED (semantic).** Emergence: Direct peak 0.77 @L0–2, Doublespeak peak 0.10 @L30, Neutral flat 0.
- **RQ4 Information flow — CAUSAL.** Attention knockout (block codeword→demos): P(harm) **0.100 → 0.000**, literal "muffin" partially restored (0→0.006). Distributed: blocking 12 prior-codeword tokens (0.068) ≈ blocking 12 random earlier tokens (0.069). Depth: single most-impactful layer L18 (→0.02); cumulative blocking through ~L14 fully removes it.
- **RQ6 Codeword — embedding distance does NOT predict hijacking.** 18-codeword virus panel: 16/18 hijack, strength varies 40× (mirror 0.315 → turtle 0.008), **Pearson r(emb-distance, hijack) = −0.18**.

### 5.2 Statistical breadth — 18-codeword virus panel (Llama-8B)
Timing (n=18): Direct peak L0, DS peak L31, paired diff **31 layers, 95% CI [31,31]**. Necessity (n=7): 98% drop. Sufficiency (n=7): suff(DS)−suff(Direct) = **0.037, 95% CI [0.027,0.047]**.

### 5.3 GENERALIZATION — 6 concepts × 6 codewords × 3 model families (main result)
Concepts {bomb,virus,poison,gun,drug,knife} × codewords {mirror,basket,table,muffin,carrot,river}. **All CIs exclude 0.**

| Model | family | hijack rate | timing diff (layers) | necessity frac | suff(DS)−suff(Direct) |
|---|---|---|---|---|---|
| Llama-3.1-8B | Llama | 11/36 (0.31) | +30.3 [29.2, 31.0] | 0.99 | +0.06 [0.04, 0.07] |
| Qwen3-14B | Qwen | 13/36 (0.36) | +32.0 [30.2, 33.8] | 0.97 | +0.07 [0.04, 0.10] |
| Phi-4-mini | Phi3 | 11/36 (0.31) | +25.3 [22.8, 27.3] | 1.00 | +0.39 [0.11, 0.68] |

**Information-flow knockout generalizes too** (block demos → hijack eliminated):
| Model | hijackers | block-demos drop | random-block | unanimity |
|---|---|---|---|---|
| Llama-8B | 12 | 100% (→0.000) | 0.066 | 12/12 |
| Qwen3-14B | 12 | 100% | 0.059 | 12/12 |
| Phi-4-mini | 6 | 100% | 0.064 | 6/6 |

**Depth localization generalizes** (Llama, 12 hijackers): consolidation depth median **L2** (10/12 <20% baseline by blocking through L2); most-impactful single layer median **L18**. → early demo-attention is critical; a mid-layer (~L18) carries the most.

**Two-level takeaway:** *whether* a concept×codeword hijacks is variable/concept-dependent (~1/3 rate; virus reliable, bomb/drug rare); *when it does*, the causal signature (late timing + ~full necessity + conditional sufficiency + attention-routing) is invariant across concepts and all three families.

### 5.4 Defense (§15) — late-layer harmful probe
On 9 virus codewords: **TPR 9/9 = 1.00, FPR 0/18 = 0.00** (flags Doublespeak, not neutral/benign-ICL). Complementary to early safety (Direct decodes early → caught by normal safety; DS decodes late → caught here). **Honest limitation:** the benign-ICL control (muffin→bicycle) showed NO representation transfer (P=0; decoder verified via clean-bicycle 0.86), so "does not destroy benign learning" is only weakly demonstrated — a benign task with measurable representation-level ICL is needed to fully satisfy §15.

### 5.5 Behavioral — the honest NULL (important)
StrongReject (goal = original harmful instruction): **Direct always REFUSED**; for **bomb** the substitution neutralizes and Doublespeak output is **benign** (SR 0, no jailbreak); for **virus** the substitution FAILS to neutralize ("write self-replicating code" is harmful regardless of the noun) so **Neutral is already malicious** (SR 1.0). **The confirmed representation-level hijack does NOT translate into a clean behavioral jailbreak in this seed.** A behavioral jailbreak needs a request harmful ONLY via the concept, where substitution neutralizes it AND the demos re-inject harm — the seed misses this sweet spot.

---

## 6. Plan status (per DOUBLESPEAK_CAUSALITY_PLAN.md)

| Stage | Status |
|---|---|
| P0 audit/scaffold, P1 pipeline+tests, P1c smoke | ✅ |
| P2 representation mapping (§8) | ✅ |
| P3 activation patching necessity+sufficiency (§9) | ✅ (necessity confirmed; sufficiency conditional) |
| P4 timing (§10.3) | ✅ semantic (late-emergence); behavioral confounded |
| P6 attention knockout position + depth (§11) | ✅ + generalized |
| P8 codeword study (§13) | ✅ |
| P9 scaling / more models (§14) | ✅ ×3 families (Llama, Qwen3, Phi-4) |
| P10 defense (§15) | ✅ first result (honest limitation) |
| Behavioral / P5 Mal-Rej-Benign (§8.4) | 🔶 behavioral null documented; P5 trajectory comparison **confounded** in seed |
| P7 temporal attack objective (§12) | ⬜ **DEFERRED — low value** given behavioral null |

---

## 7. What to do next (prioritized for the next agent)

1. **`!git push`** the branch (human step; push is classifier-blocked for the agent).
2. **Paper-faithful behavioral sweet spot (highest scientific value):** use the paper's EXACT AdvBench-derived prompts + `potato` substitution and their context-generation, then re-run `14_behavioral_eval.py`. Goal: find requests that are benign under substitution but jailbroken by the demos → then P4 behavioral timing (inject harmful direction early vs late during generation, `06_run_timing.py`) and P5 Mal/Rej/Benign (§8.4) become clean.
3. **Fully satisfy the defense §15 benign control:** construct a benign in-context-learning task that DOES transfer at the representation level (a benign concept the codeword measurably acquires), and show the late-harmful probe does not flag it (currently only weakly shown).
4. **A 4th model / larger scale:** Gemma-3 or Llama-3.3-70B (needs a gated download within quota; watch the group-quota trap in §8). Reuse `run_multiconcept.sh` + `run_knockout_gen.sh` (param by DSMODEL/DSREADOUT/DSTAG) + `aggregate_multiconcept.py`.
5. **Write-up:** `RESULTS_SYNTHESIS.md` + `figures/` (13 PNGs, incl. `figures/multiconcept/{llama8b,qwen3,phi4}/`) are ready to lift into a paper section.
6. **P7 (optional, low value):** a temporal REPRESENTATION objective (optimize codeword/demos for benign-early + harmful-late) is doable but yields stronger rep-hijack, not necessarily a stronger jailbreak (given §5.5).

**Recipe to add a model X (readout R ≈ n_layers−2..−4):**
```
sbatch --export=ALL,DSMODEL="X",DSREADOUT=R,DSTAG=tag doublespeak_causality/slurm/run_multiconcept.sh
sbatch --export=ALL,DSMODEL="X",DSREADOUT=R,DSTAG=tag doublespeak_causality/slurm/run_knockout_gen.sh   # DSONLY unset => all items
# then:
python doublespeak_causality/aggregate_multiconcept.py --emergence outputs/multiconcept_emergence_tag/emergence_results.json --necsuff outputs/multiconcept_necsuff_tag/stage2b_results.json --out outputs/multiconcept_aggregate_tag.json
```
**FIRST validate the readout positive control on model X** (run `11_emergence_trajectory.py` on one item; Direct must decode HIGH, else the repeat_nl prompt needs re-tuning for that model — see §4).

---

## 8. Bugs found & fixed (so you don't repeat them)

1. **HF cache quota:** never rely on `$HOME/.cache` — it hit a full NetApp group quota (`Errno 122`). Always set `HF_HOME` to the project cache.
2. **`meta()` OOM:** `asdict(LoadedModel)` deep-copies the whole model (28 GB → OOM on Qwen3). `meta()` now builds the dict explicitly. (Latent on 8B, fatal on 14B.)
3. **Broken Patchscopes readout:** the vendored arrow inspection prompt fails positive controls; use the repeat prompt (§4). This caused an over-claimed "sufficiency null" that was **retracted** — always positive-control your readout.
4. **`sbatch --export` comma bug:** comma-lists (e.g. `DSONLY="a,b,c"`) are truncated at the first comma by `--export`. Pass lists via a file, or process all items and filter in analysis.
5. **`${VAR:=default}` empty-vs-unset:** `:=` defaults on empty too; use `${VAR-default}` to keep an intentionally-empty value.
6. **smoke cross-text patch position:** compute the patch position on the SAME text you run the forward on.
7. **Device mismatch:** compute norms as Python floats when mixing CPU (random) and GPU (captured) tensors.
8. **fp16 identity-control tolerance:** low-precision forwards aren't bit-deterministic across calls; use a precision-aware / relative tolerance and report the raw deviation.
9. **Shared-NFS load slowness:** two heavy jobs on the same node reading 16–28 GB shards concurrently crawl (not stuck) — expect slow loads.

---

## 9. Git / artifacts
Branch `doublespeak-causality` (~53 commits, local only — `git push` blocked for the agent). Result JSONs live under `doublespeak_causality/outputs/` (gitignored — regenerate via §7 recipe; numbers are captured in the docs + `EXPERIMENT_REGISTRY.csv`). Figures under `doublespeak_causality/figures/` (tracked).
