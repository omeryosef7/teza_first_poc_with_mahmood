# reports/PHASE7_PATH.md — Path mediation: DIRECT-vs-TOTAL of the answer-position head band

**Question (plan Q7 / Gate 5):** are the Phase-5 answer-position heads genuine concept-**carry** (their
effect flows through downstream layers) or readout-**proximal output** heads (direct to the logit)?

## Method
`scripts/phase7_direct_total.py`, reusing `50_path_patching`'s freeze primitives verbatim
(`FreezeAllHeadsExcept` + `FreezeMLP` + `capture_clean_all`). For each candidate head S:
- **TOTAL[S]** = m_clean − M(patch S's z ← BENIGN at the answer position; everything recomputes).
- **DIRECT[S]** = m_clean − M(same benign injection, but ALL downstream heads + MLPs frozen to clean-DS →
  only S's residual-skip path to the logit survives).
- **direct_frac = median(DIRECT/TOTAL)** over examples with |TOTAL| > 0.05.

Metric M = logit_diff(concept − codeword) at the last position (same as 48/49/50). Sanity gate (audit
14/15): direct_frac is nulled unless `freeze_consistency_dev ≤ 0.05` (freeze-all-clean + clean sender
reproduces m_clean) AND `selfswap_dev ≤ 0.05`. Jobs 704725 (curated) / 704726 (clearharm), n≥20/split.
**All heads trust=True; freeze_consistency_dev = 0.0 and selfswap_dev = 0.0 everywhere** (freeze exact).

## Result — mid-band = CARRY (mediated), late = PROXIMAL OUTPUT (direct). Both cohorts, both splits.

direct_frac (0 ⇒ fully mediated/carry · 1 ⇒ fully direct-to-logit):

| head | curated dev | curated heldout | clearharm dev | clearharm heldout | reading |
|------|------------|-----------------|---------------|-------------------|---------|
| L14H4  | 0.00 | 0.00 | 0.00 | 0.00 | **carry** |
| L14H5  | 0.00 | 0.05 | 0.00 | 0.00 | **carry** |
| L14H23 | 0.00 | 0.00 | 0.00 | 0.00 | **carry** |
| L15H4  | 0.00 | 0.00 | 0.00 | 0.00 | **carry** |
| L15H8  | 0.00 | 0.00 | 0.00 | 0.00 | **carry** |
| L17H27 | 0.17 | 0.00 | 0.09 | 0.07 | mostly carry (small direct) |
| L18H20 | 0.00 | 0.04 | 0.08 | 0.09 | **carry** |
| L21H10 | 0.00 | 0.00 | 0.00 | 0.02 | **carry** |
| L30H15 | 0.65 | 0.57 | 0.50 | 0.47 | **proximal output** |
| L31H0  | 0.76 | 0.63 | 0.60 | 0.63 | **proximal output** |

- **The mid-to-late-mid band L14–L21 are CARRY heads (direct_frac ≈ 0):** freezing all downstream
  heads/MLPs to clean removes essentially their whole logit effect, so that effect is *reconstructed by
  downstream layers* — they feed the concept forward, they do not write it to the logit directly.
- **Only the latest heads L30–L31 are readout-PROXIMAL output heads (direct_frac ≈ 0.5–0.76):** roughly
  half-or-more of their effect reaches the logit through the residual skip alone.
- **Resolves the Phase-5 proximity caveat:** the mechanistically important mid-band (L14–L21) is genuine
  carry, NOT a readout artifact. The proximity concern applies only to L30–L31.

## Interpretation — the assembled causal circuit
**L8–11 demonstration-codeword retrieval (K/V) + L9 MLP write → L14–L21 answer-position CARRY heads
(effect mediated through downstream layers) → L30–L31 proximal OUTPUT heads → logit.**

Each stage is causally tested: demo-KV necessity (Phase 4), MLP-write necessity @L9 (Phase 6, Wilcoxon
Holm all 4 cells), head necessity L14–18 (Phase 5, Wilcoxon Holm 3/4 powered cells), and now the
carry-vs-output separation (Phase 7). Distributed within each band (no single necessary head/edge), but
clear directed layer structure. Gate 5 met for the carry band.

## Caveats / next
- direct_frac is a median over |TOTAL|>0.05 examples; TOTAL is in raw logit_diff units (mid heads have
  large TOTAL 1–2 logits, confirming a real effect being mediated, not a near-zero ratio artifact).
- This tests the head→logit split. The upstream L9-write → L14–21-head EDGE (does the carry band read the
  L9 MLP write?) is the remaining path-patch (sender=L9 MLP, receiver=carry heads) — future work.
- Sufficiency (install carry-head z into benign) not yet run.

Reproduce: `python scripts/phase7_direct_total.py --bench data/bench/bench_<cohort>.json --heads <L..H..list>`.
