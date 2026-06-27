# Research Master Claims Re-Audit

**Date:** 2026-06-25  
**Scope:** Every scientific claim in `RESEARCH_MASTER.md` audited against source data, scorer mechanics, and methodological corrections C1–C8.  
**Machine-readable version:** `outputs/audits/research_master_claims.csv`

---

## Summary Table

| # | Claim | Section | Current RM Status | Corrected Status |
|---|-------|---------|-------------------|-----------------|
| C01 | Qwen3 ASR=57.9% | 3.1 | Verified | Supported but limited |
| C02 | Gemma4 ASR=31.0% | 3.1 | Verified | Supported but limited |
| C03 | A−D: thinking causally required (Δ=+0.309) | 3.3 | Wording too strong | **Invalid — A and D both have thinking ON** |
| C04 | A−E: thinking required (Δ=+0.424, p=0.008) | 3.3 | Verified | Supported but limited |
| C05 | A−F: puzzle required (Δ=+0.429, p=0.008) | 3.3 | Verified | Supported but limited |
| C06 | Puzzle × Thinking interaction = +0.304 (superadditive) | 3.3 | Wording too strong | **Invalid — wrong formula, G condition missing** |
| C07 | Gemma4 A−D: puzzle clearly required | 3.3 | Preliminary | Preliminary |
| C08 | Two distinct mechanisms discovered | 3.4 | Wording too strong | **Preliminary — Gemma controls insufficient** |
| C09 | Gate C: RD hypothesis does not hold (0/160) | 3.5 | Wording too strong | **Invalid — known implementation mismatch** |
| C10 | Thinking annihilates refusal signal (7.5× drop) | 3.5 | Unresolved | Unresolved |
| C11 | EOI ⊥ behavioral (cosine=0.137) | 4.1 | Verified | Supported but limited |
| C12 | Gemma4 EOI aligned (cos=0.679) | 4.1 | Verified | Supported but limited |
| C13 | Sign flip = orthogonal bypass mechanism | 4.2 | Wording too strong | **Exploratory only — flip present in ALL classes** |
| C14 | Gemma4 no sign flip | 4.2 | Supported | Supported but limited |
| C15 | Dual pathway Qwen3 (both AUC>0.67) | 4.3 | Supported | Supported but limited |
| C16 | Trajectory diverges from first token | 4.4 | Wording too strong | **Preliminary — should say 'first analyzed 5% bin'** |
| C17 | Qwen3 LOGO AUC=0.757 | 4.5 | Supported | Supported but limited |
| C18 | Gemma4 LOGO AUC=0.806 | 4.5 | Supported | Supported but limited |
| C19 | P4: behavioral direction non-causal (n=11) | 5.1 | Supported | Supported but limited |
| C20 | P4b: rank-5 subspace non-causal (n=11) | 5.2 | Supported | Supported but limited |
| C21 | CoT confound ruled out (answer_only fails) | 5.2 | Wording too strong | **Unresolved — fixed-CoT test not done** |
| C22 | P7: Gemma4 direction non-causal (n=4) | 5.3 | Preliminary | Preliminary |
| C23 | 56× attention routing ratio | 6.2 | Wording too strong | **Exploratory only — invalid ratio (0-denominator in 95.9%)** |
| C24 | 4.1% of prompts have literal goal text | 6.4 | Verified | Established |
| C25 | Attention-routing hypothesis established | 6.5 | Wording too strong | **Exploratory only — rename section** |
| C26 | P5b: head ablation non-causal (n=2) | 7.3 | "Verified" | **Invalid — Run 1 all errors; Run 2 all timing-corrected** |
| C27 | P6: end-aligned patching non-causal (n=2) | 7.4 | "Verified" | **Invalid — two runs give opposite results** |
| C28 | P11: L10 is artifact | 7.5 | Partially valid | Supported — interpretation incomplete |
| C29 | P14: gen-phase injection non-causal (n=2) | 7.6 | "Verified" | Preliminary — timing-corrected results |
| C30 | P16: block ablation non-causal (n=2) | 7.7 | "Verified" | **Invalid — majority timing-corrected** |
| C31 | Mechanism is fully distributed | 9 | Wording too strong | **Unresolved — consistent with distributed/redundant** |
| C32 | Working Hypothesis: Prompt-Committed Distributed Routing | 9 | Exploratory | Exploratory only |

---

## By Evidence Level

### Established (1)
- **C24:** 4.1% of prompts have literal harmful goal text — directly measurable, robust.

### Supported but limited (10)
- C01, C02: ASR percentages (keyword scorer, not API judge)
- C04: A−E thinking effect (correct contrast, but G missing for full interaction)
- C05: A−F puzzle effect (F is length control, not the no-puzzle/no-thinking cell)
- C11, C12: Direction geometry (cosine similarities)
- C14: Gemma4 no sign flip
- C15: Dual pathway AUC values
- C17, C18: LOGO AUC (need fold-validity check)
- C19, C20: P4/P4b non-causal (most reliable intervention results — no timing correction, n=11/11)

### Preliminary (4)
- C07: Gemma4 A−D contrast (n=4, directional only)
- C16: Trajectory divergence (first 5% bin, not first token)
- C22: P7 Gemma4 direction non-causal (n=4)
- C29: P14 gen-phase patching (timing-corrected in Ex2)

### Exploratory only (4)
- C13: Sign flip (present in all mechanism classes, not specific to attack)
- C23: 56× attention ratio (invalid denominator)
- C25: Attention-routing hypothesis
- C32: Prompt-committed distributed routing hypothesis

