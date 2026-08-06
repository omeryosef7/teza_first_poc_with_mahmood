# P4b + P5 — maximum-feasible scope, verified cell inventory, and per-phase job tables

**Purpose.** P4b and P5 are *not* being narrowed away. This document replaces the "infeasible /
blocked" verdicts in `reports/readiness/P4_READINESS.md` §6 and `reports/readiness/P5_READINESS.md`
§4 with a concrete, costed, launchable program, and corrects the arithmetic and the reuse claims
those two documents rest on.

**Method.** Every cost constant below is *derived* from a completed run in this repo (out-dir
creation → last `raw.jsonl` write, model load excluded), not assumed. Every structural claim is
verified against the on-disk config or the source, with `file:line`. No job was launched, no
existing file was edited, nothing was committed.

**Headline.** The literal P4b spec is **not** 440 GPU-h — it is **≈108 GPU-h** at one readout once
GQA, the z ≡ head-result identity, and the collapsed position sets are accounted for. The
*recommended* staged program is **P4b ≈ 15.7 GPU-h in 11 jobs** and **P5 ≈ 4.9 GPU-h in 5 jobs**,
**20.6 GPU-h total**, every job ≤ 2.1 h of compute, ≤ 2 concurrent, ≈ 12 h of wall clock.

---

## 0. Measured planning constants (derived, not assumed)

| constant | value | derivation |
|---|---|---|
| `t_plain` — SDPA forward, hooks on ≤ 32 modules, ~250 tok | **0.040 s** | `outputs/phase5_headz_clearharm_20260803_124603_704131`: out-dir ts 12:46:03 → `raw.jsonl` mtime 13:14:38 = 1 715 s for 44 204 rows + 344 per-item forwards ⇒ 0.0385 s. Curated (269 tok, 704130): 1 088 s / 26 418 ⇒ 0.0412 s. |
| `t_frozen` — `FreezeAllHeadsExcept` + `FreezeMLP` (64 hooks) | **0.11 s** | `phase7_directtotal_clearharm_…704726`: 240 s for 1 720 plain + 1 720 frozen + 172 capture ⇒ 0.095 s. Curated 704725: 189 s ⇒ 0.139 s. Plan at 0.11 s. |
| `t_eager` — wrapped `eager_attention_forward` | **0.18 s** | `outputs/phase4b_pattern_clearharm_20260804_021315_707474`: 02:13:15 → 02:15:41 = 146 s for ~920 eager forwards ⇒ 0.159 s. Plan at 0.18 s. |
| model load | **≈ 9 min/job** | 704130/704131: 12:37:26 → 12:46:03 = 8 m 37 s. `ds_edgeko_703327`: 07:15:25 → 07:24:34 = 9 m 09 s. |
| FC prompt length, `bench_clearharm.json` | **min 166 / med 246 / max 296 tok** | tokenized here; `demo_block_of` + FC question + chat template. Full-DS-prompt convention: med 268 / max 316. Curated is longer: med 265 / max 345. |

`P4_READINESS.md:502-507` used 20 f/s SDPA and 5 f/s eager including model load. The
load-excluded rates are **25 f/s SDPA** and **5.5–6.3 f/s eager**. Plans below use the conservative
0.040 / 0.11 / 0.18 s.

---

# PART A — P4b

## A1. The GQA claim: VERIFIED, with the exact numbers

### A1.1 From the model config on disk

`…/.cache/huggingface/hub/models--meta-llama--Llama-3.1-8B-Instruct/snapshots/0e9e39f249a16976918f6564b8830bc894c89659/config.json`:

```
num_attention_heads   = 32
num_key_value_heads   =  8          <-- GQA, group size 4
num_hidden_layers     = 32
hidden_size           = 4096        -> head_dim = 4096/32 = 128
head_dim              = <absent>    -> derived, see A1.2
attention_bias        = false       <-- load-bearing, see A3
```

`ds_common.py:70` pins `PRIMARY_MODEL = "meta-llama/Llama-3.1-8B-Instruct"`, so this is the config
every script in scope loads.

### A1.2 From `pair_common`'s head-dim helper

```python
# pair_common.py:501-506
def _attn_head_dims(model):
    cfg = model.config
    n_heads = int(cfg.num_attention_heads)                       # 32
    hidden  = int(getattr(cfg, "hidden_size", None) or cfg.n_embd)
    head_dim = int(getattr(cfg, "head_dim", 0) or (hidden // n_heads))   # 4096//32 = 128
    return n_heads, head_dim
```

`_attn_head_dims` **only ever sees `num_attention_heads`** — it is the helper for the `o_proj`
INPUT (the per-head concat `z`), and the comment at `pair_common.py:495-500` states the reason
explicitly: *"GQA shrinks the K/V heads, NOT this tensor — it is over `num_attention_heads`."* So
`ZHeadPatch` (`:509`), `ZHeadCapture` (`:601`), `AllPositionZHeadAblate` (`:553`) and
`50_path_patching.ZHeadPatchMulti` (`:114`) are all legitimately **32-wide**.

The K/V helper is a different function and it reads the *other* config field:

```python
# scripts/phase5b_qkv.py:70-80
def _qkv_head_counts(model):
    n_q  = int(cfg.num_attention_heads)                          # 32
    n_kv = int(getattr(cfg, "num_key_value_heads", n_q))         #  8
    head_dim = int(getattr(cfg, "head_dim", 0) or (hidden // n_q))   # 128
    return n_q, n_kv, head_dim

def _proj_n_heads(proj, n_q, n_kv):
    return n_q if proj == "q" else n_kv                          # k/v -> 8
```

and the mapping from a query head to the KV slice it reads is written out at

```python
# scripts/phase5b_qkv.py:216
group = n_q // n_kv                       # = 4
# scripts/phase5b_qkv.py:286-288
kv = h // group                           # query head h -> KV head kv
head_of = {"q": h, "k": kv, "v": kv}
nheads_of = {"q": n_q, "k": n_kv, "v": n_kv}
```

`QKVHeadPatch.__init__` (`phase5b_qkv.py:140-144`) then *range-checks against 8* for `k`/`v`, so a
literal 32×32 K/V matrix does not merely lose meaning — 24 of every 32 cells would raise
`IndexError`.

### A1.3 Verdict

**The K/V-per-query-head cell is structurally impossible and the P4_READINESS claim is correct.**
The K/V panel is **32 layers × 8 KV heads = 256 cells**, not 1 024. `phase5b_qkv.py:353` labelling
those rows `L{l}H{h}` (query-head indices) is a mislabel, and it has a live consequence — see A1.4.

### A1.4 New finding: the existing K/V rows are duplicated, not just mislabelled

For the canonical carry set (`phase5b_qkv.py:202-203`)
`L14H4, L14H5, L14H23, L15H8, L17H27, L18H20, L21H10`, `h // 4` gives KV heads
`1, 1, 5, 2, 6, 5, 2`. **L14H4 and L14H5 map to the same KV head 1 in the same layer 14** — the `k`
and `v` interventions at `phase5b_qkv.py:292-311` are then *bit-identical* for those two rows, but
are written out as two separate cells and consumed as two independent members of the CI /
significance family at `:337-353`. Failure scenario: a real KV effect at L14 kv-head 1 is reported
as two concordant hits at "L14H4" and "L14H5", inflating an apparent per-head replication that is
one measurement counted twice; conversely a Holm family sized 7 for K/V is really sized 5.
**Severity: MEDIUM** (the run is already retracted, but this must not be reproduced in P4b).

---

## A2. Is a GROUP-level K/V patch a valid substitute? — **It is not a substitute. It is the correct object.**

