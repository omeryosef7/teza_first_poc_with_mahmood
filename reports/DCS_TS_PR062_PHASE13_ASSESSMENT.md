# PHASE 13 — assessment: can and should the representation-destruction ↔ downstream-use test run?

*2026-09-08. Written after PHASE 9's TEST read (job 869523, `R-131`/`R-132`) and before any PHASE 13
preregistration exists. Mandate §31 lists PHASE 13 as "Representation destruction ↔ downstream-use
test on the SAME large bank." `reports/DCS_TS_REMAINING_PHASES_GATING.md` recorded it as **BLOCKED on
PHASE 9**. PHASE 9 has now returned. This file is the decision that unblocking produced.*

## VERDICT

**PHASE 13 does NOT run. Recorded as CANNOT ANSWER ON THIS BANK, by the terms mandate §32 writes for
CLAIM E itself.** No preregistration was written; `configs/dcs_ts_pr062_phase13.json` deliberately
does not exist. No GPU is requested.

The reason is not that PHASE 9 came out negative. A negative PHASE 9 would have been a perfectly good
input to a mediation test — mediation of a null is a real question. The reason is narrower and it is
measured: **on the arm that moved the downstream readout, the mediator has no between-domain
variance, and on the arm where the mediator does vary, the readout did not move.** There is no arm on
this bank that supplies both halves of the correlation PHASE 13 is defined to compute.

---

## 1. Does PHASE 13's premise survive PHASE 9's result?

**No.** PHASE 13 asks for a domain-level association between *how much representation was destroyed*
(x) and *how much downstream use changed* (y). Take the two scope levels in turn, with the numbers.

### S1 — the mediator varies; there is no y to mediate

`h2a x S1` (button, layer 9, single position), 23 TEST domains:

| quantity | value |
|---|---|
| O2 delta (downstream semantic readout) | **−0.002997**, p = **0.807519** [attainable floor 9.999e-05] |
| C1 norm-matched random equivalence CI | [−0.008842, +0.007934], p = 0.511149 |
| O1 delta (scoped to the button bank only) | +0.391905, p < 9.999e-05 (**at the floor**) |
| conjuncts met | **1 of 4** |
| Holm | p = 0.807519 vs α = 0.01 → reject = **False** |
| realised dose | `frac_cellmean_spread_removed` = **0.1656**, `cell_residual` = {'C': 0.0936} |

The frozen verdict literal is **`[NEGATIVE]` DECODABLE BUT NOT CAUSALLY USED UNDER THIS
INTERVENTION**, and per claim-table ban 3.x-2 that sentence carries "under this intervention, at this
dose, without an upper-bound control" as part of the claim, not as a trimmable hedge — the H1
full-patch upper bound was never run and cannot be (donor concept installs in **0 of 113** domains).

For PHASE 13 the operative fact is the first row: the arm's O2 movement is −0.003 and it sits
**inside** the C1 band [−0.008842, +0.007934]. The y-variable of the mediation is, on this arm,
indistinguishable from zero and indistinguishable from what a random direction of the same norm does.
Regressing a mediator against that is regressing against noise.

Per claim-table ban 3.x-3, an S1-only null is additionally **uninformative on its own** —
`arXiv:2605.04061` reports single-position intervention at 0% transfer despite 100% probing accuracy
on this model family. So S1 is not evidence that there is nothing to mediate; it is an arm from which
no mediation can be computed either way.

### S2 — the readout moved a great deal; the mediator is a constant

`h2a x S2` (button, layers 7–14, all positions), 23 TEST domains:

| quantity | value |
|---|---|
| O2 delta | **−0.642195**, p < 9.999e-05 (**at the floor**); 21/23 domains; sign test p = 6.60419e-05 |
| O1 delta | +0.317962, p < 9.999e-05 (**at the floor**) |
| C1 norm-matched random equivalence CI | **[+0.115897, +0.206261]**, smallest p = 9.999e-05 (**at the floor**) |
| conjuncts met | **2 of 4** |
| Holm | p = 9.999e-05 vs α = 0.00833333 → reject = True |
| verdict | **`[NOT A CAUSAL RESULT]` — conjunctive criterion not met** |

