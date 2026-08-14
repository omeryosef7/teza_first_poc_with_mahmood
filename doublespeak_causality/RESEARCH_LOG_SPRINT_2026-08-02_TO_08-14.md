# Doublespeak Causality — Unified Research Log (2026-08-02 → 2026-08-14)

**What this is.** A single, self-contained research-log narrative of the *entire* sprint on the
`behavioral-causality-sprint` branch, from **Sunday 2 August 2026** (the sprint's first commit,
`3cb44050 Phase 0: master plan`) through **14 August 2026** (`c04d556b` / `1e364973`, Section 20). It is written so an
external reader — human or LLM — with no repo access can understand the goal, the method, every headline
number, the corrections we made to our own work, and what is still open. It supersedes and folds in the
prior partial summaries (`SPRINT_2026-08-02_TO_08-05_FULL_SUMMARY.md`,
`SPRINT_SINCE_2026-08-02_COMPREHENSIVE.md` [→08-06], `SPRINT_SUMMARY_2026-08-02_TO_08-09.md`,
`docs/ASYMMETRY_FINAL_SYNTHESIS.md`, `docs/SECTION20_RESULTS.md`).

**Verification provenance.** Every quantitative claim in the Aug-02→09 part was cross-checked against the
committed raw outputs (`outputs/*/summary.json`, `*.json`, `raw.jsonl`) — first by a 14-auditor pass, then a
7-agent re-verification, then two 12-agent adversarial audits (`wf_8333d36e`, `wf_383ca171`), and the
machine-regenerated claim table (`reports/CLAIM_AUDIT_TABLE.md`: **95 claims, 77 VERIFIED, 0 CHECK-FAIL, 173
numeric recompute checks / 0 failures**). The Aug-09→14 part (Next-Sprint, Asymmetry Sprint, Section 20) was
re-verified for this log by a 4-agent workflow (`wf_92ba16b8`) that re-opened the committed JSON for each
headline number. **Revision 2 (2026-08-14):** the whole document was then re-audited end-to-end by a
14-agent completeness + soundness workflow (`wf_9c6abc32`) whose findings are in
`RESEARCH_LOG_AUDIT_2026-08-14.md`; 17 numeric/scope defects were corrected and 15 omitted results added.
Everything that pass changed is marked **[c2]** inline. Tags: **[V]** verified from an output file /
recompute · **[R]** report-only · **[W]** withdrawn/superseded (kept for honesty) · **[B]** bounded null ·
**[BLK]** blocked-as-specified.

---

## 0. One-paragraph takeaway (the whole sprint)

We set out to map the complete causal circuit of the **Doublespeak** in-context jailbreak (arXiv:2512.03771),
in which a benign codeword is bound by in-context demonstrations to a harmful concept so that a request phrased
with the codeword elicits harmful output. **We mapped the concept circuit in full — and then showed that circuit
does not cause the jailbreak.** The elaborate token→concept remap (demo-codeword K/V retrieval L8–L10 + an L9
MLP write → L14–L21 "carry" heads → L30–31 output) is real, distributed, and necessary-and-partially-sufficient
*for the internal concept readout* — but ablating it through harmful generation leaves attack success
statistically unchanged, while a count-matched *random* ablation moves ASR ~3× more. What *is* behaviorally
potent is a single, orthogonal **refusal direction**: ablate it and ASR rises +0.43–0.48 (a stronger attack than
Doublespeak); re-inject it and ASR falls to 0.000 with fluent refusals; its decision-token projection *predicts*
which prompts jailbreak (AUC 0.87). **Doublespeak is, mechanistically, an imperfect in-context
refusal-suppression technique; the concept remap is a causally-decoupled, behaviorally epiphenomenal bystander.**
The dissociation reproduces on **Qwen3-14B** and survives 8-/4-bit quantization and an independent from-scratch
implementation. The final two sub-sprints turned to the sharpest question — *can the mechanism be turned into an
attack?* — and found a precise answer: the refusal direction is **causal in activation space**, **reachable and
steerable by a continuous input optimizer** (soft-prompt ASR 0.784 vs 0.153 control), yet **discrete GCG token
optimization toward the same coordinate fails** (+0.009 ΔASR, sign-unstable, below judge noise). *The medium, not
the mechanism, is what fails.* Section 20 then bounded every behavioral negative honestly (±0.19–0.27 ASR at
n=37) and separated the **objective-space** claim (a 78 % change in the optimized quantity) from the
**behavioral** claim (unmeasurable) it must never be conflated with.

---

## 1. System under study, model, environment

| item | value |
|---|---|
| Primary model | `meta-llama/Llama-3.1-8B-Instruct`, **bf16**, 32 layers × 32 heads (8 KV heads, GQA), d_model 4096 |
| Cross-model | `Qwen3-14B` (thinking-OFF); `Phi-4-mini-reasoning` (reachability replication) |
| Hardware | NVIDIA **L40S** primary; backfilled onto **a5000 / 3090** (killable partition) via a VRAM-gated allowlist |
| Stack | torch 2.7.1+cu126, transformers 5.12.1; CPU analysis in conda env `poc_stage2` (numpy 2.4.6, scipy 1.17.1); bitsandbytes 0.50.0 for quant |
| Attention | default SDPA; **eager forced** wherever attention patterns/edges are hooked (SDPA fuses softmax@V and silently no-ops the hook) |
| Decoding | greedy (`do_sample=False`); gen_determinism measured **1.000** every cell |
| Harm judge | **StrongREJECT** rubric grader (gpt-4o-mini), `MALICIOUS` iff score ≥ **0.25** (`scripts/behav_judge.py:85 MAL_THRESHOLD`); `ASR` = fraction malicious. Judge-noise: see §20.3 — the corpus figure is **0.62 %** two-pass disagreement, superseding the earlier 3.4 % (one arm at n=37) |
| ⚠ Threshold conflict **[c2]** | 0.25 is what *ran*, but the paper-facing docs specify **≥ 0.5** as the standing binary-success contract (`docs/UPDATED_PAPER_CLAIM_TABLE.md:11`, `PAPER_OUTLINE_V2.md:61`, `RESEARCH_HANDOFF_V2.md:102`). The sprint never recorded which results were produced at which threshold. The one audit that checked (§20 item 2: 27 contrasts, 0 sign flips) found it conclusion-neutral, but **any number in this log may need re-reading at 0.5 before publication** |
| Concept readout | **forced-choice `DE_context`**: `p_concept = P(concept)/(P(concept)+P(codeword))` at the answer position (representational, not behavioral) |
| Attack source | ClearHarm rev `79464fb6…`; demos via `gpt-4o-mini`, `openai_seed=7`, 12 demonstrations per prompt |

**Two metrics, kept strictly separate throughout.** `p_concept` (does the model internally *read* the codeword
as the harmful concept?) vs **ASR** (does it *emit* harmful content?). The entire program is that these
dissociate. **Six matched conditions per item** exist in the data: `doublespeak` (attack), `neutral`
(codeword, no demos), `direct` (plain harmful request), `benign` (codeword bound to benign demos),
`shuffled`, `unrelated` — but **only 3 were run in the headline behavioral cell** (`direct`, `neutral`,
`doublespeak`; `outputs/behavioral_split_beh_clearharm/behavioral_summary.json`) and 4 in the drift runs
(`+benign`). **`shuffled` and `unrelated` were never run behaviorally [c2].**

**Provenance of the L18 refusal direction — a cross-distribution transfer [c2].** Every refusal number in
Parts B, D, E, F and G rests on an axis fit **not on ClearHarm** but on `pair_carrot_bomb.json`
(`outputs/stage_gcg_full/refusal_direction_llama_L18.json`: n_harmful **60** / n_harmless **20** generic
instructions, separation **0.9525**) and then applied to ClearHarm. This was first flagged in
`docs/UPDATED_PAPER_CLAIM_TABLE.md:51` (claim A6) and is stated here for the first time. Its bidirectional
validation, which is what licenses the word "validated" throughout: `refusal_direction_llama_SELECTED.json`
→ L18 `ablate_gain +0.4667, induce_gain +0.6667, score 1.1333`, selected over L12/L14/L16/L20.

---

## 2. Data — the locked splits

- **v1** `data/splits/clearharm_doublespeak_v1.json` (frozen 08-02) — **[V]** 137 records, two cohorts split at
  the intent-cluster level: **clearharm** 86 (44 train / 42 test, 43 concepts); **curated** 51 (30 / 21, 17
  concepts ×3). 0 example/cluster/prompt overlap across train/test; 137/137 single-token concepts+codewords.
  ⚠ curated-test n=21 is the source of the sprint's one acknowledged power failure.
- **v2** `data/bench/bench_clearharm_v2.json` (08-04) — **[V]** 116 examples (86 clearharm + 30 new), 0 test leak.
- **v3** `data/behavioral_v3/` (08-05) — **[V]** **N=324**, 224 single-token concepts, 224 pairwise-disjoint
  codewords; cohorts clearharm 170 / generated 154; train 162 / dev 82 / test 80; **0 straddling** (fixed v1's
  vacuous per-instruction leakage check). Built for **$0.1426** across 496 gpt-4o-mini calls. Confirmatory audit:
  N=324, leakage 0, cells ≥20, 324/324 real demos, pinned @79464fb6. **Cohorts are NOT exchangeable** (DS is
  net-positive on clearharm, net-negative/concept-diluting on generated).

---

## 3. Statistics & controls (apply to everything)

- **Paired designs throughout**; train(dev) and test(heldout) aggregated **separately** (a pooling bug was caught
  and fixed mid-sprint).
- **Representational significance:** two-sided **Wilcoxon signed-rank**, **Holm**-corrected across the 32-layer or
  32×32=1024-head family, per split. (Replaced a sign-flip permutation test whose 5.0e-5 resolution floor returned
  an artifactual p=0 — the "60–75 heads" figure was that artifact.)
- **Behavioral significance:** **exact McNemar** on paired discordant flips + percentile bootstrap CIs (2000–10000
  resamples, seeded).
- **Tripwire controls, verified exactly 0.0 in raw:** self-swap, self-check freeze, identity patch, α=0 no-op.
- **Specificity controls:** norm-matched random directions, count-matched random heads/positions/edges. **The
  program's core epistemic move is specificity, not just significance.**
- **Coherence guard:** `empty_rate` = 0.000 in every behavioral cell.
- **Data integrity:** `validate_all_outputs.py` recomputed **4,909 summary values from raw across 29 dirs → 0
  mismatches**; test suite grew **113 → 205** passing (two real primitive defects found & fixed).
  **Scope corrections [c2]:** (a) "0 mismatches" is true *of that 29-dir pass only* — the later claim-table
  sweep found exactly one, `reports/CLAIM_AUDIT_TABLE.md` META-03: `summary!=raw at
  by_split.heldout.monotone_decreasing` on `outputs/phase9_dose_curated_L9_…704861` (2 of 5 `phase9_dose`
  dirs); it is the only such mismatch in the corpus. (b) Neither the 4,909 count nor the 113→205 trajectory
  exists in a machine artifact — both are prose in `CONTINUATION_PROGRESS.md` **[R]**. (c) The suite at HEAD
  is **228 passed / 13 skipped** (241 collected); 205 was the Part-C endpoint, not the sprint's.

---

# PART A — the representational concept circuit (sub-sprint 1, 08-02 → 08-04)

All readouts are forced-choice `p_concept`. **Sign convention: a positive effect = the intervention DROPPED the
hijacked reading.**

## 4. The circuit, stage by stage — [V]

- **4.1 Behavioral baselines / Gate 1.** clearharm agg (n=86): direct **0.116** / neutral 0.256 / doublespeak
  **0.349** (DS beats direct **+0.233**); curated 0.255 / 0.039 / 0.235. Recomputes exactly from the label field.
