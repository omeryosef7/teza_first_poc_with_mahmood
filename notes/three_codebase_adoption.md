# Three-Codebase Adoption Plan — Boombness Sprint

> Written 2026-08-16. Companion to `notes/boombness_reuse_inventory.md` (which covers what we
> already own) and `docs/BOOMBNESS_OBJECTIVE_SPRINT_PLAN.md` (§ numbers below refer to it).
> Synthesized from three independent code readings of:
> - **RC** = `doublespeak_causality/third_party/prompt_injection_role_confusion/` (Role Confusion)
> - **RD** = `Chain_of_Thought_Hijacking/refusal_direction/` (+ `Chain_of_Thought_Hijacking/Hijacking/`)
> - **IJ** = `external_repos/interp-jailbreak/`
>
> Reading constraint honoured throughout: code, signatures, docstrings and config schemas only.
> No attack-prompt text, no harmful-behaviour datasets, no `outputs/*.jsonl` were opened or quoted.

## 0. Executive ordering

| # | Item | Codebase | Closes | Cost | Risk if skipped |
|---|---|---|---|---|---|
| **P0** | Role-tag wrapping + role-probe pipeline (Userness/CoTness) | RC | §11 entirely | ~1.5 d | §11 is a from-scratch reimplementation; no other source exists |
| **P1** | Dominance edge-attribution ported to HF eager | IJ | §10.1 attribution | ~0.5 d | Edge knockout can only be ranked by raw attention `A`, the weaker predictor |
| **P2** | `select_direction` candidate bank + 3-metric validation | RD | §10.3/§10.4 gating | ~1 d + 1 GPU-h/model | Direction claims cannot be separated from "we broke the model" |
| **P3** | Readout diagnostics (position audit, post-`</think>` check) | RD + IJ | §2.4 gate | ~3 h | Silent left-padding / thinking-model readout failure |
| **P4** | No-survivor negative-result contract | RD | §2.2 | ~2 h | Best-effort numbers reported as validated results |
| **P5** | Analysis protocol: continuous axis, one-row-per-unit, refusal-only control | IJ | §9/§10 | ~1 d, CPU | Pseudo-replication + "success just looks different" artifact |
| **P6** | Small verbatim utilities (`get_logits_stats`, taxonomy, template-token counter, CE shift) | IJ | §5.3/§12 | ~1 h | Reimplementing known off-by-one traps |

Everything below is stated as (a) already reused, (b) adopt now + exactly how, (c) deliberately not adopted + why.

---

## 1. Role Confusion (RC) — `doublespeak_causality/third_party/prompt_injection_role_confusion/`

### (a) What we already reuse
Nothing. This tree is on disk but no `src/boombness/` module imports from it today. Our
`src/boombness/probes.py` and `DC/src/probes/*` (`build_items`, `assert_split_discipline`,
`fit_and_eval`, `select_C`, group-bootstrap CI, leak assertions) are the house probe stack and
are **better than RC's** on hygiene — RC has no leak assertion and no CI. We keep ours as the
outer frame and take RC's *role-specific* machinery inside it.

### (b) Adopt now — this is P0

**P0.1 — vendor the role wrapper (the single cheapest high-value file copy).**
Copy `utils/role_templates.py` → `src/boombness/vendor/role_templates.py`, provenance header,
otherwise unmodified. Keep `render_single_message(model_prefix, role, content, tool_name=None)`,
`render_single_qwen3` (matches Qwen3-14B), `render_mixed_cot`, `fold_cot_into_final`. Add two new
branches `render_single_llama3` / `render_single_phi4` following the existing per-family shape
(~40 lines). This *is* plan §11's "identical neutral text in different role tags": it builds the
tag envelope by hand rather than via `apply_chat_template`, so the `content` bytes are byte-identical
across role conditions and only the wrapper varies. Pure strings, zero dependencies.
*Validation gate before use:* assert `render_single_message(fam, role, content)` is a substring of
`ds_common.apply_template(...)` output for the same single message, per family. If it is not, our
family branch is wrong, not the theory.

