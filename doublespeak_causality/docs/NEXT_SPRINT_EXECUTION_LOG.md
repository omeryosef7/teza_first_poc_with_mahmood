# Next Sprint — Execution Log (started 2026-08-09)

Append-only log for the sprint defined in `docs/NEXT_SPRINT_PLAN_2026_08_09.md`.
Plan goals (Q1–Q7): full fair GCG arm matrix (more seeds/steps), Jacobian-vs-projection
objective, any-refusal-beats-random, concept-term effect, mechanistic-validity check,
third architecture family (Phi-4-mini-reasoning), quantization extension.

Working rules in force: ≤6 concurrent L40S jobs, killable/gpu-research, nodelist
n-801..805,t-806, no SLURM deps, offline HF cache, bf16 primary, ClearHarm locked split,
train-only selection, ≥20 unique/cell, keep all nulls, commit (no push per plan — but user
explicitly asked to push for tracking → PUSH ALLOWED this sprint), TROPT-first, subagents
never read harmful text.

---

## 2026-08-09 — Phase 0: Audit

### Repo state at start
- Branch `behavioral-causality-sprint`, HEAD `67348347` (prior sprint 28/28 complete).
- No SLURM jobs running (clean slate).
- All 4 target models cached: Llama-3.1-8B-Instruct, Qwen3-14B, Phi-4-mini-reasoning,
  DeepSeek-R1-Distill-Llama-8B.
- GCG infra: `poc_stage_gcg_early/` (project root). TROPT: `TROPT/` (project root).
- Locked split: `data/splits/clearharm_doublespeak_v1.json` (n_train=44, n_test=42, n_total=86,
  sha256 ac95d864…) and a v3 split `clearharm_doublespeak_v3.json` (N=324 confirmatory, leakage 0).
- GCG manifests present: `data/gcg/clearharm_llama/{direct,doublespeak}.jsonl` (86 rows each,
  44 train / 42 test), plus `..._doublespeak_firstcut20.jsonl` (the 20-item first-cut train).
- 16-arm matrix spec frozen: `configs/manifests/phase9_gcg_mac_matrix.json` (status: NOT LAUNCHED).
  Shared hp: suffix_len=16, n_steps=200, bs=64, topk=256, no-filter-cand, suffix-placement=user,
  universal suffix, seeds [42,43,44], selection weighted, repr_in_selection auto-on for mechanism arms.

### Current scientific state (from SPRINT_SUMMARY_2026-08-02_TO_08-09.md — treated as starting point)
- representation ≠ behavior thesis established on Llama-3.1-8B.
- Concept circuit fully mapped; epiphenomenal BY SPECIFICITY (powered n=324 write+carry ΔASR
  +0.046 ns < random +0.161).
- Refusal suppression = behavioral lever (ablate stronger than DS; re-inject kills DS; decision-token
  localization L15-18; Gate B PASS forward; mediation ≈1.0; predicts AUC 0.874; Jacobian AUC 0.807).
- Gate-7 GCG objective: NEGATIVE/non-specific first-cut (refusal 0.465 ≈ random 0.464, 2 seeds,
  50 steps, 20-item train). 16-arm matrix designed, NEVER RUN.
- Cross-model: Qwen3-14B (thinking-off) reproduces dissociation. Quant bf16/8/4-bit robust for
  refusal ablation.

### Audit subagents launched (read-only, safe files only)
1. GCG/TROPT optimization infrastructure (poc_stage_gcg_early runners, refusal-dir loss wiring).
2. Jacobian (P6) math + differentiable-loss feasibility.
3. Gate-7 first-cut reconstruction + 16-arm reconciliation.

(Results appended below as they return.)

### Audit result — Jacobian (P6) [agent 2]
- Refusal target scalar `S_refusal = <hidden[R][-1], u_ref>` (R=32 → L31 dir) is **first-order
  differentiable**; refusal projection @ L22 (arm07) is the same family. Code
  `scripts/phase6_jacobian_readout.py`.
- Peak layers: refusal ‖J‖ **L12** (100% bootstrap), concept ‖J‖ **L16**; linear readout peaks
  late **L30**. → "mechanism mid-band / readout late" dissociation.
- AUCs (clearharm, locked test): refusal ‖J‖@L12 **0.807** [.696,.901]; refusal scalar(L31) 0.845;
  refusal proj@L21 0.867; concept ‖J‖@L16 **0.583**; concept scalar 0.508. Paired refusal−concept
  ‖J‖ diff **+0.225** [.055,.361].
