# DCS-SUCC-S002 — Independent re-verification of the B1 "bombness" candidate

**Status: EXPLORATORY, TRAIN ONLY (67 domains). Nothing here is confirmatory. No TEST row was read.**

**Verdict in one line: every reported number reproduces, to six decimals, along a code path written
from the prose description without reading the original script or artifact. No arithmetic error.
Two reporting defects and one control that cannot fail are recorded in §7, and §8 argues the
quantity, though correctly computed, does not support the reading its name implies.**

Author: independent re-derivation (S002). Date: 2026-09-09.
Independence protocol: `scripts/dcs_succ_bombness_candidates.py` and
`outputs/dcs_succ/bombness_candidates_train.json` were opened only AFTER every number in §2–§5 was
already written to `/tmp/.../res_bomb.json`, `adv_*.json`. §6–§8 are the post-hoc comparison.

---

## 1. What was selected, and the guards that had to pass

Frozen manifest `data/boombness_prompts/dcs_ts116_domain_split.json`, `manifest_sha16
be7d2c772d814ef3` — re-read and re-hashed independently; 116 domains, 70/23/23.
All three preregistered whole-population exclusions (`restaurant_kitchen`, `school_campus`,
`subway_station`) are **train** domains, so analysed train = 70 − 3 = **67**. Matches.

Selection: `query_kind == "semantic_one_word"`, `n_examples == 4`, `cell ∈ {A,B,C,E}`,
`position == "codeword_last"`, domain ∈ analysed train.

| guard | result |
|---|---|
| rows selected per bank | 2680 |
| rows per cell (A / B / C / E) | 670 / 670 / 670 / 670 |
| distinct `(family_id, cell)` keys | 2680 — **equals row count**, so the dev/heldout trap did not fire |
| family slots per domain | 10 (5 `dev` + 5 `heldout`), identical for every domain and every cell |
| `bank_file_sha16` constant within a bank | yes — `dcd92d723f3e6d00` (button_bomb), `79511d9e254571e6` (basket_bomb), and distinct between banks |
| rep present for every selected `prompt_id` | yes (a missing rep raises, it does not default to zero) |
| layers header in `final_occurrence_reps.pt` | `[6..14]`, `position="codeword_last"` |

**The dev/heldout trap, checked explicitly.** My key is the *full* `family_id` plus `cell`.
Collapsing field 1 (`dev`/`heldout`) is demonstrated inside the selftest to halve a synthetic
selection 8 → 4, and the live count 2680 = 67 × 10 × 4 confirms nothing collapsed. Had field 1 been
dropped, the live count would have been 1340.

**An incidental data fact worth recording.** In `ts116m_basket_bomb`, three `school_campus`
families (`dev|slot0`, `dev|slot8`, `dev|slot12`) carry only cells **B** and **E** — no A, no C.
They are inside a preregistered exclusion so they never reach any analysis, but a domain-completeness
guard is doing real work here, not hypothetical work.

**Positional structure of the contrast (checked, not assumed).** For all 1160 `semantic_one_word`
n=4 families in the button bank, cells **A and E have identical `seq_len` and identical `token_pos`**.
The E−A contrast is therefore a *pure single-token substitution* (` button` → ` bomb`) in an
otherwise byte-identical benign prompt. Cell C differs in `seq_len`/`token_pos` from A in 1108 of
1160 families (the harmful demonstrations are a different length). This matters for §8.

---

## 2. The headline numbers

Everything below is computed in float64 from the float16 reps, domain-mean over the 10 family slots,
leave-one-domain-out reference axis.

**A note on one ambiguity in the claim text.** "`/ || mean_d (h_E - h_A) ||`" does not say whether
that norm is the leave-one-out mean's norm or the full-sample mean's norm. I computed **both**.
They differ in the 5th decimal. Both round to the claimed value.

### ts116m_button_bomb, layer 12

| quantity | claimed | mine (LOO-norm denom) | mine (full-sample-norm denom) | verdict |
|---|---|---|---|---|
| mean B1 | 0.1044 | **0.104449** | **0.104441** | **VERIFIED** |
| CI95 | [0.0955, 0.1135] | bootstrap [0.095591, 0.113366]; t [0.095309, 0.113589] | — | **VERIFIED** |
| domains positive | 66 of 67 | **66 of 67** (the negative one is `film_studio`, −0.00536) | same | **VERIFIED** |
| paired d | 2.79 | 2.7875 | **2.7897** | **VERIFIED** |
| sign test | — | p = 9.22e-19, **floor 1.36e-20** (n=67) | | reported beside its floor |

### ts116m_basket_bomb, layer 11

| quantity | claimed | mine (LOO-norm denom) | mine (full-sample-norm denom) | verdict |
|---|---|---|---|---|
| mean B1 | 0.1366 | **0.136596** | **0.136587** | **VERIFIED** |
| CI95 | [0.1269, 0.1459] | bootstrap [0.126884, 0.146160]; t [0.126696, 0.146496] | — | **VERIFIED** (upper end differs by 6e-4, i.e. bootstrap seed noise; see §7.4) |
| domains positive | 67 of 67 | **67 of 67** | same | **VERIFIED** |
| paired d | 3.37 | 3.3655 | **3.3682** | **VERIFIED** |
| sign test | — | p = 1.36e-20 = **floor** (n=67) | | at the attainable floor; the data cannot say more |

### The layer chosen is in fact the argmax, in both banks

| L | button_bomb, mine | basket_bomb, mine |
|---|---|---|
| 6 | 0.065600 | 0.057841 |
| 7 | 0.067827 | 0.075590 |
| 8 | 0.077503 | 0.092445 |
| 9 | 0.086546 | 0.102981 |
| 10 | 0.083011 | 0.109372 |
| 11 | 0.100089 | **0.136596 ← reported** |
| 12 | **0.104449 ← reported** | 0.133326 |
| 13 | 0.098837 | 0.121546 |
| 14 | 0.069617 | 0.079346 |

Both reported layers are the per-bank maximum. **VERIFIED**, and flagged: a maximum over 9 layers
selected on TRAIN is a selection, and the *layer* is a free parameter that TEST replication must
inherit rather than re-optimise.

---

## 3. Random-direction control

Claimed: 0.0015 ± 0.0072 (button) and 0.0009 ± 0.0098 (basket), 12 draws.

The statistic is deterministic in the drawn direction: `mean_d <h_C−h_A, r> / ||axis||` collapses to
`<g, r>/||axis||` with `g = mean_d (h_C − h_A)`. So its distribution over random unit `r` is exactly
Normal with sd `||g|| / (sqrt(4096) · ||axis||)`. I therefore report the **analytic** null as well as
12 draws, because 12 draws estimate a standard deviation to only ±21%.

