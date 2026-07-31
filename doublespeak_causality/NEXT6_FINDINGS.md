# NEXT6 — Findings ("all new directions")

Plan: `NEXT6_PLAN.md`. Env: Llama-3.1-8B / Qwen3-14B / Phi-4 / DeepSeek, L40S, poc_stage2,
forced_choice. Honest — negatives included. Scalars only; no harmful text in any artifact. Single
Holm family across all new NEXT6 inferential claims (assembled at the end).

---

## D6 — Unified depth timeline: superposition + circuit + TOCTOU as one story. **[WIN, synthesis]**

Reusing three committed artifacts (W3-b per-layer projections, W4-B z-AtP by layer, T3 refusal
depth) — no GPU — the Doublespeak mechanism resolves into a single depth timeline on bomb/Llama
(`next6_d6_depth_story.py`, `outputs/next6_depth_story.json`):

- **Codeword-first, concept-lagging superposition.** The codeword component leads (present from
  L2: codeword@L2–6 = +0.28 vs concept@L2–6 = +0.15) and both grow together thereafter — the rep
  carries the codeword identity from the start and the harmful concept accretes on top, exactly the
  superposition picture (W3-b), now resolved across depth.
- **TOCTOU as a monotonic concept-emergence gradient [the key quantitative result].** The concept
  component at the EARLY refusal-check depth (bomb's check is early, T3) is **+0.183** (L0–9 mean);
  at the LATE use depth it is **+4.124** (L20–end mean) — a **22.5×** gradient. So the refusal check
  reads a residual in which the harmful concept is ~22× weaker than where it is finally used: the
  codeword still "looks benign" when checked, and the concept only fully materializes downstream.
  This quantifies the paper's §3.4 TOCTOU bypass as a clean, monotonic depth gradient (not just an
  early/late binary), and mechanistically explains why the early-gated refusal is bypassed.
- **Attention writes the context-link mid-band (L7–14, peak L9 = 61.7% of Σ|AtP|)** — where heads
  causally move the demonstration context into the query's readout path (W4-B).
- **Honest nuance — write-band and concept-growth are DECOUPLED.** The attention WRITE band (mid)
  does NOT coincide with where the concept PROJECTION grows fastest: corr(z-AtP write[L], concept
  emergence[L→L+1]) = **−0.30** (excl. the mechanical readout jump). The concept projection rises
  fastest LATE (near the unembedding), after the attention writes have tapered. Interpretation: the
  mid-band attention establishes the demo→query context LINKAGE (consistent with S2 "context
  supplies the reading"), but the concept REPRESENTATION keeps accumulating downstream through the
  residual/MLP stream — the causal write and the readable projection live at different depths. We
  report this rather than force a "they align" story.
- **Synthesis:** one timeline unifies all four results — S2 (context supplies the reading
  progressively, not stored locally early), superposition (codeword+concept coexist, codeword-first),
  the mid-band distributed circuit (where attention links context), and TOCTOU (early check sees
  concept ≈0.18, late use sees ≈4.1 → 22.5× bypass gradient).
- Artifact: `outputs/next6_depth_story.json`. Code: `next6_d6_depth_story.py`.

---

## D2 — Superposition generalization: bomb-specific but CROSS-ARCHITECTURE. **[nuanced / honest]**

Ran `next5_w3b_superposition.py` on grenade/chlorine/pistol (Llama, fixed band L12–24) and bomb on
Qwen3-14B (band L15–30, proportional). DS-specific = DS concept component above the benign-remap
control (the load-bearing superposition claim).

| pair / model | DS loads both? | DS−BENIGN concept [CI] | DS-specific? |
|---|---|---|---|
| **bomb / Llama** | yes | **+0.555 [+0.26,+0.87]** | **YES** |
| **bomb / Qwen3-14B** | yes | **+8.96 [+6.39,+11.63]** | **YES (cross-arch)** |
| grenade / Llama | yes | +0.078 [−0.23,+0.38] | no |
| chlorine / Llama | yes | +0.215 [−0.11,+0.54] | no |
| pistol / Llama | yes | −0.110 [−0.43,+0.21] | no |

*(Integrity note: an initial chlorine/pistol run accidentally paired the pair's reps with GRENADE's
`d_Direct` directions — a reps↔directions dir suffix collision caught by the NEXT6 artifact-map
workflow. Numbers above are the CORRECTED runs (chlorine reps 694897 + dir 694897; pistol reps
694896 + dir 694896), validated by the strong in-pair DIRECT positive control (concept +13.3/+14.1).
The conclusion — not DS-specific for these pairs — is unchanged from either pairing.)*

- **Co-loading is universal:** every pair's DS rep loads BOTH the codeword and concept axes (both
  CIs exclude 0) — the basic superposition geometry is general.
