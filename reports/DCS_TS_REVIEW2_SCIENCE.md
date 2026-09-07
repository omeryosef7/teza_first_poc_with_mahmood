# DCS THESIS-SCALE — FOUR-HOUR REVIEW #2, SCIENCE AND CLAIMS LENS

**Window:** `e4d78bf0..b5359329` (12 commits). The first review (`A-042`) covered
`b80db84d..e4d78bf0` and is cited, not re-litigated.
**Lens:** mandate §29D, then the six questions put to this lens.
**Mode:** read-only. Nothing was edited, submitted, committed, or probed. `squeue` at the time of
writing shows exactly one job, `860468` (the multi-bank extraction), RUNNING 1:14:32.

**The state this review is written from, and it is the reason the review is worth anything:**
no probe has been run, no test split has been read, and no outcome exists. Every number below
that concerns the probe is a *prediction rule*, written before the number it will be applied to.

---

## 0. WHAT THIS LENS FOUND, IN ONE PLACE

Five new items. Three of them are, in my judgement, blocking for the headline sentence.

| id | severity | one line |
|---|---|---|
| **S-1** | **BLOCKING** | The frozen analyzer computes **no null and no nuisance comparison**. `require_null` and `require_gate` exist in `scripts/dcs_ts_prereg.py:101,107` and are **never called** by `scripts/dcs_ts_pr048_analysis.py` (0 hits for `N5`, `nuisance`, `0.7065`, `beat`). `primary.success` is "significantly above 0.5" (`configs/dcs_ts_pr049.json:208`) while the recorded honest floor is **0.7065** (`configs/dcs_ts_pr049.json:433`). **This is `B-020` again, in the code written to fix `B-020`.** |
| **S-2** | **BLOCKING** | **`PR-047` does not exist.** `configs/` contains `pr046`, `pr048`, `pr049` only. The positional contrast that `C-078` promised (log:1305) is not preregistered — and it is not *computable*: all six extractions capture `--position codeword_last` only (`runargs/dcs_ts116m_full_button_bomb.args:6-7`; `scripts/dcs_extract_under_ko.py:1074` offers exactly two choices). No hidden state exists at any control position. |
| **S-3** | **BLOCKING for CLAIM A wording** | The gist confound is unresolved and cannot be resolved by the run in flight. See §B. |
| **S-4** | correction | `Q-012`'s supporting arithmetic is **wrong**: it says "the bank carries **30** rows per domain per concept per codeword" (`configs/dcs_ts_pr048.json:217`). The bank carries **10** — verified on disk: `button_bomb`, cell C × `semantic_one_word` × `n_examples=4` = 1,160 rows over 116 domains, **10 per domain, no exceptions**. The conclusion (m=60 ⇒ both codewords) survives; the stated denominator contradicts `population.rows_per_domain_per_concept = 10` in the same frozen file. |
| **S-5** | design tension | `Q-012` pools both codewords into the primary. Mandate §5.3 (mandate:344-357) states a **"Preferred flagship protocol"** whose PRIMARY TEST is **button only**, with basket as *external lexical confirmation using the probe frozen from button*. `Q-012` reads §5.3's prohibition as applying only to the lexical-generalisation claim. That reading is contestable, it was made by the party that benefits (n_eff 193.6 → 222), and the benefit is **~15 % of n_eff**. See §D. |

---

## 1. MANDATE §29D — QUESTION BY QUESTION

Answered for the phase *as it stands*, i.e. for a probe that has not run. "UNKNOWN" is used where
that is the true answer.

**1. Is this genuinely BOMB-specific?**
UNKNOWN, and the phase has correctly stopped claiming it will be. `PR-049` explicitly *removes*
bomb from its contrast (`configs/dcs_ts_pr049.json` `_excluded_concept`) because bomb is where the
register confound lives (hedge-only +0.2217 bomb-vs-knife vs +0.0348 knife-vs-gun, log:2014-2017).
So the phase's cleanest instrument is by construction **not** bomb-specific — it is a
knife-vs-gun identity test. `PR-048`'s 3-way arm *is* bomb-inclusive and is the arm that carries
the severity confound. **Note the shape of this: the phase has one contrast that is about bomb and
confounded, and one contrast that is clean-ish and not about bomb.** That is a real limitation on
Matan's actual question, and it should be stated in the write-up rather than discovered by him.

**2. Could this be generic remapping?**
Not addressed by anything in this window. Generic remapping (button→*some* concept) is held
constant across the three arms by construction — all three arms remap — so the 3-way and 2-way
contrasts are identity contrasts, not remapping contrasts. That is a design strength and it is the
one confound the bank genuinely kills: cell A is byte-identical across concepts in **3,680/3,680**
rows (log:1919 / `configs/dcs_ts_pr048.json` `gates_g1_g3.G3a`). CLAIM B (separable remapping vs
identity axes) has **no instrument in flight at all**; it is not in `PR-048` or `PR-049`.

**3. Could this be generic harmfulness?**
Partly controlled and partly not. knife/gun/bomb are all harmful, so a pure harm axis cannot
produce above-chance 3-way identity. But harm **severity** is not held constant, and severity is
exactly what the register measurement found: bomb 44.5 % / knife 14.0 % / gun 18.3 % threat-lexicon
framing (log:1585). So "generic harmfulness" is dead; **"graded harm severity" is alive** and is the
live alternative for any bomb-inclusive contrast.

**4. Could it be installation strength?**
Not measured on `ts116m`. Installation is declared a preregistered stratification variable and
explicitly *not* a filter (`configs/dcs_ts_pr048.json` `_no_installation_exclusion`), which is the
right call, but I find **no measurement of installation rate on `ts116m`** in this window. Mandate
§15 requires every experiment to prove the mapping exists. `X4`/`R-105` measured *concept backing
of the demonstrations* (log:1899-1911), which is a property of the corpus, **not** proof that the
model took the mapping. Those are different things and the log does not currently distinguish them.
**Recorded as a gap: the phase has no prompt-validation table showing the model actually installs
knife/gun on `ts116m`.** Mandate §34 lists that table as a required output.

