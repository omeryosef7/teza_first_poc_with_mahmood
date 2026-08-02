# reports/CAUSAL_PATCHING_AUDIT.md — Phase 0 Repository & Result Audit

Audit of the existing Doublespeak causal-circuit codebase, produced by a 7-lane parallel
code audit (no harmful text read). Basis for reuse decisions in `CAUSAL_CIRCUIT_MASTER_PLAN.md`.

- **Date:** 2026-08-02 · **Branch:** `behavioral-causality-sprint` · **HEAD:** `ee74d57`
- **Model:** `meta-llama/Llama-3.1-8B-Instruct`, **bf16**, `attn_implementation='sdpa'` (house standard).
  For attention-edge/knockout work the model MUST be loaded **eager** (see §Bugs).
- **Env:** conda `poc_stage2` (`/home/sharifm/students/omeryosef/miniconda3`); torch 2.7.1+cu126, transformers 5.12.1, CUDA available. `pandas`/`pyarrow` present in this env (absent in bare `python3`).

---

## 1. Repository map (what exists, and what plan phase it serves)

### Core reusable libraries (REUSE — do not rewrite)
| File | Key symbols | Serves |
|---|---|---|
| `ds_common.py` (754 L) | `load_model`/`LoadedModel`, `find_word_occurrences`(**all occurrences, multi-token aware, offset-based**), `find_word_occurrences_in_text`, `target_positions`/`TargetPositions{codeword_last, codeword_all_last, following}`, `build_conditions`/`Conditions{direct,neutral,doublespeak}`, `apply_template`+`parse_enable_thinking`, `capture_target_reps`, **`LayerPatch(model,layer_idx,positions,vector,mode∈{replace,add,project_out},alpha)`**, `patch_layer_sweep`, `generate` (list-EOS safe), `cosine` | Phase 3 (residual patching), all localization |
| `pair_common.py` (741 L) | `resolve_positions`/`PairPositions`, `capture_components`/`ComponentCapture`, `DemoStateSwap`, `SubmodulePatch`(attn/mlp submodule replace/project), **`AttentionKnockout`** (per-edge query→demo, pre-softmax score→−inf, softmax renormalizes; per-head; multi-subtoken), `ZHeadPatch`/`ZHeadCapture` (per-head z), `make_project_out_hook`/`AllPositionProjectOut`(+MultiLayer), `make_add_hook`/`AllPositionAdd`(+MultiLayer), `semantic_score`, `patched_generate`, `norm_matched_random`/`orthogonal_random`/`in_subspace_random` | Phases 4, 5, 9 |

### Experiment scripts (reuse / extend)
| Script(s) | Purpose | Serves | Coverage today |
|---|---|---|---|
| `01_map_representations.py` | per-layer d_harm=mean(Direct)−mean(Neutral), LOO | Phase 2/8 | concept dir (3rd inconsistent builder) |
| `05_run_activation_patching.py`, `08_multilayer_sufficiency.py` | residual necessity/sufficiency | Phase 3 | single pair, n≈24-30, resid_post only |
| `07_patchscope_readout.py`, `46_forced_choice_patchscope.py`, `31_validate_readouts.py` | forced-choice / cloze concept readouts | Phase 2/8 | gated positive control |
| `09_attention_knockout.py`, `10_layerwise_knockout.py`, `36_pair_attention.py` | attention-edge / layerwise knockout | Phase 4 | **coarse**: L0,2,…,30; whole-layer; per-head via 36 |
| `33_build_directions.py` | d_Direct (concept) + d_DS (signature) + BENIGN_REMAP/UNRELATED/REPEATED cells, cross-fit dev/heldout | Phase 2 | concept & signature only (no refusal) |
| `build_refusal_direction_llama.py` | refusal_direction (harmful/refused vs harmless/compliant), layers 12-20, `--validate` gen gate | Phase 2 | separate output tree |
| `14/16/17/18/19_*` behavioral | StrongREJECT-scored generation, necessity/sufficiency by window | Phase 2 | windows: early/mid/late/late_half |
| `43_transplant_mediation.py`, `44_kv_mediation.py` | state×context transplant, demo-KV mediation | Phase 3/4 | single pair |
| `48_attribution_patching.py`, `49_head_attribution.py`, `51_mlp_attribution.py` | AtP (gated vs true patch) for resid/head/MLP | Phase 5/6 | 49 **OOMs on 14B**; layer subsets |
| `50_path_patching.py` | head→head z-edge path patching | Phase 7 | **head→head only, L7-14, top-8** |
| `25_eval_gcg_asr.py`, `gcg_manifest_bridge.py`, `gcg_mixed_cache.py`, `37_soft_prompt_objective.py` | GCG ASR eval, mixed-cache, soft-prompt objective gate | Phase 10/11 | Qwen3 temporal run only |
| `tests/` (17 files) | GPU-free synthetic + tokenizer tests | engineering | see §5 |

