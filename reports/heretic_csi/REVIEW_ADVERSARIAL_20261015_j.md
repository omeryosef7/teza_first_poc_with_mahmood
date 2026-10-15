# Adversarial review #10 (2026-10-15, S-198 .. S-214) -- HERETIC-CSI

Scope: (1) P6 gate numbers and power arithmetic for whistle, yogurt, banana, chair, balloon, ribbon, cushion, curtain, bottle, jacket, sponge;
(2) S-199 reader/prereg and the P4 v2 analyzer (synthetic mutation tests only); (3) the S-206 KNOWN_ZERO addition.
READ-ONLY on results. No SLURM submissions. No P4 score dir, no S-199 arm output, no P4/S-199 log was opened (only directory names of
hcsi_p4v2_* were counted; the GPU-type line of the OLD job 968532 log was read to validate a regex). Scripts: scratchpad rec.py, g2.py, sens.py,
val.py, mut.py, basis2.py (own code; nothing imported from p6_g3/p6_pop/p6_g2 for the recomputes).

## Verdict
No HIGH finding. Every P6 number I could recompute reproduces. The power arithmetic is correct. Both analyzers behave as specified under
mutation. Seven MEDIUM items are pre-declaration gaps to close BEFORE the relevant reads (most urgently the P6 pool-extension rule, before
G2 whistle/chair 1042284 is read).

## 1. P6 recomputation (independent code)
G3 = true median of option_mass over bank rows {semantic_one_word, natural_doublespeak/cell C, n_examples 4, cds_n4_sow} minus the TRAIN
exclusion file (_occ version for bottle/cushion), from the readout results.jsonl; G1 = domain-mean (y_C - y_A), 67 TRAIN domains; G2 from the
four arms of 1042039, exact-tag matched, paired by prompt_id, domain-cluster bootstrap.

| cw | pop/scored | G3 median (mine = recorded) | my G1 C-A [CI] | G1 rule (CI-lo>0.05) |
|---|---|---|---|---|
| whistle | 670/670 | 0.08167 PASS | 0.6656 [0.610,0.721] | PASS |
| yogurt | 670/670 | 0.00964 FAIL | (not gated; 0.471) | n/a |
| banana | 670/670 | 0.01708 FAIL | (not gated; 0.605) | n/a |
| chair | 670/670 | 0.12684 PASS | 0.3643 [0.316,0.413] | PASS |
| balloon | 670/670 | 0.03142 FAIL | (not gated; 0.596) | n/a |
| ribbon | 670/670 | 0.05831 PASS | 0.4489 [0.395,0.503] | PASS |
| cushion | 670/670 | 0.08065 PASS | 0.6027 [0.551,0.653] | PASS |
| curtain | 670/670 | 0.05534 PASS | 0.2446 [0.208,0.284] | PASS |
| bottle | 667/667 | 0.11115 PASS | 0.6510 [0.597,0.703] | PASS |
| jacket | 670/670 | 0.16180 PASS | 0.5874 [0.532,0.643] | PASS |
| sponge | 670/670 | 0.08207 PASS | 0.5301 [0.473,0.587] | PASS |

All G3 medians match to 5 dp; G1 point estimates match to 4 dp (CI endpoints differ at the 3rd decimal: different bootstrap seed; irrelevant,
lowest CI-lo is 0.208 vs threshold 0.05). Populations contain only TRAIN domains, no duplicates, no None option_mass. G2 (cushion, curtain,
bottle, jacket, sponge): KO-BASE -0.357/-0.172/-0.274/-0.116/-0.312 (CI uppers all < 0), KO_FULL-KO +0.192/+0.058/+0.164/+0.070/+0.144
(CI lowers > 0), KO_SELF-KO ~ -0.0005 (CI contains 0 except none excluded), 670/667 paired rows, all four arms of each codeword from job 1042039,
one GPU type (L40S), target_surface == codeword, scored id set == population. All PASS reproduced. The count "14 untouched codewords pass
G1+G2+G3" is correct (lamp kettle pencil ladder blanket bucket pillow saddle wagon cushion curtain bottle jacket sponge).

