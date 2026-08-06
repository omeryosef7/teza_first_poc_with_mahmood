# P3 READINESS — Attention causality, extended (B1)

Scope: plan `reports/CAUSAL_CONTINUATION_MASTER_PLAN.md:549-561` ("## P3"). Code/infrastructure inventory
only. No job launched, no existing file modified. All paths absolute-relative to
`/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood/doublespeak_causality`.

**Bottom line: P3 is ~85% built.** The knockout primitive, the eager loading, the per-head/band scan, the FC
readout, three of the four source sets and the firing control all exist and have already run to completion
(jobs 703327 / 703334 / 703335). The *only* genuinely missing piece is what the plan says it is: a
**destination selector**, plus the fact that the decision-point destination needs a *different prompt form*
and therefore a *different readout* than the forced-choice one. No new script is required.

---

## 1. Every existing attention-knockout / edge-ablation implementation

### 1.1 The primitive (one, shared)

| what | file:line | notes |
|---|---|---|
| `class AttentionKnockout` | `pair_common.py:436` | The single mask-based knockout in the repo. Blocks `query_positions → blocked_keys` per layer, optionally per head. |
| ctor `(model, layer_idxs, query_positions, blocked_keys, heads=None)` | `pair_common.py:448-455` | `heads=None` = all heads; a head list expands the mask over the **query**-head axis (GQA note in the docstring, `pair_common.py:443-447`). |
| the hook body | `pair_common.py:457-477` | `forward_pre_hook(with_kwargs=True)` on `layer.self_attn`; clones the 4-D additive mask and writes `finfo.min` at `[0, h, qp, kp]`. |
| mask-shape guard | `pair_common.py:458-462` | raises `RuntimeError` naming `attn_implementation='eager'` if the mask is `None` or not 4-D. |
| batch guard | `pair_common.py:463-464` | `NotImplementedError` for batch > 1. |
| synthetic unit tests (GPU-free) | `tests/test_attnknockout_synthetic.py:113-290` | covers SDPA footgun, exact-cell edit, head subset, causal guard, per-layer selectivity, no caller-mask mutation, handle cleanup. |

### 1.2 Call sites / experiment drivers

| script | file:line | destinations used | sources used | heads |
|---|---|---|---|---|
| **`scripts/phase4_edge_knockout.py`** — the actual B1 experiment | call sites `:144`, `:148`, `:154` (band), `:161`, `:166` (per-head) | `qdest = query_pos + [seqlen-1]`, built at `:120-121` | demo-codeword positions (`:91`), count-matched random (`:129-134`), **all previous keys** (`allsrc = range(min(qdest))`, `:152-156`) | per-head scan `:159-169`; band (all heads × `--layers`) `:140-157` |
| `scripts/phase4c_carryedge.py` — carry-head answer→demo edges | `:91` (`ko_ctx`), used `:107`, `:111`, `:114` | **answer position only** (`ans = seqlen-1`, `:105`) | demo codewords (`:102`), count-matched random (`:109-110`), **all previous keys** firing control (`KO_all`, `:114`) | fixed `--carry` head list, grouped per layer (`:56-59`) |
| `36_pair_attention.py --mode knockout` — the fixed-pair sweep | `:221` | **query codeword only** (`q = [pos.codeword_last]`, `:191`) | `SOURCE_SETS` at `:49-50` / `source_positions()` `:53-115` | `all_layers` / `per_layer` / `head_groups` / `per_head` at `:208-219` |
| `09_attention_knockout.py` — legacy, whole-mask build | `build_mask` `:41-51`, applied `:158-160` | **final codeword only** (`cw_last`, `:101`) | `prev_codewords`, `demos_only`, `request_only`, `rand_before`, `rand_demos_matched` (`:141-148`) | all heads (mask head-dim 1) |
| `10_layerwise_knockout.py` — legacy, per-layer hook | `make_block_hook` `:37-59`, applied `:62-83` | **final codeword only** (`cw_last`, `:131`) | demo region only (`:139`) | all heads (`am[0, 0, cw_pos, k]`, `:56`) |
| `next7_attention_retrieval.py` — **descriptive, not a knockout** | `:56-60` | reads attention mass at `pos.codeword_last` | reuses `36_pair_attention.source_positions` | mid-band mean |
| `scripts/phase4b_pattern.py` — attention **pattern** patching (the dual of knockout) | `_EagerAttnCapture` `:101`, `_EagerAttnPatch` `:145` | FC answer position (`qpos`) | donor rows: benign / uniform / random head / self | explicit `--heads` list |
| `next5_w4_knockout_reduce.py` | `:1-116` | analysis-only reducer for `36_pair_attention` knockout runs | — | — |

