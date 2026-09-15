# DCS-CSI Phase-1 adversarial code review

Scope: `src/boombness/donor_patch.py` (new `SubspaceDonorPatch`, `orthonormalise`,
`assert_token_identity` factoring), the new `--rescue-basis*` path in
`src/boombness/score_behavior.py`, `scripts/dcs_csi_axis.py` (whole file), and
`tests/test_subspace_donor_patch.py`.

Reviewer's bottom line: **the core numerical primitive is sound.** The two things that would
destroy the experiment outright -- full-rank equivalence with `DonorPatch`, and per-position norm
matching -- were both verified numerically and are **exact**, not approximate. The ridge dual and
the PLS1 deflation are also correct. There are **no BLOCKERs**.

What is wrong is a ring of *unenforced* guards around a correct core: three separate ways to bind
the right basis to the wrong experiment and have the run complete cleanly, one vacuous unit test,
and one documented candidate family that cannot be produced at all.

All scratch scripts: `/tmp/claude-47249/.../scratchpad/e1.py` .. `e5.py`.

---

## BLOCKER

None.

---

## MAJOR

### M1. `--fit-prompt semantic` is unreachable; `--fit-prompt` is pure unvalidated provenance
`scripts/dcs_csi_axis.py:199` (`ap.add_argument("--fit-prompt", ...)`), consumed only at
`:246` (`"fit_prompt": a.fit_prompt`).