Two independent things disqualify S2 as PHASE 13's x-arm, and the second one is the decisive one.

**(a) The equivalence control did not hold.** Conjunct 3 required the norm-matched random direction
to be equivalent to zero. It is not: its CI is [+0.115897, +0.206261], excluding zero, at the p-floor.
A norm-matched random direction edited at the same eight layers and all positions **moves this
readout by a measurable amount**. That establishes, on our own data, that the S2 readout is sensitive
to generic perturbation at S2 dose. It does not matter for this purpose that the control's sign is
opposite the arm's and its magnitude ~3× smaller: the frozen rule asked for equivalence, equivalence
failed, and re-reading a failed conjunct as a passed one after the outcome is visible is the prose
form of editing a frozen analyzer to rescue an outcome (`R-129`, mandate §21). **A mediation analysis
built on S2 would be measuring how much we perturbed the residual stream, not how much of the
representation we destroyed.**

**(b) The mediator has no between-domain variance at S2 — and this is fatal on its own.** Recomputed
by me from the frozen liveness stream (`PR057_LIVENESS.jsonl`, `realised_dose_l2_per_cell`), 23 TEST
domains, using a domain-level one-way variance decomposition:

| arm | k domains | records/domain | domain-mean dose | between-domain SD | CV | **ICC** |
|---|---|---|---|---|---|---|
| `h2a_s2_projout_button` | 23 | 80 | 9.6322 | 0.1843 | **0.0191** | **−0.0114** |
| `h2a_s2_projout_basket` | 23 | 80 | 9.6034 | 0.1778 | 0.0185 | −0.0115 |
| `h2a_s1_projout_button` | 23 | 10 | 1.3582 | 0.4174 | 0.3073 | **0.2753** |
| `h2a_s1_projout_basket` | 23 | 10 | 1.1670 | 0.3699 | 0.3170 | 0.2717 |

At S2 the realised destruction dose is **constant across domains to within 1.9%**, and its
domain-level ICC is **−0.0114** — negative, i.e. between-domain variance is not merely small but
statistically indistinguishable from none once within-domain variance is accounted for. PHASE 13's
predictor, on the only arm with a large downstream effect, **is a constant**. A correlation of a
constant against anything is undefined, not underpowered. At S1 the dose genuinely does vary
(ICC 0.2753) — but S1 is the arm whose y is −0.003.

**So the answer to (1) is: there is no representation-destruction effect left to mediate that is
attributable to the representation.** The one arm with attributable-looking mediator variance produced
no downstream movement; the one arm with large downstream movement has a degenerate mediator and a
control that demonstrably moves the same readout. Mediation on either measures something other than
what PHASE 13 names.

I am not saying, and this file must not be quoted as saying, that the concept-specific direction is
not causally used (claim-table ban 3.x-1), that S1's null shows the direction is unused at that site
(3.x-3), that H1 showed no effect (3.x-4 — H1 **never ran**), or that PHASE 9 tested the concept axis
with its preregistered controls (3.x-7 — 6 of 36 selected h2 arms were unbuildable, and H1, H2b, C2
are absent entirely).

---

## 2. PHASE 13 against its own gate

**§31 states PHASE 13 without an inline "only if".** Verbatim:

> PHASE 13
> Representation destruction ↔ downstream-use test on the SAME large bank.

Compare PHASE 12, which carries its precondition in §31 itself:

> PHASE 12
> **Only if representation story is solid:**
> row-randomized behavioural controls; mapping_use; ASR.

So PHASE 13 has no §31 gate. **Its gate is in §32, in the claim it exists to support.** CLAIM E is
PHASE 13's claim, one-to-one, and §32 writes the precondition there, verbatim:

> CLAIM E:
>
>     representation destruction predicts behavioural change.
>
> Only if:
> - SAME bank;
> - adequate power;
> - valid controls;
> - domain-level estimator.
>
> **Otherwise:**
> **CANNOT ANSWER.**

Four conditions. Against PHASE 9's actual result:

| §32 CLAIM E condition | status | evidence |
|---|---|---|
| SAME bank | **MET** | `ts116m`, 113 analysed, 23 TEST; PHASE 9 ran on exactly this bank |
| domain-level estimator | **MET as a requirement, and enforceable** | PHASE 9's O1/O2 are paired domain-level contrasts with domain permutation; row-level has measured FPR 0.2000 here and is excluded |
| **valid controls** | **NOT MET** | C1, the norm-matched random control the primary claim rests on, is **not equivalent to zero at S2** (CI [+0.115897, +0.206261], p at floor); the H1 full-patch upper bound is unconstructible; H2b and C2 are absent, all three entering Holm at p = 1.0 as CANNOT ANSWER BY CONSTRUCTION |
| **adequate power** | **NOT MET** | at S2 the mediator's domain-level ICC is −0.0114 (no x-variance); at n = 23 TEST domains a domain-level correlation needs **r ≥ 0.556** at α = 0.05 and **r ≥ 0.652** at the Holm first step α = 0.00833333, both at 80% power |

**Two of the four conditions fail on measurements already in hand. §32's own disposition for that is
the word CANNOT ANSWER, and it is written into the mandate rather than chosen here.** Per the gating
file's standing rule — *"A precondition written into the mandate is not a hurdle to be argued past"* —
that ends the matter, and I am not arguing past it.

**A second, independent gate closes the other reading.** "Downstream use" admits two readings and both
roads are blocked:

- **Narrow reading — downstream = the O2 semantic readout.** Then PHASE 13 adds nothing PHASE 9 did
  not already run: PHASE 9 *is* destruction → readout, twice, at two scope levels, with matched
  controls and a domain-level estimator. The only genuinely new quantity PHASE 13 would contribute is
  the cross-domain correlation, and §1(b) shows the S2 predictor is constant and the S1 outcome is
  zero. There is no new question left in this reading.
- **Broad reading — downstream = behaviour, i.e. `mapping_use` / ASR, which is CLAIM E's literal
  word "behavioural".** Then PHASE 13 requires **PHASE 12's instrument**, and PHASE 12 is
  **GATED OFF**, reopening on its own recorded terms "only on a PHASE 9 positive". PHASE 9 returned
  `[NEGATIVE]` at S1 and `[NOT A CAUSAL RESULT]` at S2. Neither is a positive. Running PHASE 13 in
  the broad reading would run PHASE 12's measurement under a different phase number, which is exactly
  the argue-past-a-precondition move the gating file forbids.

---

## 3. What PHASE 13 could and could not say, given PHASE 9's actual result

**Could say, if it ran anyway:**

- Nothing about S2 attributable to the representation. Any S2 coefficient would be read against a
  predictor that is constant to 1.9% across domains and a readout demonstrably movable by a
  norm-matched random direction at the same dose.
- At S1, an honestly-reported **null association with its dose attached**: "at a realised dose of
  16.56% of the cell-mean spread, per-domain destruction magnitude did not predict per-domain change
  in the semantic readout." That sentence is true, publishable under §32's clean-negative rule, and
  worth roughly nothing, because the y it correlates against is −0.003 ± a band that contains zero —
  the null is a restatement of PHASE 9's S1 row, not new evidence.
- Nothing about behaviour at all, since the behavioural instrument is gated off.

**Could not say, at any outcome:**

- That representation destruction does or does not predict behavioural change. That is CLAIM E, and
  §32 assigns it CANNOT ANSWER when the controls and power conditions fail, which they do.
