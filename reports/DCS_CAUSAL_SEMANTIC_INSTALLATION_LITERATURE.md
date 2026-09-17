# Literature review: causal semantic installation in Doublespeak / in-context semantic remapping

**Date:** 2026-09-15
**Scope:** prior work bearing on the chain `demonstrations -> installed semantic representation -> causal query-side rescue` for Doublespeak-style codeword-substitution jailbreaks.

## 1. Method and coverage limits

**Method.** 17 web searches (listed in §6) across the eight topic clusters requested, plus 6 direct page fetches of primary sources (arXiv abstract/HTML pages) to verify authors, venue, models and — critically — whether each paper's interventions are causal or descriptive. Queries deliberately varied phrasing (attack-side vocabulary: "doublespeak", "codeword substitution", "word substitution cipher", "representation hijacking"; mechanism-side vocabulary: "attention knockout", "activation patching", "causal mediation", "interchange intervention", "causal subspace", "refusal direction", "rescue refusal", "function vector", "retrieval head").

**Coverage limits — read these before relying on this file.**
- This is a *search-driven* review, not an exhaustive one. Only English-language, web-indexed material was seen. No systematic citation-graph crawl (forward/backward) was run on the closest neighbours.
- Several results returned by search carry 2026 arXiv identifiers that postdate the reviewer's training data. For those, the title + identifier come straight from the search result, but author lists and detailed claims were **not** independently verified unless a fetch is noted. Such rows are marked "unverified" rather than guessed.
- Where a paper's abstract page was fetched but the full PDF was not read end-to-end, statements about "no causal intervention" reflect the abstract + section-level HTML reading only. The single most load-bearing such judgement (Yona et al.) is flagged explicitly in §5 as a residual risk: an appendix experiment could exist that the fetch did not surface.
- Workshop papers, non-archival reports, and LessWrong/Alignment-Forum posts were not systematically searched. Some mechanistic jailbreak work circulates there first.
- No claim in this file should be read as "nobody has done X"; only as "no work doing X surfaced in these searches".

## 2. Table of relevant works

Similarity is judged against *our specific chain*: in-context demonstrations installing a codeword->harmful-concept mapping, measured by a concept-free readout, with a causal attention knockout on the demo->query edge and a query-side residual restore that rescues refusal.

