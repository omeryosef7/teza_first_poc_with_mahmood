# BUGHUNT — committed OUTPUT artifacts (wrong numbers, not wrong code)

Scope: every `summary.json` and every loose `outputs/*.json` under
`/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood/doublespeak_causality/outputs/`
(539 JSON files, 400 run dirs), plus every number that appears in BOTH a file under `reports/` and a
committed JSON. Method: `scripts/validate_all_outputs.py outputs/*/` for the summary↔raw reconciliation,
then four independent sweeps written for this audit (rate-range, CI-containment, sibling-`n` agreement,
constant-across-cells) and a hand cross-check of the report tables against their source JSON.

No script was modified, no job launched, nothing committed. No generation text, prompt text, codeword or
harmful-word value was read; `gens.jsonl` was never opened.

**Headline:** 17 findings. The four that change a number a reader would cite are
**O1** (a committed dose-response verdict that is the opposite of its own data),
**O2** (14 stale cells in the α-calibration report that flip a "below the judge noise floor" call),
**O3** (the claim-audit table pointing the flagship n=242 result at an empty run dir), and
**O4** (four wrong ranges, one with the wrong sign, in PHASE_WRITE_REFUSAL_INTX).

---

## Part 1 — triage of every non-`ok` dir from `validate_all_outputs.py`

```
400 dir(s): 0 ok, 108 warn, 283 SKIP-legacy (no raw.jsonl), 9 FAIL;
19521 summary values recomputed, 3 mismatched
```

### 1.1 The 9 FAILs

| dir | validator verdict | triage |
|---|---|---|
| `phase9_dose_curated_L9_20260803_173754_704861` | `by_split.heldout.monotone_decreasing: summary=False recomputed=True` | **REAL DATA DEFECT** → O1 |
| `phase9_dose_curated_L9_10_11_20260803_173754_704862` | same at `dev` **and** `heldout` | **REAL DATA DEFECT** → O1 |
| `phase4_edgeKO_clearharm_20260806_125131_726211` | `base_p_concept` and `base_proj_random` cover different sids; a specificity would mix axes | **REAL DATA DEFECT** (the known −0.89 cross-axis bug, still on disk) → O5 |
| `phase4_edgeKO_curated_20260803_065114_703282` | `raw.jsonl` EMPTY (0 rows) but `summary.json` exists | **ABORTED RUN**, summary is self-describing (`n_valid: 0`, `top_heads: []`) → O13 |
| `phase6_mlpKO_curated_query_window_20260803_094515_703460` | `raw.jsonl` EMPTY (0 rows) but `summary.json` exists | **ABORTED RUN**, self-describing (`n_rows: 0`, `skips: {dev:no_ds_query_pos: 2, heldout:…: 2}`) → O13 |
| `behav_refusal_clearharm_a1.0_20260804_125311_708038` | `summary.json` MISSING (run-dir contract §2.1) | **ABORTED/PARTIAL**, but it is registered as `br_twin` in `build_claim_audit.py:88` → O14 |
| `behav_refusal_clearharm_asweep0.0-…-0.25_20260806_082819_724551` | `summary.json` MISSING | aborted restart (untracked); superseded by `…_111104_725172` |
| `behav_refusal_generated_asweep0.0-…-0.25_20260806_095711_724930` | `summary.json` MISSING | aborted, 0-byte `raw.jsonl`/`gens.jsonl` (untracked) |
| `behav_refusal_generated_asweep0.0-…-0.25_20260806_135052_727984` | `summary.json` MISSING | **in-flight at audit time** (84 KB raw written 13:53, no DONE) — not a defect, but it is indistinguishable from an abort in the artifact tree |

### 1.2 The 108 WARNs — reason breakdown

| count | reason | triage |
|---|---|---|
| **111** | `no manifest under configs/manifests (plan §P0 requires one per phase)` | **schema the validator cannot check** → **O12: the manifest check is dead code project-wide** |
| 4 + 2 | `only 1 split present: ['train'] / ['dev']` | legitimate smoke runs |
| 2 | `legacy plan metadata: n_harmless_fit=20 is the SOURCE list size…` | known, already in `SELF_REVIEW_2026-08-06.md` D3 |
| 2 | `benign_p_concept absent from raw.jsonl` | schema the validator cannot recompute (decision-form phase4 rows) |
| 1 | `no necessity cell (C3/C3_*) in raw.jsonl` | schema, sufficiency-only run |

So **every WARN except 11 is the same single missing-manifest warning**, and no WARN is a data defect.

### 1.3 The 283 `SKIP-legacy`

`.gitignore:11-20` commits `summary.json` / `RUNMETA.json` / `DONE.json` and **excludes `raw.jsonl`**
(`git ls-files outputs/ | grep -c raw.jsonl` → **0**). The 283 skips are dirs whose local `raw.jsonl`
has since been archived/deleted. **Consequence worth stating plainly:** on a fresh clone
`validate_all_outputs.py` can reconcile **zero** dirs — the reconciliation guarantee holds only on this
working tree, and only for the 117 dirs that still have raw locally. That is a repository-level
reproducibility property, not a per-dir defect, but it means "0 ok, 3 mismatched out of 19521" is a
statement about one machine.

---

## Part 2 — findings

### O1 — [HIGH] `phase9_dose` curated summaries ship a `monotone_decreasing` verdict that is the opposite of their own curve

**Where.** `outputs/phase9_dose_curated_L9_20260803_173754_704861/summary.json`
(`by_split.heldout.monotone_decreasing`) and
`outputs/phase9_dose_curated_L9_10_11_20260803_173754_704862/summary.json`
(`by_split.dev.monotone_decreasing` **and** `by_split.heldout.monotone_decreasing`). Both are git-tracked.

**Stored vs recomputed.**