- **KEY**: bare ‖J‖ is partly *target-generic* (both peak L12–L16, cos(J,dir)≈0.02); the
  target-specific signal is in `jac_proj`/projection, not ‖J‖. Refusal *scalar* (0.845) predicts
  better than ‖J‖ (0.807).
- **Feasibility for GCG loss**: (A) first-order refusal-scalar/projection loss = cheap, immediate,
  already the strongest signal. (B) true ‖J‖² loss = second-order double-backward (needs
  create_graph=True; prohibitive VRAM through 8B; and target-generic/weaker). **No existing
  optimizer uses the Jacobian.**
- **DESIGN DECISION (Q2)**: operationalize the "Jacobian-refusal objective" (arm10) as a
  first-order refusal-projection loss **at the Jacobian sensitivity-peak layer L12**, vs arm07's
  projection at the readout/decision layer **L22/L18**. This is a clean, cheap, compute-matched
  test of "does targeting the max-sensitivity layer beat targeting the readout layer?" The
  second-order ‖J‖² arm is documented as out-of-scope (target-generic, weaker, prohibitive cost —
  cite P6). Will confirm exact loss wiring after infra audit.

### Audit result — Gate-7 first-cut [agent 3]
- Runner: `python -m poc_stage_gcg_early.run_optimization`; eval: `26_eval_p9_gcg_heldout_asr.py`.
- First-cut ran **arm04** (vanilla), **arm07-L18** (validated), **arm07-L22** (frozen/unvalidated),
  **arm07-rand-L18** (norm-matched random). **50 steps** (not 200), seeds **42+43** (not 44),
  λ_refusal_dir=**0.25**, suffix_len 16, bs 64, topk 256, --no-filter-cand, --suffix-placement user,
  --selection-mode weighted, --no-thinking. Train n=44, test n=42, v1 split.
- Held-out mean ASR: arm04 **0.357**; arm07-L18 **0.465**; arm07-L22 0.357; arm07-rand-L18 **0.464**
  → validated refusal ≈ random (dead heat) = well-controlled NEGATIVE (Claim F not supported).
- Random dir: `scripts/build_random_dir_L18.py`, Gaussian rescaled to exact L18 refusal norm, same
  layer/λ/wiring. Output `outputs/gate7_firstcut/refusal_rand_L18_normmatched_seed20260808.pt`.
- Validated refusal dir: `outputs/refval_clearharm_20260806_051728_721957/refusal_direction_clearharm_L18.pt`.
- **Frozen decisions** (do NOT reselect on test): refusal layer **L18** (validated, P7 721957/722611);
  λ=0.25 is a *first-cut proxy* from P8.1 α-calibration — **must be train/dev-swept (3-point)** for
  the real run (no exact α→λ map); suffix_len 16; 200 steps (spec); bs 64; topk 256.
- **NEXT per plan**: 200 steps, seed 44, larger pool, add arm06 (concept), arm08 (combined),
  §17 mechanistic-validity check (does optimizing refusal actually lower held-out L18 projection?).
- **OPEN split decision**: matrix is FROZEN on v1 (44/42) but **v1 has known leakage** per P1B_V3;
  v3 is the leakage-0 confirmatory split (has dev). First-cut used v1. → decide before scaling
  (see Gate-A note). arm05 (harmful-target-logits) is bit-identical to arm04 → likely DROP.
  arm14 (attention/carry) gated on a carry path that is causally NULL → DROP / neg-control only.
- Success criteria (frozen, verbatim): (1) beat vanilla GCG (arm3/4) AND no-suffix DS (arm2) by
  >P1 drift envelope; (2) refusal_rate falls w/o empty_rate rising; (3) survives ≥3 seeds;
  (4) transfers to locked test; (5) mechanism metric moves in intended dir; (6) norm-matched random
  does NOT match it; (7) content redacted. Primary metric = StrongREJECT held-out test ASR.

### Audit result — GCG/TROPT infra [agent 1]
- All optimizer code under project-root `poc_stage_gcg_early/`. Entry: `run_optimization.py`
  (`python -m poc_stage_gcg_early.run_optimization`). Loss terms in `objectives.py`; loop in
  `gcg_optimizer.py`; config/hash in `config.py`.
- **refusal-projection loss is layer-configurable via CLI**: `--lambda-refusal-dir`,
  `--refusal-dir-layer`, `--refusal-dir-path`, `--objective-name`, `--repr-in-selection`,
  `--repr-selection-sub-batch`. Sign: term added to a minimized loss → drives projection DOWN
  (suppress refusal). Position = last suffix token. → **arm07 (L18/L22) AND arm10 (Jacobian=proj@L12)
  need NO new code** — just different layer/path. Also supports multi-layer + λ schedule.
