# interp-jailbreak: methodology & coding practices worth reusing

> Deliverable for §1 of `docs/BOOMBNESS_OBJECTIVE_SPRINT_PLAN.md`.
> Source: `external_repos/interp-jailbreak/` (Ben-Tov, Geva, Sharif — *Universal Jailbreak Suffixes Are Strong Attention Hijackers*, arXiv 2506.12880).
> Written 2026-08-16 after direct reading of all 1381 lines of `src/` plus six scout reports in `notes/scout/`.
> All paths below are relative to `external_repos/interp-jailbreak/` unless prefixed with `doublespeak_causality/` (= our repo, "DC") or `poc_stage_gcg_early/`.

**Scope note up front.** The public repo is *small and partial*: `src/attack/` and `src/defense/` are "Coming soon!" READMEs, `src/evaluate/build_dataset.py` is a **0-byte file**, and there is **no scorer** — StrongREJECT-finetuned scores ship pre-computed inside a HuggingFace parquet. So the reusable surface is: model/tokenizer loading, prompt→slice arithmetic, the fine-grained attention decomposition, the dominance score, and the grid/plot harness. Everything about mitigation we must write ourselves from the paper text.

---

## 1. How they structure experiments

One experiment = one module under `src/interp/experiments/` exposing a plain Python function plus a `typer` CLI wrapper (`grid_hijacking.py:207-224`). The function takes only scalars/tuples as arguments (`model_name`, `n_messages`, `n_suffixes`, `inspected_dom_scores`, `dst_slc_name`, `src_slc_names`) — there is no config file, no argparse namespace object, no run registry.

The internal shape is the important part, and it is genuinely good:

1. Load model **once**, load the pre-scored dataframe **once**.
2. Sample the design points with a module-level `REPRODUCIBLE_SEED = 42` (`grid_hijacking.py:18`), stratified: suffixes drawn per `univ_score` interval so weak and strong suffixes are equally represented, with extra fine bins `[0, 0.005, 0.01]` at the bottom to keep genuinely non-universal suffixes in the design.
3. **One forward pass per (message, suffix)** — `get_model_hidden_states(...)` caches every tensor the whole metric family needs.
4. Then a pure-CPU `itertools.product` over 7 metrics × 2 flavors × 2 aggregations = 28 derived numbers *from that one pass*.
5. Emit **tidy long format**, one dict per row: `message_id, suffix_id, suffix_category, suffix_univ, response_score, response_category, dom_score_name, dom_score_flavor_name, src, layer, dom_score`, with `layer = -1` as the all-layers sentinel.
6. Analysis (`make_box_plot`) reads only the CSV — it never touches the model.

That "expensive pass once, cheap derived grid in CPU, tidy long CSV, analysis reads only the CSV" separation is the single most transferable structural idea in the repo.

**Adopt for Boombness:** one `capture_components` pass per prompt; derive every Boombness metric variant (logit-lens / direction / probe × layer × occurrence-index × aggregation) on CPU from that pass; write one tidy long-format `rows.jsonl` with an explicit `-1` sentinel for aggregated layers; all plotting/statistics scripts read only that file and never load a model.

---

## 2. How they load models/tokenizers

Two-stage load in `src/interp/utils.py::load_model`:

```python
model_base = construct_model_base(model_name)          # HF model, bf16, device_map="cuda", requires_grad_(False)
tl_model = HookedTransformer.from_pretrained_no_processing(
    model_name, hf_model=model_base.model, device=model_base.device, dtype=torch.float32)
tl_model.cfg.use_attn_in = True
tl_model.cfg.use_attn_result = True
tl_model.cfg.ungroup_grouped_query_attention = True
tl_model.cfg.use_hook_mlp_in = True
tl_model.cfg.n_key_value_heads = tl_model.cfg.n_heads   # HACK for kv-cache under ungrouping
tl_model.cfg.before_instr_tok_count = model_base.before_instr_tok_count
tl_model.cfg.after_instr_tok_count  = model_base.after_instr_tok_count
model_base.del_model(); del model_base
torch.set_grad_enabled(False)
```

