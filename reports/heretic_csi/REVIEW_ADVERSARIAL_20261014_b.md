# HERETIC-CSI — Adversarial review #2 (S-065 fixes, P2b analyzer, P3, P4, P2a r4 VAL, Phase B, S-066…S-081)

**Reviewer:** independent adversarial subagent, 2026-10-14 ~04:15 IDT. **Mode:** read-only on all code and data. No
commits and no SLURM jobs. CPU checks were throwaway scripts in the session scratchpad (`review2/`: `t_decide.py`,
`t_analyze.py` (a synthetic end-to-end of `p2b_analyze` with monkeypatched I/O), `chk_fac.py` (production factor
audit)). **No P2b, P4 or P2b-VALIDATION endpoint was read by this review.** I looked only at factor files, fitting-side
logs, preregs, code and the already-published P2a/Phase-B reports. The VAL run logs 1023578/9 were opened only to check
for auto-analysis. They print per-arm option mass, but no y_install.

## Severity-ranked summary

| # | Sev | Kind | Finding |
|---|---|---|---|
| 1 | **CRITICAL (P4, pre-endpoint)** | design bias | Rescaling the fitted RH8 controls to TOP8's norm moves them far off their own optimum. In-sample fitting-side net: button r1 RH8_0 **0.621 raw → 0.147 rescaled** (TOP8 0.622). Basket r1 0.568 → 0.460 (TOP8 0.568). r4: 0.618 → 0.581 and 0.659 → 0.586. Raw, the random head sets fit as well as TOP8. Only the norm-matching step makes them worse. A TOP8 "PASS" would be largely a rescaling artifact. |
| 2 | **HIGH** | BUG | `p2b_analyze` Holm over an incomplete primary family returns a PASS at the *unadjusted* p (it only adds a flag). Reproduced: with r4 missing, r1 gets "PASS (Holm p=0.0122)". `p4_analyze` has the same issue and no flag at all. Primary ranks run in separate jobs, so this is a live risk. |
| 3 | **HIGH** | BUG | The SECONDARY (CWONLY) test lacks the screens the prereg requires. (a) A collapsed CWONLY readout only raises a flag, never a VOID. (b) The CWRAND/CWDER controls get no per-module norm or rank check. (c) The CW controls get no collapse screen. Reproduced: with CWONLY median option mass 0.001, or with every CWRAND at 5× CAND's norm, the secondary still says PASS. |
| 4 | **HIGH** | design bias (P2b) | P2b fitted controls (DER/SHUF) have the same off-optimum rescaling problem. DER0 raw/CAND total-norm ratio: basket r4 **1.29**, button r4 1.10, r1 ≈1.0–1.05. SHUF0 is 1.65–3.4×. DER is the only family that tests input-side specificity (P3), and it is handicapped exactly at r4. |
| 5 | **HIGH** | interpretation | The P2b PRIMARY test (CAND vs 61 RAND + 20 fitted) is a weak bar. P3 shows that CAND writes the mean KO→clean output gap g, which is shared across domains and codewords (cos 0.84–0.94). An isotropic random rank-r edit of equal norm is known to *damage* y (S-065 smoke). So a PASS mostly certifies that "adding the mean clean−KO shift partially undoes the knockout". It does not certify an input-conditional or semantic operator. An input-independent mean-gap (steering-bias) control is missing. |
| 6 | **HIGH** | overclaim (S-073) | "Button rank-4 carrier: CONFIRMED". Button VALIDATION was read at r1 and r16 (both FAIL, S-049) *before* r4 was chosen on TRAIN and tested on VAL at the floor p = 1/57. Over the 3 VAL looks at button, Bonferroni/Holm gives 3 × 0.0175 = **0.053 > 0.05**. The "outcome-A shape / dimensionality difference" synthesis compares pass vs fail across codewords without any contrast test (difference-in-significance). |
| 7 | MEDIUM | overclaim (S-077) | The Phase-B verdict is supported by the cell-A read alone, since cell A is benign-literal, so "bomb" is not a sensible answer there. Two of the listed specificity planks are on collapsed readouts and are invalid under the sprint's own floor: the wrong-concept read (median option mass 0.139 → 0.009, 83–92% of rows < 0.05) and basket val-C (0.036). The knife/gun read also shows P(in-context concept) rising +0.29/+0.22, so "context-free" is too strong. "Generic end-of-prompt editing is NOT sufficient" generalizes from one Heretic objective whose target *is* "make A look like C at the answer position". |
| 8 | MEDIUM | P3 stats | The alignment null is isotropic, while activations are anisotropic. Dozens of "exceedances" appear at every rank and layer, which shows the null is miscalibrated, so "refusal@L16 > q99" is not evidence of specific alignment. `pls4_own_L18_mean_cos2` is compared to the 1-direction projection null, which is dimension-mismatched: correct null mean 4/4096, q99 different. That column is ~0.014–0.023, about 15–20× its null and comparable to the refusal number, yet S-079 calls PLS "≤0.023, weak". |
| 9 | MEDIUM | design | P4 ties the heads across L6–18, but TOP8 was nominated over the knockout band L6–14. At L15–18, "head 19" has no nomination basis. Symmetric for the controls, so it dilutes rather than biases. |
| 10 | MEDIUM | robustness | In `p2b_analyze`, a CW-family failure (missing dir → SystemExit, or hooks not fired → `void`) makes the PRIMARY cell NOT ANALYZABLE or VOID. Primary and secondary are coupled (`p2b_analyze.py:173-187`). |
| 11 | MEDIUM | provenance | The frozen P2a candidate basis `configs/heretic_csi/hcsi_ranksweep_button.pt` (and basket's) is **untracked in git**. The confirmed claim rests on it. sha256 now `1c586d1a…d75e9` (button), mtime 2026-10-02 15:33/16:04, so it was not modified after TRAIN. |
| 12 | LOW | various | The rank "check" is factor dimension, not numerical rank (the data are fine: numrank = r for all checked factors). `decide()` raises KeyError if `status=="ok"` without `ci95`. `cv_<cw>.json` was overwritten by the `--freeze` final fit (the table survives in `cv_<cw>_selection.json`). P3 DROP_i / TOPkN have no matched random controls. Read discipline for VAL is procedural only, with no code guard. |

---

## 1. P2b analyzer (`research/heretic_csi/p2b_analyze.py`)

**Holm (`:70-77`): OK.** Step-down with running max and cap 1 is correct. Checked: {0.0122, 0.0244} → both 0.0244.
{0.03, 0.02} → both 0.04. {0.6, 0.01} → {0.02, 0.6}. Strict `< 0.05` holds (p = 0.05 → DOES NOT PASS). Holm floors:
P2b primary 2/82 = 0.0244, secondary 2/77 = 0.026, P4 2/61 = 0.0328. P4 therefore needs TOP8 strictly first at one rank
(rank 2 at the best rank → 0.066).

**`decide()` (`:80-98`): OK** for VOID > gates > recovery-degenerate > descriptive > (Holm < 0.05 AND CI-lo > 0). Checked edge
cases: CI-lo exactly 0 → DOES NOT PASS; negative recovery at the p floor → DOES NOT PASS; degenerate recovery → CANNOT
ANSWER; descriptive rank → DESCRIPTIVE. LOW: `rec["ci95"]` raises KeyError if `status=="ok"` without `ci95` (`:90`).

**BUG-2 (HIGH) incomplete Holm family (`:236-247`).** `prim` contains only the ranks analysed in *this* call. If r4 is
absent (separate job, not finished) or NOT ANALYZABLE, `holm({1: p})` returns p unadjusted. The code appends a flag
(`:243-244`), but the verdict string is still PASS. Synthetic reproduction (`t_analyze.py` case D): r1 → "PASS (Holm
p=0.0122 …)". The primary ranks run in different jobs (1023012/1023264 = r1, 1023508/1023509 = r4), so this is the most
likely way a wrong PASS gets logged. `p4_analyze.py:99-106` has the same logic and no flag.
**Fix:** `prim = {r: (p if analysed else 1.0) for r in PRIMARY_RANKS}` (treat missing as p = 1, m = 2), or set the verdict
to "INCOMPLETE FAMILY" whenever `set(prim) != set(PRIMARY_RANKS)`. Do the same for `sec`, and in `p4_analyze`.

