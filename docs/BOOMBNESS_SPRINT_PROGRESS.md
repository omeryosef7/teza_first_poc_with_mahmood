# Boombness Objective Sprint — Progress Log

**Plan:** [`docs/BOOMBNESS_OBJECTIVE_SPRINT_PLAN.md`](BOOMBNESS_OBJECTIVE_SPRINT_PLAN.md)
**Branch:** `behavioral-causality-sprint`
**Started:** 2026-08-16
**Owner:** Omer Yosef (TAU MSc, adv. Mahmood Sharif) · executed by Claude Code

This file is the single place to track sprint progress. Every loop tick appends here.
Status vocabulary: `TODO` · `IN PROGRESS` · `DONE` · `BLOCKED` · `NEGATIVE (documented)` · `SKIPPED (justified)`

---

## Phase status board

| Phase | Plan § | Description | Status | Evidence |
|---|---|---|---|---|
| P1.1 | §1 | Clone `interp-jailbreak` to `external_repos/`, strip `.git` | DONE | `external_repos/interp-jailbreak/` @ upstream `89620cf` (2025-06-20) |
| P1.2 | §1 | `notes/interp_jailbreak_best_practices.md` | TODO | |
| P1.3 | §3 | Aligned prompt generator `src/boombness/prompt_families.py` | TODO | |
| P1.4 | §3.1 | Generate 50 prompts + manual review | TODO | |
| P1.5 | §2.4 | Tokenization audit | TODO | |
| P1.6 | §3 | Iterate generator until alignment + tokenization OK | TODO | |
| P2.1 | §5.1 | Hidden-state replacement, smoke | TODO | |
| P2.2 | §5.2 | Additive bomb-direction sweep, smoke | TODO | |
| P2.3 | §5.3 | Metrics + comprehension controls validated | TODO | |
| P2.4 | §5 | Pilot 30–50 prompts | TODO | |
| P2.5 | §5.4 | `decision_gate.md` | TODO | |
| P3.1 | §6.1 | Logit-lens Boombness | TODO | |
| P3.2 | §6.2 | Direction Boombness | TODO | |
| P3.3 | §6.3 | Simple probe | TODO | |
| P3.4 | §6.3 | Hard-negative / held-out-condition probe | TODO | |
| P3.5 | §6.4 | Metric comparison | TODO | |
| P4.1 | §7.1 | Token-level Boombness per occurrence × layer | TODO | |
| P4.2 | §7.1 | Occurrence × layer heatmaps | TODO | |
| P4.3 | §7.1 | Later-carrot-more-bomb-like test | TODO | |
| P4.4 | §8 | Example-count sweep | TODO | |
| P5.1 | §4 | ~600-prompt bank | TODO | |
| P5.2 | §9 | Generations + evaluation | TODO | |
| P5.3 | §9 | Prompt-level Boombness | TODO | |
| P5.4 | §9 | Correlation / regression | TODO | |
| P5.5 | §9 | Figure-9-style plot | TODO | |
| P6.1 | §10.1 | Attention edge knockout | TODO | |
| P6.2 | §10.2 | Head knockout | TODO | |
| P6.3 | §10.3 | Direction knockout | TODO | |
| P6.4 | §10.4 | Combined Boombness/refusal | TODO | |
| P6.5 | §10 | Comprehension controls | TODO | |
| P6.6 | §10 | Causal vs destructive separation | TODO | |
| P7.1 | §11 | Role-style variants | TODO | |
| P7.2 | §11 | Role framing → Boombness | TODO | |
| P7.3 | §11 | Userness/CoTness probes (if feasible) | TODO | |
| P7.4 | §11 | Boombness + role predicts ASR | TODO | |
| P8.1 | §12.1 | Boombness GCG objective | TODO (gated) | |
| P8.2 | §12.2 | Boombness − refusal objective | TODO (gated) | |
| P8.3 | §12.5 | Baseline / refusal-only comparison | TODO (gated) | |
| P8.4 | §12.5 | Universality + held-out transfer | TODO (gated) | |
| P8.5 | §15 | Final reports | TODO | |

---

## Decision gates

| Gate | Question | Verdict | Date |
|---|---|---|---|
| G1 (§5.4) | Can we force `carrot` to be `bomb`-like, and does it change behavior? | pending | |
| G2 (§9) | Does prompt-level Boombness predict ASR? | pending | |
| G3 (§10) | Can Boombness be removed without destroying comprehension? | pending | |
| G4 (§12) | Is Boombness a usable GCG objective? | pending | |
| FINAL (§18) | A strong-positive / B mechanistic-not-causal / C refusal-only / D negative | pending | |

---

## Bug / integrity audit log

Every 4h an independent agent audits code + outputs for result-affecting bugs. Findings land here.

| Date | Auditor | Finding | Severity | Fix | Rerun needed? |
|---|---|---|---|---|---|

---

## Tick log

