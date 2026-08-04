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

## Per-head decomposition (v2) — the pattern causality is DISTRIBUTED, no single necessary head
Ran the harness per-head (single `--heads` each) for the top-5 necessity heads on v2 (all self-swap 0.0):

| head | uniform-KO (C1−C_uniform, clean) dev / heldout | benign-transplant specific dev / heldout |
|------|-----------------------------------------------|------------------------------------------|
| L14H5  | **−0.050 / −0.031** | **+0.136 / +0.086** |
| L17H24 | −0.013 / −0.007 | +0.105 / +0.046 |
| L14H4  | +0.015 / +0.005 | +0.071 / +0.060 |
| L17H27 | +0.011 / +0.006 | +0.016 / +0.024 |
| L15H8  | ≈0 / ≈0 | ≈0 / ≈0 |

- **No single head's pattern is individually necessary** — the clean per-head uniform-knockout is ≈0 (even
  slightly NEGATIVE for L14H5, i.e. removing that one head's pattern alone is compensated by the others),
  yet the JOINT 7-head uniform knockout drops the reading +0.13–0.17. → the attention-pattern causality is
  **distributed / emergent across the carry set**, with redundant compensation — the same "distributed
  within a band" signature as the head output (Phase 5) and the MLP write (Phase 6/6b).
- By the (cross-length-caveated) benign-transplant measure, **L14H5 carries the most** concept-relevant
  attention, then L17H24, L14H4 — but even the top head is not individually necessary.

## Phase 4c — WHERE do the carry heads read? NOT from the demo codewords (v2, positive-controlled)
`scripts/phase4c_carryedge.py` (pc.AttentionKnockout, eager). Knock out the carry heads' ANSWER→key edges:
KO_demo (→ demo-codeword keys), KO_rand (→ random non-demo keys), **KO_all (→ ALL earlier keys = positive
firing control)**. v2, both splits:

| cell | dev (n=59) | heldout (n=57) |
|------|-----------|-----------------|
| **KO_all (positive control, C1−KO_all)** | **+0.246 [.167,.329]** | **+0.207 [.135,.288]** |
| KO_demo (C1 − KO_demo) | +0.007 [.003,.012] | +0.003 [.001,.005] |

- **The knockout machinery fires strongly** (KO_all drops the reading ~0.21–0.25, both splits) — the carry
  heads' answer-position attention IS causally important.
- **But knocking out only the demo-codeword edges is negligible** (KO_demo ~0.005 = only ~2–3% of KO_all).
- → **the carry heads retrieve the concept from the DISTRIBUTED context at the answer position, NOT from the
  demonstration codeword tokens specifically.** By the answer position the concept is already in the residual
  stream (written @L9 on the demo positions, carried up); the carry heads read it from the broad context, not
  by fresh demo-codeword attention. Reconciles the original all-head query→demo edge-KO null (Phase 4) — no
  privileged demo-codeword retrieval edge anywhere.

## Caveats / next
- The benign transplant is cross-length-approximate; the uniform knockout is the clean claim.
- Answer-position pattern only; the pattern at the demo/query positions is separate.

Reproduce: `DSBENCH=...bench_clearharm_v2.json DSNPROMPTS=0 sbatch slurm/run_ds_p4bp.sh` (heads via DSHEADS).
