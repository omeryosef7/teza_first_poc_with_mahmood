# PHASES 10 and 11 — the design, and what each phase can and cannot say

*Written 2026-09-07, at commit `b80db84d`, on branch `behavioral-causality-sprint`.*

**Nothing in either phase has run.** No GPU job has been submitted, no arm exists, no outcome
exists. This file and the two configurations it describes were written **before** any forward pass,
which is the only condition under which a preregistration means anything.

| | PHASE 10 | PHASE 11 |
|---|---|---|
| preregistration | `configs/dcs_ts_pr058_phase10.json` | `configs/dcs_ts_pr059_phase11.json` |
| id | `DCS-PR-058` | `DCS-PR-059` |
| mandate section | 13 | 14 |
| status | `FROZEN` | `FROZEN` |
| loader `--check` | **clean** — 17 hashes pinned and verified, 12/12 mandate-21 fields | **clean** — 17 hashes pinned and verified, 12/12 mandate-21 fields |
| loader `--for-extraction` | **10 refusals** | **9 refusals** |
| loader `--mutate` | **6/6 mutations RED** | **6/6 mutations RED** |
| blocking checklist items | **9 of 11** | **8 of 10** |
| analyzer | `scripts/dcs_ts_pr058_symmetry.py` — **does not exist** | `scripts/dcs_ts_pr059_localisation.py` — **does not exist** |

The refusals are the design working. A preregistration that is `FROZEN` but not yet runnable should
load cleanly under `--check` and refuse under `--for-extraction`, and both do.

---

## 0. What is shared between them, and why it is copied rather than re-derived

Both files take **verbatim** from `configs/dcs_ts_pr048.json`:

- the six `ts116m` bank paths with their `bank_file_sha16` / `bank_rows_sha16`;
- the three harm pools with their `content_sha16`, and the shared-valence pool `976aa2b0b617118d`;
- the split manifest `data/boombness_prompts/dcs_ts116_domain_split.json`, `manifest_sha16`
  `be7d2c772d814ef3` — which is a **canonical-JSON content** hash, not a file hash, and was
  re-derived here (`sha256` of the manifest minus its own `manifest_sha16` field, sorted keys,
  compact separators) to confirm that before copying it;
- the three whole-population preregistered exclusions with their full reasons;
- the model block (`meta-llama/Llama-3.1-8B-Instruct`, revision `0e9e39f2…`, bfloat16, **eager**).

No hash in either file was invented. The five report/artifact hashes each config records
(`mandate`, token-role map report and artifact, prompt-validation report, literature update,
`pair_common.py`) were computed from the files on disk today and are labelled
`*_sha16_at_freeze` — **witnesses, not gates**: the loader file-verifies only bank and pool hashes,
so a later mismatch is a signal to re-read, not an automatic refusal.

**The exclusion arithmetic.** The manifest assigns 70 / 23 / 23 over 116 domains. All three
excluded domains (`restaurant_kitchen`, `subway_station`, `school_campus`) sit in **train**, so the
analysed split is **67 / 23 / 23 = 113 domains**, and 113 × 48 rows/domain = 5,424 rows per bank,
which is exactly what `R-116` reports. `PR-048`'s own `_exclusion_note` still says "68 are
ANALYSED" and names only two exclusions — it predates the `school_campus` widening. Both new files
carry a corrected note saying so rather than propagating the stale one.

**Domain-level everything.** Split unit is the domain, permutation is the domain, the independence
unit is the domain. Row-level permutation has a **measured false-positive rate of 0.2000** on this
design and appears in no arm, no secondary and no diagnostic of either phase.

**Every `p` beside its floor.** `n_perm = 10000` ⇒ attainable floor `1/(B+1) = 9.999e-05`. The
exact sign test's own floor is `1.93e-34` at n=113 and `2.384e-07` at n=23, so the permutation
floor binds. A `p` at its floor is a statement about the resolution of the design, not a
measurement of the effect — `R-116`'s installation table already has six of them.

**Installation is a stratifier (mandate §15), and the threshold is now preregistered.** `R-116` §3
says in terms that the 0.5 cut it used is *unregistered* and that "the right fix is to declare the
threshold in the … preregistration before extraction". Both files declare **0.5** on the
concept-free channel, publish the whole 0.10 / 0.25 / 0.50 / 0.75 / 0.90 sweep beside every
stratified number, analyse **both** strata, and drop **no** row for failing to install.