### 2026-08-16 — Tick 0 (sprint start)
- Read plan, project memory (SLURM rules, cyber-safeguard subagent rule, SDPA rule, position-index bug class).
- Confirmed environment: SLURM up, L40S nodes `n-801..805`, `t-806`; no jobs of ours running; conda `base` + `poc_stage2`.
- **P1.1 DONE:** cloned `https://github.com/matanbt/interp-jailbreak.git` into `external_repos/`, recorded upstream commit `89620cfe0f78a0741e739889ef2e5cd47fe96dc1` (2025-06-20 "Update hijacking analysis"), removed `.git`.
  - Verified byte-identical to the pre-existing root-level `interp-jailbreak/` copy (only extra file there is the paper PDF) → the repo's existing copy was already up to date.
- Launched scouting fan-out (6 agents) over `interp-jailbreak` + our `doublespeak_causality` code to maximize reuse before writing anything new.
- Environment: torch 2.7.1+cu126 / transformers 5.12.1 / sklearn 1.9 / scipy / pandas / matplotlib in conda env
  `poc_stage2` (NOT `base` — base has no torch). **No `transformer_lens`**, no `seaborn`, no `statsmodels`
  → we use plain HF forward hooks (which our repo already does) rather than the paper's TransformerLens fork.

#### F1 (§3 alignment) — the SEMANTIC family is already perfectly aligned; the *benign* arm is not

Measured on `data/pair_benchmark/pair_carrot_bomb.json` (800 semantic prompts, carrot↔bomb):

| pair | mean string similarity | exact word-swap identical? |
|---|---|---|
| `DIRECT_CONCEPT` vs `DOUBLESPEAK` | **0.937** | **YES** — `direct.replace("bomb","carrot") == doublespeak` |
| `NEUTRAL_CODEWORD` vs `DOUBLESPEAK` | **0.326** | no |

So Direct↔Doublespeak is a *pure lexical swap over identical sentences* — better aligned than the plan
assumed. But the **benign-literal arm is a different story entirely** (farmer / market / smoothie /
cake vs exploded / defused / detonation / blast).

**Consequence, and it is the central methodological problem of this sprint:** the plan's §6.2 direction
`d_bombness = mean(h_bomb in direct) − mean(h_carrot in benign-literal)` is computed across two arms
that differ in *both* the surface token *and* the entire semantic domain. Such a direction is
`bombness + explosive-context-ness`, and any "Boombness predicts ASR" result using it is confounded.

