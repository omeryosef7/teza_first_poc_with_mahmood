> ## ⛔ BLOCKER, 2026-09-21 (REVIEW R13) — READ BEFORE BUILDING ANYTHING FROM THIS DOCUMENT
>
> **§4.2's realised-dose identity is INVERTED and off by a factor of 32.** The doc asserts a K-head
> arm edits `K/32` of what the all-head arm edits. Measured in `doublespeak_causality/pair_common.py:955-959`:
> the head-dim expansion `am.expand(-1, self.n_heads, -1, -1)` is guarded by
> `if self.heads is not None and am.shape[1] == 1`, so the **all-head arm (`heads=None`) never expands**
> and takes `n_heads_edited = am.shape[1] = 1`, while a K-head arm expands to 32 and takes
> `n_heads_edited = len(self.heads)`. A K=8 arm therefore records **8× the all-head arm, not 1/4**.
> Reproduced on the real hook: `heads=None` → 61 prefill edits, `heads=[0..7]` → 488, ratio **8.0**
> against the claimed 0.25. An existing artifact already refutes the doc:
> `csi1_basket_train_NEC_KO_20260918_001224_171794/summary.json` has `median_prefill_edits 2052`, and
> `2052 % 32 = 4` — unreachable if `n_heads_edited` were 32.
>
> **Consequence:** the realised-dose control is how this design separates a head effect from a dose
> effect, so an arm set built on the K/32 identity would be dose-confounded in the direction OPPOSITE
> to the one intended. **§4.2 must be re-derived before P4 spends any GPU.**

# Plan section 8.2 — DESIGN of the attention-HEAD level of the demonstration -> query circuit, for `basket`

STATUS: **DESIGN ONLY. NOTHING HERE HAS BEEN RUN. NO GPU JOB WAS LAUNCHED.**
Written 2026-09-20. Codeword: `basket` (the codeword whose plan section 19 Gate A is POSITIVE).
Model: `meta-llama/Llama-3.1-8B-Instruct` (32 blocks 0-31; `hidden_size` 4096 read from
`configs/dcs_csi_axis_basket_L20.json:"hidden_dim"`; the architecture's 32 attention heads are
asserted, NOT measured here — the smoke test below makes `score_behavior` echo the loaded model's
own `num_attention_heads` before any arm is costed).

Plan section 8.2, verbatim: *"Cheap attribution -> top candidate set -> genuine causal head
knockout/patch -> held-out validation -> cross-codeword transfer. ATTRIBUTION PROPOSES;
INTERVENTION DECIDES. A high attribution score is not a mechanism."*
Plan section 19 Gate C: *"can we identify the writer circuit? Causal head/path intervention, not
attribution. If NO: keep the representation result; do not invent a circuit."*

---

## 0. THE ONE FACT THAT DECIDES THE WHOLE DESIGN

`--knockout-heads` takes a **flat list of head INDICES**, not (layer, head) pairs, and applies that
same index set to **every layer of the `--intervene` band**:

* `src/boombness/score_behavior.py:2540-2542` — `--knockout-heads`, "comma list of head indices".
* `src/boombness/score_behavior.py:3148-3155` — parsed to `_knock_heads`, range- and
  duplicate-validated against `lm.model.config.num_attention_heads`, echoed.
* `src/boombness/score_behavior.py:3988` — forwarded as `knock_heads=_knock_heads`.
* `doublespeak_causality/pair_common.py:958` — `hs = range(am.shape[1]) if self.heads is None else
  self.heads`, inside the per-layer hook. Same `hs` for every layer in the band.

**Consequence, and it is not cosmetic: the intervention's coordinate system is `h`, not `(L, h)`.**
An attribution that ranks `(L, h)` cells and hands over "L8h22, L11h5, L13h30" is proposing a
candidate the instrument **cannot express**. Therefore the attribution stage must aggregate to the
same coordinate the knockout can address — a head index `h`, scored over the whole band — or the
design is proposing an experiment that cannot be run. This is the single strongest constraint in
this document and everything in section (a) follows from it.

A per-`(L, h)` knockout would need a new flag (`--knockout-heads-by-layer "8:22,9:14"`) inside
`score_behavior.py`. **That change is REPORTED here and NOT MADE.** Necessity half 2 (job 912736)
is running against the current file and PR-CSI-003's VOID conditions include "score_behavior.py
modified between arms of the same comparison".

---

## 1. INVENTORY — WHAT EXISTS, WITH `file:line`

### 1.1 EXISTS and is directly reusable with ZERO new code