**P0.2 — vendor the capture substrate.**
Copy `demo/simple_test_helpers.py` (not `utils/dataset.py` + `utils/probes.py`) →
`src/boombness/vendor/rc_capture.py`: `ReconstructableTextDataset`, `stack_collate`,
`convert_outputs_to_df_fast`, `run_and_export_states`. The demo copy is the same code with no
`cupy`/`cuml`/`utils.*` imports. Pass our own hook-based capture as the `run_model_return_states`
callable — the demo notebook itself endorses plain `register_forward_hook`.
Requirements: fast tokenizer (it raises otherwise); `tokenizer.pad_token_id` set (perplexity print);
left padding assumed, pads dropped via `attention_mask` so row order stays aligned to `sample_df`.
Memory: activations are held in CPU RAM as `n_tokens × n_layers_kept × D` — subsample layers
(they keep every 4th) or `n_sample_size`, or 250×1024×8×4096 fp16 ≈ 16 GB.

**P0.3 — port the probe trainer out of the notebook.**
`experiments/role-analysis/02-train-role-probes.ipynb` cell 18 (`fit_lr`, `get_probe_result`)
→ new `src/boombness/role_probes.py`. Swap `cuml.linear_model.LogisticRegression` →
`sklearn.linear_model.LogisticRegression(penalty="l2", max_iter=5000, fit_intercept=True)`
(multinomial), and `cuml.train_test_split` → `sklearn.model_selection.GroupShuffleSplit`
grouped on `prompt_ix`. Keep verbatim: one row per **content token**, label = the role tag it was
wrapped in; the grouped-by-prompt split; `acc_by_role` (full confusion table); `acc_by_pos` vs
`token_in_seg_ix`. Wire the result through our existing `fit_and_eval` conventions so it inherits
our leak assertion and bootstrap CI.
Role space for us = `(user, cot, assistant)`. Note this combination was only trained for gpt-oss
upstream; for Qwen3 we are **extending, not reproducing** — say so in the writeup.

**P0.4 — adopt the training-data construction, not just the wrapper.**
From cell 11 (`build_sample_seqs` / `get_sample_seqs_for_input_seq`): base texts are generic web
text, each rendered into **every** role, with a random unrelated `partner_text` of Beta(0.5, 4)
length prepended (or used as the CoT half of `render_mixed_cot`). This derangement is what
decorrelates role from absolute position. **Do not skip it** — without it the probe learns
"position in sequence", which is the absolute-position-index failure class already logged twice in
this repo. We substitute our own benign corpus for C4/dolma3; nothing depends on those datasets.

**P0.5 — adopt the two settings a naive reimplementation silently breaks.**
From `experiments/role-analysis/config/probe.yaml`: (i) `nested_reasoning: true` ⇒ `SKIP_FIRST_N=32`,
i.e. drop the first 32 tokens of every role segment from probe **training** (tag-transition
contamination); (ii) `C` is **not transferable** — upstream spans 5e-3 (gpt-oss) to 1e1 (nemotron).
Sweep `C ∈ [1e-4 … 1e2]` per model on dev only. Skipping the sweep produces Userness numbers that
are a hyperparameter artifact wearing the costume of a finding.

**P0.6 — the Userness/CoTness scalar.**
Per `experiments/agent-injections/01-run-user-injections-gpt-oss.ipynb` cell 15: Userness of a span
= arithmetic **mean over that span's tokens of the probe's predicted probability for class `user`**
at one fixed layer. CoTness = same, off the `cot` column. Clip probabilities at 1e-6 before
aggregation. Report the paired **ratio and difference** against a partner role (their
`user_tool_ratio` / `user_tool_diff`) as well as the raw probability, to control for probe
calibration. Write our own ~5-line numpy version of `run_projections`' shape rather than shimming
its module-level `cupy`.

**P0.7 — content masking and span location.**
Port only `label_qwen3_content_roles` (+ the `label_content_roles` dispatcher) from
`utils/role_assignments.py` and write the Llama-3 / Phi-4 analogues; do **not** vendor all 2205
lines. What we need from it is the `is_content` mask (probes must never train on tag tokens) and
`token_in_seg_ix` (used by both `SKIP_FIRST_N` and the position-robustness check). Their own
docstring says these labellers are largely LLM-generated and validated by token counts — so re-run
that validation (equal content-token counts across roles) on our tokenizers before trusting them.
Better alternative if it proves fiddly: build an offset-based labeller from
`ReconstructableTextDataset` offsets, since we always know the source strings.
For whole-message / injected-region spans adopt `utils/substring_assignments.py::flag_message_types`
— its distinctive value is **ambiguity detection** (raises when one token belongs to two target
strings), which is what you want for nesting/repeating message spans.

