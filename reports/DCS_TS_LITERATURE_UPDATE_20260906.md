# DCS — Literature update, 2026-09-06/07

**Status.** Bounded re-check, appended to (not a replacement of) `reports/DCS_LITERATURE_MATRIX.md`.
That file is **not modified** by this document, per instruction. This document re-verifies the four
named targets by direct fetch and runs one fresh sweep. Written from git branch
`behavioral-causality-sprint`; "today" for search purposes is 2026-09-06/07.

**Standing constraint carried over, unchanged.** The claim *"first to causally intervene on
demonstration→query attention in ICL"* is **FALSE** and is not re-asserted anywhere below. It was
killed by `2504.00132` (Bakalova et al., ablates `y_i → t_{N+1}` edges) and, before that, by
`2310.15916`/`2310.15213`. This document treats that as settled and does not re-litigate it.

---

## 1. The four named targets, re-verified by direct fetch

### 1.1 arXiv 2609.02438 — Sudheendra & Srivastava, "When Decodability Is Not Enough: Logical
Validity Representations, Behavioral Dissociation, and Causal Tests in Language Models"

**Fetched:** `arxiv.org/abs/2609.02438`. Submitted 2026-09-02 (v1). Authors: Smitha Muthya
Sudheendra, Jaideep Srivastava.

**Abstract, verbatim:** *"Large language models can look capable of logical reasoning, but correct
or incorrect answers alone tell us little about what the model represents internally. We study
logical verification in five open-weight transformer models using matched valid–invalid
premise–claim pairs that vary across inference families, semantic domains, templates, and difficulty
levels. Despite near-chance behavioral performance, logical validity is often almost perfectly
decodable from hidden states and remains strongly decodable under held-out templates, domains, and
inference families. Validity also remains highly decodable on behaviorally incorrect examples in the
conditions where correctness-conditioned evaluation is well defined. At the same time, exhaustive
leave-one-out tests reveal clear limits to this generalization, and interventions along
probe-derived validity directions have only weak, nonspecific effects compared with random controls.
Our results suggest that representing validity, expressing it in behavior, and using it causally are
distinct. Validity related information can be strongly decodable from a model's hidden states
without being reliably expressed in its output."*

**Precisely what it claims.** Three-way separation — decodable, expressed-in-behavior, causally-used
— on ONE property: whether a premise validly entails a claim, in a logic-verification task
(true/false judgment over premise–claim pairs). Method: linear probing for decodability, generalized
across held-out templates/domains/inference-families; probe-direction interventions (not attention
knockout, not attribution-graph patching) compared against random-direction controls, scored against
downstream behavior. Population: 5 open-weight models, a logic-verification benchmark constructed
by the authors (not a jailbreak or ICL-attack corpus).

**What it does NOT contain, checked directly against the abstract and the extraction above:** no
in-context learning framing (no demonstrations, no few-shot construction of the represented
property), no jailbreak or safety framing, no codeword/substitution mechanism, no attention
intervention of any kind, no mention of a *concept identity* that was itself installed by a
prompt — validity is a property of the input pair, not something an attacker remaps.

**Verdict: OVERLAPS on framing, ORTHOGONAL on everything else operational.**

This is the sharpest possible confirmation of what `DCS-A-025` §6.2 already flagged as an open
question for the humans, now answered concretely: **2609.02438 pre-empts the framing sentence, not
the result.** The framing sentence at risk is something like *"we show that a representation can be
decodable without being causally used"* — that sentence, unqualified, is now foreclosed as a
contribution; 2609.02438 (five models, held-out generalization, LOO limits, probe-direction vs.
random-direction intervention) is a more thorough, better-controlled instance of exactly that
three-way separation, on a cleanly operationalized property, published four days before the matrix
was compiled. It does **not** pre-empt any claim of ours that depends on: (a) the represented
property being an *attacker-installed, in-context-constructed* concept identity rather than a latent
property of the input; (b) a *safety/jailbreak* behavioral endpoint; (c) an *attention-knockout*
intervention on a *demonstration span* rather than a probe-direction intervention; (d) a
cross-model-family **interaction** (capable-vs-null) rather than a uniform effect across five models.

