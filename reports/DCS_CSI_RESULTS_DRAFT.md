# CSI sprint — RESULTS SECTION, first draft

**Created S-417, 2026-09-25.** Source of every sentence: `reports/DCS_CSI_CLAIM_TABLE.md`. This
file **adds no claim and softens no caveat**. Where the table forbids a phrasing, the forbidden
phrasing is named here too, so a later editor cannot reintroduce it by not knowing about it.

⛔ **STATUS: DRAFT PROSE, NOT A CLAIM SOURCE.** If this file and the claim table ever disagree,
**the claim table wins** and this file is the thing that is wrong. Figures in §2–§4 for **D39/D40/D41** were re-derived by hand in S-373, S-411 and S-415; **§1's D37
figures were re-derived in S-417** from `DCS_CSI_PR015_CELL_CENSUS_3HEADS_validation.json`, and
**§4's D38 figures come from S-328**, not from any of those three — S-307 is the correction entry
for **D37**, and §1 cites it for exactly that. None is copied from a
summary field. ⚠ *The header of a draft is the first sentence a sceptical reviewer tests; this one
names its scope rather than claiming a blanket.*

---

## SCOPE — what this draft covers, and what it LEAVES OUT

✅ **UPDATED S-436 — the head-level half is now DRAFTED as §H and this block is its index.**
§1–§4 report the five cell-census families (PR-CSI-014, 015, 016, 018, 020); **§H reports the
head-level results, which the cell-level half subdivides and therefore depends on.** §H is written
second and belongs first. ⚠ **A THIRD part — the axis, necessity and dissociation families
(PR-CSI-001–009, 20 claim-table rows) — is **PARTLY PRESENT**: 🔴 *CORRECTED S-453 — this block said "two … and eighteen" long after the
count reached ten:* **TEN of its rows are drafted as §A (D12, D18, D19, D23, D24, D25, D26, D27,
D29, D30) and TEN are not** (D13, D14, D15, D16, D17, D20, D21, D22, D28, D31). The
four rows below are the D-rows §H covers; it also reports **AM-36** and draws on AM-26, AM-27, AM-30, AM-33, AM-34 and AM-37:

| row | what §H reports | where |
|---|---|---|
| **D32** | eight head indices carry most of the knockout's effect on basket, **replicating on the held-out split** at the preregistered bar | it is the result the cell-level work *subdivides*; §1–§3 localise within heads D32 selected |
| **D33** | that 8-head set is **rank 1 of 21** against a control family drawn from all 32 band heads | a **SECOND and harder** rank-based certification — D32 is also rank 1 of 21, but against the candidate's complement; → H.1b |
| **D34** | four heads (2, 19, 17, 23) each clear the family's own null anchor, **all four inside `HD_TOPK` and none outside it** | it is where §1's four heads come from |
| **D35** | 🔴 head 2's single-head effect, selected on basket by a rule frozen beforehand, **DOES NOT REPLICATE on button** — ci95 [−0.015452, +0.006019] **crosses zero** | **the sprint's one EMPIRICAL negative** |

⚠ **D35 was the omission that could flatter, and it is why §H was drafted before anything else was
added.** §4 offers "one CANNOT ANSWER and one honest **methodological** negative", and a reader
might have taken that as the full negative ledger. **It is not** — the empirical negative is §H.3,
and it is now in the file.

🔴 **CORRECTED S-437 — THIS DRAFT IS TWO OF THREE PARTS, NOT TWO HALVES.** S-435 said the remaining
uncited rows were "predecessor-phase". **That was wrong for 20 of them**, and the row-by-row audit
it declined is what found it. Classified by reading each row rather than by pattern:

| | rows | status |
|---|---|---|
| predecessor-phase, pre-CSI | 10 — D1–D4, D6–D11 | correctly out of scope |
| **CSI-sprint results, GENUINELY OMITTED** | **20 — D12–D31** | 🔴 **a whole third part** |
| covered in §3/§4 prose, not cited by ID | 3 — D40-a, D40-b, D41-a | fine |

⚠ **UPDATED S-439/S-440, RE-COUNTED S-453.** §A began as D19's bidirectional conjunction and
D24's matched-power dissociation with D18, D23 and D29 as supports; it now also carries D12 (§A.3)
and D25/D26/D27/D30 (§A.4, §A.4a, §A.4b). **That is an increment, not the part: TEN of the twenty
are drafted and TEN remain** — D13, D14, D15, D16,
D17, D20, D21, D22, D28, D31. (⚠ This count has been wrong twice: SCOPE said eighteen when it was
fifteen, and a re-measure said thirteen by reading a range as a list, S-449.)

**The omitted rows are the AXIS, NECESSITY and DISSOCIATION families — PR-CSI-001 through 009**: the
rank-1 installation axis and its control families, the necessity direction, the button/basket
codeword dissociation at matched power, and the cross-codeword axis swap. 🔴 *CORRECTED S-453 — this sentence outlived its count by three ticks:* **ten of them are
in this file, as §A; the ten listed above are not.** §L.3 touches two of these results (necessity, basket-at-L20) only
to limit them, which is how the gap stayed invisible for so long — they appeared as *limitations of
results the draft never stated*, and for the **ten** still undrafted they still do.

⛔ **Review coverage is UNEVEN and every pass so far has found real defects:** §1–§6 twice, §M once
(S-421, six mismatches against the source), §L once, **§H once** (S-438: thirteen findings, two that
would have misled), and **§A and §M.8 NOT AT ALL** — they are the newest prose in the file.

---

## 0. One paragraph of setup

We ask where in a transformer a *codeword* — a token the model has been instructed to emit in place
of a concept — is installed. The instrument ablates a single attention cell `(layer, head)` during
the prefill of an in-context prompt and measures the change in the **installation probability** at
a fixed position: the two-way softmax between the concept and codeword continuations,
`y = exp(logp_concept) / (exp(logp_concept) + exp(logp_codeword))`, which lies in [0, 1]. ⚠ **It is
not the `semantic_logodds` field**, which exists in every row and equals `logp_concept −
logp_codeword`. That is the same contrast on **a different scale**: the endpoint is exactly
`sigmoid(semantic_logodds)`, so **no rank in this draft changes with the choice**: every argmax
**of this endpoint** — §1's four peaks, §2's, §3's, and §4's D38 — is invariant, **while every
effect size is not.** ⚠ §4's D41 argmaxes are of a **different statistic** (a direct-path
projection, not `y`), so they are outside this argument. Published
`installation_by_arm` values such as 0.47336 / 0.23972 are probabilities, and reading an effect like
`E = −0.2269` as a change in log-odds would **overstate** it. §M.4 gives the full definition
including the channel filter. The statistical unit is the **domain**. The split manifest
`dcs_ts116_domain_split.json` assigns **70 train / 23 validation / 23 test**. 🔴 **Two populations
must be kept apart:** the *screen* is fitted on **67 train domains** — the 70 less three
whole-population domains every CSI prereg excludes, which are `train`-assigned (a config field once
mislabelled them `test_domains` and collapsed them to the count "3", the error AM-37/S-312
corrected) — while **every census reported here is read on the 23 VALIDATION domains.** So every effect, bar and argmax
in **§1–§4 and §H** rests on **23** domains rather than 67, and a 230-row read is n = 23 because the
domain is the unit. 🔴 **CORRECTED S-453 — this said "every effect below" until §A existed, and §A
is a large exception**: §A.3's TRAIN cell, §A.4a's two TRAIN cells and §A.4b's TRAIN factorial are
computed on the **67 TRAIN domains**, which are **disjoint** from these 23. Each says so where it
stands, and §A.4b's whole in-sample/held-out argument turns on the distinction. ⚠ **The confirmatory p's themselves are NOT over domains at all** — binomial, conditional and
permutation are functions of the **admitted heads**, `K = 6` in §2 and `K = 8` in §3, which is why
§3 can say "the margin is one head". The 23 domains are the n of the `E` and `bar(h)` estimates that
feed argmax and admission. *(§4's D41 figures are a TRAIN pilot on 67 domains and carry no
confirmatory p.)* **No arm of any family reported here touched a TEST domain — and TEST is
nonetheless NOT an available axis:**
it was read to completion on 2026-09-08 and is **selection-contaminated on knobs every CSI family
inherits** (AM-39). ⛔ *"TEST is unspent / untouched / available"* is a predecessor-phase belief
that S-314 refuted and D5 is annotated to block; it must not be re-imported. An
attribution *screen* computed on basket TRAIN nominates, for each head, the band layer carrying
most of that head's effect. Every confirmatory result below asks one question: **does the screen's
per-cell prediction hold up under intervention on data it was not fitted on?**

---

## 1. The screen's per-cell prediction holds at the LAYER coordinate on basket validation (D37)

On basket VALIDATION, of 27 candidate cells exactly **three clear their own preregistered
detectability bar**, one per head: `(17, L14)` **−0.02344221** against bar 0.009082 (**2.58×**),
`(19, L14)` **−0.04397480** against 0.010223 (**4.30×**), `(23, L7)` **−0.01851354** against
0.006615 (**2.80×**). With D36's head 2 at L10 this is **4 of 4 heads across splits** — screen
fitted on basket TRAIN (67 domains), census read on basket VALIDATION (23) — at **three distinct
layers** (7, 10, 14, 14).

⚠ **Three corrections are part of this claim, not footnotes** (S-307), and the draft states them
here rather than in a caveat list. **(a) What generalises is WHICH cell, not HOW MUCH:** the shares
are 96.1 / 80.2 / 109.6 / 112.2 % and do not generalise — head 17 is significantly **sub-additive**
(ci95 [70.4, 90.6] excludes 100 %) and head 23's apparent super-additivity is not resolvable (ci95
[92.9, 140.4] crosses 1.0). **(b)** The two L14 cells correlate **r = +0.719** across domains, so
this is **~3 effectively independent agreements, not 4**. **(c)** The four peaks together are
**58.8 %** of `CL_KO` (−0.133478 / −0.226961), so *"the mechanism is these four cells"* overstates
by ~1.7×. ⛔ **And the heads were chosen as D34's load-bearing four ON VALIDATION**, the same split
the census reads — so this is a statement about **load-bearing heads, not about heads**, and the
**layer** coordinate is held out while the **head** coordinate is not.

The obvious rival, that the band edge simply attracts everything, is **refuted by the screen's own
marginal**: L14 is the screen argmax for only **6 of 32** heads (the modal layer is L11 at 8/32), so
P(all four match) is **2.06e-04** under that marginal against 1.52e-04 uniform [†] — ⚠ **the uniform figure is a comparator, not a null.** The intervention argmax marginal is measured to concentrate on L10/L14 **for D40's eight-head multiset** (§3, §L.5); **no equivalent measurement exists for these four heads**, and AM-42 records that such corrections are specific to the multiset they were computed on — and **an all-L14
guesser scores 2 of 4.**

⛔ D37 is **descriptive**: no rank, no p, no control family. *"Cell (L,h) is the writer"* is
forbidden.

## 2. The prediction transfers across codewords, at a preregistered p (D39)

PR-CSI-018 took six **fresh** button heads and asked whether the basket-TRAIN screen's per-cell
prediction survives a change of codeword. All six were **admitted** by a power gate computed from
the family's own whole-head arm (`|E|/bar` = 2.4241, 2.8551, 2.8537, 1.8365, 1.5426, 2.4937; all
≥ 1.5). **K = 6, M = 5**: five of six put their intervention argmax at exactly the predicted cell,
across **four distinct layers** (L6, L8, L10, L11). The single miss is head 20, **whose prediction was L11** and whose argmax landed on L14 — ⚠ **a miss, not a finding about L14.**

**The claim is stated with the weakest of three preregistered p-values: conditional
`p = 0.012346`** (binomial 0.000092; permutation 0.005556 over 180 distinct assignments). The
**`K_unique = 2, M_unique = 2`: both unique-layer heads matched (11→L8, 29→L6)**, and AM-42 proves
analytically that a miss on *either* would have given `p_cond = 1 − (8/9)² = 17/81 = 0.209877` and no
certification **whatever the other four heads did**. ⚠ **So §2's conditional margin is TIGHTER than
§3's** — the cross-codeword result is the more fragile of the two on this axis. The
spanning rule is satisfied on four layers, so a shared band bias cannot account for the result, and
the permutation p is why the family exists — a bias says nothing about *which* head gets *which*
layer. VOID condition 8 passes on all six heads at ≤ 4.2e-09.

⛔ ***"p = 0.000092" is FORBIDDEN*** — the claim is the weakest of three, each named. ⛔ *"the screen
is a validated cell selector in general"* is forbidden: six heads on a second codeword, **every one
chosen because it was live there**. ⛔ **No post-hoc sharpness subsetting.** Head 20's screen margin
is the weakest of the six (1.07×); the result is **5 of 6, unqualified**.

## 3. It replicates on the original codeword (D40)

PR-CSI-020 repeated the test on basket VALIDATION cells with eight heads, **all eight admitted**
(`dropped_heads: []`). **K = 8, M = 6** — heads 4→L11, 6→L11, 11→L8, 13→L10, 18→L14, 21→L6 match;
heads 10 (argmax L7, predicted L12) and 27 (argmax L9, predicted L10) miss. The three p's:
binomial **0.000043** (exactly 619/14348907), conditional **0.005030** over the four unique-layer
heads {10, 11, 18, 21} of which three matched, permutation **2 of 10080 = 0.000198**. **The claim is
the weakest: conditional 0.005030.** Spanning satisfied across **five** layers (L6, L8, L10, L11,
L14).

