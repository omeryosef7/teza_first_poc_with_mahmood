# NEXT2 — Follow-up Findings (extending the causal sprint)

Continuation of `HANDOFF.md` / `PAPER_CONTRIBUTION.md`. New low-cost experiments + techniques.

---

## N1 — The context-carried dissociation is DEPTH-INVARIANT. **[NEW, CPU-free, from existing data]**
Re-analysis of the per-layer transplant estimands already in `pair_interv_replace_*{694691,694895,694896,694897}/transplant_mediation_p_concept.json` (the runs swept `--layer-groups single` = all 32 layers).

| pair | DE_context across L0–L31 (min..max, mean) | IE_state \|max\| over all 32 layers |
|---|---|---|
| bomb | +0.334 .. +0.363 (mean +0.351) | **0.00005** |
| grenade | +0.462 .. +0.506 (mean +0.489) | **0.00009** |
| pistol | +0.149 .. +0.170 (mean +0.163) | **0.00020** |
| chlorine | +0.381 .. +0.401 (mean +0.391) | **0.00010** |

**Result:** replacing the query codeword's residual state at *any single layer* with a neutral state is causally **inert at every one of the 32 layers** (|IE_state| < 0.0002 everywhere, all 4 pairs), and the context effect (`DE_context`) is present and **flat across depth** — no layer where the local state starts to matter.

**Interpretation:** the codeword's meaning is not localized at any depth of its own residual stream; the receiver context **continuously re-supplies** it, so knocking out any single layer's local state is immediately compensated downstream. This refines §3.1 from "context-carried" to "context-carried **at every depth**," and motivates N2 (does *cumulative* multi-layer replacement ever install?).

Backing: `outputs/pair_interv_replace_*/transplant_mediation_p_concept.json` (estimand keys `IE_state|layer{0..31}`, `DE_context|layer{0..31}`).

---

### N1 overlay — where the reading LIVES vs where the refusal CHECK acts (free, unifies S2/S3/S4)
Contrast, from data already on disk:
- **Concept reading (transplant, N1):** depth-INVARIANT — the codeword's local state is inert at every layer (IE_state|max| < 0.0002, L0–31), context re-supplies the reading at all depths (DE_context flat).
- **Refusal check (TOCTOU, S4, `toctou_...694811`):** depth-GATED — additive concept install triggers *ablatable* refusal only when done EARLY: `refusal_gain` (MALICIOUS) = early **+0.45**, mid +0.10 (CI crosses 0), late +0.025 (CI crosses 0).

**Unifying interpretation:** the hijacked *meaning* is a distributed, context-supplied property present at every depth, but the *safety mechanism* that would block it acts only at an early depth. Doublespeak wins by keeping the codeword benign through that early check while the concept is (re)constructed from context at every subsequent depth — a clean statement of the time-of-check (early, fixed depth) / time-of-use (all depths, context-supplied) split. This links S2 (context-carried), N1 (at every depth), and S4 (depth-gated refusal) into one picture, using no new compute.

---

## N2 — MULTI-LAYER state replacement is also inert (free, from existing window arms)
`run_replace` already emits *window* arms that replace the codeword state at ~11 layers (an early/mid/late third) **simultaneously**. Bomb 694691: `IE_state` at the early/mid/late windows = −5e-05 / −3e-05 / +1e-05 (all equivalence ✅). So injecting the DS codeword state into a Neutral receiver installs nothing even when done across a *third of the network at once* — not just single layers (N1). Combined with N1, no local intervention (single- or multi-layer state replacement, or additive d_Direct, B4) installs the concept in a neutral context; only the receiver context does. (An all-32-layers-at-once variant is a cheap optional confirmatory but is near-certain to agree given both single-layer and 11-layer-window replacements are inert.)

---

## N3 — Patchscope readout: gated and CONFIRMED UNUSABLE for bomb (not a misconfiguration). **[honest negative]**
#3 rescue (job 695115): the layer-scanned, positive-control-gated patchscope (reuse of `07.PatchscopeDecoder` + gate) was run on the forced_choice bomb transplant/KV cells. **The positive control FAILS: `pos_ctrl_max = 0.00025` (< 0.1), `positive_control_ok = False`** even after scanning all layers (best layer 25). So a *clean DIRECT bomb rep* does not decode as "bomb" through the repeat-inspection decoder (which the registry notes passes for "virus" at 0.67–0.72 — the decoder is word/pair-specific). Consequently every `ps_concept_gated ≈ 0` (C1/C2/C3), and it would be wrong to read anything into it.
- **Correct conclusion:** the patchscope cross-check is **not achievable for this pair with this decoder** — the gate flags it unusable for a *principled* reason, not a late-layer misconfig. We therefore neither replicate nor refute the paper's "CARROT→BOMB via Patchscopes" on bomb; the **forced_choice next-token semantic readout remains the load-bearing signal** for all S2/S3/N1/N2 results. (A pair-tuned or vendored inspection prompt that passes the bomb positive control is future work; not low-hanging.)

## N4 — d_Direct dose curve: small, concept-specific, NON-monotone. **[reframes B4 honestly]**
#7 (job 695117, forced_choice, α∈{1,2,4,8}): best-layer additive `d_Direct` install (mean p_concept): α1 ≈ 0.001, α2 ≈ 0.003, α4 ≈ **0.114** (L4), α8 ≈ 0.048 (L20) — **peaks ~0.11 at α=4 then DROPS at α=8** (over-steering degrades it). So `d_Direct` is a *small, concept-specific* effect (it exceeds matched controls, B2) but **not near-ceiling and not cleanly dose-monotone** on this bench. This CONFIRMS B4 (the standing +0.971 does not reproduce) rather than rescuing it.
- **Consequence for the paper:** the headline transplant dissociation (§3.1) does **not** depend on `d_Direct`'s magnitude — its validity controls are exact self-transplant faithfulness (0.0000, n=140) + `DE_context` (+0.35) + the clean NEUTRAL baseline, none of which involve `d_Direct`. State this explicitly to pre-empt the "your positive control is weak" objection: the positive control for "the machinery can produce a concept reading" is `DE_context` itself, not `d_Direct`.

---

*(Further NEXT2 items populated as they land — see NEXT2_PLAN.md.)*

### N-x — Cross-architecture (Qwen3-14B): readout gate is a clean NEGATIVE on thinking models. **[documented negative]**
Job 695089 (`MODEL=Qwen/Qwen3-14B`, forced_choice, same bench): the readout validator **gate_pass_any=False** → the chain self-aborted before the transplant. Qwen3 is a thinking model; the next-token concept/codeword readout fires inside `<think>`, so DIRECT/DS do not separate under the non-thinking template. This is not a mechanism result — it is a **readout-transfer limitation**: the transplant method needs a thinking-aware readout (`enable_thinking=False`, or a post-`</think>` answer-position readout) before it can test Qwen3. Gemma-4 not cached (skipped). The Llama-3.1-8B dissociation therefore stands as single-architecture pending a thinking-aware readout rebuild (future work). The self-gating worked as designed (no wasted compute).
