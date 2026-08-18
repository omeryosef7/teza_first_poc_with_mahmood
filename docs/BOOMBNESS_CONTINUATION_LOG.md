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
| — | Phase 1.2 comprehension readout | **FIXED, smoke running** | jobs 764702/764703 measure prefix vs no-prefix |
| — | Phase 1.3 `analyze_steering` | **DONE — artifact replaced** | no G4 conclusion changes; intervals were 1.03–1.69× too narrow |
| — | Phase 1.4 `surgical_knockout` dst | **code fixed, UNVERIFIED; GPU re-run pending** | G3 not established until re-run |
| — | Phase 1.5 Tier-2 remainder | **PARTIAL** | T5 done for g64 only; T6/T9/T10 landed unverified; T8 + silent-failures NOT STARTED |
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
| T1 | 1 | `score_behavior.py:308` | comprehension readout scores leading-space tokens the model never emits | **fixed — smoke running** | scope wider than reported (C-1). Fix = forced answer position + fatal `--min-option-mass` gate + per-row `option_mass` |
| T2 | 1 | `analyze_steering.py:151` | unconditional `KeyError`; committed artifact is pre-fix | **VERIFIED FIXED** | re-run: all point estimates bit-identical, intervals 1.03–1.69× wider. `require_done` now covers the arms too |
| T3 | 1 | `surgical_knockout.py:271` | edge ranking still at the retracted destination token | **code fixed, unverified** | needs a GPU re-run before G3 is established |
| T4 | 2 | `analyze_g8.py:52` | `t_sf` continued fraction omits the symmetry transform | **VERIFIED FIXED** | **partly refuted as stated — see C-2** |
| T5 | 2 | `analyze_g64/g2/g9` | permutation p tests a different estimand than the ρ beside it | **PARTIAL** | `analyze_g64` done + re-run (135/135 pooled ρ bit-identical). `analyze_g2:322` and `analyze_g9:376` still carry the unlabelled pairing |
| T6 | 2 | `g2` / `probes:393` / `reanalyze_corrected:185` | uncorrected layer selection; Holm family is 10 not 32 | **code fixed, unverified** | agent concluded the family IS 32 and the code was wrong; needs my re-check |
| T7 | 2 | `surgical_knockout.py:239,225` | cross-fitting abandoned for ~54% of rows; family head-truncation | open | |
| T8 | 2 | `extract_boombness.py:484` + 3 | `--fit-dir` consumers never validate `payload["meta"]` | open | latent: all 63 runs currently match |
| T9 | 2 | `aggressive_patching.py:461`, `probes.py:236` | single-draw controls presented as bands | **code fixed, unverified** | re-runs pending (both need GPU) |
| T10 | 2 | `aggressive_patching.py:188` | readout layers overlap patched windows → tautological | **code fixed, unverified** | `semantic_logodds` unaffected, so G1 headline does not depend on it |
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

**C-3 — §6.4 could not regenerate itself, and the critique missed it here.** The critique names the
"no script regenerates this" provenance failure for §11's role statistics. `g64_summary.json` had the
same defect and was not flagged: it recorded **no input paths and no argv**, so reproducing §6.4 meant
guessing among 16 extract runs, 20+ judge runs and 2 probe-score runs. Reconstructed inputs reproduce
`coverage 270/270/72/72` exactly, which confirms the reconstruction; `analyze_g64.py` now records
argv, resolved input paths, git commit and dirty flag.

## Unverified-fix register

Seven of nine workflow agents were killed by a session limit mid-task. Four left **complete, parsing,
test-backed edits but never reported and were never adversarially verified** (their verifier stage
died too). 50 tests pass across the new files, which is evidence but not verification — the tests were
written by the same agent that wrote the fix.

| file | tests | status |
|---|---|---|
| `analyze_steering.py` | `test_analyze_steering.py` | **verified by me** — re-ran, diffed every field |
| `reanalyze_corrected.py` | `test_holm.py` | agent reported; **needs my re-check of the m=32 argument** |
| `probes.py` | `test_probes_selection.py` | **unverified** |
| `aggressive_patching.py` | `test_patching_readout.py` | **unverified** |
| `surgical_knockout.py` | `test_surgical_knockout.py` | **unverified** |
| `analyze_g64.py` | — | **verified by me** — re-ran, diffed all 135 rows |

Never started: the silent-failure group (`extract_boombness`, `judge_boombness`, `coherence_gate`,
`common`, `prompt_families`) and the `analyze_g2` / `analyze_g9` half of T5.

## Retraction / correction log (this session)

*(none yet — C-1/C-2/C-3 are corrections to the critique, not to the sprint's own claims)*

## Tick log

| # | time | action | outcome |
|---|---|---|---|
| 1 | 2026-08-18 | Phase 0: read plan + critique; resolved analysis interpreter; opened this log | — |
| 2 | 2026-08-18 | Phase 1.1: `t_sf`/`_betainc`/`t_crit` → scipy-backed, symmetry transform added to fallback; `tests/test_boombness_stats.py` (4 tests, each fails pre-fix code) | 1 of 726 artifacts corrupted; no conclusion changes |
| 3 | 2026-08-18 | measured the option-pair mass for **both** readouts on the committed baseline | T1 is wider than reported: `semantic` is 5.6e-06 median (C-1) |
| 4 | 2026-08-18 | fanned out 9 agents over the disjoint Tier-2 files | **7 killed by a session limit**; 2 completed; 4 left unreported but test-backed edits (see register above) |
| 5 | 2026-08-18 | Phase 1.2: forced answer position, per-row `option_mass`, fatal `--min-option-mass`, `else` branch on the query-kind dispatch, `semantic_forced_choice` wired in | smoke 764702 (prefix) / 764703 (no prefix) submitted |
| 6 | 2026-08-18 | Phase 1.3: verified + re-ran `analyze_steering`, replaced the committed artifact | every estimate bit-identical; intervals 1.03–1.69× too narrow; commit `accfa714` had never executed |
| 7 | 2026-08-18 | re-ran `analyze_g64` after the T5 rename; added provenance | 135/135 pooled ρ bit-identical; coverage reproduces 270/270/72/72 (C-3) |
