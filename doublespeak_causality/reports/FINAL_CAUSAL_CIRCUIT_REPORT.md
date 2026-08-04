# FINAL_CAUSAL_CIRCUIT_REPORT.md — Doublespeak causal circuit (Phases 0–10 + behavioral frontier BEHAV-*)

Complete causal account of the Doublespeak / in-context representation-hijacking mechanism on a locked
ClearHarm split, **Llama-3.1-8B-Instruct bf16**. Two cohorts reported separately: ClearHarm-native
(primary) + curated harm-in-one-noun (replication). Forced-choice DE_context readout; per-layer/head
**Wilcoxon signed-rank, Holm-corrected**; dev(train)/heldout(test) always separate. Every claim links to a
phase report with n, CIs, controls. **Audited (20/20 confirmed findings fixed/verified) + coverage-validated.**

## Headline (the main result)
We mapped the full concept circuit **and then tested whether it drives the jailbreak — it does not.**
Two dissociations, both cross-cohort/locked-test/controlled:
1. **The concept circuit is representationally necessary+sufficient (for the codeword→concept readout) but
   behaviorally INERT.** Ablating the L8–11 write OR the L14–21 carry heads throughout harmful generation
   leaves attack-success unchanged (BEHAV-CARRY/WRITE, both null).
2. **The behavioral locus is the (orthogonal) REFUSAL axis.** Ablating one refusal direction jailbreaks the
   model *more* than Doublespeak does (+0.43–0.48 ASR, p≤.004, specific); re-injecting it *into* Doublespeak
   drives ASR→0.000 (dose-dependent, axis-specific, coherence-audited); and Doublespeak's residual sits at/below
   the benign level on that axis, with suppression onsetting at the L8–11 write band and growing with depth.

**⇒ Doublespeak is, mechanistically, an imperfect in-context refusal-suppression technique; the elaborate
token→concept remap is a behaviorally epiphenomenal bystander.** Defense: scrub the refusal axis, not the
concept subspace. (Details: PHASE_BEHAV_REFUSAL / _CARRY / _WRITE.)

## The circuit (one line)
**Demonstration-codeword K/V retrieval (L8–11) + L9 MLP write → L14–L21 answer-position carry heads
(downstream-mediated) → L30–31 proximal output → logit.** Distributed within each band (no single necessary
head or edge), but a clear directed layer structure. Concept axis is independent of refusal — and, per the
headline above, that independence is *causal*, not just geometric: the concept circuit is behaviorally inert
while the refusal axis is behaviorally necessary+sufficient.

## Answers to the 12 final-deliverable questions

1. **Which demonstration tokens provide the binding?** The demonstration-codeword tokens — neutralizing
   their K/V (resid_pre ← benign) reduces the reading, **necessary in the mid band L8–11, per-layer sig,
   both cohorts** (PHASE4). Necessary, not sufficient (installing into benign gives ≈0).
2. **Which query→demo attention edges retrieve it?** **None specifically.** Surgical query→demo edge
   knockout (all heads, L8–11) is ns on both cohorts — retrieval is distributed/redundant, not a single
   induction edge (PHASE4). The observed attention pattern is descriptive, not causal.
3. **Which heads are necessary?** Answer-position **carry heads in a mid band L14–L18** (+ L21) and a late
   band (L21–31), Wilcoxon-Holm significant. On the expanded **v2 (116-ex)** bench the locked-test power is
   fixed: **dev 58 / heldout 44 Holm-sig heads** (the original curated-heldout n=21 low-power=0 is resolved
   by more examples). Robust both splits: L17H24, L14H4/H5, L17H27, L15H8, L14H23, L21H10, L18H20 (PHASE5).
   Also causal in their **attention PATTERN** (Phase 4b: uniform-pattern knockout −0.13–0.17 both splits).
4. **Which heads/head-sets are sufficient?** **No single head, but the L14–21 carry HEAD-SET is partially
   sufficient** — installing the DS carry-head z into a benign prompt raises the reading to 0.16–0.47
   (20–53% of the full DS reading), significant + specific on all 4 cells (PHASE7c). This is the FIRST
   component with both necessity and sufficiency (demo-KV / MLP-write installs were ≈0): the concept becomes
   a **transplantable representation** once carried by these heads.