The module docstring ("TWO CANDIDATE FAMILIES, DELIBERATELY ... VALIDATION adjudicates between
them (plan section 4.2)") promises a `semantic` family. But the corpus is loaded through
`lpm.load_corpus` (`dcs_csi_axis.py:223`), and `scripts/dcs_cont_layerpos_map.py:172-176` does:

```python
qks = {r.get("query_kind") for r in rows}
if qks != {"behavioral"}:
    raise Refusal("the predictor corpus must be the BEHAVIOURAL population; ...")
```

`Refusal` is a `RuntimeError` (`dcs_cont_layerpos_map.py:52`), not caught anywhere in
`dcs_csi_axis.main()`. So `--fit-prompt semantic` **cannot run** -- it dies with an uncaught
traceback whose message is about a *different* concept ("predictor corpus"), so the operator will
read it as a wrong-directory mistake, not as "this arm does not exist".

Two distinct problems:
1. A candidate family the plan says VALIDATION will adjudicate between is not constructible. If
   Phase 1 reports "we compared the semantic-fit and behavioural-fit axes", that claim has no
   producing code path.
2. `--fit-prompt` is written into `meta["fit_prompt"]` and printed by `score_behavior` without
   ever being cross-checked against the corpus. It is a required flag whose only effect is a
   free-text label. If the `load_corpus` guard is ever relaxed (it is one `if` away), passing
   `--fit-prompt behavioral` with a semantic corpus mislabels the entire artifact and nothing
   catches it.

*Wrong number:* Phase 1 concludes "the behavioural axis transfers but the semantic axis does not",
when in fact only one of the two was ever fit.

*Fix:* either wire `--fit-prompt` into a real corpus assertion
(`{"semantic": {"semantic_one_word"}, "behavioral": {"behavioral"}}[a.fit_prompt] == qks`, with a
`load_corpus(..., allow_query_kinds=...)` parameter), or delete the flag and the docstring's
two-family claim.

---

### M2. Layer mismatch between the fitted axis and `--rescue-layer` is a WARNING, not a refusal
`src/boombness/score_behavior.py:2040-2042`.

```python
if m.get("selected_layer") is not None and int(m["selected_layer"]) != int(args.rescue_layer):
    print("[rescue-basis] WARNING: basis was fit at layer L%s but --rescue-layer is L%s" ...)
```

The residual basis is fit at one layer. Residual-stream geometry is layer-specific; a direction
learned at L18 written at L24 is a direction with no interpretation. This produces a *perfectly
plausible* number -- some nonzero recovery, or a clean null -- and the only evidence is a `print`
in a SLURM `.out` that nobody greps.

This is also this repo's own recorded bug class: *thresholds published but never enforced*
(memory `feedback_published_threshold_never_enforced.md`). Compare `assert_control_norm_matched`
(`score_behavior.py:1355`), which for the attn-knockout controls does `raise SystemExit` on
exactly the analogous condition.

*Verification:* read; no `raise` on this path.

*Fix:* `raise SystemExit`, with an explicit `--allow-layer-mismatch` escape hatch if a
cross-layer transfer arm is ever wanted, and record the flag on the row.

---

### M3. Nothing cross-checks the axis's codeword / bank against the scoring run
`score_behavior.py:2018-2039`; the fields exist at `dcs_csi_axis.py:244-246`
(`"codeword": a.codeword, ... "bank_sha16": csha`).

`dcs_csi_axis.py` goes to real trouble to refuse a mismatched corpus/readout pair
(`:225-228`, `rsha != csha`), because -- per `readout_bank_sha`'s own docstring -- a `basket_*`
readout joins every TRAIN key of a `button` corpus silently and moves the target mean from 0.678
to 0.045. The `.pt` therefore carries `codeword` and `bank_sha16`.

`make_rescue_basis_loader` reads `meta` and prints `fit_prompt`, `site`, `selected_layer`,
`fit_domains`, `sha16`, `norm_match`. It reads **neither `codeword` nor `bank_sha16`**, and
compares neither against `args.bank` / the row's `codeword`. A button-fit axis applied to a basket
run executes without a murmur.

*Wrong number:* the entire basket subspace arm, run against the button axis, reported as a null
for "the installation variable is not causal in basket".

*Fix:* refuse unless `meta["bank_sha16"]` matches the run's bank sha and `meta["codeword"]`
matches the run's codeword.

---

### M4. The TRAIN-fit axis can be evaluated on the TRAIN rows, and the artifact cannot detect it
`score_behavior.py` argparse (no split filter exists -- verified by grep: there is no `--split`,
`--domains`, or `--only-split` flag) and `score_behavior.py:3824-3827`.

`--rescue-basis`'s own help text says "The basis must have been fit on TRAIN only; this script
does not verify that and records the basis provenance so the analysis can." But the provenance it
records on the row is only:

```python
"rescue_basis": os.path.basename(args.rescue_basis),
"rescue_basis_key": ..., "rescue_norm_match_key": ...,
```

The fit-domain list and split live in `meta["fit_population"]["domains"]` and are **printed to
stdout only** -- never written to `results.jsonl`, never written to a run-config artifact. So the
downstream analysis *cannot* do the check the help text delegates to it from the results file
alone; it has to go find the `.pt`, which it can only locate by basename (see m5).

Combined with there being no population filter, the default behaviour is that a TRAIN-fit axis is
scored on a population that includes its own fit domains.

*Wrong number:* a recovery fraction inflated by in-sample fit, indistinguishable in the artifact
from an out-of-sample one.

*Fix:* write `rescue_basis_fit_split`, `rescue_basis_fit_domains`, `rescue_basis_sha16`,
`rescue_basis_fit_layer` and `rescue_basis_codeword` onto every row; and refuse (or at minimum
count and report) rows whose `domain` is in the axis's fit-domain list.

---

### M5. The degenerate norm-match branch is recorded but never enforced
`src/boombness/donor_patch.py:243-249`, surfaced as
`liveness()["n_positions_norm_match_degenerate"]`.

When a control subspace carries essentially none of the delta, the code injects along
`W.sum(0)/||W.sum(0)||` and records the count. Nothing -- not the patcher, not
`score_behavior`, not any downstream gate I can find -- ever reads that count and refuses.

This matters because the fallback direction is *not* a meaningful control direction: it is an
arbitrary artifact of the QR gauge that `orthonormalise` happens to return
(`donor_patch.py:163`, `torch.linalg.qr`). For rank > 1 it is not even reproducible across
LAPACK/torch versions. A control arm that is 100% degenerate is injecting a norm-matched but
scientifically meaningless vector, and the run completes with `fired=True`, `wrote_nonzero=True`.

Note the contrast with `assert_control_norm_matched` (`score_behavior.py:1355`), whose docstring
says "a check that binds nothing is not a check" and which `raise SystemExit`s. The new path has
the diagnostic without the refusal.

*Also:* if `W.sum(0)` is itself near zero (possible for rank >= 2 with an unlucky QR gauge),
`W.sum(0)/W.sum(0).norm().clamp_min(1e-12)` yields a near-zero "unit" vector and the control
writes ~nothing while `written_norm_mean` correctly reports ~0 -- silently a zero-perturbation
control, which is exactly the "a control that cannot fail" failure the comment above it warns
against.

*Fix:* refuse the row (or the arm) when the degenerate fraction exceeds a stated threshold;
normalise the fallback to the first orthonormal row `W[0]` (gauge-stable under QR only for r=1, so
better: derive it deterministically from a seeded RNG projected into span(W) and record the seed);
and assert `||unit|| ~ 1` before writing.

---

### M6. `tests/test_subspace_donor_patch.py:196-210` -- the add-then-remove test is VACUOUS
```python
sp_fwd = SubspaceDonorPatch(model, donor, ids, basis=full_basis)
sp_bwd = SubspaceDonorPatch(model, back,  ids, basis=full_basis)
with sp_fwd:
    _ = _run(model, ids)          # <-- result discarded; patch is per-forward, not persistent
with sp_bwd:
    out_back = _run(model, ids)
check("remove-after-add returns the unpatched forward", torch.allclose(out_back, base_out, ...))
```

The two patches are applied in **separate forward passes**. A forward hook mutates the activation
tensor of *that* forward only; the model is unchanged afterwards. So `sp_bwd` runs on a completely
clean forward, and `back` holds that same clean forward's own activations. The delta is identically
zero, the projection is zero, and the assertion is `base_out == base_out`.

The docstring says this test exists because "Phase 2's necessity arm is the same primitive with
the donor swapped". It tests nothing about that.

*Verified numerically* (`scratchpad/e3.py`):
```
=== E4: is the add-then-remove test vacuous? ===
 out_back == base ? True max|d| 0.0
 spb dose delta_norm_mean (0 => the 'remove' wrote NOTHING): 0.0
 spb written_norm_mean: 0.0
 with scale=0.0 (remove disabled) the SAME assertion still passes: True
```
The last line is the proof: constructing the "remove" patch with `scale=0.0`, i.e. with the write
path deliberately switched off, passes the identical assertion.

*Fix:* test the composition arithmetically instead of through the model. Capture `h` at the layer,
compute `h1 = h + P_W(h_donor - h)` by hand, then `h2 = h1 + P_W(h - h1)`, and assert
`P_W h2 == P_W h`. Or: run the forward *nested* -- `with sp_fwd: with sp_bwd:` -- with `sp_bwd`
registered second so it sees the post-`sp_fwd` state, and assert the composed hook output equals
the unpatched one. Either way the current test must not be counted as covering the necessity arm.

---

## MINOR

### m1. `dcs_csi_axis.py:241-243` -- the contamination guard is tautologically empty
```python
bad = [d for d in fit_doms if d in VA or d in TE or d in EX]
```
`fit_doms = sorted(corpus_doms & TR)` and `TR = {d for d,v in assign.items() if v=="train"} - EX`.
A domain with `assign[d]=="train"` cannot satisfy `v=="validation"` or `v=="test"`, and `- EX`
already removed the excluded ones. `bad` is **always** `[]`. The "disjointness assertions stated as
refusals" the comment advertises are a check reading the same source it is checking -- this repo's
`feedback_check_reads_same_broken_source.md` pattern.

It is not wrong today (the construction is genuinely sound), but it provides false assurance: if
someone later changes `fit_doms` to come from anywhere other than `& TR`, the guard still cannot
fire. *Fix:* assert against the raw manifest -- `assign[d] == "train"` for every `d in fit_doms`,
plus `set(fit_doms).isdisjoint(VA | TE | EX)` computed from `assign` directly.

### m2. The prefill/decode guard is wrong when `max(positions) == 0`
`donor_patch.py:124` (`DonorPatch`) and `:221` (`SubspaceDonorPatch`), both
`if hidden.shape[1] <= max(self.donor.positions, default=-1): return output`.

A cached decode step has `hidden.shape[1] == 1`. If the donor's only/largest position is `0`, then
`1 <= 0` is `False` and the guard does not fire: the patch writes the donor's position-0
activation onto **every generated token** as it is decoded.

*Verified* (`scratchpad/e3.py`):
```
=== E6: decode guard when max(positions)==0 ===
 seq_len=1, positions=[0]: n_written = 1  -> guard shape[1]<=max(pos) is 1<=0 == False, so it PATCHED a decode step
 DonorPatch same case n_written = 1
```
Both patchers. Latent today (demo-block and query-span positions are >0 in practice), but the
failure is silent and produces a plausible "the rescue worked spectacularly" result.
*Fix:* guard on identity, not size: record `seq_len` at donor-capture time and refuse to fire
unless `hidden.shape[1] == self.donor.seq_len_at_capture` (or at least
`hidden.shape[1] > max(positions)` **and** `hidden.shape[1] > 1`).

### m3. `dcs_csi_axis.build()` -- two silent row drops, neither counted
`dcs_csi_axis.py:73-75` (`t = mp["reps"].get(r["prompt_id"]); if t is None: continue`) and
`:82` (`comp = [k for k in comp if k in inst]`).

Both are `.get`/membership fallbacks on scientifically load-bearing joins, and neither records how
many rows it dropped. `out["n_fit_rows"]` reports the survivors only.

I checked whether this is *differential*: both filters are layer-independent and site-independent,
so the layer grid in `train_loo_rho_by_layer` is scored on an identical population and the layer
selection is not biased by them. That is the reassuring part. But a half-populated readout would
silently shrink the fit population by an arbitrary amount and the JSON would look identical in
structure.
*Fix:* count and record `n_rows_dropped_no_reps` and `n_keys_dropped_no_installation`, and refuse
below a stated retention fraction.

### m4. Nested selection over 9 layers x 5 ranks, reported with no selection correction
`dcs_csi_axis.py:266-276` picks `max` over `PLATEAU` (9 layers), `:292-302` picks `max` over 5
ranks. `train_loo_rho_at_selected_layer` is then written into the artifact as a number.

Measured null spread of `loo_rho` on a 12-domain x 8-row synthetic null (`scratchpad/e4.py`):
`mean rho = +0.0361, sd = 0.1596`. E[max of 9 such draws] is ~ +0.24 under a pure null. The real
n (~700 rows) will have a smaller sd, but the point stands: the selected rho is a maximum, not an
estimate, and is stored in the same JSON under a name that does not say so.

The script's `print` does say "a rank chosen on TRAIN is a candidate, not a finding" -- but only
for the rank, only on stdout, and not for the layer. *Fix:* record the full grid (it does) **and**
record `selected_layer_is_argmax_over_n=9` / the null band, and name the field
`train_loo_rho_at_selected_layer_SELECTED` so no analysis quotes it as an unbiased rho.

### m5. The recorded `sha16` does not hash the tensor that is actually saved
`dcs_csi_axis.py:330-332`:
```python
out["bases"] = {k: {"rank": ..., "sha16": sha16(B)} for k, B in bases.items()}   # B is float64
torch.save({"meta": out, "bases": {k: B.to(torch.float32) for k, B in bases.items()}}, ...)
```
`sha16` hashes the **float64** bytes; the file stores **float32**. Re-hashing the loaded tensor
(even after `.to(torch.float64)`) will never reproduce the recorded digest, so the provenance hash
that `score_behavior` prints is unverifiable in principle. *Fix:* build `B32 = B.to(torch.float32)`
once, hash and save the same object.

### m6. `make_rescue_basis_loader` validates lazily, after the model is loaded
`score_behavior.py:2003-2049`, bound at `:2388` but first invoked at `:3622`.

`--rescue-basis-key` typos, missing keys, hidden-dim mismatches and the layer-mismatch warning are
all discovered only when the first row reaches the rescue block -- i.e. after weight loading, and
after any row that `ledger.fail`s earlier. The two guards at `:2389-2393` are eager but only cover
the two cheapest cases. The cache itself is correct: `state` is per-run, `args` is immutable after
`parse_args`, `if not state` is only False after all three keys are set, and the keys cannot be
confused (`B` and `NB` are looked up under distinct flags). `weights_only=False` is required here
because the blob is a `{"meta": dict, "bases": dict}` mix, and the file is repo-local -- acceptable,
though `weights_only=True` plus a separate JSON sidecar (which the script already writes!) would be
strictly better.
*Fix:* call `_rescue_bases()` once, eagerly, right after the `:2389-2393` guards.

### m7. `scale` is applied after norm matching, silently breaking the match
`donor_patch.py:254-256`. If `scale != 1.0` and `norm_match_basis` is set, the written norm is
`scale * target`, not `target`. The dose fields report it honestly, but the constructor accepts the
combination without comment. `score_behavior` never passes `scale`, so this is latent.
*Fix:* refuse `scale != 1.0` together with `norm_match_basis`, or apply `scale` to `target` before
the match so a dose-response sweep stays matched at every dose.

### m8. `orthonormalise` accepts a numerically degenerate basis
`donor_patch.py:160-162` uses `torch.linalg.matrix_rank(B)` with the default float64 tolerance,
after `B` has been upcast from the **float32** stored in the `.pt`.

*Verified* (`scratchpad/e3.py`):
```
 near-degenerate ACCEPTED (rows [1,0,0] and [1,1e-9,0]), gram = I
 1e-14-degenerate ACCEPTED, Q = [[1,-0,-0],[0,1,-0]]
```
A rank-r PLS basis whose r-th component is degenerate at float32 precision (~1e-7) will look
full-rank in float64, and QR will hand back an r-th direction that is pure float32 rounding noise.
The projector is then "rank r" in name and rank r-1 in substance -- the exact defect the `pls1`
docstring says this phase already shipped once.
*Fix:* check the singular-value spectrum against an explicit tolerance tied to the *stored* dtype,
e.g. `s[-1] / s[0] > 1e-4`, and refuse below it. (Also: `matrix_rank` is computed twice, once in
the condition and once in the message -- a cheap nit.)

### m9. `max_abs_cosine_with_cand_rank1` is a per-row cosine, not a subspace overlap
`dcs_csi_axis.py:322-325`: `cos[k] = float((B @ w1).abs().max())`. For a rank-r `B` this is the
largest cosine between `w1` and any single **row** of `B`, which systematically **understates** the
overlap between `w1` and `span(B)` (the correct quantity is `||B w1||`, since `B` is orthonormal
here). A `cand_pls3` whose rows each sit at 45 degrees to `w1` but which contains `w1` in its span
would be reported as 0.71, not 1.0. This is a reporting field, not a fit, so it cannot change a
result -- but it is the field an analyst would use to argue the controls are distinct from the
candidate. *Fix:* `float((B @ w1).norm())`.

### m10. bf16 write-back attenuates the delta; the dose is reported pre-cast
`donor_patch.py:257` (`new = (cur + proj).to(hidden.dtype)`) vs `:266`
(`"written_norm_mean": float(written_norm.mean())`, computed in float64 before the cast).

*Verified* (`scratchpad/e5.py`, hidden=4096, `||h||=100`, bf16):
```
 delta_frac | ||proj||/||h|| | reported | actually applied | ratio
   0.50     |    6.0e-03     |  0.6025  |     0.6120       | 1.016
   0.10     |    1.6e-03     |  0.1552  |     0.1495       | 0.963
   0.05     |    7.0e-04     |  0.0701  |     0.0546       | 0.778
   0.02     |    2.7e-04     |  0.0270  |     0.0140       | 0.520
rank-1 CANDIDATE capturing 30% of delta: ratio 1.001 - 1.005 at every delta_frac tested
```
Good news, and the reason this is MINOR not MAJOR: a real candidate axis capturing ~30% of the
delta writes a perturbation large enough that bf16 rounding is negligible (ratio ~1.00), and
norm-matched controls inherit the candidate's norm so they are equally safe. Only the **unmatched**
control arm (`--rescue-basis-key ctrl_random* ` *without* `--rescue-norm-match-key`), where a rank-1
random direction captures `~1/sqrt(4096)` of the delta, lands in the attenuated regime -- and its
reported `written_norm_mean` then overstates what the model actually saw by up to 2x. This is one
more reason the unmatched-control arm should not be interpreted quantitatively.
*Fix:* compute the applied delta after the cast -- `applied = (new.to(torch.float64) - cur)` -- and
report `applied.norm(dim=1).mean()` as `written_norm_mean_applied` alongside the pre-cast value.

### m11. The norm-matching unit test only checks the mean
`tests/test_subspace_donor_patch.py:257-259` asserts
`abs(b["written_norm_mean"] - c["written_norm_mean"]) < 1e-9`, but the class docstring's claim (and
the scientific requirement) is **per-position** matching, which a mean cannot distinguish from a
compensating pair of errors. The implementation *is* per-position exact -- I verified it
independently (`scratchpad/e3.py`):
```
 per-position candidate norms:     [0.13981, 0.05586, 0.034122]
 matched control per-pos norms:    [0.13981, 0.05586, 0.034122]
```
-- so this is a test-strength gap, not a defect. *Fix:* expose the per-position norm vector in
`_dose` and assert elementwise.

