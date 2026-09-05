# DCS — Literature matrix

**Scope.** Related work for the Doublespeak concept-specific-Boombness / surgical-demonstration-causality
phase. Built as a *positioning* document: for every work it records what was measured, what was
intervened on, and whether the paper closes the loop from representation to behavior — because that
loop is the axis on which this phase's contribution stands or falls.

---

## Provenance

| field | value |
|---|---|
| git sha | `1fb45c06568f330ba4fc20d70451b91f4b281238` |
| branch | `behavioral-causality-sprint` |
| head commit time | 2026-09-02T19:50:13+03:00 |
| document written | 2026-09-02T16:59:03Z |
| produced by | manual literature search (no script, no argv); `WebSearch` + `WebFetch`, plus `pdftotext` on the two in-repo PDFs |
| search protocol | 12 queries, run 2026-09-02, over the 11 topics named in the phase brief: in-context semantic remapping; codeword/substitution-cipher jailbreaks; mech-interp of prompt injection; activation patching for jailbreaks; causal tracing of in-context demonstrations; induction/retrieval heads in few-shot learning; attention knockout in ICL; representation-vs-behavior dissociation; mechanistically derived adversarial objectives; refusal directions/refusal suppression; cross-model replication of interpretability findings |
| in-repo reference 1 | `doublespeak/INCONTEXT_REPRESENTATION_HIJACKING.pdf`, sha256 `cd3f6945854c82d0…`, 20 pp. |
| in-repo reference 2 | `interp-jailbreak/2506.12880v2_universal_jailbreak_suffixes_are_strong_attention_hijackers.pdf`, sha256 `ca188dc4c0f9b104…` |
| rows in matrix | 24 |
| code touched | none (this phase task is documentation-only, per the brief) |

**Verification level.** Rows marked **✓fetched** were checked against the paper's own abstract page
or PDF. Rows marked **†snippet** were located through search-result snippets only and their venue /
model / claim fields carry correspondingly lower confidence. This distinction is load-bearing: do not
cite a †snippet row in a paper draft without opening it first.

**Exclusion / attrition record.** See §4.

---

## 1. The matrix

Columns are identical in every sub-table:
*citation · date/venue · model(s) · phenomenon · intervention · studies representation? · studies
behavioral causality? · overlap with our result · what is genuinely new in ours.*

"Studies behavioral causality?" = **Y** only if the paper performs an intervention on the model's
internals and measures the change in a *behavioral* endpoint (ASR, refusal rate, task accuracy),
not merely a change in a decoded representation.

⚠ **Applying that definition to OURSELVES (added 2026-09-04).** By this bar we score **Y on refusal**
and ⛔ **not on attack success**. `R-019` leaves Llama's ASR contrast unsignifiant at the independence
unit and `R-048` leaves Qwen's sign undetermined. ⇒ The novelty claim against Yona et al. is that we
run the **internal causal intervention they lack** and tie it to **refusal**; ⛔ it is **not** that we
have tied one to **ASR**, and the column above now says so.

Our result, referenced in the overlap column as **(O1)/(O2)/(O3)**:

* **(O1)** demonstration-block attention knockout at L6–14 reduces a StrongREJECT rubric endpoint on
  Llama-3.1-8B-Instruct, and is a *capable* null on Qwen3-14B (model-specific by preregistered interaction).
* **(O2)** the codeword's representation moves 10–17 % of the way toward the explicit-concept
  representation at L6–L12 — but this is **not specific to the harmful concept**: `knife`/`gun`/`club`
  match or exceed `bomb` (`DCS-R-002`).
* **(O3)** representation-vs-behavior dissociation is the recurring finding across several sprints
  of this project.

### 1.1 The two in-repo references, and the direct ancestor of the attack

