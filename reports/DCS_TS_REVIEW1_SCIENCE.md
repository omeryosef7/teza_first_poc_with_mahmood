# DCS THESIS-SCALE — REVIEW 1, LENS D: SCIENTIFIC CLAIM REVIEW

**Mandate section:** `external_md/DCS_THESIS_SCALE_MANDATE_20260906.md:1817-1837` (§29D).
**Reviewer:** read-only subagent. No file outside this one was written; nothing was committed;
no job was submitted.
**Range reviewed:** `b80db84d..e4d78bf0` plus the uncommitted working tree and the log entries
appended past `e4d78bf0` (the log is at 1,431 lines; `C-079` and `R-102` post-date the commit).
**Phase state at review time, verified independently:** `sacct -u omeryosef -S 2026-09-06 -X`
shows only `tsharm` CPU jobs (859713–859980) and no GPU extraction; `squeue` empty;
`outputs/dcs_ts/` contains only `token_roles_ts116.json.gz` and `ts116_sidecar.jsonl.gz`, both
built on the **VOID** `ts116` bank. **No hidden state exists. The claim "no GPU has run" is
confirmed from the scheduler, not from prose.**

---

## 0. WHAT I VERIFIED MYSELF, AND WHAT I FOUND THAT THE LOG DOES NOT SAY

Everything in this section is my own computation on the artifacts, with
`/home/sharifm/students/omeryosef/miniconda3/envs/poc_stage2/bin/python`, on the primary
population as `configs/dcs_ts_pr046.json:96-104` defines it (`cell == "C"`,
`query_kind == "semantic_one_word"`, `n_examples == 4`, codeword `button`, 115 domains,
`restaurant_kitchen` excluded), split by `data/boombness_prompts/dcs_ts116_domain_split.json`
(`assign`, 70/23/23 → 69/23/23 analysed). **3,450 rows; 2,070 train; 690 test over 23 test
domains.**

### 0.1 Reproductions (the phase's own numbers, recomputed from scratch)

| quantity | log value | my value | denominator |
|---|---|---|---|
| N4 length-only (`n_chars`), 3-way, TEST | 0.4014 (log:1409) | **0.4014** | 690 rows / 23 domains |
| H1 hedge-only (5 regexes), 3-way, TEST | 0.4739 (log:1408) | **0.4739** | 690 / 23 |
| N5c TF-IDF over demo block, concept-masked | 0.9217 (log:1412) | **0.9290** | 690 / 23 (my vectoriser differs slightly) |
| C-076 plural leak on `ts116n` | 30/3,680 primary rows | **15/1,856 per codeword**, 6 domains: `blood_bank`,`care_home_store`,`cheese_dairy` (train), `hospital_supply` (val), `instructional`,`physio_gym` (test) | exactly the 3/1/2 split the log states |
| C-076 fixed on `ts116m` | 0/6,900 | **0/11,136** cell-C×`semantic_one_word` rows across all six banks name any concept form | 11,136 |
| `tsm` pools free of substitution defects | asserted | **0/13,920** non-unit-substitutable, **0/13,920** naming another concept | 3 × 4,640 |
| inter-domain independence | median cosine 0.752 (`A-040`) | **0.581** median, 0.695 p90 (TF-IDF min_df=2 over harm pools, `tsm` bomb) | 6,670 domain pairs |

The independence number is instrument-dependent, not a contradiction; both say the same thing —
**the 115 domains are far from orthogonal, because every harm pool is a rewrite within one
generator family.**

### 0.2 Three things I found that are not in the log

**(a) The length-matching remedy is being judged in the wrong unit, and in the model's unit it
mostly worked.** `N4` reads `n_chars` (`scripts/dcs_ts116n_audit_leakage.py:686`). The model
reads tokens. On the real `ts116m` primary population, tokenised with the pinned Llama-3.1-8B
tokenizer:

| unit | 3-way TEST accuracy (chance 0.3333) | knife-vs-gun (chance 0.5) |
|---|---|---|
| `n_chars` (what N4 measures) | 0.4014 | 0.5652 |
| **prompt token count (what the model sees)** | **0.3623** | 0.5435 |

Mean prompt tokens: bomb **196.21** (sd 13.10), knife **195.50** (12.42), gun **196.69** (13.10)
— a ~1.2-token spread against a 13-token within-class sd, over 1,150 rows per class. So the
*positional* confound (where the codeword sits, how long the context is) is essentially matched;
the residual `n_chars` signal is **word-length / lexical composition**, i.e. register again, not
length. `R-102`'s verdict *"the remedy did not work"* is true of the char metric and pessimistic
about the thing that actually matters. **Recommendation: add `N4-tok` (prompt token count) as a
reported baseline and state which unit the claim is defended in.**

**(b) The register confound is a bomb-vs-rest severity axis, and knife-vs-gun is nearly clean of
it.** Decomposing the nuisance baselines by pairwise contrast on the real bank (TEST, domain-mean):

| contrast | TF-IDF demo block | `n_chars` | hedge-only (5 regex) |
|---|---|---|---|
| 3-way (chance .3333) | 0.9290 | 0.4014 | 0.4739 |
| **bomb vs knife** (chance .5) | 0.9826 | 0.6152 | **0.7109** |
| **bomb vs gun** (.5) | 0.9522 | 0.5370 | **0.6739** |
| **knife vs gun** (.5) | 0.9435 | 0.5652 | **0.5370** |

Hedging buys 0.21 over chance on bomb-vs-knife and **0.037 on knife-vs-gun**. The audit's own
`H1` confusion (`reports/DCS_TS116N_LEAKAGE_AUDIT.md:294-300`) says the same thing from the other
side: with only hedge counts the classifier predicts `gun` **0 times out of 1,380**.
**Consequence: knife-vs-gun is the register-clean, position-clean sub-contrast, and it is the
contrast on which CLAIM A actually lives.** It is not preregistered as a gate anywhere in
`configs/dcs_ts_pr046.json`.

**(c) A hedge-free stratum exists and is large enough to use.** Counting `ts116m` button rows in
the primary cell that contain zero matches of the five hedge patterns:

| concept | TEST rows | hedged | hedge-free |
|---|---|---|---|
| bomb | 230 | 115 (50.0 %) | **115** |
| knife | 230 | 18 (7.8 %) | 212 |
| gun | 230 | 35 (15.2 %) | 195 |

