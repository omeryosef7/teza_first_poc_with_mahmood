# ADVERSARIAL REVIEW #9 (i) — HERETIC-CSI interim deliverables (S-196)

Reviewer: fresh, independent, read-only (one file written: this one). No jobs and no commits. The only code I ran was
a copy of `build_registry.py` that wrote to the scratchpad.
Ground truth: `external_md/HERETIC_CAUSAL_SEMANTIC_INSTALLATION_PLAN_AND_PROGRESS_20261001.md` (read S-002…S-006 and
S-047…S-196 in full; later entries and CORRECTIONS take precedence), the mandate §28, committed reports/configs and
`external_repos/heretic` @ 662e4ba2.
Targets: `HERETIC_CSI_FINAL_REPORT_INTERIM.md` (R), `MEETING_UPDATE_MATAN_MAHMOOD_INTERIM.md` (M),
`EXPERIMENT_REGISTRY.json` + `research/heretic_csi/build_registry.py`, `FIGURES_INDEX.md` (FI), `VERIFICATION_INDEX.md`
(VI), `fig_p2a_val_specificity.png` (F1), `fig_p2b_preservation_vs_rank.png` (F2), `make_interim_figures.py`.

**Bottom line.** No withdrawn, voided or superseded number is quoted as a result. I found none of these in R or M:
the S-085 contrast, the VAL incumbent baseline, the S-176 numbers or struck sentence, or any P4/P6/P7 outcome. Most
numbers trace exactly. The synthesis still has 5 HIGH problems:
- (H1) The final P2b operator is described as ARA's objective, but the frozen objective is paired MSE.
- (H2) Two effect-size and rank caveats that the log requires are dropped: the "~9% of whole-state" scope and
  "not exactly 4 dims".
- (H3) The "hypotheses killed" table leaves out the preregistered outcome-D → H1 mapping.
- (H4) The headline P2a VAL r1/r16 artifacts that F1 and the registry rely on are untracked in git.
- (H5) F1 shows the fragile, descriptive basket r4 cell styled the same as the confirmed button r4 cell.

---

## HIGH

**H1 — R:20-22 (and R:17, M:19). The P2b operator is not "a clean-room reimplementation of ARA's objective".**
S-006 built the kNN-steer clean-room objective (`operator_ara.py`). But P2b production (`p2b_operator.py`) froze
**paired MSE, steer 0.3** by TRAIN CV, with kNN at 0.38 vs 0.650 pooled net (S-074; the registry itself records
`"objective": "paired MSE, steer 0.3"`). This matters for §28.2 Q1, "What parts of Heretic were useful?": ARA's kNN
objective lost the CV. What carried over was the LoRA ΔW=B·A operator on o_proj/down_proj, the preserve term and the
infrastructure.
*Fix R:20-22:* "The headline P2b operator used Heretic's ΔW=B·A parameterisation and preserve/steer structure, but its
steer term was selected by TRAIN-only CV among {kNN, MSE, cos, whiten}. Paired MSE won (pooled held-out net 0.650 vs
kNN 0.38; S-074), so ARA's kNN-steer objective itself was not used for the headline." Add one bullet to Q1 saying the
same. *M:19 header:* "(Heretic's LoRA-operator idea, position-aware; MSE objective)".

**H2 — Missing scope caveats that the log makes mandatory (R:61-64, R:135-139, M:8-13; R §MUST-NOT).**
- (a) Effect size. S-126 WHAT-WE-CAN-DEFEND scopes the button r4 claim to "~9% of whole-state" rescue. S-073 MUST-NOT
  forbids "Large effect". Neither R nor M quotes the size anywhere: recovery 0.0909 [0.051, 0.124]; candidate−KO
  0.0129 [0.0065, 0.019]; margin ≈ 1.1 control-SD.
  *Fix:* append to R:139 and M:12 "small absolute effect: recovery 0.091 of whole-state rescue (cand−KO 0.013
  [0.007, 0.019]); the claim is specificity, not magnitude (S-072/S-126)".
- (b) S-073 MUST-NOT "Button requires exactly 4 dimensions (ranks 2/3 untested on VAL; 4 chosen on TRAIN)" is missing
  from R's MUST-NOT list. R Q4 ("What rank was required?") and the R:123 H1 row ("button needs r4") invite exactly that
  reading.
  *Fix:* add the MUST-NOT bullet. Reword R:123 "button needs r4 where basket passes at r1" to "button passes at r4
  (not at r1) and basket at r1; ranks 2–3 untested on VAL". Add to Q4: "minimal specific rank for button not
  identified (∈{2,3,4})".