| citation | date / venue | model(s) | phenomenon | intervention | repr? | behav. causality? | overlap with ours | new in ours |
|---|---|---|---|---|---|---|---|---|
| Yona, Sarid, Karasik, Gandelsman, **In-Context Representation Hijacking** (the "Doublespeak" paper). arXiv 2512.03771; `doublespeak/INCONTEXT_REPRESENTATION_HIJACKING.pdf` **✓fetched** | v1 2025-12-03; **ACL 2026 Long, pp. 16852–16867** | Llama-3-8B-Instruct and Llama-3-70B-Instruct for interp; Llama-3.3-70B, Gemma-3-27b-it, and closed models (GPT-4/o1, Gemini 2.5, Claude 3.5 Sonnet, DeepSeek) for ASR | in-context substitution of a harmful keyword by a benign token drives the benign token's representation toward the harmful concept, "layer by layer"; refusal is bypassed because the refusal-mediating layer (12 in Llama-3-8B) still reads the benign meaning — an explicit time-of-check/time-of-use account | **read-out only**: logit lens + Patchscopes, averaged over 29 harmful requests, 10 in-context sentences each. Plus a *behavioral* ablation that varies the substitute token's lexical category (nouns/pronouns/adjectives/verbs) and measures ASR. **No activation patching, no attention knockout, no steering.** | **Y** | **N** — no internal intervention is tied to an ASR change | This is the paper our attack setting comes from. It owns: the layer-wise convergence claim (our **O2** is a re-measurement of the same phenomenon with a different instrument), and a generality claim on the *substitute-token* side. | (a) an internal **causal** intervention on the demonstration block with a behavioral endpoint (**O1**) — they have none. ⚠ **Updated 2026-09-04, and narrowed:** our behavioral endpoint clears this matrix's own bar on **refusal** (Llama 42→0, Qwen 150→0, well-powered, two models × four scopes) but **NOT on attack success** — Llama is direction-only and not significant at the domain independence unit (`R-019`), and Qwen is `CONFOUND-LIMITED` with the sign undetermined (`R-048`). ⛔ In this literature *"behavioral endpoint"* is read as **ASR**, so the unqualified form of this claim overstates us and must not be used; (b) a **specificity control on the harmful-concept side** (bomb vs knife/gun/club), which they never run — their ablation varies the codeword, not the concept; (c) a quantified, split-replicated effect size (`toward_B_frac`, dev-vs-heldout noise band) rather than a decoded-probability curve; (d) a **cross-family capable null** (Qwen3-14B) |
| Ben-Tov, Geva, Sharif, **Universal Jailbreak Suffixes Are Strong Attention Hijackers**. arXiv 2506.12880v2; `interp-jailbreak/` **✓fetched** | v2 2025-12-21; **TACL 2026** | Gemma-2, Qwen-2.5, Llama-3.1 | GCG suffixes "hijack" contextualization; a *dominance score* over attention quantifies hijacking strength, which predicts suffix universality | attention **knockout** on edges leaving adversarial tokens (logits→−∞, all layers), plus **patching** hijacking onto failed jailbreaks; then enhancement (≈5× universality, no extra compute) and mitigation (≥50 % ASR reduction) | **Y** | **Y** — knockout removes the attack, patching restores it, and both move ASR | Methodologically our closest neighbour: attention knockout on an attack-carrying token span, scored against a behavioral endpoint. This is where our knockout design comes from. | our carrier is an **in-context demonstration block with a semantic remapping**, not an optimized suffix; our knockout is **layer-banded (L6–14) and column-scoped** rather than all-layer; and we report a **model-specific null** where they report a mechanism that held across their three families |
| Anthropic et al., **Many-shot Jailbreaking**. OpenReview `cw5mgd71jW` †snippet | 2024; ICLR/NeurIPS-track | frontier long-context models | ASR follows a power law in the number of harmful in-context demonstrations | none (black-box, prompt-level) | N | N | shares the premise that the *demonstration block* is the attack carrier | we intervene on the demonstrations' attention path and read a behavioral endpoint; MSJ is a scaling curve with no internals |

### 1.2 Codeword / substitution jailbreaks

| citation | date / venue | model(s) | phenomenon | intervention | repr? | behav. causality? | overlap with ours | new in ours |
|---|---|---|---|---|---|---|---|---|
| Handa et al., **Jailbreaking Proprietary LLMs using Word Substitution Cipher**. arXiv 2402.10601 †snippet | 2024; OpenReview | ChatGPT, GPT-4, Gemini-Pro | word-substitution + priming bypasses safety (≈50 %/34 %/59 % ASR) | none | N | N | same *surface* idea as our codeword mapping (a benign token stands in for a harmful one) | entirely black-box there; the whole mechanistic layer (**O1**, **O2**) is absent |
| **WordGame** (obfuscation in query and response). arXiv 2405.14023 †snippet | 2024; arXiv | GPT-4, Claude, Llama | obfuscating the harmful word in both query and answer | none | N | N | codeword-substitution family | as above |
| **MetaCipher** — multi-agent cipher jailbreak framework. arXiv 2506.22557 †snippet | 2026-06; arXiv | multiple closed/open | 21 ciphers across 4 categories; time-persistent, universal | none | N | N | substitution-cipher family; establishes that the surface trick is now well-trodden | our contribution is not the attack — it is the mechanism and its **failure to be concept-specific** |

