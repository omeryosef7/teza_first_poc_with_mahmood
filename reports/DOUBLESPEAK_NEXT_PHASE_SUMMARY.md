# Doublespeak next phase — concept-specific Boombness and surgical demonstration causality

**Self-contained.** Reading this requires no other document. Full append-only log:
`external_md/DOUBLESPEAK_CONCEPT_SPECIFIC_BOOMBNESS_AND_SURGICAL_CAUSALITY_PLAN_AND_PROGRESS_20260902.md`
(id namespace `DCS-`). Branch `behavioral-causality-sprint`, `c8263888..`.
Dates 2026-09-02 → 2026-09-03. Model **Llama-3.1-8B-Instruct** unless stated.

---

## The one-paragraph truth

The phase was asked whether an intuitive, **concept-specific** measure of "the codeword is becoming
the harmful concept" can be built and validated, and whether the demonstration-processing
computation that produces it is causally responsible for the attack. **The answer to the first is
no, to the second is half-yes, and the two together are the result.** A codeword→concept movement
exists and is **causally demonstration-dependent** — blocking the query span from the demonstrations
takes the model's own forced-choice reading of `button` from +5.19 to **−2.76** log-odds, a **sign
flip back to the literal meaning**, replicated on a second codeword, against a dose-matched control
that does nothing. That path is **remapping-specific**: the identical intervention barely moves the
cell where the word already *is* the concept (DiD −9.89 and −9.35 on two codewords, 37/38 domains,
p = 2.8e-10). But the representation is **not specific to the harmful concept** (knife/gun/club
match or exceed bomb) and **does not accumulate** across demonstrations.
**And the same intervention reduces the attack** — a
conclusion reached only after two reversals. The first control induced refusal (a channel `KO-3`
annihilates to zero), which masked the effect and produced a false null; against the one
**refusal-neutral** control of the three that exist, `KO-3` removes attacks with the direction
confirmed across two independent judgings, domain clustering (p = 0.0089), 24 of 34 non-tied
domains, and a composition-free endpoint on which `KO-3` sits below every control and the baseline.
⚠ **The magnitude is not established** — the selection criterion provably favours the
highest-attack control (r = −0.97), the judge's own re-run spread on byte-identical text reaches 18
rows, and the effect is absent in the pre-declared `dev` half. So: the mechanism is real,
demonstration-built, remapping-specific, and **behaviorally causal in direction**; gate `R5` is
passed at the query-span scope and **fails at the codeword-row scope**, and the magnitude awaits
replicate judging (`DCS-PR-005`).

---

## What was preregistered before any forward pass

