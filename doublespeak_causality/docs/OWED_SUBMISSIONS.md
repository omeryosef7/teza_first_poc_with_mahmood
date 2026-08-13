# OWED SUBMISSIONS — outstanding half-launched shard sets

*Live checklist. A shard set launched partially produces valid-looking output for the shards that
DID run (`ran=N skipped=0`, exit 0), so nothing errors and no tool flags it. This file is the
counter-measure; the per-tick inventory diff is the backstop.*

| owed | reason | status |
|---|---|---|
| **seed 44 transfer matrix — MATCHED-RANDOM control** | mechanism transfer launched 2026-08-14 18:00 while seed 44's random *arm* was still at 36/37, so its control could not be built yet | **OUTSTANDING — build + launch as soon as `asym_p75_matched_random_pp_*_seed44` reaches 37/37. DO NOT analyze the mechanism transfer until this exists.** |

## Cleared
* seed 43 full-budget matched_random shard 1/2 — owed 2026-08-13 16:55, launched same tick.
* seed 42 full-budget vanilla shard 1/2 — owed 2026-08-13 20:40, launched 21:40 as 756228.
* **seed 44 full-budget vanilla shard 1/2** — owed 2026-08-14 10:45 (only one slot free, next not
  expected for ~3 h), **launched 2026-08-14 13:00 as 757157** on the first slot that freed,
  pinned `n-304,n-303,n-305,n-306,n-350` as recorded. Owed for 2 h 15 min across 5 ticks; carried
  correctly by the checklist at every one.
