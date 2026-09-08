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
