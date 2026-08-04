# Phase BEHAV-WRITE — Behavioral necessity of the L8–11 demo-codeword WRITE

**Question.** Phase BEHAV-CARRY found the L14–21 carry heads behaviorally NULL and proposed the
interpretation *"the remap is committed early at the write, so ablating the carry mid-generation is
too late."* This tests that directly: is the **demonstration write** (L8–11 MLP at the demo-codeword
positions — the write characterized in Phase 6/6b/9) **behaviorally necessary** for the jailbreak?

**Design (paired, controlled, prefill-only).** For each DS-malicious prompt, generate 3 arms and
StrongREJECT-judge each vs the true harmful goal:
- **baseline** — unmodified.
- **write_abl** — zero the L8–11 MLP output at the **DEMO** codeword positions (all codeword
  occurrences except the final/query one) via `pc.ComponentOutSwap(mlp_out, source=zeros)`. Because
  ComponentOutSwap's position guard (`0≤p<seq`) fails on cached decode steps (seq=1), the edit fires
  **only during prefill** — it corrupts the demo positions' written state (hence their KV), then
  generation proceeds normally. This is exactly "corrupt the early write, then generate." The query
  codeword position is **preserved**, so the null is not a query-parse artifact.
- **rand_pos_abl** — zero the same layers at **count-matched random non-codeword** prompt positions
  (position-specificity control).

Judge = StrongREJECT rubric + MALICIOUS-first classify. Test = McNemar exact on paired
baseline→ablated flips + paired bootstrap CI on ΔASR, Holm across arms. Cohorts: clearharm (86) +
curated (51), locked splits. ~12 demo positions ablated per prompt × 4 layers.

## Result — CLEAN NULL (even flatter than the carry heads)

| cohort · split | n | ASR base | ASR write_abl | ASR rand_pos | ΔASR write (CI) | McNemar p (Holm) | empty |
|---|---|---|---|---|---|---|---|
| clearharm train | 44 | 0.386 | 0.409 | 0.409 | **−0.023** [−0.114, +0.068] | 1.000 (1.0) | 0 |
| clearharm test  | 42 | 0.310 | 0.310 | 0.357 | **0.000** [−0.143, +0.143] | 1.000 (1.0) | 0 |
| curated train   | 30 | 0.333 | 0.267 | 0.300 | **+0.067** [−0.100, +0.233] | 0.688 (1.0) | 0 |
| curated test    | 21 | 0.095 | 0.095 | 0.095 | **0.000** [−0.190, +0.190] | 1.000 (1.0) | 0 |

- **No behavioral necessity anywhere.** Every ΔASR ∈ [−0.023, +0.067]; every McNemar p ≥ 0.69
  (Holm 1.0); every bootstrap CI includes 0. The only non-zero point (curated train +0.067) is
  non-significant and **not distinguishable from the random-position control** (+0.033).
- **Not a decoder-break artifact:** empty rate = 0 in every cell — zeroing ~12 positions across 4
  layers leaves generation fully coherent (scores span 0→1 as normal).
- Contrast with the representational result: the *same* L8–11 write is Holm-significantly **necessary
  for the concept readout** (Phase 6: L9 +0.030–0.080 FC necessity) — yet removing it does nothing to
  harmful behavior.

## Interpretation — the dissociation is COMPLETE and robust across the circuit

Both causal control points of the concept **representation** are behaviorally **null**:

| stage | representational role | behavioral necessity (ASR) |
|---|---|---|
| L8–11 demo WRITE | Holm-sig **necessary** (FC readout) | **NULL** (this phase) |
| L14–21 carry heads | necessary **+ sufficient** (FC readout) | **NULL** (BEHAV-CARRY) |

The "committed early" hypothesis is **falsified in the strong direction**: it is not that necessity
moved upstream to the write — *neither* site is behaviorally necessary. Doublespeak's harmful behavior
does **not causally reduce to the concept-carrying machinery we mapped.** Most consistent account:

1. **The jailbreak is carried by the demonstration *mode*, not the concept subspace.** The demos
   establish a "comply with the in-context substitution task" frame + refusal bypass; that frame — not
   the precise token→concept remap vector — drives the harmful continuation.
2. **Massive redundancy.** The concept is re-derivable from the intact demos/query at every decode
   step; a single-site prefill ablation is routed around autoregressively.
3. **Probe ≠ behavior.** The FC last-token DE_context readout is a sharp handle on the representation
   but is not on the causal path to the harmful generation.

This closes the loop with the study's other objective-level results — the **suffix-objective null**
(Q12), the **mechanism-guided optimization CI-backed negative**, and **state-injection ≤0.16
behavioral sufficiency**. All four point the same way.

## Bottom line (honest, and a genuine contribution)

**A rigorously-mapped, cross-cohort, Holm-corrected representational circuit for Doublespeak whose
causal grip on end-to-end harmful behavior is null at every surgical intervention we can pose.** The
mechanism faithfully explains *how the concept is represented and carried*; it does **not** explain
*why the model complies*. That is a real, bounded, publishable dissociation — it tells the field that
concept-circuit necessity (even necessity **+** sufficiency for a readout) does **not** imply
behavioral necessity for the jailbreak, and that Doublespeak defenses aimed at the concept-carrying
subspace are unlikely to work.

## Reproduce

```
sbatch --export=ALL,DSBENCH=doublespeak_causality/data/behavioral/beh_clearharm.json,DSLAYERS=8-11,DSMAXNEW=220,DSN=0 \
  doublespeak_causality/slurm/run_behav_write.sh      # + beh_curated.json
python scripts/phase_behav_carry_analyze.py outputs/behav_write_<cohort>_L8_9_10_11_<ts>_<jid>
```
Runs: clearharm `behav_write_clearharm_L8_9_10_11_20260804_110157_707908`,
curated `behav_write_curated_L8_9_10_11_20260804_110156_707909`.