**BUG-3 (HIGH) secondary screens missing (`:122-126`, `:171-188`, `:255-261`).**
- The collapse screen loops over `arms`, which excludes `cwfam`. VOID applies only to `live + [cand]`, and `KO_CWONLY_r`
  (the secondary *candidate*) is in `pos_arms`, so its collapse is only a flag. PREREG_P2B_VALIDATION applies "collapse
  … on … candidate ⇒ VOID" to both tests. Reproduced (case B): CWONLY median option mass 0.001 → secondary PASS.
- CW-family norm/rank: only `hook_calls` is checked (`:185-187`). There is no `module_fro`/`rank` comparison to CAND.
  Reproduced (case C): all 61 CWRAND at 5× norm → secondary PASS, no VOID.
- The secondary recovery CI comes from `rec[KO_CWONLY]` on the primary `common` keys, while the CW rank test uses `ck`
  (possibly fewer keys). This inconsistency is only flagged.
- **Fix:** run the same collapse/norm/rank block over `cwfam ∪ {KO_CWONLY}`, with `KO_CWONLY` collapse → secondary VOID.
  Keep a separate `void_secondary` list so secondary failures do not VOID the primary (finding 10).

**Primary norm/rank checks: executed, and real.** `module_fro` in each sidecar is computed by the runner from the
factors actually applied (`p2b_runner.py:254`), including RAND, which is regenerated in the runner. The comparison
(`:142-149`) is per module at 1e-3. "Rank" is `A.shape[0]` of the first module only (`p2b_runner.py:255`), i.e. a
factor-dimension check. That is acceptable given the data below.