| Citation | Model(s) | Phenomenon | Intervention | Causal / Correlational | Similarity | What remains novel for us |
|---|---|---|---|---|---|---|
| Yona, Sarid, Karasik, Gandelsman. *In-Context Representation Hijacking* ("Doublespeak"). arXiv:2512.03771; ACL 2026 Long Papers (aclanthology 2026.acl-long.768). (fetched) | Llama-3-8B-Instruct, Llama-3-70B-Instruct, Llama-3.1-8B-Instruct, Llama-3.3-70B-Instruct (+ closed models for ASR) | Exactly our attack: benign codeword substituted for harmful keyword across ICL demos; benign token's representation converges to harmful semantics over layers; "time-of-check vs time-of-use" gap vs the refusal direction (~L12) | Logit lens; Patchscopes (representation read-out into an identity probe) | **Correlational / descriptive.** Patchscopes patches *for interpretation*, not for ablation; no attention knockout, no steering, no ablation, no behavioral rescue | **HIGH** — same attack, same model family, same "semantics get installed across layers" claim | The entire causal layer: demo->query attention knockout, layer-band localisation (L6-14), query-side residual restore rescuing refusal, and a low-rank installation-predictive subspace as mediator |
| Wei, Wang, Wang. *Jailbreak and Guard Aligned Language Models with Only Few In-Context Demonstrations* (In-Context Attack). arXiv:2310.06387 | multiple aligned LLMs (unverified list) | Few harmful ICL demonstrations flip alignment | Prompt-level only | Correlational (behavioral) | Medium — establishes demos-as-jailbreak, no remapping, no internals | Everything mechanistic; also the *semantic remapping* variant rather than harmful-exemplar variant |
| Handa et al. *Jailbreaking Proprietary Large Language Models using Word Substitution Cipher* / *When "Competency" in Reasoning Opens the Door to Vulnerability*. arXiv:2402.10601 | GPT-3.5, GPT-4, Gemini-Pro (ASR up to 59.4%) | Unsafe->safe word mapping supplied as a cipher, then the mapped question | Prompt-level only | Correlational (behavioral) | Medium — same *surface* trick (codeword mapping) delivered as an explicit cipher rather than as ICL demos | All internals; and the distinction between an explicitly-stated mapping and one *induced* by demonstrations |
| *WordGame: Efficient & Effective LLM Jailbreak via Simultaneous Obfuscation in Query and Response*. arXiv:2405.14023 (authors unverified) | proprietary + open LLMs (unverified) | Harmful word replaced by a word-guessing game | Prompt-level only | Correlational | Low-medium | All internals |
| Arditi, Obeso, Syed, Paleka, Panickssery, Gurnee, Nanda. *Refusal in Language Models Is Mediated by a Single Direction*. arXiv:2406.11717; NeurIPS 2024 | 13 open chat models incl. Llama-3 family | Refusal mediated by one residual-stream direction | Directional ablation (necessity) and activation addition (sufficiency) | **Causal** | Medium — gives us the refusal-side causal toolkit and the 1-D mediator template; nothing about ICL remapping | Our mediator is on the *semantic installation* side (what the codeword means), not the refusal direction itself |
| Zhao, Huang, Wu, Bau, Shi. *LLMs Encode Harmfulness and Refusal Separately*. arXiv:2507.11878 (fetched) | open instruct LLMs incl. Llama family (exact list unverified) | Harmfulness direction is distinct from refusal direction; jailbreaks can suppress refusal without flipping the internal harmfulness belief | Probing + steering along each direction; finetuning robustness test; "Latent Guard" | **Causal** (steering interventions) | Medium-high on the *dissociation* theme — semantic/harm interpretation vs refusal behavior | They dissociate harmfulness-belief from refusal; we dissociate *in-context-installed concept identity* from refusal, and rescue refusal by restoring the query span |
| Wang, Li, Dai, Chen, Zhou, Meng, Zhou, Sun. *Label Words are Anchors: An Information Flow Perspective for Understanding In-Context Learning*. EMNLP 2023; arXiv:2305.14160 | GPT2-XL, GPT-J (unverified exact set) | Demonstration information aggregates into label-word positions in shallow layers, then is read by the final position in deep layers | **Attention blocking / isolation** between demo and query positions, layer-banded | **Causal** | Medium-high on *method*: this is the canonical "block demo->query attention in a layer band" experiment | Ours blocks the *query codeword row* specifically, for a semantic remapping (not a label), and reads out installed meaning concept-free, then rescues behavior |
| Geva, Bastings, Filippova, Globerson. *Dissecting Recall of Factual Associations in Auto-Regressive Language Models*. EMNLP 2023 (arXiv id unverified) | GPT-2, GPT-J (unverified) | Attribute extraction from subject positions | **Attention knockout** (block final position from attending to subject positions, per layer band) | **Causal** | Medium on *method* — origin of the attention-knockout tool we use | Application to in-context installed semantics rather than parametric facts; plus the rescue arm |
| Meng, Bau, Andonian, Belinkov. *Locating and Editing Factual Associations in GPT* (ROME). NeurIPS 2022; arXiv:2202.05262 | GPT-2 XL, GPT-J | Causal tracing of factual recall | Corrupt-then-restore causal mediation (activation patching) | **Causal** | Medium on *method* — our restore arm is a corrupt-then-restore design | Corruption is an attention knockout on a semantic *installation* edge; restored state is read out behaviorally as refusal, not as a fact token |
| Geiger, Wu, Potts, Icard, Goodman. *Finding Alignments Between Interpretable Causal Variables and Distributed Neural Representations* (DAS). CLeaR 2024 (PMLR v236); with arXiv:2303.02536 | small LMs / Alpaca in follow-ups | High-level causal variable aligned to a rotated low-dimensional subspace | Distributed interchange interventions on a learned subspace | **Causal** | Medium-high on *method* — the standard way to license a "subspace causally mediates X" claim | The variable we align is "installed meaning of the codeword under Doublespeak", which to our knowledge has not been posed as a DAS-style causal variable |
| Wu, Geiger, Icard, Potts, Goodman. *Interpretability at Scale: Identifying Causal Mechanisms in Alpaca* (Boundless DAS). arXiv:2305.08809 | Alpaca-7B | Scaling DAS to a 7B instruct model | Boundless distributed interchange interventions | **Causal** | Medium — feasibility precedent for subspace mediation at our scale | Domain (safety / in-context remapping) is new |
| Todd, Li, Sharma, Mueller, Wallace, Bau. *Function Vectors in Large Language Models*. arXiv:2310.15213 (ICLR 2024) | GPT-J, Llama-2 family (unverified exact) | A compact vector transported by a few attention heads encodes the demonstrated *task* | Add the FV into the residual stream at a chosen layer | **Causal** | Medium — closest ICL analogue of "the demos install something you can move around" | FVs encode a *task/function*; we target an installed *lexical-semantic identity* for one token, and its downstream safety consequence |
| Hendel, Geva, Globerson. *In-Context Learning Creates Task Vectors*. arXiv:2310.15916 (EMNLP 2023 Findings) | several open LMs (unverified) | Demos compressed into a task vector at the last demo position | Patch the task vector into a zero-shot run | **Causal** | Medium | as above |
| Hojel et al. (authors unverified). *In-Context Learning Operates as Concept Subspace Learning*. arXiv:2605.18830 | unverified | ICL vectors interpreted as concept subspaces; "Concept Causal Effect" by patching only a candidate concept subspace from clean runs | Subspace-restricted patching | **Causal** (per abstract; unverified) | Medium-high on *method* — closest to our "patch only the installation subspace" arm | Whether their setting includes safety / remapping is unverified; our codeword-identity variable and refusal readout appear distinct |
| *How Few-Shot Examples Add Up: A Causal Decomposition of Function Vectors in In-Context Learning*. arXiv:2605.16591 (authors unverified) | unverified | Per-demonstration contributions to the FV | Causal mediation over demonstrations | Causal (unverified) | Medium — the demo->installed-vector edge, decomposed | Our remapping content and refusal endpoint |
| Wu, Wang, Zeng, Ye, Xiao, Shang, Sun, Zheng et al. (author list unverified). *Retrieval Head Mechanistically Explains Long-Context Factuality*. arXiv:2404.15574 | Llama, Mistral, Qwen families (unverified) | A sparse set of copy-paste "retrieval heads" move context tokens to the output | Head ablation | **Causal** | Low-medium — the demo->query retrieval channel our knockout severs is plausibly carried by such heads, but they study copying, not semantic installation | Our knockout is edge-level (query codeword row -> demo block) and layer-banded, not head-identity-based; and we care about non-copy semantics |
| Olsson et al. *In-context Learning and Induction Heads* (Anthropic, 2022; Transformer Circuits) | small attention-only + larger models | Induction heads implement prefix-matching/copying ICL | Head ablation / circuit analysis | **Causal** | Low-medium — the default mechanism story for ICL, but a copying story | Our effect is explicitly *non-copy* semantic installation |
| Crabbé et al. / *Induction Heads as an Essential Mechanism for Pattern Matching in In-context Learning*. arXiv:2407.07011 (authors unverified) | Llama-3, InternLM (unverified) | Induction heads necessary for abstract pattern matching ICL | Head ablation | **Causal** | Low-medium | as above |
| Zou et al. *Representation Engineering: A Top-Down Approach to AI Transparency*. arXiv:2310.01405 (id unverified; repo andyzoujm/representation-engineering) | Llama-2 family and others | Reading/controlling high-level concepts (incl. harmlessness) via linear directions | Reading vectors, contrast vectors, LoRRA | **Causal** (control experiments) | Low-medium — supplies the "concepts are linear and steerable" background | Our subspace is discovered from an installation readout, not from a labelled concept contrast |
| Ben-Tov, Geva, Sharif. *Universal Jailbreak Suffixes Are Strong Attention Hijackers*. arXiv:2506.12880 (fetched) | open chat LLMs (list unverified) | GCG suffixes hijack contextualization of the chat-template tokens; universality tracks hijacking strength | Attention-flow analysis + surgical attention-side mitigation | Mixed: analysis correlational, mitigation interventional | Medium — nearest "attention-mediated hijacking" framing, but for optimized suffixes, not semantic remapping | Semantic-remapping channel, installation readout, and rescue |
| Ghandeharioun, Caciularu, Pearce, Dixon, Geva. *Patchscopes: A Unifying Framework for Inspecting Hidden Representations of Language Models*. ICML 2024 (arXiv:2401.06102, id unverified) | GPT-J, Llama-2, Vicuna (unverified) | Decode what a hidden state "means" by patching it into a probe prompt | Patching-for-inspection | Read-out tool (used descriptively) | Medium on *method* — our concept-free one-word readout is in this family, and it is the tool Yona et al. use | Our readout is *concept-free by construction* (the probe never names the harmful concept), used as a graded installation metric that an intervention is scored against |
| *There Is More to Refusal in Large Language Models than a Single Direction*. arXiv:2602.02132 (authors unverified) | unverified | Refusal decomposes into harm-detection + refusal-execution components | unverified | unverified | Low-medium — cautions against a 1-D refusal mediator | Reinforces that our mediator claim must be subspace-level, not single-direction |
| *The Geometry of Refusal in Large Language Models* (concept cones). arXiv:2502.17420 (authors unverified) | unverified | Multiple independent refusal-mediating directions forming cones | Ablation/steering (unverified) | Causal (unverified) | Low-medium | as above |
| *Minimal, Local, Causal Explanations for Jailbreak Success in Large Language Models*. arXiv:2605.00123 (authors unverified) | unverified | Minimal local causal explanations of jailbreak success | Patching/ablation (unverified) | Causal (unverified) | Medium if it covers ICL attacks — **flagged as the highest-priority unverified row to read in full** | unknown until read |
| Patel, Bhattamishra, Reddy, Bahdanau. *MAGNIFICo: Evaluating the In-Context Learning Ability of LLMs to Generalize to Novel Interpretations*. EMNLP 2023; arXiv:2310.11634 (fetched) | GPT-3.5/4 + open LMs (unverified exact set) | LLMs acquiring *novel interpretations* of expressions from context (benign setting) | None (evaluation benchmark); reports semantic predispositions and recency bias | **Correlational** | Medium on *phenomenon* — this is benign in-context word redefinition, the non-adversarial twin of our setting | No internals at all, and no safety coupling |

## 3. Closest prior work

**Yona, Sarid, Karasik and Gandelsman, *In-Context Representation Hijacking* (arXiv:2512.03771, ACL 2026).** This is our attack, published. They introduce "Doublespeak" by name: replace a harmful keyword with a benign token across in-context examples, and the benign token's internal representation drifts toward the harmful concept over depth, so "How to build a carrot?" is internally read as the disallowed request. They also articulate the layer story we build on — the refusal direction operates early-to-middle (they point at ~L12 on Llama-3-8B-Instruct), while the semantic overwrite completes later, a time-of-check/time-of-use gap. We must treat the *phenomenon*, the *name*, the *representation-convergence claim*, and the *layer-ordering argument* as theirs, not ours.

Crucially, though, their evidence is **descriptive**. Section 3.2 lists exactly two tools: logit lens (which they themselves call noisy and note fails on Llama-3.1-8B-Instruct, their Appendix H) and Patchscopes. Patchscopes patches a hidden state *into an interpretation probe* — it reads out what a state means; it does not remove, damage, or restore anything in the attacked forward pass. There is no attention knockout, no ablation, no steering, no subspace intervention, and no experiment in which a behavioral outcome (refusal vs compliance) is moved by an internal manipulation. The paper explicitly defers mitigation ("our work focuses on the attack surface and does not yet evaluate specific mitigation strategies"). So the arrow `demonstrations -> installed representation` is *observed* by them and `installed representation -> refusal behavior` is *inferred* from layer ordering, not tested.

**Wang et al., *Label Words are Anchors* (EMNLP 2023).** Methodologically this is the nearest neighbour to our knockout arm. They block attention between demonstration positions and the query/final position in specified layer bands and show ICL performance collapses, establishing a shallow-aggregation-then-deep-readout information flow. The structural analogy is close enough that our L6-14 knockout should be presented as *this technique applied to semantic remapping*, not as a new technique. The differences that matter: their target is label-word aggregation for classification; ours is the installation of a lexical identity onto a codeword, measured by a concept-free readout rather than by task accuracy; and they run no behavioral-rescue arm.