### 1.3 Mechanistic interpretability of jailbreaks and prompt injection

| citation | date / venue | model(s) | phenomenon | intervention | repr? | behav. causality? | overlap with ours | new in ours |
|---|---|---|---|---|---|---|---|---|
| Wagle, Uddin, Zhang, Wang, **Mechanistic Interpretability of LLM Jailbreaks via Internal Attribution Graphs**. arXiv 2607.07903 **✓fetched** | 2026-07-08; arXiv cs.CR | "multiple open-source LLMs" (unspecified in abstract) | jailbreaks act by safety suppression, feature emergence, and computation rerouting | attribution graphs over paired clean/attacked runs; targeted interventions on identified nodes, reported as improving robustness | **Y** | **Y** (defense direction) | their "safety suppression" route is the same family as our refusal-suppression finding from the prior sprint | our unit of intervention is a *prompt span* (the demonstration block), which is directly actionable at the input level, and we report the negative half (Qwen null, non-specificity) |
| Yin, Han, Li, **Robust Harmful Features Under Jailbreak Attacks: Attention Head Specialization**. arXiv 2606.28153 **✓fetched** | 2026-06-26; **ICML 2026 (oral)** | LLMs incl. a Llama-3-70B scale point | attacks suppress "Adversarially Compromised Heads" (early layers) while mid-layer "Safety-Aligned Heads" keep firing; ablating ~8 ACHs drives ASR 0 %→>95 % (≈40 heads at 70B) | head ablation, measured against ASR | **Y** | **Y** | **a dissociation in the mirror direction of ours**: their internal safety signal *persists* while behavior flips. Ours (**O3**) is a representation that *moves* while behavior does not follow. Both refute a naive representation⇒behavior reading | ours is measured on an in-context semantic-remapping attack and includes a preregistered cross-model interaction; theirs is head-level on standard jailbreaks |
| Hu, Chen, Ho, **Attention Slipping**. arXiv 2507.04365 **✓fetched** | 2025-07-06; arXiv | Gemma2-9B-It, Llama3.1-8B-It, Qwen2.5-7B-It, Mistral-7B-It | across attack families the model's attention to the unsafe span decays as the attack succeeds | attention temperature sharpening (a defense) | **Y** | **Y** | shares the premise that attention *allocation to a specific span* is the causal quantity | we knock out a span's attention as an *analysis* and get a model-specific answer, rather than proposing a universal defense |
| Zhang et al., **JBShield**. arXiv 2502.07557 **✓fetched** | 2025-02-11; **USENIX Security 2025** | multiple open LLMs | toxic concept *is* activated by jailbreak prompts; a separate "jailbreak concept" flips rejection→compliance | concept-direction manipulation (amplify toxic, suppress jailbreak); ASR 61 %→≈2 % | **Y** | **Y** | strongly relevant to **O3**: the toxic concept is *represented* even when the model complies | their concepts are generic (toxic / jailbreak); we ask the sharper question of whether the representation is specific to *one named concept* — and answer **no** (**O2**) |
| **IterInject** — indirect prompt injection with a mechanistic analysis. arXiv 2605.24659 †snippet | 2026-05; arXiv | LLM agents | attention-mediated threshold mechanism in mid-to-late layers, validated by causal intervention | causal intervention on attention | **Y** | **Y** | closest prompt-injection analogue: an injected span competing for attention with the real instruction | different threat model (agentic injection, no semantic remapping); no concept-geometry measurement |
| **Attention is All You Need to Defend Against Indirect Prompt Injection**. NDSS 2026 (arXiv 2512.08417) †snippet | 2026; NDSS | open LLMs | injected-span attention as a detection signal | attention-based detector | **Y** | N (detection, not causal manipulation of behavior) | span-attention as the operative quantity | as above |
| **Attention Eclipse**. arXiv 2502.15334 †snippet | 2025-02; arXiv | aligned LLMs | manipulating attention between prompt segments to bypass alignment | attention manipulation | **Y** | **Y** | attention between spans is causally load-bearing for refusal | our span is a *demonstration block* whose function is semantic, not adversarial-token-level |

