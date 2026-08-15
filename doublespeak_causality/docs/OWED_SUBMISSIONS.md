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

---

# 2026-08-14 15:30 — FULL AUDIT of every entry above, checked against filesystem + squeue

Stale tracking is how a half-launched set gets forgotten, so each claim above was re-verified
rather than assumed.

## CLEARED (verified, no action)
| entry | check | result |
|---|---|---|
| 04:xx §20.1 missing control | `sacct 757513/514/515` | all **COMPLETED** |
| 05:40 §20.1 CE term unrecorded | `asym_p201_ce_scores.json` | **exists**, 6 arms |
| 07:30 §20.1 behavioural endpoint | `asym_p201_softprompt_asr.json` | **exists**, 222 rows judged |
| 08:55 §20.7 "will hit the 16 h wall" | measured 73 min/prompt end-to-end | **moot** — ~12.2 h/shard, fits. No resubmission expected; the completion check below still applies |

## OUTSTANDING
1. **§20.1 μ sweep** (μ ∈ {0.1, 0.3, 1, 3, 10}) — **not run** (0 matching output dirs). Needed
   before §20.1's "78 % cost" goes in the paper: 78 % is the price of a *near-total* pin
   (Δproj ≈ −0.03), not of the coordinate as such. GPU; queue is full.
2. ~~**§20.7 seed 43 shards 2–3 of 4** — not submitted.~~ **RESOLVED 2026-08-14 17:00:** shard 2 =
   **757662** (n-305), shard 3 = **757672** (n-350). Seed 43 now has all 4 shards launched, so its
   denominator is the full **37**. Shard 1 (757526) finished clean: `ran=9 skipped=0`.
3. **§20.7 seed 44** — **entirely unlaunched** (0 output dirs).
4. **§20.7 2000-step point** — deferred by decision. The estimate for 200→600 oscillated
   (−0.079 → −0.122 → −0.062 as n grew); decide at 37/37, not before.
5. **§20.4 pass 2** — blocked. The plan requires a §20.6 multi-direction SD; §20.6 is blocked by
   the corpus ceiling (179). **Pass 2 is unreachable as specified** — the plan's "publish only the
   second" instruction cannot be followed, and pass 1 must be published with its limitation stated.
6. **§20.5 / §20.6 / §20.9** — not started.

## Launch order when slots free (in priority order)
1. §20.7 seed 43 shards 2,3 (`SEED=43 N_STEPS=600 SHARD=2|3 NSHARD=4`) — completes an existing
   half-launched set; a partial seed cannot be a curve point.
2. §20.7 seed 44 shards 0–3 — third seed for the curve.
3. §20.1 μ sweep — new evidence rather than more coverage of the same point.

## 2026-08-14 18:15 — §20.7 seed 44 is now a HALF-LAUNCHED set (shard 0 only)
**757697** = `ARM=vanilla SEED=44 N_STEPS=600 SHARD=0 NSHARD=4` on n-302. **Shards 1, 2, 3 are NOT
submitted** — only one slot was free.

Launched incrementally rather than waiting for four slots, because seed 42's remaining shards are
each one prompt from done and idling a GPU costs more than the tracking does. **But the seed-43
lesson applies verbatim: shard = index mod 4, so a partially-launched seed is a BIASED subset, not a
smaller random sample. Seed 44 must not be used as a curve point until all 4 shards are submitted
and complete.**

Submit shards 1–3 as slots free, before the §20.1 μ sweep.

## 2026-08-14 18:45 — seed 44 shards 1–2 launched; shard 3 still owed. §20.7 seed 42 CLOSED.

**Resolved this tick**
* ~~§20.7 seed 42~~ — **COMPLETE 37/37** (757516 was the last shard). Final read taken once, at
  full coverage: 200→600 mean Δ = −0.0723, 22/37, **p = 0.252** (null).
  `asym_p207_objective_curve_seed42_FINAL37.json`, `interim: false`.