| dir | cell | stored | recomputed (current definition) | the curve over α∈[0,1] |
|---|---|---|---|---|
| `…704861` | heldout | `false` | **`true`** | .6902 .6448 .6191 .5880 .5750 |
| `…704862` | dev | `false` | **`true`** | .8105 .7981 .7647 .7265 .7089 |
| `…704862` | heldout | `false` | **`true`** | .6902 .6447 .6211 .5872 .5830 |

**Why it is wrong.** `scripts/phase9_dose.py:126` now computes the verdict over `alphas <= 1.0` only
(`# audit: [0,1] only, not alpha>1 extrapolation`). That line arrived in commit **19dba9a1**
("phase9 monotonicity [0,1] only"). The committed `summary.json` files are dated **Aug 3 17:40**, i.e.
they were produced by the *previous* definition, which included α=1.5 and α=2.0 — where the curated
curves tick back up (heldout .5674→.5872) and turn the verdict false. **The artifacts were never
regenerated after the definition changed.** The stored boolean now answers a question the code no longer
asks.

**Failure scenario.** A reader (or `build_claim_audit.py`, which registers `p9_cu` =
`…704861` at line 99) opens the machine-readable artifact for the Phase-9 gate and reads
`monotone_decreasing: false` → concludes the graded-lever criterion FAILED on curated. Meanwhile
`reports/PHASE9_DOSE.md` line 34 asserts the exact opposite in bold: *"Monotone decreasing over α∈[0,1]
on all 4 cells, both cohorts, both splits"*. The report is right about the data; the committed artifact
contradicts it. Whichever one a downstream consumer reads first decides whether Phase 9 passed.

**Severity: HIGH** — a stale boolean that inverts a pass/fail gate, in the file the claim audit reads.

**Fix.** Re-run the aggregation-only tail of `phase9_dose.py` against the existing `raw.jsonl`
(no GPU needed — both raws are present, 18 rows each), or delete the stale field. Do not hand-edit.

---

### O2 — [HIGH] `PHASE8_1_ALPHA_CALIBRATION.md` §2 side-by-side table: all 14 clearharm cells are stale n=78 numbers, and one of them flips a stated conclusion

**Where.** `reports/PHASE8_1_ALPHA_CALIBRATION.md`, section *"2. `Î` tracks `I_max`"*, the
"Side by side, pooled" table — the two **clearharm** columns. Source of truth:
`outputs/alpha_calibration.json` → `cohorts.clearharm.splits.pooled.<α>.{I_max, binary.Ihat}`.

| α | report `I_max` | JSON `I_max` | report `Î_bin` | JSON `Î_bin` |
|---|---|---|---|---|
| 0.0 | +0.654 | **+0.6512** | +0.000 ‡ | +0.0000 ✓ |
| 0.25 | +0.487 | **+0.4767** | −0.013 ‡ | **−0.0233** |
| 0.5 | +0.282 | **+0.2907** | −0.103 | **−0.0814** |
| 0.75 | +0.231 | **+0.1860** | −0.128 | **−0.1744** |
| 1.0 | +0.231 | **+0.1860** | −0.154 | **−0.2093** |
| 1.5 | +0.141 | **+0.1047** | −0.205 | **−0.2558** |
| 2.0 | +0.051 | **+0.0233** | −0.269 | **−0.3140** |

**13 of 14 cells are wrong.** The curated column is correct throughout; only clearharm is stale.

**Why it is wrong.** The report's own header note says the n=78→86 refresh moved
"`I_max` at α=0.25 … +0.487→**+0.4767** and at α=1.0 +0.231→**+0.1860**" — and then the table twelve
lines below still prints **+0.487** and **+0.231**. The auto-generated "Full tables" section further down
(`#### clearharm / pooled (n=86)`) prints the *correct* +0.477 / +0.186. So the document contradicts
itself twice over, and the hand-written table is the one a reader hits first.

**Failure scenario (this one changes a claim).** The bullet immediately above the table states:
*"Specifically **clearharm α = 0.25 gives `Î_binary` = −0.013 (1.3 pp) — below the floor**"*, and the
table marks that cell ‡ ("at or below the ~2 pp judge noise floor"). The committed value is
**−0.0233 = 2.3 pp, i.e. ABOVE the 2 pp floor the same report defines**. The single sentence that
converts the operating-point interaction estimate from "measurable but null" to "not even measurable"
rests on a superseded number. The ‡ mark on that row is wrong for the same reason.

Three further stale quantities in the same report, same cause:

- §1 bullet 3: *"The score-change rate on clearharm (**6.4 %**)"* — the table 10 lines above it, and
  `alpha_calibration.json → cohorts.clearharm.judge_noise_floor.score_change_rate`, both say
  **0.05814 = 5.8 %** (5/86).
- §"Specificity holds…": *"At every α > 0 the gap is **+0.179 to +0.641**"* — recomputed pooled range over
  α>0 across both cohorts is **+0.186 to +0.663** (`specificity.delta_ASR_refabl_minus_randabl`);
  no split/cohort combination in the committed JSON produces 0.179 or 0.641. The derived "**32×** the
  noise floor" inherits it (0.641/0.02 = 32; the correct figure is 33).
- Same paragraph: *"`refusal_rate` … **0.846–0.872** against **0.846** (clearharm)"* — committed
  `direct_randabl.refusal_rate` pooled spans **0.860–0.884** against a `direct_base` baseline of
  **0.860**. (The curated half of that sentence, 0.667–0.725 vs 0.686, is correct.)

**Severity: HIGH** — the α-calibration report is the document that withdrew P8.0; its §2 is the argument,
and §2's numbers are pre-refresh.

**Fix.** Regenerate §2 from `alpha_calibration.json` rather than by hand, and re-evaluate the ‡ marks and
the "below the floor" sentence against −0.0233.

---

### O3 — [HIGH] `CLAIM_AUDIT_TABLE.md` points the flagship n=242 result at an empty run dir, and still calls it PENDING