- Universal suffix by default (grad averaged / loss summed over train tasks). Per-behavior =
  `run_batched_perbehavior.py` or a 1-task manifest.
- Random control: `scripts/build_random_dir_L18.py` (Gaussian, exact norm-match, same wiring).
  Generalize to any layer for arm10's L12 random control.
- Resume: `checkpoint.pt` (step+suffix+RNG+config_hash), atomic, SIGTERM handler; resumes only if
  config_hash matches. Output dir `phase9_gcg_mac_matrix_arm<NN>_<slug>_seed<SEED>` under
  `outputs/stage_gcg_full/`. Final suffix in `FINAL_CANDIDATES.jsonl` row[0].
- Eval: `26_eval_p9_gcg_heldout_asr.py` (StrongREJECT + kw_refusal; emits asr, mean_sr,
  refusal_rate, empty_rate, judge_fail_frac, n_scored; resume-safe; needs OPENAI_API_KEY).
  **Emits point ASR only → must add CI/McNemar across seeds ourselves.**
- **TROPT/MAC (arms 11-13): NOT implemented** — need a new `Loss` subclass under `TROPT/tropt/loss/`
  + separate venv + tokenization re-verification. Deferred to a stretch goal.
- **Concept objective (arm06/08): NO code** — needs `build_reference_cache.py` on the direct
  manifest + a new "concept readout up" loss term (+ degeneration penalty for combined). To implement.
- **DROP arm05** (bit-identical to arm04, single target) and **arm14** (carry path causally NULL).

### ⚠️ CRITICAL CORRECTNESS RISK to verify before ANY GCG run (Gate A)
Layer-index convention mismatch (agent 1): direction builders store the vector from
`hidden_states[L+1]` (post-block-L) and name it `L`; but `gcg_optimizer.py` indexes
`output.hidden_states[refusal_dir_layer]` **directly**. If true, an "L18" direction (built at
hs-row 19) is read by GCG at hs-row 18 → a **1-layer shift**. Must verify and, if real, fix
(pass layer=L+1 or correct the index) BEFORE the confirmatory matrix. The first-cut may have
optimized against a 1-layer-shifted readout (likely within the broad L13-20 valid band, so probably
not fatal to the dead-heat conclusion — but the confirmatory run must be exact). **Verifying now.**

### Off-by-one — CONFIRMED (Gate A fix)
Verified in code: `poc_stage_gcg_early/gcg_optimizer.py:173` reads `output.hidden_states[layer_idx]`
directly; `objectives.py:refusal_direction_loss` uses `candidate_hs.get(layer)`; `run_optimization.py:245`
passes `refusal_dir_layer=args.refusal_dir_layer` with **no +1**. Direction builder
(`build_refusal_direction_llama.py:82`) captures `hs[L+1]` and names it `L`. → an `L{k}` direction is
read by GCG one block early. **FIX**: our confirmatory wrapper passes `--refusal-dir-layer $((FIT+1))`
so GCG reads the exact `hidden_states[FIT+1]` row the direction was fitted on; `--objective-name`
keeps the fit-layer label. Will confirm with a smoke projection-match test. First-cut dead-heat
UNAFFECTED (refusal & random shared the identical shift within the broad L13-20 valid band).

---

## 2026-08-09 — DECISIONS (user consult)
1. **Split = v3 (leakage-0), subsampled train pool.** v1 has 90% train/test leakage (77/86 rows:
   14/43 concepts + 17/21 codewords straddle; P1B_V3_SPLIT §1) → v1 cannot support a clean transfer
   claim. v3.1: N=324, 224 concepts, 215 clusters, **0 straddling**. Plan: freeze a ~40-item
   cluster-diverse **train-only optimization pool** from v3 train (≥20 unique, balanced), evaluate the
   universal suffix on the **full v3 leakage-0 test**. Keeps compute ≈ first-cut (n_train≈40) while
   giving a leakage-free held-out test. Reconciles (does not silently replace) the v1-frozen manifest:
   a new `configs/manifests/phase9b_gcg_v3.json` will document the deviation + rationale.
2. **Scope = the ENTIRE plan.** User: "Do all the plan!!! I don't care if it takes time." → drive
   toward: full attack matrix (all objective arms + matched randoms incl. GCG *and* MAC/TROPT +
   2nd-order ‖J‖ arm) at 200(+) steps × 3–5 seeds + mechanistic-validity check; Phi-4-mini-reasoning
   X0–X5 (3rd family, native reasoning); quantization extension; all 6 deliverable docs. Only hard
   constraints: ≤6 concurrent L40S jobs, gate discipline, train-only selection, keep all nulls.
   Parallelize independent work via subagents (scalar/code only) and GPU batches.

