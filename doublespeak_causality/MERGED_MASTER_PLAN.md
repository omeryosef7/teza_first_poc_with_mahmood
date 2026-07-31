# Doublespeak Causality — Merged Master Plan & Verified Results

**One document, three sprints, every stage with its result and an audit flag.** This merges the
three chronological plans and their logs into a single per-stage record, and — for every
quantitative claim — states whether it *reproduces from the committed output artifact on disk*.

| Sprint | Plan | Stages | Live log | Result docs |
|---|---|---|---|---|
| **1** Representation-level causality | `DOUBLESPEAK_CAUSALITY_PLAN.md` | P0–P10 / RQ1–RQ6 | `PROGRESS.md`, `DOUBLESPEAK_MASTER_LOG.md` | `CAUSAL_RESULTS_SUMMARY.md`, `RESULTS_SYNTHESIS.md` |
| **2** Behavioral causality + cross-model | `NEXT_SPRINT_PLAN.md` | Workstreams A–G / Claims A–F | `SPRINT_EXECUTION_LOG.md` | `SPRINT_REPORT.md`, `BEHAVIORAL_*`, `MECHANISTIC_OBJECTIVE.md`, `GCG_MAC_COMPARISON.md`, `THINKING_VS_NONTHINKING.md`, `PAPER_DRAFT.md`, `SPRINT_HANDOFF.md` |
| **3** Fixed-pair controlled causal study | `CAUSAL_CORE_PLAN.md` | S0–S17 | `CAUSAL_CORE_PROGRESS.md` | `CAUSAL_CORE_FINDINGS.md`, `CAUSAL_OBJECTIVE.md`, `RESULTS_FREEZE_AUDIT.md` |

**Audit legend:** ✓ number reproduces from the backing artifact · ✗ doc-vs-output mismatch (both
values given) · ⚠ unverifiable / no backing artifact on disk.

**How this document was produced.** 18 result docs (591 quantitative claims) were cross-checked
against the JSON/JSONL artifacts under `outputs/`, and all ~40 analysis scripts were read for
defects, by a fan-out of verification agents. Findings were then reconciled against the
committed artifacts. Model throughout is `meta-llama/Llama-3.1-8B-Instruct` unless a stage names
another. Every "reads-as-concept"/`p_concept`/`P(harm)` number is a **safe semantic-probe**
readout, never a harmful generation.

---

# Part I — The scientific arc (read this first)

The three sprints are one argument that **got more honest as it went**:

1. **Sprint 1** established, with interventions and matched controls, a *representation-level*
   mechanism: a benign codeword used for a harmful concept acquires a **late-layer harmful
   representation** that is **necessary** (patching it back to neutral collapses `P(harm)`),
   **conditionally sufficient**, **routed from the demonstrations via attention**, **localized
   in depth**, and **generalizes** across 6 concepts × 6 codewords × 3 model families. But its
   *behavioral* link was a documented **null on the old seeds** (n=2), and one control — the
   "126×/8181× necessity-vs-random" ratio — later proved non-reproducible.

2. **Sprint 2** built a real **behavioral** benchmark (the old null was an AdvBench artifact:
   harm rarely lives in a single swappable noun — 2/193 eligible) and delivered behavioral
   **necessity**, a clean sufficiency **dissociation** (an explicit *Direct* state hijacks a
   neutral prompt; the *contextual Doublespeak* state does not), and a **causal TOCTOU timing
   law** (same content → refusal when injected early, compliance when late) on three
   architectures. Crucially, when the representation signature was turned into an **attack
   objective** (Temporal-GCG), it was a **controlled negative**: it neither optimizes nor raises
   held-out ASR (it multiplies refusal 8×). Representation hijacking is *real* but *separable
   from attack utility*.

3. **Sprint 3** made that separation rigorous on one clean pair (`CARROT ↔ BOMB`). It found the
   sharpest result in the project: the direction that *distinguishes a hijacked prompt from a
   neutral one* (`d_DS`) is **causally inert**, while the *concept direction* (`d_Direct`)
   **reversibly controls** the reading (5/5 pairs). And in the one place transfer to behavior
   could be tested directly, selecting on the causally-validated score **worsened** held-out
   ASR, while **behavioral** selection won decisively.

> **The through-line: "the codeword now *means* the concept" (a representation-decoding claim)
> does not track attack success — and where it was tested for transfer, it inverted.** For a
> paper whose early draft leaned on representation-level evidence, that is the substantive,
> reportable result, and it is why `PAPER_DRAFT.md` was corrected during Sprint 3's freeze audit.

---

# Part II — Consolidated audit (bugs + doc-vs-output integrity)

## II.0 Integrity scorecard

- **591** quantitative claims checked across **18** docs → **~527 reproduce** (✓/rounding),
  **31 flagged** (✗ mismatch or ⚠ missing-artifact).
- **No conclusion-*inverting* documentation error** survived: the one conclusion-*affecting*
  number (the 126×/8181× ratio) was already self-flagged DO-NOT-CITE by the project's own
  freeze audit. The remaining flags are stale counts, provenance drift, mislabeled columns, and
  a cluster of unverifiable headline CIs.
- **30 code findings** (2 high, ~10 medium, ~18 low). None silently inverts a headline; several
  can bias a specific number, and two touch load-bearing results — detailed below.

## II.1 Code defects (task a) — ranked, with the stage each touches

| # | Sev | File:line | Defect | Stage affected | Consequence |
|---|---|---|---|---|---|
| **C1** | 🔴 High | `07_patchscope_readout.py:135` | Patch-layer sweep runs `L in range(R+1)` — **including the readout layer R**. Patching at `L==R` overwrites the readout vector itself, so that point returns the injected vector with zero propagation. `max_nec_drop`/`max_sufds` take the max over all L **including R**. | **S1 · P3** (patchscope sufficiency) | Floors necessity/DS-sufficiency at the *observational* DS−Neutral gap → **false-positive inflation**. Sibling `08` explicitly capped this (`≤ R-1`, its F3 note); `07` was never capped. This is the mechanical reason P3's patchscope magnitudes (0.135; the 126×/8181× ratio) are unreliable. |
| **C2** | 🔴 High | `41_aggregate_pairs.py:80` | Missing per-pair cells are counted as inert: `abs(get(...) or 0) < 0.05` makes `None→0<0.05` always true; the default `34_intervention_sweep.py` modes (`site='codeword_last'`, layer-groups `L0..L31`) produce **zero** matching cells. | **S3 · S16** (`d_DS` inert 5/5) | The aggregator *can manufacture* the load-bearing null from absence of data. **The conclusion still stands** because `pair_generalization.json` holds real, measured per-pair `d_DS` window values (all ≤0.0075) — the 5/5 was verified from those, not from this aggregator. Fix so it cannot affirm inert without a measurement; also `41:59` picks the window cell by `max(abs)`, which can report a large negative and mask a real `+≥0.05` install. |
| C3 | 🟠 Med | `05_run_activation_patching.py:113` | Same readout-layer contamination class as C1: patches at every block incl. the last while reading `hidden_states[-1]`. | S1 · P3 (necessity) | "Best drop" floored at the observational baseline gap. |
| C4 | 🟠 Med | `06_run_timing.py:114` | Docstring promises a semantic `P(harm)`-by-injection-layer readout; `Patchscopes` is instantiated but **never called**; only behavioral refusal is stored. | S1 · P4 | Any citation of a "semantic P(harm) by injection layer" from Stage 3 cites a **metric that was never computed**. |
| C5 | 🟠 Med | `09_attention_knockout.py:125` | `rand_demos_matched` draws positions from the whole sequence incl. tokens *after* the codeword, which `build_mask` silently drops → fewer keys blocked than `demos_only`, but `n` is recorded as equal. | S1 · P6 | Biases the knockout comparison **toward** demo-specificity. (This corroborates Sprint 3 · S8, which overturned P6/RQ4 specificity with a proper count-matched control.) |
| C6 | 🟠 Med | `09:113` / `10:42` | `09` silently falls back to the old confounded demo/request boundary on locate-failure (no warning, unlike `10`); `10`'s block-hook silently no-ops if the attn mask isn't 4-D. | S1 · P6 | A plumbing failure could read as "attention has no causal effect" undetectably. |
| C7 | 🟠 Med | `14_behavioral_eval.py:103,96` | `malicious_rate` counted on a different partition than the authoritative `labels` dict (prefix-refusal-then-comply undercounted); no judge-health gate (present in `17`); `status` always `COMPLETE`. | S2 · benchmark | `malicious_rate` **understates** DS success and disagrees with the same file's `labels`; a flaky judge deflates ASR toward a fake null with no signal. |
| **C8** | 🟠 Med | `18_run_behavioral_necessity.py:197` | No empty-completion guard: an empty generation under an aggressive patch is scored `BENIGN` and **counted as a necessity flip**. Script `19` has the `EMPTY` guard; `18` does not. | S2 · necessity | **Can inflate `delta_necessity` upward** — the same headline (0.549) that is *also* unverifiable on disk (see II.2). Two independent findings converge here. |
| C9 | 🟠 Med | `21_extract_behavioral_features.py:96` | Harmful-direction axis built once from a random 50% spanning **all** concepts; `22` then does GroupKFold-by-concept and calls it out-of-concept. | S2 · Claim E | Covariate leakage — inflates the held-out-concept AUC (0.668) above its true value (bounded, not label leakage). |
| C10 | 🟠 Med | `31_validate_readouts.py:81` | `classify_answer` returns the *first* matched word; a DS answer that emits the codeword before the concept is scored "codeword." | S3 · S2/S16 | Biases `reads_as_concept` **toward the study's own null**. Mitigated by the one-word instruction; **`p_concept` (used by every intervention) is unaffected**, so load-bearing numbers are safe. |
| C11 | 🟠 Med | `plot_multiconcept.py:185` | `--agg` per-concept scalars are silently ignored (looks up un-prefixed keys; aggregator writes `mean_*`), so each metric falls through to a **recomputation with a different definition**. | S1 · P9 figures | A figure captioned as necessity plots a *different statistic* (layer-count fraction) than the headline aggregate (magnitude ratio). Figures only; JSON headline unaffected. |
| — | ⚪ Low ×~18 | core libs, `30–33`, analysis/plot | Docstring drift, unused variables, robustness guards, style. | — | No result impact. `ds_common.py`/`pair_common.py`/`stats.py` core paths are clean. |