**Where.** `scripts/build_claim_audit.py:112` maps
`"p8_v3_ch" → "outputs/behav_refusal_clearharm_asweep0.25_20260806_035033_720724"`, consumed by claim
**P1b-06** (`build_claim_audit.py:731-733`), rendered at `reports/CLAIM_AUDIT_TABLE.md:103`, `:178`,
`:333`, `:390`.

**Stored vs actual.**

| | `…035033_720724` (cited) | `…051610_721956` (actual) |
|---|---|---|
| contents | `RUNMETA.json` **only** | `RUNMETA`, `DONE`, `summary.json`, `raw.jsonl` (127 rows), `gens.jsonl` |
| git-tracked | **no** | yes (RUNMETA + DONE + summary) |
| cited by | `build_claim_audit.py`, `CLAIM_AUDIT_TABLE.md` | `outputs/p8_clearharm_v3.json → run_dir`, `reports/P8_INTERACTION_V3.md §8` |

**Why it is wrong.** Job 720724 produced no data; the clearharm v3 cohort was re-run as 721956, and
`outputs/p8_clearharm_v3.json` records `run_dir = …_051610_721956`, `n_rows_used = 127`. The claim-audit
mapping was never repointed. The audit's own provenance table (`CLAIM_AUDIT_TABLE.md:390`) records
`| behav_refusal_clearharm_asweep0.25_20260806_035033_720724 | yes | RUNMETA | — | SKIP-legacy — 0 values
recomputed, 0 mismatched |` — it *green-lights* a directory with no data, because "SKIP-legacy" is not a
failure state. Row `:103` shows the row count as `—` for clearharm while showing `(115r)` for generated,
so the emptiness is visible in the output and was not acted on.

**Failure scenario.** The claim table exists precisely so a reviewer can trace the headline
"no interaction, `Î` = −0.054, n = 242" to the run that produced it. Following the pointer lands on an
empty directory. Worse, P1b-06's status is still **⏳ PENDING** with the note *"Jobs 720724 / 720725
RUNNING at the time of this audit"*, while `reports/P8_INTERACTION_V3.md` line 3 declares the same result
**✅ COMPLETE**. Anyone reconciling the two documents concludes the flagship P8 result is unfinished.
The exit code contract ("non-zero if … any cited run dir has vanished") does not catch this because the
dir exists — it is merely empty.

**Severity: HIGH** — the governance artifact is wrong about the project's headline negative result.

**Fix.** Repoint `p8_v3_ch` to `…_051610_721956`, promote P1b-06 out of PENDING, and make
`build_claim_audit.py` treat "cited dir has no `summary.json`/`raw.jsonl`" as a hard failure rather than
`SKIP-legacy`.

---

### O4 — [HIGH] `PHASE_WRITE_REFUSAL_INTX.md`: all four reported ranges are wrong, and one has the wrong sign

**Where.** `reports/PHASE_WRITE_REFUSAL_INTX.md`, the main results table
("refusal `frac_of_direct_gap_restored` (range over layers)"). Source:
`outputs/write_refusal_intx_{clearharm_20260804_231656_711887,curated_20260804_232905_711888}/summary.json`
→ `by_split.<split>.per_layer.<L>.frac_of_direct_gap_restored` (32 layers per cell).

| cohort·split | report range | recomputed min…max (arg) |
|---|---|---|
| clearharm train | −0.017 … +0.004 | **−0.023 (L28) … +0.015 (L12)** |
| clearharm test | −0.013 … +0.015 | **−0.017 (L30) … +0.025 (L16)** |
| curated train | −0.048 … **−0.016** | **−0.050 (L18) … +0.011 (L12)** |
| curated test | −0.010 … +0.004 | **−0.010 (L32) … +0.019 (L15)** |

**Why it is wrong.** The reported endpoints are not the min/max — they are arbitrary interior layers
(e.g. clearharm train's "−0.017" is L27's value while L28 is −0.023; "+0.004" is L17/L21's while L12 is
+0.015). The **curated train row is qualitatively wrong**: it reports an interval that is entirely
negative (max −0.016) when the true range straddles zero (L11 = +0.003, L12 = +0.011). Every one of the
four rows understates the spread.

The accompanying claim *"At **every layer in every cell**, `frac_restored ≈ 0` (|value| < 0.05)"* is also
false as written: curated train L18 is exactly **−0.050**, so the strict inequality fails at that layer.

**Failure scenario.** The report's conclusion is "write-ablation leaves refusal suppression completely
intact" and its evidence is that the restored fraction never departs from 0. A reader who checks the
committed JSON finds a 47 % larger spread than reported and a curated-train interval whose sign was
misstated — which is exactly the kind of discrepancy that reads as a tuned quotation rather than a
reported range, even though the qualitative conclusion (all |values| ≤ 0.05) survives.

Everything else in this report reconciles exactly: the positive-control values (`.884→.799`, `.858→.817`,
`.811→.751`, `.690→.457`) and the worked example (`clearharm test hs32: direct 65.5165, ds_base 27.5239,
ds_writeabl 27.3282`) all match `summary.json` to the digit.

**Severity: HIGH** (report-level; the artifact is correct, the write-up is not).

**Fix.** Emit the range from the JSON instead of by hand; restate the claim as `|value| ≤ 0.05`.

---

### O5 — [HIGH] The −0.89 cross-axis constant is still on disk in `phase4_edgeKO_clearharm_…_726211/summary.json`

**Where.** `outputs/phase4_edgeKO_clearharm_20260806_125131_726211/summary.json` (untracked; the only
`p4ko` dir the validator FAILs). `phase4_edge_knockout.py:236-240` documents this exact bug in a comment.

**Stored values, and what they actually are:**

