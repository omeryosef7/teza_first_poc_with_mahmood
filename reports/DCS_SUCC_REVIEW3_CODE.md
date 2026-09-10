# `REVIEW-3` — PART 1, CODE REVIEW

**Scope: entries 038–047** (`C-214`, `S-008`, `C-215`, `S-009`, `ENTRY 044`, `ENTRY 045`, `C-216`,
`R-207`). `REVIEW-1` (entry 024) and `REVIEW-2` (entry 039) findings are not re-reported.

**Tree state when this review ran: 2026-09-10 06:32 – 06:47 IDT. THE TREE IS LIVE.** The `basket`
K ladder (job 873140, `runargs/dcs_succ/kladder_basket_train.txt`) was at arm **11 of 27** —
`outputs/boombness/score_behavior/ts116m_sowk_basket_K08_nondemo_matched_d1_20260910_064244_497607`
had just started at 06:42, `..._K08_demo_...063408_...` at 06:34. `ENTRY 047` (06:05) recorded
"4 of 27". Every artifact statement below is as of **06:47 IDT**; `kladder_sowk_train.json`
(00:35) is the **button** ladder and was not moving.

Reviewed at HEAD `b5ba16a4`. Commits in scope: `d1d6e14a 73f1f55e ed66b9c2 767bab86 31b6f7e8
cf379ee3 0b1c7814 48723bfb b5ba16a4`.

**VERIFIED** = I ran it, rendered it, or re-derived the number here. **INFERRED** = read from source
without execution.

---

## Summary table

| # | sev | finding | where | status |
|---|---|---|---|---|
| 1 | **CRITICAL** | a cross-bank chimera (button generations × basket judge) is constructible and **exits 0** | `dcs_succ_concept_presence.py:179`, `dcs_succ_q2_concept_present.py:213` | VERIFIED, executed |
| 2 | **CRITICAL** | `canon()` makes the frozen `kill_condition` and the corrected reliability floor editable without detection | `dcs_succ_amendment_integrity.py:37-43` | VERIFIED, forged file passes |
| 3 | **HIGH** | `ENTRY 047`'s `Q1b`/`Q1d` basket rows exist in **no script and no artifact** — `C8` recurring | `dcs_succ_pr066_behaviour.py` (not parameterised) | VERIFIED |
| 4 | **HIGH** | **`F5` still has no CI band.** `C-216`'s defect 2 was not fixed; the scope card announces the band anyway | `dcs_succ_figures.py:143-145,150,170` | VERIFIED by rendering |
| 5 | **HIGH** | **`F3`'s legend paints over `L6`/`L7` — the two layers that contradict the panel's own title** | `dcs_succ_figures.py:116` | VERIFIED by rendering |
| 6 | **HIGH** | **`F2`'s scope card paints over the tick labels of bars `B` and `E`** | `dcs_succ_figures.py:65,88` | VERIFIED by rendering |
| 7 | MED-HIGH | `F8` is not a plot: no per-domain data, no scope card, and a hardcoded conclusion sentence | `dcs_succ_figures.py:178-202` | VERIFIED by rendering |
| 8 | MEDIUM | `artifact_sha16_of_source` is **always `None`** — a provenance field that is a constant | `dcs_succ_b1_surface_floor.py:201` | VERIFIED |
| 9 | MEDIUM | the `B1 = H + I` assertion is **algebraically vacuous** and could never have caught `C3` | `dcs_succ_bombness_candidates.py:483-487` | VERIFIED |
| 10 | MEDIUM | `S-009`'s headline (1.20 / 1.02) is in no script and no artifact; row 10 cites an artifact that lacks it | `reports/DCS_SUCC_CLAIM_TABLE.md:41` | VERIFIED |
| 11 | MEDIUM | a block DECLARED changed and left unchanged classifies `IDENTICAL` with no warning — `C-213b`'s own shape | `dcs_succ_amendment_integrity.py:61-69` | VERIFIED |
| 12 | MEDIUM | `one_done()` in the figure script is **dead code** — a `DONE.json` gate that gates nothing | `dcs_succ_figures.py:49` | VERIFIED |
| 13 | MEDIUM | three refusals that cannot fire for the case they appear to guard | `q2:213`, `concept_presence:178,180` | VERIFIED |
| 14 | MEDIUM | `--out` never follows `--codeword`/`--bank-key`; the replication run overwrites the development artifact | three scripts | VERIFIED |
| 15 | LOW-MED | the position control writes a partial artifact and *then* crashes if a position refuses | `dcs_succ_b1_position_control.py:185,203` | INFERRED |
| 16 | LOW | `F5`'s scope card is a string literal, not read from the artifact it plots | `dcs_succ_figures.py:167-171` | VERIFIED |
| 17 | LOW | `EXCLUDED` re-declared as a literal in a file whose docstring says it imports rather than reimplements | `dcs_succ_q2_concept_present.py:47` | VERIFIED |
| 18 | LOW | `--bank` still overridable against `--codeword`; `C-213e` is re-creatable by hand | `dcs_succ_b1_surface_floor.py:134` | INFERRED |
| 19 | LOW | the `C4` patch shifted the shared RNG stream; bootstrap CIs across the artifact moved with no statistic changing | `dcs_succ_bombness_candidates.py:538` | VERIFIED |

**What I checked and found CORRECT** is in §20. `C3` and `C4` are arithmetically right; `S-008`'s
whole table reproduces from the artifact; the bank digests match the prereg pins; `R-207`'s `Q2`
binds all four parameters to `basket` correctly and its numbers match the artifact exactly.

---

## 1. CRITICAL — a cross-bank chimera is constructible, and it **exits 0**

This is the answer to task (a), and it is affirmative for **both** scripts. I built the call.

### 1a. The premise, verified first

`prompt_id` collides **completely** across the two banks — not partially, not for corresponding rows
only:

```
button gens 1130   basket gens 1130   intersection 1130
button judge 1130  basket judge 1130  basket-judge ∩ button-gens  1130
```

The house rule ("`prompt_id` is NOT unique across banks so joins are compound") is stronger than
`ENTRY 038`/`ENTRY 045` state it: the id sets are **identical**, so *any* membership or count check
keyed on `prompt_id` alone passes across banks.