- **DS-specific concept elevation is a BOMB property that CROSSES ARCHITECTURES.** Only bomb shows
  the concept component elevated above the benign-remap control — and it does so on **both** Llama
  (+0.55) and Qwen3-14B (**+8.96**, even stronger). For grenade/chlorine/pistol the DS concept-axis
  loading is statistically indistinguishable from a benign remap (all NS vs BENIGN) — i.e. the
  concept axis `d_Direct` for those pairs captures generic "codeword-is-remapped" structure that any
  remap shares, not a DS-specific harmful-concept component.
- **Honest reading:** this mirrors the recurring pattern (S4/T3) that bomb is the strongest, cleanest
  hijack — the DS-specific superposition is a bomb property, but a robust one (replicates on a second
  architecture). The non-generalization to other Llama pairs is reported honestly; a pair-specific
  band (analogous to T3's pair-dependent depths) is untested future work (avoided here to prevent
  post-hoc band-tuning / double-dipping).
- Artifacts: `w3b_superposition.json` in each pair's reps dir (`..._694882/883/884`, Qwen3 `..._695832`).

---

## D3 — Circuit generalization: the mid-band head circuit REPLICATES across pairs. **[WIN]**

z-AtP head map (`49_head_attribution.py`) on grenade + chlorine (heldout, validated against true
per-head z-patch), compared to bomb (NEXT5 W4-B):

| pair | peak layer | band L7–14 share of Σ\|AtP\| | AtP-vs-true pearson | trustworthy |
|---|---|---|---|---|
| bomb | L9 | 61.7% | 0.969 | yes |
| grenade | L9 | 66.6% | 0.988 | yes |
| chlorine | L13 | 55.1% | 0.970 | yes |

- **The validated mid-band (L7–14, peak L9–13) circuit generalizes to all three pairs** — each is
  trustworthy (pearson 0.97–0.99 vs true per-head z-patch) and mid-band-dominant (55–67% of total
  |AtP|). So while the SUPERPOSITION specificity is bomb-only (D2), the CIRCUIT localization — where
  attention heads causally contribute to the concept readout — is a **general** property of the
  Doublespeak mechanism on Llama, distributed across many mid-band heads for every pair.
- This strengthens the NEXT5 W4-B result from single-pair to a cross-pair regularity, and reinforces
  the D6 depth story (mid-band attention writes the demo→query context link for all pairs).
- Artifacts: `outputs/head_attr_..._697370` (grenade), `..._697371` (chlorine).

---

## D4 — Path patching: NOT a sparse attention-head circuit (rules out head→head edges). **[negative that sharpens the mechanism]**

`50_path_patching.py` (new `FreezeAllHeadsExcept`/`FreezeMLP`/`ZHeadPatchMulti`, exploiting o_proj
linearity to freeze all non-sender components) on bomb, top-8 mid-band heads (L7–14) from the z-AtP
map. Validated in a linear toy (4/4 tests, completeness identity exact). On the real model:

- **Every mid-band head has a large TOTAL true-patch effect but DIRECT ≈ 0.** TOTAL (single-head
  true patch, logit_diff, m_clean=1.23): L9h19 −2.89, L10h27 −1.30, L11h24 −1.16, L12h6 −1.06,
  L13h0 +0.92, L10h24 +0.48, L9h17 +0.64. DIRECT (sender→logits with ALL other heads+MLPs frozen):
  **−0.03 … +0.06 for every head** (essentially zero). → no mid-band head writes directly to the
  logits; each head's entire effect is **mediated through downstream computation**.
- **The head→head EDGE decomposition does NOT reconstruct TOTAL** (median rel_err 1.006 ≫ tol 0.15,
  `recon_ok=False`) → the mediation runs through components the head-only path patch freezes out
  (MLPs and multi-hop residual paths), NOT through direct sender-head→receiver-head edges. Per the
  gate, the edge matrix is **not interpreted**; only the exact TOTAL/DIRECT single-head deltas are.
- **Mechanistic conclusion (honest):** the Doublespeak context effect is **not a sparse
  attention-head circuit**. The mid-band heads matter (large TOTAL) but act entirely through
  downstream MLP/residual computation (DIRECT≈0), and their pairwise routing is not
  edge-decomposable. This converges with D3 (distributed across many heads) and W4 (no single-layer
  or single-head bottleneck): a distributed, MLP-involving mid-band computation, not a tidy circuit.
- Gate: correctness gate PASSED (linear-toy exactness); on-model recon gate FAILED → fall back to
  TOTAL/DIRECT (the designed, honest fallback). Artifact: `outputs/path_patch_..._697419/`.

---

## D5 — Phi-4-mini-reasoning 3rd architecture: readout certifies, hijack ABSENT. **[honest negative]**

`31 --answer-marker '</think>'` on `microsoft/Phi-4-mini-reasoning` (a genuinely distinct non-Llama
reasoning architecture; Phi3ForCausalLM). forced_choice DIRECT positive control PASSES (pos=1.0,
neg=0.0), so the post-`</think>` readout method certifies on Phi-4 too.
- **The Doublespeak hijack does NOT manifest on Phi-4:** gated `DS−Neutral reads_as_concept =
  +0.000` [0,0] (n=5–6 usable cells), all-cell DS reads-as-concept = 0.095 — i.e. Phi-4 reads the
  codeword as the codeword, not the concept, at the answer position. Transplant not run (no effect).
- **Cross-architecture pattern (both reasoning models):** DeepSeek-R1-Distill (weak, +0.33 n=6 NS)
  and Phi-4-mini-reasoning (absent, +0.00) both fail to show the hijack at the post-`</think>`
  answer position, while Llama-3.1-8B (non-thinking readout, +0.50) and Qwen3-14B
  (thinking-suppressed, +0.69) show it strongly. A consistent, honest observation: the
  Doublespeak reading is present in these reasoning models' prompts but does not survive to the
  answer through their chain-of-thought — a plausibly meaningful robustness property worth noting.
  The primary dissociation stands on **2 architectures** (Llama + Qwen3).
- Artifact: `outputs/pair_readout_Phi-4-mini-reasoning_..._697414/readout_summary.json`.

---

## D7 — Defense redo (with headroom): the late/use-depth defense FAILS. **[honest negative, mechanistically informative]**

`next6_d7_defense_redo.py`. Fixed W5's two flaws: (1) attack-with-headroom (recreate 45's cell-D:
install concept EARLY + ablate refusal → malicious 0.5, real headroom, matching 45's 0.53); (2)
small-α {2,4,8} + full {EMPTY,MALICIOUS,REJECTED,BENIGN} split + degeneration guardrail. Defense =
re-add the refusal axis ONLY at the late/use layers (24,26,28,30) in the same ExitStack.

