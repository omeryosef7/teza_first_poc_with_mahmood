# BUGHUNT — P3 decision-token path (`scripts/phase4_edge_knockout.py`)

Adversarial code review, 2026-08-06. Target: the newest, least-exercised code in the file — the
`--prompt-form decision` / `--readout refusal_proj` path added in `f10c3595` (tick54) and patched in
`59786181` (tick59). ~2 GPU runs of exercise (726211 buggy, 726616 / 727983 / 728189 clean).

**No file was edited and no job was launched.** Everything below is either static reading or an offline
replay of the aggregator's arithmetic on synthetic rows.

Commits touching the file (newest first): `59786181` tick59 · `f10c3595` tick54 · `14957648` tick49 ·
`2d59bea3` band mode · `f05926b5` token-index fix · `866864ea` original.

Evidence run used throughout: `outputs/phase4_edgeKO_clearharm_20260806_141548_728189/`
(`mode=band`, `prompt_form=decision`, `destinations=answer`, `layers=14..21`, `n_items=86`, 258 raw rows).

---

## Summary table

| # | Sev | Where | One line |
|---|-----|-------|----------|
| B1 | **CRITICAL** | `:281-291` + `:320` | `--mode perhead` (the DEFAULT) is silently wrong under `--prompt-form decision` and then `TypeError`s after the whole GPU scan |
| B2 | **HIGH** | `:304` | decision aggregator collapses every `(layer,head)` into one entry per sid; it is structurally band-only and never checks `args.mode` |
| B3 | **HIGH** | `:316-333` | the decision "specificity" is a different quantity from the FC one; the `rand_edge` cell is computed (86 rows) and then never used in any contrast |
| B4 | MEDIUM | `:129`, `:321-330` | the random *axis* is a floor, not a matched control — `Δrandom = −1e-05`; specificity ≈ raw shift by construction |
| B5 | MEDIUM | `:158-160`, `:215-216` | silent item drop, no counter, no denominator; an all-dropped run writes `n_items: 0` and exits 0 |
| B6 | MEDIUM | whole file | **no `RUNMETA.json` / `DONE.json` in either path** — not caused by the early `return`; plus `fh` is not exception-safe |
| B7 | MEDIUM | `:275`, `:253` | `all_query_edges` is not "all previous keys" whenever `len(qdest) > 1` — affects an already-published number |
| B8 | MEDIUM | `:253-255` | random-source pool includes BOS/attention-sink and the whole request line; empirically 47× the impact of the demo edges |
| B9 | LOW-MED | `:325`, `:340`, `:353`, `:377` | `--seed` is partially ignored (all bootstraps hardcoded to 0); `rand_src` depends on `--n-prompts` |
| B10 | LOW | `:59-62`, `:222-225` | `--readout` cannot carry information; `--destinations` is validated inside the item loop |
| B11 | LOW | `:257-262` | under decision form `base_p_concept` holds an unbounded projection, not a probability |
| B12 | LOW | `:307-310` | the `missing` guard is vacuous — it can never fire on a freshly written `raw.jsonl` |
| B13 | **NOT-A-BUG** | `:120-121`, `:176` | hs-row convention **verified correct** against the artifact sidecars; out-of-range fails loudly (but only incidentally) |

---

## B1 — CRITICAL — `--mode perhead` is silently broken under `--prompt-form decision`, and it is the default

**Where.** `scripts/phase4_edge_knockout.py:281-291` (per-head branch), crashing at `:320`.
Defaults: `:46` `--mode` default `"perhead"`; `slurm/run_phase4_edgeko.sh:38` `: "${DSMODE:=perhead}"`.