### 1b. `dcs_succ_concept_presence.py` — button's generations bound to basket's judge

`--gen-prefix` (line 119) and `--judge-prefix` (line 120) are **independent free parameters**. The
only cross-check is line 179–188:

```python
both = [p for p in gens if p in jrows]
if len(both) != n:
    res["arms"][arm] = {"status": "REFUSED: the judge run covers %d of the %d generated rows..."}
```

Because the id sets are identical, `len(both) == n` across banks. **Executed at 06:35 IDT:**

```
$ python scripts/dcs_succ_concept_presence.py --arms C_n4 \
      --gen-prefix tsb66_ --judge-prefix tsb66bj_ --out <scratch>/mismatch.json
C_n4   n=1130  concept_content=0.1858 (210 rows, 91/113 domains)  refusal_like=0.1265
       | ASR 0.1611 -> asr_and_concept_present 0.0496  (126 of 182 positives never mention it)
EXIT=0
```

Read that line against `ENTRY 047`'s table. `concept_content = 0.1858`, `91/113` domains — those are
**button's** (published: 0.0805, 57/113 for basket). `ASR 0.1611`, `182` positives — those are
**basket's**. The chimera's headline is **`asr_and_concept_present = 0.049557`** against the
published basket value **`0.052212`**. A 5 % difference. Nothing in the run, the exit code, or the
printed line says anything is wrong. The artifact records `gen_run` and `judge_run`, so it is
*auditable after the fact* — but the operator has to notice, and the whole point of `C-213d`'s
repair was to stop the operator having to notice.

### 1c. `dcs_succ_q2_concept_present.py` — basket's predictor bound to button's outcome

Four parameters, no cross-consistency: `--gen-prefix` (182), `--judge-prefix` (183), `--bank-key`
(184), `--readout-glob` (185). The **predictor** side is protected — `bank_sha` comes from the
config's `population.banks.<bank_key>.bank_file_sha16` and line 229 filters readout runs on it, so
`--bank-key basket_bomb --readout-glob '*readout_button_bomb*'` yields `len(cands)==0` and refuses.

**The OUTCOME side is bound to nothing.** No check ties `--gen-prefix`/`--judge-prefix` to
`bank_sha`. **Executed at 06:37 IDT:**

```
$ python scripts/dcs_succ_q2_concept_present.py --bank-key basket_bomb \
      --readout-glob '*readout_basket_bomb*' --n-perm 300 --out <scratch>/chimera.json
predictor ts116m_readout_basket_bomb_20260907_152329_3191150 (bound by sha16 79511d9e254571e6)
judge     tsb66j_C_n4_20260910_000237_3406997          <-- BUTTON's judge run
pooled  113 | +0.3700 p=0.003322 CI [0.199, 0.519] | +0.3431 ...
train    67 | +0.4044 ...                          | +0.4342 ...
test     23 | +0.4309 p=0.03987 ...                | +0.2970 ...
EXIT=0
```

**`ρ = +0.3700` pooled, publishable-looking, at the permutation floor for its `B`, on a
basket predictor against a button outcome.** The written artifact then records
`"bank_key": "basket_bomb"` beside `"gen_prefix": "tsb66_"` — an internally contradictory
provenance block that nothing validates and that reads, at a glance, as basket's `Q2`.

⛔ This is the exact failure `PR-059`'s transfer-pair rule exists to prevent, and `ENTRY 047`'s
opening sentence — *"the scripts were parameterised … rather than copied, which is `C8`'s lesson
applied before it could bite again"* — is a claim about a safety property the parameterisation does
not have. Parameterising **without binding the parameters to each other** replaced "two copies that
can diverge" with "one copy that can be pointed at the wrong data".

### 1d. The fix that closes it

A single derived key. Either (i) require one `--codeword` and derive `gen_prefix`,
`judge_prefix`, `bank_key`, `readout_glob` and `out` from it; or (ii) keep the four flags and
**assert** that the generation run's `metadata.json.bank_file_sha16` equals `bank_sha`, refusing
otherwise. The generation runs already carry that field — `q2` reads it on the *predictor* side at
line 229 and does not read it on the outcome side. One line, symmetrically applied, kills 1b and 1c
together.

---

## 2. CRITICAL — `canon()` strips too much, and the frozen `kill_condition` is editable through it

This is task (d), and it is worse than the question implies.

### 2a. The mechanism

`dcs_succ_amendment_integrity.py:37-43`:

```python
def canon(o, prefixes):
    if isinstance(o, dict):
        return {k: canon(v, prefixes) for k, v in o.items()
                if not any(k.startswith(p) for p in prefixes)}
    if isinstance(o, list):
        return [canon(x, prefixes) for x in o]
    return o
```

`canon` is **recursive**. It strips keys matching `_amendment_note` / `_added_by_amendment` at
**every depth of every block**, then compares. So *any* substantive change, in *any* block, at *any*
nesting level, becomes invisible to the check the moment its key is given one of those two prefixes.
There is no allow-list of blocks in which annotation is permitted, no cap on what an annotation may
contain, and no requirement that an annotation be inert.

### 2b. The exploit, executed

I copied `configs/dcs_ts_pr066_amendment2.json` to scratch (the tree was not modified), reverted the
`C-213c` repair *inside* its annotation key, and injected an override of the **frozen kill
condition**:

```python
a['classifier']['_added_by_amendment_measured_floors']\
 ['label_disagreement_on_byte_identical_text'] = 0.0221        # C-213c's defect, restored
a['classifier']['_added_by_amendment_measured_floors']\
 ['_WHICH_ONE_GATES'] = 'THE GATING FLOOR IS 0.0221 ... A1 was right.'
a['kill_condition']['_amendment_note_override'] = \
 {'pooled_cellC_dose4_ASR_floor': 0.00, 'effect': 'the kill condition never trips'}
```

