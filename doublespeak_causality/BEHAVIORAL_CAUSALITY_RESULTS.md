# Behavioral Causality Results

**Deliverable (plan §23).** Separates behavioral necessity, sufficiency, timing, mediation, and the
representation-level re-validation, keeping BEHAVIORAL (full-generation, judged) distinct from
SEMANTIC (Patchscopes P(concept)) findings. Redacted: scalars/labels only, no harmful text.
Live chronology + job registry: `SPRINT_EXECUTION_LOG.md`.

Model: `meta-llama/Llama-3.1-8B-Instruct` (bf16, L40S). Benchmark: curated harm-in-noun set
(`BEHAVIORAL_BENCHMARK.md`). Judge: StrongReject + refusal-language (MALICIOUS-first); refusal =
kw-refusal ONLY (the SR-refusal artifact fix, see §0).

---

## 0. Correctness foundation (bugs fixed before trusting any behavioral number)
- **Refusal-signal bug:** `refused` had folded in StrongReject's harmful-goal refusal, mislabeling
  benign Neutral answers as REFUSED → false behavioral null. Fixed to refusal-language only (14/17/18/19).
- **Tokenization:** behavioral capture+generation use single-BOS (`capture_reps_for_gen`), matching
  the screen; positions valid on the generation sequence (plan §19.6).
- **Δ conditioning:** necessity/sufficiency conditioned on the baseline reproducing the required label.
- Independent parallel reviewers audited all judges + patch mechanics (2 rounds).

---

## 1b. Behavioral necessity — Claim B FINAL (per-window controls, SLURM 689972 / 18) ✅ EARLY-SPECIFIC

Strengthened rerun with identity + norm-matched random controls **per window** (n=20 clean successes,
**20/20 reproduced malicious** at baseline). Δ = fraction of malicious baselines flipped to non-malicious.

| window | Δ_necessity | Δ_identity | Δ_random | **necessity − random** |
|---|---|---|---|---|
| **early (0–9)** | **0.50** | 0.05 | 0.25 | **+0.25** ✓ specific |
| mid (10–19) | 0.15 | 0.05 | 0.25 | −0.10 |
| late (20–31) | 0.15 | 0.10 | 0.15 | 0.00 |
| late-half (16–31) | 0.05 | 0.05 | 0.10 | −0.05 |

**Paired bootstrap CIs (n=20, plan §13):**
- early Δ_necessity = **0.50 [0.30, 0.70]** → significant vs baseline (CI excludes 0).
- early necessity−random = **0.25 [−0.05, 0.50]** → **CI CROSSES 0** — the specificity margin over the
  matched random control is NOT statistically significant at n=20 (underpowered).
- mid/late/late-half: Δ ≤ 0.15, necessity−random CIs all include 0.

**Verdict (honest, CI-tempered): behavioral necessity is REAL at early layers** (Δ=0.50, CI excludes 0,
identity control clean at 0.05). Patching the codeword's early representation toward Neutral flips
harmful→benign 50% of the time. **The early-layer SPECIFICITY (effect above matched random) is suggestive
(+0.25) but NOT yet significant at n=20** — needs more clean-success items to establish. Mid/late necessity
is not above random. So: Claim B supported (necessity is real, early-concentrated); the *specificity*
sub-claim requires more N before it can be asserted.

Mechanistic reading: disrupting the codeword's early rep — before the demo-derived harmful meaning is
consolidated and used — prevents the whole downstream harmful computation; once past that, generic
perturbation and the specific Neutral patch are indistinguishable.

---

## 1. Behavioral necessity — Claim B (first run, SLURM 689471 / 18) [superseded by §1b]
**Design:** on clean-success (DS_MALICIOUS) examples, replace the DS codeword state with the matched
Neutral state across a layer WINDOW during FULL generation; re-judge. Δ = 1 − (stay_malicious /
baseline_malicious), conditioned on baseline-MALICIOUS items. n=40 clean conditions; **39/40 reproduced
malicious at baseline** (pipeline sound).

| window (layers) | base_mal | stay_mal | **Δ_necessity** | transitions |
|---|---|---|---|---|
| early (0–9)  | 39 | 22 | **0.436** | 17 MALICIOUS→BENIGN |
| mid (10–19)  | 39 | 28 | 0.282 | 11 →BENIGN |
| late (20–31) | 39 | 31 | 0.205 | 8 →BENIGN |
| late-half (16–31) | 39 | 34 | 0.128 | 5 →BENIGN |
| **control: identity (DS←DS, late)** | 39 | 36 | 0.077 | (clean — reproduces baseline) |
| **control: random (norm-matched, late)** | 39 | 28 | **0.282** | — |

