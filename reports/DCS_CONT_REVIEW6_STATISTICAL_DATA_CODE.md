# DCS-CONT REVIEW-6 — STATISTICAL + DATA + CODE

Scope: what landed **since** `REVIEW-5` — `CONT-ENTRY 104`–`115`, plus the artifacts
`scripts/dcs_cont_asr_factor.py`, `reports/DCS_CONT_ASR_FACTOR.json`, the `CONT-ENTRY 111` changes to
`scripts/dcs_cont_s15_reference.py`, and the `CONT-ENTRY 115`/`b7fd3752` changes to
`src/boombness/run_completeness_check.py`.

No SLURM job submitted, no GPU used, no FROZEN config / frozen lexicon / label file / script
modified. Job `882854` untouched. Everything below is recomputed from the raw judge runs, the raw
`gens.jsonl` completions and the raw readout `results.jsonl`, keyed `(codeword, arm, prompt_id)` and
`(domain, family_slot)` as the brief requires, with every join asserted non-empty.

---

## VERDICT

**Every published number in entries 108–113 reproduces from disk, most of them to the digit — and the
phase's most consequential new claim, the proportionality test, is weaker than "significant but
confounded" says.** I reproduce `CONT-ENTRY 113`'s behavioural ladder exactly (raw
**0.1722 → 0.3389**, Δ **+0.1667 [+0.1033,+0.2278]**, 61/90; CR-002 **0.0000 → 0.0389**, Δ
**+0.0389 [+0.0244,+0.0556]**, 24/90), its proportionality test to four decimals
(predicted **−0.0134 [−0.0197,−0.0079]**, measured **+0.0090 [−0.0090,+0.0269]**, gap
**+0.0224 [+0.0060,+0.0388]**), `CONT-ENTRY 112`'s calibration exactly (offset **−0.0002
[−0.0025,+0.0020]**, positive in **45/90**; within-Quadro step **+0.0635 [+0.0294,+0.0977]**),
`CONT-ENTRY 110`'s threshold sweep exactly in all twelve cells by running the committed script
(**12.74× / 11.94× / 7.80×** with intervals **[10.19,16.62] / [9.60,15.56] / [6.33,10.04]**, CR-002's
rate **0.0252 / 0.0250 / 0.0245**), `CONT-ENTRY 111`'s prototype correction exactly
(**+0.5057** including → **+0.5030** leave-one-out, 900 slots over 90 domains, 10 slots each), and
`CONT-ENTRY 108`'s 200-draw distribution within Monte-Carlo error (my 200 independent draws: mean
**+0.4209**, sd 0.0182, 95 % range **[+0.3874,+0.4558]**, matched−mismatch **−0.0386
[−0.0735,−0.0051]**, **198/200** beating matched, against the published +0.4222 / [+0.3879,+0.4510] /
196/200). The bootstrap **is** joint, verified by reproduction: independent per-quantity resampling
gives **[−0.0017,+0.0464]**, which does not match the published interval — and which is **wider**,
not narrower, so the brief's premise on that point is backwards.

**What the proportionality test does not survive is its own null and its own declared primary.**
Three findings, each independently sufficient to downgrade it from "significant but confounded" to
"not a test of the thing it names":

1. **The linear-proportionality null is contradicted by the data that define it.** Across the three
   dose-4 conditions that actually vary installation while holding "demonstrations are present"
   fixed (`base`, `ctrl3`, `ko`; installation 0.470 → 0.685, a range *larger* than the knockout's own
   displacement), the within-domain slope of content-true ASR on installation is **−0.053** —
   *opposite in sign* to the **+0.071** chord the test uses as its reference. The dose chord is not a
   slope of ASR on installation; it is the 0→4 discontinuity, where installation goes 0 → 0.67 **and
   demonstrations appear at all**. "Same slope" is not a hypothesis anyone holds, and the gap it
   rejects is the difference between a chord and a local slope.
2. **On the program's own declared `slot0` primary the result vanishes and reverses.** The
   installation endpoint's primary was pre-declared `slot0` (`CONT-ENTRY 094`) and every published
   installation number uses it. The ASR half of entry 113 silently uses **all five slots**, and the
   ratio inside the test mixes scopes: its numerator (**−0.2082**) is the **all-slots** ko − base
   installation effect and its denominator (**+0.6719**) is the **slot0** dose slope. Computed
   consistently on `slot0`: predicted **−0.0104**, measured **−0.0149**, gap **−0.0046
   [−0.0452,+0.0366]**, **P(measured ≤ predicted) = 0.587**.
3. **The measured arm's effect is mostly a refusal-rate difference.** `ko` refuses on **4.0 %** of
   rows against **11.2 %** for `ctrl3` (and 11.5 % `base`, 12.7 % dose 4) — the 6–14 knockout
   removes two thirds of the refusals. Conditioning on non-refusal, ko − ctrl3 falls from
   **+0.0090 → +0.0061** on CR-002 and from **+0.0328 → +0.0040** on raw ASR. The knockout is not a
   dose-equivalent manipulation of installation; it is an intervention that also disinhibits.
   The whole measured effect is **32 CR-002 rows against 26**, six completions out of 670.