---

## 2. Existing scientific results (provenance-backed; the *hypothesis* the new plan tests exhaustively)

All on **pair CARROT↔BOMB** (+ grenade/chlorine/pistol/cocaine), Llama-3.1-8B bf16, single pair, n≈24-30, mostly single seed. Full synthesis in `MECHANISM_SYNTHESIS.md`.

- **Retrieval (induction):** query codeword attends to demo codewords 3.5× vs random (bomb 3.51, grenade 3.54, chlorine 3.25; N7-L, `outputs/attn_retrieval_*_699219`). Descriptive only.
- **Write (attention) mid-band L7–9 peak L9:** per-head z-AtP validated vs true z-patch pearson 0.97–0.99; distributed (top-20 heads = 12%); no head has direct-to-logits path.
- **Consolidate (MLP) L9–14 peak L11–14:** MLP-AtP validated vs true SubmodulePatch(mlp) pearson 0.93–0.95 (bomb L11 47.3%, grenade L11 52.9%, chlorine L14 40.9%; N7-A). Attention→MLP +1/+2 layer cascade (N7-E).
- **Carry (late) passive:** late MLP true-patch peaks L31 by *readout proximity* (AtP corr 0.11) — mechanical, not computation (N7-C).
- **Dissociation headline (S2):** IE_state≈0 (all depths, self-transplant faithfulness exactly 0), DE_context≈99% (Llama)/92% (Qwen3). Reading = f(receiver context), not local codeword state. Jobs 694417 (cloze), **694691 (forced_choice, n=30, DEFINITIVE)**, 694472 (seed-1 replication).
- **KV re-read (S3):** neutralizing demo K/V removes only ~9% (forced_choice mid, job 694691) — distributed, not a trivial re-read.
- **TOCTOU:** refusal check depth-gated; Direct-concept injection refusal early 0.87 / mid 0.25 / late 0.02, early−late +0.846 [.787,.899]; cross-model Llama +0.846, Qwen3 +0.854, Phi-4 +0.250. Behavioral flip 4/5 pairs (bomb +0.425 … chlorine null).

### ⚠ Priors that materially constrain later phases (report, don't ignore)
- **`d_DS` (doublespeak_signature) is CAUSALLY INERT** while **`d_Direct` (concept) is the lever** (5/5 pairs, 15 cells; CAUSAL_CORE_FINDINGS §2). Do **not** treat the DS signature as a behavioral objective.
- **Selecting codewords by causal semantic score WORSENS ASR:** TOP−BOTTOM = −0.133 [−0.200,−0.050].
- **The temporal/repr objective is NOT GCG-suffix-optimizable and BACKFIRES:** held-out ASR temporal 0.0, refusal 0.0→0.615; repr_loss flat across 3 configs (`outputs/gcg/gcg_asr_summary.json`, GCG_MAC_COMPARISON §6). Doc verdict: the attack is **demonstration-bound**, not distillable into a universal suffix.
- **N7-M all-layer induction-edge knockout is DEGENERATE/CONFOUNDED** (blocking raises p_concept; random raises it most). A **surgical per-head edge knockout at retrieval layers** (exactly Phase 4.2) is the flagged next step.
- **Do NOT cite `d_Direct = +0.971` install** — unbacked on disk; reproducible pipeline gives **+0.028/+0.029** (jobs 693571, 694706).

---

## 3. What the master plan requires that does NOT exist yet (gap list → work queue)

**Data / splits (Phase 1)**
- `data/splits/clearharm_doublespeak_v1.json` **does not exist**; no `data/splits/` dir. No locked hash-stable train/test registry (splits today are inline `dev`/`heldout` fields).
- ClearHarm has **no real validation split** (validation parquet = empty stubs; only 179 train rows in `clearharm_179.csv`, cols: `instruction, category, clearharm_native_target, clf_label`; rep40 config = 7160 dup rows).
- No mapping ClearHarm-179 → Doublespeak single-token codeword/concept pairs. **Design decision needed (see §7).**