### The R-116 asymmetry, and what it makes unconstructible — declared now

On `semantic_one_word`, cell C, dose 4, over 113 domains:

| concept | median domain-mean `concept_binary_prob` | installing at 0.5 | max |
|---|---|---|---|
| **bomb** | 0.5762 | **70/113 = 0.619** | 0.9567 |
| **knife** | 0.0868 | **0/113 = 0.000** | 0.3680 |
| **gun** | 0.0316 | **1/113 = 0.009** | 0.7174 |

**Any arm whose hypothesis requires knife or gun to have installed is unconstructible on this bank.**
Both configs say so in a field named
`installation.THE_ASYMMETRY_AND_WHAT_IT_MAKES_UNCONSTRUCTIBLE`, before extraction, rather than
leaving it to be discovered as a null afterwards. The knife and gun arms are still **run and
reported** — omitting them would itself be a selection — but as *registered descriptive* arms with
no multiplicity membership and no confirmatory weight.

It is also a **power** statement and the configs make it quantitative: a knockout predicted to
*lower* the installed reading has ~0.09 (knife) and ~0.03 (gun) of headroom, which is **less than
the design's own MDE**. And the display channel does not rescue it: `semantic_forced_choice` scores
knife at 71/113 — while naming the word `knife` in its own question on **100.0%** of its rows,
against **0.0%** on the primary channel. Falling back to it is forbidden in both phases.

---

## 1. PHASE 10 — the symmetric "last explicit-concept row" test

### 1.1 The question, and the question that is *not* asked

Mandate §13: *"The naive probe AT the token `bomb` is invalid: it trivially reads lexical
identity."* So the probe-at-the-bomb-token is **not preregistered, not run, and not reportable**.
`PR-058` `read_site.position_NOT_USED` names it explicitly and the read at that position is
captured only as a diagnostic labelled **INVALID AS A MECHANISM OUTCOME** — captured precisely so
that the difference between it and the downstream site is visible.

What is asked instead: **if the final explicit-concept row is prevented from attending to the
demonstrations, what changes downstream?**

### 1.2 Population and n

The `ts116m` banks carry a clean 2×2 that makes this a real symmetry rather than a rhetorical one.
Verified on disk (`hospital_supply`, dose 4, `semantic_one_word`):

| cell | demos | query | example demo sentence | query text |
|---|---|---|---|---|
| **A** | benign | codeword | "a large crate of **button** puree" | "…what does the word **button** actually refer to?" |
| **B** | harm | concept | "The **bomb** disposal team was alerted…" | "…what does the word **bomb** actually refer to?" |
| **C** | harm | codeword | "The **button** disposal team was alerted…" | "…what does the word **button** actually refer to?" |
| **E** | benign | concept | "a large crate of **bomb** puree" | "…what does the word **bomb** actually refer to?" |

- **cell E is the PRIMARY arm** — the demonstrations remap the *literal concept word* toward a
  benign object, and the query names the concept. Cutting the demos off that row should **restore**
  the literal explosive reading.
- **cell C is the reference codeword-row arm** — mandate §13 requires "the same layer convention and
  controls as the corresponding codeword-row experiment", so it is **re-run inside this phase** at
  the same band, sites, doses, seeds and controls. Cutting the demos off the ` button` row should
  **destroy** the installed reading. Opposite sign, one intervention, one code path, one dose.
- **cell B is the matched specificity control** — identical query text, identical intervention,
  demonstrations that *agree* with the literal reading, so the same cut should do little.

**n**: 113 domains × 10 family slots = **1,130 rows per (bank, cell)**; three cells × two bomb banks
= **6,780 rows** at dose 4. Independence unit = domain, **n = 113** (67/23/23).

### 1.3 The exact intervention

`--knockout-scope target_surface_row_only --intervene demo_all:attn_knockout:6-14:1.0 --attn-impl eager`

- **destination rows**: the token rows of the *final* `target_surface` occurrence **inside the query
  span**. The bank field `target_surface` holds the **codeword** in cells A/C and the **explicit
  concept** in cells B/E — verified on disk. That is why **one** scope is both the codeword-row
  experiment and its symmetric partner: two scopes would have been two chances for the treatment and
  its own control to differ by something other than the cell.
