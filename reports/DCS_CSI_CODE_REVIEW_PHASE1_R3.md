# DCS-CSI Phase-1 adversarial code review — ROUND 3

Scope: everything changed since `DCS_CSI_CODE_REVIEW_PHASE1_R2.md`.
`scripts/dcs_csi_subspace_analyze.py` (whole file, with emphasis on `arm_key_values`, the cross-arm
key intersection, `reference_key_set`, the VOID block, `holm`, the one-sided specificity wiring and
the new P1-i rank verdict), `scripts/dcs_csi_rederive_patch.py` (`exact_signflip_one_sided`,
`strict_run_dir(allow_short=…)`, `slurm_node_for_job` + `run_dir_in_job_window`),
`scripts/dcs_csi_known_short.py` (whole file).

**Bottom line.** The R2 BLOCKER and the four R2 MAJORs that were actioned are genuinely fixed and I
re-verified each one numerically: the option-mass floor is now a single reference key set applied to
every arm, the cross-arm `(domain, slot)` intersection is real and every contrast is computed on
exactly one key set, `KO_SELF` is no longer exempt from the liveness VOID, the arm-identity block
fires, and the norm-match check is now per-`prompt_id` and has teeth. `exact_signflip_one_sided` is
**arithmetically correct** (400 brute-force cases, 0 mismatches). `holm` is **correct** (3000
randomised cases, 0 mismatches). `strict_run_dir(allow_short=…)` is **correct** (5 constructed
cases). The `reference_key_set` / tuple-return suspicion in the brief is **refuted**.

What is wrong is the **verdict layer**, which is new. The preregistered PRIMARY as implemented
**cannot return PASS at this sprint's number of controls**, and on the way to saying so it prints a
sentence that is factually false about the data. Separately, every p-value in every shipped artifact
is published beside an "attainable floor" that is ~15 orders of magnitude below the floor the test
that actually ran can reach, and four of the shipped rank-5 control p-values are *exactly at* that
unreported floor. And the two splits are adjudicated by two different primaries, one of which the
code's own comment calls "not a verdict".

Scratch scripts (deleted after the run): `a1.py`–`a9.py` (artifact forensics, brute-force
references), `harness.py` + `t1.py`–`t5.py` (synthetic run-directory harness driving the real
`main()`).

---

## BLOCKER

### B1. The P1-i rank verdict can never return PASS at n ≤ 19 controls, and its FAIL text asserts the opposite of what the data show
`scripts/dcs_csi_subspace_analyze.py:532` (`candidate_rank_among_controls`), `:565-581`
(the verdict), specifically `:574` (`if rank == 1 and rank_p < 0.05:`) and `:578-581`.

```python
rank, n = dist["candidate_rank_among_controls"], dist["n_controls"]
rank_p = rank / float(n + 1)
...
if rank == 1 and rank_p < 0.05:
    out["VERDICT"] = "PRIMARY PASSES ..."
else:
    out["VERDICT"] = ("PRIMARY DOES NOT PASS on split=%s -- the candidate ranks %d of %d in its own "
                      "control distribution (rank p=%.4g, attainable floor %.4g). It is INSIDE the "
                      "controls, not above them." % ...)
```

The best attainable `rank_p` is `1/(n+1)`, reached exactly when `rank == 1`. So the PASS branch
requires `1/(n+1) < 0.05`, i.e. **n ≥ 20 controls**. The shipped runs have n = 10 (rank-1 candidate,
`rank_p_floor = 0.0909`), n = 8 (rank-5 candidate, `0.1111`) and n = 4 (`0.2`). **The PASS branch is
dead code on every run in the record.** The preregistered primary is a test with zero power: it
returns "DOES NOT PASS" for every possible dataset.

Worse, the `else` branch is the one that fires at `rank == 1`, and it then prints
*"It is INSIDE the controls, not above them."* — which at rank 1 means the candidate strictly
exceeded **every** control and is the exact opposite of the truth. That sentence is the VERDICT line
a reader quotes.

*Verified end-to-end* (`t1.py`, synthetic 16-arm set driving the real `main()` with the real
`lpm.load_split`, 20 train domains × 5 slots). Candidate recovery +0.07049; all ten controls between
−0.00593 and −0.00164; PRIMARY point +0.07692, CI [0.07021, 0.08429], `n_pos = 20/20`,
`p_two_sided` at the sampler's resolution bottom; every gate `true`; `VOID: []`:

```
crd  {"candidate": 0.07049,
      "controls": {"KO_RAND0": -0.00194, ..., "KO_SHUF3": -0.00164},
      "candidate_rank_among_controls": 1, "n_controls": 10, "rank_p_floor": 0.0909}
VERDICT  PRIMARY DOES NOT PASS on split=train -- the candidate ranks 1 of 11 in its own control
         distribution (rank p=0.09091, attainable floor 0.0909). It is INSIDE the controls, not
         above them.
```

A candidate that beats every control by an order of magnitude is published as a FAIL with a false
explanatory clause.

*Wrong number / wrong claim:* the shipped headline "(b) the rank-1 candidate ranks 4th of 11 in its
control distribution and **fails the primary** on both splits" is uninformative as stated: the test
returns FAIL unconditionally, so "fails the primary" carries no evidence. The rank-4-of-11 fact is
real and is the thing worth reporting; the *verdict* built on top of it is not.

*Fix:* three separate changes.
1. Decide the α the design can afford **before** running, from `rank_p_floor`. Either raise the
   control family to n ≥ 19 (the code already builds 10, so 19 is a scheduling question, not a
   design one), or state the test at the attainable level (`rank_p ≤ rank_p_floor` i.e.
   "strictly the largest", reported as an exact one-sided permutation p of 1/(n+1)) and say so.
2. Refuse rather than FAIL when `rank_p_floor > 0.05`: this is the repo's CANNOT-ANSWER shape
   ("the control family is too small for the preregistered α; no verdict"), not a negative result.
3. Make the FAIL text conditional on `rank > 1`. At `rank == 1` it must not say "INSIDE the
   controls".

---

## MAJOR

### M2. `p_floor` is the **exact-enumeration** floor but the test that actually ran is Monte-Carlo; the published floor is ~15 orders of magnitude too low and `p_at_its_floor` is permanently dead
`scripts/dcs_csi_rederive_patch.py:206` + `:227` (one-sided), `:243` + `:267` (two-sided);
consumed at `scripts/dcs_csi_subspace_analyze.py:479-481` and `:556`.

Both sign-flip functions compute `floor = 1/2**k` (one-sided) or `2/2**k` (two-sided) from the
number of informative domains, then fall through to a 200 000-draw Monte-Carlo sampler for `k > 16`
whose smallest returnable p is `(0+1)/(N+1) = 1/200001 = 4.99997e-06`. The reported `p_floor` is
never updated to the sampler's resolution.

With k = 67 (train) the artifact carries `p_floor: 1.355e-20` beside `test_mode: monte-carlo(200000)`.
The standing rule this repo wrote for itself — "a p at its floor means the test ran out of
resolution, not that the effect is infinitely strong" (`exact_signflip` docstring) — is therefore
**never enforceable**: `p_at_its_floor = abs(p - p_floor) < 1e-12` (`:481`) is `False` for every
contrast with k ≥ 18, including ones that are literally at the resolution bottom.

*Verified on the shipped data.* `reports/DCS_CSI_SUBSPACE_button_train_rank5.json`, four of the
eight specificity controls:

```
KO_R5RAND0/1/3/4   p_one_sided = 4.9999750001249995e-06 = 1/200001   (zero hits in 200 000 draws)
                   p_one_sided_floor reported = 6.8e-21  (= 1/2**67)
                   p_holm = 4e-05,  rejected_at_0.05 = true
PRIMARY            p_two_sided = 4.9999750001249995e-06,  p_floor = 1.355e-20,
                   p_at_its_floor = false,  test_mode = monte-carlo(200000)
```

Those four control p's are **indistinguishable from each other and from zero**; the artifact
presents them as four exact values, Holm-adjusts them, and declares the test had 15 orders of
magnitude of headroom. (`a4.py` reproduces the mechanism at k = 17, where the MC estimate
2.99998e-05 is *larger* than the reported "floor" 7.63e-06 — the reported floor is not even a lower
bound on what the sampler returns.)

*Wrong number:* every `p_floor` and `p_one_sided_floor` in every shipped
`DCS_CSI_SUBSPACE_*.json` and `DCS_CSI_REDERIVE_PATCH_*.json`; and any claim of the form "p = 5e-6,
far above its floor".

*Fix:* in both functions, return
`floor = max(1.0/2**k, 1.0/(N+1))` (one-sided) / `max(2.0/2**k, 1.0/(N+1))` (two-sided) **in the
Monte-Carlo branch**, and add `"floor_source": "exact" | "monte-carlo-resolution"`. Then
`p_at_its_floor` becomes live and will correctly flag the four rank-5 controls.

### M3. The two splits are adjudicated by **two different primaries**, and the FAIL branch of the suppressed rule carries none of its caveat
`scripts/dcs_csi_subspace_analyze.py:558` (`if dist and dist["n_controls"] >= 2:`) vs `:582-589`.