Four points that matter:

* `from_pretrained_no_processing` = **no LayerNorm folding, no weight centering, fp32**. This is *required* for their residual decomposition to close numerically (`embed + Σmlp + ΣY == resid[-1]`). Folding LN would break the additivity they assert on.
* They deliberately throw away the HF model after handing its weights to TL, and globally disable grad — interp work is inference-only.
* Chat-template offsets are computed **once at load** and stashed on `cfg`, so every downstream slice computation is O(1) arithmetic.
* Per-family wrappers live in `src/models/{llama3,qwen2,gemma2}_model.py` behind `ModelBase` (`src/models/model_base.py`) with abstract `_load_model / _load_tokenizer / _get_tokenize_instructions_fn / _get_refusal_toks`, plus two methods that are required in practice but **not marked `@abstractmethod`** (`_get_affirm_toks`, `_get_before_after_instr_tok_count`) — a latent hole.

The genuinely reusable trick is `Llama3Model._get_before_after_instr_tok_count` (`src/models/llama3_model.py:103-112`): render the chat template around the sentinel `"DUMMY_TXT_FOR_SPLIT"`, split on it, strip a leading BOS from the prefix string so the tokenizer re-adds it exactly once, and count tokens on each side. Model-agnostic. (`gemma2_model.py` hardcodes 4/5 instead — do not copy that one.)

Env reality check: **TransformerLens is not installed anywhere on this machine** — not in `base`, not in `poc_stage2`, not in `TROPT/.venv`, and certainly not Matan's fork. `hook_X_in` / `hook_X_WVO` / `hook_Y_out` exist *only* in `matanbt/TransformerLens@d68e8b596e097750ec386d6f9f4dd6edaaa4aae7`. Running their `src/interp/*` verbatim requires an isolated env with that fork. Our own stack (`DC/ds_common.py::load_model`) is plain HF bf16 + SDPA and needs no fork.

Traps: `Qwen2Model._load_tokenizer` sets `use_fast=False`, which kills `return_offsets_mapping` — fatal for our word-span lookup; all three families set `padding_side='left'`, so any batched absolute index shifts per example; and `ModelBase.calc_sim_with_dir` is **dead code** (`self.refusal_dir` is never assigned anywhere in the repo, and `direction or self.refusal_dir` raises on a tensor) — no refusal-direction plumbing actually ships.

**Adopt for Boombness:** keep our house loader `doublespeak_causality/ds_common.py::load_model` (bf16 + SDPA, offline HF cache, list-valued EOS preserved) as the single entry point; port only the `DUMMY_TXT_FOR_SPLIT` prefix/suffix token-count trick and the "stash template offsets on the model object once" pattern; force `use_fast=True` everywhere so offset mapping works; do all span work batch-1 / right-padded to dodge the left-padding index shift; treat TransformerLens as an *optional* isolated-env path used only if we want their exact `Y` decomposition.

---

## 3. How they define and cache activations

`src/interp/dominance_tools.py::get_model_hidden_states` is one `model.run_with_cache(toks)` that then materializes a `hs_dict` keyed by friendly names, via an explicit hook-name table:

| friendly | TL hook | shape |
|---|---|---|
| `resid` / `resid_pre` | `blocks.{l}.hook_resid_post` / `hook_resid_pre` | (layer, seq, d) |
| `attn` | `blocks.{l}.hook_attn_out` | (layer, seq, d) |
| `attn_pattern` (`A`) | `blocks.{l}.attn.hook_pattern` | (layer, head, dst, src) |
| `mlp` | `blocks.{l}.hook_mlp_out` | (layer, seq, d) |
| `X_in` | `blocks.{l}.attn.hook_X_in` **(fork only)** | (layer, head, src, d) |
| `X_WVO` | `blocks.{l}.attn.hook_X_WVO` **(fork only)** | (layer, head, src, d) |
| `Y` | `blocks.{l}.hook_Y_out` **(fork only)** | (layer, head, dst, src, d) |

