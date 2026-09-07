# PHASE 9 — what is actually constructible, and what that costs the conclusion

*2026-09-07. Written before submission, because a scope limit discovered after a result reads as an
excuse and a scope limit recorded before it is a design fact.*

The Q4b runner's `--plan` reproduces the design's **54 arms (24 live / 30 control)** exactly. It
also reports how many can be built **today: 26. Twenty-eight cannot.**

## What is constructible

| arms | what | n |
|---|---|---|
| **H2a** | the projection-out primary, 2 scopes x 2 codewords | 4 |
| **C1** | norm-matched random direction, 5 seeded draws | 20 |
| **C3** | the raw axis `v_remap` | 2 |
| | **total** | **26** |

## What is not, and why

| arms | what | why not |
|---|---|---|
| 16 | **H1**, the full-state patch upper bound | no `patch` path wired **and** the donor population is empty under R-116 |
| 2 | **C7** | same |
| 4 | **H2b**, counterfactual component replacement | no `component_replace` mode |
| 2 | **C2**, shuffled-label direction | no shuffled-label direction in the payload |
| 2 | **C4**, equal-magnitude orthogonal edit | `add` mode is uninstrumented and has no single-site form |
| 2 | **C5**, the disabled-hook bridge | `C-119`: its preregistered dose is α=0, so the bridge refuses at the node and certifies nothing |

## Why the H1 loss is the one that matters

H1 is not merely another arm. **It is the control that the interpretability-illusion literature
asks for** (`A-047`, `arXiv:2311.17030`): comparing a subspace intervention against full activation
patching at the same site is the standard check that a subspace effect is not running through
dormant or disconnected features. Our launch order `H1 → H2` existed precisely to provide it.

H1 is unconstructible for a **scientific** reason, not just a wiring one: its donor is a `C_knife`
prompt, and R-116 measures knife installing in **0 of 113 domains**. There is no knife-installed
donor to patch from. `C-112` already demoted this arm on that basis; the runner's plan confirms the
demotion is total rather than partial.

**Consequence, stated now:** with H1 unavailable, a **positive** H2a result cannot be validated
against the full-patch upper bound *in this phase*. Combined with the two bounds already recorded
in `A-047` — that the axis carries a −0.55 to −0.68 loading on a generic demonstration-presence
axis (`cos(v_knife, v_gun) = 0.91–0.95`), and that projection removes only **4.7–19.0%** of the
cell-mean spread — the honest statement of what PHASE 9 can now return is:

- **a null**, interpretable only *with the realised dose attached*, and weak evidence of non-use at
  a 5–19% dose; or
- **a positive**, which cannot be attributed to concept identity and cannot be checked against its
  own upper bound.

This is a real narrowing of the phase, and it follows from a measurement (R-116), not from a
scheduling constraint. It is **not** a reason to cancel: a dose-qualified null on the primary
concept axis, with norm-matched random and raw-axis controls, is still the thing mandate §32 calls
valuable — provided it is published with its bounds and never as "the representation is not used".

## What must be fixed BEFORE any GPU submission

1. **`C-117` — the liveness producer and consumer do not share a schema.** `n_cells_edited_expected`
   is absent, `resolved_absolute_index` is a list where a scalar is expected, and `rel_end` is None
   on S2. As it stands **the analyzer would VOID every real arm**. This would have burned the GPU
   time and returned nothing. The runner currently gates twice and writes an annotated copy rather
   than rewriting the artifact; the schemas still need to be reconciled.
2. **`C-119` — control C5 cannot certify anything at α=0.** This is not cosmetic: the frozen
   config lists *"the disabled-hook bridge not reproducing baseline"* among `primary.void`. A void
   condition that cannot be evaluated is a hole in the validity argument, not a missing nicety.
   Refused rather than silently re-dosed to α=1, which was the right call.
3. **`C-118` — `--emit-probe` is refused**: no per-row attribution point for `ProbeReadCapture`, and
   `pr048_result.json` carries no `FROZEN_PROBE` block yet. O1 is therefore not capturable, and O1
   is not the primary — but the config declares it, so its absence must be recorded rather than
   quietly dropped.
4. **The test suite has not been run to completion.** 115/115 passed on a 27-file subset before the
   run was cancelled under node contention (~1.5% CPU behind two other sessions). *"Nothing imports
   the new file"* is an argument, not a measurement. **Re-run on a quiet node before submitting.**

## Order of operations, unchanged

`Q0 → Q1 → smoke (Q7) → H1 → H2`. Q0 is satisfied. The first job is **Q1 on the VALIDATION split**,
never test, and it must print `PROCEED` before any test-split job is submitted. H1 is now skipped as
unconstructible rather than run — and under `C-112` an H1 `UNAVAILABLE` does **not** kill the H2a
primary, which is the behaviour the runner implements.