## II.2 Documentation-vs-output mismatches (task b) — grouped, with the fix

**(A) Confirmed non-reproducible — already self-flagged DO-NOT-CITE.**
The **necessity-vs-random "126× (potato) / 8181× (mango)"** ratio (`stage2_patching_..._001943`).
Not reproducible under any interpretation and points the opposite way; superseded by the
artefact-backed **necessity − random = +0.181 [−0.021, 0.383] (crosses 0)**. Appears in
`PROGRESS.md`, `CAUSAL_RESULTS_SUMMARY.md`, `RESULTS_SYNTHESIS.md`, `DOUBLESPEAK_MASTER_LOG.md`,
`SPRINT_HANDOFF.md`. → **Fix:** it is still *live* in `RESULTS_SYNTHESIS.md` RQ1 and is still the
`key_metric` for `stage2_canonical_done` in `EXPERIMENT_REGISTRY.csv` — purge both.

**(B) Unverifiable headline CIs (weakest-provenance region).**
The **multi-seed behavioral necessity** figures — `Δ_necessity = 0.549 [0.362, 0.737]`,
`nec − identity = 0.399 [0.177, 0.617]`, `nec − random = 0.181 [−0.021, 0.383]`
(`BEHAVIORAL_CAUSALITY_RESULTS.md` §1b, `PAPER_DRAFT.md` §4.2). **No committed artifact reproduces
0.549/0.399**; the three single-seed marginal deltas are all *lower* (0.378–0.4545); only the
`0.181` point matches one run's `necessity_above_random`. The "23-unit repeated-measures
recompute" is not stored. Direction (excludes 0) is plausible; the values are not on disk — **and
code C8 can bias this exact number upward.** → **Fix:** re-run the recompute, commit the summary
JSON, or mark the number *unverified* and cite the on-disk single-seed/n=20 values instead.

**(C) Stale benchmark counts (`BEHAVIORAL_BENCHMARK.md`, `PAPER_DRAFT.md`).**
`40 bases / 20 nouns` → data file now `84 bases / 42 concepts` (`expanded_iter31`); "240
conditions" is based on the stale 40; "200 screened" → screen ran **193**; PAPER_DRAFT §4.1 "18
bases" for the 42 clean successes → **16 distinct bases** (18 is the looser 46-row span); S5
"MALICIOUS-first reclassify identical" is **not robust** (one artifact 2/1 identical, another
23/9). → **Fix:** refresh counts to the committed artifacts; resolve the reclassify conflict.

**(D) Stale thinking dose-response cells (`THINKING_VS_NONTHINKING.md`).**
All six demo-count dose numbers are stale and internally inconsistent (they don't average to the
doc's own overall rates; the corrected ones do). Actual matched (n=90): non-think **0.20 / 0.267 /
0.267** (→ mean 0.244 ✓), think **0.133 / 0.20 / 0.333** (→ mean 0.222 ✓). → **Fix:** replace the
cells; the steepening/overall conclusion survives.

**(E) Sprint-3 cosmetic (`CAUSAL_CORE_FINDINGS.md`).**
§3 "`d_DS` **max**" column actually prints the **mid-window** value; true max (early) is 2–4×
larger — pistol 0.0053→**0.0075**, grenade 0.0007→**0.0020**, cocaine 0.0002→**0.0008**, chlorine
0.0001→**0.0004** — **all still ≪ 0.05, so "inert 5/5" is unaffected**; relabel or use the true
max. §2.1 cross-fit `d_DS` stability "0.93–0.97" understates the range — true **0.859–0.969** (mean
0.916; 16/32 layers below 0.93); the "high, not noise" claim stands.

**(F) Provenance drift (`RESULTS_FREEZE_AUDIT.md`, `ARTEFACT_MANIFEST.json`, registry).**
Registry "39 rows, all ≤2026-07-27" → **45 rows** (6 causal-core rows appended post-freeze);
"figures/ 11 PNGs" → **9** top-level PNGs (the 4 cited headline figures are all present); the
manifest's hash+size for the ⭐ **`pair_causal_controls_693609.json`** no longer match disk (file
regenerated 07-30 **after** the 07-29 snapshot — the only content-hash divergence among 53 hashed
files; **the current file still carries the +0.971 S6 headline**, verified). → **Fix:** regenerate
`ARTEFACT_MANIFEST.json` at the current commit.

**(G) Minor transcription (immaterial to any conclusion).**
P8 codeword correlation doc `r=−0.18` vs stored **−0.189**; SPRINT_REPORT timing early-MALICIOUS
`0.10` vs **0.123**; GCG lex-tight final `task_loss 16.4` vs **16.1**; identity control `0.008` vs
**0.0098**; Qwen DS peak-layer mean `37.6` vs **37.5**; P3 sufficiency `0.135` reproduces from the
`diag_suff_ds.log`/registry provenance but **not** from the canonical `687378` patchscope JSON —
cite the log, and note C1/C3 make the magnitude itself unreliable.

**(H) Missing artifacts (registry- or log-corroborated, no committed JSON).**
The n=7 panel necessity `98%` and sufficiency `0.037 [0.027, 0.047]`; the qwen3-generality CIs;
the rep-level §3 re-validation numbers (`0.055/0.001/0.008`, `9/11`, demos-only `8/8`, multilayer
`0/36`). Corroborated by the registry/log but the raw JSON is gitignored or was never
materialized. → **Fix:** re-materialize or mark ⚠ on citation.

## II.3 The short fix-list

1. **Purge** the 126×/8181× ratio from `RESULTS_SYNTHESIS.md` RQ1 and the registry `key_metric`.
2. **Cap** `07`/`05` patch sweeps at `L ≤ R-1` (C1/C3) and **re-run** P3 patchscope necessity/
   sufficiency; treat current P3 magnitudes as upper-bounded by the observational gap until then.
