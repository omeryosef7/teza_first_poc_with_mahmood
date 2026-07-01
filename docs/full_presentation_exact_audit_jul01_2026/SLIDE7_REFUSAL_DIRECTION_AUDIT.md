# SLIDE 7 — Audit: Our Directions vs the Refusal-Direction Paper

**Audit date:** 2026-07-01  
**Sources:** `outputs/meeting/mahmood_analysis_only_jun30_20260630_193423/18_refusal_direction_method_audit.md`, `19_direction_cosine_matrix.csv`, `20_direction_metadata.csv`, `21_direction_similarity_summary.md`

---

## Summary Answers

1. **Have we extracted the canonical refusal direction for Qwen3-14B?** NO
2. **Have we extracted it for Gemma4-E4B-IT?** NO
3. **Can any saved direction currently be called "the refusal direction"?** NO
4. **Can we say the refusal direction changed?** NO — we cannot compare something we haven't extracted
5. **What is required?** Extract the canonical refusal direction using the original method (harmful vs. harmless contrast, likely from the Zou et al. or Arditi et al. protocol), then compare via cosine similarity to our behavioral/HVP/DVP directions.

---

## Our Direction Methods

All 9 variants per model are single-layer, unit-norm mean-difference vectors. No logistic regression used. No PCA subspace.

| variant | contrast_type | token_position | d_model | training_groups | notes |
|---------|---------------|----------------|---------|-----------------|-------|
| behavioral | outcome_behavioral | mixed | 5120 (Qwen3) / 2560 (Gemma4) | complied_vs_refused | Best AUC |
| startofthink | behavioral_position | startofthink | same | complied_vs_refused | Positional behavioral |
| endofthink | behavioral_position | endofthink | same | complied_vs_refused | Positional behavioral |
| dvp_startofthink | dvp (direct_harm_vs_puzzle) | startofthink | same | direct_harm_vs_puzzle | DVP = D context vs A context |
| hvp_startofthink | hvp (harmless_vs_puzzle) | startofthink | same | harmless_vs_puzzle | HVP = harmless vs A context |
| dvp_endofthink | dvp | endofthink | same | direct_harm_vs_puzzle | |
| hvp_endofthink | hvp | endofthink | same | harmless_vs_puzzle | |
| dvp_endofresponse | dvp | endofresponse | same | direct_harm_vs_puzzle | |
| hvp_endofresponse | hvp | endofresponse | same | harmless_vs_puzzle | |

**CRITICAL:** Gemma4 hvp_startofthink has **mean_norm = 0.000** (zero vector). This direction failed to extract (degenerate). It cannot be used for any comparison or analysis.

---

## Direction Cosine Similarity Matrix (Selected Values)

**Source:** `outputs/meeting/mahmood_analysis_only_jun30_20260630_193423/19_direction_cosine_matrix.csv`

All values are at the "best" layer for each pair. All absolute cosine values are **< 0.26**, indicating the directions are essentially orthogonal to each other.

### Qwen3 Key Pairs (absolute cosine)

| Pair | cosine | abs_cosine |
|------|--------|-----------|
| behavioral ↔ startofthink | 0.006 | 0.006 |
| behavioral ↔ endofthink | -0.050 | 0.050 |
| behavioral ↔ dvp_startofthink | 0.002 | 0.002 |
| behavioral ↔ hvp_startofthink | -0.010 | 0.010 |
| behavioral ↔ dvp_endofthink | -0.028 | 0.028 |
| behavioral ↔ hvp_endofthink | -0.060 | 0.060 |
| behavioral ↔ dvp_endofresponse | -0.035 | 0.035 |
| behavioral ↔ hvp_endofresponse | -0.038 | 0.038 |
| endofthink ↔ dvp_startofthink | -0.191 | 0.191 |
| endofthink ↔ dvp_endofthink | -0.258 | **0.258** (highest) |

**Conclusion:** Behavioral direction is NOT aligned with HVP or DVP (abs_cosine < 0.06). DVP and HVP directions are not aligned with each other or with behavioral (max 0.26). All direction families are substantially different from each other.

**Cross-model comparison is INVALID:** Qwen3 directions are 5120-dimensional; Gemma4 directions are 2560-dimensional. No alignment method exists in the current artifacts, so cross-model cosine similarity cannot be computed or interpreted.

---

## Comparison: Our Methods vs Canonical Refusal Direction

| Property | Canonical Refusal Direction (Zou/Arditi et al.) | Behavioral | HVP | DVP |
|----------|------------------------------------------------|-----------|-----|-----|
| Training contrast | Harmful vs harmless prompts | Complied attack vs refused attack | Harmless prompts vs puzzle attack | Direct-harm vs puzzle attack |
| Models tested | Llama family, Qwen (in paper) | Qwen3-14B, Gemma4-E4B-IT | Same | Same |
| Prompt dataset | HarmBench / custom harmful | Factorial dataset (A condition) | Factorial A vs harmless | Factorial A vs D |
| Token position | End of harmful prompt or start of response | Mixed (best layer) | startofthink / endofthink | startofthink / endofthink |
| Hidden-state convention | Residual stream post-attention | Same (residual stream) | Same | Same |
| Direction construction | Mean difference | Mean difference | Mean difference | Mean difference |
| Layer selection | Manual inspection or sweep | Best by AUC sweep | Same | Same |
| Evaluation | Steering experiment; refusal suppression | AUC on factorial dataset | AUC | AUC |
| Uses logistic regression | Sometimes (varies by paper) | No | No | No |
| Subspace dimension | 1 or small K | K=4 (subspace rank) | K=4 | K=4 |

---

## DVP > HVP Claim

From sprint summary: "DVP consistently beats HVP at every token position for both models."

**Verification:** Sprint §8 states "11 of 12 HVP/DVP variants achieve AUC ≥ 0.70 (all except Gemma dvp_endofresponse at 0.6403)."

The full comparison table is in sprint §8. The claim that DVP > HVP at every position is consistent with the reported summary in the sprint but the individual AUC values for HVP variants (other than hvp_startofthink for Gemma4=zero) are not all accessible from the top-level summary.json files in the current audit.

**Cannot fully verify "every token position" without reading all 12 subspace_stats summary files.**

---

## Signal Dissipation at endofresponse

Sprint reports: "endofresponse variant: Weak but finished; signal dissipates by EOS." This means AUC drops significantly at the endofresponse position for at least some variants. The full AUC table in sprint §8 (line 293ff) is the authoritative reference. The `dvp_endofresponse` for Gemma4 is listed as the only one below 0.70 (AUC=0.6403).

---

## Scientific Language Guidance

- DO say: "Our behavioral direction at L26 is **predictive** of attack outcome (AUC=0.75)"
- DO say: "We have not yet extracted the canonical refusal direction for these models"
- DO say: "Our directions are essentially orthogonal to each other (max abs cosine = 0.26)"
- DO NOT say: "We extracted the refusal direction"
- DO NOT say: "The refusal direction changed" or "shifted" for the puzzle condition
- DO NOT compare cross-model directions (different embedding spaces)