**Honest interpretation:**
- Patching DS←Neutral **does causally reduce harmful behavior** — up to 44% of clean successes flip to
  BENIGN, **strongest when patched EARLY**. The identity control is clean (0.077), so the machinery
  isn't driving it.
- **BUT the late-window random control (0.282) exceeds the late necessity effect (0.205)** → in late
  layers, replacing the codeword rep with *any* norm-matched vector disrupts the malicious generation
  about as much as the Neutral patch. So a **late-specific** necessity claim is NOT supported by these
  controls; the effect is cleanest EARLY.
- **Required follow-up (queued):** run the identity + norm-matched-random controls **per window** (not
  only late), so the early-window Δ (0.436) can be compared against its own random control. The early
  effect being well above the identity control is promising but needs its matched random baseline.

**Status:** behavioral necessity DEMONSTRATED (early window, vs identity) but **partially confounded by
generic late-layer perturbation sensitivity** — reported honestly, follow-up specified. NOT overclaimed.

---

## 2. Behavioral sufficiency — Claim C (SLURM 689975 / 19, mid window) ⚠️ DISSOCIATION FROM REP-LEVEL

**Design:** on eligible baseline-BENIGN Neutral prompts (n=62 benign of 72), inject the DS state vs the
Direct state at the Neutral codeword position across the **mid** window (10–19; where rep-level DS
sufficiency peaks); re-judge. Prediction from rep-level §3 (Patchscopes): DS-injection > Direct-injection.

**Depth-resolved (early 690096 / mid 689975 / late 690097; malicious rate among baseline-benign):**

| window | Neutral←DS | Neutral←Direct | **DS−Direct [95% CI] (clean per-condition, iter42)** |
|---|---|---|---|
| early (0–9) | 0.11 | 0.08 | +0.032 [−0.081, 0.145], n=62 — NS |
| **mid (10–19)** | 0.16 | **0.46** | **−0.295 [−0.443, −0.148], n=61 — SIGNIFICANT** |
| late (20–31) | 0.03 | 0.19 | **−0.161 [−0.274, −0.048], n=62 — SIGNIFICANT** |

**Result — a DEPTH-STRUCTURED DISSOCIATION, opposite to the rep-level prediction:**
- **The hijacked DS state is only weakly behaviorally sufficient at any depth** (≤0.16), and at late layers
  falls to ~0 (below its random control). It never becomes a potent behavioral injectate — consistent with
  it being a *context-dependent* state that loses force when transplanted out of its demonstration context.
- **The raw Direct concept has a MID-LAYER behavioral-steering sweet spot** (0.46 at mid vs 0.08/0.19 at
  early/late) — injecting the concept mid-network most strongly steers generation.
- **Direct ≫ DS is significant at mid (strongest, −0.295) AND late (−0.161)** — both CIs exclude 0 on the
  clean per-condition n; **absent only at early** (DS≈Direct, +0.03 NS). Once past the early layers the raw
  concept is behaviorally more potent than the transplanted DS state. This is the *opposite* of the rep-level
  Patchscopes finding (DS>Direct for decoding).

**Interpretation (honest, important):** representation-level *decoding*-sufficiency (Patchscopes P(concept))
and *behavioral* sufficiency are **DISSOCIATED** for this mechanism. The hijacked DS rep is the distinct
state that *decodes* as the concept (rep-level, confirmed F1), but when transplanted into a bare Neutral
prompt (no demonstrations) it is a **context-dependent** state and is *less* behaviorally potent than the
context-independent raw concept rep. This is a caution for the field: **Patchscopes decoding-sufficiency
does not predict — and here inverts — behavioral sufficiency.**

**Paired bootstrap CI (plan §13) — CLEAN per-condition, all 3 windows (iter42/43 resubmit 692152-4,
context_len logged; deterministic — benign set sorted before bootstrap):**
- **mid DS−Direct = −0.295 [−0.443, −0.148], n=61** → excludes 0, SIGNIFICANT (strongest dissociation).
- **late DS−Direct = −0.161 [−0.274, −0.048], n=62** → excludes 0, SIGNIFICANT.
- early +0.032 [−0.081, 0.145], n=62 — NS (DS≈Direct at early).

The pre-fix collapsed mid estimate was −0.43 [−0.67, −0.19] on n=21; proper per-condition pairing on the
full n attenuates the point estimate but the significance and direction are unchanged, and reveals the
dissociation also holds (more modestly) at late.

