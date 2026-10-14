# PR-HCSI-S084 (+ AMENDMENT 1) — FROZEN analysis invocation

Frozen 2026-10-14 by F6, BEFORE either extended-control job (1027577, 1032110) finished and before any of their
new endpoints was read. Only the four OVL_* overlap arms (which reproduce already-read arms of job 1022698) were
checked: bit-exact (max |diff| 0.0 on identical 230-row id sets).

## The one command (run from the repo root, after BOTH jobs show `DONE_MARKER ... rc=0`)

```
/home/sharifm/students/omeryosef/miniconda3/envs/poc_stage2/bin/python research/heretic_csi/p2a_powered_analyze.py
```

It takes no arguments. Internally it (1) re-runs the overlap VOID check, (2) checks every job log reports only
"NVIDIA RTX A5000", (3) calls the frozen analyzer exactly as:

```
python scripts/dcs_csi_subspace_analyze.py --codeword button --tag-prefix hcsi_p2a_button --expect-n 230 \
  --arms BASE,KO,KO_SELF,KO_FULL,KO_CAND_r4,KO_RAND_r4_0..KO_RAND_r4_189,KO_SHUF_r4_0..KO_SHUF_r4_9 \
  --candidate-arm KO_CAND_r4 --comparator-arm KO_RAND_r4_0 --control-prefixes KO_SHUF,KO_RAND \
  --split validation --direction sufficiency --option-mass-floor 0.05 --expect-n-controls 200 --allow-short 20 \
  --require-slurm-job 1022698,1027577,1032110 --out reports/heretic_csi/hcsi_p2a_button_r4ext_validation_analyzer.json
```

(4) recomputes every arm's statistic mean_d(dmean[arm] − dmean[KO]) UNROUNDED with the analyzer's own helpers
(same run dirs, BASE-referenced floor 0.05, (domain,slot) intersection over all arms), asserts it rounds to the
analyzer's published 5-dp values and that the key count equals the analyzer's `n_keys_common`, and (5) applies the
amended rule in the pure function `decide()`:

PASS iff Holm(\{r1: 0.2456, r16: 0.1754, r4: p_ext\})[r4] < 0.05, with p_ext = (1 + #controls ≥ candidate)/201 on
UNROUNDED statistics (ties count against the candidate) AND candidate > every KO_SHUF_r4_j (unrounded) AND
candidate−KO domain-cluster CI lower bound > 0 (frozen analyzer) AND all gates true AND no VOID (overlap mismatch,
non-a5000 GPU, analyzer VOID). The shared row set is reported against 203; arms with dropped keys are named.

**Primary statistic = the unrounded rank (coordinator instruction, review #4 item 9).** The frozen analyzer's own
rank uses 5-dp-rounded points (ties against the candidate); it is reported alongside as
`frozen_analyzer_rounded_rank` with an agreement flag. If they disagree, both are reported and the disagreement
is stated in the verdict text of the log.

Outputs: `reports/heretic_csi/P2A_BUTTON_R4_POWERED.json` (verdict) and
`reports/heretic_csi/hcsi_p2a_button_r4ext_validation_analyzer.json` (frozen analyzer), log
`outputs/heretic_csi/logs/analyze_button_r4ext_val.log`.

## sha256 at freeze

| file | sha256 |
|---|---|
| research/heretic_csi/p2a_powered_analyze.py | eb0da96df409d34ba1f9f682bb0f604e6c792c2b1c5f217773e212e7138c8f4c |
| research/heretic_csi/tests/test_p2a_powered_analyze.py (7 passed: synthetic decide() edge cases + equivalence with the frozen analyzer on already-read job 1022698) | a58599f7756e39fa9eab80398398b81f1a91ff1400b8b1745f2c886522f356ab |
| scripts/dcs_csi_subspace_analyze.py (frozen analyzer, unchanged) | 8a9e16944cc4dbc41bcec72e54c6162389dfe9f3eba4a4f852b134d9c09d556e |
| research/heretic_csi/p2a_powered_contrast_v2.py (descriptive contrast; already run) | 730edd61641a9b31285c78a51b4ef69a829f16e1d82c8f29007f345d4ad621e8 |

## PARENT BINDING RULE (added at freeze, 2026-10-14, before any S-084 read)
The S-084 verdict is **PASS only if BOTH** the unrounded decision (`p2a_powered_analyze.decide`) **and** the frozen
analyzer's own (5-dp-rounded) rank give PASS under the identical rule (Holm over {r1, r4, r16}, beat every SHUF,
CI-lo>0, gates, no VOID). Any disagreement ⇒ "DOES NOT PASS (rounding-sensitive)", reported with both ranks.
