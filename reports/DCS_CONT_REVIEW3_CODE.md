# DCS-CONT REVIEW-3 — CODE

**Scope.** What has landed since REVIEW-2 (`reports/DCS_CONT_REVIEW2_CODE.md`, adjudicated in
`CONT-ENTRY 066`): `scripts/dcs_cont_f5_confirm.py` as executed for `DR-072`,
`scripts/dcs_cont_f5_probe.py`, `scripts/dcs_cont_lowrank.py`'s `C-CONT-043` deflation fix,
`src/boombness/run_completeness_check.py`'s `C-CONT-051` fix, and the uncommitted §15 cosine
analyses whose results are in `reports/DCS_CONT_S15_*.json` (`CONT-ENTRY 077/078/079/082`).
REVIEW-2's findings are not repeated; where one is unremediated it is named in one line.

**Method.** Read in full; every CONFIRMED claim below was demonstrated by a script I wrote and ran on
CPU. No SLURM job submitted, no GPU used, no frozen config edited, no script modified.

**Discipline note on TEST.** I computed **no TEST quantity**. I did read structural fields of the TEST
corpus — `metadata.json`, `summary.json`, and from `results.jsonl` the `domain` / `split` /
`family_id` / `prompt_id` / row-count fields — which `CONT-ENTRY 062` established is not a
measurement, and which is required to answer the leakage question I was asked. I did **not** load
`cache/multiposition_reps.pt` for the TEST corpus and read no `hnorm|L*` value from it. Two checks
below are marked as *not performed because they would require re-reading TEST*.

---

## Verdict

The single confirmatory read is sound. I could not break it: the two-corpus patch builds the fit side
from `provenance.corpus` filtered to the 90 train+validation domains and the test side from
`--test-corpus` filtered to the 23 test domains, `si/li` and `si_t/li_t` are resolved against their own
corpora (and the two corpora were extracted with byte-identical capture flags, so the site and layer
lists are in fact identical), the fit corpus physically contains **zero** test-domain rows and the test
corpus **zero** fit-domain rows, the two key sets are disjoint, the counts are exactly 900 and 230, the
permutation null is the fixed-predictor within-domain null the frozen document specifies, and
`outputs/dcs_cont/f5_confirmation_TEST.json` is internally consistent with the code on every quantity I
can check without re-reading TEST (`p` is exactly 1/2001, `frac_domains_positive` is exactly 23/23,
every per-domain ρ is a multiple of 1/165 as an untied n=10 Spearman must be, and the mean/median match
`CONT-ENTRY 075`). I also closed **REVIEW-2/H3**, the largest outstanding threat to the read's
interpretability: running the confirmatory script's estimator verbatim with FIT=train and EVAL=validation
reproduces `+0.678431005106532` and comparator `+0.6134737485791216` and 22/23 domains — bit-identical to
`CONT-ENTRY 061`, so the confirmatory implementation is not a second, differing estimator.
The `pls_predict` deflation fix is mathematically correct (verified three ways).
The serious finding is elsewhere and it is in the newest, uncommitted work: **the §15 permutation
p-value is the null of ρ_B, and `CONT-ENTRY 078/079/082` report it as the null of the B − ctx
difference.** I reproduced the knife control exactly and then computed the difference's own null:
knife's headline `+0.0623` has **p = 0.0845**, not `0.00050`, which removes the word *significant* from
`CONT-ENTRY 082`'s central claim. Below that: the §15 "context-only prototype" is, by an exact algebraic
identity I verified to 2e-16, a norm-weighted average of the A and E similarities whose ρ of −0.02 is
**cancellation** of ρ_A = −0.19 against ρ_E = +0.22, so the `+0.4053` headline is 2.5× the comparison
against the best single matched reference; `getsize()==0` is not "zero rows" for a `.jsonl` and I
demonstrate five file shapes that hold zero rows and pass; and the lowrank artifact on disk still holds
the withdrawn pre-fix curve. The prompt's flagged hazard — that `mean(h_A,h_E)` has a smaller norm —
is **not** a hazard here, and I demonstrate why rather than assert it.

