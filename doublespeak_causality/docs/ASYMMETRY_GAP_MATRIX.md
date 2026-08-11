# ASYMMETRY SPRINT — GAP MATRIX

*Phase 0 deliverable (plan §4). Written 2026-08-11 before any GPU job.*
*Classifies every candidate line of work as: **DONE · DONE/DO-NOT-REPEAT · PARTIAL · UNDERPOWERED · NEW · INVALID/SUPERSEDED**.*
*Sources: `docs/RESEARCH_HANDOFF.md` §5/§6 (authoritative numbers) + a 12-agent code/artifact audit whose
load-bearing claims were each independently re-verified. Audit findings that changed a classification are
cited inline.*

---

## A. GATE-A INTEGRITY RESULTS (what the audit established)

| # | Check | Result |
|---|---|---|
| A1 | Every handoff headline number traced to raw scalar JSON (20 GCG arm summaries, `GATE7_V3_MATRIX_STATS.json`, `GATE7_V3_MECH_VALIDITY_seed42.json`, 3 quantization summaries) | **0 numeric mismatches.** PASS |
| A2 | **§19.3 direction-identity check.** Is the refusal vector the same object in (i) activation ablation, (ii) the GCG projection loss, (iii) the mech-validity readout? | **PASS — byte-identical (same md5), cosine = 1.0.** `outputs/stage_gcg_full/refusal_direction_llama_L{12,14,16,18,20}.pt` are md5-identical to `outputs/refusal_alllayers/refusal_direction_llama_L{same}.pt`. No silent cross-path vector mismatch. |
| A3 | Off-by-one convention (`L{k}` fitted at `hs[k+1]`) | Convention confirmed in the sidecars (`hidden_states_index: 19`, `directions_row: 18` for L18) and honoured by the v3 GCG wrapper (`--refusal-dir-layer 19`). |
| A4 | Suffix placement | `suffix_placement=user` verified; `build_suffix_spans` asserts the suffix token ids appear at the expected index. |
| A5 | **Position conventions across code paths** | **FAIL → three defects, D1/D2/D3.** See execution log E0.3 and rows R1–R3 below. This is the single most consequential Phase-0 finding. |
| A6 | Refusal-direction fitting cohort | **Newly flagged limitation.** The L18 refusal axis was fit on `pair_benchmark/pair_carrot_bomb.json` with **n_harmful=60 / n_harmless=20**, then applied to ClearHarm-v3 doublespeak prompts. Cross-distribution direction transfer; never previously flagged. Also: the harmless class is 20 hardcoded generic instructions, not the matched `neutral` prompts. |
| A7 | Layer-validation record | `refusal_direction_llama_SELECTED.json`: L18 score 1.133 (ablate +0.467, induce +0.667). **L12 is the only layer that FAILED validation** (ablate 0.0, induce −0.333, `valid=false`) — yet Q2 used refusal@L12 as the "Jacobian-peak" arm. Q2's negative is therefore partly expected. |

**GATE A VERDICT: CONDITIONAL PASS.** Numbers reproduce and the direction is one object (A1, A2 pass), so the
*existing* results are not withdrawn. But A5 means the *interpretation* of the token-space arm must change,
and A6/A7 are limitations that belong in the paper. New GPU work is authorised.

---

## B. THE THREE POSITION DEFECTS (new; drive the sprint's re-framing)

| Row | Defect | Status | Consequence |
|---|---|---|---|
| **R1** | **D1 — cross-task absolute-position misalignment.** `gcg_optimizer.py:687` computes `refusal_dir_positions = [suffix_slice.stop - 1]` **once from `train_tasks[0]`** and applies it as an absolute token index to all 40 train prompts. Measured on the frozen pool: correct for **1/40**; lands inside the suffix for 17/40, inside the instruction for 12/40, after the suffix for 10/40, and **out of range (term silently 0) for 1/40**. | **NEW / INVALIDATES-INTERPRETATION** | The refusal & concept objectives were, for 39/40 training prompts, not reading the coordinate they claim to. Both mechanism and random arms share the defect, so the *comparison* stands but "we optimized the validated refusal projection" does **not**. |
| **R2** | **D2 — fit-position vs use-position mismatch.** The direction was fitted and causally validated at the **last token of the templated prompt** (`build_refusal_direction_llama.py:83`, `hs[L+1][0,-1,:]`, i.e. after `<\|start_header_id\|>assistant<\|end_header_id\|>\n\n`). The GCG objective reads the **last suffix token**, 5 template tokens earlier, still inside the user turn. | **NEW** | Even a D1-fixed objective would optimize a projection at a position where the axis was never validated. Directly the plan's **CASE D** ("target-position/objective mismatch"). |
| **R3** | **D3 — intervention-scope asymmetry.** The activation-space causal result ablates the direction at **every position, every decode step, and every layer** (`pair_common.py:637` `AllPositionProjectOutMultiLayer`). The token objective touches **one position, one layer**. | **NEW (not a bug — a confound)** | "Activation-space causal but token-space unreachable" is partly "all-position/all-layer vs one-position/one-layer". Must be controlled in Phase 2's Figure A, and is a first-class alternative to H1–H5. |

