# §3 — Refusal-Suppression Causal Localization at the Decision Token

**Status:** Gate A **PASS (representational)** on clearharm, replicated train/dev/**test**; NULL on generated.
Behavioral confirmation (Gate B, §23) is the decisive next arm and is **not yet run** — do **not** call this
"behaviorally causal" (§0.2).

**Runs:** `refsuploc_clearharm_...732161` (170r), `refsuploc_generated_...732162` (154r) · v3 confirmatory,
splits train85/dev43/test42 (clearharm), 77/39/38 (generated) · commit at launch `4b84c0a9`.
**Analyzer:** `scripts/analyze_refsuploc.py` (ratio-of-means frac; one-sided Wilcoxon + Holm per-component;
Gate-A hit = Holm-p<0.05 ∧ direct restores MORE than norm-matched random (paired-diff CI lo>0) ∧ frac≥0.5).

## Design
For each item, replace the **DS prompt's decision-token (last-position) residual/sub-block activation** at
(layer L, component C) with the **matched Direct-harmful donor's** decision-token activation; read the change
in the **validated** refusal-direction projection (P7 set; anchor L18, cross-checked at L24). Donors:
`direct`/`neutral` = necessity; `rand` (norm-matched random) = specificity (§0.4); `self` = locality no-op.
Endpoint is **representational** (refusal projection); this localizes the **carry / readout** of the
suppression (§4 B/C), not its demonstration origin (§4 A / §5).

## Result — clearharm (Gate A PASS, replicated incl. frozen test)
Restoration lives in the **residual stream at L15–L18** (and extends up to the readout as the anchor moves):

| anchor | split | top cell | frac (ratio-of-means) | Holm-p | direct−rand CI | self-swap |
|---|---|---|---|---|---|---|
| L18 | train (n=85) | resid_pre L18 | **0.936** | 0.0 | [1.97, 3.14] | 5e-6 |
| L18 | dev (n=43) | resid_pre L18 | **0.931** | 0.0 | [1.58, 3.16] | 5e-6 |
| L18 | **test (n=42)** | resid_pre L18 | **0.926** | **0.005** | [1.61, 3.36] | 4e-6 |
| L24 | train (n=85) | resid_pre L24 | 0.998 | 0.0 | [3.17, 5.50] | 5e-6 |

- **Residual carry, not sub-block write:** at L16/L18 the residual patches restore frac 0.61–0.94, while
  `attn_out` (0.09–0.25) and `mlp_out` (0.04–0.22) barely move the readout even where Holm-significant —
  i.e. the suppressed refusal state is carried in the **accumulated residual**, not re-injectable through a
  single attention/MLP write at the decision token.
- **Not a readout-proximity artifact:** patching the residual at L20 and reading at **L24** still restores
  frac 0.83 (specific vs random), 6 layers downstream; upstream L15–L17 patches restore 0.59–0.80.
- **Onset ~L13** (matches P7 validated-axis onset): L13/L14 residual patches restore specifically on test
  (frac 0.54, direct−rand CI [2.6,4.0]).
- **Locality:** self-swap max|restore| ≤ 5e-6 in every split.

## Result — generated cohort (NULL / no specific hit)
No Gate-A hit in any split: the L16/L17 residual patch's restoration does **not** exceed the norm-matched
random donor (paired direct−rand CI negative), so it fails specificity. Consistent with the pre-registered
non-exchangeability (generated DS is net-negative). Report per-cohort; do **not** pool as the headline.

## Verdict & next
- **Gate A: PASS (representational, clearharm)** — a targeted residual overwrite at L15–L18 specifically
  restores the refusal projection, replicated on the frozen test split. **NULL on generated.**
- **Next (decisive):** Gate B / §23 behavioral confirmation — apply the same Direct→DS decision-token
  residual patch at L18 (and the L15–L17 band) **during generation** and measure ΔASR, vs `rand` and `self`
  controls. Only that converts this representational localization into a behavioral-causality claim.
- Feeds Figure 2 (refusal-suppression localization, behavior-confirmed nodes once Gate B lands).
