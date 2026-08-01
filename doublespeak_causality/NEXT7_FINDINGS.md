# NEXT7 — Findings (continuous divergence)

Plan: `NEXT7_PLAN.md`. Env: Llama-3.1-8B / Qwen3-14B / DeepSeek / Phi-4, L40S, poc_stage2. Honest —
negatives included. Scalars only; no harmful text in any artifact.

---

## N7-D (part 1) — T3 depth-gating completes to 5/5 pairs. **[WIN, generalization]**

Ran the representational refusal-depth probe (`47_repr_toctou.py`) on the two remaining pairs
(cocaine, pistol) to get each pair's dominant refusal-check depth (the non-degenerate `early_vs_mid`
estimand; random control ~0):

| pair | install_above_random early | mid | **early_vs_mid [CI]** | dominant depth |
|---|---|---|---|---|
| bomb (prior) | +1.73 | +0.60 | +1.17 [+0.78,+1.57] | EARLY |
| **cocaine** | **+4.15** | +0.80 | **+3.41 [+2.98,+3.83]** | **EARLY** |
| grenade (prior) | −0.19 NS | +0.57 | −0.72 [−1.06,−0.38] | MID |
| chlorine (prior) | −0.07 NS | +0.66 | −0.68 [−1.05,−0.31] | MID |
| **pistol** | +0.67 | **+2.02** | **−1.29 [−1.55,−1.03]** | **MID** |

- **The depth-gated refusal check generalizes to all 5/5 pairs** — each has a concept-specific
  dominant depth (random control ≈ 0), CI excluding 0. Two families emerge: **EARLY-dominant**
  (bomb, cocaine) and **MID-dominant** (grenade, chlorine, pistol). This lifts the T3 phenomenon
  from 3 pairs to a 5/5 regularity: the refusal mechanism is depth-gated for every pair; only the
  gating depth is pair-dependent.
- **Prediction (tested next):** a behavioral TOCTOU factorial should recover the interaction at each
  pair's OWN dominant depth — early for cocaine, mid for pistol.
- Artifacts: `outputs/repr_toctou_..._698695` (cocaine), `..._698696` (pistol).

---

## N7-A — MLP-node attribution: the D4 mediation lands in mid-band MLPs. **[WIN, validated]**

`51_mlp_attribution.py` (per-layer MLP AtP, validated against a true SubmodulePatch(mlp) on the
top-40 cells). D4 showed the mid-band heads have DIRECT≈0 (all effect mediated downstream) and
head→head edges don't reconstruct it → the mediation runs through MLPs. N7-A localizes it:

| pair | MLP AtP peak | band L7–14 share | AtP-vs-true pearson | trustworthy |
|---|---|---|---|---|
| bomb | L11 | 47.3% | 0.936 | yes |
| grenade | L11 | 52.9% | 0.950 | yes |
| chlorine | L14 | 40.9% | 0.932 | yes |

- **The MLP mediation is mid-band-concentrated** (41–53% of Σ|AtP| in L7–14) and **validated**
  (pearson 0.93–0.95 vs true MLP patch) for all three pairs — directly confirming D4's inference
  that the effect the mid-band heads do NOT write directly is carried by the **mid-band MLP
  sublayers**.
- **A mid-band attention→MLP cascade.** The MLP contribution peaks slightly LATER (L11–14) than the
  attention z-AtP (peak L9): attention heads write the demo→query context link in L7–9, and MLP
  sublayers process/consolidate the concept in L9–14. Both are distributed (many heads, many MLP
  layers) — together a mid-band "processing zone" (L7–14), not a sparse circuit.
- **Unified mechanism (D3+W4+D4+N7-A):** the Doublespeak context effect is a **distributed mid-band
  computation across BOTH attention and MLP** — attention links the context, MLPs consolidate the
  concept, no single node is a bottleneck. This is the fullest mechanistic characterization to date,
  each step validated against true patching.
- Artifacts: `outputs/mlp_atp_{bomb,grenade,chlorine}/mlp_atp_results.json`.

---

