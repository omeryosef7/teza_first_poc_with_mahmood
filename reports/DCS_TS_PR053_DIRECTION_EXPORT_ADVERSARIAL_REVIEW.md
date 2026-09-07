# Adversarial review — `scripts/dcs_ts_export_directions.py` and `outputs/dcs_ts/directions_pr053/`

**Reviewer brief:** refute, do not confirm. **Date:** 2026-09-07. **Mode:** CPU only, no GPU, no
SLURM, no network. **Nothing was committed, staged or stashed; no existing file was edited.**
Scratch work in
`/tmp/claude-47249/.../9bd0f572-fe9b-4812-a92e-64b0c69878e2/scratchpad/` (`indep.py`, `dose.py`,
`h2b.py`, `rerun/`, `fresh/`).

**Target under review**

| | |
|---|---|
| producer | `scripts/dcs_ts_export_directions.py` (866 lines) |
| artifact | `outputs/dcs_ts/directions_pr053/{directions_fit_dev.pt, MANIFEST.json, VERIFY.json, MUTATIONS.json}` |
| narrative | `reports/DCS_TS_PHASE9_BLOCKERS_CLEARED.md` §12 |
| consumer | `src/boombness/score_behavior.py`, `doublespeak_causality/pair_common.py` |

> **Shared-tree note.** This is a shared working tree with a concurrent writer. At the start of the
> review `src/boombness/score_behavior.py` was modified-uncommitted; partway through it was committed
> as `e9dae21c` and `doublespeak_causality/pair_common.py` became the modified file. **I re-checked
> every `score_behavior.py` / `pair_common.py` line number cited below against the tree as of
> `e9dae21c` and they all still resolve to the quoted code.** I edited, staged, committed and
> stashed nothing; my only write to the repo is this file.

**Headline: the artifact survives every attack line aimed at it.** Four of the six attack lines
return *no finding*, and I say so explicitly rather than manufacturing one. The material findings
that remain are **not defects in the export** — they are (a) one real hole in what the verification
harness is *able* to catch, and (b) two scoping problems that belong to `PR-053`'s definition of
`v_bomb_specific` and to how a PHASE 9 result may be worded. Both of (b) would change PHASE 9's
*conclusion wording*, not its *validity*.

---

## 0. What I ran, and what I observed

All four numbers below are **mine**, from my own invocations, not transcribed from the agent's logs.
`--verify` and `--mutate` were pointed at a **scratch** `--out` holding a byte-copy of the shipped
`directions_fit_dev.pt`, so the shipped `VERIFY.json` / `MUTATIONS.json` were never overwritten.

| command | observed |
|---|---|
| `--selftest` | **16/16 PASS** (plus a benign `numpy` `ddof<=1` RuntimeWarning from the 1-domain toy AUROC fixture) |
| `--verify --out <scratch copy of the shipped .pt>` | verdict **GREEN**, **26/26 checks GREEN**, rc=0 |
| `--mutate --out <scratch>` | **20/20 turned at least one check RED**, rc=0, **`raised: null` on every case** |
| `--export --out <fresh dir>` | wrote a new payload whose **content sha256 is bit-identical** to the shipped one |

Reproduction figures I observed on my `--verify`:

```
band-mean identity AUROC   0.976401      (published R-111: 0.9764)
95% CI over domains        [0.962219, 0.990583]   (published [0.9622, 0.9906])
between-domain SD          0.034703      (published 0.0347)
domains above chance       23/23
per-layer L6..L14   0.9639 0.9687 0.9735 0.9746 0.9793 0.9809 0.9824 0.9830 0.9813
Cohen's d           min 2.806  max 3.148
split               train 67 / validation 23 / test 23
excluded            restaurant_kitchen, school_campus, subway_station
runs                ts116m_full_button_{bomb,knife,gun}_20260907_*
```

**Determinism / tamper check the agent did not perform.** I re-ran `--export` into a fresh
directory and compared:

```
shipped content_sha: 8df3fdec93c4c7b73cf38178612cc365608ab9a9f04351b1dadf0fadbe56a435
fresh   content_sha: 8df3fdec93c4c7b73cf38178612cc365608ab9a9f04351b1dadf0fadbe56a435   MATCH
shipped payload_sha: 0d59b255...   fresh payload_sha: d7b4611a...   (differ only via meta.written_utc)
fit_domains identical: True (67)
```

The shipped `.pt` **is** what today's code produces from today's caches. It was not hand-edited.

---

## 1. LEAKAGE — **NO FINDING** (one harness gap recorded separately as F-1)

**The claim under attack:** no test or validation row influences any exported vector, by *any*
route — scaler, mean, norm, shared quantile, or an all-rows domain list. The agent's evidence is an
assertion on a metadata field (`meta.fit_domains`), which is exactly the "check reads the producer's
own field" family. I did not accept it.

