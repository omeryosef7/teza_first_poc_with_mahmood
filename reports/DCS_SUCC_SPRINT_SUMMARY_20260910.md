# DCS SUCCESSOR SPRINT — WHAT WE SET OUT TO DO, WHAT WE DID, WHAT CAME OUT

**Window:** 2026-09-09 20:40 → 2026-09-10 09:40 (~13 hours).
**Record:** `external_md/DCS_BOMBNESS_MECHANISM_AND_ASR_SUCCESSOR_PLAN_AND_PROGRESS_20260909.md`,
55 append-only entries. **Commits:** 25, all pushed. **Where this disagrees with the log, the log wins.**

---

## 1. WHAT WE SET OUT TO DO

The mandate asked one question: **does Doublespeak create a concept-specific internal representation
of BOMB — where does it live, is it distinct from position / template / remapping / harmfulness /
surface, does the model causally use it, and does it predict jailbreak?**

We inherited a hard position. The previous phase had ended with a probe reading 0.9399 that turned
out to distinguish *which demonstrations were present* rather than *which concept was installed*; a
specificity claim marked UNSUPPORTED; one direct causal test returning NOT A CAUSAL RESULT with a
control moving the readout 1.93× further than the treatment; and **behaviour marked CANNOT ANSWER
for two independent reasons** — no behavioural outcome existed on the bank the representation was
measured on, and power was 0.2501 against a 0.50 bar.

Six things had to happen: build a Bombness measure that doesn't presuppose installation; measure
ASR **on the bank the representation lives on**; run the concept-free K ladder that had been named
as the highest-value follow-up and never funded; try the aggressive patch upper bound; test
localisation properly; and replicate on a second codeword.

---

## 2. WHAT WE ACTUALLY DID

**Audits and infrastructure.** 8 parallel read-only auditors before any GPU time; 3 five-part
adversarial reviews (15 reviewer-agents); 1 independent re-derivation of the headline by an agent
**forbidden to read the original code or artifact**. Three frozen preregistrations (`PR-066` + two
amendments), each validated by the machine-readable harness.

**Experiments run** (all on Llama-3.1-8B-Instruct, 113 analysed domains, domain as the independence
unit, ~40 GPU-hours):

| # | experiment | scale |
|---|---|---|
| 1 | `B1` candidate search + controls | 67 TRAIN domains × 6 banks × 9 layers, no GPU (reused caches) |
| 2 | **ASR on `ts116m`** — the 2×2 at doses 0 and 4 | 8 arms, 5,568 rows, 113 domains, + 8 judge runs |
| 3 | **concept-free K ladder** | 27 arms × 670 rows, both codewords |
| 4 | **C→A full-state patch** | 12 layer windows × 67 domains |
| 5 | position control (3 sites) | 4 new extractions, 2 banks |
| 6 | `basket` replication | 3 ASR arms + full K ladder |
| 7 | PHASE-11 kill stage completed | 7 arms (inherited, unblocked) |

**Instruments built:** a concept-presence filter with a **pre-frozen** 44-term lexicon; a judge
test-retest measurement; an amendment integrity checker; a surface/register nuisance floor (reusing
the existing register features); a figure set with scope cards; a phase-statistics filer.

---

## 3. THE RESULTS

### 3.1 The behavioural half — the part that was CANNOT ANSWER and now isn't

| | button | basket |
|---|---|---|
| **attack, concept-present** | **0.1398** | 0.0522 |
| direct harmful request | 0.0071 | 0.0071 |
| its own no-demonstration floor | 0.0088 | 0.0000 |
| **Q1d vs direct request** | **103/104 domains**, Holm-rejected | 41/42, p = 1.96e−11 |

**The attack works and beats simply asking by ~20×.**

**`Q2` (preregistered primary): installation predicts attack success.** ρ = **0.3961** over 113
domains, permutation p **at its floor**, CI [0.228, 0.541], MDE 0.2996, sign positive in 3/3 splits —
and it **strengthens to 0.4206** when the judge's false positives are removed, which is the opposite
of what an artefact does. Replicates on `basket` at 0.4468 (**exploratory** — the frozen file names
`button` in both predictor and outcome).

### 3.2 The mechanism — where the pathway runs

