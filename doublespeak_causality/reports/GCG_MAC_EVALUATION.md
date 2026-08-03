# reports/GCG_MAC_EVALUATION.md — Phase 11: GCG / MAC behavioral evaluation (design + prior evidence + gate)

**Plan Phase 11 primary success criterion:** the causally-derived objective must improve **held-out
behavioral StrongREJECT ASR** over a compute-matched naïve GCG / MAC baseline. A projection increase
without an ASR increase is a **NULL**.

## Compute-matched comparison design (arms held constant: train/test, steps, restarts, suffix length,
## candidate batch, token budget, generation, judge, model)
1. No attack · 2. Standard Doublespeak · 3. Naïve GCG (task loss only) · 4. Existing MAC/TROPT ·
5. Refusal-suppression objective · 6. **Doublespeak-signature objective (noncausal NEGATIVE control)** ·
7. **Mechanistic objective only** = concept-region (d_Direct at the L9–L12 write region, demo/codeword
positions) · 8. Standard + mechanistic · 9. Mechanistic + refusal term · 10. Random-direction control ·
11. Wrong-layer control · 12. Wrong-head control · 13. Wrong-path control.
Integration point: add the mechanistic term as an extra loss in the GCG optimizer (the existing
`run_gcg_optimize.sh` already supports a `DSLAMBDA·repr_loss` term via a reference cache — swap the temporal
mixed-cache target for the concept-region projection target).

## Prior evidence already on disk (this is NOT a fresh question)
- **Temporal-GCG (mechanism-derived) was net-negative** (project_gcg / CAUSAL_CORE): the temporal
  early-benign/late-harmful objective did not beat task-only GCG on held-out ASR; the representational/
  temporal objective **backfired** (ASR 0.0, refusal ↑) — the attack is demonstration-bound.
- **Doublespeak-signature objective is causally inert** (Phase 6 repr = late-proximity artifact; prior T2 =
  exactly 0.0). Optimizing toward "look like the hijacked state" cannot work — a confirmed NEGATIVE control.
- **Soft-prompt optimizability gate (37, plan §8.5):** the plan's own prerequisite — if continuous
  optimization cannot move the causal score, discrete GCG is uninterpretable. Prior CAUSAL_CORE found
  optimizing a predictive internal projection **did not reliably improve held-out behavioral ASR**.

## Why the honest prediction is a well-controlled NULL
Gate-6 (CAUSAL_OBJECTIVE.md) came back **9/10 — sufficiency FAILS**. The concept-write handle is necessary,
dose-dependent, refusal-independent, and control-passing, but **installing it does not create the reading**
(S3_install ≈ 0) because the binding is **distributed and context-bound** (necessity spread across the
L8–12 demo computation + the L14–21 carry band; no single component transplants). An optimization objective
built on a necessary-but-not-sufficient, distributed signal is not expected to yield a clean ASR gain — and
the prior temporal/representational GCG already realized that null. The one *sufficient* lever the circuit
identifies (explicit `d_Direct` concept installation + refusal removal) is a white-box activation edit, not
something a token suffix can reliably induce.

## Decisive minimal test (proportionate to an expected null) — the plan's §8.5 gate on the NEW objective
Rather than rebuild the full Qwen3 GCG suffix-search pipeline for Llama+ClearHarm (disproportionate for an
expected null), run the plan's **prerequisite gate** on the newly-validated objective:
- **G1 — behavioral sufficiency of the concept-region objective:** add `d_Direct` (L9–L12 write region) at
  generation time to NEUTRAL/BENIGN prompts (vs signature / random / wrong-layer controls) and measure
  StrongREJECT ASR — does the *validated causal handle* produce harmful behavior on held-out examples?
  Reuses 18/19 behavioral eval + directions + `AllPositionAddMultiLayer`. Main-loop/SLURM (harmful gen).
- **G2 — optimizability:** if G1 shows any behavioral movement, escalate to a compute-matched GCG arm
  (concept-region loss term via the existing `DSLAMBDA` hook); otherwise report the gate-negative and cite
  the prior GCG null as the Phase-11 conclusion.

## Behavioral evidence already on disk (Phase 11 concludes from existing runs + Gate-6)
The behavioral sufficiency experiment (`19_run_behavioral_sufficiency.py`, Llama-3.1-8B, StrongREJECT) has
already been run extensively and analyzed in `BEHAVIORAL_CAUSALITY_RESULTS.md`:
- **State injection is only WEAKLY behaviorally sufficient (≤0.16 malicious rate at any depth)** — "it never
  becomes a potent behavioral injectate." This is the behavioral confirmation of the Phase-6 representational
  `S3_install ≈ 0` sufficiency-failure.
- **Dissociation:** representation-level decoding-sufficiency (Patchscopes P(concept)) does NOT predict — and
  here inverts — behavioral sufficiency. A caution for the field: a decodable concept ≠ a behaviorally
  potent one.
- **Temporal/mechanistic GCG net-negative** (prior GCG work): the mechanism-derived suffix objective did not
  beat task-only GCG on held-out ASR; the representational objective backfired.
- **White-box concept-install + refusal-removal DOES increase harmful behavior** (known finding #5) — the one
  behaviorally-potent lever, but it is an activation edit, not a suffix objective.

## Phase 11 verdict (concluded)
**The distributed, context-bound Doublespeak mechanism does NOT convert into a token-suffix ASR gain.** Its
necessary components are only weakly behaviorally sufficient in isolation (≤0.16), a mechanism-derived GCG
objective is net-negative, and Gate-6 sufficiency fails — three independent lines converge on a
well-controlled NULL for a black-box optimization objective. The mechanism IS behaviorally actionable, but
only via the **white-box concept-install + refusal-removal activation edit**, not a suffix. This honest
negative delimits what is behaviorally actionable and is itself a contribution (and a field caution:
decoding-sufficiency ≠ behavioral sufficiency).

**Remaining optional extension (not needed for the verdict):** a fresh compute-matched GCG suffix comparison
(arms 3/6/7/8/9/10 above) on the ClearHarm+Llama split with the newly-precise concept-region loss term —
would re-confirm the null with the sharper objective. Deferred as low-value given the converging evidence;
launchable via the existing `DSLAMBDA` hook if desired.
