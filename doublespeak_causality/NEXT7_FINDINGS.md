# NEXT7 — Findings (continuous divergence)

Plan: `NEXT7_PLAN.md`. Env: Llama-3.1-8B / Qwen3-14B / DeepSeek / Phi-4, L40S, poc_stage2. Honest —
negatives included. Scalars only; no harmful text in any artifact.

---

## N7-D (part 1) — T3 depth-gating completes to 5/5 pairs. **[WIN, generalization]**

Ran the representational refusal-depth probe (`47_repr_toctou.py`) on the two remaining pairs
(cocaine, pistol) to get each pair's dominant refusal-check depth (the non-degenerate `early_vs_mid`
estimand; random control ~0):

| pair | install_above_random early | mid | **early_vs_mid [CI]** | dominant depth |
|---|---|---|---|---|
| bomb (prior) | +1.73 | +0.60 | +1.17 [+0.78,+1.57] | EARLY |
| **cocaine** | **+4.15** | +0.80 | **+3.41 [+2.98,+3.83]** | **EARLY** |
| grenade (prior) | −0.19 NS | +0.57 | −0.72 [−1.06,−0.38] | MID |
| chlorine (prior) | −0.07 NS | +0.66 | −0.68 [−1.05,−0.31] | MID |
| **pistol** | +0.67 | **+2.02** | **−1.29 [−1.55,−1.03]** | **MID** |

- **The depth-gated refusal check generalizes to all 5/5 pairs** — each has a concept-specific
  dominant depth (random control ≈ 0), CI excluding 0. Two families emerge: **EARLY-dominant**
  (bomb, cocaine) and **MID-dominant** (grenade, chlorine, pistol). This lifts the T3 phenomenon
  from 3 pairs to a 5/5 regularity: the refusal mechanism is depth-gated for every pair; only the
  gating depth is pair-dependent.
- **Prediction (tested next):** a behavioral TOCTOU factorial should recover the interaction at each
  pair's OWN dominant depth — early for cocaine, mid for pistol.
- Artifacts: `outputs/repr_toctou_..._698695` (cocaine), `..._698696` (pistol).

---

## N7-A — MLP-node attribution: the D4 mediation lands in mid-band MLPs. **[WIN, validated]**

`51_mlp_attribution.py` (per-layer MLP AtP, validated against a true SubmodulePatch(mlp) on the
top-40 cells). D4 showed the mid-band heads have DIRECT≈0 (all effect mediated downstream) and
head→head edges don't reconstruct it → the mediation runs through MLPs. N7-A localizes it:

| pair | MLP AtP peak | band L7–14 share | AtP-vs-true pearson | trustworthy |
|---|---|---|---|---|
| bomb | L11 | 47.3% | 0.936 | yes |
| grenade | L11 | 52.9% | 0.950 | yes |
| chlorine | L14 | 40.9% | 0.932 | yes |

- **The MLP mediation is mid-band-concentrated** (41–53% of Σ|AtP| in L7–14) and **validated**
  (pearson 0.93–0.95 vs true MLP patch) for all three pairs — directly confirming D4's inference
  that the effect the mid-band heads do NOT write directly is carried by the **mid-band MLP
  sublayers**.
- **A mid-band attention→MLP cascade.** The MLP contribution peaks slightly LATER (L11–14) than the
  attention z-AtP (peak L9): attention heads write the demo→query context link in L7–9, and MLP
  sublayers process/consolidate the concept in L9–14. Both are distributed (many heads, many MLP
  layers) — together a mid-band "processing zone" (L7–14), not a sparse circuit.
- **Unified mechanism (D3+W4+D4+N7-A):** the Doublespeak context effect is a **distributed mid-band
  computation across BOTH attention and MLP** — attention links the context, MLPs consolidate the
  concept, no single node is a bottleneck. This is the fullest mechanistic characterization to date,
  each step validated against true patching.
- Artifacts: `outputs/mlp_atp_{bomb,grenade,chlorine}/mlp_atp_results.json`.