- **source keys**: the demonstration block (`demo_key_positions` + `knockout_key_set("demo_all")`).
- **band**: blocks 6–14, inherited verbatim from every committed knockout argsfile in the repo. Not
  re-selected — re-selecting a band after seeing a profile is selection.
- **liveness**: `n_prefill_edits > 0` and `n_decode_edits == 0` exactly
  (`pair_common.LIVENESS_REQUIREMENT` / `LIVENESS_MUST_BE_ZERO`).

**Dose parity is a declared risk, not an assumption.** ` button` is one subtoken in 6,900/6,900
cell-C prompts. Whether ` bomb` is one subtoken at the cell-B/E query row **has never been
measured**. If it is two, cell E is a 2-row cut compared against a 1-row cut and the cells differ by
dose as well as by condition. The rule is fixed **before the count is known**: report the per-cell
subtoken count, and if it differs, the dose-matched last-subtoken-only comparison becomes the
headline.

### 1.4 Read sites

| what | where | why |
|---|---|---|
| **O1 semantic readout (PRIMARY)** | the answer position after full prefill | downstream of every layer and every row *by construction*, so the mandate-§12.1 artifact cannot touch it |
| **O2 downstream representation** | `following` — one token past the target-surface row; in cell C that is `rel_end −9`, `' actually'`, id 3604 | passes all four downstream-neutral criteria in 6,900/6,900 prompts and is identical across concepts in 2,300/2,300 triples (token-role map Q1) |
| layers | grid 7–14, primary block 9 | block 9 is `PR-048`'s **validation-only** selection. This phase performs **no** layer selection, so the measured test-selection FPR inflation (0.4433 vs 0.0467) cannot enter |
| **NOT used** | `codeword_last` (= the ` bomb` token itself) | mandate §13 |

**The propagation argument is met by construction, not by argument.** The intervention edits the
mask of *one* row. The primary representation read is at a *different* row, at block 9 or above —
at least three intervened blocks after the first — and the read row's own mask is **unchanged**.
That is exactly what §12.1 asks for.

`layer convention: block L == hidden_states[L+1]`, confirmed by a **planted-hook GPU test** (job
860184), not inferred from names (§22.3).

### 1.5 Outcomes, controls and nulls

Outcomes: **O1** `semantic_logodds = logp_concept − logp_codeword` (whole-answer, teacher-forced);
**O2** `Δh` at `following` over blocks 7–14 (norm, cosine with `v_bomb`, signed projection in gap
units); **O4** the full output-probability block. **O3 `mapping_use` is declared UNCONSTRUCTIBLE**:
`score_behavior.resolve_mapping_use_options` takes its two option words from generator-written row
fields, and the `ts116m` banks carry none. Mandate §13 asks for it; on this bank it does not exist,
and the config says so rather than dropping it quietly.

Controls K1–K7: untouched baseline; **dose-matched nondemo key control** (`nondemo_matched_d{1,2,3}`,
3 seeded draws, **3 distinct output hashes required** — a collapsed control band has been published
twice in this project, once with a fake between-draw sd of 0.0048); disabled-hook bridge
(byte-identical greedy generations, `max|diff| == 0.000e+00`); `n_examples = 0`; cell-B specificity;
`legacy_all_query` whole-query comparison; dose-8 replication. Eleven nulls **P-N1…P-N11**, eight of
them blocking, including an end-relative index audit and an equal-populations-across-arms check
(ledgered `prompt_id`s replayed into every arm).

Multiplicity: family **`PHASE10_SYMMETRY`**, Holm over H1–H4 at α = 0.05 family-wise. Controls,
descriptive arms, the display channel and the diagnostic concept-token read carry **no** membership.
An absent member enters at p = 1.0 rather than being dropped. The family is **disjoint** from
`PRIMARY`, `SECONDARY`, `EXPLORATORY`, `PHASE8_MECHANISM` and `PHASE9_CAUSAL`, so no existing Holm
correction is redefined — the `C-106` rule applied forwards.

### 1.6 Power

`d_MDE = 2.80158 / √n` in units of the between-domain SD of the paired delta:

| n | 113 (all analysed) | 67 (train) | 23 (test) |
|---|---|---|---|
| MDE in SD units | **0.2636** | 0.3423 | 0.5842 |

**The SD in nats has never been measured — no run has ever scored cells B or E on any channel — and
it is left `null` rather than filled with a borrowed number.** Measuring it on *validation domains
only* is blocking item **T3**, and the underpowered branch (`power < 0.8` ⇒ CANNOT ANSWER **without
reading test**) is required to be a code path, not a sentence.