- That a positive mediation coefficient implicates the concept axis. `arXiv:2311.17030` bounds this
  before any run: a subspace effect can run through dormant or disconnected features, and the
  standard control is comparison with full activation patching — the H1 arm that cannot be built here.
  Separately, `cos(v_knife, v_gun) = 0.91–0.95`, so `v_bomb_specific` loads −0.55 to −0.68 on a
  generic demonstration-presence axis and only 0.22–0.44 on `v_bomb`; the axis is not purely concept
  identity even when the intervention works.
- That the mediation is scoped beyond the development codeword. O1 is scoped to `button` only; the
  basket arms have **no C1 control at all** after the `R-132` cross-bank fix, and their conjunct 3 is
  FALSE by construction.

---

## 4. The single biggest threat to PHASE 13's interpretability

**It is not power, and it is not the failed control. It is that the mediator is fixed by design and
its residual between-domain variation is not representation content.**

PHASE 13 is written as a mediation, but no arm on this bank randomises or grades the destruction dose.
Every domain receives the *same* projection of the *same* frozen direction. Whatever between-domain
variation in `realised_dose_l2_per_cell` remains is a property of how large each domain's activations
happen to be at those sites — prompt length, token composition, domain difficulty — not a property of
how much concept was installed or removed. So even in the S1 arm, where the dose does vary
(ICC 0.2753), the cross-domain regression is **observational and confounded by domain difficulty**,
and the same confounders plausibly drive the outcome directly. A significant coefficient would be
attributable to domain difficulty at least as readily as to representation destruction, and this bank
contains no instrument that separates the two.

This is `R-097`'s lesson in a second form. `R-097` was about a mediation question with no `y` measured
where `x` lives — a CANNOT ANSWER, not a null. PHASE 13's version is a mediation question whose `x` is
**not experimentally varied at all**: at S2 it does not vary, and at S1 what varies is a nuisance.
Naming that now, before a GPU is requested, is cheaper than naming it after.

---

## 5. What would have to change for PHASE 13 to become answerable

None of these is a code change; each is a new experiment and a new preregistration (mandate §21,
"New design = new preregistration").

1. **A graded dose ladder, not a single dose.** Vary α over a preregistered ladder (e.g. partial
   projection at 0.25 / 0.5 / 0.75 / 1.0 of the component) so that `frac_cellmean_spread_removed`
   is an **experimentally assigned** predictor with real designed variance, orthogonal to domain
   difficulty because it is randomised *within* domain. This converts PHASE 13 from an observational
   cross-domain correlation into a dose–response test, which is the only form in which the mediator
   is attributable. It is also the only repair that survives §4.
2. **A C1 control that is equivalent to zero at the working dose**, or a working dose low enough that
   it is. Right now S2's dose is above the level at which a random direction of the same norm moves
   the readout; S1's is below the level at which anything moves it. The ladder in (1) is also how one
   would find whether a window between the two exists — and it may not.
3. **An upper bound.** H1 is unconstructible on this bank because the donor concept installs in 0/113
   domains. Either a bank whose donor concept installs, or an accepted permanent scope limit stated in
   every sentence the phase produces (`arXiv:2311.17030`).
4. **A behavioural `y`, only if PHASE 12's gate reopens.** CLAIM E says "behavioural". Without PHASE
   12 the broad reading of PHASE 13 is unavailable regardless of anything above.
5. **More domains, or a fresh split.** The 23 TEST domains have now been read once (job 869523). A
   second confirmatory read of the same 23 for a new primary claim is a multiplicity and independence
   problem that no analysis fixes after the fact. At n = 23 the domain-level correlation MDE is
   r ≥ 0.556 (α = 0.05) to r ≥ 0.652 (α = 0.00833333) at 80% power; at n = 113 it would be r ≥ 0.261
   to r ≥ 0.320. Any serious PHASE 13 needs the larger population and a split built before the
   outcome exists.