### 1.4 Activation patching, causal tracing, and attention knockout as methods

| citation | date / venue | model(s) | phenomenon | intervention | repr? | behav. causality? | overlap with ours | new in ours |
|---|---|---|---|---|---|---|---|---|
| Geva, Bastings, Filippova, Globerson, **Dissecting Recall of Factual Associations**. arXiv 2304.14767 †snippet | **EMNLP 2023** | GPT-2, GPT-J | three-step attribute-extraction pipeline (subject enrichment → relation propagation → attribute query) | **attention knockout**: zero out all attention edges from a chosen source-position set at chosen layers; up to 60 % prediction-probability drop | **Y** | **Y** (task accuracy) | **this is the method our knockout instantiates**, applied to demonstration columns instead of subject columns | the endpoint is a safety-relevant behavioral rubric on an attack, and the design is a preregistered `intervention × condition` interaction with matched controls |
| **Tracing the Dynamics of Refusal / SALO**. arXiv 2605.02958 †snippet | 2026-05; arXiv | Qwen, Llama, Mistral | a sparse upstream "refusal trajectory" persists even when GCG suppresses the terminal refusal signal | patching malicious→benign activations; a white-box detector | **Y** | partially (patching triggers refusal) | another instance of **O3**-flavored persistence: refusal signal survives the behavioral bypass | our dissociation runs in the opposite direction and is measured on a *concept* representation, not a refusal signal |
| **Minimal, Local, Causal Explanations for Jailbreak Success**. arXiv 2605.00123 †snippet | 2026-05; arXiv | open LLMs | small, local causal explanations of jailbreak success | path patching / head-wise causal intervention; a small mid-to-late head subset carries the effect | **Y** | **Y** | supports "few components, mid-stack" as the general shape | our carrier is early-mid (L6–14) and prompt-span-scoped, and we report where it fails to hold |

### 1.5 In-context learning mechanisms: induction heads, retrieval, function vectors

| citation | date / venue | model(s) | phenomenon | intervention | repr? | behav. causality? | overlap with ours | new in ours |
|---|---|---|---|---|---|---|---|---|
| Olsson et al., **In-context Learning and Induction Heads**. Transformer Circuits, 2022 †snippet | 2022 | toy → small transformers | induction heads as the ICL mechanism | ablation | **Y** | **Y** (loss/ICL score) | the mechanism our demonstration block presumably rides on | we never claim the head-level identity; our claim is at the span/layer-band level, and we say so |
| Crosbie & Shutova, **Induction Heads as an Essential Mechanism for Pattern Matching in ICL**. arXiv 2407.07011 †snippet | 2024–25; arXiv | Llama-3-8B, InternLM | ablating induction heads costs up to ~32 % on abstract pattern tasks; ≥3 heads → collapse | head ablation + attention knockout of the induction pattern | **Y** | **Y** (task accuracy) | the same knockout logic, on the same kind of copy/pattern circuitry a codeword-remapping prompt would use | our endpoint is safety behavior, and our finding is that the span-level knockout **does not transfer across model families** |
| Yin & Steinhardt, **Which Attention Heads Matter for In-Context Learning?**. arXiv 2502.14010 **✓fetched** | 2025-02-19; **ICML 2025** | 12 LMs | few-shot ICL depends primarily on *function-vector* heads, not induction heads, especially at scale; FV heads often begin as induction heads | detailed head ablations | **Y** | **Y** | directly relevant to *why* a demonstration-block knockout might behave differently across families: the responsible head class is scale- and model-dependent | offers a candidate explanation for our Qwen null that we did not test — flagged as future work, not claimed |
| Wang, Wang, Bakalova, Hahn, **How Few-Shot Examples Add Up: A Causal Decomposition of Function Vectors in ICL**. arXiv 2605.16591 **✓fetched** | 2026-05-15; **ICML 2026** | multiple LMs | the n-shot FV ≈ a linear combination of per-example sub-FVs; models reweight examples by informativeness; QK routing contributes more consistently than value updates | causal decomposition separating QK routing from value updates | **Y** | **Y** (ICL task behavior) | the most precise available account of *how demonstrations aggregate into a causal direction* — the mechanism our demonstration block is exploiting | we ask whether that aggregation carries a **specific harmful concept** (it does not, **O2**) and whether cutting it changes **safety** behavior (model-specifically, **O1**) |
| **One Task Vector is not Enough** / **Understanding Task Vectors in ICL** (arXiv 2506.09048) †snippet | 2025–26 | multiple | task vectors emerge as linear combinations of demonstrations and can be injected zero-shot; limitations documented | vector injection | **Y** | **Y** | the "inject the demonstrations' summary" move is the natural sufficiency test complementary to our necessity test | our necessity test is run; the matched sufficiency (transplant) test is `DCS-B-003`, explicitly **not** currently citable |

