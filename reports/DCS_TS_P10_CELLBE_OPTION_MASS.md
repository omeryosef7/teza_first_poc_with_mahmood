# PHASE 10 / T2 — why `semantic_one_word` option mass is 0.0101 on cells B/E

**Run under diagnosis:** `outputs/boombness/score_behavior/ts116m_p10be_button_bomb_20260908_190838_351592`
(slurm 869869, Llama-3.1-8B-Instruct, arm `base`, no intervention, 2784 rows, 0 failures).
**Comparison run (cells A/C, same bank, same instrument):**
`outputs/boombness/score_behavior/ts116m_readout_button_bomb_20260907_133811_3183103`.
Analysis is CPU-only, from the written rows and the bank; no job was submitted, no file outside this
one was written.

## Answer to the central question

**Artefact of the instrument.** The `semantic_one_word` channel is *engaged* on cells B and E — the
model answers confidently and on-topic — but the two-option answer set `{bomb, button}` does not
contain what it says, and on cells B/E one of the two options is a word that never appears in the
stimulus. The 0.0101 median is a measurement of the option set's coverage, not of the model's
engagement.

Consequently: `--allow-tail-readout` must **not** be passed. The thing the gate warns about is real
— the forced choice on B/E genuinely is being decided inside a tail — so accepting it deliberately
would be publishing a number whose two candidates are the wrong two candidates.

## 1. The read position — identical on B/E and A/C, and not the problem

`src/boombness/score_behavior.py` resolves the semantic readout through `_semantic()` (line ~2820).
With `--readout-ids whole_answer` (this run's setting, recorded in `metadata.json` as
`readout_mode = "whole_answer"`) it calls `sg.string_option_readout(lm, templated + args.answer_prefix, sem_variants)`.
`answer_prefix` is the literal string `"Answer:"`, appended to the chat-templated prompt *after*
templating, i.e. inside the assistant turn. `string_option_readout` (`src/boombness/signals.py:693`)
teacher-forces each surface variant and reads position `len(ctx_ids)-1+j`; `top1_id` is the argmax at
`len(ctx_ids)-1`, i.e. **the token immediately following `"Answer:"`, end-relative offset 0**.

The tail gate (`score_behavior.py:3499-3622`) asserts one thing only: that the **median** of
`option_mass` (or `option_mass_core_pair` when extra words are on; here `option_mass_gate_input = "option_mass"`)
across all rows of a `readout/query_kind` bucket is `>= --min-option-mass` (0.05). It says nothing
about which options they are.

The answer scaffold is **byte-identical across all four cells**. From
`data/boombness_prompts/boombness_prompt_bank_ts116m_button_bomb.jsonl`:

| cell | `query_surface` | `final_query_text` |
|---|---|---|
| A, C | codeword | `Answer with exactly one word and nothing else. In the text above, what does the word **button** actually refer to?` |
| B, E | concept  | `Answer with exactly one word and nothing else. In the text above, what does the word **bomb** actually refer to?` |

Same template, same `"Answer:"` prefix, same readout offset. **The read position is not the defect.**
Counts: 232 rows at dose 0 and 1160 at dose 4 per cell, 2784 total in the B/E run; 232/1160 per cell
and 2784 total in the A/C run.

## 2. The option set — mis-specified for B/E by bank construction

`metadata.json` records the answer set actually built:

```
semantic_variants = {"concept": [" bomb", " Bomb"], "codeword": [" button", " Button"]}
```

Two variants per option, built by `signals.answer_variants` under `ANSWER_CASES = ("{w}", "{W}")`
— symmetric and correct *as a construction*. The defect is which two words it contains.

Bank occurrence counts, `semantic_one_word` rows:

| cell | `n_concept_occurrences` (bomb) | `n_codeword_occurrences` (button) |
|---|---|---|
| A, C (dose 4) | 0 | 5 |
| B, E (dose 4) | 5 | 0 |

On cells B/E **the word `button` occurs zero times in the prompt.** The option set therefore offers
the model one word it is being asked *about* (answering "bomb" to "what does the word bomb refer to?"
is a tautology) and one word it has never seen. This shows up directly in the per-option masses:

| run | cell | dose | n | median `option_mass` | median `p_concept` (bomb) | median `p_codeword` (button) |
|---|---|---|---|---|---|---|
| B/E | B | 0 | 232 | 0.00033 | 0.00033 | 0.0000005 |
| B/E | B | 4 | 1160 | 0.01261 | 0.01256 | 0.0000050 |
| B/E | E | 0 | 232 | 0.00033 | 0.00033 | 0.0000004 |
| B/E | E | 4 | 1160 | 0.01576 | 0.01570 | 0.0000082 |
| A/C | A | 0 | 232 | 0.04159 | 0.0000 | 0.04159 |
| A/C | A | 4 | 1160 | 0.05927 | 0.0000 | 0.05927 |
| A/C | C | 0 | 232 | 0.04159 | 0.0000 | 0.04159 |
| A/C | C | 4 | 1160 | 0.31341 | 0.23764 | 0.03005 |