Under GQA there is no per-query-head K or V state in the model. `k_proj`/`v_proj` emit
`num_key_value_heads * head_dim = 8 × 128` (`phase5b_qkv.py:62-63`); the 32-way expansion happens
inside attention via `repeat_kv` (`phase4b_pattern.py:33-37` names it). Patching KV head *g* is
therefore an **exact and complete** intervention on the K/V channel — nothing is approximated, and
no state is left un-patched. It is simply a **coarser unit of attribution**.

| | claim you can make | claim you cannot make |
|---|---|---|
| **KV-group patch is NULL at (L, g)** | K/V mediation is ruled out for **all four** query heads `4g…4g+3` at layer L. This is a *stronger* null than a per-head null would be. | — |
| **KV-group patch is a HIT at (L, g)** | The K/V channel of group *g* at layer L is necessary. | *Which* of the 4 query heads in the group depends on it. |

**What is lost by not doing K/V-per-head, precisely:**

1. **Within-group resolution on positive results only.** 4-fold ambiguity, and only for the cells
   that fire. Nulls lose nothing.
2. **The carry-head narrative granularity.** L14H4/L14H5 (group 1) and L15H8/L21H10 (group 2) and
   L14H23/L18H20 (group 5) can never be separated on the K/V channel. Of the 7 canonical carry
   heads, only one collision is *within* a layer (L14H4/H5), so the practical loss is one
   distinction.
3. **Nothing else.** The Q channel *is* per query head (32 wide, `_proj_n_heads` returns `n_q`),
   and the pattern channel *is* per query head (`phase4b_pattern.py:35-37`: `attn_weights` is over
   `num_attention_heads`). So query-head resolution survives on 3 of the 4 attention channels
   (pattern, Q, z); only K and V are coarse.

