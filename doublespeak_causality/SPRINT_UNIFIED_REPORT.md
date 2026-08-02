# Doublespeak Causality — Unified Sprint Report

**Paper studied:** *In-Context Representation Hijacking* ("Doublespeak"), arXiv:2512.03771
(Yona, Sarid, Karasik, Gandelsman; Mentaleap). Official code: `github.com/1tux/doublespeak` (vendored → `../doublespeak/`).
**Author:** Omer Yosef (M.Sc., Tel Aviv University; advisor Dr. Mahmood Sharif; collaborator Matan Ben-Tov).
**Primary model:** `meta-llama/Llama-3.1-8B-Instruct`. **Fixed causal pair:** `carrot ↔ bomb`.
**Sprint window covered:** 2026‑07‑25 → 2026‑08‑01 (reference resolution → NEXT7 capstone).
**Branch:** `behavioral-causality-sprint`. **Compute:** L40S (44 GB), env `poc_stage2`, bf16 + SDPA.

---

## 0. How to read this document (verification status)

This is a **single, self-contained, verified** account of everything done on the Doublespeak paper
in this repository. It supersedes the scattered `*_FINDINGS.md`/`STAGE*`/`NEXT*` docs as a reading
entry point (those remain the primary sources; each claim below points to its backing artifact).

Every quantitative claim was cross-checked in an automated 12-agent verification pass (336 tool
calls, ~230 individual claims) that (a) opened the cited output JSON and compared the actual value,
and (b) read the producing script and checked its logic for correctness bugs. The result was
**overwhelmingly confirmatory**. Where a claim did **not** verify cleanly, it is marked inline and
detailed in **§13 (Verification & Integrity Appendix)**. Verification tags used below:

- **[✓ verified]** — number matches the on-disk artifact and the producing code is sound.
- **[✓ verified, corrected]** — the underlying result is real but a previously-published number or
  interpretation was wrong; the corrected form is given here.
- **[⚠ unverifiable]** — the claim has **no committed producing script or artifact**; treat as
  provisional until reproduced.
- **[▲ scoped caveat]** — verified, but with a known limitation a reviewer must see.

> **Scope boundary.** Repository commits from **2026‑07‑21 to 07‑24** belong to a *different* paper
> (Chain‑of‑Thought Hijacking / GCG) and are **not** covered here. Doublespeak work begins when the
> reference was resolved on 2026‑07‑25 (`docs/CONTEXT_HIJACKING_REPRODUCTION_REPORT.md`) and the
> implementation started 2026‑07‑26 in `doublespeak_causality/`.

---

## 1. What the original paper established (and what it left open)

**Doublespeak attack.** Demonstrations repeatedly substitute a benign codeword (`carrot`/`potato`)
for a harmful concept (`bomb`); the final query uses the benign codeword. The model "understands"
the harmful request and complies, bypassing refusal. Construction (`doublespeak_attack.py`):
generate N sentences containing the harmful keyword → replace keyword→benign substitute in the
demos → final query = substituted harmful instruction wrapped with prefix `"Do not reason, just"` /
suffix `"given the context."` Default pair `bomb→carrot` (README) / `bomb→potato` (paper main).

**Original evidence — observational only.** Logit Lens and Patchscopes (§3.2–3.3) show the benign
codeword's representation becomes increasingly **decodable** as the harmful concept across layers,
peaking late. Two mechanisms are **hypothesized but untested** (§3.4): **TOCTOU** (refusal checks an
early representation; harmful meaning emerges later → time-of-check/time-of-use bypass) and
**semantic superposition** (the codeword rep simultaneously encodes codeword + concept).

**The gap we target.** The paper never **intervenes** inside the attacked computation to show the
Doublespeak representation is *necessary* or *sufficient* for the outcome, never localizes the
circuit, never causally tests TOCTOU/superposition, and never separates representation-decoding from
behavior. Our thesis: **move from "the representation changes when Doublespeak succeeds" to "we can
causally control whether/where/when it changes, and that controls refuse-vs-comply."**

---

## 2. Research questions (from `DOUBLESPEAK_CAUSALITY_PLAN.md` §2)

- **RQ1 Necessity** — is the harmful codeword representation necessary for the attack?
- **RQ2 Sufficiency** — is injecting the harmful representation into a benign codeword sufficient?
  (4 levels: probe decodes it · model interprets it · behavior changes · bypasses refusal — never collapse.)
