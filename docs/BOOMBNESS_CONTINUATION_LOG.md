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
| — | Phase 1.2 comprehension readout | **FIXED TWICE — smoke 764744 running** | forced prefix (476× mass) then whole-answer scoring (the codeword has no capitalized single token) |
| — | Phase 1.3 `analyze_steering` | **DONE — artifact replaced** | no G4 conclusion changes; intervals were 1.03–1.69× too narrow |
| — | Phase 1.4 `surgical_knockout` dst | **code fixed, UNVERIFIED; GPU re-run pending** | G3 not established until re-run |
| — | Phase 1.5 Tier-2 remainder | **PARTIAL** | T5 done for g64 only; T6/T9/T10 landed unverified; T8 + silent-failures NOT STARTED |
| §15 | missing report sections 2/6/7/14/15/16 | **PARTIAL** | item 7 (metric comparison) **written** as report §7b; 2/6/14/15/16 outstanding |
| §9 | `correlation_summary.json`, `regression_summary.md` | NOT STARTED | named outputs never produced |
| §8/§9 | 9 of 12 named plots | NOT STARTED | |
| §5.2 | alpha sweep dose 0.25 | NOT STARTED | the dose every behavioural claim rests on was never swept |
| §14 | ClearHarm arm | **★ DECOMPOSED** | B +0.105 / C +0.233 / D +0.430 vs random +0.013–0.018. AdvBench replication 765111–114 |
| §4.1 | strength / consistency / example_position | NOT STARTED | generated, confounded, unanalysed — decide analyse-or-delete |

## Gate table

| gate | question | current answer | strength |
|---|---|---|---|
| §2.6 | does any intervention preserve comprehension? | **ANSWERED for `project_out`: it IMPROVES it** | Δ +0.2795, p=0.0010, control −0.0041 (p=0.63), on the corrected readout |
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
| T6 | 2 | `g2` / `probes:393` / `reanalyze_corrected:185` | uncorrected layer selection; Holm family is 10 not 32 | **PARTIAL — Holm half VERIFIED, consequence REFUTED (C-4)** | `probes` best-layer + `g2` layer selection still open |
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

**C-4 — T6c's consequence is REFUTED; only its code/docstring half stands.** The critique predicted
that at m=32 "L4's p=0.001631 exceeds the 0.001613 threshold and **stops being rejected**", which
would have knocked out a backstop the report cites twice. Re-derived from
`extract_boombness/full_20260816_185942_1008673` with the fixed `holm_table`:

| family rule | m | rejected set |
|---|---|---|
| displayed layers (what the code did) | 10 | **[4, 31]** |
| **available layers, all actually tested** (the honest family) | **32** | **[1, 4, 31]** |
| the 10 displayed p-values ranked against α/(32−i) | 32 | [31] |

The critique's number is the **third row** — ranking a displayed subset against a larger family's
thresholds without testing the rest. That is not Holm; a step-down over m hypotheses requires m
p-values. Done properly the correction is *stricter* and L4 still clears (p=0.001631 vs thr=0.001667),
gaining L1. The report's multiplicity backstop is not weakened, it is strengthened, and the report
line has been corrected to "L1, L4 and L31" with the artifact committed. **The real defect stands**:
code and docstring disagreed, and nothing recorded the family size. Both now do.

**C-5 — T1 is worse again, and the fix the critique recommends would not have worked.** The critique
proposes "sum `full_word_ids`, minding that the option sets are asymmetric (4 variants for literal,
2 for coded)". Measured on smoke jobs 764702/764703 (36 prompts), a forced `Answer:` prefix raises
option mass **476×** on comprehension (5.6e-05 → 0.0268) and **331×** on semantic (1.7e-04 → 0.0553),
taking rows above 1% of next-token mass from **0/36 to 36/36**. But decoding what the model actually
wants at that position shows the readout was still wrong:

| readout | argmax next token (with prefix) |
|---|---|
| comprehension | `' Literal'` 10/24 · `' Liter'` 6/24 · `' Neither'` 4/24 |
| semantic | `' Car'` 8/12 · `' Neither'` 3/12 · `' Bomb'` 1/12 |

The model **capitalises**, and the capitalised codeword is **multi-token**: `' Car'` is the first
subtoken of `' Carrot'`, which `readout_ids` rejects *by design* because `car` is the generic English
word. On Llama-3.1-8B `bomb` has four single-token variants and `carrot` has exactly **one**. So no
single-next-token readout can represent the model's preferred spelling of the codeword, and summing
`full_word_ids` — the critique's recommended fix — gives the concept **four ids against the
codeword's one**: the same bias with a larger constant. This is a measurement-validity problem in
`semantic_logodds`, the readout carrying **G1's +68%-of-span headline**.

Fixed by scoring the **answer** rather than a token: `signals.string_option_readout` teacher-forces
each option's whole surface form and logsumexps over an identically-built variant set (2 per option,
same rule), so symmetry is a property of the construction rather than of tokenizer luck.
`P(model answers "Carrot")` = `P(' Car')·P('rot' | ' Car')` is a joint probability, so no length
normalisation is wanted. Smoke 764744 confirms the fix works, and by a wide margin:

| readout | original | + forced prefix | **+ whole-answer** |
|---|---|---|---|
| comprehension | 5.6e-05 | 0.0268 | **0.297** |
| semantic | 1.7e-04 | 0.0553 | **0.541** |
| rows >1% | 0/36 | 36/36 | 36/36 |

**5,300× and 3,200×** over the original. The options now hold 30–54% of the answer probability, i.e.
it is finally a forced choice. This is consistent with the repo's own 2026-08-16 diagnostic (0.979 on
the direct arm under a forced framing) that was applied to `semantic_forced_choice` and never
propagated.

**C-6 — the blast radius is THREE scripts, not one.** The critique scopes the fix to
"re-run §4b". The same single-token readout at the same unprefixed position also computes
`semantic_logodds` in:

| script | line | what it carries |
|---|---|---|
| `score_behavior.py` | 308 | §2.6 comprehension, report §4b — **fixed** |
| `aggressive_patching.py` | 439–445 | **G1, the +68%-of-span headline** — not yet fixed |
| `surgical_knockout.py` | 295 | **G3, the attention-edge result** — not yet fixed |

Both unfixed scripts are currently held by verification agents, so the port waits for that workflow
to land rather than racing it. Until then **G1 and G3 rest on a readout that cannot represent the
model's preferred spelling of the codeword**, and neither is re-derivable from current evidence.

**C-7 — the §2.6 result the previous session called its cleanest causal claim is computed with the
broken readout, so it is not yet evidence.** The prior session's headline was
"★★★ §2.6 SATISFIED FOR ARM D — it raises attack success WITHOUT damaging comprehension, and its
control does the opposite" (`outputs/boombness/g8_comprehension_DF_arms.json`, arm D
+0.38…+0.53 at every demo count, double-random control −0.08…−0.13). Every one of those numbers is a
`comprehension_logodds` — a log-ratio of two probabilities that together hold a **median 4.4e-05** of
the next-token mass. The ordering inside that tail may well survive the corrected readout; it may
not. Until §4b is re-scored with `--readout-ids whole_answer`, **arm D has no comprehension control**,
and per the plan's §2.6 rule that means it cannot be called non-destructive.

Consequently arm D is deliberately **NOT** written into the report yet, even though the critique
correctly notes it is missing from both. Writing numbers that are queued for re-derivation is the
exact failure this log exists to prevent.

### §4b re-run queue (blocked on GPU)
All at `--readout-ids whole_answer --answer-prefix Answer:`, comprehension + semantic forward
readouts, matched to the arms already judged:

| arm | intervention | why |
|---|---|---|
| baseline | — | the paired reference for every delta |
| D | `d_surface:project_out:8-8 + refusalness:project_out:18-18` | the headline causal arm |
| Dctrl | `random:project_out:8-8 + random:project_out:18-18` | its matched double-random control |
| F / Fctrl | add-Boombness + remove-refusal, and control | §10.4's other composed arm |
| ±0.25, random, project_out | §12 steering arms | report §4b's four original verdicts |

### ★ The session's main new result — plan §14, ClearHarm

179 external harmful prompts. **No codeword, no demonstrations, no doublespeak wrapper.** All arms
coherence-gated individually, 100% coverage of the common set, 6 category clusters.

| arm | intervention | ASR | paired Δscore | refusal |
|---|---|---|---|---|
| baseline | — | 0.101 | — | 0.877 |
| **B** | remove `d_surface` (L8) | **0.207** | **+0.1047 ± 0.0238** | 0.760 |
| **C** | remove refusal (L18) | **0.341** | +0.2325 ± 0.0328 | 0.615 |
| **D** | remove both | **0.542** | +0.4295 ± 0.0362 | 0.447 |
| Dctrl | double random | 0.112 | +0.0126 ± 0.0107 | 0.872 |
| band draw 1 | double random | 0.117 | +0.0182 ± 0.0097 | 0.872 |

**Arm B is the load-bearing row.** `d_surface` was fitted on the carrot/bomb 2×2, and removing it
raises compliance on harmful requests containing **no codeword at all**, against random directions at
+0.013/+0.018. The direction is not arbitrary and the effect is not a property of the prompt bank —
which was the most serious threat to every late finding in this sprint.

**It is also not the refusal direction under another name.** cos(`d_surface`, refusal) = **0.019 at
L18**, 0.13 at L12 — near-orthogonal. *Caveat:* arm B acts at **L8**, where no house refusal direction
exists, so the cosine is measured only where both are fitted.

**NOT established — super-additivity.** The joint exceeds the sum of singles by **+0.0922**, but the
domain-clustered bootstrap CI is **[−0.1474, +0.1332]** with 21% of draws ≤ 0. This is the ClearHarm
cluster imbalance doing precisely what `external_bank.py` warned it would: 127 of 179 rows sit in one
category, so the domain bootstrap is dominated by it. **AdvBench heldout** (16 clusters, largest 26%)
is the set that can actually test it, it was built in the same commit for exactly this reason, and
arms 765111–114 are running it.

**What this does and does not license.** It licenses: "removing this direction causally raises
compliance on harmful requests generally, and it is a distinct channel from refusal". It does **not**
license calling `d_surface` "concept-ness" off-bank — the 2×2 named it from a contrast that does not
exist in a prompt with no codeword. Its off-bank behaviour is a new fact that needs its own
interpretation, not an extension of the old one.

## Unverified-fix register

Seven of nine workflow agents were killed by a session limit mid-task. Four left **complete, parsing,
test-backed edits but never reported and were never adversarially verified** (their verifier stage
died too). 50 tests pass across the new files, which is evidence but not verification — the tests were
written by the same agent that wrote the fix.

| file | tests | status |
|---|---|---|
| `analyze_steering.py` | `test_analyze_steering.py` | **verified** — re-ran, diffed every field |
| `reanalyze_corrected.py` | `test_holm.py` | **verified** — both family rules, artifact committed (C-4) |
| `probes.py` | `test_probes_selection.py` | **VERIFIED — verdict INCOMPLETE, further defects fixed** |
| `aggressive_patching.py` | `test_patching_readout.py` | **VERIFIED — verdict INCOMPLETE, further defects fixed** |
| `surgical_knockout.py` | `test_surgical_knockout.py` | **VERIFIED — verdict INCOMPLETE, further defects fixed** |
| `analyze_g64.py` | — | **verified** — re-ran, diffed all 135 rows |
| `analyze_g2/g9`, `common`, `extract_boombness`, `judge_boombness`, `coherence_gate`, `prompt_families` | `test_estimand.py`, `test_silent_failures.py` | **completed** (the two groups killed by the session limit) |

All three verifiers returned **INCOMPLETE** and found real defects in the patch they were checking.
Suite: **338 passed, 6 failed**, all six pre-existing `module_imports_without_torch` checks in legacy
GCG/reinforce files untouched by this session.

**The most instructive one:** `probes`' new leakage guard was **itself a dead guard**. At `K=1` the
z-score is `excess/se` with `se = NaN`, which yields `leak = False` — so a run whose stopping rule was
never evaluable wrote `DONE.json` and exited 0, precisely the failure the commit existed to remove.
The whole of `probes.main()` had never executed under test, which is why both this and a
`p_perm = 0.0000` (an empirical p from K draws with no `1/(K+1)` floor) survived. **Fifth dead guard,
and the first one this project shipped *while fixing* dead guards.**

Never started: the silent-failure group (`extract_boombness`, `judge_boombness`, `coherence_gate`,
`common`, `prompt_families`) and the `analyze_g2` / `analyze_g9` half of T5.

**C-8 — the probe-leakage finding is REFUTED.** The critique states that `probes`' own stopping rule
("shuffled AUROC meaningfully above 0.5 means the split is leaking") is violated at layers
8/24/28/31. Those four values are real, but the object they were compared against was a **single
permutation reused across every fold** — not a draw from the null. Against K=20 independent draws on
the same data (`extract_boombness/full2352_...`, regime d5):

| layer | single draw | null mean | null sd | max of 20 | z | flagged? |
|---|---|---|---|---|---|---|
| 8 | 0.5829 | 0.4933 | 0.0571 | 0.6206 | −0.52 | **no** |
| 24 | 0.6302 | 0.5148 | 0.0638 | 0.6578 | 1.04 | **no** |
| 28 | 0.5763 | 0.5103 | 0.0577 | 0.5943 | 0.80 | **no** |
| 31 | 0.5812 | 0.5214 | 0.0615 | 0.6767 | 1.55 | **no** |

No layer is flagged (max excess 0.021 against a 0.05 tolerance). **The splits are not leaking.**
Separately, the selection-on-test bias the critique flags at `probes.py:393` is real but now
*measured* rather than assumed: nested selection moves d5 from 0.9855 to 0.9843 and d6 from 0.9849 to
0.9831 — **0.0012–0.0018 AUROC**. No conclusion changes, and `selection_is_stable=False` confirms the
argmax was noise.

**C-9 — plan §9 decision question 5 is ANSWERED, and G2 survives it.** Open since the plan was
written; `n_examples` had only ever been a filter. Added as a regressor with the same CR1 +
within-domain permutation inference:

| position | boombness β before | after | retained |
|---|---|---|---|
| `codeword_last` (headline) | +0.08887 | **+0.08879** | **99.9%** |
| `last` | +0.0253 | **+0.0414** | grows 1.63× |