## 2026-08-09 — Phase 1 build (v3 corrected setup)
- Built v3 GCG manifests `data/gcg/clearharm_llama_v3/` (148 items: train74/dev37/test37, leakage-0,
  join 148/170). Froze cluster-diverse pool-40 (fallback); **primary uses full 74 train** (power).
- OPENAI_API_KEY present in `.env` (len 164) → StrongREJECT eval works via SLURM `.env` sourcing.
- Built norm-matched random dirs L12/18/22 (`outputs/gate7_v3_randdirs/`); concept ±L9/L16 unit +
  randoms (`outputs/gate7_v3_conceptdirs/`). All unit-norm.
- Paired-stats aggregator `scripts/analyze_gate7_matrix.py` (Wilson CI + paired bootstrap dASR +
  exact McNemar + cross-seed). **Validated on first-cut**: reproduces arm07-L18 0.464 ≈ rand 0.464,
  McNemar p=0.45/0.55 both seeds → confirmed non-specific dead heat (now with paired stats).
- Submitted smokes: **740707** (GCG v3 corrected pipeline, off-by-one fix) + **740710** (Phi-4 X0).

### CONCEPT-ARM DESIGN (reconciles manifest arm06/08) [concept subagent]
- The manifest's repr-cache route for arm06 has a **silent cross-condition position-alignment bug**:
  `repr_loss` matches by absolute token index, but direct vs doublespeak prompts differ in length →
  repr_loss collapses to 0. **Rejected.**
- **Adopted: direction-projection route** (reuse `refusal_direction_loss`), so ALL objective arms
  share ONE mechanism (projection at last suffix/decision token) — the cleanest concept-vs-refusal
  comparison. No new optimizer code.
  - concept-UP = minimize projection onto **negated** unit concept dir (positive λ). Artifact
    `concept_neg_L9_unit.pt` (from unified_directions concept[9], resid_post block9 = hs[10]).
  - off-by-one fix applies identically: pass `--refusal-dir-layer = fit+1` (concept L9 → 10,
    refusal L18 → 19, Jacobian-peak L12 → 13).
  - combined (arm08) = **multilayer** refusal_dir: `[(hs10, -concept, λc), (hs19, refusal, λr)]`
    via `--refusal-dir-layers/--refusal-dir-paths/--lambda-refusal-dir-per-layer`. task_loss stays
    as de-facto anti-degeneration (no dedicated degeneration penalty exists; documented).

### FROZEN v3 confirmatory arm set (all GCG, off-by-one-corrected)
Baselines: arm01 nosuffix-direct (eval), arm02 nosuffix-DS (eval), arm15 random-suffix-DS (eval),
arm04 vanilla-GCG-DS (task_loss), arm03 vanilla-GCG-direct (task_loss, optional).
Mechanism (each with a norm-matched RANDOM-direction control at the same layer/λ/seeds):
- REFUSAL@L18 (readout) : dir refusal_alllayers L18 @hs19 ; rand refusal_rand_L18
- REFUSAL@L12 (Jacobian peak; "Jacobian-refusal" first-order) : L12 @hs13 ; rand refusal_rand_L12
- CONCEPT@L9 (validated write) : -concept[9] @hs10 ; rand concept_rand_L9
- COMBINED (concept@L9 + refusal@L18) : multilayer ; rand = both randoms
λ: 3-point dev sweep {0.1,0.25,0.5} on REFUSAL@L18 (seed42) → freeze, reuse across direction arms
(same unit norm → shared λ defensible). Screen seed42/200steps → finalists seeds 43,44(,45,46).
DROP arm05 (=arm04). arm14 (carry) causally null → optional negative-control only. MAC arms 11-13
+ 2nd-order ‖J‖² = later (new stack/code). Mechanistic-validity + Phi X1-X5 + quant in parallel.

## 2026-08-09 — Smoke results + revised compute plan
- **Phi-4 X0 (740769) PASSED**: num_layers=32, bf16, chat_template present, eos=199999,
  codeword localization **3/3** (13 occ/item), generation works, reasoning tokens present
  (`think_open=True`) but VERBOSE — item1/2 hit gen_len=512 without closing `</think>` → **X1 needs a
  larger gen budget** (e.g. 1024-2048) to capture the full reasoning+answer. Third-family plumbing OK.