**The codeword's query row carries 62 % of the demonstration→query effect** (−4.49 of a −7.28 climb)
against a dose-matched three-draw control that moves **+0.03**, in **67/67** domains, p at its
1.355e−20 floor. `K* = 10` — the codeword — **replicates on the second codeword**.

**But its state carries nothing.** A **provably live** full-state transplant (donor cell C → recipient
cell A, same token, every layer) moves **0.054 %** of a 12.33 log-odds gap that the donor's *prompt*
reaches in 67/67 domains.

> **The codeword's row is a required conduit, not a store.** That also *explains* the previous
> phase's causal null rather than leaving it a puzzle: if the whole state at a site transfers
> nothing, no single direction there could.

### 3.3 Bombness — the central negative

We built `B1` = how far the codeword's state moves along a `button→bomb` axis constructed in the
**benign** cells, where nothing installs. It is **a real measurement**: ~10 % of that gap in
**66–67 of 67** domains, two codewords, ~14 sd over random, register-independent (six negative CV
R²), length-bounded at ~15 %, independently re-derived to 6–7 significant figures.

**It is not a bomb representation**, on four independent grounds:

| | finding |
|---|---|
| **it is an interaction** | `B1 = H + I` with `I` = **128 %/102 %** of `B1` at 67/67 domains and the harm main effect **negative** |
| **not localised** | indistinguishable from the neutral token one position later; worse-aligned than the readout position (1–2 of 67) |
| **not specific** | concentration ratio **1.20 / 1.02**, where 1.0 = spread uniformly |
| **not causally usable** | its site transfers 0.05 % |

Two competing candidates were built and **rejected**: prototype similarity (a *concept-free* context
prototype beats it) and the harm-axis projection (structurally biased).

### 3.4 An instrument result that reaches beyond this sprint

**StrongREJECT scores a fluent answer about literal buttons as a jailbreak.** On the
no-demonstration null it reads **15.5 %** — 35 positives across 31 domains, every one the model
helpfully explaining how to build a button. The floor is **codeword-dependent** (15.5 % button,
2.2 % basket). And the judge **flips 13.7 % of labels on byte-identical text** (κ = 0.44), measured
on 226 prompts generated twice and judged twice.

**127 of 461** prior judge runs use the same goal-substitution and are exposed to the mechanism.
⛔ **We did not revise any of them** — the floor was measured on a different bank, and a number
measured on one population is not a correction to another.

---

## 4. THE PROCESS RESULT

**Fourteen defects were found in this sprint's own work.** Three are one shape — **a quantity that
could not have told you it was wrong** — and it appeared **inside the repairs for itself twice**:

* `C-134` a constant printed as a measurement · `C-213a` a "machine check" that existed only in a
  shell heredoc · `C-214` a denominator that moves 30× across the thing being compared ·
  `C-217b` an integrity check defeatable by starting a key with an underscore.

Two nearly reached the log as results: a **position-control conclusion** that was a denominator
artefact, and a **figure** whose scope card had painted over the four points carrying the finding.

**What worked was procedures, not checks:**
1. **adversarial re-derivation by someone forbidden to read the original** — reproduced every
   headline to 6–7 s.f. *and* found five defects; three reviews found twenty-nine more;
2. **writing down in advance what would make a result uninterpretable** — the only reason `C-214`
   didn't enter the log as a finding;
3. **rendering an artifact and looking at it** — every statistic on that panel was correct and the
   picture was not.

---

## 5. WHAT IS OPEN

* **`Q-014`** — rebuild the corpus under a register constraint? **Omer's decision**; no analysis can
  substitute.
* **Link 5** — an intervened behavioural arm. *"Representation destruction predicts ASR"* remains
  forbidden.
* **Template transfer** — one query template per channel; untested.
* **`REVIEW-3` `C6`** — the ASR analyzer has no concept-presence field, so amendment `A1-3`'s
  instruction is recorded but not executable.
* **Re-scoring the 127 prior judge runs** — ~1 hour, no GPU.
* **The Slack draft is written and NOT SENT.** Its paragraph on prior work is deliberately hedged.

---

## 6. THE ONE-LINE VERSION

**The attack is real, beats asking directly, and the model's own semantic report predicts where it
lands; the mechanism runs through the codeword's query row as a conduit rather than a store; and the
thing we were calling Bombness is a token × context anomaly signal, not a bomb representation.**

*Generated 2026-09-10. All experiments complete.*