```
  classifier      ANNOTATED   identical once ['_amendment_note','_added_by_amendment'] keys are stripped
  kill_condition  ANNOTATED   identical once ['_amendment_note','_added_by_amendment'] keys are stripped
29 block(s) compared; 16 IDENTICAL, 3 ANNOTATED, 7 DECLARED, 0 UNDECLARED/MISSING
EXIT=0
```

**`kill_condition` was not even in `_blocks_this_amendment_changes`, and it still passed.** So the
answer to "can an amendment declare a block changed and then change a DIFFERENT one?" is: **yes —
it does not even need to declare anything, it only needs to name the change an annotation.**

### 2c. It is not hypothetical — the real `A2` already does it

Run against the committed `A2`, the tool prints:

```
  classifier   ANNOTATED   identical once ['_amendment_note','_added_by_amendment'] keys are stripped
```

The entire `C-213c` repair lives in **one** key,
`classifier._added_by_amendment_measured_floors`, holding
`label_disagreement_on_byte_identical_text = 0.1372`, `cohen_kappa = 0.4435`,
`_WHICH_ONE_GATES` ("THE GATING FLOOR IS THEREFORE THE LABEL DISAGREEMENT RATE 0.1372 … NOT
0.0221. A1 adopted the wrong statistic") and `_consequence_for_N1_and_N2` (the withdrawal of
"8–10× the floor").

⛔ **So the integrity check reports the block carrying this phase's corrected gating floor as
substantively identical to its parent's** — and the amendment's own declaration for that block
("adds the five MEASURED floors and corrects which one gates (C7)") is **overridden**, because
`classify()` tests `IDENTICAL` and `ANNOTATED` (lines 61–65) *before* `k in declared` (line 66).
The one block where you most want the diff printed is classified as a non-change.

`nulls_required` is `ANNOTATED` for the same reason.

### 2d. The check never shows you a declared diff

`--show-diff` defaults `True` (line 101), but line 123 iterates `for k in bad:` only. **`DECLARED`
and `ANNOTATED` blocks never get a unified diff printed.** A2's headline output is
`7 DECLARED, 2 ANNOTATED` with **nine diffs suppressed** — including
`things_that_must_not_be_said`, the block whose silent non-change *was* `C-213b`.

### 2e. Two smaller holes in the same file

* **line 53** `if k.startswith("_"): continue` — every top-level `_`-prefixed key is exempt from
  comparison. The parent carries six of them (`_the_parent_is_never_edited`,
  `_verbatim_copied_blocks`, `_why_blocks_are_copied`, `_question_is_NOT_verbatim`,
  `_artifacts_is_NOT_verbatim`, `_nulls_are_verbatim_plus_annotation`). An amendment can delete
  `_the_parent_is_never_edited` and the tool will not mention it.
* **line 56** `AMENDMENT-ONLY` is never added to `bad`. A **new top-level block** can be introduced
  with no declaration and exit 0. `A2` already adds three this way (`amends`, `supersedes`,
  `what_this_amendment_changes` — benign here, but the mechanism is open).
* **line 109** `ppath = os.path.join(REPO, am["amends"])` — the parent is whatever the amendment
  says it is, with **no digest pin**. The check cannot detect that the "frozen" parent moved under
  it. (A2's `amends` correctly points at `configs/dcs_ts_pr066_behaviour.json`, with
  `supersedes: amendment1` — that chain is coherent and is **not** a finding; the missing pin is.)

### 2f. The fix

Compare `canon` output **and** report, per block, the list of annotation keys that were stripped
plus a diff of their contents. An annotation that is genuinely inert produces a short, boring list;
an annotation that carries a floor produces a diff a reader can see. Refuse outright if a stripped
annotation key appears inside a block named in `void_conditions`, `kill_condition`, `primary` or
`classifier`.

---

## 3. HIGH — `ENTRY 047`'s basket `Q1b`/`Q1d` are in no script and no artifact

`ENTRY 047` publishes:

| contrast | Δ | 95 % CI | domains + | p |
|---|---|---|---|---|
| `Q1b` basket C dose 4 − dose 0 | +0.0522 | [0.0372, 0.0690] | 42/42 | 4.55e−13 |
| `Q1d` basket C dose 4 − B dose 4 | +0.0451 | [0.0301, 0.0611] | 41/42 | 1.96e−11 |

Three verified facts:

1. **`scripts/dcs_succ_pr066_behaviour.py` — the only script that computes `Q1b`/`Q1d` (lines 1456,
   1458) — has no `--codeword`, `--bank-key`, `--gen-prefix` or `--judge-prefix` argument.** Its
   full option list is `--config --selftest --mutate --plan --train-only --installation-run
   --rejudge-run --seed --n-boot --out-md --out-json` (lines 2160–2177), and its discovery pattern
   is hardcoded to `tsb66_*` (line 544). `b5ba16a4` did not touch it.
2. **There is no `outputs/dcs_succ/pr066_behaviour_basket.json`.** The directory listing at 06:47
   holds `pr066_behaviour.json` (**02:34**, i.e. two and a half hours before the basket cell-C
   dose-4 run finished) and `pr066_behaviour_train.json` (01:37). Both are button.
3. **No script in the repo computes a paired within-domain test on the concept-present channel.**
   `grep -rn asr_and_concept_present scripts/*.py` returns four files:
   `concept_presence.py` emits only a **pooled** per-arm scalar (line 197) and never a per-domain
   value; `q2_concept_present.py` builds per-domain `cp` (line 217) but only correlates it and never
   writes it out; `figures.py` reads it. `REVIEW-2`'s `C6` — *"the analyzer has no concept-presence
   field"* — is still listed **OPEN** in `ENTRY 044`, thirty minutes before `ENTRY 047` reports a
   concept-present paired contrast with a CI and a sign test.

⛔ **This is `C8` recurring, in the entry whose first paragraph claims `C8`'s lesson was applied
before it could bite again.** It is the fifth instance of the phase's named shape and the second
since `C-215` closed the previous one.

**The numbers themselves are right.** I re-derived them from the raw run directories:

```
n domains 113   pos 42   neg 0   ties 71
mean over ALL 113 domains       = 0.052212
mean over the 42 informative    = 0.140476
exact two-sided sign p = 4.547e-13   floor = 4.547e-13
```

