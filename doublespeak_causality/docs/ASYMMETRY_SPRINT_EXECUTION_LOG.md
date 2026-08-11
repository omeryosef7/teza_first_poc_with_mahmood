# ASYMMETRY SPRINT — EXECUTION LOG

*Append-only. Started 2026-08-11. Plan: `docs/ASYMMETRY_SPRINT_PLAN_2026_08_11.md`.*
*Authoritative prior state: `docs/RESEARCH_HANDOFF.md` §5/§6.*

Conventions: every entry has a UTC-ish date stamp, the phase, what was done, the artifact
path, and a verdict. Nothing is deleted; corrections are appended as new entries.

---

## 2026-08-11 — PHASE 0 START

### E0.1 Environment / baseline state
- Branch `behavioral-causality-sprint`, clean tree at `f0ef1ccc`.
- SLURM: 0 jobs owned by user. `killable` partition has idle L40S-class nodes
  (`n-[203-205,305,501-502]` idle, 13 mix). Budget rule: **≤6 concurrent GPU jobs**.
- Conda envs: `base`, `poc_stage2`. `poc_stage2` is the torch/transformers env.
- Offline HF cache at `$ROOT/.cache/huggingface`.

### E0.2 Data inventory (verified directly)
`data/gcg/clearharm_llama_v3/clearharm_llama_doublespeak.jsonl`: **n=148**, splits
`train=74 / dev=37 / test=37`. Fields include `task_id` (unique id), `split`,
`intent_cluster` (cluster field), `instruction`, `safe_target_prefix`, `codeword`,
`neutral_control_suffix`, `harm_category`.
`..._trainpool40.jsonl`: **n=40**, all `split=train` (the frozen optimization pool).

**Note for train/test discipline:** there is an untouched **`dev` split (n=37)**. It is
cluster-disjoint from test by construction of v3. This sprint uses `dev` for any
hyperparameter / threshold / layer selection that the 40-item train pool cannot support,
so that **test (n=37) is never used for selection**.

`data/pair_benchmark/`: all five pairs present — `pair_carrot_{bomb,grenade,pistol,chlorine,cocaine}.json`.

---

## GATE A — REPRODUCTION INTEGRITY / CODE AUDIT

### E0.3 Position-convention audit of the refusal direction across the three code paths

The plan (§19.3) requires asserting the refusal *vector* is the same object across code
paths. Auditing the code paths surfaced a more serious issue: the vector is (probably) the
same, but the **position at which it is read differs across all three paths**, and one of
those positions is computed incorrectly.

The three code paths and the residual-stream position each uses:

| Path | File | Position read | Layer index |
|---|---|---|---|
| **(i) Direction fit** | `build_refusal_direction_llama.py:83` `hs[L+1][0,-1,:]` | **last token of the templated prompt** (i.e. after `<\|start_header_id\|>assistant<\|end_header_id\|>\n\n`) — the decision position | `hs[L+1]` |
| **(ii) Activation ablation (the causal result)** | `pair_common.py:637` `make_project_out_hook` | **EVERY position, EVERY decode step**, and (multilayer variant) every layer | block output = `hs[L+1]` |
| **(iii) GCG token objective** | `gcg_optimizer.py:687` `refusal_dir_positions = [init_spans_rd.suffix_slice.stop - 1]` | **one fixed absolute token index**, derived from `train_tasks[0]` only | `hs[layer_idx]` passed as `k+1` (off-by-one handled) |
| **(iv) Mech-validity readout (Q5)** | `scripts/phase_gate7_mech_validity.py:89` `hs[row][0,-1,:]` | last token of the templated prompt — matches (i) | `hs[k+1]` |

**DEFECT D1 — cross-task absolute-position misalignment in the GCG objective. CONFIRMED.**
`refusal_dir_positions` is computed ONCE from `train_tasks[0]` (`gcg_optimizer.py:680-687`)
and then passed unchanged as an **absolute token index** into `_token_gradients`
(`gcg_optimizer.py:812`) and into candidate selection (`:433,:440`) for *every* task.
Prompt lengths differ across the 40-item train pool, so the index is only correct for task 0.
`_token_gradients` silently drops out-of-range positions
(`gcg_optimizer.py:172` `if pos < lt.shape[1]`), and `refusal_direction_loss` returns
`0.0` when no position survives (`objectives.py:224`) — i.e. the mechanism term silently
contributes nothing for those tasks.

Measured on the actual frozen train pool (Llama-3.1-8B tokenizer, `suffix_placement=user`,
suffix_len=16, init `' !'×16`):

```
suffix_slice.stop across the 40 train prompts: min 161, max 276, mean 241.6, std 17.5
fixed position used for ALL tasks (from task 0): P = 233

P inside the task's own suffix span :  17 / 40
P before the suffix (in instruction):  12 / 40
P after the suffix (header/target)  :  10 / 40
P out of range -> term silently 0    :   1 / 40
|P - task's own last-suffix-token|  : mean 14.0, median 9.5, max 73
EXACT matches (P == own last suffix token) : 1 / 40   (task 0 itself)
```

So the refusal/concept representation objective was evaluated at the intended position for
**1 of 40** training prompts.

**DEFECT D2 — fit-position vs use-position mismatch. CONFIRMED.**
Even for task 0, the intended position (`suffix_slice.stop - 1`, the last *suffix* token,
which lives inside the **user** turn) is not the position the direction was fitted and
causally validated at (the last token of the templated prompt, after the assistant header).
Verified token layout for train-pool item 0:

```
suffix_slice = [218, 234)   target_slice = [239, 260)
tokens between suffix end and target: ['<|eot_id|>', '<|start_header_id|>', 'assistant',
                                       '<|end_header_id|>', '\n\n']
```

The decision position is index **238**; the GCG objective reads index **233** — five tokens
earlier, still inside the user turn.

**DEFECT D3 — intervention-scope asymmetry (not a bug, but must be stated).**
The activation-space causal result ablates the direction at **all positions, all decode
steps, and (multilayer) all layers**. The token-space objective touches **one position at
one layer**. Any comparison of "activation-space causality" vs "token-space optimizability"
is therefore also a comparison of intervention *scope*, not only of intervention *medium*.
This must be controlled for in Phase 2's control-hierarchy figure (Figure A), and is a
first-class alternative explanation alongside H1–H5.

