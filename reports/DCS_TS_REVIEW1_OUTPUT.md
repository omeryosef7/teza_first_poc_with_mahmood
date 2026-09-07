# DCS THESIS-SCALE — REVIEW 1, LENS C: OUTPUT AND PROCESS

**Reviewer lens:** mandate §29C (output and process).
**Range reviewed:** `b80db84d` (phase start) → `e4d78bf0` (HEAD at review time), 9 commits.
**Working tree at review time:** 2 tracked files modified beyond HEAD
(`scripts/dcs_ts_build_ts116n.sh`, `scripts/dcs_ts_verify_ts116n.py`), 20 untracked data paths.
**Mode:** read-only. No file outside this report was written; nothing was committed; no job submitted.
**Interpreter for all reruns:** `/home/sharifm/students/omeryosef/miniconda3/envs/poc_stage2/bin/python`.

Everything below that is stated as a number was recomputed by this review from the artifact,
not read out of the log, unless the row says otherwise.

---

## 0. HEADLINE

Six findings, in descending order of how much they could cost.

| # | severity | finding |
|---|---|---|
| **C-1** | **HIGH** | `scripts/dcs_ts_verify_ts116n.py:161` — gate **G1 `exactly-one-<concept>` is singular-only**, the exact `C-076` defect. It prints `0 sentence(s) not exactly one whole-word 'knife'` over a pool file carrying **8** such sentences. The published *"Gates G1–G3 19/19 PASS"* (`R-101`) is a green verdict produced by a gate blind to the defect `A-041` found one entry later. The generator's own verifier, on the same file, reports **8 failures**. |
| **C-2** | **HIGH** | `configs/dcs_ts_pr046.json` is `FROZEN` and pins the **ts116n** bank/pool hashes — the family `A-041` declared *"knife NOT USABLE AS BUILT"*. Every pinned harm pool **fails the generator's current verifier** (bomb 1, knife 8, gun 1 failures). The frozen preregistration is pinned to a superseded artifact. |
| **C-3** | **MEDIUM** | The four `N1` `n_examples=0` nulls (`G5_09*`, all `0.3333/0.5000`) are computed on a population that is **230/230 byte-identical across bomb/knife/gun**. Their value is pinned to 1/3 by arithmetic — the `C-074` argument verbatim. They **cannot fail**, and `A-041`'s inference *"so the signal localises entirely to the demonstration block"* does not follow from them. |
| **C-4** | **MEDIUM** | `scripts/dcs_ts116n_audit_concept_backing.py:2033` credits a mutation whenever its target is RED **after** the mutation, without requiring it to have been GREEN **before**. Three of the 21 targets (`CHK-03`, `CHK-09`, `CHK-17`) are RED at baseline, so **M03 / M09 / M17 are credited vacuously**. The published *"21/21 mutations turned their target RED"* is really **18/21 demonstrated + 3 unproven**. |
| **C-5** | **LOW** | Every phase job log prints `git=NA  dirty=0`. `git` is unavailable on `rack-ai-01`, so `git rev-parse` → `NA` and `git status --porcelain \| wc -l` → **0**. `dirty=0` reads *clean* precisely when git has failed; the tree was in fact dirty (25 porcelain lines now). Provenance is **absent**, not clean, for all 10 jobs. |
| **C-6** | **LOW** | `scripts/dcs_ts_split_manifest.py` has **no `--mutate` flag**. `R-099`'s five-mutation table is an un-committed ad-hoc run. I re-derived it (all RED), but one row does not reproduce as stated. |

**Nothing is VOID.** No job ran a script or arguments other than the intended ones. No GPU job ran.

---

## 1. SLURM JOB LEDGER — all 10 jobs of this phase

Reconstructed from `sacct -u omeryosef -S 2026-09-06T20:00` and `outputs/boombness/logs/tsharm_*`.
`scontrol` returns `Invalid job id` for all of them (purged from the live controller); `sacct` is
history-only and is the source for state/exit/elapsed, per the standing rule that liveness comes
from `squeue`/`scontrol` and never from `sacct`.

All 10 are `JobName=tsharm`, `Partition=cpu-killable`, `NodeList=rack-ai-01`,
`WorkDir=/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood`, submitted via
`src/boombness/slurm/run_ts_harm_pools.sh`. **No GPU job exists in this range** — consistent with
the phase's own claim.

