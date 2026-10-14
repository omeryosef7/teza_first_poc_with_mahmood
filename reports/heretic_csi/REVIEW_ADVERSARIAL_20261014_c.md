# HERETIC-CSI — Adversarial review #3 (S-083…S-095: P2b amendment 3, P4 v2, F6 powered re-test, P6 prep)

**Reviewer:** independent adversarial reviewer (+2 read-only sub-reviewers for F6 and P6), 2026-10-14. **Mode:** read-only.
No repo file other than this one written; no commits; no SLURM submissions. **No P2b / P4 / P2a-r4ext endpoint was read**
(no analyzer run on any production run dir; only factor files, meanbias files, preregs, code, already-published P2a/P3
reports, and synthetic inputs). Throwaway scripts: session scratchpad `review3/` (`fin.py`, `fin4.py`, `mb.py`),
`review3/f6/` (`z.py`, `cmp.py`, `rm.py`), `review3/p6/` (`resolve_all.py`, `diff2.py`, `drawtest.py`, `zipf.py`, …).

## Severity-ranked summary

| # | Sev | Kind | Finding |
|---|---|---|---|
| 1 | **HIGH** | BUG (published number) | **S-085 contrast is wrong.** `p2a_powered_contrast.py:23-24` averages each arm over its *own* surviving rows (`verify_s049.per_domain`, `verify/verify_s049.py:78-83`) — no key intersection across arms, unlike the frozen analyzer (`scripts/dcs_csi_subspace_analyze.py:600-605`). Several RAND_r1 arms are 1–2 rows short. Intersected (= frozen reports' n_keys_common 133 / 193): basket r1 z **3.08 → 6.68**, button r1 **0.54 → 0.78**, r4 unchanged ⇒ **I = 6.09 [1.39, 7.36]**, not 2.74 [0.27, 4.40]. Reproduced (`review3/f6/z.py`). |
| 2 | **HIGH** | interpretation (S-085) | The interaction sign depends on the control family. z over the mixed 46 RAND + 10 SHUF family conflates two nulls with very different means. RAND-only: basket 8.74→13.37, button 0.74→4.33 ⇒ **I = −1.04**; SHUF-only I = 2.96; pooled 6.10. Under pooled/SHUF, I>0 is driven largely by basket z *falling* r1→r4. "Button gains specificity r1→r4 much more than basket" is **not supported**. |
| 3 | **HIGH** | BUG (P2b + P4 Holm) | A **VOID / CANNOT-ANSWER primary rank still enters Holm with its real p** (`p2b_analyze.py:307,310`; `p4_analyze_v2.py:117-119`). Synthetic: r1 VOID (candidate collapsed) with p=1/82, r4 p=0.03 ⇒ **r4 "PASS (Holm p=0.03)"**, no INCOMPLETE flag; same with r1 gates failing; same in P4 v2 (r4 "PASS (Holm p=0.0328)"). An invalid p from a voided test relaxes the other rank from α/2 to α. Also secondary: a rank with `void_shared` (e.g. KO_IDENT≠KO) is still in `sec_have` (`:308-309` checks only `void_secondary`) ⇒ other rank's secondary PASSes at unadjusted p=0.03. Amendment 3 says "a VOID secondary rank counts as missing" — primary is inconsistent with that. |
| 4 | **HIGH** | BUG (P6 bottle bank) | `bottled` / `bottling` in TRAIN pool sentences (`juice_bottling`, `winery_cellar`) evade the generator's `\bbottles?\b` screen (`src/boombness/prompt_families.py:1340`) but the extractor's `resolve_occurrences` (`extract_boombness.py:303-311`) counts an extra codeword-token occurrence (`occurrence_count_mismatch:text=5,tokens=6`). 7 behavioral n4 extraction rows + 3 C/sow/n4 rescue rows (+siblings) affected; intervened TRAIN arms will hit the FATAL knockout pre-flight (`score_behavior.py:2283-2290`); domain-level exclusions don't remove them. `p6_check_banks.py` never runs `resolve_occurrences` (40-row sample only), and its docstring claim "whole-word hits after repair = 0" is not implemented. 384 bank rows contain `bottl(ed\|ing)`. |
| 5 | MED-HIGH | design (F6 powered re-test) | All 144 new controls are RAND. The family moves from 46R+10S (18% SHUF) to 190R+10S (5% SHUF), and SHUF is the stronger null: at button r4, SHUF mean recovery is 0.0038 vs RAND 0.0011 (candidate 0.0129); at r16 the SHUF mean (0.020) exceeds the candidate (0.0168). The powered p resolves the floor only against the random-geometry null. Against shuffled-label PLS, n is still 10 (floor 0.091), and "rank ≤3/201" can PASS with 2 SHUF above the candidate. |
| 6 | MEDIUM | design (P2b MEANBIAS) | The MEANBIAS comparator can be weak or invalid, but it is what unlocks the "input-conditional" wording rule (CAND − KO_MEANBIAS CI-lo>0). (a) KO_MEANBIAS adds the codeword-row gap g at **every** row/position, including option tokens, at natural norm (Σ‖g‖ 46/53). It is likely to overshoot or damage, so CAND can beat it without being input-conditional. (b) The add-on analyzer (`p2b_analyze.py:267-299`) has **no collapse, hook or module-set VOID** for MEANBIAS arms. A collapsed KO_MEANBIAS readout would make CAND−MEANBIAS>0 trivially. |
| 7 | MEDIUM | overclaim (S-089 / P3 v2) | "NO alignment" / "does NOT re-discover d_surface/refusal/probe axes". The anisotropic null is **super-uniform**: the min p_aniso over all **924** statistics (14 cells × 66) is **0.27**, so it is conservative, not calibrated. The q99 of the projection² ranges 0.06–0.61 (median 0.28), i.e. a direction needs **\|cos\| ≳ 0.53** (median cell) to be detectable. The "not powerless" argument only covers perfect alignment. The P3 report's max q99 is 0.61, not the logged 0.54. |
| 8 | MEDIUM | design (P6) | The DEV draw can return **fewer than 5** codewords, against the frozen spec (`p6_dev_draw.py:9-10`, one per non-empty cell). It happens in 37/300 random survivor sets of size 5–20 and 23/2000 with ≥12 survivors. The test covers only the all-survive case. Candle is always in DEV even if it fails G1–G3 (`:53`). |
| 9 | MEDIUM | confound (P6) | Repairs give each codeword its own pool. Rows differing from basket (of 22,272): bottle 432, chair 276, curtain 180, blanket 138, jacket 120, balloon 102, cushion 96, … 0 for kettle/pencil/wagon/sponge/saddle/button (16 banks are effectively repaired, not 17). The number of repaired rows correlates with Zipf (the H6b covariate): **Spearman 0.51, p=0.02**. Some repairs are odd ("fire quilt", "life coats", "bomb tape", "cake taper", "kite floated") and shift frequency (flask, drape, pail; "seat" is ambiguous). Basket/button bytes are unchanged (OK). |
| 10 | MEDIUM | stats (P6) | Power is overstated: `p6_power.py` uses one-sided α=0.05, but H6b is two-sided and Holm's first step is α=0.025. The UNDERPOWERED threshold of 12 is therefore optimistic. H6a probe-ρ and the VAL rescue z share the same VALIDATION domains and base readout (`p6_heldout_probe.py`), so shared noise can inflate Spearman. |
| 11 | LOW-MED | provenance (F6) | The new r4ext jobs contain **no overlap arm**, and the candidate/BASE/KO are reused from 1022698. A cross-job readout offset would hit all 144 new controls and none of the old arms. Code, args, GPU type (a5000), env and seed match, but the model is now staged from the scratch mirror. The analyzer's per-row written-norm check would catch an L18-delta drift but not a downstream readout offset. The r4ext meta lacks `selected_layer`/`codeword`, so the scorer's layer/codeword guards (`score_behavior.py:2372-2385`) are skipped. |
| 12 | LOW-MED | P4 v2 | `p4_analyze_v2` docstring claims "sidecar norms match the file". The implementation checks only the factors-file **basename** (`:88`), not `factors_sha16` and not module_fro. The basket VALIDATION P4 read re-uses the population that certified TOP8 (D32). This is declared in PREREG_P4 `dependence_caveat`, but any basket-VAL P4 wording must carry it. |
| 13 | LOW | misc | The meanbias file (mtime 04:35/36) postdates the amendment-3 commit (04:34) and its sha is not frozen in the prereg (only in the log). The file is deterministic from TRAIN captures. INCOMPLETE verdict strings contain the substring "PASS" (risk for grep-based tallies). Bottle repair writes lowercase sentence starts (12 rows). `p6_install_strength.py:15` tests `not in "AC"` (substring). S-083's "1022698 started 22:14:47" is the arm start: the job started 20:18:39, 6 s after the prereg commit. Log clock labels are out of order (S-086 05:20 before S-087 04:40). |

---

## 1. P2b amendment 3 (`research/heretic_csi/p2b_analyze.py`, `p2b_meanbias.py`, runner `bias`/`opraw`)

**MEANBIAS construction: OK.**
- **TRAIN only, enforced in code.** `p2b_meanbias.py:26-31` uses `p2b_fit.load_pairs`, which raises unless every KO row's domain is `train` (`p2b_fit.py:77-78`), and refuses clean captures without a KO partner (`:84-85`). Meta: 670 pairs / 67 domains.
- **Definition and sign: correct.** It computes `mean_i(clean.acts[n]["cw"][1] − ko.acts[n]["cw"][1])`, where index 1 is the module OUTPUT (`p2b_fit.py:126`: `src[1]` = s_out). The fit's source is KO and its target is clean (`p2b_fit.py:121`), so g = clean − KO is the fit's own gap direction. `BiasHooks` (`p2b_operator.py:287-299`) **adds** g to the module output, which pushes KO toward clean. The sign is right.
- **Modules: match CAND.** The meanbias keys equal CAND's 26 modules for both codewords at r1 and r4 (`review3/mb.py`). Total norms are 46.19 (basket) and 53.08 (button), with per-module norms from 0.69 to 3.25.
- **No VAL rows used.** The VAL add-on plan uses the same TRAIN `meanbias_<cw>.pt` (`addon_template.sh`). The add-on prefixes equal the main-arm prefixes (`hcsi_p2b_<cw>_k4/_val`), as `--addon` requires.

**opraw: OK.**
- `rescale_to(fac, raw_fro)` is an exact per-module inverse; the relative error is ≤6e-8 for DER/SHUF at r1 and r4 on both codewords.
- The stored controls equal CAND's norms to ≤6e-8.
- Raw/CAND ratios reproduce review #2: basket r4 DER0 1.294; SHUF0 1.65–3.36.

**INCOMPLETE FAMILY: fixed for missing / NOT ANALYZABLE ranks, not for VOID ranks.**
- Missing or NOT ANALYZABLE ranks → INCOMPLETE. Correct and regression-tested.
- **BUG #3 (table):** `prim_have` includes ranks whose verdict is VOID or CANNOT ANSWER. Fix:
  ```python
  prim_have = {x["rank"]: x["rank_test"]["p"] for x in analysed if x["primary"]
               and not (x["void_shared"] or x["void"]) and gates_ok(x)}
  ```
- Likewise, `sec_have` must also exclude rows with `void_shared` or failed gates.
- Add regression tests for the four synthetic cases in `review3/fin.py`.

**VOID lists: separated correctly.**
- **Shared:** liveness collapse and KO_IDENT go to `void_shared`.
- **Primary-only:** CAND collapse, the CAPOP replay and BASE_CAND hooks go to `void`, and the family norm/rank check goes to `void` (`:186`).
- **Secondary-only:** CWONLY collapse and hooks go to `void_secondary` (`:163-164`, `:181`). The CW-family norm/rank/hook check goes to `void_secondary` (`:252`), and a missing CW family is caught as `SystemExit` → `void_secondary` (`:264-265`).
- **Recovery keys:** the secondary recovery uses the same keys `ck` as the secondary rank test (`:261`). OK.
- **Remaining coupling (acceptable, declared shared):** a missing *primary*-family dir raises at `:142` before the secondary block, which makes both tests NOT ANALYZABLE.

**MEANBIAS as comparator: RISK (#6).** Recommendations:
- Pre-state that "input-conditional" requires CAND to beat **both** KO_MEANBIAS and KO_CWMEANBIAS (or the better of the two, per domain).
- Add the collapse and hook VOIDs for the add-on arms.
- Report BASE_MEANBIAS damage next to it.

## 2. P4 v2 (`p4_head_fit_v2.py`, `p4_analyze_v2.py`, `p3p4_emit.py`, `PREREG_P4_AMENDMENT_1.json`)

**NC reparametrisation: correct.**
- `scale = c/sqrt(tr((AAᵀ)(BᵀB)))` (`p4_head_fit_v2.py:50-52`) equals c/‖BA‖_F, because ‖BA‖²_F = tr(AᵀBᵀBA) = tr(AAᵀBᵀB).
- `c = tn[name]` = TOP8's per-module Frobenius norm. It is computed from the embedded TOP8 in fit mode (`:145`) and from the fold-TOP8 in CV mode (`:110`).
- The scale is folded into B on output (`:71`).
- A hard per-module check at 1e-4 raises on violation (`:165-167`), and the analyzer re-checks at 1e-3.
- The preserve and steer terms both use the scaled delta. The initialisation is at the RAW optimum, which is v1's rescaled point.

**IUT + Holm: valid.**
- `p_r = max(p_RAW, p_NC)` is a valid intersection-union test under any dependence. RAW and NC deliberately share head sets, and the IUT needs no correction for that.
- Because RAW is fitted at its own optimum by the same procedure as TOP8, a constrained-fit handicap of NC cannot cause a false PASS: TOP8 must also beat RAW.
- Holm over ranks is valid under arbitrary dependence.
- The strict 4-test Holm floor (4/61 = 0.066) is reported correctly as non-decisive.
- **Leakage:** none found on the TRAIN-K4 path (fits are symmetric in-sample on TRAIN for all arms). The basket-VAL head-selection dependence is declared (#12).

**Prefixes: consistent.** `p4v2_template.sh` uses `PFX=hcsi_p4v2_<cw>_<split>` for liveness and `${PFX}_r${R}` for the operator arms. The analyzer reads `{prefix}_{live}` and `{prefix}_r{r}_{arm}` (`p4_analyze_v2.py:60-61`).

**Bugs:**
- The VOID-rank-in-Holm bug (#3) is present (`review3/fin4.py`).
- The sidecar sha/norm check is not implemented (#12).

**Status:** the P4 v2 factors don't exist yet (fits 1023752–59 are running), so there is nothing to audit numerically.

## 3. F6 powered button r4 re-test (sub-reviewer, spot-checked)

**Holm family {r1, r4ext, r16}: correct.**
- The as-recorded values verify: r1 rank 14/57 → 0.2456 (job 968534); r16 rank 10/57 → 0.1754 (968535). Each is p = rank/(n+1) over 56 controls.
- sacct shows exactly 3 button VAL sweeps were ever run.
- The threshold 0.05/3 = 0.0167 is equivalent to rank ≤3/201 (3/201 = 0.0149; 4/201 = 0.0199). Correct.
- Extending the controls after the first look does not inflate size: the final event's null probability is ≤ 3/201.

**Control generation: identical in distribution.**
- Same code path as `scripts/dcs_csi_axis.py:466-468` (`randn(4,4096,f64)` → QR → f32).
- Orthonormality error is ≤4.4e-9.
- Candidate-overlap distribution: old vs new KS p = 0.93; the mean (~9.8e-4) matches 4/4096. No duplicates.
- `cand_pls4` is byte-identical.

**Cross-job pooling: mostly sound.**
- The same score_behavior/arm_runner code (unchanged since 09-23), env, a5000 GPU type, seed 20260913, flags and exclusion file are used.
- BASE, KO and the candidate are reused, so the option-mass key set is identical.
- 968535 and 1022698 give bit-identical liveness values across nodes.
- **Gaps:**
  - #11: no overlap arm; the model is staged from the scratch mirror.
  - #5: the null composition shifts toward RAND.
  - The analysis population could shrink silently. Pre-state that n_keys_common must equal 203.

**S-085 contrast:** BUG #1 and RISK #2. I reproduced the corrected numbers myself.

## 4. P6 prep (sub-reviewer, spot-checked)

- **Envelope exclusion: mechanical.** It is the generator's `--strict` article refusal (`prompt_families.py:208-241`). No envelope GPU output exists. All other codewords are consonant-initial ("yogurt" is /j/), and no repair word is vowel-initial.
- **DEV draw: deterministic.** The output is identical across PYTHONHASHSEED values and input orderings. The frozen Zipf values match wordfreq, and the tertiles are 7/7/6. Installer strength is computed from the base readout only (TRAIN C−A), before any rescue, so it uses pre-rescue covariates only. **But:** see #8, which needs a fill rule.
- **Stage 0 → axisfit: statically compatible.**
  - The extraction argv equals the incumbents' except `--layers 18` and `--model`.
  - It writes `cache/multiposition_reps.pt` with site `rel-6` and `layers=[18]`, plus `results.jsonl` (single behavioral query_kind, dose 4) and `bank_file_sha16`. That is exactly what `lpm.load_corpus` / `dcs_csi_axis.py --force-layer 18` need.
  - The control counts are 46 + 10.
  - Not yet run end-to-end. Run one codeword first, as S-092 already says.
  - `--rank-controls 1,4,16` vs the incumbents' `1,2,4,8,16,32` changes the RNG stream for the r4/r16 controls. The r1 stream is the same.
- **Disk: safe.** Banks, extractions and axes are on `/specific/scratches`; the model is staged to node `/tmp`. Repo footprint: ~5 MB per readout, plus ~0.6 GB transient per L18 extraction until it is moved. A preempted (`--no-requeue`) job leaves a partial dir in `outputs/boombness/extract_boombness/`.
- **Slurm paths:** the scripts live in `research/heretic_csi/slurm/`, not top-level `slurm/`.

## 5. Read discipline: OK

- No `reports/heretic_csi/p2b_*` or `p4v2_*` files exist.
- No `*analy*` file exists under `outputs/heretic_csi/p2b/`.
- No json under reports/outputs newer than amendment 3 is an endpoint; the only new ones are the P3 v2 and P6 bank checks.
- `p2b_job.slurm` and `p2b_runner.py` contain no analyzer call and no y_install computation. The VAL jobs 1023578/9 are still running and are not auto-analyzed.
- No r4ext job has been submitted.
- The amendment-3 and P4-amendment config copies are byte-identical to the prod copies. `research/heretic_csi` has no uncommitted diffs.

## 6. Overclaim audit S-084…S-095

- **S-085: must be corrected (append-only).**
  - The numbers are wrong (#1). The population is mislabelled: the r1 analysis population is 133/193, not 145/203.
  - The directional reading is not robust to the null family (#2).
  - The contrast form was chosen after seeing r1 FAIL / r4 PASS, so it is post hoc even though S-084 labelled it descriptive.
  - Suggested wording: "Descriptive basket-vs-button interaction is null-family-dependent (RAND-only I<0; pooled/SHUF I>0, partly driven by basket's r1→r4 z decrease); no support for a dimensionality-difference reading."
- **S-089 "NO alignment" / H3 "does NOT re-discover": overclaim (#7).** Replace with: "no alignment detectable against a conservative covariance-shaped null (min p 0.27 over 924 stats; detectable only for \|cos\| ≳ 0.25–0.78 by cell)". H3 stays OPEN.
- **S-089 fitting-side finding** ("random 8-head sets fit as well as TOP8"): accurately scoped as fitting-side and in-sample. OK.
- **S-092** "17 repairs … new banks equal the incumbents' shape except the repaired sentences": byte-true. But 16 banks are effectively repaired, the bottle bank still has token-level collisions (#4), and the repair load correlates with Zipf (#9).
- **S-086 wording rule:** sound in intent, but it rests on a comparator lacking VOID screens (#6).

## 7. Tests

`pytest research/heretic_csi/tests -q` → **49 passed, 1 skipped** (47 s). There is no test for a VOID rank inside the Holm family (P2b or P4), for the DEV-draw fill rule with fewer than 5 cells, or for a full `resolve_occurrences` bank sweep.

## Concrete fixes (in order, all before the affected read)

1. **`p2b_analyze.finalize` and `p4_analyze_v2.finalize`:** treat a VOID, gate-failed or CANNOT-ANSWER primary rank as missing (p=1 → INCOMPLETE). Do the same in `sec_have` for `void_shared` and gates. Add the 4 regression tests. Freeze this as an amendment before the P2b TRAIN read.
2. **S-085:** append a correction with the intersected keys (I = 6.09 [1.39, 7.36]) and the RAND/SHUF/pooled table. Withdraw the directional reading. Fix `p2a_powered_contrast.py` to intersect keys.
3. **F6 prereg amendment, before any r4ext read:**
   - Report the SHUF-only rank, and require the candidate to rank above every SHUF control (or add new-seed SHUF fits).
   - Add 1–2 overlap arms (KO, KO_CAND_r4, an old RAND) under a distinct prefix as a byte-identity check.
   - Require n_keys_common = 203.
4. **P6 before bottle Stage 0:**
   - Add a full `resolve_occurrences` sweep to `p6_check_banks.py`.
   - Repair `bottled`/`bottling` or add a declared row exclusion.
   - Amend the DEV-draw fill rule and the candle-fails-gates rule.
   - Preregister a sensitivity analysis that drops repaired rows (or uses repair count as a covariate).
   - Recompute power two-sided at Holm α.
5. **P2b add-on:**
   - Add collapse, hook and module-set VOIDs for the MEANBIAS arms.
   - Require "input-conditional" wording to beat both KO_MEANBIAS and KO_CWMEANBIAS.
   - Record the meanbias sha256 in a frozen file.
6. **S-089 / H3 wording:** use the scoped wording in §6. Optionally add a planted-partial-alignment power check (\|cos\| = 0.3 / 0.5).
7. **P4 analyzer:** check `factors_sha16` against the file's sha, and the sidecar module_fro against the file.
