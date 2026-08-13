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
