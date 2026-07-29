# Does Refusal Check Early? A Depth-Resolved Causal Study of In-Context Representation Hijacking

<!-- Title corrected 2026-07-29 (RESULTS_FREEZE_AUDIT.md). The previous title, "Refusal Is a
Time-of-Check Operation: A Causal Timing Law Behind In-Context Representation Hijacking",
asserted as established two things the experiments do not show: that the depth-dependent
refusal effect is a "law", and that it is the mechanism *behind* Doublespeak. The timing
experiment injects the RAW concept at varying depth; it never manipulates the depth at which
the HIJACKED meaning emerges, so the link to Doublespeak is an inference. -->


*Working draft. Quantitative claims are derived by the scripts in `doublespeak_causality/` from files under
`outputs/` (present on disk; **not tracked in git** — `.gitignore:12`). The numbers in §4.2, the cross-model
rows of §4.3, and §6's codeword-selection result are recomputed from raw per-generation logs and do not yet
have committed summary artefacts. See [`RESULTS_FREEZE_AUDIT.md`](RESULTS_FREEZE_AUDIT.md) for the full
claim-by-claim verification (2026-07-29): ~85% VERIFIED, with the corrections below already applied.*

---

## Abstract

Recent work (*Doublespeak*, In-Context Representation Hijacking) shows that a benign codeword can acquire a
harmful meaning purely through in-context demonstrations, and that this meaning **emerges in a model's late
layers**. That evidence is observational and representation-level: it reads what a codeword *decodes to*
inside the network, leaving open whether the phenomenon is a genuine behavioral jailbreak, whether the late
emergence is *causal*, and *why* a late-emerging meaning would evade safety training. We close this loop. On
a purpose-built "harm-in-a-single-noun" behavioral benchmark with a strict eligibility gate, we show the
hijack is (i) a **real behavioral jailbreak**, if a low-rate one — 42 of 240 screened Doublespeak
generations are clean successes (Direct refused, Neutral benign, Doublespeak malicious) across 18 bases and
14 concepts — which reproduces across four model families (Llama-3.1-8B, Qwen3-14B, Phi-4-mini,
DeepSeek-R1-Distill-8B); (ii) **causally dependent** on the early-layer codeword representation — patching
it toward its benign counterpart flips harmful→benign (0.549 [0.362, 0.737]), significantly above an
identity patch (+0.399 [0.177, 0.617]) but only *non*-significantly above norm-matched random (+0.181
[−0.021, 0.383]) — while the hijacked state is **not** behaviorally sufficient when transplanted
(malicious ≤ 0.10 at every depth); and (iii) accompanied by a steep **depth-dependent refusal effect**:
injecting the raw harmful concept early is refused 87% of the time versus 2% late (early−late +0.846,
95% CI [+0.787, +0.899], n=169). This is *consistent with* refusal acting on early representations — a
**time-of-check** reading that would explain why a late-emerging meaning goes unchecked — but we never
manipulate the depth at which the *hijacked* meaning emerges, so the connection to Doublespeak remains an
inference rather than a demonstrated causal chain. Note also that late injection produces little harmful
output (malicious 0.09 versus 0.49 at mid; 89% benign), so the low late refusal rate partly reflects loss of
behavioral effect rather than escaping a check. The timing signature carries *modest correlational*
predictive signal (held-out-concept AUC 0.668 ± 0.089, a fold spread reaching chance; late alignment
alone 0.502). Two further results sharpen and bound the phenomenon. First, representation-level
*decoding*-sufficiency and *behavioral* sufficiency **dissociate** — injecting the raw concept is
behaviorally far more potent at mid layers than injecting the hijacked state (0.492 versus 0.098;
−0.393 [−0.470, −0.311], n=183), the opposite of the Patchscopes prediction — a caution for
interpretability-based attack claims. Second, the attack **resisted distillation into an adversarial
suffix** under the one optimizer we tried: 16-token GCG on Qwen3-14B across three selection strategies
showed no sustained decrease in the representation objective over 200 steps and *increased* refusal rather
than success. Other optimizers, suffix lengths, placements and models are untested, so this bounds rather
than forecloses suffix distillation.

---

## 1. Introduction

Safety-tuned language models refuse harmful requests, yet a growing catalogue of jailbreaks evades that
refusal. *Doublespeak* is a particularly clean instance: a few demonstrations teach a benign codeword (e.g.
"kettle") a harmful referent, after which the model complies with a request phrased entirely in benign
tokens. The originating work localizes the hijacked meaning to **late layers** using Patchscopes-style
representation decoding — an elegant observation, but one that stops at the representation. It does not
establish that the decoded meaning drives *behavior*, that the late emergence is *causal* rather than
correlational, or *why* late emergence should matter for safety.

This paper turns that observation into a behavioral and depth-resolved causal account, and in doing so
motivates — without yet establishing — a hypothesis about how refusal is implemented:

> **Hypothesis (time-of-check).** Safety may act on what a prompt means *early* in the network, so a
> meaning that only materializes *late* would go unchecked, and Doublespeak would work because its
> demonstrations delay the harmful meaning past the checkpoint.
>
> **What we show, and what we do not.** We show a steep depth-dependent refusal effect for injections of the
> *raw* harmful concept. We do **not** manipulate the depth at which the *hijacked* meaning emerges, which is
> what the hypothesis is actually about. The two are linked here by inference, not by experiment. Closing
> that gap is the single most valuable follow-up, and is the target of the fixed-pair causal study tracked in
> `CAUSAL_CORE_PROGRESS.md`.

Contributions:
1. A **behavioral benchmark** and eligibility gate that isolate the hijack, converting the originating
   paper's representation-level effect into a measurable — if low-rate — jailbreak (and correcting a judging
   artifact that had masked it).
2. A **causal-dependence** result for the early-layer codeword representation, with matched identity and
   norm-matched-random controls, reported together with the fact that the margin over norm-matched random
   crosses zero; and the accompanying **negative** result that the hijacked state is not behaviorally
   sufficient when transplanted.
3. A **depth-resolved refusal gradient** (§4.3): monotone early→mid→late on Llama-3.1-8B, with the
   early-vs-late difference reproduced on two further architectures (windows scaled per model), plus a
   *correlational* early-benign/late-harmful signature with modest held-out predictive value.
4. Two boundary results: a **decoding-vs-behavioral sufficiency dissociation**, and a **bounded negative** —
   the mechanism resisted distillation into a 16-token GCG suffix on one model under three selection
   strategies.

---

## 2. Background and related work

**Doublespeak / in-context representation hijacking.** Demonstrations bind a benign codeword to a harmful
concept; the harmful meaning is recoverable from late-layer representations via Patchscopes. Our benchmark,
labels, and codeword machinery build directly on this setup.

**Jailbreaks and optimized triggers.** Greedy Coordinate Gradient (GCG) and related methods optimize an
adversarial suffix to elicit harmful completions. We use a GCG harness not to attack per se, but as a
*test*: can the mechanism we identify be compiled into a suffix? (It resisted the attempt — §4.5.)

**Interpretability of refusal.** Prior work identifies refusal directions and layers. We add a *temporal*
axis, and ask whether the *when* of harmful meaning, relative to a putative refusal checkpoint, matters
causally. Our depth-resolved injections say it does for the raw concept; whether it does for a hijacked
representation is left open (§1).

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

