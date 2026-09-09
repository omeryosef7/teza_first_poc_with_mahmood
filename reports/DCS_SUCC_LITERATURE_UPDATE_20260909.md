# DCS — Successor literature update, 2026-09-09

**Status.** Bounded literature sweep. Appended to, and **not** a replacement for,
`reports/DCS_LITERATURE_MATRIX.md`, `reports/DCS_TS_LITERATURE_UPDATE_20260906.md`, and
`reports/DCS_TS_PHASE14_LITERATURE_UPDATE.md`. **No other file was modified.** No GPU or SLURM job
was run; no measurement of ours was made or re-made for this document.

**Verification convention** carried over from the matrix: **✓fetched** = arXiv abstract page (or ACL
Anthology / TACL page) retrieved this session and its abstract read; **†snippet** = located through
a search-result snippet or an arXiv API listing summary only. As in the matrix, a †snippet row's
venue / model / claim fields are **unverified and must not be cited without opening the paper**.
This session performed **abstract-level fetches only** — no full-PDF read. Anything below beyond a
quoted abstract sentence is the fetch tool's extraction, i.e. a secondary summarisation step.

---

## 1. What the prior files already cover, and their cutoff

| file | written | effective search cutoff | rows / scope |
|---|---|---|---|
| `DCS_LITERATURE_MATRIX.md` §1–§4 | 2026-09-02 | **2026-09-02** | 24 rows over 11 topics; 12 ✓fetched, 12 †snippet |
| `DCS_LITERATURE_MATRIX.md` §5 (`A-022` re-check) | 2026-09-05 | 2026-09-05 | 5 additions (`2305.14160`, `2605.04061`, `2605.28854`, `2609.00064`, `2608.03210`) + 2 by-name (`2310.15916`, `2310.15213`) |
| `DCS_LITERATURE_MATRIX.md` §6 (`A-025` re-check) | 2026-09-06 | 2026-09-06 | 5 rows (`2504.00132`, `2609.02438`, `2605.04061` venue, `2607.13075`, `2507.21141`) |
| `DCS_TS_LITERATURE_UPDATE_20260906.md` | 2026-09-06/07 | **2026-09-07** | 4 named targets re-verified by fetch + 6 fresh searches; 2 new works (`2602.11495`, `2604.22128`); §3 novelty table; §4 "what we must not say" (8 items) |
| `DCS_TS_PHASE14_LITERATURE_UPDATE.md` | 2026-09-07 | 2026-09-07 | Method-bounding for PHASE 9 subspace patching: `2311.17030`, `2605.04061`, `2604.22128`, `2609.02438`, `2512.03771`, `2605.05593`, `2608.22916` |

**So the combined coverage cutoff is 2026-09-07**, and this document's job is (a) the 2026-09-01 →
2026-09-09 window, and (b) the standing misses. **The window itself turned out to be nearly empty of
threats — the real yield was (b).** Most of what follows was published between 2026-02 and 2026-08
and was simply never surfaced by the prior files' query sets, which were built around the words
*jailbreak*, *decodable*, *demonstration→query*, and *refusal direction* and therefore missed the
**benign in-context redefinition / lexical-override literature** entirely.

**Standing constraints carried forward unchanged and NOT re-litigated here:**

- *"First to causally intervene on demonstration→query attention in ICL"* is **FALSE**
  (`2504.00132`, `2310.15916`, `2310.15213`). Not re-asserted anywhere below.
- The eight foreclosed sentences in `DCS_TS_LITERATURE_UPDATE_20260906.md` §4 all still stand.
  §3 below **adds to** that list; it retracts nothing from it.
- The `2605.04061` venue string remains **UNRESOLVED**. Nothing found this pass resolves it.

**One correction to an existing row, found incidentally.** The matrix §1.1 row 2 records Ben-Tov,
Geva & Sharif as "arXiv 2506.12880v2 … TACL 2026 … mitigation ≥50 % ASR reduction". The MIT Press
TACL page retrieved this session (`direct.mit.edu/tacl/article/doi/10.1162/TACL.a.695/137193`)
gives the published version, **TACL, June 2026**, and states the mitigation as **2.5×–10× ASR
reduction across models with minimal utility degradation**, and the enhancement as **up to ×5**.
⚠ Cite the TACL DOI and the 2.5×–10× figure, not the v2 preprint's "≥50 %". **✓fetched**

---

## 2. NEW papers

Columns: *id · exact research question · model(s) · intervention · token position · layer · causal
method · readout · harmful/jailbreak setting? · what is actually novel in OUR setting relative to
them.* "—" = not stated in the abstract-level material fetched.

### 2.1 The consequential rows

