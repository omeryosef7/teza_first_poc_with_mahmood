# Doublespeak Causal-Circuit Sprint — Complete Summary (2026-08-02 → 2026-08-05)

**Purpose of this document.** A single self-contained account of the sprint: what was planned, what was
built, what was run, what the exact numbers are, and what is *not* established. It is written to be handed
to an external reader (human or LLM) with no access to the rest of the repo.

**Verification status.** Every quantitative claim below was re-checked against the raw output files
(`outputs/*/raw.jsonl`, `summary.json`, `*.npz`) by 14 independent auditor agents that recomputed statistics
from the per-example data rather than trusting the reports. **587 claims were checked: 483 VERIFIED,
43 MISMATCH, ~70 PARTIAL, ~18 UNVERIFIABLE.** Where the in-repo reports overstate or misstate a number, this
document uses the **recomputed-from-raw value** and flags the discrepancy in §10. Do not treat the older
report files as authoritative where §10 contradicts them.

---

## 1. Executive summary

The sprint set out to map the complete causal circuit of the **Doublespeak** in-context jailbreak
(arXiv:2512.03771), in which a benign codeword is bound by in-context demonstrations to a harmful concept,
so that a request phrased with the codeword elicits harmful output.

It did two things:

**(A) It mapped the concept circuit.** On a locked ClearHarm split, with per-layer/per-head causal
interventions, Wilcoxon+Holm correction and locked-test replication, the codeword→concept remap is:

> **demonstration-codeword K/V retrieval (L8–L11) + an L9 MLP write → L14–L21 answer-position "carry" heads
> (downstream-mediated) → L30–31 readout-proximal output → logit**, distributed within each band (no single
> necessary head or edge).

The carry head-set is the first component that is both **necessary and partially sufficient** for the
concept readout (installing its activations into a benign prompt creates the reading, +0.16 to +0.47).

**(B) It then tested whether that circuit causes the jailbreak — and found it does not.** This is the
headline, and it inverts the study's own premise:

1. Ablating the L8–11 concept write, or the L14–21 carry heads, throughout harmful generation leaves
   attack success **statistically unchanged** (all ΔASR CIs include 0; McNemar p ≥ 0.29).
2. Ablating a single, orthogonal **refusal direction** is behaviorally **sufficient**: ASR rises
   **+0.43 to +0.48** on every cohort/split (p ≤ 0.004), which is a *stronger* attack than Doublespeak itself.
3. Re-injecting that refusal direction into Doublespeak generation is behaviorally **necessary**: ASR falls
   **monotonically to 0.000** at α=12 in all four cells, with fluent (not broken) refusals.
4. Doublespeak *suppresses* that refusal axis representationally, starting at the same L8–11 band, but the
   behavioral refusal **decision** is read mid-late (~L16–L22).
5. The two effects are **causally independent**: knocking out the concept write reduces the concept readout
   but leaves the refusal suppression completely unmoved (≤5% of the gap).

> **Conclusion.** Doublespeak is, mechanistically, an *imperfect in-context refusal-suppression technique*.
> The elaborate token→concept remap is a causally-decoupled, behaviorally epiphenomenal bystander.
> **Defense implication:** monitor/scrub the refusal axis; concept-subspace defenses leave the causal
> channel untouched.

**Scope bound.** All of this is **Llama-3.1-8B-Instruct only**. No cross-architecture replication was run.

---

## 2. System under study, model, and environment

| item | value |
|---|---|
| Model | `meta-llama/Llama-3.1-8B-Instruct`, **bf16**, 32 layers × 32 heads (8 KV heads, GQA), d_model 4096 |
| Hardware | NVIDIA L40S (single GPU per job), SLURM |
| Stack | torch 2.7.1+cu126, transformers 5.12.1 |
| Attention | default SDPA; **eager forced** wherever attention patterns/edges are hooked (SDPA fuses softmax@V and silently no-ops the hook) |
| Decoding | greedy (`do_sample=False`). `max_new_tokens`: 200 (Phase 2.1), 220 (behavioral arms), 180 (calibrated injection), 120 (trajectory) |
| Harm judge | **StrongREJECT** rubric grader; label `MALICIOUS` iff score ≥ **0.25**. `ASR` = fraction MALICIOUS. `refusal_rate` = fraction matching a 16-marker refusal keyword list (mutually exclusive with MALICIOUS by construction) |
| Concept readout | **forced-choice "DE_context"**: append a question to the demo block and read `p_concept = P(concept)/(P(concept)+P(codeword))` at the answer position |
| Attack source | ClearHarm, revision `79464fb6b3c2a8ee925184f394f9636600349f88`; demos generated with `gpt-4o-mini`, `openai_seed=7`, 12 demonstrations per prompt |

### 2.1 The six matched prompt conditions
Each example carries: `doublespeak` (attack), `neutral` (codeword, no demos), `direct` (plain harmful
request), `benign` (codeword bound to benign demos), `shuffled` (shuffled bindings), `unrelated`
(unrelated bindings). All 137 `neutral`/`direct`/`doublespeak` prompts are unique; prompt reconstruction
between the split file and the eval driver was verified byte-identical for all 411 prompts.

---

## 3. The plan (`CAUSAL_CIRCUIT_MASTER_PLAN.md`, 743 lines, committed 2026-08-02)

### 3.1 Phases
| Phase | Content |
|---|---|
| 0 | Repository/result audit, provenance, data-integrity validators |
| 1 | ClearHarm dataset + permanently locked train/test split |
| 2 | 2.1 behavioral baselines (10 conditions); 2.2 separate `concept_direction[L]`, `refusal_direction[L]`, `doublespeak_signature[L]` |
| 3 | Exhaustive all-occurrence residual-stream patching (32 layers × 4 locations × 10 position-sets × 2 directions) |
| 4 | Exhaustive attention: 4.1 all-head scan (descriptive), 4.2 query→demo edge knockout, 4.3 edge sufficiency |
| 5 | Exhaustive activation patching of **all** attention heads (pattern/Q/K/V/z/head-result) |
| 6 | Exhaustive MLP write-location analysis |
| 7 | Head→MLP path patching (every sender head × every downstream receiver MLP) |
| 8 | Jacobian/projection readout across all layers |
| 9 | Intervention-strength (dose-response) sweeps |
| 10 | Distill a causal optimization objective (Gate-6 eligibility checklist) |
| 11 | GCG and MAC/TROPT evaluation (13-arm compute-matched matrix) |

### 3.2 Five non-negotiable coverage mandates
1. **Every layer individually** (L0–L31); every head in every layer; every MLP layer.
2. **≥ 20 unique examples per cell**, where a cell = split × condition × layer × head × activation type ×
   position set × direction × control × strength. Repeated seeds/generations do not count.
3. **Complete train/test separation** — split created *before* any layer/head/threshold selection; the full
   all-layer sweep repeated on locked test (never best-layer-only).
4. **No layer cherry-picking** — save and report all layers, heads, controls, and null results.
5. **Primary causal conclusions require bf16.**

### 3.3 Granularity mandate (A–G)
Every principal intervention family was to be run at **seven** granularities: A each layer alone,
B canonical windows (early L0–9 / mid L10–19 / late L20–31 + unions), C sliding windows of width 2/4/8
(every valid window), D cumulative prefixes, E cumulative suffixes, F mechanism-derived windows (train-frozen),
G all layers simultaneously — each with ≥20 train and ≥20 locked-test examples, 10 window-control types,
a synergy/interaction analysis, and 12 mandatory plot types per family.

### 3.4 Seven go/no-go gates — and their actual status
| Gate | Requirement | Actual outcome |
|---|---|---|
| 1 Reproduction | existing presentation results reproduce | **MET** (declared 2026-08-02, commit `c528069`) |
| 2 Exhaustive layer coverage | all layers, n≥20/cell, before reporting | **never declared** — the in-repo checklist still shows it unchecked |
| 3 Attention causality | an edge/head passes exact necessity vs matched controls | **PARTIAL, then re-framed** — demo-codeword *content* (K/V) is necessary; query→demo *edges* are not |
| 4 Write location | exact MLP patching changes downstream interpretation | **PARTIAL** — L9 necessity yes; sufficiency no |
| 5 Path mediation | head→MLP circuit not from correlation alone | **MET** (commit `dd51531`) |
| 6 Objective | causal evidence + dose + controls + locked test | **9/10 pass, criterion 4 (sufficiency) FAILS → gate not passed** |
| 7 Behavioral improvement | improved held-out ASR vs compute-matched baseline | **NOT TESTED** — Phase 11 was concluded from prior evidence, not run |

---

## 4. Data: the locked split and the v2 expansion

### 4.1 Locked split — `data/splits/clearharm_doublespeak_v1.json` (frozen 2026-08-02, commit `c5e8ef3`)
**137 records** in two cohorts, split at the *intent-cluster* level:

