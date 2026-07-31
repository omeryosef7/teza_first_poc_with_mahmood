# NEXT5 — One-Day (max-depth) Research Sprint Plan

## Context

We have three committed, artifact-backed NEW causal contributions to the Doublespeak /
in-context-representation-hijacking paper (arXiv:2512.03771):

- **S2** — the hijacked reading is carried by receiver **context**, not the codeword's local
  state (IE_state≈0 equiv; DE_context ≈99% of TE on Llama, ≈92% on Qwen3-14B; faithfulness 0;
  4/4 pairs; depth-invariant).
- **S3** — not a trivial demo re-read (distributed on Llama; more demo-localized on Qwen3).
- **S4/T3** — a causal **depth-gated refusal TOCTOU** (interaction +0.425 Holm-sig), with the
  refusal check sitting at a **pair-dependent depth** (bomb EARLY; grenade/chlorine MID) — which
  *explains* why the behavioral factorial (#6) was null for grenade/chlorine (it only tested early).

Honest negatives on record: B4 (`d_Direct` +0.971 doesn't reproduce), T2/N3 (patchscope fails its
positive control), #6 (behavioral TOCTOU not general as-tested).

**Why this sprint:** the user asked to take the research "to the next level with meaningful things
for the paper… as deep as it gets — all of it." Three parallel explorations confirmed that five
workstreams (W1–W5) plus a full attention-head circuit all **reuse existing machinery** with small,
well-scoped additions, and that two of them are near-free CPU re-reductions of committed artifacts.
The intended outcome: (a) convert the #6 negative into a per-pair-timing **confirmation**, (b)
adjudicate the paper's *own* untested **superposition** hypothesis, (c) extend the headline to a
**3rd architecture** (DeepSeek), (d) deliver a **mechanism-derived defense**, and (e) localize the
context effect to a **head-level circuit** — knockout today, z-/path-patching as the deep ceiling.

**Standing constraints (do not violate):** no SLURM dependencies; ≤6 parallel jobs; L40S only
(nodes `n-801..805,t-806`; env `poc_stage2`); job-isolate captures by `SLURM_JOB_ID`; reuse code,
minimal new code; **gate every claim** (positive controls, true-patch validation, equivalence
margins, paired bootstrap + Holm); report negatives honestly; cyber-safeguard — subagents consume
**scalars only**, never open bench prompt text or raw completions, never reproduce harmful text;
never silently overwrite immutable artifacts. Document in external md (`NEXT5_PLAN.md`,
`NEXT5_FINDINGS.md`), commit + push after each landed workstream.

All paths below are under
`/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood/doublespeak_causality/`.

---

## Execution order & parallelism (6-slot cap; CPU reducers are import-safe / login-node-safe)

Quick CPU wins first (cannot fail on infra), then fan out the GPU work. No SLURM deps — each job
self-contained, job-isolated by `SLURM_JOB_ID`.

| Phase | CPU track (login-safe) | GPU track (L40S, ≤6 jobs) |
|---|---|---|
| **0** pre-flight | Verify `pair` field + B/D×{mid,late} cell coverage in the committed `toctou_summary.json` (grenade `..._695290`, chlorine `..._695291`); confirm `directions.npz` + DS reps for W3-b | — |
| **1** quick wins + new hooks | **W1-tier1** reducer + re-reduce; **W3-b** direction-projection | **W5** `AllPositionAdd` build + `validate_layer` positive control; **W2** DeepSeek readout-gate job (31 `--answer-marker`) |
| **2** main runs | reduce W2/W5 outputs; **W4** knockout reduction | **W5** StrongReject eval (malicious + benign); **W2** 32→34→43 transplant chain; **W4** per-head knockout (`36 --granularity per_head`) |
| **3** deep circuit | reduce W4 z-patch map with 43-style CIs | **W4-deep** z-patch AtP layer×head + true-patch validation gate; **W1-tier2** `--windows` rerun (only if tier1 blocked) |
| **4** verify | Holm across all new claims; artifact-vs-doc consistency; run + extend test suite | drain/collect |

Peak GPU concurrency ≈ 3–5, under the 6-cap. The floor deliverable ("W1 confirmation + W3
adjudication") is CPU-only and locked in Phase 1; everything else is additive.

---

## W1 — Per-pair-timing behavioral TOCTOU  *(quick win; turns #6 negative → confirmation)*

**Reuse:** `45_toctou_factorial.py::analyze_rows` already computes `refusal_gain` at early/mid/late
per pair; the #6 null came *only* from the hardcoded `INTERACTION = refusal_gain(early) −
refusal_gain(late)` (`45:113-128`). Committed raw jsonl exists: grenade `outputs/toctou_...695290`,
chlorine `..._695291`. The correct per-item diff-of-diffs reducer already exists in
`47_repr_toctou.py:131-138` (`early_vs_mid`).

**Steps:** (1) Pre-flight confirm B_mid/D_mid/B_late/D_late coverage + `pair` field in
`toctou_summary.json`. (2) In `45::analyze_rows` **add alongside** (do not overwrite) a
`INTERACTION_dominant = refusal_gain(dominant) − refusal_gain(late)` reducer, `dominant` per-pair
from T3 (grenade→MID, chlorine→MID, bomb→EARLY), mirroring `47:131-138`. (3) Re-run
`45 --analyze <dir>` on both committed dirs (CPU).

**Gate:** paired-bootstrap CI on `INTERACTION_dominant` excludes 0 with the **same sign** as T3's
`early_vs_mid` for that pair, AND the pre-existing bomb early−late interaction reproduces
bit-unchanged (regression check). Holm across the new per-pair tests.

**Fallback:** if `mid` coverage is missing or the CI includes 0 → **tier-2**: add a `--windows` CLI
to 45 (copy `47:211`), rerun the factorial only at T3's concept-specific sub-window (≤2 GPU jobs).
If still null → honest bounded negative: a representational-vs-behavioral dissociation (still
publishable).

---

## W3 — Superposition test  *(quick win; adjudicates the paper's OWN untested hypothesis)*

The paper hypothesizes both TOCTOU (tested) and semantic **superposition** (codeword rep encodes
codeword **and** concept simultaneously) — untested until now.

**W3-b (primary, zero new model runs):** load committed `directions.npz` (`d_Direct` = concept
axis; build a codeword axis consistent with how the concept axis was built) + captured DS reps.
Per layer, project each DS codeword rep onto **both** axes → 2-D `(concept_component,
codeword_component)` trajectory. Reduce 43-style (paired CI + Holm): are **both** components
simultaneously non-zero in the band where the reading emerges? Lean on projection (not patchscope)
because patchscope fails the bomb positive control (T2/N3).

**Gate (control separation):** neutral/codeword-only must load the codeword axis but **not** the
concept axis; direct-harmful must load the concept axis but **not** the codeword axis. Only if
these two controls cleanly separate is "both non-zero in DS" interpretable as superposition. Report
projection **scalars** only.

**Fallback:** if the axes don't separate (entangled), report the geometry descriptively
(inter-axis cosine, per-layer components) as an honest "not linearly separable" bound — do **not**
rescue with patchscope on bomb. **W3-a (secondary, if time):** change `11_emergence_trajectory.py:62-70`
to keep **both** `ps_concept` and `ps_codeword` (currently discards the codeword prob at `11:68`;
`44:277-303` already co-records all four scalars) — but run only for grenade/chlorine and only
after their own layer-matched patchscope positive control passes.

---

## W2 — DeepSeek-R1-Distill-Llama-8B as a 3rd architecture  *(generality; new answer-position readout)*

Cached and complete. DeepSeek hardcodes `<think>`, so `enable_thinking=false` is a no-op — needs a
post-`</think>` **answer-position** readout. `31_validate_readouts.py:111-163`
(`generate_with_first_scores`) already implements the `--answer-marker '</think>'` scoring and works
architecture-agnostically → the readout **gate** runs today.

**Gap:** `34_intervention_sweep.py` reads the forward-only `semantic_score` at prompt position −1
(= the first `<think>` token for DeepSeek), not the answer. Add **one** helper: a patched
generation-time answer-position score = compose `pair_common.patched_generate` (`521-534`) with the
`</think>`-marker scoring of `31:143-156`, threaded via a new `--answer-marker` flag through `34`'s
`emit` (`239-249`). `32` (reps, prompt-side) needs no change; `31` needs no change.

**Steps:** (1) `31 --answer-marker '</think>' --max-new-tokens ~1536` readout gate on DeepSeek. (2)
if gate passes, build the patched answer-position helper. (3) run the S2 transplant chain
31→32→33→34→43 (thinking-aware) on DeepSeek.

**Gate:** the DeepSeek readout gate must show `DS−Neutral reads_as_concept` CI-excludes-0 (as
Qwen3 did) **before** the transplant is interpreted. **Fallback:** if the gate fails (thinking-model
readout unreliable, as the Qwen3 gate once did), report it as an honest architecture-scope bound and
stop — do not force a transplant on a floored readout. (Note DeepSeek's known codeword-localization
edge cases in `ds_common.py:216-230,367-441` → expect some missing-position cells in 32.)

---

## W5 — Mechanism-derived defense  *(operationalizes the headline mechanism)*

Finding: harmful semantics emerge late while the refusal check acts earlier → **add** `+α·v_refusal`
at the late/use depth *throughout generation* to block late-emerging compliance.

**Gap:** no all-position ADD hook exists (`ds_common.LayerPatch` add is prefill-only;
`make_project_out_hook` is project-out only). Add `AllPositionAdd(MultiLayer)` to `pair_common.py`
— the `h = h + α·d̂` analogue of `make_project_out_hook` (`387-411`) / `AllPositionProjectOut`
(`414-486`), ~20 lines, firing on prefill **and** every decode step.

**Reuse:** `v_refusal` = `outputs/stage_gcg_full/refusal_direction_llama_L18.pt`;
`build_refusal_direction_llama.validate_layer` already proves ADD induces refusal (positive
control); eval harness = `14_behavioral_eval.py` (StrongReject `malicious_rate` on Doublespeak +
benign over-refusal specificity control).

**Steps:** (1) build + unit-test `AllPositionAdd` (assert it fires at a decode step `seq==1` where
prefill-only `LayerPatch` skips). (2) `validate_layer` positive control at the late layers (AtP
concentration L24–L30, or T3's mid layers for grenade/chlorine). (3) sweep α; run
`14_behavioral_eval.py` for malicious_rate (Doublespeak, should drop) + benign over-refusal (must
not spike).

**Gate (two-sided):** malicious_rate reduction CI excludes 0 **and** benign over-refusal increase is
bounded near 0 (equivalence margin) — the defense must be *specific*, not blanket refusal;
`validate_layer` must pass first. **Fallback:** if benign specificity tanks, report the
ASR-vs-over-refusal trade-off curve (still a finding); if late-layer ADD fails validation, fall back
to the mid layers where the check localizes and document the depth dependence.

**Cyber-safeguard:** the subagent running `14_behavioral_eval` consumes only the scalar
malicious/refusal summaries — never raw completion text.

---

## W4 — Attention-head circuit  *(knockout today → z-patching → path patching as the deep ceiling)*

**Tier A (today, zero new primitives):** `36_pair_attention.py --mode knockout --granularity
per_head` already does per-head attention-mask knockout (query codeword → demo/random source sets,
scored by `semantic_score`, eager attention, GQA-aware via `pair_common.AttentionKnockout:330-381`).
Restrict to the validated layer band (`--layers`). Reduce with the `43`/`stats.py` machinery keyed on
`(layer, head)` → paired bootstrap CI + Holm. A head is "necessary" only if its knockout drops
`semantic_score` with CI excluding 0 **vs the random-source knockout control**. Fallback: pooled
band-level knockout if per-head is underpowered.

**Tier B (deep, the one genuinely new primitive):** per-head **z** capture/patch — a
forward-hook on `self_attn.o_proj` splitting its input to `[seq, n_heads, head_dim]` (nothing in the
tree captures z or patches per head today; `AttentionKnockout` only masks). ~40–60 lines, mirroring
`SubmodulePatch`/`LayerPatch` semantics + a decode-step position guard + GQA handling (pattern
already in `pair_common.py:338-339`). Add a synthetic locality/self-swap unit test (clone
`tests/test_layerpatch_synthetic.py`). Then extend `48_attribution_patching.py`: swap
`_ActGradCapture`'s residual target for the z hook, key cells on `(L,h,pos)` → a **layer×head AtP
map**, gated by a **per-head true-patch validator** (the same z hook run as a real patch;
`true_patch_delta` + Pearson/Spearman ≥ `--min-corr`, exactly as `48:215-229,398-412` gates
layer×position). Alignment (`build_alignment` `48:256-301`), metric (`make_metric`), and stats all
carry over unchanged.

**Gate:** the layer×head AtP map is only trustworthy if it passes the true-patch correlation gate
(≥ min_corr, as the residual AtP already does, pearson 0.89–0.95). **Fallback:** if z-patching
doesn't validate, ship Tier A knockout localization alone (still a paper-grade result) and document
z-patching as validated-technique-pending.

**Deferred beyond z-patching:** full sender→receiver **path patching** (freeze all non-sender
components) is a further step on top of z-patching — attempt only if Tier B validates with time to
spare; otherwise explicitly deferred (~2–3 days total for the full circuit).

---

## Verification / self-check (Phase 4, mandatory)

1. **Reducer regression (W1):** the pre-existing bomb early−late interaction scalar must be
   bit-unchanged (new reducer is purely additive).
2. **Artifact-vs-doc consistency:** every new headline scalar cross-checked against committed
   narrative; specifically W1's per-pair `dominant` map must match T3's committed `early_vs_mid`
   signs (`47` per_pair/pooled). A sign mismatch is stop-ship.
3. **Single Holm family** across ALL new claims added today (W1 per-pair, W2 transplant, W3
   both-nonzero, W4 per-head, W5 malicious-rate) — no per-workstream uncorrected p-values.
4. **Equivalence margins** for every claimed null (W5 benign over-refusal, any IE_state≈0 on
   DeepSeek) — explicit margin, not "CI includes 0."
5. **Positive-control ledger:** log PASS/FAIL of each workstream's positive control *before*
   interpreting its main effect (the discipline that withdrew T2 and B4).
6. **Tests:** run the existing 52-test green suite after `45`/`pair_common`/`48` edits; add unit
   tests for (a) the W1 reducer == `47` `early_vs_mid` on a synthetic 4-cell fixture, (b)
   `AllPositionAdd` applying at a `seq==1` decode step, (c) per-head z-patch self-swap == baseline
   (locality).
7. **Docs + commit:** update `NEXT5_FINDINGS.md` + `PAPER_CONTRIBUTION.md`/`HANDOFF.md` to match
   artifacts (honest negatives included); commit + push after each landed workstream.

## Honest risk summary

Floor (cannot fail on infra): **W1-tier1 + W3-b** are CPU re-reductions of committed artifacts —
worst case they yield honest bounded negatives, which the paper treats as first-class. Mid bets:
**W5** (~20 new lines + two-sided gate; a refusal/over-refusal trade-off is itself reportable) and
**W2** (new answer-position helper + a thinking-model readout gate that has historically failed —
gated so a failure is an honest scope bound, not a forced result). Deep ceiling: **W4 Tier B**
z-patching is the one conceptually-new primitive and the item most likely to spill past a day; it is
gated by true-patch validation and degrades gracefully to Tier A knockout. Full **path patching** is
attempted only if z-patching validates early. Every branch is designed so a failed gate produces
paper content rather than nothing.
