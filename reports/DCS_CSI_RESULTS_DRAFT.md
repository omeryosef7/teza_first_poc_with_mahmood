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

---

# M. Methods

**Added S-419.** Every definition below is quoted or derived from the frozen prereg
`configs/dcs_csi_pr020_cell_census_basket_8heads.json`, the frozen read `runargs/dcs_csi_pr020_read.txt`,
or an arm's own `RUNMETA.json` — **not from memory and not from an earlier log entry**. Where the
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
admitted multiset. A p above α is a **FAIL** at K ≥ 3, but where the floor itself exceeds α **no
outcome could have certified**, and the verdict is **CANNOT ANSWER (structural)** rather than
evidence against the screen. At K < 2 the same applies. This is why a family that cannot win is not
reported as a loss.

## M.7 Gates and VOID conditions

**GATE 0** checks liveness and arm identity. **Liveness is a four-way conjunction**: no recorded
violations, **zero decode edits**, the median prefill-edit count equal to the arm's expected dose,
and the identity check. Identity comes from each arm's **own recorded intervention flags, not its
tag** — `knockout_cells` for the 80 cell-scoped arms; for the all-32 `*_KO` arm the conjunction
`knockout_heads == ALL` **and no cell list at all**, because a full-band nine-cell arm records an
empty `knockout_heads` and the *identical* dose 2016. ⚠ **The sweep asserts the base arm's identity
unconditionally** (`"not intervened"`), so 2 of the 82 arms are not identity-checked from their own
flags by GATE 0 — the census reader does read the base arm's flags separately. Exit 0 = all arms pass; 1 = failure;
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

## M.8 What the design cannot do

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
for rung 3 or 4 evidence that does not exist here.

## L.2 There is no arbitrary-cell control, and the reason is structural

No family in this sprint contrasts a nominated cell against **arbitrary** cells, so *"cell (L,h) is
the writer"* is unavailable throughout. This is not an omission that more compute fixes: no
admissible held-out axis exists, and restricting controls to one head's own nine cells returns the
**1/9 = 0.111 floor**, which is above α at every attainable effect size.

## L.3 🔴 Two results are PERMANENTLY floor-limited, and for the same reason

Both are **top of their control family** and both families are **too small to certify that**:

| result | outcome | floor | certifiable at α = 0.05? | the family that would have fixed it |
|---|---|---|---|---|
| necessity, basket | rank **1 of 9** | 0.1111 | **no** | PR-CSI-003-A — **BLOCKED by its own VOID 6, never launched** |
| sufficiency, basket at **L20** | rank **1 of 11** | 0.0909 | **no** | PR-CSI-004 — **frozen, never run, and NO LONGER RUNNABLE** |

PR-CSI-004 required all 53 arms to run one `score_behavior.py` blob; the 10 reused controls ran
`e94258bd…`, the file is now `9562bdf9…`, and its 36 new arms never began (AM-46). **So "rank 1 of
11, floor-limited" on the L20 cell is a permanent statement, not a provisional one**, and the same
holds for necessity at rank 1 of 9. ⚠ **Neither is a negative result.** Each is the *best attainable*
outcome in a family whose floor sits above α — the distinction §4 draws between a FAIL and a
structural CANNOT ANSWER, here arriving through family size rather than through K.

The escape in both cases is a fresh freeze that re-runs **every** arm on one current blob. Reusing
archived arms is what made these unfixable in the first place.

## L.4 Every head was chosen because it was live

No family draws heads at random. PR-CSI-018's six were chosen because they were live **on button**;
PR-CSI-020's eight because they were live **on basket**. The screen's per-cell prediction is
therefore tested **only where there was something to find**, and nothing here licenses *"the screen
is a validated cell selector in general"*. ⚠ And the **1.5 admission gate is frozen across three
published families**, so it cannot be relaxed after the fact — which matters because the best
unadmitted basket head sits at **1.400**, close enough that a reader may wonder, and far enough that
moving the bar would reinterpret three published results at once.

## L.5 The held-out axes differ between the two positive results, and conflating them overstates both

**§2 (D39) is held out on CODEWORD. §3 (D40) is held out on SPLIT only.** They are not two
independent confirmations of the same thing, and **three of D40's eight heads were disclosed before
the read as a replication** of predictions already tested in §2 — not an independent draw.

## L.6 Two axes are closed by contamination, not by design

**TEST** is never touched here, and it is also **not available**: read to completion on 2026-09-08
and selection-contaminated on knobs every family inherits. **The SOURCE question** — whether the
demonstrations supply the installed content — has **no confirmatory instrument**: the mass
measurement licenses a **refutation reading only**, and a null control there is *confounded*, to be
reported as CANNOT ANSWER and never as support.

## L.7 What reproducibility does and does not buy

§6 shows both published reads replay from their landed artefacts, including under a later reader
refactor. **That tests the reader, not the arm** — it re-reads the same arms, strengthens no p, and
a deterministic replay of a wrong arm is still wrong. ⚠ Relatedly, the **bootstrap parameters were
command-line defaults frozen retroactively** (§M.4), so they are a convention that became a
commitment rather than a commitment from the start.