### 1a. Code-path audit of the arithmetic that actually computes the means

- `scripts/dcs_ts_export_directions.py:182-187` — `fit_directions` builds `tr` from the caller's
  `fit_domains` and forms `v[c] = np.stack([Dm[c][d] for d in tr]).mean(axis=0)`. The only rows
  reachable are `Dm[c][d]` for `d in tr`. There is no centring, scaling, whitening, quantile or
  norm computed over any wider set.
- `scripts/dcs_ts_pr053_diffmeans.py:309-392` (`build_arm`, imported not reimplemented) — `Dmean` is
  accumulated **per domain** (`acc[dom] += (xc - xa)`, `out["Dmean"][(c,dose)][d] = acc[d]/cnt[d]`).
  No cross-domain pooled statistic exists in the returned structure. `keep_domains` widens only
  `out["rows"]`, which the estimator never reads.
- `scripts/dcs_ts_export_directions.py:447-470` — the `cell_means` / `concept_cell_means_train`
  diagnostic blocks iterate `for d in tr`, i.e. TRAIN only. I confirmed `n_per_cell == {A: 670, C: 670}`;
  67 train domains × 10 rows/domain = 670. Exact, no test rows.
- `unit()` (`dcs_diffmeans_directions.py:310`) is a **per-layer, per-vector** L2 normalisation — no
  shared norm across rows or domains. `_zconst`, the one place in `pr053_diffmeans` that computes
  shared centre/scale constants, is **never called** from the export path.

### 1b. Independent recomputation — the decisive test

I wrote `indep.py`, which does **not** import `fit_directions` or `build_payload`. It opens the
three extraction caches and the three banks directly, re-does the `family_id` pairing itself,
averages over the 67 TRAIN domains, forms `v_bomb - 0.5*(v_knife + v_gun)`, and compares to the
shipped payload arrays:

```
max|cos - 1| between my train-only fit and the shipped v_bomb_specific : 1.34e-09
max|unit diff|                                                          : 4.94e-09
gap[] vs my raw ||v||, max relative error                               : 0.0 (exact)
v_bomb / v_knife / v_gun / v_knife_specific, max|unit diff|             : 5.2e-09 / 4.4e-09 / 7.2e-09 / 6.2e-09
```

`5e-09` is the float32 storage precision of the payload. **The shipped vectors are the TRAIN-only
estimate and nothing else.**

I also built the counterfactual to prove the comparison has resolution — that a leak *would* have
been visible in the arrays:

```
cos(train-only, train+test fit) per layer : 0.99935 ... 0.99855   (max|unit diff| 1.12e-02)
cos(train-only, validation fit)  per layer : 0.99304 ... 0.98751
```

A leaked fit differs from the shipped one by ~1.1e-02, **six orders of magnitude** above the 5e-09
agreement I measured. The test is not saturated.

**Verdict: NO FINDING on leakage. Severity NON-ISSUE. Does not change a PHASE 9 conclusion.**

### F-1 (SERIOUS, harness gap — not a defect in this artifact)

**`scripts/dcs_ts_export_directions.py:283` and `:591-597`.** Every check that enforces TRAIN-only
reads `meta.fit_domains` — a field the producer writes about itself. Nothing recomputes the vectors
from the TRAIN rows (which `ctx["arm"]["Dmean"]` holds in memory at check time) and compares them to
the payload arrays.

Consequence, and I confirmed it from the mutation red-lists in my own `MUTATIONS.json`: mutations 1-3
are caught **only** by `fit domain set == the frozen manifest's TRAIN split, exactly` / `... is
DISJOINT from test` / `... count matches split.n_train` — all three of which read `meta.fit_domains`.
The dangerous mutation is therefore **absent from the set of 20**: *arrays fitted on TRAIN+TEST while
`meta.fit_domains` honestly records the 67 train domains.* That payload passes **all 26 checks**.
Mutation 4 covers the harmless converse (honest arrays, lying metadata).

This is precisely the `feedback_check_reads_same_broken_source` pattern. It did not bite here — §1b
rules it out by direct recomputation — but the artifact's *self-verification* cannot rule it out, and
§12.2 of the report overstates when it says "the domain-set checks above are what proves it". They
prove the producer's *claim* about its population, not its arithmetic.

**Would it change a PHASE 9 conclusion?** No, because I closed it externally. **Recommended fix (do
not apply now):** one added check — recompute `v_c` from `ctx["arm"]["Dmean"]` over `ctx["train"]`
and `np.allclose` against `payload[name] * gap[name]` — plus one mutation that leaks the arrays while
telling the truth in metadata.

---

## 2. CIRCULARITY IN THE REPRODUCTION — **NO FINDING**

This was flagged as the single most likely way the artifact is quietly wrong. I spent the most
effort here. It is clean, on three independent grounds.