- **4.2 Direction geometry — Concept ⊥ refusal.** mean cos(concept,refusal) = **0.012** clearharm (max |cos|
  0.078) / **0.061** curated (max 0.153) — orthogonal at every layer. The `doublespeak_signature` (DS−neutral) is
  *closer to refusal* (cos 0.127/0.151) than the concept direction is — the first hint of the headline.
- **4.3 Residual patching at the query codeword — NULL.** Logit-lens P(harm) at the query codeword is at floor;
  no patch beats random; identity control exactly 0.0 on all 137 items. The local codeword state carries nothing.
- **4.4 Demo-codeword K/V retrieval (L8–L10) is NECESSARY, not sufficient.** Neutralize demo-codeword K/V
  (donor = benign-remap): per-layer specific effect CI excludes 0 at L8–L10 both cohorts (L9 curated +0.220 /
  clearharm +0.082; L10 clearharm +0.113). Honest joint window **L8–L10** (clearharm L11 CI includes 0).
  Sufficiency ≤ 0 everywhere — the binding is **context-bound** at this stage.
- **4.5 Query→demonstration attention EDGES are NOT necessary — clean negative.** Surgical eager edge knockout,
  all heads L8–11: specific-vs-random +0.0020 [−0.0004, 0.0046] **ns** (clearharm), −0.0026 ns (curated).
  Blocking *all* query edges hurts 13×–49× more (general-attention effect). **Retrieval is distributed/redundant,
  not a single induction edge.**
- **4.6 The L9 MLP write.** Patch DS `mlp_out` with matched benign at the **demonstration** codeword positions.
  **L9 is the only layer Holm-significant on all four cells** (cur dev +0.049 [0.023,0.080]; cur heldout +0.097;
  clr dev +0.063; clr heldout +0.015). **Sufficiency ≈ 0.** Componential dissociation at the same token: `attn_out`
  at L9 is null while K/V and MLP-out are both necessary. ⚠ **[c2]** The write is *not* purely
  demonstration-position: the **query**-codeword MLP is not a clean null on clearharm (L9 **+0.0146** dev /
  +0.0046 heldout, and L15/L20 also survive Holm on both splits). The correct statement is that the query
  effect is **3–4× weaker**, not absent (`SPRINT_2026-08-02_TO_08-05_FULL_SUMMARY.md` §7.6).
- **4.7 Write granularity (143 windows, v2).** Single L9 +0.080; sliding-W4 **L8–11 +0.111** > best single layer ⇒
  the write is **distributed across L8–11**. (Corrected: "saturates at W8" is false.)
- **4.8 All-head z-patch necessity — the carry heads (L14–L21).** Wilcoxon+Holm over 1024 cells (re-running
  `phase5_analyze.py` reproduced counts exactly): Holm-sig positive-necessity heads = cur dev **58** / cur heldout
  **0** (power failure at n=21, *not* a null) / clr dev **31** / clr heldout **31** (25 heads sig on BOTH clearharm
  splits). Top: L17H27, L14H4/H5/H23, L15H8, L18H20, L21H10, L30H15, L31H0/H1. **No single head dominates** (top ≈5 %).
- **4.9 Carry heads are causal in their attention PATTERN.** Joint 7-head uniform-KO **+0.166** dev / **+0.134**
  heldout; benign-pattern transplant +0.46; per-head none individually necessary (superadditive). ⚠ **[c2]**
  the uniform-KO arm has **no specificity control**: an arbitrary non-candidate head's pattern (`C_rand`)
  already produces a **0.152 dev / 0.103 heldout** drop, so "uniform-KO is specific to the carry set" is
  **unsupported on dev** (source §7.9). The pattern-causality claim stands; the specificity claim does not.
- **4.10 Where the carry heads get the concept.** KO_all (firing control) +0.246/+0.207; **KO_demo +0.007/+0.003**
  (~2–3 %) ⇒ carry heads read from the **distributed residual context**, not fresh attention to demo codewords.
- **4.11 Carry vs proximal + closing the L9→carry edge.** (a) `direct_frac` ≈ **0.00** for L14–L21 carry heads vs
  0.47–0.76 for L30H15/L31H0 (readout-proximal). (b) L9→carry-band mediation **0.75–0.83 in 3 of 4 cells**
  (clr dev 0.751, cur dev 0.764, cur heldout 0.828); the 4th, **clearharm heldout, overshoots at 1.459**
  (n=9) — disclosed in `reports/PHASE7_PATH.md:67` and **[c2]** restored here. Random-head control 0;
  underpowered throughout (n=9–13). (c) **Carry head-set is PARTIALLY SUFFICIENT** — install DS carry-`z` into a benign prompt
  → +0.16/+0.24/+0.37/+0.41 (random install ~0). **Progression: context-bound at retrieval/write → transplantable
  once carried.** *(Sufficiency is representational only.)*
- **4.12 Readout ≠ mechanism.** Linear concept projection peaks at **L31** in all four cells while causality lives
  at **L9/L14–21** (projection ≈ 0 at L9). Logit-lens localizes readout proximity, not the write.
- **4.13 The write is a GRADED lever.** Interpolated `(1−α)·DS + α·benign` at demo `mlp_out`: monotone decreasing
  over α∈[0,1] in **8/8 cells**; α=0 bitwise-identical to baseline. (No inferential stats — descriptive.)

**Circuit summary (Part A):** demo-KV retrieval (L8–L10) → L9 MLP write (band L8–L13) → L14–L21 mediated carry
heads → L30–31 proximal output. Necessity Holm-sig at every stage; carry stage additionally partially sufficient.
**Distributed within concentrated bands — no single head, edge, or layer is a bottleneck.**

---

# PART B — the behavioral frontier (sub-sprint 1 cont., 08-04 → 08-05)

Everything StrongREJECT-judged **generation** (real behavior), paired exact McNemar, two cohorts, matched
controls, `empty_rate = 0.000`.

## 5. The dissociation — [V]

- **5.1 BEHAV-CARRY — ablate carry heads through generation: NULL.** ΔASR +0.091/+0.071/−0.100/0.000; every CI
  includes 0; McNemar p ≥ 0.289.
- **5.2 BEHAV-WRITE — ablate the L8–11 write through generation: NULL (flatter).** ΔASR ∈ [−0.023, +0.067]; every
  p ≥ 0.688. (Re-tested decode-safe in the continuation — still null.)
  > **⇒ The complete representation ≠ behavior dissociation.** The components causally necessary (and, for the
  > carry heads, sufficient) for the concept **readout** are **not behaviorally necessary** for the jailbreak.
- **5.3 Refusal ablation is a STRONGER attack than Doublespeak — sufficiency.** Arditi-style directional ablation of
  the validated L18 refusal direction: ΔASR vs direct base **+0.432 (p=4.0e-6)** ch-train, **+0.476 (p=2.0e-6)**
  ch-test, +0.433 cur-train, +0.429 cur-test. Norm-matched random direction does **nothing** (p ≥ 0.5). ≥
  Doublespeak on all four splits (sig 2/4 at α=.05, 4/4 at α=.10).
- **5.4 Re-injecting refusal kills the jailbreak — necessity.** +α·refusal at L18 through DS generation: ASR
  .386/.381 → **.000** at α=12 on clearharm (McNemar p=1.5e-5 / 3.1e-5). Coherence-audited: empty_rate 0.000,
  effect already strong at milder α=8, completions are **fluent natural refusals**. ⚠ curated-test ns (only 2/21
  malicious to flip). ⚠⚠ **[c2] the random control is NOT null at the headline dose.** It is null at α=8, but at
  the matched **α=12 a norm-matched random direction significantly RAISES ASR (+0.27 / +0.33, p ≤ 0.002)**
  (source §8.4). So the α=12 → 0.000 result is a *large-dose* effect whose specificity is only established at
  α=8. Quote the α=8 arm when specificity is the point.
- **5.5 Doublespeak SUPPRESSES the refusal axis — representational grounding.** Project last-prompt-token residual
  onto the per-layer refusal direction: clearharm-test direct−ds gap grows monotonically hs9 **+0.19** → hs32
  **+41.21**, zero violations in all four cells; onset ~hs8 (the L8–11 write band). ⇒ the demonstrations do two
  orthogonal things in the same band: remap codeword→concept (inert) and suppress refusal (the driver).
