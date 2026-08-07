# The Refusal-Suppression Circuit — Consolidated Synthesis (§34 paper-facing)

**Scope.** This document integrates the sprint's **VERIFIED / NULL** refusal-suppression-circuit results into
one coherent, paper-facing section. It reports only closed evidence; anything still in flight is marked
**PENDING** and is not used to support a claim. Every number is traced to a committed run directory. Single
model throughout: **Llama-3.1-8B-Instruct**, bf16, greedy, StrongREJECT judge (MALICIOUS iff score ≥ 0.25).
Cohorts are **not exchangeable** (generated Doublespeak is net-negative) and are reported per-cohort, never
pooled as the headline.

Source reports: `P_REFUSAL_SUPPRESSION_LOCALIZATION.md` (§3 Gate A), `P_GATE_B_DECISION_STATE_BEHAVIORAL.md`
(§23 Gate B), `P6_JACOBIAN_READOUT.md` + `P6_PEAKLAYER_AND_CURATED_JOIN.md` (§12), `P7_REFUSAL_DIRECTION_
VALIDATION.md` (validated axis), `P1_2_BASELINE_DRIFT_ENVELOPE.md` (§1.2 noise floor), `PHASE_BEHAV_REFUSAL.md`
(depth Panel B / calibrated rescue). Plan reference: `CONTINUATION_MASTER_PLAN_V2.md` §32–34.

---

## 1. Thesis

The Doublespeak in-context attack does not jailbreak the model by *remapping the harmful concept* — that
representational change exists but is behaviorally epiphenomenal. It jailbreaks by **suppressing a refusal
representation that becomes causally accessible in the mid-model residual stream (onset ~L13, strongest
L15–L18)**. Five independent lines of evidence converge on this single decision-state locus: a targeted
Direct→Doublespeak residual overwrite at L15–L18 *representationally* restores the refusal projection
(frac ≈ 0.93, replicated on frozen test); the same overwrite *behaviorally* collapses the jailbreak during
generation (ΔASR −0.14 train / −0.19 dev); restoring the refusal direction alone lowers ASR (L18 −0.18); the
refusal channel's causal sensitivity and its static projection each *predict* which items jailbreak (AUC 0.81
/ 0.87) while nothing about the concept target does; and all effects sit 7–10× above a measured judge-noise
floor. The mechanism appears exactly where the attack works (clearharm, uneven suppression) and is absent
where it does not (generated cohort, net-negative), which is itself corroborating rather than contradictory.

---

## 2. The independent lines of evidence