| id / work | exact research question | model(s) | intervention | token position | layer | causal method | readout | harmful setting? | what is genuinely novel in ours vs. them |
|---|---|---|---|---|---|---|---|---|---|
| **`2606.07555`** — "Priors Persist Through Suppression: A Stroop Paradigm for Lexical Override" (v1 2026-05-25, rev 2026-08-08) **✓fetched** | When an in-context local definition redefines a familiar word ("define *doctor* as *forest*"), does the pretrained lexical prior still interfere, and which token positions carry the redefinition? | 11 models at the behavioural level; **5 models of 1B–2B** for the patching arm | **Activation patching** of neutral-control activations into conflict ("antonym") prompts; plus a **donor-swap** variant using activations from a *different item* | **Three, jointly**: the *defined word*, the *target word inside the definition*, and the *later query word* | — (not stated in abstract) | Patch-in from a matched neutral control; normalised recovery `R` | **target-minus-distractor logit margin**; `R ∈ [0.92, 1.06]` for the joint patch, reduced in every case by the donor swap | **No** | ⚠ **This is the closest published relative of our *mechanism*, and the prior files missed it entirely.** It already establishes: in-context redefinition of a word is a *competition* with the prior rather than a replacement; the redefinition is carried **jointly by codeword + definition-site + query-site**, not by any one of them; and a same-item patch restores the margin while a cross-item donor patch does not. Ours remains distinct on: (i) **harm** — no jailbreak, no refusal, no ASR anywhere in it; (ii) **scale** — 1B–2B for the causal arm vs. our 8B; (iii) **attention** — it patches residual activations, never knocks out attention edges; (iv) it never varies the **concept identity** (bomb/gun/knife) — its manipulation is on the *distractor*, i.e. the codeword side, the same axis Yona et al. already varied; (v) it has no **demonstration block** — the redefinition is a single declarative sentence, not N few-shot demonstrations, so there is no demo→query aggregation question. ⛔ But `R-112` ("the signal is not localised at the codeword; a control nine tokens downstream decodes at 0.9261 vs 0.9446") is **substantially anticipated** by this paper's joint-position result and must be written as a replication in a harmful setting, not a finding. |
| **`2607.24425`** — "Context Is King: How In-Context Specification Shapes the Geometry of Concepts" (2026-07-27) **✓fetched** | Is the geometric structure a model *actually uses* for a concept set by its pretrained prior or by the in-context specification? | **Gemma (to 31B) and Qwen (to 27B) families** | Declarative in-context rule specification imposing a novel geometry on a concept set | Entity token activations (swap) | — | **Activation patching** (entity-activation swap), framed explicitly as establishing *causal use* rather than correlation | Representational similarity to imposed structure **0.6–0.9** vs. near-zero to the prior | **No** | ⚠ **The single largest threat in this sweep.** It publishes the general, benign, positive form of our O2's premise: an in-context specification does not merely *shift* a representation, it **installs a geometry that dominates the pretrained prior, and activation patching shows the model uses it**. Consequences: (a) any sentence of ours of the form *"we show a context-installed concept representation is real / measurable / geometrically substantive"* is now **a citation, not a contribution**; (b) our `toward_B_frac` of **10–17 %** is a conspicuously *weaker* effect than their 0.6–0.9 similarity, and a reviewer will ask why — the honest answer is that Doublespeak installs a *harmful-concept identity under a codeword*, not a *declared relational geometry*, and those need not install equally; (c) their headline scale finding — **"cleaner dominance emerging only in larger models"** — is now the most concrete published candidate explanation for our Llama-8B-vs-Qwen-14B split, and it is a *capability*, not an *architecture*, explanation, which competes with the `2605.08853` (GQA/architecture) story the matrix currently flags. What remains ours: harm; ASR; attention knockout; and, importantly, **the negative** — they show context-imposed geometry *is* used; we show the concept-identity axis is *not concept-specific*. Those are compatible and the contrast is the strongest way to frame O2. |
| **`2608.30585`** — "The Safety Relay in Roleplay Jailbreaks" (2026-08-31) **✓fetched** | Which element of a roleplay wrapper (persona / scenario / task) causally reverses refusal, and does the model still recognise the harm? | **three model families** (names not in fetched abstract) | Hidden-state contrast tracing; geometric decomposition of the effective direction; **activation-direction interventions on held-out requests** | — | — | Controlled counterfactuals: matched harmful/benign requests **with vs. without** the wrapper; per-wrapper-element ablation | **"safety-relay attenuation"** — the harmful-vs-benign distinction is *retained* while refusal-associated expression weakens; 2 benchmarks, 4 authored wrappers | **Yes** | ⛔ **This is our prior-sprint conclusion — "refusal suppression, not concept destruction, is the causal locus" — published for a different attack family, nine days before this document.** It is a *safety-setting* dissociation, which is exactly the qualifier the 09-06 update said still protected us from `2609.02438`/`2604.22128`/`2605.25151`. That protection is now materially weaker: the sentence *"we show the dissociation in a safety/jailbreak setting"* is no longer unique. What survives: their carrier is a **roleplay wrapper** (a framing device), ours is an **in-context semantic remapping of a specific lexical item**, and they intervene on **activation directions**, not on **attention from a demonstration span**; no ASR/StrongREJECT endpoint is reported in the fetched abstract. |
| **`2605.18830`** — "In-Context Learning Operates as Concept Subspace Learning" (2026-05-12) **✓fetched** | Do structured demonstrations induce a *low-dimensional concept subspace* that causally carries the ICL task? | **Llama-3-8B (primary), Qwen2.5-7B (validation)** | **Concept swaps** that redirect predictions toward an injected relation | Residual stream (4096-d) | task-aligned subspace of **68–73 dims** | **Activation patching of the subspace**, with **random** and **cross-task matched-rank** controls | restoring the subspace recovers **78.8 %** of the accuracy gap; **the complementary subspace recovers 0 %** | **No** | ⛔ **Direct precedent for PHASE 9's H2a, on our exact primary model.** Same family (Llama-3-8B + Qwen validation), same primitive (subspace activation patching in the residual stream), and it reports a *strong positive* with a **complementary-subspace control at 0 %** — the control our own design does not currently include. Two consequences: (i) *"we test whether an ICL-installed concept direction is causally used by subspace patching"* is now **method, not novelty**; (ii) their 78.8 %/0 % split sets the bar our `frac_cellmean_spread_removed` of **4.7–19.0 %** will be measured against — an H2a null at our dose, next to their result, reads as *under-dosed*, not as *non-use*. What remains ours: the subspace is an **attacker-installed harmful-concept identity**, not a benign relation; a **safety** endpoint; and the concept-specificity negative. |
| **`2607.08883`** — "Optimizing Against Safety Representations: Activation-Guided Adversarial Suffixes and the Geometry of Refusal" (2026-07-09; **AAAI 2026 Summer Symposium Series**; earlier at ICLR Re-Align workshop) **✓fetched** | Can a GCG-style discrete suffix search be driven by a loss on **internal refusal-direction projections** instead of on output log-likelihood? | not named in fetched abstract; multiple scales | **Activation-Guided GCG** — greedy discrete suffix search with the log-likelihood objective replaced by a loss suppressing projections onto learned refusal directions; plus **Soft-GCG** (Gumbel-Softmax relaxation, ~33× speedup) | suffix tokens; refusal projection read at **all layers and all positions** vs. a single layer-position pair | global (all) vs. single layer-position | discrete optimisation against an activation-space objective, scored behaviourally | **ASR**; also reports that **larger models resist both activation- and suffix-based attacks** | **Yes** | ⛔ **This is the paper §1.8 of the matrix says does not exist in this shape, and it partially pre-empts our headline negative.** Our `BLOCKED` result is "a mechanistically derived activation objective (`d_surface`/Boombness) fails as a GCG/MAC target; both steering signs suppress ASR; ρ = −0.85". `2607.08883` runs the *same class of experiment on the refusal direction*, and its two reported findings both cut at us: (i) **"suppressing refusal globally across all layers and positions is more effective than targeting a single layer–position pair,"** which they read as evidence that safety representations are **distributed, not causally localised** — that is a published, independent explanation for why *our* single-site activation objective failed, and it means our negative may be read as *"they targeted one site"* rather than *"the direction predicts but does not cause"*; (ii) they report the activation-guided objective **working**, which removes "activation-targeted objectives don't work" as an available framing. ⚠ What survives, and it is narrower than the matrix currently claims: ours targets a **semantic-concept** axis (a specific harmful concept installed in context), not the **refusal** axis, and our negative is CI-backed with a **prediction-vs-causation ρ** diagnosis that they do not report. **The §1.8 sentence "negative results of this shape are near-absent from the published record" must be softened.** |
| **`2606.30449`** — "Internal-State Probes Read the Situation, Not the Action: Three Negative Results for Pre-Action Misalignment Monitoring" (2026-06-29) **✓fetched** | Do probes that decode an internal safety-relevant property actually predict or control the *action* the model is about to take? | **Llama-3.1-8B-Instruct**, Qwen2.5-Coder-32B-Instruct, Gemma-3-27B-IT | probe read-out; direction steering | — | — | pre-action tests with **scenario/action generalisation** and explicit **concept-specificity controls** | AUC **1.000** (fine-tune/base direction) and **0.999** (prompt domain) with only marginal behavioural prediction; emotion-concept vectors show **weak steering specificity against unrelated learned directions** | **Yes** (agentic-safety monitoring) | ⚠ Two hits at once. (a) **Threat:** a fourth 2026 "decodable ≠ usable" instance, this one *in a safety setting on our exact primary model*, which further erodes the "ours is the safety instance" qualifier — same erosion as `2608.30585`. (b) **Gift:** it names and operationalises **"concept-specificity controls"** as a standard, which is precisely the control our O2/`PR-035` runs (`bomb` vs `knife`/`gun`/`club`) — so our specificity control has a **citable methodological ancestor** and should be presented as an instance of an established criterion, which is stronger than presenting it as ad hoc. |
| **`2609.08373`** — "Structural Jailbreaks Generalize but Do Not Compound" (**2026-09-08**) **✓fetched** | Do structural jailbreaks — formalised as **Involuntary In-Context Learning (IICL)** — compound with a second pressure (non-English output)? | **two Google Gemini models** | prompt-level only: harmful request reframed as the last missing row of a data-labelling task | n/a | n/a | **none** (black-box) | **StrongREJECT-style rubric**, cross-validated against independent judges, **Cohen's κ = 0.86** | **Yes** | The newest item in the search window and the only one from 2026-09. It **crowds the phenomenon** (a named "in-context structural" jailbreak class with a formal label, IICL) without touching the mechanism: no internals, closed models only. It supplies one thing we should take: a **rubric-reliability number** (κ = 0.86 against independent judges) is now an expected accompaniment to a StrongREJECT-style endpoint in this literature; our ASR endpoint currently reports no inter-judge agreement statistic. |
| **`2602.22424`** — "Causality ≠ Invariance: Function and Concept Vectors in LLMs" (2026-02-25; **ICLR 2026**) **✓fetched** | Are the ICL directions that *causally* drive task behaviour the same as the directions that *invariantly represent* the concept? | multiple LLMs (not named in fetched abstract) | steering with extracted vectors, tested for generalisation across input formats | attention-head outputs | "similar layers to FV-related heads" | causality-driven extraction (FV) vs. RSA-based selection (CV); cross-format steering | task performance under steering | **No** | ⛔ **Directly names the distinction our `v_bomb_specific` work rests on, at a top venue, seven months ago, and the prior files missed it.** It establishes that in ICL the *causal* direction (function vector) and the *representationally invariant concept* direction (concept vector) are **different objects that coexist in the same heads**. That is the cleanest available prior explanation for our own adversarial-review finding that `v_bomb_specific` carries a −0.55…−0.68 loading on a generic demonstration-presence axis and only 0.22–0.44 cosine with `v_bomb`. ⇒ We should **stop treating that decomposition as an internal artefact of our pipeline** and start citing this as the predicted structure. It also foreclosesnovelty for any framing of the form "we separate the concept axis from the task axis". |
| **`2605.08295`** — "In-Context Fixation: When Demonstrated Labels Override Semantics in Few-Shot Classification" (2026-05-08) **✓fetched** | When demonstration labels are homogeneous, does the model bind outputs to the *demonstrated token inventory* rather than to semantic content? | Pythia, **Llama**, Qwen, 0.8B–8B; Llama-3.2-1B for the circuit | **per-item paired activation patching** | **label-slot positions in demonstrations** | **layer-7-centred circuit** (rank 2/560); top-5 layers by logit lens | paired activation patching with logit-lens confirmation | probability over output tokens; accuracy; **98.4 % recovery of the performance gap** | **No** | The paper closest to our *demonstration-side* localisation. Its finding — the demonstration block installs a **token-inventory binding, not a semantic content transfer** — is a benign-setting statement of exactly the mechanism our O2 negative implies (the demonstrations install "there is a remapping here", not "the remapped thing is a bomb"). ⚠ Its **layer-7-centred** circuit sits inside our L6–14 band, which is corroboration for the band's location and simultaneously removes "we localised the demonstration effect to an early-mid band" as a novel claim. Ours remains distinct on harm, on attention knockout vs. patching, and on varying the *concept*. |
| **`2603.18353`** — "Interpretability without actionability: mechanistic methods cannot [bridge the knowledge–action gap]" (2026-03-18) **✓fetched** | Can mechanistic methods convert what a model internally knows into corrected behaviour? | Steering-8B; **Qwen 2.5 7B Instruct** | linear probes; concept-bottleneck steering; SAE steering; truthfulness-separator steering | — | — | four steering methods compared head-to-head against a behavioural endpoint | probe **AUROC 0.982** vs. **45.1 %** output sensitivity; CB steering corrects 20 % of errors while **disrupting 53 %** of correct detections; **SAE steering: zero effect** despite 3,695 significant features | **No** (clinical triage; safety-adjacent) | A fifth independent "decodable ≠ actionable" instance, and the one with the most damaging quantitative shape for a steering-based contribution: it reports a steering method that *works* while **breaking more than it fixes**. ⚠ Directly relevant to any PHASE 9 positive — the correct comparison is not "did the edit move the endpoint" but "did it move the endpoint **more than it disrupted the matched control condition**". Ours is novel only in the attacker-installed-concept + jailbreak setting. |
| **`2608.15772`** — "Broken Symmetry in LLM Refusal: Answer Release Is More Local Than Refusal Restoration" (2026-08-16) **✓fetched** | When a model refuses, is the answer *erased* internally or merely *suppressed* at the output? | not named in fetched abstract | **bidirectional activation patching** with answering/refusal outputs perfectly matched | single-position vs. multi-position | — | bidirectional patching (release direction and re-suppress direction) | **asymmetry**: releasing a withheld answer needs only **single-position** patches; reimposing suppression needs **broad multi-position** intervention. Explicitly: *"probe recoverability can overestimate true behavioural control."* | **Yes** (refusal) | ⚠ **A methodological warning aimed squarely at our knockout's interpretation.** It shows the two directions of a refusal intervention have *different locality*, so a result obtained in one direction does not transfer to the other. Our knockout runs in one direction only (remove the demonstration pathway → observe refusal/ASR); the reverse (restore it into a refusing run) is untested. It also supplies the single most quotable caution against reading our probe result as control. Nothing of ours is scooped; the design gap it exposes is real. |
| **`2606.27510`** — "The Curse of Multiple Mediators: Hidden Interaction Effects in Activation Patching" (2026-06-25) **✓fetched** | Does the natural-indirect-effect estimand that activation patching computes actually isolate one component's causal contribution? | GPT-2 (IOI circuit) | — (methodological) | — | — | decomposition of NIE into a component effect plus an **interaction term (INT)** | argues INT should be **reported as a diagnostic**, its magnitude and sign indicating when causal conclusions are prompt-dependent and when greedy component ranking will miss mechanisms | **No** | ⛔ **Method paper we should adopt; no threat.** Our knockout is applied to a *band of layers × a set of columns simultaneously* — i.e. the exact multi-mediator regime where NIE conflates the component effect with interactions. See §4.1. |
| **`2608.04183`** — "Test, then Route: How Language Models Execute In-Context Conditional Rules Across Models and Languages" (2026-08-04) **✓fetched** | Does an in-context conditional rule decompose into a predicate-testing module and an answer-routing module? | **three open models, two families, six languages** | activation patching in a **four-donor design** (two donors carry swapped rules so condition and answer word disagree) | mid-stack residual band | mid-stack band | four-donor patching with a stated **isolation criterion** | rerouting with **predicate-outcome correlation ≈ 1.0** and **mapping-change ≈ 0.0**; criterion satisfied in **17/18** cases; routing subspaces show **≈0 cross-pair transfer** | **No** | ⛔ **The single best method import in this sweep** (see §4.2). The four-donor construction is precisely the control that distinguishes "the patch moved the thing I meant" from "the patch moved the output", and the ≈1.0/≈0.0 pair is a **published, quotable causal-use criterion** — something the project has been improvising. |
| **`2609.00498`** — "Validity-Aware Jailbreak Evaluation for Large Language Models" (2026-08-31; **to appear EMNLP 2026 main**) **✓fetched** | Do standard jailbreak rubrics count plausible-but-wrong outputs as successes? | multiple benchmarks | evaluation framework (**SEAV**: LLM-judge + retrieval-grounded verification) | n/a | n/a | none (measurement) | **reclassifies 22.1 %–51.0 % of previously "successful" jailbreaks as invalid** | **Yes** | ⛔ **Threatens our endpoint, not our mechanism, and it is the more dangerous kind of threat.** Our O1 rests on a StrongREJECT rubric endpoint on which Llama is already *direction-only and not significant at the domain independence unit* (`R-019`). If up to half of rubric-positive completions are procedurally invalid, then a large share of the endpoint's variance is noise with respect to actual harm — which both explains a weak signal and makes an unqualified ASR claim harder to defend at EMNLP-adjacent venues after this paper appears. |
| **`2605.09070`** — "Single-Configuration Attack Success Rate Is Not Enough: Jailbreak Evaluations Should Report Distributional Attack Success" (2026-05-09) **✓fetched** | Does an ASR reported at one parameter configuration characterise an attack? | — | evaluation methodology | n/a | n/a | none | proposes **Variant Sensitivity Measure (VSM)** = deviation of best-reported ASR from mean ASR over the variant space, and **Union Coverage (UC)**; names **teaching-shot count, system-prompt template, conversation rounds, cipher dispersion** as the variance sources | **Yes** | Method import (§4.3). Its named nuisance axes map one-to-one onto our own prompt-bank factors (demonstration count, basket-vs-button carrier, template). ⇒ Our matched-control design is well positioned to report VSM/UC essentially for free, and doing so **converts a weak single-configuration ASR into a defensible distributional statement** — the most direct available repair for `R-019`. |
| **`2408.15510`** — "How Reliable are Causal Probing Interventions?" (v3; also OpenReview `Ku1tUKnAnC` / `tmpMQLxVHh`) **†snippet** | How reliable are probe-derived causal interventions as evidence? | — | — | — | — | formal + empirical evaluation of causal-probing methods | an inherent **completeness vs. selectivity trade-off**; *no* leading method satisfies both; **nullifying interventions are far less complete than counterfactual interventions** | **No** | ⛔ **A standing miss across all three prior files, and it is the field's canonical statement of the criterion our whole PHASE 9 argument needs.** Its "nullifying interventions are far less complete than counterfactual ones" is a published, general reason why our projection-out design under-doses — currently argued in-repo only from our own `frac_cellmean_spread_removed`. See §4.4. |

