# HERETIC × Causal-Semantic-Installation (CSI) — authoritative plan & append-only progress log

**Created:** 2026-10-01. **Author:** Omer Yosef (+ Claude Opus 4.8 session). **Branch:**
`behavioral-causality-sprint`. **Status:** LIVE sprint log. **Append-only** — never rewrite history to
make a result look cleaner. Negative results, nulls, bugs, corrections, abandoned hypotheses and
contradictions are first-class results and stay in the record with the reason.

This file is the single source of truth for the Heretic-integration sprint. It inherits, and binds itself
to, the discipline of the predecessor CSI sprint (`SUMMARY_2026-09-02_TO_09-26.md`,
`reports/DCS_CSI_CLAIM_TABLE.md`, `reports/DCS_CSI_RESULTS_DRAFT.md`, and the CSI sprint log
`external_md/DCS_CAUSAL_SEMANTIC_INSTALLATION_MECHANISM_AND_REPLICATION_PLAN_AND_PROGRESS_20260915.md`).

---

## 0. PINS, ENVIRONMENT, PROVENANCE (fill-once header)

| item | value |
|---|---|
| **Heretic commit SHA (pinned)** | `662e4ba27ecaf8878b0938c184a78f75a9116f82` (2026-10-01, "feat: modifier plugins + ARA (#446)") |
| **Heretic clone path** | `external_repos/heretic/` (AGPL-3.0; provenance/attribution preserved, see §13) |
| **Our repo HEAD at sprint start** | `152c3adf` (DCS-CSI-580) on `behavioral-causality-sprint` |
| **Primary model** | `meta-llama/Llama-3.1-8B-Instruct`, revision `0e9e39f2…` (as pinned by CSI) |
| **dtype / attention** | **bfloat16**, **eager** attention (CSI constant — do NOT change without an explicit experiment) |
| **GPU constraint** | Native-bf16 GPUs only (**RTX 3090 / L40S / a5000** acceptable). **V100 PROHIBITED** (emulated bf16 breaks norm-matched arms — CSI S-037/S-119). H100/H200/B200 are native-bf16 and acceptable but verify numerics vs 3090 before trusting cross-hardware comparisons. |
| **conda env** | `poc_stage2` (miniconda at `/home/sharifm/students/omeryosef/miniconda3`). `.env` sourced for API keys. |
| **SLURM account** | `gpu-research`. Partitions: `killable` (GPU), `cpu-killable` (heavy CPU analysis). |
| **SLURM rules** | no job deps; ≤ 6 concurrent independent GPU jobs; avoid simultaneous cold NFS model loads (batch arms in one allocation after one load); a COMPLETED `sacct` is NOT success — validate log trailer + artifacts + row count + explicit `DONE` marker. |
| **Shared tree** | 4+ peer Claude sessions share this tree AND the git index. Commit ONLY path-scoped: `git commit -- <paths>`. Never `git add -A`, never `git stash pop`, never two commits in flight. |
| **git push** | credential-blocked for the predecessor sprint (expired PAT). Commit locally; attempt push; if it fails, document and continue (do NOT stall research). |

### 0.1 Frozen data populations
- **Prompt bank:** `data/boombness_prompts/boombness_prompt_bank_ts116_<codeword>_<concept>.jsonl`
  (+ `_meta.json`). Pools: `data/boombness_prompts/demo_pools_116dom.json` (sha16 `976aa2b0b617118d`).
- **Domain split:** `data/boombness_prompts/dcs_ts116_domain_split.json`, schema `dcs_ts_domain_split/1`,
  **seed `202609061`**, **unit = domain**, 70 train / 23 validation / 23 test (3 whole-population domains
  excluded → **67 effective train**). Enforced **per-row** by the readers.
- **TEST is SPENT** (read to completion 2026-09-08, selection-contaminated — AM-39). **Never used for any
  selection, and never as "confirmation" for a claim whose method touched it.** For genuinely fresh
  confirmation we need untouched codewords (see P6) — not the TEST split.
- **Codewords:** `basket` (original) and `button`. **Never pooled** — each is a separate observation.
  25/40 further codewords survive the PR-CSI-008 lexical screen (route to scaling, P5/P6).
- **Concept:** `bomb` (the only concept that installs; knife/gun do not — R-116).

