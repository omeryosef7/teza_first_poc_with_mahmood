# Doublespeak — Complete Causal Mechanism (synthesis of NEXT5–NEXT7)

Paper: *In-Context Representation Hijacking* / Doublespeak (arXiv:2512.03771). Primary model
Llama-3.1-8B-Instruct; cross-arch on Qwen3-14B. Pair CARROT↔BOMB (+ grenade/chlorine/pistol/cocaine).
This reorganizes ~35 gated results (source docs: `NEXT_CAUSAL_SPRINT`/`STAGE*`, `NEXT5/6/7_FINDINGS.md`)
into one thematic account. Every quantitative claim is backed by a committed artifact; negatives and
confounds are included. Labels: **[causal]** intervention, **[repr]** representational, **[val]**
validated against true patching, **[neg]** negative/limitation.

---

## 1. The end-to-end mechanism (four validated stages)

The Doublespeak reading is **not stored in the codeword's local state** — it is computed by the
receiver context, and that computation resolves into a distributed mid-band pipeline:

**(0) Retrieval — induction-like token-identity attention.** The query codeword attends preferentially
to the earlier occurrences of the SAME token (the demo codewords, which the demos bind to the
concept): demo-codeword vs count-matched random attention = **3.5×** (bomb), 3.5× (grenade), 3.3×
(chlorine) in the mid-band — pair-general (it operates on the shared codeword). This induction
retrieval explains the install's codeword-specificity (§3). [repr; N7-L]

**(1) Write — mid-band attention (L7–9, peak L9).** Per-head z-attribution (validated vs true
per-head z-patch, pearson 0.97–0.99 on 3 pairs) localizes the attention contribution to L7–14, peak
L9; 55–67% of Σ|AtP| in the band. Distributed across many heads (top-20 = 12% of total); no single
head has a direct-to-logits path (DIRECT≈0 in path patching). [val; D3, W4, D4]

**(2) Consolidate — mid-band MLP (L9–14, peak L11–14).** MLP-layer AtP (validated vs true
SubmodulePatch(mlp), pearson 0.93–0.95 on 3 pairs) concentrates in L7–14 (41–53%), peaking 1–2 layers
AFTER the attention writes — a robust attention→MLP cascade. This is where the effect the heads do
NOT write directly (DIRECT≈0) is carried. [val; N7-A, N7-E]

**(3) Carry — late layers are passive.** The concept PROJECTION keeps growing late (L20–31, +8.8), but
late MLPs carry only 11–23% of Σ|AtP| (anti-correlated with the emergence rate). A forward-only
true-patch sweep confirms the split: late MLPs have large *mechanical* patch effects (proximity to the
readout) but ~0 AtP (no computation). The late growth is residual/RMSNorm accumulation toward the
unembedding, not new computation. [val; N7-E, N7-C]

**Cross-cutting: distributed, not sparse.** No single layer (per-layer knockout), head (D4 DIRECT≈0),
or head→head edge (D4 path-patch reconstruction fails) is a bottleneck. The mechanism is a
distributed mid-band attention→MLP computation. [D4, W4, N7-C]

**The dissociation headline (S2):** state×context transplant — IE_state ≈ 0 (equivalence, all depths,
4/4 pairs), DE_context ≈ 99% of the total effect on Llama, 92% on Qwen3-14B; self-transplant
faithfulness exactly 0. The reading is a function of the receiver context, causally independent of the
local codeword activation. [causal; S2, cross-arch Qwen3]

---

## 2. Superposition — the codeword rep carries codeword AND concept

The DS codeword-position rep loads BOTH a codeword axis and a concept axis (per-layer projection). The
concept component is DS-SPECIFIC (above benign-remap controls) for bomb on BOTH Llama (+0.55) and
Qwen3-14B (+8.96, cross-arch), but NOT for grenade/chlorine/pistol (NS vs benign remap) — the
concept axis for those pairs captures generic remap structure. So both of the paper's §3.4 hypothesized
mechanisms are now tested: TOCTOU causally (§4), superposition representationally. [repr; W3-b, D2]

---

## 3. Nature of the install — a specific, saturating in-context binding

- **Codeword-specific:** replacing the query word with a NOVEL benign word (banana/table/pencil) drops
  the concept-reading from 0.70 to ≈0 (vs neutral floor). The demos bind ONE codeword; a novel word is
  not captured — because retrieval is by token-identity attention (§1.0). [N7-K, 3 words]
- **Saturating:** the mid-band concept-component is flat across n_demos 4/8/12 — ≤4 demonstrations
  fully install the binding. A threshold, not gradual accumulation. [N7-G]