`DCS-PR-001` (the `KO-1`/`KO-2` arms, the DiD estimand, and the decision rules) · `DCS-PR-001a` (the
DiD pairs by domain, not by prompt — recorded when the constraint was discovered, before outcomes) ·
`DCS-PR-002` (the specificity test moved to the readout channel, with its gates) · `DCS-PR-003` (the
`basket` bank's 3-row defect and its handling, written while the arms were still running) ·
`DCS-PR-004` (the mediation test, **with its power checked in advance** and both admissible outcomes
declared). The §1 preregistration itself was committed before any extraction, generation or outcome
column existed.

---

## ESTABLISHED RESULTS

| # | result | evidence | verdict |
|---|---|---|---|
| `R-010`/`R-011` | **The demonstration→query path is necessary for the remapping and specific to it.** `KO-3` (whole query span ↛ demonstrations, L6–14) drives the codeword cell from **+5.19 → −2.76** (`button`) and **+6.79 → −3.80** (`basket`) — a sign flip to the literal reading — while barely moving the cell where the word *is* the concept. **DiD −9.889 and −9.352, both 1+/37− domains, both p = 2.838e-10**, floor 7.28e-12 | 2 codewords × 6 arms × ~380 rows × 38 domains; dose-matched controls negligible; adversarially audited (`DCS-A-002`) | **REPLICATED, remapping-specific** |
| `R-012b` | **Refusal is annihilated by `KO-3`**: 42 → **0**, while the dose-matched control moves it the *other* way (42 → **75**). −75 rows vs control, **0+/26− domains, p = 2.98e-08** | as above | **STRONG, and endpoint-scoped** |
| `R-016` (dir. only) | **`KO-3` reduces attack against a refusal-neutral control.** Direction confirmed across two independent judgings (−36 and −41), domain-clustered permutation **p = 0.0089**, 24−/10+ domains, and a composition-free endpoint (attack rate among non-refused rows) where `KO-3` is **0.313** vs every control 0.384–0.473 and baseline 0.453 | 6 arms × 380; audited (`DCS-A-004`) | **DIRECTION ONLY** — magnitude retracted by `C-016c` |
| `R-002` | **The movement is NOT concept-specific.** Against `knife`/`gun`/`club`, three of four comparisons run the *other* way and every difference is inside the measured split-to-split band (median 0.015, p90 0.044) | 10 banks, dev + heldout | **evaluated negative** |
| `R-003` | **The shift does not accumulate.** Final occurrence > first in 32/32 cells, but demonstrations-only ρ **disagrees in sign between banks** (−0.048 vs +0.278) and the effect is flat in `n_examples` (7.01/7.25/7.10/6.54) | 2 banks × 32 layers, per-row, cross-fit | **evaluated negative** |
| `R-004` | **Null control fires exactly:** at `n_examples = 0` the paired `C−A` is `0.000e+00` at all 96 cells — correct, since A and C are byte-identical without demonstrations | 2 banks | **positive control** |
| `R-006` | `KO-1` (final codeword row ↛ demonstrations) is a **well-powered null on attack** (+11 rows, p = 0.597, floor 4.66e-10) and **halves refusal** (−21, 0+/13−, p = 2.44e-04 = its floor) | 6 arms × 380 | **null + refusal effect** |
| `R-005` | `KO-1` leaves the **mapping intact** (+0.278, 25+/13−, p = 0.073 on the preregistered sign test) | 3 arms × 380; audited (`DCS-A-001`) | **null** |

### The dissociation — ⚠ NARROWED by `C-015`

Every scope tested moves **refusal** by a large, well-powered margin:
`TSC-R-006` (Qwen3, `demo_processing_only`: all 150 refusals removed) ·
`DCS-R-007` (Llama, `target_surface_row_only`: refusal halved, p = 2.44e-04) ·
`DCS-R-012b` (Llama, `query_prefill_only`: refusal 42 → **0**, control 42 → **75**, p = 2.98e-08).

⛔ **But "and attack is not" is now FALSE at the scope that matters.** It holds for `KO-1`
(`R-006`/`R-014`: +11 rows on a control verified refusal-neutral, Δ = 0, zero attack→refusal
conversions — the mapping was never destroyed there either). It does **NOT** hold for `KO-3`:
against the refusal-neutral control the attack **does** fall (`R-016`, direction established).
⇒ **The dissociation is scope-dependent, and that is the finding.** Cutting the demonstrations off
the *codeword row* changes neither representation nor attack; cutting them off the *whole query
span* changes **both**. Refusal moves under every scope tested.

---

## EXPLORATORY / NOT CONFIRMATORY

* The `KO-1` readout **increase** (+0.363, p = 0.034 on the preregistered sign test) is a point
  estimate. Magnitude-aware tests over the same domains give p ≈ 2e-04 and clear Holm×7 — but the
  sign test is what `PR-001` registered, and ⛔ switching statistics because one returns a smaller p
  is the shopping this phase forbids.
* `R-009`: specificity at the `KO-1` scope is a **capable null** (DiD +0.503, p = 0.073), but it is
  a weak test of a weak effect and must not be read as evidence against specificity.
* The hypothesis that `basket`'s cell-`B` ceiling (+10.67 vs `button`'s +6.27) explains the failed
  "opposite directions" replication. **Not tested.**

## FAILED / PARTIAL REPLICATIONS