| α | attack→defended malicious | suppression [CI] | benign over-refusal | REJ@atk-def |
|---|---|---|---|---|
| 2 | 0.50 → 0.47 | −0.033 [−0.17,+0.10] NS | +0.233 | 0.067 |
| 4 | 0.50 → 0.53 | +0.033 [−0.10,+0.17] NS | +0.267 | 0.033 |
| 8 | 0.50 → 0.47 | −0.033 [−0.27,+0.17] NS | +0.433 | 0.100 |

- **The mechanism-derived defense does NOT work even with headroom.** Re-adding refusal at the
  late/use layers gives no malicious suppression at any α (all NS, |δ|≤0.03), does NOT re-engage
  refusal on the attack (REJ stays ~0.03–0.10), and imposes large benign over-refusal (+0.23 to
  +0.43).
- **Why (the informative part):** the Doublespeak malicious COMPLIANCE is gated EARLY — the concept
  must be installed early to be caught by (and then released from) the early refusal check (early
  install → 0.5 malicious; a late-installed concept escapes entirely → 0.07, NEXT5 W1). So the
  behavioral decision is set at early depth, and re-adding refusal at LATE layers is **too late** to
  intervene — the compliance is already determined upstream. This refutes the "harm emerges late →
  defend late" hypothesis for the BEHAVIORAL attack and reinforces the TOCTOU depth structure (the
  action is early). (The D6 late concept-PROJECTION growth is a readout-space phenomenon; the
  compliance gate is early — an honest distinction.)
- **Verdict:** mechanism-derived late-depth defense is a **negative**; a defense would have to act at
  the early check depth (i.e. simply not ablating the early refusal), which is not a novel
  intervention. Reported honestly. Gate: FAIL (no α suppresses; over-refusal high). Artifacts:
  `outputs/d7_defense_..._697705` (early, headroom) and `..._697454` (late, no headroom — first run).

---

## D1 — Per-pair TOCTOU at n=60 (verified dirs): grenade CONFIRMS, chlorine is NULL. **[refines W1; integrity]**

Reran the TOCTOU factorial at n=60 (bench max) with VERIFIED-correct directions (grenade dir 694882,
chlorine dir 694897 — after the D2/D3 reps↔dir collision was caught). Re-reduced `INTERACTION_mid_late`.

| pair | n | INTERACTION_mid_late [CI] | p | vs committed n=40 |
|---|---|---|---|---|
| **grenade** | 60 | **+0.1833 [+0.0667,+0.3000]** | **0.008** | strengthened (n=40 was +0.125, CI incl 0) |
| chlorine | 60 | +0.0333 [−0.0667,+0.1171] | 0.73 | **does NOT reproduce** (n=40 was +0.15, CI excl 0) |
| **POOLED** | 120 | **+0.1083 [+0.0333,+0.1833]** | **0.012** | still significant, but **grenade-driven** |

- **Grenade robustly confirms** the per-pair-timing TOCTOU at its own MID depth (n=60, p=0.008, CI
  excludes 0) — the strongest single-pair behavioral confirmation.
- **Chlorine is NULL** with a verified-correct direction (+0.033, p=0.73). The committed NEXT5 W1
  chlorine number (+0.15, CI excluded 0) **does not reproduce** at n=60 — whether from the
  reps↔directions collision or n=40 sampling noise, the authoritative result is null for chlorine.
- **The pooled interaction remains significant** (+0.108, p=0.012, n=120) but is now understood as
  **grenade-driven**, not "both mid-dominant pairs."
- **Honest revision to NEXT5 W1:** the per-pair-timing TOCTOU generalizes **robustly to grenade**
  (and bomb at early depth), but **NOT to chlorine**; the pooled significance holds but should not be
  read as "both pairs." This tempers the W1 "win" to a grenade+bomb result with an honest chlorine
  null. Artifacts: `outputs/toctou_..._697392` (grenade), `..._697405` (chlorine).