**Recovering within-group resolution, if it is ever needed.** It is technically constructible in
the eager path only: `_EagerAttnPatch` (`phase4b_pattern.py:143-190`) already calls
`self._repeat_kv(value, n_rep)` at `:181`, i.e. it materialises the **post-`repeat_kv`** 32-wide
value tensor. A wrapper could patch that expanded tensor per query head. **Do not report this as a
component ablation.** After `repeat_kv` the tensor is not model state — it is a broadcast view — so
patching one of its 32 slices is a *path/edge* counterfactual ("what if query head *h* alone saw
different values?"), not a necessity test on any component. If P4b ever wants it, it must be
labelled an edge intervention, costed at `t_eager` (4.5× SDPA), and it does **not** belong in the
same Holm family as the group-level necessity cells.

**Recommendation: run group-level K/V (32 × 8), report it as `L{l}KV{g}` with the member query
heads listed, and state the 4-fold resolution limit in the caption.**

---

## A3. Two further cell-count corrections (both reduce scope, both verified)

### A3.1 `head result` ≡ `z` — the 6th activation type is redundant

`config.json` has `attention_bias: false`, so `o_proj` is a bias-free linear map and its input is
the per-head concat (`pair_common.py:495-498`). Head *h*'s contribution to the residual is exactly
`z_h @ W_o^{(h)}`, and the blocks are additive. Replacing `z_h` with a donor `d` therefore replaces
head *h*'s result with `d @ W_o^{(h)}` and touches nothing else — i.e. **a z-patch and a
head-result patch are the same intervention expressed in two bases.** The plan's
`{pattern, Q, K, V, z, head-result}` (`CAUSAL_CONTINUATION_MASTER_PLAN.md:577`) is **5 distinct
channels, not 6**. This alone deletes 1 024 cells × every position set × every arm.

*(Caveat to record in the manifest: this holds for `o_proj` **without** bias. It would not hold on
a model with `attention_bias: true`, so the manifest should assert `config.attention_bias == False`
at run time.)*

### A3.2 The five position sets are four — and I measured the sets

The plan's sets are `{demo codewords, query codeword, decision token, answer position,
all codewords}` (`:577-578`).

* **`decision token` ≡ `answer position`.** Under the FC readout the prompt ends at the probe
  question and the decision *is* the last token (`phase5_head_zpatch.py:111`,
  `phase4b_pattern.py:266`, `phase7_direct_total.py:123`). They separate only in a generation
  harness, which P4b does not use. **5 → 4.**
* **`all codewords` = `demo` ∪ `query`** by construction, so it is a derived set, not an
  independent one; keep it (it is the union arm the plan asks for) but note it adds no new
  resolution.

Measured on all 86 DOUBLESPEAK items of `data/bench/bench_clearharm.json`, using the
`phase6_mlp_causal.py:126-131` token-index split (**not** the char/token confusion that block warns
about — I reproduced that bug once and it silently returned `query_pos = []` for 86/86 items,
which is exactly the failure mode documented at `P4_READINESS.md:124-126`):

| convention | demo positions | query positions | DS↔BENIGN demo-count mismatch | seq len (med/max) |
|---|---|---|---|---|
| `demo_block_of` + FC question (`phase5`, `phase6`, `phase4b`, `phase7`) | **12** (84/86 items; 11×1, 6×1) | **2** — the two *quoted* codewords inside the probe question | **5 / 86 (5.8 %)** | 246 / 296 |
| full DS prompt + FC question (`phase4_edge_knockout.py:80-92`) | 13 (12 demos + request-line query) | 2 | 5 / 86 | 268 / 316 |

Two consequences the manifest must pin:

1. **Under the demo-block convention the "query codeword" is a quoted token in the *probe*, not the
   retrieval destination in the *attack*.** `P4_READINESS.md:253-255` recommends the
   `phase4_edge_knockout` convention for exactly this reason — but every P4b-relevant script uses
   the demo-block convention. Pick one **in `configs/manifests/p4b.json`** and record it per row.
2. **`P4_READINESS.md:539` is wrong about donor alignment being "the norm".** It cites
   `len_mismatch = 58/59` from `logs/ds_p4bp_707474.out` as evidence that occurrence-count mismatch
   is near-universal. That statistic is **sequence-length** mismatch (`phase4b_pattern.align_row`,
   `:211-225`), a different object. The actual DS↔BENIGN **codeword-occurrence-count** mismatch is
   **5/86 = 5.8 %**. Trailing-aligned occurrence-order donors
   (`phase6_mlp_causal.py:191-203`) are still required, but as a correctness guard on 6 % of items,
   not as a redesign forced by 98 %.

### A3.3 "Both readouts" is not runnable and must be dropped

`phase5_head_zpatch.py:91-95` builds its own FC prompt from `demo_block_of(prompt)` and never reads
the bench row's `readout` field; likewise `phase5b_qkv.py:239-249`, `phase4b_pattern.py:264`,
`phase7_direct_total.py:86-88`. Every row in `bench_clearharm.json` is `readout: "fixed"` anyway
(516/516). There is exactly **one** implemented readout in this family (FC DE_context). The plan's
"both readouts" (`:578`) has no implementation and doubles a cost that cannot be paid. **P4b runs
one readout; a second readout is a separate, un-scoped piece of work.**

### A3.4 Corrected inventory

| channel | cells / layer | cells (32 L) | position sets | combos | forward cost |
|---|---|---|---|---|---|
| pattern (attn row) | 32 (query heads) | 1 024 | 3 — answer, demo, query | 3 072 | `t_eager` |
| Q | 32 | 1 024 | 4 | 4 096 | `t_plain` |
| K | **8** (GQA) | **256** | 3 — demo, query, all (answer is structurally null: nothing attends to the last token) | 768 | `t_plain` |
| V | **8** (GQA) | **256** | 3 | 768 | `t_plain` |
| z (≡ head result) | 32 | 1 024 | 4 | 4 096 | `t_plain` |
| head result | — | **0 (≡ z)** | — | 0 | — |
| **total** | | **3 584** | | **12 800** | |

**Literal-spec cost, corrected:** 12 800 combos × 86 items × 4 arms = 4 403 200 forwards.
Eager share (pattern) = 1 024 × 3 × 86 × 4 = 1 056 768 @ 0.18 s = **52.8 GPU-h**;
SDPA share = 3 346 432 @ 0.040 s = **37.2 GPU-h**. **Literal total ≈ 90 GPU-h at one readout**
(≈ 180 at the two the plan asks for). `P4_READINESS.md:516` reports **439 GPU-h**; the gap is
GQA (K/V 1024→256), the z ≡ head-result identity, 5→4 position sets, and a readout that does not
exist. Still too large to run as specified — but the correct order of magnitude matters, because it
is what makes the staged program below obviously affordable rather than a desperate trim.

---

## A4. P4b job tables

Fixed choices for every phase below:
`--bench data/bench/bench_clearharm.json` · **dev (n = 44) for the sweep, heldout (n = 42) for the
frozen confirmation only** · FC DE_context readout · validity filter
`benign_p_concept < C1 < 1 − 1e-3` (the second half is new — `logs/ds_p5bq_707412` /
`P4_READINESS.md:414-427` show the curated cohort saturates at `C1 = 0.999995`, leaving ~5e-6 of
headroom; clearharm is healthy at `C1 = 0.879 dev / 0.869 heldout`,
`logs/ds_p4bp_707474.out:6-7`) · per-cell firing record `{donor_dist, rel_donor_dist,
n_hook_calls, act_delta}` (all free — hooks and counters, no extra forward) · `--partition killable`
so **every job is sized ≤ 2.1 h of compute** and survives inside the existing 4 h default.

### Phase P4b-0 — GPU-free prerequisites (**0 GPU-h**, ~1 day of writing)

| # | item | why it gates the GPU work |
|---|---|---|
| 0.1 | `tests/test_hook_firing_synthetic.py` (new file) — assert `n_hook_calls == len(positions)` per forward, `donor_dist > 0` for a non-self donor, `donor_dist == 0.0` exactly for a self donor, and `act_delta > 0` at a downstream probe. | `P4_READINESS.md:352` — *there is no activation-delta assertion anywhere in this repo*, and `selfswap_dev = 0.0` passes perfectly for a hook that never fires. Without this every null in P4b is un-attributable, which is precisely what the `phase5b_qkv.py:38-43` retraction is about. |
| 0.2 | `configs/manifests/p4b.json` enumerating all **12 800** (channel, layer, head/kv, position-set) combos with `status`, the chosen position convention, and the pre-registered Holm family structure. | `MASTER_PLAN:310` forbids launching without it. *(Correction to `P4_READINESS.md:563`: `configs/manifests/` is not empty — it holds `phase9_gcg_mac_matrix.json` — but no P4 manifest exists.)* |
| 0.3 | Pre-register the family: **one Holm family per (channel × position-set)**, i.e. 17 families of 256–1 024 cells, never one family of 12 800. | `MASTER_PLAN:296-298`; `phase5_analyze.py` currently Holm-corrects a single 1 024-cell family. A 12 800-cell family annihilates a real effect of the observed size (best dev necessity = 0.0325, `logs/ds_headz_704131.out:8`). |
| 0.4 | `python scripts/split_to_bench.py --split data/splits/clearharm_doublespeak_v3.json --out-dir data/bench_v3` (CPU-only — no `torch`/`load_model` import, `split_to_bench.py:20`). **`--out-dir` is mandatory**: the default `data/bench` writes `bench_<cohort>.json` and v3 still uses cohort `clearharm`, so it would overwrite `bench_clearharm.json`, the file every retained result was produced against. | Optional Phase P4b-6 (leakage-clean replication). |
| 0.5 | Add a `--resume-from <out_dir>` key (`sid, channel, layer, head, position_set, arm`) to whatever script P4b uses. | `phase5_head_zpatch.py:88` opens `raw.jsonl` with `"w"` and no skip logic; every wrapper defaults to `--partition=killable`. A preemption at 1 h 50 m loses 1 h 50 m. |

### Phase P4b-1 — z channel × 4 position sets (SDPA) — **the decisive experiment**

This is the first test of the L8–11 retrieval band *at the positions where it acts*
(`P4_READINESS.md:66-70`).

| item | count | forwards |
|---|---|---|
| necessity (matched BENIGN donor, occurrence-order trailing-aligned) | 1 024 cells × 4 pos × 44 items | 180 224 |
| per-item captures (DS z, BENIGN z, at all positions) + 2 readouts | 44 × 4 | 176 |
| controls on a probe grid — 8 layers × 4 heads × 4 pos × 44, arms = {self-swap, norm-matched random, **zero-donor firing control**} | 3 × 5 632 | 16 896 |
| **total** | | **197 296 @ 0.040 s = 2.19 GPU-h** |

| job | shard | compute | walltime to request |
|---|---|---|---|
| `p4b1-a` | layers 0–15 | 1.10 h | 3:00 |
| `p4b1-b` | layers 16–31 | 1.10 h | 3:00 |

2 concurrent → **1 wave, ≈ 1.3 h wall**.

**Primitive note that removes the only claimed blocker.** `P4_READINESS.md:99-104` says a
per-occurrence donor needs either N stacked `ZHeadPatch` contexts or a new `Dict[int, Tensor]`
overload. **Neither is needed: `50_path_patching.ZHeadPatchMulti` (`:114-137`) already patches head
`h` with `vecs[i]` at `positions[i]` in a single hook**, and `phase7_direct_total.py:33-35` already
shows the `importlib` incantation for loading `50_path_patching.py` (its name starts with a digit).
Zero new primitives; the `--positions` work is a ~50-line argument-plumbing change.

### Phase P4b-2 — Q channel × 4 position sets (SDPA)

Identical shape to P4b-1 (`_proj_n_heads` returns `n_q = 32` for `q`), using
`phase5b_qkv.QKVHeadPatch` with `proj="q"`.

| item | forwards |
|---|---|
| necessity 1 024 × 4 × 44 | 180 224 |
| captures + probe-grid controls | 17 072 |
| **total** | **197 296 @ 0.040 s = 2.19 GPU-h** |

| job | shard | compute | walltime |
|---|---|---|---|
| `p4b2-a` | layers 0–15 | 1.10 h | 3:00 |
| `p4b2-b` | layers 16–31 | 1.10 h | 3:00 |

**1 wave, ≈ 1.3 h wall.**

### Phase P4b-3 — K/V, GROUP-level, at SOURCE positions (SDPA) — **the retraction repair**

The standing retraction (`phase5b_qkv.py:38-43`) demands four things: patch K/V at the **source**
positions, add a **positive control that fires**, record **‖donor − self‖**, and run **full n on
both splits**. Because GQA shrinks this panel 4× (256 cells, not 1 024), **all four arms are
affordable on every single cell** — which is why this phase, not the z sweep, is where the
retraction is discharged.

Position sets are `{demo, query, all}` — the answer position is *excluded by construction*: nothing
attends to the last token, so a K/V patch there is a guaranteed structural null, which is the
positioning artifact the retraction names.

| arm | forwards |
|---|---|
| necessity (matched BENIGN K/V slice) — (256 K + 256 V) × 3 pos × 44 | 67 584 |
| self-swap (must be exactly 0) — all cells | 67 584 |
| **zero-donor firing positive control — all cells** (must move the readout, else the cell's null is un-reportable) | 67 584 |
| norm-matched random donor — all cells | 67 584 |
| **total** | **270 336 @ 0.040 s = 3.00 GPU-h** |

| job | shard | compute | walltime |
|---|---|---|---|
| `p4b3-a` | layers 0–15, K+V | 1.50 h | 3:00 |
| `p4b3-b` | layers 16–31, K+V | 1.50 h | 3:00 |

**1 wave, ≈ 1.7 h wall.** Rows must be keyed `L{l}KV{g}` with `member_query_heads: [4g…4g+3]`, and
the Holm family for this phase is **256**, not 1 024 (see A1.4).

### Phase P4b-4 — attention-pattern channel × 3 query-position sets (**EAGER**) — the expensive one

Requires `attn_implementation="eager"` (`phase4b_pattern.py:13-21`); `ds_common.load_model` defaults
to `"sdpa"` (`ds_common.py:373`), under which the patch is a silent no-op.

**Arm restriction, new and load-bearing.** `align_row` (`phase4b_pattern.py:211-225`) maps a donor
attention row onto the target by **trailing alignment + renormalisation**, and its own docstring
calls this *"APPROXIMATE across lengths"*. At the **answer** row that is defensible (both prompts
end at their own answer token). At a **demo** or **query** row it is not: the query index itself
differs between the DS and BENIGN prompts, so "the benign row for this demo" has no referent.
Therefore:

* `qpos = answer` → arms `{C_benign (donor), C_uniform, self-swap, random-head}` — the existing design.
* `qpos ∈ {demo, query}` → **donor arms are dropped**; arms are `{C_uniform (pattern-space knockout,
  needs no donor), self-swap, random-head}`. A cross-prompt donor arm at these positions would be a
  measurement of the alignment heuristic, not of the head.

| item | forwards |
|---|---|
| 1 024 cells × 3 qpos sets × 44 items (1 primary arm each) | 135 168 |
| self-swap on a 128-cell probe subset × 3 × 44 | 16 896 |
| **total** | **152 064 @ 0.18 s = 7.60 GPU-h** |

| job | shard | compute | walltime |
|---|---|---|---|
| `p4b4-a` | layers 0–7 | 1.90 h | 4:00 |
| `p4b4-b` | layers 8–15 | 1.90 h | 4:00 |
| `p4b4-c` | layers 16–23 | 1.90 h | 4:00 |
| `p4b4-d` | layers 24–31 | 1.90 h | 4:00 |

≤ 2 concurrent → **2 waves, ≈ 4.2 h wall**. Note `_EagerAttnPatch` accepts an arbitrary list of
`(layer, head, qpos, donor)` (`phase4b_pattern.py:157-162`), so all 12 demo rows of one cell are
**one** forward, not twelve — this is already reflected in the count.

### Phase P4b-5 — heldout confirmation on the train-frozen union set

Freeze the candidate set to `configs/manifests/p4b_frozen.json` **before** any heldout row is read
(`MASTER_PLAN:307`). Candidates = (dev Holm survivors across P4b-1…4) ∪ (P4a induction candidates).
Budget **k = 64** cells; assume 48 SDPA + 16 eager.

| item | forwards | cost |
|---|---|---|
| SDPA cells 48 × 4 pos × 42 items × 4 arms | 32 256 | 0.36 h |
| eager cells 16 × 3 pos × 42 × 4 arms | 8 064 | 0.40 h |
| **total** | **40 320** | **0.76 GPU-h** |

| job | shard | compute | walltime |
|---|---|---|---|
| `p4b5` | all frozen cells, heldout | 0.76 h | 2:00 |

**1 wave, ≈ 0.9 h wall.**

> **Honesty note that must appear in the artifact.** `bench_clearharm.json` derives from
> `clearharm_doublespeak_v1.json` (`_meta.source_split`), and `MASTER_PLAN §0.4` records that 14/43
> concepts and 17/21 codewords straddle its train/test boundary. A heldout result on this bench is
> a **held-out-items** result, not a held-out-concepts result. Phase P4b-6 fixes this.

### Phase P4b-6 (optional, recommended) — leakage-clean replication on the v3 split

After P4b-0.4 builds `data/bench_v3/bench_clearharm.json` (324 examples: 162 train / 82 dev /
80 test). Replicate **only** the decisive z-channel sweep on train (subsample n = 48 to hold cost
flat) and confirm the frozen set on the 80-item test split.

| item | forwards | cost |
|---|---|---|
| z × 4 pos × 48 train items + controls | 215 232 | 2.39 h |
| frozen 64 cells × 4 pos × 80 test × 4 arms (SDPA share) | 61 440 | 0.68 h |
| **total** | | **3.07 GPU-h** |

| job | shard | compute | walltime |
|---|---|---|---|
| `p4b6-a` | v3 train, layers 0–15 | 1.20 h | 3:00 |
| `p4b6-b` | v3 train, layers 16–31 | 1.20 h | 3:00 |
| `p4b6-c` | v3 test, frozen set | 0.68 h | 2:00 |

**2 waves, ≈ 2.0 h wall.**

### P4b totals

| phase | GPU-h | jobs | waves (≤ 2 concurrent) |
|---|---|---|---|
| P4b-0 prerequisites | 0.00 | 0 (CPU) | — |
| P4b-1 z × 4 positions | 2.19 | 2 | 1 |
| P4b-2 Q × 4 positions | 2.19 | 2 | 1 |
| P4b-3 K/V group × 3 positions (retraction repair) | 3.00 | 2 | 1 |
| P4b-4 pattern × 3 qpos (eager) | 7.60 | 4 | 2 |
| P4b-5 heldout confirmation | 0.76 | 1 | 1 |
| **core subtotal** | **15.74** | **11** | **6** |
| P4b-6 v3 leakage-clean replication (optional) | 3.07 | 3 | 2 |
| **with P4b-6** | **18.81** | **14** | **8** |

Wall clock, core: **≈ 8.5 h** (waves 1.3 + 1.3 + 1.7 + 4.2 + 0.9, plus 9 min load per job already
included in each job's requested walltime).

### What P4b still cannot deliver, stated plainly

1. **Within-KV-group query-head resolution** (A2) — 4-fold ambiguity on positive K/V cells only.
2. **A second readout** (A3.3) — not implemented anywhere in this family.
3. **`decision token` as distinct from `answer position`** (A3.2) — needs a generation harness;
   under FC they are the same token.
4. **Behavioral necessity (P4c)** — out of scope here, and constrained: `ZHeadPatch`
   (`pair_common.py:538`), `ComponentOutSwap`, `SubmodulePatch` and `dc.LayerPatch` all drop every
   position on a KV-cached decode step (`seq == 1`). The **only** decode-safe head primitive is
   `pair_common.AllPositionZHeadAblate` with `mode="zero"` — `mode="mean"` is prefill-only by its
   own docstring (`:558-560`).
5. **Cross-prompt pattern donors at non-answer rows** (P4b-4 arm restriction).

---

# PART B — P5

## B1. Two blockers that `P5_READINESS.md` does not contain

### B1.1 The AtP stack **cannot be pointed at a ClearHarm bench.** Verified, hard failure.

`P5_READINESS.md:241-249` specifies Stage A as a reuse of `51_mlp_attribution.py:94-99`. Both
`50_path_patching.py` and `51_mlp_attribution.py` route pair selection through

```python
# 48_attribution_patching.py:242-251
sem = bench["semantic"]
ds  = [r for r in sem if r["condition"] == "DOUBLESPEAK"
       and r["readout"] == readout and r["split"] == split and r.get("has_demos")]