What *does* exist is a derived **upper bound**: `R-116` publishes p10 = 0.2823 and p90 = 0.8007 for
bomb's domain-mean `concept_binary_prob`, giving SD ≈ **0.20226**. It is an upper bound on the
*paired* SD because pairing removes the shared domain intercept. Implied MDE in `cbp` units:
**0.0533** at n=113, 0.0692 at n=67, **0.1182** at n=23. Declared minimum meaningful effect: **0.5
nats**, set equal to `PR-057`'s so all three phases sit on one scale — stated as an assumption.

ICC 0.0884 (PR-048, this population), design effect 1.796 at m=10, ≈629 effective rows per bank.
Reported because §20 asks for it; **not** a route to a row-level p-value.

### 1.7 CANNOT ANSWER, kill, VOID

**CANNOT ANSWER** if: `option_mass` on cells B/E `semantic_one_word` is below the 0.05 gate (a
disengaged primary channel is CANNOT ANSWER, never a licence to use the display channel); **or** the
cell-E baseline shows the benign remapping never installed, so there is no installed state to knock
out — reported as CANNOT ANSWER and explicitly **not** as a mechanism null; **or** (for H4 only) the
cells-B/E token-role map yields no valid downstream-neutral site; **or** realised power < 0.8.

**Kill conditions**, in order: (1) cells B/E channel disengaged ⇒ no knockout job at all, because
that would reproduce `R-097` at GPU cost; (2) the whole-query knockout does not move cell E ⇒ the
single-row scope is not submitted, since a one-row cut cannot do what cutting the entire query span
could not; (3) the cell-E baseline is at the ceiling ⇒ not submitted, CANNOT ANSWER on ceiling
grounds.

**VOID** (not a negative): non-eager attention on a live arm; `hook_fired_count == 0`;
`n_decode_edits != 0`; realised ≠ expected cells; the disabled-hook bridge not reproducing the
baseline byte-for-byte; identical hashes across the three control draws; any absolute index in the
path; unequal per-arm populations.

**The negative has mandatory wording**: *"the demonstration→query pathway at the final
explicit-concept row is not required for the model's semantic report under this intervention, at
this dose, on this bank."* An asymmetry between the codeword row and the concept row is exactly what
the symmetric experiment was asked to find out.

### 1.8 What PHASE 10 cannot say whatever it returns

Nothing about knife or gun as *installed* concepts. Nothing about localisation — a positive shows
the sufficiency of *that* cut, not that no other row carries the pathway. Nothing that escapes the
cell-B/E query naming the concept. Nothing about CLAIM E (behaviour/ASR are gated off and
`mapping_use` does not exist on this bank). Register remains CANNOT ANSWER as an absolute confound.
Llama-only, one query template.

---

## 2. PHASE 11 — the query-position scope family, without instrument leakage

### 2.1 What is being replaced, and the four defects

`DCS-R-080` / `PR-032`: a K-ladder over `query_last_k_rows`, K ∈ {1,2,3,4,5,6,7,8,16,32}, on bank
`cds38` (38 domains, 380 rows), `--query-kinds semantic_forced_choice`, band 6–14. A dramatic step
at K = 7. The argsfiles are in the repo (`runargs/dcs/dcsk7_C_demo.txt`) and confirm every one of
those parameters.

1. **Instrument leakage.** K = 7 is the rung at which the cut first reaches the ` bomb` token — and
   ` bomb` was in the query only because `semantic_forced_choice` **names the concept in its own
   question**. `R-116` §4 measured this on our own data: the concept word appears in `full_prompt`
   on **100.0%** of forced-choice rows and **0.0%** of `semantic_one_word` rows, across all 32,544
   analysed rows, with two independent occurrence counts agreeing exactly. The same rows scored
   through the display channel take knife from **0.000 → 0.628** installing domains. **The channel,
   not the model, decides the answer.**
2. **Unmapped rows.** Mandate §12.3: *"Avoid raw last-K rows when they include unknown chat
   scaffold. First map every token. Then define semantic regions."* The token-role map (Q4) shows
   the **first five rungs of any last-K ladder on this template carry zero query content**: K=1…5
   are `'\n\n'`, `<|end_header_id|>`, `assistant`, `<|start_header_id|>`, `<|eot_id|>`.