So `Δ`, `42/42` and `p` all reproduce. But note what re-deriving them exposes:

⛔ **`Δ = +0.0522` is a mean over 113 domains printed in the same table row as a sign test over
42.** Seventy-one domains are exact ties (both zero) — counted as zeros in the effect size, dropped
from the test. The mean over the domains that actually moved is **0.1405, 2.7× larger**. The row
mixes two denominators with no note. (`Δ` and the *comparison* to button's 0.1398 are internally
consistent, since both are 113-domain pooled means — the defect is that `42/42` sits beside a number
whose `n` is 113.) "missing != zero" applies: 71 domains contributing a structural zero to the
numerator is a fact about coverage, and it belongs in the row.

---

## 4. HIGH — `F5` still has no CI band, and its scope card says it does

Task (e), and the render duty. **`C-216` reports this defect as fixed. It is not.**

`ENTRY 046`: *"2. The CI band was missing for the same reason (`ci95` vs the artifact's
`bootstrap`)"* … *"Fixed by asserting the accessors instead of defaulting."*

`dcs_succ_figures.py:143-145`:

```python
bs = r.get("bootstrap") or {}
ci = bs.get("ci95") or bs.get("ci95_domain_bootstrap") or [None, None]
los.append(ci[0]); his.append(ci[1])
```

The **outer** key was fixed (`bootstrap`). The **inner** key was guessed twice and is wrong both
times. The artifact's rung `bootstrap` block carries:

```
outputs/dcs_succ/kladder_sowk_train.json  rungs["10"]["bootstrap"]
  {'point': -7.1738, 'lo': -7.5262, 'hi': -6.7881, 'n_boot': 3000, 'caveat': '...'}
```

Keys are **`lo` / `hi`**. Neither `ci95` nor `ci95_domain_bootstrap` exists on any rung, so
`ci = [None, None]` for all fourteen, `los` is all-`None`, and line 150
`if all(v is not None for v in los)` is `False` — **`fill_between` never runs.** This is the *same
silent `.get(...) or` fallthrough* the entry says was replaced by assertions; `mean_delta` (139) and
the control band (152–155) were converted to `Refusal`s, the CI accessor was not.

**Rendered and looked at** (`reports/figures/F5_kladder_concept_free.png`, committed in `48723bfb`):
there is no shaded region anywhere on the red curve. Meanwhile the scope card, four lines down,
reads **`shaded: 95% domain bootstrap`** — a caption for a band that is not in the picture. A reader
who trusts the card will read the unbanded line as a point estimate they have been told is bounded.

Two further things visible only by opening the file:

* **the scope card overlaps the x-axis label.** `C-216` moved the card out of the axes so it could
  not cover *data*; at `(1.0, −0.42)` it now covers the *axis label*, which renders as
  `K  (the cut reaches q` — the rest is behind the box. Same class of defect, one element over.
* **the y-axis label is clipped** at the left figure edge (`mean paired delta in semantic_logod…`),
  and roughly 55 % of the canvas below the card is empty. `fig.savefig(p, dpi=200)` at line 254 has
  no `bbox_inches="tight"`.

**Fix:** `ci = bs.get("lo"), bs.get("hi")` with a `Refusal` when either is absent — the same
treatment `mean_delta` already gets — and make the scope card's "shaded" line conditional on the
band having actually been drawn.

---

## 5. HIGH — `F3`'s legend paints over `L6` and `L7`, the two layers that contradict its title

**Rendered and looked at** (`reports/figures/F3_position_layer_map.png`). `ax.legend(fontsize=6.5,
loc="upper left")` at line 116 places an opaque legend box over the top-left of both panels. The
x-axis runs `L6 … L14`. **The `L6` and `L7` points of all three curves are behind the legend box on
both panels** — only the grey `last` marker at `L6` on the button panel peeks below its bottom edge.

That is not a cosmetic loss. From `outputs/dcs_succ/b1_position_control.json`:

| | button `L6` | button `L7` | basket `L6` | basket `L7` |
|---|---|---|---|---|
| `codeword_last` mean_cos | **0.1565** | 0.1478 | **0.1486** | 0.1829 |
| `following` | 0.0772 | 0.1561 | 0.1448 | 0.2395 |
| `last` | **0.0208** | 0.1744 | **0.0410** | 0.1949 |

The panel's own `suptitle` is *"F3 B1 is NOT localised: the codeword matches its neighbour and
trails the readout position."* **At `L6` the codeword leads the readout position by 7.5× on button
(0.1565 vs 0.0208) and 3.6× on basket (0.1486 vs 0.0410).** The two layers that qualify the title
are precisely the two the legend covers.

⛔ **This is `C-216`'s finding verbatim — "the figure looked complete and had its own evidence
hidden behind a box" — recurring in the same commit that records it, with the legend in the scope
card's old role.** The lesson `C-216` drew ("rendering an artifact and opening it is a check") was
correct; it was applied to one box and not to the other one on the same axes.

Also visible: the scope card covers the x-axis label (`blo…` for `block layer`) on both panels, and
the right panel's y-label text (`POSITION-PORTABLE`) collides with the `suptitle`.

**Fix:** `loc="lower right"` or `bbox_to_anchor` outside the axes, plus `framealpha` — and, since
this is now the second instance, a rule: no opaque artist inside `ax.transAxes` on a panel that
plots a series.

---

## 6. HIGH — `F2`'s scope card paints over the labels of two of its four bars

**Rendered and looked at** (`reports/figures/F2_cell_coordinates.png`). `scope_card` at
`(1.0, −0.42)` in axes coordinates, five lines tall, `fontsize=6.2`. The x tick labels set at line
83 are three lines each (`"B\nharmful\nconcept"`, `"E\nbenign\nconcept"`). On both panels:

* the `C` label renders as `C / Doublespea` — truncated mid-word by the card's left edge;
* **the `B` and `E` labels are entirely behind the card.** Under the two blue bars there is nothing.