| job | args (from log lines 4–9) | state | exit | elapsed | output written | §26.10 first-lines check |
|---|---|---|---|---|---|---|
| 859713 | concept=knife, out=`ts_smoke/smoke_knife.json`, seed=20260906, domains=`airport_apron` | COMPLETED | 0:0 | 00:06:06 | `sha16=50f094801d1d232b`, 1 domain | **OK** — script + all 4 env args echoed and match intent |
| 859722 | concept=bomb, out=`demo_pools_116dom_ts_bomb.json`, seed=20260906, all 116 | **FAILED** | **1:0** | 00:16:45 | `sha16=9dcaed6e32f30065`, 116 domains | **OK** |
| 859723 | concept=knife, out=`…_ts_knife.json`, seed=20260906, all 116 | COMPLETED | 0:0 | 00:15:34 | `sha16=1f164f69d2f17a9e`, 116 domains | **OK** |
| 859724 | concept=gun, out=`…_ts_gun.json`, seed=20260906, all 116 | **FAILED** | **1:0** | 00:17:08 | `sha16=a68ab2ceef4144b7`, 116 domains | **OK** |
| 859813 | concept=bomb, out=`ts_repair/rk_bomb_s20260907.json`, seed=**20260907**, domains=`restaurant_kitchen` | COMPLETED | 0:0 | 00:04:25 | `sha16=375bf804f3414082` | **OK** |
| 859814 | concept=knife, out=`ts_repair/rk_knife_s20260907.json`, seed=20260907, `restaurant_kitchen` | COMPLETED | 0:0 | 00:04:30 | `sha16=e7f42054faa69a35` | **OK** |
| 859815 | concept=gun, out=`ts_repair/rk_gun_s20260907.json`, seed=20260907, `restaurant_kitchen` | **FAILED** | **1:0** | 00:04:30 | `sha16=6a3df9b2fcefd5b7` | **OK** |
| 859978 | concept=bomb, out=`ts_cand/cand_bomb.json`, seed=20260906, all 116, **n_per_pool=60** | COMPLETED | 0:0 | 00:25:44 | `sha16=39a3fadfdd45d156` | **OK** |
| 859979 | concept=knife, out=`ts_cand/cand_knife.json`, seed=20260906, all 116, n_per_pool=60 | COMPLETED | 0:0 | 00:25:04 | `sha16=59f3c520896bea65` | **OK** |
| 859980 | concept=gun, out=`ts_cand/cand_gun.json`, seed=20260906, all 116, n_per_pool=60 | COMPLETED | 0:0 | 00:25:22 | `sha16=df61664d4c74cb3a` | **OK** |

### 1.1 How strong the §26.10 "did it run what I meant?" check actually is

`src/boombness/slurm/run_ts_harm_pools.sh:39` echoes the script name as a **hard-coded string
literal**, not as the variable that is later invoked. It happens to be correct only because
`:47` also hard-codes the same path in the same file. So the script-name line is a *duplicate
literal*, not a read-back — it could not detect a `DCS-C-047`-class divergence if one were
possible here. It is not possible here, because this wrapper has no script variable at all.

What **is** a faithful read-back, and is the load-bearing part: `TSH_CONCEPT`, `TSH_OUT`,
`TSH_SEED`, `TSH_DOMAINS`, `TSH_NPP` are echoed from the same shell variables that are passed to
`python -u` at `:47–49`. Those five are genuinely verified above. **Confirmed: 10/10 jobs ran the
intended script with the intended arguments. Zero VOID.**

### 1.2 Two wrapper versions ran, and the logs prove which

Jobs 859713–859815 print **no** `n_per_pool:` line; 859978–859980 do. `git log -p --
src/boombness/slurm/run_ts_harm_pools.sh` shows `TSH_NPP`, the `n_per_pool:` echo and
`--n-per-pool` were **all introduced at `e4d78bf0`** (HEAD); the file's only prior version is
`c6a99bbc`. So the first seven jobs ran the `c6a99bbc` wrapper (fixed 40/pool) and the last three
ran the `e4d78bf0` wrapper (60/pool). This is consistent with `C-077`'s narrative and is
*inferable from the logs alone*, which is the property §26.10 is after. **No discrepancy.**

### 1.3 C-5 — `git=NA  dirty=0` is a false clean, in all 10 logs

`run_ts_harm_pools.sh:45`:
`echo "git=$(git rev-parse HEAD 2>/dev/null || echo NA)  dirty=$(git status --porcelain 2>/dev/null | wc -l)"`

Every log prints `git=NA  dirty=0`. `git` is not usable on `rack-ai-01`, so `rev-parse` fails →
`NA`, and `git status` fails → empty stdout → `wc -l` → **0**. The same `git status --porcelain |
wc -l` on the login node right now returns **25**. So the field reports *clean* exactly in the
case where it knows nothing. This is the "a check that reads the same broken source" shape applied
to provenance: **no phase job records the commit it ran at**, and the field that would have said
so instead affirms cleanliness. Recommendation: fail the job, or print `dirty=UNKNOWN`, when
`git rev-parse` returns non-zero.

---

## 2. THE TWO `FAILED 1:0` JOBS — CONFIRMED, plus a third the log does not state

**Claim under test:** 859722 (bomb) and 859724 (gun) failed on their own *verifier* and not on
generation; their outputs were nonetheless written and are the files later used.

**CONFIRMED, on four independent pieces of evidence.**

1. **Order of operations in the source.** `scripts/dcs_ts_gen_concept_harm_pools.py:341` —
   `return verify(a.out)` — runs *after* the file has been written. `verify()` (`:245`) re-opens
   the path from disk. So a non-zero exit from this script always leaves the artifact behind.
2. **The logs match that order.** Both `.out` files end at
   `wrote data/boombness_prompts/demo_pools_116dom_ts_{bomb,gun}.json  content_sha16=…  116 domains`
   with **all 116/116 domain lines present** (`n=40` each), and neither carries the
   `[gen-harm-pools] OK:` line or `=== done ===`. Both `.err` files carry exactly one failure:
   * `tsharm_859722.err`: `FAIL restaurant_kitchen|harm: 1 sentence(s) mention the OTHER concept 'knife' (indices [39])`
   * `tsharm_859724.err`: `FAIL restaurant_kitchen|harm: 1 sentence(s) mention the OTHER concept 'knife' (indices [19])`
   followed by `[gen-harm-pools] 1 failure(s) over 348 shared and 116 harm pools`.
   Generation completed; the gate refused to certify.
3. **The files exist and carry those hashes.**
   `demo_pools_116dom_ts_bomb.json` `content_sha16 = 9dcaed6e32f30065`,
   `demo_pools_116dom_ts_gun.json` `= a68ab2ceef4144b7` — identical to the logged values.
