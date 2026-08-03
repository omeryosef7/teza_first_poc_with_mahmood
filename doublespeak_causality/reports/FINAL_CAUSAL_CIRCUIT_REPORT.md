# reports/FINAL_CAUSAL_CIRCUIT_REPORT.md (INTERIM — Phases 0–6)

Synthesis of the Doublespeak causal-circuit sprint on the new locked ClearHarm split. Llama-3.1-8B-Instruct
bf16, forced-choice DE_context readout, paired bootstrap CIs, two cohorts (ClearHarm-native primary +
curated harm-in-one-noun replication). Status: interim — Phases 0–6 (partial); Phases 5/7–11 pending.
Every claim links to a phase report with n, CIs, controls.

## Model / setup
`meta-llama/Llama-3.1-8B-Instruct`, bf16, sdpa (eager for edge-knockout). Split
`data/splits/clearharm_doublespeak_v1.json` @ `clearharm@79464fb…`. Discovery on train/dev only; test/
heldout for frozen replication. Directions built cross-fit dev/heldout.

## Answers to the 12 final-deliverable questions (so far)

1. **Which demonstration tokens provide the binding?** The demonstration-codeword tokens: neutralizing
   their K/V (resid_pre) reduces the reading, significant in the mid band both cohorts, per-layer SIG
   **L8–L11** (PHASE4_DEMO_RETRIEVAL). [answered — necessity]
2. **Which query→demo edges retrieve it?** **None specifically** — surgical query→demo edge knockout
   (all heads, L8–11) is ns on both cohorts; the retrieval is distributed/redundant, not a single edge.
   The 3.5× attention pattern is descriptive, not causal. [answered — negative]
3. **Which heads are necessary?** No single head — per-head edge knockout negligible (distributed;
   matches prior D4). A causally-necessary minimal head set is not identified (likely none small). [answered — distributed]
4. **Which heads/head-sets are sufficient?** Not established; demo-codeword K/V is not locally sufficient
   (installing into benign ⇒ p_concept≈0), so a sufficient local head-set is unlikely. [partial]
5. **At which layers is the binding first causally available?** Mid-band **L8–L11** (demo-KV necessity
   localization, per-layer CIs exclude 0). [answered]
6. **Which MLP writes it?** Representational projection is late-dominated (L29–31) but that is the
   readout-proximity artifact, not the causal write (PHASE6_MLP); causal MLP patching (mid-band expected)
   pending. [pending — causal]
7. **Which head→MLP paths mediate?** Pending (Phase 7). Prior: attention→MLP +1/+2 cascade, no single path. [pending]
8. **Localized or distributed?** **Distributed** — no single head, no local codeword state, no single
   query→demo edge; the effect is a mid-band (L8–11) distributed computation. [answered]
9. **How is concept separated from refusal?** concept_direction ⊥ refusal_direction at every layer
   (mean cos 0.01/0.06, |cos|≤0.15) — independent axes (PHASE2_DIRECTIONS). [answered]
10. **Generalizes to locked test?** Behavioral: ClearHarm stable train/test; curated test weak (n=21).
    Mechanistic (demo-KV): reported over dev+heldout pooled with CIs; a frozen test-only replication of
    the demo-KV sweep is a remaining rigor step. [partial]
11. **Convertible to a differentiable objective?** Not yet — gated on a causal signal passing the Phase-10
    gate. The validated handle so far (demo-KV necessity) is not locally sufficient, which weakens its use
    as an install objective. [pending]
12. **Does the objective improve held-out GCG/MAC ASR?** Pending (Phase 11); prior priors (temporal
    objective backfires, d_DS inert) make a null the likely outcome — will be reported honestly. [pending]

## The mechanism as currently established
Under Doublespeak, the hijacked reading is a property of the **receiver context**, not the query codeword's
local state (IE_state≈0). The **demonstration-codeword content is causally necessary in the L8–11 mid-band**
(both cohorts, per-layer significant), but **not sufficient** in isolation and **not carried by a specific
query→demonstration attention edge** — the binding is a **distributed, context-bound** mid-band computation.
Concept and refusal are **independent axes** at every layer. This reproduces and sharpens the prior
carrot↔bomb account (mid-band retrieval/write) on a multi-concept ClearHarm dataset with matched controls,
and contributes a clean negative: the query→demo induction *edge* is not the causal locus.

## What remains
- Causal MLP write (intervention, mid-band expected) — the write half.
- Head→MLP path patching (Phase 7).
- Concept-direction dose-response (Phase 9) + resolving the prior d_Direct install discrepancy (+0.97 doc vs +0.03 disk).
- Q/K/V/pattern all-head activation patching (Phase 5).
- Behavioral-generation confirmation of the decisive causal cells.
- Frozen test-only replication of the demo-KV sweep.
- Objective (Phase 10) + GCG/MAC (Phase 11) — only if a signal passes the causal gate; null is likely and will be reported.

## Confidence / honesty
The significant claims rest on the **curated** cohort (clean harm-in-one-noun); ClearHarm-native
corroborates direction but is often ns due to concept noise. All effects are matched-control, paired,
bootstrap-CI'd; one control bug (DS-own vs benign random donor) was self-caught and fixed. Readout is
forced-choice DE_context (validated: DS reads concept, benign reads codeword, self-swap exact).