So the panel whose whole argument is *"C sits at 0.106 while B sits at 0.837 and E at 1.000"*
does not show the reader which bar is `B` and which is `E`. The docstring at line 59–64 asserts the
card "now lives below the axes **where it cannot cover data**" — true of the bars, false of the
labels that name them, and the label is where a bar's identity lives.

Two more, from looking:

* **no CI or error bars anywhere on `F2`**, though the module docstring (line 5) says plan §36's
  *"n independent domains; split; CI; controls; exact metric"* is *"implemented literally"*. `F2`'s
  card lists n, split and metric and silently omits CI and controls. The per-cell bootstrap exists
  in the artifact (`cell_coordinates_on_bomb_axis`).
* y-axis label clipped (`position on the button->bomb axis (gap un`), ~55 % dead canvas.

**Also (INFERRED, worth a decision rather than a fix):** line 72 hardcodes
`zip(axes, ("button","basket"), (12, 11))` — the peak layer, chosen per codeword, baked into the
figure. Neither the title nor the card says the layer was selected as the maximum rather than
declared in advance. `S-009` and claim-table row 8 read at the same two layers.

---

## 7. MED-HIGH — `F8` is not a plot, has no scope card, and states its conclusion from a string

`dcs_succ_figures.py:178-202`. The docstring (line 13) promises *"F8 per-domain installation vs
per-domain ASR, raw and concept-present ← plan Fig 8"*. **Rendered and looked at**
(`reports/figures/F8_installation_vs_asr.png`): the first statement in the function body is
`ax.axis("off")` and the panel is a monospace text block of four summary numbers. There is **no
scatter, no per-domain point, no axis, no regression line** — nothing per-domain at all. It could
not be otherwise: `q2_concept_present.json` stores only aggregated `rows`, never the 113 domain
pairs. Under the file's own doctrine (lines 15–17, *"a panel that cannot be drawn from data is not
drawn with placeholder data"*), `F8` should have refused; instead it drew a table and called itself
a figure.

Two further defects in the same function:

* **`F8` never calls `scope_card()`** — the only panel that does not, against a docstring (line 6)
  saying *"every panel draws a SCOPE CARD from the artifact it plots, and a panel whose artifact
  cannot supply one is not drawn."*
* **lines 196–198 are a hardcoded conclusion**: `"the correlation STRENGTHENS under the C-209
  correction, / which is the opposite of what a false-positive artefact would do"`. It is emitted
  unconditionally, not derived from `rows`. It happens to be true of the pooled row plotted
  (0.3961 → 0.4206); it is **false** on the test split of the same artifact (0.3779 → 0.3245) and
  false on basket's test split (0.4615 → 0.4398). A sentence that asserts the direction of an effect
  and cannot fail is `C-134`'s shape rendered at 200 dpi.

**Fix:** export per-domain `x`/`y` from `q2_concept_present.py` (it already has them in `inst`,
`raw` and `cp` at lines 236–263) and draw the scatter plan §36 asks for; derive the "strengthens"
sentence from `r2["rho"] > r1["rho"]`; add the scope card.

---

## 8. MEDIUM — a provenance field that is always `None`, added in the `C-213a` repair commit

`scripts/dcs_succ_b1_surface_floor.py:201`:

```python
"artifact_sha16_of_source": art.get("_label", "")[:0] or None,
```

`s[:0]` is `""` for every `s`; `"" or None` is `None`. **The field is the constant `None` under a
name that promises a digest of the source artifact.** Confirmed in both artifacts:

```
b1_surface_floor.json         artifact_sha16_of_source  ABSENT (pre-fix file)
b1_surface_floor_basket.json  artifact_sha16_of_source  None
```

⛔ It was introduced in `d1d6e14a` — the commit whose message is *"the integrity check I claimed to
have run did not exist"* and whose lesson is *"a constant printed as a measurement"*.

**And the button half of the `C-213e` repair was never re-run.** `b1_surface_floor.json` and
`b1_surface_floor_button.json` are both stamped **2026-09-09 22:14**; the fix landed at **02:32** and
only `b1_surface_floor_basket.json` (02:34) was regenerated. The button files carry **no `bank` key
and no `split` key at all** — the two fields `C-213e` added so "the artifact records which bank it
used". Claim-table row 11 cites `outputs/dcs_succ/b1_surface_floor_*.json` for both codewords; half
of that glob predates the fix it is cited under. (No number moves — button was always the default
bank — but the repair is half-applied and the artifact cannot show it.)

---

## 9. MEDIUM — the `B1 = H + I` assertion is vacuous; the check that would catch `C3` is not in the code

This is task (b). **The `C3` fix itself is correct — see §20.1.** The guard beside it is not.

`dcs_succ_bombness_candidates.py:468-487`:

```python
b1v.append(float(torch.dot(ca, vhat_ref)) / gref)
hv.append(float(torch.dot(ca + be, vhat_ref)) / (2 * gref))
iv.append(float(torch.dot(ca - be, vhat_ref)) / (2 * gref))
...
resid = max(abs(b1 - (h + i)) for b1, h, i in zip(b1v, hv, iv))
if resid > 1e-4:
    raise Refusal("B1 = H + I is an identity and it failed by %g ...")
```

`h + i = (⟨ca+be,v⟩ + ⟨ca−be,v⟩)/(2g) = ⟨ca,v⟩/g = b1` **by the linearity of the dot product, for
any `v` whatsoever.** The residual is bounded by float rounding alone (`2.32e−08` button,
`3.13e−08` basket). A zero vector, a random vector, the wrong concept's axis, the in-sample axis —
all give `resid ≈ 0`. **The assertion cannot fail for the reason it is written to guard, and it did
not fail during the entire period `C3` was live** (`ENTRY 039` records the identity holding to
`3.09e−08` *while* `B1` was `0.10556605` instead of `0.10444100`).

The check that *would* have caught `C3` is `interaction_decomposition[L][cell].B1 ==
metrics["B1|L…"].mean_gap_units`. It is **not in the script.** `ENTRY 043`'s *"its `B1` matches `B1`
proper to 0.00e+00 (was 1.08e−03)"* is a number read off two places in an artifact by a human, not
an assertion that can fail in public — which is `C-213a`'s complaint, one layer in.