- **5.6 The refusal DECISION is read MID-LATE (~L22).** Calibrated-α injection (each layer's own gap): L9 null in
  both cohorts; **L22 −0.250 (p=0.001) ch-train, sig in both cohorts.** Suppression starts at L8–11 but the
  behavioral decision is read mid-late. ⚠ Later refined: L9 is not linearly decodable as a refusal axis at all, so
  "L9 null" is *uninformative*; anchor mid-late on the validated L16/L18/L22.
- **5.7 Concept-remap ⊥ refusal-suppression — causally decoupled.** Ablate the L8–11 write, then measure the
  refusal projection: positive control fires (p_concept .884→.799) yet refusal suppression is unmoved (restoration
  within |0.05| of the gap at every layer; where sig, negative & ≤5 %). **This is why the concept circuit is
  behaviorally epiphenomenal: the two L8–11 effects run on separate pathways.**
- **5.8 The refusal projection PREDICTS which prompts jailbreak.** clearharm **AUC 0.874** at decoder L21 (n=86, 32
  malicious), Mann-Whitney **p=3.8e-9**, r=−0.584; **train 0.863 / test 0.891 [c2]** (the previously-quoted
  0.867 is the *pooled* column of `reports/P6_JACOBIAN_READOUT.md:89`, not train; per-split AUCs are
  report-only — `outputs/rep_predicts_behavior_sweep.json` stores pooled). curated is a genuine null (AUC 0.42) —
  uniform suppression → concept-dilution. ⚠ [W] the "5-fold CV 0.887±0.106" was withdrawn (recompute 0.869±0.055).
- **5.9 Outcome fixed at the DECISION POINT.** Token-0 L30 refusal projection: Direct 13.6, DS→refuses 9.1,
  **DS→jailbreak −2.1** (stays low); zero trajectory crossings; token-0 separation AUC 0.936 test / 1.000 train
  (**[R] [c2]** — `outputs/refusal_traj_clearharm_…711956/summary.json` stores no AUC field; the trajectory
  numbers themselves are **[V]**). The hypothesis that refusal *re-engages* mid-generation is falsified.

- **5.10 The `doublespeak_signature` direction (d_DS) is causally INERT — the sprint's best-supported
  negative [c2].** Adding d_DS at matched relative strength moves the concept reading by at most **1e-05**
  across 9 control cells and **3e-05** across 175 dose cells, while `d_Direct` at the same strengths moves it
  **+0.167 / +0.533 / +0.971** (`SPRINT_2026-08-02_TO_08-05_FULL_SUMMARY.md` §9.2, bottom-line item 8). The
  DS−neutral contrast vector — the most obvious "the attack direction" candidate — does *nothing* causally.
  It survives in this program only as the cosine observation in §4.2.

- **5.11 Run-to-run ASR drift bounds every 2-decimal Δ [c2].** The same `ds_base` condition, greedy, yields
  test ASR **0.286–0.381** across four separate runs (source §10.4) — a ~0.1 envelope from resampling alone,
  independent of the judge-noise floor measured in §20.3. This is the empirical reason §20.4's bounds land
  where they do.

- **5.12 The refusal_rate ladder — why "imperfect suppressor" is the right phrase [c2].** direct 0.84–0.88 →
  `ds_base` **0.45–0.48** → full refusal-ablation 0.05–0.10 (source §8.3): Doublespeak moves the model
  *halfway* down the refusal ladder, which is exactly what §5.3's "ablation is a stronger attack" means
  mechanistically. Composite DS+ablation train ASR **0.727** vs 0.568 (ablation alone) vs 0.386 (DS alone),
  McNemar **+0.341, p=2.8e-4** — the additivity later formalized in §8.5/§11.

**5.13 What sub-sprint 1 explicitly did NOT establish — Gate 6 and Phase 11 [c2].** Two planned items closed
as *not run*, and the log's later Gate-7 discussion must be read against them: (a) **Gate 6** — the candidate
`concept_objective` scored **9/10** on the eligibility checklist and **failed criterion 4 (behavioral
sufficiency)**, so the gate was never passed (source §9.1); (b) **Phase 11** — the 13-arm GCG/MAC matrix was
**designed but never run, 0 of 13 arms executed**, and even the scaled-down decisive arm G1 was planned and
never launched (§9.2). The source is explicit at line 838: *"Gate 7 was never tested … treat it as a
well-motivated hypothesis, not a measured null."* Everything in Parts D/E that calls Gate 7 a measured
negative refers to the **later** first-cut and v3 matrix, not to anything from this window.

**Consolidated behavioral verdicts:** carry & write behaviorally NULL; refusal ablation CAUSAL (sufficient);
refusal re-injection CAUSAL (necessary); DS suppresses refusal CONFIRMED; decision read mid-late (~L22); the two
pathways INDEPENDENT; refusal projection PREDICTIVE (clearharm); outcome set at the DECISION POINT.

---

# PART C — the continuation "tick" sprint (sub-sprint 2, 08-05 → 08-06)

Run under a 30-minute cron loop (`reports/CAUSAL_CONTINUATION_MASTER_PLAN.md`, ticks 1–86). Job: **trust then
extend** — harden provenance, recompute every number from raw, hunt bugs adversarially, add the causal tests the
plan still demanded. Changed no Part-A/B headline but **corrected several of our own claims** and added five results.

- **6. Integrity hardening — [V].** Provenance RUNMETA/DONE across 397/412 dirs; `validate_all_outputs.py` 4,909
  values / 0 mismatch; test suite 113→205; single StrongREJECT judge contract (`scripts/behav_judge.py`)
  differential-tested against 6 copies (found the missing-EMPTY-label defect in `14_behavioral_eval.py`; audited to
  have zero exposure).
- **7.2 (P1) Baseline audit — SAFE.** 0 of 411 Phase-2.1 generations empty; all 6 malicious rates recompute
  exactly. Secondary: truncation heavy & cohort-asymmetric (`stop_reason=length` 25 % clearharm vs 72 % curated).
- **7.3 (P2) All-occurrence patching ~doubles the L9 write necessity.** Patching all codeword occurrences vs
  demo-only raises L9 necessity **1.38×–2.27×** across six cells, specificity-controlled. (Ratio is unpaired —
  descriptive.)
- **8.1 (P7) 32-layer refusal-direction validation.** Under both independent direction families, ablate+induce
  arms: **L9 FAILS both** (valid=False); **L18 validates strongly** (ablate_spec +0.60/+0.90, induce +1.00/+0.80).
  The refusal axis first becomes linearly decodable at **L13**; **11 layers validate in both families** ({13–20,
  24, 28, 29}). Consequence: every per-layer refusal claim leaning on an *early* direction is affected → the "L9
  null" depth contrast is uninformative, not evidence of late-reading.
- **8.2 (P3) Decision-token attention edges — NULL with a working control.** edge-KO refusal shift −0.0032 (CI incl
  0); firing control (block all incoming edges) moves the projection to −0.666 / +1.075 (hook fires). Concept
  retrieval reaches the decision token through **no identifiable query→demo edge.**
- **8.3 (P4a) Induction-head identification.** query codeword attends to demo codewords at ~2× count-matched random
  (correlational only).
- **8.4 (P4b-1) No single head bottlenecks concept-reading.** Confirmed set {L4H16, L10H2, L13H18, L14H13}; effects
  0.001–0.014 (near floor) — distributed and weak.
- **8.5 (P8) The interaction saga — sub-additive → NULL (three corrections).** **The single most instructive
  correction.** P8.0 reported sub-additive Î=−0.186 (p=0.045) → **[W] withdrawn** (saturation artifact: at α=1.0,
  62.8 % of items already jailbroken; 7.5 % judge label-flips in the signal arms). P8.1 at de-saturated α=0.25:
  clean null Î=−0.0233 (p=0.860); Î tracks the I_max ceiling (Spearman +0.991). P8 v3 (n=242): pooled **Î=−0.054
  (p=0.172) NULL**; train sub-additivity (−0.124) **reverses on held-out test (+0.088)** — "the pre-registered
  split is the only thing standing between this project and making the same error twice." At the strong dose
  α=0.20 (where refusal-ablation provably fires: **+0.1417 vs random, McNemar b=20/c=2, p=1.2e-04** —
  `outputs/p8_alpha020_clearharm.json`, **corrected [c2]** from a previously-quoted "+0.194, p<1e-12" that
  belongs to a *different run at a different dose*, `p8_v3_combined.json` pooled@0.25, n=242): interaction
  **exactly 0.000 (p=1.000)**. **⇒ Doublespeak and refusal-ablation ADD, never synergize.**
- **8.6 (P10 / P10.0) Decode-safe write null survives; graded re-analysis → "undetermined."** P10: BEHAV-WRITE null
  survives decode-safe re-test (n=86; **n≈275 is needed for ΔASR≈0.09 and n≈419 for ΔASR≈0.07 [c2]** — the
  "275 for 0.07" pairing is a mis-citation `P10_DECODE_SAFE_WRITE.md` made of its own source and
  `reports/CLAIM_AUDIT_TABLE.md` P100-05 already corrected). P10.0: the binary "behaviorally inert" carry
  claim is **[W] retracted** — the graded endpoint recovers a small carry effect (d=+0.074, p=0.034) **but its
  specificity control FAILS** (random-head ablation = 53 % of the effect). Honest status **"undetermined."**

- **8.7 (P9.0) The GCG candidate-selection bug — the correction that made Gate 7 testable at all [c2].** The
  mechanism objective was entering the *gradient* but **not candidate selection**, so it never influenced
  which suffix was kept. Consequence, stated by the sprint itself
  (`SPRINT_SINCE_2026-08-02_COMPREHENSIVE.md:553`): *"every prior 'mechanism-derived GCG is net-negative'
  statement was made with the objective DISABLED in candidate selection, so Gate 7 currently has NO valid
  evidence for or against."* Fixed in commits `84bf7a1e` / `76acb44a` (`CONTINUATION_PROGRESS.md:193`).
  **Everything in Parts D–F that reports a GCG negative post-dates this fix; nothing before it is citable.**

**Corrections ledger (Part C):** P8.0 interaction (→ saturation artifact); CV-AUC 0.887→0.869; Phase-5b Q/K/V
"clean null" retracted; "behaviorally inert" carry → undetermined; a FALSE "D_i=+2 zero times in every cohort"
claim (curated actually shows 4) demoted; "SLURM SOLVED" falsified. **Direction of every finding preserved;
stated ranges tightened.**

---

# PART D — Continuation V2: the refusal circuit, closed (sub-sprint 3, 08-06 → 08-09)

`CONTINUATION_MASTER_PLAN_V2.md` — **28 sections, all DONE** (audited by `wf_df3944cb`; a section counts DONE only
if a committed run-dir + report with real numbers backs it, several as honest negatives). This sub-sprint pivoted
from *mapping the concept circuit* to *mapping and behaviorally validating the refusal-suppression circuit*, then
tested attack-objective, prediction, defense, and cross-model generalization. All numbers **[V]** unless tagged.

## 9. The refusal circuit and its behavioral causality

- **§3 Gate A — refusal-suppression localized at the decision token.** Residual stream **L15–L18**; `resid_pre`
  L18 train frac **0.936** (Holm-p 0.0), dev 0.931, **frozen TEST 0.926 (p=.005)**; residual ≫ attn_out/mlp_out;
  onset ~L13; self-swap ≤5e-6. (Null on the generated cohort, as expected — DS net-negative there.)
- **§23 Gate B — behavioral causality of the decision-token refusal state (PASS).** Restoring the Direct
  decision-token residual during DS generation lowers ASR: train (n=85) direct L17 **ΔASR −0.1412 (p=.012)**;
  random control **+0.1412 (opposite sign)**; self +0.0118. dev replicates (−0.186, p=.008). ⚠ Reduction to
  ≈direct level, not zero; frozen test underpowered (base at floor). **Reverse (comply) arm is NULL** → the DS
  state is not *sufficient* to induce compliance. Gate B is **PASS, not STRONG.**
- **§25 Full mediation: demo → refusal → decision → behavior.** train: ds_base .282 / direct .129 /
  ds_dpatch_direct .118 → **mediated fraction 1.07** (McNemar p=.0013); dev **1.00** (p=.0039). The DS attack is
  ~100 % mediated by the decision-state refusal representation.
- **§24 Orthogonalization: control lives in the refusal component.** train (n=85): **refusal⊥concept −0.2118
  (p=.00012)**; concept⊥refusal +0.1059 (p=.049); both ns. The causal control is in the refusal component, not the
  concept component.
- **§4 / §7 / §8 refusal-circuit anatomy.** §7 refusal heads are **head-distributed but LAYER-concentrated at L13**
  (audit-2 corrected); §4 carry-vs-readout **72–88 % mediated** with a monotone depth gradient; §8 full head→MLP
  path patching is **NO-PATH** (candidate/control 1.44×, needs ≥2×) — the refusal signal is carried, not
  sparsely written, in both families.
- **§5 position-decomposition — NULL (powered).** No demonstration-position manipulation both restores refusal AND
  keeps the concept remap; suppression is broad/distributed over demo structure.
- **§6 demonstration-count dose response — STEP, not ramp.** Nearly all suppression at the first demo; refusal
  proj@L18 4.02→2.98 then flat; concept flat; ASR weakly coupled (dRefusal↔dASR −0.292).
- **§22 token-timing.** What matters is the decision *state*, not decode-persistence; additive steering does not
  reduce ASR.

## 10. Concept circuit is epiphenomenal — by SPECIFICITY (powered, n=324)

- **§9 carry-head behavioral sufficiency — NULL.** Installing DS carry-`z` through generation: ΔASR +0.023 train /
  −0.048 test ≈ random; carry−rand specificity ≈0. **Concept sufficiency was never established behaviorally.**
- **§10 powered concept-circuit ablation — the key specificity result.** Pooled **n=324** (ASR_base .333):
  write+carry ΔASR **+0.046 [−0.011,+0.104] p=.142 (ns)** while count-matched **random +0.161 [.110,.211] p≈0
  (~3×)**; clearharm concept ablation **exactly 0.000** (b=22/c=22) vs random +0.124. **Epiphenomenal by
  SPECIFICITY** — not "inert/equivalent" (the pooled-equivalence framing was **[W] withdrawn** in audit-2: CI
  upper 0.104 > the claimed 0.09 MDE).
- **§12 The Jacobian / gradient-sensitivity readout — the dissociation, restated by a THIRD measure [c2].**
  (Run 08-07; `reports/P6_JACOBIAN_READOUT.md`, `outputs/p6_predicts_behavior_clearharm.json`; plan §12
  marked DONE. Omitted from every prior summary.) Instead of asking *what the model represents*, this asks
  *what the loss is sensitive to* — the gradient norm of the harmful-continuation objective w.r.t. each
  direction. Sensitivity peaks at **L12 for refusal** and **L16 for concept**. As a jailbreak predictor
  (n=86, 32 malicious): **`refusal_gradnorm_peak` AUC pooled 0.8073 [0.696, 0.901], train 0.7996, test
  0.8148** vs **`concept_gradnorm_peak` pooled 0.5828 (CI spans 0.5)**. The linear-projection scalars
  behave the same way (refusal 0.8449 pooled / 0.8469 test; concept 0.5075 pooled, 0.4222 test). **⇒ The
  concept channel is invisible not only to ablation (§10) and to linear readout (§5.8) but to the loss
  geometry itself.** This is the strongest single-experiment statement of the program's thesis and it should
  be in the paper.

- **§11 joint 2×2: concept × refusal.** Pooled n=324: Δ_concept −0.006 ns, **Δ_refusal −0.102 (p=9e-6)**,
  interaction **Î=−0.0216 perm-p=.56 (additive, not floor-bound**, I_max .787). Refusal restoration collapses ASR
  regardless of concept state; concept ablation inert in both refusal states.

## 11. Attack objective, prediction, defense

- **§14–18 Gate-7 — mechanism-derived GCG objective is NEGATIVE / non-specific.** Multi-seed (42+43) held-out ASR:
  vanilla 0.357; **refusal@L18 mean 0.465 ≈ random@L18 0.464** (dead heat); large per-seed variance. First-cut
  scope (2 seeds, 50 steps, no CI). Knowing *where* refusal is read (a scalar decision variable) does not hand you
  a *token-space* lever. Cleanly separates "predicts" (works) from "optimizes" (fails).
- **§18 continuous sanity gate.** Every candidate direction has a committed continuous gate: refusal **PASSES**;
  carry-head + combined + concept **FAIL** — only the refusal axis was ever cleared for discrete optimization.
- **§13 prospective frozen-threshold predictor (leakage-free v3).** Train-frozen threshold → **TEST AUC 0.9714,
  acc 0.857, fn=0** (every test jailbreak caught, 7 tp / 6 fp / n=42). Always paired with **train AUC 0.80** (only
  7 test positives).
- **§19–21 defense with utility — NEGATIVE (Gate F FAIL).** Causal refusal-restoration genuinely lowers ASR
  (**−0.224 train** best-layer L18; random does not defend) **but over-refuses attack-structured benign** at every
  layer/dose (over-refusal +0.28→+0.40 > |ΔASR|); an intent-gate on the refusal projection fires on benign as much
  as on attacks. Redeeming datum: **ZERO over-refusal on 40 unrelated-normal prompts** (§20; 39/40 gens changed →
  not a no-op). The refusal circuit *drives* behavior but is *not intent-selective*; the concept circuit *is*
  intent but *epiphenomenal* — so no scalar/gate on the refusal axis can be selective.

## 12. Generalization & robustness

- **§26 within-Llama generalization** (cluster-disjoint v3 held-out): existence ✓ / causal control ✓ / prediction ✓
  generalize to unseen concepts+codewords; attack-optimization ✗ (Gate-7 negative); novel-benign-codeword transfer
  is the one thin axis (probes only the epiphenomenal concept channel).
- **§27 Cross-model Qwen3-14B (thinking-OFF) — X1–X5 all ✅.** X1 DS raises ASR (.143 > direct .095 > neutral
  .024); X2 refusal direction validates (5/5, best L32); X3 DS suppresses the validated projection at every layer;
  X4 refusal ablation raises harm (+0.17–0.19) while random is null; **X5-CAUSAL: concept ablation is causally
  INERT (+0.035/−0.02 ≈ random) vs refusal +0.19** → **the concept≠behavior dissociation generalizes to a second
  model family.**
- **§28 framework robustness.** An independent from-scratch implementation reproduces the refusal-ablation headline
  (+0.31 vs +0.33; label-agreement 0.88/0.83; token divergence isolated to bf16 reduction-order, ~1 ULP/layer —
  not a logic bug).
- **§29 quantization robustness.** Refusal ablation raises harm at bf16/8-bit/4-bit (**+0.286 / +0.262 /
  +0.571**, McNemar sig); random ns at all precisions. **The mechanism survives quantization.** *(**[c2]** the
  previously-printed "+0.26 / +0.29 / +0.52" had bf16 and 8-bit swapped and understated 4-bit; §15's table
  below was always right. Source: `direct_refabl_a1.0_vs_direct_base.delta_ASR`, test n=42.)*

**Two 12-agent adversarial audits (`wf_8333d36e`, `wf_383ca171`): no core conclusion reversed, no claim REFUTED**;
corrections were overclaim-tightening (DEF-01 ratio, §10 specificity basis, X5 orientation) plus 5 latent
code/verdict-logic bugs, none of which changed a committed result. Live tally: **95 claims / 77 VERIFIED / 0
CHECK-FAIL / 173 numeric checks passed.**

---

# PART E — the Next Sprint: fair GCG matrix, a third family, quantization (sub-sprint 4, 08-09 → 08-11)

Plan `docs/NEXT_SPRINT_PLAN_2026_08_09.md` (Q1–Q7). Having established the mechanism in activation space, this
sprint asked the hard practical questions: *(a) does a properly-budgeted, leakage-free GCG matrix still show the
attack-objective negative? (b) does the dissociation hold on a third model family? (c) does it survive
quantization?* All headline numbers below were re-opened from the committed JSON for this log (`wf_92ba16b8`,
agent `next-sprint`).

**Foundational decision — the v3 leakage-0 split + an off-by-one fix. [V]** The frozen 16-arm GCG matrix was
specced on v1, but `reports/P1B_V3_SPLIT.md` found v1 has **~90 % train/test leakage** (77/86 rows; 14/43
concepts + 17/21 codewords straddle — the per-instruction hashing had made the leakage check vacuous). The matrix
was moved to **v3.1 leakage-0** (N=324, 0 straddling), a cluster-diverse **train pool of 40**, universal suffix
evaluated on **v3 test n=37** (every arm in `GATE7_V3_MATRIX_STATS.json` carries `"n":37, "split":"test"`). A
**refusal-direction off-by-one** was also found and fixed: builders store `hidden_states[L+1]` labelled `L` but
`gcg_optimizer.py:173` read `hidden_states[layer]` → a 1-block shift (fix: pass `fit+1`). *(This is the same
absolute-position/index bug class that has now hit this repo repeatedly.)*

## 13. The fair GCG attack-objective matrix (Q1–Q4) — a definitive NON-SPECIFIC NEGATIVE [V]

Llama-3.1-8B bf16, GCG, suffix_len 16, **batch 32 × 200 steps** (4× the first-cut's 50), v3 test n=37.
Source `reports/GATE7_V3_MATRIX_STATS.json`. **Two scope corrections before the table [c2]:** (i) **"3 seeds"
is true of 5 of the 10 arms only** — `arm03`, `arm08`, `arm08r`, `arm10`, `arm10r` each carry **one** seed,
which means **Q2 (L12) and Q4b (combined), both quoted below, are single-seed results** in a section whose
whole argument is that a single seed swings ~0.24 ASR. (ii) `batch 32` is **[R]**: the only committed GCG
manifest (`configs/manifests/phase9_gcg_mac_matrix.json`) says `batch_size 64`; suffix_len 16 and 200 steps
are confirmed. **Headline — refusal↓@L18 vs its norm-matched random@L18 (3 seeds, [V]):**

| seed | refusal@L18 ASR | random@L18 ASR | ΔASR | McNemar p |
|---|---|---|---|---|
| 42 | 0.324 | 0.351 | **−0.027** | 1.000 |
| 43 | 0.405 | 0.243 | **+0.162** | 0.109 |
| 44 | 0.162 | 0.243 | **−0.081** | 0.508 |
| **mean** | **0.297** | **0.279** | **+0.018** | — (swing ~0.24 ≫ mean) |

**Sign flips across seeds, no seed significant, mean +0.018 dwarfed by the ~0.24 between-seed swing → the
validated refusal-suppression objective is statistically indistinguishable from a random direction as a GCG
signal.** Companion arms: **Q4** concept↑@L9 mean 0.252 = its random 0.252 (inert, 3 seeds); **Q4b** combined
0.216 < refusal-alone (adding concept *degrades*; single seed). **Q2** refusal↓@L12 (Jacobian
sensitivity-peak) ASR 0.216 < vanilla, vs its random **+0.108** — and this arm needs two caveats it was
previously reported without **[c2]**: (a) it is the **one arm where the mechanism objective beats its
norm-matched control**, and while McNemar is ns (p=0.125) the **bootstrap CI EXCLUDES zero, boot95 [0.027,
0.216]**; (b) **L12 is the single layer that FAILED the ablate+induce validation gate**
(`refusal_direction_llama_SELECTED.json`: L12 `ablate_gain 0.0, induce_gain −0.3333,
both_gains_positive=false`; L18 selected at score 1.1333) — so a negative *or* a positive at L12 says
nothing about whether a validated mechanism direction is reachable. Both readings rest on one seed. **Q5 mechanistic-validity** (`GATE7_V3_MECH_VALIDITY_seed42.json`): at seed 42 the
refusal-optimized suffix suppresses the refusal projection *less* than a random suffix (−1.66 vs −2.04) — but this
seed-42-only reading was **[W] withdrawn** by the Asymmetry sprint (seeds 43/44 reverse it on 37/37 & 35/37
prompts, mean −2.013 vs random −1.204; seed 42 drew an unusually strong random). The **ASR negative stands and
sharpens.** *(The earlier first-cut pair "refusal 0.465 ≈ random 0.464" is **[R]**: its run-dirs are not retained;
this committed 3-seed matrix is the citable replacement.)* ⚠ **Provenance limit of the replacement [c2]:** the
stats JSON reproduces every number above exactly, but **all 20 per-seed run directories it names are absent
from `outputs/`** (globbed 20/20 missing). The sprint's headline Gate-7 negative is **summary-JSON-backed but
not raw-reproducible** — the largest single verification gap in this log, and one §22 previously did not
disclose. **Not done:** MAC/TROPT arms 11–13; a true 2nd-order ‖J‖² Jacobian loss (the "Jacobian objective"
was a first-order L12 proxy — and see above, at a layer that failed validation).

## 14. Phi-4-mini-reasoning — a third family (Q6): dissociation REPLICATES [V]

`microsoft/Phi-4-mini-reasoning` (~3.8B, 32 layers). **X1 behavioral** (n=30/split, native reasoning): DS raises
ASR **+0.066 train / +0.100 test** — but Phi is **weakly aligned** (direct 0.567/0.700 vs Llama 0.116), so
neutral≈DS (limited headroom). **X2**: refusal direction strongly separable at every layer yet ablate+induce
validates at **only L14 (1/6 layers)** — representation ≫ behavioral potency. **X3** (test n=42): refusal-ablation
ASR 0.714 → **0.952** at α=1, refusal_rate → 0.000, random-ablation flat (0.714) → **ΔASR +0.238, McNemar
p=0.006** (causal, dose-dependent, specific). **X5**: neither concept nor refusal linear readout predicts jailbreak
(all AUC CIs span 0.5, n=42 underpowered). Geometry also replicates: **|cos(concept, refusal)| ≤ 0.056 at
every Phi layer [c2]**, matching Llama's §4.2 orthogonality.

⚠ **Scope correction — what "replicates" means here [c2].** `docs/THIRD_FAMILY_REPLICATION.md` contains X2
geometry, X3 refusal-ablation and X5 readout **only**: there is **no Phi concept-ablation arm with a
count-matched random control**. The plan's own Gate E says *"only claim cross-family dissociation after
**both** concept intervention and refusal intervention have appropriate random controls."* So what replicates
on Phi is the **refusal half plus the readout dissociation**; the concept half — the "epiphenomenal by
specificity" result that carries Part D §10 — was **never tested outside Llama and Qwen3**.
**Not done:** the Phi concept-ablation arm; Phi objective-transfer GCG; a DeepSeek-R1 secondary replication;
plan Phase 6 (powering up the Phi readout on a leakage-free ≥60-item cohort) was **consciously dropped**
(execution log, 08-12 01:06); Phi X3 is thinking-**off** (an original native-reasoning run was killed for a
projected ~50 h and rescoped).

## 15. Quantization extension (Q7): the mechanism survives bf16 / 8-bit / 4-bit [V]

Llama-3.1-8B, refusal axis L18, test n=42, activation-space ablation vs norm-matched random, α∈{0, 0.5, 1.0}.
Extends Continuation-V2 §29 with a full **dose-response + specificity control** at each precision:

| precision | refusal-abl ASR (α=0/0.5/1) | random-abl ASR | refusal_rate 0→1 | α=1 ΔASR | McNemar p |
|---|---|---|---|---|---|
| bf16 | 0.191 / 0.476 / 0.476 | 0.214 / 0.143 / 0.191 | 0.762→0.238 | **+0.286** | 4.9e-4 |
| 8-bit | 0.262 / 0.429 / 0.524 | 0.262 / 0.143 / 0.143 | 0.738→0.238 | **+0.262** | 7.4e-3 |
| 4-bit NF4 | 0.167 / 0.643 / 0.762 | 0.167 / 0.167 / 0.167 | 0.762→0.071 | **+0.571** | <1e-4 |

At every precision the refusal-ablation is causal, dose-dependent, and **specific** (random flat/drops); strongest
at 4-bit. **Not done:** quantized concept-geometry/predictor and the attack-objective GCG arms under quant.

---

# PART F — the Asymmetry Sprint: *the medium, not the mechanism, fails* (sub-sprint 5, 08-11 → 08-12)

`docs/ASYMMETRY_FINAL_SYNTHESIS.md`. This is the sprint's intellectual crux. It resolved the tension the whole
program had reached: **a refusal direction is causal in activation space, yet GCG suffixes optimized toward it
fail like random.** Two hypotheses — **H1** (the direction is not *reachable* from input tokens; the failure is
geometric) vs **H2′** (it *is* reachable, but *discrete* search can't find the tokens; the failure is the
optimizer). **Result: H1 is rejected, H2′ is supported, and we measured the boundary.** Verified for this log by
`wf_92ba16b8` agent `asymmetry`.

**Headline.** The refusal direction is **unusually easy to reach** from input tokens (**4.71×** a
covariance-matched control); a **continuous** input optimizer exploits this to jailbreak at **ASR 0.784 vs 0.153**
dose-matched control (ΔASR **+0.631**); **discrete** optimization toward the *same direction* gains **+0.009 ΔASR**,
sign-unstable and below the judge's noise floor. **The medium, not the mechanism, is what fails.**

## 16. Gate-by-gate

| gate | question | verdict | key numbers | verification |
|---|---|---|---|---|
| **A** | is the published token objective correctly configured? | **NEGATIVE — defect** | read a fixed absolute index from `train_tasks[0]`: correct for **1 of 40** prompts, 5 template tokens from where the axis was fitted | [R] code-audit |
| **B** | is the linear surrogate valid at token scale? | **NEGATIVE (Llama) — and worse than a null** | Pearson r **0.8395 → −0.0015** (train) and **0.8104 → −0.3242** (test) from ε=0.1 to ε=1.0, vs random directions **+0.041 / +0.129** and activation-random **+0.204 / +0.334** at ε=1.0 | **[V] [c2]** recomputed from `asym_p1_reach_{train,test}_…7503{61,62}/eps_scan.jsonl` |
| **C** | is the direction reachable from suffix tokens? | **POSITIVE — strongly** | ‖Jᵀv‖ **4.71×/4.91×** (train/test) covariance-matched, pct 0.990; **~15×** isotropic; mech norm 22.04/19.79 byte-exact | **[V]** (ratio has a control-aggregation caveat; test 4.89×≈4.91×) |
| **D** | does continuous input control work, specifically? | **POSITIVE — at one dose, read on test (EXPLORATORY)** | **ASR 0.784 vs 0.153**, ΔASR **+0.631**, 3 seeds, **0 sign flips**, all p<1e-4 — but see the inverted-U below | **[V]** `ASYM_P2_DOSEMATCHED/SEED43/SEED44.json`, reproduces to 3rd decimal |
| **E** | does mechanism-derived *token* optimization work? | **NEGATIVE, unstable** | position-corrected ΔASR **+0.009** (legacy +0.018); sign-unstable; below ±0.03–0.08 judge floor | **[R/log]** heldout-ASR run-dirs not retained |
| **F** | does the causal locus generalize across concepts? | **PARTIAL** (the artifact's own verdict — refusal half yes, concept half underpowered) | refusal ablation raises ASR **5/5** pairs, median specific ΔASR **+0.414**, **4/5** Holm-sig (chlorine ns); but **only 1 of 5 pairs (grenade) had concept-half attack headroom** — chlorine/pistol floor-limited, bomb/cocaine marginal | **[V] [c2]** `ASYM_P4_MULTICONCEPT.json` → `GATE_F.verdict = "PARTIAL … Do NOT claim 'general across concepts'"` |
| **G** | does a mechanism-derived defense follow? | **NEGATIVE (honest) — but floor-limited on test** | test: **no arm** reduces ASR (gate_two +0.024 ns); gate_concept ≡ gate_two (refusal half fires ~always). **[c2]** test DS ASR *without any defense* is **0.143**, so the test arm cannot demonstrate a reduction at all; on **train** the two-signal gate **Pareto-dominates** its random control (none 0.282 → gate_two 0.129, Δ **−0.153**, p=0.0010; over-refusal +0.141 vs unconditional +0.365) — EXPLORATORY | **[V]** `defense_2signal_…751316`; caveats `docs/TWO_SIGNAL_DEFENSE.md` §3–4 |
| **E′** | does removing the UNIVERSALITY constraint rescue it? | **NEG behaviourally, POS mechanistically** | per-prompt ΔASR 0/3 sig; projection **3/3 consistent** mean **−0.354** (Holm-survives s44) | **[R]** scalars consistent across 3 docs |

**Replication beyond the primary setting:** Gate C replicates on **Phi-4-mini** (isotropic 5.53×≈doc 5.56×,
covariance 4.10×) and under **4-bit NF4** (isotropic 13.62×≈13.25×) — the reachability asymmetry is **not a Llama
or bf16 artifact [V]**. Gate B does *not* fully replicate: on Phi the surrogate degrades but does not collapse — so
H2′'s **qualitative core** holds in both families while its **sharp form** (mechanism ends up worse-predicted than
a matched null) is **Llama-only** (stated in the paper body, not buried). *(A Phi Gate-B "inverts" claim was
retracted — train-split-only.)*

**Two Gate-C companion results, previously unreported [c2]** (both in
`asym_p1_reach_train_…750361/ANALYSIS.json`, cell `decision|hs19`, 15,360 substitutions):
1. **The reachable subspace R(v) is enormous for refusal** — `refusal_L18 R = 0.5846` vs random-direction
   mean **0.003936** and isotropic null **0.003906**, i.e. **148.5×**, `percentile_among_random = 1.0`. This
   is a far sharper statement of Gate C than the 4.71× gradient-norm ratio the log leads with.
2. **…but refusal gradients are barely more cross-prompt coherent than random — a NEGATIVE for the
   universality story.** `mean_pairwise_cosine 0.3482`, participation ratio 5.18, 92.9 % of pairs positive —
   against **8 random directions at mean 0.2680, max 0.3831**. Refusal is inside the random spread. This is
   the direct answer to the plan's flagged-HIGH-VALUE §5.5 hypothesis (*"a universal suffix should exist
   because the refusal gradient points the same way for every prompt"*): **it does not, particularly.**

## 17. The three-capability picture (the organizing claim)

| capability | works? | evidence |
|---|---|---|
| **intervene** on the direction in activation space | **yes** | Gate F, 5/5 pairs |
| **steer** it from the input, continuously | **yes** | Gate D, ΔASR +0.631 |
| **optimize discrete tokens** toward it | **no** | Gate E, +0.009, sign-unstable |

The first two working is what makes the third's failure *informative*: because the direction is reachable and
demonstrably exploitable by a continuous optimizer with the *same* objective on the *same* coordinate, the discrete
failure isolates **the discreteness itself**. **Four measured causes** (1–2 as previously reported, 3–4
restored **[c2]** from `docs/TOKEN_REACHABILITY_ANALYSIS.md`):

1. The first-order surrogate **collapses before one-token step size** (r 0.84 → −0.002 train / −0.324 test —
   past zero, and *below* both random controls).
2. A perfect solution inside the token simplex **retains only 5.7 %** of its effect once rounded to real
   tokens. *(Caveat: this measures **projection** retention only — no generation was ever run with the
   rounded suffix.)*
3. **§19.2 — what discrete suffixes actually do is GENERIC suppression, not the targeted intervention.**
   Sweeping the fit layer L10–L24, the refusal drop is ~0 before L14, grows monotonically with depth, and is
   **deepest at L24 — not at the L18 the objective optimized**. The refusal-suffix and random-suffix depth
   profiles are near-identical in shape, **Pearson r = 0.9965** (refusal vs plain doublespeak r = 0.9968).
   The suffixes differ in the *magnitude* of one shared profile, not in *where* they act — strong support
   for H4 (generic adversarial suppression). **This is the mechanistic content of the Gate-E negative:** GCG
   is not failing to hit the coordinate, it is hitting a generic direction that happens to include it.
4. **§6.1(c) — and it is not an overfitting failure.** Transfer ratio (test drop / train drop) is **> 1 in
   all 9 cells (1.17–2.00)**: the universal suffix suppresses refusal *more* on held-out prompts than on the
   pool it was optimized on. The "universal suffix overfits its suppression" hypothesis is **rejected**,
   independently of §19's per-prompt result.

⚠ **The one control that would qualify this whole hierarchy was never run [c2].** The activation intervention
is **all-position / all-layer** while the soft prompt is **16 input positions** — so the "activation >
continuous > discrete" ordering is **not budget-matched**. `docs/RESEARCH_HANDOFF_V2.md` §5.2 calls the
scope-matched activation arm (**D3**) *"the single cleanest missing control"* and ranks it the control a
reviewer will ask for first. Until it runs, the ladder is confounded with intervention scope.

## 17b. Gate D's dose response is an INVERTED U — and probe displacement is not mechanism control [c2]

Gate D is reported above as a clean positive, which is how it was carried through the sprint. The full dose
sweep (`docs/CONTINUOUS_VS_DISCRETE.md` §5, held-out) says something more interesting and more cautionary:

| budget_rel | Δ refusal proj | resulting proj | in natural range? | **ASR** | refusal_rate |
|---|---|---|---|---|---|
| 0.05 | −1.07 | +3.35 | yes | 0.135–0.162 | 0.730 |
| **0.10** | **−8.22** | −3.80 | no | **0.757–0.838** | **0.027** |
| 0.25 | −8.95 | −4.53 | no | *(not judged)* | — |
| **1.00** | **−20.09** | **−15.68** | no | **0.000** | **0.000** |
| random @0.10 | −2.21 | +2.21 | yes | 0.081 | 0.460 |

Too little suppression and the model still refuses; the right dose jailbreaks; **too much drives the residual
so far off-manifold that the model neither refuses nor complies** — ASR 0.000 *and* refusal_rate 0.000 at the
largest displacement of the whole sprint (verified independently:
`asym_p2_soft_refusal_free_b1.0_seed42_…750364/projections.json`, n=37, baseline 4.4170 → final −15.6751,
Δ **−20.0921**, per-prompt sd collapsing 2.532 → 0.252). Note also the plateau between 0.10 and 0.25 (−8.22
vs −8.95) before the jump.

**Two consequences the paper must carry.** (1) **Probe displacement is not evidence of mechanism control** —
the run that moved the coordinate furthest produced *zero* behavior. This is the same lesson as §20.1's
objective-vs-behavior dissociation, arrived at from the opposite direction, and it independently indicts any
mechanistic result reported as a projection shift. (2) **Gate D is EXPLORATORY, not confirmatory**: 0.10 was
selected as optimal *by reading the dose sweep on test*. A confirmatory dose needs freezing on the untouched
v3 dev split. The headline 0.784 vs 0.153 is real and 3-seed sign-stable — but it is the peak of a curve that
was chosen after seeing it.

## 18. The λ=10 probe — the negative survives a meaningful objective weight [R/log]

Gate E's negative carried one caveat: at the published λ=0.25 the refusal term is only **0.37 %** of the total
GCG-selection loss, so the negative could mean merely "the position fix alone doesn't rescue it." **Re-run at
λ=10 (~40× published), 3 seeds:** ΔASR **+0.622 / −0.162 / +0.189**; McNemar 1.55e-6 / 0.109 / 0.065.
**Sign-consistency 2/3 → FAILS. The negative STANDS and is stronger:** at λ=10 the objective *works internally*
(carries 24–34 % of selection loss, drives held-out projection past zero in all 3 seeds) yet behaviour does not
follow stably; all three |ΔASR| exceed the judge floor yet disagree in sign. **Do not quote the mean (+0.216)** —
three seeds that disagree in sign estimate nothing. This rules out the "discrete negative was an implementation
artifact" alternative on two independent grounds (position fix changed nothing: +0.009 vs +0.018; a 40× λ increase
produced no seed-stable gain). *(Verification note: the λ=10 and position-corrected Gate-E heldout-ASR run-dirs
were pruned from `outputs/`; these two numbers are backed by three mutually-consistent committed `.md` files but
were **not JSON-reproducible** in this pass — the only such gap in Part F besides E′.)*

## 19. Per-prompt vs universal (§7.5, added mid-sprint per Mahmood) [V/R]

Tests whether the token-space negative is a *universality* failure. One suffix optimized **per prompt** (vs one
universal suffix), 3 arms × 3 seeds × 2 budgets. **The two endpoints dissociate:** projection (internal target)
**3/3 sign-consistent, mean −0.354** (the objective moves its coordinate further than random); behaviour (ΔASR)
**inconsistent, 0/3 significant.** **Answer: NO** — the universal negative is *not* a universality/prompt-specificity
failure (per-prompt suffixes even transfer off-diagonally ≥ the universal arm's own held-out; their specificity is
matched by a random direction; the projection moves so the objective is not inert). **The failure sits downstream
of the representation.** A methodological result that outlives it: **compute dominates direction** — the
matched-*random* arm alone gains **+0.216 ASR** from 5→200 steps/prompt, larger than every direction effect in the
sprint. Had §7.5 been run only at full budget, "per-prompt beats universal" would have followed, produced entirely
by compute using a random direction; the compute-matched arm was added pre-registration on exactly this reasoning.

## 20. Methodological findings that stand on their own (Asymmetry) [V]

1. **A representation objective reading one absolute token index** (Gate A) — produced a published negative;
   correcting it changed the result +0.009 vs +0.018 (i.e. nothing), which *is* the finding: the defect was a
   confound, not the cause.
2. **Two ASR thresholds (0.25 / 0.5) reported under one name** — conclusion-neutral here (27 contrasts, 0 sign
   flips) but only because it was checked.
3. **A judge that flips labels between runs at temperature 0** → ±0.03–0.08 on ASR at n=37, *larger than
   several previously-reported effects including the +0.018 it retired.* Any n≈37 ASR paper without a measured
   judge-noise floor is reporting effects it cannot distinguish from resampling. ⚠ **[c2] the flip rate quoted
   here has been superseded twice — use §20.3's numbers, not this section's.** The "~3.4 %" was an n≈148
   hand-count (execution log, not an artifact, **[R]**); the measured replicate design gives **35.5 % inside
   the 4.65 % boundary band and 1.65 % corpus-wide** (`outputs/asym_p203_judge_replicates.json`), and the
   two-pass corpus disagreement is **0.62 %**. The ±0.03–0.08 floor derived from the retired figure is what
   Part F used to retire the +0.018 and the λ probe; §20.3's variance decomposition (judge = 1.8–7.5 % of
   total variance, sampling SD 0.067 dominating judge SD 0.009–0.019 by 3.5–7.4×) **reaches the same verdict
   for a different reason** — those effects are below the *sampling* floor, not the judge floor.