**P0.8 — the sanity gate.**
Adopt the four-way validation design from cell 26 (`prep_untagged_conv` / `prep_mistagged_conv`):
tagged / untagged / user_tagged / tool_tagged. The probe is credible only if it scores real user
text as `user` both under correct tags and under no tags, **and** shifts when the same text is
mistagged. `test_seperators` in their config exists solely to keep the untagged control
byte-comparable; carry that idea over.

### (c) Do NOT adopt
- `utils/loader.py::load_model_and_tokenizer` — hardcodes `cache_dir='/workspace/hf'`,
  `dtype='auto'`, `device_map=None` then `.to(device)`, a flash-attn3 kernel for gpt-oss, and raises
  on transformers version mismatches. Conflicts with `ds_common.load_model` (bf16 + sdpa +
  `device_map='auto'`) on every axis and buys nothing. **Ours is better for our stack.**
- `utils/loader.py::load_custom_forward_pass`, `utils/pretrained_models/*` — bespoke per-architecture
  forward passes existing only to expose MoE routing top-k. Their own docstring says simpler hooks
  suffice; `demo/role-probe-demo.ipynb` cell 4 does exactly that. Use our hooks.
- `utils/probes.py` as an import — module-level `cupy`. Rewrite the 10 lines we need.
- Their `tool` / `developer` / `system` roles — no analogue in our chat-only Doublespeak setting.
- `find_word_occurrences_in_text` **stays ours** for the codeword: single-word, case-insensitive,
  left word-boundary enforced, `_offsets_by_decode` fallback for broken offset maps, contiguity
  verified, overlap dedup, returns subtoken ids. RC's is exact/case-sensitive with no word-boundary
  rule. Use `flag_message_types` only for message-level spans.

### ⚠ Blocking decision before any §11 run — activation site
RC trains on `all_pre_mlp_hidden_states` = the **output of `post_attention_layernorm`**, a normalized
mid-block tensor, *not* the residual stream. Our `LayerPatch` / `ComponentOutSwap` / `capture_components`
machinery operates on decoder-layer outputs. Probes fit at one site and applied at the other are not
comparable, and their layer indexing differs too (they keep every 4th layer and index by position in
`layers_to_keep_acts`). `extraction_key='all_hidden_states'` makes the switch a one-word change and is
almost certainly what we want for compatibility with our patching code — but then their published `C`
values are void (see P0.5, which we are doing anyway). **Decide once, record in `RUNMETA`, keep probe
training and projection on the same site.**

---

## 2. interp-jailbreak (IJ) — `external_repos/interp-jailbreak/`

### (a) What we already reuse
Conceptually a lot (see `notes/interp_jailbreak_best_practices.md`, verified accurate against source),
but **no code**. Our `pair_common.capture_components`, `AttentionKnockout`, `resolve_positions`,
`36_pair_attention.py::source_positions`, and `RunDir`/`write_runmeta` already cover the plumbing
their scripts hand-roll.

### (b) Adopt now

**P1 — port the dominance score to HF eager: new `src/boombness/dominance.py`.**
Source: `src/interp/dominance_tools.py::_calculate_hooks_for_dom_scores` (the `get_dot_with_vectors`
closure and the `Y@dir` branch) and `::get_dominance_scores`.
The score is per-`(layer, head, dst, src)`: the einsum reduces **only** over `d_model`, so nothing is
summed over head or src. Two heads:
- `D_attn = einsum('hsd,d->hs', Y_dst, ref) / ref.norm()**2` with `ref = attn_out[dst]`. Dividing by
  `‖ref‖²` (not `‖ref‖`) makes it a *coefficient*, which is why `sum_{h,s} D_attn == 1` — a partition
  of unity we can assert.
- `D_dir = einsum('hsd,d->hs', Y_dst, v/‖v‖)` with `v = v_bomb[l]` from `src/boombness/signals.py::estimate_directions`.
  Signed magnitude in direction units; does **not** sum to 1. This is the §10.1 quantity: *which source
  token wrote bomb-ness into the final carrot position*.

