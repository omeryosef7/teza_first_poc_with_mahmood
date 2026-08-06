# P9 — GCG / MAC Gate 7: launch readiness audit

**Scope:** plan `reports/CAUSAL_CONTINUATION_MASTER_PLAN.md` §P9.0–P9.3 (lines 778–862).
**Audit date:** 2026-08-06. **Auditor:** code/infrastructure inventory only — no job launched, no script
modified, no generation or suffix text read.
**Headline:** the P9.0 optimizer fixes are real and committed, the dataset is genuinely frozen, and
**7 of 16 arms have all their scientific inputs on disk — but 0 of 16 are launchable as-is**, because the
launch wrapper cannot express a refusal-direction objective, cannot vary the seed, the evaluator still
hardcodes 3 Qwen arms, and arm 7's frozen direction is the one P7 just failed.

---

## 1. What P9.0 actually fixed, and whether it is committed

All optimizer work landed in **one commit, `ef59f732`** ("P10 decode-safe harness + P7 direction-validation
harness + P9 Gate-7 manifest", 2026-08-05), touching `poc_stage_gcg_early/{config,gcg_optimizer,
run_optimization,model_adapter,build_reference_cache}.py`. Working tree is clean for all of these files
(`git status` shows only logs/outputs dirty). Tests pass today:
`pytest poc_stage_gcg_early/tests/test_repr_in_selection.py tests/test_suffix_placement.py` → **33 passed,
3 skipped** (re-run by this audit, 57 s, CPU only).

| P9.0 item | status | evidence |
|---|---|---|
| **1. selection bug** — `repr_loss` must enter candidate selection | ✅ **FIXED, committed** | `gcg_optimizer.py:291–460` `_evaluate_candidates` now takes `reference_hs`, `repr_layers/positions`, `refusal_direction`, runs the candidate batch with `output_hidden_states=True` in sub-batches (`repr_selection_sub_batch`, default 8) and feeds `composite_loss`/`refusal_direction_loss`. Auto-enable logic `gcg_optimizer.py:740–760`. Tests A1–A4, B1–B2, E1–E2 in `tests/test_repr_in_selection.py` prove repr_loss was identically 0 pre-fix, is non-zero and candidate-varying post-fix, sub-batching is loss-invariant, and task-only arms stay byte-identical. |
| **2. provenance bug** — `repr_layers` / `reference_cache_id` / `objective_name` in CONFIG.json + `config_hash()` | ✅ **FIXED, committed** | Fields on `ObjectiveWeights` `config.py:120–148`; content hash helper `config.py:22` `reference_cache_content_id`; hash logic `config.py:175–200` with `_HASH_BACKCOMPAT_DEFAULTS` (`config.py:143`) so pre-P9.0 runs keep their hash and stay resumable. Tests C1–C6 including `test_c2_real_run_hashes_still_reproduce`. |
| **3. `llama` model family** | ◐ **3 of 4 files done** | Added: `run_optimization.py:104–105` (CLI choice) + `:332–345` (loader), `build_reference_cache.py:53` + `:104`, `model_adapter.py:37` (`_EMBED_PATHS_BY_FAMILY["llama"]`). **NOT added** to `evaluate_cross_model_transfer.py:56–68` and `:194` — still `choices=["qwen3","gemma4"]` and `raise ValueError` for anything else. Also **`slurm_scripts/run_gcg_free_generation.slurm:104–107`** does `if family=="qwen3": load_qwen3_model else: load_gemma4_model`, i.e. a `llama` run would silently load **Gemma**. |
| **4. Llama+ClearHarm manifest, joined on instruction text** | ✅ **BUILT and committed** | `build_clearharm_gcg_manifest.py` (317 lines) → `data/gcg/clearharm_llama/{clearharm_llama_direct,clearharm_llama_doublespeak}.jsonl` (86 rows each, 44 train / 42 test, `join_tier=exact` ×86, `safe_target_prefix` non-empty ×86, `model=llama`, `enable_thinking=False`), `JOIN_REPORT.json`, `.sha256` sidecars, `RUNMETA.json`, `DONE.json`. sha256 values match the manifest spec. |
| **5. objective registry** (`--objective NAME`) | ❌ **NOT done** | There is no `--objective` flag and no registry object anywhere in the repo. What exists is a *label*: `--objective-name` (`run_optimization.py:188`) plus auto-derivation from the active λ's (`run_optimization.py:79–99`). Objectives are still assembled from ad-hoc λ/cache/path flag combinations. |
| **6. generalize the ASR evaluator** | ❌ **NOT done** | `25_eval_gcg_asr.py` still hardcodes exactly three arms (`:101–102` `{"none","baseline","temporal"}`), *requires* `--temporal-dir` and `--baseline-dir` (`:56–57`), requires a curated **screening matrix** for goal extraction (`:55`, `:94–99`) which the ClearHarm/Llama manifests do not have, and defaults to `Qwen/Qwen3-14B` (`:58`). It also reports `asr` and `refusal_rate` but **no `empty_rate`** in the summary (`:126–131`) — the EMPTY label exists only in `gcg_asr_raw.jsonl`. |
| **7. seed driver** (42/43/44) | ❌ **NOT done** | `--seed` exists on the optimizer (`run_optimization.py:114`, default 42) and is in `config_hash` via `GCGHyperparams.seed` (`config.py:71`), but **`slurm/run_gcg_optimize.sh` has no `DSSEED`** — unlike every other wrapper in `slurm/` (`run_behav_write.sh:66`, `run_jacobian.sh:93`, `run_refusal_validate.sh:101`, …). No multi-seed driver script exists. |

**Consequence of item 1 that must survive into the paper:** every prior "the mechanism-derived objective does
not help" statement in this project was produced with the objective **disabled in candidate selection**.
Those are not evidence about the objective; they are evidence about task-loss GCG.

---

## 2. The 16 arms — inputs on disk, and GO / NO-GO

Manifest: `configs/manifests/phase9_gcg_mac_matrix.json` (spec_version 1, `status: "FROZEN-SPEC / NOT
LAUNCHED"`, created 2026-08-05). **No P9 run directory exists** (`outputs/` contains `phase9_dose_*` from an
unrelated phase, and `outputs/gcg/` contains only Qwen3 Track-B runs). Confirmed present and reusable for
every arm: both 86-row manifests, the split file, the local HF cache for `meta-llama/Llama-3.1-8B-Instruct`
(16 GB, so `HF_HUB_OFFLINE=1` is safe), and a non-empty `OPENAI_API_KEY` in `.env` for the StrongREJECT judge.