**Bearing on "which half of the paper leads" (the question `DCS-Q-002` posed to Omer and Matan).**
This re-verification makes the answer sharper, not softer: if the paper's positioning sentence is any
version of "decodable ≠ causally used, we show this too," it is now a **citation of a converging
literature (Walsh & Barkett 2605.25151, Sudheendra & Srivastava 2609.02438, Cheng & Zhang 2605.04061,
the bracket-sequence paper 2604.22128 below)**, not a contribution. The lead must be the **specific,
narrower** claim — the attention-knockout intervention on the demonstration block, scored against a
safety behavioral endpoint, with the cross-family interaction — because that combination is what
survives after 2609.02438. This strengthens rather than changes the direction §6.2 was already
pointing.

### 1.2 arXiv 2504.00132 — Bakalova, Veitsman, Huang & Hahn, "Contextualize-then-Aggregate:
Circuits for In-Context Learning in Gemma-2 2B"

**Fetched:** `arxiv.org/abs/2504.00132`. v1 2025-03-31, v4 (latest) 2025-09-17.

**Abstract, verbatim:** *"In-Context Learning (ICL) is an intriguing ability of large language
models (LLMs). Despite a substantial amount of work on its behavioral aspects and how it emerges in
miniature setups, it remains unclear which mechanism assembles task information from the individual
examples in a fewshot prompt. We use causal interventions to identify information flow in Gemma-2 2B
for five naturalistic ICL tasks. We find that the model infers task information using a two-step
strategy we call contextualize-then-aggregate: In the lower layers, the model builds up
representations of individual fewshot examples, which are contextualized by preceding examples
through connections between fewshot input and output tokens across the sequence. In the higher
layers, these representations are aggregated to identify the task and prepare prediction of the next
output."*

**Confirmed exactly, cross-checked against `DCS-A-025` F-1 which is carried forward unchanged:**
it ablates **`y_i → t_{N+1}` edges** (demonstration-output-token to final-query-token connections) by
**counterfactual K/V patching**, applied **simultaneously at every layer and every head** — i.e. an
**all-layer, all-head, single-source-class, single-target-position** intervention. Endpoint: **task
accuracy** on five naturalistic ICL tasks, on **one model, Gemma-2 2B**.

**What it does NOT do, stated precisely for the delta:**
- No layer-banding: the intervention is applied at every layer simultaneously, not localized to a
  layer range (our L6–14 knockout is a band, chosen and tested as a band).
- No attention-weight zeroing: it substitutes K/V activations computed from a *corrupted prompt*,
  not zeroed attention logits (a different intervention primitive from the Geva et al. / Ben-Tov et
  al. knockout our method descends from).
- Single query position: the "query" is the one final next-token prediction slot; there is **no
  variation of query-row count**, so there is still no analogue anywhere in this paper of a
  query-row-count threshold / ladder.
- No safety or jailbreak framing, no semantic-remapping attack, no cross-model-family comparison
  (one model only), no `intervention × condition` interaction design.
- Task is standard few-shot classification/naturalistic ICL, not an attacker-installed codeword.

**Verdict: OVERLAPS** (it is the closest precedent for "intervene on the demo→query pathway causally
in ICL", and the standing rule from §6.1 of the matrix stands: do not claim to be first at that). It
does **not** threaten the K-step (query-row-count axis), the layer-banding, the attention-knockout
primitive specifically, the semantic-remapping attack setting, or the cross-family capable-null
design. Confirms the matrix's existing characterization; no correction needed.

### 1.3 Yona, Sarid, Karasik & Gandelsman — ACL 2026, "In-Context Representation Hijacking"

**Fetched/located:** ACL Anthology `2026.acl-long.768` (pp. 16852–16867, ACL 2026, San Diego), arXiv
`2512.03771`. This is the **same paper already at row 1.1 of the matrix** (the "Doublespeak" paper,
the in-repo PDF, the direct ancestor of our attack) — there is no second Yona et al. paper. Re-search
confirms authorship (Itay Yona, Amir Sarid, Michael Karasik, Yossi Gandelsman), venue, and the core
claim: the attack substitutes a harmful keyword with a benign token across in-context examples,
driving the benign token's internal representation toward the harmful concept "layer by layer",
validated by logit lens + Patchscopes, with ASR up to 74% on Llama-3.3-70B-Instruct.

**Verdict: no new overlap beyond what the matrix already records at length in §1.1 and §3.** This
re-check found nothing indicating a second, distinct Yona-authored ACL 2026 paper on a different
topic. Treat the matrix's existing row-1.1 and §3 analysis (the "Overlap 1/2/3" breakdown and the
layer-12-vs-L6–L12 tension) as current and unrevised.