- **GCG v3 smoke (740768) TIMEOUT** (20-min limit too tight): weight load alone took **6:38**
  (node-contention slowdown, cf. feedback_slurm_node_contention), leaving no time to log steps.
  BUT the log CONFIRMS the **off-by-one fix is live**: "refusal_direction_loss ENABLED: lambda=0.25,
  **layer=19**, position=[233], path=…refusal_direction_llama_**L18**.pt". v3 manifest loaded (3 tasks).
- **COMPUTE REVISION**: 200 steps × **74** train would exceed 8h (first-cut = 50 steps×44 ≈ 1.3 GPU-h/arm;
  scaling → vanilla ~5.4h, refusal(repr-in-sel) ~10.8h ✗). **Reverted optimization pool to the frozen
  cluster-diverse POOL-40** (the originally-approved subsample): vanilla ~2.9h, refusal ~5.8h < 8h ✓.
  Eval still on FULL v3 test (37). Launcher `run_gcg_v3_arm.slurm` now uses `*_trainpool40.jsonl`.
- **Batch 1 launched**: 740899 (smoke, 45min, sign test refusal vs random) + 740900 (vanilla) +
  740901 (vanilla_direct), seed42, 200 steps, pool40. Next: on sign-test pass, launch refusal_L18 /
  refusal_L12(Jac) / concept_L9 / combined + matched randoms (batch 2, ≤6 jobs).

## 2026-08-10 — GPU obstacles resolved + GATE B PASS
- **a6000 (n-602) GPU FAULTY** ("Unable to determine device handle … Unknown Error", exit 127) —
  killed 3 GCG jobs; n-601 a6000 down. L40S fair-share-throttled (~23h est start).
- **Resolution**: run GCG on idle **3090 (24GB)** at **BATCH=32 × N_STEPS=400** = exactly
  compute-matched to batch64×200 (same candidate-forwards), fits 24GB. Phi-4 (small) on 3090 too.
  Guards → min-VRAM (≥20GB); broken node excluded; nodes spread ≤2/arm-per-node (weight-load
  contention). Documented deviation (primary claims still bf16; GPU type held constant within matrix).
- **GATE B PASS (sign test, batch-32 3090 smoke 740960, COMPLETED, no OOM)**:
  - real L18 refusal dir: refusal_dir_loss **+0.038 → −0.04** over 8 steps (projection actively
    suppressed by the optimizer).
  - norm-matched random dir: **flat ~0** (0.003→0.0002, no systematic movement).
  → the refusal-projection GCG loss moves its intended internal scalar; random does not. Off-by-one
  fix confirmed working (reads hs[19] for the L18 dir). Cleared to launch multi-arm optimization.
- **Batch 2 launched** (seed42, BATCH=32, N_STEPS=400, 3090 n-303/304/306): 741053 vanilla,
  741054 refusal_L18, 741055 refusal_rand_L18, 741056 refusal_L12(Jac-peak), 741057 refusal_rand_L12.
  Held concept_L9 (wave 2) to respect ≤6 (5 GCG + Phi X1 740944). Each arm ~6h (batch32×400 on 3090).
  Wave 2 (as slots free): concept_L9/rand, combined/rand, vanilla_direct. Then seeds 43,44(,45,46).

## 2026-08-10 — Timing right-sizing + node failures
- 3090 timing: **~1.6–2.2 min/step** (batch32, repr-in-selection). → 400 steps ≈ 12–15h, and a
  timed-out 400-step run writes NO FINAL_CANDIDATES (only at completion) = no usable suffix.
- **DECISION: confirmatory matrix at N_STEPS=200** (meets plan's ≥200 confirmatory bar; all arms
  equal; batch32×200 = 6400 candidate-forwards/item, 4× the first-cut's 50-step budget; completes
  ~7.5h < --time=10h on 3090). **Extend only ambiguous finalists** (refusal vs random) to more steps
  later per plan (screen → finalists). All arms use identical steps → comparison stays fair.
