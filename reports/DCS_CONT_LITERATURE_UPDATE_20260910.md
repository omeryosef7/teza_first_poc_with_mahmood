# DCS — Continuation literature update, 2026-09-10

**Mandate.** §41 literature update for the Doublespeak / semantic-installation phase.

**Status.** Additive sweep. Appends to — does **not** replace — `reports/DCS_LITERATURE_MATRIX.md`,
`reports/DCS_TS_LITERATURE_UPDATE_20260906.md` and `reports/DCS_SUCC_LITERATURE_UPDATE_20260909.md`.
No other file modified. No GPU/SLURM job run. No measurement of ours made or re-made.

**Provenance**

| field | value |
|---|---|
| git sha | `8e631175cacd1052ccad7337579f90ef5fcf3311` |
| branch | `behavioral-causality-sprint` |
| written | 2026-09-10T10:56Z |
| produced by | manual sweep; `WebSearch` + `WebFetch` (arXiv abstract pages), plus two parallel delegated search agents |
| new works catalogued | see §2 |

**Verification convention** (carried over unchanged from the matrix):

- **✓fetched** — the arXiv / venue abstract page was retrieved *this session* and read.
- **†snippet** — located only via a search-result snippet. **Venue, model and claim fields are
  unverified and must not be cited without opening the paper.**

⚠ **This pass performed abstract-level fetches only. No full-PDF read anywhere.** Every "one-sentence
finding" below is the fetch tool's extraction of an abstract, i.e. a secondary summarisation step.

---

## 0. Why this pass exists and what is genuinely new in it

The three prior files were built around the query vocabulary *jailbreak*, *decodable*,
*demonstration→query*, *refusal direction*, *concept specificity*. This pass was built around a
**different** question set — the five columns below — and around one specific claim the prior files
never tested against the record:

> **"Conduit, not store."** A single token position's attention row is causally **necessary** for
> transmitting an effect from an earlier context span (knockout of that one row removes ~62 % of the
> demonstration→query effect), **yet** transplanting that token's full residual state at all 32
> layers transfers ~0 % of the semantic gap.

That is our most distinctive finding, and §5 reports what the record does and does not contain on it.

**The five novelty columns**, used in every table:

| col | question |
|---|---|
| **(a)** | localises to a specific **QUERY-side codeword/token ROW** via attention knockout? |
| **(b)** | runs a **LADDER** over query positions (progressively including more query rows)? |
| **(c)** | uses a **CONCEPT-FREE readout** (probe question that never names the answer)? |
| **(d)** | does **CAUSAL representation patching** for a semantic concept? |
| **(e)** | measures a **BEHAVIOURAL ASR change caused by an internal intervention**? |

Coding rules used: **yes** = the paper does this as a reported experiment; **partial** = it does a
recognisably weaker or differently-scoped version; **no** = absent. Where the abstract was
insufficient to decide, the cell reads **unknown** rather than being guessed.

---

## 1. Headline verdict, stated up front

1. **Column (e) — behavioural ASR change caused by an internal intervention — is NOT novel.** It is
   pre-empted at least six times over, most cleanly by **`2606.28153`** (ICML 2026 **Oral**:
   suppressing "adversarially compromised heads" drives ASR 0 % → 95 %+), **`2608.27504`** (ablating
   a discovered jailbreak circuit at first-token prediction cuts ASR by up to 80 %), **`2607.14147`**
   (prefill-attention knockout, 64 % → 25 %), **`2605.00123`** (COLM 2026, LOCA) and **`2508.10029`**
   (hidden-state interpolation at selected layers *and token positions*, 94.13 % macro ASR). See §4.
2. **Column (d) — causal representation patching for a semantic concept — is NOT novel**, and was
   already conceded in the 09-09 file (`2605.18830`, `2607.24425`). This pass adds `2401.06102`
   (Patchscopes), `2602.07794`, `2603.08234` and `2605.00123` as further ancestors. See §4.
3. **Columns (a), (b), (c) survive**, but all three survive *more narrowly than the prior files
   assumed*, and each now has a named ancestor that must be cited rather than ignored — in
   particular **`2605.04061` already establishes that the QUERY position is strictly necessary
   (53–100 % disruption)** in ICL, and **the Doublespeak paper itself uses Patchscopes**, which sits
   directly adjacent to our concept-free readout. **(b), the position ladder, is the cleanest
   surviving claim.** See §4.
4. **"Conduit, not store" is NOT published in our exact shape — but the gap is much narrower than we
   thought.** The closest relative is **`2606.08292`, Quirke, *Necessary, Decodable and Reversible,
   Yet Not Transferable*** (arXiv 2026-06-06, rev 2026-08-04), whose abstract states in terms:
   *"necessity, decodability, same-prompt repair, and cross-prompt transfer are separable
   evidence."* That is our logical form, one year earlier, in head-space rather than
   token-position-space. **It must be cited in the same paragraph as our result.** See §5.
5. **Top three methods to borrow: `2605.29971` (continuous-variable causal intervention),
   `2303.02536`/`2507.08802` (DAS *with* the non-linear-representation-dilemma guard), and
   `2607.08349` (certified interventional fidelity / anytime-valid confidence sequences).** See §6.
6. **The pitfall to pre-register against, above all others, is the MISSING POSITIVE CONTROL for our
   0 % transplant** (§7.1) — followed by `2412.09565` obfuscated activations, `2511.04638` divergent
   representations, and `2307.15771` self-repair contaminating the 62 %. See §7.

---

## 2. Main table — works found this pass

Rows are ordered by consequence for our claims. `id` is the arXiv id unless stated.

### 2.1 Consequential rows (all ✓fetched this session)

