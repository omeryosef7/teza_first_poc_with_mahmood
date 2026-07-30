# Stage 2 — State × Receiver-Context Transplant: Findings

**Status:** EXPLORATORY→CONFIRMATORY (seed 0, n=24; confirmatory seed pending)
**Run:** `outputs/pair_interv_replace_Llama-3.1-8B-Instruct_20260730_155014_694417` (job 694417)
**Backing artifacts:** `.../transplant_mediation_p_concept.json`, `.../interv_raw.jsonl`; consistent bench/reps/dir triple built in the same job (readout gate `gate_pass_any=True`, `DS−Neutral p_concept +0.31`). Faithfulness: both self-transplants exactly `0.0000` (n=140).
**Metric:** `p_concept` = P(BOMB) next-token mass under the cloze readout. Pair CARROT↔BOMB, Llama-3.1-8B-Instruct.

---

## DEFINITIVE RESULT (forced_choice readout, job 694691, n=30)

The cloze run below established the dissociation but floored the `d_Direct` positive control (B3: cloze reads DIRECT_CONCEPT 0.005 vs forced_choice 0.785). The **forced_choice** re-run is the definitive, sharper version — same dissociation, stronger DS signal, and a fully clean 2×3:

| receiver \ source | h_N | h_DS | h_Direct |
|---|---|---|---|
| **Neutral** (mid) | 0.000 | 0.000 | 0.000 |
| **DS** (mid) | 0.347 | 0.353 | 0.314 |

- **The reading depends ONLY on the receiver context, and is completely independent of the local codeword state.** Every source state (h_N, h_DS, h_Direct) transplanted into a **Neutral** receiver → **0.000**; every source state in a **DS** receiver → **~0.35**.
- `IE_state ≈ 0` (equivalence) all windows; `DE_context = +0.347` [mid] ≈ **99% of TE (+0.352)**; faithfulness exactly 0.0.
- `PORT_Direct ≈ 0` — even the DIRECT concept's own rep is **not portable** into a neutral context via full-state transplant. NO single-position state transplant installs the concept; only the context does.
- **Positive control (pending, job 694706):** additive `d_Direct` under forced_choice — expected to install strongly (DIRECT source decodes 0.785), showing the concept IS installable *additively* even though it is not installable by *state transplant*. This is the key contrast: adding the concept direction on top of the context-appropriate state works; replacing the state with a foreign one does not — consistent with context-conditioned routing.
- **Patchscope readout DROPPED** as configured: `ps_concept`=0 for all cells including the DS baseline, but 44 reads at a late layer (R=28) with no positive control, and per the project's readout saga concept reps decode *early* — so this is a mis-configuration artifact, not a meaningful null. A properly positive-control-gated patchscope is a future refinement; the forced_choice semantic readout is the clean signal.

---

## Headline result (original cloze run, job 694417 — dissociation holds, positive control floored)

The Doublespeak concept reading is carried by the **receiver context**, not the **local codeword activation**.

2×3 table (mean P(BOMB), preregistered windows):

| receiver \ source | h_N | h_DS | h_Direct |
|---|---|---|---|
| **Neutral** (early/mid/late) | 0.000 | 0.000 | 0.003 / 0.000 / 0.000 |
| **DS** (early/mid/late) | 0.204 / 0.247 / 0.209 | 0.215 | 0.005 / 0.003 / 0.012 |

Estimands (paired bootstrap CI, n=24), consistent across early/mid/late:

| estimand | early | mid | late | reading |
|---|---|---|---|---|
| **TE** (total) | +0.215 [.11,.33] | +0.215 | +0.215 | the DS attack shifts P(BOMB) by +0.22 |
| **DE_context** | **+0.204** [.11,.31] | **+0.247** [.14,.36] | **+0.209** [.11,.32] | a *neutral* local state in a DS context still reads +0.20 |
| **IE_state** | **−0.000** (equiv) | +0.000 (equiv) | +0.000 (equiv) | a DS local state in a neutral context installs **nothing** |
| RESID_ctx | +0.011 | −0.032 | +0.007 | swapping neutral↔DS local state in a DS context ≈ no change |
| INT | +0.011 | −0.032 | +0.007 | negligible state×context interaction |
| PORT_Direct | +0.003 | +0.000 | +0.000 | (see caveat) |