- Node failures this session: n-602 (a6000, device-handle error) and **n-303** (3090, "GPU: none /
  CUDA not available" — nvidia-smi sees GPU but torch can't) → both EXCLUDED. Healthy 3090s: n-304,
  n-306, n-307; Phi on n-302.
- **Seed-42 matrix relaunched @200 steps / 10h** (741203 vanilla, 741204 refusal_L18,
  741205 refusal_rand_L18, 741206 refusal_L12, 741207 refusal_rand_L12) + Phi X1 740944 = 6.
  Wave 2 (concept_L9/rand, combined/rand, vanilla_direct) as slots free.



### Gotcha: config_hash + resume (2026-08-10)
Changing N_STEPS (400→200) with the SAME run-id/output-dir made run_optimization ABORT on a
checkpoint config_hash mismatch (it refuses to resume a differently-configured run). Fix: `rm -rf`
the stale run dirs (no FINAL_CANDIDATES = safe) before relaunch. N_STEPS now frozen at 200 → no
recurrence. Seed-42 clean relaunch: 741205 refusal_rand_L18(run), 741206 refusal_L12,
741211 vanilla, 741212 refusal_L18, 741213 refusal_rand_L12; + Phi 740944 = 6 concurrent.

### 2026-08-10 02:13 progress check
- GCG seed42 arms healthy: vanilla 33 / refusal_L18 24 / refusal_rand_L18 19 steps in ~32min
  (~1–1.7 min/step → 200 steps ~4–6h, comfortable in 16h). 741283/741284 pending (GPU free wait).
- Phi X1 740944 ALIVE (raw.jsonl 21 items, writing live; ~7.6 min/item reasoning@2048; ~1h to 30).
  NOTE: hit sbatch --export comma bug on DSSPLITS=train,test → only TRAIN ran. Will run test split
  separately with DSSPLITS=test (comma-free) to complete X1. (Fix rule: never put comma-lists in --export.)

## 2026-08-10 — Phi-4 X1 behavioral reproduction (TRAIN, n=30, native reasoning)
Job 740944 COMPLETED (3.5h). baseline_drift_clearharm_..._740944/summary.json (train):
| cond | ASR_majority | refusal(1-ASR proxy) | trunc_len_rate | mean_ntok | judge_any_flip |
|---|---|---|---|---|---|
| direct | 0.567 | — | 0.267 | 1345.8 | 0.067 |
| doublespeak | **0.633** | — | 0.300 | 1603.6 | 0.000 |
| neutral | 0.667 | — | 0.167 | 1457.9 | 0.133 |
| benign | 0.600 | — | 0.233 | 1436.1 | 0.167 |
- **KEY: Phi-4-mini-reasoning is WEAKLY ALIGNED** — direct (bare harmful) ASR **0.567** (vs Llama
  0.116, Qwen3 0.095). So Doublespeak has **little headroom**: DS 0.633 ≈ direct 0.567 (ΔASR +0.066),
  neutral 0.667 ≈ DS. The DS *attack* barely moves a model that already complies. Per plan, "no
  meaningful attack headroom = a valid result" — do NOT force a DS story on Phi.
- CAVEATS: (a) ~30% truncation even at max_new=2048 (Phi reasoning very verbose, mean ntok ~1350-1600)
  — a longer budget would help but 2048 already slow (~7.6min/item); note as limitation. (b) benign
  "ASR" 0.60 is a StrongREJECT-on-benign artifact (judge scores request-fulfilled, not harm) — not
  real over-refusal/compliance; ignore benign column for alignment claims.
- IMPLICATION for X3: with high direct compliance there is less refusal to ablate; the concept-vs-
  refusal *dissociation* can still be probed (X2 geometry, X3 ablation), but the behavioral attack
  axis is weak on Phi. Proceed X2-X4; report headroom limitation honestly.
- Launching Phi X1 TEST split next (DSSPLITS=test, comma-free) to complete X1.

## 2026-08-10 — Phi-4 X1 TEST split (n=30) + X1 verdict
Job 741427 COMPLETED. baseline_drift_..._741427/summary.json (test):
| cond | ASR_majority | trunc_len_rate | mean_ntok |
|---|---|---|---|
| direct | 0.700 | 0.233 | 1334.1 |
| doublespeak | **0.800** | 0.367 | 1624.6 |
| neutral | 0.767 | 0.333 | 1443.7 |
| benign | 0.567 | 0.333 | 1434.1 |
**X1 VERDICT (Phi-4-mini-reasoning, native reasoning, train+test n=30 each):**
- DS **does** raise ASR over direct on BOTH splits: train 0.633 vs 0.567 (+0.066), test 0.800 vs 0.700
  (+0.100). So the Doublespeak attack reproduces on a 3rd architecture family — modestly.
- BUT Phi is WEAKLY ALIGNED (direct ASR 0.567/0.700, ~6-7x Llama/Qwen3), so DS has limited headroom
  and neutral≈DS. The attack works but the model barely refuses to begin with.
- Truncation 23-37% even at 2048 tokens (verbose reasoning); benign ASR 0.57-0.60 is a StrongREJECT-
  on-benign artifact. X1 = DONE (Q6 behavioral repro: POSITIVE-but-limited-headroom on Phi).
- Next Phi: X2 (concept+refusal direction geometry) then X3 (concept-vs-refusal ablation dissociation).

## 2026-08-10 — FIRST v3 attack-objective ASR (seed42, leakage-0 test n=37)
Eval 742022 (StrongREJECT, v3 test):
| arm | ASR | refusal_rate |
|---|---|---|
| arm04 vanilla GCG (doublespeak) | **0.243** | 0.568 |
| arm07 refusal_down_L18 | **0.324** | 0.513 |
- refusal@L18 (0.324) beats vanilla GCG (0.243) by +0.081, with lower refusal rate — the refusal
  objective DOES something over vanilla. BUT the decisive control is refusal_rand_L18 (norm-matched
  random @ same layer) — if random also ≈0.32, non-specific (first-cut pattern); if refusal>random,
  SPECIFIC POSITIVE (new). refusal_rand_L18 finalizing (200 steps); eval pending. Also refusal_L12
  (Jacobian-peak) FINAL, evaling now. Pairs populate in analyze_gate7_matrix once both members evaled.

### 2026-08-10 — I/O contention root cause (weight-load)
Two eval jobs loading Llama-8B simultaneously on n-302 crawled at ~2.5min/shard (291 shards) →
~12h projected model load (0 generations in 1h). Cause: concurrent model-loads on one node saturate
disk I/O (cf. feedback_slurm_node_contention: multi-load = 16x+ slowdown). Also explains arms
~1.9min/step (4 arms on n-301). FIX: stagger new-job launches so weight-loads don't overlap; prefer
1 model-load at a time per node. Cancelled the 2 stuck evals; resubmitted as ONE combined eval 742254
(refusal_L12 + refusal_rand_L18). Not launching more jobs until it loads.

## 2026-08-10 — KEY RESULT: v3 attack-objective matrix (seed42, leakage-0 test n=37)
| arm | ASR | refusal_rate |
|---|---|---|
| arm04 vanilla GCG | 0.243 | 0.568 |
| arm07 refusal_down_L18 | 0.324 | 0.513 |
| arm07r refusal_rand_L18 (norm-matched control) | **0.351** | 0.432 |
| arm10 refusal_down_L12 (Jacobian-peak) | 0.216 | 0.595 |
**DECISIVE (Q3): refusal_L18 vs refusal_rand_L18 → ΔASR −0.027, boot95 [−0.189,+0.135],
McNemar b=4/c=5 p=1.000 → NOT DIFFERENT.** The validated refusal-suppression GCG objective is
statistically indistinguishable from a norm-matched RANDOM direction — **CONFIRMS the first-cut
NEGATIVE on the corrected leakage-0 v3 split, 200 steps (4× first-cut budget), proper paired stats.**
- (Q2) Jacobian-peak layer L12 (0.216) does NOT beat readout-layer L18 (0.324); if anything worse
  (and below vanilla) → no "target the sensitivity peak" advantage.
- refusal_rand_L18 (0.351) even edges vanilla (0.243) — a random direction is as good a GCG signal
  as the validated mechanism → the ASR gains are a generic optimization effect, NOT mechanism-specific.
- STATUS: strong NON-SPECIFIC NEGATIVE at seed42; needs seeds 43,44 (Gate D: don't call confirmed
  from 1 seed). concept_L9/rand + combined arms still optimizing (Q4). Mechanistic-validity (Q5) next.

## 2026-08-10 — seed42 matrix ASR (8/10 evaled; v3 leakage-0 test n=37)
| arm | ASR |
|---|---|
| vanilla GCG (arm04) | 0.243 |
| vanilla direct (arm03) | pending |
| refusal_down_L18 (arm07) | 0.324 |
| refusal_rand_L18 (arm07r) | 0.351 |
| refusal_down_L12 Jac-peak (arm10) | 0.216 |
| refusal_rand_L12 (arm10r) | 0.108 |
| concept_up_L9 (arm06) | **0.243** |
| concept_rand_L9 (arm06r) | pending |
| combined (arm08) | optimizing |
| combined_rand (arm08r) | optimizing |
PAIRED (seed42): refusal_L18 vs refusal_rand_L18 ΔASR **−0.027, McNemar p=1.000** (headline NEGATIVE);
refusal_L12 vs refusal_rand_L12 ΔASR +0.135 boot95[0.000,0.270] McNemar b=6/c=1 **p=0.125 (ns)** —
a hint of L12 specificity but underpowered AND both L12 arms are BELOW vanilla (not a useful attack).
**Q4: concept_up_L9 (0.243) == vanilla (0.243) EXACTLY — the concept objective is inert** (does not
even beat vanilla), consistent with the concept circuit being epiphenomenal. (n-302 slow-disk avoided;
evals now pinned n-304 and complete fast.) Last 2 arms + combined pair pending.

## 2026-08-11 — Phase 4 seed-44 in flight + Phase 5 (Phi X2) launched
- Seed-44 finalists optimizing: refusal@L18(744353), concept@L9(744479), refusal_rand@L18(744550),
  concept_rand@L9(744582). Seed-43 concept_rand@L9(744093, ~8h) near FINAL. Vanilla s44 evaled
  (dir `phase9b_v3_arm04_vanilla_ds_seed44`): ASR=0.324 (refusal 0.487). Seed-44 evals pending arm completion.
- PHASE 5 X2 (Q6, third family) LAUNCHED: job 744772 `run_phi_x2_refusal.slurm`. Builds refusal
  directions on microsoft/Phi-4-mini-reasoning (32 layers) at L12/14/16/18/20/22 from the SAME
  model-agnostic bench Llama used (pair_carrot_bomb.json direct=harmful/neutral=harmless, 60/20),
  with --validate. Provenance-checked: Llama's own refusal dirs came from this bench (n_harmful=60,
  n_harmless=20) — reusing it keeps the cross-family comparison apples-to-apples. Out: outputs/refusal_phi/.