### 1.6 Refusal directions and refusal suppression

| citation | date / venue | model(s) | phenomenon | intervention | repr? | behav. causality? | overlap with ours | new in ours |
|---|---|---|---|---|---|---|---|---|
| Arditi et al., **Refusal in LLMs Is Mediated by a Single Direction**. arXiv 2406.11717 †snippet | 2024; **NeurIPS 2024** | 13 open chat models | one diff-in-means direction is necessary and sufficient for refusal | directional ablation / addition | **Y** | **Y** | the Doublespeak paper's layer-12 argument is built on this; our prior sprints found refusal-*suppression*, not concept-injection, to be the causal locus | our locus is a **prompt span**, upstream of the refusal direction, and we test it with a behavioral rubric rather than a refusal-substring rate |
| Wollschläger et al., **The Geometry of Refusal: Concept Cones and Representational Independence**. arXiv 2502.17420 **✓fetched** | 2025-02-24, rev. 2026-02 | open chat models | refusal is mediated by multiple independent directions / cones up to ~5-D; orthogonality ≠ independence under intervention | gradient-based representation engineering | **Y** | **Y** | a direct caution for any single-direction reading of the Doublespeak time-of-check argument, and for our own `d_*` family | we already carry that caution in-repo (`R-23`/`R-24` retraction); nothing of ours is new *here* — this row exists to constrain what we may claim |
| **Refusal Beyond a Single Direction: Diff-in-Means vs INLP**. arXiv 2606.13720 †snippet | 2026-06; arXiv | open LLMs | multiple representationally independent refusal directions; ASR declines as more are searched | direction ablation | **Y** | **Y** | as above | — |
| **Refusal geometry reflects refusal training**. arXiv 2608.25390 †snippet | 2026-08; arXiv | open LLMs | diverse refusal prefixes raise stable rank and weaken refusal-vector ablation attacks | refusal-vector ablation | **Y** | **Y** | a training-side explanation for why a refusal-geometry result may be **model-specific** — a live candidate for our Llama-vs-Qwen split | we *measure* the model-specific split with a preregistered interaction and a capability floor; we do not yet test this explanation |

### 1.7 Representation-vs-behavior dissociation, and cross-model replication

| citation | date / venue | model(s) | phenomenon | intervention | repr? | behav. causality? | overlap with ours | new in ours |
|---|---|---|---|---|---|---|---|---|
| Walsh & Barkett, **Representation Without Control: Testing the Realization Effect in Language Models**. arXiv 2605.25151 **✓fetched** | 2026-05-24; arXiv cs.AI | Gemma | a linearly decodable realization-status signal at layer 18 whose steering direction does **not** reliably shift downstream risk choices; SAE decomposition shows probe-aligned and control-aligned features are semantically disjoint | linear probing vs activation steering, same construct | **Y** | **Y** (steering, null) | **the closest published statement of O3 as a general claim**: decodable ≠ controlling; they also warn against deploying probes as runtime safety monitors | ours is the same dissociation in a **safety/jailbreak** setting, on an *in-context-constructed* concept rather than a task-state signal, and with the added negative that the representation is not even concept-specific (**O2**) |
| **The Personality Illusion: Dissociation Between Self-Reports and Behavior**. arXiv 2509.03730 †snippet | 2025-09 | multiple | self-reported traits do not predict open-ended behavior | none (behavioral) | N | N | a weaker, non-mechanistic cousin of **O3** | ours is at the activation level |
| **Cross-Model Activation Generalizability Isn't Strong (Yet)**. LessWrong †snippet | 2026 | Llama, Gemma, Qwen, Pythia | cross-architecture activation similarity is real but weak; within-family patterns 4–9× stronger | linear transfer probes | **Y** | N | direct prior for our Llama↔Qwen split (**O1**) | we report a *causal-intervention* null across families with a preregistered interaction and a demonstrated capability floor, not a similarity statistic |
| **Architecture, Not Scale: Circuit Localization in LLMs**. arXiv 2605.08853 †snippet | 2026-05; arXiv | multiple families | GQA yields more concentrated, mechanistically stable circuits than MHA; architecture matters more than parameter count | circuit localization | **Y** | partially | a concrete candidate mechanism for why Llama-3.1-8B and Qwen3-14B differ under identical knockout | we have the empirical split; this is an untested explanation, flagged as such |
| **Do All Autoregressive Transformers Remember Facts the Same Way?** arXiv 2509.08778 †snippet | 2025-09; arXiv | several families | factual-recall mechanisms differ across architectures | causal tracing | **Y** | **Y** | precedent that a knockout result is a claim about *a model*, not about transformers | — |