3. **Rows vs cells.** `PR-032` states its own limit: `_q[-K:]` makes destination-row count and
   cut-cell count rise together *by construction*.
4. **Population.** 38 domains, one codeword, one concept. Mandate §14.2 asks for all available
   domains for the headline mechanism estimate.

### 2.2 Population, n, and the channel

Cell C, `semantic_one_word`, dose 4, concept bomb, **both** codeword banks as a declared **transfer
pair, never pooled** (`button_bomb` installs in 92/113 domains, `basket_bomb` in 46/113 — a factor
of two from the lexical codeword alone). **1,130 rows per bank, 2,260 rows, n = 113 domains**
(67/23/23).

The primary channel is engaged: `R-116` measures median `option_mass` = **0.1138** against a 0.05
gate, p10 = 0.0227, 95.5% of rows carrying ≥1% of next-token mass — three to four orders of
magnitude above the ~1e-5 this phase family feared. Two caveats are written in **up front**: at dose
0 the median is **0.0328, below the gate** (so the dose-0 null is a population check, not a readable
outcome), and a median of 0.11 means the model's actual preferred word is a *third* word ~89% of the
time, so `semantic_logodds` is an **ordering inside a residual** and is reported as one.

### 2.3 Semantic regions first, then scopes — the exact intervention

The token-role census is **constant in 6,900/6,900 cell-C prompts**: 28 query-side tokens =
answer-format instruction 8 + punctuation 3 + user-instruction scaffold 11 + codeword 1 + chat
scaffold 1 + response header 4, and **`neutral_content` = 0**. Layout in `rel_end`:

```
-28…-21 answer-format   -20 '.'   -19…-16 ' In the text above'   -15 ','
-14…-11 ' what does the word'     -10 CODEWORD ' button'/' basket'
 -9…-7  ' actually refer to'      -6 '?'   -5 <|eot_id|>   -4…-1 response header
```

| scope | mandate §14.1 label | `rel_end` rows | n rows | implementation |
|---|---|---|---|---|
| **S_A** | A. chat scaffold only | −5…−1 | 5 | **EXISTS** — `query_last_k_rows`, K=5 (`sorted(query_span)[-5:]` *is* exactly the scaffold set) |
| **S_B** | B. neutral question content only | ∅ | **0** | **UNCONSTRUCTIBLE** |
| **S_C** | C. codeword row only | −10 | 1 | **EXISTS** — `target_surface_row_only` |
| **S_D** | D. user content minus codeword | −28…−6 minus −10 | 22 | **NEW row-set**, existing channel |
| **S_E** | E. all user-content rows | −28…−6 | 23 | **NEW row-set**, existing channel |
| **S_F** | F. downstream readout row only | −9 | 1 | **NEW row-set**, existing channel |
| S_F2 | (extra) last query-span row | −1 | 1 | **EXISTS** — `prompt_last_row_only` |
| S_G | (reference) whole query span | −28…−1 | 28 | **EXISTS** — `query_prefill_only` |
| S_0 | (reference) no intervention | — | 0 | **EXISTS** — baseline |

**S_B is declared unconstructible now, not discovered later.** There is no neutral question content
on this template — every query-side token is instruction, scaffold, punctuation, the codeword, or
header. It enters the multiplicity family at **p = 1.0** as an absent member, and the report states
that mandate §14.1's scope B could not be built rather than omitting it. Building one would be a new
bank and therefore a new preregistration.

**S_F2 is not a substitute for S_F.** `prompt_last_row_only` resolves to `max(query_span)` =
`rel_end −1`, the response-header terminator `'\n\n'` — scaffold, not the readout content row. It is
run as a labelled extra.

**No K is swept.** The word K appears in no arm name. The old rungs are not re-run, not re-plotted,
and not cited as a mechanism result.

**Dose matching.** `S_C` vs `S_F` are exactly matched (1 row each). `S_D` vs `S_E` differ by
**exactly the codeword row** and are the phase's **primary contrast**. Every scope additionally gets
*two* controls: a seeded **random-row** draw of the same size excluding the scope's own rows (3
draws, 3 distinct hashes), and a dose-matched **nondemo-key** draw (`nondemo_matched_d{1,2,3}`,
whose pool excludes `query_span_positions`). The first asks "does cutting *these* rows matter, or
any m rows?"; the second asks "do the *demonstrations* matter, or any equal quantity of context?".
The old ladder had only the second — which is precisely the rows-vs-cells confound `PR-032`
declared it could not separate.