* ⛔ **"The two cells move in opposite directions" does NOT replicate.** On `button`, cell `B` moved
  **up** (+1.808); on `basket` it moves **down** (−1.466, 5+/33−). The general claim is about
  **magnitude, not sign**. `R-010`'s strongest rhetorical form — *"generic damage cannot selectively
  improve one cell"* — holds **only on `button`**, as does the argmax evidence (4→104 vs 21→6).

## UNDERPOWERED / CANNOT ANSWER

* ⛔ **`KO-2` on the ASR endpoint.** Cell `B` baseline is **10/380 = 0.0263**, so the maximum
  removable is 10 rows against a 17-row judge band. No outcome could have reached significance.
  The registered DiD reports `UNINFORMATIVE BY CONSTRUCTION, k_informative = 1`. **This was my
  preregistration error** (`C-007`): `PR-001` fixed everything except whether the control cell could
  move, which twelve committed artifacts would have said for free.
* The concept/topical endpoint throughout: **degenerate on these banks** (one distinctive word,
  values ∈ {0,1}); it is a concept-word presence test, not topicality.

## RETRACTED — never revive

| # | retracted claim | why |
|---|---|---|
| `C-010` | "The mapping is **constructed during demonstration processing**, not retrieved at the final codeword token" | The knocked-out token sits 10 tokens before the end and the readout is scored *after* it; every downstream position kept unblocked demonstration attention at all 32 layers. `KO-1` licenses only *"the final codeword token's own L6–14 demonstration attention is not necessary."* |
| `C-005` | `R-001`'s **L6–L12 peak** | Absent from the per-row standardized effect size, which is largest at L0 and declines. The peak exists only in a between-cell-mean distance ratio. |
| `C-008` | `R-005`'s **option-mass caveat** | Algebraically impossible: `logodds` is a difference of logsumexps over the full vocabulary, verified mass-invariant to 1.8e-15. The caveat *understated* the result. |
| `C-009`/`C-011` | "**The controls are inert**" | Negligible in magnitude (|Δ| < 0.31) but **not sign-null**: 31+/7− and 6+/32−. |
| `C-015` | **`R-012`'s null — "the mapping can be destroyed without the attack changing"** | Two independent defects. (a) Reported via a **domain sign test on row-paired data**; the correct McNemar gives p = 0.235, not 0.860, and the sign test's MDE is a **43 % reduction** — a 30 % reduction had power 0.10. (b) The dose-matched control suppresses attack **by inducing refusal** (19 direct `ATTACK→REFUSE`, refusal +33, p = 9.5e-07), a channel `KO-3` annihilates to **zero**, so the comparator is **not exchangeable**. Refusal-discounted: **−34 rows, McNemar p = 0.0051**. Status: **CANNOT ANSWER** |
| `C-016a` | "**All six `B-008` arms were judged in one invocation**" | **False.** Six processes, two batches, two commits. `d1` (batch A) 117 attacks vs `capped_d1` (batch B) **135** on **byte-identical text** — an +18 drift in the direction that inflates the headline contrast |
| `C-016b` | "**Four controls**" / "a family of six draws" | **False.** `capped_dK ≡ matched_dK` by construction here (`min(pool − demo) = +57`); verified 380/380 byte-identical. **Three** distinct draws exist. The promised six-point correlation would have been a fabrication |
| `C-016c` | `R-016`'s "**−36 attacks, p = 0.0034**" as a magnitude | Direction survives; **magnitude does not**. Selection favours the highest-attack control (r = −0.97), judge re-run spread reaches 18 rows, effect absent in `dev` |
| `C-004` | `R-003(b)`'s ρ figures | Quoted from the series *including* the query occurrence at 4 sampled layers; the demonstrations-only series over all 288 is the correct statistic. |
| `C-002` | "The `basket` replication is partly an illusion" | Measured exactly: cells `A` and `C` are **0.000** byte-identical across lexical banks. Only `B`/`E` share behavioral rows, and those are the cells with no codeword. `TSC-R-004` stands. |
| *inherited* | `d_surface` as validated, or as a GCG/MAC objective | Still **BLOCKED**. `R-012` closes the door for the new representation too. |