### 2.2 Secondary rows — relevant, catalogued, no threat

| id | work | date | verification | one-line bearing |
|---|---|---|---|---|
| `2605.29971` | Causal Interventions on Continuous Variables: Verb Bias in Steering Vectors for ICL | 2026-05 | †snippet | Continuous-variable causal-intervention machinery for ICL steering vectors; a candidate estimator if we ever regress a graded readout on a graded edit. |
| `2605.24856` | The Concept Allocation Zone: Tracking How Concepts Form Across Transformer Depth | 2026-05 | ✓fetched | *"the probe direction rotates substantially during assembly and does not settle until after the Concept Allocation Zone in which it forms."* ⚠ A published reason why a probe taken at a peak-separation layer inside L6–14 may be the wrong layer. |
| `2512.17325` | Task Schema and Binding: A Double Dissociation Study of ICL | 2025-12 | †snippet | ICL separates into task-schema recognition and input–output binding — the benign structural analogue of "remapping-presence vs. concept-identity". |
| `2406.16007` | Label Words as Local Task Vectors in ICL | 2024 | †snippet | Missing citation beside `2305.14160`; the label-word position carries a *local* task vector. |
| `2602.02132` | There Is More to Refusal in LLMs than a Single Direction | 2026-02 | †snippet | Eleven refusal/non-compliance categories occupy geometrically distinct directions. Strengthens the `2502.17420` caution the matrix already carries. |
| `2604.08524` | What Drives Representation Steering? A Mechanistic Case Study on Steering Refusal | 2026-04 | †snippet | Mechanism of *why* refusal steering works; missing from §1.6. |
| `2606.13709` | LoMC: Localized Multidirectional Correction for Refusal Suppression | 2026-06 | †snippet | Multi-direction refusal suppression; §1.6 family. |
| `2603.18280` | Detection Is Cheap, Routing Is Learned: Why Refusal-Based Alignment Evaluation Fails | 2026-03, rev 2026-05 | ✓fetched | *"Both miss the layer where alignment often operates: routing from concept detection to behavioral policy."* Nine open-weight models. The cleanest available framing for our own detect-vs-act split. |
| `2603.08234` | The Struggle Between Continuation and Refusal: Mechanistic Analysis of Continuation-Triggered Jailbreak | 2026-03 | †snippet | Head-zeroing on causal paths enabling jailbreaks; §1.3 family. |
| `2608.27504` | Circuit Discovery Helps Detect LLM Jailbreaking | 2026-08-27 | †snippet | Circuit-level jailbreak detection; §1.3 family, post-matrix. |
| `2604.23130` | From Concept-Aligned Tokens to Vulnerable Features: Mechanistic Localization of Jailbreaks | 2026-04 | †snippet | Token→feature localisation of jailbreaks; §1.3 family. |
| `2604.10326` | Jailbreaking the Matrix: Nullspace Steering for Controlled Model Subversion | 2026-04 | †snippet | Nullspace steering; relevant to §1.8's activation-objective family. |
| `2608.17360` | Fair ASR: Re-Evaluating Black-Box Jailbreaks under Shared Target-Call Budgets | 2026-08 | †snippet | Budget-matched ASR comparison; endpoint-methodology family with `2605.09070`. |
| `2608.02486` | Cultural Awareness is Represented but Not Decoded (18 LLMs) | 2026-08-03 | †snippet | Sixth "represented ≠ decoded" instance. |
| `2606.21678` | Decodable but Not Faithful: Coupling NL Rationales to Programmatic Verifiers | 2026-08-08 | †snippet | Seventh instance. |
| `2510.09794` | Causality ≠ Decodability, and Vice Versa: Lessons from Interpreting Counting ViTs | 2025-10 | †snippet | ⚠ Pre-dates every "2026 consensus" paper the prior files cite, and states the claim *bidirectionally* (things can also be causal without being decodable). Should be cited as the earliest clean statement. |
| `2605.28639` | The Attentional White Bear Effect in Transformer LMs | 2026-05 | †snippet | Suppression instructions increase attention to the suppressed item — a possible confound for any "attention to the demonstration span" reading. |
| `2606.15733` | Vernier: Probing Representational Misalignment Behind Lexical Gaps in Causal Reasoning | 2026-06 | †snippet | Patching to test whether a decision representation *transfers between prompts* — a transfer control we lack. |
| `2607.15893` | Induction in Both Directions: Mechanistic Analysis of ICL in Masked Diffusion LMs | 2026-07 | †snippet | Induction-circuit provenance, other architecture. |
| `2606.19349` | Where to Place the Query? Positional Bias in ICL for Diffusion LLMs | 2026-04/06 | †snippet | Query-position sensitivity in ICL — adjacent to our query-row axis, wrong architecture. |
| `2505.13737` | Causal Head Gating: Interpreting Roles of Attention Heads | 2025-05 | †snippet | A learned-gate alternative to hard knockout; possible robustness check. |