**Separate families: OK.** Primary Holm uses `rank_test.p`, and secondary uses `rank_test_CWONLY_vs_cw_family.p`, with
separate `holm()` calls.

## 2. S-065 fixes: did they land?

| claim | verdict | evidence |
|---|---|---|
| constructive derangement | **OK** | `p2b_fit.py:89-112`. Re-ran `shuffle_plan` on the *production* anchors (670 rows / 67 domains × 10, both codewords) for all 30 DER seeds (r ∈ {1,4}, j < 15) + 10 SHUF seeds: 0 same-domain pairs, 0 target reuse, 15 distinct DER permutations. |
| CI rule | **OK (primary)** | `decide()` above, plus mutation test. |
| collapse screen every arm | **PARTIAL** | primary arms yes. CW family and CWONLY no (BUG-3). |
| DER family, no role swap | **OK** | `p2b_fit.py:243-248` `role_swap=False`. 15 DER at r1/r4 in the saved files. |
| code provenance | **OK** | `fac/code_1023012_r0_{basket,button}/` and `code_eval_*`/`code_val_*` snapshots. The shas of p2b_fit/operator/analyze/operator_ara equal the working tree (`b31adede…`, `f2cb3f80…`, `da9d3852…`, `5b80713f…`). The preregs in `configs/` and `outputs/` are byte-identical. VAL factor sha = TRAIN factor sha (`9c2d453a…`, `96e3af94…`). |

**Saved factor audit** (`chk_fac.py`, factors_{basket,button}_r{1,4}.pt; 24 keys each = CAND, NEUT, SRC2SRC, TGT2TGT, 5
SHUF, 15 DER; 26 modules; identical module sets). Every SHUF/DER matches CAND per module to ≤6e-8 relative, with
numerical rank (rtol 1e-3) = r in all modules. RAND regenerated with seeds 7100/7160 (r1) and 7400/7460 (r4): ≤3e-8
relative, numerical rank r. SRC2SRC/TGT2TGT are exactly 0. NEUT has some 0-norm modules (expected; descriptive).
**Pre-rescale raw totals** (sum of per-module norms), against CAND = 44.9 / 55.5 / 38.9 / 60.2 (basket r1, r4, button r1,
r4):

| | DER0 raw | DER0/CAND | SHUF0 raw | SHUF0/CAND |
|---|---|---|---|---|
| basket r1 | 47.3 | 1.05 | 126.9 | 2.83 |
| basket r4 | 71.9 | **1.29** | 101.4 | 1.83 |
| button r1 | 38.9 | 1.00 | 130.6 | 3.36 |
| button r4 | 66.1 | 1.10 | 99.5 | 1.65 |

These feed finding 4.

## 3. P4 (`p4_head_fit.py`, `p4_analyze.py`, `p3p4_emit.py`)

- **Head-column restriction: OK.** `cols()` gives [128h, 128h+128) for the sorted heads. `restrict` slices
  `s_in/t_in/p_in`. `embed` writes A into those columns and leaves zeros elsewhere (`:41-55`). The same head set is used
  for every o_proj module (tied across layers). The runner applies the full 4096-column A, so the zeros hold.
