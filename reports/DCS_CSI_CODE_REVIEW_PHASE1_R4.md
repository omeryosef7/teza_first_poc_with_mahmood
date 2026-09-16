# DCS-CSI Phase-1 adversarial code review — ROUND 4

Scope, part 1: the `--rescue-rel-end-rows` block in `src/boombness/score_behavior.py`, the
`--force-layer` path in `scripts/dcs_csi_axis.py`, and groups E/F/G/H/I/J of
`slurm_scripts/dcs_csi_p1_arms.slurm`.
Scope, part 2: an independent recomputation of the sprint's headline numbers
(S-054/S-058, S-059, S-063, S-069, S-070, S-071, S-072) from the raw `results.jsonl` files, with my
own domain-mean + paired domain bootstrap — `dcs_csi_subspace_analyze.py` and
`dcs_csi_rederive_patch.py` were not used, imported or consulted for any number below.

**Bottom line on the science: every load-bearing number in the position map and the position ladder
reproduces, most of them to the last published digit.** `rel −10` is the codeword `' button'` in the
semantic prompt and `rel −11` in the behavioural one; there is no off-by-one; the 16 position arms
each restored exactly one position and are all on one 670-key set with `KO_FULL`; `KO_POS28` and
`KO_FULL` are distinct run directories with byte-identical output on both splits. I also found an
end-to-end cross-validation the sprint has not run — the ladder's `KO_POS1` arm and the named-position
arms agree on **401/401 shared rows to 0.000e+00** — which independently confirms the rel_end
arithmetic.

**Bottom line on the code: one BLOCKER, live right now.** Groups F and I both consume `$5`, and the
group-I half-selector is being read as a *layer override*. Jobs **897569** and **897570** are running
as I write this with `--rescue-layer 1` and `--rescue-layer 2` instead of basket's L18.

Scratch scripts (deleted after the run): `lib.py`, `e1.py`–`e9.py`.

---

## BLOCKER

### B1. Group I's `$5` half-selector is silently consumed as the LAYER override — jobs 897569 / 897570 are running the basket controls at **L1 and L2** instead of L18
`slurm_scripts/dcs_csi_p1_arms.slurm:59` (`LAYER="${5:-}"`, before the group dispatch) vs `:140`
(`if [ "${5:-1}" = "1" ]`), with `:83` (`R="--rescue-positions query --rescue-layer $LAYER ..."`).

`$5` is read as the layer override **unconditionally, for every group**, at line 59. Group I (added
in S-074 to split the 24-arm request into two halves after the 30-minute pending-rule breach) then
re-uses the *same* positional argument as its half selector. Passing `1` or `2` therefore does both
things at once.

*Verified on the live jobs.* `outputs/boombness/logs/csi_p1_897569.out` line 1 and
`csi_p1_897570.out` line 1:

```
[layer-override] using L1 instead of the axis artifact's selected layer
HOST=n-301 JOB=897569 CW=basket SPLIT=train GROUP=I LAYER=1 RANK=3 EXPECT_N=670
[layer-override] using L2 instead of the axis artifact's selected layer
HOST=n-301 JOB=897570 CW=basket SPLIT=train GROUP=I LAYER=2 RANK=3 EXPECT_N=670
```

and the `config.json` the two running arms already wrote:

```
csi1_basket_train_KO_RAND6_20260916_063527_78314   rescue_layer = 1    basis ctrl_random6
csi1_basket_train_KO_RAND12_20260916_063527_78315  rescue_layer = 2    basis ctrl_random12
```

against `configs/dcs_csi_axis_basket_behavioral.json` → `selected_layer = 18`, and against the six
already-complete basket controls (`KO_RAND0..5`), every one of which recorded `rescue_layer = 18`.

*Consequence.* Because these are **subspace** arms, the R1-M2/R3 layer-mismatch refusal in
`score_behavior.py:2044` will fire — but only *after* the 8 B weights are loaded (the basis loader
is lazy, R1-m6), and `set -euo pipefail` then kills the whole job on arm 1. So the outcome is two
allocations burned for zero rows and the S-071 INCONCLUSIVE left unresolved. **The dangerous
version is the silent one:** groups D, E, F, G and H pass no `--rescue-basis`, so nothing checks
their layer at all. `sbatch dcs_csi_p1_arms.slurm button axis.pt train H 1` would run the entire
position map at **L1** and record `rescue_layer: 1` in rows that look completely healthy.

Note this is the review's recurring shape at the launcher level: the `[layer-override]` line *did*
print the truth, into a log nobody read until the arms had been pending and running for 21 minutes.

