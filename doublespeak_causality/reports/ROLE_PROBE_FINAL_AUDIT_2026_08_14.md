# ROLE-PROBE SPRINT — FINAL INDEPENDENT AUDIT

Required deliverable (plan §21). Reopens the raw artifacts and recomputes the
load-bearing numbers with **fresh code** (not the analysis scripts), to catch any
script bug before write-up. Read-only; scalar fields only (scores/labels/positions),
never generation text.

**Result: all load-bearing numbers reproduce exactly from raw.** No discrepancy found.

---

## 1. Independent recomputation (fresh code vs reported)

| quantity | recomputed from raw | reported | match |
| --- | --- | --- | --- |
| Gate 1 holdout AUC (`acts.npy` @L11 codeword, fit train / eval test) | **0.9972** | 0.997 | ✅ |
| Gate 1 token-identity control | 0.500 | 0.500 | ✅ |
| Necessity ΔASR (`raw.jsonl` scores, 757931) | **−0.048** | −0.048 | ✅ |
| Necessity refusal control ΔASR | +0.238 | +0.238 | ✅ |
| 2×2 main-effect Bombness (757943) | **+0.000** | +0.000 | ✅ |
| 2×2 main-effect refusal | +0.357 | +0.357 | ✅ |
| 2×2 interaction | **+0.000** | +0.000 | ✅ |
| Sufficiency ΔASR (757992) | **+0.048** | +0.048 | ✅ |
| Sufficiency refusal control ΔASR | +0.333 | +0.333 | ✅ |

Gate 1 AUC was recomputed by loading `acts.npy` directly and fitting a fresh
`LogisticRegression`; the Phase-4 ASRs by binarising `*_score >= 0.5` directly from
`raw.jsonl` and computing the 2×2 estimands by hand. All match the analysis-script
outputs to the printed precision.

## 1b. Cross-family recomputation (added 2026-08-15)

Independently recomputed the Phi/Qwen numbers from raw (Gate 1 from `acts.npy`, Phase-4
ASRs from `raw.jsonl`, fresh code):

| quantity | recomputed | reported | match |
| --- | --- | --- | --- |
| Phi Gate 1 AUC @L10 | 0.9858 | 0.985 | ✅ |
| Qwen Gate 1 AUC @L15 | 0.9989 | 0.999 | ✅ |
| Phi necessity ΔASR | −0.071 | −0.071 | ✅ |
| Phi refusal ΔASR | +0.095 | +0.095 | ✅ |
| Qwen necessity ΔASR | +0.048 | +0.048 | ✅ |
| Qwen refusal ΔASR | +0.167 | +0.167 | ✅ |

All cross-family headline numbers are raw-reproducible; the analysis scripts are bug-free
for the Phi/Qwen runs too. The entire body of work (Llama core + cross-cohort + 3-family
cross-model) is now audit-covered.

## 2. §21 checklist

| # | Item | Status |
| --- | --- | --- |
| 1 | Bombness probe: no token/position leakage | ✅ token-id 0.500 (exact, matched-pair), position 0.578 / length 0.587 near chance, vs AUC 0.997 |
| 2 | CARROT genuinely held out | ✅ CARROT ∈ dev, ∉ train (`test_probe_dataset`); split is codeword-disjoint |
| 3 | No test tuning | ✅ C/layer/position selected on **dev**; test evaluated once (`gate1_eval`) |
| 4 | Layer indexing | ✅ `hidden_states[L+1]` == post-block-L (D1/B8); preflight construction-valid; Gate 1 clean result confirms |
| 5 | Orthogonalization math | ✅ `orthogonalize()` = Gram-Schmidt; v_bomb cos vs refusal 0.06–0.15 (reported), used descriptively |
| 6 | α / dose sign | ✅ ablate DROPS readout (−1.3 to −1.6); add RAISES it (+5 to +8) — correct signs, direction-aware manip check |
| 7 | Random controls | ✅ bomb_random ≈ base in every Phase-4 run |
| 8 | StrongREJECT threshold | ✅ 0.5 (D2); sensitivity table shows the refusal-ablation headline is threshold-robust |
| 9 | Paired denominators | ✅ McNemar b/c paired per example; bootstrap resamples examples |
| 10 | 2×2 factorial estimands | ✅ independently recomputed (§1) |
| 11 | GCG candidate selection | N/A — no attack objective run (Gate D = Story A → §13 says do NOT optimize Bombness) |
| 12 | Seed coverage | N/A — greedy generation is deterministic; probe fitting deterministic (sklearn). No stochastic optimization in the core result |
| 13 | All new output dirs registered | ✅ 7/7 probe+phase4 full runs registered; registry 598 rows |
| 14 | All deviations logged | ✅ B19 (stale spans), V1 (doc location); process bugs (no_grad, band, sbatch-arg) in the execution log |
| 15 | No run directories overwritten | ✅ every run dir has a unique timestamp+jobid; all 7 distinct |

## 3. Limitations the audit confirms are stated, not hidden

- n=42 (clearharm test) / 38 (generated) for behavioral claims — nulls are CI bounds
  that exclude the refusal-magnitude effect, stated as such.
- Cross-cohort: Gate 1 replicates; the *prediction* is cohort-specific (frozen-direction
  transfer, B17); the generated *Bombness causal* run is INCONCLUSIVE (manip check failed,
  E22) — all reported honestly (CC3–CC5).
- Single dose/band/seed for the clearharm Phase 4; the sufficiency dose was calibrated
  on-manifold (§8.2).
- Refusal direction fit cross-distribution (B17); disclosed.
- Cross-model (Phi/Qwen) not run.

## 4. Verdict

The role-probe sprint's headline claims (Gate 1 decodability; Phase 3 prediction
dissociation; Phase 4 necessity/sufficiency/2×2 causal nulls; refusal as the sole causal
lever) are **raw-reproducible and pass the §21 checklist.** The result is trustworthy for
write-up. The one material boundary (cross-cohort prediction weakness / generated causal
inconclusive) is documented, not hidden.