6. **Installation as a stratifier.** Whatever runs, mandate §15 binds: on the concept-free channel the fraction of 113 domains
   reaching `concept_binary_prob >= 0.5` is bomb 0.619, knife 0.000, gun 0.009 (`R-116`). Non-installing domains are a
   **stratification variable or a descriptive limitation, never a post-hoc exclusion.**

---

## 6. GPU cost, for the record

PHASE 13 is not being requested, so this is an estimate of the counterfactual, given so the decision
not to spend is a priced decision rather than an assumed one.

**Measured baseline.** PHASE 9's H2 confirmatory run (job 869523): 30 arms, 6,900 rows, **54.3 min**,
1 model load, on one L40S — and that was with `--no-generate` and `--max-new 8`, i.e. **scoring only,
no free generation**. The Q1 validation run was 2 arms / 460 rows / 3.7 min. Queue cost is the larger
term in practice: job 867233 pended **42 minutes** on a fully-held six-node L40S pool (`C-125`), and
there is no L40S outside those six nodes.

**A minimal repaired PHASE 13**, i.e. option (1) above — a 4-level dose ladder × 2 scope levels ×
2 codeword banks, plus C1 draws at each ladder level, on 23 TEST domains at 10 rows/domain — is on the
order of **60–80 arms and ~14,000–18,000 rows**, scoring only: **≈ 2.0–2.5 GPU-hours of compute**,
realistically **4–6 wall-clock hours** with queue. That is the cheap version, and it still cannot
answer CLAIM E because it has no behavioural `y`.

**A PHASE 13 that answers CLAIM E as written** needs generation for `mapping_use`/ASR. PHASE 9's
per-row cost is a scoring cost at `--max-new 8`; a behavioural readout needs materially longer
completions plus a judge pass, which on this repo's history runs **10–30×** the scoring cost per row.
That puts it at **20–60 GPU-hours plus judge API**, on a fair-share pool where a 4-minute job waited
42 minutes. **Spending that behind a gated-off PHASE 12, a failed C1 equivalence, an unconstructible
upper bound, and a mediator with ICC −0.0114 would be the most expensive way this sprint could
produce an uninterpretable number.**

---

## 7. Disposition

- **PHASE 13: CANNOT ANSWER ON THIS BANK.** Not skipped, not deferred — the decision and its authority
  (mandate §32, CLAIM E's own "Otherwise: CANNOT ANSWER") are recorded here.
- `configs/dcs_ts_pr062_phase13.json` **not written**, by decision. Writing a FROZEN preregistration
  for a design whose predictor is a constant would be preregistration theatre.
- No GPU requested. No SLURM job submitted or cancelled in producing this file.
- Claim-table row for CLAIM E should read **CANNOT ANSWER**, with this file as evidence, caveat
  "mediator ICC −0.0114 at S2; C1 equivalence failed at S2; no upper bound; behavioural instrument
  gated off with PHASE 12". Amending `reports/DCS_TS_CLAIM_TABLE.md` is a separate, owner-authorised
  edit — this file does not make it.
- The recorded reopening condition is **option (1) plus (2)**: a graded, within-domain-randomised dose
  ladder that finds a working dose at which C1 is equivalent to zero. If no such dose exists, PHASE 13
  is CANNOT ANSWER permanently on this bank, and that too is a result.

**Numbers reproduced in this file that I computed rather than copied:** the four ICC / CV rows in §1
(from `outputs/boombness/score_behavior/ts116m_pr057_h2a_{s1,s2}_projout_{button,basket}_*/PR057_LIVENESS.jsonl`,
field `realised_dose_l2_per_cell`, one-way domain decomposition, 23 domains each, 0 missing values)
and the correlation MDEs in §2 and §5 (Fisher-z, two-sided, 80% power, n = 23 and n = 113). Every
other number is quoted from `R-127`–`R-134`, `reports/DCS_TS_CLAIM_TABLE.md`,
`reports/DCS_TS_PHASE14_LITERATURE_UPDATE.md`, or the PHASE 9 verdict as reported.
