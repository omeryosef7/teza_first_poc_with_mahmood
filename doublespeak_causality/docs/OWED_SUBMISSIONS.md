# OWED SUBMISSIONS — outstanding half-launched shard sets

*Live checklist. A shard set launched partially produces valid-looking output for the shards that
DID run (`ran=N skipped=0`, exit 0), so nothing errors and no tool flags it. This file is the
counter-measure; the per-tick inventory diff is the backstop.*

| owed | reason | status |
|---|---|---|
| *(none)* | | |

## Cleared
* seed 43 full-budget matched_random shard 1/2 — owed 2026-08-13 16:55, launched same tick.
* seed 42 full-budget vanilla shard 1/2 — owed 2026-08-13 20:40, launched 21:40 as 756228.
* **seed 44 transfer matrix, matched-random control** — owed 2026-08-14 18:00 with an explicit
  analysis embargo on the mechanism arm; **built and launched 18:20 as 757305** the moment the
  random arm reached 37/37. Embargo held: the mechanism transfer (757255) was never analyzed
  alone.
* **seed 44 full-budget vanilla shard 1/2** — owed 2026-08-14 10:45 (only one slot free, next not
  expected for ~3 h), **launched 2026-08-14 13:00 as 757157** on the first slot that freed,
  pinned `n-304,n-303,n-305,n-306,n-350` as recorded. Owed for 2 h 15 min across 5 ticks; carried
  correctly by the checklist at every one.

## 2026-08-14 — §20.1 was launched WITHOUT its control (caught by design-vs-inventory diff)

757508/509/510 are **all three `task_orth`** (seeds 42/43/44, free, b0.1, L40S). §20.1 asks
whether task success survives pinning the refusal projection — that is a *contrast*, and the
unconstrained `task` arm is the other half of it. **No plain `task` arm existed at any budget.**
As launched, §20.1 could only have reported "task_orth reached loss X", which answers nothing.

Fix: submitted **757513/514/515** = `ASYM_OBJ=task`, free, b0.1, seeds 42/43/44, `ASYM_GPU=l40s`
(matching the task_orth arms' GPU class per §3.1), n-802/803/804 one seed per node.

**Embargo: do not analyze or write up §20.1 until 757513/514/515 are all COMPLETED.**
A `task_orth` number on its own is not a §20.1 result.

## 2026-08-14 05:40 — §20.1 second blocker: no arm records CE on its own

`task_orth` optimizes `ce + mu*pen` and the run logs **only that sum**; nothing anywhere
records CE separately. Comparing the two arms' logged `loss` would compare CE against
CE+penalty — not a comparison of anything. §20.1's question is about achieved *task*
performance, so the CE term has to be recovered.

Fix (no rerun needed): `scripts/asym_p201_score_ce.py` + `slurm/run_asym_p201_ce.sh` re-score
the **frozen** `soft_suffix.pt` of each arm through the optimizer's own
`build_prompts`/`forward_batch`, so the CE reported is definitionally what `task` minimized.
Preferred over mid-run logging on two counts: the training print is a per-batch training-pool
number on a non-monotonic series, and this works on already-finished arms.

**Owed submission — all 6 arms in ONE job** (shared model load, no load-order confound; the
script asserts the arms share model/manifest/layer):
`task_orth` 757508/509/510 (s42/43/44) + `task` 757513/514/515 (s42/43/44).

**Embargo stands: no §20.1 analysis until that scoring job has run.** A `Dproj` without a
matched CE cannot distinguish "the penalty worked" from "the penalty destroyed the attack".

## 2026-08-14 06:30 — §20.7 compute-scaling curve, seed 42 launched; seeds 43/44 OWED
757516/517/518/519 = `ARM=vanilla SEED=42 N_STEPS=600 SHARD=0..3/4` on n-301/302/303/305
(3090, matching the GPU class of the existing 5- and 200-step points per §3.1). Shards verified to
partition all 37 prompts exactly once. Runner tags non-200 budgets `_s600`, so no collision.

Cost basis: the 200-step arm ran 19 prompts in 4:58 on a 3090 (~4.7 s/step), so 600 steps ≈ 47
min/prompt ≈ **29 GPU-h per seed**; ~7.5 h wall per shard, inside the 16 h limit.

**OWED:**
* seeds **43 and 44** at 600 steps — until then the 600 point on the ASR-vs-log(steps) curve has
  **n=1 seed** while the 5- and 200-step points have 3. Do not plot them on one axis as if matched.
* the **2000-step** point (~97 GPU-h/seed) is NOT launched — scope it explicitly before committing;
  it may need a prompt subset rather than all 37.
* aggregation for the curve (reuse `aggregate_perprompt_asr.py --mode perprompt`).
