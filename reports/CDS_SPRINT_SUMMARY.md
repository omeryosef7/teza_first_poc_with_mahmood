# CDS sprint summary — confirmatory defensibility, 2026-09-01

**Self-contained.** Reading this requires no other document. Full log:
`external_md/CONFIRMATORY_DEFENSIBILITY_SPRINT_PLAN_AND_PROGRESS.md` (id namespace `CDS-`).
Branch `behavioral-causality-sprint`, `c5239c16..` .

---

## The one-paragraph truth

The sprint was asked to make the **existing** claims more defensible, not to find new ones. It did
three things. **(1)** It built the domain-level analysis this project had never run, validated it by
reproducing two published results exactly, and then found that **`C7` — demonstration-specificity,
the claim it set out to extend — does not survive its own stated independence unit**: every Qwen3
cell is incapable-by-construction or capable-and-null. **(2)** It therefore built the first
population on which that test is *capable* — 38 domains × 10 verified-disjoint demonstration sets —
screened three lexical pairs on **baseline only** against a floor fixed in advance, and replicated
demonstration-specificity **on Llama at the domain level**: ASR 0.39–0.42 → 0.1447, **−104 rows**,
against three seeded count-matched controls at **0, −9, −11**, domain sign test **p ≤ 2.6e-06**,
29–32 of 32–34 informative domains. **(3)** Adversarial audit then removed six of the sentences
around that result and the whole of a second, weaker headline. **`C7` is now cross-model and
cluster-level; it is also more narrowly scoped than it was this morning.**

## What was preregistered before any forward pass

`CDS-PR-001` (the two-stage Llama design, with the accept/decline rule **as executable code**),
`CDS-PR-002` (the cross-bank installation analysis), `CDS-PR-003` (the rescue interaction, declared
**outcome-exposed** rather than blind), `CDS-PR-004`+`A1` (`C1` at 38 domains, with what its arm may
**not** be used for if Stage 1 declined), `CDS-PR-005` (the Boombness figure), `CDS-PR-006` (an
independent lexical-pair replication, with its capability written down first).

## Results

| # | result | verdict |
|---|---|---|
| `R-005` | **`C7` fails at the domain level in every cell** — incapable-by-construction or p = 0.45–0.73. Row counts reproduce exactly. | scope, not refutation |
| `R-015` | Stage-1 screen: carrot **declines by one row** (0.0974 vs 0.10); basket 0.1220 and **button 0.3895** qualify | `PROCEED on button` |
| `R-018`/`REV` | **Demonstration-specificity replicates on Llama at 38 domains**, p ≤ 2.6e-06 vs each of 3 controls | **STRONG** |
| `R-019` | On that bank the same scope makes **refusal FALL** (−20 rows, p = 0.0034) | strongest form of `C2` |
| `R-016` | **`C1` replicates at 38 domains**, sign p = 0.0156 **= its attainable floor** | third domain-level confirmation |
| `R-010` | `C1` also holds at the domain level on `d10`, **both models**, both p at their floors | **the claim that survives** |
| `R-007` | Rescue **refusal** effect is **indistinguishable between models** (interaction 1 row, p = 1.000); **ASR selectivity p = 0.102 / 0.156** | half supported, half declined |
| `R-009` | Installation ≠ sufficiency survives only as a **matched-skeleton contrast** (2/24 vs 12/24, Fisher p = 0.0034) | scoped to one pair |
| `R-012` | The 220/0 readout statistic holds for the **0.1 transport gate**; **two cells clear `MASS_GATE`** | narrowed |
| `R-014` | **The domain ICC that had no estimator: −0.0123** (carrot), **0.1583** (button) | closes `RAH3-C-006` |
| `R-017` | Boombness-vs-ASR figure: between-level ρ **+0.557**, within-level **+0.098** | descriptive only |

## What was declined, and why that is the point

* **`carrot↔bomb` DECLINED FOR POWER by one row.** Every other criterion passed and the measured
  ICC says the design would have been adequately powered. **The floor was not moved.**
* **The n=8 cell was dropped on TOKENIZATION** — `match_ratio` min 0.000 — before any ASR at either
  dose existed.
* **The first-192-token secondary was declined with its number**: 86–92 % of completions exceed 192
  tokens and the arm differential would be 0.060 against a 0.02 gate.
* **The ASR selectivity interaction was declined as underpowered** rather than reported as a
  demonstrated model difference.

## The six sentences the audit took away

The **attainable floor** was quoted as the **p-value** (`< 1e-9` → **2.6e-06**) · the control deltas
were **sign-inverted** · "the controls are indistinguishable" describes differences **below the
judge's own re-run noise** (**51 label flips on byte-identical text**) · "non-demonstration masks"
are **99.7 % neutral filler preamble** · "the true independence unit" is 38 **demonstration pools
around ONE identical request** · and the `R-168` **falsification is retracted** (different,
dose-pooled population).

## Verification

Two independent verifiers, neither importing its producer. Stage 2: **349 checks, 0 failures**,
exact binomial derived **three ways** and cross-checked against brute-force enumeration;
**18/18** mutation classes red. Installation analysis: **176 checks, 0 failures**; **15/15** red.
The mutation harness **found four green holes in the first verifier**, all caused by an absolute
tolerance swallowing relative corruption of values down to 3e-19.

## Hazards worth inheriting

* ⚠ **A threshold published and enforced by nothing — five times in two sprints, and the fifth was
  inside the docstring claiming to have fixed the pattern.** Grep every published threshold for a
  code path that reads it.
* ⚠ **The attainable floor and the p-value must never be adjacent columns** without the reader being
  told which is which. That is how `< 1e-9` got published for 2.6e-06.
* ⚠ **Judge re-run noise on byte-identical text is 13.4 % of rows here.** Measure it on your own
  population before calling anything indistinguishable.
* ⚠ **A gate that passes on an empty selection is not a gate** (`CDS-C-001`), and **a precondition
  can fail for a defect in the checker** (`CDS-C-014`) — both happened tonight, in opposite
  directions.
* ⚠ **Amend a rule where it lives.** `CDS-PR-004` amended `CDS-PR-001` §2.4 from a later section,
  and the result was a genuine ordering violation that only the audit surfaced.
* ⚠ **Screen headroom on baseline before committing to a lexical pair.** `R-52` generalised one
  pair's collapse under a neutral preamble into a design law; the same preamble on a different
  lexeme reads **0.3895**.