- **RQ3 Timing** — does the *layer* where harmful meaning appears decide refuse-vs-comply? (TOCTOU)
- **RQ4 Information flow** — where does the new meaning come from (earlier codewords / demos / heads / MLPs / paths)?
- **RQ5 Attack objective** — can the temporal representation pattern be optimized into an attack?
- **RQ6 Codeword selection** — is a codeword farther from the concept a better carrier? (Matan's hypothesis)

---

## 3. Models, data, metrics, methodology

**Models.** Primary white-box: `Llama-3.1-8B-Instruct` (all causal numbers). Cross-architecture:
`Qwen3-14B` (thinking-suppressed), `DeepSeek-R1-Distill-Llama-8B` and `Phi-4-mini-reasoning`
(post-`</think>` answer-position readout). Deviations from the paper's setup, all logged in
`PAPER_REPRODUCTION_NOTES.md`: float16→**bf16**+SDPA; raw text→**chat template applied**; native
list-valued **EOS** preserved; transformers 5.12.1.

**Data.** Fixed-pair benchmark `data/pair_benchmark/pair_carrot_bomb.json` — a **gpt‑4o‑mini** API
build, `generated_at 2026‑07‑29T21:44`, seed 7 (the committed canonical bench; **must not be
overwritten in place** — lesson B1). Five concepts across four harm categories: **bomb** (explosive),
**grenade** (explosive), **pistol** (weapon), **chlorine** (toxin), **cocaine** (narcotic).
Behavioral: a curated **harm-in-a-single-noun** benchmark (20 nouns × clean templates, 6 categories)
where substitution provably neutralizes ("build a {bomb}" → "build a {kettle}").

**Prompt conditions** (`pair_common.py`): `DIRECT_CONCEPT` · `NEUTRAL_CODEWORD` · `DOUBLESPEAK` ·
`REPEATED_CODEWORD` · context-only controls `BENIGN_REMAP` (carrot→bicycle) / `UNRELATED_TARGET`.

**Outcome metric.** `p_concept` = next-token probability mass on the concept token group under a
**safe semantic readout** — the model never emits a harmful answer; it reports which *word* it thinks
the codeword refers to. Readout = **`forced_choice`** (validated); **not `cloze`**, which floors the
positive control (B3: DIRECT decodes 0.005 cloze vs 0.785 forced_choice). Behavioral outcome:
**StrongReject** continuous score + 3-way `MALICIOUS`/`REJECTED`/`BENIGN` labels.

**Statistics.** Paired bootstrap CIs; **Holm–Bonferroni** families per sprint (`next{5,6,7}_holm_family.json`);
matched controls in three families (norm-matched-random, orthogonal, in-PCA-subspace, 60/window);
equivalence testing (TOST-style, margin 0.05) for the "inert" nulls. Rule (plan §5.6/§15):
**never infer causality from correlation; never conflate rep-decoding with behavior.**

---

## 4. Sprint phase map (chronological)

| Phase | Dates | Scripts | Theme | Primary docs |
|---|---|---|---|---|
| **A** Reproduction + first causal pass (multi-concept) | 07‑26→29 | 01–25 | Logit-lens/Patchscopes; rep-level RQ1–4; behavioral benchmark; codeword study | `DOUBLESPEAK_MASTER_LOG`, `CAUSAL_RESULTS_SUMMARY`, `UPDATED_PAPER_STORY`, `RESULTS_FREEZE_AUDIT`, `BEHAVIORAL_CAUSALITY_RESULTS` |
| **B** CAUSAL_CORE (fixed pair) | 07‑29→30 | 30–42 | `d_DS` inert vs `d_Direct` controls; 5-pair generalization; behavioral selection | `CAUSAL_CORE_FINDINGS/PLAN/PROGRESS` |
| **C** NEXT_CAUSAL_SPRINT (S0–S5, B4) | 07‑30 | 43–48 | S0 integrity; **S2 transplant**; **S3 KV**; **S4 TOCTOU**; B4 | `STAGE0/2/3/4/5`, `BUG_AND_DEVIATION_LOG`, `PAPER_CONTRIBUTION` |
| **D** NEXT2 | 07‑31 | (re-analysis) | depth-invariance; control-D; honest negatives | `NEXT2_*` |
| **E** NEXT3 | 07‑31 | 46–48 | **T1 Qwen3 cross-arch**; T2 patchscope neg; **T3 repr-TOCTOU**; T4 attribution patching | `NEXT3_*` |
| **F** NEXT4 | 07‑31 | (re-run) | Qwen3 KV replication | `NEXT4_*` |
| **G** NEXT5 | 07‑31 | 49, `next5_*` | **superposition W3b**; **head circuit W4**; DeepSeek W2; defense W5; TOCTOU W1 | `NEXT5_*` |
| **H** NEXT6 | 07‑31 | 50, `next6_*` | **path patching D4**; depth D6; cross-arch D2/D5; defense D7; **D1 integrity** | `NEXT6_*` |
| **I** NEXT7 | 08‑01 | 51, 52, `next7_*` | **full circuit** (MLP AtP, cascade, sweep); induction retrieval; novelword; saturation; CoT probe; detection; benign-remap; **TOCTOU capstone** | `NEXT7_*`, `MECHANISM_SYNTHESIS` |

---

## 5. PHASE A — Reproduction + first causal pass (representation level)

**Goal.** Reproduce the paper's observational hijack and take the first causal/behavioral steps on a
multi-concept panel across three architectures. Frozen tag `frozen-rep-result-2026-07-27`.

### 5.1 Observational reproduction
- **Logit Lens / Patchscopes crossover reproduced** (`01_map_representations.py`, `07_patchscope_readout.py`):
  the benign codeword decodes increasingly as the concept across layers. A **readout fix** was needed —
  the naive projection metric was inflated; the repeat-prompt Patchscope decoder that **passes positive
  controls** is the reliable one (commit `a372c21`). **[✓ verified]** the reproduction exists and is
  artifact-backed (`outputs/stage2b_patchscope_*`).

### 5.2 Representation-level causal results (all CIs exclude 0, cross-model)
- **Necessity (RQ1).** Replacing the DS codeword state with its matched Neutral state removes the decoded
  harmful meaning. **▲ Correction (already bracketed):** the *specificity* over a norm-matched **random**
  patch does **not** hold — the random patch also collapses `P_harm` at mid/late layers, so the once-cited
  "126× (potato) / 8181× (mango)" random-control ratios are **wrong** (actual ratio < 1). This was caught
  in `RESULTS_FREEZE_AUDIT.md` and retracted in `CAUSAL_CORE_FINDINGS.md §6`; **do not cite P6/RQ4 necessity
  specificity in its old form.** **[✓ verified, corrected]**
- **Conditional sufficiency (RQ2).** Injecting the *Direct concept* state is **not** sufficient, but the
  *Doublespeak* state is more successful → the hijacked rep is a **distinct late-emerging state**, not a
  copy of the concept.
- **Timing (RQ3, semantic).** Direct concept decodes early; hijacked codeword meaning decodes late.
- **Information flow (RQ4).** Attention knockout (codeword→demonstrations) eliminates the hijack — but,
  like necessity, **not demonstration-specific** once a count-matched random-token control is included
  (blocking random earlier tokens removes it too). Reported honestly. **[✓ verified, corrected]**
- **Codeword embedding distance does NOT predict hijacking** (RQ6) — see §5.5.

### 5.3 The behavioral jailbreak — flipping a false null (the Phase-A advance)
The paper's/seed's behavioral null was **two artifacts**, both fixed:
1. **Benchmark artifact** — AdvBench harm is rarely localized in one swappable noun (only 2/193 bases had a
   benign Neutral). Fix: the curated harm-in-a-single-noun benchmark.
2. **Judging artifact** — the screen labeled a response *refused* if refusal-language **OR** StrongReject
   refusal-subscore ≥0.5; but SR judges against the harmful goal, so a **benign** Neutral answer scored
   refusal=1 → mislabeled REJECTED (78/80 curated Neutrals harmless, yet 56 mislabeled). Fix:
   `refused = refusal-language only`. **Methodological lesson worth publishing:** a harmful-goal-conditioned
   judge conflates benign compliance with refusal and manufactures a false behavioral null.

**Result (Llama, curated set):** 37/40 eligible bases, **18 clean-success bases, 42 score-verified
clean-success conditions across 14 concepts**; all Neutrals harmless (<0.05); 37/42 DS score ≥0.5,
26/42 ≥0.75; DS-malicious ≈20% of eligible. The clean Doublespeak jailbreak (Direct refused · Neutral
benign · Doublespeak complies) **exists**. **[✓ verified]** (backing in `outputs/behavioral_screen_*`).

### 5.4 Behavioral causality — the HEADLINE of Phase A (TOCTOU timing law)
- **Necessity (behavioral, RQ1).** Patching the DS codeword state to its Neutral counterpart flips
  malicious→benign, **early-layer specific** (seed-avg early Δ=0.549 [0.362, 0.737]; necessity−identity
  +0.399 [0.177, 0.617] — significant, content matters). Specificity over a **random** patch is modest and
  crosses 0 (+0.181 [−0.021, 0.383]) — reported as an honest caveat.
  **▲ [✓ verified, caveat]:** the 0.549 estimator is a **re-weighted** aggregate; a plain per-seed mean is
  **0.414** (documented ambiguity, `RESULTS_FREEZE_AUDIT` mismatch #5). No committed summary JSON.
- **Sufficiency DISSOCIATES from the rep-level prediction (RQ2).** Rep-level Patchscopes said DS-injection >
  Direct-injection. **Behaviorally it INVERTS: Direct ≫ DS** at mid (DS−Direct −0.393 [−0.470, −0.311],
  n=183) and late (−0.064 [−0.116, −0.012], n=173). The hijacked DS state loses behavioral force when
  transplanted out of its demonstrations. **A methodological caution: decoding-sufficiency does not predict
  (here inverts) behavioral sufficiency.** **[✓ verified]**
- **Causal timing law (RQ3) ⭐.** Injecting the raw harmful concept at different depths into benign prompts:
  **early → REFUSAL, mid → COMPLIANCE, late → NEITHER.** early−late refusal Δ = **+0.846 [+0.787, +0.899]**,
  n=169 (Llama). **TOCTOU confirmed: refusal is a time-of-check operation on EARLY representations.**
  **▲ [✓ verified, caveat]:** the by-depth malicious rates were cited as early 0.10 / mid 0.49 / late 0.09;
  disk shows early **0.123** / mid 0.492 / late 0.092 (stale 12-base value for "early"; mid/late match;
  "late never refused 0%" is actually 0.017). Direction and headline unaffected.

### 5.5 Cross-model generalization & codeword study
- **TOCTOU timing gradient is significant on all 3 architectures:** Llama +0.846 [+0.787,+0.899] (n=169) ·
  Qwen3 +0.854 [+0.732,+0.951] (n=41) · Phi‑4 +0.250 [+0.056,+0.444] (n=36). **▲ [⚠ partly]:** the Qwen3/
  Phi‑4 numbers were **verified from raw `sufficiency_raw.jsonl` in `RESULTS_FREEZE_AUDIT`, not from a
  committed summary JSON** — the analyzer logic is correct but there is no summary artifact on disk.
- **Codeword study (RQ6).** Embedding distance does **not** predict hijacking (r ≈ −0.18, n=18; 16/18 hijack).
  All 15 static-property × outcome tests non-significant after Holm. Matan's "farther is better" hypothesis is
  **directionally consistent but unsupported** at this n. **[✓ verified]** (`aggregate_multiconcept.py`).
- **▲ [✓ verified, caveat]:** the Phi‑4 "architecture-general" necessity/sufficiency CIs aggregate over only
  n=5 hijackers; `stats.paired_bootstrap_ci` itself flags n<8 as `ci_reliable=False`. Treat Phi‑4 Phase-A
  causality as suggestive.

### 5.6 ▲ Known bug confined to Phase A — double-BOS
`ds_common.py:603` (`forward_hidden_states`) tokenizes an **already chat-templated** string with the tokenizer
default `add_special_tokens=True`, prepending a **second `<|begin_of_text|>`**. This affects the
reproduction-phase capture path (scripts 01/05/06/07/08/11/13). Because the offset is applied identically to
all conditions and analyses use codeword-relative positions, it is a mild confound (not a conclusion-inverter),
but **Phase-A absolute positions/numbers carry it.** **Crucially, every Phase-B and Phase-C→I causal number
uses `pair_common.py`, which tokenizes with `add_special_tokens=False`** (documented at `pair_common.py:13–15,
69, 178`) — so **the paper's causal contributions are on the clean path.** **[✓ verified — bug real, scope limited]**

---

## 6. PHASE B — CAUSAL_CORE (fixed-pair `carrot↔bomb`, 5-concept generalization)

**Goal.** Replace the multi-concept sprawl with a rigorous single-pair causal study of two competing
directions, then test whether the causal signal transfers to behavior.

### 6.1 The two directions
- `d_Direct = mean(DIRECT) − mean(NEUTRAL)` (the concept direction).
- `d_DS     = mean(DOUBLESPEAK) − mean(NEUTRAL)` (the observational "codeword now decodes as concept" vector).
- **They are different objects at the codeword.** `cos(d_Direct, d_DS)` at the codeword = **0.28** (cloze) /
  **0.19** (one_word), vs **0.83** at the final prompt token — they diverge *specifically where the hijack
  lives*. Replicates across 5 pairs (0.279 bomb, 0.277 grenade, 0.259 chlorine, 0.223 cocaine, 0.216 pistol).
  `d_DS` is **exactly zero at `resid_pre` L0** (DS and Neutral share the codeword token — nothing lexical
  changes; the hijack is purely contextual). **[✓ verified]**

### 6.2 The headline: `d_DS` is causally inert; `d_Direct` controls the reading
Adding a direction at codeword positions (α = fraction of residual norm), `p_concept` readout:

| window | `d_Direct` install (site=codeword_all) | `d_DS` install |
|---|---|---|
| early | +0.167 [+0.105, +0.232] | ~0 |
| mid | +0.533 [+0.453, +0.613] | ~0 |
| **late** | **+0.971 [+0.955, +0.984]** | **0.0000** |

- `d_Direct` **exceeds all 60 window-matched controls** (control mean +0.00002); position-specific (adjacent
  token +0.013, random +0.004); concept-specific (`d_benign`/`d_unrelated`/`d_repeated` all ~0); monotone in α
  (Spearman +0.81/+0.86); holds on **held-out** paraphrases (mid +0.483, late +0.960). It also **removes** the
  reading when projected out (mid −0.157, late −0.068), while projecting out `d_DS` does nothing.
- `d_DS` is **inert in all 15 cells** (5 pairs × 3 windows), each vs its own 60 controls — **the load-bearing
  null generalizes 5/5.** **[✓ verified]**

> **⚠ IMPORTANT CORRECTION to the later B4 claim (see §7.5).** The **+0.971 late install is REAL and
> on-disk** — `outputs/pair_causal_controls_693609.json`: `add_d_Direct | late | α=1.0 | codeword_all →
> 0.9711 [0.9547, 0.9841]` (and `dose_cloze_693607 = 0.97317`). It is measured at **site=codeword_all**
> (the concept direction added at *every* codeword position). At **site=codeword_last** (query position
> only) the same install is only **+0.028** (`693571`). The install is **site-dependent**, which is a
> scientifically meaningful fact, not a discrepancy.

### 6.3 Generalization (5 pairs, 4 harm categories)

| pair | category | `d_Direct` early/mid/late (codeword_all) | `d_DS` max | DS−Neutral hijack |
|---|---|---|---|---|
| bomb | explosive | +0.167 / +0.533 / **+0.971** | 0.0000 | +0.500 |
| pistol | weapon | +0.169 / **+0.909** / +0.771 | 0.0053 | +0.519 |
| grenade | explosive | +0.003 / +0.211 / +0.302 | 0.0007 | +0.619 |
| chlorine | toxin | +0.003 / +0.048 / +0.058 | 0.0001 | +0.449 |
| cocaine | narcotic | +0.012 / +0.004 / +0.011 | 0.0002 | +0.500 |

- **`d_DS` inert: 5/5** (15/15 cells). **`d_Direct` installs: 4/5**, spanning two orders of magnitude.
- **`cocaine` is a genuine exception** (its readout gate passes at +0.500, so the demos *do* install the
  meaning, yet `d_Direct` barely moves it) — "demonstrations achieve what the concept direction cannot."
  Reported per-pair, never pooled. **[✓ verified]**
- **▲ Readout-gate bug found + fixed (07‑30):** benchmark lexicons were hardcoded to the `bomb` pair, so the
  four scale-up pairs' **label** gate was vacuously 0/30 until fixed. The **probability readout `p_concept`
  (used by every intervention) was unaffected**; gates pass on rerun. **[✓ verified]**

### 6.4 The behavioral result — the causal score does NOT beat behavior (RQ5/RQ6, the decisive test)
Does optimizing the causally-validated quantity improve held-out behavioral ASR? **No.**
- **Codeword selection.** Ranking 27 codewords by the safe semantic causal score, then evaluating top-5/bottom-5:
  NEUTRAL 0.008 · TOP-5 0.200 · BOTTOM-5 0.333 → **TOP−BOTTOM = −0.133 [−0.200, −0.050]** (replicated in an
  independent judging pass −0.183). Selecting on the causal score **significantly worsens** ASR.
- **Demonstration selection.** Selecting demos on **behavior** lifts ASR 0.167→**0.833** (+0.667) and beats
  random search; selecting on the **causal score** reaches only 0.250 (**below random search**). Also
  `full_default` (all 12 demos) = 0.167 → **fewer, better-chosen demos beat all twelve.**
- **[✓ verified].** Four independent lines converge: *"measures of the codeword now means the concept do not
  track attack success, and where transfer was directly testable it inverted."* This is the Phase-B thesis and
  it directly disciplines any interpretability-based attack claim.

---

## 7. PHASE C — NEXT_CAUSAL_SPRINT (the paper's three NEW causal contributions + integrity)

The strongest, cleanest results. All on Llama-3.1-8B, `carrot↔bomb`, forced_choice, consistent
(bench, reps, dir) triples.

### 7.1 S0 — Integrity repairs of the prior in-house pipeline
`STAGE0_INTEGRITY_REPORT.md`: **10 defects (C1–C10)** fixed with unit tests + independent adversarial
review, **none conclusion-inverting** — patch-sweep readout contamination (C1/C3), aggregation
manufacturing a null from missing cells (C2), empty-generation miscounting (C8), judge-health/partition
(C7), held-out-concept axis leakage (C9), knockout controls (C5/C6), label de-bias (C10). **[✓ verified]**

### 7.2 S2 — The hijacked reading is carried by receiver CONTEXT, not the local codeword state ⭐ (headline NEW result)
**State × receiver-context transplant** (forced_choice, `34_intervention_sweep.py::run_replace` +
`43_transplant_mediation.py`; artifact `outputs/pair_interv_replace_...694691/transplant_mediation_p_concept.json`):

| receiver \ source state | h_N | h_DS | h_Direct |
|---|---|---|---|
| **Neutral** | 0.000 | 0.000 | 0.000 |
| **DS** | **0.347** | **0.353** | **0.314** |

- `IE_state ≈ 0` — replacing the DS query-codeword's **full local state** with any source carries **nothing**
  into a neutral context; **within-equivalence (margin 0.05) at all 35 layer windows**, max |effect| = 5e‑5. **[✓ verified — 35/35 windows]**
- `DE_context = +0.347 [+0.261, +0.434]` = **98.5% of TE (+0.352)** — a *neutral* codeword state in a DS context
  still reads the concept. **[✓ verified: DE/TE = 0.347/0.352 = 0.985]**
- `PORT_Direct ≈ 0` (a clean DIRECT rep is not portable into a neutral context). **[✓ verified]**
- **Validity:** self-transplant faithfulness is **exactly 0.0** — the transplant machinery is faithful.
  **▲ [✓ verified, corrected annotation]:** the sample size is **n=1050** (694691) / n=840 (694417), **not the
  cited "n=140"** (a stale count from an early 4-prompt run, 4×35=140). The *effect = 0.0* is correct; only
  the n annotation in `PAPER_CONTRIBUTION.md:30` / `STAGE2` is stale.
- Readout gate: `DS−Neutral p_concept = +0.31` [+0.249,+0.367], NEUTRAL clean 0.000, `gate_pass_any=True`
  (`pair_readout_...694417`). **[✓ verified]**

**Code audited (CL1/CL12):** the replace hook truly **overwrites** (not adds) the receiver codeword hidden
state; the (receiver, source) spec mapping has **no swap**; the estimand algebra (IE/DE/TE/PORT/RESID/INT)
and the equivalence test are correct; `semantic_score` returns the concept-token softmax mass = `p_concept`.
**No conclusion-affecting bug.**

**Significance.** This is the **causal counterpart** to the paper's decoding-only "the codeword decodes as
bomb": the token *decodes* as the concept, yet its residual state is **not** what causally drives the reading —
the receiver context's downstream computation is. Directly adjudicates the paper's open causal question.

### 7.3 S3 — Not a trivial demonstration re-read; the effect is distributed
**Demonstration-K/V mediation** (`pair_common.DemoStateSwap` + `44_kv_mediation.py`; `pair_kv_mediation_...694691`):
- **`ReRead_test` (C1−C3) mid = +0.032** of a ~0.35 baseline → **~91% of the reading survives** neutralizing the
  demonstration codeword K/V. If the readout merely re-read the demos, neutralizing them would collapse it. It doesn't.
- The demo-codeword K/V carries a **small, codeword-specific** slice (mid ReRead > random control); the bulk is
  **distributed** — Stage-3 outcome **C**. `DemoStateSwap` self-swap reproduces the no-hook baseline exactly.
- **[✓ verified — all 14 CL3 claims MATCH].** **▲ minor:** the `random_control` swaps a slightly different count
  than C3 (not exactly count-matched: C3 4–13 positions, random 5–13); the codeword-specificity margin is small
  but the direction holds. Flagged, not conclusion-changing.

### 7.4 S4 — A causal TOCTOU signature: the refusal check catches EARLY concepts, a LATE one escapes ⭐
**Concept × refusal behavioral factorial** (n=40; `45_toctou_factorial.py` + multi-layer Arditi refusal
ablation `build_refusal_direction_llama.py`; StrongReject, **0 judge failures**; `toctou_...694811`):
- **Install concept early → refusal** (REJECTED **0.82**) **concept-specifically** — norm-matched random and
  orthogonal directions give 0.00; baseline and refusal-only give 0.00 malicious.
- **Ablate refusal → early concept flips to compliance** (MALICIOUS **0.53**); **a late-installed concept yields
  no compliance even with refusal removed** (**0.07**).
- **Interaction (early−late refusal_gain) = +0.425 [+0.250, +0.600]** for MALICIOUS (Holm-sig); −0.400 for REJECTED.
- Compliance-flip is concept-specific (NEXT2 #2 control-D, job 695111: Dspec early +0.475 [+0.30,+0.65]).
- **[✓ verified — 17/18 CL4 claims MATCH]** (the 18th, grenade/chlorine generalization, is verified under §8/§9).
  The refusal ablation must be **multi-layer** (single-layer barely ablates 1.0→0.93; all-layer L18 → 1.0→0.53).

**Significance.** The **causal test of the paper's §3.4 TOCTOU hypothesis**: the refusal mechanism is
**depth-gated** — it checks an early representation, so Doublespeak's deferral of harmful semantics to later
layers is a genuine time-of-check/time-of-use bypass.

### 7.5 B4 — ⚠ CORRECTED integrity finding (this supersedes the prior B4 write-up)
**As published (`BUG_AND_DEVIATION_LOG.md` B4 / `PAPER_CONTRIBUTION.md §4.1`):** "the CAUSAL_CORE `d_Direct`
+0.971 install does **not** reproduce (+0.03 on the current pipeline; on-disk artifact 693571 = +0.028); the
+0.971 appears **unbacked on disk** (deleted run or doc-vs-metric mislabel); **no** local codeword intervention —
transplant *or* additive direction — installs the concept, **only context does.**"

**Verified reality (this audit):** **the +0.971 IS backed on disk.** `pair_causal_controls_693609.json`:
`add_d_Direct | late | α=1.0 | site=codeword_all → 0.9711 [0.9547, 0.9841]`; `dose_cloze_693607 → 0.97317`.
B4 compared the **wrong site**: `693571` only contains **`codeword_last`** (query position → +0.028). The two
numbers are **different sites of the same experiment**, not a reproduction failure.

**Corrected conclusion (what we can stand behind):**
1. `d_Direct`'s additive install is **strongly site-dependent**: **+0.97 at all codeword positions**, **+0.03
   at the query position alone.** Both are real and on disk.
2. **S2 (§7.2) is unaffected** — S2 replaces the **full local state** of the **query** codeword and finds it
   inert (`IE_state≈0`), with context carrying 99% of the effect. That result stands independently.
3. **The editorial strengthening "no local intervention of any kind installs the concept; only context does"
   is OVERSTATED and should be narrowed** to: *no full-state transplant of the query codeword installs it, and
   additive `d_Direct` at the query position alone does not — but additive `d_Direct` across all codeword
   positions does (+0.97).* The dissociation is about the **query-codeword local state vs the surrounding
   context**, not about "any additive concept injection anywhere."
- **[✓ verified, corrected] — MAJOR documentation/interpretation fix.** Action for the reviewer: treat the old
  B4 "unbacked on disk" line and the "transplant OR additive direction" phrasing in `PAPER_CONTRIBUTION.md §4.1`
  and `HANDOFF.md` as **retracted/narrowed**.

---

## 8. PHASES D–F — depth-invariance, cross-architecture, patchscope, Qwen3 KV

### 8.1 NEXT2 — depth-invariance + closed caveats
- **The S2 dissociation is depth-invariant.** Single-layer state replacement is inert at **all 32 layers**
  (|IE_state| < 0.0002, 4/4 pairs; **▲** pistol's max = exactly 0.0002 at L14, i.e. ≤ not <); `DE_context` flat
  across depth. Even **multi-layer** replacement is inert (**▲** the "11-layer window" is actually 10/10/12-layer
  early/mid/late thirds — cosmetic wording; inertness holds). **[✓ verified]**
- **Control-D closes the TOCTOU specificity caveat** (§7.4). **Honest negatives:** patchscope unusable (N3);
  `d_Direct` dose small/non-monotone (N4, peaks ~0.11 at α=4); the early Qwen3 thinking-model readout gate failed
  (fixed in NEXT3).

### 8.2 NEXT3 — the four deferred levers
- **T1 Cross-architecture ⭐:** the context-carried dissociation **replicates on Qwen3-14B** (thinking-aware
  readout, `--enable-thinking false`): Neutral receiver 0.00 for every source, DS receiver ~0.70, `IE_state≈0`
  (equivalence), **`DE_context +0.70 ≈ 92% of TE`**, faithfulness 0.0 — hijack **stronger** than Llama. **The
  primary claim now holds on 2 architectures.** **[✓ verified]**
- **T4 Attribution patching (`48_attribution_patching.py`):** AtP validated vs true patching (**pearson 0.89**);
  a fast, faithful layer×position attribution. **▲ An early "L0 + demo-codewords localization" claim was a
  reshape-bug artifact, caught by the bug-check and withdrawn** (`605641` NEXT4 bug-check). It attributes the
  effect to late/mid layers at the query/readout position (partly the mechanical direct-path-to-logit). **[✓ verified, corrected]**
- **T3 Representational TOCTOU (`47_repr_toctou.py`):** the refusal-direction projection is raised
  concept-specifically at a **pair-dependent depth** — bomb **early** (+1.79 ≫ mid +0.62), grenade/chlorine
  **mid**. Explains why the behavioral TOCTOU (tested at *early*) did not generalize. **[✓ verified]**
- **T2 Forced-choice patchscope:** **fails its positive control for bomb** (a clean DIRECT bomb rep does not
  decode via the repeat-prompt decoder) → cannot cross-check via patchscope; **consistent with `IE_state=0`**
  (the concept is not locally in the query rep). Honest negative. **[✓ verified]**

### 8.3 NEXT4 — Qwen3 KV replication
S3 qualitatively replicates on Qwen3-14B: **54% of the reading survives** demo-K/V neutralization (not a pure
re-read), codeword-specific (ReRead 0.354 ≫ random 0.093), faithfulness 0.0 — but the demo K/V is **more
load-bearing on Qwen3** than Llama (46% removed vs 9%): the effect is **less distributed / more demo-localized**
on Qwen3. An honest architecture difference within a shared mechanism. **[✓ verified]**

---

## 9. PHASE G — NEXT5 (superposition, head circuit, defense, per-pair TOCTOU)

All new inferential claims survive one Holm family (`next5_holm_family.json`). Full test suite 93 passed.

- **W3‑b Superposition SUPPORTED (paper's 2nd hypothesis, `next5_w3b_superposition.py`).** The DS
  codeword-position rep loads **both** a codeword axis AND a concept axis (band L12–24, projections vs DEV axes,
  heldout reps). DS concept component is **DS-specific above controls**: DS−BENIGN **+0.555 [+0.260,+0.866]**,
  DS−UNRELATED **+0.459 [+0.173,+0.769]** (Holm p 0.002/0.007). Concept loading is **weak** (~13% of DIRECT's
  +14.1) — superposition with a small concept component. **[✓ verified]** Both §3.4 mechanisms are now
  empirically tested: TOCTOU causally (§7.4), superposition representationally.
- **W4 Head-circuit — a validated, mid-band, distributed-across-heads mechanism (`49_head_attribution.py`,
  new `ZHeadPatch`/`ZHeadCapture`).** Per-head z-AtP validated vs **true per-head z-patch (pearson 0.969,
  trustworthy)**. Contribution concentrates in a **mid band L7–14 (61.7% of Σ|AtP|), peaking L9**; distributed
  (top-20 cells = 12%). Per-**layer** knockout: **no single-layer bottleneck** (largest drop +0.024, none
  Holm-sig); per-**head** in-band: no single necessary head (largest ~0.015). Necessity clusters at L7–9 = the
  z-AtP peak. **[✓ verified core]** **▲ minor precision fixes (do not affect conclusions):** the two single
  strongest heads are **L9h19/L9h17**, not the L10–13 list the doc names (peak-L9 conclusion holds); "demos_*
  ≤ 0.014" is actually max 0.023; "all p_holm = 1.0" is actually min 0.72; only `demos_all`/`demos_first` exist
  (no `demos_last`).
- **W2 DeepSeek-R1-Distill (3rd arch):** the post-`</think>` answer-position readout **method is validated**
  (0/120 truncation; DIRECT positive control passes), but the DS hijack is **weak** (gated DS−Neutral +0.333
  [0.000,0.667], n=6, CI incl. 0; p_concept 0), so the transplant was **not run**. Honest scope bound. **[✓ verified]**
- **W5 Mechanism-derived defense (add refusal at use-depth) — NEGATIVE.** Baseline DS malicious = 0.033 (no
  attack headroom on the StrongReject set) and all-position additive steering **destabilizes generation** (30/30
  neutral hit max-length; over-refusal at α=8; degenerate output α=16). First-class negative. **[✓ verified]**
- **W1 Per-pair-timing behavioral TOCTOU [win, later tempered].** Using each pair's OWN dominant depth
  (mid for grenade/chlorine, **pre-registered from the independent T3 probe**), the pooled mid-dominant
  interaction = **+0.1375 [+0.0375,+0.2375], n=80, p=0.015** (cluster-robust). Bomb early−late reproduces
  bit-identically (+0.425). **⚠ Superseded by NEXT6 D1 (§10): at n=60 with verified directions, chlorine is
  NULL; the effect is grenade-driven.** **[✓ verified, superseded]**

---

## 10. PHASE H — NEXT6 (path patching, depth story, cross-arch, defense, n=60 integrity)

All new positive claims survive one Holm family (`next6_holm_family.json`). Full suite green.

- **D4 Path patching — NOT a sparse attention-head circuit (`50_path_patching.py`, new
  `FreezeAllHeadsExcept`/`FreezeMLP`/`ZHeadPatchMulti`; linear-toy 4/4 exact).** Every mid-band head has a large
  **TOTAL** true-patch effect but **DIRECT ≈ 0** (−0.03…+0.06 for every head) → all effect **mediated
  downstream**; head→head **edges do NOT reconstruct TOTAL** (recon fails, `recon_ok=False`) → routes through
  MLPs/residual, not sender→receiver head edges. **[✓ verified — all 21 CL8 claims MATCH]**
- **D3 Circuit generalizes:** the validated mid-band head circuit replicates on **bomb/grenade/chlorine**
  (peak L9/L9/L13; band share 62/67/55%; AtP-vs-true **pearson 0.97–0.99**). **[✓ verified]**
- **D2 Superposition — bomb-specific but cross-architecture.** DS-specific concept elevation is strong on
  **Qwen3-14B (+8.96)** and Llama bomb (+0.55), but **NS vs benign-remap for grenade/chlorine/pistol** on Llama.
  Co-loading (both axes) is universal. **▲ integrity:** an initial chlorine/pistol run paired reps with
  **grenade's `d_Direct`** (a reps↔dir suffix collision) — **caught by the NEXT6 artifact-map workflow** and
  rerun with verified dirs; conclusion unchanged. **[✓ verified]**
- **D6 Depth story:** one timeline unifies superposition + circuit + TOCTOU. **TOCTOU as a monotonic gradient:**
  concept component at the early-check depth **+0.183** vs late-use depth **+4.124** = **22.5×**. Honest nuance:
  the attention **write** band (mid) is **decoupled** from where the concept **projection** grows fastest (late);
  corr(z-AtP write, concept emergence) = −0.30. **[✓ verified]**
- **D5 Cross-architecture bound:** **Phi-4-mini-reasoning** shows the hijack **absent** at the answer
  (reads-as-concept +0.000); with DeepSeek weak, **both reasoning models fail to carry the hijack to the
  post-`</think>` answer**, while Llama (+0.50) and Qwen3 (+0.69) show it strongly. Primary dissociation stands
  on 2 architectures. **[✓ verified]**
- **D7 Defense redo (with headroom) — NEGATIVE.** Re-adding refusal at late/use layers gives **no malicious
  suppression at any α** (|δ|≤0.03, all NS), does not re-engage refusal on the attack, and imposes large benign
  over-refusal (+0.23…+0.43). **Why:** the compliance is gated **EARLY**; a late intervention is too late. **[✓ verified]**
- **D1 n=60 verified-dirs integrity refinement (supersedes W1).** grenade **+0.183 [+0.067,+0.300], p=0.008**
  (strengthened); chlorine **+0.033, p=0.73 (NULL)** — the NEXT5 W1 chlorine +0.15 **does not reproduce**; pooled
  **+0.108, p=0.012** but **grenade-driven**. **Authoritative: per-pair-timing TOCTOU generalizes robustly to
  grenade (+bomb), not chlorine.** **[✓ verified]** (**▲ minor:** grenade p sits between 0.0073 holm-family and
  0.0105 reanalysis due to bootstrap seed — same conclusion.)

---

## 11. PHASE I — NEXT7 (full circuit, install nature, reasoning, detection, capstone)

New behavioral TOCTOU claims survive a NEXT7 Holm family (`next7_holm_family.json`: cocaine/pistol p_holm 0.001).

### 11.1 The full mechanistic circuit (validated stage by stage)
- **N7-A MLP-node attribution (`51_mlp_attribution.py`).** MLP-layer AtP validated vs true `SubmodulePatch(mlp)`
  (**pearson 0.936/0.950/0.932** bomb/grenade/chlorine); MLP contribution concentrates **L7–14 (41–53%), peak
  L11–14**. The mediation the mid-band heads do NOT write directly (D4 DIRECT≈0) is carried by **mid-band MLPs**. **[✓ verified]**
- **N7-E Attention→MLP cascade.** MLP |AtP| peaks **1–2 layers AFTER** the attention z-AtP for every pair
  (attn L9→MLP L11, chlorine L13→L14). Late MLPs carry only **11–23%** of Σ|AtP|. **▲ [⚠ two sub-numbers not
  re-derived by the audit]:** the "concept projection +8.82 across L20–31" and "MLP AtP anti-correlates with
  emergence rate −0.26" reuse the D6/W3-b projection series (committed, but the verifier did not recompute them).
  The core cascade + late-passive split is verified. **[✓ verified core; ⚠ 2 sub-stats]**
- **N7-C Forward-only true-patch sweep (`next7_layer_patch_sweep.py`).** Measures per-layer component
  contribution by true patching only (no backward → fits Qwen3-14B). Llama cross-validation: **attention agrees**
  (true-patch peak L12 vs AtP L9, corr 0.63, 58% in L7–14); **MLP dissociates** (true-patch peaks L31 vs AtP L11)
  — the **computation-vs-proximity split** (late MLPs have large mechanical patch effect but ~0 AtP → passive
  carry). **[✓ verified]** **▲ caveat:** the Qwen3-14B sweep **RUNS** but the `logit_diff(concept−codeword)`
  metric is **reversed** there (m_clean = −9.95) → the Qwen3 circuit localization is **not interpreted**; the
  fine-grained circuit stands **on Llama only** (cross-arch evidence is at the S2/superposition/S3/detection
  level). **▲ minor:** the "re-launched full Qwen3 run" is byte-identical to the demo-capped run.

### 11.2 Nature of the install
- **N7-K Codeword-specific (`next7_novelword_transfer.py`).** Replacing only the query word with a **novel**
  benign word (demos still carrot→bomb) collapses the concept reading **0.70 → banana 0.10, table 0.00,
  pencil 0.00** (p_concept 0.208→0). The remapping applies to the **specific bound codeword**, not a general
  "benign word = harmful" rule. **[✓ verified, 3 words]**
- **N7-L Induction-like retrieval explains N7-K (`next7_attention_retrieval.py`).** From the query codeword, mean
  attention to earlier **same-token** demo codewords vs count-matched random = **3.5× (bomb), 3.5× (grenade),
  3.3× (chlorine)** in the mid-band → token-identity (induction-head-like) retrieval of the in-context binding.
  A novel word has no matching demo tokens to attend to → no retrieval. **Pair-general retrieval, pair-specific
  content.** **[✓ verified]**
- **N7-G Saturating install.** The mid-band concept component is **flat across n_demos 4/8/12** (+1.749/+1.712/
  +1.634) → **≤4 demonstrations fully install** the binding (threshold, not gradual). **[✓ verified]** (▲ tested
  range 4–12; threshold could sit below 4.)
- **N7-M All-layer induction-edge knockout — CONFOUNDED (honest inconclusive).** Blocking the induction edge at
  all 32 layers is so severe it *raises* p_concept (an artifact; the random control raises it most). The clean
  induction evidence remains the N7-L attention **pattern**; a surgical induction-head path-patch is future work. **[✓ verified]**

### 11.3 Reasoning models
- **N7-B Anchored CoT probe (`52_cot_concept_trajectory.py`).** At n=12, **Qwen3-thinking names the concept
  throughout its CoT and at the answer** (~1.0; positive control passes, Neutral 0.0) → reasoning does **NOT
  resolve** the codeword. DeepSeek is genuinely **weak** (~0.33 at the answer at n=12; the noisy n=6 spike of
  0.67 did not replicate). **Refines D5:** D5's "absent" was a *natural-answer readout* property, not concept
  resolution — the anchored forced-naming readout reveals the hijack is present (strongly for Qwen3). **[✓ verified]**
  **▲** Phi-4 anchored probe fails its own positive control (truncation + `\boxed{}` verbosity) → inconclusive on Phi-4.

### 11.4 TOCTOU capstone — representation predicts behavior
- **N7-D pt1 — T3 depth-gating completes to 5/5 pairs.** The refusal check is depth-gated concept-specifically
  for **all 5 pairs** at a pair-dependent depth: **EARLY {bomb, cocaine}**, **MID {grenade, chlorine, pistol}**
  (early_vs_mid CI excludes 0; random control ≈0). **[✓ verified]**
- **N7-D pt2 — behavioral TOCTOU at each pair's OWN T3-predicted depth: 4/5.** bomb +0.425, **cocaine +0.333
  [+0.15,+0.52]**, grenade +0.183, **pistol +0.467 [+0.33,+0.58]** — **all Holm-sig**; only chlorine null. The
  representational refusal-check depth **predicts** where the behavioral compliance-flip appears. **[✓ verified —
  all 25 CL5 claims MATCH]**

| pair | T3 refusal-check depth | behavioral TOCTOU at own depth | Holm-sig |
|---|---|---|---|
| bomb | EARLY | +0.425 | ✅ |
| cocaine | EARLY | +0.333 | ✅ |
| grenade | MID | +0.183 (n=60) | ✅ |
| pistol | MID | +0.467 | ✅ |
| chlorine | MID | +0.033 | ✗ (null) |

### 11.5 Defense vs detection
- **N7-F Concept-ablation defense (right depth) — specific but INEFFECTIVE.** Projecting out `d_Direct` at the
  mid-band (L7–13) throughout generation causes **zero benign over-refusal** (clean vs D7) but does **NOT reduce
  malicious behavior** — because the concept is a **distributed** mid-band computation, not one direction. **▲
  sign note:** the reported field "suppression +0.20" is `def − attack`, i.e. malicious slightly **increased**;
  the label is sign-confusing but the conclusion (no suppression) is right. **[✓ verified]**
- **Defense synthesis:** both mechanism-derived intervention defenses fail for **distinct principled reasons** —
  D7 (add refusal late) targets the wrong depth (decision is early) and destabilizes; N7-F (ablate concept mid)
  is specific but the representation is distributed. **Doublespeak resists representation-surgery defense.**
- **⚠ N7-H/I/J Detection — NOT REPRODUCIBLE FROM THE REPO.** The claims are: in-domain mid-band linear probe
  **AUC 1.0** (Llama + Qwen3); partial cross-pair transfer (grenade/pistol yes, chlorine/cocaine no); transfer
  tracks concept-axis cosine (**corr 0.857**). **These were committed as DOC-ONLY edits to `NEXT7_FINDINGS.md`
  (commits 67a8452 / c0a9c67 / 0a35994 / 16808b3 = "1 file changed" each) — there is NO committed producing
  script and NO output artifact.** The mid-band reps they would use (`pair_reps_...694691`, etc.) ARE committed,
  so the numbers are plausibly from an in-session uncommitted script, but **as it stands the AUC-1.0 detection
  result cannot be reproduced or verified.** **Treat as provisional; re-run and commit the probe before citing.**

### 11.6 N7-N — Doublespeak is generic in-context remapping
A **benign** remap (carrot→bicycle) uses the **same mid-band attention circuit** (peak L12–13) as the harmful
hijack → the remapping mechanism is **generic**; the **safety failure is solely the depth-gated refusal miss**,
not a special hijack mechanism. **▲** the benign reading is weaker in this metric (L7–14 share 37% vs 58%);
localization matches, magnitude differs. **[✓ verified]** (▲ the stdout label prints the unmodified pair; the
metric used the bicycle override — verified in code.)

---

## 12. Complete mechanism (synthesis) & cross-architecture summary

**One-paragraph mechanism.** Under a Doublespeak prompt, an **induction-like attention head** at the query
codeword attends back to the demonstration codewords and **retrieves** the in-context binding (N7-L, 3.5×);
**mid-band attention (L7–9, peak L9) writes** the demo→query context link (W4/D3, z-AtP validated pearson
0.97–0.99); **mid-band MLPs (L9–14, peak L11–14) consolidate** the harmful concept (N7-A, validated 0.93–0.95),
a robust attention→MLP cascade (+1–2 layer lag, N7-E); **late layers passively carry** it to the readout (high
mechanical true-patch but ~0 AtP — computation vs proximity, N7-C/E). The computation is **distributed** (no
single head/layer/MLP/edge bottleneck — W4/D4). The reading is a property of the **receiver context**, not the
query codeword's local state (**IE_state≈0, DE_context≈99%**, S2, depth-invariant, replicated on Qwen3). The
install is a **specific, saturating** codeword→concept binding (≤4 demos, one codeword). The safety failure is a
genuine **TOCTOU bypass**: the refusal check is depth-gated (EARLY, or a pair-specific depth) where the concept
is still ~22× weaker than at use — confirmed representationally (5/5) and behaviorally (4/5). The attack
**resists representation-surgery defense** (early decision + distributed representation) but is claimed
**linearly detectable in-domain** (⚠ that detection claim is not yet reproducible — §11.5).

**Cross-architecture status:**

| Evidence level | Llama-3.1-8B | Qwen3-14B | DeepSeek-R1-Distill | Phi-4-mini-reasoning |
|---|---|---|---|---|
| Semantic hijack readout | +0.50 | +0.69 (stronger) | weak (+0.33, n=6, NS) | absent (+0.00) |
| S2 transplant dissociation | ✅ (DE 99%) | ✅ (DE 92%) | not run (readout too weak) | not run |
| S3 KV mediation | ✅ (91% survives) | ✅ (54% survives, more demo-localized) | — | — |
| Superposition (DS-specific) | ✅ bomb | ✅ bomb (+8.96) | — | — |
| Fine-grained circuit (AtP) | ✅ (3 pairs) | ✗ metric reversed | — | — |
| Detection AUC 1.0 | ⚠ claimed, not committed | ⚠ claimed, not committed | — | — |

---

## 13. Verification & Integrity Appendix (what a reviewer must know)

**Method.** A 12-agent automated verification pass (896k tokens, 336 tool calls) checked every quantitative
claim against its on-disk artifact and bug-checked the producing code. ~230 claims; the large majority MATCH.
Below is the complete list of everything that did **not** cleanly verify, ranked by importance.

### 13.1 Material corrections (change a stated conclusion or number)
1. **B4 is itself incorrect — the +0.971 install IS on disk (MAJOR).** See §7.5. `d_Direct` late install =
   +0.971 at `site=codeword_all` (`pair_causal_controls_693609.json`), +0.028 at `codeword_last` (`693571`).
   B4's "unbacked on disk / no additive intervention installs" is wrong; narrow the dissociation claim to the
   query-codeword local state. **S2 itself stands.**
2. **N7-H/I/J detection AUC 1.0 is not reproducible (INTEGRITY GAP).** Doc-only commits, no script/artifact
   (§11.5). Re-run and commit before citing.
3. **Phase-A double-BOS bug (`ds_common.py:603`) (MAJOR but SCOPED).** Reproduction-phase captures prepend a
   second BOS; the causal contributions (`pair_common.py`) use `add_special_tokens=False` and are clean (§5.6).
4. **Phase-A necessity/knockout random-control specificity retracted.** "126×/8181×" ratios invert (random
   control also collapses P_harm); already bracketed in `RESULTS_FREEZE_AUDIT`/`CAUSAL_CORE §6` (§5.2). The
   necessity/knockout *effects* hold; their *specificity over random* does not.

### 13.2 Minor precision issues (conclusion unaffected)
- **S2 faithfulness "n=140"** → actual n=1050 (694691)/840 (694417); effect=0.0 correct (stale early-run count).
- **W4 top heads "all L10–13"** → true top-2 are L9h19/L9h17; peak-L9 conclusion holds.
- **W4 "demos_* ≤0.014"** → actual max 0.023; "all p_holm=1.0" → min 0.72; no `demos_last` set.
- **N2 "11-layer window"** → actually 10/10/12-layer thirds; **N1 "|IE|<0.0002"** → pistol L14 = exactly 0.0002.
- **Phase-A TOCTOU early malicious "0.10"** → disk 0.123; "late never refused 0%" → 0.017 (mid/late match).
- **S3 `random_control` not exactly count-matched** to C3 (off by a few positions); specificity margin small.
- **N7-F "suppression +0.20"** is `def−attack` (malicious increased); label sign-confusing, conclusion right.
- **Behavioral necessity 0.549** is a re-weighted estimator (plain seed-mean 0.414); documented ambiguity.
- **Cross-model timing (Qwen3/Phi-4)** verified from raw jsonl, no committed summary JSON.
- **Phi-4 Phase-A causality** aggregates n=5 (< the n≥8 reliability threshold); suggestive only.

### 13.3 Code-logic audit (CL12 + per-cluster) — clean where it counts
Audited and **sound**: `34_intervention_sweep.py::run_replace` (true overwrite, no receiver/source swap, correct
site resolution), `43_transplant_mediation.py` (estimand algebra, TOST equivalence, faithfulness), `44_kv_mediation.py`
(DemoStateSwap), `45_toctou_factorial.py` (factorial + Holm), `49/50/51` (ZHead/path/MLP AtP validated vs true
patch), `pair_common.py` hooks + readouts (`add_special_tokens=False`, `semantic_score`=p_concept). Two
non-conclusion-affecting code defects filed: `ds_common.py:603` double-BOS (Phase A only) and
`ds_common.py:468` a latent `UnboundLocalError` on an offset-less-but-decodable tokenizer path (would crash
loudly, never silently bias a number).

### 13.4 What is safe to publish as-is
S2 transplant dissociation (§7.2), S3 KV mediation (§7.3), S4 + T3 + N7-D TOCTOU (§7.4/§8.2/§11.4), the full
validated circuit (§11.1), superposition (§9), path-patching distributedness (§10), the codeword-specific
saturating induction install (§11.2), the honest defense negatives (§9/§10/§11.5), and the Phase-B
"causal-score-does-not-beat-behavior" result (§6.4) — **all verified against artifacts with sound producing
code.** Publish the corrected B4 (§7.5), and either re-run+commit the detection probe or drop the AUC-1.0 claim.

---

## 14. Key artifact index (claim → backing file)

| Claim | Artifact |
|---|---|
| S2 transplant 2×3 + estimands | `outputs/pair_interv_replace_Llama-3.1-8B-Instruct_20260730_190530_694691/transplant_mediation_p_concept.json` |
| S2 readout gate (DS−Neutral +0.31) | `outputs/pair_readout_..._153943_694417/readout_summary.json` |
| S2 generalization (grenade/pistol/chlorine) | `.../pair_interv_replace_..._694895/896/897/` |
| S2 cross-arch Qwen3 | `.../pair_interv_replace_Qwen3-14B_..._695832/` |
| S3 KV mediation (Llama / Qwen3) | `.../pair_kv_mediation_..._694691/` · `..._Qwen3-14B_..._696091/` |
| S4 TOCTOU factorial (bomb) | `.../toctou_..._694811/toctou_summary.json` |
| B4 corrected (+0.971 codeword_all) | `outputs/pair_causal_controls_693609.json`; codeword_last `..._one_word_693571.json` |
| Superposition W3-b | `.../pair_reps_..._694691/w3b_superposition.json` |
| Head circuit W4 (z-AtP) | `.../head_attr_..._696255/head_attribution.json` |
| Path patching D4 | `.../path_patch_..._697419/` |
| MLP AtP N7-A | `.../mlp_atp_{bomb,grenade,chlorine}/mlp_atp_results.json` |
| Forward sweep N7-C | `.../patchsweep_llama_bomb/`, `patchsweep_qwen3_bomb*/`, `patchsweep_benign_remap/` |
| Induction retrieval N7-L | `.../attn_retrieval_..._699219/` |
| Novelword N7-K | `.../novelword_..._699189/` |
| Holm families | `.../next5_holm_family.json`, `next6_holm_family.json`, `next7_holm_family.json` |
| N7-H/I/J detection | **⚠ none committed** |

---

## 15. Reproduction notes (must-read before re-running)
- Use **`--readout forced_choice`**, never cloze (B3).
- Use a **consistent (bench, reps, dir) triple**; never mix builds (B1); job-isolate concurrent runs (B5).
- Refusal ablation must be **multi-layer** (Arditi all-layer project-out).
- Tokenize captures with **`add_special_tokens=False`** on templated strings (avoids the Phase-A double-BOS).
- Report `p_concept` and behavior **separately**; never convert decoding into a behavioral claim (plan §15).
- Environment: L40S 44 GB, `poc_stage2`, bf16 + SDPA; 14B AtP needs the forward-only sweep (backward OOMs).