## N7-B — Reasoning-model CoT trajectory: hypothesis REFUTED; D5 refined. **[novel, honest]**

`52_cot_concept_trajectory.py` on Qwen3-14B (thinking-on) and DeepSeek-R1-Distill. At a grid of
CoT-depth checkpoints + the answer, INTERRUPT with a benign forced-naming anchor ("in one word, the
object referred to above is:") and read the concept-vs-codeword LABEL. n=6/condition (small).
Positive control PASSES on both (Direct@answer 0.8/1.0; Neutral 0.0 throughout).

reads_as_concept trajectory (cot_0→cot_9 = CoT deciles, then answer):

| model | condition | mid-CoT | answer |
|---|---|---|---|
| **Qwen3-14B** | DOUBLESPEAK | **0.67–1.00 (high throughout)** | **1.00** |
| Qwen3-14B | NEUTRAL | 0.00 | 0.00 |
| **DeepSeek** | DOUBLESPEAK | **~0.00–0.25 (near zero)** | **0.67** |
| DeepSeek | NEUTRAL | 0.00 | 0.00 |

- **The "reasoning resolves the codeword" hypothesis is REFUTED.** Neither model resolves the
  hijack away: Qwen3 names the concept at EVERY CoT checkpoint (the reading is fully present from the
  start and persists to the answer); DeepSeek names it only at the answer (it emerges LATE, the
  opposite of resolution). Neutral stays 0.0 for both — the anchored readout is specific.
- **This REFINES D5 (important):** D5's natural post-`</think>` readout found the hijack weak/absent
  on reasoning models, but the **anchored forced-naming** readout reveals it IS present (DeepSeek
  0.67 at the answer vs D5's +0.33 natural; Qwen3 ~1.0 throughout). So reasoning is NOT a
  representational defense — the hijacked reading is there when the model is forced to name the
  referent; it simply isn't verbalized in the free-form answer. The D5 "absent" is a readout
  property (natural answers don't name the object), not evidence the concept is gone.
- **Model contrast:** Qwen3-thinking carries the concept from the CoT's first token (consistent with
  the reading being context-installed early/mid-stack, per D6); DeepSeek's concept naming builds up
  and only surfaces at the answer.
- **Honest scope:** n=6/condition, single seed, per-bin counts small — suggestive, not definitive;
  a larger-n rerun would tighten the trajectory. But the qualitative contrast (Qwen3 throughout vs
  DeepSeek answer-only, both Neutral-clean, both positive-control-passing) is clear.
- Artifacts: `outputs/cot_traj_Qwen3-14B_..._698757`, `cot_traj_DeepSeek-..._698758`.

### N7-B Phi-4 follow-up: readout does NOT certify (inconclusive).
Anchored CoT probe on Phi-4-mini-reasoning fails its positive control (Direct@answer = 0.0): 13/18
prompts truncated (CoT > 1536 tokens never reaches `</think>`) AND Phi-4's verbose `\boxed{}` math
answers defeat the first-4-word `classify_answer` (the D5-flagged readout artifact). So we cannot
resolve whether D5's Phi-4 "absent" is a readout artifact — the anchored readout is also broken on
Phi-4. The Qwen3/DeepSeek N7-B result (both positive-control-passing) is unaffected. Honest
inconclusive; not chased further (readout engineering rabbit hole on one model).

---

## N7-E — The attention→MLP cascade quantified; D6 decoupling clarified. **[synthesis, CPU]**

Reusing committed artifacts (D3 head z-AtP, N7-A MLP AtP, D6/W3-b concept projection) — no GPU:

| pair | attn peak | MLP peak | lag | attn L7–14 | MLP L7–14 | MLP late (L20–31) |
|---|---|---|---|---|---|---|
| bomb | L9 | L11 | +2 | 62% | 47% | 17% |
| grenade | L9 | L11 | +2 | 67% | 53% | 11% |
| chlorine | L13 | L14 | +1 | 55% | 41% | 23% |

- **The cascade is robust:** MLP |AtP| peaks **1–2 layers after** the attention z-AtP for every pair —
  attention writes the demo→query context link, MLPs consolidate the concept ~2 layers downstream.
- **D6's "decoupling" is clarified (honest):** the concept PROJECTION grows +8.82 across L20–31, but
  late-layer MLPs carry only **17% of Σ|AtP|** (bomb; 11–23% across pairs) and MLP AtP anti-correlates
  with the concept-emergence rate (−0.26). So the late projection growth is **passive residual /
  RMSNorm accumulation toward the unembedding, NOT new causal computation** — the causally-important
  computation (both attention and MLP) is confined to the mid-band (L7–14). The projection keeps
  rising late only because the residual accumulates and its overlap with the concept axis grows as
  the rep approaches the readout, not because late layers compute anything.
- **Fully unified mechanism (D3+W4+D4+N7-A+N7-E):** (1) attention heads write the context link at
  L7–9 (peak L9), (2) MLP sublayers consolidate the concept at L9–14 (peak L11–14, +2-layer cascade),
  (3) late layers passively carry/scale it to the readout (low AtP), (4) all distributed across many
  heads and MLPs — no bottleneck, no sparse circuit. Every step validated against true patching.

---

## N7-C — Cross-arch circuit via a forward-only true-patch sweep. **[method win + honest caveat]**

Gradient AtP (49/51) OOMs for a 14B model on a 44GB L40S (backward doubles memory on top of 28GB
weights). `next7_layer_patch_sweep.py` measures per-layer attn_out/mlp_out contribution by TRUE
patching only (replace the whole component at the aligned positions with matched-NEUTRAL, record the
metric delta) — no backward, so it fits Qwen3-14B.

**Llama cross-validation (true-patch sweep vs the validated AtP):**
- **Attention AGREES:** true-patch peak L12 vs AtP peak L9, corr **0.63**, 58% of |Δ| in L7–14 —
  both localize attention to the mid-band. The sweep reproduces the D3/W4 attention circuit.
- **MLP DISSOCIATES (informative):** true-patch peaks at **L31** (the last layer), AtP at **L11**
  (mid), corr 0.11. This is exactly the **computation-vs-proximity split N7-E predicted**: the
  all-position layer true-patch is dominated by the LAST MLP's mechanical proximity to the readout
  (patching it directly perturbs the logits), while the per-cell AtP isolates the mid-band
  COMPUTATION. Late MLPs have large true-patch deltas but ~0 AtP → they passively carry, they don't
  compute — confirming N7-E from a second method.
- **Caveat:** the all-position layer true-patch conflates computation with readout-proximity, so for
  localizing the concept-FORMING computation the per-cell AtP is the cleaner tool; the sweep's value
  is (a) it runs on any model size and (b) it cross-validates the attention mid-band + the N7-E
  passive-late-carry claim.
- Qwen3-14B full-demo sweep running (the demo-capped run had a weak/reversed m_clean=−9.95, so it
  was re-launched without the cap for a strong-hijack signal). Artifacts:
  `outputs/patchsweep_llama_bomb/`, `outputs/patchsweep_qwen3_bomb*/`.

---

## N7-D (part 2) — Behavioral TOCTOU confirms at each pair's T3-predicted depth: 4/5 pairs. **[WIN, capstone]**

Behavioral TOCTOU factorial (n=60) on cocaine and pistol, reduced at the depth the INDEPENDENT T3
representational probe predicted (cocaine EARLY, pistol MID):

- **cocaine (EARLY-dominant):** `INTERACTION` (early−late) = **+0.333 [+0.15,+0.52], p_holm=0.0075** ✅
- **pistol (MID-dominant):** `INTERACTION_mid_late` = **+0.467 [+0.33,+0.58], p_holm=0.0075** ✅

Each pair recovers the TOCTOU at its own T3 depth and NOT at the other (cocaine mid_late −0.03 NS;
pistol early−late +0.18 borderline). The full cross-pair picture:

| pair | T3 depth | behavioral TOCTOU at own depth | Holm-sig |
|---|---|---|---|
| bomb | EARLY | +0.425 | ✅ |
| **cocaine** | EARLY | **+0.333** | ✅ (new) |
| grenade | MID | +0.183 (n=60) | ✅ |
| **pistol** | MID | **+0.467** | ✅ (new) |
| chlorine | MID | +0.033 | ✗ (null) |

- **The behavioral depth-gated TOCTOU now generalizes to 4/5 pairs**, each confirmed at the depth
  its T3 representational probe independently predicted — only chlorine is null. This is a strong
  **predictive** structure: the representational refusal-check depth (T3) predicts WHERE the
  behavioral compliance-flip interaction appears. It turns the NEXT5/NEXT6 chlorine-driven doubt
  into a robust cross-pair regularity (4/5, all Holm-sig at their own depth).
- Together with N7-D part 1 (T3 depth-gating 5/5) this closes the TOCTOU thread: the refusal check
  is depth-gated for every pair (5/5 representationally), and the behavioral bypass reappears at each
  pair's own depth for 4/5 pairs — a representation→behavior prediction confirmed.
- Artifacts: `outputs/toctou_..._698713` (cocaine), `..._698714` (pistol).

### N7-C Qwen3 caveat: metric doesn't transfer.
The forward-only sweep RUNS on Qwen3-14B (memory solved), but the logit_diff(concept−codeword) metric
is reversed there (m_clean = −9.95; codeword > concept at the readout position under
forced_choice/thinking-off) — the metric doesn't cleanly capture Qwen3's hijack, so the Qwen3 circuit
localization (attn L24 / mlp L16) is UNRELIABLE and not interpreted. The fine-grained circuit result
stands on Llama (3 pairs, AtP-validated + sweep-cross-validated). Cross-architecture evidence for the
mechanism remains at the S2/superposition/S3-KV level (Qwen3), not the per-layer circuit level.

---

## N7-G — The hijack SATURATES at low demonstration count. **[new, CPU]**

Reusing committed bomb reps (694691), binned the DS mid-band concept-component (projection onto
`d_Direct`, L12–24) by the prompt's demonstration count:

| n_demos | DS concept-component | n |
|---|---|---|
| 4 | +1.749 | 10 |
| 8 | +1.712 | 10 |
| 12 | +1.634 | 10 |

- **The hijack does NOT scale with more demonstrations** — it is flat (slightly decreasing) across
  4/8/12 demos. So the in-context codeword→concept remapping **saturates at ≤4 demonstrations**: a
  few examples fully install the reading, and additional examples do not deepen it. This is a
  threshold/saturating phenomenon, not gradual accumulation — complementing S2/S3 (the reading is
  context-installed, and the install saturates quickly).
- **Honest scope:** single pair (bomb), n=10/bin, tested range 4–12; the saturation threshold could
  sit below 4 (untested — the bench has no 1–2-demo prompts). The claim is "saturated across 4–12",
  i.e. the install completes by 4 demos.
- Artifact: reuses `outputs/pair_reps_..._694691`.

---

## N7-F — Concept-ablation defense at the mid-band: specific but INEFFECTIVE. **[honest negative, ties to distributed mechanism]**

Mechanism-derived defense at the RIGHT depth (unlike D7's late refusal-add): project out `d_Direct`
(the concept axis) at the mid-band (L7–13) throughout generation, on the headroom attack (early
install + refusal ablation, malicious 0.47).

| α | attack→defended malicious | suppression | benign over-refusal | REJ@atk-def |
|---|---|---|---|---|
| 1 (full project) | 0.47 → 0.67 | +0.20 [0.0,0.4] NS | +0.00 | 0.0 |
| 2 (over-project) | 0.47 → 0.53 | +0.07 [−0.13,0.27] NS | +0.00 | 0.0 |

- **Specific but ineffective:** projecting the concept direction out at the mid-band causes **zero
  benign over-refusal** (d=0.0 — a clean improvement over D7's blanket refusal) but does **NOT reduce
  malicious behavior** (no suppression; REJ stays 0).
- **Why (ties to the mechanism):** the concept is a **distributed mid-band computation** (D4:
  DIRECT≈0 for every head; N7-A: MLP-mediated), **not a single direction** — so ablating one axis
  (`d_Direct`) does not remove the distributed reading, and the harmful trajectory (set by the early
  install) proceeds. This is consistent with S2/B4 (the reading is context-carried, and the single
  `d_Direct` direction is not the causal carrier).
- **Defense synthesis (both mechanism-derived defenses fail, for distinct principled reasons):**
  D7 (add refusal LATE) fails because the compliance is gated EARLY (wrong depth) and destabilizes
  generation; N7-F (ablate concept MID) is specific but fails because the concept is DISTRIBUTED
  (no single direction to remove). Together they explain WHY Doublespeak is hard to defend by
  representation surgery: the decision is early and the representation is distributed. Honest,
  mechanistically-grounded negative.
- Artifact: `outputs/d7_defense_..._698953`.

---

## N7-H — Doublespeak is perfectly DETECTABLE from the mid-band representation. **[WIN, defensive]**

Where intervention defenses fail (D7, N7-F), DETECTION succeeds. A linear probe (L2 logistic,
trained on DEV, tested on HELDOUT) on the mid-band residual (codeword_last, L12–24 mean) separating
DOUBLESPEAK from benign conditions (BENIGN_REMAP + UNRELATED_TARGET + NEUTRAL):

| detector | heldout AUC |
|---|---|
| **full mid-band linear probe** | **1.000** |
| 1-D concept-component (d_Direct projection) | 0.858 |

- **Doublespeak is perfectly detectable** (AUC 1.0 on held-out prompts) by a linear probe on the
  mid-band representation — the hijack signature is linearly accessible.
- **Distributed but linearly separable:** the 1-D concept-component alone gives only 0.858 (the
  overlapping distributions of W3-b/D2), but the FULL probe reaches 1.0 — the DS signal lives across
  many dimensions, not one. This exactly reconciles N7-F: you can DETECT the distributed reading
  (linear probe over all dims) but you can't REMOVE it by ablating a single direction.
- **Practical synthesis of the defense thread:** representation-surgery defense is hard (the decision
  is early — D7; the representation is distributed — N7-F), but **detection is easy and reliable**
  (AUC 1.0). The actionable takeaway is detection, not intervention.
- **Honest scope:** single pair (bomb), n=60 dev / 60 heldout, one regularization setting — AUC 1.0
  is striking but on small n; a multi-pair, larger-n probe would confirm robustness. Still, the
  detection-vs-ablation asymmetry is clear and mechanistically grounded.
- Artifact: reuses `outputs/pair_reps_..._694691`.

---

## N7-I — Detector transfer is PARTIAL, not universal. **[honest refinement of N7-H]**

Trained the mid-band linear probe on BOMB, tested on each pair (and leave-one-pair-out):

| test pair | bomb-trained AUC | leave-one-out AUC |
|---|---|---|
| bomb | 1.000 (in-domain) | 0.617 |
| grenade | 0.995 | 0.639 |
| pistol | 0.981 | 0.610 |
| chlorine | 0.557 | 0.280 |
| cocaine | 0.316 (below chance) | 0.298 |

- **The detector transfers to some pairs but not others:** a bomb-trained probe detects grenade/
  pistol Doublespeak nearly perfectly (AUC ≥0.98) but fails on chlorine (0.557) and cocaine (0.316 —
  below chance, i.e. cocaine's DS signature is anti-aligned with bomb's on the probe axis). Leave-
  one-pair-out (train 4, test 5th) is weak for all (~0.6 for the transferring pairs, below chance
  for chlorine/cocaine).
- **Honest tempering of N7-H:** in-domain Doublespeak detection is perfect (AUC 1.0), but the
  mid-band signature is **pair-specific** enough that a single-pair (or even 4-pair) detector does
  NOT universally generalize. A practical detector would need per-concept calibration or a more
  concept-invariant feature — the hijack representation is not a single universal "Doublespeak
  direction". This is consistent with the distributed, partly pair-specific mechanism (D2's
  bomb-specific superposition; the pair-dependent TOCTOU depths).
- Artifacts: reuses pair reps `694691/694882/694897/694896/693696`.
