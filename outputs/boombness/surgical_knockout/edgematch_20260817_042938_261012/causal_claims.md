# §10.4 Causal claims — combined Boombness/refusal interventions

**Mandatory named deliverable of plan §10.4** (`outputs/boombness/surgical_knockout/<run_id>/causal_claims.md`).
Written 2026-08-18. It was **missing while the board recorded §10.4 as in progress** — the second time in
this sprint a plan-mandated deliverable turned out not to exist (the first was §5.4's `decision_gate.md`).

The plan's instruction is explicit: *"Do not make strong causal claims unless controls pass."* This file is
organised around which controls passed, and it labels the two places where they **fail or reverse**.

## Arms and their status

| plan arm | intervention | ASR run | status |
|---|---|---|---|
| A no intervention | — | `len_base` | done |
| B remove boombness | `d_surface:project_out:8-8:1.0` | `len_B` | done |
| C remove refusalness | `refusalness:project_out:18-18:1.0` | `len_C` | done |
| **D remove both** | `d_surface:project_out:8-8 + refusalness:project_out:18-18` | `len_D` | **RUNNING (763594)** |
| E add boombness | `d_surface:add:8-8:0.25` | `len_A` | done |
| F add boombness + remove refusalness | `d_surface:add:8-8:0.25 + refusalness:project_out:18-18:1.0` | `len_F` | done |
| G random controls | matched random at the same layers | `len_Bctrl`, `len_Fctrl`, `len_Dctrl` | Dctrl **RUNNING (763595)** |

Arm D's control is a **double** random projection at both layers, not a single one: matching a
two-projection arm against a one-projection control would repeat the control-mismatch this sprint already
had to correct for arm B, where every control was an `add` while the arm was a `project_out`.

All arms are length-matched (512 new tokens), judged by the same StrongReject rubric judge, paired on the
same 420 `natural_doublespeak` prompts, and every arm passed `coherence_gate.py` on that population
(`outputs/boombness/coherence_lenfair.json`) — no ASR below is computed on degenerate text.

## Result on the attack population (`natural_doublespeak`, n=420 paired)

| arm | ASR@0.5 | mean score | refusal | Δ ASR vs A |
|---|---|---|---|---|
| A baseline | 0.243 | 0.204 | 0.057 | — |
| B remove boombness | 0.269 | 0.242 | 0.055 | +0.026 |
| B control (random project_out) | 0.229 | 0.186 | 0.057 | −0.014 |
| C remove refusalness | 0.269 | 0.214 | 0.000 | +0.026 |
| E add boombness | 0.088 | 0.077 | **0.676** | **−0.155** |
| **F add boombness + remove refusalness** | **0.548** | **0.487** | 0.002 | **+0.305** |
| F control (random + remove refusalness) | 0.219 | 0.172 | 0.000 | −0.024 |

## The plan's key question, answered

> *"Can we reduce ASR by removing Boombness while preserving comprehension?"*

**No.** Removing Boombness (arm B) **raises** ASR slightly (+0.026), it does not reduce it. The reduction
comes from **adding** Boombness (arm E, −0.155), and arm E does it by **triggering refusal** — refusal goes
0.057 → 0.676. That is refusal suppression working in reverse, not the removal of a harm-carrying
representation, so it does not support the causal story §10.4 was designed to test.

> *"…or can we produce the opposite direction by adding Boombness while manipulating refusal?"*

**Yes on the doublespeak population, and this is the sprint's largest behavioural effect.** Arm F reaches
ASR 0.548 against a 0.243 baseline (+0.305), while the composed random control moves −0.024. The effect is
**not** explained by refusal removal alone: arm C, which removes exactly the same refusal direction, gives
only +0.026. The interaction is real and it is `d_surface`-specific **on this population**.

## ⛔ Where the controls REVERSE — and why no mechanism claim is made

The plan requires separating *semantic remapping* from *refusal suppression* from *general
confusion/destruction*. Running the same arms on the other conditions defeats the semantic-remapping story:

| condition (n) | baseline | **F** | **F control (random)** | C (remove refusal only) |
|---|---|---|---|---|
| `natural_doublespeak` (420) | 0.243 | **+0.305** | −0.024 | +0.026 |
| `direct_harmful` (72) | 0.042 | **+0.000** | **+0.417** | +0.167 |
| `concept_in_benign_ctx` (72) | 0.042 | **+0.000** | **+0.236** | +0.139 |
| `benign_literal` (324) | 0.015 | +0.019 | −0.009 | −0.003 |

**The specificity inverts.** On explicit harm the *random* composition gains +0.417 while arm F gains
**nothing** — the exact opposite of the doublespeak cell. So `d_surface` is not "supplying harm content":
on `direct_harmful` it actively **blocks** the gain that removing refusal otherwise produces (+0.167 for C
alone, +0.000 for F). This is consistent with arm E, where adding `d_surface` drives refusal to 0.676.

This is why **retraction #8** withdrew the "capability channel" mechanism. The empirical interaction stands;
the explanation does not.

### What may and may not be claimed

**Supported:**
- Adding `d_surface` at L8 while projecting out the refusal direction at L18 raises doublespeak ASR from
  0.243 to 0.548, robust to thresholds, domains, held-out families and length-matching, with an inert
  composed random control on that population.
- Adding `d_surface` alone suppresses ASR by triggering refusal (0.057 → 0.676).
- Removing `d_surface` does **not** reduce ASR.

**NOT supported, and explicitly disclaimed:**
- Any claim that `d_surface` carries harmfulness or "supplies harmful content" — refuted by the
  `direct_harmful` reversal and by the §0.3 finding that the gain appears on `benign_remap`, where the
  mapping is never taught.
- Any claim that the arm-F gain is *doublespeak-semantic* rather than an interaction whose sign depends on
  the condition. The mechanism is **unknown**.
- Any comprehension-based claim about these arms: §8 shows a **norm-matched random direction perturbs
  comprehension ~3× more than `d_surface`** at every demonstration count, so the §2.6 comprehension
  readout cannot attribute anything to this axis (corrections C10, and §8).

## Pending

Arm D (remove both) and its double-random control are running as 763594 / 763595. D is the arm that
distinguishes "the two directions act independently" from "removing Boombness matters only once refusal is
out of the way": if D ≈ C, Boombness removal contributes nothing even with refusal suppressed. **This file
will be updated with D when the judge lands, whichever way it falls.**