3. **Add** the `EMPTY`-completion guard to `18` (C8), then re-run and **commit** the multi-seed
   necessity summary so 0.549/0.399 are backed (or retract the exact values).
4. **Harden** `41_aggregate_pairs.py` (C2): require a measured cell before scoring inert; use
   `max(effect)` for the install test.
5. **Refresh** stale counts (benchmark 84/193/16, thinking dose cells) and **regenerate**
   `ARTEFACT_MANIFEST.json`.
6. Backport the judge-health gate to `14` (C7); recompute `dvec` per-fold in `21`/`22` (C9).

---

# Part III — Per-stage plans and verified results

<!-- The three sections below are the merged plan proper: each stage's intent, its driving
script(s), its output artifact(s), the verified result with CI, the verdict, and the audit flag. -->


## Sprint 1 — Representation-level causality (DOUBLESPEAK_CAUSALITY_PLAN, P0–P10)

**Objective.** This sprint set out to convert the Doublespeak paper's *observational* claim — that a benign codeword (e.g. `carrot`/`potato`/`muffin`) repeatedly used for a harmful concept acquires an increasingly harmful representation across layers — into a *causal* account: to establish, with explicit interventions and matched controls, whether the late-layer harmful representation of the codeword is **necessary** and **sufficient** for the hijack (RQ1/RQ2), **when** in the layer stack it emerges relative to the safety check (RQ3), **where** the meaning is routed from (RQ4), whether it can be turned into a mechanistic optimization objective (RQ5), which codeword properties predict success (RQ6), and whether the mechanism generalizes across concepts/codewords/models and supports a defense. Primary model Llama-3.1-8B-Instruct; secondary Qwen3-14B and Phi-4-mini. Metrics are separated per plan §5.8: Patchscopes/readout P(harmful) as the semantic-probe signal, and StrongReject/three-way labels (MALICIOUS/REJECTED/BENIGN) as behavior.

### Per-stage results