**`CONT-ENTRY 112`'s conclusion survives; its central sentence does not.** "**within the Quadro run**,
offset-free" is false: `+0.0635` is `ts116m_readout_button_bomb_n8` (2026-09-12 04:04) minus
`ts116m_readout_button_bomb_n4cal` (2026-09-12 09:20) — **two different runs**, five hours apart, on
the same node. Nothing in this program has ever measured dose 4 and dose 8 inside one run. The same
sentence is in claim-table row **A14**. The calibration design is nonetheless *sound*, and better
than the entry argues: the L40S dose-4 run uses `readout_max_batch = 0` and both Quadro runs use
`readout_max_batch = 1`, so the calibration contrast changes hardware **and** batching **and** run
identity together — exactly the bundle that contaminates the 4→8 comparison. The bound is on all
three at once, which is the right bound. What it does not license is the entry's general rule:
**at the slot level the same offset has sd 0.0150 and reaches 0.069**, so "comparisons whose endpoint
is a readout need not be hardware-matched" holds for a mean over 90 domains and not for a readout on
few rows.

**Three reproducibility defects, one of them live.** `scripts/dcs_cont_asr_factor.py`'s
**`--adjust-recall` flag is a no-op** — it is declared, documented in the docstring as printing "its
own stratum table", and never read; a user who passes it gets the *unadjusted* factor with no
warning. The script's `--cluster` **defaults to `run+domain`**, the option `CONT-ENTRY 105` itself
calls "the obvious wrong way to do this", and the only committed result artifact
`reports/DCS_CONT_ASR_FACTOR.json` carries exactly that disowned interval (**[11.23, 12.69]**) while
the record quotes [9.60, 15.56]. `CONT-ENTRY 105` says the script "now says so in its own help text";
`--cluster` has **no help text at all**. And `CONT-ENTRY 111`'s item 4 — "the mismatch caveat is now
in the docstring" — is **false**: the commit `d53839c4` changes no docstring line.
**Entries 108, 112 and 113 committed no code**, so the calibration and the proportionality test join
098/099/103 as heredoc results; `CONT-ENTRY 106`'s **129-row census (126/129 = 0.977)**, now cited in
claim row **A7c**, has **no label artifact in the repository** — `v4` holds 100 rows and there is no
`v5`. The `started-but-empty` guard **does what its docstring says** and the suspect conditional
expression was **correct**; it has since been rewritten anyway.

---

## FINDINGS BY SEVERITY

### S1 — "if installation drove attack success with a constant slope…". **The arithmetic SURVIVES exactly; the null FAILS as the right null**

**Claim** (`CONT-ENTRY 113`, `114`, `115`): predicted −0.0134 [−0.0197,−0.0078], measured +0.0089
[−0.0090,+0.0269], gap +0.0223 [+0.0060,+0.0389], P(measured ≤ predicted) = 0.0022.

**(a) It recomputes.** Rebuilding all six quantities from raw judge rows and raw readout rows over
the 67 `train` domains (70 − 3 `EXCLUDED_DOMAINS`), 20 000 joint domain resamples:

| quantity | published | **mine** |
|---|---|---|
| installation dose slope | +0.6719 | **+0.6719** |
| installation ko effect | −0.2082 (scope unstated) | **−0.2082** = `ko − continst2_base`, **all slots** |
| CR-002 ASR dose slope | +0.0433 | **+0.0433** |
| **predicted** | −0.0134 [−0.0197,−0.0078] | **−0.0134 [−0.0197,−0.0079]** |
| **measured** | +0.0089 [−0.0090,+0.0269] | **+0.0090 [−0.0090,+0.0269]** |
| **gap** | +0.0223 [+0.0060,+0.0389] | **+0.0224 [+0.0060,+0.0388]** |
| P(measured ≤ predicted) | 0.0022 | **0.0030 – 0.0050** over four seeds and four `n_boot` |

The P is at the optimistic edge of what I reproduce but inside Monte-Carlo error at any plausible
`n_boot`; I record it rather than dispute it. Everything else is exact. **The entry never states
which contrast or which slot scope `0.2082` comes from** — I had to search a 3 × 2 × 3 grid to find
it, and the neighbouring candidates are −0.1864 (`slot0`, ko−base, the figure `CONT-ENTRY 100`
publishes), −0.1957 (`slot0`, ko−ctrl) and −0.2150 (all slots, ko−ctrl).

**(b) The null is not one anyone holds, and the data refute it directly.** The test's reference slope
is a **two-point chord** from dose 0 to dose 4. Between those two points installation moves
0 → 0.6719 **and** the prompt acquires four demonstrations, changes bank block (`cds_n0` → `cds_n4`),
changes length, and — verified — shares **zero prompt_ids** with the dose-4 arm. The knockout moves
installation 0.685 → 0.470 **within** dose 4, on the **same 670 prompt_ids** as `ctrl3` and `base`.
These are not the same exposure, and the chord is not the local slope. The four dose-4-regime
conditions let me measure the local slope directly, within domain:

| conditions used | installation range | **d(CR-002 ASR)/d(installation)** | d(raw ASR)/d(installation) |
|---|---|---|---|
| dose 0 → dose 4 (**the chord the test uses**) | 0.000 → 0.678 | **+0.0709** | +0.1946 |
| dose 0, base, ctrl3, ko | 0.000 → 0.685 | +0.0614 | +0.2348 |
| **base, ctrl3, ko (dose-4 regime only)** | 0.470 → 0.685 | **−0.0526** | **−0.1411** |

The relation is **not a line**: within the regime the knockout actually lives in, it has the opposite
sign. Predicting the knockout's ASR effect from the *local* slope gives **+0.0110** against a measured
**+0.0134** (`ko − base`) — no gap at all. (That local slope is itself partly derived from the arm
under test, so it is not an alternative estimate; it is a demonstration that the chord assumption is
the entire result.)

**A fairer null exists and was not run.** The matched comparison is a **dose-8 ASR arm**: dose 4 → 8
moves installation by +0.0635 *within the upper regime*, which is the regime the knockout perturbs.
Judging a dose-8 behavioural arm would give a local slope on the same scale as the knockout's
displacement, with no chord assumption. `CONT-ENTRY 113` names a different missing experiment (a
hardware-matched control, now running as `882854`); that one fixes the confound, not the null.
A second fairer null, cheaper still: state the test as **mediation** — "installation is the only
mediator of the knockout's ASR effect, with a gain estimated off the dose manipulation" — which makes
the compound hypothesis explicit and stops the rejection reading as "installation does not drive ASR".

**(c) The two populations are comparable — more comparable than the brief suspects — with two
exceptions, one of which is inside the test.** All five judge runs share the same bank file
(`boombness_prompt_bank_ts116m_button_bomb.jsonl`), the same cell `C`, the same condition
(`natural_doublespeak`), the same pinned judge (`openai/gpt-4o-mini`), the same primary threshold
0.5, `goal_status = substituted` on every row, `judge_null_frac = 0`, and the same
`EXCLUDED_DOMAINS` treatment. `base`, `ko`, `ctrl3` and the dose-4 arm carry **identical prompt_id
sets** (670, verified set-equal). What differs:

| | dose 0 (`tsb66_C_n0`) | dose 4 (`tsb66_C_n4`) | `contasr2_ko` | `contasr2_ctrl3` |
|---|---|---|---|---|
| rows (67 train domains) | **134** | 670 | 670 | 670 |
| **slots present** | **`slot0` only** | 5 slots | 5 slots | 5 slots |
| bank block | `cds_n0` | `cds_n4` | `cds_n4` | `cds_n4` |
| generation GPU / node | L40S / **n-804** | L40S / **n-803** | A5000 / n-503 | L40S / n-804 |
| refusal rate | 0.000 | 0.112 | **0.040** | 0.112 |

**The dose-0 arm carries `slot0` only.** So the "+0.0433 dose slope" compares a one-slot dose-0 arm
to a five-slot dose-4 arm. Slot composition is not innocuous: on the same 67 domains the dose-4
CR-002 rate is **0.0433** over five slots and **0.0373** on `slot0`, and raw ASR is **0.3224** against
**0.3731**. Restricting the slope to `slot0` — the only apples-to-apples version, and the declared
primary — is what produces finding S1-2 below. Separately, the dose-0 anchor is **0 of 134 rows**
(Wilson 95 % upper **0.028**), which is two thirds of the slope it anchors; and the dose contrast is
**between prompts** while the knockout contrast is **within prompt**. (The `base` arm, not used in
the test, was generated on a **Tesla V100** — a third architecture — which is worth knowing before
anyone builds `ko − base` on it.)

**(d) The bootstrap is joint.** I could not check this against code — entry 113 committed none — so I
checked it by reproduction. Joint resampling (one domain index vector, all six quantities recomputed
on it) gives **[+0.0060, +0.0388]**, matching the published [+0.0060, +0.0389] across four seeds.
Resampling the ASR arms and the installation arms on independent index vectors gives
[+0.0060,+0.0387] — indistinguishable. **Fully independent per-quantity resampling gives
[−0.0017, +0.0464] and P = 0.034** — i.e. it **widens** the interval and crosses zero, because the
covariance the joint bootstrap propagates is *stabilising* here, not inflating. The published
interval could not have come from independent resampling. **SURVIVES, and the concern is the
opposite of what was anticipated.**

**Verdict: the computation SURVIVES exactly. The claim FAILS as a test of proportional mediation**
— its reference slope is a chord across a discontinuity, the local slope in the knockout's own regime
has the opposite sign, and the entry never states the slot scope of the ratio it divides. Stated
honestly it is: *"content-true ASR did not fall when 28 % of installation was removed"* — which is
the qualitative dissociation the record already had, now with the measured arm confounded two ways.