Discipline worth copying: `gc.collect()` + `torch.cuda.empty_cache()` **before and after** the cached pass, and `cache = cache.to('cpu')` immediately. They also build a `decompose_resid` view and split it into `__embed` / `__attns` / `__mlps` by the even/odd stride `range(1, 2*n_layers, 2)` / `range(2, 2*n_layers+1, 2)` — note index 0 is the **embedding**, exactly the off-by-one that bites us.

Their acceptance test is inline (`dominance_tools.py:100-103`, `apply_sanity_checks=True`):

```python
(decompose_resid__attns[5] - Y[5].sum(dim=(0,2))).abs().max()          # Σ_{h,src} Y == attn term
((embed + mlps.sum(0) + Y.sum((0,1,3))) - resid[-1]).abs().max()       # full decomposition closes
```

Do not reuse the *function*: it unconditionally materializes `Y` for **all** layers, which is `L·H·T²·d·4` bytes — ~1.7 GB at T=30 and ~28 GB at T=120 for gemma-2-2b, and ~19 GB for gemma-2b at seq=100. Our Doublespeak prompts (12 demos!) are far longer than their `message + 20-token suffix`, so a verbatim port OOMs immediately.

**Adopt for Boombness:** reuse the hook-name table and the gc/`empty_cache`/`.to('cpu')` discipline, and reuse the two-line decomposition sanity assert as a unit test — but capture with our `doublespeak_causality/pair_common.py::capture_components`, which already returns `{comp: Tensor[n_layers, n_pos, H]}` in float32 on CPU with the embedding row dropped, and **never** materialize `Y` for all layers: take `hook_pattern` (L·H·T², ~4600× cheaper) plus targeted per-layer recomputation of `X W_VO` only at the read layer.

---

## 4. How they implement attention/path localization

Localization is entirely **span arithmetic**, in `src/interp/utils.py::get_idx_slices(model, message, suffix, response_str="")`. Given the two template token counts cached on `cfg`, everything else is derived from lengths:

```python
input_len       = to_toks(message + suffix, model)[0].shape[1]
adv_suffix_len  = tokenizer.encode(suffix, add_special_tokens=False).shape[1]
slcs = dict(
  bos      = slice(0, 1),
  chat_pre = slice(1, chat_pre_len),
  instr    = slice(chat_pre_len, input_len - adv_suffix_len - chat_suffix_len),
  adv      = slice(input_len - adv_suffix_len - chat_suffix_len, input_len - chat_suffix_len),
  chat     = slice(input_len - chat_suffix_len, input_len),
  affirm   = slice(input_len, input_len + affirm_tok_len),
  bad      = slice(input_len + affirm_tok_len, None),
  input    = slice(chat_pre_len, input_len - chat_suffix_len))
slcs['chat[-1]']  = slice(slcs['chat'].stop - 1, slcs['chat'].stop)
slcs['chat[:-1]'] = slice(slcs['chat'].start, slcs['chat'].stop - 1)
```

`chat[-1]` — the very last template token before generation — is the canonical **destination**; `adv` is the canonical **source**. Everything in the paper is "how much of `chat[-1]`'s attention output came from `adv`". Path localization is then just `tensor[:, :, dst_slc, src_slc]`.

The strength of this design is that spans are *named*, computed in exactly one place, and shared by every metric — which is precisely the discipline we lack (our absolute-position-index bug class, memory `feedback_absolute_position_index_bug.md`). The weakness is that it assumes a rigid three-part layout (instruction, then suffix, then template) and cannot find a *word* inside the instruction. Our codeword occurs many times, mid-prompt, at variable offsets.

Note also `set_period_if_not_exists` in `src/evaluate/utils.py:63`, which coerces every message to end with `". "`. This looks cosmetic but is a load-bearing BPE-boundary invariant: without it, the suffix's first token merges with the message's last token and `adv_suffix_len` is wrong by one.

