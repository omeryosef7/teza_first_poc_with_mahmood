# CSI sprint — RESULTS SECTION, first draft

**Created S-417, 2026-09-25.** Source of every sentence: `reports/DCS_CSI_CLAIM_TABLE.md`. This
file **adds no claim and softens no caveat**. Where the table forbids a phrasing, the forbidden
phrasing is named here too, so a later editor cannot reintroduce it by not knowing about it.

⛔ **STATUS: DRAFT PROSE, NOT A CLAIM SOURCE.** If this file and the claim table ever disagree,
**the claim table wins** and this file is the thing that is wrong. Figures in §2–§4 for **D39/D40/D41** were re-derived by hand in S-373, S-411 and S-415; **§1's D37
figures were re-derived in S-417** from `DCS_CSI_PR015_CELL_CENSUS_3HEADS_validation.json`, and
**§4's D38 figures come from S-307/S-328**, not from any of those three. None is copied from a
summary field. ⚠ *The header of a draft is the first sentence a sceptical reviewer tests; this one
names its scope rather than claiming a blanket.*

---

## 0. One paragraph of setup

We ask where in a transformer a *codeword* — a token the model has been instructed to emit in place
of a concept — is installed. The instrument ablates a single attention cell `(layer, head)` during
the prefill of an in-context prompt and measures the change in a semantic log-odds readout at a
fixed position. The statistical unit is the **domain**. The split manifest
`dcs_ts116_domain_split.json` assigns **70 train / 23 validation / 23 test**; the census families
score **67** train domains, the 70 less **three whole-population domains excluded by every CSI
prereg** — those three are `train`-assigned, and a config field once mislabelled them `test_domains`
and collapsed them to the count "3", which is the error AM-37/S-312 corrected. **No arm in this sprint touched a TEST domain — and TEST is nonetheless NOT an available axis:**
it was read to completion on 2026-09-08 and is **selection-contaminated on knobs every CSI family
inherits** (AM-39). ⛔ *"TEST is unspent / untouched / available"* is a predecessor-phase belief
that S-314 refuted and D5 is annotated to block; it must not be re-imported. An
attribution *screen* computed on basket TRAIN nominates, for each head, the band layer carrying
most of that head's effect. Every confirmatory result below asks one question: **does the screen's
per-cell prediction hold up under intervention on data it was not fitted on?**

---

## 1. The screen's per-cell prediction holds at the CELL coordinate on basket validation (D37)

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
P(all four match) is **2.06e-04** under that marginal against 1.52e-04 uniform [†], and **an all-L14
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

## 4. One CANNOT ANSWER, and one honest negative

**PR-CSI-016 could not test the question it asked (D38) — this is CANNOT ANSWER, NOT a negative result.** Both admitted heads matched at L14, so the
preregistered **spanning rule fired**: a shared top-of-band bias and a correct screen are
indistinguishable there. K = 2, M = 2; **the binomial is forbidden for this family and is not reproduced here** — note it collides with D39's certified conditional p, so printing it invites a reader to conclude PR-CSI-016 passed. Conditional 1.0
(K_unique = 0) and permutation 1.0 over a space of size **1**. The fallback delivered a head-level
cross-codeword test never run before: head 17 **98.3 %**, head 19 **88.7 %** (both ci95 excluding
0), head 23 **18.4 %** with **ci95 crossing zero** — ⚠ **an AMPLITUDE result only**: exploratorily, head 23's per-cell depth **shape** tracks across codewords at ρ = +0.817, so *"head 23 does not transfer"* is true of the amplitude and false of the shape (AM-41, **not preregistered**). ⛔ *"The screen transfers across codewords"* and
the figure 0.012346 are forbidden from this family. ⛔ *"Head 23's mechanism is refuted"* is
forbidden — null on button is CANNOT ANSWER, not a negative.

**Rung 2 was attempted and is not reachable (D41).** Decodability was built, reviewed, executed and
piloted, then **closed without a validation read, by decision**. Four measurements: K = 8 is the
*whole* admissible population (0 of 7 fresh basket heads clear the frozen 1.5 gate, best 1.400; on
button the ceiling is K = 2); the natural statistic is **confounded** — the direct-path projection
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
held-out axis exists, and restricting controls to one head's nine cells returns the 1/9 floor.
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
| any rung-2/3/4 language | every claim here is rung 1 | AM-34 |
| "correcting" either 1.52e-04 | `(1/9)^4 = (1/3)^8 = 1/6561` — two real quantities, one value | [†] §4 |
| ‼ "TEST is unspent / untouched / available" | read to completion 2026-09-08 and selection-contaminated | AM-39, D5 |
| "the screen is a validated cell selector in general" | forbidden for **both** D39 and D40, not just D39 | D39, D40 |
| "the basket result is weakened" (by D38) | D38 is CANNOT ANSWER; D37 stands | D38 |
| "the mechanism is these four cells" | overstates by ~1.7× — the peaks are 58.8 % of `CL_KO` | D37 (c) |
| "the effect is single-layer" | forbidden; §1's depth framing is where this returns | D36 |
| a 4-of-5 or 2-of-3 rate from D40's heads | no p attaches to either subset and none was computed | D40-c |
| "head 23 does not transfer", unqualified | true of amplitude, false of shape (ρ = +0.817) | AM-41 |
| "D37 is superseded by D40" / "D38 is explained by D39" | both ⛔; the §2→§3→§4 order invites both | D39, D40 |
| "a NULL source control is support" | a null control is CONFOUNDED — report as CANNOT ANSWER | AM-43 |

**‼ marks a phrasing this draft itself committed and had corrected** — the TEST row is here because
§0 asserted exactly it in the first version (S-417), which is the whole argument for keeping this
checklist attached to the prose rather than in a reviewer's head.
