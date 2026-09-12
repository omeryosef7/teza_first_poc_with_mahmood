# DCS continuation — REVIEW-8, OUTPUT + SCIENTIFIC dimensions

**Scope.** `CONT-ENTRY 129`–`137` of
`external_md/DCS_BOMBNESS_REPRESENTATION_TO_CAUSAL_ASR_CONTINUATION_20260910.md` (entry 137 appeared
during the review and is treated as part of the record); `reports/DCS_CONT_CLAIM_TABLE.md` as a
standalone deliverable; `configs/dcs_cont_dr075_dose8_refusal.json`;
`reports/DCS_CONT_DR075_RESULT.json`; `reports/DCS_CONT_EXACT_TESTS.json`. Named targets: **A16**
(entry 130), **DR-075** (entry 136), the claim table, cross-entry coherence, narrative honesty.

**Discipline.** Read-only. No SLURM job, no GPU, no judge, no API. No FROZEN config, lexicon or
artifact edited. Nothing committed. All arithmetic below is re-derived from numbers already in the
record; where a number could not be verified against an artifact, it is marked **UNVERIFIABLE**.

**`REVIEW-7/OUTPUT_SCIENTIFIC` was read first.** Its findings are not repeated except where entries
130–136 use a quantity REVIEW-7 had already qualified, or where a REVIEW-7 item was accepted in the
record and then left out of the deliverable.

**Severity.** CRITICAL = a published claim is unsupported or contradicted by the record itself;
HIGH = a claim needs a qualifier it does not have; MEDIUM = bookkeeping/provenance.

---

# SUMMARY OF FINDINGS

