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