4. **They are the files later used.** All six `ts116n` bank meta files record
   `pools_path = data/boombness_prompts/demo_pools_116dom_ts_<cc>.json` with
   `pools_sha16` ∈ {`9dcaed6e32f30065`, `1f164f69d2f17a9e`, `a68ab2ceef4144b7`}, and
   `configs/dcs_ts_pr046.json` pins the same three under `/population/pools/harm_*/content_sha16`.

**A third job also exited `FAILED 1:0` and the log's ledger does not say so.** Job **859815**
(gun, `restaurant_kitchen`, seed 20260907) failed identically —
`tsharm_859815.err`: `FAIL restaurant_kitchen|harm: 1 sentence(s) mention the OTHER concept 'knife' (indices [3])`.
`R-100`'s prose does describe the outcome (*"a second seed cleaned bomb and knife while leaving
gun contaminated again"*), and `R-101` acts on it correctly, but neither entry records **859815's
state and exit code**. Its output `ts_repair/rk_gun_s20260907.json` was written and is **not** used
by anything. Not a defect; a gap in the job ledger. **3 of 10 jobs exited FAILED 1:0, not 2.**

---

## 3. MUTATION HARNESSES — every one actually run

All four were executed by this review. Summary first, evidence after.

| harness | checks | mutations run | result | binds ≥1 object? | verdict |
|---|---|---|---|---|---|
| `scripts/dcs_ts_verify_ts116n.py --mutate` | **19/19 PASS** | 4 | **4/4 RED** | yes, each | reproduces the log; **but see 3.1 — the harness is weak and G1 is blind** |
| `scripts/dcs_ts_split_manifest.py` | 6 (all pass) | **no `--mutate` exists**; 7 re-derived here | **7/7 RED** | yes, each | falsifiable; **not re-runnable** |
| `scripts/dcs_ts116n_audit_leakage.py --mutate` | 29 (20 PASS / 9 FAIL) | 10, over 16 targets | **16/16 `PASS -> FAIL`** | yes; one mutation *is* the zero-binding test | **strongest of the four** |
| `scripts/dcs_ts116n_audit_concept_backing.py --mutate` | 21 (18 GREEN / 3 RED) | 21 | 21/21 target RED **as reported** | yes, each | **3 credited vacuously — see C-4** |

### 3.1 `dcs_ts_verify_ts116n.py` — reproduces, and has two structural weaknesses

Rerun verbatim (`--mutate`), full output reproduced:

```
[verify-ts116n] 19/19 gates pass
  RED    g1_share_knife   -> 1 gate(s) fail ['G1[knife] shared byte-identical']
  RED    g1_other_knife   -> 1 gate(s) fail ['G1[knife] no other concept']
  RED    g2_button        -> 2 gate(s) fail ['G2[button] bomb vs knife DIFFERS', 'G2[button] bomb vs gun DIFFERS']
  RED    g3_button        -> 1 gate(s) fail ['G3a[button] cell A concept-free identical']
[mutate] 4/4 mutations turned a gate RED
```

Each mutation binds a nonzero object (one pool, one sentence, 1,856 rows, one row respectively),
and each turned its *intended* gate red. So the log's `4/4 RED` is honest.

**Weakness A — the harness credits collateral damage.** `:295-299`:
```python
failed = [g for g, ok, _ in r2.rows if not ok]
red = bool(failed)
```
It never names a target and never checks the baseline was PASS. A mutation that broke an
*unrelated* gate would be scored RED. Here all four happen to hit their intended gate, so the
published number is not wrong — but the harness would not have told us if it were. Contrast
`dcs_ts116n_audit_leakage.py:952`, which requires `base["pass"] and not now["pass"]` per named
target and prints `baseline already FAIL` when it cannot.

**Weakness B — coverage.** The mutation list is
`[g1_share_knife, g1_other_knife, g2_button, g3_button]`. Never attacked:
* **`G1 exactly-one-<cc>`** — the check that C-1 shows is broken;
* **`G3b`** (both sub-checks, `fc demos+preamble identical` and `fc differs ONLY by concept noun`) — 3,680 rows of published PASS with no demonstration of falsifiability;
* all four **binding guards** (`G1 binding`, `G2 binding`, `G3a binding`, `G3b binding`);
* the `bomb` and `gun` arms of G1, and the `basket` arm of G2/G3.

Attacked: **4 of 19 gates.** The remaining 15 are asserted-pass, undemonstrated.

### 3.2 C-1 — G1 cannot detect `C-076`, and it green-lit the pool that has it

`scripts/dcs_ts_verify_ts116n.py:161`:
```python
if len(re.findall(rf"(?i)\b{re.escape(cc)}\b", s)) != 1:
```
Own-concept occurrence is counted **singular-only**. The adjacent other-concept check at `:164`
*does* allow a plural (`rf"(?i)\b{other}s?\b"`). So the gate is inflection-aware for the concept
it is not looking for and inflection-blind for the one it is.

Measured, on the exact file `PR-046` pins:

| pool file | violations under **inflection-aware** count (`knife`+`knives`) | violations under **G1's singular-only** count |
|---|---|---|
| `demo_pools_116dom_ts_bomb.json` | 0 / 4,600 | 0 |
| `demo_pools_116dom_ts_knife.json` | **8** / 4,600 | **0** |
| `demo_pools_116dom_ts_gun.json` | 0 / 4,600 | 0 |
| `demo_pools_116dom_tsm_*.json` (length-matched) | 0 / 4,600 each | 0 |
*(denominator = 115 domains × 40 sentences, `restaurant_kitchen` excluded as G1 does)*