| id / citation | URL | one-sentence finding | (a) query-row knockout | (b) query ladder | (c) concept-free readout | (d) causal semantic patching | (e) internal→ASR |
|---|---|---|---|---|---|---|---|
| **`2605.22488`** — Darade & Thorat, *Represented Is Not Computed: A Causal Test of Candidate Algorithmic Intermediates in a Transformer*, 2026-05-21, arXiv (cs.LG) | https://arxiv.org/abs/2605.22488 | Linear probes decode the closed-form arithmetic intermediates, but "the identified localized causal route does not transmit them to the output stream" — the route is real and the represented content is real, and they are not the same thing. | **partial** — localises a causal *route* (D-selective early communication) but not a query-side codeword attention row | **no** | **no** — linear probes | **yes** — causal tests separating representation from use | **no** — task accuracy, no safety endpoint |
| **`2608.27504`** — Mehrbod, Knyazev, Wolf, Belilovsky & Nanfack, *Circuit Discovery Helps Detect LLM Jailbreaking: A Mechanistic Interpretability Study*, 2026-08-27; ICML 2025 R2-FM workshop; LLaMA-2-7B-chat-hf | https://arxiv.org/abs/2608.27504 | Edge attribution patching + subnetwork probing find circuits producing affirmative jailbreak responses; "ablating these circuits during the first token prediction can reduce attack success rates by up to 80 %". | **partial** — attention heads, positions not specified in abstract | **no** | **no** | **no** — circuit discovery, not semantic-concept patching | ⛔ **yes** |
| **`2508.10029`** — Xing, Yang, Li, Hu, Xu, Zhang, Lin & Han, *Latent Fusion Jailbreak*, v1 2025-08-08 / v3 2026-07-17 | https://arxiv.org/abs/2508.10029 | Interpolates hidden states of a harmful and a structurally matched harmless query "at carefully selected layers and token positions", chosen by refusal-loss gradients; 94.13 % macro ASR over 5 open-weight models, 27.45 % with random pairing. | **no** | **no** | **no** | ⛔ **yes** — a hidden-state edit that installs harmful content | ⛔ **yes** |
| **`2606.08044`** — Jiang, Gjølbye, Zhang & Koyejo, *When Behavioral Safety Evaluation Fails: A Representation-Level Perspective*, 2026-06-06 rev 2026-08-04; Gemma-2-2B, Llama-3.2-3B, Qwen-2.5-3B | https://arxiv.org/abs/2606.08044 | Defines an "audit gap" and a **Latent Vulnerability Score** = safety degradation per unit of bounded latent perturbation; models passing every static audit show 54–86 % harmful compliance under small internal perturbations vs 3–48 % baseline. | **no** | **no** | **no** | **partial** — bounded latent perturbation, not concept-identity patching | ⛔ **yes** — internal perturbation → compliance rate |
| **`2412.09565`** — Bailey, Serrano, Sheshadri, Seleznyov, Taylor, Jenner, Hilton, Casper, Guestrin & Emmons, *Obfuscated Activations Bypass LLM Latent-Space Defenses*, 2024-12-12 rev 2025-02-08 | https://arxiv.org/abs/2412.09565 | Optimising against an internal-activation objective produces "obfuscated activations" that drive monitor recall from 100 % → 0 % while retaining a 90 % jailbreaking rate; SAEs, representation probes and latent OOD detection all fall. | **no** | **no** | **no** | **partial** — activations are the optimisation target | **yes** |
| **`2609.01604`** — Vasava & Jiang, *Beyond Scores: Understanding LLM-as-a-Judge Mechanisms in Summarization Evaluation*, 2026-09-01, **EMNLP 2026 Main**; Themis (Llama-3-8B), Prometheus (Mistral-7B), base Llama-3-8B control | https://arxiv.org/abs/2609.01604 | A four-experiment battery of causal tracing, logit-lens projection and **attention-head knockout** finds a two-stage architecture: "below layer 15, attention performs local error comparison and **routes** the result to the final input position; above it, the MLP cascade integrates the signal and **writes** the rating." | **partial** — attention-head knockout with an explicit *route-to-final-position* framing, but heads not a query codeword row | **no** | **no** | **partial** | **no** — rating, not ASR |
| **`2606.13168`** — Javadov, *When Does Routing Become Interpretable? Causal Probes on Block Attention Residuals*, 2026-06-11 | https://arxiv.org/abs/2606.13168 | Finds "a sharp dissociation between average routing mass and causal importance" — the largest-mass slice is not the largest causal contribution, and one source family carries appreciable mass with **no detectable causal role**; concludes architectural exposure of routing is "necessary but not sufficient for mechanistic interpretation". | **no** | **no** | **no** | **partial** | **no** |
| **`2605.29971`** — Zhou, McCoy & Frank, *Causal Interventions on Continuous Variables: A Case Study on Verb Bias in Steering Vectors for In-Context Learning*, 2026-05-28 | https://arxiv.org/abs/2605.29971 | Given activation vectors paired with a **graded** target variable, localise a low-dimensional direction for it and edit toward counterfactual values; "counterfactual edits to verb bias systematically shift downstream structural preferences." | **no** | **no** | **no** | **yes** — for a continuous variable | **partial** — behavioural, but structural preference not ASR |
| **`2507.11878`** — Zhao, Huang, Wu, Bau & Shi, *LLMs Encode Harmfulness and Refusal Separately*, v1 2025-07-16 / rev 2026-07-06 | https://arxiv.org/abs/2507.11878 | There is a **harmfulness direction distinct from the refusal direction**: steering harmfulness changes the model's judgment of the instruction, steering refusal elicits refusal *without* reversing that judgment; the latent harmfulness representation works as an intrinsic safeguard ("Latent Guard"). | **no** | **no** | **no** | **yes** | **partial** — refusal behaviour measured, not an attack ASR |
| **`2606.25487`** — Gao, *How Reliable Is Your Jailbreak Judge? Calibration and Adversarial Robustness of Automated ASR Scoring*, 2026-06-24 rev 06-25 | https://arxiv.org/abs/2606.25487 | Dedicated classifier over-flags at precision 0.835 / recall 0.974 while three LLM-judges hold precision 0.81–0.94 but show **recall 0.06–0.65**; benign wrappers that leave the harmful text untouched flip every LLM-judge 57–100 % of the time, and GCG flips 70 % of confident classifier true positives. | **no** | **no** | **no** | **no** | **no** — measurement paper |
| **`2605.08012`** — Lin & Liu, *Position: Mechanistic Interpretability Must Disclose Identification Assumptions for Causal Claims*, 2026-05-08, **NeurIPS 2026 Position Track** | https://arxiv.org/abs/2605.08012 | "Validation is not identification": faithfulness, completeness and ablation effects are routinely reported as causal support without stating the assumptions that make them identifying; proposes a 5-point disclosure norm (is the claim causal / name the strategy / enumerate assumptions / stress one / say how conclusions shift if it fails). | **no** | **no** | **no** | **no** | **no** — position paper |
| **`2607.08349`** — Asiaee, *Certified Interventional Fidelity: Anytime-Valid, Adaptive Evaluation of Causal Claims in Mechanistic Interpretability*, 2026-07-09, **UAI 2026** | https://arxiv.org/abs/2607.08349 | Formalises an interpretability claim as a causal estimand over a stated input distribution **and a stated intervention distribution**, and supplies **anytime-valid confidence sequences** valid under adaptive sampling; variance-adaptive betting sequences cut certification cost 10–30×. | **no** | **no** | **no** | **no** | **no** — statistics paper |
| **`2507.08802`** — Sutter, Minder, Hofmann & Pimentel, *The Non-Linear Representation Dilemma: Is Causal Abstraction Enough for Mechanistic Interpretability?*, 2025-07-11 rev 2025-11-12, **NeurIPS 2025 Spotlight** | https://arxiv.org/abs/2507.08802 | If the alignment map is not constrained to be linear, "any neural network can be mapped to any algorithm" — they hit **100 % IOI alignment accuracy using randomly initialised LMs**, so unrestricted causal abstraction is vacuous. | **no** | **no** | **no** | **yes** (theory of) | **no** |
| **`2511.04638`** — Grant, Han, Tartaglini & Potts, *Addressing divergent representations from causal interventions on neural networks*, 2025-11-06 rev 2026-04-22 | https://arxiv.org/abs/2511.04638 | Common causal interventions shift internal representations **off the model's natural distribution**; distinguishes harmless divergences inside the behavioural null-space from **pernicious** ones that activate dormant pathways, and proposes a Counterfactual Latent loss to stay near-distribution. | **no** | **no** | **no** | **yes** (methodological) | **no** |
| **`2407.08734`** — Miller, Chughtai & Saunders, *Transformer Circuit Faithfulness Metrics are not Robust*, 2024-07-11, **CoLM 2024** | https://arxiv.org/abs/2407.08734 | Faithfulness scores are "highly sensitive to seemingly insignificant changes in the ablation methodology" and conflate methodological choices with circuit properties — "the task a circuit is required to perform depends on the ablation used to test it". | **no** | **no** | **no** | **no** | **no** |
| **`2606.09899`** — Zhang & Wang, *When Attribution Patching Lies: Diagnosis and a Second-Order Correction*, 2026-06-05 | https://arxiv.org/abs/2606.09899 | The dominant error in attribution patching comes from **downstream non-linearity**, not local curvature at the patched site; supplies an HVP second-order correction, a reliability score and error bounds in a Screen-Flag-Fix workflow. | **no** | **no** | **no** | **no** | **no** |
| **`2604.15557`** — Billa, *Predicting Where Steering Vectors Succeed*, 2026-04-16; Pythia-2.8B → Llama-8B, 24 binary concept families | https://arxiv.org/abs/2604.15557 | A training-free logit-lens quantity (the **Linear Accessibility Profile**) predicts steering effectiveness at ρ = +0.86…+0.91 and best-layer choice at ρ = +0.63…+0.92 — and the middle-layer heuristic fails where LAP succeeds. | **no** | **no** | **no** | **partial** | **no** |
| **`2401.06102`** — Ghandeharioun, Caciularu, Pearce, Dixon & Geva, *Patchscopes: A Unifying Framework for Inspecting Hidden Representations of Language Models*, 2024-01-11, **ICML 2024** | https://arxiv.org/abs/2401.06102 | Patches a hidden representation into a **separate inspection prompt** and lets the model verbalise what that representation encodes, unifying prior decoding methods and fixing their weakness on early layers. | **no** | **no** | ⚠ **partial** — an inspection prompt that elicits the content without the analyst naming it; the direct methodological ancestor of our readout | **yes** | **no** |
| **`2605.10664`** — Kang, Liu, Ma, Huang, Tan & Jiang, *Prompt–Activation Duality: Improving Activation Steering via Attention-Level Interventions*, 2026-05-11 rev 05-14 | https://arxiv.org/abs/2605.10664 | Residual-stream steering fails over long generations because "steered token states are stored and repeatedly reused" (KV-cache contamination); extracting the steering signal from **system-prompt contributions to self-attention** with token-level gating (GCAD) fixes it — coherence drift −18.6 → −1.9. | **no** | **no** | **no** | **partial** | **no** |
| **`2602.07794`** — Xu, Zhang, Qiu & Huang, *Emergent Structured Representations Support Flexible In-Context Inference in Large Language Models*, 2026-02-08 rev 2026-04-20 | https://arxiv.org/abs/2602.07794 | A conceptual subspace emerges in middle-to-late layers whose structure **persists across contexts**; causal mediation shows it is "functionally central to model predictions", built by early-to-middle attention heads and read by later layers. | **no** | **no** | **no** | **yes** | **no** |
| **`2510.08604`** — Mura, Piras, Lukošiūtė, Pintor, Karbasi & Biggio, *LatentBreak: Jailbreaking Large Language Models through Latent Space Feedback*, 2025-10-07 rev 10-30 | https://arxiv.org/abs/2510.08604 | A **word-substitution** attack whose objective is internal: minimise latent-space distance between the adversarial prompt's representation and that of harmless requests, producing low-perplexity prompts that beat perplexity filters. | **no** | **no** | **no** | **no** | **partial** — internal *objective*, prompt-level intervention |

### 2.2 Rows from the two delegated sweeps

⚠ **Provenance note.** These were located by two delegated search agents (§9). Rows marked
**✓re-fetched** were independently re-verified by me against the arXiv abstract page and any
discrepancy is noted. Rows marked **‡agent** rest on the agent's retrieval only — the URL is real
and was retrieved, but I did not personally read the abstract, so treat them at †snippet confidence.