⛔ **This is held out on SPLIT, not on CODEWORD.** D39 is the cross-codeword result and this is not;
**conflating them overstates both**. ⛔ The binomial alone may never be quoted: for this prediction
multiset a random screen matches at ≈0.1625 against the binomial's assumed 1/9. ⛔ No
margin-restricted subset may be reported, in either direction. ⛔ **Not a validated cell selector in
general** — eight heads, **every one chosen because it was live on basket** (the same restriction
§2 states for D39; it applies to both families). ⚠ **`M_unique = 3` sits ON the boundary:** at
`M_unique = 2` the conditional would be 0.063557 > alpha and the read could not have certified
whatever the other four heads did — **the margin is one head.** ⚠ **Three of the eight heads (6, 11,
27) were disclosed BY NAME before the read as a REPLICATION** of predictions PR-CSI-018 had already
tested on button, **not as an independent draw**; heads 6 and 11 match and **head 27 misses**. **No p
attaches to that subset and none was computed** — quoting a 2-of-3 or 4-of-5 rate is forbidden
whichever direction it points.

## 4. One CANNOT ANSWER, and one honest METHODOLOGICAL negative

**PR-CSI-016 could not test the question it asked (D38) — this is CANNOT ANSWER, NOT a negative result.** Both admitted heads matched at L14, so the
preregistered **spanning rule fired**: a shared top-of-band bias and a correct screen are
indistinguishable there. K = 2, M = 2 — and this is the one family grandfathered to `binomial_only` gating (§M.6), so **its p-gate PASSED and the spanning rule vetoed the PASS afterwards.** **The binomial is FORBIDDEN for this family** and is quoted below only inside the prohibition, because a ban that does not name what it bans cannot be checked. ⚠ **It is numerically identical to D39's certified conditional p in §2** — the same six digits appear as a certified result there and as a forbidden figure here, so an editor must keep the antecedents apart. Conditional 1.0
(K_unique = 0) and permutation 1.0 over a space of size **1**. The fallback delivered a head-level
cross-codeword test never run before: head 17 retains **98.3 %** of its basket whole-head effect on button, head 19 **88.7 %** (both ci95 excluding
0), head 23 **18.4 %** with **ci95 crossing zero** — ⚠ **an AMPLITUDE result only**: exploratorily, head 23's per-cell depth **shape** tracks across codewords at ρ = +0.817, so *"head 23 does not transfer"* is true of the amplitude and false of the shape (AM-41, **not preregistered**) — ⚠ **measured on the same 23 domains as the basket census, which INFLATES ρ, and nine cells are not nine independent units.** ⛔ *"The screen transfers across codewords"* and
the figure 0.012346 are forbidden from this family. ⛔ *"Head 23's mechanism is refuted"* is
forbidden — null on button is CANNOT ANSWER, not a negative.

**Rung 2 was attempted and is not reachable (D41).** Decodability was built, reviewed, executed and
piloted, then **closed without a validation read, by decision**. Four measurements: K = 8 is the
*whole* admissible population (0 of 7 fresh basket heads clear the frozen 1.5 gate, best 1.400; on
button **this same eight-head basket set** tops out at K = 2, and the arithmetic needs all four
reasons or it does not come to two: **heads 6, 11 and 27 are already cell-mapped on button** by
PR-CSI-018, so re-running them counts a known outcome as a fresh draw; **head 10** sits at 1.45,
below the gate; **head 21's** ci95 crosses zero; and **heads 4, 13 and 18** have no button
whole-head measurement at all, head 18 additionally predicting L14, the band-edge layer PR-CSI-018
excluded by design. **So only heads 4 and 13 are even conceivable, each needing its own button
`HD_` arm with admission unknown until it lands.** ⚠ **These are not the six BUTTON-selected heads
§2 admitted** — a different pool); the natural statistic is **confounded** — the direct-path projection
puts all 8 raw argmaxes in the top three of nine layers, P = (1/3)^8 = 1.524158e-04 [†]; a
layer-normalised statistic removes the confound and gives **M = 3 of 8 on train**; at that rate
**power is 0.1446**, and the PPV of a PASS is **0.24 / 0.42 / 0.55** at priors 0.10 / 0.20 / 0.30.
**At priors 0.10 and 0.20 a positive would more likely be false than true (PPV 0.24 / 0.42); only at a 0.30 prior does it exceed even odds (0.55).** On that arithmetic it was not run. 📌 **A reader weighing the priors differently should reach a different answer** — this was a decision, not a fact.

⛔ Not a claim that the concept is undecodable at these cells — **nothing was measured on a
held-out axis**. ⛔ Not a claim that rung 2 is unreachable in general.

> **[†] NOT a duplicated figure — do not "fix" either one.** §1's uniform baseline is `(1/9)^4`;
> §4's depth-confound probability is `(1/3)^8`. **These are equal — both are exactly 1/6561 =
> 1.524158e-04.** They are unrelated quantities (four heads each matching one of nine layers; eight
> heads each landing in the top three of nine) that coincide because `(1/9)^4 = (1/3)^8`. Verified
> S-417. **An editor who assumes a copy-paste slip and changes one will introduce an error.**

## 5. What this evidence is, and what it is not

**Every certified claim here is RUNG 1 — NECESSITY** on the ladder of `arXiv:2606.08292`
(necessity / decodability / same-prompt repair / cross-prompt transfer). Their result is that the
four are **separable**: passing 1–3 does not imply 4. ⚠ **"Transfers across codewords" in §2 is NOT the ladder's rung-4 transfer** — rung 4 moves an
activation *state* between prompts requiring different operations, while §2 re-runs the same
intervention on a different codeword and asks whether the prediction holds. That is **replication of
a rung-1 finding across stimuli and has no number on their ladder** (AM-34); claiming otherwise
would be matching the form and not the operation. **Nothing in this sprint has reached rung 2,
3 or 4**, and D41 records the attempt that established rung 2 is out of reach at this head count.

⛔ **There is no control family of arbitrary cells anywhere in this sprint**, so *"cell (L,h) is the
writer"* is unavailable for every result above. The reason is measured, not assumed: no admissible
held-out axis exists, and restricting controls to one head's nine cells returns the 1/9 floor, **which is above α at every attainable effect size.**
⛔ The **source** question — whether the demonstrations supply the installed content — is open with
no confirmatory instrument; the mass measurement licenses a **refutation reading only**.
⛔ **TEST is spent and selection-contaminated** and is not an available axis.

## 6. Reproducibility

Both published PASSes **replay from their landed artefacts**. Each family's frozen read recipe was
re-run verbatim at its own read commit and at HEAD, separated by a +307/−148 reader refactor:
GATE 0 exit 0 at every version (62/62 for D39, 82/82 for D40); the census is **byte-identical** to
the published artefact at the read commit (md5 `512f42a1`, `e7f09f67`); at HEAD each differs only by
two **added** disclosure keys, and each argmax artefact differs only in the input path. Every value
the claims rest on is identical at every version.

⚠ **Byte-identity includes a sentence now known FALSE.** Both artefacts' `GATING_FLOOR.WHAT_THIS_IS`
says a floor above α gives CANNOT ANSWER and **never** FAIL — which holds only at K < 3; at K ≥ 3 it
is a FAIL with an unwinnability warning. It is a disclosure that **decided nothing** in either family,
and it is **deliberately not rewritten**, because rewriting a read after the fact is what VOID 12
forbids and this very byte-identity claim rests on the files as they shipped.

⚠ **D39's readers themselves moved** — `scripts/` changed by +559/−18 across four files while its
62 arms were landing, three of them the readers its frozen recipe names, and PR-CSI-018's read
carried **no VOID 11** because that condition was introduced for the *next* family. **A frozen
recipe and a frozen reader are different guarantees, and only the first was originally claimed.**
The decisive test was run (S-414): GATE 0 62/62 at both commits, a byte-identical census, and **not
one number the claim rests on moved**.

⚠ This is **reproducibility, not corroboration**: it re-reads the same arms, strengthens no p, and
tests the reader rather than the arm. ⛔ It says nothing about PR-CSI-021, which was never read, or
about any arm's correctness — **a deterministic replay of a wrong arm is still wrong.**

---

## Editor's checklist — the phrasings this draft must never acquire

| forbidden | why | source |
|---|---|---|
| "p = 0.000092" for D39 | the claim is the weakest of three | D39 |
| the binomial alone for D40 | a random screen matches at ≈0.1625, not 1/9 | D40 |
| "0.012346" from PR-CSI-016 | that family returned CANNOT ANSWER | D38 |
| "cell (L,h) is the writer" | no arbitrary-cell control exists | D37/D39/D40 |
| D40 described as cross-codeword | it is held out on split only | D40 |
| any margin-restricted subset | post-hoc subsetting the prereg forbids | D39/D40 |
| "head 23's mechanism is refuted" | null on button is CANNOT ANSWER | D38 |
| "the concept is undecodable" | nothing was measured held out | D41 |
| any rung-2/3/4 **CLAIM** for a result here | every certified claim is rung 1 — but naming rung 2 as *unreached* is required, not forbidden, so the ban is on the claim and not the vocabulary | AM-34 |
| "correcting" either 1.52e-04 | `(1/9)^4 = (1/3)^8 = 1/6561` — two real quantities, one value | [†] §4 |
| ‼ "floor above α ⇒ CANNOT ANSWER, never FAIL" | true only at K < 3; at K ≥ 3 it is a FAIL with an unwinnability warning — and the sentence is **still live in both published artefacts**, so it can be re-imported from a source an editor will read | AM-45 (S-428), §M.6 |
| ‼ "these are the sprint's results" / "the sprint's negatives are §4's" | §1–§4 are the CELL-level part and §H the HEAD-level part; of the axis / necessity / dissociation families (D12–D31) **ten of D12–D31 are drafted as §A and TEN remain in neither** — see SCOPE | D12–D31, SCOPE |
| ‼ quoting `VERDICT: "WE FOUND (part of) THE WRITER"` | it is a **verdict LABEL live in TWO published artefacts** (PR-010 and PR-011), not a claim; the permitted form is that file's `REPORTABLE_AS` — 8 head indices, at least half the effect, **leg (i) only**, **not** a claim about any cell | D32, §M.8 |
| "deduplicating" the two 0.012346s | D39's certified conditional (§2) and D38's forbidden binomial (§4) are **both exactly 1/81** — one is a result, one is banned | D39, D38, §4 |
| ‼ "TEST is unspent / untouched / available" | read to completion 2026-09-08 and selection-contaminated | AM-39, D5 |
| "the screen is a validated cell selector in general" | forbidden for **both** D39 and D40, not just D39 | D39, D40 |
| "the basket result is weakened" (by D38) | D38 is CANNOT ANSWER; D37 stands | D38 |
| "the mechanism is these four cells" | overstates by ~1.7× — the peaks are 58.8 % of `CL_KO` | D37 (c) |
| "the effect is single-layer" | forbidden; §1's depth framing is where this returns | D36 |
| a 4-of-5 or 2-of-3 rate from D40's heads | no p attaches to either subset and none was computed | D40-c |
| "head 23 does not transfer", unqualified | true of amplitude, false of shape (ρ = +0.817) | AM-41 |
| "D37 is superseded by D40" / "D38 is explained by D39" | both ⛔; the §2→§3→§4 order invites both | D39, D40 |
| "a NULL source control is support" | a null control is CONFOUNDED — report as CANNOT ANSWER | AM-43 |

**‼ marks a phrasing this draft itself committed and had corrected.** The **TEST** row is here
because §0 asserted exactly it in the first version (S-417); the **floor** row because §M copied it
out of the published artefact, where it is still live (S-428). Two different routes to one failure —
one written from memory, one inherited from a source — which is the whole argument for keeping this
checklist attached to the prose rather than in a reviewer's head.

---

# M. Methods

**Added S-419.** Every definition below is quoted or derived from the frozen prereg
`configs/dcs_csi_pr020_cell_census_basket_8heads.json`, the frozen read `runargs/dcs_csi_pr020_read.txt`,
or an arm's own `RUNMETA.json` — **except §M.8, derived from `configs/dcs_csi_pr010/011/012/013_*.json`** — **not from memory and not from an earlier log entry**. Where the
prereg discloses a weakness in its own machinery, that disclosure is reproduced here rather than
left in the config.

## M.1 Model and hardware

Llama-3.1-8B-Instruct (snapshot `0e9e39f2…`), **bfloat16**, `attn_impl = eager`, torch 2.7.1+cu126,
transformers 5.12.1, on a single **NVIDIA GeForce RTX 3090** (compute capability 8.6). Generation
seed 20260913. **Eager attention is load-bearing, not incidental**: it is VOID condition 10, and a
fused kernel would change the arithmetic the cell-level intervention depends on.

## M.2 Population and unit

Prompt bank `boombness_prompt_bank_ts116m_{basket,button}_bomb.jsonl`, `n_examples = 4`. The split
manifest `dcs_ts116_domain_split.json` assigns **70 train / 23 validation / 23 test**; families
score **67** train domains (the three whole-population exclusions are train-assigned) and **23**
validation domains. **The domain is the statistical unit — rows never inflate n**, so a 230-row
validation read is n = 23, not n = 230.

## M.3 Intervention and arms

`demo_all:attn_knockout:6-14:1.0` with scope `target_surface_row_only`: attention from the
demonstration block is zeroed within band layers 6–14 at the target surface row. Four arm kinds:

| arm | what it is |
|---|---|
| `*_BASE` | no intervention — the clean reference every delta is taken against |
| `*_KO` | the all-32-head band knockout — the denominator |
| `HD_<h>` | all nine band cells of head h — **the bar source AND the admission arm** |
| `*_H<h>_L<ll>` | one cell — the judged unit |

**The mask is live during PREFILL ONLY.** GATE 0's pass predicate requires **zero decode edits** on
every arm, so the generated answer is scored under an uncontaminated decode. This is the difference
between measuring installation and measuring generation, and it is checked rather than assumed.
⚠ **`knockout_scope` itself is read off the config and is verified by NO CSI reader** — it is in the
same class as the prose VOID conditions, and this draft's standard is to say which facts are checked
and which are read off a config.