---

## 3. Papers that pre-empt or narrow our novelty claim, ranked by threat

**T1 — `2607.24425` "Context Is King".** *Pre-empts:* that an in-context specification installs a
concept geometry the model **causally uses**, established by activation patching, on two model
families up to 31B. ⇒ Any claim of ours that the Doublespeak-installed representation is real,
substantive, or causally live is now a citation. ⇒ It also supplies a **competing explanation for
our Llama/Qwen split** (capability/scale, not architecture) that we have not tested. *Survives:*
harm, ASR, attention knockout, and the concept-specificity negative — which is the *contrast* to
their positive and should be framed that way.

**T2 — `2606.07555` "Priors Persist Through Suppression".** *Pre-empts:* the position structure of
in-context lexical override. Its joint patch over {defined word, definition-site target, query-site
word} recovering `R ≈ 1.0`, with a cross-item donor patch failing, is the benign-setting form of
`R-112` (signal not localised at the codeword). ⇒ `R-112` must be written as replication-in-a-harmful-setting.
*Survives:* 8B scale, attention intervention, demonstration-block aggregation, harm, concept-side
variation.

**T3 — `2607.08883` "Optimizing Against Safety Representations".** *Pre-empts:* the framing in matrix
§1.8 that a CI-backed negative for a mechanistically derived, activation-targeted adversarial
objective is near-absent from the record. It runs the same experiment class on the refusal axis,
reports it **working**, and independently reports that **single layer–position targeting
under-performs global targeting** — a ready-made alternative explanation for our `BLOCKED` result
that is not "the direction predicts but does not cause". ⛔ **The §1.8 sentence must be softened, and
our negative must be reported with an explicit statement of the site/scope we optimised at**, or a
reviewer will attribute it to under-targeting.