| # | line of evidence | cohort / split | n (per cell) | effect | CI / p | control | status | run dir |
|---|---|---|---|---|---|---|---|---|
| E1 | **Representational localization** — Direct→DS decision-token residual overwrite restores refusal projection | clearharm train / dev / **test** | 85 / 43 / 42 | frac restored **0.936 / 0.931 / 0.926** at resid_pre L18 | Holm-p 0.0 / 0.0 / **0.005**; direct−rand CI [1.6, 3.4] all >0 | self-swap ≤5e-6; rand donor fails specificity | **VERIFIED** (Gate A) | `refsuploc_clearharm_…732161` |
| E1b | same, generated cohort | generated train/dev/test | 77 / 39 / 38 | no cell beats norm-random donor | direct−rand CI negative | — | **NULL** (expected; DS net-negative) | `refsuploc_generated_…732162` |
| E2 | **Refusal-direction rescue (subspace-only)** — inject calibrated +α·refusal axis at layer L during generation, ΔASR | clearharm train | 44 | **ΔASR L18 = −0.182** (L16 −0.136, L24 −0.159) | McNemar **p = 0.021** (L18); rand control +0.023 | norm-matched random ≈ null | **VERIFIED** | `refinject_cal_clearharm_…732204` |
| E2b | same, frozen test | clearharm test | 42 | ΔASR L18 = −0.119 | p = 0.125 (ns) | rand 0.0 | **UNDERPOWERED** (low base ASR) | `refinject_cal_clearharm_…732204` |
| E3 | **Decision-state behavioral causality** — Direct→DS resid_post overwrite at {15,16,17} during generation, ΔASR | clearharm train / dev | 85 / 43 | **ΔASR L17 = −0.141 / −0.186** (→ ≈ direct_base level) | McNemar **p = 0.012 / 0.008** | rand L17 moves ASR **opposite** (+0.14, p=0.045 train); self ≈0 (p=1.0) | **VERIFIED** (Gate B) | `refdecpatch_clearharm_…732388` |
| E3b | same, frozen test | clearharm test | 42 | ΔASR L17 = −0.048 (ns) | p ns; rand +0.214 p=0.004 (design live) | self ≈0 | **UNDERPOWERED** (ds_base ASR 0.167) | `refdecpatch_clearharm_…732388` |
| E3c | same, generated cohort | generated train/dev/test | 77 / 39 / 38 | small ΔASR (train L17 −0.052) | p = 0.52 ns | self ≈0 (locality holds) | **NULL** (DS net-negative: direct_base ASR > ds_base) | `refdecpatch_generated_…732389` |
| E4 | **Prediction — refusal Jacobian sensitivity predicts jailbreak** | clearharm pooled / locked test | 86 / — | **AUC 0.807** (‖J‖@L12), 0.815 locked test | 95% CI **[0.696, 0.901]** | concept ‖J‖@L16 **inert** AUC 0.583, CI incl. 0.5 | **VERIFIED** | `jacobian_clearharm_…732004` |
| E4b | **Prediction — refusal projection predicts jailbreak** | clearharm | 86 (32 malicious) | AUC **0.874** (decision-token projection) | Mann-Whitney p=3.8e-9, r=−0.584 | — | **VERIFIED** (RP-01) | `refproj_clearharm_…711392` |
| E4c | Jacobian dissociation (paired) | clearharm | 86 | refusal − concept ‖J‖ AUC = **+0.225** | 95% CI **[0.055, 0.361]** (excludes 0) | concept scalar AUC 0.51 (chance) | **VERIFIED** | `jacobian_clearharm_…732004` |
| E4d | same behavioral join, curated cohort | curated | 51 (11 malicious) | refusal−concept AUC diff −0.05 | CI [−0.239, 0.157] incl. 0 | — | **NULL / UNDERPOWERED** (2 test positives) | `jacobian_curated_…732011` |
| E5 | **Noise floor** — greedy determinism + judge label-flip on byte-identical text | clearharm train / test | 85 / 42 | gen determinism **1.000**; judge flip mean **~1–2%** (≤~7% any) | — | empty_rate 0 everywhere | **VERIFIED** | `baseline_drift_clearharm_…732432` |

**Reading the table.** E1 establishes the *representational* locus and E3 converts it to *behavior* using the
identical intervention primitive; E2 confirms the same effect with a **refusal-subspace-only** donor (not the
whole residual); E4 shows the refusal channel is the item-level *predictor* of success while the concept
channel is not; E5 certifies the E2/E3 effect sizes (−0.14 to −0.19) are **7–10× the ~2 pp judge-noise
floor** — robustly real, not judge jitter.

### Supporting representational facts (same channel, VERIFIED elsewhere in the audit)
- Ablating the validated **L18 refusal direction** through generation raises ASR by **+0.43/+0.48**
  (clearharm), norm-matched random null (BR-01/BR-02, `behav_refusal_clearharm_a1.0_…708038`).
- Re-injecting the axis drives ASR **monotonically to 0.000 at α=12**, axis-specific, empty_rate 0
  (BR-04/BR-05/BR-06, `behav_refinject_clearharm_L18_…710769`).
- Doublespeak only **partially** suppresses refusal on clearharm (ds_base refusal_rate .45–.48 vs direct
  .84–.88 vs full ablation .05–.10) — this uneven suppression is why the attack works item-by-item and why
  the refusal projection is predictive (BR-07).

---

## 3. The concept-vs-refusal dissociation (claims A / C / D / E)

The sprint mapped **two parallel computations** induced by the same in-context attack and causally separated
them. This is the paper's central contribution.

- **Claim A — a distributed concept remap exists but concept strength is not the main behavioral
  determinant.** The L8–11 concept write is real representationally (ablation drops FC p_concept in every
  cell, WR-01) but is **behaviorally inert / at most underpowered**: prefill and decode-safe write ablation
  give ΔASR in [−0.023, +0.067], every McNemar p ≥ 0.5, and the graded endpoint is null (−0.004, p=0.94)
  (P10-07, P100-04, `behav_write_clearharm_L8_9_10_11_ds_…718938`). The carry-head graded effect **fails its
  specificity control** (random-head reaches 53% of the carry effect; direct contrast +0.035, p=0.382,
  P100-02/03). Honest caveat: the binary write null is **UNDERPOWERED** (n=86, post-hoc power 0.09–0.14) — we
  write "no effect detectable at this n," never "no effect" (§10, §4 below).