The per-cell dose is an **identity**, not a measurement: `2016 / 9 = 224` edits per cell (verified
from GATE 0's own sweep — one-cell arms at 224.0, `HD_<h>` and `*_KO` at 2016.0), so a deviation is
a **code defect and a VOID condition**, not a surprising fact about the model.

⚠ **The dose is NOT identity-diagnostic, and GATE 0 says so itself:** 72 of the 82 arms expect 224
and 9 expect 2016, so the dose confirms an arm is a one-cell arm but **cannot say which cell**.
That is precisely why arm identity is verified from each arm's own `knockout_cells` field and never
from its tag or its dose.

## M.4 Estimator

**The endpoint.** For each row the reader takes the two-way softmax between the concept and the
codeword log-probabilities, `y = exp(logp_concept) / (exp(logp_concept) + exp(logp_codeword))`
(max-subtracted for stability), on rows filtered to **`query_kind == "semantic_one_word"` and
`cell == "C"`**. 🔴 **That filter is load-bearing, not cosmetic:** the mandate forbids defining the
target from the forced-choice channel, which supplies the option set and therefore names the
answer. A duplicate key is a **refusal** rather than an overwrite, precisely because weakening the
filter would substitute the forbidden channel silently. Rows are averaged **within domain first**,
so the domain is the unit before any statistic is taken.

📌 **The endpoint is exactly `sigmoid(semantic_logodds)`** — verified across all 670 rows of an arm
at max |difference| **1.1e-16**, i.e. to floating point. The consequence is **asymmetric and worth
stating**: because the transform is **monotone**, every **rank-based** result in this sprint is
**invariant** to which scale one names — no rank can change. **Effect sizes are not.** `E = −0.2269`
is a change of **22.7 percentage points of probability**, and reading it as a change in log-odds
would overstate it. ⚠ Where a source describes this endpoint loosely as *"a concept-vs-codeword
log-odds"*, that is right about the contrast and wrong about the scale.

Per arm, **E = the mean over DOMAINS of the per-domain paired delta** (arm minus its base arm,
which is the CLEAN `*_BASE` reference and never the KO arm).
Confidence intervals are **percentile bootstrap, resampling domains, B = 10000, seed 20260922,
ci 0.95**.

⚠ **Disclosed by the prereg about itself:** those three bootstrap values *"were COMMAND-LINE
DEFAULTS of `scripts/dcs_csi_head_census.py`, not preregistered quantities"*. Every published census
used them, so they were frozen retroactively as a sprint-wide constant. **They are a convention that
became a commitment, not a commitment from the start**, and the draft states this rather than
letting the prereg's presence imply otherwise.

## M.5 The detectability bar, and admission

The bar is **a rule, not a number** — it must come from the family it judges:

> `bar(h) = 1.96 × SD(per-domain paired delta of HD_<h> minus the base arm, ddof = 1) / √n_domains`

`ddof = 1` is pinned: S-318 verified it reproduces the published bars exactly. ⚠ **The rule's two
prereg-supplied constants are not treated alike:** `z` **must** be declared, and is bounds-checked —
a missing `z` once defaulted to 1.96 and was published as though the prereg had frozen it, and
`z = 0.0` was once accepted, giving a bar of 0.0 and "11 of 27 cells CLEAR THE BAR". The admission
`ratio` is read from the prereg with **no validation of any kind**. **Head h is ADMITTED
iff `HD_<h>`'s ci95 excludes 0 AND `|E(HD_<h>)| ≥ 1.5 × bar(h)`**, computed from the whole-head arm
**alone and never from the cells** — the cells are what admission is a precondition for judging.
A dropped head **leaves K and is reported with its measured power; it is not counted as a miss.**

⚠ **Admission carries a 1e-12 tolerance** (`|E|/bar ≥ ratio − 1e-12`) because the comparison is not
exact in IEEE doubles — `abs(-0.009)/0.006` evaluates to `1.4999999999999998`. **A head sitting
exactly at 1.5 is admitted**; the code's own note is that without the tolerance roughly **one
boundary pair in twelve** would evaluate below the bar and be dropped.

🔴 **The same bar has a SECOND use, and it is the one §1 reports.** Admission applies it to the
whole-head arm at ratio **1.5**. The *depth map* applies it **per cell at ratio 1.0 with a strict
inequality** — `|E(cell)| > bar(h)` — and that is what "clears its own preregistered detectability
bar" means in §1, where the three clearing cells sit at 2.58× / 4.30× / 2.80× of it. The census
also prints the weaker "ci95 excludes 0" count beside the bar count, because the two disagreed on
PR-CSI-014.

⚠ The ratio **1.5 is frozen across three published families** (PR-CSI-016/018/020). It cannot be
lowered after the fact without reinterpreting all three — which matters because the best unadmitted
basket head sits at **1.400** (D41).

## M.6 The primary statistic and its three p-values

**M = the number of ADMITTED heads, WITH NO TIE for that head's argmax, whose argmax band layer by
|E| equals that head's frozen screen-predicted layer.** The reader keeps the observation
(`ARGMAX_EQUALS_SCREEN`) separate from the scoring decision (`COUNTED_IN_M`), which is a
three-way conjunction: admitted **and** untied **and** matching. Under the null the screen's per-cell prediction is unrelated to the depth
profile. Three p-values, all preregistered:

- **binomial** — `P(Binom(K, p₀) ≥ M)` where **p₀ = 1/|band| is derived from the band size**, not
  hardcoded; with the nine-layer band 6–14 that is 1/9
- **conditional** — the same over the admitted heads whose predicted layer is **unique** in the set
- **permutation** — the fraction of distinct assignments of the prediction **multiset** to the
  admitted heads achieving at least M agreements, **scored against the OBSERVED ARGMAX VECTOR**

🔴 **A TIE for the argmax on any admitted head is a preregistered CANNOT ANSWER** — M, p and the
span are emitted as `None` and never computed, because a tied head is *undetermined*, not a miss.
⚠ **M = 0 is NOT that case:** it yields the ordinary gating p of 1.0 and the preregistered **FAIL**.
Verified by executing the verdict function on constructed inputs: M=0 at K=8 returns
`FAIL, M=0, p=0.99999…`; a single tie returns `CANNOT ANSWER, M=None, p=None`.

⚠ **That last clause is not cosmetic.** PR-CSI-020's first freeze compared against the *prediction*
vector, which is a different statistic; S-352 caught it and the family was re-frozen. The two agree
on a perfect result and diverge elsewhere.

**Gating is `weakest_of_three` for PR-CSI-018 and PR-CSI-020: the family PASSES iff the weakest of
the three ≤ α = 0.05 AND the spanning rule is satisfied.** The reader reads the rule from the
prereg's `PRIMARY.GATING` and **fails closed** — a prereg that declares no gating is refused.

🔴 **PR-CSI-016 is the exception and §4 depends on it: its frozen prereg declares NO `GATING`
field**, and it is the one family grandfathered to the legacy `binomial_only` rule. Verified by
reading all three configs. So "the weakest of three gates" is **not** a sprint-wide fact, and the
three families are not interchangeable in this respect.

⚠ **At `K_unique = 0` the conditional is not a p-value.** The reader sets `p_cond = 1.0` as a
**placeholder for a statistic that does not exist**, and under `weakest_of_three` the `max()` would
promote that placeholder to the gate and publish a structural FAIL. R30-B found this on synthetic
censuses. ⚠ **It is NOT what happened to PR-CSI-016**: that family gates on the binomial alone, so
the placeholder never reached its gate. Its verdict artefact gives the cause in its own `why`
field — *"the SPANNING RULE is violated: all 2 matching head(s) share band layer L14"* — and
`spanning_rule_satisfied` is `false`. The placeholder is a hazard for `weakest_of_three` families;
the spanning rule is what returned PR-CSI-016's CANNOT ANSWER. **Two different mechanisms, and
conflating them would misattribute the one real CANNOT ANSWER this sprint has.** The **spanning rule** is that the matching heads must not all share
one band layer, because a shared top-of-band bias and a correct screen are indistinguishable there.
⚠ **It is a PASS-VETO, not an override:** the spanning test is evaluated *after* the p-gate, so it
converts a would-be PASS into CANNOT ANSWER however small the p-values are, and **it cannot rescue a
FAIL** — when the gating p exceeds α the verdict is already FAIL (at K ≥ 3) and the rule is never
reached, with `spanning_rule_satisfied` published as *"NOT_APPLICABLE — the rule was never reached"*. This is not
hypothetical: it is what happened to PR-CSI-016 (§4). **The claim must be stated with the weakest of
the three, each named; quoting the binomial alone is forbidden.**

**The FAIL / CANNOT-ANSWER boundary is preregistered, and §4 rests on it.** The reader computes
each statistic's **floor** — the p it would report on a *perfect* result at the realised K and
admitted multiset. 🔴 **The floor NEVER changes the verdict.** At **K ≥ 3** a gating p above α is a
**FAIL whatever the floor**, and where the floor also exceeds α the verdict carries an explicit
unwinnability warning beside it, so the FAIL is not cited as evidence against the screen. Structural
**CANNOT ANSWER** is reached only at **K < 3**, where the prereg defines no adverse verdict at all.
⚠ **The opposite rule — floor above α ⇒ CANNOT ANSWER — was tried and REJECTED in the code**, whose
own comment records why: *"Deciding after the fact that a preregistered FAILURE is really a
non-answer, because its floor is unflattering, is the post-hoc move this sprint exists to forbid."*
Verified by execution at K=4, M=0, floor 1.0: the verdict is **FAIL**.

## M.7 Gates and VOID conditions

**GATE 0** checks liveness and arm identity. **Liveness is a four-way conjunction**: no recorded
violations, **zero decode edits**, the median prefill-edit count equal to the arm's expected dose,
and the identity check. Identity comes from each arm's **own recorded intervention flags, not its
tag** — `knockout_cells` for the 80 cell-scoped arms; for the all-32 `*_KO` arm the conjunction
`knockout_heads == ALL` **and no cell list at all**, because a full-band nine-cell arm records an
empty `knockout_heads` and the *identical* dose 2016. ⚠ **The sweep asserts the clean base arm's identity unconditionally** (`"not intervened"`), so
**1 of the 82** arms is not identity-checked from its own flags by GATE 0. *(The gate's source calls
`*_BASE` and `*_KO` "the two BASE arms", which invites "two unchecked"; the `*_KO` arm **is**
checked, by the `ALL`-plus-no-cell-list conjunction just described.)* The census reader reads the
base arm's flags separately. Exit 0 = all arms pass; 1 = failure;
**3 = ran but is not the verdict** (a partial sweep), a distinction that exists because a pipe once
made `tail`'s exit status look like the gate's.

**VOID 8 is enforced by the reader**: each `HD_<h>` must reproduce the corresponding whole-head
effect from PR-CSI-012 within **1e-6**, across a different job and family. ⚠ **It pins the MEAN only** — `bar(h)` and `ci95` are unpinned, while admission is a conjunction
over all three. ⚠ **The 1e-6 tolerance is supplied by the PREREG, not the reader** (which refuses a
missing one, and requires it in (0, 1e-3]), and **only heads that declare a reference are
evaluated** — any others are named as NOT EVALUATED rather than silently passed. All eight
PR-CSI-020 heads declared one.

🔴 **The other VOID conditions are unenforced BY ANY READER**, and the frozen read says so rather
than letting them read as automatic. ⚠ **One is enforced upstream, and §M said otherwise until
S-421 checked the source:** **VOID 10 is enforced by the scoring script at run time** —
`score_behavior.py` forces eager on every knockout arm and `assert_eager_for_knockout` refuses a
non-eager backend *and refuses an absent one* ("a check that reads its own absence as a pass" is
the failure it was rewritten to avoid), so a non-eager arm could not have been written. **VOID 5, 9,
11 and 12 are prose and nothing checks them.**

| | condition |
|---|---|
| VOID 5 | the screen artefact's md5 is unchanged (`81fc4dca…`) |
| VOID 9 | every arm on one SLURM job and one GPU architecture |
| VOID 10 | `attn_implementation == eager` on every arm — ⚠ **the key actually recorded in each arm is `attn_impl`**; an operator grepping the prereg's spelling finds nothing |
| VOID 11 | `scripts/` and `src/` unchanged while the arms are in flight |
| VOID 12 | the read file is not amended after any number from the family is seen |

⚠ **VOID 11 did not exist for PR-CSI-018** — it was introduced for PR-CSI-020. §6 records what that
cost and what the decisive test found. ⚠ **The commit of record is the launcher's
`BLOB <sha> PORCELAIN clean` line, NOT any arm's `RUNMETA git_commit`**: a job runs many arms, each
stamps the repo at its own start, and `git_dirty` is recorded as `true` or as `None` but **never as
`false`** across this sprint's runs — so the direction that would falsify a clean-tree claim is
recorded while the direction that would confirm it is not.

## M.8 The HEAD-level machinery (§H)

§M.1–§M.7 describe the cell-level families. §H uses a different CONTROL vocabulary and a different
decision rule, neither defined above. ⚠ Two names for one intervention: **`SINGLE_hh` is §M.3's
`HD_<h>` under PR-CSI-012's naming** — the same nine band cells of one head.

| arm | what it is, from `configs/dcs_csi_pr010_head_causal_basket.json` and `..._pr012_...` |
|---|---|
| `HD_BASE` | no intervention — the clean reference every head-level delta is taken against |
| `HD_KO` | `--knockout-heads` omitted = **all 32** band heads; the positive control **and the ceiling** |
| `HD_TOPK` | the candidate 8-head set, `[19, 17, 23, 6, 13, 2, 24, 28]` |
| `HD_BOTK` | the matched opposite end, `[29, 11, 30, 10, 15, 16, 0, 9]` — declared the **COMPARATOR and explicitly NOT part of the control family** |
| `HD_RAND00..19` | the 20 dose-matched control sets. ⚠ **Drawn from `control_pool`, the candidate's 24-head COMPLEMENT** — the restriction H.1 carries and H.1b lifts |
| `SINGLE_hh` | one head, for every `h` in 0..31 — the census H.2 reads |
| `LOO_hh` | `HD_TOPK` minus head `h` — the leave-one-out marginals |
| `HD_ALL32_00..19` | the 20 controls of **PR-CSI-011** (`seed_base` 20261001), drawn from **ALL 32** band heads — the family §H.1b reads, and the one that lifts the complement restriction |
| `BT_*` | BUTTON: `BT_SINGLE` = head 2 alone, `BT_KO` = all 32. ⚠ **`BT_CTRL_*` are 20 SINGLE heads** drawn from the 31 other than head 2 — singleton controls for a singleton candidate, **not** `HD_RAND`'s 8-head sets |

⛔ **PR-CSI-012 (the census — `SINGLE_hh`, `LOO_hh`) is EXEMPT FROM THE RANK TEST BY DESIGN**, and
its prereg says so in a field of its own: *"There is NO candidate, NO control family, NO rank and NO
p-value in this preregistration"* — a rank among the 8 `HD_TOPK` singletons would carry a floor of
**1/8 = 0.125** and could never clear α, so `control_prefix` and `n_controls` are **absent on purpose**
so the rank tooling refuses the file. The rule below governs PR-CSI-010, 011 and 013 only.

**The rank test.** The candidate is ranked among its controls by effect, most negative first, with an
**attainable floor of `1/(n_controls + 1)`**. At 20 controls that is `1/21 = 0.047619`. ⚠ **The
prereg states the consequence in advance and it is severe: this clears α = 0.05 ONLY at rank 1 —
rank 2 gives `2/21 = 0.0952` and cannot clear at any data.** A head-level family of this size has
exactly one passing outcome.

⚠ **A rank of 1 is NECESSARY AND NOT SUFFICIENT.** The prereg's verdict ladder requires rank 1 of
21 **AND `F ≥ 0.50` with a ci95 excluding 0**, behind two gates: GATE 0 (liveness, per arm) and
**GATE 1** — `E(HD_KO) < 0` with its ci95 upper bound below 0 — whose failure is *"CANNOT ANSWER;
report feasibility and STOP; do NOT report the candidate"*.

⛔ **Every TRAIN rank must be printed with the words the prereg mandates: *"selection-contaminated,
not an inferential statement"*** — the heads were chosen on TRAIN activations, so a TRAIN rank of 1
is partly a restatement of the selection. **VALIDATION adjudicates with ONE preregistered test**, so
no multiplicity correction is applied or needed, and `HD_BOTK` does **not** enter the control
distribution.

🔴 **AND THE ARTEFACTS' OWN `VERDICT` STRING MUST NEVER BE QUOTED.** **BOTH**
`DCS_CSI_PR010_HEAD_validation.json` **and** `DCS_CSI_PR011_ALL32_validation.json` record the
identical `VERDICT: "WE FOUND (part of) THE WRITER"` (a sweep in S-444 found the second; S-443 had
seen only the first) — the prereg's branch is named
`WE_FOUND_THE_WRITER` and its conditions were met, and the reader hedged it at write time. **The
sprint forbids "the writer" language throughout**, and the same file's `REPORTABLE_AS` gives the
form that is permitted: *"8 head INDICES … carry at least half of the A1 knockout's effect on
installation for basket — for leg (i) of the circuit ONLY. NOT a claim about any single (layer,
head) cell."* ⚠ **A verdict LABEL is not a claim**, and this label is live in a published artefact —
the same hazard class as the floor sentence in §M.6.

⚠ **`|E(HD_BOTK)|` doubles as the NULL ANCHOR in §H.2** — a third use of a threshold, beyond the two
§M.5 enumerates. It is the family's own opposite-end set, not an external bar.

## M.9 The AXIS-level machinery (§A)

§A uses a third vocabulary, defined in neither §M.3 nor §M.8. From
`configs/dcs_csi_pr001_subspace_rescue.json` (the sufficiency arms) and `..._pr003_necessity_basket.json`
(the necessity arms). ⚠ **The 46-control composition and the subfamily floors are NOT in either** — they
are `..._pr005_button_L18_family.json` / `..._pr007_button_L18_validation.json`; and **pr003 declares its
own floor as 0.10**, which `..._pr003a_necessity_family.json` corrects to 0.1111 at 8 controls:

| arm | what it is |
|---|---|
| `BASE` / `KO` | no knockout / the A1 knockout with no rescue |
| `KO_SELF` | knockout + whole-state rescue with **donor = self** — the intervention-mechanics identity control, which **MUST be inert** |
| `KO_FULL` | knockout + whole-state **clean** rescue — the POSITIVE CONTROL and the upper bound |
| `KO_AXIS` | knockout + the rank-1 installation axis (`cand_rank1`) — **the candidate** |
| `KO_ORTH` | `ctrl_orth`, norm-matched to the candidate — the prereg's words are **"THE PRIMARY COMPARATOR"**, ⚠ **but it is NOT the comparator §A's ranks use**: it enters as `--comparator-arm` only, is excluded from the 46-control family by `--control-prefixes KO_SHUF,KO_RAND`, and its single-comparator verdict is **SUPPRESSED** in both published artefacts (`single_comparator_verdict_SUPPRESSED`), because a verdict decided by which control the caller names is not a verdict |
| `KO_PLS` | knockout + the rank-r\* PLS subspace, r\* selected on TRAIN — **not the candidate of any §A read**, but it is the arm on which *"the representation is one-dimensional"* would turn |
| `KO_SHUF*` / `KO_RAND*` | shuffled-label and random directions, norm-matched — the control family, grown to **24 shuffled + 22 random = 46** |
| `NEC_*` / `KO_NEC_*` | the same shapes **except one**, for the NECESSITY direction: `NEC_BASE` clean, `NEC_KO`, `KO_NEC_AXIS` the candidate, `KO_NEC_FULL` the positive control, `KO_NEC_ORTH` the comparator, `KO_NEC_SHUF0-3` / `KO_NEC_RAND0-3` the 8 controls. ⛔ **There is NO `KO_SELF` analogue**: for removal the natural identity control IS the identity and is refused by the arm's own precondition, so the identity gate is **SKIPPED BY DESIGN** and the artefact records the skip and its reason — *"a real limitation of the direction, not an oversight"*. ⚠ The `NEC_` prefix is **load-bearing**: a second complete directory under one tag is the tag ambiguity an earlier entry had to untangle |

**Three gates precede any rank**, all published and all true on every read in §A: `manipulation_check`,
`identity_check` (SKIPPED for necessity, above) and `instrument_capable`. ⛔ **`instrument_capable` is
the axis-side GATE 1**: if the whole-state rescue does not itself recover installation, the question is
**CANNOT ANSWER for want of a capable instrument, NOT a negative**.

🔴 **AND THE FLOOR IS NOT THE RULE — the implementation is STRICTER than the preregs.** The
analyser's PASS branch is `rank == 1 AND round(1/(K+1), 4) < 0.05`, so **rank 2 of 47 takes the FAIL
branch** even though `2/47 = 0.042553` is below α — while PR-CSI-005, 006 and 007 all declare that
**rank 1 or 2 certifies**. **The divergence is live in a published artefact** (AM-48): the
basket-validation swap cell sits at rank 2 of 47 and its `VERDICT` string says *"DOES NOT PASS …
INSIDE the controls, not above them"* of a candidate above 45 of 46 controls. ⚠ **No published claim
rests on that string** — the claim table read that cell by the prereg's rule — but nothing was
checking. Also: the floor test is **strict on a 4-dp rounded value**, so K = 19 (floor exactly 0.0500)
does not certify and **K ≥ 20 is the minimum**; and **ties count against the candidate**, which is what
"strictly the largest" means.

⚠ **Intervals in §A are domain-clustered percentile bootstrap at B = 20000, seed 20260915** — **not**
§M.4's B = 10000 / seed 20260922, which are the cell-census constants and produced no number in §A.

**The rank test is the same shape as §M.8's, with different arithmetic.** Direction is
orientation-dependent: **more POSITIVE is stronger for sufficiency, more NEGATIVE for necessity**.
At 46 controls the attainable floor is `1/47 = 0.0213`; ⛔ the subfamilies are **SECONDARY and may not be substituted for the 46-control primary**, and for
the NECESSITY direction PR-CSI-003-A **inverts** this — there the shuffled-only rank is the primary and
the random-only rank is descriptive only and *"must never be quoted as a p-value"*. They carry their own floors,
**shuffled-only `1/25 = 0.0400`** and **random-only `1/23 = 0.0435`**. ⚠ **The necessity family has
only 8 controls — not the 9 pr003's own prose and its `attainable_p_floor: 0.10` imply, because
`--control-prefixes KO_NEC_SHUF,KO_NEC_RAND` matches neither `KO_NEC_ORTH` nor `KO_NEC_AXIS_ANCHOR`
— so its floor is `1/9 = 0.1111`, above α** — which is why §A.1's necessity half
cannot certify at any data and §L.3 records the extension that would have fixed it.

## M.10 What the design cannot do

The screen is fitted on **basket TRAIN**. For the cross-codeword family (§2) the prediction is held
out on **codeword**; for the within-codeword replication (§3) it is held out on **split only**.
**There is no control family of arbitrary cells** in any family, because no admissible held-out
axis exists — and restricting controls to one head's nine cells returns the 1/9 floor, which is
above α for every attainable effect size.

---

## M.11 Bootstrap confidence bounds are quoted to five decimals and are stable to four

Every CI in §A comes from `dcs_csi_rederive_patch.boot_paired_diff`, a percentile bootstrap over
domains. It is seeded, so a re-run at the same `(domains, arms, B, seed)` reproduces — but a bound
recomputed at a **different** draw count, or by an independent implementation with its own seed,
moves in the **fifth decimal**. Two instances, both measured while checking this draft:

* 🔴 **WITHDRAWN S-455.** This section first cited D12's held-out upper bound as `+0.00775` in the
  artefact against `+0.00774` on re-run. **It reproduces EXACTLY** — `[+0.00098, +0.00775]`, p and
  verdict identical — when the analyser is re-run end to end rather than when `boot_paired_diff` is
  called directly on the stored `domain_means`. The discrepancy was in the re-derivation path, not
  in the bootstrap, and citing it here overstated the instability.
* §A.4's paired difference has lower bound `+0.00064` at B = 20000 and at B = 400000, `+0.00065` at
  B = 100000, against the claim table's independently computed `+0.000664`. **This one stands** —
  the artefact does not publish that contrast, so there is no pipeline value to defer to.

⛔ **A fifth-decimal disagreement between two CIs for the same quantity is therefore not evidence
that either is wrong**, and no argument in this draft turns on one. ⚠ **But the first place to look
is the re-derivation path, not the seed**: on the one case where a stored value existed to check
against, the pipeline reproduced it exactly and the shortcut did not. Where a stored artefact value
exists it is quoted; where none does — §A.4's paired contrast is not published by its artefact — the
re-derived value is quoted and named as re-derived.

⚠ **This does not extend to p-values or point estimates.** Both reproduced *exactly* wherever they
were checked in §A. A p-value disagreement here means a **different test**, not a different seed —
which is precisely what §A.4b found.

# L. Limitations

**Added S-423.** §5 states what the evidence *is*; this states what it **cannot become** without new
data. Each item is a measured constraint, not a hedge, and names the measurement that fixes it.

## L.1 Everything here is one rung

Every certified claim is **RUNG 1 — NECESSITY**: ablation damage. Nothing reaches decodability,
repair or transfer, and the ladder's own result is that the four are **separable**. §4 records the
attempt on rung 2 and why it stopped. A reader who wants "this cell writes the codeword" is asking
for a claim **§L.2 shows is unavailable for a separate, structural reason on top of the rung
limit** — the claim table gives the control-design reason, not a rung reason, and more rungs would
not supply it.

## L.2 There is no arbitrary-cell control, and the reason is structural

No family in this sprint contrasts a nominated cell against **arbitrary** cells, so *"cell (L,h) is
the writer"* is unavailable throughout. This is not an omission that more compute fixes: no
admissible held-out axis exists, and restricting controls to one head's own nine cells returns the
**1/9 = 0.111 floor**, which is above α at every attainable effect size.

## L.3 🔴 Two results are floor-limited, and BOTH extensions died the same death

Both are **top of their control family** and both families are **too small to certify that**:

| result | outcome | floor | certifiable at α = 0.05? | the extension that would have fixed it |
|---|---|---|---|---|
| necessity, basket | rank **1 of 9** | 0.1111 | **no** — needs ≥ 20 controls | PR-CSI-003-A — built, patched, **never launched** |
| sufficiency, basket at **L20** | rank **1 of 11** | 0.0909 | **no** | PR-CSI-004 — frozen, **never run, unrunnable as frozen** |

🔴 **The two failures have ONE cause, not two.** Each extension was designed to **reuse
already-run arms** and therefore had to pin the code blob so old and new arms would match.
PR-CSI-004 requires its 36 new arms to run the blob its 10 reused controls ran; PR-CSI-003-A's **own VOID 6 — a different family's numbering: the code-blob condition, NOT
PR-CSI-020's tie condition in §M.6** — requires its 20 new arms to run the blob its two already-run
halves ran. **In both cases
`src/boombness/score_behavior.py` moved before the new arms were launched, and the reuse that made
each design cheap is exactly what killed it.** That is the transferable lesson: **a family that
reuses archived arms and pins the blob has a shelf life, and nothing warns you when it expires.**

⚠ **Their statuses differ and the draft should not blur them.** PR-CSI-004 is **dead as frozen** —
its requirement can no longer be met. PR-CSI-003-A is **not dead: it is escalated and waiting.**
Its launcher patch is applied and verified; the launch was withheld deliberately, because amending
a VOID condition *after it fires* to let one's own experiment proceed is the shape of an earlier
blocker. **8.7 GPU-hours were not spent on twenty arms that would have been VOID by a condition the
author wrote** — a decision that is still open, not a dead end.

🔴 **FAMILY SIZE IS NOT THE ONLY THING BETWEEN EITHER RESULT AND A CERTIFIED ONE.** Both are
**TRAIN-only and IN-SAMPLE** — `evaluation_is_in_sample: true` with `scored_domains_also_in_fit: 67`
on **every arm of both reads**, verified at the artefacts. Neither has a held-out read, and the
fresh freeze below **would not supply one**: it fixes the floor, not the in-sampleness.

⚠ **PR-CSI-003-A is blocked by TWO stranded conditions, not one:** its own VOID 6 (the score blob)
and **VOID 7** (`dcs_csi_rederive_subspace.py` moved, +36 lines). A launch would also intersect 20
new arms against a key set **already reduced to 664 by three short control arms**, and today's
re-derivation path refuses the family outright.

⚠ **And "floor-limited" is a statement about these families, NOT about the cells.** Neither result
is permanently uncertifiable: a fresh freeze that re-runs every arm on one current blob **and
carries the full extension** — **33 arms for necessity** (the 13 existing plus 20) and **53 for
L20** — would carry a floor below α in both cases. ⚠ Re-running the existing arms alone changes
nothing: necessity would still have 8 controls and a floor of 0.1111. What is permanent is that
**these two preregs cannot deliver it**, and reusing archived arms to avoid the cost is what
produced this situation.

🔴 **And the necessity result's EFFECT is small against the thing it is a fraction of.** Removing the
rank-1 component from a clean forward moves the endpoint **−0.00852**, against **−0.10950** for
removing the whole state: `removal_fraction_candidate_of_full` = **0.0778 [0.0560, 0.1009]**. **The
axis accounts for 7.8 % of what whole-state removal moves — about 92 % of the effect is elsewhere**,
and that figure must travel with any statement of the necessity direction.

⚠ **And none of the necessity sign-flip p's carries information.** All of them — 15 of the 23
contrasts, including the candidate's — report **p = 4.9999750001249995e-06**, which is *exactly*
the Monte-Carlo sampler's floor of **1/200001**. The artefact says so in its own
`p_floor_basis`: *"monte-carlo sampler (200000 draws); the exact floor 1.36e-20 is unreachable by
the test that ran"* — the exact sign-flip floor over 2⁶⁷ assignments is 2/2⁶⁷ = 1.355e-20.
**These p's record that the sampler saturated, not how strong the effect is**, and may not be quoted
as evidence of magnitude.

⚠ **Neither is a negative result.** Each is the *best attainable* outcome in a family whose floor
sits above α — the same FAIL-versus-structural-CANNOT-ANSWER distinction §4 draws, arriving here
through **family size** rather than through K.

## L.4 Every head was chosen because it was live

No family draws its **CANDIDATE** heads at random — the *control* sets are random by design (§M.8). PR-CSI-018's six were chosen because they were live **on button**;
PR-CSI-020's eight because they were live **on basket**. The screen's per-cell prediction is
therefore tested **only where there was something to find**, and nothing here licenses *"the screen
is a validated cell selector in general"*. 🔴 **And the worst selection case is §1's, not these two.** D37's four heads were chosen as D34's
load-bearing four **ON VALIDATION — the same split the census then reads**. That is selection on the
split being reported, which is strictly worse than choosing heads because they were live on the
*other* codeword.

⚠ **The screen is validated for WITHIN-head depth only, and has a MEASURED failure at ranking
heads.** The same screen that localises head 2's effect to the right layer ranked head 2 — **the
single strongest head of 32** — only **6th of 32** at head level. So "the screen works" is true of
*which cell within a head* and false of *which head matters*.

⚠ And the **1.5 admission gate is frozen across three
published families**, so it cannot be relaxed after the fact — which matters because the best
unadmitted basket head sits at **1.400**, close enough that a reader may wonder, and far enough that
moving the bar would reinterpret three published results at once.

## L.5 The two positive results differ in what is held out — and D40's nominal null is measured to be wrong

**§2 (D39) is held out on CODEWORD. §3 (D40) is held out on SPLIT only.** They are not two
independent confirmations of the same thing, and **three of D40's eight heads were disclosed before
the read as a replication** of predictions already tested in §2 — not an independent draw.

🔴 **And D40's nominal null is MEASURED to be wrong for its own multiset.** The intervention argmax
marginal is not uniform: across the cell censuses published at the time, **L10 and L14 together took
60 % of ten heads** while uniform would be 11.1 % each. **Three of PR-CSI-020's eight predictions
land on those two modal layers**, so a *random* screen predicting that multiset would match at
**0.1625, not 1/9 = 0.1111 — 46 % higher** (re-derived: 1.30/8). **The binomial is therefore
anti-conservative here**, which is the measured reason §3's binomial may never be quoted alone.
⚠ **0.1625 is NOT a corrected null and must never be substituted into anything** — constructing a
"corrected binomial" after seeing the marginal is exactly the post-hoc statistic-selection this
sprint forbids. ✅ **The permutation and conditional p's are immune**: both condition on the
multiset, so a marginal favouring L10/L14 helps every assignment equally and cancels. The claim
rests on the weakest of three, and the binomial is never the weakest.

## L.6 Two axes are closed by contamination, not by design

**TEST** is never touched here, and it is also **not available**: read to completion on 2026-09-08
and selection-contaminated on knobs every family inherits. **The SOURCE question** — whether the
demonstrations supply the installed content — has **no confirmatory instrument**: the mass
measurement licenses a **refutation reading only**, and a null control there is *confounded*, to be
reported as CANNOT ANSWER and never as support.

## L.7 Every result here reads the SAME 23 domains, and most heads were never looked at

🔴 **All five cell censuses — PR-CSI-014, 015, 016, 018 and 020 — read an IDENTICAL set of 23
validation domains, and so does the head-level button family in §H.3**, whose 23 domains are
recorded as identical to basket's. **The limitation is sprint-wide within §1–§4 and §H, not cell-level.** 🔴 *CORRECTED S-453 —
§A also reads the 67 TRAIN domains, which are disjoint from these 23; see §0.* Verified by comparing the domain sets arm-by-arm: union 23, intersection 23.
**So §1, §2, §3 and §4 are not independent in the domain dimension**, and that includes the
cross-codeword pair: D39 and D40 share their entire domain sample. Domain idiosyncrasy is common to
every result in this draft, and **nothing here speaks to domain generality.**

⚠ **Head coverage is thin and the two ways of counting it differ.** At most **8 of 32** heads are
cell-censused in any single family; the **union across all five families is 15 of 32**, so
**17 heads have never been cell-censused at all**. Every claim about "where the codeword is
installed" is a claim about the heads that were looked at.

## L.8 What reproducibility does and does not buy

§6 shows both published reads replay from their landed artefacts, including under a later reader
refactor. **That tests the reader, not the arm** — it re-reads the same arms, strengthens no p, and
a deterministic replay of a wrong arm is still wrong. ⚠ **And replay is NOT uniform.** The two published PASSes replay exactly; the **necessity
re-derivation does not reproduce under today's code at all** — the script now refuses an arm whose
`DONE.json` is not `ok`, and **three of the eight necessity controls are short** (669 / 666 / 669 of
670, handled by intersection at 664 keys). **The guards got stricter; the result did not get
weaker.** ⚠ Relatedly, the **bootstrap parameters were command-line defaults frozen retroactively**
(§M.4), so they are a convention that became a commitment rather than a commitment from the start.

---

# H. The head-level half

**Added S-436**, closing the omission the SCOPE block declares. **Every figure below was read by me
from the artefacts** — `DCS_CSI_PR010_HEAD_validation.json`, **`DCS_CSI_PR011_ALL32_validation.json`**,
`DCS_CSI_PR012_CENSUS_validation.json`, `DCS_CSI_PR013_BUTTON_HEAD_validation.json` and
`..._REDERIVE.json` — **not copied from the claim table**, which is the rule
§M was written under after a methods section inherited an artefact's error.

The cell-level half (§1–§4) subdivides heads that *this* half selected. It is written second and
belongs first.

## H.1 Eight heads carry most of the knockout (D32)

On basket VALIDATION, knocking out eight head indices across band layers 6–14 on the query-codeword
row reproduces most of the all-32 knockout:

```
HD_KO    (all 32 heads)   E = -0.22696123   ci95 [-0.27586414, -0.17868012]
HD_TOPK  (the eight)      E = -0.19598350   ci95 [-0.24306753, -0.15349093]
HD_BOTK  (the null anchor) E = -0.01256722  ci95 [-0.02020293, -0.00465766]
F = E(HD_TOPK) / E(HD_KO) = 0.86351092      ci95 [0.78710197, 0.94784347]
```

Against **20 random 8-head control sets**: mean −0.004006, sd 0.013205, range [−0.024571,
+0.019694], and **0 of 20 are more negative than the candidate**. `HD_TOPK` is **rank 1 of 21**.

⚠ **The p IS the floor.** Rank 1 of 21 gives `p = 0.047619`, which is *exactly* the attainable floor
`1/21` — the artefact reports the two together for this reason. **There is no margin: this family
could not have produced a smaller p at any data.**

⛔ **D32's controls are drawn K-of-(32−K) from the candidate's COMPLEMENT**, so *this family* makes
no statement about arbitrary 8-head subsets. **That gap is what H.1b closes — the prohibition
applies to D32 and NOT to D33.** ⛔ **`F` is a ratio of two net-of-compensation causal effects; the
direction of the bias is ARGUED to be downward and its size is UNMEASURED** — no compensation
magnitude has been measured for this cell. It is not "the fraction of the mechanism these heads
are", and it does **not** license *"the other 24 heads contribute 14 %"*. ⛔ **Leg (i) ONLY** — leg
(ii) (`rel-11 → rel-6`) has no scope and is untested, and blocks 0–5 and 15–18 are untouched. ⛔
RUNG 1, necessity. ⛔ D32's caveat that this says nothing about any single `(layer, head)` **cannot
be lifted** with the axes this sprint has.

## H.1b The same set beats controls drawn from ALL 32 heads (D33) — a SEPARATE experiment

D33 is **not** a restatement of D32: a different prereg, a different job, and a different control
pool. Its 20 controls are drawn from **all 32 band heads**, not from the candidate's complement:

```
controls: 20, mean -0.057700, ALL TWENTY NEGATIVE, strongest -0.15245762
candidate HD_TOPK -0.1959835 (bit-identical to D32's)   rank 1 of 21, p = 0.047619 = the floor
```

**This is the arbitrary-8-head-subset comparison D32 could not make**, and it is a harder test:
D32's controls average −0.004006, D33's −0.057700.

🔴 **And it carries the sharpest bound on the whole head-level story. Sufficiency is certified;
UNIQUENESS IS NOT.** The strongest control shares **exactly ONE head** with the candidate (head 2)
and still reaches **77.8 %** of the candidate's effect and **67.2 %** of the all-32 knockout's. The
dose-response in candidate-head *count* is weak and non-monotone (Spearman ρ = −0.0932), which
argues against additivity across the eight. **Nothing here says this is *the* 8-set.** ⚠ Two
rank-1-of-21 certifications, both sitting exactly at their floor — separate evidence, not one result
counted twice.

## H.2 Exactly four heads clear the family's own null anchor (D34)

Using `|E(HD_BOTK)| = 0.012567` as the anchor the family itself supplies, the 32 single-head arms on
basket validation give **exactly four** heads with a negative effect, a magnitude above the anchor
and a ci95 excluding zero:

```
head  2   -0.04947467   ci95 [-0.06973814, -0.03265628]
head 19   -0.04010869   ci95 [-0.05037628, -0.03052043]
head 17   -0.02921839   ci95 [-0.03880694, -0.02090066]
head 23   -0.01650303   ci95 [-0.02320141, -0.01006879]
```

**All four are inside `HD_TOPK` = [19, 17, 23, 6, 13, 2, 24, 28], and no head outside it clears** —
verified by me over all 32. These four are where §1's heads come from.

⛔ **Descriptive, RUNG 1. No rank, no p per head, no control family** — and **32 unadjusted
intervals are read at once, with no multiplicity correction**, which is exactly the inference "no
head outside clears" rests on. It identifies heads worth a **preregistered** test and nothing more;
it licenses a map, never *"head X is the writer"*. ⛔ **No singleton may be summed
against `E(HD_KO)`** to attribute a share: head 2 alone is 25.2 % of `HD_TOPK` and 21.8 % of
`HD_KO`. ⚠ **No interaction model over the 8-set was run, so additivity on basket is neither
established nor refuted** — non-decomposition is *measured* only on button (H.3). ⚠ **Four of `HD_TOPK`'s eight carry no
individually detectable load at this bar**, and two of those have marginals of the wrong sign — so
the set is certified while per-head necessity is refuted for half of it.

## H.3 🔴 The negative: head 2 does NOT replicate on the other codeword (D35)

Head 2 — the strongest single head on basket, selected by a rule frozen **before the census
existed** — was re-run on BUTTON. It fails:

```
BT_SINGLE  E = -0.00352162   ci95 [-0.0154519, +0.0060195]   <- CROSSES ZERO
           rank 6 of 21, p = 0.285714, attainable floor 1/21 = 0.047619
           5 controls strictly better, 0 ties
BT_KO      E = -0.28990714   ci95 [-0.34261611, -0.24548635] <- the positive control fires hard
```

**The instrument works on button**: the all-32 knockout moves the endpoint by −0.290 with a ci95
far from zero, so **this null is a measurement and not a dead apparatus.** The effect **collapsed
14×** from the codeword it was selected on — basket **−0.04947467** (ci95 excluding 0) → button
**−0.00352162** (ci95 crossing 0) — **retaining 7 %**. The independent re-derivation, sharing no
analysis code, agrees: rank 6 of 21, candidate −0.00352, **DOES NOT PASS**.

⛔ **It retracts NOTHING.** D32 and D33 are set-level basket results and H.2 is a basket census;
this tests **codeword** generality only. ⛔ **It says nothing about domain transfer** — the 23
button validation domains are *identical* to basket's. ⛔ *"Head 2 is the writer"* was forbidden
before the data and is now also **unsupported**. ⛔ RUNG 1, and explicitly **not** rung 4: no
activation state was transferred.

⚠ **And the set-level effect does not decompose on button either**: 21 single-head arms sum to
−0.058286 against a joint all-32 knockout of −0.289907 — the joint is **4.97×** the sum, and the
measured singles account for **20.1 %** of it. ⚠ **This is 21 of 32 heads, NOT a decomposition** —
the other 11 were never run singly on button, so −0.058286 is a **subset sum** and the true total is
unknown and could be larger. ⚠ **And D34's basket set does not predict button's ranking:** of the
five controls beating the candidate, **only head 19 is in D34's four** — heads 11, 20, 6 and 16 are
basket-irrelevant yet outperform the basket-selected candidate.

## H.4 How the parts depend on each other

🔴 **The dependency is NARROWER than it looks, and I had it wrong.** Checked against the frozen
preregs with `HD_TOPK = {2,6,13,17,19,23,24,28}` and `HD_BOTK = {0,9,10,11,15,16,29,30}`:

| section | heads | in `HD_TOPK` | in `HD_BOTK` |
|---|---|---|---|
| §1 (D37) | 17, 19, 23 | **3 of 3** | 0 |
| §4 (D38) | 17, 19, 23 | **3 of 3** | 0 |
| §2 (D39) | 6, 11, 20, 24, 27, 29 | 2 of 6 | **2 of 6** |
| §3 (D40) | 4, 6, 10, 11, 13, 18, 21, 27 | 2 of 8 | **2 of 8** |

**§1 and §4 localise within D34's four heads. §2 and §3 — the sprint's ONLY two certified p's — do
not.** Their heads were admitted from H.2's and H.3's *whole-head* arms by the 1.5 gate, not
selected from `HD_TOPK`; **four of them sit in `HD_BOTK`, the set H.1 uses as its null anchor.**
PR-CSI-020's prereg rejects the narrower pool by name: the screen's top-8 *"COULD NOT CERTIFY ON ANY
OUTCOME … the pool was widened before any cell of any head here was measured."*

**So the head-level half supplies §2's and §3's ADMISSION ELIGIBILITY, not their selection** — and
the deflationary reading I first wrote here (that the certified cell results rest on a head set
whose strongest member fails to replicate) **is false for exactly the two results that carry a
p-value.** It holds for §1 and §4, which carry none.

---

# A. The axis half — FIRST INCREMENT ONLY

**Added S-439.** ⛔ **This is NOT part three. It is ten of its twenty rows**, drafted as a deliberate
increment rather than as a section. The axis/necessity/dissociation families (D12–D31) remain
largely undrafted and SCOPE says so.

**Why these two first:** D19 is the sprint's only bidirectional conjunction and D24 its
matched-power dissociation — the two results most often leaned on elsewhere in the record. **Every
figure below was verified by me against the artefacts earlier in this sprint** (S-412 for the basket
ranks and the **shuffled-only** subfamily, **S-416** for button TRAIN, **S-413** for the held-out
button cell, S-430 for the necessity candidate and its 7.8 %, S-425 for the necessity floor).
⚠ **Two of those citations were wrong in the first version and are corrected here** — S-413 verified
the *held-out* cell, not TRAIN, and S-425 mentions button nowhere. ⚠ **And the blanket "every
figure" was too broad:** the point estimates and domain sign-counts were read from the artefacts
**for this draft**, not re-derived in any earlier entry.

## A.1 The same direction is top-of-family in BOTH directions (D18, D19)

At basket, layer 18, one rank-1 direction is the strongest in its control family **both** when added
back under a live knockout and when removed from a clean forward:

```
SUFFICIENCY  KO_AXIS - KO          TRAIN  +0.00264 [+0.00068, +0.00471]  rank  1 of 47  p 0.0213
                                   VALID  +0.00401 [+0.00098, +0.00775]  rank  1 of 47  p 0.0213
             subfamilies pass separately on BOTH splits:
                shuffled-only 1 of 25 (floor 0.0400)   random-only 1 of 23 (floor 0.0435)
NECESSITY    KO_NEC_AXIS - NEC_BASE  -0.00852 [-0.01127, -0.00592]  55 of 67 domains  rank 1 of 9
```

🔴 **The two halves are NOT equally certified, and the conjunction must never be quoted as though
they were.** Sufficiency passes at rank 1 of 47 with a floor of 0.0213 — ⚠ **but on TRAIN that cell
is ALSO in-sample** (`evaluation_is_in_sample: true`, 67 of 67 scored domains in the fit); **only the
VALIDATION cell is held out** (`false`, 0 in fit). **Necessity is rank 1 of 9
against an attainable floor of 0.1111 — above α — so it is INCONCLUSIVE by a ceiling whose UNREACHABILITY
was declared before the first arm ran** (⚠ the prereg declared the floor as **0.10**; the true floor
at 8 controls is **0.1111** — AM-8's correction, not an advance figure), and §L.3 records that the family which would have fixed it — PR-CSI-003-A — is **built and patched
but blocked by two of its own VOID conditions and never launched: escalated, not dead.** ⚠ *That is
PR-CSI-004's status, not this one's, and §L.3 warns in terms against blurring them.*

📌 **That the two directions use the SAME direction is MEASURED, not assumed:** the two arms load
*different* basis files with different `basis_sha16`, and their `cand_rank1` tensors are
**bit-identical**. The conjunction rests on this. ⛔ **Basket only** — nothing here was run on button,
and §A.2 is the reason not to assume it transfers. ⛔ **Three clauses must travel with the necessity
half every time: floor-limited, TRAIN-only, in-sample.** ⛔ **And the axis moves only 7.8 % [5.6, 10.1] of what whole-state removal moves —
about 92 % of the effect is elsewhere.** ⛔ *"The axis is causal"* is forbidden unqualified; *"the
axis is necessary"* is forbidden outright.

## A.2 The codeword dissociation, at matched power (D23, D24, D29)

Same layer, same family size, same family composition, same procedure, same 67 TRAIN domains:

```
basket L18 TRAIN   +0.00264  [+0.00068, +0.00471]  44 pos / 23 neg of 67  rank  1 of 47  PASSES
button L18 TRAIN   -0.00014  [-0.00111, +0.00081]  36 pos / 31 neg of 67  rank 36 of 47  DOES NOT PASS,
                                                                                        CERTIFIED
     ⚠ BOTH TRAIN cells are IN-SAMPLE (evaluation_is_in_sample: true, 67 of 67 in fit)
```

⛔ **ADDED S-455 — the two PRESPECIFIED statistics designed for exactly this comparison, which
this section owed and did not carry.** PR-CSI-005's S2/S4 and PR-CSI-007's S1/S2 require the
**family-size-free z** and the **exceedance rate with an exact Clopper–Pearson CI**, *"because this
statistic does not improve with more controls, so it is the honest cross-family comparison"* — which
is this section's entire subject. Re-derived:

```
                       rank        z          exceedance (R47-1)/46, Clopper-Pearson 95%
basket L18 TRAIN        1 of 47   +2.56        0 / 46 = 0.000  [0.000, 0.077]
button L18 TRAIN       36 of 47   -0.57       35 / 46 = 0.761  [0.612, 0.874]
basket L18 VALIDATION   1 of 47   +5.14        0 / 46 = 0.000  [0.000, 0.077]
button L18 VALIDATION   6 of 47   +1.40        5 / 46 = 0.109  [0.036, 0.236]
```

🔴 **These say more than the ranks do, in both directions.** On TRAIN the two exceedance intervals
are **disjoint by a wide margin** — [0.000, 0.077] against [0.612, 0.874] — so the dissociation is
an interval statement, not a comparison of two ordinals; and **button's TRAIN z is NEGATIVE**
(−0.57), meaning its own axis recovers *below the mean of its own control family*, which "rank 36 of
47" understates. ⚠ **But the held-out pair is closer than the ranks suggest**: button's validation z
is **+1.40** with exceedance [0.036, 0.236], against basket's +5.14 and [0.000, 0.077] — the
intervals still do not overlap, but button's held-out cell is **not** where its TRAIN cell is.

⚠ **Three further prespecified secondaries, reported because the preregs require them and because
two of them weaken the section.** Subfamily ranks (S3): button TRAIN **20 of 25** shuffled-only and
**17 of 23** random-only; button VALIDATION **4 of 25** and **3 of 23**. Leave-one-domain-out on the
rank (PR-007 S4): button validation's histogram is `{3:2, 4:1, 5:4, 6:12, 7:3, 8:1}` — **the best
attainable rank under any single deletion is 3**, still short of the bar, so the DOES-NOT-PASS
verdict is invariant to dropping any one domain. The analyser's per-control Holm test (S5):
`all_controls_rejected` **False** in both button cells, **0 of 46** rejected. And S6, the primary
comparator contrast `KO_AXIS − KO_ORTH`: TRAIN **+0.00079 [−0.00021, +0.00178] p = 0.130**,
VALIDATION **+0.00151 [−0.00017, +0.00309] p = 0.088** — **both CIs include zero**.

🔴 **ADDED S-456 — THE TWO CODEWORDS ARE NOT MATCHED ON READOUT VALIDITY, and nothing in the record
said so.** "Matched power" above means matched **control-family size**. Measured on the `BASE` arm —
the clean run, and the arm whose option mass gates the retained key set — the share of scored rows
falling below PR-CSI-001's declared 0.05 validity floor:

```
                rows below 0.05      median option mass
basket TRAIN       243 / 670 = 36.3 %        0.0902
basket VALIDATION   84 / 230 = 36.5 %        0.0835
button TRAIN        84 / 670 = 12.5 %        0.3298
button VALIDATION   25 / 230 = 10.9 %        0.2650
```

⚠ **On basket prompts the model puts roughly three times as much of its mass outside the two
options**, and basket's median option mass is ~3.5× lower. The endpoint is a two-way softmax over
`{concept, codeword}`, so for basket it renormalises a **much smaller share of the distribution**
than it does for button. **This is a dimension on which the dissociation's two sides differ and were
never compared.**

⛔ **It does NOT explain the dissociation away, and the direction of the bias is measured rather
than argued.** §A.3 re-executes basket's read at the 0.05 floor on both splits: a third of the keys
are discarded and **the verdict is unchanged, rank 1 of 47 on both**. 🔴 **And the candidate GREW —
+0.00264 → +0.00365 on TRAIN, +0.00401 → +0.00538 held out.** If the low-validity rows had been
manufacturing basket's effect, deleting them would have shrunk it; deleting them **enlarged** it. **That is what attenuation
looks like, and it is the opposite of what a readout artefact would produce.** ⚠ *Stated as the
inference it is: deleting rows also changes the retained set in ways this test does not isolate, so
what is established is the sign of the change, not a mechanism for it.* ⚠ **But "matched" must not be read as "matched on everything"** — it is
matched on family size, composition, layer, procedure and domains, and **unmatched on this**.

**This removes "unequal control families" as the explanation of the dissociation, and nothing
else** — it cannot say *why* the codewords differ.

⚠ **The matched-power comparison proper is TRAIN vs TRAIN** — ⚠ though the record notes this own-layer
TRAIN cell as the **weakest** evidence in the dissociation set (its paired-domain Δz CI includes zero;
matched-10 Fisher exact p = 0.1053), with the dissociation carried by the held-out split and the
shared-layer comparison. Basket's VALIDATION cell (+0.00401,
rank 1 of 47, 23 domains) is a **held-out strengthening and is NOT part of the power match** — *"the
same 67 domains"* must never be said while pointing at it. ⚠ **Both sides now have a held-out cell
and they are reported side by side, never pooled:** basket **rank 1 of 47**; button **+0.00218
[+0.00030, +0.00406] at rank 6 of 47, rank p 0.1277 against a floor of 0.0213 — which DOES NOT
PASS.** 🔴 **And by PR-CSI-007's own decision rule that means button's TRAIN result DOES NOT
REPLICATE.** ⚠ *It is not "nearly significant", and nothing here says button's axis is or is not
causal.* ⚠ Nothing pools this family's controls with TRAIN's — disjoint domains, and the two ran at
different blobs.

⚠ **Basket's PASS sits EXACTLY at its attainable floor** (0.02128 against a floor of 0.0213) in both
splits: a pass at the floor is a pass, but it has **no margin**. ⚠ **And basket's TRAIN rank 1 is
not robust to per-domain reweighting** — two of five schemes move it to rank 3 of 47, p = 0.0638.
That caveat is unaffected by everything above and still binds.

## A.3 The result §A.1 reports without naming: the rank-1 axis is top of its control family on both splits (D12)

⚠ **§A.1's sufficiency figures are D12's**, cited there as D19's because D19 restates them inside the
conjunction. D12 is the primary, and it is the most-amended row in the claim table — four amendments
govern it (AM-2, AM-4, AM-5, AM-7) and all four are carried here. ⚠ **Amendments are not the whole
of that row**: its caveat column also carries binding instructions that were never issued as
amendments, and the two below are both of that kind. **VALIDATION leads because D12 requires it** —
it is both the held-out split and the sturdier one — and **TRAIN's rank may not be quoted without
the sensitivity beside it**, which is why the leave-one-out line sits inside the block rather than
in a footnote.

```
VALIDATION  KO_AXIS - KO  +0.00401 [+0.00098, +0.00775]  15 pos /  8 neg of 23  rank 1 of 47  p 0.0213
TRAIN                     +0.00264 [+0.00068, +0.00471]  44 pos / 23 neg of 67  rank 1 of 47  p 0.0213
leave-one-domain-out on the rank:  VALIDATION holds rank 1 under 23 of 23 drops
                                   TRAIN holds rank 1 under 65 of 67; its worst single-domain
                                   deletion (pipeline_station) leaves rank 2 of 47, p = 0.0426 -- still passing
subfamilies, both splits: shuffled-only 1 of 25 (floor 0.0400)   random-only 1 of 23 (floor 0.0435)
population: 642 keys / 67 TRAIN domains and 215 keys / 23 VALIDATION domains, 53 arms each
```

⛔ **ADDED S-455 — PR-CSI-001's OWN secondary endpoints, which S-454's sweep missed.** PR-001
declares three under `endpoints.secondary`: the **recovery fraction with a degeneracy guard**, the
**realised intervention dose** (written delta norm, captured energy fraction, norm-match degeneracy
count) and the **semantic option mass**. The recovery fraction and the captured fraction are above;
the rest, re-derived:

```
                      written_norm mean   captured_frac   degenerate   recovery_frac
basket TRAIN              0.058492           0.03237          0           0.0219  (status ok, 0 draws dropped)
basket VALIDATION         0.058819           0.03195          0           0.0386  (status ok, 0 draws dropped)
                      28 rescue positions per row in both splits
```

✅ **The degeneracy guard passes**: `degenerate_positions` is **0** in both splits, so no row is
measuring rounding error, and the recovery fraction's own status is `ok` with **0 bootstrap draws
dropped**. ⚠ **The TRAIN recovery fraction is 0.0219, not the 0.0386 quoted above** — that figure is
VALIDATION's, and the two splits' denominators differ (`KO_FULL − KO` = +0.12041 TRAIN against
+0.10370 VALIDATION). TRAIN's candidate is **1.15 %** of `|KO − BASE|` and **2.19 %** of the whole
state, both ~40 % smaller than the validation figures this section leads with.

🔴 **The semantic option mass is the one that raises a question rather than answering one.** PR-001
names it *"the readout validity gate, min 0.05"*. The gate is applied to **one reference arm**
(`BASE` by default) and its surviving key set is then used for every arm — never per-arm, because
option mass is an outcome and a per-arm filter would be post-treatment selection (review R2-B1).
Measured on TRAIN: **`BASE` has 36.3 % of its 670 scored rows below 0.05** (243 rows, median
**0.0902**, minimum `0.000001`), while the rescued arms sit higher — `KO` and `KO_AXIS` both **18.1 %**
below, median **0.191**. ⚠ **It is `BASE`'s distribution that gates**, and it is the worst of the
three. The analyser's own comment on those rows is that *"the model's actual prediction is some
third word entirely"*. ⚠ **Every number in the record was computed at `option_mass_floor = 0.0`** —
the analyser's help calls that *"the frozen protocol, which gates option mass POOLED"*, with 0.05
available as a **declared sensitivity** — and **that sensitivity had never been run**: all 27
subspace and swap artefacts record floor 0.0 and no `_om` artefact exists.

🔴 **ADDED S-455 — IT HAS NOW BEEN RUN, ON BOTH SPLITS, AND THE VERDICT IS INVARIANT.** The frozen
read was re-executed at floor 0.0 as a control and at the prereg's 0.05, through the analyser end to
end:

```
                 keys   candidate - KO                       p        rank        verdict
TRAIN  floor 0.00  642   +0.00264  [+0.00068, +0.00471]   0.0107   1 of 47    PASSES
TRAIN  floor 0.05  412   +0.00365  [+0.00080, +0.00686]   0.0164   1 of 47    PASSES
VALID  floor 0.00  215   +0.00401  [+0.00098, +0.00775]   0.0182   1 of 47    PASSES
VALID  floor 0.05  135   +0.00538  [+0.00197, +0.00923]   0.0069   1 of 47    PASSES
```

✅ **Both floor-0.0 controls reproduce the published artefacts exactly** — point, CI, p, key count
and verdict — so the comparison is against a validated harness and not against a re-implementation.
✅ **Dropping the invalid-readout rows costs 36 % of the keys on TRAIN (642 → 412) and 37 % on
VALIDATION (215 → 135), and the candidate GROWS on both splits** (+38 % and +34 %), with all three
gates still true and the rank unchanged at 1 of 47. ⛔ **The sensitivity does not threaten the
result; it strengthens the point estimate and widens the interval.** ⚠ **This was not the only
possible outcome, which is why it was worth running** — a third of the evidence is discarded and the
verdict does not move. ⛔ **NOT established: that the same holds for any other family.** This was run
for D12's two cells only; the swap cells and the button family were not re-run at 0.05.

⛔ **ADDED S-454 — two more PRESPECIFIED secondaries this section owed and did not carry.**
PR-CSI-005's S2 and S4 (restated as PR-CSI-007's S1 and S2) require the **family-size-free z** and
the **exceedance rate with an exact Clopper–Pearson CI**, both precisely because they are the
statistics that *do not* improve when the control family is enlarged. Re-derived:

```
                    z = (cand - mean(46 ctrl)) / sd   exceedance (R47-1)/46, Clopper-Pearson 95%
basket TRAIN                 +2.56                     0 / 46 = 0.000  [0.000, 0.077]
basket VALIDATION            +5.14                     0 / 46 = 0.000  [0.000, 0.077]
```

⚠ **The z is the honest cross-family number and it says the two splits are not alike**: the held-out
cell sits **5.1 control-SDs** above the control mean, the TRAIN cell **2.6**. The rank is 1 of 47 in
both and cannot show that. ⚠ **The prereg names basket's TRAIN z as `+2.561`; it does not reproduce
to three decimals under any of four conventions I tried** (controls-only vs controls-plus-candidate
× ddof 0/1); the closest is **+2.5577**, controls only, ddof = 1, which is the value quoted above.
The discrepancy is in the reference, not the verdict, and nothing here turns on it.

⛔ **ADDED S-453 — the analyser's own PRESPECIFIED per-control test is weaker than the rank, and it
was absent from this section.** PR-CSI-005's `secondary_statistics_PRESPECIFIED` S5 requires
`specificity_holm` / `specificity_all_controls_rejected` *"as the analyser emits them, reported
unmodified"*. The test is a **one-sided sign-flip (candidate > control), Holm-corrected across the
46-control family**, and `specificity_all_controls_rejected` is **False on both splits**. Rejections
at α = 0.05: **6 of 46 on TRAIN**, **0 of 46 on VALIDATION** — where the smallest Holm-corrected p is
**0.0529**. ⚠ **So on the held-out split the axis is top of its family of 47 and does not
significantly beat a single individual control once multiplicity is paid for.** Both are true and
they measure different things — the rank asks whether the candidate tops the family, Holm asks
whether it beats each member — but quoting only the rank overstates the per-control evidence.

