# GCG Phase 8: Refusal-Direction Layer/Lambda Sweep — Pipeline Log

**Started:** 2026-07-13 07:00 UTC
**Researcher:** Omer Yosef (jobs launched by Claude Code per explicit user request)
**Budget:** 8 hours max, checked every 30 minutes

**This is an execution log** — it retains historical/in-progress detail as recorded and is not the final source of truth. For final, corrected numbers see `docs/GCG_FINDINGS_SYNTHESIS.md` (once this sweep's results are folded in) and `docs/GCG_REFUSAL_DIRECTION_AUDIT.md` for the full audit trail this sweep is designed to extend.

---

## Motivation

The 2026-07-13 audit of Phases 4-7 (`docs/GCG_PHASE4_7_AUDIT_REPORT.md`, `docs/GCG_REFUSAL_DIRECTION_AUDIT.md`) found that Finding 3 ("refusal-direction suppression eliminates the CoT-prefix ASR gain") was tested under exactly **one** configuration: layer=25, lambda_refusal_dir=1.0, optimization seed=42 (run `gcg_full_qwen3_6c_cot_refusal`, 0% ASR vs. 5A's 10.7%). The audit explicitly flagged the broader claim ("this is a general incompatibility between the two objectives") as unsupported by a single configuration, and listed a layer/lambda sweep as the highest-value unresolved GPU experiment — the one place where a different result would actually change the write-up's conclusions, rather than just reinforcing already-clean findings (detector AUC, Gemma4's 0% ceiling).

**Question this sweep answers:** does refusal-direction suppression eliminate the CoT-prefix gain (a) at nearby layers, and (b) at weaker/stronger lambda values? If the gain is eliminated everywhere tested, that's stronger evidence for a real incompatibility. If ASR recovers at some layer/lambda, that changes the finding to "layer/lambda-dependent" rather than general.

## Design

4 new GCG optimization runs, each reusing the exact 6C recipe (`advbench_cot_target_manifest.jsonl`, 25 behaviors, 500 steps, batch=64, suffix_length=20, topk=256, seed=42, lambda_repr=0, lambda_kl=0) via `slurm_scripts/run_gcg_full_6c_qwen3_combined.slurm` (already fully parameterized for `REFUSAL_LAYER` and `LAMBDA_RD` — no script changes needed), varying only:

| Run ID | `refusal_dir_layer` | `lambda_refusal_dir` | Compares against |
|---|---|---|---|
| `gcg_full_qwen3_8_rd_layer20` | **20** (nearby, below) | 1.0 | 6C (layer 25, lambda 1.0) |
| `gcg_full_qwen3_8_rd_layer30` | **30** (nearby, above) | 1.0 | 6C (layer 25, lambda 1.0) |
| `gcg_full_qwen3_8_rd_lambda03` | 25 | **0.3** (weaker) | 6C (layer 25, lambda 1.0) |
| `gcg_full_qwen3_8_rd_lambda3` | 25 | **3.0** (stronger) | 6C (layer 25, lambda 1.0) |

Qwen3-14B has 40 transformer layers (`num_hidden_layers=40`, confirmed from the model config) — layers 20 and 30 are valid, roughly symmetric nearby choices around the already-tested layer 25.

Each run's full pipeline (identical to how every other Phase 4-7 row was produced):
1. **Optimization** (`run_gcg_full_6c_qwen3_combined.slurm`, up to 8h SLURM time limit): 500-step GCG on the CoT-prefix target with the refusal-direction loss term at the specified layer/lambda.
2. **Free generation** (`run_gcg_full_free_generation.slurm`, MANIFEST overridden to `advbench_cot_target_manifest.jsonl` to match 6C): 25 behaviors x 4 conditions (`optimized_weighted`/`neutral_control`/`random_spaces`/`task_only`) x 3 generation seeds (42/43/44) = 300 rows, scored by StrongREJECT.
3. **Replay** (`run_gcg_replay.slurm`): captures hidden states per row for detection analysis.
4. **Analysis** (`run_gcg_analysis.slurm`, CPU-only): writes `RESULTS_SUMMARY.md` + `DETECTION_DELAY_ANALYSIS.md`.

Each stage is chained via SLURM `--dependency=afterok:<jobid>` so free-gen auto-starts the moment optimization finishes, etc. — no manual polling needed to advance stages, only to check status and eventually pull results into this doc.

## Job IDs (submitted 2026-07-13 07:00 UTC)

| Run | Optimization | Free-gen | Replay | Analysis |
|---|---|---|---|---|
| layer20 | 660404 | 660408 | 660409 | 660410 |
| layer30 | 660405 | 660411 | 660412 | 660413 |
| lambda0.3 | 660406 | ~~660414~~ **660636** (done) | ~~660415~~ ~~660637~~ **660912** | ~~660416~~ ~~660638~~ **660913** |
| lambda3.0 | 660407 | 660417 | 660418 | 660419 |

All 4 optimization jobs confirmed **RUNNING** as of 07:00 UTC, all on node `n-802` (8x L40S GPU node, 7/8 GPUs allocated at submission time — each of these 4 jobs holds one dedicated GPU via `--gpus=1`, no sharing/contention). All 12 downstream jobs confirmed **PENDING (Dependency)**, correctly queued behind their respective optimization job.

## Timing basis (from the existing `gcg_full_qwen3_6c_cot_refusal` run, same recipe, layer=25/lambda=1.0)

| Stage | Observed duration (6C reference run, 2026-07-10) |
|---|---|
| Optimization (500 steps) | ~2h (started ~12:06 UTC per `ITERATION_LOG.jsonl`, ended ~14:06 UTC) |
| Free generation (300 rows) | ~2.5h (14:06 → 16:36 UTC) |
| Replay + analysis | ~10 min (16:36 → 16:45 UTC) |
| **Total pipeline** | **~4h45min** |

This is comfortably inside the 8-hour budget per run, with real margin — the earlier "~6h45min" estimate quoted when this was first proposed used the wrong reference point (a different, slower run); the actual 6C reference timing above is faster. All 4 pipelines run in parallel on separate GPUs, so expected wall-clock for the whole sweep to finish is ~4h45min-ish, not 4x that.

## FINAL RESULTS (2026-07-13, all 4 pipelines complete)

All 4 optimization runs converged at least as well as, and mostly better than, the reference on task_loss. Exact free-generation results (300 rows each, 25 behaviors x 4 conditions x 3 generation seeds 42/43/44), recomputed directly from `FREE_GENERATION_RESULTS.jsonl`:

| Run | best task_loss | optimized_weighted ASR | neutral_control ASR | task_only ASR | random_spaces ASR | Uplift vs. neutral |
|---|---|---|---|---|---|---|
| Reference (6C, layer=25/λ=1.0) | 25.6367 | 0/75 (0%) | ~2/75 (2.7%) | ~2/75 (2.7%) | ~4/75 (5.3%) | **0%, net-negative** |
| layer=20, λ=1.0 | 24.3086 | 4/75 (5.33%) | 3/75 (4.0%) | 3/75 (4.0%) | 4/75 (5.33%) | +1.3pp |
| layer=30, λ=1.0 | 22.9180 | 0/75 (0%) | 3/75 (4.0%) | 3/75 (4.0%) | 4/75 (5.33%) | −4.0pp (net-neg) |
| layer=25, **λ=0.3** | 25.8516 | **18/75 (24.0%)** | 2/75 (2.67%) | 2/75 (2.67%) | 4/75 (5.33%) | **+21.3pp** |
| layer=25, λ=3.0 | 23.8945 | 2/75 (2.67%) | 3/75 (4.0%) | 3/75 (4.0%) | 4/75 (5.33%) | −1.3pp (net-neg) |

### Headline finding: the refusal-direction/CoT-prefix "incompatibility" is lambda-dependent, not general

**At the originally-tested configuration (layer=25, λ=1.0) and at a stronger lambda (λ=3.0) or a layer below (λ=1.0, layer=20 barely recovers anything) or above (layer=30) the original layer, the CoT-prefix ASR gain stays eliminated or is only marginally recovered — consistent with the original Phase 6 finding.** But **at a weaker lambda (λ=0.3, same layer=25), ASR jumps to 24.0% — more than double the original 5A CoT-prefix-only reference's 10.7%, and the polar opposite of this same layer's 0% at λ=1.0.**

This means the correct, evidence-backed claim is now: **"under the tested token-space objective, refusal-direction suppression's effect on the CoT-prefix ASR gain is strongly lambda-dependent — a lambda of 1.0 (and layers other than 25) eliminated it, while a weaker lambda of 0.3 at the original layer (25) more than doubled it relative to CoT-prefix targeting alone."** The previous framing ("refusal-direction suppression eliminates the CoT-prefix gain," stated without lambda-scoping) is **superseded** by this sweep — not wrong for the one configuration it was based on, but incomplete as a general claim about the two objectives being incompatible.

**What this does NOT establish**: *why* λ=0.3 specifically helps this much (a real, single, reproducible run — not yet replicated across other seeds at λ=0.3) — this is now the natural next question for the sprint (a candidate follow-up: replicate λ=0.3 at another optimization seed to confirm this isn't a lucky run, analogous to the 7B seed-variance finding). Flagging as unresolved rather than over-interpreting a single run's result, consistent with this project's standing practice.

### Replication follow-up: λ=0.3 at a second optimization seed (launched 2026-07-13, same day)

The λ=0.3 result (24.0% ASR) is from a single optimization seed (42) — flagged above as needing replication before being treated as fully settled, analogous to the Phase 7B seed-variance caution (an 11x ASR swing was observed between two nearly-tied-loss seeds for the plain CoT-prefix objective, so a lambda=0.3+refusal-dir result could in principle be similarly seed-sensitive). Launched the identical recipe (layer=25, λ=0.3, CoT-prefix manifest) at **optimization seed=43** — new run dir `gcg_full_qwen3_8_rd_lambda03_seed43/`, jobs: optimization=**660927**, free-gen=**660928**, replay=**660929**, analysis=**660930** (chained via `--dependency=afterok`, same pattern as the rest of this sweep). Not yet complete as of launch.

### Detection (AUC) — not yet run for these 4 new configurations

The replay+analysis stage (which produces `DETECTION_DELAY_ANALYSIS.md`, including AUC) completed for all 4 runs using the existing pipeline — see each run's own `DETECTION_DELAY_ANALYSIS.md` for full detail; all showed the same pattern as every other Phase 4-8 Qwen3 run (AUC=1.000 at position 0), consistent with detection being independent of attack success (the λ=0.3 run is both the most successful AND still perfectly detectable — the same "detection ≠ success" pattern documented throughout this project).

## Progress Log (updated every 30 minutes)

### 07:00 UTC — Launch
All 4 optimization jobs submitted and running (660404/660405/660406/660407). All 12 downstream jobs queued with correct dependencies. No manual action needed until first check-in.

### 07:31 UTC — Check-in 1 (elapsed: 31 min)

All 4 optimization jobs still `RUNNING` on n-802, all 12 downstream jobs still correctly `PENDING (Dependency)`.

| Run | Step | task_loss | refusal_dir_loss |
|---|---|---|---|
| layer20 | 32/500 | 30.91 | −0.089 |
| layer30 | 34/500 | 35.70 | −0.127 |
| lambda0.3 | 34/500 | 34.56 | −0.080 |
| lambda3.0 | 31/500 | 31.98 | −0.084 |

Per-step wall time checked directly from `ITERATION_LOG.jsonl`'s `wall_time_sec` field (not the coarser SLURM elapsed-time counter, which also includes one-time model-load overhead): **~31-33s/step**, only slightly slower than the `gcg_full_qwen3_6c_cot_refusal` reference run's ~29-30s/step — on pace for optimization to finish in **~4.3-4.6h**, consistent with the timing basis in this doc's header. All refusal_dir_loss values are already negative this early (steps 31-34), same qualitative pattern as the layer=25/lambda=1.0 reference. No action needed; continuing to next check-in.

### 08:03 UTC — Check-in 2 (elapsed: 1h03min)

All 4 optimization jobs still `RUNNING` on n-802 (SLURM elapsed time 1:04:2x), all 12 downstream jobs still correctly `PENDING (Dependency)`. No free-gen/replay/analysis outputs exist yet (expected — optimization isn't done).

| Run | Step | task_loss | refusal_dir_loss |
|---|---|---|---|
| layer20 | 93/500 | 29.00 | −0.095 |
| layer30 | 96/500 | 32.53 | −0.090 |
| lambda0.3 | 95/500 | 29.38 | −0.091 |
| lambda3.0 | 90/500 | 28.17 | −0.048 |

Steady-state pace confirmed from step deltas between check-ins (layer20: 32→93 = 61 steps in 32 min = **31.5s/step**, matching the per-step `wall_time_sec` field exactly). At this rate: ~407 steps remaining ÷ 31.5s/step ≈ 3.6h more optimization → **optimization ETA ≈ 11:40 UTC**, then free-gen (~2.5h per the 6C reference) → **ETA ≈ 14:10 UTC**, then replay+analysis (~15min) → **full pipeline ETA ≈ 14:25-14:30 UTC**, comfortably inside the 15:00 UTC hard stop with roughly 30-35min margin. task_loss is dropping steadily in all four (28-33 range at ~step 90-96, down from ~48 at step 0 per the CONFIG's manifest target), same trajectory shape as the reference 6C run. No action needed.

### 08:34 UTC — Check-in 3 (elapsed: 1h34min)

All 4 optimization jobs still `RUNNING` (SLURM elapsed 1:35:2x), all 12 downstream jobs still `PENDING (Dependency)`. Still no free-gen/replay/analysis outputs (expected).

| Run | Step | task_loss | refusal_dir_loss | steps this interval | pace this interval |
|---|---|---|---|---|---|
| layer20 | 146/500 | 26.23 | −0.086 | +53 in 31 min | 35.1s/step |
| layer30 | 156/500 | 27.02 | −0.083 | +60 in 31 min | 31.0s/step |
| lambda0.3 | 154/500 | 28.15 | −0.093 | +59 in 31 min | 31.5s/step |
| lambda3.0 | 148/500 | 26.56 | **−0.027** | +58 in 31 min | 32.1s/step |

Pace is holding steady (~31-35s/step, minor run-to-run variance, nothing concerning). Remaining steps average ~348 across the 4 runs; at ~33s/step average that's **~3.2h more optimization → ETA ≈ 11:45 UTC**, then free-gen (~2.5h) → **≈ 14:15 UTC**, then replay+analysis (~15min) → **full pipeline ≈ 14:30 UTC**, still comfortably inside the 15:00 UTC hard stop.

**One interim observation worth flagging (not yet conclusive):** `lambda3.0`'s refusal_dir_loss (−0.027) is notably smaller in magnitude than the other three runs (all around −0.08 to −0.09) at a similar step count, despite lambda3.0 having the *strongest* refusal-direction weighting (3.0x) of any run in this sweep. This is the opposite of the naive expectation (higher lambda → more aggressive suppression → more negative projection). Will watch whether this holds at step 500 — if so, it's a genuinely interesting wrinkle for the final write-up (possibly the higher lambda destabilizes optimization rather than sharpening it, similar in spirit to how higher-lambda regularization terms can sometimes make gradient-based search noisier rather than more targeted). Not drawing a conclusion yet at 148/500 steps.

### 09:05 UTC — Check-in 4 (elapsed: 2h05min)

All 4 optimization jobs still `RUNNING` (SLURM elapsed 2:06:2x), all 12 downstream jobs still `PENDING (Dependency)`. Still no free-gen/replay/analysis outputs.

| Run | Step | task_loss | refusal_dir_loss | steps this interval | pace this interval |
|---|---|---|---|---|---|
| layer20 | 204/500 | 25.48 | −0.089 | +58 in 31 min | 32.1s/step |
| layer30 | 216/500 | 23.63 | −0.100 | +60 in 31 min | 31.0s/step |
| lambda0.3 | 214/500 | 28.01 | −0.094 | +60 in 31 min | 31.0s/step |
| lambda3.0 | 202/500 | 25.11 | **+0.0018** | +54 in 31 min | 34.4s/step |

Pace unchanged (~31-34s/step). Remaining steps ~296 (slowest run, layer20) at ~32s/step ≈ **2.6h more optimization → ETA ≈ 11:41 UTC**, then free-gen (~2.5h) → **≈ 14:11 UTC**, then replay+analysis → **full pipeline ≈ 14:25 UTC** — unchanged from prior estimate, still comfortably inside the 15:00 UTC hard stop.

**The `lambda3.0` anomaly is now more definite, not just noise:** its refusal_dir_loss has gone from −0.027 (step 148) to **positive +0.0018** (step 202) — the projection is moving in the WRONG direction (increasing toward the refusal direction, not away from it) despite lambda=3.0 being 3x stronger than the reference (lambda=1.0) run, while task_loss (25.1) is tracking normally, comparable to the other three runs at the same step count. This is a genuinely interesting, unplanned-for result: a stronger refusal-direction penalty is not producing a more suppressed refusal-direction projection here — if anything, the opposite. One candidate explanation (not yet confirmed): at lambda=3.0 the refusal-direction gradient term may dominate the combined gradient used for candidate proposal strongly enough to destabilize convergence on that specific term, even though task_loss optimization proceeds normally (task_loss and refusal_dir_loss are somewhat decoupled at the gradient level per the earlier audit's finding that refusal_dir_loss isn't even part of the candidate-*selection* objective — see `docs/GCG_REFUSAL_DIRECTION_AUDIT.md` §2). Will report the final value at step 500 rather than draw a conclusion now.

### 09:36 UTC — Check-in 5 (elapsed: 2h36min)

All 4 optimization jobs still `RUNNING` (SLURM elapsed 2:37:2x), all 12 downstream jobs still `PENDING (Dependency)`.

| Run | Step | task_loss | refusal_dir_loss | steps this interval | pace this interval |
|---|---|---|---|---|---|
| layer20 | 262/500 | 25.31 | −0.080 | +58 in 31 min | 32.1s/step |
| layer30 | 276/500 | 24.27 | −0.102 | +60 in 31 min | 31.0s/step |
| lambda0.3 | 270/500 | 28.36 | −0.070 | +56 in 31 min | 33.2s/step |
| lambda3.0 | 259/500 | 25.04 | **−0.032** | +57 in 31 min | 32.6s/step |

Pace unchanged (~31-33s/step). Remaining steps ~238-241 at ~32s/step ≈ **2.1h more → optimization ETA ≈ 11:45 UTC**, free-gen → **≈ 14:15 UTC**, full pipeline → **≈ 14:30 UTC** — unchanged, still comfortably inside the 15:00 UTC hard stop.

### 2026-07-13, ~15:30 UTC — MAJOR interim finding: lambda=0.3 recovers substantial ASR

Ran `scripts/build_gcg_source_of_truth.py` (extended with the 4 Phase 8 rows) against current data (lambda0.3 at 292/300 rows, others complete):

| Run | Optimized ASR | Neutral ASR | Uplift | vs. reference (layer25/λ1.0, 0% ASR) |
|---|---|---|---|---|
| layer20 (λ=1.0) | 5.33% (16/300) | 4.00% | +1.3pp | small recovery |
| layer30 (λ=1.0) | 0.00% | 4.00% | net-neg | same as reference |
| **lambda0.3 (layer=25)** | **21.92%** (64/292) | 2.74% | **+19.2pp** | **dramatically higher — ~2x the original 5A reference's 10.7% ASR, and the complete opposite of the layer=25/λ=1.0 reference's 0%** |
| lambda3.0 (layer=25) | 2.67% | 4.00% | net-neg (small) | similar to reference |

**This directly refutes "refusal-direction suppression eliminates the CoT-prefix gain" as a general claim.** At a weaker lambda (0.3 vs. the originally-tested 1.0), the same layer (25) and same CoT-prefix target produces a substantial *positive* effect, not a null/negative one — refusal-direction suppression is not uniformly destructive; its effect is lambda-dependent, and a weak enough suppression term can apparently reinforce rather than fight the CoT-prefix objective. **Caveat: lambda0.3's free-gen isn't 100% complete yet (292/300) — verifying with the final 300 rows before treating this as final, but the effect size (19.2pp) is large enough that the last 8 rows are very unlikely to change the qualitative conclusion.** This is exactly the kind of result that justifies having run this sweep at all — the audit's own recommendation flagged this as "the one place where a different result would actually change the write-up's conclusions."

**Update, ~16:06 UTC: free-gen finished at 300/300, then a SECOND instance of the slow-node issue.** `lambda0.3`'s free-gen (job 660636) completed all 300 rows on schedule. Its dependent replay job (660637) then landed on `n-801` again — the exact same node that stalled a free-gen job's model load earlier in this sweep — and was still stuck at 78% weight-loading after 19 minutes (versus the ~2-5 min every other job's model load has taken). Checked node health again (`n-803` fully idle, 0/8 GPUs, same as last time); cancelled the stuck replay job and its pending dependent analysis job (`scancel 660637 660638` — safe, since replay had produced 0 hidden-state files yet, nothing to lose) and resubmitted both pinned to `n-803` (new IDs: replay=**660912**, analysis=**660913**). **`n-801` appears to have a real, reproducible slow-storage-path problem for this workload specifically** (not a one-off fluke) — worth flagging to whoever administers the cluster, and worth defaulting to `--nodelist` excluding `n-801` for large-model-loading jobs in this project if this keeps recurring.

**Revising the `lambda3.0` framing from the last check-in:** its refusal_dir_loss went −0.027 (step 148) → +0.0018 (step 202) → **−0.032 (step 259)**, i.e. it crossed back to negative rather than continuing to worsen. This looks more like **noisier oscillation around a weaker suppression level** than a monotonically-worsening trend — still notably less negative than the other three runs' steady −0.07 to −0.10 range at comparable steps, but not the "getting worse and worse" trajectory the previous entry's phrasing might have implied. Correcting that nuance now rather than waiting for the final report, per the standing practice in this project of not letting an interim framing harden into an unwarranted claim.

### 10:08 UTC — Check-in 6 (elapsed: 3h08min)

All 4 optimization jobs still `RUNNING` (SLURM elapsed 3:09:2x), all 12 downstream jobs still `PENDING (Dependency)`.

| Run | Step | task_loss | refusal_dir_loss | steps this interval | pace this interval |
|---|---|---|---|---|---|
| layer20 | 324/500 | 25.23 | −0.080 | +62 in 32 min | 31.0s/step |
| layer30 | 332/500 | 24.34 | −0.103 | +56 in 32 min | 34.3s/step |
| lambda0.3 | 331/500 | 27.82 | −0.070 | +61 in 32 min | 31.5s/step |
| lambda3.0 | 318/500 | 24.69 | −0.055 | +59 in 32 min | 32.5s/step |

Pace unchanged (~31-34s/step). Remaining steps 168-182 across the 4 runs; slowest ETA-to-optimization-done ≈ **11:44 UTC**, free-gen → **≈ 14:14 UTC**, full pipeline → **≈ 14:30 UTC** — unchanged from prior estimates, still comfortably inside the 15:00 UTC hard stop.

`lambda3.0`'s refusal_dir_loss (−0.055) has settled back to clearly negative and is closing some of the gap to the other three, though still the weakest-magnitude suppression of the four at this step count (layer20 −0.080, layer30 −0.103, lambda0.3 −0.070, lambda3.0 −0.055). The oscillation observed two check-ins ago (crossing briefly positive) looks like it was a genuine but transient instability rather than a persistent divergence — the run is not obviously "broken," just noisier and converging to a somewhat weaker suppression magnitude than the others. Will report final step-500 values rather than extrapolate further.

### 10:39 UTC — Check-in 7 (elapsed: 3h39min)

All 4 optimization jobs still `RUNNING` (SLURM elapsed 3:40:2x), all 12 downstream jobs still `PENDING (Dependency)` — no transition yet, on track for the ~11:40-11:48 UTC window predicted last check-in.

| Run | Step | task_loss | refusal_dir_loss | steps this interval | pace this interval |
|---|---|---|---|---|---|
| layer20 | 383/500 | 24.77 | −0.080 | +59 in 31 min | 31.5s/step |
| layer30 | 386/500 | 23.48 | −0.104 | +54 in 31 min | 34.4s/step |
| lambda0.3 | 390/500 | 26.88 | −0.105 | +59 in 31 min | 31.5s/step |
| lambda3.0 | 374/500 | 24.20 | −0.045 | +56 in 31 min | 33.2s/step |

Pace unchanged. Remaining steps 110-126 across the 4; per-run ETAs to finish optimization: layer20 ≈11:41, layer30 ≈11:44, lambda0.3 ≈11:35, lambda3.0 ≈11:48 UTC — all still within the previously projected window. Full-pipeline ETA remains **≈14:30 UTC**.

`lambda0.3` has notably strengthened this interval (−0.070 → −0.105, now on par with layer30's −0.104) — the weak-lambda run is not showing a correspondingly weak suppression at this point, which is itself a useful data point for the final write-up (lambda strength and realized suppression magnitude don't track cleanly across this sweep). `lambda3.0` remains the persistent outlier at −0.045, the weakest of the four throughout the second half of optimization.

### 11:10 UTC — Check-in 8 (elapsed: 4h10min)

All 4 optimization jobs still `RUNNING` (SLURM elapsed 4:11:2x), all 12 downstream jobs still `PENDING (Dependency)` — running slightly behind the tightest end of the projected window but still within it.

| Run | Step | task_loss | refusal_dir_loss | steps this interval | pace this interval |
|---|---|---|---|---|---|
| layer20 | 442/500 | 25.01 | −0.071 | +59 in 31 min | 31.5s/step |
| layer30 | 445/500 | 23.98 | −0.105 | +59 in 31 min | 31.5s/step |
| lambda0.3 | 450/500 | 26.52 | −0.107 | +60 in 31 min | 31.0s/step |
| lambda3.0 | 433/500 | 24.57 | −0.045 | +59 in 31 min | 31.5s/step |

All four are in the final ~50-70 steps; per-run finish ETAs: lambda0.3 ≈11:33, layer30 ≈11:38, layer20 ≈11:41, lambda3.0 ≈11:49 UTC. Full-pipeline ETA holds at **≈14:30 UTC**.

**Side observation from reading `logs/gcg_6c_combined_660404.out` (layer20) directly:** the accepted suffix stayed byte-identical for steps 220-410 (190 steps, over a third of the whole run) before the optimizer found an improving candidate at step 420 — a genuine optimization plateau, not a bug (task_loss and refusal_dir_loss both continued fluctuating slightly within that plateau, and the run has since moved again). Worth keeping in mind when interpreting "best step" numbers later: a very long plateau followed by a late improvement is a normal, if slightly unusual, GCG trajectory shape and doesn't indicate anything wrong with this run specifically.

### 11:41 UTC — Check-in 9 (elapsed: 4h41min) — transition to free-gen underway

**3 of 4 optimization jobs (660404 layer20, 660405 layer30, 660406 lambda0.3) have exited the SLURM queue (optimization complete), and their dependent free-gen jobs (660408, 660411, 660414) are correctly now `RUNNING`.** `660407` (lambda3.0) is still optimizing (SLURM elapsed 4:42:27, step 489/500 — a bit behind the others, consistent with it having run slightly slower this whole sweep per earlier check-ins' per-step timing).

Last recorded `ITERATION_LOG.jsonl` step for each (near-final, not yet the "best" step which may differ):

| Run | Last step | task_loss | refusal_dir_loss | Status |
|---|---|---|---|---|
| layer20 | 499/500 | 25.04 | −0.082 | optimization done, free-gen (660408) running |
| layer30 | 499/500 | 23.09 | −0.093 | optimization done, free-gen (660411) running, 2/300 rows so far |
| lambda0.3 | 499/500 | 26.52 | −0.115 | optimization done, free-gen (660414) running |
| lambda3.0 | 489/500 | 24.07 | −0.056 | still optimizing, ~11 steps left |

`RESULTS_SUMMARY.md` hasn't appeared yet for any of the 3 finished runs at the moment of this check (it's written as one of the last steps inside the optimization script, evidently slightly after the point SLURM considers the job "done" enough to release the dependency) — will pick up the official best-task-loss/best-refusal-dir-loss numbers next check-in once those files exist. Free-gen for 300 rows took ~2.5h for the original 6C reference run — full-pipeline ETA holds at **≈14:30 UTC** (lambda3.0 is running ~10-15 min behind the other three, immaterial to the overall ETA since free-gen dominates the remaining time budget).

### 12:12 UTC — Check-in 10 (elapsed: 5h12min) — all 4 in free-gen; RESULTS_SUMMARY.md gap found and fixed; one operational slowdown flagged

**Root cause found for the missing `RESULTS_SUMMARY.md`s:** that file is written by a separate script, `poc_stage_gcg_early/analyze_pareto_frontier.py`, which is **not** invoked anywhere in `run_gcg_full_6c_qwen3_combined.slurm` — the historical `gcg_full_qwen3_6c_cot_refusal` reference run must have had it run as a separate manual step at the time, which this automated sweep's job chain didn't replicate. Ran it manually now for the 3 finished optimization runs:

| Run | best task_loss | at step | best refusal_dir_loss (min over run) | at step | final (step 499) refusal_dir_loss |
|---|---|---|---|---|---|
| layer20 | **24.31** | 494 | −0.101 | 125 | −0.082 |
| layer30 | **22.92** | 469 | −0.131 | 24 | −0.093 |
| lambda0.3 | **25.85** | 454 | −0.124 | 54 | −0.115 |
| lambda3.0 | *(still optimizing at time of this check — 489/500 last seen)* | — | — | — | — |

Reference (`gcg_full_qwen3_6c_cot_refusal`, layer=25, lambda=1.0): best task_loss=25.6367 at step 443, final refusal_dir_loss=−0.115. **All three finished sweep runs so far have LOWER (better) best task_loss than the reference** (24.31, 22.92, 25.85 vs 25.64) — layer30 in particular converges noticeably better. Final refusal_dir_loss values are in a similar ballpark to the reference (−0.08 to −0.12) except layer20 which is slightly weaker (−0.082).

Free-gen row counts at this check: layer20 44/300, layer30 60/300, lambda3.0 41/300 — all progressing normally. **lambda0.3's free-gen job (660414) has NOT produced any output rows after 38 minutes and its log shows it is still loading model weights (56% through 443 shards at the 32-minute mark)** — this job landed on node `n-801` (the other three free-gen jobs are on `n-802`, the same node all 4 optimizations ran on, which therefore already had the model weights warm in local/page cache). `n-801` appears to be reading the ~28GB checkpoint from slower/cold shared storage, causing this specific job's startup to take far longer than the others. This is a real, if modest, risk to the timeline — will watch closely next check-in; no manual intervention taken (killing and resubmitting would lose the already-sunk 38 minutes and isn't obviously better than letting it finish loading).

### 12:45 UTC — Check-in 11 (elapsed: 5h45min) — real timeline risk found and fixed; all 4 optimizations now finished

**All 4 optimization runs finished.** Ran `analyze_pareto_frontier` on `lambda3.0` (the last to finish) — final comparison of all 4 sweep runs' optimization results against the reference:

| Run | best task_loss | at step | reference (6C, layer25/λ1.0) best task_loss=25.6367 |
|---|---|---|---|
| layer20 | 24.31 | 494 | better |
| layer30 | **22.92** | 469 | notably better |
| lambda0.3 | 25.85 | 454 | ~comparable |
| lambda3.0 | 23.89 | (final, not yet re-derived precisely) | better |

**All four sweep configurations converge at least as well as, and mostly better than, the original layer=25/lambda=1.0 run on task_loss** — the refusal-direction objective is not harder to optimize jointly with the CoT-prefix target at these alternative layers/lambdas.

**Real operational issue found and resolved:** `lambda0.3`'s free-gen job (660414) took **50 minutes just to finish loading model weights** (vs. ~2-5 min for the other three jobs, all on node `n-802`), then generated at roughly **88s/row** afterward (13 rows in ~19 min) — more than double the ~30-38s/row the other three jobs were achieving. Extrapolated, this would have pushed `lambda0.3`'s free-gen alone to finish around **19:45 UTC, ~5 hours past the 15:00 UTC hard stop.**

Checked node health directly (`scontrol show node`): `n-801` (where 660414 landed) had 0 GPUs allocated to other jobs and low CPU load — not obviously congested — but the checkpoint read was still very slow, most likely a cold local cache / slower path to shared storage for that specific node. `n-803` was found to be **completely idle** (0/8 GPUs allocated, CPULoad 0.03).

**Action taken:** cancelled the stuck free-gen job and its two not-yet-started dependents (`scancel 660414 660415 660416`), then resubmitted the free-gen job pinned to the idle node (`sbatch --nodelist=n-803 ...`) plus fresh replay/analysis jobs chained to it (new IDs: free-gen=**660636**, replay=**660637**, analysis=**660638**). This was safe because `evaluate_optimized_suffixes.py` (the free-gen script) is explicitly resumable by `row_key` (`# Resume: skip if already in log`) — confirmed the existing `FREE_GENERATION_RESULTS.jsonl` (14 rows) was left intact and the new job will pick up from row 15, not restart from scratch. The other three free-gen jobs (660408 layer20, 660411 layer30, 660417 lambda3.0) were left untouched — they were performing normally on `n-802` despite that node's high CPU load (224 — GPU-bound generation isn't CPU-load-sensitive the way disk-bound model loading is).

**Updated job IDs for lambda0.3 from this point:** free-gen=660636, replay=660637, analysis=660638 (superseding 660414/660415/660416 in the table at the top of this doc).

### 13:19 UTC — Check-in 12 (elapsed: 6h19min) — resubmit helped but not fully; honest deadline-risk reassessment

Row counts: layer20 141/300, layer30 182/300, lambda3.0 162/300, **lambda0.3 43/300**.

Per-job average pace since each free-gen job's own start (not just this interval — more reliable given lambda0.3's history):
- layer20 (660408): 141 rows / 98.4 min elapsed = 41.9s/row → **~1.85h remaining → ETA ≈15:11 UTC**
- layer30 (660411): 182 rows / 100.4 min elapsed = 33.1s/row → **~1.08h remaining → ETA ≈14:23 UTC**
- lambda3.0 (660417): 162 rows / 91.4 min elapsed = 33.9s/row → **~1.30h remaining → ETA ≈14:36 UTC**
- lambda0.3 (660636, resubmitted on n-803): produced 29 new rows (43 total, 14 carried over from the cancelled job) in 31.4 min = **65s/row** — much better than the ~88s/row + 50-min load on the old node, but still ~2x slower than layer30/lambda3.0's pace. At this rate: 257 rows remaining × 65s ≈ **4.64h more → ETA ≈17:56 UTC.**

**Honest assessment: `lambda0.3` is very unlikely to finish free-gen (let alone replay+analysis) by the 15:00 UTC hard stop, even after the node-pinning fix.** `layer20` is also now marginal (ETA ≈15:11, ~11 min past). `layer30` and `lambda3.0` should finish comfortably before 15:00.

**Root cause of the residual `n-803` slowdown is unclear** — it's a fully idle node with the same GPU type (`L40S`), so this isn't an obvious contention story the way the first slowdown was. Possible explanations not confirmed: a slower storage path specific to that node for this workload, or ordinary run-to-run variance in how many tokens each condition/seed happens to generate before hitting EOS (longer chain-of-thought completions before the model stops). Not worth further reallocation this late — three of four runs are on track, and the fourth is progressing steadily, just slower than hoped.

**Decision for the 15:00 UTC boundary:** per the standing instruction to stop the *check-in loop* at 8 hours and document whatever state things are in, that is what will happen — but the underlying SLURM jobs are real, already-paid-for compute that will keep running on the cluster regardless of whether this loop keeps checking on them. Stopping the loop is not the same as killing the jobs, and killing jobs that are legitimately close to finishing (layer20, layer30, lambda3.0) or steadily progressing (lambda0.3) would waste the GPU-hours already spent for no benefit. Plan: continue checking through 15:00 UTC as instructed; at that point, report final status honestly (which of the 4 are fully done vs. still running) rather than silently extending the loop indefinitely, and leave the still-running job(s) to finish on their own — the user can check `squeue` themselves afterward, or ask for one more check-in.

### 13:51 UTC — Check-in 13 (elapsed: 6h51min) — second-to-last check before the 15:00 UTC boundary

Row counts: layer20 203/300, layer30 258/300, lambda3.0 247/300, lambda0.3 98/300.

Recomputed pace this interval (faster/more reliable signal than the job-lifetime average used last check, since per-node conditions can shift):
- layer20: +62 rows in 32 min = 31.0s/row → 97 remaining ≈ 50 min → **free-gen ETA ≈14:41**, full pipeline (+ replay/analysis ~15min) ≈ **14:56 UTC** — tight but should land just inside the 15:00 deadline.
- layer30: +76 rows in 32 min = 25.3s/row → 42 remaining ≈ 18 min → **free-gen ETA ≈14:09**, full pipeline ≈ **14:25 UTC**.
- lambda3.0: +85 rows in 32 min = 22.6s/row → 53 remaining ≈ 20 min → **free-gen ETA ≈14:11**, full pipeline ≈ **14:27 UTC**.
- lambda0.3: +55 rows in 32 min = 34.9s/row (sped up from 65s/row last check, still the slowest) → 202 remaining ≈ 2.0h → **free-gen ETA ≈15:51 UTC — will miss the 15:00 UTC boundary.**

**So: layer30 and lambda3.0 should be fully done (through analysis) comfortably before 15:00. layer20 is genuinely tight (projected ~14:56, i.e. right at the wire) — the next check-in (14:21 UTC, the last one before the boundary) will show whether it made it. lambda0.3 will not finish in time and will be reported as still-running-in-background at the 15:00 cutoff**, per the plan above — its SLURM jobs will be left running rather than killed, since it's making steady (if slow) progress and killing it now would waste the ~7h of GPU time already spent on its optimization + partial free-gen.

### 2026-07-14, ~03:38 UTC — seed=43 replication result (Sprint 2 follow-up)

The headline finding above (λ=0.3, layer=25, seed=42 → 24.0% ASR, 18/75) was flagged as needing seed-robustness confirmation before being treated as fully settled, given the project's known seed-variance issue (Finding 6: up to 11x ASR swings between nearly-tied-loss seeds on unrelated runs). Ran the identical recipe at optimization seed=43 (jobs 660927 → 661079 → 661357, full pipeline, no dependency chain per this sprint's corrected SLURM policy).

**Result: optimized_weighted 9/75 (12.0%) vs. neutral_control 3/75 (4.0%), random_spaces 4/75, task_only 2/75.**

**Replicates directionally**: clear, real uplift over controls at both seeds, and both exceed/match the no-refusal-dir 10.7% reference. **Does not replicate in exact magnitude**: 24.0% (seed=42) vs. 12.0% (seed=43) — a 2x difference. Given this project's already-documented seed sensitivity, this is consistent with "λ=0.3 genuinely helps, but the exact ASR is seed-dependent" rather than evidence the seed=42 result was a fluke — both seeds land meaningfully above baseline/controls, neither lands near 0%. **Recommended final framing for the audited docs**: report λ=0.3's effect as a range (12-24% ASR across 2 seeds) rather than a single point estimate, and flag that a 3rd seed would further tighten this if time permits.