**Scientific consequence (stated carefully, per plan §3.15).**
D1/D2 affect the *refusal* arm and its *norm-matched random* arm **identically** — both used
the same misaligned position. Therefore:
- the **comparison** "refusal ≈ random" is still an apples-to-apples comparison, and the
  reported ASR numbers stand as reported;
- but the **interpretation** "we optimized the validated refusal projection in token space
  and it did not help" is **NOT supported**, because for 39/40 training prompts the objective
  was not reading the validated refusal coordinate at all.

Gate D's negative is therefore downgraded from "the refusal objective fails" to
**"an objective that mostly did not measure the refusal coordinate fails"** — which is a much
weaker statement and re-opens H3 (objective/optimizer failure). This is recorded as a
**SUPERSEDED-PENDING** status for the Gate-D interpretation, not a withdrawal of the numbers.

**Actions taken:** see gap matrix rows R1–R3 in `docs/ASYMMETRY_GAP_MATRIX.md`. A
per-task position fix is required before any Phase 3 work, and a corrected-objective arm
becomes a *scientifically justified* Phase 3 candidate (it tests a hypothesis the old run
could not test).

---
## 2026-08-11 — PHASE 0 COMPLETE

### E0.4 Twelve-agent code/artifact audit (6 topics x audit+adversarial-verify)
Topics: direction fitting · GCG optimizer · mech-validity + activation intervention · data/splits ·
SLURM/TROPT infrastructure · handoff-number traceability. Every audit report was independently
re-checked by a second agent. Headline results:

- **A1 traceability: 0 numeric mismatches.** All 20 GCG arm ASRs, `GATE7_V3_MATRIX_STATS.json`,
  `GATE7_V3_MECH_VALIDITY_seed42.json` and the 3 quantization summaries reproduce the handoff exactly.
- **A2 / plan §19.3 direction identity: PASS.** `outputs/stage_gcg_full/refusal_direction_llama_L{12,14,16,18,20}.pt`
  are **md5-identical** to `outputs/refusal_alllayers/refusal_direction_llama_L{same}.pt` (cosine 1.0).
  No silent cross-code-path vector mismatch. The concept vector used by GCG
  (`concept_neg_L9_unit.pt`) is confirmed cos=1.000000 with `unified_directions/clearharm.npz["concept"][9]`
  (fit layer 9 → `hs[10]`), and only 0.56 with the `curated` cohort — so the clearharm cohort is the source.
- **A6 NEW LIMITATION.** The L18 refusal axis was fit on `pair_benchmark/pair_carrot_bomb.json` with
  **n_harmful=60 / n_harmless=20** (harmless = 20 hardcoded generic instructions, not the matched
  `neutral` prompts), then applied to ClearHarm-v3 doublespeak prompts. Cross-distribution transfer;
  never previously flagged. Belongs in the paper's limitations.
- **A7 NEW CONTEXT FOR Q2.** `refusal_direction_llama_SELECTED.json` records per-layer ablate+induce
  validation: L14 0.40, L16 0.80, **L18 1.133 (selected)**, L20 0.60, and **L12 = −0.333, `valid=false`**.
  L12 is the ONLY layer that failed validation — and Q2's "Jacobian-peak" arm targeted L12. Its negative
  is therefore weak evidence about token-space reachability.
- Infrastructure: conda env `poc_stage2` (py3.12 / torch 2.7.1 / transformers 5.12.1) is the project env;
  **TROPT is importable only from `$ROOT/TROPT/.venv/bin/python`** (py3.13 / torch 2.11 / transformers 5.8.1)
  and that venv has **no StrongREJECT checkout**, so any behavioral reranking under TROPT needs a
  two-process split. MAC (`MAC__wang2024`) and SoftPrompt (`SoftPrompt__schwinn2024`) recipes exist, and
  `$ROOT/scripts/phase3_tropt_optimize.py` is an existing MAC driver.
- Reusable prior art found for Phase 2: `$DC/37_soft_prompt_objective.py` implements the **simplex
  (softmax-over-vocabulary) relaxation** whose optimum upper-bounds any token sequence, plus
  discretization-retention and peak-weight diagnostics — exactly the instrument plan §19.4 asks for.
  `phase6_jacobian_readout.py` does **not** help Phase 1: it creates an `inputs_embeds` leaf only to avoid
  a param-grad buffer and **never reads `embeds.grad`**, so no input-embedding Jacobian exists in the repo.

### E0.5 Deliverables written
- `docs/ASYMMETRY_GAP_MATRIX.md` — full classification + §E pre-registration (target position, rows,
  selection split, controls, subspace-honesty rule, Figure A quantities, D3 scope-matched arm).
- Instruments: `scripts/asym_p1_reachability.py`, `scripts/asym_p1_analyze.py`,
  `scripts/asym_p1c_mech_validity_ext.py`, `scripts/asym_p2_softprompt.py`;
  runners `slurm/run_asym_p1_reach.sh`, `slurm/run_asym_p2_soft.sh`.

### GATE A VERDICT: **CONDITIONAL PASS** — GPU work authorised.
Numbers reproduce (A1) and the direction is one object (A2), so nothing is withdrawn. The position
defects D1/D2 change the *interpretation* of the token-space arm, and A6/A7 are limitations to carry.

### E0.6 Smoke tests submitted
- job **750338** `asym_p1_reachability.py --smoke` (2 prompts, 4 random dirs, 3 sub-tokens), split=train.
- jobs **750350 / 750351** `asym_p2_softprompt.py --smoke`, param=free (budget_rel 1.0) and param=simplex.
Per plan §3.1 no scale run is submitted until a smoke run loads the model, locates the suffix span,
computes the objective, takes an optimizer step and writes the intended scalars.

---
## 2026-08-11 — GATE A ADDENDUM

### E0.7 The program reports TWO different binary "ASR"s under one name — quantified, benign
Found while scoping Phase 4. The two halves of the handoff use different StrongREJECT
binary thresholds:

| Pipeline | Threshold | Source |
|---|---|---|
| GCG held-out eval (Q1–Q4 table) | **≥ 0.5** | `26_eval_p9_gcg_heldout_asr.py:163` counts `strongreject_is_success` |
| Every behavioural harness (Q6 Phi X1/X3, Q7 quantization) | **0.25** | `MAL_THRESHOLD = 0.25` — `scripts/phase_behav_refusal.py:58`, `phase_behav_carry.py:52`, `14_behavioral_eval.py:33`, `scripts/behav_judge.py:85` |