**Why it is wrong.** `emit()` (`:179-189`) exists precisely so "a cell cannot silently keep the
forced-choice readout under `--prompt-form decision`" — that is its docstring, and
`CONTINUATION_PROGRESS.md:1117-1123` records it as bug-fix #1 of the tick54 self-review
("Fixed by routing **every** cell through one `emit()` helper, so a cell **physically cannot** be left on
the wrong readout"). That claim is false. `emit()` is called from exactly three places — `:269`, `:272`,
`:277` — all inside `if args.mode == "band"`. The per-head loop calls `readout(...)` **directly**:

```python
# :283-291
ko = pc.AttentionKnockout(lm.model, [lyr], qdest, demo_pos, heads=[h])
p_ko = readout(tok, cid, kid, [ko])                      # <-- FC readout, not emit()
rec = {**brow_row, "layer": lyr, "head": h, "cell": "edge_KO", "p_concept": p_ko}
```

So under `decision` the per-head branch (a) scores `p_concept = P(" concept")/(P(" concept")+P(" codeword"))`
at the first-generated-token position, where — by the script's own argument at `:77-79` — that label does
not exist and the quantity is undefined; and (b) writes rows that carry **no** `proj_refusal` /
`proj_random` field. The two guards at `:77-82` only police the `--prompt-form`/`--readout` pair; nothing
policies `--mode`.

Then the decision aggregator reads `r.get("proj_refusal")` → `None` (`:304`) and does
`d[x][0] - base_ref[x]` (`:320`), i.e. `None - float`.

**Verified offline** (replay of `:300-333` on synthetic per-head rows):

```
missing guard: set()            -> the :307 guard does NOT fire
by_cell edge_KO: {'s1': (None, None)}
CRASH at line 320: TypeError unsupported operand type(s) for -: 'NoneType' and 'float'
```

**Concrete failure scenario.** An operator repeats the P3 run on the second cohort and forgets one
`--export` variable:

```
sbatch --export=ALL,DSBENCH=...,DSFORM=decision,DSREADOUT=refusal_proj,DSDEST=answer,DSLAYERS=14-21 \
       slurm/run_phase4_edgeko.sh          # DSMODE unset -> defaults to perhead
```

The script passes both `--prompt-form`/`--readout` guards, prints `attn_implementation='eager' (asserted)`
and the reassuring `refusal readout: hs18 (decoder L17) ... norm-matched random control armed`, then runs
8 layers × 32 heads × 2 cells × 86 items ≈ **44 000 forward passes** (all layers: ~176 000) producing a
meaningless `p_concept`, writes a complete-looking `raw.jsonl`, and dies with a `TypeError` at the
aggregation step — or hits the 4 h walltime first. Because of B6 there is no `DONE.json`, so the leftover
run dir is indistinguishable from a finished one to `scripts/update_registry.py` / `scripts/audit_artifacts.py`
(it has a `raw.jsonl` payload). The wrapper's own log header (`slurm/run_phase4_edgeko.sh:60`) prints
`destinations/form/readout/proj_hs` but **not** `DSMODE`, so the mistake is invisible in the log.

**Fix.** Either (a) add a third guard next to `:77-82` — `if args.prompt_form == "decision" and
args.mode != "band": raise SystemExit(...)` — or (b) route `:283-291` through `emit()` and give the
aggregator a `(layer, head)` key (see B2). (a) is one line and honest; (b) is the real feature.

---

## B2 — HIGH — the decision aggregator throws away `layer`/`head`

**Where.** `:304` `by_cell[r["cell"]][r["sid"]] = (...)`.

**Why it is wrong.** The key is `(cell, sid)`. Nothing in the decision branch — not the accumulation, not
the loop at `:316`, not the emitted summary — mentions `layer` or `head`. In band mode there is one row
per `(cell, sid)` so this is fine. In per-head mode there are `len(layers) × Hn` rows per `(cell, sid)`,
all writing into the same slot: **last head wins, silently**. The replay above shows it —
`by_cell['edge_KO']` has a single entry after three rows from two different heads.

So even if B1's readout were fixed, `--mode perhead --prompt-form decision` would report the L21H31 result
labelled as if it were the whole scan. `out["mode"] = args.mode` is written into `summary.json` (`:311`),
which makes the output *look* mode-aware while the arithmetic is not.

**Concrete failure scenario.** Someone patches B1 by making the per-head branch call `emit()` (the obvious
one-line fix, and the one the tick54 note claims was already applied). The run now completes and produces a
plausible `summary.json` with three cells, `n = 86`, `ci_reliable: true` — computed entirely from the last
`(layer, head)` visited. No error, no warning, and the per-head structure the run existed to measure is gone.

**Fix.** Key on `(r["cell"], r["layer"], r["head"])` and emit per-head rows in the summary, or assert
`args.mode == "band"` at the top of the branch.

---

## B3 — HIGH — the decision-form "specificity" answers a different question than the FC-form one, and `rand_edge` contributes nothing to it

**Where.** FC path `:375` `spec = rk[s] - ko[s]` / `:357`. Decision path `:320-330`.

**Why it is wrong.** Two different quantities carry the same word:

| form | reported quantity | control |
|---|---|---|
| `fc` (`:357`, `:375`) | `rand_edge − edge_KO`, paired per item | count-matched random **edge** — "is it the *demo* edges?" |
| `decision` (`:321-330`) | `Δrefusal − Δrandom`, **within** a cell | random **axis** — "is it the *refusal* direction?" |

Both are legitimate controls for *different* confounds, but the decision branch computes only the second.
The `rand_edge` cell — 86 rows of real GPU time in run 728189 — is reported as a standalone row and is
**never contrasted with `edge_KO`**. There is no paired demo-vs-random-edge statistic anywhere in the
decision path. The one control that speaks to the actual P3 claim ("the query→demonstration edges carry
refusal to the decision token") is computed and discarded.

**Concrete failure scenario.** The headline P3 row from 728189 reads

```
edge_KO   mean_delta_refusal −0.00262   mean_delta_random −0.00001   specificity −0.00261   CI [−0.00558, +0.00027]
```

and gets written up as "the demo→decision edges are not specific". But that CI is a refusal-vs-random-*axis*
statement about `edge_KO` alone. The matched-edge comparison — which in the same run would be
`rand_edge − edge_KO` on `Δrefusal`, i.e. `+0.12187 − (−0.00262) = +0.125` — was never computed or
bootstrapped. A reviewer asking "how does the demo-edge knockout compare to the count-matched random-edge
knockout, the control your own FC path is built on?" cannot be answered from `summary.json`; the raw rows
are there, but no reported number uses them.

**Fix.** Add the paired cross-cell contrast to the decision branch (`Δrefusal[rand_edge] − Δrefusal[edge_KO]`,
paired on sid, `st.paired_bootstrap_ci`), and rename the axis statistic so the two controls are not both
called "specificity".

---

## B4 — MEDIUM — the norm-matched random axis is a floor, not a control (and Q5: drawn ONCE per run)

**Where.** `:129-130` `refrand = pc.norm_matched_random(refdir, 1, args.seed)[0]`.

**Answer to the question asked.** The random direction is drawn **once per run**, before the item loop, at
module scope of `main()`. It is *not* re-drawn per item, per cell, per layer or per head — every item and
every cell projects onto the same fixed axis. For a per-item **paired** specificity that is defensible and
matches repo convention (`phase_behav_refusal.py:132`, `phase_behav_refusal_inject.py:78`,
`45_toctou_factorial.py:285` all use `n=1`; only the per-*layer* scripts vary the seed,
`phase_refusal_projection.py:52`, `phase_refusal_inject_calibrated.py:79`). The pairing is at the item
level, so a shared axis does not break the pairing.

**What is wrong anyway.** With `n = 1` the bootstrap CI is conditional on one arbitrary axis; the variance
over the *choice* of random direction is never propagated. More seriously, an isotropic Gaussian direction
in 4096-d absorbs O(1/√d) ≈ 1.6 % of an arbitrary perturbation's norm, so `Δrandom` is near-zero **by
construction** and `specificity ≈ Δrefusal`. The control cannot reject the confound the comment at
`:322-324` says it exists to reject ("masking attention perturbs the residual stream at all").

Run 728189 shows exactly this:

| cell | Δrefusal | Δrandom | specificity | fraction removed by the control |
|---|---|---|---|---|
| `edge_KO` | −0.00262 | −0.00001 | −0.00261 | 0.4 % |
| `rand_edge` | +0.12187 | +0.00496 | +0.11691 | 4 % |
| `all_query_edges` | +1.07545 | −0.16626 | +1.24172 | control has the **wrong sign**, inflating the effect |

**Concrete failure scenario.** `all_query_edges` blocks *every* incoming edge to the decision token across
layers 14-21 — the maximal generic-damage cell, the one that by design should fail a specificity test. It is
reported as `specificity = +1.242, CI [+0.925, +1.555], ci_reliable: true`, i.e. **maximally specific**,
because the random axis moved the other way and the subtraction added 0.166 instead of removing anything.
Any claim of the form "cell X is specific because its CI excludes 0" is therefore unfalsifiable in this
design — the designated negative control passes the test with the largest effect in the table.

Also cosmetic-but-misleading: `refdir` is normalised to unit norm at `:125` *before* being handed to
`norm_matched_random`, and the result is re-normalised at `:130`. The "norm matching" is a no-op — it is a
random unit vector. Harmless arithmetically (both axes are unit, so the projections are comparable), but the
log line `norm-matched random control armed` (`:131-132`) overstates what happened.

**Fix.** Draw `n ≥ 20` axes and report the specificity against the random-axis *distribution* (or at least
its max), and add a variance-matched control (e.g. a direction sampled from the empirical residual
covariance) rather than an isotropic one. At minimum, gate on `all_query_edges` failing the test.

---

## B5 — MEDIUM — `build_decision`'s `rfind` fallback silently drops items, with no counter and no denominator

**Where.** `:158-160` (`req_off`/`req_tok`), `:161-163` (`demo_pos`/`query_pos`), `:215-216` (the guard).

**Answer to the question asked (Q1): a silent mis-split is NOT possible; a silent LOSS is.** If
`REQ_MARKER` is absent, `req_off == -1`, so `req_tok` falls back to `0`. Then:

* `demo_pos = [li for li in hit.last_idx if li < 0]` → **always empty** (token indices are ≥ 0);
* `query_pos = [li for li in hit.last_idx if li >= 0]` → **every** codeword occurrence, demos included.

The guard at `:215` then sees `not demo_pos` and `continue`s. So the item is dropped, not mis-split — the
fallback is accidentally safe. What is *not* safe is that the drop is completely silent: no counter, no
warning, no `n_attempted` field, and `n_items` in `summary.json` (`:315`) is the count of **survivors** with
no denominator.

**Concrete failure scenario.** A future bench (or a template revision, or a Gemma/Qwen chat template that
rewrites whitespace around the request line) changes the request line so `"Do not reason, just "` no longer
appears verbatim in the *templated* string. Then **every** item is dropped: `raw.jsonl` is empty,
`all_rows == []`, `base_ref == {}`, `base_rnd == {}`, the `missing` guard at `:307` compares two empty sets
and does not fire, `by_cell` is empty so the `:316` loop body never runs, and the script writes

```json
{"...": "...", "n_items": 0, "cells": {}}
```

prints `{}`, prints `decision-form summary -> <dir>`, and **exits 0**. A well-formed summary, a clean null,
and nothing anywhere says the experiment measured zero items. This is precisely the failure class the tick59
commit message congratulates the smoke for catching ("a run to completion producing a well-formed summary
whose numbers were impossible") — the same hole is still open one level up.

**Not currently biting.** Verified for run 728189: `bench_clearharm.json` has 86 DOUBLESPEAK rows in
`dev,heldout`, all 86 contain the marker, all 86 have codeword occurrences on both sides of it, and
`summary.json` reports `n_items: 86`. Zero drops. The bug is latent, not active.

**Secondary defect in the same guard.** `:215` requires `query_pos` non-empty even under
`--destinations answer`, where `qdest = [seqlen-1]` and `query_pos` is never used. An item whose request
line does not repeat the codeword would be dropped for a reason that does not apply to the configuration
being run.

**Fix.** Count and print drops (`n_attempted`, `n_dropped_no_demo`, `n_dropped_no_query`), write them into
`summary.json`, and `raise SystemExit` if `n_rows == 0` instead of writing an empty summary.

---

## B6 — MEDIUM — no `RUNMETA.json` / `DONE.json` in **either** path, and `fh` is not exception-safe

**Answer to the question asked (Q3).** The early `return` at `:337` skips **nothing that the other path
does**. Specifically:

* `fh.close()` is at `:292`, **before** the branch — not skipped. ✅
* The FC per-head path also has no RUNMETA/DONE/registry call; the band path `return`s at `:365` the same way.
* `grep -c "write_runmeta\|write_done" scripts/phase4_edge_knockout.py` → **0**.

So the early return is clean. The real finding is that the contract is not honoured **anywhere in the file**.
`ds_common.py:165-186` states it plainly: *"Write `out_dir/RUNMETA.json` as the FIRST action of a run"*,
`DONE_NAME = "DONE.json"`, `write_runmeta` is explicitly documented as never raising so that provenance can
never kill an experiment. Only 6 of 55 scripts call it, so this file is consistent with its neighbours
(`phase4b_pattern.py`, `phase4c_carryedge.py`, `phase5b_qkv.py`, `phase7d_onset.py`,
`phase_write_refusal_interaction.py`, `phase9_dose.py` all score 0 too) — but "everyone does it" is not a
defence for the *newest* result.

**Evidence.** The four 2026-08-06 P3 run dirs contain **only** `raw.jsonl` + `summary.json`. The 2026-08-03
dirs *appear* to comply but do not: their `RUNMETA.json` carries `"schema": "RUNMETA/1-reconstructed"`,
`"reconstructed": true`, `"slurm_job_id": {"source": "reconstructed", "evidence": "parsed from dir name"}` —
written after the fact by `scripts/backfill_runmeta.py` on 2026-08-05, not by the run.

**Concrete failure scenario.** Two of them, both live:

1. *No provenance on the headline P3 number.* `outputs/phase4_edgeKO_clearharm_20260806_141548_728189/`
   records no git commit, no `sys.argv`, no `transformers`/`torch` version, no GPU, no wall time. If the
   paper cites `edge_KO specificity = −0.0026`, the only record of *which code produced it* is a SLURM log
   that `logs/` rotation or a `--output` overwrite can lose. `scripts/update_registry.py:87` will register
   the run from a reconstruction (`_read_field` handles both flavours precisely because of this).
2. *A crashed run is indistinguishable from a finished one.* Combined with B1: the `TypeError` at `:320`
   leaves a run dir with a full-looking `raw.jsonl`, no `summary.json`, and no `DONE.json`. `audit_artifacts.py`
   classifies dirs by presence of a *payload* file (`:12-13`), so this dir has one and is not flagged as broken.
   Nothing marks it as failed.

**Third, smaller defect in the same area.** `fh = open(...)` at `:114` is a bare handle closed only on the
happy path at `:292` — no `with`, no `try/finally`. Any exception in the item loop (OOM on a long prompt,
the `AttentionKnockout` `RuntimeError` at `pair_common.py:460`, a `KeyboardInterrupt`, a SLURM
`SIGTERM` at walltime) leaves the last buffered rows unflushed. The resulting truncated `raw.jsonl` looks
complete because there is no row-count contract to check it against.

**Fix.** `dc.write_runmeta(out_dir, args)` immediately after `os.makedirs` at `:113`; `dc.write_done(...)`
with `rows_written=n_rows` before each `return` and at the end; `with open(...) as fh:` around the loop.

---

## B7 — MEDIUM — `all_query_edges` is not "all previous keys" when `len(qdest) > 1`, and a published number depends on it

**Where.** `:274-275` `allsrc = list(range(min(qdest)))`; same shape at `:253` for the random pool.

**Why it is wrong.** `AttentionKnockout` blocks `(qp, kp)` only for `kp <= qp` (`pair_common.py:473`), and
the source list is capped at `min(qdest)`. With the **default** `--destinations query_cw,answer`,
`qdest = query_pos + [seqlen-1]` and `min(qdest)` is the request-line codeword position. For the
`seqlen-1` destination, every key from the query codeword through `seqlen-2` — the entire request line and
(in FC form) the entire forced-choice question — stays **unblocked**. The cell named `all_query_edges` and
documented as the "all previous keys (firing control)" therefore blocks only a prefix of the causal keys for
one of its two destinations.

**Concrete failure scenario.** `reports/readiness/P3_READINESS.md:113` certifies this cell ✅ as the
"all previous keys (firing control)", pointing at `allsrc = list(range(min(qdest)))`, and
`reports/PHASE4_DEMO_RETRIEVAL.md:83-87` reports the resulting number
(`outputs/phase4_edgeKO_curated_20260803_074952_703335`, `all_query_edges_drop = [0.1084, 0.0484, 0.1821]`).
That run used the fused default destination set, so the published "we knocked out all incoming edges and the
reading dropped only 0.108" is really "we knocked out all edges into the query codeword, plus a *prefix* of
the edges into the answer position". A reviewer who reruns with `--destinations answer` gets a very
different number — 728189, the single-destination case, gives `Δrefusal = +1.075` for the same nominal cell.
The two are not comparable and nothing in the schema says so.

Note the decision-form run **is** correct here (`n_dest_positions: 1` in every raw row), so this defect is
confined to the FC/fused configuration — which is the one already in the paper.

**Fix.** Build `allsrc` (and `pool`) per destination: `range(qp)` for each `qp in qdest`, or document the
cell as "all keys before the first destination" and stop calling it the firing control.

---

## B8 — MEDIUM — the count-matched random source pool is not position- or type-matched

**Where.** `:253-255`.

```python
pool = [p for p in range(first_dest) if p not in demoset]
rand_src = sorted(rng.sample(pool, min(k, len(pool)))) if pool else []
```

**Why it is wrong.** The pool is *every* non-demo causal position: position 0 (BOS — the attention sink,
whose removal is known-catastrophic for transformer attention), every chat-template control token, the
system header, and the whole request line. `demo_pos` by contrast is a homogeneous set of codeword tokens
inside the demonstration block. The two source sets are matched on **count only** (`k = len(demo_pos)`,
`:254`), not on position, token type, or baseline attention mass. With `k` between 6 and 12 (verified from
728189's `n_demo_edges`) drawn from a several-hundred-token pool, position 0 is hit in ~2 % of items and
template tokens far more often.

**Concrete failure scenario.** In 728189, `rand_edge` moves the refusal axis by `+0.12187` while `edge_KO`
moves it by `−0.00262` — a **47× asymmetry in the opposite direction**. If B3 were fixed and the FC-style
paired contrast `rand_edge − edge_KO` were reported, it would come out strongly "significant" (+0.125)
almost entirely because the random sources are higher-impact tokens, not because the demo edges are special.
The control is biased in the direction that manufactures a positive result.

**Fix.** Exclude position 0 and the template span from `pool`; ideally sample from non-codeword tokens
*within the demonstration block* so the control is position-matched.

---

## B9 — LOW-MEDIUM — `--seed` is accepted but only partially used

**Where.** Declared `:72`. Used at `:84` (`dc.set_seed`), `:85` (`rng` for `rand_src`), `:129`
(the random axis). **Not** used at:

* `:325` `st.paired_bootstrap_ci(dref, drnd, n_boot=10000, seed=0)` — hardcoded
* `:340` `rng2 = np.random.default_rng(0)` — hardcoded
* `:353`, `:377` — both consume `rng2`

**Failure scenario.** A reviewer asks for a seed-sensitivity check on the P3 CI. `--seed 1` re-draws the
random axis and the random sources (so the point estimate moves) but produces the **identical** bootstrap
resampling stream, so "the CI is stable across seeds" cannot be distinguished from "the CI is stable because
the CI's own randomness is frozen". The reported `specificity_ci95` is not seed-controllable at all.

**Second-order.** `rng = random.Random(args.seed)` (`:85`) is a *single* stream consumed in item order at
`:255`. Because items can be skipped before it is consumed (`:216`, `:229`), and because `--n-prompts`
truncates the candidate list, changing `--n-prompts` or the bench changes the random sources for **every**
subsequent item. Two runs that share `--seed` do not share controls unless the item set is byte-identical.
Per-item seeding (`random.Random(hash((args.seed, r["sid"])))`) would fix it.

---

## B10 — LOW — flags accepted that cannot carry information / are validated too late

* **`--readout` (`:59-62`) is fully determined by `--prompt-form`.** The two guards at `:77-82` make the
  only legal combinations `(fc, fc)` and `(decision, refusal_proj)`. There is no configuration the flag can
  express. Not harmful — both guards fail loudly and early, which is good — but the flag advertises a degree
  of freedom that does not exist, and `slurm/run_phase4_edgeko.sh:52-53` propagates two variables
  (`DSFORM`, `DSREADOUT`) that must always be set together or the job dies at second one.
* **`--destinations` is validated inside the item loop (`:222-225`), not at parse time.** A typo
  (`--destinations query_word`) costs a GPU allocation, a full model load, the eager assertion, the refusal
  direction load, and one item's prompt build before `SystemExit`. Worse: combined with B5, if every item is
  dropped by the `:215` guard the validation **never runs at all** and an invalid `--destinations` string is
  written verbatim into `summary.json["destinations"]` (`:314`) of a zero-item run.
* **`--mode` is recorded (`:311`) but not respected** by the decision aggregator — see B2.

---

## B11 — LOW — field names lie under the decision form

**Where.** `:257-262`.

`base_p_concept` holds `readout_proj(...)` — an unbounded inner product with a unit vector, typically in
[−2, +2] — not a probability. `benign_p_concept` is `None`. The per-cell twins are named
`proj_refusal`/`proj_random` while their baselines are named `base_p_concept`/`base_proj_random`, so the
refusal pair is `(base_p_concept, proj_refusal)` and the random pair is `(base_proj_random, proj_random)` —
asymmetric, and the asymmetry is exactly where tick59's cross-axis bug lived.

**Failure scenario.** Any future analysis script (or an audit that sanity-checks probability columns for
range) reading `raw.jsonl` and treating `base_p_concept ∈ [0,1]` gets nonsense — the 728189 rows have values
outside that range. Currently latent: `grep` finds no consumer of `base_p_concept` / `proj_refusal` /
`proj_random` outside this file. `prompt_form` and `readout` are on every row, so a careful consumer *can*
disambiguate — but only if it thinks to.

---

## B12 — LOW — the `missing` guard cannot fire

**Where.** `:307-310`.

```python
missing = set(base_ref) - set(base_rnd)
if missing: raise SystemExit("... refusing to compute a cross-axis delta ...")
```

`base_ref` and `base_rnd` are both derived at `:305-306` from `all_rows`, which is read at `:294` from the
`raw.jsonl` this same process just wrote at `:257-262`, where `base_proj_random` is set unconditionally
whenever `prompt_form == "decision"`. The two key sets are therefore always identical and the guard is dead
code. It was written (tick59) to prevent recurrence of the cross-axis bug, but there is no `--reanalyze`
path that could feed it an old file, so it provides assurance it cannot deliver. Verified in the offline
replay: with per-head rows that break the aggregator two lines later, `missing` is `set()`.

If a re-analysis entry point is ever added, the guard becomes real — until then it should not be counted as
a defence in any readiness document.

---

## B13 — NOT-A-BUG (verified) — hs-row indexing and `--proj-layer` range

**Question asked (Q4): does `hidden_states[args.proj_layer]` match the `hs h == decoder layer h-1`
convention, and does an out-of-range `--proj-layer` fail loudly?** Both check out.

**Convention — correct, verified against the artifacts, not the comments.**
`:120-121` loads `refusal_direction_llama_L{proj_layer-1}.pt`; `:176` reads
`out.hidden_states[args.proj_layer]`. The artifact's own sidecar
`outputs/refusal_alllayers/refusal_direction_llama_L17.json` states:

```json
{"layer": 17, "d_model": 4096, "hidden_states_index": 18, "directions_row": 17}
```

Exact match with the default `--proj-layer 18`. The sibling family uses the same convention
(`outputs/stage_gcg_full/refusal_direction_llama_L18.json` → `"hidden_states_index": 19`), so the two
directories cannot be confused. `summary.json` records both rows (`proj_layer_hs: 18`,
`proj_layer_decoder: 17`, `:312-313`) — correct.

**Range — fails loudly, but only incidentally.** There is no explicit bounds check. Safety comes from the
filename lookup at `:122-123`: `--proj-layer 0` → `L-1.pt` missing → `SystemExit`; `--proj-layer -1` →
`L-2.pt` missing → `SystemExit`; `--proj-layer 33` → `L32.pt` missing (the dir holds L0..L31) → `SystemExit`.
So negative indices cannot silently wrap onto the last layer. `--proj-layer 32` resolves to `L31.pt`, which
exists, and `hidden_states[32]` is the last of the 33 rows — consistent, no error.

**The two gaps worth one line of code each.** (i) The range guarantee is a side effect of which files happen
to be on disk; a directions directory with a differently-named or extra file would remove it, and
`hidden_states[k]` for `k > num_layers` would then `IndexError` inside the first forward pass rather than at
argument time. (ii) Nothing asserts that the loaded `.pt`'s sidecar `hidden_states_index` equals
`args.proj_layer` — the whole convention rests on a filename. Reading the adjacent `.json` and asserting
`meta["hidden_states_index"] == args.proj_layer` would turn a naming convention into a checked invariant,
and would catch the day someone regenerates the directions with a different offset.

Also verified NOT-a-bug in the same area: `refdir` is a bare `torch.float32` tensor of shape (4096,)
(so `.float()` / `.norm()` are safe); `readout_proj` re-entering the same `AttentionKnockout` context twice
per cell (once per axis, `:185-186`) is safe because `__exit__` clears `_handles` (`pair_common.py:485-489`);
and the eager assertion at `:91-95` does what it claims — the log line
`[edgeko] attn_implementation='eager' (asserted)` is present in `logs/ds_edgeko_728189.out`.

---

## What I would fix before the next P3 run, in order

1. **B1** — one-line guard rejecting `--prompt-form decision --mode perhead` (and fix
   `slurm/run_phase4_edgeko.sh:38`'s default or print `DSMODE` in the wrapper header at `:60`).
2. **B6** — `write_runmeta` at `:113`, `write_done` before every `return`, `with open(...)` for `fh`.
   Without these the 728189 numbers have no recorded provenance and a crashed run is unrecognisable.
3. **B3** — report the paired `rand_edge − edge_KO` contrast in the decision branch; the rows already exist.
4. **B4** — `all_query_edges` currently *passes* the specificity test with the largest effect in the table.
   Until a control exists that this cell fails, no decision-form "specific" claim should be published.
5. **B5** — count and report drops; refuse to write a zero-item summary.
6. **B7** — either fix `allsrc`/`pool` per destination or correct `P3_READINESS.md:113` and
   `PHASE4_DEMO_RETRIEVAL.md:83-87`, which describe the fused-destination `all_query_edges` as a complete
   firing control.

Verification performed: git history for all 6 commits touching the file; static read of all 396 lines;
`pair_common.AttentionKnockout` / `norm_matched_random`, `ds_common.apply_template` /
`find_word_occurrences_in_text` / `write_runmeta`, `stats.paired_bootstrap_ci`; offline replay of the
decision aggregator on synthetic per-head rows (B1/B2/B12 confirmed by execution); numeric-only inspection
of `raw.jsonl` and `summary.json` for run 728189 and the three 2026-08-03 runs; marker/occurrence counts on
`bench_clearharm.json` and `bench_curated.json` (labels and counts only, no prompt text read or printed);
sidecar metadata for `refusal_direction_llama_L17` and `L18`. No file was edited; no job was launched.