Partial ρ(boombness, ASR │ n_examples) = **+0.2705** pooled / +0.2643 within-domain (perm p=0.0015)
against a raw +0.3067. ⛔ *(All of C-9's figures are computed on the unfiltered 234-row set and are **superseded by R-18** — see below; C-9 was defending a correlation that is not present on the clean rows.)* The reason it is not a confound is measurable: `n_examples` predicts ASR
(ρ=+0.206) but is essentially **uncorrelated with boombness at `codeword_last`** (ρ=−0.034). At the
last-token position it correlates −0.185 and acted as a **suppressor**, not a confound. **G2 is
defended against the dose-response confound the critique raised.**

**C-10 — two provenance holes worse than §6.4's.** `analyze_g2.py` never recorded its
`--refusalness` directory, yet `g2_analysis_cwpos.json` ships a full `mediation` section computed
from it, and the only invocation in the progress log omits the flag entirely. And **no committed
invocation of `analyze_g9.py` exists anywhere** — its inputs were reconstructible only because the
artifact happens to echo them as separate keys. Both scripts now record `provenance{argv, git_commit,
git_dirty, python}`; the recovered refusalness paths reproduce every mediation number.

### ★ R-6 resolved — and it resolves in the sprint's favour

§4b re-run on the whole-answer readout, paired by prompt, domain-clustered
(`outputs/boombness/section4b_whole_answer.json`):

| arm | comprehension Δ | p | semantic Δ | p |
|---|---|---|---|---|
| Dctrl (double random) | −0.0041 [−0.025, +0.016] | 0.63 | +0.0666 | 0.0004 |
| **`project_out` `d_surface`** | **+0.2795** [+0.175, +0.384] | **0.0010** | **+2.4073** | <1e-4 |

The withdrawn claim was "comprehension unchanged, p=0.681". The corrected answer is not merely
different, it is **opposite in kind**: removing `d_surface` *increases* the coded reading by +0.28
log-odds while the norm-matched control is flat.

**The semantic row is the mechanistically important one.** Removing the surface-identity direction
moves the model **+2.41 log-odds** toward answering with the **concept** rather than the **codeword** —
the first direct confirmation that `d_surface` does what its name claims, on an instrument that can
represent both answers (the previous one structurally could not, since `carrot` has no capitalised
single-token form). Together with the ClearHarm decomposition: `project_out d_surface` raises attack
success, increases the coded reading, and increases the concept reading, while its control does none
of the three.

## Retraction / correction log (this session)

**R-12 (mine) — the ClearHarm control band was n=1.** `score_behavior.py:123` recursed into composed
arms **without passing `control_seed`**, so every sub-spec fell back to the default 20260816
regardless of `--seed`. The 2026-08-17 fix threaded the seed into the *single*-spec path and missed
this one: same parameter, same one-of-two-paths shape, second time.

| `--seed` | draw seeds actually used (pre-fix) |
|---|---|
| 20260901 | `[20260824, 20260834, 20260824, 20260834]` |
| 20260902 | `[20260824, 20260834, 20260824, 20260834]` |
| 20260903 | `[20260824, 20260834, 20260824, 20260834]` |

Byte-identical `gens.jsonl` across all three (sha256 `276b6af46eb68a76`). The reported
"3-draw band, between-draw sd **0.0048**" was one draw stated three times — and **retraction #7's
fake band reported sd 0.0049**. A control band is the one artifact whose entire purpose is to measure
draw-to-draw variance, which makes it the one artifact that cannot be falsified by looking at its own
value. Both times the tell was arms agreeing to four decimals.

**Scope:** arms B/C/D use real fitted directions and are unaffected; `Dctrl` remains a valid *single*
control, so arm B (+0.105) vs control (+0.013) stands. What was not established is the between-draw
variance. No other composed control in the sprint carried a band claim. Band relaunched 765210–212.

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
| 8 | 2026-08-18 | verified the Holm fix: re-ran both family rules, wrote `reanalyze_corrected_d_surface_cos.json`, corrected the report line | **critique's consequence refuted** — L4 survives at m=32; L1 added (C-4) |
| 9 | 2026-08-18 | paired smoke of the forced answer prefix (764702/764703) | 476×/331× more option mass; 0/36 → 36/36 rows above 1% |
| 10 | 2026-08-18 | decoded the argmax next token — found the capitalisation + multi-token-codeword asymmetry | **C-5**: the critique's recommended fix would not have worked; built whole-answer scoring instead |
| 11 | 2026-08-18 | first whole-answer smoke (764743) **FAILED** — `readout_id_pair` did not know the new mode | my own one-of-two-paths slip; died loudly, fixed, resubmitted as 764744 |
| 12 | 2026-08-18 | Phase 3: built `external_bank.py`; generated ClearHarm 179 + AdvBench 495; launched base/D/Dctrl (764745–747) | first ASR in this sprint from a set the bank did not generate |
| 13 | 2026-08-18 | ClearHarm arms died **179/179 with COMPLETED 0:0** — empty `target_surface` matches every token | my own one-of-two-paths fix; the FailureLedger is the only reason it was visible. Relaunched 764754–756 |
| 14 | 2026-08-18 | verification workflow returned: 3× INCOMPLETE + 2 completed groups | C-8 (probe leakage refuted), C-9 (§9 Q5 answered, G2 survives), C-10 (provenance) |
| 15 | 2026-08-18 | pinned three self-invalidating tests that loaded the pre-fix module via `git show HEAD:` | committing a fix turned its own tests red with no regression |
| 16 | 2026-08-18 | ClearHarm base + control judged 179/179; arm D judging | first external-set ASR in the sprint |
| 17 | 2026-08-18 | ★ **ClearHarm arm D: 0.101 → 0.542**, double-random control +0.011, refusal 0.877 → 0.447, all arms coherence-gated | the bank-artifact explanation is **excluded**. Decomposition (B/C) + 3-draw band launched |
| 18 | 2026-08-18 | wrote report **§7b**, the metric comparison (plan §15 item 7) that appeared in neither report | three metrics disagree in **sign** about ASR at L12; all three agree on comprehension |
| 19 | 2026-08-18 | rewrote report §0: one conclusion, retraction table R-6…R-11, `§0.3` resolved, G1 → +68%, interpreter path fixed | the gate table no longer contradicts the body |
| 20 | 2026-08-18 | added the five new retractions to `retraction_sweep.py` **the same day they were declared** | it immediately caught **4 unqualified stale claims** the old list called clean; all fixed, sweep clean over 4 files |
| 21 | 2026-08-18 | ClearHarm **decomposition**: B/C/D + a judged band draw | arm B alone is **+0.105** vs random +0.013 — `d_surface` is causal off-bank |
| 22 | 2026-08-18 | super-additivity test, domain-clustered bootstrap | **+0.0922, CI [−0.147, +0.133] — NOT established**; the one-dominant-cluster problem, as predicted |
| 23 | 2026-08-18 | cos(`d_surface`, refusal) = 0.019 @L18 | the two arms are **not** the same channel |
| 24 | 2026-08-18 | launched AdvBench replication (765111–114) + judged band draws 2/3 | 16 clusters is the design that can test super-additivity |
| 25 | 2026-08-18 | §4b whole-answer re-runs 765052–765055 running | unblocks R-6, arm D's comprehension control, and G1 |
| 26 | 2026-08-18 | §4b re-run: `project_out` comprehension **+0.2795 (p=0.0010)**, semantic **+2.4073** | **R-6 resolved in the sprint's favour**; `d_surface` confirmed to do what its name claims |
| 27 | 2026-08-18 | tail gate fired on arm D and destroyed a healthy comprehension readout | restructured: per-`query_kind`, **after** `finish()`, exit 4 |
| 28 | 2026-08-18 | caught the band draws returning byte-identical generations | **R-12** — composed recursion dropped the seed; retraction #7 re-created |

---

# Session 2 — opened 2026-08-19

**How session 1 ended.** Not at a stopping point: it died between tick 28 and its harvest. At the
moment it stopped, **seven GPU runs had COMPLETED and none had been judged** — the four AdvBench
replication arms (765111–114, launched at tick 24 to test super-additivity on 16 clusters, which the
ClearHarm cluster imbalance could not) and the three relaunched control-band draws (765210–212, the
R-12 fix). The scientific question tick 22 left open was therefore answerable from artifacts already
on disk. That is the first thing this session did.

## Inherited-state audit (before touching anything)

| check | result |
|---|---|
| SLURM queue | **empty** — nothing was still running, so nothing was lost by the session ending |
| `ab_base/B/C/D` | all 4 `DONE.json`, `option_mass_gate: PASS`, `n_bank_rows` 495 |
| `ctrlband_s2026090{1,2,3}` (19:09–19:14) | all 3 `DONE.json`, `n_bank_rows` 179 |
| judged? | **none of the 7** — no judge run references `ab_*` or the 19:09 band dirs |
| **R-12 fix worked?** | **YES** — the 3 band draws have *distinct* `gens.jsonl` sha256 (`61249763…`, `3b962119…`, `485698e9…`). The pre-fix draws were byte-identical; these are not. |
| AdvBench arms genuinely distinct? | **YES** — 4 distinct gens sha256, and `config.args.intervene` differs per arm as designed |
| `arm: base` in all 4 summaries | **not a defect.** `--arm` is the prompt-construction label; the intervention is recorded separately in `args.intervene`. Verified per-arm. |
| 765053 / 765177 FAILED | **both are guards working.** 765053: the `--min-option-mass` gate refused a semantic readout at median mass 0.03743 < 0.05. 765177: the tail gate flagged `semantic_one_word` at 0.01205 and exited non-zero *after* writing the run. Two of the six dead guards this project shipped now have live successors that have actually fired. |

**Arms as specified (confirmed from `config.args.intervene`, not from the tag):**

| tag | intervene | seed |
|---|---|---|
| `ab_base` | *(none)* | 20260816 |
| `ab_B` | `d_surface:project_out:8-8:1.0` | 20260816 |
| `ab_C` | `refusalness:project_out:18-18:1.0` | 20260816 |
| `ab_D` | `d_surface:project_out:8-8:1.0+refusalness:project_out:18-18:1.0` | 20260816 |
| `ctrlband_s2026090{1,2,3}` | `random:project_out:8-8:1.0+random:project_out:18-18:1.0` | **20260901 / 02 / 03 — distinct** |

## Tick log (session 2)

| # | action | outcome |
|---|---|---|
| 29 | inherited-state audit: queue, DONE flags, gens sha256, per-arm `intervene`, the two FAILED jobs | 7 runs complete and unharvested; **R-12 fix confirmed by distinct sha256**; both "failures" are guards firing correctly |
| 30 | launched judging of all 7 (3 parallel API streams; judging is OpenAI-bound, not GPU-bound, so it does not touch the 6-job SLURM cap) | `judge_ab_s1/s2/band_fix` |
| 31 | fanned out 7 fix agents over disjoint modules + 7 adversarial verifiers | see the Phase-1 close table below |

## Phase-1 close — what session 2 dispatched

Session 1's defect table left these open. Ownership is disjoint by file so the agents cannot collide.

| agent | files owned | defects |
|---|---|---|
| `aggressive_patching` | `aggressive_patching.py` | **C-6 (G1 readout port)**, T10 verify, T9 verify |
| `surgical_knockout` | `surgical_knockout.py` | **T3 verify (G3)**, T7a cross-fitting, T7b family truncation, **C-6** |
| `analyze_g2` | `analyze_g2.py` | T5 estimand, T6 layer selection, C-10 provenance |
| `analyze_g9` | `analyze_g9.py` | T5 estimand, **the 6th dead guard** (role-identifiability), T4 knock-on, C-10 |
| `probes` | `probes.py`, `role_probes.py` | T9 verify, T6 nested selection default, the K=1/NaN dead guard + `p_perm` floor |
| `common` | `common.py` | **`seed` + `tokenizer_revision` (plan §2.1 — absent from all 145+130 files)**, `bank_content_sha16` rename + the comparison that never existed, `finish()` guard, scipy audit |
| `silent_failures` | `extract_boombness.py`, `judge_boombness.py`, `coherence_gate.py`, `prompt_families.py` | **T8 `--fit-dir` meta validation**, the never-started silent-failure group, `bank_content_sha16` half, `--max-null-frac` abort |

**C-6 is the load-bearing one.** Session 1 fixed the readout in `score_behavior.py` and proved the fix
(5,300×/3,200× more option mass), but never ported it to the two scripts that carry **G1** and **G3**.
Confirmed still open at session-2 start: `signals.string_option_readout` exists at `signals.py:428`,
and both `aggressive_patching.py:~437` and `surgical_knockout.py:~295` still compute
`semantic_logodds` from the invalid single-next-token tail. **Until that port lands and re-runs,
neither G1's +68% headline nor G3 is re-derivable from current evidence.**

## ★ R-13 — the "matched footing" incremental table is the one table in that section whose footing is NOT matched

The external critique (Tier-3) states that the incremental-R² table "gives refusalness 5 predictors and
Boombness 1, and it flips at matched df". **Confirmed, by arithmetic, and the flip is real.**

**The published table — now WITHDRAWN** (report §3 ~L320, `§19 Q7`, short update L156):

| ⛔ *all four cells withdrawn* | Boombness adds over refusalness | refusalness adds over Boombness |
|---|---|---|
| @ codeword_last | +0.028 | **+0.144** |
| @ last token | +0.025 | **+0.091** |

**Where the withdrawn numbers come from.** `docs/BOOMBNESS_SPRINT_PROGRESS.md:2528` states it outright —
"all **five** refusalness layers jointly add +0.144 over Boombness" — and L2524 gives the components:
refusalness all-layers joint R² = 0.2565, `d_surface|L12|proj` alone = 0.1411. The joint model is
`boombness(1 column) + refusalness(5 columns)`, R² ≈ 0.285, and **both published cells are increments
against that same model**:

* `0.285 − 0.1411 = 0.144` ← refusalness's increment, **5 df** *(withdrawn)*
* `0.285 − 0.2565 = 0.0285` ← Boombness's increment, **1 df** *(withdrawn)*

R² is monotone in predictors, so a 5-df block mechanically adds more than a 1-df column. ⛔ The retracted table is
labelled "at matched footing" and sits **20 lines after** a retraction whose entire content is
"we compared these two probes at mismatched footing". It repeats the retracted error in the paragraph
that announces the retraction.

**The matched-df comparison already exists, committed, and has since the artifact was first added.**
`g9_three_predictor_{cwpos,lastpos}.json` fit `boombness_only` (1 col), `refusalness_only` (1 col) and
the 2-column joint on the same n=234:

| position | model R² (b / r / joint) | Boombness adds | refusalness adds |
|---|---|---|---|
| **@ codeword_last** | 0.1411 / 0.1759 / 0.2502 | **+0.0743** | **+0.1091** |
| **@ last token** | 0.006567 / 0.001275 / 0.006567 | **+0.00529** | **+4.5e-07** |

**Two conclusions change.**

1. **@ last token the comparison FLIPS.** Refusalness adds **4.5e-07** — nothing, to seven decimal
   places — over Boombness, while Boombness adds +0.0053 over refusalness. The published "+0.091 the
   other way" is entirely the 4 extra columns. §19 Q7's "less than refusalness adds beyond it" and the
   short update's "the increment comparison, **done correctly**, favours refusalness" are **false at
   this position**. The phrase "done correctly" is attached to the one cell that is computed wrongly.
2. **@ codeword_last the direction survives but the magnitude collapses.** Refusalness still adds more,
   but by **1.47×** (0.1091 vs 0.0743), not the **5.1×** the published table implies. The progress
   log's reading of it — "Boombness is close to redundant given refusalness" (L45, L2616) — is
   **withdrawn, not supported**: +0.0743 on a refusalness-only base of 0.1759 is a **42% increase** in explained
   variance. Not redundancy.

**Provenance note, and it is the worse half.** The published 0.144/0.028 pair is **not in any committed
artifact**, in any commit. `position_2x2.json` — the artifact the report names as the generator of this
section, and which was built specifically to make the table regenerable — contains **only
single-predictor R²** and no `incremental_r2` key at all. `g9_three_predictor_cwpos.json` has carried
0.1091/0.0743 in **all four** of its committed versions (`fe6755e8`, `2aa414a6`, `fb361288`,
`e42f5fc4`). So the report's numbers were never regenerable, and the artifact that *was* committed
disagreed with them the whole time. This is the standing bar — "if you cannot name the script and the
artifact, the number does not go in" — failing in the one section that claims to have fixed exactly
this failure.

**Not yet done, and it is the better test:** a symmetric *block* comparison (give Boombness 5 columns
too, or refusalness 1). The 1-vs-1 above is matched and citable now; the 5-vs-5 needs `analyze_g9` to
re-run and is queued behind the Phase-1 workflow that currently owns that file.

## ⛔⛔ R-14 — EVERY external-set ASR number in this sprint was judged against an EMPTY GOAL

**This is the most serious defect found in either session, and it invalidates the measurement behind
the sprint's best new result until it is re-judged.** It was caught by a guard that the Phase-1
`silent_failures` agent added *while my judge stream was running* — draws 1 and 2 of the control band
were judged by the old module, draw 3 by the new one, and draw 3 **aborted**.

### The defect

`judge_boombness.make_goal` reads the intended harmful request from **`final_query_text`, and nothing
else**. The generated bank carries that key. **Both external banks — ClearHarm and AdvBench — never
had it**; `external_bank.py:62` emitted the instruction as **`full_prompt`** only.

So for every external row: `q = row.get("final_query_text") or ""` → `""` → `make_goal` returns the
**empty string**. StrongReject was asked to score each completion **against no request at all**.

**Why nobody saw it.** The pre-fix `make_goal` returned a bare string with no status, so an empty goal
was recorded as `judge_status: "ok"` and counted in ASR exactly like a real one. And an empty-goal
StrongReject score still tracks *how harmful the response looks*, so the numbers moved with the
refusal rate and looked entirely reasonable — arm D's 0.101 → 0.542 against refusal 0.877 → 0.447 is
a coherent-looking table produced by an instrument that was never given the question.

### Proof, not inference

| evidence | |
|---|---|
| new judge on band draw 3, same inputs | `goal statuses: {'empty_query': 179}` → **ABORTED**, `judge_null_frac 1.0000 > 0.05` |
| `final_query_text` in `clearharm_179.jsonl` | **MISSING** (only `full_prompt`) |
| `final_query_text` in `advbench_heldout_495.jsonl` | **MISSING** (only `full_prompt`) |
| `final_query_text` in the generated bank | **present** |
| `--bank` passed by any ClearHarm judge run | **None** for all five (`ch_base`, `ch_B`, `ch_C`, `ch_D`, `ch_Dctrl`) — and it would not have helped, since the key was absent from the bank too |

### Scope — what is suspended

**⛔ Suspended pending re-judge — every figure named in this paragraph is WITHDRAWN as published:** report **§7c**, the §0 gate row **§10.4-D**, and tick
17/21/22's ClearHarm figures — baseline 0.1006, B 0.2067, C 0.3408, D 0.5419, Dctrl 0.1117, the
+0.0922 super-additivity estimate, and the control band. **Arm B (+0.106 vs +0.011), the row that
excludes the bank-artifact explanation, is suspended with the rest.**

**Not affected:** everything measured on the *generated* bank — G1, G2, G3, G4, §4b, the §10.4
Llama/Qwen3 arms, R-13. The generated bank has always carried `final_query_text`, and those judge runs
report real goal substitutions.

**Direction may well survive.** An empty-goal score is not random — it reads the response — so the
ordering D > C > B > baseline ≈ control is plausibly robust. But "plausibly robust" is not a
measurement, and the ASR values are not StrongReject-against-goal scores. **Re-judging decides it.**

### The fix

`external_bank.py` now emits `final_query_text` beside `full_prompt` (they are equal by construction
for an external set: the intended request *is* the instruction). Both banks regenerated, and the
regeneration is surgical — verified against the pre-fix files:

| bank | rows | `prompt_id` identical | keys added | other values changed |
|---|---|---|---|---|
| clearharm_179 | 179 → 179 | **yes, all** | `['final_query_text']` | **0** |
| advbench_heldout_495 | 495 → 495 | **yes, all** | `['final_query_text']` | **0** |

So **no generation needs re-running** — only re-judging, which is API-only and cheap. All existing
`gens.jsonl` still join on `prompt_id`.

### Two follow-ups this exposes

1. **A status mislabel remains.** `external_bank.py:78` stamps `concept="bomb"`, `codeword="carrot"`
   on external rows because `score_behavior` reads them off row 0 to build the readout option sets.
   With the goal now non-empty, `make_goal` will run the carrot→bomb substitution on external
   instructions. Measured: **0 of 179 and 0 of 495** contain "carrot", so the goal string is correct
   verbatim — but the *status* will come back `noop_codeword_absent` ("SUSPECT") for ~97% of rows
   instead of the correct `no_codeword_metadata`. The judge should recognise these rows by
   **`bank_block == "external"`** — by identity, per the house rule, not by guessing from an absent
   substitution. That is a `judge_boombness.py` change and is queued behind the Phase-1 workflow which
   currently owns that file.
2. **The AdvBench judging launched this session was killed mid-flight** and must be redone against the
   fixed bank. Nothing was lost but API time; the generations are intact and unchanged.

### The lesson, which is the same one twice

Retraction #7 and R-12 were both "a control band that could not be falsified by looking at its own
value". R-14 is the same shape one level up: **an ASR table cannot be falsified by looking at its own
numbers**, because a broken judge still returns a plausible ordering. Only the *goal string* — the
input nobody printed — reveals it. The sprint's own house rule says a guard untested against a case it
should fail is not a guard; here the guard did not exist at all until Phase 1 added it, and it fired
within hours of existing.

## Tick log (session 2, continued)

| # | action | outcome |
|---|---|---|
| 32 | **R-13**: traced the "matched footing" incremental-R² table to its source | it gives refusalness **5 predictors against Boombness's 1**; at matched df the last-token comparison **flips** (refusalness adds 4.5e-07). The published pair is in **no committed artifact**; `g9_three_predictor_cwpos.json` has disagreed with it in all four of its versions. Report + short update corrected. |
| 33 | G1 headline promoted to the stratified run | +68% CI [+50,+95], **24 families / 6 domains**, replacing the n=8 / 2-domain +84%. Disclosed that the **whole-prompt** transplant is null (+14%, CI [−9,+32]) and flagged the readout as pending re-derivation (C-6). |
| 34 | wrote report **§7c**, the ClearHarm decomposition | …and suspended it three ticks later (R-14). |
| 35 | built `analyze_condition_profile.py` and gave the Llama cross-condition table the same test the Qwen3 table already had | see **R-15** below — the "harmful yes, benign no" profile is **one significant cell of six** |
| 36 | ⛔⛔ **R-14** — external-set ASR judged against an **empty goal** | `external_bank.py` never emitted `final_query_text`. Fixed; both banks regenerated with every `prompt_id` preserved and **0** other values changed, so only re-judging is needed. AdvBench judge streams killed mid-flight. |
| 37 | launched the **Qwen3-14B ClearHarm replication at `max_new 512`** (766485–489, smoke 766483 clean) | also removes the audit's length confound: the published Llama-vs-Qwen3 non-replication compares a **512**-token Llama run against a **192**-token Qwen3 run |

## ★ R-15 — "harmful yes, benign no" is one significant cell out of six

⛔ The report's **SECOND CAUSAL RESULT** previously argued from a cross-condition profile — "≈0 on every
benign condition and ≈+0.056 on every harmful one", a "clean split" licensing the stronger claim
*harm-general, not doublespeak-specific*. That reading is **withdrawn**. That table shipped **six deltas and zero p-values**, while
the **Qwen3** table printed eleven lines below it carries `p_cl` on every cell and annotates two of
them "(n.s.)".

Given the same test (`analyze_condition_profile.py`, paired by `prompt_id`, domain-clustered t on the
correct 512-token runs `len_B` / `len_Bctrl`, n=960 — deltas reproduce the report exactly):

| condition | n | Δ | p_cl | domain-clustered CI |
|---|---|---|---|---|
| `benign_literal` | 324 | +0.0069 | 0.334 | [−0.010, +0.024] |
| `benign_remap` | 36 | +0.0104 | 0.745 | [−0.068, +0.088] |
| `concept_in_benign_ctx` | 72 | +0.0035 | 0.862 | [−0.045, +0.052] |
| **`natural_doublespeak`** | 420 | **+0.0560** | **0.0077** | **[+0.023, +0.089]** |
| `direct_harmful` | 72 | +0.0556 | 0.363 | [−0.087, +0.198] |
| `direct_codeword` | 36 | +0.0590 | 0.438 | [−0.121, +0.239] |

⛔ **Only `natural_doublespeak` is distinguishable from zero**, so the earlier reading is WITHDRAWN. The two other "harmful" cells — the ones
carrying "it generalises across three attack types" — have CIs spanning **±0.2**, six times the effect
they are claimed to demonstrate.

**The split is a power artifact, not a mechanism.** `natural_doublespeak` has **420** prompts;
`direct_harmful` has 72 and `direct_codeword` 36. The only benign cell that is genuinely tight is
`benign_literal` (n=324, CI ±0.017). The design has power to resolve exactly the two large cells, and
they are one benign and one doublespeak. Every 36–72-row cell is uninformative in **both** directions,
so the data cannot distinguish "harm-general" from "doublespeak-specific" at all.

**Consequences.** The established claim is the narrow one: *removing `d_surface` at the codeword
position raises attack success on natural doublespeak prompts* (+0.056, p=0.0077, control inert). The
report's stronger reading — "raises attack success **wherever there is an attack**, and does nothing
where there is not" — is **not supported**, and the sentence calling that "a **stronger** statement" is
exactly backwards: it is a weaker-evidenced one. The comparison table "✅ harmful yes, benign no" vs
Qwen3's "⛔ does not replicate" applies an **asymmetric evidential standard** — Qwen3's cells were
discounted for failing a test the Llama cells were never given, and when given it, three of them fail
it too.

## R-14 — re-judge underway, and the first two arms say the damage is bounded

Re-judging with `--bank` against the fixed banks. The decisive line is **`null_frac=0.0000`**: goals are
non-empty, so StrongReject is finally being given the request. First two arms in:

| arm | old ASR (empty goal) | **re-judged ASR (real goal)** | refusal |
|---|---|---|---|
| baseline | 0.1006 *(withdrawn)* | **0.1061** | 0.877 |
| C (remove refusalness @L18) | 0.3408 *(withdrawn)* | **0.3631** | 0.615 |

**The numbers move by ~0.005–0.02, not by an order of magnitude.** That is consistent with R-14's own
diagnosis — an empty-goal StrongReject score still reads how harmful the *response* is, so it tracked
compliance closely enough to look right. The severity of R-14 for the **final numbers** is therefore
lower than feared; its severity as a **measurement-validity failure** is unchanged, because "the wrong
instrument happened to agree" is not a defence, and nobody could have known it agreed without doing
this re-judge. Arms B, D, Dctrl and the fixed band are still running.

### A second defect, confirmed exactly as predicted

Every re-judged run prints:

```
goal statuses: {'noop_codeword_absent': 173, 'noop_concept_already_present': 6}
GOAL WARNING: 173 row(s) carry a codeword and a concept but the codeword never occurred in the
query ... those rows were judged against the VISIBLE (benign) request. ASR is structurally deflated
```

**That warning is wrong for this bank, and the goals are correct.** ClearHarm rows have no codeword;
the visible request *is* the harmful request, so no substitution is wanted and the goal string is right.
The mislabel comes from `external_bank.py:78` stamping `concept="bomb"`, `codeword="carrot"` onto
external rows — which it does deliberately, because `score_behavior` reads those keys off row 0 to build
the forward-readout option sets, and confirmed still needed (the Qwen3 smoke prints them).

So the correct status is `no_codeword_metadata`, which `make_goal` already has and which its own
docstring calls "CORRECT for plan §14's external harmful banks". The judge must select it by
**identity — `bank_block == "external"`** — not by inferring from a substitution that did nothing.
Queued behind the Phase-1 workflow, which owns `judge_boombness.py`.

**Consequence for reading the artifacts:** the ASR values from these re-judged runs are **valid**; the
`goal_status_counts` field and its warning are **cosmetically wrong** on external banks. Recorded here
so the next reader does not retract a good number on the strength of a bad label.

### Also found: the bank-identity guard cannot run on external banks

Every external judge run prints `BANK IDENTITY UNCHECKABLE: ['no *_meta.json for the bank']`.
`compare_bank_hashes` exists and now has a caller, but `external_bank.py` writes no `*_meta.json`, so
the check that exists specifically to catch "a bank from a different regeneration joined perfectly and
silently" — the stated root cause of retraction R1 — is inert for exactly the banks this session
regenerated. Filed as **E10**. Deliberately **not** fixed mid-flight: adding the meta file while judge
streams are reading the bank would switch `compare_bank_hashes(strict=True)` on underneath them.

## The seventh dead guard — mine, caught before it shipped

`clearharm_decomposition.json` had **no provenance block and no script that produces it**. It was
assembled ad hoc, which is the standing bar failing again in the artifact that carries the sprint's
best new result. Wrote the missing producer, `src/boombness/analyze_external_arms.py`, which is also
the harvest path for the R-14 re-judge and the AdvBench super-additivity test.

Its control-band guard was **itself a dead guard on the first attempt**, and the way it was caught is
worth recording because it is a new variant.

* **v1 fingerprinted the judge SCORES.** Unit tests passed, including a negative case.
* Run against the **actual historical R-12 band** — three draws whose generations are byte-identical —
  it returned `REFUSED: False, between_draw_sd = 0.0032` and three "distinct" fingerprints.
* **Why:** StrongReject (gpt-4o-mini) is **not bitwise deterministic even at temperature 0**, so
  re-judging one identical generation set three times yields three slightly different score vectors.
  A score-level check therefore reports three distinct draws for a band that has exactly one — it can
  never fire on the defect it exists to catch.

**Fixed by fingerprinting the artifact whose variance the band actually measures: the generations**,
resolved by identity through the judge run's own recorded `gens` path. Re-run against the same
historical band it now prints:

```
BAND REFUSED: draws are not distinct -- IDENTICAL GENERATIONS: s20260901=s20260902=s20260903 ...
Note the judge SCORES differ across these draws (StrongReject is not bitwise deterministic),
so a score-level check would have passed this.
```

It also **refuses when the source generations cannot be resolved**, rather than falling back to the
weak check — a silent fallback to a check that cannot fire is the same defect wearing a different hat.
`tests/test_external_arms.py` (9 tests) pins all of it, including
`test_source_gens_fingerprint_catches_what_the_score_fingerprint_MISSES`, which asserts the weak check
fails and the real one holds on the same input.

**The transferable lesson, and it sharpens FM1.** "Test the guard against a case it should fail" is
not sufficient if the *synthetic* failing case is easier than the real one. The unit test used
identical scores; reality supplied identical generations with different scores. **Test the guard
against the historical defect itself, not a reconstruction of it** — the artifact of the original
failure is still on disk and is the only faithful fixture.

## ★★ R-16 — ClearHarm arm B, the load-bearing row, is NOT significant under domain clustering

The R-14 re-judge is complete for ClearHarm. **§7c's structure survives** — every arm moved by ≤0.03
and the ordering is intact — but running the arms through a *committed* analyzer with the clustering
the design requires changes the verdict on the one row that mattered most.

| arm | ASR (old, empty goal) | **ASR (re-judged)** | Δ pooled | **Δ cluster-mean** | **p_cl** | domain-clustered CI |
|---|---|---|---|---|---|---|
| baseline | 0.1006 | **0.1061** | — | — | — | — |
| **B** — remove `d_surface` @L8 | 0.2067 | **0.1899** | +0.0831 | **+0.0843** | **0.2102** | **[−0.067, +0.235]** ⛔ n.s. |
| C — remove refusalness @L18 | 0.3408 | **0.3631** | +0.2402 | +0.3941 | **0.0410** | [+0.024, +0.764] ✓ |
| D — remove both | 0.5419 | **0.5140** | +0.3911 | +0.4603 | **0.0200** | [+0.109, +0.812] ✓ |
| Dctrl — double random | 0.1117 | **0.1061** | −0.0007 | +0.0009 | 0.530 | [−0.003, +0.004] — inert ✓ |

`outputs/boombness/clearharm_decomposition_regoal.json`, produced by
`src/boombness/analyze_external_arms.py` with full provenance — the first time these numbers have been
regenerable at all.

### It is the estimator, and the estimator was inconsistent within one table

| arm | iid SEM | t (iid) | **clustered SEM** | **t (clustered, G=6)** |
|---|---|---|---|---|
| **B** | 0.0241 | **3.45** | 0.0587 | **1.44** |
| C | 0.0337 | 7.13 | 0.1440 | 2.74 |
| D | 0.0362 | 10.80 | 0.1368 | 3.36 |

**The published "+0.1047 ± 0.0238" is the iid SEM** — my re-judged iid SEM is **0.0241**, matching to
three decimals. Under domain clustering arm B's t falls from 3.45 to **1.44**.

**And the same table already used clustered inference where it produced a negative answer.** §7c
reported super-additivity with a "domain-clustered bootstrap CI [−0.1474, +0.1332] — NOT established"
while reporting arm B with an iid interval. Clustered inference for the claim that failed, iid
inference for the claim that passed, in one table. That is the **same asymmetric-standard defect as
R-15**, and it is now the third instance (R-13 was the first).

### What this does to the ClearHarm conclusion

**Withdrawn:** "arm B is the load-bearing row … `d_surface` is causal off-bank … the bank-artifact
explanation is excluded". **That exclusion rested entirely on arm B, and arm B is not established on
ClearHarm.**

**Still standing on ClearHarm:** removing **refusalness** (C) and removing **both** (D) raise attack
success on an external harmful set with no doublespeak wrapper, against a control that is inert to
within ±0.004. Those survive clustering. But neither isolates `d_surface`, so neither answers the
bank-artifact question.

**Not a null result — an underpowered one, exactly as predicted.** `external_bank.py` warned at build
time that **127 of ClearHarm's 179 rows sit in one category**, so G=6 with one dominant cluster. The
point estimate (+0.084) is unchanged from the original; only the honest interval is wide.

**AdvBench is the test, it is judging now, and it was built for precisely this.** 495 prompts,
**16 clusters**, largest 25.7%. If arm B clears zero there under the same clustered estimator, the
bank-artifact explanation is excluded on a properly-powered external set. If it does not, the claim
that `d_surface` is causal off-bank has no support and must be withdrawn outright rather than
suspended. **This is now the single most consequential open number in the sprint.**

## Staged and ready — the G1 / G3 re-runs (E2, E3, E9)

The Phase-1 workflow has landed both C-6 ports and the T3 fix; confirmed by inspection:
`aggressive_patching.py` and `surgical_knockout.py` both call `signals.string_option_readout`, both
default `--readout-ids whole_answer --answer-prefix "Answer:"` with a `--min-option-mass` gate, and
`surgical_knockout` now sets `rank_dst = readout_pos` under `--dst readout`. Argsfiles are staged and
grep-verified; they are **not launched yet** because the workflow is still editing those files and a
run started now would use pre-verification code.

| argsfile | what it settles |
|---|---|
| `args_g1wa_smoke.txt` | house rule: 2 families before the sweep |
| `args_g1wa_sow.txt` | **G1 re-run, `semantic_one_word`** — same prompts as the original, so this isolates the *readout* change alone. Also **α=0.25 added** (E9): the original swept 0.5/1/2/4, and 0.25 is the dose every §12 behavioural claim rests on. |
| `args_g1wa_sfc.txt` | **G1 on `semantic_forced_choice`** — the 288 rows built to fix exactly this problem and **never scored by any run** (C-5). Running both separates "the readout was wrong" from "the prompt framing was wrong". |
| `args_g3wa_smoke.txt` / `args_g3wa_readout.txt` | **G3 re-run with `--dst readout`**, the ranking destination retraction #3 called fatal. Also `--n-families 24`, because the audit showed the runs labelled "6 families" were **3 domains × 2 splits** — `--n-families` counted prompts, not families. |

**Prediction, recorded before the runs so it cannot be adjusted afterwards.** G1's *direction* should
survive on any readout — the query-codeword arm moves the wrong way by −71% of span, far outside what
an instrument artifact plausibly produces. G1's *magnitudes* should move, and the old readout's bias
was **toward the concept** (four single-token variants against the codeword's zero capitalised form),
so the corrected `demos_only|L18` figure should come in **at or below +68%**, not above. G3 is the
genuinely open one: its top-k/bottom-k null was measured at the wrong token, so it could go either way.

## Phase-1 workflow COMPLETE — 14 agents, 0 errors, all 7 verifiers INCOMPLETE

Every verifier returned **INCOMPLETE** and fixed further defects in the patch it was checking. That is
7 of 7, after 3 of 3 in session 1 — the base rate for "a fix is complete as submitted" in this project
is now **0 of 10**. Suite: **584 passed, 6 failed** (the same six pre-existing
`module_imports_without_torch` checks in legacy GCG/reinforce files, untouched). Test count went
**338 → 584**.

**C-6 and T3 are in.** `aggressive_patching.py` and `surgical_knockout.py` both call
`signals.string_option_readout`, both default to `--readout-ids whole_answer --answer-prefix "Answer:"`
with a fatal `--min-option-mass` gate, and `surgical_knockout` sets `rank_dst = readout_pos`.

### Two things the agents found that the brief did not ask for

**A new bug class — the batched readout under a patch.** `signals.string_option_readout` batches its
option variants into a single forward, while `ds_common.LayerPatch._hook` writes `hidden[0,p,:]` and
`pair_common.ComponentOutSwap._hook` writes `h[bi,...]` with `bi=0`. Calling the helper naively under
a patch would have scored the **concept** variants patched and the **codeword** variants *unpatched* —
turning `semantic_logodds` into a patched-vs-unpatched comparison rather than a concept-vs-codeword
one. Pinned to `max_batch=1` and demonstrated behaviourally against the real `LayerPatch`. This would
have silently corrupted the entire G1 re-run.

**T9b — a live second instance of the fake-band defect.** `between_draw_band` already returned
`sd=None` at n=1, so T9 "as stated" was fixed. But a 1-draw cell was still **emitted with
`intervention="add_control_band"`** — a single observation carrying a band's name, which is retraction
#7 and R-12 verbatim — and `summary.json`'s `control_draws_underpowered` was a pure function of the
*requested* `--n-control-draws`, so a run that asked for 12 and achieved 1 reported "not underpowered".

### ★ An open question the verifier could not settle, now settled: the 1464 → 2352 bank join is BENIGN

The `silent_failures` verifier flagged that `extract_boombness/full_20260816_185942_1008673` was fitted
over a **1464-row** bank and is consumed by **72** committed runs, **28** of which are `score_behavior`
runs over the **2352-row** bank — *"the R1 cross-regeneration join shape, detectable from metadata
alone. Whether it is benign is a question I cannot settle without reading prompt text."*

It is settleable without reading prompt text, because the fit records **content-derived** fields.

1. All 1464 fit `prompt_id`s are present in the current bank, **0 missing**. Not sufficient on its own:
   `prompt_families.py:350` computes `prompt_id = sha256(family|condition)`, which is **metadata-derived,
   not content-derived**, so an ID match does not pin the text. (The fit rows carry no `prompt_sha16`.)
2. The bank's git history shows the content **did** change: `ab679b02` (2026-08-16 19:00:02) rewrote
   **1102 of 1464** prompts relative to `50f7133f` (18:46:49). The fit run started at **18:59:42** —
   *twenty seconds before that commit* — so which content it read was genuinely ambiguous.
3. Settled with `seq_len`, which the fit records per row and which is a pure function of the prompt
   text under a fixed tokenizer and template:

| candidate bank content | `seq_len` agrees | disagrees |
|---|---|---|
| `50f7133f` (pre) | 441 | **1023** |
| **`ab679b02` (post)** | **1464** | **0** |

**The fit read the post-regeneration content, which is byte-identical to the corresponding rows in
today's 2352-row bank.** The bank grew by **addition**; the shared 1464 rows never changed. So the
28 cross-bank joins are directions fitted on a **strict, content-identical subset** and applied more
broadly — a legitimate design, not a contamination. **No number is affected, and `comp_projout` (R-6)
and `band2_*` (R-12) are cleared of this particular worry.**

*What remains a real defect* is that this took a tokenizer and a git bisect to establish, because the
fit records `n_bank_rows` and a bank **path** but no bank **content hash** — exactly the gap
`bank_content_sha16` / `compare_bank_hashes` was supposed to close, and exactly why storing two
different functions under one key mattered.

### Correction to my own G3 re-run plan

I had staged G3 at `--dst readout`. The verifier is right that the comparable configuration is
**`--dst both`** — it ranks at `readout_pos` (the T3 fix) while cutting the same destination set the
original cut, so the re-run isolates the ranking change instead of confounding it with a narrower
intervention. Restaged as `args_g3wa_block.txt` and `args_g3wa_codeword.txt`, both at `--dst both`,
because `block` is the scope G3's claim rests on and `codeword` is the scope the original "~7%" came
from. Every G3 number in the sprint changes and **none can be recomputed from committed artifacts** —
all three effects (ranking destination, cross-fitting, readout) require forward passes.

### Also flagged: a second G1 artifact nobody had marked

`outputs/boombness/g1_g3_analysis.json`'s G1 block comes from a **different** aggressive_patching run
(`pilot_20260816_210506_1142800`), also `readout: semantic_logodds`, and is invalidated by C-6 on
identical grounds. It must be marked pending re-derivation alongside `g1_stratified.json`.

## ✅ R-12 CLOSED — the ClearHarm control band is real, and the fake one understated variance 2.7×

Three re-seeded draws, re-judged against a real goal, run through `analyze_external_arms.py` whose
band guard **accepted** them on the primary (generation-level) check:

| draw | seed | source gens sha16 | ASR@0.5 |
|---|---|---|---|
| 1 | 20260901 | `61249763c34b4840` | 0.0950 |
| 2 | 20260902 | `3b962119cfc6c1f9` | 0.0950 |
| 3 | 20260903 | `485698e92ca55ba9` | 0.1173 |

**Band mean 0.1024, between-draw sd 0.0129, sem 0.0074**, against a baseline of **0.1061**. The
control is genuinely inert — the band straddles the baseline.

**The retracted band reported sd 0.0048. The true value is 0.0129 — 2.7× larger.** That is the cost of
R-12 stated precisely: not a wrong ASR, but a **fake precision**. And it is the second time this exact
number was fabricated (retraction #7's fake band reported 0.0049), which is why the guard now lives in
a committed script with a test rather than in a reviewer's attention.

Note draws 1 and 2 return the *same* ASR (0.0950) despite different generations — 17/179 either way.
Under the old score-level fingerprint that coincidence plus judge noise is exactly the pattern that
would have been mistaken for a repeated draw, or missed as one. The generation hash settles it in both
directions.

**This does not rescue arm B.** The band bears on whether the *control* is inert (it is, to ±0.013);
arm B's problem is R-16 — its **domain-clustered** interval [−0.067, +0.235] includes zero at G=6.
A tight control band and an underpowered arm are different facts and the report must not let the first
stand in for the second.

## Plan §9's named outputs finally exist (6 of the 12 missing artifacts)

`correlation_summary.json`, `regression_summary.md` and all **four** §9 plots were required by the plan
and had never been produced. `src/boombness/summarize_section9.py` produces all six from committed
artifacts, in `outputs/boombness/section9/`.

**It computes no statistic** — `analyze_g2` / `analyze_g9` own the inference and this consolidates
their artifacts. The one thing it does compute is the row-level join the plots need, and it **refuses
to write anything** unless that join reproduces `g2_analysis_cwpos.json` first. It does, bit-identically:
**n=234, rho=0.306667780204175**. A plot drawn from a join that disagrees with the inference is a plot
of a different dataset, and this project has already shipped one phantom cell from exactly that.

The four models plan §9 names, now in one table:

| model | R² @ codeword_last | R² @ last token |
|---|---|---|
| `ASR ~ boombness` | 0.1411 | 0.0066 |
| `ASR ~ refusalness` | 0.1759 | 0.0013 |
| `ASR ~ boombness + refusalness` | 0.2502 | 0.0066 |
| `ASR ~ boombness + refusalness + n_examples` | 0.2541 | 0.0496 |

**`ASR ~ boombness + role_style` is reported as REFUSED, not fitted.** The plan permits role-style "as a
temporary proxy, explicitly labelled as a proxy" — but labelling an unidentifiable term does not make it
identifiable, and `role_style` is confounded with `family_id` in the bank as generated. Refusing is the
honest reading of the plan's intent, and it is recorded rather than silently skipped.

**G2 survives the T5/T6 fixes.** The regenerated `g2_analysis_cwpos.json` still gives rho_pooled
**0.3067** and within-domain **0.2618**, and now carries the multiplicity correction the layer selection
never had: **maxT family-wise p = 0.0015**, `holm_rejected_within_domain = True`. The headline was
selected over ~20 layers and it survives being told so.

Per-domain rho ranges **0.020 (lab_safety) to 0.410 (farm_storage)** across the 6 clusters — a wide
spread, which is precisely why the inference is domain-clustered and why `p_iid_pooled_rho` is now
explicitly marked WITHDRAWN as a sole basis inside the artifact.

## The G1/G3 re-runs surfaced two instrument findings before producing a single number

### ★ G1: the whole-answer readout works — and the CEILING does not

`g1wa_smoke` (2 families) shows the C-6 port doing exactly what it promised. Option mass by arm:

| arm | n | median option mass | frac > 1% | gate |
|---|---|---|---|---|
| `none` (baseline) | 4 | 0.0885 | 1.000 | OK |
| `transplant` | 80 | **0.1536** | 0.925 | OK |
| `add` | 208 | 0.0972 | 1.000 | OK |
| `add_control_band` | 16 | 0.1489 | 1.000 | OK |
| **`donor_ceiling`** | 4 | **0.0071** | **0.250** | ⛔ **BELOW GATE** |

Against the old readout's median of **5.6e-06**, the live arms are a genuine forced choice at last.
**But the `donor_ceiling` arm is not**, and it is the one that matters most for G1's headline: every
number G1 reports is `frac_of_span = (arm − baseline) / (ceiling − baseline)`, so **the ceiling is the
denominator of the entire claim.**

Decoding what the model actually wants to say at that position (`top1_id`, now recorded per row —
token ids, decoded through the tokenizer, no prompt text read):

| arm | top-1 tokens |
|---|---|
| `none` (baseline) | ` Bomb` ✓, ` Evidence`, ` Tops`, ` Vegetable` |
| **`donor_ceiling`** | **` Explos`**(ive), **` Squ`**(ash), **` F`** |

**On the donor prompt the model answers with a synonym or a category word, not the option word.**
` Explos…` for *bomb*, ` Squ…`/` Vegetable` for *carrot*. Both are semantically correct and both fall
outside the option set `{' bomb',' Bomb'} / {' carrot',' Carrot'}`, so the ceiling captures **0.4–2%**
of the donor's answer probability.

This is a **different** defect from C-5, which was about capitalisation and multi-token codewords and
which the whole-answer readout fixed. This one is lexical substitution, and no readout built from the
two literal surface forms can see it. Note the ceiling's `semantic_logodds` is *high* (+2.3 to +13.4),
i.e. the model does prefer bomb over carrot there — the **ratio** is meaningful even when both options
sit in a 0.4% slice. So this may not invalidate `frac_of_span`; it does mean the span's upper anchor
is estimated from a tail. **n=4 in the smoke — to be quantified at n=48 in the full run** (766659 /
766660, `semantic_one_word` and `semantic_forced_choice`), which writes its data even when the gate
fires. Recorded now, before the numbers, so the finding cannot be shaped by them.

### G3: `dense_two_layer` is structurally infeasible, and the old code met that by truncating 87%

The G3 smoke died on a guard a Phase-1 verifier added:

```
dense_two_layer INFEASIBLE at layer 8: needs 30720 edges but only 3840 exist there
(1920 demo + 1920 non-demo). Two layers cannot match an all-layer cut's edge count;
widen --layers instead of silently cutting 12% of the target.
```

The code comment records what the pre-2026-08-17 version did instead: **"on the real run it delivered
7,264 of a needed 56,832 (87% short) while still being reported as the layer-matched dense arm."**
`dense_two_layer` exists to break the tie between *depth redundancy* and *edge count* — and it was
8× short, so it broke nothing.

It cannot be fixed by widening `--layers`: feasibility needs `n_chosen ≥ 16`, at which point it is not
a two-layer arm. **The arm is structurally infeasible for its stated purpose.** The tie is instead
broken from the other side by `subsampled_all_layers_demo` (same total edge count, spread over all 32
layers), which *is* feasible.

Added `--skip-arms` / `--skip-arms-reason` to `surgical_knockout.py`: an arm may be dropped
**deliberately**, never silently. The reason is **mandatory**, unknown arm names are refused (by
identity, so a typo cannot skip nothing and report success), skipped arms are charged to the
`FailureLedger` and named in `summary.json`, and the completeness check no longer demands them.
Validation runs **before the model load**, so a bad flag costs nothing and is testable without a GPU —
the first version validated after the load and could not be tested at all. Four tests, 60 passing in
`tests/test_surgical_knockout.py`.

## ★★★ AdvBench, 16 clusters — arm B is REINSTATED and SUPER-ADDITIVITY IS ESTABLISHED

The properly-powered external test. 495 held-out AdvBench prompts, **16 domain clusters, largest
25.7%** — built in the same commit as ClearHarm for exactly this purpose, judged against real goals
(post-R-14), analysed by the committed `analyze_external_arms.py`
(`outputs/boombness/advbench_decomposition.json`).

| arm | intervention | ASR@0.5 | refusal | Δ pooled | Δ cluster-mean | p_cl | domain-clustered CI |
|---|---|---|---|---|---|---|---|
| baseline | — | 0.0646 | 0.9313 | — | — | — | — |
| **B** | remove `d_surface` @L8 | **0.1071** | 0.8889 | +0.0422 | **+0.0305** | **0.0089** | **[+0.0089, +0.0522]** ✓ |
| C | remove refusalness @L18 | 0.2707 | 0.7091 | +0.1967 | +0.1895 | 0.0001 | [+0.1097, +0.2692] ✓ |
| D | remove **both** | 0.3515 | 0.6222 | +0.2722 | +0.2544 | <0.0001 | [+0.1589, +0.3499] ✓ |

### 1. Arm B clears zero — R-16's withdrawal is reversed, on the set that can test it

`d_surface` was fitted **entirely on the carrot/bomb 2×2**. Removing it raises compliance on 495
harmful requests that contain **no codeword, no demonstrations and no doublespeak wrapper**, with a
**domain-clustered** interval that excludes zero: **+0.0305, p_cl = 0.0089, CI [+0.0089, +0.0522]**.

This is the same estimator that found arm B **n.s. on ClearHarm** (p=0.21) three hours ago. The
difference is entirely power, and it was predicted at build time: ClearHarm has **G=6 with 127 of 179
rows in one cluster**; AdvBench has **G=16 with the largest at 25.7%**. The point estimates agree
(+0.084 pooled on ClearHarm, +0.042 pooled here); only the intervals differ.

**So the claim R-16 withdrew — `d_surface` is causal off-bank, and the bank-artifact explanation is
excluded — is reinstated, and now on the better-designed set.** Both facts stay in the record: it is
not established on ClearHarm and it *is* on AdvBench, and the reason is the cluster structure, not
the arm.

### 2. ★ SUPER-ADDITIVITY IS ESTABLISHED — a genuinely new result

**excess = +0.0333, domain-clustered bootstrap CI [+0.0128, +0.0638], 0.025% of 4000 draws ≤ 0.**

Removing `d_surface` and refusalness **together** produces more than the sum of removing each alone.
The two channels **interact**; they are not independent additive contributions.

On ClearHarm this was **+0.0677, CI [−0.218, +0.123] — NOT established**, and the log predicted why
before AdvBench was judged: one dominant cluster. **AdvBench was built to answer this and it answers
it.** This is the first interaction result in the sprint that survives clustered inference.

### ⛔ The gap this exposes, stated before anyone can call the result clean

**There is NO CONTROL ARM on AdvBench.** All four arms use real fitted directions. The ClearHarm
double-random control was inert (+0.0009, CI [−0.003, +0.004]) and the band sd is 0.0129, which is
evidence — but it is evidence *on a different set*. Arm B's effect here is **+0.0305**, and a
norm-matched random projection has never been run on AdvBench, so "removing `d_surface` raises ASR"
is not yet separated from "removing **any** direction at L8 raises ASR" **on this set**.

Until that lands, the honest statement is: *arm B's effect on AdvBench is significantly non-zero and
its ClearHarm counterpart is controlled and inert; the matched AdvBench control is running.*
`ab_Bctrl` (random @L8, seed 20260901) submitted as **766662**; `ab_Cctrl` and `ab_Dctrl` are staged
and go in as slots free. **Super-additivity has the same gap** — it is a contrast among three real
arms with no random-composition reference.

*(Also killed cleanly: `g1wa_sfc` (766660) was refused in 6 seconds — `semantic_forced_choice` names
both the concept and the codeword, so donor and recipient occurrence positions do not correspond and a
position-matched transplant is undefined. The plan to run G1 under both query kinds to separate
"readout change" from "prompt framing change" is therefore **not available**; only `semantic_one_word`
is valid for the transplant design, and the guard said so before spending a GPU-hour.)*

## A new instance of the house argsfile trap — and a guard so it cannot recur

Job **766661 died in five seconds**. The `--skip-arms-reason` I had just added was written into the
argsfile as a quoted sentence:

```
--skip-arms dense_two_layer --skip-arms-reason "dense_two_layer is structurally infeasible below ..."
```

`run_boombness.sh` deliberately word-splits `$BOOMB_ARGS` into flags (`# shellcheck disable=SC2086`).
Quotes in the file are therefore **not grouping** — they are literal argv characters — so the reason
arrived as `["dense_two_layer]` plus a dozen stray positional arguments and argparse rejected the run
**after** the node and GPU were allocated.

This is the same family as the wrapper's two documented traps (`--export` truncating comma lists;
argsfiles on node-local `/tmp`), and my own note two hours earlier said *"build argsfiles with printf
and grep them back"* — I did grep them back, and the grep showed the quotes sitting there looking
correct.

**Guard added to `run_boombness.sh`:** an argsfile containing `"` or `'` is **refused before the
model load**, with a message saying why and printing the offending values. Tested both directions —
a quoted argsfile is REFUSED, the real one is ACCEPTED. Multi-word values must now be joined with
underscores by the caller, which is what the G3 argsfiles do.

*This is the seventh guard this project has added, and the third added after the defect it prevents
had already fired. The pattern worth noting: every one of them was cheap, and every one of them was
only written after something died.*

## Qwen3-14B ClearHarm — 4 of 5 arms generated, judging

`q3ch_base`, `q3ch_B`, `q3ch_C`, `q3ch_Dctrl` are DONE (179/179, gate PASS, zero failures);
`q3ch_D` is still on GPU (766488). All at **`max_new 512`**, matching the Llama ClearHarm runs — which
also settles the audit's length-confound complaint, since the published Llama-vs-Qwen3 non-replication
compared a **512**-token Llama run against a **192**-token Qwen3 run and the sprint's own log records
that halving the budget roughly halves the Llama effect.

Judging launched against the fixed bank. Once `q3ch_D` lands, the cross-model decomposition runs
through the same committed `analyze_external_arms.py` as Llama, so the two models are compared by one
estimator rather than two write-ups.

## AdvBench controls in flight

`ab_Bctrl` (766662), `ab_Dctrl` (766665), `ab_Cctrl` (766666) — norm-matched random projections at the
same layers and seed 20260901. These close the gap flagged in the AdvBench section above: until they
land, arm B's +0.0305 and the established super-additivity are contrasts among real arms with no
random-direction reference **on that set**.

## ★ Plan §4.1's designed variance — resolved, and the data makes the decision

The handoff framed this as a choice: *"Either fix the generator and analyse them, or delete them from
the bank and say so. Generated-confounded-unexamined is the worst of the three states."* Measuring the
bank first turns it into a decision the data makes, and produces a **third, better option**.

### 1. They are already isolated — nothing is contaminated

| `bank_block` | rows | non-default levels |
|---|---|---|
| `core2x2` | 1152 | **none — all default** |
| `role_style` | 720 | none |
| `families` / `extra_conditions` | 144 / 144 | none |
| **`strength`** | **96** | aggressive / medium / strong / weak (24 each) |
| **`consistency`** | **72** | conflicting / irrelevant / mixed (24 each) |
| **`position`** | **24** | far / distributed (12 each) |

The designed variance lives in **three dedicated blocks totalling 192 of 2352 rows**, and `core2x2` —
which every main analysis filters on — contains **only** all-default rows. So they have never
contaminated a single published number. "Unexamined" was accurate; "contaminating" was never a risk.

### 2. They cannot support inference, and now that is measured rather than asserted

**Behavioural** rows — the only ones on which ASR could ever be computed:

| block | behavioural rows | levels | rows per level | rows per domain per level |
|---|---|---|---|---|
| `position` | **12** | 2 | **6** | **1** |
| `consistency` | 36 | 3 | 12 | 2 |
| `strength` | 48 | 4 | 12 | 2 |

**Compare against R-15, established three hours ago on this same design:** a **36-row** condition cell
had a domain-clustered CI of **[−0.068, +0.088]** and a **72-row** cell **[−0.087, +0.198]** — both
declared uninformative, and both *larger* than every comparison available here. The `position` factor
would be **6 rows against 6**, one per domain per level, which cannot produce a between-cluster
variance estimate at all.

### 3. And they are confounded exactly as the handoff described — measured

| factor | level | prompt chars (median) | `n_target_occurrences` (mean) | `n_examples` (mean) |
|---|---|---|---|---|
| **position** | `near` (default) | **413** | 5.97 | 4.80 |
| | `far` / `distributed` | **777** | 5.00 | 4.00 |
| **consistency** | `consistent` (default) | 412 | 5.98 | 4.76 |
| | **`conflicting`** | 591 | **8.00** | 6.00 |
| | `mixed` / `irrelevant` | 586 / 518 | 7.00 / **1.00** | 6.00 |
| **strength** | `none` (default) | 416 | 6.02 | **4.91** |
| | weak / medium / strong / aggressive | 274–390 | 4.00–6.00 | **2.00** |

Every non-default level differs from its default in **prompt length, codeword-occurrence count, and
number of demonstrations simultaneously**. `strength` moves `n_examples` from 4.91 to 2.00 — and
`n_examples` is a *known* ASR predictor (ρ=+0.206, C-9). Any "effect of strength" would be
substantially an effect of demonstration count.

### 4. Resolution — the third option, and it is the honest one

Not "analyse" (the design cannot carry it, and doing so would manufacture exactly the underpowered,
confounded cells R-15 just retracted) and not "delete" (the rows are already isolated, and deleting
them changes the bank hash and breaks the join for ~130 committed runs **for no analytical gain**).

**Documented, measured, and explicitly excluded — with the regeneration named as future work.**
That converts *generated-confounded-unexamined* into *generated-confounded-documented-and-excluded*,
which is a legitimate state: a reader can see the rows exist, why they are not analysed, and what it
would take to make them analysable.

**What it would take** is already **E8** in report §9b: balanced levels at ≥120 behavioural rows each,
with prompt length, `n_target_occurrences` and `n_examples` matched across levels by construction.
That is a generator change plus a fresh extraction plus fresh behavioural runs — a project, not a
tick.

**@Omer — the reversible half is done and committed. If you would rather I delete the 192 rows
outright, say so and I will; it costs a bank regeneration and a re-hash of the join for every
committed run, which is why I did not do it unilaterally.**

## G3 smoke passes — and the whole-answer readout changes the picture by three orders of magnitude

`g3wa_smoke2` (766664) COMPLETED with `dense_two_layer` skipped exactly as designed:
`failures: {'arm_dense_two_layer:skipped_by_request': 2}` — counted in the FailureLedger, named in
`summary.json`, reason recorded. Not absent-and-unexplained.

Option mass per arm on the corrected readout, against the old readout's median of **5.6e-06**:

| arm | median option mass | gate |
|---|---|---|
| `none` (baseline) | **0.5504** | OK |
| `topk_demo` | 0.5743 | OK |
| `bottomk_demo` | 0.5503 | OK |
| `random_demo` / `random_nondemo` / `same_head_random` | 0.549–0.552 | OK |
| `subsampled_all_layers_demo` | 0.5776 | OK |
| `all_demo` | 0.6243 | OK |
| `positive_control` | 0.4989 | OK |
| `no_demo_text` | 0.1242 | OK |
| **`all_layers_demo`** | **0.0165** | ⛔ **BELOW GATE** |

**G3's arms are a genuine forced choice for the first time** — ~55% of the answer probability sits on
the two options, against 0.00056% before.

### ⚠ And `all_layers_demo` is the exception, which is the arm the headline rests on

`all_layers_demo` — cutting every demonstration edge at all 32 layers — drops option mass to **0.0165**,
33× below every other arm. This is the arm the report's G3 table reports as recovering **84%** of the
deletion ceiling.

The reading is not obviously "the instrument failed": cutting *all* demonstration influence plausibly
leaves the model unable to answer with **either** option, in which case low option mass is a **finding
about the intervention** rather than a defect of the readout — which is exactly why the gate treats
intervened arms as non-fatal and reports `reportable` per bucket instead. But it does mean the
recovered-fraction for that arm is computed where the model is not choosing between the two options,
and that has to be said next to the number. **n=2 in the smoke; the full runs (766667 `--demo-scope
block`, 766668 `--demo-scope codeword`, both `--dst both`, 24 families) will settle it at n=24.**

Recorded before the full-run numbers arrive, so the caveat cannot be tuned to them.

## In flight

| job / stream | what |
|---|---|
| 766659 | `g1wa_sow` — G1 re-run, whole-answer readout, **α=0.25 added** (E9) |
| 766665 / 766666 | `ab_Dctrl` / `ab_Cctrl` — the missing AdvBench controls |
| 766667 / 766668 | `g3wa_block` / `g3wa_codeword` — G3 re-run at `--dst both` (E3) |
| `judge_q3ch_s1/s2` | Qwen3 ClearHarm base / B / C / Dctrl |
| `judge_q3ch_D` | Qwen3 ClearHarm arm D (766488 completed) |
| `judge_ab_Bctrl` | the AdvBench control for arm B (766662 completed) |

## ✅ The AdvBench control lands — arm B is `d_surface`-specific, and the headline gap is closed

`ab_Bctrl` — a **norm-matched random projection at the same layer (L8), same seed** — judged against
the fixed bank:

| arm | ASR@0.5 | refusal | Δ pooled | Δ cluster-mean | p_cl | domain-clustered CI |
|---|---|---|---|---|---|---|
| baseline | 0.0646 | 0.9313 | — | — | — | — |
| **B** — remove `d_surface` @L8 | **0.1071** | 0.8889 | +0.0422 | **+0.0305** | **0.0089** | **[+0.0089, +0.0522]** ✓ |
| **Bctrl** — remove a **random** direction @L8 | **0.0626** | 0.9333 | −0.0018 | **−0.0062** | 0.539 | **[−0.0271, +0.0147]** — inert |

**The control is dead flat and slightly negative.** So arm B's effect is specific to `d_surface`, not
to "removing any direction at L8", and it holds on 495 external harmful prompts that contain no
codeword, no demonstrations and no doublespeak wrapper, over 16 domain clusters.

**The caveat written into §0, the gate table and §7c three ticks ago is now discharged for arm B.**
`ab_Cctrl` and `ab_Dctrl` are judging; until they land, super-additivity keeps its own version of the
caveat, since it is a contrast among three real arms.

## ★ Qwen3-14B ClearHarm — the two models use DIFFERENT channels, and that is the finding

Length-matched at `max_new 512` (which also removes the audit's length confound: the published
Llama-vs-Qwen3 non-replication compared 512 against 192 tokens). `d_surface`@L11 + refusalness@L20,
the established Qwen3 depths. `outputs/boombness/clearharm_decomposition_qwen3.json`.

| arm | ASR@0.5 | refusal | Δ pooled | Δ cluster-mean | p_cl |
|---|---|---|---|---|---|
| baseline | 0.1341 | 0.7486 | — | — | — |
| **B** — remove `d_surface` @L11 | **0.2793** | 0.5642 | **+0.1306** | +0.0416 | 0.181 |
| **C** — remove refusalness @L20 | **0.1285** | 0.7207 | **−0.0042** | −0.0120 | 0.287 |
| D — remove both | 0.2793 | 0.5475 | +0.1201 | +0.0557 | 0.081 |
| Dctrl — double random | 0.1285 | 0.7039 | −0.0084 | −0.0100 | 0.358 |

### Three things worth stating

**1. The channel that matters is reversed between models.** On Llama, refusalness is the big mover
(C: +0.240 pooled) and `d_surface` the small one (B: +0.083). On **Qwen3 it is the exact opposite**:
`d_surface` moves ASR from 0.134 to **0.279** (+0.131 pooled, and refusal 0.749 → 0.564), while
removing refusalness does **nothing at all** (−0.004, indistinguishable from the double-random control
at −0.008). **D equals B to four decimals (0.2793 both)** — on Qwen3 the entire joint effect is the
`d_surface` channel and refusalness contributes zero.

**2. ⛔ WITHDRAWN (R-17) — `d_surface` removal raises external-set ASR in BOTH models.** Llama +0.083 pooled, Qwen3 +0.131
pooled. *(This was written on **pooled** estimates and is **retracted** — neither Qwen3 number survives clustering: ClearHarm p=0.181, AdvBench p=0.657. See R-17.)* That was read at the time as a **cross-model replication of the `d_surface` causal effect** — and it is the
opposite of G2, where the *correlational* Boombness↔ASR relationship did not replicate. Worth stating
plainly: the correlation is Llama-specific; the causal intervention is not.

**3. It is n.s. under clustering, for the same reason as before, and the fix is already running.**
Qwen3's ClearHarm arm B is +0.0416 cluster-mean, p_cl=0.181 — **the identical 6-clusters-with-one-at-71%
problem that made Llama's ClearHarm arm B n.s. before AdvBench settled it.** So the obvious experiment
is Qwen3 × AdvBench (16 clusters), and it is launched: `q3ab_base` (766674), `q3ab_B` (766675),
`q3ab_Bctrl` (766676). **If arm B clears zero there, `d_surface`'s causal role replicates across two
models on a properly-powered external set**, which would be the strongest claim in the sprint.

*Prediction recorded before the run:* on the pooled estimate Qwen3's effect is **larger** than Llama's
(+0.131 vs +0.083), so with 16 clusters instead of 6 it should clear zero comfortably. If it does not,
the ClearHarm pooled effect was carried by the one dominant cluster and that must be said.

## G3 re-run: honest under-delivery, and a fix

`g3wa_block` / `g3wa_codeword` (766667/766668) completed — **12 families, not the 24 requested**, and
the run said so rather than pretending:

```
family_accounting = {requested_n_families: 24, n_families_eligible: 12,
                     n_families_selected: 12, effective_G: 12,
                     selection: "round_robin_over_domains_split_balanced"}
```

Only 12 families exist under `--n-examples 4` (6 domains × 2 splits). **This is the T7b fix working**:
the pre-fix code counted prompts rather than families and would have reported "24" for the same data.
Relaunched at `--n-examples 4,8`, which doubles eligibility to 24 families — `g3wa_block24` (766672),
`g3wa_codeword24` (766673). The 12-family runs are kept; they are valid, just half the power.

---

# CURRENT PHASE BOARD — supersedes the board at the top of this file (2026-08-19 02:35)

The board in the header is session 1's and is stale. This is the live one.

| plan § | subject | status | evidence |
|---|---|---|---|
| — | **Phase 1 — fix what is broken** | **DONE** | 14-agent workflow, 7/7 verifiers INCOMPLETE, suite 338 → 584 tests |
| 1.1 | `t_sf` scipy-backed | **DONE — verified** | exactly 1 of 726 artifacts corrupted (C-2) |
| 1.2 | comprehension readout | **DONE — verified** | whole-answer readout, 3,200–5,300× more option mass |
| 1.3 | `analyze_steering` | **DONE — artifact replaced** | intervals were 1.03–1.69× too narrow |
| 1.4 | `surgical_knockout` dst / cross-fit / families | **CODE DONE; re-run in flight** | 766672/766673 at 24 families |
| 1.5 | Tier-2 remainder (T5–T10) | **DONE — all verified** | incl. T8 `validate_direction_payload`, silent-failure group |
| **C-6** | whole-answer readout ported to G1 + G3 | **DONE; re-runs in flight** | 766659 (G1), 766672/3 (G3) |
| §5 | **G1** | **RE-RUN IN FLIGHT** | 766659, `whole_answer`, **α=0.25 added** (E9). ⚠ donor-ceiling instrument problem found |
| §6.4 | metric comparison | **DONE** | report §7b |
| §8 | demo-count dose-response | DONE (report §6) | 5 plots still missing |
| §9 | correlation + regression + 4 plots | **DONE** | `outputs/boombness/section9/`, join verified bit-identical |
| §10 | **G3** | **RE-RUN IN FLIGHT** | `--dst both`, `dense_two_layer` ledgered as skipped |
| §11 | role framing | DONE | report §5 |
| §12 | **G4 / the objective** | **DONE — outcome B stands** | both signs suppress ASR; do not build it |
| §13 | "found the mechanism"? | **NO** | six criteria, not all met |
| **§14** | **external sets** | **★ DONE — the sprint's best result** | AdvBench arm B +0.0305 p=0.0089 w/ inert control; **super-additivity ESTABLISHED**; Qwen3 channel reversal |
| §15 | report items 2/6/7/14/15/16 | **PARTIAL** | 7 ✅, 14 ✅ (§8b), 15 ✅ (§8c), 16 ✅ (§9b); **2 and 6 outstanding** (6 blocked on the G1 re-run) |
| §4.1 | designed variance | **RESOLVED — documented + excluded** | N12; isolated in 3 blocks, underpowered, triple-confounded |
| §2.1 | `seed` + `tokenizer_revision` | **DONE (forward-only)** | recorded by `common.RunDir` from now on |
| Phase 4 | rewrite the deliverable | **SUBSTANTIALLY DONE** | one conclusion, retraction table, §0.3 resolved, G1 → +68%, R-13/14/15/16 applied, sweep clean |

## Retraction / correction ledger — this session

| id | what | status |
|---|---|---|
| R-12 | ClearHarm control band was one draw stated 3× | **CLOSED** — real band sd 0.0129, fake one understated 2.7× |
| R-13 | "matched footing" incremental R² gave refusalness 5 predictors vs 1 | **applied** to report + short update |
| R-14 | **every external ASR judged against an EMPTY GOAL** | **CLOSED** — banks fixed, all arms re-judged, ≤0.03 movement |
| R-15 | "harmful yes, benign no" is 1 significant cell of 6 | **applied**; the split tracks sample size |
| R-16 | ClearHarm arm B significant only under an iid SEM | **applied — and then REVERSED on AdvBench**, which is the right outcome and both halves are recorded |

## Guards added this session (each with a test that fails the pre-fix case)

1. `analyze_external_arms` band guard — fingerprints **generations**, not judge scores *(was dead on first writing; caught by running it against the real R-12 band)*
2. `--skip-arms` / `--skip-arms-reason` — an arm may never vanish unexplained
3. argsfile **quote guard** in `run_boombness.sh` — refuses before the model load
4. `summarize_section9` — **refuses to draw** unless its join reproduces the committed inference

## Open

* `ab_Cctrl` / `ab_Dctrl` judging → discharges the super-additivity control caveat
* **Qwen3 × AdvBench** (766674–676) → does `d_surface` replicate causally at 16 clusters?
* G1 (766659) and G3 (766672/3) re-runs → the last two suspended headline claims
* Report §15 items **2** ("what was implemented") and **6** (aggressive-patching results, blocked on G1)
* §8's five plots

## ★★ G3 IS RE-ESTABLISHED on the corrected readout — and it is cleaner than the version it replaces

The T3 fix (rank at `readout_pos`, `--dst both`), the cross-fitting fix, the real family count
(**24/24 eligible, `effective_G=24`**) and the C-6 whole-answer readout, all at once.
`outputs/boombness/g3_wholeanswer_{block,codeword}24.json`.

### Demo-block scope — the arm G3's claim rests on

| arm | edges cut | Δ readout | sem | fraction of the deletion ceiling |
|---|---|---|---|---|
| `no_demo_text` — demonstrations removed from the prompt | — | **−17.879** | 1.072 | **1.000 (the ceiling)** |
| **`all_layers_demo`** — every demo edge, all 32 layers | **81,707** | **−13.437** | 0.787 | **0.752** |
| `positive_control` | 8,883 | +0.258 | 0.306 | −0.014 |
| `all_demo` — every demo edge, **2 layers** | 5,107 | +0.152 | 0.154 | −0.009 |
| `subsampled_all_layers_demo` — same count, **32 layers** | 5,107 | +0.079 | 0.090 | −0.004 |
| `topk_demo` | 16 | **+0.020** | 0.017 | −0.001 |
| `random_demo` | 16 | +0.001 | 0.003 | −0.000 |
| `bottomk_demo` | 16 | −0.003 | 0.003 | +0.000 |
| `same_head_random` | 16 | +0.003 | 0.023 | −0.000 |
| `random_nondemo` | 16 | −0.044 | 0.037 | +0.002 |

**1. The retrieval is attention-carried.** Cutting every demonstration edge at every layer recovers
**75.2%** of the effect of deleting the demonstrations outright. *(The superseded figure was 84%, on
the invalid readout.)*

**2. The ranking carries no information — and this time it was measured at the right token.**
`topk_demo` **+0.020**, `bottomk_demo` **−0.003**, `random_demo` **+0.001** — indistinguishable, with
sems of 0.017/0.003/0.003. Retraction #3 said the old null could not distinguish *"these edges don't
matter"* from *"they were ranked at the wrong destination"*. Ranked at `readout_pos`, **the null
holds**: no 16-edge subset matters, however chosen.

**3. ★ The edge-count-vs-depth tie is BROKEN — and the answer is edge count, not depth.** This is the
question the `dense_two_layer` arm was built for and could never answer (structurally infeasible, and
the pre-fix code met that by truncating 87%). It is answerable from the **feasible** side:

| edges | spread | Δ |
|---|---|---|
| 5,107 | concentrated at **2 layers** (`all_demo`) | **+0.152** — nothing |
| 5,107 | spread over **32 layers** (`subsampled_all_layers_demo`) | **+0.079** — nothing |
| 81,707 | all demo edges, all layers | **−13.437** |

**6.25% of the demonstration edges does nothing *however distributed*.** Concentrating them or
spreading them over depth makes no difference; only cutting essentially all of them works. The
redundancy is in the **number of edges**, and the response is close to all-or-nothing.

### ★ Codeword scope — the sharper half, and it corroborates G1 from the attention side

Restricting the cut to edges into the **codeword occurrences inside the demo block**:

| arm | edges | Δ readout | sem |
|---|---|---|---|
| **`all_layers_demo`** (codeword scope) | **6,144** | **+1.332** | 0.351 |
| `subsampled_all_layers_demo` | 384 | +0.125 | 0.062 |
| `all_demo` | 384 | −0.110 | 0.079 |
| every 16-edge arm | 16 | −0.037 … +0.013 | — |

**Cutting all attention into the demo-block codeword tokens, at every layer, does not reproduce the
deletion effect at all — it moves the readout the *wrong way* (+1.33).** Cutting attention into the
**whole demonstration block** recovers 75%.

So the information is retrieved from the **demonstration block as a whole, not from the codeword
tokens within it**. That is G1's conclusion — meaning lives in the demonstrations, not in the
codeword — reached independently from the attention side, on an instrument that can now represent
both answers.

### On the script's `dynamic_range_established = False`

`analyze_g1_g3` prints "NO DYNAMIC RANGE ESTABLISHED" because `positive_control` (+0.258) does not
exceed 3× the largest other arm. **That verdict is expected here and the code says so itself**
(`analyze_g1_g3.py:225-231`): the largest arm is `no_demo_text`, which is the deletion **ceiling** the
fractions are taken *of*, not an arm awaiting validation — *"Movability is established, overwhelmingly,
by `no_demo_text` itself."* The guard is doing its job (it refuses to certify vacuously, which is how
its predecessor died); its False is not a verdict on G3. Left as-is and reported rather than tuned.

## Plan §8's five plots now exist — and the comprehension curve is on a valid readout for the first time

`src/boombness/summarize_section8.py` → `outputs/boombness/section8/`. Domain-clustered error bars
throughout. The join is the same one `summarize_section9` validates, and the script refuses to draw
unless it reproduces `g2_analysis_cwpos.json` (it does: n=234, rho bit-identical).

**Comprehension is read from the WHOLE-ANSWER run, not the committed §8 artifact.**
`g8_comprehension_by_nexamples.json` is computed from the pre-R-6 baseline whose comprehension options
held a median **4.4e-05** of next-token mass — any curve through that is a curve through a tail. The
whole-answer run gives **median option mass 0.3155**, so this is the first §8 comprehension curve that
is a forced choice.

| `n_examples` | Boombness (`d_surface|L12|proj`) | ASR | refusal | comprehension log-odds (coded−literal) |
|---|---|---|---|---|
| 0 | −3.402 *(degenerate CI)* | +0.240 | 0.500 *(degenerate)* | **+0.184** *(degenerate)* |
| 1 | −3.670 | +0.115 | 0.000 | **−2.237** |
| 2 | −3.665 | +0.094 | 0.000 | −2.255 |
| 4 | −3.583 | +0.163 | 0.000 | −2.798 |
| 8 | −3.585 | +0.266 | 0.019 | −3.246 |
| 16 | −3.451 | **+0.302** | 0.083 | **−3.754** |

*(`natural_doublespeak` only for the first three columns; all conditions for comprehension.
`comprehension_logodds = logp_coded − logp_literal`, so **negative = the model reads the codeword
literally**.)*

**Three observations, stated without over-reading them:**

1. **Boombness is FLAT in demonstration count** — −3.40 to −3.67 across 0→16 demonstrations, with
   overlapping intervals throughout. There is no dose-response in the representation. This is a
   negative result and it sits oddly beside ASR, which is not flat.
2. **ASR is U-shaped**: 0.240 at zero demonstrations, a minimum of 0.094 at two, then rising
   monotonically to 0.302 at sixteen. The zero-demonstration cell also carries **refusal 0.50** against
   ~0 everywhere else, so it is a different regime (an unexplained codeword) rather than the low end of
   one curve — the U is probably two effects, not one.
3. **Comprehension moves monotonically toward the LITERAL reading as demonstrations increase**
   (−2.24 at n=1 → −3.75 at n=16), which is the opposite of the naive expectation that more
   demonstrations teach the coded mapping more strongly. Worth flagging rather than explaining: it is
   consistent with the demonstrations establishing an in-context *literal* usage of the surface word,
   but this sprint has not tested that and should not assert it.

⚠ **Four cells have `degenerate=True`** (between-cluster SD exactly 0) and are drawn without error
bars. Those are not tight estimates — they are cells where every domain saw the same value.

**The `strength` panel is drawn with its disclaimer inside the figure.** Plan §8 names it, but N12
shows `strength` cannot support inference (12 behavioural rows per level; it moves prompt length,
codeword-occurrence count and `n_examples` 4.91→2.00 at once). Drawing it silently would put a
confounded underpowered comparison in a report figure; it is drawn, labelled **"NOT AN INFERENCE"**,
and annotated with the reason.

**A bug I caught in my own guard while doing this.** The first version filtered comprehension rows on
`semantic_logodds` — the wrong key; the comprehension rows carry `comprehension_logodds`. The filter
returned **zero rows**, and the option-mass gate then reported *"median 0.0000 → REFUSED"*, which reads
exactly like an instrument verdict. **A guard that fires because the data was not found is
indistinguishable from one that fires because the data is bad.** Emptiness is now checked and named
separately, and it raises rather than reporting a fake measurement.

## ✅ All three AdvBench controls are inert — and super-additivity survives the RIGHT test, narrowly

| arm | ASR@0.5 | Δ cluster-mean | p_cl | domain-clustered CI |
|---|---|---|---|---|
| baseline | 0.0646 | — | — | — |
| **B** `d_surface`@L8 | 0.1071 | **+0.0305** | **0.0089** | [+0.0089, +0.0522] ✓ |
| **C** refusalness@L18 | 0.2707 | **+0.1895** | 0.0001 | [+0.1097, +0.2692] ✓ |
| **D** both | 0.3515 | **+0.2544** | <0.0001 | [+0.1589, +0.3499] ✓ |
| Bctrl random@L8 | 0.0626 | −0.0062 | 0.539 | [−0.0271, +0.0147] — inert |
| Cctrl random@L18 | 0.0606 | −0.0021 | 0.292 | [−0.0063, +0.0020] — inert |
| Dctrl double random | 0.0667 | +0.0031 | 0.330 | [−0.0034, +0.0096] — inert |

**Every control is flat.** The three real arms move ASR by +0.031 / +0.190 / +0.254; their matched
random projections move it by −0.006 / −0.002 / +0.003. The caveat carried in §0, the gate table and
§7c since this result first landed is now **fully discharged**.

### ★ I nearly committed the difference-of-significance fallacy, and the correct test is tighter

The obvious move was: *real* super-additivity is **+0.0333, CI [+0.0128, +0.0638]** (established);
run the same statistic on the **control triple** and it is **+0.0066, CI [−0.0013, +0.0170]** (not
established); conclude the interaction is real.

**That reasoning is wrong, and the numbers show why: the two intervals OVERLAP** in
[+0.0128, +0.0170]. "One CI excludes zero and the other does not" is not a test of whether they
differ — it is the classic difference-of-significance error, and this project has already retracted
three claims (R-13, R-15, R-16) that came from comparing two arms measured on different footings.

The quantity that answers the question is the **difference of the two excesses**, bootstrapped **once**
over the same resampled domains so the two are paired and their correlation is respected. Implemented
as `--super-additive-control` in `analyze_external_arms.py`:

**real − control super-additivity = +0.0268, domain-clustered CI [+0.0029, +0.0584], 1.5% of 4000
draws ≤ 0 → ESTABLISHED against control.**

**It survives — but state the margin honestly.** The lower bound is **+0.0029**, about 11% of the
point estimate; this is a real interaction, not a comfortable one. The naive comparison would have
made it look far safer than it is.

**So the claim, at full strength and no further:** on 495 external harmful prompts over 16 domain
clusters, removing `d_surface` and the refusal direction **together** produces more than the sum of
removing each alone, by +0.027 [+0.003, +0.058] beyond what a matched random-projection triple
produces. The two channels interact.

## Plan §15 item 2 written — the only §15 item left is item 6, which is blocked on G1

Report **§1b, "What was actually implemented"**: 36 modules, 32 test files, **584 passing tests**, 244
committed run directories, mapped by role (generation/audit → representation → intervention → scoring
→ analysis → infrastructure), so any number in the report can be traced to the module that produced it.

It ends with **what the plan asked for and did not get**, stated rather than glossed:

* **§4.1's designed variance** — generated, isolated in three `bank_block`s, unable to support
  inference (N12).
* **`prompt_level_correlation.py` / `example_count_sweep.py` as named scripts** — the *work* exists as
  `summarize_section9.py` / `summarize_section8.py`, which read committed artifacts instead of
  re-running the sweeps. Same required outputs, different provenance path. Worth recording because a
  reader looking for the plan's filenames will not find them.
* **A second concept pair** — every claim in this report is carrot↔bomb (**E6**).

### §15 status
| item | subject | status |
|---|---|---|
| 2 | what was implemented | ✅ §1b |
| 6 | aggressive-patching results | ⏳ **blocked on the G1 re-run** (766659, ~1h50m in) |
| 7 | Boombness metric comparison | ✅ §7b |
| 14 | negative results | ✅ §8b (now N1–N12) |
| 15 | failure modes | ✅ §8c (FM1–FM8) |
| 16 | recommended next experiments | ✅ §9b (E1–E10) |

## Phase 4: the two ★ sections moved into the body, and §18 is SETTLED

### The sections
`## ★ THE HEADLINE RESULT` and `## ★ SECOND CAUSAL RESULT` sat **after** the reproduction commands,
which is how they survived contradicting §0 for so long. Moved into the body as **§7d** and **§7e**,
beside §7c where the causal results belong.

**§7d's opening sentence was the contradiction itself:** *"This supersedes the §18 = B label and
reopens §12."* It is now **withdrawn in place**, with a banner saying why: the §12 verdict is unchanged
and negative, §9b lists building the objective under *explicitly NOT recommended*, and arm F's
mechanism was retracted (R-8) because its gain is largest in `benign_remap` — where the mapping is
**never taught**. Its inner "§12.2 is REOPENED and worth building" bullets are withdrawn too, and §19
Q10 now answers **no** with both prior corrections shown rather than reading as a live reopening.

Dangling cross-references fixed (report ×3, short update ×2), including **N6**, whose *"a matched-length
Qwen3 arm is running"* was stale — that arm landed and changed the picture (§7c).

### ★ §18 settled — C, amended

Both blockers landed (**R-6 resolved**, **R-7 discharged**), so the label is decided instead of deferred
for a third time.

| option | verdict | why |
|---|---|---|
| A. Strong positive | **No** | *adding* Boombness suppresses ASR at both signs; no objective built or recommended |
| **B. Mechanistic but not causal** | **No** | B requires interventions *"do not affect ASR **or** destroy comprehension"* — **both clauses fail**: removing `d_surface` raises external ASR (+0.0305, p_cl=0.0089, inert control), and comprehension *improves* (R-6) |
| **C. Refusal-only story** | **Closest** | on Llama refusal dominates: +0.190 vs `d_surface`'s +0.031 |
| D. Negative | **No** | G2 survives multiplicity correction and the `n_examples` control; G1 and G3 established |

**The amendment is the sprint's actual result**, and the plan's taxonomy has no box for it:
(1) `d_surface` is a **distinct** causal channel, near-orthogonal to refusal (cos=0.019) and effective
alone off-bank against an inert control; (2) the two channels **interact** — +0.0268 [+0.0029, +0.0584]
beyond a matched random triple, which a pure refusal account cannot produce; (3) **on Qwen3 the refusal
channel does nothing and `d_surface` does everything**, the inverse of Llama.

**Verdict: C on Llama-3.1-8B, with a real and interacting `d_surface` channel that the C label
understates, and an inverted picture on Qwen3-14B.** Stated once, in §0, and nowhere else.

*Flagged as a judgement call:* the numbers are regenerable; disagreeing with the label is not
disagreeing with any number. @Omer — this is the one place I picked a verdict rather than computed one.

## ⛔ R-17 — my recorded prediction was WRONG: Qwen3 does NOT replicate on AdvBench, and the cross-model causal claim is withdrawn

Two ticks ago I wrote, deliberately before the run so it could not be adjusted afterwards:

> *"On the pooled estimate Qwen3's effect is **larger** than Llama's (+0.131 vs +0.083), so with 16
> clusters instead of 6 it should clear zero comfortably. If it does not, the ClearHarm pooled effect
> was carried by the one dominant cluster and that must be said."*

**It did not clear zero. It is not close.**

| Qwen3-14B, AdvBench 495, 16 clusters | ASR@0.5 | refusal | Δ cluster-mean | p_cl | CI |
|---|---|---|---|---|---|
| baseline | **0.0081** | 0.9374 | — | — | — |
| **B** — remove `d_surface` @L11 | **0.0141** | 0.9212 | **+0.0024** | **0.657** | [−0.0089, +0.0138] |
| C — remove refusalness @L20 | 0.0061 | 0.9111 | −0.0010 | 0.333 | [−0.0032, +0.0012] |
| Bctrl — random @L11 | 0.0081 | 0.9293 | **+0.0000** | — | — |

Arm B moves **4/495 → 7/495**. Three prompts.

### The reason is a floor, not the cluster structure — so my stated fallback was wrong too

| | baseline ASR | refusal | headroom (1−refusal) |
|---|---|---|---|
| Llama ClearHarm | 0.1061 | 0.8771 | 0.1229 |
| Llama AdvBench | 0.0646 | 0.9313 | 0.0687 |
| Qwen3 ClearHarm | 0.1341 | 0.7486 | 0.2514 |
| **Qwen3 AdvBench** | **0.0081** | 0.9374 | 0.0626 |

**Qwen3 complies with 0.8% of AdvBench against 13.4% of ClearHarm — a 16× drop**, where Llama drops
only 1.6× between the same two sets. And it is **not simply more refusal**: Qwen3's AdvBench headroom
(0.0626) is close to Llama's (0.0687), but Llama converts nearly all of its non-refusal into judged
compliance while Qwen3 converts about an eighth of it. Qwen3 on AdvBench mostly produces answers that
neither refuse nor comply usefully. **There is almost nothing to move, and an intervention cannot be
measured against a floor.**

So the fallback I committed to — *"if it does not clear zero, the ClearHarm pooled effect was carried
by the one dominant cluster"* — is **also not supported**. The AdvBench null does not diagnose the
ClearHarm result; the two sets are not measuring the same thing on this model.

### What is withdrawn, and what survives

⛔ **Withdrawn:** *"`d_surface` removal raises external-set ASR in BOTH models … a cross-model
replication of the causal effect."* Written two ticks ago on **pooled** estimates. Neither Qwen3 number
survives clustered inference — ClearHarm p=0.181, AdvBench p=0.657 — and a pooled estimate is not the
estimand this project reports.

✅ **Survives, and it is the one solid off-bank result:** **Llama-3.1-8B on AdvBench, arm B,
+0.0305, p_cl=0.0089, CI [+0.0089, +0.0522], against an inert matched control.** Plus C, D and the
super-additivity interaction on the same set.

⚠ **Open, not negative:** whether `d_surface` is causal on Qwen3. The ClearHarm point estimate is
*large* (+0.131 pooled, ASR 0.134 → 0.279, refusal 0.749 → 0.564) and merely under-powered at G=6;
AdvBench is a floor. **Neither set can answer it.** What would: an external harmful set on which Qwen3
has real baseline compliance — i.e. chosen for *this* model rather than inherited from the Llama
pipeline. Added as **E11**.

### The methodological point, which is worth more than the result

**Two "external harmful sets" are not interchangeable, and the choice can decide whether any effect is
measurable at all.** ClearHarm and AdvBench give Llama similar baselines (0.106 / 0.065) and Qwen3
wildly different ones (0.134 / 0.008). A cross-model comparison run on one set alone would have
produced a confident and wrong answer in either direction — "replicates" from ClearHarm, "does not
replicate" from AdvBench. **Report the baseline compliance rate beside every external-set ASR**, or the
reader cannot tell an intervention that fails from a set with no headroom.

## A control gap found while looking for E11: neither ClearHarm arm B has a matched control

**E11 is not buildable from this repo.** The only other external harmful manifest is
`external_maliciousinstruct.csv` — 100 rows in **one** category, so no clustered inference is possible.
Every other manifest is either a ClearHarm slice or `heldout_495` itself. E11 needs a set that is not
here; it stays as future work rather than something this session can close.

**But looking for it surfaced a real gap.** On **AdvBench**, arm B has a matched **single**-random
control at the same layer (`Bctrl`, inert). On **ClearHarm** — for *both* models — the only control is
`Dctrl`, a **double**-random composition matched to arm D, not to arm B:

| set / model | arm B control |
|---|---|
| Llama AdvBench | ✅ `ab_Bctrl` random@L8 — inert (−0.0062) |
| **Llama ClearHarm** | ⛔ **none** — only the double-random `Dctrl` |
| **Qwen3 ClearHarm** | ⛔ **none** — only the double-random `Dctrl` |

Qwen3's ClearHarm arm B is the large-but-underpowered result (ASR 0.134 → 0.279) that R-17 leaves
**open**, and it has been compared only against a control for a *different* intervention. That is the
mismatched-footing shape this project has retracted three times (R-13, R-15, R-16), and it should not
survive into the report unnoticed.

Launched: `ch_Bctrl` (766765, Llama random@L8) and a **3-draw band** for Qwen3,
`q3ch_Bctrl_2026090{1,2,3}` (766766–768, random@L11) — a band rather than one draw, per plan §2.5 and
per R-12, which is what made a single control draw a retraction in the first place.

## ★★ G1 RE-ESTABLISHED on the corrected readout — and the numbers barely moved

`g1wa_sow` (766659) ran 3h03m, wrote **31,104 rows with zero failures**, and exited 4 on the tail gate
— *"the run is written and its healthy readouts are usable"*. Analysed:
`outputs/boombness/g1_wholeanswer_sow.json`.

**harm_ctx — the headline pair.** baseline +4.052, ceiling +12.269, **span +8.217 ± 1.144**,
self-swap |Δ| = 6.5e-02 (the no-op invariant holds).

| arm | **whole-answer (corrected)** | old single-token readout |
|---|---|---|
| **`transplant demos_only L18`** | **+0.689, CI [+0.51, +0.97]** | +0.681, CI [+0.50, +0.95] |
| `transplant demos_only L12` | +0.488 [+0.18, +0.88] | +0.580 [+0.30, +1.00] |
| `transplant first_demo L18` | +0.316 [+0.19, +0.48] | +0.287 [+0.13, +0.49] |
| `transplant last_demo L18` | +0.095 [+0.04, +0.18] | +0.070 [+0.02, +0.13] |
| `transplant all L18` (whole prompt) | **+0.133 [−0.17, +0.34] — null** | +0.141 [−0.09, +0.32] — null |
| **`transplant query_only L18`** | **−0.570 [−1.03, −0.40] — wrong way** | −0.706 [−1.05, −0.56] |

**Every arm reproduces, most of them to within a few points of span.**

### The prediction I recorded before the run, scored

> *"G1's direction should survive on any readout … G1's magnitudes should move, and the old readout's
> bias was toward the concept, so the corrected `demos_only|L18` should come in at or below +68%."*

**Direction: right.** `demos_only` positive, `query_only` negative, `all` null — unchanged.
**Magnitude: the prediction was not wrong so much as unnecessary.** It came in at **+68.9%** against
+68.1% — the numbers did not move at all. So **C-6, which looked like it might invalidate G1, does not
change G1**. The defect was real (the instrument structurally could not represent the codeword's
preferred spelling); the *log-odds ordering* turned out to be robust to it.

That is worth stating precisely: **the readout fix was necessary to know whether G1 held, and the
answer is that it does.** "The old number was fine" is only knowable *after* re-deriving it — which is
the entire argument for having done the work.

### E9 closed — α = 0.25 is now swept

The dose every §12 behavioural claim rests on was never in the §5.2 sweep (0.5/1/2/4 only). It is now:

| arm | harm_ctx | benign_ctx |
|---|---|---|
| `add all all d_surface a=0.25` | **+1.034 [+0.88, +1.14]** | **+1.450 [+1.34, +1.61]** |
| `add query_only all d_surface a=0.25` | −0.717 [−2.00, −0.23] | +0.908 [+0.78, +1.09] |

Adding `d_surface` across the **whole prompt** at α=0.25 reaches or **overshoots** the donor ceiling
(103% / 145%), while adding it to the **query only** moves harm_ctx the **wrong way** (−0.72). Same
asymmetry as the transplant arms, from the additive side.

### ⚠ The ceiling caveat stands, and the agreement does NOT discharge it

`donor_ceiling` option mass at n=48 is **0.007414**, with only **39.6%** of rows above 1% — confirming
at full scale what the n=4 smoke showed. The model answers the donor prompt with ` Explos`(ive) and
` Squ`(ash)/` Vegetable`: semantically right, lexically outside the option set. **The span denominator
is estimated where the model wants to say a different word.**

The old and new readouts agreeing does **not** clear this — *both* normalise by the same span
construction, and the old one had the same problem worse. What the agreement shows is that the two
instruments rank the arms the same way, not that the denominator is well estimated. **The direction
and ordering of G1 are safe; the absolute "% of span" figures inherit a ceiling measured in a tail**,
and that belongs beside the number. Fixing it needs an option set that admits synonyms, which changes
what is being measured — filed as future work rather than patched silently.

## ✅ Plan §15 is COMPLETE — item 6 was the last one

Report **§6b, "Aggressive patching — the full arm table"**: both context pairs, transplant and additive
arms, domain-clustered intervals, from `g1wa_sow`'s 31,104 rows.

**Three things the full table says that the headline number does not:**
1. The demonstration **block** carries the meaning and the codeword does not — `query_only` moves the
   readout **backwards** on the harm pair. The §7c attention result says the same thing independently.
2. The transplant is **not additive over demonstrations**: `first_demo` ~32%, `last_demo` ~10%, block
   ~69%. The first demonstration is worth three times the last and the parts do not sum.
3. **The two context pairs are different experiments.** On `benign_ctx` the whole-prompt transplant
   works (+76.9%) and query-only is nearly inert (−8.2%); on `harm_ctx` whole-prompt is **null** and
   query-only is strongly negative. The harm pair is the harder one, which is why it carries the
   headline.

### ⚠ A caveat that only the full table makes visible

`add query_only d_surface α=0.25` moves harm_ctx **−71.7%** — which looks like a mirror of the
transplant result. **It is not direction-specific:** the `random` (−146.5%) and `orthogonal` (−135.0%)
controls on that same arm move *further* in the same direction. Whatever happens when the query
position is perturbed additively is a property of the perturbation, not of `d_surface`.

**Only the *transplant* query-only arm has controls that stay near zero, so that is the one the report
cites.** Reporting the additive query-only number without its controls beside it would have been a new
instance of the sprint's most common error — and it is exactly the sort of thing that is invisible in a
headline and obvious in a full arm table, which is why plan §15 asked for one.

### §15 final status
| item | subject | status |
|---|---|---|
| 2 | what was implemented | ✅ §1b |
| **6** | **aggressive-patching results** | ✅ **§6b** |
| 7 | metric comparison | ✅ §7b |
| 14 | negative results | ✅ §8b (N1–N14) |
| 15 | failure modes | ✅ §8c (FM1–FM8) |
| 16 | next experiments | ✅ §9b (E1–E11) |

## ⛔⛔ R-18 — G2's correlation is carried by rows that should not be in it, and my own N12 claim was wrong

Found while checking whether **E4** (powering the cross-condition profile by adding demonstration
`slots`) is sound. It is not — sibling slots take overlapping pool slices — and checking that led here.

### `analyze_g2` filters on `condition`, **not** on `bank_block`

`analyze_g2.py:477` keeps rows where `condition == args.arm`. There is **no `bank_block` filter**. So
G2's headline n=234 is not 234 core-design prompts. It is:

| `bank_block` | rows in G2's n=234 |
|---|---|
| `core2x2` | **60** |
| `families` (sibling slots 1 and 2) | **72** |
| `role_style` | 30 |
| **`strength`** | **24** |
| **`consistency`** | **36** |
| **`position`** | **12** |

**Two distinct problems, both material.**

1. **72 rows are sibling families sharing demonstrations.** `family_slot` takes a contiguous pool slice
   stepping by 3 from a pool of 20, so slot-1 and slot-2 families reuse demonstrations from their
   slot-0 siblings (at `n_examples=8`, **5 of 8** are shared). That is pseudo-replication — the R1
   defect class — inside the headline n.
2. **72 rows come from the three designed-variance blocks** whose levels are confounded (N12). Worse,
   those blocks exist to **experimentally manipulate** how readable the codeword is — and a
   manipulation that moves both Boombness and ASR **manufactures** correlation in an otherwise
   observational statistic.

### ⛔ My N12 claim is FALSE and is corrected

I wrote two ticks ago: *"`core2x2` — which every main analysis filters on — contains only all-default
rows. So they have never contaminated a single published number."* **They are 31% of G2's headline n.**
I checked the filter in `surgical_knockout` (which does filter `bank_block == "core2x2"`) and
generalised it to "every main analysis" without checking `analyze_g2`. That is exactly the
address-by-assumption error this project keeps retracting.

### What it does to G2

| subset | n | ρ pooled | per-domain mean ± se |
|---|---|---|---|
| **ALL 234 — as published, now WITHDRAWN** | 234 | **+0.3067** | +0.2334 ± 0.0652 |
| slot-0 only (no sibling families) | 162 | +0.2761 | +0.2385 ± 0.0803 |
| no designed-variance blocks | 162 | +0.2396 | +0.1271 ± 0.0701 |
| **slot-0 AND no designed-variance** | **90** | **+0.0860** | **+0.0252 ± 0.1255** |
| *(the 144 rows dropped)* | 144 | **+0.4027** | — |

**It is not a small-n artifact.** Against 2,000 random 90-row subsets of the published set — median
ρ +0.3078, 95% range [+0.144, +0.464] — the clean subset's **+0.0860 sits at the 0.4th percentile**.
The rows removed carry ρ **+0.403**; the rows kept carry **+0.086**.

### What I claim, and what I do not

**Claimed:** G2's published ρ = +0.307 is computed over a **heterogeneous** row set, and on the 90 rows
that are neither sibling families nor experimentally-manipulated designed variance, the correlation is
**+0.086 with a per-domain mean of +0.025 ± 0.126** — indistinguishable from zero.

**NOT claimed:** that G2 is false. The clean subset is n=90 over G=5 domains and is underpowered; a real
but smaller effect would look like this too. The honest statement is that **G2 is not established on
the clean subset, and the published figure is inflated by rows that do not belong in an observational
correlation.**

### Scope — this is not confined to G2

`analyze_g9` uses the same arm filter, so the **incremental-R² table (R-13)**, the **§9 outputs I
generated this session**, and G2's **mediation** section all inherit the same row set. The §9 join I
"validated" reproduces `g2_analysis_cwpos.json` bit-identically — which now reads as *both* being built
on the same unfiltered set, not as either being right. **Validation against a committed artifact
proves agreement, not correctness**, and I should have said so when I wrote it.

**Gate status:** G2 moves to **UNDER REVIEW**. The re-analysis that settles it is CPU-only — add a
`bank_block` / `family_slot` filter to `analyze_g2` and `analyze_g9`, re-run, and report both the
clean and the full estimate. **Not done in this tick because it changes a headline and should not be
rushed at the end of one.**

## ⛔⛔⛔ R-18 RESOLVED — G2 is RETRACTED

`analyze_g2` now records the **row composition of the analysed set** in every artifact and warns when
sibling-slot or designed-variance rows are included. Two runs, same inputs, same code:

| | n | composition | ρ pooled | **ρ within-domain** | **p_perm (the cited estimand)** |
|---|---|---|---|---|---|
| **as published — WITHDRAWN** | 234 | core2x2 60, strength 24, consistency 36, position 12, role_style 30, families 72 · slots {0:162, 1:36, 2:36} | +0.3067 | **+0.2618** | **5.00e-04** |
| **clean** | **90** | **core2x2 60, role_style 30 · slots {0:90}** | **+0.0860** | **−0.0518** | **0.658** |

**The within-domain correlation — the estimand this project's own artifact says to cite, "PAIRED WITH
rho_within_domain, NOT WITH rho_pooled" — goes from a **retracted** +0.2618 (p=5e-4) to −0.0518 (p=0.658).** It does
not shrink; it crosses zero and becomes a null.

### G2 as published is withdrawn

> ⛔ *"Boombness predicts attack success on Llama-3.1-8B: ρ=+0.307 pooled / +0.262 within-domain at
> L12, n=234, 6/6 domains positive, p<5e-4."*

That figure is computed over a row set in which **31% are sibling families that share demonstrations
with their slot-0 siblings** (pseudo-replication — the R1 defect class) and **31% are rows whose
codeword readability was *experimentally manipulated*** by the `strength` / `consistency` / `position`
blocks. A manipulation that moves Boombness and ASR together manufactures exactly the correlation the
statistic is supposed to discover observationally.

**What is left:** on the 90 independent, unmanipulated prompts, **there is no detectable relationship
between Boombness and attack success.** n=90 over 6 domains cannot exclude a small effect, so the
honest verdict is **"not established"**, not "proven absent" — but it is no longer a positive finding
and must stop being reported as one.

### What else this touches

* **G2's multiplicity defence** (maxT family-wise p=0.0015) was computed on the same 234 rows and
  inherits the problem — surviving a layer-selection correction does not repair the row set.
* **C-9** (`n_examples` is not a confound; partial ρ retains 99.9%) was computed on the same set. The
  finding may still hold *within* it, but it was defending a correlation that is not there on the
  clean rows.
* **R-13's incremental-R² table** and the **§9 outputs** use the same arm filter via `analyze_g9`.
* **§18's label** was argued partly from "the metrics are not non-predictive, G2 survives multiplicity
  correction" as the reason to reject outcome **D**. That reason is now gone. The label was settled as
  **C-amended** on §7c's *causal* evidence, which is unaffected — but the D-rejection needs rewriting
  on those grounds instead.

### The lesson, which is FM4 in a new place

Every previous instance of this project's dominant failure was *"the best of mine against a fixed
instance of yours"* — mismatched **footing** between two arms. This is the same error one level down:
**the row set itself was heterogeneous, and nobody looked.** The filter was `condition == arm`, which
reads as sufficient and is not, and the artifact recorded `n_analysed: 234` without recording what the
234 were. **A count is not a description of a sample.** Every analysis artifact in this project should
record the composition of its rows, not just their number — `analyze_g2` now does.

## R-18 blast radius, bounded — and R-13's ordering does not survive either

### ✅ G1, G3 and the probes are CLEAN

`aggressive_patching.py:1170`, `surgical_knockout.py:664` and `probes.py:275,288` all filter
**`bank_block == "core2x2"`**, and the `core2x2` block is defined with `slots=[0]`. So **G1, G3 and every
probe result are computed on independent, unmanipulated prompts.** R-18 does not touch them, and the
two headline re-derivations of this session (G1 +68.9%, G3 75.2%) stand.

That is the whole blast radius: **the defect is confined to the two scripts that filter on
`condition` alone — `analyze_g2` and `analyze_g9`.**

### `analyze_g9` had the identical defect, now fixed the same way

`analyze_g9.py:522` — `condition == args.arm`, no `bank_block`. Ported the same row-provenance
recording, the same `--require-bank-block` / `--slot0-only` filters, and the same warning.

### ⛔ R-13's conclusion changes on the clean rows

Incremental R² at matched df, `codeword_last`:

| row set | n | Boombness adds over refusalness | refusalness adds over Boombness | ordering |
|---|---|---|---|---|
| **as published** | 234 | +0.0743 | **+0.1091** | refusalness ahead by 1.47× |
| **clean** | **90** | **+0.0441** | **+0.0378** | **near-equal, Boombness marginally ahead** |

**R-13 corrected the *degrees of freedom* of this table (5-vs-1 → 1-vs-1) and got the right answer for
that question. It did not correct the *rows*, and on the clean rows the ordering it established —
"refusalness adds more at the codeword token" — does not hold.** The two increments are within 0.007 of
each other.

⚠ **Do not now claim "Boombness adds more".** Both increments are ~0.04 on n=90 with G=6; neither is
well estimated, and the honest statement is that **at matched df on clean rows neither predictor
dominates**. The published 1.47× advantage was an artifact of the row set, the same way G2's ρ was.

Consistent with G2's retraction, the clean fit also gives boombness β = +0.0557 pooled / **+0.0200
within-domain, permutation p = 0.807** — a null, as expected once the manufactured correlation is
removed.

### §9 Q5 (C-9) on clean rows

`n_examples` control: β +0.0557 → +0.0537, **retains 0.96**. The *robustness* to `n_examples` survives
— but it is now robustness of a null, which is not a finding. C-9 stands as a method result and is
withdrawn as evidence for G2.

### Artifacts
`g2_analysis_cwpos_CLEAN.json` · `g9_three_predictor_cwpos_CLEAN.json`, both beside their unfiltered
counterparts, both carrying `row_composition`. **Every future run of either script records what its
rows are, and warns when the mix is unsafe.**

## ★ The experiment that can actually settle G2 — launched

G2 is retracted, but on **n=90 over 6 domains**, which cannot exclude a small effect. "Not established"
is the honest verdict and it is also an unsatisfying one. The clean sample is small **for a fixable
reason**: `core2x2` uses `slots=[0]`, one family per design cell.

### Why the existing sibling families could not be used, and why slot 3 can

`prompt_families._take` returns `pool[(slot*3 + i) % 20]`, so slot *k* is disjoint from slot 0 exactly
when `3k >= n` and `3k + n <= 20`:

| n_examples | slot 1 | slot 2 | **slot 3** | slot 5 |
|---|---|---|---|---|
| 1, 2 | disjoint | disjoint | **disjoint** | disjoint |
| 4 | **overlaps** | disjoint | **disjoint** | disjoint |
| 8 | **overlaps** | **overlaps** | **disjoint** | overlaps |
| 16 | impossible on a 20-sentence pool | | | |

**That table is exactly why the `families` block (slots 1 and 2) is pseudo-replicated** and had to be
excluded — it was built with the two slots that overlap. **Slot 3 is disjoint from slot 0 at every
level up to 8**, which is the whole safe range on this pool.

### What was added

New block **`core2x2_slot3`**: the four core-2×2 conditions, all 6 domains, both splits,
`n_examples ∈ {1, 2, 4, 8}`, `slots=[3]`, behavioural + `semantic_one_word` — **384 rows**.
`n_examples=16` is **omitted rather than fudged**: it cannot be disjoint on a 20-sentence pool.

Bank **2352 → 2736**, and the regeneration is **purely additive**, verified against the pre-change file:

| check | result |
|---|---|
| old `prompt_id`s now missing | **0** |
| old rows whose content changed | **0** |
| new rows | 384, all `core2x2_slot3`, all `family_slot=3` |
| slot-3 vs slot-0 sibling behavioural pairs with an **identical prompt** | **0 of 192** |

So all 244 committed runs still join, exactly as with the `external_bank` fix.

This roughly **doubles** the clean `natural_doublespeak` behavioural sample at the levels that matter
(60 → ~108 at `n_examples ≥ 1`), which is the difference between "not established at n=90" and an
answer.

`tests/test_slot_disjointness.py` (5 tests) pins the index arithmetic, **including the negative case**
— slots 1 and 2 *must* be shown to overlap, or R-18's pseudo-replication finding would need revisiting.

**Launched:** `r18pow_extract` (766890) and `r18pow_base` (766891) on the expanded bank. Judge and the
clean G2/G9 re-fits follow.

⚠ **Recorded before the result, so it cannot be shaped by it:** the clean estimate at n=90 is
ρ_within = **−0.052 (p=0.658)**, and core2x2-only at n=60 is **−0.083 (p=0.572)** — two independent
subsets, both null, both negative. **I expect the enlarged sample to confirm a null.** If it instead
shows a clear positive correlation, that would mean the clean subsets were unrepresentative in a way I
have not identified, and I will say so rather than treating it as G2 restored.

## Qwen3 ClearHarm now has a real matched control band — and it does not rescue arm B

Three re-seeded random projections at **L11, matched to arm B** (not the double-random `Dctrl`, which
was matched to a different intervention — the gap found last tick). Band guard **accepted** them on
distinct generation hashes:

| draw | ASR | | |
|---|---|---|---|
| b1 / b2 / b3 | 0.1285 / 0.1453 / 0.1229 | **mean 0.1322, between-draw sd 0.0116** | baseline **0.1341** |

**The band straddles the baseline** — the control is inert on Qwen3 too, and its draw-to-draw sd
(0.0116) is close to Llama's (0.0129), so judge/sampling noise is comparable across models.

Arm B remains **+0.1306 pooled but n.s. clustered (p=0.181)**. The control was never the problem;
**G=6 with one cluster at 71% is**. Unchanged by having a proper control, which is the right outcome:
a matched control tells you the effect is direction-specific, not that it is significant.

## ★ New experiment launched — is the off-bank `d_surface` effect LAYER-LOCALIZED?

Everything in §7c removes `d_surface` at **L8 only**, because that is where the sprint fitted it. That
leaves an obvious question the sprint has never asked: **is L8 special, or would removing `d_surface`
anywhere raise attack success?**

It matters for interpretation. A flat layer profile would say "this direction carries harm-relevant
information throughout the residual stream" — closer to a generic capability effect. A peaked profile
at L8 would say the effect is localized where the surface/concept contrast is represented, which is a
much more specific mechanistic claim and the one §7c implicitly assumes.

Launched `abL{4,12,18,24}_B` (766953–956) — AdvBench 495, arm B's exact intervention at four other
layers, everything else identical to `ab_B`. With L8 already in hand that gives a **five-point layer
profile on the properly-powered external set**.

⚠ Note L18 doubles as a check on a possible confound: it is where `refusalness` is projected in arm C,
so if `d_surface`@L18 behaves like arm C the two directions are less separable at that depth than
cos = 0.019 suggests.

**Prediction, recorded before the runs:** `d_surface` was fitted at every layer but its cosine with
refusal is near-zero at L18 and 0.13 at L12, and the L8 effect is small (+0.0305). I expect a **broad,
low profile** rather than a sharp peak — i.e. removing `d_surface` helps a little at several depths.
If instead L8 is sharply peaked, that is a stronger mechanistic result than anything §7c currently
claims, and it would deserve its own section.

## G2's retraction propagated through every deliverable

The gate table alone was not enough — the claim appeared in five more places, each of which would have
survived a reader who never reached §0:

| location | was | now |
|---|---|---|
| report **§3** (the G2 body section) | ρ=+0.307, "predicts attack success" | ⛔ retracted banner at the head, retracted analysis kept below for the record |
| report **§19 Q5** | "Yes, modestly — in Llama-3.1-8B" | ⛔ retracted; the two clean subsets and the pending power experiment |
| report **§19 Q7** | "Yes, and which probe adds more depends on where you read" | ⛔ superseded **three times**; neither dominates, on a null |
| report **N15 / N16** | — | added as negative results |
| **short update** L48 | "Boombness predicts attack success within the doublespeak arm" | ⛔ retracted in place, before the numbers it introduced |

Each carries the same three facts so none can be read alone: the clean numbers (−0.0518 at n=90,
−0.0832 at n=60), that this is **a null and not a proof of absence**, and that **G1, G3 and the probes
are unaffected** because they filter on `bank_block`.

**Q7 is worth noting as a pattern.** It has now been wrong three times in three different ways — a
mixed-footing artifact, then a 5-df-vs-1-df table, then a correct 1-vs-1 table over a contaminated row
set. Each correction fixed a real defect and each left a different one in place. The lesson is not
"check the footing" or "check the df" but that **a comparison has several independent ways to be
mismatched, and fixing one does not audit the others.**

## §18 rebuilt on causal grounds — and the sprint's claim is sharper than before

The **D-rejection** was argued from *"G2 survives multiplicity correction and control for
`n_examples`"*. R-18 removed that reason. D is still rejected, but now only on the **intervention**
evidence — which is the stronger ground anyway:

> D requires the metric to be "unstable, non-predictive, or confounded after alignment fixes". It **is**
> non-predictive (R-18). But it is not inert: removing `d_surface` **causally raises attack success on
> 495 external harmful prompts against an inert matched control**, it **interacts** with the refusal
> channel, and G1 and G3 are established on independent core-design rows.

**The two facts together are the sprint's actual claim, and R-18 sharpens rather than weakens it:**

> **Boombness does not predict attack success — and removing the direction it measures causally raises
> attack success.**

Those are consistent: a representation can be causally load-bearing without its scalar projection
tracking the outcome across prompts. A single number read off a residual stream is a *lossy* summary
of a direction; ablating the direction is not the same operation as regressing on its magnitude. But
the sprint spent most of its length describing Boombness as **predictive**, and that framing is now
wrong everywhere it appears.

**This is arguably the most interesting thing in the sprint.** The original objective assumed
prediction and causation would travel together — maximise the axis, get more attack success. They do
not: the axis does not predict, the *opposite* manipulation (removing it) is what moves behaviour, and
the objective is dead for both reasons rather than one.

## Layer profile: matched controls launched at every swept layer

`abL{4,12,18,24}_B` completed and are judging. But an arm-B layer profile needs a **control** layer
profile — random-direction effects can themselves vary with depth, and a rising arm-B curve against an
unmeasured control would be exactly the unmatched comparison this session has retracted three times.
`abL{4,12,18,24}_Bctrl` (766968–971) launched at the same layers, same seed discipline as `ab_Bctrl`.
The five-point profile will be reported as **arm minus its own control at each depth**, never as a raw
curve.

## ⛔ R-19 — R-18's blast radius is wider than "G2 and G9": the LOCALIZATION result is half wrong too

`analyze_position`, `analyze_g64` and `analyze_role` **all** filter on `condition == args.arm` with no
`bank_block` clause — the same defect. `analyze_position` produces the **position 2×2**, which the
report calls *"the localization result — the finding worth following"* and lists as takeaway #3 in two
separate places.

Recomputed on the same best columns the artifact selected, full set vs clean set:

| probe / position | full n=234 R² | **clean n=90 R²** |
|---|---|---|
| `d_surface` @ codeword_last (L12\|proj) | 0.1411 | **0.0575** |
| `d_surface` @ last (L8\|proj) | 0.0701 | **0.0488** |
| **`d_surface` position ratio** | **2.01×** | **1.18×** |
| `refusalness` @ codeword_last (L20\|cos) | 0.1888 | **0.0576** |
| `refusalness` @ last (L12\|cos) | 0.0455 | **0.0007** |
| **`refusalness` position ratio** | **4.15×** | **82×** *(unstable — see below)* |

### The published claim was "both probes are 2–4× more predictive of ASR at the codeword token". It is half wrong, and the surviving half does not mean what the number suggests.

**`d_surface`'s position effect is gone.** 0.0575 against 0.0488 is **1.18×** — no localization. This is
exactly what R-18 predicts: if Boombness does not predict ASR at all on clean rows (ρ_within=−0.052),
there is no ASR-predictive state to localize.

**`refusalness` retains a position effect and it is not 4×.** On clean rows it is 0.0576 against
**0.0007** — the last-token R² is essentially zero, so the *ratio* explodes to 82× purely because its
denominator vanished. **A ratio whose denominator is ~0 is not a magnitude**, and quoting "82×" would
be a worse error than the "4×" it replaces. The defensible statement is qualitative: **refusalness has
a detectable relationship with ASR at the codeword token and none at the last token; `d_surface` has
neither.**

**And both surviving numbers are small.** R² ≈ 0.058 on n=90. The localization finding, restated
honestly, is *"the only probe with any ASR relationship on clean rows is refusalness, and only at the
codeword token, and it explains about 6% of the variance."* That is a much weaker claim than
"the ASR-predictive state sits at the codeword token, 2–4× more, for both probes."

### Running total of what R-18 touched

| script | filters `bank_block`? | consequence |
|---|---|---|
| `aggressive_patching` (G1) | ✅ `core2x2` | clean |
| `surgical_knockout` (G3) | ✅ `core2x2` | clean |
| `probes` | ✅ `core2x2` | clean |
| `analyze_g2` | ⛔ no | **G2 retracted** |
| `analyze_g9` | ⛔ no | **R-13's ordering does not survive** |
| `analyze_position` | ⛔ no | **the localization result is half wrong (R-19)** |
| `analyze_g64` | ⛔ no | metric comparison (§7b) — needs the same check |
| `analyze_role` | ⛔ no | §11 role results — needs the same check |

**The pattern is now unmistakable:** every script that filters by `condition` is contaminated; every
script that filters by `bank_block` is clean. The three intervention scripts got it right and the five
correlational ones got it wrong, which is why **all four surviving headline results are causal and none
are correlational.**

## Layer profile — partial, verified, and pointing the opposite way to my prediction

Two of five layers judged. Against baseline **0.0646**:

| layer | arm-B ASR | mean score |
|---|---|---|
| L4 | 0.0667 | 0.0662 |
| **L8** *(the fitted layer)* | **0.1071** | **0.1056** |
| L18 | 0.0667 | 0.0657 |
| L12, L24 | judging | |

**L4 and L18 both land on exactly 0.0667 — the same value as `Dctrl`.** Before reading that as "flat",
I checked whether the interventions had applied at all, because three arms agreeing to four decimals is
the R-12 signature:

| arm | `intervene` | gens sha16 |
|---|---|---|
| `ab_base` | *(none)* | `1447929b8b1dfb24` |
| `ab_B` | `d_surface:project_out:8-8` | `1f5e5d70e75f624b` |
| `abL4_B` | `d_surface:project_out:4-4` | `065d2a1275096079` |
| `abL12_B` | `d_surface:project_out:12-12` | `177b394ab714690f` |
| `abL18_B` | `d_surface:project_out:18-18` | `3adf649a1e460277` |
| `abL24_B` | `d_surface:project_out:24-24` | `1fa8e5173e0782ce` |

**All distinct — the interventions applied.** The identical 0.0667 is a binary-threshold coincidence
(33/495 either way) and the *mean scores* differ, 0.0662 vs 0.0657. Worth the two minutes: had they
been identical generations, the whole profile would have been an artifact.

### My recorded prediction is on course to be wrong

I predicted a **"broad, low profile"** — removing `d_surface` helping a little at several depths — and
said that a sharp peak at L8 *"would be a stronger mechanistic result than anything §7c currently
claims, and would deserve its own section."* So far L4 and L18 sit **at baseline** while L8 is **+66%
above it**. If L12 and L24 come in flat too, the profile is **peaked at the fitted layer**, not broad.

⚠ **Not concluding it yet, and the controls are the reason.** A peak is only a peak relative to what a
*random* direction does at the same depth. `abL{4,12,18,24}_Bctrl` are judging, and the profile will be
reported as **arm minus its own control at each layer** — never as a raw curve. Extended the sweep to
**L6, L10, L16, L28** (766990–993) to bracket L8 tightly, because if the peak is real its *width* is
the interesting quantity and four widely-spaced points cannot resolve it.

## ★ The layer profile is a BAND, not a peak and not a plateau — both my predictions were wrong

All five original layers judged. AdvBench 495, arm B's exact intervention at each depth, baseline
**0.0646**:

| layer | ASR@0.5 | Δ vs baseline | mean score | refusal |
|---|---|---|---|---|
| L4 | 0.0667 | +0.0021 | 0.0662 | 0.9313 |
| **L8** *(where `d_surface` is fitted for interventions)* | **0.1071** | **+0.0425** | 0.1056 | 0.8889 |
| **L12** *(where `d_surface\|L12\|proj` was G2's headline column)* | **0.1010** | **+0.0364** | 0.0997 | 0.8949 |
| L18 | 0.0667 | +0.0021 | 0.0657 | 0.9333 |
| L24 | **0.0646** | **+0.0000** | 0.0636 | 0.9333 |

**Removing `d_surface` raises attack success at L8 and L12, and does nothing at L4, L18 or L24.**
Refusal moves with it — 0.931 → 0.889/0.895 in the band, unchanged outside it.

### Both recorded predictions were wrong, in opposite directions

* I first predicted a **"broad, low profile"** — helping a little at several depths. It is not broad:
  three of five layers are indistinguishable from baseline, and L24 matches it to four decimals.
* I then said a **sharp peak at L8** would be the stronger result. It is not a single-layer peak
  either: **L12 is 86% as large as L8**.

It is a **mid-stack band, roughly L8–L12**. Recording both wrong predictions because both were written
down before the numbers, and the shape that emerged was in neither.

### Why the two elevated layers are the two that matter

L8 and L12 are not arbitrary: **L8 is where every §7c intervention projects `d_surface` out**, and
**L12 is where `d_surface|L12|proj` was the headline column** the whole sprint used as "Boombness".
The causally-effective depth range coincides with the range the sprint independently selected on
representational grounds — which is the kind of convergence that is worth something precisely because
the two selections were made for unrelated reasons.

⚠ **Still not a result until the controls land.** A band is only a band relative to what a *random*
direction does at the same depths, and random-projection damage can itself vary with layer — a mid-stack
random projection may simply be more destructive than a late one. `abL{4,12,18,24}_Bctrl` are judging;
`abL{6,10,16,28}_B` are judged next to resolve the band's **edges**. The profile will be reported as
**arm minus its own control at each layer**, and not before.

## ⚠ SLURM controller outage (infrastructure, not this project)

`sbatch`, `squeue` and `sinfo` all return `Unable to contact slurm controller (connect failure)` as of
**08:04**. The four `abL{6,10,16,28}_Bctrl` submissions failed with that error and are **not queued** —
they must be resubmitted when the controller returns. Nothing was lost: all GPU work already submitted
had completed, and the judge streams run on the login node against the OpenAI API, so they are
unaffected and still going.

## The last two contaminated-filter scripts checked — both survive, for different reasons

I flagged `analyze_g64` (§7b) and `analyze_role` (§11) as filtering on `condition` with no
`bank_block` clause, and said the check would probably cost another finding. It does not.

### §7b (metric comparison) — the sign disagreement SURVIVES

Its central claim is that three operationalisations of "Boombness" **disagree in sign** about ASR at
L12. Recomputed on both row sets:

| metric | full n=234 | **clean n=90** | sign |
|---|---|---|---|
| `direction_boombness` (`d_surface\|L12\|proj`) | **+0.3067** *(retracted)* | **+0.0860** | positive on both |
| `logit_lens` (`ll\|L12\|boombness`) | **−0.1658** | **−0.0865** | negative on both |

**The disagreement holds on clean rows.** ⚠ But it now has a different character: on the clean set
**both correlations are near zero** (+0.086 / −0.087), so what survives is *"two metrics of the same
construct point in opposite directions, and neither is distinguishable from zero"* rather than *"two
real effects with opposite signs"*.

That **strengthens §7b's conclusion while weakening its evidence** — the section's point was that
"Boombness" is not one quantity and that any "Boombness predicts X" claim must name the metric and the
layer. R-18 makes that point harder, not softer: with G2 retracted, the metric that looked predictive
was the one carrying the contamination.

### §11 (role framing) — structurally immune

`analyze_role` does filter on `condition` alone, but its comparison is **only among the five non-plain
role styles**, which live entirely in the `role_style` block at slot 0. `g11_role_full.json` records
`n_prompts: 180` = 5 styles × 36, and its own identifiability note says role *"is NOT identified
against `plain`, which shares no families with any role style"*. The contaminated rows are **all
`plain`** (`strength` 24, `consistency` 36, `position` 12, `core2x2` 60), so they are excluded by the
very guard §9 once flagged as dead and then repaired. **§11 stands unchanged.**

### R-18 final scope

| script | filter | verdict |
|---|---|---|
| `aggressive_patching` (G1) | `bank_block == core2x2` | ✅ clean |
| `surgical_knockout` (G3) | `bank_block == core2x2` | ✅ clean |
| `probes` | `bank_block == core2x2` | ✅ clean |
| `analyze_role` (§11) | `condition` only | ✅ **immune** — compares only within `role_style` |
| `analyze_g64` (§7b) | `condition` only | ✅ **survives** — sign disagreement holds, on two nulls |
| `analyze_position` | `condition` only | ⛔ **half retracted (R-19)** |
| `analyze_g9` | `condition` only | ⛔ **R-13's ordering does not survive** |
| `analyze_g2` | `condition` only | ⛔ **G2 RETRACTED (R-18)** |

**Three retracted, two survived, three were never exposed.** The audit is now complete: every analysis
script in the sprint has been checked against this defect, and the answer for each is recorded above
rather than assumed.

## ★★ R-18 SETTLED — the powered clean estimate confirms the null

The `core2x2_slot3` power block (384 new rows at a slot **provably disjoint** from slot 0) was
extracted, scored and judged. Clean G2 re-fit on **independent core-design rows only**:

| estimate | n | composition | ρ pooled | **ρ within-domain** | **perm p** |
|---|---|---|---|---|---|
| ⛔ as published | 234 | 6 blocks, slots {0,1,2} | +0.3067 | **+0.2618** | **5.0e-04** |
| clean (slot-0, no manipulated) | 90 | core2x2 60 + role_style 30 | +0.0860 | −0.0518 | 0.658 |
| clean (core2x2 only) | 60 | core2x2 60 | +0.1062 | −0.0832 | 0.572 |
| **★ POWERED clean** | **108** | **core2x2 60 + core2x2_slot3 48 · slots {0:60, 3:48}** | +0.1537 | **−0.0660** | **0.493** |

**Three independent clean estimates, at n=60, 90 and 108, all give a within-domain ρ between −0.05 and
−0.08 with p between 0.49 and 0.66.** The powered one adds 48 rows whose demonstrations are disjoint
from every existing family — genuinely new information, not more of the same prompts.

### The prediction, scored

Recorded before the run: *"I expect the enlarged sample to confirm a null. If it instead shows a clear
positive correlation, that would mean the clean subsets were unrepresentative in a way I have not
identified, and I will say so rather than treating it as G2 restored."*

**It confirmed the null.** −0.0660 (p=0.493) at n=108.

### The verdict, stated at its final strength

**G2 is retracted, and this is no longer "not established at n=90 which cannot exclude a small
effect".** It is a null replicated across three independent clean samples, the largest of which was
built specifically to have the power the earlier ones lacked. A small positive effect is still not
formally excluded — n=108 over 6 domains is not large — but every clean estimate is **negative**, and
the published +0.2618 is recoverable **only** by including sibling families that share demonstrations
and rows whose codeword readability was experimentally manipulated.

*(Note `rho_pooled` wanders — +0.086, +0.106, +0.154 across the three clean sets — while
`rho_within_domain` stays pinned near −0.06. That is the domain confound the sprint's own artifact
warns about: the pooled figure mixes between-domain and within-domain variation, which is exactly why
`p_iid_pooled_rho` is marked WITHDRAWN as a sole basis and the within-domain estimand is the one to
cite. The published headline was a pooled number.)*

## ★★★ THE LAYER PROFILE, CONTROLLED — the causal effect is a mid-stack band, and every control is inert

AdvBench 495, 16 domain clusters, arm B's exact intervention at five depths, **each with its own
norm-matched random-projection control at the same depth**
(`outputs/boombness/advbench_layer_profile.json`):

| layer | **arm Δ (clustered)** | **p_cl** | control Δ | control p |
|---|---|---|---|---|
| L4 | +0.0092 | 0.260 | +0.0007 | 0.288 |
| **L8** | **+0.0305** | **0.0089** ✓ | −0.0062 | 0.539 |
| **L12** | **+0.0322** | **0.0056** ✓ | −0.0003 | 0.418 |
| L18 | +0.0037 | 0.305 | −0.0026 | 0.201 |
| L24 | +0.0005 | 0.450 | −0.0066 | 0.512 |

### Three things, and the second is the one that makes it a result

**1. The effect is a band, L8–L12.** Significant at both (p=0.0089 and 0.0056), and **null at L4, L18
and L24** — +0.0005 at L24, which is nothing. Removing `d_surface` raises attack success at mid-stack
depths and nowhere else.

**2. Every control is inert at every depth.** This was the whole reason for running them: a rising arm
curve against an *unmeasured* control would have been the unmatched comparison this session retracted
three times, and "mid-stack random projections are simply more destructive" was a live alternative
explanation. It is now excluded — the five controls span **−0.0066 to +0.0007**, with no depth
dependence at all. **The band is a property of the direction, not of the depth.**

**3. L12 is marginally *larger* than L8** (+0.0322 vs +0.0305) under clustered inference, despite L8
being the layer every §7c intervention was fitted and applied at. So L8 is not privileged; the sprint
picked a depth inside the effective band rather than its centre.

### Why this is worth more than the single-layer result it extends

§7c established that removing `d_surface` causally raises attack success off-bank. That is a claim
about **one intervention at one depth**. This is a claim about **where in the network the direction
matters**, with a matched null at every other depth — and the answer coincides with the two layers the
sprint had independently selected on representational grounds (**L8**, where `d_surface` is fitted for
interventions; **L12**, the `d_surface|L12|proj` column that was the headline "Boombness"). Those two
selections were made for unrelated reasons and they land on the same band.

⚠ **It also sharpens R-18 rather than softening it.** L12 is where the *retracted* correlation lived.
The same layer at which `d_surface`'s projection **fails to predict** attack success (ρ_within = −0.066,
p = 0.49, n=108) is a layer at which **ablating that direction causally raises it** (+0.0322,
p = 0.0056). That is the sprint's central claim localized to a specific depth, and it is a sharper
statement of it than §0 currently makes.

### Still open
`abL{6,10,16,28}_B` are judging and will resolve the band's **edges** — whether it is a plateau from
L8–L12 or peaked between them. Their matched controls **could not be submitted**: the SLURM controller
has been unreachable since 08:04. Until those land the profile is five points, not nine, and the band's
width is bounded only as "≥L8 and ≥L12, <L4 and <L18".

## ★★★ THE NINE-POINT LAYER PROFILE — a contiguous mid-stack band with a hard edge

All nine depths judged. AdvBench 495, 16 domain clusters, baseline **0.0646**
(`outputs/boombness/advbench_layer_profile.json`):

| layer | ASR@0.5 | **Δ clustered** | **p_cl** | refusal |
|---|---|---|---|---|
| L4 | 0.0667 | +0.0092 | 0.260 | 0.9313 |
| L6 | 0.0828 | +0.0159 | **0.0567** *(marginal)* | 0.9131 |
| **L8** | **0.1071** | **+0.0305** | **0.0089** ✓ | 0.8889 |
| **L10** | **0.0970** | **+0.0223** | **0.0190** ✓ | 0.8990 |
| **L12** | **0.1010** | **+0.0322** | **0.0056** ✓ | 0.8949 |
| **L16** | **0.0646** | **+0.0000** | — | 0.9313 |
| L18 | 0.0667 | +0.0037 | 0.305 | 0.9333 |
| L24 | 0.0646 | +0.0005 | 0.450 | 0.9333 |
| L28 | 0.0667 | +0.0037 | 0.305 | 0.9313 |

**Matched random-projection controls at L4/8/12/18/24 span −0.0066 to +0.0007 — all inert, no depth
dependence.**

### The shape: a contiguous band ~L6–L12 with a hard edge between L12 and L16

The profile rises out of baseline at L6 (marginal, p=0.057), is significant at **L8, L10 and L12**, and
then **stops**. L16 is **exactly baseline** — 32/495 either way — and L18, L24, L28 are flat. Refusal
tracks it precisely: 0.931 outside the band, 0.889–0.899 inside, back to 0.931 at L16.

This is not a gradient. It is a **contiguous block of the residual stream, roughly the middle third of
the early-to-mid stack, with a boundary somewhere in L12–L16.**

### ★ L16 is the most informative point, and it is not a null

L16's Δ is **exactly zero**, which is the shape of a failed intervention — so I checked, as with L4/L18
last tick:

> `abL16_B` gens sha16 `b26aeaa2d5cc2772` vs baseline `1447929b8b1dfb24`, and **146 of 495
> generations (29.5%) differ from baseline.**

**The intervention applied and it changed what the model said on nearly a third of prompts — and
changed whether it complied on none of them.** That excludes the boring explanation ("`d_surface` is
not present at L16, so removing it does nothing") and replaces it with a much stronger one:

> **At L16 the direction is present, ablating it perturbs generation, and the perturbation is
> behaviourally inert.**

A layer where the intervention demonstrably *does something* to the text and *nothing* to compliance is
a far better control for the band than any random direction — it is the same direction, the same
operation, at a depth 4 layers away, and the behavioural effect vanishes completely.

### What the profile adds to §7c

§7c showed the effect exists at one depth. This shows it exists in a **bounded region** and is absent
outside it, with the boundary sharp enough to see between two adjacent probe points. Combined with
R-18 — the same L12 at which the projection **fails to predict** attack success (ρ_within=−0.066,
p=0.49) is inside the band where **ablating it causally raises** attack success (+0.0322, p=0.0056) —
the sprint's central claim is now localized in depth as well as demonstrated.

⚠ **The four edge points (L6, L10, L16, L28) have no matched control**, because the SLURM controller
has been unreachable since 08:04. They are reported as arm-only. The five controlled points already
bracket the band on both sides (L4 and L18/L24 controlled and inert), so the band's *existence* does
not depend on them; its *edges* are currently arm-only measurements.

## SLURM recovered — the outage cost nothing, and two things went back in

The controller returned some time before **09:33** (down since 08:04). Nothing was lost: all GPU work
submitted before the outage had already completed, and the judge streams run on the login node against
the OpenAI API, so they were never affected.

**Resubmitted:** `abL{6,10,16,28}_Bctrl` (767100–103) — the four edge controls whose submissions failed
during the outage. That completes the layer profile at all nine depths.

## ★ New: a specificity test stronger than a random control

Every control so far has been a **norm-matched random direction**, which answers *"is this better than
noise?"* It does not answer the obvious follow-up: **is the band about `d_surface` specifically, or
about any direction fitted on this bank?** A random vector is not a fair comparison for that — it has
no structure at all, while `d_surface` was fitted on a real contrast.

The extraction already produces three sibling directions from the same 2×2 on the same rows:

| direction | what it is fitted to separate |
|---|---|
| **`d_surface`** | codeword surface form vs concept — the sprint's headline direction |
| **`d_naive`** | the naive concept-minus-codeword contrast, without the 2×2's controls |
| **`d_context`** | benign vs harmful *context*, holding surface form fixed |

Launched `abL8_naive` and `abL8_context` (767150–151): arm B's exact intervention at L8, same set, same
seed, **substituting a sibling direction**. `d_naive` and `d_context` are real fitted directions with
their own meaning, so this is a much sharper specificity test than a random projection.

**Prediction, recorded before the runs.** `d_naive` is the *less* controlled version of the same
contrast and correlates strongly with `d_surface` (the extract shows cosines around 0.9 at mid-stack),
so I expect it to reproduce most of the effect — that would be reassuring rather than surprising.
`d_context` separates a different thing entirely (harm context, not surface identity), so if the band is
about surface/concept representation it should be **substantially smaller or absent**. If `d_context`
matches `d_surface`, the effect is not about the codeword contrast at all and §7c's interpretation
needs rewriting — that is the outcome that would cost the most, which is why it is worth running.