### m12. Transductive within-domain centring inside the LOO folds
`dcs_csi_axis.py:85-94`: `X` and `y` are both within-domain centred over the *whole* fit
population before `loo_rho` / `subspace_loo_rho` split it. The held-out domain's rows are therefore
centred using the held-out domain's own feature and **label** means. Strictly, the fold is not
label-clean.

I tested whether it inflates the null (`scratchpad/e4.py`, 30 pure-null draws, 12 domains x 8 rows,
d=200): `mean rho = +0.0361, sd = 0.1596` (SE of the mean ~0.029, so ~1.2 sigma from zero;
uncentred null gives +0.0498). **No measurable inflation.** Reported for completeness because it is
the kind of thing a reviewer will ask about, and the answer should be on record; it is not worth
changing the code for.

---

## NIT

- `donor_patch.py:225-227`: `self.basis` and `self.donor.acts` are `.to(hidden.device)`-ed on
  **every** firing forward. Correct, but it is a host->device float64 copy of `[r, 4096]` per row.
  Cache the device-resident copy keyed on `hidden.device`.
- `donor_patch.py:160-161`: `torch.linalg.matrix_rank(B)` computed twice.
- `donor_patch.py:91-93`: `rid = list(recipient_input_ids)` is materialised before the
  `if not strict_ids: return` early-out.