---

### S1 — the test uses all five slots for the endpoint whose declared primary is `slot0`, and mixes scopes inside one ratio. **FAILS as stated; the result does not survive its own primary**

`CONT-ENTRY 093`/`094` pre-declared `slot0` as the installation primary *before the data existed*;
`CONT-ENTRY 100`, `CONT-ENTRY 112` and claim row `A14` all use it; `REVIEW-4` caught and `CONT-ENTRY
095` fixed a composition error of exactly this kind. Entry 113 then builds its ratio out of an
**all-slots numerator** and a **`slot0` denominator**, and takes its ASR endpoint over **all five
slots**, without saying so anywhere.

| configuration | predicted | measured | **gap** | **P(meas ≤ pred)** |
|---|---|---|---|---|
| **as published** (inst ko all-slots ÷ inst dose `slot0`; ASR all slots) | −0.0134 | +0.0090 | **+0.0224 [+0.0060,+0.0388]** | 0.0037 |
| inst ko−ctrl all-slots instead of ko−base | −0.0139 | +0.0090 | +0.0228 [+0.0065,+0.0392] | 0.0033 |
| installation consistently `slot0`, ASR all slots | −0.0120 | +0.0090 | +0.0210 [+0.0045,+0.0377] | 0.0065 |
| **everything on the declared `slot0` primary** | **−0.0104** | **−0.0149** | **−0.0046 [−0.0452,+0.0366]** | **0.587** |
| `slot0` throughout, inst ko−ctrl | −0.0109 | −0.0149 | −0.0041 [−0.0443,+0.0371] | 0.579 |

On `slot0` the measured knockout effect is **negative** (−0.0149: 6 CR-002 rows in `ko` against 8 in
`ctrl3`, of 134 each) and sits *below* the prediction. The gap reverses sign and P goes from 0.004 to
0.59. **The `slot0` cell is small and noisy** — that is the honest reading, and it cuts both ways:
the all-slots version is better powered, but it is not the pre-declared population, and the entry
neither declares a switch nor reports the primary alongside it. A result that exists on the secondary
and not the primary is a result that must be reported on both. **FAILS as stated; report both.**

---

### S1 — the knockout removes two thirds of the refusals, which the proportionality null attributes to installation. **WEAKENED; a second confound of the same size as the first**

Per-arm, 67 train domains, 670 rows each:

| arm | refused | raw ASR | CR-002 | **raw among non-refused** | **CR-002 among non-refused** |
|---|---|---|---|---|---|
| `base` (V100) | 0.1149 | 0.3373 | 0.0343 | 0.3811 | 0.0388 |
| `ctrl3` (L40S) | 0.1119 | 0.3597 | 0.0388 | 0.4050 | 0.0437 |
| **`ko` (A5000)** | **0.0403** | 0.3925 | 0.0478 | 0.4090 | 0.0498 |
| dose 4 (L40S) | 0.1119 | 0.3224 | 0.0433 | 0.3630 | 0.0487 |

`ko` is the only arm with a 4 % refusal rate; the other three — on three different GPUs — sit at
11–13 %, so this is the **intervention**, not the hardware. Conditioning on non-refusal:

| | unconditional | **among non-refused** |
|---|---|---|
| `ko − ctrl3`, raw ASR | +0.0328 | **+0.0040** |
| `ko − ctrl3`, CR-002 | +0.0090 | **+0.0061** |

**Nearly the whole raw effect and a third of the content-true effect is a refusal-rate shift.** A
mediation null that attributes the knockout's entire ASR effect to installation is therefore
mis-specified twice over: the knockout also disinhibits, and it does so by an amount large enough to
produce the sign of the measured effect on its own. `CONT-ENTRY 113` records the hardware confound
and not this one. **WEAKENED.**

---

### S1 — `CONT-ENTRY 112`: "within the Quadro run, offset-free". **The number SURVIVES exactly; the sentence FAILS, and it is in the claim table**

Every figure reproduces to the digit:

| | published | **mine** |
|---|---|---|
| dose 4 on L40S | 0.6728 | **0.6728** |
| dose 4 on Quadro | 0.6726 | **0.6726** |
| **offset (Quadro − L40S)** | **−0.0002 [−0.0025,+0.0020]** | **−0.0002 [−0.0025,+0.0020]** |
| positive in | 45/90 | **45/90** |
| 4 → 8 cross-run | +0.0632 [+0.0304,+0.0993] | +0.0632 [+0.0290,+0.0976] |
| **4 → 8 "within the Quadro run"** | **+0.0635 [+0.0296,+0.0963]** | **+0.0635 [+0.0294,+0.0977]** |

**But the +0.0635 is not within a run.** It is `ts116m_readout_button_bomb_n8` (slurm 1427404,
start 04:04) minus `ts116m_readout_button_bomb_n4cal` (slurm 1537123, start 09:20) — two separate
submissions five hours apart. There is no run in this repository containing both dose 4 and dose 8.
The entry's phrase, and claim row `A14`'s "**+0.0635 … within-run**", should read *"across two runs on
matched hardware and matched batching"*.