4. **The naive covariance-matched random control is rank-1 degenerate** (E[|cos|] 0.97–0.998, ~1 effective
   direction because the activation covariance is dominated by one mode). Dropping the top component gives mean
   |cos| 0.094 and moved the headline Gate-C ratio from an inflated **6.74× → 4.71×**.

**The sprint's own errors (kept as a record):** a **Gate-E clause-(ii) POSITIVE on one seed (08:52) was
RETRACTED 10:05** when seed 43 reversed it — "the sprint's main judgment error"; a Gate-F verdict was published on
partial `raw.jsonl` from a still-running job (aggregator now requires `DONE.json`); a Phi Gate-B "inverts" claim
retracted (train-split-only); the covariance-control 6.74×→4.71× correction. **Every gate that survived did so on
≥3 seeds or both splits — the rule the λ probe is bound by.**

---

# PART G — Section 20: bounding the negatives honestly (sub-sprint 6, 08-12 → 08-14)

`docs/SECTION20_RESULTS.md`. The final sub-sprint took the program's *behavioral negatives* — which had been
reported as point estimates — and asked what they can actually exclude, separating the **objective-space** claim
from the **behavioral** claim it must never be conflated with. Verified for this log by `wf_92ba16b8` agent
`section20`; almost every number reproduces from JSON (exceptions flagged).