I verified the claim independently over the full grid (2 codewords × 9 layers × 9 shift/ref cells):

```
max |interaction_decomposition.B1 - metrics.B1| = 0   (exactly, not to a tolerance)
```

So `ENTRY 043` is **true and unasserted**. Promote it: three lines inside the `L` loop, comparing to
the `metrics` entry already computed above at line 335.

**On "does the fix use LOO everywhere in the H/I block" — yes, VERIFIED.** Lines 476–477 build
`vhat_ref` per domain inside the `for d in common` loop, using
`loo_direction(delta_EA[ref_c], common, d)` — structurally identical to `B1` proper at lines
317–319. The `gref = gap[ref_c]` denominator (line 466) is the **in-sample** full-gap norm, which
matches `B1` proper's line 323 exactly, so the decomposition and the headline are on the same
convention. That convention remains the LOO-numerator/in-sample-denominator mixture `REVIEW-1`'s
`A6` flagged and `C-214` re-flagged — a standing issue, not a new one, and it is consistent between
the two here, which is what `C3` required.

---

## 10. MEDIUM — `S-009`'s headline number is in no script and no artifact

`grep -rn concentration scripts/ configs/ outputs/dcs_succ/ reports/DCS_SUCC_CLAIM_TABLE.md` →
**no matches.** There is no `concentration_ratio` field, no `projection_retained`, no
`axis_retained` anywhere. `claim_table` row 10 cites
`outputs/dcs_succ/bombness_candidates_train.json` for *"Concentration ratio … = 1.20 on button and
1.02 on basket"*; the artifact contains neither number.

It is **re-derivable** from two fields the `C4` fix did add, so this is weaker than §3 — but it is
the same shape. I re-derived it:

```
button L12:  0.09485427 / 0.10444100 = 0.90821   ÷ 0.7563529 = 1.2008    (log: 1.202)
basket L11:  0.09907    / 0.13658700 = 0.72532   ÷ 0.7078955 = 1.0247    (log: 1.025)
```

Both correct. Add `concentration_ratio` to the `residual_axis_3x3` table (three lines beside
`frac_of_axis_orthogonal_to_the_other_two`, which is already the denominator) so row 10's cited
artifact contains row 10's number.

---

## 11. MEDIUM — a declared-and-unchanged block classifies `IDENTICAL`, silently

`classify()` (lines 61–69) tests, in order: `IDENTICAL` → `ANNOTATED` → `k in declared` →
`UNDECLARED DRIFT`. So a block listed in `_blocks_this_amendment_changes` that is **byte-identical
to its parent** falls out as `IDENTICAL` with no note that a declaration was made about it.