A class-balanced hedge-free TEST subsample of **115 × 3 = 345 rows across 23 domains** is
available at zero extra GPU cost from the same forward pass. That is the cheapest existing
answer to `Q-011`, and it is currently unplanned.

---

## 1. Is what we are about to measure genuinely BOMB-specific, or could it be generic remapping?

**Not established, and the design as frozen cannot establish it.**

`PR-046` is a 3-way discrimination *within* cell C (`configs/dcs_ts_pr046.json:96,105-108`). Cell
C is `natural_doublespeak` for all three arms: every arm is a remapping. So the probe cannot be
confounded by "remapped vs not remapped" — that variance is zero by construction. Good.

But CLAIM A as the mandate words it (`:1948-1951`) is *"contains the identity of the concept
installed … not merely generic remapping"*, and the design contains **no cell-B (`benign_remap`)
comparison and no remap-axis control at all**. The eight required nulls
(`configs/dcs_ts_pr046.json:222-266`) are: n_ex=0, domain permutation, full-prompt leakage,
length, TF-IDF, template-id, codeword-only, label permutation. **None of them is a remapping
control.** The n_ex=0 null (N1) tests "no demonstrations", not "demonstrations that remap to
something harmless".

What a 3-way concept probe *does* rule out is that the signal is *only* remap-strength in the
scalar sense — a 1-D "how strongly is the codeword remapped" axis cannot produce 3-way
above-chance unless the three concepts differ in installation strength, which is question 3 and
is **not** ruled out. Verdict: **the phase can support "the state distinguishes which of three
installed concepts", and must not, on this design alone, write "not merely generic remapping"**
unless a cell-B axis is added (see §9 and Part A).

## 2. Could it be generic harmfulness?

**Yes, and this is currently the second-strongest live alternative.** The three concepts are not
matched on threat salience. My own count over the shipped length-matched harm pools
(`data/boombness_prompts/demo_pools_116dom_tsm_*.json`, 4,640 sentences per concept):

| concept | threat-lexicon sentences | mundane-lexicon sentences |
|---|---|---|
| bomb | **2,065 / 4,640 = 44.5 %** | 942 / 4,640 = 20.3 % |
| knife | 650 / 4,640 = 14.0 % | 1,638 / 4,640 = 35.3 % |
| gun | 849 / 4,640 = 18.3 % | 1,374 / 4,640 = 29.6 % |

(threat = `threat|evacuat|police|emergency|security|lockdown|arrest|alarm|hazard|injur|weapon|danger|incident|unattended|suspicious|confiscat`;
mundane = `clean|wash|stor*|sharpen|maintenance|inventory|replace|inspect*|shelf|drawer|rack`.)

A bomb demonstration block is three times more likely to be framed as an emergency than a knife
block. A probe that recovers "this codeword sits in alarming discourse" would score well above
chance 3-way **without representing any concept identity**. The corroborating design fact is that
the concept-backing audit's own positive control is *affordance*, not severity
(`external_md/…_20260906.md:1235-1239`), so severity was never matched and was never measured as
a confound.

Again the discriminating statistic is **knife vs gun**: similar severity (14.0 % vs 18.3 %
threat), hedge-only near chance (0.5370). If the probe is strong 3-way but at chance on
knife-vs-gun, the honest reading is *generic harm-salience*, not identity.

## 3. Could it be installation strength?

**Unknown, and unmeasurable until the first forward pass — which is the correct state, but the
preregistration under-commits.**

`PR-046` says installation is a stratification variable and never an exclusion
(`configs/dcs_ts_pr046.json:120`, mandate `:1145-1180`). That is right. What is missing is the
*analysis* that makes it a control rather than a caveat. Three things are known in advance and
point the same way:

- the demos are natural incident-log text, and Llama has a far stronger prior on bomb-as-threat
  than on knife-as-threat, so bomb is a priori the easiest concept to install;
- `A-034.2` already records that gun "does not remap consistently across domains" is a banned
  sentence precisely because gun installation was ragged on the old banks (mandate `:2033`);
- 49.0 % of bomb primary rows are hedged (my count, 564/1,150), and a hedged demonstration
  installs *weaker* — the log itself says hedging "bounds absolute installation"
  (`external_md/…:876-879`). So installation strength is not even monotone in concept.

**Requirement:** the phase must report, before interpreting the probe, the per-concept
installation table mandate §15 demands (`:1150-1170`), and must show the probe's per-domain
accuracy is **not** explained by per-domain installation strength — e.g. accuracy conditioned on
installation quartile, or a per-domain partial correlation. Absent that, the sentence
"the state carries identity" is not separable from "the state carries how strongly *something*
was installed, and bomb installs hardest".

## 4. Could it be prompt length?

**Partly, and the remedy's success depends entirely on which unit you ask in.**

The trail is clean process: the length-matching rule was written into
`configs/dcs_ts_pr046.json:157` *before* N4 was measured; G5 measured N4 = 0.4174 / AUROC 0.5750,
z = +6.62 (`reports/DCS_TS116N_LEAKAGE_AUDIT.md:209`); the rule fired; the matcher is
deterministic, prompt-only, RNG-free and outcome-blind
(`scripts/dcs_ts_length_match_pools.py:26-41,104-118`). That is exactly how a preregistered
trigger is supposed to behave and it should be reported as a success of the process regardless of
the outcome.

**On the numbers.** Three different "spread reduction" figures are in circulation and they have
different denominators:

| statement | before | after | reduction |
|---|---|---|---|
| `R-102`, log:1394 | 7.03 chars | 4.16 | 40.8 % |
| my measurement, shipped `ts_*` → `tsm_*` pools, 4,640 sentences/concept | **6.517** | **4.161** | **36.2 %** |
| the parent brief's figure | — | — | 41.2 % (**UNKNOWN provenance**; not in the log or any committed artifact) |

The discrepancy is real and instructive: `R-102`'s "before" is the *usable-filtered 60-candidate
pool truncated to 40* (`scripts/dcs_ts_length_match_pools.py:137`), not the pool that was actually
shipped in `ts116n`. Against the bank that existed, the cut is **36.2 %**. Please quote the
denominator with the percentage.

