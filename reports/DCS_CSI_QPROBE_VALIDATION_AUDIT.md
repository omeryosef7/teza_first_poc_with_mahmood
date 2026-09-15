# DCS-CSI P0.3 -- audit of the query-side probe's VALIDATION number

Status: **SETTLED.** Verdict = **(b) coincidence**, demonstrated by a full-precision re-run on
SLURM (job 896358, node n-303, 2026-09-15T17:06-17:28). The basket validation figure **may be
cited as independent validation**, with one caveat recorded at the end.

---

## 1. The question

`scripts/dcs_cont_qprobe.py` fits a LOO-by-domain ridge on TRAIN over a (site, layer) grid, takes
the TRAIN argmax, and reports a VALIDATION transfer at that fixed cell via `transfer()`. Its two
outputs looked structurally different:

| codeword | report | `train_best.rho_loo` | `validation_best.rho` |
|---|---|---|---|
| button | `reports/DCS_CONT_QPROBE.json` | 0.5935 (rel-6, L20) | 0.6450 |
| basket | `reports/DCS_CONT_QPROBE_basket.json` | 0.6525 (rel-6, L18) | **0.6525** |

The basket validation rho is byte-identical at 4 dp to its own train rho, and identical to
`grid_train_rho["rel-6"]["L18"]`. A "validation" number equal to the train number is exactly the
shape of a bug where the validation path silently re-reads the training population, so the figure
was frozen pending an explanation. Three candidate explanations:

* **(a)** a real bug -- the validation path reads TRAIN rows;
* **(b)** a coincidence -- two genuinely different computations rounding to the same 4 dp;
* **(c)** degenerate population -- the basket corpus has no validation rows, so `build(VA, ...)`
  returns something empty or aliased.

The reported `validation_best {slots: 230, domains: 23}` argued against (c), but that field is
itself produced by the code under suspicion, so it could not be used to clear the code.

## 2. Evidence 1 -- the split and the corpora, read from row metadata only

Read from `data/boombness_prompts/dcs_ts116_domain_split.json` plus each corpus's
`results.jsonl` (no `multiposition_reps.pt` load):

* Manifest: 70 train / 23 validation / 23 test domains. `EXCLUDED_DOMAINS` removes 3 train
  domains, giving **|TRAIN| = 67, |VALIDATION| = 23, |TEST| = 23**.
* **TRAIN &cap; VALIDATION = {} ; TRAIN &cap; TEST = {} ; VALIDATION &cap; TEST = {}.**
* basket corpus `cont1_behavioral_basket_bomb_20260910_113902_3966018`: 3714 rows, 93 domains --
  67 TRAIN domains / 2680 rows, 23 VALIDATION domains / 920 rows, **0 TEST rows**, 3 excluded
  domains present but dropped.
* button corpus `cont1_behavioral_button_bomb_20260910_152806_272296`: 3720 rows, 93 domains --
  same 67/2680 and 23/920 split, 0 TEST rows.
* prompt_id intersection between the TRAIN-domain rows and the VALIDATION-domain rows: **0**, in
  both corpora.

So explanation **(c) is dead**: the basket corpus carries a real, non-empty, disjoint validation
population of exactly 920 rows -> 230 four-cell slots over 23 domains, which is what the JSON
says.

## 3. Evidence 2 -- the decisive re-run at full precision

`scripts/dcs_csi_qprobe_valaudit.py` replays qprobe's own `build` / `loo` / transfer kernels
verbatim for both codewords at the cell each report names, and prints `repr(float)` with no
rounding. Submitted as
`sbatch --export=ALL,DCS_CMD="python scripts/dcs_csi_qprobe_valaudit.py" slurm_scripts/dcs_cont_cpu.slurm`
-> job **896358**, log `outputs/boombness/logs/dcs_cpu_896358.out`, rc=0.

```
[split] |TRAIN|=67 |VALIDATION|=23 |TEST|=23
[split] TR&VA=[]  TR&TE=[]  VA&TE=[]

[button] bank: corpus=dcd92d723f3e6d00 readout=dcd92d723f3e6d00 agree=True
[button] TRAIN  population: 670 slots / 67 domains / 2680 prompt_ids
[button] VALID  population: 230 slots / 23 domains /  920 prompt_ids
[button] key intersection TRAIN&VALID = 0   prompt_id intersection = 0
[button] y hashes: train 3181293756349780593  valid 8569926635833071849
[button] TRAIN  rho_loo      = 0.5934700332983854   (round4=0.5935)
[button] VALID  transfer rho = 0.6450094807413964   (round4=0.6450)
[button] identical bits? False   |diff| = 0.05153944744301098
[button] F5 TRAIN rho_loo = 0.6241297239584491 ; F5 VALID transfer = 0.678431005106532
[button] SENSITIVITY: refit on 33/67 TRAIN domains -> VALID rho = 0.6226472597082052

[basket] bank: corpus=79511d9e254571e6 readout=79511d9e254571e6 agree=True
[basket] TRAIN  population: 670 slots / 67 domains / 2680 prompt_ids
[basket] VALID  population: 230 slots / 23 domains /  920 prompt_ids
[basket] key intersection TRAIN&VALID = 0   prompt_id intersection = 0
[basket] y hashes: train -7716577294458622527  valid 1976538211533650931
[basket] TRAIN  rho_loo      = 0.6524545477487157   (round4=0.6525)
[basket] VALID  transfer rho = 0.6525210881770593   (round4=0.6525)
[basket] identical bits? False   |diff| = 6.654042834364216e-05
[basket] F5 TRAIN rho_loo = 0.6336014952404444 ; F5 VALID transfer = 0.6807438621754172
[basket] SENSITIVITY: refit on 33/67 TRAIN domains -> VALID rho = 0.6468854100143259
```

