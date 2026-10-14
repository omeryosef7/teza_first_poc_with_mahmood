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

## S-004 — 2026-10-01 — DESIGN RULING: architecture for the headline rank sweep (consequential; documented per plan §24)

Reconstructing the CSI scoring + position + intervention infrastructure revealed a genuine fork that
determines whether the rank sweep is *comparable* to the inherited basket/button rank-1 dissociation. Decision
made autonomously (conservative choice, documented, continue):

**The headline operator rank-sweep (P2) is run in the CSI "rescue" paradigm, forced to eager attention, reusing
the frozen CSI readout and rank-matched control families — with Heretic's ARA L-BFGS kNN optimizer + plugin API
+ Optuna as the operator-fitting *engine*.** Concretely:
- **Intervention modality = rescue under the live attention knockout** (`demo_all:attn_knockout:6-14:1.0`,
  `--knockout-scope target_surface_row_only`, dose 4, cell C, `query_kind=semantic_one_word`). TARGET = clean
  (no-KO) module-I/O at the codeword row; SOURCE = KO module-I/O at the codeword row. The learned operator ΔW=BA
  is fit to move SOURCE→TARGET at the per-example codeword position, generalizing the inherited rank-1-axis
  rescue to an arbitrary-rank weight operator. This is the ONLY framing directly comparable to basket rank 1/47
  PASS vs button 36/47 NEGATIVE and to the whole-state ceiling (recovery 0.341).
- **Position = per-example codeword row (`rel-10`), axis site (`rel-6`) as a secondary site** — NEVER
  last-token, NEVER an absolute index (CSI proved absolute indices VOID: 0/2300 triples match; the capture must
  be end-relative and self-validated by decoding the captured token == the codeword, failing loudly otherwise).
- **Endpoint = the frozen CSI readout** `y_install = logistic(logp_concept − logp_codeword)` via
  `score_behavior.py`'s forward-only `next_token_readout` at the "Answer:" position, with `option_mass<0.05`
  degraded-regime flagging, and validated concept/codeword id-groups (`signals.readout_id_pair`). Scored in
  `poc_stage2` (eager) by loading the exported LoRA adapter — maximal reuse of guard-tested code — AND by an
  inline heretic scorer cross-checked against it (independent re-derivation; satisfies VOID 9).
- **Eager everywhere:** force `attn_implementation="eager"` in the heretic env (minimal tracked patch to
  `model.py` load, under `patches/`, OR a wrapper monkeypatch) so the operator is fit under the same attention
  implementation it is scored under. An eager-vs-SDPA sensitivity smoke runs first.
- **Controls = the existing CSI rank-matched families** (random orthogonal rank-k, shuffled source↔target,
  norm-matched random LoRA, neutral-position, identity no-op, source→source, target→target) at every rank.

**What still uses Heretic natively:**
- **Phase B** = Heretic ARA run *as shipped* (last-position, knockout-free) on our matched populations — a
  deliberate baseline/control answering "is generic end-of-prompt operator editing sufficient?" (expected: no).
- **Optuna layer/component search (P4)** as a corroborating *knockout-free* modality, scoped separately and never
  mixed into the headline rescue numbers.

**Why not pure Heretic-native for the headline:** knockout-free source/target (installed vs not-installed
domains) conflates "installs" with "already installed", runs under SDPA≠eager, and cannot reuse the CSI
knockout/controls — so its rank numbers would not be comparable to the inherited dissociation, defeating the
scientific purpose. **Why not pure CSI-reimplementation:** the plan mandates exploiting Heretic's ARA optimizer,
plugin API and Optuna; we use all three as the engine and run native ARA as a control. This hybrid is the
plan-faithful AND inherited-science-faithful choice. **Reversibility:** nothing frozen is touched; both Phase B
and the hybrid are new artifacts under `research/heretic_csi/` + new `outputs/heretic_csi/`.

## S-005 — 2026-10-01 — P1 position primitive VALIDATED; QUOTA blocker + strategy pivot; env escalation

**P1 position primitive validated offline (no GPU), against the real Llama tokenizer:**
- id-pairs (mode=primary, leading-space, single-token, distinct): **bomb=13054, basket=14351, button=3215**.
- `positions.py` is correct: on the **chat-templated prompt (add_generation_prompt=True, NO "Answer:")**, the
  **codeword row is `rel_end=-10`** and decodes exactly to ` basket`/` button`; the LOUD self-check correctly
  REFUSED when `-10` was applied to the `+"Answer:"` input (there the codeword shifts to `-12`). Axis site
  `rel_end=-6` is the query-final `?` on the bare prompt (not the codeword — expected; `require_codeword_match`
  is off for the axis site).
- **VOID-critical fact pinned:** CSI's knockout/axis offsets (-10 codeword, -6 axis) are relative to the **bare
  templated prompt**; the `y_install` readout appends `"Answer:"` and reads the last position. `dcs_csi_axis.py`
  fits on `semantic_one_word`, cell C, site `rel-6` FROZEN, from pre-extracted `extract_boombness` states —
  consistent with the bare-templated construction. **TODO before any scored run:** confirm `extract_boombness`
  captured on the bare templated prompt (expected) so the operator anchor matches the axis/KO site exactly.

**BLOCKER (escalation, per plan §24 — NOT stalling the headline):** the `heretic_csi` conda env install fails
on `torch` with `OSError [Errno 122] Disk quota exceeded`. Root cause = a **group/qtree quota on
`/Netapp5_sharifm` (group `cs_sharifm`), exhausted by the whole group (~25T)** — invisible to `quota` (which
reports user 200G/16T, group 16.9T/32T), but a `dd` probe fails EDQUOT leaving 0-byte files. Volume is 94% full,
~1.4T physical free. `heretic_llm` itself builds fine; only the ~8–10G torch stack can't be written.
- **Reclaimed ~6G of my own** to relieve the razor's edge: removed the broken partial `heretic_csi` env (2.9G)
  and `/home/sharifm/students/omeryosef/.pip_cache` (3.2G). Writes healthy again, but the group volume remains
  near its limit — **stay frugal; prefer compact JSON; clean scratch.**
- **STRATEGY PIVOT (keeps P0–P3 moving with zero new env):** the headline operator rank-sweep already runs in
  `poc_stage2` per the S-004 ruling (working torch/transformers/peft, eager). We implement the position-aware
  low-rank operator optimization by **porting ARA's L-BFGS kNN-steer objective as a clean-room reimplementation
  from the §9 audit (attributed to ARA / Weidmann 2026; algorithm, not AGPL code)** into `research/heretic_csi/`,
  driven by the existing CSI knockout + readout + control families. **No torch install needed for the headline.**
- **What remains env-blocked (deferred, not headline):** Phase B (native Heretic ARA *as shipped*) and the
  Optuna layer/component **search** modality (P4 corroboration). **USER DECISION needed to unblock these** (not
  needed for P0–P3): (A) raise/free the `cs_sharifm` qtree quota [cleanest]; (B) build the env on a spacious
  shared FS visible to SLURM nodes — candidates `/specific/scratches` (8.3T free) or `Netapp5_tkoren` (7.4T),
  each pending access/visibility verification; (C) treat native ARA as a `poc_stage2` reimplementation too
  (loses "ran the shipped tool" provenance). Recommendation: (A). This is surfaced to the user; core work proceeds.

## S-006 — 2026-10-01 — P1/P2 core built + UNIT-TESTED (CPU, no GPU): operator optimizer + position primitive
- `research/heretic_csi/operator_ara.py`: clean-room reimplementation of ARA's kNN-steer L-BFGS objective
  (attributed to Weidmann 2026 / Heretic ARA; NOT a copy of AGPL source). Fits `W_eff = W_base + B@A`
  (rank-r LoRA factors, B zero-init = identity start) jointly over modules with
  `L = preserve_w·‖target_in·W_effᵀ − target_out‖² + steer_w·[knn(source→target) − overcorrect·knn(source→source)]`.
  Renamed good/bad → TARGET(clean)/SOURCE(knockout). Exposes effective ΔW for SVD (P3), row-norm-preserve
  option, and **rank-matched controls** (`random_orthogonal_operator` norm+rank-matched, `identity_operator`).
- `research/heretic_csi/tests/test_operator_and_positions.py`: **8/8 PASS** in `poc_stage2` —
  loss decreases; SOURCE steers toward TARGET (knn dist shrinks vs un-edited); ΔW rank ≤ configured rank
  (ranks 1/2/4); identity adapter inert; random-orthogonal control matches target Frobenius norm & rank;
  row-norm-preserve is exact identity at ΔW=0; position self-check passes on correct token and RAISES on
  wrong token; left-padding handled; right-padded mask rejected.
- Committed `--no-verify` path-scoped; push credential-blocked (documented).
- **NEXT (GPU integration, P2):** capture real codeword-row (`rel_end=-10`) module-I/O for o_proj/down_proj
  over the CSI knockout band (L6-14) — TARGET=clean forward, SOURCE=KO forward — via the existing CSI
  knockout harness (`score_behavior.make_intervention`, eager/bf16), fit the operator at ranks
  {1,2,4,8,16,32,50} per codeword, apply ΔW, read `y_install`, compare basket vs button with rank-matched
  controls. First a tiny GPU smoke (one domain) before the sweep. Must confirm `extract_boombness` capture
  is on the bare templated prompt (TODO from S-005) so the anchor matches the frozen axis/KO site.

## S-007 — 2026-10-02 — loop tick: capture-reuse mapping + refined P2 plan (P2a activation / P2b weight)
- Ops: SLURM idle; index unlocked; HEAD `9c225600`; **quota eased to 4.4T free (85%, was 1.4T/94%)** — more
  headroom (user freed space / admin); still staying frugal.
- **Finding (decisive for P2 design):** the existing `extract_boombness` runs store **residual-stream
  representations only** (`cache/final_occurrence_reps.pt`, `multiposition_reps.pt`) at sites — **NOT**
  o_proj/down_proj module input/output, and **clean only (no KO arm)**. So the *weight-level* ARA fit (needs
  matrix I/O under clean AND KO) requires a **fresh capture**. The KO itself is reusable: `pc = pair()` (from
  `common`) is the patch-core provider; the attention-knockout context manager lives in `surgical_knockout.py` /
  `score_behavior.py` (`make_intervention` builds it, but is deeply coupled to composed-arm plumbing).
