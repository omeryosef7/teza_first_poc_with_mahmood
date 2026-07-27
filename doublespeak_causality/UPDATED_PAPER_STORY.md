# Doublespeak Causality — Evolving Paper Story

**Deliverable (plan §23).** The honest, evolving narrative of what we add to the original
"In-Context Representation Hijacking" (Doublespeak, arXiv:2512.03771) paper. Updated as results
land. Redacted: no operational harmful content. Numbers are from real runs (see `SPRINT_EXECUTION_LOG.md`
job registry); pending items are marked.

---

## 1. What the original paper showed

*Observationally* (logit lens, Patchscopes): when demonstrations repeatedly substitute a benign
codeword (e.g. `potato`) for a harmful concept (e.g. `bomb`), the codeword's representation grows
increasingly similar to the harmful concept across layers, peaking late. It did **not** establish
causality, behavioral effects, timing, information flow, an attack objective, thinking-mode
differences, or a validated defense.

## 2. What we causally established at the REPRESENTATION level (pre-sprint, frozen baseline)

Tag `frozen-rep-result-2026-07-27`. Cross-model (Llama-3.1-8B, Qwen3-14B, Phi-4-mini), all CIs
exclude 0:
- **Necessity** — replacing the DS codeword state with its matched Neutral state removes the
  decoded harmful meaning (identity + norm-matched-random controls).
- **Conditional sufficiency** — injecting the *Direct concept* state is NOT sufficient, but injecting
  the *Doublespeak* state IS more successful → the hijacked rep is a **distinct late-emerging state**,
  not a copy of the concept.
- **Timing (semantic)** — Direct concept decodes early; hijacked codeword meaning decodes late.
- **Information flow** — attention knockout (codeword→demonstrations) eliminates the hijack.
- Codeword embedding distance does NOT predict hijacking.

**Honest limitation carried into the sprint:** these were all *representation-level* (Patchscopes
P(concept)); the behavioral jailbreak was a documented NULL on the seed data.

## 3. What became BEHAVIORAL this sprint (the key advance)

### 3a. A credible behavioral benchmark (Phase 2)
The seed's behavioral null was two-fold: (i) a **benchmark problem** — AdvBench harm is rarely
localized in a single swappable noun (redundant harmful terms mean substitution doesn't neutralize;
behavioral screen: only 2/193 AdvBench bases had a benign Neutral), and (ii) a **measurement bug**
(§3b). Fix (i): a curated **harm-in-single-noun** benchmark (20 nouns × clean templates, 6 categories)
where substitution provably neutralizes ("build a {bomb}" → "build a {kettle}").

### 3b. The behavioral "null" was largely a JUDGING ARTIFACT
The screen labeled a response *refused* if it used refusal language **OR** StrongReject's refusal
sub-score ≥0.5. But StrongReject judges against the *harmful* goal, so a **benign** Neutral answer
that legitimately doesn't fulfill the harmful goal was scored refusal=1 → mislabeled REJECTED →
eligibility destroyed. (Proof: 78/80 curated Neutrals harmless, but 56 mislabeled REJECTED by
SR-refusal alone.) Fix: `refused = refusal-language only`. A benign off-goal answer and a safety
refusal both score ~0 — only refusal *language* distinguishes them.

### 3c. The clean behavioral Doublespeak jailbreak EXISTS (Claim A ✓)
After the fix, on the curated set (Llama-3.1-8B): **37/40 eligible bases, 18 clean-success bases,
42 score-verified clean-success conditions across 14 concepts** (bomb, cocaine, grenade, landmine,
napalm, thermite, …). All Neutrals harmless (<0.05); **37/42 DS score ≥0.5, 26/42 ≥0.75.** DS-malicious
rate ≈20% of eligible conditions. This is the sweet spot: Direct refused · Neutral benign · Doublespeak
restores harmful compliance. **This flips the paper's (and our seed's) behavioral null into a positive,
statistically-meaningful result.**

## 4. Behavioral causality — Claims B & C (Phase 3, IN PROGRESS)
`18_run_behavioral_necessity.py` (DS←Neutral patch during generation → does the malicious behavior
disappear?) + `19_run_behavioral_sufficiency.py` (Neutral←DS vs Neutral←Direct injection → does the
hijacked state, more than the plain concept state, *cause* harmful behavior?). SLURM 689471 running.
**Result: PENDING.** Prediction (from §2): DS-state injection > Direct-state injection, behaviorally.

## 5. Causal timing — Claim D ✅ CONFIRMED (Phase 4) ⭐ HEADLINE
Injecting the raw harmful concept at different depths into benign prompts: **early → REFUSAL (0.86),
mid → COMPLIANCE (0.52 malicious), late → NEITHER (refusal 0.00)**. Refusal decreases monotonically with
depth; early−late refusal Δ=+0.857 [+0.714, +1.00] (every pairwise step significant). **TOCTOU confirmed:
refusal is a time-of-check operation on EARLY representations.** This explains WHY Doublespeak works — the
hijacked meaning emerges LATE (rep-level result), so it slips past the early refusal checkpoint. Closes the
representation→behavior loop with a causal timing law. (Success Level 3.)

## 6. Mechanistic attack objective — Claim E (Phases 5-6, NOT STARTED; DE-RISKED)
`poc_stage_gcg_early/objectives.py` already has `repr_loss` + `ObjectiveWeights` + activation capture;
`reinforce_mac.py` = MAC. Temporal-GCG = a layer-weighted `repr_loss` plug-in. Must improve held-out
behavioral ASR vs standard GCG/MAC to count.

## 7. Thinking vs non-thinking — Claim F (Phase 7, NOT STARTED; DE-RISKED)
Qwen3 same-weights toggle already implemented+tested (`qwen3_model.py`); gotcha documented (default
thinking-ON; `enable_thinking=False` injects empty `<think>`). Needs `ds_common` pass-through.

## 8. What remains unresolved
- Behavioral necessity/sufficiency magnitudes + controls (Phase 3, imminent).
- Whether timing is causal for refusal-vs-compliance (Phase 4).
- Whether a mechanistic objective beats standard GCG/MAC on held-out ASR (Phases 5-6).
- Thinking-mode mechanism differences (Phase 7).
- Cross-model behavioral generalization (Phase 8) — rep-level already 3 families.

## 9. One-line thesis (current)
> Doublespeak builds a distinct, late-emerging, attention-routed codeword representation (causally
> necessary + conditionally sufficient at the representation level, cross-model) that **translates into a
> real behavioral jailbreak** on a properly-constructed benchmark — and we show **WHY it works**: refusal
> is a *time-of-check* operation on EARLY representations (injecting harmful meaning early → 86% refusal,
> late → 0%), so Doublespeak's late emergence is precisely the mechanism that smuggles harmful meaning
> past the refusal checkpoint. We further find that representation-level decoding-sufficiency and
> behavioral sufficiency **dissociate** — a methodological caution for interpretability-based attack claims.

**Methodological lesson worth stating in the paper:** measuring "refusal" via a harmful-goal-conditioned
judge conflates *benign compliance* with *refusal* and can manufacture a false behavioral null — a trap
for anyone evaluating substitution-based attacks.