**Geva et al.'s attention knockout and Meng et al.'s causal tracing.** These supply the two halves of our design as generic tools: knock out an information-flow edge over a layer band (Geva), and corrupt-then-restore a residual state to see which restoration recovers the behavior (Meng/ROME). Our contribution cannot be the tools. It has to be the *variable* they are applied to and the *endpoint* they are scored against — an in-context-installed concept identity, scored by downstream refusal.

**Arditi et al. (NeurIPS 2024) and Zhao et al. (arXiv:2507.11878).** Arditi et al. establish the template for a legitimate low-dimensional mediation claim in exactly our safety domain: find a direction, show necessity by ablation and sufficiency by addition. Zhao et al. then break "safety" into a harmfulness representation and a refusal representation and show, with steering, that these dissociate — jailbreaks can suppress refusal while the model's internal harmfulness belief stands. That dissociation result is adjacent to, but not the same as, ours: theirs is *belief about harm vs the act of refusing*; ours is *what the model thinks the codeword denotes vs whether it refuses*, with the additional structure that the denotation was installed by demonstrations in the same context. Follow-ups (arXiv:2602.02132, arXiv:2502.17420, both unverified) warn that a single refusal direction is an oversimplification, which argues for framing our mediator as a subspace and for reporting how much variance/behavior it does *not* capture.

**The function/task-vector line (Todd et al. 2310.15213; Hendel et al. 2310.15916; and the unverified concept-subspace work arXiv:2605.18830).** This line already owns the claim "demonstrations compress into a low-dimensional object that can be causally moved into another forward pass", and arXiv:2605.18830 appears to already own "patch only a candidate concept subspace from clean runs and measure the causal effect". If that paper is as described, our subspace arm is a *domain transfer* of an existing causal method, and should be written that way. Verifying it in full is the single highest-value follow-up before we write our methods section.

## 4. What is already done and we must not claim as novel

1. **The Doublespeak attack itself, its name, and its ASR characterisation.** Yona et al. (arXiv:2512.03771, ACL 2026). Also older, cruder codeword-mapping jailbreaks: word-substitution cipher (arXiv:2402.10601) and WordGame (arXiv:2405.14023).
2. **The observation that the benign codeword's representation converges to the harmful concept across layers**, and that this is progressive/depth-ordered. Yona et al.
3. **The time-of-check/time-of-use argument** that refusal machinery reads an early-to-middle layer state while the semantic overwrite completes later. Yona et al.
4. **Reading out "what does this hidden state mean" by patching it into a probe prompt.** Patchscopes (Ghandeharioun et al.), and used for Doublespeak already by Yona et al.
5. **Attention knockout / demo-to-query attention blocking over layer bands as a causal ICL tool.** Geva et al. 2023; Wang et al. EMNLP 2023.
6. **Corrupt-then-restore activation patching / causal mediation.** Vig et al. 2020; Geiger et al. 2021; Meng et al. 2022.
7. **Refusal as a low-dimensional, causally manipulable feature; ablation-and-addition as the necessity/sufficiency template.** Arditi et al. 2024; Zou et al. RepE.
8. **Harm-representation vs refusal-behavior dissociation, demonstrated causally.** Zhao et al. arXiv:2507.11878.
9. **Subspace-level causal mediation methodology (DAS / Boundless DAS / interchange interventions).** Geiger et al.; Wu et al. arXiv:2305.08809.
10. **Demonstrations compressing into a causally transplantable low-dimensional object in ICL**, and subspace-restricted patching of a concept in ICL. Todd et al.; Hendel et al.; arXiv:2605.18830 (unverified).
11. **In-context acquisition of novel word interpretations as a phenomenon.** MAGNIFICo, EMNLP 2023.
12. **Attention-mediated hijacking as a jailbreak framing.** Ben-Tov, Geva, Sharif, arXiv:2506.12880.

## 5. What appears genuinely novel in our design

Stated conservatively; each item carries the caveat that the searches in §6 are not exhaustive and that three of the nearest neighbours were read at abstract/section level only.