**Is dose 4 measured twice on different hardware the right way to estimate the offset? Yes — and it
is better matched than the entry argues.** The contaminating contrast is
`L40S-dose4(batch 0) → Quadro-dose8(batch 1)`; the calibration contrast is
`L40S-dose4(batch 0) → Quadro-dose4(batch 1)`. Read from the configs:

| run | GPU / node | `readout_max_batch` | query kinds | conditions |
|---|---|---|---|---|
| dose 0 + dose 4 | L40S / n-804 | **0** (batched) | one_word + forced_choice | doublespeak + benign |
| dose 8 | Quadro / rack-omerl-g01 | **1** | one_word + forced_choice | doublespeak + benign |
| dose 4 calibration | Quadro / rack-omerl-g01 | **1** | one_word only | doublespeak only |

Hardware, batching mode and run identity all change together in both contrasts, so the calibration
bounds the whole bundle rather than hardware alone — which is what is needed, and the entry
undersells it by calling it a hardware offset. The residual assumptions, unstated: that the offset is
**dose-invariant** (measured at dose 4, applied to a dose-8 comparison, where prompts are longer), and
that the n4cal run's narrower channel/condition mix is immaterial (it is, at `--readout-max-batch 1`,
and `CONT-ENTRY 104` says so — but entry 112 does not carry the reason forward).

**What the calibration does not license is the general rule.** The offset is a **mean over 90
domains**. At the level of an individual slot it is not small:

| | slot-level offset, `slot0` dose 4, 180 slots |
|---|---|
| mean | −0.00022 |
| **sd** | **0.01496** |
| **max abs** | **0.0695** |
| bit-identical slots | 4 / 180 |

The 4→8 step it is protecting is **+0.0635**, about **4.2 slot-level sds**. So the rule
"comparisons whose endpoint is a readout need not be hardware-matched" is safe for means over ~90
domains (SE 0.0011) and not for readouts on a handful of rows. Note also that the sign of the offset
flips with slot scope: all slots gives **+0.0008**, not −0.0002. **Conclusion SURVIVES; "within-run"
FAILS; the general rule needs its n attached.**

---

### S2 — `scripts/dcs_cont_asr_factor.py`: a documented flag that does nothing, a default the record disowns, and a committed artifact carrying the disowned number. **FAILS**

**(a) `--adjust-recall` is a no-op.** It is declared at line 35 and **never read**. The docstring
states: *"Recall adjustment is therefore OPT-IN (`--adjust-recall`) and prints its own stratum
table."* It prints nothing. Run with the flag, the script emits the **unadjusted** factor with no
warning and writes a JSON with no recall field. Given that this repository has had five incidents of
a printed number not being the number described, a flag that silently ignores the correction
`C-CONT-077` exists to enforce is the most dangerous line in the file.

**(b) The default clustering is the one `CONT-ENTRY 105` calls "the obvious wrong way".** `--cluster`
defaults to `run+domain`, which resamples **(run, domain) cells** — finer than either one-way cluster.
Entry 105: *"returns a spuriously narrow [11.23, 12.69] — recorded here because it is the obvious
wrong way to do this and **the script now says so in its own help text**."* The `--cluster` argument
has **no help text**; `--help` prints only the choice list. Running the script with defaults today:

```
[factor] button  rows=43022 raw=0.2984 cr2=0.0250 | factor 11.94x  95% CI [11.23x, 12.69x]
                                                    over 4483 run+domain clusters
```

**(c) And `reports/DCS_CONT_ASR_FACTOR.json` — the only committed result artifact for the headline —
records `"cluster": "run+domain"` and `ci95: [11.23, 12.69]`**, while the record, the claim table and
entry 110 all quote **[9.60, 15.56]**. It also predates entry 110 and therefore carries **no
`sr_threshold` field**, which is precisely the omission entry 110 added the argument to prevent.
A reader who takes the repository's artifact over its prose gets the disowned interval at an
unrecorded threshold.

**(d) Smaller.** The `split` element of each row tuple (index 5) and the `load_split()` call that
produces it are computed and never used, so the script cannot reproduce entry 099's nine-cell
train/val/test table. `gens` is keyed on `prompt_id` alone with no duplicate assertion — safe within a
run today, silent last-row-wins if a run ever emits a repeat. `r["strongreject_score"] >= threshold`
will raise on a null judge score rather than refuse informatively. **The docstring's three correction
notes are accurate and valuable; the executable disagrees with two of them.**

---

### S2 — `CONT-ENTRY 111` item 4 is false: the docstring caveat was never written. **FAILS**