* §20.7 seed 44 **shard 1/4 = 757709** (n-303), **shard 2/4 = 757711** (n-301).

**Still owed, in launch order as slots free**
1. **§20.7 seed 44 shard 3/4** — completes the set. Seed 44 remains a **half-launched** set until
   it is in, and (shard = index mod 4) must not be a curve point before then.
2. **§20.1 μ sweep** (μ ∈ {0.1, 0.3, 1, 3, 10}) — still **0 output dirs**. Needed before §20.1's
   "78 % cost" can go in the paper: 78 % is the price of a *near-total* pin (Δproj ≈ −0.03).
3. **§20.5 best-of-k pool attack** — not started; no new optimization, but 4–8 GPU-h of generation.
   Mandatory conditions from the plan: majority-vote judging *before* the max, a `randtok` pool as
   the noise-inflated floor, diagonal pairs dropped.
4. **§20.7 2000-step point** — **descope is the standing recommendation** on seed 42's null, but the
   final call waits on seed 43 reaching 37/37, whose interim slice disagrees (p = 0.026 at 20/37).
   Do not score seed 43 before full coverage: completion order tracks optimization cost, so the
   partial set is biased in the endpoint being measured.
5. **§20.6 / §20.9** — blocked by the corpus ceiling (179) via §20.8. Do not launch §20.6 first.

**Standing submission rule (reaffirmed the hard way):** every §7.5/§20.7 job takes an explicit
3090-only `--nodelist`. 757702 was submitted without one, landed on an 8× V100 DGX node, and died
at 14 s only because the GPU probe crashed — *not* because the guard rejected it. The guard could
not have reported anything: its error branch was unreachable under `set -e` until fixed this tick.

## 2026-08-14 19:45 — §20.7 fully launched; §20.5 reclassified

**Resolved**
* ~~§20.7 seed 44 shard 3/4~~ — **757741** on n-304. All four shards of every seed are now
  submitted; **no half-launched set remains** and the index-mod-4 bias caveat is cleared.
* ~~§20.5 "not started, 4-8 GPU-h"~~ — **the classification was wrong.** §7.5's transfer runs left
  a 37x37 grid on disk (1332 rows, 6 cells); a provisional pool result is delivered with **zero
  GPU** in `asym_p205_bestofk_existing.json`.

**Still owed, in launch order as slots free**
1. **§20.1 μ sweep** (μ ∈ {0.1, 0.3, 1, 3, 10}) — still **0 output dirs**, now the top GPU item and
   the next thing to launch. Needed before §20.1's "78 % cost" can go in the paper.
2. **§20.5 follow-ups** — three separable items, not one job:
   a. **`randtok` floor pool** (GPU generation) — *mandatory*; without it the +0.08 at k=2 cannot
      be separated from two draws of judge noise.
   b. **M=5 re-judging** of the transfer grid (**API spend, not GPU**) — *mandatory*; single-pass
      judging biases every k>1 number upward.
   c. **A redesigned dense grid** if large-k is wanted — balanced k caps at **2** on the existing
      one, and going higher keeps only big-pool targets. Re-estimate the cost from this design,
      not from the stale 4-8 GPU-h figure. Note the **vanilla arm has no transfer rows at all**.
3. **§20.7 2000-step point** — descope still recommended on seed 42's null; the call waits on
   seed 43 reaching 37/37 (24/37 now). Do not score seed 43 before full coverage.
4. **§20.6 / §20.9** — blocked by the corpus ceiling (179) via §20.8.

---

# 2026-08-15 — CLOSING STATE. Three of the four items above are DONE; this ledger was stale.

**Read this section before acting on anything above it.** The 19:45 entry listed the μ sweep and
the randtok floor as owed. Both have since been executed. Acting on that list now would **relaunch
~30 completed jobs**, which is precisely the failure this ledger exists to prevent.

