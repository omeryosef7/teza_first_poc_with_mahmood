# ADVERSARIAL REVIEW R10 — PR-CSI-003 / 005 / 006 gate scripts

Environment for every command below:
`bash -lc 'source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh && conda activate poc_stage2 && cd /home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood && <cmd>'`
No file in the repo was edited. No sbatch. No git write. All scratch under `/tmp/claude-47249/.../scratchpad/`.

---

## 0. WHAT I COULD NOT BREAK (state this first, it bounds everything else)

**(d) The swap artifacts are CORRECT.** Independent verification, my own code, sha256 over `tensor.numpy().tobytes()`:

| | `dcs_csi_axis_button_L18_PLUS_basket_swap.pt` | `dcs_csi_axis_basket_L18_PLUS_button_swap.pt` |
|---|---|---|
| pre-existing keys byte-identical to source | **53 of 53** | **41 of 41** |
| keys removed | 0 | 0 |
| keys added | `swap_cand_from_basket` | `swap_cand_from_button` |
| `meta.codeword` | `'button'` (recipient's) | `'basket'` (recipient's) |
| `meta.selected_layer` | 18 | 18 |
| added key == donor `cand_rank1` | **True (sha256 identical)** | **True (sha256 identical)** |
| added key == recipient `cand_rank1` | False | False |
| `cos(added, out.cand_rank1)` | 0.55689294 | 0.55689294 |
| provenance `donor_file_sha16` vs actual file sha16 | `9fd8975480273ba2` = `9fd8975480273ba2` | `2a7014c134af36ab` = `2a7014c134af36ab` |

**All four committed ranks reproduce at higher precision.** I re-ranked from `domain_means` (5 dp *per domain*, averaged over 67/23 domains → ~1e-6 precision) instead of from the 5-dp scalars the gates use:

| report | candidate | recomputed | report | rank recomputed / reported | native `KO_AXIS` recomputed | native rank |
|---|---|---|---|---|---|---|
| `SUBSPACE_button_train_L18_n46` | KO_AXIS | −0.00014493 | −0.00014 | **36 / 36** | −0.00014493 | 36 |
| `SWAP_button_train_L18_from_basket_n46` | XSWAP_FROM_BASKET | +0.00149881 | +0.00150 | **4 / 4** | −0.00014493 | **36** |
| `SWAP_basket_train_L18_from_button_n46` | XSWAP_FROM_BUTTON | +0.00090000 | +0.00090 | **13 / 13** | +0.00264881 | 1 |
| `SWAP_basket_validation_L18_from_button_n46` | XSWAP_FROM_BUTTON | +0.00223565 | +0.00224 | **2 / 2** | +0.00400522 | 1 |

S-137 `X = 28` reproduces. S-133 reproduces exactly: `point −0.00852`, `ci95 [−0.01127, −0.00592]`, `n_neg 55 / n_pos 12 / 67`, rank 1 of 9, floor 0.1111, VERDICT INCONCLUSIVE; my own recomputation from `domain_means` gives mean −0.008518, 55 of 67 negative. S-138's side numbers reproduce: `KO_FULL−KO` = +0.10938 / +0.12063 / +0.10369; direction A `ci95 [0.00047, 0.00256]`, `p_two_sided 0.00701`, `n_pos 44 / 67`; 0.00150/0.10938 = 1.37 %. `python src/boombness/run_completeness_check.py` passes (95 documented short, 0 undocumented).

So: **no committed number is wrong.** Every finding below is about gates that would not have caught it if one had been.

---

## 1. PER-SCRIPT TABLE

