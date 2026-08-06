# VERIFY_P4B1_ANALYSIS — analysis & pooling audit for P4b-1 (sharded jobs 728710/728711)

Scope: `scripts/phase5_analyze.py` (authoritative pooled analyzer) + `scripts/phase5_head_zpatch.py`
(the per-job run script that also writes `summary.json`), checked numerically against the completed smoke
`outputs/phase5_headz_clearharm_demo_20260806_181558_728619/` (raw.jsonl + summary.json).
Pre-reg reference: `reports/P4B_PREREGISTRATION.md` §1 (one Holm family of 32×32 = 1024 cells per (C,P),
per split; a cell "survives" only if Holm-sig on BOTH dev and heldout).

Bottom line: the **pooling path is correct and a valid 1024-cell command exists** (Q1 OK), splits are kept
separate (Q4 OK), Wilcoxon is the test used (Q3 OK). The run's raw data is sound, so **the GPU jobs do NOT
need to be killed on account of the family/pooling structure.** But there are real analysis-plan defects
that MUST be fixed before any P4b-1 number is quoted: an estimand mismatch vs pre-reg §2, an unenforced
1024-cell assumption, and a power floor that the per-shard `summary.json` does not surface.

---

## Q1 — What family does `phase5_analyze.py` Holm-correct over? Can it pool two shard dirs?

**Family:** per split, it Holm-corrects over `pv`, one p-value per `(layer,head)` cell that has valid diffs
(`phase5_analyze.py:87-97`, `holm()` at :47 uses `m = len(pv)`). It does NOT correct across channel or
position-set — exactly the "32×32 head grid, per (C,P), per split" the pre-reg §1 asks for.

**Pooling: YES, natively.** `main()` reads `sys.argv[1:]` as a list of dirs and concatenates every dir's
`raw.jsonl` into one `rows` list *before* building `pv` (`:61-73`). Layer shards are disjoint (0-15 / 16-31),
so pooling the two dirs yields 16×32 + 16×32 = **1024 cells**, and `valid`/`C1` are computed per sid and are
identical across shards, so the union is consistent. It does NOT assume a single dir.

**Exact pre-registered command** (run from `doublespeak_causality/`, per cohort — here clearharm/demo):
```
python scripts/phase5_analyze.py \
  outputs/phase5_headz_clearharm_demo_*_728710 \
  outputs/phase5_headz_clearharm_demo_*_728711
```
This prints, per split: `n_cells` (should read 1024), `n_valid`, `selfswap_dev`, `underpowered`, the
Holm-sig positive-necessity heads, and top-12 by necessity. **This command produces the pre-registered
1024-cell result. It is not a gap.**

Verified on the smoke (single 4-layer dir): analyzer logic reproduces `n_cells = 128` (4×32) and the exact
`top10_by_mean` in `summary.json`, e.g. heldout L8H11=0.0114, L8H29/L9H23/L10H1/L9H19/L8H28=0.0086 — a
byte-match. Pooling two 16-layer dirs is the same code path scaled to 1024.

Caveat (see Finding F2): `m = len(pv)` is data-dependent. Pointed at **one** dir, or at a truncated shard,
it silently Holm-corrects over <1024 cells with **no error** — you must eyeball the printed `n_cells`.

---

## Q2 — Does each job's per-shard `summary.json` under-correct? By how much?

The per-shard `summary.json` is written by the **run** script `phase5_head_zpatch.py`, not by the analyzer.
Its embedded Holm loops `for l in layers: for h in range(n_heads)` (`:258-263`) over only that job's layer
set. So job 728710 (layers 0-15) → 512 cells; job 728711 (layers 16-31) → 512 cells. Its `holm()` uses
`m = len(pv) = 512`.

**Direction: UNDER-correction (too permissive).** The most-significant-cell threshold is α/m:
- per-shard: 0.05/512 = **9.77e-5**
- pre-registered pooled: 0.05/1024 = **4.88e-5**

So reading a per-shard `summary.json` directly applies a threshold **≈2× too lenient** (2× at the top cell;
α/(512-i) vs α/(1024-i) ≈ 2× across the whole step-down for small i). It inflates false positives. **Do not
quote `holm_sig_heads`/`n_holm_sig_heads` from either per-shard `summary.json`; they are per-512-cell, not
the pre-registered per-1024-cell family.** Only the pooled analyzer output is authoritative (the run
docstring even says so: `phase5_head_zpatch.py:11`).

---

## Q3 — Wilcoxon per (layer,head)? Does the smoke corroborate?

**Yes.** `phase5_analyze.py:pval` (:20-35) computes a two-sided **Wilcoxon signed-rank** p (`stats.wilcoxon`)
on the paired necessity diffs `C1 − p_patched_benign`, matching its docstring (:21). The run script's
`perm_p` (:227-238) is the identical Wilcoxon (despite the misleading name `perm_p` / "permutation" comment),
so the `summary.json` you can read now was produced by the same test the analyzer will apply.

