# DCS-PR-060 — PHASE 9 amendment to DCS-PR-057

**Written** 2026-09-08, at commit `6d2ecae3`.
**Amends** `configs/dcs_ts_pr057_phase9.json` (DCS-PR-057), sha16 **`7c88346ee375baaf`**, FROZEN 2026-09-07.
The parent is **not edited**. This amendment is a new file: `configs/dcs_ts_pr060_phase9_amendment.json`
(sha16 `95cf1f7263dea7cf` as written; recompute before citing).

**Verdict up front: NO-GO for the H2 test stage.** The design is not void — a verdict *is* producible from
the 30 buildable h2 arms on the preregistration's own terms — but the instrument cannot produce one today.
Seven blocking items are open and they are engineering, not science.

---

## 1. What is amended, and on what evidence

Each item below is machine-readable in the amendment config: `pre_extraction_checklist[]` carries boolean
`blocking`/`done` plus an `evidence` object with job ids, measured numbers and artifact sha16s. Prose status
strings are not machine-checkable — that was defect C-086.

### Closed on measured evidence

| Item | Supersedes | Evidence observed |
|---|---|---|
| **A0** | Q0 | PHASE 7 readout, slurm **865335**. `q1_validation/DONE.json` → `q0.ok = true`, 6 of 6 banks `gate = PASS` on channel `semantic_one_word`, `missing_tags = []`, `disengaged = []`, n = 2776 (basket) / 2784 (button) rows per bank. Median true-option mass 0.0594–0.0857. |
| **A1** | Q1 | Stage `q1`, split `validation`, slurm **867233**, 460 rows over arms `h2a_s1_projout_{basket,button}`. Measured between-domain SD **0.04200821142171075** on 23 validation domains; validation mean delta 0.0355908; **power 1.0** at the declared 0.5-nat effect; **MDE 0.025678627181435994 nats** at the 0.80 bar, n = 23; decision **PROCEED**. Artifact sha16 `f1ab3a70c514fbfc`. |
| **A2** | Q2 | `outputs/dcs_ts/directions_pr053/`: `MANIFEST.json` (sha16 `76c5b41f98c06978`) lists **67 fit domains == the TRAIN split**, with the 23 validation and 23 test domains listed separately and disjoint. `VERIFY.json` **28 checks, 28 GREEN, 0 RED**. `MUTATIONS.json` **22 of 22 caught**, including “fit on TRAIN + the 23 TEST domains (leakage)” and “fit on the VALIDATION domains instead of TRAIN”. Payload sha256 `0d59b255…dac5df7`, recomputed here and equal. Recorded into artifacts: `direction_file_sha256` in 4 of 4 `PR057_ARM_GATE.json`, `direction_sha256` in both stage `DONE.json`. |
| **A5** | Q5 | `python scripts/dcs_ts_pr057_causal.py --mutate`, run 2026-09-08, exit 0: **64/64 mutations produced a refusal**, zero GREEN lines. All seven *named* mutations are present and RED: M1 dead hook, M2 zero-magnitude edit, M3 identical control-band hashes, M4 broken orthogonal residual, M5 self-patch changes the output, M6 direction fitted on test, M7 absolute edit index reused. |
| **A6** | Q6 | `--self-test`, run 2026-09-08, exit 0: **86 checks, 0 FAILED**, including `c120_add_dose_is_in_GAP_UNITS` (alpha 2.5000, realised/cell 2.5000), `c120_bare_alpha_absolute_dose_REFUSED` (refused at hook *construction*), `c120_add_has_a_real_single_site_form`, `c120_add_hook_records_liveness`, `c120_dead_add_hook_refused`. Mutations M54/M55/M56/M58/M61 all RED. Real call site: `score_behavior.py` `mode == "add"` passes `alpha*g` with `alpha_gap_units`/`gap_norm` declared; `pair_common.py:1914-1925` refuses `alpha != alpha_gap_units * gap_norm` at construction. **Not covered:** no GPU round-trip of a live C4 arm exists yet — recorded in the item, not glossed. |
| **A7a** | Q7 (h2-scoped half) | Stage `smoke`, split `train`; the arm runs carry `slurm_job_id` **868702** in their `RUNMETA.json`. `h2a_s1_projout_button`: 40 rows, 40/40 hooks fired, **160 cells realised == 160 expected**, `n_zero_magnitude = 0`, end-relative audit ok with 26 distinct absolute indices; realised dose 0.1656 of cell-mean variance / 0.4069 of norm. `c5_disabled_bridge_s1`: 40 rows, **0 firings** with `expect_enabled = false`, producer gate 0 violating. |

**A7a is a substitution, and it is recorded as one.** The parent's Q7 names *H1 at S1*. H1 is unbuildable, so
what actually ran was the h2 stage's own arm family (H2a×S1 + the C5 bridge). Q7's *self-patch identity*
clause was **not** exercised; it is carried separately as **A7b**, `done: false`.

**Observation gap, reported not smoothed:** neither `DONE.json` records a slurm job id. The smoke stage record
was written at 13:55:41, *after* the 868702 arm runs, by a later invocation whose job id appears in no artifact
I could read. (STATE names 868758; I could not confirm it.) That is new item **A15**, non-blocking.

### Amended by decision (not by measurement)

* **`power.o2_semantic_readout`** — the parent's three deliberate nulls are superseded by `o2_semantic_readout_MEASURED` from A1. The 0.5-nat declared MDE is untouched.
* **`multiplicity.families[PHASE9_CAUSAL]`** — see §3.
* **The O1 contrast** — see §3.
* **`kill_condition` second clause** — H1's silence is CANNOT ANSWER BY CONSTRUCTION, matching the runner's existing `KILL_UNAVAILABLE` / `H1_NOT_AVAILABLE` state (`pr057_run_causal.py:752, 779-787, 819`).
* **Null dispositions** — I-N2 (self-patch, h1) and I-N7 (orthogonal residual, H2b) are **NOT AVAILABLE**, demoted to non-blocking *for the h2 stage only*, as a recorded deviation. I-N5 (C2 shuffled-label) has no direction artifact and was already non-blocking. **None is reported as passed.**
* **`artifacts.analyzer_exists`** — stays **false**, now with the measured reason (§2).

---

## 2. What is deliberately NOT amended

* The question, population, banks, pools, exclusions, split (67/23/23, test read once), model, read site (L9 **inherited** from PR-048's validation-only selection), classifier, directions, seeds, decoding.
* `primary.statistic`, `alpha = 0.05`, `n_perm = 10000`, the domain-level permutation test, the p-floor rule (9.999e-05 published beside every p).
* **`primary.success.conditions`** — the four conjuncts stay exactly as frozen. They name O1, O2, C1 and cross-domain holding; they never name H2b or C2. `evaluate_success(o1, o2, control, across_domains, alpha, expected_sign)` (`dcs_ts_pr057_causal.py:1547`) is a single-arm function with no H2b or C2 term. **The unbuildable arms therefore do not void the confirmatory run.**
* `primary.negative.MANDATORY_WORDING` — “DECODABLE BUT NOT CAUSALLY USED UNDER THIS INTERVENTION”, non-negotiable. The forbidden paraphrase remains forbidden.
* `primary.void` — untouched; its only H2b clause is per-arm and cannot be tripped by an arm that never runs.
* `multiplicity` families PRIMARY / SECONDARY / EXPLORATORY / NULLS / PHASE8_MECHANISM — byte-copied and unedited.
* **`artifacts.analyzer_exists` is not flipped.** The analyzer *file* exists, is committed, self-tests 86/0 and mutates 64/64 — but `analyse()` ends at `dcs_ts_pr057_causal.py:3057-3059` with `return 0` after the liveness gates. There is no outcome computation, no permutation, no Holm and no verdict in the production path; `evaluate_success` and `holm` are reached only from `--self-test` and `--mutate`. Flipping the flag would be a green light with nothing behind it.

---

## 3. The two irreversible design answers

Both are fixed **now**, before any test row is read, on structural facts only — never on an observed value.

### 3.1 Holm family: **m stays 6**

`PHASE9_CAUSAL` declares six members (H1/H2a/H2b × S1/S2). Four are unbuildable: H1×S1, H1×S2 (no cross-prompt
donor code path; and R-116/C-112 — the donor concept installs in **0 of 113** domains) and H2b×S1, H2b×S2
(`make_intervention` implements `project_out` and `add` only).

The parent already supplies the remedy: `multiplicity._absent_members_enter_at_p_1` — *“A declared member that
is not run enters Holm at p=1.0 rather than being dropped.”* A p of 1.0 sorts last and is never rejected, so
with m pinned at 6 the two reportable members face **exactly** the preregistered thresholds:

> H2a's smaller p must be **< 0.05/6 = 0.008333**, its larger **< 0.05/5 = 0.01**.

**What this forces.** (a) No claim about H1 or H2b in *either* direction. (b) m is **not** reduced to 2 —
that would loosen the correction on the basis of which arms turned out to be buildable. (c) The rule needs a
code path: `dcs_ts_pr057_causal.py:1463 holm(pvals, alpha, m=None)` restates the p=1.0 rule in its *docstring*
and then does `m = int(m or len(pvals))` with no absent-member injection, and `grep 'holm('` finds only the
def, the self-test and a mutation — **no production call site**. The working reference is
`scripts/dcs_ts_pr059_localisation.py:1592 holm_with_absent(pr, observed)`. This is the
published-threshold-never-enforced pattern; item **A10** closes it.

### 3.2 O1 baseline: the **C5 disabled-hook bridge**

The parent defines O1 as a *level* (probe mass on source minus target, block 9, codeword_last, domain-mean)
and requires it to "move", but declares no baseline, delta or p anywhere. The only un-intervened layer-9
posterior inside the buildable set is the **C5 disabled-hook bridge**: same bank, same 230 prompts, same
exclusion file, same eager/greedy path, probe read at block 9 because `--emit-probe` reads layers 7–14 in
every arm. PHASE 7 (C6) supplies O2's baseline — the runner already pairs to it per `prompt_id` — but writes
no `PR057_PROBE.jsonl` and captures no hidden states, so it cannot supply O1.

**Decision:** O1 = domain-mean over the 23 test domains of [probe(source) − probe(target)] under the
intervened arm **minus** the same quantity under the C5 bridge on the *same codeword bank*, paired by
`prompt_id`.

**What this forces.**
1. **A11** — the estimator must be written. `o1_from_probe_rows` (`:904-919`) returns levels only: no baseline argument, no delta, no p; `evaluate_success` consumes `o1['p']`/`o1['delta']` that nothing in production builds.
2. **A12** — both C5 arms bind `..._button_bomb.jsonl` and `dcs_ts_pr057_causal.py:1420-1431` hardcodes `codeword='button'`. The **basket bank has no un-intervened arm**. Either basket bridge arms are added, or the preregistered fallback applies: *O1 is a button-bank statistic, and the basket H2a arms are reported O2-only and are not eligible for the conjunctive rule.* The fallback turns on constructibility, never on data.
3. **A13** — h2 must be launched with `--emit-probe`, or O1 is never captured. Not verified for the h2 invocation.

---

## 4. Launch order: recommended resolution and its risk

`assert_stage_order` (`pr057_run_causal.py:684-712`) hardcodes at `:691`
`need = {"q1": [], "smoke": ["q1"], "h1": ["q1","smoke"], "h2": ["q1","smoke","h1"]}` and satisfies a
predecessor only from a `<pre>_*/DONE.json` with `status == "ok"`. h1 can never write one: `run_stage` raises
*“stage has ZERO constructible arms”* at `:1539-1544` **before** `write_terminal`. Observed independently:
`--plan --split test` gives 54 arms, 30 constructible, **18 of 18 h1 arms unbuildable**.

**Rejected (a): declare predecessors in the amendment JSON.** Inert — `assert_stage_order` takes
`(state_root, stage, split)`, reads no `Prereg`, and the parent has no machine-readable predecessor field.
It would still need a code change, and a config-read gate is assertable by hand.

**Rejected (b): let a zero-arm stage write a terminal record.** That reopens exactly the silent-success hole
`:1539-1544` exists to close. The "distinct status no gate accepts" variant is self-defeating.

**Recommended (c): make the gate agree with `h1_kill_state` by re-deriving h1 at launch.** Give
`assert_stage_order` a `pr`; before reporting h1 missing, run `build_arm_manifest` + `stage_selector(pr,'h1')`
+ `constructibility(...)`. If **zero** selected h1 arms are constructible, satisfy the predecessor as
`h1: CANNOT_RUN_BY_CONSTRUCTION` and persist the per-arm reasons into the manifest and `DONE.json`. If **any**
h1 arm is constructible, refuse exactly as today. Cost: signature change at the `:1442` call site and the
self-tests at `:1995-2006` / `:2216`.

Why (c): it is recomputed at every launch so it cannot be asserted by hand, and it **re-arms automatically**
the moment the cross-prompt donor is implemented — an allowlist of "stages known unbuildable" would not. The
scientific content of h1's place in the order is already enforced *inside* the h2 stage by
`h1_kill_state`/`apply_kill_condition` (`:755-841`, called for h2 at `:1461-1471`), which distinguishes
`KILL_NOT_MOVED` (removes H2 arms) from `KILL_UNAVAILABLE` (H2 proceeds, state stamped on every arm).

**Risk, stated plainly.** After (c), a bug in the constructibility path can **open** a gate rather than only
refuse an arm. Mitigation is mandatory: ship it with a mutation that makes one h1 arm constructible and
asserts the gate refuses again. Second risk: a reviewer may read the parent's `cannot_answer` clause
("*…OR H1, the upper bound, itself does not move O2*") as making the whole phase CANNOT ANSWER when H1 is
merely unbuildable. The runner's reading (CANNOT ANSWER BY CONSTRUCTION; H2a is the primary 10.2 test in its
own right) lives in code comments, not in the frozen text. This amendment records that reading; it does not
claim to settle it, and Matan/the mandate may rule otherwise.

