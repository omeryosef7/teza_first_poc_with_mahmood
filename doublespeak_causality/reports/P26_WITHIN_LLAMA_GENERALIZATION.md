# §26 — Within-Llama Generalization of the Refusal-Suppression Mechanism

**Status: ✅ DONE.** Assembled from **already-committed** evidence — **no new GPU run**. This report closes
plan §26 by laying every committed within-Llama (meta-llama/Llama-3.1-8B-Instruct) result out as an
**axis × property matrix**: for each of the four headline mechanism properties, does it hold, and does it
generalize across the requested axes?

**One-line verdict.** Within Llama, the refusal-suppression mechanism generalizes on **existence + causal
control + prediction** across unseen concepts/codewords/clusters, cohort, and demo-count — all on the
**cluster-disjoint v3 held-out test** — while **attack-optimization is the single NEGATIVE** (Gate-7
first-cut: the mechanism-derived objective is not refusal-specific). The one genuinely **thin** axis is the
dedicated *novel-benign-codeword* swap, whose only committed probe is a concept-remap readout (the
epiphenomenal channel), not a refusal-mechanism transfer test.

---

## 0. The generalization substrate — why "held-out" here means cluster-disjoint

All property results below are read on the **v3 split** `data/splits/clearharm_doublespeak_v3.json`
(`reports/P1B_V3_SPLIT.md`), which is **leak-free by construction**:

- Two cohorts, both full 6-condition, both ≥20/side: **`clearharm` (170 rows)** = ClearHarm-native
  instructions; **`generated` (154 rows)** = new single-token harm concept + one-line request.
- Split integrity (from the build log): `v3_clearharm: concepts_straddling=0/70, codewords_straddling=0,
  clusters_straddling=0, rows_any_leak=0`; `v3_generated: concepts_straddling=0/154,
  codewords_straddling=0, clusters_straddling=0, rows_any_leak=0`. Codewords are **pairwise disjoint per
  split** (104/60/60). Per-cohort sizes: train {ch 85, gen 77} · dev {ch 43, gen 39} · test {ch 42, gen 38}.

So **every test-split concept, codeword, and intent-cluster is unseen relative to train.** This is what
supersedes the old v1 caveat — the master-plan line *"Generalizes to unseen concepts/codewords — ⚠
UNSUPPORTED (64% of v1 rows straddled at concept level, §0.4)"* was a **v1** artifact; v3 is cluster-disjoint
by construction, so the generalization claims below are read on a leak-free test.

---

## 1. Axis × Property matrix

Rows = the four §26 mechanism properties. Columns = the generalization axes. Each cell:
✓ generalizes · ~ partial/thin · ✗ negative · n/a axis does not apply to that property. Key statistic +
run-dir in the cell.