Running the **generator's own** verifier — the one that *was* hardened for `C-076`
(`dcs_ts_gen_concept_harm_pools.py:120 _clean_strict`, `:88 CONCEPT_FORMS`) — over the same three
files at HEAD:

```
ts_bomb : 1 failure(s)  (restaurant_kitchen|harm  -- names 'knife')
ts_knife: 8 failure(s)  (blood_bank[5,26,39], care_home_store[12], cheese_dairy[26],
                         hospital_supply[2], instructional[36], physio_gym[30])
ts_gun  : 1 failure(s)  (restaurant_kitchen|harm  -- names 'knife')
tsm_*   : OK
```

**Two verifiers over one artifact disagree, and the weaker one is the one whose verdict was
published.** `R-101`'s *"Gates G1–G3: 19/19 PASS"* and *"G1 exactly one whole-word target concept
per harm sentence — 115 harm pools, **0** violations, each concept"* are both literally reproduced
by the code and both blind. The `C-076` fix landed in the **generator** and in the **audits**
(`dcs_ts_audit_leakage.py:47`, `dcs_ts116n_audit_concept_backing.py:421`,
`dcs_ts_length_match_pools.py:72` all enumerate `knives`) but **not** in the independent gate.

This is the repo's own `matcher/scope` class again, one turn later, and it is worth saying plainly
that the phase *did* catch the defect — `A-041`/`C-076` found it via a different instrument. The
finding here is narrower and still matters: **the gate that is advertised as the pre-GPU stop
(`dcs_ts_verify_ts116n.py --mutate`, named in `dcs_ts_build_ts116n.sh:79` as required before any
extraction) will pass ts116m for the same reason it passed ts116n**, so it is not the thing
standing between the phase and a contaminated extraction. Recommended one-line fix: reuse
`CONCEPT_FORMS` from `dcs_ts_gen_concept_harm_pools.py` in `g1_pools`, and add a fifth mutation
that plants `knife … knives` and asserts `G1 exactly-one-knife` goes RED.

### 3.3 `dcs_ts_split_manifest.py` — no `--mutate`; the log's table re-derived

The script exposes only `--write` / `--check` (`:183-185`). `R-099`'s five-mutation table came
from an ad-hoc run that is not committed and cannot be re-run by anyone else. I re-derived it by
importing `verify()` and corrupting an in-memory copy of the committed manifest.
Baseline: `verify()` returns **0 errors**.

| mutation | this review | log's row | agree |
|---|---|---|---|
| flip one domain's label (`sha` left stale) | **RED, 3 errors** (rebuild-mismatch, sizes 70/22/24, sha mismatch) | RED, 3 errors | **yes** |
| flip one domain's label (`sha` recomputed — isolates the rebuild check) | **RED, 2 errors** | — | new |
| wrong seed | **RED** — `20260906` → **70** domains disagree | RED, **62** domains disagree | **in kind, not in number** |
| empty assignment | **RED, 3 errors**, incl. the explicit `manifest assigns NO domains` line | RED, explicitly caught | **yes** |
| corrupted `manifest_sha16` | **RED, 1 error** | RED | **yes** |
| illegal label `trian` (`sha` recomputed) | **RED, 3 errors**; without recomputing sha: **4** | RED, 4 errors | **yes** (log did not re-sha) |
| swap one train ↔ one test domain (sizes preserved) | **RED, 1 error** | — | new; closes the gap that size-preserving tampering would leave |

**The wrong-seed row does not reproduce as written.** The log gives `62` but never names the seed
it used. `20260906` gives 70; `202609062` gives 67; `20260907` gives 64; `1` gives 62. The check is
demonstrably falsifiable either way, so nothing scientific turns on it — but a mutation table
whose inputs are not recorded is not a reproducible harness. **Every mutation binds ≥1 domain; the
empty-assignment case is the explicit zero-binding test and it fires.**

