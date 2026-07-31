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

## Caveat CLOSED — compliance-flip is concept-specific (cell-D controls, job 695111, n=40). **[NEXT2 #2]**
The pilot ran random/orthogonal controls only for cell B; the follow-up (`toctou_...695111`) added them to cell D. Result — **Dspec** (D-main MALICIOUS − D-control MALICIOUS, per timing):

| timing | vs concept_rand | vs concept_orth | D-main / D-rand rates |
|---|---|---|---|
| **early** | **+0.475** [+0.300,+0.650] | **+0.475** [+0.300,+0.650] | 0.525 / ~0.05 |
| mid | +0.225 [+0.050,+0.400] | +0.150 [−0.025,+0.325] | 0.35 / ~0.13 |
| late | +0.000 [−0.125,+0.125] | −0.025 [−0.150,+0.100] | 0.10 / ~0.10 |

So ablating refusal converts an **early-installed CONCEPT** to compliance (D/early 0.525), but a norm-matched **random** or **orthogonal** direction installed at the same early layers + the same refusal ablation does **not** (~0.05) — CI excludes 0 at early. **Both halves of the TOCTOU are now concept-specific**: refusal-trigger (B/early concept 0.82 vs random 0.00) and compliance-flip (D/early concept 0.525 vs random 0.05). Baselines A (none) and C (refusal-only, no concept) are 0.0. The main interaction is unperturbed (refusal_gain early +0.45, late +0.05). This closes the sole remaining S4 caveat.
- **Semantic vs behavioral dissociation:** the additive `d_Direct` moves the p_concept next-token readout only trivially (B4), yet behaviorally it triggers strong early refusal (0.82) and, under ablation, compliance (0.53). The behavioral generation integrates the small representational nudge over the whole completion. p_concept interaction is +0.0002 (tiny) — the effect lives in behavior, not the single-token semantic readout.
- **Single pair / single model / n=40**, one seed. Deterministic greedy decoding.
- Refusal ablation is partial (harmful refusal 1.0→0.53 at validation), so absolute compliance rates are conservative lower bounds.

## Generalization to other pairs — does NOT clearly replicate (honest negative). **[NEXT2 #6]**
Ran the same factorial (concept-agnostic L18 refusal dir + per-pair `d_Direct`, cell-D controls, n=40, 0 judge failures) on grenade + chlorine (`toctou_...695290/695291`):

| pair | INTERACTION (MALICIOUS) [CI] | refusal_gain early / mid / late | D_early MAL | verdict |
|---|---|---|---|---|
| **bomb** | **+0.425** [+0.25,+0.60] Holm-sig | +0.45 / +0.05 / +0.05 | 0.525 | depth-gated ✅ |
| grenade | −0.025 [−0.15,+0.10] NS | +0.00 / +0.15 / +0.03 | 0.075 | null (no early gating) |
| chlorine | +0.15 [−0.05,+0.33] NS | +0.175 / +0.175 / +0.03 | 0.275 | directionally like bomb but NOT significant; flat (not early-specific) |

**Honest conclusion:** the depth-gated-refusal TOCTOU is **strong and significant on bomb but does NOT clearly generalize** — grenade is null and chlorine is directionally consistent but underpowered/non-significant with a *flat* (not early-specific) refusal_gain. The likely cause: the *behavioral* effect requires the concept install to actually flip generation to harmful compliance, and the additive `d_Direct` install is weak and pair-dependent (B4/N4), with much lower base compliance for grenade/chlorine (D_early 0.075/0.275 vs bomb 0.525). This contrasts with the *representational* dissociation (§3.1), which generalizes 4/4 pairs (S5) because it measures the semantic reading, not behavioral compliance. **The TOCTOU depth-gating stands as a bomb-pair result**, pending a stronger/pair-robust concept-install lever or larger n to test generality.

## Significance
A **second new causal contribution**: beyond §3.1 (the reading is context-carried), this shows the *safety consequence* — on the CARROT↔BOMB pair the refusal mechanism is depth-gated, so deferring harmful semantics to later layers is a genuine TOCTOU bypass. Concept-specific (both refusal-trigger and compliance-flip), controlled, and significant on bomb; generalization to other pairs is **not** established (see above).