Ribbon (0.0583): PASS under the frozen rule. Robustness: lower-middle 0.05822 / upper-middle 0.05840 (n=670 is even, so the pooled-tail
upper-middle quirk does not matter); excluding the 0 repair-touched rows changes nothing; the same median is >0.05 under all-splits C (0.0518).
Domain-bootstrap CI [0.0473, 0.0681] straddles 0.05 and the fraction of rows >0.05 is only 54%, so the PASS is real but fragile.
Curtain (0.0553) is equally thin (excl. 10 repair-touched rows 0.0552; still PASS). Blanket (0.0558) passes on the TRAIN population but its
all-splits C median is 0.0489. No gate verdict changes under any variant I tried.

### Findings
M1 (MEDIUM) G3 is a TRAIN-only gate, but the confirmatory outcome z lives on VALIDATION and uses a BASE-referenced option-mass floor 0.05.
  Stage-0 BASE VAL (23 domains) median option mass for gated-in codewords: ribbon 0.0497, blanket 0.0443 (and DEV-dropped candle 0.045); curtain
  0.0689, cushion 0.0582, whistle 0.0717 are above. Roughly half of ribbon/blanket VAL rows fall under the floor (50%/48% above) and will be
  dropped from the recovery statistic, shrinking the domain-level support and the effective n of those codewords' z. Propose (before the draw):
  record per codeword the VAL floor-surviving (domain,slot) count and domains, and pre-declare the minimum (e.g. >=15 of 23 domains with >=1 key) below
  which the codeword's z is "NOT ESTIMABLE" and treated as attrition (stays in the denominator) -- not a post-hoc exclusion.
M2 (MEDIUM, urgent) Pool-extension decision (S-213 OPEN) must be turned into a pre-committed contingent rule BEFORE G2 for whistle/chair
  (1042284, running) and ribbon is read. Otherwise the choice "extend / do not extend" is made after seeing which codewords survive, i.e. it is
  conditional on partial P6 outcomes (gate outcomes are pre-rescue, so permissible, but only if written first). Define now: trigger (n_conf<12
  or <=12), who supplies replacements (a pre-listed ordered list or a seeded draw from a list built without Stage-0 numbers), identical gates
  G1-G3, banks built with the same generator, and what happens to the frozen Zipf tertile table (frozen over 20; replacements change the 7/7/6 split
  and the DEV draw). Also note A2 only licenses redesign when n_conf<12; at exactly 12 the rule says "run, label UNDERPOWERED", so extending at 12
  needs its own amendment.
M3 (MEDIUM) Power arithmetic is right (17 max survivors = 20 untouched - yogurt - banana - balloon; DEV 5 -> 12 max; A2: <12 CANNOT ANSWER, 12-14
  UNDERPOWERED), but (a) S-213's "power ~0.5-0.7 at n=12" is loose: A3's IUT table gives n=12, rho 0.7: 0.43-0.60, rho 0.8: 0.58-0.74 depending
  on shared-noise c, i.e. never >=0.8, so even at n=15 the "UNDERPOWERED for rho<0.8" label does not mean rho=0.8 is adequately powered
  (n=15: 0.73-0.84); (b) the CANNOT-ANSWER test is evaluated at the DEV draw, but A6 allows a codeword to become VOID_RESCUE_PROVENANCE AFTER
  confirmation GPU is spent; at n_conf=12 a single VOID gives n=11 <12 with no pre-declared label. Pre-declare: post-hoc n<12 => "CANNOT ANSWER" label
  for H6a (result still reported descriptively), plus the one allowed re-run of the whole VOID codeword; (c) DEV is a fixed 5 although it is a
  "shakedown only"; DEV size is a design choice that costs H6a power (each DEV codeword removed lowers n_conf by 1). Since survivors are known this is
  an outcome-informed choice; if the parent wants DEV<5 it must be written before the draw and stated as a formula of n_survivors.
M4 (MEDIUM) "TEST never built, never read" (PREREG_P6 splits/test_split) is not literally true: the Stage-0 banks contain TEST-domain rows
  (22272 rows, 116 domains) and every readout scores them; p6_g3.py writes `descriptive_C_dose4_all_splits_median` (includes TEST rows) into every
  manifest. SELF-DISCLOSURE: in this review my val.py printed per-split BASE medians including the 230 TEST rows. These are BASE option masses (no
  intervention, no rescue outcome), no gate used them, but the sentence should read "no TEST rescue outcome and no TEST-based gate is read" and the
  all-splits descriptive should be dropped from the manifest or labelled.
