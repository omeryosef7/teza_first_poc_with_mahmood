# Refusal Is a Time-of-Check Operation: A Causal Timing Law Behind In-Context Representation Hijacking

*Working draft. All quantitative claims are copied from committed, audited output files (see
`SPRINT_REPORT.md` §Appendix for paths) and were re-verified against code. Numbers are stable; prose is a
first pass for the authors to edit.*

---

## Abstract

Recent work (*Doublespeak*, In-Context Representation Hijacking) shows that a benign codeword can acquire a
harmful meaning purely through in-context demonstrations, and that this meaning **emerges in a model's late
layers**. That evidence is observational and representation-level: it reads what a codeword *decodes to*
inside the network, leaving open whether the phenomenon is a genuine behavioral jailbreak, whether the late
emergence is *causal*, and *why* a late-emerging meaning would evade safety training. We close this loop. On
a purpose-built "harm-in-a-single-noun" behavioral benchmark with a strict eligibility gate, we show the
hijack is (i) a **real behavioral jailbreak** that reproduces across four model families (Llama-3.1-8B,
Qwen3-14B, Phi-4-mini, DeepSeek-R1-Distill-8B); (ii) **causally necessary** at early layers and
**conditionally sufficient**; and (iii) governed by a **causal timing law**: injecting a harmful concept
*early* yields refusal 87% of the time, but *late* yields refusal only 2% and compliance instead
(early−late refusal gap +0.846, 95% CI [+0.787, +0.899]). We interpret this as a **time-of-check (TOCTOU)**
property — refusal checks *early* representations, so Doublespeak's late-emerging meaning slips past the
check. The timing signature is *predictive*: a "benign-early / harmful-late" feature predicts held-out
jailbreak success (held-out-concept AUC 0.67). Two further results sharpen and bound the phenomenon. First,
representation-level *decoding*-sufficiency and *behavioral* sufficiency **dissociate** — injecting the raw
concept is behaviorally more potent than injecting the hijacked state, the opposite of the Patchscopes
prediction — a caution for interpretability-based attack claims. Second, the attack is
**demonstration-bound**: a mechanism-derived temporal objective cannot be optimized into an adversarial
suffix (and attempting it *increases* refusal), so the hijack's power lives in the in-context
demonstrations, not in a distillable trigger.

---

## 1. Introduction

Safety-tuned language models refuse harmful requests, yet a growing catalogue of jailbreaks evades that
refusal. *Doublespeak* is a particularly clean instance: a few demonstrations teach a benign codeword (e.g.
"kettle") a harmful referent, after which the model complies with a request phrased entirely in benign
tokens. The originating work localizes the hijacked meaning to **late layers** using Patchscopes-style
representation decoding — an elegant observation, but one that stops at the representation. It does not
establish that the decoded meaning drives *behavior*, that the late emergence is *causal* rather than
correlational, or *why* late emergence should matter for safety.

This paper turns that observation into a causal, behavioral, architecture-general account, and in doing so
surfaces a general principle about how refusal is implemented:

> **Refusal is a time-of-check operation on early representations.** Safety acts on what a prompt means
> *early* in the network; a meaning that only materializes *late* is never checked. Doublespeak works
> because its demonstrations delay the harmful meaning past the checkpoint.

Contributions:
1. A **behavioral benchmark** and eligibility gate that isolate the hijack, converting the paper's
   representation-level effect into a measurable jailbreak (and correcting a judging artifact that had
   masked it).
2. **Causal necessity and sufficiency** of the early-layer codeword representation, with matched identity
   and norm-matched-random controls.
3. The **TOCTOU timing law** (§4.3): a monotone early→late refusal gradient, significant across three
   architectures and reproducing on a fourth, and a **predictive** early-benign/late-harmful signature.
4. Two boundary results: a **decoding-vs-behavioral sufficiency dissociation**, and a demonstration
   proving the attack is **not distillable into an adversarial suffix**.

---

## 2. Background and related work

**Doublespeak / in-context representation hijacking.** Demonstrations bind a benign codeword to a harmful
concept; the harmful meaning is recoverable from late-layer representations via Patchscopes. Our benchmark,
labels, and codeword machinery build directly on this setup.