⚠ **Both p-values sit EXACTLY at their attainable floor** (0.02128 against 1/47 = 0.0213): a pass at
the floor is a pass with **no margin**, and §M.9 records that the implementation certifies only at
rank 1 in any case.

🔴 **The effect is very small, and two denominators are routinely conflated.** The candidate
`+0.00401` is **1.74 %** of the knockout it is rescuing from (`KO − BASE` = −0.23094) and **3.87 %**
of what the whole state restores (`KO_FULL − KO` = +0.1037) — the artefact's own
`recovery_fraction_candidate_of_full` reads **0.0386**. ⛔ *"Recovers 3.9 % of the knockout"* merges
the two and is forbidden.

⛔ **TRAIN is IN-SAMPLE** (`evaluation_is_in_sample: true`, 67 of 67 scored domains in the fit);
only VALIDATION is held out. ⛔ **The captured fraction is an AMPLITUDE, not an energy**, and the
quantity itself belongs beside the correction: the axis spans **≈ 3.2 % of the displacement in
amplitude** (`arm_meta.KO_AXIS.captured_frac` mean **0.03237** TRAIN, **0.03195** VALIDATION), so the
energy fraction is of order **0.1 %**. ⚠ **But the persisted field is a mean of per-row ratios**, so
squaring it yields the square of the mean and *not* the mean of the squares: the exact mean energy
fraction is **not recoverable** from what was stored, and 0.1 % is an order, not a measurement.