neu = {(r["demo_style"], r["n_demos"], r["probe_word"]): r
       for r in sem if r["condition"] == "NEUTRAL_CODEWORD" … and r.get("has_demos")}
```

I checked the on-disk benches. **`has_demos` is `None` for every row of every
`data/bench/bench_*.json`** — 516/516 in `bench_clearharm.json`, 636/636 in `bench_clearharm_v2.json`,
306/306 in `bench_curated.json`. `r.get("has_demos")` is falsy ⇒ `ds` and `neu` are both empty ⇒
`_select_pair_rows` raises `ValueError("no matched DOUBLESPEAK/NEUTRAL_CODEWORD pair…")` at `:252`.

And one line earlier, `50_path_patching.py:168` / `51_mlp_attribution.py:62` do
`pair["concept"], pair["codeword"]`. In `bench_clearharm.json` the `pair` object has keys
`{cohort, kind, n_concepts, concepts, note}` — **no `concept`, no `codeword`** ⇒ `KeyError` before
the model is even used.

The field set that satisfies both (`has_demos: True`, `pair.concept`, `pair.codeword`) exists only
in `data/pair_benchmark/pair_*.json`, which is the **single-concept, n = 1 prompt-pair** benchmark
(clean_len = 123 tokens, 4 demo codewords — see
`outputs/path_patch_Llama-3.1-8B-Instruct_20260731_181722_697419/path_patching.json` `alignment`).

**Failure scenario:** a P5 Stage-A job is submitted as
`python 51_mlp_attribution.py --bench data/bench/bench_clearharm.json …`; it dies in under a second
with a `KeyError`, after a 9-minute model load, and the operator concludes the bench is corrupt.
**Severity: HIGH — it invalidates the "reuse, don't rewrite" premise of `P5_READINESS.md:241-249`.**

**Fix (cheap, but it is new code and must be budgeted):** the per-item pairing already exists in the
`phase7` idiom — `by_key = {(condition, split, sid): row}` (`phase7_direct_total.py:76`,
`phase5_head_zpatch.py:78`). P5's new script must do its own selection by `sid` and pass
`(concept, codeword)` from `r["target_concept"], r["codeword"]`, importing from `48`/`51` **only**
`build_alignment`, `align_corrupt`, `make_metric`, `pearson`, `spearman`, and `_MLPActGradCapture`.
~30 lines.

### B1.2 Node-AtP ≠ edge-AtP: the existing trust evidence does not transfer

`51`'s estimator is a **node** attribution, `AtP[L,pos] = g_mlp · (mlp_corrupt − mlp_clean)`
(`51:106-108`). It is well validated on this exact model:

| run | Pearson(AtP, true) | Spearman | trustworthy (≥ 0.7) |
|---|---|---|---|
| `outputs/mlp_atp_bomb/mlp_atp_results.json` | 0.936 | 0.905 | True |
| `outputs/mlp_atp_chlorine/…` | 0.932 | 0.914 | True |
| `outputs/mlp_atp_grenade/…` | 0.950 | 0.863 | True |

P5's Stage A needs an **edge** estimator, `AtP_edge[S→R] = g_mlp[R] · Δmlp_R(S)`, which composes a
gradient from the **clean** run with a delta measured under the **frozen** run. Two things follow
that must be written into the artifact:

1. **There is zero validation evidence for the edge estimator on this model.** The 0.93 Pearsons
   above are for nodes. Stage C (§B4) is therefore not a formality.
2. **`Δmlp_R(S)` under `FreezeAllHeadsExcept` + a capture-variant `FreezeMLP` is the *direct* S→R
   delta**, because every intermediate head and MLP is pinned to clean. It is not the total S→R
   path. Label the ranking column `AtP direct-edge rank (not a causal estimate)`, per
   `MASTER_PLAN:604-606`.

---

## B2. "Self-freeze must be EXACTLY 0" — what verifies it (and what does not)

**Nothing in the repo verifies it today.** `P5_READINESS.md:158-162` cites
`summary.json` values of `0.0`. Those are rounded and gated loosely:

```python
# scripts/phase7_direct_total.py:166-167
TOL = 0.05
trustworthy = (frz <= TOL) and (selfdev is not None and selfdev <= TOL)
# :175-176
"selfswap_max_dev":     round(selfdev, 5),
"freeze_consistency_dev": round(frz, 4),
```

So a summary `0.0` certifies only `|dev| < 5e-6` (self-swap) and `< 5e-5` (freeze consistency), and
the *gate* would have passed anything below 0.05 — a 1 000-fold slack.

**I verified exactness independently, from the unrounded raw scalars.** `raw.jsonl` stores
`TOTAL_self = m_clean − m_tot_self` and `m_frozen_clean` and `m_clean` at full float precision
(`phase7_direct_total.py:144-148`). Recomputing `max|TOTAL_self|` and
`max|m_frozen_clean − m_clean|` and counting non-zero rows:

| run | rows | `max|TOTAL_self|` | non-zero | `max|m_frozen_clean − m_clean|` | non-zero |
|---|---|---|---|---|---|
| `phase7_directtotal_clearharm_…704726` | 860 | **0.0** | **0** | **0.0** | **0** |
| `phase7_directtotal_curated_…704725` | 510 | **0.0** | **0** | **0.0** | **0** |
| `phase7_directtotal_curated_…704606` | 42 | **0.0** | **0** | **0.0** | **0** |

**1 412 rows, 3 runs, 2 cohorts, 2 splits, 10–11 heads: bit-exactly zero, every row.** The
freeze machinery is exact on-model — the *claim* in `P5_READINESS.md` is right, its *evidence* was
not.

**Why it is exact, so P5 knows when to expect it to stop being exact.**
`capture_clean_all` stashes `z` and `mlp` as fp32 (`50:147, :153`); the freeze casts back with
`.to(zr.dtype)` (`50:66`) / `.to(h.dtype)` (`50:98`). bf16 → fp32 → bf16 is a lossless round trip,
and the self-swap donor `self_v = z_clean[ls][ds_last, hs]` (`phase7:130`) comes from that same fp32
copy. Exactness therefore **depends on** (a) the clean capture and the patched forward tokenizing
the *identical* string, and (b) the donor originating from the fp32 cache rather than a re-capture.
Break either and the equality degrades to ~1e-3.

**What P5 must assert, per position set and per receiver type:**

| cell | assertion | current coverage |
|---|---|---|
| head sender, self-swap, answer position | `TOTAL_self == 0.0` exactly | ✅ verified above (1 412 rows) |
| head sender, freeze-all-clean consistency, answer position | `m_frozen_clean == m_clean` exactly | ✅ verified above |
| head sender, **multi-position** (aligned) sender set | `== 0.0` | ❌ never run — `50` patches 44 aligned positions but has **no self-freeze cell at all**, only `recon_tol` (`50:253`) |
| **MLP receiver self-swap** (`ComponentOutSwap` with the receiver's own clean rows) | `== 0.0` | ❌ never run on-model. Synthetic only (`tests/test_componentoutswap_synthetic.py`, invariant (a) at `pair_common.py:385`) |
| upstream (non-downstream) receiver edge | `== 0.0` | ❌ **structurally excluded**: `50:233` only forms edges with `L_R > L_S`, so the impossible control is never *measured*, only *skipped* |

**The gate P5 ships with:** `assert dev == 0.0` on the raw float (not `<= 1e-6`, and certainly not
`<= 0.05`), evaluated per position set and per receiver type, with the run aborted — not merely
`trustworthy: false` — if any cell is non-zero. Record the raw unrounded value in `raw.jsonl` so a
future regression cannot hide under a `round()`.

---

## B3. Which of the six path tests are CLAIMS and which are RANKINGS

`MASTER_PLAN:600-602` lists six tests. The AtP/exact boundary is set by `MASTER_PLAN:604-606`
(*"AtP never substitutes for exact patching in a claim"*).

| # | test | status | CLAIM or RANKING | what produces it |
|---|---|---|---|---|
| 1 | sender patched, downstream frozen (= DIRECT) | ✅ exists, exact, CI-grade n | **CLAIM** | `50:207-212` `direct_effect` as called by `phase7_direct_total.py:134-137` |
| 2 | sender ablated, receiver restored | ⚠ exists only MLP-sender → head-receiver (`phase7b_mediation.py:13-16`) — the reverse of P5 | **CLAIM** (new arm) | `pc.ZHeadPatch` on the sender + `pc.ComponentOutSwap(…, "mlp_out")` restoring receiver R to clean |
| 3 | receiver patched, sender clean | ⚠ head-receiver only (`50:222-225`, run 3b) | **CLAIM** (new arm) | re-inject the Stage-A-captured `Δmlp_R(S)` with `ComponentOutSwap`; **the capture is reusable from Stage A — this test costs 1 forward, not 2** |
| 4 | direct vs total | ✅ complete | **CLAIM** | `phase7_direct_total.py` whole file |
| 5 | edge necessity | ❌ not implemented for component edges (the repo's only "edge necessity" is the *attention* q→k knockout, `phase4c_carryedge.py:106-116`) | **CLAIM on the top-k family only; RANKING elsewhere** | new arm: sender free/corrupt, receiver R pinned to clean |
| 6 | edge sufficiency | ⚠ nearest analogue is head-receiver `edge_effect` (`50:214-225`) and *component* sufficiency (`phase7c_sufficiency.py:7-11`) | **CLAIM on the top-k family only; RANKING elsewhere** | new arm: everything frozen clean, only the S→R edge injected |
| — | all 6 543 edges | — | **RANKING ONLY. Never a claim.** | Stage A edge-AtP |

**Claim boundary, verbatim for `PHASE5_HEAD_TO_MLP_PATH_MATRIX.md`:**

> Every edge drawn in the causal graph carries an exact-patch effect with a bootstrap CI and a
> Holm-corrected p across the pre-registered family of *k* + *r* edges. Edges outside that family
> are reported as **"AtP-ranked, not exactly tested"**, with the false-negative rate estimated from
> the stratified random stratum. No AtP number appears without the label *"AtP rank (not a causal
> estimate)"*.

---

## B4. The AtP-rank → exact-patch-top-k decomposition, concretely

### B4.0 Sender / receiver / edge counts (exact)

| sender family | senders | Σ receivers (MLPs at `L_S+1 … 31`) |
|---|---|---|
| all L8–11 heads | 4 × 32 = 128 | 32 × (23+22+21+20) = 2 752 |
| all L14–21 heads | 8 × 32 = 256 | 32 × (17+…+10) = 3 456 |
| carry heads outside the bands (`L30H15`, `L31H0`) | 2 | 1 + 0 = 1 |
| P4a induction candidates | expected ⊂ L8–11 ⇒ **+0** (any that fall outside must be added explicitly) | 0 |
| random count-matched senders, drawn outside both bands | 20 | ≈ 334 |
| **total** | **≈ 406** | **≈ 6 543 ordered edges** |

### B4.1 Stage 0 — GPU-free, mandatory (**0 GPU-h**)

`tests/test_path_patching.py:38` uses `ToyMLP → zeros`, with the explicit comment
*"MLP == 0 → no MLP-mediated path"*. **The head→MLP path — exactly what P5 measures — has zero
synthetic coverage.** Write a **new** file `tests/test_path_patching_mlp.py` (the hard rules forbid
editing the existing test) with a non-zero *linear* toy MLP and assert:

| # | assertion | tolerance |
|---|---|---|
| a | `TOTAL == DIRECT + Σ_R EDGE_head + Σ_R EDGE_mlp` | 1e-5 |
| b | self-freeze and self-swap | **exactly 0** (`==`) |
| c | MLP-receiver self-swap via `ComponentOutSwap` | **exactly 0** (`==`) |
| d | an upstream (non-downstream) receiver edge | **exactly 0** (`==`) |
| e | multi-position sender injection (`ZHeadPatchMulti`) self-swap | **exactly 0** (`==`) |

### B4.2 Stage A — the ranking. **Produced by a new script, not by `51`.**

**Script:** `scripts/phase_p5_head_mlp_paths.py --stage atp`
(`P5_READINESS.md:271-291` sketches it; §B1.1 above adds the per-item selection it was missing).

**The one missing primitive**, exactly as `P5_READINESS.md:276-281` says — subclass, never edit `50`:

```python
class FreezeMLPCapture(pp50.FreezeMLP):
    """FreezeMLP + capture EVERY layer's recomputed mlp output BEFORE the overwrite."""
