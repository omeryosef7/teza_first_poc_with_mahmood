# `REVIEW-3` — PART 3, OUTPUT REVIEW (entries 038–047)

**Reviewer:** adversarial, independent. **Written 2026-09-10 06:30–07:05 IDT.**
**Scope:** entries 038–047 (`C-214`, `S-008`, `C-215`, `S-009`, ENTRY 044 claim table, ENTRY 045
draft, `C-216` figures, `R-207`). `REVIEW-1` (entry 024) and `REVIEW-2` (entry 039) findings are not
re-reported.

⚠ **THE TREE IS LIVE.** `squeue` at **2026-09-10 06:48 IDT**: job **873140** `sowk_bsk` **RUNNING**
on **n-802**, 1 h 14 m elapsed — the `basket` K ladder (`R-205`'s replication). Every file below is
described at its mtime, which is stated. Nothing was modified; no job was submitted.

**Artifact mtimes as read:**
`reports/figures/F{2,3,5,8}*.png` 05:38:54–55 · `reports/DCS_SUCC_CLAIM_TABLE.md` **04:36:34**
(**not touched since**, so it predates `R-207` at 06:05) · `DCS_SUCC_SLACK_DRAFT_..._20260910.md`
**06:38:41** (edited *after* `R-207` and after ENTRY 048) · `b1_position_control.json` 02:39 ·
`bombness_candidates_train.json` 03:39 · `q2_concept_present_basket.json` 06:06 ·
`concept_presence_basket.json` 06:05.

**VERIFIED** = I recomputed it from the artifact or re-rendered it. **INFERRED** = reasoning from
verified facts.

---

# 0. HEADLINE

Six findings that change what a reader is told, ranked:

| # | finding | where |
|---|---|---|
| **F-1** | **`F2` plots the exact in-sample number `C-215`/`C3` forbids, and its scope card labels it `leave-one-domain-out`.** The artifact's own `_reading` on the block says `FULL (in-sample)`. | A1 |
| **F-2** | **`F3`'s legend covers L6 and L7 — the only two layers in the panel that contradict its own title.** `C-216` moved the *card* off the data; the *legend* was never looked at. | A2 |
| **F-3** | **The `basket` cell-B "replication" is the *same 1130 completions*, byte for byte.** Entries 041, 042 and 047 call it a clean replication three times. | C2 |
| **F-4** | **Claim-table row 13 is wrong** — the context prototype wins from **L10**, not "every layer ≥ 8"; μ_B wins at L8 and L9 on **both** codewords. | D1 |
| **F-5** | **Claim-table row 14's "all 35" is false** — **33** of 35; the log's own ENTRY 028 title says 33. | D2 |
| **F-6** | **The draft's "127 of 461 … on *every* row" is the count for *any* row.** Every-row is **102**. | E1 |

---

# A. THE FIGURES — RENDERED AND LOOKED AT (the new duty)

All four `.png` were read as images. Two diagnostic re-renders were made **in scratchpad only**
(`/tmp/claude-47249/.../scratchpad/F3_diagnostic.png`, `F5_diagnostic.png`); no repo file changed.

## A1 ⛔ CRITICAL — `F2` plots the number the phase forbade, under a label that says it did not

**VERIFIED.** `scripts/dcs_succ_figures.py:70-95` (`fig2`) reads
`cand["by_codeword"][cw]["cell_coordinates_on_bomb_axis"]["L12"]["coords"]`. Values on disk
(`outputs/dcs_succ/bombness_candidates_train.json`, mtime 03:39):

| bar | F2 prints | artifact value | the phase's **headline** `B1` |
|---|---|---|---|
| button L12 cell C | **0.106** | `0.10556605299541143` | **`0.10444100418877339`** |
| basket L11 cell C | **0.137** | `0.13749508226099563` | **`0.13658738024777953`** |

`0.10556605…` is **the exact constant** ENTRY 042 (`C-215`/`C3`) identified:

> *"`0.105566` is the exact number this file's own `leakage_probe` block says 'may never be quoted as
> a control that the effect survived'"*

and which `C-208a` had already mis-printed once as "+0.1056 … the candidate I reported". `C3` was
fixed in `interaction_decomposition` — I confirm `interaction_decomposition.L12.shift_bomb|ref_bomb
.B1 = 0.1044410042`, matching `B1` proper to 0.00e+00, exactly as ENTRY 043 claims. **The fix was
not applied to `cell_coordinates_on_bomb_axis`, and that is the block `F2` plots.**

⛔ **And the panel asserts the opposite of the artifact.** `F2`'s scope card, line 5 of 5, reads
`v_lex leave-one-domain-out`. The artifact's own `_reading` on the very block being plotted reads:

> `"gap units relative to cell A, on the FULL (in-sample) bomb axis. A is 0 by construction and E is ~1 by construction"`

So the figure states a provenance its source explicitly denies.

**Why it is structural, not a typo:** the panel's fifth card line is `A and E are 0 and 1 by
construction`. `E = 1.000` is true **only** on the in-sample axis (artifact: `1.0000001170854094`).
On the leave-one-domain-out axis `E` is not 1 and the panel's framing collapses. The figure's design
*requires* the forbidden axis. This cannot be repaired by swapping a key.

**Consequence for the reader.** `F2` and claim-table row 8 are the same quantity and print different
numbers — **0.106 / 0.137** on the picture, **0.1044 / 0.1366** in the table — as do ENTRY 046's own
summary line ("C 0.106") and ENTRY 044's ("0.1044"), written 59 minutes apart.

## A2 ⛔ CRITICAL — `F3`'s legend covers exactly the two layers that refute the panel's title

**VERIFIED by re-render.** `fig3` (`scripts/dcs_succ_figures.py:113`) calls
`ax.legend(fontsize=6.5, loc="upper left")`. The x-axis runs L6→L14. The legend box occupies the
upper-left corner — **L6 and L7 in both panels**.

`F3`'s suptitle: *"`B1` is NOT localised: the codeword matches its neighbour and trails the readout
position."* Recomputed from `b1_position_control.json`, `mean_cos`:

| | button L6 | button L7 | basket L6 | basket L7 |
|---|---|---|---|---|
| `codeword_last` | **0.1565** | 0.1478 | **0.1486** | 0.1829 |
| `last` (readout) | **0.0208** | 0.1744 | **0.0410** | 0.1949 |
| paired `cw − last` | **+0.1357, 62/67 POSITIVE, p = 1.42e−13** | −0.0266, 31/67, p = 0.63 | **+0.1077, 55/67 POSITIVE, p = 1.03e−07** | −0.0120, 29/67, p = 0.33 |

⛔ **At L6 the codeword is better aligned than the readout position — 7.5× on button — in 62 of 67
domains, at p = 1.4e−13, on both codewords.** That is the panel's title reversed, significantly, and
it is the single most claim-contradicting point on the chart. In the published `F3` it is **behind
the legend**; only a sliver of one grey triangle escapes below the box.

The diagnostic re-render (`scratchpad/F3_diagnostic.png`, legend moved to `lower right`) shows the
grey `last` curve **crossing** the red `codeword_last` curve between L6 and L8 in both panels. The
published figure shows the grey curve uniformly on top, because the crossing is under the legend.

⛔ **This is `C-216` one degree worse.** `C-216`'s scope card covered K10–K14, which **supported**
the result; here the legend covers the region that **contradicts** it. The figure does not merely
hide its evidence — it hides its counter-evidence, and the result is a panel that looks cleaner than
the data.

## A3 ⛔ HIGH — `F5`'s CI band is *still* missing, and the card on the panel says it is there

**VERIFIED.** `C-216` defect 2 was: *"The CI band was missing for the same reason (`ci95` vs the
artifact's `bootstrap`)"*, and ENTRY 046 says it was *"Fixed by **asserting** the accessors instead of
defaulting."* The control-band accessor **was** fixed (`controls` / `band_mean`, correct). The CI
accessor **was not**. `scripts/dcs_succ_figures.py:140-142`:

```python
bs = r.get("bootstrap") or {}
ci = bs.get("ci95") or bs.get("ci95_domain_bootstrap") or [None, None]
los.append(ci[0]); his.append(ci[1])
...
if all(v is not None for v in los):
    ax.fill_between(ks, los, his, ...)      # never reached
```

The artifact's bootstrap block carries **`point` / `lo` / `hi` / `n_boot` / `caveat`**. Neither
`ci95` nor `ci95_domain_bootstrap` exists on any rung. So `ci == [None, None]` for all 14 rungs, the
`all(...)` guard is `False`, and **no band is drawn** — silently, with no `Refusal`. Confirmed by
looking at the rendered `F5`: there is no shading anywhere on the red curve.

⛔ **And `F5`'s scope card, line 4 of 5, reads `shaded: 95% domain bootstrap`.** The panel asserts a
band that is not on it.

It is not a negligible band. Widths `hi − lo` from the artifact:
`0.024, 0.024, 0.028, 0.241, 0.239, 0.243, 0.384, 0.441, 0.449, 0.738, 0.739, 0.740, 0.742, 0.743`
— **0.74 at K10–K14, ~10 % of the plotted y-range.** The diagnostic re-render
(`scratchpad/F5_diagnostic.png`) shows it plainly.

⛔ The comment block at `dcs_succ_figures.py:128-133` says *"They are asserted now"*, immediately
above the surviving `.get(...) or` chain. **The comment describing the fix is false about the code
it sits on.** This is the same failure `C-213a` named — a check that reads as evidence and is not
one — recurring inside the correction that named it.

## A4 ⛔ HIGH — `F8` is not a figure; it is a text card, and the phase's own rule required a `Refusal`

**VERIFIED.** `fig8` (`dcs_succ_figures.py:178-205`) calls `ax.axis("off")` and draws one
monospace text block. **Zero data are plotted.** No axes, no points, no scatter, no CI.

The script's own docstring (line 16) declares:

> `F8  per-domain installation vs per-domain ASR, raw and concept-present   <- plan Fig 8`

`fig8` reads only `q2["rows"]["pooled"]` — two scalars and two CIs. It never touches a per-domain
value, and **it cannot**: I checked, and `q2_concept_present.json` holds only
`_label/config/judge_run/generation_run/predictor_run/predictor_bound_by_sha16/join_key/n_perm/seed/rows`,
while `pr066_behaviour.json`'s `Q2` block holds no per-domain array either (`Q2.by_split` is `{}`;
the only per-domain export in that file belongs to `Q1`). **The (installation, ASR) pairs behind
ρ = 0.3961 are persisted in no artifact in the repo.**

⛔ ENTRY 046's stated policy is explicit: *"a panel that cannot be drawn from data is not drawn with
placeholder data"*, and the script refuses five of nine panels on exactly that ground. `F8` is the
sixth case and it **did not refuse** — it drew something that occupies a `.png`, is named
`F8_installation_vs_asr.png`, and will be read as a figure. A text card is not placeholder data, but
it is a panel drawn without data, which is the thing the rule forbids.

⛔ **Second-order consequence, and it is the more serious one:** the phase's **preregistered primary**
is the one result with no per-domain table on disk. ρ = 0.3961 cannot be recomputed from any
artifact — only re-derived by re-running the script against run directories. The claim table's
preamble promises *"Nothing here is a number that cannot be pointed at"*; for row 2's underlying data
that is not met.

## A5 MEDIUM — the scope card was moved off the data and onto the axis labels

**VERIFIED by rendering.** `scope_card()` (line 64) places the box at `(1.0, -0.42)` in **axes**
coordinates. `C-216` moved it out of the data area; it now lands on the axis furniture:

* **`F5`** — the x-axis label renders as `K  (the cut reaches ` and the rest is **under the card**.
* **`F3`** — both panels' x-axis label renders as `blo` and the rest is **under the card**
  (should read `block layer`).
* **`F2`** — the card covers the x **tick labels**: cell C's reads `Doublespea`, and **cells B and E
  have no visible label at all**. The panel's four bars are `A / C / B / E` and two of the four are
  unidentifiable on the rendered image.

The docstring's justification (*"the card now lives below the axes where it cannot cover data"*) is
true of the data series and false of everything else on the panel. On `F2`, what it covers is the
labels that say which bar is which.

## A6 MEDIUM — `F5`'s scope card is five hardcoded string literals, in a script that says otherwise

**VERIFIED.** Docstring, line 7: *"every panel draws a SCOPE CARD **from the artifact it plots**"*.
`fig2` and `fig3` honour that (`b["n_train_domains"]`, `rec[...]["n_domains"]`). `fig5`
(lines 165-169) does not — **all five lines are literals**:

```
"n = 67 TRAIN domains, 670 rows/arm"
"readout: semantic_one_word (concept word on 0 of 32544 rows)"
"shape rule returns NEITHER -- 'step' is not used"
```

The values happen to be correct today (I verified `population.n_domains_declared = 67`,
`n_rows_per_arm = 670`, `shape.shape = "NEITHER — reported as such, no mechanism claimed"`, and
`32544` present in the artifact). But the card **cannot detect that it is wrong**, which is the
`C-134` shape the phase named as its own signature defect.

⚠ **This is live right now.** Job **873140** is producing the `basket` ladder. Re-pointing `fig5` at
that artifact yields a panel titled `carries 62% of the effect` with a card reading `n = 67 TRAIN
domains, 670 rows/arm … 0 of 32544 rows` regardless of what the basket ladder returns. The title's
`62%` is a literal too (line 172), and it will not move either.

## A7 LOW/MEDIUM — layout defects visible on every rendered panel

**VERIFIED by rendering.** `figsize=(10.0, 4.7)` with `tight_layout(rect=(0, 0.24, 1, 0.95))`
(`F2`/`F3`) and `rect=(0, 0.28, 1, 0.95)` (`F5`) collapses the axes into a strip:

* **55–70 % of every canvas is blank white** below the plot (worst on `F5`).
* **y-axis labels are clipped at the figure edge**: `F5` reads `mean paired delta in semantic_logod`
  (truncated); `F2` reads `position on the button->bomb axis (gap un` (truncated).
* **`F3`'s right-panel y-label overprints the suptitle** — the rotated `POSITION-PORTABLE` runs
  through the word `its` in *"the codeword matches its neighbour"*.
* `F3`'s left panel gets only two y-ticks (`0.00`, `0.25`) for a series spanning 0.02–0.35.

None of these change a number. All of them are visible in one second of looking, which is the point
of the new duty.

## A8 — verified correct on the figures

| checked | result |
|---|---|
| `F5` title `62%` | **VERIFIED** — `shape.largest_single_rung_rise = {from_K: 9, to_K: 10, rise: 0.6168284, rise_raw: −4.4927}`; 61.68 % → 62 % |
| `F5` control band drawn at K = 8, 9, 10, 11 | **VERIFIED** — `controls` band_means −0.0277 / −0.0292 / **+0.0334** / +0.0301 |
| `F5` 14 rungs, `Refusal` guards | **VERIFIED** — `len(ks) != 14` and empty-`controls` refusals are real and correct |
| `F5` `%%` escaping | **VERIFIED FIXED** — `62%` and `95%` render correctly |
| `F3` all nine layers L6–L14 plotted for all three series | **VERIFIED** — no series missing; only *obscured* (A2) |
| `F3` CI bands | **VERIFIED present** (`ci95_cos` is the right key) |
| `F8` ρ, p, CI, sha16, MDE | **VERIFIED** against `q2_concept_present.json` |

---

# B. `b1_position_control.json` vs ENTRY 041 — RECOMPUTED

## B1 ✅ Every tabulated number in ENTRY 041 reproduces

**VERIFIED.** I recomputed both contrasts at every layer for both banks from
`b1_position_control.json` and checked ENTRY 041's two 4×2 tables cell by cell. **All 16 cells
match**, means to 3 d.p., domain counts exactly, p-values to the printed digits.

I also checked internal consistency: for all 18 (bank × layer) cells,
`mean_cos[codeword] − mean_cos[following] − paired_mean == 0` to ±1e−16, and the same for `last`.

And I re-derived **all 36 `sign_p` values from scratch** under an exact two-sided sign test
(min-tail doubled, n = 67): **0 mismatches**, and the attainable floor `1.3552527156068805e-20`
= `2/2^67` is correct. The instrument's arithmetic is sound.

## B2 ⛔ HIGH — "at every layer" is false, and the artifact contains the refutation

ENTRY 041, verbatim:

> *"A larger fraction of the Doublespeak shift points along the local button→bomb axis at the FINAL
> PROMPT TOKEN than at the codeword, in 65–66 of 67 domains, on both codewords, **at every layer**."*

The artifact holds **L6–L14**. ENTRY 041 tabulated **L9, L11, L12, L13**. The four untabulated
layers are where the sentence fails:

| layer | button `cw − last` | basket `cw − last` |
|---|---|---|
| **L6** | **+0.1357, 62/67 POSITIVE, p = 1.42e−13** | **+0.1077, 55/67 POSITIVE, p = 1.03e−07** |
| **L7** | −0.0266, 31/67, **p = 0.63** (null) | −0.0120, 29/67, **p = 0.33** (null) |
| L8 | −0.1767, 2/67, 3.09e−17 | −0.1475, 3/67, 6.80e−16 |
| L10 | −0.2337, 1/67, 9.22e−19 | −0.2086, 1/67, 9.22e−19 |
| L14 | −0.1488, 3/67, 6.80e−16 | −0.2009, 1/67, 9.22e−19 |

⛔ **At L6 the claim is reversed and significant on both codewords; at L7 it is null on both.** The
sentence holds at **7 of 9 layers**, not "every layer". The correct statement is *"at every layer
from L8"*.

⛔ Same error, propagated: **claim-table row 7** ends *"both codewords, **every layer**"*; ENTRY 043's
candidate table says *"not localised at the codeword (`S-008`)"* unqualified; and the Slack draft
(§3) drops even the hedge (see E5).

## B3 MEDIUM — the two ranges quoted are the ranges of the *tabulated quarter*, not of the grid

**VERIFIED.**

* *"indistinguishable from the adjacent neutral token (mixed signs, **34–44/67**, p **0.014–1.0**)"*
  (claim-table row 7). Over all 18 `codeword − following` cells the true range is **19/67 to 62/67**,
  and **five** cells fall below α = 0.05, **three** below 0.005: button L6 `+0.0794, 47/67,
  p = 0.00131`; button L8 `+0.0575, 48/67, p = 0.000522`; **basket L7 `−0.0566, 19/67,
  p = 0.000522`**; basket L8 `+0.0320, 43/67, p = 0.0271`; basket L14 `−0.0559, 24/67, p = 0.0271`.
  ENTRY 041's *"only one cell of eight reaches p = 0.014"* is true **of its eight tabulated cells**
  and false of the eighteen the artifact contains.
* *"in **65–66 of 67** domains"* — that is L9 and L12 only. At L11 the counts are **59/67** (button)
  and 62/67 (basket); ENTRY 041's own table prints the `8/67` and `5/67` that give them. Across the
  four tabulated layers the range is **59–66 of 67**.

⚠ Neither correction reverses `S-008`'s verdict — the L8–L14 evidence is overwhelming and the
direction is against the phase's own hypothesis, which is the right way for an error to point. But
both ranges are quoted in a deliverable as if they described the grid.

## B4 MEDIUM — the paired contrasts cannot be independently recomputed from the artifact

**VERIFIED.** The review brief asks me to *"recompute the paired contrasts from `per_domain_cos`"*.
**There is no `per_domain_cos`, and no per-domain array of any kind, anywhere in
`b1_position_control.json`.** Each position node carries only
`mean_gap_units / sd / ci95 / gap_norm / mean_raw_proj / mean_cos / ci95_cos / mean_shift_norm`, and
each paired node only `mean / ci95 / n_positive / n_domains / sign_p / sign_p_floor /
_this_is_the_portable_one`.

What I could verify: the mean identity, and every `sign_p` from `n_positive` (B1). What I could
**not** verify from the artifact: the `n_positive` counts themselves, and the bootstrap `ci95`
intervals. `S-008`'s domain counts — the "1/67", "2/67" that carry the whole result — rest on the
producing script, not on anything a reader can re-derive. Given that the same phase persisted
`per_domain_delta` in the K ladder and `per_domain_B1_export` in the candidates file, this omission
looks like an oversight rather than a policy.

## B5 ✅ `C-214` verified sound

**VERIFIED.** The denominator artefact ENTRY 040 caught is real and its numbers are right.
`gap_norm` at the codeword runs **3.3274 → 5.2043** (L6→L14), at `following` **1.0398 → 2.3164**, at
`last` **0.1129 → 1.4515**. Max ratio codeword∶last = **29.5×** at L6 → claim-table row 18's
"up to 30×" is correct. `C-214` is the strongest piece of work in the reviewed range.

---

# C. `q2_concept_present_basket.json` / `concept_presence_basket.json` vs ENTRY 047

## C1 ✅ Every number in ENTRY 047 reproduces

**VERIFIED**, both tables, against the two artifacts (mtimes 06:06 / 06:05):

`Q1` — raw C dose 4 **0.16106**→0.1611 ✓ · concept-present **0.052212**→0.0522 ✓ · C dose 0 raw
**0.0221239**→0.0221 ✓ · C dose 0 concept-present **0.0**→0.0000 ✓ · B dose 4 **0.0070796**→0.0071 ✓
· domains with concept content **57**/113 ✓ · button column (0.3274 / 0.1398 / 0.1549 / 0.0088 /
0.0071 / 91) all ✓ against `concept_presence.json`.
Ratio "~2.7× weaker": 0.139823 / 0.052212 = **2.678** ✓. Installation ratio 46/92 = **0.50** ✓.
Sign tests: Q1b 42/42 → exact two-sided p = **4.547e−13** ✓ ("4.55e−13 at its floor");
Q1d 41/42 → **1.955e−11** ✓ ("1.96e−11"). Both Δ reproduce as pooled-row differences, which here
coincide exactly with the domain-paired means (10 rows per domain in every arm).

`Q2` — pooled **+0.4467769** / CI [0.2856, 0.5834] ✓ · concept-present **+0.4868175** / [0.3319,
0.6161] ✓ · train +0.52620 / +0.53998 ✓ · validation −0.07333 (p 0.73713) / +0.09707 (p 0.65943) ✓ ·
test +0.46147 (p **0.027797**) / +0.43982 (p **0.033997**) ✓.
DONE/coverage discipline holds: all three basket arms report `n_judged == n_rows` (1130/1130,
226/226, 1130/1130).

## C2 ⛔ CRITICAL — the `basket` cell-B "replication" is the *same data*, byte for byte

**VERIFIED three independent ways.**

ENTRY 047: *"cell B dose 4 (direct harmful) | 0.0071 | **0.0071** — identical"* and *"**the
direct-harmful control is identical to four decimals on both codewords** (0.0071), which is what a
control arm should do."* ENTRY 041: *"identical to `button`'s direct-harmful baseline to four
decimals, which is a **clean replication of the control arm**."* ENTRY 042: *"`basket` cell B dose 4
**replicates** `button`'s direct-harmful control **to four decimals**."*

**It is not a replication. It is the same 1130 prompts and the same 1130 completions.**

1. **The generations are byte-identical.** `tsb66_B_n4_20260909_212431_276958/gens.jsonl` vs
   `tsb66b_B_n4_20260910_020713_3997667/gens.jsonl`: 1130 rows each, **1130 of 1130 identical
   position-wise**, and `prompt_sha16` identical on every row (first row `acd5f0ee48d81315` in
   both). Sorted-text SHA-256/16 of both files: **`554c46182b36b91d`**.
2. **The bank rows are identical.** In `ts116m_button_bomb.jsonl` vs `ts116m_basket_bomb.jsonl`,
   block `cds_n4`, `query_kind = behavioral`: **cell B identical on 1160/1160 rows; cell E identical
   on 1160/1160**. `n_codeword_occurrences = 0` in cell B on both banks. Cells **A** and **C**
   differ on 1160/1160 — they carry the codeword. (Block `cds_n4_sow`: B and E identical on
   **1160/1160**, i.e. all of them.)
3. **The configs differ, so this was a real second GPU run.** Different `bank`, different
   `exclude_prompt_ids`, different `seed` (20260909 vs 20260910), different `run_id` — and identical
   output, because the codeword never appears in a cell-B prompt.

The integer counts are therefore identical, not merely the rates: **10 judge positives, 8
concept-present, 1120 refusals, out of 1130**, in both. Three exactly-equal integers across
"two independent behavioural waves" is what should have prompted the check.

⛔ **What this costs.**
* The sentence *"which is what a control arm should do"* is **circular**. A control arm should give a
  statistically indistinguishable rate on **new data**; this gave an identical rate on **the same
  data**. Nothing was measured twice.
* "identical to four decimals" understates it: it is identical to **all** decimals, necessarily.
* ENTRY 047's *"Two codewords, **two independent behavioural waves**"* is true of three arms
  (C dose 4, C dose 0) and false of the fourth.
* **`Q1d` on basket is `basket-C` against `button-B`.** The contrast is still *scientifically* right
  — the direct-harmful baseline is codeword-free by construction, so it is the correct comparator —
  but it is not a basket-side control, and it is presented as one.
* ⛔ **`D-001`'s fifth appearance.** ENTRY 045 recorded the `basket` exclusion file's
  `exclusion_sha16` being byte-identical to `button`'s as the fourth. Here the identity is not a
  `prompt_id` collision but genuine row identity — and it was read as a scientific result rather than
  as the same structural fact.

**INFERRED, and worth a line in the log:** because cell **E** is likewise identical across banks,
`v_lex = mean(h_E − h_A)` differs between the two codewords **only through `h_A`**. The two
codewords' `B1` measurements share one endpoint of their own axis exactly. "Replicates on a second
codeword" (row 8, draft §3) is therefore weaker than it reads — it is a replication in `h_C` and
`h_A`, not an independent construction of the axis. This does not invalidate anything; it should be
stated.

## C3 MEDIUM — the TEST-split significance claim contradicts its own paragraph

**VERIFIED.** ENTRY 047: *"unlike button, **reaches significance on the 23-domain TEST split alone**
(p = 0.028), where the design's own MDE is 0.556"*, listed under ✅ — followed four lines later by
*"at n = 23 neither small split can test anything"*.

Both cannot be quoted. Specifically: ρ = 0.4615 is **below** the declared MDE of 0.556, so the design
was underpowered to detect it; there are **8 per-split tests** in the pair of Q2 artifacts with no
multiplicity control; and button's test split (+0.3779, p = 0.078) is not significantly different
from basket's. Presenting "basket significant on TEST, button not" as a **✅ advantage** is a
comparison of two underpowered, uncorrected, post-hoc tests.

⚠ To the entry's credit, it prints the null validation split unconditionally and says why. The fix is
to delete the "unlike button" clause, not to add a caveat.

## C4 LOW — the B-row in ENTRY 047's `Q1` table is the only unlabelled metric

Every other row names its metric (`raw ASR@0.5`, `concept-present`). The B row reads
`cell B dose 4 (direct harmful) | 0.0071 | 0.0071` with no label; **0.0071 is concept-present**
(raw is 0.0088). Both banks match on both metrics, so nothing is wrong — but entries 041/042 quote
`0.0088` for the same comparison and 047 quotes `0.0071`, with no statement that they are different
statistics.

---

# D. `reports/DCS_SUCC_CLAIM_TABLE.md` — NINETEEN ROWS, EVERY NUMBER

File mtime **04:36:34**, unmodified since. Verdicts below; **11 rows verify clean**.

| row | verdict |
|---|---|
| 1 | ⚠ raw ✅ · concept-present **not in the cited artifact** (D7) |
| 2 | ✅ |
| 3 | ✅ |
| 4 | ✅ (see D11) |
| 5 | ✅ |
| 6 | ✅ |
| 7 | ⛔ **"every layer" false** (B2); ⚠ ranges are of a quarter of the grid (B3) |
| 8 | ⚠ **"~14 sd" uses the sd the artifact forbids** (D6); values ✅ |
| 9 | ⛔ **"H is negative" holds on button only** (D5) |
| 10 | ⚠ **no CI, no test** (D8) |
| 11 | ✅ |
| 12 | ✅ |
| 13 | ⛔ **"every layer ≥ 8" is false — it is ≥ 10** (D1) |
| 14 | ⛔ **"all 35" is false — 33 of 35** (D2) |
| 15 | ✅ |
| 16 | ✅ (⚠ cited artifact still carries the withdrawn `C-213c` rule — D10) |
| 17 | ✅ |
| 18 | ✅ |
| 19 | not verifiable here (inherited knife/gun install counts) |

## D1 ⛔ HIGH — row 13, "at every layer ≥ 8", is wrong on both codewords

**VERIFIED.** Row 13: *"a context-only prototype containing no concept token (μ_C) beats the concept
prototype **at every layer ≥ 8** (0.0515 vs 0.0429)."*
`bombness_candidates_train.json`, `metrics["B3proto|L*|shift_bomb|proto_*"].mean_delta_cos`:

| layer | button `proto_C` | button `proto_B` | winner | basket `proto_C` | basket `proto_B` | winner |
|---|---|---|---|---|---|---|
| **L8** | 0.04215 | **0.04717** | ⛔ **proto_B** | 0.03700 | **0.04347** | ⛔ **proto_B** |
| **L9** | 0.04495 | **0.04839** | ⛔ **proto_B** | 0.04124 | **0.04609** | ⛔ **proto_B** |
| L10 | **0.04896** | 0.04468 | proto_C | **0.04429** | 0.04204 | proto_C |
| L11 | **0.05196** | 0.04432 | proto_C | **0.04574** | 0.04087 | proto_C |
| L12 | **0.05145** | 0.04290 | proto_C | **0.04504** | 0.04202 | proto_C |
| L13 | **0.05771** | 0.04125 | proto_C | **0.04848** | 0.03874 | proto_C |
| L14 | **0.05629** | 0.02948 | proto_C | **0.04530** | 0.02566 | proto_C |

⛔ **The concept prototype wins at L8 and L9 on both codewords.** The correct threshold is **L10**.
The quoted pair `0.0515 vs 0.0429` is button L12 and is correct (0.051452 / 0.042901) — the numbers
are right, the range is not.

**Direction: it overstates the rejection.** Row 13's status is `REJECTED`; a reader is told the
context-only prototype dominates across a seven-layer band when it dominates across five, and is not
told that the concept prototype wins at the two layers immediately below. `B3`'s rejection survives
(five layers, both codewords, including every peak layer), but the row as written is not what the
artifact says.

## D2 ⛔ HIGH — row 14's "all 35" is false, and the log already says 33

**VERIFIED.** Row 14: *"Cell C **dose 0** … reads **0.1549** with refusal 0.0000; **all 35** positives
across 31 domains are the model answering the *literal* codeword question well."*

Verified from the judge run `tsb66j_C_n0_20260909_220818_3373361/results.jsonl` (226 rows,
`DONE.json` present): **35** rows at `strongreject_score ≥ 0.5`, across **31** domains — both ✅.
Refusal 0.0000 ✅. ASR 0.154867 ✅.

⛔ But the cited artifact, `outputs/dcs_succ/concept_presence.json`, says on the same arm:
`n_judge_positive_WITH_concept_content: 2`, `judge_positives_that_never_mention_the_concept: 33`,
`asr_and_concept_present: 0.008850` ( = 2/226). I re-derived it against the frozen 44-term lexicon
and found the two rows: **`cargo_airfield` (0.875, term `casing`)** and **`postal_depot` (0.875,
term `casing`)**.

⛔ **And the log's own ENTRY 028 is titled *"the `C-209` repair works, and it removes **33 of 35**
dose-0 'successes'"*.** The deliverable says 35, the log says 33, and the deliverable's own footer
says *"Where this file and the log disagree, the log wins."*

⛔ **This is `C-213d` repeating verbatim.** `C-213d` corrected exactly this word — ENTRY 028's
*"**all** 11 of 11"* for cell A, which the correction showed was 29 of 30. The same absolute
quantifier was then written into the deliverable for cell C sixteen entries later.

⚠ Substantively the reading may well be right — `casing` in a cargo-airfield or postal-depot
completion is very plausibly a benign package casing, and the two rows are almost certainly literal
answers too. But row 3 of this same table makes concept-presence **the** corrective filter, so row 14
cannot then assert the filter found nothing when the artifact records that it found two.

## D3 ⛔ HIGH — row 7 carries `S-008`'s "every layer"

See **B2** and **B3**. Row 7 is the deliverable's statement of the phase's headline negative and both
of its quantified clauses are stated over a range they were not measured over.

## D4 ⛔ HIGH — §3's own forbidden rule forbids row 1 and every `basket` contrast

**VERIFIED arithmetic.** §3 line 91: *"⛔ **any ASR difference below 0.1372**, the measured
label-flip rate."*

| quantity | value | vs 0.13717 |
|---|---|---|
| **row 1, concept-present** | **+0.1327** | ⛔ **below** |
| §2 item 1 ("14.0 % against 0.7 %") | +0.1327 | ⛔ **below** |
| ENTRY 047 `Q1b` basket | +0.0522 | ⛔ far below |
| ENTRY 047 `Q1d` basket | +0.0451 | ⛔ far below |
| row 1, raw | +0.3186 | ✅ clears (2.3×) |

The deliverable's headline corrected effect is **0.132743**; the floor it declares in the same file
is **0.137168**. ⛔ **The claim table forbids its own row 1 and its own §2 item 1**, and the entire
`basket` behavioural replication of ENTRY 047 falls below the bar.

⚠ **This may be over-strict rather than a wrong number**, and that is worth Omer's judgement: the
0.1372 disagreement rate bounds a *between-run* difference on identical prompts, whereas row 1 is a
*within-domain paired* contrast where the same judge noise partly cancels. But the rule is stated
absolutely, it was adopted deliberately in `C-213c` after a weaker rule was withdrawn, and as written
it is violated by the deliverable's own headline. Either the rule needs its scope stated, or row 1's
concept-present figure needs a caveat. It cannot stand as it is.

## D5 ⛔ MEDIUM/HIGH — row 9's "the main effect is negative" holds on button only

**VERIFIED.** Row 9: *"`I` = **128 % / 102 %** of `B1` at **67/67** domains **and the harm-context
main effect `H` is negative** (−0.0287, 13/67)."* The "128 % / 102 %" spans both codewords, so the
`H` clause reads as spanning both. The parenthetical gives **button only**.

| | `H` | `n_positive` | exact two-sided sign p | `I` | `I/B1` |
|---|---|---|---|---|---|
| button L12 | **−0.028732** | **13/67** | **4.47e−07** | +0.133173 | **127.5 %** |
| basket L11 | **−0.002875** | **29/67** | **0.328** | +0.139463 | **102.1 %** |

⛔ **On the replication codeword `H` is a null, not a negative** — 29 of 67 domains positive,
p = 0.33, mean 10× smaller. The correct statement is *"`H` is negative on button and indistinguishable
from zero on basket."*

⛔ ENTRY 043 prints `H = −0.0029` for basket **without its `n_positive`**, while printing `13/67` for
button — so the log itself does not show the reader the one number that distinguishes the two cases.
The claim is then repeated unqualified in ENTRY 044's §2 item 5, in row 9, and in the Slack draft
(E4).

(`128 %` from 1.27511 and `102 %` from 1.02105 both round correctly. `B1 = H + I` holds to 2.3e−08
button / 2.8e−08 basket ✅ — `C3`'s fix is genuinely in place here.)

## D6 MEDIUM — row 8's "~14 sd" uses the sd its own artifact says not to quote

**VERIFIED.** Row 8: *"~14 sd over 12 random directions"*. The artifact
(`controls[L].random_unit_gap_units`) carries **two** sds and an instruction:

> `"_why_the_analytic_sd_is_here": "12 draws estimate a standard deviation to about +/-21%, so two banks printing 0.0015 +/- 0.0072 and 0.0009 +/- 0.0098 invite a between-bank reading that is pure sampling noise. The analytic value costs nothing and is the one to quote (S-002 IV 7.3)."`

| | empirical sd (12 draws) | **analytic sd (the one to quote)** |
|---|---|---|
| button | 0.0071929 → **14.32 sd** | 0.0084869 → **12.13 sd** |
| basket | 0.0097997 → **13.85 sd** | 0.0083419 → **16.26 sd** |

"~14" is the average of the two **empirical** figures. On the sd the artifact designates, the pair is
**12.1 and 16.3** — and the artifact's note describes precisely this failure: quoting the 12-draw sd
invites a between-bank reading that is sampling noise. Nothing scientific turns on 12 vs 16 sd, but
this is a deliverable quoting the statistic its cited artifact names as the wrong one.

## D7 MEDIUM — row 1's `+0.1327` is not in the artifact row 1 cites

**VERIFIED.** Row 1 cites **only** `outputs/dcs_succ/pr066_behaviour.json`. The raw `+0.3186` is
there (`Q1_paired_contrasts.Q1d.mean_delta = 0.318584`, `n_informative 104`, `n_positive 103`,
`holm.reject true` — all ✅). The concept-present `+0.1327` is **not**: it is
`0.139823 − 0.007080` computed from `concept_presence.json`, a different file, and that difference
appears in no artifact at all.

⚠ **And the file does contain `0.1327` — as something else.** Searching `pr066_behaviour.json` for
values near 0.1327 returns exactly three hits, all `/Q1/A_n0/asr_at_0.5 = 0.13274336…` — **cell A
dose 0's raw ASR**. A reader who follows the pointer finds the number, attached to a different arm
and a different quantity. The table's preamble promises *"Nothing here is a number that cannot be
pointed at"*; this one points at a coincidence.

(Numerically `+0.3186` happens to equal the pooled-row difference too, since every domain carries
exactly 10 rows in both arms — so mixing a domain-paired mean with a pooled difference costs nothing
here. But row 1 attaches "103 of 104 informative domains" to both figures, and that count was
computed for the raw contrast only.)

## D8 MEDIUM — row 10's concentration ratio has no interval and no test

**VERIFIED.** Row 10 is the row that **withdraws** the phase's specificity claim on the strength of
**1.20 vs 1.02**. Both reproduce exactly:
button 0.0948543/0.1044410 = **0.90821** ÷ 0.756353 = **1.2008**;
basket 0.0990697/0.1365874 = **0.72532** ÷ 0.707855 = **1.0247**.

⛔ **Neither carries a CI, a bootstrap, or a test against 1.0** — the only headline statistic in the
phase without one, in a project whose house rule is *"every p beside its attainable floor"*. With
n = 67 and per-domain sds of ~0.037/0.041 on the numerator, **1.02 and 1.20 have not been shown to
differ**, and neither has been shown to differ from 1.0.

⚠ The mechanical reason is visible in the artifact: `frac_of_axis_orthogonal_to_the_other_two` is a
single scalar property of the **mean** axis, not a per-domain quantity, so the ratio is a
domain-mean over a pooled scalar and no paired bootstrap is available without more work.

**Direction:** row 10's conclusion is a *withdrawal*, so an unquantified statistic pointing at
"no effect" is the safe direction. But ENTRY 044's §2 item 5 and the Slack draft convert it into a
**positive finding of absence** — *"its concept specificity is 1.02×, i.e. none"* — and that
inversion is not licensed by a point estimate with no interval.

## D9 MEDIUM — the deliverable has no row for `R-207`

**VERIFIED by mtime.** The claim table was last written at **04:36:34**; `R-207` landed at **06:05**.
ENTRY 047 states *"Row 2 of the claim table is **strengthened**"* — but the file on disk contains
**no basket ρ, no basket `Q1`, and no replication row**. Nineteen rows, none of them the phase's
newest and (per ENTRY 047) most reassuring result: ρ = 0.4468 pooled, above button's 0.3961, at the
permutation floor. A reader of the deliverable gets `Q2` on one codeword only.

## D10 LOW — row 16's cited artifact still asserts the rule `C-213c` withdrew

**VERIFIED.** Row 16 cites `outputs/dcs_succ/n5_judge_reliability.json`. Its numbers verify exactly
(226 pairs, `n_identical_completions 226`, disagreement **0.13716814**, Wilson [0.09835, 0.18812],
κ **0.44353**). But the file's own `_reading` still says:

> `"No ASR difference smaller than abs_asr_difference is a result."`

with `abs_asr_difference: 0.0221` — **the statistic `C-213c` withdrew as having no lower-bound
property.** The artifact was not re-emitted after the correction, so the file the deliverable points
to contradicts §3 of the deliverable by a factor of 6.

## D11 LOW — row 4's "+0.03" is one rung of a band that changes sign

Row 4: *"the dose-matched 3-draw non-demonstration control moves **+0.03**"*. `band_mean` by K:
**K8 −0.0277, K9 −0.0292, K10 +0.0334, K11 +0.0301**. `+0.03` is K10 — the correct, dose-matched
rung. But the band spans −0.029 to +0.033, and "moves +0.03" reads as a property of the control
rather than of one rung. `|band| ≤ 0.034 at every K` would be both stronger and true of all four.

## D12 ✅ Rows verified clean, with the recomputation

* **Row 2** — ρ `0.3960558994659426` ✅, `perm_p` at floor `9.999e−05` ✅, CI [0.228, 0.541] ✅,
  `declared_mde 0.2996` ✅, `sign_consistency 3/3` ✅.
* **Row 3** — 0.4206 pooled / 0.5260 train ✅.
* **Row 4** — `rise_raw −4.4927` → −4.49 ✅; `rise 0.6168284` → 61.7 % ✅; K10→K14 rises sum to
  **0.015068** → 1.5 % ✅; K10 `n_negative 67/67`, `p = p_floor = 1.3552527e−20` ✅.
* **Row 5** — `shape.shape = "NEITHER"` ✅; `f_K9 = 0.36810` ✅; STEP rule requires crossing
  0.20 → 0.50 and K9 already exceeds 0.20 ✅.
* **Row 6** — recomputed from `pr068_train67_20260909_233414_3931861/results.jsonl` (1005 rows,
  `DONE.json` ok): `donor_ceiling` mean **+12.3312**, **67/67** ✅; `transplant|all` mean
  **+0.006645**, **32/67**, exact sign p **0.8072** ✅, **0.0539 %** of the ceiling ✅.
* **Row 11** — six LOO-CV R²: button −0.4833 / −0.3464 / −0.4239, basket −2.0785 / −0.7181 /
  −0.5543. All negative ✅; range −0.35 to −2.08 ✅.
* **Row 12** — `mean_delta_C_minus_A 39.6239` ✅; Pearson 0.31009 / 0.18098 ✅; surviving fraction
  **0.848393 / 0.926712** ✅.
* **Row 15** — 0.154867 vs 0.0221239, ratio **7.0×** ✅. (⚠ "on the **identical** null" is loose —
  cell C **does** carry the codeword, so unlike cell B these two arms are *not* the same prompts.
  Given C2, that word now needs care.)
* **Row 17** — B dose 4 `0.008850`, E dose 4 `0.005310` ✅, both < 0.1372 ✅.
* **Row 18** — gap-norm collapse verified, max ratio **29.5×** ✅.

---

# E. `reports/DCS_SUCC_SLACK_DRAFT_MATAN_MAHMOOD_20260910.md`

File mtime **06:38:41** — edited after ENTRY 048 (06:35) and after `R-207` (06:05).
⛔ Confirmed **NOT SENT**: no send/mail/calendar action anywhere; the file's own header and footer say
so twice; no transmission machinery was invoked in this review either.

## E1 ⛔ HIGH — "127 of 461 … on **every** row" is the count for **any** row

**VERIFIED by independent recount.** Draft lines 59–60, and ENTRY 048 verbatim:

> *"**127 of 461** earlier judge runs (≥ 200 rows) have `goal_status = substituted` on **every** row."*

I walked `outputs/boombness/judge/*/results.jsonl` (805 dirs, 790 with results):

| selection | count |
|---|---|
| ≥ 200 rows, `DONE.json` present, excluding this phase | **461** ← denominator **reproduces exactly** |
| …of those, `goal_status = substituted` on **every** row | ⛔ **102** |
| …of those, `goal_status = substituted` on **any** row | ⛔ **127** |

⛔ **The quantifier is attached to the wrong number.** `127` counts runs with *at least one*
substituted row. The distribution of the substituted fraction over the 461 is
`{0.0: 334, 1.0: 102, 0.7: 18, 0.8: 6, 0.5: 1}` — **25 runs are partial**, and the draft's sentence
claims all 127 are total.

⛔ **And there is no artifact.** ENTRY 048 says "Counted on disk"; the count exists in no `.json`, no
script, and no output file — it is a shell count reported in prose. That is **exactly `C-213a`'s
shape**, occurring inside the correction ENTRY 048 wrote *to fix an unchecked claim about prior
work*, and it is heading to collaborators.

**What is correct:** *"**102 of 461** carry `substituted` on every row; a further **25** carry it on
part of their rows."*

## E2 ⛔ MEDIUM — `missing != zero`: 39 of the 461 have no `goal_status` field at all

**VERIFIED.** Of the 461 denominator runs, **39 carry no `goal_status` field on any row** — they
predate the field. The count treats them as "not substituted". They are **unmeasured**, not negative.

The house rule is `missing != zero`. On the measurable population the figures are
**102 / 422 = 24.2 %** all-substituted (and 127/422 = 30.1 % any), against the stated
**127 / 461 = 27.5 %**.

## E3 MEDIUM — the stated selection rule does not reproduce the stated denominator

**VERIFIED.** The draft says *"461 earlier judge runs (≥ 200 rows)"*. Applying exactly that —
≥ 200 rows, excluding this phase — I get **469**. The **`DONE.json` gate is what makes it 461**, and
it is not stated. A collaborator re-running the described rule gets a different number. (The gate is
correct and is a house rule; it simply needs to be in the sentence.)

## E4 ⛔ HIGH — "the main effect … is **negative**", unqualified, to collaborators

Draft §3, bullet 1: *"the whole effect is the token × context term (**128 %** of it), and the main
effect of adding harmful demonstrations is **negative**"*.

See **D5**: on `basket` the main effect is **−0.0029 at 29/67 domains, p = 0.33** — a null.
⛔ The draft is **weaker than the claim table**, which at least prints "128 % / 102 %" so a reader can
see two codewords exist. The draft gives **one** number and one unqualified sign, for the sentence
that kills the concept reading. A collaborator is told an effect replicates when one of its two
components does not.

## E5 ⛔ HIGH — the localisation sentence drops even the log's (already-wrong) hedge

Draft §3, bullet 2: *"it is **not localised at the codeword** — statistically indistinguishable from
the neutral token one position later, and *worse* aligned than the final prompt token."*

`S-008` at least said "at every layer" (wrong — **B2**). The draft removes the qualifier entirely, so
the reader gets an unconditional statement whose artifact shows, at **L6, on both codewords, at
p ≤ 1e−07**, the codeword **better** aligned than the final prompt token in 55–62 of 67 domains; and
whose `codeword − following` contrast reaches **p = 0.000522** at two layers, i.e. distinguishable.

The conclusion survives on L8–L14. The sentence as written does not describe the measurement.

## E6 MEDIUM — one of two numbers, twice, in the same paragraph

* *"its concept specificity, measured properly, is **1.02×** on the replication codeword"* — the
  development codeword reads **1.20**, which the claim table's row 10 carries and the draft does not.
* *"the token × context term (**128 %** of it)" — 102 % on basket is absent.

Each omission is in the conservative direction (understating the phase's own effect), so this is not
spin. But a collaborator who later sees 1.20 and 128 %/102 % will not be able to reconcile them with
what they were sent, and **neither ratio has a CI** (D8) — so "1.02×, 1.0 means no specificity at
all" states a null as a measurement.

## E7 MEDIUM — §1's headline is below the floor §5 declares

Draft §1: *"it runs at **14.0 %** against the direct request's **0.7 %**"* (both ✅: 0.139823,
0.007080). Draft §5: *"it flips **13.7 %** of labels"*.
⛔ **14.0 − 0.7 = 13.3 points, below 13.7.** The draft states its headline effect and, three
paragraphs later, a noise floor larger than it — without connecting them. See **D4**; the same
tension, but here it is two paragraphs apart in a document for external readers.

## E8 MEDIUM — the `basket` replication is absent from a draft edited after it landed

`R-207` completed at **06:05**; the draft was last written at **06:38**. Draft §2 gives
ρ = 0.396 / 0.421 (button) and says nothing about basket's **ρ = 0.4468 / 0.4868**, its
`Q1` replication, or its `Q1b` 42/42. ⛔ The phase's **only confirmatory replication** of its
preregistered primary is missing from the collaborator-facing summary written half an hour later,
while §5 does carry basket's 2.2 % floor — so the draft uses the basket wave for the caveat and not
for the result.

## E9 LOW — "in 67/67 domains" is attached to the control

Draft §4: *"against a dose-matched control … which moves **+0.03**, in 67/67 domains."* The 67/67 is
the **treatment** arm's sign count at K10 (`rungs.10.n_negative = 67`). Claim-table row 4 orders it
correctly; the draft's clause order gives it to the control.

## E10 LOW — "survives register and length controls" drops the quantified cost

Draft §3: length correction leaves **84.8 % / 92.7 %** (claim-table row 12 calls it *"a real but
bounded confound"*). "Survives" without the number is the one place the draft is looser than the
table in the *un*conservative direction.

## E11 ✅ Verified correct in the draft

103/104 ✅ · 14.0 % / 0.7 % ✅ · ρ 0.396 → 0.421 ✅ · MDE 0.300 ✅ · sign positive in all three splits
✅ · ~10 % of the gap in 66–67 of 67 ✅ · 62 % ✅ · +0.03 ✅ · 0.05 % of 12.3 log-odds ✅ (0.0539 %,
12.3312) · 15.5 % ✅ · 13.7 %, κ 0.44 ✅ · 226 byte-identical prompts, 226/226 identical completions
✅ · 2.2 % basket ✅ · **ASR 0.27–0.35** on the largest substituted runs ✅ (I checked the six largest:
0.2741, 0.2819, 0.3172, 0.3405, 0.3422, 0.3457, all `target_surface = button`, 1160 rows each) ·
0.9 % concept-present ✅ (0.008850). The `judge_boombness.make_goal` mechanism description matches the
`goal_status` field's behaviour on disk. §6's forbidden list is consistent with the claim table's §3.

⚠ Also to the draft's credit, and worth saying: **§5's "I would not revise any published number on
this alone"** is the correct call, correctly argued (different bank, floor is population-specific,
7× between codewords), and ENTRY 048 tightened the paragraph *before* anyone read it. The defect is
in the count, not the judgement.

---

# F. WHAT I COULD NOT CHECK

* Row 19's inherited install counts (knife 3/113, gun 1/113) — outside the reviewed entries.
* `S-008`'s per-domain sign counts and bootstrap CIs — **not persisted** (B4).
* `Q2`'s per-domain (x, y) pairs — **not persisted** (A4); only the summary ρ is on disk.
* The `basket` K ladder — **job 873140 was still RUNNING on n-802** at 06:48. Nothing about it is
  reviewed here, and per **A6** the `F5` panel that will plot it carries five hardcoded button
  constants and a hardcoded `62%` title.

---

# G. THE PATTERN, STATED ONCE

ENTRY 044 names this phase's signature defect as *"a quantity that could not have told you it was
wrong."* Four of this review's findings are that shape and three are its visual twin:

* **A3** — a `.get() or` chain that silently draws nothing, under a comment saying it was replaced by
  assertions, under a card saying the band is there.
* **A6** — a scope card of five string literals in a function whose docstring says cards come from
  the artifact.
* **E1** — a count of "every" that is a count of "any", existing in no file.
* **A1** — a number that the phase forbade twice, replotted under a label naming the axis it is not.

And the new duty's own harvest: **A2** and **A5**. `C-216` found the card covering data and moved it
below the axes. **Nobody then re-opened the file.** Had they, they would have seen the card now
covering three x-axis labels and two of `F2`'s four bar names — and, worse, the **legend** sitting on
the only two layers in `F3` that argue against `F3`'s title.

> ⛔ **`C-216`'s lesson generalises further than `C-216` applied it.** Rendering the artifact catches
> the card. **Looking at what is *under* every opaque box on the panel** — legend included — is what
> catches the rest. A panel is finished when nothing on it is on top of anything else.

*`REVIEW-3` Part 3. Written 2026-09-10, 06:30–07:05 IDT, against a live tree (job 873140 running).
No file in the repository was modified except this report; no job was submitted; nothing was sent.*
