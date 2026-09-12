# PRODUCED NOTHING. Kept with provenance (mandate section 53).

SLURM job 876983, generated on an RTX A5000 at n-503 -- the same hardware as the `ko` arm, which is
why CONT-ENTRY 113 proposed judging it. It cannot be judged: the directory holds `config.json`,
`RUNMETA.json` and an empty `plots/` and **nothing else** -- no `results.jsonl`, no `gens.jsonl`, no
`summary.json`, no `DONE.json`. `expect_n` is 670 and zero rows were persisted.

CONSEQUENCE, recorded because it corrects a proposal in the record: CONT-ENTRY 113 stated that
judging this arm "gives a hardware-matched ko-ctrl comparison for the cost of a judge run and no GPU
time". That is FALSE -- there are no generations to judge. A hardware-matched button control requires
RE-GENERATING one on the A5000, which is GPU work.