**Is it enough?** In characters, no: N4 went 0.4174 → 0.4014, i.e. excess over chance 0.0841 →
0.0681 (−19 %), and macro AUROC went *up* (0.5750 → 0.5793). In tokens — the unit the model
actually consumes — **N4-tok = 0.3623 against chance 0.3333**, and the class means are within 1.2
tokens on a 13-token sd (§0.2a).

**What I would require, concretely, and none of it costs a GPU hour extra:**
1. report `N4` in **both** units, and declare the token unit primary, because the representational
   nuisance length could create is positional and positions are tokens;
2. report N4 **per pairwise contrast** — it is 0.6152 on bomb-vs-knife in chars, which is where
   the whole 3-way effect comes from;
3. add a **length-residualised probe** as a preregistered secondary: on TRAIN only, regress the
   codeword hidden state on prompt token count and refit the probe on residuals. If the probe
   survives residualisation, length is closed; if it does not, the claim was length.
4. do **not** run a third matching round. `R-102` is right that the rule forbids it, and the rule
   should hold.

## 5. Could it be template identity?

**No — this one is genuinely closed, and it is the strongest single piece of evidence the bank is
sound.** N6 template-id-only = 0.3333 accuracy / 0.5000 AUROC, z = 0.00, on both the probe
population (1,380 test rows) and all of cell C (6,624 test rows)
(`reports/DCS_TS116N_LEAKAGE_AUDIT.md:317-318`; reproduced on `ts116m`, log:1404-1405). The check
was proved able to fail: the `template_leak` mutation flips it PASS → FAIL
(`reports/DCS_TS116N_LEAKAGE_AUDIT.md:404-405`). N6 is also the VOID trigger
(`configs/dcs_ts_pr046.json:258-261`), so it is wired to a consequence, not just printed.

The one thing that must not be over-claimed: N6 at chance proves **alignment**, not
**generalisation across templates**. `Q-006`/`C-067` — the LOBO template-family null with mean
0.8494 — is still unresolved (log:213-221), and mandate §5.4 already bars a template-generalisation
claim. Keep it barred.

## 6. Could it be lexical leakage?

**Closed for the literal concept word; not closed for near-lexical cues.**

- `C-076` was real, and I reproduced it exactly: 15/1,856 rows per codeword on `ts116n`, in 6
  domains, 3 train / 1 validation / **2 test** (`instructional`, `physio_gym`). A literal
  `knives` inside a cell-C prompt is an outright label in the probe's own population.
- The fix is confirmed on the artifact: **0 of 11,136** cell-C × `semantic_one_word` rows across
  all six `ts116m` banks contain any of `bomb|bombs|knife|knives|gun|guns` (my count), and
  **0 of 13,920** `tsm` harm sentences are non-unit-substitutable or name another concept.
- `C-079` then found the two mirror-image defects (plural-only survives substitution;
  case-insensitive counting vs a three-form substituter) and the build **refused** with 170
  violations rather than shipping (log:1327-1370). The named pattern — *the checker's notion of an
  occurrence must be exactly the transformer's* — is the correct generalisation and should go into
  the write-up as a methods note.
- **What remains:** N5b/N5c show that masking the concept word is a **no-op to four decimals**
  (`reports/DCS_TS116N_LEAKAGE_AUDIT.md:250-252`) — the label is not carried by the word, it is
  carried by everything around it, at 0.92. That is not "leakage" in the bug sense; it is the
  treatment. But it does mean the phrase "leakage controls passed" must never be written as if it
  meant "the text does not reveal the concept". It reveals it at 0.92.

## 7. Did we train on a test domain? Did selection use TEST?

**No training-on-test found. Two disclosures are owed.**

- The split is by **domain**, in a new field `dsplit`, frozen before any outcome, from the pool
  keys, one shuffle at seed `202609061`, and `--write` refuses to overwrite
  (log:756-778). I confirmed 70/23/23 in `assign` and that the primary population joins on domain.
  The `split` field already in the banks is a *within-domain* sentence cut and all 116 domains
  straddle it (log:344-350) — using it would have been the leak; it was not used.
- Selection discipline is written into the config (`configs/dcs_ts_pr046.json:167`) and is backed
  by a measured reason: validation-selected FPR 0.0467 vs test-selected 0.4433 over the real
  36-point grid, 300 reps (`:168`). This is the single best-instrumented decision in the phase.
- **Disclosure 1:** two of the six old discovery domains whose accuracies supply the power
  analysis' SD — `instructional` and `lab_safety` — are in **TEST**
  (`reports/DCS_TS_POWER_ANALYSIS.md:161-167`; I checked their `dsplit`). No hyperparameter or
  threshold derives from them, so this does not inflate type-I rate; but the effect-size prior is
  not fully independent of the test set and should be said in one sentence.
- **Disclosure 2:** the length-matcher's shared quantile target is pooled over the three concepts'
  candidates **within each domain, including test domains**
  (`scripts/dcs_ts_length_match_pools.py:137-140`). It never sees a label-relevant outcome — it is
  corpus construction — so it is not selection. Say so explicitly rather than leaving a reader to
  wonder.

## 8. Is the read site downstream of any intervention we plan?

**For `PR-046`, the question does not bind — there is no intervention.** The probe reads
`codeword_last` (`configs/dcs_ts_pr046.json:200`). Fine for a decoding claim.

**Three carry-forward hazards, all currently unaddressed:**

1. **The read site must not be reused for the causal test.** `codeword_last` is the *intervention
   site* for any codeword-row knockout, so reading there is exactly the `C-068` degeneracy that
   made gate R6 CANNOT ANSWER (log:118-127). The downstream neutral site is already nominated —
   `pos = len(input_ids) − 9`, `' actually'`, codeword+1 (log:800-812) — and must be the read site
   for CLAIM C/D.
2. **The layer grid starts at 6** (`configs/dcs_ts_pr046.json:201-211`). That is harmless for a
   probe, but mandate §8.2 (`:668-674`) bans L6 as a *causal* read site, and the previous phase's
   worst error was importing a probe-selected layer into a causal test. Preregister now that the
   probe's selected layer does not automatically become the mechanism layer.