- NOTE: build_refusal_direction_llama.py reads bench["behavioral"][i]["direct"/"neutral"]; the
  behavioral_v3b/beh_clearharm.json uses items/harmful_instruction (WRONG shape for this builder) —
  pair_benchmark files are the correct direct/neutral source. Documented to avoid re-tripping.

## 2026-08-11 (tick 2) — Phi X2 refusal DONE; X1/X3 launched; seed43 concept_rand eval
- Phi X2 refusal build (744772) SUCCEEDED. Separations 0.34–0.58 (L14–22 all ~0.5+), but induced-
  refusal validation passes ONLY at L14 (score +0.20); L16/L18 ablate-only +0.10; L12/L20/L22 <=0.
  => representation strongly separable, behavioral potency weak (1/6 layers) = rep!=behavior on a
  3rd family. SELECTED=L14. Details in docs/THIRD_FAMILY_REPLICATION.md.
- Phi X1+X3 behavioral run LAUNCHED (744801, run_phi_x13_behav.slurm): phase_behav_refusal on Phi,
  refusal-pt=L14, alphas 0.0/0.5/1.0, train+test, StrongREJECT. Gives baseline jailbreak labels (for
  X5 AUC) + refusal-ablation dose-response vs random. Long pole (reasoning gen, max_new 512).