1. **Answer to the key question: no — we did not find any work that closes the chain `demonstrations -> installed semantic representation -> causal query-side rescue` for Doublespeak or for in-context semantic remapping.** The one paper that owns the phenomenon (Yona et al., arXiv:2512.03771 / ACL 2026) runs only logit lens and Patchscopes, both read-out tools, and explicitly leaves mitigation and intervention to future work. Nothing else surfaced that installs a codeword meaning via demonstrations and then intervenes causally on the query side. *Confidence: moderate-to-high on the Doublespeak-specific claim (we fetched the paper's HTML and checked its analysis section); lower on the general claim, because non-archival posts and 2026 preprints were not exhaustively checked, and arXiv:2605.00123 ("Minimal, Local, Causal Explanations for Jailbreak Success") was not read in full.*
2. **Causal establishment of the demo->query-codeword attention edge as the installation channel**, localised to a layer band (L6-14 on Llama-3.1-8B-Instruct), with installation measured by a concept-free readout rather than by task accuracy. The technique is Geva/Wang; its application to semantic installation, and the fact that installation is *graded* and knocks down under it, appears new. *Uncertainty: someone may have run demo-blocking on an ICL jailbreak without framing it as semantic installation.*
3. **The rescue direction of the experiment.** Restoring the *clean* query-span residual under a *live* knockout and recovering downstream refusal is, as far as these searches show, unattested for this attack. Generic "restore the harm direction and refusal partially re-engages" results exist in the refusal literature (see the search-snippet claims under arXiv:2607.14147 / arXiv:2608.15772, both unverified), so the *idea* of behavioral rescue by restoration is not new — what appears new is rescuing refusal by restoring the representation of an **in-context-installed denotation**, i.e. attacking the attack at the semantics rather than at the refusal feature.
4. **A concept-free one-word installation readout used as a quantitative, intervention-scorable dependent variable.** Patchscopes-family read-out is prior art; the specific construction where the probe never names the harmful concept (so the metric cannot be contaminated by the concept being present in the probe) and the metric is then used as the outcome of a causal manipulation is the piece we should defend. *Uncertainty: this is a design detail, and reviewers may reasonably call it a Patchscopes variant.*
5. **A low-dimensional installation-predictive subspace as the claimed mediator between the demo block and refusal behavior.** This is the most contestable novelty claim. DAS and concept-subspace patching already exist as methods; refusal subspaces already exist as objects. The genuinely new object would be a subspace defined by *predicting installation* that then *carries the behavioral effect* — a two-endpoint claim (representation readout AND refusal) that neither the refusal literature (which stops at refusal) nor the ICL-vector literature (which stops at task performance) makes. **We should not claim the method as novel, only the mediator and the two-endpoint result — and only if the subspace passes both necessity and sufficiency, given arXiv:2602.02132 and arXiv:2502.17420 caution that low-rank mediation claims in refusal have been overstated before.**
6. **Model-level note:** Yona et al. report logit lens *failing* on Llama-3.1-8B-Instruct (their Appendix H) — the model we work on. If our readout works where their tool did not, that is a small methodological contribution worth stating plainly, and it is also a reason our numbers may not line up with theirs.

**Recommended verification before we write any novelty claim:** read in full (a) arXiv:2512.03771 appendices, especially H and I; (b) arXiv:2605.00123; (c) arXiv:2605.18830. Any one of these could narrow items 2, 3 or 5.

## 6. Searches run and their result counts

All via WebSearch unless noted. "Results" = distinct links returned in the result block.

| # | Query | Results | Useful hits |
|---|---|---|---|
| 1 | Doublespeak jailbreak LLM codeword substitution in-context demonstrations arXiv | 9 | arXiv:2512.03771 (the paper), arXiv:2310.06387 |
| 2 | in-context word redefinition language model mechanistic interpretability new word meaning | 10 | 0 direct; surveys only |
| 3 | attention knockout mechanistic interpretability in-context learning demonstration attention blocking causal | 9 | Geva et al. 2023 knockout; arXiv:2407.07011; arXiv:2402.13055 |
| 4 | refusal direction single direction mediates refusal Arditi 2024 arXiv | 10 | arXiv:2406.11717 (+NeurIPS PDF), arXiv:2602.02132, arXiv:2502.17420 |
| 5 | distributed alignment search causal subspace interventions interchange intervention Geiger arXiv | 10 | arXiv:2301.04709, arXiv:2303.02536, arXiv:2305.08809, PMLR v236 geiger24a |
| 6 | task vectors function vectors in-context learning compressed representation causal patching arXiv | 8 | arXiv:2310.15213, arXiv:2310.15916, arXiv:2605.18830, arXiv:2605.16591, arXiv:2502.05390, arXiv:2506.09048 |
| 7 | how jailbreaks work internally activation patching refusal suppression mechanistic analysis LLM 2024 | 7 | arXiv:2605.00123, arXiv:2603.08234, arXiv:2604.18510 (all unverified) |
| 8 | harmfulness representation versus refusal behavior dissociation LLM model knows harmful but complies probe | 9 | arXiv:2507.11878 (key), arXiv:2606.08044 |
| 9 | label words are anchors information flow in-context learning attention blocking Wang 2023 arXiv | 10 | arXiv:2305.14160 / EMNLP 2023 (key) |
| 10 | word substitution cipher jailbreak LLM word game encode harmful word benign synonym attack | 8 | arXiv:2402.10601, arXiv:2405.14023 |
| 11 | causal mediation analysis locating factual associations ROME Meng activation patching residual stream | 10 | arXiv:2202.05262; Vig 2020 / Geiger 2021 lineage |
| 12 | LLM learn novel word definition in context probing internal representation nonce word semantics layers | 10 | arXiv:2310.11634 (MAGNIFICo) |
| 13 | retrieval heads in-context retrieval attention heads copying long context Wu 2024 arXiv | 10 | arXiv:2404.15574, arXiv:2506.09944 |
| 14 | representation engineering top-down transparency Zou reading vector control LLM refusal | 9 | RepE (Zou et al.); arXiv:2512.03771 resurfaced |
| 15 | restoring clean activations restores refusal jailbreak patching clean residual stream rescue safety behavior | 10 | arXiv:2607.14147, arXiv:2608.15772, arXiv:2506.12880, arXiv:2509.09708 (all unverified) |
| 16 | low-rank subspace causally mediates safety refusal distributed alignment search jailbreak subspace intervention | 10 | arXiv:2606.14388, arXiv:2508.20766, arXiv:2605.00123 (unverified) |
| 17 | "In-Context Representation Hijacking" Doublespeak follow-up causal attention knockout query token | 10 | confirmed ACL 2026 Long 768 + OpenReview; no causal follow-up found |

**Pages fetched and read (6):** arxiv.org/abs/2512.03771; arxiv.org/html/2512.03771v1 (interpretability sections); arxiv.org/abs/2507.11878; arxiv.org/abs/2310.11634; arxiv.org/abs/2506.12880; (plus search-result verification of aclanthology.org/2026.acl-long.768).

**Total: 17 searches, 5 primary-page fetches, ~170 result links inspected.**

---

# ADDENDUM — 2026-09-17: gap-fill pass on plan §12, with a direct answer to the two framing questions

**Date:** 2026-09-17
**Why this pass.** The 2026-09-15 review above predates the sprint's current results. Two of those
results now govern how everything may be worded: (i) a **rank-1 / low-rank installation axis recovers
only a few percent** of what the **whole state** recovers, and (ii) a **per-position causal map**
puts **46.6 % of the whole-state effect on the codeword's own query row**. This pass asks the
literature specifically whether either of those is (a) already published, (b) already explained away
by a known artefact, or (c) already refuted as a methodology. It also re-checks §12's topic list for
coverage.

**Method.** 22 WebSearch queries and 15 direct arXiv page fetches (listed in §A7). Every row in the
tables below was checked by fetching the paper's own arXiv/proceedings page: title, authors, date and
abstract were read from the source, not from a search snippet. Rows that could not be verified that
way are **not** in the tables — they are in §A6 (UNVERIFIED) and must not be cited.

**Same coverage limits as §1 apply**, and one more: several judgements below ("they do not test
rank-1", "they patch at the final position") come from the arXiv **HTML** rendering of the paper
(abstract + numbered sections + appendix headings), not from an end-to-end PDF read. Each such
judgement is marked *(html-read)*.

---

## A1. Coverage assessment against the §12 topic list

| §12 topic | State before this pass | State after |
|---|---|---|
| Doublespeak / semantic-remapping jailbreaks | **Covered** (2512.03771; 2402.10601; 2405.14023) | unchanged; no new remapping attack surfaced |
| In-context concept remapping | **Thin** — only MAGNIFICo, no internals | **Filled**: 2501.00070 (ICLR 2025), 2602.04212, 2412.12276 |
| Activation patching of semantic representations | Covered on *method*, **thin on pitfalls** | **Filled**: 2309.16042, 2404.15255, 2311.17030, 2606.27510 |
| Causal mediation in transformers | Covered (ROME, Vig, Geiger) | **Deepened**: 2606.27510 re-derives the patching estimand and shows NIE ≠ component effect |
| Refusal circuits | Covered (2406.11717) + two *unverified* rows | **2502.17420 now VERIFIED** (ICML 2025); + 2609.14759 |
| Semantic interpretation vs refusal | Covered (2507.11878) | **Deepened**: 2609.14759, 2606.28153 |
| Demonstration retrieval circuits | **Thin** — retrieval heads only | **Filled**: 2505.15807 (NeurIPS 2025), Sia et al. (NeurIPS 2024) |
| Induction / retrieval heads | Covered | unchanged |
| Representation hijacking | Covered (2512.03771; 2506.12880) | unchanged |
| Activation-based jailbreak mechanisms | Covered, one key row *unverified* | **2605.00123 now VERIFIED** (COLM 2026) + 2606.28153 |
| Causal subspace interventions | Covered on *method*, **absent on negatives/controls** | **Filled — this was the biggest gap**: 2507.08802, 2501.17148, 2504.13151, 2407.12404, 2307.15771, 2402.15390, 2605.16362 |

**Still uncovered after this pass** — see §A5.

---

## A2. Table of added works — subspace mediation, controls, and published negatives (bears on 3a)

Same similarity yardstick as §2.

| Citation | Model(s) | Phenomenon | Intervention | Causal / Correlational | Similarity | What remains novel for us |
|---|---|---|---|---|---|---|
| Makelov, Lange, Nanda. *Is This the Subspace You Are Looking for? An Interpretability Illusion for Subspace Activation Patching*. arXiv:2311.17030 (28 Nov 2023); NeurIPS 2023 Attributing-Model-Behavior workshop; **ICLR 2024 poster**. (fetched) | GPT-2 (IOI), factual-recall setting | A subspace patch can produce the *intended* end-to-end behavioural change **while being causally disconnected from the output**, by activating a *dormant parallel pathway* | Subspace activation patching + counter-analysis | **Causal** (it is a critique *of* causal claims) | **HIGH on methodology.** This is the canonical published statement that a subspace-patching **positive** need not mean the feature lives in that subspace; they tie it to rank-1 fact editing and to the known fact-editing / fact-localisation inconsistency | Directional relevance is inverted for us: it disciplines *positives*. Our load-bearing subspace result is a **negative**, which this paper's illusion cannot manufacture — worth stating explicitly, because it is one of the few respects in which a negative is *safer* than a positive |
| Sutter, Minder, Hofmann, Pimentel. *The Non-Linear Representation Dilemma: Is Causal Abstraction Enough for Mechanistic Interpretability?* arXiv:2507.08802 (11 Jul 2025); **NeurIPS 2025 Spotlight**. (fetched) | LMs incl. randomly-initialised controls | If the alignment map is not capacity-constrained, **any network can be mapped to any algorithm**; they obtain **100 % interchange-intervention accuracy on randomly initialised models** for algorithms those models cannot solve | Interchange interventions under alignment maps of varying expressivity | **Causal** | **HIGH on methodology — this is the paper that licenses our control family.** It is the published statement that **the expressivity/capacity of the map, not the feature, can determine whether an intervention "succeeds"** | Nothing of ours is novel here; it is the *justification* for fit-capacity-matched and rank-matched controls. Cite it as the reason the control family exists, not as a result |
| Vaidyanathan, Arbour, Mueller, Niekum, Jensen. *The Curse of Multiple Mediators: Hidden Interaction Effects in Activation Patching*. arXiv:2606.27510 (25 Jun 2026). (fetched) | GPT-2 (IOI circuit) | The activation-patching estimand (natural indirect effect) **also contains interaction effects (INT)** measuring how a component's effect depends on other components' states; components whose importance is conditional are *"either invisible or artificially inflated"*; INT variance explains documented faithfulness instability. They prove **INT scales with the distance between clean and patched activations** | Re-derivation of the estimand + IOI demonstrations | **Causal / theoretical** | **HIGH — directly bears on our 46.6 % vs ~1–4 % gap.** A whole-row restore is a large clean-vs-patched distance (large INT); a rank-1 write is a small one (small INT). Some of the gap between the two may be interaction effect, not "the direction carries less information" | Our setting (in-context installed denotation, refusal endpoint) is not theirs; but this is now a **required caveat**, not an optional one, on any statement of the form "the axis carries only k % of what the state carries" |
| McGrath, Rahtz, Kramar, Mikulik, Legg. *The Hydra Effect: Emergent Self-repair in Language Model Computations*. arXiv:2307.15771 (Jul 2023). (search-verified; abstract read) | PaLM-family LMs | Ablating one attention layer causes **another layer to compensate**; late MLPs counterbalance. At mid layers the two together **restore ≈70 % of the logit reduction** | Layer / component ablation | **Causal** | Medium-high — a published mechanism by which **single-component interventions under-read** relative to whole-state ones | Not about subspaces or ICL; supplies a second, independent reason a rank-1 write can under-recover without the direction being wrong |
| Rushing, Nanda. *Explorations of Self-Repair in Language Models*. arXiv:2402.15390 (Feb 2024). (search-verified; html abstract read) | GPT-2 family / small LMs | Self-repair is partial and heterogeneous; **LayerNorm rescaling alone accounts for a substantial fraction** of apparent self-repair (reported up to ~30 % of the ablated effect) | Component ablation + decomposition | **Causal** | Medium — the "mechanical" half of the Hydra story | Same as above; also a warning that norm changes at the edited site are themselves an effect channel, which is why our controls must be **norm-matched** and not merely random |
| Tan, Chanin et al. *Analysing the Generalisation and Reliability of Steering Vectors*. arXiv:2407.12404; **NeurIPS 2024**. (search-verified; proceedings PDF located) | open chat LMs | Steerability is **highly variable across inputs**; spurious biases contribute; for several concepts steering is brittle to reasonable prompt changes; on several datasets steering produces the **opposite** behaviour for ~50 % of inputs | Steering-vector addition | **Causal** | Medium-high — the closest published statement that a single direction's causal effect is **unreliable and input-dependent** | Our concentration finding (top 5 of 23 held-out domains carrying most of the axis effect; per-domain sd 6–10× controls') is **the same shape of result** in a new domain. This is prior art for "a direction's effect can be real and still be concentrated and unreliable" — we should cite it rather than present concentration as surprising |
| Wu, Arora, Geiger, Wang, Huang, Jurafsky, Manning, Potts. *AxBench: Steering LLMs? Even Simple Baselines Outperform Sparse Autoencoders*. arXiv:2501.17148; **ICML 2025**. (search-verified; PMLR v267 wu25a located) | Gemma-2-2B, Gemma-2-9B | On steering, **prompting beats all representation methods**, then finetuning; SAEs lag on both steering and concept detection; difference-in-means is the best representation-based detector | Steering + concept detection benchmark | **Causal** (steering evaluated behaviourally) | Medium — a large published negative on **low-dimensional feature-level control** | Not our task or endpoint. Useful as the general prior that a sparse/low-dimensional feature underperforming a cruder full-state manipulation is a **common, publishable outcome**, not an anomaly |
| Mueller, Geiger, Wiegreffe, Arad, Arcuschin, … Bau, Belinkov. *MIB: A Mechanistic Interpretability Benchmark*. arXiv:2504.13151; **ICML 2025**. (fetched) | 5 models, 4 tasks | Two tracks: circuit localisation and **causal variable localisation**. Finding: *"the supervised DAS method performs best, while SAE features are not better than neurons, i.e., non-featurized hidden vectors"* | Benchmark over DAS / SAE / probe featurisations | **Causal** | Medium-high — a **published, benchmarked negative on low-dimensional featurisations** for causal variable localisation | It is a benchmark, not our phenomenon. But it is the cleanest citation for "a learned low-dimensional featurisation failing to beat the raw hidden vector is an outcome the field has measured and reports" |
| Robertson, Zhu, Vikalo, Wang. *When Is Rank-1 Steering Cheap? Geometry, Granularity, and Budgeted Search*. arXiv:2605.16362 (9 May 2026; v2 20 May 2026). (fetched) | three model families (names not in abstract) | Argues variability in steering effectiveness is **search difficulty, not absence of a rank-1 direction**: *"a useful rank-1 intervention often exists, but finding it can be expensive"*; introduces a concept-granularity metric and the GRACE search framework | Budgeted search over rank-1 directions | **Causal** | **HIGH as a threat to our negative.** This is the paper a reviewer will raise against any rank-1 null | Nothing of ours is novel here. **It imposes a duty**: our rank-1 negative must be stated as a negative *for the axis we fit, by the fitting procedure we used, at the layer and position we tested* — never as "no rank-1 direction mediates installation" |
| Tang, Jiang, Karray, Hu. *In-Context Learning Operates as Concept Subspace Learning*. arXiv:2605.18830 (12 May 2026). (fetched: abs + html) | **Llama-3-8B**, CounterFact-derived multi-relation prompts | ICL concepts occupy a low-dimensional subspace of the residual stream that **mediates** ICL behaviour | Subspace-restricted patching, with controls | **Causal** | **HIGH — and the numbers matter more than the headline**; see §A3 | Their positive is at **rank 73**, at the **final/query position**, at **layer 30**. See §A3 for what that does and does not do to our claim |

### Verified detail from arXiv:2605.18830 *(html-read, layer/rank/control figures read from the paper's own HTML)*

This is the single most consequential set of numbers in this addendum, so it is recorded in full.

| Arm | Dimensionality | Result |
|---|---|---|
| Learned concept subspace `U_learned` | **73 of 4096** (rank chosen as the minimal *r* with ≥98 % of cross-covariance singular-value energy; Appendix B.2 reports 61–74 across estimation-set sizes) | **78.8 %** of the clean−corrupted accuracy gap; 60.5 % acc (baseline 40.0, clean 66.0) |
| **Complementary** subspace `I − P` | 4023 | **0.0 %** recovery; 40.0 % acc |
| **Random orthogonal**, rank-matched | 73 | override success **2.3 %** (baseline 2.5 %) |
| **Cross-task**, rank-matched | 73 | override success **3.3 %** (baseline 2.5 %) |
| **Full-space** patching | 4096 | **98.1 %** recovery; 65.5 % acc |

Layer: **ℓ\* = 30** of Llama-3-8B, selected from a layerwise sweep (layers 0–14 near-zero recovery;
15–20 emergence; 21+ steep rise). Position: *"residual stream activations at the final sequence
position (the query token)"* — i.e. the **generation position**, used for both estimation and
patching. **No rank-1 or very-low-rank variant is tested** *(html-read; the singular-value spectrum
is shown as sharply concentrated at layer 30, but no rank-1 arm is run)*.

---

## A3. Direct answer to question 3(a)

> *Is there prior work showing a LOW-DIMENSIONAL / rank-1 direction FAILS to mediate while the full
> state does — published negatives on subspace mediation, or work on why 'dose/dimensionality'
> rather than 'direction' explains patching recoveries? Anything on rank-matched or norm-matched
> control subspaces as a methodology?*

**Short answer, in three parts.**

**(i) A published negative of our exact shape — "rank-1 fails, full state succeeds, same task, same
layer, same position" — did not surface.** I searched for it directly (§A7 queries 3, 19) and it did
not appear. That is a *gap in these searches*, not a proof of absence, and the §1 coverage limits
apply.

**(ii) But the nearest published positive is at rank ≈73, not rank 1 — and this is the single most
important fact in this addendum for how our result must be worded.** arXiv:2605.18830's
concept-subspace positive uses a **73-dimensional** subspace of a 4096-dimensional residual stream,
with the rank chosen by a 98 %-variance criterion that would select ~61–74 dimensions, not 1. They
never test rank 1.

The consequence is direct and it cuts against an over-strong framing of our own result. **A rank-1
null is not a contradiction of a rank-73 positive.** The two are measurements at ranks separated by a
factor of ~70, on different tasks (CounterFact relations vs Doublespeak remapping), at different
layers (their 30 vs our 18/20), at different positions (their final/query generation position vs our
codeword row), and with different endpoints (their next-token accuracy vs our installation readout
and refusal). Wording of the form *"we dissociate from a published positive"* should therefore be
qualified to something like:

> *"arXiv:2605.18830 reports a causal ICL concept subspace at rank ≈73 of 4096, at the final query
> position of layer 30 of Llama-3-8B. Our low-rank axis, fit at a much lower rank by a different
> criterion, at a different layer and a different position, does not reproduce that scale of
> recovery. Whether the difference is the rank, the layer, the position, the task, or the readout is
> not resolved by our experiments."*

That is a defensible sentence. *"The low-dimensional mediation result does not replicate"* is not.

**(iii) "Dose/dimensionality rather than direction" — there IS a published treatment, and it points
both ways.**

*Supporting a dimensionality/capacity account:*
- **Sutter et al., arXiv:2507.08802 (NeurIPS 2025 Spotlight)** is the strongest citation. They prove
  that without a capacity constraint on the alignment map, *any network maps to any algorithm*, and
  demonstrate **100 % interchange-intervention accuracy on randomly initialised models**. This is
  the published statement that **intervention success can be a property of the map's expressivity
  rather than of the representation.** It is the direct justification for our fit-capacity-matched
  control family.
- **Vaidyanathan et al., arXiv:2606.27510** proves **INT scales with the distance between clean and
  patched activations**. Whole-row restores move the state far; rank-1 writes move it little.
  Part of a whole-state-vs-axis gap can therefore be interaction effect rather than information
  content. This is now a mandatory caveat on the 46.6 % vs ~1–4 % comparison.
- **McGrath et al., arXiv:2307.15771** and **Rushing & Nanda, arXiv:2402.15390**: self-repair
  restores ~70 % of an ablation's logit effect at mid layers, and LayerNorm rescaling alone accounts
  for up to ~30 %. Both predict that *small, single-component* interventions under-read relative to
  *whole-state* ones, for reasons that have nothing to do with where the feature lives.

*Cutting against a pure dimensionality account:*
- **arXiv:2605.18830's own complement control**: the **4023-dimensional** complementary subspace
  recovers **0.0 %** while the **73-dimensional** learned subspace recovers **78.8 %**. In that
  setting, dimension alone buys nothing — direction/alignment is what carries the effect. So we may
  **not** claim that "dose explains patching recoveries" as a general fact; the honest claim is that
  *dose is a live confound that must be controlled*, which is exactly what our rank- and norm-matched
  families do.
- **Robertson et al., arXiv:2605.16362** argues the opposite of a dimensionality account: rank-1
  directions usually *exist* and the variability is **search cost**. This is the strongest available
  objection to our negative and must be cited as a limitation, not omitted.

**(iv) Rank-matched / norm-matched control subspaces as methodology: PUBLISHED. We may not claim
the method as ours.**
- **arXiv:2605.18830** runs a **rank-matched random-orthogonal** control (73-d, 2.3 % vs 2.5 %
  baseline) and a **rank-matched cross-task** control (73-d, 3.3 %) alongside the complement control.
  That is, precisely, a matched-capacity control family for a subspace-patching claim, already in
  print for ICL.
- **Arditi et al., arXiv:2406.11717** already pairs directional ablation with random-direction
  controls in the refusal domain.
- **Sutter et al., arXiv:2507.08802** supplies the *principled* argument for why such matching is
  required.
- **Makelov et al., arXiv:2311.17030** supplies the failure mode the matching guards against.

⇒ **Our control design is standard practice with a published rationale.** What is *not* obviously
standard, and is the most we should claim methodologically, is the **size and composition** of the
family we run (46 controls: 22 random + 24 fit-capacity-matched shuffled, with a preregistered
exchangeability test before pooling, and a stated attainable p-floor of 1/47) and the fact that the
**shuffled-label controls are fit by the same procedure as the candidate**, so they match fitting
capacity and not merely rank. I did not find that specific construction in these searches, but it is
an increment on published practice, not a new methodology.

---

## A4. Direct answer to question 3(b), and the added works it rests on

> *(b) Is there prior work localising an in-context induced semantic mapping to the QUERY TOKEN ROW
> of the remapped word specifically? And prior work on LAYER vs FEATURE confounds in patching
> studies?*

### A4.1 Added works bearing on token-row localisation and ICL position structure

| Citation | Model(s) | Phenomenon | Intervention | Causal / Correlational | Similarity | What remains novel for us |
|---|---|---|---|---|---|---|
| Kahardipraja et al. *The Atlas of In-Context Learning: How Attention Heads Shape In-Context Retrieval Augmentation*. arXiv:2505.15807; **NeurIPS 2025** (poster 119839; code `pkhdipraja/in-context-atlas`). (search-verified: OpenReview + NeurIPS page + repo) | open LMs (list not verified) | Prompt decomposed into informational components; **in-context heads** that read instructions and retrieve context vs **parametric heads** holding relational knowledge | Attribution-based head identification + **attention-weight modification** + function-vector extraction | **Causal** (weights modified, effect measured) | Medium-high on the *channel* — this is the demo→query retrieval channel our knockout severs, resolved to head identity | Their unit is the **head**; ours is the **edge and the row**. They do not study a remapped word's own position, nor a safety endpoint |
| Sia, Mueller, Duh, et al. *Where does In-context Learning Happen in Large Language Models?* **NeurIPS 2024** (proceedings hash 3979818cdc7bc8dbeec87170c11ee340); earlier as *Where does In-context Translation Happen…*, arXiv:2403.04510. (search-verified: NeurIPS proceedings PDF + poster page) | GPTNeo-2.7B, Bloom-3B, Starcoder2-7B, **Llama-3.1-8B**, **Llama-3.1-8B-Instruct** | A **"task recognition" point**: beyond some layer, attention to the context is no longer needed (e.g. layer 14/32 for MT), giving ~45 % compute savings | **Layer-wise context masking** — mask all attention to context from layer *ℓ* onward | **Causal** | **Medium-high, and newly relevant**: same masking family as our knockout, **on our exact model**, and it is the published precedent for "the demo→query channel stops mattering above some layer" | Theirs masks **all** context, wholesale, from a layer onward, and measures task accuracy. Ours masks **one edge to one row** in a band, and measures an installed denotation and refusal |
| Park, Lee, Lubana, Yang, Okawa, Nishi, Wattenberg, Tanaka. *ICLR: In-Context Learning of Representations*. arXiv:2501.00070 (29 Dec 2024); **ICLR 2025**. (fetched) | open LMs (Llama-family; exact list unverified) | With enough context, a **sudden re-organisation from pretrained semantic representations to in-context ones**; analogised to energy minimisation | Representation analysis across context scale | **Correlational** (observational; no ablation/steering) | **Medium-high on phenomenon** — this is the benign, non-adversarial twin of Doublespeak's "the token's meaning gets overwritten by context", with a context-size threshold | No intervention, no token-row localisation, no safety coupling. Relevant to us as evidence the *phenomenon* generalises beyond jailbreaks, and as a dose/context-size prior |
| Lepori, Linzen, Yuan, Filippova. *Language Models Struggle to Use Representations Learned In-Context*. arXiv:2602.04212 (4 Feb 2026; rev 1 May 2026). (fetched) | open-weights LMs (list unverified) | LLMs **do** induce rich representations of in-context-defined novel semantics but **fail to deploy them** downstream | Next-token evaluation + an "adaptive world modeling" probe task | **Correlational** *(no causal intervention described in the abstract; html not read end-to-end)* | **Medium-high, and it is an argument we must answer.** It is a published dissociation between *installed representation* and *downstream use* — which is structurally what our knockout/rescue asymmetry could be mistaken for | Ours is causal and adversarial; theirs is behavioural and benign. But if our installation readout moves while behaviour does not, **this paper is the prior art for that pattern** and we must cite it rather than present it as new |
| Park, Yang, Lee, Lubana, Tanaka et al. *Emergence of Abstractions: Concept Encoding and Decoding Mechanism for In-Context Learning in Transformers*. arXiv:2412.12276 (later titled *Emergence and Effectiveness of Task Vectors in In-Context Learning: An Encoder-Decoder Perspective*). (search-verified: arXiv abs/html + HF paper page) | Gemma-2 (2B/9B/27B), **Llama-3.1 (8B/70B)** | Coupled emergence of **concept encoding** (latent concepts → separable representations) and **conditional decoding**; explains why task vectors emerge | Representation analysis + task-vector patching | **Mixed** (patching used; much of the analysis representational) | Medium — the encode/decode split is the natural frame for our "installation readout moves, behaviour may not" | Their concept is a task; ours is a lexical denotation with a refusal endpoint |
| Kumar, Ahuja. *Minimal, Local, Causal Explanations for Jailbreak Success in Large Language Models* (**LOCA**). arXiv:2605.00123 (30 Apr 2026; v3 7 Aug 2026); **COLM 2026**. (fetched: abs + html — supersedes the unverified row in §2) | **Llama-3.1-8B-Instruct**, Gemma-2-2B-IT | Minimal set of interpretable intermediate representation changes that **causally induce refusal** on an otherwise-successful jailbreak; ~6 changes on average vs 20+ in prior work | **Directional** edits along SAE concept vectors: *"we subtract the jailbreak's projection onto v and add the original's projection onto v, leaving the orthogonal component unchanged"* | **Causal** | **HIGH on the representation→refusal framing** (as S-036 recorded) — and now with the detail that matters: their edits are **low-dimensional/directional**, at **early-to-mid layers** (Llama 3, 7, 15), and their §4.3 localisation is by **token TYPE** (punctuation vs words; instruction vs post-instruction tokens) | **They do not compare a low-rank edit against a full-state edit** *(html-read)*, and they report **no per-position causal map** — §4.3 is a categorical analysis of which token types get selected, not a ranking over positions. Our whole-state-vs-axis comparison and our per-row position map are not things LOCA does |
| Yin, Han, Li. *Robust Harmful Features Under Jailbreak Attacks: Mechanistic Evidence from Attention Head Specialization in LLMs*. arXiv:2606.28153 (26 Jun 2026). (fetched) | open chat LLMs (list unverified) | Jailbreaks **selectively suppress** components rather than erasing safety features; Adversarially Compromised Heads (early layers) vs Safety-Aligned Heads (mid layers); "Robust Harmful Features" persist under successful attack | **Head ablation** (suppress ACHs / remove SAHs) + token-level attribution | **Causal** | Medium-high on *semantic interpretation vs refusal*; their **token-level attribution finds ACH suppression is driven by attack-TEMPLATE tokens** | Closest published "which tokens drive it" result in the jailbreak setting — and it lands on **template** tokens, not a **remapped content word's own row**. Our codeword-row finding is a different locus |
| Reblitz-Richardson. *Refusal Reads Only a Slice of What the Model Knows: Harm-Keyed Routing and Its Exceptions Across Model Families*. arXiv:2609.14759 (13 Sep 2026). (fetched) | OLMo-3 (primary), Llama, Qwen, GPT-OSS | Refusal runs on a narrow harm-detection channel decoupled from moral comprehension; *"about three-quarters of refusal's causal input lies outside the moral subspace"* | **Nested interchange rank sweep**; single-direction edit | **Causal** (*"The central result is causal and comes from one model, OLMo-3"*) | Medium-high on the interpretation-vs-refusal axis, and note the **rank sweep** methodology — a published precedent for varying rank rather than asserting one | Very recent (4 days before this pass); not on our model family for the causal result; no ICL remapping, no codewords. Treat as a framing neighbour, and as prior art for "sweep the rank" |
| Wollschläger, Elstner, Geisler, Cohen-Addad, Günnemann, Gasteiger. *The Geometry of Refusal in LLMs: Concept Cones and Representational Independence*. arXiv:2502.17420; **ICML 2025** (PMLR v267 wollschlager25a). (search-verified: PMLR + ICML poster + TUM portal — **this upgrades the §2 row from "authors unverified"**) | open chat LLMs | **Multiple independent** refusal directions and multi-dimensional **concept cones**, not a single direction; **orthogonality does not imply independence under intervention**, motivating "representational independence" | Gradient-based representation engineering; ablation/steering | **Causal** | Medium-high — and the orthogonality point is a **methodological warning for us**: our orthogonal-control arm (`KO_ORTH`) must not be described as an *independent* control on the strength of orthogonality alone | Their object is refusal geometry; ours is an installed denotation |

### A4.2 The answer on the QUERY TOKEN ROW of the remapped word

**No prior work surfaced that localises an in-context-induced semantic mapping to the remapped
word's own query token row.** The nearest neighbours, and exactly how each falls short:

1. **arXiv:2605.18830 patches at the query token — but that means the FINAL/generation position**,
   not a content word's row: *"residual stream activations at the final sequence position (the query
   token)"*. This is a vocabulary collision we must be careful about in writing, because "query
   token" in that paper and "query codeword row" in ours denote **different positions**. Any sentence
   of ours using "query token" needs disambiguating.