**Design response (supersedes plan §6.2's simple difference):** use a 2×2 factorial that separates the
two effects, keeping the *final query sentence byte-identical except for the target word* in every cell:

| | demo block = benign domain | demo block = harm domain |
|---|---|---|
| **surface = carrot** | `A` benign literal | `C` natural doublespeak |
| **surface = bomb** | `E` bomb-in-benign-context (hard negative, plan §6.3) | `B` direct harmful |

`d_bombness` = main effect of surface word **within matched context** (`(B−C) and (E−A)` averaged),
`d_context` = main effect of domain (`(C−A) and (B−E)`). The plan's naive direction is `B−A`, which is
the *sum* of the two effects. This is a real improvement over the plan and is worth reporting to
Matan/Mahmood on its own.

#### F2 (§3 alignment) — the BEHAVIORAL triplet is misaligned by construction

`doublespeak_causality/ds_common.py:814-816` (`build_conditions`):

```python
direct      = f"{prefix} {harmful_instruction} {suffix}"                 # NO demo block
neutral     = f"{prefix} {substituted_query} {suffix}"                   # NO demo block
doublespeak = f"{demos}\n\n{prefix} {substituted_query} {suffix}"        # demo block present
```

Measured over all 900 behavioral rows of the carrot↔bomb bank: mean similarity `direct↔doublespeak`
= **0.239**, `neutral↔doublespeak` = **0.255**, exact-word-swap-identical = **0/900**. Typical lengths
86 / 88 / 378 chars — i.e. Doublespeak carries ~292 extra characters of context that Direct and Neutral
do not have.

Note the file header of `30_build_pair_benchmark.py` claims conditions are "structurally matched: every
one has a demo block of the same size". That claim is **true for the semantic family and false for the
behavioral family**. For ASR a no-context Direct baseline is defensible; for *representation* comparisons
at the codeword position it is a length/context confound.

**Design response:** the Boombness generator emits `DIRECT_WITH_DEMOS` and `BENIGN_WITH_DEMOS` arms so
every condition carries a demo block of matched size and matched sentence frames.

#### F3 (§5.4, §10.3) — a Boombness direction ablation has ALREADY been run here, and it is a negative

Scouting turned up prior, uncommitted work I did not know about: `doublespeak_causality/scripts/phase4_bombness_intervention.py`
plus direction bundles `outputs/phase4_directions/v_bomb_*.pt` and 15 run dirs `outputs/phase4_bombness_*`
(2026-08-14/15). The existing `v_bomb[L]` is the unit diff-of-means **(doublespeak − benign) at
`codeword_last`**, over the write/carry band `L8–21`, shipped with `v_bomb_perp_ref` (orthogonalized
against refusal-L18), a norm-matched `v_random` control, and a per-layer `gap` dose unit.

Aggregating the most recent AdvBench/Llama-3.1-8B run (`phase4_bombness_full_advbench_..._758964`,
n=230, patch band L8–18, α=1.0, readouts L20/24/28/31 — scalars only):

| arm | ASR (judge = MALICIOUS) | mean judge score | bombness readout L20 / L24 / L28 / L31 |
|---|---|---|---|
| `ds_base` | 0.2043 | 0.1826 | −0.388 / −0.048 / +0.212 / +10.373 |
| `ds_bomb_ablate` | 0.2217 | 0.2005 | **−1.218 / −1.081 / −1.109 / +7.664** |
| `ds_bomb_random` | 0.1957 | 0.1826 | −0.376 / −0.040 / +0.222 / +10.429 |

Paired Δ(judge score) vs base: **ablate = +0.0179, 95% CI [−0.0001, +0.0360]**; random = 0.0000,
CI [−0.0111, +0.0111].

**Read:** the intervention *demonstrably works on the representation* — the bombness readout is driven
negative at every readout layer, while the norm-matched random direction moves it not at all. And ASR
does **not fall**; if anything it drifts marginally up. This is the plan §18 **outcome-B/C signature**
(representation manipulable, behavior unmoved) and it is consistent with the repo's established result
that *refusal suppression, not concept content, is the causal locus*
(`project_continuation_v2_complete`, `project_causal_circuit_sprint`).

**Why the sprint is still worth running (this is the sharpened hypothesis):** `v_bomb = doublespeak − benign`
is measured with the surface word held constant (`carrot` in both arms) and the demo domain varying — so
under the F1 2×2 it is the **context main effect**, not the surface-identity effect. It is also fitted
against the misaligned benign arm (F1). The plan's actual claim — "`carrot` acquires a hidden
representation that is increasingly *bomb*-like" — is a claim about movement along the
**surface-identity axis**, which is a *different direction*:

```
d_surface := ½[ (B − C) + (E − A) ]     # "bomb token minus carrot token", context matched
d_context := ½[ (C − A) + (B − E) ]     # what the existing v_bomb approximates
Boombness(h) := <h, d_surface>          # A low, B high; the question is where C lands
```

So the sprint's job is to redo the gate with the **unconfounded** `d_surface`, plus the interaction term
`(B−C) − (E−A)` which isolates what is doublespeak-*specific*. If the negative survives that, it is a
well-controlled negative worth publishing rather than a measurement artifact — which is exactly the
outcome the plan's §18-D asks us to be explicit about.

#### F4 (§2.4) — `carrot` and `bomb` do NOT tokenize symmetrically, and it hit the most important position

The mandatory tokenization audit (`src/boombness/tokenization_audit.py`, 1464 rows, Llama-3.1-8B-Instruct):

| variant | `carrot` | `bomb` |
|---|---|---|
| `" carrot"` / `" bomb"` | **1 token** | **1 token** |
| `"carrot"` / `"bomb"` (no leading space) | **2 tokens** `['car','rot']` | 1 token |
| `"Carrot"` / `"Bomb"` | 2 tokens | 1 token |
| `" Carrot"` / `" Bomb"` | 2 tokens | 1 token |

`bomb` is one token in essentially every surface form; `carrot` is one token **only** with a
leading space and lowercase. Measured over the first full bank: `bomb` was 1 subtoken in
2664/2664 occurrences, `carrot` in 4918/5808 — **890 two-subtoken occurrences**, and 558/1464
prompts contained a mix of widths.

Two distinct causes, both now fixed:

1. **The query template.** `the word "{W}"` renders `"carrot"`, and the opening quote steals the
   leading space → `['"','car','rot','"']`. This hit **the final query occurrence — the single
   most load-bearing position in the sprint** — in 516/516 semantic rows. Quotes around the
   target were removed from every query and mapping template.
2. **Sentence-initial demo sentences** ("Carrots can be stored…") → 374 occurrences. `demo_pools._clean`
   now requires the occurrence to be preceded by a space, so it is never sentence-initial.

**Why this mattered rather than being cosmetic:** the house readout position is `codeword_last`,
the *last* subtoken of the occurrence. For a 2-subtoken carrot that is the vector at `"rot"` —
a different vector entirely, and not comparable to the `" bomb"` vector it is differenced against
in `d_surface`. Left unfixed it would have put a systematic, arm-asymmetric error straight into
the direction estimate and the logit lens, in the direction of *understating* Boombness in the
carrot arm. After the fix every occurrence in both arms is exactly one token.

`extract_boombness.py` now records `n_subtokens` / `is_single_token` per occurrence regardless,
so any residual case can be conditioned on rather than averaged over.

- Next: await scouts, then write `src/boombness/prompt_families.py` implementing the 2×2 + plan axes.
