# FAILED RUN -- quarantined with provenance. Its 5.1G `cache/` was reclaimed; nothing else removed.

Job 880540, node rack-omerl-g01. SLURM reported **COMPLETED, ExitCode 0:0**, while the script's own
trailer reported **rc=1**: `OSError: [Errno 122] Disk quota exceeded`. See CONT-ENTRY 072.

## What failed, and what did not

`results.jsonl` holds **3720 rows -- the full row set**. The run captured everything and died at the
end, while writing `metadata.json`, which is **0 bytes**.

## The judgment call, stated honestly

Every reader here resolves a corpus through `lpm.load_corpus`, which needs `metadata.json` for the
site list, the layer list and `bank_file_sha16`. Without it the cache could not be loaded, indexed or
verified against a bank. **It was probably reconstructible** -- the site and layer lists follow from
`config.json` and the bank hash is computable -- and I chose not to reconstruct it. Hand-writing the
provenance file of a scientific corpus so that it passes the very hash checks that exist to catch
mismatches is a worse hazard than re-running. That is a choice, not a necessity; it cost about one
GPU-hour.

## What is KEPT

`config.json`, `RUNMETA.json`, `results.jsonl` (3720 rows of per-row provenance), and this file --
the evidence that the run happened and how it failed (mandate section 53). What was reclaimed is bulk
no reader could interpret.

## Superseded by

Job 880762, a re-run restricted to **layer 24 only**. The controls this corpus exists to supply --
`cw_demo_prev_mean`, `cw_demo_next_mean`, `cw_demo_rand_mean` (C-CONT-040, CONT-ENTRY 068) -- are
needed at L24 and nowhere else. The original swept 19 layers because it copied the cont1 invocation.