2. **Wang et al., *Label Words are Anchors* (EMNLP 2023)** localises to **label-word positions inside
   the demonstrations**, not to a position in the query.
3. **Meng et al., ROME (arXiv:2202.05262)** is the closest *methodological* precedent and supplies the
   comparator number: causal tracing puts the decisive effect at the **last subject token**, with an
   average maximum restoration of **19.5 %** over the corrupted run (peaking around layer 15).
   So "one content-word row carries a large share of the restoration effect" is an *established shape
   of result* for **parametric** factual recall. Our 46.6 % is the same shape of claim for an
   **in-context-installed** denotation — which is what is new, not the shape.
4. **Geva et al.'s attention knockout (EMNLP 2023)** blocks the final position from attending to
   **subject positions** — again parametric, again not a remapped word.
5. **LOCA (arXiv:2605.00123)** localises by **token type** (punctuation vs word; instruction vs
   post-instruction) on **our exact model**, with no per-position ranking *(html-read)*.
6. **Yin et al. (arXiv:2606.28153)** localise token-level attribution to **attack-template tokens**.
7. **Sia et al. (NeurIPS 2024)** localise by **layer**, masking the whole context, not by row.

⇒ **Defensible wording for our position-map result:** the *technique* (a per-position causal map from
a corrupt-then-restore design) is ROME/Geva standard and must be presented as such; the *comparator*
is ROME's ~19.5 % at the last subject token for parametric recall; what appears unattested is
applying it to an **in-context-installed denotation** and finding the **codeword's own row** dominant.
State it as "we did not find prior work localising an in-context-installed mapping to the remapped
word's own row", never as "we are the first to".

