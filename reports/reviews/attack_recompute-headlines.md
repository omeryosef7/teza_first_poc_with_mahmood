All three committed headlines reproduce exactly from raw rows with an independent stdlib-only estimator. The defects I found are in the *audit* code and the *decision rule*, not in the numbers.

My estimator: `/tmp/claude-47249/-home-sharifm-students-omeryosef-first-poc-teza-first-poc-with-mahmood/4da49896-7f0f-40cd-a8f0-50b462615089/scratchpad/indep.py` (imports nothing from the project; `y = exp(lc-m)/(exp(lc-m)+exp(lk-m))` on `query_kind=="semantic_one_word" and cell=="C"`, key `(domain, "|".join(family_id.split("|")[1:-1]))`, split from `data/boombness_prompts/dcs_ts116_domain_split.json`, per-arm key intersection, per-domain mean, then domain-level contrast, 20000-draw domain-clustered bootstrap with my own seed).

## RECOMPUTATION TABLE

| quantity | committed | my value | difference | verdict |
|---|---|---|---|---|
| **1. NECESSITY** (basket/train) n_keys_common | 664 | 664 | 0 | MATCH |
| n_domains / all train | 67 | 67 (0 test, 0 validation) | 0 | MATCH |
| KO_NEC_AXIS − NEC_BASE | −0.00852 | −0.0085170 | 3e-6 (rounding) | MATCH |
| ci95 | [−0.01127, −0.00592] | [−0.01129, −0.00589] | ≤3e-5 | MATCH (own RNG seed) |
| negative domains | 55 of 67 | 55 of 67 (12 pos, 0 tied) | 0 | MATCH |
| rank among 8 SHUF/RAND controls | 1 of 9 | 1 of 9 | 0 | MATCH |
| all 13 `installation_by_arm` values | as committed | max abs diff 6.1e-6 | — | MATCH |
| **2. PR-CSI-005** (button/train/L18/n46) n_keys | 626 | 626 | 0 | MATCH |
| n_domains | 67 | 67 (all train) | 0 | MATCH |
| KO_AXIS − KO | −0.00014 | −0.00014466 | — | MATCH |
| rank among 46 controls | 36 of 47 | 36 of 47 | 0 | MATCH |
| X (36 blind KO_SHUF4-23 / KO_RAND6-21) | 28 | 28 (28 also with strict `>`) | 0 | MATCH |
| **3. SWAP A** basket→BUTTON train n_keys / n_dom | 626 / 67 | 626 / 67, **set-identical** to PR-005's 626 (sym-diff 0) | 0 | MATCH |
| XSWAP_FROM_BASKET − KO | +0.00150 | +0.00149891 | — | MATCH |
| its rank | 4 of 47 | 4 of 47 | 0 | MATCH |
| its ci95 / n_pos (S-138 text) | [+0.00047,+0.00256], 44 of 67 | [+0.00047,+0.00255], 44 of 67 | 1e-5 | MATCH |
| native KO_AXIS − KO, same key set | −0.00014 | −0.00014466 | — | MATCH |
| its rank | 36 of 47 | 36 of 47 | 0 | MATCH |
| **SWAP B** basket train swap / rank | +0.00090 / 13 | +0.00090068 / 13 | 0 | MATCH (641 keys / 67 dom) |
| SWAP B basket train native / rank | +0.00265 / 1 | +0.00264929 / 1 | 0 | MATCH |
| SWAP B validation swap / rank | +0.00224 / 2 | +0.00223736 / 2 | 0 | MATCH (215 keys / 23 dom) |
| SWAP B validation native / rank | +0.00400 / 1 | +0.00400669 / 1 | 0 | MATCH |
| TEST-split domains anywhere | 0 | 0, across **173 distinct run dirs** | 0 | MATCH |

No sign, rank or key-set discrepancy anywhere. **No BLOCKER on any committed number.**

---

## FINDINGS