- `dcs_csi_axis.py:287`: `except SystemExit: break` around `subspace_loo_rho` swallows a `SystemExit`
  that `pls1` raises for "produced no components" -- but it would also swallow one raised for any
  other reason inside the fold. Narrow it to a dedicated exception.

---

## CHECKED AND FOUND CORRECT

Everything below was checked and, where a numeric claim is made, verified by running code. Scratch
scripts are in the scratchpad dir.

**`donor_patch.py`**

1. **Full-rank `SubspaceDonorPatch` reproduces `DonorPatch` EXACTLY** -- the load-bearing
   positive-control requirement. `scratchpad/e2.py`, on a real 3-layer toy model, in both dtypes:
   ```
   torch.float32   full-rank vs DonorPatch  max|diff| = 0.0   (vs base 0.107)
   torch.bfloat16  full-rank vs DonorPatch  max|diff| = 0.0   (vs base 0.129)
   ```
   Bit-identical, not merely close. The reason it survives: `cur` and `don` upcast from bf16/fp32
   to float64 losslessly, `don - cur` is exact for operands with <=24-bit mantissas, `P_I` is
   numerically the identity to 1e-16, and `cur + proj` rounds back to exactly `don`.
2. **Per-position norm matching is exact** (`scratchpad/e3.py`, quoted in m11). The
   non-degenerate branch `proj / proj_norm.clamp_min(1e-12) * target` is a true per-row
   renormalisation, not an average.