| property ↓ / axis → | **Unseen concepts / codewords / clusters** (cluster-disjoint held-out test) | **Cohort split** (clearharm vs generated / curated) | **Variable demo count** (n_demo 0→12) | **Alternate / novel benign codeword** |
|---|---|---|---|---|
| **(1) Existence** — does the refusal direction exist? | **✓** L18 validates in **two independently-fit families** (incl. a from-scratch ClearHarm-native refit) on **held-out ClearHarm** items: ablate **+0.900** / induce **+0.800** (`clearharm`), +0.600/+1.000 (`existing`); **11 layers valid in both families** (L13–20,24,28,29). `refval_clearharm_..._721957`, `..._722611` | **~** existence validated on the **clearharm** cohort only; the same validated L18 axis is *applied* to `generated` in the causal arms below, but not separately re-fit/validated per-cohort. `refval_clearharm_..._721957` | **n/a** (axis existence is a fit property, not a demo-count quantity; the demo-count effect on the axis is under (2)/(3)) | **n/a** (the direction is fit on a refusal contrast, not on codewords; codeword-agnostic) |
| **(2) Causal control** — does intervention change behavior? | **✓** on cluster-disjoint splits: refusal⊥concept ablation **ΔASR −0.212 (p=0.0001)** train (§24); decision-state patch **mediated fraction ≈1.07 train / 1.00 dev, McNemar p=0.0013 / 0.0039** (§25). Concept lever is an exact null (§10). `phase24_..._736571`, `refdecpatch_clearharm_..._732560` | **~** concept-null shown in **both** cohorts — §10 write+carry ΔASR **clearharm 0.000** (b=22/c=22, p=1.0) vs **generated +0.097** (p=0.04), both **< random +0.124/+0.201** (specificity); the *refusal-lever* positive (§24/§25) is established on **clearharm** only. `phase10_powered_concept_..._732980` | **~** step-not-ramp: refusal proj @L18 **4.02→2.98** at n=0→1 then flat; within-item **dRefusal↔dASR = −0.292 train / −0.162 test** (weak, \|r\|<0.3); ASR slope null. `dose_response_clearharm_20260808_124748_735299` | **✗ / thin** no refusal-mechanism transfer run; only committed probe is concept-remap (see §3), which does **not** transfer (0.7→0.0). `novelword_..._699245` |
| **(3) Prediction** — does projection predict success? | **✓** item-level DS refusal projection predicts jailbreak at **AUC 0.874** (Mann-Whitney p=3.8e-9, point-biserial r=−0.584) on cluster-disjoint clearharm; **all 11** cross-family-validated layers Holm-significant (AUC 0.773→0.888, L16 0.888 / L18 0.882); **20/32** layers Holm-sig. `rep_predicts_behavior` (joins `refproj_*` + `behav_refusal_*`) | **~** strong on **clearharm (AUC 0.874)**, **null on curated (AUC 0.42, p=0.79, 0/32 Holm-sig)** — but *explained*: curated suppresses refusal uniformly (proj std 1.84 vs 3.51), so projection can't discriminate; limiting factor there is concept-dilution, not a refusal-locus failure. `rep_predicts_behavior` | **~** within-item **dRefusal↔dASR −0.292 train / −0.162 test** — the projection change tracks ASR change across demo steps (weak but consistently signed). `dose_response_clearharm_20260808_124748_735299` | **n/a** (item-level projection readout is codeword-agnostic; unseen codewords covered by the held-out-test column) |
| **(4) Attack optimization** — does the objective help search? | **✗ NEGATIVE** suffix optimized on 20-item train, held-out test n=42 (cluster-disjoint): refusal-suppression **@ validated L18 ASR 0.405 < norm-matched random 0.476** (and < unvalidated L22 0.500); vanilla GCG 0.262. Objective moved the search but is **not refusal-specific**. `phase9_gcg_mac_matrix_arm07_L18_seed42` (job 732918), `p9_heldout_asr_summary.json` (job 736438) | **n/a** (single cohort, one seed, 50 steps — first-cut only) | **n/a** | **n/a** |

---

## 2. Per-property read (verbatim numbers, with source)

**(1) Existence — ✓ generalizes.** `P7_REFUSAL_DIRECTION_VALIDATION.md`. Base harmful refusal 0.950;
n=20/cell (ablate), n=10 (induce). L18 — the direction every downstream behavioral arm uses — validates
strongly in **both** independently-fit families on held-out ClearHarm: `existing` ablate +0.600 / induce
+1.000; `clearharm` (a from-scratch ClearHarm-native refit) ablate +0.900 / induce +0.800. The full 32-layer
sweep (job 722611, 3870 rows, 1348 values reconciled / 0 mismatched) gives a **contiguous** valid block:
L0–12 fail in both families without exception, L13–20 pass in both without exception; 11 layers valid in
both (13–20,24,28,29). L9 fails in both families on both arms (the "refusal not read early" contrast, as
claimed). Runs: `refval_clearharm_..._721957` (headline), `..._722611` (full sweep), `..._720463` (ablate).

**(2) Causal control — ✓ generalizes (refusal lever), with concept lever a controlled null in both
cohorts.**
- §10 (`P10_POWERED_CONCEPT_ABLATION.md`, `phase10_powered_concept_..._732980`, pooled n=324): the concept
  circuit is behaviorally negligible **via specificity** — a count-matched **random** ablation reduces ASR
  *more* than the concept-circuit ablation (+0.161 vs +0.046 pooled; **clearharm write+carry ΔASR exact
  0.000** vs random +0.124; generated +0.097 vs random +0.201). Holds in **both** cohorts.
- §24 (`P24_ORTHOGONALIZATION.md`, `phase24_..._736571`): after removing concept↔refusal overlap, the
  **refusal component alone** controls ASR — refusal⊥concept **ΔASR −0.212 (p=0.0001)** train; concept⊥refusal
  does not reduce ASR (+0.106). Test underpowered (n=42, ns) but same sign.