### F1 — MAJOR (arguably BLOCKER): the preregistered HELPS rule (R47 ≤ 2) is implemented in no code that writes a report, so the committed verdict for the one cell that clears the bar says the opposite of the prereg

Measured:
- `configs/dcs_csi_pr006_axis_swap.json` states the rule four times: `primary_statistic.decision` = `"HELPS iff R47 <= 2."`, `decision_rule.step_3` same, `definition_of_HELPS` = *"rank 1 or 2 among 46 controls (p = 0.02128 or 0.04255 <= 0.05)"*, and `must_not_be_said_if_positive` = *"only R47 <= 2 licenses 'helps'"*.
- `scripts/dcs_csi_subspace_analyze.py:1022` — `if rank == 1 and attainable:` → PASS, else the FAIL text.
- `scripts/dcs_csi_rederive_subspace.py:303` — `"PASSES" if (r == 1 and fl <= 0.05) else ... "DOES NOT PASS"`.
- Consequence, read from the committed artifacts: `reports/DCS_CSI_SWAP_basket_validation_L18_from_button_n46.json` → `VERDICT: "PRIMARY DOES NOT PASS on split=validation -- the candidate ranks 2 of 47 ... It is INSIDE the controls, not above them."` and its twin `DCS_CSI_SWAP_REDERIVE_basket_validation_L18_from_button.json` → `ranks.pooled.verdict = "DOES NOT PASS"` at `rank: 2, floor: 0.0213, certifiable_at_0.05: true`.
- The same rank in the same repo, from `python scripts/gates/dcs_csi_pr006_native_vs_swap.py`: `PRE-FIXED RULE: HELPS == rank <= 2 -> swap HELPS`. S-138 reads it the same way ("VALIDATION says rank 2 (HELPS)").
- `grep -rn "<= 2" scripts/ src/ tests/ --include=*.py` finds the HELPS rule in exactly one place: the `print` on line 37 of `native_vs_swap.py`.

Why it matters: two committed artifacts and the committed narrative give opposite verdicts for the same number, on the **only** cell in the entire experiment that meets the preregistered bar — the cell that makes direction B "NOT REPLICATED" (prereg `decision_rule.step_6`) and that, read alone, puts the experiment in CELL 2 (state confirmed), the opposite of the headline. A reader trusting the report files concludes nothing helps anywhere. The prereg's own decision rule is unreachable code: no report-writing tool here can emit HELPS at rank 2.

Minimal fix (not applied): make the pass predicate a parameter (`--rank-pass-max`, default 1) in both analyzers and pass 2 for PR-CSI-006; or, if `rank == 1` is the intended standard, amend the prereg and S-138 to say the bar was rank 1 and that no cell met it.

### F2 — MAJOR: the two new PRIMARY-statistic scripts recompute from 5-decimal-rounded report fields with a `>=` tie rule, and the margin deciding button's rank is 5.0e-6 — half the rounding quantum

Measured:
- `reports/DCS_CSI_SUBSPACE_button_train_L18_n46.json`: `control_recovery_distribution.candidate` = `-0.00014` and `controls.KO_SHUF16` = `-0.00014` — an **exact tie at stored precision**.
- Full precision (my estimator): candidate `-0.00014466`, KO_SHUF16 `-0.00013967`. Gap **4.99e-06**.
- `scripts/gates/dcs_csi_pr005_primary_X.py:41` computes X as `[k for k, v in ctrl.items() if v >= cand]` over exactly those rounded values.
- `scripts/gates/dcs_csi_pr006_native_vs_swap.py:91` is worse: it *reconstructs* the native contrast as `round(inst["KO_AXIS"] - inst["KO"], 5)` from two already-rounded pooled means (`0.46867 - 0.46881`), yielding `-0.00014` against a true `-0.00014466` — an error of **+4.66e-06, i.e. 93 % of the gap to the nearest control**.