- **Claim C — concept-remap and refusal-suppression are causally separable.** Restricted to the P7-validated
  layers {L13–20,24,28,29}, `frac_of_direct_gap_restored` from write-ablation is **≤|0.05|** in every cell
  (≤|0.025| clearharm) — ablating the concept write leaves DS's refusal suppression unmoved where the refusal
  axis is real (WR-02, VERIFIED). The two directions are near-orthogonal (mean cos 0.012/0.061, max |cos|
  ≤0.153, BR-12). **VERIFIED.**
- **Claim D — the decision-token refusal state is causally sufficient for refuse/comply.** Gate A (E1) +
  Gate B (E3) + depth Panel B (E2): the same L15–18 decision-state overwrite that restores the refusal
  projection also collapses the jailbreak, with a specific random control moving ASR the opposite way.
  **VERIFIED (clearharm train+dev); test underpowered; generated NULL by construction.**
- **Claim E — a refusal-based objective predicts attack success better than the concept representation.**
  E4/E4b/E4c: refusal ‖J‖@L12 predicts jailbreak at AUC 0.807 (0.815 locked test) and the refusal projection
  at AUC 0.874, while the concept target is at chance on every measure (value AUC 0.51, ‖J‖ AUC 0.58 CI incl.
  0.5); paired refusal−concept AUC diff +0.225 [0.055, 0.361]. **VERIFIED on clearharm** (curated NULL/
  underpowered, E4d).

**One-line dissociation:** *representation ≠ behavior* — the concept circuit is a behaviorally
epiphenomenal bystander (Claims A/C), the refusal channel is the behaviorally causal lever (Claims D/E),
shown on both a static-readout axis and an independent gradient/sensitivity axis.

---

## 4. Caveats (explicit, must travel with the claims)

1. **Generated cohort is NULL — and this is coherent, not a failure.** On the generated cohort
   `direct_base` ASR > `ds_base` ASR (train 0.49 vs 0.40; dev 0.44 vs 0.36; test 0.39 vs 0.37), i.e.
   Doublespeak is **net-negative** there, so there is no refusal-suppression to restore. Gate A (E1b) and
   Gate B (E3c) are both NULL on generated; self no-op ≈0 confirms locality holds. The mechanism appears
   exactly where the attack works (clearharm) and is absent where it does not — corroborating.
2. **Frozen-test cells are underpowered, not failed.** Gate B test (E3b) has ds_base ASR only 0.167
   (≤7 rescuable items, discordant b=4–5), so the direct effect is directionally consistent but ns; the
   depth-Panel-B test cell (E2b) is likewise ns (−0.119, p=0.125). That the *wrong-direction* random effect
   is significant on test (E3b rand +0.214, p=0.004) confirms the design is live, not dead. Gate A test **is**
   powered and passes (frac 0.926, Holm-p 0.005). Powering the behavioral test cell needs n≈275 (ΔASR 0.09)
   / 419 (0.07) per §30.
3. **Donor granularity: whole decision state vs refusal-subspace-only.** Gate B (E3) transplants the *entire*
   Direct decision-token residual → this demonstrates decision-**state** sufficiency. The
   refusal-**subspace-only** version is depth Panel B (E2), which also ↓ASR. Both are reported; the two
   together bracket the claim, but neither alone isolates "only the refusal subspace, nothing else."
4. **Single model.** Everything is Llama-3.1-8B-Instruct, bf16, single hooking framework. No
   cross-architecture check (§27) and no framework-robustness check (§28) yet.
5. **Bidirectional arm is PENDING.** The reverse swap (insert DS decision residual into a *refusing* Direct
   prompt → does ASR **rise**?) is launched as **job 732560** (forward arm byte-unchanged; reverse-self
   no-op=0 in smoke) but has **not landed**. If the reverse swap raises ASR, Gate B upgrades from PASS to
   **STRONG** (§32 Gate B STRONG criterion). Until then the causal claim rests on the necessity direction
   (restore→refuse) plus specificity/locality controls, which is already a PASS.
6. **Jacobian ‖J‖ is a partly-generic mid-layer profile** (cos with semantic directions ≤0.03); the
   target-specific signal lives in `jac_proj`/projection, so the load-bearing P6 result is the mid-causal /
   late-readout dissociation and the behavioral-prediction AUC, not the bare ‖J‖ peak (P6 §3).
7. **Depth anchoring.** Every refusal endpoint uses a **generation-validated** direction. Only
   {L13–L20, L24, L28, L29} validate in both direction families; L0–L12 (incl. L9) carry **no** valid
   refusal axis. Of layers carrying headline results, L16/L18 validate strongly in both families; L18 is the
   anchor for every behavioral arm (P7, BR-09/BR-10/P7-32). Depth claims must be read at L16/L18, and the
   old "L9 ns" prose is replaced by the positive "onset ~L13" statement.