| id / citation | URL | one-sentence finding | (a) | (b) | (c) | (d) | (e) |
|---|---|---|---|---|---|---|---|
| ⛔ **`2606.08292`** — Quirke, *Necessary, Decodable and Reversible, Yet Not Transferable: A Stress Test for Attention-Head Role Claims*, 2026-06-06 rev 2026-08-04, arXiv (cs.AI) **✓re-fetched** | https://arxiv.org/abs/2606.08292 | Tests whether an activation that is necessary, linearly decodable and repair-capable can also **carry the computation into another prompt**; in ~8 of 15 model-family cells (three 7–8B instruct models, 5 computation families) "tested attention-head states did not produce clean computation transfer" — ⭐ **"necessity, decodability, same-prompt repair, and cross-prompt transfer are separable evidence."** | **no** — attention-head states, not a token's residual row | **no** | **no** | **partial** — matched-control transfer assay | **no** — no safety endpoint |
| ⛔ **`2605.04061`** — Cheng & Zhang, *Single-Position Intervention Fails: Distributed Output Templates Drive In-Context Learning*, 2026-04-10; LION 2026 + ICLR 2026 workshops; Llama-3.2-3B primary, 4 families **✓re-fetched** | https://arxiv.org/abs/2605.04061 | "Single-position activation intervention achieves **0 % task transfer** across all 28 layers" despite high probing accuracy; and — ⚠ critically for us — "**the query position is strictly necessary (53–100 % disruption)** while no individual demonstration position is necessary (0 % disruption)." | ⚠ **partial** — establishes *query-position* necessity, but by position-level disruption, **not** by attention-row knockout | **no** | **no** | **yes** (negative) | **no** |
| **`2606.28153`** — Yin, Han & Li, *Robust Harmful Features Under Jailbreak Attacks: Attention Head Specialization*, 2026-06-26, **ICML 2026 Oral** ‡agent | https://arxiv.org/abs/2606.28153 | Attacks suppress early-layer "adversarially compromised heads" while mid-layer safety heads keep firing; suppressing those heads drives **ASR 0 % → 95 %+**. | **no** | **no** | **no** | **partial** | ⛔ **yes** |
| **`2607.14147`** — Kwon, *Breaking Refusal in the First Half: A Mechanistic Study of the Prefill Jailbreak*, 2026-07-14 ‡agent | https://arxiv.org/abs/2607.14147 | Knocking out early-response attention **to the prefill span**, with an equal-attention-mass control, collapses harmful continuation (**64 % → 25 %**) while the harm probe stays high. | ⚠ **partial** — knockout of specific *rows attending to a named span*, but response-side prefill, not a query codeword | ⚠ **partial** — dose-matched position **halves**, not a progressive ladder | **no** | **yes** | ⛔ **yes** |
| **`2605.00123`** — Kumar & Ahuja, *Minimal, Local, Causal Explanations for Jailbreak Success (LOCA)*, 2026-04-30, **COLM 2026** ‡agent | https://arxiv.org/abs/2605.00123 | Finds a **minimal** set of intermediate-representation changes that causally restore refusal for a given jailbreak. | **no** | **no** | **no** | ⛔ **yes** | ⛔ **yes** |
| ⛔ **`2602.04212`** — Lepori, Linzen, Yuan & Filippova, *Language Models Struggle to Use Representations Learned In-Context*, 2026-02-04 rev 2026-05-01 **✓re-fetched**; **cites Doublespeak** | https://arxiv.org/abs/2602.04212 | LLMs "struggle to deploy representations of novel semantics that are defined in-context, **even if they encode these semantics**", shown on next-token prediction with open-weights LLMs and on a novel adaptive-world-modeling task with frontier reasoning models. | **no** | **no** | ⚠ **partial** — downstream task avoids naming the target | **no** — no causal intervention described in the abstract | **no** |
| **`2504.19395`** — Fang, Mishra, Gao, Liu & Khashabi, *ICL CIPHERS: Quantifying "Learning" in In-Context Learning via Substitution Ciphers*, 2025-04-28, **EMNLP 2025 main (1316)** ‡agent | https://arxiv.org/abs/2504.19395 | Bijective substitution ciphers are solved better than non-bijective ones, and a **logit-lens rank-difference** measure shows the model internally decodes the substituted token; the authors report Patchscope-style methods **failed** for them and only logit lens worked. | **no** | **no** | **no** — the readout names the target token | **no** | **no** |
| **`2608.03210`** — Zhu, Huang, Juefei-Xu, Li, Zeng, Qin, Guo & Pu, *ICO: Enhancing Semantic-Shift Jailbreaks via Iterative Context Optimization*, 2026-08-04 ‡agent; **cites Doublespeak** | https://arxiv.org/abs/2608.03210 | Independently names the phenomenon "**semantic-shift jailbreak**" and optimises the context that drives it — but is explicitly and entirely black-box ("cannot access parameters, gradients, or internal representations"). | **no** | **no** | **no** | **no** | **no** |
| **`2609.09553`** — Rivasseau, *Arbitrary Cipher Attacks Against LLMs Do Not Require Fine-Tuning*, **2026-09-09** ‡agent | https://arxiv.org/abs/2609.09553 | Frontier models learn arbitrary ciphers in-context and alignment collapses inside the cipher channel; purely black-box. **The newest item in this sweep — one day old.** | **no** | **no** | **no** | **no** | **no** |
| **`2606.25182`** — Nikolenko, Papucci, Rezaei & Manchingal, *What Intermediate Layers Know: Detecting Jailbreaks from Entropy Dynamics*, 2026-06-23, **ECML PKDD 2026** ‡agent | https://arxiv.org/abs/2606.25182 | Logit-lens **entropy trend across token positions** separates jailbreaks, peaking in mid layers. | **no** | ⚠ **partial** — a per-token-position trajectory, but observational, not interventional | **no** | **no** | **no** |
| **`2603.14923`** — *Directional Routing in Transformers* ‡agent | https://arxiv.org/abs/2603.14923 | Disabling routing collapses factual recall to near-zero and induction from 93.4 % → 0.0 %; ⭐ "**the coordination mechanism is irreplaceable; the components it coordinates are not.**" | **no** | **no** | **no** | **partial** | **no** |
| **`2604.04385`** — *How Alignment Routes* ‡agent | https://arxiv.org/abs/2604.04385 | Knockout confirms a routing gate is causally necessary, yet **injecting the plaintext gate activation restores only 48 % of refusals** — a partial, not null, transfer. | **partial** | **no** | **no** | **yes** | **partial** |
| **`2607.03502`** — Brauer, Verdun & Marks, *Reading Between the Dots* ‡agent | https://arxiv.org/abs/2607.03502 | Filler-token residuals are 80–95 % decodable and "**KV-cache transplants at filler positions causally swap outputs between examples**" — a semantically-empty-looking position that IS a store. | **no** | **no** | **no** | **yes** | **no** |
| **`2604.22128`** — *Dissociating Decodability and Causal Use in Bracket-Sequence Transformers* ‡agent (already in matrix) | https://arxiv.org/abs/2604.22128 | Masking the single stack-top attention edge collapses accuracy, and patching shows it is "not only causally necessary, but its recovery is **sufficient**" — the explicit counterexample to our asymmetry. | **partial** | **no** | **no** | **yes** | **no** |
| **`2312.10091`** — Variengien & Winsor, *Look Before You Leap: A Universal Emergent Decomposition of Retrieval Tasks in Language Models*, 2023-12-13 **✓re-fetched** | https://arxiv.org/abs/2312.10091 | ORION over 18 models (125M–70B): "middle layers at the last token position process the request, while late layers retrieve"; task decomposition preserves 70 % accuracy, and a prompt-injection mitigation goes 15.5 % → 97.5 % on Pythia-12b. ⚠ The "request patching gives ~100 % single-position transfer" figure is **in the body, not the abstract — unverified here**. | **no** | **no** | **no** | **yes** | **no** |
| **`2301.04213`** — Hase et al., *Does Localization Inform Editing?* ‡agent | https://arxiv.org/abs/2301.04213 | Causal-tracing localization does **not** predict where model editing works — the ancestor of every necessity-vs-manipulability dissociation. | **no** | **no** | **no** | **yes** | **no** |
| **`2510.06182`** — Gur-Arieh, Geva & Geiger, *Mixing Mechanisms* ‡agent | https://arxiv.org/abs/2510.06182 | Positional, lexical and **reflexive (pointer)** retrieval mechanisms coexist; a causal model reaches 95 % agreement. The published pointer-vs-content taxonomy. | **no** | **no** | **no** | **yes** | **no** |
| **`2506.12913`** — Angell, Brinkmann & He, *Jailbreak Transferability Emerges from Shared Representations*, 2025-06-15, **ICLR 2026** ‡agent | https://arxiv.org/abs/2506.12913 | Jailbreak transfer tracks benign representational similarity; **cipher jailbreaks transfer worse** than persona ones because they exploit idiosyncratic quirks. | **no** | **no** | **no** | **no** | **partial** |
| **`2602.19396`** — Farzam et al., *Hiding in Plain Text: Detecting Concealed Jailbreaks via Activation Disentanglement*, 2026-02-23 ‡agent | https://arxiv.org/abs/2602.19396 | Disentangles **goal** vs **framing** factors in activations to detect concealed-intent jailbreaks (FrameShield). | **no** | **no** | **no** | **no** | **no** |
| **`2604.14865`** — He, Sel, Ali, Bao, Cunningham & Wei, *Segment-Level Coherence for Robust Harmful Intent Probing*, 2026-04-16 ‡agent | https://arxiv.org/abs/2604.14865 | Multi-evidence-token streaming probes detect harmful intent even under adversarially-finetuned character ciphers (AUROC 98.85 %). | **no** | **no** | **partial** | **no** | **no** |

### 2.3 Secondary rows — relevant, catalogued, no direct threat