Nothing else in the repo ablates attention edges. `scripts/phase5_head_zpatch.py` / `scripts/phase5b_qkv.py`
patch head **activations**, not edges, and are P4's problem, not P3's.

---

## 2. Does anything already support choosing the DESTINATION?

**No. There is no `--destination` / `--dest` flag anywhere in the repo** (verified by grep over all `*.py`:
the only hits are the three comments in `scripts/phase4_edge_knockout.py:80,120,129`).

How the destination is specified today — always hard-coded:

* `scripts/phase4_edge_knockout.py:120-121`
  `qdest = sorted(set(query_pos + [seqlen - 1]))` — the request-line **query codeword** ∪ the **FC answer
  position**, fused into one destination set and never separable. This is exactly the coverage gap the plan
  names.
* `scripts/phase4c_carryedge.py:105` `ans = ds_tok["input_ids"].shape[1] - 1` — answer position only.
* `36_pair_attention.py:191` `q = [pos.codeword_last]` — query codeword only.
* `09_attention_knockout.py:101` / `10_layerwise_knockout.py:131` — final codeword only.

**Important structural point about the "decision token".** In the FC prompt form used by
`phase4_edge_knockout.py` the *final prompt token* and the *FC answer position* are the **same index**
(`seqlen - 1`, `:94`, `:121`) — appending the FC question makes the last prompt token the answer slot. So
"final prompt token" is **not** a new destination inside the FC prompt; it is already covered.

The genuinely uncovered destination is the **decision point of the behavioral prompt**: the last token of
`dc.apply_template(..., add_generation_prompt=True)` on the *unmodified Doublespeak prompt* (no FC question),
i.e. the position whose logits produce the first generated token — where §8's refusal decision is read
(`scripts/phase_refusal_projection.py:7-9`, `scripts/phase_write_refusal_interaction.py:65-71`). Reaching it
requires a second prompt form **and** a readout that exists at that position (there is no concept/codeword
label there), not merely a different index.

**The position helper already exists and is exactly right:**

* `pair_common.PairPositions.final_prompt` — `pair_common.py:49`, set at `pair_common.py:89` (`n - 1`).
* `pair_common.PairPositions.get("first_generated")` — `pair_common.py:52-56`, returns `final_prompt`
  with the correct comment ("the token generated right after the prompt is produced FROM final_prompt").
* `pair_common.resolve_positions(lm, templated_text, probe_word)` — `pair_common.py:64-91`, returns
  `codeword_all`, `codeword_last`, `following`, `final_prompt`, `seq_len` in one call.

So all three plan destinations {query codeword, final prompt token, decision token} are *resolvable* today;
none of them is *selectable* today.

---

## 3. Is eager attention asserted?

**Partially. There is exactly one hard assertion in the repo, and it is not in the knockout path.**

| site | file:line | strength |
|---|---|---|
| `_require_eager(model)` — reads `model.config._attn_implementation`, raises if `!= "eager"` | `scripts/phase4b_pattern.py:92-98` | **hard config assertion**. Used only by the *pattern*-patching primitives (`:108`, `:157`). |
| `AttentionKnockout._pre` mask-shape check | `pair_common.py:458-462` | **indirect / late**: raises only if the mask it receives is `None` or non-4-D. It does not read `_attn_implementation`. |
| load-time comments | `scripts/phase4_edge_knockout.py:55`, `scripts/phase4c_carryedge.py:53`, `36_pair_attention.py:150` | callers pass `attn_implementation="eager"`, but nothing verifies it afterwards. |
| the default that makes this dangerous | `ds_common.load_model(..., attn_implementation: str = "sdpa")`, `ds_common.py:372` | every script that forgets the kwarg silently gets SDPA. |
| plan's own statement of the hazard | `reports/CAUSAL_CONTINUATION_MASTER_PLAN.md:142-143` (§0.9) | "`AttentionKnockout` **silently no-ops under SDPA** and `ds_common.load_model` defaults to `sdpa`." |