---

## 5. What remains open

- **§23 bidirectional counterfactual (PENDING, job 732560).** The strongest possible causal demonstration; a
  clean reverse swap would move Gate B to STRONG.
- **§19–21 causal defense + utility (OPEN).** Whether refusal-axis restoration to the *normal* Direct-harmful
  distribution (not extreme α=12) is a *selective* defense that reverses Doublespeak while preserving benign
  behavior (over-refusal, task quality). Claim G is unearned until the utility arm runs.
- **§27 cross-model replication (OPEN, gated).** Is "refusal suppression, not concept remapping" general or
  Llama-specific? Requires the staged X1–X5 gate on ≥1 further instruction-tuned model. Claim H open.
- **§14–18 Gate-7 attack objective (OPEN).** Whether a refusal-derived objective *improves* adversarial
  optimization (Claim F) — 0/13 GPU arms run under the fixed `objective.repr_in_selection`; all prior
  "mechanism-GCG net-negative" claims predate the fix and are invalid.
- **§10 powered concept-circuit ablation (OPEN).** To convert the concept-write "no effect at this n" into a
  properly-powered NULL at the pre-registered minimum meaningful ΔASR.

---

## 6. Honest status of the refusal-circuit story (one line)

**On Llama-3.1-8B / clearharm the refusal-suppression circuit is closed and behaviorally causal: a validated
refusal axis onsets ~L13, Doublespeak suppresses it, and specifically restoring the L15–18 decision state —
by whole-residual overwrite (Gate B, ΔASR −0.14/−0.19) or by refusal-subspace injection (depth Panel B, L18
−0.18) — collapses the jailbreak (Gate A/B PASS, 7–10× the noise floor), while the concept remap is
behaviorally inert; still open are the bidirectional swap (running, 732560), a utility-preserving defense,
Gate-7 optimization, and cross-model generalization.**

---

## Appendix — inconsistencies found BETWEEN the source reports (flagged, not smoothed over)

1. **Gate B report is internally stale about the generated cohort.** `P_GATE_B_DECISION_STATE_BEHAVIORAL.md`
   header and §Caveats both say generated is "**pending** (`732389`)," yet the report's own §"Result —
   generated cohort" already **reports the completed `732389` NULL numbers** (117 vals recomputed, 0
   mismatch). The status line prose was not updated when the results section landed. **Resolution used here:**
   treated generated as **DONE / NULL** (E1b, E3c). (The upstream task brief inherited the same stale
   "pending" wording; the data on disk is complete.)

2. **Bidirectional arm status conflicts across documents.** `P_GATE_B_…md` §Caveats/§Next say the
   bidirectional §23 arm is "not yet run" / "optionally," making **no mention of a job id**, whereas
   `CONTINUATION_V2_PROGRESS.md` (tick +11) records "**§23 bidirectional launched (732560)**" with a passing
   smoke. **Resolution:** reported as **PENDING, job 732560** (the progress log is the more recent record);
   flagged so the Gate B report's "not yet run" prose is not read as "not scheduled."

3. **Doublespeak clearharm-train baseline ASR differs ~3.5 pp across two v3 n=85 runs.** The noise-floor
   report gives doublespeak ASR **0.306** (`732432`, n=85, max_new 200, greedy) while Gate B gives
   `ds_base` ASR **0.271** (`732388`, same split, same n=85, same max_new 200, same greedy). Since the
   noise-floor report itself certifies **generation determinism = 1.000**, this ~3 pp / ~3-item gap cannot be
   generation noise; it is most plausibly a harness/template or single-judge-vs-mean-of-K difference between
   the two code paths, but it is a genuine cross-report numeric discrepancy on the *same* baseline condition.
   It does not affect any ΔASR (all effects are within-harness paired), but the two baselines should not be
   quoted interchangeably. **Flagged for reconciliation.**
   (Separately, the depth-Panel-B / P6 runs report ds_base ASR ~0.34–0.36 on clearharm train — but those are
   the older **n=44** split, not the v3 n=85 split, so that difference is expected, not an inconsistency.)

4. **Minor: onset-layer wording drift.** `P_REFUSAL_SUPPRESSION_LOCALIZATION.md` reports refusal-carry
   "onset ~L13," matching P7's validated-axis onset L13, but the localization band is quoted as **L15–L18**
   for the *strongest* restoration; some earlier prose says "L16." Not a numeric conflict (L13 = onset,
   L15–18 = peak), but harmonized here as "onset ~L13, strongest L15–L18" to avoid the appearance of two
   different localizations.

_Not committed, per instructions._