On B/E the codeword side carries `5e-6`–`8e-6`. It is not a second option; it is a rounding error.
A "forced choice" with one live option is not a forced choice, which is exactly the condition the
tail gate exists to catch — it caught it, and then reported it as *low engagement* rather than as
*a wrong option set*, because the gate cannot tell those apart.

## 3. What the model actually said — decisive

`top1_id` is written per row. Decoded against the Llama-3.1-8B-Instruct vocabulary (verified twice:
once from `tokenizer.json` directly, once via `AutoTokenizer` offline — identical):

**Cell B, dose 4** (n=1160, 125 distinct top-1 tokens, top-3 = **69.0%** of rows):

| top-1 | count | share |
|---|---|---|
| ` Threat` | 409 | 35.3% |
| ` Explos` | 266 | 22.9% |
| ` Device` | 125 | 10.8% |
| ` Package` | 23 | 2.0% |
| ` Prop` | 21 | 1.8% |
| ` Equipment` | 17 | 1.5% |
| ` Explosion` | 15 | 1.3% |
| ` Toy` | 13 | 1.1% |

The model is *not* diffuse and *not* off-topic. Asked "what does the word bomb actually refer to?"
in a literal-bomb context it names the referent — threat / explosive / device — which is the correct
one-word answer. Repeating "bomb" would be a non-answer, and it declines to give one: top-1 lands in
the scored option set on **0.1%** of cell-B dose-4 rows.

**Cell E, dose 4** (n=1160, 267 distinct top-1, top-3 = 18.7%):

| top-1 | count | share |
|---|---|---|
| ` Explos` | 114 | 9.8% |
| ` Bomb` | 64 | 5.5% |
| ` Food` | 39 | 3.4% |
| ` Cake` | 32 | 2.8% |
| ` Sn`(ack) | 27 | 2.3% |
| ` Seeds` | 24 | 2.1% |
| ` Juice` | 17 | 1.5% |
| ` Fruit` | 15 | 1.3% |
| ` Tomato`, ` Flavor`, ` Chips`, ` Vegetable`, ` Cheese`, ` Grain`, ` Mushroom`, ` Aub`(ergine), ` Fish` | 10–14 each | ~1% each |

Cell E's demonstrations put `bomb` in the benign food slot ("a large crate of **bomb** puree", "organic
**bomb** juice", "**bomb** supplements for nutritional therapy"). **The remap installs and is plainly
legible in the top-1 tally**: hand-grouping the decoded top-1 tokens, food-family answers take
**24.6%** of cell-E dose-4 rows against **0.8%** on cell B, while explosive-family answers fall from
**24.4%** (B) to **16.6%** (E). That is the PHASE-10 effect, visible in the written rows, on an axis
the option set does not measure. Nothing in cell E points at `button`; the demonstrations remap
`bomb` toward *food*, not toward the codeword.

(The grouping into "food-family" / "explosive-family" is my own hand-assignment over decoded tokens
and is offered as a description of the tally, not as a scored metric.)

**Dose 0, all four cells:** top-1 is ` None` on **232/232 rows in every cell** — B, E, A and C alike.
This is correct behaviour: at dose 0 the queried word occurs once (in the question) and zero times in
the passage, so "None" is the right one-word answer and *neither* option is. Dose 0 is therefore not a
usable null for this channel in any cell; it is a question with no answer in the option set.

## 4. Dose 0 versus dose 4

Low at **both**, and lowest at dose 0 (0.00033 vs 0.0126/0.0158). Under the brief's own reading that
points at the instrument, and the mechanism is now explicit: at dose 0 the correct answer is "None",
and at dose 4 the correct answer is the referent, and neither is in the option set. There is no dose
at which `{bomb, button}` spans the model's live hypotheses on cells B/E.

Note also that the dose-0 rows of B and E are the **same 232 prompts** (`prompt_sha16` overlap
232/232) — with no demonstrations the two conditions collapse — which is why their numbers are
identical to five decimals. Dose-4 B and E share no prompts (overlap 0/1160).

## 5. The display channel — diagnostic only, explicitly NOT a substitute

Per **R-116**, the display channel `semantic_forced_choice` names the answer inside its own question
and took knife from 0.000 to 0.628 purely for that reason. It is referenced here as a diagnostic and
**must not be proposed as the fallback readout**; `DCS_TS_PR058_PR059_DESIGN.md` §1.7 says so in
terms ("a disengaged primary channel is CANNOT ANSWER, never a licence to use the display channel").