**Infrastructure (Phase 3+)**
- `LayerPatch` edits **resid_post only**. Plan Phase 3 needs **4 locations** (resid_pre, attn_out, mlp_out, resid_post). resid_pre/attn_out/mlp_out patch + donor-capture must be added (SubmodulePatch covers attn/mlp *replace*; no unified 4-location capture+patch+necessity helper).
- No **necessity convenience** (mean/corrupted/zero donor) helper; caller composes via project_out.
- No unified per-layer artifact co-locating `concept_direction[L]`, `refusal_direction[L]`, `doublespeak_signature[L]` (split across 2 scripts / 2 output trees, different capture paths).
- `AttentionKnockout` has **no synthetic test** (Phase-4 correctness unverified by CI).
- No attention-edge **sufficiency/insertion** primitive (Phase 4.3 leans on DemoStateSwap).
- No **Q/K/V/pattern** head patching (50 patches z only); no per-head z-ADD (Phase 9 head granularity).
- `50_path_patching` is **head→head only** — Phase 7 needs sender-head → **every downstream receiver MLP**.
- Sweep harness only composes `LayerPatch` tuples; attention/head hooks not driveable through the cheap forward-only sweep.

**Coverage / stats (all phases)**
- No `configs/manifests/*.json` enumerating cells. No `scripts/validate_experiment_coverage.py`.
- Existing scans are **coarse** (L step 2; head subsets; 49 OOMs at 14B) and **single-pair, single-seed, n≈24-30** — below the plan's ≥20/≥20 locked-split + Holm bar.
- TROPT package **not installed** (only the skill); `llm-attacks` present but not wired in.

---

## 4. Provenance / run registry
- `EXPERIMENT_REGISTRY.csv`: 45 runs (37 COMPLETE, 5 RUNNING, 1 PARTIAL, 1 QUEUED, 1 FAILED); cols incl. run_id, git_commit, seed, output_dir, key_metric, value.
- 285 dirs under `outputs/`. Key: `outputs/pair_interv_*_694691` (S2 forced_choice), `outputs/mlp_atp_{bomb,grenade,chlorine}`, `outputs/patchsweep_llama_bomb`, `outputs/attn_retrieval_*_699219`, `outputs/gcg/*`, `outputs/stage_gcg_full` (refusal dirs + AdvBench 520 manifest), `pair_directions_*` (d_Direct/d_DS).
- SLURM jobs cited across findings: 689972/689975/690096-7 (behavioral), 692xxx (multi-seed), 693571/694417/694691/694706 (causal core / transplant), 699219/699294 (attention). Env/model audit: `ENV_AUDIT.md`, `STAGE0_INTEGRITY_REPORT.md`, `RESULTS_FREEZE_AUDIT.md`.

## 4b. Presentation values — reproducible vs not
- **Reproducible from artifacts:** all §2 numbers above have committed output dirs/jobs. Attention 3.5×, MLP-AtP pearson, IE_state≈0/DE_context≈99% (694691), KV ~9% (694691), TOCTOU timing, GCG temporal 0.0/refusal 0.615.
- **NOT reproducible / withdrawn:** `d_Direct=+0.971` (disk = +0.028); "DS below its random control" sufficiency claim (no random arm was ever run — RESULTS_FREEZE_AUDIT); Patchscope confound-free readout at R=28 (fails positive control, dropped); Qwen3 per-layer circuit maps (metric reverses, m_clean=−9.95 — uninterpretable).

---