### A4.3 The answer on LAYER vs FEATURE confounds in patching studies

**Prior work exists on layer as a confound in patching, but I did not find a paper that states our
specific confound** — that comparing two conditions *each selected at its own argmax layer* confounds
condition with layer. The relevant prior art:

| Citation | What it establishes about layer/method confounds |
|---|---|
| **Zhang, Nanda. *Towards Best Practices of Activation Patching in Language Models: Metrics and Methods*. arXiv:2309.16042; ICLR 2024.** (fetched) | The canonical citation. *"Varying these hyperparameters could lead to disparate interpretability results."* Systematically shows metric choice (logit difference favoured; probability discouraged; KL as a supplement) and corruption method (**Symmetric Token Replacement preferred over Gaussian Noising**, which produces out-of-distribution artefacts) change conclusions. Also treats **sliding-window layer patching** and the token-scan vs layer-scan distinction as separate design axes |
| **Heimersheim, Nanda. *How to use and interpret activation patching*. arXiv:2404.15255 (Apr 2024).** (search-verified; PDF located) | Distinguishes **exploratory** patching (sweeps over layers, positions, components, to generate hypotheses) from **confirmatory** patching (verify a specific circuit). Results depend on source/destination prompts, corruption construction, granularity and metric; patching is *"evidence of causal contribution under a specified setup"*, not an algorithm. **This is the citation for why a layer picked by an exploratory sweep must not then be treated as confirmed** |
| **Makelov, Lange, Nanda. arXiv:2311.17030; ICLR 2024.** | Where you patch (which bottleneck) determines whether you get an illusion; they recommend patching at **activation bottlenecks, especially the residual stream** |
| **Vaidyanathan et al. arXiv:2606.27510.** | The estimand itself is contaminated by interaction effects whose magnitude depends on the perturbation distance — a confound that survives any layer choice |
| **arXiv:2605.18830.** | Their own layer sweep (0–14 near-zero, 15–20 emergence, 21+ steep rise, ℓ\*=30) is a worked example of an argmax-selected layer; they use one layer for every arm, which is the design our layer-control experiment is trying to match |