**Causal interventions** (full greedy generation; layer windows early 0–9 / mid 10–19 / late 20–31 **for
the 32-layer Llama-3.1-8B**; the cross-model replications in §4.3 use the same thirds rule scaled to each
model's depth, so their window boundaries differ):
- **Necessity** — patch the codeword's representation toward its Neutral counterpart during DS generation;
  controls: identity patch (no-op) and norm-matched random patch.
- **Sufficiency** — inject the DS-state vs the Direct-state into a bare Neutral prompt (no demonstrations).
- **Timing** — inject the raw harmful concept at each window and read the refusal rate by depth.

Paired-bootstrap CIs (10k resamples, fixed seed); effects conditioned on the baseline reproducing the
required label. Models run in bf16 on L40S GPUs.

---

## 4. Results

### 4.1 A real behavioral jailbreak
On the curated Llama screen, **37/40 bases are eligible**, and **42 of the 240 screened DS generations are
clean jailbreak successes** — Direct refused, Neutral benign, DS malicious — spanning **18 bases and 14
concepts**, i.e. roughly 0.18–0.24 per generation. (The strict three-way cut behind "42" is tighter than the
file's own `DS_MALICIOUS` = 46 / `MALICIOUS` = 52.) With correct judging the hijack is a genuine behavioral
attack, if a low-rate one — the originating paper's "behavioral null" was a judging artifact.

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
| early (0–9)  | **0.87** | 0.12 |
| mid (10–19)  | 0.25 | **0.49** |
| late (20–31) | **0.02** | 0.09 |

Paired refusal gradient **early − late = +0.846 [+0.787, +0.899]** (n=169); early−mid +0.631; mid−late
+0.214 — all significant. Early harmful meaning is exposed to the refusal machinery and refused; late
harmful meaning is not refused. **Read the second column before reading the first.** Harmful output peaks at
**mid** (0.49), not late (0.09, with 89% of late generations benign) — so the near-zero late refusal rate
partly reflects the injection having little behavioral effect at all, not only its escaping a check. The
depth-dependent refusal effect is therefore *consistent with* a time-of-check account, but injecting the raw
concept at depth is not the same manipulation as delaying the emergence of a *hijacked* meaning, and we have
not performed the latter. We report the gradient; we do not claim it is the demonstrated mechanism of
Doublespeak.

**Architecture-generality.** The full monotone early→mid→late gradient is measured on Llama only. The
**early-vs-late difference** reproduces on two further architectures — Llama **+0.846** [+0.787,+0.899]
(n=169), Qwen3 **+0.854** [+0.732,+0.951] (n=41), Phi-4-mini **+0.250** [+0.056,+0.444] (n=36); the Qwen3
and Phi-4 runs used the early and late windows only, scaled to each model's depth. The **behavioral
jailbreak additionally reproduces on a fourth model**, DeepSeek-R1-Distill-8B: 27/40 eligible, **37**
`DS_MALICIOUS` conditions on eligible bases across 16 bases. (An unrestricted count over all 240 conditions
gives 66; and DeepSeek's Direct arm is judged malicious rather than refused, so the strict three-way cut
behind Llama's "42" yields 0 there — the two figures are not comparable.)

### 4.4 The mechanism predicts, and dissociates from decoding
A "benign-early / harmful-late" temporal signature carries **modest correlational** predictive signal for
held-out jailbreak success: held-out-**concept** AUC **0.668 ± 0.089** (GroupKFold, 46 positives of 240),
5-fold CV 0.732. The ±0.089 is a fold standard deviation, not a confidence interval — a two-sd band reaches
0.49, i.e. chance — and we run no test against 0.5. The load-bearing feature is *early-benign* alignment
(late alignment alone is inert, AUC 0.502). This is an association, not further causal evidence.

However, **decoding-sufficiency and behavioral-sufficiency dissociate.** Patchscopes predicts DS-injection >
Direct-injection; behaviorally we find the opposite. Direct is far more potent at **mid** (0.492 vs 0.098; DS−Direct =
**−0.393** [−0.470, −0.311], n=183). The same sign holds at **late** between two near-floor rates (0.029 vs
0.092; −0.064 [−0.116, −0.012], n=173) and at **early** with a CI touching zero (−0.061 [−0.123, 0.000],
n=179). On Qwen3 the early window in fact runs the *other* way (DS−Direct = **+0.190** [+0.071, +0.310],
n=42), so the dissociation is mid-specific rather than uniform. The hijacked state decodes as the
concept but is *context-dependent* — it loses behavioral force when transplanted out of its demonstrations.
**Interpretability-based decoding-sufficiency does not predict, and here inverts, behavioral sufficiency** —
a methodological caution.

### 4.5 The attack resisted distillation into a suffix (bounded negative)
Can the temporal objective (make late reps harmful, early benign) be compiled into an adversarial suffix?
We built a mixed reference cache (early layers ← benign reps, late ← harmful reps) and optimized a 16-token
GCG suffix on Qwen3 to minimize distance to it. **The objective resisted this optimizer:** the temporal
`repr_loss` showed no sustained decrease in any of three selection strategies, including one that freely
sacrificed the task target — the largest transient improvement was 0.017 (lex-tight, 0.480 → 0.463), and the
final value exceeded the initial in two of the three runs. Behaviorally the temporal suffix **backfires** —
held-out ASR 0 (equal to baseline GCG), while refusal rises to **0.615 (8 of 13 held-out bases)** versus 1 of
13 for baseline GCG and 0 of 13 with no suffix; a clear directional increase, but on n=13 with no interval.
This is one optimizer (GCG), one model (Qwen3-14B), 16 tokens, 200 steps, one placement, 25 training bases.
It bounds rather than forecloses suffix distillation: **we did not find** a transferable trigger, and on this
evidence the hijack's power appears to reside in the in-context demonstrations.

---

## 5. Discussion

The candidate account is temporal: safety training may install a *check* that reads early-layer meaning,
so that a prompt whose harmful meaning is delayed past that check is complied with. If it holds, this would
(a) recast Doublespeak's late emergence as the *mechanism* of evasion rather than an incidental property,
(b) explain the correlational early-benign signature's
predictive value, and (c) bound the attack (a late meaning must be *installed by context*,
not appended as a suffix, or it is re-checked/refused). The decoding-vs-behavior dissociation warns that
representation-decoding evidence should not be read as behavioral evidence.

**Defensive implication.** If refusal is time-of-check, robustness may require *time-of-use* checking —
re-evaluating harmfulness at the layers/positions where meaning actually resolves, not only early. The
reasoning-model result (Phi-4/DeepSeek) is suggestive: chain-of-thought, which re-examines meaning at any
depth, compresses (but does not erase) the timing gradient.

---

## 6. Limitations
- Necessity's specificity over a *random* patch is modest (+0.18, CI crosses 0) — robust but not
  significant; likewise a codeword-selection variant gives a directional but NS **+0.092 [−0.037, +0.225]**
  gain in *jailbreak rate from temporal vs random codeword selection* (n=40 bases,
  `outputs/features_cw6/codeword_selection.json`) — note this is a selection effect, not an ASR gain from an
  optimized attack. Larger N is the lever.
- **The central claim is an inference, not a demonstrated chain.** The timing experiment injects the *raw*
  concept at varying depth; nothing in this work manipulates the depth at which the *hijacked* meaning
  emerges. The step from "refusal is depth-sensitive" to "Doublespeak evades refusal by delaying meaning"
  is therefore unproven.
- **Provenance.** `outputs/` and `data/behavioral_benchmark/` are gitignored, and the numbers in §4.2, the
  cross-model rows of §4.3, and §6's codeword result are recomputed from raw logs with no committed summary
  artefact. See `RESULTS_FREEZE_AUDIT.md`.
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