- **20.1 The refusal coordinate is necessary — in objective space. [V]** Two soft-prompt objectives at matched
  budget, 3 seeds: `task` (minimise target CE) vs `task_orth` (CE + a penalty pinning the refusal projection at
  baseline). **Pinning the refusal projection costs 78.0 % of the achievable CE reduction** (mean progress 12.7 %
  vs 57.4 %), 3/3 sign-consistent. Manipulation checks pass: the pin holds the projection (Δproj ≈ −0.03 mean —
  *report says −0.026; JSON −0.032, a minor mismatch that doesn't change the conclusion*) while plain `task` moves
  it **−3.09** as a pure side effect. (All CE-table numbers JSON-confirmed exactly.)
- **20.1 follow-up: that necessity does NOT transfer to behaviour. [B]** 222 generations (0 empty, 0 judge-fail):
  ΔASR(task − task_orth) = **+0.135 / −0.027 / +0.108** — **2/3 sign-consistent, 0/3 significant, every CI spans 0.**
  A 78 % change in what the optimizer minimises produces a behavioural change we cannot distinguish from zero.
  **This is the program's central dissociation one level down: objective vs behaviour, not representation vs
  behaviour — §20.1 must never be cited as a behavioural result.** *(ΔASR per seed JSON-confirmed; the McNemar/
  Wilcoxon p-values and CIs in the report are not stored in the artifact — [R].)*
- **20.2 Per-prompt mediation is MODALITY-SPECIFIC. [R]** In the unconfounded vanilla-discrete arm, more refusal
  suppression → more jailbreak: partial r **−0.291** (n=74, p=0.012). It does **not** replicate for continuous soft
  prompts (r −0.008, n=111) — and at n=111 the soft arm *excludes* an effect as strong as the discrete one, despite
  a larger drop range. Consistent with the coordinate acting as a **gate, not a dose** (the stratified saturation
  test is underpowered). *(Verification gap: no `asym_p202` artifact exists; the partial-r values are not
  reproducible from any committed §20 JSON — treat as report-only pending the mediation artifact. The soft-arm
  Δproj means that motivate the framing **are** JSON-confirmed.)* **One well-powered side finding from the
  same analysis, previously unreported [c2]:** in the `task_orth` (pinned) arm, per-prompt success correlates
  with the *baseline* refusal projection at **r = −0.512, p = 9.6e-09**, versus **−0.037** in the unpinned
  `task` arm (`SECTION20_RESULTS.md` §3b). That is the only **behavioural** evidence anywhere that the §20.1
  pin actually did what it claims — when the optimizer is forbidden to move the coordinate, whether a prompt
  jailbreaks falls back on where its refusal projection already sat.
- **20.3 Judge reliability — the "5.4 %" figure is superseded. [V]** Band-only replicate design (M=5, 665 calls,
  15× cheaper): intermediate band flips **35.48 %** (n=93) while the **extreme control flips 0/40** (SD 0.0023) —
  validating the band-only design rather than assuming it. Corpus-level two-pass disagreement ≈ **0.62 %**, not
  5.4 % (that was one arm at n=37). **Variance decomposition:** sampling SD 0.067 (92–98 %) dominates judge noise
  (0.009–0.019) by **3.5–7.4×**. The denoising was *carried out*: re-running all 18 §7.5 contrasts on the majority
  vote moved **7/18 ΔASR** (max 0.054 = exactly 2 rows of 37) and **flipped 0/18 significance**. Practical
  consequence: individual ΔASR carry ~±0.05 of judge-attributable uncertainty — 54 % of the whole Doublespeak
  effect — so **do not quote ASR to three decimals.**
- **20.4 Every behavioural negative is bounded at ~±0.2 ASR. [B]** TOST equivalence bounds (paired bootstrap): the
  nulls rule out **only effects larger than ~0.19–0.27 ASR.** For scale, **the Doublespeak effect itself is +0.100
  ASR** (test split, majority-vote, n=30: DS 0.800 vs direct 0.700 — `baseline_drift_…741427`). **So the bounds are
  1.9–2.7× the size of the phenomenon the paper is about:** our behavioural nulls cannot exclude an effect two-to-
  three times larger than Doublespeak. Every "no effect" must read "no effect larger than ~0.2 ASR at this n." (All
  six bound rows JSON-confirmed.)
- **20.4 pass 2 — the bounds are SAMPLING-limited, not judge-limited. [V] [c2]** *(Ran after this log's first
  revision; `outputs/asym_p204_equivalence_pass2.json`, commit `c04d556b`.)* The plan's specified pass 2 (a
  multi-direction SD supplied by §20.6) is unreachable because §20.6 is corpus-blocked, so the bounds were
  instead recomputed on the **judge-denoised endpoint** (majority vote over M=5 on the 4.65 % band) — the
  other stated motivation. Result: **the bounds got 6.4 % WIDER, not tighter** (mean worst bound **0.2117 →
  0.2252**; `full mech−random 0.1892→0.2432`, `full random−vanilla 0.2162→0.2432`, the other four rows
  unchanged; every change an exact multiple of 1/37, i.e. 1–2 rows). This is not a defect in the denoising —
  it is the demonstration that **no amount of better judging tightens these bounds**: the bound is
  max(|CI_lo|,|CI_hi|), so removing judge noise shifts point estimates without shrinking sampling variance,
  and here the denoised estimates landed slightly *further* from zero. Exactly what §20.3's variance
  decomposition predicted. The artifact is written **`provisional: false`** — §20.4 is a finished deliverable
  and the bounds stand at **2.1–2.3× the Doublespeak effect**. Only more prompts help; the ceiling is 179.
