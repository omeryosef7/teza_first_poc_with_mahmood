# Stage 5 — Generalization of the Context-Carried Dissociation

**Status:** CONFIRMATORY. The Stage-2 dissociation is a property of Doublespeak, not of CARROT↔BOMB. **[NEW]**
**Runs (forced_choice, n=30, job-isolated after B5 fix):** bomb `...694691`; grenade `...694895`; pistol `...694896`; chlorine `...694897`. Backing: each `transplant_mediation_p_concept.json`.

## Per-pair result (NO pooling — per-pair + heterogeneity, plan §5)

| pair (harm cat) | Neutral rcv (h_N / h_DS / h_Direct) | DS rcv (h_N / h_DS / h_Direct) | IE_state (equiv) | DE_context [95% CI] | DE/TE |
|---|---|---|---|---|---|
| **bomb** (explosive) | 0.00 / 0.00 / 0.00 | 0.35 / 0.35 / 0.31 | ≈0 ✅ | **+0.347** [0.261, 0.434] | 99% |
| **grenade** (explosive) | 0.00 / 0.00 / 0.00 | 0.47 / 0.49 / 0.44 | 0.0 ✅ | **+0.465** [0.368, 0.566] | 95% |
| **pistol** (weapon) | 0.00 / 0.00 / 0.02 | 0.16 / 0.17 / 0.20 | ≈0 ✅ | **+0.159** [0.108, 0.218] | 96% |
| **chlorine** (chemical) | 0.00 / 0.00 / 0.00 | 0.39 / 0.39 / 0.38 | ≈0 ✅ | **+0.388** [0.270, 0.515] | 99% |

Every pair: gate passed (real hijack signal); self-transplant faithfulness exact; NEUTRAL receiver clean.

## Conclusion
**On 4/4 pairs across explosive/weapon/chemical harm categories, the dissociation replicates:**
- The **Neutral receiver reads ~0 for every source state** (h_N/h_DS/h_Direct) — no local codeword activation installs the concept in a neutral context.
- The **DS receiver reads the concept for every source state** — the reading is a function of the receiver context, causally independent of the local state.
- `IE_state ≈ 0` (equivalence within ±0.05) on all 4; `DE_context` large with CI excluding 0 on all 4; DE_context ≈ 95–99% of TE.

**Heterogeneity (honest):** absolute hijack strength varies by pair — pistol is the weakest (DS reading 0.16 / DE +0.16), grenade the strongest (+0.47). But the *structural* dissociation (context-carried, local-state-inert) is identical across all pairs. The RELATIVE finding is universal; the ABSOLUTE magnitude is pair-dependent. No pair is an exception to the dissociation; pistol is a weaker-hijack case, not a broken one.

This lifts §3.1 from a single-pair result to a **general property of the Doublespeak mechanism on Llama-3.1-8B.**