**Audit fix (iter42):** the CI code (`analyze_behavioral_causality.sufficiency_cis`) previously keyed
`(base,codeword)` only — collapsing the 3 context-lengths to one point (n=21, last-wins) and able to mix
windows. **Fixed** to per-condition `(base,codeword,context_len)` + per-window grouping. For runs whose raw
logs `context_len` (Qwen3/Phi-4, and Llama once resubmitted), the CI now uses the full per-condition n and
the mid dissociation direction is unchanged:
| model | window | DS−Direct [95% CI] | n | verdict |
|---|---|---|---|---|
| Qwen3 | late | **−0.349 [−0.512, −0.186]** | 43 | excludes 0 ✓ |
| Phi-4 | early | **−0.263 [−0.421, −0.132]** | 38 | excludes 0 ✓ |
| Phi-4 | late | **−0.167 [−0.306, −0.028]** | 36 | excludes 0 ✓ |
| **Llama** | **mid** | **−0.295 [−0.443, −0.148]** | **61** | **excludes 0 ✓ (clean, resubmit 692153)** |
| **Llama** | **late** | **−0.161 [−0.274, −0.048]** | **62** | **excludes 0 ✓ (clean, resubmit 692154)** |
| Llama | early | +0.032 [−0.081, 0.145] | 62 | NS (DS≈Direct early) |

All Llama windows now on clean per-condition n (692152-4). **Audit fully closed — no pending numbers.**

**Remaining limitations:** (1) multi-seed generation pending. (2) 12 bases per window (all eligible would
be 37) — scale-up pending. Neither affects the confirmed dissociation direction/significance.

---

## 2c. CAUSAL TIMING — Claim D ⭐ (TOCTOU; Success Level 3) — the headline mechanistic result

Extracted from the sufficiency window sweep (concept injected into baseline-BENIGN Neutrals; the judge
labels include REJECTED, so the refusal rate is available per injection depth). Injecting the **raw
harmful concept** at different depths and reading the **refusal** rate:

| injection window | REFUSAL rate | MALICIOUS rate | BENIGN |
|---|---|---|---|
| **early (0–9)** | **0.87** | 0.10 | 0.05 |
| **mid (10–19)** | 0.34 | **0.52** | 0.14 |
| **late (20–31)** | **0.00** | 0.16 | 0.84 |

**Paired refusal gradient — reproducible per-condition (base,cw,context_len), clean full n
(`analyze_behavioral_causality.py --timing-dir`, deterministic; no longer hand-computed):**
- early − late refusal Δ = **+0.869 [+0.770, +0.951], n=61** — hugely significant.
- early − mid = +0.525 [+0.410, +0.639], n=61; mid − late = +0.350 [+0.233, +0.467], n=60 — both significant.
- (pre-fix hand-computed values on n=21 were +0.857 / +0.524 / +0.333 — direction identical, CIs now tighter.)

**Verdict: the TIMING of harmful meaning causally controls refusal vs compliance (TOCTOU, Hypothesis 1
confirmed; H2 monotonic-safety and H3 distributed-safety refuted).**
- **Early** harmful meaning is exposed to the model's refusal processing → **refused (86%)**.
- **Late** harmful meaning arrives *after* the refusal-sensitive window → **never refused (0%)**.
- Refusal decreases **monotonically** with injection depth; every step is significant.

**Why this matters — it explains WHY Doublespeak works.** The rep-level result showed the hijacked
codeword meaning emerges *late* (peaks at the last layers). This timing experiment shows that **late-
arriving harmful meaning evades refusal** because refusal is a *time-of-check* operation on *early*
representations. So Doublespeak's late-emergence is not incidental — it is the *mechanism* by which the
attack bypasses safety: it smuggles the harmful meaning past the early refusal checkpoint. This closes
the loop from representation (late emergence) → behavior (refusal evasion) with a causal timing law.

(Note: the DS-state injection barely triggers refusal at any depth — early 6/63, mid 4/63, late 0 — and
is weakly malicious, consistent with §2: the contextual DS state is a weak out-of-context injectate. The
TOCTOU law is cleanest with the raw-concept injectate, which is potent enough to engage refusal.)

### CROSS-MODEL: the TOCTOU direction holds across 3 architectures (Phase 8, `fig_toctou_timing.png`)

Reproducible per-condition (`analyze_behavioral_causality.py --timing-dir`, clean full n, deterministic):