| Stage | What it tested | Driving script(s) / artifact(s) | Verified result (with CI) | Verdict | Audit |
|---|---|---|---|---|---|
| **P0** — Env audit + scaffold + docs (§4, §29) | Environment/SLURM/model audit; `doublespeak_causality/` module; tracking docs | `ENV_AUDIT.md`, PLAN/PROGRESS/MASTER_LOG/`EXPERIMENT_REGISTRY.csv` | All tracking docs present; official repo vendored | control (infra) | ✓ structural |
| **P1a** — Core library (§19) | Model load (bf16+SDPA, native EOS, chat template), multi-token target localization, matched Direct/Neutral/Doublespeak builder, activation capture | `ds_common.py` | Library present; reuses `doublespeak/mech_interp.py` + house hooks | control (infra) | ✓ structural |
| **P1b** — Unit tests (§23) | Synthetic patching + real-tokenizer localization | registry `core_lib_20260726` (`tests_pass`) | **13/13 pass** (6 synthetic LayerPatch + 7 Llama-BPE localization) | gate-passed | ✓ registry 13/13 (6+7 split not separately stored) |
| **P1c** — Smoke test 3–5 prompts (§24) | End-to-end correctness gate on Llama-8B | `outputs/smoke_llama_login.json` (fp16); bf16 canonical `smoke_Llama-3.1-8B-Instruct.json` (job 686635) | 3-token EOS preserved (`n_eos=3`); α=0 add is identity; **replace Δ=6.42** (`6.41992`, fp16); all 5 checks (load/localization/capture/patching/generation) OK | gate-passed | ✓ (bf16 canonical shows Δ=6.3125 for same check; doc correctly cites the fp16 figure) |
| **P2** — Representation mapping (§8) | Patchscopes/logit-lens trajectory of the codeword rep; onset & peak; cos-to-Direct/Neutral | `outputs/stage1_repmap_Llama-3.1-8B-Instruct_20260726_231610/stage1_results.json` (+ `stage1_gpt4omini_login`) | Late crossover P(harm)>P(code) at **L17 / L20 / L21** (potato/mango/carrot); peak-harm layers **L30 / L31 / L31**; peak P(harm) **potato 0.125, carrot 0.0085, mango 0.2051**; cos(DS,Direct) rises **~0.06 → ~0.58** while cos(DS,Neutral) stays high | positive (observational only) | ✓ crossovers, peaks, magnitudes all match |
| **P3** — Activation patching, necessity + conditional sufficiency (§9) | Necessity: DS←Neutral patch collapses P(harm); controls (identity, random). Sufficiency: Neutral←DS vs Neutral←Direct | `outputs/stage2_patching_..._20260727_001943/stage2_results.json`; `stage2b_..._canonical` (job **687378**); `logs/diag_suff_ds.log` + registry `suff_conditional` | **Necessity CONFIRMED**: DS←Neutral drives P(harm) to ~0 from mid-layers; identity control ≪ effect (potato dev 0.0098 vs drop 0.124; mango 0.0396 vs 0.205). **Conditional sufficiency**: Neutral←DS reaches **P=0.135 @L15** vs Neutral←Direct **0.001** (hijack rep is late-structured, direct is early) | positive (necessity); positive-conditional (sufficiency) | ✗ **necessity-vs-random "126x/8181x" is NOT reproducible** from the stage2 artifact and points the opposite way — doc **self-flags DO-NOT-CITE** (RESULTS_FREEZE_AUDIT); superseding artefact-backed control **necessity−random = +0.181 [−0.021, 0.383], crosses 0**. ⚠ the 0.135 figure matches `diag_suff_ds.log`+registry but does **not** appear in the stage2b **687378** JSON (max per-item suff there ≈0.0015, suff_ds ≈0.033) — cite the log/registry provenance, not 687378 |
| **P4** — Timing: early vs late injection (§10.3) | Whether early vs late harmful-direction injection separates refusal from compliance | (semantic side via P2/P6 emergence; behavioral side not run) | Semantic late-emergence CONFIRMED (peak L30–31); a behavioral flip was observed anecdotally but **StrongReject confirmation not run** | partial / not established | ⚠ behavioral half unverified (no StrongReject artifact) |
| **P5** — Malicious/Rejected/Benign behavioral split (§8.4) | Whether the rep signal corresponds to an actual jailbreak on seed prompts | `outputs/behavioral_login/behavioral_summary.json` | **Honest null (n=2 pilot)**: Direct 2/2 REJECTED (SR 0); Doublespeak mean SR **0.375** (virus-DS 0.75, bomb-DS 0); Neutral mean **0.5** (virus-neutral 1.0). Representation-hijack ≠ clean behavioral jailbreak on this seed | negative (behavioral) / partial | ✓ per-concept means reproduce; n=2 pilot only |
| **P6** — Attention knockout + depth (§11) | Where the codeword's new meaning is routed from; position and depth localization | `outputs/stage4_knockout_..._20260727_024621/` (canonical job **687520**), `stage4_knockout_login/`, `stage4_layerko_login/`; gen `ko_gen_*`, `lko_gen_llama8b` | Block codeword→all-demos removes hijack: **P(harm) 0.0983 → 9.3e-7** ("0.10→0"); literal codeword returns 0→0.006; block 12 prev codewords **0.068 ≈** 12 random-earlier **0.069** (distributed, not a single source). Depth: strongest single layer **L18→0.02**, cumulative blocking kills it by **~L14**; consolidation median **L2**. Cross-model gen unanimous: **12/12, 12/12, 6/6** below-20% (Llama/Qwen/Phi) | positive (causal route) | ✓ all knockout/depth numbers match (recomputed) |
| **P7** — Temporal mechanistic objective (§12) | Optimize benign-early / harmful-late representation pattern | — | **DEFERRED, not run** — low value given the P5 behavioral null (would optimize a rep-signal that doesn't cleanly produce a jailbreak on seed) | not run (documented) | ⚠ no artifact (by design) |
| **P8** — Codeword study (§13) | RQ6: does static embedding distance predict hijack strength? | `outputs/codeword_study_virus_..._041811/codeword_study_results.json` (+ `codeword_study_login`) | **n=18** codewords, **16/18 hijack**; **mirror strongest (0.312)**, two near-zero non-hijackers (turtle 0.007, banana 0.018); ~40× strength range. Embedding distance **NOT predictive**: Pearson r(dist,hijack) **−0.189** | positive (16/18 hijack) + negative (distance non-predictive) | ✗ doc cites **r=−0.18**, stored value is **−0.189** (truncation; rounds to −0.19). Sign/magnitude/conclusion unaffected |
| **P9** — Scaling / generalization (§14) | Generalize necessity/sufficiency/timing across 6 concepts × 6 codewords × 3 model families | `outputs/multiconcept_aggregate_{llama8b,qwen3,phi4}.json`; `emergence_Qwen3-14B_..._064244`; `stage2b_..._Qwen3..._064447` | **All three families, all CIs exclude 0.** Llama: 11/36 hijack, timing **+30.3 [29.18, 31.0]**, necessity 0.99, suff-diff **+0.055 [0.039, 0.072]**. Qwen3: 13/36, **+32.0 [30.15, 33.77]**, nec 0.97, suff **+0.070 [0.045, 0.102]**. Phi-4: 11/36, **+25.3 [22.82, 27.27]**, nec 1.00, suff **+0.390 [0.108, 0.676]**. Qwen full-panel timing **33.5 [32.6, 34.0]**, 16/18 hijack | positive (generalized) | ✓ all aggregate CIs match; ⚠ minor: Qwen DS peak-layer mean is **L37.5** (doc says 37.6); Phi-4 bomb hijacks 3/6 slightly exceeds the "bomb rarely 0–2/6" qualitative band |
| **P10** — Mechanism defense (§15) | Late-layer harmful-semantic probe as a detector; benign-ICL preservation | `outputs/defense_login/defense_results.json` | Late-harmful probe **TPR 1.00 (9/9) / FPR 0.00 (0/18)**, threshold 0.02, layers ≥24; benign-learned rate 0.0 | positive (detection) / partial (utility) | ✓ exact; benign-ICL *preservation* only weakly shown (no benign-transfer test) |

### Sprint conclusion

What was actually established, with artifact-backed interventions and matched controls: (1) the late-layer harmful representation of the codeword is **necessary** — patching the Doublespeak activation back to Neutral collapses P(harm) to ~0, with the identity control an order of magnitude below the effect; (2) sufficiency is **conditional** — injecting the *Doublespeak* rep into a neutral codeword recovers the harmful reading (P=0.135@L15) whereas the *Direct* rep does not (0.001), i.e. the hijack rep is late-structured, not an early literal insertion; (3) the meaning is **routed from the demonstrations via attention** and is distributed (blocking all demos → ~0; prev-codeword ≈ random-earlier), **localized in depth** (single-layer L18, cumulative kill by ~L14); (4) the signature **generalizes** across 6 concepts × 6 codewords × 3 model families with every timing/necessity/sufficiency CI excluding zero; (5) a **late-harmful probe defense** cleanly separates hijack from benign on the tested set (TPR 1.00 / FPR 0.00). These are genuine causal-representation results.

What was a **negative or killed claim**: the behavioral link is a documented **null on seed** (P5, n=2) — the representation hijack does **not** translate into a clean StrongReject jailbreak, which is why the timing behavioral confirmation (P4) and the temporal attack objective (P7) were, respectively, left unconfirmed and deferred rather than pursued. Static **embedding distance does not predict** codeword hijack strength (r=−0.189). The **one integrity defect** across all four Sprint-1 docs is the RQ1 "**126×/8181× necessity-vs-random**" ratio: it is not reproducible from the stage2 artifact, points the opposite way, and is superseded by an artefact-backed control (necessity−random = +0.181 [−0.021, 0.383]) that **crosses zero** — the docs already self-flag it DO-NOT-CITE, but the registry still lists it as that run's key metric. Net: the *necessity/sufficiency/routing/generalization* representation story is solid; the *behavioral* causal claim and the necessity-vs-random *control margin* are the weak points, and both are honestly logged as such.
---

## Sprint 2 — Behavioral causality + cross-model (NEXT_SPRINT_PLAN, Workstreams A–G)

**Objective.** This sprint (directive authored 2026-07-27) set out to convert the project's representation-level Doublespeak findings — a cross-model, causally manipulable *semantic* hijacking mechanism that carried a *behavioral null* on the old confounded seeds — into paper-grade behavioral science. Six target claims were pursued: (A) a statistically credible behavioral benchmark occupying the true Doublespeak "sweet spot"; (B/C) behavioral necessity and conditional sufficiency under activation intervention on full generations; (D) a causal timing law for refusal vs. compliance; (E) a mechanistic objective that predicts held-out behavioral success; (F) a temporal-representation GCG/MAC objective that beats standard suffix optimization on held-out ASR; and (G) a within-model thinking-vs-non-thinking comparison. The headline outcome: Claims A–D and the *predictive* half of E were established with paired CIs and controls, while the *utility* claim E→F (Level 5, Temporal-GCG) is a clean, controlled **negative**, and G is a small mixed/null behavioral effect. Below, audit flags are ✓ (number reproduces from artifact), ✗ (doc-vs-output mismatch, both values given), ⚠ (unverifiable / missing artifact).

---

### Workstream A / Claim A — Behavioral benchmark & yield

| Stage | Tested | Script(s) | Artifact | Verified result | Verdict | Flag |
|---|---|---|---|---|---|---|
| S4/S5 AdvBench screen | Does raw AdvBench occupy the sweet spot? | `16_prepare_behavioral_benchmark.py`, screen runner (job 688994) | `outputs/behavioral_screen_llama8b_v1/screen_summary*.json` | N=193 bases, 1158 DS conditions; Direct gate 193/193; Neutral-benign only **2/193**; DS response-level REJECTED/MALICIOUS/BENIGN = 955/193/10; triplet DS_MALICIOUS=1; 0 judge failures; 191/193 (98.96%) ineligible; 14 explosives + 6 weapons categories yield 0 eligible | negative (AdvBench unsuitable) | ✓ core; ✗ two issues below |
| — "200 screened" | benchmark source size | same | `screen_summary.json` n_bases | Doc says **200**, artifact n_bases=**193** | — | ✗ (200 has no backing; 193 ran) |
| — reclassify "identical" | labeling-artifact check | reclassify pass | `screen_summary_reclassified.json` vs `_corrected.json` | reclassified.json = 2 eligible / 1 clean (identical to original), **but same-method `screen_summary_corrected.json` = 23 eligible / 9 clean** | unresolved | ✗ (conflicting artifact; "identical" claim not robust — flag for human) |
| S3.1 curated screen | Curated single-concept set at the sweet spot (Llama) | curated screen (`behavioral_screen_curated_v1`) | `screen_summary_reclassified.json` | **37/40** bases eligible, 18 clean-success bases, DS_MALICIOUS=46, MALICIOUS-among-eligible=52, 0 judge-fail; per-generation DS-malicious rate 0.176/0.203/0.243 by context length (~20% overall) | positive (benchmark exists) | ✓ |
| S3.1 "42 clean successes" | strict triplet count | `per_condition_corrected.json` | recompute | 42 strict three-way successes over 240 DS generations, spanning **14 concepts** and **16 distinct bases** — doc/PAPER_DRAFT §4.1 says "18 bases" | positive | ✗ (16, not 18; 18 = looser 46-row DS_MALICIOUS span) |
| S3.1 curated data file | benchmark scale | `data/curated_concepts.json` | `_meta` | File now holds **84 bases / 42 concepts** (`expanded_iter31`); BEHAVIORAL_BENCHMARK.md still describes 40 bases / 20 nouns / 240 conditions | — | ✗ (doc stale vs artifact) |
| S3.1 expanded screen | 84-base / 336-condition expansion | curated screen (cw4x42) | `behavioral_screen_curated_cw4x42/` | Output dir empty — screen cancelled by preemption | incomplete | ⚠ |
| TrackA DeepSeek-R1 | 4th-architecture benchmark reproduction | curated screen (deepseek_r1) | `behavioral_screen_curated_deepseek_r1/screen_summary_reclassified.json` | 27/40 eligible, 16 clean-success bases, MALICIOUS-on-eligible=37 across 16 bases, DS_MALICIOUS(unrestricted)=66, 0 judge-fail | positive (reproduces) | ✓ |

**Level 1 achieved** on the curated set (Llama 37/40; reproduced on DeepSeek-R1); AdvBench itself is a documented negative (harm rarely lives in a single swappable noun).

---

### Workstream B / Claims B & C — Behavioral necessity & sufficiency

| Stage | Tested | Script(s) | Artifact | Verified result | Verdict | Flag |
|---|---|---|---|---|---|---|
| S3.2 necessity (n=40, n=20) | DS←Neutral patch reduces harmful behavior; identity/random controls | `18_run_behavioral_necessity.py`, `analyze_behavioral_causality.py` | `beh_necessity_*/necessity_summary.json`, `behavioral_causality_cis.json` | First run n=40: 39/40 reproduced malicious; Δ_necessity early/mid/late/late-half = **0.436/0.282/0.205/0.128**; identity control (late) 0.077; random control (late) 0.282. n=20 early: Δ 0.50 [0.30,0.70]; nec−random 0.25 [−0.05,0.50] (crosses 0) | positive (necessity real, early-specific); specificity-over-random modest | ✓ |
| S3.2 multi-seed headline | seed-averaged necessity (3 seeds, "23 units") | seeds jobs 692698/699/700, `_155404` | none located | Doc/PAPER_DRAFT: Δ=**0.549 [0.362,0.737]**; nec−identity **0.399 [0.177,0.617]**; nec−random **0.181 [−0.021,0.383]** | positive direction, but value contested | ⚠ (no committed artifact reproduces 0.549/0.399; single-seed marginal deltas 0.378–0.4545 all *below* 0.549; only nec−random point 0.181 matches `necessity_above_random` in the 155404 run; CIs unverifiable — two of three audits flag missing_artifact) |
| S3.3 sufficiency dissociation (37-base) | Neutral←DS vs Neutral←Direct harmful-compliance | `19_run_behavioral_sufficiency.py` | `behavioral_causality_llama_37base.json` | DS−Direct: early **−0.061 [−0.123, 0.000]** n=179 (DS 0.061 / Direct 0.123); **mid −0.393 [−0.470, −0.311]** n=183 (DS 0.098 / Direct 0.492 — flagship); late **−0.064 [−0.116, −0.012]** n=173 (DS 0.029 / Direct 0.092). DS-injection ≤0.10 at every depth (max DS rate 0.164 on 12-base mid) | positive (Direct-state hijacks; DS-state does NOT — dissociation, mid-specific) | ✓ |
| S3.3 12-base clean corroboration | robustness on clean subset | same | `behavioral_causality_llama_clean.json` | mid −0.295 [−0.443,−0.148] n=61; late −0.161 [−0.274,−0.048] n=62; early +0.032 [−0.081,0.145] n=62 (NS) | positive | ✓ |
| S3.3 cross-model sufficiency | Qwen3 / Phi-4 dissociation | sufficiency runner | `beh_sufficiency_Qwen3-14B_*`, `Phi-4-mini-reasoning_*` | Qwen3 late DS−Direct −0.349 n=43; Qwen3 early +0.190 [+0.071,+0.310] n=42 (runs other way); Phi-4 early −0.263 n=38, late −0.167 n=36 | positive (cross-model) | ✓ point/n; ⚠ bootstrap CI endpoints not stored per-run |
| §3 rep-level re-validation | conditional sufficiency 0.055 vs 0.001 vs 0.008; 9/11 hijackers; demos_only 8/8; multi-layer 0/36 | rep-level stages 07/08/09 | none located | — | prior-sprint claim | ⚠ (no backing JSON among behavioral outputs) |

**Level 2 achieved**: sufficiency dissociation (Direct-state hijacks, DS-state does not) is artifact-solid with paired CIs on 3 models; necessity is real and early-specific but its multi-seed headline CIs lack a reproducible on-disk artifact.

---

### Workstream C / Claim D — Causal timing (TOCTOU)

| Stage | Tested | Script(s) | Artifact | Verified result | Verdict | Flag |
|---|---|---|---|---|---|---|
| S3.4 timing gradient (Llama, 37-base) | early→refusal, late→compliance | `20_run_behavioral_timing.py` | `behavioral_causality_llama_37base.json` timing | Per-window refusal early/mid/late = **0.866/0.246/0.017**; paired early−late **+0.846 [+0.787,+0.899]** n=169; early−mid +0.631 [0.562,0.699] n=176; mid−late +0.214 [0.156,0.277] n=173; ~89% of late generations benign | positive (TOCTOU confirmed) | ✓ |
| S3.4 timing table MALICIOUS/BENIGN cells | descriptive per-window malicious/benign | same | `sufficiency.*.suff_Direct_rate` | mid 0.49 / late 0.09 match exactly; **early MALICIOUS cell doc 0.10 vs artifact 0.123** (baseline-filtered) / 0.113 (all); early BENIGN doc 0.03 vs implied ~0.011 | — | ✗ (early row cells; refusal column and mid/late correct — does not affect monotonic conclusion) |
| S3.4 12-base corroboration | robustness | same | `behavioral_causality_llama_clean.json` | early−late refusal +0.869 [0.770,0.951] n=61 | positive | ✓ |
| S3.4 cross-model TOCTOU | Qwen3 / Phi-4 gradient | sufficiency dir_transitions | `beh_sufficiency_Qwen3-14B_*`, `Phi-4_*` | Qwen3 early/late refusal 1.00/0.14, Δ **+0.854** n=41; Phi-4 0.61/0.33, Δ **+0.250** n=36 | positive (all 3 architectures) | ✓ refusal rates & point Δ reconcile; ⚠ paired bootstrap CIs not stored |

**Level 3 achieved**: same semantic content produces refusal when early, compliance when late — reproduced on Llama, Qwen3, Phi-4.

---

### Workstream D — Causal circuit (carried/confirmed from handoff)

| Stage | Tested | Artifact | Verified result | Verdict | Flag |
|---|---|---|---|---|---|
| Attention knockout (3 models) | demos necessary for hijack | `ko_gen_{llama8b,qwen3,phi4}/stage4_knockout_results.json` | Llama 12/12 hijackers eliminated (P_harm→~0), random-patch control 0.066; Qwen3 12/12, rand 0.059; Phi-4 6/6, rand 0.064 | positive (unanimous) | ✓ |
| Depth localization | where the circuit consolidates | `lko_gen_llama8b/stage4_layerko_results.json` | consolidation median L2 (10/12 <20% by L2); best single-layer median L18 | positive | ✓ |
| Emergence timing panel | Direct-early vs DS-late onset | `emergence_panel_login/emergence_results.json` | all 18 items: Direct peak L0, DS peak L31, paired diff = 31 [31,31] | positive | ✓ |
| RQ1 random-norm control ("126×/8181× weaker") | necessity specificity | `stage2_patching_*_001943/stage2_results.json` | **Not reproducible**; random patch collapses P(harm)→~0 (control fails, points opposite way) | negative/retracted | ✗ (doc self-flags "DO NOT CITE"; superseded by nec−random +0.181 [−0.021,0.383]) |
| Panel necessity/sufficiency (n=7) | small-panel corroboration | none on disk | necessity 98%; suff(DS)−suff(Direct) 0.037 [0.027,0.047] | corroborated by registry only | ⚠ (raw JSON gitignored/absent) |

---

### Workstream E / Claim E — Mechanistic objective (predictive)

| Stage | Tested | Script(s) | Artifact | Verified result | Verdict | Flag |
|---|---|---|---|---|---|---|
| S3.5 success predictors | does the temporal signature predict held-out jailbreak? | `21_extract_behavioral_features.py`, `22_fit_success_predictors.py` | `outputs/features_llama8b/success_predictors.json` | n=240 conditions, 46 positives; **held-out-CONCEPT AUC 0.668 ± 0.089**; 5-fold CV AUC **0.732 ± 0.060**; temporal objective (late − λ·early) AUC 0.654; late_align-alone AUC **0.502** (inert). Direction-flipped univariate AUCs: early_align 0.651, mid_align 0.657 (LOW early harmful alignment predicts jailbreak) | positive but moderate | ✓ (univariate values are 1−AUC flips, internally consistent with abs_power fields) |

**Level 4 achieved**: a benign-early/harmful-late signature predicts held-out-concept behavioral success at AUC≈0.67 (moderate, not 0.9). Labeled *predictive*, not yet mechanistic-utility.

---

### Workstream F / Claim E→utility — GCG/MAC optimization (Level 5)

| Stage | Tested | Script(s) | Artifact | Verified result | Verdict | Flag |
|---|---|---|---|---|---|---|
| S6b codeword selection | pick codeword by temporal score → higher jailbreak | `codeword_selection` analysis | `outputs/features_cw6/codeword_selection.json` | n=40 bases; temporal 0.300 / random 0.208 / anti 0.225; temporal−random **+0.092 [−0.037,+0.225]** (crosses 0); multivariate LOCO +0.067 [−0.046,+0.183] | weak-positive / NS (+9pp, CI crosses 0) | ✓ |
| S6c smoke | temporal-GCG plumbing | `26_run_temporal_gcg.py` | `opt_qwen3_smoke/ITERATION_LOG.jsonl` | 5 steps, step-0 repr_loss=0.4464 | gate-passed | ✓ |
| S6d Temporal-GCG (3 configs) | does repr objective optimize? | `26_run_temporal_gcg.py` | `opt_qwen3_temporal{,_lex,_lexwide}/ITERATION_LOG.jsonl` + `CONFIG.json` | weighted (λ0.3): repr 0.446→0.446→0.565, task 59.6→3.8; lex-tight (λ1.0,ε0.01): repr 0.480→0.463→0.535, task 63.4→**16.1** (doc says 16.4); lex-wide (λ1.0,ε20): repr 0.454→0.450→0.452, task 77.7→71.1; 16-token suffix, 200 steps. repr_loss never net-improves (final>init in 2 of 3; best transient 0.017) | **negative** (objective does not optimize) | ✓ (lex-tight final task_loss ✗ 16.1 vs 16.4, within end-band 15.78–16.45) |
| S-TrackB held-out ASR | does temporal suffix beat baseline behaviorally? | `28_evaluate_optimized_attacks.py` | `outputs/gcg/gcg_asr_summary.json` | n=13 val bases (25 train / 13 val split); ASR temporal **0.0**, baseline **0.0**, none 0.077; refusal temporal **0.615** (8/13) = **8× baseline 0.077**; 0 judge-fail | **negative** (temporal suffix backfires — raises refusal, ASR still 0) | ✓ |

**Level 5 = controlled NEGATIVE**: the mechanistic temporal objective does not reduce repr_loss under GCG and its suffix does not raise held-out behavioral ASR (it *increases* refusal 8×). This is an honest, controls-backed separation of "representation hijacking" from "behavioral attack utility."

---

### Workstream G / Claim F — Thinking vs non-thinking

| Stage | Tested | Script(s) | Artifact | Verified result | Verdict | Flag |
|---|---|---|---|---|---|---|
| Phase 7 within-model (Qwen3-14B) | thinking changes attack success / refusal | `29_run_thinking_comparison.py` | `outputs/behavioral_screen_curated_qwen3_think/thinking_comparison.json` | n=90 matched (15 bases × 3 lengths); DS-malicious **0.222 (think) vs 0.244 (nothink)**, Δ −0.022 [−0.122,0.078] **NS**; DS-rejected **0.000→0.067**, Δ +0.067 [+0.022,+0.122] **sig**; Direct-refused 1.000→0.933 (Δ −0.067 sig); transition matrix cells all match | mixed/null (ASR unchanged; thinking *introduces* a small refusal channel) | ✓ |
| Phase 7 dose-response by demo-count | does thinking steepen dose-response? | `per_condition_corrected.json` (matched n=90) | recompute | Doc quotes nothink 0.09/0.16/0.16 & think 0.14/0.23/0.36; **actual matched rates nothink 0.20/0.267/0.267, think 0.133/0.20/0.333** — doc figures are stale and internally inconsistent (average to 0.137/0.243 vs headline 0.244/0.222) | direction (steepening) holds; numbers wrong | ✗ (all 6 dose cells; qualitative claim survives with corrected values) |

**Level 6 = partial/null**: no ASR difference between modes; thinking's only significant effect is a small added refusal channel (0→0.067). Cross-checkpoint comparisons (Phi-4, DeepSeek) labeled exploratory.

---

### Sprint conclusion

**Established (artifact-backed):** a real behavioral Doublespeak benchmark on curated single-concept prompts (Llama 37/40 eligible, ~20% DS-malicious yield; reproduced on DeepSeek-R1 27/40) — resolving the prior behavioral null, which was itself an artifact of AdvBench's harm not living in a single swappable noun (2/193 eligible) plus a judging bug (iter10). On that benchmark the sprint delivered **Level 1–4**: behavioral necessity (early-specific, identity/random-controlled), a clean sufficiency **dissociation** (explicit Direct state hijacks a Neutral prompt, mid −0.393 [−0.470,−0.311]; the contextual DS state does *not*, ≤0.10 at every depth), a **causal TOCTOU timing law** (early→refusal, late→compliance; early−late +0.846 [0.787,0.899], reproduced on Qwen3 +0.854 and Phi-4 +0.250), and a moderate **predictive** benign-early/harmful-late objective (held-out-concept AUC 0.668 ± 0.089, CV 0.732).

**Negative / killed claims (equally load-bearing):** **Level 5** — the temporal representation objective is *not* a better attack: it fails to optimize under GCG (repr_loss net-worsens in 2/3 configs) and its held-out suffix drives ASR to 0 while multiplying refusal 8×. Codeword-selection gain is only +9pp with a CI crossing 0. **Level 6** — thinking does not change ASR (0.222 vs 0.244, NS); it adds only a small refusal channel. The RQ1 random-norm necessity control ("126×/8181×") is retracted/non-reproducible (self-flagged DO NOT CITE), superseded by nec−random +0.181 [−0.021,0.383].

**Caveats for the merged plan:** the flagship **multi-seed necessity CIs (0.549 / 0.399 / 0.181)** are the weakest-provenance region — no committed artifact reproduces the 0.549/0.399 point estimates (single-seed deltas are all lower; only the 0.181 nec−random point matches one run), so cite them as unverified; several rep-level §3 numbers, the 84-base expanded screen, and two n=7 panels are unverifiable/missing; and the benchmark docs (40 vs 84 bases, "200" vs 193 screened, "18" vs 16 bases, the 2/1-vs-23/9 reclassify conflict, and the thinking dose-response cells) carry stale or mismatched figures that should be corrected before publication. Net: representation hijacking is causal over behavior on the timing and dissociation axes, but is **separable** from attack-optimization utility — a rigorous negative that strengthens, rather than weakens, the paper story.
---

## Sprint 3 — Fixed-pair controlled causal study (CAUSAL_CORE_PLAN, S0–S17)

**Objective.** Rather than scale the behavioral benchmark, this sprint executes a highly controlled, pair-specific causal study on one clean codeword↔concept pair (`CARROT ↔ BOMB`, Llama-3.1-8B-Instruct primary): directly manipulate the internal representation to establish *reversible causal control* over what the codeword is interpreted to mean, dissociate the two candidate causal directions (`d_Direct = h_BOMB-direct − h_CARROT-neutral` vs `d_DS = h_CARROT-DS − h_CARROT-neutral`), convert the validated causal quantity into an optimization objective, and test whether optimizing that objective over demonstrations/codewords beats behavioral optimization on real held-out attack success. The load-bearing empirical result is a clean **dissociation**: `d_Direct` causally *installs* the concept reading (bidirectionally, dose-monotone, exceeding all matched controls), while `d_DS` is causally *inert* — and the causal objective, when used to optimize the attack, is a **CI-backed negative** that behavioral selection beats decisively.

### Per-stage results (S0–S17)

| Stage | What it tested | Driving script(s) / job | Key artifact | Verified result (CI) | Verdict | Audit |
|---|---|---|---|---|---|---|
| **S0** | Audit & freeze prior sprint; fix overclaims | `RESULTS_FREEZE_AUDIT.md`; edits to `PAPER_DRAFT.md` | RESULTS_FREEZE_AUDIT.md | ~85% of ~100 claims verified; 12 wording fixes, 2 claims withdrawn. Meta-audit reproduces from disk (TOCTOU +0.846 [+0.787,+0.899] n=169; Qwen3 +0.854 n=41; Phi-4 +0.250 n=36; CV-AUC 0.732, held-out 0.668±0.089) | gate-passed | ✗ registry now 45 rows not 39 (6 causal-core rows appended post-freeze); ✗ figures/ has 9 top-level PNGs not 11; ⚠ panel07/qwen3_generality CIs have no backing file (SOURCE_MISSING) |
| **S1** | Fixed-pair semantic benchmark build | benchmark builder → `data/pair_benchmark/pair_carrot_bomb.json` | pair_carrot_bomb.json | 800 semantic + 900 behavioral prompts, 60 paraphrases, 0 skipped, tests pass | control | ✓ |
| **S2** | Readout validation gate (Direct+ / Neutral−) | `run_pair_readout.sh` (693557, 800 prompts) | pair_readout_…_693557 | 17/30 cells usable; DS−Neutral reads-as-concept **+0.500 [+0.393,+0.607]**; p_concept **+0.307 [+0.249,+0.367]**, n=84 | positive / gate-passed | ✓ |
| **S3** | Rep extraction (layers×positions×components) | `run_pair_reps.sh` (693558 cloze / 693559 one_word) | pair_reps_…_69355{8,9} | 160 rows each, 256 cells, 0 missing position cells | control | ✓ |
| **S4** | Cross-fitted `d_Direct`/`d_DS` + PCA subspaces | `33_build_directions.py` (299312 / 299521, CPU) | pair_directions_…_299312/299521 | cos(d_Direct,d_DS) at codeword = **0.28** (cloze) / **0.19** (one_word); at final-prompt token **0.83**; d_DS norm **exactly 0** at resid_pre L0 (identical static embedding) | control | ✓; ✗ §2.1 cross-fit d_DS stability doc "0.93–0.97" understates true range **0.859–0.969** (mean 0.916, 16/32 layers below 0.93) — qualitative "high, not noise" stands |
| **S5** | Add/remove/replace intervention sweeps | `run_pair_interv.sh` layer_scan (693570/693571), replace (693597) | pair_interv_layer_scan/replace_… | one_word layer_scan null after Holm; replace arm DS_from_Neutral mid **+0.032 vs shuffled +0.031** (clean negative — replacement not source-specific) | control / negative | ✓ |
| **S6** ⭐ | Dose-response + ≥20 matched controls (main causal result) | `run_pair_interv.sh` controls 693609, dose 693607/693608 | pair_interv_controls_…_693609 | add `d_Direct` at codeword sites: early **+0.167 [+0.105,+0.232]**, mid **+0.533 [+0.453,+0.613]**, late **+0.971 [+0.955,+0.984]** — exceeds all 60 controls/window (180 total; max control +0.0002); monotone Spearman **+0.81/+0.86**; **add `d_DS` = 0.0** and 3 other remap directions exactly 0; adjacent-token +0.013, random-token +0.004 | positive (install) + negative (d_DS inert) | ✓ |
| **S7** | Held-out paraphrase confirmation (text-disjoint splits) | analysis over 693609 interv_raw.jsonl | pair_interv_controls_…_693609 | add `d_Direct` mid **dev +0.584 / heldout +0.483**, late **+0.982 / +0.960**, all CIs exclude 0; add `d_DS` = 0 on both | positive / gate-passed | ✓ |
| **S8** | Attention knockout + attn-vs-MLP patching | `run_pair_attn.sh` (693647 all-layers, 693623 per-layer, 693614 component) | pair_attn_knockout/component_… | all-layers `demos_all` **−99.9%** vs count-matched `random_matched` **−99.7%**; per-layer **−0.0057 vs −0.0077** (random control ≥ demos → NOT demonstration-specific); prev_codewords −2.8% (NS); component patches ≤0.019 (Neutral_from_DS exactly 0) | negative | ✓ (DOUBLESPEAK slice; naive all-rows avg halves it — not a doc error) |
| **S9** | Causal attack-window estimate | analysis (693609 install / 693607 projout) | CAUSAL_OBJECTIVE.md §3 | install peaks **late (+0.971)**; removal (projout `d_Direct`) peaks **mid (−0.157)** → install/remove windows differ (reported as asymmetry, not one number) | control | ✓ |
| **S10** | Causal-objective term adjudication | `CAUSAL_OBJECTIVE.md` | CAUSAL_OBJECTIVE.md | 8 terms: **2 validated** (d_Direct semantic score; early-neutral retention), **4 killed** (d_DS projection, attention routing, component patching, single-window framing), 2 excluded as unvalidated. Early projout raises literal reading **+0.192 (cloze) / +0.280 (one_word)**; add-early p_codeword **0.008→0.488** | positive+negative mix | ✓ |
| **S11** | Continuous soft-prompt positive control (gate) | `run_pair_softprompt.sh` (693655 concept, n=8) | pair_softprompt_simplex_…_693655 | relaxed **0.98861 → discretized 0.00424 (0.43% retention)**; controls 0.9994→0.0124 (unrelated), 1.0→0.1016 (codeword). Not unreachability — real DS demo block hits ~0.476 → optimization gap | negative (gate resolved) | ✓ (took 4 attempts; 3 prior runs vacuous/frozen-optimizer artefacts, caught) |
| **S12** ⭐ | Demonstration/codeword optimization: causal objective vs behavior | `run_pair_behcw.sh` (693683, 693698); `pair_demosel` (693816) | pair_behcw_…_693{683,698}; demosel_…_693816 | slice 1: TOP−BOTTOM = **−0.183 [−0.267,−0.083]** n=12, replicated **−0.133 [−0.200,−0.083]**; per-codeword ρ = **−0.488** (causal score anti-predicts ASR); refusal 0/132; NEUTRAL no-demo arm 0.008 (n=120). slice 2: behavior_greedy 0.833 / causal_greedy 0.250 / full_default 0.167; **behavior−causal +0.583 [+0.333,+0.833]**; causal−random **−0.167 [−0.417,0.000]** | negative (CI-backed) | ✓ |
| **S13** | Codeword properties incl. embedding distance | `run_pair_codeword.sh` (693669, 27 codewords) | pair_codeword_…_693669 | hijack strength spans **4.3×** (0.170→0.737); no static property predicts it (all 15 tests NS after Holm); Matan's distance hypothesis directionally consistent (cosine ρ=**−0.276**, L2 ρ=**+0.186**) but unsupported at n=27 | negative | ✓ |
| **S14** | Qwen3 thinking / non-thinking on fixed pair | `run_pair_readout.sh` (693666 non-thinking; 693837 thinking, 1536 tok) | pair_readout_Qwen3-14B_…_693{666,837} | non-thinking DS−Neutral **+0.694 [+0.583,+0.792]**, p_concept +0.580, n=72, 15/30 (stronger than Llama); thinking: hijack reads-as-concept **1.00** at answer transition, DIRECT 1.00/NEUTRAL 0.00, 0/96 truncated — no second safety check (n=9 degenerate, p_concept invalid in thinking mode) | positive (replicates, stronger) | ✓ |
| **S15** | DeepSeek tokenizer localization + regression tests | tokenizer fix; pytest suite | (test-infra, no jobid artifact) | codeword_last correctness on DeepSeek **28.8%→100%**; failures 192→96/480; other 3 models bit-identical; 43/43 tests; a further fix reverted (measured worse, 96→364) | control | ⚠ unverifiable — no output artifact (test-infra numbers; pytest not runnable here) |
| **S16** | Scale to 5 pairs; is the dissociation Doublespeak-general? | `run_pair_reps/interv/readout.sh` (693694–693705, 693783–693786); `41_aggregate_pairs.py` | pair_generalization.json | 5 pairs, all S2-gated (14–21/30 cells, hijack **+0.45…+0.62**); **`d_DS` inert 5/5; `d_Direct` installs 4/5** (span +0.011 cocaine … +0.971 bomb, ~84×). cocaine a genuine null for both directions (not a readout failure). Per-pair only, never pooled | positive (dissociation general) + negative (cocaine) | ✗ §3 "d_DS max" column reports MID window, true max is EARLY (2–4× larger): pistol doc 0.0053 → **0.0075**, grenade 0.0007 → **0.0020**, cocaine 0.0002 → **0.0008**, chlorine 0.0001 → **0.0004**. All still ≪ 0.05 inert threshold → "5/5 inert" conclusion unaffected; only the column label is wrong |
| **S17** | Documentation / registry / artefact manifest | doc updates; `ARTEFACT_MANIFEST.json` | ARTEFACT_MANIFEST.json; EXPERIMENT_REGISTRY.csv | manifest **55 files / 0.967 GB**, sha256+mtime at commit 0607a61; **+6 causal-core registry rows** (S1/S2/S6/S12×2/S16) | control | ✓ |

### Sprint conclusion

The sprint **established reversible, controlled causal control over the codeword reading via `d_Direct`** and a clean **`d_Direct`-installs / `d_DS`-inert dissociation** that is a property of Doublespeak, not of one pair: adding `d_Direct` at the codeword sites installs the concept interpretation dose-monotonically and near-ceiling (late +0.971), exceeds all 180 matched controls, reverses under projection-out, confirms on text-disjoint held-out paraphrases, and generalizes across 5 pairs / 4 harm categories (inert 5/5, installs 4/5); it replicates and strengthens on Qwen3-14B (+0.694) and survives into thinking mode with no added safety check. **Every attempt to turn the causal quantity into a winning attack objective is an evaluated negative**: attention knockout is not demonstration-specific (S8), the causal soft-prompt objective is discretization-limited (S11, 0.43% retention), no static codeword property predicts hijack strength (S13), and — the decisive §9 result — selecting codewords or demonstrations by the causal score *anti-predicts* held-out ASR (S12: TOP−BOTTOM −0.183, ρ=−0.488) while behavioral greedy selection beats both the causal objective (+0.583) and random search. Doc-vs-artifact integrity is high across all four backing documents: every load-bearing headline reproduces from disk with **no conclusion-inverting mismatch**. The flagged discrepancies are cosmetic/artefact-drift — the §3 "d_DS max" column mislabels the mid-window value (true max 2–4× larger but still far below the inert threshold), the §2.1 cross-fit stability range understates its lower bound (true 0.859–0.969), and post-freeze registry/figure counts drifted (45 rows not 39; 9 PNGs not 11) — none of which alters any positive or negative claim; two items (S15 test-infra numbers, panel07/qwen3 CIs) remain unverifiable for lack of a backing artifact.

---

# Part IV — Master status: what stands, what is retracted, what is unverifiable

| Claim | Sprint · Stage | Status | Backing (verified) |
|---|---|---|---|
| Codeword acquires a late-layer harmful representation (Patchscopes crossover L17–21, peak L30–31) | 1 · P2 | ✅ **stands** | `stage1_repmap_...231610` (crossovers 17/20/21; peaks 30/31/31) |
| Necessity: DS←Neutral patch collapses `P(harm)` to ~0 | 1 · P3 | ✅ stands (direction) | `stage2_patching_...001943`; magnitude upper-bounded pending C1/C3 fix |
| Necessity-vs-random margin "126×/8181×" | 1 · P3 | ❌ **retracted** | non-reproducible; → `nec−random +0.181 [−0.021,0.383]` crosses 0 |
| Conditional sufficiency (Neutral←DS 0.135 > Neutral←Direct 0.001) | 1 · P3 | ⚠ direction stands, magnitude unreliable | `diag_suff_ds.log`/registry; not in canonical 687378; C1 contamination |
| Meaning routed from demonstrations via attention; depth-localized (L18 / kill by ~L14) | 1 · P6 | ✅ stands (magnitude); ⚠ **specificity overturned** | `stage4_knockout/layerko_...`; specificity refuted by 3·S8 (count-matched) |
| Signature generalizes 6 concepts × 6 codewords × 3 families (all timing/nec/suff CIs exclude 0) | 1 · P9 | ✅ stands | `multiconcept_aggregate_{llama8b,qwen3,phi4}.json` |
| Late-harmful probe defense TPR 1.00 / FPR 0.00 | 1 · P10 | ✅ stands (tested set) | `defense_login/defense_results.json` |
| Behavioral link on old seeds | 1 · P5 | ⛔ **null** (n=2) — later explained as AdvBench artifact | `behavioral_login/` |
| Behavioral benchmark exists (Llama 37/40 eligible, ~20% DS-malicious; DeepSeek-R1 27/40) | 2 · A | ✅ stands | `behavioral_screen_curated_v1/`, `..._deepseek_r1/` |
| Behavioral necessity (early-specific) | 2 · B | ✅ direction stands; ⚠ **multi-seed CIs (0.549/0.399) unverifiable** | single-seed on disk; headline not committed; C8 can inflate |
| Sufficiency dissociation (Direct-state hijacks mid −0.393; DS-state does not, ≤0.10) | 2 · C | ✅ **stands** (3 models, paired CIs) | `behavioral_causality_llama_37base.json` etc. |
| Causal TOCTOU timing (early→refuse, late→comply; early−late +0.846) | 2 · D | ✅ **stands** (Llama/Qwen3/Phi-4) | `behavioral_causality_llama_37base.json`, cross-model |
| Predictive objective (held-out-concept AUC 0.668; CV 0.732) | 2 · E | ✅ stands (moderate); ⚠ C9 leakage bounds it | `features_llama8b/success_predictors.json` |
| Temporal-GCG attack objective beats baseline ASR | 2 · F | ❌ **controlled negative** (ASR 0; refusal 8×; repr_loss net-worsens) | `gcg/gcg_asr_summary.json`, `opt_qwen3_temporal*/` |
| Thinking changes ASR | 2 · G | ⛔ **null** (0.222 vs 0.244 NS; only +0.067 refusal channel) | `..._qwen3_think/thinking_comparison.json`; ✗ stale dose cells |
| `d_Direct` reversibly installs the reading (late +0.971; beats all 180 controls; dose-monotone) | 3 · S6 | ✅ **stands** (headline) | `pair_causal_controls_693609.json` (verified in current file) |
| `d_DS` causally inert (5/5 pairs, both readouts, all windows) | 3 · S6/S16 | ✅ **stands** | `pair_generalization.json`; ✗ "max" column shows mid (still inert) |
| Held-out paraphrase confirmation (mid +0.483, late +0.960) | 3 · S7 | ✅ stands | `pair_interv_controls_693609` |
| Attention knockout is demonstration-specific | 3 · S8 | ❌ **negative** (demos −99.9% ≈ random −99.7%) | `pair_attn_knockout_...693647/623` |
| Causal soft-prompt objective is optimizable | 3 · S11 | ❌ negative (0.43% retention; optimization gap, not unreachability) | `pair_softprompt_..._693655` |
| Selecting on causal score improves held-out ASR | 3 · S12 | ❌ **CI-backed negative / inverts** (TOP−BOTTOM −0.183; behavior−causal +0.583) | `pair_behcw_693683/698`, `pair_demosel_693816` |
| Static embedding property predicts codeword hijack strength | 3 · S13 | ⛔ **null** (15/15 NS after Holm; Matan's distance ρ=−0.276 unsupported at n=27) | `pair_codeword_..._693669` |
| Hijack replicates & strengthens on Qwen3-14B (+0.694); survives thinking mode | 3 · S14 | ✅ stands | `pair_readout_Qwen3-14B_693666/837` |

**Bottom line.** The representation-level *mechanism* (necessity, dissociation, timing, routing,
generalization, detection) is solid and artifact-backed. Every attempt to convert it into a
*better attack* is an evaluated **negative**, and the causal-decoding score **anti-transfers** to
behavioral ASR. The publishable result is the dissociation itself plus this honest separation —
not a stronger attack. Before submission, apply the Part II.3 fix-list (retract the 126× ratio,
cap the C1/C3 patch sweeps and re-run P3, commit or retract the 0.549 necessity CIs, refresh stale
counts, regenerate the manifest).