### 2.4 Read sites and outcomes

**The primary read site is the output.** A whole-answer teacher-forced score at the answer position
is downstream of every layer and every intervened row *by construction*, so the §12.1 "first
affected layer sees only its own mask" artifact cannot touch it. That is the cleanest available
answer to the R5 defect. **O2** (secondary) is `Δh` at `following` (`rel_end −9`), blocks 7–14.
Where a scope's cut *includes* the read row (S_C, S_D, S_E), the codeword-row read is persisted only
as a diagnostic labelled **INVALID FOR PROPAGATION**.

### 2.5 Success, negative, power

**Success is conjunctive** (all four): S_G moves in the expected direction; **at least one narrower
scope reaches ≥ 0.5 of the S_G effect** under Holm within `PHASE11_LOCALISATION`; that scope's own
dose-matched random-row control does **not** reproduce it across 3 draws with 3 distinct hashes; and
**S_A (scaffold only) is null**. The 0.5 threshold is `PR-032` §11.5's own half-of-reference rule,
**inherited verbatim** — inheriting a threshold from the design being replaced is the one way to be
sure it was not picked to fit this phase's numbers.

**Negative wording is mandatory**: *"the demonstration→query pathway is distributed across the query
rather than localised to any predeclared semantic region, under this intervention, at this band, on
this bank."* And the literature bound is written in **before** the run: `arXiv:2605.04061` reports
single-position activation intervention at **0% task transfer across all 28 layers of
Llama-3.2-3B despite 100% probing accuracy at those same positions**. A single-row null (S_C, S_F)
is the *expected* shape and on its own is close to uninformative.

**Power**: same arithmetic — MDE **0.2636 / 0.3423 / 0.5842** SD units at n = 113 / 67 / 23. The SD
in nats is **`null`**: the old ladder's magnitudes (K=8 δ = −6.616, controls +5.16…+5.38) are
*display-channel* numbers on a 38-domain bank and borrowing them would import the very instrument
this phase removes. Measuring it on validation only is blocking item **U3**. The derived upper bound
gives MDE ≈ **0.0533** `cbp` at n=113 against `R-116`'s measured installation effect of **+0.5563** —
so a knockout removing even a *tenth* of the installed effect is detectable at 113 domains, and only
a *fifth* would be at 23. **That is the argument for running all 113 domains, and it is made before
any data exist.** The same arithmetic condemns the knife and gun arms: their headroom (0.087, 0.032)
is smaller than the MDE.

**Cost, stated before asking for it**: 6 family scopes + S_F2 + S_0 + 3 random-row draws/scope + 3
nondemo draws/scope ≈ **44 arms × 2,260 rows** at dose 4, before doses 0/8 and the descriptive
knife/gun arms. Submission is **staged**: S_G and S_0 first, because the kill condition reads them.

### 2.6 CANNOT ANSWER, kill, VOID

**CANNOT ANSWER** if median `option_mass` in an arm falls below the 0.05 gate; or realised power
< 0.8; or a scope's row-set resolver fails on > 5% of rows so the arms no longer share a population.

**Kill**, in order: (1) if **S_G does not move**, no narrower scope is submitted — there is nothing
to localise, and running six narrow cuts to find nothing would be six chances to report a null that
is really a dead intervention; (2) baseline `option_mass` below gate ⇒ nothing is submitted; (3) if
**S_A moves**, the whole family is VOID until the cause is found — scaffold rows carry no query
content, so a scaffold-only effect means the arms differ by something the design does not know
about.

**VOID** adds one item PHASE 10 does not need: **any realised row set that does not equal its
declared `rel_end` set**. That is null **L-N4**, and it is the check the whole phase exists to
provide.

### 2.7 What PHASE 11 cannot say whatever it returns

It can never produce the sentence "the model does not need to read the demonstrations from the
neutral content of the question" — there is no neutral content. It cannot separate rows from cells
*across* scopes of different size (within a scope the random-row control does it). It cannot speak
outside blocks 6–14, which are inherited and not swept. Nothing about knife or gun as installed
concepts. Nothing about CLAIM E. One template, one model.

---

## 3. What exists, what must be built — the honest inventory

**Reused, with the call site named.** Nothing below is reimplemented.

