# ADVERSARIAL REVIEW #4: read-readiness for the P2b TRAIN read and the S-084 read (2026-10-14)

Independent and read-only. No existing file was modified, nothing was committed and no SLURM job was submitted.
I did not compute or view any y_install, logp or recovery value from `hcsi_p2b_*_k4_*`, `hcsi_p2b_*_val_*`, P4
or the r4ext dirs. From production dirs I read only directory names, `DONE.json`, `RUNMETA.json`, `config.json`
args, `p2b_operator.json` operator-provenance fields (factors sha, rank, hook_calls) and log GPU lines.
Scratch scripts are in `.../scratchpad/review4/`: `p2b_dryrun.py` and `s084_dryrun.py`.

## Summary (severity-ranked)

| # | Sev | Area | Finding | Fix |
|---|---|---|---|---|
| 1 | **HIGH (process)** | both reads | **No frozen analysis invocation exists for the P2b TRAIN read.** A grep of configs/external_md/research/reports/plans finds only the VALIDATION command (`PREREG_P2B_VALIDATION.analysis_command`), and that command **omits `--addon`**, although A3/A4 route the MEANBIAS comparators and the wording-eligibility flag through `--addon`. The S-084 analyzer `research/heretic_csi/p2a_powered_analyze.py` is **untracked in git** (`??`, mtime 11:40, after job 1027577 had started). Its logic matches the prereg (see §2), but it is not frozen. | Before either read, commit (a) `p2a_powered_analyze.py` and (b) one command line per (cw, split) for P2b. Suggested TRAIN form: `--prefix hcsi_p2b_<cw>_k4 --split train --expect-n 268 --ranks 1,4 --nrand 61 --nshuf 5 --nder 15 --capop --cw-nrand 61 --cw-nder 15 [--addon] --out reports/heretic_csi/p2b_<cw>_primary_train.json`. Record their sha256 in the log. |
| 2 | MEDIUM | P2b A3/A4 | **The add-on arms have not been run.** There is no `KO_MEANBIAS`, `KO_CWMEANBIAS`, `BASE_MEANBIAS` or `*RAW*` dir, and no `argv_addon_*`. The add-on jobs (~11.8 GPU-h) appear never to have been submitted. A TRAIN read with `--addon` now returns `addon: NOT ANALYZABLE` (tested). The primary verdict is unaffected, but under A3 any TRAIN or VAL PASS must then be worded only as "writing ≈ the mean KO→clean shift undoes part of the knockout". | Submit `addon_<cw>_{k4,val}` now. State in the read entry that the wording stays minimal until the add-on is analysed. |
| 3 | MEDIUM | P6 consistency | **P6's primary outcome is still the pooled z over 46 RAND + 10 SHUF** (`PREREG_P6.primary_outcome_per_codeword`; neither amendment mentions SHUF). S-097/S-098 established that z over this mixed family is control-family-dependent (basket r1 z: RAND 8.74, SHUF 3.94, pooled 6.68; I flips sign). H6a, the single confirmatory P6 test, is a Spearman on exactly this z. | Before any Stage-0 number, freeze P6 A3: either SHUF-only or RAND-only z as primary, or pooled z with RAND-only/SHUF-only sensitivity where a decision flip ⇒ "family-sensitive". |
| 4 | MEDIUM | P2b consistency | **The outcome mapping was never re-stated after A1.** The base prereg defines `min_sufficient_rank` and outcomes A–E over ranks {1,2,4,8,16,32,50}. A1 made only {1,4} confirmatory. No dir exists for r2/8/16/32/50, and the evalB/evalC plans have not run. The prereg also does not say which split decides A–E, or what happens with TRAIN FAIL + VAL PASS. VALIDATION says it "certifies or fails the TRAIN verdicts" and "a claim needs PASS on VALIDATION". | Freeze one sentence: A–E are decided on VALIDATION, min rank ∈ {1, 4, ">4 / none"}; TRAIN-FAIL + VAL-PASS ⇒ report both, claim = VAL; descriptive ranks are mandate §9 curve only. |
| 5 | LOW-MED | `p2b_analyze.py:306-308` | **`input_conditional_wording_eligible_on_this_split` = True on TRAIN** in the synthetic baseline. A4 says eligibility exists only on VALIDATION. The key name hedges this, but a reader of the TRAIN JSON sees "eligible: true". | `... and a.split == "validation"`, or emit `null` on TRAIN. |
| 6 | LOW | `p2b_analyze.py:174-186` | The preregistered "hooks fired" gate is **not checked for `KO_CAND_r` or `KO_IDENT`**. Synthetic `hook_calls=0` on both CANDs ⇒ PASS. A dead CAND cannot win the rank test, but a dead KO_IDENT makes the identity gate vacuous. | Add `cand` and `KO_IDENT` to the hook check (VOID primary / shared). |
| 7 | LOW | `p2b_analyze.py` | (a) There is no bank/exclusion-file/codeword consistency VOID, which the frozen subspace analyzer has (`:618-628`). `--codeword` is unused, so `--codeword button --prefix hcsi_p2b_basket_k4` would silently mislabel. The real dirs are clean (below). (b) `run_dirs` records only the 91 main arms, not the 76 CW or 43 add-on dirs used. (c) A non-SystemExit inside the add-on block (e.g. ZeroDivision) crashes the whole read, primary included. | Add the bank/excl/codeword VOID. Record `run_dirs_secondary` / `run_dirs_addon`. Catch `Exception` in the add-on block. |
| 8 | LOW | P2b provenance | The r4 jobs (1023508/09, VAL 1023579) and the add-on jobs reuse BASE/KO/KO_FULL/KO_IDENT from the r1 jobs. No overlap or bit-exact check is made, unlike the S-084 A1 standard. The rank test is invariant to a KO offset (all r-arms share KO), but the recovery CI is not. All jobs ran on A5000 (logs), and S-108 showed cross-job bit-exactness. | Optional: re-run `KO` once inside the add-on job as an overlap arm (`OVL_KO`) and require \|Δy\| ≤ 1e-6. |
| 9 | LOW | `p2a_powered_analyze.py:88-92` | Ranks and beat-every-SHUF use the analyzer's **5-dp-rounded** values, not its own unrounded `candidate_rank_among_controls`. This is conservative only (ties count against CAND). The 203-row deviation is reported, but **the responsible controls are not named**, which A1 requires. | Assert computed rank == `verdict_basis.candidate_rank`. List arms with `arm_meta[x].n_rows < 230`. |
| 10 | LOW | carry-overs from review #3 | Still open: P4 v2 checks only the factors **basename**, not `factors_sha16`/module_fro (#12). INCOMPLETE verdict strings still embed "PASS" (#13; e.g. `INCOMPLETE FAMILY (...): PASS (Holm p=…)`). H6a probe ρ and z share VALIDATION domains (#10, second half). P6 H6c reads r1 then r4 on VAL without Holm, while S-084 exists precisely to correct sequential VAL looks. H6c is descriptive, but it is the P6 test of "basket 1 vs button 4". | Fix the sha check. Prefix the INCOMPLETE strings so that `startswith("PASS")` is the only tally rule. Add one line on H6c multiplicity. |
| 11 | LOW | overclaims | No HIGH overclaim in S-097…S-109. S-100: "FULLO and MLP-only close more of the gap in every cell" is true (JSON: MLP 0.604/0.639/0.674/0.687 vs TOP8) but lacks the prereg's own **norm/param confound** caveat (FULLO = 32 heads, MLP different module), and it rests on 6–8 of 60 in-sample controls. S-098: "basket r1 strongly specific … at r4 both above controls" uses z against **n=10 SHUF** with no CI. | Add "(norm/param-confounded, in-sample, partial)" and "(descriptive; SHUF n=10)". |