3. **The token-role map and the read-site nomination were computed on the VOID `ts116` bank.**
   `outputs/dcs_ts/token_roles_ts116.json.gz` and `reports/DCS_TS_TOKEN_ROLE_MAP.md` are
   `ts116`-derived (log:795-830); the sidecar `outputs/dcs_ts/ts116_sidecar.jsonl.gz` likewise.
   The prompt tails are shared skeleton and I confirmed by inspection that `ts116m` cell-C rows
   still end *"…what does the word button actually refer to?"*, so the nomination will almost
   certainly survive — but the prompt-length range, the "only position −10 varies" claim, and the
   K-rung mapping are **length-dependent** and were measured on different demo text (`ts116m` mean
   196.2 tokens; the map reports a 196–280 range on `ts116`). **A-036 must be re-run on `ts116m`
   before it is cited.** It is not in the "still required before extraction" list (log:1214-1222).
   This is the same class as inheriting the `A-037` blacklist, which the phase correctly refused
   to do.

## 9. Do the controls actually test the alternative?

**Partly. Four of the eight nulls are load-bearing and demonstrably able to fail; two do not test
the alternative they are named for; two alternatives have no control at all.**

| null | tests what it claims? | evidence |
|---|---|---|
| N1 n_ex=0 | **yes** — 0.3333/0.5000 on every baseline; localises signal to the demo block | log:1402 |
| N2 domain permutation | **yes**, and row-level is explicitly banned (measured FPR 0.2000) | `configs/dcs_ts_pr046.json:229-232` |
| N3 full-prompt leakage | **yes**, and now passes at 0/11,136 (my count) | §6 |
| N6 template-id | **yes**, wired to VOID | §5 |
| N4 length | **weakly** — wrong unit, no per-contrast breakdown | §4 |
| N5 TF-IDF | **no** — reads the treatment; this is `C-078` and it is correct | §12 |
| N7 codeword-only | pipeline sanity only | — |
| N8 label permutation through selection | **yes**, if actually implemented | analyzer does not exist yet |
| *generic remapping* | **absent** | §1 |
| *harm severity / register* | **absent as a control**; measured and kept | §2, Part C |

Two further gaps worth naming:
- **cell-A controls are the right shape and are at exact chance** (0.3333/0.5000 for length,
  TF-IDF and hedge+register: log:1403) — that is a strong "the instrument reads nothing when there
  is nothing" result and should be quoted;
- **the `n_examples=8` replication is declared but no gate is attached to it**
  (`configs/dcs_ts_pr046.json:101`). Declare in advance what a dose-4/dose-8 disagreement means,
  or it becomes a post-hoc choice.

## 10. Is n_domains sufficient?

**For the headline 3-way contrast, yes with a caveat. For the contrast that actually carries
CLAIM A (knife-vs-gun, §0.2b), UNKNOWN, and probably not at the same margin.**

- The power work is unusually good: p-floors published next to p-values, B = 10,000
  (`configs/dcs_ts_pr046.json:181,183`), domain as the unit, ICC 0.0884 → DEFF 6.22 → n_eff = 222
  of 1,380 test rows (`:217-220`), and a row-level p explicitly refused. The sign-test floor at
  n = 23 is 2.384e-07 (I confirm: 2/2²³).
- **The caveat is stated but its consequence is not carried into the verdict vocabulary.** The SD
  0.1406 rests on **5 df** from six domains of a *different, unaligned* bank
  (`reports/DCS_TS_POWER_ANALYSIS.md:150-175`); at its 95 % upper bound 0.3439 the MDE degrades
  0.0925 → 0.2102 (`configs/dcs_ts_pr046.json:214-216`). `PR-046` defines NEGATIVE as
  "not significant, WITH power ≥ 0.8 for the MDE below" (`:187`) — and "the MDE below" is the
  *projected* one. **Requirement: the NEGATIVE label must be earned against the realised
  between-domain SD measured on the test folds, not the projected one.** Otherwise a null on a
  noisier-than-expected population gets labelled NEGATIVE when it is CANNOT ANSWER. Add one line
  to the analyzer.
- The flip trigger (train-only, SD > 0.25 or LODO mean < 0.55 → rebuild 58/29/29,
  `configs/dcs_ts_pr046.json:212-216`) is the right instrument and is checkable before any test
  read. Keep it.
