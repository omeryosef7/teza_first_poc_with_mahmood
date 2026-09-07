# DCS-PR-057 PHASE 9 — checklist item Q0: SIGNED OFF

**Verdict: Q0 is CLEARED.** 2026-09-07.

Q0 asks three things of the PHASE 7 readout, and all three are now true where at the time
`DCS_TS_PR057_DESIGN.md` was written only three of six banks had landed.

## 1. All six banks completed

Each bank's most recent run carrying a `DONE.json` (filtered on `DONE.json`, never on recency —
C-051/C-012, and `basket_bomb` was mid-flight during the design write-up for exactly this reason):

| bank | rows_written | status | `semantic_one_word` median_true | reportable | option_mass_gate |
|---|---|---|---|---|---|
| button_bomb  | 5568 | ok | 0.0825 | true | PASS |
| button_knife | 5568 | ok | 0.0663 | true | PASS |
| button_gun   | 5568 | ok | 0.0616 | true | PASS |
| basket_bomb  | 5552 | ok | 0.0594 | true | PASS |
| basket_knife | 5552 | ok | 0.0857 | true | PASS |
| basket_gun   | 5552 | ok | 0.0666 | true | PASS |

## 2. The primary channel is engaged, on every bank and not just on the one that was inspected

`option_mass_gate = PASS` and `reportable = true` on **6/6**. The preregistration says in terms
that a disengaged `semantic_one_word` is a CANNOT ANSWER on the primary rather than a licence to
fall back on the display channel. That branch is not taken: the channel is engaged everywhere.

## 3. The 16-row discrepancy, chased rather than waved through

The button banks wrote 5568 rows and the basket banks 5552. The prompt banks themselves are
identical in size (22272 rows each) and carry the same 116 domains with an empty symmetric
difference, so the gap arises **during scoring**, which is where an unexplained missing row would
matter most.

Located by differencing the per-field counts: the entire 16-row gap lies in the single domain
**`school_campus`** (button 48, basket 32) — one of the three whole-population exclusions
(`restaurant_kitchen`, `subway_station`, `school_campus`). It is excluded from every analysis in
this phase, so it cannot reach a result.

Restricted to the **113 analysed domains**, all six banks are exactly balanced:

- 113 domains, **5424 rows each**, on all six banks
- identical (cell × query_kind × n_examples) profile on all six:
  `A`/`C` × `semantic_forced_choice`/`semantic_one_word` × {0: 226 rows, 4: 1130 rows}

This is what makes the gap explained rather than tolerated. Recorded because a 16-row difference
that had landed inside an analysed domain would have been a defect, and the two cases are
indistinguishable without looking.

## 4. The PHASE 9 population follows arithmetically

Cell `C`, `semantic_one_word`, `n_examples = 4` → 1130 rows per bank over 113 domains = **10 rows
per domain**. The TEST split is 23 domains, giving **230 rows per arm on TEST** — which is the
number `DCS_TS_PR057_DESIGN.md` §2 states independently. The two agree.

## 5. What Q0 does NOT establish

Q0 is an instrument-liveness and population-balance sign-off. It says the readout ran, the channel
is engaged and the rows are balanced. It says nothing about whether the demonstrations install
their concept — that is R-116, which measured installation at bomb 0.619, gun 0.009, knife 0.000
over these same 113 domains, and which is why C-112 demoted the patch arm. A PASS here is not
evidence against R-116 and must not be quoted as though it were.

**Remaining blockers after Q0: Q1, Q2, Q3 (GPU wiring), Q4b, Q7, and Q9–Q13.**