*Fix, in order.*
1. `scancel 897569 897570` now.
2. Move group I's half selector to `$6`, or give it a named variable
   (`HALF="${GROUP_ARG:-1}"`), and make the layer override refuse when `GROUP` is not `F`:
   `if [ -n "${5:-}" ] && [ "$GROUP" != "F" ]; then echo "REFUSING: \$5 is the layer override and is only meaningful for group F"; exit 2; fi`
3. Refuse a layer outside the axis artifact's `layer_grid` regardless of group — L1 and L2 are not
   in `[16,18,20,22,24,26,28,30,31]` and could have been rejected in the shell before the GPU was
   touched.
4. Update the usage header and `GROUP="${4:?A|B|C|D|E|F}"`, which still lists only A–F while
   G, H, I and J exist.

---

## MAJOR

### M2. The position map and the position ladder have **no committed analysis code and no persisted artifact**. Every number in S-059, S-063, S-066, S-067, S-069 and S-072 exists only as prose in the append-only log
`grep -rln 'KO_AT\|KO_POS' scripts/ src/ tests/ reports/` returns **exactly one file**:
`slurm_scripts/dcs_csi_p1_arms.slurm`. There is no `reports/DCS_CSI_POSITION_MAP*.json`, no
`DCS_CSI_LADDER*.json`, and no script that reads a `KO_AT*` run directory.

Everything the Phase-1 *subspace* claims go through — `strict_run_dir`'s anchored resolver (the
S-042 fix), the cross-arm `(domain, slot)` intersection, the arm-identity table, the liveness VOIDs,
the norm-match VOID, the gate block, `n_keys_common`, `allow_short` — is bypassed for what S-072
calls *"the sprint's most defensible mechanistic claim"*. The map's key set, its VOIDs, its
`n_rescue_positions` agreement and its `rescue_fired` counts were never written down anywhere a
reader can check them.

*I checked them, and they all pass* (see CHECKED AND FOUND CORRECT). That is the point: the claims
are **true and unreproducible from the repo**. A reader handed S-072 has no path from the log to the
numbers, and the next person to touch the position arms has no resolver, no gate and no key-set
record to inherit.

*Fix:* add a `--position-map` mode to `dcs_csi_subspace_analyze.py` (or a small sibling) that takes
`BASE, KO, KO_FULL` plus a list of `KO_AT*` arms, resolves them with `strict_run_dir`, intersects the
keys, VOIDs on `n_rescue_positions != 1` / `rescue_fired < n_rows` / disagreeing
`rescue_rel_end_rows`, and writes `reports/DCS_CSI_POSITION_MAP_<codeword>_<split>.json` carrying
`n_keys_common`, `n_domains`, every point + CI, the `% of KO_FULL` denominator, and the sum. Then
cite the artifact from S-072 rather than the table.

### M3. S-072's *"The 12 unmeasured carry ≈ 7.6 %"* does not reproduce — it is `100 % − 92.4 %`, i.e. the additivity assumption the 92.4 % figure is being used to *support*; the direct estimate has the opposite sign
`external_md/…_20260915.md` S-072, the line under the token table, and the bullet
*"It is **complete**: the measured positions account for 92.4 % of the quantity being explained, so
nothing large is hiding in the unmeasured remainder."*

The 92.4 % is a fact about the **16 measured** positions. It says nothing about the other 12 unless
single-position effects add exactly, and "roughly additive" is itself inferred (S-069, point 1)
*from* the sum being ≈ 100 %. As written the sentence is circular.

It is also testable, and the sprint already owns the data: `KO_POS1` draws one position per row with
`random.Random(f"{prompt_id}|1")`, which I reproduced exactly (see the 401/401 check below), so every
`KO_POS1` row can be labelled with the `rel` it restored. Partitioning its 670 rows:

```
                       mean single-position recovery      implied group total   % of KO_FULL
measured-16 rels  (401 rows) +0.00483 [+0.00285,+0.00686]   x16 = +0.07727        109.5 %
UNMEASURED-12 rels(269 rows) -0.00058 [-0.00183,+0.00059]   x12 = -0.00691         -9.8 %
all 28            (670 rows) +0.00281 [+0.00158,+0.00407]   x28 = +0.07875        111.5 %
        (domain-clustered bootstrap, 67 domains, 20 000 resamples)
```

The direct estimate of the unmeasured remainder is **−9.8 %**, not **+7.6 %**; its CI
[−31 %, +10 %] contains 7.6 % but is centred on the wrong side of zero. The same arithmetic says the
sum over **all 28** single positions point-estimates to **111.5 %** of `KO_FULL`, i.e. mildly
**super**-additive, not "roughly additive".

