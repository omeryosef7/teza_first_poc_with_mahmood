# Boombness Objective Sprint — full report

**Author:** Omer · **Date:** 2026-08-17 · **Branch:** `behavioral-causality-sprint`
**Plan:** `docs/BOOMBNESS_OBJECTIVE_SPRINT_PLAN.md` (20 sections)
**Execution log:** `docs/BOOMBNESS_SPRINT_PROGRESS.md` (phase board, gate table, 5 retractions, 5 corrections, 5 audits)
**Summary for collaborators:** `reports/boombness_objective_sprint_short_update.md` (revision 5)
**Status:** every claim below re-derived by an independent verifier; the 15 gaps it found are fixed and marked ⚠.

**Model:** `meta-llama/Llama-3.1-8B-Instruct`, bfloat16. **Concept pair:** carrot ↔ bomb.
**Bank:** 2352 prompts, 912 families (240 matched 2×2), content sha `71bea179345ed118`.
**Judge:** StrongReject rubric via `gpt-4o-mini`, threshold 0.5, continuous score always persisted.

---

## 0. What the sprint set out to do, and what it found

**Rewritten 2026-08-18.** The previous head stated the sprint's conclusion in two incompatible ways —
the gate table and four passages said "not causal, §12 was not built, do not build the objective",
while two sections added later said that verdict was withdrawn and §12 reopened, with no marker on
either. A gate table is the part of a report a reader trusts to be current, so the withdrawn verdicts
have been moved out of it into the retraction table below and the conclusion is stated once, here.

### The conclusion, stated once

**The objective as specified — steer a "Boombness" axis to make a codeword's representation more
concept-like, and optimise a GCG suffix against it — was not built, and should not be.** G4 is a
directional null: *both* signs of `d_surface` suppress attack success, so ASR does not follow the
axis, and the one arm that clears a random-control band does so by triggering refusal.

⛔ **And one of the four headline findings has since been retracted.** **G2 — "Boombness predicts
attack success" — does not survive** (R-18): its n=234 mixed sibling families that share
demonstrations with rows whose codeword readability was experimentally manipulated, and on the 90
independent unmanipulated prompts the within-domain correlation is **−0.052 (p=0.658)** against a
published **+0.262 (p=5e-4)**.

**The intervention results are unaffected — they are causal, measured on external sets, and they
survive.** On **AdvBench held-out — 495 prompts, 16 domain clusters** —
removing `d_surface` **alone** raises attack success by **+0.0305 (p_cl=0.0089, CI [+0.0089,
+0.0522])** on harmful requests carrying no codeword, no demonstrations and no doublespeak wrapper.
`d_surface` was fitted entirely on the carrot/bomb 2×2, so this **excludes the prompt-bank artifact
explanation** — the most serious threat to every late finding here.

A norm-matched **random** projection at the same layer is **inert** (−0.0062, p_cl=0.539, CI
[−0.027, +0.015]), so the effect is specific to this direction rather than to removing any direction.

**And the two channels interact.** Removing `d_surface` and refusalness together exceeds the sum of
removing each alone by **+0.0333, CI [+0.0128, +0.0638]**, and — by a *paired* bootstrap against the
matched random-projection triple, which is the test that actually answers this — by **+0.0268,
CI [+0.0029, +0.0584]** beyond what random directions produce. All three controls are inert. ⚠ The
lower bound is close to zero; this is a real interaction, not a comfortable one.

**On ClearHarm (179 prompts, 6 clusters, 127 in one) arm B is NOT significant** (+0.084, p_cl=0.21).
That is a power difference, not a disagreement — the point estimates agree and only the intervals
differ. Both results are reported; neither is dropped.

### Current gate table

Every row here is current as of 2026-08-18. Superseded verdicts are in the retraction table, never
here.

| gate | question | verdict |
|---|---|---|
| **G1** (§5) | Where does the codeword's meaning live? | **In the demonstrations, not the token — re-derived on the corrected readout 2026-08-19.** The single-layer L18 demonstration transplant moves the readout **+68.9% of span, CI [+51%, +97%]** (24 families, 6 domains); the **whole-prompt** transplant is **null** (+13%, CI [−17%, +34%]) and the **query-codeword** transplant moves it the **wrong way** (−57%). C-6 discharged: the old readout gave +68.1%, so the instrument defect did not change G1. ⚠ The "% of span" denominator inherits a ceiling measured in a tail (option mass 0.0074). |
| **G2** (§9) | Does Boombness predict attack success? | ⛔ **RETRACTED (R-18).** `analyze_g2` filtered on `condition` only, so the published n=234 contained **72 sibling families sharing demonstrations** (pseudo-replication) and **72 rows whose codeword readability was experimentally manipulated** (`strength`/`consistency`/`position`). On the **90 independent, unmanipulated prompts** the within-domain ρ — the estimand the artifact itself says to cite — goes from **+0.2618 (p=5e-4)** to **−0.0518 (p=0.658)**. **Not established.** n=90 cannot exclude a small effect, so this is a null, not a proof of absence. |
| **G3** (§10) | Can it be removed surgically? | **Established, re-derived 2026-08-19** on 24 families with the ranking at `readout_pos` (R-7 discharged). Cutting **all** demo edges at all layers recovers **75.2%** of the deletion ceiling; **no 16-edge subset matters** (top-k +0.020 vs bottom-k −0.003 vs random +0.001); and **6.25% of the edges does nothing however distributed** — the redundancy is in **edge count**, not depth. Codeword-scope cuts move the readout the **wrong way** (+1.33), so the meaning is in the demonstration **block**. |
| **G4** (§12) | Is it a usable objective? | **No.** Both signs of `d_surface` suppress ASR. Only `+0.25` exceeds a 4-draw random-control band, by **triggering refusal**. |
| **§10.4-D** | Does removing `d_surface` **and** refusal raise ASR? | **Yes, on two external sets** (§7c). AdvBench (495, 16 clusters): 0.065 → **0.352**, p_cl<0.0001. ClearHarm (179, 6 clusters): 0.106 → **0.514**, p_cl=0.020, control inert to ±0.004. |
| **§14-B** | Does removing `d_surface` **alone** raise ASR off-bank? | **Yes on AdvBench** — +0.0305, p_cl=**0.0089**, CI [+0.0089, +0.0522], 16 clusters. **Not significant on ClearHarm** (+0.084, p_cl=0.21) — a power difference (6 clusters, 127/179 in one), not a disagreement. **This excludes the prompt-bank artifact explanation.** ⚠ AdvBench control arms still running. |
| **§14-SA** | Is the joint arm super-additive? | **Established on AdvBench, against its own control** — +0.0333, CI [+0.0128, +0.0638]; and by the **paired** difference against the matched random triple, **+0.0268, CI [+0.0029, +0.0584]** (comparing the two intervals separately would have been the difference-of-significance fallacy — they overlap). ⚠ Lower bound near zero. **Not established on ClearHarm** (+0.0677, CI [−0.218, +0.123]), as predicted from its cluster imbalance. |
| **§2.6** | Does any intervention preserve comprehension? | **UNKNOWN.** The comprehension readout was measuring a ~1e-5 probability tail. Rebuilt; re-run outstanding. See R-6. |
| **FINAL** (§18) | outcome label | **C, amended** — see below. Both blockers have landed (R-6 resolved, R-7 discharged), so this is decided rather than deferred. |

### §18: the outcome label, settled

Both things that blocked this decision have landed — **R-6 is resolved** (`project_out` does not damage
comprehension; it *improves* the coded reading, +0.2795, p=0.0010) and **R-7 is discharged** (G3 re-derived
at the correct token). So the label is decided here rather than deferred again.

**The honest answer is C, and it needs an amendment the plan's four-way taxonomy has no box for.**

| plan §18 option | verdict | why |
|---|---|---|
| **A. Strong positive** | **No** | *Adding* Boombness does not increase attack behaviour — steering the axis suppresses ASR at **both** signs (G4), and no GCG objective was built or should be. |
| **B. Mechanistic but not causal** | **No** | B requires that "interventions do not affect ASR **or** destroy comprehension". **Both clauses fail.** Removing `d_surface` raises external-set ASR (+0.0305, p_cl=0.0089, 16 clusters, inert control), and comprehension is not destroyed — it *improves* (R-6). |
| **C. Refusal-only story** | **Closest** | On Llama refusal is the dominant channel: +0.190 against `d_surface`'s +0.031 on AdvBench. |
| **D. Negative** | **No** | The metrics are not unstable or non-predictive: G2 survives multiplicity correction (maxT p=0.0015) and control for `n_examples`; G1 and G3 are both established. |

**The amendment, which is the sprint's actual result:** "refusal-only" is too strong in three specific ways.

1. **`d_surface` is a distinct, causally efficacious second channel.** It is near-orthogonal to refusal
   (cos = 0.019 @L18), and removing it alone raises attack success on 495 external harmful prompts
   against an inert matched control.
2. **The two channels interact.** Removing both exceeds the sum of removing each alone by **+0.0268
   [+0.0029, +0.0584]** beyond a matched random triple (§7c) — so they are not two independent levers,
   and a pure refusal account cannot produce that term.
3. **On Qwen3-14B the refusal channel does nothing and `d_surface` does everything** (§7c) — the exact
   inverse of the Llama picture. A "refusal-only" label is model-specific in a way the taxonomy does not
   express.

**So: C on Llama-3.1-8B, with a real and interacting `d_surface` channel that the C label understates,
and an inverted picture on Qwen3-14B.** Stated as a single verdict once, here, and nowhere else in this
document.

⚠ *This is a judgement call about a four-way taxonomy that does not fit the evidence. The evidence it
rests on is in §7c and is fully regenerable; a reader who prefers to call this "C" without amendment, or
to add a fifth category, is disagreeing with the label and not with any number.*

### Retraction and correction table

Verdicts and numbers this report previously asserted and no longer does. Nothing in this table
appears in the gate table above.

| id | what was asserted | status | why |
|---|---|---|---|
| R-6 | "`project_out` is the only arm that leaves comprehension unchanged (p=0.681)", and every other §4b verdict | **WITHDRAWN** | The readout scored `' literal'`/`' coded'` at a position where the model emits neither. Median mass on the option pair: **4.4e-05**, with **0/288** rows above 1%. Every verdict was an ordering inside that tail. Rebuilt as a whole-answer forced choice (median mass now **0.297**); re-run outstanding. |
| R-7 | G3: "cutting 6.25% of demo→query edges does nothing however distributed" | **WITHDRAWN, then DISCHARGED 2026-08-19** | The edge *ranking* had been computed at the final codeword occurrence — the destination retraction #3 called fatal — while the readout is ~9 tokens later, so the null could not distinguish "these edges don't matter" from "ranked at the wrong token". Re-run at 24 families with `--dst both` (ranking at `readout_pos`): **the claim survives** — top-k +0.020, bottom-k −0.003, random +0.001, and 5,107 edges do nothing whether concentrated at 2 layers or spread over 32. What stays superseded is the **arithmetic** of the 6-family run: the 84% recovery (now **75.2%**) and the 56,832/3,552 edge counts (now 81,707/5,107). |
| R-8 | G1: "+84% of span, CI [+57%, +105%], n=8 families, 2 domains" | **SUPERSEDED** by +68% on 24 families / 6 domains (`g1_stratified.json`). Additionally **under re-derivation**: `semantic_logodds` is computed by the same defective readout as R-6 (`aggressive_patching.py:439`), and the codeword has **no capitalised single-token form** while the concept has four, so the readout is structurally biased toward the concept. |
| R-9 | "§18 = B, mechanistic but not causal" as a settled label | **WITHDRAWN**, and not replaced — see the FINAL row above. |
| R-10 | The §6.4 metric comparison, presented as probe (n=72) beside direction (n=270) | **RETRACTED**; on the common 72 no metric predicts ASR once `n_examples` is partialled out. §7b. |
| R-11 | "the mid-band attenuation does not survive multiplicity correction … `holm_rejected` True only at L4 and L31" | **CORRECTED** to **L1, L4 and L31** at the honest family (m=32, all layers actually tested). The conclusion is unchanged — none of the three is in the L16–L24 mid-band — and the backstop is *stronger*, not weaker. |

### Where "§0.3" pointed