- **20.7 Compute dominates; the direction term buys ≤23 %. [V]** §7.5's central negative was measured on binary
  ASR at **0.05 power** (an uninformative null). Re-asked on the optimization objective (best-so-far GCG loss;
  continuous, paired, judge-free, full n=37): 5→200 steps improves **37/37 prompts** at **p=1.1e-07** for all three
  arms — a demonstrably sensitive endpoint. On it, **0 of 18 arm contrasts are significant**, and they are
  *bounded*: the mechanism−vanilla advantage is at most **22.7 %** of the compute effect (mechanism−random 17.1 %).
  **This converts the program's weakest claim from "we found nothing, with 5 % power" into "we found nothing, on an
  endpoint able to find something 4× smaller than what we sought."** **200→600 update [V] [c2]:** the seed-42
  extension has since completed at full n — `outputs/asym_p207_objective_curve_seed42_FINAL37.json`
  (`n_paired 37, n_expected 37, interim false`, commit `dce44a92`) gives **mean Δ −0.0723, p=0.2515, 22/37
  prompts improved: a NULL.** This *supersedes* the earlier "the estimate oscillates −0.079/−0.122/−0.062 as n
  fills in" reading — the oscillation was interim noise and the full-n answer is that tripling compute past
  200 steps buys nothing detectable. (Seeds 43/44 still filling in; see §23.) *(Compute effect
  and 0/18 nulls JSON-confirmed; the specific loss-unit bounds 0.2151/0.1618 are report-only but their ratios are
  internally consistent. Objective space only — licenses no behavioural claim.)*