*What survives:* the scientific conclusion ("nothing large hides in the unmeasured 12") is
supported — by the −0.00058 per-position estimate above, and by the fact that the 12 unmeasured
tokens are boilerplate function words (`' does'`, `' what'`, `' above'`, `' text'`, `' the'`,
`' In'`, `' else'`, `' nothing'`, `' and'`, `' word'`, `' exactly'`, `' with'`) bracketed by
measured neighbours at `−12`, `−15`, `−20`, `−25` that are all ≈ 0. It is the **stated number and
the stated reasoning** that are wrong.

*Fix:* delete "The 12 unmeasured carry ≈ 7.6 %". Replace the "It is complete" bullet with the
measured statement: *"the 12 unmeasured positions were estimated directly from `KO_POS1`'s own
seeded draws at −0.00058 per position (×12 = −0.7 % of `KO_FULL`, CI [−31 %, +10 %]); nothing large
hides there."* And measure the remaining 12 properly if the additivity claim is to carry weight —
it is 12 arms of the same 29 min each.

### M4. Group J is launched with **13 controls**, so by the sprint's own R3-B1 rule it cannot return a PASS at α = 0.05 — and S-073/S-074 do not say so
`slurm_scripts/dcs_csi_p1_arms.slurm:118-127` (`for i in 0 1 2 3 4 5 6 7` → 8 random,
`for j in 0 1 2 3 4` → 5 shuffled), against `configs/dcs_csi_axis_button_cwrow_L20.json`, which holds
exactly `ctrl_random0..7` and `ctrl_shuffled0..4` (30 bases total; verified).

13 controls ⇒ attainable `rank_p_floor = 1/14 = 0.0714 > 0.05`. This is the identical situation
S-071 diagnosed for basket ("certifying it at alpha=0.05 needs at least 19 controls"), and group I
exists precisely to fix it — yet the *flagship follow-up*, the one S-072 names as "Phase 1's question
asked at the position the causal evidence actually points to", is launched one rung short of
certifiable. Job 897576 is running it now. Best possible outcome: INCONCLUSIVE.

A second, smaller confound rides along: `KO_CW_PLS` is rank 5 (`cand_pls5`, since the cwrow_L20 axis
selects rank 5), but group J's controls are all rank-1 bases norm-matched to `cand_rank1`. That is
exactly the DCS-CSI-048 dose confound group C was built to remove, and there is no group-C
equivalent for the cwrow axis.

*Fix:* regenerate the cwrow_L20 axis with `--n-random 22 --n-shuffled 12` (the parameters S-071's
job 897529 already used for basket) before or alongside group J, and add rank-5 matched controls via
`--rank-controls 5`. Record in the log, at launch time, the attainable `rank_p_floor` of every arm
set — a one-line precondition that would have caught this and the basket case.

### M5. `--rescue-rel-end-rows` is **span**-relative, but its help text, its parser's refusal message and the entire published position map read it as **sequence**-relative. They coincide only because this bank's query span happens to end at the final token
`src/boombness/score_behavior.py:3686` — `_idx = len(_rpos) + _re if _re < 0 else _re`, where `_rpos`
is `sorted(prot)` (the query span) or `list(dk)` (the demo block) — against `:2331-2334`
(*"by rel_end (-1 = last)"*) and `:379-384`, whose refusal text states
*"Every edit index in this phase is `len(input_ids)+rel_end`"*. It is not: it is
`len(span)+rel_end`.

For the runs in the record the two are identical, and I verified that is a property of the data, not
of the code. On all 670 rows of `csi1_button_train_KO_AT10`:

```
seq_len - 1 - query_span_bounds[1]   = 0      on 670/670 rows
n_query_span_positions               = 28     on 670/670 rows  (== bounds width)
surface_span_positions - seq_len     = -10    on 670/670 rows, token ' button'
```

so span index `28−10 = 18` ↔ absolute `180+18 = 198` ↔ sequence `rel −10`. Both conventions agree.

They stop agreeing the moment either premise moves. The **default** is
`--rescue-positions demo`, and in the same row the demo block is `demo_span_bounds = [131, 178]`
with `seq_len = 208`: `--rescue-rel-end-rows -1` under the default restores absolute 178, which is
sequence `rel −30`. Every token identity in S-072's table would be off by 29. The same happens for
any bank whose template puts anything after the query span.

Nothing on the row disambiguates it either: `rescue_rel_end_rows` is recorded verbatim (`"-10"`) and
the realised absolute positions are still not persisted (R2-m10, still open), so a reader must know
`rescue_positions` *and* that `query_span_bounds[1] == seq_len-1` to decode what was patched.