⚠ **Earlier figures at the 34- and 30-control families are superseded** — the governing artefacts
are the n46 pair — and a **stale floor pair `(1/35, 1/31)`** stood uncorrected across several ticks, where both floors
are now `1/47`.

⚠ **The shuffled-only subfamily was once recorded as "INCONCLUSIVE on its own, both splits"** at
1 of 13 and 1 of 9. **At n46 it is 1 of 25 on both splits, floor 0.0400 — it certifies on its own**,
so that caveat understated the result rather than overstating it.

## A.4 The cross-codeword axis swap: NO CELL IS CLAIMED FOR EITHER DIRECTION (D25, D27, D30; **D26 is reported in §A.4b**)

🔴 **This family's original headline was WITHDRAWN, and a prohibition written to police it mandated
a sentence that was itself later retracted.** It is drafted here with that history attached, because
a careless summary of it would do more damage than any other section of this draft.

All four cells, read by me from the four `DCS_CSI_SWAP_*_n46.json` artefacts:

```
                                                        swap arm                    recipient's OWN axis
direction A  basket's axis -> BUTTON's knockout  TRAIN  +0.00150 [+0.00047,+0.00256] r 4/47   -0.00014  rank 36/47
                                                 VALID  +0.00338 [+0.00122,+0.00559] r 1/47   +0.00218  rank  6/47
direction B  button's axis -> BASKET's knockout  TRAIN  +0.00090 [-0.00029,+0.00217] r13/47   +0.00265  rank  1/47
                                                 VALID  +0.00224 [+0.00042,+0.00430] r 2/47   +0.00401  rank  1/47
                                   TRAIN cells are IN-SAMPLE; VALIDATION cells are held out
```