### Unresolved (3)
- C10: Thinking annihilates refusal signal (under buggy implementation)
- C21: CoT confound (fixed-CoT test pending)
- C31: Mechanism is distributed (consistent with but not proven)

### Invalid (6)
- **C03:** A−D labeled as "thinking causally required" — both conditions have thinking ON
- **C06:** Puzzle × Thinking interaction +0.304 — wrong formula, G missing
- **C08:** Two mechanisms discovered — Gemma controls insufficient for confirmation
- **C09:** Gate C "hypothesis does not hold" — known 3-bug implementation mismatch
- **C26:** P5b NON-CAUSAL — Run 1 all errors, Run 2 all timing-corrected
- **C27:** P6 NON-CAUSAL — two runs give opposite results
- **C30:** P16 NON-CAUSAL — Example 2 all timing-corrected

---

## Detailed Notes on Invalid Claims

### C03 — A−D interpreted as "thinking causally required"

**Correction:** Both condition A and condition D have extended thinking enabled. A−D measures the **puzzle effect with thinking ON**, not whether thinking is required. Thinking requirement is measured by A−E (puzzle condition, thinking ON vs OFF) and D−G (bare harmful, thinking ON vs OFF). The table in Section 3.3 labels A−D as "Thinking causally required" — this is a labeling error in the analysis script and must be corrected in both the document and `analyze_factorial_attack_effects.py`.

### C06 — Interaction formula wrong

**Correction:** The current formula `(A-D) - (E-F)` uses F as the thinking-OFF/no-puzzle cell, which is not what F is (it is a length-matched benign control). The correct full factorial interaction is `(A-E) - (D-G)`. Condition G (bare harmful + thinking OFF) does not exist in the current dataset. The reported +0.304 figure cannot be interpreted as a factorial interaction.

### C09 — Gate C "does not hold"

**Three implementation bugs found in `replicate_standard_refusal_direction.py`:**

1. **Single-layer ablation vs all-layer (critical).** Arditi et al. apply ablation hooks to every layer of the model (input pre-hook + attn output hook + MLP output hook at every transformer block). The current code applies a single-layer hook at the candidate source layer only. This changes the intervention fundamentally: the paper removes the refusal direction globally from all activations; the current code removes it only locally.

2. **KL computation uses wrong hook type.** Upstream computes KL using the same all-layer ablation hooks. The current code computes KL using activation-addition hooks at a single layer. These test different things (fluency under global direction removal vs fluency under single-layer perturbation).

3. **Steering coefficient mismatch.** Upstream uses `coeff=1.0` for the steering (refusal-induction) filter. The current code uses `steer_alpha=20.0`.

These bugs make the current 0/160 result uninformative — it reflects a different intervention than the paper's, not a replication of it.

### C26 — P5b head ablation

**Run 1 (050502):** All ablation conditions have elapsed_s ≈ 0.0–0.2s. The exception handler in `run_head_ablation.py:325` silently catches errors and sets `sr_success=True`. These are errors masquerading as successful attacks. The "NON-CAUSAL" result from this run has zero validity.

**Run 2 (054202):** Example 2 has ALL six conditions with elapsed_s ≈ 800–827s and `sr_success=False`. Every label for example 2 is timing-corrected. The claim that ablating any/all L10 heads is NON-CAUSAL rests entirely on whether these 800s generations are genuine compliance or long refusals/truncated outputs. This cannot be resolved without re-running and storing full generation text.

### C27 — P6 causal tracing

**The two smoke runs give contradictory results:**

- Run 1 (040234): L3 and L10 patching produces `sr_success=False` (short, refusal-like elapsed times of 30–34s). Only L26 maintains the attack. This would suggest L3 and L10 **ARE** causally relevant — the opposite of the claimed conclusion.
- Run 2 (050647): All patches succeed (elapsed ≈ 570–800s). Example 2 all timing-corrected.

The analysis report (Section 7.4) cites only Run 2 and reaches a NON-CAUSAL conclusion. Run 1's contradictory result is not mentioned. The correct conclusion is: **results are contradictory between runs; no conclusion about causal relevance of L3/L10 is warranted at n=2 with these scorer issues**.

### C30 — P16 block ablation

Example 2: all five conditions (baseline, zero_attn_L10, zero_mlp_L10, zero_attn_L26, zero_mlp_L26) have elapsed ≈ 800–810s and `sr_success=False`. Every label for example 2 is timing-corrected. Without timing correction, Ex2 ASR = 0/4 ablation conditions. The claim of NON-CAUSAL for zeroing entire sublayers cannot be established from these data.

---

## Required Actions Per Claim

| Action | Claims Affected |
|--------|----------------|
| Fix A−D label to "puzzle effect (thinking ON)" | C03 |
| Add G condition, recompute interaction | C06 |
| Change Gate C to UNRESOLVED REPLICATION DISCREPANCY | C09 |
| Rename sign-flip to exploratory; add matched comparison | C13 |
| Fix "from first token" → "from first 5% bin" | C16 |
| Verify LOGO folds have both classes | C17, C18 |
| Add fixed-CoT test pending note | C21 |
| Rename 56× ratio section; remove as routing evidence | C23 |
| Rename attention-routing to exploratory P5a | C25 |
| Mark P5b as INVALID, describe errors | C26 |
| Mark P6 as CONTRADICTORY RUNS, no conclusion | C27 |
| Mark P16 as INVALID/PENDING RESCORE | C30 |
| Replace "fully distributed" with "consistent with distributed/redundant" | C31 |
| Demote working hypothesis to exploratory | C32 |