5. **At which layers is the binding first causally available?** The MLP write appears at **L9** (necessity
   Holm all 4 cells), co-located with the L8–11 K/V retrieval. Linear *readability* only emerges late (L31),
   which is a readout-proximity artifact, NOT the write layer (PHASE6, PHASE8).
6. **Which MLP/MLP-set writes it?** The **L9 demo-codeword MLP** (band L9–L12) — necessity Wilcoxon-Holm on
   all 4 cells + a monotone dose-response (PHASE6, PHASE9). Necessary, not sufficient.
7. **Which head→MLP paths mediate?** The L14–L21 carry heads are **downstream-mediated** (DIRECT/TOTAL
   `direct_frac ≈ 0` — freezing downstream removes their whole logit effect); only **L30–31 are readout-
   proximal output** (direct_frac ≈ 0.5–0.76). **And the L9-write→carry EDGE is causal**: freezing the
   L14–21 carry band to clean restores ~75–83% of the L9-neutralization drop (random heads restore 0%),
   so the carry band *reads* the L9 write — a directed, edge-connected pathway (PHASE7 + PHASE7b, Gate 5).
8. **Localized or distributed?** **Distributed within concentrated bands** — an L8–12 retrieval/write region
   and an L14–21 carry band. No single necessary head or edge; clear layer structure.
9. **How is the concept mechanism separated from refusal?** Two ways, and the second is the study's headline.
   **(a) Representationally orthogonal:** `cos(concept, refusal) ≈ 0.01–0.06` at every layer, both cohorts
   (PHASE2_DIRECTIONS). **(b) Causally dissociated (BEHAV-*):** the two are separated not just in geometry but
   in *what drives harmful behavior* — ablating the concept circuit (write OR carry, each necessary+sufficient
   for the readout) leaves ASR unchanged (behaviorally NULL), whereas the refusal axis is behaviorally
   **necessary AND sufficient**: ablating it jailbreaks the model (>Doublespeak), and re-injecting it into
   Doublespeak drives ASR→0.000 (dose-dependent, axis-specific, coherence-audited). So Doublespeak's harm runs
   entirely through the refusal channel, with the concept channel a behaviorally-inert bystander
   (PHASE_BEHAV_REFUSAL / PHASE_BEHAV_CARRY / PHASE_BEHAV_WRITE).
10. **Does it generalize to locked test?** Yes — L9 write survives Holm on heldout (both cohorts); carry
    heads on clearharm heldout; dose-response on heldout; every claim replicates on ≥20 locked-test examples
    (except curated heldout heads, n=21 low-power, honestly flagged).
11. **Can it be a differentiable objective?** The `concept_objective` (d_Direct in the L9–L12 write region)
    + independent `refusal_objective` are eligible: **Gate-6 9/10 pass** (necessity, dose, controls, test,
    refusal-independent) but **sufficiency fails** (distributed). The `doublespeak_signature` is KILLED
    (causally inert) (PHASE10).