**T4 — `2605.18830` "ICL Operates as Concept Subspace Learning".** *Pre-empts:* PHASE 9's H2a design
on our own primary model (Llama-3-8B, Qwen2.5-7B validation), with a stronger control set
(complementary-subspace = 0 %) and a much larger realised effect (78.8 %). ⇒ Subspace patching of an
ICL-installed concept direction is **method, not novelty**, and our 4.7–19.0 % dose now has a
published comparison point that makes an under-dosed null harder to publish.

**T5 — `2608.30585` "The Safety Relay in Roleplay Jailbreaks"** *(with `2606.30449` reinforcing).*
*Pre-empts:* the last remaining qualifier on the dissociation framing. The 09-06 update's escape
route was "ours is the dissociation **in a safety/jailbreak setting**". `2608.30585` publishes
harm-recognition-retained-while-refusal-attenuates for roleplay jailbreaks (three model families),
and `2606.30449` publishes near-perfect decodability with marginal behavioural prediction in an
agentic-safety setting **on Llama-3.1-8B-Instruct**. ⇒ ⛔ Add to the "must not say" list:
*"ours is the first demonstration of the decodability/causal-use dissociation in a safety setting."*
What is left is narrower still: an **attacker-installed, in-context-constructed concept identity**
under a **demonstration-span attention** intervention.