| bank / layer | ‖g‖ | ‖axis‖ | **analytic sd** | 20 000-draw sd | my 12 draws | claimed 12 draws | observed effect, in sd |
|---|---|---|---|---|---|---|---|
| button_bomb L12 | 2.0965 | 3.8598 | **0.00849** | 0.00842 | 0.00275 ± 0.00638 | 0.0015 ± 0.0072 | **12.3 σ** |
| basket_bomb L11 | 2.0578 | 3.8544 | **0.00834** | 0.00831 | −0.00465 ± 0.00768 | 0.0009 ± 0.0098 | **16.4 σ** |

**VERIFIED in substance.** The seed differs, so the 12 individual draws cannot match and do not.
All four sample sds (0.0072, 0.0098, 0.0064, 0.0077) are consistent with the analytic 0.0084 at
n=12. Nothing here is off. The effect is 12–16 analytic sd from the isotropic null.

---

## 4. Harm-context contrast

Claimed: `<h_B − h_E, v_lex_hat> / ‖·‖` is negative, "about −0.16 and −0.14".

| bank / layer | claimed | mine (LOO denom) | mine (full denom) | domains positive | verdict |
|---|---|---|---|---|---|
| button_bomb L12 | ≈ −0.16 | −0.161930 | **−0.161906** | 0 of 67 | **VERIFIED** |
| basket_bomb L11 | ≈ −0.14 | −0.142352 | **−0.142338** | 0 of 67 | **VERIFIED** |

---

## 5. `‖h_A(bomb bank) − h_A(knife bank)‖ = 0` at every layer

Joined on `(family_id, cell="A")` — never on `prompt_id`, which is not unique across banks. The two
banks' `bank_file_sha16` were asserted **different** (`dcd92d723f3e6d00` vs `94fd300d611fccf2`), so
this is not a file compared with itself. 670 train families.

| L | max per-row L2 diff | mean per-row L2 diff | max abs element diff | mean ‖h_A‖ |
|---|---|---|---|---|
| 6 | 0.00000000 | 0.00000000 | 0.00000000 | 5.3293 |
| 7 | 0.00000000 | 0.00000000 | 0.00000000 | 5.7345 |
| 8 | 0.00000000 | 0.00000000 | 0.00000000 | 6.3409 |
| 9 | 0.00000000 | 0.00000000 | 0.00000000 | 6.8188 |
| 10 | 0.00000000 | 0.00000000 | 0.00000000 | 7.6456 |
| 11 | 0.00000000 | 0.00000000 | 0.00000000 | 8.2643 |
| 12 | 0.00000000 | 0.00000000 | 0.00000000 | 8.2786 |
| 13 | 0.00000000 | 0.00000000 | 0.00000000 | 9.0427 |
| 14 | 0.00000000 | 0.00000000 | 0.00000000 | 9.6529 |

`numpy.all(diff == 0)` is `True` over the whole `[670, 9, 4096]` tensor: **bit-identical**, not
merely small. **VERIFIED.** The mean ‖h_A‖ column is there so the zero is read against a scale.

---

## 6. Reconciliation with the original (opened only at this point)

`scripts/dcs_succ_bombness_candidates.py` uses `gap[ref_c] = ‖ mean over ALL train domains of
(h_E − h_A) ‖` as the denominator, and leave-one-out **only for the direction**. That is my
"full-sample-norm denom" column. Under that convention my independent numbers agree with the
artifact **to every printed digit, at all nine layers, in both banks**:

| L | button_bomb: mine (full denom) | artifact | basket_bomb: mine (full denom) | artifact |
|---|---|---|---|---|
| 6 | 0.065590 | 0.065590 | 0.057833 | 0.057833 |
| 7 | 0.067820 | 0.067820 | 0.075585 | 0.075585 |
| 8 | 0.077498 | 0.077498 | 0.092439 | 0.092439 |
| 9 | 0.086541 | 0.086541 | 0.102975 | 0.102975 |
| 10 | 0.083002 | 0.083002 | 0.109363 | 0.109363 |
| 11 | 0.100079 | 0.100079 | **0.136587** | **0.136587** |
| 12 | **0.104441** | **0.104441** | 0.133318 | 0.133318 |
| 13 | 0.098829 | 0.098829 | 0.121539 | 0.121539 |
| 14 | 0.069611 | 0.069611 | 0.079338 | 0.079338 |

Secondary quantities, likewise exact:

| quantity | mine | artifact |
|---|---|---|
| button L12 `ref_gap_norm` | 3.859813 | 3.859813 |
| button L12 `mean_proj` | 0.4031 | 0.4031 |
| button L12 `mean_cos` | 0.1327 | 0.1327 |
| button L12 `d_paired` | 2.7897 | 2.7897 |
| basket L11 `ref_gap_norm` | 3.854366 | 3.854366 |
| basket L11 `mean_proj` | 0.5265 | 0.5265 |
| basket L11 `mean_cos` | 0.1787 | 0.1787 |
| basket L11 `d_paired` | 3.3682 | 3.3682 |
| cos(v_lex bomb, v_lex knife) button L12 | 0.4419 | 0.44188 |
| cos(v_lex bomb, v_lex gun) button L12 | 0.6478 | 0.64785 |
| cos(v_lex knife, v_lex gun) button L12 | 0.5667 | 0.56675 |
| harm-context, button L12 | −0.161906 | −0.161906 |
| harm-context, basket L11 | −0.142338 | −0.142338 |

**No arithmetic discrepancy of any size.** The original computes in float32; I recomputed the whole
headline in float32 and float64 and the two agree to all six printed decimals, so precision is not
carrying anything.

Method differences that are real but immaterial:

1. **Pairing key.** Original: `(cell, domain, "|".join(family_id.split("|")[1:-1]))`. Mine:
   `(family_id, cell)`. Equivalent, since field 0 is the domain and field −1 is the (constant)
   `query_kind`. Both keep the `dev`/`heldout` field. Both refuse on a duplicate key.
2. **Denominator.** Discussed above; the two conventions differ by ≤ 1e-5 in the mean.
3. **Leave-one-out is nearly cosmetic.** I computed the in-sample (non-LOO) value as a diagnostic:
   button L12 0.105566 vs LOO 0.104441; basket L11 0.137495 vs 0.136587. LOO removes about **1.0 %
   of the effect**. Averaging a direction over 67 domains makes each domain's own contribution tiny,
   so LOO is buying very little protection here. It is right to have it; it should not be cited as
   the thing that makes the result non-circular.
4. **Cross-concept transfer.** My first pass scored bank X's shift on bank Y's *full* axis; the
   original uses the LOO axis even off-diagonal. This matters more than it does on the diagonal —
   my 0.03860 vs the original's 0.037529 for `shift_bomb|ref_knife` at button L12 — because cells A
   are *shared across banks* (§5), so `h_C(bomb) − h_A` and `h_E(knife) − h_A` share the `h_A` term
   and leaving the domain out breaks a real shared-noise correlation. The original's handling is the
   correct one. Not a discrepancy in the claim; a discrepancy in my first pass, resolved in the
   original's favour.