The code's own comment (`:559-564`) says a single-comparator verdict "is not a verdict" — it flips
with which control the caller happens to name (S-050). It then suppresses it *only when a control
family exists*. The shipped validation run
(`reports/DCS_CSI_SUBSPACE_button_validation.json`, arms `BASE,KO,KO_SELF,KO_FULL,KO_AXIS,KO_PLS,KO_ORTH`)
has **no control family at all**, so `pairs` is empty, `dist` is `None`, and the verdict falls to
the suppressed single-comparator rule against `KO_ORTH`.

Note the asymmetry: the **PASS** branch (`:583-586`) appends the caveat
*"only %d control(s) present; a single comparator is an arbitrary draw … S-050"*. The **FAIL**
branch (`:587-589`) appends nothing:

```
PRIMARY DOES NOT PASS on split=validation -- see p, p_floor and the CI before calling this a negative
```

So the one place the arbitrary rule actually decided something, it decided a negative, and the
warning the authors wrote for exactly this situation is on the other branch.

*Wrong claim:* the headline "(b) … fails the primary on **both** splits" is two different tests. On
train it is the (unpassable, see B1) rank rule; on validation it is the rule the code declares
inadmissible. The validation numbers are a borderline null, not a clean failure: point **+0.00097**
(larger than train's +0.00042), CI [−0.00011, 0.00197], `n_pos = 16/23`,
`recovery_fraction = 0.0141` with CI [0.0, 0.0281].

*Fix:* refuse to emit a PRIMARY verdict when `n_controls < 2` — "CANNOT ANSWER: no control family on
this split" — and schedule the `KO_SHUF*`/`KO_RAND*` arms on validation, which is where the claim
lives. At minimum, move the S-050 caveat onto **both** branches.

### M4. The PRIMARY uses a **two-sided** p for the same directional question P1-h made one-sided
`scripts/dcs_csi_subspace_analyze.py:556` (`single_ok … and p["p_two_sided"] < 0.05`) vs `:514-520`
(the specificity family, deliberately one-sided).

P1-h's own argument — "the two-sided p answers 'does the candidate DIFFER from this control', which
is not the specificity question … Specificity asks only whether the candidate BEATS the control,
which is one-sided by construction" — applies verbatim to `PRIMARY_candidate_minus_comparator`,
whose null is "the candidate does not beat its norm-matched comparator". The fix was applied to the
family and not to the primary.

*Verified on the shipped validation artifact* (`a9.py`, re-running
`exact_signflip_one_sided` on the artifact's own `domain_means`, 23 domains):

```
validation PRIMARY  two-sided p = 0.08750
validation PRIMARY  ONE-sided p = 0.04376     <- crosses 0.05
```

The verdict does not flip *in this instance* only because `single_ok` also requires
`ci95[0] > 0` and the bootstrap lower bound is **−0.00011** — i.e. the published negative rests on a
1e-4 margin in a bootstrap CI while the sign-flip test at the same nominal level says the opposite.
Any future split where the CI clears zero will have its verdict decided by which of the two
conventions the code happens to use.

Also undeclared: `single_ok` is a **conjunction** of two nominally-5 % tests (bootstrap CI *and*
sign-flip p), which is not the preregistered α.

*Fix:* use `exact_signflip_one_sided` for the PRIMARY too, with the direction stated in the
preregistration; report both p's; state the CI-and-p conjunction explicitly or drop one of them.

### M5. The per-`prompt_id` norm-match VOID is silently skipped **entirely** whenever the candidate arm records no `written_norm_mean`
`scripts/dcs_csi_subspace_analyze.py:424-434`.

```python
_cw = (meta.get(a.candidate_arm) or {}).get("written_norm_by_pid") or {}
_aw = m.get("written_norm_by_pid") or {}
if _cw and _aw:
    ...
```

If the candidate arm has no `written_norm_by_pid`, `_cw` is `{}`, the `if` is false, and **every**
norm-matched control skips the check — with no `void.append`, no print, and no field in the
artifact recording that the check did not run. The empty-intersection case *is* VOIDed (`:429`);
the empty-candidate case is not.

This is reachable: `written_norm_mean` is emitted by `SubspaceDonorPatch.liveness()`
(`src/boombness/donor_patch.py:288`) but **not** by `DonorPatch.liveness()` (`:134-137`), the
whole-state patcher. So `--candidate-arm KO_FULL` (the obvious sanity run: "does the positive
control beat the controls?") disables the entire norm-match gate.

*Verified* (`t2.py`, 8-arm synthetic, real `main()`):
```
A  controls correctly norm-matched            -> VOID: []
B  KO_ORTH written norm 10x off               -> VOID: ['KO_ORTH: written norm differs from the
                                                        candidate by up to 6.300e-01 on 100 shared
                                                        rows -- NOT norm-matched']
C  candidate records no written_norm           -> VOID: []      <-- check silently vanished
```
Case B shows the check has real teeth; case C shows it can be turned off without leaving a trace.

*Fix:* `if not _cw: void.append("%s: the candidate arm records no written norm, so the norm match
for %s CANNOT BE VERIFIED" % (a.candidate_arm, arm))`, and record
`"norm_match_checked": {arm: n_shared}` in the artifact so a reader can see the check ran.

### M6. `BASE` is exempt from **every** liveness and rescue check; a `BASE` arm that carried live hooks passes with `VOID: []` and all gates true
`scripts/dcs_csi_subspace_analyze.py:353-367` (`if arm != a.base_arm:` around the prefill/decode
checks; `arm != a.base_arm` in the rescue-fired check) and `:400-403` (`rescue_basis is None`
exemption).

The analyser asserts that the knockout **is** live on every non-BASE arm. It never asserts that
BASE is **clean** — no `prefill_edits == 0`, no `rescue_fired == 0`, no `rescue_layer is None`.
Its own sibling verifier does exactly this check (`dcs_csi_rederive_patch.py:573-574`,
`"arm %s: CTRL arm has nonzero prefill edits"`).

BASE is the denominator of the manipulation contrast, and `KO−BASE` is the scale every recovery
fraction is read against. A BASE arm that inherited a stray `--rescue-layer`/`--rescue-basis` from a
copy-pasted sbatch line (the `feedback_sbatch_export_comma` shape) writes clean donor state into an
un-knocked-out row — a near no-op on the readout, so it changes `installation_by_arm["BASE"]` by a
small, silent amount and every downstream fraction with it.

*Verified* (`t4c.py`): a BASE arm whose rows carry `hook_n_prefill_edits = 5`,
`rescue_liveness.fired = True`, `rescue_layer = 14`, `rescue_basis_key = "cand_rank1"`:
```
VOID: []
gates: {"manipulation_check": true, "identity_check": true, "instrument_capable": true}
VERDICT: PRIMARY DOES NOT PASS ...
```
(The run is only caught if the stray rescue happens to use a *different* layer from the other arms,
which trips the unrelated `rescue_layers` VOID — I confirmed that by first running the same test
with layer 20.)

*Fix:* add the positive BASE assertions:
```python
if arm == a.base_arm:
    if m["prefill_edits_min"]:      void.append("BASE has nonzero prefill edits")
    if m["decode_edits_total"]:     void.append("BASE has decode edits")
    if m["rescue_fired"]:           void.append("BASE fired a rescue")
    if m["rescue_layers"]:          void.append("BASE declares a rescue layer")
```

### M7. `dcs_csi_known_short.py` **does** document claims it has not verified — this is the direct answer to review question 3
`scripts/dcs_csi_known_short.py:21-32` (TEMPLATE), `:59-61`.

The module docstring promises: *"This script REFUSES to document a run it has not verified."* What
it verifies is (i) every `failure_reasons` key contains `"norm-match DEGENERATE"`, and (ii)
`n_succeeded == have` and `n_attempted == want`. What the TEMPLATE it writes into
`src/boombness/run_completeness_check.KNOWN_SHORT` **asserts** is considerably more:

1. *"The loss is OUTCOME-INDEPENDENT (the angle between a fixed basis and a fixed delta, both
   determined before any readout; the delta is identical across arms) **and is not
   domain-clustered**."* Neither clause is checked. The script holds the failing `prompt_id`s and
   could look up their domains; it does not. Non-clustering is precisely the property that makes
   the shortfall safe, and it is the one asserted on faith.
2. *"{nfail} row(s) ({ids}) REFUSED …"* — `ids` comes from `failure_example_ids`, which
   `src/boombness/common.py:390-392` **caps at 10 per reason**:
   ```python
   xs = self.examples.setdefault(reason, [])
   if len(xs) < 10:                      # ids only, never prompt text
       xs.append(str(ident))
   ```
   So for any run short by more than 10 rows the entry names a *sample* in a grammatical frame that
   reads as an exhaustive enumeration. Rendered (`a6.py`):
   ```
   "DCS-CSI-047: 658 of 670 rows. 12 row(s) (id00, id01, ..., id09) REFUSED by the sprint's ..."
   ```
   Twelve rows, ten ids, no indication that two are missing.
   Currently latent: all five short `csi1_*` runs lost exactly **1** row each (measured).
3. *"`dcs_csi_subspace_analyze.py` intersects (domain, slot) KEYS across all arms before averaging,
   so every arm is compared on the same key set."* True today (I verified it), but the entry is
   written into a guard that is consulted by runs that may never go through that analyser.

*Wrong number:* a KNOWN_SHORT entry is the artifact that converts "this run is incomplete" into
"this run is fine". An entry asserting non-clustering that was never measured licenses a
domain-correlated row loss to enter a domain-unit analysis.

*Fix:* (a) compute the failing rows' domains from `results.jsonl`/the bank and either state them or
refuse when they concentrate in one domain; (b) either drop `{ids}` when
`nfail > len(ids)` or render it as `"e.g. …"` with the count of listed vs total; (c) have
`common.py` record `n_examples_truncated` so the cap is visible to consumers.

*One thing this script gets right:* `nfail = f.get("n_failed")` is unvalidated, but the ledger
invariant `attempted = succeeded + n_failed` (`common.py:381-392`) makes it exactly `want - have`
whenever the two checks at `:57` pass. No defect.

---

## MINOR

### m1. `rows_dropped_by_option_mass_floor` is hard-coded to 0 in the artifact
`:289` (`n_drop = 0`) and `:302`. Since `installation_with_option_mass` is no longer used to build
the values, nothing ever assigns `n_drop`. Verified (`t3.py`): at `--option-mass-floor 0.5` on data
constructed so BASE drops half its rows, the artifact says
`rows_dropped_by_option_mass_floor: 0` for every arm while `n_keys_common` correctly falls from 100
to 50. The field a reader consults to ask "did the floor do anything?" always answers "no".
*Fix:* record `len(keep_keys)` and `len(kv[arm]) - len(kv[arm] & keep_keys)` per arm, or delete the
field.

### m2. The default `--out` filename does not encode the candidate, and a **stale** artifact is sitting under it
`:603-605`: the path is `DCS_CSI_SUBSPACE_<codeword>_<split>[_om<floor>].json` — no `--tag-prefix`,
no candidate arm, no arm list. The rank-1 and rank-5 analyses of the same codeword and split
collide; they only avoided it because `--out` was passed by hand.
`reports/DCS_CSI_SUBSPACE_button_train.json` is the collision target and it is **stale**: it carries
`control_recovery_distribution.n_controls = 4` (≥ 2, so today's code would take the rank branch) yet
has **no** `verdict_basis` and the pre-P1-i verdict text. Its `schema` is `dcs_csi_subspace/1`, the
same as the current artifacts — nothing marks it as superseded.
*Fix:* include the candidate arm and tag prefix in the default name; bump `schema` when the verdict
rule changes; add `"code_sha16"` or the analyser's mtime to the artifact.

### m3. Three load-bearing row fields are silently defaulted, turning their VOIDs into permanent passes
`:182` `out["decode_edits_total"] += (r.get("hook_n_decode_edits") or 0)` — if the field is renamed
or absent, the total is 0 and the "decode-time edits must be 0" VOID (`:357-358`) can never fire.
Contrast `:180-181`, which handles the *prefill* field's absence correctly (empty list → `None` →
VOID).
`:192` `(rl.get("n_positions_norm_match_degenerate") or 0)` — same shape; the degeneracy VOID
(`:415-418`) goes quiet.
`:193` + `:206-208` `rl.get("n_positions")` → `None` → filtered out of the sorted list, so an arm
whose rows lack the field is **silently exempt** from the cross-arm position-count VOID (`:373-375`)
rather than VOIDing it.
`:178` `if r.get("hook_liveness_violations")` — absent field reads as zero violations.
*Fix:* treat "field absent on every row" as VOID, exactly as the prefill path does.

### m4. R2-M2 is only partially actioned: `intervene`, `rescue_donor`, `rescue_positions` and
`rescue_n_positions` are still unchecked across arms
`:296-300` reads `bank`, `exclude_prompt_ids`, `attn_impl`, `dtype` from `config.json` and stops;
`:405-408` checks only `knockout_scopes`, from the rows. Two KO arms carrying different knockout
bands (`…:6-14:1.0` vs `…:6-20:1.0`), different rescue donors, or `demo`-vs-`query` rescue spans of
equal size all pass. Latent: I read all sixteen `config.json`s behind
`DCS_CSI_SUBSPACE_button_train_rank1.json` and every arm agrees
(`demo_all:attn_knockout:6-14:1.0`, layer 20, donor `clean`, positions `query`) except `KO_SELF`'s
`rescue_donor=self`, which is correct by design and must be exempted by any fix.
*Fix:* extend `:296-300` to `intervene`, `rescue_donor`, `rescue_positions`, `rescue_n_positions`
and compare across arms with an explicit per-arm exemption table, as `ARM_SPEC` already does.

### m5. `--allow-short` is not recorded in the artifact and is not tied to a documented reason
`:252-255`, `:280`, `:286`, `:346`. `strict_run_dir` enforces the ledger/file agreement correctly
(see CHECKED), but it never consults `summary.json`'s `failure_reasons` — so `--allow-short 5`
accepts five rows lost to an OOM exactly as it accepts five lost to the degeneracy refusal. The
output JSON has no `allow_short` key; the only trace is `arm_meta[*].n_rows` differing from
`expect_n`. The rank-1 artifact was produced with `--allow-short ≥ 1` (four arms at 669/670) and
does not say so.
*Fix:* record `allow_short` and each arm's shortfall+reason in the artifact; have `strict_run_dir`
require the shortfall to be in `KNOWN_SHORT` (the `known_short` script already produces those
entries).

### m6. The rank distribution pools two different null families and reuses one Monte-Carlo seed
`:509`, `:517`. The rank-1 distribution mixes 6 `KO_RAND*` with 4 `KO_SHUF*` and treats the ten as
exchangeable draws from one null. A random subspace and a shuffled-label subspace are different
nulls; if their spreads differ, the pooled rank is not calibrated against either. Observed spreads
are similar (RAND −0.00098…+0.00159, SHUF −0.00138…+0.00104), so this is a caveat rather than a
measured error — but it should be stated, and the rank reported within each family as well.
Separately, `exact_signflip_one_sided` hard-codes `random.Random(20260915)`
(`dcs_csi_rederive_patch.py:218`), so every control in the family is tested against the **same**
200 000 sign patterns; the Monte-Carlo error is common to all of them rather than independent.

### m7. Nothing prevents the candidate or comparator from being inside its own control family
`:509` selects `ctrl_arms` purely by name prefix. With `--control-prefixes KO_`, the candidate lands
in its own control set. It fails loudly (`KeyError` at `:527`, because the recovery loop at `:495`
skips `base/ko/self`) rather than silently — verified (`t4.py`) — but a prefix that catches the
candidate without catching a skipped arm would produce a self-contrast with `p = 1` and a
tie-inflated rank.
*Fix:* `void.append` if `a.candidate_arm in ctrl_arms`.

### m8. R2-m3 is still open: the in-sample fingerprint is copied and never compared
`:440-456`. `bmeta["fit_domains_sha16"]` (`4614853e5636eb5f` on every shipped arm) is written into
the artifact and never checked against `sha256("|".join(sorted(fit_doms)))[:16]` from the sidecar,
and `evaluation_is_in_sample` (`true` on every train artifact) never reaches the VERDICT string.
The train verdicts read "PRIMARY DOES NOT PASS on split=train" with no in-sample qualifier.

### m9. `run_dir_in_job_window` proves time-overlap, not ownership
`dcs_csi_rederive_patch.py:361-375`. The check is a genuine improvement over R2-M4 and it
**fails closed** (a `None` from any arm appends "(job-window verification incomplete…)" to
`hw_verdict`, which then trips the `!= "SAME ARCHITECTURE"` problem at `:716-717` — verified by
reading the control flow). It also parses the real `DONE.json` `end_ts` format
(`"2026-09-15T23:06:51"`, `"%Y-%m-%dT%H:%M:%S"`) correctly. What it cannot show is that *this*
allocation produced *this* directory: any concurrent run on any node whose `end_ts` falls inside the
window passes. Of the four shipped `DCS_CSI_REDERIVE_PATCH_*.json`, only `_p0cmp` has
`arms_inside_declared_job_window` populated; the other three are `null` (no `--slurm-job`), i.e. the
new check ran on one artifact out of four.
*Fix:* persist `SLURM_JOB_ID` into `config.json` at score time and compare it directly, as R2-M4
recommended; the window check is a proxy for that and should say so in `hardware_verdict`.

---

## NIT

* `:121-138` `arm_domain_means` is **dead** (no caller anywhere in `scripts/`, `src/`, `tests/`).
  Its `keep_keys` semantics differ from `main()`'s — it drops keys *before* the split filter and
  returns an `n_dropped` — so re-wiring it would silently change behaviour.
* `:411` `cand_norm` is assigned and never read (the vestige of the per-arm-mean comparison R2
  flagged; the live check is the per-`prompt_id` one below it). Delete it, or a future reader will
  reintroduce the mean comparison.
* `:59-72` `installation_with_option_mass`'s docstring still describes it as the function that
  computes the floored contrast ("the primary contrast is computed on ALL rows and RE-computed above
  a floor"). It is now only called at floor 0.0 by `_assert_matches_loader`; the floor is applied via
  `reference_key_set`. R2-m1's duplicate-key-ordering defect inside it is consequently unreachable.
* `:368-369` the `if …: pass  # reported below once` empty body flagged in R2 is still there.
* `dcs_csi_known_short.py:69` `src.replace("KNOWN_SHORT = {\n", …, 1)` is a **silent no-op** if the
  anchor ever changes (line ending, a comment on the same line, reformat): the script writes the
  unmodified file and prints "wrote N entr(ies)". The anchor currently matches
  (`run_completeness_check.py:95`). Verified that a `\r\n` variant does not match.
* `dcs_csi_known_short.py:44` `if rid in src: continue` is a substring test over the whole guard
  file, so a run id mentioned in any comment or in a different dict counts as documented.
* `dcs_csi_subspace_analyze.py:334` `a.codeword not in (list(banks)[0] or "")` is still a substring
  test on a path (R2-m9/nit).
* `dcs_csi_rederive_patch.py:277` vs `:312` still use two different GPU regexes for the same field
  (R2-m13).

---

## CHECKED AND FOUND CORRECT

Every claim below was verified by running code, not by reading.

**`exact_signflip_one_sided` is arithmetically correct** (`dcs_csi_rederive_patch.py:191-228`).
400 randomised cases (n = 1…9, mixed signs, deliberate exact zeros, shifted means) against an
independent `itertools.product` brute force: **0 mismatches** (`a3.py`). Named cases:
`d = [1,1,1]` → p = 0.125 = 1/2³ (its floor); `d = [-1,-1,-1]` → **p = 1.0** (the brief's
negative-observation case behaves correctly, not "near 0"); `d = [1,-1]` → 0.75 (ties counted into
the tail, the conservative convention); `k = 0` → 1.0 with `mode: "degenerate"`.
`p_floor = 1/2**k` is the correct one-sided floor (the identity mask always hits, so
`p ≥ 1/2**k`), and it is reached exactly at `k = 16`. `obs` includes the zero-difference domains in
both the numerator and the divisor `len(d)`, matching the enumeration — no off-by-`k/n` error. The
**only** defect is the Monte-Carlo branch's floor (M2).

**`holm` is correct** (`dcs_csi_subspace_analyze.py:222-231`). 3000 randomised cases (m = 1…7, with
deliberate ties at 0.0 / 0.01 / 0.02 / 0.05 / 0.2 / 1.0) against two independent references — an
adjusted-p reference and a classic stop-at-first-failure step-down: **0 mismatches on both**
(`a5.py`). The `(m-i)` multiplier is right for 0-based `i`, the running max enforces monotonicity
(making rejection-by-adjusted-p equivalent to the step-down), ties are handled by the running max
regardless of sort order, `min(1.0, …)` is applied after the max. `adj < 0.05` is strict where the
textbook uses `≤`; verified at the exact boundary (`p = 0.05/3` with m = 3 → `p_holm = 0.05`,
`rejected = False`) — conservative, not a defect. This re-confirms R2.

**The cross-arm key intersection is sound and every contrast uses one key set**
(`:309-327`). `common_keys = set.intersection(*[set(kv[x]) for x in arms])`, optionally `&=
keep_keys`; `dmeans[x]` is built by iterating `common_keys` only; `doms = {k[0] for k in
common_keys}`; `installation_by_arm`, all five named contrasts, every `recovery_*_minus_ko`, every
`specificity_*`, `recovery_fraction` and `domain_means` are all computed over that same `doms` and
those same `dmeans`. I also confirmed the *arithmetic* consistency on the shipped rank-5 artifact
(`a2.py`): for all eight controls,
`specificity_candidate_minus_X.point == candidate_minus_ko.point − recovery_X_minus_ko.point` to the
last reported digit — which is only possible if all three were computed on an identical key set.
R2-B1 is fixed.

**`reference_key_set`'s return type is right** — the brief's suspicion is refuted.
`installation_with_option_mass_keys` returns `(set, None)`; `:159` unpacks
`inst, _ = …`; `:160` returns the **set**; `:281` binds it to `keep_keys`; `:311` does
`common_keys &= keep_keys`. Set-to-set throughout.

**The single-reference option-mass key set works end-to-end.** `t3.py`: synthetic data where BASE
alone loses half its rows to a low option mass. At `--option-mass-floor 0.5` the analyser prints
`[P1-f] key set from reference arm BASE at floor 0.5: 50 keys retained`, and **all six arms** are
then averaged over the identical 50 keys (`n_keys_common: 50`, `n_domains: 20`). The R2-B1
differential-deletion defect does not reproduce.

**The per-`prompt_id` norm-match check has real teeth.** `t2.py` case B: a `KO_ORTH` whose written
norm is 10× the candidate's produces
`VOID: ['KO_ORTH: written norm differs from the candidate by up to 6.300e-01 on 100 shared rows --
NOT norm-matched']`. On the shipped rank-5 data all nine subspace arms report a byte-identical
`written_norm` triple (mean 0.222893, min 0.102539, max 0.588072) over all 670 shared `prompt_id`s.
(The skip path is M5.)

**R2-M1 is fixed.** `:364` is now `if arm.startswith("KO_") and arm != a.base_arm and arm !=
a.ko_arm:` — the `arm != a.self_arm` exemption is gone, and the shipped artifacts confirm
`KO_SELF: rescue_fired 670 of 670`.

**R2-M3 is fixed.** `src/boombness/score_behavior.py:2426`:
`if args.rescue_basis_key and not args.rescue_basis: raise …`, alongside the two pre-existing guards
at `:2416` and `:2419`.

**`strict_run_dir(allow_short=…)` is correct** (`dcs_csi_rederive_patch.py:53-107`). Five
constructed directories (`t5.py`):

| DONE.rows_written | file lines | expect | allow_short | result |
|---|---|---|---|---|
| 670 | 669 | 670 | 1 | REFUSE — "the ledger and the file disagree" |
| 669 | 669 | 670 | 1 | ACCEPT |
| 669 | 669 | 670 | 0 | REFUSE — "669 lines != 670" |
| 671 | 671 | 670 | 1 | REFUSE (over-long is not "short") |
| 668 | 668 | 670 | 1 | REFUSE (beyond the bound) |

The ledger/file equality is unconditional and precedes the short allowance, exactly as the docstring
claims; `allow_short = 0` is correctly falsy; the anchored `_pat` regex and the "exactly one
candidate" rule are unchanged; the `row_file` default stays `gens.jsonl`.

**`known_short`'s ledger check is sound.** `n_succeeded == have` and `n_attempted == want` together
with the `RunLedger` invariant `attempted = succeeded + n_failed`
(`src/boombness/common.py:381-392`) pin `n_failed == want - have` exactly, so the count in the
generated prose cannot drift. The "all reason keys contain `norm-match DEGENERATE`" test is a
genuine gate — I confirmed all five short `csi1_*` runs carry exactly one reason key, the ValueError
from `SubspaceDonorPatch`, and one failing row each. (The unverified claims are M7.)

**`run_dir_in_job_window` parses the real timestamps and fails closed.**
`DONE.json.end_ts` is `"2026-09-15T23:06:51"`, matching the hard-coded
`"%Y-%m-%dT%H:%M:%S"`. A `None` return (missing `DONE.json`, unparseable timestamp, or an empty
`job_window` from a failed `sacct`) propagates to
`hw_verdict += " (job-window verification incomplete for some arms)"`, which then makes
`hw_verdict != "SAME ARCHITECTURE"` true and appends a PROBLEM. The shipped `_p0cmp` artifact shows
`{"ctrl": true, "ko": true, "rescue_clean": true, "sizematch": true}`. (The residual is m9.)

**No VOID check compares per-arm aggregates over different row sets.** I traced each one: the
norm match is per-`prompt_id` over the intersection; `liveness_violations`, `prefill_edits_min`,
`decode_edits_total`, `rescue_fired`, `degenerate_positions` are all within-arm counts thresholded
individually; `rescue_layers`, `n_rescue_positions`, `basis_keys`, `norm_match_keys`, `models`,
`knockout_scopes` are set comparisons, not means; `installation_by_arm` is over the common `doms`.
The repo's recurring defect is **absent** from this VOID block.

**`arm_key_values` call site agrees with its signature** — it returns a 3-tuple and `:288` unpacks
`kv[arm], n_inst, kinds`. `_assert_matches_loader` is now called unconditionally on every arm
(R2-m2 fixed), which also means `option_mass` is required on every cell-C row of every arm.

**`candidate_rank_among_controls`'s tie handling and `rank_p` are the right statistic.**
`1 + sum(v >= cand)` counts ties **against** the candidate (conservative), `rank == 1` means strictly
largest, and `rank_p = rank/(n+1)` is the standard one-sided permutation p over the n+1 exchangeable
values. `rank_p_floor = 1/(n+1)` is the correct attainable minimum and is honestly reported. The
defect is not the statistic — it is the threshold applied to it (B1).

**`recovery_fraction`'s degeneracy guard is live on the real data:** denominators
`FULL−KO` = 0.0696 (train) / 0.0950 (validation), both well above `min_denominator = 0.01`, with
`n_domains_with_movement` = 67 / 23 and `draws_dropped = 0`.