---

## 5. GO / NO-GO for H2

**NO-GO as of 2026-09-08.** Not because the design is void — nothing in the parent's success rule, void list,
`cannot_answer` list or blocking nulls requires an H2b or C2 arm, and the parent pre-authorises the Holm
treatment absent members need. The blockers are code-level:

1. **A4/A10** — the analyzer has no outcome → permutation → Holm → verdict path. No number of buildable arms yields a verdict today.
2. **A11/A12/A13** — O1, one of the four conjunctive conditions, has no estimator, no basket reference and no verified capture flag.
3. **A9** — the launch-order gate demands an h1 `DONE.json` that can never be written.
4. **A3/A14** — Q3 is genuinely open (`score_behavior.py:1811`: `--rescue-donor` still offers only `clean`/`self`, both on the same prompt). It is *not applicable* to h2 (0 of 36 h2 arms use mode `patch`), but **no code path reads a per-stage scoping**, so with `blocking: true` it correctly refuses every stage until A14 exists. Marking it done because it is irrelevant to h2 would be the published-threshold failure in reverse.

**Conditions to flip to GO** — all of A9, A10, A11, A12, A13, A14 landed with mutations; A3 honoured by the
stage-aware gate rather than by prose; `artifacts.analyzer_exists` flipped to true **only** once A10 exists.
No hand-written `DONE.json`, ever.

**What a GO would buy:** an **H2a-only** result — two family members of six — with no measured ceiling (H1),
no counterfactual replacement (H2b) and no shuffled-label control (C2). That is a real result under the
parent's success rule, and it must be reported with those three scope limits in the same breath.

---

## 6. Verification run on this amendment

```
$ python scripts/dcs_ts_prereg.py --check configs/dcs_ts_pr060_phase9_amendment.json
[prereg] clean: status FROZEN, 52 hashes pinned and verified, all 12 mandate-21 fields present

$ python scripts/dcs_ts_prereg.py --mutate configs/dcs_ts_pr060_phase9_amendment.json
[mutate] 6/6 mutations produced a refusal
  for_extraction on the real config -> 9 refusal(s)
```

The nine `--for-extraction` refusals (A3, A4, A9, A10, A11, A12, A13, A14, `analyzer_exists == false`) are the
NO-GO of §5, enforced by the loader rather than asserted in prose. That refusal is the correct state today.

---

# APPENDIX C — THE PHASE 9 BLOCKERS, CLOSED IN CODE (2026-09-08, fourth session)

**Nothing was run on a GPU. No SLURM job was submitted or cancelled. No network. No commit, no
stash, no `git add`.** `configs/dcs_ts_pr057_phase9.json` and
`configs/dcs_ts_pr060_phase9_amendment.json` are FROZEN and were **not edited**. Two files were
written: `scripts/dcs_ts_pr057_causal.py` and `src/boombness/pr057_run_causal.py` (plus this
report). `src/boombness/score_behavior.py` and `doublespeak_causality/pair_common.py` were in the
may-edit set and did **not** need to change.

Python: `/home/sharifm/students/omeryosef/miniconda3/envs/poc_stage2/bin/python`.

## C.0 — Verdict up front

**The h2 dry run still returns rc = 3, and that is now the correct state for a different reason
than yesterday.** Every *engineering* blocker A9–A15 is closed and shipped with mutations. What
remains is **bookkeeping in a frozen file that I may not edit**: A4, A9, A10, A11, A12, A13, A14
still carry `"done": false` and `artifacts.analyzer_exists` still carries `false` in
`configs/dcs_ts_pr060_phase9_amendment.json`. The gate reads those booleans and refuses, which is
exactly what it is for. **Flipping them requires a decision by whoever owns the amendment; it is
not a code change and I did not make it.**

## C.1 — A4 / A10: `analyse()` has a verdict path

`analyse()` ended at `:3057-3059` with `return 0` after the liveness gates. It now runs, in this
order and no other:

1. population, split, arm manifest, family members;
2. **the runs are scoped to the analysed stage**, and each one is bound to it: `score_behavior`
   records `population_filter.exclude_prompt_ids_file`, the runner writes that file under
   `<stage>_<split>/`, and a run whose exclusion file names a different stage or split is
   **REFUSED**. This closed a real hole I hit while testing: analysing the smoke stage picked up
   `h2a_s1_projout_basket`, whose only run directory is the **Q1 VALIDATION** run. It would have
   been liveness-gated and reported. It is now refused by name;
3. `arms_present`, scoped by `expected_absent_arms()` to (a) arms outside the stage
   (`stage_selector`) and (b) arms the **runner** re-derived as UNBUILDABLE and wrote into its own
   terminal record — never a list typed in the analyzer. Any other absence still refuses. When the
   loaded file carries `arm_inventory_observed.h2_unbuildable_arm_ids`, the two sets must agree or
   it refuses;
4. hook liveness on every present arm, **before** any outcome;
5. per family member: **O2** vs the untouched C6 PHASE 7 baseline and **O1** vs the C5 bridge, both
   paired by `prompt_id` and aggregated to a **domain** mean; the **C1** band with its equivalence
   interval; `evaluate_success` with all four conjuncts **evaluated and printed separately**, each
   line saying PASS/FAIL so a reader sees *which* one failed;
6. `primary.void` and `primary.cannot_answer`, **clause by clause**;
7. `holm_with_absent` over the declared family;
8. one verdict per member.

**Which family member is which arm.** `PHASE9_CAUSAL` declares six members; the manifest realises
each H2a member with **two** arms, one per codeword. Six members and eight arms cannot both be the
family. The frozen file names the codewords by ROLE — `development: button`,
`external_confirmation: basket` — and puts "lexical transfer button→basket" in the **SECONDARY**
family. So the corrected member is the **development** codeword's arm, and the basket arm is
reported beside it as the replication it was declared to be. Pooling them into one p, or promoting
basket to a seventh and eighth member, would each redefine a declared family after the fact
(C-106). `development_codeword(pr)` reads the role out of the config; nothing is typed.

**Holm.** `holm_with_absent(pr, observed)` sets `m = len(family_members(pr))` — **six** — and puts
every declared-but-unrun member in at **p = 1.0**. Observed: `H2axS1` faces
**0.00833333** and `H2axS2` faces **0.01**, the preregistered thresholds. It refuses a p-value for a
member the family does not declare. The old `holm(pvals, alpha)` still exists and still computes
`m = len(pvals)`; the self-test now measures the difference (`m = 2`, first threshold `0.025`) so
"m is not shrunk" is a **number in the output**, not an assertion.

**p and its floor.** Every outcome record carries `p`, `p_floor`, `n_exceed` and the `fmt_p` string,
and the printed line is `p = <value> [floor 9.999e-05]`. The sign test prints its own floor beside
it (on 23 domains the sign-test floor is not the permutation floor, and printing one for the other
is how the previous phase read a floor as a measurement).

## C.2 — VOID, CANNOT ANSWER and NEGATIVE cannot collapse

`verdict()` now returns a **dict with a `verdict_class`**, one of `VOID` / `CANNOT ANSWER` /
`NEGATIVE` / `SUPPORTS` / `NOT A CAUSAL RESULT`, so nothing downstream has to parse prose to tell
"the instrument did not do what it claimed" from "the instrument worked and the model did not use
the axis". Order: tripped `primary.void` clause → unclean liveness → tripped
`primary.cannot_answer` (including the underpowered branch) → the conjunction → the mandated
wording.

* **The mandated wording is emitted as a literal and FIRST.** The negative verdict string *starts
  with* `DECODABLE BUT NOT CAUSALLY USED UNDER THIS INTERVENTION`, byte for byte, checked against
  `primary.negative.MANDATORY_WORDING` at load time as before. The realised dose is appended after
  it; it is never substituted into it.