---

## 7. Defects found

### 7.1 `n_selected_rows` in the artifact is not the number of rows analysed — **reporting defect**

`bombness_candidates_train.json` publishes `"n_selected_rows": 4520` and `"n_rows": 4520` per bank,
directly beside `"n_train_domains": 67`. 4520 = 113 analysed domains × 10 slots × 4 cells. The
number of rows the metrics were computed on is **2680** = 67 × 10 × 4. `load_bank` selects all 113
analysed domains and `domain_cell_means` filters to train afterwards, so the analysis is correct —
but a reader who divides 4520 by 67 gets 67.5 rows per domain and either concludes the file is
inconsistent or, worse, quotes 4520 as the sample size. It should read 2680, or be renamed
`n_rows_selected_before_split_filter`.

Consequence for the house rule about TEST: the script *reads* the validation and test domains'
rows and reps into memory, and never computes any statistic on them. No leakage occurred. But the
artifact gives no way to see that from the outside, which is exactly the situation the rule exists
to avoid. Recommend the script filter to the requested split at selection time and report 2680.

### 7.2 The `domain_shuffled_ref` control cannot fail — **a gate that is not a gate**

C2 permutes which domain's `(h_E − h_A)` sits in which slot, then takes the LOO mean excluding
slot `d`. But `mean_{d'≠d} delta[perm[d']] = (Σ_all delta − delta[perm[d]]) / 66`: permuting only
changes *which single domain* is dropped from a 67-term mean. The shuffled axis is therefore the
full axis to within one 67th, and the projected domain is now *inside* it. The control is
mathematically obliged to return approximately the **in-sample** value, which is ≥ the real value:

| bank / layer | real (LOO) | shuffled control | my independently computed in-sample value |
|---|---|---|---|
| button L12 | 0.104441 | 0.105600 | 0.105566 |
| basket L11 | 0.136587 | 0.137465 | 0.137495 |

It agrees with the in-sample value to 3e-5, as predicted. So C2 measures the LOO leakage (1.0 %,
§6.3) — genuinely useful — but it is **not a null control** and cannot produce one. Sitting in a
`"controls"` block next to `random_unit_gap_units`, whose job *is* to produce a null, it invites the
reading "we shuffled and the effect survived". Rename it `loo_leakage_probe` or move it out of
`controls`. The script's own comment ("it is not a test of 'is 4096-d chance small'") is honest but
does not go far enough: it is not a test.

### 7.3 The random-direction control is under-powered for the ± it prints

12 draws estimate a standard deviation to about ±21 % (§3). Printing `0.0015 ± 0.0072` next to
`0.0009 ± 0.0098` invites reading a difference between two banks that is pure sampling noise — the
analytic sds are 0.00849 and 0.00834, i.e. the same. The analytic value is free (`‖g‖ /
(64·‖axis‖)`) and should be printed instead of, or beside, 12 draws.

### 7.4 Bootstrap CIs are drawn from one shared RNG consumed sequentially