- **Not a trivial re-read:** neutralizing the demonstration K/V removes only ~9% on Llama (91%
  survives), more on Qwen3 (46% removed). Distributed/robust. [S3]

---

## 4. TOCTOU — the refusal check is depth-gated (representation predicts behavior)

- **5/5 representational:** the refusal check is depth-gated concept-specifically for all 5 pairs, at a
  PAIR-DEPENDENT depth — EARLY {bomb, cocaine}, MID {grenade, chlorine, pistol} (T3 early_vs_mid CIs
  exclude 0). [repr; S4, T3, N7-D pt1]
- **4/5 behavioral:** the behavioral compliance-flip interaction reappears at each pair's OWN
  T3-predicted depth — bomb +0.425, cocaine +0.333, grenade +0.183, pistol +0.467 (all Holm-sig);
  only chlorine null. The representational depth PREDICTS the behavioral effect location. [causal;
  S4, W1, N7-D pt2; Holm families]
- **Depth timeline:** concept @ early-check depth ≈0.18 vs @ late-use depth ≈4.1 = 22.5× gradient —
  the early check reads a near-benign residual; the harmful concept materializes downstream. [D6]

---

## 5. Reasoning models carry the hijack

An anchored forced-naming CoT probe: Qwen3-thinking names the concept throughout its CoT AND at the
answer (robust at n=12); DeepSeek is weak (~0.33 at answer). Reasoning does NOT resolve the codeword —
D5's natural-readout "absent" was a readout property, not concept resolution. [N7-B]

---

## 6. Defense vs detection

- **Intervention defense fails, for two principled reasons:** adding refusal LATE (D7) targets the
  wrong depth (compliance is gated early) and destabilizes generation; ablating the concept direction
  at the mid-band (N7-F) is specific (0 benign over-refusal) but ineffective (the concept is
  distributed, not one direction). [neg; D7, N7-F]
- **Detection is easy in-domain:** a mid-band linear probe detects Doublespeak with AUC 1.0 on Llama
  AND Qwen3. [N7-H]
- **But not universal:** cross-pair transfer tracks concept-axis alignment (corr 0.86) → harm-category
  semantics (weapons transfer to weapons, a drug does not). The detector detects the pair-specific
  concept direction, not a universal "Doublespeak-ness" axis. [N7-I, N7-J]

---

## 7. Honest negatives / confounds / limitations

- **B4:** the in-house `d_Direct` "+0.971 install" does not reproduce (+0.03) — strengthens S2 (no
  local intervention installs the reading). [neg]
- **Patchscope (T2/N3):** fails its positive control for bomb — consistent with IE_state=0. [neg]
- **N7-M:** all-layer induction-edge knockout is degenerate (disrupting attention raises p_concept as
  an artifact) — inconclusive; the clean induction evidence is the pattern (N7-L). A surgical
  induction-head path-patch is future work. [neg]
- **Cross-arch circuit:** the per-layer AtP/sweep metric (logit_diff at the prompt's final position)
  does not transfer to thinking models (Qwen3/Phi-4 predict `<think>` there). The fine-grained circuit
  is Llama-only; cross-arch evidence is at the S2/superposition/S3/detection level. [neg]
- **Phi-4 3rd architecture:** the Doublespeak hijack is weak/absent at its answer position (readout
  does not certify — truncation + math verbosity). [neg]
- **Effect sizes are modest** (DS reading ~0.35); the dissociation is relative and robust.

---

## 8. One-paragraph summary

Under a Doublespeak prompt, an **induction-like attention head** at the query codeword attends back to
the demonstration codewords and retrieves the in-context binding; **mid-band attention (L7–9) writes**
this demo→query link and **mid-band MLPs (L9–14) consolidate** the harmful concept, which **late layers
passively carry** to the readout. The computation is **distributed** (no single head/layer/MLP
bottleneck) and the reading is a property of the **receiver context**, not the codeword's local state
(IE_state≈0, DE_context≈99%). The install is a **specific, saturating** codeword→concept binding
(≤4 demos, one codeword). The safety failure is a genuine **time-of-check/time-of-use bypass**: the
refusal check is depth-gated EARLY (or at a pair-specific depth) where the concept is still ~0, while
the harmful concept only fully forms downstream — confirmed representationally (5/5 pairs) and
behaviorally (4/5). The attack **resists representation-surgery defense** (early decision + distributed
representation) but is **linearly detectable in-domain**, though detection is concept-specific, not
universal.
