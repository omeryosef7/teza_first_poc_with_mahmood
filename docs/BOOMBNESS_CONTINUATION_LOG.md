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
