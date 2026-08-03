# reports/CAUSAL_OBJECTIVE.md — Phase 10: distilled causal objective + Gate-6 eligibility

**Rule (plan Phase 10):** an internal quantity is an eligible optimization target only if interventions
have shown it *controls* interpretation — never a mere predictor. This distills the objective from the
now-complete, Holm-corrected, cross-cohort circuit (Phases 3–9) and grades each term against the 10-point
Gate-6 checklist. Terms are kept SEPARATE (never merge concept + refusal).

## Objective terms (kept separate)

| term | definition (from the validated circuit) | source |
|------|------------------------------------------|--------|
| `concept_objective` | push residual along `d_Direct[L]` (concept axis) at demo-codeword positions, in the **write region L9–L12** | Phase 6 + prior T1 |
| `refusal_objective` | remove the `refusal_direction[L]` component (concept ⊥ refusal, so independent) | Phase 2 dirs + prior T3 |
| `retrieval_objective` | preserve demo-codeword K/V content at the mid band (L8–11) | Phase 4 demo-KV |
| `mlp_write_objective` | the L9 (band L9–L12) demo-position MLP write | Phase 6 |
| `path_objective` | L14–L21 answer-position carry-head contribution | Phase 5 + 7 |
| ~~`doublespeak_signature`~~ | project onto `d_DS` (DS−neutral) | **KILLED — causally inert** (Phase 6 repr = late-proximity artifact; prior T2 = exactly 0.0) |

## Gate-6 eligibility checklist — `concept_objective` / L9-write handle

| # | criterion | evidence | verdict |
|---|-----------|----------|---------|
| 1 | changes under validated circuit intervention | it IS the intervention (MLP-out patch @L9) | ✅ |
| 2 | manipulating it changes interpretation | Phase 6 necessity; Phase 9 dose-response | ✅ |
| 3 | necessity demonstrated | Phase 6 L9 **Wilcoxon-Holm on all 4 cells** | ✅ |
| 4 | **sufficiency** (where feasible) | Phase 6 S3_install ≈ 0 at every layer — installing the demo-position write into benign does **NOT** create the reading | ❌ **necessary-not-sufficient (distributed / context-bound)** |
| 5 | dose-response exists | Phase 9 monotone α∈[0,1] all 4 cells | ✅ |
| 6 | replicates on ≥20 locked test | L9 survives on heldout (both cohorts); dose-response on heldout | ✅ |
| 7 | random / unrelated controls fail | Phase 6 `random_control` (benign donor at non-codeword pos) ≈ 0 | ✅ |
| 8 | not general degradation | per-layer localized L9 (the broad `early`-window +0.42 was flagged as degradation; per-layer L9 is the clean effect) | ✅ |
| 9 | distinct from global refusal removal | cos(concept, refusal) ≈ 0.01–0.06 at every layer (Phase 2) | ✅ |
| 10 | transfers across >1 prompt/concept condition | both cohorts (curated + ClearHarm), 137 examples, many concepts | ✅ |

**Verdict: 9/10 pass; sufficiency (4) fails.** The concept-write handle is a *validated, dose-dependent,
refusal-independent, control-passing, test-replicating NECESSARY* target — but it is **not sufficient in
isolation**, because the Doublespeak binding is distributed and context-bound (necessity spread across the
L8–12 demo computation + the L14–21 carry band; no single component transplants). This matches every
"necessary-not-sufficient" result across Phases 4/5/6 and the prior CAUSAL_CORE T1/T4 finding that the
*sufficient* lever is the explicit `d_Direct` add (not the reconstruction of the hijacked state).

## What the circuit prescribes for optimization
- **Target:** `d_Direct` concept content in the L9–L12 write region at demo-codeword positions **+** an
  independent `refusal_objective`. This is the plan's two-term objective (late concept write + early refusal
  evidence), now localized by causal evidence.
- **Do NOT target** the doublespeak signature (`d_DS`) — causally inert, killed on both the pair and the
  new split — nor a single attention edge/head (distributed; edge-KO null, no single-head sufficiency).

## Phase-11 go/no-go (GCG / MAC)
Gate 6 is **partially met**: the objective is eligible as a necessity-targeting term, but the failed
sufficiency criterion + the distributed mechanism predict a **limited standalone ASR gain**. Prior
CAUSAL_CORE already found mechanism-guided GCG **net-negative / null** (the `d_DS` objective backfired to
ASR 0.0; optimizing a predictive projection did not reliably improve held-out ASR). The NEW contribution a
Phase-11 run can make is a *compute-matched* test of whether the **precisely-localized** L9-write /
concept-region objective (vs the old diffuse one) improves held-out StrongREJECT ASR over naïve GCG — with
the honest prior that it likely will not, because sufficiency fails. **Recommendation:** run one
compute-matched Phase-11 comparison (naïve GCG vs concept-region objective vs signature control vs random
control) as a decisive positive-or-null, rather than assume; flag to Omer that it is a larger GPU ask and
that the expected result is a well-controlled null. (Primary success criterion per plan: improved held-out
behavioral ASR — a projection increase without ASR gain is a NULL.)
```
concept_objective  ✅ eligible (necessity, dose, controls, test, refusal-independent) — NOT sufficient
refusal_objective  ✅ eligible (independent axis)
signature          ❌ killed (inert)
retrieval/mlp/path ✅ necessary contributors, ❌ not individually sufficient (distributed)
```