| script | verdicts printed | size asserted? | dir resolution | can it PASS having compared nothing / the wrong thing? |
|---|---|---|---|---|
| `dcs_csi_pr005_gate0.py` | 0(c), 0(a), 0(b), 0(f) + PART 2 | 0(c) **no** (literal `"36 expected"`); 0(a) `assert n>=50` (loose); 0(b) `assert checked==3`; 0(f) **no** | by **job id** (`newest(arm, jobs)`), no layer filter. 36 new dirs measured all `rescue_layer=18`, one per (job,arm) — unambiguous today | **YES** — 0(f) PASSes on empty `OUT_PATHS`; 0(c) PASSes on a 1-arm family; 0(a) tolerates losing 4 stage-1 arms |
| `dcs_csi_pr005_primary_X.py` | X, threshold firings, VERDICT | `assert len(ctrl)==46` + partition asserts. **No report-identity assert** | n/a | **YES** — aimed at the wrong report it passes every assert and prints a different verdict |
| `dcs_csi_pr005_gate0d.py` | GATE 0d | `fa/fb/common >= 600`, all 6 fields present on every common row — **the best non-vacuity in the set** | `A_DIR = sorted(glob(CODEANCHOR_R0_*))[-1]` = **newest dir**, no job/layer filter (1 candidate today); `B_DIR` hardcoded | Structurally yes: never asserts `A.git_commit != B.git_commit`, i.e. never asserts the two blobs it exists to contrast actually differ |
| `dcs_csi_pr006_gate0.py` | (c),(a),(b),0e,0f,0g,(g) + PART 3 | (a) `assert n==3`; (b) `assert n==3`; 0e `assert len(shared)==n_keys`; (g) `assert n_rows>=lo`. (c) **no**; 0f **no** | `rundir(tag,arm,jobs,layer)` — **job id AND layer**; the S-127 hazard is genuinely fixed (mutation M8 proves the layer filter is load-bearing) | **YES** — 0f's sha anchor never compares; (g) reads a field name that, if wrong, silently yields 0; (c) PASSes on zero cells |
| `dcs_csi_pr006_native_vs_swap.py` | swap rank, native rank, HELPS | `assert len(ctrl)==46` only. **No exit code at all** | n/a | **YES** — both arm names are free variables with no assertion; native is computed from a lossier path than the controls |
| `dcs_csi_pr006_stage_anchor.py` | STAGING ANCHOR PASS/FAIL | rows/fields asserted like 0d | **`A_DIR` and `B_DIR` are both `sorted(glob(...))[-1]` — newest dir, no job filter, no layer filter** | Structurally yes: never asserts `A.model != B.model`. Its own docstring says S-134's 0d failed by having both arms on the staged path — and it repeats the omission |
| `dcs_csi_pr006_build_swap_bases.py` | per-spec asserts + GATE 0e | everything asserted incl. re-load from disk | n/a by construction | **No** — strongest script in the set. Verified independently in §0 |
| `dcs_document_short_runs.py` | "documented: …" / "REFUSED to exempt" | none | reference arm = **newest mtime** over a glob whose prefix is truncated | **YES** — prints "documented:" after a `str.replace` that may have changed nothing |

---

## 2. MUTATION TABLES

### `dcs_csi_pr006_gate0.py` (copies in scratchpad/mut, run against the real repo)

| # | mutation | result | survives? |
|---|---|---|---|
| M0 | none | exit 0, ALL GATES PASS | baseline |
| **M1** | `donor_sha` → `deadbeefdeadbeef` / `cafebabecafebabe` | **exit 0, ALL GATES PASS** | **SURVIVES** |
| M2 | `n_keys=53` → `52` | exit 1, `AssertionError: expected 52 shared keys, found 53` | killed |
| M3 | `key="swap_cand_from_*"` → `"cand_rank1"` | exit 1, `FAIL -> ['0f:… cos=1.0000', …]` | killed |
| **M4** | `n_positions_norm_match_degenerate` → `…_XX` | **exit 0, ALL GATES PASS** | **SURVIVES** |
| **M5** | `lv.get("fired")` → `lv.get("firedXX")` | **exit 0, ALL GATES PASS** | **SURVIVES** |
| M6 | `expect_n=670` → `6700` | exit 1, `AssertionError: only 670 rows` | killed |
| M7 | add `--never-passed` to `EXPECT_DIFF` | exit 1, `0g: missing=['--never-passed']` | killed |
| M8 | `rundir(…, layer=18)` → `layer=20` | exit 1, `0g: unexpected=['--rescue-layer']` | killed (layer filter is real) |
| M9 | cos target `0.5569` → `0.9999` | exit 1, `0f:… cos=0.5569` | killed |
| M10 | `"[layer-override]"` → `"HOST="` | exit 1, `b:913190/1/2` | killed (gate b is not vacuous) |
| M11 | `CELLS = []` | exit 1 — but **`GATE (c)` printed `3 expected \| 0 FINISHED` and did not abort**; only `assert n == 3` in gate (a) stopped it | partially survives |
| M12 | norm target `1.0` → `99.0` | exit 1, `0f:… norm` | killed |