| # | arm | inputs on disk? | verdict |
|---|---|---|---|
| 1 | no suffix, direct | ✅ direct manifest (86 rows) | **CONDITIONAL GO** — data complete; needs a P9 eval/judge driver (§1 item 6) |
| 2 | no suffix, doublespeak | ✅ doublespeak manifest | **CONDITIONAL GO** — same |
| 3 | vanilla GCG, direct | ✅ manifest + targets; λ=0 path needs no cache | **CONDITIONAL GO** — optimization launchable via `slurm/run_gcg_optimize.sh` with `DSFAMILY=llama`/`DSMODEL`/`DSMANIFEST` overrides, but **seed pinned to 42** and no eval driver |
| 4 | vanilla GCG, doublespeak | ✅ same | **CONDITIONAL GO** — same |
| 5 | GCG, harmful-target logits only | ❌ **no distinct target exists** | **NO-GO** — the join supplies exactly one affirmative target per item and it *is* the harmful target, so as specified arm 5 is bit-identical to arm 4. Needs either a codeword-surface target for the DS condition or a longer harmful-continuation target. Nothing on disk provides either; none was invented. |
| 6 | GCG, concept-readout objective | ❌ **reference cache absent** | **NO-GO** — `inputs.reference_cache_direct.exists=false` and no llama cache dir exists under `outputs/gcg/` (only `cache_qwen3_{direct,mixed,neutral}`). Also the concept-readout position is not frozen. Build cost is small (§5). ⚠ `slurm/run_gcg_refcache.sh:43` defaults `DSLAYERS=0,5,…,35`, **invalid for a 32-layer Llama** — must be overridden. |
| 7 | **GCG, refusal-suppression (candidate A)** | ✅ `outputs/refusal_alllayers/refusal_direction_llama_L22.pt` (torch.Size([4096]) fp32, `weights_only=True` loadable) | **NO-GO today — 4 concrete blockers, all cheap to clear** (see §2a). This is the arm the plan names first-to-run. |
| 8 | GCG, concept-up + refusal-down (E) | ❌ inherits arm 6's cache; **no output-degeneration penalty term** | **NO-GO** — `objectives.py` has `fluency_loss` (`:398`, experimental, needs an n-gram frequency table) but nothing implementing the specified degeneration penalty. |
| 9 | GCG, Jacobian concept | ❌ **P6 never run**; no `jacobian_*` objective | **NO-GO (gated, correctly)** — `scripts/phase6_jacobian_readout.py` exists but there is no P6 output directory, and `poc_stage_gcg_early/objectives.py` has no Jacobian loss. |
| 10 | GCG, Jacobian refusal | ❌ same | **NO-GO (gated, correctly)** |
| 11 | MAC/TROPT concept | ◐ TROPT v0.1.1 installed (`TROPT/`, own `.venv`, not importable from `poc_stage2`) but no logit-difference/concept loss | **NO-GO** — needs a new `Loss` and cross-stack tokenization verification. |
| 12 | MAC/TROPT refusal | ✅ **more ready than the manifest records** | **NO-GO today, but re-scope:** the manifest says "TROPT v0.1.1 has no representation/direction loss". That is **wrong** — `TROPT/tropt/loss/losses.py:429` `HiddenStateBasedLoss` and **`:444` `SteeringActivationLoss`** exist, with `steer_away=True` documented verbatim as *"refusal direction suppression combined with GCG"*, `targeted_layers`, `slc_name` position selection and `do_cosine_sim`. Arm 12 needs **configuration + tokenization verification**, not a new subclass. |
| 13 | MAC/TROPT combined | ◐ needs arm 11's loss | **NO-GO** |
| 14 | GCG attention/carry | ❌ gated on P3–P6; no `attention_carry` objective in `objectives.py` | **NO-GO (gated, correctly)** |
| 15 | random suffix control | ✅ manifest; ❌ **no random-suffix generator** | **NO-GO as specified** — the only built-in "random" baseline is `evaluate_optimized_suffixes.py:197` `random_suffix_ids = [220]*16`, i.e. **16 identical space tokens**, which is a padding control, not a length-matched random suffix. Needs a seeded random-token sampler. |
| 16 | transfer train→test | ✅ test split (42 rows) present | **NO-GO until a winner exists** — depends on the frozen winning suffix string from an optimizing arm; strictly sequential after arms 3/4/7. |

