# reports/PHASE9_DOSE.md — Dose-response of the L9 / mid-band MLP write

**Question (plan Phase 9):** is the L9 demo-codeword MLP write a GRADED causal lever, or an on/off
artifact? A valid handle shows an ordered dose-response, not one isolated coefficient.

## Method
`scripts/phase9_dose.py`, reusing the audited phase6 machinery (FC DE_context readout, demo-codeword
positions, `pc.ComponentOutSwap`). Patch the demo-position `mlp_out` with an **interpolated donor
(1−α)·DS + α·BENIGN** at α ∈ {0, .25, .5, .75, 1, 1.5, 2}. **α=0 = DS baseline (exact no-op anchor,
verified p≈C1); α=1 = full benign swap (= phase6 C3 necessity).** dev(train)/heldout(test) separate;
valid = examples where the α=0 reading exceeds benign. Jobs 704861–704864 (both cohorts × {L9 single,
L9–L11 band}), n≥20/split.

## Result — monotone graded dose-response on all four cells

p_concept as α increases from 0 (full DS write) to 1 (full benign):

**Single L9:**
| cell | α=0 | 0.25 | 0.5 | 0.75 | 1.0 | drop(0→1) |
|------|-----|------|-----|------|-----|-----------|
| curated dev      | .811 | .803 | .790 | .778 | .762 | .048 |
| curated heldout  | .690 | .645 | .619 | .588 | .575 | **.115** |
| clearharm dev    | .884 | .874 | .856 | .839 | .819 | .065 |
| clearharm heldout| .879 | .877 | .872 | .868 | .862 | .017 |

**L9–L11 band (jointly):**
| cell | α=0 | 0.5 | 1.0 | drop(0→1) |
|------|-----|-----|-----|-----------|
| curated dev      | .811 | .765 | .709 | .102 |
| curated heldout  | .690 | .621 | .583 | .107 |
| clearharm dev    | .884 | .833 | .797 | .087 |
| clearharm heldout| .879 | .864 | .851 | .028 |

- **Monotone decreasing over α∈[0,1] on all 4 cells, both cohorts, both splits** — as the DS MLP write is
  progressively replaced by benign, the concept reading falls smoothly. (clearharm dev/heldout monotone all
  the way to α=2; curated shows a trivial plateau/uptick only in the α>1 EXTRAPOLATION region — over-
  subtracting past a full benign swap is not meaningful.)
- The α=0 no-op anchor reproduces the DS baseline exactly (harness correct); the α=1 point equals the
  phase6 necessity magnitude (per-layer L9 ≈ .02–.12, band larger) — internally consistent.
- The band (concentrated write region L9–L11) gives a slightly larger, cleaner curve than L9 alone, as
  expected for a distributed write.

## Interpretation
The mid-band demo-codeword MLP write is a **graded causal lever**: partial neutralization yields partial
loss of the hijacked reading, with an ordered dose-response — satisfying the Phase 9 requirement (not one
isolated successful coefficient). This is the handle Phase 10 can target as a causal optimization objective.

## Caveats / next
- Effect sizes are modest (matching the small-but-real, right-skewed per-layer L9 necessity) — the write is
  one distributed contributor, consistent with the whole-circuit "distributed within a band" picture.
- Other Phase-9 dose targets (concept-direction add sufficiency, refusal-removal, head-output/path scaling)
  reuse existing hooks (AllPositionAdd + directions; the phase7 freeze) — available extensions.

Reproduce: `python scripts/phase9_dose.py --bench data/bench/bench_<cohort>.json --layers 9` (or 9-11).