*Fix:* (a) say "rel_end **within the chosen rescue span**" in the help and in the parser's refusal
text, and stop asserting `len(input_ids)+rel_end` there; (b) record
`rescue_positions_realised_rel_end` (cheap — `[p - len(ids_r) for p in _rpos]`) on the row so the
published map is self-describing; (c) refuse `--rescue-rel-end-rows` together with
`--rescue-positions demo` unless the operator passes an explicit acknowledgement, or offer
`--rescue-rel-end-rows-sequence` as the sequence-relative variant the docs currently describe.

### M6. `reports/DCS_CSI_CLAIM_TABLE.md` — declared "the file to read before writing any sentence for Matan or Mahmood" — contains **none** of S-059/S-063/S-066/S-069/S-072
Sections A, B and C of the claim table run D1–D8, E1–E2, C1–C4. The position ladder, the position
map, the 46.6 % codeword result and the `KO_POS28` consistency check appear nowhere. The only trace
of this half of the sprint is prohibition **D-15**, imported from S-070.

Two consequences, both live:
* The sprint's two self-described headline positives ("the sprint's clearest positive mechanistic
  result", S-059; "the sprint's most defensible mechanistic claim", S-072) are absent from the
  authority file. Anyone following the stated procedure writes them up from nothing.
* S-066's **withdrawals** are also absent. The sentences *"each query-span position contributes an
  equal, additive ~1/28 of the effect"*, *"no privileged position"* and *"the answer to 'is it
  localised?' is a quantified no"* are still sitting, unannotated, in S-059's boxed quote in an
  append-only file. Section D — the prohibitions list, which already carries four WITHDRAWN items —
  does not carry them.