**Count check:** the 7 arms the progress log calls "launchable" are exactly the 7 with `status:"ready"` in the
manifest — 1, 2, 3, 4, 7, 15, 16. This audit confirms their *scientific inputs* exist, and finds that 15 and
16 are not actually runnable (missing generator / missing dependency), and that 7 is blocked (below). The
honest count is **4 arms (1, 2, 3, 4) that could run today once an eval driver exists, and 0 that can run
end-to-end today**.

### 2a. Arm 7 — the four blockers (all fixable without new science)

1. **The wrapper cannot express the objective.** `slurm/run_gcg_optimize.sh:52–58` only builds `REPR_ARGS`
   when `DSLAMBDA` (= `--lambda-repr`) > 0, and then *requires* `DSCACHEDIR`. There is **no env path** to
   `--lambda-refusal-dir`, `--refusal-dir-path`, `--refusal-dir-layer` or `--seed`. Arm 7 uses
   `lambda_repr = 0` and a refusal direction, so today the wrapper physically cannot launch it.
2. **Off-by-one on the layer index — would silently optimize the wrong layer.** The direction builder writes
   `hs[L+1]` (`build_refusal_direction_llama.py:77`) and its sidecar records `"layer": 22,
   "hidden_states_index": 23`. The optimizer indexes `hidden_states[refusal_dir_layer]` **directly**
   (`gcg_optimizer.py:279–287` `_slice_hidden_states`, consumed at `objectives.py:213`). To read the L22
   axis, arm 7 must pass `--refusal-dir-layer 23`. The manifest's `objective_config.refusal_dir_layer` is
   **22**, which would read the post-L21 residual instead. Nothing in the code catches this.