**5. Could it be prompt length?**
No, and this is now well established. Token length is the quantity the model reads: N4 in tokens
**0.3623** against 1/3 on the 3-way (log:1554-1560), and **+0.0435** on knife-vs-gun
(`reports/DCS_TS_PR049_BLOCKERS.md:325-330`). Character length is *not* matched (+0.1174 on
knife-vs-gun) but `C-084`'s argument applies. Cross-concept templated prompt spread is **1.194
tokens** (log:1893). Length is retired as a live confound and the phase should stop apologising
for it.

**6. Could it be template identity?**
No. Template-id-only sits at exactly **0.3333 / 0.5000, z = 0.00** on the probe population and on
all 6,624 cell-C test rows (log:1409-1410). This is the check that would scream if alignment broke,
and it is silent. Strongest single piece of corpus evidence in the phase.

**7. Could it be lexical leakage?**
Mostly closed, with two residuals that must be quoted together:
- **0/6,900** primary-channel rows print their own concept word (log:1380).
- `C-087` found the substituter eats compounds (`handgun` → `handbutton`); measured scope **exactly
  one occurrence across all three pools**, remedied by excluding `subway_station` (log:1868-1872).
- **`C-083` is the one that is still open and got worse:** verbatim TEST harm sentences appearing in
  a TRAIN domain went **3/2,760 (0.109 %) → 15/2,760 (0.543 %)**, a 5× regression caused by length
  matching (log:1495-1501). Small, real, and it must appear in the limitations paragraph.

**8. Did we train on a test domain?**
No, on the evidence available. Split is frozen at 68/23/23 with 0 overlap, rebuilds from seed
202609061, `manifest_sha16` recomputes (log:1538). The analyzer refuses if any domain appears in
both train and test (log:2117-2122). The two prospective exclusions are both TRAIN, so
validation/test stay 23/23 (log:1870).

**9. Did selection use TEST?**
Not by the probe — selection is validation-only and returns a `SELECTION_TRACE` the caller cannot
drop (log:2124). **But TEST prompt text has been read.** `scripts/dcs_ts_pr049_blockers.py:803-804`
fits the surface baselines on TRAIN domains and evaluates them on the **23 TEST domains**, which is
how 0.7065 was obtained. I judge this **acceptable and in fact correct** — it is prompt-only, uses
no model, selects nothing, and it puts the nuisance floor on the same population the probe will be
scored on. But it is a TEST read and it is nowhere declared as one. It should be recorded explicitly
so that nobody later discovers it and reads it as a breach.

**10. Is the read site downstream of the intervention?**
Not applicable to this measurement — `knockout_applied = false`, this is a baseline-reproduction
capture (log:2098). For the later mechanism work, `R-105` established `rel_end = −9` as a verified
downstream neutral site (log:1879-1883) and, critically, that the **absolute** codeword index is
identical across concepts in **0/2,300** triples while the end-relative index is identical in
**2,300/2,300** at −10, sd 0 (log:1885-1890). That is the position-index bug class caught before it
bit. Best catch of the window.

**11. Does the control actually test the alternative?**
**No — this is the weakest answer in §29D and it is `S-1`+`S-2`.** Eight nulls are declared
`nulls_required` (`configs/dcs_ts_pr048.json:252`), of which the analyzer implements exactly one
(N2, domain-level permutation). N3–N8 live in separate audit scripts and are **not bound to the
primary**; N5's stated expectation is literally *"the probe must beat it"* and no code path performs
that comparison. The positional control that would test the localisation alternative has neither a
preregistration nor an extracted hidden state.

**12. Is n_domains sufficient?**
Yes for the effect sizes contemplated, with one honest caveat. 23 TEST domains give conjunctive
power **0.963** at δ = +0.15 (0.900 under Holm) at the *assumed* sd 0.1406 (log:2043-2047). But
**there is no measured 2-way per-domain SD anywhere in the record** (log:2049) and the demotion
contingency triggers at sd = 0.188. The sign test is the binding arm and needs **k ≥ 17 of 23**
(log:2041). Also: mandate §5.5 asks for ≥100 *independent* domains; median inter-domain cosine is
**0.752** (log:941-945), so 114 domains are not 114 independent draws. That bound must be stated.

**13. Are we calling CANNOT ANSWER a null?**
Not yet, because nothing has been answered. But §B and §C below argue the phase is at risk of the
*inverse* error: calling a measurable-but-uninterpretable number an answer.

**14. Did a failed preregistered metric tempt us to switch?**
Yes, once, and it was handled well but incompletely. `C-078` declared the preregistered N5 bar
miscalibrated (log:1287) **before any probe ran**, which is the fact that makes it a correction
rather than a goalpost move, and `A-042` endorsed it *conditionally*. The condition — that the
positional contrast must not inherit N5's job — was discharged on paper by creating `PR-049`
(log:1755-1762). §C argues the discharge is now only partial.

**15. Would Matan accept this sentence after seeing the full table?**
For the infrastructure sentences in §F: yes. For any sentence about the codeword representation:
**there is no such sentence yet, and the one the current design will license is weaker than the one
the phase set out to write.** §A and §B give the exact wording that will and will not survive.

---

## 2. §A — THE INTERPRETATION TABLE, WRITTEN BEFORE THE NUMBER EXISTS

### A.0 The logical point that governs everything below

The hidden state at `codeword_last` is a **deterministic function of the prompt text**. Therefore
every bit of information a text classifier can extract from that prompt is, in principle,
*available* to the probe. It follows that:

> **No single probe accuracy, however high, can by itself establish that the probe is reading
> concept identity rather than surface statistics.** A high number is equally consistent with both
> hypotheses. Only a *contrast* — against a matched surface baseline, against a matched position,
> or against a matched-gist prompt — can separate them.