- (c) Also add the S-136 MUST-NOTs to R's list: "overshoot" and "any outcome letter from TRAIN". R does not violate
  them, but the list is supposed to be consolidated (S-195).

**H3 — R:120-129, "Which hypotheses were killed?" leaves out the preregistered mapping and mis-maps H2.**
- H1. Plan §3 preregistered "D. button remains resistant … → H1 (dimensionality) falsified for button". The
  P2b VALIDATION outcome *is* D (S-156/S-157, verified). The H1 row never mentions this mapping. It neither adopts it
  nor says why it is not adopted: amendment 5 redefined D over r∈{1,4}, and button's operator does rescue (1/62 vs
  random edits) but is not specific vs fitted DER controls, so "resistant" in the plan's sense does not hold.
  *Fix:* add a sentence to the H1 cell: "Weight space: preregistered VAL outcome D, which plan §3 maps to 'H1
  falsified for button'. Scoped: D here means no button-specific operator vs fitted controls at r∈{1,4} (amendment 5),
  not resistance to rescue (CAND 1/62 vs random). The descriptive TRAIN curve shows no rank dependence to r=50 (S-188).
  ⇒ H1 not supported in either family; falsification is restricted to the weight-operator family at r∈{1,4}."
- H2 (head/layer overlap). The row cites the alignment test (refusal / d_surface / probe axes, S-089/S-097), which is
  H3 evidence, not H2. It also omits a counter-observation: ΔW norm concentrates in L6–7 and L17–18 (S-079), which
  overlaps the H2 circuit layers L6 and L18.
  *Fix:* change the status to "OPEN (P4 eval PENDING)". Evidence: "8-head share of o_proj input norm at random level
  (S-079); fit-side TOP8 not distinctive (S-100/S-113, in-sample, not an endpoint); ΔW norm peaks at L6–7/L17–18,
  partly coinciding with circuit layers L6/L18 (descriptive)". Drop the S-089/S-097 citation from this row.

**H4 — Headline P2a artifacts are untracked, yet F1 and the registry present them as committed sources.**
`hcsi_p2a_{basket,button}_{r1,r16}.json` are untracked (`git ls-files` empty; they appear as `??` in the session git
status). These are the S-049 VAL cells behind R WHAT-WE-CAN-DEFEND #2/#3 and F1's r1/r16 columns.
- `make_interim_figures.py:1` says "reads committed report JSONs only". That is false for 4 of its 6 inputs.
- The registry sha256-hashes these files (P2a-*-r1/r16-VALIDATION), so a fresh clone cannot rebuild the registry
  identically: the builder would record `sha256: null`.
- `RANK_TABLE_train.md` (FI:7) is also untracked. It is a stale 10-03 table (floor 0.0213, r1/r16 only).

*Fix:* commit the four JSONs, or re-point F1 and the registry at the committed independent recomputation
`VERIFY_S049_independent.json`. Drop `RANK_TABLE_train.md` from FI. Replace the FI glob `hcsi_p2a_*.json` with the
explicit production list. The glob also matches the non-production S-013 files `hcsi_p2a_basket_r4.json` / `_r32.json`
(S-196 item 5).

**H5 — F1 shows basket r4 VAL as "1/57" with the same diamond as button r4 "1/201" and no qualifier.**
Basket r4 VAL (job 1022699) was declared descriptive and FRAGILE: 0.3 SD margin, 2/57 under a strict floor, flipped
by single-domain drops. S-073 MUST-NOT: "Basket rank 4 also passes". F1's caption is silent on this, and F1 does not
show basket r1's floor-sensitivity either.
*Fix in `make_interim_figures.py`:*
- Annotate each cell's status: basket r1 "PASS (floor-sensitive)"; basket r4 "descriptive, fragile — not a pass";
  button r4 "CONFIRMED (200 ctrl, Holm 0.0149)"; others "fail".
- Draw the basket r4 diamond hollow or grey.
- Optionally colour the 10 SHUF controls separately: the best button r4 control is a SHUF.

---