**(a) The target pre-exists the artifact and is not derived from it.** `R111`
(`scripts/dcs_ts_export_directions.py:107-120`) is transcribed from
`reports/DCS_TS_PR053_DIFFMEANS.md`. I checked that file's git provenance:

```
$ git log --oneline -1 -- reports/DCS_TS_PR053_DIFFMEANS.md
504a3cc9 DCS-R-111: PHASE 6 result -- CLAIM B is UNSUPPORTED, caught by a preregistered check
```

— committed long before this artifact (HEAD is `2a478209`). All eight constants are literally in
that file: `:141` band-mean **0.9764**, `:142` CI **[0.9622, 0.9906]**, `:143` SD **0.0347**,
`:180` the nine per-layer values, `:186` Cohen's d **2.81 → 3.15**, `:204` 23/23. Nothing here was
back-fitted to the run.

**(b) `--verify` scores the vector loaded FROM DISK, not an in-process one.**
`scripts/dcs_ts_export_directions.py:832-838`: `payload = torch.load(path, ...)` then
`uspec = np.stack([payload["v_bomb_specific"][int(L)]... for L in payload["layers"]])`, and
`check_payload` runs on that loaded object. There is no shared state between the loaded vector and
the arrays `build_payload` produced — the process re-reads the bytes. (`--export`'s *pre-write*
reproduction does score the in-memory object, but that arm is a refusal gate, not the published
evidence; the published evidence is `VERIFY.json`.)

**(c) I reproduced it end-to-end with an independent implementation.** In `indep.py` §A3 I score
the shipped payload against the raw caches using **`sklearn.metrics.roc_auc_score`**, my own
`np.einsum` projection and my own domain loop — sharing no code with `auroc`/`project`/`band`:

```
n_domains 23
per-layer mean : 0.9639 0.9687 0.9735 0.9746 0.9793 0.9809 0.9824 0.9830 0.9813
band-mean AUROC: 0.976401
sd 0.034703   CI [0.962219, 0.990583]   above-chance 23/23
```

Identical to six decimals, on every layer, against a completely separate AUROC implementation.

**(d) Resolution check.** The leaky fit scores **0.978019** on the same rows — 1.6e-03 away, which
`DP=4` rounding rejects. So the reproduction check can tell the two apart; it is not a test that
passes for any plausible vector. (Mutations 16-18 already show the AUROC checks reject the
sign-flip, `v_bomb` at 0.8856, and `v_knife_specific`.)

**Verdict: NO FINDING. Severity NON-ISSUE. The 0.9764 reproduction is informative, not guaranteed.**

---

## 3. THE MUTATION HARNESS — **NO FINDING on the three specific attacks; one structural caveat**

I re-ran `--mutate` and read the resulting `MUTATIONS.json` case by case.

- **"Applied to a copy no check reads?"** No. `case()` (`:567-586`) round-trips every mutated payload
  through `torch.save`/`torch.load` (`_rt`, `:557-565`) and then runs `check_payload` — the same
  function `--verify` runs on the shipped file. The base object is a freshly built payload rather
  than the shipped bytes, which I initially treated as a gap; my `--export` determinism test (§0)
  shows the two are **content-identical** (`content_sha256` matches bit for bit), so the distinction
  is immaterial.
- **"RED produced by an unrelated exception?"** No. **`raised` is `null` on all 20 cases** in my run.
  Nothing was caught by a `KeyError` or a shape error standing in for a real guard.
- **"Are the checks the ones that gate the export?"** Yes — `main()` (`:806-818`) runs
  `check_payload` + `check_reproduction` before `write_artifact` and returns 2 without writing if
  any is RED. The mutation harness calls the same two functions.

I verified the *reason* each mutation went red, not just that it did. Every one is caught by the
check designed for it, e.g. zeroed layer → `no direction is degenerate` + `every stored vector is
UNIT` + the algebra check; layer rotation → the algebra check + all five reproduction checks;
`v_remap` repointed → `v_remap == v_bomb`. **20/20 for the right reason.**

**Structural caveat (MINOR, not a finding against the claim).** Mutations 5, 6, 8, 9, 10, 11 are all
partly caught by `content sha256 of the arrays matches the recorded one`. That check can *never* fail
on a genuine export, because `meta.content_sha256` is computed from the same arrays it is later
compared against (`:419-540` writes it, `:347-351` re-derives it). It is a **tamper detector, not a
correctness check** — which is appropriate, since those mutations *are* tamper mutations, and each of
them is independently caught by a real algebra or norm check as well. Worth stating so the "20/20"
is not read as 20 independent correctness guarantees.

**Would it change a PHASE 9 conclusion?** No.

---

## 4. THE CONSUMER CONTRACT — **NO FINDING on the layer convention; three MINOR findings**

I read the consumer myself rather than trusting §12.1.

### 4a. Layer convention — **NO FINDING, and the off-by-one is positively excluded**