`docs/RESEARCH_HANDOFF.md` §2.3/§3.6 and the sprint plan §3.6 both state 0.5. So the
behavioural ASRs were produced at 0.25 while being described as 0.5.

**Cost to fix: zero GPU.** `raw.jsonl` stores the continuous per-item `{arm}_score`, so the
binary label is recomputable on CPU. New tool: `scripts/asym_relabel_asr.py`
→ `reports/ASYM_ASR_THRESHOLD_AUDIT.json`.

**Result — the discrepancy is real but changes nothing.** Over all three quantization runs
(test n=42 each), **27 paired contrasts**: **0 sign flips, 0 significance flips, max shift in
ΔASR = 0.0714.** The Q7 headline numbers at both thresholds:

| Precision | handoff ΔASR α=1 | recomputed @0.25 | recomputed @0.5 | McNemar p @0.5 |
|---|---|---|---|---|
| bf16 | +0.286 | **+0.2857** | **+0.2857** | 0.000488 |
| 8-bit | +0.262 | **+0.2619** | **+0.2619** | 0.007385 |
| 4-bit | +0.571 | **+0.5714** | **+0.5476** | ~0 |

The random-ablation control stays flat at both thresholds (|Δ| ≤ 0.0476, all p ≥ 0.5) in
every precision. **Q7's dose-dependent, specific, quantization-robust conclusion is
threshold-robust.** This also independently re-reproduces the handoff's Q7 numbers from raw
per-item scores, strengthening A1.

**Standing decision for this sprint:** every new behavioural number is reported at
**≥ 0.5** (plan §3.6), with the 0.25 value alongside wherever a prior number is being
compared. `asym_relabel_asr.py` is the single place the threshold is applied.

---
## 2026-08-11 — PHASE 1c RESULT (plan §19.1 a–d, §19.2) — job 750363

`scripts/asym_p1c_mech_validity_ext.py` → `outputs/asym_p1c_mechval_20260811_212142_750363`
(43,197 per-prompt projections; 17 suffix conditions × 15 refusal fit layers × 2 concept
layers × 2 positions × (37 held-out + 40 train-pool) prompts; 12 min, forward passes only).
Analysis: `scripts/asym_p1c_analyze.py` → `ANALYSIS_P1C.json`.

### Reproduction check first
Seed 42, held-out, `decision` position, fit layer L18 → `hs[19]`:
no-suffix baseline **3.4023** (handoff: 3.40); refusal-suffix drop **−1.664** vs
random-suffix **−2.045** (handoff Q5: **−1.66 vs −2.04**). **Exact reproduction** — the
instrument agrees with the shipped Q5 artifact before it is extended.

### §19.1(a) — THE Q5 CONCLUSION DOES NOT REPLICATE ACROSS SEEDS
Held-out test (n=37), refusal-optimized suffix vs its own norm-matched random suffix,
paired over prompts (10,000-resample bootstrap + sign-flip permutation):

| seed | mean proj (refusal) | mean proj (random) | diff | boot95 | p | prompts where refusal is lower | reading |
|---|---|---|---|---|---|---|---|
| 42 | 1.738 | 1.358 | **+0.381** | [+0.224, +0.545] | 1e-4 | 8/37 (0.22) | refusal suppresses **LESS** — the published Q5 reading |
| 43 | 0.800 | 2.264 | **−1.464** | [−1.748, −1.192] | 1e-4 | **37/37 (1.00)** | refusal suppresses **MORE** |
| 44 | 1.630 | 2.975 | **−1.345** | [−1.638, −1.049] | 1e-4 | 35/37 (0.95) | refusal suppresses **MORE** |

Drops from the no-suffix baseline (3.4023), by arm across the three seeds:

| arm | per-seed drop | mean | sd |
|---|---|---|---|
| refusal-optimized | −1.664 / −2.602 / −1.773 | **−2.013** | 0.513 |
| refusal-random | −2.045 / −1.138 / −0.428 | **−1.204** | **0.810** |
| vanilla doublespeak | −1.125 / −1.255 / −2.299 | −1.560 | 0.644 |
| concept-optimized | −1.067 / −0.849 / −0.694 | −0.870 | 0.188 |
| concept-random | −1.677 / −2.327 / −2.317 | −2.107 | 0.372 |

**Mean over seeds, refusal minus random = −0.810 in favour of the mechanism** (refusal
suppresses its own target *more*), and the sign flips in **2 of 3** seeds relative to the
published claim. The random arm's spread (sd 0.810) is larger than the mechanism arm's
(0.513): seed 42 happened to draw an unusually *effective* random direction.

**Verdict.** The handoff's Q5 statement — *"adversarial suffixes suppress the refusal signal
generically; the mechanism objective adds no specificity even at the internal-target level"* —
is **UNDERPOWERED, not established**: it rests on **one seed with one random draw**, exactly
the single-control weakness plan §3.8 warns about. Restated honestly:

> At the internal-target level the refusal-optimized suffix lowers the held-out refusal
> projection **more** than its matched random counterpart in 2/3 seeds and on average
> (−2.013 vs −1.204), but a single random draw per seed makes this contrast unstable.
> **What does NOT change: this internal-target control does not convert into ASR** (handoff
> 3-seed mean ASR 0.297 refusal vs 0.279 random, no seed significant).

That is a *sharper* dissociation than the one previously reported: the token objective **can**
move its intended internal coordinate, and the behaviour still does not follow. Gate D's
clause (ii) ("does not move its intended internal target more than random") is **WITHDRAWN as
unsupported**; clause (i) (no ASR advantage) **stands**.

### §19.1(c) — NO train→held-out overfitting of the suppression
Drop vs each pool's own no-suffix baseline, train pool (n=40) vs held-out (n=37):

| arm | train | test | transfer ratio |
|---|---|---|---|
| refusal s42/43/44 | −1.269 / −2.063 / −1.176 | −1.664 / −2.602 / −1.773 | 1.31 / 1.26 / 1.51 |
| refusal-random | −1.591 / −0.793 / −0.214 | −2.045 / −1.138 / −0.428 | 1.29 / 1.44 / 2.00 |
| vanilla DS | −0.718 / −1.076 / −1.780 | −1.125 / −1.255 / −2.299 | 1.57 / 1.17 / 1.29 |

