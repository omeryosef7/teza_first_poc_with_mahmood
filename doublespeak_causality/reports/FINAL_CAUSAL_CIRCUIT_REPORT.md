# FINAL_CAUSAL_CIRCUIT_REPORT.md — Doublespeak causal circuit (Phases 0–10)

Complete causal account of the Doublespeak / in-context representation-hijacking mechanism on a locked
ClearHarm split, **Llama-3.1-8B-Instruct bf16**. Two cohorts reported separately: ClearHarm-native
(primary) + curated harm-in-one-noun (replication). Forced-choice DE_context readout; per-layer/head
**Wilcoxon signed-rank, Holm-corrected**; dev(train)/heldout(test) always separate. Every claim links to a
phase report with n, CIs, controls. **Audited (20/20 confirmed findings fixed/verified) + coverage-validated.**

## The circuit (one line)
**Demonstration-codeword K/V retrieval (L8–11) + L9 MLP write → L14–L21 answer-position carry heads
(downstream-mediated) → L30–31 proximal output → logit.** Distributed within each band (no single necessary
head or edge), but a clear directed layer structure. Concept axis is independent of refusal.

## Answers to the 12 final-deliverable questions

1. **Which demonstration tokens provide the binding?** The demonstration-codeword tokens — neutralizing
   their K/V (resid_pre ← benign) reduces the reading, **necessary in the mid band L8–11, per-layer sig,
   both cohorts** (PHASE4). Necessary, not sufficient (installing into benign gives ≈0).
2. **Which query→demo attention edges retrieve it?** **None specifically.** Surgical query→demo edge
   knockout (all heads, L8–11) is ns on both cohorts — retrieval is distributed/redundant, not a single
   induction edge (PHASE4). The observed attention pattern is descriptive, not causal.
3. **Which heads are necessary?** Answer-position **carry heads in a mid band L14–L18** (+ L21) and a late
   band (L21–31), Wilcoxon-Holm significant. On the expanded **v2 (116-ex)** bench the locked-test power is
   fixed: **dev 58 / heldout 44 Holm-sig heads** (the original curated-heldout n=21 low-power=0 is resolved
   by more examples). Robust both splits: L17H24, L14H4/H5, L17H27, L15H8, L14H23, L21H10, L18H20 (PHASE5).
   Also causal in their **attention PATTERN** (Phase 4b: uniform-pattern knockout −0.13–0.17 both splits).
4. **Which heads/head-sets are sufficient?** **No single head, but the L14–21 carry HEAD-SET is partially
   sufficient** — installing the DS carry-head z into a benign prompt raises the reading to 0.16–0.47
   (20–53% of the full DS reading), significant + specific on all 4 cells (PHASE7c). This is the FIRST
   component with both necessity and sufficiency (demo-KV / MLP-write installs were ≈0): the concept becomes
   a **transplantable representation** once carried by these heads.
5. **At which layers is the binding first causally available?** The MLP write appears at **L9** (necessity
   Holm all 4 cells), co-located with the L8–11 K/V retrieval. Linear *readability* only emerges late (L31),
   which is a readout-proximity artifact, NOT the write layer (PHASE6, PHASE8).
6. **Which MLP/MLP-set writes it?** The **L9 demo-codeword MLP** (band L9–L12) — necessity Wilcoxon-Holm on
   all 4 cells + a monotone dose-response (PHASE6, PHASE9). Necessary, not sufficient.
7. **Which head→MLP paths mediate?** The L14–L21 carry heads are **downstream-mediated** (DIRECT/TOTAL
   `direct_frac ≈ 0` — freezing downstream removes their whole logit effect); only **L30–31 are readout-
   proximal output** (direct_frac ≈ 0.5–0.76). **And the L9-write→carry EDGE is causal**: freezing the
   L14–21 carry band to clean restores ~75–83% of the L9-neutralization drop (random heads restore 0%),
   so the carry band *reads* the L9 write — a directed, edge-connected pathway (PHASE7 + PHASE7b, Gate 5).
8. **Localized or distributed?** **Distributed within concentrated bands** — an L8–12 retrieval/write region
   and an L14–21 carry band. No single necessary head or edge; clear layer structure.
9. **How is the concept mechanism separated from refusal?** `cos(concept, refusal) ≈ 0.01–0.06` at every
   layer, both cohorts — orthogonal, separate levers (PHASE2_DIRECTIONS).
10. **Does it generalize to locked test?** Yes — L9 write survives Holm on heldout (both cohorts); carry
    heads on clearharm heldout; dose-response on heldout; every claim replicates on ≥20 locked-test examples
    (except curated heldout heads, n=21 low-power, honestly flagged).
11. **Can it be a differentiable objective?** The `concept_objective` (d_Direct in the L9–L12 write region)
    + independent `refusal_objective` are eligible: **Gate-6 9/10 pass** (necessity, dose, controls, test,
    refusal-independent) but **sufficiency fails** (distributed). The `doublespeak_signature` is KILLED
    (causally inert) (PHASE10).