| Piece | Where | What it does / why it is enough |
|---|---|---|
| Head-restricted attention knockout, flag | `src/boombness/score_behavior.py:2540`, guards at `:3068-3071`, `:3143-3155`, wiring at `:3988` | Refuses `--knockout-heads` without `--intervene` and without an `attn_knockout` spec, refuses out-of-range and duplicate heads, prints `knockout restricted to N of M heads`. |
| Head axis inside the SURGICAL scope | `doublespeak_causality/pair_common.py:955-959`, `:977-978`, `:1011` | `ScopedAttentionKnockout` accepts `heads=`; it expands the eager mask's head dim (`am.expand(-1, n_heads, -1, -1).clone()`) because the eager mask arrives with head-dim 1, then edits only the listed heads. |
| Head list reaches the SCOPED hook (not only the legacy one) | `src/boombness/score_behavior.py:1834-1838` passes `heads=knock_heads` to `pc.ScopedAttentionKnockout`; test `tests/test_scoped_knockout_wiring.py:184` asserts `pc.made[0].heads == [22]` alongside the scope | This is what makes `--knockout-heads` composable with `--knockout-scope target_surface_row_only`, i.e. with the A1 instrument. |
| **Realised dose IS counted and IS persisted, and it scales with the head count** | `doublespeak_causality/pair_common.py:959` (`n_heads_edited`), `:995`, `:1006`, `:1011` (`n_edits += n_rows * n_heads_edited`); surfaced in `summary.json` as `knockout_liveness.median_prefill_edits` / `total_prefill_edits` | **Measured**: `csi1_basket_train_NEC_KO` (all 32 heads) records `median_prefill_edits 2052.0`, `total_prefill_edits 1385460`, `total_decode_edits 0`, `frac_rows_scope_live 1.0`, `scope_violations {}`. A K-head arm must record **exactly K/32** of the all-head arm's prefill edits on the same rows. That makes dose-matching between the candidate set and its K-head controls **verifiable from the artifact**, not assumed. |
| Head list persisted per run | `outputs/boombness/score_behavior/phH22_20260824_062537_2174882/config.json` -> `args.knockout_heads: "22"` | Provenance of a head arm is already machine-readable. |
| All eight knockout scopes | `doublespeak_causality/pair_common.py:614-658` (`SCOPED_KNOCKOUT_MODES`) | Enumerated in section 1.4 below. |
| Liveness contract per scope | `pair_common.py:661-686` (`LIVENESS_REQUIREMENT`, `LIVENESS_MUST_BE_ZERO`) | `target_surface_row_only` REQUIRES `n_prefill_edits > 0` and REQUIRES `n_decode_edits == 0`. A head arm inherits this gate unchanged. |
| Per-head z capture / patch / ablate primitives | `pair_common.py:1064` `_attn_head_dims`, `:1072` `ZHeadPatch`, `:1115` `AllPositionZHeadAblate`, `:1161` `ZHeadCapture` | `ZHeadCapture` retains grad on the o_proj input — this is the AtP primitive. `ZHeadPatch` is the true-patch validator. Unit-tested GPU-free: `doublespeak_causality/tests/test_zhead_synthetic.py`, `test_allposzheadablate_synthetic.py`, `test_hook_firing_synthetic.py:55-116`. |
| Per-head AtP script | `doublespeak_causality/49_head_attribution.py` (AtP at `:1-16`, capture at `:40-46`, true-patch gate at `:120-130`) | `AtP[L,h,pos] = g_z . (z_corrupt - z_clean)`, validated against real `ZHeadPatch` patches on the top-k cells with a Pearson/Spearman `--min-corr` gate. |
| Path patching (sender -> receiver on the z channel) | `doublespeak_causality/50_path_patching.py`, `FreezeAllHeadsExcept` at `:44`, `ZHeadPatchMulti` at `:114` | TOTAL / DIRECT / EDGE decomposition with a reconstruction tolerance. Tested: `doublespeak_causality/tests/test_path_patching.py`. |
| Per-head demonstration-attention mass, already recorded | `src/boombness/retrieval_strength.py:128-141` (`_mass(..., per_head=True)`, `per_head_band`, `per_head_late`) | Per-(layer, head) attention mass onto the demo key set, from one eager `output_attentions=True` forward. |
| The endpoint and its loader | `scripts/dcs_cont_layerpos_map.py:107-146` `load_installation` | `y_install = sigmoid(logp_concept - logp_codeword)` on `query_kind == semantic_one_word`, `cell == C` only, with a duplicate-key refusal. |
| Domain-clustered analyser, rank test, VOID gates | `scripts/dcs_csi_subspace_analyze.py` (args at `:431-489`), independent re-derivation `scripts/dcs_csi_rederive_subspace.py`, run-dir strictness + bootstrap from `scripts/dcs_csi_rederive_patch.py` | `--candidate-arm` / `--comparator-arm` / `--control-prefixes` / `--base-arm` / `--ko-arm` / `--full-arm` is exactly the arm shape a head experiment has. Reusable **unchanged**. |
| Reference arms already on disk, right population, right GPU | `outputs/boombness/score_behavior/csi1_basket_train_NEC_BASE_...` and `..._NEC_KO_...` (job `906433`, `n-307`, `NVIDIA GeForce RTX 3090`, `expect_n 670`); validation twins under `csi1_basket_validation_BASE/KO` (job `897658`, RTX 3090, `expect_n 230`) | See section 4.4 — reusable **only** under stated conditions; the design does NOT rely on that and re-runs them in-allocation. |

### 1.2 EXISTS but is bound to a DIFFERENT experiment (reuse the code, not the result)

`49_head_attribution.py` and `50_path_patching.py` were written for **NEXT5/NEXT6**, whose
contrast is `clean = DOUBLESPEAK` vs `corrupt = matched NEUTRAL_CODEWORD` **prompt**, whose bench is
`data/pair_benchmark/pair_carrot_bomb.json`, and whose metric is `logit_diff(concept - codeword)`
on the `forced_choice` readout (`49_head_attribution.py:8-14`, `50_path_patching.py:5-7`). Two of
those three are wrong for this sprint:

* the corruption must be **the A1 attention knockout**, not a different prompt — the phenomenon
  being explained is the knockout's effect, and
* the endpoint must be `y_install`, which is the **concept-free `semantic_one_word`** channel;
  plan mandate section 4 and `dcs_cont_layerpos_map.py:110-112` **forbid** defining the target from
  the forced-choice channel, which supplies the option set and therefore names the answer.

The existing outputs (`doublespeak_causality/outputs/head_attr_Llama-3.1-8B-Instruct_*`,
`path_patch_Llama-3.1-8B-Instruct_20260731_181722_697419`) are therefore **NOT reusable as
results**. They are dated 2026-07-31, predate the whole DCS phase, and answer a different question.

**But the change needed is a SIMPLIFICATION, not an extension.** 49 inherits 48's token-alignment
machinery (`align_z` at `49_head_attribution.py:48-59`, `mapping` from 48) because its clean and
corrupt runs are two DIFFERENT prompts with different tokenisations. With the knockout as the
corruption, clean and corrupt are **the same token sequence** — only the attention mask differs.
The alignment layer, which is the fragile part, is **deleted**, not ported.