**Our port is genuinely better than theirs, and here is why:** their `get_model_hidden_states`
materializes `Y` for all layers and all destinations — `L·H·T²·d·4` bytes, ≈1.7 GB at T=30 and ≈28 GB at
T=120 for a 2 B model. Our Doublespeak prompts carry 12 demonstrations and are far longer than their
message+20-token suffix, so their function OOMs immediately. §10.1 needs exactly **one** destination
(the final carrot), which collapses `T²` to `T` and makes the computation ~T× cheaper. We also avoid
their pinned TransformerLens fork (`matanbt/TransformerLens@d68e8b5`, not installed here) entirely:
of its three added hooks only `hook_Y_out` is not reconstructible from a stock HF forward, and that is
precisely the all-dst tensor we do not want. **Do not install the fork.**

Recipe (~150 lines):
1. `ds_common.load_model(..., attn_implementation="eager")` (as `DC/next7_attention_retrieval.py:46` already does).
2. Forward hook on `layers[l].self_attn.v_proj` capturing its **output** `[1, T, n_kv*head_dim]`.
   RoPE is applied to Q/K only, never V, so `v_proj` output *is* `X_src W_V` exactly.
3. Reshape `[T, n_kv, head_dim]`, expand to query heads with `n_rep = n_heads // n_kv`, head `h`
   reading kv head `h // n_rep` — this matches HF's `repeat_kv`. **Do not use `torch.repeat`/`tile`;
   the interleave order differs and this is the silent GQA head-mismatch bug.**
4. `W_O` for head `h` = `o_proj.weight[:, h*head_dim:(h+1)*head_dim]`, shape `[d_model, head_dim]`;
   `V_h @ W_O_h.T` = `X_src W_VO`. Assert `o_proj.bias is None` rather than assuming it.
5. `A` from `out.attentions[l][0]` with `output_attentions=True` in the same forward; `model.eval()`.
6. `Y_dst[h,s,:] = A[h, dst, s].unsqueeze(-1) * (V_full[:, h] @ W_O_h.T)` — cost `H·T·d`.
7. **float32 before the einsum**; bf16 will not close the sanity check.

Mandatory gates (adapted from `dominance_tools.py:99-103`, their own closure asserts):
`Y_dst.sum(dim=(0,1)) ≈ attn_out[dst]` to <1e-3, and `D_attn.sum() ≈ 1.0` to <1e-4. Also assert our
named spans are non-overlapping and tile `[0, seq_len)` — partition-of-unity then gives a second free check.
Reducer: copy `get_dominance_scores`' flatten → `topk(k=max(1,int(q·numel)))` → sum body verbatim for
`q ∈ {1.0, 0.1}` (their `'sum'` flavor is literally q=1.0). **Do not** copy its empty-slice behaviour
(prints a warning and `continue`s) — §2.2 forbids silent failures; raise.

**P1b — pair dominance with knockout on the SAME edge set (observation + intervention, their §5/§4 structure).**
`dst = pair_common.resolve_positions(...).codeword_last` (our analogue of their `chat[-1]` canonical
destination). Source sets come straight from `DC/36_pair_attention.py::source_positions`, which already
yields `prev_codewords`, `demos_all`, and `random_matched` — three of §10.1's four required comparisons
for free. Protocol: (1) measure `D_dir` per (layer, head, src) clean; (2) knock out top-q% edges with
`pair_common.AttentionKnockout(model, layer_idxs, query_positions=[codeword_last], blocked_keys=top_edges, heads=...)`
— its additive pre-softmax mask **is** the paper's knockout semantics, remaining mass renormalizes;
(3) re-measure Boombness, ASR, refusal, and the forced-choice comprehension control
(`DC/46_forced_choice_patchscope.py`); (4) repeat ranking by raw `A` and by `random_matched` as the two nulls.
Reporting `D_dir` alongside `A` is worth doing on its own — their grid includes `A` precisely to show
attention weight alone is the weaker predictor.