| id | work | verification | bearing on us |
|---|---|---|---|
| `2310.17191` | Feng & Steinhardt, *How do Language Models Bind Entities in Context?* | †snippet | The canonical binding-ID result: binding information is carried by **additive binding-ID vectors attached to entities and attributes**, present in every sufficiently large Pythia/LLaMA model. The natural competing hypothesis for what our codeword row carries. |
| `2409.05448` | *Representational Analysis of Binding in Language Models* | †snippet | Binding IDs form a **continuous subspace** with geometric structure, are transferable across tasks, and fidelity scales with model size. Directly relevant to whether "semantic installation" is a binding-ID magnitude. |
| `2606.08644` | *A retrieval-conditioned rebinding circuit for dynamic entity tracking in LLMs* | †snippet | Object representations are **preserved** while swap information redirects retrieval to a different binding ID at retrieval time — a published "the content did not move, the pointer did" mechanism. See §5.3. |
| `2505.20896` | *How Do Transformers Learn Variable Binding in Symbolic Programs?* (ICML 2025) | †snippet | Developmental account of binding acquisition; useful background, wrong setting. |
| `2303.02536` | Geiger et al., *Finding Alignments Between Interpretable Causal Variables and Distributed Neural Representations* (DAS) | †snippet | The canonical method for §6.2. Learns a rotation of the residual stream and performs **distributed interchange interventions** on k dimensions. |
| `2602.05234` | *Faithful Bi-Directional Model Steering via Distribution Matching and Distributed Interchange Interventions* (ICLR 2026) | †snippet | A 2026 DAS descendant adding distribution matching — relevant to the `2511.04638` off-distribution worry. |
| `2602.16698` | *Position: Causality is Key for Interpretability Claims to Generalise* | †snippet | Position piece; pairs with `2605.08012` for the pre-registration section. |
| `2307.15771` | McGrath et al., *The Hydra Effect: Emergent Self-repair in Language Model Computations* | †snippet | Knocking out an attention layer causes another to compensate ⇒ ablation-based **necessity** systematically under-estimates. The single most important false-negative mechanism for our knockout ladder. |
| `2309.16042` | *Towards Best Practices of Activation Patching in Language Models* | †snippet | Denoising vs noising and corruption-choice guidance; the standard citation for "which direction did you patch in". |
| `2404.15255` | Heimersheim & Nanda, *How to use and interpret activation patching* | †snippet | The standard practitioner caveat list. |
| `2311.17030` | *Is This the Subspace You Are Looking for? An Interpretability Illusion for Subspace Activation Patching* | †snippet (already in matrix) | A 1-D subspace patch can move outputs by activating a **dormant** pathway while patching the whole containing MLP layer does nothing. Pre-registration target for §6.2. |
| `2604.18901` | *Harmful Intent as a Geometrically Recoverable Feature of LLM Residual Streams* | †snippet | Abliterated models still detect harmful intent as reliably as their instruct counterparts. |
| `2603.27518` | *Over-Refusal and Representation Subspaces: Task-Conditioned Refusal in Aligned LLMs* | †snippet | Harmful-refusal directions are task-agnostic/global; over-refusal directions are task-dependent. |
| `2604.09544` | *Large Language Models Generate Harmful Content Using a Distinct, Unified Mechanism* | †snippet | Claims a single unified harmful-generation mechanism; would compete with a concept-specific story if it holds. **Unopened.** |
| `2604.07006` | *Continuous Interpretive Steering for Scalar Diversity* | †snippet | Treats **steering strength as a continuous experimental variable** — the dose-response design our next phase needs. |
| `2603.10068` | *ADVERSA: Measuring Multi-Turn Guardrail Degradation and Judge Reliability in LLMs* | †snippet | Second independent 2026 judge-reliability instrument. |
| `2503.02574` | *LLM-Safety Evaluations Lack Robustness* | †snippet | Earlier, broader statement of the same endpoint problem. |
| `2505.24244` | *Mamba Knockout for Unraveling Factual Information Flow* | †snippet | Attention-knockout analogue in a non-attention architecture; a possible architecture-generality control. |
| `2402.14811` | Prakash et al., *Fine-Tuning Enhances Existing Mechanisms: A Case Study on Entity Tracking* | †snippet | Documents the **query-box token vs correct-object token** split at the last position — early heads read the query token's residual stream, late heads read the object token. Closest published statement of a query-side/content-side division of labour. |
| `2606.16407` | *A Mechanistic Understanding of Pronoun Fidelity in LLMs* | †snippet | DAS applied to a binding-like linguistic variable; a concrete DAS template. |
| `2504.03022` | Feucht et al., *The Dual-Route Model of Induction* | †snippet | **Token-level** induction heads copy exact subword tokens; **concept-level** induction heads copy whole words as abstract concepts. Directly relevant to whether Doublespeak rides the token route or the concept route. |
| `2406.09519` | *Talking Heads: Understanding Inter-layer Communication in Transformer Language Models* | †snippet | Inter-layer communication channels; relevant to "conduit" framing. |
| `2601.06109` | *CBMAS: Cognitive Behavioral Modeling via Activation Steering* | †snippet | Steering-to-behaviour chain, non-safety. |

---

## 3. Topics that returned NOTHING relevant — reported honestly

These are **null searches, not evidence of novelty.**

1. **"Concept-free readout" as a named method.** ⛔ Multiple query formulations
   (`indirect probing "never names" concept-free readout`; `model self-report what does word refer
   to`) returned **nothing on target** — the results were concept-bottleneck literature, self-report
   / introspection literature, and, on one reformulation, physics papers about quantum sensor
   readout. There is **no established term** for what we do. The nearest published relatives are
   **Patchscopes** (`2401.06102`) and the self-interpretability / introspection line, neither of
   which is a per-domain graded score from a question that withholds the answer.
2. **A LADDER over query positions.** ⛔ No paper found that progressively includes more *query-side*
   rows. The only "progressive" knockout designs located are **over layers** (progressive unblocking
   of layers, in the Geva-derived tradition) and **over components** (cumulative expert removal in
   MoE). Explicitly: the multiple-granularity framing found in search snippets is *all-layer vs
   single-layer vs intermediate*, i.e. a **layer** ladder, not a **position** ladder.
3. **A "semantic installation"-style graded score that predicts per-domain ASR.** ⛔ Nothing found.
   Searches for a continuous internal quantity regressed against per-domain attack success returned
   only prompt-injection ASR reports and unrelated "semantic drift" monitoring/marketing material.
4. **Follow-ups or replications of Doublespeak with mechanistic content.** ⛔ **Fourth consecutive
   null, and now quantified.** The delegated sweep queried the Semantic Scholar citations API for
   `arXiv:2512.03771` and got **exactly 4 indexed citing papers** — `2608.03210`, `2605.28854`,
   `2605.00583`, `2604.05273` — plus two more found by snippet (`2601.10294`, `2602.04212`) that S2
   has not indexed; OpenAlex has not indexed the paper at all. An arXiv metadata query
   `all:"representation hijacking"` returns **1 hit — Doublespeak itself**. Of the citing works, only
   **`2608.03210` (ICO)** builds an attack on the phenomenon, and it is explicitly and entirely
   black-box. ⇒ **No mechanistic competitor on our exact attack exists in the indexed record.**
   ⚠ Two of the six citing papers (`2605.00583`, `2604.05273`, `2601.10294`) were **not opened** by
   either sweep and remain unassessed.
4b. **`abs:codeword AND abs:jailbreak` on the arXiv API returns ZERO results**; so does
   `all:jailbreak AND all:"attention knockout"` and `all:"word substitution" AND all:jailbreak`.
   Two independent confirmations this pass that the codeword-substitution *mechanism* literature is
   Doublespeak plus descendants.