### Full-precision numbers, both codewords

| codeword | cell | TRAIN rho_loo | VALIDATION transfer rho | |diff| |
|---|---|---|---|---|
| button | rel-6, L20 | 0.5934700332983854 | 0.6450094807413964 | 5.15e-02 |
| basket | rel-6, L18 | 0.6524545477487157 | 0.6525210881770593 | **6.654e-05** |

F5 incumbent, same two paths: button 0.6241297239584491 (TRAIN) vs 0.678431005106532 (VAL);
basket 0.6336014952404444 (TRAIN) vs 0.6807438621754172 (VAL).

## 4. Verdict: (b), a coincidence

The two basket numbers are **different floats** -- they differ in the fifth decimal place
(6.65e-05), and round to the same 4 dp only because the difference is below the printed
precision. The re-run reproduces both published 4-dp figures exactly, so the JSON was computed by
the code, not copied.

Four further facts rule out (a):

1. The two populations are structurally disjoint: 0 shared (domain, slot) keys and 0 shared
   prompt_ids between what `build(TR, ...)` and `build(VA, ...)` actually return; their target
   vectors have different hashes and different lengths (670 vs 230).
2. A leak would be systematic, not codeword-specific. The identical `transfer()` code path gives
   a 0.0515 train/validation gap on button and a 0.0471 gap for F5 on basket
   (0.6336 -> 0.6807). Only this one cell collides.
3. The validation number moves when the fit moves: refitting on half the TRAIN domains (33/67)
   changes the basket validation rho from 0.6525 to 0.6469 and the button one from 0.6450 to
   0.6226. A validation path that re-read TRAIN would be insensitive to the fit sample in this
   way only by accident; in the degenerate-aliasing case it would instead track the TRAIN LOO
   number.
4. Bank identity holds on both pairs (corpus sha == readout sha), so no cross-codeword pooling is
   in play.

The collision is unsurprising in size: the basket TRAIN grid at rel-6 is a flat plateau
(L16 0.6417, L18 0.6525, L20 0.6512, L22 0.6386), and the validation transfer lands inside that
same plateau band. Two values drawn from a ~0.64-0.65 band colliding at 4 dp is a ~1-in-a-few-
hundred event, not a 1-in-10000 one.

## 5. The hardening patch (applied)

`scripts/dcs_cont_qprobe.py`, additive only, in the file's existing `print("REFUSING: ...")` +
nonzero-return style. Two blocks:

* **Split-level guard**, immediately after `TR` / `VA` / new `TE` are constructed and before any
  data is loaded: refuses if TRAIN is empty, VALIDATION is empty, TRAIN &cap; VALIDATION is
  non-empty, TRAIN &cap; TEST is non-empty, or VALIDATION &cap; TEST is non-empty.
* **Population-level guard**, after `build` is defined and before the TRAIN grid runs: a
  `_built_keys(keep)` helper enumerates exactly what `build` would return -- same `keep` filter,
  same reps-presence test, same `(domain, family_slot) x cell` key, same 4-cell completeness rule
  -- but reads **no** `[site, layer]` slice, so it costs no tensor I/O. It prints the two
  populations and refuses if either is empty, if they share any `(domain, slot)` key, or if they
  share any `prompt_id`.

Every one of these raises (returns 2 from `main`, which the module turns into `SystemExit(2)`).
None warns, and none substitutes a default. Nothing else in the file was changed; no frozen
result is affected, because on the current data all six conditions pass.

## 6. Citability

**`reports/DCS_CONT_QPROBE_basket.json`'s `validation_best.rho = 0.6525` MAY be cited as an
independent, held-out validation transfer.** It is computed on 230 slots over 23 validation
domains that share no domain, no (domain, slot) key and no prompt_id with the 670-slot / 67-domain
TRAIN fit population, at the (site, layer) selected on TRAIN without retuning.

Two caveats that are NOT leakage but must travel with the number:

* It should be quoted at higher precision, or with the gap stated, so it is not mistaken for the
  train figure: **0.65252** (validation) vs **0.65245** (train LOO). The near-equality is
  arithmetic coincidence on a flat plateau, not evidence of anything.
* The honest reading of rel-6 remains the one already in the JSON's `notes_from_review`: rel-6
  sits on a flat plateau (rel-4..rel-14), the winner's TRAIN argmax is a selection over 162 grid
  cells, and the quoted `train_best_perm_p` is a single-cell upper bound, not family-wise.

## 7. Artifacts

* re-run script: `scripts/dcs_csi_qprobe_valaudit.py`
* SLURM log: `outputs/boombness/logs/dcs_cpu_896358.out` (job 896358, rc=0)
* patched: `scripts/dcs_cont_qprobe.py` (assertions only)
* TEST data was not read at any point; both corpora were verified to contain 0 test-split rows.