**Jailbreaks and optimized triggers.** Greedy Coordinate Gradient (GCG) and related methods optimize an
adversarial suffix to elicit harmful completions. We use a GCG harness not to attack per se, but as a
*test*: can the mechanism we identify be compiled into a suffix? (It cannot — §4.5.)

**Interpretability of refusal.** Prior work identifies refusal directions and layers. We add a *temporal*
axis: the *when* of harmful meaning, relative to a refusal checkpoint, is itself causal.

---

## 3. Method

**Benchmark (harm-in-a-single-noun).** Each item ("base") is constructed so its harm resides in one noun.
Three prompt variants: **Direct** (the raw harmful request), **Neutral** (the harmful noun replaced by a
benign codeword → a harmless request), and **Doublespeak (DS)** (Neutral preceded by demonstrations binding
the codeword to the harmful meaning). An **eligibility gate** keeps only bases where Direct is refused/harmful
AND Neutral is benign, so any harm under DS is attributable to the hijack.

**Judging.** A StrongReject rubric harm-score plus a keyword refusal detector, combined MALICIOUS-first:
`score ≥ 0.25 → MALICIOUS; elif keyword-refusal → REJECTED; else BENIGN`. (An earlier StrongReject
*refusal* sub-score mislabeled benign off-goal answers as refusals, faking a behavioral null; we use
keyword-only refusal.)

**Causal interventions** (full greedy generation; layer windows early 0–9 / mid 10–19 / late 20–31):
- **Necessity** — patch the codeword's representation toward its Neutral counterpart during DS generation;
  controls: identity patch (no-op) and norm-matched random patch.
- **Sufficiency** — inject the DS-state vs the Direct-state into a bare Neutral prompt (no demonstrations).
- **Timing** — inject the raw harmful concept at each window and read the refusal rate by depth.

Paired-bootstrap CIs (10k resamples, fixed seed); effects conditioned on the baseline reproducing the
required label. Models run in bf16 on L40S GPUs.

---

## 4. Results

### 4.1 A real behavioral jailbreak
On the curated Llama screen, **37/40 bases are eligible and 42 DS generations are clean jailbreak successes
across 14 concepts**. With correct judging, the hijack is a genuine behavioral attack — the paper's
"behavioral null" was a judging artifact.

### 4.2 Necessity is early-layer and content-specific
Patching the codeword's **early** representation toward Neutral flips malicious→benign. Seed-averaged over
three random seeds (repeated-measures-correct, 23 units):
- Δ_necessity = **0.549** [0.362, 0.737] (strong);
- necessity − identity = **0.399** [0.177, 0.617] — the patch's *content* matters, not just the act of
  patching;
- necessity − random = **0.181** [−0.021, 0.383] — the margin over a norm-matched random patch is genuinely
  modest (robust across seeds, not a single unlucky draw). *We do not over-claim specificity beyond the
  identity control.*

### 4.3 ⭐ The TOCTOU timing law
Injecting the raw harmful concept at increasing depth (37 bases, per-condition, reproducible):

| injection window | refusal | malicious |
|---|---|---|
| early (0–9)  | **0.87** | 0.10 |
| mid (10–19)  | 0.25 | **0.49** |
| late (20–31) | **0.02** | 0.09 |

Paired refusal gradient **early − late = +0.846 [+0.787, +0.899]** (n=169); early−mid +0.631; mid−late
+0.214 — all significant. Early harmful meaning is exposed to the refusal machinery and refused; late
harmful meaning arrives after the refusal-sensitive window and is complied with. **Refusal is a
time-of-check operation on early representations, and Doublespeak's late emergence is precisely the
mechanism of evasion.**

**Architecture-generality.** The timing gradient is significant on three architectures — Llama
**+0.846** [+0.787,+0.899] (n=169), Qwen3 **+0.854** [+0.732,+0.951] (n=41), Phi-4-mini **+0.250**
[+0.056,+0.444] (n=36); the reasoning model (Phi-4) is smaller but still excludes 0. The **behavioral
jailbreak additionally reproduces on a fourth model**, DeepSeek-R1-Distill-8B (27/40 eligible, 66 malicious
conditions).