- **RH8 sets: OK.** Recomputed `random.Random(4000+100r+j).sample(NON_TOP8, 8)`: 60/60 distinct and 60/60 disjoint from
  TOP8 at both r1 and r4. All 24 non-TOP8 heads are used (12–30 times each).
- **TOP8 recovery: OK.** `configs/dcs_csi_pr010_head_causal_basket.json` `head_sets.HD_TOPK = [19,17,23,6,13,2,24,28]`,
  selected by signed AtP on the TRAIN screen (`w1_screen_train_basket_916132`). `DCS_CSI_PR010_HEAD_validation.json` is
  the certification (dependence caveat correctly disclosed in PREREG_P4). There is no VALIDATION row in the P4 fits:
  `pf.load_pairs` uses the TRAIN capture.
- **Same objective and steps: OK** (`freeze_pooled.json` mse:0.3, n_steps 15, for all variants).
- **CRITICAL-1: norm matching is off-optimum.** RH8 is fitted, then `po.rescale_to(f, tn)` (`:131`) rescales it to
  TOP8's per-module norm. TOP8 itself needs about 1.8–2.3× FULLO's norm (18.3 vs 10.2 basket r1; 21.8 vs 9.3 button r1),
  so its inputs are *less* informative. In-sample fitting-side net from the job logs `outputs/heretic_csi/logs/
  p3p4_102355{4..7}.out`:

  | | TOP8 net | RH8_0 raw net | RH8_0 rescaled net |
  |---|---|---|---|
  | basket r1 | 0.568 | 0.568 | **0.460** |
  | basket r4 | 0.615 | 0.618 | 0.581 |
  | button r1 | 0.622 | 0.621 | **0.147** |
  | button r4 | 0.651 | 0.659 | 0.586 |

  At their own optimum, random 8-head sets fit as well as TOP8. Only the rescaling makes them worse. The P4 rank test
  compares TOP8 at its optimum against controls pushed off theirs, which structurally favours TOP8 (worst for button r1).
  **Fix (amend PREREG_P4 before any P4 eval):** fit RH8 *under* a per-module Frobenius constraint equal to TOP8's (for
  example, projected L-BFGS or a norm penalty with a Lagrange multiplier). Alternatively, make the raw-norm RH8 family
  co-primary, with PASS required against both. Also report the full distribution of `_summary.TOP8_rank_among_RH8_raw`
  and `_cv` from `p4_fit_*.json` once written. If TOP8 is not rank 1 among *raw* RH8 on the fitting side, say so before
  the endpoint.
- `p4_analyze.py`: there is no check that A is zero outside the declared heads, and no check that the RH8 heads are
  disjoint. Add both from the factors file. It also has the incomplete-Holm problem (BUG-2).
- Liveness prefix: `p4_template.sh` writes liveness at `hcsi_p4_<cw>_<split>_{BASE,…}` and arms at `…_r<R>_…`.
  `p4_analyze.py:24-25` reads them consistently. OK. Liveness only comes from the `LIVE=1` job.

## 4. P3 (`p3_svd_analysis.py`, `p3_write_direction.py`, `p3_make_truncations.py`)

- **SVD via QR of the factors: OK** (`:35-41`). **Effective rank** = exp(H(s²/Σs²)) (`:44-47`). This is the *energy*
  version, declared in the docstring. It is smaller than the Roy–Vetterli (s/Σs) version, so "~2 at r4" should say
  "energy-entropy".
- **Random-subspace null:** for `proj2(U_k, d)` the null Beta(k/2, (D−k)/2) with mean k/D is the right dimension
  (`:86-91`). For `pls4_own_L18_mean_cos2` (`:153`) the null mean is 4/D, not k/D, and the distribution differs. Yet
  `p3_report.py:73` compares *every* `align` key to the k-direction q99. This is a **BUG (MEDIUM)**. In addition, the
  isotropic null is not appropriate for anisotropic activation geometry. The report lists exceedances in almost every
  layer for refusal and d_surface at every rank, which is a miscalibration signature. Use an empirical null instead: the
  same statistic for DER/SHUF write subspaces, or for the top PCs of the clean outputs.