**Verdict: a true eager assertion is ABSENT from the knockout path.** The shape guard is a decent net (under
SDPA/flash HF often hands `self_attn` no mask at all → loud `RuntimeError`), but it is not equivalent: if the
backend *does* pass a 4-D mask the guard passes and the edit's effect is backend-dependent, and the guard
fires per-forward rather than at setup. P3's plan text says "Eager attention, asserted" — satisfy it by
calling the existing `_require_eager` (or a 3-line copy) at model-load time in the driver, and by recording
`model.config._attn_implementation` into `summary.json`. Env note: `transformers 5.12.1`, `torch 2.7.1+cu126`.

---

## 4. Plan source sets — what already exists as a helper

| plan source set | exists? | file:line |
|---|---|---|
| **demo codewords** | ✅ | `scripts/phase4_edge_knockout.py:91` (`demo_pos`, offset-filtered to before the request); `scripts/phase4c_carryedge.py:75`; `36_pair_attention.source_positions(..., "prev_codewords")` `:88-89`. Underlying finder: `ds_common.find_word_occurrences_in_text` `:650` (offset-based, returns `spans`/`first_idx`/`last_idx`, `ds_common.py:431-441`). |
| **demo binding spans** | ⚠️ **partial — no helper for "span", only "line" and "whole demo block"** | Closest existing pieces: per-demonstration **line** spans via the newline split in `36_pair_attention.py:92-100` (`demos_first` / `demos_last`); whole-demo-block span `demos = range(0, req_start)` `:86` with the boundary resolver `ds_common.request_start_token` `:571` (+ the templated-string fallback `36_pair_attention.py:66-85`). A *binding span* (the codeword-plus-its-context clause inside each demo) is **not** implemented anywhere; grep for "binding" over `*.py` returns only dataset-construction hits (`scripts/build_doublespeak_split.py:91,116,121,126`). Cheapest faithful definition to add: for each demo-codeword occurrence, the token range of the demo **line** containing it — ~8 lines, reusing `hit.spans` + the newline scan already written at `36_pair_attention.py:94-95`. |
| **all previous keys (firing control)** | ✅ | `scripts/phase4_edge_knockout.py:152-156` (`all_query_edges`, `allsrc = list(range(min(qdest)))`); `scripts/phase4c_carryedge.py:114` (`KO_all`, `ko_ctx(ans, list(range(ans)))`). Both are already reported (`reports/PHASE4_DEMO_RETRIEVAL.md:83-87`). |
| **count-matched random** | ✅ | `scripts/phase4_edge_knockout.py:129-134` (pool = non-demo, causal, strictly before the first destination); `scripts/phase4c_carryedge.py:109-110`; `36_pair_attention.py:103-114` (with an explicit honesty note that its pool is slightly smaller than `demos_all`). |
| *(bonus)* request-only / demos-first / demos-last | ✅ | `36_pair_attention.source_positions` `:101-102`, `:92-100`. |

