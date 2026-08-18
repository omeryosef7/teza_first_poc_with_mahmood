# Boombness sprint — continuation log

**Opened 2026-08-18.** Governing documents:
`docs/BOOMBNESS_OBJECTIVE_SPRINT_PLAN.md` (authoritative on what to do) ·
`docs/BOOMBNESS_SPRINT_EXTERNAL_CRITIQUE_2026-08-18.md` (authoritative on what is broken) ·
`docs/BOOMBNESS_SPRINT_PROGRESS.md` (prior execution log — grep, do not read linearly; its clock is wrong).

**Analysis interpreter (was a `<conda-env>` placeholder in the report's repro block, now resolved):**
`/home/sharifm/students/omeryosef/miniconda3/envs/poc_stage2/bin/python` — scipy 1.17.1, sklearn 1.9.0,
torch 2.7.1+cu126. The **login shell python has none of these**; every analysis command must use the
full path above.

**Rule this log exists to enforce:** every number in the final report must be regenerable by a
committed script from a committed artifact. If the script and the artifact cannot both be named, the
number does not go in.

---

## Phase board

| plan § | subject | status | evidence / blocker |
|---|---|---|---|
| — | Phase 0 orient + this log | **DONE** | this file |
| — | Phase 1.1 `t_sf` | **DONE — verified** | see defect T4 |
| — | Phase 1.2 comprehension readout | **IN PROGRESS** | blocks every "non-destructive" claim |
| — | Phase 1.3 `analyze_steering` | NOT STARTED | |
| — | Phase 1.4 `surgical_knockout` dst | NOT STARTED | G3 not established until done |
| — | Phase 1.5 Tier-2 remainder | NOT STARTED | |
| §15 | missing report sections 2/6/7/14/15/16 | NOT STARTED | item 7 (metric comparison) is the substantive one |
| §9 | `correlation_summary.json`, `regression_summary.md` | NOT STARTED | named outputs never produced |
| §8/§9 | 9 of 12 named plots | NOT STARTED | |
| §5.2 | alpha sweep dose 0.25 | NOT STARTED | the dose every behavioural claim rests on was never swept |
| §14 | ClearHarm arm | NOT STARTED | **highest-value new result** — discriminates mechanism from bank artifact |
| §4.1 | strength / consistency / example_position | NOT STARTED | generated, confounded, unanalysed — decide analyse-or-delete |

## Gate table

| gate | question | current answer | strength |
|---|---|---|---|
| §2.6 | does any intervention preserve comprehension? | **UNKNOWN — the readout is broken** | every §4b verdict sits inside a 1e-5 probability tail |
| §13 | may we claim "we found the mechanism"? | **NO** | six criteria, not all met |
| §12 | build the GCG objective? | **REOPENED, undecided** | the report states this both ways; see Tier-3 |

---

## Defect table — external critique's 31 findings

Status: `open` → `fixed` (code changed) → `verified` (a test fails the old code, or the number is
recomputed and diffed). `refuted` means I checked and the finding does not hold as stated.

| id | tier | file:line | finding | status | note |
|---|---|---|---|---|---|
| T1 | 1 | `score_behavior.py:308` | comprehension readout scores leading-space tokens the model never emits | **open** | **scope is wider than the critique states — see C-1 below** |
| T2 | 1 | `analyze_steering.py:151` | unconditional `KeyError: 'wilson95'`; committed artifact is pre-fix | open | |
| T3 | 1 | `surgical_knockout.py:271` | edge ranking still at the retracted destination token | open | G3 headline not established |
| T4 | 2 | `analyze_g8.py:52` | `t_sf` continued fraction omits the symmetry transform | **VERIFIED FIXED** | **partly refuted as stated — see C-2** |
| T5 | 2 | `analyze_g64/g2/g9` | permutation p tests a different estimand than the ρ beside it | open | |
| T6 | 2 | `g2` / `probes:393` / `reanalyze_corrected:185` | uncorrected layer selection; Holm family is 10 not 32 | open | |
| T7 | 2 | `surgical_knockout.py:239,225` | cross-fitting abandoned for ~54% of rows; family head-truncation | open | |
| T8 | 2 | `extract_boombness.py:484` + 3 | `--fit-dir` consumers never validate `payload["meta"]` | open | latent: all 63 runs currently match |
| T9 | 2 | `aggressive_patching.py:461`, `probes.py:236` | single-draw controls presented as bands | open | |
| T10 | 2 | `aggressive_patching.py:188` | readout layers overlap patched windows → tautological | open | `semantic_logodds` unaffected |
| T11–T17 | 3 | reports | report states its conclusion both ways; `§0.3` dangling; G1 headline superseded | open | Phase 4 |
| T18+ | 4 | various | plan sections not done or not reported | open | Phases 2–3 |

## Corrections to the external critique

The critique is authoritative on *what is broken*, but it is not itself above verification. Two of its
claims do not survive re-derivation as stated. Both are recorded here rather than quietly adjusted.

**C-1 — T1's scope is WIDER than reported (worse, not better).** The critique flags only the
`comprehension_usage` readout. Measured on the same committed baseline
(`score_behavior/base_20260816_203355_3985444/results.jsonl`), the `semantic_one_word` readout has the
identical defect and is **an order of magnitude further into the tail**:

| readout | n | median mass on the option pair | p90 | max | rows >1% |
|---|---|---|---|---|---|
| comprehension | 288 | 4.400e-05 | 2.109e-04 | 1.165e-03 | **0/288** |
| **semantic** | 516 | **5.595e-06** | 1.130e-04 | 4.226e-04 | **0/516** |

`semantic_logodds` is the readout carrying **G1 / plan §5 — the +68%-of-span headline** and every cell
of `decision_gate.md` Q1. So the fix and the re-run are larger in scope than the critique's "re-run
§4b". Whether this *invalidates* G1 is a separate question — a tail log-odds is a defensible readout of
an internal representation, which is what G1 claims, in a way it is not defensible for a
"does the model still comprehend" claim. To be resolved by the re-run, not by argument.

**C-2 — T4 is real but its stated magnitude is wrong by ~20×.** The critique says the continued
fraction is wrong "for all |t| < 1.69 at df=5". Re-derived against `scipy.stats.t`: that is the region
where convergence is not *guaranteed* (t < 1.464 at df=5), but with 200 Lentz iterations the CF in fact
converges to <1e-6 relative error down to |t| ≈ 0.08. Verified grid in `tests/test_boombness_stats.py`.

I then swept **all 726 committed JSON artifacts** for published p-values reproducible from the buggy
function and inconsistent with `scipy`. **Exactly one is corrupted**, and it is the one the critique
found:

```
outputs/boombness/g9_three_predictor_lastpos.json
  models/boombness+refusalness/terms/refusalness   t=0.01138  G=6
  p_cr1  published 0.7656  ->  true 0.9914
```

The correction makes an already-null term **more** null. **No conclusion in the sprint changes.** The
fix is still right and still worth having — the error direction is always anticonservative, so the next
occurrence might not have been harmless — but "every clustered p in the sprint is wrong" is not what
the artifacts show, and the recommended-order item 1 rationale ("it touches every clustered p") is
overstated.

## Retraction / correction log (this session)

*(none yet — C-1 and C-2 above are corrections to the critique, not to the sprint's own claims)*

## Tick log

| # | time | action | outcome |
|---|---|---|---|
| 1 | 2026-08-18 | Phase 0: read plan + critique; resolved analysis interpreter; opened this log | — |
| 2 | 2026-08-18 | Phase 1.1: `t_sf`/`_betainc`/`t_crit` → scipy-backed, symmetry transform added to fallback; `tests/test_boombness_stats.py` (4 tests, each fails pre-fix code) | 1 of 726 artifacts corrupted; no conclusion changes |
| 3 | 2026-08-18 | measured the option-pair mass for **both** readouts on the committed baseline | T1 is wider than reported: `semantic` is 5.6e-06 median (C-1) |