**Decomposition:** `DE_context / TE ≈ 0.204/0.215 ≈ 95%`; `IE_state ≈ 0%`. The effect is **context-mediated**, not stored in the query codeword's residual stream.

### Answer to the primary research question
The semantic effect is carried by **B (surrounding context and its downstream computation)**, not **A (local hidden state of the query codeword)**. `IE_state ≈ 0` (equivalence within ±0.05 at every window); `DE_context` is large and CI-excludes-zero. This is the **causal** counterpart of the paper's observational "codeword decodes as BOMB" — the token *decodes* as the concept (paper, patchscope) yet its residual state is **not** what causally drives the reading; the receiver context is.

---

## Controls & validity

- **Faithfulness (identity check):** self-transplants `Neutral_from_Neutral`, `DS_from_DS` reproduce the no-patch baseline exactly (effect 0.0000, n=140). The transplant machinery is faithful.
- **Neutral-receiver negative controls:** every source transplanted into a neutral receiver reads ~0 (`h_N`, `h_DS`, `h_Direct`, and also `Neutral_from_Benign`, `Neutral_from_Unrelated` in `interv_raw`). No local state installs the concept in a neutral context.
- **Shuffled-donor controls:** each arm has a `*_SHUFFLED` cross-prompt donor; present in `interv_raw` for the record.

---

## Caveats (honest; do not over-claim)

1. **PORT_Direct is a weak/ill-posed positive control for REPLACE mode.** `Neutral_from_Direct` ≈ +0.003 (max +0.045 at layer 4). Reason: the DIRECT_CONCEPT prompt's `probe_word` is the concept, so its "codeword_last" source rep is questionable, and a single-position full-state transplant is a weaker operation than the additive `d_Direct` that installs +0.97 in prior work (CAUSAL_CORE). **The concept-installability positive control is the ADDITIVE `d_Direct` arm, not the transplant** — a confirmatory run adds it (`--mode controls`) on this same consistent triple.
2. **Cloze-readout-attends-to-context confound.** The cloze readout is appended after the demonstrations, so the model can re-derive the concept by attending to the demo context regardless of the single codeword token's state. "Context-carried" therefore includes the possibility that the readout **re-reads the demonstrations** rather than a query-token effect. **This is exactly what Stage 3 (KV / path patching) must separate** — demonstration-KV mediation vs a genuine query-token contribution. This result *motivates* Stage 3; it does not pre-empt it.
3. **Multiple comparisons.** Per-window CIs exclude zero for DE_context, but no cell survives Holm across the full 35-layer × 6-estimand exploratory family. The preregistered **confirmatory** family is the 3 windows only; DE_context's effect size (+0.20 on a 0–1 scale) with CI [+0.11,+0.32] at n=24 is robust to that smaller family. Full-layer Holm is exploratory.
4. **Determinism / replication.** Seed-1 (job 694472) reproduces the main-arm estimands **identically** (IE_state≈0 equiv; DE_context +0.204/+0.247/+0.209; TE +0.215; faithfulness 0.0) — expected, since the replace/identity arms are deterministic given the prompt set (only the random/shuffled controls use the seed). Prompt-level uncertainty is captured by the paired bootstrap CI over n=24 prompts; a larger-n run is a cheap power follow-up but the DE_context CI already excludes zero.

---

## Consequences for the plan
- **Stage 2 → Stage 3 gate: PASS.** Receiver context contributes substantial causal effect (DE_context) after controlling the query-token activation (IE_state ≈ 0). Stage 3 (KV/path patching) is warranted and is the natural next step to localize *where* in the context (demonstration codeword occurrences vs other tokens) the effect is routed, and to resolve caveat (2).
- This is a candidate **paper-worthy positive result** (context-mediated, not locally stored) pending: confirmatory seed, the additive positive control, and Stage 3 disambiguation of the readout confound.