### 1.8 Mechanistically derived adversarial objectives

| citation | date / venue | model(s) | phenomenon | intervention | repr? | behav. causality? | overlap with ours | new in ours |
|---|---|---|---|---|---|---|---|---|
| Winninger, Addad, Kapusta, **Using Mechanistic Interpretability to Craft Adversarial Attacks against LLMs**. arXiv 2503.06269 **✓fetched** | 2025-03-08, rev. 2026-07-03 | Gemma2, Llama3.2, Qwen2.5 | "acceptance subspaces" that do not trigger refusal; gradient optimization steers embeddings into them | subspace-targeted optimization; 80–95 % ASR, minutes not hours | **Y** | **Y** | **the positive result whose negative we hold**: this project tried a mechanistically derived objective (`d_surface`/Boombness as a GCG/MAC target) and it is **BLOCKED** — both steering signs suppress ASR, prediction-vs-causation ρ = −0.85, and naive baselines match or beat it | a documented, CI-backed **negative** for a mechanistically derived objective in this setting, with the diagnosis (the direction predicts but does not cause). Negative results of this shape are near-absent from the published record |
| **Attention-hijacking-guided GCG enhancement** (same paper as §1.1, row 2) | TACL 2026 | Gemma-2, Qwen-2.5, Llama-3.1 | dominance score used to select/boost universal suffixes (≈5×) | mechanism-guided selection | **Y** | **Y** | the successful counterpart to our blocked objective | our negative is on a *semantic-concept* direction, theirs a positive on an *attention-allocation* statistic — consistent with our own finding that the concept geometry is not concept-specific |

---

## 2. What the matrix says about our position

1. **The attack is not ours and must never be presented as ours.** Doublespeak is published (ACL 2026)
   and the repo vendored the authors' own code. Our contribution can only be mechanistic.
2. **The representation-convergence observation is also not ours.** The ACL paper claims layer-by-layer
   semantic hijacking. **O2** re-measures it with a different instrument and adds a control they did
   not run.
3. **The two things nobody in this matrix has published for this attack are:**
   (a) an internal **causal** intervention on the demonstration block scored against a behavioral
   endpoint (**O1**), and (b) the **concept-specificity control** on the harmful-concept side (**O2**,
   a negative).
4. **The dissociation framing has a strong 2026 precedent** (Walsh & Barkett; Yin et al.). We are not
   first to say "decodable ≠ controlling". We can be first to say it for an *in-context-constructed*
   concept in a *jailbreak* setting, with a preregistered cross-model interaction.
5. **Our strongest single asset is the negative.** §1.8 shows the published record is dominated by
   successful mechanism-guided attacks. A CI-backed, diagnosed failure of a mechanism-guided objective
   is rarer, and harder to get published, than another 90 %-ASR number.

---

## 3. Concurrent work that threatens novelty

**Yes — one work substantially overlaps, and it is the one this project is built on.**

**Yona, Sarid, Karasik & Gandelsman, "In-Context Representation Hijacking", ACL 2026 (arXiv 2512.03771).**

The exact overlapping claims:

* **Overlap 1 (representation convergence).** They claim, and support with logit lens and Patchscopes
  averaged over 29 harmful requests, that under the attack the benign token's internal representation
  progressively acquires the harmful concept's semantics across layers. **Our O2 is a re-measurement of
  the same phenomenon.** `toward_B_frac` = 10–17 % at L6–L12 is a different instrument (difference-of-means
  geometry over cell means) and a different effect-size convention, but it is not a different claim.
  We may present O2 as a **replication with a stronger control**, never as a discovery.