| cell | `mean_delta_refusal` | `mean_delta_random` | `specificity` | `specificity_ci95` |
|---|---|---|---|---|
| `edge_KO` | **+0.00082** | **−0.88928** | **+0.89010** | [−0.7398, +3.2310] |
| `rand_edge` | +0.01941 | **−0.89828** | +0.91769 | [−0.7491, +3.3114] |
| `all_query_edges` | +0.04884 | **−0.93632** | +0.98516 | [−0.4488, +3.2465] |

**Recomputed from `raw.jsonl` (12 rows, 4 items):** the rows carry **no `base_proj_random` field at all**.
`mean_delta_random` is therefore `mean(proj_random) − mean(base_p_concept)` — a *random*-axis reading
minus a *refusal*-axis baseline. mean(base_p_concept) = **1.0111**; mean(proj_random) per cell =
0.1218 / 0.1128 / 0.0748. Their differences reproduce −0.88928 / −0.89828 / −0.93632 **exactly**. It is a
fixed axis offset, identical to ~1 pp across three interventions that share nothing but the offset.

**Why it is wrong / severity.** This is the failure mode the task brief names, and it also trips the
"specificity larger than the effect it is derived from" test in the most extreme form available:
`specificity` = **+0.890** while the refusal-axis effect it is supposedly cleaning is **+0.00082** —
**1085×** larger than the quantity it modifies. Three cells that differ by an order of magnitude in
`mean_delta_refusal` (0.0008 / 0.019 / 0.049) all report near-identical "specificity" ≈ 0.89–0.99, because
the specificity is essentially the constant. The current script raises `SystemExit` rather than emit this
(`phase4_edge_knockout.py:308-310`), so it can only be a pre-fix artifact.

**Failure scenario.** The dir is not git-tracked, so it is not a *committed* defect — but it sits in
`outputs/` alongside the clean reruns `…_726616` (same 4 items, `specificity` = **−0.00036**, a
2500× difference) and `…_727983` / `…_728189` (n = 86). Anything that globs `outputs/phase4_edgeKO_*`
— including `validate_all_outputs.py outputs/*/`, which is how this was found — picks it up. A reader who
sorts by timestamp and takes the first clearharm decision-form run gets a specificity of +0.89 for a
knockout whose real effect is −0.003. `reports/PHASE3_ATTENTION_CAUSALITY_TARGETED.md:165-169` documents
the bug correctly, which makes the surviving artifact the only remaining hazard.

**Fix.** Delete `…_726211/` (and `…_726616/`, the smoke that replaced it) or move them under an
`outputs/_retracted/` prefix that the glob does not reach.

---

### O6 — [MEDIUM] `REP_PREDICTS_BEHAVIOR.md` retracts a CV number and then re-asserts it 8 lines later, and mis-indexes a layer it warns about mis-indexing

**Where.** `reports/REP_PREDICTS_BEHAVIOR.md`, sections *"Robustness — RECOMPUTED 2026-08-06"* and
*"Robustness (audit)"*. Source: `outputs/rep_predicts_behavior_sweep.json`.

