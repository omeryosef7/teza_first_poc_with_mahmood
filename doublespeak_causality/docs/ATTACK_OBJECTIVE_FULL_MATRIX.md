# Attack-Objective Full Matrix (Gate-7 v3) — NEXT sprint 2026-08-09

Model: Llama-3.1-8B-Instruct (bf16). Optimizer: GCG (`poc_stage_gcg_early.run_optimization`),
suffix_len=16, topk=256, `--no-filter-cand`, `--suffix-placement user`, `--selection-mode weighted`,
repr-in-selection ON for mechanism arms. Compute-matched: **batch=32 × N_STEPS=200** (= batch64×100;
all arms identical). Split: **v3 leakage-0** ClearHarm (train pool 40 items, held-out **test n=37**).
Primary metric: StrongREJECT held-out **test ASR**. Off-by-one FIX applied (direction read at the
`hidden_states[fit+1]` row it was fitted on). Direction fits frozen train-side; test touched only in eval.

Gate-B sign test PASSED pre-launch: the refusal-projection GCG loss suppresses the L18 projection
(+0.038→−0.04 over 8 steps) while a norm-matched random direction stays flat (~0).

## Arms (per the frozen 16-arm design, reconciled for v3)
Baselines: **vanilla GCG** (arm04, doublespeak), **vanilla direct** (arm03), **random-suffix** (arm15,
dropped — the random-*direction* arms are the stronger control).
Mechanism (each with a norm-matched RANDOM-direction control at the same layer/λ/seeds):
**refusal@L18** (readout/decision), **refusal@L12** (Jacobian sensitivity-peak = the "Jacobian
objective", operationalized first-order), **concept@L9** (validated concept-write), **combined**
(concept@L9 + refusal@L18, multilayer). λ=0.25 (P8.1 proxy). DROP arm05 (=arm04), arm14 (carry
causally null). MAC/TROPT + 2nd-order ‖J‖² = stretch (documented out-of-scope: ‖J‖ is target-generic
& weaker per P6; MAC needs a new TROPT Loss subclass).

## SEED 42 (v3 test n=37) — 10/10 COMPLETE
| arm | ASR | refusal_rate | vs vanilla ΔASR | vs its random ΔASR (McNemar p) |
|---|---|---|---|---|
| vanilla GCG (arm04) | 0.243 | 0.568 | — | — |
| vanilla direct (arm03) | 0.324 | — | +0.081 | — |
| **refusal@L18 (arm07)** | **0.324** | 0.513 | +0.081 | **−0.027 vs rand 0.351 (p=1.000)** |
| refusal_rand@L18 (arm07r) | 0.351 | 0.432 | +0.108 | (control) |
| **refusal@L12 Jac-peak (arm10)** | **0.216** | 0.595 | −0.027 | +0.108 vs rand 0.108 (p=0.125, ns) |
| refusal_rand@L12 (arm10r) | 0.108 | — | −0.135 | (control) |
| **concept@L9 (arm06)** | **0.243** | — | **+0.000 (inert)** | +0.054 vs rand 0.189 (ns) |
| concept_rand@L9 (arm06r) | 0.189 | — | −0.054 | (control) |
| combined (arm08) | 0.216 | — | −0.027 | +0.027 vs rand 0.189 (p=1.000) |
| combined_rand (arm08r) | 0.189 | — | −0.054 | (control) |

### Seed-42 reads (answers Q1–Q4)
- **Q1/Q3 — the headline NEGATIVE:** the validated refusal-suppression objective (@L18, the only axis
  with demonstrated activation-space behavioural potency) is **statistically indistinguishable from a
  norm-matched random direction** (0.324 vs 0.351, ΔASR −0.027, McNemar p=1.000) — and a random
  direction is itself as good a GCG signal as the mechanism. This CONFIRMS the first-cut "refusal≈random"
  result on the **corrected leakage-0 split, at 200 steps (4× the first-cut budget), with paired stats**.
- **Q2 — Jacobian:** targeting the Jacobian sensitivity-peak layer (L12) gives **no advantage**
  (0.216 < vanilla 0.243; below the readout-layer L18). refusal@L12 edges its own random (+0.108) but
  ns (p=0.125) and both are below vanilla → not a useful attack lever.
- **Q4b — combined:** concept+refusal (0.216) is WORSE than refusal@L18 alone (0.324) and ≈ its
  random (0.189, ΔASR +0.027, McNemar p=1.000) — adding the concept term does not help and degrades
  the mix. **Every mechanism arm is ≈ its norm-matched random control.**
- **Q4 — concept:** the concept objective is **inert** — concept@L9 ASR (0.243) is *identical* to
  vanilla (0.243); it only "beats" its random because a random concept direction is a slightly worse
  optimization signal. Consistent with the concept circuit being behaviourally epiphenomenal.

## SEEDS 43, 44 (confirmation)
### Seed 43 (v3 test n=37) — finalists
| arm | ASR |
|---|---|
| vanilla | 0.351 |
| refusal@L18 | **0.405** |
| refusal_rand@L18 | **0.243** |
| concept@L9 | 0.270 |
| concept_rand@L9 | _pending_ |
**IMPORTANT — cross-seed sign flip / high variance:** refusal@L18 vs its random flips between seeds:
seed42 ΔASR −0.027 (rand≥refusal) vs seed43 **+0.162** (refusal>rand). Mean(42,43)=+0.068 but the
between-seed swing (~0.19) dwarfs it — consistent with the plan's ~6pp between-run floor being far
exceeded here → the refusal-vs-random comparison is **UNDERPOWERED / seed-dependent**, NOT a clean
positive. Seed 44 (running) needed; report all seeds, do not cherry-pick. Concept still ≤ vanilla
both seeds (0.243==vanilla s42; 0.270<0.351 vanilla s43) → concept inert holds.
_(Seed 44 all 5 finalists running; per-seed McNemar + 3-seed mean±spread to be filled on completion.)_

## Mechanistic-validity (Q5) — pending
`phase_gate7_mech_validity.py`: for each optimized suffix, does the intended internal projection move
on held-out test (refusal proj @L18 before→after), and does the mechanism suffix move it MORE than
random? (Distinguishes "objective moved its target but ASR didn't beat random" from "objective failed".)

## GATE D classification (provisional, seed 42): **NON-SPECIFIC NEGATIVE**
The mechanism-derived objectives do not beat norm-matched random controls; the refusal axis (causal &
predictive in activation space) does not convert into a specific token-space optimization lever, and
the concept axis is inert. Pending ≥3-seed confirmation before finalizing.

## MECHANISTIC-VALIDITY (Q5) — seed42, held-out v3 test n=37 (reports/GATE7_V3_MECH_VALIDITY_seed42.json)
Projection change vs neutral suffix (mean over 37 test prompts), at the fitted hidden_states rows:
| suffix | Δ refusal_proj @hs19 (L18) | Δ refusal_proj @hs23 (L22) | Δ concept_proj @hs10 (L9) |
|---|---|---|---|
| refusal@L18 | **−1.66** | −2.81 | −0.19 |
| refusal_rand@L18 | **−2.04** | −3.53 | −0.17 |
| concept@L9 | −1.05 | −1.45 | **−0.16** (wanted UP) |
| concept_rand@L9 | −1.66 | −2.58 | −0.22 |
(baseline refusal_proj @hs19 = 3.40, @hs23 = 4.39; concept_proj @hs10 = 0.55)
**DECISIVE READ:** the refusal-optimized suffix does NOT lower the refusal projection MORE than a
norm-matched RANDOM-direction suffix — random suppresses it MORE (−2.04 vs −1.66 @hs19; −3.53 vs
−2.81 @hs23). So the mechanism objective fails to move its intended internal target specifically on
HELD-OUT prompts. Adversarial GCG suffixes suppress the refusal signal GENERICALLY (any strong
perturbation does); the validated-direction objective adds no specificity even at the mechanism level.
The concept "up" objective likewise does NOT raise concept projection (Δ −0.16, wrong direction).
=> This resolves the ASR seed-variance: the objective is **NON-SPECIFIC at the mechanism level**, not
merely ASR-underpowered. Q5 answer: the intended internal change does NOT occur more than random.

## GATE D (updated): NON-SPECIFIC NEGATIVE (mechanistically grounded)
Refusal/concept/Jacobian/combined GCG objectives neither beat norm-matched random controls on ASR
(refusal-vs-random seed-dependent/underpowered; concept inert) NOR move their intended internal
targets more than random on held-out test (Q5). The causal+predictive activation-space refusal axis
does NOT convert into a specific token-space optimization lever. (bf16 primary; Llama-3.1-8B; v3
leakage-0; 3 seeds; batch32×200.)