- **"CAND and fitted controls write along the same mean gap direction": computed correctly, and not a rescaling
  artifact.** `rescale_to` multiplies B by a scalar per module, which leaves U unchanged. But it is largely true **by
  construction**. DER pairs are a permutation of all rows, so DER's mean target − source equals g exactly. Any rank-1
  MSE fit of a mostly-common shift recovers g. So the finding is expected rather than structural, and its main
  consequence is correctly stated in S-079: CAND vs DER/SHUF tests read-side specificity only.
- **Truncations:** TOP{k} raw, TOP{k}N renormalized per module to FULL, DROP_i raw (`p3_make_truncations.py:119-127`).
  Renormalization is declared in `meta.renorm` and the docstring. OK. Gap: `p3p4_emit.py:34-36` creates random controls
  only for raw TOP{k}. There is no matched control for TOP{k}N or for DROP_i (necessity of component i needs a "drop a
  random equal-energy direction" control).

## 5. P2a button r4 VALIDATION (S-072/S-073)

- **Timing: OK.** `prereg_S051_rank4_validation.json` was committed in 532d220d at 2026-10-13 20:18:33 +0300. The first VAL
  dir `hcsi_p2a_button_KO_CAND_r4_20261013_221446_3159296` has RUNMETA `slurm_job_id 1022698`, `start_ts
  2026-10-13T22:14:47` (epoch 1791918887 = 22:14:47 IDT), which is about 1 h 56 m after the commit. There is one commit
  only, so the file was not edited afterwards. The 61 dirs come from job 3159296 (34 dated 1013, 27 dated 1014).
- **Population: OK.** VAL r4 has 230 rows / 23 domains; TRAIN-K4 r4 has 268 / 67. **0 domain overlap and 0 prompt-id
  overlap.** argv uses `exclude_button_bomb_sow_validation.txt`, seed 20260913, `--rescue-basis
  configs/heretic_csi/hcsi_ranksweep_button.pt --rescue-basis-key cand_pls4`.
- **Remaining ways it could be wrong or overstated:**
  1. **Multiplicity across VAL looks (HIGH, finding 6).** S-049 had already read button VAL at r1 (18/57) and r16 (10/57).
     r4 was chosen on TRAIN after those failures. For the hypothesis "button has a specific carrier at some tested
     rank", VAL has been consulted 3 times. With p at the 1/57 floor, no correction can survive (3 × 0.0175 = 0.0525).
     The S-051 prereg treats r4 as a fresh single hypothesis. That is defensible only if the claim is scoped to "rank 4
     specifically, nominated on TRAIN". The "CONFIRMED" wording should carry this caveat.
  2. p is at the floor and the margin is 1.2 control-SD. A fresh-draw control family would give an uncorrelated second
     estimate (descriptive).
  3. The candidate basis file is untracked in git (finding 11). Commit it, or record its sha in the claim table.
  4. The control construction for r4 matches r1/r16, per the verifier (all 57 arms rank 4, norm-matched exactly, seed
     20260913). Not re-derived here.

## 6. Phase B verdict (S-077)

**Adequately supported for the narrow claim** "Heretic-native last-position ARA, tuned this way, installs a bomb answer
bias". The decisive read is cell A: benign-literal prompts go from y 0.000 → 0.925 / 0.796, with Δlogp(bomb) +13.9 nats,
and option mass is not collapsed on A. **Overclaims:**
- Plank 2 (wrong concept: knife/gun) runs on a **collapsed readout** (median option mass 0.139 → 0.009, 83–92% < 0.05).
  Under the sprint's floor rule it is not readable. Also P(knife) rises +0.289 and P(gun) +0.215, so the edit also boosts
  the in-context concept. "Context-free" overstates this; "predominantly a bomb bias" is better.
- Plank 3 (C falls) for basket is also on a collapsed readout (val_C option mass 0.036). Only button's −0.111 (option mass
  0.213) is readable. The cross-codeword read shows button's edit *raises* basket val_C by +0.53, so "damages installed
  prompts" is not general.
- "Generic end-of-prompt operator editing is NOT sufficient": the Heretic ARA objective maps A-states to C-states *at the
  answer position*, so an answer bias is the expected optimum of this objective. That shows the objective is wrong for
  installation. It does not show that no end-of-prompt edit can install. Scope the verdict to "native ARA as shipped".

## 7. Read discipline: basket P2b VALIDATION (1023578/9) running before the TRAIN read

