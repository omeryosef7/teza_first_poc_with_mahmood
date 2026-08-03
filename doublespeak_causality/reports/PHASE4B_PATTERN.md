# reports/PHASE4B_PATTERN.md — Attention-PATTERN causality at the carry heads (NEW, v2 116-ex)

**Question:** do the L14–21 carry heads read the concept via WHERE they attend (their attention pattern),
not just via their output z? Complements the edge-knockout (Phase 4, null) and the head-z necessity (Phase 5).

## Method
`scripts/phase4b_pattern.py` (harness authored by the ultracode workflow, self-swap-gated + code-reviewed;
in-file eager-attention capture/patch primitive, requires attn_implementation="eager"; GQA-aware). For the
validated carry heads, at the FC answer position, replace the DS attention-probability ROW (query→all keys)
with a donor and read FC p_concept. Cells: C1 baseline · **C_benign** (row ← matched BENIGN pattern,
trailing-aligned) · **C_uniform** (row ← uniform over causal keys = pattern-space knockout) · C_rand
(random non-candidate head's own DS pattern, specificity) · **C_self** (own DS pattern = exact no-op).
Run on the expanded **v2 bench (116 examples, 30 new concepts)**, both splits. self-swap_max_dev = **0.0**.

## Result — the carry-head attention PATTERN is causal, replicating on locked test

| cell | dev (n=59) | heldout (n=55) |
|------|-----------|-----------------|
| **C_uniform knockout** (C1 − C_uniform; clean, same-length) | **+0.166 [.097,.238]** | **+0.134 [.077,.199]** |
| **C_benign transplant** specific (C_rand − C_benign) | +0.460 [.371,.547] | +0.451 [.362,.542] |
| self-swap dev | 0.0 | 0.0 |

- **Washing out WHERE the carry heads attend (uniform pattern) drops the reading +0.13–0.17**, clean and
  replicating on the locked test — so the carry heads' attention **pattern** is causally necessary, a
  stronger and more specific lever than the null query→demo edge-knockout (Phase 4) and larger than the
  per-head z-output necessity (~.02–.10, Phase 5).
- The **benign-pattern transplant** effect is much larger (+0.45) but carries a **cross-length caveat**: DS
  and benign FC prompts differ in token length, so the benign row is trailing-aligned onto the DS keys (an
  approximate transplant, flagged per-example as `n_len_mismatch`). The clean, exact-length **uniform
  knockout** (+0.13–0.17) is the conservative, un-caveated measure of pattern causality.

## Interpretation
The carry heads (L14–21) do not merely emit a concept-laden output — **they read the concept by attending to
the right places** (attention pattern), and disrupting that pattern removes a robust chunk of the reading.
This refines Phase 5/7: the carry stage is causal both in its **pattern** (where it reads, Phase 4b) and its
**output** (what it writes, Phase 5) and is downstream-mediated (Phase 7). New causal handle beyond the
head output.

## Caveats / next
- The benign transplant is cross-length-approximate; the uniform knockout is the clean claim.
- Answer-position pattern only; the pattern at the demo/query positions is separate.
- Per-head pattern-necessity (which head's pattern matters most) not yet decomposed — future.

Reproduce: `DSBENCH=...bench_clearharm_v2.json DSNPROMPTS=0 sbatch slurm/run_ds_p4bp.sh` (heads via DSHEADS).