## 1. P2b analysis readiness: synthetic end-to-end dry-run with real I/O

**Setup.** I imported `p2b_analyze` unchanged and pointed `rederive.SCORE_DIR` at a scratch dir. The real
`strict_run_dir`, `lpm.load_installation` (with its loader-equality assert), `reference_key_set`, `row_fields`,
`sidecar`, `effect_fraction`, Holm, `decide` and `finalize` all ran through `main()` with the CLI flags above.

- **Arm names** come from running the real `p2b_emit.py` (liveness + rank 1 + rank 4 + addon; 373 arms). The rank
  and liveness part, 330 arms, matches the real argv files `argv_eval_basket_{1,4}_*` exactly. The only differences
  are the 43 add-on arms, which have not been run. The real dirs match the argv families: per rank, 61 RAND,
  5 SHUF, 15 DER, 61 CWRAND, 15 CWDER, and one each of CAND, BASE_CAND, CWONLY, ATLAST, NEUT and CAPOP, plus 4
  liveness arms. The TRAIN CW families are still filling: basket CWRAND 37/38 of 61, CWDER 0. **No arm-name
  mismatch** exists between the plans, the emitter and the analyzer.
- **Decoys** were planted in every scenario:
  - for the same tag: an incomplete duplicate (no DONE), a `FAILED` duplicate and a short duplicate;
  - under other prefixes: `hcsi_p2b_smoke3_basket_*`, `hcsi_p2b_basket_val_*`, `hcsi_p2b_button_k4_*`, and the
    siblings `<prefix>_KO_CAND_r1_x` and `<prefix>X_*`.

  All 16 scenarios picked exactly the intended dir, with 0 wrong `run_dirs`. A second complete dir for the same
  tag ⇒ that rank is NOT ANALYZABLE ⇒ the other rank becomes INCOMPLETE (correct, loud).