- **Independence, not count, is the binding limit.** Median inter-domain TF-IDF cosine 0.581 (my
  measurement, 6,670 pairs) / 0.752 (`A-040`'s instrument): 115 domains generated from one
  template family are not 115 independent draws. The domain-level permutation handles the
  *estimator*, but the **generalisation** claim is bounded by the corpus, and that sentence must
  appear next to the n.

## 11. Are we calling anything CANNOT ANSWER a null, or vice versa?

**Discipline is good; two specific risks.**

Right now: `R-098` was withdrawn as VOID rather than reported as a 0.333 null (log:661-760) —
which is the single best decision of the phase, because a probe pinned to 1/3 by arithmetic would
have been published as "the model does not represent the concept". `PHASE 7`/R8 stays CANNOT
ANSWER; ρ = +0.60 stays uncitable; gate R6 stays CANNOT ANSWER (log:110-130). The verdict table
at log:26-33 is used strictly.

Risks:
1. the NEGATIVE-vs-CANNOT ANSWER boundary depends on the projected SD (§10);
2. `cannot_answer` is defined only as "option_mass shows the channel is disengaged, or a PHASE-4
   gate fails" (`configs/dcs_ts_pr046.json:188`). The `semantic_one_word` channel's absolute option
   mass is known in advance to sit near 1e-5 (log:601-607). **Preregister the numeric option-mass
   threshold now**, before the forward pass, or the CANNOT ANSWER verdict becomes a judgement call
   made after seeing the accuracy.

## 12. Did a failed preregistered metric tempt us to switch? — `C-078` under maximum scrutiny

### The facts, established from artifacts

- `PR-046` states, in the frozen file, that the register asymmetry is **kept and converted into
  the bar**: *"It is instead measured, published, and converted into the bar: N5 concept-masked
  TF-IDF becomes strong and the probe MUST beat it"* (`configs/dcs_ts_pr046.json:156`), and
  N5's `expect` field is literally `"the probe must beat it"` (`:250`).
- G5 measured N5c = 0.8870 / 0.9829 on `ts116n` (`reports/DCS_TS116N_LEAKAGE_AUDIT.md:248`), 0.9217
  on `ts116m` (log:1412). I get 0.9290 independently.
- `C-078` (log:1287-1319) declares the bar wrong, keeps the comparison, and proposes `PR-047`, a
  positional contrast.
- **Timing is verifiable and clean.** No hidden state exists (sacct, §0). N5c is a text
  classifier: it can be — and was — computed with zero GPU. The declaration therefore genuinely
  precedes any probe outcome. Nothing about the probe's value was knowable when the bar was
  retracted.

### The case that it is legitimate

The scientific argument is correct and it is not close. A hidden state at the codeword is a
deterministic, lossy function of the prompt text. A bag-of-bigrams over the demonstration block is
an *upper bound* on what any function of that text can recover. Requiring
`probe > text-classifier` is therefore not a nuisance bar at all — it is a requirement that a
lossy compression beat the thing it is a compression of, which no true positive could ever clear.
Mandate §6.6 (`:545-566`) asks for nuisance baselines and lists "lexical clues, different prompt
lengths, different role scaffolding" — *shortcuts*. The demo block is the treatment; `C-078`'s
reading of §6.6 is the correct one. And the handling followed the mandate's own remedy for a
mis-specified design (`§21:1466` *"New design = new preregistration"*): keep and report the
original comparison, open a new preregistration for the question actually asked.

### The case that it is goalpost-moving in effect

`PR-046` did not adopt N5 as an incidental baseline. It adopted N5 **as the designated answer to
the register confound** — that is the plain text of `:156`, and `Q-011` (log:1141-1147) says the
register question is *"the single most likely thing Matan will press on"* and answers it by
pointing at exactly this bar. Removing the bar therefore does not merely fix an over-strict
threshold: **it deletes the only preregistered defence against the confound the phase itself
named as its biggest exposure, and the replacement does not defend against it.** A positional
contrast asks *where* information sits. It is silent on *what* the information is. If the codeword
state encodes "this context is an alarm-framed threat context", a positional contrast can show
that encoding is localised at the codeword and CLAIM A would still be false. So the net effect of
`C-078` + `PR-047`, if `PR-047` is treated as the substitute, is: the strong bar that could not be
cleared is gone, and what replaces it tests a different proposition. That is what goalpost-moving
looks like from the outside even when every individual step was taken in good faith.

There is also a smaller structural point. `C-078` is the phase's **third** gate-alteration in one
day (`R-101`'s G3 split; `C-077`'s length trigger; `C-078`). The length trigger is impeccable —
the rule pre-existed the measurement. The G3 split is *described inaccurately*: the log says the
replacement pair is **"strictly stronger than the single gate it replaces"** (log:1195). It is
not. Old G3 demanded byte-identity on every cell-A row; G3b demands only that the forced-choice
query *restore under substitution* with demo-block and preamble identical — both of which are
**implied** by byte-identity. G3a+G3b is therefore strictly **weaker** on 1,840 rows and stronger
nowhere. The change was nonetheless *correct*, because old G3 was unsatisfiable by construction
(the forced-choice question names the concept). The honest sentence is *"the original gate was
mis-specified and impossible; the replacement is the strongest satisfiable version"*. **Fix that
sentence** — a reviewer who checks it and finds it false will discount `C-078` by association, and
`C-078` deserves better.

### Verdict

**Legitimate as a correction; illegitimate if `PR-047` is allowed to inherit N5's job.**

`C-078` correctly identifies a specification error and correctly refuses to delete the
measurement. Judged as "did the orchestrator move a threshold to make a result look better", the
answer is no, and the timing proves it: no result existed, and none could.

What would make it illegitimate, stated as a testable condition:
1. if any hidden state or probe output existed at the time — it did not (sacct);
2. if the N5c number stopped being reported — `PR-046` says it will be reported at whatever value
   (log:1300-1303); hold them to it;
3. **if the register confound ends up with no preregistered control at all** — this is the live
   risk and it is not yet closed;
4. if `PR-047` were written after the probe ran.

**Safeguards I would require, all cheap:**
- freeze `PR-047` **and** commit its analyzer **before** the first extraction job, with bank shas
  pinned, exactly as `PR-046` was;
- in `PR-047`, state in one sentence that it does **not** discharge `Q-011`, and name the control
  that does (Part C);
- keep N5c in the results table forever, with the `C-078` reasoning inline, so a reader sees the
  bar, the retraction and the reason together rather than only the survivor;
- add the pre-declared *interpretation* of N5c, which is the useful thing it actually gives you:
  **0.92 is the text-decodability ceiling**, and probe accuracy should be reported as a fraction
  of it, per position. That converts a discarded bar into a scale.

## 13. Would Matan accept these sentences after seeing the full table?

For the *bank*: yes, and this is the phase's real achievement. Six banks, 115 domains, cell C
differing in 115/115 domains while cell A is byte-identical in 3,680/3,680 rows (log:1160-1172),
a diagonal-dominant 3×3 affordance matrix (bomb 374, knife 520, gun 282 with largest off-diagonals
2/6/8, log:1235-1237), tier-1 explosive predicates bomb 4.07 % / knife 0.00 % / gun 0.09 % where
the old bank read 4.27 % for all three, N6 and N1 at exact chance, and three self-caught CRITICALs
before a single GPU hour. That table survives an adversarial reading.

For the *claim*: not yet, because there is no claim — nothing has been measured. If Matan is
shown the nuisance table as it stands he will ask, in this order: (1) *how much of your 3-way
accuracy is bomb-vs-everything?* (2) *your bomb demos are hedged 50 % of the time and your knife
demos 8 % — what happens when you match that?* (3) *is knife-vs-gun above chance?* **All three
questions are answerable from the same single forward pass and none of them is currently
preregistered.** Adding them costs nothing and is the difference between a defensible table and a
contested one.

---

# A. THE STRONGEST REMAINING THREAT TO CLAIM A, AND THE EXPERIMENT THAT KILLS IT

**Named precisely: CONTEXT-GIST, not codeword binding.**

> The codeword's hidden state at layer L encodes the *topic and threat-register of the
> demonstration block it sits after* — "this passage is about an alarming explosive-device
> incident" — rather than a binding of the token `button` to the concept BOMB. Under this
> hypothesis every token in the query inherits the same gist by attention, the probe at
> `codeword_last` succeeds, and CLAIM A is false.

It is the strongest threat because every piece of evidence now in hand is consistent with it:
demo-block TF-IDF recovers the concept at 0.929; hedge/register alone at 0.474 (0.711 on
bomb-vs-knife); threat framing differs 44.5 % vs 14.0 %; and a probe read at *any* position
downstream of the demonstrations would show the same thing. Note that the positional contrast
`PR-047` weakens the *localisation* version of this alternative but **not** the version above,
because gist is available at the codeword too.

**The experiment that kills it: a within-prompt two-codeword interference bank.**

Construct prompts that install **two different concepts on two different codewords in one prompt**
— interleaved demonstrations, `button` ↔ BOMB and `basket` ↔ KNIFE — then read the *same* frozen
probe (trained on single-concept prompts, TRAIN domains only) at `button_last` and at
`basket_last` **within the same forward pass**.

Why it is decisive: the two read sites share, byte-for-byte and token-for-token, the prompt, the
topic, the register, the hedging, the length, the domain, the position band and the model state.
Context gist is *identical* at both. The only thing that differs is which token you read.
- If the probe outputs BOMB at `button_last` and KNIFE at `basket_last` — **binding**, and CLAIM A
  is supported in the strongest form available.
- If it outputs the same label at both (or the dominant/most-salient concept at both) —
  **gist**, and the honest sentence becomes *"the prompt's installed-concept content is decodable
  from downstream states; we could not show it is bound to the codeword."*

Cost and feasibility: prompt-only construction on the existing generator (both codewords and all
three concepts already exist on the same domain ids, mandate §6.3 `:491-502`), plus **one**
extraction job on the same model. Primary statistic: per-domain proportion of prompts where the
argmax at `button_last` equals the button-installed concept **and** the argmax at `basket_last`
equals the basket-installed concept, versus the two matched nulls (same label at both; labels
swapped), domain-level permutation over the 23 TEST domains. Preregister before building.
Predeclared limits: the dose per codeword halves (4 demos each → 8-demo prompts, which the bank
already supports at `n_examples=8`), and an interference bank is a *new* population, so it is a
new preregistration, not an amendment.

# B. IS `PR-047` SUFFICIENT? — AND THE CONTROL I WOULD DEMAND

**No. A positional contrast can separate "localised at the codeword" from "diffuse", but it
cannot separate "the codeword is represented as BOMB" from "the prompt is about bombs", because
under the second hypothesis the codeword position carries the gist too.** It is necessary and
worth running; it is not sufficient. Say that in `PR-047` itself.

## B.1 The positional design I would demand

**Positions** — all resolved from a token-role map **re-derived on `ts116m`** (see §8.3), all
offsets from the END of the sequence, never absolute (the absolute-index bug class has hit this
repo twice; log:814-818):

| id | position | role in the argument |
|---|---|---|
| **P1** | `codeword_last` — the last codeword occurrence in the query | the claim site |
| **P2** | codeword + 1 (`' actually'`, `len−9`) | downstream, non-lexical; comparable to prior `following` results |
| **P3** | last token of the demonstration block | **the ceiling of "the prompt is about bombs"** — if P1 ≤ P3 there is no codeword-specific gain |
| **P4** | final `'?'` of the query (`K=6`) | query content, maximally distant from the codeword |
| **P5** | last token of the **preamble**, strictly before the first demonstration | **causal floor** — must be at chance; under causal attention it cannot see the demos. If it is above chance the pipeline is broken and the run is VOID |
| **P6** | codeword − 1 (the token immediately before the codeword) | position-adjacent, token-identity-different: isolates "the codeword" from "that place in the sentence" |
| **P7** | P1's offset in **cell A** (`benign_literal`) rows | no installation, same site; must be at chance (already 0.3333 for all text baselines) |

**Layers:** the full frozen grid 6–14 (`configs/dcs_ts_pr046.json:201-211`), applied **identically
to every position**. One hyperparameter set, selected once on the 23 VALIDATION domains at P1, then
**frozen and reused at every position**. Selecting the layer per position would compare seven
maxima against one and inflate P1's rivals or P1 itself depending on order. Report the full
7 × 9 layer × position accuracy surface with `SELECTION_TRACE.inert` and `n_tied_at_best` persisted
(`:212`), because a flat surface here is exactly the `C-070` failure.

**Statistic:** per test domain d, Δ_d = acc_d(P1) − acc_d(P3). Primary = mean Δ over the 23 TEST
domains, tested by **paired domain-level permutation** (sign-flip of Δ_d), B = 10,000, p published
next to its floor 9.999e-05, plus a two-sided sign test (floor 2.384e-07). Preregister the
direction (Δ > 0), the MDE from the realised paired SD, and the reading of Δ ≤ 0 in advance:
*"decodable throughout the post-demonstration context, with no codeword-specific localisation"*.
Report P2, P4, P6, P7 as the profile and P5 as the VOID trigger.

## B.2 The control the positional design does **not** provide, and that I would demand alongside

Three additions, all from the same forward pass:

1. **The knife-vs-gun identity gate.** Preregister the 2-way knife-vs-gun probe at P1 on the 23
   TEST domains as the **CLAIM A identity gate**, because it is the contrast where register buys
   0.037 and length buys 0.0435 (in tokens) over chance, while the text still carries 0.9435.
   CLAIM A should require *both* the 3-way primary and knife-vs-gun above chance. If 3-way passes
   and knife-vs-gun fails, the supported claim is **harm-salience**, not identity, and the phase
   should say so.
2. **The hedge-free stratum.** Re-evaluate the frozen probe on the class-balanced hedge-free TEST
   subsample (115 per class, 345 rows, 23 domains, §0.2c). No retraining, no reselection — the same
   frozen model, a preregistered subpopulation. If accuracy holds, the register alternative is
   quantitatively bounded; if it collapses, `Q-011` is answered in the unwelcome direction and that
   is a finding.
3. **The text ceiling as a scale, per position.** For every position report probe accuracy
   *and* N5c on the identical rows, so the table reads "at the codeword the state recovers X of the
   0.92 the text itself carries; at the last demo token, Y". That is the honest use of the number
   `C-078` retired as a bar.

# C. IS THE UNMATCHED REGISTER ASYMMETRY DEFENSIBLE?

**The decision to keep it is defensible. The decision to leave it without a control is not.**

Defensible half, and I agree with it: bomb in workplace incident English *is* overwhelmingly a
suspected bomb; knife is simply present (log:1114-1120). Equalising register means writing
demonstrations no one would write, and demonstrations that differ only cosmetically are precisely
how `R-098` ended with no manipulation at all. Register is partly constitutive of the concept, so
"matching it away" would remove signal along with confound. `Q-011`'s framing (log:1141-1147) is
right that it is *not fully separable*.

Not defensible: `PR-046`'s answer to this was "N5 becomes the bar and the probe must beat it"
(`configs/dcs_ts_pr046.json:156`), and `C-078` removed that bar. As of now the phase's single
largest named exposure has **zero** preregistered control. Hedge-only reaches 0.4739 / AUROC
0.6374 and hedge+register 0.5014 / 0.6929 on `ts116m` (log:1407-1408) — *hand-written regexes with
no lexical content get 43 % of the way from chance to the text ceiling*
(`reports/DCS_TS116N_LEAKAGE_AUDIT.md:288-292`).

**Minimum fix — three items, no new generation, no extra GPU:**
1. **the knife-vs-gun gate** (B.2.1) — a register-clean contrast, measured not asserted;
2. **the hedge-free stratified re-analysis** (B.2.2) — 345 TEST rows already exist;
3. **a hedge-count covariate**: report the probe's per-domain accuracy conditioned on block hedge
   count (0, 1, ≥2), and refit the probe on hedge-residualised states as a preregistered
   secondary (residualise on TRAIN only).

If all three hold, the write-up may say the effect is not reducible to register **and can quote
the numbers**. If any fails, the correct sentence is *"part of what we decode is the discourse
register in which the concept naturally occurs; we cannot fully separate the two, and here is how
much"* — which is a perfectly publishable sentence and far better than being asked for it.

# D. EVERY SENTENCE THE PHASE COULD WRITE FOR MATAN TODAY

Nothing has been measured on a model. Everything below is about the **data foundation**.

## SAFE — supported by a committed artifact, with the denominator

| # | sentence | evidence |
|---|---|---|
| D1 | "We built six aligned banks, {button, basket} × {bomb, knife, gun}, over 115 domains, in which the harm demonstrations differ by concept and **every other byte is shared**: cell A is byte-identical across concepts in 3,680/3,680 concept-free rows, and cell C differs in 115/115 domains for both codewords." | log:1160-1172; `configs/dcs_ts_pr046.json:296-300` |
| D2 | "The concepts are genuinely different concepts: the 3×3 affordance matrix is diagonal-dominant (bomb 374, knife 520, gun 282; largest off-diagonals 2, 6, 8) and tier-1 explosive predicates run bomb 4.07 % / knife 0.00 % / gun 0.09 %, where the previous bank read 4.27 % for all three because they were the same sentences." | log:1233-1239 |
| D3 | "Template identity carries no concept information: a template-id-only classifier sits at exactly 0.3333 accuracy / 0.5000 AUROC on 1,380 probe-population test rows and on 6,624 cell-C test rows, and the check was proved able to fail under a planted leak." | `reports/DCS_TS116N_LEAKAGE_AUDIT.md:101-102,317-318,404-405` |
| D4 | "With zero demonstrations, every baseline is at exact chance — the signal, whatever it is, lives in the demonstration block." | log:1402 |
| D5 | "The split is by domain, 70/23/23, frozen from the domain roster alone before any hidden state existed, in a new field `dsplit` because the banks' existing `split` field is a within-domain sentence cut that all 116 domains straddle." | log:756-778 |
| D6 | "Selecting hyperparameters on test rather than validation inflates the false-positive rate 9.5× on our real 36-point grid (0.4433 vs 0.0467 over 300 noise replicates); that is why selection is validation-only." | `configs/dcs_ts_pr046.json:168` |
| D7 | "Three CRITICAL defects in our own bank were caught by prompt-only gates before any GPU time: a total-alignment error that pinned any probe to 1/3 by arithmetic, a singular-only substitution that shipped a literal plural into 30 of 3,680 primary rows, and two mirror-image occurrence-counting bugs. Each cost CPU, not GPU." | `C-074` log:661-760; `C-076` log:1244-1268; `C-079` log:1327-1370 |
| D8 | "The literal concept word does not appear in the probe's population: 0 of 11,136 cell-C × `semantic_one_word` rows across all six banks contain any inflection of bomb, knife or gun." | my count on `ts116m` |
| D9 | "A preregistered length trigger fired and was followed: the rule was written before the measurement, the remedy was deterministic and outcome-blind, and it was reported to have largely failed in characters rather than quietly re-run." | `configs/dcs_ts_pr046.json:157`; `C-077` log:1269-1286; `R-102` log:1388-1400 |
| D10 | "Surface text predicts the installed concept at 0.92 — that is the treatment, not a leak, and it is the ceiling any representational readout is a lossy compression of." | log:1412; `C-078` log:1287-1319 |

## NEEDS QUALIFICATION — true, but incomplete without the stated rider

| # | sentence | required rider |
|---|---|---|
| D11 | "We have a thesis-scale population of 115 domains." | *"…but the domains are not independent draws: median inter-domain text cosine is 0.58–0.75 because every harm pool is a rewrite within one generator family. n=115 buys resolution, not independence."* |
| D12 | "The bank is aligned so only the manipulation differs." | *"…aligned in everything the generator controls. It is **not** matched on discourse register: bomb demonstrations are hedged 5.5–14 % at sentence level and 49 % at 4-demo-block level against knife's 5.5 %, and hedge counts alone classify concept at 0.474."* |
| D13 | "Length is controlled." | *"…in tokens, effectively (N4-tok 0.3623 vs chance 0.3333, class means within 1.2 tokens on a 13-token sd). In characters it is not: N4 = 0.4014, and 0.6152 on bomb-vs-knife. We report both and defend the claim in tokens."* |
| D14 | "We excluded one domain, prospectively and on prompt text alone." | *"`restaurant_kitchen`, because a kitchen keeps naming knives in its bomb and gun pools; it sits in TRAIN, so validation and test stay 23/23. Note its regenerated bomb pool also shows the mass-noun frame (`a bomb of unsealed fish`), so the exclusion is over-determined."* |
| D15 | "Our power analysis says n=23 test domains gives MDE 0.0925 against an old effect of 0.4152." | *"…on a between-domain SD with 5 degrees of freedom, taken from six domains of the **old, unaligned** bank; at its 95 % upper bound the MDE degrades to 0.2102. Two of those six domains are now in TEST."* |
| D16 | "Concept-masked TF-IDF was preregistered as a bar and we retracted it." | *"…because a text classifier reads the treatment and a representation probe is a lossy function of that same text; the comparison is still reported at 0.92 and is used as a ceiling, not a bar. Retracted before any hidden state existed."* |
| D17 | "The read site and the token-role map are established." | *"…on the `ts116` bank, which is VOID. They must be re-derived on `ts116m` before being cited; the prompt-length range in particular is bank-dependent."* |
| D18 | "Gate G3 was split into G3a and G3b." | *"The log calls the replacement 'strictly stronger'; it is not — it is strictly weaker on 1,840 forced-choice rows. It is nonetheless correct, because the original gate was unsatisfiable: the forced-choice question names the concept by construction. Please fix that sentence."* |

## MUST NOT SAY — today, on this evidence

| # | sentence | why |
|---|---|---|
| D19 | "The codeword representation carries the concept's identity." | No hidden state exists. Nothing has been measured. |
| D20 | "…not merely generic remapping." | No remapping control exists in `PR-046` (§1). |
| D21 | "…not merely generic harmfulness." | Threat framing differs 44.5 % / 14.0 % / 18.3 % across concepts and is uncontrolled (§2). |
| D22 | "Leakage controls passed, so the prompt does not reveal the concept." | The prompt reveals it at 0.92. What passed is that the concept *word* and the *template* do not. |
| D23 | "Length is not a confound." | 0.4014 in characters, and 0.6152 on bomb-vs-knife (§4). Say "in tokens", or say the number. |
| D24 | "Register is controlled / matched." | It is deliberately kept, and as of `C-078` it has no preregistered control (Part C). |
| D25 | "The old 0.7485 concept probe replicates / is confirmed." | It is PRELIMINARY under `Q-007` (log:735-740) and may have separated three corpora (`A-034.1`). Nothing has re-measured it. |
| D26 | "n=115 gives us independent thesis-scale generalisation." | Independence is bounded by the corpus (D11), and template generalisation has no valid instrument (`C-067`, `Q-006`). |
| D27 | "PR-047 answers whether the codeword is represented as BOMB." | It answers *where*, not *what* (Part B). |
| D28 | Every sentence already banned at mandate `:2017-2040`, unchanged — including "we are first to intervene on demo→query attention", "probe accuracy proves causal use", "club is a clean hard negative", and "a significant row-level p-value establishes a domain-level claim". | Standing ban; nothing in this phase has weakened any of them. |

---

## E. PROCESS ITEMS FOR THE ORCHESTRATOR (not scientific claims, but they gate them)

1. **`configs/dcs_ts_pr046.json` is stale.** Its status is `FROZEN` with `ts116n` bank shas pinned
   (`:22-49`), but the analysis population is now `ts116m` (`R-102`, built 03:02, six banks on
   disk). Re-pinning a frozen preregistration's population is a change of population: per mandate
   `§21:1466` it wants either an explicit amendment entry recording old and new shas and the reason,
   or `PR-046b`. The G1–G3 results embedded at `:295-301` are `ts116n` results and must be replaced
   by the `ts116m` run, not inherited.
2. **The analyzer does not exist.** `configs/dcs_ts_pr046.json:288` names
   `scripts/dcs_ts_pr046_analysis.py` and `:7-11` asserts that it *"REFUSES to run if this file is
   absent, if any `*_sha` field is still null, or if a gate it needs is missing"*. No such file is
   on disk, and `analyzer_commit` is `null`. Until it is committed, the machine-readable
   preregistration is exactly the thing it was written to prevent — a threshold no code path reads.
   Commit it before the first extraction.
3. **`multiplicity` is a required §21 field (`:1443`) and is absent.** Two codewords × two doses ×
   several sub-contrasts are in play. Name the single primary test and the correction for the rest.
4. **The `option_mass` CANNOT-ANSWER threshold is unnumbered** (§11).
5. **The NEGATIVE label must be earned against the realised SD**, not the projected one (§10).
6. **Re-run `A-036` (token roles / read site) and rebuild the sidecar on `ts116m`** before either is
   cited; both current artifacts are `ts116`-derived (§8.3). Mandate deliverable 7 (`:568-615`)
   is also unmet for the live bank.
7. **`R-102`'s "40.8 %" and the "strictly stronger" sentence at log:1195** both need a denominator
   or a correction (§4, §12).

---

## F. HOW MY OWN NUMBERS WERE PRODUCED (so they can be checked or discarded)

Python 3.12, `/home/sharifm/students/omeryosef/miniconda3/envs/poc_stage2/bin/python`,
scikit-learn `LogisticRegression(max_iter=5000)` on standardised features, TF-IDF
`min_df=2, ngram_range=(1,2), sublinear_tf=True` fit on TRAIN rows only. Population: rows of
`data/boombness_prompts/boombness_prompt_bank_ts116m_button_{bomb,knife,gun}.jsonl` with
`cell == "C"`, `query_kind == "semantic_one_word"`, `n_examples == 4`, `domain != "restaurant_kitchen"`
(3,450 rows; 1,150 per concept). Split from `dcs_ts116_domain_split.json` → `assign`. All reported
accuracies are **domain-mean over the 23 TEST domains** (which equals the row accuracy here
because every test domain contributes 30 rows). Tokenisation with
`meta-llama/Llama-3.1-8B-Instruct` under `HF_HUB_OFFLINE=1`, the revision pinned at
`configs/dcs_ts_pr046.json:193`. Pool-level statistics are over
`demo_pools_116dom_{ts,tsm}_{bomb,knife,gun}.json`, harm valence only, 4,640 sentences per concept.
Threat/mundane/hedge lexicons are stated inline in §2 and §0.2c; they are my own and are coarse —
they are offered as effect-size indicators, not as instruments.

**Nothing in this report was measured on a model's hidden states, because none exist yet.**