- **20.8 is BLOCKED, and no endpoint change fixes it. [BLK]** The corpus ceiling is **179** items (→ ~139 held-out
  after a disjoint 40-item train pool), not the 300 the plan assumes; at n=37 the paired-McNemar **power against
  §7.5's own reported effect is 0.05 — the false-positive rate.** The **graded endpoint does not rescue it**:
  0/18 significant either way, only **2.2 % tighter → effective-n multiplier 1.04×** (because 92.7 % of rows sit at
  exactly 0/1). *(An earlier "1.34×" was a standardization bug — binary width standardized by an assumed binomial
  SD vs graded by its empirical SD; corrected.)* **Resolution: report behavioural results as equivalence bounds,
  not point estimates; only a second corpus buys real behavioural power.** *(Endpoint-compare numbers **and**
  the corpus ceiling are JSON/CSV-confirmed: `data/clearharm/clearharm_179.csv` exists at the **repo root**,
  179 data rows, cols `instruction, category, clearharm_native_target, clf_label`. A previous revision of this
  log called the file missing — that was a search-scope error confined to `doublespeak_causality/`; the
  caveat is **withdrawn [c2]**.)*
- **20.5 / 20.6 / 20.9 — NOT STARTED; and §20.1's headline needs one more run. [BLK] [c2]** Previously absent
  from this log entirely, in either direction. Per `docs/OWED_SUBMISSIONS.md`: **§20.5, §20.6, §20.9 were
  never started**; §20.6 specifically is **blocked by the same 179-item corpus ceiling** as §20.4 pass 2
  (`SECTION20_RESULTS.md:207` — *"§20.6 and §20.4-pass-2 are blocked by the corpus, not the endpoint"*), which
  is the link that explains why §20.4 stopped at one planned pass. Separately, the **§20.1 μ sweep**
  (μ ∈ {0.1, 0.3, 1, 3, 10}) was **not run** (0 matching output dirs) and is *required before §20.1's "78 %
  cost" can go in the paper*: 78 % is the price of a **near-total pin** (Δproj ≈ −0.03), not the price of the
  coordinate as such. And §20.7 is delivered at **half its planned span** — the plan
  (`ASYMMETRY_SPRINT_PLAN_2026_08_11.md:607`) specifies **600 *and* 2000 steps**; the 2000-step point was
  deferred by decision.

**What §20 changes about the paper:** (1) a **necessity/usefulness distinction** — the refusal coordinate is
necessary for the continuous attack yet useless as an optimization target (plain task optimization already moves it
−3.09 for free, ~9× further than the discrete mechanism objective managed), reconciling §20.1/§20.2/§7.5 without
any being wrong; (2) an **objective-vs-behaviour dissociation** distinct from representation-vs-behaviour; (3)
**every behavioural negative restated as a ±0.2 ASR bound**; (4) two methodological figures corrected (judge-flip
rate, graded-endpoint power); (5) a **powered null replaces an uninformative one** (≤23 % of the compute effect on
a sensitive endpoint).

---

# PART H — cross-cutting: corrections, verification gaps, backlog, bottom line

## 21. The honesty ledger (claims we changed about our own work)

The machine-regenerated `reports/CLAIM_AUDIT_TABLE.md` tracks the Aug 2–9 tally (**95 claims: 77 VERIFIED, 8
WITHDRAWN, 4 SUPERSEDED, 6 UNDERPOWERED, 0 CHECK-FAIL, 173 numeric checks / 0 failures**). Across the whole sprint
the load-bearing corrections were:

1. **[W] P8.0 sub-additive interaction (p=0.045)** → saturation artifact; null at the decisive dose (§8.5). *The
   pre-registered held-out split is what caught it — train sub-additivity reversed to test additivity.*
2. **[W] "5-fold CV AUC 0.887±0.106"** → non-reproducing recompute 0.869±0.055.
3. **[W] "carry heads behaviorally inert" (binary)** → "undetermined" after the specificity control failed.
4. **[W] §10 "informative-null MDE ≤0.09"** → epiphenomenality re-grounded on **specificity** (random +0.161 >
   concept +0.046), not equivalence.
5. **[W] Gate-E clause-(ii) single-seed POSITIVE** → retracted when seed 43 reversed it (the Asymmetry sprint's
   main judgment error).
6. **[W] Q5 seed-42 "mechanism non-specific at the mechanism level"** → withdrawn; seeds 43/44 reverse it.
7. **Covariance control 6.74× → 4.71×** (rank-1 degeneracy fixed).
8. Numerous scope tightenings (L8–L11→L8–L10; "monotone readout"→terminal L31 spike; "3/4"→"2/4"; DS "triples"→
   "~2–3× on clearharm train, no effect on the small v3 test split"). **Direction of every finding preserved.**
9. **[c2] The GCG candidate-selection bug (P9.0)** — the mechanism objective entered the gradient but not
   candidate selection, so *every* pre-fix "mechanism-derived GCG is net-negative" statement was made with the
   objective effectively off. Fixed in `84bf7a1e`/`76acb44a`; nothing before it is citable (§8.7).
10. **[c2] The λ task-loss endpoint statistic** — summarised from a single endpoint, and in one comparison as a
   *ratio of two endpoints*, which swung **1.45×–34× across seeds** and was **withdrawn**. The standing rule
   (`RESEARCH_HANDOFF_V2.md` trap 7) is best-so-far only. Commits `f91acf6b`, `1b5b4d94`.