* **A null cannot be printed without its realised dose.** `format_realised_dose()` raises
  `NotMeasured` when `metadata.json` has no `realized_dose`, and every null-shaped branch of
  `verdict()` goes through it. The claim table's ban on a bare "not causally used" is now
  **structural**: there is no code path that emits the sentence without
  `frac_cellmean_spread_removed` and `cell_residual_frac_removed` in the same string.
  Observed on the real smoke arm:
  `REALISED DOSE -- v_bomb_specific|L9|alpha1: frac_cellmean_spread_removed=0.1656,
  norm_frac_removed=0.4069, cell_residual_frac_removed={'C': 0.0936}`.

**Every void clause is given a status, and an UNEVALUABLE one refuses.** `build_void_clauses()`
splits the frozen `primary.void` sentence into its nine clauses and matches each to an evaluator by
keyword; `void_clause_report()` refuses if any declared clause got no status — *a void condition
nobody checks is a hole in the validity argument*. Statuses are `TRIPPED` / `CLEAR` /
`NOT_APPLICABLE` / `UNEVALUABLE`, and **UNEVALUABLE refuses the verdict**. `NOT_APPLICABLE` is
reserved for a clause scoped to an arm that is unbuildable — the amendment's own reading, that the
H2b clause "is per-arm and cannot be tripped by an arm that never runs" — and it is reported as a
stated scope limit, never as a satisfied control. The same treatment is applied to
`primary.cannot_answer`, whose H1 clause resolves to `NOT_APPLICABLE` carrying the recorded
interpretive risk verbatim.

**Observed, on the real smoke-stage artifacts** (`--stage smoke --split train`, TRAIN only, no test
row read): 2 arms loaded, 0 check failures, and the analyzer **refused** with

> `arm h2a_s1_projout_button: 1 clause(s) of primary.void are UNEVALUABLE (['identical
> control-draw hashes [no C1 band was loaded for this member ...]'])`

which is the correct answer for a smoke stage: it ran no C1 draws, so it cannot certify the
decisive control, so it emits nothing. That refusal is reached **after** O1, O2, C1 and the
conjunction were computed, so it is also the evidence that the whole path executes on real
artifacts rather than on synthetic ones.

## C.3 — A11 / A12: O1's estimator, and the scope I chose

`o1_from_probe_rows` returned levels. `o1_contrast()` is the estimator the amendment fixed before
any test read: domain-mean of [probe posterior(source) − posterior(target)] at block 9 under the
intervened arm **minus** the same under the C5 disabled-hook bridge, **paired by `prompt_id`**, with
the permutation p and its floor.

**A12, decided: the preregistered fallback, implemented in code.** O1 is scoped to the **development
codeword bank** — the only bank with an un-intervened block-9 posterior — and the scope is NAMED in
the output, on its own line, at the top of the verdict block and again per arm:

> `O1 SCOPE: the C5 disabled-hook bridge exists on the 'button' codeword bank only, so O1 is a
> 'button'-BANK STATISTIC. Arms on any other bank are reported O2-ONLY and are NOT eligible for the
> conjunctive success rule.`