**Adopt for Boombness:** keep the *named-span-registry* idea and the `chat[-1]` destination convention, but replace length arithmetic with offset-mapping word lookup — `DC/ds_common.py::find_word_occurrences_in_text` / `DC/pair_common.py::resolve_positions` — producing a span dict `{bos, chat_pre, demos, codeword_occ_0..k, codeword_last, query, chat, chat[-1]}` computed once per prompt and passed to every metric; carry over the trailing-`". "` boundary invariant; add an assert that spans are non-overlapping and cover `[0, seq_len)`.

---

## 5. How they quantify hijacking (dominance score)

The whole numerical contribution is ~4 lines in `dominance_tools.py::_calculate_hooks_for_dom_scores`. Decompose each attention output into per-(dst, src) transformed vectors `Y[l,h,t,s,:] = A[l,h,t,s] · X_s W_VO`, then project onto a reference vector and normalize:

```python
dot = torch.einsum('lhtsd,lktkd->lhts', main_vecs, ref_vecs)   # layer, head, dst, src
dot = dot / torch.norm(ref_vecs, dim=-1).pow(2)
```

With `ref = attn_out` (metric `Y@attn`, paper Eq. 3) the scores over all sources **sum to 1** — a partition of unity, so "fraction of this position's attention output contributed by that span" is literally true. Variants: `Y@resid`, `Y@dcmp_resid`, `(X@W_VO)@attn` (looks broken — einsum `t=1` vs `t=seq` mismatch), plus norm-only `norm(X)`, `norm(Y)`, raw `A`, and — the one we care about — **`Y@dir`**:

```python
hs_dict['Y@dir'] = torch.einsum('lhtsd, ld -> lhts', Y[:, :, dst_slc],
                                given_dir / given_dir.norm(dim=-1, keepdim=True))
```

That is per-(layer, head, dst, src) attribution *along an arbitrary direction* — i.e. exactly "which source token wrote bomb-ness into position *t*".

Aggregation (`get_dominance_scores`): slice `[:, :, dst_slc, src_slc]` → flatten from dim 1 (or dim 0 if `aggr_all_layers`) → `topk(k = max(1, q · numel))` → `.sum(-1)`. Flavor `'sum'` is just `q = 1.0`. Result: `{src_name: [n_layers]}`, or a singleton list when aggregated. Empty slices are skipped with a printed WARNING rather than an exception — a silent-failure pattern our §2.2 rules forbid.

Paper-reported read layers and Spearman ρ(univ_score, dominance): Gemma-2-2b L20 ρ=0.425, Qwen2.5-0.5B L15 ρ=0.620, 1.5B L21 ρ=0.650, 32B L35 ρ=0.719; Llama-3.1-8B L14.

**Adopt for Boombness:** implement `Y@dir` with our `v_bomb[L]` as `given_dir` — this is the natural bridge from "Boombness exists in the residual" to "Boombness *flowed from* the demo tokens"; reuse the flatten→`topk(q)`→`sum` aggregator verbatim as our per-layer reducer (with `q ∈ {1.0, 0.1}`); keep the partition-of-unity `Y@attn` as the sanity-anchored baseline; but raise, not `print`, on an empty slice.

---

## 6. How they compare weak vs strong suffixes

They never binarize. Every suffix carries a continuous `univ_score` = its mean StrongREJECT-finetuned score across all messages (`load_data`, computed as `df.groupby('suffix_id').strongreject_finetuned.mean()`), plus a `suffix_rank`. Then:

* **Stratified sampling** over `univ_score` intervals at design time so the weak tail is not swamped.
* **Aggregate to one point per suffix** before correlating: `agg_df = df.groupby('suffix_id').agg({'suffix_univ':'first', 'dom_score':'mean'})` — i.e. average out the message axis, so *n* = number of suffixes, not rows. This is the correct unit of analysis and avoids pseudo-replication.
* **`spearmanr(agg_df.suffix_univ, agg_df.dom_score)`** — rank correlation, not Pearson.
* Presentation: `pd.cut` into bins `[0, 0.01, 0.05] + arange(0.10, max, 0.10)`, plotly boxplot per bin, plus a crimson **median** trendline over bins.
* **The key control:** `sample_filter='fail[cannot]'` restricts to samples where the attack *failed with a refusal*. If dominance still tracks universality within only-failures, the correlation cannot be an artifact of "successful attacks look different because the response is different". This is the cheapest and most convincing confound check in the paper, and it costs nothing.

Also available for free: `data/other_suffix_dists.json` gives 9 non-GCG baseline suffix families (`style_`, `start-with_`, `pointless_greeting_`, `random_fact_`, `sure_suffixes_{0,1,2}`, `random_letters_`, `random_words_`) — a ready-made null distribution for "is this just any suffix?".

**Adopt for Boombness:** treat "Boombness level" as continuous, never as strong/weak buckets; stratify prompt-bank sampling across the Boombness axis with extra-fine bins near zero; aggregate to one row per *prompt family* before correlating and report Spearman ρ with a group bootstrap CI; and mandatorily re-run the correlation restricted to refused-only generations as the success-confound control (plan §9).

---

## 7. How they run evaluation and scoring

There is **no scorer in the repo**. `strongreject_finetuned` arrives pre-computed inside `MatanBT/gcg-evaluated-data` (`hf_hub_download(repo_id=..., filename=f"{model_name.split('/')[-1]}_eval_data.parquet")`). Only the *thresholds* live in code: `success_thr = 0.65`, `fail_thr = 0.35`, non-trivial message `prefilled__strongreject_finetuned < 0.25`, hard message `> 0.75`.

What *is* reusable is the layered, judge-free readout stack:

1. **`get_logits_stats(logits[vocab], model_base)`** — softmax, top-5, then the double-`argsort` rank trick (`logits_ranks = argsort(argsort(probs, descending=True))`, which maps token id → rank) to report `probs__refusal_top_rank`, `probs__refusal_sum_probs`, `probs__affirm_top_rank`, `probs__affirm_sum_probs`. Continuous, free, computed at the first generated token. Token ids are hardcoded per family: Llama-3 refusal `[40]` ('I') / affirm `[40914]` ('Sure'); Qwen `[40, 2121]`; Gemma `[235285, 1718, 107, 1]`.
2. **`enrich_with_categorization`** — a 10-label response taxonomy combining first-token-id ∈ refusal/affirm toks, `'cannot'`/`'sure'` in the first 200 chars, and `x.count('.') == 1`, crossed with the score thresholds: `fail[cannot]`, `fail[sure_eos]`, `fail[sure_cannot]`, `fail[sure_other]`, `fail[other]`, `success[sure]`, `success[cannot_sure]`, `success[cannot_~sure]`, `success[other]`. This distinguishes "flat refusal" from "started complying then stopped" — for us, the difference between *no Boombness* and *Boombness present but suppressed*.
3. **Prefilled generation** — `ModelBase.generate_batch(messages, prefix_fillers=...)` forces a per-message response prefix; this is how the `prefilled__` column is produced, and it is the "capability floor" control (does the model *know* the answer if refusal is bypassed?).
4. **`calc_gcg_ce_loss(messages, target)`** with the correct shift indexing `logits[..., len(inputs)-len(targets)-1 : -1]`, broadcasting a single target across many messages.

**Adopt for Boombness:** three-tier readout — (a) free logits stats on the first generated token via the double-argsort rank trick with our Llama-3/Qwen/Phi refusal+affirm ids, (b) the 10-label response taxonomy as a diagnostic column on *every* row, (c) our sanctioned API judge `DC/scripts/asym_p2_judge.py` (StrongREJECT rubric, `--mal-threshold 0.5`, hard-fails if `judge_null_frac > 0.05`) as the authoritative ASR; adopt their 0.65/0.35 threshold pair for the "clear success / clear fail" bands used by the taxonomy only, and keep prefilled generation as the comprehension/capability floor.