**T6 — `2602.22424` "Causality ≠ Invariance" (ICLR 2026).** *Pre-empts:* the conceptual separation
between the causal ICL direction and the invariant concept direction. ⇒ Our adversarial-review
finding that `v_bomb_specific` is largely a generic demonstration-presence axis is the **predicted**
structure, not a surprise; cite it as such rather than as a pipeline artefact.

**T7 — `2609.00498` (SEAV, EMNLP 2026 main).** *Pre-empts nothing mechanistic; attacks the endpoint.*
22.1–51.0 % of rubric-positive jailbreaks reclassified invalid. ⇒ Our O1 behavioural endpoint needs
a validity qualifier, and `R-019`'s non-significance now has an external, citable candidate cause.

**T8 — `2605.08295` "In-Context Fixation".** *Pre-empts:* "we localised the demonstration effect to
an early-mid band" (their circuit is layer-7-centred, inside L6–14) and "demonstrations bind
inventory rather than transfer semantics" — the benign version of our O2 implication.

**T9 — `2603.18353`, `2608.15772`, `2608.02486`, `2606.21678`, `2510.09794`.** No individual threat;
collectively they raise the count of independent "represented ≠ used" instances from the five the
09-06 update logged to **at least eleven**, across logic validity, bracket structure, realisation
status, safety-head persistence, clinical triage, refusal suppression, cultural knowledge, NL
rationales, agentic monitoring, roleplay jailbreaks, and vision counting. ⛔ Restating the general
phenomenon in any form is now actively costly.

### 3.1 ⛔ Additions to `DCS_TS_LITERATURE_UPDATE_20260906.md` §4 ("what we must not say")

9. *"Ours is the first / one of the first demonstrations of the decodability-vs-causal-use
   dissociation in a safety or jailbreak setting."* — foreclosed by `2608.30585` and `2606.30449`.
10. *"We show that an in-context specification installs a concept representation the model actually
    uses."* — foreclosed by `2607.24425`.
11. *"We are the first to test whether an ICL-installed concept subspace is causally used by
    patching it."* — foreclosed by `2605.18830` (same model family, stronger controls).
12. *"Negative results for mechanistically derived, activation-targeted adversarial objectives are
    absent from the published record."* — foreclosed by `2607.08883`; matrix §1.8 must be amended.
13. *"The remapping signal being distributed across positions rather than localised at the codeword
    is a new observation."* — foreclosed by `2606.07555` (benign) and `2605.04061` (ICL).
14. *"The concept axis and the task/demonstration-presence axis being distinct is an unexpected
    property of our directions."* — foreclosed by `2602.22424` (ICLR 2026); it is the predicted
    structure.

---

## 4. Methods worth adopting, with the exact slot in our pipeline

### 4.1 `2606.27510` — report the **interaction term (INT)**, not just the NIE
*The problem it names:* activation patching's NIE estimand conflates a component's own causal
contribution with its **interaction** with the state of other components; the authors argue INT's
**magnitude and sign** should be reported as a diagnostic of when a causal conclusion is
prompt-dependent.
*Where it slots in:* our attention knockout is applied to **a band of layers × a set of columns
simultaneously** — the canonical multi-mediator regime. Concretely: alongside the existing
band-level knockout effect, report the **single-layer knockout effects summed** vs. the **band
knockout effect**; their difference *is* INT. A large positive INT means the L6–14 band result is a
band property and cannot be attributed to any layer; a near-zero INT licenses the additive reading
we have been implicitly using. This is a **CPU-cheap re-analysis of runs we already have**, not new
compute.

### 4.2 `2608.04183` — the **four-donor design** and the ≈1.0 / ≈0.0 **isolation criterion**
*The method:* four donors, two of which carry swapped rules so that the condition and the answer
word **disagree**, letting the analyst read off whether a patch moved the intended variable or
merely moved the output. Success is declared only when **predicate-outcome correlation ≈ 1.0** *and*
**mapping change ≈ 0.0** — both, jointly.
*Where it slots in:* PHASE 9's hidden-state transplant (H1/H2a). Today the transplant has a donor and
a receiver; the four-donor construction adds the two **disagreeing** donors that separate "the
transplant installed BOMB" from "the transplant broke the prompt". ⇒ Adopt the paired criterion as
our **preregistered causal-use bar**: an effect counts only if the concept-readout moves *and* the
generic remapping/competence readout does not. This directly answers the PHASE 14 §5 problem that
our interpretation warning is asymmetric — a two-sided criterion fires against a positive and a null
equally.