X = 28 and rank 36 are correct (I reproduced both at full precision, and at full precision there are no ties), but only because the `>=` tie-break direction happens to agree with the true ordering. The authoritative rank inside the report *is* computed at full precision (`analyze.py:954`), so both gate scripts are strictly less accurate than the artifact they audit. A perturbation smaller than the report's own display rounding silently moves the PRIMARY statistic.

Minimal fix: emit an unrounded control/candidate block (or the rank and X themselves) from the analyzer and have both scripts read that; never reconstruct a contrast by subtracting two rounded pooled means.

### F3 — MAJOR: `tests/test_bf16_capability_guard.py` contains a test that cannot fail, in the file written to stop exactly that

Lines 63–74 re-implement the predicate inside the test and assert it against itself:

```python
got = bool(dtype == "bfloat16" and cuda_available and cc[0] < 8)
assert got is refuses
```

No symbol from `score_behavior.py` participates. Change the guard to `_cc[0] < 7` and this test still passes. The entire file is textual (`_src(path)` + `str.index` / `re.search`); nothing imports or executes the guard — `python -m pytest tests/test_bf16_capability_guard.py tests/test_atomic_report_write.py -q` → `32 passed in 0.63s`, which is only possible because the code under test never runs. This is the S-042 / R2-M5 / S-134 pattern the sprint says it has stopped committing. `tests/test_atomic_report_write.py`, by contrast, drives the real `_atomic_json_dump` and injects `OSError(errno.EDQUOT)` — so the standard was available in the same session.

Minimal fix: import the guard as a callable and exercise it with a stubbed `torch.cuda.get_device_capability`; failing that, delete the tautological `parametrize` — the regex pin on line 43 is the only thing actually protecting the predicate.

### F4 — MAJOR: `scripts/gates/dcs_document_short_runs.py` uses the exact unanchored glob S-042 was written about, then writes a source file non-atomically

- Line 78: `pref = rid.rsplit("_", 3)[0].rsplit("_", 1)[0]`. For `csi1_button_train_KO_SHUF16_20260920_144136_913270` this yields `csi1_button_train_KO`; line 80 globs `csi1_button_train_KO_*`, which matches KO_SELF, KO_FULL, KO_AXIS, KO_PLS, KO_ORTH, KO_AXIS_ANCHOR and every control. For an arm with no suffix (`..._KO_<ts>`, `..._BASE_<ts>`) `pref` collapses to `csi1_button_train` and the glob matches every arm of the codeword. `strict_run_dir`'s own comment block documents this defect verbatim ("an ad-hoc check using the unanchored glob resolved arm `KO` to the `KO_SELF` directory"). The effect is bounded here (the reference is only used to diff key sets, which are arm-independent), but the generated text asserts *"MEASURED here against the full 670-row arm {ref} **of the same allocation**"* — which the selector does not establish.
- Line 104: `open(P, "w").write(src)` on `src/boombness/run_completeness_check.py` — truncate-then-write, no temp file, no fsync, no re-parse, on the filesystem whose EDQUOT behaviour is asynchronous. This is the S-124 idiom that `tests/test_atomic_report_write.py` now forbids for reports, applied to a source file. `print("wrote", os.path.getsize(P), "bytes")` is not verification. (I observed no damage: the file holds 27 `DCS-CSI-133` entries and `git diff --stat` shows it clean.)
- Line 39: `r.get("family_id") or r.get("slot") or r.get("prompt_sha16")` silently changes key shape instead of raising, which would make `kr - kk` meaningless rather than loud.

### F5 — MINOR: `pr006_gate0.py` silently skips a cell in gates 0e and 0f
Lines 122–123 and 146–147: `if c["cell"] == "basket/validation": continue`, with nothing printed. The check is genuinely redundant (both basket cells name the same two `.pt` paths), but the gate header claims per-cell coverage and prints 2 comparisons where a reader expects 3. Under the sprint's own rule it should print "SKIPPED — identical artifact to basket/train".