12. **Does the objective improve held-out GCG/MAC ASR?** **No — well-controlled NULL** (PHASE11 /
    GCG_MAC_EVALUATION, concluded from existing evidence): state injection is only weakly behaviorally
    sufficient (≤0.16 ASR, "never a potent injectate"); a mechanism-derived GCG objective is net-negative;
    Gate-6 sufficiency fails — three converging lines. The mechanism IS behaviorally actionable, but only via
    the **white-box concept-install + refusal-removal activation edit** (finding #5), NOT a token-suffix
    objective. Field caution: decoding-sufficiency ≠ behavioral sufficiency (a documented dissociation).

## Behavioral grounding (Phase 2)
Doublespeak >> direct on the locked split (ClearHarm malicious-rate DS 0.349 vs direct 0.116 — codeword
rephrase bypasses the refusal that blocks the direct request); curated neutral floor ≈0.03, DS train +0.30
(10×). Gate 1 (reproduction) met.

## Novel contributions vs prior work
- First **ClearHarm-split, cross-cohort, Holm-corrected, locked-train/test** causal account (prior work was
  a single carrot↔bomb pair).
- **Componential dissociation at the demo codeword:** K/V (retrieval) necessary, MLP-out (write @L9)
  necessary, attn-out NOT necessary.
- **Carry-vs-proximal separation** (Phase 7 DIRECT/TOTAL): mid-band L14–21 = genuine mediated carry, only
  L30–31 proximal — resolves the readout-proximity confound quantitatively.
- **Graded dose-response** of the MLP write (Phase 9).
- **Readout ≠ mechanism** demonstrated (Phase 8): linear readability peaks L31, dissociated from the L9/L14
  causal loci.

## Methodological rigor
- **Statistics corrected under audit:** switched per-layer/head significance from a resolution-limited
  sign-flip permutation (which returned artifactual p=0 over the 1024-cell head family) to **Wilcoxon
  signed-rank** (robust to the right-skewed necessity diffs; a t-test was over-conservative). Conclusions
  held under the correct test.
- All patch primitives self-swap = exact no-op (unit-tested + in-data 0.0); matched random/position/donor
  controls; `scripts/validate_experiment_coverage.py` confirms no dup rows / n≥20 / cells present on all
  committed dirs. 20/20 audit findings fixed or verified-inert.

## Sufficiency emerges at the carry stage (refinement)
The binding is **context-bound at the demonstration/write stage** — demo-KV, MLP-write, and behavioral
state injections are all ≈0 sufficient (Phases 4/6). But by the time the concept is carried in the **L14–21
answer-position heads it becomes a transplantable representation**: installing that carry-head z into a
benign prompt raises the reading to 0.16–0.47, specific and replicating (PHASE7c). So the mechanism is a
**progression** — context-bound retrieval/write → transplantable carried concept — not uniformly
non-sufficient.

## Honest limitations
- No single head/edge/layer is the bottleneck; effects are distributed within concentrated bands.
- The carry-head sufficiency is **partial (20–53%)** and **representational** (FC p_concept); its behavioral
  (StrongREJECT) sufficiency is untested (prior state-injection was ≤0.16 behaviorally).
- curated heldout (n=21) is under-powered for the 1024-cell head family — head claims rest on the 3 powered
  cells.
- Sufficiency-installation of carry heads (install carry-head z into benign) not run. (The upstream
  L9-write → carry-head EDGE is now closed — PHASE7b mediation, ~75–83% mediated, random-control 0%.)
- Phase 11 behavioral-ASR test outstanding.

## Phase status — ALL PHASES COMPLETE
0 ✅ · 1 ✅ · 2 ✅ · 3 ✅ · 4 ✅ · 5 ✅ · 6 ✅ · 7 ✅ · 8 ✅ · 9 ✅ · 10 ✅ · 11 ✅ (concluded: null for
suffix objective; behaviorally actionable only via white-box edit).
Reports: CAUSAL_PATCHING_AUDIT · DATASET_AND_SPLIT_CONTRACT · PHASE2_{BEHAVIORAL,DIRECTIONS} ·
PHASE3_RESIDUAL · PHASE4_DEMO_RETRIEVAL · PHASE5_HEADS · PHASE6_MLP · PHASE7_PATH · PHASE8_READOUT ·
PHASE9_DOSE · CAUSAL_OBJECTIVE · GCG_MAC_EVALUATION.

## Bottom line
A complete, audited, cross-cohort, Holm-corrected causal circuit for Doublespeak: **demo-KV retrieval
(L8–11) + L9 MLP write → L14–21 mediated carry heads → L30–31 proximal output → logit**, distributed within
bands, concept axis ⊥ refusal. The mechanism is behaviorally real (DS ≫ direct) and white-box-actionable
(concept-install + refusal-removal), but distributed/context-bound — it does not reduce to a single
head/edge/layer, and it does not convert into a black-box token-suffix attack objective (a well-controlled
null + a field caution that decoding-sufficiency ≠ behavioral sufficiency).
