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
against a raw +0.3067. The reason it is not a confound is measurable: `n_examples` predicts ASR
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