The brief's worry (`block L == hidden_states[L+1]`) is the one place an invisible fatal error could
hide. Both sides agree, and I traced both:

- **Read side.** `configs/dcs_ts_pr053.json` `read_site.layer_convention` = `"block L ==
  hidden_states[L+1]; hidden_states[0] == embeddings"`, and `build_arm`
  (`scripts/dcs_ts_pr053_diffmeans.py:331-346`) **refuses** if the extraction cache's own
  `layers`/`position`/`layer_convention` disagree — normalised comparison, so `block_L` vs `block L`
  is not a false alarm. My `--verify` run printed no refusal, so the cache declares that convention.
- **Write side.** `doublespeak_causality/pair_common.py:1311-1326`, `make_project_out_hook`:
  *"The hook is registered on the decoder-LAYER output (`register_forward_hook`), so `direction`
  lives in the post-block-L residual == hidden_states[L+1]."* `AllPositionProjectOut.__enter__`
  (`:1384-1386`) does `self.layer.register_forward_hook(...)` on `_resolve_layer(model, layer_idx)`.

**The two conventions are the same one. No off-by-one.**

### 4b. Keys, dtypes, device — **NO FINDING**

- `src/boombness/score_behavior.py:2081-2085` joins `--fit-dir` with `directions_fit_dev.pt` first.
  The file is named exactly that.
- `:1396-1401` — `dmap = payload[name]`; `gaps = payload["gap"][name]`. Payload carries
  `v_bomb`, `v_bomb_specific`, `v_gun`, `v_knife`, `v_knife_specific`, `v_remap` at top level and the
  matching `gap` sub-dicts (verified by loading the file).
- `:1432` — `for L in band: d = dmap.get(L)`. `band` comes from
  `list(range(lo, hi+1))` (`:2044`), i.e. **Python `int`s**; payload keys are `int(L)` (`:463`).
  Types match — this would have been a silent-null if one side were `str` or `np.int64`.
- Device/dtype independence: the hook does `d_cpu.to(device=h.device, dtype=h.dtype)` per call
  (`pair_common.py:1336`) and **re-normalises its own copy** (`:1325-1326`), so a `float32` CPU tensor
  against a `bfloat16` CUDA model is fine, and even a non-unit vector would be safe for `project_out`.
- `mode=add` refuses on an empty `gap` (`:1447-1451`) and dosing is `alpha * g` (`:1453`) —
  **unit vectors + gap-unit dosing is exactly what this call site expects**, and the payload matches.
- `cell_means` has ≥2 cells (`A`, `C`), which is the minimum `cellmean_dose`
  (`insubspace_null_test.py:344-348`) and `cell_residual_frac_removed`
  (`score_behavior.py:201-232`) need. PHASE 9's population is `cell: "C"`, and `cell_means["C"]`
  exists, so the dose record will bind rather than silently going `UNAVAILABLE`.

### F-2 (MINOR) — no guard that the requested band is covered by the payload

`src/boombness/score_behavior.py:1431-1434`: `d = dmap.get(L); if d is None: continue`. The only
guard is `if not ctxs: raise` (`:1455`) — the **all**-missing case. The payload covers **L6-14 only**,
on a **32-block** model. A band such as `0-31` would register 9 hooks, not 32, **silently**, while
`:2042` echoes `"band 0-31 -> blocks 0..31 of 32"` — the echo reports the *request*, not the
*realisation*. `arm_echo["n_hooks"]` (`:1483`) records the truth post hoc, so it is recoverable, but
nothing refuses.

PHASE 9's declared scopes are S1 = block 9 and S2 = L7-14, both inside L6-14, so **this is a latent
hazard, not an active defect**. It is the same shape as the "silently weaker knockout" bug the file's
own comment at `:2031-2035` was written to prevent — the band bounds are checked against the *model*
but never against the *payload*. **Would not change a PHASE 9 conclusion as currently scoped.**

### F-3 (MINOR) — `H2b`'s dose constant is not `gap`, and must not be wired as `alpha=1`

`configs/dcs_ts_pr057_phase9.json` H2b specifies `c_knife` = the TRAIN-mean component of `C_knife`
states along `v_knife_specific`. `score_behavior`'s `add` path doses in **gap units**
(`:1447-1453`). Those are not the same number, and the ratio is **layer-dependent**, so no single
`alpha` reproduces it (`h2b.py`):

```
L      gap[v_knife_specific]   c_knife = m_Cknife . u_kspec   ratio
L6         0.803                    0.376                     0.47
L8         1.241                    1.341                     1.08
L12        1.545                    0.649                     0.42
L14        1.937                    1.331                     0.69
```

The export **anticipated this correctly**: `payload["concept_cell_means_train"][c][L]` is present, and
`c_knife` is exactly `m_knife · û_knife_specific` from it — I computed the column above from the
payload alone. And `scripts/dcs_ts_pr057_causal.py:2432-2434` already marks `component_replace` as
*"NEW MODE, does not exist yet"*, with a dedicated hook
(`make_instrumented_component_replace_hook`, `:421-470`) that takes `c_in` as an explicit float.