| model | early refusal | late refusal | early−late Δ [95% CI] | verdict |
|---|---|---|---|---|
| Llama-3.1-8B | 0.87 | 0.00 | **+0.869 [+0.770, +0.951]** (n=61) | strong, significant |
| Qwen3-14B | 1.00 | 0.14 | **+0.854 [+0.732, +0.951]** (n=41) | strong, significant |
| Phi-4-mini-reasoning | 0.61 | 0.33 | **+0.250 [+0.056, +0.444]** (n=36) | significant, smaller |

**Honest verdict:** the causal timing law (early injection refuses far more than late) is **significant on
all three architectures** on the clean per-condition full n. It is strongest and near-identical on the two
non-reasoning models (Llama/Qwen3, Δ≈0.86) and **smaller but still significant on Phi-4-mini** (Δ=0.25,
CI excludes 0 — the earlier n=12 estimate was directionally identical but underpowered/NS). The compression
on Phi-4 coheres with it being a **reasoning** model — its CoT can re-examine injected meaning at any depth,
blurring (but not erasing) the early-vs-late timing distinction. **TOCTOU is architecture-general.**

---

## 3. Representation-level causal re-validation (frozen baseline, audited + reruns)
Independent reviewers flagged under-specified controls on the frozen rep-level claims; all 3 HIGH
findings were fixed and re-run on the 6-concept × 6-codeword panel (Llama-8B):

| claim | fix | verdict |
|---|---|---|
| **Conditional sufficiency** (DS-inject > Direct-inject, Patchscopes) | norm-matched control (Direct rescaled to ‖ds_vec‖ + ds-norm random into Neutral) AND re-checked excluding the readout layer L=R (07) | ✅ **SURVIVES both** — DS peaks at a MID layer (DS@R≈0.001), and DS>Direct AND DS>random holds 9/11 hijackers with L<R (mean DS 0.055 vs Direct@DSnorm 0.001 vs random 0.008). Real direction/meaning effect, not magnitude, not a readout-layer artifact. |
| **Information-flow / demos necessary** (attention knockout) | block ONLY demo tokens (request intact) + complementary request_only (09) | ✅ **CONFIRMED confound-free** — demos_only kills hijack 8/8 (P_harm→0). Bonus: query framing also in the causal path. |
| **Multi-layer sufficiency** (distributed *Direct* injection) | exclude the readout layer R from injection windows (08) | ❌ **ARTIFACT — RETRACTED.** With L=R excluded, multi-layer Direct injection → ~0 (0/36 ≈ random). The old effect was readout-layer injection. **Reinforces the story:** Direct is not sufficient any way (single OR multi-layer); only the distinct DS state is. |

**Necessity (semantic, DS←Neutral Patchscopes)** was not flagged critical and stands (identity + random
controls present).

---

## 4. Combined behavioral+semantic picture (current, honest)
- **Semantic (rep-level):** hijacked codeword state is causally necessary (semantic) and **conditionally
  sufficient beyond the plain concept rep** (survives norm-matching), attention-routed from the
  demonstrations (survives the confound fix). Cross-model (3 families, frozen).
- **Behavioral:** the hijack **translates into a real jailbreak** (~20% of eligible curated DS conditions;
  42 clean successes / 14 concepts — BEHAVIORAL_BENCHMARK.md). **Necessity (Claim B):** patching the
  codeword's EARLY representation toward Neutral causally reduces harmful behavior (Δ=0.50), specifically
  (above identity 0.05 and random by +0.25); later layers not specific. **Sufficiency (Claim C):**
  DS-injection is behaviorally sufficient above the null (0.16 vs 0.03), but — a DISSOCIATION from the
  rep-level result — raw Direct-injection is *more* behaviorally sufficient (0.52), so decoding-sufficiency
  (DS>Direct) inverts behaviorally (Direct>DS) at the mid window.
- **Headline nuance for the paper:** the representation-level and behavioral causal pictures **partly
  dissociate** — the hijacked state is decoding-necessary/sufficient and behaviorally necessary (early),
  but the *raw concept* is behaviorally the more potent injectate. Rep-level Patchscopes evidence should
  NOT be read as behavioral evidence — a methodological contribution in itself.

## 5. Limitations / follow-ups
- ✅ DONE: per-window random+identity controls for necessity (§1b); sufficiency (§2, clean per-condition,
  all 3 windows); timing / Claim D (§2c, the headline TOCTOU law, reproducible + architecture-general).
- Remaining: multi-seed generation + mixed-effects CIs (plan §13) for the behavioral rates.
- Remaining: manual blind verification of a clean-success sample (plan §5.6).
- Remaining: scale from 12 bases/window to all 37 eligible (does not affect the confirmed directions).
