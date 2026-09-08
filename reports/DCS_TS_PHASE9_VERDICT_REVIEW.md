# ADVERSARIAL CODE REVIEW -- PHASE 9 CAUSAL VERDICT (commit f6022f58)

Reviewer: adversarial 4-hourly review. Mode: READ + RUN + REPORT. No file in the repo was
edited; this report is the only file written. No `git add` / `commit` / `stash` was run.

Python: `/home/sharifm/students/omeryosef/miniconda3/envs/poc_stage2/bin/python`. CPU only.

## 0. Harness re-run (my numbers)

| command | expected | **observed** |
|---|---|---|
| `scripts/dcs_ts_pr057_causal.py --self-test` | 111 / 0 FAILED | **111 checks, 0 FAILED** (rc=0) |
| `scripts/dcs_ts_pr057_causal.py --mutate` | 90/90 RED | **90/90 mutations produced a refusal** (rc=0) |

## 0b. Full re-analysis reproduced, bit for bit

```
python scripts/dcs_ts_pr057_causal.py --stage h2 --split test \
       --fit-dir outputs/dcs_ts/directions_pr053 --out <scratch>/analysis.json      # rc=0
```

30 arms loaded, 0 check failures. Every reported number in the review brief reproduced exactly
(O2 -0.002997 / p 0.807519; O1 +0.391905; C1 CI [-0.008842,+0.007934]; O2 -0.642195; O1 +0.317962;
C1 CI [+0.115897,+0.206261]; both verdicts; the 0.1656/0.4069/0.0936 dose). The analysis is
reproducible from the committed code and the committed run directories.

---

## FINDING 1 -- THE ANOMALY. It is not (a), not (c), it is (b) -- AND the conjunct that called it "unintended" is WRONG. **SERIOUS**

**The premise of the attack is false, and the analyzer supplied the false premise.**

`scripts/dcs_ts_pr057_causal.py:4386-4387`:

```python
success = evaluate_success(o1, o2, control, across, alpha,
                           expected_sign=o2["expected_sign"])
```

`evaluate_success` (`:1589-1610`) takes ONE `expected_sign` and applies it to **both** conjunct 1
(O1) and conjunct 2 (O2):

```python
c1_ok = (... and _sign(o1.get("delta", 0.0)) == _sign(expected_sign))   # :1600  <- O1
c2_ok = (... and _sign(o2.get("delta", 0.0)) == _sign(expected_sign))   # :1608  <- O2
```

O1 and O2 have **opposite** preregistered directions and the analyzer computes both correctly and
separately:

* `o1_expected_sign` (`:3534-3548`) parses `outcome_variables.O1_probe.direction_expected` =
  `"toward knife under a bomb->knife edit"`; the leading clause names the SOURCE -> **+1**.
* `o2_expected_sign` (`:3550-3564`) parses `"...FALLS under projection-out of v_bomb_specific"` -> **-1**.

The run's own JSON confirms both arms:

```
H2axS1  O1 expected_sign = 1   delta = +0.391905   moved_intended_sign = True   p at floor
H2axS2  O1 expected_sign = 1   delta = +0.317962   moved_intended_sign = True   p at floor
```

So O1 moved in **exactly the intended direction on both arms**, and the analyzer knows it -- the
`verdict()` call at `:4457` correctly uses `o1["moved_intended_sign"]` and passes `o1_moved=True`.
Only the conjunct table was scored against O2's sign, i.e. against `-1`, so a correct O1 was
printed as `[FAIL] 1_probe_moves_intended`.

The frozen file is unambiguous that this is a defect, not a reading:
`configs/dcs_ts_pr057_phase9.json:primary.success.conditions[0]` =
*"O1: the concept-probe score moves in the INTENDED direction"* -- O1's intended direction, not O2's.

**Internal contradiction in the published artifact.** The S1 verdict sentence is
`DECODABLE BUT NOT CAUSALLY USED` -- a sentence reachable only because `o1_moved == True`
(`verdict()` `:1748`) -- printed three lines below `[FAIL] 1_probe_moves_intended`. The same report
says the probe both did and did not move as intended.

### End-to-end arithmetic on real rows (ruling out (a) and (c))

`ProbeReadCapture` writes `o1_margin_source_minus_target = P(knife) - P(bomb)` (`:872`);
`FrozenProbe.margin` (`:690-712`) is `post[source] - post[target]`; `domain_group_permutation`
(`:1538-1541`) forms `delta = mean(arm) - mean(baseline)`. I recomputed from the two run
directories actually bound (`ts116m_pr057_h2a_s1_projout_button_20260908_155134_3905688` and
`ts116m_pr057_c5_disabled_bridge_s1_20260908_171902_3414524`), 230 shared prompt_ids, block 9:

```
mean bridge (un-intervened) margin = -0.94230     <- probe is confidently BOMB
mean arm     (projected-out) margin = -0.55039    <- P(bomb) FELL
HAND-COMPUTED domain-mean delta     = +0.391905   <- matches the reported number exactly
```