| piece | file |
|---|---|
| scoped knockout modes, row algebra, per-mode liveness contract | `doublespeak_causality/pair_common.py` — `SCOPED_KNOCKOUT_MODES`, `resolve_scoped_query_rows`, `LIVENESS_REQUIREMENT`, `LIVENESS_MUST_BE_ZERO` |
| `target_surface_row_only` destination rows (codeword **and** concept, one code path) | `src/boombness/score_behavior.py:target_surface_positions` |
| protected query span | `src/boombness/score_behavior.py:query_span_positions` |
| arbitrary row set → hook (`surface_span` channel) | `pair_common.resolve_scoped_query_rows("query_last_k_rows")` — "the consumer, not this resolver, owns the definition" |
| dose-matched nondemo key control | `score_behavior.nondemo_control_draw` / `nondemo_draw_seed` / `nondemo_matched_d{1,2,3}` |
| semantic readout, whole-answer scoring, `option_mass` | `src/boombness/score_behavior.py` (`_semantic`, `semantic_logodds`, `option_mass_core_pair`) |
| hidden-state capture **under a live knockout** | `scripts/dcs_extract_under_ko.py` — `--position following` (exposed 2026-09-07, `C-099`), `--knockout-scope` |
| token map, roles, `rel_end` layout, downstream-neutral criteria | `scripts/dcs_ts116m_token_roles.py` + `outputs/dcs_ts/token_roles_ts116m.json.gz` + `reports/DCS_TS116M_TOKEN_ROLE_MAP.md` |
| preregistration enforcement | `scripts/dcs_ts_prereg.py` |
| verifier **architecture** | `scripts/dcs_verify_kladder.py` (C1 arm identity / C2 dose / C3 pairing; imports nothing from the producer), `scripts/dcs_verify_kladder_rowlevel.py` (R1–R5), red-teamed by `scripts/dcs_redteam_kladder_verifier.py` |

**Genuinely new — and there is no code for any of it today.**

| what | phase | checklist |
|---|---|---|
| a token-role map for **cells B and E**; `dcs_ts116m_token_roles.py` hardcodes cell C and has no `--cell` argument, and needs a `concept_word` role class | 10 | T1 |
| **any readout at all on cells B or E** — they have never been scored, on any channel, by any run | 10 | T2 |
| the **declared-offset row selector** (`rel_end` set → `surface_span`) at *both* `score_behavior` call sites and in `dcs_extract_under_ko.py`; today only `sorted(query_span)[-K:]` exists | 11 | U1 |
| the per-scope **random-row** control draw (the nondemo-**key** control exists; the random-**row** control does not) | 11 | U2 |
| `scripts/dcs_ts_pr058_symmetry.py` and `scripts/dcs_ts_pr059_localisation.py` | 10, 11 | T7, U5 |
| mutation harnesses for both analyzers | 10, 11 | T8, U6 |
| independent verifiers for these populations | 10, 11 | T9, U7 |

**`scripts/dcs_kladder_analysis.py` is *not* a reusable analyzer for PHASE 11.** It is frozen
against `PR-032`'s rung set (`NEW_RUNGS = (3,4,5,6,7)`, `INHERITED = (1,2,8,16,32)`), its `EXPECT_N`
is 380, and it resolves arm directories by the `dcsk*` glob. It is a **template for the shape** —
its half-of-reference rule is inherited verbatim into `PR-059` — not an analyzer for this
population. The same is true of the two verifiers: their **check classes** are reused, their code is
not.

---

## 4. Blocking checklists

### PHASE 10 — 9 blocking of 11

| id | blocking | item |
|---|---|---|
| **T1** | ✅ | token-role map for cells B and E; report the ` bomb` subtoken count at the query row |
| **T2** | ✅ | score cells B/E on `semantic_one_word`, no intervention; check `option_mass` and the cell-E ceiling |
| **T3** | ✅ | measure the between-domain SD on **validation only**; recompute MDE and power |
| **T4** | ✅ | confirm `target_surface_positions` resolves the concept occurrence on B/E; empty-needle guard fires |
| T5 | ✗ | PR-053 train-only direction file for O2, sha256 recorded into every artifact |
| **T6** | ✅ | nondemo draw protects the query span; 3 draws ⇒ 3 distinct hashes |
| **T7** | ✅ | write the analyzer — every threshold through `Prereg.require()`, no numeric literal |
| **T8** | ✅ | mutation-test it (8 named corruptions must each refuse) |
| **T9** | ✅ | independent verifier closing R1–R5 |
| **T10** | ✅ | smoke run on train domains |
| T11 | ✗ | fair-share coordination with PHASES 9 and 11 |