**The preregistered rule is `HELPS iff R47 ≤ 2`, and its step 6 is: if the two splits disagree, the
direction is reported NOT REPLICATED and no cell is claimed for it.** Applying it: **direction A
disagrees (4 vs 1) and direction B disagrees (13 vs 2).**

⛔ **So the verdict is: NO CELL IS CLAIMED FOR EITHER DIRECTION. The 2×2 is unresolved in both
directions, and C1 — "basket simply has a better probe" — is NEITHER REFUTED NOR SUPPORTED by it.**

⚠ **The native column is in that table for a reason**: direction B's recipient is already at
**rank 1 of 47 on both splits**, so a transplant has nowhere to go, while direction A's recipient
sits at **36** and **6**. The two directions are not symmetric tests, and reading the four swap
ranks without the native beside them makes them look like one.

⚠ **The family's single best-looking cell carries its own null, and the two facts are about the same
23 domains.** Direction A's validation cell is **rank 1 of 47** — strictly the largest of the 46
controls — yet the swap and button's **own** axis are **not statistically distinguishable there**:
`XSWAP_FROM_BASKET − KO_AXIS` = **+0.00120**, ci95 **[−0.00044, +0.00282]**, p = **0.1716** over the
23 held-out domains, **a CI that crosses zero**. That is the fourth cell of §A.4b's table. **"Rank 1
of 47" and "indistinguishable from the native axis" are both true of this cell**, and quoting the
rank without the contrast is the most flattering single sentence this family admits.

🔴 **What must never be said, because it was said and withdrawn:** *"basket's axis rescues button 32
ranks better than button's own axis does"*, *"C1 is SUPPORTED"*, *"the STATE hypothesis is
REFUTED"*, and any CELL 1 or CELL 2 reading. ⚠ **And the replacement was wrong too** — a prohibition
once required *"CELL 4 on TRAIN, C1 refuted by the fixed rule"* as a mandatory companion sentence,
which a later amendment withdrew. **A rule that compels a retracted claim is the one failure mode
care cannot catch**, because following it is what triggers it.

⚠ **The rank p here is DESCRIPTIVE, not a valid permutation p — and BOTH halves of that finding
have to be read together, because each one alone misleads.** The rank test's null requires the
candidate to be exchangeable with the family it is ranked against, and by construction it is not:
`|cos|` with the recipient's native axis runs **min 0.0001, median 0.0156, max 0.1894** across the
46 controls, while the swap axis sits at **0.5569** — **2.9× more aligned with the native axis than
any control**. The controls are built near-orthogonal to the native axis; the transplanted axis
retains 56 % of it. So the ranks — **all four, 4 and 1 and 13 and 2 alike** — may be quoted as
*positions*, never as **p-values**. ⚠ *(Not "never as tests":
this section's own verdict comes from testing all four ranks against the preregistered `R47 ≤ 2`
bar. A fixed threshold on a position is not a permutation p, and it is the p that is unavailable.)* ⚠ **Including rank 1**, direction A's validation cell and the strongest
number this family has: the axis whose alignment breaks exchangeability is the *same axis* in that
cell, so the objection governs it identically. (D27's own row enumerates only *"4, 13 and 2"*
because it was written before D30 gave direction A a validation split; the omission is the row's
vintage, not a judgement about that cell.)

**The obvious repair was attempted and it failed, and that cuts the other way.** If alignment
explained the swap's position, recovery should track `|cos|` across the control family. It does not:
Pearson **r = −0.027** over the 46 controls, and a linear fit extrapolated to `|cos| = 0.5569`
predicts **+0.000035** against an observed **+0.001499** — a residual of **+1.95 sd**. **The
alignment asymmetry does not explain rank 4.** It weakens the inferential standing of the ranks
without explaining them away. Stating only the first half reads as "the swap result is an artefact";
stating only the second reads as "the objection was answered". Neither is what was measured.

⚠ **This does not touch the paired contrast in §A.4b.** `XSWAP − KO_AXIS` is a within-report,
domain-paired statistic and makes no exchangeability assumption; whatever is wrong with the ranks
leaves it standing.

*The `|cos|` and regression figures in these two paragraphs are* `[READ, not reproduced]` *— they
derive from the `.pt` bases, which need the run environment, and no interpreter with `torch` is
reachable from the login node. Everything else in §A.4 and §A.4b was re-derived (S-451, S-452).*

🔴 **And direction B's validation cell is where the analyser and its preregistration DISAGREE
(AM-48):** at **rank 2 of 47, rank_p 0.04255**, the prereg's `definition_of_HELPS` (`rank ≤ 2`) says
**HELPS**, while the artefact's own `VERDICT` string says *"DOES NOT PASS … INSIDE the controls, not
above them"* — of a candidate above 45 of 46 controls. **The claim table read it by the frozen rule.
Nothing reconciles the two, and the divergence is live in the published file.**