---

## C. CLASSIFICATION OF PRIOR WORK

### DONE / DO NOT REPEAT (plan §4 explicit list — all confirmed present and sound)
| Item | Artifact |
|---|---|
| Concept-circuit mapping (retrieval → L9 write → L14–21 carry → L30–31 readout) | `reports/FINAL_CAUSAL_CIRCUIT_REPORT.md`, `MECHANISM_SYNTHESIS.md` |
| Broad attention edge KO · induction-head search · head→MLP path sweep · all-codeword-occurrence concept patch | `reports/PHASE{3,4A,4B,5,6,7,8}*.md` |
| First-order refusal GCG 3-seed × 200-step matrix; L18 vs L12; concept GCG; combined GCG | `GATE7_V3_MATRIX_STATS.json`, 20 arm dirs |
| GCG mech-validity showing random suppresses more | `GATE7_V3_MECH_VALIDITY_seed42.json` |
| Phi third-family causal refusal replication (X1/X2/X3/X5) | `docs/THIRD_FAMILY_REPLICATION.md` |
| bf16 / 8-bit / 4-bit refusal-ablation robustness | `docs/QUANTIZATION_EXTENSION.md` |

### PARTIAL / UNDERPOWERED / RE-OPENED
| Item | Prior status | New status | Why |
|---|---|---|---|
| **Gate-D token-space negative** | NEGATIVE (final) | **SUPERSEDED-PENDING** | R1/R2. Numbers stand; the mechanistic reading does not. A position-corrected arm now tests a hypothesis the old run could not. |
| **Q5 mech-validity** | Done, seed 42 | **PARTIAL** (plan §19.1a) | n=1 seed; means only, no per-prompt arrays; no train-pool comparison; no no-suffix-baseline distribution. |
| **Layer profile of held-out suppression** | not run | **NEW** (plan §19.2) | Distinguishes generic (H4) from partially specific suppression. Cheap forward-only. |
| **Phi readout AUC (X5)** | UNDERPOWERED (n=42, all CIs span 0.5) | **UNDERPOWERED — fixable** | Audit: **102 ClearHarm items** are outside `trainpool40 ∪ v3-test37`; **68** are outside `train74 ∪ test37`; **31** appear in no v3 split at all. A ≥60-item leakage-free replication cohort is constructible. |
| **Multi-concept generalization** | assumed, not tested | **NEW — data ready** | All 5 pairs exist with **cluster-disjoint `dev`/`heldout` splits** (not named train/test): bomb 34/26, chlorine 33/27, cocaine 22/38, grenade 20/40, pistol 31/29 unique paraphrase items; `pid` overlap = 0 for all 5; demo blocks asserted disjoint at build time (`30_build_pair_benchmark.py:460`). **Every pair clears ≥20 train and ≥20 test.** |
| **Defense (over-refusal tradeoff)** | prior-sprint Gate-F FAIL, not re-run | **NEW angle** | Two-signal gating (concept detects, refusal actuates) was never tested. |
| **MAC / TROPT** | scoped out | **AVAILABLE** | `$ROOT/TROPT` is a full checkout with `MAC__wang2024` and `SoftPrompt__schwinn2024` recipes, plus an existing project driver `scripts/phase3_tropt_optimize.py`. |

### INVALID / SUPERSEDED
| Item | Why |
|---|---|
| "Refusal@L12 is the Jacobian-peak target" (Q2) | L12 **failed** the ablate+induce validation (A7). Its negative is uninformative about mechanism reachability. |
| Old `arm06` manifest repr-cache concept route | Already retired for an absolute-index position bug (handoff §7.4.5) — the *same class* of bug as R1, which survived in the direction-projection route. |

---

## D. WHAT REMAINS UNANSWERED (the plan's §4 question list, answered)

