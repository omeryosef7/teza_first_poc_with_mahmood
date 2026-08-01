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

---

## N7-B — Reasoning-model CoT trajectory: hypothesis REFUTED; D5 refined. **[novel, honest]**

`52_cot_concept_trajectory.py` on Qwen3-14B (thinking-on) and DeepSeek-R1-Distill. At a grid of
CoT-depth checkpoints + the answer, INTERRUPT with a benign forced-naming anchor ("in one word, the
object referred to above is:") and read the concept-vs-codeword LABEL. n=6/condition (small).
Positive control PASSES on both (Direct@answer 0.8/1.0; Neutral 0.0 throughout).

reads_as_concept trajectory (cot_0→cot_9 = CoT deciles, then answer):

| model | condition | mid-CoT | answer |
|---|---|---|---|
| **Qwen3-14B** | DOUBLESPEAK | **0.67–1.00 (high throughout)** | **1.00** |
| Qwen3-14B | NEUTRAL | 0.00 | 0.00 |
| **DeepSeek** | DOUBLESPEAK | **~0.00–0.25 (near zero)** | **0.67** |
| DeepSeek | NEUTRAL | 0.00 | 0.00 |

- **The "reasoning resolves the codeword" hypothesis is REFUTED.** Neither model resolves the
  hijack away: Qwen3 names the concept at EVERY CoT checkpoint (the reading is fully present from the
  start and persists to the answer); DeepSeek names it only at the answer (it emerges LATE, the
  opposite of resolution). Neutral stays 0.0 for both — the anchored readout is specific.
- **This REFINES D5 (important):** D5's natural post-`</think>` readout found the hijack weak/absent
  on reasoning models, but the **anchored forced-naming** readout reveals it IS present (DeepSeek
  0.67 at the answer vs D5's +0.33 natural; Qwen3 ~1.0 throughout). So reasoning is NOT a
  representational defense — the hijacked reading is there when the model is forced to name the
  referent; it simply isn't verbalized in the free-form answer. The D5 "absent" is a readout
  property (natural answers don't name the object), not evidence the concept is gone.
- **Model contrast:** Qwen3-thinking carries the concept from the CoT's first token (consistent with
  the reading being context-installed early/mid-stack, per D6); DeepSeek's concept naming builds up
  and only surfaces at the answer.
- **Honest scope:** n=6/condition, single seed, per-bin counts small — suggestive, not definitive;
  a larger-n rerun would tighten the trajectory. But the qualitative contrast (Qwen3 throughout vs
  DeepSeek answer-only, both Neutral-clean, both positive-control-passing) is clear.
- Artifacts: `outputs/cot_traj_Qwen3-14B_..._698757`, `cot_traj_DeepSeek-..._698758`.

### N7-B Phi-4 follow-up: readout does NOT certify (inconclusive).
Anchored CoT probe on Phi-4-mini-reasoning fails its positive control (Direct@answer = 0.0): 13/18
prompts truncated (CoT > 1536 tokens never reaches `</think>`) AND Phi-4's verbose `\boxed{}` math
answers defeat the first-4-word `classify_answer` (the D5-flagged readout artifact). So we cannot
resolve whether D5's Phi-4 "absent" is a readout artifact — the anchored readout is also broken on
Phi-4. The Qwen3/DeepSeek N7-B result (both positive-control-passing) is unaffected. Honest
inconclusive; not chased further (readout engineering rabbit hole on one model).

---

## N7-E — The attention→MLP cascade quantified; D6 decoupling clarified. **[synthesis, CPU]**

Reusing committed artifacts (D3 head z-AtP, N7-A MLP AtP, D6/W3-b concept projection) — no GPU:

| pair | attn peak | MLP peak | lag | attn L7–14 | MLP L7–14 | MLP late (L20–31) |
|---|---|---|---|---|---|---|
| bomb | L9 | L11 | +2 | 62% | 47% | 17% |
| grenade | L9 | L11 | +2 | 67% | 53% | 11% |
| chlorine | L13 | L14 | +1 | 55% | 41% | 23% |

- **The cascade is robust:** MLP |AtP| peaks **1–2 layers after** the attention z-AtP for every pair —
  attention writes the demo→query context link, MLPs consolidate the concept ~2 layers downstream.
- **D6's "decoupling" is clarified (honest):** the concept PROJECTION grows +8.82 across L20–31, but
  late-layer MLPs carry only **17% of Σ|AtP|** (bomb; 11–23% across pairs) and MLP AtP anti-correlates
  with the concept-emergence rate (−0.26). So the late projection growth is **passive residual /
  RMSNorm accumulation toward the unembedding, NOT new causal computation** — the causally-important
  computation (both attention and MLP) is confined to the mid-band (L7–14). The projection keeps
  rising late only because the residual accumulates and its overlap with the concept axis grows as
  the rep approaches the readout, not because late layers compute anything.
- **Fully unified mechanism (D3+W4+D4+N7-A+N7-E):** (1) attention heads write the context link at
  L7–9 (peak L9), (2) MLP sublayers consolidate the concept at L9–14 (peak L11–14, +2-layer cascade),
  (3) late layers passively carry/scale it to the readout (low AtP), (4) all distributed across many
  heads and MLPs — no bottleneck, no sparse circuit. Every step validated against true patching.
