# Doublespeak Causality — Paper-Contribution Draft

**Paper:** *In-Context Representation Hijacking* / Doublespeak (arXiv:2512.03771).
**Sprint:** NEXT_CAUSAL_SPRINT. **Model:** Llama-3.1-8B-Instruct. **Pair:** CARROT ↔ BOMB.
**Status:** DRAFT — S0/S2/S3/B4 complete & artifact-backed; S4 (TOCTOU) pilot pending.
Every quantitative sentence points to a committed backing artifact. Labels: CONFIRMATORY · NEW · NEGATIVE · LIMITATION.

---

## 1. Original-paper claims (what Doublespeak established)
Observational / decoding evidence that under a Doublespeak in-context prompt a benign codeword (CARROT) becomes **decodable** as a harmful concept (BOMB) in later layers — via Logit Lens and Patchscopes (§3.2–3.3) — plus behavioral attack evaluations and two *hypothesized* mechanisms (TOCTOU; semantic superposition, §3.4). The paper does **not** intervene inside the attacked computation to show the Doublespeak representation is necessary or sufficient for the outcome.

## 2. Our reproduced findings (CONFIRMATORY)
- The Doublespeak attack produces a real, moderate concept reading on the fixed pair: DS−Neutral p_concept **+0.31** (readout gate, `pair_readout_...694417/readout_summary.json`), with NEUTRAL clean at 0.000 across readouts.
- The `d_Direct` / `d_DS` **direction** framing from prior in-house work holds qualitatively: `d_DS` (observational Doublespeak difference vector) is causally inert; see §3.

## 3. Our NEW causal findings (the contribution)

### 3.1 The hijacked reading is carried by receiver CONTEXT, not the local codeword state — a causal transplant dissociation. **[NEW]**
State × receiver-context transplant (forced_choice, n=30; `pair_interv_replace_...694691/transplant_mediation_p_concept.json`; code `34_intervention_sweep.py::run_replace` + `43_transplant_mediation.py`):

| receiver \ source | h_N | h_DS | h_Direct |
|---|---|---|---|
| **Neutral** | 0.000 | 0.000 | 0.000 |
| **DS** | 0.347 | 0.353 | 0.314 |

- `IE_state ≈ 0` (equivalence within ±0.05, every layer window): the DS codeword's **local hidden state carries nothing** into a neutral context.
- `DE_context = +0.347` [+0.261,+0.434] ≈ **99% of TE (+0.352)**: a *neutral* codeword state in a DS context still reads the concept.
- **No source state installs the reading in a neutral context** (h_N/h_DS/h_Direct all 0.000); **every source state reads ~0.35 in a DS context.** The reading is a function of the receiver context and is **causally independent of the local codeword activation.**
- Validity: self-transplant faithfulness is **exactly 0.0** (n=140) — the transplant machinery is faithful (`43` faithfulness block; `tests/test_transplant_mediation.py`).

**Significance vs the paper:** this is the *causal* counterpart to the paper's observational "codeword decodes as BOMB." The token *decodes* as the concept, yet its residual state is **not** what causally drives the behavior — the surrounding context's downstream computation is. This directly adjudicates the paper's open causal question (their evidence is decoding-only).

**Generalization (§S5, `STAGE5_GENERALIZATION.md`):** the dissociation replicates on **4/4 pairs** across explosive/weapon/chemical harm categories (bomb, grenade, pistol, chlorine): `IE_state ≈ 0` (equivalence) and `DE_context` CI-excludes-0 (range +0.16 to +0.47, ≈95–99% of TE) on every pair. Absolute hijack strength is pair-dependent (pistol weakest at 0.16); the *structural* dissociation is universal. → a general property of Doublespeak on Llama-3.1-8B, not of CARROT↔BOMB.

**Depth-invariance (N1/N2, `NEXT2_FINDINGS.md`):** the dissociation holds at **every depth** — single-layer state replacement is inert at all 32 layers (|IE_state| < 0.0002 everywhere, 4/4 pairs) and `DE_context` is flat across depth; even multi-layer (11-layer-window) replacement is inert (N2). The codeword's local state is causally irrelevant at all depths; the context re-supplies the reading continuously.

### 3.2 The effect is NOT a trivial demonstration re-read, and is distributed. **[NEW]**
Demonstration-K/V mediation (forced_choice, n=30; `pair_kv_mediation_...694691/kv_mediation_summary.json`; new `pair_common.DemoStateSwap` + `44_kv_mediation.py`):
- **`ReRead_test` (C1−C3) is small** (mid +0.032 of a 0.35 baseline → **~91% of the reading survives** neutralizing the demonstration codeword K/V). If the readout merely re-read the demonstrations, neutralizing them would collapse it. It does not.
- The demonstration-codeword K/V carries a **small, codeword-specific** slice (mid ReRead > random control), but the bulk is **distributed / robust** — Stage-3 outcome **C (distributed computation)**, reported honestly.
- Validity: `DemoStateSwap` self-swap reproduces the no-hook baseline **exactly** on the real model (n=30); 8 CPU tests + independent adversarial review.

### 3.3 A causal TOCTOU signature: the refusal check catches an EARLY concept but a LATE one escapes it. **[NEW]**
Concept × refusal factorial (n=40; `toctou_...694811/toctou_summary.json`; `45_toctou_factorial.py` + multi-layer refusal ablation, `STAGE4_TOCTOU_FINDINGS.md`; StrongReject, 0 judge failures):
- **Installing the concept early triggers refusal** (REJECTED 0.82) **concept-specifically** — norm-matched random and orthogonal directions give 0.00; baseline and refusal-only give 0.00 malicious.
- **Ablating refusal then flips early-concept to compliance** (MALICIOUS 0.53), but **a late-installed concept yields no compliance even with refusal removed** (0.07).
- **Interaction (early−late refusal_gain) = +0.425** [+0.250, +0.600] for MALICIOUS (Holm-sig); −0.400 for REJECTED. An intervention *interaction* (not crossing curves), meeting plan §Stage-4 H5.