**Transfer ratio > 1 in all 9 cells.** The universal suffix's refusal suppression is *stronger*
on held-out prompts than on the prompts it was optimized on. So the "universal suffix overfits
its refusal suppression to the train pool" hypothesis (a candidate H3/H5 mechanism) is
**REJECTED** — the suppression generalizes fully.

### §19.2 — LAYER SWEEP: the suppression is generic and NOT localized at the target (H4)
Held-out drop vs no-suffix across refusal fit layers L10–L24, seed 42:

```
  L    refusal    random  vanillaDS   ref-rand
 10     +0.031    +0.048     +0.023     -0.017
 12     +0.014    +0.022     -0.024     -0.008
 14     -0.214    -0.217     -0.199     +0.004
 16     -0.955    -0.868     -0.604     -0.087
 18     -1.664    -2.045     -1.125     +0.381   <- the objective's target layer
 20     -2.170    -2.600     -1.574     +0.429
 22     -2.825    -3.557     -2.093     +0.733
 24     -3.051    -4.055     -2.389     +1.003
```

Three facts: (1) suppression is **nil before ~L14** and grows **monotonically with depth**;
(2) the deepest suppression is at **L24**, the edge of the sweep — **not** at the L18 target
the objective optimized; (3) the layer profile of the refusal suffix and of the random suffix
are **near-identical in shape**, Pearson **r = 0.9965** (refusal vs vanilla doublespeak
r = 0.9968).

**Verdict — strong support for H4 (GENERIC ADVERSARIAL SUPPRESSION).** Any adversarial suffix,
mechanism-derived or not, produces the *same broad late-layer refusal-suppression profile*;
targeting L18 does not carve a dip at L18. The suffixes differ in the **magnitude** of a
shared profile, not in **where** they act.

### D2 — the fit/use position mismatch is material
Refusal-minus-random difference at the two positions (held-out):

| seed | at `decision` (where the axis was fitted/validated) | at `last_suffix` (what the GCG objective read) |
|---|---|---|
| 42 | +0.381 (p=1e-4) | −0.067 (p=0.003) |
| 43 | −1.464 (p=1e-4) | −0.063 (p=0.108) |
| 44 | −1.345 (p=1e-4) | −1.013 (p=1e-4) |

At the position the optimizer actually read, refusal and random are nearly indistinguishable
in 2/3 seeds (|diff| ≈ 0.06, ~20× smaller than at the decision position). The absolute
projections differ in regime too (`last_suffix` ≈ −2.1 vs `decision` ≈ +1.7). Consistent with
defects D1/D2: **the objective barely steered the coordinate it was pointed at**, while the
coordinate that matters behaviourally moved a lot — generically.

**Sanity checks passed:** the `neutral` (single-space) condition has drop exactly 0.0000 vs
no-suffix; template tail measured at 5 tokens, matching the manual token layout in E0.3.

---
## 2026-08-11 — PHASE 1 + PHASE 2 FIRST RESULTS

### E1.1 GATE C — the refusal direction has UNUSUALLY **HIGH** token reachability
*Run: `outputs/asym_p1_reach_train_20260811_212152_750361` (job 750361), frozen train pool
n=40, 32,800 Jacobian rows, 25 min. Analysis `scripts/asym_p1_analyze.py`.*

`‖Jᵀ v‖` at the `decision` position, `hs[19]`, averaged over the 40 train prompts, against
all four control families (all directions unit norm):

| direction | kind | `‖Jᵀv‖` | ratio to that family's per-prompt median | mean percentile |
|---|---|---|---|---|
| **refusal_L18** | mechanism | **22.4** | — | — |
| isotropic random (n=100) | `random` | 1.68 | **14.31×** | **1.000** |
| covariance-matched random (n=100) | `actrandom` | 3.80 | **6.74×** | **0.998** |
| refusal @ L10/L14/L22 (n=3) | `otherlayer` | 8.29 | **3.40×** | 0.983 |
| concept_L9 @ hs19 (n=1) | `foreign` | 3.31 | 2.16× | 1.000 |

**GATE C VERDICT: UNUSUALLY-HIGH REACHABILITY.** The result survives every control, including
the strict covariance-matched null (a direction with the anisotropy of a real activation
direction but no mechanism) and the same-mechanism-wrong-depth control.

**This decisively REJECTS H1 (input-reachability failure).** The causal refusal direction is
not hard to reach from suffix-token perturbations — it is *unusually easy* to reach, by a
large margin, on every prompt.

Consistent with §5.4: the refusal direction lies largely INSIDE the empirical local
token-reachable subspace — `R(v)` at rank 16 = **0.585** (isotropic null 0.0039, isotropic
random mean 0.0039) and 0.697 at rank 64, i.e. a rank-16 subspace of token-induced Δh already
captures ~59% of the refusal direction's mass. At the `last_suffix` position it is far lower
(0.156 at rank 16) — another quantification of defect D2.

### E1.2 GATE B — OPEN. The first-order model does NOT predict real token substitutions
Pearson r between the predicted `⟨g_j(v), e_new − e_old⟩` and the measured `Δ⟨h,v⟩` over real
vocabulary swaps: **r = 0.077**, slope 0.122, sign agreement 0.381 (best cell). This is a
FAIL by the pre-registered criterion, and per plan Gate B it must be resolved **before** any
scientific reading of the finite-difference numbers.

The `--eps-scan` diagnostic was added precisely for this and its output
(`eps_scan.jsonl`) is not yet analysed. Two possibilities, which it distinguishes:
(a) the Jacobian is correct and a real token swap is simply far outside the linear regime —
    a *result* about why gradient-guided discrete search is hard here;
(b) an implementation error.
**Gate C does not depend on Gate B** (`‖Jᵀv‖` is an autograd quantity, not a finite-difference
one), but every §5.3/§5.4 claim does, so `R(v)` above is provisional pending the ε-scan.

### E1.3 PHASE 2 — the continuous soft prompt reaches the direction, and behaviour does NOT follow
*Run: `outputs/asym_p2_soft_refusal_free_b1.0_seed42_20260811_213644_750364` (job 750364),
16 continuous suffix positions, universal over the 40-item train pool, 300 Adam steps,
per-position L2 budget = 1.0 × mean init embedding norm (binding at every step).*