### 0.2 Verdict vocabulary (inherited, used strictly, never widened after seeing a result)
CONFIRMED · NEGATIVE (failed **with power**) · CANNOT ANSWER (design can't resolve; incl. floor-limited &
structurally-blocked) · FLOOR-LIMITED (control family too small for any outcome to reach α=0.05; smallest
attainable rank-p with *n* controls is 1/(*n*+1)) · VOID (run did not execute its frozen design) ·
WITHDRAWN · MEASURED/EXPLORATORY (real numbers, not preregistered, not quotable as a result) · INHERITED.

---

## 1. SCIENTIFIC MOTIVATION

The predecessor CSI sprint established, on Llama-3.1-8B-Instruct, a **controlled codeword dissociation**:
a **rank-1 direction suffices** to rescue semantic installation of the concept for the codeword `basket`
(rank 1/47, p=0.0213, both splits — at the floor, no margin) but is a **certified NEGATIVE for `button`**
(rank 36/47 train, well-powered). Crucially, the **whole-state rescue works for `button`** (recovery
fraction 0.341 train / 0.328 val) — so the site *is* causal; the rank-1 **axis** just isn't a sufficient
carrier there. The dissociation is **not** explained by layer choice (exonerated by a codeword×layer 2×2),
headroom, or population; only C1 ("basket has a better rank-1 probe", +12% LOO ρ, **unquantified**) survives.

**This is exactly the gap Heretic/ARA addresses.** Rank-1 failure does NOT imply non-causality. The natural
next question is **dimensionality / operator structure**: *can the causal semantic-installation mechanism be
distilled into a compact weight-level operator (ΔW = BA) of some effective rank, and does the required rank /
location explain the basket-vs-button dissociation?* We exploit Heretic's Arbitrary-Rank Ablation (ARA),
module-I/O optimization, LoRA-style weight edits, external Modifier/Scorer plugin API, and Optuna
multi-objective search as a **mechanistic-intervention framework** — NOT to "decensor" a model.

### 1.1 Inherited picture that MUST be preserved (do not rediscover or overstate)
- Doublespeak effect is **real on Llama**, **model-specific** (capable null on Qwen3-14B).
- Installed concept is highly **decodable** (probe 0.94) but decodability ≠ causality; "only bomb installs".
- The scalar "Bombness"/`d_surface` story **failed** as a general causal representation.
- installation→ASR correlation (ρ=0.396) is **TRAIN-only**; does NOT replicate held-out.
- Attention knockout removes installation and halves refusal **without** moving content-true attack success
  (powered null, DR-070).
- **Raw LLM-judge ASR overstates content-true success ~11.8× (button)** — DO NOT optimize against naive
  LLM-judge ASR.
- Whole-state rescue establishes the site carries causal information.
- rank-1: basket PASS, button NEGATIVE (matched power). NOT explained by layer alone. Codeword row (`rel-10`)
  is unusually important (46.6% of whole-state effect). ~8-head circuit `[19,17,23,6,13,2,24,28]` carries
  much of the basket knockout; 4 single heads clear (2,19,17,23); cell (L10,head2)=96.1% of head2's effect.
  Head 2 does NOT transfer to button in amplitude (D35, the one clean empirical negative); shape transfers
  (ρ=+0.817). Cell-depth structure transfers better than amplitude.
- Everything certified is **rung-1 necessity** (AM-34 ladder `arXiv:2606.08292`, NOT Pearl). No arbitrary-cell
  control exists anywhere → "cell (L,h) is the writer" is unavailable.
- **AM-48 OPEN (user call):** code certifies at rank 1 only; preregs declare rank ≤ 2 of 47 certifies. This
  sprint will **report both rank-1 and rank≤2 verdicts** and NOT silently pick one.

---

## 2. HYPOTHESES

- **H1 (primary).** The basket-vs-button dissociation partly reflects a difference in the **dimensionality /
  operator structure** required to install/restore the concept, rather than merely the existence/absence of a
  rank-1 semantic direction. → *basket saturates at low rank; button requires higher rank (or is resistant).*
- **H2.** ARA can discover a compact operator-level intervention whose learned singular subspace **overlaps
  the independently-identified causal head/layer structure** (L6/L8/L10/L11/L14/L18; heads 2,19,17,23).
- **H3.** Heretic's learned operator can be **distilled into a mechanistically interpretable low-dimensional
  subspace**, giving a better causal variable than the old `d_surface`/Bombness scalar.