⚠ **So how much of this section's verdict rests on the contested rule? Applied both ways, the
answer is: the top line survives, one label does not.** Under the prereg (`HELPS iff R47 ≤ 2`)
direction B's splits **disagree** (13 vs 2) and it is NOT REPLICATED. Under the rule the analyser
actually implements (`PASS iff rank == 1`) rank 2 fails, so B's splits **agree** and B becomes
claimable as *consistently does not help*. ✅ **The 2×2 is unresolved either way**, because
**direction A's splits disagree under BOTH rules** (4 vs 1 — rank 1 passes under both), and a cell
needs both directions claimable. ⛔ **But "direction B is NOT REPLICATED" is rule-dependent and must
not be stated as if it were not.** The verdict is determinate; that one label is not.

### A.4a The preregistration's GRADED read (S1), all four cells

🔴 **CORRECTED S-453 — this contrast is PRESPECIFIED, and it had been reported for one cell of
four and mislabelled.** `configs/dcs_csi_pr006_axis_swap.json` carries it as
`secondary_statistics_PRESPECIFIED.S1_paired_contrast_against_the_native_candidate`: *"Delta =
recovery(XSWAP_FROM_<donor>) − recovery(KO_AXIS) … domain-clustered bootstrap over the split's
domains, 20000 resamples, seed 20260913 … **This is the GRADED read and must be reported beside
every cell of the 2×2.** Sign convention: Delta > 0 means the FOREIGN axis rescues the recipient
BETTER than the recipient's own."* It is **secondary**. It is **not unpreregistered** — this draft
and the claim table both called it so, inheriting the error from D25.

All four, at the prereg's own B and seed:

```
                                S1 = XSWAP - KO_AXIS         ci95              p2      pos/neg
A  basket's axis -> BUTTON  TRAIN  +0.00164   [+0.00065, +0.00260]   0.0019   47 / 20
                            VALID  +0.00120   [-0.00043, +0.00283]   0.1716   13 / 10
B  button's axis -> BASKET  TRAIN  -0.00175   [-0.00288, -0.00070]   0.0020   22 / 45
                            VALID  -0.00177   [-0.00366, -0.00024]   0.0514    9 / 14
```

🔴 **Reported together these are not "one survivable number". They are a DIRECTION-ASYMMETRIC
pattern.** The foreign axis rescues **button** better than button's own on both splits (S1 > 0), and
rescues **basket** worse than basket's own on both splits (S1 < 0), at nearly equal magnitude
(+0.00164 against −0.00175 on TRAIN). ⚠ **Both TRAIN cells clear α and neither held-out cell does** —
the same in-sample/held-out split §A.4b reports, because the probe contrast there **is ±S1**.

⚠ **Direction B is the weaker test by construction, and that is why its sign is negative.** Basket's
native axis already ranks **1 of 47** on both splits, so a transplant has almost no room above it;
in both B cells the swap sits **below** the native. Direction A's native ranks **36 of 47** on TRAIN
and **6 of 47** on validation — that is the room A has and B does not. **A negative S1 in direction
B is a ceiling, not a failed transplant**, and reading the four signs as "basket's probe is better"
without this is the reading D25's caveat exists to block.

⛔ **The magnitude must travel with every one of them, or these read as large numbers.** As a
fraction of what the whole clean state recovers (`recovery_fraction_candidate_of_full`, read per
cell): **A train 1.4 %, A valid 2.5 %, B train 0.8 %, B valid 2.2 %** — **97–99 % of the recovery is
elsewhere in every cell.** §A.3 states the same ratio for D12 and this family is no different: the
axis is top-of-family in one cell, and top-of-family is a small thing.

⛔ **The other prespecified secondaries this section owed, re-derived (S-454).** PR-CSI-006's S4
requires `n_degenerate` and says it **MUST be 0** — it is **0 in all four cells**, so no arm is
measuring rounding error. The family-size-free z and the exceedance rate (S6) for the four cells:

```
                   z      exceedance (R47-1)/46, Clopper-Pearson 95%
A train         +1.64      3 / 46 = 0.065  [0.014, 0.179]
A valid         +2.67      0 / 46 = 0.000  [0.000, 0.077]
B train         +0.47     12 / 46 = 0.261  [0.143, 0.411]
B valid         +2.65      1 / 46 = 0.022  [0.001, 0.115]
```

⚠ **The z says what the ranks cannot: B train's swap is half a control-SD above the control mean** —
it is not near-missing, it is **inside the family** — while A train's z of +1.64 sits well above the
family despite ranking only 4 of 47. **Rank and z disagree about which cell is closest to passing**,
and the prereg asks for both for exactly this reason.

⛔ **And S5, the analyser's per-control specificity test, also prespecified and also absent until
now.** `specificity_all_controls_rejected` is **False in all four cells**; rejections at α = 0.05 are
**A train 8 of 46, A valid 0 of 46, B train 1 of 46, B valid 2 of 46** (smallest Holm p 0.0067 /
0.0695 / 0.0308 / 0.0432). ⚠ **Neither held-out cell rejects a single control** — the same
in-sample/held-out asymmetry S1 shows, from a statistic that never entered the record.

⚠ **On the CI's last digit.** At the prereg's seed the A-TRAIN bound is `[+0.00065, +0.00260]`; the
claim table records `[+0.000664, +0.002605]` from an independently seeded bootstrap, and the artefact
publishes no stored value for this contrast. The disagreement is seed, not substance — §M.11.


### A.4b The same four numbers, read as a 2×2: a probe main effect on TRAIN, and no test of the recipient factor (D26)

§A.4 reports what the preregistration returns. The four cells also support a reading the
preregistration does not contain, and it points the other way, so it is reported here rather than
left out. 🔴 **CORRECTED S-453 — what is post-hoc here, precisely.** The **four cell contrasts** below are
**±S1, the preregistration's graded read** (§A.4a); they are secondary but **prespecified**. What is
post-hoc is the **2×2 arithmetic built on top of them** — the main effects and the interaction —
which review R10 constructed after the read. An earlier draft called the whole subsection
unpreregistered; that was wrong, and it understated the four cells while overstating nothing.
⚠ None of it may be quoted without §A.4's result beside it.

Both TRAIN reports carry the **same 67 domain names** (intersection 67 of 67), so the 2×2 pairs
domain by domain:

|  | probe = basket | probe = button |
|---|---|---|
| **recipient = button** | +0.001499 | −0.000145 |
| **recipient = basket** | +0.002649 | +0.000900 |

Each cell is `arm − KO` within its own report, so the knockout baseline cancels within a recipient.
Paired over the 67 common domains, under the family's own sign-flip test:

```
PROBE main effect      +0.00170  ci95 [+0.00092, +0.00251]  p2 = 0.0001
RECIPIENT main effect  +0.00110  ci95 [-0.00056, +0.00286]  p2 = 0.2216
INTERACTION            -0.00011  ci95 [-0.00148, +0.00122]  p2 = 0.8825
|recipient| / |probe| = 0.647
```

**What this licenses, and it is narrow.** A *pure*-state model — one in which the probe contributes
nothing and only the recipient's state matters — is refuted. Nothing more. The recipient main effect
is **not estimated by this design**: the contrast crosses button and basket, and pooling the two
codewords is what §A.2's dissociation forbids — they differ in their whole response to this
instrument, which is the result §A.2 certifies. So the experiment contains **no legitimate test of the recipient factor at all**. Its point
estimate is 65 % of the probe effect with a CI containing values *larger* than the probe effect, and
the interaction is flat — the shape of "both factors, additively". **"The state hypothesis is
REFUTED" is absence of evidence**, and the only permitted wording is: *a pure-state model with no
probe effect is refuted; the recipient factor is not estimated by this design.*

⚠ **And the rule that fixes that wording also requires the state-side reading to travel with it,
because it is the one live alternative pointing the other way.** `|cos|` between each axis and
**button's OWN knockout delta**, over 670 rows: **basket's axis 0.056749, button's own axis
0.051459, best control 0.036661** — **basket's axis fits button's own knockout delta better than
button's own axis does.** That reads as *"button's probe mis-estimates a real state direction"*,
which is a **state** reading of the same data. It is **not proven** — alignment predicts recovery
only weakly across the controls (r = 0.19, n = 46) — but it is live, and §A.4b argues the probe side
for thirty lines, so leaving it out would make this subsection one-sided in exactly the way the rule
exists to prevent. *These three cosines are* `[READ, not reproduced]` *— same reason as §A.4's:
they need the `.pt` bases and there is no `torch` on the login node.*

🔴 **CORRECTED S-451 — "the probe effect replicates three times" does not survive re-derivation, on
two independent counts. Both were found by recomputing the cells from `domain_means` rather than
re-reading the record.**

**(i) There are FOUR cells, not three, and the fourth was never reported.** The probe contrast is
defined in every one of the family's four reports. Re-derived, all four:

| recipient | split | in-sample | probe contrast (basket-probe − button-probe) | sign-flip p2 |
|---|---|---|---|---|
| button | train | yes | **+0.001644** | **0.0019** |
| basket | train | yes | **+0.001749** | **0.0020** |
| basket | **validation** | **no** | **+0.001770** | **0.0514** |
| button | **validation** | **no** | **+0.001195** | **0.1716** |

The omitted cell is **button/validation** — the only held-out cell for the button recipient, and the
smallest of the four. "Replicates three times" is three of four, and the one left out is the weakest.

**(ii) The p-values in the record are BOOTSTRAP PERCENTILE p's, not the test this family reports.**
Every `contrasts` block in these artefacts publishes `ci95` from the paired bootstrap and
`p_two_sided` from `exact_signflip`; the record's trio (0.0014 / 0.0007 / 0.019) reproduces under the
bootstrap percentile (0.0018 / 0.0008 / 0.0177) and under **no** other test tried — not the sign-flip,
not a paired *t*, not a sign test, not one-sided forms of any of them. The switch is not neutral: it
moves the held-out basket cell from **0.0514 to 0.019**, across the 0.05 line, in the only direction
that matters.

**And the switch is systematic, not confined to those cells.** The factorial p's in the record are
bootstrap percentile p's too — recipient **0.2001** quoted as *0.201*, interaction **0.8890** quoted
as *0.888* — against the sign-flip **0.2216** and **0.8825** given in the block above. ⛔ **No
conclusion moves there**: the recipient effect is NOT TESTED and the interaction is flat on either
test. What moves is the claim that the row reproduces — **every p in it comes from the estimator
these artefacts do not publish**.

**So the accurate statement is: the probe contrast is significant in both TRAIN cells and in NEITHER
held-out cell** (0.0514 and 0.1716 under the family's own test). The PROBE main effect itself
(p2 = 0.0001) is computed from the two TRAIN reports and is therefore a **TRAIN-only, in-sample**
quantity. It is real and it is not a replication.

⚠ **One asymmetry that cannot be waved away in either direction.** 🔴 **CORRECTED S-453 — an
earlier draft called this a DOMAIN-level asymmetry and it is not.** Both arms in both TRAIN reports
carry the *same* `fit_domains_sha16` (`4614853e5636eb5f`, n_fit = 67), so the donor's fit domains and
the recipient's are the **same 67 domains** — as the pairing premise twelve lines above already
says. The asymmetry is **codeword-level**: the native arm was fit on the recipient's *own codeword*
and the transplanted arm on the *donor's*, so the native arm carries a codeword-specific in-sample
advantage the swap arm does not. That advantage
inflates the contrast where the native arm is the basket-probe term (recipient = basket) and
*deflates* it where the native arm is the button-probe term (recipient = button) — it pushes the two
TRAIN cells in **opposite** directions. They nonetheless came out nearly equal (+0.001644 vs
+0.001749). That is an observation consistent with a small advantage; it is **not** a measurement of
one, and no arm here was re-fit to obtain it.

🔴 **ADDED S-453 — THE HELD-OUT 2×2, which an earlier draft said was not established and never
computed.** Both VALIDATION reports exist and carry the **same 23 domain names** (intersection 23 of
23), so the identical factorial is computable off TRAIN. Re-derived under the family's own sign-flip:

```
held-out cells       probe=basket   probe=button
recipient=button       +0.003378      +0.002183
recipient=basket       +0.004005      +0.002236

PROBE main effect      +0.00148  ci95 [+0.00025, +0.00281]  p2 = 0.0363
RECIPIENT main effect  +0.00034  ci95 [-0.00205, +0.00294]  p2 = 0.7978
INTERACTION            -0.00057  ci95 [-0.00288, +0.00148]  p2 = 0.6394
```

⚠ **This cuts FOR the probe reading and it was missing, which is the same defect as every other one
this section has had — only pointing the other way.** The held-out **probe main effect clears α**
(+0.00148, p = 0.036) at 87 % of the TRAIN magnitude, while the recipient effect stays untested
(p = 0.80) and the interaction stays flat (p = 0.64). **The pattern replicates off TRAIN; the
individual cells do not.** Reporting the pooled effect on TRAIN and only the per-cell nulls held-out
was an asymmetry a reader could not see: with n = 23 and one tied domain, the per-cell held-out tests
are underpowered, and pooling the two recipients is what recovers the signal.

⛔ **It does not rescue the per-cell claim.** "Significant in both TRAIN cells and in neither
held-out cell" remains exactly true, and §A.4a's four S1 rows stand. What changes is that **the
probe factor does generalise off TRAIN when the two recipients are pooled** — and the pooled
contrast is as post-hoc as the TRAIN one, so it is secondary on both splits.

**NOT ESTABLISHED by this subsection:** that the probe factor generalises **cell by cell** off TRAIN
— it does not, and only the pooled contrast clears α; that the recipient factor exists or does not;
that the state hypothesis is refuted in any form other than the pure one; and anything at all about
**necessity**, which has never been run in the swap design.