| Topic | What exactly is still open | Phase |
|---|---|---|
| **Token reachability** | No measurement of `∂⟨h,v⟩/∂e_suffix` exists anywhere. Audit confirms `phase6_jacobian_readout.py` computes a *layer-to-layer / position* sensitivity and **explicitly discards `embeds.grad`** (it only creates the leaf to avoid a 16 GB param-grad buffer). GCG's `_token_gradients` normalizes per-row and folds in an unconditional CE term, so it cannot be reused as-is. **Must be written fresh.** | 1 |
| **Continuous input reachability** | Never measured on this axis/split. But strong prior art exists to reuse: `poc_stage4/phase9_soft_opt.py` (Adam on free prefix embeddings maximizing a direction projection) and `$DC/37_soft_prompt_objective.py` (**simplex parameterization** — softmax over the vocabulary, so its optimum *upper-bounds* any real token sequence; the docstring records that the `free` parameterization made the gate vacuous). The simplex relaxation is exactly the right instrument for the discrete-bottleneck question. | 2 |
| **Discrete-token reachability** | Open, and now *more* open because of R1/R2. | 1, 3 |
| **Optimizer choice** | Untested. TROPT/MAC usable but requires `$ROOT/TROPT/.venv/bin/python` (py3.13 / torch 2.11 / transformers 5.8.1) — **not** `poc_stage2` (py3.12 / torch 2.7.1 / transformers 5.12.1). StrongREJECT is **not** available in the TROPT venv, so any behavioral reranking needs a two-process split (documented at `slurm_scripts/run_reinforce_mac_smoke.slurm:60-62`). | 3 |
| **Multi-concept generality** | Wide open; data ready (§C). Must pin `pair_carrot_bomb.json` vs `pair_carrot_bomb_offline.json` — they are structurally indistinguishable and carry no commit/sha provenance. | 4 |
| **Selective defense** | Wide open. | 5 |
| **Phi readout power** | Underpowered but fixable with a ≥60-item leakage-free cohort. | 6 |

---

## E. PRE-REGISTERED DECISIONS (frozen before any outcome is seen)

1. **Primary target position = `decision`** (last token of the templated prompt), because that is where the
   refusal axis was fitted, validated, and is read out. `last_suffix` (the GCG position) is reported as a
   **secondary** position purely to quantify D2. This choice is made now, before any result.
2. **Primary target row = `hs[19]`** for refusal (fit layer L18) and **`hs[10]`** for concept (fit layer L9).
   `+1` is applied inside every new script and asserted into `meta.json`.
3. **Selection data.** The v3 `dev` split (n=37, cluster-disjoint, never used by the GCG matrix) is this
   sprint's selection set for any threshold / rank / layer choice that the 40-item train pool cannot support.
   **`test` (n=37) is never used for selection.**
4. **Random controls.** ≥100 norm-matched unit random directions per cell, generated deterministically via
   `pair_common.norm_matched_random(seed=42+hs_row)`. A "foreign mechanism" control (the concept vector
   evaluated at the refusal row and vice-versa) is included as a *structured* non-random control.
5. **Subspace honesty.** The empirical Δh subspace is built from **direction-agnostic random-vocabulary
   substitutions only**, never from refusal-top-gradient candidates, so `R(v_refusal)` cannot be inflated by
   the candidate-selection rule. It is reported as the *empirical local token-reachable subspace*, never as
   "the vocabulary-reachable subspace". The isotropic null `r/d_model` is reported alongside every `R`.
6. **Figure A pre-registration (plan §19.6).** Plotted quantities are fixed now: y1 = held-out **Δ refusal
   projection at `hs[19]`, `decision` position, vs the no-suffix baseline**; y2 = **Δ binary ASR
   (StrongREJECT ≥ 0.5)** vs the same baseline. Arms: no-intervention · activation ablation (α=1) ·
   continuous soft prompt · GCG mechanism suffix · matched random suffix · matched random soft prompt.
   Norm matching: every random control is unit-norm at the same row; soft-prompt controls share the
   embedding-norm budget chosen on train.
7. **D3 control.** Because the activation arm is all-position/all-layer and the token arm is
   one-position/one-layer, Figure A additionally carries a **scope-matched activation arm**
   (single-layer L18, single position = `decision`) so the medium and the scope are separable.

---

*End of gap matrix. Companion: `docs/ASYMMETRY_SPRINT_EXECUTION_LOG.md`.*