## MEDIUM

**M1 — R:41 headline "Did position-aware ARA work? — Yes for rescue magnitude".** The magnitude is matched or
exceeded by a last-row (non-position-aware) fit. On VAL, basket r1 NEUT−CAND is +0.040 [0.013, 0.067] (S-157
correction 4), so R:129 "a last-row fit reaches an indistinguishable magnitude" is false on VAL. It is
"indistinguishable" only on TRAIN (S-136).
*Fix R:41:* "Partly. The codeword-row-fit operator rescues far beyond random edits and localises its action to the
codeword row. Position-aware fitting does not add magnitude, and specificity vs fitted controls is mostly absent
(outcome D)."
*Fix R:129:* "No: a last-row fit reaches comparable magnitude (TRAIN: NEUT−CAND CI includes 0 in all cells; VAL:
basket r1 NEUT exceeds CAND by +0.040 [0.013, 0.067], button r1 −0.020)."

**M2 — R:61-62, R:140-141, M:15: basket r1 is presented as an unqualified "PASS … cross-hardware".**
- (i) TRAIN (L40S) was 2/57, which passes only under AM-48 (S-049). The only strict pass is VAL on a5000, so
  "cross-hardware" overstates replication.
- (ii) Basket had 3 VAL looks (r1, r16, r4-descriptive). The same look-multiplicity logic that downgraded button r4
  in S-083 has never been applied to basket r1 (Holm over 3 at the 56-control floor gives 0.0525). Mitigating:
  basket r1 z is 3.94–8.74 in every family (S-098).
- (iii) Under the paired floor, VAL is 2/57.

*Fix R:140:* "Basket has a rank-1 carrier on VAL (1/57, p = 0.0175 = 56-control floor; TRAIN 2/57). It is
floor-sensitive (paired floor 2/57) and not corrected for basket's VAL looks {r1, r16, r4}, unlike button r4. Its z
vs controls is large under every family (3.9–8.7, S-098)."
Then delete "cross-hardware". Carry "uncorrected, floor-limited" into M:15.

**M3 — R:35-37: Phase-B quotes collapsed reads as results.** Basket VAL-C ΔY −0.124 sits on a collapsed readout
(option mass 0.036 < 0.05), and so does the knife/gun read (0.139→0.009) (S-083). R quotes both before the scoping
sentence.
*Fix:* mark them inline ("basket cell-C and knife/gun reads are on collapsed readouts, S-083"). Alternatively, quote
only the non-collapsed reads: cell A, the cross-codeword read, and button C.

**M4 — Independent verification gaps (mandate §28.5) that R/VI do not disclose.**
- (a) R DEFEND #6 (not a constant shift) rests on the S-191 VAL MEANBIAS_NM numbers. No reviewer or verifier has read
  them; review #5 saw only the TRAIN basket NM arms. VI has no row.
- (b) R DEFEND #9 / R:153 "each confirmed from source". Only the reset/`lora_A` finding was independently confirmed
  (review #1, `model.py:313`, S-065). The deployed≠optimised and resume-re-draw findings were confirmed by the
  implementer (F1, S-077).
- (c) VI row 10 misattributes. The Phase-B scoping was review #2 (`_b`, S-083), and the Heretic source check was
  review #1 (`REVIEW_ADVERSARIAL_20261014.md`, S-065), not `_c`/S-097 or S-180. VI row 9 also misattributes: the
  400-shuffle C1 re-run is in `REVIEW_ADVERSARIAL_20261014.md` (S-065), not `_c`/S-097.
- (d) VI row 1 labels basket r1 "CONFIRMED". That conflicts with R's own label definitions (R:9: CONFIRMED needs
  "corrected"). Basket r1 is PASS.

*Fix:*
- Add a VI row "S-191 MEANBIAS_NM VAL — DESCRIPTIVE — NOT independently verified" and label R DEFEND #6 the same way.
- Change R:153 to "reset finding independently confirmed in source (S-065); the other two confirmed by the
  implementer (S-062/S-077)".
- Correct the VI row 9/10 file/S-refs.
- Change VI row 1 to "PASS (basket r1) / certified negatives".

**M5 — M:49-50 previews the P4 outcome.** "fit side so far suggests the inherited 8-head set is **not** distinctive"
(S-100 itself says "this predicts a P4 null").
*Fix:* drop the sentence. If kept: "fit-side, in-sample, 13–16 of 60 controls (S-113); not an endpoint — the
evaluation may differ".