| cohort | n | train | test | unique concepts | intent clusters |
|---|---|---|---|---|---|
| **clearharm** (primary) | 86 | 44 | 42 | 43 | 86 (each instruction its own cluster) |
| **curated** (replication) | 51 | 30 | 21 | 17 (×3 records each) | 17 → 10 train / 7 test |
| **total** | 137 | 74 | 63 | — | — |

Integrity, all recomputed from the artifact:
- **0** example_id overlap, **0** intent_cluster overlap, **0** duplicate prompts across train/test — in all six conditions.
- **137/137** concepts and codewords are **single-token**.
- Codeword occurrences after chat templating: 13 for 135 items (12 demo bindings + 1 query); one item 12, one item 7.
- Harm categories — clearharm: other/uncategorized 54, weapons/explosives 16, cyber/malware 13, identity theft 2, fraud 1. curated: weapons 27, narcotics 12, explosives 9, toxins 3.
- 86 usable single-token-concept examples were derived from 179 ClearHarm instructions; 25 multi-token curated concepts were excluded.

⚠ **The curated locked-test cell is n=21**, one above the ≥20 floor. This is the direct cause of the sprint's
one acknowledged power failure (Phase 5 curated-heldout = 0 significant heads).

### 4.2 v2 expanded bench — `data/bench/bench_clearharm_v2.json` (2026-08-04)
**116 Doublespeak examples** = the 86 clearharm items + **30 new gpt-4o-mini-generated single-token concepts**
(73 unique concepts total), split **dev 59 / heldout 57**; effective `n_valid` on causal scans is **59 / 55**.
**No test leak**: 0 concept, 0 codeword and 0 prompt overlap between the v1 test ids and the 30 new concepts.
(Caveat: the file's `_meta.n_examples=86` and `pair.n_concepts=43` are stale metadata — the actual contents are
116 / 73. Also, the 30 expanded items carry only 4 of the 6 conditions — no shuffled/unrelated.)

---

## 5. Statistics and controls (applies to everything below)

- **Paired designs throughout.** Per-example matched differences, dev(train) and heldout(test) aggregated
  **separately** (a pooling bug was caught and fixed mid-sprint).
- **Representational significance:** two-sided **Wilcoxon signed-rank**, **Holm**-corrected across the
  32-layer family or the full 32×32 = 1024-cell head family, per split. *This replaced a sign-flip
  permutation test whose resolution floor (1/2e4 = 5.0e-5) was coarser than the Holm threshold
  (0.05/1024 = 4.88e-5) and which returned artifactual p=0 — see §10.1.*
