# Phase BEHAV-CARRY — Behavioral necessity of the L14–21 carry heads

**Question.** The carry heads (L14–21, 9 heads) are representationally **necessary** (Phase 5) *and*
**sufficient** (Phase 7c) for the Doublespeak concept *readout* — the forced-choice DE_context probe at
the last token. Does that representational role translate into **behavioral** necessity? I.e. if we
ablate the carry heads throughout actual harmful generation, does the jailbreak success rate (ASR) drop?

**Design (paired, controlled).** For each DS-malicious prompt, generate 3 arms and StrongREJECT-judge each
against the true harmful goal:
- **baseline** — unmodified generation.
- **carry_abl** — `pc.AllPositionZHeadAblate(CARRY, mode="zero")` zeroes the 9 carry heads' output z at
  *every* position on *every* forward (prefill + each cached decode step), so the ablation persists
  through generated tokens (decode-safe zero mode, per the iter-86 audit).
- **rand_abl** — same construction on 9 **random non-carry** heads (count-matched specificity control).

Judge = StrongREJECT rubric + MALICIOUS-first classify (reuses 18's judge; MAL_THRESHOLD=0.25). Metric =
ASR (malicious rate) per arm/split. Test = **McNemar exact** on the paired baseline→ablated flips (correct
test for a paired judge design), Holm across the {carry, rand} arms, plus a paired bootstrap CI on ΔASR.
Cohorts: `clearharm` (86: 44 train / 42 test) and `curated` (51: 30 / 21), locked train/test splits.

## Result — WELL-CONTROLLED NULL (at best a weak, non-significant trend)

| cohort · split | n | ASR base | ASR carry_abl | ASR rand_abl | ΔASR carry (CI) | McNemar p (Holm) | empty |
|---|---|---|---|---|---|---|---|
| clearharm train | 44 | 0.364 | 0.273 | 0.341 | **+0.091** [−0.023, +0.227] | 0.289 (0.578) | 0 |
| clearharm test  | 42 | 0.357 | 0.286 | 0.333 | **+0.071** [−0.024, +0.167] | 0.375 (0.750) | 0 |
| curated train   | 30 | 0.333 | 0.433 | 0.300 | **−0.100** [−0.300, +0.100] | 0.508 (1.00) | 0 |
| curated test    | 21 | 0.095 | 0.095 | 0.190 | **0.000** [−0.190, +0.190] | 1.000 (1.00) | 0 |

- On **clearharm**, carry-ablation reduces ASR in a **consistent direction** across train and test
  (~7–9 pp), and by **more than the random-head control** (~2 pp). Discordant flips favor removal
  (train 6 off-1→0 vs 2 on-0→1; test 4 vs 1). **But it is NOT statistically significant** — every
  McNemar p > 0.28 (Holm > 0.57) and every bootstrap CI on ΔASR includes 0.
- On **curated**, the effect does **not replicate**: reversed on train (Δ = −0.10, ablation slightly
  *increased* ASR) and null on test (base ASR 0.095 is a floor — underpowered).
- **No degenerate-generation confound:** empty rate = 0 in every cell, so the null is not an artifact of
  zero-ablation breaking the decoder.

## Interpretation — a representation≠behavior dissociation (honest)

The carry heads are a **causal handle on the concept representation** (necessity + sufficiency for the
FC readout) but we have **NOT** shown they are **behaviorally necessary** for the jailbreak. The most
likely mechanistic reasons:

1. **The remap is committed early.** The demo-codeword→concept mapping is *written* at the L9 MLP
   demo positions (Phase 6/9); the carry heads *propagate* it to the last-token readout. During
   autoregressive harmful generation the model may re-derive the concept from the still-intact early
   write and demo KV at each step, routing around 9 zeroed carry heads.
2. **Distributed redundancy.** The concept is distributed within the L14–21 band (every prior phase
   found within-band distribution); zeroing 9 heads is a small perturbation to a redundant carry — the
   count-matched random control confirms 9 heads is near the noise floor behaviorally.
3. **Probe ≠ behavior.** The FC last-token DE_context probe and the harmful continuation may read the
   concept through partially different paths; the carry heads are pivotal for the explicit probe but
   not the generation.

This **dissociation is consistent with the study's other objective-level results** — Q12 suffix-objective
patching (well-controlled null) and the mechanism-guided optimization (CI-backed negative). The through-line
holds: **a strong, rigorously-established representational circuit whose causal grip on end-to-end harmful
behavior is weak.** That is a finding, not a failure — it bounds what "the circuit" explains.

## What would change the verdict (not run)

- **Behavioral necessity of the L9 write** (the *write* site, not the *carry*) — ablate the demo-position
  L9 MLP write through generation. If the remap is committed early, the write may be behaviorally
  necessary where the carry is not. This is the natural next causal test.
- **Wider-band / top-k carry ablation** — but the random control shows 9 heads is near the behavioral
  noise floor; a larger set risks non-specific decoder damage and would need a matched large random arm.

## Reproduce

```
sbatch --export=ALL,DSBENCH=doublespeak_causality/data/behavioral/beh_clearharm.json,DSMAXNEW=220,DSN=0 \
  doublespeak_causality/slurm/run_behav_carry.sh          # + beh_curated.json for cross-cohort
python scripts/phase_behav_carry_analyze.py outputs/behav_carry_<cohort>_<ts>_<jid>
```
Runs: clearharm `behav_carry_clearharm_20260804_100009_707831`, curated `behav_carry_curated_20260804_100428_707832`.
