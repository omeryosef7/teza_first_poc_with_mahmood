# Causal Results Summary

Per plan §5.6 / §22: **observational**, **predictive**, and **causal** findings are kept strictly separate. A layer-wise curve is NOT causal evidence. "Causal" is used only for results backed by an intervention + controls.

Seed caveat (applies to all below): results use the small **hand-written seed** (`data/seed_concepts.json`, 3 items, seed-variant demos — NOT the paper's GPT-4o-mini-generated demos). Directionally informative; absolute magnitudes and statistics are not paper-faithful until we scale items + regenerate demos. Model: Llama-3.1-8B-Instruct, bf16, L40S, templated. Run: `stage1_repmap_*_20260726_231610`.

---

## 1. Observational findings (Stage 1, §8) — NO causal claim

**O1 — The Doublespeak codeword acquires the harmful direction across layers.**
At the codeword position, cosine(DS, Direct) rises from ~0.06 (early) to ~0.55–0.62 (late), while cosine(DS, Neutral) stays high (~0.82–0.88). Interpretation: the codeword keeps its surface-token identity but progressively gains a harmful-concept component in mid/late layers (superposition), consistent with the paper.

**O2 — Patchscopes: harmful meaning emerges LATE (matches the paper's headline).**
Patching the codeword rep into the inspection prompt, P(harmful) overtakes P(codeword) at:
| item | crossover layer | peak P(harm) | peak layer |
|---|---|---|---|
| bomb_potato | 17 | 0.125 | 30 |
| poison_mango | 20 | 0.205 | 31 |
| bomb_carrot | 21 | 0.009 | 31 |
P(harmful) is ~0 early and rises only in late layers; P(codeword) stays ~0 throughout. Absolute probs are modest (weak demos) but the late-emergence direction is clear.

**O3 — NN-decode (auxiliary, not standalone evidence).**
Logit-lens argmax around the codeword in late layers:
- `poison_mango`: L24 → " poison", L28 → " deadly", L31 → " poison" — the benign codeword reads out as the harmful concept.
- `bomb_potato`: L24 → " makeshift"/" ingredients" (bomb-making context), settles to " potato" at L31.

**O4 — Codeword choice appears to matter (RQ6 signal, anecdotal n=1).**
For "bomb": potato (peak P_harm 0.125) ≫ carrot (0.009). Motivates the P8 codeword study.

**Gate check (§25) — passed:** baseline reproducible ✅, target indices valid ✅, Direct/Neutral/Doublespeak trajectories differ meaningfully ✅, α=0 = identity ✅. → cleared to run the causal test (P3).

## 2. Predictive findings
_None yet._ (Would require: does an early-layer feature predict Malicious vs Rejected vs Benign outcome? — comes after P5.)

## 3. Causal findings

**PRELIMINARY** (login-GPU fp16 validation run; canonical bf16 L40S = job 686723 pending). Not yet committed as a final claim.

**C1 (necessity, preliminary) — the codeword's mid/late-layer representation is causally necessary for harmful decoding.**
Intervention: during the Doublespeak forward, replace the codeword activation at layer L with the matched Neutral activation (DS←Neutral), sweep L, read P(harm) at the codeword (in-context logit lens).
- Patching at EARLY layers (L0–4) barely changes P(harm) (potato ~0.11–0.14 vs baseline 0.128) — early the DS and Neutral codeword reps are ~identical (hijack not yet formed).
- Patching from MID layers on collapses it (potato →0.04 by L6 →0 late; mango 0.207→0 by ~L12).
- Controls: identity (DS←DS) reproduces baseline (id_max_dev 0.008 potato ≪ effect); random norm-matched patch does not mimic the necessity drop.
Reading: the harmful component the codeword *acquires* across layers (see O1/O2) is necessary for the harmful readout, and it lives in the codeword's own representation from mid-layers onward.

**C2 (sufficiency, preliminary NULL — readout-limited).** A single-layer Neutral←Direct patch does NOT make the codeword decode as harmful (P(harm)=0 at all layers). BUT the in-context logit-lens readout measures next-token prediction, not concept meaning, so this is a lower bound. **Refinement queued:** re-measure sufficiency with the Patchscopes readout (Stage-1's paper-faithful method) before any sufficiency claim.

Caveats: fp16 login run + hand-written seed demos; confirm on bf16 (686723) and paper-faithful demos. Necessity is robust across two readouts (logit-lens here + Patchscopes crossover in O2).

## 4. Failed interventions
_None yet._

## 5. Open questions
- Is the weak absolute Patchscopes signal due to hand-written demos? → regenerate demos with GPT-4o-mini (paper-faithful) + scale items before strong quantitative claims.
- Does the late-emergence (O2) causally separate refusal (early) from compliance (late)? → P4 timing experiment.
- `find_word_occurrences` variant-undercount must be fixed before P6 (attention knockout needs all codeword occurrences).