This is the same argument `C-078` made about N5 (log:1291-1296), and the phase has not yet noticed
that it cuts the other way too: **if N5 is not a legitimate bar, N5 is also not a legitimate
gist diagnostic.** Losing N5 as a bar means the phase lost its only cheap gist detector at the same
time, and nothing replaced it.

### A.1 The numbers the table is built from (all measured, all pre-outcome)

| population | chance | measured nuisance floors |
|---|---|---|
| 3-way (`PR-048`) | 0.3333 | template-id 0.3333 · N1 zero-dose 0.3333 · cell-A controls 0.3333 · token length 0.3623 · register-only 0.3942 · hedge-only 0.4739 · **hedge+register 0.5014** · TF-IDF full prompt masked 0.9014 · **TF-IDF demo block masked 0.9217** (log:1406-1418) |
| knife-vs-gun (`PR-049`) | 0.5 | hedge-only 0.5348 · token length 0.5435 · char length 0.6174 · register-only length-free 0.6870 · **register-only 17-feature 0.7065, AUROC 0.7479** (`reports/DCS_TS_PR049_BLOCKERS.md:287-330`) |

Sampling scale at n = 23 domains, sd = 0.1406 (the borrowed 3-way value; **the 2-way sd is
UNKNOWN**): SE = **0.0293**, 95 % CI half-width **0.0575**. At the demotion-contingency sd of 0.188,
SE = 0.0392 and the half-width is 0.0768. **Every band below should be widened accordingly if the
measured sd comes in above 0.1406.**

### A.2 INTERPRETATION TABLE — `PR-049`, knife-vs-gun domain-mean accuracy on 23 TEST domains

Chance 0.5. Measured surface floor **0.7065**. Floor + 2 SE ≈ **0.765** at sd 0.1406.

| observed A(k,g) | preregistered verdict | **what it is actually evidence for** |
|---|---|---|
| ≤ 0.55 | fails `primary.success` | Null. Informative only for δ ≥ 0.15 (power 0.963); for δ = 0.10 the phase must publish the achieved power before calling it a negative. Note 0.5348 is *hedge-only* — a probe here is at the weakest text baseline. |
| 0.55 – 0.71 | **may PASS `primary.success`** | **The dangerous band, and the reason this table exists.** The frozen success rule compares to 0.5 and nothing in code compares to 0.7065 (`S-1`). A result here is *below a 17-feature bag-of-surface-counts* and is **not evidence for CLAIM A**. Required sentence: "the probe does not exceed the measured surface floor of 0.7065 on this contrast." |
| 0.71 – 0.765 | passes | Above the floor but **within sampling error of it**. Suggestive; not evidence. Report the floor and the probe CI in the same row. |
| 0.765 – 0.85, **CI lower bound > 0.7065**, k ≥ 17/23 | passes | **The first result in this phase that clears its own nuisance floor.** Licenses: *"concept identity is linearly decodable from the codeword-position hidden state above the strongest measured surface baseline."* Does **not** license "the codeword is represented as KNIFE" — see §B. |
| ≥ 0.90 | passes | **Paradoxically weaker for CLAIM A, not stronger.** Bag-of-words over the demo block reaches 0.9217 on the 3-way. A probe that matches text-classifier performance is exactly what "the prompt's lexical gist propagated into the residual stream" predicts. Say so; do not report it as the strongest possible outcome. |

### A.3 INTERPRETATION TABLE — `PR-048`, 3-way domain-mean accuracy

Chance 0.3333. Strongest *shortcut* floor 0.5014 (hedge+register). Treatment-text ceiling 0.9217.

| observed A(3) | **what it is evidence for** |
|---|---|
| ≤ 0.40 | Null. Also inconsistent with the old 6-domain 0.7485, which would then need explaining. |
| 0.40 – 0.50 | Above chance and **within reach of hedge+register**. Uninterpretable as identity. |
| 0.50 – 0.75 | Above the shortcut floor. **Read the confusion matrix before the accuracy.** If bomb is near-perfectly separated and the residual errors are knife↔gun, the 3-way number is carrying the severity axis and must be reported that way. |
| 0.75 – 0.90 | Strong decodability. Still severity-contaminated; the honest sentence must name the bomb-vs-rest OvR AUROC beside it. |
| ≈ 0.92 or above | Matches the concept-masked TF-IDF over the demonstration block. Consistent with the hidden state carrying the demo-block gist. **Not** stronger evidence for CLAIM A. |

### A.4 The pre-committed SURFACE signature vs the pre-committed BINDING signature

Written now so neither can be assembled after the fact. These use only artifacts that already exist
or are already required.

**Consistent with "the probe is reading surface statistics that propagated into the hidden state" —
any two of:**
1. **Ordering match.** Probe accuracy across the three pairwise contrasts reproduces the surface
   baselines' ordering *and* approximate spacing: surface gives bomb-vs-knife 0.7217 >
   bomb-vs-gun 0.6870 > knife-vs-gun 0.7065-with-full-features / 0.5348-hedge-only. If the probe's
   pairwise profile is an affine rescaling of the surface profile, it is the same axis.
2. **Per-domain correlation.** Pearson r between the probe's 23 per-domain accuracies and the
   surface classifier's 23 per-domain accuracies **> 0.5**. Both vectors already exist or are one
   CPU re-run away: `fit_eval_2way` already returns `per_domain`
   (`scripts/dcs_ts_pr049_blockers.py:293`) and the analyzer already computes per-domain accuracy.
   **This is the single cheapest discriminator available and it should be added to the reporting
   set today, before the probe runs.**
3. **Flat layer profile.** Best accuracy at layer 6 ≈ best at layer 14, and `SELECTION_TRACE.inert`
   or a large `n_tied_at_best`. Lexical gist is in the residual stream early and does not develop;
   a *computed* binding should have a profile.