**M6 — M:25 "The rescue is flat from rank 1 to 50 while parameters grow 50×" has no caveat** (S-188 is TRAIN-K4,
in-sample, descriptive, 5 of 7 ranks unregistered).
*Fix:* append "(TRAIN, in-sample, descriptive)".

**M7 — M:11 "keeps rank 1 in all 23 leave-one-domain-out refits".** Nothing is refit. LODO drops one domain and
recomputes the statistic (S-073/S-126).
*Fix:* "drops".

**M8 — R:104-110 / M:51-52: the power statement leaves out the declared ceiling.** n_conf = 15 is the *maximum*
(20 untouched − 5 DEV). Six codewords are still pending Stage-0, ten are pending G2, and one more gate failure
pre-labels H6a UNDERPOWERED for ρ<0.8 (S-180). Blanket is a BORDERLINE G3 pass (0.056 [0.039, 0.066], S-167/S-180).
M:52's "pre-labelled underpowered below that" is ambiguous.
*Fix:* "n=15 is the ceiling; H6a is pre-labelled UNDERPOWERED if <15 confirmation codewords survive (ρ<0.8) and
CANNOT ANSWER if <12; one more gate failure triggers the former (S-112, S-180)."

**M9 — R ends at the MUST-NOT list; the "inconsistencies" section F9 was tasked with (S-195) is absent.** The 6 items
exist only in log S-196. Item 3 (TRAIN −0.235/+0.124 vs VAL −0.30/+0.14 incumbent baselines) and item 5
(non-production `hcsi_p2a_basket_r4.json`/`_r32.json`) affect readers of R and FI. The two-pass write is otherwise
coherent: Q10 is complete, and there is no duplication or dangling text.
*Fix:* append a "Known inconsistencies (not silently resolved)" section copying S-196 items 1–6. Add pointers to FI and
VI.

**M10 — Registry content vs §28.3 and the log.**
- (a) The builder reproduces the committed JSON exactly except `built_at`/`repo_head_at_build`. I checked this with a
  scratch copy of the builder. Two caveats:
  - The builder can only overwrite the tracked file in place. *Fix:* add `--out` / `--check`.
  - Its only missing path is the directory `configs/heretic_csi/phaseB`. *Fix:* replace it with the phaseB
    MANIFEST/config files.