⇒ **The methodological point our sprint's layer-control experiment makes — run both conditions at the
same layer before attributing a dissociation to the condition — is standard scientific practice and
is implied by Zhang & Nanda and by Heimersheim & Nanda, but I did not find it stated as a named
pitfall for cross-condition comparisons in patching.** That makes running the control clearly
correct, and makes claiming the *observation* as a contribution unwise: at most a sentence in
methods, phrased as applying Zhang & Nanda's warning to a two-condition comparison.

---

## A5. §12 topics still uncovered after this pass

1. **Doublespeak-specific follow-ups.** Still none found (search 17 in §6 and search 16 in §A7 both
   came back empty). The attack has one paper.
2. **Non-archival mechanistic jailbreak work** (LessWrong / Alignment Forum / workshop tracks). Still
   not systematically searched — unchanged from §1, and still the most likely place a close
   neighbour hides.
3. **Retrieval/induction heads specifically for non-copy semantic transfer.** Every head-level paper
   found (retrieval heads 2404.15574; induction heads; Atlas 2505.15807) studies **copying or
   task-identification**. Whether a head carries an *installed denotation* that is not a copy is
   still not addressed by anything I found. **This is a real, open, adjacent question** and, per Gate
   C, we should not invent a circuit to fill it.
4. **A citation-graph crawl** (forward citations of 2512.03771, 2605.18830, 2605.00123). Not run.
   This is the highest-value remaining literature action and it is cheap.