4. **Hedge-free collapse.** Accuracy on the hedge-free stratum (840 balanced knife-vs-gun rows,
   23/23 domains, log:2057-2060) falls toward the surface floor.

**Consistent with "the codeword position carries the installed concept" — needs all of:**
1. Domain-mean accuracy with **CI lower bound above 0.7065** on knife-vs-gun, and k ≥ 17/23.
2. **Per-domain decorrelation** from the surface classifier (r near 0, or the probe winning on the
   domains where surface loses).
3. A **non-flat layer profile** with an interior peak in 6–14 and `inert = false`.
4. Accuracy **preserved** on the hedge-free stratum.
5. Zero-shot button→basket transfer at the same TEST domain ids without recalibration.

Even all five together license only the decodability sentence. They do not license "represented as
BOMB" — that is §B.

---

## 3. §B — THE CANNOT ANSWER THE PHASE HAS NOT FULLY PRICED

### B.1 The strongest case that the planned primary cannot distinguish the two hypotheses

State the two hypotheses precisely.

- **H_bind:** the token `button`, at its own position, has been assigned the concept KNIFE by the
  demonstrations; the hidden state at that position encodes *that assignment*.
- **H_gist:** the prompt as a whole is about knives; a knife-ness feature is present in the residual
  stream at essentially every position from the demonstration block onward; the codeword position
  is one such position and carries nothing specific to itself.

The planned primary reads **one position, in one prompt, whose demonstration block already
determines the concept at 0.9217 by bag-of-words** (log:1417). Under H_gist, this measurement is
predicted to succeed, with high accuracy, for a reason that has nothing to do with the codeword.
Concretely, the argument has four legs and each is a measured fact in this record:

1. **The label is fully determined by text the probe's input depends on.** Not partially — 0.9217
   by TF-IDF over the demo block alone, 0.9014 over the full prompt.
2. **A transformer's residual stream at layer 6–14 at *any* mid-prompt position has attended over
   the whole preceding context.** The codeword sits at K = 10 rungs into the query, with the entire
   demo block behind it (log:1893). There is no architectural reason the knife-ness of the context
   would be absent there.
3. **The phase has no position-matched control**, so it cannot show the codeword position is
   *special*. `rel_end = −9` was verified as a control site (log:1879-1883) and then **not
   extracted** — every run is `--position codeword_last`.
4. **The phase has no gist-matched control**, so it cannot show the *concept* rather than the
   *topic* is what is read. Cell A is byte-identical across concepts, so it has zero signal by
   construction and cannot serve.

Therefore: **on the run currently in flight, H_bind and H_gist make the same prediction, and no
declared statistic separates them.** A positive primary is a positive for H_bind ∨ H_gist. That is
a genuine CANNOT ANSWER on Matan's actual sentence — *"the codeword is becoming represented as
BOMB"* — even though it is a perfectly good ANSWER on the weaker sentence *"concept identity is
linearly decodable from the codeword position."*

The phase **has** noticed the threat: `A-042` named it the "killer experiment" and proposed the
two-codeword interference bank (log:1613-1625). But it filed it as *"the design to preregister
after the probe"*. The risk is not that it was missed; the risk is that the primary will be
reported first, in a document, in the strong wording, with the interference bank listed as future
work. That is how a CANNOT ANSWER becomes a claim.

### B.2 What the phase should do — cheap, already possible, in priority order

**B.2.1 — Free, today, no GPU: fix the wording before the number exists.**
Amend the log (not the frozen configs) to state that `PR-048`/`PR-049` answer
*"is the installed concept linearly decodable from the hidden state at the codeword position,
above the strongest measured surface baseline"* and **do not** answer *"the codeword is
represented as the concept"*. Written now it is a scope statement; written after the number it is
a retreat.

**B.2.2 — Free, today, no GPU: add the four surface-signature diagnostics of §A.4 to the reporting
set.** Per-domain correlation with the surface classifier is one `pearsonr` call over two 23-vectors
that both already exist. It is the highest information-per-CPU-second item in the entire phase.

**B.2.3 — Free, today, no GPU: the surface-matched re-analysis.** This is the instrument §C says
the phase is missing, and it is computable from the extraction already on disk. For each TEST
domain, score every knife/gun row with the frozen 17-feature register classifier, then either
(a) subsample rows to equate the surface-score distribution between the two arms within each
domain, or (b) report probe accuracy stratified by surface-score decile, or (c) regress the probe's
decision value on the surface score and test the residual. If the probe's advantage survives on
surface-matched rows, that is the first real evidence in the phase that the hidden state carries
something the surface does not. **Preregister it before the probe runs**, as a `PR-050`, and it
costs zero GPU.

**B.2.4 — ~6 GPU-hours, one job, existing CLI: extract a control position.**
`scripts/dcs_extract_under_ko.py:1074` already accepts `--position last`. Re-running the six banks
at `--position last` gives a downstream, concept-token-free, template-tail position in the *same
prompts*. Under H_gist, identity is decodable there at similar accuracy; under H_bind, the codeword
position should win. It is not a perfect control (later position, different token role), but it is
the difference between having a positional contrast and having none, it uses no new code, and at
the measured ~58 min/bank it fits in one allocation like `860468`. **Do this while the analyzer is
still unrunnable anyway.** Preregister the direction of the prediction first.

**B.2.5 — later, and it is the real answer:** the two-codeword interference bank (log:1617-1623).
Right design, and I endorse it — but note it requires the substituter to handle two codewords in
one prompt, and the substituter is the component that has produced seven defects. Budget a gate for
it before budgeting GPU for it.

---

## 4. §C — THE `C-078` → `PR-049` → `R-106` CHAIN, END TO END

### C.1 The chain as it actually ran