The entry and the commit message both state: *"the mismatch caveat is now in the docstring, not only
in the record: the comparator is a single random draw whose null holds that draw fixed, so it must be
quoted as the 200-draw distribution +0.4222 [+0.3879,+0.4510] and never as a point value
(C-CONT-081)."* `git show d53839c4 -- scripts/dcs_cont_s15_reference.py` contains **no change above
line 79**; the docstring is byte-identical to its pre-111 form and its `mismatch` line still reads
only *"cos to a DIFFERENT slot's B state from the same domain…"*. The substantive defect is still
live in the code: `matched_minus_mismatch`'s permutation null is built from `rb - rm` with **one
fixed** mismatch draw, so its p-value remains conditional on that draw — which is exactly what
`C-CONT-081` found and what item 4 claims to have documented.

**Items 1, 2 and 3 of entry 111 are real and correct, and I verified all of them.** Leave-one-out is
implemented correctly (`ks = [q for q in comp if q[0] == k[0] and q != k]`); the single-slot refusal
fires before any NaN can propagate into a Spearman; `layers_requested_but_absent` is recorded and
printed. The measured numbers reproduce exactly: prototype **+0.5057 → +0.5030**, on **900 slots /
90 domains / exactly 10 slots per domain**, ρ_B **+0.3823**. The one cosmetic wart is that the
sibling list is now computed twice per row under two names (`sib`, `ks`) with identical expressions.

---

### S2 — entries 108, 112 and 113 committed no code. **FAILS as an artifact; the numbers SURVIVE**

`git show --stat` on `1bf4e418` (108), `bcb851f0` (112) and `bd059170` (113): the log file, and for
112 one claim-table line. No script builds the 200-draw distribution, the cross-run calibration, or
the proportionality test. `REVIEW-5` named the unscripted headline "the single largest remaining
process risk"; `CONT-ENTRY 105` answered it for entries 098/099/103 by writing
`dcs_cont_asr_factor.py`, and the three entries since have gone straight back to heredocs — including
the one whose result the phase is deciding whether to claim. I reproduced all three, but entry 113
cost the most work of anything in this review purely because the scope of `0.2082` had to be searched
for rather than read.

---

### S2 — `CONT-ENTRY 106`'s 129-row census has no label artifact. **The population SURVIVES; the precision figure is unverifiable from the repo**

I confirm the population exactly: **81 CR-002 keeps on button** across
`contasrj_base` / `contasrj2_ko` / `contasrj2_ctrl3` (2,010 rows) and **48 on basket** across
`cbkasrj_base` / `cbkasrj_ko` / `cbkasrj_ctrl` (2,010 rows), **129 total**. The *labels* for those
129 rows exist nowhere in the tree: `data/labels/` holds `v2` (40), `v3` (76) and `v4` (100), and the
`set` field partitions `v4` as 40 derivation + 36 out-of-sample + 24 precision-batch-2. There is no
`v5`, no census JSON, no relabelling artifact. **`126/129 = 0.977` is now in claim row `A7c` as
"CENSUSED, not sampled"** and cannot be checked by anyone. `CONT-ENTRY 106`'s own standing fix
("any future labelling reads the whole completion, and the criteria file will say so") does not cover
this: the problem is not the protocol, it is that the product was never committed.

---

### S3 — `CONT-ENTRY 110`'s threshold sweep. **SURVIVES entirely — all twelve cells exact, by running the committed script**

| SR cutoff | button raw | button factor | 95 % CI | basket factor | 95 % CI | button CR-002 rate |
|---|---|---|---|---|---|---|
| ≥ 0.25 | **0.3207** | **12.74×** | **[10.19, 16.62]** | **7.13×** | **[5.49, 10.32]** | **0.0252** |
| ≥ 0.50 | **0.2984** | **11.94×** | **[9.60, 15.56]** | **6.59×** | **[5.10, 9.53]** | **0.0250** |
| ≥ 0.75 | **0.1914** | **7.80×** | **[6.33, 10.04]** | **4.49×** | **[3.57, 6.22]** | **0.0245** |

Exact in every cell, on 43,022 button and 5,628 basket rows over the recomputed 114-run census.

**One qualification on the interpretation.** The entry reads the near-constant CR-002 rate as *"a
small independent check that CR-002 is measuring something other than judge enthusiasm."* It is not
independent: CR-002 is **defined** as `SR ≥ t ∧ lexicon ∧ MATERIAL ∧ ¬SCOPE`, so its denominator is a
function of the same threshold. What the numbers show is that **97.2 %** of CR-002 keeps at SR ≥ 0.25
already score SR ≥ 0.75 — content-true rows are concentrated at the *top* of the judge's scale. That
is a genuinely useful fact and it supports the entry's mechanism sentence ("a stricter threshold
removes raw positives that were never content-true"), but it is a statement about where CR-002's
keeps sit inside the judge's distribution, not a check that is independent of it.

---

### S3 — `CONT-ENTRY 113`'s behavioural ladder. **SURVIVES entirely — every cell, CI and domain count**