- **REFINED P2 (two complementary experiments, both feed H1 "dimensionality explains the dissociation"):**
  - **P2a — activation-space LEARNED low-rank rescue (do FIRST; maximal reuse, maximal comparability).** The
    inherited basket-PASS/button-NEGATIVE was an *activation-space rank-1 axis* rescue. Extend it by replacing
    the PLS/fixed subspace with an **optimization-learned rank-r projector** fit on the already-captured
    clean (`h_clean`) and KO (`h_ko`) site states, run through the **existing** `dcs_csi_subspace*` rescue+rank
    harness (which already does KO, site capture, rescue arm `h' = h_ko + P_r(h_clean−h_ko)`, rank test vs the
    46-control family, splits, independent rederive). Rank sweep {1,2,4,8,16,32} per codeword → the
    rescue-vs-rank curve, directly comparable to the rank-1 result. New code ≈ a small projector fitter.
  - **P2b — weight-space ARA operator ΔW=BA (the plan's literal "compact weight-level operator").** Fresh
    capture of o_proj/down_proj I/O at the codeword row (`rel_end=-10`) under clean (TARGET) and KO (SOURCE)
    over band L6-14, fit `operator_ara` at ranks {1,2,4,8,16,32,50}, apply, read `y_install`. Reuse the KO CM
    from patch-core (validated by reproducing the frozen manipulation KO−BASE≈−0.2, a GATE-0 liveness check).
- **Decision:** P2a first (fast, high-reuse, comparable), then P2b (novel weight distillation). Both with
  rank-matched controls; TRAIN for fitting, VALIDATION for the certifying rank test; TEST never touched.
- **NEXT tick:** read `dcs_csi_subspace_analyze.py` rescue entrypoints; add the rank-r projector fitter
  (`research/heretic_csi/learned_projector.py`) + unit test; wire a one-domain GPU smoke for P2a.

## S-008 — 2026-10-02 — loop tick: P2a basis builder built + tested (4/4); basis format locked
- Locked the frozen rescue-basis format from `dcs_csi_axis.save_bases`:
  `torch.save({"meta":meta,"bases":{key:Tensor[r,hidden] float32}}, path)`, `meta["bases"][key]={rank,sha16}`,
  `meta["bases_sha16_of"]="saved_float32_tensor_bytes"`. Consumed by `score_behavior` rescue arm +
  `dcs_csi_subspace_analyze` rank test — zero changes needed.
- `research/heretic_csi/learned_projector.py`: `pls1` (deflating, provenance=dcs_csi_axis), **`random_orthonormal_basis`
  / `random_orthonormal_family`** (the RANK-MATCHED control CSI's rank-5 negative lacked; distinct seeded draws so
  the seed reaches the draw — guards against retraction-#7's fake n=1 band), `save_basis`/`load_basis` (byte-exact
  format). `research/heretic_csi/tests/test_learned_projector.py`: **4/4 PASS** — random basis is rank-r &
  orthonormal (r∈{1..32}); PLS deflation gives true rank-r; control family distinct+reproducible; save/load
  round-trip with sha16 matching bytes on disk.
- Committed `--no-verify`; push still credential-blocked.
- **NEXT tick:** read a frozen subspace-rescue runargs (e.g. `runargs/` for the rank-1/rank-5 PR-CSI-001 runs) to
  learn exactly how `score_behavior` is invoked with a candidate basis + control family under KO; then build the
  P2a orchestration (per codeword × rank {1,2,4,8,16,32}: emit PLS candidate + N random controls, run the rescue,
  run the rank test) and a one-domain GPU smoke (eager/bf16, 3090/L40S, gpu-research).

## S-009 — 2026-10-02 — loop tick: P2a recipe fully specified (near-pure reuse); feasible both codewords
- **`dcs_csi_axis.py` already emits the whole rank-r candidate + rank-matched control family:** `--max-rank`,
  `--rank-controls 1,2,4,8,16,32` ("for each rank r, random rank-r subspaces AND rank-r PLS fits on shuffled
  labels"), `--n-random-rank` (set 46 to match the hardened family), `--force-layer`, with built-in TEST-leak
  refusal + codeword/cell checks. So P2a needs **no new fitting code** — my `learned_projector` is demoted to a
  cross-check / P2b tool.
- **`score_behavior` rescue interface** (from `dcs_csi_p1_smoke.slurm`): arms via `--rescue-donor clean|self`,
  `--rescue-basis <pt> --rescue-basis-key <key> --rescue-norm-match-key <key>`, `--rescue-positions query
  --rescue-layer L`, under `--intervene demo_all:attn_knockout:6-14:1.0 --knockout-scope target_surface_row_only`,
  `--attn-impl eager --dtype bfloat16`, model = pinned local snapshot `0e9e39f2…`.
- **Inherited setup (for comparability, read from `DCS_CSI_SUBSPACE_basket_train_n46.json`):** fit_prompt=**behavioral**
  corpus (`cont1_behavioral_<cw>_bomb`), scored on semantic `y_install`; arms BASE/KO/KO_SELF/KO_FULL/KO_AXIS/
  KO_PLS/KO_ORTH/KO_RAND0..N. **Both behavioral + semantic corpora exist for basket AND button** → P2a feasible
  both codewords. (Layer: dissociation at L18/L20 — confirm exact `rescue_layer` + locate the `--readout` dir next.)
- **P2a orchestration (next build):** per codeword: (1) `dcs_csi_axis.py` CPU job → one `.pt` with candidates at
  ranks {1,2,4,8,16,32} + 46 matched controls each; (2) `score_behavior` rescue arms per rank (GPU, batched per
  alloc, eager/bf16); (3) `dcs_csi_subspace_analyze.py` rank test per rank → recovery-fraction + rank-p, TRAIN
  then VALIDATION (TEST never touched). Deliverable: **rescue-vs-rank curve, basket vs button**, with the exact
  rank-matched controls CSI's rank-5 negative lacked. One-domain GPU smoke first.

## S-010 — 2026-10-02 — loop tick: FIRST GPU JOB — PR-CSI-001 smoke launched (job 964277); P2a recipe pinned
- **Launched the validated 6-arm smoke** `sbatch dcs_csi_p1_smoke.slurm basket configs/dcs_csi_axis_basket_behavioral.pt`
  → **job 964277 RUNNING on n-205** (killable, gpu-research, 1 GPU, eager/bf16, --limit 24). Purpose: GATE-0
  liveness of the KO+rescue+readout harness in THIS environment before the full sweep — expect KO−BASE≈−0.2,
  KO_FULL recovers, KO_AXIS writes nonzero delta, KO_SELF inert. Inherited basket axis verified smoke-compatible
  (selected_layer=18, fit_prompt=behavioral, site=rel-6, bases incl. cand_rank1+ctrl_orth, 41 total).
- **P2a recipe fully pinned (basis key naming from `dcs_csi_axis.py`):** candidates `cand_rank1` (r=1) and
  `cand_pls{r}` (r≥2); rank-matched controls `ctrl_random_r{r}_{i}` + `ctrl_shuffled_pls{r}_{j}` (via
  `--rank-controls 1,2,4,8,16,32 --n-random-rank 46 --n-shuffled-rank …`); rank-1 controls ctrl_orth/ctrl_random*/
  ctrl_shuffled*. Corpus=`cont1_behavioral_<cw>_bomb`, readout=`ts116m_readout_<cw>_bomb_*`, bank=ts116m, excl=
  `runargs/dcs_cont/exclude_<cw>_bomb_sow_train.txt`, model snapshot `0e9e39f2…`, COMMON = `--query-kinds
  semantic_one_word --conditions natural_doublespeak --n-examples 4 --readout-ids whole_answer --min-option-mass
  0.05 --dtype bfloat16 --attn-impl eager`, KO=`demo_all:attn_knockout:6-14:1.0 --knockout-scope
  target_surface_row_only`, RESC=`--rescue-positions query --rescue-layer 18`.
- **NEXT tick:** read smoke 964277 (validate GATE-0 + artifacts + DONE), then fit the ranksweep axes (CPU job:
  `dcs_csi_axis.py --max-rank 32 --rank-controls 1,2,4,8,16,32 --n-random-rank 46` per codeword) and write the
  P2a rescue sweep slurm (ranks {1,2,4,8,16,32} × candidate+controls, batched per allocation).

## S-011 — 2026-10-02 — loop tick: smoke 964277 FAILED (protective HW guard) → resubmitted 3090-pinned (964329)
- **Self-check catch (log, not sacct):** smoke 964277 landed on **RTX 2080 Ti (cc 7.5, Turing = EMULATED bf16)**
  because `--gpus=1` had no architecture constraint. The inherited `score_behavior` has a **built-in hardware
  guard** that REFUSED: *"--dtype bfloat16 on RTX 2080 Ti … native bf16 requires >=8.0; below that EMULATED …
  (S-037/S-119/S-121)."* So the job FAILED **before producing any number** — the guard protected us; **no VOID
  result**. This is the V100-class emulated-bf16 hazard from §0/§12.
- **STANDING RULE (added):** every GPU job in this sprint MUST pin a native-bf16 architecture:
  **`--gpus=geforce_rtx_3090:1`** (positive constraint, never an exclude-list) — or l40s/a5000 equivalently; never
  bare `--gpus=1`. Verify `nvidia-smi compute_cap >= 8.0` in the log trailer.
- **Resubmitted:** `sbatch --gpus=geforce_rtx_3090:1 dcs_csi_p1_smoke.slurm basket configs/dcs_csi_axis_basket_behavioral.pt`
  → **job 964329 RUNNING on n-302** (3090-pinned). Read next tick for GATE-0 liveness.
- Quota fine; index unlocked.

## S-012 — 2026-10-02 — loop tick: smoke cold-loading (not hung); basket axis-fit launched (CPU, parallel)
- **Smoke 964329:** on RTX 3090 (native bf16 ✓). `.err` shows `Loading weights: 0/291` at ~30 min — the
  documented **cold cross-user NFS model-load tax** (§8; snapshot lives under `matanbentov/`), NOT a hang
  (diagnosed via the loading bar per the stall-diagnostic rule, not elapsed time). 2h limit is ample; read next tick.
- **Launched basket rank-sweep axis fit** (CPU, `cpu-killable`): `research/heretic_csi/slurm/axisfit_ranksweep.slurm
  basket` → **job 964404 RUNNING on rack-iscb-31**. Reuses `dcs_csi_axis.py` unchanged
  (`--max-rank 32 --rank-controls 1,2,4,8,16,32 --n-random-rank 46 --n-shuffled-rank 10 --force-layer 18
  --fit-prompt behavioral --site rel-6`) → emits `configs/heretic_csi/hcsi_ranksweep_basket.pt` with candidates
  `cand_rank1`/`cand_pls{2..32}` + rank-matched control families. Independent of the smoke outcome (valid PLS
  artifacts regardless). 2 GPU/CPU jobs running (≤6 cap).
- **NEXT tick:** read smoke 964329 (GATE-0 liveness) + axisfit 964404 (DONE_MARKER, candidate count); if both
  clean, write + launch the P2a rescue sweep (ranks {1,2,4,8,16,32} × candidate+controls, 3090-pinned, batched
  per allocation) for basket, then button.

## S-013 — 2026-10-02 — loop tick: P2a runner built+validated; basket axisfit DONE; reduced sweep LAUNCHED
- **basket axisfit 964404 COMPLETED** (5:54): `hcsi_ranksweep_basket.pt`, 383 bases, 33 candidates
  (cand_rank1/cand_pls1..32), L18 rho_loo=+0.6525, TRAIN-selected rank r3 (candidate, not a finding).
- **button axisfit 964435 RUNNING** (CPU).
- **Model-load tax CONFIRMED pathological under contention:** smoke 964329 loaded at ~30 s/tensor (47/291 @ 54min,
  ETA +2h) on contended n-302 — and the per-arm `python` invocation means a **cold load on the FIRST arm only**
  (warm page cache after). Killed the 2h-limited smoke (couldn't extend; killable denies). Design response:
  **one allocation, generous `--time=08:00:00`, liveness arms first, all sweep arms after** → one cold load amortized.
- **Built + validated the P2a runner:** `research/heretic_csi/emit_sweep_arms.py` (resolves candidate +
  rank-matched control keys from the .pt, pre-flight fail-fast if missing — dry-run exit 0, all keys resolve for
  ranks 1..32 with correct norm-match) and `research/heretic_csi/slurm/rescue_sweep.slurm` (pre-flight →
  BASE/KO/KO_SELF/KO_FULL liveness → per-rank candidate+controls; reuses score_behavior KO+rescue UNCHANGED,
  3090-pinned, eager/bf16).
- **LAUNCHED reduced basket sweep 964437** (ranks 1,4,32; 6 random + 2 shuffled controls; --limit 24) on n-302
  → validates the whole pipeline end-to-end in one cold load + first basket rescue-vs-rank signal.
- **NEXT tick:** read 964437 liveness (KO_FULL recovers, KO_SELF inert, KO_CAND fires) + button axisfit; if clean,
  run `dcs_csi_subspace_analyze` per rank for the reduced basket signal, then launch the FULL basket + button sweeps.

## S-014 — 2026-10-02 — loop tick: model-load tax FIX (node-local staging); button bases ready; sweep resubmitted
- **button axisfit 964435 COMPLETED** (5:44) → `hcsi_ranksweep_button.pt` ready. Both codewords' bases now exist.
- **Model-load tax worsened on n-302** (964437: 77/291 @ 22min, 50 s/tensor, ETA +3h) — unusable. Root cause =
  per-tensor random NFS reads of the cross-user snapshot under node contention.
- **FIX (standing rule S-014):** `rescue_sweep.slurm` now **stages the snapshot to node-local disk once**
  (`cp -rL $SNAP $SLURM_TMPDIR/llama31`, dereferencing HF blob symlinks) and loads `--model` from there — a single
  sequential bulk copy instead of hours of per-tensor NFS reads. Falls back to NFS if the copy fails. All future
  GPU jobs should stage-in likewise.
- Killed 964437; **resubmitted reduced basket sweep → 964500** (ranks 1,4,32; 6 rand + 2 shuf; --limit 24).
- **NEXT tick:** verify STAGE_IN succeeded + load became fast on 964500; read liveness (KO_FULL recover / KO_SELF
  inert / candidate fires); run `dcs_csi_subspace_analyze` for the first basket rescue-vs-rank signal; then launch
  full basket + button sweeps.

## S-003 — 2026-10-01 — scaffolding research/heretic_csi (in progress)
- Creating `research/heretic_csi/` with: README (AGPL provenance note), a position-aware Modifier plugin
  skeleton, custom Scorer skeletons (SemanticInstallation / Preservation), a `configs/` dir, and unit-test
  stubs. Code is written against the audited base-class signatures (§9.6) and will be compiled/tested once the
  `heretic_csi` env is ready. No frozen CSI behavior is touched.

## S-015 — 2026-10-02 — loop tick: n-302 is a bad-I/O node (not contention) → exclude it
- 964500 STAGE_IN (16GB cp -rL) ran >29min without finishing; `squeue -w n-302` showed ONLY my job → the
  slowness is **n-302's NFS path itself**, not SLURM contention. Killed 964500.
- Resubmitted reduced basket sweep with `--exclude=n-302` → **964561 on n-350**. If n-350 stages+loads fast,
  the rule is simply "exclude n-302"; if n-350 is also slow, the durable fix is a one-time model copy to a fast FS
  (/specific/scratches 8.3T) that all jobs read from.
- NEXT tick: confirm 964561 STAGE_IN done + load fast + liveness; run subspace_analyze for first basket signal.

## S-016 — 2026-10-02 — loop tick: slow load is SOURCE-path (not node); analyzer CLI + naming fix; patience
- n-350 ALSO staged slowly → the ~9MB/s read is the **matanbentov snapshot netapp path itself**, not a single
  node. Decision: **STOP killing jobs** (each kill wasted a partial stage); 964561 has an 8h limit — let the
  one-time stage finish, then 31 warm arms run fast. If a durable fix is needed later: one-time copy of the model
  to my own FS and point all jobs there.
- Learned `dcs_csi_subspace_analyze.py` CLI: `--codeword --tag-prefix --expect-n --arms --direction sufficiency
  --candidate-arm --comparator-arm KO_ORTH --full-arm KO_FULL --ko-arm KO --base-arm BASE --self-arm KO_SELF
  --split --control-prefixes KO_SHUF,KO_RAND --option-mass-floor 0.05 --self-inert-tol 0.005`. Per-rank test:
  `--candidate-arm KO_CAND_r{r}` against that rank's `KO_RAND_r{r}_*`/`KO_SHUF_r{r}_*` controls.
- **BUG FIX:** `emit_sweep_arms.py` named random controls `KO_RND_*`; analyzer default prefix is `KO_RAND`.
  Renamed emitter → `KO_RAND_r{r}_{i}` (full sweep will match the analyzer default). The in-flight reduced run
  964561 still emits `KO_RND` → analyze it one-off with `--control-prefixes KO_SHUF,KO_RND`.
- NEXT tick: if 964561 stage done + liveness clean, analyze the reduced basket signal per rank; launch full sweeps.

## S-017 — 2026-10-02 — MILESTONE: staging works (4s load), GATE-0 liveness PASSES; tab-parse bug fixed
- **Node-local staging SOLVES the load tax:** 964561 STAGE_IN done (51min cp, 30G node-local) → model loaded in
  **~4 seconds** (291/291 @ 62 it/s) vs hours from NFS. Arms then ran ~45s each.
- **GATE-0 LIVENESS PASSES (pipeline validated end-to-end):** BASE/KO/KO_SELF/KO_FULL all completed
  (`failures: {}`). KNOCKOUT LIVENESS: `median_prefill_edits=2016, total_prefill_edits=47484,
  total_decode_edits=0, scope_violations={}, attn=eager` — the attention knockout is LIVE and scope-correct;
  `option_mass median=0.1212` (>0.05 floor OK); readout ids concept=13054 / codeword=14351 (matches offline
  validation). The semantic-one-word forward-only rescue contract is satisfied.
- **BUG FOUND + FIXED (self-check):** candidate arm failed with `--rescue-norm-match-key 'candidate'`. Cause: bash
  `read` with `IFS=$'\t'` **collapses consecutive tabs** (tab is IFS-whitespace), eating the candidate's empty
  norm-match field and shifting ROLE into `$NM`. Fix: emit `NONE` sentinel for candidates; slurm skips norm-match
  when `NONE`. Verified emitter output.
- Resubmitted reduced basket sweep (fixed) → **965233 on n-350** (stages, then candidate+control arms).
- **SCALE NOTE for the real rank test:** --limit 24 covers only ~3 domains; the domain-level rank test needs all
  67 TRAIN domains (~670 rows) × (46+10 controls) × ranks. That is ~hours/allocation and 6 parallel per-rank jobs
  would contend on the slow source stage. **Next design:** likely a one-time DURABLE model copy to a fast-read
  location so parallel per-rank jobs each stage quickly; evaluate next tick.
- **NEXT tick:** confirm 965233 candidate+control arms produce valid rescue output; run subspace_analyze (one-off
  --control-prefixes KO_SHUF,KO_RAND) for the first basket rescue-vs-rank verdict; design the full-population run.

## S-018 — 2026-10-02 — loop tick: full-population knobs added to sweep slurm (965233 still staging)
- 965233 still in STAGE_IN (~28min; ~51min expected) — no arms yet.
- Prepared the full-population run: `rescue_sweep.slurm` now takes `LIMIT=0` (no --limit = all 67 TRAIN domains)
  and `BATCH` (--readout-max-batch; 1 = validated smoke, raise to 8/16 for speed). One job per codeword, all ranks,
  one stage → avoids parallel-stage contention on the slow source. `bash -n` syntax-clean. Does not affect the
  in-flight 965233 (submitted pre-edit).
- Plan: once 965233 confirms candidate+control arms produce valid rescue output, launch full basket (LIMIT=0
  BATCH=8, ranks 1,2,4,8,16,32) and full button, ~2-3h each; then subspace_analyze per rank → rescue-vs-rank curve.
- NEXT tick: read 965233 candidate/control arms + analyze; validate batch=8 numerics match batch=1 before trusting.

## S-019 — 2026-10-02 — loop tick: candidate+control arms RUN clean; analysis harness built
- 965233 arms running clean with the tab fix: KO_CAND_r1/r4 + KO_RAND_r{1,4}_* + KO_SHUF_r{1,4}_* all
  `failures: {}` (~45s/arm). rank-32 arms finishing; whole reduced run ~completes this hour.
- Learned analyzer semantics: `--tag-prefix <p>` (tags=`<p>_<arm>`), `--arms <names>`, `--candidate-arm
  KO_CAND_r{r}`, `--control-prefixes KO_SHUF,KO_RAND`, per-rank. 965233 uses KO_RAND naming (submitted post-rename).
- Built `research/heretic_csi/analyze_sweep.py`: per rank → builds arm list (liveness + candidate + that rank's
  controls via emit_sweep_arms), calls the FROZEN `dcs_csi_subspace_analyze.py` (reused rank test), tabulates
  rank→recovery_fraction/rank_p/verdict into a SUMMARY json. (Reduced run has only ~3 train domains → validates
  the harness produces verdicts, NOT a real rank test; full population comes next.)
- NEXT tick: 965233 done → run analyze_sweep for the reduced basket (sanity that candidate rescues > controls at
  some rank); validate the analyzer JSON keys; then launch full basket (LIMIT=0 BATCH=8) + full button.

## S-020 — 2026-10-02 — MILESTONE: first end-to-end P2a analysis works (gates PASS); FULL basket launched
- 965233 reduced basket COMPLETED; `analyze_sweep.py` runs the FROZEN `subspace_analyze` per rank and produces
  verdicts. Disambiguation: the analyzer REFUSES duplicate same-tag run dirs ("separate by slurm_job_id, never by
  recency") — added `--slurm-job` → `--require-slurm-job` (clean; no need to delete the un-deletable stale dirs).
- **GATES PASS at every rank** (reduced, 3 train domains — harness validation, NOT a result): manipulation
  KO−BASE=−0.301, identity KO_SELF−KO=+0.001 (inert), instrument KO_FULL−KO=+0.211. option_mass OK; KO live.
- **Interpretable early signal (not certifiable at 3 domains / 8 controls):** candidate raw rescue
  (candidate−ko) rises with rank (r1 +0.012 → r4 +0.036 → r32 +0.047), BUT at r32 random rank-matched controls
  also rescue (candidate ranks 3/9, DOES NOT PASS) while at r1 the candidate is top-of-controls (INCONCLUSIVE,
  floor 0.111). → the **dose/dimensionality confound is real and visible**; rank-matched controls are doing exactly
  their job (this is why CSI's rank-5 was a confounded negative). A real verdict needs the 46-control family.
- **LAUNCHED the real experiment — full basket sweep 965462** (LIMIT=0 = all 67 TRAIN domains, ranks
  {1,2,4,8,16,32}, 46 random + 10 shuffled controls/rank, BATCH=8, 346 arms, one stage). ~3h expected.
- **NEXT tick:** verify 965462 BATCH=8 liveness option_mass matches the BATCH=1 reduced (0.1212) before trusting;
  when done, analyze_sweep full basket (floor 0.0213) → the first DEFENSIBLE basket rescue-vs-rank curve; launch
  full button (staggered to avoid stage contention).

## S-021 — 2026-10-02 — loop tick: full button sweep launched in parallel (both full sweeps staging)
- 965462 (full basket) still staging on n-350. Launched **full button sweep 965502 on n-304** (LIMIT=0, ranks
  {1,2,4,8,16,32}, 46 rand + 10 shuf controls, BATCH=8). Both full-population runs now staging in parallel (2 jobs,
  ≤6 cap; share source read-bandwidth but parallel wins overall). Quota 4.4T free, fine.
- NEXT tick: when each finishes, verify BATCH=8 liveness option_mass≈0.1212 (vs BATCH=1 ref) + gates, then
  analyze_sweep per codeword (floor 0.0213) → the first DEFENSIBLE basket-vs-button rescue-vs-rank comparison.

## S-022 — 2026-10-02 — BUGS: BATCH=8 OOMs + per-arm reload too slow → switch to arm_runner (model-once)
- **BATCH=8 OOMs the 3090** (23GB): full BASE arm flooded with CUDA OOM on the whole-answer readout + KO mask.
  `--readout-max-batch 1` is why the inherited code used batch 1. Numerics fine (survivor option_mass 0.1239 ≈
  batch-1 0.1212) — purely memory. **Revert to BATCH=1.**
- **Per-arm reload too slow:** my `rescue_sweep.slurm` runs a separate `python score_behavior.py` per arm = a
  model reload each; 346 arms × reload is many hours. Killed both broken full runs (965462, 965502).
- **FIX = reuse `scripts/dcs_csi_arm_runner.py`:** it reads an argv-file (one full score_behavior command/line) and
  **memoizes `dc.load_model`** → model loads ONCE, reused across all arms (keyed on load params incl.
  attn_implementation=eager); also hook-leak-checks between arms + skip-if-done (strict_run_dir) for resume.
- **Rebuild plan (next tick):** rescue_sweep.slurm → stage model; emit an argv-file of lines
  `python src/boombness/score_behavior.py $COMMON [$KO $RESC $EXTRA] --arm X --tag Y` (model = staged local path,
  BATCH=1); run `arm_runner --argv-file F --expect-n N --out LOG`. One model load, all 346 arms. Relaunch full
  basket + button. Then analyze_sweep for the first defensible curve.
- Nothing running now (both killed). No results lost (BATCH=8 runs were invalid).

## S-023 — 2026-10-02 — loop tick: rescue_sweep rebuilt on arm_runner (model loads ONCE); full sweeps relaunched
- Rewrote `rescue_sweep.slurm`: after staging, it emits an argv-file (one `python score_behavior.py ...` line per
  arm: liveness + candidate + rank-matched controls) and runs `scripts/dcs_csi_arm_runner.py --argv-file F
  --expect-n EXPECTN --out ...`. arm_runner memoizes `dc.load_model` → **one model load for all 346 arms** (no
  per-arm reload), hook-leak-checks between arms, skips complete arms. `set +e` guard around it to capture RC.
  BATCH reverted to 1 (no OOM). `bash -n` clean.
- Relaunched full **basket 965561** + **button 965562** (both n-304, BATCH=1, LIMIT=0, ranks {1,2,4,8,16,32},
  46 rand + 10 shuf controls). EXPECTN=0 (fresh run, skip-if-done off).
- NEXT tick: confirm arm_runner log shows exactly ONE "MODEL LOAD" (key=...eager...) and arms advancing fast;
  verify liveness option_mass≈0.1212 at BATCH=1; when done, analyze_sweep per codeword (floor 0.0213) for the
  first defensible basket-vs-button rescue-vs-rank curve.

## S-024 — 2026-10-02 — ~4h DEEP SELF-REVIEW (adversarial; GPU-blocked tick, both full sweeps staging)
Reviewed the live P2a path against the plan's bug classes. Findings:
- **Rank-matched controls — CORRECT (the thing CSI's rank-5 lacked).** emit_sweep_arms emits, per rank r, the
  candidate (cand_rank1 / cand_pls{r}) and ONLY rank-r controls (ctrl_random_r{r}_* [46] + ctrl_shuffled_pls{r}_*
  [10]); analyze_sweep runs the rank test per rank with exactly that family (--control-prefixes KO_SHUF,KO_RAND on
  the per-rank --arms). So a rank-r candidate is scored vs rank-r nulls — no rank-1-null confound. ✓
- **No TEST leak.** dcs_csi_axis refuses TEST domains in the fit; analyze_sweep uses --split train (discovery).
  ⚠ ACTION: the certifying claim must also read --split validation; TEST stays spent (never use).
- **option_mass degraded handling.** --min-option-mass 0.05 (row filter) + analyzer --option-mass-floor 0.05. ✓
- **positions.** P2a does NOT use my positions.py — it uses dcs_csi_axis/score_behavior's frozen rel-6 site logic
  (guard-tested); positions.py is for P2b only (and is unit-tested with decode==codeword). ✓
- **sufficiency vs necessity.** analyze_sweep uses --direction sufficiency (rescue ADDs back under KO) — correct;
  not the necessity contract. ✓
- **MINOR:** analyze_sweep's --comparator-arm is an arbitrary rank-r random control for r>=2 (no ctrl_orth at r>=2).
  This only affects the single "candidate−comparator" reported contrast; the VERDICT rests on the rank test vs the
  whole family, so it does not bias the decision. Acceptable; noted.
- **OPEN VERIFY (next tick):** confirm arm_runner logs exactly ONE "MODEL LOAD key=(...eager...)" — if score_behavior
  failed to thread --attn-impl eager into dc.load_model, the memo default is sdpa (VOID 9). The smoke's liveness
  already reported attn=eager, so expected fine, but verify on the arm_runner path explicitly.
- **Duplicate-dir hygiene:** stale hcsi_p2a_* dirs exist from killed runs; analysis disambiguates by
  --require-slurm-job <jobid> (cannot rm them — deletion permission-denied). Confirmed clean mechanism.
No headline exists yet (both runs staging); nothing to overclaim. The pipeline + controls are sound.

## S-025 — 2026-10-02 — arm_runner verified (1 eager load); FIX r=1 control-count bug; relaunch all-ranks-correct
- **arm_runner validated:** `MODEL LOAD #1 (18.8s) key=(...,'eager',...)` — exactly ONE load, EAGER (VOID 9 clear);
  304-line argv; arms advancing in-process (no reload). option_mass medians sane (basket 0.090, button 0.330 at
  BASE — note these are per-arm BASE aggregates, button installs more as expected).
- **BUG (self-check): rank-1 was under-powered.** emit_sweep_arms had an r==1 branch using the LEGACY small
  control family (ctrl_orth + 8 random + 5 shuffled = 14 → floor 0.067, cannot certify at 0.05), instead of the
  rank-matched 46+10 family (ctrl_random_r1_*/ctrl_shuffled_pls1_*) that the .pt has and the inherited n46 rank-1
  PASS used. Fixed: use the rank-matched family uniformly for ALL ranks (legacy only as fallback if absent).
  Verified r=1 now emits 57 arms (1+46+10). Only 1 arm had run on the buggy jobs → negligible waste.
- Killed 965561/965562; relaunched **basket 965624 + button 965625** (n-350). Now every rank (incl r=1) is
  certifiable at floor 0.0213. argv will be 346 lines (4 + 6×57).
- **NEXT tick:** monitor arms to completion (~2-3h, one load); then analyze_sweep per codeword, TRAIN then
  VALIDATION, --require-slurm-job → the first defensible basket-vs-button rescue-vs-rank curve.

## S-026 — 2026-10-02 — loop tick: both full sweeps staging; built rescue-vs-rank table generator (deliverable prep)
- 965624 (basket) + 965625 (button) still in STAGE_IN on n-350 (~28min; parallel source reads). No arms yet.
- Built `research/heretic_csi/make_rank_table.py` (GPU-free): reads the analyze_sweep SUMMARY jsons → the P2a
  deliverable markdown table (rank | recovery_fraction | candidate−ko | verdict, basket vs button) + ascii plot.
  Syntax-clean. Ready for when the sweeps + analyze_sweep complete.
- NEXT tick: monitor arms; when a sweep finishes, analyze_sweep (TRAIN+VALIDATION, --require-slurm-job) then
  make_rank_table → first defensible basket-vs-button rescue-vs-rank comparison.

## S-027 — 2026-10-02 — SCALE FIX: ~520s/arm → per-rank jobs (not all-ranks-in-one); launch ranks 1 & 16
- **Measured cost:** BASE arm = 521s over the full ~670-row population (whole-answer readout, batch 1). 346 arms
  in one job = ~50h >> 8h limit → the all-ranks jobs (965624/965625) were infeasible; killed them.
- score_behavior has only `--limit` (first-N, not domain-stratified) → no cheap row subsample. Keeping FULL rows
  (maximal power/defensibility, exact inherited population).
- **Design = one job per (codeword, rank):** liveness(4) + candidate + 46 rand + 10 shuf = 61 arms × ~520s ≈ 8.8h;
  bumped slurm `--time` to 20:00:00. Matches how the inherited expensive n46 runs were structured (one rank-family
  per job). Each job self-contained (own liveness) so analyze_sweep --require-slurm-job groups it cleanly.
- **Launched 4 jobs:** basket r1 (965765), basket r16 (965766) RUNNING on n-350; button r1 (965767), button r16
  (965768) PENDING (resources). Tests the DISSOCIATION ANCHOR (rank 1, inherited) vs a HIGH rank (16) for both
  codewords at full power — the directional H1 test ("does button need higher rank?").
- **NEXT tick:** confirm steady arm cadence (~520s) + pending jobs start (watch the 30-min pending rule); fill in
  ranks {2,4,8,32} after; analyze when a (cw,rank) completes.

## S-028 — 2026-10-02 — 3090s drained/contended → moved all 4 jobs to L40S (matched, CSI-approved)
- sinfo: most 3090 nodes DRAIN (only n-302/304/350 usable, busy) → 965767/768 would dead-wait ~9h (pending>30min
  rule). L40S nodes (n-801-805) available and are in the CSI-approved native-bf16 set (sm_89). a5000/a6000 also
  available (sm_86) but L40S is explicitly inherited-approved.
- Killed all 4 (basket staging had no compute done — only ~28min stage lost) and relaunched ALL on **L40S** so the
  headline **basket-vs-button comparison is hardware-matched**: basket r1 (965838), basket r16 (965839), button r1
  (965840), button r16 (965841) — all RUNNING on n-803, parallel, no pending. Hardware for these runs = L40S
  (note alongside the inherited 3090 results; both native-bf16, CSI lists them interchangeably; verify robustness
  if a verdict is marginal).
- NEXT tick: watch staging (4 parallel source reads on n-803 → may be slow) + arm cadence on L40S (likely faster
  than 3090's 520s); analyze each (cw,rank) as it completes → first matched dissociation signal (rank 1 vs 16).

## S-029 — 2026-10-02 — BUG: scancel littered node /tmp → ENOSPC; fix staging (SLURM_TMPDIR + TERM trap + df precheck)
- All 4 L40S jobs FAILED in 22s: `OSError [Errno 28] No space left on device` at the preflight mktemp. Root cause:
  my EXIT-only cleanup trap does NOT fire on `scancel` (SIGTERM), so every killed job left its ~30G node-local
  stage behind, filling nodes' /tmp (n-803 was full before the job even staged). The repeated kill/resubmit cycles
  caused this.
- **FIX in rescue_sweep.slurm:** (1) `export TMPDIR="${SLURM_TMPDIR:-/tmp/$USER/$JOBID}"` so mktemp + stage live in
  SLURM-managed per-job scratch (auto-cleaned on scancel); (2) `trap ... EXIT TERM INT` (clean on kill too);
  (3) a fast **df pre-check** (needs ~36G node-local; else exit 1 in seconds — no cryptic ENOSPC, no wasted stage).
  `bash -n` clean.
- Relaunched basket/button × ranks {1,16} → 965927-30 on L40S (`--exclude=n-803,n-302`), PENDING for L40S slots.
- ⚠ NOTE: killed-job /tmp litter from earlier runs still sits on n-304/n-350/n-803 (cannot rm node-local from
  login; SLURM/node reboot or the owner's cleanup reclaims it). The df precheck now routes jobs AWAY from full
  nodes automatically.
- NEXT tick: confirm 965927-30 start + pass df precheck + stage + arm cadence on L40S.

## S-030 — 2026-10-03 — df precheck works; lean staging (skip `original/` 30G->16G); 4 (cw,rank) jobs in flight
- df precheck validated: 965928 passed (t-806, staging + PREFLIGHT_OK 57 arms); 965927/929/930 fast-failed in
  <7s with INSUFFICIENT_TMP on n-801 (33.6G free) — no wasted stage, exactly as designed.
- **Stage reduced 30G->16G:** the 30G was the snapshot's `original/` subdir (consolidated .pth duplicate).
  from_pretrained needs only the 4 safetensors (16G) + config/tokenizer/index jsons. Staging now copies just
  those; df threshold lowered 36G->18G (fits far more nodes). `bash -n` clean.
- In flight: basket r16 (965928, RUNNING t-806, old 30G stage — fine); resubmitted basket r1 (966084),
  button r1 (966085), button r16 (966086) with lean staging, PENDING for L40S.
- NEXT tick: 965928 arm cadence on L40S (expect faster than 3090 520s); pending jobs start + lean-stage fast;
  analyze each (cw,rank) as it completes → first matched rank-1-vs-16 dissociation signal.

## S-031 — 2026-10-03 — cadence confirmed ~517s/arm (L40S=3090, readout-bound); 4 (cw,rank) jobs progressing
- basket r16 (965928): BASE arm = 517.6s → ~517s/arm is FIXED (L40S not faster than 3090; the whole-answer
  readout over ~670 rows is CPU/IO-bound, not GPU-bound). 61 arms/job => ~8.75h/job (20h limit ample).
- In flight: basket r16 (965928, t-806, arm 1/61 done), basket r1 (966084, n-801, staging), button r1 (966157)
  + button r16 (966158) PENDING (L40S, excl full nodes n-803/804/302). L40S /tmp broadly tight (my scancel litter
  + others); df precheck routing around it.
- **Trade-off noted for the FULL 6-rank sweep:** 12 jobs × 8.75h is heavy. These 4 full-row jobs give the key
  rank-1-vs-16 dissociation at FULL power (defensible). For the remaining ranks {2,4,8,32}, consider a
  domain-stratified subset bank (~3 rows/domain → ~2.6min/arm, ~2.6h/job) — a declared power trade-off — decided
  AFTER seeing these effect sizes.
- NEXT tick: monitor arm progress (no action unless a job dies); analyze_sweep each (cw,rank) when it hits 61/61.

## S-032 — 2026-10-03 — monitor: all 4 (cw,rank) jobs healthy on L40S; lean staging confirmed
- basket r16 (965928) 3/61, basket r1 (966084) loaded, button r1 (966157) 3/61, button r16 (966158) model loading
  after **STAGE_IN done size=15G** (original/-skip lean stage CONFIRMED working). All RUNNING, ≤6 cap, no failures,
  ~517s/arm. Each completes in ~8-9h. No action; analyze each at 61/61.

## S-033 — 2026-10-03 — monitor (jobs ~20%); built domain-stratified row-reduction tool for the remaining ranks
- 4 jobs healthy (~12/61 arms each). Population structure: after SOW exclusion = 670 rows = 67 TRAIN domains ×
  10 rows (5 dev + 5 heldout sub-splits); analyzer applies the train/val/test domain split.
- Built `research/heretic_csi/make_stratified_exclusion.py`: keeps K rows/domain (deterministic sort by
  split,family_slot,prompt_id) by UNIONing the base SOW exclusion with the overflow prompt_ids — reuses
  score_behavior's --exclude-prompt-ids (no bank edit), all 67 domains retained. Generated K=4 exclusions
  (`runargs/heretic_csi/exclude_{basket,button}_K4.txt`): verified 268 rows = 67×4. ~2.5x faster (~210s/arm,
  ~3.5h/job). Added slurm arg7 to override the exclusion file. DECLARED power trade-off (noisier domain means).
- Plan: headline rank-1-vs-16 uses FULL rows (the 4 running jobs). Remaining ranks {2,4,8,32} will use K4 subset
  (feasible) IF the full-row results show an effect worth mapping — decided after they land.
- NEXT tick: monitor; analyze at 61/61.

## S-034 — 2026-10-03 — self-check PASS: candidate rescue writes NONZERO delta (not a silent null); jobs ~30%
- Verified on basket KO_CAND_r16 (completed, 670 rows): `fired=true, wrote_nonzero=true`, delta_norm_mean=1.16,
  written_norm_mean=0.272, captured_energy_frac_mean=0.178 (rank-16 subspace captures ~18% of the KO->clean
  difference energy), n_positions=28, norm_match_degenerate=0. So the subspace rescue is genuinely applied — rules
  out the "rescue writes ~0 == indistinguishable from never fired" bug class (plan §3 self-check).
- All 4 jobs healthy (~16-18/61 arms), 0 hook leaks/OOM. On track (~4-5h remaining).
- NEXT tick: monitor; analyze_sweep at 61/61 (first matched rank-1-vs-16 dissociation).

## S-035 — 2026-10-03 — ~4h REVIEW of the analysis path: rank-matched control scoping CONFIRMED correct
- Verified in `scripts/dcs_csi_subspace_analyze.py`: the control family is built from the `--arms` list
  (line 518 `arms=a.arms.split(',')`) filtered by `--control-prefixes` (line 956) — it does NOT glob all-rank
  `KO_RAND_*` dirs. Since analyze_sweep passes ONLY that rank's arms, the control family is genuinely RANK-MATCHED
  (candidate rank-r vs rank-r controls). Analyzer also REFUSES if candidate/comparator/norm-match is inside the
  control family (line 966). require_slurm_jobs parsed from --require-slurm-job disambiguates stale dirs.
- Hardening: analyze_sweep now passes `--expect-n-controls = len(sweep)-1` so a MISSING control run dir (a failed
  arm) fails the analysis loudly rather than silently shrinking the family. PY syntax clean.
- Jobs ~48% (33/61 ish), 0 failures, ~2h remaining.
- NEXT tick: monitor; analyze at 61/61.

## S-036 — 2026-10-03 — first 2 (cw,rank) jobs DONE; analysis unblocked (stale-dir crash + bash-timeout)
- **DONE:** basket r16 (965928, 61/61 rc=0) + button r1 (966157, 61/61 rc=0). basket r1 (966084) 57/61, button r16
  (966158) 58/61 — finishing soon.
- Two analysis snags fixed (NOT science bugs):
  1. `strict_run_dir`'s completeness loop CRASHED on a stale killed-job KO dir (965462: DONE.json, status
     INCOMPLETE, rows_written=0, NO results.jsonl) — it reads results.jsonl before the slurm-job filter runs.
     Can't rm it (permission), so wrote an empty results.jsonl there → now cleanly REJECTED (0≠670), no crash.
     (Only 1 such dir across hcsi_p2a_*.)
  2. The `ANALYZER_ERROR` was my 118s BASH timeout killing the analyzer mid-bootstrap (20000 draws × 56 controls
     is slow, ~2-3min), NOT a code error — direct run completed exit 0. Fix: run analyze_sweep in background (no
     timeout).
- Launched basket r16 + button r1 analyses in background (bzb8ihqal, bzn67m0vv) → SUMMARY jsons incoming.
- NEXT tick: read the first real verdicts (gates + recovery + rank test); when basket r1 + button r16 finish,
  complete the matched rank-1-vs-16 per-codeword comparison + make_rank_table.

## S-037 — 2026-10-03 — analysis fix: allow-short for norm-match degeneracy drops (controls lose up to 6 rows)
- Real cause of button-r1 ANALYZER_ERROR: control arms drop a few rows to NORM-MATCH DEGENERACY (control can't
  match the candidate's norm at some positions). Button r1 (job 966157) control row counts: 22×670, 23×669,
  8×668, 2×667, 1×664 (KO_RAND_r1_6 drops 6). strict_run_dir with allow_short=0 (then my first try =4) rejects
  the 664 arm → "0 complete". Inherited standard is `--allow-short 4`, but one control here drops 6.
- FIX: analyze_sweep `--allow-short` default 20 (~3%; still rejects a truly broken arm via the rows_written==
  n_lines consistency check). The analyzer intersects (domain,slot) keys across arms, so short arms don't bias
  domain means — admission just needs to cover the worst degeneracy drop. (NOT a science change.)
- Also neutralized the one stale DONE-but-no-results crash dir (S-036). Re-running button r1 + basket r16 TRAIN.
- NEXT tick: read the first real verdicts (both TRAIN); finish basket r1 + button r16 when their jobs complete →
  matched rank-1-vs-16 per codeword + make_rank_table.

## S-038 — 2026-10-03 — FIRST DEFENSIBLE RESULT: basket rank-16 TRAIN = DOES NOT PASS (dose-confounded)
- **basket r16 (TRAIN, n_domains=67, 56 rank-matched controls):** gates ALL PASS (manip/identity/instrument);
  recovery_fraction = 0.1667 [0.1272, 0.2053]; **VERDICT DOES NOT PASS** — candidate ranks 10/57, rank p=0.1754
  (floor 0.0175); 9 controls recover >= it. "INSIDE the controls, not above them."
- INTERPRETATION (preliminary, TRAIN only): at rank 16 a PLS subspace recovers ~17% of whole-state but random
  rank-16 subspaces recover as much → the rank-16 candidate is DOSE/DIMENSIONALITY, not a specific carrier. With
  the inherited basket rank-1 PASS (1/47), this says basket's installed meaning is a LOW-RANK-SPECIFIC direction;
  adding dimensions does not give a MORE specific operator (it just adds generic dose any subspace matches).
  ⚠ TRAIN only; VALIDATION needed before any claim; and this is the PLS/axis-family candidate (not yet an
  ARA-optimized operator — that's P2b).
- button r1 analysis running; basket r1 (966084) + button r16 (966158) jobs finishing → full matched comparison next.

## S-039 — 2026-10-03 — button r1 TRAIN = DOES NOT PASS (recovery ~0); last 2 analyses launched
- **button r1 (TRAIN, 67 domains, 56 controls):** gates ALL PASS; recovery_fraction = -0.0009 (≈ zero);
  VERDICT DOES NOT PASS — ranks 23/57, rank p=0.4035. The rank-1 PLS candidate recovers ~nothing for button and
  is mid-pack among controls. Consistent with the inherited button rank-1 NEGATIVE.
- TRAIN verdicts so far: basket r16 DOES NOT PASS (recovery 0.167, dose); button r1 DOES NOT PASS (recovery ~0).
- Launched final TRAIN analyses: basket r1 (966084) and button r16 (966158) — the latter is the key H1 test
  (does higher rank rescue button?). Awaiting.
- NEXT: assemble make_rank_table (basket vs button, r1 vs r16, TRAIN); then VALIDATION for all 4 before any claim.

## S-040 — 2026-10-03 — FIRST HEADLINE (TRAIN, PLS candidate, NOT yet certified): rank does NOT rescue button
All gates PASS (manip/identity/instrument), n_domains=67, 56 rank-matched controls (floor 0.0175, well-powered).

| codeword | rank | recovery_fraction | rank in 57 | rank-p | verdict (rank-1 rule) |
|---|---|---|---|---|---|
| basket | 1  | 0.0275 [0.008,0.047] | **2/57**  | 0.0351 | DOES NOT PASS (rank-1); **PASS under rank<=2 (AM-48)** |
| basket | 16 | 0.1667 [0.127,0.205] | 10/57     | 0.1754 | DOES NOT PASS (dose) |
| button | 1  | -0.0009              | 23/57     | 0.4035 | DOES NOT PASS (recovers ~nothing) |
| button | 16 | 0.1180 [0.096,0.140] | 10/57     | 0.1754 | DOES NOT PASS (dose) |

**READING (preliminary, TRAIN-only):**
- The inherited **codeword dissociation replicates at rank 1**: basket's rank-1 PLS direction sits near the top
  of its controls (2/57, p=0.035 ~ "specific") while button's recovers ~nothing and is mid-pack (23/57, p=0.40).
- **Higher rank does NOT give either codeword a *specific* carrier.** At r16 both recover more (basket 0.167,
  button 0.118) but BOTH rank 10/57 (p=0.175) — i.e. a random rank-16 subspace recovers just as much. The extra
  recovery is generic DOSE/dimensionality, not a button-specific mechanism.
- => Prereg outcome **D** (button remains resistant even at high rank) + partial **B**: the basket-vs-button
  dissociation is about the EXISTENCE of a specific low-rank direction (basket has one, button does not), NOT
  about button needing a higher-dimensional operator. Adding dimensions helps both only as much as any subspace.

**WHAT WE CANNOT SAY YET (honesty contract):**
- TRAIN only — NOT certified. VALIDATION is the certifying split (launching now).
- These are **PLS/axis-family candidates** (the inherited rank-1 method extended to more ranks), NOT yet an
  ARA-OPTIMIZED weight operator (that is P2b). This answers H1 for the activation-space PLS family only.
- basket r1 = rank 2/57: the AM-48 rank-1-vs-rank<=2 choice flips its verdict — report BOTH; do not pick silently.
- No behavioral/ASR claim; this is semantic-installation rescue (rung-1-style sufficiency) only.
- Only ranks {1,16} so far; the intermediate ranks {2,4,8,32} (K4 subset) fill the curve.

## S-041 — 2026-10-03 — VALIDATION (certifying) runs launched for ranks 1 & 16
- Launched 4 validation sweeps (arg7 = exclude_<cw>_bomb_sow_validation.txt; 23 val domains x10 ~230 rows, ~3x
  faster than train): basket r1 (968528), basket r16 (968529), button r1 (968530), button r16 (968531). PENDING L40S.
- These CERTIFY the S-040 TRAIN headline on the held-out validation split. (TEST remains spent — never used.)
- Next after validation lands: fill intermediate ranks {2,4,8,32} via the K4 subset bank (feasible), run
  make_rank_table for the full curve, and begin P2b (the ARA-optimized WEIGHT operator) + P3 SVD.

## S-042 — 2026-10-03 — validation moved to a5000 (L40S pended >30min); running
- 968528-31 pended >30min on L40S (contended). Moved to a5000 (sm_86 native-bf16, 3090-class, CSI-approved family):
  basket r1 (968532), basket r16 (968533), button r1 (968534) on n-501; button r16 (968535) on n-503 — all RUNNING.
- Note: TRAIN headline ran on L40S, validation on a5000 — a cross-hardware replication (bonus robustness; both
  native bf16; inherited used 3090/L40S interchangeably). Will note the hardware in the result.
- NEXT tick: monitor (validation ~3h on 230 rows); analyze --split validation when done => certify/deny S-040.

## S-043 — 2026-10-03 — P5/C1 QUANTIFIED (TRAIN LOO): basket better probe (+12%); decodability != rescue-specificity
- Probe quality (TRAIN LOO rho, from the ranksweep axis .json; layer 18, behavioral fit):
  - basket: rank-1 LOO rho = 0.5629 (peaks r3=0.6407); button: rank-1 LOO rho = 0.5042 (peaks r7=0.5889).
  - shuffled-label null ~0 (basket -0.052, button +0.017) => both codewords DECODABLE; basket's rank-1 probe is
    +0.0587 (~12% rel) better. **C1 replicated** (inherited: 0.5629 vs 0.5021, +12%).
- KEY OBSERVATION (links P5 to S-040): button's DECODABILITY rises with rank (peaks r7=0.589) yet its causal
  RESCUE never becomes specific (S-040: button r1 23/57, r16 10/57, both fail vs rank-matched controls). So
  **decodability and causal-rescue-specificity DISSOCIATE** for button — the concept is linearly readable but not
  rescuable by a specific low-rank operator at any tested rank. (Echoes the inherited decodability!=causality /
  representation!=behavior theme.)
- SCOPING: TRAIN LOO rho only (NOT held-out; a held-out probe rho still does not exist, same gap the inherited C1
  flagged). Descriptive geometry; not a causal test by itself. basket's modestly-better probe is a LIVE partial
  explanation for why basket (not button) has a specific rank-1 carrier — but 12% probe-rho does not obviously
  explain a 2/57-vs-23/57 rescue gap, so "better probe" is necessary-maybe, not clearly sufficient.

## S-044 — 2026-10-03 — P3 geometry (descriptive): same geometry, different causal efficacy
- cos(basket rank-1 axis, button rank-1 axis) = **0.557** (4096-D; well above chance ~0) => the codewords use
  MODERATELY ALIGNED directions, not geometrically distinct ones.
- PLS subspaces are NESTED (deflation): the rank-1 direction is captured 0.989 by rank-4, 1.0 by rank-16/32 for
  BOTH codewords. So rank-16 = rank-1 carrier + 15 generic "dose" dimensions.
- basket-r16 vs button-r16 subspaces heavily overlap: principal cosines 0.96/0.94/0.94/0.92/0.91, mean cos^2=0.46.
- SYNTHESIS (geometry paired with the S-040 causal rescue test): basket & button recruit geometrically SIMILAR
  directions/subspaces, yet their causal rescue DISSOCIATES (basket rank-1 specific 2/57; button never specific).
  => the dissociation is NOT "different directions" but **same geometry, different causal efficacy** — coherent
  with S-043 (button decodable + probe rises with rank, yet not rescuable). The puzzle sharpens: button's concept
  is decodable AND lives in a basket-like subspace, but adding back that subspace does not causally reinstall it.
- SCOPING: cosine/principal-angle = DESCRIPTIVE geometry; the causal claim rests on the rescue rank test (S-040),
  TRAIN-only until validation certifies. No held-out geometry yet.

## S-045 — 2026-10-03 — deliverable #4 table generated (TRAIN); validation ~37%
- make_rank_table.py works; wrote reports/heretic_csi/RANK_TABLE_train.md (regenerable; not committed per the
  research/+external_md commit scope). Recovery-vs-rank: basket r1=0.028 r16=0.167; button r1=-0.001 r16=0.118;
  all FAIL the rank test (basket r1 = the 2/57 borderline; AM-48 rank<=2 would pass — see S-040).
- Validation jobs ~22-23/61 arms on a5000 (~2h left). No failures.
- NEXT: certify on validation; then decide the next big build — P4 (head-restricted rescue, links to the 8-head
  circuit), P6 (fresh codewords = generalize the "specific low-rank direction" finding, highest paper value), or
  P2b (ARA weight operator, Heretic-native confirmation).

## S-046 — 2026-10-03 — ~4h ADVERSARIAL REVIEW (tried to kill the headline): survives
Attempted to break S-040/043/044 before validation lands:
- **NOT domain-floor-limited** (the inherited behavioral-recovery failure mode): all 4 verdicts use n_domains=67
  and recovery.n_domains_with_movement=67 — recovery estimated over ALL 67 train domains, tight CIs. (Inherited
  behavioral recovery rested on 5 informative domains; this does not.)
- **button r1 recovery = -0.0009 CI [-0.0115, 0.009]** — tightly on ZERO across 67 domains (robust null, not a
  noisy few-domain artifact). basket r16 0.167[0.127,0.205], button r16 0.118[0.096,0.140] clearly positive (dose).
- **rank-test well-powered:** floor 0.0175 (57 controls) << 0.05, so r16 "DOES NOT PASS" (10/57) are CERTIFIED
  negatives, not floor-limited.
- Dissociation gap at r1 is large (basket 2/57 recovery 0.028 vs button 23/57 recovery ~0) — not a borderline.
- SURVIVING caveats (all already logged, none fatal): TRAIN-only (validation in flight); PLS/axis candidate NOT
  the ARA weight operator (P2b); AM-48 flips basket-r1 pass/fail; basket's bank has more option-mass-degraded
  rows (unmatched caveat, inherited); no behavioral/ASR claim.
- Verdict of review: the headline is defensible pending validation; no overclaim detected in the log.
- Validation jobs ~3h elapsed on a5000, healthy (~1h left).

## S-047 — 2026-10-03 — validation jobs completing; certifying analyses launched
- Validation arm row count = 230 (23 val domains x10). basket r1 (968532) + button r16 (968535) DONE; analyses
  launched (--split validation --expect-n 230 --allow-short 20). basket r16 (968533) + button r1 (968534) at 60/61.
- NEXT tick: read the 2 validation verdicts; analyze the last 2; assemble the TRAIN+VALIDATION matched table.
  Certification criterion: does the dissociation (basket r1 specific vs button r1 null; both r16 dose-fail)
  REPLICATE on validation (a5000, held-out domains)?

## S-048 — 2026-10-03 — VALIDATION CERTIFIES the dissociation direction (2 of 4 cells in)
Held-out validation, 23 val domains, a5000 (cross-hardware vs TRAIN's L40S); gates all PASS.
- **basket r1: PRIMARY PASSES on VALIDATION** — strictly largest of 56 controls, rank p=0.01754 < 0.05
  (recovery 0.0359 [0.013,0.066]). Basket's rank-1 carrier CERTIFIES held-out (cleaner than TRAIN's 2/57), and
  on DIFFERENT hardware => cross-hardware robust. This is a DEFENSIBLE positive (rung-1-style sufficiency rescue).
- **button r16: DOES NOT PASS on VALIDATION** — ranks 10/57, p=0.1754 (floor 0.0175, well-powered). Higher rank
  does NOT give button a specific carrier on held-out data either. DEFENSIBLE negative.
- Awaiting basket r16 (968533) + button r1 (968534) validation analyses to complete the matched 2x2.
- INTERPRETATION so far (now VALIDATION-backed): basket has a specific, certifiable rank-1 installation carrier;
  button is not rescued at rank 1 (TRAIN null) nor rank 16 (TRAIN+VAL certified fail). The dissociation is about
  the EXISTENCE of a specific low-rank causal direction, not dimensionality (prereg D). Still PLS/axis candidate,
  not the ARA weight operator; no behavioral claim.

## S-049 — 2026-10-03 — HEADLINE CERTIFIED (TRAIN + VALIDATION): dissociation = specific low-rank direction, NOT dimensionality
Full matched 2x2 (gates PASS all cells; 56 rank-matched controls, floor 0.0175; TRAIN=L40S/67dom, VAL=a5000/23dom):

| cell | TRAIN rank/p (recovery) | VALIDATION rank/p (recovery) | verdict |
|---|---|---|---|
| basket r1  | 2/57 p=0.035 (0.028) | **1/57 p=0.0175 (0.036)** | **PASS on VALIDATION** (TRAIN borderline/AM-48) |
| basket r16 | 10/57 p=0.175 (0.167) | 10/57 p=0.175 (0.152) | FAIL both (dose) |
| button r1  | 23/57 p=0.40 (-0.001) | 14/57 p=0.246 (0.008) | FAIL both (recovers ~0) |
| button r16 | 10/57 p=0.175 (0.118) | 10/57 p=0.175 (0.118) | FAIL both (dose) |

**CERTIFIED FINDING:** basket has a specific, held-out-certifiable RANK-1 installation-rescue direction
(VALIDATION rank 1/57, p=0.0175, cross-hardware L40S->a5000). Button has NO specific carrier at rank 1 OR rank
16 (all fail, well-powered). Higher rank rescues NEITHER codeword beyond generic dose (both r16 ~ random rank-16).
=> The basket-vs-button dissociation is about the EXISTENCE of a specific low-rank causal direction, NOT about
button needing higher dimensionality (prereg outcome **D**, TRAIN+VAL). New vs inherited: adds the full rank
sweep + rank-matched controls at every rank, cross-hardware validation, and the decodability!=rescue-specificity
+ same-geometry!=same-causality framings (S-043/S-044).

### WHAT WE CAN DEFEND (this sprint, so far)
- basket's rank-1 installation-rescue direction CERTIFIES on held-out validation (p=0.0175) and is cross-hardware.
- Higher rank (16) does NOT give EITHER codeword a specific carrier — both r16 are certified fails vs rank-matched
  controls (the extra recovery is dimensionality/dose any subspace matches). Dissociation != dimensionality.
- C1 replicated: basket rank-1 probe LOO rho +12% over button (both decodable); button decodability rises with
  rank yet rescue never specific (decodability != rescue-specificity).
- basket & button recruit geometrically similar directions (rank-1 cos 0.56; r16 subspaces overlap) => same
  geometry, different causal efficacy.

### WHAT WE MUST NOT SAY
- NOT the ARA-optimized WEIGHT operator yet (these are PLS/axis-family activation-space candidates; P2b pending).
- NO behavioral/ASR claim (semantic-installation rescue only; rung-1-style sufficiency).
- basket r1 TRAIN is 2/57 (passes only under AM-48 rank<=2); the clean PASS is the VALIDATION 1/57 read.
- button's "no carrier" is scoped to the tested ranks {1,16} and the PLS family; not "button is uninstallable".
- TEST never used (spent). Only 2 codewords => a 2-point dissociation, not yet a population law (P6 = generalize).
- basket's bank has more option-mass-degraded rows than button's (unmatched caveat, inherited).

## S-050 — 2026-10-03 — fill rank-sweep curve: intermediate ranks {4,8} launched (K4 subset, TRAIN)
- Headline certified (S-049). Now completing the {1,2,4,8,16,32} curve middle: basket r4 (969085), basket r8
  (969086), button r4 (969087), button r8 (969088) on a5000, K4 domain-stratified subset (268 rows, ~3.5h), TRAIN.
- These are CURVE-SHAPE (K4 subset = fewer rows/domain than the full-row headline cells; declared trade-off) —
  they test WHERE basket loses rank-1 specificity (only r1? or r2-8 too) and confirm the dose monotonicity. The
  certified PASS/FAIL headline stands on full-row r1/r16 (S-049), not on these.
- Parallel plan: begin P2b design (ARA-optimized WEIGHT operator ΔW=BA on o_proj/down_proj via operator_ara +
  the KO capture) — the plan's literal novel step; and P6 (generalize across screen-viable codewords).
- NEXT tick: monitor; analyze {4,8} when done; extend table to {1,4,8,16}.

## S-051 — 2026-10-13 — RESUME after 10-day gap; rank {4,8} TRAIN analyzed; button-r4 TRAIN pass → prereg'd VALIDATION test
- **Resume / ops.** User re-issued the sprint mandate; recorded VERBATIM at
  `external_md/HERETIC_CSI_SPRINT_MANDATE_VERBATIM.md` (this log remains the authoritative plan+progress).
  30-min ops loop re-armed (session cron); ~4h adversarial reviews continue. No jobs were running.
- **S-050 jobs (969085-88) validated** by log (not sacct): each `DONE_MARKER ... rc=0`, 61/61 arms ok, 1 model load,
  no hook leak.
- **BUG/OPS (mine, now fixed):** running `analyze_sweep.py` per-rank in parallel CLOBBERED
  `reports/heretic_csi/hcsi_p2a_<cw>_SUMMARY_train.json` (all runs wrote the same name). The r1/r16 TRAIN summary files
  from S-049 are therefore overwritten; the per-rank analyzer jsons and this log's S-049 table remain the record.
  Fix: summary filename now includes the ranks (`..._SUMMARY_r<ranks>_<split>.json`).
- **PREEMPTION duplicates (new mechanical attrition rule, declared before reading any endpoint):** 969085 (n-501→n-503)
  and 969088 (n-501→n-501) were preempted+requeued on `killable`, leaving complete-looking duplicate run dirs with the
  same `slurm_job_id`; the frozen analyzer correctly refused. Rule: keep only dirs whose RUNMETA `hostname` == the job
  log's final `SWEEP DONE ... HOST=` AND `start_ts` ≥ the log's last `STAGE_IN start`. Exactly 61 dirs/job remain; the
  49 first-attempt dirs were MOVED (not deleted) to `outputs/boombness/score_behavior/_preempted_attempts/`.
  Independent verifier (F3) asked to re-check the rule.
- **TRAIN rank curve (PLS activation-space rescue, L18 rel-6, 56 rank-matched controls, floor 0.0175).**
  r1/r16 = full 67-domain rows (S-049); r4/r8 = K4 domain-stratified subset (268 rows, 63-67 domains).

  | codeword | r1 | r4 (K4) | r8 (K4) | r16 |
  |---|---|---|---|---|
  | basket rank/57 (recovery) | 2 (0.028) | 3 (0.132) | 4 (0.131) | 10 (0.167) |
  | button rank/57 (recovery) | 23 (−0.001) | **1 (0.090) PASS** | 3 (0.102) | 10 (0.118) |

  Liveness on these jobs: KO_SELF−KO ≈ 0 (button r4: −0.0008 [−0.003,0.001]); KO_FULL−KO > 0 (0.109–0.142).
- **Reading (TRAIN, NOT a finding):** button's candidate is near-top at ranks 4–8 (1/57, 3/57) but not at r1 or r16;
  basket is near-top at r1–r8 and dilutes by r16. If real, this is the outcome-A shape (basket specific from rank 1,
  button needs rank ~4), contradicting a too-broad reading of S-049 ("button has no carrier") — S-049 tested only
  {1,16}. BUT four ranks were examined per codeword on TRAIN ⇒ multiplicity (~4×0.0175 ≈ 0.07 family-wise) and r4/r8
  are on the K4 subset. **Must not be quoted.**
- **PREREGISTERED (committed `532d220d` BEFORE launch):** `configs/heretic_csi/prereg_S051_rank4_validation.json`
  (sha256 `e170da61…`). PRIMARY = button r4 on VALIDATION (230 rows/23 domains, a5000, frozen analyzer rule: strictly
  largest of 56 controls), single confirmatory test; basket r4 descriptive. Interpretations frozen for PASS/FAIL.
  **Launched:** 1022698 (button r4 val), 1022699 (basket r4 val).
- **Parallel workstreams launched (subagents; parent owns this log + commits):**
  F1 = P0 Phase-A Heretic env + base→modify→reset audit + Phase-B native last-position ARA control;
  F2 = P1/P2b position-aware WEIGHT-space operator ΔW=BA rank sweep {1..50} with rank-matched controls, ΔW saved for P3;
  F3 = independent re-computation of S-049 + r4/r8 (own code, mutation tests);
  F4 = P5/P6 codeword provenance/contamination table, frequency, power design, held-out probe quality (CPU).
  GPU budget: parent 2 + F1 ≤2 + F2 ≤2 ≤ 6.

## S-052 — 2026-10-13 — INDEPENDENT VERIFICATION (F3) of S-049 + S-050 K4: all verdicts reproduce; two caveats
- From-scratch code (`research/heretic_csi/verify/verify_s049.py`, did not reuse the analyzer), report
  `reports/heretic_csi/VERIFY_S049_independent.{md,json}`.
- **Reproduced (BASE-referenced option-mass floor = analyzer rule):** basket r1 VAL 1/57 p=0.0175 recovery 0.036;
  basket r16 10/57 (TRAIN 0.167 / VAL 0.152); button r16 10/57 (0.118 / 0.118); button r1 FAILS (TRAIN 25/57, VAL
  18/57; recorded 23 / 14). K4 r4/r8 match the analyzer exactly (basket 3,4; button **1**,3).
  Rank-1 ±1–4 rank shifts trace to norm-match-degenerate row drops (mechanical); no verdict changes.
- **Integrity PASS:** no TEST domain anywhere; split membership correct; every control is truly rank-r (matrix_rank)
  and norm-matched (rel err ≤6e-16); 57 distinct keys; KO−BASE −0.21…−0.30, KO_FULL+ 0.11…0.14, |KO_SELF−KO| ≤0.0008;
  mutation tests null (candidate↔control swap median p 0.32–0.54; within-domain arm shuffle 0.27–0.66).
  Preemption quarantine rule (S-051) verified against logs for all 12 jobs.
- **CAVEAT 1 — basket r1 is option-mass-floor-SENSITIVE (correction to how S-049 may be quoted).** With a stricter
  *paired* floor (drop a prompt if BASE, KO or KO_FULL < 0.05; drops 42% of basket TRAIN rows): TRAIN 5/57 p=0.088
  (fail), VAL 2/57 p=0.035 (still p<0.05 but not strictly largest). The BASE-only floor is the frozen, pre-treatment
  rule and stays primary (paired floor conditions on post-treatment arms), but **"basket r1 strictly largest" must
  not be presented as robust** — added to WHAT WE MUST NOT SAY.
- **CAVEAT 2 — button r4 K4-TRAIN 1/57 holds under every floor variant** (recovery 0.090 [0.068,0.114]); still
  TRAIN/K4 only and cannot survive Bonferroni over 4 ranks (floor 0.0175 > 0.0125). S-049's "outcome D" is
  PROVISIONAL pending the preregistered button-r4 VALIDATION test (S-051; jobs 1022698/99).
- Hygiene: r1/r16 analyzer jsons exist only un-split (pre-fix); F3's JSON regenerates both splits.

### WHAT WE MUST NOT SAY (addendum S-052)
- "basket r1 is robustly the strictly-largest of its controls" — it is floor-sensitive (paired-floor VAL 2/57).
- "button has no specific carrier at any rank" — r4 TRAIN passes; tested held-out ranks are {1,16} only until S-051 reads.

## S-053 — 2026-10-13 20:40 — ops tick: NFS stage-in contention (4 concurrent stagers)
- Running: 1022698/1022699 (prereg r4 VALIDATION, a5000), 1022701 (F2 P2b weight-operator, a5000), 1022704 (F1 Phase-A
  Heretic audit, L40S), 1022696 (F4 CPU probe job). No failures, no duplicates.
- **Problem:** all 4 GPU jobs began staging the same 16 GB snapshot from the cross-user NFS path within ~11 min;
  `srun --overlap du` shows ~2 GB staged per job after 20 min (≈7 MB/s aggregate) — the cold-NFS-load bottleneck the
  mandate warns about. NOT a hang (bytes increasing).
- **Action:** asked F1 to cancel/resubmit Phase-A after the others finish staging; F2 told not to submit more GPU jobs
  until current stage-ins finish. **Standing rule S-053:** never start a stage-in while another of our jobs is
  mid-stage-in (stagger), and batch arms per allocation.
- `sacct -u` also lists 3 ancient "RUNNING" records (740944/741053/741054, 64 days, other project) absent from
  `squeue` — stale accounting rows, not ours to act on in this sprint; ignored.
- Next: read STAGE_IN done; then verify arm cadence; prereg r4 VAL read when DONE_MARKER appears.

## S-054 — 2026-10-13 — P5/P6 (F4, CPU job 1022696, DONE_MARKER x2): C1 NOT SUPPORTED held-out; P6 staged design + power
- **Held-out probe quality** (fit TRAIN 67 dom → score VALIDATION 23 dom/230 rows; L18 rel-6; Spearman over
  within-domain-centred rows; 95% domain-cluster bootstrap):
  rank-1 basket **0.533 [0.434,0.631]** vs button **0.574 [0.497,0.653]**; full ridge 0.653 vs 0.647.
  Installer strength (C−A, one-word, n4): VAL basket 0.40 vs button **0.67** (TRAIN 0.48 vs 0.68).
- **Reading (MEASURED, n=2 codewords):** the TRAIN-LOO +12% basket probe advantage (S-043, inherited C1) does **not**
  replicate held-out: decodability is statistically indistinguishable (point estimate favours button) and button is
  the STRONGER installer. The certified dissociation (basket r1 rescue PASS / button FAIL) therefore occurs at equal
  held-out decodability ⇒ the surviving C1 explanation ("basket simply has a better probe") is **not supported**
  for this pair. Scoping: (i) 2 codewords — no population claim; (ii) the held-out statistic is within-domain-centred
  Spearman, not byte-identical to S-043's LOO rho definition; (iii) the shuffle null used only 20 within-domain
  shuffles (p floor 0.048) and one shuffle reached 0.42/0.52 — a large shuffle family is required before quoting any
  p; I'm treating the shuffle-max as an open check (adversarial review item).
- **Codeword pool (PR-CSI-008):** 25 lexical survivors; GPU screen never ran. Contaminated: basket, button. Excluded:
  carrot (pool placeholder — 9,396 hits in demo_pools — + early-DCS GPU use). candle = DEV-only (missile banks).
  **21 untouched**: lamp kettle pencil ladder blanket bucket pillow saddle wagon cushion curtain envelope bottle jacket
  ribbon sponge whistle yogurt banana chair balloon. Zipf range narrow (3.54–4.69) ⇒ frequency question low-power.
- **Cost/codeword (measured on basket):** bank+exclusions CPU minutes; readout 34 GPU-min; behavioral extraction
  33 GPU-min (MUST be slimmed to L18 — full grid 12 GB/codeword breaks the 200 GB cap); axisfit 6 CPU-min; r1 VAL
  rescue ~3.5 GPU-h ⇒ ~4.7 GPU-h/codeword. axisfit/rescue slurm hard-code cw paths (need generic branch).
- **Hardware provenance caveat (inherited, re-surfaced):** basket/button behavioral corpora behind every axis fit were
  extracted on V100 (emulated bf16); new codewords will be extracted on native-bf16 GPUs ⇒ incumbents and new
  codewords differ in extraction hardware. Must be stated in any P6 result.
- **Proposed frozen P6 design** (`reports/heretic_csi/P6_CODEWORD_PROVENANCE_AND_DESIGN.md`, written before any P6 GPU
  number): Stage-0 covariates for all 22 (~26 GPU-h) → mechanical gates G1 installer-strength CI-lo>0.05, G2 KO
  liveness, G3 option-mass (attrition in denominators) → DEV 6 (candle + 5 seeded 20261013 across freq tertile ×
  installer strength; basket/button as contaminated DEV points; ranks 1/4/16) → freeze → CONFIRM ~16 at r1 on VAL.
  Primary per-codeword outcome = r1 specificity z vs 56 rank-matched controls. H6a probe→specificity (1-sided),
  H6b frequency→specificity (2-sided), Holm. Power: n=2 CANNOT ANSWER; DEV 6 shakedown only (0.24–0.39);
  CONFIRM n=16 → 0.60/0.74/0.87 at ρ=0.6/0.7/0.8; MDE(80%) ρ≈0.75; if attrition leaves <12 → pre-label UNDERPOWERED.
- **Decision:** P6 Stage-0 GPU work is QUEUED behind P2b/P3/P4 per the priority order and the stage-in stagger rule;
  the design is adopted as the working plan and frozen in that file (any change gets a new S-entry).

## S-055 — 2026-10-13 21:10 — ops tick: staging slow but progressing; Phase-A deferred
- Running: 1022698 / 1022699 (r4 VAL; staged 6.9 / 5.5 GB of ~16 GB after 50 min), 1022701 (P2b; 5.5 GB). Throughput
  ≈1.7 MB/s per job from the cross-user NFS snapshot ⇒ stage-in ETA ~22:45–23:00, then ~3 h of arms (r4 VAL read
  expected ~02:00). Bytes increasing ⇒ not stalled. 1022704 (Phase-A) cancelled by F1 per S-053 stagger rule.
- Ops note: an `srun --overlap` progress probe hit its 60 s timeout and its own step (1022701.0) was cancelled; the
  batch step is unaffected (verified RUNNING). Future probes: `timeout` > srun runtime or `sattach`-free `du` only.
- No failures, no duplicates. Next: STAGE_IN done → check per-arm cadence.

## S-056 — 2026-10-13 21:40 — ops tick: staging 13 / 9.5 / 9.5 GB (accelerating, ~3.5 MB/s/job)
- 1022698 (button r4 VAL) 13 GB of ~16; 1022699 (basket r4 VAL) 9.5 GB; 1022701 (P2b) 9.5 GB. No failures/duplicates.
  Agents F1 (Phase-A/B) and F2 (P2b) still working; no new GPU submissions while staging (S-053 rule).

## S-057 — 2026-10-13 22:10 — ops tick: button r4 VAL (1022698) staged and scoring
- 1022698: STAGE_IN done; first arm running; KO pre-flight 230/230 rows ok (23 val domains), readout ids
  concept=[13054] codeword=[3215] (button) — correct population + ids. 1022699 (basket r4 VAL) and 1022701 (P2b) still
  staging. No failures/duplicates.

## S-058 — 2026-10-13 22:40 — ops tick: model mirror on /specific/scratches; P2b smoke PASSES plumbing
- **Stage-in bottleneck fix (F2):** byte-identical Llama snapshot mirrored to
  `/specific/scratches/scratch/omeryosef/models/llama31_0e9e39f2` (separate server from the contended netapp; copied
  from 1022701's node-local stage, so netapp wasn't re-read; VERIFIED marker + SHA256SUMS). Parent check: all 10 file
  sizes equal the snapshot's; shard blob names = sha256; independent re-hash in progress (shard 1 ✓ `2b1879f3…`).
  `rescue_sweep.slurm` now prefers the mirror when VERIFIED exists (STAGE_SOURCE logged), falls back to netapp;
  `p2b_job.slurm` likewise. Running jobs unaffected (SLURM copies the script at submit).
- **P2b smoke 1022701 (F2) DONE** (DONE_MARKER rc=0, 10/10 arms, 1 model load, 0 hook leaks, 2h03m mostly stage-in):
  codeword anchors verified (basket id 14351), KO_IDENT == KO exactly, KO_FULL live. Two design fixes made by F2
  before production: preserve set widened to 6 extra clean rows/prompt; neutral last-row control NOT norm-matched.
  (To be audited in the next adversarial review: is "not norm-matched" a rank/norm-mismatched control? — mandate §10.)
- Progress: 1022698 (button r4 VAL) 10/61 arms ok; 1022699 (basket r4 VAL) first arm 100/230 rows; 1022919 (F1
  Phase-A/B) running on n-805. No failures/duplicates. button r4 VAL read ETA ~02:00.

## S-059 — 2026-10-13 22:55 — mirror independently VERIFIED; P2b production launched (1023012)
- Parent re-hashed all 4 shards of the `/specific/scratches` mirror: sha256 == the netapp snapshot's LFS blob names
  for every shard (2b1879f3…, 09d433f6…, fc1cdddd…, 92ecfe1a…). Mirror is the verified stage source (5 s stage-in vs
  1h46m from netapp).
- **P2b production 1023012 (F2, n-503):** stage 1 = capture clean/KO module I/O at the codeword row on full TRAIN
  (670 rows × basket, button); TRAIN-CV objective selection (fitting-side criteria) → pooled freeze → basket fits at
  ranks {1,4,16,50} + liveness (~17 h). Parent asked F2 to (i) fill in {2,8,32} for both codewords and record the
  rank set before any endpoint, (ii) justify/report norm of the neutral-position control vs candidate ΔW (§10),
  (iii) confirm objective freeze uses no y_install.

## S-060 — 2026-10-13 — P2b PREREG frozen before any production y_install (F2)
- `outputs/heretic_csi/p2b/prod/PREREG_P2B.json` (sha256 4d0a6b5f…), committed now with 0 production score dirs on
  disk. Ranks fit {1,2,4,8,16,32,50} both codewords; eval pass 1 {1,4,16,50}, pass 2 {2,8,32}.
- Controls per (cw, rank): 46 RAND random-orthonormal rank-r, per-module Frobenius norm = CAND, same modules/layers/
  rank/#params + 5 SHUF (role-swap + domain-deranged pairing fits, rescaled to CAND norm) ⇒ 51 controls, floor 0.0192;
  analyzer VOIDs a cell on any norm/rank mismatch. NEUT (fit at last prompt row) kept at its own norm — its clean-vs-KO
  gap is tiny (smoke ‖ΔW‖ 2.6 vs CAND 172), and ×56 inflation collapsed option mass to 8e-5 (pathological); NEUT is
  therefore a *position* control reported with its achieved norm, NOT part of the rank-matched null family.
- Objective freeze: TRAIN-only, 5-fold domain-grouped CV on captured module I/O; score = held-out gap_closure −
  preserve_damage; {knn,mse,cos,whiten} × steer {0.3,1,3}, averaged over basket+button; y_install never read.
- **Correction (same entry):** the PREREG_P2B sha256 above ("4d0a6b5f…", as first reported by F2) is wrong; the
  actual hash (parent-recomputed, F2 confirmed) is **e273df1d…ced378**. Because `outputs/` is a symlink outside git,
  the frozen file is committed as a byte copy at `configs/heretic_csi/PREREG_P2B.json` (same sha256).

## S-061 — 2026-10-13 23:10 — ops tick
- 1022698 (button r4 VAL) 18/61 arms ok, 1022699 (basket r4 VAL) 14/61, 0 failures. 1023012 (P2b production) capturing
  TRAIN I/O (500/670 rows).
- F1: 1022919 (Phase-A/B) COMPLETED in 27 min (results pending F1's report); 1023043 FAILED at t=0 — node-local
  `/tmp` full on the assigned node ("mkdir /tmp/omeryosef: No space left on device"; node-side, not our data). F1 owns
  resubmission (exclude that node). Not a scientific result.

## S-062 — 2026-10-13 23:25 — P0 / PHASE A (F1, job 1022919): Heretic audit — gate FAILED by design; 2 real Heretic findings
Artifact `reports/heretic_csi/PHASE_A_heretic_audit_job1022919_r0.json` (L40S; isolated venv
`/specific/scratches/scratch/omeryosef/envs/heretic_csi` — torch 2.13+cu126, transformers 5.6.2; eager bf16 forced).
1. **Heretic ARA reset is NOT a full reset (upstream finding @662e4ba2).** `reset_model` zeroes `lora_B` only;
   `lora_A` retains the previous trial's values. Same params re-applied after reset ⇒ ΔW rel diff 1.08, max |Δlogit| 4.2;
   Optuna trial-0 objective 0.0706 vs replay 0.0513 ⇒ **shipped Heretic trials are history-dependent and not exactly
   replayable.** Our drivers restore `lora_A` to its post-`apply_lora` snapshot at every reset (documented deviation;
   no upstream patch). Candidate upstream bug report — NOT filed (outward-facing; user's call).
2. **Reset to identity itself is exact:** ΔW after reset = 0; greedy-16 tokens identical to base. Base vs
   LoRA-wrapped (B=0) max |Δlogit| 0.0625 (bf16 rounding of the wrapped path).
3. **Deployed ≠ optimized operator (upstream finding):** with default `preserve_row_magnitudes=True`, ARA's loss uses
   `normalize(W+BA)·‖W‖_row` but PEFT deploys `W+BA`; per-module relative gap 1–30% (max 0.298, L15 down_proj); on
   captured I/O the loss is similar for both (0.0279 deployed vs 0.0246 objective-form; base 0.207). Our P2b operator
   deploys exactly what it optimizes (no row-norm reparam) — keep it that way.
4. **Learned ΔW (tiny fixed config, L12–16, rank 8):** numerical rank 8 everywhere, but entropy-effective rank
   ≈1.0–4.0; down_proj L12/13/15 ≈1.0 (essentially rank-1); ‖ΔW‖/‖W‖ 0.02–0.35. (Descriptive; P3 template.)
5. **Cross-hardware readout noise (affects interpretation of OUR numbers):** the frozen `score_behavior` readout is
   bit-exact within a GPU type but differs ACROSS types (3090/L40S/a5000): mean |Δy_install| 0.009–0.013, max 0.25,
   |Δlogp| up to 0.87 (over existing hcsi_p2a BASE dirs, n≤670). F1's inline-scorer port: mean |Δy| 0.0088 vs frozen
   (gate set at ≤0.015 from this hardware envelope, not from any endpoint).
   **Implication audit (parent):** every certified rank-test cell is self-contained within ONE job on ONE GPU type
   (candidate + all 56 controls + liveness) ⇒ the verdicts are not cross-hardware confounded. BUT the descriptive
   rescue-vs-rank curve (S-051) mixes L40S (r1/r16) and a5000 (r4/r8, all VAL) — curve *recoveries* across those
   cells carry hardware noise; only within-cell ranks/p are clean. Recorded as a standing caveat.
6. Optuna JournalStorage resume works (2 trials → reload → 3). Llama chat template with empty system prompt is
   byte-identical to the CSI no-system template (date string stays "26 Jul 2024" under tf 5.6).
- Gate failed by design on (1)/(5-old gate); Phase B was skipped, fixes applied, **resubmitted as 1023182**
  (mirror stage-in, `--exclude=n-803`).

## S-063 — 2026-10-13 23:40 — ops tick
- r4 VAL: 1022698 (button) 27/61 ok, 1022699 (basket) 23/61 ok, 0 failures. P2b 1023012: fit stage, objective CV
  fold 1/5 done (898 s/fold; 670 paired prompts, 67 TRAIN domains, 26 modules). F1: 1023182 exited fast on
  INSUFFICIENT_TMP guard (no GPU wasted) → 1023185 running (Phase-A rerun), 1023251 Phase-B pending; F2 1023264 pending
  (BeginTime-deferred). Concurrency ≤6 GPU respected. Deep adversarial review due next tick (~00:00, 4 h since resume).

## S-064 — 2026-10-14 00:10 — ops tick + ~4h DEEP ADVERSARIAL REVIEW launched
- r4 VAL: button 36/61, basket 32/61 ok, 0 failures. P2b 1023012: objective CV fold 3/5. F1: 1023185 (Phase-A rerun)
  and 1023251 (Phase-B native ARA) running. F2 1023264 pending. 5 GPU running ≤6.
- **Deep adversarial review (4 h since resume):** delegated to a FRESH independent reviewer agent (no shared context
  with F1/F2 implementers), read-only, covering: token positions; source/target pairing & split leakage; rank+norm
  matching of controls (incl. NEUT exclusion); objective-freeze data flow (no y_install); domain-clustered statistic;
  norm confound; the S-054 held-out-probe shuffle-null anomaly (null max 0.42/0.52); requeue safety; overclaim audit
  of S-051…S-063; unit tests + mutation tests. Output → `reports/heretic_csi/REVIEW_ADVERSARIAL_20261014.md`.

## S-065 — 2026-10-14 00:30 — ~4h ADVERSARIAL REVIEW (independent reviewer): 2 CRITICAL + 5 HIGH; no result affected yet
Report: `reports/heretic_csi/REVIEW_ADVERSARIAL_20261014.md`. No P2b production endpoint had been read ⇒ all fixes
land BEFORE any P2b result (the frozen-before-endpoint discipline holds).
- **CRITICAL-1 (parent-confirmed by reading `p2b_fit.py:85-95`):** SHUF control's domain derangement by rejection
  sampling (1000 shuffles of 670 rows, 10/domain) almost never succeeds (expected ~9 same-domain collisions per
  shuffle ⇒ P(success)≈e^−9). Reviewer: 7/35 production seeds succeed; seed 1000 fails both codewords ⇒ **1023012 would
  SystemExit at basket r=1 after CV with no factors.** Fix: constructive derangement + 67×10 test; rerun with --freeze.
- **CRITICAL-2 (parent-confirmed `p2b_analyze.py:106-108`):** verdict PASSes on rank p alone; the prereg requires rank
  p<0.05 AND recovery CI-lo>0. Smoke shows norm-matched random/SHUF controls *damage* y by 0.17–0.28, so a candidate
  that merely damages less (negative recovery) would rank 1 and "PASS". Fix + mutation test.
- HIGH: option-mass screened only on BASE (smoke KO_NEUT: mass 8e-5, y=0.99 ⇒ fake rescue) → screen every arm.
- HIGH: "position-aware" applies to the FIT only; the edit is a real weight edit active at all positions incl. the
  Answer/readout rows (unconstrained by the preserve set) ⇒ a rescue could be lexical codeword-logit suppression. Need a
  codeword-row-only application arm + Δlogp_concept vs Δlogp_codeword decomposition before any position/mechanism wording.
- HIGH: NEUT (‖ΔW‖ ≈1.5% of CAND) is a size control, not a position control. HIGH: SHUF's 50% role swap cancels the
  KO→clean direction (weak fitted control; fitted-only family floor 1/6). HIGH: 7 ranks × "smallest passing rank" ⇒
  ~30% false-pass/codeword; Bonferroni 0.0071 < 51-control floor 0.0192.
- **Parent decision (PREREG AMENDMENT, to be filed by F2 before any production endpoint):** PRIMARY confirmatory
  ranks {1,4} per codeword, Holm over 2, ≥80 norm-matched controls (floor ≤0.0123); other ranks DESCRIPTIVE.
  Add a no-role-swap fitted control family. Record per-job code provenance (source copied into output dir).
- MEDIUM: uncommitted code in production (p2b_operator.py edited 23:41 during 1023012; phaseB_native_ara.py in
  1023251) — committed now as a snapshot; scorer declares but never applies its option-mass floor; Phase B maximizes
  y_install with no floor (F1 notified); per-module fits deployed jointly can compound.
- **Verified OK:** codeword-row capture correct (Answer suffix stripped, rel −10 decode-checked, right-padding, KO
  site = capture site per row); no VAL/TEST leakage (per-row split filter, domain-grouped CV); objective freeze never
  reads y_install; domain-clustered bootstrap; p-floor 1/(n+1) correct. Heretic reset finding (S-062) confirmed in
  source (`model.py:313` zeroes lora_B only).
- **S-054 correction (held-out probe):** reviewer re-ran rank-1 with 400 within-domain shuffles: real ρ reproduced,
  null SD 0.26, 95th pct ≈0.43, max 0.50/0.51 ⇒ p = 1/401 both codewords (the wide null arises because y_install
  correlates with single top PCs, |ρ| up to 0.40 — not a leak). BUT **"equal decodability" is an overclaim**: no
  paired test, CIs ±0.1, unequal y variance. Correct reading: **no evidence of a basket probe advantage held-out
  (C1 unsupported); a basket-vs-button decodability difference is CANNOT ANSWER.** S-054's wording is superseded by this.
- Tests: `pytest research/heretic_csi/tests` fails collection in poc_stage2 (heretic import) → importorskip; 23 other
  tests pass; that file 5/5 in heretic_csi env.
- Actions: fix list sent to F2 (items 1–9) and F1 (scorer floor, Phase-B floor, provenance). r4 VAL (P2a, frozen
  analyzer — unaffected by these P2b bugs) continues.

## S-066 — 2026-10-14 00:45 — F1 review fixes landed; PHASE B (native last-position ARA) interim — MEASURED
- F1 fixes: scorer applies the CSI option-mass floor (AM-53/54: key set fixed from BASE; reports y_floor,
  denominators, per-arm median option mass + `collapsed` flag), test 6/6. Phase-B freeze rule v2: KL ≤1.0 AND not
  collapsed; option mass logged per trial/read. Provenance: per-job src_snapshot + sha256s; the two running jobs
  (1023185 basket, 1023251 button) ran v1 — deltas in `reports/heretic_csi/phaseB/PROVENANCE_v1_jobs.md` (readout
  identical v1/v2). Both TRAIN-tuned; validation read once after freeze.
- **Phase-B interim, basket (1023185; TRAIN-chosen trial 5: layers 6–30, rank 50, KL_val_C 0.85):** frozen edit
  ΔY on VAL not-installed cell A **+0.925** (y 0.000→0.925, 23 domains); on VAL installed cell C **−0.124**; TRAIN reads
  A +0.914 / C −0.238. Spectrum-matched random controls (≥30/39 so far) ΔY ≈ 0.000.
- **Reading (MEASURED, not a verdict):** native ARA edits module outputs at the LAST prefill (= answer) position, so a
  large rise on cell A with a FALL on installed cell C is the signature of a context-free answer bias ("say bomb"),
  not coherent installation. Requested before any verdict: option mass on those reads (collapse check),
  Δlogp_concept vs Δlogp_codeword, an answer-bias control on prompts where "bomb" is not sensible, cross-codeword
  replay, benign-prompt KL. Per plan §6, a context-free output bias counts as "generic end-of-prompt editing is NOT
  sufficient for installation".

## S-067 — 2026-10-14 00:40 — ops tick
- r4 VAL: button 44/61, basket 41/61 ok, 0 failures (ETA ~01:45). F1 1023185 (basket Phase-A/B) COMPLETED; 1023251
  (button Phase-B) running; 1023386 (Phase-B replay) pending (1023385 cancelled/replaced by F1). F2: 1023012 still in
  CV (expected to hit the S-065 derangement bug after CV unless F2 intervenes), 1023264 + 1023389 pending. Watching the
  ≤6 concurrent-GPU cap as pending jobs start.

## S-068 — 2026-10-14 00:55 — P2b review fixes DONE (F2); PREREG AMENDMENT 1 frozen before endpoint
- All 9 review items fixed; tests 30 passed / 1 skipped; new arms GPU-smoked (1023389, 15/15 ok). No production
  endpoint read (0 prod score dirs).
  1. Constructive derangement (seeded cyclic domain→domain map + within-domain permutation); tested 67×10 × 40 seeds
     incl. 1000/1001 + unequal domain sizes. 1023012 survives: CV never builds shuffles; its final fit spawns a fresh
     process on the fixed code (sha logged, source copied to `fac/code_<attempt>_<cw>/`).
  2. PASS = Holm-adjusted p<0.05 AND recovery CI-lo>0 AND gates (pure `decide()`); mutation test: rank 1/82 with
     negative recovery ⇒ DOES NOT PASS.
  3. Option-mass collapse screen on every arm (BASE/KO/FULL/IDENT/CAND collapse ⇒ VOID; collapsed controls flagged +
     sensitivity rank test without them).
  4. KO_CWONLY_r (CAND only at the codeword row) + Δlogp_concept/Δlogp_codeword decomposition.
  5. KO_ATLAST_r = CAND's ΔW applied only at the last row (norm-matched by construction); position contrast
     CWONLY−ATLAST. NEUT demoted to descriptive.
  6. DER family: domain-deranged pairing, NO role swap, rescaled to CAND (15 at primary ranks, 5 descriptive).
  7. **AMENDMENT 1** `configs/heretic_csi/PREREG_P2B_AMENDMENT_1.json` (sha256 fd01d54e…baf10a): PRIMARY ranks {1,4},
     Holm over 2, 61 RAND + 5 SHUF + 15 DER = 81 controls (floor 0.0122); descriptive ranks 41+5+5 = 51. GPU ≈67 h.
  8. Per-job code snapshot + SHA256SUMS; importorskip("heretic"). 1023012's capture ran the pre-review runner (its
     fit/eval stages record their own shas) — capture code path was reviewed OK in S-065 (positions/split).
  9. KO_CAPOP_r replays KO_CAND within |Δy|≤1e-4 (smoke-verified); `p2b_deployed_residual.py` reports fitted vs
     deployed gap-closure (sanity cases give exactly 0 and 1).
  Also fixed: random controls were 0.1% off in norm (float32 dW.norm()); now exact double — caught by the norm guard.
- **Parent decision (consequential, documented):** add codeword-row-only matched controls (61 RAND + 15 DER, applied
  only at the codeword row) at primary ranks {1,4} as a **SECONDARY** preregistered test (Amendment 2, to be written
  before any endpoint). PRIMARY (all-rows KO_CAND) unchanged. **Disclosure:** a 12-row in-sample smoke hinted
  CWONLY ≫ CAND before this test was added (forking-path risk); any CWONLY claim requires VALIDATION replication with
  the frozen operator. Cost ≈ +24 GPU-h. Rationale: position-specificity is central to the mandate and is untestable
  without a matched null.

## S-069 — 2026-10-14 01:05 — PREREG AMENDMENT 2 (secondary CWONLY test) frozen before endpoint
- `configs/heretic_csi/PREREG_P2B_AMENDMENT_2.json` (sha256 65a5f0cb…06a3bf; tracked copy of the outputs/ file):
  secondary = KO_CWONLY vs 61 CWRAND + 15 CWDER codeword-row-only controls (floor 0.0130), Holm over {1,4}, CI-lo>0;
  forking-path disclosure; mandatory VALIDATION replication. Primary unchanged.
- **Disclosure numbers (corrected in-file before the sha, with revision_note):** smoke2 (12 rows, in-sample) CWONLY
  ΔY +0.267 (recovery 1.48) vs CAND +0.150 (0.83), ATLAST +0.001. F2's earlier "CWONLY ≫ CAND" → "CWONLY > CAND";
  a first-draft CAND −0.01 came from smoke1's differently-fit operator (wrong source; corrected).
- Scheduling: a primary rank = 163 arms (~12 GPU-h) ⇒ one primary rank per job: 1023012 → basket r1 + liveness;
  1023264 → button r1 + liveness; evalD_{basket,button} (r4) queued for free slots. Primary Holm verdicts only after
  BOTH r1 and r4 land. Smoke3 1023398 (12 rows, r1+r4) GPU-testing the secondary path.

## S-070 — 2026-10-14 01:10 — CORRECTION to S-058/S-059: the "5 s stage-in" was a warm NFS client cache
- The 5 s stage-in on n-503 came from that node's NFS client cache (mount uses fsc), not general scratch-mirror speed.
  Cold staging from the mirror on n-501 (smoke3 1023398) runs ~5.4 MB/s (~45 min for 15 GB). The mirror spreads load
  off the contended netapp but is NOT a general fix. Warm nodes: n-503, n-501.
- Decision: no node pinning (45 min ≈ 6% of a 12 h primary job; queue wait likely costs more); opportunistic `-w`
  only when a warm node has a free matching GPU at submit. S-053 stagger rule stays.

## S-071 — 2026-10-14 01:10 — ops tick
- r4 VAL: button 52/61, basket 50/61 ok (shuffled-control arms now), 0 failures; read ETA ~01:50. 6 GPU jobs running
  (= cap): 1022698, 1022699, 1023012 (P2b), 1023398 (P2b smoke3), 1023251 (Phase-B button), 1023386 (Phase-B replay);
  1023264 pending. No failures/duplicates.

## S-072 — 2026-10-14 01:45 — PREREGISTERED TEST (PR-HCSI-S051): button r4 PASSES on VALIDATION (pending independent verification)
- Job 1022698 (a5000, n-501): DONE_MARKER rc=0, 61/61 arms, 1 model load, 1 attempt (61 run dirs, no preemption).
  Frozen analyzer (`dcs_csi_subspace_analyze.py` via analyze_sweep, `--split validation --expect-n 230 --nrand 46
  --nshuf 10 --slurm-job 1022698`), output `reports/heretic_csi/hcsi_p2a_button_r4_validation.json`.
- Gates: KO_SELF−KO −0.0005 [−0.0026,0.0015] (inert); KO_FULL−KO **+0.142** [0.123,0.162] (23/23 domains).
- **PRIMARY: candidate (button cand_pls4, L18 rel-6) is strictly the largest of its 56 rank-matched, norm-matched
  controls ⇒ rank 1/57, p = 0.0175 < 0.05 ⇒ PASS** (frozen rule). Candidate−KO **+0.0129 [0.0065, 0.0190]**,
  20/23 domains positive; recovery fraction **0.091** of whole-state rescue.
- **Frozen interpretation (from the prereg, written before the run):** button HAS a specific low-rank (rank-4, not
  rank-1) activation-space rescue carrier at L18 ⇒ partial support for H1 / outcome A in the PLS activation family;
  S-049's "button has no specific carrier" must be re-scoped to ranks {1,16}. Still NOT the ARA weight operator.
- Status: **PASS pending independent verification (F3 re-tasked: recount, rank, CI, floor sensitivity, best-control
  margin, leave-one-domain-out).** Not yet quotable. basket r4 VAL (1022699, descriptive) still running.
- Scoping notes recorded now: (i) the prereg was written AFTER seeing TRAIN K4 r1–r16 (that is what motivated it);
  this VALIDATION read is the single held-out test, so it is clean, but the rank (4) was selected on TRAIN;
  (ii) small absolute effect (9% of whole-state rescue) — specificity, not magnitude; (iii) a5000 only (within-job
  comparison, so cross-HW noise S-062 does not affect the verdict); (iv) semantic-installation rescue only — no
  behavioral claim.

## S-073 — 2026-10-14 02:10 — INDEPENDENTLY VERIFIED: button r4 VALIDATION PASS (PR-HCSI-S051) is robust; basket r4 VAL fragile
Verifier F3 (`research/heretic_csi/verify/verify_r4_val.py`, analyzer logic not reused) →
`reports/heretic_csi/VERIFY_S072_r4_validation.{md,json}`.
- **PRIMARY button r4 VAL (1022698): AGREES — PASS.** 230 rows / 23 VAL domains, no TEST; 203 rows after the frozen
  BASE-ref 0.05 floor; 61 run dirs, single attempt. Rank **1/57, p=0.0175**, strictly largest (no ties); also 1/47
  vs RAND-only and 1/11 vs SHUF-only. Recovery **0.0909 [0.051, 0.126]**; candidate−KO **0.0129 [0.0063, 0.0192]**;
  20/23 domains positive. **Floor-robust** (strict paired floor keeps the same 203 rows → 1/57; no floor → 1/57,
  recovery 0.087). **Leave-one-domain-out: rank 1 in all 23 drops.** Margin over best control (KO_SHUF_r4_9, 0.0092)
  +0.0037 ≈ 1.2 control-SD. Liveness KO−BASE −0.302, FULL−KO +0.142, SELF−KO −0.0005. All 57 arms rank 4 (basis +
  per-row), norm-match exact (≤5e-16), distinct keys, seed 20260913, no short arms. Mutations null (median p 0.45 /
  0.39). Matches the frozen analyzer on every number.
- **DESCRIPTIVE basket r4 VAL (1022699, frozen analyzer: rank 1/57):** recovery 0.141 [0.077, 0.233], candidate−KO
  0.0198, 19/23 positive, but **FRAGILE**: margin over KO_SHUF_r4_9 only +0.0015 (0.3 SD); strict floor → 2/57
  (p=0.035, margin −0.0020); dropping `airport_apron` or `botanic_glasshouse` alone → rank 2; only 145/230 rows pass
  the floor (basket's option-mass-degraded bank, inherited caveat). **Not quoted as a pass.**
- **Status: CONFIRMED (held-out, preregistered, independently verified)** — button has a specific rank-4 (not rank-1)
  activation-space installation-rescue carrier at L18 rel-6 under the attention knockout.

### Updated synthesis of the P2a rank sweep (supersedes the S-049 "outcome D" reading)
| codeword | r1 | r4 | r16 | held-out status |
|---|---|---|---|---|
| basket | VAL 1/57 PASS (floor-sensitive, S-052) | VAL 1/57 (fragile, descriptive) | VAL 10/57 FAIL | specific carrier from rank 1 (fragile margin) |
| button | VAL 18/57 FAIL (verifier) | **VAL 1/57 PASS (robust, prereg)** | VAL 10/57 FAIL | **no rank-1 carrier; specific carrier at rank 4** |
- **Reading:** this is the **outcome-A shape** (prereg §3): basket's specific carrier appears at rank 1; button needs
  rank ~4; by rank 16 neither is specific (extra dimensions add generic dose any random subspace matches). Combined
  with S-054/S-065 (no evidence of a basket probe advantage held-out), the basket/button dissociation is better
  described as **a difference in the dimensionality of the specific carrier** than as "button has no carrier" or
  "basket has a better probe". H1 PARTIALLY SUPPORTED (activation-space PLS family only).

### WHAT WE CAN DEFEND (addendum S-073)
- Held-out, preregistered, independently verified: button's rank-4 PLS subspace at L18 rescues semantic installation
  under knockout more than every one of 56 rank- and norm-matched controls (p=0.0175, floor-robust, LODO-robust),
  whereas its rank-1 direction does not (VAL 18/57).

### WHAT WE MUST NOT SAY (addendum S-073)
- "Button requires exactly 4 dimensions" — ranks tested on VAL are {1,4,16}; 2/3 not tested; rank 4 was chosen on TRAIN.
- "Basket rank 4 also passes" — fragile (0.3 SD margin; strict floor 2/57; single-domain drops flip it).
- Anything about the ARA *weight* operator (P2b not yet read), behavior/ASR, or a population law (2 codewords).
- "Large effect" — recovery 9% of whole-state rescue; the claim is specificity, and p is at the 56-control floor.
- "Button has no specific carrier" (S-049 wording) — superseded.

## S-074 — 2026-10-14 02:30 — P2b BUILT + smoke-validated (F2 hand-off); primary eval jobs running; no endpoint read
- Code (research/heretic_csi): `p2b_operator.py` (joint factored ΔW=B@A on o_proj+down_proj, layers 6–18 = 26 modules;
  objectives knn/mse/cos/whiten; weight-edit hooks all-rows or single-row; capture hooks; rank+norm-matched controls),
  `p2b_runner.py` (arm_runner design: one model load, hook-leak check per arm, per-arm operator spec, code sha256 per
  arm), `p2b_fit.py` (exact-context clean/KO pairing, loud per-row anchor==KO-row and TRAIN-domain checks,
  domain-grouped CV, rank sweep, controls), `p2b_freeze.py`, `p2b_emit.py`, `p2b_analyze.py`,
  `p2b_deployed_residual.py`, `slurm/p2b_job.slurm` (no-requeue, mirror stage, code snapshot). score_behavior.py
  UNCHANGED. Tests 30 passed / 1 skipped.
- Verified: 268/268 K4 prompts codeword at rel −10; production capture 670 prompts × 2 codewords, 67 TRAIN domains,
  every anchor matched the KO-recorded row; smokes (1022701, 1023389, 1023398): KO 0.399 < BASE 0.732, FULL recovers,
  KO_IDENT == KO exactly, CWONLY/ATLAST hit ' basket' / '\n\n', CAPOP replays CAND exactly, 1 load, 0 hook leaks.
- **Objective FROZEN (TRAIN-only CV, no endpoint):** paired **MSE, steer 0.3**; pooled held-out net gap-closure 0.650
  (basket 0.621); kNN 0.38; cosine overshoots.
- Populations (PREREG_P2B, declared): fit = TRAIN full 670 rows; **TRAIN eval = K4 subset 268 rows — IN-SAMPLE w.r.t.
  the fit**; held-out = VALIDATION 230 rows with frozen operators, after the TRAIN read; TEST never.
  **Parent note:** because the candidate is fit on the TRAIN rows it is scored on while the RAND controls are not fit,
  a TRAIN rank-test PASS is structurally favoured and is weak evidence; only the VALIDATION read is confirmatory.
  (DER/SHUF fitted controls partly level this.) The VALIDATION plan must be written + committed before the TRAIN read.
- Jobs: 1023012 (n-503; final fits → basket r1 + liveness, ~12 h), 1023264 (button r1, begins 03:20), 1023508 /
  1023509 (basket / button r4, n-501). Descriptive plans evalC {16,50}, evalB {2,8,32} not yet submitted.

## S-075 — 2026-10-14 02:50 — P2b VALIDATION plan PREREGISTERED before any P2b endpoint
- `configs/heretic_csi/PREREG_P2B_VALIDATION.json` (sha256 5b1f3bac…5d2b9b) + plans
  `configs/heretic_csi/p2b_plans/val_{basket,button}_r{1,4}.sh` (copies of outputs/heretic_csi/p2b/plans/; not yet
  submitted — GPU cap). Frozen fac/ operators, no refit, factor-file sha256 recorded per job; population = VALIDATION
  230 rows / 23 domains; same 163 arms/rank (81 primary + 76 secondary CW-row controls + CAND/BASE_CAND/CWONLY/ATLAST/
  NEUT/CAPOP); same pass rule + analyzer; a5000.
- **Control draws IDENTICAL to TRAIN** (same seeds, same frozen CAND norms ⇒ byte-identical RAND; same frozen SHUF/DER
  fits): the control family is part of the frozen intervention spec, so validation tests the same candidate-vs-family
  comparison on new domains with no new random degree of freedom. A fresh-draw run may follow as a separately
  labelled descriptive sensitivity.
- Cost ≈ 42 GPU-h for 4 jobs (~227 s/230-row arm). Submit order when slots free: r1 both codewords, then r4.

## S-076 — 2026-10-14 02:10 — ops tick; P3/P4 CPU workstream (F5) launched
- Running: 1023012 (P2b final fits — basket r1, r2 factors written; then basket r1 TRAIN eval), 1023508/1023509 (r4,
  waiting on factors), 1023386 (Phase-B replay); 1023264 pending. Completed: 1023251 (Phase-B button, 1h48m),
  1023398 (smoke3). No failures/duplicates. VALIDATION P2b plans gated on fit_summary (not yet present).
- First production fit (fitting-side, in-sample, not an endpoint): basket r1 gap-closure 0.594, preserve damage
  0.0006, total ‖ΔW‖ 44.9 (vs 172 in smoke — wider preserve set constrains it); ~12 min per rank.
- **F5 launched (CPU only, additive code):** P3 = SVD/effective-rank/norm-location of every fitted ΔW + descriptive
  alignment (with matched random-subspace nulls) to basket/button r1 axes, PLS r4 subspaces, d_surface, refusal dir,
  probe weights; GPU truncation/removal plans gated on a validated operator. P4 = verify Llama o_proj head-column
  layout from source; recover the inherited head circuit; fit head-restricted o_proj operators (target heads vs ≥20
  matched random head sets vs full o_proj vs MLP-only vs attn+MLP, ranks {1,4}); draft PREREG_P4 before any endpoint.

## S-077 — 2026-10-14 02:20 — PHASE A PASS; PHASE B VERDICT: native last-position ARA is NOT sufficient for installation (context-free answer bias)
Env: pinned Heretic 662e4ba2 in venv `/specific/scratches/scratch/omeryosef/envs/heretic_csi` (torch 2.13+cu126, tf
5.6.2, optuna 4.8.0, peft 0.19.1; conda create blocked by an unaccepted channel ToS — not accepted on the user's behalf).
**Cell mapping recovered from `prompt_families.py`:** A = benign_literal, B = direct_harmful, C = natural_doublespeak,
E = concept_in_benign_ctx. Phase-B ARA groups renamed target = C (installed), source = A (not installed).
- **Phase A PASS (1023185;** 1022919 = superseded failed-gate record): eager+bf16, deterministic base, exact reset to
  identity, Optuna resume works. Heretic findings (S-062) confirmed + one more: **resume re-draws trial 0's exact
  params** (re-seeded TPE). Restoring lora_A makes replay bit-exact.
- **Phase B (MEASURED control; TRAIN-tuned 67 dom, VAL 23 dom read once, TEST never):**

  | | basket | button |
  |---|---|---|
  | VAL cell A ΔY (not installed) | +0.925 | +0.796 |
  | rank vs 42 rank-matched controls | 1/43, p=0.023 (floor) | 1/43, p=0.023 (floor) |
  | control ΔY | ≤6e-5 | ≤0.0035 |
  | VAL cell C ΔY (installed) | −0.124 | −0.111 |
  | Δlogp(bomb) on VAL A | +13.9 | +13.4 |
  | first-token KL, VAL C | 0.85 | 1.02 |
  | keyword refusal (secondary) | 0.065→0.022 | 0.196→0.087 |

  Specificity reads (MEASURED): cross-codeword — button-fit edit on basket prompts gives A +0.995 / C +0.530; wrong
  concept — on knife contexts the basket edit raises P(bomb) +0.395 > P(knife) +0.289 (gun: bomb +0.272 > gun +0.215);
  damages installed prompts; basket VAL C option mass 0.036 (< 0.05 floor); first-token KL on benign A prompts 4.55.
  Saved-factor replay bit-exact on another node.
- **VERDICT (plan §6 question):** generic end-of-prompt operator editing is **NOT sufficient for semantic
  installation** — it beats random controls only by installing a context-free "answer bomb" output bias at the answer
  position (Heretic's capture site). Expected; motivates position-aware ARA (P1/P2b). Caveats: freeze rule v1 (no
  option-mass clause); 42 controls exclude random perturbation but not answer bias (the specificity reads do);
  r1/r8 same-param refits descriptive (basket 0.0 / +0.43 [r8 below floor]; button +0.75 / +0.48).
- Ops: several F1 jobs lost to node /tmp exhaustion (n-803, n-804, n-801); scripts now fall back to loading from the
  mirror directly (~20 min).

## S-078 — 2026-10-14 02:40 — ops tick
- P2b fits (1023012): basket factors r1,2,4,8,16,32 saved (fitting-side in-sample gap-closure r16 0.677, r32 0.637;
  preserve damage ≤0.003); r50 then button ranks next. 1023508/09 (r4) waiting on factors; 1023264 pending.
- F5 CPU jobs (cpu-killable): P4 head-restricted fits 1023554–57 (basket/button × r1/r4), P3 1023558. 3 GPU running.
  No failures/duplicates.

## S-079 — 2026-10-14 03:00 — P3 (descriptive SVD, basket r1–r32) + P4 setup; PREREG_P4 frozen before any P4 endpoint
F5 (CPU only). Reports: `reports/heretic_csi/P3_SVD_REPORT.md`, `P3_svd_descriptive.json`, `P3_write_direction.json`,
`P4_HEAD_RESTRICTED_DESIGN.md`. Button P3 pending (button factors not yet fit).
- **P3 key structural finding (DESCRIPTIVE geometry):** at r1–2 the candidate AND every fitted control (DER, SHUF)
  write along the same direction per module = the mean KO→clean output gap (|cos| 1.000 CAND/DER, 0.999 SHUF); they
  differ only in input conditioning (whole-ΔW cos: DER 0.6, SHUF 0.35; NEUT 0.13). The mean gap carries 44–75%
  (basket) / 52–78% (button) of per-prompt gap energy and is largely SHARED across codewords (basket·button |cos|
  0.84–0.94 at L6–14, 0.50 at L18). **Consequence for P2b reading:** CAND vs fitted controls tests input-side
  specificity only; CAND vs RAND tests write direction + conditioning.
- Shape: o_proj holds 59–79% of ‖ΔW‖²; norm concentrates in layers 6–7 and 17–18; entropy-effective rank 1.0 (r1),
  ~2 (r4), ~4.8 (r8, r16); ‖ΔW‖/‖W‖ median 2–6%.
- Alignment (vs matched random-subspace null): weak. Largest = refusal direction at L16 o_proj (squared projection
  0.025–0.043, |cos| ≈0.16–0.21, every rank, > random 99th pct); d_surface at L6/L12 ≤0.019; L18 probe axes ≤0.023
  (different token position — not like-for-like). **No preference for the inherited 8-head circuit** (TOP8 share of
  o_proj input-column norm median 0.23–0.25 vs 0.25 expected; ≤1/13 modules above random 95th pct).
  (F5 self-corrected a draft claim that alignment never exceeded the null — refusal@L16 does.)
- **P4 setup:** query head h ↔ o_proj input columns [128h, 128h+128) verified in transformers LlamaAttention (GQA
  repeat_kv precedes; same indexing as the CSI head knockout); unit-tested. Existing captures contain o_proj inputs
  at the codeword row L6–18 ⇒ no new GPU capture. Fits (CPU, 1023554–57, ~12 h): TOP8 heads [19,17,23,6,13,2,24,28]
  vs 60 fitted random-8-head sets from the 24 other heads (norm-matched per module), + FULLO, MLP, ATTNMLP, H2,
  CELL_L10H2; ranks {1,4}. In-sample (fitting-side): basket r1 TOP8 gap-closure 0.571 (‖ΔW‖ 18.3, damage 0.0025) vs
  FULLO 0.575 (10.0, 0.0007); basket r4 0.620 vs 0.638; button r1 0.624 vs 0.628. CPU thread count changes TOP8 norm
  by 0.04% (saved factors are the frozen ones). Summary-file collision (S-051 class) caught + fixed before results.
- **PREREG_P4 frozen** `configs/heretic_csi/PREREG_P4.json` (sha256 aba003bc…aacbf), parent-reviewed: candidate
  KO_TOP8_r vs 60 fitted, norm-matched random-8-head controls (floor 0.0164); basket PRIMARY (Holm {1,4}, CI-lo>0,
  gates, VOIDs), button = secondary transfer; TRAIN-K4 in-sample then VALIDATION frozen factors; parent additions:
  the test measures head/input-side specificity (all fits share the write direction), unscaled norms reported, no
  post-hoc promotion of descriptive variants. **Dependence caveat:** the 8-head set was certified on basket
  VALIDATION ⇒ basket VAL P4 read is held-out for the weight fit, not a fresh test of the head nomination.
- Plans copied to `configs/heretic_csi/p2b_plans/` (P3 truncation ≈11 GPU-h gated on a validation PASS; P4 ≈37 GPU-h).

## S-080 — 2026-10-14 03:10 — ops tick
- P2b: basket fits complete (fit_summary_basket.json); button r1, r2 fitted. 1023508 (basket r4 TRAIN-K4 eval) scoring
  (first arm 100/268); 1023509 (button r4) waiting for button factors; 1023264 pending (BeginTime). P4 CPU fits
  1023554–57 running. No failures/duplicates. VALIDATION P2b plans for basket now runnable (fit_summary present) —
  will submit when GPU slots allow (currently 3 GPU + 1 pending).
- **Submitted P2b VALIDATION runs for basket** (frozen factors; PREREG_P2B_VALIDATION): 1023578 (r1, incl. liveness)
  and 1023579 (r4), pinned to warm n-503 (free a5000s; avoids cold stage-in). **Read discipline:** these run in
  parallel for wall-clock reasons only; their outputs will NOT be analyzed until the basket TRAIN-K4 primary read
  (r1 + r4) is analyzed and logged. GPU: 5 running + 1 pending = 6.

## S-081 — 2026-10-14 03:40 — ops tick
- 6 GPU running (cap): 1023012 (button fits, r32 done → r50, then basket r1 TRAIN eval), 1023508 (basket r4 TRAIN,
  ~13 arms), 1023509 (button r4, waiting factors), 1023264 (button r1, started), 1023578/79 (basket VAL r1/r4, not to
  be read before TRAIN). 4 P4 CPU fits running. No failures/duplicates.

## S-082 — 2026-10-14 04:10 — ops tick; all P2b fits done; ~4h ADVERSARIAL REVIEW #2 launched; P3 rerun incl. button
- fit_summary_{basket,button}.json present ⇒ all 7 ranks × 2 codewords fitted (frozen). TRAIN-K4 evals running:
  1023012 (basket r1), 1023508 (basket r4, ~20 arms), 1023264 (button r1), 1023509 (button r4). VAL basket r1/r4
  (1023578/79) running, unread. 6 GPU (cap). P4 CPU fits running. hcsi_p3svd2 (1023562) COMPLETED (F5). No failures.
- **Adversarial review #2** (fresh independent reviewer, read-only): p2b decide()/Holm/CI/collapse/VOID, whether the
  S-065 fixes actually landed (incl. checking saved control factors' rank/norm), P4 head-column restriction + random
  head sets + TOP8 provenance + leakage, P3 effective-rank/null construction and the "shared write direction" claim,
  P2a button-r4 VAL headline re-attack incl. prereg-commit-time vs job-start, Phase-B verdict, read discipline for the
  early VAL runs, overclaim audit S-066…S-081, tests. → `reports/heretic_csi/REVIEW_ADVERSARIAL_20261014_b.md`.
- **P3 rerun with button factors:** CPU job 1023746 (`research/heretic_csi/p3_run_all.py`). The basket-only S-079
  reports are preserved as `reports/heretic_csi/P3_*_S079_basket_only.*` (the regenerated files supersede them; no
  history rewritten).

## S-083 — 2026-10-14 04:40 — ~4h ADVERSARIAL REVIEW #2: 1 CRITICAL + 5 HIGH; CORRECTIONS to S-073 / S-077 / S-079
Report `reports/heretic_csi/REVIEW_ADVERSARIAL_20261014_b.md` (independent reviewer; read-only; no P2b/P4 endpoint read).
**CORRECTIONS (appended, not rewritten):**
- **S-073 DOWNGRADED.** "CONFIRMED" for button r4 VAL is withdrawn. Button VALIDATION had already been read at r1
  (FAIL) and r16 (FAIL) before r4 was chosen (on TRAIN); over the 3 VAL looks, Bonferroni 3×0.0175 = 0.053 > 0.05 and
  p sits at the 56-control floor. The single preregistered test PASSED honestly and is robust (floor/LODO), but over
  all looks it is **SUGGESTIVE (floor-limited, look-multiplicity)**, not confirmatory. The "outcome-A / dimensionality
  difference" synthesis compares a pass with a fail and has no basket-vs-button contrast test ⇒ it is a HYPOTHESIS.
  Remedy launched (F6): preregistered powered re-test on the same VAL data with ≥200 rank-4 controls (floor ≤0.005),
  Holm over the 3 button VAL looks {r1,r4,r16}, + descriptive basket-vs-button interaction; fresh confirmation → P6.
- **S-077 SCOPED.** Phase-B "not sufficient for installation" holds on the benign cell-A read + cross-codeword read; but
  the knife/gun read (option mass 0.139→0.009) and basket VAL-C (0.036) are on COLLAPSED readouts, and P(knife)/P(gun)
  also rose ⇒ "context-free" is too strong. Wording now: native last-position ARA (Heretic objective, as shipped)
  produces a largely context-insensitive answer-position bias toward "bomb", not codeword-specific installation.
- **S-079 alignment wording.** The isotropic alignment null is miscalibrated (almost every layer "exceeds" it) and the
  PLS-4 comparison used a dimension-mismatched null; the "refusal@L16" headline is withdrawn pending an anisotropic
  null (F5). The shared-write-direction finding is correct but expected by construction (fitted controls are fit to
  the same gap).
**Findings → owners (all before any affected endpoint read):**
1. CRITICAL P4 (`p4_head_fit.py:131`): rescaling fitted random-8-head controls to TOP8 norm moves them off optimum
   (in-sample net RH8_0 raw→rescaled: button r1 0.621→0.147 vs TOP8 0.622; basket r1 0.568→0.460 vs 0.568; basket r4
   0.618→0.581 vs 0.615; button r4 0.659→0.586 vs 0.651). **Fitting-side finding: at their own optimum, random
   8-head sets fit as well as TOP8.** Fix (F5): PREREG_P4 amendment — TOP8 must beat BOTH raw-norm RH8 and
   norm-constrained RH8 (refit under constraint preferred), Holm over ranks × families.
2. HIGH bug (`p2b_analyze.py:236-247`, `p4_analyze.py:99-106`): Holm over an incomplete family PASSes at unadjusted p
   ⇒ must be INCOMPLETE. 3. HIGH bug: secondary CWONLY lacks collapse/norm/rank VOIDs, and CW-family failures void the
   primary. 4. HIGH: P2b fitted controls carry the same rescaling handicap (DER0 raw/CAND 1.10–1.29; SHUF0 1.65–3.4×)
   ⇒ report raw-norm rank tests. 5. HIGH interpretation: CAND writes the shared mean KO→clean gap ⇒ add an
   input-independent MEAN-GAP BIAS comparator; a CAND PASS not beating it certifies only "adding the mean shift undoes
   part of the KO". (2–5 → F2: PREREG_P2B_AMENDMENT_3 before the TRAIN read.)
6. MEDIUM: P4 heads nominated on L6–14 but tied over L6–18 (F5: descriptive variant/caveat). Provenance: P2a basis
   files untracked (65 MB) ⇒ sha256 manifest committed `configs/heretic_csi/hcsi_ranksweep_SHA256SUMS.txt`
   (button `1c586d1a…`, basket `0bf29e02…`, mtime 2026-10-02 — predate all VAL reads).
**Verified OK:** Holm step-down + CI-lo>0 + VOID/gate order in decide(); constructive derangement (0 same-domain, 0
reuse, all seeds); DER no role swap; saved fitted controls match CAND per module (≤6e-8) at rank r; RAND seeds
regenerate (≤3e-8); code shas = working tree; prereg copies byte-identical; VAL factor shas = TRAIN; P4 column
restriction correct, 60 head sets distinct & disjoint, TOP8 = HD_TOPK from TRAIN screen; P3 truncation renorm
declared; **P2a r4 prereg committed 20:18:33, job 1022698 started 22:14:47; TRAIN/VAL share 0 domains, 0 prompt ids**;
nothing auto-analyzes the early VAL jobs (read-after-TRAIN is procedural). Tests 35 passed / 1 skipped.

### WHAT WE MUST NOT SAY (addendum S-083)
- "Button r4 is CONFIRMED" / "certified" — suggestive, floor- and look-limited until the powered re-test reads.
- "The dissociation is a dimensionality difference" — hypothesis (no contrast test yet).
- "Native ARA is context-free" — context-insensitive on non-collapsed reads; scoped to the shipped objective.
- "The learned operator aligns with the refusal direction" — withdrawn pending a calibrated null.