**P1c — edge suppression as an `attn_out` edit (paper Eq. 6, β=0.1 on top-1%).**
Under HF eager there is no module boundary after the softmax, so the TL `hook_pattern` route has no
analogue — but suppression is **exactly** equivalent to subtracting `(1-β)·Σ_{i∈S} Y[h, dst, i]` from
`attn_out[dst]`, and we already have `Y` (P1) and the output-editing primitives
(`pair_common.SubmodulePatch` / `ComponentOutSwap` on component `attn_out`). Exact, not approximate.
Report suppression and knockout as **separate arms**: suppression does not renormalize the remaining
attention mass, knockout does — the paper leans on that difference. Note `AttentionKnockout` uses
`torch.finfo(dtype).min`; prefer a large finite value in a float32 mask to avoid NaN rows in bf16.
Caveat: `Y` is prefill-only (fixed `dst`); for generation-time necessity fall back to the decode-safe
primitives (`AllPositionProjectOutMultiLayer` etc.).

**P5 — adopt their analysis protocol wholesale for §9/§10 (analysis-side, no GPU).**
This is the part of IJ that is genuinely better than ours. From `src/interp/experiments/grid_hijacking.py`:
keep the strength axis **continuous** (never binarize strong/weak); stratify the prompt-bank sample with
extra-fine bins near zero (`[0, 0.005, 0.01] + arange(step, max, step)`) so the weak tail is not swamped;
**aggregate to one row per unit of analysis before correlating** (`make_box_plot` line 162 groups by
`suffix_id` then aggregates, so n = number of prompt families, not number of rows — the anti-pseudo-replication
step we keep skipping); report **spearmanr**, not Pearson. And the cheapest, most convincing control in the
paper: re-run the correlation restricted to `sample_filter='fail[cannot]'` — samples where the attack failed
with a flat refusal. If dominance still tracks the strength axis within refusals only, the correlation cannot
be an artifact of successful generations simply looking different. **Mandatory arm, not optional.**
Harness shape: one expensive forward per (message, suffix); all metric variants (7 metrics × 2 flavors ×
2 aggregations = 28 numbers) derived on CPU from that single pass; one tidy long-format `rows.jsonl`;
every plotting/statistics script reads only that file and never loads a model.

