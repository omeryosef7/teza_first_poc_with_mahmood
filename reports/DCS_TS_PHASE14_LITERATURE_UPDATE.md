# PHASE 14 — literature update, and what it says about PHASE 9 *before* PHASE 9 runs

*2026-09-07. Mandate §31 lists "literature update" under PHASE 14; `A-046` recorded it as the one
outstanding component. This is it.*

**Provenance caveat, stated first.** These are search results plus one full-text fetch
(`arXiv:2311.17030`), summarised. I have **not** read every paper end to end, and one summary came
from a small model. Nothing below is used as a measurement or a threshold — it is used to say what
is already known about the *method* PHASE 9 uses, and every design consequence I draw is checkable
against our own artifacts. Where I state a number from our own data, it is ours and sourced.

---

## 1. The finding that bounds a POSITIVE result

**Makelov, Lange & Nanda, "Is This the Subspace You Are Looking for? An Interpretability Illusion
for Subspace Activation Patching"** (`arXiv:2311.17030`).

This paper is about **exactly the intervention H2a performs**: patching or projecting along a
subspace found by difference-in-means or a probe. Its claim is that such an intervention can
produce a real behavioural effect *without* the subspace being the thing the model uses — the
effect can run through **dormant or disconnected features** that correlate with the behaviour in
the fitting distribution but sit off the causal path, with the observed change coming from
distribution shift rather than from disrupting the mechanism.

**Consequence for us, and it is not a small one.** A *positive* H2a result would NOT by itself
establish that `v_bomb_specific` is causally used. This must be written into the interpretation
**before** the run, because after the run it reads as explaining away an inconvenient result.

Our design already carries two of the recommended controls, which is worth stating plainly:

- **H1, the full-state patch, is run first as an upper bound.** Comparing a subspace intervention
  against full activation patching at the same site is the central sanity check this literature
  asks for, and PHASE 9's launch order (`H1 → H2`, with H2 not submitted at a site where H1 does
  not move O2) implements it.
- **C1 and C4** — norm-matched random, and an equal-magnitude edit along an orthogonal direction —
  separate "this direction matters" from "this much perturbation at this site matters".

What we do **not** have: cross-model replication (Llama-3.1-8B-Instruct only, by decision — Qwen3-14B
is absent from both caches under `HF_HUB_OFFLINE=1`), and any test of whether the subspace has a
direct downstream connection rather than a circuitous one. Both are scope limits on a positive, and
they are now recorded as such.

## 2. The finding that predicts our S1 arm

**"Single-Position Intervention Fails: Distributed Output Templates Drive In-Context Learning"**
(`arXiv:2605.04061`) reports single-position activation intervention achieving **0% task transfer
across all 28 layers of Llama-3.2-3B, despite 100% probing accuracy at those same positions**.

That is the same model family, the same dissociation, and the same intervention geometry as our
**S1** (one position, one depth). It predicts S1 nulls.

Our preregistration already treats this correctly and I want that on the record as foresight rather
than hindsight: `scope_levels` declares S1 and S2 as **distinct hypotheses**, not two measurements
of one quantity, with the interpretation written in advance — *"S1 negative with S2 positive means
the direction is used but redundantly encoded across depth."* The literature says that is the
expected shape. It also means **an S1 null is close to uninformative** on its own and must not be
reported as "the direction is not used".

## 3. The findings that license the sentence the mandate wants

**"Dissociating Decodability and Causal Use in Bracket-Sequence Transformers"** (`arXiv:2604.22128`)
and **"When Decodability Is Not Enough: Logical Validity Representations, Behavioral Dissociation,
and Causal Tests in Language Models"** (`arXiv:2609.02438`) both establish the pattern our mandate
§32 calls valuable: representations linearly decodable at high accuracy while probe-derived
directions have little specific causal effect on behaviour.

So **"decodable but not causally used under this intervention" is an established finding shape, not
a consolation prize.** That is worth knowing before we run something whose most likely outcome is a
null. It does not lower the evidentiary bar for *our* null — see §5.

## 4. The attack literature our object of study sits in