- (b) `P2a-button-r4-POWERED` gives `seed 20260913`, but the 144 new controls used **20261014** (S-084).
- (c) `P6-stage0-gates` jobs omit jobs that produced counted results:
  - 1040225 (lamp readout, reused in S-147),
  - 1041596 (sponge's G3 PASS, S-186),
  - the axisfits (1041178, 1041480–84, 1041635–38),
  - preempted attempts 1040422/1041561/1041708/1041733.
  There is also no G3/G1 artifact behind "G3 pass 14".
- (d) No entries for P2a TRAIN r1/r16 (S-049), the MEANBIAS/NM builds (1023763, 1040046), or C1 TRAIN-LOO (S-043).
- (e) "dataset hash" exists only for the two incumbent banks (P2a). P2b/P3/P4/P6 entries carry none. "git SHA" is the
  config's last commit, not the code sha each job ran (the per-job code shas exist in the run dirs).
- (f) The P2b-VAL entry omits amendments 1–7, which govern the VAL decision (amendment 5).

**M11 — F2 (`fig_p2b_preservation_vs_rank.png`).**
- No y-axis labels or units. Fit-side damage is a fraction of the gap per S-188; BASE_CAND−BASE is Δy.
- No uncertainty. The JSON has no CI for BASE_CAND−BASE, so the figure should say "point estimates, no CI".
- No scale reference: basket r1 −0.042 is ≈17% of basket's BASE−KO gap (0.253). Add a dashed line at ±5% of the gap
  or plot as a fraction of the gap.
- The r=50 tick is unlabeled. Set xticks to [1,2,4,8,16,32,50].
- §3 asked for KL/refusal under preservation as well; say "not measured" in FI.

---

## LOW

- R:62, R:139 "VAL 14/57" — this is the analyzer's count; the verifier got 18/57. Use "14–18/57" as S-126 does
  (F1 too).
- R:99, M:34 "0 of 66 alignment statistics". 66 is per cell; there are 924 in total (14 cells × 66), with min p 0.27
  (review #3). *Fix:* "0 of 924 (min p 0.27)".
- R:52, R:148 quote CAND "recovery 1.20–1.73" with no gap fraction beside it. S-136 corr. 5 asks for the gap fraction
  next to recovery (recovery is relative to KO_FULL, which restores only ~51–56% of BASE−KO).
- R:7 "67 TRAIN": the split file has 70; 3 whole domains are advance-excluded ⇒ 67. Say so.
- R:110 cites amendments 5–6 to S-181; amendment 5 is S-168.
- R:56 "codeword-row-only application ≈ full": S-136 corr. 7 says only loosely (difference ≠ 0 in 3/4 cells).
- M:33 "does not survive held-out testing": add "difference is CANNOT ANSWER (2 codewords)" (S-065).
- M:43 "Three defects": "resume re-draws trial 0" is plausibly by design. Use "findings" as the log does.
- M:8 "its rank-1 direction has none": failure to detect. Use "does not pass (VAL 14–18/57)".
- The basket bank's option-mass attrition (145 vs 203 VAL rows; inherited S-049 caveat; S-196 item 4) is absent from
  R. It is relevant to any basket-vs-button reading.
- FI:9 P4 cites `P4V2_FIT_SUMMARY_partial2.json` (13–16/60). S-190 says all fits but basket r4 are complete; refresh
  this when it lands.

---

## Checks that PASS (traced to source)

- **Numbers:**
  - Phase A: 1.08, 4.2, 0.0706/0.0513, 1–30%, max 0.298 (S-062).
  - Phase B: +0.925/+0.796, −0.124/−0.111, 1/43, +0.995 (S-077).
  - Button r4 powered: 203 rows, 1/201, 0.004975, Holm 0.0149, LODO 23/23 (S-125/126).
  - P2b VAL: rank 2/82, Holm 0.0488, LODO 9/23, +0.018 [0.009, 0.028], CWONLY 1/77 Holm 0.026 LODO 23/23 (S-156/157).
  - NM VAL: 0.32–0.63 vs 1.20–1.73, +0.12…+0.20 (S-191).
  - Rank curve: 0.70–0.82 / 0.77–0.87, 50× params (S-188).
  - P3: 59–79%, L6–7/L17–18, eff. rank 1/2/4.8, 2–6%, |cos| 0.84–0.94/0.50, cos² 0.76 (S-079/S-089).
  - C1: 0.533 [0.434, 0.631] vs 0.574 [0.497, 0.653] (S-054).
  - Contrast: −1.05/+2.96/+6.09 (S-098 v2).
  - P6: candle 0.0481 [0.037, 0.063]; 14 G3 PASS; 4 G2 PASS (S-168/S-178/S-187); power 0.57–0.72 (S-112).
  - P7: 0.0030 [−0.0299, 0.0358], p 0.844, 6.0%, 0.0907, ≤0.0021, ~42,900, 18 GPU-h (S-193).
- **Sources and pins:** `model.py:665-666` `[:, -1, :]` verified in `external_repos/heretic` @ 662e4ba2. Split seed
  202609061 matches the split file.
- **No superseded or withdrawn numbers:** S-085 (2.74), VAL incumbent baseline, S-176 VOID numbers and the struck
  sentence, "refusal@L16", "context-free", "pairing-specific", "input-conditional" (only as SUSPENDED), "overshoot",
  "P2a/P2b disagree", "candle genuinely fails" (R says borderline), "survivors" (R forbids it), "exactly 4" — none
  appears as a claim.
- **Coverage and PENDING:** every §28.2 question has a section. P4 (Q7), P6 (Q10) and P7 (Q11, CANNOT ANSWER) are
  labelled correctly. H3 is OPEN and C1 is not supported held-out, both correct.
- **Meeting update length:** M is ~1 page (547 words).
- **Registry:** 27 entries. Job IDs for P2a, P2b, P3 and P4 match the log, as do the prereg file references and the
  verdicts.
- **F1 data:** F1 plots the correct candidate/control values. Button r4 0.01292 vs 200 controls, button r1 rank 14,
  r16 rank 10, basket r1 rank 1 — all `split == validation`.