1. **The retracted number is still asserted as fact.** The upper section says, in bold:
   *"⚠️ The cross-validation figure does NOT reproduce. The previously quoted `5-fold CV AUC =
   0.887 ± 0.106` is not recoverable … A deterministic stratified 5-fold (seed 0) gives **0.869 ± 0.055**
   … **Cite that number, not the original.**"* The very next section then states:
   *"and **5-fold cross-validated AUC = 0.887 ± 0.106** (out-of-sample logistic regression on the single
   projection feature), matching/exceeding the in-sample value."* Committed JSON:
   `cohorts.clearharm.cv_auc_at_headline_layer = {mean: 0.8693, sd: 0.055, folds: [0.8961, 0.7792,
   0.8636, 0.9242, 0.8833]}`. There is no 0.887 and no 0.106 anywhere in `outputs/`.
   **Failure scenario:** the paragraph that survives into a paper draft is whichever one the writer
   copies; the retracted figure is the more favourable one and is the one phrased as a positive result.
2. **Off-by-one on the layer index, in the one report that warns about it.** The same section says
   *"only the early **L13** is weaker at **0.69**"*. JSON: decoder **L12** = 0.6916; decoder **L13** =
   **0.7731**. 0.69 is the hs-13 row, i.e. decoder L12 under the report's own stated convention
   ("hs `h` = decoder layer `h−1`", stated 12 lines earlier and flagged "because it is easy to get wrong").
3. **Out-of-range layer.** Same sentence: *"stable 0.84–0.89 across **L17–L32**"*. Decoder layers run
   0–31; there is no L32. The correct statement, and the one the section above it makes, is L17–L31,
   0.844–0.884.

Everything else in this report reconciles exactly: L21 AUC 0.8744, `mw_p` 3.8247e-09, `r` −0.5837;
curated 0.4205 / 0.7919 / +0.0146; the 11-layer P7 table (0.773 / 0.819 / 0.876 / 0.888 / 0.884 / 0.882 /
0.881 / 0.879 / 0.857 / 0.856 / 0.850); "20 of 32 Holm-significant"; curated "0/32, 0.364–0.605".

**Severity: MEDIUM.** **Fix:** delete the stale "Robustness (audit)" paragraph outright — every number in
it is superseded by the section above it.

---

### O7 — [MEDIUM] `PHASE8_READOUT.md` claims the readout "grows monotonically"; the committed arrays are not monotone anywhere

**Where.** `reports/PHASE8_READOUT.md`, first result bullet. Source:
`outputs/phase8_readout/{clearharm,curated}.json → by_split.<split>.ds_proj_concept` (32 values each).

**Claim:** *"The linear concept projection **grows monotonically** and peaks at the LAST layer (L31) on all
cells."*

**Recomputed.** No cell is monotone, and curated heldout is not close:

- curated heldout: … L21 **+0.091** → L22 +0.095 → L23 +0.012 → L25 −0.060 → **L26 −0.297** → L27 −0.268
  → L29 −0.130 → L30 +0.035 → **L31 +0.449**. The series drops 0.39 below its L22 value before the final
  jump.
- clearharm dev: L15 +0.025 → **L16 −0.146** → L17 −0.099 → L18 +0.061 (a 0.17 excursion mid-stack).
- curated dev: L24 +0.132 → **L26 −0.189** → L27 −0.142 → L31 +0.766.

The four tabulated cells (`ds_proj_at_L9/L14/L21`, `frac_of_max_by_L9/L14`, onset, peak) all match the JSON
to the digit — only the monotonicity sentence is unsupported.

**Failure scenario.** The sentence is load-bearing for the report's mechanism story ("the residual
*accumulating* the concept toward the unembedding"). What the committed arrays actually show is a flat/
oscillating trace with a single last-layer spike: `onset_layer_50pct == peak_layer == 31` in **all four
cells**, i.e. nothing reaches 50 % of max before the max — the "emergence curve" is one jump at L31
(clearharm dev L30 = 0.424 → L31 = 1.272). "Accumulation" and "one final-layer spike" are different
claims, and the artifact supports the second.

**Severity: MEDIUM.** **Fix:** replace "grows monotonically" with the actual shape, and note that
onset==peak makes the onset column uninformative by construction.

---

### O8 — [MEDIUM] α-sweep monotonicity: 6 non-monotone `ASR(direct_refabl)` steps, 5 of them well above the ~2 pp judge floor

Task item 3. Source: `outputs/alpha_calibration.json`, `outputs/p8_lowalpha_clearharm.json`
(`p8_{clearharm,generated}_v3.json` and `p8_v3_combined.json` are single-α and cannot be checked).

| file | cohort · split | step | ASR | Δ | vs 2 pp floor |
|---|---|---|---|---|---|
| `alpha_calibration.json` | curated · train | 0.75 → 1.0 | .7333 → .6333 | **−10.00 pp** | **5.0×** |
| `alpha_calibration.json` | curated · test | 1.5 → 2.0 | .6667 → .5714 | **−9.52 pp** | **4.8×** |
| `p8_lowalpha_clearharm.json` | · test | 0.15 → 0.20 | .2800 → .2000 | **−8.00 pp** | **4.0×** |
| `alpha_calibration.json` | curated · pooled | 1.5 → 2.0 | .6863 → .6275 | **−5.88 pp** | **2.9×** |
| `alpha_calibration.json` | clearharm · test | 0.75 → 1.0 | .5952 → .5476 | **−4.76 pp** | **2.4×** |
| `alpha_calibration.json` | curated · test | 1.0 → 1.5 | .7143 → .6667 | −4.76 pp | 2.4× |
| `alpha_calibration.json` | curated · train | 1.5 → 2.0 | .7000 → .6667 | −3.33 pp | 1.7× (**at/under floor**) |

Clearharm **pooled** is weakly monotone throughout (0.75 and 1.0 are exactly tied at .5814), and
clearharm **train** is strictly monotone. So the dose-response is clean on the cohort the operating point
was selected on, and ragged on curated and on the low-α subsample.

**Failure scenario.** `PHASE8_1_ALPHA_CALIBRATION.md` uses α-monotonicity implicitly when it argues the
dose grid is well-behaved ("the dose response is too steep — `ASR(0,1)` jumps from 0.294 at α = 0 straight
to 0.529 at α = 0.25, stepping clean over the band"). On curated the same grid also steps *backwards* by
10 pp between α = 0.75 and α = 1.0 on train — five times the report's own noise floor. That is not
mentioned anywhere, and it undermines the "landing in the band would need roughly α ≈ 0.1" extrapolation,
which assumes a monotone curve.

**Severity: MEDIUM** — no stored number is wrong; the omission is.

---

### O9 — [MEDIUM] `refusal_rate` is exactly `0.000` across the entire curated Doublespeak arm — 8 arms × 51 items × 7 α, in two independent harnesses

Task item 2 ("ASR/refusal rates that are exactly 0 or exactly 1 across a whole arm").

**Where.** `outputs/alpha_calibration.json` → `cohorts.curated.splits.{train,test,pooled}.<α>.arms.
{ds_base,ds_refabl}.refusal_rate` = **0.0 in all 42 cells**. Reproduced in the raw:
`behav_refusal_curated_asweep…_716015/raw.jsonl` gives `{False: 51}` for `ds_base_refused` and for every
one of the seven `ds_refabl_a<α>_refused` fields — **408 rows, zero refusals**. Same cohort,
`direct_base_refused` = `{True: 35, False: 16}`.

Independently: `outputs/refusal_traj_curated_20260805_061151_711957/summary.json` →
`by_split.{train,test}.ds_refused_rate` = **0.0** (and `ds_refused` trajectories are `null` at all 40
token positions, with `ds_complied` byte-identical to `ds_all`).

**Why it is suspicious rather than clearly wrong.** Both harnesses key on the same
`REFUSAL_MARKERS` keyword list (`phase_behav_refusal.py:60-63`), so agreement between them is not
independent evidence. On the clearharm cohort the identical detector fires on 40/86 DS generations, so it
is not globally dead. But: curated `ds_base` ASR = 0.275 with refusal = 0.000 leaves **72.5 % of items in
an unreported third bucket** (neither jailbroken nor refused), whereas curated `direct_base` sums to
exactly 1.000 (ASR 0.314 + refusal 0.686). The field therefore means something different in the two arms
of the same table.

**Failure scenario.** `reports/PHASE_REFUSAL_TRAJECTORY.md` and `REP_PREDICTS_BEHAVIOR.md` both build a
mechanism claim directly on this constant — *"curated DS has `ds_refused_rate = 0.000` — zero of its
generations refuse (uniform suppression)"* → "the limiting factor on curated must be a **second
mechanism**, concept-dilution". If the 0.000 is instead the keyword list failing on codeword-substituted
outputs (which are, by construction, *about a different noun*), the "two sources of partial ASR" result
loses one of its two legs. Nothing in `outputs/` distinguishes the two readings, because the third bucket
is never counted.

**Severity: MEDIUM** — a metric that is a hard constant across an entire arm should not be quoted as an
effect without a counter-check.

**Fix (cheap, no GPU).** Emit `n_empty` and `n_other` alongside ASR/refusal so the buckets sum to n;
spot-check the 37 curated non-malicious non-refused rows with a second refusal detector. Until then, quote
"0/51 keyword refusals" rather than "refusal is fully off".

---

### O10 — [MEDIUM] `outputs/p8_v3_combined.json` — the n=242 headline artifact has no reproducible provenance

**Where.** `outputs/p8_v3_combined.json`, `cohorts.v3_combined` (git-tracked via the `!outputs/*.json`
rule).

**Stored:**

```
run_dir       = /tmp/claude-.../6441812b-.../scratchpad/comb     <- session-scoped temp dir
refusal_pt    = null      model = null      slurm_job_id = null
judge_noise_floor = null  ceiling_tracking = {train: null, test: null, pooled: null}
```

Sibling cohorts (`p8_clearharm_v3.json`, `p8_generated_v3.json`, `alpha_calibration.json`) all carry a
real `outputs/…` run dir, a `refusal_pt` path, a model id and a job id.

**Why it is wrong.** This is the file behind `P8_INTERACTION_V3.md`'s entire §2 headline
(`Î` = −0.054, CI [−0.124, +0.017], p = 0.172, n = 242) — every one of which I confirmed correct against
this file. But `raw.jsonl` is never committed (§1.3), and the *only* recorded location of the concatenated
raw is a scratchpad path that no longer exists and never could be shared. The two contributing raws
(`…721956`, `…720725`) are also uncommitted. So on a clean clone the project's headline negative result is
**unreproducible and unauditable** — `validate_all_outputs.py` cannot reach it, and `build_claim_audit.py`
does not list it among its `D[...]` dirs at all.

I did verify the disjointness claim from `P8_INTERACTION_V3.md §8` on this machine: 127 + 115 rows,
127 + 115 distinct ids, **overlap 0**, 242 distinct total; splits 85/42 and 77/38 → 162/80. That matches
the report exactly. The point is that nobody else can check it.

**Severity: MEDIUM.** **Fix:** rebuild the combined analysis with `--out` pointing at a real
`outputs/p8_v3_combined/` run dir, and record `source_run_dirs: [721956, 720725]` in the JSON.

---

### O11 — [MEDIUM] `outputs/p8_lowalpha_clearharm.json` is a committed orphan that contradicts two published conclusions

**Where.** `outputs/p8_lowalpha_clearharm.json` (git-tracked). Cited by **zero** files under `reports/`
and by **zero** entries in `build_claim_audit.py` (`grep -rn "lowalpha\|v3low\|725172" reports/ scripts/`
→ no hits).

Three things it contains that the published record says otherwise about:

1. **The ceiling signature reverses sign.** `PHASE8_1_ALPHA_CALIBRATION.md` §2 rests on
   *"`Î` tracks `I_max` … Spearman **+0.991** (clearharm, n=86)"* — which I confirmed exactly against
   `alpha_calibration.json → cohorts.clearharm.ceiling_tracking.pooled.binary.spearman_rho = 0.9910`.
   The low-α file, same model, same cohort family, gives
   `cohorts.clearharm_v3low.ceiling_tracking.pooled.binary.spearman_rho = **−0.3676**`
   (pearson −0.4173; test split −0.1312 / −0.3395). **Opposite sign.**
2. **α = 0.25 is verdicted differently.** `P8_INTERACTION_V3.md §7` states in bold that
   *"α = 0.25 qualifies on **neither** v3 cohort … clearharm lands at `ASR(0,1)` = **0.402** (outside by
   0.002)"*. This file's `selection.candidates` records α = 0.25 with `ASR_direct_refabl = **0.400**`,
   `in_band = **true**`, `qualifies = **true**` — and selects **α = 0.05** as the operating point
   (`selected_alpha: "0.05"`, `n_qualifying: 5`).
3. **The sample is a head-of-file subsample, not a random one.** `RUNMETA.argv` shows `--n 25`, so n = 50
   is `items[:25]` of each split of the same v3 clearharm bench that elsewhere gives n = 127 (85/42). The
   split proportion differs too (50/50 vs 67/33).

**Failure scenario.** A committed, tracked, machine-readable file selects a *different* operating point
(0.05) from the one the paper uses (0.25), verdicts the paper's dose as in-band when the paper says it is
out, and reverses the correlation the P8.0 withdrawal argument is built on — with no report anywhere
reconciling any of it. A reviewer who greps `outputs/` for the α selection finds two answers.

**Severity: MEDIUM** (would be HIGH if it were cited; the danger is that it is committed and silent).

**Fix.** Either write it up (the sign reversal at low α is a real qualification of the ceiling argument
and deserves a paragraph) or move it out of `outputs/`.

---

### O12 — [MEDIUM] The validator's strongest check never runs: `configs/manifests/` contains one file, for a phase that was never launched

**Where.** `scripts/validate_all_outputs.py:16` — *"if `configs/manifests/<phase>.json` exists, asserts
every expected cell / arm / split is present and **FAILS on a missing one**"*. `--manifest-dir` defaults
to `configs/manifests` (`:1185`).

**Actual contents of `configs/manifests/`:** exactly one file, `phase9_gcg_mac_matrix.json`, whose own
header reads `"status": "FROZEN-SPEC / NOT LAUNCHED"`. Its stem (`phase9_gcg_mac_matrix`) matches none of
the 14 phase tags the validator detects (`behav`, `p4b`, `p4c`, `p4ko`, `p5b`, `p7`, `p7b`, `p7c`, `p7d`,
`p9`, `phase5`, `phase6`, `refval`, `None`).

**Consequence.** The warning `no manifest under configs/manifests` fires **111 times** — it is 111 of the
119 warnings emitted across the whole sweep. Step 5 of the validator has therefore **never fired on any
real run**, which means the one check designed to catch a *missing* cell (as opposed to a wrong number) is
inert project-wide.

**Failure scenario.** A phase silently drops an arm — e.g. a `--destinations` value that yields no query
positions, or a cohort whose split has zero valid items — and every downstream check still passes: the
summary reconciles against the raw (both are missing the cell), the deletion-detector only compares
*sibling* nodes that exist, and the manifest check that would have caught it never runs. This is not
hypothetical: `phase6_mlpKO_curated_query_window_…_703460` records
`skips: {dev:no_ds_query_pos: 2, heldout:no_ds_query_pos: 2}` and produced a summary with zero windows,
and only the *empty-raw* rule caught it.

**Severity: MEDIUM.** **Fix:** write one manifest per live phase, or make "no manifest" a FAIL for phases
that have a report, so the gap is visible rather than warned-about 111 times.

---

### O13 — [LOW] Two committed `summary.json` files describe runs with zero rows

`outputs/phase4_edgeKO_curated_20260803_065114_703282/summary.json` (`n_valid: 0`, `top_heads: []`,
`n_sig_heads: 0`) and `outputs/phase6_mlpKO_curated_query_window_20260803_094515_703460/summary.json`
(`n_rows: 0`, `by_split.{dev,heldout}.windows: {}`). Both are git-tracked, both carry a `DONE.json`, and
both have a 0-byte `raw.jsonl`.

**Triage: aborted run, not a data defect.** Both summaries are honestly self-describing — no number in
either can mislead, because there are no numbers. The defect is contract-level: `DONE.json` marks a run
that produced nothing as done, so "has DONE" cannot be used as a completeness signal. Note the good runs
that replaced them (`…_703335`, `…_703460`'s layer-granularity sibling) are also present, so the reader
has to know which is which by timestamp.

**Severity: LOW.** **Fix:** have the harness refuse to write `DONE.json` when `n_rows == 0`.

---

### O14 — [LOW] `br_twin` is a claim-audit input with no `summary.json`

`outputs/behav_refusal_clearharm_a1.0_20260804_125311_708038/` has `DONE.json` + `RUNMETA.json` (both
tracked) and a local `raw.jsonl` (untracked, 43 KB) but **no `summary.json`** — the only committed dir in
the sweep that violates run-dir contract §2.1 that way. It is wired into `build_claim_audit.py:88` as
`"br_twin"` and used by two claims (`:610` the P8.0 §5.3b judge-replicate, `:1033` the data-integrity
claim, whose `recompute` line literally runs `validate_all_outputs.py` on it — which FAILs).

**Failure scenario.** The byte-identical-replicate claim ("the judge returns different verdicts on
identical text") is sourced to a run whose only committed artifact is metadata; on a clean clone there is
nothing to recompute, and on this tree the recompute command the audit prints returns FAIL.

**Severity: LOW** (the claim itself is corroborated by `alpha_calibration.json`'s `judge_noise_floor`
block, which is committed and reconciles). **Fix:** generate the missing summary from the local raw before
it is archived.

---

### O15 — [LOW] `d7_defense_…_698953`: the defense-only arm is byte-identical to baseline at both doses

`outputs/d7_defense_Llama-3.1-8B-Instruct_20260801_044852_698953/d7_summary.json`:
`results.alpha_1.labels.defonly_a1` = `{REJECTED: 9, BENIGN: 21}` and `results.alpha_2.labels.defonly_a2`
= `{REJECTED: 9, BENIGN: 21}` — both exactly equal to the run's own `baseline_labels`
`{REJECTED: 9, BENIGN: 21}`. Consequently `benign_refusal_defonly` = `benign_refusal_baseline` = 0.3 and
`benign_over_refusal` = `{delta: 0.0, lo: 0.0, hi: 0.0, excl0: false}` — a degenerate zero-width CI.

The attack arm *did* move (`attack_def_malicious` 0.6667 vs `attack_malicious` 0.4667) and
`degeneration_length_frac.defonly` differs between the two α (0.633 vs 0.6), so the hook fired and the
generations did change — the labels simply did not. Plausible, but "defense at L7–13 changes zero benign
labels at two different strengths" is the signature one would also see if the defense-only arm reused
baseline generations.

**Severity: LOW** — flagged for a spot-check, not asserted as a bug. The sibling runs (`697454`, `697705`,
defense at L24–30) show `benign_refusal_defonly` 0.533–0.733, i.e. large movement, so the null is specific
to the early-layer configuration.

---

### O16 — [LOW] A z-score computed on float noise, in an all-zero cell flagged `sd_usable_for_z: true`

`outputs/pair_causal_controls_693705.json` →
`control_distribution["None|early|1.0|random_token"]`: the cell's control `sd` is **3.87e-06** and every
`concept_arms.<arm>.effect` is **0.0**, yet `sd_usable_for_z` is `true` and all **five** arms
(`add_d_DS`, `add_d_Direct`, `add_d_benign`, `add_d_repeated`, `add_d_unrelated`) report the identical
`z_vs_controls = **−0.129**`. Five interventions that share nothing but the arithmetic produce one
number — the same shape as O5, but three orders of magnitude smaller and correctly guarded
(`materially_nonzero: false`, `exceeds_all_controls: false`).

**Severity: LOW** (guarded). **Fix:** gate `sd_usable_for_z` on an absolute floor, not just non-zero.

---

### O17 — [LOW] `REP_PREDICTS_BEHAVIOR.md`'s headline table has four numbers with no committed source

The headline table quotes DS-projection medians **−1.15 / +3.60** (clearharm) and **+0.28 / −0.49**
(curated), and the text quotes projection spreads **std 1.84 vs 3.51**. None appear in
`outputs/rep_predicts_behavior_sweep.json` (which stores only `auc`, `mw_p`, `r`, `mw_p_holm` per layer)
or in `refproj_*/summary.json`. `scripts/analyze_rep_predicts_behavior.py` computes a median only for a
plot annotation (`:180`) and does not serialize it.

The report itself declares this class of number UNVERIFIED for the *robustness* section
("previously quoted but emitted by no committed code path, claim `RP-03`") — but the headline table's
medians and the std figures were never brought under the same rule. The AUC / p / r columns of that same
row **do** reconcile exactly (0.8744, 3.8247e-09, −0.5837 / 0.4205, 0.7919, +0.0146).

**Severity: LOW.** **Fix:** have `--sweep` also emit per-outcome median and sd, or drop the columns.

---

## Part 3 — checks that came back clean (so the negative result is on record)

| check | result |
|---|---|
| Rates outside [0,1] (`ASR`, `refusal_rate`, `p_concept`, `auc`, `acc`, …) across 539 JSONs | **none**. All 117 raw hits were counters (`n_frac`, `n_saturated…`) or legitimately signed quantities (`direct_frac`, `frac_of_direct_gap_restored`, `frac_of_max_by_L*`). |
| CI that does not contain its own point estimate | **none**, over 252 matched `ci`/`ci95`/`specificity_ci95`/`specific_ci`/`delta_CI` pairs. No inverted `[lo, hi]` either. |
| `n` disagreeing between sibling fields | **none**. Every `splits.<split>.<α>.n` equals every `arms.*.n` beneath it; `train + test == pooled == n_rows_used` in all five α-files (86 = 44+42, 51 = 30+21, 127 = 85+42, 115 = 77+38, 242 = 162+80, 50 = 25+25). |
| P8 v3 id disjointness (`P8_INTERACTION_V3.md §8` claim) | **verified**: 127 + 115 rows, 242 distinct ids, overlap 0. |
| `P8_INTERACTION_V3.md` vs `p8_*_v3.json` / `p8_v3_combined.json` | **every number matches**: §2 (all 21 cells), §4 (8 cells), §5 (9 cells), §6 (8 cells), §7 (`sat_by_one` 0.624), the derived pp deltas (+9.5, −9.6, +4.7, −15.6, +19.4) and Spearman(`I_max`,`Î`) = +0.800 over the 4 cells. |
| `PHASE4_DEMO_RETRIEVAL.md` vs `phase3_demoKO_*` / `phase4_edgeKO_*_7033*` | **every number matches** (necessity 6 cells + CIs, C1 readouts .882/.761, sufficiency ranges, band table both cohorts). |
| `PHASE9_DOSE.md` curve tables vs `phase9_dose_*` | **every number matches** (16 α-points + 8 drops); only the `monotone_decreasing` *field* disagrees → O1. |
| `PHASE8_READOUT.md` numeric table vs `phase8_readout/*.json` | **all 12 cells match**; only the monotonicity sentence fails → O7. |
| `PHASE_REFUSAL_TRAJECTORY.md` vs `refusal_traj_*` | **every number matches** (13.578→13.6, 9.145→9.1, −2.148→−2.1, rate 0.452→0.45, curated −2.638→−2.6, `ds_refused_rate` 0.000). |
| `PHASE_WRITE_REFUSAL_INTX.md` positive controls + worked example | **match exactly**; only the four ranges fail → O4. |
| `REP_PREDICTS_BEHAVIOR.md` sweep section vs `rep_predicts_behavior_sweep.json` | 11-layer table, L21 reference, 20/32 Holm, curated 0/32 and 0.364–0.605, CV 0.869±0.055 — **all match**; only the stale paragraph fails → O6. |
| "Constant masquerading as an effect" sweep (identical float across ≥3 sibling cells) | 1 real hit (**O5**), 1 guarded hit (**O16**); all others were counters, α-independent baselines, or 1e-5 rounding floors. |
| Duplicate SLURM-job-id dirs (24 job ids own 2–5 dirs) | benign: in every case checked the extra dirs are `RUNMETA`-only restart stubs (`717879`, `717880`, `724931`, `725172`, `708038`) or per-concept siblings of one array job (`694882-4`, `694895-7`). |

---

## Ranked fix list

1. **O1** — regenerate the two `phase9_dose_curated` summaries from their existing raws (aggregation-only, no GPU). A committed gate verdict is currently inverted.
2. **O3** — repoint `build_claim_audit.py:112` at `…_051610_721956`, clear P1b-06's PENDING status, and make an empty cited dir a hard failure instead of `SKIP-legacy`.
3. **O2** — regenerate `PHASE8_1_ALPHA_CALIBRATION.md` §2 from `alpha_calibration.json`; re-evaluate the ‡ marks and the "α=0.25 is below the floor" sentence against `Î` = −0.0233.
4. **O4** — recompute the four ranges in `PHASE_WRITE_REFUSAL_INTX.md` from `per_layer`; fix the curated-train sign and the `<0.05` → `≤0.05`.
5. **O5** — remove `phase4_edgeKO_clearharm_…_726211/` (and `…_726616/`) from the `outputs/*` glob.
6. **O6 / O7** — delete the superseded "Robustness (audit)" paragraph; restate the PHASE8 readout shape.
7. **O10 / O11** — give `p8_v3_combined.json` a real run dir; write up or retire `p8_lowalpha_clearharm.json` (its ceiling Spearman is **−0.368** where the published figure is **+0.991**).
8. **O9** — emit `n_other`/`n_empty` so the curated DS arm's buckets sum to n before quoting "refusal is fully off".
9. **O12** — one manifest per live phase, or make the absence a FAIL.
10. **O8, O13–O17** — noted; none blocks a claim on its own.