---

## CONFIRMED — HIGH

### H1. The §15 `perm_p` is the null of ρ_B, not of the B − ctx difference; `CONT-ENTRY 082`'s "significantly non-zero" does not survive its own null

`reports/DCS_CONT_S15_CROSS_CODEWORD.json`, `..._GUN_CONTROL.json`, `..._KNIFE_CONTROL.json`,
`..._MATCHED_REFERENCE.json` — each stores one `perm_p` adjacent to `diff`.
`CONT-ENTRY 078` (table, column head **`perm p`** next to **`B − ctx`**), `CONT-ENTRY 079` (same
table shape) and `CONT-ENTRY 082` (same, and the sentence *"Knife gives +0.0623 — significantly
non-zero (p at the 2000-permutation floor, so not the gun-style inconclusive null)"*) all read that
number as the difference's p. It is not. `CONT-ENTRY 077` reads the same number correctly, as ρ_B's.

**How I verified it.** I reconstructed the computation from the entries and reproduced it from the
corpora. Reconstruction: cosine similarity at `cw_demo_mean`, references A / B / E and
`ctx = mean(h_A, h_E)`, **both** the similarity and `y_install` centred within domain, pooled Spearman,
then a within-domain label permutation with the similarity held fixed. That convention — and only that
one of the four I tried — reproduces every published number:

| button/bomb, L24 | mine | `DCS_CONT_S15_CROSS_CODEWORD.json` |
|---|---|---|
| ρ_B | +0.382299 | 0.3822992538673916 |
| ρ_E | +0.222519 | 0.22251927059992255 |
| ρ_ctx | −0.022957 | −0.022957197066498437 |
| ρ_A | −0.192341 | −0.192328912340221 |

(L14 and L31 reproduce to 6 dp likewise; ρ_A differs at the 5th decimal because I cast the stored
`bfloat16` to `float64` rather than `float32`. The three alternative centrings — similarity raw,
target raw, neither — reproduce nothing: e.g. L24 ρ_B would be +0.3344, +0.3289, +0.3911. A **dot
product** instead of a cosine would give ρ_B = +0.2074. The published convention is fixed.)

Then, on the knife corpus `s15_behavioral_button_knife_20260911_150342_902441` (train+validation only;
its bank `94fd300d611fccf2` matches readout `ts116m_readout_button_knife_...`), I reproduced the control
exactly and computed **both** nulls, 2000 within-domain permutations each:

| knife/button | ρ_B | ρ_ctx | diff | p(ρ_B) | **p(diff)** | published `perm_p` |
|---|---|---|---|---|---|---|
| L24 | +0.120579 | +0.058317 | **+0.062262** | **0.00050** | **0.08446** | **0.00050** |
| L14 | −0.114695 | −0.002490 | −0.112205 | 0.99950 | 0.99450 | 0.99950 |

The published `perm_p` equals **p(ρ_B)** in both cells, to five decimals, and differs from p(diff).
I then did the same on button/bomb, all three published layers:

| button/bomb | ρ_B | ρ_ctx | diff | p(ρ_B) | **p(diff)** | published `perm_p` |
|---|---|---|---|---|---|---|
| L14 | +0.049071 | −0.072979 | +0.122050 | **0.07546** | **0.00750** | **0.07546** |
| L24 | +0.382299 | −0.022957 | +0.405256 | 0.00050 | 0.00050 | 0.00050 |
| L31 | +0.303315 | −0.024650 | +0.327965 | 0.00050 | 0.00050 | 0.00050 |

Five cells across two banks: the published `perm_p` is **p(ρ_B)** in every one, to five decimals.
Independently, `CONT-ENTRY 077` quotes the null quantiles *"p50 = +0.0015, p95 = +0.0566,
max = +0.1229"*; my ρ_B null on button/bomb L24 gives **p50 = +0.0015, p95 = +0.0567, max = +0.1229**,
while the difference's null on the same data gives **p50 = −0.0000, p95 = +0.0803, max = +0.1681**.
Three independent confirmations that the published p is ρ_B's.

**What number it changes.** `CONT-ENTRY 082`'s knife row: the `B − ctx = +0.0623` effect that the entry
calls *significantly non-zero* has **p = 0.0845** against its own null and is **not** significant at
0.05. That is the entry's load-bearing datum — it is the whole basis for *"it is **not** unique to
`bomb` either — knife's effect is real and significant"* and therefore for narrowing A13 to
**concept-DEPENDENT** rather than bomb-specific. On the correct null the knife control is a second
inconclusive result, not a positive one, and the honest §15 statement becomes *"bomb and basket
replicate; gun and knife are both inconclusive."*

**The error is not uniformly conservative.** `CONT-ENTRY 078` reports `button` L14 as
`B − ctx = +0.1220, perm p = 0.075` and reads it as the null end of the depth profile
(*"nothing at L14"*). Against the difference's own null that cell is **p = 0.0075** — significant, and
an order of magnitude away from what is printed. So the same mislabel turns one significant cell into a
null and one null cell into a significant one. The bomb/button and bomb/basket **L24 and L31**
conclusions are **unaffected**: +0.4053, +0.3317 and +0.3280 exceed even the difference null's maximum
(+0.1681 / +0.1866), and p(diff) is at the 2000-permutation floor there too.

**Fix.** Recompute the null for the statistic actually being reported — `ρ_B − ρ_ctx`, permuting the
labels once per draw and recomputing both correlations, which is what my script does — and store both
p-values under distinguishing keys (`perm_p_rho_B`, `perm_p_diff`). Correct the tables in
`CONT-ENTRY 078/079/082`, and withdraw "significant" from the knife row. `CONT-ENTRY 077` needs no
change; it used the number correctly.

---

## CONFIRMED — MEDIUM

### M1. §15's "context-only prototype" is an average of two oppositely-signed references, and the `+0.4053` headline is inflated by their cancellation

`CONT-ENTRY 077`, §15's decision rule, and `DCS_CONT_S15_MATCHED_REFERENCE.json`
(`difference = 0.40525645093389007`).

**What is wrong.** With `ctx = (h_A + h_E)/2`, cosine similarity obeys the **exact** identity

```
cos(h_C, (h_A+h_E)/2)  ==  ( |h_A|·cos(h_C,h_A) + |h_E|·cos(h_C,h_E) ) / |h_A+h_E|
```

so the prototype similarity is a norm-weighted average of the two constituent similarities — it is not
an independent reference. At button/bomb L24 the two constituents correlate with installation with
**opposite signs**, ρ_A = −0.1923 and ρ_E = +0.2225, so ρ_ctx ≈ 0 is arithmetic cancellation rather
than "the context carries no information". Across all **ten** published cells, ρ_ctx tracks
mean(ρ_A, ρ_E) to within 0.038 (median |deviation| 0.019).

**How I verified it.** The identity, on the real 900 slots at L24: **max absolute error 2.220e-16**,
and the identity-form similarity reproduces ρ_ctx = −0.022957 exactly. The ten-cell table is computed
directly from the committed artifacts.

**What number it changes.** Not ρ_ctx itself — the interpretation of the gap. §15's matched *single*
reference is E (the benign remap: same context, a non-BOMB concept installed), which gives
**B − E = +0.1598** at button L24 and **+0.1703** at basket L24 — against the published
**B − ctx = +0.4053 / +0.3317**, i.e. the headline is **2.5× / 1.95×** the matched single-reference
comparison. At button L14 the reported `+0.1220` collapses to `B − E = +0.0020`.

**Fix.** Report B − E alongside B − ctx wherever the prototype comparison appears, and state that the
prototype's ρ is bounded between its constituents'. Do not drop the prototype — §15 names it — but do
not let a cancellation carry the claim.

### M2. `run_completeness_check.py:321` — `getsize()==0` is not "zero rows" for a `.jsonl`, in the direction that matters

`src/boombness/run_completeness_check.py:317-322`; `CONT-ENTRY 069` states the equivalence outright:
*"Zero rows is exactly a zero-byte file."* The `⇐` direction holds. The `⇒` direction does not, for all
three `ROW_FILE` types (all are `.jsonl`).

**How I verified it.** I pointed the module's `ROOT` at a scratch tree and ran its own `scan()`:

| run | bytes | rows a reader gets (`_rows`) | guard verdict |
|---|---|---|---|
| zero-byte | 0 | 0 | FLAGGED zero-row |
| **lone newline** | 1 | 0 | **PASSES as non-empty** |
| **UTF-8 BOM only** | 3 | 0 | **PASSES** |
| whitespace only | 8 | 0 | **PASSES** |
| **truncated final JSON object** | 41 | 0 | **PASSES** |
| **one bad line then two good rows** | 99 | **0** | **PASSES** |

The last row is the compounding defect: `_rows()` (line 199-203) is
`try: [json.loads(l) for l in open(path)] / except Exception: return []`, so **one** unparseable line
anywhere makes the whole file read as zero rows to every other check in the module. A truncated write
is exactly the disk-quota failure mode (`d38beh`) this module was written for.

**What number it changes.** **None — latent.** I scanned all **1030** DONE run directories under
`outputs/boombness/{score_behavior,extract_boombness,retrieval_strength}`: zero files with nonzero bytes
and zero parseable rows, zero files of 1-16 bytes, and zero files where a bad line poisons the parse.
The guard currently runs green (536 checked / 490 unchecked / 8 allowed).

**Fix.** Replace `getsize(_rp) == 0` with "read lines until the first non-blank one and `json.loads` it;
refuse if there is none or it does not parse". That is O(1) per run — it reads one line, not the file —
so it keeps the 7.9 s budget that motivated the byte check. Separately, make `_rows()` raise (or return
a sentinel) on a parse failure instead of `[]`; today a corrupt file is indistinguishable from an empty
one, and in `file_agreement()` (line 246) it silently becomes NOT COMPARABLE.

### M3. `outputs/dcs_cont/lowrank_train_button_bomb.json` still holds the withdrawn pre-`C-CONT-043` rank curve

The on-disk F6 artifact reports `1: 0.4814, 2: 0.5215, 4: 0.4626, 8: 0.4437` — the rise-then-fall shape
`C-CONT-043` identified as a bug artifact and `CONT-ENTRY 068` formally withdrew. The corrected numbers
live only in `reports/DCS_CONT_F6_DEFLATED_L14.json` / `..._L24.json`, under a different filename, and
nothing in the `outputs/` file says it is superseded. `outputs/` is `.gitignore`d, so the stale artifact
is not caught by any commit-time guard.

**What number it changes.** None published — but it is the artifact whose filename an analyst would
reach for, and it contradicts the record. *Fix:* rewrite it from the deflated run or add a
`SUPERSEDED_BY` key naming the two `DCS_CONT_F6_DEFLATED_*` files (§53: supersede with provenance).

*Related, and worth recording:* the two files are from **different corpora** (`cont3nb_...` vs
`cont1_...`), so `CONT-ENTRY 068`'s *"Rank 1 is untouched by the fix, as expected"* is not actually
demonstrated by comparing them — 0.4814 vs 0.4808 differ by 0.0006. That gap is inside the cross-GPU
drift `C-CONT-052`/`CONT-ENTRY 075` measured (~0.001), so the claim is almost certainly true; it is the
*evidence offered* that does not establish it.

### M4. `dcs_cont_f5_confirm.py:66-71` — the readout bank check added for REVIEW-2/H1 has two silent-pass channels

```python
if os.path.isfile(rmeta_p):                                    # absent metadata.json -> NO CHECK
    rmeta = json.load(open(rmeta_p))
    if rmeta.get("bank_file_sha16") not in (None, pv["bank_file_sha16"]):   # missing field -> PASS
```

REVIEW-2/H1's recommended fix was `lpm.readout_bank_sha()`, which searches `metadata.json`,
`config.json`, `summary.json` and `RUNMETA.json`, falls back to hashing `args.bank`, and **raises** if
it cannot establish the identity at all. The shipped version accepts both "no file" and "field absent"
as agreement. This is the `.get()`-turns-missing-into-legitimate shape that `C-CONT-036` and
`C-CONT-056` both were.

**What number it changes.** **None — latent, and verified so.** The executed run's readout
`ts116m_readout_button_bomb_20260907_133811_3183103` carries `metadata.json:bank_file_sha16 =
dcd92d723f3e6d00`, matching the config and both corpora; `lpm.readout_bank_sha()` returns the same.
*Fix:* call `readout_bank_sha()` and refuse on any outcome other than an exact match; record the value
and its source in the output JSON.

### M5. Four artifacts cited as evidence have no producing code in the repo, and record no provenance

Nothing under `scripts/` or `src/` writes `reports/DCS_CONT_F5_ADJACENCY.json`,
`reports/DCS_CONT_F5_MASS_CONTROLS_L24.json`, or the four `reports/DCS_CONT_S15_*.json`. They were
produced by heredocs. `DCS_CONT_CLAIM_TABLE.md:121` cites two of them as the evidence for live claims,
and `DCS_CONT_F5_MASS_CONTROLS_L24.json` is the control table in `CONT-ENTRY 075` §1 — the evidence on
which the decision to spend the single TEST read was taken. `dcs_cont_f5_probe.py` cannot have produced
it: `CORPUS` is hard-coded at line 28 to the corpus that lacks `cw_demo_prev/next/rand_mean`, and its
own committed artifact `DCS_CONT_F5_RESULTS.json` records those three controls as `null`.

The §15 artifacts additionally record **no corpus path, no bank sha, no readout path (except gun's), no
site, no `n_permutations`, and no seed**. I recovered the button/bomb and knife computations only by
guessing the corpus and the convention; both then reproduced to 6 dp, so they are right — but that was
reconstruction, not reproduction.

**What number it changes.** None retroactively. *Fix:* commit the §15 script and the control script with
`--corpus/--readout/--site/--layer/--n-perm/--seed` arguments, re-emit the artifacts with those fields
plus `bank_file_sha16` and `git rev-parse HEAD`, and add the `readout_bank_sha` refusal every sibling
script has (the knife corpus/readout pair does agree — `94fd300d611fccf2` — but nothing checked it).

---

## CONFIRMED — LOW

### L1. `dcs_cont_lowrank.py:52` — `torch.tensor(C)` silently downcasts the PLS coefficients to float32
`pls_fit` returns `torch.tensor(C)` from a list of Python floats, which infers `float32`. With
`float64` inputs the predictions carry ~1e-7 error (measured: max |diff| 8.9e-8 against the exact
`B = Wᵀ(PWᵀ)⁻¹C` form, and the rank-2 training residual is 5e-8 instead of 5e-17). **Number changed:
none** — `main()` builds `X` and `Y` in `float32` anyway, so the run that produced the published curve
was float32 end to end. *Fix:* `torch.tensor(C, dtype=X.dtype)`.

### L2. `dcs_cont_lowrank.py:132-133` — a failed fold is silently a zero prediction
`if W is None: continue` leaves `pred[i] = 0.0` for every slot of that held-out domain, which then
enters the pooled Spearman as a block of ties rather than as an error. Likewise `pls_fit`'s two early
`break`s can return fewer than `r` components while the result is filed under rank `r`.
**Number changed: none** — with d = 4096 and n = 660 neither triggers. *Fix:* raise, and record the
realised component count per fold.

### L3. `outputs/dcs_cont/f5_confirmation_TEST.json` is not under version control
`.gitignore:11` excludes `outputs/` wholesale, so the one artifact in this phase that can never be
regenerated exists only on disk. *Fix:* copy it into `reports/` (which is tracked) as the canonical
record. REVIEW-2/L3's other complaint is **partly discharged**: the file now carries `config_sha16`,
`fit_corpus` and `test_corpus`, and the config it names is committed at `fce1c8e4`, so the site, layer,
cell, λ, seed and `n_perm` are all recoverable. It still lacks the git commit and a timestamp.

### L4. `CONT-ENTRY 075` §3 presents a console block the script does not print
The script prints `comparator (unregularised)` and `per-domain rho: mean ... median ... positive in ...`;
the entry's fenced block reads `comparator (ridge at inf)` and `per-domain: mean ... median ...`. The
numbers are right (I checked `mean +0.6401 / median +0.7212` against the JSON's 23 values) and the
relabel is the `C-CONT-046` correction being applied — but a fenced block that reads as a transcript
should be a transcript. *Fix:* quote verbatim and annotate outside the fence.

### L5. `dcs_cont_f5_probe.py:46` — a guard that cannot fire
`if any(assign[d] == "test" for d in TR | VA)` is checked against sets built two lines earlier by the
predicates `v == "train"` and `v == "validation"`. It is a tautology. The *real* guard is line 50,
which tests the corpus rows and is correct. *Fix:* delete the tautology so it is not mistaken for
coverage.

### L6. `dcs_cont_f5_confirm.py:102` — the whole multi-position stack is retained per row
`byk[...] = t.float()` stores the full `[20, 19, 4096]` tensor for each of 3720 + 920 rows before
indexing `[si, li]`, i.e. ~29 GB of float32 on top of the ~15 GB of loaded `.pt`. It fit on a 125 GB
node. On the one run that cannot be repeated, an OOM here would have burned the read.
*Fix:* `t[si, li].float()`.

**Unremediated from REVIEW-2, restated in one line each:** M4 (a missing representation is silently
dropped in `f5_confirm`/`lowrank`/`trajectory`/`nb1_control` where `layerpos_map` refuses) — still open,
and `f5_confirm` still has no `len(yf)==900 / len(yt)==230` assertion above the first test-row access;
M1 (`within_domain_map`'s per-cell fresh permutations); M2/M3 (`dcs_succ_concept_presence.py`).

---

## Checked and found CORRECT — recorded so they are not re-reviewed

**`dcs_cont_f5_confirm.py`, the executed path.**
* **The fit side and the test side are built from the corpora they claim.** `build(FIT)` closes over
  `rows`/`mp` from `provenance.corpus`; `build(TST, rows_t, mp_t, si_t, li_t)` passes the
  `--test-corpus` objects positionally into `_rows/_mp/_si/_li`. The `_x is None` defaults are `is`
  tests, not truthiness tests, so an index of 0 would not fall back — I checked, because `si` can
  legitimately be 0.
* **Site and layer indices are resolved per corpus, correctly**, and the "NOTE: indices differ" branch
  at line 86-88 is a diagnostic, not a fallback. In fact they cannot differ: both corpora were
  extracted with identical `--layers`, `--position`, `--capture-rel-end=-16..-1` and
  `--capture-codeword-occ` (verified from both `metadata.json:argv`), giving the same 20 sites and 19
  layers. I confirmed the site list is `[rel-16 … rel-1, cw_query, cw_demo_last, cw_demo_first,
  cw_demo_mean]` by loading the fit corpus.
* **No TRAIN or VALIDATION row could enter the test set, and no TEST row the fit set.** Measured
  against the frozen split manifest: the fit corpus holds 93 domains, **70 train + 23 validation,
  0 test**; the TEST corpus holds **23 test, 0 fit**. `FIT ∩ TST = ∅`; the two `(domain, family_slot)`
  key sets are disjoint (900 and 230, overlap 0); `EXCLUDED_DOMAINS` are all `train`, so FIT = 90 and
  TST = 23 exactly as `DR-072` states. Both filters are explicit, so even a mis-split corpus could not
  cross-contaminate. The `results.jsonl` `split` field is `dev`/`heldout` (the bank block) and is never
  used for the population — correct, though the name collision is a trap.
* **The permutation null is the documented one.** Labels permuted **within domain** on TEST
  (`torch.randperm` per domain), the predictor `pred` computed once and held fixed, 2000 draws,
  `torch.Generator().manual_seed(20260911)` from the config — no unseeded randomness. `p = (k+1)/(n+1)`.
* **The output JSON is internally consistent with what the code computes**, on everything checkable
  without re-reading TEST: `p = 0.0004997501249375312` is exactly 1/2001 (so `k = 0`);
  `frac_domains_positive = 1.0` equals `sum(v>0)/23` over the stored 23 values; all 23 per-domain ρ are
  exact multiples of 1/165, which is what an untied Spearman on n = 10 must be, and there are exactly
  23 of them for `n_test_domains = 23`; `n_fit_domains/slots = 90/900` and `n_test = 23/230` match the
  corpora's actual row counts (3720 = 930×4 and 920 = 230×4); `mean = +0.6401`, `median = +0.7212` match
  `CONT-ENTRY 075`; the verdict follows from the three stored criteria; `f5_beats_comparator` follows
  from `0.6054 > 0.5475`. **Not performed:** recomputing `rho_test` itself, which would require loading
  the TEST representations — I am flagging that rather than doing it.
* **REVIEW-2/H3 is closed.** I re-ran `f5_confirm`'s `build()` and estimator **verbatim** with
  FIT = train, EVAL = validation on the fit corpus (no TEST touched): `rho = 0.678431005106532`,
  comparator `0.613473748579122`, positive in **22/23** domains — identical to `CONT-ENTRY 061` and to
  `reports/DCS_CONT_F5_RESULTS.json` to the last digit. The confirmatory script is therefore *the same
  estimator* as the selection, and a low `rho_test` could not have been an implementation discrepancy.
* **REVIEW-2/H2 is closed.** The sha pin works: `sha256(configs/dcs_cont_dr072_f5_confirmation.json)[:16]
  == 35a5ed952756e88a == DR072_SHA16`, and the config has exactly one commit (`fce1c8e4`).
* **The executed code is the committed code.** `git status` clean and `git diff HEAD` empty for the
  script; its last commit `df4049a1` (16:30) already contains `--test-corpus` and the sha pin, and the
  output file was written at 19:42. Ordering holds: freeze `fce1c8e4` 15:05 → TEST extraction commit
  `a9109dea` 16:06 (freeze is an ancestor) → fix `df4049a1` 16:30 → read 19:42.
* **The fit and TEST corpora are commensurable.** Identical `model`, `model_revision_resolved_commit`
  (`0e9e39f2…`), `dtype` (bfloat16), `attn_implementation`, `layers`, `hidden_size`, `bank_file_sha16`,
  `bank_rows_sha16`, `bank_path`, `tokenizer_files_sha16`, `transformers`, `torch`, `python`. They differ
  only in GPU (RTX 3090 vs L40S) and host — the drift `CONT-ENTRY 075` §2 bounded at ~0.001 ρ.
* `load_corpus`'s `query_kind == {"behavioral"}` and `n_examples == {4}` refusals apply to the TEST
  corpus too; `load_installation`'s `semantic_one_word` + cell-C filter and duplicate-key refusal apply
  to both sides, and the readout's 1392 keys cover all 900 fit and 230 test keys with none missing.

**`dcs_cont_lowrank.py` — the `C-CONT-043` deflation fix is mathematically correct.** Verified three
independent ways on random data (5 seeds × ranks 1,2,3,5):
1. against the closed-form regression coefficient `B = Wᵀ(P Wᵀ)⁻¹C` — max |diff| **1.7e-15**;
2. against `sklearn.cross_decomposition.PLSRegression(n_components=r, scale=False)` — correlation
   1.000000000000, max |diff| 2.5e-7 (the float32 `C` of L1);
3. a hand-derived 2-component case: manual NIPALS deflation of new data reproduces `pls_predict`, and
   `pls_predict` on the *training* matrix reproduces `pls_fit`'s own deflated residual `yd` — the
   regression test REVIEW-2 asked for, which fails on the old body at r ≥ 2 and passes now.
Rank 1 is exact in both bodies, as claimed. The LOO structure is clean: `pls_fit` is refit inside each
fold on `X[tr]` only, and within-domain centring uses only that domain's own rows.

**`dcs_cont_f5_probe.py`.** Reproduces `CONT-ENTRY 059`/`061` to the digit
(`train_rho_loo = 0.6241297239584491`, λ-ladder monotone, `validation_rho = 0.678431005106532`,
comparator `0.6134737485791216`, `train_perm_p = 0.004975…`), and its `build`/estimator are
character-identical to `f5_confirm`'s. The `loo()` kernel subsetting `K[ti][:,ti]` / `K[ei][:,ti]` is
correct, the null **refits** under permuted labels (the `C-CONT-002` requirement), the generator is
seeded, and it correctly refuses a corpus containing test rows (line 50). It also correctly records the
three uncaptured control sites as `null` rather than inventing them.

**§15, the parts that are right.**
* **Within-domain centring is applied to BOTH the similarity and the target** — confirmed by
  reproduction, since none of the three other conventions reproduces any published number.
* **The permutation preserves domain structure** — my within-domain shuffle reproduces the published
  `perm_p` to five decimals in five separate cells across two banks and reproduces `CONT-ENTRY 077`'s quoted null
  quantiles (+0.0015 / +0.0567 / +0.1229 against +0.0015 / +0.0566 / +0.1229). The statistic it is
  attached to is the problem (H1), not the resampling scheme.
* **The domain-level bootstrap is right.** 4000 resamples of domains gives CI
  **[+0.2935, +0.5122]** against the published **[+0.2943, +0.5101]** — agreement to the resampling
  noise of an unrecorded seed.
* **The flagged norm hazard is NOT a hazard.** Cosine similarity is invariant to the scale of either
  argument, so the smaller norm of `mean(h_A, h_E)` divides out exactly; the comparison of
  `cos(h_C, mean)` against `cos(h_C, h_B)` is not biased by it. Measured: replacing the raw mean with a
  **unit-normalised** mean `(h_A/|h_A| + h_E/|h_E|)/2` moves ρ_ctx from −0.0230 to −0.0266 at L24
  (and −0.0730 → −0.0699 at L14, −0.0246 → −0.0264 at L31) — an effect of ~0.004 against a claimed gap
  of 0.4053. Had the analysis used a **dot product**, the norm would have mattered a great deal
  (ρ_B would be +0.2074, not +0.3823) — it did not. The real hazard in this construction is M1.

**`run_completeness_check.py`, the parts that are right.** `KNOWN_ZERO` is **not** doing more work than
documented: it is applied at one place (`main():362`) and only to the `zero_row` list, so it cannot
suppress a short run, a ledger disagreement, a cell imbalance, a missing config or a file-agreement
defect — those flow through `problems`/`KNOWN_SHORT` independently. All **8** `KNOWN_ZERO` ids and all
**11** `KNOWN_SHORT` ids resolve to real DONE directories (no stale allowlist entries), and
`tests/test_run_completeness_check.py:340` enforces that each carries a cause. The `unchecked` branch's
comment about `is_a_run` is right — reaching it means `config.json` parsed. The guard runs green in
~8 s over 1030 DONE runs: 536 checked against a target, 490 non-empty-only, 8 allowed zeros, 4 non-runs,
605 comparable for file agreement.

**Hunt categories with no new findings.** No **index/offset** error: every site and layer lookup in the
new code is `index(name)` / `index(int(layer))`, resolved per corpus, and I verified the two corpora
agree. No **leakage**: demonstrated above at the row, domain and key level in both directions, and F6's
LOO refits inside the fold. No **unseeded randomness** in committed code (`torch.Generator().manual_seed`
in `f5_confirm` and `f5_probe`; `lowrank` and `run_completeness_check` use none) — the §15 heredocs'
seeds are simply unrecorded, which is M5, not unseededness. No **mutable default argument**, no bare
`except` in the new scripts (the one bare `except` in scope is `_rows`, M2). The `.get()`-makes-missing-
legitimate channel appears twice: `f5_confirm:69` (M4) and `run_completeness_check._rows` (M2).