### 1.4 arXiv 2605.04061 — Cheng & Zhang, "Single-Position Intervention Fails: Distributed Output
Templates Drive In-Context Learning"

**Fetched:** `arxiv.org/abs/2605.04061`.

**Abstract, verbatim (key sentences):** *"Single-position activation intervention achieves 0% task
transfer across all 28 layers of Llama-3.2-3B — despite 100% probing accuracy at those same
positions... Multi-position intervention — replacing activations at all demonstration output tokens
simultaneously — achieves up to 96% transfer (N=50, 95% CI: [87%, 99%]) at layer 8... We establish
the generality of these findings across four models spanning three architecture families (LLaMA,
Qwen, Gemma), discovering a universal intervention window at ~30% network depth. Causal tracing
uncovers an asymmetric architecture: the query position is strictly necessary (53-100% disruption)
while no individual demonstration position is necessary (0% disruption)."*

**Concretely assessing the threat.** The matrix's `A-022` flagged this as "most direct threat to the
K-step" (our query-row-count knockout axis) on the strength of an abstract-only read. Now fetched in
full:
- What it establishes: (i) single demonstration position ≠ causally sufficient, but the **set** of
  demonstration-output positions, patched together, is; (ii) a depth window (~30%) that is stated to
  coincide with our L6–14 band; (iii) **the query position is asymmetrically necessary** — but this
  is stated as a binary (present vs. ablated single query token), not as a **count** of query rows.
- **What it still does not have, confirmed on the fetched abstract:** no variation of the number of
  query rows/positions being attended to or knocked out — the "query" throughout is the single
  next-token-prediction slot of a standard few-shot classification setup. There is no ladder over
  "how many query rows does the effect require" because there is exactly one query row in this
  paper's task design (it evaluates one final query token per trial, four models, not a swept
  query-row count within a trial).