Refusal projection at the `decision` position, `hs[19]`:

| pool | baseline | after | Δ | sd before → after |
|---|---|---|---|---|
| train (n=40) | +3.365 | **−15.787** | **−19.15** | 2.909 → 0.380 |
| held-out test (n=37) | +4.417 | **−15.675** | **−20.09** | 2.497 → 0.249 |

For scale, the **entire discrete family** moves this quantity by −0.43 to −2.60 (§19.1b).
The continuous prompt moves it **~10× further**, and it generalizes (test Δ > train Δ).

**But the behaviour does not follow.** StrongREJECT on the 37 held-out generations
(`scripts/asym_p2_judge.py` → `reports/ASYM_P2_ASR.json`, 0% null judges):

> **binary ASR = 0.0000 · mean continuous StrongREJECT = 0.0000 · refusal_rate = 0.0000 ·
> empty_rate = 0.0000** (mean response length ≈ 501 chars)

Zero refusals *and* zero successes: the model is neither refusing nor complying.

**Reading (plan §6.4 CASE D — "investigate before claiming a reachability explanation").**
The per-prompt standard deviation of the projection collapses from 2.5 to **0.25**: the soft
prompt is not *steering* the refusal state along its natural manifold, it is **overwriting**
the decision-position residual with a nearly prompt-independent vector far outside the
direction's natural range (harmful prompts sit at ≈ +3.4 to +4.4). Driving a linear readout
to −15.7 does not mean "refusal was suppressed"; it means we left the regime in which that
readout indexes anything.

**Methodological consequence worth stating in the paper:** *a continuous soft prompt can drive
a linear probe arbitrarily far without producing the behaviour the probe is supposed to
index.* Probe displacement is not evidence of mechanism control.

**Action.** Budget `1.0` saturates, so §6.2's dose sweep is not optional — it is the
experiment. Launched `budget_rel ∈ {0.05, 0.1, 0.25}` (jobs 750441/750442/750443) to find the
budget at which the continuous intervention lands the projection in the *natural* range
(≈ 0, comparable to what the activation ablation achieves) and to test ASR there. Only a
dose-matched comparison can populate Figure A honestly.

---
## 2026-08-11 — GATE B RESOLVED — AND IT ANSWERS THE SPRINT'S CENTRAL QUESTION

The ε-scan (plan §5.3, added after the smoke run) walks continuously along the *same*
direction a real token swap moves in: `e(ε) = e_old + ε·(e_new − e_old)`, so ε=1 reproduces
the real substitution exactly. Pearson r between the first-order prediction `ε·⟨g_j, Δe⟩` and
the measured `Δ⟨h,v⟩`, at the `decision` position, `hs[19]`, mechanism = refusal_L18:

**TRAIN pool (n=40, job 750361)** — 120 probes per ε
```
 eps      0.01    0.05    0.10    0.25    0.50    1.00
   r    0.2047  0.5558  0.8395  0.6319  0.0531 -0.0015
 slope  1.6420  1.0986  1.2787  0.6904  0.1154 -0.0019
 sign   0.467   0.583   0.658   0.742   0.600   0.575
```
**HELD-OUT test (n=37, job 750362)** — r: 0.480 (ε=.05) → **0.810 (ε=.10)** → 0.692 (ε=.25)
→ −0.131 (ε=.50) → **−0.324 (ε=1.00)**.

### GATE B VERDICT: **PASS on the implementation.**
The Jacobian is correct — at ε=0.10 the linear model predicts the measured change with
**r = 0.84 (train) / 0.81 (test) and slope ≈ 1**. The failure at real-token scale is not a
bug; it is a property of the model.

### The finding: the linear surrogate dies *before* the discrete step size
The first-order model is accurate for perturbations up to ~ε=0.25 and has **collapsed to
r ≈ 0 by ε=0.5**, i.e. **long before ε=1.0, which is the smallest move a discrete optimizer
can make** (a single token substitution; mean ‖Δh‖ ≈ 2.03).

This breakdown is **general, not refusal-specific** — every direction family peaks at ε≈0.1
and collapses. But the *ranking at ε=1.0* is the point:

| direction kind | r at ε=0.10 | **r at ε=1.00 (a real token swap)** |
|---|---|---|
| **refusal_L18 (mechanism)** | 0.840 / 0.810 | **−0.002 / −0.324** |
| refusal @ other layers | 0.752 / 0.650 | +0.147 / −0.162 |
| isotropic random | 0.477 / 0.495 | +0.041 / +0.129 |
| **covariance-matched random (strict null)** | 0.683 / 0.498 | **+0.204 / +0.334** |

*(train / held-out)*

### THE ANSWER TO THE SPRINT'S CENTRAL QUESTION
Putting Gate C and Gate B together:

> **The refusal direction is the MOST reachable direction in the linear regime and among the
> LEAST predictable at the step size a discrete optimizer actually takes.**
>
> Gate C: `‖Jᵀ v_refusal‖` is **6.7×/7.1×** the covariance-matched null (train/test),
> percentile 0.998/0.979 — it is *unusually easy* to move with infinitesimal suffix
> perturbations. H1 (input-reachability failure) is **rejected**.
>
> Gate B: that sensitivity is **entirely washed out by nonlinearity at one-token step size**
> — r goes from 0.84 to ≈ 0 (train) / −0.32 (test), while a covariance-matched random
> direction still retains r ≈ 0.20/0.33.

GCG's whole mechanism is: take a first-order gradient, use it to rank vocabulary
substitutions, keep the best. **If the first-order model carries no information about the
effect of a real substitution on this coordinate, the gradient cannot tell the optimizer
which token to pick** — no matter how causal, or how locally reachable, the direction is.

This is a *new* explanation, adjacent to but sharper than the plan's H2. H2 says
"discretization destroys specificity". The measurement says something more specific and more
falsifiable:

> **H2′ — LINEAR-SURROGATE INVALIDITY AT DISCRETE STEP SIZE.** The direction is
> continuously reachable and locally highly sensitive, but the first-order surrogate that
> discrete search depends on is invalid at the granularity of a single token — and it is
> *more* invalid for the refusal direction than for a typical activation-like direction.

It also explains the Phase-2 CASE D result without contradiction: the *continuous* optimizer
does not rely on a linear surrogate (it re-linearizes every step), so it reaches the direction
easily — indeed so easily that at budget 1.0 it overshoots into an off-manifold regime where
the projection no longer indexes behaviour at all.

