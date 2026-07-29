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

## 4. Behavioral causality — Claims B & C (Phase 3) ✅ COMPLETE
`18_run_behavioral_necessity.py` (DS←Neutral patch during generation) + `19_run_behavioral_sufficiency.py`
(Neutral←DS vs Neutral←Direct injection). Clean per-condition CIs (audit-verified, deterministic):
- **Necessity ✅ (Claim B):** patching the DS codeword state to its Neutral counterpart flips malicious→benign,
  **early-layer specific** (early Δ=0.455 [0.303, 0.636]); specificity over a random patch is modest (necessity−random
  +0.182 [−0.030, +0.394], underpowered — honest caveat).
- **Sufficiency ✅ but DISSOCIATES from the rep-level prediction (Claim C):** the rep-level Patchscopes
  prediction was DS-injection > Direct-injection. **Behaviorally it INVERTS: Direct ≫ DS** — the raw concept
  is the more potent injectate at mid (DS−Direct −0.393 [−0.470, −0.311], n=183, 37 bases) AND late (−0.064
  [−0.116, −0.012], n=173); at early the dissociation is weak/borderline. The hijacked DS state is a *context-dependent*
  state that loses behavioral force when transplanted out of its demonstrations — a **methodological caution:
  Patchscopes decoding-sufficiency does not predict (here inverts) behavioral sufficiency.**

## 5. Causal timing — Claim D ✅ CONFIRMED (Phase 4) ⭐ HEADLINE
Injecting the raw harmful concept at different depths into benign prompts: **early → REFUSAL (0.87),
mid → COMPLIANCE (0.52 malicious), late → NEITHER (refusal 0.00)**. Refusal decreases monotonically with
depth; early−late refusal Δ=+0.846 [+0.787, +0.899], n=169 (37 bases; reproducible per-condition via
`analyze_behavioral_causality.py --timing-dir`; every pairwise step significant). **TOCTOU confirmed:
refusal is a time-of-check operation on EARLY representations.** This explains WHY Doublespeak works — the
hijacked meaning emerges LATE (rep-level result), so it slips past the early refusal checkpoint. Closes the
representation→behavior loop with a causal timing law. (Success Level 3.)

## 6. Mechanistic attack objective — Claim E (Phase 5-6) — PARTIAL
**Level 4 ✅:** the "benign-early / harmful-late" signature PREDICTS held-out jailbreak (held-out-concept
AUC 0.668, CV 0.73); the predictive component is EARLY-benign alignment (late_align alone inert) —
cohering with the TOCTOU law. **Level 5 🔶 (directional, not significant):** using the objective to SELECT
codewords (min early-align) raises jailbreak rate 0.30 vs 0.208 random (+0.092 [−0.037, +0.225], n=40) —
positive but underpowered; consistent with the moderate objective. Full suffix-GCG designed
(`GCG_MAC_COMPARISON.md`: temporal = mixed early-benign/late-harmful `repr_loss`), not yet run.

## 7. Thinking vs non-thinking — Claim F (Phase 7) — PARTIAL (Level 6)
Within-model on Qwen3 (same weights, n=90): thinking does NOT amplify success (DS mal 0.22 vs 0.24, NS) but
INTRODUCES some DS refusals (0.00→0.067, sig — reasoning catches some hijacks) and STEEPENS the dose-response
(DS-mal by demos 0.14/0.23/0.36 vs 0.09/0.16/0.16). A real but modest within-model difference; no causal
thinking-time intervention yet. (`THINKING_VS_NONTHINKING.md`.)

## 7b. Cross-model generalization ⭐
The **behavioral jailbreak** and the **TOCTOU causal-timing law** reproduce on **all three architectures**,
and the timing gradient is **significant on all three** (clean per-condition, reproducible):
early−late refusal Δ = Llama **+0.846 [+0.787, +0.899]** (n=169, 37 bases) · Qwen3 **+0.854 [+0.732, +0.951]** (n=41) ·
Phi-4-mini **+0.250 [+0.056, +0.444]** (n=36) — Phi-4's is smaller (a reasoning model re-examines meaning
at any depth) but its CI now excludes 0 on the full n. Together with the rep-level results (also
cross-Llama/Qwen3/Phi-4), the causal story is **architecture-general at every level**.

## 8. What remains unresolved
- **Level 5 clean:** a *significant* attack-ASR gain from the temporal objective — needs the full
  suffix-GCG (designed) or larger-N codeword selection. Currently directional only.
- **Level 6 clean:** a causal thinking-time intervention (remove/add the harmful direction during early vs
  late thinking; does refusal onset shift?) — would connect thinking to the TOCTOU law. Behavioral
  comparison done; intervention not.
- Necessity specificity-over-random is underpowered (n=20) — larger N.
- Representation-level thinking trajectories (where in the CoT the hijack forms).
- Phi-4 / Llama-3.3-70B behavioral + timing replication (rep-level already 3 families).

## 10. Success scorecard (plan §24, honest)
**Level 1 ✅** benchmark · **Level 2 ✅** behavioral necessity (early) · **Level 3 ✅ ⭐** causal timing
(TOCTOU) — architecture-general · **Level 4 ✅** predictive objective (AUC 0.67) · **Level 5 🔶** directional
attack gain (NS) · **Level 6 🔶** modest thinking difference. Plus: cross-model behavioral reproduction, a
fully bug-audited/re-validated frozen baseline, and the rep↔behavioral **dissociation** methodological result.

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