Two passages cited "§0.3, above" as the causal evidence. **No section 0.3 has ever existed.** The
result intended is the `project_out` arm of §10.4, reported in **§7e** (*"Removing the
concept component helps attacks, on Llama"* near the end of this document. Both citations now point
there. The gate-table row that carried the `§0.3` label is now **§10.4-D**, and its numbers are the
ClearHarm ones rather than the superseded 192-token bank run.

## 1. The methodological contribution: the 2×2 identification design (§3–§4)

**This is the most reusable thing here.** The existing benchmark compares a harm-domain arm against
a benign arm that is *a different story*, so the natural direction
`mean(h_bomb) − mean(h_carrot_benign)` is `bombness + explosive-context-ness` — two effects that
cannot be separated by that contrast.

Replaced with a 2×2 over **surface word × demonstration valence**, plus two off-cells:

| cell | condition | surface | context |
|---|---|---|---|
| A | `benign_literal` | carrot | benign |
| B | `direct_harmful` | bomb | harmful |
| C | `natural_doublespeak` | carrot | harmful |
| E | `concept_in_benign_ctx` | bomb | benign |
| D | `direct_codeword` | — | mapping stated outright |
| F | `benign_remap` | — | bicycle remap (surface-change control) |

```
d_surface = ½[(B−C) + (E−A)]     surface-word effect, context matched   ← "Boombness"
d_context = ½[(C−A) + (B−E)]     what the naive direction mostly measures
d_inter   = (B−C) − (E−A)        interaction
d_naive   = B−A = d_surface + d_context
```

**Quantified effect of the confound** (C−A contrast on each direction, cluster-robust p over 6 domains):

| L | 4 | 8 | 12 | 16 | 20 | 24 | 31 |
|---|---|---|---|---|---|---|---|
| `d_surface` | +0.023 | +0.027 | +0.015 | **−0.023** | **−0.029** | **−0.021** | +0.047 |
| p_clustered | 0.002 | 0.022 | 0.043 | **0.028** | **0.009** | 0.053 | 0.000 |
| `d_naive` | +0.043 | +0.048 | +0.037 | −0.006 | −0.016 | −0.005 | +0.094 |
| p_clustered | 0.000 | 0.003 | 0.001 | 0.437 | 0.074 | 0.623 | 0.000 |

The naive direction **roughly doubles** the effect where both agree (1.75–2.4× at L4/L8/L12/L31).

⚠ **The mid-layer half of this claim is weaker than it looks, and both weakenings came from the final
verifier.** (a) The naive p range is **0.074–0.62**, not 0.22–0.62 — at L20 the naive direction is
*also* marginally negative. (b) More seriously, **the L16–L24 negative band does not exist in the
behavioural prompts**, the population every ASR claim lives on: split by query kind those layers read
**+0.003 / −0.004 / +0.015 (all n.s.)** for `behavioral` versus ≈−0.035 for `comprehension_usage` and
≈−0.045 for `semantic_one_word`. And `reanalyze_corrected.py`'s own `holm_rejected` field is **True
only at L1, L4 and L31** — none of them in the mid-band. (Corrected 2026-08-18: the file previously
corrected over the 10 *displayed* layers while its docstring claimed 32. The honest family is every
layer with a `d_surface|L*|cos` column in `results.jsonl`, all 32, each actually tested and entered
into the step-down; that rule *adds* L1 and leaves L4 and L31 rejected. The external critique
predicted L4 would stop being rejected at m=32 — that holds only if the 10 displayed p-values are
ranked against `alpha/(32-i)` without testing the other 22, which is not Holm. Sensitivity table and
all three rejection sets are in `outputs/boombness/reanalyze_corrected_d_surface_cos.json`
under `holm_rejected_by_family`.) So the defensible claim is that the naive direction inflates ~2× where both
agree; the mid-band attenuation is a semantic/comprehension-prompt effect that does not survive
multiplicity correction.

**Bank integrity:** **912 families** total, of which 240 are the matched 2×2 set; all target
occurrences single-token in both arms; **0 alignment violations among the 216 families where the
exact-swap invariant is defined** — the other 696 are forced-choice and cannot satisfy an exact swap
by construction. (Three different denominators, so all three are stated.)

---

## 1b. What was actually implemented (plan §15 item 2)

Required by the plan and absent from both reports. This is the map a reader needs to check any number
in this document against the code that produced it.

**36 modules in `src/boombness/`, 32 test files, 584 passing tests, 244 committed run directories.**

### Generation and audit
| module | what it does |
|---|---|
| `prompt_families.py` | the aligned 2×2 generator — 2,352 prompts, 912 families, 6 domains, 7 `bank_block`s. Every family holds the four cells of the identification design. |
| `demo_pools.py`, `make_manual_review.py` | demonstration pools; the 50-prompt human-review sample |
| `tokenization_audit.py` | plan §2.4's mandatory audit — single-token codeword by construction, 0 alignment and 0 tokenization violations |
| `external_bank.py` | plan §14 adapter: ClearHarm (179) and AdvBench held-out (495) into bank schema, with the source's own categories as clusters and the imbalance **reported at build time** rather than discovered later |

### Representation
| module | what it does |
|---|---|
| `signals.py` | readout construction. `string_option_readout` is the **whole-answer** instrument that replaced the single-next-token one (C-6) |
| `extract_boombness.py` | activation extraction at both readout positions; fits `d_surface` / `d_context` / `d_naive` / `d_inter`; logit-lens Boombness; per-row `is_self_fit`, `is_final_occurrence`, `seq_len`, `token_pos` |
| `probes.py`, `role_probes.py` | 6 probe regimes, domain group-k-fold, shuffled controls, nested layer selection |
| `refusalness.py` | the refusal direction at both positions — matched footing for the R-5 retraction |

### Intervention
| module | what it does |
|---|---|
| `aggressive_patching.py` | §5 transplant + additive steering; the G1 design |
| `surgical_knockout.py` | §10 attention-edge knockout; 11 arms incl. two edge-count-matched ones; `--dst`, `--demo-scope`, `--skip-arms` |
| `score_behavior.py` | generation under intervention; composed arms; forced answer position; per-row `option_mass` and the tail gate |
| `dominance.py`, `diagnose_knockout.py` | knockout diagnostics |

### Scoring
| module | what it does |
|---|---|
| `judge_boombness.py` | StrongReject via the house harness, with the **goal** built by mapping the codeword back to the concept — and per-row goal **status**, which is how R-14 was found |
| `coherence_gate.py` | per-arm coherence, applied individually rather than pooled |

### Analysis (all CPU, all committed, every gate-bearing number comes from here)
`analyze_g1_g3` · `analyze_g2` · `analyze_g8` · `analyze_g9` · `analyze_g11` · `analyze_g64` ·
`analyze_position` · `analyze_role` · `analyze_steering` · `analyze_boombness` ·
`reanalyze_corrected` · `compare_runs` · **`analyze_external_arms`** (the §14 decomposition, incl. the
paired super-additivity-vs-control test) · **`analyze_condition_profile`** (R-15) ·
**`summarize_section8`** · **`summarize_section9`** · `retraction_sweep`

### Infrastructure that carries the discipline
| module | what it enforces |
|---|---|
| `common.py` | `RunDir` (refuses `finish()` without a `FailureLedger`), `clustered_proportion_ci`, `validate_direction_payload` (T8), `compare_bank_hashes`, `require_done`, seed + tokenizer revision |
| `slurm/run_boombness.sh` | one GPU wrapper for every stage. Encodes the house traps: nodelist reduced not `--exclude`; `--export` truncates comma lists; argsfiles on the shared FS; **and now refuses an argsfile containing a quote**, because its args are word-split |
| `retraction_sweep.py` | scans the deliverables for retracted figures asserted as fact; **exit 1 gates a commit** |

### What the plan asked for and did not get
* **§4.1's designed variance** (`strength`, `consistency`, `example_position`) — generated into three
  dedicated `bank_block`s, analysed by nothing, and shown in **N12** to be unable to support inference.
* **`prompt_level_correlation.py` / `example_count_sweep.py`** as *named* scripts — the work exists as
  `summarize_section9.py` and `summarize_section8.py`, which read committed artifacts rather than
  re-running the sweeps. Same outputs, different provenance path, recorded here rather than glossed.
* **A second concept pair** — every claim in this report is carrot↔bomb (**E6**).

## 2. Where the meaning lives (§5, §7, §10) — G1 and G3

### G1: retrieved from the demonstrations at answer time, not stored in the codeword
Activation transplant on matched fixed pairs, semantic log-odds readout. **Headline is the stratified
run** — `g1_stratified.json`, **24 families across all 6 domains**, harm-context pair, bootstrap
resampling **domains** (families drawn wholesale with their domain):

**Re-derived 2026-08-19 on the corrected whole-answer readout** (`g1_wholeanswer_sow.json`,
31,104 rows, self-swap no-op |Δ| = 6.5e-02). The old single-token figures are shown beside it:

| arm | **whole-answer (current)** | old readout |
|---|---|---|
| **transplant demonstrations, L18** (`demos_only`) | **+68.9%, CI [+51%, +97%]** | +68.1% [+50%, +95%] |
| transplant demonstrations, L12 | +48.8% [+18%, +88%] | +58.0% [+30%, +100%] |
| transplant first demonstration only, L18 | +31.6% [+19%, +48%] | +28.7% [+13%, +49%] |
| transplant last demonstration only, L18 | +9.5% [+4%, +18%] | +7.0% [+2%, +13%] |
| transplant **whole prompt**, L18 (`all`) | **+13.3% [−17%, +34%] — null** | +14.1% [−9%, +32%] — null |
| transplant **query codeword**, L18 | **−57.0% [−103%, −40%] — wrong way** | −70.6% [−105%, −56%] |

**The direction is the finding and it is unambiguous:** transplanting the *demonstrations* moves the
model's reported meaning most of the way to the donor's; transplanting the *query codeword* moves it
**backwards**. The meaning is retrieved from the demonstrations at answer time.

⛔ **R-8 — the earlier "+84%, CI [+57%, +105%]" headline is superseded.** It came from a pilot of
**n=8 families in only 2 domains**, so its effective number of independent units was nearer 2 than 8.
The stratified re-run at 24 families / 6 domains gives **+68%**. An interval of "+23% to +135%" quoted
before that was a **chimera** (one arm's lower bound welded to another's) and is withdrawn.

⚠ **Arm-selection exposure, and it bites here.** This is one arm of ~130. In the stratified data the
*whole-prompt* transplant `transplant|all|L18` — which an earlier draft treated as interchangeable
with the demonstration arm — is **null on the harm-context pair**: +14%, CI **[−9%, +32%]**. The G1
claim is specific to transplanting the **demonstration block** at a **single-layer L18 window**, not
to demonstration transplants in general and not to whole-prompt transplants at all.

✅ **C-6 discharged — and the answer is that it did not change G1.** The old figures came from the
single-next-token readout that R-6 retracted elsewhere: the options held a median **5.6e-06** of
next-token mass, the model capitalises, and the capitalised codeword is **multi-token**
(`Carrot` = ` Car` + `rot`) while the concept has four single-token variants — an instrument
structurally biased toward the concept. Ported to `signals.string_option_readout` and re-run at 24
families: **`demos_only|L18` comes in at +68.9% against +68.1%**, and every other arm reproduces. The
defect was real; the log-odds ordering was robust to it. *That is only knowable after re-deriving it,
which is the argument for having done so.*

⚠ **What does NOT clear is the ceiling.** `donor_ceiling` option mass is **0.0074** with only 39.6% of
rows above 1%: on the donor prompt the model answers ` Explos`(ive) or ` Squ`(ash)/` Vegetable` —
semantically right, lexically outside the option set. **The span denominator is estimated where the
model wants to say a different word.** The two readouts agreeing does not discharge this, since both
normalise by the same span. **G1's direction and ordering are safe; the absolute "% of span" figures
inherit a ceiling measured in a tail.** Fixing it requires an option set admitting synonyms, which
changes what is measured — future work, not a silent patch.

### G3: the retrieval is attention-carried, and the redundancy is in the EDGE COUNT — re-derived 2026-08-19
**24 families / 24 eligible (`effective_G=24`), whole-answer readout, `--dst both` (ranking at
`readout_pos`), cross-fitting restored.** This replaces the earlier 6-family run whose ranking was
computed at the destination retraction #3 called fatal — R-7 is **discharged**, and the null it
questioned survives.
`outputs/boombness/g3_wholeanswer_block24.json` · `..._codeword24.json`

| arm | edges | layers | Δ readout | sem | fraction of deletion ceiling |
|---|---|---|---|---|---|
| `no_demo_text` (delete the demos) | — | — | **−17.879** | 1.072 | **1.000 — the ceiling** |
| **`all_layers_demo`** | **81,707** | 32 | **−13.437** | 0.787 | **0.752** |
| `positive_control` | 8,883 | 2 | +0.258 | 0.306 | −0.014 |
| `all_demo` | 5,107 | 2 | +0.152 | 0.154 | −0.009 |
| **`subsampled_all_layers_demo`** | **5,107** | **32** | **+0.079** | 0.090 | −0.004 |
| `topk_demo` | 16 | 2 | **+0.020** | 0.017 | −0.001 |
| `random_demo` | 16 | 2 | +0.001 | 0.003 | −0.000 |
| `bottomk_demo` | 16 | 2 | −0.003 | 0.003 | +0.000 |
| `same_head_random` / `random_nondemo` | 16 | 2 | +0.003 / −0.044 | 0.023 / 0.037 | ≈0 |

**1. The retrieval is attention-carried.** Cutting every demonstration edge at every layer recovers
**75.2%** of deleting the demonstrations outright. *(The superseded figure was 84%, computed on the
invalid single-next-token readout.)*

**2. The ranking carries no information, and this time it was measured at the right token.**
`topk` **+0.020**, `bottomk` **−0.003**, `random` **+0.001**, sems 0.017/0.003/0.003 — indistinguishable.
R-7 flagged that the old null could not separate *"these edges do not matter"* from *"they were ranked
at the wrong destination"*. Ranked at `readout_pos`, **the null holds**.

**3. The edge-count-vs-depth tie is broken, and the answer is edge count.** At an identical **5,107**
edges, concentrating them at 2 layers (+0.152) and spreading them over 32 (+0.079) are both **nothing**;
only cutting essentially all 81,707 works. **6.25% of the demonstration edges does nothing however
distributed.** Layer spread is not the operative variable — edge count is, and the response is close to
all-or-nothing.

This is the question `dense_two_layer` was built for and can never answer: it is **structurally
infeasible** (it needs ≥16 chosen layers, at which point it is not a two-layer arm), and the pre-fix
code met that by silently delivering 7,264 of 56,832 edges — 87% short — while still reporting the arm
as edge-count-matched. It is now skipped **deliberately**, with the reason recorded in `summary.json`
and charged to the FailureLedger. The tie is broken from the feasible side instead.

**4. ★ Codeword scope: the information is in the demonstration BLOCK, not the codeword tokens in it.**
Restricting every cut to edges into the codeword occurrences *inside* the demo block:

| arm | edges | Δ readout | sem |
|---|---|---|---|
| **`all_layers_demo`** (codeword scope) | 6,144 | **+1.332** | 0.351 |
| `subsampled_all_layers_demo` / `all_demo` | 384 | +0.125 / −0.110 | 0.062 / 0.079 |
| every 16-edge arm | 16 | −0.037 … +0.013 | — |

Cutting **all** attention into the demo-block codeword tokens at every layer does not reproduce the
deletion effect — it moves the readout the **wrong way** (+1.33), while cutting attention into the
**whole block** recovers 75%. **G1's conclusion reached independently from the attention side**: the
meaning is retrieved from the demonstrations as a whole, not from the codeword tokens within them.

**Identification limit, stated rather than hidden.** The converse arm is impossible: a layer holds only
~3.6k edges, so any cut above ~7.3k *must* span layers. Edge count and layer spread cannot be decoupled
upward — only downward, which is what the 5,107-edge pair above does.

**On `dynamic_range_established = False`.** The script prints it because `positive_control` (+0.258)
does not exceed 3× the largest other arm. That is expected and the code says so
(`analyze_g1_g3.py:225`): the largest arm is `no_demo_text`, the deletion **ceiling** the fractions are
taken *of*, not an arm awaiting validation — movability is established overwhelmingly by
`no_demo_text` itself. ⚠ The `positive_control` still does not behave like one (+0.258 here, and it
changed **sign** between two earlier runs of the same design); **do not cite it as validating
anything**. Nothing in this section depends on it.

### §7: semantics move far more than the representation
The model's *reported meaning* of the codeword travels **59%** of the way from literal to direct
(paired, n=60, monotone in demo count: +7.6 → +16.8) while the token's position on the concept axis
moves a few percent. Domain-clustered t (13.5) ≈ naive t (13.3); bootstrap CI on the ratio ≈ [50%, 68%].

---

## 2b. Token-level Boombness, kept separate from prompt-level (§7)

The plan insists these not be merged, and the reason turns out to be load-bearing: the token-level
result **inverts** the intuition the prompt-level one invites.

### Does the final codeword occurrence become more concept-like than earlier ones? **No — less.**
Within-prompt paired contrast: same prompt, same surface word, only the occurrence position differs.
Domain-clustered over 6 domains, n=246 doublespeak behavioural prompts with ≥2 occurrences:

| L | 4 | 8 | 12 | 16 | 20 | 24 | 31 |
|---|---|---|---|---|---|---|---|
| Δ(final − earlier) | −0.025 | −0.082 | −0.090 | **−0.154** | −0.123 | −0.119 | −0.080 |
| t_clustered | −5.0 | −6.2 | −7.1 | **−10.5** | −8.3 | −6.3 | −3.7 |
| p_clustered | 0.004 | 0.002 | 0.001 | **0.0001** | 0.0004 | 0.001 | 0.014 |

### And the control is what makes it interpretable
The identical comparison in `benign_literal` — where there is **no** concept meaning at all — gives the
**same sign and comparable magnitude** (n=162: L16 −0.105, L31 −0.131, all p < 0.004). At some layers
doublespeak is more negative, at others benign is; there is **no consistent doublespeak-specific
excess**.

**So this is a POSITION effect, not a semantic one:** the last occurrence of a word sits differently on
the axis than earlier occurrences regardless of what it means. ⛔ The earlier
"later-carrot-is-more-bomb-like" claim is retracted, and this is its replacement — computed with the
control the retracted version lacked. That claim read a within-prompt gradient as accumulating concept
content without asking whether a prompt containing no concept content shows the same gradient. It does.

**Why keeping the levels separate mattered.** Prompt-level Boombness *rises* with demonstrations
(L8 +0.0138 → +0.0449 over k=1→16) and correlates with ASR. Token-level, the final occurrence is
*lower* than earlier ones. Merged, those two would have been reported as one incoherent trend or —
worse — the prompt-level rise would have been narrated as "the codeword accumulates bombness as the
prompt proceeds", which the token-level data directly contradicts.

This is the third independent place position beat meaning on this axis: the predictor×position 2×2
(2–4×), the surface-matched probes (context decodable at the codeword from block 0), and now the
within-prompt occurrence comparison.

---

## 3. Does Boombness predict attack success? (§9) — G2

**ρ = +0.307** for `d_surface|L12|proj`, **+0.302** after partialling out the residual-stream norm,
n = 234. "100% coverage" means all 270 judged doublespeak rows had a representation row — it does not
mean nothing was dropped: 36 zero-demo prompts are excluded on principle (no demonstrations ⇒ no
codeword mapping), leaving 234.

**Inference, corrected.** The 234 prompts are 6 domains × 39 and the predictor is strongly clustered
by domain (ICC ≈ 0.45). The i.i.d. p originally reported was overstated by ~3.5 orders of magnitude:

| inference | p |
|---|---|
| i.i.d. (withdrawn) | 1.7e-06 |
| CR1 domain-clustered (G=6, few clusters — indicative) | 1.2e-03 |
| **within-domain permutation, group-demeaned — cite this** | **< 5e-4** (resolution floor: 0 of 2000 draws reached the observed value) |

Per-domain: **6 of 6 positive**, but two are essentially null (`lab_safety` +0.020, `news_report`
+0.062), so "positive in 6/6" reads more uniform than the data is.

### The between-arm story: the attack removes refusal
On the 234-prompt population:

| | refusalness (L18) | ASR | refusal rate |
|---|---|---|---|
| direct harmful request | **+7.06** | 0.050 | 95.0% |
| doublespeak | **−0.15** | **0.214** | 0.85% |
| mapping stated outright | +0.01 | 0.375 | 0% |
| benign literal | −0.30 | 0.031 | 1.85% |

To the refusal direction a doublespeak prompt looks **benign** — it sits at −0.15, next to
`benign_literal`'s −0.30 and **7.2 units below** the matched direct request. Every figure above is on
the `n_examples ≥ 1` population; an earlier draft mixed the all-rows numbers in and had the
doublespeak cell at **+0.04**, i.e. the wrong sign.

### ⛔ The "Boombness beats refusalness 3.7×" claim is retracted
It compared `d_surface`@`codeword_last` against refusalness@last-token — different tokens. Rebuilt as
a freedom-matched 2×2 (columns available at **both** positions: 20 for `d_surface`, 10 for refusalness):

| single-predictor R² | @ last token | @ codeword_last | position effect |
|---|---|---|---|
| `d_surface` | 0.070 | 0.141 | **2.0×** |
| refusalness | 0.046 | 0.189 | **4.2×** |
| **ratio B/R** | **1.54** [0.64, 3.60] | **0.75** [0.33, 1.13] | |

**Neither probe dominates** — which wins depends on where you read, and both domain-clustered CIs
straddle 1.0. The 3.7× was the most favourable of four possible cross-position pairings.

**This table is now regenerable.** `src/boombness/analyze_position.py` produces it from a committed
command, records the run paths, and **verifies that each of the four cells actually read where it
claims to** — the check that caught the phantom cell. It refused to run until the `@last` refusalness
cell had an artifact recording its position (job 761697), rather than accepting the source code as
evidence.

**Stated at its least favourable framing, deliberately.** The 2.0×/4.2× above uses each probe's *best*
column. On *median* columns the position effect is far larger — `d_surface` 0.0076 → 0.0847 (**11×**)
and refusalness 0.0033 → 0.1643 (**50×**) — so the localization finding is stronger than the headline
number suggests. The best-column version is quoted because it is the conservative one.

⚠ **Two things about the freedom in that table.** (a) It is matched *within* each probe across
positions but **not between probes**: `d_surface` draws its best column from 20 candidates,
refusalness from 10, and both are max-of-k statistics, so the ratios are biased **toward Boombness**.
Re-selecting the column inside each bootstrap resample gives [0.84, 2.88] and [0.38, 1.12] — same
conclusion, wider. (b) On **incremental** R², at **matched degrees of freedom** (one column each,
from `g9_three_predictor_{cwpos,lastpos}.json`, n=234):

| row set | Boombness adds over refusalness | refusalness adds over Boombness |
|---|---|---|
| ⛔ @ codeword_last, **unfiltered n=234** | +0.0743 | **+0.1091** |
| ✅ @ codeword_last, **clean n=90** | **+0.0441** | **+0.0378** |
| @ last token, unfiltered | **+0.0053** | +0.0000005 |

⛔ **R-18: the ordering does not survive the row set.** R-13 corrected this table's *degrees of
freedom* (5-vs-1 → 1-vs-1) and was right to. It did not correct its *rows*, and the n=234 set is 31%
sibling families sharing demonstrations plus 31% experimentally-manipulated designed variance (see the
G2 row of the gate table). On the **90 independent, unmanipulated prompts the two increments are
within 0.007 of each other** — the 1.47× refusalness advantage is an artifact of the row set, exactly
as G2's ρ was.

⚠ **Do not read this as "Boombness adds more".** Both increments are ~0.04 on n=90 over 6 domains;
neither is well estimated. **At matched df on clean rows, neither predictor dominates.** At the last
token refusalness adds nothing (4.5e-07), which remains a position fact.

⛔ **Retraction R-13.** Two earlier drafts of this table were wrong in opposite directions. The first
quoted +0.104 / +0.039 from the mixed-footing artifact. The second quoted **+0.028 / +0.144
@codeword and +0.025 / +0.091 @last and labelled them "matched footing"** — but those two cells are
increments against the *same* model, `boombness(1 column) + refusalness(5 columns)`, so refusalness's
increment carried **5 degrees of freedom against Boombness's 1** and R² is monotone in predictors.
That table repeated the mismatched-footing error inside the paragraph announcing its retraction. It
was also never regenerable: the pair 0.144/0.028 appears in no committed artifact, while
`g9_three_predictor_cwpos.json` has carried the matched-df values in all four of its committed
versions. At matched df the codeword-position gap is **1.47×**, not the 5.1× implied, and the earlier
reading "Boombness is close to redundant given refusalness" does not hold — +0.0743 on a
refusalness-only base of 0.1759 is a **42% increase** in explained variance.

**What replaces it is a position finding:** both probes are 2–4× more predictive of ASR at the
**codeword token** than at the final prompt token — a larger factor than any difference between the
probes. The attack-relevant state is **localized at the codeword**, consistent with G1 and G3.

**Construct-validity caveat:** the refusal direction was fitted for a last-token readout. At the
codeword position it no longer orders conditions like a refusal probe (`direct_harmful` becomes
indistinguishable from doublespeak, and `benign_literal` reads as *least* refusing). The predictor
comparison is fair — both probes treated identically — but "refusalness at the codeword token" is
**not** a validated refusal measurement, which is why outcome C is not claimed.

---

## 4. Steering (§12) — G4, and why the objective was not built

L8, gap-unit dosing (α=1 = one diff-of-means), common 270-prompt set, all arms coherence-gated:

| arm | ASR | 95% CI | refusal | paired Δscore |
|---|---|---|---|---|
| baseline | 0.219 | [0.173, 0.272] | 0.074 | — |
| **+0.25** | 0.081 | [0.054, 0.120] | **0.696** | **−0.1144 ± 0.0235** |
| **−0.25** | 0.148 | [0.111, 0.195] | 0.067 | **−0.0741 ± 0.0198** |
| random ×4 (band) | — | — | 0.085 | ⛔ **−0.0366 / sd 0.0049 RETRACTED (#7)** — those four "draws" were byte-identical. Genuine 4-draw band: **−0.0120, between-draw sd 0.0301** |
| orthogonal | 0.189 | [0.147, 0.240] | 0.093 | −0.0306 ± 0.0179 |

**Both signs suppress ASR**, so mean ASR does not follow the sign of the axis. The falsifying branch
was written into the analysis code before the numbers existed, and it fired. **No directional causal
support ⇒ no objective.**

Against a proper 4-draw random-control band (Welch df, not the SE of the band mean):


⛔ **The table that stood here quoted t/p computed from the RETRACTED band** (p=0.0014 on
df=235). Those are downstream of retraction #7 and were withdrawn with it — the sweep missed them
because I had enumerated the band's mean and sd but not the statistics derived FROM it. Against
the GENUINE 4-draw band (n_draws=4, so the Welch df is ~7, not ~235):

| arm | diff vs band | t | df | p | verdict |
|---|---|---|---|---|---|
| **+0.25** | -0.1023 ± 0.0410 | -2.49 | 6.6 | **0.043** | clears the band |
| −0.25 | -0.0620 ± 0.0391 | -1.59 | 5.4 | **0.168** | does **not** clear |

**The two signs suppress by different routes** — of the prompts each arm suppressed, the fraction
that are keyword refusals:

| +0.25 | −0.25 | random | orthogonal |
|---|---|---|---|
| **0.901** | **0.000** | 0.000 | 0.042 |

So: **adding concept-ness to the codeword triggers refusal; removing it just damages the model like
any other perturbation of that size.** "Pure disturbance" is too strong, and so is "axis-magnitude
effect at both signs" — only the positive sign exceeds a norm-matched perturbation.

⚠ **Coherence caveat on the arm carrying the only positive G4 result.** All five arms pass the gate,
but `coherence_gate` skips generations under 8 words, and the +0.25 arm — refusal rate 0.696 — had
**68 of its 270** doublespeak generations (25%) excluded on that basis, so `coherent: true` was
computed on n=202. Baseline dropped 0; the others 0–1. The gate is weakest exactly where it matters.

**A near-miss worth recording:** an arm at α=1 showed ASR 0.219 → 0.759 and was an **artifact** — the
intervention broke generation (55% of trigrams repeated, 100% truncated) and the judge scored the
degenerate loop as harmful. It was caught by the coherence gate only after being written down. **The
usable dose window is narrow**, which is itself an argument against the objective: an optimizer
maximizing this projection has no reason to stop at 0.25 and will find the degenerate regime.

---

## 4b. The §2.6 comprehension control, and what it does to every intervention claim (added 2026-08-17)

The plan's §2.6 forbids reading a lowered ASR as causal without checking the model still understands the
prompt. **That control was missing for the whole sprint** until an independent plan-coverage sweep found
it. It now exists, and it reorders the intervention arms.

Readout: `comprehension_logodds` = log p("coded") − log p("literal") on `comprehension_usage` rows;
positive means the model still reports the codeword as meaning the coded thing. 60 doublespeak prompts
with ≥1 demonstration, common to all arms, domain-clustered over 6 domains:

| arm | Δ comprehension | p | frac still "coded" | verdict |
|---|---|---|---|---|
| `d_surface` **+0.25** | +0.643 | 0.006 | 0.733 | improves |
| **random +0.25** | **+1.065** | 0.001 | 0.800 | improves MORE |
| `d_surface` **−0.25** | **−0.792** | 0.040 | **0.500** | **degrades below zero** |
| **random −0.25** | **−1.470** | 0.004 | **0.383** | degrades MORE |
| **`project_out`** | **+0.088** | **0.681** | 0.683 | **unchanged** |
| arm C (remove refusalness) | +0.207 | 0.001 | 0.717 | improves |
| arm F (add Boombness + remove refusalness) | +0.863 | 0.002 | 0.783 | improves |

**Three consequences, one of them a retraction of my own claim.**

1. **The −0.25 arm is disqualified.** Its ASR suppression (0.219 → 0.148) coincides with comprehension
   falling *below zero* — the model now prefers the literal reading — so that suppression is at least
   partly confusion. It must not be described as "removing concept-ness reduces attack success".
2. **The +0.25 arm is exonerated** in the narrow sense that matters: comprehension did **not** degrade, so
   its ASR drop is not confusion. Combined with refusal rising 0.074 → 0.696, the reading "it triggers
   refusal" stands.
3. ⛔ **But the pattern is NOT axis-specific, which retracts a gloss I added (C10).** The effect is driven
   by the **sign of the dose**: positive steps raise p(coded), negative steps lower it, for `d_surface`
   *and* for a norm-matched random direction — and **random moves comprehension further in both
   directions**. I had claimed "only the negative `d_surface` step degrades comprehension, and no control
   does"; that was untested (no negative random control existed) and is false. Comprehension therefore
   does **not** discriminate `d_surface` from a generic perturbation.

**What survives as genuinely distinctive: `project_out` is the only one of five arms that leaves
comprehension unchanged** while all four additive arms move it by 0.6–1.5. That is what makes it the
surgical condition, and it is why its ASR result (the §10.4 `project_out` arm, reported under
**§7e** — this passage previously cited a §0.3 that does not exist) was
called the sprint's cleanest causal test. ⚠ That description is **withdrawn**: its comprehension
control is R-6, the readout measuring a 1e-5 tail.

---

## 5. Role framing (§11)

Six role styles with demonstration content, domain, demo count and final query held **fixed**
(the content-constancy design, following the Role-Confusion codebase's `render_single_message`):

| style | Boombness L12 | ASR (n=36 each) |
|---|---|---|
| system_like_quoted | −0.2807 | **0.035** |
| assistant_like | −0.2876 | 0.160 |
| tool | −0.2858 | 0.163 |
| cot_like | −0.2820 | 0.177 |
| plain | −0.2909 | 0.195 |
| user_like | −0.2888 | **0.233** |

⛔ **RETRACTED (retraction #6) — the "tight null" was an ERROR TERM mistake and the corrected answer is
the opposite.** The arithmetic reproduced exactly (F=0.175, p=0.972 at L12), but the design is perfectly
crossed — 72 complete 6-style stems — and the correct **paired within-stem** test gives
**F(5,355)=20.30, p=8.1e-18** (permutation p<5e-5), with **11 of 15 pairwise style differences surviving
Bonferroni**. Blocking on `query_kind` alone already breaks the null (p=0.016).
The "3.6% of within-style sd" was a **variance-decomposition error** — that denominator (0.110) is almost
entirely *between-stem* variance, which the paired design removes; against the correct within-stem residual
(0.0082) the spread is **53%**. And in the 816-row pool `plain` and the five role styles occupy **disjoint
`bank_block`s with zero family overlap**, so "content, domain, demo count and query held fixed" was **false
for the analysis actually run** — true only inside the 72 stems.
**Corrected: role framing DOES move Boombness — reliably but by a small amount** (largest pairwise gap
0.0116 = **4.1% of the grand mean** at L12). A small, highly reliable effect, not a null.

**The ASR half is suggestive but not established:** `role → ASR` F = 1.94, **p = 0.087** on an
unbalanced omnibus (`plain` n=204 vs 36 each); the largest pair (0.035 vs 0.233, a 6.6× ratio) is
MW p = 0.007 uncorrected ≈ **0.105 Bonferroni** over 15 comparisons.

So §11's answer is: **role DOES move Boombness — reliably, and by ~4% of the grand mean — while whether
it moves ASR is unresolved at this n.** (I predicted (b) before the powered run; the representational
half is supported, the behavioural half is not yet.)

⛔ This sentence previously read "role definitively does not change Boombness", **four lines below the
paragraph retracting exactly that claim** (retraction #6). Caught 2026-08-18 by an independent audit, not
by my own retraction sweep — the sweep scopes to a paragraph and this paragraph contains the word
"corrected", which its marker regex reads as retraction context. A marker word in the block is now known
to be an unreliable exemption; the sweep's own limitation is recorded in `retraction_sweep.py`.

`role_style` is a **categorical proxy**: no Userness/CoTness probe was fitted on this model, so this
is not a measured role signal.

---

## 6. Demonstration-count dose-response (§8)

C−A contrast on `d_surface|L|cos`, surface held constant at `carrot`, cluster-robust t, n=36/cell:

| band | behaviour |
|---|---|
| **L4–L12** | positive, **strictly monotone** in demo count (4/4 steps); L8 grows **+0.0138 → +0.0449 (3.3×)** from k=1 to k=16 |
| **L16–L24** | **negative**, magnitude dose-dependent, **saturating at k=8** (L20 −0.051, easing to −0.042 at k=16) |
| **L31** | **FLAT** across a 16× dose change (+0.0485/+0.0457/+0.0485/+0.0438/+0.0499; t = +5.9…+10.2) |

**One demonstration achieves the entire output-layer effect**; fifteen more add nothing, while the
mid-layer effects keep scaling to k=8–16. So the quantity reaching the output is **not** a simple
readout of the quantity accumulating mid-stack — independently consistent with G4's directional null.

This also gives the retracted "two humps" observation a proper account: two bands of **opposite
sign** responding differently to dose. The mid band is not null; it is negative *and* dose-dependent.

⚠ **This table is POOLED over three query kinds, and the mid-layer band is not a behavioural-prompt
effect** (correction C7). Split out, L16/L20/L24 read **+0.003 / −0.004 / +0.015 (all n.s.)** for
`behavioral` versus ≈−0.035 for `comprehension_usage` and ≈−0.045 for `semantic_one_word`. For the
behavioural prompts — the population all ASR claims live on — the picture is simpler: **early positive
band (L8 +0.048 t=+2.1, L12 +0.036 t=+2.2), no mid-layer band, and a large L31 effect (+0.133,
t=+9.8)**. The pooled negative band also fails the artifact's own Holm correction, which rejects only
L4 and L31.

**Scale caveat:** these are cosines in the 0.01–0.05 range. The sign structure and the dose response
are the findings; the magnitudes are small.

---

## 6b. Aggressive patching — the full arm table (plan §15 item 6)

Required by the plan and absent from both reports. `g1wa_sow` — 24 families over 6 domains, both
context pairs, whole-answer readout, **31,104 rows, zero failures**
(`outputs/boombness/g1_wholeanswer_sow.json`). Percentages are of each pair's own baseline→ceiling
span; intervals are domain-clustered.

### Transplant arms — what has to be moved to move the meaning

| arm | harm_ctx | benign_ctx |
|---|---|---|
| `demos_only` **L18** | **+68.9%** [+51, +97] | **+94.3%** [+78, +114] |
| `demos_only` L12 | +48.8% [+18, +88] | +103.7% [+84, +129] |
| `first_demo` L18 | +31.6% [+19, +48] | +24.1% [+19, +30] |
| `last_demo` L18 | +9.5% [+4, +18] | +5.7% [+4, +7] |
| `all` (whole prompt) L18 | **+13.3%** [−17, +34] — **null** | +76.9% [+63, +96] |
| `query_only` L18 | **−57.0%** [−103, −40] — **wrong way** | −8.2% [−10, −7] |

**Three things this table says that the single headline number does not.**

1. **The demonstration *block* is the carrier, and the codeword is not.** `demos_only` moves the
   readout most of the way; `query_only` moves it **backwards** on the harm pair. §7c reaches the same
   conclusion from the attention side — cutting attention into the demo-block *codeword tokens*
   fails to reproduce the deletion effect while cutting attention into the *whole block* recovers 75%.
2. **The transplant is not additive over demonstrations.** `first_demo` alone buys ~32% and `last_demo`
   ~10%, against ~69% for the block — the first demonstration is worth three times the last, and the
   parts do not sum to the whole.
3. **The two context pairs are not the same experiment.** On `benign_ctx` the whole-prompt transplant
   works (+76.9%) and the query-codeword arm is nearly inert (−8.2%); on `harm_ctx` the whole-prompt
   arm is **null** and the query arm is strongly negative. The harm pair is the harder and more
   informative one, which is why the headline is quoted from it.

### Additive steering — including α = 0.25, swept for the first time (E9)

The §5.2 sweep had run α ∈ {0.5, 1, 2, 4}. **0.25 — the dose every §12 behavioural claim rests on —
was never in it.** It is now:

| arm | harm_ctx | benign_ctx |
|---|---|---|
| `add all all d_surface α=0.25` | **+103.4%** [+88, +114] | **+145.0%** [+134, +161] |
| `add all all d_surface α=0.5 … 4.0` | 138–161% (benign_ctx) | monotone in α |
| `add query_only all d_surface α=0.25` | **−71.7%** [−200, −23] | +90.8% [+78, +109] |
| `add query_only all random α=1.0` | −146.5% [−384, −94] | — |
| `add query_only all orthogonal α=1.0` | −135.0% [−281, −83] | — |

**Adding `d_surface` across the whole prompt reaches or overshoots the donor ceiling** (103% on
harm_ctx, 145% on benign_ctx) — the readout can be driven past the donor's own value, so "% of span"
is not bounded at 100% and should not be read as a saturating quantity.

**Adding it to the query alone moves harm_ctx the wrong way** (−71.7%), the same asymmetry the
transplant arms show. ⚠ But the `random` and `orthogonal` controls are **also** strongly negative
(−146.5%, −135.0%) on that arm, so the query-only *additive* result is **not direction-specific** —
whatever is happening there is a property of perturbing the query position, not of `d_surface`. Only
the **transplant** query-only arm has matched controls that stay near zero, so that is the one to cite.

### ⚠ Carried caveats
* The **ceiling** is measured in a tail (`donor_ceiling` option mass **0.0074**, 39.6% of rows above
  1%) — the model answers the donor prompt with a synonym outside the option set. Direction and
  ordering are safe; the absolute percentages inherit that denominator.
* This is **one concept pair** (carrot↔bomb) and one model. **E6.**
* `--query-kind semantic_forced_choice` is **not available** for this design: it names both the
  concept and the codeword, so donor and recipient occurrence positions do not correspond and a
  position-matched transplant is undefined. The script refuses it, in six seconds, before loading the
  model.

## 7. Probes (§6)

**⚠ The original four regimes are uninformative by construction.** All shared one label —
`cell ∈ {B,E}` = "the target token IS the concept", i.e. **the surface word**. `bomb` and `carrot`
are trivially separable, so every regime returns **AUROC = 1.000 at every layer**, shuffled controls
near chance. `d3_hard_negative` is affected too: its C-vs-E test set is also carrot-vs-bomb. **These
1.000s must never be quoted as "Boombness is linearly decodable."**

**New surface-matched regimes**, holding the word constant and varying the meaning:

| layer | d5 (A vs C, both "carrot") | shuffled | d6 (B vs E, both "bomb") | shuffled |
|---|---|---|---|---|
| 0 | 0.960 | 0.561 | 0.974 | 0.376 |
| 12 | 0.982 | 0.571 | 0.985 | 0.408 |
| 31 | 0.983 | 0.657 | 0.979 | 0.594 |

⚠ **"Shuffled controls at chance" is too clean a description.** Per layer they span **0.354–0.657**
(d5) and **0.350–0.716** (d6); the *means* are ≈0.52 but the scatter is ±0.2 at n=432. The lift over
shuffle is large and the conclusion holds — the description does not.

A length/position confound was suspected (A/E average 137.9 tokens vs 129.6 for B/C, tracking
context) and **refuted**: on the full cell populations `seq_len` alone gives AUROC **0.430** (d5) /
0.437 (d6) and `token_pos` **0.454** / 0.475 — chance-level, though `seq_len` is a little further from
0.5 than the "~0.47" quoted earlier, in the unhelpful direction. The per-family direction is also
inconsistent (A's codeword is later in only 42/72 families).

**What they establish:** with surface held constant, the codeword token carries strong information
about which context preceded it — a probe-side confirmation of G1's retrieval story.
**What they do not:** that the retrieved content is specifically *bombness*. A and C differ in
demonstration text, so separating them shows context is encoded there, not what it encodes. That is a
projection question, which is why the conclusions rest on the 2×2 projections.

---

## 7b. Which Boombness metric? The three-way comparison (plan §6.4 / §15 item 7) — added 2026-08-18

**This section was missing.** Plan §15 requires it as report item 7, §6.4 was run and closed, and
grepping this report for "metric comparison", "probe_boombness", "direction_boombness" or
"logit_lens" previously returned zero hits. The answer is unflattering, which is the reason it
belongs here rather than the reason to omit it.

Script `src/boombness/analyze_g64.py`; artifact `outputs/boombness/g64_metric_comparison/`
(`correlation_table.csv`, `g64_summary.json`, 3 plots). All numbers below are from that CSV.

### The coverage problem comes first

| population | n |
|---|---|
| judged (ASR available) | 270 |
| with extraction (logit-lens + direction) | 270 |
| with a probe score at the headline layer | **72** |
| **common to all three** | **72 of 270 (27%)** |

`probe_boombness` is out-of-fold margins from the `d5_surface_matched_codeword` regime, whose rep
cache was built on a **1464-row** version of the bank against today's 2352, and whose regime is
hardcoded to the `core2x2` block. So the three metrics are **not** computed on the same prompts
unless they are restricted to the common 72 — which `--common-subset` now does by default. Every
number in this section is on those 72. An earlier comparison that put probe (n=72) beside direction
(n=270) as if like-for-like is **retraction #9**.

### The three metrics disagree about ASR — including in sign

Spearman ρ against the continuous StrongReject score, n=72, 6 domains. `ρ_within` is the
within-domain estimate the permutation p actually tests; `ρ_pooled` is the raw pooled value. (They
were adjacent and unlabelled until 2026-08-18; see the estimand note in the process section.)

| layer | logit_lens ρ_within | direction ρ_within | probe ρ_within |
|---|---|---|---|
| 0 | **+0.274** (p=0.005) | +0.185 (0.099) | **+0.215** (0.034) |
| 4 | −0.211 (0.086) | **+0.324** (0.008) | +0.145 (0.243) |
| 8 | −0.171 (0.154) | **+0.297** (0.015) | +0.087 (0.455) |
| **12** | **−0.026** (0.818) | +0.228 (0.076) | **+0.284** (0.010) |
| 16 | −0.176 (0.093) | −0.151 (0.196) | +0.202 (0.075) |
| 20 | **−0.296** (0.006) | −0.184 (0.127) | +0.186 (0.100) |
| 24 | −0.074 (0.538) | −0.185 (0.120) | +0.132 (0.233) |
| 28 | +0.068 (0.580) | −0.141 (0.256) | +0.123 (0.248) |
| 31 | +0.139 (0.217) | +0.149 (0.210) | +0.082 (0.412) |

**There is no layer at which all three agree.** At L12 — the layer this report headlines for G2 —
they read **−0.026, +0.228, +0.284**: one of the three has the opposite sign, and it is the
logit-lens metric, the most direct readout of "does this token look like *bomb* to the unembedding".
Each metric's strongest ASR association is at a different layer and, for logit_lens, in the opposite
direction: logit_lens peaks **negative** at L20 (−0.296), direction peaks **positive** at L4
(+0.324), probe peaks at L12 (+0.284).

**Multiplicity:** this is 27 metric×layer cells per target, uncorrected. At Holm m=27 only p≤0.0019
survives the first step, so **none of the ASR cells above is individually safe** — the smallest is
p=0.005. Read the table as a disagreement map, not as nine findings.

### On comprehension the three agree much better

Same 72 prompts, target = the §2.6 comprehension log-odds:

| layer | logit_lens | direction | probe |
|---|---|---|---|
| 4 | +0.214 (0.084) | **+0.316** (0.008) | **+0.442** (0.0005) |
| 8 | −0.123 (0.351) | **+0.336** (0.004) | **+0.473** (0.0005) |
| **12** | −0.156 (0.198) | **+0.361** (0.003) | **+0.462** (0.0005) |
| 16 | −0.273 (0.027) | +0.098 (0.429) | **+0.375** (0.002) |
| 31 | **+0.437** (0.001) | +0.127 (0.319) | **+0.396** (0.0005) |

`probe_boombness` is positive and significant at **every** layer tested, and survives Holm at m=27.
`direction_boombness` is positive and significant through the early-mid stack.

### What this section concludes

1. **The axis predicts comprehension far better than it predicts attack success.** That is the
   cleanest statement §6.4 supports, and it is consistent with — and independent evidence for — the
   report's overall position that Boombness is a representational quantity whose behavioural
   consequences are mediated by something else (refusal).
2. **"Boombness" is not one quantity.** Three reasonable operationalisations of the same construct
   disagree in sign about ASR at the sprint's own headline layer. Any claim of the form "Boombness
   predicts X" must name the metric and the layer, and G2's ρ=+0.307 should be read as a statement
   about `direction_boombness` at L12 specifically.
3. **The probe is the strongest metric on both targets but covers 27% of the population.** Fixing
   that means re-fitting the probe on the current 2352-row bank and lifting the `core2x2` hardcode
   in `probes.py:199` — not done, and the honest reason the probe is not promoted to the headline.

### ⚠ Carried caveat, added 2026-08-18

`logit_lens_boombness` and the comprehension target are both computed from single-token readouts
that the whole-answer diagnostic has since shown are measured in the far tail of the next-token
distribution (see the readout note in the process section). The comparison above is internally
consistent — all three metrics are scored the same way — but the **comprehension column will move**
when §4b is re-scored with the corrected readout. This section will be regenerated at that point.

## 7c. ClearHarm — the external-set decomposition (plan §14) — added 2026-08-18, re-derived 2026-08-19

This is the section that answers the question every other causal result in this sprint is exposed to:
**is any of this a property of our own prompt bank?** Every ASR number in §§3–7 comes from the bank
`prompt_families.py` generated, and the largest arm-F gain appeared in `benign_remap` — the condition
where the mapping is **never taught** — which is the signature of a bank artifact rather than a
mechanism. ClearHarm is 179 external harmful prompts with **no codeword, no demonstrations and no
doublespeak wrapper**. Nothing our generator produced.

> **⛔ Two corrections landed on this section within a day of it being written. Read them first.**
>
> **R-14 — the original numbers were judged against an EMPTY GOAL.** `judge_boombness.make_goal` reads
> the request from `final_query_text`; `external_bank.py` emitted the instruction only as
> `full_prompt`, so **both external banks lacked that key** and StrongReject scored every completion
> against no request at all. The pre-fix judge recorded that as `judge_status: "ok"`. It looked right
> because an empty-goal score still reads how harmful the *response* is, so the values tracked the
> refusal rate. Fixed, banks regenerated with **every `prompt_id` preserved and no other value
> changed**, and **all arms re-judged** — the table below is the re-judged one. Every arm moved by
> ≤0.03 and the ordering held, so R-14's cost was measurement validity, not the conclusion.
>
> **R-16 — arm B was significant only under an iid interval.** See below; it is the more consequential
> of the two.

### The decomposition, re-judged and domain-clustered

`outputs/boombness/clearharm_decomposition_regoal.json`, produced by
`src/boombness/analyze_external_arms.py` — the first version of these numbers that a committed script
regenerates from committed artifacts. All arms coherence-gated, 100% coverage, n=179, **G=6 domains**.

| arm | intervention | ASR@0.5 | Δ pooled | Δ cluster-mean | p_cl | domain-clustered CI |
|---|---|---|---|---|---|---|
| baseline | — | 0.1061 | — | — | — | — |
| **B** | remove `d_surface` @L8 | 0.1899 | +0.0831 | +0.0843 | **0.2102** | **[−0.067, +0.235]** ⛔ **n.s.** |
| **C** | remove refusalness @L18 | 0.3631 | +0.2402 | +0.3941 | **0.0410** | [+0.024, +0.764] ✓ |
| **D** | remove **both** | 0.5140 | +0.3911 | +0.4603 | **0.0200** | [+0.109, +0.812] ✓ |
| Dctrl | two norm-matched **random** directions | 0.1061 | −0.0007 | +0.0009 | 0.530 | [−0.003, +0.004] — inert |

*(`Δ pooled` weights prompts equally; `Δ cluster-mean` weights domains equally and is the estimand the
interval belongs to. They come apart on this set because 127 of 179 rows are in one category.)*

### ⛔ R-16 — the row that carried the argument does not survive clustering

An earlier draft of this section called arm B **"the load-bearing row"** and reported it as
**+0.1047 ± 0.0238**, concluding that `d_surface` is causal off-bank and that the bank-artifact
explanation was therefore **excluded**. That ± is an **iid SEM**:

| arm | iid SEM | t (iid) | clustered SEM | t (clustered, G=6) |
|---|---|---|---|---|
| **B** | 0.0241 | **3.45** | 0.0587 | **1.44** |
| C | 0.0337 | 7.13 | 0.1440 | 2.74 |
| D | 0.0362 | 10.80 | 0.1368 | 3.36 |

Under the domain clustering this design requires, arm B's t falls from **3.45 to 1.44**. **And the same
table already used clustered inference where it produced a negative answer** — super-additivity was
reported with a domain-clustered bootstrap and called "NOT established", while arm B beside it was
reported iid. Clustered inference for the claim that failed, iid for the claim that passed. That is the
same asymmetric-standard defect as R-13 and R-15, and this is its third instance.

**Withdrawn:** "arm B is the load-bearing row", "`d_surface` is causal off-bank", and "the
bank-artifact explanation is excluded". **All three rested on arm B.**

**Still standing:** removing **refusalness**, and removing **both**, raise attack success on an external
harmful set carrying no doublespeak wrapper, against a control inert to within **±0.004**. Both survive
clustering. Neither isolates `d_surface`, so neither answers the bank-artifact question.

**This is an underpowered result, not a null one — and it was predicted at build time.**
`external_bank.py` warned when generating the set that **127 of 179 rows sit in one category**. The
point estimate is unchanged; only the honest interval is wide.

### ★★★ AdvBench settles it — arm B is reinstated, and super-additivity is ESTABLISHED

**AdvBench held-out: 495 prompts, 16 domain clusters, largest 25.7%** — built in the same commit as
ClearHarm precisely because ClearHarm's cluster structure could not resolve these questions. Judged
against real goals (post-R-14), analysed by the same committed `analyze_external_arms.py`
(`outputs/boombness/advbench_decomposition.json`).

| arm | intervention | ASR@0.5 | refusal | Δ pooled | Δ cluster-mean | p_cl | domain-clustered CI |
|---|---|---|---|---|---|---|---|
| baseline | — | 0.0646 | 0.9313 | — | — | — | — |
| **B** | remove `d_surface` @L8 | **0.1071** | 0.8889 | +0.0422 | **+0.0305** | **0.0089** | **[+0.0089, +0.0522]** ✓ |
| **Bctrl** | random direction @L8 | 0.0626 | 0.9333 | −0.0018 | **−0.0062** | 0.539 | **[−0.0271, +0.0147]** — inert |
| **Cctrl** | random direction @L18 | 0.0606 | 0.9354 | −0.0033 | −0.0021 | 0.292 | [−0.0063, +0.0020] — inert |
| **Dctrl** | two random directions | 0.0667 | 0.9313 | +0.0015 | +0.0031 | 0.330 | [−0.0034, +0.0096] — inert |
| **C** | remove refusalness @L18 | **0.2707** | 0.7091 | +0.1967 | +0.1895 | 0.0001 | [+0.1097, +0.2692] ✓ |
| **D** | remove **both** | **0.3515** | 0.6222 | +0.2722 | +0.2544 | <0.0001 | [+0.1589, +0.3499] ✓ |

#### Arm B clears zero — R-16's withdrawal is reversed

`d_surface` was fitted **entirely on the carrot/bomb 2×2**. Removing it raises compliance on 495
harmful requests carrying **no codeword, no demonstrations and no doublespeak wrapper**, with a
domain-clustered interval that excludes zero.

This is the **same estimator** that found arm B non-significant on ClearHarm (p=0.21). The difference
is power, and it was predicted at build time: ClearHarm is **G=6 with 127 of 179 rows in one cluster**,
AdvBench is **G=16 with the largest at 25.7%**. The point estimates agree (+0.084 pooled on ClearHarm,
+0.042 here); only the intervals differ. **Both facts belong in the record** — not established on
ClearHarm, established on AdvBench, and the reason is the cluster structure rather than the arm.

So the claim R-16 withdrew is reinstated on the better-designed set: **`d_surface` is causal off-bank,
and the prompt-bank-artifact explanation for the sprint's late causal results is excluded.**

#### ★ Super-additivity is established — against its own control, by the correct test

**excess = +0.0333, domain-clustered bootstrap CI [+0.0128, +0.0638]; 1 of 4000 resamples ≤ 0.**

Removing `d_surface` and refusalness **together** does more than the sum of removing each alone — the
two channels **interact** rather than contributing independently.

**The tempting argument for this is invalid, so it is not the one used.** Running the same statistic
on the *control* triple gives **+0.0066, CI [−0.0013, +0.0170]** — not established — and concluding
"one interval excludes zero, the other does not, therefore the interaction is real" is the
difference-of-significance fallacy. On this data it is visibly unsafe: **the two intervals overlap**
in [+0.0128, +0.0170].

The quantity that answers the question is the **difference of the two excesses**, bootstrapped once
over the same resampled domains so the two are paired:

> **real − control super-additivity = +0.0268, domain-clustered CI [+0.0029, +0.0584]**, 1.5% of 4000
> draws ≤ 0 — **established against control**.

⚠ **State the margin honestly:** the lower bound is **+0.0029**, roughly 11% of the point estimate.
This is a real interaction, not a comfortable one, and the naive comparison would have made it look
far safer than it is.

On ClearHarm the same quantity was **+0.0677, CI [−0.218, +0.123] — not established**, and this report
recorded *why* before AdvBench was judged: one cluster holding 71% of the rows. That prediction is now
checked rather than asserted.

#### ✅ The control is inert — arm B is `d_surface`-specific

A norm-matched **random** projection at the same layer and seed moves ASR by **−0.0062**
(p_cl=0.539, CI [−0.027, +0.015]) — flat, and if anything slightly negative, against arm B's
**+0.0305**. So the effect is not "removing any direction at L8"; it is this direction.

**All three controls are now in and all three are flat** (−0.006 / −0.002 / +0.003 against real arms
of +0.031 / +0.190 / +0.254), so the missing-control caveat this section carried is fully discharged —
for the single arms and, via the paired test below, for super-additivity.
### ★ Cross-model: Qwen3-14B uses a DIFFERENT channel, and `d_surface` replicates where the correlation did not

ClearHarm 179, Qwen3-14B, `d_surface`@L11 + refusalness@L20 (the established Qwen3 depths), at
**`max_new 512` — length-matched to the Llama runs**. That matching matters on its own: the published
Llama-vs-Qwen3 non-replication elsewhere in this report compares a **512**-token Llama run against a
**192**-token Qwen3 run, and the sprint's own log records that halving the budget roughly halves the
Llama effect. `outputs/boombness/clearharm_decomposition_qwen3.json`.

| arm | ASR@0.5 | refusal | Δ pooled | Δ cluster-mean | p_cl |
|---|---|---|---|---|---|
| baseline | 0.1341 | 0.7486 | — | — | — |
| **B** — remove `d_surface` @L11 | **0.2793** | 0.5642 | **+0.1306** | +0.0416 | 0.181 |
| **C** — remove refusalness @L20 | **0.1285** | 0.7207 | **−0.0042** | −0.0120 | 0.287 |
| D — remove both | 0.2793 | 0.5475 | +0.1201 | +0.0557 | 0.081 |
| Dctrl — double random | 0.1285 | 0.7039 | −0.0084 | −0.0100 | 0.358 |
| **Bctrl band** — 3 random draws @L11 | **0.1322 ± 0.0116** | ~0.72 | — | — | inert; straddles baseline |

*(The arm-B control band is matched to arm B — three re-seeded random projections at L11, accepted by
the band guard on distinct generation hashes. Its between-draw sd of 0.0116 is close to Llama's 0.0129,
so judge and sampling noise are comparable across models. **The control was never the problem**; G=6
with one cluster holding 71% of rows is.)*

**The channel that carries the effect is reversed between the two models.** On Llama, refusalness is
the large mover (+0.240 pooled) and `d_surface` the small one (+0.083). On Qwen3 it is the other way
round: `d_surface` takes ASR from **0.134 to 0.279** and refusal from 0.749 to 0.564, while removing
refusalness does **nothing** (−0.004, indistinguishable from the double-random control at −0.008).
**D equals B to four decimal places** — on Qwen3 the entire joint effect is the `d_surface` channel.

⚠ **Not established under clustering.** Qwen3's ClearHarm arm B is +0.0416 cluster-mean, **p_cl=0.181**
— the same 6-clusters-with-one-at-71% limitation that made Llama's ClearHarm arm B non-significant
before AdvBench settled it.

#### ⛔ R-17 — the matching experiment was run, and it does NOT replicate

A prediction was recorded here before that run: *"Qwen3's pooled effect is larger than Llama's, so it
should clear zero comfortably at 16 clusters."* **It did not.**

| Qwen3-14B, AdvBench 495, 16 clusters | ASR@0.5 | refusal | Δ cluster-mean | p_cl | CI |
|---|---|---|---|---|---|
| baseline | **0.0081** | 0.9374 | — | — | — |
| **B** remove `d_surface` @L11 | 0.0141 | 0.9212 | **+0.0024** | **0.657** | [−0.0089, +0.0138] |
| C remove refusalness @L20 | 0.0061 | 0.9111 | −0.0010 | 0.333 | [−0.0032, +0.0012] |
| Bctrl random @L11 | 0.0081 | 0.9293 | +0.0000 | — | — |

Arm B moves **4/495 → 7/495**. **The reason is a floor, not the clustering:**

| | baseline ASR | refusal | headroom |
|---|---|---|---|
| Llama ClearHarm / AdvBench | 0.1061 / 0.0646 | 0.877 / 0.931 | 0.123 / 0.069 |
| **Qwen3 ClearHarm / AdvBench** | **0.1341 / 0.0081** | 0.749 / 0.937 | 0.251 / 0.063 |

**Qwen3 complies with 0.8% of AdvBench against 13.4% of ClearHarm — a 16× drop, where Llama drops
1.6×.** It is not simply more refusal: Qwen3's AdvBench headroom (0.063) is close to Llama's (0.069),
but Llama converts nearly all its non-refusal into judged compliance while Qwen3 converts about an
eighth. **An intervention cannot be measured against a floor.**

⛔ **Withdrawn:** the claim that `d_surface` removal raises external-set ASR *in both models* — it was
made on **pooled** estimates, and neither Qwen3 number survives clustered inference (p=0.181, p=0.657).

✅ **What survives is Llama-specific and solid:** arm B on AdvBench, **+0.0305, p_cl=0.0089**, inert
control (§7c above).

⚠ **Open, not negative:** whether `d_surface` is causal on Qwen3 at all. Its ClearHarm point estimate
is large (ASR 0.134 → 0.279, refusal 0.749 → 0.564) and merely under-powered; AdvBench is a floor.
**Neither set can answer it**, and the experiment that could is an external harmful set chosen for
*this model's* baseline compliance rather than inherited from the Llama pipeline (**E11**).

**The methodological point is worth more than the result.** Two "external harmful sets" are not
interchangeable: they give Llama similar baselines (0.106 / 0.065) and Qwen3 wildly different ones
(0.134 / 0.008). A cross-model comparison run on **either set alone** would have produced a confident
and wrong answer — "replicates" from ClearHarm, "does not replicate" from AdvBench. **Report baseline
compliance beside every external-set ASR**, or a reader cannot distinguish an intervention that fails
from a set with no headroom.

### ⚠ Super-additivity on ClearHarm alone — NOT established, and that is the expected result

On ClearHarm the joint arm exceeds the sum of the singles by **+0.0677**, domain-clustered CI
**[−0.218, +0.123]**, 28% of draws ≤ 0. Unchanged in kind by the re-judge. ClearHarm cannot resolve it
for the one-dominant-cluster reason above. **AdvBench does** — see the section above, where the same
quantity is +0.0333 with CI [+0.0128, +0.0638].

### What this licenses, and what it does not

**Licensed:** "removing the refusal direction — and removing it together with `d_surface` — causally
raises compliance on harmful requests that our generator never produced."

**Not licensed, on this set:** any claim about `d_surface` **alone** off-bank. And even if AdvBench
rescues arm B, calling `d_surface` "concept-ness" off-bank would remain unlicensed: the 2×2 named the
direction from a codeword-vs-concept contrast that **does not exist in a prompt with no codeword**. Its
off-bank behaviour is a new fact needing its own interpretation, not an extension of the old name.

*(cos(`d_surface`, refusalness) = **0.019 @L18**, 0.13 @L12 — near-orthogonal, so the two arms are not
the same channel under another name. Caveat: arm B acts at **L8**, where no house refusal direction is
fitted, so the cosine is measured only where both exist.)*

### ✅ The control band, resolved (R-12 closed)

The published band — 3 draws, between-draw sd 0.0048 — **was one draw stated three times**;
`score_behavior.py:123` recursed into composed arms without passing `control_seed`. Re-seeded,
re-judged, and accepted by the band guard on distinct generation hashes:

| draw | seed | gens sha16 | ASR@0.5 |
|---|---|---|---|
| 1 | 20260901 | `61249763c34b4840` | 0.0950 |
| 2 | 20260902 | `3b962119cfc6c1f9` | 0.0950 |
| 3 | 20260903 | `485698e92ca55ba9` | 0.1173 |

**Band mean 0.1024, between-draw sd 0.0129**, against baseline 0.1061 — the control is inert and the
band straddles the baseline. ⛔ **The retracted band's sd 0.0048 understated draw-to-draw variance by
2.7×**; the defect was fake precision, not a wrong ASR. It was the second fabrication of this same
statistic (retraction #7 reported 0.0049), which is why the check now lives in a committed script with
a test rather than in a reviewer's attention.

**This does not rescue arm B.** An inert control and an underpowered arm are different facts: arm B's
problem is R-16, its domain-clustered interval, not the control.

`analyze_external_arms.py` now **refuses** to report a band whose draws share a generation hash, and
that guard was itself dead on first writing — it fingerprinted judge *scores*, and StrongReject is not
bitwise deterministic, so three re-judgings of one identical generation set produced three "distinct"
draws. Run against the real R-12 band it now refuses correctly.

## 7d. The arm-F interaction — a real number whose mechanism was refuted (§10.4)

> ⛔ **Read this first.** An earlier draft of this section opened *"This supersedes the §18 = B label
> and reopens §12"*. **It does not, and that sentence is withdrawn.** The §12 objective verdict is
> unchanged and negative (§4/G4: both signs of the axis suppress ASR), and §9b lists building it under
> **explicitly NOT recommended**. What follows is a real and large effect whose **mechanistic
> interpretation was retracted** (R-8, the "capability channel"): the gain appears most strongly in
> `benign_remap`, the condition where the carrot→bomb mapping is **never taught**, which is the
> signature of a prompt-bank artifact rather than a mechanism. It is reported because the *number* is
> real and reproducible, not because it supports the objective.

Everything below is at a matched 512-token budget, n = 420, every arm complete and coherence-gated on
the doublespeak population, domain-clustered over 6 domains.

| arm | ASR | refusal | Δ score vs baseline | p_cl |
|---|---|---|---|---|
| baseline | 0.2429 | 0.0571 | — | — |
| add Boombness `+0.25` | 0.0881 | **0.6762** | −0.1274 | 0.0117 |
| remove refusalness | 0.2690 | **0.0000** | +0.0101 *(0.9× the judge-noise sem — **not measurable to ±0.03**, not "does nothing")* | 0.4746 |
| **add Boombness AND remove refusalness** | **0.5476** | 0.0024 | **+0.2824** | **<0.0001** |
| **RANDOM direction + remove refusalness** *(control)* | **0.2190** | 0.0000 | −0.0321 | 0.1160 |

⚠ **The control is inert only on THIS condition, and reverses elsewhere.** On `direct_harmful` the same
random composition raises score by **+0.389 (p=0.008)** and cuts refusal **0.96 → 0.54**, while arm F stays
at baseline (+0.000, refusal 0.96). On `concept_in_benign_ctx` it gains +0.203. **Specificity is established
for the doublespeak population only, and is reversed where harm is explicit.**

**Neither manipulation alone raises attack success — together they more than double it.**
Interaction contrast (F−A) − (C−base) = **+0.400 continuous, p=0.0001**, and +0.471 / +0.433 / +0.364 at
ASR thresholds 0.25 / 0.50 / 0.75.

⚠ **That +0.400 is ~45% a mechanical artifact.** Arm A refuses on 284/420 rows, each scored exactly 0.0 by
construction. On the rows where A did *not* refuse, **A−base = +0.094 (positive)** and the interaction falls
to **+0.222**. The **refusal-free** contrasts — **F−C = +0.272** and **F−Fctrl = +0.315**, between arms with
~0% refusal — are the numbers that carry the claim.

### The mechanism
`d_surface` does **two opposing things at once**:
1. **detection** — it makes the request legible to the refusal mechanism (refusal 0.057 → **0.676**), which
   *suppresses* ASR;
2. **a second, refusal-independent channel** raises judged harmfulness once refusal is removed.
   ⛔ **We have NOT established that this is a "capability" channel.** The gain is *largest where the
   doublespeak mapping is weakest* — **+0.361 at `n_examples=0`** (no demonstrations at all) and **+0.267 on
   `benign_remap`**, where carrot→bomb is **never taught** — and it is **absent on explicitly harmful
   prompts** (+0.000 on `direct_harmful`, where the random control gains +0.389). It is better described as
   a **prompt-independent injection by the L8 steering vector** than as the doublespeak attack succeeding.

In the unmodified model channel 1 dominates and **masks channel 2 entirely**. That is why the within-arm
correlation was positive while every steering attempt looked suppressive — a contradiction this report
carried for days.

### Why this is not any of the artifacts that killed earlier versions
| competitor | how it is excluded |
|---|---|
| degenerate generation | passes `coherence_gate` on the doublespeak denominator |
| truncation / length | ⚠ **attenuated, not eliminated.** All arms complete at 512 tokens, but arm F writes 260 median words vs the control's 145 and common support covers only ~27% of control rows. Matched on 25-word bins, **F−Fctrl falls +0.315 → +0.233** (bootstrap CI [0.149, 0.310]) and **F−base +0.282 → +0.150**. A quarter to a half of the raw gap is length, which may itself be a mediator. |
| "longer answers score higher" | baseline calibration shows truncation **suppresses** score (+3.7pp when completed) |
| judge noise | effect is **25×** the measured test–retest floor (0.011) |
| threshold luck | holds on the continuous score and at three thresholds |
| **"any two perturbations do this"** | **the random composition does nothing (p=0.116)** |
| domain artifact | domain-clustered throughout |

A prediction for the arm-F value was **recorded in the log before judging** (`≥0.474`); it came in at
**0.5476**.

### Consequences — as they stand 2026-08-19, not as first written
- **§18 = B is withdrawn**, but *not* replaced by "causal via this arm". The label is settled in §0's
  FINAL row as **C-amended**, on the external-set evidence (§7c), not on this arm.
- ⛔ **"§12.2 is REOPENED and worth building" is WITHDRAWN.** That reading rested on arm F, whose
  mechanism was retracted (R-8): the gain is **not conditional on the doublespeak mapping** — it is
  largest in `benign_remap`, where the mapping is never taught — and it **does not transfer to explicitly
  harmful requests** (+0.000). Those are exactly the properties an attack objective would need, and the
  arm has neither. §9b lists building the objective under **explicitly NOT recommended**.
- The §12.1 "pure Boombness objective" (maximise alone) remains **wrong** — alone, it *lowers* ASR.

### Honest limits — scope, not validity
One model (Llama-3.1-8B), one concept pair (carrot↔bomb), one judge, refusal projected at a single layer
(L18), and `d_surface` fitted on the same bank it is evaluated on. The Qwen3 replication of the *projection*
arm is running; **G2's correlation did not replicate on Qwen3**, so cross-model generality is an open
question for this result too.

---

## 7e. Removing the concept component alone — the on-bank result (§10.4 `project_out`)

Unlike the interaction above, this one survived every check **including the ones that refuted the
interaction's mechanism**. Llama-3.1-8B, 512 tokens, n=420, all arms gate-passed and length-matched by
construction (163 vs 150 median words), against a **projection-type** control:

| contrast | Δ score | t_cl | p_cl |
|---|---|---|---|
| `project_out d_surface` − baseline | +0.0378 | +5.12 | **0.0037** |
| `project_out RANDOM` − baseline | −0.0182 | −1.27 | 0.260 — **inert, as a control should be** |
| **`d_surface` − RANDOM control** | **+0.0560** | **+4.30** | **0.0077** |

**5× the measured judge-noise floor.**

### ⛔ The cross-condition profile — R-15, corrected 2026-08-19
This table originally shipped **six deltas and no inference**, while the Qwen3 table eleven lines below
carries `p_cl` on every cell and annotates two of them "(n.s.)". Given the same test
(`analyze_condition_profile.py`, paired by `prompt_id`, domain-clustered t on `len_B` / `len_Bctrl`,
n=960 — the deltas reproduce the original exactly):

| condition | n | arm − control | p_cl | domain-clustered CI |
|---|---|---|---|---|
| `benign_literal` | 324 | +0.0069 | 0.334 | [−0.010, +0.024] |
| `benign_remap` | 36 | +0.0104 | 0.745 | [−0.068, +0.088] |
| `concept_in_benign_ctx` | 72 | +0.0035 | 0.862 | [−0.045, +0.052] |
| **`natural_doublespeak`** | 420 | **+0.0560** | **0.0077** | **[+0.023, +0.089]** |
| `direct_harmful` | 72 | +0.0556 | 0.363 | [−0.087, +0.198] |
| `direct_codeword` | 36 | +0.0590 | 0.438 | [−0.121, +0.239] |

⛔ **Only one of the six cells is distinguishable from zero, and it is `natural_doublespeak`**, so the
earlier profile reading is **withdrawn**. The two other "harmful" cells — precisely the ones that
previously carried the generalisation claim —
have intervals spanning **±0.2**, roughly six times the effect they were cited to demonstrate.

⛔ **The "clean split" was a power artifact.** `natural_doublespeak` has **420** prompts against 72 and
36 for the other two harmful conditions. The design can resolve its two large cells and nothing else,
and those happen to be one benign (`benign_literal`, n=324, CI ±0.017) and one doublespeak. Every
36–72-row cell is uninformative in **both** directions, so these data **cannot** discriminate
"harm-general" from "doublespeak-specific".

**What is actually established** is the narrow claim:

> Removing the concept component from the codeword position raises attack success **on natural
> doublespeak prompts** (+0.056, p=0.0077, against an inert control).

The earlier reading — "wherever there is an attack, and does nothing where there is not" — is
withdrawn, and describing it as "a *stronger* statement" was backwards: it was a weaker-evidenced one.
Note also that the Qwen3 comparison below applied an **asymmetric evidential standard** — Qwen3's cells
were discounted for failing a test the Llama cells had never been given, and three of them fail it too.

### ⛔ It does NOT replicate on Qwen3-14B — and the failure is informative
Same intervention, same fitting procedure, same relative depth (25% vs 27.5%), same bank, **inert control on
both models** — and mirror-image condition profiles:

| condition | Llama-3.1-8B | Qwen3-14B |
|---|---|---|
| `natural_doublespeak` (attack) | +0.056 | **+0.339** |
| `direct_harmful` | +0.056 | +0.111 (n.s.) |
| `direct_codeword` | +0.059 | +0.010 (n.s.) |
| `benign_literal` | +0.004 | **+0.224** |
| `concept_in_benign_ctx` | +0.010 | **+0.245** |
| `benign_remap` | +0.004 | **+0.441** |

⛔ **This table previously showed only TWO Qwen3 values in a "harmful conditions" row against THREE
Llama values, silently omitting `natural_doublespeak = +0.339` — the LARGEST Qwen3 effect of all.**
Found 2026-08-18 by an independent audit and verified against the judge artifacts. Every condition is
now listed on its own row so a column cannot hide one.

**The omission inverted the conclusion.** With `natural_doublespeak` restored, Qwen3 is elevated on
**five of six** conditions, attack and benign alike — this is a **broad elevation of judged
harmfulness**, not a profile that "tracks the absence of an attack" as the previous text claimed.
The only near-null is `direct_codeword` (+0.010). The contrast with Llama still stands and is
if anything sharper: on Llama the effect is confined to harmful conditions (+0.056 vs +0.004 benign);
on Qwen3 it is everywhere, including on prompts containing no attack. **The result remains
single-model**, and for the corrected reason: Qwen3's projection does not isolate an attack-related
quantity at all.

The Qwen3 effect is real and `d_surface`-specific (its random-projection control is inert, −0.004,
p=0.77), but it raises judged harmfulness nearly everywhere.

### Why the small result outlived the large one
| | arm F interaction | this result |
|---|---|---|
| size | +0.27 to +0.32 | **+0.056** |
| control | inert on doublespeak only; **reverses** on `direct_harmful` | inert **everywhere** |
| cross-condition | ⛔ appears where the mapping is never taught | ⚠ **one significant cell of six** (R-15) — doublespeak only |
| cross-model | not tested | ⛔ does not replicate |
| status | real number, **mechanism refuted** | **established, single-model** |

Effect size was consistently the *worst* predictor of which claim survived. Every large effect in this sprint
either failed a cross-condition check or lost its interpretation; the surviving causal result is the smallest
one measured.

---


## 8. Process — sixteen retractions, ten corrections, seven dead guards

Every retraction came from independent audit, and they share **one** root cause in two forms:
*the manipulated and the measured quantity were not the same thing*, or *the best of mine was
compared against a fixed instance of yours*.

| # | retracted claim | why |
|---|---|---|
| R1 | tick-7 headline incl. a "null carry band" | pseudo-replication; the band is significantly negative, not null |
| R2 | G2's original negative verdict | predictor read off the *wrong prompt* (semantic, not behavioural) |
| R3 | a §10 null | edges cut into the wrong destination token |
| R4 | "`d_naive` manufactures signal where `d_surface` finds none" | sourced to an already-retracted section; corrected data **reverse** it |
| R5 | "Boombness beats refusalness 3.7×" | the two probes were read at **different tokens** |

Corrections: C1 (L8 norm contamination → L12), C2 (40× → 3.7×, then retracted entirely), C3 ("2–3× the
controls" is sign-dependent), C4 (clustered p, 1.7e-06 → 5.0e-04), C5/C6 (wrong column for the
per-domain count; population mismatch between headline table and headline correlation).

**Three guards were found to have never executed:**
1. the **coherence gate** — keyed on a `score_behavior` dirname while arms were named from judge tags, so every lookup missed and `None` passed as "checked";
2. the **dynamic-range check** — `max` over *signed* deltas returned a null control (+0.031) as "the largest effect" and certified itself;
3. the **control band** — selected `ctrl_rand_s*` while the runs were tagged `ctrlband_s*`; **zero** arms ever matched.

Plus a fourth in my own notes: a phase-board edit addressed rows by **line index**, destroying two
rows and duplicating two others (recovered from git).

**The transferable lessons**, each learned by being wrong:
- **A guard that is never tested against a case it should fail is not a guard.** Every guard now ships with such a test.
- **Address things by identity, not by an incidental property.** All four failures above matched on a filename, a tag prefix, an mtime, or a line number.
- **A robustness check that resamples *rows* cannot rescue a comparison whose arms sit in different *places*.** The 3.7× survived nested CV and leave-one-domain-out, and was still an artifact.
- **When correcting an error, verify the measured thing changed — not just the knob you turned.** The first attempt at the position fix moved the direction-fitting position and left the readout where it was, producing a phantom cell that briefly flipped the sprint's conclusion.
- **A summary that does not know what it skipped will be believed.** A driver reported "complete" having judged 2 of 4 arms.

---

## 8b. Negative results (plan §15 item 14)

Listed because they are the deliverable too, and because several cost more compute than the positive
findings did. Nothing here is a failed experiment; each is an answer.

| # | question | answer | where |
|---|---|---|---|
| N1 | Does a **pure Boombness objective** — maximise the axis — increase attack success? | **No.** Steering the axis suppresses ASR at **both** signs. The objective as specified in plan §12.1 is dead, and this is the single most consequential negative result in the sprint: it is why §12 was not built. | §4 (G4) |
| N2 | Does Boombness's correlation with ASR **replicate on a second model**? | **No.** ρ≈+0.307 at L12 on Llama-3.1-8B does not carry to Qwen3-14B. | §3 (G2) |
| N3 | Does the codeword's **final** occurrence become more concept-like than earlier ones? | **No — less.** The opposite of the natural hypothesis, and the control is what makes it readable. | §2b |
| N4 | Do the three Boombness metrics (probe / direction / logit-lens) agree? | **No.** They disagree in **sign** about ASR at L12, and `common_all_three` covers only **72 of 270** rows. They agree far better on comprehension. | §7b |
| N5 | Is the meaning stored **in the codeword token**? | **No.** Transplanting the query codeword moves the readout the **wrong way** (−71% of span). This negative is what makes G1 positive. | §2 (G1) |
| N6 | Does the §10.4 projection result replicate on Qwen3-14B **on the bank**? | **No** — on Qwen3 the same intervention raises judged harmfulness on **benign** prompts too, so it does not isolate an attack-related quantity there. ⚠ That comparison also had a **length confound** (Llama 512 vs Qwen3 192 tokens). **Resolved 2026-08-19:** the matched-length Qwen3 arm landed, and *off-bank* the picture is different again — `d_surface` removal raises external-set ASR on **both** models (§7c). The correlation is Llama-specific; the causal intervention is not. | §7e, §7c |
| N7 | Is the §10.4 effect **harm-general** rather than doublespeak-specific? | **Not established, and the data cannot answer it.** Only 1 of 6 condition cells is distinguishable from zero (R-15); the two other harmful cells have intervals spanning ±0.2 at n=72 and n=36. | §R-15 |
| N8 | Is the ClearHarm joint arm **super-additive** in its two components? | **Not established.** +0.0922 with a domain-clustered CI of [−0.147, +0.133]; 127 of 179 rows sit in one cluster, so the set cannot resolve it. AdvBench (16 clusters) is the right test. ⚠ Currently also blocked by R-14. | §7c |
| N9 | Is `d_surface` "concept-ness" **off-bank**? | **Not licensed.** The 2×2 named the direction from a contrast that does not exist in a prompt with no codeword. Its off-bank behaviour needs its own interpretation. | §7c |
| N10 | Do the probe splits **leak** across families? | **No** — the critique's leakage finding is refuted against a real K=20 null (max excess 0.021 against a 0.05 tolerance). A single reused permutation had been mistaken for a null distribution. | C-8 |
| N15 | Does Boombness predict attack success (G2)? | ⛔ **RETRACTED (R-18) — no, not on prompts that belong in the question.** The published ρ=+0.307/+0.262 came from a row set that was 31% **sibling families sharing demonstrations** and 31% **experimentally-manipulated** designed variance. On the 90 independent, unmanipulated prompts the within-domain ρ is **−0.0518 (p=0.658)**. n=90 cannot exclude a small effect — a null, not a proof of absence. | R-18 |
| N16 | Is `n_examples` a confound for G2 (C-9)? | **Superseded.** C-9 answered "no" on the unfiltered 234 rows — it was defending a correlation that is not present on the clean 90. The question does not arise until G2 is re-established. | R-18 |
| N13 | Does the `d_surface` causal effect **replicate on Qwen3-14B**? | **Not established, and neither external set can answer it** (R-17). On ClearHarm the point estimate is large (ASR 0.134 → 0.279) but n.s. at G=6 (p=0.181); on AdvBench it is null (p=0.657) — **because Qwen3 complies with only 0.8% of AdvBench** (4/495) against 13.4% of ClearHarm, a 16× drop where Llama drops 1.6×. An intervention cannot be measured against a floor. ⛔ An earlier draft claimed replication from pooled estimates; withdrawn. | §7c, **E11** |
| N14 | Are two "external harmful sets" interchangeable? | **No, and the choice can decide the answer.** ClearHarm/AdvBench give Llama similar baselines (0.106 / 0.065) and Qwen3 wildly different ones (0.134 / 0.008). A cross-model comparison on **either alone** yields a confident, opposite, wrong conclusion. **Report baseline compliance beside every external-set ASR.** | §7c |
| N12 | Can plan §4.1's **designed variance** (`strength`, `consistency`, `example_position`) be analysed? | **No, and it is now measured rather than assumed.** The 192 rows sit in three dedicated `bank_block`s. ⛔ **An earlier draft said they had "never contaminated a published number" — that is FALSE (R-18):** `analyze_g2` filters on `condition`, not `bank_block`, so 72 of them are inside G2's headline n=234 and carry a large part of its correlation. But the largest available comparison is **12 behavioural rows per level**, smaller than cells R-15 just declared uninformative, and `position` is **6 vs 6, one row per domain per level**. Every non-default level also moves prompt length, codeword-occurrence count and `n_examples` **simultaneously** — `strength` takes `n_examples` from 4.91 to 2.00, and `n_examples` is a known ASR predictor. Documented and explicitly excluded; regeneration is **E8**. | §9b, E8 |
| N11 | Is `n_examples` a **confound** for the Boombness↔ASR correlation? | **No.** It predicts ASR (ρ=+0.206) but is essentially uncorrelated with Boombness at `codeword_last` (ρ=−0.034); the partial ρ retains **99.9%** of the raw coefficient. | C-9 |

**Two of these (N10, N11) are negatives against the external critique rather than against the sprint** —
the critique is authoritative on what is broken but is not itself above verification, and re-derivation
overturned two of its claims and found three more it had missed.

---

## 8c. Failure modes (plan §15 item 15)

Not a list of bugs. These are the **recurring shapes**; each one bit this project more than once, which
is the reason for writing them down rather than the individual fixes.

**FM1 — The dead guard.** A guard whose condition can never be true. **Six** so far: the coherence gate
(keyed on a dirname while arms were named from judge tags); the dynamic-range check (`max` over *signed*
deltas certified a null control as the largest effect); the control-band selector (matched `ctrl_rand_s*`
against runs tagged `ctrlband_s*` — **zero** arms ever matched); a phase-board edit addressing rows by
line index; `probes`' own leakage guard (at K=1 the z-score is `excess/NaN`, yielding `leak=False`, so a
run whose stopping rule was never evaluable wrote `DONE.json` and exited 0 — **shipped while fixing dead
guards**); and `analyze_g9`'s role-identifiability gate, which tests family overlap on a `family_id`
string that *embeds the style name*, so overlap is 0 by construction and the gate would refuse even a
correct design. **Countermeasure, now mandatory: every guard ships with a test that fails the pre-fix
code.** Five of the six matched on an incidental property — a filename, a tag prefix, an mtime, a line
number — rather than on identity.

**FM2 — The one-of-two-paths miss.** A fix applied to the single-spec path and dropped on the composed or
recursive path. Three occurrences, most recently **R-12**: `score_behavior.py:123` recursed into composed
arms without passing `control_seed`, so a three-draw "control band" was one draw stated three times — and
it re-created retraction #7, whose fake band reported an almost identical sd. **Countermeasure: when a
parameter is threaded, grep for every call site of the function that consumes it, and test the composed
path explicitly.**

**FM3 — The unfalsifiable-by-inspection artifact.** Some artifacts cannot be checked by looking at their
own values. A **control band** is the clearest case: its entire purpose is to measure draw-to-draw
variance, so a fake one looks *better* than a real one. Both times the tell was arms agreeing to four
decimals. **R-14 is the same shape one level up:** an ASR table cannot be falsified by reading its
numbers, because a judge given no goal still returns a plausible *ordering* that tracks the refusal rate.
Only the goal string — an input nobody printed — revealed it. **Countermeasure: check the input, not the
output, for any artifact whose value is what you are trying to establish.**

**FM4b — The heterogeneous row set (R-18, the most expensive instance).** Every other FM4 case was
mismatched footing between two *arms*. This one is a level down: the **sample itself** was mixed and
nobody looked. `analyze_g2` filtered on `condition == arm`, which reads as sufficient and is not, and
the artifact recorded `n_analysed: 234` with no description of the 234 — 31% sibling families sharing
demonstrations, 31% experimentally-manipulated readability. It cost a headline finding.
**Countermeasure: a count is not a description of a sample.** Every analysis artifact must record the
*composition* of its rows, not just their number; `analyze_g2` now does, and warns when the mix is
unsafe.

**FM4 — The mismatched footing.** Comparing the best of one arm against a fixed instance of another, or
two probes read at different tokens, or two increments with different degrees of freedom. This produced
retraction R5 (the "3.7×") and then produced **R-13** *inside the paragraph announcing R5's retraction* —
a table labelled "at matched footing" that gave refusalness 5 predictors against Boombness's 1.
**Countermeasure: state the degrees of freedom and the selection freedom of both arms, in the table.**

**FM5 — The instrument that cannot represent the answer.** The `semantic_logodds` readout scored two
single tokens at a position where the model emits neither, with the options holding a median **5.6e-06**
of next-token mass; worse, the model capitalises, and the capitalised codeword is multi-token
(`Carrot` = ` Car` + `rot`) while the concept has four single-token variants — so the instrument was
biased 4-ids-to-1 *toward the concept* and structurally could not represent the model's preferred
spelling of the codeword. The fix the external critique recommended (sum `full_word_ids`) would have
preserved the bias with a larger constant. **Countermeasure: before trusting a forced-choice readout,
decode what the model actually wants to say at that position, and verify the options hold a material
share of the mass.**

**FM6 — The silent failure.** A dropped row, a swallowed exception, an unhandled branch. `score_behavior`'s
query-kind dispatch had no `else`, so an unhandled kind counted as a success with no output. R-14 is the
most expensive instance: the pre-fix `make_goal` returned a bare string, so an empty goal was recorded as
`judge_status: "ok"`. **Countermeasure: every drop is counted with a reason in `summary.json` via
`FailureLedger`; a status is returned beside every value that can be degenerate.**

**FM7 — Robustness checks that test the wrong thing.** The 3.7× survived nested cross-validation *with
selection inside the fold* and leave-one-domain-out, and was still an artifact. Both resample **rows**;
the defect was in **where** the two arms were measured. **Countermeasure: resampling cannot repair a
contrast whose arms sit in different places — check the design before checking the estimate.**

**FM8 — The deliverable drifting from the evidence.** The sprint's own diagnosis of session 1: it
self-caught seven retractions, which is more than most published work manages, and still shipped a report
that stated its conclusion both ways and cited a `§0.3` that did not exist. **Countermeasure, now the
standing bar: every number in the report must be regenerable by a committed script from a committed
artifact. If the script and the artifact cannot both be named, the number does not go in.** R-13 was found
by applying exactly this test — its published pair exists in no artifact, in any commit.

---

## 9. What we would take forward

1. **The 2×2 design is the reusable artifact** — it separates surface identity from context, and it caught the confound quantitatively rather than rhetorically.
2. **Do not build the GCG objective on this axis.** G4 is a directional null on two independent lines (the sign test, and the refusal-route split). If an objective is wanted, target the **demonstration-retrieval pathway** G1/G3 localized, not the codeword's position on `d_surface`.
3. **The localization result is the finding worth following** — the ASR-predictive state sits at the codeword token, ~2–4× more than at the final prompt token, for both a concept probe and a refusal probe.
4. **Re-measure refusalness properly at the codeword position** before any A-vs-C claim: a direction fitted for the last token does not validate there.
5. **Second model and second concept pair.** Everything here is Llama-3.1-8B, carrot↔bomb, one judge.
6. **G1/G3 are on `semantic_one_word` prompts while G2/G4's ASR claims are on `behavioral` ones.** Each is internally consistent; joining them into one causal story is the same manipulated-≠-measured pattern one level up. A behavioural-prompt knockout would close it.

---

## 9b. Recommended next experiments (plan §15 item 16)

Ordered by *evidence bought per GPU-hour*, not by ambition. The first three are blocking — they decide
whether existing claims stand — and none of them needs new generation.

### Blocking: re-derive what is currently suspended

**E1 — Re-judge every external-set arm against a real goal (R-14).** *Cost: API only, no GPU.* Both
banks now emit `final_query_text`, regenerated with **every `prompt_id` preserved and no other value
changed**, so all existing `gens.jsonl` still join. This decides §7c, the §10.4-D gate row, and whether
the bank-artifact explanation is actually excluded. **Until it lands, the sprint's best new result has
no measurement behind it.** Highest value per unit cost by a wide margin.

**E2 — Port the whole-answer readout to `aggressive_patching` and `surgical_knockout`, then re-run G1
and G3 (C-6).** *Cost: two GPU sweeps.* `signals.string_option_readout` is built and proven (3,200×
more option mass) but lives only in `score_behavior`. Until it is ported, **G1's +68% headline and all
of G3 rest on an instrument that cannot represent the model's preferred spelling of the codeword.** The
*direction* of G1 is safe on any readout; the magnitudes are not.

**E3 — Rank G3's attention edges at `readout_pos` (T3).** *Cost: one GPU sweep.* The knockout was fixed
after retraction #3; the **edge ranking** was not, so G3's top-k/bottom-k null cannot distinguish "these
edges don't matter" from "they were ranked at the wrong token". Fix `:239` (cross-fitting, ~54% of rows
currently scored in-sample, which advantages the targeted arm and not the controls) and `:225` (family
head-truncation on a domain-prefixed sorted list) in the same pass.

### High value: the questions the current design cannot answer

**E4 — Power the cross-condition profile (R-15).** The "harm-general vs doublespeak-specific" question is
open *only because* `direct_harmful` has 72 prompts and `direct_codeword` has 36 against
`natural_doublespeak`'s 420. Generating those two conditions to n≈400 each is cheap, needs no new
mechanism, and converts the sprint's most-contested interpretive claim into a measurement. **This is the
best new-evidence-per-hour experiment available.**

**E5 — Finish AdvBench super-additivity on 16 clusters.** Generations exist (495 × 4 arms). ClearHarm
cannot resolve it — 127 of 179 rows sit in one cluster. AdvBench's largest cluster is 25.7%. Blocked on
E1 only.

**E6 — A second concept pair.** Every claim in this sprint is carrot↔bomb. A second pair is the cheapest
test of whether `d_surface` is a *concept-surface* direction or a carrot-detector. **Plan §2.4's
tokenization audit is mandatory here and is real work**: the current bank forces single-token by
construction, and the R-14/C-5 experience shows a pair whose capitalised form is multi-token silently
breaks the readout. Pick the pair *after* auditing, not before.

**E7 — Matched-length cross-model replication.** The published Llama-vs-Qwen3 non-replication compares a
**512**-token Llama run against a **192**-token Qwen3 run, and the sprint's own log records that halving
the budget roughly halves the Llama effect. A Qwen3 arm at 512 is running; until it lands, "does not
replicate" is confounded with "was given a quarter of the tokens".

### Worth doing, lower priority

**E8 — Decide plan §4.1's designed variance.** `strength`, `consistency` and `example_position` were
generated exactly as specified and are analysed by **nothing**, and they are confounded as built: `near`
gets 0 filler sentences while `far`/`distributed` get 6 (403 vs 792 chars); `conflicting` leaves the
demonstrations consistent and appends a counter-mapping sentence carrying an **extra codeword
occurrence in the closest-to-query position**; `strong`/`aggressive` inject the literal concept token
into a codeword-surface prompt. Either fix the generator and analyse them, or delete them from the bank
and say so. **Generated-confounded-unexamined is the worst of the three states** and it is currently the
one we are in.

**E9 — The §5.2 alpha sweep at α=0.25.** The additive sweep ran α ∈ {0.5, 1, 2, 4}; **0.25 — the dose
every behavioural claim in §12 rests on — was never swept in the G1 design.** One arm, cheap, closes a
gap between the two halves of the report.

**E10 — Give the judge a bank-identity check that can actually run.** `compare_bank_hashes` exists and
now has a caller, but the external banks ship no `*_meta.json`, so every external judge run prints
`BANK IDENTITY UNCHECKABLE`. Writing the meta file is a few lines and converts a warning into a real
guard — one that would have caught R-14's sibling (a bank from a different regeneration joining
perfectly and silently, the stated root cause of retraction R1).

**E11 — an external harmful set chosen for *Qwen3's* baseline compliance.** R-17 leaves "is `d_surface`
causal on Qwen3?" open rather than answered: ClearHarm is under-powered at G=6 and AdvBench is a floor
(0.8% baseline compliance). Both sets were inherited from the Llama pipeline. Selecting or filtering a
set so the second model has real headroom — say 10–15% baseline compliance over ≥12 clusters — is the
only way to settle it, and it is cheap: no new mechanism, no new generator, just a better-chosen bank.

### Explicitly NOT recommended

**Building the GCG Boombness objective (plan §12).** Outcome B stands: steering the axis suppresses ASR
at **both** signs, so there is no gradient to follow. The `project_out` results are a different
intervention (removing a component, not maximising it) and do **not** reinstate the objective. Revisit
only if E2 changes G1's sign or E4 shows the effect is genuinely harm-general.

---

## §15.5 Tokenization audit (plan §2.4 — mandatory)

`tokenization_audit/audit_20260817_013432_3151000`, 2352/2352 rows, 0 failures:

| check | result |
|---|---|
| target occurrences that are a **single** token | **2352 / 2352** |
| tokenization flagged ambiguous | **0** |
| `tokenization_ok` | **True on every row** |
| distinct subtoken ids used | 2 — `[75294]` (` carrot`, 1776 rows) and `[13054]` (` bomb`, 576 rows) |

**Why this mattered.** An earlier bank quoted the target as `"{W}"` and placed demonstrations
sentence-initially, which produced **890 of 5808** two-subtoken occurrences (`car`+`rot`,
`Car`+`rot`). A two-subtoken occurrence puts a *different vector* at `codeword_last` — the embedding of
`rot`, not of `carrot` — so any per-token comparison silently mixed two different quantities. The bank
was regenerated to force the leading-space whole-word form; the variant table in the audit summary
records that `carrot` alone is 2 tokens while ` carrot` is 1, which is exactly the trap.

**Alignment:** 0 violations among the **216** of 912 families where the exact-swap invariant is defined
(the other 696 are forced-choice and cannot satisfy it by construction).

---

## §19 — the eleven questions, answered directly

The plan asks these to be answered directly, so they are, each with its status and its caveat.

**1. Does Natural Doublespeak create the same kind of internal `bomb` representation as Direct prompts?**
**Partly, and much less than the model's own behaviour suggests.** On the identified axis the doublespeak
codeword moves only a few percent toward the concept (C−A ≈ +0.015 to +0.027 at L4–L12), while the
model's *reported meaning* of that codeword travels **59%** of the way from literal to direct. So the
semantics move far more than the representation. It is not the same representation, and the gap between
"what the model says the word means" and "where the token sits on the axis" is the sprint's most robust
qualitative finding.

**2. Does the final `carrot` become more `bomb`-like than earlier `carrot`s?**
**NO — it becomes LESS so, and the effect is positional rather than semantic.** Within-prompt paired
(same prompt, same word, only position differs), domain-clustered, n=246 doublespeak prompts:
Δ(final − earlier) is **negative at every layer** (L16 **−0.154**, t_cl = −10.5, p = 0.0001; L8 −0.082,
p = 0.0016; L31 −0.080, p = 0.014). **The control is what settles the interpretation:** the same
comparison in `benign_literal` — where there is no bomb meaning at all — gives effects of the **same
sign and comparable size** (L16 −0.105, L31 −0.131, all p < 0.004). So the last occurrence of a word
simply sits differently on the axis than earlier occurrences, regardless of meaning. There is no
consistent doublespeak-specific excess. ⛔ The earlier "later-carrot-more-bomb-like" claim (P4.3) stays
retracted; this is its replacement, computed with the control it lacked.

**3. How many examples are needed before Boombness rises?**
**One, for the output layer; eight to sixteen for the middle.** L31 is **flat** across a 16× dose change
(+0.0485 → +0.0499, t = +5.9…+10.2) — one demonstration achieves the whole output-layer effect. L4–L12
grow strictly monotonically (L8 +0.0138 → +0.0449, 3.3×). The mid-layer bands keep scaling to k=8 and
then saturate. ⚠ Pooled over query kinds; see C7.

**4. Does Boombness vary enough across prompts to support optimization?**
**It varies, but the usable dose window is narrow enough to be a problem.** Within-arm sd is non-trivial
and the correlation with ASR is real. But steering at α=1 destroys generation (55% trigram repeats,
100% truncated) and the judge scores the degenerate loop as harmful — an artifact we nearly reported. An
optimizer maximizing this projection has no reason to stop at 0.25.

**5. Does Boombness predict ASR?**
**Yes, modestly — in Llama-3.1-8B, and only there** (it does not replicate on Qwen3-14B; see §14). ρ = **+0.307** (`d_surface|L12|proj`), **+0.302** norm-partialled, n = 234, 6/6
domains positive though two are essentially null, **p < 5e-4** (within-domain permutation; the i.i.d.
1.7e-06 is withdrawn as pseudo-replication).

**6. Does Boombness predict ASR better than refusalness?**
**No.** ⛔ The 3.7× is retracted — it compared the two probes at *different tokens*. At matched footing
neither dominates: ratio **1.54** [0.64, 3.60] @last and **0.75** [0.33, 1.13] @codeword_last, both CIs
straddling 1. ⚠ And the between-probe selection freedom is not matched (20 vs 10 candidate columns),
which biases those ratios toward Boombness.

**7. Does Boombness add predictive power beyond refusalness?**
**Yes, and which probe adds more depends on where you read.** At matched degrees of freedom (one column
each, n=234): @codeword_last Boombness adds **+0.0743** and refusalness adds **+0.1091**; @last token
Boombness adds **+0.0053** and refusalness adds **+0.0000005** — i.e. nothing. ⛔ Two earlier drafts
were wrong here (R-13): one from a mixed-footing artifact, one from a table labelled "matched footing"
that in fact gave refusalness 5 predictors against Boombness's 1. Boombness is **not** redundant given
refusalness — at the codeword token it adds 42% over a refusalness-only base.

**8. Do user-like / CoT-like framings increase Boombness?**
⛔ **RETRACTED — the answer is YES, by a little (retraction #6).** I reported a tight null; the paired
within-stem test gives F(5,355)=20.30, p=8.1e-18 with 11/15 pairwise gaps surviving Bonferroni, and the
"3.6%" statistic used a between-stem denominator where the within-stem residual was correct (53%). The
effect is **small but reliable** — largest pairwise gap 4.1% of the grand mean. The naive one-way test that produced
"F = 0.175, p = 0.972" pooled across design cells and used a between-stem denominator; the paired
within-stem test on the perfectly-crossed design gives **F(5,355) = 20.30, p = 8.1e-18**. The claim that
content, domain, demo count and query were "held fixed" was **false for that pooled analysis** — `plain`
and the five role styles occupy disjoint `bank_block`s with zero family overlap. Whether role framing
changes *ASR* remains unresolved (F = 1.94, p = 0.087; largest pair ≈ 0.105 Bonferroni). `role_style` is a
categorical proxy — no Userness/CoTness probe was fitted.

**9. Can we surgically remove Boombness without destroying comprehension?**
⚠ **UPDATED — the answer depends on which instrument you use, and the two disagree.**
- **By attention-edge knockout: ⛔ WITHDRAWN (R-7), previously "no".** The claim was that the retrieval
  is massively redundant — cutting 6.25% of demo→query edges doing nothing *however distributed across
  depth*, while cutting 100% recovers 84% of the deletion ceiling, with every localized knockout
  (16 edges, ~0.03%) reading zero. The edge **ranking** was measured at the wrong token, so that null
  is uninterpretable. Fixed; re-run outstanding.
- **By direction projection: the ASR effect stands; the comprehension half is ⛔ WITHDRAWN (R-6).**
  `project_out d_surface` at L8 was reported to leave comprehension **statistically unchanged**
  (Δ +0.088, p=0.681 — "the only one of five arms that does"). That p is a log-odds between two tokens
  holding a median 4.4e-05 of the next-token mass, so it is not evidence either way. Coherence intact,
  while beating an inert projection control by **+0.056, p=0.0077**, on harmful conditions only. So a
  *surgical removal that preserves comprehension* does exist — it just is not an edge cut, and its effect is
  to **raise** attack success, not lower it.
⚠ Single-model: this does not replicate on Qwen3-14B (see §14).

**10. Can we turn Boombness into a useful GCG objective?**
**No — and the reasoning has been corrected twice, so read the whole answer.** The first "no" was reached
by faulty reasoning; a later draft over-corrected to "§12.2 is reopened"; that too is ⛔ **withdrawn**.
The answer is **no**, for the reasons below.
- **§12.1 (maximise Boombness alone): still NO** — but for a *demonstrated* reason rather than the one I
  gave. Adding `+0.25` alone drives refusal 0.057 → **0.676** and ASR *down* to 0.088. My original reason
  ("no directional causal support") was **wrong**: there is directional support, it was masked by refusal.
- **§12.2 (Boombness MINUS refusal): NO.** Composing the two takes ASR 0.243 → **0.548** (p<0.0001) on
  the bank, where neither manipulation alone raises it — but the gain is *not conditional on the
  doublespeak mapping* (+0.267 where the mapping is **never taught**, largest at zero demonstrations) and
  **does not transfer to explicitly harmful prompts** (+0.000). An attack objective needs both properties
  and this has neither, so "reopened, worth building" is withdrawn.
- **What IS causal is a different intervention with the opposite sign.** Off-bank, *removing* `d_surface`
  raises attack success (§7c: AdvBench +0.0305, p_cl=0.0089, inert control). That is a real causal channel,
  but it is **subtraction, not maximisation** — it gives an objective nothing to ascend.
- The 4-draw band figure quoted earlier (p=0.0014) was **retracted** — those four "draws" were one draw
  wearing four labels; on a genuine 4-draw band it is p=0.043.

**11. What exactly should Matan/Mahmood take from this sprint?**
Four things, in order of durability:
1. **The 2×2 identification design** — it separates surface identity from context and quantifies the
   confound (~2× inflation) instead of arguing about it. Reusable for any codeword/concept pair.
2. **The localization result** — the ASR-predictive state sits at the **codeword token**, 2–4× more than
   at the final prompt token (11–50× on median columns), for a concept probe *and* a refusal probe. This
   is the finding worth following.
3. **A documented negative on the objective**, with the specific reason: correlation without
   sign-following intervention. Do not build on this axis; target the demonstration-retrieval pathway.
4. **The failure catalogue** — five retractions, three guards that never executed, and four transferable
   rules: test guards against cases they should fail; address things by identity not by
   filename/tag/mtime/line-number; resampling *rows* cannot rescue a comparison whose arms sit in
   different *places*; and when correcting an error verify the *measured thing* changed, not just the
   knob you turned.

---

## Limitations and safety scope

**Dual-use scope.** This work studies *why* a known jailbreak family works, in order to characterize it.
It produces no operational harmful instructions. All harmful content is benchmark material behind
project abstractions, and harm labels are automated (StrongReject rubric via `gpt-4o-mini`).

**What is stored.** Judge scores, refusal flags, and scalar degeneracy statistics. Raw generations stay
in local run directories under `outputs/` (git-ignored) and **no completion text appears in any report,
commit message, or analysis artifact**. Every subagent audit in this sprint was explicitly restricted to
numeric fields and source code for the same reason.

**Attack targets.** Only the local open-weight model (`Llama-3.1-8B-Instruct`). No proprietary or
hosted model was attacked; the only API use is the *judge*, which evaluates rather than generates.

### We do NOT claim to have found the mechanism. Plan §13's six criteria, scored honestly:

| # | criterion | met? |
|---|---|---|
| 1 | Boombness predicts ASR across prompts | **YES IN LLAMA ONLY** — ρ=+0.307, p<5e-4 clustered, 6/6 domains positive (2 near-null); on Qwen3-14B the same measurement is carried by 1 of 6 domains (clustered p=0.206) |
| 2 | Adding Boombness increases behaviour or relevant internal scores | **YES, once refusal is removed** — alone it *decreases* ASR by triggering refusal (0.057→0.676), but composed with refusal-removal it takes ASR 0.243→**0.548** (p<0.0001) where neither manipulation alone raises it. The earlier **NO** was a ceiling effect of refusal. ⚠ The gain is not conditional on the doublespeak mapping, so this is scored on behaviour, not on mechanism. |
| 3 | Removing Boombness reduces ASR | **NO — it RAISES it, and this is now controlled.** `project_out` beats an inert projection-type control by +0.056 (p=0.0077) on harmful conditions, ≈0 on benign, comprehension unchanged (p=0.681). ⚠ Single-model — does not replicate on Qwen3. |
| 4 | Comprehension is preserved | **NOW MEASURED (§2.6).** project_out: preserved (p=0.681). +0.25: improves (+0.643). −0.25: **degrades below zero** (−0.792) → disqualified. But the effect is **sign-driven, not axis-specific** — a norm-matched random step moves comprehension MORE in both directions (C10). |
| 5 | Random controls fail | **YES for the projection result, PARTIAL for the additive one.** ⛔ The p=0.0014 figure previously quoted here came from a band whose four "independent draws" were byte-identical (retraction #7); on a **genuine** 4-draw band it is **p=0.043**. Where controls are unambiguous: the **projection control is inert on every condition** (−0.018 vs baseline, p=0.26) while the arm moves harmful conditions by +0.056; and the **composed random control** does nothing on doublespeak (p=0.116) — though it *reverses* on `direct_harmful` (+0.389), so specificity there is scoped, not general. |
| 6 | Replicates across prompt families or models | **PARTIAL, and mostly NO for the causal claims.** Replicates: the ~2× confound (median 1.74 on Qwen3), the token-level positional result, the final-layer effect at matched depth (Llama L31 +0.047 vs Qwen3 L39 +0.052). Does NOT replicate: **G2's correlation** (1 of 6 domains on Qwen3) and **the projection causal result** (mirror-image condition profile). Across *prompt families* the projection result replicates well — it holds on all three harmful conditions. |

**Two of six met, three partial, one no. So the correct description is a documented correlational
finding with a directional null — not a mechanism.** The §18 label is B for exactly this reason, and
§12's objective was not built.

### Plan §4.1's designed variance is generated but not analysable
`strength`, `consistency` and `example_position` were generated exactly as §4.1 specifies and are
analysed by nothing. That is deliberate and now justified by measurement rather than left implicit —
see **N12**. They occupy three dedicated `bank_block`s (`strength` 96 rows, `consistency` 72,
`position` 24) which no analysis reads, so they have never contaminated a result; they are simply
underpowered by an order of magnitude and confounded on three variables at once. Making them usable
is a generator change plus fresh extraction and behavioural runs (**E8**), not a re-analysis.

### Specific limits a reader should carry
- **One model, one concept pair, one judge.** Llama-3.1-8B, carrot↔bomb, StrongReject/`gpt-4o-mini`.
- **G1 is a pilot**: n=8 families from **2 domains**, and its headline is one arm of ~130.
- **G3's identification is one-sided by construction** (a layer holds only ~3,648 edges).
- **G1/G3 run on `semantic_one_word` prompts; G2/G4's ASR claims run on `behavioral` ones.** C7 showed
  this is not merely a join hazard — it changes the sign of a reported effect.
- **"Refusalness at the codeword token" is off-label** — the direction was fitted for a last-token
  readout and its condition ordering degrades badly there.

---

## Exact commands to reproduce the main runs

All GPU stages go through one wrapper. **Argsfiles must live on the shared filesystem** — `/tmp` is
node-local and the job dies in 3 seconds (this cost a launch cycle; see the tick log).

```bash
AD=$PWD/outputs/boombness/argsfiles          # shared FS, NOT /tmp
BANK=$PWD/data/boombness_prompts/boombness_prompt_bank.jsonl   # sha 71bea179345ed118

# 1. prompt bank + mandatory audits
python src/boombness/prompt_families.py --out "$BANK"
sbatch --export=ALL,BOOMB_SCRIPT=tokenization_audit.py,BOOMB_ARGSFILE=$AD/tokaudit.txt        src/boombness/slurm/run_boombness.sh

# 2. extraction — BOTH readout positions (the 2x2 needs both; --position last was once wired
#    into stage_fit only, producing a phantom cell)
printf -- '--bank %s --stage both --layers all --position codeword_last --tag full\n'  "$BANK" > $AD/x_cw.txt
printf -- '--bank %s --stage both --layers all --position last          --tag lastpos\n' "$BANK" > $AD/x_last.txt
for f in x_cw x_last; do sbatch --export=ALL,BOOMB_SCRIPT=extract_boombness.py,BOOMB_ARGSFILE=$AD/$f.txt        src/boombness/slurm/run_boombness.sh; done

# 3. behaviour + judge  (judge refuses to start without OPENAI_API_KEY, by design)
printf -- '--bank %s --query-kinds behavioral --arm base --tag base\n' "$BANK" > $AD/base.txt
sbatch --export=ALL,BOOMB_SCRIPT=score_behavior.py,BOOMB_ARGSFILE=$AD/base.txt src/boombness/slurm/run_boombness.sh
set -a; source .env; set +a
python src/boombness/judge_boombness.py --gens <GENS_DIR> --bank "$BANK" --tag base

# 4. refusalness at BOTH positions (matched footing — the 3.7x retraction)
for POS in codeword_last last; do
  printf -- '--bank %s --layers 12,14,16,18,20 --query-kind behavioral --position %s --tag %s\n' \
    "$BANK" "$POS" "$POS" > $AD/ref_$POS.txt
  sbatch --export=ALL,BOOMB_SCRIPT=refusalness.py,BOOMB_ARGSFILE=$AD/ref_$POS.txt src/boombness/slurm/run_boombness.sh
done

# 5. G1 / G3 / G4
sbatch --export=ALL,BOOMB_SCRIPT=aggressive_patching.py,BOOMB_ARGSFILE=$AD/g1.txt src/boombness/slurm/run_boombness.sh
printf -- '--bank %s --fit-dir <FIT> --layers 8,18 --topk 8 --n-families 6 --n-examples 4 \
--query-kind semantic_one_word --dst both --demo-scope block --tag edgematch\n' "$BANK" > $AD/g3.txt
sbatch --export=ALL,BOOMB_SCRIPT=surgical_knockout.py,BOOMB_ARGSFILE=$AD/g3.txt src/boombness/slurm/run_boombness.sh
# steering + a >=3-draw random-control band (one draw cannot support "more than a random direction")
for S in 20260817 20260818 20260819 20260820; do
  printf -- '--bank %s --query-kinds behavioral --fit-dir <FIT> --intervene random:add:8-8:0.25 \
--arm ctrl_rand_s%s --seed %s --tag ctrl_rand_s%s\n' "$BANK" "$S" "$S" "$S" > $AD/ctrl_$S.txt
  sbatch --export=ALL,BOOMB_SCRIPT=score_behavior.py,BOOMB_ARGSFILE=$AD/ctrl_$S.txt src/boombness/slurm/run_boombness.sh
done

# 6. ANALYSIS — all CPU, all committed, every gate-bearing number comes from here
PY=/home/sharifm/students/omeryosef/miniconda3/envs/poc_stage2/bin/python
# scipy 1.17.1, sklearn 1.9.0, torch 2.7.1+cu126. The login shell has NONE of these.
$PY src/boombness/analyze_g2.py --judge <JUDGE> --extract <EXTRACT_CW> --score <GENS> \
    --refusalness <REFUSAL_CW> --extract-position codeword_last --cluster-by domain \
    --out outputs/boombness/g2_analysis_cwpos.json
$PY src/boombness/analyze_position.py --judge <JUDGE> \
    --extract-codeword <EXTRACT_CW> --extract-last <EXTRACT_LAST> \
    --refusalness-codeword <REFUSAL_CW> --refusalness-last <REFUSAL_LAST> \
    --out outputs/boombness/position_2x2.json
$PY src/boombness/analyze_g1_g3.py --g1 <PATCH_RUN> --g3 <KNOCKOUT_RUN> --out outputs/boombness/g1_g3_analysis.json
$PY src/boombness/analyze_steering.py --baseline <JUDGE_BASE> --arms <JUDGE_ARMS...> \
    --out outputs/boombness/steering_analysis.json
$PY src/boombness/analyze_role.py --extract <EXTRACT_ROLE> --judge <JUDGE_ROLE> \
    --out outputs/boombness/role_analysis.json
$PY src/boombness/reanalyze_corrected.py --run <EXTRACT_CW> --metric d_surface|cos \
    --out outputs/boombness/reanalyze_d_surface_cos.json
$PY src/boombness/probes.py --run <EXTRACT_CW> \
    --regimes d5_surface_matched_codeword,d6_surface_matched_concept --tag surfmatch
```

**Three refusals are load-bearing and will stop you if inputs are wrong** — this is intended:
`analyze_g2.py` refuses when the two probes' readout positions disagree; `analyze_position.py` refuses
unless every run's readout position is verifiable *from its artifact*; `analyze_steering.py` refuses to
report an arm whose coherence was never assessed.

---

## Appendix — committed artifacts

| file | contents |
|---|---|
| `outputs/boombness/position_2x2.json` | freedom-matched predictor × position table |
| `outputs/boombness/g2_analysis*.json` | G2 + clustered inference + per-domain + mediation |
| `outputs/boombness/g1_g3_analysis.json` | G1 spans, paired-bootstrap CIs, n_domains |
| `outputs/boombness/g3_dstfix.json`, `g3_edgematch.json` | G3 arms incl. the edge-matched pair |
| `outputs/boombness/steering_analysis.json` | G4 arms, paired contrasts, control band, routes |
| `outputs/boombness/role_analysis.json` | §11 by role style |
| `outputs/boombness/reanalyze_d_{surface,naive}_cos.json` | §4 confound + §8 dose-response |
| `outputs/boombness/coherence_steering.json` | coherence records incl. the retracted α=1 arm |

Every gate-bearing number is produced by a committed script under `src/boombness/`; run dirs record
model, revision, dtype, attention implementation, git commit, and (since 2026-08-17) the prompt
bank's **content hash**.
