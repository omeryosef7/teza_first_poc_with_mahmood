# DCS SUCCESSOR PHASE — FINAL REPORT

Answers to successor-plan **§43 A–N**, self-contained. Every number carries an entry id from
`external_md/DCS_BOMBNESS_MECHANISM_AND_ASR_SUCCESSOR_PLAN_AND_PROGRESS_20260909.md` and an artifact
path. Where this report and the log disagree, **the log wins**.

**Scope, once.** One model (Llama-3.1-8B-Instruct, rev `0e9e39f249a16976918f6564b8830bc894c89659`,
eager, bfloat16), one bank family (`ts116m`), **two codewords** (`button` development, `basket`
replication, **never pooled**), **bomb only** (knife installs 3/113, gun 1/113 — arms requiring them
are unconstructible), **113 analysed domains**, frozen split 67/23/23, **domain as the independence
unit throughout**. Register remains a stated corpus limit (`Q-014`, undecided by Omer).

---

## A — What is our best operational definition of Bombness?

**`B1` = ⟨h_C − h_A, v̂_lex⟩ / ‖mean(h_E − h_A)‖**, where `v̂_lex` is the leave-one-domain-out
direction from the codeword token to the concept token, built in the **benign** cells (`A`→`E`)
where nothing installs and nothing needs to.

This is Matan's §2.1 question made arithmetic: *how far does the codeword's state move along a
`button → bomb` axis?* It was chosen because it needs **no installation to construct** — which is
what made it usable when `R-116` showed knife and gun never install.

**Two competitors were built and rejected.** `B3` (prototype similarity) — ⛔ **REJECTED**: a
context-only prototype containing **no concept token** beats it at every layer ≥ 8 (0.0515 vs
0.0429, `S-003a`). `B1_harmref` (the same shift on the harm-context axis) — ⛔ **not a valid test**:
structurally biased by a shared incongruity term (`S-003c`).

## B — Why do we believe it is BOMB-specific?

⛔ **We do not.** This is the phase's central negative and it was reached in four steps, three of
them corrections to our own earlier claim:

1. `S-002` reported *"90.8 % of the alignment lives in the part knife and gun cannot express"*.
2. `C-208b` **withdrew** that as a specificity statement: specificity requires the residual bomb axis
   to be traversed **more** by the bomb shift than by the others, and that cell had never been
   computed. Computed: knife's shift reaches **59 %** of bomb's on the residual bomb axis.
3. `C-215`/`C4` showed the number was **in the wrong units** — in comparable units residualising
   **REDUCES** the bomb shift by **9.2 %** (button) and **27 %** (basket), and 0.9082 is exactly that
   reduction ratio.
4. `S-009` gave the statistic the question needs — **projection retained ÷ axis retained**, where
   **1.0 = spread uniformly**: **1.202** on button, **1.025** on basket.

> **20 % concentration on the development codeword, 2 % on the replication codeword.** No
> specificity claim is licensed.

## C — Where is it represented?

⛔ **Not at the codeword.** On the position-portable cosine (`C-214` established gap units are not
portable — the reference gap shrinks up to **30×** downstream), `B1` at the codeword is
**statistically indistinguishable from the neutral token one position later** (mixed signs, 34–44 of
67 domains, p = 0.014–1.0) and **worse-aligned than the final prompt token** (−0.20, **1–2 of 67
domains**, p ≈ 1e−17…1e−19), on both codewords at every layer (`S-008`).

In **raw** projection the codeword *is* the largest site through L12 — the shift is **biggest at the
codeword and best-aligned at the readout position**. Both are reported; neither is quoted alone.

## D — When does it appear across layers?

Rises monotonically from L6, peaks at **L11–L12**, decays by L14 — the same shape on both codewords
independently (`S-002`). ⚠ **The peak layer is an argmax over a 9-layer TRAIN grid** (`D-006`);
selection inflates it ~30 % (L6 = 0.066, L14 = 0.071 against L12 = 0.104), and any confirmatory test
must inherit L = 12 / L = 11 frozen.

## E — Localized to the codeword, or global prompt gist?

**Neither, exactly.** It is not localised (C). But it is not uniform either: the raw displacement
peaks at the codeword and the *alignment* peaks downstream. The accurate statement is that
**whatever `B1` measures accumulates downstream of the codeword, toward the position where the
answer is produced.**

## F — Does the concept-free semantic interpretation track it?

**Yes, at the domain level, and this is the phase's strongest positive.** Per-domain installation
predicts per-domain attack success: **ρ = 0.3961** over 113 domains, permutation p **at its
9.999e−05 floor**, CI [0.228, 0.541], declared MDE 0.2996, sign positive in **3 of 3** splits
(`Q2`, preregistered, ENTRY 037). It **strengthens to 0.4206** when the judge's false positives are
removed (`C-215`) — the opposite of what an artefact would do. It replicates on `basket` at
**0.4468** (⛔ **EXPLORATORY**, `C-217c`).

⛔ But the predictor is **installation**, the model's own concept-free report — **not `B1`**. And
`B1` is **not** a proxy for installation: `basket` has the **larger** `B1` (0.1366 vs 0.1044) and
**half** the installation (46/113 vs 92/113).

