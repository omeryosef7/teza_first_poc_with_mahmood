# P6 — Curated behavioral join + formal peak-layer inferential test

**Status:** Both §12-remaining sub-tasks executed from raw per-item ‖J‖ / labels. No GPU, no new runs.
Single model (Llama-3.1-8B-Instruct). Seed=0 for every bootstrap; 5000 resamples.

**Bottom line:**
- **(1) Curated behavioral join = NULL / UNDERPOWERED.** On the curated cohort neither the refusal ‖J‖
  nor the concept ‖J‖ predicts jailbreak (all CIs include 0.5); the refusal−concept paired diff is −0.05
  [−0.239, 0.157]. This is expected-by-construction (curated suppresses refusal *uniformly* →
  concept-dilution, not under-suppression), and the cohort is small (n=51, only 11 MALICIOUS; locked test
  has just **2** positives → uninformative).
- **(2) Peak-layer test = VERIFIED on both cohorts, both targets.** The ‖J‖ peak is inferentially mid-band:
  concept modal peak **L16**, refusal modal peak **L12**, and mid(L12–17) ≫ late(L28–30) with paired-bootstrap
  CIs clear of 0 and sign tests 100% of items (p≈0). Meanwhile the linear *readout* (projection) of the same
  targets peaks late (L25–L30). The mid-causal / late-readout dissociation now has inferential support, not
  just an argmax of point estimates.

---

## Files / columns used

- Jacobian raw (per-item, per-layer ‖J‖): `outputs/jacobian_clearharm_20260807_132150_732004/raw.jsonl`
  and `outputs/jacobian_curated_20260807_132644_732011/raw.jsonl`.
  Columns: `item_key`, `split`, `condition` (filtered = `doublespeak`), `target` (`concept`/`refusal`),
  `by_pos["final_prompt"][layer]["grad_norm"]` (= ‖J‖, layers 0–30), `["jac_proj"]`, `scalar`.
- Readout peak cross-check: `summary.json → by_split_condition[train|doublespeak].by_position.final_prompt.<target>.per_layer[*].proj_<target>`.
- Behavioral labels (curated join): `outputs/behav_refusal_curated_a1.0_20260804_125055_708039/raw.jsonl`,
  columns `id`, `split`, `ds_base_label` (MALICIOUS=jailbroken → 1). Join `item_key == id`, exact, 51/51.
- Clearharm labels (sanity reproduction only): `outputs/behav_refusal_clearharm_a1.0_20260804_133355_708038/raw.jsonl`.

## Scripts

- **Reused unchanged:** `scripts/analyze_jacobian_predicts_behavior.py` (curated run → new output
  `outputs/p6_predicts_behavior_curated.json`). Reproduced the committed clearharm numbers exactly
  (refusal ‖J‖ pooled AUC 0.807, diff +0.2245 [0.0549, 0.3607]) before running curated.
- **New sibling:** `scripts/analyze_jacobian_peaklayer.py` → `outputs/p6_peaklayer_clearharm.json`,
  `outputs/p6_peaklayer_curated.json`. Bootstraps (over items) the argmax layer of mean ‖J‖ and the
  pre-specified MID (L12–17) vs LATE (L28–30) band contrast, per target. Seed=0, 5000 resamples.

---

## (1) Curated behavioral-prediction join

Doublespeak `final_prompt` Jacobian × `ds_base` StrongREJECT label. Peaks L16 (concept) / L12 (refusal),
matching clearharm. AUC oriented ≥0.5, seeded 5000-resample percentile bootstrap. n=51 (train 30 / test 21),
11 MALICIOUS total (train 9 / **test 2**).

| feature | pooled AUC [CI] | train | test (locked) | verdict |
|---|---|---|---|---|
| refusal ‖J‖ @ L12 | 0.564 [0.381, 0.739] | 0.603 | 0.290 | **NULL / UNDERPOWERED** (CI incl. 0.5) |
| refusal scalar (L31 proj) | 0.652 [0.486, 0.809] | 0.656 | 0.500 | NULL (CI incl. 0.5) |
| refusal jac_proj @ L12 | 0.675 [0.473, 0.863] | 0.709 | 0.500 | NULL (CI incl. 0.5) |
| concept ‖J‖ @ L16 | 0.614 [0.405, 0.815] | 0.550 | 0.711 | NULL (CI incl. 0.5) |
| concept scalar (logit-diff) | 0.639 [0.466, 0.802] | 0.587 | 0.842 | NULL (CI incl. 0.5) |
| concept jac_proj @ L16 | 0.516 [0.307, 0.731] | 0.540 | 0.368 | NULL (CI incl. 0.5) |

