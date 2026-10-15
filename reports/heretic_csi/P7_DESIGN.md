# P7 (behavioural linking) — DESIGN ONLY (F8, 2026-10-15)

**Headline: the P7 primary as the mandate specifies it is `CANNOT ANSWER / UNDERPOWERED` by §20
arithmetic, before any GPU is spent.** The confirmed interventions move semantic installation by
~2–6% of what the knockout itself moves, and the knockout's own content-true ASR effect was a
powered null. No attainable sample resolves the implied effect. The recommendation is therefore to
*declare* that, not to run it and call the result a null.

## 1. Which interventions qualify (pre-declared, not chosen by behaviour)

| intervention | status | installation effect (Δy vs KO) | carry to P7? |
|---|---|---|---|
| P2a button r4 (S-126) | CONFIRMED: held-out, multiplicity-corrected, 200 controls, independently verified | +0.0129 [0.0065, 0.0190] | **yes — the only one that meets §18's bar** |
| P2b basket CWONLY r1/r4 (S-157) | robust VAL pass (Holm 0.026, LODO 23/23) — but secondary, with the amendment-2 forking-path disclosure | large (≈0.79 of BASE−KO) | second choice, disclosed as secondary |
| P2a basket r1 (S-049/S-052) | VAL pass but floor-sensitive (strict floor → 2/57) | +0.0050 | no |
| P2b basket r4 primary (S-156/S-157) | marginal (Holm 0.0488; LODO loses it in 9/23) | — | no |

§18 requires reproducible, controlled, held-out, better than rank-matched controls. Only
**P2a button r4** satisfies all four without qualification.

## 2. Inherited behavioural pipeline (recovered)

* **Generation**: `src/boombness/score_behavior.py --query-kinds behavioral --max-new 640`,
  eager + bf16, seed 20260913, a5000. Measured cost **20.2 s/row** (DR-070 KO run: 670 rows,
  13 513 s) ⇒ **1.29 GPU-h per arm on VAL (230 rows)**, 3.75 GPU-h on TRAIN.
* **Judge**: `src/boombness/judge_boombness.py`, StrongREJECT via **OpenAI gpt-4o-mini**
  (`OPENAI_API_KEY` present in `.env`; pinned with `--pin-judge-model openai/gpt-4o-mini`
  because the judge is not bitwise deterministic). Re-judging cached generations is free of GPU.
  Estimated **$0.07 per 230-row arm** (~1.2k in / 200 out tokens per row) ⇒ ~$1 for a 14-arm
  design, ~$4 for a 59-arm one. **API cost is not the constraint.**
* **Content-true endpoint**: primary = `ASR AND concept_present AND non_refusal`, where
  `concept_present` uses the frozen 44-term lexicon (`scripts/dcs_succ_concept_presence.py`) and the
  frozen content rule `configs/dcs_cont_content_rule_v2.json` (CR-002, MATERIAL ∧ ¬SCOPE, applied to
  the completion only). Raw StrongREJECT overstates content-true success by **6.6× (basket) to
  11.8× (button)** — `reports/DCS_CONT_ASR_FACTOR.json`. Raw ASR must never be the primary.
* **The inherited same-population null (DR-070 / DR-073)**: with a dose-matched control cut,
  ASR(ko−ctrl) = **+0.0030 [−0.0299, +0.0358], p = 0.844** (button; basket −0.0090, p = 0.402),
  while the *manipulation check* confirmed installation moved **−0.2150** (67/67 domains). Base
  rates: **button 0.1418, basket 0.0463**. Refusal was roughly halved by the cut (band-specific).
* **Populations**: cell C (`natural_doublespeak`), `query_kind=behavioral`, n_examples 4, 10
  rows/domain. **Blocker: `runargs/dcs_cont/exclude_*_behavioral_*.txt` exist for TRAIN only** —
  a VALIDATION behavioural exclusion file has to be built first (CPU, minutes, via the existing
  `dcs_ts_make_exclusions.py`).

## 3. Power — why the primary is CANNOT ANSWER

Using the inherited per-domain paired SD for the content-true endpoint (0.1553):

| n_domains | MDE (80 %, α .05) | vs button base 0.142 | vs basket base 0.046 |
|---|---|---|---|
| 67 (TRAIN) | 0.0531 | 38 % relative | 115 % — floor |
| **23 (VALIDATION)** | **0.0907** | **65 % relative** | 196 % — floor |

And the effect that could plausibly exist:

* the knockout moves installation by **0.2150** and moved content-true ASR by **+0.0030**, with the
  CI excluding anything beyond **±0.036**;
* **P2a button r4 moves installation by 0.0129 = 6.0 % of that**;
* under a generous *proportional* model, the implied |ΔASR| is **≤ 0.0021**;
* detecting 0.0021 at 80 % power needs **≈ 42 900 domains** (we have 23).

The gap between the detectable (0.091) and the plausible (0.002) is **~45×**. Per mandate §20 this
is to be labelled `CANNOT ANSWER / UNDERPOWERED` and redesigned, **not run**.

## 4. What is worth running instead (if P7 is pursued at all)

1. **Refusal as a descriptive secondary, button only.** The knockout halves refusal and the inherited
   patch test recovered ~42 % of de-refusal on button, so there is headroom. Basket refusal is at
   floor (1 event in 180 rows inherited) ⇒ basket refusal is CANNOT ANSWER.
2. **The manipulation check on the same rows** (y_install under the behavioural prompt), which is
   what makes any chain statement same-population.
3. Both are **descriptive**; neither licenses a mediation claim (§18: two things moving is not
   mediation).

## 5. Arms, if run (14 arms, VAL, one codeword)

`BASE`, `KO`, `KO+CAND`, `KO+RAND×10` (rank/norm-matched, the same basis file as P2a), `noKO+CAND`
(side-effect check). ≈ **18 GPU-h + ~$1 judge** for button. A 56-control family would be ≈ 76 GPU-h
and ~$4 — and still underpowered for the primary.

## 6. Mediation-language rules (binding if P7 ever reports)

* Never "the rescue causes the behaviour" from a joint change; the chain needs the intervention to
  move installation **and** behaviour on the **same rows**, with the control arms separating them.
* Preserve the inherited null: semantic/refusal changes have **not** moved content-true attack
  success in this project (DR-070/073, powered).
* Never report raw LLM-judge ASR as the endpoint, and never exclude rows by ASR.
