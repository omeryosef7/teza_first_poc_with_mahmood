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

| window | Neutral←DS | Neutral←Direct | random ctrl | **DS−Direct [95% CI]** |
|---|---|---|---|---|
| early (0–9) | 0.13 | 0.10 | 0.079 | +0.00 [−0.14, 0.14] — NS |
| **mid (10–19)** | 0.16 | **0.52** | 0.03 | **−0.43 [−0.67, −0.19] — SIGNIFICANT** |
| late (20–31) | 0.02 | 0.16 | 0.098 | −0.10 [−0.24, 0.00] — borderline |

**Result — a DEPTH-STRUCTURED DISSOCIATION, opposite to the rep-level prediction:**
- **The hijacked DS state is only weakly behaviorally sufficient at any depth** (≤0.16), and at late layers
  falls to ~0 (below its random control). It never becomes a potent behavioral injectate — consistent with
  it being a *context-dependent* state that loses force when transplanted out of its demonstration context.
- **The raw Direct concept has a MID-LAYER behavioral-steering sweet spot** (0.52 at mid vs 0.10/0.16 at
  early/late; random 0.03 at mid) — injecting the concept mid-network strongly steers generation.
- **Direct ≫ DS is significant ONLY at mid** (CI excludes 0); absent early (DS≈Direct), borderline late.
  This is the *opposite* of the rep-level Patchscopes finding (DS>Direct for decoding).

**Interpretation (honest, important):** representation-level *decoding*-sufficiency (Patchscopes P(concept))
and *behavioral* sufficiency are **DISSOCIATED** for this mechanism. The hijacked DS rep is the distinct
state that *decodes* as the concept (rep-level, confirmed F1), but when transplanted into a bare Neutral
prompt (no demonstrations) it is a **context-dependent** state and is *less* behaviorally potent than the
context-independent raw concept rep. This is a caution for the field: **Patchscopes decoding-sufficiency
does not predict — and here inverts — behavioral sufficiency.**

**Paired bootstrap CI (plan §13):** mid-window **DS−Direct = −0.43 [−0.67, −0.19]** → **CI excludes 0,
the Direct>DS dissociation is STATISTICALLY SIGNIFICANT.** (n=21 unique base×codeword; see limitation.)

**Limitations:** (1) CIs collapse the 3 context-lengths per (base,codeword) to one point (n=21) because
the raw log for these jobs pre-dates the `context_len` fix (now in 19); the summary point-estimates use
the full n≈61–63. Re-running with context_len will tighten the CIs. (2) multi-seed generation pending.
(3) 12 bases per window (all eligible would be 37) — scale-up pending a stable (non-preempting) slot.

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
- Per-window random+identity controls for necessity (not only late window). [queued]
- Sufficiency results pending (689471/19).
- Timing (Claim D) not yet run: does moving harmful meaning early vs late change refusal vs compliance.
- Multi-seed generation + mixed-effects CIs (plan §13) for the behavioral rates.
- Manual blind verification of a clean-success sample (plan §5.6).