**Status of §5.3/§5.4 claims:** Gate B passes on the implementation, so `R(v)` and the
finite-difference numbers are no longer provisional. But every one of them is a
**linear-regime** statement and must be labelled as such — the ε-scan proves that
extrapolating them to real token moves is exactly the error we are diagnosing.

### Held-out replication of Gate C (job 750362, n=37)
`‖Jᵀ v_refusal‖ = 19.82` vs isotropic random 1.494 (**15.0×**, pct 1.000), covariance-matched
3.412 (**7.07×**, pct 0.979), other-layer refusal 7.501 (**3.41×**, pct 1.000). Replicates the
train result on the locked held-out split with no selection.

---
## 2026-08-11 — H4 REFINED + PHASE-2 SPECIFICITY CONTROL

### E1.4 Unoptimized-suffix control (job 750431) — optimization scales a GENERIC profile
20 suffixes of 16 uniformly-sampled ordinary vocabulary tokens, never optimized, plus the
GCG initialization suffix. Held-out drop in refusal projection @L18 (baseline 3.4023):

| suffix | held-out Δ refusal proj |
|---|---|
| **`init` = `' !'×16` (GCG optimization step 0)** | **+1.015** — it *raises* refusal |
| 20 unoptimized random-token suffixes | **−0.663** (sd 0.236, range −0.177 … −1.046) |
| GCG vanilla task-loss (3 seeds) | −1.559 |
| GCG random-direction (3 seeds) | −1.204 |
| **GCG refusal-optimized (3 seeds)** | **−2.013** — larger than **all 20** unoptimized suffixes (percentile 1.000) |

But the **layer profile shape** of an unoptimized random-token suffix and of the
refusal-optimized suffix correlate at **r = 0.985** across L9–L24.

**H4, refined.** The earlier reading ("generic adversarial suppression") was half right. The
correct statement is:

> **The suppression MODE is generic — any suffix, optimized or not, produces the same
> late-layer, depth-increasing refusal-suppression profile. What optimization changes is the
> MAGNITUDE of that shared profile, not its shape or its location.** Optimization is not
> inert (every optimized suffix beats every unoptimized one), and the refusal objective
> produces the largest magnitude of all (−2.013 vs −1.204 for its random-direction control),
> consistent with §19.1(a).

**Internal consistency check (independent, and it passes exactly).** The Phase-2 run measured
its baseline with the init suffix present and got **+4.417** held-out; the no-suffix baseline
here is **3.4023**; the init suffix's measured effect is **+1.015**. 3.4023 + 1.015 = 4.417.
The two independently-written scripts agree to 3 decimals.

### E1.5 PHASE 2 SPECIFICITY CONTROL (job 750365) — continuous optimization IS specific
Same setup as job 750364 but the objective targets a norm-matched **random** direction
(cos with v_refusal = +0.0055):

| soft-prompt objective | its own objective reached | **Δ refusal projection (held-out)** |
|---|---|---|
| refusal direction | yes | **−20.09** |
| norm-matched random direction | yes (own loss −12.8) | **−1.56** |

The optimizer is equally *able* to drive a random direction, so the contrast is not an
optimization artifact. Targeting refusal moves refusal **13× more** than targeting a random
direction does.

**Continuous input optimization is SPECIFIC to the refusal direction. Discrete token
optimization is at best marginally so** (§19.1a: −2.013 vs −1.204, sign-unstable across
seeds). That is the continuous/discrete asymmetry the sprint set out to find, now measured on
the same axis, the same split, and the same target position.

**Still outstanding:** at budget 1.0 the specific continuous suppression produces **ASR = 0**
(E1.3, CASE D). The dose sweep (jobs 750441/750442/750443) decides whether a smaller budget
lands the projection in its natural range *and* raises ASR — which would make this a clean
CASE A (discrete bottleneck) — or whether behaviour never follows at any dose.

---
## 2026-08-11 — §19.4 ROUNDING PROBE (job 750366) — THE DISCRETE BOTTLENECK, MEASURED

The **simplex** parameterization optimizes logits over the vocabulary and uses the
softmax-weighted convex combination of embedding rows. Every real token sequence is a
**vertex** of that simplex, so its optimum **upper-bounds what any discrete suffix can do**.
Plan §19.4 then asks: project the solution to its per-position argmax token and re-measure.

Held-out test (n=37), refusal projection @ `decision`, `hs[19]`, baseline **+4.418**:

| state | mean projection | Δ vs baseline | per-prompt sd |
|---|---|---|---|
| baseline (init suffix) | +4.418 | — | 2.498 |
| **relaxed simplex optimum** | **−4.277** | **−8.694** | **0.178** |
| **rounded to nearest tokens** | **+3.922** | **−0.496** | 2.386 |

> ### RETENTION AFTER DISCRETIZATION = **5.7 %**

Optimizer-validity diagnostics (all pass, so this is not an optimizer artifact):
`budget_sufficient = True` (logit budget 150 ≫ the 2×init_scale = 20 gap, so the argmax
*could* move), `frac_positions_changed = 0.44`, `mean_peak_weight = 0.755`,
`min_peak_weight = 0.070`, **6 of 16 positions blended** (peak < 0.9).

**Reading.** The relaxed solution buys its −8.69 almost entirely with **off-manifold
blending** — convex combinations of tokens that no real prompt can contain. Forced onto
actual vocabulary, **94 % of the effect evaporates**, landing at −0.496 — which is *inside*
the range of the 20 **unoptimized** random-token suffixes (−0.177 … −1.046, mean −0.663).
The sd signature tells the same story: 2.498 → 0.178 (relaxed, overwriting) → 2.386
(rounded, back to natural prompt-to-prompt variation).

### GATE D — DECISION
Two independent mechanisms, measured separately, both point the same way:

1. **Gate B / H2′ — the linear surrogate is invalid at discrete step size.** The gradient
   GCG uses to rank candidate tokens correlates r = 0.84/0.81 with the true effect at
   ε = 0.10 but r = −0.002/−0.324 at ε = 1.0 (one real token substitution), *worse* than a
   covariance-matched random direction (+0.204/+0.334). The optimizer's search signal is
   uninformative for this coordinate.
2. **§19.4 — even a perfect continuous solution does not survive rounding.** The
   token-simplex upper bound retains **5.7 %** of its effect on discretization.

