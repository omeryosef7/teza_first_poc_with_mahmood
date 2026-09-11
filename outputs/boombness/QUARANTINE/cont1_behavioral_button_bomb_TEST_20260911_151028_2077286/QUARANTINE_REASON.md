# QUARANTINED -- partial run, never completed. NOT deleted (mandate section 53).

SLURM job 878972, cancelled by me at 54 minutes on 2026-09-11. It was allocated n-307, where the
shared HF cache read at a pathological rate: 21 minutes for the FIRST of 291 weight shards, 46
minutes to reach 41. Extrapolated it would have consumed its 6h limit inside the model load and
produced nothing. See CONT-ENTRY 064.

State on disk: cache/, config.json, RUNMETA.json. NO metadata.json, NO results.jsonl, NO DONE.json
-- it never reached the extraction stage, so it holds no measurements of any kind.

SUPERSEDED BY: outputs/boombness/extract_boombness/cont1_behavioral_button_bomb_TEST_20260911_160414_251697
(job 879904, COMPLETED 00:08:53, rc 0, failures {}, bank dcd92d723f3e6d00, 19 layers, DONE.json present),
which ran the byte-identical command on n-804 after --exclude=n-801,n-307 was added.

NOTE ON DISCIPLINE: neither directory has been read for any measurement. The corpus that supersedes
this one holds the TEST split for preregistration DR-072, and DR-072 is HELD (CONT-ENTRY 065/066) --
its single confirmatory read is unspent.
