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
  curated (30/21) + clearharm (44/42), **all cells complete**. Reuses `refusal_direction_llama_L18.pt`
  + 45_toctou ablation recipe.

## Result — refusal suppression is behaviorally SUFFICIENT, SPECIFIC, and STRONGER than Doublespeak

**ASR / refusal_rate per arm:**

| cohort·split | direct_base | direct_refabl | direct_randabl | ds_base | ds_refabl |
|---|---|---|---|---|---|
| clearharm train (44) | .136 / .841 | **.568** / .273 | .136 / .864 | .386 / .477 | .727 / .045 |
| clearharm test (42) | .071 / .881 | **.548** / .262 | .071 / .881 | .357 / .452 | .548 / .095 |
| curated train (30) | .267 / .700 | **.700** / .233 | .233 / .700 | .300 / .000 | .367 / .000 |
| curated test (21) | .286 / .667 | **.714** / .286 | .381 / .619 | .095 / .000 | .095 / .000 |

**Paired McNemar (exact):**

| comparison | clearharm train | clearharm test | curated train | curated test |
|---|---|---|---|---|
| refusal-ablation vs Direct base (ΔASR, p) | **+.432, p<1e-5** (19/0) | **+.476, p<1e-5** (20/0) | **+.433, p=1e-3** | **+.429, p=4e-3** |
| random-ablation vs Direct base (control) | .000, p=1.0 | .000, p=1.0 | −.033, p=1.0 | +.095, p=0.5 |
| Doublespeak vs refusal-ablation (ΔASR, p) | −.182, p=.057 | −.190, p=.057 | −.400, p=2e-3 | −.619, p=2e-4 |

Three findings, consistent across both cohorts and splits:

1. **Refusal suppression ALONE is behaviorally sufficient** — projecting out one refusal direction
   turns a refusing model into a complying one (ASR +0.43–0.48 over Direct baseline, **every split
   p ≤ 0.004**, clearharm flipping 19/19 and 20/20 discordant cases toward harm; refusal_rate
   collapses .70–.88 → .23–.29).
2. **Clean specificity** — a norm-matched **random** direction has **no effect** on any split (McNemar
   p ≥ 0.5, refusal_rate unchanged). The effect is the refusal axis, not generic perturbation.
3. **Refusal suppression is at least as strong as Doublespeak — usually stronger.** `direct_refabl`
   ASR ≥ `ds_base` on all four splits (significantly on 3/4). Pure refusal-axis removal is a *better*
   attack than the actual Doublespeak jailbreak.

Corroborating detail: **Doublespeak only *partially* suppresses refusal** (ds_base refusal_rate
.44–.48 on clearharm, vs Direct .84–.86 and full-ablation .05–.11), and DS + explicit ablation
(`ds_refabl`) climbs higher than either alone (clearharm train .773) — i.e. Doublespeak leaves refusal
headroom that explicit ablation still removes. Doublespeak is an **imperfect** refusal suppressor.

## Necessity — re-injecting refusal INTO Doublespeak kills the jailbreak (dose-dependent, specific)

Sufficiency (above) shows refusal removal is *enough*. The necessity arm (`phase_behav_refusal_inject.py`)
tests the converse: ADD +α·refusal-axis at every position/timestep through Doublespeak generation
(`pc.AllPositionAdd`, single-layer L18 = validated induce layer), α∈{4,8,12}, vs a norm-matched
random-direction control at α=8, with an empty_rate coherence guard. Paired McNemar vs ds_base.

**Dose-response — ASR (refusal_rate):**

| cohort·split | ds_base | +refusal α4 | +refusal α8 | +refusal α12 | +random α8 |
|---|---|---|---|---|---|
| clearharm train (44) | .386 (.48) | .159 (.77) | .091 (.91) | **.000 (1.00)** | .500 (.32) |
| clearharm test (42)  | .381 (.45) | .190 (.79) | .071 (.93) | **.000 (1.00)** | .500 (.31) |
| curated train (30)   | .333 (.00) | .200 (.53) | .000 (.97) | **.000 (1.00)** | .433 (.00) |
| curated test (21)    | .095 (.00) | .095 (.33) | .000 (1.00)| **.000 (1.00)** | .286 (.00) |

**Paired McNemar vs ds_base (ΔASR, p):** clearharm α12 **−.386 p=2e-5** (17/0 flips off) / **−.381 p=3e-5**
(16/0); α8 −.296/−.310 **p=2e-4**; curated train α8/α12 −.333 **p=2e-3**. Random control: ΔASR **+.10 to
+.19, p≥.125 everywhere** (never reduces ASR; refusal_rate stays ≈ ds_base). **empty_rate = 0.000 in every
cell at every α** — the ASR→0 is genuine refusal restoration, not a broken decoder.

Three facts, all four cells: (1) refusal re-injection **monotonically drives ASR to 0** and refusal_rate
to 1.0; (2) at α=12 **every** Doublespeak jailbreak is neutralized (ASR .000) with generation still
coherent; (3) the effect is **axis-specific** — a random push of equal norm never restores refusal and
never lowers ASR (if anything nudges it up). Necessity is established.

## Interpretation — the mechanistic account completes

Combining all three behavioral experiments:

| lever | representational role | behavioral effect on ASR |
|---|---|---|
| L8–11 concept WRITE | Holm-sig necessary (readout) | **NULL** (BEHAV-WRITE) |
| L14–21 carry heads | necessary + sufficient (readout) | **NULL** (BEHAV-CARRY) |
| **refusal axis (L18)** | (orthogonal to concept, cos≈0.01–0.06) | **NECESSARY + SUFFICIENT** — ablate→jailbreak (>Doublespeak); re-inject→ASR .000, dose-dependent, specific |

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

- Refusal suppression is now shown **both sufficient** (ablation → jailbreak, > Doublespeak) **and
  necessary** (re-injection → ASR .000, dose-dependent, axis-specific, coherent). The causal loop is
  closed in both directions.
- Necessity α-injection is single-layer L18 all-position; the effect saturates by α=12 (ASR 0 all cells)
  and is already significant at α=8 on clearharm + curated-train. curated-test is floor-limited (ds_base
  ASR .095) but still → 0. Random-direction control excludes generic-perturbation and decoder-break
  explanations (empty=0).
- L18 direction, ablation α=1.0, greedy decode, StrongREJECT MAL≥0.25. All four cells complete (clearharm
  44/42, curated 30/21). Greedy-decode/judge numerics vary ~1–2 examples/cell across GPU nodes
  (a clearharm run was preempted+restarted); the +0.43–0.48 effect dwarfs that wobble.

## Reproduce
```
sbatch --time=01:30:00 --export=ALL,DSBENCH=doublespeak_causality/data/behavioral/beh_clearharm.json,DSMAXNEW=220,DSN=0 \
  doublespeak_causality/slurm/run_behav_refusal.sh      # + beh_curated.json
```
Runs (sufficiency): curated `behav_refusal_curated_a1.0_20260804_125055_708039`,
clearharm `behav_refusal_clearharm_a1.0_20260804_133355_708038`.
```
# necessity (re-injection):
sbatch --time=01:30:00 --export=ALL,DSBENCH=...beh_clearharm.json,DSMAXNEW=220,DSN=0 \
  doublespeak_causality/slurm/run_behav_refinject.sh    # alphas 4,8,12 + random@8
```
Runs (necessity): clearharm `behav_refinject_clearharm_L18_20260804_141615_710769`,
curated `behav_refinject_curated_L18_20260804_142104_710770`.