3. **The `torch.where` broadcast in the degenerate branch is correct.** `degen` is `[n_pos]`,
   `degen.unsqueeze(1)` is `[n_pos,1]`, `W.sum(0)` is `[hidden]` and `.expand_as(proj)` widens it to
   `[n_pos,hidden]`; the false branch is `[n_pos,hidden]`. Rows are selected independently, as
   intended. (Both branches are eagerly evaluated -- harmless here.)
4. **The degenerate branch fires when it should.** `rel = proj_norm / dn_all` with threshold
   `1e-6` -- the test's orthogonal-to-delta subspace is flagged on 3/3 positions; the realistic
   control (orthogonal to the *candidate*, not to delta) is flagged on 0/3. Both behaviours confirmed
   by running the suite.
5. **The tuple-vs-tensor return is correctly shaped.** Python's conditional expression binds looser
   than `+`, so `return (hidden,) + tuple(output[1:]) if isinstance(output, tuple) else hidden`
   parses as `((hidden,) + tuple(output[1:])) if ... else hidden`, and `output[1:]` is never
   evaluated on the tensor branch.
6. **The in-place mutation is deliberate and consistent.** `hidden[0].index_copy_` mutates the
   tensor the rest of the forward holds; `SubspaceDonorPatch` does exactly what `DonorPatch` does,
   so the two arms mutate identically. Confirmed by (1).
