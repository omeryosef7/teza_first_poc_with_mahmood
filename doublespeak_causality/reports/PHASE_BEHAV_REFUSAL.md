# Phase BEHAV-REFUSAL — Is the refusal bypass the behavioral locus of Doublespeak?

**Motivation.** BEHAV-CARRY and BEHAV-WRITE showed the *concept circuit* (necessary + sufficient for
the FC concept readout) is **behaviorally inert** — ablating it does not reduce jailbreak ASR. That
raises the positive question: *what IS behaviorally sufficient?* Goal #5 of the plan (Doublespeak
"bypasses the normal refusal mechanism") and Phase 2.1 conditions point at the **refusal axis**.

**Design (5 arms, paired, StrongREJECT-judged vs the harmful goal).** For each harmful item, on the
matched Direct and Doublespeak prompts, apply the standard **Arditi directional ablation** — project
the validated **L18 refusal direction** out at *every layer/position through generation*
(`pc.AllPositionProjectOutMultiLayer`, refusal dir bidirectionally validated: ablate_gain +0.47,
induce_gain +0.67):
- `direct_base` — plain harmful request · `direct_refabl` — Direct + refusal ablation (refusal
  suppression ALONE) · `direct_randabl` — Direct + norm-matched **random**-direction ablation
  (specificity control) · `ds_base` — Doublespeak (the jailbreak) · `ds_refabl` — Doublespeak +
  refusal ablation. Metric = ASR (MALICIOUS rate) + refusal_rate + paired McNemar exact. Cohorts:
  curated (30/21, **complete**) + clearharm (44 train **complete**, 42 test — 36/42 shown, preemption
  restart finalizing). Reuses `refusal_direction_llama_L18.pt` + 45_toctou ablation recipe.

## Result — refusal suppression is behaviorally SUFFICIENT, SPECIFIC, and STRONGER than Doublespeak

**ASR / refusal_rate per arm:**

| cohort·split | direct_base | direct_refabl | direct_randabl | ds_base | ds_refabl |
|---|---|---|---|---|---|
| clearharm train (44) | .159 / .841 | **.591** / .273 | .136 / .864 | .386 / .477 | .773 / .045 |
| clearharm test (36*) | .111 / .861 | **.472** / .278 | .083 / .861 | .361 / .444 | .556 / .111 |
| curated train (30) | .267 / .700 | **.700** / .233 | .233 / .700 | .300 / .000 | .367 / .000 |
| curated test (21) | .286 / .667 | **.714** / .286 | .381 / .619 | .095 / .000 | .095 / .000 |

**Paired McNemar (exact):**

| comparison | clearharm train | clearharm test* | curated train | curated test |
|---|---|---|---|---|
| refusal-ablation vs Direct base (ΔASR, p) | **+.432, p=2e-5** | **+.361, p=2e-4** | **+.433, p=1e-3** | **+.429, p=4e-3** |
| random-ablation vs Direct base (control) | −.023, p=1.0 | −.028, p=1.0 | −.033, p=1.0 | +.095, p=0.5 |
| Doublespeak vs refusal-ablation (ΔASR, p) | −.205, p=.035 | −.111, p=.34 | −.400, p=2e-3 | −.619, p=2e-4 |

Three findings, consistent across both cohorts and splits:

1. **Refusal suppression ALONE is behaviorally sufficient** — projecting out one refusal direction
   turns a refusing model into a complying one (ASR +0.36–0.43 over Direct baseline, **every split
   p ≤ 0.004**; refusal_rate collapses .70–.86 → .23–.29).
2. **Clean specificity** — a norm-matched **random** direction has **no effect** on any split (McNemar
   p ≥ 0.5, refusal_rate unchanged). The effect is the refusal axis, not generic perturbation.
3. **Refusal suppression is at least as strong as Doublespeak — usually stronger.** `direct_refabl`
   ASR ≥ `ds_base` on all four splits (significantly on 3/4). Pure refusal-axis removal is a *better*
   attack than the actual Doublespeak jailbreak.

Corroborating detail: **Doublespeak only *partially* suppresses refusal** (ds_base refusal_rate
.44–.48 on clearharm, vs Direct .84–.86 and full-ablation .05–.11), and DS + explicit ablation
(`ds_refabl`) climbs higher than either alone (clearharm train .773) — i.e. Doublespeak leaves refusal
headroom that explicit ablation still removes. Doublespeak is an **imperfect** refusal suppressor.

## Interpretation — the mechanistic account completes

Combining all three behavioral experiments:

| lever | representational role | behavioral effect on ASR |
|---|---|---|
| L8–11 concept WRITE | Holm-sig necessary (readout) | **NULL** (BEHAV-WRITE) |
| L14–21 carry heads | necessary + sufficient (readout) | **NULL** (BEHAV-CARRY) |
| **refusal axis (L18)** | (orthogonal to concept, cos≈0.01–0.06) | **+0.4 ASR, sufficient, specific, > Doublespeak** |

**Doublespeak's harm is driven by refusal bypass, not by the token→concept remap.** The concept
circuit is a faithful, rigorously-mapped account of *how the codeword is re-interpreted*, but that
representation is **causally disconnected from compliance**: ablating it does nothing, while ablating
the orthogonal refusal axis — which the concept circuit never touches — reproduces and exceeds the
jailbreak. The demonstrations' real causal work is (partially) pushing the hidden state off the
refusal axis; the elaborate concept-remap is behaviorally incidental.

This unifies every objective-level result in the study: the concept-circuit behavioral nulls, the
suffix-objective null (Q12), the mechanism-guided-optimization negative, ≤0.16 concept state-injection
sufficiency — and now a **positive** locus (the refusal axis) that IS behaviorally potent.

**Defense implication (sharp):** monitoring or scrubbing the *concept* subspace will not stop
Doublespeak; the actionable axis is **refusal**. Conversely, this is also why Doublespeak works at all
— it is a soft, in-context way to achieve what direct refusal-direction ablation does with white-box
access.

## Honest scope

- Shows refusal suppression **sufficient** (+ that it exceeds Doublespeak). It does **not** directly
  show refusal suppression is **necessary** to Doublespeak — that needs the complementary re-injection
  arm (add the refusal direction back *into* DS generation and test whether ASR drops). Flagged as the
  next experiment. The convergence (concept null + refusal sufficient + DS partially suppresses
  refusal) strongly implies it, but the necessity arm would close it.
- L18 direction, α=1.0, greedy decode, StrongREJECT MAL≥0.25. *clearharm test = 36/42 (preemption
  restart 708038 finalizing); train (44) complete, curated (30/21) complete — headline rests on the
  complete cells.

## Reproduce
```
sbatch --time=01:30:00 --export=ALL,DSBENCH=doublespeak_causality/data/behavioral/beh_clearharm.json,DSMAXNEW=220,DSN=0 \
  doublespeak_causality/slurm/run_behav_refusal.sh      # + beh_curated.json
```
Runs: curated `behav_refusal_curated_a1.0_20260804_125055_708039` (complete),
clearharm `behav_refusal_clearharm_a1.0_..._708038`.