| step | what was claimed | verdict now |
|---|---|---|
| `PR-046` | N5 (concept-masked TF-IDF, 0.8870→0.9217) is the bar the probe must beat, **adopted as the answer to the register confound** | The adoption was a category error: N5 is a *total-surface* instrument, not a register instrument, and the demo block is the treatment. |
| `C-078` (log:1287) | that bar is miscalibrated; declare it before any probe runs; answer Matan's question with a **positional** contrast (`PR-047`) | **Legitimate.** Timing independently verifiable — no GPU had run, no hidden state existed. I agree with `A-042`'s verdict. |
| `A-042` (log:1595-1611) | legitimate **only if** the positional contrast does not inherit N5's job | Correct condition. |
| `PR-049` (log:1741) | knife-vs-gun is register-clean by measurement (+0.037), so *it* answers register while the positional contrast answers localisation — "two questions, two instruments" | **The premise is now measured false in its general form.** |
| `R-106` / `Y3` (log:2012-2033) | hedge-only +0.0348 ⇒ kill condition SURVIVE; but a 17-feature register-only surface classifier reaches **+0.2065** (acc 0.7065), **+0.1870 with every length channel removed** | Honest, self-reported, pre-outcome. Excellent conduct. |

### C.2 The plain answer: **yes — the phase currently has no instrument that answers the register confound.**

I want to be precise, because this matters and because the phase deserves credit for the part it
did get right.

**What survives.** The kill condition was written about the hedge-only classifier, it was frozen in
that form before the measurement, and rewriting its scope after seeing +0.2065 would have been the
exact move the freeze exists to prevent. `Y3-kill = SURVIVE` is correct and should stay. And the
+0.2217 vs +0.0348 asymmetry is a real, replicated, useful finding: **register is a bomb-vs-rest
severity axis, not a uniform nuisance.** That is a publishable observation about the corpus.

**What does not survive.** `PR-049` exists *because* it was going to be register-clean. Its
`_why_this_exists` block says "clean on register AND on length"
(`configs/dcs_ts_pr049.json` `_why_this_exists[4-5]`). On the live corpus that sentence is false:
clean on **hedges** (+0.0348) and on **token length** (+0.0435); not clean on character length
(+0.1174) and **not clean on surface register generally** (+0.2065, +0.1870 length-free). The
instrument answers a *narrower* construct (hedging) than the confound it was adopted to answer
(register). **That is structurally the same defect `C-078` diagnosed in N5** — an instrument
retained because it clears a bar that is not the question — and the phase has not named it as such.

So the ledger is:

- **N5** — disqualified as a bar by `C-078`. Correctly.
- **`PR-047` positional contrast** — never written; no config exists; and **no hidden state at a
  control position exists**, so it cannot be produced from the run in flight (`S-2`).
- **`PR-049` knife-vs-gun** — survives its own kill condition, but is measured *not* register-clean.
- **hedge-free stratum** (secondary) — removes hedges only, i.e. the channel that was already the
  smallest on this contrast (+0.0348). It does not touch the +0.1870 length-free surface signal.

**Conclusion, stated plainly as instructed: the register confound has no clean instrument. It has
been converted from an unknown into a quantified floor of 0.7065 / 0.7479, and that conversion is
real progress — but a quantified floor is a *bar*, not an *answer*, and the phase currently has no
code path that applies even that bar (`S-1`).**

### C.3 It must not be papered over by the positional contrast — and it currently is being

`PR-049` discharges `A-042`'s condition **on paper only**: it says the positional contrast answers
localisation while `PR-049` answers register (`configs/dcs_ts_pr049.json` `_why_this_exists[10-13]`).
In fact the positional contrast does not exist, is not preregistered, and is not extractable from
this run. So the two-instrument story is currently a **zero-instrument story with one partial
instrument**. The honest restatement:

> Register is not eliminated on any contrast in this phase. On knife-vs-gun it is reduced to a
> measured surface floor of 0.7065 accuracy / 0.7479 AUROC, which the probe must clear with a
> domain-level confidence interval, and which no analyzer currently checks. Localisation is
> untested: no preregistration and no control-position hidden state exist.

**Recommendations for §C, all cheap:**
1. Make the 0.7065 / 0.7479 floor a **code-enforced** comparison — read it via `Prereg.require()`
   in the analyzer, print it next to the primary, and make it impossible to emit a success verdict
   without it. This is `S-1` and it is a five-line fix to a file that was written specifically to
   prevent this failure.
2. Build the **surface-matched re-analysis** (B.2.3) as `PR-050`. It is the only design on the table
   that can actually *answer* register rather than bound it, and it costs zero GPU.
3. Either write `PR-047` and extract a control position (B.2.4), or **stop citing the positional
   contrast in any document as though it exists.** Currently `PR-049`, `PR-048`'s notes and the log
   all cite it.

---

## 5. §D — `Q-012`: SOUND, OR RATIONALISATION?

**Verdict: the process was sound, the arithmetic offered as evidence is wrong, and the conclusion
is contestable against the mandate. Net: I would not call it rationalisation, but I would not let
it stand unamended either.**

### D.1 What is genuinely good about it

- It was raised **before any test read** and before three of six banks existed (log:2137-2141).
- It was resolved **from the frozen artifact** rather than from preference, which is the correct
  hierarchy.
- `A-039` rule (4) — *"use both codewords (SD 0.1514→0.1406, n_eff 193.6→222.0)"* (log:926-929) —
  predates the ambiguity and the extraction, so the resolution is not invented at analysis time.
- The consequence adopted is **costly, not convenient**: the primary must wait for all six banks
  rather than running on the three finished button banks (log:2166-2170). An agent optimising for
  a result would have taken the shortcut and called it a preview.
- It was flagged for Omer as a defect in the preregistration rather than quietly patched.

That combination is the opposite of motivated reasoning, and it should be said.

### D.2 The arithmetic is wrong (`S-4`)

`configs/dcs_ts_pr048.json:217` states: *"The bank carries **30** rows per domain per concept per
codeword, so m = 60 is arithmetically TWO codewords."*