### 1.3 The four named output directories, checked

* `outputs/boombness/surgical_knockout/` — 40+ runs (`apA_firstcw_*`, `btn_q3_firstcw_*`,
  `blockscope_*`, ...). The positional/block knockout ladder. **All-head**; the `heads=` argument
  did not reach `score_behavior` until the R-AL follow-up. **Not head-level. Not reusable.**
* `outputs/boombness/retrieval_strength/` — 7 runs (`rsQwen3H_*`, `rsLlamaH_*`, `rsmoke_*`). These
  **are** per-head (`per_head_band` / `per_head_late` per row). **Reusable as a measurement
  PATTERN, not as data**: the readout position is `q = seq_len - 1`
  (`src/boombness/retrieval_strength.py:120`), which is **not** the row the A1 knockout edits, and
  the banks are the older `boombness_prompt_bank.jsonl` populations, not
  `boombness_prompt_bank_ts116m_basket_bomb.jsonl`.
* `outputs/boombness/aggressive_patching/` — residual-stream patching (`pr068_train67_*`,
  `contposc*`). **Not head-level.**
* `phase8_attn_causal` — **DOES NOT EXIST** under `outputs/boombness/`.
  `ls outputs/boombness/ | grep -iE "surgical|phase8|retrieval_strength|aggressive|head|atp|attrib"`
  returns only `aggressive_patching`, `retrieval_strength`, `surgical_knockout` and two
  `headline_*_decomposition.json` files. CANNOT REPORT anything about `phase8_attn_causal`.

### 1.4 Every `--knockout-scope` id the code accepts

From `doublespeak_causality/pair_common.py:614-658` (the authoritative tuple; `score_behavior.py`
deliberately validates against it rather than restating it — `:2674`, `:2804`):

| scope id | rows it may edit | liveness contract |
|---|---|---|
| `legacy_all_query` (default) | every query row, prefill AND decode | prefill>0 AND decode>0 |
| `query_prefill_only` | prefill only, the final-query span rows | prefill>0, decode==0 |
| `decode_only` | decode only; prefill untouched | decode>0, prefill==0 |
| `response_query_only` | final-query rows at prefill + every generated row at decode | prefill>0 AND decode>0 |
| `demo_processing_only` | prefill only, rows INSIDE the demonstration block | prefill>0, decode==0 |
| **`target_surface_row_only`** | **prefill only, the rows of the FINAL occurrence of the prompt's `target_surface` (the query codeword row)** | **prefill>0, decode==0** |
| `prompt_last_row_only` | prefill only, `max(query_span)` | prefill>0, decode==0 |
| `query_last_k_rows` | prefill only, a caller-supplied row set (last K of the query span) | prefill>0, decode==0 |

**A1 is `target_surface_row_only`** and that is the scope every arm below uses.

### 1.5 MUST BE WRITTEN

| # | Thing | Size | Why it cannot be avoided |
|---|---|---|---|
| W1 | `scripts/dcs_csi_head_atp.py` — AtP on the per-head z channel with **the A1 knockout as the corruption** and **`M = logp_concept - logp_codeword`** as the metric | ~250 lines, and it is mostly deletion: `ZHeadCapture` + `ZHeadPatch` from `pair_common`, the ranking and the true-patch correlation gate lifted from `49_head_attribution.py:100-158`, the scoring arithmetic from `src/boombness/signals.py:693-745`. The `align_z` layer is dropped. | 49's corruption and metric are both wrong for this sprint (section 1.2). |
| W2 | A **head-set draw** module: deterministic, seeded, reproducible K-of-32 draws written to a frozen JSON before any arm runs | ~60 lines | The control family must be fixed in the pre-registration, not generated at launch time. |
| W3 | A **loop-the-arms runner** for the CSI arm shape (load the model once, run N arms in-process) | ~120 lines, pattern lifted from `src/boombness/pr057_run_causal.py:1-30` (memoising `ds_common.load_model`, counted as `--model-loads`) | **Measured**: job `906433` spent `7834 s` wall on 5 arms whose own `DONE.json wall_seconds` sum to `3503.23 s`. **4330.77 s — 55.3% of the allocation — was model loading**, `866 s` per arm. At 24 arms that is 5.8 GPU-hours spent on `from_pretrained`. This file is worth more than everything else in this table. It does **not** edit `score_behavior.py`; it sets `sys.argv` and calls its `main()`, exactly as `pr057_run_causal.py` already does.  **⛔ WITHDRAWN 2026-09-21 (S-171 / REVIEW R13): the 866 s/arm figure divides a TOTAL by an arm count when 92% of it (3971 s of 4331 s) is ONE-TIME staging, measured before the first arm. Per-arm overhead is 72 s, so W3 saves 0.48 GPU-h at 24 arms, not 5.77 — a 12× overestimate. EVERY 'Without W3' FIGURE IN §7.2 INHERITS THIS and is ~12× too large. W1 is the critical path.** |
| W4 | `scripts/dcs_csi_head_analyze.py` — a thin wrapper choosing arm names and calling `dcs_csi_subspace_analyze.py` | ~40 lines, or **zero** if the arm names are chosen to fit the existing flags (they are; see section 4.2) | Optional. Prefer zero. |
| — | per-`(L, h)` knockout | **NOT WRITTEN, REPORTED ONLY** | Would require editing `score_behavior.py`. Prohibited while job 912736 runs. Section 0. |
| — | a `rel-6 <- rel-11` intra-query head knockout | **NOT WRITTEN, REPORTED ONLY** | Would require a new `SCOPED_KNOCKOUT_MODES` entry. Section 2, leg (ii). |

---

## 2. THE CAUSAL GEOMETRY — which heads are even CANDIDATES to be the writer

Three positions/layers must be kept apart, and the project's own artifacts say they are **not** the
same:

* **the row the A1 knockout edits** is `target_surface_row_only` = the final occurrence of the
  query codeword. `scripts/dcs_cont_qprobe.py:351-353` records it exactly:
  *"cw_query_equals: rel-11 (byte-identical); the knockout-edited row is rel-11, not the winner
  rel-6 which is 5 positions downstream -- the causal follow-up must target cw_query/rel-11"*.
* **the row the axis was fit at** is `rel-6` (`configs/dcs_csi_axis_basket_L20.json:"site"`,
  `scripts/dcs_csi_axis.py:30,276` — frozen, not re-searched). `rel-6` sits **5 positions
  downstream of** `rel-11`, on a flat plateau `rel-4..rel-14` (`dcs_cont_qprobe.py:355-356`).
* **the layer the rescue is read/written at** is `L18`
  (`configs/dcs_csi_pr003_necessity_basket.json:"rescue_layer": 18`), and `L18` means `resid_post`
  of **block 18** — `src/boombness/donor_patch.py:56-72` hooks `dc._get_layers(model)[layer_idx]`
  with a forward hook on that block's output.

So the target of plan section 8.2 for `basket` decomposes into **two legs**:

* **leg (i), `demo -> rel-11`, over blocks 6-14.** This is the edge the A1 knockout cuts. The
  candidate writers are attention heads at blocks 6..14 reading demonstration keys into the query
  codeword row.
* **leg (ii), `rel-11 -> rel-6`, over blocks <= 18.** Whatever leg (i) deposits at `rel-11` must be
  *moved* 5 positions to `rel-6` to be read by the axis at `resid_post[18]`. A1 does **not** cut
  this edge.

**This design tests leg (i) only, and says so.** Leg (ii) is real, is unaddressed, and needs a
scope that does not exist (section 1.5). Claiming "we found the writer" from leg (i) alone would
be claiming a circuit from half of it.

**Which blocks are candidates for leg (i), justified from causal ordering, not convenience:**

1. `resid_post[18]` at `rel-6` is a function of attention heads at blocks **0..18** — blocks 19-31
   are causally downstream of the read site and are **excluded by ordering**, full stop.
2. Blocks **15..18** are *not* excluded by ordering. They are heads that could read demo keys into
   the query rows and are **not cut by A1**. Their non-exclusion is not a detail: it is a candidate
   explanation for why A1 only takes `y_install` from `0.46852` to `0.23901` rather than to the
   floor (values from `configs/dcs_csi_pr003_necessity_basket.json`,
   `FEASIBILITY_ESTABLISHED_BEFORE_SPENDING_GPU`).
3. Blocks **0..5** are likewise not excluded by ordering, only by the A1 band.

The **primary causal test is restricted to blocks 6-14**, and the reason is *not* that the band is
convenient. It is that **a head knockout must be a fraction of an established ceiling.** The
all-head knockout at `6-14 / target_surface_row_only` is the only head-axis intervention on this
population with a measured, committed effect to be a fraction of. A head arm at `0-5` or `15-18`
would have no all-head positive control at that band, so a null there would be uninterpretable —
which is precisely what plan section 15 forbids buying with GPU hours.

**The AtP screen is nevertheless run over blocks 0..18**, because it is one backward pass and
covers every layer for free. If the screen puts substantial mass outside 6-14, that is a
**reported finding that pre-registers a second experiment** (establish the all-head ceiling at the
new band first, then screen it), **never** a mid-flight band change.

---

## 3. (a) THE ATTRIBUTION STAGE

### 3.1 The metric is the endpoint itself, not a proxy — and this is the design's best break

`y_install = sigmoid(logp_concept - logp_codeword)` (`dcs_cont_layerpos_map.py:126-131`), and
`logp_*` come from `signals.string_option_readout` (`src/boombness/signals.py:693-745`): teacher-
forced, `logsumexp` over each option's surface variants, read at `len(ctx)-1+j`. That is a **smooth
differentiable scalar**. Define

```
M         = logp_concept - logp_codeword     # == results.jsonl "semantic_logodds"
y_install = sigmoid(M)                       # strictly monotone in M
```

So gradient attribution can target **the endpoint's own logit**. No surrogate, no forced-choice
channel, no proxy metric to defend. `n_variants_concept == 2` and `n_variants_codeword == 2`
(measured from `csi1_basket_train_NEC_BASE_.../results.jsonl`), so all four variants fit in **one
batched forward** of width 4 — and the four sequences share the identical prompt prefix, so `z` at
every candidate position is identical across the batch and `z.grad` summed over the batch axis is
exactly `dM/dz`.

### 3.2 The estimator

```
AtP[L, h, p] = < g_z[L, h, p] , z_ko[L, h, p] - z_clean[L, h, p] >
```

* `z` = the o_proj **input**, the per-head attention output (`pair_common.py:1061-1063`). GQA
  shrinks the K/V heads, **not** this tensor — it is over `num_attention_heads`, so the AtP head
  axis and the `--knockout-heads` head axis are **the same 32 indices**. This is the property that
  makes the whole design coherent and it is documented at `pair_common.py:1061-1062`.
* `z_clean`: one clean batched forward under `ZHeadCapture(model, range(0, 19))`, backward on `M`.
* `z_ko`: one **batch-1, no-grad** prefill under exactly the A1 hook
  (`demo_all:attn_knockout:6-14:1.0`, `--knockout-scope target_surface_row_only`). Batch-1 because
  every knockout hook in `pair_common` raises on batch>1 (`score_behavior.py:3721-3728` documents
  this constraint). `z` at prompt positions is variant-independent, so one forward suffices.
* **No token alignment.** Clean and corrupt are the same `input_ids`. This deletes 49's `align_z`.

Per row: 1 batched forward+backward (4 seqs) + 1 batch-1 prefill. ~1.5x a scoring arm's per-row
work.

### 3.3 The aggregation — forced by section 0

The intervention addresses a head **index** across the whole band. So the screen's headline
statistic must be, for each head index `h`:

```
S[h] = sum over L in 6..14 of  AtP[L, h, p*]      (p* = the rel-11 / target-surface row)
```

signed, not absolute — a head whose z-change under the knockout *raises* `M` is not a writer of the
installed meaning, and folding it in by absolute value would let a protective head be promoted.
Magnitude is kept as a **diagnostic** and as the ranking used for the true-patch gate (where
magnitude is what is being validated), never as the selection statistic.

Reported alongside, never used for selection:

* the same sum over blocks 0..5 and 15..18 (the band-extension question of section 2);
* `AtP` at the demonstration key positions (the sender side);
* per-head demo attention mass at `rel-11`, the `retrieval_strength.py:128-141` pattern, read at
  `p*` instead of `seq_len - 1`. **Deliberately not the proposer**: `retrieval_strength.py:132-135`
  already records that band-level demo mass **ANTI-predicts** causal importance on one model
  (band `0.0316` vs late `0.0416` while the band knockout is 2.7x stronger). Attention mass answers
  "does this head look at the demonstrations", which is not the question.

### 3.4 The gate that decides whether the screen may be used at all

Lifted from `49_head_attribution.py:120-158`: take the top 40 cells by magnitude, apply a **real**
`ZHeadPatch` (`pair_common.py:1072`) of `z_ko` into the clean forward at that cell, measure the
true `delta M`, and correlate AtP against truth.