`boot_ci(vals, rng)` shares one `random.Random(seed)` across all 90 metrics × 9 layers × 2 codewords
in file order, so no individual CI is independently reproducible — changing an unrelated metric
shifts every later CI. This is cosmetic (my independent bootstrap lands within 6e-4 of the
artifact's, and the t-interval lands within 3e-4 of both), but it means "re-run and get the same
CI" only holds if nothing upstream changed.

### 7.5 Not a defect, but under-reported: the layer is a selected parameter

§2 shows both reported layers are the argmax over 6..14 on TRAIN. The artifact reports all nine
layers, so nothing is hidden, but the summarised claim quotes only the maximum. Any TEST
replication must inherit L=12 (button) / L=11 (basket) as frozen.

---

## 8. Is the reference axis measuring "bombness"? — the substantive objection

The numbers are right. The name is the problem.

**8.1 By construction, `v_lex` is a token-substitution vector, not a concept vector.** I verified
(§1) that cells A and E have *identical* `seq_len` and *identical* `token_pos` in every family. E is
A with one word swapped everywhere the codeword appears, in benign demonstrations. So `h_E − h_A` is
"the token here is ` bomb` rather than ` button`, in an otherwise identical benign hardware-store
context". That bundles at least four things: the semantics of *bomb*; its unigram statistics; the
model's surprise that a weapon word is sitting in an apiary-supply demo; and the norm/anisotropy
direction of the residual stream. `v_lex` is a perfectly good name. "Bombness" is not.

**8.2 The decisive test is already in the original's own 3×3, and the summarised claim omits it.**
The script computes `shift_c × ref_c` for all nine combinations. I reproduced the diagonal
independently. If B1 measured "the codeword acquires the demonstrated concept", the diagonal should
be positive for all three concepts. It is not:

| codeword | layer | shift_bomb·ref_bomb | shift_knife·ref_knife | shift_gun·ref_gun |
|---|---|---|---|---|
| button | 12 | **+0.1044** (66/67 pos) | +0.0134 (47/67) | **−0.0163** (22/67) |
| basket | 11 | **+0.1366** (67/67 pos) | +0.0220 (44/67) | +0.0051 (34/67) |

*(my independent values: button knife +0.01344, gun −0.01623; basket knife +0.02200, gun +0.00510 —
matching the artifact.)* **Knife is at the noise floor and gun is negative.** Doublespeak
demonstrations using *knife* do not move the codeword toward *knife*.

**8.3 Every concept's shift points toward `bomb`.** Off-diagonal, at button L12:

| | ref_bomb | ref_knife | ref_gun |
|---|---|---|---|
| shift_bomb | **+0.1044** | +0.0375 | +0.0571 |
| shift_knife | **+0.0237** | +0.0134 | −0.0371 |
| shift_gun | **+0.0396** | +0.0253 | −0.0163 |

For the button codeword, `ref_bomb` is the *largest* column entry for **all three** shifts — knife's
shift aligns with the bomb axis (+0.024) about twice as well as with its own (+0.013), and gun's
shift aligns with the bomb axis (+0.040) while being *negative* on its own (−0.016). This is the
signature of "harmful-instruction demonstrations push the queried token toward a generic
danger/explosives region of the residual stream, and ` bomb` happens to be the token nearest that
region", **not** of "the codeword is bound to the concept that was demonstrated". The cross-concept
specificity that would license the word "bombness" is absent, and the file contains the evidence.
(The basket family is weaker on this point — `shift_knife·ref_bomb` there is −0.010 — so the pattern
is not uniform across codewords, which is itself a reason not to over-read either direction.)

**8.4 `B1resid` partly answers 8.3, and should be extended.** The artifact Gram-Schmidts the bomb
axis against span{knife, gun} — 24.4 % of the bomb axis is expressible by the other two (button L12,
`frac_kept` 0.7564) — and finds 0.1254 residual units, i.e. 0.1254 × 2.9194 = 0.366 of the original
0.403 projection, ~91 %, survives. So the alignment is genuinely in the bomb-specific part of the
axis. That is a real and useful result. But `B1resid` is computed **only for `shift_bomb`**. The
missing rows — `shift_knife` against knife-minus-{bomb,gun}, `shift_gun` against gun-minus-{bomb,knife}
— are exactly what would tell you whether "the shift lands in the concept-specific part of the axis"
is a general property or a bomb-only one. On the evidence of 8.2 it will be bomb-only. That
computation costs nothing and should be run before this candidate is promoted.

**8.5 Two confounds that are adequately handled, recorded so they are not re-raised.**
- *Position/length.* Cell C is one token later than A in 1108/1160 families, while E sits exactly on
  A. A pure position artefact would be a plausible source of a spurious `<h_C − h_A, v_lex>`. It is
  ruled out by the harm-context control: `h_B − h_E` carries the *same* +1 position shift and the
  *same* harm-demonstration context, and its projection is **−0.16**, not +0.10.
- *Norm / anisotropy.* I checked `cos(v_lex, global mean hidden state)` = −0.125 (button L12) and
  −0.097 (basket L11) — the axis is nearly orthogonal to the dominant anisotropy direction — and the
  projection of `h_C − h_A` on that global-mean direction is +0.013 and +0.023 gap-units, 5–10x
  below the effect. Not a norm artefact.

**8.6 The effect is small in absolute terms, and the "gap units" framing flatters it.** Reading the
positions of all four cells on the button→bomb axis (mine, button L12 / basket L11):

| coordinate on `v_lex` (gap units) | button L12 | basket L11 |
|---|---|---|
| A (benign, codeword) | 0.000 | 0.000 |
| **C (doublespeak, codeword)** | **0.104** | **0.137** |
| B (harmful, concept) | 0.836 | 0.855 |
| E (benign, concept) | 0.998 | 0.998 |

`cos(h_C − h_A, v_lex)` is 0.133 and 0.179 — the doublespeak shift is a ~3.0-norm vector of which
about 0.4–0.5 lies along the axis, roughly 13–18 % of its length. "Traverses 10 % of the
button→bomb gap" is true and is the right unit for the question asked, but the same number is also
"87 % of what the doublespeak context does to this token is orthogonal to the lexical axis". Both
should be quoted together. The one genuinely reassuring structural fact is that C (0.104) and B
(0.836) are *far apart*: a simple "harm demonstrations pull everything toward one common attractor"
account would put C and B at the same coordinate, and it does not.

**8.7 What would settle it.** (a) `B1resid` for all three shifts (8.4). (b) A benign-but-incongruous
hard negative — a codeword→*ordinary noun that does not belong here* axis — to separate "bomb-ness"
from "an out-of-place word is here"; the `club` banks under
`outputs/boombness/extract_boombness/bombspec_*_club_*` are the nearest existing material.
(c) A causal step: the correlational quantity is a projection, and until adding `α·v_lex` to cell A
at this layer changes the model's behaviour, "the codeword carries bombness" remains a description
of a 0.13-cosine alignment.

---

## 9. Exact code

Written from the prose spec only. `--selftest` and `--mutate` both pass; the mutation run confirms
that sabotaging LOO, the domain mean, the pairing key, or the summary statistics each breaks the
selftest (a verifier that survives its own sabotage is not a verifier).

```
$ python indep_b1.py --selftest
SELFTEST OK
$ python indep_b1.py --mutate
MUTATE OK: loo_axis_scores -> AssertionError: -6.605148865413116e-07
MUTATE OK: domain_means -> AssertionError:
MUTATE OK: select_rows -> AssertionError: 4
MUTATE OK: summarise -> AssertionError:
MUTATE ALL OK
$ python indep_b1.py --banks ts116m_button_bomb ts116m_basket_bomb --out res_bomb.json
$ python indep_b1.py --hA ts116m_button_bomb ts116m_button_knife --out res_hA_button.json
$ python adv.py ts116m_button_bomb ts116m_button_knife ts116m_button_gun
$ python adv.py ts116m_basket_bomb ts116m_basket_knife ts116m_basket_gun
$ python rnd.py ; python fin.py ; python pos.py
```

Interpreter: `/home/sharifm/students/omeryosef/miniconda3/envs/poc_stage2/bin/python`.
No GPU job, no SLURM job, no frozen config touched, no TEST domain read.

### `indep_b1.py`

```python
#!/usr/bin/env python
"""
INDEPENDENT re-derivation of the DCS-SUCC "B1" lexical-axis candidate.

WHY THIS FILE EXISTS: the original candidate scorer
(scripts/dcs_succ_bombness_candidates.py) reported mean B1 ~ 0.10-0.14 at layers
11-12 on TRAIN.  This file recomputes that quantity from the raw extraction
artifacts along a deliberately separate code path -- nothing is imported from,
copied from, or read out of the original script or its JSON output.  It exists
to catch three specific defects that this project has already been bitten by:

  (D1) family_id field 1 is the BANK's own split ('dev'/'heldout'), NOT the
       domain-level manifest split.  A pairing key that drops it collapses
       dev and heldout rows and silently halves the data.  We therefore key on
       the FULL family_id and assert one row per (family_id, cell).
  (D2) prompt_id is not unique ACROSS banks, so nothing here ever joins two
       banks on prompt_id alone; cross-bank joins use (bank_file_sha16 is
       recorded and asserted constant within a bank) + family_id + cell.
  (D3) missing != zero.  Any missing rep, missing layer, missing domain, or
       empty selection raises.

Modes: --selftest (synthetic checks), --mutate (sabotage each core function and
assert the selftest catches it).
"""
import argparse, json, os, sys, math
import numpy as np

ROOT = "/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
EXTR = os.path.join(ROOT, "outputs/boombness/extract_boombness")
MANIFEST = os.path.join(ROOT, "data/boombness_prompts/dcs_ts116_domain_split.json")
EXCLUDED = ("restaurant_kitchen", "school_campus", "subway_station")
LAYERS = list(range(6, 15))
RUNS = {
    "ts116m_button_bomb":  "ts116m_full_button_bomb_20260907_040927_3131687",
    "ts116m_button_knife": "ts116m_full_button_knife_20260907_043559_3133560",
    "ts116m_button_gun":   "ts116m_full_button_gun_20260907_044459_4158652",
    "ts116m_basket_bomb":  "ts116m_full_basket_bomb_20260907_054404_4164227",
    "ts116m_basket_knife": "ts116m_full_basket_knife_20260907_064357_4169305",
    "ts116m_basket_gun":   "ts116m_full_basket_gun_20260907_074403_4175988",
}

# ---------------------------------------------------------------- core pieces

def load_split(path=MANIFEST):
    m = json.load(open(path))
    if m.get("unit") != "domain":
        raise ValueError("manifest unit is not 'domain'")
    return m["assign"], m.get("manifest_sha16")


def select_rows(results_path, split_map, want_split="train"):
    """Return {(family_id, cell) -> row} for the analysed selection.

    Refuses on: duplicate key, unknown domain, empty selection, non-constant
    bank_file_sha16, position != codeword_last, missing critical field.
    """
    sel = {}
    shas = set()
    ndup = 0
    for line in open(results_path):
        r = json.loads(line)
        for f in ("family_id", "cell", "domain", "query_kind", "n_examples",
                  "position", "prompt_id", "bank_file_sha16", "layers"):
            if f not in r:
                raise KeyError("missing critical field %r in %s" % (f, results_path))
        if r["query_kind"] != "semantic_one_word":
            continue
        if r["n_examples"] != 4:
            continue
        if r["cell"] not in ("A", "B", "C", "E"):
            continue
        if r["domain"] in EXCLUDED:
            continue
        if r["domain"] not in split_map:
            raise KeyError("domain %r absent from frozen manifest" % r["domain"])
        if split_map[r["domain"]] != want_split:
            continue
        if r["position"] != "codeword_last":
            raise ValueError("unexpected position %r" % r["position"])
        if list(r["layers"]) != LAYERS:
            raise ValueError("unexpected layers %r" % r["layers"])
        k = (r["family_id"], r["cell"])
        if k in sel:
            ndup += 1
        sel[k] = r
        shas.add(r["bank_file_sha16"])
    if not sel:
        raise ValueError("empty selection -- a gate that passes on nothing is not a gate")
    if ndup:
        raise ValueError("%d duplicate (family_id, cell) keys -- pairing key is not unique" % ndup)
    if len(shas) != 1:
        raise ValueError("bank_file_sha16 not constant within bank: %r" % shas)
    return sel, shas.pop()


def domain_means(sel, reps, cell):
    """{domain -> float64 [nL, 4096]} = mean over family slots of h_cell."""
    acc = {}
    for (fam, c), r in sel.items():
        if c != cell:
            continue
        dom = fam.split("|")[0]
        if dom != r["domain"]:
            raise ValueError("family_id domain field disagrees with row domain")
        pid = r["prompt_id"]
        if pid not in reps:
            raise KeyError("no rep for prompt_id %s" % pid)
        v = np.asarray(reps[pid], dtype=np.float64)
        if v.shape != (len(LAYERS), 4096):
            raise ValueError("bad rep shape %r" % (v.shape,))
        acc.setdefault(dom, []).append(v)
    if not acc:
        raise ValueError("no rows for cell %r" % cell)
    out = {}
    for d, lst in acc.items():
        out[d] = np.mean(np.stack(lst, 0), axis=0)
    return out, {d: len(l) for d, l in acc.items()}


def loo_axis_scores(delta_ref, delta_num, denom_mode="loo"):
    """delta_ref: [D, dim] per-domain (h_E - h_A). delta_num: [D, dim] numerator diffs.

    For each domain d: m_d = mean over d' != d of delta_ref -> v_hat = m_d/||m_d||
    score(d) = <delta_num[d], v_hat> / ||m||, with ||m|| the LOO norm ('loo')
    or the full-sample norm ('full').
    """
    D = delta_ref.shape[0]
    if D < 2:
        raise ValueError("LOO needs >= 2 domains")
    tot = delta_ref.sum(0)
    full_norm = float(np.linalg.norm(tot / D))
    out = np.empty(D, dtype=np.float64)
    for d in range(D):
        m = (tot - delta_ref[d]) / (D - 1)
        n = float(np.linalg.norm(m))
        if n == 0.0:
            raise ValueError("zero LOO axis")
        den = n if denom_mode == "loo" else full_norm
        out[d] = float(delta_num[d] @ (m / n)) / den
    return out, full_norm


def summarise(x, n_boot=20000, seed=20260909):
    x = np.asarray(x, dtype=np.float64)
    n = x.size
    mean = float(x.mean())
    sd = float(x.std(ddof=1))
    d = mean / sd if sd > 0 else float("inf")
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, n, size=(n_boot, n))
    bm = x[idx].mean(1)
    lo, hi = np.percentile(bm, [2.5, 97.5])
    # exact two-sided sign test
    npos = int((x > 0).sum()); nneg = int((x < 0).sum()); m = npos + nneg
    k = min(npos, nneg)
    p = 0.0
    for i in range(0, k + 1):
        p += math.comb(m, i)
    p = min(1.0, 2.0 * p / (2.0 ** m)) if m else float("nan")
    floor = 2.0 / (2.0 ** m) if m else float("nan")
    # t-based CI too, for cross-check
    se = sd / math.sqrt(n)
    return dict(n=n, mean=mean, sd=sd, d=d, ci_lo=float(lo), ci_hi=float(hi),
                t_lo=mean - 1.9966 * se, t_hi=mean + 1.9966 * se,
                npos=npos, nneg=nneg, sign_p=p, sign_floor=floor)

# ---------------------------------------------------------------- self-tests

def selftest():
    rng = np.random.default_rng(0)
    # loo_axis_scores: if all delta_ref rows are identical e = u*s, then
    # m_d = e for every d, and score = <num, u>/s.
    dim = 8
    u = np.zeros(dim); u[0] = 1.0
    s = 3.0
    ref = np.tile((u * s)[None, :], (5, 1))
    num = rng.normal(size=(5, dim))
    sc, fn = loo_axis_scores(ref, num, "loo")
    assert abs(fn - s) < 1e-9, fn
    assert np.allclose(sc, num[:, 0] / s), (sc, num[:, 0] / s)
    # denom_mode full agrees here
    sc2, _ = loo_axis_scores(ref, num, "full")
    assert np.allclose(sc, sc2)
    # LOO really excludes d: make domain 0 an enormous outlier along axis 1;
    # its own score must not feel it.
    ref2 = np.tile((u * s)[None, :], (5, 1)); ref2[0, 1] = 1e6
    sc3, _ = loo_axis_scores(ref2, num, "loo")
    assert np.allclose(sc3[0], num[0, 0] / s), sc3[0]
    assert not np.allclose(sc3[1], num[1, 0] / s)
    # LOO with D<2 refuses
    try:
        loo_axis_scores(ref[:1], num[:1]); raise AssertionError("no refusal on D=1")
    except ValueError:
        pass
    # summarise: symmetric data -> mean ~0, all-positive -> npos==n, sign floor
    st = summarise(np.array([1.0, 2.0, 3.0, 4.0]))
    assert st["npos"] == 4 and st["nneg"] == 0
    assert abs(st["sign_floor"] - 2.0 / 16) < 1e-12
    assert abs(st["sign_p"] - 2.0 / 16) < 1e-12
    assert abs(st["mean"] - 2.5) < 1e-12
    assert abs(st["d"] - 2.5 / np.std([1, 2, 3, 4], ddof=1)) < 1e-12
    # domain_means: means over slots, refuses missing rep
    sel = {("dA|dev|slot0|x", "C"): {"prompt_id": "p1", "domain": "dA"},
           ("dA|heldout|slot1|x", "C"): {"prompt_id": "p2", "domain": "dA"}}
    reps = {"p1": np.ones((len(LAYERS), 4096)), "p2": np.full((len(LAYERS), 4096), 3.0)}
    dm, cnt = domain_means(sel, reps, "C")
    assert cnt == {"dA": 2}
    assert np.allclose(dm["dA"], 2.0)
    try:
        domain_means(sel, {"p1": reps["p1"]}, "C"); raise AssertionError("no refusal on missing rep")
    except KeyError:
        pass
    try:
        domain_means(sel, reps, "B"); raise AssertionError("no refusal on empty cell")
    except ValueError:
        pass
    # select_rows: duplicate key and empty selection refusals, and the (D1) trap:
    # a key that drops the split field must collapse -- we assert ours does not.
    import tempfile
    rows = []
    for sp in ("dev", "heldout"):
        for cell in ("A", "B", "C", "E"):
            rows.append(dict(family_id="dA|%s|slot0|n4|none|consistent|near|plain|semantic_one_word" % sp,
                             cell=cell, domain="dA", query_kind="semantic_one_word", n_examples=4,
                             position="codeword_last", prompt_id="p_%s_%s" % (sp, cell),
                             bank_file_sha16="deadbeef", layers=LAYERS))
    with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False) as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")
        p = fh.name
    sel2, sha = select_rows(p, {"dA": "train"})
    assert len(sel2) == 8, len(sel2)          # 2 splits x 4 cells, NOT 4
    collapsed = {("|".join([f.split("|")[0]] + f.split("|")[2:]), c) for f, c in sel2}
    assert len(collapsed) == 4                 # the trap, demonstrated
    assert sha == "deadbeef"
    try:
        select_rows(p, {"dA": "test"}); raise AssertionError("no refusal on empty selection")
    except ValueError:
        pass
    with open(p, "a") as fh:
        fh.write(json.dumps(rows[0]) + "\n")
    try:
        select_rows(p, {"dA": "train"}); raise AssertionError("no refusal on duplicate key")
    except ValueError:
        pass
    os.unlink(p)
    print("SELFTEST OK")


def mutate():
    import copy
    g = globals()
    orig = {k: g[k] for k in ("loo_axis_scores", "domain_means", "select_rows", "summarise")}
    muts = {}
    def m_loo(delta_ref, delta_num, denom_mode="loo"):  # sabotage: no LOO, use full mean
        D = delta_ref.shape[0]
        m = delta_ref.mean(0); n = float(np.linalg.norm(m))
        return np.array([float(delta_num[d] @ (m / n)) / n for d in range(D)]), n
    def m_dm(sel, reps, cell):  # sabotage: first slot instead of mean, no missing check
        out = {}
        for (fam, c), r in sel.items():
            if c != cell: continue
            out.setdefault(fam.split("|")[0], np.asarray(reps[r["prompt_id"]], dtype=np.float64))
        if not out: raise ValueError("no rows")
        return out, {d: 1 for d in out}
    def m_sel(results_path, split_map, want_split="train"):  # sabotage: drop split field from key
        sel = {}
        for line in open(results_path):
            r = json.loads(line)
            if r["query_kind"] != "semantic_one_word" or r["n_examples"] != 4: continue
            if r["cell"] not in "ABCE" or r["domain"] in EXCLUDED: continue
            if split_map.get(r["domain"]) != want_split: continue
            f = r["family_id"].split("|")
            sel[("|".join([f[0]] + f[2:]), r["cell"])] = r
        return sel, "deadbeef"
    def m_sum(x, n_boot=20000, seed=0):  # sabotage: ddof=0 and no sign floor
        x = np.asarray(x, float); mean = float(x.mean()); sd = float(x.std())
        return dict(n=x.size, mean=mean, sd=sd, d=mean / sd, ci_lo=mean, ci_hi=mean,
                    t_lo=mean, t_hi=mean, npos=int((x > 0).sum()), nneg=int((x < 0).sum()),
                    sign_p=1.0, sign_floor=1.0)
    muts = dict(loo_axis_scores=m_loo, domain_means=m_dm, select_rows=m_sel, summarise=m_sum)
    ok = True
    for name, fn in muts.items():
        g[name] = fn
        try:
            selftest()
            print("MUTATE FAIL: sabotaging %s did NOT break the selftest" % name); ok = False
        except Exception as e:
            print("MUTATE OK: %s -> %s: %s" % (name, type(e).__name__, str(e)[:70]))
        g[name] = orig[name]
    if not ok:
        sys.exit(1)
    print("MUTATE ALL OK")

# ---------------------------------------------------------------- main
def run_bank(bank, split_map, cache_dir):
    import torch
    run = RUNS[bank]
    rp = os.path.join(EXTR, run, "results.jsonl")
    sel, sha = select_rows(rp, split_map)
    ncell = {}
    for (f, c) in sel:
        ncell[c] = ncell.get(c, 0) + 1
    reps = torch.load(os.path.join(EXTR, run, "cache/final_occurrence_reps.pt"),
                      map_location="cpu", weights_only=False)
    if reps["position"] != "codeword_last" or list(reps["layers"]) != LAYERS:
        raise ValueError("rep header mismatch")
    R = reps["reps"]
    dms = {}
    for cell in ("A", "B", "C", "E"):
        dms[cell], cnt = domain_means(sel, R, cell)
        if len(set(cnt.values())) != 1:
            raise ValueError("uneven slot counts for cell %s: %r" % (cell, sorted(set(cnt.values()))))
    doms = sorted(dms["A"])
    for cell in ("B", "C", "E"):
        if sorted(dms[cell]) != doms:
            raise ValueError("domain sets differ across cells")
    del reps, R
    out = dict(bank=bank, run=run, bank_file_sha16=sha, n_domains=len(doms),
               n_rows=len(sel), n_per_cell=ncell, slots_per_domain=cnt[doms[0]], layers={})
    A = np.stack([dms["A"][d] for d in doms])   # [D, nL, 4096]
    B = np.stack([dms["B"][d] for d in doms])
    C = np.stack([dms["C"][d] for d in doms])
    E = np.stack([dms["E"][d] for d in doms])
    rng = np.random.default_rng(12345)
    for li, L in enumerate(LAYERS):
        ref = E[:, li, :] - A[:, li, :]
        numC = C[:, li, :] - A[:, li, :]
        numB = B[:, li, :] - E[:, li, :]
        sc_loo, full_norm = loo_axis_scores(ref, numC, "loo")
        sc_full, _ = loo_axis_scores(ref, numC, "full")
        # non-LOO (in-sample) axis, for contrast
        mfull = ref.mean(0); vhat = mfull / np.linalg.norm(mfull)
        sc_insample = (numC @ vhat) / full_norm
        scB, _ = loo_axis_scores(ref, numB, "loo")
        # 12 random unit directions, same normalisation
        rnd_dom_means = []
        for _ in range(12):
            r = rng.normal(size=4096); r /= np.linalg.norm(r)
            rnd_dom_means.append(float(np.mean(numC @ r) / full_norm))
        rnd = np.array(rnd_dom_means)
        st = summarise(sc_loo)
        out["layers"][L] = dict(
            B1_loo=st,
            B1_loo_fulldenom_mean=float(sc_full.mean()),
            B1_insample_mean=float(sc_insample.mean()),
            axis_norm=full_norm,
            BE_loo=summarise(scB),
            rand12_mean=float(rnd.mean()), rand12_sd=float(rnd.std(ddof=1)),
            rand12_min=float(rnd.min()), rand12_max=float(rnd.max()),
            per_domain=dict(zip(doms, [float(v) for v in sc_loo])),
        )
    return out


def cross_bank_hA(bank1, bank2, split_map):
    """||h_A(bank1) - h_A(bank2)|| per layer, joined on (family_id, cell='A').

    prompt_id is NOT unique across banks, so the join is on family_id and each
    bank's own prompt_id is looked up in its own rep table only.
    """
    import torch
    res = {}
    stacks = {}
    for bank in (bank1, bank2):
        run = RUNS[bank]
        sel, sha = select_rows(os.path.join(EXTR, run, "results.jsonl"), split_map)
        reps = torch.load(os.path.join(EXTR, run, "cache/final_occurrence_reps.pt"),
                          map_location="cpu", weights_only=False)
        R = reps["reps"]
        fams = sorted(f for (f, c) in sel if c == "A")
        arr = np.stack([np.asarray(R[sel[(f, "A")]["prompt_id"]], dtype=np.float64) for f in fams])
        stacks[bank] = (fams, arr, sha)
        del reps, R
    f1, a1, s1 = stacks[bank1]; f2, a2, s2 = stacks[bank2]
    if f1 != f2:
        raise ValueError("family_id sets differ between banks")
    if s1 == s2:
        raise ValueError("banks share bank_file_sha16 -- not two distinct banks")
    diff = a1 - a2                      # [N, nL, 4096]
    per_layer = {}
    for li, L in enumerate(LAYERS):
        dl = diff[:, li, :]
        per_layer[L] = dict(max_row_l2=float(np.linalg.norm(dl, axis=1).max()),
                            mean_row_l2=float(np.linalg.norm(dl, axis=1).mean()),
                            max_abs=float(np.abs(dl).max()),
                            mean_hA_l2=float(np.linalg.norm(a1[:, li, :], axis=1).mean()))
    return dict(bank1=bank1, bank2=bank2, n_families=len(f1),
                sha1=s1, sha2=s2, per_layer=per_layer,
                identical_everywhere=bool(np.all(diff == 0)))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--mutate", action="store_true")
    ap.add_argument("--banks", nargs="*", default=[])
    ap.add_argument("--hA", nargs=2, default=None)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    if a.selftest:
        selftest(); sys.exit(0)
    if a.mutate:
        mutate(); sys.exit(0)
    split_map, sha16 = load_split()
    res = {"manifest_sha16": sha16, "banks": {}, "hA": None}
    for b in a.banks:
        res["banks"][b] = run_bank(b, split_map, None)
        print("done", b, flush=True)
    if a.hA:
        res["hA"] = cross_bank_hA(a.hA[0], a.hA[1], split_map)
    if a.out:
        json.dump(res, open(a.out, "w"), indent=1)
    print(json.dumps({k: (v if k != "banks" else {b: {L: dd["layers"][L]["B1_loo"]["mean"] for L in dd["layers"]} for b, dd in v.items()}) for k, v in res.items()}, indent=1)[:4000])
```

### `adv.py` — cross-concept transfer and anisotropy controls

```python
"""Adversarial probes on top of indep_b1: is v_lex 'bombness' or 'a concept word is here'?"""
import sys, json, os, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from indep_b1 import (RUNS, EXTR, LAYERS, load_split, select_rows, domain_means,
                      loo_axis_scores, summarise)
import torch

split_map, sha = load_split()
BANKS = [b for b in sys.argv[1:]]
store = {}
for bank in BANKS:
    run = RUNS[bank]
    sel, bsha = select_rows(os.path.join(EXTR, run, "results.jsonl"), split_map)
    reps = torch.load(os.path.join(EXTR, run, "cache/final_occurrence_reps.pt"),
                      map_location="cpu", weights_only=False)
    R = reps["reps"]
    dm = {c: domain_means(sel, R, c)[0] for c in "ABCE"}
    del reps, R
    doms = sorted(dm["A"])
    store[bank] = {c: np.stack([dm[c][d] for d in doms]) for c in "ABCE"}
    store[bank]["doms"] = doms
    print("loaded", bank, bsha, len(doms), flush=True)

d0 = store[BANKS[0]]["doms"]
for b in BANKS:
    assert store[b]["doms"] == d0

out = {}
for li, L in enumerate(LAYERS):
    row = {}
    ax = {}
    for b in BANKS:
        S = store[b]
        ref = S["E"][:, li, :] - S["A"][:, li, :]
        ax[b] = ref
    # global mean hidden state direction (norm/anisotropy confound)
    allh = np.concatenate([store[b][c][:, li, :] for b in BANKS for c in "ABCE"], 0)
    gmean = allh.mean(0); u_g = gmean / np.linalg.norm(gmean)
    for b in BANKS:
        S = store[b]
        numC = S["C"][:, li, :] - S["A"][:, li, :]
        own, own_norm = loo_axis_scores(ax[b], numC, "loo")
        row[b] = {"B1_own": summarise(own)["mean"], "axis_norm": own_norm,
                  "B1_own_npos": summarise(own)["npos"]}
        # transfer: score bank b's C-A along OTHER banks' axes (full, not LOO --
        # the other bank's axis never saw b's C rows anyway)
        for b2 in BANKS:
            if b2 == b: continue
            m = ax[b2].mean(0); n = np.linalg.norm(m)
            sc = (numC @ (m / n)) / n
            row[b]["B1_via_" + b2.split("_")[-1]] = float(sc.mean())
            row[b]["B1_via_%s_npos" % b2.split("_")[-1]] = int((sc > 0).sum())
        # norm / anisotropy control: project C-A on the global mean direction
        row[b]["C_minus_A_on_globalmean"] = float((numC @ u_g).mean() / own_norm)
        row[b]["cos_axis_globalmean"] = float((ax[b].mean(0) / own_norm) @ u_g)
        row[b]["norm_hC_minus_normhA"] = float((np.linalg.norm(S["C"][:, li, :], axis=1)
                                                - np.linalg.norm(S["A"][:, li, :], axis=1)).mean())
        # what fraction of ||C-A|| does the axis capture?
        row[b]["mean_norm_C_minus_A"] = float(np.linalg.norm(numC, axis=1).mean())
    # cosines between the different concepts' lexical axes
    for i, b in enumerate(BANKS):
        for b2 in BANKS[i+1:]:
            m1 = ax[b].mean(0); m2 = ax[b2].mean(0)
            row["cos_%s_%s" % (b.split("_")[-1], b2.split("_")[-1])] = float(
                m1 @ m2 / (np.linalg.norm(m1) * np.linalg.norm(m2)))
    out[L] = row
print(json.dumps(out, indent=1))
json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "adv_%s.json" % BANKS[0]), "w"), indent=1)
```

### `rnd.py` — analytic random-direction null

```python
import sys,os,json,numpy as np,torch
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from indep_b1 import *
sm,_=load_split()
for bank,L in [("ts116m_button_bomb",12),("ts116m_basket_bomb",11)]:
    run=RUNS[bank]; sel,_=select_rows(os.path.join(EXTR,run,"results.jsonl"),sm)
    reps=torch.load(os.path.join(EXTR,run,"cache/final_occurrence_reps.pt"),map_location="cpu",weights_only=False); R=reps["reps"]
    dm={c:domain_means(sel,R,c)[0] for c in "ACE"}; del reps,R
    doms=sorted(dm["A"]); li=LAYERS.index(L)
    A=np.stack([dm["A"][d] for d in doms])[:,li,:]; C=np.stack([dm["C"][d] for d in doms])[:,li,:]; E=np.stack([dm["E"][d] for d in doms])[:,li,:]
    g=(C-A).mean(0); ax=(E-A).mean(0); an=np.linalg.norm(ax)
    sig=np.linalg.norm(g)/(np.sqrt(4096)*an)
    rng=np.random.default_rng(7); vals=[]
    for _ in range(20000):
        r=rng.normal(size=4096); r/=np.linalg.norm(r); vals.append(float(g@r)/an)
    v=np.array(vals)
    print(bank,"L",L,"||g||=%.4f ||axis||=%.4f analytic_sd=%.5f  20k-draw mean=%.5f sd=%.5f  p95abs=%.5f"%(np.linalg.norm(g),an,sig,v.mean(),v.std(ddof=1),np.percentile(np.abs(v),95)))
    print("   true B1 / analytic_sd  = %.1f sigma"%( (0.104449 if 'button' in bank else 0.136596)/sig))
```

### `fin.py` — precision-matched headline recompute

```python
import sys,os,json,numpy as np,torch
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from indep_b1 import *
sm,_=load_split()
for bank,L in [("ts116m_button_bomb",12),("ts116m_basket_bomb",11)]:
    run=RUNS[bank]; sel,_=select_rows(os.path.join(EXTR,run,"results.jsonl"),sm)
    reps=torch.load(os.path.join(EXTR,run,"cache/final_occurrence_reps.pt"),map_location="cpu",weights_only=False); R=reps["reps"]
    dm={c:domain_means(sel,R,c)[0] for c in "ABCE"}; del reps,R
    doms=sorted(dm["A"]); li=LAYERS.index(L)
    for dt,nm in [(np.float64,'f64'),(np.float32,'f32')]:
        A=np.stack([dm["A"][d] for d in doms])[:,li,:].astype(dt); C=np.stack([dm["C"][d] for d in doms])[:,li,:].astype(dt)
        E=np.stack([dm["E"][d] for d in doms])[:,li,:].astype(dt); B=np.stack([dm["B"][d] for d in doms])[:,li,:].astype(dt)
        ref=E-A; numC=C-A; numB=B-E
        for mode in ["full"]:
            sc,fn=loo_axis_scores(ref.astype(np.float64),numC.astype(np.float64),mode)
            s=summarise(sc); scb,_=loo_axis_scores(ref.astype(np.float64),numB.astype(np.float64),mode); sb=summarise(scb)
            # cos and proj like the original
            proj=[]; cos=[]
            tot=ref.sum(0)
            for i in range(len(doms)):
                m=(tot-ref[i]); vh=m/np.linalg.norm(m)
                p=float(numC[i]@vh); proj.append(p); cos.append(p/float(np.linalg.norm(numC[i])))
            print("%s L%d %s: mean_gap=%.6f d=%.4f sd=%.6f npos=%d gapnorm=%.6f mean_proj=%.4f mean_cos=%.4f | BE mean=%.6f"%(
                bank,L,nm,s['mean'],s['d'],s['sd'],s['npos'],fn,np.mean(proj),np.mean(cos),sb['mean']))
```

### `pos.py` — cell coordinates on the lexical axis

```python
import sys,os,json,numpy as np,torch
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from indep_b1 import *
sm,_=load_split()
for bank,L in [("ts116m_button_bomb",12),("ts116m_basket_bomb",11)]:
    run=RUNS[bank]; sel,_=select_rows(os.path.join(EXTR,run,"results.jsonl"),sm)
    reps=torch.load(os.path.join(EXTR,run,"cache/final_occurrence_reps.pt"),map_location="cpu",weights_only=False); R=reps["reps"]
    dm={c:domain_means(sel,R,c)[0] for c in "ABCE"}; del reps,R
    doms=sorted(dm["A"]); li=LAYERS.index(L)
    A,B,C,E=[np.stack([dm[c][d] for d in doms])[:,li,:] for c in "ABCE"]
    ref=E-A
    def sc(num):
        s,fn=loo_axis_scores(ref,num,"full"); return s.mean(),fn
    for nm,num in [("E-A (should be ~1)",E-A),("C-A",C-A),("B-A",B-A),("B-E",B-E),("B-C",B-C)]:
        m,fn=sc(num); print("%-22s %-12s coord=%.4f"%(bank,nm,m))
    print("   gap=%.4f  ||C-A||=%.3f ||B-A||=%.3f ||E-A||(perdom)=%.3f ||B-C||=%.3f"%(
        np.linalg.norm(ref.mean(0)),np.linalg.norm(C-A,axis=1).mean(),np.linalg.norm(B-A,axis=1).mean(),
        np.linalg.norm(E-A,axis=1).mean(),np.linalg.norm(B-C,axis=1).mean()))
```