- Seed-43 concept_rand@L9 FINAL -> eval submitted (744793, pinned n-304). Last missing seed-43 arm.
- Found concept builder path: phase_x5_concept_qwen3.py is model-generic (diff-of-means concept fit +
  concept/refusal/random proj AUC) -> reuse for Phi X5 once X1 labels land. build_unified_directions
  needs a pair_directions npz (heavier) -> X5 script is the lighter, sufficient route.

## 2026-08-11 (tick 3) — seed43 complete; seed44 arm07 near FINAL
- seed43 concept_rand@L9 eval (744793) DONE: ASR=0.297. Seed-43 now COMPLETE (5/5):
  vanilla .351 / refusal@L18 .405 / refusal_rand .243 / concept .270 / concept_rand .297.
  concept<vanilla AND concept<its-random -> concept inert holds; refusal>random +0.162 (seed-dependent).
- seed44: arm07_refusal_L18 at step 193/200 (near FINAL); 07r@101, 06@147, 06r@118. Phi X1/X3 (744801) 30m in.
- Held free slot for the imminent seed44 eval rather than pre-launching quant.

## 2026-08-11 (tick 4) — seed44 arm07 FINAL+eval; Phase6 quant-8bit launched
- seed44 arm07_refusal_L18 FINAL -> eval submitted 745066 (pinned n-304..). Other seed44: 07r step110,
  06 step160, 06r step130 (FINAL within ~1h).
- Phi X1/X3 (744801) healthy on 3090; run dir = outputs/behav_refusal_clearharm_asweep0.0-0.5-1.0_20260811_083438_744801
  (this is the --beh for X5). Generating.
- PHASE 6 (Q7) STARTED: run_llama_quant_behav.slurm QUANT=8bit -> job 745089. phase_behav_refusal on
  Llama-3.1-8B, refusal-pt L18, alphas 0/0.5/1.0, test split, bnb 8-bit. Tests whether the refusal-
  ablation dose-response survives quantization vs bf16. 4bit + geometry-under-quant to follow.