* Pearson **and** Spearman must both be `>= 0.7` (49's `--min-corr` default).
* **If the gate fails, the attribution stage is declared UNTRUSTWORTHY and the causal stage is NOT
  launched on its ranking.** The fallback is stated in advance so it is not invented later:
  select the candidate set by **true single-head patch effect** measured directly on a 40-row
  subsample (32 heads x 1 patch x 40 rows = 1280 forwards, ~15 min). That is slower but it is a
  measurement, not an estimate.

**Stated limitation, in advance:** the model runs in `bfloat16` (fp32 8B does not fit a 24 GB
RTX 3090), so `g_z` is a bf16 gradient and is noisy. The true-patch gate is exactly the instrument
that catches this, which is why it is a gate and not a diagnostic.

---

## 4. (b) THE CAUSAL STAGE

### 4.1 The intervention — expressible TODAY, zero new code

```
--intervene demo_all:attn_knockout:6-14:1.0
--knockout-scope target_surface_row_only
--knockout-heads <comma list>
```

Every flag exists; `tests/test_scoped_knockout_wiring.py:184` already asserts the head list reaches
the scoped hook. Endpoint: `y_install`, concept-free `semantic_one_word`, cell C, dose 4, loaded by
`dcs_cont_layerpos_map.load_installation`. Statistical unit: **DOMAIN** (67 train, 23 validation).
`button` is never pooled with `basket` and does not appear in this experiment.

### 4.2 Arms — TRAIN (67 domains, `expect_n 670`)

Named so the **existing** `dcs_csi_subspace_analyze.py` consumes them with no new analyser:

| Arm | `--knockout-heads` | Role |
|---|---|---|
| `HD_BASE` | (no `--intervene`) | clean reference. `--base-arm` |
| `HD_KO` | omitted = all 32 | **the positive control and the ceiling**. `--ko-arm` and `--full-arm` |
| `HD_TOPK` | the K heads with the most negative `S[h]` | **the candidate**. `--candidate-arm` |
| `HD_BOTK` | the K heads with `S[h]` closest to zero | matched "same procedure, opposite end". `--comparator-arm` |
| `HD_RAND00` .. `HD_RAND19` | 20 independent K-of-(32-K) draws, seeds frozen in the prereg | **the dose-matched control family**. `--control-prefixes HD_RAND` |

**K = 8, fixed here, before any AtP number exists.** Rationale stated in advance: `8/32 = 25%` of
the head budget is small enough that a large effect is a localisation claim and not a restatement
of `HD_KO`, and large enough that 8 heads spread over 9 layers is a plausible circuit size. K is
**not** tuned to the screen.

**Dose matching is by construction and is VERIFIED, not asserted.** Because
`n_edits += n_rows * n_heads_edited` (`pair_common.py:1011`), every K=8 arm must record
`knockout_liveness.median_prefill_edits` equal to **8/32 = 1/4** of `HD_KO`'s on the same rows.
A pre-registered gate refuses the analysis if any control's realised dose differs from the
candidate's by more than one edit-count unit. `HD_KO`'s all-head value on this exact population is
already on disk (`median_prefill_edits 2052.0`), so the expected K=8 value — **513.0** — is
predictable **before the run**, and a deviation is a bug, not a result.

**Control draws**: 8 heads drawn uniformly without replacement from the **24 non-candidate** heads,
so overlap with `HD_TOPK` is 0 by construction and is recorded as 0. Seeds `20260920 + j`, frozen
in the prereg JSON by W2 before any arm launches.

### 4.3 Arms — VALIDATION (23 held-out domains, `expect_n 230`)

The **same 24 arm definitions**, the **same frozen head sets**, the **same seeds**, on the held-out
domains listed in `configs/dcs_csi_axis_basket_L20.json:"held_out_validation_domains"`. Nothing is
re-selected. The three TEST domains (`restaurant_kitchen`, `school_campus`, `subway_station`) are
touched by nothing here.

### 4.4 The positive control, and why BASE/KO are re-run rather than reused

Plan section 15: a null is uninterpretable unless the instrument has been shown capable.
`HD_KO` **is** that demonstration: all 32 heads, same band, same scope, same population.
Pre-registered requirement: `HD_KO - HD_BASE` must be clearly negative with **ci95 upper bound
< 0**. If it is not, the verdict for the whole head experiment is **CANNOT ANSWER** and no head arm
is read.

Arms that would serve are already on disk — `csi1_basket_train_NEC_BASE` / `NEC_KO` (job `906433`,
node `n-307`, `NVIDIA GeForce RTX 3090`, `expect_n 670`, same bank
`boombness_prompt_bank_ts116m_basket_bomb.jsonl`, same exclusion file
`runargs/dcs_cont/exclude_basket_bomb_sow_train.txt`) — and the committed span is
`BASE 0.46852 -> KO 0.23901`, a `0.22951` drop
(`configs/dcs_csi_pr003_necessity_basket.json`).

**The design re-runs them anyway, inside the new allocation, at a cost of 2 arms.** Reasons, in
order: (1) PR-CSI-003's VOID conditions include "compared arms not on one GPU architecture", and
S-119/S-121 established that this repo has already been bitten by exactly that; (2) the head arms
take the `am.expand(...).clone()` branch (`pair_common.py:955-956`) that the all-head arms do not,
so candidate and ceiling differ in a code path and should not additionally differ in allocation;
(3) two arms is ~23 minutes of the looped runner. Cheap insurance against a VOID.

### 4.5 A second, stronger control family — costed but NOT in the primary

`HD_MASS00..19`: 8 heads drawn to **match `HD_TOPK`'s total demo-attention mass at `rel-11`** while
excluding the candidates. This separates "writes the installed meaning" from "looks at the
demonstrations", which the uniform-random family cannot. It is scientifically the better control
and it is **deliberately not primary**, because the task's requirement is K matched **random**
heads and because doubling the family doubles the cost. It is specified and costed in section 7 and
is to be run **only if the primary passes** — never as a rescue after a primary failure.

---

## 5. (c) THE MULTIPLE-COMPARISONS PROBLEM

**Where multiplicity does and does not enter, stated before the data exists:**

1. **The AtP screen emits no p-value and performs no test.** It ranks 19 layers x 32 heads of
   cells, aggregated to 32 head indices. It is a *proposal*. Nothing in it is reported as
   significant, and no head is reported as "significant by attribution". Plan section 8.2's
   "ATTRIBUTION PROPOSES" is implemented by *not testing here at all*. This is what keeps the
   family small.
2. **No per-head causal test is run on TRAIN.** A 32-arm one-head-at-a-time screen with 32 tests
   would need a family-wise correction, would cost 32 arms, and would be underpowered per head.
   It is **rejected by design**. Exactly **one** candidate set is formed.
3. **TRAIN is DESCRIPTIVE. Its rank p is selection-contaminated and is reported as such** — the
   heads were chosen using TRAIN activations, so a TRAIN rank of 1 is partly a restatement of the
   selection. The design commits in advance to printing the TRAIN rank with the words
   "selection-contaminated, not an inferential statement" next to it.
4. **VALIDATION adjudicates, with ONE preregistered test.** Candidate set frozen, control seeds
   frozen, K frozen, band frozen, layer frozen, endpoint frozen — all before the validation arms
   launch. One candidate against 20 controls is one test in a family of one. **No correction is
   needed and none is applied**, and that is a consequence of the design, not a convenience.
5. **The attainable floor is stated with the p, always.** 20 controls -> floor `1/21 = 0.0476`.
   That clears `alpha = 0.05` — but only just, and **only if the candidate is rank 1**. Rank 2 of
   21 is `p = 0.0952` and does **not** pass. This is exactly the S-125 situation (rank 1 of 11,
   floor `0.0909`, INCONCLUSIVE *by design*) and it is being avoided on purpose by using 20 and not
   fewer. The analyser already prints the floor beside the p (`dcs_csi_subspace_analyze.py`
   docstring: *"it will not report a p without its attainable floor beside it"*).
6. `HD_BOTK` is the `--comparator-arm` and is **not** matched by `--control-prefixes HD_RAND`, so
   it does **not** enter the control distribution. That is deliberate and is named here explicitly
   because S-120(e) recorded that a silently-empty or silently-widened control family is this
   sprint's known foot-gun.
7. If section 3.4's true-patch gate fails and the fallback selection is used, **the fallback is
   still a single preregistered candidate set** and clause 4 is unchanged.

---

## 6. (d) THE VERDICTS, WRITTEN BEFORE THE EXPERIMENT

Let `E(arm) = mean_over_domains( y_install(arm) - y_install(HD_BASE) )`, domain-clustered, with
ci95 from the domain bootstrap already used by `dcs_csi_rederive_patch`. Define the localisation
fraction `F = E(HD_TOPK) / E(HD_KO)`.

**Read in this order. Stop at the first failure.**

* **GATE 0 — liveness.** Every arm: `knockout_liveness.scope_violations == {}`,
  `frac_rows_scope_live == 1.0`, `total_prefill_edits > 0`, `total_decode_edits == 0`, and the
  realised-dose identity of section 4.2. Any failure -> **VOID**, not a result.
* **GATE 1 — positive control.** `E(HD_KO) < 0` with ci95 upper bound `< 0`. If not ->
  **CANNOT ANSWER**. Report the feasibility numbers and STOP. Do not report the candidate.
* **GATE 2 — attribution trustworthiness** (section 3.4). Failed -> the fallback selection was
  used; say so in the artifact.

Then, on **VALIDATION**:

| Verdict | Condition |
|---|---|
| **WE FOUND (part of) THE WRITER** | `HD_TOPK` is **rank 1 of 21** against the `HD_RAND` family (`p = 0.0476`, floor `0.0476`) **AND** `F >= 0.50` with the ci95 on `F` excluding 0. Reported as: *8 head indices, applied across blocks 6-14 on the query-codeword row, carry at least half of the A1 knockout's effect on installation for `basket` — for leg (i) of the circuit only.* |
| **PARTIALLY LOCALISED** | rank 1 of 21 **AND** `0 < F < 0.50`. A real but minority share. Not "the writer". |
| **IT IS DISTRIBUTED** | GATE 1 passes (the instrument moves the endpoint) **AND** `HD_TOPK` sits inside the `HD_RAND` distribution (`p > 0.05`) **AND** the `HD_RAND` arms themselves show a clear effect, i.e. 8 arbitrary heads already reproduce a substantial share of `E(HD_KO)`. Reported as: *no 8-head subset is privileged; the demo->codeword-row write is spread across heads.* Plan section 19 Gate C then says **keep the representation result and do not invent a circuit.** |
| **CANNOT ANSWER** | GATE 1 fails; **or** GATE 0 fails on any arm; **or** `E(HD_KO)` and the whole `HD_RAND` family are all statistically indistinguishable from 0 on the validation split (the split is underpowered for head-sized effects); **or** the candidate and the controls are separated by less than the run-to-run reproducibility of a single arm. |

**Recorded in advance, so that a null reads as what it was predicted to be:** `E(HD_KO) = -0.22951`
on TRAIN is the whole-band, all-head effect. If the effect were uniform across 32 heads, 8 heads
would give `~ -0.057`, against a TRAIN sufficiency CI width of order `0.004`
(`configs/dcs_csi_pr003_necessity_basket.json`, `PREDICTION_FIXED_BEFORE_THE_DATA`). So the
experiment is **well powered to detect the uniform null itself**, and the discriminating question
is whether `HD_TOPK` beats that uniform expectation, not whether it differs from zero. The rank
test against `HD_RAND` is precisely the test of that, which is why it and not a zero-test is the
primary.

**Honest expectation, on record before the data:** attention-head effects read 5 positions
downstream and 4+ layers later are usually distributed. I expect **PARTIALLY LOCALISED or
DISTRIBUTED**, and I expect `F` to be well under `0.50`. A **WE FOUND THE WRITER** verdict should
read as the surprise it would be.

---

## 7. (e) COST

### 7.1 Everything below is calibrated from measurements taken from committed artifacts

| Measurement | Value | Source |
|---|---|---|
| job `906433`, 5 arms, one RTX 3090 (`n-307`) | `02:10:34` = `7834 s` | sprint log line 8397 |
| `csi1_basket_train_NEC_BASE` (670 rows, clean) | `669.547 s` | its `DONE.json wall_seconds` |
| `csi1_basket_train_NEC_KO` (670 rows, all-head A1 knockout) | `798.424 s` | its `DONE.json` |
| `KO_NEC_FULL` / `KO_NEC_AXIS` / `KO_NEC_ORTH` (670, rescue arms) | `680.041` / `679.667` / `675.551 s` | their `DONE.json` |
| **sum of the 5 arms' own wall** | **`3503.23 s`** | computed from the five files |
| **model-load + startup overhead** | **`4330.77 s` = `866.2 s`/arm = 55.3% of the allocation** | `7834 - 3503.23` |
| `csi1_basket_validation_KO` (230 rows) | `223.784 s`, job `897658`, RTX 3090 | its `DONE.json` |
| generation cost on this population | **zero** — `gens.jsonl` is 0 lines; `semantic_one_word` is not a generating kind (`score_behavior.py:2964`) | `wc -l` on the run dir |

Per-arm cost model: **670-row knockout arm ~ 800 s compute; 230-row knockout arm ~ 224 s compute;
model load ~ 866 s, paid once per allocation if W3 exists, once per arm if it does not.**

### 7.2 Arm counts and hours

| Stage | Arms | Compute | With W3 (one load/allocation) | Without W3 |
|---|---|---|---|---|
| Smoke (section 7.3) | 2 x 24 rows + 1 AtP on 8 rows | ~180 s | **~0.3 h** | ~0.7 h |
| AtP screen, TRAIN, 670 rows | (1 script, not an arm) | ~1200 s | **~0.6 h** | ~0.6 h |
| True-patch gate, 40 cells x 40 rows | (same script) | ~1200 s | **~0.3 h** | (in the above) |
| **TRAIN causal**: `HD_BASE`, `HD_KO`, `HD_TOPK`, `HD_BOTK`, `HD_RAND00..19` | **24** | 24 x ~800 s = 19200 s | **~5.6 h** | ~10.4 h |
| **VALIDATION causal**: the same 24 | **24** | 24 x ~224 s = 5376 s | **~1.8 h** | ~5.8 h |
| **TOTAL, primary** | **48 arms + 1 script** | | **~8.6 GPU-hours** | **~17.5 GPU-hours** |
| Optional `HD_MASS00..19` family (only if the primary passes) | +40 | | +5.0 h | +12.7 h |

**One RTX 3090. Never a V100** — `runargs/dcs_csi_pr003_read.txt:5-16` makes sm_70 a VOID
condition for this sprint, and while the head arms are not norm-matched, mixing architectures
across a comparison is itself a VOID condition.

**Cost risk that must be measured, not assumed:** a head-restricted arm takes the
`am.expand(-1, 32, -1, -1).clone()` branch (`pair_common.py:955-956`) that an all-head arm does
not, materialising a `[1, 32, S, S]` mask clone per layer per prefill. At `S ~ 700` in bf16 that is
~31 MB x 9 layers transient. The smoke test **measures the slowdown factor** before the 24-arm
stage is costed; if it exceeds 1.5x, the table above is re-derived from the measured factor and
nothing is launched on the old estimate.

### 7.3 The minimum smoke test that MUST pass first

1. **`SMOKE_HD_KO`** — `--limit 24`, all heads, the A1 flags. Record
   `knockout_liveness.median_prefill_edits`, `frac_rows_scope_live`, `scope_violations`, and the
   wall time.
2. **`SMOKE_HD_8`** — `--limit 24`, the **same 24 rows**, `--knockout-heads 0,1,2,3,4,5,6,7`
   (a fixed placeholder set, **not** an AtP result — this is a wiring test, not a science run).
   **PASS requires all of:**
   * `score_behavior` prints `knockout restricted to 8 of 32 heads` (this also **measures** the
     model's true `num_attention_heads`, which section 0 only asserted);
   * `median_prefill_edits` is **exactly 1/4** of `SMOKE_HD_KO`'s -> the head restriction reached
     the hook and did not silently block all 32 (failure mode 1 of
     `tests/test_knockout_heads.py:6-13`);
   * `scope_violations == {}`, `total_decode_edits == 0`, `frac_rows_scope_live == 1.0`;
   * `config.json args.knockout_heads == "0,1,2,3,4,5,6,7"` -> provenance persisted;
   * `y_install` differs from `SMOKE_HD_KO`'s on the same rows -> the arm is not a no-op;
   * wall-time ratio vs `SMOKE_HD_KO` recorded -> the section 7.2 cost risk.
3. **`SMOKE_ATP`** — W1 on 8 rows. **PASS requires**: `z_ko != z_clean` at the `rel-11` row on
   every row (if the knockout changed no `z`, AtP is identically zero and would score as a clean
   null); the `M` reconstructed by the script equals `results.jsonl semantic_logodds` for those
   rows to `< 1e-3`; and at least one `ZHeadPatch` of `z_ko` into the clean forward moves `M`
   measurably.
4. **`python -m pytest tests/test_knockout_heads.py tests/test_scoped_knockout_wiring.py
   doublespeak_causality/tests/test_zhead_synthetic.py -q`** — green, on CPU, before anything is
   submitted.

**Nothing in section 7.2 is launched until 1-4 pass and the placeholder head set is discarded.**

---

## 8. FOOT-GUNS, NAMED IN ADVANCE

1. **`--knockout-heads` is head-index-only.** An AtP ranking of `(L, h)` cells cannot be handed to
   the instrument. Section 0 / section 3.3.
2. **`rel-6` is not `rel-11`.** The axis site and the knocked-out row are 5 positions apart
   (`dcs_cont_qprobe.py:351-353`). This design tests leg (i) only and must not be written up as
   "the circuit".
3. **`--control-prefixes` must be spelled out.** The default `KO_SHUF,KO_RAND` would match
   **nothing** in the `HD_*` naming, the control distribution would be **silently empty**, and the
   analyser would fall through to the single-comparator branch that S-050 showed can be made to
   say either thing. `--control-prefixes HD_RAND`, always, explicitly.
4. **Dose is not "8 heads" in the abstract; it is a realised edit count.** Verify it from
   `knockout_liveness`, expected `513.0` against `HD_KO`'s `2052.0`.
5. **Do not reuse the July 2026 `head_attr_*` / `path_patch_*` outputs.** Different bench,
   different corruption, forced-choice metric — which mandate section 4 forbids as the target.
6. **Do not edit `src/boombness/score_behavior.py`** for the per-`(L, h)` flag, or for anything
   else, while a necessity arm is running.
7. **Do not launch on a V100.**
8. **The TRAIN rank is not an inferential statement.** Section 5 clause 3.
9. **If `HD_KO` in this allocation disagrees with the committed `NEC_KO` span (`-0.22951`)**, that
   is a hardware/flag discrepancy to be resolved BEFORE any head arm is read, not a result.

---

## 9. THE COMMAND SHAPE (for reference; NOT RUN)

Template, from the measured `csi1_basket_train_NEC_KO` argv, with the head restriction added:

```
python src/boombness/score_behavior.py \
  --bank data/boombness_prompts/boombness_prompt_bank_ts116m_basket_bomb.jsonl \
  --model <Llama-3.1-8B-Instruct snapshot> \
  --query-kinds semantic_one_word --conditions natural_doublespeak --n-examples 4 \
  --exclude-prompt-ids runargs/dcs_cont/exclude_basket_bomb_sow_train.txt --expect-n 670 \
  --readout-ids whole_answer --readout-max-batch 1 --answer-prefix "Answer:" \
  --min-option-mass 0.05 --semantic-options bank_pair \
  --option-mass-gate-scope pooled --option-mass-gate-min-dose 1 \
  --intervene demo_all:attn_knockout:6-14:1.0 \
  --knockout-scope target_surface_row_only \
  --knockout-heads <K indices> \
  --attn-impl eager --dtype bfloat16 --seed 20260913 \
  --arm HD_TOPK --tag csi3_head_basket_train_HD_TOPK
```

`HD_BASE` drops `--intervene`, `--knockout-scope` and `--knockout-heads`. `HD_KO` drops only
`--knockout-heads`. Validation swaps the exclusion file for
`runargs/dcs_cont/exclude_basket_bomb_sow_validation.txt` and `--expect-n 230`.

Analysis, with the EXISTING analyser and no new code:

```
python scripts/dcs_csi_subspace_analyze.py \
  --codeword basket --tag-prefix csi3_head_basket_validation --expect-n 230 \
  --arms HD_BASE,HD_KO,HD_TOPK,HD_BOTK,HD_RAND00,...,HD_RAND19 \
  --base-arm HD_BASE --ko-arm HD_KO --full-arm HD_KO \
  --candidate-arm HD_TOPK --comparator-arm HD_BOTK \
  --control-prefixes HD_RAND \
  --split validation --require-slurm-job <JOB>
```

plus the independent re-derivation `scripts/dcs_csi_rederive_subspace.py` with the same arm names,
which shares no code with the analyser.

---

## 10. WHAT THIS DESIGN CANNOT DO, STATED UP FRONT

* It cannot test leg (ii) (`rel-11 -> rel-6`). No scope exists for it.
* It cannot resolve **which layer** a head acts at — `--knockout-heads` ties the index across 6-14.
* It cannot test blocks 0-5 or 15-18 causally without first establishing an all-head ceiling there.
* It does not do **cross-codeword transfer** (plan section 8.2's last clause). Transfer to `button`
  is only meaningful once `basket` has a positive head result; running it on a distributed or
  CANNOT-ANSWER outcome would be testing the transfer of nothing. It is the **next** design.
