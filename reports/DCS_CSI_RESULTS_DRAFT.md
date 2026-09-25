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
(PR-CSI-001–009, 20 claim-table rows) — is **almost entirely absent**: two of its rows are drafted as §A and eighteen are not; see the correction below. The
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

⚠ **UPDATED S-439/S-440: TWO of the twenty are now drafted as §A** — D19's bidirectional conjunction
and D24's matched-power dissociation, with D18, D23 and D29 as their supports. **That is an
increment, not the part: EIGHTEEN rows remain undrafted.**

**The omitted rows are the AXIS, NECESSITY and DISSOCIATION families — PR-CSI-001 through 009**: the
rank-1 installation axis and its control families, the necessity direction, the button/basket
codeword dissociation at matched power, and the cross-codeword axis swap. **Only the two named
above are in this file, as §A.** §L.3 touches two of these results (necessity, basket-at-L20) only
to limit them, which is how the gap stayed invisible for so long — they appeared as *limitations of
results the draft never stated*, and for the sixteen still undrafted they still do.

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
below rests on **23** domains rather than 67, and a 230-row read is n = 23 because the domain is the
unit. ⚠ **The confirmatory p's themselves are NOT over domains at all** — binomial, conditional and
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
| ‼ "these are the sprint's results" / "the sprint's negatives are §4's" | §1–§4 are the CELL-level part and §H the HEAD-level part; of the axis / necessity / dissociation families (D12–D31) **only D18/D19/D23/D24/D29 are drafted, as §A — EIGHTEEN rows remain in neither** — see SCOPE | D12–D31, SCOPE |
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

⚠ **`|E(HD_BOTK)|` doubles as the NULL ANCHOR in §H.2** — a third use of a threshold, beyond the two
§M.5 enumerates. It is the family's own opposite-end set, not an external bar.

## M.9 What the design cannot do

The screen is fitted on **basket TRAIN**. For the cross-codeword family (§2) the prediction is held
out on **codeword**; for the within-codeword replication (§3) it is held out on **split only**.
**There is no control family of arbitrary cells** in any family, because no admissible held-out
axis exists — and restricting controls to one head's nine cells returns the 1/9 floor, which is
above α for every attainable effect size.

---

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
recorded as identical to basket's. **The limitation is sprint-wide, not cell-level.** Verified by comparing the domain sets arm-by-arm: union 23, intersection 23.
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

**Added S-439.** ⛔ **This is NOT part three. It is two of its twenty rows**, drafted as a deliberate
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
