# P4 — head-restricted weight operator: design, verification, fit status (F5, 2026-10-14)

## Head → o_proj mapping (verified in source, poc_stage2 transformers)
`LlamaAttention.forward`: `attn_output` [b, 32 query heads, q, 128] → `.transpose(1, 2).contiguous()` →
`.reshape(*input_shape, -1)` → `o_proj`. Query head *h* owns o_proj **input columns [128h, 128h+128)**. GQA
(`repeat_kv`, 4 query heads per KV head) happens before and does not change the column layout. The CSI knockout's
`heads=` argument indexes the same **query** heads (`ScopedAttentionKnockout`: `n_heads = num_attention_heads = 32`).
Unit-tested: `tests/test_p3_p4.py::test_p4_head_restriction_embeds_zero_outside_heads` (head 2 → columns 256–383).

## Inherited head circuit (SUMMARY_2026-09-02_TO_09-26 §4.3)
- D32: 8-head set **[19, 17, 23, 6, 13, 2, 24, 28]** reproduces F = 0.8635 of the all-head knockout on **basket
  validation** (rank 1/21, floor p = 0.0476). Heads tied across the knockout band L6–14.
- D34: single heads **2, 19, 17, 23** clear the null anchor. D36: cell **(L10, head 2)** carries 96.1 % of head 2's
  effect. D35 (negative): head 2 does **not** transfer to button.
- All rung-1 necessity; no arbitrary-cell control → no "writer" language.

## Capture coverage
`cap_<cw>_{BASE,KO}.pt` hold o_proj and down_proj **input and output** at the codeword row for layers 6–18
(26 modules), 670 TRAIN prompts × 67 domains per codeword. o_proj input = concatenated query-head outputs ⇒ a
head-restricted operator can be fitted from the existing capture with no new GPU work.

## Operators (`research/heretic_csi/p4_head_fit.py`, frozen P2b objective mse / steer 0.3)
TOP8 (o_proj L6–18, A restricted to the 8 heads) · RH8_0..59 (random disjoint 8-head sets from the 24 non-TOP8
heads, fitted identically, rescaled per module to TOP8's norm) · FULLO (all heads) · MLP (down_proj) · ATTNMLP
(both; refit) · H2 · CELL_L10H2 — at ranks 1 and 4. Fitting-side diagnostics: in-sample net gap closure, and
5-fold domain-grouped TRAIN CV for TOP8 vs RH8_0..19.

## Early fitting-side numbers (in-sample, rank 1; from the first, cancelled serial jobs 1023525/1023526 — same code)
| cw | variant | o_proj gap closure | preserve damage | gap closure over all 26 modules | total ‖ΔW‖ |
|---|---|---|---|---|---|
| basket | TOP8 | 0.571 | 0.0025 | 0.194 | 18.33 |
| basket | FULLO | 0.575 | 0.0007 | 0.196 | 9.97 |
| button | TOP8 | 0.625 | 0.0023 | 0.199 | 22.34 |
Reading (fit side only): restricting the o_proj edit to 8 of 32 heads loses almost no in-sample gap closure
(0.571 vs 0.575) but needs ~1.8× the norm and causes ~3.5× the preserve damage. Whether random 8-head sets do
equally well is exactly what the RH8 family + CV measure. Not an endpoint.

## Status
Fits running on cpu-killable (32 CPUs, 2-day limit), one job per (codeword, rank): 1023554 basket r1,
1023555 basket r4, 1023556 button r1, 1023557 button r4. Each writes `outputs/heretic_csi/p2b/prod/p4/
factors_p4_<cw>_r<R>.pt` (BEFORE its CV step) and `p4_fit_<cw>_r<R>.json`; log line `FACTORS_SAVED` then
`P4_FIT_DONE`, slurm trailer `DONE_MARKER p3p4 rc=0`.

## GPU eval (written, NOT submitted)
Plans `outputs/heretic_csi/p2b/plans/p4_<cw>_r<R>_{train,val}.sh` → `p4_template.sh` → `p3p4_emit.py --what p4` →
F2's `p2b_runner.py` (`op:<factors_p4>:<KEY>` OPSPEC, unchanged). 68 arms per (cw, rank, split) + 4 liveness at r1.
Analysis: `research/heretic_csi/p4_analyze.py --codeword <cw> --prefix hcsi_p4_<cw>_<train_k4|validation>
--split <train|validation> --expect-n <268|230> --ranks 1,4 --out reports/heretic_csi/p4_<cw>_<split>.json`.
Estimate: TRAIN-K4 ≈ 5.0 GPU-h, VALIDATION ≈ 4.3 GPU-h per (cw, rank) ⇒ ≈ 37 GPU-h for both codewords × both ranks
× both splits. Pre-registration draft: `outputs/heretic_csi/p2b/prod/p4/PREREG_P4_DRAFT.json` (must be reviewed,
copied to `configs/heretic_csi/PREREG_P4.json` and committed before any P4 endpoint).

## Caveat that must travel with any P4 result
The 8-head set was certified on **basket VALIDATION** (D32). A basket VALIDATION P4 read is a held-out test of the
TRAIN-fitted weight operator, but **not** a fresh test of the head nomination. Fresh confirmation needs P6 codewords.