5. **Norm-matched control practice stated as a named methodology.** Found in practice
   (2605.18830, 2406.11717) and justified in principle (2507.08802), but no methods paper
   consolidating it surfaced. Minor.
6. **Whether any concurrent work uses a concept-free readout as an intervention-scorable DV.** Still
   nothing found, and still the §5-item-4 claim most exposed to a "this is a Patchscopes variant"
   reviewer response.

---

## A6. UNVERIFIED — surfaced in searches, NOT verified, MUST NOT be cited

These returned as search results only. Titles/ids are copied from result blocks; **no arXiv page was
fetched for any of them** and several may not exist as described. They are recorded so a later pass
does not have to re-find them.

- arXiv:2608.22985 — *What Does Activation Steering Control? Attribution Across Answer Encodings and Output-Sensitive Subspaces*
- arXiv:2605.31183 — *Steering LLMs? Actually, Sparse Autoencoders can outperform simple baselines*
- arXiv:2605.29634 — *Relational Rank Geometry in Transformers: Detecting and Steering Hidden-State Relation Frames*
- arXiv:2603.28744 — *Stop Probing, Start Coding: Why Linear Probes and Sparse Autoencoders Fail at Compositional Generalisation*
- arXiv:2602.09783 — *Why Linear Interpretability Works: Invariant Subspaces as a Result of Architectural Constraints*
- arXiv:2607.01033 — *The Model Organism Lottery: Model Organism Interpretability Strongly Depends on Training Methodology*
- arXiv:2603.08234 — *The Struggle Between Continuation and Refusal: A Mechanistic Analysis of the Continuation-Triggered Jailbreak in LLMs*
- arXiv:2402.17700 — *RAVEL: Evaluating Interpretability Methods on Disentangling Language Model Representations* (very likely real and relevant; simply not fetched this pass)
- the §2 rows still unverified from the 2026-09-15 pass: arXiv:2602.02132, 2605.16591, 2607.14147, 2608.15772, 2606.14388, 2508.20766, 2509.09708

**Note on `arXiv:2606.15092`** (*High-Dimensional Random Projection for Activation Steering*, Pham,
Do, Abdullaev, Nguyen, Than, 13 Jun 2026): the paper **is verified to exist** (abstract fetched), but
the specific thing we wanted from it — whether it uses **norm- or dimension-matched random
projections as controls** — **could not be determined from the abstract**. It is therefore not in the
§A2 table. Do not cite it for control methodology without reading the full paper.

---

## A7. Searches run in this pass

| # | Query | Useful hits |
|---|---|---|
| 1 | interpretability illusion subspace activation patching dormant pathway Makelov Nanda | 2311.17030 (key) |
| 2 | activation patching best practices metrics methods layer confound Zhang Nanda | 2309.16042 (key), 2404.15255 |
| 3 | single direction fails to mediate but full activation patching works negative result low-rank steering | 2606.27510, 2605.16362 (both key) |
| 4 | Hydra effect self-repair ablation compensation language models McGrath | 2307.15771, 2402.15390 |
| 5 | random control subspace rank-matched norm-matched baseline activation steering methodology null direction | 2606.15092 (abstract only) |
| 6 | patching recovery explained by magnitude norm dose rather than direction residual stream intervention | LayerNorm-rescaling self-repair detail |
| 7 | in-context learning token position where information stored query token attention localization last demonstration | 2505.15807 |
| 8 | layer versus feature confound mechanistic interpretability patching which layer chosen argmax artifact | 2311.17030 resurfaced; no direct hit |
| 9 | Atlas of In-Context Learning attention heads in-context retrieval augmentation 2025 | 2505.15807 (NeurIPS 2025 confirmed) |
| 10 | in-context novel word meaning nonce word representation causal tracing token position language model redefinition | 0 direct |
| 11 | concept encoding decoding mechanism in-context learning emergence of abstractions 2024 | 2412.12276 |
| 12 | geometry of refusal concept cones multiple refusal directions Wollschlager ICML 2025 | 2502.17420 **verified** |
| 13 | "Where does In-context Learning Happen" large language models Sia task recognition layers | NeurIPS 2024 proceedings (key) |
| 14 | per-token position causal map activation patching jailbreak which token position carries effect residual stream | 2605.00123, 2606.28153 |
| 15 | AxBench steering LLMs simple baselines outperform sparse autoencoders concept subspace negative | 2501.17148 (ICML 2025) |
| 16 | in-context learning semantic remapping representation of substituted word query position patching 2026 | 2501.00070, 2602.04212; **no Doublespeak follow-up** |
| 17 | steering vectors generalization reliability spurious brittle negative results Tan 2024 arXiv | 2407.12404 (NeurIPS 2024) |
| 18 | linear subspace insufficient nonlinear distributed representation DAS fails negative result causal abstraction | 2507.08802 (key), 2504.13151, 2402.17700 |
| 19 | full residual state patching recovers behavior but best single direction does not rank-1 insufficient mediator | 0 direct — **the searched-for negative did not surface** |
| 20 | comparing conditions at different layers confound interpretability each condition own best layer unfair comparison | 0 direct |
| 21 | word defined in context representation at its own token position hidden state patching causal effect euphemism | 0 direct |
| 22 | Heimersheim Nanda how to use and interpret activation patching pitfalls layer choice interpretation | 2404.15255 |

**Pages fetched and read this pass (15):** arxiv.org/abs/{2606.27510, 2605.16362, 2311.17030,
2309.16042, 2605.00123, 2605.18830, 2501.00070, 2602.04212, 2507.08802, 2609.14759, 2606.15092,
2606.28153, 2504.13151}; arxiv.org/html/2605.18830; arxiv.org/html/2605.00123v1.

**This pass: 22 searches, 15 primary-page fetches.** Running totals with §6: **39 searches, 20
primary-page fetches.**