Head sets from the plan {all, L8–11 band, L14–21 band, train-selected induction candidates, random
count-matched}: `all` and any layer band are already expressible via `--layers` + `--mode band`
(`scripts/phase4_edge_knockout.py:46-47`, `:140-157`); a `--heads L14H4_...` parser exists at
`scripts/phase4c_carryedge.py:37-38` (`parse_heads`) and at `scripts/phase4b_pattern.py`. **A random
count-matched HEAD set does not exist** (only random *key* sets do) — ~4 lines with `rng.sample`.
**Train-selected induction candidates do not exist** — that is P4a's deliverable, and P3 must not block on it
(run P3's head axis as {all, L8–11, L14–21, random count-matched} and add the induction set later).

---

## 5. THE DECODE-SAFETY TRAP — explicit per-primitive verdict

The trap (plan §0.9, `reports/CAUSAL_CONTINUATION_MASTER_PLAN.md:136-143`; and the P10 write-up
`reports/P10_DECODE_SAFE_WRITE.md:13`): a position guard of the form
`keep = [k for k, p in enumerate(pos) if 0 <= p < seq]` is **prefill-only** — on a KV-cached decode step
`seq == 1`, every fixed prompt position is out of range, the hook contributes nothing, and the run still
prints a completed number.

### Primitives P3 would touch

| primitive | file:line of the guard | decode-safe? |
|---|---|---|
| **`pc.AttentionKnockout`** | `pair_common.py:470-471` `if qp >= am.shape[2]: continue` and `:474` `if 0 <= kp <= qp and kp < am.shape[3]` | **NO — PREFILL-ONLY, same trap class.** On a KV-cached decode step the mask is `[1, h, 1, past+1]`, so `am.shape[2] == 1` and **every** destination index > 0 is skipped → total silent no-op. Worse, the *row* index and the *absolute key* index are compared (`kp <= qp`), so if a destination of `0` were ever passed during decode the causal filter would be wrong. **This is fine for P3 as specified** (every P3 readout is a single forward over the full prompt; the decision token is scored at *prefill*, position `seq-1`), but any behavioral/`generate()` arm added to P3 would produce a vacuous null. |
| `pc.resolve_positions` / `PairPositions` | `pair_common.py:64-91` | **N/A** — pure index computation on the templated string, no hook. Safe. |
| `36_pair_attention.source_positions` | `36_pair_attention.py:53-115` | **N/A** — pure index computation. Safe. |
| `dc.find_word_occurrences_in_text` / `dc.request_start_token` | `ds_common.py:650`, `ds_common.py:571` | **N/A** — tokenizer-side. Safe. |
| `pc.semantic_score` | `pair_common.py:921-936` | **Safe by construction** — single forward, no generation. (Note: the `patches` it takes are `dc.LayerPatch`, which *is* prefill-only — irrelevant when there is no decode.) |
| the in-script FC readout | `scripts/phase4_edge_knockout.py:97-106`; `scripts/phase4c_carryedge.py:79-87` | **Safe** — one `lm.model(**tok)` forward, reads `logits[0, -1, :]`. No KV cache, no decode step. |
| the decision-token refusal readout | `scripts/phase_write_refusal_interaction.py:65-71` (`proj_last`, accepts a `ctx` of intervention context managers) | **Safe** — single forward with `output_hidden_states=True`, reads `hs[h][0, -1, :]`. This is the readout to reuse for the new destination. ⚠️ but that script loads via `dc.load_model(args.model)` (`:48`) = **SDPA default** — copy the 6-line function, never the loader. |

### Prefill-only primitives P3 must NOT reach for (documented so the trap is not re-entered)

`pc.ComponentOutSwap` `pair_common.py:410` · `pc.DemoStateSwap` `pair_common.py:256` ·
`pc.SubmodulePatch` `pair_common.py:325` · `pc.ZHeadPatch` `pair_common.py:538` ·
`dc.LayerPatch` `ds_common.py:929` — all five carry the guard, all five are prefill-only.

### Genuinely decode-safe primitives (for reference, none needed by P3 as scoped)

`pc.AllPositionZHeadAblate` `pair_common.py:553` (mode `"zero"`; mode `"mean"` is prefill-only, see the NOTE
at `:562-564`) · `pc.AllPositionMLPAblate` `pair_common.py:742` (modes `zero`/`scale`/`project_out`;
`mean` prefill-only) · `pc.AllPositionProjectOut(MultiLayer)` `pair_common.py:664`/`:692` ·
`pc.AllPositionAdd(MultiLayer)` `pair_common.py:852`/`:872`.

**Statement required by the task:** for P3 as the plan scopes it (forward-only readouts at prompt positions),
**every primitive in the path is decode-safe *because no decode ever happens***. `AttentionKnockout` itself is
**not** decode-safe and must never be used inside `generate()`; if P3 later grows a behavioral arm, it needs an
all-timestep mask hook that does not exist yet.

---

## 6. SMALLEST CHANGE THAT UNBLOCKS P3

**Do not write a new script.** Add flags to `scripts/phase4_edge_knockout.py` — it already has the eager load,
the band/per-head scan, the demo/random/all-previous sources, the FC readout, the validity filter, the paired
bootstrap aggregation, and a working SLURM wrapper.

**Edit 1 — `scripts/phase4_edge_knockout.py` (~60 lines, additive, all defaults preserve today's behavior):**

1. `--destinations` (comma list, default `query_cw,answer` = today's fused set at `:121`).
   Replace the hard-coded `qdest` at `:120-121` with a dict built from the values `build_fc` already returns
   (`:95`): `query_cw → query_pos`, `answer → [seqlen-1]`, `final_prompt → [seqlen-1]` (alias; identical in the
   FC form — record it as such rather than double-counting), and emit `destination` as a row field so the
   existing aggregator can group on it.
2. `--prompt-form {fc,decision}` (default `fc`). `decision` skips the FC question entirely and builds
   `dc.apply_template(lm.tokenizer, r["prompt"], add_generation_prompt=True)`; the destination is
   `pc.resolve_positions(lm, templated, r["codeword"]).final_prompt` — the helper at `pair_common.py:89` /
   `.get("first_generated")` at `:52-56` already returns exactly this index.
3. `--readout {fc,refusal_proj}` (default `fc`). `refusal_proj` = the 6-line `proj_last` copied from
   `scripts/phase_write_refusal_interaction.py:65-71` (last-token residual · per-layer refusal direction from
   `outputs/refusal_alllayers/`), **plus** the `pc.norm_matched_random` control (`pair_common.py:958`) that
   §0.10 requires, since those directions are unvalidated. This is what makes the decision-token destination
   readable at all — there is no concept/codeword label at that position.
4. `--sources` (comma list, default `demo_cw,random,all_previous` = today's three cells at `:144/:148/:154`),
   plus one new value `binding_span` = the demo **line** containing each demo-codeword occurrence, built with
   the newline scan already written at `36_pair_attention.py:94-95`.
5. **Assert eager**: call `_require_eager`-equivalent (`scripts/phase4b_pattern.py:92-98`) right after
   `dc.load_model(..., attn_implementation="eager")` at `:55`, and write
   `model.config._attn_implementation` into `summary.json`.
6. *(recommended, 4 lines)* `--rand-heads N` for the count-matched random **head** set the plan asks for.

**Edit 2 — `slurm/run_phase4_edgeko.sh` (2 lines):** pass `--destinations "$DSDEST" --prompt-form "$DSFORM"
--readout "$DSREADOUT" --sources "$DSSRC"` and add the four `: "${VAR:=default}"` defaults. The existing
comma-guard loop at `:41-43` must be extended to the new vars, or better, keep using the
underscore/dash-range trick the file already uses for `DSLAYERS` (`:44-45`) — **`--export` truncates
comma-list values**, which has already bitten this project (memory: `feedback_sbatch_export_comma`).

**What must NOT change:** `pair_common.AttentionKnockout` itself needs no modification — it already takes an
arbitrary `query_positions` list. The whole P3 gap is a caller-side selector.

---

## 7. Launch command

**NOT-READY** — the two edits above do not exist yet, and this task is inventory-only (no file may be modified
and no job may be launched). Once Edit 1 + Edit 2 land, the launch is (band arms first, both cohorts, no
SLURM dependencies, ≤ 6 parallel, L40S-only per the standing rules):

```
# 1. decision-point destination, refusal readout, ClearHarm  (the NEW cell)
sbatch --export=ALL,DSBENCH=doublespeak_causality/data/bench/bench_clearharm.json,DSNPROMPTS=0,DSLAYERS=8-11,DSMODE=band,DSFORM=decision,DSREADOUT=refusal_proj,DSDEST=final_prompt,DSSRC=demo_cw slurm/run_phase4_edgeko.sh
# 2. same, L14-21 carry band
sbatch --export=ALL,DSBENCH=doublespeak_causality/data/bench/bench_clearharm.json,DSNPROMPTS=0,DSLAYERS=14-21,DSMODE=band,DSFORM=decision,DSREADOUT=refusal_proj,DSDEST=final_prompt,DSSRC=demo_cw slurm/run_phase4_edgeko.sh
# 3-4. the same two on the curated cohort (bench_curated.json)
# 5-6. FC-form destination split (query_cw vs answer, previously fused) as the continuity check
sbatch --export=ALL,DSBENCH=doublespeak_causality/data/bench/bench_clearharm.json,DSNPROMPTS=0,DSLAYERS=8-11,DSMODE=band,DSFORM=fc,DSREADOUT=fc,DSDEST=query_cw,DSSRC=demo_cw slurm/run_phase4_edgeko.sh
```

Sources must be swept one value per job (`DSSRC=demo_cw` / `random` / `all_previous` / `binding_span`) unless
the script loops internally — prefer the internal loop (today's script already runs all three source cells per
prompt, `:144-156`), in which case `DSSRC` can carry a dash-joined list expanded inside the wrapper, exactly
like `DSLAYERS`.

**Smoke first:** `DSNPROMPTS=2, DSLAYERS=8-11, DSMODE=band` — the measured smoke (job 703327) was ~10 min
wall including model load.

---

## 8. Blockers / risks

1. **No `--destination` selector anywhere** (§2). The single true blocker; Edit 1 removes it.
2. **The decision-token destination needs a new readout, not just a new index** (§2). The FC label pair does
   not exist at the decision token. Mitigation is a 6-line copy of `proj_last`
   (`scripts/phase_write_refusal_interaction.py:65-71`).
3. **Per-layer refusal directions are unvalidated** (plan §0.10, `:145-149`). Any `refusal_proj` readout must
   ship the `pc.norm_matched_random` control (`pair_common.py:958`) in the same run, and must not claim a
   per-layer localization.
4. **Eager is not asserted in the knockout path** (§3). A future caller that forgets
   `attn_implementation="eager"` gets SDPA by default (`ds_common.py:372`); the shape guard usually raises but
   is not a substitute for a config assertion.
5. **`AttentionKnockout` is prefill-only** (§5). Safe for P3 as scoped; fatal for any `generate()` arm.
6. **`slurm/run_ds_p4ce.sh` is broken** — the `python -u ... phase4c_carryedge.py` invocation at the end is
   followed by an orphan continuation line (`--granularity "$DSGRAN" --positions ...`) copy-pasted from
   `run_phase3_demoko.sh`; under `set -euo pipefail` that line runs as a command and fails. P3 should use
   `slurm/run_phase4_edgeko.sh`, which is clean. (Reported, not fixed — no modifications permitted here.)
7. **No v3 semantic bench.** `data/bench/` holds only `bench_clearharm.json`, `bench_clearharm_v2.json`,
   `bench_curated.json`; the v3 split (`data/splits/clearharm_doublespeak_v3.json`,
   `data/behavioral_v3/`) has **no** `bench["semantic"]` counterpart. P3 therefore runs on the same two
   cohorts B1 used — which is correct for a coverage extension of an existing negative, but P3 cannot be
   quoted as a v3 result.
8. **Train-selected induction heads do not exist** (P4a's job). P3's head axis must run without them.
9. **`--export` comma truncation** (project memory). Every new comma-list flag must be expanded inside the
   wrapper, as `DSLAYERS` already is (`slurm/run_phase4_edgeko.sh:44-45`).

---

## 9. Cost estimate

Measured baseline from the completed B1 jobs (`logs/ds_edgeko_703334.out`, `logs/ds_edgeko_703335.out`):
band mode over `L8-11`, n = 83 prompts, 5 forwards/prompt → **~2 min of compute**, ~10 min wall including
model load; the n = 2 per-head scan (4 layers × 32 heads × 2 cells = 1024 forwards) also ran in ~10 min wall.
That is ≈ 0.3–0.5 s per full-prompt forward on an L40S.

* **Band grid, per cohort per layer-band:** 3 destinations × 4 sources × ~85 prompts ≈ 1 000 forwards
  ≈ **8 min compute / ~20 min wall**. Two layer-bands × two cohorts = **4 jobs, ≤ 30 min each** — well inside
  the wrapper's 4 h default. This is the whole headline P3 deliverable.
* **Per-head scan** (if wanted): restrict to the **decision** destination × {demo_cw, all_previous} over
  L8–11 ∪ L14–21 = 12 layers × 32 heads × 2 sources × 85 prompts ≈ 65 000 forwards ≈ **6–9 h** → run at
  `DSNPROMPTS=25` (≈ 2 h) or split across 2–3 jobs. Do **not** attempt 32 layers × 32 heads × 4 sources ×
  3 destinations (≈ 10⁶ forwards, ~5 days).
* **Total to close P3: ~4 GPU-hours**, 4–6 jobs, one L40S each, `--cpus-per-task=4 --mem=48G` (the measured
  fast-allocating footprint documented in `slurm/run_phase4_edgeko.sh:14-18`).

---

## 10. Confidence

**High** on the inventory (§1–§5): every claim is grounded in a read of the file at the cited line, and the
knockout surface is small and fully enumerated. **Medium** on the cost estimate for the per-head extension
(extrapolated from an n = 2 smoke, and prompt length varies across cohorts). **Medium-high** that Edit 1 + 2 is
genuinely sufficient — the one judgement call is that the decision-token cell needs the refusal-projection
readout, which is a design decision the plan implies (§8's decision point) but does not spell out.