**P6 — vendor four self-contained utilities → `src/boombness/ext_interp_jailbreak.py`** (with provenance
comments; vendor rather than import, because their package root is `src`, which collides with ours, and
`src.evaluate.utils` drags in `load_data`'s `hf_hub_download` and a read of a harmful-behaviour CSV):
- `get_logits_stats(logits, model_base)` — torch-only; the double-`argsort` maps token_id → rank, so
  refusal/affirm ranks and summed probabilities are free. Feed it `capture_components()['logits_last']`.
  Gives a continuous refusal/compliance readout on every row at zero cost (§5.3, §10).
- `enrich_with_categorization(df, ...)` — pandas-only 10-label taxonomy at bands 0.65/0.35. For us it
  separates "no Boombness" (flat refusal) from "Boombness present but suppressed" (started complying,
  stopped). It is also the enabling machinery for the refusal-only control in P5, so wire it in first.
- `Llama3Model._get_before_after_instr_tok_count` — tokenizer-only sentinel-split measurement of how many
  template tokens precede/follow user content (§2.4 audit). **Do not** copy `gemma2_model.py`, which hardcodes 4/5.
- `ModelBase.calc_gcg_ce_loss` — the reference off-by-one shift (`tmp = inputs.shape[1] - targets.shape[1]`;
  `shift_logits = logits[..., tmp-1:-1, :]`) for §12.
- Plus the `set_period_if_not_exists` invariant (`x if x.endswith('. ') else x + '. '`) into prompt
  construction. It looks cosmetic; it is a load-bearing BPE-boundary rule — without it the suffix's first
  token merges with the message's last token and the computed suffix length is off by one.

### (c) Do NOT adopt
- The pinned TransformerLens fork — see P1. Convenience, not information, and its all-dst tensor OOMs us.
- `get_model_hidden_states` as written — unconditional all-layer `Y`.
- The `'(X@W_VO)@attn'` metric — `X_WVO` is unsqueezed to a dst dim of size 1 (`dominance_tools.py:96`),
  then einsum'd against a ref with `dst = seq`, and `get_dominance_scores:220-221` silently substitutes
  `slice(None)` whenever a dim has size 1. It is quietly measuring something other than its name. Ignore it.
- `ModelBase.calc_sim_with_dir` — dead code; `self.refusal_dir` is never assigned anywhere in the repo.
- Their `results/` convention — entire config encoded in the filename, no run id, no git commit, no
  timestamp, no manifest; `wandb` in requirements with zero call sites. **Our `RunDir` / `write_runmeta` /
  `DONE` contract is strictly better and is mandated by §2.1.**
- `interp/utils.py::get_idx_slices` — pure length arithmetic over a rigid instruction/suffix/template
  layout; it cannot find a *word* inside the instruction, and our codeword occurs many times at variable
  offsets. Keep their **discipline** (spans named, computed in exactly one place, shared by every metric;
  `chat[-1]`-as-canonical-destination) but back it with `pair_common.resolve_positions`.
- `load_data` — `hf_hub_download` of a parquet plus a harmful-behaviour CSV read.
- Their scorer: none ships. `strongreject_finetuned` arrives pre-computed in a HF parquet; only the
  thresholds are in code. Use their thresholds for the taxonomy bands only;
  `DC/scripts/asym_p2_judge.py` remains the authoritative ASR.
- `Qwen2Model._load_tokenizer` sets `use_fast=False`, which kills `return_offsets_mapping` and would
  break our codeword lookup. Force `use_fast=True`. All their wrappers set `padding_side='left'`;
  do all span and dominance work **batch-1** (`AttentionKnockout` is batch-1 only anyway).
- `src/attack/`, `src/defense/` are "Coming soon!" READMEs; `src/evaluate/build_dataset.py` is 0 bytes.
  §10's mitigation arm is a fresh implementation from the paper text regardless.

---

## 3. Chain-of-Thought Hijacking (RD + Hijacking)

### (a) What we already reuse
Nothing directly. `DC/build_refusal_direction_llama.py` and `outputs/stage_gcg_full/refusal_direction_llama_L18.pt`
(+ `refusal_alllayers/`, `refusal_qwen3/`, `refusal_phi/`) are our own refusal-axis stack.

### (b) Adopt now

**P2 — `src/boombness/refusal_dir_adapter.py` + vendored submodules.**
Write a thin `ModelBase`-compatible shim over `ds_common` (`load_model`, `apply_template`) exposing
`.model`, `.tokenizer`, `.tokenize_instructions_fn`, `.eoi_toks`, `.refusal_toks`,
`.model_block_modules`, `.model_attn_modules`, `.model_mlp_modules`. Then vendor
`refusal_direction/pipeline/{utils/hook_utils.py, submodules/generate_directions.py, submodules/select_direction.py}`
under `src/boombness/vendor/refusal_direction/` with a provenance header. Deps: `jaxtyping`, `einops`,
`tqdm`, and `matplotlib` only for `plot_refusal_scores` (no-op it).

**Their selection/validation is clearly better than ours; their data is not.** Ours fits diff-of-means at
the last token over 5 hand-chosen layers and selects by `max(ablate_gain + induce_gain)` with both > 0.
Theirs adds four things we lack: (i) a full **(position × layer)** candidate bank at ~2 forward passes total
(`get_mean_activations` uses `positions = range(-len(eoi_toks), 0)` — every token of the assistant-prefill
suffix, not just the last); (ii) a **KL ≤ 0.1** coherence constraint on harmless prompts that separates
"removed refusal" from "broke the model" — exactly the semantic-remapping / refusal-suppression /
general-destruction trichotomy §10.4 demands, and we have no equivalent; (iii) an explicit
`induce_refusal_threshold ≥ 0` **bidirectional** check (the direction must remove refusal when ablated
*and* induce it when added); (iv) `filter_data`'s pre-filtering of fit prompts to those the model actually
refuses, plus presample-then-trim so n stays fixed across models. `filter_fn` also prunes the last 20% of
layers. **Their machinery, our data:** keep our prompt sets (pooled behavioral `direct` as harmful, the 20
benign harmless items) — do not adopt `refusal_direction/dataset/splits`, a different distribution.

Also take from `hook_utils.py`: `add_hooks` (the contextmanager harness — composes cleanly with our
`LayerPatch`/`ComponentOutSwap`/`AttentionKnockout` since those are also nn.Module hooks);
`get_all_direction_ablation_hooks` (projection removal at `resid_pre` of every block **plus** every
`self_attn` and `mlp` output — the strictly stronger "never present anywhere" ablation our single-site
`LayerPatch` project-out should be compared against); `get_directional_patching_input_pre_hook`
(ablate-then-set, `h := h - (h·d̂)d̂ + coeff·d̂`) as the **dose-controlled** §10.4 arm we currently lack —
it removes the confound that the pre-existing projection differs across prompt families; and
`utils/utils.py::get_orthogonalized_matrix` as a weights-level replication control (a cheap correctness
check on our hook plumbing, and it makes ablated generation as fast as baseline).

Three hard traps, all of which must be handled at vendoring time:
1. Their ablation hooks do **in-place** `activation -= …` on the hook input tuple element, mutating the
   caller's tensor. Running alongside our `LayerPatch`/`ComponentOutSwap` in the same forward this can
   double-apply. Rewrite out-of-place (`activation = activation - …`) and add a unit test that baseline
   logits are bit-identical after a hooked pass with a zero direction. They also normalize `direction`
   in place via `nonlocal` on every call — clean that up too.
2. **Layer-index convention clash.** Their candidate index is `resid_pre` of block L; ours is
   `hidden_states[L+1]` == post-block-L. These are off by one. Their `select_direction` also returns
   positions as **negative** indices into the eoi suffix. Write the translation once, `assert` it, and
   record it in `RUNMETA` — this is precisely the absolute-position-index bug class that has hit this
   repo twice. Do **not** copy `act_add_qwen3_weights`, which indexes `model.layers[layer-1]` for a
   "layer L" act-add — a third convention.
3. `refusal_toks` must be re-derived per model (`[40]` = 'I' for Llama-3 is plausible; Qwen3 and
   Phi-4-mini-reasoning with thinking on almost certainly refuse *after* `</think>`, where a first-token
   score is meaningless). Run P3 first.

**P3 — `src/boombness/diagnose_refusal_readout.py`, before any §10.4 run.** Port both diagnostics:
`diagnose_refusal_scoring.py::prompt_position_checks` / `make_assessment` (does the scored position
actually equal the chat-template assistant prefill, after left-padding? classifies failure as
refusal-token-mismatch vs template/position-mismatch vs mixed) and
`diagnose_reasoning_visible_tokens.py::first_visible_token_after_reasoning` (token-id-level, not
string-level, location of `<think>`/`</think>` then the first non-whitespace token after the close).
Emit their assessment-code JSON shape so a bad readout is a **typed failure**, not a quiet null.
Expect this to FAIL for Qwen3/Phi-4 with thinking enabled — that is the point; it tells us whether §10.4's
refusal metric must be generation-based rather than first-token-logit-based.
`first_visible_token_after_reasoning` is also the only piece of RD usable for §11: it gives the
CoT-span vs visible-answer-span segmentation that must exist before any CoTness probe is trained.
Cheap: 16-32 prompts, 256 new tokens. It is a **gate, not an experiment**.

**P2b — `refusal_score` / `get_refusal_scores` / `kl_div_fn`** (all in `select_direction.py`):
generation-free refusal readout as `log p(refusal) - log(1 - p(refusal))` at `logits[:, -1, :]` in
float64, hook-aware so any intervention scores through the same function. Lets every knockout arm report
a refusal delta at ~1 forward pass. Pair with IJ's `get_logits_stats` (P6) — they are complementary
readouts of the same logits vector.

**P4 — adopt the no-survivor contract.** This is the one run-recording idea in RD better than ours.
When zero candidates pass the filters, `select_direction` writes
`no_survivor_summary.json` with `scientific_status='not_validated_no_surviving_candidates'`,
`failure_counts_by_reason`, `selection_thresholds`, and the nearest-miss candidate by
steering/KL/tradeoff — and returns `(None, None, None)` rather than a best-effort answer. Mirror this in
`src/boombness/surgical_knockout.py`: when no knockout/direction arm passes its controls, write
`causal_claims.md` plus `no_survivor_summary.json` and return `None`. A typed negative-result artifact
plus a hard `None` beats a ledger entry beside a returned best-effort number. Expect this to convert some
currently-reporting arms to "not validated" — that is the intended effect.

### (c) Do NOT adopt
- **`Hijacking/` for §10 or §11 — nothing there.** Grepping the whole package for
  `hook` / `output_attentions` / `hidden_states` / `register_forward` / `knockout` returns **zero hits**.
  It is a purely black-box API attack loop (`core/attack.py` → `core/target.py::TargetLM` →
  `core/judge.py`, driven by `core/runner.py` / `core/workflow.py`), models reached via `litellm` or a
  single local HF `.generate()` wrapper that string-splits on the last `</think>`. **The "hijacking-paper
  style" edge knockout in plan §10.1 must come from our own `AttentionKnockout` + the IJ dominance port
  (P1), not from this repo.** Keep `Hijacking/` only as an ASR-protocol reference (n parallel streams,
  judge-score feedback iterations, `keep_last_n` truncation, `judge_score == 10` as success) if we ever
  need a comparable black-box ASR number. Note `config/parameters.py` imports `google.generativeai` at
  module top, so even importing it fails without that dep.
- `refusal_direction/pipeline/model_utils/model_base.py` as a class — adopt only its **contract**.
  `Llama3Model` builds prompts from a hardcoded `LLAMA3_CHAT_TEMPLATE` string rather than
  `apply_chat_template` (only `Qwen3Model` uses the tokenizer's template), so running their
  `run_pipeline.py` as-is would produce prompts that are **not byte-identical** to
  `ds_common.apply_template` and the resulting direction would not transfer into our runs. That is the
  single strongest argument for vendoring the three submodules under our own shim.
- `refusal_direction/dataset/splits/*` — generic advbench/alpaca-style distribution. **Ours is better
  for our purposes:** pooled behavioral `direct` fields, deliberately concept-agnostic across pairs.
- Their **precomputed artifacts**. `pipeline/runs/{gemma-2b-it, llama-2-7b-chat-hf,
  meta-llama-3-8b-instruct, qwen-1_8b-chat, yi-6b-chat}/direction.pt` are none of our models —
  `meta-llama-3-8b-instruct` is Llama-**3.0**, different weights. The "load a precomputed `.pt`" route
  the sprint currently assumes is **not satisfied**; we must fit our own for
  Llama-3.1-8B-Instruct, Qwen3-14B and Phi-4-mini-reasoning.

---

## 4. Cross-cutting invariants (apply to all adoptions)

1. **Batch-1 for all span/dominance/knockout work.** All three repos assume `padding_side='left'`;
   any batched absolute position index shifts per example. This is the absolute-position-index bug class
   already logged twice here.
2. **Fast tokenizers only** (`use_fast=True`) — `return_offsets_mapping` is load-bearing for both
   `find_word_occurrences_in_text` and `ReconstructableTextDataset`.
3. **float32 before every einsum / probe fit / score.** bf16 will not close the dominance sanity check
   and RD computes its refusal scores in float64 deliberately.
4. **No silent failures (§2.2).** Both RC (`allow_ambiguous`) and IJ (`print WARNING; continue`) have
   permissive paths. Convert to raises. RD's no-survivor JSON is the model to follow.
5. **Vendor, don't import**, for all three: RC has module-level `cupy`; IJ's package root is `src`,
   colliding with ours; RD's `model_utils` hardcodes chat templates. Every vendored file gets a
   provenance header (repo, path, commit if available, date, list of modifications).
6. **Record the convention choices in `RUNMETA`**: activation site (`all_hidden_states` vs
   `all_pre_mlp_hidden_states`), layer-index convention (`resid_pre[L]` vs `hidden_states[L+1]`),
   probe `C` per model, `SKIP_FIRST_N`, and the `dst` position definition. Assert them; do not infer
   them by inspection later.
7. **Keep our house stack where it is better**: `ds_common.load_model`, `apply_template`,
   `build_conditions` (byte-frozen), `find_word_occurrences_in_text`, `resolve_positions`,
   `capture_components`, `RunDir`/`write_runmeta`/`DONE`, `asym_p2_judge.py`, and the
   `DC/src/probes/*` leak-assertion + bootstrap-CI discipline. None of the three reference repos
   improves on any of these.