3. **λ_refusal is not frozen.** `objective_config.lambda_refusal_dir` literally reads *"to be fixed at freeze
   time from the P8.1 alpha calibration"*. P9.1 freeze item 5 is therefore not satisfied for the first-to-run
   arm.
4. **P7 just failed this exact direction.** `reports/P7_REFUSAL_DIRECTION_VALIDATION.md` (complete, all 32
   layers, runs 720463 / 721957 / 722611): the **`existing` family — i.e. the shipped
   `outputs/refusal_alllayers/*.pt`, which is arm 7's input — FAILS the induce arm at L22 (+0.000 against
   +1.000 of headroom)**; only the ClearHarm refit passes at L22, and weakly (+0.100 induce = 1 item of 10).
   **L18 is the only layer carrying a published claim that validates in both families** (+0.600/+1.000 and
   +0.900/+0.800). Recommendation: repoint arm 7 to **L18** (`outputs/refusal_alllayers/
   refusal_direction_llama_L18.pt`, on disk) or to the ClearHarm refit in
   `outputs/refval_clearharm_20260806_054117_722611/refusal_direction_clearharm_L18.pt`, and record the
   change in the manifest before launch. Optimizing against an axis that induces nothing is a pre-registered
   way to produce an uninterpretable null.

**Two further measurement caveats for arm 7** (declare, do not silently absorb):
`refusal_direction_loss` normalizes the hidden state (`objectives.py:220`, cosine), while
`scripts/phase_refusal_projection.py` reports a raw dot product with a unit direction — success criterion 5
would compare two different quantities unless one is converted. And the directions were built under
`add_special_tokens=True` (the known double-BOS convention) while the GCG stack tokenizes with
`add_special_tokens=False` (`model_adapter.py:150–157`), so direction and optimizer live in slightly
different token contexts.

---

## 3. The two known GCG hazards, in the current code

**(a) `filter_cand=True` silently kills all optimization with BPE tokenizers → `--no-filter-cand` required.**
**HANDLED ON THE LAUNCH PATH, NOT ENFORCED IN CODE.**
- Default is still the hazardous value: `poc_stage_gcg_early/config.py:75` `filter_cand: bool = True`.
- Opt-out flag: `run_optimization.py:119` `--no-filter-cand`, applied at `run_optimization.py:231`
  (`filter_cand=not args.no_filter_cand`).
- Consumed at `gcg_optimizer.py:834–837` → `get_filtered_cands` (`suffix_token_manager.py:336, 357, 366,
  370`).
- The wrapper passes it unconditionally: **`slurm/run_gcg_optimize.sh:66`**.
- The manifest freezes it: `shared_hyperparams.filter_cand = false`, and `_notes` records
  *"--no-filter-cand always"* as binding.
- **Residual risk:** any invocation that does not go through that one wrapper line reverts to the hazard
  silently. There is no assertion, no warning, and no CONFIG.json post-check.

**(b) suffix optimized in the ASSISTANT turn but evaluated in the USER turn.**
**HANDLED, WITH TEST COVERAGE.**
- `config.py:82` `suffix_placement: str = "user"` (comment: FIXED 2026-07-19; included in `config_hash` so v1
  and v2 can never cross-resume).
- CLI default `run_optimization.py:115` (`choices=["user","assistant"]`, legacy value retained only for exact
  v1 replay), applied at `run_optimization.py:232`.
- Threaded into every span build: `suffix_token_manager.py:132` signature, user branch at `:201`, legacy
  branch at `:176`, unknown-value guard at `:260`; call sites `gcg_optimizer.py:628, 653, 685, 714, 797, 848,
  886, 937, 1005, 1042, 1077, 1117`.
- The user branch hand-assembles `header + suffix + trailer + target` and then **asserts byte-equality with
  eval's exact tokenization of the whole prompt**.
- Evaluation side puts the suffix in the user turn too: `evaluate_optimized_suffixes.py:92`
  (`apply_chat_template(user_content)`) and `25_eval_gcg_asr.py:113`.
- Tests: `tests/test_suffix_placement.py:47` `test_user_placement_matches_eval`, `:93`
  `test_legacy_assistant_placement_reproduces_bug` — both passing today.