7. **`assert_token_identity` is behaviour-preserving.** It is position-scoped (a token differing
   *outside* the patched span is allowed -- correct, since it cannot misplace a write), it refuses an
   empty `donor.input_ids` under `strict_ids`, and both patchers now call the one copy. The
   `p >= len(rid) or p >= len(donor.input_ids)` bounds are checked before the index.
8. **`orthonormalise` returns the right object.** QR of `B.T` gives an orthonormal basis for
   `colspace(B.T) = rowspace(B)`; `Q.T` is `[r, hidden]`; the `Q @ Q.T == I` self-check passes; the
   row space is preserved (test verified: `rank(cat([M, Q3])) == 3`). 1-D input is promoted to
   `[1, hidden]`. Integer input works (`orthonormalise(torch.tensor([[1,0,0],[0,1,0]]))` ->
   `(2,3)`) because of the `.to(torch.float64)`. `r > hidden` is caught by the rank check. QR sign
   gauge is irrelevant to `W^T W`. (The near-degenerate tolerance is m8.)
9. **Float64 is used throughout the projection and the cast happens once, on write**, exactly as
   the docstring claims. Verified by reading; the precision consequence of the single cast is
   quantified in m10.
10. **`liveness()` / `_dose`.** `_dose` is overwritten per firing forward, but only the prefill
    forward fires (decode steps short-circuit), so the recorded dose is the prefill dose. `n_applied`
    accumulates. `captured_energy_frac_mean` uses the pre-norm-match `proj_norm`, i.e. the arm's own
    genuine captured energy, not the matched value -- correct.

