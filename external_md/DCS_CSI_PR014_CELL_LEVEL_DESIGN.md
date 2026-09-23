# PR-CSI-014 — DESIGN ONLY. The cell-level family that would settle S-269's layer question

**Status: DESIGN. Not preregistered, not frozen, nothing launched.** Written 2026-09-23 while PR-CSI-013's
arms load, as the design work S-269 deferred with its blocker named. **No code was written and
`src/boombness/score_behavior.py` was not opened** — the standing constraint forbids editing it while arms
run, and this document is precisely what can be done without it.

---

## 1. The question, and why D34 cannot answer it

D34 established **which** heads carry load — 2, 19, 17, 23, all inside `HD_TOPK`, with none outside it
clearing the bar. It cannot say **at what depth**, because design §10 fixes that `--knockout-heads` ties a
head index across all nine blocks: every census arm knocked its head out at 6, 7, … 14 simultaneously.

S-269 then read the TRAIN screen's 288 cells and found each of the four heads dominated by **one** cell, at
**four different layers** (2→L10, 19→L14, 17→L14, 23→L7). **That is a gradient surrogate's fine structure,
and S-245 measured that this sprint's other surrogate was uncorrelated with the intervention at ρ = +0.07.**
So the layer assignments are a hypothesis with a known reason to distrust them.

## 2. ⛔ The floor decides the design, before anything else

```
288 cells (32 heads x 9 blocks); a full cell census = 288 arms x ~290 s = 23.2 h  -> INFEASIBLE
rank among  9 members (the 9 layers of one head)  -> attainable floor 1/9  = 0.1111  CANNOT certify
rank among 21 members (1 candidate + 20 controls) -> attainable floor 1/21 = 0.0476  CAN certify
```

**So the experiment cannot be "which layer of head h carries the load".** A rank among nine layers has a
floor of 0.111 and could never clear α = 0.05 **for any effect size** — the same arithmetic that killed
AM-30's original design in S-245 and that S-250's Rule 2 encodes. **The question must be reshaped, not
merely scaled down.**

**The shape that can certify:** *is cell (L, h) privileged among ARBITRARY cells?* — one candidate cell
against **20 preregistered random cells**, floor `1/21 = 0.047619`, rank 1 the only certifying outcome.

## 3. The family, and its cost

```
BASE                       1 arm   no --intervene
KO                         1 arm   all 32 heads x all 9 blocks (the existing A1 knockout) = the denominator
CELL_CANDIDATE             1 arm   the single cell (L*, h*)
CELL_CTRL_00..19          20 arms  20 DISTINCT random cells, drawn from the 287 cells other than (L*, h*)
                          -------
                          23 arms  x ~290 s = 1.9 h
```

**Identical in shape to PR-CSI-013** — one candidate, 20 controls, floor 1/21 — which means
`dcs_csi_head_single_rank.py` reads it **with no change beyond the arm-name prefix**, and its R22 sign
clause and S-246 identity check apply unaltered.

## 4. ⛔ The blocker, named precisely

`--knockout-heads` **cannot express a single cell.** §10: a head index is tied across the whole band. A
cell-level family needs a new scope in `score_behavior.py` — something of the form
`--knockout-cells L:h[,L:h...]` — and **that file may not be edited while arms are running** (the
PR-CSI-003 VOID condition).

**Consequences that follow, and must be respected in order:**

1. **Nothing can be preregistered yet.** A prereg naming a flag that does not exist is exactly S-167c
   (`--multipos`, invented by a plan document, cost a submitted job to discover).
2. **The new scope needs its own identity check.** S-246's dose identity is already blind on 1-head arms;
   a 1-CELL arm would record **1/9 of that** — a new collision surface, and the argv gate's
   `knockout_heads` assertion would need a `knockout_cells` sibling.
3. **W1's screen already emits `AtP_by_cell` for all 288 cells**, so the candidate cell can be nominated by
   a rule frozen before the data, exactly as S-248/S-250 did for the head.

## 5. How the candidate cell must be chosen, if this ever runs

**Not by the screen.** S-269's whole point is that the screen's per-cell ordering has never been validated
against an intervention. **Two admissible routes, both requiring a rule frozen first:**

* **(a) From the census, not the screen.** D34 gives four heads with intervention-measured load. Pick
  `h* = argmin E(SINGLE_h)` — **already h\* = 2 under S-248's frozen rule** — then the candidate cell is
  `(L*, 2)` where `L*` comes from the screen. ⚠ **This imports the screen's unvalidated fine structure into
  the candidate**, which is the thing under test, so the preregistration must say the result bounds
  *that cell*, not *that layer*.
* **(b) A 9-arm descriptive pass first.** Run `(L, 2)` for all nine L as a **census** (no rank, no p — the
  PR-012 pattern), then preregister the confirmatory cell test on a **held-out axis** (the `button`
  codeword, or the 3 TEST domains). **Costs one extra 11-arm job (~0.9 h) and buys a candidate chosen by
  intervention rather than by surrogate.**

**(b) is the better design and this document recommends it**, for the same reason S-245 reshaped AM-30:
choosing on a surrogate and testing on the same axis is how a rung-1 finding gets dressed as more.

## 6. What this family could and could not claim

```
COULD:  "cell (L*, h*) is rank 1 of 21 against 20 arbitrary cells" -- a RUNG 1 result (AM-34), at CELL
        rather than HEAD granularity, which is strictly finer than anything in D32/D33/D34.
COULD:  lift D32's standing caveat "NOT a claim about any single (layer, head) cell" for ONE cell only.
COULD NOT: say the effect is single-layer. That needs the other 8 cells of that head measured, which is
        design (b)'s descriptive pass and is NOT a rank test.
COULD NOT: revise D32/D33/D34. A finer localisation does not retract a coarser one.
```

## 7. Order of work, when PR-CSI-013 is done

1. add `--knockout-cells` to `score_behavior.py` **(only once no arms are running)**, with its liveness
   contract and an identity field the gate can assert;
2. extend the argv gate's identity assertion to cells, and the dose expectation to `DOSE_UNIT / 9`;
3. run design (b)'s 11-arm descriptive pass on basket validation;
4. freeze the nomination rule **before** reading it, per S-248/S-250;
5. freeze the read, then launch the 23-arm confirmatory family on the held-out axis.

**Nothing in steps 1–5 may begin while PR-CSI-013's arms are in flight.**
