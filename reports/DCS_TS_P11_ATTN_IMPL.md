# DCS-TS-P11 — was PHASE 11's knockout arm running eager or SDPA?

**Answer: EAGER.** The guard that fired was reading a field the producer never wrote, and it was
blocking a valid run. The knockout was live. Nothing about the SDPA hazard is relaxed.

---

## 1. What actually refused, and where

The refusal did **not** come from `score_behavior.py:2551`. That guard runs on the loaded model
and it **passed** — arm `basket_bomb_S_G_scope` loaded, hooked, scored 40 rows and wrote
`DONE.json {"status": "ok"}`. Job 870303's `.out` ends with `[score] failures: {}` for that arm.

The refusal is in the **runner**, `pr059_run_localisation.py::verify_arm_artifacts`, reading the
finished artifact:

```python
impl = str(((summary.get("intervention") or {}) ...).get("attn_implementation")
           or summary.get("attn_implementation") or "")
if arm.kind != "baseline" and impl != want_impl:   # "" != "eager"
```

`summary.json` for that arm contains:

| where | key | value |
|---|---|---|
| top level | `attn_implementation` | **absent** |
| `intervention` | `attn_implementation` | **absent** (block holds `direction/mode/layers/alpha/knockout_scope`) |
| `knockout_liveness` | `attn_implementation` | `"eager"` — and this was the **REQUESTED** `_attn_impl`, not the loaded config |

Both places the gate looked were absent, the absent field collapsed to `""`, and `"" != "eager"`
refused a healthy arm as VOID. A **missing field read as a value** — the mirror image of PR-057's
C-117, in the same file whose `liveness_records_from_rows` docstring warns against exactly this.

## 2. Evidence that the model was eager

Three independent lines, all CPU-only or already on disk.

### 2a. The decisive one: the two arms' outputs are not identical

A discarded mask edit is a no-op, and a no-op produces bit-identical logits. Row-for-row over the
40 shared `prompt_id`s (`results.jsonl`, baseline arm vs `S_G` arm, same bank, same seed 20260909,
same population filter `sha16=b3ba3d5ea6c91d34`, 40 rows each, prompt_id sets equal):

```
rows identical across ALL shared keys:   0 / 40
p_concept          n_differing 40/40   max|A-B| 0.403219   mean 0.0967
p_codeword         n_differing 40/40   max|A-B| 0.690839   mean 0.2350
logp_concept       n_differing 40/40   max|A-B| 13.7675    mean 6.897
semantic_logodds   n_differing 40/40   max|A-B| 20.7878    mean 10.31
option_mass        n_differing 40/40   max|A-B| 0.609618   mean 0.1845
top1_id            n_differing 36/40   (the ARGMAX TOKEN changed on 36 of 40 rows)
```

Pooled option mass moved `median_true` 0.0895 → 0.2611. **Every scored quantity moved on every
row and the argmax flipped on 90% of them.** The mask edit landed.

### 2b. The library property, re-established rather than assumed

Installed: **transformers 5.12.1**, torch 2.7.1+cu126. CPU round-trip on a 2-layer Llama built
from config and reloaded through `from_pretrained` with the same kwargs `ds_common.load_model`
uses:

| requested | `config._attn_implementation` | `config._attn_implementation_internal` | `layers[0].self_attn.config._attn_implementation` |
|---|---|---|---|
| `"eager"` | `'eager'` | `'eager'` | `'eager'` |
| `"sdpa"` | `'sdpa'` | `'sdpa'` | `'sdpa'` |
| *(default)* | `'sdpa'` | `'sdpa'` | `'sdpa'` |

`model.model.config is model.config` → `True`; there is no per-submodule split to chase, and the
attribute has **not** moved. So `score_behavior.py:2551` was reading the right field, it did not
fire, and therefore the loaded backend was `'eager'`.

### 2c. The hook's own 4-D assertion never raised

`pair_common.AttentionKnockout._pre` raises `RuntimeError("expected a 4-D additive attention
mask; is the model loaded with attn_implementation='eager'?")` unless it is handed a 4-D additive
mask. It was entered on every prefill forward and never raised: `total_prefill_edits 2298240`,
`median_prefill_edits 57456`, `frac_rows_scope_live 1.0`, `n_decode_edits 0`, `scope_violations {}`.