---

## 8. How they organize results, seeds, configs, and plots

Honestly: **this is the weakest part of the repo, and we should not copy it.** A bare `results/` directory created on demand; the entire configuration encoded in the filename —

```
results/grid_hijacking[chat[-1]]_google_gemma-2-2b-it-n=[30, 400].csv
```

— no run id, no config serialization, no git commit, no timestamp, no manifest. `wandb` is in `requirements.txt` with **zero call sites**. Seeding is a single module constant `REPRODUCIBLE_SEED = 42` used for `random.seed`, with a second inline `random.seed(42)` inside `load_data`; `torch`/`numpy` are never seeded (defensible, since generation is `do_sample=False` and the analysis is deterministic).

The two things worth keeping: (a) the **tidy long CSV** as the sole interchange format between compute and analysis, and (b) plots as pure functions of a CSV path — `make_box_plot(csv_path, layer=20, slc_src_name='adv', dom_score_name='Y@attn', dom_score_flavor_name='sum', sample_filter=None, save_fig=False)` — re-runnable, vector PDF output, no hidden state.

Our own conventions are strictly better and are already mandated by plan §2.1: `DC/ds_common.py::write_runmeta(out_dir, args, extra)` (RUNMETA/1: git commit + dirty flag, seed, full argv, SLURM job id + nodelist, GPU model, library versions; a second call merges `lm.meta()` with model/tokenizer revision) written *first*, and `write_done(out_dir, rows_written, extra)` (DONE/1) written *last*; run dirs named `outputs/<prefix>_<ModelTag>_<timestamp>_<SLURM_JOB_ID or PID>`; configs in `configs/manifests/*.json`. `src/boombness/common.py` already implements `RunDir`, `FailureLedger`, and `seed_everything`.

**Adopt for Boombness:** their tidy-long-CSV + plots-are-pure-functions-of-a-CSV pattern, dropped into *our* run-dir contract — every experiment writes `RUNMETA.json` first, `rows.jsonl` (tidy long) during, `DONE.json` last, under `outputs/boombness/<experiment>/<run_id>/`, with the config YAML from `configs/boombness/*.yaml` copied into the run dir verbatim; never encode configuration in a filename; seed `random`, `numpy`, and `torch` through `src/boombness/common.py::seed_everything` and record the seed in RUNMETA.

---

## 9. How they implement surgical mitigation

**It is not in the repo.** `src/attack/` and `src/defense/` contain only "Coming soon!". There is no `add_hook`, no `run_with_hooks`, no intervention code anywhere in `src/`. We must implement the paper's §4 from the text. The spec, in TransformerLens terms:

* **Knockout (paper §4.1, "jailbreak flip rate" JFR ≈ 1 for `adv → chat`).** Hook `blocks.{l}.attn.hook_attn_scores`, shape `[batch, head, q, k]`, and set

  ```python
  t[:, heads, dst_slc, src_slc] = -1e5   # pre-softmax; softmax then renormalizes over remaining sources
  ```

  Because it is applied pre-softmax, the remaining attention mass is redistributed — this is "the destination cannot see the source at all".

* **Suppression (paper Eq. 6, β = 0.1 on the top-1 % of edges ranked by `A[j,i]`).** Hook `blocks.{l}.attn.hook_pattern` (post-softmax) and

  ```python
  t[:, h, dst, src] *= beta          # deliberately NO renormalization
  ```

  Scaling the pattern is *exactly equivalent* to scaling the transformed vector, since `Y_{i→j} = A_{j,i} · X_i W_VO`, and is ~4600× cheaper than materializing `Y`.

* Attach via `model.run_with_hooks(toks, fwd_hooks=[...])`, or `with model.hooks(...)` wrapped around `generate`.