## RESOLVED since 19:45
| item | resolution |
|---|---|
| §20.1 μ sweep ("0 output dirs, top GPU item") | **COMPLETE.** μ ∈ {0.1, 0.3, 1.0, 3.0, 10.0} × seeds {42, 43, 44} = 15 runs + 3 free arms, all CE-scored in one model load. `asym_p201_ce_musweep.json`, propagated to `SECTION20_RESULTS.md` §1b |
| §20.5a randtok floor (*mandatory*) | **COMPLETE.** K=10 × 37 prompts = 370 evals. Floor ASR@1 = **0.2351**. `asym_p205_bestofk_existing.json` is now `provisional: false` |
| §20.5b M=5 re-judging (*mandatory*) | **ALREADY MET FROM DISK** — §20.3's replicate pool (`pool_total = 1998`) contains the transfer grid; 66 of its 93 band rows are `xfer_*`. **No API spend was needed**, contrary to the 19:45 entry |
| §20.7 2000-step point | **DESCOPED** by the pre-registered decision rule, 1 of 3 criteria met (pooled p = 0.0023 PASS; 1/3 seeds significant FAIL; efficiency 14.9× worse FAIL). `asym_p207_curve_200to600_3seed.json` |

## STILL OWED — none of it is a job you can submit
1. **§20.0 governance** — the dev-split allocation decision named as a *precondition* in the plan
   was **never written**. Dev (37 items) is **verified unspent**: every §20 job ran `split=test`
   on the 37-item test set with the 40-item train pool. It remains a clean one-shot out-of-sample
   surface, and the decision is still owed **before** anything is run against it.
2. **§20.6 / §20.9** — behind §20.8, whose n=300 is unreachable (corpus ceiling **179**, ≈139
   usable). The 08:00 entry records three options and recommends **Option 3** (continuous
   endpoints, adequately powered at n=37 where binary ASR is not). **A plan decision, not compute.**
3. **§20.5c dense grid** — only if large-k is wanted. Balanced k caps at **2** on the existing
   sharded grid; going higher keeps only large-pool targets. Cost must be re-estimated from a
   *designed* grid, not from the stale "4–8 GPU-h". The **vanilla arm has no transfer rows at all**.
4. **§20 integration into `ASYMMETRY_FINAL_SYNTHESIS.md`** beyond the two annotations of 2026-08-15
   (one superseded claim, one refinement). Editorial. **Do not** touch `ASYMMETRY_GAP_MATRIX.md` —
   it is a dated pre-GPU snapshot and retrofitting results into it would corrupt the deliverable.
5. **Registry scope** — `EXPERIMENT_REGISTRY.csv` indexes only `doublespeak_causality/outputs/`, so
   §20.7's **111 per-prompt runs (~900 GPU-h)** and the floor have no rows. Fixing needs the
   hardcoded `output_dir` prefix in `scripts/update_registry.py` derived rather than assumed.

**Queue state at close: empty.** Every registered §20 computation is done, and every number in
`SECTION20_RESULTS.md` is traced to an artifact and verified against it.

## 2026-08-15 — item 6: reconcile the asymmetry framing with D3

The Phase 6 scope-matched control (`d3_actscope_*_L18_test_*`, 3 arms, full n) shows the published
activation ablation is **positional-scope dependent**: +0.571/+0.810 at all-layers, +0.429/+0.452 at
one layer, **+0.000/+0.024** at one layer and one position — the scope a token attack reaches.

Both `SECTION20_RESULTS.md` and `ASYMMETRY_FINAL_SYNTHESIS.md` now carry an **annotation** at the
point where the framing is stated. Neither has been rewritten. **Owed:** reconcile §20's
contribution list and the synthesis's §0 puzzle with a scope account that covers much of the gap —
substantive editorial work on a headline claim, and a decision about how much of the
representation-vs-behaviour framing survives.

**Do not treat the token-space negatives as affected**: §7.5, §20.5 and §20.7 are measurements and
stand. **Do note the endpoint caveat**: D3 is measured on direction-validation (probe refusal
rates), not doublespeak ASR.