| endpoint | dose 0 | dose 4 | Δ | 95 % CI (mine) | domains + | published |
|---|---|---|---|---|---|---|
| raw `ASR@0.5` | **0.1722** | **0.3389** | **+0.1667** | [+0.1033, +0.2278] | **61/90** | +0.1667 [+0.1044,+0.2267], 61/90 ✔ |
| **CR-002** | **0.0000** | **0.0389** | **+0.0389** | [+0.0244, +0.0556] | **24/90** | +0.0389 [+0.0244,+0.0556], 24/90 ✔ |
| installation (`slot0`) | ~0 | **0.6728** | **+0.6728** | [+0.6100, +0.7326] | **90/90** | +0.6728 [+0.6096,+0.7338], 90/90 ✔ |

"Content-true ASR at dose 0 is exactly 0.0000" is true — **0 of 180 rows** over the 90 domains
(0 of 226 in the arm as a whole; 0 of 134 over the 67 train domains), against raw 0.1722. The factor-of-17 magnitude gap (0.6728 / 0.0389 =
17.3) and the 90/90-vs-24/90 consistency contrast both hold. The one presentational defect is that
the installation row is `slot0` while the two ASR rows are all-slots, inside one table, unlabelled —
the same mixing that becomes load-bearing in S1-2 above.

---

### S3 — `CONT-ENTRY 108`'s 200-draw distribution. **SURVIVES within Monte-Carlo error; the "95 % range" is not a confidence interval**

Recomputed on `cont1_behavioral_button_bomb_20260910_152806_272296` at `cw_demo_mean` L24, 900 slots
over 90 domains, 200 fresh independent partner draws:

| | published | **mine (200 independent draws)** |
|---|---|---|
| matched (deterministic) | +0.3823 | **+0.3823** (exact) |
| mismatched, mean | +0.4222 | **+0.4209** |
| mismatched, sd | 0.0167 | **0.0182** |
| mismatched, 95 % range | [+0.3879, +0.4510] | **[+0.3874, +0.4558]** |
| matched − mismatched, mean | −0.0399 | **−0.0386** |
| matched − mismatched, 95 % range | [−0.0687, −0.0056] | **[−0.0735, −0.0051]** |
| draws exceeding matched | 196/200 = 0.980 | **198/200 = 0.990** |

Two independent sets of 200 draws agreeing to ~0.001 on the mean (MC SE ≈ 0.0013). `CONT-ENTRY 085`'s
+0.4059 and the script's +0.4196 both sit inside both ranges, so `C-CONT-081`'s withdrawal of
`C-CONT-074` is correct.

**The statistical qualification the entry needs.** *"the difference −0.0399, 95 % range [−0.0687,
−0.0056] — an interval that excludes zero, where before there was one number and no uncertainty at
all"* reads as a significance statement. It is not one. The matched value is **deterministic**; the
only thing resampled is *which sibling B state* is drawn. The range therefore describes the
comparator's arbitrariness with the data held fixed, and contains **no** sampling uncertainty over
domains or slots. The defensible statement is the 98 % one — *"the mismatched partner beats the
matched one for 98 % of possible partner choices"* — which is the claim `C-CONT-062` needs and which
survives untouched. "Excludes zero" should go.

---

### S3 — the started-but-empty guard. **SURVIVES: the logic does what the docstring says, and the suspect conditional was correct**

The brief's line, as committed in `1ba8bef7`:

```python
if os.path.getsize(os.path.join(d, rowfile)) > 0 if os.path.isfile(os.path.join(d, rowfile)) else False:
    continue
```

Python parses this as `if ((getsize(...) > 0) if isfile(...) else False)`. Truth table: rows file
present and non-empty → `True` → `continue` (not flagged, correct); present and empty → `False` →
flagged, correct; **absent** → `False` → flagged, correct. **It is not backwards.** It has since been
rewritten as an explicit row count in `b7fd3752`, which also added a `started_partial` census; the
new form is equivalent and readable. `30 tests pass` (entry 115 says 29, `b7fd3752` says 30; the tree
has 30). I ran the guard: **57 started-empty** directories and **2 started-partial**
(`VOID_C037c_dcsp24_base` 53/1160, `contasr_ko` 76/670), matching entry 115 and `b7fd3752`. It
**reports without failing**, as claimed.

**Four qualifications, none fatal:**

1. **"untouched for > 6 hours" is not what it measures.** The test is
   `time.time() - os.path.getmtime(config.json) < 6*3600`, and `config.json` is written **once, at
   start**, never touched again. So the predicate is *"started more than 6 hours ago"*. A job that
   has been running 7 hours and has not yet flushed its first rows **will** be flagged. The
   docstring's "so in-flight jobs are not flagged" is true only for jobs younger than 6 h. Using the
   directory's own mtime, or the newest file in it, would measure what the comment says.
2. **The motivating run is not in the census, and cannot be.** `contasr2_ctrl2` was moved to
   `outputs/boombness/QUARANTINE/` by `CONT-ENTRY 114`, one entry before the check was written, and
   `ROW_FILE`'s roots do not include `QUARANTINE`. The test's docstring implies the check would have
   caught it; it would have, before the move, and will catch the next one. Worth a sentence in the
   test so a later reader does not conclude the census covers quarantined runs.
