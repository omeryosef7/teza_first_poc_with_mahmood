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

## 2026-08-14 07:30 — §20.1 owes two follow-ups before it can be written up
§20.1's CE verdict (pinning costs 78 % of objective progress) is **objective-space only**.
1. **Behavioural endpoint for the 6 soft-prompt arms.** Each arm wrote `GENERATIONS.jsonl` but
   none has been judged. If `task_orth` reaches far worse CE yet comparable ASR, that is another
   representation≠behaviour dissociation and materially weakens the §20.1 entry. This is cheap
   (judging only, no GPU optimization) and is the single highest-value unrun item in §20.
2. **μ sweep** (μ ∈ {0.1, 0.3, 1, 3, 10}) to map the CE-vs-Δproj frontier. 78 % is the cost of a
   *near-total* pin (Δproj ≈ −0.03), not of the coordinate as such.

Neither is launched. **§20.1 must not be written into the paper claim table until (1) is scored** —
a CE-only claim would be exactly the objective-vs-behaviour conflation this program exists to
document.

## 2026-08-14 08:10 — §20.7 seed 43 is a HALF-LAUNCHED shard set
757525 (SHARD=0/4, n-306) and 757526 (SHARD=1/4, n-350) are running. **Shards 2 and 3 of 4 are NOT
submitted** — only 2 slots were free. Until they run, seed 43 covers 19 of 37 prompts.

**Do not aggregate seed 43 as a curve point before shards 2 and 3 complete** — a half-covered seed
is a biased subset of prompts (shard = index mod 4), not a smaller random sample.
Seed 44 at 600 steps is still entirely unlaunched.

## 2026-08-14 08:55 — §20.7 shards will hit the 16 h wall; resubmission required (not lost work)
**CORRECTED 09:45.** The 10.2 s/step figure was measured over a window that included the ~6 min
model load, so it over-stated per-prompt cost. End-to-end measurement from shard 0's own RUN
timestamps (23:07:00 -> 00:20:08) is **73 min/prompt**. A 10-prompt shard therefore needs
**≈12.2 h**, which **fits inside the 16 h wall**.

So: my first estimate (47 min/prompt) was optimistic, my second (102 min/prompt, "will hit the
wall") was pessimistic, and the measured value is 73 min/prompt. **No resubmission is expected to
be necessary** — but the verification step below stays mandatory, because "expected to fit" is not
"verified complete".

The runner skips any prompt whose `FINAL_CANDIDATES.jsonl` exists, so this costs a resubmission,
not the work — only the prompt in flight at the wall is redone.

**OWED after 757516–519 / 757525–526 end (TIMEOUT or COMPLETED):**
1. Re-submit each shard with the **same** ARM/SEED/N_STEPS/SHARD/NSHARD to finish stragglers.
2. Verify per-shard completion by counting `FINAL_CANDIDATES.jsonl` — **not** by SLURM state,
   since TIMEOUT is expected here and is not failure. Exact command (outputs live under
   `outputs/stage_gcg_perprompt/`, NOT under `perprompt_test/`):
   ```
   find outputs/stage_gcg_perprompt -maxdepth 2 -name FINAL_CANDIDATES.jsonl -path '*s600*' | wc -l
   ```
   Target is **37 per seed**. Joblists verified: seed42/seed43 each have 37 rows, 37 unique
   task_ids, 37 unique output_dirs (no collision that would silently overwrite).
3. Only then aggregate the 600-step curve point.