**Significance:** the refusal mechanism is **depth-gated** — it checks the concept representation at an early depth, so Doublespeak's deferral of harmful semantics to later layers is a genuine **time-of-check/time-of-use** bypass. This is the causal test of the paper's §3.4 TOCTOU hypothesis. **Both halves are concept-specific** (NEXT2 #2: refusal-trigger B/early concept 0.82 vs random 0.00; compliance-flip Dspec early +0.475). **Scope:** demonstrated on CARROT↔BOMB; it does **not** clearly generalize to grenade (null) or chlorine (directional, NS) — the behavioral effect needs a strong concept install (weak/pair-dependent `d_Direct`), unlike the representational §3.1 dissociation which is 4/4. Reported honestly in `STAGE4_TOCTOU_FINDINGS.md`.

## 4. Our NEGATIVE / integrity findings (equally load-bearing)

### 4.1 `d_Direct` "installs the concept +0.971" does NOT reproduce. **[NEGATIVE / integrity]** (`BUG_AND_DEVIATION_LOG.md` B4)
On a fresh, consistent, byte-identical-bench pipeline, additive `d_Direct` install is **+0.03** (p_concept) / label-flip max **0.27**, NOT the standing CAUSAL_CORE **+0.971**. This is **not a regression** — the current code reproduces the on-disk CAUSAL_CORE artifact (`pair_causal_analysis_one_word_693571.json` = +0.028). The +0.971 is unbacked on disk (doc-vs-artifact drift). **This strengthens §3.1:** on the reproducible pipeline, **no** local codeword intervention — full-state transplant *or* additive direction — installs the concept in a neutral context; only the context does.

### 4.2 Stage-0 integrity repairs of prior in-house pipeline. **[integrity]** (`STAGE0_INTEGRITY_REPORT.md`)
10 defects (C1–C10) fixed with tests + independent review (no conclusion-inverting bug): patch-sweep readout contamination (C1/C3), aggregation manufacturing a null from missing cells (C2), empty-generation miscounting (C8), judge-health/partition (C7), held-out-concept axis leakage (C9), knockout controls (C5/C6), etc.

### 4.3 TOCTOU — see §3.3 (a POSITIVE result). The compliance-flip specificity caveat is now CLOSED (NEXT2 #2, job 695111): cell-D random/orthogonal controls give Dspec early +0.475 [+0.30,+0.65] (D-main 0.525 vs controls ~0.05) — so both the refusal-trigger AND the compliance-flip are concept-specific. Honesty note retained: the semantic next-token p_concept install is weak (B4/N4) yet the *behavioral* interaction is strong and concept-specific.

## 5. Limitations
- **Modest absolute magnitudes** (DS reading ~0.35; `d_Direct` install ~0.03). The dissociation is *relative* and robust (context +0.35 vs local-state 0), but effect sizes are small.
- **Single pair / single model** for the primary causal claims (CARROT↔BOMB, Llama-3.1-8B). Generalization (Stage 5) deferred.
- **Patchscope confound-free readout unusable as configured** (reads a late layer with no positive control; concept reps decode early) — dropped from claims; the forced_choice semantic readout carries the signal.
- **cloze readout floors the positive control** (DIRECT 0.005 vs forced_choice 0.785, B3) — resolved by using forced_choice; a caution for anyone reading the cloze-era numbers.
- **Patchscope cross-check not achievable for bomb** (N3): a layer-scanned, positive-control-gated patchscope fails its positive control (a clean DIRECT bomb rep does not decode via the repeat-prompt decoder; pos_ctrl_max 0.0003) — so we neither replicate nor refute the paper's patchscope decoding on this pair. The forced_choice next-token readout is load-bearing. A pair-tuned inspection prompt is future work.
- **`d_Direct` install is small and non-monotone** (N4: peaks ~0.11 at α=4, drops at α=8) — the transplant conclusion (§3.1) does NOT depend on it (validity = faithfulness + `DE_context`), but `d_Direct` is not a strong positive control.
- **Cross-architecture untested** (§5-cross-arch): Qwen3-14B's readout gate fails because it is a thinking model (the next-token readout fires inside `<think>`); a thinking-aware readout (`enable_thinking=False`) is needed. Gemma-4 not available. Primary claims are Llama-3.1-8B only.
- **TOCTOU (§3.3) does not clearly generalize** beyond bomb (grenade null, chlorine NS) — behavioral compliance requires a strong concept install. The representational dissociation (§3.1) does generalize 4/4.

## 6. Paper-worthiness
Two defensible **NEW causal contributions** to the paper's observational story:
1. **§3.1 transplant dissociation** — *the hijacked meaning is not stored in the target token's residual state; it is a property of the receiver context's computation* (IE_state ≈ 0 equiv; DE_context +0.35 ≈ 99% of the effect; exact faithfulness; clean neutral baseline), with a mechanistically-informative follow-up (§3.2: not a demo re-read, distributed).
2. **§3.3 causal TOCTOU** — *the refusal mechanism is depth-gated; an early-installed concept is caught (concept-specifically) while a late one escapes* (interaction +0.425, Holm-sig, controlled). This is the causal test of the paper's §3.4 TOCTOU hypothesis.

Plus a load-bearing **integrity negative** (§4.1: the in-house +0.971 `d_Direct` install does not reproduce). Remaining to strengthen for publication: generalization across pairs/models (Stage 5), control-D cells for §3.3, larger n/seeds, and a positive-control-gated patchscope readout.