- PREREG_P2B ("frozen operators only, after TRAIN read") and PREREG_P2B_VALIDATION constrain *reading*, not running.
  Running early also locks the VAL plan. **No auto-analysis found:** `p2b_job.slurm` and `val_template.sh` call only the
  runner. `p2b_analyze`/`p4_analyze` are invoked nowhere in slurm/plans (grep). The only analyzer references are the
  P3 truncation gates, which require a VAL verdict JSON.
- **Leak surface (LOW):** the job logs print per-arm option-mass medians (`p2b_1023578.out`), and each run dir's
  `summary.json` is readable during ops ticks. The discipline is therefore procedural only.
  **Fix:** make `p2b_analyze --split validation` refuse unless `reports/heretic_csi/p2b_<cw>_primary_train.json` exists
  and its mtime predates the call (log the check). Ops ticks should not open VAL `summary.json`.
- Factor identity: the `val_factors_sha_*` files equal the TRAIN factor shas. OK.

## 8. Overclaim audit S-066…S-081

- **S-073** "CONFIRMED … specific rank-4 carrier": see §5.1 (VAL multiplicity). "Outcome-A shape: basket carrier at r1,
  button needs ~4" rests on a floor-sensitive basket r1 pass and a button r1 fail, with no basket-vs-button contrast test.
  It also treats r16 FAIL as "neither is specific", which is absence of evidence. **Downgrade to "consistent with".**
  "Carrier" means sufficiency of a patched subspace for 9% of rescue, not a representation claim. Keep the "specificity,
  not magnitude" wording everywhere.
- **S-074/S-075**: TRAIN-K4 is in-sample, and the parent note is correct. The upcoming P2b TRAIN read must be labelled
  "in-sample; CAND fitted on these rows, RAND not fitted".
- **S-077**: §6.
- **S-079**: "No preference for the inherited 8-head circuit" is weight geometry of a fit whose read side is driven by
  KO-vs-clean input variance. It is not evidence about the circuit's causal role. TOP8 also needs ~2× FULLO's norm, which
  is mild dis-preference on the fitting side. "Refusal direction at L16 > random 99th pct" is uncorrected for multiplicity
  (13 layers × 2 comps × 3–4 references × 6 ranks) and uses an isotropic null (§4). "Largest alignment = refusal" omits
  the PLS-4 column, which has a similar magnitude.
- **S-076/S-078/S-079 fitting-side gap-closures** (0.594, 0.677, 0.571 vs 0.575) are in-sample fitting diagnostics. They
  are labelled as such. OK.
- **Cross-hardware:** Phase B ran on L40S. P2a/P2b eval ran on a5000. P4/P3 fits ran on CPU (thread count changes the
  TOP8 norm by 0.04%, disclosed). No cross-hardware *comparison* is made in S-066…S-081. OK.
- **"Mechanism" wording:** S-077 item 5 says "mechanistically expected". Acceptable as a hypothesis. No mechanism claim
  found elsewhere.

## 9. Tests

`poc_stage2`: `python -m pytest research/heretic_csi/tests -q` gives **35 passed, 1 skipped in 7.3 s** (skip = heretic
importorskip). The existing tests cover none of BUG-2/BUG-3. Add the three synthetic cases from `t_analyze.py` (missing
primary rank, collapsed CWONLY, mis-normed CW family) as regression tests.

## Concrete fix list (in priority order, all before the corresponding endpoint read)

1. P4: amend PREREG_P4. Replace post-hoc rescaling with norm-constrained RH8 fits, or add a raw-norm RH8 co-primary
   family. Report TOP8's rank among raw RH8 (fitting side) before any eval.
2. `p2b_analyze`/`p4_analyze`: Holm with missing primary rank treated as p = 1, or force verdict INCOMPLETE.
3. `p2b_analyze`: secondary VOIDs (CWONLY collapse), CW-family norm/rank/collapse checks, separate `void_secondary`.
4. P2b: report a DER-only rank test with DER at *raw* norm (descriptive), next to the norm-matched one. Add (or
   at least plan) an input-independent mean-gap bias control, so that a PASS can be attributed to input-conditional
   structure.
5. Re-word S-073 (VAL multiplicity; no cross-codeword contrast test) and S-077 (collapsed planks; objective-scoped).
6. P3: empirical (DER/SHUF or data-PC) null and correct the pls4 null. Add controls for TOP{k}N and DROP_i.
7. Commit `hcsi_ranksweep_{basket,button}.{pt,json}` (or record their sha256 in the claim table). Add a code guard for
   VAL-after-TRAIN reads.