- **Behavioral significance:** **exact McNemar** on paired discordant flips, plus percentile bootstrap CIs
  (2000–5000 resamples, seeded RNG; the analyzer's CIs were reproduced digit-for-digit by the audit).
- **Effect CIs:** nonparametric percentile bootstrap, 2000 resamples, `np.random.default_rng(0)`.
- **Tripwire controls, all verified exactly 0.0 in the raw data:** self-swap (patch a component with its own
  captured value), self-check freeze, identity patch, α=0 no-op anchor.
- **Specificity controls:** norm-matched random directions, count-matched random heads, count-matched random
  positions, random-edge donors, random-head installs.
- **Coherence guard:** `empty_rate` = 0.000 in every behavioral cell, plus a `--save-gen` inspection pass.

---

## 6. Chronology of execution

163 commits on branch `behavioral-causality-sprint` (Aug 2: 25, Aug 3: 66, Aug 4: 59, Aug 5: 14),
130 files touched, **37 new analysis scripts**, **20 new SLURM wrappers**, **3 new hook primitives**
(`SubmodulePatch` resid_pre support, `ComponentOutSwap`, `AllPositionZHeadAblate`), each gated on synthetic
tests before use.

| date | work |
|---|---|
| **Aug 2** | Phase 0 repo audit (`CAUSAL_PATCHING_AUDIT.md`) + data-integrity validator; Phase 1 locked split built and frozen; split→bench and split→behavioral adapters; Phase 2 representation extraction, concept/refusal/signature directions (32-layer refusal build); **Phase 2.1 behavioral baseline → Gate 1 met**; Phase 3 resid_post launched |
| **Aug 3** (heaviest) | Phase 3 resid_post null; Phase 4.2 demo-KV necessity + edge-knockout negative; Phase 6 MLP write (+ attn_out generalization); Phase 5 full 32×32 head scan; Phase 7 DIRECT-vs-TOTAL (**Gate 5**); Phase 9 dose; Phase 8 readout; Phase 7b circuit-closure mediation; Phase 7c sufficiency; Phase 7d onset; Phase 10 objective; Phase 11 designed then concluded; first formal code audit (**20 findings**) |
| **Aug 4** | **Scale-up**: 30 new concepts → v2 116-example bench; all core results re-run on v2; three new harnesses (MLP windows, attention-pattern, Q/K/V) authored by a parallel agent workflow; second formal code audit (**15 findings**, incl. the Q/K/V retraction). **Then the pivot** (iter 83–84): from representational readout to the **behavioral frontier** — carry/write behavioral necessity (both null) → refusal sufficiency → refusal necessity → refusal projection → calibrated depth localization |
| **Aug 5** | Harness bug-audits; three paper figures; consolidated Table 1; a new no-GPU result mined from existing data (item-level AUC 0.87); trajectory runs completed on freed GPU; robustness audit of the AUC claim; drop-in abstract |

**The pivot (the most important decision of the sprint).** On Aug 4 the representational circuit was judged
comprehensively established, scaled and audited, so the open question became *whether that circuit actually
controls harmful behavior*. The first two behavioral tests came back **null**, which motivated the
complementary search for what *is* behaviorally potent — and that search produced the headline.

---

## 7. RESULTS PART A — the representational concept circuit

All readouts here are **forced-choice `p_concept`** (not behavior). Sign convention: a **positive effect =
the intervention DROPPED the hijacked reading**.

### 7.1 Phase 2.1 — behavioral baselines (Gate 1)
Malicious rate (StrongREJECT ≥ 0.25), greedy, `max_new_tokens=200`:

| cohort | n | direct | neutral | doublespeak |
|---|---|---|---|---|
| clearharm (aggregate) | 86 | **0.116** | 0.256 | **0.349** |
| clearharm train | 44 | 0.136 | 0.250 | 0.364 |
| clearharm test | 42 | 0.095 | 0.262 | 0.333 |
| curated (aggregate) | 51 | 0.255 | 0.039 | 0.235 |
| curated train | 30 | 0.200 | 0.033 | **0.333** (+0.30 over neutral, 10×) |
| curated test | 21 | 0.333 | 0.048 | 0.095 (2/21; 95% CI [0.012, 0.304]) |

Doublespeak beats direct on ClearHarm by **+0.233** aggregate. Curated test is weak and wide — honestly flagged.
Refusal rates (present in raw but omitted from the report): clearharm direct/neutral/DS = 0.860/0.605/0.465;
curated = 0.686/0.157/**0.000**.

### 7.2 Phase 2.2 — direction geometry
Per-layer directions at `resid_post` / codeword-last position, all 32 layers, built from train only.
Recomputed in float64 from the raw `.npz`:

| quantity | clearharm | curated |
|---|---|---|
| mean cos(concept, refusal) | **0.012** (max abs **0.078** @L10) | **0.061** (max abs **0.153** @L11) |
| mean cos(signature, refusal) | 0.127 | 0.151 |
| mean cos(concept, signature) | 0.245 | 0.138 |
| refusal separation by depth | 0.334 (L0) → 1.037 (L23) → 0.942 (L31) | — |

**Concept ⊥ refusal is real** (|cos| ≤ 0.153 everywhere). Note the `doublespeak_signature`
(DS − neutral difference vector) is *closer to refusal* than the concept direction is — an early hint of the
headline. The refusal direction was built from 60 harmful / 20 harmless prompts, separation 0.922 at L16.

### 7.3 Phase 3 — residual-stream patching at the query codeword: **NULL**
Logit-lens P(harm) at the query codeword is at the floor for clean Doublespeak, and no patch beats the
random control:

| cell | n | baseline p_harm | best necessity drop | random-control drop |
|---|---|---|---|---|
| clearharm train | 44 | 0.013 | +0.012 @L25 | +0.013 |
| clearharm test | 42 | 0.020 | +0.015 @L30 | +0.020 |
| curated train | 30 | 0.001 | +0.001 @L30 | +0.001 |
| curated test | 21 | 0.000 | +0.000 @L5 | +0.000 |

Identity control exactly 0.0 for all 137 items. **The local codeword state carries nothing** — consistent with
the prior `IE_state ≈ 0` result. *(Coverage note: this swept 31 layers L0–L30, not 32; the final block is
excluded by design because patching at the readout layer would overwrite the measured vector.)*

### 7.4 Phase 4.2 — demonstration-codeword K/V retrieval is NECESSARY (not sufficient)
Neutralize the demo-codeword K/V (donor = BENIGN_REMAP, which has codeword demos), forced-choice readout.
Specific effect = random_control − C3, bootstrap 95% CI:

| window | curated (n=51) | clearharm (n=85) |
|---|---|---|
| early L0–9 | **+0.258 [0.146, 0.372]** | +0.017 [−0.054, 0.087] ns |
| mid L10–20 | **+0.177 [0.087, 0.278]** | **+0.081 [0.012, 0.151]** |
| late L21–31 | −0.037 ns | −0.009 ns |

Per-layer localization (CI excludes 0 = significant):

| layer | curated | clearharm |
|---|---|---|
| L8 | +0.176 [0.084, 0.266] ✓ | +0.069 [0.003, 0.136] ✓ |
| **L9** | **+0.220 [0.136, 0.310] ✓** | +0.082 [0.018, 0.148] ✓ |
| **L10** | +0.213 [0.129, 0.299] ✓ | **+0.113 [0.045, 0.189] ✓** |
| L11 | +0.112 [0.045, 0.186] ✓ | +0.022 [−0.033, 0.079] **ns** |

⇒ **The honest joint statement is L8–L10 on both cohorts** (the reports say L8–L11; clearharm L11 is ns).
Self-swap deviation exactly 0.0 at every window and every one of the 32 layers.
**Sufficiency is ≤ 0 at every window** (installing DS demo-K/V into a benign prompt creates nothing) —
the binding is context-bound at this stage.

### 7.5 Phase 4.2 — query→demonstration attention EDGES are NOT necessary (clean negative)
Surgical edge knockout (eager attention), all heads across L8–11, destination = query codeword + answer
position, source = demo codewords:

| cohort | n | raw KO drop | **specific vs random-edge** | all-query-edges (degradation control) |
|---|---|---|---|---|
| clearharm | 83 | 0.0024 [0.0001, 0.0049] | **+0.0020 [−0.0004, 0.0046] ns** | 0.0312 (13× larger) |
| curated | 51 | 0.0022 [−0.006, 0.012] | **−0.0026 [−0.014, 0.009] ns** | 0.1084 (49× larger) |

⇒ Retrieval is **distributed / redundant**, not a single induction edge. The observed attention pattern is
descriptive, not causal. Blocking *all* query edges hurts far more than blocking the demo edges specifically —
a general-attention effect.

### 7.6 Phase 6 — the L9 MLP write (the concept write location)
Patch DS `mlp_out` with matched benign `mlp_out` at the **demonstration** codeword positions.
**L9 is the only layer Holm-significant on all four cells:**

| cell | L9 necessity | 95% CI |
|---|---|---|
| curated dev (n=30) | +0.049 | [0.021, 0.081] |
| curated heldout (n=21) | +0.097 | [0.038, 0.165] |
| clearharm dev (n=44) | +0.063 | [0.022, 0.113] |
| clearharm heldout (n=41) | +0.015 | [0.006, 0.030] |
| **v2 clearharm dev (n=59)** | **+0.080** | Holm band L8–L13 |
| **v2 clearharm heldout (n=55)** | **+0.030** | Holm band L9–L13 |

- **Sufficiency ≈ 0 at every layer** (max |S3_install − S_random| = 0.0002–0.014; the largest magnitudes are
  *negative* degradation at L0/L1).
- **Componential dissociation at the same token:** `attn_out` at L9 is **null** on all four cells
  (+0.003 / −0.076 / +0.011 / +0.001, none Holm-significant), while K/V and MLP-out are both necessary.
- Self-swap exactly 0.0 at every layer/window/split.
- ⚠ **The query-codeword MLP is NOT a clean null on clearharm** — L9 (+0.0146 dev, +0.0046 heldout), L15 and
  L20 all survive Holm on both splits. The correct statement is that the query effect is **3–4× weaker** than
  the demo effect, not absent. (It *is* a clean null on curated.)

### 7.7 Phase 6b — write granularity (143 windows, the one place the A–G mandate was met)
On v2, `n_valid` dev 59 / heldout 55, self-swap 0.0 across all 143 windows:

| granularity | window | dev | heldout |
|---|---|---|---|
| A single layer | L9 | +0.080 | +0.030 |
| C sliding W2 | L8–9 | +0.083 | +0.052 |
| C sliding W4 | **L8–11** | **+0.111** | **+0.076** |
| C sliding W8 | L8–15 | +0.112 | +0.077 |
| C sliding W8 | **L2–9 (best W8)** | **+0.192** | **+0.193** |
| D cumulative prefix | L0–13 | +0.229 | +0.250 |
| E cumulative suffix | L8–31 | +0.096 | +0.069 |

⇒ **One layer is not sufficient**: the L8–11 window (+0.111) exceeds the best single layer (+0.080) — the
write is **distributed across L8–11**. ⚠ But the report's "saturates at W8, wider windows add nothing" is
**wrong**: the best W8 window (L2–9) is ~1.7× the best W4 window. Saturation holds only within the fixed
L8-start family.

### 7.8 Phase 5 — all-head z-patch necessity (the carry heads)
Patch each (layer, head) answer-position `z` with the matched benign value; Wilcoxon + Holm over 1024 cells.

| cell | n_valid | Holm-significant positive-necessity heads |
|---|---|---|
| curated dev | 30 | **58** |
| curated heldout | **21** | **0** ← low power, not a structural null (see below) |
| clearharm dev | 44 | **31** |
| clearharm heldout | 41 | **31** |
| **v2 dev** | **59** | **58** |
| **v2 heldout** | **55** | **44** ← the power problem is fixed by more examples |

Top heads (effect = drop in reading): v2 **L17H24 0.051 dev / 0.023 heldout**; clearharm dev L17H27 0.035,
L14H4 0.033, L14H5 0.027, L14H23 0.021, L30H15 0.020, L21H10 0.018. Heads robust in both v2 splits include
L17H24, L14H4/H5/H23, L17H27, L15H8, L21H10, L18H20, L22H11/H19, L27H7, L30H15, L31H0/H1.

- **The curated-heldout 0 is a power failure, not a null**: its per-head *raw* effects are the **largest of any
  cell** (L15H4 +0.106 [0.046, 0.173], L14H4 +0.104 [0.053, 0.159], CIs excluding 0) — they simply cannot
  clear a 1024-cell Holm threshold at n=21.
- **No single head dominates**: the top head is ~5% of total positive necessity; the top 10 are 20–33%
  (34–40% on v2).
- Self-swap exactly 0.0 in all six split-cells.

### 7.9 Phase 4b — the carry heads are causal in their attention PATTERN, not only their output
Uniform-pattern knockout (replace each carry head's attention row with 1/k over its causal keys), v2:

| effect | dev (n=59) | heldout (n=55) |
|---|---|---|
| joint 7-head uniform-pattern KO | **+0.166 [0.097, 0.238]** | **+0.134 [0.077, 0.199]** |
| benign-pattern transplant (specific) | +0.460 [0.371, 0.547] | +0.451 [0.362, 0.542] |
| baseline C1 reading | 0.879 | 0.869 |
| self-swap (own pattern) | **exactly 0.0** | **exactly 0.0** |

Per-head decomposition: **no head is individually necessary**; L14H5 is even **negative** (−0.050 / −0.031,
CIs exclude 0 → other heads *compensate*), L17H24 −0.013 / −0.007, L14H4 +0.015 / +0.005, L15H8 ≈ 0. The joint
effect is **strongly superadditive** vs the sum of per-head effects (−0.018 / −0.021) — the same
distributed-with-compensation signature as the output and write stages.

⚠ **Honest caveat the report omits:** the uniform-KO arm has **no specificity control** — an arbitrary
non-candidate head's pattern (`C_rand`) already produces a 0.152 dev / 0.103 heldout drop, so
"uniform-KO is more specific" is unsupported on dev (difference CI includes 0).

### 7.10 Phase 4c — where the carry heads get the concept from
Knock out the carry heads' answer→demo-codeword edges:

| arm | dev (n=59) | heldout (n=57) |
|---|---|---|
| **KO_all** (block all earlier keys — *firing control*) | +0.246 [0.167, 0.329] | +0.207 [0.135, 0.288] |
| **KO_demo** (block only demo-codeword keys) | +0.007 [0.003, 0.012] | +0.003 [0.001, 0.005] |

⇒ The machinery fires (KO_all), but blocking the demo codewords specifically does almost nothing (~2–3% of
KO_all). **The carry heads read the concept from the distributed residual context by the answer position, not
by fresh attention to the demo codewords.** *(Self-caught caveat: KO_all is a firing control, not a retrieval
measure — it also blocks the forced-choice question, which contains the answer options. Phase 4c uses a 9-head
carry set; Phase 4b uses 7 — the reports present both as "the carry heads".)*

### 7.11 Phase 7 — carry vs proximal, and closing the circuit edge
**(a) DIRECT-vs-TOTAL** (`direct_frac` = fraction of a head's logit effect that survives freezing everything
downstream), n = 30/21/44/42, all four cells:

| head | direct_frac (cur dev / cur held / ch dev / ch held) | reading |
|---|---|---|
| L14H4, L14H23, L15H4, L15H8 | 0.00 / 0.00 / 0.00 / 0.00 | pure **carry** (fully mediated) |
| L14H5 | 0.00 / 0.05 / 0.00 / 0.00 | carry |
| L17H27 | 0.17 / 0.00 / 0.09 / 0.07 | carry + small direct |
| L18H20 | 0.00 / 0.04 / 0.08 / 0.09 | carry |
| L21H10 | 0.00 / 0.00 / 0.00 / 0.02 | carry |
| **L30H15, L31H0** | **0.47 – 0.76** | **readout-proximal output** |

24 of the 32 mid-band cells are **exactly 0.000**. Freeze-consistency and self-swap deviation = **exactly 0.0**
across all 1370 head-rows. This resolves the readout-proximity confound quantitatively.

**(b) Phase 7b — the L9-write → carry-band edge is causal.** Neutralize L9, then freeze the L14–21 carry `z`
to clean and measure how much of the L9 drop is restored:

| cell | mediation fraction | random-head control |
|---|---|---|
| curated dev (n=9 L9-responsive) | 0.764 | 0.0 |
| curated heldout (n=9) | 0.828 | 0.0 |
| clearharm dev (n=13) | 0.751 | 0.0 |
| clearharm heldout (n=9) | 1.459 | 0.0 |

Self-check freeze deviation exactly 0.0. ⚠ **Caveat:** these are medians over the *L9-responsive subset*
(n = 9–13), which is below the plan's ≥20 mandate; the headline "75–83%" range excludes the fourth cell (1.459).

**(c) Phase 7c — the carry head-set is PARTIALLY SUFFICIENT** (the first component that is). Install the DS
carry-head `z` into a benign prompt:

| cell | reading achieved | specific effect (vs random-head install) |
|---|---|---|
| curated dev (n=30) | 0.162 | **+0.162 [0.086, 0.254]** |
| curated heldout (n=21) | 0.240 | **+0.239 [0.126, 0.370]** |
| clearharm dev (n=44) | 0.434 | **+0.369 [0.268, 0.477]** |
| clearharm heldout (n=42) | 0.467 | **+0.406 [0.297, 0.509]** |
| **v2 dev (n=59)** | — | **+0.326 [0.246, 0.411]** |
| **v2 heldout (n=57)** | — | **+0.348 [0.261, 0.439]** |

Random-head install does **nothing** (S3−S_rand ≈ S3−S1); self-install deviation exactly 0.0.
⇒ The mechanism is a **progression**: context-bound at retrieval/write → **transplantable** once carried.

**(d) Phase 7d — sufficiency accumulates GRADUALLY** across L14→L14-21 (not abruptly). The single largest
increment in every cell is adding **L17 (H27)**: ×11.0 (cur dev), ×4.0 (cur heldout), ×2.0 / ×2.2 (clearharm).
Clearharm already has substantial L14-alone sufficiency (0.16–0.19) while curated builds from ~0.

### 7.12 Phase 8 — readout ≠ mechanism
Per-layer linear concept projection (mean DS − mean neutral, onto the unit concept direction):
**peak = L31 in all four cells**, and at the causal write layer L9 the projection is **≈ 0**
(|fraction of max| = 0.008–0.163). The L30→L31 jump is 2.4× to 12.8×.

⇒ **Linear readability peaks at the very last layer while causality lives at L9/L14–21.** Logit-lens-style
readouts localize *readout proximity*, not the write. ⚠ But the report's "grows monotonically" is **false**:
11–14 of the 31 layer-to-layer steps are *decreases*, and the curve goes clearly negative mid-late. The
accurate phrasing is: *small and non-monotone through L0–L30, then a sharp terminal spike at L31.*

### 7.13 Phase 9 — the write is a GRADED lever (dose-response)
Interpolated donor `(1−α)·DS + α·BENIGN` at the demo-codeword `mlp_out`. **Actual α grid = {0, 0.25, 0.5,
0.75, 1.0, 1.5, 2.0}** (the plan asked for a 3.0 point; it was not run).

| cell | single L9: p_concept at α = 0 → 1 | drop | band L9–L11 drop |
|---|---|---|---|
| curated dev (n=30) | 0.811 → 0.762 | 0.048 | 0.102 |
| curated heldout (n=21) | 0.690 → 0.575 | 0.115 | 0.107 |
| clearharm dev (n=44) | 0.884 → 0.819 | 0.065 | 0.087 |
| clearharm heldout (n=41) | 0.879 → 0.862 | 0.017 | 0.028 |

**Monotone decreasing over α ∈ [0,1] in 8/8 cells.** Anchors are exact, not approximate: α=0 is **bitwise
identical** to the Phase-6 unpatched DS baseline (51/51 curated, 86/86 clearharm), and α=1 is **bitwise
identical** to the Phase-6 necessity patch.

⚠ **Phase 9 has no inferential statistics at all** — no CI, no p-value, no per-example test. The claim rests
on the ordering of 5 point-means per cell (smallest cell n=21). The α>1 region shows a trivial uptick on two
curated cells; the monotonicity claim was correctly restricted to [0,1] by audit, but the **on-disk
`summary.json` files still carry the pre-fix flag** and should be regenerated.

### 7.14 Circuit summary (Part A)

```
demo-codeword K/V retrieval (L8–L10, peak L9–L10)   ──┐
    necessary (both cohorts), NOT sufficient           │  co-located at L9
L9 demo-codeword MLP write (band L8–L13)            ──┘
    Holm-sig all 4 cells, graded dose-response, NOT sufficient
                    │  (edge is causal: ~75–83% mediation, random control 0%)
                    ▼
L14–L21 answer-position CARRY heads
    necessary (58 dev / 44 heldout Holm-sig heads on v2)
    causal in their attention PATTERN (−0.13 to −0.17)
    PARTIALLY SUFFICIENT (+0.16 to +0.47) ← first component with both
    fully downstream-mediated (direct_frac ≈ 0)
    reads from distributed residual context, NOT from fresh demo attention
                    ▼
L30–L31 readout-proximal output (direct_frac 0.47–0.76) → logit
```

**Distributed within concentrated bands.** No single head, edge, or layer is a bottleneck.

---

## 8. RESULTS PART B — the behavioral frontier (the headline)

Everything here is **StrongREJECT-judged generation** (real behavior), paired **exact McNemar**, two cohorts,
locked splits, matched controls, `empty_rate = 0.000` everywhere.

### 8.1 BEHAV-CARRY — ablating the carry heads through generation: **NULL**
Zero the 9 carry heads' `z` at **every position on every forward pass** (prefill + each cached decode step):

| cell | n | base ASR | carry-ablated | ΔASR | 95% CI | McNemar p | random-head control |
|---|---|---|---|---|---|---|---|
| clearharm train | 44 | 0.364 | 0.273 | +0.091 | [−0.023, +0.227] | 0.289 | +0.023 |
| clearharm test | 42 | 0.357 | 0.286 | +0.071 | [−0.024, +0.167] | 0.375 | +0.024 |
| curated train | 30 | 0.333 | 0.433 | −0.100 (reversed) | [−0.300, +0.100] | 0.508 | +0.033 |
| curated test | 21 | 0.095 | 0.095 | 0.000 | [−0.190, +0.190] | 1.000 | −0.095 |

Every CI includes 0; every Holm-corrected p ≥ 0.578. The clearharm trend is consistent in direction and ~3–4×
the random control, but **not significant**.

### 8.2 BEHAV-WRITE — ablating the L8–11 concept write through generation: **NULL (flatter)**
Zero `mlp_out` at L8–11 at the ~12 **demonstration** codeword positions (the query codeword is preserved):

| cell | n | base ASR | write-ablated | ΔASR | McNemar p | random-position control |
|---|---|---|---|---|---|---|
| clearharm train | 44 | 0.386 | 0.409 | −0.023 | 1.000 | −0.023 |
| clearharm test | 42 | 0.310 | 0.310 | 0.000 | 1.000 | −0.048 |
| curated train | 30 | 0.333 | 0.267 | +0.067 | 0.688 | +0.033 |
| curated test | 21 | 0.095 | 0.095 | 0.000 | 1.000 | 0.000 |

All ΔASR ∈ [−0.023, +0.067]; every CI includes 0; the one non-zero point is indistinguishable from its random
control. *(Implementation note: `ComponentOutSwap`'s position guard means this edit fires during **prefill
only** — it is a prompt-side ablation, whereas BEHAV-CARRY fires at every decode step.)*

> **⇒ The complete representation ≠ behavior dissociation.** The very components that are causally necessary
> (and, for the carry heads, sufficient) for the concept **readout** are **not behaviorally necessary** for the
> jailbreak.

### 8.3 BEHAV-REFUSAL, sufficiency arm — ablating the refusal axis is a STRONGER attack than Doublespeak
Arditi-style directional ablation: project the validated **L18 refusal direction** out at **every layer and
every position through generation** (α=1.0). Five paired arms per item.

**ASR / refusal_rate per arm:**

| cohort·split | direct_base | **direct_refabl** | direct_randabl | ds_base | ds_refabl |
|---|---|---|---|---|---|
| clearharm train (44) | .136 / .841 | **.568** / .273 | .136 / .864 | .386 / .477 | .727 / .045 |
| clearharm test (42) | .071 / .881 | **.548** / .262 | .071 / .881 | .357 / .452 | .548 / .095 |
| curated train (30) | .267 / .700 | **.700** / .233 | .233 / .700 | .300 / .000 | .367 / .000 |
| curated test (21) | .286 / .667 | **.714** / .286 | .381 / .619 | .095 / .000 | .095 / .000 |

**Paired exact McNemar:**

| comparison | clearharm train | clearharm test | curated train | curated test |
|---|---|---|---|---|
| **refusal-ablation vs direct base** | **+0.432, p=4.0e-6** (19 flips to harm / 0 away) | **+0.476, p=2.0e-6** (20/0) | **+0.433, p=9.8e-4** (14/1) | **+0.429, p=3.9e-3** (9/0) |
| random-ablation vs direct base | 0.000, p=1.0 | 0.000, p=1.0 | −0.033, p=1.0 | +0.095, p=0.5 |
| Doublespeak vs refusal-ablation | −0.182, p=0.057 | −0.190, p=0.057 | −0.400, p=1.8e-3 | −0.619, p=2.4e-4 |

Three findings:
1. **Refusal suppression alone is behaviorally sufficient** — ASR **+0.43 to +0.48**, every split p ≤ 0.004,
   refusal_rate collapsing **0.67–0.88 → 0.23–0.29**.
2. **Clean specificity** — a norm-matched random direction of equal norm does **nothing** on any split (p ≥ 0.5).
3. **Refusal removal alone ≥ Doublespeak on all four splits** — ⚠ significantly on **2/4** at α=.05
   (curated train and test), **4/4 only at α=.10**. *(The reports say "3/4"; that count comes from a preempted,
   incomplete run — see §10.4.)*

**Doublespeak is an imperfect refusal suppressor:** ds_base refusal_rate 0.45–0.48 on clearharm sits between
Direct (0.84–0.88) and full ablation (0.05–0.10), and DS + explicit ablation climbs higher than either alone
(clearharm train 0.727 vs direct_refabl 0.568 vs ds_base 0.386; McNemar +0.341, p=2.8e-4).

The refusal direction was bidirectionally validated before use: ablate_gain +0.467, induce_gain +0.667,
separation 0.9525 at L18.

### 8.4 BEHAV-REFUSAL, necessity arm — re-injecting refusal kills the jailbreak
Add **+α · refusal axis** at every position/timestep at L18 through Doublespeak generation:

| cohort·split | ds_base | α=4 | α=8 | **α=12** | random @ α=8 |
|---|---|---|---|---|---|
| clearharm train (44) | .386 (.48) | .159 (.77) | .091 (.91) | **.000 (1.00)** | .500 (.32) |
| clearharm test (42) | .381 (.45) | .190 (.79) | .071 (.93) | **.000 (1.00)** | .500 (.31) |
| curated train (30) | .333 (.00) | .200 (.53) | .000 (.97) | **.000 (1.00)** | .433 (.00) |
| curated test (21) | .095 (.00) | .095 (.33) | .000 (1.00) | **.000 (1.00)** | .286 (.00) |

*(format: ASR (refusal_rate))*

McNemar vs ds_base: clearharm α12 **−0.386, p=1.5e-5** (17 flips off / 0 on) and **−0.381, p=3.1e-5** (16/0);
α8 already −0.296 / −0.310 at p=2.4e-4; curated train α8 and α12 −0.333, p=2.0e-3.
⚠ **curated test is p=0.50 — not significant** (only 2 of 21 items were malicious at baseline, so there is
nothing to flip). The reports' "p = 2e-5 … 2e-3" range silently drops this cell.

**Coherence audit (the key confound closed).** A large α could garble generation, and garbage might trip
refusal keywords. Ruled out three ways: (i) `empty_rate = 0.000` in every cell at every α; (ii) the effect is
already strong at the milder α=8; (iii) **the actual completions were inspected** — the α=8/12 outputs are
fluent, natural refusals, while the norm-matched random control at the same α produces coherent *harmful*
text. So ASR→0 is genuine refusal restoration, not decoder breakage.

⚠ **Control nuance:** the random control is null at α=8 (ΔASR +0.10 to +0.19, p ≥ 0.125), but at the
**matched α=12** a random direction *significantly raises* ASR (+0.27 / +0.33, p ≤ 0.002). The specificity
claim is therefore about *direction of effect* (only the refusal axis ever lowers ASR), which is the relevant
comparison, but "random null" is not literally true at the headline α.

### 8.5 Representational signature — Doublespeak suppresses the refusal axis
Forward-only: project the **last prompt token** residual (the position deciding the first output token) onto
the per-layer refusal direction, for matched direct / doublespeak / neutral prompts.

**clearharm test (n=42)** — `hs` row *h* = post-block *h−1*:

| hs row (~layer) | direct | doublespeak | neutral | direct − ds (95% CI) |
|---|---|---|---|---|
| hs5 (~L4) | 0.20 | 0.21 | 0.22 | −0.02 **ns** |
| hs9 (~L8) | 0.11 | −0.08 | 0.17 | **+0.19 [0.16, 0.22]** |
| hs17 (~L16) | 4.09 | 1.54 | 2.02 | +2.55 [2.0, 3.1] |
| hs25 (~L24) | 7.70 | 0.72 | 2.58 | +6.98 [5.6, 8.4] |
| hs31 (~L30) | 15.19 | 3.65 | 6.94 | +11.54 [9.4, 13.6] |
| hs32 (~L31) | 71.23 | 30.01 | 40.07 | **+41.21 [33.3, 49.4]** |

Curated at hs31: direct 15.55 / ds −1.21 / neutral −1.61.

Verified: the direct−ds gap **grows monotonically from hs9 to hs32 with zero violations in all four cells**,
and the **suppression onsets at ~hs8 (i.e. the L8–11 concept-write band)**.

⚠ Two overstatements corrected: (a) "DS below direct and at/below neutral **at all layers**" fails at
hs1–hs6 in both cohorts, and on **curated** DS sits at-or-*above* neutral through hs16–hs31 (so the "curated
goes negative *below* neutral" phrasing is wrong — it goes negative but stays at/above neutral).
(b) The norm-matched random control is negligible in **magnitude** (≤0.28 vs a 41.2 signal, <1%) but its
bootstrap CI **excludes 0 at 20–25 of 32 layers** — "zero condition gap, CIs straddle 0" is not literally true.

⇒ **The demonstrations, in the same L8–11 band, do two orthogonal things:** remap codeword→concept
(behaviorally inert) **and** suppress the refusal representation (the behavioral driver).

### 8.6 Depth localization — the refusal DECISION is read MID-LATE
**First attempt (fixed α=12) failed, honestly reported.** Because α is an absolute residual magnitude while
residual norm grows with depth, fixed α is over-driven early and under-driven late:

| inject layer | refusal α=12 (ASR / refusal_rate) | random α=12 | verdict |
|---|---|---|---|
| L9 (early) | .000 / 1.00 | **.000 / 0.00** | **CONFOUNDED** — random also kills ASR (without producing refusals) |
| L18 (mid) | .000 / 1.00 | **.619 / 0.00** | **CLEAN** — refusal-specific full rescue |
| L28 (late) | .21–.29 / .64–.67 | ≈ base | specific but **under-driven** |

**Corrected version — calibrated α.** Inject each layer's *own* refusal direction at **α = that layer's
measured direct−ds projection gap** (i.e. restore exactly to the "refused" level): α = 0.470 / 1.968 / 5.106 /
7.590 at L9 / L16 / L22 / L28. Now the random control is null at every layer.

| inject layer (α) | clearharm train (n=44, base .386) | clearharm test (n=42, base .333) | curated train (n=30) |
|---|---|---|---|
| L9 (0.47) | −0.068, p=0.453 **ns** | −0.071, p=0.508 ns | −0.100, p=0.453 ns |
| L16 (1.97) | **−0.205, p=0.0039** | −0.071, p=0.453 ns | −0.133, p=0.180 ns |
| **L22 (5.11)** | **−0.250, p=0.00098** | **−0.167, p=0.039** | **−0.200, p=0.031** |
| L28 (7.59) | **−0.227, p=0.00195** | −0.071, p=0.375 ns | −0.100, p=0.125 ns |

Pooled curated (n=51): L22 −0.137, p=0.0156. curated test is floor-limited (ds_base .095) — all p=1.0.
Random control: |ΔASR| ≤ 0.068, all p ≥ 0.45, at every layer.

⇒ **L22 is the one layer significant in both cohorts, and L9 is null in both.** Doublespeak suppresses refusal
from the early write band, but the **behavioral refusal decision is read mid-late (~L16–L22)** — restoring the
signal only early is not enough. ⚠ The defensible claim is *"L22 significant in both cohorts (train), L9 null
everywhere"* — **not** the reports' "L16/22/28 significant, both cohorts," which holds only on clearharm train.
Rescue is *partial* (not →0) because the calibrated α is a minimal restore-to-refused push.

### 8.7 WRITE × REFUSAL — the two pathways are causally INDEPENDENT (the mechanistic *why*)
Ablate the L8–11 concept write, then measure the refusal-axis projection (forward-only):

| cell | positive control: p_concept before → after | drop 95% CI | refusal `frac_of_direct_gap_restored` |
|---|---|---|---|
| clearharm train | 0.884 → 0.799 | [0.042, 0.143] ✓ | −0.023 … +0.015 |
| clearharm test | 0.858 → 0.817 | [0.013, 0.085] ✓ | −0.017 … +0.025 |
| curated train | 0.811 → 0.751 | [0.030, 0.092] ✓ | −0.050 … +0.011 |
| curated test | 0.690 → 0.457 | [0.126, 0.348] ✓ | −0.010 … +0.019 |

⇒ **The positive control fires in all four cells** (the write ablation really does reduce the concept readout),
yet the refusal suppression is **completely unmoved**: at every one of 128 layer-cells the restoration is
within **|0.05|** of the gap it would need to close, and where significant it is *negative* (moving further
from refusal, not toward it). Verified that the hook actually fired (per-item |ds_writeabl − ds_base| reaches
23.7 — this is not a dead hook).

⚠ Two corrections: the reports' per-cell ranges are all **understated** (true ranges above), and
"CIs include 0 throughout" is **false** — 33 of 128 layer-cells are significant (21 consecutive layers on
curated train), though all are negative and ≤5% of the gap. The correct statement is the **fractional** one.

> **This is why the concept circuit is behaviorally epiphenomenal:** the demonstrations' two L8–11 effects run
> on separate pathways, and knocking out the remap does nothing to the refusal bypass.

### 8.8 Item-level link — the refusal projection PREDICTS which prompts jailbreak
Join each Doublespeak item's decision-token refusal projection (decoder L21 / hs22) with its `ds_base`
StrongREJECT outcome (no new GPU work — a join of two committed runs, full id overlap):

| cohort | n (malicious) | median proj: jailbroken | refused | **AUC** | Mann-Whitney p | point-biserial r |
|---|---|---|---|---|---|---|
| **clearharm** | 86 (32) | **−1.15** | **+3.60** | **0.874** | **3.8e-09** | **−0.584** |
| curated | 51 (11) | +0.28 | −0.49 | 0.42 (ns) | 0.79 | +0.015 (ns) |

Robustness (all reproduced): AUC stable **0.844–0.888 across hidden-state rows 17–32** (all p < 1e-7);
**5-fold cross-validated AUC = 0.887 ± 0.106** (out-of-sample ≥ in-sample).
⚠ Two things the report omits: the headline AUC is computed on the **pooled** cohort, not the locked test
(it does hold per split: **train 0.867, locked-test 0.891**), and **no CI is given** — the audit computed
bootstrap 95% CI **[0.797, 0.940]**.

⇒ **The items Doublespeak jailbreaks are precisely those it most suppresses on the refusal axis.** This
directly explains the partial base ASR (~0.36) and identifies **two sources** for it:
1. **Under-suppression (clearharm)** — DS suppresses refusal unevenly; the under-suppressed items refuse.
2. **Concept-dilution (curated)** — suppression is *uniform* (std 1.84 vs 3.51), so the projection cannot
   discriminate; the limiter there is that the codeword remap makes the answer benign, failing the harm judge.

### 8.9 Trajectory — the outcome is fixed at the DECISION POINT, not re-engaged mid-generation
Track the refusal projection along generated tokens (first 40 steps, layers 18 and 30), split by outcome
(clearharm test, n=42, 19/42 = 0.452 of DS generations refuse):

| condition | projection @ token 0 (L30) | trajectory |
|---|---|---|
| Direct harmful (refuses) | **13.6** | high → decays as refusal text is emitted |
| Doublespeak → **refuses** | **9.1** (≈ Direct) | high → decays |
| Doublespeak → **jailbreak** | **−2.1** | stays low/negative throughout (never rises above its token-0 value) |

**Zero crossings** between the two DS trajectories across all comparable steps, at both L18 and L30.
Item-level token-0 separation: AUC 0.936 (test) / 1.000 (train).

⇒ The author's own earlier hypothesis — that refusal *re-engages* mid-generation — is **falsified**. The
outcome is set at the decision position.
**curated confirms the second mechanism**: `ds_refused_rate = 0.000` on **both** splits — *zero* refusals —
yet ASR is only ~0.10. Its non-jailbreaks are not refusals; they are benign codeword-dilution outputs.

### 8.10 Consolidated behavioral table (audit-corrected)

| # | Claim | Effect (clearharm) | Effect (curated) | Significance | Control | Verdict |
|---|---|---|---|---|---|---|
| 1a | Carry heads behaviorally inert | ΔASR +0.09 tr / +0.07 te | −0.10 / 0.00 | McNemar p ≥ 0.289 | random-head ≈ +0.02 | **NULL** |
| 1b | L8–11 write behaviorally inert | ΔASR −0.02 / 0.00 | +0.07 / 0.00 | p ≥ 0.688 | random-pos ≈ 0 | **NULL** |
| 2 | Refusal ablation **sufficient** (> DS) | .568/.548 vs base .136/.071 (Δ+.43/+.48) | .700/.714 vs .267/.286 (Δ+.43/+.43) | p = 4e-6 … 3.9e-3 (all ≤ .004) | random-dir null (p ≥ .5) | **CAUSAL** |
| 3 | Refusal re-injection **necessary** | ds .386/.381 → **.000** @α12 | .333/.095 → **.000** | p = 1.5e-5 … 2.0e-3 **(curated-test p=0.50, ns)** | random @α8 null; empty=0; coherence-audited | **CAUSAL** |
| 4 | DS **suppresses** the refusal axis | proj@hs31: direct 15.19 / ds 3.65 / neutral 6.94 | 15.55 / −1.21 / −1.61 | onset ~hs8, monotone growth (0 violations) | random-dir <1% of signal (but CI≠0 at 20–25/32 layers) | **CONFIRMED** |
| 5 | Refusal decision read **mid-late** | L22 ΔASR −0.250 (p=.001) tr, −0.167 (p=.039) te; L9 ns | L22 −0.200 (p=.031); L9 ns | **L22 sig in both cohorts; L16/L28 sig on clearharm train only** | random-dir null all layers | **CAUSAL** |
| 6 | Concept-remap ⊥ refusal-suppression | p_concept .884→.799 (control fires); frac_restored ∈ [−.023,+.025] | .811→.751 / .690→.457; frac ∈ [−.050,+.019] | control CIs exclude 0; frac ≤ 5% of gap everywhere | positive control (p_concept) | **INDEPENDENT** |
| 7 | Refusal proj **predicts** jailbreak | **AUC 0.874** (pooled; train .867 / test .891), r=−0.584 | null (AUC .42) → concept-dilution | MW p=3.8e-9 / p=.79 | 5-fold CV AUC .887; stable L17–L32 | **PREDICTIVE (clearharm)** |
| 8 | Outcome set at **decision point** | token-0 L30: jailbreak −2.1 vs refused 9.1 vs Direct 13.6 | ds_refused_rate = **0.000** | 0 trajectory crossings | outcome-split | **DECISION-POINT** |

---

## 9. Phases 10 & 11 — objective distillation and the GCG null

### 9.1 Phase 10 — Gate-6: 9/10 pass, **sufficiency fails**
The candidate `concept_objective` (the L9-write handle) was scored against the plan's 10 eligibility criteria:

| # | criterion | verdict | evidence |
|---|---|---|---|
| 1 | changes under validated intervention | pass (definitional) | the target *is* the intervention |
| 2 | manipulating it changes interpretation | pass | Phase 6 necessity |
| 3 | necessity demonstrated | **pass** | L9 Holm-sig on all 4 cells |
| **4** | **sufficiency demonstrated** | **FAIL** | `S3_install − S_random` ≤ **+0.014** at *every* one of 32 layers |
| 5 | dose response exists | **pass** | Phase 9 monotone on α ∈ [0,1], 8/8 cells |
| 6 | replicates on ≥20 locked test | pass | heldout n = 21 / 41 / 55 |
| 7 | random/unrelated controls fail | pass | random_control ≈ 0 (mean \|Δ\| 0.001–0.011) |
| 8 | not general degradation | pass | broad early-window +0.42 flagged as degradation (negative sufficiency −0.17); clean per-layer L9 used instead |
| 9 | distinct from global refusal removal | pass | \|cos(concept, refusal)\| ≤ 0.153 at every layer |
| 10 | transfers across conditions | pass | 2 cohorts × 2 splits |

**`doublespeak_signature` is KILLED** — the best-supported negative in the sprint. Adding the d_DS direction at
matched relative strength moves the reading by at most **1e-05** (9 control cells) and **3e-05** (175 dose
cells), whereas adding d_Direct moves it **+0.167 / +0.533 / +0.971** (early / mid / late). The observational
DS−neutral difference vector is causally inert.

### 9.2 Phase 11 — **the 13-arm GCG/MAC matrix was DESIGNED but NEVER RUN**
This is the single most important honesty item in the sprint.

- **0 of 13 arms executed.** No GCG artifact newer than 2026-07-29 exists; no Llama/ClearHarm GCG manifest
  exists. Even the phase's own scaled-down "decisive minimal test" (arm G1: behavioral sufficiency of the
  concept install) was planned and then never launched.
- The phase was **concluded as a null from three lines of pre-existing evidence**:
  1. **State injection is only weakly behaviorally sufficient** — max malicious rate **0.164** across all Llama
     sufficiency runs (0.098 at the full 37-base set). ✔ verified on the model under study.
  2. **A mechanism-derived GCG objective was net-negative** — held-out ASR: no-attack 0.077 (1/13), baseline
     GCG 0.000, temporal objective 0.000; refusal rate rose 0.000 → 0.615 under the temporal objective, and
     `repr_loss` never dropped across three configs (it is not suffix-optimizable).
     ⚠ **This run was on Qwen3-14B, not Llama-3.1-8B**, and it used a *temporal mixed-cache* objective — **not**
     a d_DS objective, contrary to how the report describes it.
  3. **Gate-6 sufficiency failure.** ✔ verified.
- A supporting dissociation *is* verified: representational decoding-sufficiency does not predict — and here
  **inverts** — behavioral sufficiency (DS − Direct = −0.393 [−0.470, −0.311], n=183 at mid depth).

⇒ **Gate 7 was never tested.** The claim "the mechanism does not convert into a token-suffix attack objective"
is a reasoned inference from converging prior evidence, **not a result of this sprint**. Treat it as a
well-motivated hypothesis, not a measured null.

---

## 10. Audit findings — where the in-repo reports are wrong

The 14-agent verification found **43 mismatches**. None overturns a headline conclusion, but several matter for
anyone quoting numbers. The most consequential:

### 10.1 Statistical corrections made *during* the sprint (already fixed in-repo)
- **Permutation → Wilcoxon (HIGH).** Per-layer/head significance used a sign-flip permutation whose resolution
  floor (5.0e-5) was coarser than the 1024-cell Holm threshold (4.88e-5) and could return p=0. The Phase-5
  headline "60–75 Holm-significant heads" was a **p=0 artifact**; re-derived under Wilcoxon it is
  **58 / 0 / 31 / 31**. Phase 6 was re-derived and **held** (L9 survives on all 4 cells). Qualitative
  conclusions unchanged.
- **Phase 5b Q/K/V result RETRACTED (HIGH).** The reported "clean null" for answer-position Q/K/V necessity is
  **INCONCLUSIVE**: under causal masking K/V are read from *earlier source positions* that were never patched
  (a pure positioning artifact), there was no positive control, and the only run was an n=2 smoke. Retracted in
  the FINAL report and in the script's own docstring. **Do not cite it.**
- **Delivered figure had mislabels.** `figures/circuit_summary.png` Panel B labelled the L9 MLP-write value as
  "head-output necessity" and annotated an unsourced "mediation 0.79". Fixed to the sourced 0.75–0.83 range and
  re-rendered *after the wrong version had already been delivered*.

### 10.2 Overstated scope (claim direction right, stated range wrong)
| report claim | corrected from raw |
|---|---|
| demo-KV necessity "L8–L11, both cohorts, each CI excludes 0" | **L8–L10** on both cohorts; clearharm L11 CI = [−0.033, +0.079] includes 0 |
| "window neutralization exceeds any single layer" | only true for curated-early; the other 3 windows are **below** their best single layer |
| Phase 8 projection "grows monotonically" | **non-monotone** — 11–14 of 31 steps decrease; correct: flat/noisy then a terminal L31 spike |
| Phase 6b "saturates at W8; wider adds nothing" | best W8 (L2–9) = +0.192/+0.193, **1.7× the best W4** |
| query-codeword MLP "inert / nothing survives Holm" | on **clearharm**, L9/L15/L20 survive Holm on both splits (3–4× weaker than demo, not absent) |
| DS projection "below direct and at/below neutral at ALL layers" | fails at hs1–hs6 both cohorts; on **curated** DS is at/above neutral through hs16–hs31 |
| refusal random control "null at every layer / CIs straddle 0" | magnitude <1% of signal, but CI excludes 0 at **20–25 of 32** layers |
| WRITE×REFUSAL "Δ CIs include 0 throughout" | **33 of 128** layer-cells are significant (all negative, ≤5% of gap) — use the fractional statement instead |
| WRITE×REFUSAL per-cell frac ranges | all four understated; true: [−0.023,+0.015], [−0.017,+0.025], [−0.050,+0.011], [−0.010,+0.019] |
| calibrated depth "L16/L22/L28 sig, both cohorts" | **only clearharm train**; defensible claim = **L22 sig in both cohorts, L9 null everywhere** |
| refusal re-injection "p = 2e-5 … 2e-3" | curated **test is p=0.50 (ns)** — dropped from the stated range |
| "refusal-ablation ≥ DS, significant on 3/4" | significant on **2/4** at α=.05 (4/4 only at α=.10); the 3/4 came from a preempted run |
| Gate-6 #9 "cos(concept,refusal) 0.01–0.06 at every layer" | those are the **means**; correct is **\|cos\| ≤ 0.153 at every layer** |
| Table 1 header "all numbers verified, zero transcription errors" | **not true** — 6 table claims did not match raw as stated |
| split contract "curated ~9 train / 8 test clusters" | **10 train / 7 test** |

### 10.3 Missing statistics / controls
- **Phase 9 has no inferential statistics at all** (no CI, no p-value) — the dose claim is the ordering of
  5 point-means per cell.
- **Phase 4b uniform-KO has no specificity control** — an arbitrary non-candidate head's pattern already
  produces most of the effect.
- **Phase 7b mediation** rests on the L9-responsive subset, **n = 9–13**, below the ≥20 mandate; the quoted
  "75–83%" excludes the fourth cell (1.459).
- **Phase 7d's count-matched random control was added by audit *after* the runs and has never been executed.**
- **Phase 3's random control was applied to the neutral receiver, not the DS receiver**, and has no CIs.
- **BEHAV-CARRY / BEHAV-WRITE random controls are a single fixed seed-0 draw**, not a distribution.
- Neither WRITE×REFUSAL nor TRAJECTORY has a negative/placebo control.

### 10.4 Run-selection and reproducibility
Several conditions have multiple run directories (preemptions, restarts). The audit identified the
authoritative complete run for each cell. Notably, **the same `ds_base` condition yields test-split ASR
between 0.286 and 0.381 across four runs** under greedy decode (train 0.386–0.409) — up to ~10 pp of
run-to-run drift. This is larger than the "1–2 examples/cell" the report claims and **bounds the precision of
every 2-decimal ΔASR**. It does not threaten the ±0.43 effects, but sub-0.10 effects should be read with it in
mind. (Each comparison is paired *within* its own run, so the drift does not bias the paired tests.)

### 10.5 What the audits caught during the sprint (20 distinct bugs/corrections)
Two formal multi-auditor workflows ran: **wvrceb4zt** (20 findings: 2 high, 4 medium, 14 low — all resolved)
and **ww3tvlc9z** (15 findings: 2 high, 4 medium, 9 low — all resolved). Self-caught issues included:
the split builder silently dropping multi-token-codeword items (curated 19 → 51 records); a cross-split
prompt-leakage bug; **two independent token-index-vs-char-offset bugs** (edge-KO produced 0 rows; the Phase-6
demo/query split silently included 2 question codewords and emptied the query set — fixing it deflated a
heldout L9 effect from .18 to .097, removing a ~2× inflation); a necessity random-control sourced from the
wrong donor (inflating a clearharm effect to spurious significance); a pooled-CI aggregation that violated the
train/test mandate; a readout that measured the wrong thing entirely (patchscope instead of forced-choice); a
stale-code smoke test; four SLURM wrapper bugs; and a transient node-level cgroup failure correctly diagnosed
as infrastructure rather than code.

---

## 11. What was NOT done (open items, blunt)

1. **Phase 11 / Gate 7: the 13-arm GCG/MAC matrix was never run** — nor was its own minimal G1 test. The
   "objective does not improve ASR" conclusion is inferred, not measured.
2. **No cross-architecture replication.** Everything is Llama-3.1-8B-Instruct. Qwen3 was flagged as future work
   and explicitly held pending direction.
3. **Carry-head sufficiency was never tested behaviorally** — the +0.16–0.47 install is representational
   (forced-choice) only.
4. **The granularity mandate A–G was met for exactly one intervention family** (MLP-out necessity,
   143 windows), and only for necessity (no sufficiency arm). Head z-patching ran granularity A only;
   edge-knockout ran A plus one band; the pattern knockout ran only on the carry set; **the refusal
   interventions ran at 3–4 hand-picked layers out of 32** and never as windows. The plan's required
   **concept-granularity × refusal-granularity factorial was never run.**
5. **All 7 machine-readable cell manifests are missing** — `configs/manifests/` is empty. Consequently the
   coverage validator can only check dirs that exist; it can never detect a cell that was never launched.
6. **The coverage validator supports only the phase5/phase6 schemas** and **crashes (KeyError) on every
   behavioral output dir** — so *none of the sprint's headline behavioral results is covered by the
   plan-mandated coverage validation*, despite the FINAL report implying otherwise.
7. **Phase 3 covered ~5 of ~80** layer × location × position-set combinations. Never run: each demo occurrence
   individually, every query occurrence, target-concept occurrences in direct prompts, unrelated-noun and
   punctuation controls.
8. **Phase 2.1 ran 3 of 10 conditions** (direct / neutral / doublespeak). The benign, shuffled-binding and
   unrelated-binding behavioral conditions were never run, even though those rows exist in the bench.
9. **Phase 7 never swept sender-head × receiver-MLP** — 10 heads were freeze-tested, and no head×MLP matrix
   exists.
10. **The plan's 12 mandatory plot types per family were not produced** — 6 summary/publication figures exist
    in total.
11. **Mandate deviation:** the headline refusal-ablation arm applies **one L18 vector across all 32 layers**
    (standard Arditi ablation), which the plan explicitly forbids. The later calibrated harness does use each
    layer's own direction, so the deviation is confined to the sufficiency arm.
12. **Phase 9's dose grid omitted α=3.0**, and dose-response was run for 2 of ~7 intervention families rather
    than "every main causal intervention".
13. The in-repo `IMPLEMENTATION_PROGRESS.md` **structured trackers are stale** (they still show Phases 4–11 as
    "not started" and all 7 gates unchecked) — trust the narrative log and this document instead.
14. **Test suite:** 19 files / 115 test functions; last reported state "113 pass". This could not be
    re-executed in the audit environment (no torch), so the pass count is reported, not reproduced.

---

## 12. Artifact index

**Reports** (`doublespeak_causality/reports/`): `CAUSAL_PATCHING_AUDIT.md`, `DATASET_AND_SPLIT_CONTRACT.md`,
`PHASE2_{BEHAVIORAL,DIRECTIONS}.md`, `PHASE3_RESIDUAL.md`, `PHASE4_DEMO_RETRIEVAL.md`, `PHASE4B_PATTERN.md`,
`PHASE5_HEADS.md`, `PHASE6_MLP.md`, `PHASE7_PATH.md`, `PHASE8_READOUT.md`, `PHASE9_DOSE.md`,
`CAUSAL_OBJECTIVE.md`, `GCG_MAC_EVALUATION.md`, `PHASE_BEHAV_{CARRY,WRITE,REFUSAL}.md`,
`PHASE_WRITE_REFUSAL_INTX.md`, `PHASE_REFUSAL_TRAJECTORY.md`, `REP_PREDICTS_BEHAVIOR.md`,
`BEHAVIORAL_RESULTS_TABLE.md`, `FINAL_CAUSAL_CIRCUIT_REPORT.md`, `SLACK_UPDATE.md`.
Paper draft: `PAPER_CONTRIBUTION.md` (CAUSAL_CIRCUIT addendum + drop-in abstract).

**Figures** (`figures/`): `circuit_summary.png`, `behavioral_dissociation.png`, `refusal_depth_mechanism.png`,
`causal_decoupling.png`, `refusal_trajectory.png`, `rep_predicts_behavior.png`.

**Key harnesses** (`scripts/`, each with a `slurm/` wrapper): `phase3_demo_neutralize.py`,
`phase4_edge_knockout.py`, `phase4b_pattern.py`, `phase4c_carryedge.py`, `phase5_head_zpatch.py` (+`_analyze`),
`phase5b_qkv.py` *(retracted)*, `phase6_mlp_causal.py` (+`_analyze`), `phase6b_windows.py`,
`phase7_direct_total.py`, `phase7b_mediation.py`, `phase7c_sufficiency.py`, `phase7d_onset.py`,
`phase8_readout.py`, `phase9_dose.py`, `phase_behav_{carry,write,refusal,refusal_inject}.py`,
`phase_refusal_{projection,inject_calibrated,trajectory}.py`, `phase_write_refusal_interaction.py`,
`analyze_rep_predicts_behavior.py`, `validate_data_integrity.py`, `validate_experiment_coverage.py`.

**Primitives** (`pair_common.py`): `SubmodulePatch` (with resid_pre), `ComponentOutSwap`,
`AllPositionZHeadAblate`, `AttentionKnockout`, `ZHeadPatch`, `AllPositionProjectOutMultiLayer`,
`AllPositionAdd`, `norm_matched_random`.

**Data**: `data/splits/clearharm_doublespeak_v1.json` (locked, 137), `data/bench/bench_{clearharm,curated}.json`,
`data/bench/bench_clearharm_v2.json` (116), `data/behavioral/beh_{clearharm,curated}.json`.

**Authoritative run directories** for the headline behavioral results:
`behav_carry_clearharm_20260804_100009_707831`, `behav_carry_curated_20260804_100428_707832`,
`behav_write_clearharm_L8_9_10_11_20260804_110157_707908`, `behav_write_curated_..._707909`,
`behav_refusal_clearharm_a1.0_20260804_133355_708038`, `behav_refusal_curated_a1.0_20260804_125055_708039`,
`behav_refinject_clearharm_L18_20260804_141615_710769`, `behav_refinject_curated_L18_20260804_142104_710770`,
`refproj_clearharm_20260804_162641_711392`, `refproj_curated_..._711393`,
`refinject_cal_clearharm_..._711685`, `write_refusal_intx_{clearharm,curated}_20260804_2316xx_71188{7,8}`,
`refusal_traj_clearharm_..._711956`, `refusal_traj_curated_..._711957`.

---

## 13. Bottom line for an external reader

**What is solidly established (cross-cohort, locked-test, controlled, recomputed from raw):**
1. A complete, distributed **concept circuit** for Doublespeak on Llama-3.1-8B: demo-KV retrieval L8–L10 +
   an L9 MLP write → L14–L21 mediated carry heads → L30–31 proximal output. Necessity is Holm-significant at
   every stage; the carry stage is additionally **partially sufficient** (+0.16 to +0.47).
2. **Readout ≠ mechanism**: linear readability peaks at L31 while causality sits at L9/L14–21.
3. **The concept circuit is behaviorally inert** — ablating either control site through harmful generation
   leaves ASR statistically unchanged.
4. **A single orthogonal refusal direction is behaviorally necessary AND sufficient** — ablate it and ASR rises
   +0.43–0.48 (a *stronger* attack than Doublespeak); re-inject it and ASR goes to 0.000 with fluent refusals.
5. **The two pathways are causally decoupled** — ablating the concept write moves the refusal suppression by
   ≤5% of the relevant gap.
6. **The refusal decision is read mid-late (~L22)** even though the suppression starts at the L8–11 write band,
   and the outcome is **fixed at the decision token**, not re-engaged during generation.
7. **Partial ASR has two identified sources**: uneven refusal suppression (predicted per item at AUC 0.874) and
   concept-dilution (curated: 0% refusals yet low ASR).
8. **`doublespeak_signature` is causally inert** (effect ≤ 3e-05) — the observational difference vector is not
   a mechanism.

**What is NOT established:** anything about other model families; whether the mechanism yields a usable
black-box attack objective (Gate 7 untested, 0 of 13 GCG arms run); behavioral sufficiency of the carry heads;
and full coverage at the granularities the plan demanded.

**The one-line takeaway:** *Doublespeak is an imperfect in-context refusal-suppression technique; the elaborate
token→concept remap is a causally-decoupled, behaviorally epiphenomenal bystander. Defend the refusal axis, not
the concept subspace.*