### F6 — MINOR: `pr005_gate0.py` GATE 0(a) `assert n >= 50` admits a short stage-1 sample
Line 88 `if d is None: continue` drops an unresolvable stage-1 arm silently; with 36 new + 18 stage-1 possible, the assert passes with up to 4 stage-1 arms missing and never names them. Should be `assert n == 36 + len(STAGE1_ARMS)`, or print the misses.

### F7 — MINOR: 3 of the 70 frozen TRAIN domains are absent from every run and no report says so
`dcs_ts116_domain_split.json` assigns 70 train / 23 validation / 23 test. All 173 run directories behind the five reports carry exactly 67 train domains: `restaurant_kitchen`, `school_campus`, `subway_station` have **0 rows in every run**, in both codewords. They are not explained by the exclude lists — each has 64 `semantic_one_word` rows in its bank and only 10 of 192 excluded, the same fraction as 49 other domains; the drop happens upstream of the scorer (`csi1_button_train_BASE_...` emits 670 rows, all `semantic_one_word`/cell C, over 67 domains). It is identical across every arm and both codewords, so it **cannot bias a within-read contrast**, but `n_domains: 67` is reported with no statement that 3 frozen train domains are missing. **CANNOT MEASURE** the rule that drops them.

### F8 — MINOR: headline/body mismatch in `d515cc76` and the S-138 title line
The subject asserts "C1 SUPPORTED, STATE hypothesis REFUTED". Under the prereg's binding rules direction A at R47 = 4 does **not** help, and `decision_rule.step_6` / `must_not_be_said_if_positive` require direction B to be "reported as NOT REPLICATED and no cell claimed for it" when train and validation disagree — which they do (13 vs 2). The S-138 **body** discloses all of this at length under "What may NOT be said", so this is a headline overstating its own body, not a concealed claim.

---

## THINGS I TRIED TO BREAK AND COULD NOT (all measured)

- **No TEST-split domain** in any of the 173 run directories behind the five reports.
- **The S-125 key-set trap was avoided**: the PR-005 read's 626 keys and the swap read's 626 keys are the *same set* (symmetric difference 0), so S-138's "both ranks on ONE key set" is literally true.
- **The 46 controls are 46 distinct directions**: no duplicated `run_dir`, and 50 distinct `(basis_keys, rescue_basis, norm_match_keys)` signatures across 53 arms (the 3 collisions are BASE/KO/KO_SELF/KO_FULL, which carry no basis by design). Same for the necessity read's 8 controls.
- **Dose is matched despite the candidate being the only un-norm-matched rescue arm.** `KO_AXIS`/`KO_NEC_AXIS` carry `norm_match_keys: []` while all 46 (resp. 8) controls carry `cand_rank1`; the comparability rests on "basis == norm-basis is the identity", which was bit-identically measured only once (STAGEANCHOR, basket/validation, 230 rows, sufficiency) and never in the necessity direction. I checked the dose directly instead: `written_norm` means are candidate **0.067975** vs KO_RAND0 **0.067975** / KO_SHUF0 **0.067918** (button L18), and candidate **0.058469** vs KO_NEC_SHUF0 **0.058469** / KO_NEC_RAND0 **0.058465** (necessity). Matched in fact.
- `liveness_violations = 0` and `degenerate_positions = 0` on every arm of all three reads; `n_rows` min/max 666/670 within the declared `--allow-short 4`.
- All four REDERIVE twins agree with their primaries on point estimate and on every rank (necessity 1 of 9; button L18 36 of 47; swap A 4 of 47; swap B 13 / 2 of 47), on their own slightly different key sets (664 / 627 / 627 / 641 / 215).

Note: `squeue -u omeryosef` returns no rows from this node — job 913407 is not visible as running. I launched nothing, edited nothing, and wrote only to my scratchpad.