Sample rows (arm / bridge / diff): `063ecc0ae7ea5c8d` -0.51603 / -0.96751 / +0.45148;
`0185540634e96feb` -0.97740 / -1.00000 / +0.02260.

* **(a) sign-convention error -- REFUTED for `o1_contrast` / the probe / the direction.** Projecting
  out `v_bomb_specific` *lowers* the bomb posterior; margin = knife-minus-bomb therefore *rises*.
  The sign is right end to end.
* **(c) wrong baseline / wrong difference orientation -- REFUTED.** The C5 bridge is the
  un-intervened state (margin -0.94, saturated on bomb), the difference is arm-minus-baseline, and
  the bridge's void clause is CLEAR: byte-identical to the untouched PHASE 7 baseline on every
  paired row.
* **(b) genuine effect -- CONFIRMED**, and it is the *intended* one, not a surprise.

### Does it change the VERDICT?

I re-ran the full analysis with `evaluate_success` monkey-patched (in memory, no file edited) so
conjunct 1 uses `o1["expected_sign"]`:

| arm | conjuncts as published | conjuncts corrected | class published | class corrected |
|---|---|---|---|---|
| H2a x S1 | 1 FAIL 2 FAIL 3 PASS 4 FAIL (1/4) | **1 PASS** 2 FAIL 3 PASS 4 FAIL (2/4) | NEGATIVE | **NEGATIVE (unchanged)** |
| H2a x S2 | 1 FAIL 2 PASS 3 FAIL 4 PASS (2/4) | **1 PASS** 2 PASS 3 FAIL 4 PASS (3/4) | NOT A CAUSAL RESULT | **NOT A CAUSAL RESULT (unchanged)** |

**No verdict class changes.** `verdict()` never consults the conjunct table except through
`success["success"]` (all-four), and `o1_moved`/`o2_moved` were already computed from the correct
per-outcome signs. What *does* change is what the reader is told:

* the printed S2 sentence changes from **"2/4 conditions"** to **"3/4 conditions"**, and the single
  failing conjunct is the decisive control C1 -- not the probe;
* the S1 negative stops contradicting itself: the probe moved, the readout did not, which is
  precisely the preregistered NEGATIVE (`primary.negative.condition` = *"O1 moves but O2 does not"*).

**Severity: SERIOUS. Would not change the VERDICT; does change the per-condition table, the "2/4"
count, and removes an internal contradiction in the published artifact.**

---

## FINDING 2 -- Is the S1 NEGATIVE real, or a resolution limit? **REAL. No finding against the verdict; MINOR reporting gap.**

The analyzer *does* distinguish the two, at `realised_power()` (`:4119-4138`) and the
`primary.cannot_answer` clause *"power < 0.8 at the realised between-domain SD of O2"*, which was
evaluated and returned **CLEAR**:

```
H2axS1  n_domains=23  realised_between_domain_sd=0.058754  declared_mde=0.500
        power=1.000 (bar 0.80) -> power_ok=True     mde_at_bar=0.035915
```

So the resolution limit at the *realised* SD is 0.0359 nats and the observed |delta| = 0.0030 is
below it -- an effect that small is indeed unresolvable. But the design's own bar for "meaningful"
is `power.declared_minimum_meaningful_effect.o2_semantic_logodds_shift = 0.5` nats, and against
that the test has power 1.000. The negative is scoped to the 0.5-nat MDE, and it holds.

I computed the arm's own equivalence interval (the analyzer builds one only for C1), using the
analyzer's own `equivalence_interval` on the arm's 23 domain deltas:

```
H2axS1 arm O2 equivalence 95% CI  [-0.028405, +0.022410]      (mean -0.002997, sd 0.058754)
H2axS2 arm O2 equivalence 95% CI  [-0.827730, -0.456660]
```

The S1 interval excludes everything above 0.028 nats in either direction -- **18x tighter than the
declared meaningful effect**. This is a genuine null, not "cannot resolve".

Corroboration the analyzer never uses: the *validation* run of the same arm
(`..._h2a_s1_projout_button_20260908_043320_3252166`, bound to
`exclude_..._button_bomb_validation.txt`) gives O2 delta = **+0.002723, p = 0.746, n=23** -- an
independent null of the same size on a different split.