## G — Does demonstration→query information flow create or expose it?

**The pathway runs through the codeword's query row, and this replicates.** On a readout that never
names the answer, adding that one row to the attention cut moves the readout **−4.49** — **61.7 %**
of the whole climb — against a dose-matched three-draw non-demonstration control that moves
**+0.03**, in **67/67** domains, p at its 1.355e−20 floor (`R-205`). `K* = 10` — the codeword —
replicates on `basket` (`R-208`).

⚠ Its **share** does not replicate (61.7 % → 39.5 %), and basket's channel sits at **0.051** against
the 0.05 reportability gate. ⛔ The frozen shape rule returns **`NEITHER`** (button) and **`RAMP`**
(basket); **"step" is not used**.

## H — Can we causally manipulate it?

⛔ **No, at this site.** Donor→recipient **full hidden-state** transplant, cell C → cell A, same
domain, same family, **same codeword token on both sides**, every layer window, 67 domains
(`S-007`):

```
donor_ceiling        +12.3312 log-odds   67/67 domains   p at its floor
self_swap_noop         0.0000            0/67
transplant | all      +0.0066  = 0.054 % of the gap   32/67   p = 0.81
transplant | best     +0.0433  = 0.351 %              41/67   p = 0.086
```

**Liveness proved per row**: the logit-lens columns take the donor's *exact* value at every read
layer inside the patched window. The patch works; the reading does not move.

## I — Are the causal effects larger than matched controls?

**The K-ladder pathway: yes, decisively** — −7.17 against a dose-matched control at +0.03.
**The state transplant: there is no effect to compare** (H).

## J — Does manipulating it change ASR?

⛔ **NOT TESTED.** No intervened behavioural arm was run. Plan §32's **Link 5 is not established**,
and *"representation destruction predicts ASR"* remains forbidden.

## K — Does it transfer across codewords / templates / domains?

**Codewords**: the attack replicates (`R-207`), `Q2` replicates (exploratory), `K* = 10` replicates
(`R-208`) — but **specificity does not** (1.02), the codeword's ladder share does not (39.5 %), and
basket's channel is at its floor. **Domains**: yes — 66–67 of 67 for `B1`, 67/67 for the ladder.
**Templates**: ⛔ **not tested.** One query template per channel; a declared scope limit.

## L — What alternative mechanism is supported?

**The codeword's query row is a required CONDUIT, not a STORE.** Cutting its access to the
demonstrations destroys 62 % of the semantic report (G); copying its entire state transfers 0.05 %
(H); its state is no better aligned than its neighbour's (C). The reading is **recomputed** from the
demonstration block at the position where the answer is produced.

And **`B1` itself is the token × context interaction**: `B1 = H + I` with `I` = **128 % / 102 %** of
`B1` at **67/67** domains and the harm-context main effect **negative** (`C-208a`). Length cannot
produce it — the `seq_len` deltas of `C−A` and `B−E` are distributionally identical, so it cancels
exactly in `I`.

⚠ **This account is not forced by the data.** It is the simplest reading of four results; `REVIEW-3`
was asked to name alternatives and the log carries them.

## M — What can we confidently tell Matan and Mahmood?

1. **The attack works and beats asking directly** — 103 of 104 informative domains, ~20× the direct
   request on the corrected outcome.
2. **The model's own semantic report predicts where it lands** — ρ = 0.396, preregistered, powered,
   strengthening under correction.
3. **We know which row of the prompt the mechanism runs through** — and that it is a conduit, not a
   store.
4. **"Bombness" is not a bomb representation.** We built the measurement, it is real and
   reproducible, and it is an anomaly signal.
5. **The ASR instrument needed repair before any of this was quotable** — a 15.5 % false-positive
   floor on `button`, 2.2 % on `basket`, and a judge that flips **13.7 %** of labels on
   byte-identical text (κ = 0.44).

## N — What claims are still forbidden?

⛔ "the codeword is represented as BOMB" · "Bombness is localized at the codeword" · "the probe
measures concept identity" · "remapping and concept identity are separable axes" · "the concept
direction is causally used" · "Bombness predicts jailbreak" · "representation destruction predicts
ASR" · any ASR difference below **0.1372** · any pooled button+basket number · any knife or gun ASR
on this bank · **"90.8 % bomb-specific"** (withdrawn twice, finally quantified at 1.20 / 1.02) ·
**"the codeword carries the installed reading"**.

---

## The transferable output

Fourteen defects were found in this phase's own work (claim table §4). Three are one shape —
**a quantity that could not have told you it was wrong** — and it appeared **inside the repairs for
itself** twice (`C-213a`, `C-217b`). The two defences that worked are **procedures, not checks**:

* **adversarial re-derivation by someone forbidden to read the original** (`A-103` reproduced every
  headline to 6–7 s.f. *and* found five defects; three reviews found twenty-nine more);
* **writing down in advance what would make a result uninterpretable** — which is the only reason
  `C-214`'s denominator artefact did not enter the log as a finding.

A third earned its place late: **an artifact that renders must be rendered and looked at** (`C-216`,
`C-218`). Every statistic on that panel was correct and the picture was not.

*Generated 2026-09-10. All experiments complete.*