- Manifest freezes `suffix_placement = "user"` and `_notes` records it as binding on every arm.

---

## 4. P9.3 pre-registered success criteria — can the planned arms test them?

Quoted verbatim from the plan (§P9.3, lines 851–858):

> 1. Held-out ASR improves over compute-matched vanilla GCG **and** over no-suffix DS, by more than the P1
>    drift envelope. 2. `refusal_rate` falls **without** `empty_rate` rising. 3. Survives ≥ 3 seeds.
>    4. Transfers to locked test. 5. The mechanism metric moves in the intended direction. 6. A
>    random-direction objective does not match it. 7. Harmful content stays redacted.

| # | testable by the planned arms? | what is missing |
|---|---|---|
| 1 | **Partly** | Comparators exist (arms 3/4 vanilla, arm 2 no-suffix DS). But **P1 has never been run** (`CONTINUATION_PROGRESS.md` status table: "needs GPU"), so the *drift envelope* is undefined. Interim substitutes from the plan itself: `ds_base` test ASR spans 0.286–0.381 across four existing runs (~10 pp), and P1's exit rule already says *"any later arm claiming a sub-0.10 ASR improvement is declared uninterpretable"*. With n = 42 locked-test items, one item = 2.4 pp, so a 10-pp bar is ~4 items — pre-register the test (paired McNemar on items) or the criterion is decorative. |
| 2 | **Not as currently instrumented** | `25_eval_gcg_asr.py:126–131` reports `asr` and `refusal_rate` but no `empty_rate`; EMPTY exists only as a row label in `gcg_asr_raw.jsonl` (`:120`). Derivable, but the P9 evaluator must emit it as a first-class column. |
| 3 | **No** | No seed passthrough in the wrapper and no seed driver (§1 item 7). P9.2's own strategy is 1 seed for the screen, 3 seeds only for the top-3 — so criterion 3 can only ever be met in the *second* stage, which must be stated in the pre-registration. |
| 4 | **Yes, conditionally** | Arm 16 covers it and the test split (42 rows) is on disk and untouched. It cannot start until an optimizing arm wins on train. |
| 5 | **Partly** | Needs a per-arm readout of the refusal projection under the optimized suffix. `scripts/phase_refusal_projection.py` exists but is not wired to GCG run dirs, and its metric is a raw projection vs the optimizer's cosine (§2a). Glue + a unit convention are required. |
| 6 | **No — not one of the 16 arms** | The manifest itself concedes this: arm 15's note says the norm-matched random-**direction** control *"is a separate re-run of arm 7"*. There is also no generator for a norm-matched random direction `.pt`, and `--refusal-dir-path` only accepts a file. **An arm 17 must be added to the frozen manifest before launch**, otherwise criterion 6 is untestable by construction. The same is true of the doublespeak-signature negative control that P9.2's budget line assumes. |
| 7 | **Yes** | Existing convention already complies: `25_eval_gcg_asr.py:124–137` keeps the summary scalar-only, writes suffix strings to a separately-named artifact and stores only category labels per row; no generations are persisted. |

