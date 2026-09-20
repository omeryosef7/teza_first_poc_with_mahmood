R9b — LENS: the row-shortfall exemption machinery. Repo untouched (`git status --porcelain` identical to start; `md5sum src/boombness/run_completeness_check.py` == `git show d515cc76:` copy). No sbatch, no git write ops. All scratch in `/tmp/claude-47249/.../scratchpad/ks/`.

## (a) KNOWN_SHORT before/after

`git show a853d5b6~1:src/boombness/run_completeness_check.py` vs `git show d515cc76:...`, dicts extracted with `ast.literal_eval`:

- **before (a853d5b6~1): 67 entries** — **HEAD (d515cc76): 95 entries** — **+28 added, 0 removed, 0 existing entry's text changed.** Working tree == HEAD for this file.
- `git diff --numstat a853d5b6~1..d515cc76 -- src/boombness/run_completeness_check.py` → **`461 0`**, one hunk `@@ -154,0 +155,461 @@ KNOWN_SHORT = {`. **No guard logic was edited this session** — only the table grew. `tests/test_run_completeness_check.py` has **zero** diff this session. So the brief's "roughly a dozen" is wrong: it is 28.

## (b) Audit of all 28 added entries — ALL CLAIMS CHECK OUT

Command: `python .../ks/audit.py` (parses each entry's Ledger/pids/domain claims out of the KNOWN_SHORT string, re-measures against `DONE.json` + `results.jsonl` + the named reference arm).

| run_id | claim n_failed | rows on disk | Σfailure_reasons | domains | pids verified | reference used |
|---|---|---|---|---|---|---|
| csi1_basket_train_KO_NEC_RAND0_…904077 | 1 | 669 | 1 | 1 | YES | KO_NEC_SHUF0_…900451 |
| csi1_basket_train_KO_NEC_RAND2_…908639 | 4 | 666 | 4 | 3 | YES | KO_NEC_SHUF0_…900451 |
| csi1_basket_train_KO_NEC_RAND3_…910493 | 1 | 669 | 1 | 1 | YES | KO_NEC_SHUF0_…900451 |
| csi1_basket_train_XSWAP_FROM_BUTTON_…752290 | 1 | 669 | 1 | 1 (printing_works) | YES | hand-written, KO_AXIS_…1768788 |
| csi1_button_train_KO_RAND6_…905064 | 2 | 668 | 2 | 2 | YES | KO_SHUF14_…909805 |
| csi1_button_train_KO_RAND7_…907356 | 2 | 668 | 2 | 2 | YES | KO_SHUF14_…909805 |
| csi1_button_train_KO_RAND8_…909321 | 1 | 669 | 1 | 1 | YES | KO_SHUF14_…909805 |
| csi1_button_train_KO_RAND10_…912952 | 1 | 669 | 1 | 1 | YES | KO_RAND19_…918010 |
| csi1_button_train_KO_RAND11_…914600 | 1 | 669 | 1 | 1 | YES | KO_RAND19_…918010 |
| csi1_button_train_KO_RAND12_…905052 | 2 | 668 | 2 | 2 | YES | KO_SHUF14_…909805 |
| csi1_button_train_KO_RAND13_…907435 | 2 | 668 | 2 | 2 | YES | KO_SHUF14_…909805 |
| csi1_button_train_KO_RAND15_…911373 | 2 | 668 | 2 | 2 | YES | KO_RAND9_…911304 |
| csi1_button_train_KO_RAND17_…914678 | 1 | 669 | 1 | 1 | YES | KO_RAND19_…918010 |
| csi1_button_train_KO_RAND18_…916511 | 3 | 667 | 3 | 2 | YES | KO_RAND19_…918010 |
| csi1_button_train_KO_RAND20_…920797 | 1 | 669 | 1 | 1 | YES | KO_SHUF6_…921383 |
| csi1_button_train_KO_RAND21_…922373 | 2 | 668 | 2 | 2 | YES | KO_SHUF23_…927673 |
| csi1_button_train_KO_SHUF4_…916403 | 1 | 669 | 1 | 1 | YES | KO_RAND19_…918010 |
| csi1_button_train_KO_SHUF5_…918691 | 1 | 669 | 1 | 1 | YES | KO_RAND19_…918010 |
| csi1_button_train_KO_SHUF7_…922528 | 1 | 669 | 1 | 1 | YES | KO_SHUF23_…927673 |
| csi1_button_train_KO_SHUF8_…924695 | 1 | 669 | 1 | 1 | YES | KO_SHUF23_…927673 |
| csi1_button_train_KO_SHUF9_…927085 | 1 | 669 | 1 | 1 | YES | KO_SHUF23_…927673 |
| csi1_button_train_KO_SHUF10_…924611 | 2 | 668 | 2 | 2 | YES | KO_SHUF23_…927673 |
| csi1_button_train_KO_SHUF12_…905056 | 1 | 669 | 1 | 1 | YES | KO_SHUF14_…909805 |
| csi1_button_train_KO_SHUF15_…911849 | 1 | 669 | 1 | 1 | YES | KO_RAND9_…911304 |
| csi1_button_train_KO_SHUF17_…914759 | 2 | 668 | 2 | 2 | YES | KO_RAND19_…918010 |
| csi1_button_train_KO_SHUF19_…918007 | 1 | 669 | 1 | 1 | YES | KO_RAND19_…918010 |
| csi1_button_train_KO_SHUF20_…920725 | 1 | 669 | 1 | 1 | YES | KO_SHUF6_…921383 |
| csi1_button_train_KO_SHUF22_…925273 | 1 | 669 | 1 | 1 | YES | KO_SHUF23_…927673 |

Verified per entry, all 28 clean:
- claimed `n_attempted`/`n_succeeded`/`n_failed` == `DONE.json` `n_rows_attempted`/`rows_written`/`n_rows_failed`, and `rows_written` == actual `wc -l results.jsonl`;
- `failure_reasons` keys are **exclusively** the norm-match degeneracy string, and **Σ values == n_rows_failed** (so nothing is lost outside the ledgered refusals);
- every claimed failing prompt_id is **present in the reference arm and absent from the short arm**, and the claimed pid list is **exactly** the measured missing set (no under-listing);
- claimed domain count and "at most m rows per domain out of 10" match measurement (27/27 auto entries, 0 mismatches); reference arms genuinely hold 670 rows, 67 domains × 10 rows each;
- the two embedded cross-report numbers are real: XSWAP's "641 keys / 67 domains / 53 arms" == `reports/DCS_CSI_SWAP_basket_train_L18_from_button_n46.json` (`n_keys_common` 641, `n_domains` 67, 53 arms); the basket NEC entries' "664 keys / 67 domains / 13 arms" == `reports/DCS_CSI_SUBSPACE_NECESSITY_basket_train.json`;
- config comparison short-run vs named reference: `rescue_layer`, `split`, `expect_n`, `slurm_job_id`, `codeword`, `rescue_donor` identical in all 27 cases;
- largest shortfall among the 28 is 4 rows (KO_NEC_RAND2), exactly at the declared `allow_short: 4` (`configs/dcs_csi_pr003a_necessity_family.json:80`).

**No BLOCKER. No false exemption found among the added entries.**

## (c) Can the guard still FAIL? Yes — three demonstrations, plus one real blunting

1. **Guard currently passes**: `python src/boombness/run_completeness_check.py` → exit 0, "848 finished runs carry an expect_n; 95 documented short".
2. **Every one of the 95 exemptions is load-bearing, zero are stale.** `rc.scan()` flags exactly 95 rids; `set(KNOWN_SHORT) - flagged = ∅` and `flagged - set(KNOWN_SHORT) = ∅`. So an entry whose run became LONGER than claimed *is* noticed — by `tests/test_run_completeness_check.py::test_every_KNOWN_SHORT_entry_is_actually_flagged_by_the_scan`, not by the guard itself.
3. **Undocumented short run still trips it.** Removing one added entry (`KO_SHUF9_…927085`) from `rc.KNOWN_SHORT` in-memory and calling `rc.main()` → **exit 1**, `SHORT csi1_button_train_KO_SHUF9_…: persisted 669 rows in results.jsonl against --expect-n 670` + `[run-complete] FAIL`. Script: `.../ks/demo1.py`.
4. `pytest tests/test_run_completeness_check.py -q` → **30 passed** (202s).

## FINDINGS

### MAJOR-1 — a KNOWN_SHORT exemption is unbounded in magnitude, and swallows the ledger and cell-balance checks too
**Measured.** Built `.../ks/fakeroot/` (symlinks to all 1374 real run dirs, one dir replaced by a copy of `KO_SHUF9_…927085` whose `results.jsonl` was `head -300`). With `rc.ROOT` pointed there:
- `rc.scan()` flags it `persisted 300 rows in results.jsonl against --expect-n 670`
- `rc.main()` → **exit 0**, no FAIL line, run not printed.

The entry claims "669 of 670, 1 lost row, 1 domain". The run held 300 rows and its `summary.json` ledger still claimed `n_succeeded = 669`. That ledger-vs-file disagreement — the *dangerous* case the module docstring names — was never reported, because `run_completeness_check.py:1613` does `problems.append(SHORT); continue`, so a short run never reaches the `n < succeeded` check (line 1620) or `cell_imbalance` (line 1626); then line 1708 `if rid in KNOWN_SHORT: continue` suppresses the only problem it did raise. **A rid in KNOWN_SHORT currently receives zero checks of any kind.** Script: `.../ks/demo3.py`.
**Why it matters:** a re-run or a quota truncation of any of the 95 exempted runs would pass silently, and 28 of those 95 arms feed the committed PR-CSI-003/005/006 ranks.
**Minimal fix (do not apply):** make KNOWN_SHORT values carry the tolerated shortfall (or parse `n_failed` out of the text) and only exempt when `expect - n <= tolerated`; and move the SHORT branch's `continue` so the ledger/cell checks still run on exempted runs.

### MAJOR-2 — `dcs_document_short_runs.py` will exempt a run whose loss is far beyond `--allow-short`, and writes a false "Within the declared --allow-short 4"
**Measured by mutation.** Built `.../ks/fakerepo/` (symlinked corpus + 4 synthetic short runs) and ran a copy of the script with `REPO` repointed (`.../ks/doc_mut.py`). Its stated safety property **holds** for the reason it advertises:
- `MUTOTHER` (`failure_reasons = {"semantic_one_word:RuntimeError:CUDA out of memory": 1}`) → `REFUSED to exempt (not a pure degeneracy loss)` ✅
- `MUTMIXED` (degeneracy + OOM) → `REFUSED` ✅

But `MUTUNDER` — 620 of 670 rows, `n_rows_failed = 50`, `failure_reasons = {degeneracy: 1}` (Σ=1 ≠ 50) — was **`documented: … (620/670, 5 domains)`** and got an exemption reading: *"50 row(s) of 670 REFUSED by the sprint's own norm-match degeneracy guard … at most 10 row(s) per domain out of 10 … **Within the declared --allow-short 4.** Ledger: n_attempted 670, n_succeeded 620, n_failed 50"* — five whole domains wiped, 50 ≫ 4, and the sentence still asserts compliance.
**Why it matters:** `--allow-short 4` is a preregistered ceiling (`configs/dcs_csi_pr005_button_L18_family.json:285` "Do NOT widen --allow-short"). The documenter is the only thing writing these entries, it never compares the measured shortfall to 4, and it never checks `Σ failure_reasons.values() == n_rows_failed`. The 28 real entries happen to satisfy both — I measured it — so no committed number is wrong today. **Latent, not realized.**
**Minimal fix:** in the loop, refuse unless `sum(reasons.values()) == done["n_rows_failed"] == len(missing) <= ALLOW_SHORT`, with `ALLOW_SHORT` read from the run's config rather than baked into the template string.

### MAJOR-3 — the documenter has NO size assertion on its comparison, and will write a zero-row exemption (the S-134 pattern, again)
**Measured by mutation.** In `.../ks/fakerepo2/` I added `KO_MUTVAC_…` (669 real rows, pure degeneracy ledger) and a same-prefix 670-row "reference" `KO_ZZREF_…` whose 670 lines are the *same* `(domain, family_id)`. It is the newest by mtime, so `sorted(cands)[-1]` selects it. `.../ks/doc_vac.py` printed:
```
documented: csi1_button_train_KO_MUTVAC_20260920_180000_999111  (669/670, 0 domains)
```
and wrote the exemption: *"…against the full 670-row arm KO_ZZREF of the same allocation: the **0 lost row(s)** fall in **0 distinct domain(s)**, at most 0 row(s) per domain out of 10 … Ledger: n_attempted 670, n_succeeded 669, **n_failed 0**. Failing prompt_ids (complete): **.**"* — an exemption that self-contradicts (669 succeeded of 670 attempted, 0 failed) and an empty evidence list, written with no complaint.
**Why it matters:** this is exactly the standing lesson (S-134 PASS-on-zero-rows, S-042, R2-M5). The script computes `missing = kr - kk` and never asserts `len(kr) == expect_n` or `len(missing) > 0` before templating the evidence.
**Minimal fix:** `assert len(kr) == int(expn)` and `assert len(missing) == done["n_rows_failed"] > 0` before formatting; print both sizes on every documented run.

### MAJOR-4 — the "reference arm" is picked by mtime from a pool that is 72% wrong-layer, with no config check
`pref = rid.rsplit("_", 3)[0].rsplit("_", 1)[0]` → `"csi1_button_train_KO"`, globbed, filtered only by `rows_written == expect_n`, then `sorted(cands)[-1]` = **newest mtime**. I enumerated that pool: **83 candidate dirs, of which 60 are `rescue_layer=20`, 21 are `rescue_layer=18`, 2 are `None`.** The script asserts nothing about layer, split, codeword, donor or job; it got layer-18 references only because the layer-18 arms happened to be today's newest. Note `KO_NEC_*`-style names strip to `csi1_basket_train_KO_NEC`, but a run tagged plain `KO` would strip to `csi1_button_train`, matching `BASE` as a reference.
**Realized impact: none.** I measured it: the missing-pid set for `KO_SHUF9` against its layer-18 reference (`KO_SHUF23`) and against a layer-20 arm (`KO_AT10_…1786974`) is the **same single pid**, `missing=1, extra=0` — the prompt population is identical across layers. So the committed entries are unaffected; the safety argument is not.
**Minimal fix:** require the candidate's `config.json["args"]` to match the short run's on `rescue_layer`, `split`, `codeword`, `expect_n`, and select deterministically (e.g. sorted run_id) rather than by mtime — and name the reference by full run_id in the entry, as the hand-written XSWAP entry already does.

### MINOR-1 — template constants are asserted as measured facts
`TEMPLATE` hard-codes `DCS-CSI-133:` as the log ID for every entry (including entries written for the S-137/S-138 reads), `'REFUSING to patch: N of 28 positions'` with a literal `N`, `out of 10` (true only for 67×10 train splits), `exp = "PR-CSI-005 button L18 family" if "button" in rid else "PR-CSI-003 necessity"`, and `--allow-short 4`. Each is an unverified constant inside a string labelled "MEASURED here". Also `scripts/gates/dcs_document_short_runs.py:53` hard-codes `results\.jsonl` in the SHORT regex, so a short `retrieval_strength` run (`retrieval.jsonl`) can never be documented — safe direction, but it would look like an unfixable guard failure.

### MINOR-2 — the documenter ignores the guard's exit code
`subprocess.run(...)` without `check=`; only stdout is regex-scanned. If the guard crashes or its message wording changes, `shorts` is empty and the script prints `undocumented SHORT runs: 0` and exits 0 — a no-op indistinguishable from "nothing to do". Same class as MAJOR-3.

## (e) Guard's own tests — still live, one gap

`tests/test_run_completeness_check.py` is **unchanged this session** (0-line diff) and all 30 tests pass. The failure paths are genuinely exercised and several are explicitly mutation-hardened (`test_the_ROW_COUNT_check_fires_on_loss_the_cell_check_CANNOT_see` uses a cell-*balanced* fixture so it cannot pass through the other check; `test_an_EMPTY_scan_is_refused_rather_than_reported_clean`; `test_the_KNOWN_SHORT_run_really_IS_short_and_fails_without_its_exemption` — independently re-confirmed by my demo 3 above). `test_every_KNOWN_SHORT_entry_is_actually_flagged_by_the_scan` is the anti-staleness check and it is live (0 stale of 95).

**Gap (MINOR):** no test asserts the *magnitude* of an exempted shortfall. `test_the_KNOWN_SHORT_run_really_IS_short_and_fails_without_its_exemption` only proves the table is non-vacuous; nothing pins "this run is short by 1, and short by more than 1 must fail" — which is exactly the hole MAJOR-1 walks through. A fixture using the existing `_fake_run` helper with a rid placed in `KNOWN_SHORT` and rows far below the documented count would go red against today's code.

Scratch artifacts (mine, not in the repo): `/tmp/claude-47249/-home-sharifm-students-omeryosef-first-poc-teza-first-poc-with-mahmood/4da49896-7f0f-40cd-a8f0-50b462615089/scratchpad/ks/` — `parse.py`, `audit.py`, `audit.json`, `canfail.py`, `demo1.py`, `demo3.py`, `doc_mut.py`, `doc_vac.py`, `fakeroot/`, `fakerepo/`, `fakerepo2/`.