### PHASE 11 — 8 blocking of 10

| id | blocking | item |
|---|---|---|
| **U1** | ✅ | declared-offset row selector at both call sites + the extractor; persist realised positions **and decoded tokens** |
| **U2** | ✅ | per-scope random-row control draw; 3 distinct hashes |
| **U3** | ✅ | SD on the **concept-free** channel, validation only; do **not** borrow display-channel magnitudes |
| **U4** | ✅ | CPU-verify every scope's `rel_end` set against the token-role artifact in 6,900/6,900 prompts |
| **U5** | ✅ | write the analyzer; kill condition evaluated **before** the narrow scopes are read |
| **U6** | ✅ | mutation-test it (8 named corruptions) |
| **U7** | ✅ | independent verifier declaring its expected arm set *here*, so a producer cannot make it vacuous |
| **U8** | ✅ | smoke run S_G and S_C |
| U9 | ✗ | fair-share coordination and staged submission order |
| U10 | ✗ | re-run the token-role map and confirm its sha16, or record the diff |

---

## 5. The single biggest interpretability risk to each phase

**PHASE 10 — the cell-B/E query names the concept.** "In the text above, what does the word **bomb**
actually refer to?" contains ` bomb`, so `logp_concept` sits high by construction and the readout has
a ceiling cell C does not have. A null in the primary arm is confounded with that ceiling; a positive
is confounded with the model copying a word out of its own prompt. This is *not* the `R-116` leakage
defect — that defect is a readout naming an answer it did not have to name, whereas here the concept
token **is the object of the intervention** — but it bites just as hard. The mitigation is
preregistered rather than left to the write-up: the cell-E baseline distribution is reported in full
*before* any delta is interpreted (and a p90 at the top of the scored range is CANNOT ANSWER on
ceiling grounds); cell B carries the identical query text and identical ceiling, so the H1−H3
contrast differences it out; and **the copy account and the mechanism account predict opposite signs
for H1 relative to H2**, both of which are declared before any data exist.

**PHASE 11 — the concept-free channel is only weakly engaged.** Median `option_mass` is **0.1138**:
the two scored options carry about a ninth of the next-token mass, and the model's actual answer is a
*third* word (` Basket`, ` Container`, ` Button`, ` Mushroom`, ` Alarm`) roughly **89%** of the time.
So `semantic_logodds` is an ordering inside a residual, and a knockout can move that ordering while
the model's output word never changes. Mitigation, preregistered: the argmax decoded answer and the
full `option_mass` distribution are reported for every arm **beside** every delta, never after it; an
argmax-switch rate is reported as a corroborant and is explicitly **not** required for success
(§10.5 says "ideally"); and an arm whose median `option_mass` drops below the gate is CANNOT ANSWER.
The tempting escape — the display channel, where `option_mass` is 0.708 — is **exactly the leakage
this phase exists to remove**, and is forbidden.

---

## 6. Reproduce the loader results

```
python3 scripts/dcs_ts_prereg.py --check configs/dcs_ts_pr058_phase10.json
python3 scripts/dcs_ts_prereg.py --check configs/dcs_ts_pr059_phase11.json
python3 scripts/dcs_ts_prereg.py --check --for-extraction configs/dcs_ts_pr058_phase10.json   # 10 refusals
python3 scripts/dcs_ts_prereg.py --check --for-extraction configs/dcs_ts_pr059_phase11.json   #  9 refusals
python3 scripts/dcs_ts_prereg.py --mutate configs/dcs_ts_pr058_phase10.json                   # 6/6 RED
python3 scripts/dcs_ts_prereg.py --mutate configs/dcs_ts_pr059_phase11.json                   # 6/6 RED
```

Observed 2026-09-07: both clean under `--check` (17 hashes pinned and verified, 12/12 mandate-21
fields); 10 and 9 refusals respectively under `--for-extraction` (9 and 8 blocking checklist items,
plus `artifacts.analyzer_exists == false` in each); 6/6 mutations RED for both. The `--mutate` run
re-hashes all six 22,272-row bank files per mutation and takes a few minutes on this filesystem.