**Bottom line on P9.1's freeze (7 items):** (1) dataset/prompts ✅ (sha256-pinned), (2) judge ✅ by reference
but ❌ no P9 driver, (3) suffix budget ✅ (16 tokens / 200 steps / bs 64 / topk 256), (4) compute budget ✅
stated, (5) objective definitions ❌ (arm 7's λ unfixed; 4 of 11 objectives have no implementation),
(6) train/test split ✅ 44/42, (7) manifest file ✅. **5 of 7 frozen.**

---

## 5. Budget: P9.2 as planned vs. what the launchable subset actually costs

P9.2 as written: *"universal suffix, 44 train tasks, 200 steps, bs = 64 → 563,200 candidate forwards ≈ 1.60
GPU-h per arm-seed on one L40S. Strategy: 16 arms × 1 seed as a screen (≈ 33 GPU-h, ~6 h wall at the
6-parallel cap), then top-3 + naive baseline + signature control at 3 seeds (≈ 55 GPU-h total) rather than
98.6 for the full 3-seed matrix."* The manifest reconciles this as 12 optimizing arms × 1.6 = **19.2 GPU-h of
optimization**, with the remaining ≈ 13.8 GPU-h covering generation + judging across all 16 arms
(≈ 0.86 GPU-h per arm).

| item | plan (16 arms) | the 7 "ready" arms | note |
|---|---|---|---|
| optimizing arms in the set | 12 | **3** (arms 3, 4, 7) | arms 1, 2, 15, 16 do no optimization |
| optimization, 1 seed | 19.2 GPU-h | **4.8 GPU-h** | upper bound; the 1.6 h anchor was measured on **Qwen3-14B**, and P9 runs **Llama-3.1-8B**, so expect ≈ 0.8–1.2 h/arm-seed → realistically **2.4–3.6 GPU-h** |
| generation + judging, 1 seed | ≈ 13.8 GPU-h | **≈ 6 GPU-h** at the plan's 0.86/arm | 86 prompts × 200 new tokens on an 8B is minutes, so the true figure is likely < 1.5 GPU-h total |
| **screen total (seed 42)** | **≈ 33 GPU-h** | **≈ 10.8 GPU-h upper bound, ~5 GPU-h realistic** | ≈ **1/3 of the planned screen**, and it buys 7 of 16 cells |
| wall time | ~6 h at the 6-parallel cap | **~2 h** — the 3 optimizing arms fit one parallel wave (wrapper `--time=06:00:00` is ample) | |
| 3-seed follow-up | ≈ 55 GPU-h total | ≈ **28 GPU-h** for the seed-sensitive subset (arms 3, 4, 7, 15 × 3 seeds; arms 1–2 are seed-invariant, arm 16 replays a frozen string) | |
| judge (non-GPU) | — | ≈ 558 judged completions per seed (6 arms × 86 + 42), ≈ 1,700 for the 3-seed follow-up | `OPENAI_API_KEY` is present in `.env` |

**Verdict on budget:** the 7-arm subset is **not budget-constrained** — it is roughly a third of the planned
screen and fits one 6-parallel wave. The constraint is entirely **plumbing**: no wrapper path for the refusal
objective, no seed passthrough, no P9 evaluator, no random-suffix generator, and no random-direction control
arm.

---

## 6. Minimal path to a real GO (smallest change first, no new science)

1. **Add env passthrough to the existing wrapper `slurm/run_gcg_optimize.sh`** — `DSSEED`, `DSREFLAMBDA`,
   `DSREFPT`, `DSREFLAYER`, `DSBATCH`, `DSOBJNAME` — following the `DSSEED` pattern already used by every
   other wrapper in `slurm/`. This alone converts arms 3, 4 and 7 from unlaunchable to launchable, at 3 seeds.
   *Prefer this over a new P9 runner script.*
2. **Fix arm 7's frozen inputs in the manifest, before launch:** `refusal_dir_layer 22 → 23` (hidden-states
   index), repoint the path to the **L18** direction per P7, and fix λ from the P8.1 calibration.
3. **Generalize `25_eval_gcg_asr.py` to N arms** (arm-dir list + `--goal-field` instead of the curated
   screening matrix, `--model-family llama`, and an `empty_rate` column). This is P9.0 item 6 and it gates
   *every* arm, including the four "data-complete" ones.
4. **Add arm 17 (norm-matched random direction)** and the doublespeak-signature negative control to the frozen
   manifest — criteria 6 and the P9.2 budget line already assume they exist.
5. Then, and only then: launch **arm 7 first** (as the plan directs), with arms 2, 3, 4 as its comparators.

Deferred, larger work: the reference cache + frozen concept position (arms 6/8), a distinct target for arm 5,
P6 (arms 9/10), the TROPT `SteeringActivationLoss` wiring + tokenization audit (arm 12, cheaper than
recorded), and a concept/logit-difference loss for arms 11/13.

**Naming reminder (manifest `_notes`):** every P9 run directory must be named
`phase9_gcg_mac_matrix_arm<NN>_<slug>_seed<SEED>` for `scripts/validate_all_outputs.py` to resolve the
manifest by the shorter-prefix rule.

---

*No SLURM job was submitted, no file outside this report was created or modified, and no prompt, generation
or suffix text was read or reproduced during this audit.*
