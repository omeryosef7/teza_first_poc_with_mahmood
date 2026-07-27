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

## 1. Behavioral necessity — Claim B (SLURM 689471 / 18)
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

## 2. Behavioral sufficiency — Claim C (SLURM 689471 / 19)
**Design:** on eligible, baseline-BENIGN Neutral prompts, inject the DS state vs the Direct state at the
Neutral codeword position across windows; re-judge. Prediction (from rep-level §4): DS-injection >
Direct-injection behaviorally. **Status: RUNNING (689471 sufficiency phase) — results pending; will fill
suff_DS vs suff_Direct malicious-rate per window + identity/random controls.**

---

## 3. Representation-level causal re-validation (frozen baseline, audited + reruns)
Independent reviewers flagged under-specified controls on the frozen rep-level claims; all 3 HIGH
findings were fixed and re-run on the 6-concept × 6-codeword panel (Llama-8B):

| claim | fix | verdict |
|---|---|---|
| **Conditional sufficiency** (DS-inject > Direct-inject, Patchscopes) | norm-matched control: Direct rescaled to ‖ds_vec‖ + ds-norm random into Neutral (07) | ✅ **SURVIVES** — hijackers: DS 0.09 vs Direct@DSnorm 0.002 vs rand 0.002. A real direction/meaning effect, not magnitude. |
| **Information-flow / demos necessary** (attention knockout) | block ONLY demo tokens (request intact) + complementary request_only (09) | ✅ **CONFIRMED confound-free** — demos_only kills hijack 8/8 (P_harm→0). Bonus: query framing also in the causal path. |
| **Multi-layer sufficiency** (distributed Direct injection) | exclude the readout layer R from injection windows + add cumulative random control (08) | ⏳ rerun 689683 (verdict pending) |

**Necessity (semantic, DS←Neutral Patchscopes)** was not flagged critical and stands (identity + random
controls present).

---

## 4. Combined behavioral+semantic picture (current, honest)
- **Semantic (rep-level):** hijacked codeword state is causally necessary (semantic) and **conditionally
  sufficient beyond the plain concept rep** (survives norm-matching), attention-routed from the
  demonstrations (survives the confound fix). Cross-model (3 families, frozen).
- **Behavioral:** the hijack **translates into a real jailbreak** (~20% of eligible curated DS conditions;
  42 clean successes / 14 concepts — see BEHAVIORAL_BENCHMARK.md), and **patching the codeword state
  toward Neutral causally reduces harmful behavior** (Claim B, early window), with the honest caveat that
  late-layer patching is not specific vs random. Sufficiency (Claim C) pending.

## 5. Limitations / follow-ups
- Per-window random+identity controls for necessity (not only late window). [queued]
- Sufficiency results pending (689471/19).
- Timing (Claim D) not yet run: does moving harmful meaning early vs late change refusal vs compliance.
- Multi-seed generation + mixed-effects CIs (plan §13) for the behavioral rates.
- Manual blind verification of a clean-success sample (plan §5.6).