So this is **not a gap in the artifact** — it is a note for whoever writes that mode: the plan's
`alpha=1.0` (`:1153`) is a placeholder for a **per-layer** constant, and dosing it in gap units would
inject 0.9×-2.4× the specified magnitude, layer-dependently. The §12.1 claim that "the payload
carries exactly those keys" is true for the modes that exist; it should not be read as "H2b is
runnable".

### F-4 (MINOR) — the realised-dose block is rank-1, and §12.1 misstates its range

With only two cells (`A`, `C`), the centred cell-mean matrix has **rank 1** — I measured
`np.linalg.matrix_rank == 1` at L9. §12.1 discloses this honestly and notes `cellmean_dose` returns
1.0000 for `v_remap` *by construction*. But its stated range for `v_bomb_specific`, "0.14-0.17", is
**wrong at the bottom of the band**. My measurement across all nine layers:

```
L      cellmean_dose   cell_residual_frac_removed[C]   [A]
L6        0.0467              0.1220                 0.0804
L7        0.0468              0.1003                 0.0578
L8        0.1466              0.0396                 0.0553
L9        0.1656              0.0936                 0.0073
L10       0.1370              0.1412                 0.0496
L11       0.1594              0.1681                 0.0646
L12       0.1421              0.2058                 0.1060
L13       0.1899              0.2106                 0.0872
L14       0.1817              0.1729                 0.0513
```

The true range is **0.047-0.190**, not 0.14-0.17; L6 and L7 are a factor of ~3 below the quoted
floor. The `cell_residual_frac_removed` values §12.1 quotes (C 0.094 at L9, 0.206 at L12) match mine
(0.0936, 0.2058) exactly. **Severity MINOR — a mis-stated range in prose, with the underlying
artifact correct.** It does become load-bearing via F-5 below.

Also cosmetic, **NON-ISSUE**: `score_behavior.py:1397-1399`'s "not in the fitted payload" error
enumerates `k for k in payload if k.startswith('d_')`, which is empty for a `v_`-named payload — the
refusal message would list nothing. The `CONTROL_ARMS` branch at `:1325` already uses
`startswith(('d_','v_'))`. A person reading a failure would be briefly misled; nothing is wrong.

---

## 5. SIGN AND ORIENTATION — **NO FINDING**

`v_bomb_specific` is oriented so that **bomb is the positive end**. From `indep.py` §A5, mean
projection of cell-C states on the shipped unit vector, pooled over the 23 test domains:

```
L        L6     L7     L8     L9    L10    L11    L12    L13    L14
C_bomb  +0.619 +0.550 +0.236 +0.599 +1.027 +1.305 +1.578 +1.776 +1.562
negatives -0.354 -0.547 -1.244 -0.995 -0.834 -0.615 -0.275 -0.383 -0.796
```

Positive for bomb at **every** layer, negative for `{C_knife, C_gun}` at every layer.

Three further points:
1. `project_out` (`pair_common.py:1337-1338`, `h - alpha*(h·d)d`) is **quadratic in `d`** and
   therefore sign-free. A flip could not affect H2a at all.
2. The sign *is* pinned anyway by the verification: mutation 16 (`-uspec`) turns five reproduction
   checks RED, and my `--selftest` confirms `score_identity_auroc` returns 0.0 for a flipped
   separating direction. An export that flipped the sign could not have been written.
3. `mode=add` **is** sign-dependent, and the orientation above is the one a reader assumes: `+alpha`
   pushes toward bomb. `v_knife_specific` is oriented symmetrically (knife positive), which is what
   H2b's `+ c_knife * v_knife_specific` requires.

**Severity NON-ISSUE.**

---

## 6. THE R-116 CAVEAT — **SERIOUS**, and the warning is not quite adequate

I assessed this independently rather than accepting the agent's framing. The `interpretation_warning`
embedded in the payload (`scripts/dcs_ts_export_directions.py:525-533`) quotes R-116 accurately —
I checked against `reports/DCS_TS_CLAIM_TABLE.md:35,42` (bomb **0.619**, knife **0.000**, gun
**0.009** of 113 domains; on the 23 TEST domains bomb 0.522, knife 0.000, gun 0.000).

### The geometry makes the problem sharper than the prose does

From `dose.py`, cosines between the exported raw axes:

```
L      cos(spec,bomb)  cos(spec,knife)  cos(spec,gun)  cos(bomb,knife)  cos(knife,gun)
L6        +0.2162         -0.6790         -0.4784         +0.5644          +0.9488
L9        +0.4069         -0.6434         -0.3521         +0.4301          +0.9125
L12       +0.3770         -0.5885         -0.3348         +0.5191          +0.9264
L14       +0.4263         -0.5686         -0.3086         +0.4908          +0.9119
```