**`score_behavior.py` (new parts only)**

11. **The loader cache is keyed correctly and cannot go stale.** One closure per process over an
    immutable `args`; `state` gains all three keys atomically or the function raises; `B` and `NB`
    come from distinct flags and cannot cross-contaminate.
12. **Missing keys raise, they do not default.** `--rescue-basis-key` is required (no
    "first one in the dict"), and an unknown key or unknown norm-match key raises `SystemExit`
    listing the available names. This is the right behaviour and it is the thing the docstring
    promises.
13. **The two eager guards are correct**: `--rescue-basis` without `--rescue-layer` refuses
    (the whole block is gated on `--rescue-layer`, so it would be inert); `--rescue-norm-match-key`
    without `--rescue-basis` refuses.
14. **The subspace and whole-state arms share everything but the projection.** At `:3617-3625`
    the donor capture, the position resolution (`_rpos`), the layer, the token-identity guard and
    `strict_ids=True` are all upstream of the `if args.rescue_basis:` branch. So the whole-state arm
    is a genuine upper bound for the subspace arm and not a differently-constructed comparison --
    together with finding (1), the recovery-fraction denominator is sound.
15. **`rescue_liveness` reaches the row** (`:3823`), including the dose dict, so a zero-norm or
    never-fired rescue is detectable post hoc.
16. **`--rescue-donor self` ordering.** The donor capture is inside the per-row body *after* `ctxs`
    is built for that row, as its comment says; no previous-iteration `ctxs` leak.

**`dcs_csi_axis.py`**

17. **The ridge dual is the primal ridge solution.** `scratchpad/e1.py`, n=40, d=120, lam=100:
    `max|w_dual - w_primal| = 8.3e-17` against `torch.linalg.solve(X.T@X + lam*I, X.T@y)`, with
    `||w|| = 0.296`. Exact to float64 round-off.
18. **`loo_rho` is leave-one-DOMAIN-out, and the kernel algebra is right.**
    `p = K[te][:,tr] @ alpha = X_te X_tr^T alpha = X_te w_tr`, which is the primal prediction from a
    ridge fit on the training folds only. Folds are formed on `dof` (the domain label), never on the
    row index.
19. **`subspace_loo_rho` fits PLS strictly inside the fold.** `W = pls1(X[ti], y[ti], r)` -- the
    held-out domain contributes to neither the component estimation nor the OLS head, which is fit on
    `Ztr`/`y[ti]`. No leakage.