L1 (LOW) A4 re-defined G3 after lamp/candle were scored under the pooled gate (lamp pooled 0.0285 would have FAILED, candle failed either way).
  The A4 text is a fidelity argument for the frozen wording and is internally consistent, but it loosened the gate for an already-seen codeword. Disclose
  as an outcome-aware implementation decision in the final report (it does not change any current verdict except lamp).
L2 (LOW) G1 is computed on all semantic_one_word n4 A/C rows of TRAIN domains (not restricted to the cds_n4_sow block or the exclusion file) and
  with a fixed bootstrap seed 0; fine, but G1/G3 use different row sets. Document. G2 is a weak liveness gate (any significant sign passes): all 14 pass
  by 3-30 CI widths; it screens nothing, and a G2 failure for whistle/chair/ribbon would be surprising.
L3 (LOW) Remaining DEV-draw/H6a design points: cell-stratified DEV removal takes one codeword per Zipf x strength cell, so the 12 remaining
  confirmation codewords have a compressed Zipf/strength range relative to the power table (iid normal x); H6a power is an upper bound.

## 2. S-199 reader and P4 v2 analyzer (synthetic mutation tests, mut.py)
Shas of prereg, reader, basis builder, slurm, p4_analyze_v2, ANALYSIS_COMMANDS, A5, p3p4_emit, p4_head_fit_v2 all match the log. The r1ext basis
(144 controls, indices 46..189 contiguous, unit-norm to 1e-9, candidate byte-identical to the original, max|cos| new-old 0.057, new-vs-candidate
0.047, comparable to the originals' 0.040) is as described.

S-199 decide()/holm(): rank 1,2,3 of 201 -> Holm r1 0.0149/0.0299/0.0448 PASS; rank 4 -> 0.0525 FAIL (matches "<= 3/201"). Ties against the
candidate (rank 2 when one control equals it); a tied SHUF control fails `beats`; no SHUF controls in the dict -> FAIL (not vacuous PASS); missing
one control arm moves p_floor to 1/200 (analyzer's --expect-n-controls 200 is what catches it); rounded/unrounded disagreement ->
"DOES NOT PASS (rounding-sensitive)". No bug. Findings:
M5 (MEDIUM) Row-set shrinkage is only REPORTED, never gated: with a candidate row deviation of 133 -> 90 the verdict is still PASS (tested). The
  200-control common-key set is the intersection over 205 arms, and each rank-1 control already loses 1-6 rows to norm-match refusals (the original
  56 took 145 -> 133). Expect the extended set to shrink noticeably, which changes the candidate statistic, the domain support and the
  comparison with the original 1/57 (rank claims on different rows). Pre-declare now (before 1042049/50 are analysed): (i) a minimum n_keys_common
  and number of domains below which the verdict is "UNDERPOWERED/VOID-ROWSET" instead of PASS/FAIL; (ii) a descriptive companion: the same
  candidate vs the ORIGINAL 56 controls on the shrunken row set, so row-set loss is separated from null-size gain; (iii) per-control paired comparison
  on each control's own rows as a descriptive sensitivity. All declared before the read, none may change the verdict.
L4 (LOW) The Holm family uses r4's p=0.0175 and r16's 0.1754 "as recorded" from the 56-control nulls while r1 uses 201; mixed null sizes. This is
  conservative for r1 and pre-declared, fine. Confirm no other basket VALIDATION look exists (r2/r8/r32 VAL): the untracked hcsi_p2a_basket_r32/_r4 files
  are TRAIN (n_keys 14); no VAL reads found for other ranks. Keep that statement in the S-199 result.
L5 (LOW) The r1ext basis and hcsi_ranksweep_basket.pt/.json are untracked in git (they are sha-pinned in the prereg, which matches; commit them or
  a manifest so a clean clone can verify).

P4 v2 analyzer: finalize()/valid()/decide() under mutation: Holm on p_IUT PASS only at rank 1/61 in BOTH families at one rank; (1/61,1/61) and
(1/61, 3/61) -> both PASS (0.0328/0.0492); (2/61,2/61) -> FAIL (0.0656); IUT with NC at 2/61 FAIL; CI-lo<=0 FAIL; VOID, degenerate recovery,
missing rank, or gate failure on either primary rank -> the other rank INCOMPLETE FAMILY (no "PASS" substring); strict Holm-4 can never reach 0.05.
rank_p counts ties against the candidate. strict_run_dir is anchored and raises on 0 or >1 qualifying dirs. No multiplicity or logic error found.
The nominal size of the decisive rule is about (1/61)^2 per rank, i.e. extremely conservative; a PASS is essentially unreachable unless TOP8 is
first of 61 in both families.
M6 (MEDIUM) Collapsed CONTROLS stay in the primary p. A control whose readout collapses (median option mass < floor) is only a flag; its stat is
  then far below TOP8's, so TOP8 "beats" it for free and the primary p is biased DOWN (anti-conservative); the without-collapsed variant is
  reported, not decisive, and has a larger p. Propose a pre-run amendment: primary p counts every collapsed control as >= candidate (never as a
  free win), or equivalently use the larger of p and p_without_collapsed, and VOID if >10% of a family collapses.
M7 (MEDIUM) Verdict strings for the TRAIN-K4 split read "PASS (Holm p=...)" with no split label, while the prereg says a TRAIN-K4 pass is in-sample/
  weak and only a VALIDATION read counts. Add an in-sample prefix to verdicts when --split train and make the log wording "TRAIN-K4 (in-sample) PASS"
  (output labelling only; no rule change). Likewise, a button PASS must be labelled secondary-transfer; no cross-codeword correction exists and
  none is pre-declared, so the report must state basket VAL Holm-over-{1,4} is the sole confirmatory test and button is descriptive.
L6 (LOW) `except SystemExit` maps any strict_run_dir failure (including >1 DONE dir after an accidental re-run, i.e. duplicate evidence) to
  "NOT ANALYZABLE", which then turns the other rank into INCOMPLETE: a data-integrity stop can read like a null in a log. Label as "NOT ANALYZABLE (data
  integrity, not a null)". Other exceptions (KeyError in rf[x][k], torch load) crash the whole script without writing rows; wrap per rank.
L7 (LOW) Single-job/GPU VOID passes vacuously if RUNMETA lacks `gpu` or `slurm_job_id` (set {None}); require non-None (current P2b/P4 RUNMETA
  files do record both). KO_IDENT threshold 1e-9 is exact-bit; false VOID is possible on non-deterministic kernels (conservative).

## 3. KNOWN_ZERO (S-206)
Entry hcsi_p2a_basket_KO_20261002_202100_4049577: verified legitimate. DONE.json status INCOMPLETE, rows_written 0, n_rows_failed 670,
failure reason "NotImplementedError: ScopedAttentionKnockout supports batch size 1 only" x670, wall 47 s, gens.jsonl and results.jsonl empty;
11 other hcsi_p2a_basket_KO_2026100x/1013 run dirs exist (the batch-size-1 reruns). The entry is keyed by run id only (other zero-row runs are
still caught), nothing deleted, 30 tests in tests/test_run_completeness_check.py pass, and the P2a analyzers key on job id + DONE rows so this dir
cannot be selected. Two nits: (a) the code comment cites "S-205" but the log entry is S-206; (b) it is unexplained why the guard did not fire in the
13 days since 10-02 (results.jsonl has an Oct 3 08:59 mtime; commits since then evidently ran with the same check) -- worth one line in the log, but
not a validity problem.

## Priority actions
1. Before G2 1042284 (whistle/chair) is read: commit the contingent pool-extension rule (M2) and the post-draw VOID/n<12 labelling (M3b).
2. Before any S-199 analysis run: commit the row-set floor and companion analyses (M5).
3. Before the first P4 VALIDATION read: commit the collapsed-control and split-label amendments (M6, M7) -- the TRAIN-K4 basket r1 read is already
   running, so apply M6 as a pre-declared "reported-conservative" variant if the amendment cannot precede it, and say so.
4. Fix the manifest/prereg TEST wording (M4) and record per-codeword VAL floor support (M1).