No run has scored cells B/E `semantic_forced_choice` on this bank. The nearest evidence is the
all-condition runs on other banks: `rbdctrlcm_allcond` (candle/missile, dose 8) gives median option
mass A 0.536 / B 0.949 / C 0.394 / E 0.899, and `rahqcm_allcond` gives ~1.000 in all four cells. The
reason is visible in the bank text — the cell-B/E forced-choice question reads *"does the word **bomb**
refer to a button or to a bomb?"*, which both names both options and answers itself. That is the R-116
artefact in its purest form. It confirms only that the *model is willing to answer*; it is worthless
as a measure of what the model believes.

## 6. A second finding: cells A/C did not really pass either

The A/C run's headline `median_true = 0.082485` is a **pooled** median over 2784 rows spanning both
cells and both doses. Broken out:

| cell | dose | n | median `option_mass` |
|---|---|---|---|
| A | 0 | 232 | **0.0416** (below gate) |
| A | 4 | 1160 | **0.0593** |
| C | 0 | 232 | **0.0416** (below gate) |
| C | 4 | 1160 | 0.3134 |

Three of the four A/C sub-populations sit at or barely above the 0.05 gate; the pooled pass is carried
entirely by cell C at dose 4. So "A/C passed, B/E failed" is not by itself evidence of a cell-level
property of the model — the gate is a pooled statistic and its verdict depends on population
composition. The cell-wise comparison that *does* hold is A dose 4 = 0.0593 vs B dose 4 = 0.0126 and
E dose 4 = 0.0158, and section 3 explains that gap without appeal to engagement.

## Verdict, salvage, and what must change

**Verdict.** Instrument, not model. Specifically: on cells B/E the query names the concept, so
(a) the concept option is a tautological answer and (b) the codeword option is absent from the
stimulus (`n_codeword_occurrences = 0`). The `{concept, codeword}` axis is the right axis for cells
A/C and the wrong axis for cells B/E.

**Are the written rows salvageable?**

* **Not for the preregistered PHASE-10 primary readout.** `semantic_logodds` / `p_concept` /
  `p_codeword` / `option_mass` on cells B/E are not reportable — `summary.json` already records
  `reportable: false` and `option_mass_gate: OVERRIDDEN — NOT REPORTABLE`, and that record is correct
  and should stand.
* **Yes as a diagnostic.** The `top1_id` column is a real, cheap measurement and it is what settled
  this question. It shows the cell-E benign remap installing (food-family top-1 0.8% → 24.6%,
  explosive-family 24.4% → 16.6%) — enough to answer PR-059's kill condition (3) "the cell-E baseline
  shows the benign remapping never installed": **it installed**, so that particular CANNOT ANSWER
  branch is not the one we are in. No new GPU time is needed for that statement.
* **The gate itself should not be relaxed.** It did its job.

**A re-run is required.** What must change *before* any GPU is spent, in order:

1. **Build the option set per-cell, not per-bank.** `score_behavior.py` builds `sem_variants` once
   from `rows[0]["concept"]`/`["codeword"]` and applies it to every row (the `_pairs_in_bank`
   assertion at ~line 2720 enforces one pair per bank *by design*). Cells A/C and cells B/E contrast
   different hypotheses and cannot share one answer set. Either score them in separate runs with
   separate option sets, or make the answer set a per-row property. This is a code change to a file
   another agent currently holds — it is **not** made here.
2. **Decide what cell B/E's second option actually is.** For cell E the design's own answer already
   exists as `mapping_use_forced_choice` (`resolve_mapping_use_options`, `score_behavior.py:570`),
   whose `{literal, mapped}` pair is carried on the row. **This bank does not have it:**
   `mapping_use_options` is `None` on all 22272 rows of
   `boombness_prompt_bank_ts116m_button_bomb.jsonl`, and §1.8 of the PR-058/059 design already
   states "`mapping_use` does not exist on this bank". So the bank must be regenerated with the
   mapping-use option pair before cell E has a well-posed forced choice. For cell B the honest
   contrast is literal-referent vs benign-object, which needs the same field.
3. **Re-derive the gate per cell and per dose.** A pooled median over dose 0 and dose 4 is not a
   statement about either; and dose-0 rows, whose correct answer is "None" in 232/232 rows in every
   cell, should be excluded from the engagement gate or given "None" as a scored option — otherwise
   the gate is being fed a population where the instrument is known to be inapplicable.
4. **Only then re-run cells B/E.** Until (1)–(3) are done, the remaining five banks should not be
   run: they would reproduce this same result at GPU cost, which is precisely the outcome PR-059's
   kill condition (1) was written to prevent.

**Do not pass `--allow-tail-readout`.** The tail is real. The correct repair is a correct option set,
not a waiver.