11. **[c2] Corrections made by the 08-14 re-audit** (`RESEARCH_LOG_AUDIT_2026-08-14.md`), all of them defects
   *in this document* rather than in the underlying work: Gate-B r **0.817→0.8395 and +0.140→−0.0015/−0.3242**
   (a sign error that erased the sprint's sharp H2′ claim); quant deltas **+0.26/+0.29/+0.52 → +0.286/+0.262/
   +0.571** (bf16↔8-bit swapped); P8 α=0.20 **+0.194/p<1e-12 → +0.1417/p=1.2e-04** (wrong run); Gate F
   **POSITIVE → PARTIAL** (the artifact's own verdict); §5.8 train AUC **0.867→0.863** (pooled column
   mislabelled); P10 power **275 for 0.07 → 275 for 0.09, 419 for 0.07**; and the withdrawal of a false
   "`clearharm_179.csv` missing" caveat.

**The recurring failure mode, named:** *a single-seed or single-split quantity promoted to a verdict.* It appears
in P8.0, the Gate-E retraction, and the Q5 withdrawal. Every surviving claim rests on ≥3 seeds or both splits.

## 22. Verification gaps in THIS log (numbers not reproducible from committed JSON)

Stated plainly so an external reader knows exactly what is and isn't machine-backed:

- **Gate-E discrete +0.009** and the **λ=10 probe (+0.622/−0.162/+0.189)** — heldout-ASR run-dirs pruned from
  `outputs/`; backed by three mutually-consistent committed `.md` files but not JSON-reproducible here.
- **Gate-7 first-cut "refusal 0.465 ≈ random 0.464"** — run-dirs absent; **superseded** by the committed 3-seed v3
  matrix (0.297 vs 0.279), which backs the same conclusion.
- **§20.2 partial-r (−0.291 / −0.008 / −0.170)** — no `asym_p202` artifact; report-only.
- **§20.7 loss-unit bounds (0.2151 / 0.1618)** and **§20.1-followup p-values/CIs** — only the ratios/deltas they
  normalize are in the JSON.
- **Continuous soft-prompt seed-42 endpoints 0.757/0.081** — the scoring file was repurposed; the **3-seed
  0.784/0.153/+0.631 synthesis figure IS JSON-confirmed** (`ASYM_P2_DOSEMATCHED/SEED43/SEED44`), so the finding
  stands.
- **[c2] THE LARGEST GAP, previously undisclosed: all 20 per-seed run directories of the Gate-7 v3 matrix
  (§13) are absent from `outputs/`** (globbed 20/20 missing; `outputs/stage_gcg_full/` now holds only
  refusal-direction files). The sprint's headline attack-objective negative is backed by
  `GATE7_V3_MATRIX_STATS.json` — which reproduces every printed number exactly — but is **not raw-reproducible**.
- **[c2] `configs/manifests/phase9b_gcg_v3.json`** (cited in §25) **does not exist**; `configs/manifests/`
  holds 8 files and none is a v3 GCG manifest. Consequence: §13's `batch 32` is unverifiable and the one
  surviving GCG manifest says `batch_size 64`.
- **[c2] §5.9's token-0 AUCs (0.936 / 1.000)** — the run-dir summary stores no AUC field.
- **[c2] §5.8's per-split AUCs, §3's 4,909-value and 113→205 test counts** — prose-only, no machine artifact.
- **[c2] `EXPERIMENT_REGISTRY.csv` (last updated 08-05) and `BUG_AND_DEVIATION_LOG.md` (08-08) stopped being
  maintained mid-sprint** — the registry holds 395 rows against 605 output dirs and matches `asym` once
  against 65 such dirs, so **the entire Asymmetry sprint (Part F) and Section 20 (Part G) are unregistered and
  their deviations unlogged**, in a document that advertises provenance discipline. Relatedly the sprint's one
  formally logged pre-registration deviation — the Gate-7 (§14–18) decisive refusal arm having run at an
  **un-validated L22 vector on the leaky v1 GCG split**, resolved by running both directions — is recorded
  only in the bug log, though §11/§22 quote that run's numbers.
- **[c2] ~~`clearharm_179.csv` not in this checkout~~ — WITHDRAWN.** The file exists at the repo root
  (`data/clearharm/clearharm_179.csv`, 179 rows); the earlier search was scoped to `doublespeak_causality/`.
  The corpus-ceiling arithmetic in §20.8 is artifact-backed.

Everything else in Parts A–G that carries a **[V]** was reproduced from an opened output file (7/7 → in practice
6/7 of the whole-sprint load-bearing headline numbers PASS direct JSON re-verification; the 7th, Gate-7 first-cut,
is superseded by a committed replacement).

## 23. What is NOT done (the blunt backlog)

- **Cross-family fine-grained circuit:** the retrieve→write→carry→readout map is **Llama-only**; Qwen3 and Phi-4
  confirm the *dissociation*, not the circuit anatomy. H2′'s sharp form (surrogate collapse to *worse-than-null*)
  is Llama-only. **[c2] And on Phi the *concept half* was never tested at all** — no concept-ablation arm with
  a count-matched random control exists, which is what the plan's Gate E requires before the phrase
  "cross-family dissociation" is licensed.
- **[c2] The D3 scope-matched activation arm** — the activation intervention is all-position/all-layer while
  the soft prompt is 16 input positions, so §17's "activation > continuous > discrete" ladder is **not
  budget-matched**. The handoff calls this *"the single cleanest missing control"* and *"the control a
  reviewer will ask for first."* Not run.
- **[c2] Gate D is exploratory** — its dose (0.10) was chosen by reading the sweep on **test**; a confirmatory
  run on the untouched v3 dev split is owed. The 5.7 % rounding-retention figure is projection-only; **no
  generation was ever run with a rounded suffix.**
- **[c2] The §20.1 μ sweep** (μ ∈ {0.1,0.3,1,3,10}) — not run; §20.1's "78 % cost" is the price of a
  near-total pin, not of the coordinate, until it is. **§20.5 / §20.6 / §20.9** never started (§20.6
  corpus-blocked). **§20.7's 2000-step point** deferred, so that curve covers half its planned span.
- **Behavioral sufficiency of the concept circuit** was never positively demonstrated (carry-install is NULL).
- **The behavioural power problem (§20.8):** at n=37 the design has 0.05 power against its own effect size; every
  behavioural null is a ±0.2 ASR bound, not a point null. Only a second corpus fixes this.
- **Attack-objective completeness:** MAC/TROPT arms never run; a true 2nd-order Jacobian loss never implemented;
  quantized attack-objective arms not run; Phi objective-transfer GCG and a DeepSeek-R1 reasoning replication not
  run.
- **No defense** survived (Gate F/G both honest negatives) — the redeeming datum is zero over-refusal on
  unrelated-normal prompts.
- **Owed compute (live as of 2026-08-14, [c2] — the previous "27/74" is stale):** the §20.7 200→600 extension
  has **seed 42 COMPLETE at 37/37 with a NULL result** (Δ −0.0723, p=0.2515); **seed 43** is filling in with
  all four shards launched; **seed 44** has only **shard 0** launched — which the owed-submissions doc flags
  as a **biased subset**, so seed 44 must not be read until its remaining shards land. Six `gcg_perprompt`
  jobs were running at the time of this revision, so these numbers move. Also: the soft-prompt A4 scored-ASR
  file appears overwritten (a live audit gap).

## 24. Bottom line for an external reader

**Solidly established (cross-cohort, locked-test, controlled, recomputed from raw, cross-model where noted):**
1. A complete, **distributed concept circuit** for Doublespeak on Llama-3.1-8B (demo-KV retrieval L8–L10 → L9 MLP
   write → L14–L21 mediated carry heads → L30–31 output), necessity Holm-significant at every stage, carry stage
   partially sufficient; no single head/edge/layer is a bottleneck; **readout ≠ mechanism** (readability peaks L31,
   causality at L9/L14–21).
2. **The concept circuit is behaviorally epiphenomenal by specificity** — ablating it moves ASR +0.046 ns while a
   count-matched random ablation moves +0.161 (~3×); clearharm concept ablation is exactly 0.000. **[c2]** Two
   independent measures agree: the concept channel is also invisible to the *loss geometry* (gradient-norm AUC
   0.583, CI spans 0.5, vs refusal 0.807 — §12), and the `doublespeak_signature` direction is causally inert
   to within 1e-05 while `d_Direct` moves the same readout +0.167→+0.971 (§5.10).
3. **A single orthogonal refusal direction is the behavioral lever** — ablate → ASR +0.43–0.48 (a stronger attack
   than Doublespeak); re-inject → 0.000 with fluent refusals; decision read mid-late (~L22); the two pathways are
   causally decoupled and **add, never synergize**; the refusal projection **predicts** jailbreak (AUC 0.87).
4. **The dissociation generalizes** to Qwen3-14B and Phi-4-mini, and survives 8-/4-bit quantization and an
   independent from-scratch implementation.
5. **The mechanism is causal, reachable, and continuously steerable, but not discretely optimizable** — continuous
   soft-prompt ASR 0.784 vs 0.153; discrete GCG toward the same coordinate +0.009 (sign-unstable, below judge
   noise; survives a 40× λ increase). *The medium, not the mechanism, fails.* **[c2]** And we now know *why*
   in mechanistic terms, not only statistically: what a discrete suffix achieves is **generic depth-graded
   suppression** whose profile is Pearson **0.9965** identical to a random suffix's and deepest at **L24**, not
   at the optimized L18 (§17 cause 3) — the suffix is not missing the coordinate, it is hitting a generic
   direction that contains it.
6. **Every behavioural negative is now an honest bound** (~±0.2 ASR at n=37); the objective-space direction-term
   null is powered (≤23 % of the compute effect on a p=1.1e-07-sensitive endpoint) and must be reported separately
   from the behavioural claim.

**NOT established:** the fine-grained circuit in any non-Llama family; a usable attack objective from the mechanism
(the token-space negative is now definitive and mechanistically explained, not merely observed); a behaviorally
sufficient concept intervention; any working defense; and behavioural effects at the ±0.2-ASR resolution the n=37
corpus forbids. **[c2] Add four more:** the concept half of the dissociation **on Phi-4** (never run); the claim
that the causal locus is **general across concepts** (the multiconcept artifact's own verdict is PARTIAL — 1 of
5 pairs had concept-half headroom); the **budget-matched** version of the activation > continuous > discrete
ladder (D3 never run); and a **confirmatory** continuous dose (Gate D's optimum was read on test).

**One-line takeaway.** *Doublespeak is an imperfect in-context refusal-suppression technique; the elaborate
token→concept remap is a causally-decoupled, behaviorally epiphenomenal bystander. The refusal direction is a
genuine causal handle — you can intervene on it, and steer it continuously — but it does not become a discrete
token attack, and it did not become a defense. Defend the refusal axis, not the concept subspace; and treat every
n=37 behavioural number as a ±0.2-ASR bound.*

---

## 25. Artifact & figure index

**Consolidated summaries (chronological):** `SPRINT_2026-08-02_TO_08-05_FULL_SUMMARY.md` →
`SPRINT_SINCE_2026-08-02_COMPREHENSIVE.md` (→08-06) → `SPRINT_SUMMARY_2026-08-02_TO_08-09.md` →
`CONTINUATION_MASTER_PLAN_V2.md` + `MASTER_STATUS_V2.md` (28 §) → `docs/ASYMMETRY_FINAL_SYNTHESIS.md` →
`docs/SECTION20_RESULTS.md` → **this file** (unifies all of the above).

**Claim tables / audits:** `reports/CLAIM_AUDIT_TABLE.md` (machine-regenerated),
`reports/CLAIMS_AUDIT_2026-08-08.md` + `reports/CLAIMS_AUDIT_2026-08-08_wave2.md` **[c2 — both live under
`reports/`]**, `docs/UPDATED_PAPER_CLAIM_TABLE.md`, `docs/PAPER_OUTLINE_V2.md`, and this log's own re-audit
`RESEARCH_LOG_AUDIT_2026-08-14.md`.

**Part-A/B (circuit + behavior):** `reports/PHASE{2_DIRECTIONS,3_RESIDUAL,4_DEMO_RETRIEVAL,4B_PATTERN,5_HEADS,
6_MLP,7_PATH,8_READOUT,9_DOSE}.md`, `reports/PHASE_BEHAV_{CARRY,WRITE,REFUSAL}.md`, `REP_PREDICTS_BEHAVIOR.md`,
`FINAL_CAUSAL_CIRCUIT_REPORT.md`, `REFUSAL_CIRCUIT_SYNTHESIS.md`.
**Continuation-V2:** `reports/P{1,4,5,6,7,8,9,10,11,13,22,24,25,26,27,28,29}*.md`, `GATE7_EXECUTION_PLAN.md`,
`P_GATE7_FIRSTCUT.md`, `P_DEFENSE_UTILITY.md`, `P27_CROSSMODEL.md`.
**Next-Sprint:** `docs/{ATTACK_OBJECTIVE_FULL_MATRIX,THIRD_FAMILY_REPLICATION,QUANTIZATION_EXTENSION,
NEXT_SPRINT_PLAN_2026_08_09,NEXT_SPRINT_EXECUTION_LOG}.md`; `reports/GATE7_V3_MATRIX_STATS.json`,
`GATE7_V3_MECH_VALIDITY_seed42.json`.
**Asymmetry:** `docs/{ASYMMETRY_SPRINT_PLAN_2026_08_11,ASYMMETRY_SPRINT_EXECUTION_LOG,ASYMMETRY_GAP_MATRIX,
TOKEN_REACHABILITY_ANALYSIS,CONTINUOUS_VS_DISCRETE,ADVANCED_OPTIMIZER_RESULTS,MULTICONCEPT_CAUSAL_GENERALIZATION,
TWO_SIGNAL_DEFENSE,PERPROMPT_VS_UNIVERSAL}.md`; `reports/ASYM_P2_DOSEMATCHED.json`, `ASYM_P2_SEED4{3,4}.json`,
`ASYM_P4_MULTICONCEPT.json`; `outputs/asym_p1_reach_*`, `outputs/defense_2signal_…751316`.
**Section 20:** `docs/SECTION20_RESULTS.md`; `outputs/asym_p20{1,3,4,7,8}_*.json`.

**Key data:** `data/splits/clearharm_doublespeak_v1.json` (137), `data/bench/bench_clearharm_v2.json` (116),
`data/behavioral_v3/` (324), **`../data/clearharm/clearharm_179.csv` (179 — the corpus ceiling, at the REPO
ROOT not under `doublespeak_causality/`)**, `outputs/stage_gcg_full/refusal_direction_llama_{L18,SELECTED}.json`
(the L18 axis and its validation). ⚠ **[c2] `configs/manifests/phase9b_gcg_v3.json` does not exist** — the only
committed GCG manifest is `configs/manifests/phase9_gcg_mac_matrix.json`.
**Previously unindexed, added [c2]:** `reports/P6_JACOBIAN_READOUT.md` + `outputs/p6_predicts_behavior_clearharm.json`
(§12); `outputs/asym_p204_equivalence_pass2.json` (§20.4 pass 2);
`outputs/asym_p207_objective_curve_seed42_FINAL37.json` (§20.7 full-n 200→600 null);
`outputs/asym_p203_judge_replicates.json`; `outputs/p8_alpha020_clearharm.json`;
`outputs/asym_p2_soft_refusal_free_b1.0_seed42_…750364/projections.json` (the inverted-U endpoint);
`docs/OWED_SUBMISSIONS.md`.
**Figures:** `figures/{circuit_summary,behavioral_dissociation,refusal_depth_mechanism,causal_decoupling,
refusal_trajectory,rep_predicts_behavior,fig5_dose_response,fig6_attack_objective,fig7_defense_tradeoff,
fig_crossmodel_behavioral}.png`; `figures/asymmetry/{FIG_A_control_hierarchy,FIG_B_reachability_{train,test},
FIG_B2_eps_scan_{train,test},FIG_C_coherence_train,FIG_D_multiconcept,FIG_E_defense_pareto}.png`.

**Verification provenance of this log:** Aug 2–9 numbers inherit the 14-auditor + 7-agent + two 12-agent
adversarial passes and the machine claim table. Aug 9–14 numbers were re-verified for this document by a 4-agent
workflow (`wf_92ba16b8`) that re-opened the committed JSON; results and the flagged verification gaps are in §22.
**Revision 2 (2026-08-14):** a 14-agent completeness + soundness workflow (`wf_9c6abc32`, 690 tool calls) then
re-audited the document itself — six agents asking *what important work is missing* against the plan and status
docs, seven re-opening the JSON behind every headline number, and an adjudicator independently re-checking each
high/medium finding and discarding what it could not confirm. Output: `RESEARCH_LOG_AUDIT_2026-08-14.md`
(17 defects, 15 omissions, 5 staleness items). All are resolved in this revision and marked **[c2]**. **What
that pass did not change: no core conclusion, in either direction.** Every correction was a wrong number
transcribed into this summary, a verdict stated more strongly than its own artifact, a caveat dropped in
compression, or a result that was simply never written down.

**Standing cutoff.** This revision reflects the repo as of commit `1e364973` / `c04d556b` plus the live
`squeue` state on 2026-08-14. §20.7 seeds 43–44 and the §23 owed list **will** move; re-read §20.7 and §23
against `docs/OWED_SUBMISSIONS.md` before quoting either.