### `dcs_csi_pr005_gate0.py`

| # | mutation | gates printed | survives? |
|---|---|---|---|
| N0 | none | 0c PASS, 0a PASS, 0b PASS, **0f FAIL** (see MINOR-1) | baseline |
| **N1** | `NEW_ARMS = ["KO_RAND6"]` | **`36 expected \| 1 FINISHED … GATE 0(c): PASS`**, then killed only by `assert n >= 50` in 0(a) | **0(c) survives** |
| N2 | `rows_written` → `rows_writtenXX` | 0c FAIL | killed |
| N3 | `.get("gpu")` → `.get("gpuXX")` | 0a FAIL | killed |
| N4 | `EXPECT_N 670 → 6700` | 0c FAIL | killed |
| **N5** | `OUT_PATHS = []` | **`checked 0 paths` → `GATE 0(f): PASS`, exit 0, "ALL GATES PASS"** | **SURVIVES** |
| N6 | `[layer-override]` → `HOST=` | 0b FAIL | killed |
| N7 | `NEW_JOBS = ["999999"]` | exit 2, refuses | killed |
| N8 | banner expect `("20","5")` | 0b FAIL | killed |
| **N9** | `STAGE1_JOBS` wrong + `assert n>=50` relaxed | `inspected 36 run dirs (36 new + 0 stage-1)` → **0(a) PASS** | **survives** (real script's `n>=50` still allows losing 4 of 18) |
| N10 | tag `csi1_button_train_` → `csi1_basket_train_` | exit 2, refuses | killed |

### `dcs_csi_pr005_primary_X.py` and `dcs_csi_pr006_native_vs_swap.py`

| # | mutation | result | survives? |
|---|---|---|---|
| P0 | none | X = 28, inside [13,34], "CONFIRMED" | baseline |
| **P1** | `v >= cand` → `v > cand` | **X = 27** | survives (tie-sensitive, see MAJOR-2) |
| **P2** | `REP` → `SWAP_button_train_L18_from_basket_n46.json` | **all asserts pass; X = 2; "a falsification threshold FIRED"** | **SURVIVES** |
| **P3** | `REP` → `SWAP_basket_train_L18_from_button_n46.json` | **all asserts pass; X = 9; "a falsification threshold FIRED"** | **SURVIVES** |
| P4 | `range(4,24)` → `range(4,25)` | `AssertionError: KO_SHUF24 missing` | killed |
| **Q1** | `inst["KO_AXIS"]` → `inst["KO_FULL"]` | **exit 0**, prints `native KO_AXIS +0.10938 -> rank 1 of 47` | **SURVIVES** |
| **Q2** | `ko = inst["KO"]` → `inst["BASE"]` | **exit 0**, prints `native KO_AXIS −0.20697 -> rank 47 of 47` | **SURVIVES** |
| Q3 | remove the `round(...,5)` | ranks unchanged today | — |
| **Q4** | `v >= x` → `v > x` | **native rank 36 → 35** | survives |

---

## 3. FINDINGS

### BLOCKER-1 — S-138's committed conclusion is the opposite of what PR-CSI-006's own decision rule returns
**Measured.** `python -c` walk of `configs/dcs_csi_pr006_axis_swap.json`:
- `/THE_DISCRIMINATING_2x2.../definition_of_HELPS`: *"rank 1 or 2 among 46 controls … Rank 3 of 47 is p = 0.06383 and is NOT 'helps'."*
- `/decision_rule/step_6`: *"Report the validation replication of direction B beside its train result. **If they disagree, the direction is reported as NOT REPLICATED and no cell is claimed for it.**"*
- `/must_not_be_said_if_positive/5`: *"NOT 'replicated' unless direction B's train and validation cells AGREE."*
- `cell_neither_helps` (CELL 4) interpretation: *"**C1 is REFUTED** — a shared direction estimated BETTER should have transferred, and did not."*

Measured outcome: A = rank 4 (**not** helps), B train = rank 13 (**not** helps), B validation = rank 2 (helps). B disagrees across splits ⇒ **no cell may be claimed for B**; on train the cell is **CELL 4 ⇒ C1 REFUTED**.

Committed headline of S-138 (line 10206 of the sprint log) and commit `d515cc76`: *"**C1 is SUPPORTED and the STATE hypothesis is REFUTED**"* — which is the CELL 1 reading, a cell that was not attained in either direction.

The S-138 **body** is honest about all of this (it assigns CELL 4, says "no cell of the 2×2 was cleanly attained", "direction A misses its own preregistered bar", "p = 0.085, which does not clear 0.05"). The **headline and the commit message carry only the inverted post-hoc conclusion**, which is what any downstream reader, the claim table, and `git log` will pick up. Why it matters: the whole point of the prereg was that the cell assignment "does not get moved after the fact"; the entry says that in the body and then moves it in the title.
*Minimal fix (do not apply): restate the S-138 headline as the prereg's output — "CELL 4 on train; direction B NOT REPLICATED; C1 REFUTED by the fixed rule, SUPPORTED by the unpreregistered rank-36→4 contrast, which is reported as a secondary" — and amend the claim-table row accordingly.*

### BLOCKER-2 — GATE 0f's donor-sha identity anchor is a check that cannot fail, and its declared constants are wrong
**Measured.** `python scripts/gates/dcs_csi_pr006_gate0.py`:
```
button/train  key=swap_cand_from_basket  sha16=679c76d2d0e8fe9e (expect 0c397a778db933ba)
basket/train  key=swap_cand_from_button  sha16=b2f266d711994013 (expect 7d4e01f5475e6b53)
  GATE 0f: PASS
```
The printed sha16 **disagrees with the printed expectation in both cells and the gate says PASS**, because `c["donor_sha"]` appears only inside the `print` at `scripts/gates/dcs_csi_pr006_gate0.py:153-154` and is never compared. Mutation M1 (both constants replaced with `deadbeef…`/`cafebabe…`) still prints ALL GATES PASS. The declared constants match nothing in the artifacts: not the tensor sha (`679c…`/`b2f2…`), not the donor file sha (`9fd8975480273ba2`/`2a7014c134af36ab`), not the recipient file sha. This is R2-M5 / S-042 / S-134 for the fourth time, in the gate S-138 calls *"the one that mattered most"*.
Secondary: `cos(swap, recipient cand_rank1)` is **symmetric** — cos(basket_axis, button_axis) is the same scalar in both cells. "0.5569 in BOTH directions" is one measurement printed twice, not two independent confirmations.
*Minimal fix: `assert t16(sw) == c["donor_sha"]` with the correct tensor sha16, and compute `donor_sha` from the donor .pt rather than pasting a literal.*

### MAJOR-1 — `dcs_csi_pr005_primary_X.py` has no report-identity check; aimed at the wrong report it prints a falsification
Mutations P2/P3: repointing `REP` at either swap report passes `len(ctrl)==46`, `STAGE1 <= names`, `NEW <= names`, `len(NEW)==36`, and prints `X = 2` / `X = 9`, *"observed X inside the 95% predictive interval? **False**"*, *"**VERDICT: a falsification threshold FIRED.**"* The swap reports have the identical 46 control names, so every non-vacuity assert in the script is satisfied by the wrong file. Nothing checks `codeword`, `split`, `run_dirs`, `require_slurm_job`, or that the candidate arm is `KO_AXIS`.
*Minimal fix: assert `d["codeword"]=="button" and d["split"]=="train" and d["require_rescue_layer"]==18` and that `"KO_AXIS"` (not `XSWAP_*`) is the candidate, before reading `crd`.*

### MAJOR-2 — the PRIMARY statistic X is recomputed from 5-dp-rounded values and there is a live tie
`scripts/dcs_csi_subspace_analyze.py:952-958` computes the authoritative rank on **unrounded** means and then writes `round(v,5)`. `primary_X.py` recounts from the rounded numbers. Measured: `KO_SHUF16` has rounded recovery **exactly** `−0.00014` = the rounded candidate. Mutation P1 (`>` instead of `>=`) gives **X = 27**, not 28. X=28 happens to agree with the report's `rank 36`, but the agreement is luck of rounding, not a property the script checks.
*Minimal fix: assert `len(ex_all)+1 == crd["candidate_rank_among_controls"]` (currently printed as `True`, never asserted), and report the number of exact ties.*

### MAJOR-3 — `native_vs_swap.py`: the committed "native rank 36" is computed on a lossier path than the controls it is ranked against
`native = round(inst["KO_AXIS"] - inst["KO"], 5)` differences two values that are **already** rounded to 5 dp, while `crd["controls"]` are rounded **once** from unrounded means. Measured discrepancy: reconstructing every control the same way disagrees with the report's own controls on **20 of 46** (button/train), **13 of 46** (basket/train), **18 of 46** (basket/validation) — always by exactly 1e-5, which is the spacing of the controls near the middle of the distribution. Perturbing native by +1e-5 moves the committed **rank 36 → 35**; mutation Q4 (strict `>`) also gives 35. Independently re-derived from `domain_means` at ~1e-6: the true value is −0.00014493 and rank 36 is **correct** — but the script is not what established that.
Also: apart from `len(ctrl)==46` the script asserts nothing and returns no exit code. Mutation Q1 (`KO_AXIS`→`KO_FULL`) and Q2 (`KO`→`BASE`) both run clean and print an authoritative-looking `native KO_AXIS …` line with a fabricated number.
*Minimal fix: recompute both the candidate and the native from `domain_means` over the intersected domain set, and assert the recomputed candidate rank equals `crd["candidate_rank_among_controls"]`.*

### MAJOR-4 — gate (g)'s degeneracy count and `fired` flag are read by name with a silent zero default
`lv.get("n_positions_norm_match_degenerate") or 0`. Mutation M4 (field renamed to a name that does not exist) → `n_degenerate=0` on all three cells → **ALL GATES PASS**. Mutation M5 (`fired` renamed) → `fired=0` printed, still **ALL GATES PASS**, because `(g)` asserts `n_rows` and not `fired`. I confirmed the real field names exist in `results.jsonl` today, so the number is right; the gate cannot tell.
*Minimal fix: count rows where the key is **present** and assert that count equals `n_rows`; assert `fired == n_rows`.*

### MAJOR-5 — sizes are PRINTED as literals, not ASSERTED, in the two "family complete" gates
- `pr005_gate0.py:56` prints `"  36 expected | %d FINISHED"` with **36 hardcoded**. Mutation N1 (`NEW_ARMS` reduced to one arm) prints `36 expected | 1 FINISHED … GATE 0(c): PASS`. The only thing that stopped it was `assert n >= 50` two gates later.
- `pr005_gate0.py:120-126` — mutation N5 (`OUT_PATHS = []`) prints `checked 0 paths`, `GATE 0(f): PASS`, exit 0, **"ALL GATES PASS"**.
- `pr006_gate0.py:68` prints `"  3 expected"` with **3 hardcoded**. Mutation M11 (`CELLS = []`) prints `3 expected | 0 FINISHED | 0 not`, does not take the abort branch, and prints `GATE (c): PASS`.
The S-134 rule adopted this sprint is "print the size **and assert that size**". These three print a constant and assert nothing.
*Minimal fix: `assert len(NEW_ARMS) == 36`, `assert len(OUT_PATHS) == 3`, `assert len(CELLS) == 3` and print `len(...)`, not a literal.*

### MAJOR-6 — "newest dir" resolution is still present in two scripts, both of which feed committed results
- `dcs_csi_pr005_gate0d.py:18` — `A_DIR = sorted(glob(".../csi1_button_train_CODEANCHOR_R0_*"))[-1]`
- `dcs_csi_pr006_stage_anchor.py:24-25` — **both** `A_DIR` and `B_DIR` are `sorted(glob(...))[-1]`

No job filter, no layer filter. Measured: exactly one dir matches each glob today (`CODEANCHOR_R0_20260920_135631_905054`, `STAGEANCHOR_AXIS_20260920_170734_754715`, `basket_validation_KO_AXIS_20260916_090004_102474`), so the committed anchors used the right dirs — but nothing in either script asserts that, and S-127 is specifically about a tag existing twice at two layers. `pr005_gate0.py`'s `newest()` filters by job id only, no layer; measured, all 36 new dirs are `rescue_layer=18` with one dir per (job, arm), so it is unambiguous today by luck of the data, not by construction.
*Minimal fix: `assert len(hits) == 1` in every resolver, and add the `layer=` filter that `pr006_gate0.rundir` already has.*

### MAJOR-7 — the two bit-identity anchors never assert the contrast they exist to establish
- `gate0d` prints `git_commit=dabfeb854ec6 dirty=None` vs `git_commit=bc8e77793633 dirty=True` and **never asserts they differ**. If both arms ran the same blob, the gate passes and proves nothing — which is exactly the S-042 vacuous-identity-gate shape.
- `stage_anchor` prints `model=/tmp/dcs_snap_omeryosef/0e9e39f…` vs `model=/home/sharifm/.../snapshots/0e9e39f…` and **never asserts they differ**. Its own docstring records that S-134's gate 0d failed precisely this way (*"BOTH of its arms used the staged path (measured)"*) — and the new script repeats the omission. It also never asserts the two arms agree on `rescue_layer`, `rescue_basis_key` or `rescue_donor`.
*Minimal fix: `assert A.git_commit != B.git_commit` / `assert A.args.model != B.args.model`, plus `assert` equality on every other arm-defining field.*

### MAJOR-8 — `dcs_document_short_runs.py` can print "documented:" having written nothing, and its reference arm is mtime-resolved over a mixed pool
1. `src = src.replace(anchor, anchor + block, 1)` at line 99. If `"KNOWN_SHORT = {\n"` is ever absent (reformat, different newline), `replace` is a **no-op**, yet line 100 prints `documented: <rid>` and `added += 1`. Silent success. (The anchor is present today — verified.)
2. `pref = rid.rsplit("_", 3)[0].rsplit("_", 1)[0]` truncates the arm name. Measured: for `csi1_button_train_KO_SHUF9_20260920_160010_927085` → `pref = "csi1_button_train_KO"` → glob matches **118 dirs**; the full-row candidate pool is **83 dirs, of which 60 are `rescue_layer=20`, 21 are 18, 2 are None**. The reference is then `sorted(cands)[-1]` = **newest mtime**. It picked `KO_SHUF23` from **job 912837** while the short run is **job 912835**, and the generated text then asserts *"of the same allocation"* — a claim the code does not establish. Nothing prevents the mtime winner from being an L20 arm.
3. `open(P, "w").write(src)` with no read-back, no `ast.parse`, no atomic temp+replace — on the very NFS/EDQUOT hazard S-124 was written about. It prints `os.path.getsize`, which a successful-then-truncated write would also satisfy.
*Minimal fix: `assert anchor in src` before the replace; require the reference arm to share the exact arm-stripped prefix **and** `slurm_job_id` **and** `rescue_layer`, or refuse; write via the S-124 `_atomic_json_dump`-style temp+fsync+replace and re-parse.*

### MAJOR-9 — `tests/test_bf16_capability_guard.py::test_guard_predicate_truth_table` is tautological
The test body re-implements the predicate (`got = bool(dtype == "bfloat16" and cuda_available and cc[0] < 8)`) and **never reads `score_behavior.py`**. Demonstrated: I copied the function verbatim into `/tmp/.../tautology_demo.py`, ran `python -m pytest` from `/tmp` with no repo present — **5 passed**. The guard could be deleted entirely and this test would still be green. The file's other seven tests are source-text greps, which do catch deletion; `test_the_guard_is_absent_from_the_pre_fix_blob` is a genuine mutation proof. But the one test that *looks* behavioral is the one that cannot fail. 32/32 tests in the two new files pass; `test_atomic_report_write.py` is a real behavioral test (drives the actual helper, injects `OSError(errno.EDQUOT)`) and I found nothing wrong with it.
*Minimal fix: import the predicate from the module (or exec the guard block) rather than restating it.*

### MAJOR-10 — `pr005_gate0` GATE 0(a) tolerates silently losing stage-1 arms
`for a in STAGE1_ARMS: d = newest(a, STAGE1_JOBS); if d is None: continue` — a missing arm is dropped with no print. The only guard is `assert n >= 50` against 36 new + 18 stage-1 = 54. Up to **4 stage-1 arms can vanish** and 0(a) still prints PASS on the remaining set. Mutation N9 (wrong `STAGE1_JOBS`, assert relaxed) prints `inspected 36 run dirs (36 new + 0 stage-1) … GATE 0(a): PASS`.
*Minimal fix: `assert n == 54`, and print each dropped arm.*

---

### MINOR
- **MINOR-1** — `pr005_gate0.py` gate 0(f) ("output paths must NOT exist") now **permanently FAILs**, because the three reports exist. Measured today: `PART 2 VERDICT: FAIL -> ['0f:reports/…n46.json', …]`, exit 1. The committed "all Part 2 gates pass" claim is therefore not reproducible by re-running the committed script. By design, but nothing in the script or the log says so.
- **MINOR-2** — `reports/DCS_CSI_SWAP_basket_validation_L18_from_button_n46.json` carries `VERDICT: "PRIMARY DOES NOT PASS … ranks 2 of 47 … It is INSIDE the controls, not above them"` (analyser rule: `rank == 1 and floor < 0.05`, `dcs_csi_subspace_analyze.py:1020`), while the prereg's rule says rank 2 **HELPS** and `native_vs_swap.py` prints `swap HELPS`. Two pre-fixed rules, opposite words, same number, committed in the same hour.
- **MINOR-3** — every auto-generated `KNOWN_SHORT` entry is stamped `"DCS-CSI-133:"` (hardcoded in `TEMPLATE`), including PR-CSI-005 runs read at S-137 (e.g. `csi1_button_train_KO_SHUF9_…` reads `"DCS-CSI-133: PR-CSI-005 button L18 family"`). Also `exp=` is a two-way `"button" in rid` branch, so any non-button, non-necessity short run is labelled "PR-CSI-003 necessity".
- **MINOR-4** — `build_swap_bases.py:78` writes `"all_pre_existing_keys_byte_identical": True` as a **literal** into the artifact's provenance before the verification runs (the asserts follow `torch.save`). It is true — I verified it independently — but the artifact asserts it of itself.
- **MINOR-5** — `pr006_gate0.py` gates 0e and 0f `continue` past `basket/validation` with no printed note, so those two gates report 2 cells while `CELLS` has 3 and the header does not say so.
- **MINOR-6** — `flags()` (`pr006_gate0.py:189-194`) maps any flag whose value begins with `--` to `True`, and keeps only the last occurrence of a repeated flag. Not triggered by the current argv (23 flags compared in each cell), but the 0g diff is built on it.