### 4.3 `2605.09070` — **VSM + Union Coverage** as the ASR reporting format
*The method:* report the **Variant Sensitivity Measure** (deviation of the best configuration's ASR
from the mean over the variant space) and **Union Coverage** (fraction of prompts jailbroken by *any*
tested configuration) alongside the headline ASR.
*Where it slots in:* the O1 behavioural endpoint and `R-019`. Our prompt banks already vary the
carrier (`button` / `basket`), the concept (`bomb`/`gun`/`knife`), and the demonstration count —
i.e. we already **have** the variant space this paper says must be reported. Computing VSM and UC is
a re-aggregation of existing StrongREJECT scores. ⇒ This is the cheapest available upgrade from
"Llama ASR contrast is direction-only and not significant" to a defensible **distributional**
statement, and it pre-empts the reviewer objection that our ASR is a single-configuration number.

### 4.4 `2408.15510` — the **completeness vs. selectivity** trade-off as the frame for our dose
*The finding:* no leading causal-probing intervention satisfies both completeness and selectivity,
and **nullifying interventions are systematically far less complete than counterfactual ones**.
*Where it slots in:* the PHASE 9 interpretation, replacing an in-repo-only argument with a citable
one. Our design projects a direction *out* (a nullifying intervention) and achieves
`frac_cellmean_spread_removed` = **4.7–19.0 %** — i.e. low completeness by construction, exactly as
this paper predicts for the nullifying class. ⇒ Two concrete moves: (a) attach this citation to
every reported null, beside the dose, as the PHASE 14 §6.1 rule already requires; (b) **prefer the
counterfactual form** — patch in the donor concept's activation rather than project the direction
out — wherever we can afford it, since the same paper says that is the more complete instrument.

### 4.5 `2606.30449` — **"concept-specificity control"** as the name for what O2 already does
*The method:* an explicit specificity control checking whether a decoded/steered direction is
specific to the named concept or generic, plus scenario/action generalisation tests.
*Where it slots in:* `PR-035` / O2 (`bomb` vs `knife`/`gun`/`club`). No design change — a **framing
and citation** change. Presenting our specificity control as an instance of an established criterion
(`2606.30449`, `2609.02438`'s random-direction comparison) is strictly stronger than presenting it as
a bespoke control, and it is the correct answer to a reviewer who asks why `knife`/`gun`/`club` are
the right foils. ⚠ A related **unattributed** lead: a search snippet described a
"direction-specificity control" over **111 concept-model pairs** with 10 random unit vectors per
pair, mean concept-direction reduction **45.6 %** vs. random **0.24 %**, median specificity ratio
**377×**. That is a ready-made **nuisance floor** for exactly our measurement, but the snippet could
**not be attributed to a paper** this session — the two candidates checked (`2605.25848`,
`2603.18280`) do not contain it in their abstracts. ⛔ Do not cite the numbers; the lead is recorded
in §5 for a later session to chase.

### 4.6 `2609.08373` — report an **inter-judge agreement statistic** for the rubric
It reports **Cohen's κ = 0.86** between its StrongREJECT-style rubric and independent judges. Our
endpoint reports no agreement statistic. ⇒ Add κ (or equivalent) against a second judge on a
stratified subsample of existing completions. Cheap, and it is becoming an expected line.

### 4.7 `2609.00498` (SEAV) — a **validity screen** on the endpoint
Retrieval-grounded validity checking reclassifies 22.1–51.0 % of rubric-positive jailbreaks as
invalid. ⇒ Even a lightweight version — a second-pass check that a rubric-positive completion is
procedurally coherent — applied to the existing O1 completions would tell us whether `R-019`'s
non-significance is a mechanism fact or an endpoint-noise fact. This is the highest-information
cheap experiment identified in this sweep.

### 4.8 `2605.18830` — the **complementary-subspace** control
Restoring the identified subspace recovers 78.8 % of the gap; restoring its **complement** recovers
**0 %**. ⇒ Add the complement arm to PHASE 9's control set (currently C1 norm-matched random, C4
orthogonal equal-magnitude). The complement arm is the one that distinguishes "this subspace" from
"this much of the residual stream", and it is stronger than a random-direction control because it is
**matched in rank and in the data**.

### 4.9 `2608.15772` — run the intervention **bidirectionally**
Release and re-suppression have different locality. ⇒ Where feasible, complement the knockout
(remove the demonstration pathway from a jailbroken run) with its inverse (patch the demonstration
pathway into a refusing run). A one-directional result is now known to be a weaker claim than it
looks.

---

## 5. Searches run, and what returned nothing

**Tools:** `WebSearch` (US region) and `WebFetch` against arXiv abstract pages, the arXiv export API,
and MIT Press TACL. **No OpenReview search, no Semantic Scholar API query, no full-PDF read.**

### 5.1 WebSearch queries (12)