## NOVELTY — what is ours and what is not

`reports/DCS_LITERATURE_MATRIX.md`. ⛔ **The representation-convergence phenomenon is
Yona et al., "In-Context Representation Hijacking", ACL 2026 (arXiv 2512.03771)** — logit lens and
Patchscopes over 29 harmful requests. `R-001`/`R-010`'s *representational* half is a **replication
with a different instrument**, never a discovery, and their Appendix D (varying the codeword, ASR
flat) partly anticipates `R-002`. **What they have no version of is any internal causal
intervention** — their only causal manipulation is at the prompt level. Method provenance for the
knockout is Geva et al. 2023 (arXiv 2304.14767) and Ben-Tov, Geva & Sharif (TACL 2026).
"Representation ≠ behavior" is a 2026 consensus (Walsh & Barkett arXiv 2605.25151; Yin, Han & Li
ICML 2026), novel here only **as an instance**.
⇒ **The defensible novelty is the causal combination**: demonstration-block knockout **+** a
preregistered `intervention × condition` interaction with dose-matched controls **+** a *capable*
cross-family null **+** a CI-backed negative for a mechanistically derived attack objective.

## SCOPE — the line that accompanies every number

**38 domains × 2 codewords × 1 concept (`bomb`) × 1 model (Llama-3.1-8B-Instruct) × one layer band
(L6–14) × one dose.** That is 38 *contexts for a single mapping*, **not** 38 mappings. Measured
ICC ≈ 0.34, so domain is the correct independence unit.

## OPEN QUESTIONS

0. ⛔ **THE PHASE'S TOP OPEN EXPERIMENT (`DCS-PR-005`): what is the MAGNITUDE?** Direction is
   established (`R-016`, downgraded by `C-016`). The size is not: −36 is inflated by a selection
   criterion that provably favours the highest-attack control, the judge's re-run spread on
   byte-identical completions reaches **18 rows**, and the effect is absent in `dev` (p = 0.349)
   while present in `heldout` (p = 0.0018). Replicate judging is submitted with its decision rule
   fixed in advance.
1. **Which position retrieves?** `KO-3` cuts the whole query span and cannot separate the readout
   position from the ~10 intervening query tokens. A readout-row-only scope does not exist;
   the machinery added this phase makes it a small extension.
2. **Where do the 75 rows go?** `KO-3` eliminates refusal without buying attack success. What that
   text *is* has not been characterised.
3. **Does `R-010` hold on a second concept, and on Qwen3?** Neither run.
4. **Is the `basket` ceiling the reason "opposite directions" failed?** Untested.

## KNOWN DEFECTS

* `DCS-B-007`: per-row control-draw **positions** are not persisted, so control/demonstration
  disjointness is a **code guarantee, not an artifact fact**.
* `DCS-B-006`: after `KO-3` the two cells are not in comparable measurement regimes (cell `C` leaves
  the option set on 257/380 rows). The defense — the dose-matched control on the *same* prompts
  keeps mass at 0.798 — is strong but **must be argued in the text**.
* `DCS-B-003`: the L18 transplant result is neither retracted nor re-affirmed; **not citable**.

## VERIFICATION

Two headline findings each carry an independent adversarial audit that reproduced every published
number to the digit and attacked the named failure modes (`DCS-A-001`, `DCS-A-002`). The
`run_completeness_check` pre-commit guard **refused two commits** during the phase (377-vs-380 rows,
then non-uniform domain loss); ⛔ `--no-verify` was never used. All 9 deliverable guards and 341
guard tests pass at every commit. Three bugs were caught **before** they produced a result: a
position resolver that returned an empty span on 1032/1032 real rows, a pre-flight that declared the
new scope universally dead, and `CDS-R-020` reproduced exactly (ledgered in a baseline arm, fatal in
an intervened one).
