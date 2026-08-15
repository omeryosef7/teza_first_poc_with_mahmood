# PHASE 9 — Mechanism-derived attack objective: DECISION (by-design negative)

Plan §13 ("ONLY THEN test a new mechanism-derived attack objective"). This report records
why Phase 9 is **deliberately not run** — it is a decision-tree outcome, not an omission.

## The plan's own gating rule

§13 is explicitly conditional: *"IF a new causal state emerges: exact-state objective."*
The premise for building a Bombness-derived attack objective is that the Bombness state is
**behaviorally causal** — otherwise optimizing an input to induce it cannot, by
construction, change behavior. §13.1 only fires when Phases 3–4 surface a causal state.

## The premise is falsified — Story A holds

Every causal test in this sprint found Bombness **behaviorally epiphenomenal**:

| test | result | source |
| --- | --- | --- |
| necessity (ablate v_bomb) | ΔASR −0.05 (n.s.), manip check passed | D2 / 757931 |
| sufficiency (add v_bomb) | ΔASR +0.05 (n.s.) | §8.5 / 757992 |
| 2×2 Bombness main effect | +0.00 [−0.07, +0.07] | 757943 |
| per-example component patching | +0.05 both ways, = random (Phase 5) | 758162/3 |
| cross-family (Phi, Qwen) | epiphenomenal on all 3 families | §9 |
| second corpus (AdvBench) | +0.06 (n.s.), = random | 758657 |

The refusal axis, not Bombness, is the behavioral lever (ΔASR +0.24 → +0.36; +0.295 p=0.0 on
AdvBench). So **no new causal state emerged**; the §13 precondition is not met.

## Why running it anyway is a predicted (and already-observed) negative

Optimizing a GCG/soft-prompt objective to drive an **epiphenomenal** direction is predicted
to be net-neutral-to-negative on ASR: you would spend attack budget inducing a
representation that does not move behavior. This is not merely predicted — the broader
attack-objective work in this repository already established it empirically:

- The GCG/Gate-7 program found mechanism-derived (refusal-direction / concept) attack
  objectives **net-negative** vs a neutral suffix (GCG July master log; refusal-dir
  objective net-negative; concept objectives not decisive).
- The asymmetry thread (§D3, this sprint) shows the activation-space result that *does* move
  refusal is largely a **scope** effect unreachable by a one-position/one-layer token
  objective — so even the causal (refusal) axis is not productively token-optimizable.

Running a Bombness objective would therefore be optimizing the *weaker* (epiphenomenal)
of the two axes, under the *harder* (input-space, scope-limited) medium — a CI-backed
negative before a single GPU-hour is spent.

## Decision

**Phase 9 is recorded NOT RUN, by design (§13 decision tree → Story A → do not optimize
Bombness).** This is the plan's intended branch, and it is the honest, budget-respecting
outcome: the sprint's job was to determine *whether* a mechanism-derived objective is
warranted, and the answer is no. If a future experiment surfaces a genuinely causal,
input-reachable state (Story B), §13.1–13.5 (exact-state objective, candidate selection on
the objective, MAC/TROPT) become live; the harness for that is inherited and ready.
