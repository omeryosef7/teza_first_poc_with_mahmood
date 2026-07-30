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

*(N2+ populated from the design-panel synthesis + execution — see NEXT2_PLAN.md.)*