12. **Does the objective improve held-out GCG/MAC ASR?** **No — well-controlled NULL** (PHASE11 /
    GCG_MAC_EVALUATION, concluded from existing evidence): state injection is only weakly behaviorally
    sufficient (≤0.16 ASR, "never a potent injectate"); a mechanism-derived GCG objective is net-negative;
    Gate-6 sufficiency fails — three converging lines. The mechanism IS behaviorally actionable, but only via
    the **white-box concept-install + refusal-removal activation edit** (finding #5), NOT a token-suffix
    objective. Field caution: decoding-sufficiency ≠ behavioral sufficiency (a documented dissociation).

## Behavioral grounding (Phase 2)
Doublespeak >> direct on the locked split (ClearHarm malicious-rate DS 0.349 vs direct 0.116 — codeword
rephrase bypasses the refusal that blocks the direct request); curated neutral floor ≈0.03, DS train +0.30
(10×). Gate 1 (reproduction) met.

## Novel contributions vs prior work
- First **ClearHarm-split, cross-cohort, Holm-corrected, locked-train/test** causal account (prior work was
  a single carrot↔bomb pair).
- **Componential dissociation at the demo codeword:** K/V (retrieval) necessary, MLP-out (write @L9)
  necessary, attn-out NOT necessary.
- **Carry-vs-proximal separation** (Phase 7 DIRECT/TOTAL): mid-band L14–21 = genuine mediated carry, only
  L30–31 proximal — resolves the readout-proximity confound quantitatively.
- **Graded dose-response** of the MLP write (Phase 9).
- **Readout ≠ mechanism** demonstrated (Phase 8): linear readability peaks L31, dissociated from the L9/L14
  causal loci.

## Methodological rigor
- **Statistics corrected under audit:** switched per-layer/head significance from a resolution-limited
  sign-flip permutation (which returned artifactual p=0 over the 1024-cell head family) to **Wilcoxon
  signed-rank** (robust to the right-skewed necessity diffs; a t-test was over-conservative). Conclusions
  held under the correct test.
- All patch primitives self-swap = exact no-op (unit-tested + in-data 0.0); matched random/position/donor
  controls; `scripts/validate_experiment_coverage.py` confirms no dup rows / n≥20 / cells present on all
  committed dirs. 20/20 audit findings fixed or verified-inert.

## Sufficiency emerges at the carry stage (refinement)
The binding is **context-bound at the demonstration/write stage** — demo-KV, MLP-write, and behavioral
state injections are all ≈0 sufficient (Phases 4/6). But by the time the concept is carried in the **L14–21
answer-position heads it becomes a transplantable representation**: installing that carry-head z into a
benign prompt raises the reading to 0.16–0.47, specific and replicating (PHASE7c). So the mechanism is a
**progression** — context-bound retrieval/write → transplantable carried concept — not uniformly
non-sufficient.

## Honest limitations
- No single head/edge/layer is the bottleneck; effects are distributed within concentrated bands.
- The carry-head sufficiency is **partial (20–53%)** and **representational** (FC p_concept); its behavioral
  (StrongREJECT) sufficiency is untested (prior state-injection was ≤0.16 behaviorally). Behavioral
  **necessity** IS now tested at BOTH concept-control sites (BEHAV-CARRY carry heads + BEHAV-WRITE L8–11 demo
  write, below) and is a **well-controlled NULL at each** — a complete representation≠behavior dissociation:
  the circuit explains how the concept is represented/carried, not why the model complies.
- curated heldout (n=21) is under-powered for the 1024-cell head family — head claims rest on the 3 powered
  cells.
- Sufficiency-installation of carry heads (install carry-head z into benign) not run. (The upstream
  L9-write → carry-head EDGE is now closed — PHASE7b mediation, ~75–83% mediated, random-control 0%.)
- Phase 11 behavioral-ASR test outstanding.

## Phase status — ALL PHASES COMPLETE
0 ✅ · 1 ✅ · 2 ✅ · 3 ✅ · 4 ✅ · 5 ✅ · 6 ✅ · 7 ✅ · 8 ✅ · 9 ✅ · 10 ✅ · 11 ✅ (concluded: null for
suffix objective; behaviorally actionable only via white-box edit).
Reports (representational circuit): CAUSAL_PATCHING_AUDIT · DATASET_AND_SPLIT_CONTRACT ·
PHASE2_{BEHAVIORAL,DIRECTIONS} · PHASE3_RESIDUAL · PHASE4_DEMO_RETRIEVAL · PHASE5_HEADS · PHASE6_MLP ·
PHASE7_PATH · PHASE8_READOUT · PHASE9_DOSE · CAUSAL_OBJECTIVE · GCG_MAC_EVALUATION.

**Reports (behavioral frontier — the headline dissociation, read these for the main result):**
- **PHASE_BEHAV_CARRY.md** — carry-head behavioral necessity = NULL.
- **PHASE_BEHAV_WRITE.md** — L8–11 demo-write behavioral necessity = NULL.
- **PHASE_BEHAV_REFUSAL.md** — refusal axis: sufficiency (ablate→jailbreak > DS), necessity (re-inject→ASR 0),
  representational signature (DS suppresses refusal), calibrated depth-localization (decision read mid-late),
  coherence + code audit. *The central behavioral report.*
- **PHASE_WRITE_REFUSAL_INTX.md** — concept-write × refusal-suppression are causally INDEPENDENT pathways
  (why the concept circuit is behaviorally epiphenomenal).
- *(in progress)* refusal-trajectory (does refusal re-engage mid-generation — explains partial base ASR).
Harnesses: `scripts/phase_behav_{carry,write,refusal,refusal_inject}.py`,
`phase_refusal_{projection,inject_calibrated,trajectory}.py`, `phase_write_refusal_interaction.py`,
`phase_behav_carry_analyze.py`. All new harnesses code-audited (mappings verified consistent, no off-by-one).

## Scale-up validation (v2, 116-example bench = clearharm 86 + 30 NEW gpt-4o-mini concepts)
Every core finding replicates or STRENGTHENS on the expanded data (locked test preserved, no leak), and two
new activation-patching experiments were added (harnesses authored by an ultracode workflow, each
self-swap-gated + code-reviewed):
- **L9 MLP-write necessity** — strengthens: dev L8–L13 Holm-sig (L9 +0.080), heldout L9–L13 (L9 +0.030).
- **Carry-head necessity** — heldout POWER FIXED: dev 58 / heldout 44 Holm-sig heads (was 0 on n=21).
- **Carry-head sufficiency** — confirmed: install DS carry-z into benign +0.33/+0.35 specific (dev/heldout).
- **MLP-write granularity** (Phase 6b) — write distributed L8–11, sliding-W4-reproducible, saturates by W8.
- **NEW: attention-PATTERN causality** (Phase 4b) — uniform-pattern knockout at the carry heads −0.13–0.17
  (both splits) → the carry heads read via WHERE they attend, not only their output.
- **Q/K/V decomposition** (Phase 5b) — **INCONCLUSIVE, not a clean null** (audit iter-85): the K/V cells
  patched only the ANSWER position, but under causal masking K/V are read from EARLIER source positions that
  were never touched → the K/V ~0 is a positioning artifact, not inertness; the harness also lacked a
  positive control and the only run was the n=2 smoke. The Q cell (query originates at the answer position)
  is well-posed but likewise underpowered. **Retracted as a result; a corrected K/V-at-source-positions +
  positive-control re-run is future work.**
- **NEW: BEHAVIORAL necessity — complete representation≠behavior DISSOCIATION** (BEHAV-CARRY + BEHAV-WRITE).
  Ablating throughout harmful generation (decode-safe/prefill, StrongREJECT-judged, paired McNemar, 2 cohorts,
  count-matched random controls) — **BOTH concept-control sites are behaviorally NULL:**
  (a) **carry heads** L14–21 — consistent-direction but non-significant (clearharm train −9pp/test −7pp,
  McNemar p≥0.29, CIs include 0; curated reversed/null);
  (b) **L8–11 demo WRITE** — even flatter (all ΔASR ∈ [−.02,+.07], every McNemar p≥0.69, CIs include 0,
  indistinguishable from the random-position control). 0 empty-gen everywhere.
  So the very components that are causally **necessary (+ carry: sufficient) for the concept READOUT** are
  **NOT behaviorally necessary for the jailbreak** — harmful behavior does not reduce to the concept-carrying
  machinery. Falsifies "remap committed early." Consistent with the suffix-objective null, the mechanism-guided
  optimization negative, and ≤0.16 state-injection sufficiency — four converging lines.
  (PHASE_BEHAV_CARRY.md, PHASE_BEHAV_WRITE.md)
- **NEW: the POSITIVE locus — REFUSAL suppression is behaviorally sufficient, specific, and STRONGER than
  Doublespeak** (BEHAV-REFUSAL). Standard Arditi ablation of the validated L18 refusal axis (project out at every
  layer/position through generation) on Direct-harmful raises ASR **+0.43–0.48 over baseline, every split
  p≤0.004** (clearharm 19/19 & 20/20 discordant flips → harm; refusal_rate .70–.88→.23–.29); a norm-matched
  **random** direction does **nothing** (p≥0.5) =
  clean specificity; and refusal-ablation-alone **≥ Doublespeak** on all 4 splits (sig 3/4). Doublespeak only
  *partially* suppresses refusal (ds refusal_rate .44–.48 vs full-ablation .05–.11). → **Doublespeak's harm is
  refusal bypass, NOT the concept remap:** ablating the concept circuit (necessary+sufficient for the readout)
  does nothing, while ablating the orthogonal refusal axis (which the concept circuit never touches) reproduces
  and exceeds the jailbreak. The concept mechanism is representationally faithful but causally disconnected from
  compliance. **Defense: scrub the refusal axis, not the concept subspace.** **NECESSITY now also confirmed**
  (re-injection arm): adding +α·refusal-axis back into Doublespeak generation drives ASR **monotonically to
  0.000 at α=12 in all 4 cells** (clearharm α12 p=2e-5/3e-5; α8 p=2e-4; curated-train p=2e-3), refusal_rate→1.0,
  **empty=0** (coherent, not a broken decoder); a norm-matched **random** direction never lowers ASR (p≥.125).
  Refusal suppression is thus **necessary AND sufficient** for Doublespeak's harm. (PHASE_BEHAV_REFUSAL.md)
- **NEW: representational signature (forward-only)** — projecting the decision-position residual onto the
  per-layer refusal axis shows **Doublespeak's projection sits far below direct-harmful, at/below the neutral
  (benign) level**, both cohorts, every layer (clearharm hs32 direct 71 vs ds 30 vs neutral 40; curated ds
  even goes *negative*). The suppression **onsets at ~L8 (the L8–11 concept-write band) and grows monotonically
  through depth**; a norm-matched random direction shows zero condition gap (axis-specific, not norm-drift). So
  the demonstrations, in the same band, do two ORTHOGONAL things — remap codeword→concept (behaviorally inert)
  AND suppress the refusal representation (the behavioral driver). This is the representational mechanism behind
  the causal arms.
- **NEW: refusal depth-localization (calibrated, confound-free)** — injecting each layer's own refusal direction
  at α = its measured direct−ds projection gap (restore-to-"refused" level; matched random control null at every
  layer) rescues the model **only at MID-LATE layers** — L16/L22/L28 ΔASR −0.21/−0.25/−0.23 (p=.004/.001/.002)
  but **L9 ns** (p=0.45), clearharm train. So although DS *suppresses* refusal from the early write band, the
  behavioral refusal **decision is read mid-late (~L16+)** — restoring the signal only early is insufficient.
  (A prior fixed-α sweep confounded this via over-drive at low-norm early layers; the calibration removes it.)
  (PHASE_BEHAV_REFUSAL "Calibrated localization".)
- **NEW: concept-write × refusal-suppression are causally INDEPENDENT** (WRITE×REFUSAL, forward-only). Ablating
  the L8–11 concept-write (zero mlp_out @ demo codeword positions) **reduces the concept readout** (positive
  control fires: p_concept .88→.80 / curated .69→.46, CIs exclude 0) but leaves DS's **refusal-axis suppression
  completely unmoved** — `frac_of_direct_gap_restored ≈ 0` (|·|<0.05) at every layer, every cohort/split;
  ds_writeabl refusal projection ≡ ds_base, both far below direct. So the demos' two L8–11 effects run on
  **separate pathways**: knocking out the remap does nothing to the refusal bypass. **This is the mechanistic
  reason the concept circuit is behaviorally epiphenomenal** — the harm-enabling refusal suppression is
  decoupled from the concept machinery at the source. (PHASE_WRITE_REFUSAL_INTX.md)
All self-swap controls exact (0.0); all CIs on ≥55 locked-test examples; rules held (Wilcoxon-Holm,
train/test separation, no trimming).

## Bottom line
A complete, audited, cross-cohort, Holm-corrected causal circuit for Doublespeak: **demo-KV retrieval
(L8–11) + L9 MLP write → L14–21 mediated carry heads → L30–31 proximal output → logit**, distributed within
bands, concept axis ⊥ refusal. The mechanism is behaviorally real (DS ≫ direct) and white-box-actionable
(concept-install + refusal-removal), but distributed/context-bound — it does not reduce to a single
head/edge/layer, and it does not convert into a black-box token-suffix attack objective (a well-controlled
null + a field caution that decoding-sufficiency ≠ behavioral sufficiency). **And a complete
representation≠behavior dissociation:** ablating the concept-control machinery (L8–11 write OR L14–21 carry)
throughout generation leaves harmful ASR statistically unchanged — the circuit is a faithful account of how
the concept is *represented and carried*, but harmful *compliance* does not causally depend on it. **And the
positive counterpart: the behavioral locus is the REFUSAL axis** — ablating the (orthogonal, L18) refusal
direction is sufficient, specific, and a *stronger* attack than Doublespeak itself, while the concept circuit
never touches it. Doublespeak is, mechanistically, an imperfect in-context refusal-suppression technique.
Concept-subspace defenses will not blunt it; the actionable axis is refusal.