All three are to be **tested, not assumed.** A null on any is a first-class result.

---

## 3. CENTRAL EXPERIMENT & PREREGISTERED OUTCOMES (the rank sweep, P2)

Run the matched position-aware operator intervention at LoRA/operator rank `{1,2,4,8,16,32,50}` (plus a
full-rank diagnostic if feasible), **independently** for basket and button. **Primary endpoint = semantic
installation / semantic rescue** (NOT raw jailbreak ASR). Core plot: *semantic rescue vs intervention rank*,
basket vs button. Also report parameter count, intervention (ΔW) norm, KL/preservation, refusal, and a
**rank-matched random control distribution** at every rank.

**Preregistered discrete outcomes (declared before any rank-sweep number exists):**
- **A.** basket low-rank, button higher-rank → H1 supported (the target result).
- **B.** both low-rank → the button rank-1 null reflected the particular axis construction, not dimensionality.
- **C.** both require multi-rank.
- **D.** button remains resistant even at high rank → H1 (dimensionality) falsified for button.
- **E.** the effect disappears under proper controls → the whole operator story is a control artifact.

All five are scientifically meaningful and will be reported as found.

---

## 4. EXPERIMENT GATES / PRIORITY ORDER

- **P0** — verify Heretic implementation & reproduce it (smoke, reset/identity, ΔW rank). (Phase A/§5-Phase-A)
- **P1** — implement correct **arbitrary-position** ARA (NOT last-token `[:, -1, :]`). (Phase C)
- **P2** — basket vs button **rank sweep** with strong rank-matched controls. (central, §3)
- **P3** — inspect/**SVD** the learned operator; distill minimal causal subspace; necessity-by-removal.
- **P4** — compare learned operator with existing **layer/head/cell** circuit (head-restricted ARA).
- **P5** — quantify the C1 "better-probe vs different-state" explanation across additional codewords.
- **P6** — scale to **fresh** codewords / confirmation data.
- **P7** — ONLY after all the above: downstream behavioral linking (expect a null; never optimize judge FPs).

If P2 yields a strong, replicated dimensionality result, invest the compute to make it thesis/paper quality
before any flashy side direction.

---

## 5. CONTROL FAMILIES, SPLIT POLICY, STOPPING & VOID RULES

**Controls (every rank-k intervention compared to rank-matched nulls):** random orthogonal rank-k subspaces;
shuffled source↔target domain pairing; norm-matched random LoRA updates; neutral-position optimization;
no-op identity adapter; source→source fit; target→target fit. Match: rank, update norm, targeted
layers/components, # optimized params, training examples. (No "rank-5 vs rank-1 null" mistake — CSI killed
exactly that.)

**Split policy (mandatory, no leakage):** TRAIN = discovery, hyperparameter/Optuna search, choosing
ranks/layers/objectives. VALIDATION used only per predeclared role. **TEST is spent — never used.** Any new
confirmatory claim needs a genuinely fresh confirmation population (fresh codewords, P6). ≥ 20 independent
examples per meaningful cell; unit of independence = domain (NOT prompt rows sharing a domain). No ASR-based
exclusion, no post-hoc filtering; attrition mechanical & declared in advance; all denominators reported.

**Power before GPU (P-rule):** before any confirmatory run, compute whether the planned control family & N
can resolve the preregistered criterion. If the minimum attainable rank/permutation p-floor > threshold,
label **CANNOT ANSWER / UNDERPOWERED** and redesign before GPU use. (46 controls → floor 0.0213.)

**VOID conditions (sprint-wide):**
1. Ran on V100 / non-native-bf16 hardware.
2. Token-position hook captured a padding token, a generated token, or `[:, -1, :]` when an explicit
   per-example position was intended.
3. source↔target pairing not domain-matched (pairing unrelated semantic domains without an explicit test).
4. any read that touched the TEST split for selection.
5. objective tuned on the final behavioral endpoint.
6. ΔW reset/identity check not performed before trusting a modified-vs-base comparison.
7. rank-k arm compared against a non-rank-matched control.
8. `sacct COMPLETED` accepted without artifact + row-count + `DONE`-marker validation.

**Stopping rules:** P2 proceeds to P3/P4 only if the rank sweep's manipulation + positive control (whole-state
or KO_FULL analogue) both fire AND an identity/no-op arm is inert. Otherwise: report feasibility, STOP.

---

## 6. METRICS / SCORERS (to be implemented as Heretic external Scorer plugins where practical)
- **SemanticInstallationScore** (PRIMARY): existing validated `y_install = sigmoid(logp_concept − logp_codeword)`
  on `query_kind=semantic_one_word`, cell C. Direction: maximize (rescue). Unit: domain.
- **OptionMassScore**: option-mass/readout endpoint with the 0.05 readout-validity floor (OPTIONMASS05).
- **RepresentationScore**: projection/probe metric using frozen analysis objects (axes in `configs/`).
- **PreservationScore**: unrelated/domain-control representation & output preservation. Direction: minimize damage.
- **KLDivergence**: reuse Heretic's implementation where appropriate.
- **RefusalScore** (SECONDARY only).
- **ContentTrueBehaviorScore**: the project's content-gated endpoint — NOT naive raw LLM-judge ASR.

Each scorer fixes: direction (min/max/none), population, aggregation unit, baseline, denominator — and its
meaning is frozen and never changes between experiments.

---

## 7. ENGINEERING PRINCIPLES
Reuse existing project code (`scripts/dcs_csi_*`, `configs/dcs_csi_axis_*`, the readers/rederive scripts) and
Heretic's interfaces. Keep upstream Heretic **isolated and pinned**; prefer its external plugin API
(`path/to/plugin.py:ClassName`); patch/fork only when the plugin API genuinely cannot support an experiment,
and then keep the patch minimal and documented. New research code under `research/heretic_csi/`. One clean
generic engine over one-script-per-condition, but never "generalize" working research code in a way that
silently changes frozen behavior. Before any scale run: unit test → tiny synthetic → small real-data smoke →
manual output inspection → scale. Offload frozen activations to CPU; don't retain graphs.

---

## 8. DELIVERABLES (end of sprint)
(1) this append-only log; (2) a concise final report answering the P0–P7 questions; (3) a machine-readable
experiment registry (config, git SHA, Heretic SHA, dataset hash, split, SLURM job, seed, params, artifact
paths, status, verdict); (4) tables/plots (rescue vs rank; preservation vs rank; basket vs button; singular
spectra; cumulative SVD rescue; layer/component search; head-restricted vs full-module; codeword
frequency/probe quality vs required rank); (5) independent verification reports for every headline;
(6) `WHAT WE CAN DEFEND` + `WHAT WE MUST NOT SAY`; (7) a short Matan/Mahmood update of only defensible results.

---

## 9. HERETIC MECHANISM AUDIT (from independent source read @ `662e4ba2`)

Full audit is in the progress log S-002. Load-bearing findings:

1. **ARA optimizes** a per-matrix low-rank PEFT-LoRA edit `W_eff = W_base + B·A` (optionally row-norm-preserved:
   `normalize(W_base+BA)·‖W_base‖_row`), fit by **L-BFGS** (`ara.py:301-326`). Objective (`ara.py:125-160`):
   `preserve_good_weight · ‖new_good − good‖² + steer_bad_weight · [ kNN(bad→good) − overcorrect · kNN(bad→orig_bad) ]`
   — a **kNN-in-activation-space** steer: keep "good" outputs fixed, pull "bad" outputs toward "good", push off
   original "bad". **No explicit refusal direction** (that's the other modifier, `Abliteration`). Maps to our
   design as **good=target, bad=source** (rename in our notes per plan §6).
2. **Modules modified:** `attn.o_proj` and `mlp.down_proj` ONLY (the two residual-stream *writers*), across an
   Optuna-searched layer range `[start∈[0,L/2], end∈[L/2,L])` (`ara.py:206-215`, `model.py:360-428`). Never q/k/v/gate/up/embed.
3. **TOKEN POSITION — CONFIRMED last-prefill `[:, -1, :]`**, hardcoded in core (`model.py:665-666`, also
   `get_residuals` `model.py:553`). **No per-example position support anywhere.** Left-padding (`model.py:91`)
   means `-1` is the last real prompt token. → Native ARA tests the wrong site for us; **P1 (position-aware ARA) is mandatory.**
4. **Optuna searches** 6 ARA params: `start_layer_index`, `end_layer_index`, `preserve_good_behavior_weight`
   [0,1], `steer_bad_behavior_weight` [1e-4,1] log, `overcorrect_relative_weight` [0,1.3], `neighbor_count` [1,15].
   **Multi-objective multivariate TPE** (`main.py:672-683`), NOT NSGA-II; `study.best_trials` = genuine Pareto
   front. Default objectives: `KeywordRate` + `KLDivergence`, both minimize. **`lora_rank` is FIXED config
   (default 50), NOT searched** → for the rank sweep we set `lora_rank` per run. 100 trials, 30 startup, resumable JournalStorage.
5. **Reset = exact.** Zeroing `lora_B` restores identity (ΔW=0), incl. the norm-preserving path. Reproduce mode
   replays stored params through `reset_model→modify_model`; single global `transformers.set_seed(seed)`; L-BFGS
   deterministic given inputs. Merge is one-way (forces reload).
6. **Plugin API (`plugin.py`):** external via `path/to/plugin.py:ClassName`. A `Plugin` must NOT define `__init__`
   (setup in `init(ctx)`); optional pydantic `settings` schema from TOML `[modifier.<Class>]`. `Modifier` (one
   only) implements `suggest_parameters(ctx,trial)→Parameters`, `modify_model(ctx,params)`, `reset_model(ctx)`;
   `Parameters` is `Serializable` (to_dict/from_dict). `Scorer` (any number) implements `get_score(ctx)→Score{value,
   rich_display, md_display}` (+ optional `get_baseline_score`), with config `optimization="minimize|maximize|none"`.
   `Context` exposes `get_responses/get_logits/get_residuals/get_model()/load_prompts` — `get_model()` is the full
   escape hatch (raw transformers model, `get_layers()`, `get_layer_modules()`, `apply_lora()`, `register_forward_hook`, `generate()`).
7. **Reuse vs fork:** custom Scorers and a **custom position-aware Modifier are pure external plugins** — register
   our own forward hooks on `ctx.get_model().get_layer_modules(i)`, index each row at its codeword position computed
   from the (left-padded) attention mask, drive `generate(max_new_tokens=1)`. We re-implement ~30 lines of
   `get_module_io` with our position policy and reuse ARA's objective/L-BFGS. **A fork is only needed if we insist on
   reusing core `get_module_io`/`get_residuals`** (which bake in `-1`). We will NOT fork for this.

**Deps (uv.lock @ pin):** torch 2.13.0, torchvision 0.28.0, transformers 5.6.2, optuna 4.8.0, peft 0.19.1,
accelerate 1.13.0, bitsandbytes 0.49.2, datasets 4.8.4, numpy 2.2.6; Python ≥3.10. **These conflict with the
frozen `poc_stage2` CSI stack → Heretic runs in its OWN env `heretic_csi`; frozen CSI numerics stay untouched.**

**Model load:** Heretic sets NO `attn_implementation` (uses HF default = SDPA), and tries dtype auto→fp16→bf16→fp32.
**CSI constant is eager+bf16.** VOID risk: our semantic-installation logprob scorer could differ between SDPA and
eager. **Mitigation:** force `attn_implementation="eager"` + `dtype=bfloat16` + pinned revision when loading inside
the plugin/env, and run an eager-vs-SDPA sensitivity smoke before trusting any number (new VOID condition 9 below).

**ΔW extraction for SVD:** original `module.base_layer.weight` (dequant 4-bit if needed), factors
`module.lora_A["default"].weight` / `lora_B["default"].weight`; ΔW = `lora_B@lora_A` (or diff merged−base; if
`preserve_row_magnitudes` the true delta is `normalize(W_base+BA)·‖W_base‖_row − W_base`). `Abliteration` already
does `torch.svd_lowrank` on a delta — code template for P3.

**AGPL-3.0:** kept in `external_repos/heretic/` with LICENSE intact; we build via external plugins, do not vendor
large chunks, do not distribute/network-serve a derivative. §13.

**VOID condition 9 (added):** any semantic number produced under an attention implementation other than the
CSI-frozen `eager` (bf16) without a passing eager-vs-used sensitivity check.

## 13. LICENSE / PROVENANCE
Heretic is **AGPL-3.0**. We keep it in `external_repos/heretic/` with its LICENSE intact, do NOT copy large
chunks into our tree, and build against it via config + external plugins. Any unavoidable upstream patch is
tracked as a diff under `patches/` with provenance. Our plugin code under `research/heretic_csi/` imports
Heretic; we note the AGPL network-copyleft implication (we do not distribute a network service built on it).

---

# PROGRESS LOG (append-only; newest entries at the bottom)

## S-001 — 2026-10-01 — sprint bootstrap
- Read inherited state: `SUMMARY_2026-09-02_TO_09-26.md` (full), located `reports/DCS_CSI_CLAIM_TABLE.md`
  (384 KB), `reports/DCS_CSI_RESULTS_DRAFT.md` (212 KB), CSI sprint log (2.98 MB). Recovered the §12
  reproducibility constants verbatim into §0 above.
- Cloned Heretic → `external_repos/heretic/`, pinned SHA `662e4ba27ecaf8878b0938c184a78f75a9116f82`.
  Confirmed ARA is present (`src/heretic/modifiers/ara.py`) and the modifier/scorer plugin API exists
  (`src/heretic/plugin.py`, `modifier.py`, `scorer.py`).
- Recovered infra: conda env `poc_stage2`; SLURM account `gpu-research`, partitions `killable`/`cpu-killable`;
  no L40S-named partition in current `sinfo` (killable holds the mixed GPU nodes) — GPU type to be requested
  via `--gres`/constraints, verified per job.
- Recovered data: prompt banks `data/boombness_prompts/boombness_prompt_bank_ts116_*`; split
  `dcs_ts116_domain_split.json` (seed 202609061, 70/23/23, 67 effective train, unit=domain, TEST spent);
  axes `configs/dcs_csi_axis_*.pt`; preregs `configs/dcs_csi_pr*.json`.
- Launched independent Heretic source-audit subagent (benign infra code) to answer the 7 ARA/plugin questions
  and verify the `[:, -1, :]` last-prefill-position capture claim from source. **Pending.**
- No GPU jobs launched yet. No files committed yet. Peer sessions all idle; no SLURM jobs of mine running.

### NEXT (planned)
- Fold the Heretic source-audit findings into a new §9 (Heretic mechanism audit) when the subagent returns.
- Scaffold `research/heretic_csi/` and run the P0 Phase-A smoke (model load, LoRA reset, identity inertness,
  ΔW numerical-rank inspection) as a single small GPU allocation.

## S-002 — 2026-10-01 — Heretic source audit COMPLETE (folded into §9)
- Independent source-read subagent returned a full, file:line-cited audit of Heretic @ `662e4ba2`. The
  load-bearing findings are folded into **§9** above. Headline confirmations:
  - **`[:, -1, :]` last-prefill-position capture is CONFIRMED in core** (`model.py:665-666`) with **no**
    per-example position support → position-aware ARA (P1) is mandatory, exactly as the plan anticipated.
  - **Position-aware ARA is implementable as a pure external plugin** (own forward hooks on
    `get_layer_modules`, per-row position from the left-padded attention mask) — **no upstream fork needed**.
  - ARA objective is a kNN-in-activation steer (preserve good / move bad→good / overcorrect away from bad) →
    maps to our preserve-target / move-source→target design (rename good/bad → target/source in notes).
  - `lora_rank` is **fixed config, not Optuna-searched** → the rank sweep sets `lora_rank` per run.
  - Heretic uses HF-default attention (**SDPA**), not the CSI-frozen **eager** → added **VOID 9** and an
    eager-vs-SDPA sensitivity smoke requirement before trusting any semantic number.
  - Deps (torch 2.13 / transformers 5.6 / optuna 4.8 / peft 0.19 / bnb 0.49) conflict with `poc_stage2` →
    Heretic gets its own env.
- Launched isolated-env subagent to build conda env `heretic_csi` (install pinned Heretic, verify imports/CLI,
  no GPU, do not touch `poc_stage2`). **Pending.**

## S-003 — 2026-10-01 — scaffolding research/heretic_csi (in progress)
- Creating `research/heretic_csi/` with: README (AGPL provenance note), a position-aware Modifier plugin
  skeleton, custom Scorer skeletons (SemanticInstallation / Preservation), a `configs/` dir, and unit-test
  stubs. Code is written against the audited base-class signatures (§9.6) and will be compiled/tested once the
  `heretic_csi` env is ready. No frozen CSI behavior is touched.