**Verdict: eager. The arm is a real measurement, not a void one.**

## 3. What changed

Nothing was weakened. Two producers of confusion were removed and the checks got stricter.

### `src/boombness/score_behavior.py`
* New module-level `loaded_attn_implementation(model)` and `assert_eager_for_knockout(loaded,
  requested)` — the guard is now importable and therefore testable against a *real* load instead
  of only against a running job.
* **The request and the loaded state are now separate recorded facts.** `_attn_impl` is what was
  asked for; `_attn_impl_loaded` is what the model holds. Every `attn_implementation` field the
  run writes (`metadata.json` via `note_model`, the intervention note, `knockout_liveness`, and a
  new **top-level `summary.json` key**) now carries the **LOADED** value, with
  `attn_implementation_requested` beside it so a silent backend fallback stays visible.
* **ABSENT is no longer a pass.** The old guard was
  `getattr(cfg, "_attn_implementation", "eager") != "eager"` — a transformers build that stopped
  populating the attribute would have waved every knockout through. It now returns the sentinel
  `"<unrecorded>"` and refuses.

### `src/boombness/pr059_run_localisation.py`
* The gate reads the LOADED value from `summary.attn_implementation` or
  `summary.intervention.attn_implementation`.
* `knockout_liveness.attn_implementation` is **deliberately not a fallback**: historically it held
  the *requested* value, and accepting it would let an arm whose backend silently fell back to
  SDPA pass on the strength of its own request.
* **Absent and wrong are now different refusals, and both refuse.** An artifact that records the
  backend nowhere gets "the attention backend cannot be established from this artifact … re-run
  the arm", never an empty string compared against `"eager"`.

## 4. Verification

Genuine loads, driven through the real `score_behavior` functions (CPU, tiny Llama):

```
requested='eager'   loaded='eager'         -> ACCEPTED
requested='sdpa'    loaded='sdpa'          -> REFUSED (…not 'eager'…CLEAN NULL)
requested=None      loaded='sdpa'          -> REFUSED
attribute ABSENT    loaded='<unrecorded>'  -> REFUSED (backend cannot be established)
```

Harnesses:

| harness | self-test | mutate |
|---|---|---|
| `scripts/dcs_ts_pr059_localisation.py` | 114 / 0 failed (unchanged) | 94/94 RED (unchanged) |
| `src/boombness/pr059_run_localisation.py` | **58** / 0 failed (was 56; +2 new) | **49/49** RED (was 46; +3 new) |
| `scripts/dcs_ts_pr057_causal.py` | 117 / 0 (unchanged) | 102/102 RED (unchanged) |
| `src/boombness/pr057_run_causal.py` | 70 / 0 (unchanged) | 41/41 RED (unchanged) |
| `scripts/dcs_ts_pr058_symmetry.py` | 57 / 0 (unchanged) | 56/56 RED (unchanged) |

New coverage in the runner harness:
* `M23b` an arm whose summary records the backend **nowhere** → RED
* `M23c` the backend recorded **only** in `knockout_liveness` (the requested echo) → RED
* `M23d` an SDPA arm recorded in the **intervention** block → RED (`M23`, the top-level SDPA case,
  stays RED)
* two positive self-tests that a valid eager arm passes through **each** accepted source — the
  regression being fixed was the refusal of a *good* arm, which no mutation can cover.

`pytest` over every test touching `score_behavior` / `pr059_run_localisation`: **676 passed**,
0 failed, 323.9 s.

## 5. Can the smoke be resubmitted?

Yes. The blocker was a verifier reading the wrong field; the science was fine.

One caveat: the two run dirs already on disk
(`pr059_basket_bomb_s_0_baseline_n4_20260908_233859_472834`,
`pr059_basket_bomb_s_g_scope_n4_20260908_233954_472834`) were written by the **old** producer and
still carry no loaded-config field, so the fixed gate will — correctly — still refuse them: their
backend cannot be established *from the artifact*. They must be re-scored, not patched. That is
cheap: the two arms cost 36 s and 25 s of wall time and the model cache is hit after the first
load. Re-running the smoke from the top produces artifacts that carry the loaded value and pass.
