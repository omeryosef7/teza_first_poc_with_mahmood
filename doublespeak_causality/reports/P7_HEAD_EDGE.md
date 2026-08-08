# §7 — Targeted Refusal Head/Edge Analysis (active band L13–20)

**Status:** ✅ DONE. The refusal-carry evidence is **DISTRIBUTED across L13–20 heads — no single-head
bottleneck** (parallel to P4b's distributed concept-reading). Endpoint = decision-token refusal projection
(validated L18); Direct→DS head-z patch restoration.

**Run:** `phase7_refusal_head_edge.py` (`...736900`), v3 clearharm, band L13–20. Reuses pc.ZHeadCapture/
ZHeadPatch (§5 head-z) + pc.AttentionKnockout (§4 edge) + proj_last refusal readout.

## Result — HEAD z-patch (Direct→DS, restore refusal projection)
- **distributed = True**: best single head restores only **25–33%** of the refusal gap (max_single_frac
  0.253–0.325; top heads L15H7, L13H9, L13H12, L14H24, L16H4, L16H10), while **all band heads together restore
  61–81%** (band_all_frac 0.61–0.81). Holm-significant heads: 48–82. self-swap dev = 0 (no-op ✓); norm-random
  dev ≈ 0.05 (control ≈0).
- => No sparse refusal-carry head; the "do-not-refuse" evidence is carried by a distributed set across
  L13–20. Quantified distributed necessity rather than forced sparsity (as P4b found for concept-reading).

## Result — EDGE knockout (decision-token incoming edges by source group)
- Knocking out the **demo-ANSWER** source edges has the largest effect (restore ≈ −2.6, spec_vs_rand excl 0),
  i.e. the demo answers' incoming edges carry substantial refusal-relevant signal; demo_codeword/query/
  separators edges are small. (Edge magnitudes are noisier than the head z-patch; the head distributed-necessity
  is the load-bearing §7 result.)

## AUDIT CORRECTION (2026-08-08)
The `distributed=True` verdict was computed from the best single HEAD only; the audit (wf_383ca171) showed a
single LAYER carries much of the ceiling: **per-layer L13 restores ~0.53 of the gap = ~66% of the band ceiling
(0.81)**. So the refusal-carry is **distributed across HEADS (no single-head bottleneck) but CONCENTRATED at the
LAYER level (L13-heavy)** — not fully distributed. The head-level distributed-necessity claim stands; the
layer-level claim is corrected to "L13-concentrated." (Harness `distributed` verdict fixed to also gate on max_layer.)

## Verdict
Refusal-carry is **head-distributed but layer-concentrated (L13)** across the L13–20 band (no bottleneck head); demo-answer edges are the most
implicated source group. Consistent with the residual-carry picture (§3) and the distributed concept circuit (P4b).
