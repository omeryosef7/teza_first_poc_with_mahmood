# What a next-generation bank has to change, and why — three blocked lines, one root cause

**2026-09-12.** Written because three independent results in this phase have now traced back to the
same place, and the record was carrying them as three separate "open, with cost" rows rather than as
one constraint. This is a specification, not a proposal to build: it says what would have to be true,
and what each change unblocks.

## The three blocked lines

| line | what is blocked | `CONT-ENTRY` |
|---|---|---|
| **Sufficiency** | the within-domain demonstration-side patch — **0 of 4050** within-domain pairs share their demonstration codeword positions, so an `absolute`-aligned transplant is not constructible | `076` |
| **Specificity** | §15's harmful **non-BOMB** reference — `gun` does not install (within-domain sd **0.085** vs bomb's **0.374**) and `knife` shows **no excess** under the fair contrast, so there is no second concept to contrast against | `079`, `082` |
| **Power** | nearly everything — A2 is underpowered in content-true units, the quantitative dissociation was withdrawn partly for it, and the installation↔refusal link sits at **ρ 0.176 against an MDE of 0.337** | `107`, `116`, `124` |

## Why they are one constraint

All three are properties of **how the bank is generated**, fixed before any model is run:

* demonstration blocks are drawn from per-domain pools, so their **internal token layout varies** —
  which is what makes occurrence *i* of one prompt not the same object as occurrence *i* of another;
* the concept is a **generation parameter**, so which concepts install is decided at bank time;
* the domain list is a **declared constant** — `prompt_families.DOMAINS` holds **116**, and the
  `ts116m` bank uses all 116, of which 23 are TEST and 3 excluded, leaving **~90** usable and **67**
  where the knockout arms exist.

No analysis of the existing arms moves any of them.

## What would have to change

**1. Position-matched demonstrations.** Emit each demonstration block padded or templated to an
identical token layout within a domain, so that occurrence *i* sits at the same index in every slot.
*Unblocks:* the within-domain, install-graded sufficiency patch — the one test that would give `F5`
causal content at its own site. *Cost:* a change in `prompt_families.generate_bank`'s emission, then
regeneration. *Risk:* padding is itself a manipulation; the padded bank must reproduce the existing
installation and ASR levels before it is used for anything, or it is a different experiment.

**2. A second concept that installs.** The remap installs `bomb` at **0.5636** and `gun` at **0.0470**
(`A12`), so the existing contrast concepts are floor-bound. A specificity test needs a concept whose
installation is within, say, a factor of two of `bomb`'s. *Unblocks:* §15's harm control, and with it
the only route to separating "toward BOMB" from "toward any installed concept". *Cost:* `generate_pools`
per candidate concept plus a screening readout — cheap per candidate, and **screen before committing**:
`gun` and `knife` were both built in full before their floors were known.

**3. More domains.** ~240 domains would put a ρ ≈ 0.18 linking test at 80 % power; the present 67
reaches ρ ≈ 0.34. *Unblocks:* A2/A3 in content-true units, the linking test, and every per-domain
correlation this phase has had to report as underpowered. *Cost:* the dominant one — pools and bank
generation scale linearly, and every arm (installation, ASR, knockout, control) must be re-run.

## What this does not claim

That a new bank would produce positive results. The two-codeword behavioural null is robust and a
larger bank would most likely **sharpen** it rather than overturn it. What a new bank buys is the
ability to **distinguish** a null from an underpowered test — which is exactly the distinction this
phase has repeatedly been unable to make, and has repeatedly had to say so.

## The honest ordering

**3 > 2 > 1.** Power is the binding constraint on the most claims; a second installing concept is the
cheapest and unblocks a specific named control; the position-matched bank serves one experiment and
carries the largest interpretive risk. None of them is analysis work, and none should be started
without the screening step its predecessor lacked.