**Smoke recomputation (from raw.jsonl):** means match `summary.json` exactly (dev all 0.0; heldout top as
above). Both scripts guard `a.size < 6 → p = 1.0`. The smoke has **n_valid = 2** per split (it ran
`--n-prompts 2`), so every cell's p = 1.0 and `n_holm_sig_heads = 0` in `summary.json` — consistent. Note
the smoke therefore **does not actually exercise Wilcoxon at a significant cell**; it only proves the code
runs and the means/splits are right, not that significance behaves at scale.

---

## Q4 — dev vs heldout: separated or pooled?

**Separated.** Both scripts iterate `for split in ...` and compute `valid`, `pv`, Holm, and top cells
independently per split (`phase5_analyze.py:74-109`; `phase5_head_zpatch.py:248-271`). The smoke
`summary.json` has distinct `by_split.dev` and `by_split.heldout` blocks with different numbers
(dev top = all 0.0; heldout top = 0.0114…). Splits are **not** pooled. Confirmed.

Gap (F3): neither script computes the pre-reg §1/§4 **intersection** (a cell Holm-sig in the *same* (l,h) on
BOTH splits). Each reports its own per-split Holm set; the "both splits" survival gate must be applied by
hand by intersecting the two `holm_sig` lists. Not a bug, but an easy place to over-claim if skipped.

---

## Additional findings (must be resolved before quoting P4b-1)

### F1 — HIGH: analyzer computes RAW necessity, not the pre-registered specificity-controlled estimand
Pre-reg §2 defines the reported quantity as `necessity_specific(l,h,P) = (C1 − benign-patched) −
(C1 − count-matched RANDOM-donor)`, i.e. a **per-head** random-donor subtraction. The analyzer computes only
`C1 − benign` (`phase5_analyze.py:88, :90-91`) — no random-donor term. And the raw cannot supply one: the
run captures the random donor (`cell="normrand"`) at a **single probe cell** `(layers[len//2], head 0)` only
(`phase5_head_zpatch.py:200-221`; smoke raw has 4 `normrand` rows total vs 512 `benign`), never per (l,h).
**Consequence:** any "necessity" figure from this pipeline is plain necessity, NOT the §2
specificity-controlled necessity; labeling it as the pre-registered estimand would be wrong. This does not
corrupt the raw run (kill not required), but the report must either (a) relabel the estimand as raw
necessity and amend §2, or (b) add a per-head random-donor pass (doubles the head sweep) before claiming
specificity control.

### F2 — MEDIUM: 1024-cell family is assumed, never enforced
`holm()` uses `m = len(pv)`, so a missing shard, a partial/truncated `raw.jsonl`, or accidentally passing
one dir silently corrects over <1024 cells and **under-corrects with no error**. Minimal fix: before quoting,
assert `n_layers == 32` and `n_cells == 1024` per split (the analyzer already computes/prints both at
`:99, :106-107` — promote to a hard check, or at least gate the headline on it).

### F3 — MEDIUM: "both splits" survival gate is manual
See Q4. The intersection of dev and heldout Holm-sig cells is required by §1/§4 but computed by neither
script. Add an explicit `dev ∩ heldout` step to the analyzer, or document that reporting must intersect.

### F4 — HIGH (readiness, not a code bug): power floor — need n_valid ≥ 16 per split
Two-sided Wilcoxon's minimum achievable p for n all-same-sign pairs is ≈ 2/2^n. For the 1024-family top
threshold 4.88e-5 this requires **n_valid ≥ 16** (verified: n=15 → 6.10e-5 fails; n=16 → 3.05e-5 passes).
`valid` further filters to sids with `C1 > benign_p_concept`, which can drop many. **If the full clearharm
run yields < 16 valid sids per split, NO cell can clear Holm regardless of the true effect — any null is a
power artifact, not evidence of no head.** The analyzer flags this via `underpowered` (`:104-105`), but the
per-shard `summary.json` does **not** report `pfloor`/`underpowered` (`:269-271`), so reading `summary.json`
will not tell you the family is unresolvable. Action: after the jobs finish, run the pooled analyzer and
confirm `underpowered=False` (n_valid ≥ 16) on both splits before interpreting any 0-significant-head result.

---

## Verdict
Family structure and pooling for P4b-1 are **correct**; the pre-registered 1024-cell result is reproducible
with the single command above, and the raw data is sound — **no reason to kill jobs 728710/728711 on these
grounds.** But before any P4b-1 number is quoted: fix/relabel the §2 estimand (F1), enforce n_cells=1024
(F2), apply the dev∩heldout gate (F3), and verify n_valid ≥ 16 per split via the analyzer, not the per-shard
`summary.json` (F4). Never quote the per-shard `summary.json` Holm sets — they under-correct ≈2× (Q2).