```

**The accounting lever:** one frozen forward with `sender = corrupt` yields `Δmlp_R(S)` for **all 32
receivers at once**. `50:231-235` re-runs per receiver only because `FreezeAllHeadsExcept` captures
a single head. So Stage A is **406 forwards + 1 backward per prompt**, not 6 543.

| item | per prompt |
|---|---|
| 406 frozen forwards @ 0.11 s | 44.7 s |
| 1 clean forward + 1 backward (`_MLPActGradCapture`, `51:94-99`) | 0.29 s |
| corrupt-side MLP capture + alignment (`48.build_alignment`, `48.align_corrupt`) | 0.05 s |
| **total** | **≈ 45 s** |

| job | scope | forwards | compute | walltime |
|---|---|---|---|---|
| `p5a` | concept metric, **dev only** (n = 44) — ranking on test would leak | ≈ 17 900 | **0.55 h** | 2:00 |

**Rank on dev only.** `MASTER_PLAN:307`: select on train/dev, freeze, then run the frozen
configuration on locked test.

**Memory note:** Stage A is the only phase in either part that runs a **backward** through the 8B
model. `51:63-65` carries a `--demo-cap` flag added precisely to *"shorten prompt (fewer demos) to
fit big-model backward"*. At 246 tokens on a 48 GB L40S this should fit with the standard
4 cpu / 48 G footprint, but Stage A must be smoke-tested at `--n-prompts 2` before the full job.

### B4.3 Stage B — exact patching. **This is the claim.**

**Family, pre-registered before Stage A output is inspected:**

| stratum | size | purpose |
|---|---|---|
| top-\|AtP\| edges | **k = 120** | the positive claims |
| stratified random edges — 10 drawn from each of 6 \|AtP\| deciles | **r = 60** | calibrates the null, bounds the miss rate, **and is the only source of the random-sender / random-receiver controls** |
| **Holm family** | **m = 180** | α′ = 2.78e-4; a Wilcoxon signed-rank at n = 44 reaches p ≈ 1e-13, so the family is not resolution-limited (`phase5_head_zpatch.py:160-171`) |

**Correction to `P5_READINESS.md:220-221`**, which states random-receiver and random-sender controls
are *"free — a full matrix already contains them"*. The top-k family is **not** a full matrix, and
top-\|AtP\| selection is precisely anti-correlated with randomness. **These controls are free only
because the 60-edge random stratum is deliberately drawn to supply them** — drop the stratum and
they cost extra forwards. The stratum is therefore mandatory, not optional.

Per prompt, with ≤ 60 distinct senders in the family:

| item | forwards | seconds |
|---|---|---|
| sender-level: TOTAL (plain), DIRECT (frozen), self-freeze (frozen), self-swap (plain) × 60 | 240 | 18.0 |
| edge tests 2, 3, 5 (1 plain-ish forward each) × 180 | 540 | 27.0 |
| edge test 6 (sufficiency — frozen) × 180 | 180 | 19.8 |
| non-downstream impossible control: 1 upstream receiver per sender × 2 arms | 120 | 13.2 |
| norm-matched path control on the 2 injecting tests × 180 | 360 | 21.6 |
| random sender / random receiver | 0 (⊂ the 60-edge stratum) | 0 |
| setup captures | 3 | 0.2 |
| **total** | **1 443** | **≈ 99.8 s** |

| job | scope | compute | walltime |
|---|---|---|---|
| `p5b-dev` | concept metric, dev n = 44, select | 1.22 h | 3:00 |
| `p5b-held` | concept metric, heldout n = 42, **frozen family** | 1.16 h | 3:00 |

**Stage B = 2.38 GPU-h per metric.**

**How large can *k* actually be?** *k* enters only the edge-level terms (0.26 s/edge plus 0.12 s of
norm-matched control). Sensitivity, dev + heldout, concept metric:

| k + r | per prompt | GPU-h (both splits) | Holm α′ | verdict |
|---|---|---|---|---|
| 120 + 60 | 100 s | **2.38** | 2.8e-4 | **recommended primary family** |
| 250 + 100 | 154 s | 3.67 | 1.4e-4 | affordable |
| 400 + 100 | 224 s | 5.34 | 1.0e-4 | affordable |
| 1 000 + 200 | 494 s | 11.8 | 4.2e-5 | affordable in 4 jobs |
| all 6 543 | 2 470 s | 59.0 | 7.6e-6 | **not** affordable, and pointless — the Holm correction destroys the effect sizes long before the GPU budget does |

**So the binding constraint on *k* is the multiple-testing family, not the GPU.** Recommendation:
**k = 120 + r = 60 as the pre-registered primary family**, with a secondary exploratory tier at
k = 400 reported **uncorrected and explicitly labelled exploratory** if the primary tier is
saturated. This is the sentence `P5_READINESS.md:251-256` should have contained: it justified
k ≈ 100 on cost, and cost is not what limits it.

### B4.4 Stage C — the AtP trust gate (**free**)

Stage B produces exact deltas for the same 180 cells Stage A ranked. Report Pearson **and** Spearman
of AtP vs exact and require `min ≥ 0.7`, exactly as `48_attribution_patching.py:409-412` and
`51_mlp_attribution.py:123-126`. Prior on the **node** estimator: 0.93/0.90, 0.93/0.91, 0.95/0.86
(§B1.2) — encouraging but not transferable to the **edge** estimator. If the gate fails, the ranking
is discarded and only the 180 exactly-patched edges are reported; they remain valid, because they
are exact.

### B4.5 Stage D — the reconstruction gate. **`P5_READINESS.md` omits its cost entirely.**

The only on-model run of `50_path_patching.py` **failed its own reconstruction gate**:
`outputs/path_patch_Llama-3.1-8B-Instruct_20260731_181722_697419/path_patching.json` —
`median_rel_err = 1.0059`, `recon_ok = false`, `parallel_score_median_direct_frac = 0.0`,
`verdict = "UNTRUSTWORTHY (recon gate failed; report TOTAL/DIRECT only)"`, over 8 senders (L9–L13)
and 24 head→head edges, `recon_tol = 0.15`. `DIRECT ≈ 0` and `Σ EDGE_head ≈ 0` while `TOTAL ≠ 0` is
exactly the signature of mediation running through the MLPs — which is P5's premise.

**Closing the reconstruction requires ALL receivers (heads *and* MLPs) for the reconstruction
senders. That set is not a subset of the 180-edge family**, so it must be costed separately.
Restrict to **8 reconstruction senders** (the same count `50` used) and a **pilot n = 20** — the
floor allowed by `MASTER_PLAN:301` (*"n ≥ 20 unique examples per cell"*).

| item | per prompt |
|---|---|
| 8 senders × [heads `(31−L_S)×32` + MLPs `(31−L_S)`] ≈ 8 × 726 = 5 808 edges, 1 injecting forward each (capture shared from the sender's single frozen forward) @ 0.06 s | 348 s |
| 8 sender-level TOTAL/DIRECT/self cells | 2.4 s |
| **total** | **≈ 350 s** |

| job | scope | compute | walltime |
|---|---|---|---|
| `p5d-a` | senders 1–4, n = 20 | 0.97 h | 3:00 |
| `p5d-b` | senders 5–8, n = 20 | 0.97 h | 3:00 |

**Stage D = 1.94 GPU-h.** Pre-register `recon_tol` **before** the run and report the result whether
or not it passes — do **not** inherit the 0.15 default silently (`50:282`).

### B4.6 The exact control set

| control | how it is realised | must equal |
|---|---|---|
| **self-freeze** | freeze-all-clean + clean sender, per position set | **exactly 0.0** on the raw float, run aborts otherwise (§B2) |
| **self-swap (head sender)** | sender ← its own clean `z` | **exactly 0.0** |
| **self-swap (MLP receiver)** | `ComponentOutSwap` with the receiver's own clean rows | **exactly 0.0** — never yet tested on-model |
| **non-downstream impossible** | receiver at `L_R < L_S`; requires bypassing `50:233`'s `if L_R > L_S`, which currently *excludes* rather than *measures* it | **exactly 0.0** |
| **random receiver** | MLPs drawn from the 60-edge stratum | CI overlapping 0 |
| **random sender** | the 20 count-matched senders outside both bands, via the stratum | CI overlapping 0 |
| **norm-matched path** | `pc.norm_matched_random` (`pair_common.py:958-964`) on every injecting test | ≪ the true edge |
| **hook-firing** | `n_hook_calls`, `‖donor − self‖`, `act_delta` per cell (free) | `n_hook_calls > 0`, `donor_dist > 0` |

### B5. P5 totals

| stage | GPU-h | jobs | waves (≤ 2 concurrent) |
|---|---|---|---|
| Stage 0 — synthetic MLP-path coverage | 0.00 | 0 (CPU) | — |
| Stage A — edge-AtP ranking, dev | 0.55 | 1 | 1 |
| Stage B — exact patching, dev + heldout (k = 120 + r = 60) | 2.38 | 2 | 1 |
| Stage C — AtP trust gate | 0.00 | 0 (free, in Stage B) | — |
| Stage D — reconstruction gate, 8 senders × all receivers, n = 20 | 1.94 | 2 | 1 |
| **P5 concept metric total** | **4.87** | **5** | **3** |

Wall clock: **≈ 4.2 h**.

### B6. P5-R — the refusal-suppression graph (**BLOCKED, costed, not scheduled**)

`MASTER_PLAN:608-609` calls the second graph *"the genuinely novel object"*. It is gated on
**P7 §0.10**: 66 files exist in `outputs/refusal_alllayers/` with **zero validation metadata**, and
only 5 layers were generation-validated (L12 failed) — `MASTER_PLAN:648-651`. Building it on
unvalidated per-layer directions would put the paper's most novel claim on the least validated
substrate.

Cost if unblocked: the same shape, ≈ **4.9 GPU-h**, but on a different prompt condition (the
behavioral/refusal harness, not the FC readout), so **no forward is shared with the concept graph**.
Recommended order: **concept graph now; refusal graph after P7's rebuild.**

---

# PART C — Grand totals and the launch order

| block | GPU-h | GPU jobs | waves |
|---|---|---|---|
| P4b-0 + P5 Stage 0 (CPU prerequisites) | 0.00 | 0 | — |
| P4b-1 z × 4 positions | 2.19 | 2 | 1 |
| P4b-2 Q × 4 positions | 2.19 | 2 | 1 |
| P4b-3 K/V group × 3 positions (retraction repair) | 3.00 | 2 | 1 |
| P4b-4 pattern × 3 qpos (eager) | 7.60 | 4 | 2 |
| P4b-5 heldout confirmation | 0.76 | 1 | 1 |
| P5 Stage A ranking | 0.55 | 1 | 1 |
| P5 Stage B exact (the claim) | 2.38 | 2 | 1 |
| P5 Stage D reconstruction gate | 1.94 | 2 | 1 |
| **CORE TOTAL** | **20.61** | **16** | **9** |
| P4b-6 v3 leakage-clean replication (optional) | 3.07 | 3 | 2 |
| **WITH OPTIONAL** | **23.68** | **19** | **11** |
| P5-R refusal graph (blocked on P7) | 4.87 | 5 | 3 |

**Wall clock, core: ≈ 12.7 h** at ≤ 2 concurrent jobs, every job ≤ 2.1 h of compute and ≤ 4 h
requested, i.e. comfortably inside the existing `--time=04:00:00` `killable` defaults and inside a
6–8 h ceiling with a 2× preemption-retry margin.

**Launch order (dependencies are real, not stylistic):**

1. **P4b-0** (all five items) and **P5 Stage 0** — CPU, no GPU, and P4b-0.1 is what makes every
   subsequent null reportable.
2. **P4b-1** ∥ **P4b-3** — the two decisive experiments: the L8–11 band at the positions where it
   acts, and the K/V retraction repair. If P4b-1 is null at demo positions too, the "retrieval is
   distributed/redundant" exit in `MASTER_PLAN:559-560` is reached at **5.2 GPU-h** rather than 440.
3. **P5 Stage A** (independent of P4 except for the induction-sender family, which is expected
   ⊂ L8–11 and therefore adds no new senders) → **P5 Stage B dev** → **Stage C gate**.
4. **P4b-2** ∥ **P4b-4** (the eager pattern sweep is the single largest line item — do it after the
   cheap decisive tests, not before).
5. Freeze candidates → **P4b-5** and **P5 Stage B heldout**.
6. **P5 Stage D**, then **P4b-6** if the v3 bench has been built.

---

## Appendix — corrections to the two source readiness documents

| # | where | claim | correction | severity |
|---|---|---|---|---|
| 1 | `P4_READINESS.md:496-519` | literal P4b = **439 GPU-h**, 30 720 cells | **≈ 90 GPU-h**, 12 800 combos over 3 584 distinct cells. Errors: K/V counted 32-wide (GQA ⇒ 8), `head-result` counted as distinct from `z` (identical under `attention_bias: false`), 5 position sets (decision ≡ answer ⇒ 4), and "both readouts" (only one exists). | **HIGH** — a 5× overstatement is what produced the "do not launch this" verdict |
| 2 | `P4_READINESS.md:99-104, 140` | per-occurrence donors need stacked `ZHeadPatch` or a new `Dict` overload | `50_path_patching.ZHeadPatchMulti:114-137` already does exactly this and is already importable via the `phase7_direct_total.py:33-35` pattern | MEDIUM |
| 3 | `P4_READINESS.md:539` | occurrence-count mismatch is "the norm", citing `len_mismatch = 58/59` | that is **sequence-length** mismatch (`align_row`), not occurrence count. Measured occurrence-count mismatch: **5/86 = 5.8 %** | MEDIUM |
| 4 | `P4_READINESS.md:563` | `configs/manifests/` is empty | it contains `phase9_gcg_mac_matrix.json`; no **P4** manifest exists | LOW |
| 5 | `phase5b_qkv.py:286-311, :353` | K/V rows labelled `L{l}H{h}` | L14H4 and L14H5 both map to KV head 1 ⇒ **bit-identical interventions counted as two independent cells** in the CI/Holm family | MEDIUM |
| 6 | `P5_READINESS.md:241-249` | Stage A reuses `51_mlp_attribution.py` | `48._select_pair_rows:244,247` filters on `has_demos`, which is `None` for all 1 458 rows of all three `data/bench/bench_*.json`; and `50:168`/`51:62` read `bench["pair"]["concept"]`, absent there. Both raise before the first forward. The AtP stack is **pair-benchmark-only**. | **HIGH** |
| 7 | `P5_READINESS.md:158-162` | self-freeze "measured 0.0" per `summary.json` | `summary.json` rounds (`phase7:175-176`) and the gate is `TOL = 0.05` (`:166`). I verified bit-exact 0.0 across **1 412 raw rows / 3 runs** — the claim is true, the cited evidence is not. P5 must assert on the raw float. | MEDIUM |
| 8 | `P5_READINESS.md:220-221` | random-sender/receiver controls are "free" | free **only** because the 60-edge random stratum supplies them; top-\|AtP\| selection is anti-correlated with randomness. The stratum is mandatory. | MEDIUM |
| 9 | `P5_READINESS.md:251-256` | k ≈ 100 justified by cost | cost permits k = 1 000+. The binding constraint is the **Holm family**. | MEDIUM |
| 10 | `P5_READINESS.md` §4 | — | the **reconstruction gate** (Stage D) is never costed; it needs all receivers for the reconstruction senders, ≈ **1.94 GPU-h**, and is not a subset of the top-k family | MEDIUM |
| 11 | `slurm/run_p4a_identify.sh` | header documents `sbatch slurm/run_p4a_identify.sh` | the script sets `: "${DSBENCH:?set DSBENCH}"` **before** the later `: "${DSBENCH:=…bench_clearharm.json}"` default, under `set -euo pipefail` ⇒ a bare submit **aborts**. It also carries `run_phase4_edgeko.sh` residue (`DSNPROMPTS`/`DSLAYERS`/`DSMODE`/`LAYER_ARG` computed and never used; prints `=== Phase4 edgeKO: …`). | MEDIUM — blocks the "zero-new-code partial" of `P4_READINESS.md:257-273` |
| 12 | `phase4b_pattern.py:211-225` + P4b design | benign-donor pattern arm at any query position | `align_row` is trailing-aligned + renormalised — defensible at the **answer** row only. At demo/query rows the query index itself differs across prompts, so donor arms there measure the heuristic. Use `C_uniform`/knockout arms instead. | MEDIUM |
| 13 | position convention | — | under the demo-block convention the "query codeword" is the **2 quoted tokens in the probe question**, not the attack's request-line codeword (`demo_block_of` strips it). `P4_READINESS.md:253-255` prefers the `phase4_edge_knockout` convention; every P4b-relevant script uses the other. Pin it in the manifest. | MEDIUM |
| 14 | all P4b/P5 scripts | — | no `--resume`; `raw.jsonl` opened `"w"` (`phase5_head_zpatch.py:88`); every wrapper defaults to `--partition=killable`. A preemption loses the whole shard. Hence the ≤ 2.1 h job sizing above. | MEDIUM |

**Files referenced:** `pair_common.py`, `ds_common.py`, `50_path_patching.py`,
`51_mlp_attribution.py`, `48_attribution_patching.py`, `scripts/phase5_head_zpatch.py`,
`scripts/phase5b_qkv.py`, `scripts/phase4b_pattern.py`, `scripts/phase4c_carryedge.py`,
`scripts/phase4_edge_knockout.py`, `scripts/phase6_mlp_causal.py`,
`scripts/phase7_direct_total.py`, `scripts/phase7b_mediation.py`, `scripts/phase7c_sufficiency.py`,
`scripts/phase5_analyze.py`, `scripts/split_to_bench.py`, `tests/test_path_patching.py`,
`tests/test_componentoutswap_synthetic.py`, `slurm/run_p4a_identify.sh`,
`slurm/run_phase5_headz.sh`, `slurm/run_phase7_dt.sh`, `slurm/run_ds_p5bq.sh`,
`data/bench/bench_clearharm.json`, `data/bench/bench_clearharm_v2.json`,
`data/bench/bench_curated.json`, `data/pair_benchmark/pair_carrot_bomb.json`,
`data/splits/clearharm_doublespeak_v3.json`,
`outputs/phase5_headz_clearharm_20260803_124603_704131`,
`outputs/phase5_headz_curated_20260803_124603_704130`,
`outputs/phase4b_pattern_clearharm_20260804_021315_707474`,
`outputs/phase7_directtotal_{clearharm,curated}_20260803_160846_{704726,704725}`,
`outputs/path_patch_Llama-3.1-8B-Instruct_20260731_181722_697419`,
`outputs/mlp_atp_{bomb,chlorine,grenade}`, `logs/ds_headz_704130.out`, `logs/ds_headz_704131.out`,
`logs/ds_edgeko_703327.out`, `logs/ds_p4bp_707474.out`,
`reports/CAUSAL_CONTINUATION_MASTER_PLAN.md`, `reports/readiness/P4_READINESS.md`,
`reports/readiness/P5_READINESS.md`,
`…/models--meta-llama--Llama-3.1-8B-Instruct/snapshots/0e9e39f249a16976918f6564b8830bc894c89659/config.json`.