**"In-Context Representation Hijacking"** (`arXiv:2512.03771`) describes an attack it calls
**"Doublespeak"**: a token's meaning is dynamically and covertly overwritten mid-inference, with
internal-representation analysis used to explain the mechanism. The stated safety consequence is
that input-layer keyword checks and static refusal directions are insufficient, motivating
"representation-aware" defences.

This is the closest published neighbour to what this project studies, and it changes what our
results are *for*: our contribution is not "doublespeak exists" but the **measurement discipline
around whether the remapped representation is actually used** — plus two negative results this
literature does not report, `R-112` (the signal is not localised at the codeword; a control nine
tokens downstream decodes at 0.9261 vs 0.9446) and `R-116` (on a concept-free channel, two of three
concepts never install at all).

## 5. Where the literature and our own adversarial review CONVERGE — and why both PHASE 9 outcomes are bounded

The adversarial review of the PR-053 direction export
(`reports/DCS_TS_PR053_DIRECTION_EXPORT_ADVERSARIAL_REVIEW.md`) measured two things from our own
exported vectors that combine badly with §1:

- **`cos(v_knife, v_gun) = 0.91–0.95` at every layer in the band.** The two subtracted terms are
  **one generic demonstration-presence axis measured twice**, not two independent concept controls.
  `v_bomb_specific` carries a −0.55 to −0.68 loading on that generic axis and only 0.22–0.44 cosine
  with `v_bomb`.
- **Projecting the axis out removes only 4.7–19.0% of the cell-mean spread, leaving 78–96% of
  `v_bomb` intact.**

Put beside the literature, this is the honest statement of PHASE 9's evidential ceiling:

| outcome | what bounds it |
|---|---|
| **H2a positive** | `arXiv:2311.17030` — a subspace effect need not mean the subspace is used; and the axis is substantially *generic demonstration presence*, not concept identity, so even a genuine effect is not attributable to identity content |
| **H2a null** | the realised dose is **4.7–19.0%** of the cell-mean spread with most of `v_bomb` still present. A null under that dose is **weak evidence of non-use**, and must never be published without the dose attached |
| **S1 null** | `arXiv:2605.04061` — single-position nulls are the *expected* result even where information is fully decodable |

The payload's `meta.interpretation_warning` currently guards **only the null**. The review's sharpest
point is that this is asymmetric: a positive is *equally* unattributable to identity content. That
asymmetry must be fixed in the interpretation, and it is a preregistration-integrity matter — a
caveat that only fires against the result you did not want is not a caveat.

**None of this is a reason not to run PHASE 9.** It is a reason to state the ceiling in advance. The
sentence this phase can support is bounded, and it is better to know the bound now than to write it
after seeing which way the result went.

## 6. What this changes in the design, concretely

1. Any PHASE 9 null is published **with `frac_cellmean_spread_removed` attached**, in the same
   sentence, never as a bare "no effect".
2. Any PHASE 9 positive is published with the illusion caveat and the generic-axis loading, and
   does **not** on its own license "the concept-identity direction is causally used".
3. An S1-only null is reported as **uninformative**, not as evidence of non-use.
4. `meta.interpretation_warning` should be made symmetric — it currently reads only against a null.
5. The Llama-only scope limit is now also a **literature-relative** limit (`arXiv:2311.17030` asks
   for cross-model consistency), not merely a resourcing note.

**Sources**

- [Is This the Subspace You Are Looking for? An Interpretability Illusion for Subspace Activation Patching](https://arxiv.org/pdf/2311.17030)
- [Single-Position Intervention Fails: Distributed Output Templates Drive In-Context Learning](https://arxiv.org/html/2605.04061)
- [Dissociating Decodability and Causal Use in Bracket-Sequence Transformers](https://arxiv.org/pdf/2604.22128)
- [When Decodability Is Not Enough: Logical Validity Representations, Behavioral Dissociation, and Causal Tests in Language Models](https://arxiv.org/html/2609.02438)
- [In-Context Representation Hijacking ("Doublespeak")](https://arxiv.org/pdf/2512.03771)
- [Causal Probing for Internal Visual Representations in Multimodal LLMs](https://arxiv.org/html/2605.05593)
- [Knowing Isn't Always Saying: When Do Spatial Encodings Reach Answers in Vision-Language Models?](https://arxiv.org/html/2608.22916)
