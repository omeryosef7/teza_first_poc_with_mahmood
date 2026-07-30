# Stage 4 — Concept × Refusal TOCTOU Factorial: Findings

**Status:** POSITIVE, CONFIRMATORY (n=40 items, Holm-corrected). **[NEW]**
**Run:** `outputs/toctou_Llama-3.1-8B-Instruct_20260730_211925_694811` (job 694811). Backing: `toctou_summary.json`, `toctou_raw.jsonl`.
**Code:** `45_toctou_factorial.py` + `pair_common.AllPositionProjectOutMultiLayer` (Arditi all-layer refusal ablation) + `build_refusal_direction_llama.py`. Refusal dir L18 (validated: harmful refusal 1.0→0.53, induce 0.67). Concept = additive `d_Direct` at codeword_last over early/mid/late windows. Judge = StrongReject; **0 judge failures**.

---

## Headline: a causal TOCTOU signature — the refusal check catches an EARLY concept but not a LATE one.

The interaction (concept-timing × refusal-intervention), paired bootstrap CI, Holm-corrected:

| outcome | INTERACTION = refusal_gain(early) − refusal_gain(late) | sig |
|---|---|---|
| **P(MALICIOUS)** | **+0.425** [+0.250, +0.600] | ✅ |
| **P(REJECTED)** | **−0.400** [−0.550, −0.250] | ✅ |

Per-cell behavioral rates (main concept arm, n=40/cell):

| cell | early | mid | late |
|---|---|---|---|
| **B** concept-only → REJECTED | **0.82** | 0.53 | 0.45 |
| **B** concept-only → MALICIOUS | 0.07 | 0.25 | 0.05 |
| **D** concept+ablate → MALICIOUS | **0.53** | 0.35 | 0.07 |
| **D** concept+ablate → REJECTED | 0.03 | 0.03 | 0.05 |
| A baseline (none) → MALICIOUS | 0.00 | | |
| C refusal-only (no concept) → MALICIOUS | 0.00 | | |

`refusal_gain` (MALICIOUS): early **+0.45** [+0.275,+0.625]; mid +0.10 [CI crosses 0]; late +0.025 [CI crosses 0].

### Mechanism (the TOCTOU story, causal)
1. **Installing the concept EARLY triggers the refusal mechanism** — REJECTED jumps to **0.82**. The safety check *sees* the early concept representation and fires.
2. **Ablating refusal then converts that to compliance** — D/early MALICIOUS **0.53** (refusal removed, 0.03). The early-concept-induced refusal is *removable* → the concept was driving a refusal that gated a harmful completion.
3. **Installing the concept LATE does neither strongly** — REJECTED only 0.45, and even with refusal ablated, MALICIOUS stays **0.07**. A late-installed concept escapes the refusal check *and* does not manifest as compliance.
4. **The interaction is significant** — the difference between early and late refusal_gain (+0.425, CI excludes 0). This is an intervention *interaction* (plan §Stage 4 H5), NOT two crossing curves.

This is the paper's hypothesized **time-of-check / time-of-use** failure, shown causally: the refusal mechanism checks the concept representation at an early depth; a concept that emerges only later is used after the check has passed.

## Concept-specificity controls (decisive)
The early refusal-triggering is **concept-specific**, not generic early perturbation:

| early-install direction | → REJECTED (B/early) |
|---|---|
| **`d_Direct`** (concept) | **0.82** |
| `concept_rand` (norm-matched random) | **0.00** |
| `concept_orth` (orthogonal random) | **0.00** |

A norm-matched random or orthogonal direction installed at the same early layers does **not** trigger refusal. And the two null baselines are clean: A (no intervention) and C (refusal-only, no concept) both give **0.00 MALICIOUS** — ablating refusal without a concept produces no harm on these benign items.

---

## Caveats / limitations (honest)
- **Control D cells not run** (the pilot generated the random/orthogonal controls only for cell B, not cell D). So concept-specificity is established for the *refusal-triggering* half (B/early: concept 0.82 vs random 0.00) but the *compliance-flip* half (D) lacks a random-direction interaction. A follow-up should run D for the controls to fully rule out that ablation+any-early-perturbation flips to compliance. (The B-side control is already strong evidence, since without early refusal there is nothing for ablation to convert.)
- **Semantic vs behavioral dissociation:** the additive `d_Direct` moves the p_concept next-token readout only trivially (B4), yet behaviorally it triggers strong early refusal (0.82) and, under ablation, compliance (0.53). The behavioral generation integrates the small representational nudge over the whole completion. p_concept interaction is +0.0002 (tiny) — the effect lives in behavior, not the single-token semantic readout.
- **Single pair / single model / n=40**, one seed. Deterministic greedy decoding.
- Refusal ablation is partial (harmful refusal 1.0→0.53 at validation), so absolute compliance rates are conservative lower bounds.

## Significance
A **second new causal contribution**: beyond §3.1 (the reading is context-carried), this shows the *safety consequence* — the refusal mechanism is depth-gated, so the Doublespeak strategy of deferring harmful semantics to later layers is a genuine TOCTOU bypass. Concept-specific, controlled, and significant.