20. **`pls1` deflation is genuinely deflating, and the components are independent.**
    `scratchpad/e1.py`, r=4:
    ```
    row norms          = [1.0, 1.0, 1.0, 1.0]
    gram off-diagonal  = 5.6e-17          (the W rows are mutually ORTHONORMAL)
    cos(w1, w2)        = 2.8e-17
    rank(W)            = 4
    ```
    "Rank r" is genuinely rank r, not rank 1 repeated -- the specific historical defect this file
    was written against is not present. (Incidentally the W rows *are* orthonormal for PLS1 with this
    deflation, so the downstream `orthonormalise` is a gauge change, not a repair -- but applying it
    is still right, because the projector must not depend on that happening to be true.)
21. **The PLS subspace is scored with the same coordinates the patcher will project onto.**
    `subspace_loo_rho` evaluates `X @ W.T`, and `SubspaceDonorPatch` writes `P_{span(W)}`. The
    selection statistic and the intervention are about the same subspace.
22. **`shuffled_y` preserves the within-domain label multiset and really shuffles.**
    `scratchpad/e1.py`: 200 draws x 8 domains x 5 rows -> multiset identity asserted on every domain
    and every draw; **0/200** identity permutations. Degenerate-by-design check: with 4 domains x 2
    rows, 11/200 draws are the identity vs the expected 200/16 = 12.5 -- i.e. the generator is
    correct, and identity draws only become likely when domains are tiny. It reads from `y` and writes
    to a clone, so there is no in-place aliasing.
23. **`build()` joins on the right key.** Corpus key and installation key are both
    `(domain, family_slot(family_id))`, and `family_slot` drops the `query_kind` field -- which is
    exactly the field that legitimately differs between the behavioural predictor and the semantic
    target. Duplicate keys `raise SystemExit` on both sides (`build()` and `lpm.load_installation`),
    so the silent-channel-substitution path is closed.
24. **Within-domain centring is applied to both X and y, consistently**, in the same loop over the
    same `ks` ordering, so row i of `X` and element i of `y` are the same key. `dof` and `keys` are
    appended in that same order.
25. **The fit population is TRAIN-only.** `fit_doms = corpus_doms & TR`, `TR` excludes
    `EXCLUDED_DOMAINS`, and `build(..., keep=set(fit_doms), ...)` filters rows on `r["domain"] not in
    keep`. Validation and test domains never reach `X`. The corpus-level test-domain refusal at
    `:206-209` is a real check (it reads `assign`, not `fit_doms`). Only the *redundant* guard at
    `:215-217` is vacuous (m1).
26. **Bank/readout pairing is enforced** at `:201-204` (`rsha != csha` -> refuse), which is the
    check that prevents pooling a basket readout with a button corpus.
27. **`ctrl_orth` is genuinely orthogonal** (Gram-Schmidt against `w1`, then a hard refusal at
    `:326-328` if the residual cosine exceeds 1e-9 -- and that refusal *can* fire, unlike m1).
28. **`lpm.spearman` handles ties correctly** (average ranks within tie runs) and returns 0.0 on a
    degenerate constant vector rather than dividing by zero.

**`tests/test_subspace_donor_patch.py`** -- non-vacuous tests, confirmed by reasoning about what a
broken implementation would do:

29. `full-rank subspace reproduces DonorPatch` -- non-vacuous; the companion assertion "both differ
    from the unpatched forward" (`:186`) is what stops it from passing on a no-op patcher. Good.
30. `orthogonal subspace writes nothing` -- non-vacuous. `orth_basis = Vh[len(pos):len(pos)+2]` from
    a `full_matrices=True` SVD of the `[3,16]` delta genuinely spans directions orthogonal to the
    delta's row space, and the assertion pairs an output check with a `written_norm_mean < 1e-8`
    dose check.
31. `linearly dependent rows REFUSED` -- non-vacuous (`[M[0]; 2*M[0]]` is rank 1 of 2).
32. `row space preserved` -- non-vacuous; `rank(cat([M, Q3])) == 3` would fail for any QR bug that
    rotated out of the row space.
33. `rank-1 writes a nonzero but sub-total delta` -- non-vacuous, and the
    `0 < captured_energy_frac <= 1` bound would catch a missing normalisation.
34. The token-identity block -- non-vacuous for both patchers, including the deliberately-allowed
    out-of-span mismatch and the empty-`input_ids` refusal.
35. `unmatched control writes a different norm than the candidate` -- non-vacuous; it is the
    assertion that proves the *matched* assertion is not trivially true.
36. `degenerate control is FLAGGED on every position` -- non-vacuous.

The one vacuous test is M6.