| # | query | outcome |
|---|---|---|
| 1 | cipher substitution jailbreak LLM mechanistic interpretability September 2026 | `2608.27504`, `2603.08234` new; rest already catalogued |
| 2 | in-context semantic remapping word meaning override language model interpretability 2026 | ⭐ **`2606.07555`** — the highest-yield query of the pass |
| 3 | arXiv 2609 in-context learning task vector causal intervention | `2605.29971`, `2502.05390`, `2412.12276`; no 2609 hits |
| 4 | activation patching control interpretability illusion hidden state transplant methodology 2026 | `2510.09794` new; `2311.17030` already in PHASE 14 |
| 5 | demonstration attention aggregation label words in-context learning 2026 attention knockout | `2605.08295`, `2406.16007` new |
| 6 | refusal direction single direction safety mediation 2026 critique multiple directions | `2602.02132`, `2604.08524`, `2606.13709` new |
| 7 | adversarial suffix optimization objective on internal activations representation space GCG 2026 | ⭐ **`2607.08883`** |
| 8 | arxiv September 2026 jailbreak activation patching probe causal use safety representation | nothing new; all already catalogued |
| 9 | "encoded" OR "codeword" jailbreak internal representation harmful concept probe 2026 Llama | ⛔ **NOTHING NEW.** Returns the same JailbreakLens / NeuroBreak / trace-detection family. Fourth independent confirmation that the *codeword-substitution mechanism* literature is Doublespeak plus descendants |
| 10 | causal use criterion probing critique "probing accuracy does not imply" causal relevance 2026 | ⭐ **`2408.15510`** + its OpenReview records |
| 11 | universal jailbreak suffix attention hijacking follow-up 2026 dominance score contextualization | ⛔ **No follow-up work found.** Only the TACL publication itself — which corrected our venue/number metadata (§1) |
| 12 | StrongREJECT rubric jailbreak evaluation mechanistic intervention 2026 attention ablation ASR | ⭐ `2609.00498`, `2605.09070`, `2608.17360` |
| 13 | ACL 2026 / EMNLP 2026 in-context learning attention demonstration query causal intervention semantic override | ⛔ **NOTHING ON TARGET.** Returned generic ICL demonstration-selection work. Anthology full-text search was **not** used and would be the right instrument |
| 14 | arxiv 2609 mechanistic interpretability refusal concept representation September 2026 | `2603.18280`, `2604.23130`, `2603.18353` new — all pre-September |
| 15 | "Doublespeak" OR "representation hijacking" jailbreak follow-up replication 2026 concept specificity | ⛔ **NO FOLLOW-UP OR REPLICATION EXISTS** on the indexed web. Only the paper's own venues (arXiv / OpenReview `tWfEMpDapM` / ACL Anthology `2026.acl-long.768` / mentaleap.ai). ⚠ Recorded as a **null search, not as evidence of novelty** |
| 16 | concept specificity control probe harmful concept "not concept-specific" residual stream 2026 | ⭐ `2606.30449`, `2605.18830`, `2605.24856`, `2605.28639`; ⚠ also produced the **unattributed 111-pair / 377× specificity-ratio snippet** (§4.5) |
| 17 | arxiv 2609 in-context learning mechanism attention demonstration September 2026 interpretability | ⛔ **NOTHING NEW.** `2609.00064` and `2609.02737` only; the September ICL-interpretability window is essentially empty |

### 5.2 arXiv export-API listings (5)

| query | window returned | outcome |
|---|---|---|
| `abs:"in-context" AND abs:"jailbreak"`, 40 newest | 2026-06-08 → **2026-09-08** | ⭐ `2609.08373`, `2608.30585`. Everything else is attack/defense engineering with no internals |
| `abs:"activation patching"`, 40 newest | 2026-06-14 → **2026-09-06** | ⭐ `2607.24425`, `2606.27510`, `2608.04183`, `2608.15772`, `2608.02486`, `2606.21678`, `2606.15733`. ⚠ The **three September entries** (`2609.06715`, `2609.03511`, `2609.03322`) are all **off-target** — AI-consciousness, multilingual reordering, perturbation robustness |
| `abs:"attention knockout" OR abs:"attention hijack"`, 40 newest | 2022 → **2026-08-27** | ⛔ **NOTHING RELEVANT.** 2026 attention-knockout work is now **almost entirely vision-language / VLA / audio**. No new LLM-ICL or LLM-jailbreak knockout competitor exists. This is a **positive null for our method's uniqueness** in the text-safety setting |
| `abs:"in-context learning" AND (abs:"causal" AND abs:"attention")`, 30 newest | 2024 → **2026-09-03** | ⭐ `2602.22424`, `2512.17325`, `2505.13737`, `2607.15893`, `2606.19349`. September entries are tabular-foundation-model reports, off-target |
| `abs:"decodable" AND abs:"causal"`, 40 newest | — | ⛔ **FAILED — HTTP 429 (rate-limited).** Not retried. **A later session should re-run this one**; it is the highest-yield unexecuted query in this pass |

### 5.3 Direct fetches performed (16)

`2606.07555`, `2607.08883`, `2605.08295`, `2607.24425`, `2608.30585`, `2606.27510`, `2609.08373`,
`2605.09070`, `2609.00498`, `2603.18353`, `2602.22424`, `2605.18830`, `2603.18280`, `2608.04183`,
`2606.30449`, `2605.25848`, `2608.15772` — all **abstract page only**.

### 5.4 ⚠ Gaps that remain OPEN after this pass — do not treat as searched

1. **OpenReview.** Still not queried, third consecutive pass. The matrix §5.3 and the 09-06 update
   §5 both flagged it as the largest uncovered risk. **Unchanged.** A competing mechanistic
   Doublespeak paper under review remains invisible.
2. **Semantic Scholar / ACL Anthology full-text search.** Neither was used. Query 13's null is
   therefore **uninformative** about the ACL/EMNLP 2026 proceedings.
3. **`abs:"decodable" AND abs:"causal"` arXiv API listing** — rate-limited, never executed (§5.2).
4. **The 111-pair / 377× direction-specificity-control source** could not be attributed (§4.5).
   `2605.25848` and `2603.18280` were both checked and neither contains it in its abstract. Next
   candidate to check: the full text of `2606.30449`, or a targeted search on the exact phrase
   "median specificity ratio".
5. **`2607.13075` and `2507.21141`** — flagged as missing citations for the specificity half by
   `A-025` F-5 and still unopened after the 09-06 update. **Still unopened.**
6. **No full-PDF read anywhere in this pass.** Every ✓fetched row rests on an abstract page plus the
   fetch tool's extraction. The rows most likely to change on a full read are `2607.24425` (layer and
   position detail absent from the abstract), `2608.30585` (model names and whether ASR is measured
   at all), and `2607.08883` (which models, and whether any negative result matching ours is
   reported in the body).
7. **Model-family coverage.** No search was run specifically for Qwen3-14B-family mechanistic
   results that would bear on our capable null.