**Paired refusal ‖J‖ − concept ‖J‖ AUC diff = −0.05, 95% CI [−0.239, 0.157] — includes 0. → NULL.**

Reads: the clearharm dissociation does **not** transfer to curated, exactly as the P6 report §3 caveat
predicted (curated's refusal projection was already non-predictive at AUC≈0.42 in `REP_PREDICTS_BEHAVIOR`).
Every predictor is at chance on curated. The locked-test column is essentially meaningless (2 positives) and
should not be interpreted. Verdict: **cross-cohort behavioral join UNDERPOWERED / NULL**, not a contradiction
of the clearharm result — a floor effect from uniform refusal suppression + tiny malicious count.

---

## (2) Formal peak-layer inferential test

Doublespeak, `final_prompt`. ‖J‖ = `grad_norm`. Bootstrap over items (seed=0, 5000). Bands pre-specified:
MID = L12–17, LATE = L28–30.

### (a) Bootstrapped argmax peak layer of ‖J‖

| cohort | target | point peak | modal peak (freq) | peak 95% CI | % bootstrap peaks in MID (L12–17) | verdict |
|---|---|---|---|---|---|---|
| clearharm | concept | L15 | **L16** (35.2%) | [L0, L16] | 96.9% | **VERIFIED mid** (L0 tail only) |
| clearharm | refusal | L12 | **L12** (100%) | [L12, L12] | 100% | **VERIFIED mid** |
| curated | concept | L16 | **L16** (100%) | [L16, L16] | 100% | **VERIFIED mid** |
| curated | refusal | L12 | **L12** (98.3%) | [L12, L12] | 100% | **VERIFIED mid** |

Clearharm concept CI lower bound touches L0 (a known secondary L0 spike — train top-5 included L0 in the P6
report), but 96.9% of resamples peak inside L12–17 and the mode is L16; refusal is rock-solid at L12 in every
resample.

### (b) Mid (L12–17) vs Late (L28–30) contrast — paired bootstrap + sign test

| cohort | target | mean MID | mean LATE | diff (MID−LATE) | 95% paired-boot CI | sign test | verdict |
|---|---|---|---|---|---|---|---|
| clearharm | concept | 8.73 | 3.87 | +4.86 | [4.31, 5.43] | 86/86 items, p≈0 | **VERIFIED** |
| clearharm | refusal | 33.73 | 6.49 | +27.24 | [24.61, 29.87] | 86/86, p≈0 | **VERIFIED** |
| curated | concept | 8.45 | 3.88 | +4.57 | [4.04, 5.15] | 51/51, p≈0 | **VERIFIED** |
| curated | refusal | 25.98 | 6.42 | +19.56 | [17.82, 21.47] | 51/51, p≈0 | **VERIFIED** |

All four contrasts: CI excludes 0, every single item has MID > LATE (sign test exact two-sided p ≈ 0).

### Readout peaks late (anchor for the scientific point)

Cross-check of the *linear readout* (|projection| of the same target direction) on the same
doublespeak/final_prompt curve:

| cohort | target | ‖J‖ (causal) peak | |projection| (readout) peak |
|---|---|---|---|
| clearharm | concept | L16 | **L30** |
| clearharm | refusal | L12 | **L30** |
| curated | concept | L16 | **L25** |
| curated | refusal | L12 | **L26** |

⇒ The **mechanism (‖J‖) peaks mid-band (L12/L16), the readout (projection) peaks late (L25–L30)** — the
"readout ≠ mechanism" dissociation, now established with inferential support (bootstrapped argmax +
paired-band contrast + sign test) rather than a bare argmax. **VERIFIED, both cohorts, both targets.**

---

## Missing data / caveats

- Curated behavioral join is genuinely **underpowered**: 11 MALICIOUS of 51; locked test = 2 positives.
  Report the NULL, do not over-interpret. No larger curated behavioral label set exists on disk (only the
  a1.0 run has per-item `ds_base_label`; the asweep run is a dose sweep, not a cleaner single-alpha label set).
- Single model (Llama-3.1-8B-Instruct); no cross-architecture check.
- ‖J‖ is a partly-generic sensitivity profile (P6 report §3): the mid-band peak is target-agnostic in
  magnitude, so the *peak-layer* result establishes "‖J‖ peaks mid, not late" but the target-specific signal
  lives in `jac_proj`/projection — consistent with the readout table above.

_Not committed, per instructions._