**MINOR gap:** the printed block for H2axS1 shows O2, O1, C1, the four conjuncts, the void clauses,
Holm and the dose -- but **never prints `power_at_realised_sd`, the realised SD, `mde_at_bar`, or
an arm-level equivalence interval**. That block is in the JSON, not in the artifact a reader sees.
The analyzer applies its own doctrine ("a control is shown NOT to move by its equivalence interval,
never a bare p > alpha", `control_c1_report` `:3798`) to the *control* but not to the *primary
null*. Would not change the verdict; it is the number that makes the negative defensible and it is
not on the page.

---

## FINDING 3 -- Is the S2 control failure interpreted correctly? **The code matches the declared test (NON-ISSUE). The scientific reading is impoverished, and two built controls were never analysed (SERIOUS, Finding 7a).**

Declared conjunct 3, `configs/dcs_ts_pr057_phase9.json:primary.success.conditions[2]`:
*"C1: the norm-matched random control does NOT move O2 (and its 5 draws are genuinely distinct)"*.

Implemented at `control_c1_report` `:3792-3794` as `moved = min(per-draw permutation p) < alpha`,
and consumed at `:1611-1617` as `c3_ok = distinct_hashes_ok and equivalence is not None and
moved is False`. It is **direction-agnostic by design** and it is the declared test, verbatim.
The per-draw S2 numbers:

```
draw0 -0.0776 p=0.0038 | draw1 +0.0360 p=0.1186 | draw2 +0.1683 p=2.0e-04
draw3 +0.3203 p=floor  | draw4 +0.3584 p=floor      band mean +0.1611, CI [+0.1159,+0.2063]
```

Four of five draws move, three at or near the floor, and the band's own CI excludes zero. Under the
frozen rule this is a failed control, full stop. **The analyzer's test matches the declared one; no
code defect.**

Is "opposite sign" different from "merely moves"? Scientifically yes -- and the analyzer discards
that information (it stores only `moved`). But it does not rescue a causal claim, and the reason is
a control the analyzer never looked at. See Finding 7a: **C4 (norm-matched ADD orthogonal to the
concept subspace) moves O2 by +1.2376 at S2 -- roughly twice the arm's -0.642, at the p floor.** A
concept-free perturbation of matched norm at that band moves the readout harder than the concept
edit does. That is exactly the confound conjunct 3 exists to catch, and it is the strongest
available support for the published `NOT A CAUSAL RESULT`. The verdict is right; the reasoning
printed under it is thinner than the data on disk.

**Severity: NON-ISSUE for the analyzer's conjunct-3 logic. Would not change the VERDICT.**

---

## FINDING 4 -- Holm. **NO FINDING.**

`holm()` `:1463-1480`, `holm_with_absent()` `:1483-1523`. Recomputed by hand from the six reported
p-values:

```
i=1 H2axS2  p=9.999e-05  thr=alpha/6=0.00833333  reject=True
i=2 H2axS1  p=0.807519   thr=alpha/5=0.01000000  reject=False   <- step-down stops here
i=3 H1xS1   p=1.0        thr=alpha/4=0.01250000  reject=False
i=4 H1xS2   p=1.0        thr=alpha/3=0.01666667  reject=False
i=5 H2bxS1  p=1.0        thr=alpha/2=0.02500000  reject=False
i=6 H2bxS2  p=1.0        thr=alpha/1=0.05000000  reject=False
```

Identical to the analyzer's `holm` block. Verified: `m = 6` (declared members, not the 2 observed);
the four absent members enter at exactly `p = 1.0` and are never dropped; the sort is ascending by
p; the `rejected` latch is cleared on the first failure and never re-armed, so the step-down is
correct; `m` is re-asserted against `len(family_members(pr))` at `:1512`; `family_members` is
re-derived from `holm_family(pr, PR_ID)` and refuses a family that is not `PHASE9_CAUSAL`.

One cosmetic note, not a defect here: `holm` uses `p <= thr` rather than `p < thr`. No p in this run
sits on a threshold, so it is immaterial.

**Severity: NON-ISSUE. Would not change the VERDICT.**

---

## FINDING 5 -- The C1 cross-bank fix did not touch the button arms. **NON-ISSUE, verified.**

The fix (`git diff f6022f58^ f6022f58 -- scripts/dcs_ts_pr057_causal.py`) adds
`and x.codeword == arm.codeword` to the `c1_draws` selector at `:4353-4357`, and passes `arm` into
`control_c1_report` so a mismatch is refused by name.

I re-derived both selectors from the frozen manifest (`build_arm_manifest`, in memory):

```
h2a_s1_projout_basket  basket   old_n=5  new_n=0   identical=False
h2a_s1_projout_button  button   old_n=5  new_n=5   identical=True
h2a_s2_projout_basket  basket   old_n=5  new_n=0   identical=False
h2a_s2_projout_button  button   old_n=5  new_n=5   identical=True
```

All 20 C1 arms are declared `codeword="button"` (`build_arm_manifest` `:1360-1372`, hardcoded), so
for a button arm the new clause is a **no-op**: the same five draw arm_ids, in the same order,
paired against the same `base["results"]`. `control_c1_report`'s inputs for the button arms are
therefore identical pre- and post-fix, and so are the reported CI, `smallest_draw_p`,
`distinct_hashes_ok` and conjunct 3. Only the two basket arms lost their (cross-bank, bogus)
control.

I also attempted a direct end-to-end run of the pre-fix analyzer (`git show f6022f58^:...` executed
against symlinked repo directories). It cannot complete: it refuses the whole run at
`h2a_s1_projout_basket` on the UNEVALUABLE C5-bridge void clause -- the defect the same commit
fixed. The static equivalence above is therefore the proof, and the analyzer's own self-test
`fixE_every_c1_arm_is_on_the_dev_bank (n=20)` asserts the constructibility fact it turns on.

**Severity: NON-ISSUE. Would not change the VERDICT.**

---

## FINDING 6 -- The dose IS definitional. Finding F-4 is confirmed exactly. **SERIOUS**

`frac_cellmean_spread_removed` is `cellmean_frac_at_alpha1` from
`src/boombness/score_behavior.py:250` (`realized_dose_record`), whose `frac` comes from
`src/boombness/insubspace_null_test.py:319-357` (`cellmean_dose`):

```python
M = torch.stack(rows); M = M - M.mean(dim=0, keepdim=True)      # CENTRED cell means
return float(((M @ u.reshape(-1,1))**2).sum()) / float((M**2).sum())
```

The PR-053 payload (`outputs/dcs_ts/directions_pr053/directions_fit_dev.pt`) has **exactly two
cells, `A` and `C`** (n=670 each). Centring a 2-row matrix leaves rank 1: `M`'s rows are
`+-(m_A - m_C)/2`, so the ratio collapses identically to `cos^2(u, m_A - m_C)`. And `v_bomb` is
*defined* as `mean over TRAIN domains of [h(C_bomb) - h(A_shared)]`
(payload `meta.definitions.v_c`), i.e. it **is** that contrast: I measured
`cos(v_bomb, m_A - m_C) = -0.99999999999998` at L9.

Measured directly (float64, my run):

| layer | `cellmean_dose` | `cos^2(v_bomb_specific, m_A-m_C)` | `cos^2(v_bomb_specific, v_bomb)` |
|---|---|---|---|
| L7 | 0.046827 | 0.046827 | 0.046827 |
| **L9** | **0.165585** | **0.165585** | **0.165585** |
| L13 | 0.189872 | 0.189872 | 0.189872 |

All eight edited layers agree to every printed digit. The reported **0.1656 is exactly
`cos^2(v_bomb_specific, v_bomb)`** at L9, and `norm_frac_removed = alpha*sqrt(frac) = 0.4069` is
exactly `|cos|`. **Both headline dose numbers are a geometric property of two directions from the
same fit. They are computable before any model is loaded, on any prompt, on any split, and they
carry zero information about how much of the model's state the hook actually changed.**

Consequence for the claim. The mandated sentence is scoped
*"at frac_cellmean_spread_removed=0.1656"*. Read literally a reader takes that as "we removed 16.6%
of the bomb signal and nothing happened". What it actually says is "`v_bomb_specific` sits about 24
degrees off `v_bomb`". The only genuinely *measured* dose in the printed line is
`cell_residual_frac_removed={'C': 0.0936}` (`score_behavior.cell_residual_frac_removed`, the
un-centred `alpha*|m_C . u| / ||m_C||`) -- and that function's own docstring exists precisely
because the centred metric once hid a 6.60x dose gap. The null's scope sentence should be carried
by the 0.0936 (and by the per-row liveness `norm_ratio`), not by the two definitional numbers
printed first and largest.

Secondary scope note surfaced by the same payload: `meta.cell_means_note` says the cell means are
*"TRAIN rows of the DEVELOPMENT codeword's BOMB bank only"*, so the basket arms' dose records are
borrowed from the button bank. Those arms are O2-only and make no claim, so this is a note, not a
finding.

**Severity: SERIOUS. Would not change the VERDICT class, but it changes what the null is scoped to,
and the current sentence overstates the realised intervention.**

---

## FINDING 7 -- Other things that could VOID the run

### 7a. Two built, live, liveness-passing controls are analysed NOWHERE. **SERIOUS**

`c3_vremap_s1/s2` and `c4_samenorm_orth_s1/s2` all ran, all passed liveness (`[PASS]
liveness_c3_vremap_s2 n=1840` etc. in the analyzer's own check block), and all four are among the
30 arms loaded. Grepping `analyse()` (`:4142-4600`) for `C3`/`C4`: **no match**. They produce no O2
contrast, appear in no report section, and gate no void clause. Four arms of confirmatory GPU time
are loaded, liveness-checked, and discarded.

I computed their O2 contrasts myself with the analyzer's own `o2_contrast`, against the same PHASE 7
baseline (`ts116m_readout_button_bomb_20260907_133811_3183103`):

```
arm                     delta       p          domains moving intended
h2a_s1_projout_button   -0.002997   0.807519   15/23
c3_vremap_s1            -0.047336   0.078192   17/23
c4_samenorm_orth_s1     +0.149133   9.999e-05   0/23      <- floor, opposite sign
h2a_s2_projout_button   -0.642195   9.999e-05  21/23
c3_vremap_s2            -2.844680   9.999e-05  23/23
c4_samenorm_orth_s2     +1.237557   9.999e-05   5/23      <- floor, ~2x the arm, opposite sign
```

Two consequences the published report does not carry:

1. **S2**: an orthogonal, concept-free, norm-matched ADD moves O2 by +1.24 where the concept edit
   moves it by -0.64. The site is grossly perturbation-sensitive at this norm. This corroborates
   `NOT A CAUSAL RESULT` far more strongly than the C1 band alone, and it is the direct answer to
   attack 3's question.
2. **S1**: the arm moved -0.003 (null) while C4 at the same site moved +0.149 at the floor. The site
   *is* movable at that norm -- so the S1 negative is not "nothing can move this site", which
   strengthens it. That sentence belongs next to the negative and is absent.

These do not void anything. They are evidence that was paid for and not reported.

### 7b. A void clause reports CLEAR over ZERO records, with a false sentence. **MINOR**

For H2axS2 the analyzer prints:

```
CLEAR | an absolute read/edit index | 0 records, every index == len(input_ids)+rel_end
```

`audit_end_relative` (`:344-350`) deliberately returns, for an all-position arm,
`{"n_records": 0, "not_applicable": True, "ok": True, "witness_note": "... Not applicable, not
passed."}` -- the producer says in words that this is not a pass. `build_void_clauses`
(`:4040-4044`) tests `aud.get("ok") is True` **first**, never reads `not_applicable`, and emits
CLEAR with a sentence asserting a universal quantifier over an empty set. The dedicated
`NOT_APPLICABLE` branch three lines below (`:4048`) is unreachable for this case. This is the
repo's own "a check that reads the producer's own field and prints PASS" pattern.

Both statuses are non-tripped, so the verdict is unaffected -- but the artifact contains a false
statement, and the mutation suite does not catch it.

### 7c. Holm is computed and printed but never gates anything. **MINOR**

`primary.success._holm` says *"each of the six family members is assessed under Holm within
PHASE9_CAUSAL **before its conjunction is evaluated**"*. In `analyse` the only alpha used anywhere
is `alpha = float(pr.require("primary","alpha"))` = 0.05 (`:4163`), passed unchanged to
`evaluate_success` and to `o1_moved`/`o2_moved` at `:4457-4459`. The Holm per-member threshold is
printed and stored, and read by no decision. Today it is harmless (S2 rejects under Holm anyway;
S1's p=0.808 fails under either threshold), but it is the "threshold published but never enforced"
shape this file's own docstrings say has now been committed four times.

### 7d. `_find_run` takes newest-complete before the split check -- latent, and clean here. **NON-ISSUE**

`_find_run` (`scripts/dcs_ts_pr048_analysis.py:251-267`) returns the lexicographically last
directory carrying `DONE.json`; the stage/split binding is checked *after* (`:4204-4217`) and would
REFUSE a wrong-split run rather than analyse it. `h2a_s1_projout_button` has **three** complete run
directories. I checked what each bound:

```
..._043320_3252166  ->  exclude_..._button_bomb_validation.txt   O2 +0.002723  p=0.746  n=23
..._133924_3330294  ->  exclude_..._button_bomb_train.txt        O2 +0.035428  p=0.255  n=4
..._155134_3905688  ->  exclude_..._button_bomb_test.txt         O2 -0.002997  p=0.808  n=23   <- bound
```

Newest is the TEST run, so the analysis bound the right one and **TEST was read once**. The
fragility is that ordering alone decides and only then does the guard fire -- but the guard is a
hard refusal, so a wrong pick fails loudly rather than silently. Not a finding against this run.

### 7e. Cross-launch pairing for the S1 O1 contrast -- checked, defused. **NON-ISSUE**

The S1 arm run is PID 3905688 (15:51) while its C5 bridge and its five C1 draws are PID 3414524
(17:19+). The O1 contrast therefore pairs two different launches. Determinism across launches is
demonstrated empirically by the I-N1 gate itself: the bridge (3414524) is **byte-identical** to the
PHASE 7 untouched baseline (a third launch, 3183103, 2026-09-07) on every paired row, with the
outcome sha computed over the shared prompt_ids on both sides (`:4396-4409`). S2's arm, bridge and
draws are all 3414524.

### 7f. What was checked and is genuinely clean

All nine `primary.void` clauses on both family members: direction fitted on 67 TRAIN domains only;
`hook_fired_count` 230/230 and 1840/1840; realised cells == expected (920/920 and 1753120/1753120);
the C5 disabled-hook bridge byte-identical to the untouched baseline; 5 distinct control-draw
hashes; bank sha matches the pin (`button_bomb`). All four `primary.cannot_answer` clauses: PHASE 7
baseline present, option_mass CLEAR (channel engaged), realised power CLEAR, H1 NOT_APPLICABLE with
the correct "CANNOT ANSWER BY CONSTRUCTION, not evidence" wording. No UNEVALUABLE clause on either
member. 30 arms, 0 check failures, 6900 rows = 30 x 230. **Nothing found that should have made this
run VOID.**

---

## Summary

| # | Finding | Severity | Changes the VERDICT? |
|---|---|---|---|
| 1 | Conjunct 1 scored against O2's expected sign (`:4386-4387` / `:1600`); O1 moved in the INTENDED direction on both arms and was printed as FAIL; S2's count is 3/4, not 2/4 | SERIOUS | **No** (both classes unchanged); yes to the conjunct table and printed count |
| 2 | S1 negative is real (equivalence CI [-0.0284,+0.0224] vs a 0.5-nat declared MDE), but power/SD/MDE and an arm-level equivalence interval are never printed | MINOR | No |
| 3 | Conjunct 3 matches the declared test exactly; the opposite-sign fact is discarded but does not rescue a claim | NON-ISSUE | No |
| 4 | Holm: m=6, absent at p=1.0, thresholds and step-down all recomputed by hand and correct | NON-ISSUE | No |
| 5 | C1 cross-bank fix: button selectors identical pre/post; only basket lost its bogus control | NON-ISSUE | No |
| 6 | `frac_cellmean_spread_removed=0.1656` is exactly `cos^2(v_bomb_specific, v_bomb)` -- definitional, not measured (F-4 confirmed at all 8 layers) | SERIOUS | No, but it changes what the null is scoped to |
| 7a | C3 and C4 ran, passed liveness, and are analysed nowhere; C4 moves O2 +1.24 at S2 (~2x the arm, opposite sign) and +0.149 at S1 | SERIOUS | No |
| 7b | Index-audit void clause prints CLEAR over 0 records with a false universal sentence | MINOR | No |
| 7c | Holm thresholds computed, printed, and never read by any decision | MINOR | No |
| 7d/e | `_find_run` newest-wins before the split guard; cross-launch O1 pairing -- both checked and clean | NON-ISSUE | No |

**Verdict: YES with one correction -- the two verdict CLASSES (S1 NEGATIVE, S2 NOT A CAUSAL RESULT)
are trustworthy and I could not refute either, but the per-condition table is wrong on conjunct 1
for both arms (S2 is 3/4, not 2/4), and the dose the null is scoped to is a definitional cosine
rather than a measured intervention.**

---

# APPENDIX F -- THE FIXES, AND THE CORRECTED RE-RUN (2026-09-08)

Written by the agent that implemented the review's findings. One file was edited:
`scripts/dcs_ts_pr057_causal.py`. **No frozen config was touched**
(`configs/dcs_ts_pr057_phase9.json` and `configs/dcs_ts_pr060_phase9_amendment.json` are
byte-identical), no file another agent holds was touched, and no `git add` / `commit` / `stash`
was run.

Python: `/home/sharifm/students/omeryosef/miniconda3/envs/poc_stage2/bin/python`. CPU only. No
SLURM job was submitted or cancelled.

## F.0 Harness, my observed numbers

| command | before | **after** |
|---|---|---|
| `--self-test` | 111 checks / 0 FAILED | **117 checks, 0 FAILED** (rc=0) |
| `--mutate` | 90/90 RED | **102/102 mutations produced a refusal** (rc=0) |

Twelve new mutations, all observed RED:

```
M89 D-1 conjunct 1 scored against O2's sign        -> gate says ok=False
M90 D-1 conjunct 2 scored against O1's sign        -> gate says ok=False
M91 D-1 ONE shared expected_sign for both          -> refusal (evaluate_success refuses by name)
M92 D-1 an outcome with NO sign of its own         -> refusal (NotMeasured)
M93 D-2 a null on the DEFINITIONAL dose alone      -> refusal (NotMeasured)
M94 D-2 a measured dose recorded EMPTY             -> refusal (NotMeasured)
M95 D-2 the cellmean figure printed UNLABELLED     -> gate says ok=False
M96 D-3 a built C4 arm reported NOWHERE            -> refusal (1 arm analysed nowhere)
M97 D-3 NO concept-free control reported at all    -> refusal (2 arms analysed nowhere)
M98 D-3 a C3/C4 control from ANOTHER bank          -> refusal (C4 REFUSED, by name)
M99 D-3 a C3/C4 control at ANOTHER scope           -> refusal (C4 REFUSED, by name)
M100 7b: a void clause CLEAR over ZERO records     -> gate says ok=False
```

and five new self-test checks: `conjuncts_use_their_own_expected_sign`,
`o1_scored_against_o2s_sign_FAILS`, `shared_expected_sign_REFUSED`,
`outcome_without_its_own_sign_REFUSED`, `cellmean_dose_is_labelled_DEFINITIONAL`,
`null_with_ONLY_the_definitional_dose_REFUSED`.

## F.1 DEFECT 1 (Finding 1) -- each conjunct is now scored against ITS OWN sign

`evaluate_success` no longer accepts a direction from its caller at all. A new
`outcome_expected_sign(outcome, name)` reads `outcome["expected_sign"]` -- which
`paired_outcome` already writes on both O1 (+1) and O2 (-1) -- and refuses (`NotMeasured`) an
outcome record that does not carry its own. The legacy `expected_sign=` parameter survives only
as a tripwire: a caller that still passes one is REFUSED by name, because one shared sign
necessarily scores one of two opposite-signed outcomes against the other's direction. The call
site at `analyse()` now reads `evaluate_success(o1, o2, control, across, alpha)`.

The success record also carries `_expected_signs = {"O1": 1, "O2": -1}` and the printed block
states the two signs under the conjunct table, so a reader can see they are opposite.

The internal contradiction is gone: `[PASS] 1_probe_moves_intended` now agrees with
`DECODABLE BUT NOT CAUSALLY USED`, both of which rest on `o1_moved == True`.

## F.2 DEFECT 2 (Finding 6) -- the dose the null is scoped to is the MEASURED one

`format_realised_dose` now prints `MEASURED cell_residual_frac_removed=...` **first**, and
`frac_cellmean_spread_removed` / `norm_frac_removed` only as bracketed "definitional, for
reference only" figures, followed once by `DEFINITIONAL_DOSE_NOTE`:

> DEFINITIONAL, NOT MEASURED: with only two cells (A, C) the centred cell-mean matrix is rank 1,
> so frac_cellmean_spread_removed collapses identically to cos^2(edited direction, m_A - m_C) =
> cos^2(v_bomb_specific, v_bomb) -- a geometric property of two directions from the same fit,
> identical at every edited layer and computable without loading the model. It is NOT an
> intervention measurement and NO null is scoped to it.

The header of every dose line reads `REALISED DOSE (the null above is scoped to the MEASURED
figure, cell_residual_frac_removed)`, and the same statement is added to the run-level
`SCOPE LIMITS THAT TRAVEL WITH EVERY SENTENCE ABOVE` block.

**A null is still impossible to emit without a dose** (`verdict()._null` still calls
`format_realised_dose`, and `M75 a null with NO realised dose` is still RED) -- and it is now
*also* impossible to emit with only the definitional one: an entry whose
`cell_residual_frac_removed` is absent or empty raises `NotMeasured` (M93/M94).

## F.3 DEFECT 3 (Finding 7a) -- C3 and C4 are analysed, printed, and gated

New `concept_free_control_report()` computes each C3/C4 arm against the SAME untouched PHASE 7
baseline as the arm, with C1's discipline: an equivalence interval over the domain-level deltas,
the direction and draw seed named, the sign reported, the permutation p beside its attainable
floor, and the ratio to the arm's own delta. Bank / scope / target-concept mismatches are
REFUSED by name (M98/M99), exactly as `control_c1_report` refuses a cross-bank C1 draw.

New `concept_free_controls_reported_gate()` refuses the whole report if any C3/C4 arm that ran is
not in it (M96/M97). Observed on the re-run: `every C3/C4 concept-free control that ran is
reported above (4 of 4)`.

**The C4 numbers, observed:**

| arm | delta | p | floor | equivalence 95% CI | |C4| / |arm| | sign vs arm | domains moving O2's intended way |
|---|---|---|---|---|---|---|---|
| `c4_samenorm_orth_s1` | **+0.149133** | at the floor | 9.999e-05 | [+0.118710, +0.179557] | **49.75x** | OPPOSITE | 0/23 |
| `c4_samenorm_orth_s2` | **+1.237557** | at the floor | 9.999e-05 | [+0.789922, +1.685192] | **1.93x** | OPPOSITE | 5/23 |

and C3, for completeness:

| arm | delta | p | equivalence 95% CI | |C3| / |arm| | sign vs arm | domains |
|---|---|---|---|---|---|---|
| `c3_vremap_s1` | -0.047336 | 0.0781922 | [-0.100677, +0.006005] | 15.79x | SAME | 17/23 |
| `c3_vremap_s2` | -2.844680 | at the floor | [-3.153896, -2.535464] | 4.43x | SAME | 23/23 |

The printed C4 sentence at both scopes is not left to implication:

> DECISIVE AGAINST A DIRECTION READING: a CONCEPT-FREE, norm-matched, equal-magnitude ADD
> ORTHOGONAL to the concept subspace moves O2 by +1.237557 (p at the floor) where the concept
> edit moves it by -0.642195 -- 1.93x as far, in the OPPOSITE direction to the arm. Whatever
> moved the readout at these sites moved it for a reason that does not need the concept
> direction: at this norm the site is perturbation-sensitive, and the arm's own movement cannot
> be read as the concept direction being used.

## F.4 The two "cheap if safe" items

**7b -- FIXED.** `build_void_clauses` now tests `not_applicable` (and a zero-record audit)
*before* `ok is True`, so the index clause on an all-position arm prints
`NOT_APPLICABLE -- the audit bound ZERO records and is NOT APPLICABLE, NOT PASSED` instead of
`CLEAR ... 0 records, every index == ...`. Verified on the re-run: H2axS2's clause is now
`void[NOT_APPLICABLE]`. `audit_end_relative` was NOT touched (it is correct; the reader was
wrong). M100 shows the old behaviour RED.

**7c -- ENFORCED, not silently changed.** Making Holm the alpha of the conjunction would have
required a two-pass restructure and would have changed the meaning of O1's and C1's tests too, so
that was NOT done. What was done: after `holm_with_absent`, the analyzer re-evaluates conjunct 2
at each member's **Holm per-member threshold** and REFUSES the report if that disagrees with the
verdict published at `primary.alpha`. The threshold is now read by a decision. Observed:

```
H2axS1  Holm threshold 0.01       -> FAIL ; alpha 0.05 -> FAIL ; AGREE
H2axS2  Holm threshold 0.00833333 -> PASS ; alpha 0.05 -> PASS ; AGREE
```

**Finding 2's reporting gap -- also closed** (cheap, no behaviour change): each member now prints
`NULL RESOLUTION` with the realised between-domain SD, n, power at the declared MDE, the bar and
`mde_at_bar`, plus the ARM's own O2 equivalence interval:

```
H2axS1  SD 0.058754  n=23  power 1.000 @ MDE 0.50 (bar 0.80)  mde_at_bar 0.035915
        arm O2 equivalence 95% CI [-0.028405, +0.022410]
H2axS2  SD 0.429050  n=23  power 1.000 @ MDE 0.50 (bar 0.80)  mde_at_bar 0.262268
        arm O2 equivalence 95% CI [-0.827730, -0.456660]
```

## F.5 THE RE-RUN -- corrected per-condition table

```
python scripts/dcs_ts_pr057_causal.py --stage h2 --split test \
       --fit-dir outputs/dcs_ts/directions_pr053 --out <scratch>/analysis_fixed.json   # rc=0
```

30 arms loaded, 0 check failures. Holm: family PHASE9_CAUSAL, m = 6 (NOT reduced), absent members
`['H1xS1','H1xS2','H2bxS1','H2bxS2']` at p = 1.0.

| conjunct | H2axS1 published | **H2axS1 corrected** | H2axS2 published | **H2axS2 corrected** |
|---|---|---|---|---|
| 1 `_probe_moves_intended` | FAIL | **PASS** | FAIL | **PASS** |
| 2 `_semantic_readout_moves_intended` | FAIL | FAIL | PASS | PASS |
| 3 `_matched_random_control_does_not_move` | PASS | PASS | FAIL | FAIL |
| 4 `_holds_across_domains` | FAIL | FAIL | PASS | PASS |
| count | 1/4 | **2/4** | 2/4 | **3/4** |
| Holm | p=0.807519 vs 0.01, reject=False | unchanged | p=9.999e-05 vs 0.00833333, reject=True | unchanged |
| verdict class | NEGATIVE | **NEGATIVE (unchanged)** | NOT A CAUSAL RESULT | **NOT A CAUSAL RESULT (unchanged)** |

Outcome numbers, unchanged to every printed digit: H2axS1 O2 -0.002997 (p 0.807519, 15/23
domains), O1 +0.391905 (p at floor), C1 equivalence [-0.008842, +0.007934], smallest draw p
0.511149. H2axS2 O2 -0.642195 (p at floor, 21/23), O1 +0.317962 (p at floor), C1 equivalence
[+0.115897, +0.206261], smallest draw p 9.999e-05.

**Verdict literals, verbatim from the re-run:**

* H2axS1 -- `NEGATIVE`: *"DECODABLE BUT NOT CAUSALLY USED UNDER THIS INTERVENTION  REALISED DOSE
  (the null above is scoped to the MEASURED figure, cell_residual_frac_removed) --
  v_bomb_specific|L9|alpha1: MEASURED cell_residual_frac_removed={'C': 0.0936} [definitional, for
  reference only: frac_cellmean_spread_removed=0.1656, norm_frac_removed=0.4069]  ||
  DEFINITIONAL, NOT MEASURED: ..."*
* H2axS2 -- `NOT A CAUSAL RESULT`: *"NOT A CAUSAL RESULT -- the conjunctive criterion is not met
  (**3/4** conditions). Reported as such, per condition."* followed by the eight per-layer
  measured doses (`cell_residual_frac_removed` L7..L14 = 0.1003, 0.0396, 0.0936, 0.1412, 0.1681,
  0.2058, 0.2106, 0.1729) and the definitional note once.

**BOTH VERDICT CLASSES HELD.** S1 is still `NEGATIVE`, S2 is still `NOT A CAUSAL RESULT`. The
only changes a reader sees are the ones the review predicted: conjunct 1 flips to PASS on both
arms, S2's count becomes 3/4, the single failing conjunct on S2 is the CONTROL rather than the
probe, and the dose, the C3/C4 controls and the null-resolution numbers are now on the page.

## F.6 Still open after these fixes

1. **Holm still does not set the alpha of the conjunction.** It is now *enforced* (a disagreement
   refuses) rather than decorative, but the frozen sentence "assessed under Holm before its
   conjunction is evaluated" is satisfied by an agreement check, not by using the Holm threshold
   as the test's alpha. Doing it properly needs a two-pass `analyse()` and would also change O1's
   and C1's alphas, which is a design question, not a code fix.
2. **The measured dose is itself bank-borrowed.** `meta.cell_means_note` says the PR-053 cell
   means are TRAIN rows of the development codeword's BOMB bank only, so the basket arms' dose
   records are borrowed. Those arms are O2-only and make no claim (Finding 6's secondary note),
   but the labelling now printed does not say so per arm.
3. **C2 (shuffled labels) still has no artifact** and C7/H1/H2b still have no code path -- all
   four already carried as stated scope limits.
4. **`_find_run` still takes newest-complete before the split guard** (Finding 7d). Clean on this
   run; the guard is a hard refusal, so a wrong pick fails loudly. Not changed.
5. The C3 arm is the **raw** axis, not a remapping-only axis (R-111 question D failed), so its
   numbers bound what the raw axis does at these sites and nothing finer. The printed C3 sentence
   says this; no arm in this design isolates remapping.