*Fix:* add A-rows for the ladder (with the S-066 interpretation, not S-059's) and for the position
map, each citing the artifact M2 asks for; add the three withdrawn sentences to section D; and
disambiguate C2, which still reads "Does position **identity** matter beyond position **count**?" —
true for the *behavioural* patch endpoint, decisively answered for *semantic installation*, and a
reader will conflate them.

---

## MINOR

### m1. `rescue_rel_end_rows` is missing from the non-rescue row schema, defeating the docstring's own promise
`src/boombness/score_behavior.py:3117-3120`. The early-return tuple lists ten keys; the live return
at `:3122-3133` writes **eleven**. `rescue_rel_end_rows` is not in the tuple.

The docstring two lines above says: *"Emit the keys even on non-rescue arms (as None) so every row in
a run set shares one schema; an absent key and a null key are different things to an analysis that
iterates."* Verified on the shipped data — `BASE` and `KO` rows have no `rescue_rel_end_rows` key at
all, while `KO_FULL` has it as `null` and `KO_AT10` has `"-10"`. Any analyser doing
`r["rescue_rel_end_rows"]` (rather than `.get`) raises `KeyError` on exactly the two arms that
anchor every contrast.
*Fix:* add `"rescue_rel_end_rows"` to the tuple at `:3119`.

### m2. `--rescue-rel-end-rows` and `--rescue-n-positions` compose silently, and the size-match wins
`:3696-3705` runs unconditionally after the named selection. With
`--rescue-rel-end-rows -10,-7 --rescue-n-positions 1`, the row donates a *seeded random one* of the
two named positions while `rescue_rel_end_rows` still records `"-10,-7"`; `n_rescue_positions`
correctly says 1, so the two fields disagree about what was patched and only the reader can tell.
The reverse order (`n` larger than the named set) refuses every row via
`rescue:too_few_positions_to_size_match` — a whole-run failure whose reason names the wrong cause.
Currently latent: no run in the record passes both.
*Fix:* `raise SystemExit` when both are given, or intersect them explicitly and record the realised
set (see M5b).

### m3. `--force-layer`'s provenance is honest in the axis artifact and **dropped** on the way to the rows
`scripts/dcs_csi_axis.py:314-330` writes `layer_forced: true` and `layer_argmax_not_used: 28` into
`out`, and `out` is saved as `meta` inside the `.pt` (`:412`). But
`score_behavior.py:_meta()` (`:2060-2069`) copies only nine fields and neither of those two is
among them. So `configs/dcs_csi_axis_button_cwrow_L20.json` says the layer was forced; the
`rescue_basis_meta` on every group-J row says `selected_layer: 20` and nothing else — indistinguishable
from an axis that selected L20 on its merits (which `dcs_csi_axis_button_behavioral.json` genuinely
did). S-073's claim that *"the artifact records `selected_layer = 20`, `layer_forced = true`, and
`layer_argmax_not_used = 28`"* is true of the axis JSON and false of the run rows, which is where a
downstream analysis looks.
*Fix:* add `"layer_forced"` and `"layer_argmax_not_used"` to `_meta()`.

Otherwise the `--force-layer` path is correct and I could not make it disagree with what was fit:
`layer` is reassigned **before** the final `build(...)` at `:334`, so the bases, the rank sweep, the
controls and `hidden_dim` all come from the forced layer; `train_rho` is re-read from the forced
layer's entry rather than carrying the argmax's value; the `not in layers` refusal is anchored to
the captured plateau; and the printed line names both layers and both ρ.

### m4. `if a.force_layer:` makes layer 0 unforceable
`dcs_csi_axis.py:314` with `default=0`. `--force-layer 0` is silently ignored and the argmax is used.
Harmless today (0 is not in any `layer_grid`), but the sentinel should be `None`, and 0 should then
hit the explicit `not in layers` refusal like every other bad value.

### m5. Group E's comment still asserts the off-by-one that group H exists to correct
`slurm_scripts/dcs_csi_p1_arms.slurm:176-178`: *"rel-6 is the site the AXIS was fit at and **rel-11
is cw_query, the codeword row the knockout actually edits**"*. Group H's comment (`:148-152`) states
the correction — `rel −10` is the codeword, span index 18 of 28 — but group E's text was never
annotated. Re-running group E reproduces the mislabel, and S-066's table inherited it.
*Fix:* one line in group E: `# CORRECTED (DCS-CSI-068): rel -11 is ' word'; the codeword is rel -10. See group H.`

### m6. S-072's *"token identities are verified two independent ways"* holds for one token, not sixteen
`surface_span_positions` locates only `target_surface` — I confirmed it is a single-element list
carrying `[' button']` on all 670 rows. The other fifteen entries in the table rest solely on the
re-tokenisation. (The re-tokenisation is right: I reproduced the whole 28-token tail independently
from the bank's `full_prompt` through `apply_chat_template`, 208 tokens, every identity matching.)
*Fix:* "the codeword's identity is verified two independent ways; the remaining identities come from
re-tokenising the chat-templated prompt."

### m7. `rel −4`'s "1.1 %" is one domain, and S-072 drops the CIs that S-069 carried
S-069's table published CIs; S-072's does not. `rel −4` is the one entry where that matters:
point **+0.00077**, CI **[−0.00527, +0.00696]** — eight times wider than any neighbour — with
**31/36** domains *negative* and median **−0.00137**. It is driven by a single domain
(`surveying_office`, +0.0763); excluding it the mean is **−0.00038**. S-072 nevertheless ranks it
(1.1 %) above `'?'` (1.0 %), and `'<|start_header_id|>'` is not a token one wants to be defending.
*Fix:* restore the CI column, and move `rel −4` into the "indistinguishable from zero" group with a
one-line note that its point estimate is a single-domain artifact.

### m8. S-070 cites a field that is null in the corpus it names
S-070's table is headed *"measured from `surface_span_positions − seq_len`"* and attributes the
behavioural row to *"the corpus the axis was fit on"*,
`outputs/boombness/extract_boombness/cont1_behavioral_button_bomb_20260910_152806_272296`. In that
corpus `surface_span_positions` is **`null` on all 3720 rows** (and the row count is 3720, not 180).
The `−11` is there under a different field — `token_pos − seq_len = −11` on 3720/3720, `token_text`
`' button'` ×1860 — and the "180/180" figure comes from a different run,
`score_behavior/patch_ko_button_20260915_115234_2437732`, where `surface_span_positions − seq_len` is
indeed `−11` on 180/180 with `surface_span_tokens == [' button']`.
**The claim is right and doubly confirmed; the provenance line points at the wrong field in the
wrong file.** For an entry whose entire job is to settle a provenance dispute, that matters.
*Fix:* name both sources: `token_pos − seq_len` in the extraction corpus (3720/3720) and
`surface_span_positions − seq_len` in the 180-row patch run.

### m9. Nothing checks `rescue_rel_end_rows` across arms (extends R3-m4)
`dcs_csi_subspace_analyze.py:405-408` still compares only `knockout_scopes`; R3-m4's list of
unchecked fields (`intervene`, `rescue_donor`, `rescue_positions`, `rescue_n_positions`) has gained a
fifth member. Two arms differing only in `rescue_rel_end_rows` — the exact axis the position map
varies — would be averaged against each other with `VOID: []`.

### m10. Two arithmetic wobbles in the log, both trivial, both quotable
*(a)* S-069 says the top four carry **92.6 %**; S-072 says **92.5 %**. The value is
0.06533 / 0.070596 = **92.54 %**; S-069 rounded from the truncated 0.0706.
*(b)* S-069's *"Slope × 28 = 0.0695"* is the **through-origin** slope (0.002482 × 28 = 0.06950);
S-059's headline *"slope × 28 = 0.07049"* is the **intercept** fit (0.002517 × 28). Both are correct
and reproduce; they are different fits quoted without saying which.

---

## NIT

* `parse_rel_end_rows` refuses every non-negative offset (`:376-384`), so the `else _re` branch at
  `score_behavior.py:3686` is unreachable dead code. Likewise `sorted(set(_sel))` at `:3694` can
  never dedupe, since the parser already refuses duplicate offsets and distinct offsets map to
  distinct indices.
* Group J's `KO_CW_FULL` (`:110-112`) is command-line-identical to group H's `KO_AT10`. That is a
  *good* choice — a within-allocation positive control at +0.03289 — but the comment presents it as
  a new arm rather than a deliberate re-run, so a reader may not notice that the two should come out
  equal and that their difference measures allocation drift for free.
* The header block documents groups A–F only; G, H, I and J are documented in the inline comments
  and in `GROUP`'s `:?` message not at all.
* `strict_run_dir`'s anchored `_pat` (`dcs_csi_rederive_patch.py:72`) correctly separates
  `KO_AT1` from `KO_AT10/11/12/15` — I re-confirmed it, and my own first-draft resolver got this
  wrong, which is a fair indication of how easy the mistake is. The position map never used that
  resolver (M2).
* S-072 labels `−12, −15, −20, −25, −28` as "(earlier query/context)". They are `' the'`, `','`,
  `'.'`, `' one'`, `'Answer'` — all inside the final instruction sentence. There is no context in
  the 28-token span.

---

## CHECKED AND FOUND CORRECT

Every number below was recomputed from `results.jsonl` with my own loader
(`p_concept = softmax(logp_concept, logp_codeword)` on `query_kind=semantic_one_word` ∧ `cell=C`,
keyed by `(domain, family_slot)`), my own cross-arm key intersection, my own domain means and my own
paired domain bootstrap (20 000 resamples). No sprint analysis script was imported.

**The codeword's position, both prompt types — reproduces exactly (S-069, S-070).**

| prompt type | source | measurement | rows |
|---|---|---|---|
| semantic_one_word | `csi1_button_train_KO_AT10` | `surface_span_positions − seq_len = −10`, token `' button'` | **670/670** |
| behavioural | `patch_ko_button_2026…2437732` | `surface_span_positions − seq_len = −11`, token `' button'` | **180/180** |
| behavioural | `cont1_behavioral_button_bomb_2026…272296` | `token_pos − seq_len = −11`, `token_text ' button'` | **3720/3720** |

**There is no off-by-one, and the two conventions coincide *for this bank* because the query span
ends at the final token** — `seq_len − 1 − query_span_bounds[1] = 0` and
`n_query_span_positions = 28` on **670/670** rows. (This is the premise M5 flags as undocumented.)

**Token identities — reproduce exactly (S-072).** Re-tokenising the bank's `full_prompt` through
`apply_chat_template(add_generation_prompt=True)` gives **208** tokens, matching `seq_len`:
`−1 '\n\n'`, `−2 '<|end_header_id|>'`, `−3 'assistant'`, `−4 '<|start_header_id|>'`, `−5 '<|eot_id|>'`,
`−6 '?'`, `−7 ' to'`, `−8 ' refer'`, `−9 ' actually'`, **`−10 ' button'`**, `−11 ' word'`,
`−12 ' the'`, `−15 ','`, `−20 '.'`, `−25 ' one'`, `−28 'Answer'`. Every published identity matches.

**The 16 position arms each restored exactly one position, and all 16 are live.** On all 670 rows of
each arm: `n_rescue_positions = 1`, `rescue_rel_end_rows` equal to the arm's own rel and nothing
else, `rescue_n_positions_requested = null`, `rescue_layer = 20`, `rescue_positions = "query"`,
`rescue_liveness.fired = true` **670/670**, `n_positions_written = 4` with `n_forward_calls = 4`
(1 position × 4 readout forwards). `KO_FULL` and `KO_POS28` both write **112 = 4 × 28**.
`hook_n_decode_edits = 0` and `hook_liveness_violations = []` on every row of every arm.
`BASE` is clean: `hook_n_prefill_edits = 0` on 670/670, `rescue_liveness = null`, no rescue layer
(the R3-M6 hazard does not bite here). All 19 arms share one `config.json` fingerprint —
same bank, model snapshot, `demo_all:attn_knockout:6-14:1.0`, `target_surface_row_only`,
bfloat16/eager, seed 20260913, `min_option_mass 0.05` — with `rescue_basis` empty on all of them
(whole-state, as S-072 claims).

**One key set. The repeated "averages over non-identical key sets" defect is ABSENT.** All 19 arms
(`BASE`, `KO`, `KO_FULL`, 16 × `KO_AT*`) return **670 keys each, and the sets are byte-identical to
BASE's** — no intersection loss, **67 TRAIN domains**, which is the population S-072 names. The
validation ladder likewise: **230 keys / 23 domains** across all nine arms.

**The complete position map — every point estimate reproduces to the last published digit** (67
domains, denominator `KO_FULL − KO = +0.07060`; manipulation scale `KO − BASE = −0.20704`
[−0.22608, −0.18817], 0/67 domains positive):

| rel | recovery | CI95 | pos/neg | % of `KO_FULL` | S-072 says |
|---|---|---|---|---|---|
| **−10** | **+0.03289** | [+0.02778, +0.03788] | **62/5** | **46.6 %** | 46.6 %, 62/5 ✓ |
| −1 | +0.01721 | [+0.01537, +0.01903] | 67/0 | 24.4 % | 24.4 %, 67/0 ✓ |
| −7 | +0.00784 | [+0.00663, +0.00905] | 64/3 | 11.1 % | 11.1 %, 64/3 ✓ |
| −2 | +0.00739 | [+0.00646, +0.00836] | 67/0 | 10.5 % | 10.5 %, 67/0 ✓ |
| −4 | +0.00077 | [−0.00527, +0.00696] | 31/36 | 1.1 % | 1.1 %, 31/36 ✓ (see m7) |
| −6 | +0.00071 | [+0.00002, +0.00139] | 39/28 | 1.0 % | 1.0 %, 39/28 ✓ |
| −5 | +0.00033 | [−0.00026, +0.00090] | 36/31 | 0.5 % | 0.5 %, 36/31 ✓ |
| −8 | +0.00030 | [−0.00041, +0.00102] | 33/34 | 0.4 % | 0.4 %, 33/34 ✓ |
| −9 | −0.00003 | [−0.00075, +0.00070] | 33/34 | −0.0 % | −0.0 %, 33/34 ✓ |
| −11 | −0.00025 | [−0.00101, +0.00053] | 26/41 | −0.4 % | −0.4 %, 26/41 ✓ |
| −12 | −0.00026 | [−0.00085, +0.00032] | 35/32 | −0.4 % | ≈0 ✓ |
| −3 | −0.00052 | [−0.00115, +0.00009] | 33/34 | −0.7 % | −0.7 %, 33/34 ✓ |
| −15 | −0.00049 | [−0.00119, +0.00021] | 31/36 | −0.7 % | ≈0 ✓ |
| −20 | −0.00013 | [−0.00073, +0.00045] | 34/33 | −0.2 % | ≈0 ✓ |
| −25 | +0.00008 | [−0.00062, +0.00078] | 33/34 | +0.1 % | ≈0 ✓ |
| −28 | −0.00061 | [−0.00118, −0.00003] | 26/41 | −0.9 % | ≈0 ✓ |

**The sum-to-92.4 % arithmetic is exact.** Σ(16) = **+0.06523** = **92.4 %** of `KO_FULL` = 0.07060.
Top four (−10, −1, −7, −2) = **+0.06533** = **92.5 %**. S-069's twelve-position variant also
reproduces: Σ(12) = **+0.06593** = **93.4 %**. (What does *not* follow from these is M3.)

**The position ladder, TRAIN — reproduces exactly (S-059).** k = 1/2/4/8/14/20/28 →
+0.00281 / +0.00607 / +0.00876 / +0.01734 / +0.03328 / +0.05020 / +0.07060, pos/neg
40/27 → 51/16 → 53/14 → 59/8 → 61/6 → 63/4 → **66/1**, every CI as published.
Fit `recovery = 0.002517·k − 0.000683`, **R² = 0.9971**; slope × 28 = **0.07048** vs `KO_FULL`
0.07060, ratio **0.998**. Through-origin slope 0.002482 (× 28 = 0.06950), R² 0.9968.

**The position ladder, VALIDATION — reproduces exactly (S-063).** 230 keys / **23 domains**;
+0.00319 / +0.00620 / +0.00692 / +0.02550 / +0.04690 / +0.06710 / +0.09502; pos/neg
14/9, 20/3, 17/6, 20/3, **23/0**, 22/1, **23/0**; through-origin slope **0.003349**,
**R² = 0.9939**, slope × 28 = 0.09378 vs `KO_FULL` 0.09502, ratio **0.987**. The noisy k = 4 rung
(0.51× linear) is present and is reported in S-063 rather than smoothed.

**`KO_POS28` ≡ `KO_FULL`, and S-042's lesson is honoured on both splits.** Distinct run directories,
distinct PIDs, distinct nights, distinct file hashes, identical values:

```
TRAIN       KO_POS28_20260915_235451_3361779  (sha16 dd7a7902520e7896)
            KO_FULL_20260915_194003_1705849   (sha16 21c368c23e00dc2e)   max|diff| 0.000e+00 / 670 keys
VALIDATION  KO_POS28_20260916_005109_1769735
            KO_FULL_20260915_222841_1724423                              max|diff| 0.000e+00 / 230 keys
```

**NEW — an end-to-end cross-validation of `--rescue-rel-end-rows` that the sprint has not run.**
`KO_POS1`'s draw is `random.Random(f"{prompt_id}|1").sample(sorted(query_span), 1)`, which depends
only on the list length, so I reproduced the restored position for each of its 670 rows
(distribution over the 28 rels: 12–31 rows each, no degeneracy). For the **401** rows whose draw
landed on one of the 16 named positions, `KO_POS1`'s value and the corresponding `KO_AT*` arm's
value are **identical on 401/401 rows, max|diff| 0.000e+00**, rel by rel. Two different code paths
(`--rescue-n-positions` vs `--rescue-rel-end-rows`), two different launcher groups, two different
nights, same answer. This is the strongest available evidence that the rel_end → index arithmetic is
correct and that no off-by-one exists anywhere in the position map.

**S-054 / S-058 rank 4 of 11 — reproduces on both splits.** Candidate `KO_AXIS` vs its 10-arm
family (4 shuffled + 6 random), recomputed independently:

```
TRAIN       666 keys / 67 domains   candidate +0.00040   rank 4 of 11   rank_p 0.3636
            KO_RAND2 +0.00159, KO_SHUF2 +0.00104, KO_RAND3 +0.00049  (the 3 that beat it)
VALIDATION  229 keys / 23 domains   candidate +0.00132   rank 4 of 11   rank_p 0.3636
            KO_SHUF2 +0.00266, KO_RAND2 +0.00211, KO_RAND3 +0.00172
```

All ten TRAIN control values match `reports/DCS_CSI_SUBSPACE_button_train_rank1.json` to 5 dp.

**S-071 basket rank 1 of 11 — reproduces, and INCONCLUSIVE is the right word.** 664 keys /
67 domains; candidate **+0.00283** CI [+0.00076, +0.00524], 45/22 domains; `KO_FULL − KO` =
**+0.12410**, recovery fraction **0.0228**. Rank **1 of 11**, `rank_p = 0.0909 = 1/(10+1)`, its floor.
All ten control values match S-071's table exactly, and the margin over `KO_SHUF2` (+0.00219) is
**+0.00064** — an order of magnitude inside the candidate's own CI width, which S-071 states
("the margin is thin … a ratio of 1.3×"). The three-way verdict and its prohibitions are correctly
stated.

**Caveats stated early and NOT dropped later.** I checked the three that matter.
*S-067's output-adjacency caveat* on `rel −1` is restated in full in S-069 ("its 24.4 % must not be
read as storage") and again in S-072 (group 2, "this is the **readout site**").
*S-070's prompt-type qualifier* is honoured in S-072 ("the `rel −6` offset — which **in the semantic
prompt** is `'?'`") and is codified as prohibition D-15 in the claim table.
*S-066's uniformity withdrawal* is correctly scoped in S-066 itself ("RETAINED: the linearity
measurements themselves … their *interpretation* changes"), and S-072's additivity language does not
re-assert uniformity. The one place it is dropped is the claim table (M6).

**`--force-layer` is correct** apart from the provenance gap (m3) and the falsy-zero sentinel (m4):
refuses a layer outside the captured plateau, reassigns `layer` and `train_rho` before the final
`build`, so bases, ranks, controls and `hidden_dim` are all fit **at** the forced layer;
`configs/dcs_csi_axis_button_cwrow_L20.json` honestly records `selected_layer 20`,
`layer_forced true`, `layer_argmax_not_used 28` and `train_loo_rho_at_selected_layer 0.5254` (the
L20 entry of its own grid, not the L28 argmax 0.5871). The consumer-side layer guard at
`score_behavior.py:2044` is a hard `SystemExit`, not a warning — and B1 is about to demonstrate that
on two live jobs.

**Groups E, F, G, H and J agree with their comments** in every respect I could check other than B1
and m5: arm labels equal the `KO_AT<|rel|>` the loop builds, tags are `${P}_${arm}` with no
collisions, group G's `-2,-3,-4,-5,-8` and group H's `-10,-7,-9,-12,-15,-25` and group E's
`-1,-6,-11,-20,-28` are disjoint and together give exactly the 16 arms analysed, group F runs only
whole-state arms under the override as its comment promises, and group J's basis keys
(`cand_rank1`, `cand_pls5`, `ctrl_random0..7`, `ctrl_shuffled0..4`) and its `cand_rank1` norm-match
all exist in `dcs_csi_axis_button_cwrow_L20.pt`. No group silently reuses another's parameters.