- Cross-checking my own earlier fetch above against `A-022`'s venue claim: the source this session
  retrieved labels the venue **"ICLR 2026 (Learning and Intelligent Optimization Conference)"** —
  which is an internally inconsistent string (LION and ICLR are different venues) and does **not**
  clearly resolve `A-022`'s F-4 correction ("LION 2026 + ICLR 2026 workshops"). **Flag as UNRESOLVED,
  not corrected** — a second source disagrees with a third in exactly the way that made `A-022`
  mark this "verify before citing" in the first place. Do not cite a specific venue string for this
  paper without a further check (e.g. the paper's own PDF header / OpenReview page) before
  submission.

**Verdict: OVERLAPS**, confirmed, on the *depth-window* and *single-position-insufficiency* claims;
the matrix's existing framing — "quantitative localisation on the query-row axis, not discovery of
distribution" — is the correct hedge and needs no revision. **The K-step's query-row-COUNT axis
specifically remains unaddressed by this paper** on the fetched abstract; this is confirmed, not
newly discovered.

---

## 2. Fresh sweep, 2025–2026

Six searches run: concept-specific representation probing / causal concept erasure (LEACE, concept
scrubbing); activation patching for concept identity; ICL demonstration→query attention flow;
codeword/semantic-remapping interpretability; decodable-but-not-causal dissociations; in-context
jailbreak/representation-hijacking mechanisms. Two new works surfaced that were not already in the
matrix or in `A-022`/`A-025`; both are logged below with a verdict. Everything else returned either
already-catalogued items (`2607.07903`, `2608.03210`, `2609.00064`-adjacent territory) or off-target
hits (LEACE itself, 2023; generic concept-erasure tooling; multimodal ICL).

| id | work | date | fetched? | what it does | verdict |
|---|---|---|---|---|---|
| `2602.11495` | Kadali & Papalexakis, "Jailbreaking Leaves a Trace: Understanding and Detecting Jailbreak Attacks from Internal Representations of LLMs" | 2026-02-12, rev. 02-20 | ✓fetched abstract | Layer-wise tensor-based analysis of hidden-state differences between jailbreak and benign prompts, across GPT-J/LLaMA/Mistral/Mamba; proposes an inference-time "selective layer bypass" defense (78% jailbreaks blocked, 94% benign preserved). Detection/defense paper; no codeword-substitution mechanism, no concept-specificity control, no attention-knockout intervention on a demonstration span. | **RELATED, no threat.** Shares only the general premise that jailbreak internal states differ layer-wise; does not touch concept identity, in-context construction, or our intervention design. |
| `2604.22128` | Sharma, Dawes & Raval, "Dissociating Decodability and Causal Use in Bracket-Sequence Transformers" | 2026-04-24, rev. 06-16 | ✓fetched abstract | Toy/synthetic Dyck-language (balanced-bracket) transformers, extended to templated natural language. Probes depth/distance/top-of-stack signals (all decodable); shows only attention-to-true-top-of-stack is causally used for long-range accuracy, while decodable residual-stream subspaces for depth/distance are near-causally-inert when ablated. | **OVERLAPS on framing only, same bucket as 2609.02438.** Another instance of "decodable ≠ causally used" published in the 2026 window, but on a synthetic symbolic task, not language/safety/ICL-attack content. Adds to the density of the converging literature that the dissociation *framing* (not our specific instance of it) cannot lead the paper. |

**Everything else the sweep returned was already in the matrix** (`2607.07903`, `2608.03210` "ICO",
LEACE `2306.03819`, `2605.25151` Walsh & Barkett, `2605.04061`, `2504.00132`) or was off-target
(`2601.10700` LIBERTy — counterfactual concept-explanation benchmarking, not a jailbreak/ICL setting;
`2601.00267` ActErase — image/diffusion-model concept erasure, wrong modality; `2301.04709` causal
abstraction theory, foundational not novel; `2608.10566`, `2608.10214` — concept-dimension and
parametric-modularity questions unrelated to attacker-installed concepts).

**Null-search note (per the honesty rule).** The query aimed specifically at "codeword or semantic
remapping interpretability" returned nothing beyond the Doublespeak/ICO family already catalogued —
consistent with `A-022`'s and the original matrix's finding that the LLM-mechanism literature on this
exact phenomenon is essentially the Doublespeak paper plus its own descendants. This is recorded as a
**NULL SEARCH**, not as evidence that the space is empty of competitors — see §4 below on blind spots.

---

## 3. Updated novelty table

| # | candidate novel piece | verdict | deciding citation | narrowed claim we can still defend |
|---|---|---|---|---|
| 1 | semantic codeword remapping under **causal attention intervention** | **NARROWED** | `2504.00132` (demo→query edge ablation, all-layer); `2305.14160`/`2304.14767` (knockout method itself) | We are not first to causally intervene on the demo→query pathway in ICL, and not first to knock out attention in ICL generally. We can defend: a **layer-banded (L6–14), attention-zeroing** (not K/V-substitution) knockout **on an in-context semantic-remapping/jailbreak attack specifically**, scored against a **safety** behavioral endpoint, which no fetched work combines. |
| 2 | remapping vs. concept-identity axes as **separable directions** | **SURVIVES** (narrowly) | Doublespeak/Yona et al. `2512.03771` Appendix D (varies codeword, measures ASR) | Nobody fetched varies the **harmful-concept side** while measuring **representation geometry** (our O2: `bomb` vs `knife`/`gun`/`club`, no specificity found). Yona et al. vary the codeword and measure ASR — the mirror axis. This survives as an instance, not as "the first specificity control on either axis." |
| 3 | **query-row-count** threshold under attention knockout | **SURVIVES**, but now precisely bounded | `2605.04061` (single query POSITION is necessary, but never varies query-row COUNT); `2504.00132` (single query slot, no count axis) | No fetched paper varies the *number* of query rows subjected to/spared from knockout. We can defend a **quantitative localization on the query-row-count axis** specifically — but must not claim to have discovered that "the query is necessary" (that is `2605.04061`'s result, confirmed above), only that we measured *how many* query rows the effect requires. |
| 4 | **concept-axis causal intervention** (projection-out / patching a concept-identity direction, not just a codeword position) | **NARROWED** | `2609.02438`, `2604.22128`, `2605.25151` (Walsh & Barkett) — all publish probe-direction/subspace interventions with weak or null causal effect on a decodable-but-inert signal | The general move "intervene on a probe-derived concept direction and find it causally inert/weak" is now a 2026 pattern across logic-validity, bracket-depth, and realization-status domains. We can defend it only as an instance **in the safety/jailbreak, in-context-constructed-concept setting**, not as a novel intervention type. |
| 5 | representation **survives** semantic-readout destruction (i.e., decodability persists after an intervention that kills the behavioral report) | **NARROWED / effectively DEAD as a general claim** | `2609.02438` ("remains strongly decodable... interventions... have only weak, nonspecific effects"); `2604.22128`; `2605.25151`; matrix's own Yin/Han/Li `2606.28153` (mirror-direction persistence) | "Decodable survives behavioral destruction" is now a densely populated 2026 finding across at least four independent domains (logic validity, bracket structure, realization status, safety-head persistence). We can defend only the **specific instance**: this persistence holds for an *attacker-installed* concept identity under a *demonstration-attention* knockout, in a *jailbreak* setting — stated as one more confirming data point in a converging literature, never as the phenomenon's discovery. |

---

## 4. WHAT WE MUST NOT SAY

Novelty sentences now foreclosed, to be actively screened out of any draft:

1. *"We show that a representation can be decodable without being causally used."* — Foreclosed by
   `2609.02438`, `2604.22128`, `2605.25151`, and (mirror-direction) `2606.28153`. This is now a 2026
   consensus finding across at least five papers in five different task domains; ours is one more
   instance, stated last, not the discovery.
2. *"We are the first to causally intervene on the demonstration→query attention pathway in
   in-context learning."* — Already killed twice in the matrix (`2310.15916`/`2310.15213`, then
   `2504.00132`); re-confirmed FALSE by this update's direct fetch of `2504.00132`. Do not resurrect
   in any form, including softened variants like "one of the first."
3. *"We discover that ICL's causal locus is distributed rather than single-position."* — This is
   `2605.04061`'s finding (0% single-position transfer, 96% multi-position, on four model families),
   confirmed by direct fetch. We may cite it as a **method precedent** for why a layer-band / span
   knockout (rather than a single-position ablation) is the right instrument; we may not claim the
   distributed-vs-local finding itself.
4. *"We discover that the ICL causal effect concentrates at a specific network depth (~30%)."* —
   `2605.04061`'s finding, confirmed. Our L6–14 band may be presented as landing inside that reported
   window, which is corroboration, not discovery.
5. *"Decodability of a concept does not imply it is used causally"* stated as a **general
   contribution of this paper** — must be reframed as a citation to the converging 2026 literature
   (§3 row 5), with our own instance offered as confirmation in a novel (safety/jailbreak,
   attacker-installed-concept) setting, never as the lead claim.
6. *"Nobody has probed whether an installed representation survives destruction of its behavioral
   report"* (unqualified) — foreclosed for the same reason as #5; must specify "for an
   attacker-installed, in-context-constructed concept identity, in a jailbreak setting" every time
   this claim is made.
7. Any claim implying a **second, independent Yona-authored ACL 2026 paper** distinct from the
   Doublespeak paper already in the matrix — this re-check found no such paper; there is one Yona et
   al. ACL 2026 paper, already fully catalogued at matrix row 1.1.
8. Do not cite a specific venue string for `2605.04061` (e.g. "ICLR 2026") without an independent
   check — this update's own fetch produced an internally garbled venue string ("ICLR 2026 (Learning
   and Intelligent Optimization Conference)"), which conflicts with `A-022`'s "LION 2026 + ICLR 2026
   workshops" note. Both are now flagged UNVERIFIED; resolve from the paper's own PDF/OpenReview page
   before the venue is printed anywhere.