**Scenario results** (all as preregistered unless marked):

| scenario | primary | secondary | addon |
|---|---|---|---|
| baseline (CAND rank 1/82 both ranks) | PASS both, Holm 2/82 = 0.0244 | PASS both, Holm 2/77 = 0.026, 76 controls | eligible **True on TRAIN** (#5) |
| r1 CAND collapsed | r1 VOID; r4 INCOMPLETE (Holm 2×p4) | unaffected (A3) | – |
| KO_IDENT ≠ KO | VOID both (shared) | VOID both (A3/A4) | – |
| CAPOP ≠ CAND | primary VOID only | unaffected | – |
| duplicate complete RAND_r4_7 | r4 NOT ANALYZABLE; r1 INCOMPLETE | r1 INCOMPLETE | – |
| one CWRAND missing (r1) | PASS | r1 VOID; r4 INCOMPLETE | – |
| DER control wrong rank | r1 VOID; r4 INCOMPLETE | unaffected | – |
| CWDER wrong norm (r4) | PASS | r4 VOID; r1 INCOMPLETE | – |
| CWONLY collapsed (r4) | PASS | r4 VOID; r1 INCOMPLETE | – |
| KO_FULL missing | both NOT ANALYZABLE | – | – |
| **CAND / KO_IDENT hooks = 0** | **PASS (no VOID)** (#6) | PASS | – |
| add-on not run | primary unaffected | – | NOT ANALYZABLE |
| KO_MEANBIAS collapsed | – | – | void listed, eligible False |
| BASE_MEANBIAS hooks = 0 | – | – | void listed, eligible False (conservative) |

- **Holm/INCOMPLETE/VOID** behaviour matches A3 and A4 (p=1 and m=2 for an invalid rank; a shared VOID
  invalidates both families).
- **CI rule:** `decide` requires CI-lo > 0 and refuses a recovery that has no CI.
- **No VAL dirs enter a TRAIN read.** Selection is by an anchored per-prefix regex plus a split filter on keys. A
  prefix/split mismatch (e.g. `_val` with `--split train`) crashes loudly with empty keys; it never mixes splits.

**Production provenance** (metadata only):

- Every DONE dir is `status ok`, with rows_written 268 (k4) or 230 (val) and n_rows_failed 0. The
  basket/button k4 and basket val dirs use one exclusion file and one bank per prefix, with the codeword matching.
- Every sidecar's `factors_sha16` is constant per (prefix, rank). The TRAIN r1/r4 shas equal the VAL r1/r4 shas
  equal the current `fac/` files (9c2d…/96e3… basket, 7a5b…/9406… button), and equal `val_factors_sha_*.txt`. No
  cross-codeword or cross-rank factors file was found.
- All P2b jobs ran on RTX A5000.

## 2. S-084 powered re-test readiness (`p2a_powered_analyze.py`, untracked)

Run dirs by job (from RUNMETA/config only):

- **1022698:** 61 arms = BASE, KO, KO_SELF, KO_FULL, KO_CAND_r4, RAND 0–45, SHUF 0–9.
- **1027577:** OVL_BASE, OVL_KO, OVL_CAND_r4 and OVL_RAND_r4_0 plus RAND from 46 up (38 done).
- **1032110:** RAND from 118 up (11 done).

No tag has more than one dir within the three jobs. Other BASE/KO dirs (jobs 966157, 968534, …) are excluded by
`--require-slurm-job`. I tested the real `strict_run_dir` with this job list on a synthetic set (multi-job BASE,
in-progress duplicate, a run short by 4 with `allow_short 20`, a complete duplicate within one job): it picks the
1022698 BASE, skips no-DONE dirs, accepts a documented short run and refuses the duplicate.

I mocked only the subprocess, overlap and GPU steps of the wrapper:

- **Command:** 205 arms. OVL arms are **absent** from `--arms`; they are used only by `overlap()`. 190 RAND + 10
  SHUF = 200 controls via `--control-prefixes KO_SHUF,KO_RAND --expect-n-controls 200`.
  `--require-slurm-job 1022698,1027577,1032110`; options `--split validation --expect-n 230 --option-mass-floor 0.05
  --allow-short 20` (the S-072 standard).
- **Decision logic:**

  | scenario | outcome | p and Holm |
  |---|---|---|
  | rank 1 | PASS | p 0.00498, Holm 0.0149 |
  | rank 3 | PASS | Holm 0.0448 |
  | rank 4 | DOES NOT PASS | Holm 0.0597 |
  | rank 2 with one SHUF above | DOES NOT PASS | – |
  | SHUF tie | DOES NOT PASS | strict `>` |
  | CI-lo ≤ 0 | DOES NOT PASS | – |
  | overlap / non-A5000 / analyzer VOID | VOID | – |
  | 201 rows | PASS, deviation −2 reported | – |

  Holm uses the as-recorded r1 0.2456 and r16 0.1754.
- **Gates:** the analyzer's `gates` are all booleans, so `all(bool(v))` is sound.
- **GPU check:** the logs for all three jobs contain only "NVIDIA RTX A5000".

Gaps: #1 (not committed), #9 (rounding; responsible controls not named).

## 3. Cross-amendment consistency

- **P2b (base + A1–A4 + VALIDATION):**
  - The pass rules nest consistently (A4 ⊂ A3 ⊂ A2 ⊂ A1); the families and populations are consistent.
  - The prereg hashes in `configs/` equal the `prod/` copies and the shas cited in each amendment.
  - Gaps are #4 (outcomes and the deciding split), the missing `--addon` in the VAL command (#1), and position
    wording. Position wording has three uncoordinated conditions: A1 "CWONLY > ATLAST" (point only, no CI), A2
    secondary PASS on VAL, and A3 "CWONLY − CWMEANBIAS CI-lo > 0". It should be stated once as a conjunction.
- **P4 (A1–A3):** consistent. A2's "no Holm unless both valid" and P2b-A4's "p=1, m=2" both end in INCOMPLETE, never
  PASS, so they are equivalent in outcome but worded differently.
- **S-084 + A1:** consistent. A1's 203-row rule is "report, use as-is", which the code follows except for naming the
  responsible controls.
- **P6 + A1–A2:**
  - A2 supersedes A1's Holm and UNDERPOWERED rule cleanly.
  - Open: #3 (outcome z), H6c multiplicity, and shared VAL domains between the probe and z.
  - The DEV fill rule and the occ-exclusion files are consistent with S-103.

## 4. Overclaim audit S-097…S-109

- **Fine:**
  - S-097 corrections.
  - S-099/S-100/S-101 amendments, all frozen before endpoints.
  - S-103: verified; the "basketball" rows touch no incumbent artifact.
  - S-106/S-109 "unread" holds.
  - S-107: guard conditions verified.
  - S-108: the overlap check reads only already-read arms (OVL_CAND = the S-072 candidate).
- **Wording to tighten:** see #11.
- **Process:** log clock labels are again out of order (S-102 08:40 after S-101 09:30).

## 5. Tests

`pytest research/heretic_csi/tests -q`: **57 passed, 1 skipped** (poc_stage2, 62 s).

## Concrete fixes, in order (all before the affected read)

1. Commit `p2a_powered_analyze.py` and the exact P2b TRAIN and VAL command lines, with `--addon` and their sha.
2. Submit the four add-on jobs. Until the add-on is analysed, any P2b PASS gets the A3 minimal wording.
3. Make three small code fixes in `p2b_analyze.py`:
   - eligibility only when split is validation;
   - hook check on CAND and KO_IDENT;
   - a bank/excl/codeword VOID, plus run-dir provenance for the CW and add-on arms.

   Add regression tests for each. These are analysis-hygiene changes, but freeze them as a note in A5 or the log
   before the read.
4. Freeze one P2b sentence covering outcomes A–E, the deciding split (VAL) and TRAIN-FAIL + VAL-PASS. Freeze one P6
   A3 covering the outcome-z family and H6c multiplicity, before any Stage-0 number.
5. Make the small S-084 wrapper changes: assert rank equality and name the short controls.