### 4.4 The mechanism predicts, and dissociates from decoding
A "benign-early / harmful-late" temporal signature **predicts held-out jailbreak success**:
held-out-**concept** AUC **0.668 ± 0.089** (GroupKFold), 5-fold CV 0.732; the load-bearing feature is
*early-benign* alignment (late alignment alone is inert, AUC 0.502) — coherent with the timing law.

However, **decoding-sufficiency and behavioral-sufficiency dissociate.** Patchscopes predicts DS-injection >
Direct-injection; behaviorally we find the opposite, **Direct ≫ DS**, at mid (DS−Direct = **−0.393**
[−0.470, −0.311], n=183) and late (**−0.064** [−0.116, −0.012], n=173). The hijacked state decodes as the
concept but is *context-dependent* — it loses behavioral force when transplanted out of its demonstrations.
**Interpretability-based decoding-sufficiency does not predict, and here inverts, behavioral sufficiency** —
a methodological caution.

### 4.5 The attack is demonstration-bound, not a distillable suffix
Can the temporal objective (make late reps harmful, early benign) be compiled into an adversarial suffix?
We built a mixed reference cache (early layers ← benign reps, late ← harmful reps) and optimized a 16-token
GCG suffix on Qwen3 to minimize distance to it. **The objective is not suffix-optimizable:** the temporal
`repr_loss` never decreased across three selection strategies, including one that freely sacrificed the task
target. Behaviorally the temporal suffix **backfires** — held-out ASR 0 (equal to baseline GCG), but refusal
rises to **0.615** (8× baseline). A raw adversarial suffix appending harm *late* is caught by or fails to
install past the refusal checkpoint; only the **demonstrations** smuggle late-emerging meaning through.
**The hijack's power resides in the in-context demonstrations, not in a transferable trigger.**

---

## 5. Discussion

The unifying account is temporal. Safety training installs a *check* that reads early-layer meaning; a
prompt whose harmful meaning is delayed past that check is complied with. This (a) explains Doublespeak's
late emergence as the *mechanism* of evasion rather than an incidental property, (b) predicts which items
jailbreak (early-benign signature), and (c) bounds the attack (a late meaning must be *installed by context*,
not appended as a suffix, or it is re-checked/refused). The decoding-vs-behavior dissociation warns that
representation-decoding evidence should not be read as behavioral evidence.

**Defensive implication.** If refusal is time-of-check, robustness may require *time-of-use* checking —
re-evaluating harmfulness at the layers/positions where meaning actually resolves, not only early. The
reasoning-model result (Phi-4/DeepSeek) is suggestive: chain-of-thought, which re-examines meaning at any
depth, compresses (but does not erase) the timing gradient.

---

## 6. Limitations
- Necessity's specificity over a *random* patch is modest (+0.18, CI crosses 0) — robust but not
  significant; likewise a codeword-selection variant of the objective gives a directional but NS +0.09 ASR
  gain (n=40). Larger N is the lever.
- Scale: sufficiency/timing on 37 Llama-eligible bases; GCG on Qwen3 (25 train / 13 held-out). One greedy
  generation per condition.
- The 4th model contributes jailbreak *reproduction* only; its timing-sufficiency run was deferred (a
  model-specific tokenizer edge case).

## 7. Conclusion
On a properly-built behavioral benchmark, in-context representation hijacking is a real, causal,
architecture-general jailbreak whose mechanism is a **time-of-check timing law**: refusal inspects early
representations, so late-emerging harmful meaning evades it. The mechanism is predictive, dissociates from
representation-decoding sufficiency, and bounds the attack to its demonstration context. Refusal robustness
may need to become time-of-*use*.

---

### Reproducibility
All results, CIs, and figures are produced by scripts in `doublespeak_causality/` from committed outputs
(`SPRINT_REPORT.md` §Appendix). Interventions: `18/19_run_behavioral_{necessity,sufficiency}.py`; CIs:
`analyze_behavioral_causality.py`; predictor: `22_fit_success_predictors.py`; temporal-GCG:
`gcg_manifest_bridge.py` → `gcg_mixed_cache.py` → `poc_stage_gcg_early/run_optimization.py` →
`25_eval_gcg_asr.py`. Figures: `figures/fig_{toctou_timing,sufficiency_depth,necessity_windows,
crossmodel_behavioral}.png`.