4c. **Cipher-jailbreak successors do not look inside the model.** CipherChat/ArtPrompt/CodeChameleon/
   WordGame successors located (`2609.09553`, `2607.27373` RoguePrompt, `2510.10281` ArtPerception,
   `2606.29649`, LASH, MetaCipher) are **all strictly black-box**. The only cipher work with
   internals is `2504.19395` (ICL CIPHERS, EMNLP 2025) and a NeurIPS 2025 Mech-Interp workshop paper,
   *Demystifying Cipher-Following in LLMs via Activation Analysis* (Gross, Kaya, Kruegel & Vigna,
   OpenReview `UUOia1o3ud`, https://openreview.net/pdf?id=UUOia1o3ud) — ⚠ the PDF 403'd for the
   agent, so that row is **snippet-level and unverified**; neither measures a jailbreak ASR from an
   internal intervention.
5. **The exact phrase family "conduit not store" / "routing not storage" / "pointer not value".**
   ⛔ Not a term of art. Nothing indexed uses it. See §5.
6. **Attention-knockout competitors in LLM text safety, 2026.** ⛔ Consistent with the 09-09 arXiv
   API listing: 2026 attention-knockout work remains overwhelmingly vision-language / VLA / audio /
   video. `2609.01604` (EMNLP 2026, LLM-as-judge) is the one **new** text-domain LLM knockout paper
   found this pass, and it is not a safety paper.
7. **Doublespeak's own internals.** ⚠ The arXiv abstract page for `2512.03771` does **not** state
   which interpretability tools the paper uses beyond "interpretability tools to show that this
   semantic overwrite emerges layer by layer". **We cannot code the original paper against columns
   (a)–(e) from the abstract**, and this pass did not open the PDF. ⛔ **A full read of
   `2512.03771` §"interpretability" is a prerequisite for any novelty sentence we write**, and it is
   the single cheapest outstanding action — the PDF is in-repo at
   `doublespeak/INCONTEXT_REPRESENTATION_HIJACKING.pdf`.

---

## 4. Which of our five claims is NOT novel

### ⛔ (e) — behavioural ASR change caused by an internal intervention. **NOT NOVEL.**

Three independent pre-emptions, in increasing order of directness:

- **`2608.27504`** (https://arxiv.org/abs/2608.27504) — *the paper that pre-empts it most cleanly.*
  Circuits for affirmative jailbreak responses are found by edge attribution patching and subnetwork
  probing on LLaMA-2-7B-chat; **ablating them at first-token prediction reduces ASR by up to 80 %**.
  This is exactly the shape "internal intervention → measured ASR change in a jailbreak setting".
- **`2508.10029`** (https://arxiv.org/abs/2508.10029) — an internal **hidden-state edit at chosen
  layers *and token positions*** that *creates* the jailbreak, at 94.13 % macro ASR across five
  open-weight models, with a random-pairing control at 27.45 %. This pre-empts the *positive*
  direction (edit installs harm) as well as the ablative one.
- **`2606.08044`** (https://arxiv.org/abs/2606.08044) — quantifies the whole chain as a metric
  (**Latent Vulnerability Score**: safety degradation per unit bounded latent perturbation), with
  54–86 % harmful compliance under internal perturbation vs 3–48 % baseline.

⇒ **Do not write "we close the loop from an internal intervention to a behavioural safety
endpoint" as a contribution.** It is a citation. What survives is only *which* internal quantity we
intervene on (an in-context-installed concept identity under a codeword), not that we do it at all.

### ⛔ (d) — causal representation patching for a semantic concept. **NOT NOVEL** (already conceded).

Pre-empted by `2605.18830` and `2607.24425` in the 09-09 file. This pass adds two more ancestors:
**`2401.06102` Patchscopes** (patching a representation into an inspection prompt is a 2024 ICML
method) and **`2602.07794`** (causal mediation on an ICL conceptual subspace). ⇒ unchanged verdict.

### ⚠ (a) — query-side codeword ROW knockout. **SURVIVES, BUT MORE NARROWLY THAN PREVIOUSLY BELIEVED.**

Nothing found knocks out *the query-side codeword's own attention row* as the unit of analysis. But
four papers now occupy adjacent ground, and one of them is a real narrowing:

- ⛔ **`2605.04061`** (✓re-fetched) already publishes **query-position necessity in ICL**: "the query
  position is strictly necessary (53–100 % disruption) while no individual demonstration position is
  necessary (0 % disruption)", on Llama-3.2-3B with four families. ⇒ **"The query position is where
  the demonstration effect lands" is no longer ours.** What remains is that we locate it to *one
  token's attention row* by **knockout of that row**, versus their position-level disruption.
- ⚠ **`2607.14147`** (‡agent) knocks out *response-side attention rows to a named span* (the prefill),
  **with an equal-attention-mass control** — methodologically the closest published knockout design
  to ours, in a jailbreak setting, with an ASR endpoint.
- **`2402.14811`** (†snippet) reports that at the last position, **early heads read the query-box
  token's residual stream while late heads read the correct-object token** — a query-side/content-side
  split, discovered by patching rather than by row knockout.
- **`2609.01604`** (EMNLP 2026, ✓fetched) uses attention-head knockout with an explicit **"routes the
  result to the final input position"** finding — the same conceptual move (attention as router to a
  destination position), on a different task.

⇒ Frame (a) as *"the **row**, not the head and not the position, as the unit"*, cite all four, and
**never** claim attention knockout, knockout-in-ICL, or query-position importance as novel —
`2504.00132` / `2310.15916` / `2310.15213` / `2605.04061` have each closed part of that.

### ✅ (b) — LADDER over query positions. **THE CLEANEST SURVIVING CLAIM.**

No paper found runs a progressive-inclusion ladder over *query-side positions*. Both independent
sweeps returned the same null. All progressive designs located ladder over **layers** (the
Geva-derived progressive-unblocking tradition) or over **components** (cumulative expert removal).
The two nearest misses are **`2607.14147`**'s dose-matched first-half/second-half position split and
**`2606.25182`**'s per-token-position entropy *trajectory* — the former is a two-point comparison,
the latter is observational, not interventional.

⚠ Caveat: this is a null over a search vocabulary, and "ladder" is our word, not the field's — a
paper doing this under *cumulative ablation*, *incremental masking* or *positional sweep* could have
been missed. State the claim as *"we are not aware of a published position-wise ladder"*, not
*"the first"*.

### ⚠ (c) — CONCEPT-FREE readout. **SURVIVES, but the name is ours and the ancestor is Patchscopes — which Doublespeak itself uses.**

§3.1 records a genuine null: there is no established method with this description, and neither sweep
found any paper measuring a graded internal remapping score. But two things narrow it:

- **`2401.06102` Patchscopes** (ICML 2024) does the structurally analogous thing — an inspection
  prompt elicits what a representation encodes without the analyst supplying the answer.
- ⛔ **The Doublespeak paper itself uses Patchscopes.** The delegated sweep reports, from a full-text
  read of `2512.03771`, that its representation-transfer evidence is Patchscopes-based. ⇒ A reviewer
  who knows the attack paper will read our readout as a variant of the attack paper's own
  instrument. **This must be verified directly against the in-repo PDF before we write a novelty
  sentence** (§9 item 1), but plan for it to be true.

The nearest published *graded* remapping measure is **`2504.19395`** (ICL CIPHERS, EMNLP 2025): a
**logit-lens rank-difference** score for how well the model internally decodes a substituted token.
⚠ Note their reported experience — Patchscope-style methods **failed** for them and only logit lens
worked — which is a live alternative explanation for any readout instability we see.

⇒ Present the concept-free readout as **a prompt-level, patch-free analogue of a Patchscope**, cite
`2504.19395` as the graded-measure ancestor, and let the novelty rest on *graded + per-domain +
predicts ASR*, not on *concept-free*.

### 4.1 ⛔ Additions to the "what we must not say" list

Continuing the numbering from `DCS_SUCC_LITERATURE_UPDATE_20260909.md` §3.1 (which ended at 14):

15. *"We are the first to show that an internal intervention changes a behavioural jailbreak
    endpoint."* — foreclosed by `2608.27504`, `2508.10029`, `2606.08044`.
16. *"We introduce a readout that inspects what a representation encodes without naming it."* —
    foreclosed as a *method claim* by `2401.06102` (Patchscopes, ICML 2024).
17. *"Attention knockout shows the effect is routed to a destination position"* as a novel structural
    finding — foreclosed by `2609.01604` (EMNLP 2026) for the routing claim per se.
18. *"Optimising an internal-activation objective is a novel attack formulation."* — foreclosed by
    `2412.09565`, `2510.08604`, `2508.10029` and (from 09-09) `2607.08883`.
19. *"Our ASR endpoint is a settled measurement."* — `2606.25487` reports LLM-judge recall as low as
    **0.06** and benign wrappers flipping judges 57–100 % of the time. Any unqualified ASR statement
    is now a liability.
20. *"Necessity and cross-prompt transferability of a representation are separable — we show this."*
    — ⛔ foreclosed by **`2606.08292`**, whose abstract states exactly that as its conclusion, on
    three 7–8B instruction-tuned models.
21. *"The query position is where the demonstration effect lands."* — ⛔ foreclosed by
    **`2605.04061`** (query position strictly necessary, 53–100 % disruption; four model families).
22. *"LLMs encode in-context-defined novel semantics but fail to deploy them."* — ⛔ foreclosed by
    **`2602.04212`** (Lepori, Linzen, Yuan & Filippova), which is also one of the six papers citing
    Doublespeak. This is close to our O2 negative and must be cited as prior, not discovered.
23. *"We name a new phenomenon of in-context semantic shift."* — ⛔ `2608.03210` already uses
    **"semantic-shift jailbreak"** as a term.

---

## 5. Is "conduit not store" already published?

**Verdict: NO for our exact shape — no paper pairs (i) single-token-position attention-row knockout
showing necessity with (ii) an all-layer residual transplant of that same token transferring ~0 %,
and reads the conjunction as routing-vs-storage. But the gap is MUCH narrower than the prior files
assumed, and two papers must now be cited in the same paragraph as our result.**

### 5.0 ⛔ The threat we did not know about: `2606.08292`

> Quirke, *Necessary, Decodable and Reversible, Yet Not Transferable: A Stress Test for
> Attention-Head Role Claims*, https://arxiv.org/abs/2606.08292 — 2026-06-06, rev 2026-08-04,
> arXiv cs.AI. **✓re-fetched and abstract read directly.**

Abstract, verbatim:

> "Mechanistic studies often assign a component a role when removing it damages a behavior, its
> activation linearly encodes task information, and restoring that activation repairs the damage. We
> test the stronger implication: **can the same activation carry the requested computation into
> another prompt?** In the roughly 8 of 15 model-family cells receiving our full matched-control
> transfer assay, covering **three 7-8B instruction-tuned models** and 5 single-step computation
> families, **tested attention-head states did not produce clean computation transfer.** Same-answer
> and matched-context controls instead exposed inert or broad effects. Positive controls bound this
> result rather than eliminating its caveats: the instrument recovers known function vectors when
> writing into an underspecified prompt, and recovers a compact override-capable residual state in
> one of three controlled-model seeds."
>
> "**These results show that necessity, decodability, same-prompt repair, and cross-prompt transfer
> are separable evidence.**"

**This is our logical form, published three months ago, at our model scale.** The differences, which
are real but narrower than we would like:

| | `2606.08292` | ours |
|---|---|---|
| unit intervened on | **attention-head output states** at selected layers/positions | a **token position's residual stream at all 32 layers** |
| necessity arm | inherited from a screening stage; not quantified as a share of a named span's effect | quantified: ~62 % of the demonstration→query effect from one row |
| transfer arm | matched-control cross-prompt transfer assay | all-layer residual transplant, ~0 % of the semantic gap |
| framing | **negative / methodological**: a stress test on evidence standards | **positive mechanistic**: the site is a conduit |
| setting | 5 single-step computation families, benign | in-context semantic remapping, harmful, ASR endpoint |
| vocabulary | does not use "conduit", "routing", "store", or "storage" | ours |

⚠ ⛔ **Consequences.** (i) *"Necessity and cross-prompt transfer are separable"* is **no longer a
finding** — it is `2606.08292`'s stated conclusion, and our version is an instance of it at a new
unit of analysis. (ii) The paper **runs positive controls on its own instrument** and still hedges;
we currently run none (§7.1). (iii) It explicitly declines the positive claim — per the delegated
sweep, it states that its results "do not establish that a portable selection state is absent from
untested components or settings" — so **the positive conduit interpretation is still available to
us**, but we would be making a claim the nearest prior work deliberately refused to make, which
raises rather than lowers our evidential burden.

⇒ **Reframe.** Our contribution is not "necessity and transfer dissociate". It is: *at a single
token position, with the transplant taken at every layer, in a harmful in-context-remapping setting,
the dissociation is quantitatively extreme (~62 % vs ~0 %) and licenses a positive routing
interpretation.* Cite `2606.08292` as the general result and `2605.22488` as the arithmetic-domain
sibling.

### 5.1 What we searched

Query families run this pass, all returning **no exact match**:

- `"conduit not store"` / `"routing not storage"` / `"pointer not value"` transformer — ⛔ not terms
  of art, nothing indexed.
- `attention mediates information routing but residual state does not transfer "necessary but not
  sufficient"` — returned `2606.13168` (see below) and architecture papers, no match.
- `token is a pointer not a store ... residual stream transplant fails causal necessity attention` —
  returned `2605.22488`, `2605.09239`, `2605.25891`, `2606.29522`; see §5.3.
- `"information mover" head copies from token but token state alone insufficient ... cross-prompt
  transfer failure` — ⛔ **nothing**; the search engine explicitly reported no paper matching.
- `context-dependent representation only meaningful in situ ... patching across different prompts
  fails brittleness 2026` — returned steering-brittleness material, no match.

### 5.2 The second-closest relative — `2605.22488` (the arithmetic-domain sibling)

> Darade & Thorat, *Represented Is Not Computed: A Causal Test of Candidate Algorithmic Intermediates
> in a Transformer*, https://arxiv.org/abs/2605.22488

Abstract, verbatim in the load-bearing part:

> "Causal tests then separate representation from use: within the localized route from the stream
> with $D$ as input to the output positions, behavior depends on early $D$-selective communication,
> independent of $N$ and $B$. … Thus, the model represents the intermediates that make the
> closed-form solution plausible, **but the identified localized causal route does not transmit them
> to the output stream.**"

**How close is it, precisely.** It is the **same dissociation, run in the opposite order**:

| | `2605.22488` | ours |
|---|---|---|
| what is causally live | a localized **route** carrying early *D*-selective **communication** | the query codeword's **attention row** (~62 % of the effect) |
| what fails to move | the **represented intermediates** are not transmitted along that route | the **residual state** of the site does not transfer the semantic gap |
| conclusion | representation ≠ computation; the route carries something other than the decoded content | the site is a conduit, not a store |
| setting | synthetic arithmetic transformer, trained from scratch | Llama-3.1-8B-Instruct, jailbreak |
| endpoint | exact-answer accuracy (99.83 %) | ASR / semantic-installation score |

⇒ ⚠ **Our "conduit not store" is a replication of `2606.08292`'s and `2605.22488`'s core logic in a large pretrained
model and a safety setting, not a new logical form.** Write it that way. What is genuinely ours is
(i) the scale and naturalness of the model, (ii) that the causally-live unit is a *single token's
attention row* rather than a route between streams, (iii) the harm setting, and (iv) the quantitative
pairing of ~62 % necessity against ~0 % transfer **in the same experiment**, which `2605.22488` does
not do (its two arms are a route analysis and a sparse circuit search, not a matched
necessity/sufficiency pair on one site).

### 5.3 Other near relatives, honestly ranked

0. ⛔ **`2605.04061`** — *Single-Position Intervention Fails* (✓re-fetched). Contains **both legs of
   our conjunction in the same paper**, but at **different positions**, which is why it does not
   pre-empt us: the **query** position is strictly necessary (53–100 % disruption) while the
   **demonstration** positions give 0 % transfer under single-position intervention. Our result puts
   *both* legs on the *same* site. ⚠ This distinction is the whole of our remaining novelty on the
   conjunction, so it must be stated explicitly and defended — a reviewer who skims will read
   `2605.04061` as having done it already.
1. **`2606.08644`** — *A retrieval-conditioned rebinding circuit for dynamic entity tracking*
   (‡agent). The delegated sweep reports the binding signature lives in **Q/K subspaces (Gemma) or
   key vectors (Llama)** rather than in the position's content — a routing-flavoured hint — but
   found **no knockout/transplant dissociation**. ⇒ Downgraded from "highest-priority threat" to
   "supporting citation"; still worth a full read for the Q/K-subspace framing, which is a concrete
   hypothesis for *what* our conduit carries.
2. **`2606.13168`** — *When Does Routing Become Interpretable?* (✓fetched). Establishes a
   **dissociation between routing mass and causal importance**, and states in so many words that
   architectural exposure of routing is "necessary but not sufficient for mechanistic
   interpretation". This is the **necessary-but-not-sufficient vocabulary** applied to routing, but
   its dissociation is *attention mass vs causal effect*, not *causal effect vs state transfer*. Cite
   for the vocabulary, not for the result.
3. **`2609.01604`** — *Beyond Scores* (✓fetched, EMNLP 2026). Explicitly separates a stage where
   "attention … **routes** the result to the final input position" from a stage where "the MLP
   cascade integrates the signal and **writes** the rating". A published **route/write** division of
   labour — the same intuition, established by knockout plus logit lens rather than by a failed
   transplant.
4. **`2307.15771` The Hydra Effect** (†snippet) — the *reason* an unmatched necessity/sufficiency
   pair is dangerous: knockout of a layer causes another to compensate. Relevant here because it
   predicts that a **necessity** measurement can be an *under*-estimate; our 62 % may therefore be a
   floor, which strengthens rather than weakens the asymmetry.
5. **`2402.14811`** (†snippet) — the query-token vs object-token reading split at the last position;
   a division of labour between a positional handle and a content site, from patching.
6. **`2603.14923`** — *Directional Routing in Transformers* (‡agent). "The coordination mechanism is
   irreplaceable; the components it coordinates are not." The nearest published statement of the
   *routing-matters-more-than-content* intuition, at circuit rather than token level.
7. **`2604.04385`** — *How Alignment Routes* (‡agent). Knockout establishes a routing gate is
   necessary; injecting the gate activation restores **only 48 %** of refusals. A **partial**
   transfer where ours is null — the closest quantitative analogue, and the paper whose vocabulary
   ("activation transplant"/"overlay") is nearest to ours.
8. **`2510.06182`** — *Mixing Mechanisms* (‡agent). The published **pointer vs content** taxonomy
   (positional / lexical / reflexive retrieval), with a causal model at 95 % agreement. If our
   conduit is a pointer, this is the paper that names the category.

### 5.3b ⛔ Counterexamples we must confront, not omit

Two papers run **the same experimental pairing and get the opposite answer**, and a reviewer will
raise them:

- **`2604.22128`** — masking the single stack-top attention edge collapses accuracy, and patching
  shows the site is "not only causally necessary, but its recovery is **sufficient**". Necessity and
  transfer co-occurring at one site.
- **`2607.03502`** — *Reading Between the Dots*: **KV-cache transplants at filler positions causally
  swap outputs between examples**, at positions that look semantically empty. A store where one
  would least expect one.

⇒ These establish that our 0 % is **not** a generic property of the instrument or of token
positions. That is good for us — but only if we cite them, because they are also the strongest
evidence that a 0 % transplant *can* be an instrument failure rather than an absence of content.

### 5.4 What we could NOT determine

These three were checked by the delegated sweep and reported as **NOT** containing the shape
(‡agent confidence; I did not re-verify):

- **`2605.09239`** (*Repeated-Token Counting Reveals a Dissociation Between Representations and
  Outputs*) — a probe/output dissociation with a late MLP overwriting a decodable count; **no
  attention knockout, no transplant**.
- **`2606.29522`** — ⚠ **title changed between versions**: v1 (2026-06-28) *Do Models Read What They
  Write? Causal Registers in Scratchpad Reasoning*; v2 (2026-09-06) *When Does Activation Steering
  Change What a Model Computes From?*. v1 finds written states **are** causally used (a *store*, the
  inverse of ours); v2 reports single-layer replacement giving under 2 % of the margin gain from
  patching through all remaining layers — a transplant failure **attributed to layer scope, not to
  conduit-vs-store**. ⚠ **Directly relevant to our design**: it is published evidence that
  single-layer transplants under-dose, which is why our all-layer transplant is the right instrument
  and must be described as such.
- **`2605.25891`** (*Causal Tongue-Tie*) — encode/express dissociation, not necessity/transfer.

⛔ **Still genuinely undetermined:**

- ⚠ **OpenReview.** The delegated sweep attempted `openreview.net` HTML and both `api`/`api2`
  endpoints and was **bot-gated on every request** (`ChallengeRequiredError`). No reviewer text,
  decision or rebuttal for `tWfEMpDapM` is obtainable this way. ⇒ **The OpenReview blind spot is now
  known to be tool-inaccessible, not merely unsearched** — it needs a human with a browser, or a
  different access route. This is the fourth consecutive pass it has gone uncovered.
- Whether `2606.08292`'s body contains a per-site necessity **share** comparable to our 62 %.

---

## 6. Method to borrow for the next phase

**The requirement.** Find a representation that predicts a **continuous** semantic variable
(semantic installation), then **causally** test it. Below, three primaries and three supports, each
with an honest implementation cost.

### 6.1 ⭐ PRIMARY 1 — Continuous-variable causal intervention (`2605.29971`)

> Zhou, McCoy & Frank, *Causal Interventions on Continuous Variables: A Case Study on Verb Bias in
> Steering Vectors for In-Context Learning*, https://arxiv.org/abs/2605.29971

*The method, as stated in the abstract:* "given activation vectors paired with a graded target
variable, we localize a low-dimensional direction for that variable and use this direction to edit
vectors toward counterfactual target values", then verify that "counterfactual edits … systematically
shift downstream structural preferences."

*Why it is the right first move for us.* This is the **only** method found in any pass that is built
for a **graded** variable in an **ICL** setting, which is exactly the shape of semantic installation.
Our current tooling treats installation as a score to correlate; this converts it into a variable to
**set**. It also supplies the dose-response frame that answers the standing "you under-dosed"
objection to our nulls (`2408.15510`, `2605.18830`).

*Cost.* **Low.** We already have per-domain installation scores and per-domain activations; the
additional work is (i) fit a direction by regression rather than by difference-of-means, (ii) edit
along it to a *target value* rather than by a fixed multiplier, (iii) verify monotonicity. No new
generation compute for the fitting stage; one generation sweep per dose level for the verification
stage. Pair with **`2604.07006`** (†snippet), which treats steering strength as a continuous
experimental variable, for the dose-grid design.

### 6.2 ⭐ PRIMARY 2 — DAS / distributed interchange interventions, **with the dilemma guard** (`2303.02536` + `2507.08802`)

> Geiger et al., *Finding Alignments Between Interpretable Causal Variables and Distributed Neural
> Representations*, https://arxiv.org/abs/2303.02536 (†snippet)
> Sutter, Minder, Hofmann & Pimentel, *The Non-Linear Representation Dilemma*,
> https://arxiv.org/abs/2507.08802 (✓fetched, NeurIPS 2025 Spotlight)

*The method.* DAS learns an orthogonal rotation of the residual stream and performs a **distributed
interchange intervention** — swap k dimensions from a source input into a base input in the rotated
space, rotate back — testing whether a *distributed* subspace realises a high-level causal variable.
This is precisely the instrument for our situation: the whole-state transplant transferred ~0 %, which
is consistent either with "no store here" **or** with "the store is a low-dimensional subspace that a
whole-state swap drowns". **DAS distinguishes those two.** That is the single most valuable thing it
buys us, and our current design cannot tell them apart.

⛔ *The guard is mandatory.* `2507.08802` proves that if the alignment map is unconstrained, **any
network can be mapped to any algorithm** — they achieve 100 % IOI alignment accuracy using *randomly
initialised* language models. ⇒ **Pre-register the rotation as linear and orthogonal, pre-register k,
and run the randomly-initialised-model control as a floor.** Without that control a DAS positive is
uninterpretable, and this is now a Spotlight-level published objection.

*Cost.* **Medium-high.** DAS requires gradient-based training of the rotation, which means backward
passes through an 8B model on paired (base, source) prompts — heavier than anything in the current
pipeline, though LoRA-style low-rank rotations and single-layer targeting keep it tractable. Budget a
GPU-week including the random-init control and the `2605.18830` complementary-subspace arm. Concrete
templates exist: **`2606.16407`** (pronoun fidelity, †snippet) and **`2602.05234`** (ICLR 2026
distribution-matched variant, †snippet).

### 6.3 ⭐ PRIMARY 3 — Certified interventional fidelity (`2607.08349`)

> Asiaee, *Certified Interventional Fidelity: Anytime-Valid, Adaptive Evaluation of Causal Claims in
> Mechanistic Interpretability*, https://arxiv.org/abs/2607.08349 (UAI 2026)

*The method.* Formalise each claim as a causal estimand — "an expectation of a bounded score over a
stated input distribution **and a stated intervention distribution**" — and report **anytime-valid
confidence sequences** rather than point estimates, remaining valid under adaptive sampling.
Variance-adaptive betting sequences reduce certification cost 10–30×.

*Why we specifically need it.* Our sprint has repeatedly adapted its intervention toward suspected
failures mid-run (the DCS commit log is a record of exactly that). Anytime-valid sequences are the
only honest statistics for that workflow — with fixed-n intervals, our adaptivity is a preregistration
violation. It also forces us to write down the **intervention distribution**, which is the field's
current blind spot per `2605.08012`.

*Cost.* **Very low.** Pure re-analysis of existing runs plus a wrapper around future ones. This is
the cheapest high-value item in the report and should be adopted regardless of what else is chosen.

### 6.4 Supporting methods, cheap

| method | source | slot | cost |
|---|---|---|---|
| **LAP / `A_lin` logit-lens layer selection** — predicts steering effectiveness at ρ = +0.86…+0.91 and best layer at ρ = +0.63…+0.92; the middle-layer heuristic fails where LAP works | `2604.15557` https://arxiv.org/abs/2604.15557 | Choosing *which layer* to fit and edit at. Replaces our peak-probe-separation heuristic, which `2605.24856` already warned is the wrong criterion. | **Very low** — training-free, one forward pass per prompt |
| **Attention-level rather than residual-stream steering (GCAD)** | `2605.10664` https://arxiv.org/abs/2605.10664 | If residual-stream editing keeps under-dosing, edit the *attention contribution* instead. Directly motivated by our conduit finding: if the site routes, intervene on the routing. Also fixes KV-cache contamination over long generations. | **Medium** — new intervention code, no training |
| **Patchscopes inspection-prompt decoding** | `2401.06102` https://arxiv.org/abs/2401.06102 | A *patched* version of our concept-free readout: transplant the codeword state into an inspection prompt and let the model verbalise it. Would test whether the ~0 % transfer is a property of the state or of our receiver prompt. | **Low** — no training; reuses existing transplant code |
| **Judge calibration + κ against a second judge** | `2606.25487` https://arxiv.org/abs/2606.25487 ; `2603.10068` (†) | The ASR endpoint. Given recall as low as 0.06 across judges, report precision/recall against a human-labelled subsample, not a bare ASR. | **Low** — annotation of a stratified subsample |
| ⛔ **Matched-control transfer assay + positive control** — the instrument must be shown to detect a store when one exists | `2606.08292` https://arxiv.org/abs/2606.08292 ; `2312.10091` https://arxiv.org/abs/2312.10091 | **The conduit/store claim itself.** `2606.08292` supplies the same-answer and matched-context control design; `2312.10091` supplies the positive-control construction. **Mandatory, not optional** — see §7.1. | **Low-medium** — reuses the existing transplant harness on a new prompt pair |
| **Logit-lens rank-difference as a second graded remapping measure** | `2504.19395` https://arxiv.org/abs/2504.19395 | A convergent-validity check on the semantic-installation score, from a different instrument family. Their report that Patchscope-style methods failed where logit lens worked is a reason to have both. | **Low** — no training, forward passes only |

### 6.5 What we should NOT borrow

- **A second refusal-direction study.** `2507.11878`, `2602.02132`, `2604.08524`, `2606.13709`,
  `2603.27518`, `2604.18901` already saturate that space. Our axis is semantic, not refusal; keep it
  that way and cite `2507.11878` for the separation.
- **Attribution patching as the primary estimator.** `2606.09899` shows its dominant error comes from
  downstream non-linearity, not local curvature. If used at all, use it as a *screen* with the
  Screen-Flag-Fix workflow and verify flagged components with real patches.

---

## 7. Known pitfalls to PRE-REGISTER against

Ranked by how likely each is to bite this specific next phase.

### 7.1 ⛔⛔ P0 — **A null transplant is worthless without a positive control on the same instrument**

*This is the single most important item in this report, and it is a gap in our design, not merely a
citation.*

A 0 % transfer is cheap: it is what a broken, mis-scoped or under-dosed instrument also produces.
Three published results establish that **this exact intervention class works when there is something
to move**:

- **`2312.10091`** (Variengien & Winsor, ✓re-fetched) — mid-layer last-token-position patching
  transfers a *request* across prompts; ⚠ the widely-quoted "~100 % normalised accuracy" figure is a
  body result I did **not** verify, but the paper's positive direction is not in doubt.
- **`2607.03502`** (‡agent) — KV-cache transplants **at filler positions** causally swap outputs
  between examples; even a semantically-empty-looking position can be a store.
- **`2604.22128`** (‡agent, in matrix) — at the bracket stack-top edge, necessity **and** sufficiency
  co-occur at one site.

And the nearest prior work to ours, **`2606.08292`**, runs its own positive controls (recovering
known function vectors when writing into an underspecified prompt) **and still hedges its negative**
— explicitly noting that its controls do not prove sensitivity to the object real attention carries.

⇒ ⛔ **Pre-register a positive control before reporting the ~0 % again.** Concretely: run the
identical all-layer transplant on a prompt pair where the semantic content demonstrably *is* stored
at the target position (a function-vector or request-patching construction, per `2312.10091`), and
report its transfer rate beside our ~0 %. **Without that number, our headline finding is
unpublishable as a positive claim**, and `2606.08292` is the referee's ready-made objection.

### 7.2 ⛔ P1 — Obfuscated activations (`2412.09565`)

> https://arxiv.org/abs/2412.09565 — recall 100 % → 0 % while retaining a **90 % jailbreaking rate**;
> SAEs, representation probes and latent OOD detection all fall.

**Why it bites us specifically.** The moment we optimise *anything* against our installation
representation — a GCG-style objective, a steering target, an adversarial suffix — we should expect
the model to satisfy the behaviour while moving the representation off the axis we are reading. That
is not a null result about the representation; it is the documented behaviour of activation-space
objectives. ⇒ **Pre-register:** any optimisation against the installation axis must report the
*paired* behavioural and representational outcomes, and must include a **held-out probe trained after
the attack** to detect obfuscation. A drop in probe signal with behaviour preserved is to be reported
as *obfuscation*, not as *the representation does not cause the behaviour*.

### 7.3 ⛔ P2 — Divergent / off-distribution representations from the intervention itself (`2511.04638`)

> https://arxiv.org/abs/2511.04638 — interventions shift representations off the natural
> distribution; **pernicious** divergences activate dormant pathways and cause behavioural changes
> that are artefacts of the intervention.

Paired with **`2311.17030`** (a 1-D subspace patch can move outputs through a dormant pathway while
patching the whole containing layer does nothing). ⇒ **Pre-register:** report a distributional
distance between intervened and natural activations at the edited site, and treat any effect
accompanied by large divergence as *unattributed* until a near-distribution variant (e.g. the
Counterfactual Latent loss of `2511.04638`, or `2602.05234`'s distribution matching) reproduces it.
**This is the specific pitfall that would turn a DAS positive into an illusion.**

### 7.4 ⛔ P3 — The Hydra effect / self-repair makes necessity an under-estimate (`2307.15771`)

Knockout of a component causes others to compensate. ⇒ Our 62 % is plausibly a **floor**, and any
*additional* row we knock out may show a spuriously small marginal effect because the network has
already re-routed. **Pre-register:** for the ladder, report both the marginal effect of each added
row **and** the effect of the cumulative set, and state explicitly that single-row nulls inside the
ladder do not license "this row is not used". Combine with the 09-09 recommendation to report the
**interaction term** (`2606.27510`).

### 7.5 ⛔ P4 — Ablation-methodology sensitivity (`2407.08734`)

Faithfulness scores are "highly sensitive to seemingly insignificant changes in the ablation
methodology", and "the task a circuit is required to perform depends on the ablation used to test
it". ⇒ **Pre-register the exact ablation**: mean-ablation vs zero-ablation vs resample-ablation,
which distribution the replacement is drawn from, and whether the knockout is applied at all layers
or a band. Pair with `2309.16042` (denoising vs noising) — our knockout is a *noising* design and
our transplant is a *denoising* design, and `2408.15510` already tells us those are not comparable
in completeness. ⚠ **Our 62 % and our ~0 % are measured by two different instrument classes. That
must be stated in the paper, not buried.**

### 7.6 ⛔ P5 — Probe accuracy does not predict intervention success (`2604.15557`)

A probe can hit >93 % accuracy at every layer while steering at its best-accuracy layer produces
near-zero effect. ⇒ **Pre-register the layer-selection rule before fitting**, and use LAP/`A_lin`
rather than probe AUROC. Otherwise a null is attributable to layer choice.

### 7.7 ⛔ P6 — Unconstrained alignment maps make causal abstraction vacuous (`2507.08802`)

100 % IOI alignment accuracy from **randomly initialised** models. ⇒ **Pre-register linearity,
orthogonality and k**, and run the random-init floor. Non-negotiable if we adopt §6.2.

### 7.8 ⛔ P7 — The judge (`2606.25487`, plus `2609.00498` from the 09-09 pass)

LLM-judge recall 0.06–0.65; benign wrappers flip judges 57–100 % of the time; GCG flips 70 % of
confident classifier true positives. **A Doublespeak completion is *exactly* a case where the harmful
content is present under a benign surface** — i.e. the regime this paper shows judges handle worst,
in both directions. ⇒ **Pre-register the judge, and pre-register a human-labelled calibration
subsample stratified by domain.** Report precision and recall, not ASR alone.

### 7.9 ⚠ P8 — Identification assumptions must be written down (`2605.08012`, `2602.16698`)

The NeurIPS 2026 position track's five-point disclosure norm — state whether the claim is causal,
name the identification strategy, enumerate its assumptions, stress at least one, and say how the
conclusion shifts if it fails — should be adopted verbatim as the template for each of our claims.
"Validation is not identification."

---

## 8. Searches run this pass

**Tools:** `WebSearch` (US region) and `WebFetch` against arXiv abstract pages, plus two delegated
parallel search agents (§9). **No arXiv export-API listing was run this pass** (the 09-09 pass's
rate-limited `abs:"decodable" AND abs:"causal"` query therefore **remains unexecuted**).

| # | query family | outcome |
|---|---|---|
| 1 | attention mediates routing but residual state does not transfer / "necessary but not sufficient" | ⭐ `2606.13168`; no exact match |
| 2 | variable binding transformers binding ID in-context entity attribute | ⭐ `2310.17191`, `2409.05448`, `2606.08644`, `2505.20896` |
| 3 | sufficiency vs necessity causal interpretability activation patching | ⭐ `2605.08012`, `2603.17624` |
| 4 | distributed alignment search / causal abstraction subspace intervention | ⭐ `2303.02536`, `2507.08802`, `2602.05234`, `2511.04638`, `2602.16698`, `2606.16407` |
| 5 | attention knockout progressive ablation ladder over query positions | ⛔ **null for a position ladder**; all hits are layer ladders or VLM/video work |
| 6 | token is a pointer not a store / transplant fails / necessity without transfer | ⭐ `2605.22488`, `2605.09239`, `2605.25891`, `2606.29522` |
| 7 | activation patching pitfalls / illusion / hydra / self-repair | ⭐ `2307.15771`, `2311.17030`, `2309.16042`, `2404.15255` |
| 8 | StrongREJECT judge false positives / grader disagreement | ⭐ `2606.25487`, `2603.10068`, `2503.02574` |
| 9 | Doublespeak follow-up / replication | ⛔ **null — fourth consecutive** |
| 10 | "label words are anchors" follow-up / critique | ⛔ nothing beyond `2305.14160`, `2504.00132`, already catalogued |
| 11 | concept-free readout / indirect probing / "never names" | ⛔ **null**; nearest relative `2401.06102` Patchscopes |
| 12 | GCG on internal activation objective / latent-space target | ⭐ `2412.09565`, `2510.08604`; confirms `2607.08883` |
| 13 | probing a continuous graded variable then causal steering | ⭐ `2605.29971`, `2604.07006`, `2604.15557` |
| 14 | refusal direction dissociated from harmfulness | ⭐ `2507.11878`, `2606.08044`, `2604.18901`, `2603.27518`, `2604.09544` |
| 15 | steering→behaviour chain / probe accuracy does not predict steering | ⭐ `2604.15557`, `2607.29062`, `2602.05234` |
| 16 | arXiv 2609 / September 2026 sweep, twice | ⭐ `2609.01604` only; the September window is otherwise empty of on-target work |
| 17 | distributed vs localized concept representation across tokens | ⭐ background only; reinforces `2605.24856` |
| 18 | semantic cloaking / word substitution jailbreak internal representation | ⭐ `2510.08604`, `2508.10029` |
| 19 | path patching / attention edge knockout at a specific query row in safety | ⭐ `2609.01604`, `2304.05969`; no query-row competitor |
| 20 | causal scrubbing / faithfulness / necessity+sufficiency standards | ⭐ `2407.08734`, `2607.08349`, `2301.04709` |
| 21 | "information mover" head / token state insufficient / cross-prompt transfer failure | ⛔ **explicit null** |
| 22 | context-dependent representation / patching across prompts brittleness | ⛔ no match; steering-brittleness material only |
| 23 | graded internal score predicting per-domain ASR | ⛔ **null** |
| 24 | Doublespeak paper's own internals (`2512.03771` abstract page) | ⚠ **inconclusive from the abstract** — sweep A's full-text read reports Patchscopes; verify in-repo |
| 25 | *(sweep A)* OpenReview HTML + `api`/`api2` for `tWfEMpDapM` and cipher-mechanistic submissions | ⛔ **BLOCKED** — `ChallengeRequiredError` on every request |
| 26 | *(sweep A)* Semantic Scholar citations API for `arXiv:2512.03771` | ⭐ 4 indexed citers + 2 by snippet; OpenAlex has not indexed the paper |
| 27 | *(sweep A)* arXiv `abs:codeword AND abs:jailbreak`; `all:jailbreak AND all:"attention knockout"`; `all:"word substitution" AND all:jailbreak`; `all:"representation hijacking"` | ⛔ **zero / one-self-hit**; strong nulls |
| 28 | *(sweep A)* ICLR 2027 submissions; NeurIPS 2026 & EMNLP 2026 accepted lists | ⛔ nothing on target beyond §2.2 |
| 29 | *(sweep A)* `"semantic installation"` / `"concept remapping score"` as named internal metrics | ⛔ **no such named metric exists** in anything found |
| 30 | *(sweep B)* arXiv `abs:"conduit not a store"`; `abs:"routing" AND abs:"storage" AND abs:"token position"`; `abs:"necessary" AND abs:"does not transfer" AND abs:"attention"` | ⛔ **literal zero results, all three** |
| 31 | *(sweep B)* `"carrier not container"` / `"wire not register"` / `"channel not buffer"` / `"bottleneck token"` / `"gateway token"` + transformer interpretability | ⛔ **all null** |
| 32 | *(sweep B)* coreference/pronoun, arithmetic-operator, and ICL-demonstration variants of "attention necessary + content not stored" | ⛔ **all null** |

### 8.1 Direct fetches performed by me (24, all abstract pages)

`2605.22488`, `2606.13168`, `2606.25487`, `2605.08012`, `2412.09565`, `2507.08802`, `2507.11878`,
`2605.29971`, `2608.27504`, `2604.15557`, `2609.01604`, `2508.10029`, `2510.08604`, `2407.08734`,
`2607.08349`, `2604.04364`, `2605.10664`, `2602.07794`, `2606.08044`, `2511.04638`, `2603.17624`,
`2401.06102`, `2606.09899`, `2512.03771`.

⚠ Two fetches were **uninformative**: `2604.04364` (*Context is All You Need*) turned out to be a
domain-adaptation paper unrelated to the search snippet that surfaced it, and `2603.17624` did not
contain necessity/sufficiency operational definitions in its abstract.

### 8.2 ⚠ Unattributed lead — do not cite

A search snippet stated: *"Under prompt shifts, linear decodability degrades primarily in terms of
mean accuracy, while peak accuracy remains largely stable across contexts. Causal sufficiency drops
significantly on novel contexts."* That is a near-perfect statement of a decodability/sufficiency
split under context shift, i.e. directly on our topic. ⛔ **It could not be attributed to a paper
this session.** The candidate it appeared under (`2604.04364`) was fetched and does **not** contain
it. Recorded for a later session to chase, alongside the 09-09 pass's still-unattributed
"111 concept-model pairs / 377× median specificity ratio" snippet.

---

## 9. Delegated sweeps, and gaps that remain OPEN

### 9.1 The two delegated sweeps

Two parallel search agents were run alongside the main sweep:

- **Sweep A — OpenReview + cipher/codeword jailbreaks.** Produced §2.2 rows 3–10 and 17–20 and the
  Doublespeak citation census (§3 item 4). It attempted OpenReview directly and was **bot-gated**.
  It did reach Semantic Scholar and OpenAlex.
- **Sweep B — conduit-not-store precedent hunt.** Produced `2606.08292`, `2603.14923`, `2604.04385`,
  `2607.03502`, `2510.06182`, `2301.04213`, `2312.10091` and the verdict machinery in §5.

⚠ **I independently re-fetched and re-read four of the load-bearing rows** (`2606.08292`,
`2605.04061`, `2602.04212`, `2312.10091`). **Two corrections resulted**, both recorded above:

1. Sweep A gave `2606.08292`'s title as *"Ablation-Reversible Heads Don't Transfer: A Stress Test for
   Mechanistic Role Claims in Transformers"*. The arXiv page I retrieved gives
   **"Necessary, Decodable and Reversible, Yet Not Transferable: A Stress Test for Attention-Head
   Role Claims"**. ⇒ **Cite the title I verified.** (Likely a v1/v2 retitle, as with `2606.29522`.)
2. Sweep B attributed a "~100 % single-position request-patching transfer" figure to `2312.10091`.
   That figure is **not in the abstract** and I did not verify it. ⇒ Do not quote the number without
   opening the PDF.

⛔ **Every ‡agent row in §2.2 carries this same risk and must be opened before citation.**

### 9.2 Gaps that remain OPEN — do not treat as searched

1. **`2512.03771` full text.** ⛔ Still the highest-priority, zero-cost action. Sweep A reports from a
   full-text read that Doublespeak's transfer evidence is **Patchscopes-based**, which — if true —
   materially narrows claim (c). The PDF is in-repo at
   `doublespeak/INCONTEXT_REPRESENTATION_HIJACKING.pdf`. **Verify this directly before writing any
   novelty sentence about the readout.**
2. **`2606.08292` full text** — the nearest prior work to our headline claim, and we have read only
   its abstract. **Read next.**
3. **The three unassessed Doublespeak citers**: `2605.00583`, `2604.05273`, `2601.10294`.
4. **OpenReview** — now known to be **tool-inaccessible** (`ChallengeRequiredError` on HTML, `api`
   and `api2`). Needs a human with a browser session, or an alternative route. Fourth consecutive
   pass uncovered.
5. **arXiv export-API listings.** None run by me this pass. `abs:"decodable" AND abs:"causal"` is now
   **two passes overdue**.
6. **Full-PDF reads.** None anywhere in this pass by me. Every ✓fetched row rests on an abstract plus
   the fetch tool's extraction.
7. **ACL Anthology full-text search.** Still not used (fourth consecutive pass). Semantic Scholar was
   reached this pass, for citations only.
8. **Two unattributed snippets** (§8.2 here; §5.4 item 4 of the 09-09 file) remain unchased.