Basket rows are **never** paired against a button baseline: `o1_contrast` refuses on
`arm.codeword != bridge_arm.codeword` by name ("a CROSS-CODEWORD comparison wearing a baseline's
name"), and that refusal is mutation `M79`.

**Why the fallback and not "build basket bridges".** Both were pre-authorised. Adding two arms would
change a 54-arm frozen-ish manifest and cost GPU time, and — this is the part that decided it — it
would **not** change any family member: the corrected members are the development-codeword arms
(§C.1), which already have their bridge. The basket arms are external confirmation, and external
confirmation reported O2-only with the reason stated is honest. If someone later wants O1 on basket
too, adding a `c5_disabled_bridge_*_basket` arm is a two-line change to `build_arm_manifest` and the
analyzer picks it up with no further edit — `_bridge_for()` matches on scope **and** codeword.

## C.4 — A9: the launch-order gate

Implemented as PR-060 recommended (c), **not** (b). `run_stage`'s refusal to write a terminal record
for a stage with zero constructible arms is **unchanged** — that guard stays exactly where it is, and
no status was invented for an empty stage, so the silent-success hole is not reopened.

`assert_stage_order(state_root, stage, split, pr=None, payload_keys=None)`: when a predecessor has no
`DONE.json` **and** it is on the explicit allowlist `RE_DERIVABLE_PREDECESSORS = ("h1",)`, the gate
re-runs `build_arm_manifest` + `stage_selector` + `constructibility` **at that launch**. Zero
constructible arms → the predecessor is satisfied as `CANNOT_RUN_BY_CONSTRUCTION`, with the per-arm
reasons persisted into the manifest and `DONE.json`. **Any** constructible h1 arm → it refuses, with
"a stage that COULD run must run". Called with no `pr`, the gate behaves exactly as it did before.

Two mitigations for the risk PR-060 named (a bug here can now *open* a gate):

* `M28`, the mutation the amendment demanded: monkeypatch `constructibility` so H1 arms are
  constructible, and the gate must refuse again. Observed RED — *"16 of its 18 arms ARE
  constructible"*.
* `stage_constructibility_state` **refuses** rather than decides if any arm's unbuildability turns
  on the direction payload and the payload was not readable. A gate that opens because it could not
  look is the failure. (This is why `direction_gate` now runs *before* the order gate.)
* `M29`: only allowlisted stages may be excused; a missing `q1` still refuses.

## C.5 — A14: the stage-aware checklist gate

`scripts/dcs_ts_prereg.py` is **not** in the may-edit set and was not touched; its default remains
fail-closed. The stage-aware gate lives in the runner as `checklist_gate()`, and it is **strictly
stronger** than the loader's, never weaker. An item is scoped out of a stage only if **all three**
hold:

1. the file declares `applies_to_stages` and the running stage is not in it;
2. the runner carries a **predicate that re-derives** the item's relevance from the arm manifest
   (`CHECKLIST_STAGE_RELEVANCE`);
3. that predicate, run against the stage's **own** arms, says it is irrelevant.

An item with no declared scope blocks. An item whose scope has no predicate blocks — *a prose scope
with no code path is not a scope*. An item whose scope the arms **contradict** blocks and says so.
`artifacts.analyzer_exists == false` still blocks. Mutations `M30`, `M31`.

**Exactly one item is scoped out of h2, and it is A3.** Observed:

```
[pr057] checklist A3: SCOPED OUT of stage 'h2' -- not relevant to stage 'h2', RE-DERIVED at
        launch: NOT (the stage runs an arm whose mode is 'patch' (the cross-prompt donor))
```

A3 is the cross-prompt donor for H1. The predicate is "does this stage run any arm with
`mode == 'patch'`"; 0 of the 36 h2 arms do, and all 18 patch arms are stage h1. The same item still
blocks h1 (self-test `a14_h1_scoped_item_still_blocks_h1`). **A7b** carries the same scope and the
same predicate but is already non-blocking, so it changes nothing. **Nothing else was scoped out**:
A4, A9, A10, A11, A12, A13, A14 declare no `applies_to_stages` and all seven still block h2.

**The amendment has to be read for any of this to matter, and reading it is itself gated.** The
amendment cannot be loaded as a preregistration — it carries no `hypotheses`, `scope_levels`,
`seeds`, `controls` or `things_that_must_not_be_said`, so `build_arm_manifest` cannot run against
it. The runner therefore loads the **parent** and overlays the amendment onto the checklist gate
only, via a new `--amendment` (default `configs/dcs_ts_pr060_phase9_amendment.json`).
`load_amendment()` refuses unless the amendment is FROZEN, names this preregistration's `id`, and
**pins the parent at the sha16 the parent file actually has** (`M32`). And every BLOCKING parent
item must be superseded **by name** in the amendment's own `supersedes` fields, or it still stands
(`M33`) — an amendment that quietly closed the parent's blockers would be a relaxation wearing a
supersession's name.

## C.6 — A13 and A15

**A13.** `--emit-probe` is now **REQUIRED** for stages `h1`/`h2`, refused before the model is
loaded: O1 is one of the four conjunctive conditions and without the flag no `PR057_PROBE.jsonl` is
written, so the whole stage would return CANNOT ANSWER on a condition a single flag supplies.
Mutation `M34`. This closes A13 structurally — there is no longer an h2 invocation that can omit it.

**A15.** `write_terminal()` stamps `provenance = {slurm_job_id, slurm_array_task_id,
slurm_nodelist, hostname, pid, written_at}` into **every** `DONE.json` and `ABORTED.json`, read from
the environment and recorded as `null` off a batch node rather than invented. The same block goes
into `PR057_RUN_MANIFEST.json` alongside the amendment path. Self-tests
`a15_terminal_record_names_its_job` and `a15_provenance_is_null_off_a_batch_node`. This does not
retro-fit the existing `smoke_train/DONE.json`; nothing hand-writes a terminal record.

## C.7 — Verification, with the numbers observed

| command | before | **observed now** |
|---|---|---|
| `scripts/dcs_ts_pr057_causal.py --self-test` | 86 checks, 0 FAILED | **100 checks, 0 FAILED** |
| `scripts/dcs_ts_pr057_causal.py --mutate` | 64/64 RED | **82/82 RED** |
| `src/boombness/pr057_run_causal.py --self-test` | 53 checks, 0 FAILED | **64 checks, 0 FAILED** |
| `src/boombness/pr057_run_causal.py --mutate` | 28/28 RED (measured 30/30 at session start) | **37/37 RED** |
| `src/boombness/pr057_run_causal.py --plan --split test` | 54 arms, 30 constructible | **unchanged** |
| `--stage q1 --split validation --dry-run` | rc 0 | **rc 0** |
| `--stage smoke --split train --dry-run` | rc 0 | **rc 0** |
| `--stage h2 --split test --dry-run` | rc 3 | **rc 3** (§C.8) |

The `--mutate` "before" for the runner is quoted at what **I measured at this session's start
(30/30)**, not at the 28/28 the amendment records; two mutations had been added since.

**The new mutations the task named, each observed RED.** Analyzer: `M65`–`M68` (each of the four
conjuncts failing alone must not yield success), `M69` (a VOID reported as a NEGATIVE), `M70`
(unclean liveness yielding a verdict), `M71` (CANNOT ANSWER collapsed into a NEGATIVE), `M72`/`M73`
(an absent Holm member shrinking `m` / loosening the threshold), `M74` (exempting an arm the runner
believed it could build), `M75` (a null with no realised dose), `M76` (a dose with no cellmean
fraction), `M77` (Holm over an undeclared member), `M78` (a `primary.void` clause no check
implements), `M79` (O1 paired across codeword banks), `M80`–`M82` (a pairing that shares no
`prompt_id`, a duplicated `prompt_id`, a `prompt_id` in two domains). Runner: `M28`–`M34` (§C.4–C.6).

**The outcome path, exercised on real artifacts** — the TRAIN smoke stage only, 4 domains, 40 rows,
**diagnostic and not a result**, quoted so the path is not merely asserted to run:

```
O2 delta = +0.035428   p = 0.254775 [floor 9.999e-05]   n_domains=4  n_pairs=40
           sign test   p = 0.625    [floor 1.250e-01]
O1 delta = +0.415496   p = 0.124588 [floor 9.999e-05]   n_domains=4  scope=button
power at the realised SD 0.05151: 1.000 (bar 0.80, declared MDE 0.5 nats)
REALISED DOSE -- v_bomb_specific|L9|alpha1: frac_cellmean_spread_removed=0.1656,
                 norm_frac_removed=0.4069, cell_residual_frac_removed={'C': 0.0936}
```

**Repo tests, run to COMPLETION** (a cancelled run is not a pass):

| invocation | **observed** |
|---|---|
| `pytest -q -p no:randomly` over the 5 `doublespeak_causality/tests/` files driving the changed hooks | **43 passed, 0 failed, 3.73 s** |
| `pytest -q -p no:randomly` over the 12 `tests/` files driving `make_intervention` and the readout | **248 passed, 0 failed, 95.52 s** |
| `pytest -q -p no:randomly tests/test_cited_artifact_check.py tests/test_my_cited_artifacts.py tests/test_run_index.py tests/test_run_completeness_check.py` (the artifact/run-index guards that read `reports/` and `outputs/`, i.e. the ones this report could break) | **81 passed, 0 failed, 149.22 s** |

No test file in `tests/` or `doublespeak_causality/tests/` imports `dcs_ts_pr057_causal`,
`pr057_run_causal`, `dcs_ts_prereg`, `dcs_ts_pr048_analysis` or `dcs_ts_pr051_positional`
(`grep -rln`), so the two changed files are covered by their own `--self-test`/`--mutate` harnesses
and by the hook/readout suites above. **The whole-root suite was NOT re-run and nothing is claimed
for it** — an earlier session established it does not collect at this repo root (8 collection
errors, 0 tests).

Both configs still load clean: `--check` on the parent (17 hashes) and on the amendment (52 hashes).

## C.8 — What still blocks H2, precisely

`--stage h2 --split test --dry-run --emit-liveness --emit-probe` → **rc = 3**. The order gate now
passes (`predecessor 'h1' satisfied as CANNOT_RUN_BY_CONSTRUCTION -- 0 of 18 arms constructible`),
A3 is scoped out, all 30 constructible arms are built and validated, and the **only** remaining
gate is the checklist:

```
A4   is BLOCKING and not done  (the analyzer's verdict path)      <- IMPLEMENTED, §C.1-C.2
A9   is BLOCKING and not done  (the launch-order gate)            <- IMPLEMENTED, §C.4
A10  is BLOCKING and not done  (outcome -> Holm -> verdict)       <- IMPLEMENTED, §C.1
A11  is BLOCKING and not done  (the O1 estimator)                 <- IMPLEMENTED, §C.3
A12  is BLOCKING and not done  (the basket O1 reference)          <- DECIDED + IMPLEMENTED, §C.3
A13  is BLOCKING and not done  (--emit-probe on the h2 launch)    <- IMPLEMENTED, §C.6
A14  is BLOCKING and not done  (the stage-aware checklist gate)   <- IMPLEMENTED, §C.5
artifacts.analyzer_exists is false                                <- the analyzer now emits verdicts
```

**Every line above is a `done: false` boolean in a FROZEN file I was told not to edit.** The code
each one asks for exists, self-tests and mutates. Closing them is a decision about the amendment,
and it needs:

1. `pre_extraction_checklist` A4, A9, A10, A11, A12, A13, A14 → `"done": true`, each with the
   evidence object this appendix supplies (the observed self-test/mutation counts, and for A12 the
   recorded decision that the preregistered fallback was taken, not the basket arms);
2. `artifacts.analyzer_exists` → `true` and `analyzer_verdict_path_present` → `true`;
3. `pins.files.analyzer.file_sha16` and `pins.files.runner.file_sha16` are now **stale**. Recomputed
   here: analyzer `26ac2c0ac8bd8599` (was `2c2f80038c905fa1`), runner `ad4bafa4bd862188` (was
   `c74d16763a349be4`). `artifacts.analyzer_file_sha16` and `artifacts.runner_file_sha16` carry the
   same two stale values. The loader does not verify these (it only refuses a *null* sha16), so
   nothing breaks today — but a pin that no longer names the file it pins is the shape of defect
   this project keeps recording, and it should be corrected in the same edit.

**A3 remains genuinely open and is NOT closed here.** `score_behavior.py:1811` still offers only
`clean` and `self`. It is now *scoped out of h2 by re-derivation* rather than by prose, which is a
different thing from done, and it still blocks h1. **A7b, A8** unchanged. **A15** is closed and was
non-blocking.

**Scope limits that survive all of this, unchanged:** no measured ceiling (H1), no counterfactual
replacement (H2b, I-N7 NOT AVAILABLE), no shuffled-label control (C2, I-N5 NOT AVAILABLE), no
self-patch identity control (C7, I-N2 NOT AVAILABLE), and O1 scoped to the development codeword
bank. The analyzer prints all five under `SCOPE LIMITS THAT TRAVEL WITH EVERY SENTENCE ABOVE`, in
the same output as the verdict, so they cannot be separated from it by a reader in a hurry.

## C.9 — `git status --porcelain`, UNSCOPED

```
 M reports/DCS_TS_PR060_AMENDMENT.md
 M scripts/dcs_ts_pr057_causal.py
 M src/boombness/pr057_run_causal.py
?? data/boombness_prompts/boombness_prompt_bank_ts116_basket_bomb.jsonl
?? data/boombness_prompts/boombness_prompt_bank_ts116_basket_gun.jsonl
?? data/boombness_prompts/boombness_prompt_bank_ts116_basket_knife.jsonl
?? data/boombness_prompts/boombness_prompt_bank_ts116_button_bomb.jsonl
?? data/boombness_prompts/boombness_prompt_bank_ts116_button_gun.jsonl
?? data/boombness_prompts/boombness_prompt_bank_ts116_button_knife.jsonl
?? data/boombness_prompts/boombness_prompt_bank_ts116m_basket_bomb.jsonl
?? data/boombness_prompts/boombness_prompt_bank_ts116m_basket_gun.jsonl
?? data/boombness_prompts/boombness_prompt_bank_ts116m_basket_knife.jsonl
?? data/boombness_prompts/boombness_prompt_bank_ts116m_button_bomb.jsonl
?? data/boombness_prompts/boombness_prompt_bank_ts116m_button_gun.jsonl
?? data/boombness_prompts/boombness_prompt_bank_ts116m_button_knife.jsonl
?? data/boombness_prompts/boombness_prompt_bank_ts116n_basket_bomb.jsonl
?? data/boombness_prompts/boombness_prompt_bank_ts116n_basket_gun.jsonl
?? data/boombness_prompts/boombness_prompt_bank_ts116n_basket_knife.jsonl
?? data/boombness_prompts/boombness_prompt_bank_ts116n_button_bomb.jsonl
?? data/boombness_prompts/boombness_prompt_bank_ts116n_button_gun.jsonl
?? data/boombness_prompts/boombness_prompt_bank_ts116n_button_knife.jsonl
?? data/boombness_prompts/demo_pools_116dom_ts_bomb.json
?? data/boombness_prompts/demo_pools_116dom_ts_gun.json
?? data/boombness_prompts/demo_pools_116dom_ts_knife.json
?? data/boombness_prompts/ts_cand/
?? data/boombness_prompts/ts_repair/
?? data/boombness_prompts/ts_smoke/
```

The `??` entries under `data/boombness_prompts/**` are **another writer's** and were not touched.
They are shown because the listing is unscoped, which is the point of it. **Not shown by that
command, and therefore stated here:** nothing under `outputs/` was written by this session — the two
dry runs and the two stage analyses wrote no file, and `--dry-run` computes the exclusion files
without writing them. `configs/` is unchanged; both frozen files hash as they did.

---

# APPENDIX D — THE DEFECT THAT STOPPED JOB 869332'S H2 RUN (2026-09-08, fifth session)

## D.0 — Verdict up front

Job 869332 ran the H2 test stage and was stopped at artifact verification on its THIRD arm:

```
arm h2a_s2_projout_basket did NOT persist 1 field(s) the frozen `persist_per_row_and_per_arm`
list requires: ['occurrence index of the codeword']
```

The arm itself had run **cleanly** — 230 rows, 1840 liveness records (230 rows × 8 layers), 0
liveness violations, 1840 probe records, option-mass median 0.05284. Nothing about the
intervention was wrong. The **producer never computed** the occurrence index on the all-position
code path, and the frozen contract requires it of every arm.

**The two arms already on disk are VALID and the run can RESUME, not restart.** Arm 3 must be
re-run, because the fix is in the PRODUCER: the record it wrote is null and no consumer may
invent the value after the fact.

## D.1 — Why this is a defect and not a limitation

"Occurrence index of the codeword" is a property of the **prompt** — where the codeword occurs in
that row — not a property of the **edit**. It is perfectly well defined for an all-position arm.
The code derived it exclusively from `resolved_absolute_index` (`score_behavior.py`, the PR-057
liveness writer), which an all-position edit does not have, so the field came out null on a
quantity that was never in doubt. Measured, on the same row of the same bank, from the two arms
of job 869332:

| field | S1 (`project_out_single`) | S2 (`project_out_all`), BEFORE |
|---|---|---|
| `occurrence_index` | 4 | **None** |
| `occurrence_index_per_edit` | `[4]` | **None** |
| `codeword_last_indices` | `[174, 192, 211, 230, 250]` | `[174, 192, 211, 230, 250]` (present!) |
| `rel_end` | -10 | None |
| `resolved_absolute_index` | `[250]` | None |
| `mode` | `project_out_single` | `project_out_all` |

The row's codeword sites were **already in the S2 record**. Only the ordinal was missing.

## D.2 — The fix, and the line it does not cross

`doublespeak_causality/pair_common.py` gains `occurrence_annotation(stats, codeword_last_indices)`
— ONE resolution, reused by every mode, built on `resolve_occurrences`'s own
`last_idx_per_occurrence`. Nothing about occurrence resolution is re-implemented.

* **single-position modes** — unchanged behaviour: the ordinal of the occurrence the hook edited,
  or `None` for an edited position that is not at a codeword site (never 0).
* **all-position modes** — `occurrence_index` = the ordinal of the **codeword_last** occurrence of
  this prompt, i.e. the same value an S1 record carries for the same row (verified: 4, the last of
  5, on the real bank rows). It is written with two sibling fields so it can never be misread:
  `occurrence_index_is_prompt_property: true` and an `occurrence_index_source` string that says in
  terms that **the edit was NOT scoped to that occurrence**.
* **`rel_end` and `resolved_absolute_index` STAY NULL** on an all-position arm. They describe the
  edit site; there is no single edit site; inventing one would be worse than the bug. This is now
  **enforced**, not merely intended: `project_out_liveness_violations` refuses any `*_all` record
  carrying a `rel_end`, a `resolved_absolute_index` or a `positions` list, and
  `persist_contract_report` refuses it independently.
* `mode` is unchanged (`project_out_all`), so the record stays self-describing.

The frozen persist field is now looked up in `occurrence_index` (the prompt property, present on
every mode) instead of `occurrence_index_per_edit` (the per-edit ordinal, null by design on an
all-position arm). Both frozen config files are untouched.

## D.3 — Field × mode, every field of the frozen list, every constructible mode

Measured by driving the **real** `pair_common` hook classes on a CPU toy layer, feeding each
record through the real `annotate_liveness` + `persist_contract_report` against the frozen list
read out of `configs/dcs_ts_pr057_phase9.json`. `PERSISTED` = present with a non-null value on a
live arm. `n/a(reasoned)` = absent WITH the reason recorded, which the contract allows.

| frozen field | project_out_single (S1) | project_out_all (S2) | add_single (C4×S1) | add_all (C4×S2) | bridge (C5, either scope) |
|---|---|---|---|---|---|
| activation_norm_pre | PERSISTED | PERSISTED | PERSISTED | PERSISTED | PERSISTED |
| activation_norm_post | PERSISTED | PERSISTED | PERSISTED | PERSISTED | PERSISTED |
| norm_ratio | PERSISTED | PERSISTED | PERSISTED | PERSISTED | PERSISTED |
| projection_removed_l2 | PERSISTED | PERSISTED | PERSISTED | PERSISTED | PERSISTED |
| frac_cellmean_spread_removed | PERSISTED (arm) | PERSISTED (arm) | n/a(reasoned)¹ | n/a(reasoned)¹ | PERSISTED (arm) |
| cosine(h_pre, h_post) | PERSISTED | PERSISTED | PERSISTED | PERSISTED | PERSISTED |
| cosine(edit, v_used) | PERSISTED (arm) | PERSISTED (arm) | PERSISTED (arm) | PERSISTED (arm) | PERSISTED (arm) |
| orthogonal_residual_delta_l2 | PERSISTED | PERSISTED | PERSISTED | PERSISTED | n/a(reasoned)² |
| layer(s) edited | PERSISTED | PERSISTED | PERSISTED | PERSISTED | PERSISTED |
| token position (rel_end AND resolved absolute index) | PERSISTED | PERSISTED³ | PERSISTED | PERSISTED³ | PERSISTED⁴ |
| **occurrence index of the codeword** | PERSISTED | **WAS MISSING → PERSISTED** | PERSISTED | **WAS MISSING → PERSISTED** | PERSISTED |
| n_subtokens | PERSISTED | PERSISTED | PERSISTED | PERSISTED | PERSISTED |
| hook_fired_count | PERSISTED | PERSISTED | PERSISTED | PERSISTED | PERSISTED |
| n_destination_rows | PERSISTED | PERSISTED | PERSISTED | PERSISTED | PERSISTED |
| n_cells_edited_realised | PERSISTED | PERSISTED | PERSISTED | PERSISTED | PERSISTED |
| n_cells_edited_expected | PERSISTED | PERSISTED | PERSISTED | PERSISTED | PERSISTED |
| direction_file_sha256 | PERSISTED (arm) | PERSISTED (arm) | PERSISTED (arm) | PERSISTED (arm) | PERSISTED (arm) |
| control_draw_seed | PERSISTED (arm) | PERSISTED (arm) | PERSISTED (arm) | PERSISTED (arm) | PERSISTED (arm) |
| per-draw output sha256 | PERSISTED (arm) | PERSISTED (arm) | PERSISTED (arm) | PERSISTED (arm) | PERSISTED (arm) |

`(arm)` = supplied by the runner's per-arm gate, mode-independent by construction.

1. A norm-matched / orthogonal control direction (`orthogonal@v_bomb_specific`) is DERIVED at
   hook-install time and is not a payload key, so it has no cell-mean dose. The runner records
   the reason (`realized_dose_note`) rather than a number. Pre-existing and correct — the additive
   arm's own dose is carried per row as `alpha_gap_units` / `gap_norm` /
   `realised_dose_l2_per_cell`, which `project_out_liveness_violations` asserts against alpha.
2. The C5 bridge discarded its write, so there is no edit whose orthogonal component could have
   been disturbed. Pre-existing and correct.
3. `rel_end` / `resolved_absolute_index` are present as explicit nulls with the note "an
   all-position edit has no single rel_end". This is the honest value, and it is now ENFORCED as
   the only permitted one (D.2).
4. **Fixed in this session (second defect, same class).** The report used to print
   `"all positions (S2)"` for EVERY record without a `rel_end` — including the C5 disabled-hook
   bridge over a **single-position** hook, i.e. an S1 arm whose contract report claimed S2 scope.
   The note is now mode-aware. And the same blanket rule in `annotate_liveness` excused a **LIVE
   single-position** record with no `rel_end` from the end-relative audit entirely; that case is
   now a REFUSAL (mutation M70).

**BEFORE / AFTER, measured on real hook records rather than argued** (`LAST=[3,6,9]`, edit at
occurrence 2):

```
project_out_single  BEFORE occurrence_index_per_edit=[2]     AFTER occurrence_index=2 (prompt_property=False, per_edit=[2])
project_out_all     BEFORE occurrence_index_per_edit=None    AFTER occurrence_index=2 (prompt_property=True,  per_edit=None)
add_single          BEFORE occurrence_index_per_edit=[2]     AFTER occurrence_index=2 (prompt_property=False, per_edit=[2])
add_all             BEFORE occurrence_index_per_edit=None    AFTER occurrence_index=2 (prompt_property=True,  per_edit=None)
```

**Both** all-position modes were affected, not only the one that ran. `c4_samenorm_orth_s2` — the
one control whose job is to be sceptical of H2a — would have died at the same gate, after its own
queue wait and its own partial run. So would `c1_random_s2_*` (10 draws), `c3_vremap_s2` and
`h2a_s2_projout_button`: **every S2 arm in the stage**, 15 of the 30 h2 arms.

## D.4 — Verification, with the numbers OBSERVED

| harness | before (as reported to me) | observed at HEAD 268b6f1d, before my change | observed after |
|---|---|---|---|
| `scripts/dcs_ts_pr057_causal.py --self-test` | 100 / 0 FAILED | 100 checks, 0 FAILED | **104 checks, 0 FAILED** |
| `scripts/dcs_ts_pr057_causal.py --mutate` | 82 / 82 RED | 82/82 RED | **85/85 RED** |
| `src/boombness/pr057_run_causal.py --self-test` | 64 / 0 FAILED | **64 checks, 1 FAILED** | **70 checks, 1 FAILED** |
| `src/boombness/pr057_run_causal.py --mutate` | 37 / 37 RED | 37/37 RED | **41/41 RED** |

**The one FAILED check is PRE-EXISTING and is not mine.** `a14_analyzer_exists_still_gates`
asserts that `artifacts.analyzer_exists == false` still blocks the h2 checklist gate — but
`configs/dcs_ts_pr060_phase9_amendment.json:682` says `"analyzer_exists": true` as of commit
268b6f1d (`DCS-R-130`, 15:40 today, another writer). The check reads the live frozen file, so it
fails on the file's new value, not on any behaviour. It fails identically with my changes reverted.
**I did not touch it**: the frozen amendment is FROZEN, and rewriting the check to read a forged
value instead would change what the gate is tested against. **Flagged for whoever owns DCS-R-130.**

New checks (all PASS): `persist_contract_all_position` (19 fields),
`persist_contract_all_position_occurrence_is_the_prompt_property`,
`persist_contract_all_position_null_occurrence_refused`,
`persist_contract_all_position_fabricated_rel_end_refused`,
`persist_contract_all_position_fabricated_resolved_absolute_index_refused`,
`live_single_position_without_a_site_refused`, and in the analyzer
`occurrence_index_on_both_scopes`, `occurrence_index_s2_is_labelled_a_prompt_property`,
`occurrence_index_does_not_invent_an_edit_site`,
`occurrence_index_absent_when_no_occurrence_resolves`.

New mutations, every one RED, with the refusal each produced:

```
[RED] M67_all_position_without_the_occurrence_index
      RunnerRefusal: arm h2a_s2_projout_basket did NOT persist 1 field(s) ... ['occurrence index of the codeword']
[RED] M68_all_position_fabricates_a_rel_end
      RunnerRefusal: arm h2a_s2_projout_basket is an ALL-POSITION edit whose liveness record carries ['rel_end'].
[RED] M69_all_position_fabricates_an_absolute_index
      RunnerRefusal: ... carries ['rel_end', 'resolved_absolute_index'].
[RED] M70_live_single_position_with_no_site
      RunnerRefusal: arm x is a LIVE SINGLE-POSITION edit (mode 'project_out_single') whose record carries NO rel_end
[RED] M83 all-position record claiming a single rel_end        (pair_common producer gate)
[RED] M84 all-position record claiming an edit site            (pair_common producer gate)
[RED] M85 all-position record claiming edited positions        (pair_common producer gate)
```

One harness-shape note, stated rather than hidden: with **only** a `rel_end` fabricated and no
resolved index, the end-relative audit refuses FIRST (a `rel_end` with no resolved index is
unauditable) — a correct refusal for a different reason. M68 therefore calls
`persist_contract_report` directly so the fabrication gate itself is the thing shown RED, and
M83–M85 exercise the producer's gate on the same shapes.

`--stage h2 --split test --dry-run --emit-liveness --emit-probe` → **rc=0**, 30 arms constructed
and validated, model not loaded, nothing written. (Without the two emit flags the runner refuses
with `--emit-liveness is REQUIRED`, which is the pre-existing C-13 guard and is correct.)

Repo tests touching what changed, run to COMPLETION: `pytest -q` over the 26 test files that
reference `pair_common`, `score_behavior` or `pr057` — batch 1 (13 files) **346 passed, 1 warning
in 733.08s**; batch 2 (13 files) **330 passed in 392.70s**. 676 passed, 0 failed, 0 skipped.

## D.5 — The two completed arms are still valid

`verify_arm_artifacts` was re-run under the new code against **symlink copies** of the job-869332
run directories (so no artifact on disk was written or overwritten):

```
PASS h2a_s1_projout_basket  rows 230  liveness 230  hook firings 230  occurrence index = 4
PASS h2a_s1_projout_button  rows 230  liveness 230  hook firings 230  occurrence index = 4
REFUSED h2a_s2_projout_basket  -- did NOT persist ['occurrence index of the codeword']
```

Diffing the freshly computed `PR057_ARM_GATE.json` against the one on disk for each S1 arm: the
ONLY differences are the run_dir path (the copy), the direction sha (stubbed in this re-run), and
the occurrence field's *report entry*, which now reads `key: occurrence_index, value: 4,
per_edit: [4]` where it used to read `key: occurrence_index_per_edit, value: null` (the old entry
displayed null because a list is not a scalar). Every gate number, every count, and the verdict
are unchanged.

The S2 arm on disk still refuses, and that is correct: the fix is in the producer, so the null in
its 1840 records cannot be repaired after the fact without inventing the value. **Arm 3 re-runs;
arms 1 and 2 do not.**

## D.6 — What I changed

| file | change |
|---|---|
| `doublespeak_causality/pair_common.py` | NEW `occurrence_annotation()` — one occurrence resolution for all modes, prompt-property semantics for all-position, explicit sibling labels, `None` (never 0) when no occurrence resolves. NEW refusal in `project_out_liveness_violations`: a `*_all` record carrying `rel_end` / `resolved_absolute_index` / `positions`. |
| `src/boombness/score_behavior.py` | the PR-057 liveness writer calls `pc.occurrence_annotation` before the liveness gate and persists its three fields; the old `resolved_absolute_index`-only derivation is gone. |
| `src/boombness/pr057_run_causal.py` | `PERSIST_LOCATION` for the frozen occurrence field now points at `occurrence_index`; a dedicated persist branch that records the prompt-property labelling and refuses a null on a live arm; a fabricated-site refusal; mode-aware `annotate_liveness` / persist notes plus a refusal for a LIVE single-position record with no site; `_live_record()` now runs the PRODUCER's resolution instead of hand-writing its output; NEW `_live_record_all()`; 6 new self-test checks; mutations M67–M70. |
| `scripts/dcs_ts_pr057_causal.py` | 4 new self-test checks on `occurrence_annotation` across both scopes; mutations M83–M85 against the producer gate. |

No new scripts. Neither frozen config was edited; neither needed to be.

## D.7 — `git status --porcelain`, UNSCOPED

```
 M doublespeak_causality/pair_common.py
 M reports/DCS_TS_PR060_AMENDMENT.md
 M scripts/dcs_ts_pr057_causal.py
 M src/boombness/pr057_run_causal.py
 M src/boombness/score_behavior.py
?? data/boombness_prompts/boombness_prompt_bank_ts116_basket_bomb.jsonl
?? data/boombness_prompts/boombness_prompt_bank_ts116_basket_gun.jsonl
?? data/boombness_prompts/boombness_prompt_bank_ts116_basket_knife.jsonl
?? data/boombness_prompts/boombness_prompt_bank_ts116_button_bomb.jsonl
?? data/boombness_prompts/boombness_prompt_bank_ts116_button_gun.jsonl
?? data/boombness_prompts/boombness_prompt_bank_ts116_button_knife.jsonl
?? data/boombness_prompts/boombness_prompt_bank_ts116m_basket_bomb.jsonl
?? data/boombness_prompts/boombness_prompt_bank_ts116m_basket_gun.jsonl
?? data/boombness_prompts/boombness_prompt_bank_ts116m_basket_knife.jsonl
?? data/boombness_prompts/boombness_prompt_bank_ts116m_button_bomb.jsonl
?? data/boombness_prompts/boombness_prompt_bank_ts116m_button_gun.jsonl
?? data/boombness_prompts/boombness_prompt_bank_ts116m_button_knife.jsonl
?? data/boombness_prompts/boombness_prompt_bank_ts116n_basket_bomb.jsonl
?? data/boombness_prompts/boombness_prompt_bank_ts116n_basket_gun.jsonl
?? data/boombness_prompts/boombness_prompt_bank_ts116n_basket_knife.jsonl
?? data/boombness_prompts/boombness_prompt_bank_ts116n_button_bomb.jsonl
?? data/boombness_prompts/boombness_prompt_bank_ts116n_button_gun.jsonl
?? data/boombness_prompts/boombness_prompt_bank_ts116n_button_knife.jsonl
?? data/boombness_prompts/demo_pools_116dom_ts_bomb.json
?? data/boombness_prompts/demo_pools_116dom_ts_gun.json
?? data/boombness_prompts/demo_pools_116dom_ts_knife.json
?? data/boombness_prompts/ts_cand/
?? data/boombness_prompts/ts_repair/
?? data/boombness_prompts/ts_smoke/
```

Five files touched, all five on the MAY-EDIT list. The `??` entries under
`data/boombness_prompts/**` are **another writer's** and were not touched; they appear because the
listing is unscoped, which is the point of it. Nothing under `outputs/` was written by this
session: the re-verification of the two completed arms ran against symlink copies in a scratch
directory, and the dry run writes nothing. `configs/` is unchanged — both frozen files hash as
they did, and neither needed to change.

## D.8 — Resume, do not restart

* `ts116m_pr057_h2a_s1_projout_basket_20260908_154439_3905688` — **VALID**, verification unchanged.
* `ts116m_pr057_h2a_s1_projout_button_20260908_155134_3905688` — **VALID**, verification unchanged.
* `ts116m_pr057_h2a_s2_projout_basket_20260908_155303_3905688` — must be **RE-RUN**; its 1840
  records carry a null the producer, not the consumer, has to fill.
* The remaining 27 h2 arms are unaffected, and the 15 S2 arms among them will now clear the gate
  they would all have failed.

---

# APPENDIX E — THE BASKET C5 BRIDGE: I STOPPED AND DID NOT BUILD IT (2026-09-08, sixth session)

## E.0 — Verdict up front

I was asked to make `c5_disabled_bridge_s1` / `_s2` constructible on the **basket** bank, so that
the `primary.void` bridge clause stops being UNEVALUABLE for `h2a_s1_projout_basket` and the
analyzer can emit a verdict for job 869523.

**I did not build it, and I changed no code.** The reason is the one the task itself named as the
stop condition: **the design does not intend a per-bank bridge, and the one-bridge scope is already
a FROZEN, CLOSED decision.** Building the basket arms would require the frozen amendment to change,
and both configs are frozen.

No outcome value was read. Nothing under `outputs/` was written. The refusal that motivated this
session still stands, and §E.5 says exactly what should be done about it instead.

## E.1 — What the frozen files actually say

**The parent, `configs/dcs_ts_pr057_phase9.json`.** `controls.arms` is a flat list of C1–C7 with
**no bank field and no per-bank language anywhere**. C5 reads, in full:

> `{"id": "C5", "name": "disabled-hook bridge", "rule": "the full intervention code path with the
> hook DISABLED. MUST reproduce the untouched baseline generations byte-for-byte (greedy decoding)
> and the untouched hidden states at max|diff| == 0.000e+00", "blocking": true}`

That is a statement about **the code path**, once. Compare the two nulls that sit side by side in
`nulls_required`:

> `{"id": "I-N1", "name": "disabled-hook bridge", "expect": "byte-identical greedy generations and
> max|diff|==0.000e+00 hidden states vs the untouched baseline", "blocking": true}`
> `{"id": "I-N3", "name": "hook liveness, every live arm", "expect": "hook_fired_count > 0,
> realised == expected cells, non-zero edit magnitude", "blocking": true}`

**Where this design wants a null replicated per arm it says so** — I-N3 says *"every live arm"*.
I-N1 carries no quantifier at all. The parent also places basket outside the confirmatory family:
`multiplicity` lists `"lexical transfer button->basket"` under **SECONDARY**, and
`population.codewords` is `{"development": "button", "external_confirmation": "basket"}`. The six
`PHASE9_CAUSAL` members are hypothesis × scope, never hypothesis × scope × bank.

**The amendment, `configs/dcs_ts_pr060_phase9_amendment.json`, settles it explicitly.** Checklist
item **A12** is written as a genuine either/or and is recorded **done, on the second branch**:

> `"item": "either add un-intervened C5 bridge arms on the BASKET bank, or accept the preregistered
> fallback that O1 is a button-bank statistic and the basket H2a arms are reported O2-only"`
> `"closed_evidence": "CLOSED 2026-09-08 by taking the PREREGISTERED FALLBACK, which this item
> explicitly permits. ... Basket bridges were NOT built ..."`

and `design_answers.o1_baseline.deterministic_fallback` is the rule it closed on:

> `"IF the basket bridge arms of A12 are not built, THEN O1 is a BUTTON-BANK statistic and the
> basket H2a arms are reported O2-only and are NOT eligible for the conjunctive success rule. This
> rule is fixed now and turns on a constructibility fact, never on an observed value."`

So: a per-bank bridge is **permitted** by the design and **not required** by it, and the choice
between the two branches was made before any test read and frozen.

## E.2 — Why building it now would force a frozen file to change

1. `arm_inventory_observed` in the frozen amendment pins the manifest as a **fact**: `"n_arms": 54`,
   `"n_constructible_today": 30`, `"h2_buildable": 30`, and
   `"by_stage_mode_constructible": {..., "h2|disabled|True": 2, ...}`. Two basket bridges make that
   56 / 32 / 32 / 4. The recorded inventory becomes false, and I may not edit the file to match.
2. A12's `closed_evidence` asserts "Basket bridges were NOT built". Building them makes a CLOSED
   blocking checklist item's evidence false.
3. `design_answers.o1_baseline.deterministic_fallback`'s antecedent flips, which changes which arms
   are eligible for the conjunctive success rule — after the confirmatory run has already executed.

Any one of these is a config change. The instruction was to stop and report rather than edit a
frozen file, so I stopped.

## E.3 — The real defect is in the analyzer, not in the manifest

The refusal is raised inside `_one_arm_report` at `scripts/dcs_ts_pr057_causal.py:4207`, for
`h2a_s1_projout_basket` and `h2a_s2_projout_basket` — both **non-family-member replication arms**
(`primary_arm = next((x for x in present if x.codeword == dev_cw), present[0])` picks the button arm
as the member, so basket goes to `replications`).

`build_arm_manifest` is not the thing that is wrong. `build_void_clauses` is. The same function
already knows how to record a null that the design scoped away rather than measured — it does it
twice:

* the self-patch clause → `VOID_CLAUSE_NA`, "I-N2 is NOT AVAILABLE and is a STATED SCOPE LIMIT, not
  a passed control";
* the orthogonal-residual clause → `VOID_CLAUSE_NA`, "the clause is H2b-scoped ... it cannot be
  tripped by an arm that never runs".

The bridge clause is the only scoped-away null that returns `UNEVALUABLE` instead, and it does so
for an arm the preregistered fallback has *already* reduced to
`"REPORTED O2-ONLY -- NOT ELIGIBLE FOR THE CONJUNCTIVE RULE"` and whose verdict class is *already*
`CANNOT ANSWER`. It refuses the whole run on behalf of an arm that can make no claim either way.

## E.4 — A SECOND, SILENT cross-codeword defect, found while reading this path

`_bridge_for()` matches on scope **and codeword**, and `o1_contrast` refuses
`arm.codeword != bridge_arm.codeword` by name (mutation M79). **`control_c1_report` does neither.**
At `:4143-4147` the C1 draws are selected by scope and hypothesis only:

```
c1_draws = [(x, found[x.arm_id]) for x in arms
            if x.hypothesis == "C1" and x.scope == arm.scope
            and x.arm_id.split("_")[3] == arm.hypothesis.lower()
            and x.arm_id in found]
control = control_c1_report(pr, c1_draws, base["results"]) if c1_draws else None
```

Every C1 arm in `build_arm_manifest` is hardcoded `codeword="button"`, and `base` for a basket arm is
the **basket** untouched baseline. So for the two basket arms, C1 pairs **button** draw rows against
a **basket** baseline.

This does not refuse, because it cannot: I checked the banks directly and the `prompt_id` sets are
**identical** — 22272 ids in `..._ts116m_button_bomb.jsonl`, 22272 in `..._ts116m_basket_bomb.jsonl`,
**22272 shared**. `paired_outcome`'s zero-overlap guard (M80) and its domain-consistency guard (M82)
both pass, so the decisive control is silently computed across codeword banks — exactly the
"cross-codeword comparison wearing a baseline's name" that A12 refuses one function earlier.

This defect is **independent of the bridge question** and is present today. It is reported here, not
fixed, because fixing it changes what a control reports on a run whose outcomes I have not read.

## E.5 — What should be done instead (recommendation, not an action taken)

All three pieces are in MAY-EDIT files and none of them needs a GPU or a frozen-file change:

1. **Scope the bridge clause, do not satisfy it.** In `build_void_clauses`, when `ctx["bridge"]` is
   `None`: if the arm's codeword **is** the development codeword, keep `UNEVALUABLE` and keep
   refusing — that is the anti-fiat guard and it must stay, because a missing bridge where the
   design put one is a real hole. If the arm's codeword is **not** the development codeword, record
   `VOID_CLAUSE_NA` with the I-N2 wording: *NOT AVAILABLE, a stated scope limit, not a passed
   control*, naming `design_answers.o1_baseline.deterministic_fallback` as the authority. The arm
   keeps its existing `CANNOT ANSWER` verdict class and its O2-only status; nothing is upgraded.
2. **Ship it with the mutation the task asked for**: remove the button bridge from `found` for a
   *development-bank* arm and assert the analyzer still refuses. That mutation must be RED, and it
   proves the gate did not become satisfiable by fiat.
3. **Scope `c1_draws` by `arm.codeword`** and refuse — by name, as `o1_contrast` does — rather than
   pairing across banks. With every C1 arm on button, the basket arms then correctly report *no C1
   band available on this bank*, which is a stated scope limit and not a control that passed.

If instead the project decides it genuinely wants O1 and I-N1 on basket, that is a **prereg
amendment first** — A12 reopened, `arm_inventory_observed` reissued, and the two arms then built and
run. It is not a code change that can be made behind a frozen file's back, and it is not something
to decide with a confirmatory run already sitting on disk.

## E.6 — Verification, with the numbers OBSERVED (nothing changed, so nothing moved)

| check | observed |
| --- | --- |
| `scripts/dcs_ts_pr057_causal.py --self-test` | **104 checks, 0 FAILED** |
| `scripts/dcs_ts_pr057_causal.py --mutate` | **85/85 RED** |
| `src/boombness/pr057_run_causal.py --self-test` | **70 checks, 0 FAILED** |
| `src/boombness/pr057_run_causal.py --mutate` | **41/41 RED** |
| `--plan --split test` | 54 arms, **30 constructible / 24 unbuildable**; both C5 arms bind `..._button_bomb.jsonl` |
| `--stage h2 --split test --dry-run --emit-probe --emit-liveness` | rc 0; "36 selected, 30 constructible, 6 unbuildable, 0 not-submitted"; "30 arm(s) constructed and validated, model NOT loaded, nothing written, nothing run" |

All four harness numbers are **identical to the pre-session baselines** (104/0, 85/85, 70/0, 41/41),
which is the expected result of a session that changed no code. The new-mutation requirement of the
task is deferred with the fix it belongs to (§E.5 item 2) — a mutation for a code path that does not
exist would be a mutation over nothing.

## E.7 — `git status --porcelain`, UNSCOPED

```
?? data/boombness_prompts/boombness_prompt_bank_ts116_basket_bomb.jsonl
?? data/boombness_prompts/boombness_prompt_bank_ts116_basket_gun.jsonl
?? data/boombness_prompts/boombness_prompt_bank_ts116_basket_knife.jsonl
?? data/boombness_prompts/boombness_prompt_bank_ts116_button_bomb.jsonl
?? data/boombness_prompts/boombness_prompt_bank_ts116_button_gun.jsonl
?? data/boombness_prompts/boombness_prompt_bank_ts116_button_knife.jsonl
?? data/boombness_prompts/boombness_prompt_bank_ts116m_basket_bomb.jsonl
?? data/boombness_prompts/boombness_prompt_bank_ts116m_basket_gun.jsonl
?? data/boombness_prompts/boombness_prompt_bank_ts116m_basket_knife.jsonl
?? data/boombness_prompts/boombness_prompt_bank_ts116m_button_bomb.jsonl
?? data/boombness_prompts/boombness_prompt_bank_ts116m_button_gun.jsonl
?? data/boombness_prompts/boombness_prompt_bank_ts116m_button_knife.jsonl
?? data/boombness_prompts/boombness_prompt_bank_ts116n_basket_bomb.jsonl
?? data/boombness_prompts/boombness_prompt_bank_ts116n_basket_gun.jsonl
?? data/boombness_prompts/boombness_prompt_bank_ts116n_basket_knife.jsonl
?? data/boombness_prompts/boombness_prompt_bank_ts116n_button_bomb.jsonl
?? data/boombness_prompts/boombness_prompt_bank_ts116n_button_gun.jsonl
?? data/boombness_prompts/boombness_prompt_bank_ts116n_button_knife.jsonl
?? data/boombness_prompts/demo_pools_116dom_ts_bomb.json
?? data/boombness_prompts/demo_pools_116dom_ts_gun.json
?? data/boombness_prompts/demo_pools_116dom_ts_knife.json
?? data/boombness_prompts/ts_cand/
?? data/boombness_prompts/ts_repair/
?? data/boombness_prompts/ts_smoke/
```

Taken **before** this appendix was appended. All 24 entries are **another writer's** untracked data
files under `data/boombness_prompts/**` and were not touched; they appear because the listing is
unscoped, which is the point of it. The only file this session modifies is this report. No `.py`
file was edited, `configs/` is byte-unchanged, and nothing was submitted or cancelled.

## E.8 — The 30 completed arms of job 869523 are untouched

No arm was renamed, no manifest entry changed, no run directory was written or removed. The two
completed button bridges still resolve under their existing ids `c5_disabled_bridge_s1` /
`c5_disabled_bridge_s2`, and the `--plan` inventory is bit-for-bit the one the frozen amendment
records (54 / 30 / 24). Nothing needs re-running as a consequence of this session.

# APPENDIX F — THE TWO ANALYZER FIXES OF APPENDIX E, IMPLEMENTED (2026-09-08, seventh session)

## F.0 — What this session did

APPENDIX E §E.5 recommended two analyzer changes and took neither. Both are implemented here, in
`scripts/dcs_ts_pr057_causal.py` only. **No frozen file was edited** (`configs/` is byte-unchanged
under `git diff`), no SLURM job was submitted or cancelled, no GPU was used, and **no outcome value,
p-value or verdict was printed, read or reported.** Everything below is structural: gate statuses,
refusals and counts.

## F.1 — FIX 1: the missing-bridge clause is SCOPED on a non-development bank, and still REFUSES on
the development bank

`build_void_clauses` returned `UNEVALUABLE` for "the disabled-hook bridge not reproducing baseline"
whenever `ctx["bridge"] is None`, and `_one_arm_report` then refused the WHOLE run on behalf of
`h2a_s1_projout_basket` / `h2a_s2_projout_basket` — two arms the preregistered fallback has already
reduced to "REPORTED O2-ONLY -- NOT ELIGIBLE FOR THE CONJUNCTIVE RULE" and whose verdict class is
already CANNOT ANSWER.

**What was added.** One helper, `_absent_null_status(pr, ctx, uneval_detail, na_detail)`, placed
beside `_clause_status`. It is a two-way switch on the arm's bank and nothing else:

* `arm.codeword == development_codeword(pr)` (`button`) → returns `UNEVALUABLE` with the original
  wording. **This is the anti-fiat half and it is the first branch on purpose**: a missing blocking
  null where the design put one is a hole, and the arms that carry the primary claim keep refusing.
* otherwise → returns `VOID_CLAUSE_NA` with the I-N2 wording already used twice in this file
  ("NOT AVAILABLE ... a STATED SCOPE LIMIT, not a passed control"), naming amendment item **A12**,
  closed on its second branch, and `design_answers.o1_baseline.deterministic_fallback` as the
  authority, and restating that the arm stays O2-only and ineligible for the conjunctive rule.

The authority is cited **by name, not read from the file**, and that is a deliberate, stated
limitation: `deterministic_fallback` lives in `configs/dcs_ts_pr060_phase9_amendment.json`, and the
analyzer loads only the PARENT prereg (`PREREG_DEFAULT`). `o1_contrast` and `_one_arm_report`
already cite the same rule the same way. Binding it would mean loading a second config in the
analyzer, which is a larger change than APPENDIX E authorised.

The bridge clause now calls the helper. **Nothing is upgraded, nothing is marked passed**, and the
clause is reported in `not_applicable`, never in `tripped` and never in `ok` by fiat.

**The knock-on that FIX 1 alone would have hidden.** Scoping the bridge clause is not sufficient on
its own: once FIX 2 (below) correctly leaves the basket arms with no C1 draws, the *other* absent
blocking null — "identical control-draw hashes" — would have gone `UNEVALUABLE` and refused the run
for the same wrong reason. That clause now takes the same two-way switch, but **only** behind an
explicit `ctx["control_scope_limited"]` flag, which is `True` only when NO C1 arm is *declared* on
the arm's bank — a constructibility fact fixed before any test read. Any *other* absent C1 band
(a load failure, an empty band, a band that failed to build) still returns `UNEVALUABLE` and still
refuses. That distinction is the whole point: this repo's "a check that reads the same broken
source" lesson is that a scope limit and a broken measurement must not share a code path.

## F.2 — FIX 2: the C1 control was silently computed ACROSS codeword banks

This was the serious one. At the old `:4143-4147`, `c1_draws` selected control draws by **scope and
hypothesis only**. Every C1 arm in `build_arm_manifest` is hardcoded `codeword="button"`, while
`base` — the untouched baseline C1 is paired against — is *this arm's own bank*. For the two basket
arms the DECISIVE control was therefore **button draws against a basket baseline**.

It could not be caught downstream. The two ts116m banks share **22272/22272 identical `prompt_id`s**
(APPENDIX E §E.4), so `paired_by_prompt`'s zero-overlap guard (M80) and its one-domain-per-prompt
guard (M82) **both pass** on a cross-bank pair. The mismatch was invisible by construction.

**What was changed, in the two places this codebase already fixes this class:**

1. **The selector.** `c1_draws` now also requires `x.codeword == arm.codeword` — the same clause
   `_bridge_for()` has always had (`same scope AND same codeword bank`).
2. **The estimator refuses by name.** `control_c1_report` gained a `member_arm: ArmSpec` parameter
   and, before it pairs anything, walks the draws and raises `Refusal` on
   `arm.codeword != member_arm.codeword` (and on a `target_concept` mismatch), naming both arms and
   both banks — modelled directly on `o1_contrast`'s M79 refusal. A future selector that forgets
   clause (1) now raises instead of silently pairing. The refusal fires *before* any pairing, so it
   is reached even on rows that would pair perfectly.
3. **The absence is STATED, not papered over.** When a basket arm is left with no C1 draws,
   `rep["C1"]` is `None`, `rep["C1_scope_note"]` records why in full, `evaluate_success`'s third
   conjunct stays FALSE (a missing control is never a passed control — the arm *cannot* satisfy the
   conjunctive rule), and the void clause is `NOT_APPLICABLE` via §F.1's flag.

## F.3 — Verification, with the numbers OBSERVED

| check | before | **observed now** |
| --- | --- | --- |
| `scripts/dcs_ts_pr057_causal.py --self-test` | 104 checks, 0 FAILED | **111 checks, 0 FAILED** |
| `scripts/dcs_ts_pr057_causal.py --mutate` | 85/85 RED | **90/90 RED** |
| `src/boombness/pr057_run_causal.py --self-test` | 70 checks, 0 FAILED | **70 checks, 0 FAILED** |
| `src/boombness/pr057_run_causal.py --mutate` | 41/41 RED | **41/41 RED** |
| `--plan --split test` | 54 arms | **54 arms, 24 live / 30 control** (unchanged) |
| h2/test analysis, arm loading | 30 arms, 0 failures | **30 arm(s) loaded, 0 check failure(s)**, 0 `[FAIL]` rows |
| `pytest tests/test_arm_report.py tests/test_bridge_bank_guard.py tests/test_donor_patch.py tests/test_control_feasibility.py` | — | **37 passed in 27.48s** |

No repo test under `tests/` references `dcs_ts_pr057_causal.py`, `pr057_run_causal.py`,
`control_c1_report` or `build_void_clauses` (`grep -rln` over `tests/` returns nothing); the four
run above are the nearest neighbours by subject and all passed to completion. The two harnesses
above ARE the test suite for this file.

**The five NEW self-test checks** (all PASS), each driving the real functions rather than a
re-implementation:

* `fixE_bridge_dev_bank_still_unevaluable` — a `button` arm with `bridge=None` keeps the clause
  `UNEVALUABLE` **and** `void_clause_report(...)["unevaluable"]` is non-empty, which is what makes
  `_one_arm_report` refuse. n=2.
* `fixE_bridge_nondev_bank_scoped_away` — the same arm on `basket` is `NOT_APPLICABLE`.
* `fixE_c1_band_dev_bank_still_unevaluable` / `fixE_c1_band_nondev_bank_scoped_away` — the same two
  halves for the control-draw-hashes clause.
* `fixE_void_report_na_is_not_ok_by_fiat` — a `NOT_APPLICABLE` clause is never counted as TRIPPED.
* `fixE_c1_cross_bank_refused_by_name` — `control_c1_report` raises on a mismatched draw.
* `fixE_every_c1_arm_is_on_the_dev_bank` — n=20; the constructibility fact the whole scope limit
  turns on is **re-derived from the manifest**, not asserted in prose.

**The five NEW mutations, all RED:**

| mutation | observed |
| --- | --- |
| `M86 dev-bank arm with NO C5 bridge scoped away` | **RED** — gate says ok=False (status is UNEVALUABLE, not NOT_APPLICABLE) |
| `M86b dev-bank arm with NO C5 bridge stops refusing` | **RED** — gate says ok=False (the unevaluable list is non-empty, so the run still refuses) |
| `M86c dev-bank arm with NO C1 band scoped away` | **RED** — gate says ok=False |
| `M87 C1 draw from ANOTHER codeword bank` | **RED** — `C1 REFUSED: arm h2a_s1_projout_basket is on the 'basket' bank and the ...` |
| `M88 cross-bank C1 that every OTHER guard allows` | **RED** — same refusal, raised on 9 rows with **identical prompt_ids and identical domains**, which `paired_by_prompt` pairs cleanly (the mutation asserts that premise: 9 shared ids, 3 domains, no M80/M81/M82 refusal). This is the mutation for the invisible half of the defect. |

M86/M86b/M86c are the anti-fiat mutations APPENDIX E §E.5 item 2 asked for, and they are RED:
**a development-bank arm with no bridge is still UNEVALUABLE and still refuses the run.**

## F.4 — The per-arm structural result on the 30 completed arms of job 869523

Read out of the analyzer's own JSON, **fields other than outcomes only**:

| arm | role | C1 | C1_scope_note | O1 | bridge clause | control-draw-hashes clause | n UNEVALUABLE |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `h2a_s1_projout_button` | development | PRESENT | — | PRESENT | CLEAR | CLEAR | 0 |
| `h2a_s2_projout_button` | development | PRESENT | — | PRESENT | CLEAR | CLEAR | 0 |
| `h2a_s1_projout_basket` | external_confirmation | **ABSENT** | yes | ABSENT | **NOT_APPLICABLE** | **NOT_APPLICABLE** | 0 |
| `h2a_s2_projout_basket` | external_confirmation | **ABSENT** | yes | ABSENT | **NOT_APPLICABLE** | **NOT_APPLICABLE** | 0 |

The two button arms are **unaffected** by both fixes: they keep a real bridge, a real O1 and a real
C1 band on their own bank. The two basket arms lose the C1 band they should never have had — before
FIX 2 they reported a C1 computed against the *other* bank — and both their absent nulls are now
recorded as stated scope limits. `REFUSING` and `Traceback` appear **0 times** in the analyzer's
output; `O1 IS NOT AVAILABLE FOR THIS ARM` and `REPORTED O2-ONLY` appear **twice each**, as they did
before.

**Is any basket arm left without a C1 control? Yes — both of them, and that is the correct and
stated outcome.** No C1 arm is declared on the basket bank (20 C1 arms, all `button`), so there is
nothing on that bank to control with, and borrowing the button draws is exactly the cross-codeword
comparison A12 refuses. It is stated in three places that a reader and a program both see:
`rep["C1_scope_note"]`, the `NOT_APPLICABLE` clause detail, and the third conjunct of
`evaluate_success`, which stays FALSE. **It is a scope limit, not a control that passed.**

## F.5 — What is now WEAKER, said plainly

The basket arms no longer contribute a C1 equivalence interval at all. Before this session they
appeared to have one; that appearance was wrong, and removing it removes evidence the phase never
actually had. Anyone reading the basket arms must now read them as: O2-only, no O1, no C1, CANNOT
ANSWER by construction, ineligible for the conjunctive rule. If the project wants O1, I-N1 and C1 on
basket, APPENDIX E §E.5's last paragraph still applies: that is a **prereg amendment first** — A12
reopened, `arm_inventory_observed` reissued — and not a code change made behind a frozen file's back.

## F.6 — `git status --porcelain`, UNSCOPED

```
 M reports/DCS_TS_PR060_AMENDMENT.md
 M scripts/dcs_ts_pr057_causal.py
?? data/boombness_prompts/boombness_prompt_bank_ts116_basket_bomb.jsonl
?? data/boombness_prompts/boombness_prompt_bank_ts116_basket_gun.jsonl
?? data/boombness_prompts/boombness_prompt_bank_ts116_basket_knife.jsonl
?? data/boombness_prompts/boombness_prompt_bank_ts116_button_bomb.jsonl
?? data/boombness_prompts/boombness_prompt_bank_ts116_button_gun.jsonl
?? data/boombness_prompts/boombness_prompt_bank_ts116_button_knife.jsonl
?? data/boombness_prompts/boombness_prompt_bank_ts116m_basket_bomb.jsonl
?? data/boombness_prompts/boombness_prompt_bank_ts116m_basket_gun.jsonl
?? data/boombness_prompts/boombness_prompt_bank_ts116m_basket_knife.jsonl
?? data/boombness_prompts/boombness_prompt_bank_ts116m_button_bomb.jsonl
?? data/boombness_prompts/boombness_prompt_bank_ts116m_button_gun.jsonl
?? data/boombness_prompts/boombness_prompt_bank_ts116m_button_knife.jsonl
?? data/boombness_prompts/boombness_prompt_bank_ts116n_basket_bomb.jsonl
?? data/boombness_prompts/boombness_prompt_bank_ts116n_basket_gun.jsonl
?? data/boombness_prompts/boombness_prompt_bank_ts116n_basket_knife.jsonl
?? data/boombness_prompts/boombness_prompt_bank_ts116n_button_bomb.jsonl
?? data/boombness_prompts/boombness_prompt_bank_ts116n_button_gun.jsonl
?? data/boombness_prompts/boombness_prompt_bank_ts116n_button_knife.jsonl
?? data/boombness_prompts/demo_pools_116dom_ts_bomb.json
?? data/boombness_prompts/demo_pools_116dom_ts_gun.json
?? data/boombness_prompts/demo_pools_116dom_ts_knife.json
?? data/boombness_prompts/ts_cand/
?? data/boombness_prompts/ts_repair/
?? data/boombness_prompts/ts_smoke/
```

Taken **before** this appendix was appended. **Exactly two files are modified**:
`scripts/dcs_ts_pr057_causal.py` (+244 / -9) and this report (whose `M` was already there when this
session started — it carries APPENDIX E, appended by the previous session and not yet committed).
`git diff --stat configs/ src/boombness/` is **empty**: both frozen configs and every shared module
(`pair_common.py`, `score_behavior.py`, `pr057_run_causal.py`) are byte-unchanged. The 24 untracked
`data/boombness_prompts/**` entries are **another writer's** files, untouched; they appear only
because the listing is unscoped, which is the point of it. Nothing was committed, added or stashed.
Analyzer scratch output was written under the session scratchpad, never under `outputs/`.