Measured on disk, `data/boombness_prompts/boombness_prompt_bank_ts116m_button_bomb.jsonl`, cell C ×
`semantic_one_word` × `n_examples = 4`: **1,160 rows over 116 domains = exactly 10 per domain, no
domain differing.** The same file declares `population.rows_per_domain_per_concept = 10`. `R-106`'s
6,840 rows over 114 domains = 60/domain is 114 × 3 concepts × 2 codewords × 10, which is consistent.

The **correct** statement is: *30 rows per domain per codeword across the three concepts (3 × 10);
m = 60 therefore spans two codewords.* The conclusion is unchanged, but a preregistration that
justifies a scope decision with a number contradicting its own field two hundred lines earlier is
one grep away from looking like post-hoc arithmetic. Fix the sentence.

### D.3 The conclusion is contestable against mandate §5.3 (`S-5`)

`Q-012` argues §5.3 forbids pooling only for the flagship *lexical-generalisation* claim
(log:2158-2164). But mandate:344-357 does two things, not one:

```
Do NOT pool button and basket into training for the flagship lexical-generalisation claim.

Preferred flagship protocol:
TRAIN:          button, TRAIN domains
SELECTION:      button, VALIDATION domains
PRIMARY TEST:   button, untouched TEST domains
LEXICAL EXTERNAL CONFIRMATION: basket, the SAME untouched TEST-domain IDs
                using the model/direction/probe frozen from button.
```

The prohibition is scoped to the lexical claim; the **preferred flagship protocol** is not, and its
PRIMARY TEST is button-only. `PR-048`'s own vocabulary agrees with the mandate and not with
`Q-012`: `population.codewords.development = "button"`,
`population.codewords.external_confirmation = "basket"` (`configs/dcs_ts_pr048.json:77`). Under the
pooled reading, the arm the config calls *external confirmation* is consumed by the primary's own
training and testing, and the only thing preserving its external status is a separately-fit
secondary.

And the benefit is small: n_eff 193.6 → 222.0, about **15 %**; projected sd 0.1514 → 0.1406. The
pooled reading is the higher-power reading, chosen by the party that benefits, for a gain that would
not change any verdict in the §A tables.

### D.4 What I would have done

1. **Make the mandate-preferred protocol the primary**: train button/TRAIN, select button/VALIDATION,
   test button/TEST (m = 30, sd 0.1514, n_eff 193.6, MDE ≈ 0.095 rather than 0.0925). Report the
   pooled fit as a **declared secondary**, Holm-corrected. This costs ~15 % n_eff and buys exact
   conformity with the frozen mandate plus an untouched external lexical confirmation.
2. **Report both regardless of outcome**, declared now. Two readings of an ambiguous frozen line is
   precisely the situation where you publish both rather than pick.
3. **Escalate rather than resolve.** The mandate is the frozen human authority and this is a
   deviation from its preferred protocol. `Q-012` does flag it for Omer, which is right; but it also
   *decides* it in the same breath, and marks the decision as derived from the artifact. Given
   there is a live job and hours of slack, "ask and wait" was affordable.
4. Fix the "30" to "10" (`S-4`).

To be explicit about the accusation the question invites: **I do not think this is rationalisation.**
Rationalisation looks like choosing the reading that avoids a cost; this reading *imposed* a cost
(waiting for all six banks) and the power gain it captured is negligible. It reads as an honest
resolution that leaned, unremarked, in the analyst's favour and against the mandate's stated
preference — which is why it needs a second reader, not a rebuke.

---

## 6. §E — NINE CORRECTIONS IN ONE WINDOW: RIGOUR, OR AN UNTRUSTWORTHY PIPELINE?

Omer has to defend this to Matan, so here is my actual opinion rather than a balanced non-answer.

### E.1 It is rigour, and there is a checkable test that proves it

The test is **direction of cost**. Motivated correction moves results toward the desired answer;
rigorous correction costs you something. Every correction in this window costs:

| correction | what it cost |
|---|---|
| `C-079`/`C-080` | retracted a published 19/19 (log:1442-1469) |
| `C-081` | demoted the phase's own null from evidence to sanity check (log:1471) |
| `C-082` | retracted the phase's own justification for an exclusion (log:1482) |
| `C-083` | published a **5× regression** in leakage caused by the phase's own remedy (log:1495) |
| `C-085` | retracted "strictly stronger" as false, against itself (log:1568) |
| `C-086` | published that its own extraction gate would not have stopped an early extraction (log:1811) |
| `C-087` | cost a TRAIN domain (log:1868) |
| `C-088` | corrected `A-039`'s zero-binding finding to corpus-specific, weakening a warning the phase had been quoting (log:2064-2072) |
| `C-089` | replaced a guard test that had been *passing* (log:2126) |
| `C-084` | the **only** correction in the window that moved a number favourably (0.4014 → 0.3623) — and it came from an independent lens, not from the operator |

**Nine of ten corrections went against the phase, and the one that went for it was found by
somebody else.** That is not the signature of a pipeline being talked into a result. Matan can
check that column himself in ten minutes, and it is the single strongest thing Omer can put in
front of him.

Add to that: the design was frozen in machine-readable form **before the data existed**, the
analyzer was committed before any hidden state existed (log:1792-1800), the +0.10 kill condition was
declared before `Y3` was measured and then *survived a measurement that could have killed it*
(log:2012), and the 0.7065 bar was written down **before the probe** in the explicit words *"it is
much easier to accept a bar before you know whether you cleared it"* (log:2031-2033). Those are
behaviours that cannot be faked retroactively and are timestamped in git.

### E.2 It is also evidence of a pipeline that is too complex to be *self*-trusted — a different claim

Two things worry me, and Omer should hear them from this review rather than from Matan.