---

## 5. Search coverage, honestly stated

**What was done this pass.** Four direct WebFetch calls against arXiv abstract pages for the four
named targets (2609.02438, 2504.00132, Yona et al. via ACL Anthology + arXiv, 2605.04061), plus two
follow-up fetches on papers the sweep surfaced (2602.11495, 2604.22128), plus four fresh WebSearch
sweeps across the six requested topics collapsed into four queries (concept-erasure/LEACE/patching;
ICL demo→query attention; codeword/semantic-remapping jailbreak mechanism; decodable-but-not-causal
dissociations) and one targeted search on representation-hijacking/concept-remapping activation
patching. All four named targets were fetched at the abstract level (not full-PDF); none were fetched
as full text/HTML body in this pass beyond what the WebFetch tool's markdown conversion returned for
the abstract page.

**Blind spots, explicit:**
- **OpenReview / conference-proceedings search was not performed in this pass either.** The matrix's
  §5.3 flagged this as the largest uncovered risk on 2026-09-02 ("A competing mechanistic Doublespeak
  paper under review would be invisible to both arXiv and Semantic Scholar. Web search cannot close
  this.") and `A-025` §6.3 confirmed it was still open on 2026-09-06. **It remains open after this
  update.** This update used only WebSearch (which indexes public web/arXiv listings, not OpenReview
  submission systems) and WebFetch against arXiv/ACL Anthology URLs — neither tool queried OpenReview
  directly, and no OpenReview search was attempted this pass. This is a **gap, not a null result** —
  it was not searched, so its absence from this document is uninformative about what exists there.
- **No full-PDF read** was performed for any of the four named targets in this pass (abstract-page
  fetch only); a full-text read could surface additional overlap (e.g., method details, specific
  numeric effect sizes, or discussion-section framing) not visible in the abstract. Anything stated
  above beyond the quoted abstract text should be treated as **derived from the fetch tool's
  extraction**, which is a secondary summarization step, not a verbatim PDF read — a residual source
  of error the matrix's own verification-level convention (✓fetched vs. †snippet) would mark as
  intermediate: better than a search snippet, short of a full-PDF ✓fetched read.
- **Venue metadata for `2605.04061` is unresolved**, not merely unverified — two independent checks
  (this update's fetch, and `A-022`'s original note) disagree on the specific venue string. Flagged in
  §4 item 8; do not print a venue for this paper without a third, authoritative check.
- **No search was run this pass specifically for a second/independent replication of the
  concept-specificity control (O2: bomb vs. knife/gun/club)** beyond what the original matrix already
  logged as missing citations (`2607.13075`, `2507.21141`, both still †snippet, unopened). This
  update did not open them; they remain **missing citations for the specificity half**, exactly as
  `A-025` F-5 left them.
- **Semantic Scholar was not queried directly** in this pass (only Google-indexed web search via the
  WebSearch tool and direct arXiv/ACL Anthology fetches); this mirrors the original matrix's own
  stated method and does not close any gap it left open.
- Two new works were found (`2602.11495`, `2604.22128`); given the density of hits returned by only
  four fresh queries, it is very likely that a broader or differently-worded sweep would surface
  additional 2026 "decodable ≠ causal" instances beyond the five already catalogued (Walsh & Barkett,
  Sudheendra & Srivastava, Sharma/Dawes/Raval, Yin/Han/Li's mirror case, and the matrix's own O3).
  This is stated as a **likelihood, not a finding** — no further search was run to confirm or refute
  it in this bounded pass.