| # | finding | class | sev |
|---|---|---|---|
| **R8-01** | **A16's second half ("not capability") asserts the negative that the same claim table forbids under `C-CONT-032`.** Entry 050 computed the prediction (−0.0301) and found it *on* the measured CI bound; entry 121's matched-hardware CI `[−0.0597, +0.0448]` against a ctrl base of 0.0522 cannot exclude the knockout **abolishing content-true entirely**. A16 converts that undecidability into a positive claim. | **OVERREACH** | CRITICAL |
| **R8-02** | **The dose leg's "dissociation" is a units artifact.** At dose 4 *both* endpoints sit at their phase-typical full-attack values (refusal 0.1111 vs ctrl 0.1119; content-true 0.0389 vs 0.0343/0.0522). Content-true:refusal ratio 0.35 at dose 4 vs 0.31–0.47 in the reference arms. Expressed in each endpoint's own units, **nothing dissociates**. | **OVERREACH** | CRITICAL |
| **R8-03** | **The ρ = +0.2376 is not a dose-response test.** If dose 0 is exactly 0.0000 per domain — which entry 130 bolds — then "gain" = "level at dose 4" identically, and ρ is algebraically the **cross-sectional** correlation at dose 4. The stronger entry 130's zero-anchor rhetoric, the more its linking test collapses into an observational correlation. | **UNSUPPORTED** | CRITICAL |
| **R8-04** | **A16's dose leg is 20 refusal rows and 7 content-true rows out of 180; DR-075's verdict is a net of 5 rows.** Derived exactly from 2 rows/domain × 90 domains. Gross churn: refusal 15 rows moved, content-true 12. Never stated anywhere in the record or the table. | **MISSING CAVEAT** | CRITICAL |
| **R8-05** | **ρ = 0.2376 sits below the design's own MDE**, by the power calculation entry 124 used four entries earlier to excuse a null (ρ≈0.34 at n=67; ≈0.29 at n=90; α=0.05 threshold 0.208). Entry 124 called ρ=0.176 "not supported"; entry 129 calls ρ=0.238 "supported". The two are statistically indistinguishable. | **OVERREACH** | CRITICAL |
| **R8-06** | **A16 cites as corroboration a quantity entry 134 declares inadmissible.** The "+0.2548 on the secondary … agrees both ways" is an all-slots **dose contrast**; entry 134 makes `Scope.for_dose_contrast()` **raise** on exactly that. The claim table still carries it as support. Also: the two scopes share `slot0`, so agreement is arithmetic, not replication. | **OVERREACH** | CRITICAL |
| **R8-07** | **A16 is not labelled button-only, and basket is a counterexample, not a floor.** Basket: installation +0.4578, refusal +0.0056 (**1 row of 180**), ρ +0.0592 / −0.0547. Entry 137 concedes even DR-075's *premise* (saturation) is button-only. Every other A-row states codeword coverage in its STATUS; A16 does not. | **MISSING CAVEAT** | CRITICAL |
| **R8-08** | **"Refusal" is a 16-term substring at char 0 on 23–148-char stubs; under the only independent refusal instrument in the data the effect goes bidirectional and basket's sign reverses** (rubric scores 404/670 button-`ko` rows as refusals against the field's 27). A15's row says this; **A16's row does not**, though A16's entire refusal leg is `kw_refusal`. "The safety response" is an upgrade of "refusal boilerplate at position 0". | **MISSING CAVEAT** | HIGH |
| **R8-09** | **A simpler single-mechanism account fits every datum and is nowhere tested against.** "Installation gates whether the request is *interpreted* as a bomb request; refusal and bomb-content are both downstream" explains A1, A2, A2b, A4, A15 and A16 with one mechanism instead of two — and is directly corroborated by A2b (+8.5 pp literal basket-weaving) and A15 ("what replaces the refusal is mostly not an attack"). **This is the single strongest reason to doubt the headline.** | **UNSUPPORTED** | CRITICAL |
| **R8-10** | **DR-075's falsification region lies outside the historical range of its own instrument.** Falsification needed refusal > 0.1666; every button refusal rate in the phase is 0.0403–0.1195. The threshold is **4.8×** the config's own prediction, and only a *strictly linear* demonstration-counting alternative is excluded — √2-scaling (0.157) or log-scaling pass as SUPPORTED. | **OVERREACH** (of the *inference*; the verdict itself is honest bookkeeping) | HIGH |
| **R8-11** | **Asymmetric evidential standards between the two dose steps.** At 0→4 a raw percentage-point gap with no CI on the difference is accepted as evidence *for* the dissociation; at 4→8 the relative gap (+57 % vs +25 %) that runs *against* it is set aside because the CIs include zero. Same design, same n, same endpoints. Entry 136's "not established" is technically correct but is applied in one direction only. | **MISSING CAVEAT** (motivated asymmetry, not a wrong number) | HIGH |
| **R8-12** | **A5 contradicts A16 and neither row mentions the other.** A5: installation predicts corrected ASR *within domain*, slope +0.140, **p = 0.0006** — a better-powered installation→**capability** link than the installation→refusal link (p = 0.023) A16 rests on. A5 also carries **no caveat** that its endpoint is the pre-CR-002 corrected ASR that Section B forbids quoting as an estimate. | **OVERREACH / MISSING CAVEAT** | CRITICAL |
| **R8-13** | **The two legs of A16 disagree quantitatively by 2×** and the record presents them as one mechanism: dose leg 0.169 refusal per unit installation, knockout leg 0.333. The between-prompt/within-prompt combination also confounds "installation" with "harm-laden demonstration text present in context at all" — the dose-0 anchor cannot separate them. | **UNSUPPORTED** | HIGH |
| **R8-14** | **The dose-0 anchor is near-tautological and is presented as a three-way convergence.** With no demonstrations the prompt is a benign question about a button. Zero installation, zero refusal and zero bomb content is what *every* account predicts, including ones in which refusal and capability share one mechanism. It carries no discriminating information. | **OVERREACH** | HIGH |
| **R8-15** | **"Exactly 0.0000" is not in the record.** `CONT-ENTRY 100`'s ladder prints dose-0 mean/median/sd as **"~0"**, and the claim table's own A14 row says "dose 0 ≈ 0". Entry 130 bolds *"All three quantities start at **exactly** zero"*. | **UNSUPPORTED** (UNVERIFIABLE) | HIGH |
| **R8-16** | **Three unreconciled values for one quantity sit in the same claim table.** Button dose-4 installation on the `slot0` primary: **0.6728** (A14 / entry 100 / entry 129's linking table, 90 domains), **0.6587** (A16 / entries 130, 133, 90 domains), **0.6589** (DR-075 config, 116 domains). Saturation fraction: A14 **9.4 %**, A16 **10.3 %**. Entry 131 presents 0.6589 vs 0.6587 as *"a useful check on the readout"* while the 0.014 disagreement with the figure published two rows above in the same table goes unmentioned. | **MISSING CAVEAT** | HIGH |
| **R8-17** | **A16's headline correlation has no committed artifact and no script.** `git show --stat 5ecd8cf2` (entry 129) adds only the MD and `scripts/dcs_cont_scope.py`; `eb229f48` (entry 130) adds only the MD and one table line. The four ρ values exist as prose. This is the phase's own recurring defect shape (`C-CONT-036`, `C-CONT-039`). | **UNSUPPORTED** (UNVERIFIABLE) | HIGH |
| **R8-18** | **`DCS_CONT_DR075_RESULT.json` under-records the entry.** It carries refusal only — the content-true series (0.0389→0.0611, CI), the raw-judge series (0.3833→0.3871) and the ↑/↓/= domain counts that entry 136 reports are absent from the artifact. | **MISSING CAVEAT** | MEDIUM |
| **R8-19** | **A2's row mixes endpoints within one cell** — statistic column quotes the frozen-lexicon primary (+0.0030 `[−0.030,+0.036]`) while the status text argues from CR-002's 0.0343 base. The CR-002 primary (+0.0090 `[−0.0090,+0.0269]`) is not in the row at all. Nor is the fact that the **best-controlled** measurement is the **least** powered (matched-hardware half-width 0.052 ≈ the entire ctrl base rate). | **MISSING CAVEAT** | HIGH |
| **R8-20** | **A3 is labelled EXPLORATORY; A16 — the strengthened version of the same inference — is not.** A3 = A1 ∧ A2 carries "EXPLORATORY", "qualitatively ONLY" and "WITHDRAWN TWICE". A16 is A1 ∧ A2 ∧ a dose correlation and carries "MEASURED, `slot0` PRIMARY". The stronger claim wears the weaker label. | **OVERREACH** | CRITICAL |
| **R8-21** | **A13's claim text uses the exact framing Section B forbids.** A-row: *"§15's **matched** reference … beating the **matched** context-only prototype"*. B-row: *"the §15 result as a **matched**-reference finding — a mismatched partner scores higher; the matching does no work"*. The same deliverable states and prohibits the same sentence. | **OVERREACH** | HIGH |
| **R8-22** | **A15's "STRUCTURE REPLICATED ON TWO CODEWORDS" rests on basket's `1 ⊂ 8`** — a one-element subset relation, trivially satisfiable. And entry 134's explicitly-named open item (*"A15's Wilson intervals are row-level where the declared unit is the domain … named so it is not quietly dropped"*) **is absent from the table**. | **OVERREACH / MISSING CAVEAT** | HIGH |
| **R8-23** | **Claim-table front matter is four reviews stale** — *"Revised 2026-09-12 after REVIEW-2 and REVIEW-3 (`C-CONT-038`…`C-CONT-068`)"* on a table that now carries `C-CONT-091`, A15, A16 and DR-075. The preamble's *"**One** preregistered confirmation has happened: `DR-072`"* is also no longer the whole story (DR-073a, DR-074, DR-075). | **MISSING CAVEAT** | MEDIUM |
| **R8-24** | DR-075's process discipline — freezing before submission, pinning the GPU, identifying the comparator population *before* reading, disclosing the incidental TEST touch, the `OPENAI_API_KEY` guard — is **exemplary and better than the field norm**. Entry 136's three travelling caveats are unusually candid. Entry 133's "the cause is now unexplained rather than wrongly explained" is the right call. Entry 134's `NotImplementedError` branch is good engineering. Entry 137 pre-registers the basket ladder before looking. | **ACCEPTABLE** | — |

**Net.** The *process* around A16 is better than the *claim*. Four of the five loads A16 carries —
the dose-0 anchor, the dose-4 "dissociation", the ρ, and the capability null — are each individually
weaker than the record states, and they are weak in **the same direction**, which is the signature of
a conclusion being assembled rather than found. The headline as written ("installation gates REFUSAL,
not capability") should be withdrawn to something like: *"on button, demonstrations that install the
remap also produce short refusal stubs; whether they also change the rate of genuine bomb content is
below this design's resolution in every arm that has been run."*

---

# PART 1 — A16 (CONT-ENTRY 130)

## 1.1 CRITICAL · R8-01 — "not capability" is the negative the table itself forbids

A16's second half is a **negative** claim. Its entire support is A2, plus entry 121's matched-hardware
content-true null. The claim table already records, twice, that this null cannot bear that weight:

> **Section E:** *"**Power on A2/A3 in content-true units** — **worse now that the endpoint exists**:
> against CR-002's button base rate on the ASR arms of **0.0343**, the primary's CI half-width (~0.029)
> is ~85 % of the entire genuine attack rate."*

> **Section B:** *"'installation causally drives ASR' | A3 is **qualitative only**; the quantitative
> version was **downgraded** (`C-CONT-032`) — the within-domain prediction (−0.030) sits *on* the
> measured CI bound."*

`C-CONT-032` is the finding that the experiment **cannot distinguish** "installation drives ASR at the
observed within-domain rate" from "it does not". Entry 050 said so in terms:

> *"The experiment is **underpowered to distinguish** 'installation causally drives ASR at the observed
> within-domain rate' from 'it does not' — the predicted effect (−0.030) and the MDE (0.053) are the
> same order, and the CI contains both the prediction and zero."*

A16 takes that same undecidable comparison and states one side of it as a result. Section B forbids
*"installation causally drives ASR"*; A16 asserts *"installation does not gate capability"*. **Both
are ruled out by the same null.** A deliverable cannot forbid one direction and headline the other.

**And the newest, cleanest measurement is the weakest of all.** Entry 121, matched hardware, one judge
manifest, `slot0` primary:

| endpoint | ko | ctrl | Δ | 95 % CI |
|---|---|---|---|---|
| CR-002 content-true | 0.0448 | 0.0522 | −0.0075 | **[−0.0597, +0.0448]** |

Against a control base rate of **0.0522**, that interval spans **−114 % to +86 %** in relative terms.
It is consistent with the knockout **abolishing content-true attacks entirely**. Meanwhile the refusal
effect on the same rows is −0.0716/0.1119 = **−64 % relative** — a value that sits comfortably *inside*
the content-true interval (a −64 % content-true effect is −0.0334; the CI runs to −0.0597).

⇒ **On the only hardware-clean, single-judge-manifest measurement the phase owns, there is no evidence
of a differential effect on the two endpoints.** The proportional effect measured on refusal is not
excluded on content-true. A16's second half is not merely underpowered; the specific alternative it
denies is *inside the interval*.

## 1.2 CRITICAL · R8-02 — the dose leg's dissociation is a units artifact

Entry 130's argument is: *"Adding four demonstrations raises installation by +0.659 and refusal by
+0.111, while content-true attack success reaches only 0.039."* Refusal moved 0.111; capability moved
0.039; therefore refusal is gated and capability is not.

That comparison is only meaningful if the two endpoints have comparable scales. They do not, and the
record already contains the reference values:

| endpoint | dose-4 arm | `ctrl` arm (full attack) | `base` arm | corpus (114 runs) |
|---|---|---|---|---|
| refusal (`kw_refusal`) | **0.1111** | **0.1119** | 0.1149 | — |
| content-true (CR-002) | **0.0389** | **0.0522** (`slot0`) / 0.0343 (ASR arms) | — | 0.0250 |

**At dose 4, both endpoints are already at their phase-typical full-attack values.** Refusal 0.1111
against a control of 0.1119 — a match to three decimals. Content-true 0.0389 against 0.0343–0.0522.
The content-true:refusal ratio is **0.350** at dose 4, against **0.307** (ASR-arm base rates) and
**0.467** (matched-hardware `slot0` ctrl). Four demonstrations do not move one endpoint and leave the
other at the floor: **they move both endpoints from zero to their normal operating level, in their
normal proportion.**

The appearance of a dissociation is produced entirely by comparing 0.111 to 0.039 in raw percentage
points when the two measures have base rates differing by ~3×. This is the floor-effect concern in its
sharpest form, and the answer is worse than "possibly a floor effect": **it is not a floor at all.**
Content-true at dose 4 (0.0389) is *above* the corpus-wide button content-true rate (0.0250) and ~75 %
of the highest value the endpoint takes anywhere in the phase (0.0522). Calling 0.039 "near the floor"
while calling 0.111 "moved" is a choice of scale, not a measurement.

Entry 130's own summary sentence makes the error explicit:

> *"at dose 4 it refuses 11 % of the time and produces genuine content 4 % of the time, and removing
> the remap moves the first number and not the second."*

11 % *is* this model's refusal rate on this attack. 4 % *is* this model's content-true rate on this
attack. Neither is anomalous; the sentence describes the model's ordinary behaviour and reads it as a
dissociation.

## 1.3 CRITICAL · R8-03 — the ρ is a cross-sectional correlation, not a dose-response link

Entry 129/130 present ρ as a *dose* result: *"the domains where demonstrations install the most are
the domains where refusal rises the most"*, computed as per-domain `installation gain (0→4)` against
`refusal gain (0→4)`.

But entry 130 also bolds, of the same 90 domains:

> **"All three quantities start at exactly zero on both codewords."**

If dose-0 installation and dose-0 refusal are zero **in every domain**, then for every domain
`gain = level at dose 4` identically. The Spearman correlation of the gains is then, term for term,
the Spearman correlation of the **dose-4 levels**. The dose-0 arm contributes **zero variance** and
therefore zero information. What entry 129 calls *"the linking test done properly"* is an
**observational cross-sectional correlation within the dose-4 arm** — structurally the same kind of
object as A5, not a manipulation-linked test.

**This is an internal contradiction, and it is unavoidable in one direction or the other:**
* if dose 0 is exactly zero per domain, the ρ is not a dose-response result and entry 130's framing
  ("Across the dose ladder…", "a dose manipulation") is wrong; or
* if dose 0 is *not* exactly zero per domain, entry 130's bolded "exactly zero" is wrong (see R8-15,
  where `CONT-ENTRY 100` prints "~0").

Both cannot hold. The record does not contain the per-domain dose-0 values, so this cannot be settled
from the deliverables (**UNVERIFIABLE** — the dose-0 per-domain vector should be published).

## 1.4 CRITICAL · R8-04 — the event counts, which the record never states

`slot0` carries 232 rows / 116 domains (entry 135) = **2 rows per domain**. On the 90-domain train+val
population that is **180 rows per dose**. Every reported rate is therefore an integer over 180:

| quantity | rate | **rows** |
|---|---|---|
| refusal, dose 4 | 0.1111 | **20 / 180** |
| refusal, dose 8 | 0.1389 | **25 / 180** |
| content-true, dose 4 | 0.0389 | **7 / 180** |
| content-true, dose 8 | 0.0611 | **11 / 180** |
| basket refusal, dose 4 | 0.0056 | **1 / 180** |
| basket content-true, dose 4 | 0.0056 | **1 / 180** |

(Each product is an integer to within rounding — 19.998, 25.002, 7.002, 10.998, 1.008 — which
confirms the 2-rows-per-domain reconstruction.)

The ↑/↓/= counts in entry 136 close the arithmetic exactly: refusal 10↑/5↓ at half a domain-unit each
gives Δ = 2.5/90 = **+0.02778** ✓; content-true 8↑ with 2 domains −0.5 and 1 domain −1.0 gives
Δ = 2.0/90 = **+0.02222** ✓.

**So, stated in events:**
* A16's dose leg is **20 refusal rows and 7 content-true rows** out of 180.
* **DR-075's entire verdict is a net of 5 rows** (10 rows became refusals, 5 stopped).
* The "content-true rose proportionally more" observation is **a net of 4 rows** (8 on, 4 off).
* Gross churn: **15 rows** changed refusal status, **12 rows** changed content-true status. At this
  resolution the two endpoints are behaving identically.
* Per-domain refusal can only take the values **{0, 0.5, 1}**, with roughly 70–80 of 90 domains at
  exactly 0. The Spearman ρ is therefore computed against a three-valued variable that is tied at the
  bottom in ~80 % of units. **Flagged for the STATISTICAL reviewer**: asymptotic Spearman p-values are
  not reliable under that tie structure, and a handful of domains determine the coefficient.

None of these counts appears in entry 129, 130, 131, 135, 136 or the claim table. They change a
reader's impression of A16 more than any confidence interval in the record does.

## 1.5 CRITICAL · R8-05 — the ρ is below the design's own MDE, and the power argument is used one way

`CONT-ENTRY 124`, four entries before A16:

> *"At n = 67, the minimum detectable correlation at 80 % power is **ρ ≈ 0.34**. The observed 0.176 is
> **half the MDE** … A linking test with useful power at ρ ≈ 0.18 needs roughly **240 domains**."*

Re-deriving at n = 90 (Fisher-z): α = 0.05 significance threshold **ρ = 0.208**; 80 %-power MDE
**ρ = 0.292**; power at a true ρ of 0.2376 is **≈ 0.62**.

⇒ **ρ = 0.2376 is below this design's own 80 %-power MDE and only 0.030 above the bare significance
threshold.** It is exactly the regime entry 124 said the design cannot resolve. At 62 % power,
conditioning on p < 0.05 biases the point estimate upward; the true value is plausibly ~0.15 — i.e.
entry 124's "not supported" value.

**And the two results are statistically indistinguishable.** Entry 124's ρ = 0.176 had CI
[−0.0513, +0.4048], which **contains 0.2376**. The record calls one "not supported" and the other
"supported"; the difference between them is n = 67 vs n = 90 and where the threshold happens to fall.
The power argument is deployed to excuse the null and withheld from the positive.

**Multiplicity.** Entry 129 is candid that four tests ran and offers Bonferroni over two
(0.023 → 0.046, *"which only just survives"*). That is defensible *if* the secondary scope is excluded
from the evidence. It is not: entry 130 and the claim table both use the secondary's +0.2548 as a
positive evidential point. **You cannot count a test as corroboration and exclude it from the
correction.** Over four tests, 0.023 → **0.092**.

## 1.6 CRITICAL · R8-06 — "agrees both ways" cites a quantity the record later rules inadmissible

Entry 130, and the A16 row verbatim:

> *"and the same in sign and size on the secondary (+0.2548) — the first scope-sensitive quantity in
> this phase that agrees both ways."*

Entry **134**, four entries later:

> *"for **any** dose contrast on this bank, `slot0` is the only admissible analysis, and 'all slots'
> is **not a defensible secondary** — it is comparing 1 slot against 5 and calling the difference a
> dose effect."*
> `Scope.for_dose_contrast()` *"**raises** if `ALL_SLOTS` is passed for a dose contrast"*.

ρ = +0.2548 is an all-slots dose contrast. By entry 134's own rule it could not be computed today. It
is still in the claim table, as corroboration, in a table whose last edit (commit `0ddec947`, entry
136) post-dates entry 134.

**Separately, the corroboration was never independent.** The dose-0 arm is `slot0` only; the dose-4
arm is `{slot0, 4, 8, 12, 16}`. The two scopes share the entire dose-0 arm and 1/5 of the dose-4 arm.
Two estimates built on overlapping rows agreeing in sign and magnitude is arithmetic, not replication.
Presenting it as *"the first scope-sensitive quantity in this phase that agrees both ways"* — i.e. as a
novel virtue — inverts what it is.

## 1.7 CRITICAL · R8-07 — A16 is button-only, and basket is a counterexample

Entry 130's own table:

| codeword | dose | installation | refusal | content-true |
|---|---|---|---|---|
| basket | 0 | 0.0000 | 0.0000 | 0.0000 |
| basket | 4 | **0.4578** | **0.0056** | 0.0056 |

Four demonstrations install the remap on basket to 0.458 — two thirds of button's level, a large,
unambiguous, 90/90-domain effect — and refusal moves by **one row in 180**. ρ = +0.0592 (p = 0.699) on
the primary and **−0.0547** on the secondary.

Entry 129 defends this as *"a floor, not a contradiction, but I cannot prove that distinction from
these data."* That defence is circular. The A16 claim is that refusal **tracks** installation. Basket
supplies a large installation change with no refusal change. That is the definition of a
counterexample to tracking; calling it a floor is asserting the conclusion to exempt the data that
contradicts it. A floor argument would need an independent reason refusal *cannot* rise on basket —
and none is offered; basket refuses 8 times in 670 rows on the ASR arms, so the instrument fires there.

The weaker claim that survives basket is **necessity** ("no installation ⇒ no refusal"), not the
tracking claim entry 130 makes (*"the safety response tracks it closely, up and down"*).

**The table does not say any of this.** A16's status reads "MEASURED, `slot0` PRIMARY". Every other
A-row states codeword coverage in its status — A1/A2/A12/A13 "REPLICATED CROSS-CODEWORD", A15
"STRUCTURE REPLICATED ON TWO CODEWORDS", A3 "TWO-CODEWORD". A16 says nothing, and the word "button"
appears once, parenthetically, mid-cell. A reader scanning statuses will conclude A16 has the same
cross-codeword standing as A1.

**Entry 137 makes this worse, not better.** Written after the table's last edit, it concedes that the
*saturation premise DR-075 rests on* has been measured on button only, and pre-registers that if
basket does not saturate then DR-075's conclusion *"is a statement about button and must be relabelled
as such in the claim table."* That relabelling is already owed for A16 as a whole, independent of how
job 886483 comes out.

## 1.8 HIGH · R8-08 — the refusal construct, and what A16 upgrades it to

From REVIEW-7, verified against this record: `kw_refusal` is a 16-term case-insensitive substring
matcher; the marker sits at **character 0 in 111/111** positive rows; those completions are **23–148
characters**; StrongREJECT is **0.0 in 111/111**; the length distribution is perfectly bimodal
(refusals ≤ 148 chars, everything else ≥ 530). It measures "is this a one-line refusal stub", exactly
and without error.

The only refusal signal in the data that is **not** a function of the opening string is the judge's own
rubric subscore. Under it: button **119 de-refusals against 114 reversals**; basket **43 against 64 —
the sign reverses**. The rubric scores **404/670** button-`ko` rows as refusals against the field's 27.

⇒ The knockout's refusal effect, and therefore A16's refusal leg, **exists on one construct and
reverses on the other available one.** A15's row carries this (*"one-directionality is near-definitional
under the `kw_refusal` substring detector and goes bidirectional under the judge's own rubric
refusal"*). **A16's row carries nothing**, although A16's entire refusal leg — the dose-4 0.1111,
DR-075's 0.1389, the −0.0716 knockout effect, and the ρ — is `kw_refusal`.

And entry 130 does not write "refusal stubs". It writes:

> *"installation gates the model's **refusal behaviour**"* … *"the **safety response** tracks it
> closely"*.

That is a construct upgrade from a 16-term opening-string matcher to "the model's safety response", in
a phase where the other refusal instrument disagrees.

## 1.9 HIGH · R8-13 — combining a between-prompt and a within-prompt manipulation

The parent brief asks whether combining the dose (between-prompt) and knockout (within-prompt) legs
smuggles in an assumption. It does, in two ways.

**(a) The implied slopes disagree by 2×.**

| leg | Δrefusal | Δinstallation | refusal per unit installation |
|---|---|---|---|
| dose 0→4 | +0.1111 | +0.6587 | **0.169** |
| knockout | −0.0716 | −0.2150 | **0.333** |

If a single monotone map from installation to refusal governed both, they would agree. Read the other
way: the knockout leaves installation at ≈ 0.44, which on the dose curve corresponds to a refusal of
≈ 0.074 — a drop of 0.037, **half** the measured 0.0716. Entry 130 presents the two as "the same pair
in the same direction"; that is true of the **signs** only, and the entry does not say so.

**(b) The dose contrast confounds installation with the presence of demonstrations at all.** Dose-0
prompts carry no demonstration block: no harm vocabulary, different length, different context. The
knockout keeps the demonstrations in context and cuts row access. So they are not two handles on one
latent variable. Notably, the knockout arm (demonstrations present, installation reduced ~31 %) refuses
at **0.0403**, while dose 0 (no demonstrations, no installation) refuses at **0.0000** — consistent
with a dose response, and equally consistent with harm text in context contributing to refusal
independently of the remap. **The record contains no arm that separates them**, and A16's "all three
start at zero" anchor is precisely where that confound lives.

## 1.10 HIGH · R8-14 / R8-15 — the zero anchor

**R8-14.** With no demonstrations, the prompt is a benign question about a button or a basket. Zero
installation, zero refusal and zero bomb content is what *every* hypothesis predicts — including the
single-mechanism account of R8-09 that A16 is competing against. A joint zero carries no information
about the *relative* dependence of the three endpoints on installation; it is presented in entry 130
as a three-way convergence (*"All three quantities start at exactly zero"*, bolded, followed by
*"the last of these verified by direct inspection, 0/226 completions"*). The inspection verifies the
zero; nothing verifies that the zero discriminates.

**R8-15.** `CONT-ENTRY 100`'s ladder, on the same `slot0` primary and the same 90 domains, prints
dose 0 as **"~0"** for mean, median *and* sd, and the claim table's A14 row says **"dose 0 ≈ 0"**.
Entry 130 upgrades this to **"exactly zero"**, in bold, and A16 tabulates **0.0000**. The actual
dose-0 value at more than one significant figure does not appear anywhere in the record
(**UNVERIFIABLE**). Given R8-03 depends on whether it is exactly zero *per domain*, this needs
publishing rather than asserting.

## 1.11 CRITICAL · R8-09 — the account the record never tests against

Every observation A16 assembles is also predicted by a **single-mechanism** account:

> *Installation determines whether the model interprets the request as being about a bomb. Given that
> interpretation, it refuses some of the time (~11 %) and supplies genuine content some of the time
> (~4 %). Remove the interpretation and it answers about buttons: no refusal, and no bomb content.*

Under that account there is **no dissociation between a refusal mechanism and a capability
mechanism** — both are downstream of one interpretive step. And it is the account the rest of the
record actively supports:

* **A2b**: the cut rewrites 669/670 completions, **+8.5 pp [+4.3, +12.8] literal basket-weaving**;
* **A15**: *"what replaces them is mostly not an attack"* — the de-refused rows are literal answers;
* **REVIEW-7**: the judge's rubric scores 404/670 `ko` rows as refusing *the harmful goal*, because a
  literal answer satisfies that rubric — i.e. the knockout makes the model **literal**, not compliant;
* **entry 122** built exactly this chain and named it.

The single-mechanism account predicts content-true should fall under the knockout **in proportion**
(−64 %, i.e. −0.0334 against a 0.0522 base). R8-01 shows the matched-hardware CI `[−0.0597, +0.0448]`
cannot reject that. **The record contains no measurement that discriminates the two accounts**, and
A16 selects the two-mechanism one, which is the more surprising and more quotable of the pair.

That is the single strongest reason to doubt the headline: **a strictly simpler explanation fits every
number, is corroborated by the text-level evidence the phase collected, and has never been tested
against.**

---

# PART 2 — DR-075 (CONT-ENTRY 131, 135, 136)

## 2.1 Was the rule set up so it could realistically only pass? — HIGH · R8-10

**Largely, yes — though not by intent, and the entry is honest about the consequence.**

| | value |
|---|---|
| comparator (dose 4, train+val) | 0.1111 |
| config's own prediction | **0.1226** (Δ +0.0115) |
| SUPPORTED if | Δ < +0.0555 |
| FALSIFIED if | refusal > **0.1666** |
| measured | 0.1389 (Δ +0.0278) |

**(a) The falsification region lies outside the historical range of the instrument.** Every button
refusal rate recorded anywhere in this phase: `ko` 0.0403, dose-4 0.1111, ctrl 0.1119, `base` 0.1149,
all-domains dose-4 0.1195. The maximum ever observed is **0.1195**. Falsification required **0.1666** —
**39 % above the highest value the endpoint has ever taken**, on a model whose refusal rate on this
attack has been stable to three decimals across arms, hardware and judge manifests. The prior
probability of falsification was low **by construction of the threshold**, not by the strength of the
hypothesis.

**(b) The threshold is 4.8× the config's own prediction.** The config predicts +0.0115 and accepts
anything below +0.0555. A result missing the prediction by a factor of 4.8 still reads SUPPORTED. The
measured +0.0278 is a 2.4× miss and passes comfortably.

**(c) Only the strictly linear alternative is excluded.** "Refusal counts demonstrations" is
operationalised implicitly as *doubling the demonstrations doubles the refusal gain* (Δ = +0.1111,
which is 2.8 SE inside the falsification region — genuinely well powered against **that**). But the
natural alternatives for a saturating system are sublinear: √2-scaling gives 0.1111 × 1.414 = **0.157**
(SUPPORTED), log-scaling gives less (SUPPORTED). The only refusal-counting model the test can kill is
the one nobody would have proposed for a system whose *installation* is already known to saturate.

**(d) The design's resolution.** SE(Δ) ≈ 0.0199 from the reported CI. The distance between the
prediction (+0.0115) and the threshold (+0.0555) is **2.2 SE**. The design was never able to separate
"A16 exactly right" from "A16 wrong by a factor of 5" — and the measured value landed exactly in that
gap.

**Verdict on the verdict.** As *bookkeeping under a frozen rule*, "SUPPORTED" is correct and calling it
anything else would be worse. Entry 136 does not oversell it and explicitly records it *"as a passed
falsification test rather than as positive confirmation, because that is what it is."* **That sentence
is the right standard.** The problem is downstream: the claim table renders it as

> *"🆕 `DR-075` SUPPORTED: dose 4→8 raises installation only 10.3 % and refusal only **+0.0278**
> (vs +0.1111 for the first four demos) — **refusal is not a demonstration counter**."*

*"Refusal is not a demonstration counter"* is a general negative licensed only against the linear
version. It should read "refusal does not rise **linearly** with demonstration count" — or, with the
CI, "the second four demonstrations did not produce another large refusal increment; whether they
produced a small one is unresolved."

## 2.2 Does the content-true result falsify A16's second half? — HIGH · R8-11

**It does not falsify it; but "not established" is being applied asymmetrically, and that is the
finding.**

The numbers (entry 136): refusal 0.1111 → 0.1389, **+25 %**; content-true 0.0389 → 0.0611, **+57 %**;
domains ↑/↓/= 10/5/75 and 8/3/79; in events, 5 net rows and 4 net rows (R8-04).

Strictly, entry 136 is right: both CIs include zero, the counts are tiny, and 4 net rows cannot
establish anything. So "not established" is the correct *statistical* call, and the entry deserves
credit for refusing to file it under caveats.

**The asymmetry is the problem.** The *same* design, the *same* n, the *same* two endpoints:

* at **0→4**, the raw percentage-point gap (0.1111 vs 0.0389) is taken as evidence **for** the
  dissociation — with no CI on the *difference* between the endpoints, no relative-scale comparison,
  and no event counts;
* at **4→8**, the relative gap (+57 % vs +25 %) that runs **against** the dissociation is set aside
  **because** the CIs include zero and the counts are tiny.

The 0→4 evidence is not stronger than the 4→8 evidence — it is 20 and 7 rows against 5 and 4 rows, and
neither has an interval on the between-endpoint contrast. A consistent standard either admits both or
neither. Applied consistently, **A16's dose leg fails the standard A16's own forward test is judged
by.**

Second, the 4→8 step is the **only** place in the entire phase where the two endpoints are put on the
same relative scale, and there the result goes the wrong way for A16. That deserves more than
"awkward"; it is the only directly comparable observation available.

Third, the domain-level movement patterns (10/5/75 vs 8/3/79) are **indistinguishable**. Entry 136
reports both rows and does not remark on it. At this resolution refusal and content-true behave
identically — which is R8-09's single-mechanism prediction.

## 2.3 What DR-075 does well — ACCEPTABLE · R8-24

Recorded so the criticisms above are read in proportion: the config was frozen and sha-pinned before
submission and re-hashed at read time; the GPU was pinned with a cited reason (`C-CONT-075`); the
comparator's **population** was identified *before* the result was read, preventing exactly the
`DR-074` failure; the incidental TEST touch was disclosed unprompted rather than buried; the
`OPENAI_API_KEY` guard is named as the thing that prevented a fabricated clean number (the
`C-CONT-036` shape); and the judge model was pinned to the comparator's manifest. The three travelling
caveats in entry 136 are more candid than most published work. **The process is not the problem.**

## 2.4 MEDIUM · R8-18 — the artifact under-records the entry

`reports/DCS_CONT_DR075_RESULT.json` carries `refusal_dose4/8`, `delta`, `ci95`, `verdict`,
`predicted`. It does **not** carry the content-true series, its CI, the raw-judge series, the ↑/↓/=
domain counts, the row counts, or the `judge_status` integrity checks — all of which entry 136
reports. Anyone re-deriving A16 from the committed artifacts cannot reconstruct the caveat that entry
136 says is the most consequential one.

---

# PART 3 — THE CLAIM TABLE AS A STANDALONE DELIVERABLE

Audited as a reader would: assuming the MD record is not available.

## 3.1 CRITICAL · R8-20 — A16 carries a weaker label than the weaker claim it supersedes

| row | claim | status |
|---|---|---|
| **A3** | A1 ∧ A2 ⇒ dissociable under intervention | *"MEASURED, **EXPLORATORY**, TWO-CODEWORD. The quantitative version is **WITHDRAWN TWICE**"*, "**qualitatively ONLY**" |
| **A16** | A1 ∧ A2 ∧ a dose correlation ⇒ installation gates refusal not capability | *"MEASURED, `slot0` PRIMARY"* |

A16 is A3 plus a correlation. It is a **stronger** claim resting on the **same** null plus one
underpowered ρ, and it carries neither "EXPLORATORY", nor a codeword scope, nor "qualitatively only".
On the brief's question — *is anything listed as MEASURED that is actually EXPLORATORY?* — **A16 is,
by the table's own precedent one row away.**

A16's correct status line would be approximately:
`EXPLORATORY, BUTTON ONLY, slot0 PRIMARY; the "not capability" half is a null the table elsewhere calls underpowered (C-CONT-032, Section E)`.

## 3.2 CRITICAL · R8-12 — A5 and A16 contradict each other, and neither row says so

**A5** (unchanged since entry 050): *"Installation predicts attack success **within domain**, topic
held fixed — slope +0.140, perm p = 0.0006"*, status **MEASURED**, no ⚠️.

**A16**: installation gates refusal, **not capability**.

A5 is an observational installation → **capability** link at **p = 0.0006** — a *better-powered*
association than the installation → refusal link A16 rests on (p = 0.023, below its own MDE). The two
rows sit eleven rows apart in the same table with no cross-reference.

**Either way the table is defective:**
* if A5 stands, A16's second half is contradicted by the table's own row;
* if A5 does not stand — its endpoint is the **pre-CR-002 "corrected ASR"** that Section B says must
  never be quoted as an estimate (*"any corrected ASR number as an estimate | it is an UPPER BOUND —
  63/100 kept positives spurious on button"*) — then **A5 needs a caveat it does not have**, and the
  phase's only within-domain installation→ASR slope is on a contaminated endpoint.

A5 carrying **no warning marker at all**, in a table where nearly every other row carries two, is the
most conspicuous omission in Section A.

## 3.3 HIGH · R8-19 — A2 mixes three endpoints in one row and omits the one A16 needs

The A2 statistic cell quotes **button +0.0030, CI [−0.030, +0.036]** — the *frozen-lexicon* endpoint
from `DR-070`. The status cell argues from **CR-002's 0.0343** base rate and a **"CI half-width ~0.029"**.
The CR-002 primary itself (**+0.0090, CI [−0.0090, +0.0269]**, entry 098) is **not in the row**. Three
endpoints, one row, and the reader cannot tell which CI goes with which base rate.

Missing from the row, and material to A16: the **hardware-matched** figure the row does quote
(−0.0075 `[−0.0597, +0.0448]`) has a half-width of **0.052** against a ctrl base rate of **0.0522** —
i.e. **the best-controlled measurement in the phase cannot exclude the knockout abolishing content-true
attacks entirely.** The row says "null survives"; it should say the null is uninformative at that
scope.

## 3.4 HIGH · R8-21 — A13's claim text is the sentence Section B forbids

| Section A, A13 | *"§15's **matched** reference: cell C's demonstration-side state aligns with the explicit-BOMB state as installation rises, **beating the matched context-only prototype**"* |
|---|---|
| Section B | *"the §15 result as a **matched**-reference finding \| a mismatched partner scores **higher**; the matching does no work (`C-CONT-062`)"* |

The headline sentence of A13 is the framing Section B prohibits. The ⚠️ later in the same cell states
the refutation (*"the token-level matching does no work — a mismatched same-domain partner scores
+0.4222 … beating the matched pairing in 98 % of them"*), but a reader takes the claim from the claim
column. **A13's claim text needs rewriting to drop "matched", not just a caveat appended.**

A13's status (**"MEASURED, REPLICATED CROSS-CODEWORD"**) also survives caveats that between them say:
the contrast choice determines the number (+0.1598 vs +0.4053), the matching does no work, the effect
is concept-dependent with knife non-significant (p = 0.0845) and negative under the fair contrast
(−0.0171), and installability is confounded with geometry strength across 3 concepts. A status that
survives that list is not doing its job.

## 3.5 HIGH · R8-22 — A15

* **"STRUCTURE REPLICATED ON TWO CODEWORDS"** rests on basket's **`1 ⊂ 8`**. A one-element subset
  relation is satisfied by any single event. REVIEW-7 supplied the correct quantitative form
  (rule-of-three upper bound 0.0045 on basket, 0.0050 on button, pooled 0.0024); the table uses the
  rhetorical form instead.
* **Entry 134's explicitly-named open item is absent**: *"the one genuinely open REVIEW-7 item remains:
  **A15's Wilson intervals are row-level where the declared unit is the domain**. Not touched here;
  **named so it is not quietly dropped**."* It is not in the A15 row. The table quotes
  "10.4 % [4.5, 22.2]" with no indication the interval is on the wrong unit. An item named in the
  record specifically to prevent it being dropped, dropped from the deliverable, is the sharpest kind
  of output defect.
* The one-directionality caveat is present and correct (*"near-definitional … goes bidirectional under
  the judge's own rubric refusal"*) — which makes its absence from A16 (R8-08) harder to excuse, since
  the author demonstrably knows to write it.

## 3.6 HIGH · R8-16 — the same quantity, three values, one table

| source | button dose-4 installation, `slot0` primary | domains |
|---|---|---|
| A14 / `CONT-ENTRY 100` / entry 129's linking table | **0.6728** | 90 |
| A16 / entries 130, 133 | **0.6587** | 90 |
| `DR-075` config / entry 131 (`n4cal`) | **0.6589** | 116 |
| `CONT-ENTRY 100` "published" denominator | **0.6719** | — |

And the derived saturation fraction appears twice, differently: **A14 "9.4 %"**, **A16 "10.3 %"** —
adjacent rows, same step, no reconciliation.

Entry 131 presents *"0.6589 vs 0.6587 … agree to the third decimal"* as *"a useful check on the
readout"*. It is a check between two members of one readout family, offered while a **0.014**
disagreement with the number the same table publishes two rows above goes unmentioned. This is the
`C-CONT-034/035` shape (an asserted quantity beside the thing it should equal).

**It also matters substantively**: entry 129's ρ was computed against an installation series whose mean
gain is 0.6728, while A16's headline table reports 0.6587. If those are different readouts, **A16's
table and A16's correlational evidence are on different installation measurements** and the record does
not say so.

## 3.7 HIGH · R8-17 — A16's headline correlation is unbacked by any artifact

```
git show --stat 5ecd8cf2   # CONT-ENTRY 129, the linking test
  external_md/...CONTINUATION_20260910.md | 50 +
  scripts/dcs_cont_scope.py               | 83 +
git show --stat eb229f48   # CONT-ENTRY 130, A16
  external_md/...CONTINUATION_20260910.md | 48 +
  reports/DCS_CONT_CLAIM_TABLE.md         |  1 +
```

No script computes the four ρ values; no JSON records them; `grep -r "0\.2376"` finds nothing under
`reports/`, `outputs/dcs_cont/` or `scripts/`. **The single number A16's novel leg rests on exists only
as prose in the record and prose in the table.** Section D of the same table is a list of twenty-plus
defects whose stated common shape is *"a quantity that could not have told you it was wrong"*
(`C-CONT-036`: a fabricated clean 0.0000; `C-CONT-039`: a regex count read as a rate). A16 is currently
in that category by construction. DR-075, by contrast, has a config, a result JSON and a hash — the
contrast within the same claim is itself informative.

**Recommendation (process, not science):** a `scripts/dcs_cont_linking.py` + `DCS_CONT_LINKING.json`
carrying, per codeword × scope: n, the per-domain installation and refusal gain vectors, the tie
structure, ρ, a permutation p, and the scope tag from `Scope.require()`.

## 3.8 MEDIUM · R8-23 — front matter

* **Header:** *"Revised 2026-09-12 after **REVIEW-2 and REVIEW-3** (`C-CONT-038`…`C-CONT-068`)"* on a
  table containing `C-CONT-091`, A15, A16 and DR-075 — i.e. four reviews and thirty entries later.
  A reader dates the provenance from this line.
* **Preamble:** *"**One** preregistered confirmation has happened: `DR-072`"*. `DR-073a`, `DR-074`
  (NOT SUPPORTED) and `DR-075` (SUPPORTED) are all preregistered reads. The intended meaning is
  presumably "one TEST read", which is true and should be what it says — otherwise a reader cannot
  place DR-075's "SUPPORTED" on any register at all.

## 3.9 A2 as a null — is it fairly presented? (brief's specific question)

**Yes, and A2 is the best-caveated row in the table.** It names the three populations explicitly
(0.0343 / 0.0250 / 0.0263), states which one the primary is computed on, gives the MDE comparison,
flags the undetermined basket sign, and says *"flagged by four consecutive reviews"*. Given the brief's
concern, the honest finding is that **A2 is not the overreach — A16 is, because A16 takes A2's
carefully-hedged null and spends it as a positive claim in a different row of the same document.**
The defect R8-19 describes is a mixing of endpoints, not an overstatement.

## 3.10 A3 as "withdrawn twice" (brief's specific question)

A3's row is **accurate and unusually complete** post-entry-133: the quantitative version is marked
withdrawn twice with both P-values, the basket-only cause is stated with the 4.2× figure, and the
button non-explanation is stated as such (*"the button reversal's cause is **unexplained**, not
established"*). Entry 133 is the strongest entry in this window. The only residue is R8-20: A3's
honesty makes A16's absence of the same hedging more conspicuous, since they are the same inference.

---

# PART 4 — CROSS-ENTRY COHERENCE (129–137)

| # | entries | contradiction |
|---|---|---|
| 1 | **130 ↔ 134** | 130 cites the all-slots dose ρ (+0.2548) as corroboration; 134 makes all-slots dose contrasts **inadmissible** and makes the helper raise on them. 134 does not retract 130's use of it; the table still carries it. (R8-06) |
| 2 | **130 ↔ 124** | 124 uses an MDE argument to say a ρ of 0.176 "cannot settle it either way"; 130 declares a ρ of 0.2376 — inside 124's own CI, below 124's own MDE at this n — "supported". (R8-05) |
| 3 | **130 ↔ 050 / `C-CONT-032` / Section B** | 130 asserts the negative that 050 declared undecidable and that Section B forbids in the mirror direction. (R8-01) |
| 4 | **130 ↔ A5** | 130 says installation does not gate capability; A5 says installation predicts capability within domain at p = 0.0006. (R8-12) |
| 5 | **130 internal** | "all three start at **exactly** zero" ⟹ the linking ρ is a cross-sectional dose-4 correlation, not a dose-response one. The two halves of the entry cannot both be strong. (R8-03) |
| 6 | **130 ↔ 100** | dose-0 "exactly 0.0000" vs "~0"; dose-4 0.6587 vs 0.6728. (R8-15, R8-16) |
| 7 | **131 ↔ 137** | 131 treats the saturation as the premise that makes DR-075 forced; 137 concedes it is measured on button only and that if basket does not saturate, DR-075's conclusion "must be relabelled". The claim table was frozen between the two and carries the unrelabelled version. (R8-07) |
| 8 | **136 ↔ 130** | see below. |

## 4.1 Does entry 136 undercut entry 130 more than it admits? — **Yes.**

**What 136 admits** (and deserves credit for): the CI is not inside the supported region and includes
zero; the measured rise is 2.4× the prediction; content-true rose proportionally more; A16's
quantitative half is "not confirmed"; DR-075 is "a passed falsification test rather than positive
confirmation".

**What 136 does not admit:**

1. **The domain-level patterns of the two endpoints are indistinguishable** — 10/5/75 vs 8/3/79. Both
   rows are printed; the comparison is not drawn. At this resolution refusal and content-true are the
   same behaviour, which is the single-mechanism prediction (R8-09).
2. **The event counts** — 5 net rows and 4 net rows out of 180 (R8-04). "Content-true rose 57 %" is
   four rows.
3. **The asymmetry of standards** between the 0→4 and 4→8 steps (R8-11). 136 applies "both CIs include
   zero, so neither is established" to the step that hurts A16 and never applies it to the step that
   helps it.
4. **That A16's dose leg would fail DR-075's own standard.** DR-075 was judged on a preregistered
   threshold against a stated alternative. A16's dose leg has no interval on the between-endpoint
   contrast, no preregistration, and 20-vs-7 events. 136 leaves it "as entered".
5. **That its own premise is button-only** — conceded only in 137, after the table's last edit.

**Net:** entry 136 is an honest entry attached to a claim that its honesty does not rescue. The
sentence *"A16 stays as entered"* is where the undercutting stops short: every caveat 136 writes is a
reason to **re-enter** A16 with a narrower scope, not to leave the table row unchanged.

---

# PART 5 — NARRATIVE HONESTY

## 5.1 Is the story drifting toward a conclusion the data does not carry? — Yes, and the drift has a shape.

Trace the same behavioural fact across the phase:

| entry | how the same null is described |
|---|---|
| 049/050 | *"a dissociation **in the qualitative sense**"*; the quantitative version **downgraded**, prediction on the CI bound |
| 107/116 | A2 is **underpowered in content-true units**; MDE exceeds the base rate |
| 121 | *"null, **sign undetermined**, on two codewords and now on matched hardware"* |
| 124 | *"the domain-level link that would show it is **absent at the power available**"* |
| **130** | **"installation gates REFUSAL, not capability … the strongest mechanistic statement this phase has produced"** |

Nothing was measured between 124 and 130 that bears on capability. Entry 130 is a **re-description** of
existing nulls plus one below-MDE correlation, and the re-description is strictly stronger than
anything the underlying measurements said. Entry 130 states this transformation openly —
*"This reframes A2's null into a positive statement"* — which is admirable disclosure of exactly the
move that should not have been made. **A null does not become a positive statement by being placed
next to a second measurement; it becomes a positive statement when something is measured that could
have come out the other way.** DR-075 was the attempt to supply that, and R8-10 shows its threshold
was placed outside the instrument's historical range.

**The counter-evidence, in the phase's favour:** the record is self-correcting at an unusual rate —
entry 132 (the bootstrap floor), 133 (a wrong cause in a deliverable, then a correction to the
correction when the edit no-op'd), 134 (a requested estimator shown to be a no-op), 137 (pre-registering
the basket ladder the moment the button-only premise was noticed). The defect ledger is longer and more
specific than most published work's limitations section. **The problem is not concealment; it is that
the strongest-sounding sentence in the deliverable is the one least supported by the artifacts, and
the corrective apparatus has been applied to everything around it rather than to it.**

## 5.2 The single strongest reason to doubt the headline

**A strictly simpler account explains every number, is corroborated by the phase's own text-level
evidence, and has never been tested against (R8-09).**

*Installation determines whether the model reads the request as a bomb request. Refusal and genuine
bomb content are both downstream of that one interpretive step. Removing the remap makes the model
answer literally — so refusals vanish (A4, A15), completions are rewritten (A2b), the judge's rubric
starts scoring `ko` rows as refusing the harmful goal (404/670), and content-true output should fall
too — by about 64 %, which every content-true interval in the phase is too wide to see
(`[−0.0597, +0.0448]` against a base of 0.0522).*

A16's two-mechanism framing ("a gated safety response, an ungated capability") is the *more* surprising
of the two available readings, is selected without a discriminating measurement, and requires that the
reader accept a null the same deliverable calls underpowered as a positive result.

**Runner-up (R8-02):** at dose 4, refusal is 0.1111 against a control of 0.1119, and content-true is
0.0389 against base rates of 0.0343–0.0522. Both endpoints reach their ordinary level. The
"dissociation" is 0.111 vs 0.039 read as a difference in kind when it is the ordinary ratio between two
endpoints with different base rates. **In the one place the phase does put both endpoints on the same
relative scale — DR-075's 4→8 step — the comparison runs against A16 (+57 % vs +25 %).**

---

# WHAT WOULD CHANGE THE VERDICT

Ordered by cost.

1. **Relabel A16 in the claim table** — free, and owed today: `EXPLORATORY, BUTTON ONLY`; add basket's
   dose leg (installation +0.4578, refusal +0.0056, ρ +0.0592/−0.0547) to the row; delete the
   +0.2548 corroboration (entry 134 forbids it) or mark it inadmissible; add the `kw_refusal`
   construct caveat A15's row already carries; add the `C-CONT-032` cross-reference; state the event
   counts (20/7 of 180, DR-075 net 5 rows).
2. **Publish the linking artifact** (R8-17) with the per-domain vectors and the tie structure, so the
   ρ can be audited and the Spearman tie problem assessed.
3. **Reconcile 0.6728 / 0.6587 / 0.6589 and 9.4 % / 10.3 %** (R8-16), and publish dose-0 per domain at
   full precision (R8-15) — this also settles R8-03 one way or the other.
4. **Express both endpoints on one scale, with an interval on the difference.** The quantity A16 needs
   is `Δlog(refusal) − Δlog(content-true)` (or a ratio-of-ratios) with a domain-clustered CI, on the
   0→4 step. It requires no new generation. If that interval excludes zero, A16's dose leg has an
   actual statistic behind it for the first time; if it does not, A16's dose leg should be withdrawn.
5. **The discriminating experiment (R8-09).** A16's two-mechanism account and the single-mechanism
   interpretation account diverge on one prediction: under the knockout, does content-true fall
   *proportionally* with refusal? Answering it needs the content-true CI half-width below ~0.017 at a
   base of 0.05 — i.e. roughly 4× the rows, or a bank with more domains. This is the fourth distinct
   result this phase has traced to bank generation (`CONT-ENTRY 076`, `079`, `124`), and it belongs in
   `DCS_CONT_NEXT_BANK_SPECIFICATION.md` as the headline requirement, not as a power footnote.
6. **A second refusal instrument that is not a function of the opening string** (R8-08). Until one
   exists, every refusal claim in this phase — A4, A15, A16 — is a claim about refusal boilerplate at
   character 0, and the one alternative instrument in the data disagrees with it.