One check no mutation exercises: **`pools_sha16` drift** (`verify()`'s first branch). Not attacked
in the log's five nor plausibly in mine without editing the pools file on disk.

Worth noting positively: the sha-over-body construction means *any* body tampering trips at least
the sha check, which is why several rows show extra errors. That is belt-and-braces, not a defect,
but it does mean the log's error *counts* are not evidence that the *specific* substantive check
fired — my `resha` variants above are what isolate that, and they still go RED.

### 3.4 `dcs_ts116n_audit_leakage.py --mutate` — 16/16, and it is the model harness

Rerun in full (≈8 min). Baseline **29 checks, 20 PASS / 9 FAIL**; the 9 are 4 structural
(`G5_01`, `G5_01_knife`, `G5_01d`, `G5_08` — the `C-076` and cross-domain-sentence findings) and 5
tagged `MEASUREMENT (may be RED by design)`. Mutation harness output, all 16 transitions:

```
inject_concept_word      G5_01_bomb_primary_channel_zero_concept_word   PASS -> FAIL
                         G5_01_gun_primary_channel_zero_concept_word    PASS -> FAIL
                         G5_05_probe_mask_gap_is_zero                   PASS -> FAIL
length_leak              G5_10b_cellA_control_length_at_chance          PASS -> FAIL
template_leak            G5_06_N6_templateid_at_chance                  PASS -> FAIL
                         G5_06b_N6_templateid_all_cellC_at_chance       PASS -> FAIL
corrupt_split            G5_07_domain_grouping_disjoint                 PASS -> FAIL
empty_population         G5_00_excluded_domain_absent_and_pop_is_115    PASS -> FAIL
                         G5_06_N6_templateid_at_chance                  PASS -> FAIL
                         G5_08b_sentence_leakage_is_not_wholesale       PASS -> FAIL
                         G5_10_cellA_control_text_at_chance             PASS -> FAIL
break_codeword_control   G5_11_codeword_positive_control_detects_signal PASS -> FAIL
unmask_cellB             G5_13_masker_deletes_every_printed_concept_word PASS -> FAIL
hedge_leak               G5_10c_cellA_control_hedge_register_at_chance  PASS -> FAIL
plant_shared_sentence    G5_08b_sentence_leakage_is_not_wholesale       PASS -> FAIL
reintroduce_excluded_dom G5_00_excluded_domain_absent_and_pop_is_115    PASS -> FAIL
```

**16/16 RED, every one a genuine `PASS -> FAIL` transition against a named target.** This harness
does the three things the other three do not: it names a target per mutation, it distinguishes
`baseline already FAIL` from `RED as required`, and `Checks.record` (`:132-136`) forces
`n_bound <= 0` to FAIL with the text `BOUND ZERO ROWS (vacuous check)`. `empty_population` is an
explicit zero-binding attack and it fires on four checks.

**Coverage gap.** `MUTATION_TARGETS` (`:913-931`) names **13 distinct** of the 29 checks. Of the
20 currently-PASSING checks, **7 are never attacked**:
`G5_bank_rows_sha16_matches_preregistration`, `G5_01b_recount_matches_producer_field`,
`G5_09_N1_n0_tfidf_at_chance`, `G5_09b`, `G5_09c`, `G5_09d`, `G5_12_leak_detector_finds_a_real_text_leak`.
Four of those seven are the `N1` nulls — and §4 below shows they cannot fail at all.

### 3.5 `dcs_ts116n_audit_concept_backing.py --mutate` — 21/21 reported, 18/21 demonstrated

Rerun in full with `--out` redirected to scratch (the committed report was **not** touched).
Baseline reproduces exactly: **21 checks, 18 GREEN, 3 RED** — `CHK-03` (16 leaking sentences over
90 of 33,120 cell-C rows), `CHK-09` (0 byte-identical shared, 3 shared-modulo-noun), `CHK-17`
(12 deviations). Report: `21/21 mutations turned their target RED`.

`Auditor.add` (`:305-311`) is correct on zero-binding: `bound <= 0` forces `RED` with
`BOUND ZERO OBJECTS (…) -- a check that cannot fail`. `M07` and `M16` are explicit zero-binding
attacks and both fire. Every one of the 21 mutations binds ≥1 object.

**C-4.** The acceptance test is `:2033`:
```python
if target not in red_ids:
    print(f"    !! {mid} did NOT turn {target} RED", …)
```
It asks only whether the target is RED *after*. It never asks whether it was GREEN *before*.
`M03 → CHK-03`, `M09 → CHK-09`, `M17 → CHK-17` all target checks that are **already RED at
baseline**, so those three rows are satisfied by doing nothing. The report's own table exposes the
raw material (the three ids recur in the "other checks also RED" column of nearly every row) but
its verdict column still reads `YES`. **The defensible statement is 18/21 demonstrated, 3
undetermined**, and the three undetermined ones happen to be the audit's live findings — precisely
where you would want the falsifiability demonstrated on a clean baseline. Fix: run each mutation's
target against a baseline where that target is GREEN, or report `baseline already RED` in the
table as the leakage harness does.

---

## 4. CHECKS THAT CANNOT FAIL

The four classes asked for: self-comparison, empty collections, producer-field asserts, and
arithmetic pinning.

**Empty collections — clean, in all four scripts.** Every one has an explicit zero-binding guard
and every guard was observed to fire:
`Checks.record` (`leakage:132`), `Auditor.add` (`concept_backing:305`),
`G1 binding` / `G2 binding` / `G3a binding` / `G3b binding` (`verify_ts116n:154, 205, 240, 260`),
`if not got:` (`split_manifest:172`), and the generator's
`n_shared_checked == 0` / `n_harm_checked == 0` (`gen_concept_harm_pools:294-297`). **No
pass-over-the-empty-set survives in this phase's code.** That is a real improvement over the four
harnesses `C-071` had to repair.

**C-3 — arithmetic pinning: the four `N1` `n_examples=0` nulls cannot fail.** This is the one
serious instance.

`A-041` reports and this review reproduces:
`N1a_n0_tfidf`, `N1b_n0_length`, `N1c_n0_hedge_register`, `N1d_n0_templateid` = **exactly
`0.3333 / 0.5000`, z = 0.00**, on `n_tr=828 / n_te=276`. `A-041` reads this as
*"so the signal localises entirely to the demonstration block."*

Measured on the artifact, over cell C × `semantic_one_word`, `restaurant_kitchen` excluded:

| dose | rows (per codeword) | byte-identical across bomb ∧ knife ∧ gun |
|---|---|---|
| `n_examples=0` | 230 | **230 / 230 = 100 %** |
| `n_examples=4` | 1,150 | 0 / 1,150 |
| `n_examples=8` | 460 | 0 / 460 |

The `N1` population is **the same bytes under three different labels**. A hidden state — or a
TF-IDF vector, or a character count — is a deterministic function of its text, so the Bayes-optimal
accuracy there is **exactly 1/3 and nothing else is reachable**. This is `C-074`'s argument applied
to the null instead of to the primary. The four checks are therefore *tautologies about the bank
construction*, not evidence about where signal lives; a value other than 0.3333 would indicate a
label-leaking pipeline bug and nothing more. They are legitimate as a pipeline smoke test and
should be labelled as one. **The inference `A-041` draws from them is not supported by them.**
(The genuinely informative n=0 evidence would be a dose-response on `n_ex` ∈ {4, 8}, where the arms
do differ, or the `n_ex=0` **hidden-state** probe once extraction exists.)

Mitigating: this is exactly what `R-098` itself said the n=0 rows are for — *"the sharpest
available test of the corpus confound: a probe that separates concepts there is reading nothing
but its own labels."* The defect is that `A-041` then re-used the same rows for a *localisation*
claim. Also mitigating: none of the four is mutation-tested (§3.4), so nothing asserts they *can*
fail.

**Producer-written summary fields, asserted rather than re-derived — three instances, all minor:**

1. `scripts/dcs_ts_build_ts116n.sh:74` reads `n_alignment_violations` straight out of
   `_meta.json['stats']` and asserts `== 0`. That field is written by the same
   `prompt_families` run that wrote the rows. The adjacent `bank_rows_sha16` check *is* a genuine
   re-derivation (rows on disk → `common.rows_sha16`), so row tampering is caught; but a producer
   that mis-computed alignment at build time is not. Low severity — `dcs_ts_verify_ts116n.py` G2/G3
   independently re-derive alignment from raw rows.
2. `G5_01b_recount_matches_producer_field` (`leakage:594`) compares an independent regex recount
   against the producer's `n_concept_occurrences` — `0/132,480` disagreements. This is the
   `C-075` shape *by design*, and the script's docstring is explicit that this is why check J /
   `G5_01` exist alongside it. Reported for completeness, not as a defect: it is one of the 7
   never-mutated checks (§3.4), so its ability to fail is asserted rather than shown.
3. `G5_05_probe_mask_gap_is_zero` requires `abs(unmasked_acc − masked_acc) < 1e-12` and passes at
   `0.8725 − 0.8725 = 0.0000`. Accuracy is a coarse, tie-prone statistic: two materially different
   classifiers can score identically on 1,380 rows. "Gap is zero" therefore evidences *a tie*, not
   *a no-op*. It is mutation-tested (goes RED under `inject_concept_word`), so it is not vacuous —
   but the wording in the check's own detail string overstates what it establishes.

**Comparisons of a field against itself — none found** in the four scripts under review.

---

## 5. LOG vs ARTIFACT — twenty load-bearing numbers, independently recomputed

Source of truth for the "log value" column:
`external_md/DCS_THESIS_SCALE_BOMBNESS_CAUSAL_CONFIRMATION_PLAN_AND_PROGRESS_20260906.md`.
Every "my value" was computed by this review from the artifacts named.

| # | claim (log entry) | log value | my value | agree |
|---|---|---|---|---|
| 1 | `ts116` cell C × `semantic_one_word` identical across bomb∧knife∧gun (`C-074`) | 1,856 / 1,856 | **1,856 / 1,856** | **yes** |
| 2 | `ts116` whole bank identical per codeword (`C-074`) | 7,424 / 22,272 = 33.3 % | **7,424 / 22,272 = 33.33 %** | **yes** |
| 3 | `ts116` cell C all channels identical (`C-074`) | 3,712 / 5,568 = 66.7 % | **3,712 / 5,568** | **yes** |
| 4 | **G2** — `ts116n` cell C × `semantic_one_word` DIFFERS, per domain (`R-101`) | 115 / 115, both codewords, knife and gun, 1,840 rows each | **115/115 button-knife, 115/115 button-gun, 115/115 basket-knife, 115/115 basket-gun, 1,840 rows each** | **yes** |
| 5 | **G3a** — cell A concept-free channels byte-identical (`R-101`) | 3,680 / 3,680, both codewords | **3,680 / 3,680 button and basket** | **yes** |
| 6 | **G3b** — forced-choice demos+preamble identical; query restores under `concept→bomb` (`R-101`) | 1,840 / 1,840 each | **1,840 / 1,840 each, both codewords** | **yes** |
| 7 | `ts116n` gates + mutations (`R-101`) | 19/19 PASS, 4/4 RED | **19/19 PASS, 4/4 RED** | **yes** (but see C-1: G1 is blind) |
| 8 | **N4 length-only** (`C-077`) | 0.4174 acc / 0.5750 AUROC, z = +6.62 | **0.4174 / 0.5750, z = 6.62**, `n_te=1380`; cell-A control 0.3333/0.5000 | **yes** |
| 9 | **N5c** concept-masked TF-IDF over demo block (`C-078`) | 0.8870 / 0.9829 | **0.8870 / 0.9829**, and the audit names it `THE PROBE MUST BEAT` | **yes** |
| 10 | **tier-1 explosive predicates** bomb/knife/gun (`A-041`) | 4.07 % / 0.00 % / 0.09 % | **374 / 9,200 = 4.07 %; 0 / 9,200 = 0.00 %; 8 / 9,200 = 0.09 %** | **yes** |
| 11 | 3×3 affordance matrix diagonal, largest off-diagonals (`A-041`) | 374 / 520 / 282; off-diag 2, 6, 8 | **374 / 520 / 282; off-diag 2, 6, 8** | **yes** |
| 12 | **`C-076` blast radius** (`A-041`) | 8 sentences, 30 / 3,680 primary rows, 6 domains, 3 train / 1 val / 2 test | **8 sentences; 30 / 3,680; 6 domains (`blood_bank`, `care_home_store`, `cheese_dairy`, `hospital_supply`, `instructional`, `physio_gym`); 3 train / 1 validation / 2 test**; bomb 0/3,680, gun 0/3,680 | **yes, exactly** |
| 13 | **N6 template-id-only** (`A-041`) | 0.3333 / 0.5000, z = 0.00 → run not VOID | **0.3333 / 0.5000, z = 0.00** on both `N6a` (n=1,380) and `N6b` (n=6,624) | **yes** |
| 14 | cross-domain verbatim sentence leakage (`A-041`) | 8 / 1,380 = 0.58 %, down from 72 / 3,864 = 1.86 % | **8 / 1,380**, 8 distinct sentences of 5,518 distinct test-domain sentences | **yes** |
| 15 | register baselines (`A-041`) | hedge 0.4768/0.6350; register 0.4406/0.6277; combined 0.5174/0.7159 | **0.4768/0.6350; 0.4406/0.6277; 0.5174/0.7159** | **yes** |
| 16 | population after exclusion (`R-101`) | 115 domains, 69 / 23 / 23 | **manifest 116 = 70/23/23; `restaurant_kitchen` ∈ train ⇒ 115 = 69/23/23** | **yes** |
| 17 | six `ts116n` `bank_rows_sha16` and `bank_file_sha16` (`R-101`) | table of 12 hashes | **all 12 reproduce byte-for-byte** (`common.rows_sha16` over `(prompt_id, prompt_sha16)`; `sha256(file)[:16]`); 22,272 rows each; `stats.n_alignment_violations = 0`, `n_duplicate_prompt_id_rows_dropped = 0` in all six | **yes** |
| 18 | `manifest_sha16`, `pools_sha16` (`R-099`, `R-098`) | `be7d2c772d814ef3`, `976aa2b0b617118d` | **`be7d2c772d814ef3`, `976aa2b0b617118d`**; harm pools `9dcaed6e32f30065` / `1f164f69d2f17a9e` / `a68ab2ceef4144b7` all reproduce | **yes** |
| 19 | leakage audit scale (`A-041`) | 29 checks, 16/16 mutation targets RED | **29 checks (20 PASS / 9 FAIL), 16/16 `PASS -> FAIL`** | **yes** |
| 20 | concept-backing audit scale (`A-041`) | 21 checks, 21 mutations, 21/21 RED | **21 checks (18 GREEN / 3 RED), 21 mutations, 21/21 target-RED as the harness scores it** — but **18/21** on a baseline-GREEN criterion (C-4) | **yes as reported; overstated as evidence** |
| 21 | `R-099` mutation "wrong seed → 62 domains disagree" | 62 | **70** with seed `20260906`; 67 / 64 / 62 with `202609062` / `20260907` / `1`. Seed not recorded in the log | **no — unreproducible as stated** |

**20 of 21 agree, 19 of them exactly. The one disagreement (#21) is a documentation gap in an
ad-hoc mutation table, not a scientific claim.** No number in the log was found to be inflated in
the phase's own favour; #12, #10 and #17 in particular are reported against the phase's interest
and are exact.

---

## 6. COMPLETENESS — is anything the log claims to exist missing from disk?

**Nothing claimed is missing.** All 14 artifacts named across `A-034` … `C-078` are present:

| artifact | bytes |
|---|---|
| `reports/DCS_TS_PHASE1_BRIEFING_20260906.md` | 262,659 |
| `reports/DCS_TS_LITERATURE_UPDATE_20260906.md` | 26,558 |
| `reports/DCS_TS_TOKEN_ROLE_MAP.md` | 15,359 |
| `reports/DCS_TS_CONCEPT_BACKING_AUDIT.md` | 334,710 *(log says "334 KB" — exact)* |
| `reports/DCS_TS_LEAKAGE_AUDIT.md` | 21,369 |
| `reports/DCS_TS_POWER_ANALYSIS.md` | 33,138 |
| `reports/DCS_TS_ADVERSARIAL_AUDIT_BANK.md` | 22,636 |
| `reports/DCS_TS116N_CONCEPT_BACKING_AUDIT.md` | 213,378 |
| `reports/DCS_TS116N_LEAKAGE_AUDIT.md` | 27,095 |
| `reports/DCS_TS116N_ADVERSARIAL_AUDIT.md` | 36,681 |
| `outputs/dcs_ts/token_roles_ts116.json.gz` | 4,401,864 *(log says "4.4 MB" — exact)* |
| `outputs/dcs_ts/ts116_sidecar.jsonl.gz` | 21,313,085 |
| `configs/dcs_ts_pr046.json` | present, `status = FROZEN`, all 17 `*_sha16` fields non-null |
| 6 × `ts116n` bank `.jsonl` + `_meta.json`, 6 × `ts116` | present, all hashes verified (§5 #17) |

Five things that are **not** claimed missing but that a reader of the log would reasonably expect
and should know the status of:

1. **C-2 — `PR-046` is frozen against a superseded bank.** `configs/dcs_ts_pr046.json` pins the
   three `ts116n` harm pools and six `ts116n` banks. Those three pools **fail the generator's own
   current verifier** (§3.2: 1 / 8 / 1 failures) and `A-041` records `knife NOT USABLE AS BUILT`.
   The replacement pools `demo_pools_116dom_tsm_{bomb,knife,gun}.json` **exist on disk**
   (`content_sha16` = `e561c812ee355c73` / `27eaf6a76f6d0526` / `50ba5d1fbeb5764f`) and pass that
   verifier cleanly, but **no `ts116m` bank has been built** — `ls data/boombness_prompts/` shows
   `ts116` and `ts116n` only. So the frozen preregistration currently points at an artifact the
   phase has already superseded, and re-pinning a `FROZEN` config is exactly the move the phase's
   own §21 discipline exists to make visible. This should be a `C-xxx` entry with an explicit
   statement of what re-pinning a frozen config does and does not permit, **before** the ts116m
   banks are built — not after.
2. **Uncommitted in-flight work.** `scripts/dcs_ts_build_ts116n.sh` and
   `scripts/dcs_ts_verify_ts116n.py` are modified beyond `e4d78bf0`, adding
   `POOLS_TAG` / `BANK_TAG` env selection so one recipe serves both families. Good direction. Note
   that `scripts/dcs_ts116n_audit_leakage.py:58` already reads `BANK_TAG`, but
   **`scripts/dcs_ts116n_audit_concept_backing.py:326` hard-codes `ts116n`** in `bank_path` — so
   G4 cannot be re-run on ts116m without an edit, while G5 can. Asymmetry worth closing in the same
   pass. Also: `G5_bank_rows_sha16_matches_preregistration` compares against `PR-046`'s pinned
   ts116n hashes, so running G5 with `BANK_TAG=ts116m` will make that check FAIL for a benign
   reason unless it is re-pinned first — which is C-2 again, arriving as an operational error.
3. **A-036's read site was derived on `ts116`, not `ts116n`.** `outputs/dcs_ts/token_roles_ts116.json.gz`
   and `reports/DCS_TS_TOKEN_ROLE_MAP.md` nominate `pos = len(input_ids) − 9` from 6,960 `ts116`
   prompts, and report `prompt length 196–280 tokens` and `only position −10 varies over the last
   28` on that family. `ts116n`'s demonstration text is different by construction, so those
   distributions are not inherited. The tail is the query and is very likely unchanged — but the
   log does not say the map must be re-derived, and it does not list that among the "still required
   before extraction" items. **UNKNOWN whether it holds on `ts116n`; re-running
   `scripts/dcs_ts_token_roles.py` against the new banks is CPU-only and would close it.** Same
   applies to `outputs/dcs_ts/ts116_sidecar.jsonl.gz`.
4. **`restaurant_kitchen`'s exclusion rationale no longer holds on the new candidate pools.**
   `dcs_ts_verify_ts116n.py:56-70` justifies the exclusion as *"that is the domain, not the draw"* —
   two seeds failed to produce a clean gun pool for it. On the length-matched `tsm_*` pools,
   **all 116 domains including `restaurant_kitchen` pass the generator's verifier cleanly**
   (§3.2). The exclusion is preregistered, prompt-only, outcome-blind, and sits in TRAIN, so
   keeping it costs nothing and reversing it would be a post-hoc population change — **keep it**.
   But the *stated reason* is now falsified by the artifact, and the write-up should say the
   exclusion is retained for preregistration discipline rather than because the domain is
   irreparable.
5. **`R-100`'s job ledger omits 859813/814/815's states**, and 859815's `FAILED 1:0` is nowhere
   recorded (§2). Cosmetic, but this phase's whole method is that the ledger is reconstructable
   from the log alone.

---

## 7. WHAT THIS LENS WOULD BLOCK, AND WHAT IT WOULD NOT

**Would not block.** The data foundation is sound and the numbers are honest. Twenty of twenty-one
load-bearing figures reproduce, nineteen exactly, including three (`C-076`'s 30/3,680, tier-1
`4.07/0.00/0.09`, the six bank hashes) that cut against the phase's own convenience. No job ran the
wrong thing. No pass-over-the-empty-set survives anywhere in this phase's code. The `C-074`
correction is real and `G2`'s 115/115 against `G3a`'s 3,680/3,680 is a genuine matched pair.

**Would block, before the ts116m banks are built and before the first GPU job:**

1. **C-1.** Fix `dcs_ts_verify_ts116n.py`'s G1 to count inflections, and add the mutation that
   proves it. As it stands the pre-extraction gate named in `dcs_ts_build_ts116n.sh:79` would
   green-light a `C-076`-contaminated ts116m exactly as it green-lit ts116n.
2. **C-2.** Decide and record, in a `C-xxx`, what happens to a `FROZEN` `PR-046` when the bank it
   pins is superseded. Re-pinning silently is the failure mode; a `PR-047` that supersedes it, or
   an explicit amendment entry, is not.
3. **C-3.** Relabel the four `N1` `n_ex=0` nulls as pipeline smoke tests and withdraw the
   localisation inference drawn from them.
4. **C-4.** Re-score the concept-backing mutation table against a baseline-GREEN criterion and
   publish `18/21 demonstrated, 3 baseline-already-RED`.
5. **C-5.** Make the wrapper refuse, or print `dirty=UNKNOWN`, when `git rev-parse` fails.
6. **C-6.** Give `dcs_ts_split_manifest.py` a `--mutate` flag carrying the seven mutations of §3.3,
   with the seeds recorded.

None of these six is a reason to distrust a published number. All six are reasons the *next*
number could go wrong the same way the last one did.

---

*Written read-only at HEAD `e4d78bf0`. Reruns of `dcs_ts_verify_ts116n.py`,
`dcs_ts116n_audit_leakage.py`, `dcs_ts116n_audit_concept_backing.py` and
`dcs_ts_gen_concept_harm_pools.py --verify` were executed with outputs redirected to a scratch
directory; no committed report or artifact was modified. Concurrent activity observed in the tree
during the review: another session running `dcs_ts116n_audit_leakage.py` against `ts116m`.*