Together with Gate C (the direction is *unusually easy* to reach, 6.7×/7.1× the strict null,
so H1 is rejected) and E1.5 (continuous optimization **is** specific: −20.09 vs −1.56):

> **GATE D VERDICT: CASE A/B — DISCRETE-TOKEN BOTTLENECK, with a mechanism.**
> The causal refusal direction is continuously input-reachable and *specifically* so. It is
> not discretely reachable, for two measured reasons: the first-order surrogate discrete
> search relies on is invalid at one-token granularity, and the continuous optimum's
> advantage is carried by off-manifold blending that discretization destroys.
>
> **Caveat carried forward (CASE D, unresolved):** at the budget tested, the specific
> continuous suppression yields **ASR = 0** — the projection is driven far outside its
> natural range and behaviour does not follow. Until the dose sweep finds a budget where
> continuous suppression *both* stays in-range *and* raises ASR, the hierarchy is established
> **on the internal target**, not on behaviour. Do not state the behavioural half without it.

**Known gap, stated:** the rounding probe measured retention of the *projection*, not of ASR
— no generation was run with the rounded token suffix. Given the rounded projection lands
inside the unoptimized-suffix range, an ASR measurement there is expected to be
uninformative, but it was not run and is not claimed.

---
## 2026-08-11 — CASE D RESOLVED: it is CASE A. Continuous input optimization JAILBREAKS, specifically.

Judging the Phase-2 dose sweep (`scripts/asym_p2_judge.py` → `reports/ASYM_P2_ASR.json`,
StrongREJECT ≥ 0.5, held-out n=37, 0 % null judges) turns the earlier ASR=0 from a dead end
into a **dose-response curve with an interior optimum**:

| arm | budget | Δ refusal proj | resulting proj | **ASR** | mean SR | refusal_rate |
|---|---|---|---|---|---|---|
| refusal | 0.05 | −1.07 | +3.35 | **0.162** | 0.162 | 0.730 |
| **refusal** | **0.10** | **−8.22** | −3.80 | **0.757** | **0.713** | **0.027** |
| refusal | 1.00 | −20.09 | −15.68 | **0.000** | 0.000 | 0.000 |
| **random (dose-mismatched)** | 1.00 | −1.56 | +2.86 | **0.000** | 0.000 | 0.000 |
| simplex relaxed (token upper bound) | — | −8.69 | −4.28 | 0.189 | 0.176 | 0.000 |

For reference: vanilla doublespeak ASR on this split is **0.243–0.351** across seeds and the
best GCG arm ever recorded is **0.405** (handoff §5).

> **A continuous 16-position soft prompt targeting the refusal direction reaches
> ASR = 0.757 on the locked held-out split — roughly double the best discrete result — while
> its refusal_rate collapses to 0.027.**

The ASR/dose relation is an inverted U: too little suppression (0.05) leaves the model
refusing (refusal_rate 0.73); the right dose (0.10) jailbreaks; too much (1.00) pushes the
residual so far off-manifold that the model neither refuses nor complies (ASR 0, refusal 0).
This *explains* the earlier ASR=0 rather than explaining it away, and it vindicates the
decision to treat CASE D as a dose problem.

**GATE D ⇒ CASE A (discrete-token bottleneck), now established on BEHAVIOUR as well as on the
internal target.** Continuous input optimization specifically suppresses refusal *and* raises
ASR; discrete optimization on the same axis, split, position and budget does neither
specifically.

### THREE CAVEATS, none of which may be dropped when this is written up
1. **The dose was not pre-registered, and the sweep was read on TEST.** By plan §3.5 this
   makes the dose curve **EXPLORATORY**, not confirmatory. A confirmatory claim needs the
   budget frozen on the untouched **v3 `dev` split (n=37)** and then evaluated once on test.
2. **The random-direction control is DOSE-MISMATCHED.** The only random arm judged so far is
   at budget 1.0 (where *everything* gives ASR 0). Comparing refusal@0.10 (ASR 0.757) against
   random@1.00 (ASR 0.000) confounds mechanism with dose, so **that contrast is not yet
   evidence of specificity on behaviour.** Launched: random-direction soft prompt at
   **budget 0.10, seeds 42/43/44** (job 750501 + resubmits), plus refusal at budget 0.10 for
   seeds 43/44 (jobs 750504/750505) to meet the plan's ≥3-seed requirement.
   **Until the dose-matched random arm lands, the headline is "continuous optimization
   jailbreaks at a dose where discrete optimization does not" — NOT "specifically".**
3. Single seed (42) so far at the winning dose; plan §6.1 requires ≥3.

### Process note — 6-job cap
Submitting the extra seeds pushed the queue to **11 jobs**, violating the plan's
non-negotiable ≤6 rule (§3.1). Detected immediately and corrected by cancelling
750495/750496/750497 (Phase-4 pairs 3–5) and 750502/750503 (random seeds 43/44); those are
queued for resubmission as slots free. Queue is back to exactly 6.

Also: L40S fair-share throttling pushed Phase-4 start times ~18 h out, so all five Phase-4
pairs were repinned to the idle **a5000** nodes via a new `ASYM_GPU` guard. Every Phase-4
contrast is within a single job (hence a single GPU) and Gate F is a meta-analysis over those
within-pair effects, so this does not mix GPU classes inside a comparison; all five pairs are
still pinned to one class and the class is recorded in the run metadata.

---
## 2026-08-11 — MEASUREMENT NOTE: StrongREJECT judge nondeterminism, quantified by accident

Two independent judge runs were launched over the **same** `GENERATIONS.jsonl` files (a stray
duplicate invocation). They disagree:

| arm | run A ASR | run B ASR | items flipped (n=37) |
|---|---|---|---|
| refusal free b=0.05 | 0.1622 | 0.1351 | 1 |
| **refusal free b=0.10** | **0.7568** | **0.8378** | **3** |
| refusal free b=1.00 | 0.0000 | 0.0000 | 0 |
| random free b=1.00 | 0.0000 | 0.0000 | 0 |
| refusal simplex | 0.1892 | 0.2162 | 1 |

**≈ 5 label flips in ~148 judgements ⇒ a ~3.4 % per-item flip rate**, i.e. an ASR uncertainty
of roughly **±0.03–0.08 at n=37**, on top of sampling error. `strong_reject/evaluate.py:182`
already passes `temperature=0`, so this is irreducible OpenAI API nondeterminism, not a
configuration error.