**(a) The find rate is not decelerating.** Seven instances of one bug class (a checker's notion of
a token ≠ the substituter's), the fourth of which was inside a *gate* and the sixth of which was the
extraction gate itself failing on `"not done".contains("done")` (log:1815-1820). The class was
finally fixed structurally — one shared implementation for generator, matcher and gate (log:1861),
booleans instead of prose (log:1830) — which is the right response. But `C-088` then found **three
GREEN mutations in the newest harness** and `C-089` found a stale selftest, both *after* the
"harden the four verifier harnesses" commit `b80db84d`. When each audit of the audits still yields,
you have no evidence you are near the bottom.

**(b) Every guard has the same author as the thing it guards.** `dcs_ts_prereg.py`,
`dcs_ts_pr048_analysis.py`, `dcs_ts_verify_ts116n.py`, `dcs_ts_pr049_blockers.py` and their
selftests are all the orchestrator's. The genuinely independent 4-hourly lenses have produced the
three highest-value corrections of the phase — `C-084` (wrong unit), `C-085` (false "strictly
stronger"), `R-103` (the whole knife-vs-gun idea) — and this review's `S-1` and `S-2` are the same
pattern: **a guard file that does not do the thing its own documentation says it does.** Self-audit
finds instances; independent audit finds classes.

### E.3 The sentence Omer should and should not use

**Say:** *"The design was frozen before the data existed, and every correction we made before the
outcome cost us something — a retracted gate, a lost domain, a 5× worse leakage number we published
ourselves. Here is the ledger."*

**Do not say:** *"We found and fixed eighteen defects, so the pipeline is clean."* That inference is
unavailable and Matan will spot it. Eighteen found defects is evidence about the *finding process*,
not about the *remaining defect count* — and the remaining count is, on this record, plausibly
non-zero.

**Concrete recommendation:** before the headline is written, have a human (Omer or Mahmood) hand-verify
**one** number end-to-end from bytes — I suggest the primary accuracy for one TEST domain, recomputed
by hand from the cache. One hand-checked number from outside the toolchain is worth more to a sceptical
reader than the whole guard suite, precisely because the guard suite has the same author as the code.

---

## 7. §F — WHAT THE PHASE CAN WRITE FOR MATAN, AS OF THIS COMMIT

Updated for `e4d78bf0..b5359329`. **No probe has run; there is no result about the representation.**

### F.1 SAFE — say as-is

*Infrastructure and corpus findings are real results, and several are better than the phase seems
to realise.*

1. **The layer convention is confirmed by experiment, not by reading code.** Planted-hook test, job
   860184: a post-hook on block 12 moves `hidden_states[13]` by +1000.158 and moves
   `hidden_states[12]` by 0.000000. **block L == `hidden_states[L+1]`; `hidden_states[0]` ==
   embeddings.** (log:1690-1712)
2. **End-relative indexing is mandatory, and we proved it before it bit us.** The absolute codeword
   index is identical across the three concept arms in **0/2,300** triples (spread 9.36 ± 5.90
   tokens, range 0–50); the end-relative index is identical in **2,300/2,300** at exactly −10, sd 0.
   An absolute index would have read a different token in each arm. (log:1885-1890)
3. **The bank is aligned on everything a template could leak.** Cell A byte-identical across
   concepts **3,680/3,680**; cell C differs across concepts in **115/115** domains; template-id-only
   classifier at exactly **0.3333 / 0.5000, z = 0.00**; **0/6,900** primary-channel rows print their
   own concept word; 0 duplicates over 133,632 rows. (log:1409-1410, 1380, 1538-1544)
4. **The demonstrations really do afford their concepts.** 0/9,200 tier-1 explosive predicates in
   any knife pool; 3×3 affordance matrix diagonal-dominant with largest off-diagonal 8; 24 mutations
   24/24 RED. This is the positive control the original 6-domain banks scored zero on. (log:1899-1911)
5. **Register is a bomb-vs-rest severity axis, not a uniform nuisance** — replicated across two
   corpora: hedge-only buys **+0.2217** on bomb-vs-knife and **+0.0348** on knife-vs-gun
   (`ts116n` said +0.211 / +0.037). (log:2014-2018)
6. **Length in tokens is not a live confound; character length overstates it.** N4 3-way: 0.4014 in
   characters, **0.3623 in tokens** against 1/3. knife-vs-gun: +0.1174 chars vs **+0.0435 tokens**.
   Templated prompt lengths bomb 230.22 / knife 229.50 / gun 230.69, cross-concept spread **1.194
   tokens**. (log:1550-1566, 1891-1893)
7. **The nuisance floor for the probe is measured, published, and was written down before the probe
   existed:** knife-vs-gun surface floor **0.7065 accuracy / 0.7479 AUROC**; 3-way hedge+register
   0.5014; 3-way concept-masked TF-IDF over the demo block 0.9217. (log:2019-2033, 1406-1418)
8. **Power is settled at the domain level.** Sign-test floor at n = 23 is **2.3842e-07** (closed
   form agreeing with brute force over all 2²³ patterns); permutation floor at B = 10,000 is
   9.999e-05; conjunctive power **0.963** at δ = +0.15 (0.900 under Holm); FPR on pure noise through
   the real 36-point grid **0.0400 [0.0174, 0.0773]**. (log:2035-2053)
9. **Validation-selected vs test-selected selection differs by 9.5×** in FPR on pure noise
   (0.0467 vs 0.4433, 300 reps, real 36-point grid). This is why the discipline exists and it is a
   result in its own right. (log:915-921)
10. **The old headline was the floor.** The previous phase's p = 0.004975 *was* 1/(B+1) at B = 200,
    and 6/6 domains by sign test is worth p = 0.031, not 0.005. (log:911-913)
11. **First bank extracted and provably the preregistered one.** Job 860352, 22,272/22,272 rep
    stacks, 0 failures, `bank_rows_sha16 = 4ca3ec165ab5b018` **matching the hash `PR-048` froze
    before the bank was extracted**. (log:2085-2100)
12. **`forward_hidden`'s last-layer path is broken on Llama-3.1-8B under transformers 5.12** (T5
    FAIL), and the tied post-final-norm tensor differs from the raw last-block output by a **0.6276
    relative norm** — so any future last-layer read is blocked, not merely cautioned. (log:1721-1731,
    2102-2106)

### F.2 NEEDS QUALIFICATION — true only with the caveat attached

1. **"The gates pass 19/19 with 4/4 mutations RED."** → *on `ts116m`, under the **corrected** gate.*
   `R-101`'s identical sentence about `ts116n` was **retracted** because the gate was singular-only
   and could not see the eight `knives` sentences (`C-080`, log:1442). The sentence needs the family
   name and the retraction cited, or it repeats a claim already withdrawn once.
2. **"The bank is clean."** → clean on template identity, cell-A alignment, own-concept occurrence
   and token length. **Not** clean on surface register (0.7065 on knife-vs-gun) and not clean on
   demo-block bag-of-words (0.9217 3-way).
3. **"knife-vs-gun is the register-clean contrast."** → clean on **hedges** (+0.0348) and **token
   length** (+0.0435) only. `R-106` measured +0.2065 for a 17-feature surface classifier and +0.1870
   with every length channel removed. (log:2019-2027)
4. **"114 independent domains."** → 114 domains; **median inter-domain cosine 0.752**, and every harm
   pool is a rewrite of one bomb template family. They are not 114 independent draws. (log:941-945)
5. **"Cross-split leakage is negligible."** → **15/2,760 (0.543 %)** TEST harm sentences appear
   verbatim in a TRAIN domain, **5× worse** than the previous family, caused by our own length
   matching. Small in absolute terms; a regression, and ours. (`C-083`, log:1495)
6. **"restaurant_kitchen is a bad domain."** → the two "independent" seeds shared **13 of 14** OpenAI
   draws, so the second failure says little; the domain is in fact **clean in the new pools (0/40 on
   all three concepts)**. The exclusion is **conservative, not necessary**, and is kept because
   reversing a preregistered exclusion is worse. (`C-082`, log:1482)
7. **"The n=0 null passes."** → it is **degenerate by construction**: with no demonstrations the
   three arms are byte-identical prompts (230/230), so the probe is pinned to 1/3 by arithmetic. A
   pipeline sanity check, not evidence about the model. (`C-081`, log:1471)
8. **"Selecting the wrong field binds zero rows."** → **corpus-specific.** On `ts116m`,
   `condition == "natural_doublespeak"` binds the *same* 6,840 rows as `cell == "C"`. And
   `prompt_id` is **not unique across banks** — 6,840 rows carry 1,140 distinct ids — so the
   compound key `(bank_file_sha16, prompt_id)` is load-bearing. (`C-088`, log:2064-2072)
9. **Everything is Llama-3.1-8B-Instruct only**, by decision (Qwen3-14B absent from both caches
   under `HF_HUB_OFFLINE=1`). A scope limit, **not** a model-specificity finding.
10. **"The extraction gate held."** → it held **after** `C-086`; as written it would have let an
    extraction start with two blockers outstanding, and it was caught by hand-checking the gate
    against the checklist, not by the gate. (log:1811-1830)

### F.3 MUST NOT SAY

1. **Anything at all about probe accuracy, decodability, or CLAIM A.** No probe has run, no test
   split has been read, and the primary cannot even be computed until all six banks finish
   (log:2166-2170).
2. **"The model represents button as BOMB."** Mandate §33 forbids it without scope and decodability
   qualification, and §B above shows the planned primary cannot separate that from *"the prompt is
   about bombs"*.
3. **"The signal localises entirely to the demonstration block."** Retracted (`C-081`, log:1477).
4. **"ts116n passed 19/19 gates."** Retracted (`C-080`, log:1461).
5. **"Length matching fixed the length confound."** It moved accuracy by 0.016 and the AUROC *rose*;
   the honest statement is that token length was already essentially matched (`C-084`) and the
   remedy was aimed at the wrong level of aggregation. (log:1388-1402)
6. **"knife-vs-gun is register-clean"** without the +0.2065 qualification.
7. **"The positional contrast answers localisation."** `PR-047` does not exist, and no hidden state
   at any control position has been extracted (`S-2`).
8. **"We have an instrument for the register confound."** See §C — the phase has a measured floor,
   not an instrument, and nothing in code applies even the floor (`S-1`).
9. **"The pipeline is verified clean, we found and fixed every defect."** See §E.3.
10. **Any row-level p-value in support of a domain-level claim.** A row-level p prints 1.02e-06
    where the honest domain-level p is 0.05, and row-level permutation was measured at FPR 0.2000.
11. **"Probe accuracy proves causal use"**, and anything about CLAIM C/D/E — no intervention has
    been run in this phase.

---

## 8. WHAT I WOULD DO IN THE NEXT FOUR HOURS

In priority order, all compatible with the running job:

1. **Fix `S-1`.** Make the analyzer read `nulls_required` and `_y3_result.THE_BAR` through
   `Prereg.require()` and refuse to print a success verdict that does not carry the nuisance floor
   beside it. The file that exists to prevent unenforced thresholds currently contains one.
2. **Amend the scope sentence (B.2.1)** in the log, before the number exists.
3. **Add the four surface-signature diagnostics (§A.4)** to the reporting set, especially the
   per-domain correlation with the surface classifier. Zero GPU, one afternoon.
4. **Preregister `PR-050`, the surface-matched re-analysis (B.2.3).** This is the missing register
   instrument and it costs no GPU.
5. **Preregister and queue the `--position last` control extraction (B.2.4)**, ~6 GPU-hours in one
   allocation, before the primary is computed.
6. **Correct `S-4`** (30 → 10) and **escalate `S-5`** (button-only vs pooled primary) to Omer as a
   human decision against mandate §5.3, reporting both fits either way.
7. **Produce the prompt-validation table** that mandate §15/§34 require and that §29D question 4
   currently cannot answer.