`A2` already exercises this: `_blocks_this_amendment_changes` names **ten** blocks; the run reports
**7 DECLARED**. The three that vanish are `status` (declared *"unchanged value FROZEN, listed for
completeness"* → `IDENTICAL`), `classifier` and `nulls_required` (→ `ANNOTATED`, §2c).

⛔ **That is exactly `C-213b`.** `A1` declared `things_that_must_not_be_said` changed and left it
byte-identical; the tool built to repair that would have printed `IDENTICAL` and exited 0. The check
verifies "no undeclared change"; it does not verify "every declared change was made", and `C-213b`
was a failure of the second kind.

**Fix:** after `classify`, refuse on `set(declared) - {k for k,s,_ in rows if s == "DECLARED"}`
being non-empty — a declaration that produced no drift is a false statement in a frozen document.

---

## 12. MEDIUM — a `DONE.json` gate in the figure script that gates nothing

`dcs_succ_figures.py:49-53` defines `one_done()`. `grep -n "one_done" scripts/dcs_succ_figures.py`
→ lines **49** (definition) and **219** (selftest). **No panel calls it.** All four panels take
their input from `need(art)` (line 251), a plain `os.path.exists`.

The selftest prints `one_done refuses when nothing matches   PASS`, which reads as evidence that the
figure set is gated on completed runs. It is not — every panel reads a **derived JSON artifact**, and
whether *that* artifact was produced from a completed run is whatever the upstream script enforced.
With the basket K ladder live at 11/27 arms as I write, `F5` pointed at a partial basket ladder
would refuse only via the `len(ks) != 14` check at line 146 — which is a real gate, and the
`DONE.json` one is decoration. Either wire `one_done` in or delete it and the selftest line; a
`PASS` on an uncalled function is a green light for a check that is not running.

Related, same file: **line 258 `except Exception as e:`** converts every bug — `KeyError`,
`TypeError`, `IndexError` — into a printed `REFUSED` line, and **line 263 `return 0 if drawn else 1`**
exits 0 as long as *one* panel drew. A panel silently missing from the set is a success.

---

## 13. MEDIUM — three refusals that cannot fire for the case they appear to guard

Task (f).

* **`q2_concept_present.py:213-214`** — `if r["prompt_id"] not in gens: raise Refusal("judge row %s
  absent from the generation run")`. With id sets identical across banks (§1a), this cannot fire for
  the cross-bank binding it looks like it guards; within a bank it is subsumed by the count check at
  219. It reads, in review, as protection that does not exist.
* **`concept_presence.py:179-188`** — same, and this one carries a four-line explanatory `status`
  string about `REVIEW-2 C5` that makes it look like the stronger check it is not.
* **`concept_presence.py:178` `if jrows:`** — a judge directory with `DONE.json` and an **empty**
  `results.jsonl` yields `jrows == {}`, the whole ASR block is skipped, and the arm is written with
  `"status": "ok"` and **no** `asr_at_0.5_as_published` / `asr_and_concept_present` keys. Exit 0, no
  message. That is a gate passing on an empty selection: the arm's outcome is *absent*, and absence
  in this artifact is indistinguishable from "this arm has no judge run yet". `missing != zero`
  holds for the value but not for the reader.

---

## 14. MEDIUM — `--out` never follows the codeword, in all three parameterised scripts

* `concept_presence.py:123` → `outputs/dcs_succ/concept_presence.json`
* `q2_concept_present.py:188` → `outputs/dcs_succ/q2_concept_present.json`
* `b1_surface_floor.py:136` → `outputs/dcs_succ/b1_surface_floor.json`

Every one is a fixed path that does **not** derive from `--codeword` / `--bank-key` / `--gen-prefix`.
A basket re-run with the four prefix flags set and `--out` forgotten overwrites the button artifact
in place. The button `q2_concept_present.json` is the artifact `F8` plots and the artifact
`ENTRY 042`'s ρ table cites. Derive the default `--out` from the codeword, or refuse to overwrite an
existing artifact whose recorded `bank_key` differs from the current one.

(Note the button `q2_concept_present.json`, written 03:36, predates `b5ba16a4` and therefore has
**no `bank_key` and no `gen_prefix` field at all** — only basket's does. The button artifact cannot
say which bank it used; the same staleness as §8.)

---

## 15. LOW-MED — the position control writes a partial artifact and then crashes

`dcs_succ_b1_position_control.py`. If any of the three positions raises `Refusal` at line 138, it is
recorded in `metas` and **omitted from `got`**; the run continues. Line 142 intersects over whatever
survived, line 156's loop is `[n for n in got if n != "codeword_last"]`, and line 157's
`if "codeword_last" not in got: continue` skips every paired contrast. The JSON is then written at
**line 185** — a two-position artifact with no contrasts and no top-level status flag — and only
*afterwards* does the summary at **line 203** hit `row["codeword_last"]["mean_cos"]` and raise
`KeyError`. Net effect: a partial artifact on disk, a traceback on stderr, and a non-zero exit that
does not say the artifact is partial. `_this_is_the_portable_one` is absent from the file, so a
downstream reader (`F3` at `figures.py:108`) fails on `KeyError` rather than on a refusal.

Refuse before writing when `len(got) != len(POSITIONS)`, or stamp
`"status": "PARTIAL — positions refused: [...]"` at the top of `res`.

---

## 16. LOW — `F5`'s scope card is a string literal, not read from the artifact it plots

`dcs_succ_figures.py:167-171`. Every line is hardcoded: `"n = 67 TRAIN domains, 670 rows/arm"`,
`"readout: semantic_one_word (concept word on 0 of 32544 rows)"`, `"shaded: 95% domain bootstrap"`,
`"shape rule returns NEITHER"`. The artifact supplies all of these:
`population.n_domains_declared`, `population.n_rows_per_arm`, `readout.query_kind`, `shape`. The
docstring (line 6) says every panel draws its card *"from the artifact it plots"*.

They happen to be right for the button ladder. **The basket K ladder is running as I write (11/27
arms at 06:43).** Pointed at `kladder_sowk_basket_train.json`, this card will print button's
scope over basket's curve, and — per §4 — will still claim a shaded band. This is one commit away
from being wrong on live data.

---

## 17. LOW — `EXCLUDED` reimplemented in a file whose docstring says it imports

`q2_concept_present.py:47` `EXCLUDED = ("restaurant_kitchen", "school_campus", "subway_station")`
duplicates `bombness_candidates.py:72 EXCLUDED_DOMAINS`. Currently identical (verified), and both
match the prereg's population block. The docstring's claim is *"imports … rather than reimplementing
either"* — true of `concept_binary_prob` and `concept_hits`, false of the exclusion set, which is the
thing that decides `n`. `from dcs_succ_bombness_candidates import EXCLUDED_DOMAINS as EXCLUDED`.

---

## 18. LOW — `--bank` is still independently settable against `--codeword`

`b1_surface_floor.py:134-149`. The `C-213e` repair makes `--bank` *default* from `--codeword`, but
an explicit `--codeword basket --bank <button path>` still runs, with no cross-check — exactly the
state that produced the original defect, now one flag away instead of zero. The artifact records
`bank`, so it is detectable after the fact. Refuse when `--bank` is given and its basename does not
contain `--codeword`.

---

## 19. LOW — the `C4` patch moved the shared RNG stream; CIs across the artifact shifted

`bombness_candidates.py:538` adds `boot_ci(in_full, rng)` inside the per-layer loop, drawing from the
same `rng` every later bootstrap in the run consumes. Consequences:

* `ci95` and `ci95_in_FULL_gap_units` on the **same numbers** are not proportional. Button L12
  `bomb/bomb`: rescaling `ci95` by `resid_norm/full_gap_norm = 0.7563529` gives
  `[0.0832469, 0.1064036]`; the artifact prints `[0.0832358, 0.1064162]`. Different resamples of the
  same linear transform of the same data — harmless, but it invites a reader to treat them as
  independent evidence.
* Downstream CIs in the artifact moved when `C4` landed. Diffing `31b6f7e8^` against HEAD, button
  L12 `controls.harm_context_at_concept_token_gap_units.ci95` went
  `[-0.17457541, -0.14927353] → [-0.17442530, -0.14904064]` with `mean` and `sd` **byte-identical**.
  ✅ The `random_unit_gap_units` control — the source of claim-table row 8's *"~14 sd over 12 random
  directions"* — is **unchanged**, so no published number moves. Recorded because an artifact whose
  CIs shift under an edit that changed no statistic is not reproducible from its seed, and a future
  reviewer diffing this file will chase it.

**Fix:** rescale the existing bootstrap rather than redrawing —
`ci95_in_FULL_gap_units = [v * rnorm_c / gap[ref_c] for v in ci95]` — which is both exact and
stream-neutral.

---

## 20. What I checked and found CORRECT

Recorded so the next reviewer does not redo it.

**20.1 `C3` is really fixed, and LOO really is used throughout the H/I block.** Lines 476–477
construct the axis per held-out domain, inside the domain loop, from `loo_direction` — identical in
form to `B1` proper (317–319), same `gap[ref_c]` denominator (466 vs 323). Numerically, over
2 codewords × 9 layers × 9 shift/ref cells:

```
max |interaction_decomposition[L][cell].B1 - metrics["B1|L…"].mean_gap_units| = 0
```

button L12 `B1 = 0.1044410042` in both places (was `0.10556605`); `H = −0.028732` (13/67),
`I = +0.133173` (67/67), `I/B1 = 1.2751`. basket L11 `H = −0.0029`, `I = +0.1395` (67/67),
`I/B1 = 1.0211`. `ENTRY 043`'s "128 % / 102 %" and "H negative, 13/67" reproduce.
⚠ The *assertion* beside this is vacuous — §9.

**20.2 `C4`'s conversion arithmetic is exact.** Over the same grid,
`max |mean_resid_units × resid_norm / full_gap_norm − mean_in_FULL_gap_units| = 1.39e−17`
(float noise). Button L12 `bomb/bomb`: `0.1254100673 × 2.9193807 / 3.8598127 = 0.09485427`, against
`B1 = 0.10444100` → `0.908212`, a **9.2 % reduction**. `ENTRY 042`'s inline `0.094847` is the same
figure recomputed from rounded inputs and is off in the 5th decimal (artifact: `0.09485427`); the
9.2 % / 0.9081 reading is unaffected. `resid_norm`, `full_gap_norm`,
`frac_of_axis_orthogonal_to_the_other_two` and `_WHICH_COLUMN_IS_COMPARABLE_TO_B1` are all present
on every cell, as `ENTRY 042` claims. ⚠ CI redraw — §19.

**20.3 `S-008`'s entire table reproduces from `b1_position_control.json`.** Every cell of `ENTRY
041`'s two contrast tables checked: button `L9 −0.006 36/67 p=0.625`, `L11 +0.029 44/67 p=0.0139`,
`L12 +0.019 42/67 p=0.0498`, `L13 +0.011 42/67 p=0.0498`; `last`-contrasts `−0.225/−0.091/−0.203/
−0.120` at `1,8,2,5 / 67`; basket likewise. The raw-projection sentence reproduces too (button L12
`0.4031 / 0.2876 / 0.3385`; basket `0.5586 / 0.4701 / 0.3782`). `ENTRY 040`'s pre-correction raw
table also reproduces. The `cos` statistic **is** scale-free in both terms and is the right choice.
⚠ One caveat the claim table does not carry: at the codeword `v_lex` is a *token-substitution*
direction and at `following`/`last` it is a *context-propagation* direction. The script's docstring
(19–23) and `ENTRY 038` both say so; claim-table row 7 states the negative flatly. Not a code defect.

**20.4 `R-207`'s `Q2` is correctly bound.** `q2_concept_present_basket.json` records all four
parameters on basket — `bank_key basket_bomb`, `gen_prefix tsb66b_`, judge
`tsb66bj_C_n4_20260910_050209_3469931`, gen `tsb66b_C_n4_20260910_020713_3997666`, predictor
`ts116m_readout_basket_bomb_20260907_152329_3191150` bound by sha `79511d9e254571e6`. Every number in
`ENTRY 047`'s `Q2` table matches: pooled 113 `+0.4468 / +0.4868` at the `9.999e−05` floor, train 67
`+0.5262 / +0.5400`, validation 23 `−0.0733 / +0.0971`, test 23 `+0.4615 p=0.0278 / +0.4398 p=0.034`.
The null validation split is printed unconditionally, as claimed.

**20.5 The bank digests match the prereg pins.** The banks are untracked (`git status ??`), so I
recomputed: `sha256 | cut -c1-16` gives `dcd92d723f3e6d00` (button) and `79511d9e254571e6` (basket),
both 22272 lines — identical to `configs/dcs_ts_pr066_amendment2.json`'s
`population.banks.*.bank_file_sha16`.

**20.6 `R-207`'s basket `Q1` pooled numbers all reproduce** from `concept_presence_basket.json`:
C dose 4 raw `0.161062` / cp `0.052212`; C dose 0 raw `0.022124` / cp `0.000000`; B dose 4 cp
`0.007080`; `57/113` domains with concept content. `ENTRY 042`'s codeword-dependent floor (0.1549 vs
0.0221, 7×) is right. ⚠ The *paired contrasts* built on these are §3.

**20.7 The amendment chain is coherent.** `A1` and `A2` both `amends`
`configs/dcs_ts_pr066_behaviour.json`; `A2` additionally `supersedes` `A1`. `A2` is not an edit to a
frozen file, and the "grandparent" reading I initially suspected is wrong. The **holes are in what
the checker does with that chain** — §2, §11.

**20.8 `C-216`'s `%%` defect is genuinely fixed** — `F5`'s title renders `62%` and `F2`'s renders
correctly.

**20.9 `ENTRY 045`'s "NOT SENT" is consistent with the tree.** `reports/DCS_SUCC_SLACK_DRAFT_MATAN_
MAHMOOD_20260910.md` is a committed file; nothing in the diff touches a transport.

---

## The pattern, since the log is keeping score

`ENTRY 044` names the phase's recurring shape as *"a quantity that could not have told you it was
wrong"* and counts three instances (`C-134`, `C-213a`, `C-214`), with `C-216` added as a fourth.
This review adds four more, all inside the four entries that named the shape:

* **§3** — basket `Q1b`/`Q1d` published with no script and no artifact, in the entry claiming `C8`'s
  lesson was applied. (`C-213a`'s shape, 5th instance.)
* **§8** — `artifact_sha16_of_source` is `None` by construction, added in the commit repairing
  `C-213a`. (`C-134`'s shape, 4th instance.)
* **§9** — an assertion that is true for every possible input, guarding the axis whose error it
  failed to catch. (New sub-shape: *a check that cannot go red*.)
* **§4, §5, §6** — the figure fixed for hiding its evidence still hides its evidence, in three
  panels, behind three different boxes. (`C-216`'s shape, immediately.)

And one shape the log has not named. `C8`'s repair was *parameterise, don't copy*. §1 shows that
parameterising **without binding the parameters to one another** is a new failure mode, not the
absence of the old one: four unbound flags in one script and two in the other, and I ran two of the
mixed settings — button generations against basket's judge, and basket's predictor against button's
outcome — **both silently, both at exit 0, one of them producing a number within 5 % of the
published one.** The transfer-pair rule (`PR-059`)
is currently enforced by the operator typing four flags consistently. It should be enforced by the
`bank_file_sha16` that both sides already carry.