Landmine, stated explicitly in their own `generate`: **`use_past_kv_cache` must stay `False`** (it defaults to `False` in `utils.py::generate`). With the KV cache on, the query dimension collapses to 1 during decoding and every absolute `dst` index silently means something different. Second landmine: with `ungroup_grouped_query_attention=True` plus the `n_key_value_heads = n_heads` hack, head indices are **query** heads, not KV heads.

Our repo already has the HF-native equivalents, which are better tested for our stack: `DC/pair_common.py::AttentionKnockout(model, layer_idxs, query_positions, blocked_keys, heads=None)` (4-D additive mask; **requires `attn_implementation="eager"`**, raises if the mask is not 4-D, batch-1 only), `DC/ds_common.py::LayerPatch(..., mode="replace"|"add"|"project_out")` (prefill-only, generation-safe), and the decode-safe family `AllPositionProjectOutMultiLayer` / `AllPositionAdd(MultiLayer)` / `AllPositionMLPAblate` / `AllPositionZHeadAblate` — the only primitives valid during generation-time necessity tests, with `SinglePositionProjectOut` as the pre-registered scope-matched control.

**Adopt for Boombness:** implement edge *knockout* (pre-softmax `-1e5`) and edge *suppression* (post-softmax `×β`, no renorm) on our `AttentionKnockout` (eager attention, batch-1) rather than porting TL hooks; adopt their JFR metric — fraction of successful attacks flipped to refusal by the edit — as the headline mitigation number; adopt their β = 0.1 / top-1 %-of-edges parameterization as the starting point; and pair every edit with a scope-matched random-edge control plus the forced-choice comprehension check (`DC/46_forced_choice_patchscope.py::PatchscopeForcedChoice`) so that "lowered ASR" is never reported as "causal understanding" (plan §2.6).

---

## 10. What to copy/adapt for our Boombness experiments

Ranked by value, with the verdict:

| # | Their thing | Verdict |
|---|---|---|
| 1 | Tidy-long-CSV + one-forward-pass-many-metrics harness (`grid_hijacking`) | **Copy the shape** |
| 2 | `Y@dir` einsum — per-(layer, head, dst, src) attribution along an arbitrary direction | **Copy the math**, feed `v_bomb[L]` |
| 3 | Named span registry (`get_idx_slices`) computed once, shared by all metrics | **Copy the idea**, replace arithmetic with offset-mapping word lookup |
| 4 | `topk(q)` → `sum` per-layer aggregator | **Copy verbatim** |
| 5 | Decomposition sanity asserts (`Σ Y == attn`, `embed + Σmlp + ΣY == resid`) | **Copy as a unit test** |
| 6 | Continuous strength axis + per-suffix aggregation + Spearman + `fail[cannot]`-only control | **Copy the analysis protocol** |
| 7 | `get_logits_stats` double-argsort rank readout + 10-label response taxonomy | **Copy** as free diagnostics |
| 8 | `DUMMY_TXT_FOR_SPLIT` template-offset trick | **Copy** |
| 9 | Trailing `". "` BPE-boundary invariant | **Copy** |
| 10 | Attention edge knockout / suppression spec (paper §4, absent from code) | **Write fresh** on our `AttentionKnockout` |
| — | `get_model_hidden_states` materializing all-layer `Y` | **Do not reuse** — O(L·H·T²·d), OOM on our long prompts |
| — | `results/` + config-in-filename + no run metadata | **Do not reuse** — use our RUNMETA/DONE contract |
| — | `calc_sim_with_dir` | **Dead code**, ignore |
| — | `(X@W_VO)@attn` metric | Likely buggy einsum; ignore |

**Adopt for Boombness:** build `src/boombness/` as our-infrastructure-plus-their-methodology — DC loaders, DC span resolution, DC intervention primitives, DC run-dir contract, carrying over from the paper exactly four things: the `Y@dir` attribution math, the named-span discipline, the one-pass/many-derived-metrics tidy-CSV harness, and the analysis protocol (continuous axis, per-group aggregation, Spearman, refusal-only confound control, JFR for mitigation). See `notes/boombness_reuse_inventory.md` for the file-by-file allocation.