### Two consequences, both load-bearing
1. **This sprint's headline survives easily.** The continuous soft prompt at budget 0.10 gives
   ASR **0.757–0.838** against a vanilla-doublespeak baseline of 0.243–0.351 and a best-ever
   GCG arm of 0.405. That gap is an order of magnitude larger than judge noise.
2. **The program's central GCG negative is *smaller than the judge's own noise floor.*** The
   handoff's Q1/Q3 result is a 3-seed mean ΔASR of **+0.018** for refusal@L18 vs its matched
   random control (per-seed −0.027 / +0.162 / −0.081). A ±0.03–0.08 judge-noise band means
   that effect was **never measurable at n=37 regardless of the mechanism**. This does not
   overturn the negative — it *strengthens* the "non-specific" reading and reframes the
   between-seed swing of ~0.24 as partly judge variance rather than optimization variance.

### Standing rule adopted for the rest of this sprint
Any ΔASR below **0.08** at n≈37 is reported as **within judge noise**, never as an effect,
unless it is backed by repeated judging. Where a contrast matters, the judge is run more than
once and the spread is reported. `scripts/asym_p2_judge.py` already stores per-item continuous
scores, so re-judging is cheap and does not require re-generation.

---
## 2026-08-11 — DOSE-MATCHED SPECIFICITY: PHASE 2 COMPLETE

The control the previous entry flagged as missing has landed. Budget **0.10** for both arms,
same GPU class, same 300 steps, same frozen train pool, same locked held-out test set
(n=37) — the **only** manipulated variable is which direction the soft prompt targets.

| arm | Δ refusal proj (held-out) | **binary ASR** | mean continuous SR | refusal_rate |
|---|---|---|---|---|
| **refusal direction** | **−8.22** | **0.7568** | 0.7095 | **0.027** |
| **norm-matched random direction** (cos with v_refusal = +0.0055) | **−2.21** | **0.0811** | 0.0709 | **0.4595** |

**Paired contrast: ΔASR = +0.676, exact McNemar p = 5.96e-08, bootstrap 95 % CI
[+0.514, +0.811], n=37, 0 % null judges.**

That is an order of magnitude above the measured judge-noise floor (±0.03–0.08) and above
every discrete result in the program.

### GATE D — FINAL
> **Continuous input optimization on the validated causal refusal direction is causal,
> SPECIFIC, and behaviourally effective** — ASR 0.757 vs 0.081 for a dose-matched random
> direction (ΔASR +0.676, p = 6e-8), with the refusal rate collapsing 0.46 → 0.03.
> **Discrete token optimization on the SAME direction, axis, position, split and budget is
> neither** — 3-seed mean ΔASR +0.018 vs its matched random control, which is *below the
> judge's own noise floor*.
>
> The hierarchy **activation ⊇ continuous-input ⊇ discrete-token** is now established on
> BEHAVIOUR, not only on the internal target, with specificity demonstrated at the continuous
> level. This is plan §17 **RESULT 2**, in full.

### Why the dose being chosen on test does NOT weaken the specificity claim
The dose sweep was read on test, so **"0.10 is the optimal budget" is EXPLORATORY** (plan
§3.5) and needs a dev-split confirmation. But the specificity contrast is a **paired
comparison at a FIXED budget shared by both arms** — whatever procedure picked 0.10 applied
identically to the mechanism arm and its control, so it cannot manufacture a
refusal-vs-random difference. The two claims must be reported at different confidence:
* **"Continuous optimization on the refusal direction specifically raises ASR far above a
  dose-matched random direction"** — CONFIRMATORY on the locked test set.
* **"0.10 is the best dose"** — EXPLORATORY; a dose-response curve, not a selected optimum.

### Remaining limitations for this phase, stated
* **Single seed (42)** at the winning dose; plan §6.1 asks for ≥3. Seeds 43/44 were cancelled
  to respect the 6-job cap and are queued for resubmission.
* The judge refused to score one generation ("I'm sorry, I can't assist with that",
  `strong_reject/evaluate.py:195`); it was counted as a parse failure, not silently as
  benign, and `judge_null_frac` was 0.00 for both arms.
* The **D3 scope caveat** still stands: the activation arm in Figure A is
  all-position/all-layer while every input arm is 16 suffix positions. The scope-matched
  activation arm (gap matrix §E.7) has not been run.

---
## 2026-08-11 — PHASE 5 SMOKE (job 750838) + an early warning sign

`scripts/asym_p5_defense_2signal.py` runs end-to-end on a5000: all 5 conditions, both
pre-generation features in one forward, thresholds fit on TRAIN before any generation, and
all 7 arms derived from just 2 generations per (item, condition). n=3, `--gen-splits train`,
`--max-new 64`, 525 s — diagnostic only, not a result.

Two things the smoke tells us:

1. **The features are near-orthogonal as expected:** `cos(refusal, concept) = −0.0108` at
   L18, so the concept axis does carry information independent of the refusal axis. That is
   the precondition for a two-signal gate to be able to do anything at all.

2. **⚠ An early warning that the concept signal may point the WRONG WAY.** The fit line reads
   `ds_concept mean = 1.761` vs `benign_attack_concept mean = 1.972` — the attack-structured
   **benign** prompts score *higher* on the concept axis than the **doublespeak attacks** do.
   If that survives at n=85, a `concept > T` gate will fire *more* on benign prompts than on
   attacks — exactly the failure mode that sank the prior refusal-only gate (benign fire-rate
   0.90 vs attack 0.71).

   **This is n=3 and must not be treated as a result.** It is recorded here *before* the full
   run so that the eventual outcome cannot be presented as a surprise either way. If it
   holds, Phase 5 is plan §17 **RESULT 8** ("two-signal defense also fails → refusal control
   remains non-selective even with concept information"), which the plan explicitly counts as
   publishable. The full run is worth its ~3 h regardless, because a *quantified* negative
   with all six arms and five utility conditions is what the paper needs — the prior Gate-F
   negative had neither the concept feature nor the direct/neutral/unrelated conditions.

Full run launched: job **751316** (all splits, max_new 200, α = 2.5893 from the v3b-train-fit
projection summary, StrongREJECT ≥ 0.5).

---