- §25 (`P25_FULL_MEDIATION.md`, `refdecpatch_clearharm_..._732560`): restoring the DS decision-state to the
  refusing value removes ~100% of DS's ASR advantage — **mediated fraction ≈1.07 (train, p=0.0013) / 1.00
  (dev, p=0.0039)**; norm-matched-random and self-donor controls do not. Chain: demos suppress the refusal
  representation (§6) → that state (near-)fully mediates behavior.

**(3) Prediction — ✓ generalizes on clearharm, cohort-dependent (explained).**
`REP_PREDICTS_BEHAVIOR.md`. A DS prompt's refusal projection classifies its jailbreak at **AUC 0.874**
(clearharm, n=86/32 malicious; Mann-Whitney p=3.8e-9; point-biserial r=−0.584, p=3.7e-9). Layer-stable:
all 11 cross-family-validated layers Holm-significant (AUC 0.773→0.888; L16 0.888, L18 0.882); 20/32 layers
Holm-sig. **curated is a null (AUC 0.42, p=0.79)** — explained mechanistically: curated suppresses refusal
uniformly, so projection can't discriminate who jailbreaks; the limiting factor there is concept-dilution.

**(4) Attack optimization — ✗ NEGATIVE (the one non-generalizing property).** `P_GATE7_FIRSTCUT.md`. Held-out
StrongREJECT ASR (test n=42, suffix optimized on 20-item train, compute-matched): vanilla GCG **0.262**;
refusal @ validated L18 **0.405**; refusal @ unvalidated L22 **0.500**; **norm-matched random @ L18 0.476**.
The objective changes the search (all repr arms 0.40–0.50 > vanilla) but is **not mechanism-specific** — the
random control beats the validated refusal objective, so Claim F (a refusal-derived objective improves
adversarial optimization) is **not supported at first-cut**. A well-controlled negative. Caveat: one seed
(42), 50 steps, single cohort — directional, not definitive.

---

## 3. The one thin axis — dedicated novel-benign-codeword transfer

"Unseen codewords" as a *distribution* is fully covered by the cluster-disjoint held-out test (test codewords
pairwise disjoint from train, §0). The **dedicated single-codeword swap** has exactly one committed run,
`novelword_..._699245` (scalar `novelword_summary.json`), and it probes only the **concept-remap** channel
(the epiphenomenal one, per §10), not the refusal mechanism:

- pair bomb↔carrot, novel word **"pencil"**, one-word readout, n=20/variant.
- **DS_orig reads_as_concept_rate 0.7** (mean_p_concept 0.208) → **DS_novel ("pencil") 0.0** (mean_p_concept
  0.0); NEUTRAL_novel 0.0.

So the concept-remap does **not** transfer to an arbitrary novel codeword — consistent with the remap being
epiphenomenal — but this is **not** a refusal-mechanism transfer test. **Honest statement of the gap:** for
the refusal-suppression mechanism specifically, the novel-benign-codeword axis is covered only by the
cluster-disjoint held-out test (unseen codewords in aggregate); a dedicated single-novel-codeword refusal
transfer run was **not** performed. This is the one thinner axis.

---

## 4. Verdict — §26 DONE

Within Llama, on the leak-free cluster-disjoint v3 test:

1. **Existence generalizes (✓):** the refusal direction validates on held-out ClearHarm under two
   independent fits, strongest and cross-validated at L18 (ablate +0.900 / induce +0.800).
2. **Causal control generalizes (✓):** intervening on the refusal component / decision-state changes
   behavior (ΔASR −0.212, p=1e-4; mediated fraction ≈1.0), while the concept lever is a controlled null in
   both cohorts.
3. **Prediction generalizes (✓ on clearharm):** the refusal projection predicts jailbreak at AUC 0.874
   (p=4e-9), layer-stable across all 11 validated layers; the curated null is mechanistically explained
   (uniform suppression → concept-dilution), not a counterexample.
4. **Attack optimization does NOT (✗):** the mechanism-derived GCG objective (0.405) is beaten by a
   norm-matched random control (0.476) on held-out test — Gate-7 first-cut negative, mechanism not specific.

**Assembled from committed evidence; no new GPU run.** The single thin axis is the dedicated
novel-benign-codeword swap, which only has a concept-remap probe (§3).
