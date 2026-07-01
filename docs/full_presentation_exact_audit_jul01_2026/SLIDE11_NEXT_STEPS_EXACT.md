# SLIDE 11 — Exact Audit: Next Steps

**Audit date:** 2026-07-01  
**Source:** SPRINT_SUMMARY_JUN14_30.md (§12, Priority Order), MAHMOOD_ANALYSIS_ONLY_BRIEF_JUN30.md (§Next Steps)

---

## Priority-Ordered Next Steps (from SPRINT_SUMMARY §12)

The sprint summary lists the following priority order for the next sprint:

### P1 (Critical / Blocks Conclusions)

**P1a — Failure text capture:** Re-run Condition A for both models with `store_text=True` to capture thinking + final output for ALL rows (not just successes). Currently 51.3% of Qwen3 failures and 58.4% of Gemma4 failures are metadata-only (no text). This blocks understanding WHY the puzzle attack fails.

**P1b — Gemma4 causal validation:** Run Stage 4A1 + 4A2 for Gemma4-E4B-IT. Currently 0/160 causal candidates are from the DVP/HVP/Behavioral direction families for BOTH models, but the Gemma4-specific validation used a different pipeline. The sprint notes that the 0/160 result needs explicit per-model accounting.

**P1c — StrongREJECT API access:** The SR API calls in the intervention experiments (P11/P14/P16) use the `sr_api_binary` field from external API calls. Some annotations are pending. The `sr_success` field is a placeholder (all=True) and cannot be trusted. Full SR scoring with live API access is required to finalize the intervention result tables.

### P2 (High Priority / Strengthens Claims)

**P2a — Scale up CoT causal role:** Currently N=8 per condition. Need minimum N=50 per condition for any statistical inference. Expand to all 11 goals (not just 4 goals used in pilot).

**P2b — Gemma4 P11/P14/P16:** All three intervention experiments are currently Qwen3-only. Replicate for Gemma4.

**P2c — L26-specific causal analysis:** Fit a mechanistic model explaining WHY L26 attention is the most suppressive ablation point. Options: residual stream probing at L26, attention head attribution at L26, comparison to other "refusal-relevant" layers in the mechanistic interpretability literature.

### P3 (Medium Priority / Generalizes Results)

**P3a — Additional harmful goals:** Current factorial dataset uses 11 goals. Expand to the full HarmBench benchmark (100+ goals) to test generalization.

**P3b — Third model:** Add a third model (e.g., Llama-3.1-8B or another instruction-tuned model) to test whether the L26 behavioral direction is model-specific or architecture-general.

**P3c — Canonical refusal direction comparison:** Extract the canonical refusal direction for Qwen3-14B and Gemma4-E4B-IT using the Zou/Arditi protocol, then compute cosine similarity to our behavioral direction. This is required to make any claim about relationship to the known refusal direction.

### P4 (Nice-to-Have)

**P4a — Selectivity pilot expansion:** N=9 per selectivity condition is too small for inference. Expand the P11 selectivity experiment to N=50+.

**P4b — seed sensitivity analysis:** Current results use multiple seeds but no formal seed sensitivity analysis. Bootstrap seed variation to estimate variance of ASR estimates.

---

## What the Presentation Should Say About Next Steps

**Safe to claim:**
- We need full failure text capture for Condition A before failure analysis is complete
- CoT causal role experiment needs scale-up (N=8 → N≥50 per condition)
- Gemma4 causal validation (Stage 4A2) is still pending
- Canonical refusal direction comparison has not yet been done

**Do NOT claim:**
- That any specific timeline is committed (no SLURM jobs have been submitted for Sprint 2)
- That P2c is "almost done" — there is no evidence L26 analysis is in progress

---

## Artifacts Needed for Next Sprint (not present in current repo)

1. Condition A with full text storage for failures (currently absent for most rows)
2. Stage 4A2 results for Gemma4 specifically (current 0/160 applies to which model?)
3. SR API key with access restored for re-scoring
4. CoT causal role runs for goals beyond the 4 used in pilot
5. P11/P14/P16 runs for Gemma4-E4B-IT