* **Overlap 2 (generality of the codeword).** Their Appendix D varies the substitute token across
  lexical categories (nouns, pronouns, adjectives, verbs), finds ASR flat, and concludes explicitly
  that "Doublespeak exploits a fundamental, general-purpose mechanism of in-context learning rather
  than relying on specific properties of particular token pairs." This is **adjacent to O2 and partly
  anticipates its spirit.** The differences are real but must be stated precisely rather than glossed:
  they vary the **codeword** and measure **ASR**; we vary the **harmful concept** and measure
  **representation geometry**. Their result says the attack does not care which benign word you pick;
  ours says the geometry does not care which harmful concept you pick. Ours is the sharper negative for
  a "Boombness" construct — but a reviewer who has read their Appendix D will not find our conclusion
  surprising, and we should not write as though they would.
* **Overlap 3 (the refusal-layer story).** Their §3.4 already connects the layer-wise convergence to
  Arditi et al.'s refusal direction, arguing a time-of-check/time-of-use gap at layer 12 in
  Llama-3-8B-Instruct. Our prior-sprint conclusion that **refusal suppression, not concept injection,
  is the causal locus** is in the same territory, though it reaches a different emphasis.

**Where they do not threaten us, stated as plainly:** the paper performs **no internal causal
intervention**. Its interpretability is entirely read-out (logit lens, Patchscopes); the only causal
manipulation anywhere in the paper is at the *prompt* level. It therefore cannot make, and does not
make, any claim of the form "this internal pathway is necessary for the attack's behavior". **O1** —
demonstration-block attention knockout at L6–14 against a StrongREJECT rubric endpoint — is not
anticipated by it. Neither is the cross-family capable null on Qwen3-14B.

**A tension worth resolving before publication, not after.** Their §3.4 argues that at layer 12 in
Llama-3-8B-Instruct "the semantic representation of the benign token is **not yet altered**", with the
shift arriving in middle-to-late layers. Our **O2** locates the peak of `toward_B_frac` at **L6–L12**
and finds it *decaying* through the mid-stack. These are different instruments on different model
sizes (they read layer indices off Llama-3-8B; we measure on Llama-3.1-8B), and a Patchscopes decode
probability and a difference-of-means distance ratio need not peak together — but as written the two
layer stories point in opposite directions. Either we explain the discrepancy or we do not cite their
layer claim as agreeing with ours.

**Second-order threats (overlap on framing, not on result):**

* **Walsh & Barkett (arXiv 2605.25151)** publishes the representation-vs-behavior dissociation as a
  standalone finding, including the SAE evidence that probe-aligned and control-aligned features are
  disjoint. **O3 is therefore not novel as a phenomenon.** It is novel only as an instance: in a
  safety setting, on an in-context-constructed concept.
* **Yin, Han & Li (ICML 2026 oral, arXiv 2606.28153)** publishes the mirror-image dissociation
  (safety representation persists, behavior flips) with head-level ablations. Combined with the row
  above, "representation ≠ behavior" is a 2026 consensus position, not a discovery.
* **Ben-Tov, Geva & Sharif (TACL 2026)** owns attention knockout on an attack-carrying span with a
  behavioral endpoint. Our method is theirs, redirected at a demonstration block. We should cite it as
  method provenance and not present the design as new.

**Nothing found in this search anticipates the combination** of (i) demonstration-block attention
knockout, (ii) a StrongREJECT rubric endpoint, (iii) a preregistered `intervention × condition`
interaction with matched controls, and (iv) a *capable* cross-family null. That combination, plus the
blocked mechanism-derived objective in §1.8, is the defensible novelty. The concept-convergence
geometry alone is not.

---

## 4. Exclusion / attrition record