Three things follow, and none of them is in the warning:

1. **`v_knife` and `v_gun` are ~0.91-0.95 collinear at every layer.** They are not two independent
   concept axes being averaged — they are essentially **one** direction measured twice. R-116 says why:
   neither installs, so both are dominated by the common "a harmful demonstration block is present"
   effect. The `mean(v_knife, v_gun)` in the definition is therefore a **single generic
   demonstration-presence axis**, not a two-concept control.
2. **`v_bomb_specific` is only 0.22-0.44 aligned with `v_bomb`** and carries a **large negative**
   loading (-0.55 to -0.68) on that generic axis. It is not "the bomb axis with the other concepts
   removed"; it is closer to *"bomb-demonstration minus generic-harmful-demonstration"*, and most of
   its length lies along the anti-generic component.
3. Consequently the **0.9764 AUROC** is separating *bomb demonstration text* from *knife/gun
   demonstration text*, in a population where — per R-116 — only the bomb arm has an installed
   concept at all. `DCS_TS_CLAIM_TABLE.md:35` already reaches this conclusion by a different route
   ("the three-way separation is **not** 'which concept was installed' — it is **which demonstration
   set is present**"). My geometry corroborates it directly from the exported vectors.

### Is the `interpretation_warning` adequate? — **No, it is one-sided**

Its operative sentence is:

> "Projecting this axis out therefore removes the bomb remapping component **MINUS** an average of
> two non-installing contrasts; **a null is not attributable to the identity content alone**."

That guards **only the null**. Given that PHASE 9's design and `C-112` both anticipate a null, a
caveat that fires only on the expected outcome is doing exactly the PR work the brief asks about.
**A positive result is equally unattributable**, and for a sharper reason: because the axis is
substantially the *anti-generic-demonstration* direction, an intervention that moves the readout may
have moved it by ablating "there is harmful demonstration text here" rather than "the installed
concept is bomb". The warning should say so in both directions.

### What a projection-out result could and could not mean — plainly

**COULD mean, on a positive:** that *some* component of the residual at L6-14 that discriminates
bomb-demonstration prompts from knife/gun-demonstration prompts is causally used by the semantic
readout, at these sites and this dose, on this population.

**COULD mean, on a null:** that this particular ~0.22-0.44-of-`v_bomb` axis is not causally used at
these sites and this dose — the mandated wording, *"DECODABLE BUT NOT CAUSALLY USED UNDER THIS
INTERVENTION"*, remains correct and is the right sentence.

**COULD NOT mean, either way:** anything about *concept identity* specifically. The subtracted term
is not "knife-ness averaged with gun-ness" — it is one generic demonstration-presence axis measured
twice. Nor could a null mean the bomb representation is not used: only 22-44% of `v_bomb` is inside
the ablated axis (see F-5).

**Severity SERIOUS. Would it change a PHASE 9 conclusion?** It changes the **wording**, not the
validity — and it is a property of `PR-053`'s *definition* of `v_bomb_specific`, which was frozen
before R-116 existed, not a defect the export introduced. The export is right to ship the axis
`PR-053` named; it should carry a two-sided warning.

### F-5 (SERIOUS, PHASE 9 wording) — the realised dose is small, and a null is dose-limited

Combining §4 F-4 and §6: projecting `v_bomb_specific` out at α=1 removes only **4.7%-19.0%** of the
cell-mean spread and **4.0%-21.1%** of `‖m_C‖`, and leaves **78%-96% of `v_bomb` intact**
(`1 - cos²(spec, bomb)`). For scale, this repo's `d_surface` arm removed **0.81-0.90** of the
cell-mean spread and that was still argued to be dose-confounded
(`insubspace_null_test.cellmean_dose` docstring, `:319-343`).

A PHASE 9 null under H2a must therefore be reported **with its realised dose attached**, and must not
be worded as though the installation representation was removed — it was not; most of it survives.
`configs/dcs_ts_pr057_phase9.json` `primary.negative` already mandates *"under this intervention"* as
part of the claim; F-5 says what that phrase is standing in for numerically, and those numbers
belong next to the sentence. The config's `cannot_answer` clause ("power < 0.8 at the realised
between-domain SD") is about statistical power; this is a separate **physical** dose limit.

---

## 7. Two factual corrections to `reports/DCS_TS_PHASE9_BLOCKERS_CLEARED.md` §12

| where | says | I observed |
|---|---|---|
| §12.3, last line | "All **25** checks GREEN" | **26**. My `--verify` printed 26 GREEN lines (19 payload + 7 reproduction); `VERIFY.json["checks"]` has 26 entries and `MANIFEST.json["checks"]` has 26. |
| §12.1, `cell_means` note | `cellmean_dose` "0.14-0.17 for `v_bomb_specific`" | **0.047-0.190**. L6 = 0.0467 and L7 = 0.0468 are ~3× below the quoted floor (F-4). |

Both **MINOR**; neither changes a PHASE 9 conclusion. Recorded because §12 is the document a reader
will quote from, and the second one understates a number that F-5 makes load-bearing.

Not a defect, recorded for completeness: `configs/dcs_ts_pr057_phase9.json` `split._exclusion_note`
says *"68 are ANALYSED (restaurant_kitchen, subway_station)"* — two exclusions — while
`split.n_train` is **67** and `configs/dcs_ts_pr053.json` lists **three** whole-population exclusions
(`restaurant_kitchen`, `subway_station`, `school_campus`). The code reads the structured
`n_train`/`preregistered_exclusions` fields, not the prose, so nothing computes on the stale
sentence, and my run bound 67/23/23 correctly. It is a **stale prose string in a FROZEN config**,
and it is the third exclusion the export correctly applied.

---

## 8. Summary

| # | attack line | finding | severity | changes a PHASE 9 conclusion? |
|---|---|---|---|---|
| 1 | leakage into any exported vector | **no finding** — recomputed independently, agrees to 5e-09 | NON-ISSUE | no |
| F-1 | the TRAIN-only property rests on a self-reported field; no check recomputes the arrays | harness gap | **SERIOUS** | no (closed externally in §1b) |
| 2 | circularity in the 0.9764 reproduction | **no finding** — target pre-dates artifact, verify loads from disk, reproduced with `sklearn` | NON-ISSUE | no |
| 3 | mutations on a copy / RED for the wrong reason | **no finding** — 20/20, `raised: null` on every case, each caught by its intended check | NON-ISSUE | no |
| 3′ | `content_sha256` catches several mutations but can never fail on a real export | tamper detector, not a correctness check | MINOR | no |
| 4a | layer-key off-by-one (`block L == hidden_states[L+1]`) | **no finding** — read side and hook side traced, both the same convention | NON-ISSUE | no |
| F-2 | band wider than L6-14 silently edits fewer layers; echo reports the request | latent | MINOR | no (S1/S2 both inside L6-14) |
| F-3 | H2b's `c_knife` is 0.42-1.08× `gap`, per layer; must not be dosed as `alpha=1` | note for the unwritten mode | MINOR | no |
| F-4 | rank-1 `cell_means`; §12.1's `cellmean_dose` range is 0.047-0.190, not 0.14-0.17 | prose error | MINOR | no |
| 5 | sign / orientation | **no finding** — bomb positive at all 9 layers; `project_out` sign-free anyway | NON-ISSUE | no |
| 6 | R-116: is this axis what its name says? | `v_knife`⊥`v_gun` cos **0.91-0.95** — one generic axis, not two concepts; warning guards only the null | **SERIOUS** | **wording, not validity** |
| F-5 | realised dose 4.7-19% of cell-mean spread; 78-96% of `v_bomb` survives the ablation | scoping | **SERIOUS** | **wording, not validity** |
| 7 | "25 checks" vs 26 | count error | MINOR | no |

**No BLOCKING finding.** Nothing I ran contradicts the artifact's numbers; my independent
reimplementations reproduce all of them.

---

## VERDICT

**YES** — the artifact is fit to carry PHASE 9's primary causal claim: the exported
`v_bomb_specific` is provably the TRAIN-only (67-domain) estimate, it reproduces `R-111`'s published
0.976401 under a fully independent reimplementation, it is byte-reproducible from source, and it
matches the consumer's key, dtype and layer-convention contract exactly — **provided** the result is
reported with its realised dose (4.7-19% of the cell-mean spread; 78-96% of `v_bomb` survives, F-5)
and with a **two-sided** R-116 caveat, since `v_knife`/`v_gun` are ~0.92 collinear and the subtracted
term is one generic demonstration-presence axis rather than two concept controls (§6).

---

## F-1 — CLOSED IN THE HARNESS (fix applied 2026-09-07, by a later session)

F-1 was closed EXTERNALLY above: `indep.py` re-derived the vectors from the caches and matched the
shipped ones to 5e-09, with a leaked fit 1.1e-02 away. That proves the shipped artifact is clean
TODAY; it does not make the artifact SELF-verifying tomorrow. This section records the change that
does, and the numbers it produced. **The producer script and the artifacts under
`outputs/dcs_ts/directions_pr053/` are the only things that were written; nothing was committed,
staged or stashed.**

### The check — `check_train_only_recomputation`, `scripts/dcs_ts_export_directions.py`

Two new rows, added inside `check_payload` (so `--export`'s pre-write gate, `--verify` and every
mutation case all run them), backed by `train_refit()`, which re-derives the directions from
`ctx["arm"]["Dmean"]` over `ctx["train"]` — the TRAIN set `prepare()` rebuilds from the FROZEN
SPLIT MANIFEST, never from `meta.fit_domains`:

| row | what it compares | catches |
|---|---|---|
| `direction arrays RECOMPUTED from the TRAIN rows equal the stored arrays (atol 1e-06, not trusting meta.fit_domains)` | every stored unit vector, and every `gap` scalar, against the manifest-TRAIN refit | **arrays leaked, metadata honest** |
| `meta.fit_domains == the TRAIN set rebuilt from the frozen split manifest` | the producer's self-report against the same rebuilt set | **arrays honest, metadata lying** |

**The tolerance is taken from the two numbers section 1b measured, and the reasoning is in the
comment on `REFIT_ATOL`.** An honest float32 payload agrees with the refit to ~5e-09 (the storage
floor); a leaked fit is ~1.1e-02 away (the smallest deviation that must be caught). `REFIT_ATOL =
1e-6` sits ~200x above the floor and ~10<sup>4</sup>x below the leak — inside a six-order-wide
window, which is why the check has resolution rather than merely a threshold. `gap` is a float64
scalar and matches EXACTLY on an honest export, so `REFIT_GAP_RTOL = 1e-9`.

**Observed residuals (from my `--verify` and `--mutate` on the shipped artifact):**

```
honest, shipped artifact : max|unit diff| 7.186e-09   (worst direction), gap rel-diff 0.000e+00
leaked mutant (TRAIN+TEST): max|unit diff| 1.121e-02   vs atol 1e-06, gap rel-diff 3.518e-02
```

— i.e. the shipped artifact clears the threshold by ~140x and the leak trips it by ~11210x, the
same six orders of separation `indep.py` reported, now inside the artifact's own harness.

### The mutations — 22/22 RED, `raised: null` on every case

Two were added. The count is not hand-typed anywhere: `--verify` prints `N checks` and
`{green}/{N} checks GREEN`, `VERIFY.json` carries `n_checks` / `n_checks_green` /
`n_checks_red`, and `--mutate` prints `n/N`.

* **#21 `arrays LEAKED (fitted on TRAIN+TEST) while meta.fit_domains still reports the 67 TRAIN
  domains`** — the mutation F-1 says was missing. It turns **exactly 1 check RED**, and that
  check is the new recomputation row; `raised` is `null`, so it is a real guard and not an
  exception standing in for one. Every metadata-reading TRAIN-only check, the algebra check and
  `content_sha256` all stay GREEN on it, exactly as F-1 predicted — **before this change it passed
  all 26.**
* **#22 `arrays honest, meta.fit_domains swaps one TRAIN domain for a TEST domain (count
  unchanged)`** — the mirror, made subtler than the existing #4 (which rewrites the field to the 23
  TEST domains and so also trips the count check). 3 checks RED, including the new
  domain-set row.

`--selftest` grew from 16/16 to **21/21**: the new cases drive `check_train_only_recomputation` on a
toy arm — honest fit GREEN on both rows, leaked arrays RED on the array row only, lying metadata RED
on the domain-set row only, a `2 x REFIT_ATOL` shift RED — plus an assertion that `REFIT_ATOL` lies
between the 5e-09 floor and the 1.1e-02 leak. `MUTATIONS.json` now also records `red_details`, so
the residual behind each verdict is on disk, not only in a terminal.

### Nothing about the exported vectors changed

`--export` into a fresh directory reproduces the shipped payload **bit for bit**:

```
shipped content_sha: 8df3fdec93c4c7b73cf38178612cc365608ab9a9f04351b1dadf0fadbe56a435
fresh   content_sha: 8df3fdec93c4c7b73cf38178612cc365608ab9a9f04351b1dadf0fadbe56a435   MATCH
```

`build_payload` was not touched; the change is verification-only. **`directions_fit_dev.pt` was
therefore left exactly as shipped** (re-exporting would change only `meta.written_utc`, and with it
the `payload_sha256` that `reports/DCS_TS_PHASE9_BLOCKERS_CLEARED.md:674` publishes). `VERIFY.json`
and `MUTATIONS.json` were regenerated; `MANIFEST.json` still carries the 26-row pre-write log from
the original export, which is the correct historical record of that export — `VERIFY.json` is the
current authority.

### The check count

**28**, all GREEN, verdict GREEN (26 before this change — the reviewer's 26, not the
"25" printed in `reports/DCS_TS_PHASE9_BLOCKERS_CLEARED.md:756`). That line is in a file this
session was scoped not to edit; section 7 above already records the correction, and the number it
should now read is **28**. The count itself is no longer transcribed by hand anywhere in the
producer.

### What this does and does not buy

It removes the `feedback_check_reads_same_broken_source` hole: the TRAIN-only property is now
enforced by ARITHMETIC over the manifest's TRAIN rows, not by a field the producer writes about
itself, and a disagreement in either direction is RED. It does not touch F-2 through F-5 or the
section 6 wording caveat, all of which stand as written.