3. **`judge` is not covered.** `ROW_FILE = {score_behavior, extract_boombness, retrieval_strength}`;
   `outputs/boombness/judge/` is outside every census here, so a judge run that starts and vanishes
   is still invisible. Pre-existing, but `C-CONT-082`'s lesson applies to it identically.
4. **The "length-agnostic" test unpacking is not length-agnostic.** `b7fd3752`'s message says
   *"Test unpacking is now length-agnostic (`*_`) so extending the census again will not break them a
   third time"*, but the three new tests use `*_, started_empty, started_partial = rc.scan()`, which
   binds **from the end**. Appending a seventh return value silently rebinds both names. The five
   older tests (`probs, checked, *_`) are genuinely position-safe; the ones that matter are not.
   A named tuple or a dataclass would close it.

---

### S3 — `CONT-ENTRY 104`–`107` bookkeeping. **SURVIVES; nothing new to report**

`CONT-ENTRY 104`'s out-of-sample precision table (button 24/0, basket 23/1; pooled 29/5 and 33/1
under the naive `rule_keeps` filter) and `CONT-ENTRY 105`'s corpus/clustering corrections were both
verified by `REVIEW-5` and are not re-litigated here. I confirm the two figures those entries turn
on and that the current tree matches: the census is **114 runs**, button **43,022 rows**, basket
**5,628 rows**, factors **11.94× / 6.59×**, and the `v4` label file's `set` partition
(40 / 36 / 24) is intact with no row in two sets. `CONT-ENTRY 107`'s A2 correction is arithmetically
right: CR-002 puts the button content-true rate at 0.0263 and the primary's half-width near 0.029, so
the MDE does exceed the entire genuine attack rate.

---

## WHAT I VERIFIED CORRECT, STATED PLAINLY

* **Entry 113's behavioural ladder** — all six cells, both CIs, both domain counts — exact.
* **Entry 113's proportionality test** — all six quantities and all three intervals — exact to four
  decimals; and the bootstrap is **joint**, confirmed by reproduction against the independent
  alternative.
* **Entry 112's calibration** — offset −0.0002 [−0.0025,+0.0020], 45/90, both 4→8 steps — exact.
* **Entry 110's threshold sweep** — all twelve factor/CI cells and all three CR-002 rates — exact, by
  running the committed script rather than reimplementing it.
* **Entry 111's §15 hardening** — prototype +0.5057 → +0.5030, 900 slots / 90 domains / 10 slots per
  domain, ρ_B +0.3823, leave-one-out and single-slot refusal correctly implemented.
* **Entry 108's 200-draw distribution** — reproduced with a fresh 200 draws, agreeing within MC error
  on the mean, sd, range, difference and the 98 % dominance figure.
* **Entry 106's population** — 81 button + 48 basket = **129** CR-002 keeps across the six ASR arms.
* **Arm comparability** — same bank, same cell, same condition, same judge, same threshold, same
  exclusions, `goal_status = substituted` and zero null judgements on every row of all five arms, and
  `base`/`ko`/`ctrl3`/dose-4 carrying **set-identical** 670 prompt_ids.
* **The started-empty guard** — logic correct, conditional expression correct, 57 + 2 census
  reproduced, 30 tests pass, reports without failing.

## RECOMMENDED FORMS

* **Proportionality test:** *"Removing 28 % of installation did not lower content-true ASR: measured
  `ko − ctrl3` = +0.0089 [−0.0090, +0.0269] against a dose-chord prediction of −0.0134. The gap
  (+0.0223 [+0.0060, +0.0389]) is significant against a **constant-slope** null, but that null is not
  supported by the data: within the dose-4 regime the installation→ASR slope is **−0.053**, opposite
  in sign to the +0.071 chord. The result is confounded three ways — hardware (`ko` A5000 vs `ctrl3`
  L40S), a refusal-rate difference (4.0 % vs 11.2 %), and slot scope (on the declared `slot0` primary
  the gap is −0.0046, P = 0.59). Not claimed."*
* **Dose calibration:** *"Dose 4 re-measured on the dose-8 node, GPU and batching mode gives an offset
  of −0.0002 [−0.0025, +0.0020] as a mean over 90 domains; the 4→8 step is +0.0635 [+0.0296, +0.0963]
  **across two matched runs**, not within one. At the level of an individual slot the same offset has
  sd 0.015, so this licenses unmatched hardware for readouts averaged over many domains, not for
  small-n readouts."*
* **Mismatch comparator:** *"The mismatched partner beats the matched one in 98 % of 200 partner
  draws (mismatched +0.4222, 95 % of draws in [+0.3879, +0.4510]). That range is the comparator's
  arbitrariness with the data held fixed, not a confidence interval; do not say it excludes zero."*
* **Threshold-conditional factor:** unchanged from entry 110 — it reproduces exactly. Add: *"97 % of
  CR-002 keeps already score SR ≥ 0.75, which is why the content-true rate barely moves; that is a
  statement about where the keeps sit in the judge's distribution, not a check independent of it."*