| item | disposition |
|---|---|
| queries run | 12 |
| distinct works surfaced | ≈60 |
| works entered into the matrix | 24 |
| works excluded — attack papers with no internal analysis, beyond the 3 kept as family exemplars | ≈14 (cipher/obfuscation/agentic jailbreak variants; none change the novelty picture) |
| works excluded — defense-only papers with no mechanistic claim | ≈9 |
| works excluded — off-target (multimodal jailbreaks, malware detectors, neuroscience/lexical-semantics hits from the "semantic remapping" query) | ≈10 |
| **"in-context semantic remapping" query — failed** | returned lexical-semantics and neuroscience literature, no LLM-mechanism work. The LLM-side literature on this phenomenon appears to consist essentially of the Doublespeak paper itself. Recorded as a **null search**, not as evidence of a gap. |
| rows verified by fetching the source (**✓fetched**) | 12 |
| rows resting on search snippets only (**†snippet**) | 12 — venue/model/claim fields in these rows are **unverified** and must be opened before citation |
| in-repo PDFs read | 2 (structure and analysis sections only; no prompt, demonstration, or completion text was read into this document) |
| our own numbers quoted here | inherited from the phase log (`DCS-R-001`, `DCS-R-002`, `TSC-R-001/004/005`); **no new measurement was made for this document** |

**Known limits of this document.** It is a point-in-time web search by one worker on 2026-09-02, run
in US-region search; it is not a systematic review, has no inclusion protocol beyond the eleven topics
in the brief, and searched no venue proceedings directly. Absence of a work from this matrix is weak
evidence of its non-existence. The half of the matrix marked **†snippet** has not been read.

---

## 5. Re-check 2026-09-05 (`DCS-A-022`) — five additions, one of which changes the framing

Appended, not merged into §1–§4: the rows above are the 2026-09-02 state and are left standing.
Bounded re-check, ~25 min. ⚠ Verification levels are lower here than in §1 — only the first row was
read in full.

| id | venue / date | what it does | bearing on our position | verified |
|---|---|---|---|---|
| `2305.14160` | EMNLP 2023 | "Label Words are Anchors". Zeroes attention `A_l(p,i)` at label-word positions in first-5 / last-5 layer bands; App. D sweeps the number of isolated layers | **Closest method precedent inside ICL, and it was missing.** Cite as provenance beside `2304.14767`. Limits: edge is text→label *within* demos, not demo→query; its demo→query claim is correlational (AUC≈0.8), not a knockout | ✓ full PDF |
| `2605.04061` | ⚠ venue string self-contradictory — **verify before citing** | "Single-Position Intervention Fails". Single-position 0 %, multi-position ≤96 %; query position strictly necessary; "universal intervention window at ~30 % depth" (≈L10/32) | ⚠ **Most direct threat to the K-step.** Publishes "the ICL pathway is distributed, not single-position", and its depth window coincides with our L6–14. Frame K as quantitative localisation on the **query-row axis**, not as discovering distribution | ⚠ abstract |
| `2605.28854` | COLM 2026 | Representational geometry reorganises during ICL; task-axis amplification "insufficient to improve behavioral performance" | Representation≠behaviour **inside ICL** — closer than `2605.25151`. Citation now mandatory | ⚠ abstract |
| `2609.00064` | 2026-08-30 | Attention-level ICL metrics saturate while behaviour degrades | Post-matrix. Cautions directly against inferring behaviour from a readout endpoint | ⚠ abstract |
| `2608.03210` | 2026-08-04 | ICO: black-box semantic-shift jailbreak, 74.6 % ASR, no mech analysis | Crowds the **phenomenon**, not the mechanism | ⚠ abstract |

**Also missing by name and to be added:** `2310.15916` (Hendel et al., task vectors) and `2310.15213`
(Todd et al., function vectors). The matrix cited only their descendants.

### 5.1 ⛔ Correction to §2's framing

§2 concluded that the internal causal intervention is ours. That **stands only as an intersection**.
The sentence *"nobody has causally intervened on the demonstration→query pathway in ICL"* is **FALSE**:
`2310.15916` patches a demonstration-derived vector into the query pass (sufficiency) and
`2310.15213` ablates function-vector heads by causal mediation (necessity). What remains ours is the
**intersection**: demo→query attention knockout, layer-banded, **on an in-context semantic-remapping
attack**, with a cross-family capable null.

### 5.2 ⛔ Standing wording rule

Write **"abolishes the forced-choice preference"**, never *"destroys the remapping"* — the endpoint
is a readout and the behavioural link is `NOT ESTABLISHED` (`R-075`); `2609.00064` and `2605.28854`
are exactly the papers a reviewer would cite against the stronger wording.

### 5.3 ⚠ Largest uncovered risk

No OpenReview / proceedings search was performed. A competing mechanistic Doublespeak paper under
review would be invisible to both arXiv and Semantic Scholar. Web search cannot close this.