## 5. Known bugs / footguns / caveats (carry into every new script)
1. **EAGER mandatory for knockouts.** Under SDPA/flash the 4-D additive mask is silently ignored → knockout no-ops. Load eager for 09/10/36/attention-edge work; assert 4-D mask + `mask_ok`. bf16+SDPA remains the house standard for *non-mask* work.
2. **`LayerPatch` = resid_post after block `layer_idx`.** Use `patch_layer_sweep(readout_layer)` (not `range(num_layers)`) or you reintroduce the C1/C3 self-overwrite floor. During KV-cache decode (seq==1) fixed prompt positions are silently skipped (effect only at prefill).
3. **AttentionKnockout self-block → NaN:** if all causal keys for a query are blocked, softmax of all −inf = NaN. Always leave ≥1 unblocked key (self/BOS). Head-dim expansion assumes HF emits head-dim-1 masks.
4. **`d_DS` degenerate at resid_pre L0** (cos NaN by design) — use nan-safe reductions.
5. **Forced-choice/cloze readouts gated** on a positive control (clean Direct must force concept, max>0.1); no DS/Neutral cell recorded if the gate fails. Patchscope needs a **layer-scanned, positive-control-gated** readout (44's R=28 fixed-layer readout is unusable).
6. **AtP trustworthy only if** min(pearson,spearman) ≥ 0.7 (48/51) / recon rel_err ≤ 0.15 (50); else fall back to true deltas. AtP is a **ranking diagnostic, not a causal claim** (matches plan).
7. **Count-matching inconsistency:** 36 `random_matched` blocks fewer keys than `demos_all` (excludes codewords); use recorded `n_blocked`, not nominal set. 09 adds `rand_demos_matched`.
8. **Multi-token / tokenizer:** `find_word_occurrences` suffix fallback returns a *partial* span (label `suffix:`) — fine for `codeword_last`, risky for full-span consumers. Prefer single-token codewords (plan mandate).
9. **GCG:** always `--no-filter-cand` (BPE optimization dies silently otherwise). Optimized suffix strings live in `gcg_suffixes_used.json` (adversarial token soup) — keep out of scalar summaries.
10. **Boundary confounds:** demo/request boundary uses `ds_common.request_start_token`; Llama chat template ends with `\n\n` (needed a `rfind('\n\n')` fallback; check `n_request_boundary_unlocated`). Pre-fix layerwise artifacts conflate block-demos with block-request.

---

## 6. Engineering-test status (Phase "add tests" requirement)
Already covered by `tests/`: LayerPatch locality/propagation/α=0-noop/project_out/hook-removal; localization all-occurrence/multi-token/template round-trip/request-boundary; ZHead self-swap==baseline; projectout/alladd α=0 no-op; DemoStateSwap self-swap exact; AtP==true-delta; path-patch recon; kv/transplant.
**Missing tests (to add):** AttentionKnockout edge-only + row-renormalization + eager-guard; 4-location LayerPatch (once added); no-op reproduces baseline **logits** on the real model; train/test ID non-overlap; coverage n≥20; codeword-occurrence completeness on the ClearHarm split.

---

## 7. Decisions surfaced for Omer (do not block Phase 0/1 scaffolding)
1. **ClearHarm → Doublespeak mapping.** ClearHarm = 179 free-form harmful instructions (`instruction, category, clearharm_native_target`). Doublespeak needs a **single-token concept** + **single-token codeword** + demonstrations per example. Proposed default (see split contract): derive one single-token target concept per item (from `clearharm_native_target`/`category`, filter to single-token; separately bucket multi-token), assign single-token novel codewords, **cluster the 40+ examples by `category`** so paraphrases/same-intent stay in one split, then split categories into ≥20 train / ≥20 test. Confirm or override.
2. **Primary readout during exhaustive scans.** Forced-choice harmful−benign logit-diff (cheap, gated) for the L×head sweeps; full StrongREJECT generation only on decisive causal cells. Matches plan; confirm.
3. **Honest-prior scope.** Given the recorded negatives (d_DS inert, temporal objective backfires, mechanism distributed), Phases 10–11 are at high risk of reproducing nulls. Plan explicitly wants nulls reported. The genuinely novel, positive-EV contributions are: **ClearHarm generalization**, **locked-split + Holm rigor**, **full 4-location + all-layer/all-head coverage**, and the **surgical per-head edge knockout** (N7-M's flagged next step). Proceeding on that basis unless redirected.

---

## 8. Verdict
Infrastructure is ~80% reusable; the plan is a **rigor + coverage + ClearHarm-generalization + surgical-knockout** upgrade of an existing, well-documented hypothesis — not a rewrite. **Gate 1 (reproduction)** is largely satisfiable from committed artifacts (§4b). Immediate work queue: (a) lock ClearHarm split (Phase 1), (b) extend `LayerPatch` to 4 locations + add AttentionKnockout test, (c) write coverage manifests + validators, (d) smoke-test the three exhaustive sweeps on 2 examples/2 layers/2 heads.
