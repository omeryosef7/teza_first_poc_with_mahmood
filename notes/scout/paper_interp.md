# Scout: `interp-jailbreak` (Ben-Tov, Geva, Sharif — "Universal Jailbreak Suffixes Are Strong Attention Hijackers", arXiv 2506.12880)

Repo root: `/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood/external_repos/interp-jailbreak`
(identical copy at `.../teza_first_poc_with_mahmood/interp-jailbreak`, which additionally holds the paper PDF
`2506.12880v2_universal_jailbreak_suffixes_are_strong_attention_hijackers.pdf`).

Total interp surface is tiny: `src/interp/dominance_tools.py` (246 L), `src/interp/utils.py` (217 L),
`src/interp/experiments/grid_hijacking.py` (225 L), `src/evaluate/utils.py` (170 L), `src/models/*` (~500 L), `demo.ipynb` (13 cells).
`src/attack/README.md` and `src/defense/README.md` are both literally "Coming soon!" — **the GCG-Hij attack and the
Hijacking-Suppression defense are NOT in this repo.** Everything below about interventions is either paper-spec or my
reconstruction.

**Hard dependency:** a *fork* of TransformerLens, pinned in `requirements.txt`:
```
transformer-lens @ git+https://github.com/matanbt/TransformerLens.git@d68e8b596e097750ec386d6f9f4dd6edaaa4aae7
```
It is **not installed anywhere on this machine** (`import transformer_lens` → ModuleNotFoundError; no vendored copy).
The fork's only claimed delta (README §Additional Research Artifacts) is "fine-grained attention hooks to enable the
calculation of dominance score", i.e. the three hooks + the `cfg.use_attn_fine_grained` flag + `set_use_attn_fine_grained()`
listed below. Everything else is upstream TL.

---

## 1. Dominance score (Eq. 3)

### 1.1 Math (paper §5.1)

Residual decomposition (Elhage et al.):
`X_j^(l) = X_j^(l-1) + MLP(X_j^(l-1)) + Y_{*→j}^(l)`, and the attention sub-layer output decomposes into
**transformed vectors** (Kobayashi et al. 2020/2021):

```
Y_{*→j}^(l) = Σ_h Σ_{i ≤ j} Y_{i→j}^(l,h)      with     Y_{i→j}^(l,h) = A_{j,i}^(l,h) · X_i^(l-1) W_VO^(l,h)      (Eq. 1)
```

Eq. 3 (dominance of token-subsequence `T` on `j := chat[-1]`, at layer `l`):

```
D̂_T^(l) = < Σ_{i∈T, h} Y_{i→chat[-1]}^(l,h) ,  Y_{*→chat[-1]}^(l) >  /  || Y_{*→chat[-1]}^(l) ||²
```

i.e. the scalar projection coefficient of `T`'s contribution onto the *total* attention output at that layer.
Key property the paper leans on: `Σ_{all i} D̂_i^(l) = 1` — the score is a **partition of unity over source
positions**, so "adv dominance" is directly "fraction of the layer's attention output that came from the suffix".
That is what makes it comparable across prompts/layers with no normalization tricks.

### 1.2 Exact implementation

`src/interp/dominance_tools.py`

```python
def get_dominance_scores(
    model: HookedTransformer,
    msg: str, suffix: str,
    hs_dict: Dict[str, torch.Tensor] = None,
    dst_slc_name: str = 'chat[-1]',
    src_slc_names: Tuple[str] = ('bos','chat_pre','instr','adv','chat[:-1]','chat[-1]'),
    dominance_metric: str = 'Y@attn',
    dominance_metric_flavor: str = 'sum',          # 'sum' | 'sum-top_q'
    dominance_metric_flavor_q: float = 0.1,
    aggr_all_layers: bool = False,
) -> Dict[str, List[float]]                        # src_name -> list of len n_layers (or singleton)
```

The numerator/denominator live in the closure `get_dot_with_vectors` inside
`_calculate_hooks_for_dom_scores(hs_dict, selected_dom_scores, given_dir, dst_slc)`:

```python
main_vecs = main_vecs[:, :, dst_slc]                                   # l, h, dst, src, d
ref_vecs  = ref_vecs[:, dst_slc].unsqueeze(-2).unsqueeze(-2).transpose(1, 2)  # l, 1, dst, 1, d
dot_prod_vals = torch.einsum('lhtsd,lktkd->lhts', main_vecs, ref_vecs)  # l, h, dst, src
dot_prod_vals = dot_prod_vals / torch.norm(ref_vecs, dim=-1).pow(2)     # normalize per (layer, dst)
return dot_prod_vals.cpu()
```

So the code computes the **per-(layer, head, dst, src) projection coefficient**, and only *then* sums.
Because the projection is linear in the numerator, `flavor='sum'` over a full slice is **exactly Eq. 3**;
`flavor='sum-top_q'` (top-q fraction of the flattened entries, `q=0.1` default) is a deliberate variant, not Eq. 3.

Reduction, at the end of `get_dominance_scores`:

```python
dim_to_start_reduce = 1 if not aggr_all_layers else 0
flatten_vecs = dominance_score_dict[src][ :, :, dst_slc, src_slc ].flatten(start_dim=dim_to_start_reduce)
k = max(1, int(dominance_metric_flavor_q * flatten_vecs.shape[-1]))   # q forced to 1.0 when flavor=='sum'
out = flatten_vecs.topk(k=k, dim=-1, largest=True, sorted=False).values.sum(dim=-1)
```

**Reduction axes:** heads are summed (never head-resolved in the output), dst is summed over the dst slice
(normally a single token, `chat[-1]`), src is summed over the chosen span. Layer is *kept* unless
`aggr_all_layers=True`, in which case layer is folded into the flatten too and you get a scalar (returned as a
singleton list). Note the top-q with `aggr_all_layers=True` selects across layers as well — different semantics
from per-layer top-q. `topk(..., sorted=False)` is a small speed win since only the sum is needed.

### 1.3 Tensors consumed (`get_model_hidden_states`)

```python
def get_model_hidden_states(model, toks, return_labels=False, force_output_prefix=None,
                            apply_sanity_checks=False,
                            add_dominance_calc=False,
                            given_dir: Float[Tensor,"n_layer d_model"] = None,
                            selected_dom_scores: List[str] = ['Y@attn'])
    -> (hs_dict, cache)  |  (hs_dict, hs_dict_labels, cache)
```

Hook name table (the three `X_in`/`X_WVO`/`Y` are **fork-only**):

| key | TL hook | shape after stacking |
|---|---|---|
| `resid` | `blocks.{l}.hook_resid_post` | l, seq, d |
| `resid_pre` | `blocks.{l}.hook_resid_pre` | l, seq, d |
| `attn` | `blocks.{l}.hook_attn_out` | l, seq, d |
| `attn_pattern` (alias `A`) | `blocks.{l}.attn.hook_pattern` | l, head, dst, src |
| `mlp` | `blocks.{l}.hook_mlp_out` | l, seq, d |
| `X_in` | `blocks.{l}.attn.hook_X_in` | l, head, src, d |
| `X_WVO` | `blocks.{l}.attn.hook_X_WVO` | l, head, src, d → `.unsqueeze(2)` → l, h, 1, src, d |
| `Y` | `blocks.{l}.hook_Y_out` | **l, head, dst, src, d** (per-layer cache entry is `1, h, T, T, d`) |

Plus derived: `decompose_resid`, `decompose_resid__embed / __attns / __mlps`, `decompose_resid_coar`
(embed + Σ mlp + Σ attn folded per layer), legacy alias `resids_pre_attn = X_in`.

Available `dominance_metric` values (asserted): `'Y@attn'` (default, = Eq. 3), `'Y@resid'`, `'Y@dcmp_resid'`,
`'(X@W_VO)@attn'`, `'norm(X)'`, `'norm(Y)'`, `'Y@dir'`, `'A'`. The reference vector per variant:

```python
dom_score_to_args = {
    'Y@resid':        (hs_dict['Y'], hs_dict['resid']),
    'Y@dcmp_resid':   (hs_dict['Y'], hs_dict['decompose_resid_coar']),
    'Y@attn':         (hs_dict['Y'], hs_dict['attn']),
    '(X@W_VO)@attn':  (hs_dict['X_WVO'], hs_dict['attn']),
}
```
`'Y@dir'` projects `Y` onto a supplied unit direction (`given_dir`, per-layer `l d` or global `d`) — this is the
"principal direction / diff-in-means" variant of hijacking strength the paper mentions (§6, App. B.4), and is the
one that connects to a refusal-direction-style analysis. `norm(X)` / `norm(Y)` are plain magnitudes, shaped to 4D
so the same slicing code works.

**Gotchas found by reading:**
- `_calculate_hooks_for_dom_scores` takes a `dst_slc` arg and then immediately overwrites it:
  `dst_slc = slice(None, None)` on the first line. The arg is dead; slicing always happens later in
  `get_dominance_scores`.
- `'(X@W_VO)@attn'`: `main_vecs` has `t=1` while `ref_vecs` has `t=seq_len`; `torch.einsum` does **not** broadcast
  mismatched named dims, so this metric will raise unless `seq_len==1`. `grid_hijacking` lists it in the default
  `inspected_dom_scores` — expect it to blow up (untested here; TL not installed). Same suspicion applies to
  `norm(X)` only in the sense that its dst dim is 1, but that one is handled by the `shape[-2] > 1` guard in
  `get_dominance_scores`, so it's fine.
- Empty spans are skipped with a printed WARNING, and the src key is then simply **absent** from the returned dict —
  downstream code must not assume all requested keys exist.
- `cache` is moved to CPU immediately (`cache = cache.to('cpu')`), with `gc.collect(); torch.cuda.empty_cache()`
  bracketing the forward pass on both sides.

### 1.4 Self-check the authors ship (`apply_sanity_checks=True`)

```python
"decomp vs Y:", (hs_dict['decompose_resid__attns'][5] - hs_dict['Y'][5].sum(dim=(0,2))).abs().max()
"decomp (w/ y) vs resid:", ((hs_dict['decompose_resid__embed'] + hs_dict['decompose_resid__mlps'].sum(0)
                             + hs_dict['Y'].sum(dim=(0,1,3))) - hs_dict['resid'][-1]).abs().max()
```
Worth porting verbatim as the acceptance test for any re-implementation of `Y`: summing `Y` over (head, src) must
reproduce the attention-out term, and the full re-composition must reproduce the final residual.

---

## 2. Span localization: token positions and layer windows

`src/interp/utils.py::get_idx_slices(model, message, suffix, response_str="") -> Dict[str, slice]`

Spans are **plain python `slice` objects in a dict**, computed arithmetically from four lengths — no token search,
no string matching:

```python
input_len       = to_toks(message + suffix, model)[0].shape[1]
chat_pre_len    = model.cfg.before_instr_tok_count
adv_suffix_len  = model.tokenizer.encode(suffix, return_tensors="pt", add_special_tokens=False).shape[1]
chat_suffix_len = model.cfg.after_instr_tok_count
slcs = dict(
    bos      = slice(0, 1),
    chat_pre = slice(1, chat_pre_len),
    instr    = slice(chat_pre_len, input_len - adv_suffix_len - chat_suffix_len),
    adv      = slice(input_len - adv_suffix_len - chat_suffix_len, input_len - chat_suffix_len),
    chat     = slice(input_len - chat_suffix_len, input_len),
    affirm   = slice(input_len, input_len + affirm_tok_len),
    bad      = slice(input_len + affirm_tok_len, None),
    chat3_affirm3 = slice(input_len - 3, input_len + 3),
    chat_s2  = slice(input_len - 2, input_len),
    input    = slice(chat_pre_len, input_len - chat_suffix_len),   # instr + adv
)
slcs['chat[-1]']  = slice(slcs['chat'].stop - 1, slcs['chat'].stop)   # THE destination token
slcs['chat[:-1]'] = slice(slcs['chat'].start, slcs['chat'].stop - 1)
```

- `affirm_tok_len` comes from `enrich_with_affirm_length(df, tokenizer, ...)` (same file), a heuristic that takes
  the first line / first sentence of the response, splits again on the first `:` or `,` after char 10, trims to 20
  tokens, and falls back to the first 5 tokens if empty. Defaults to 20 when `response_str=""`
  (`affirm_tok_len = affirm_tok_len or 20`). It also supports `set_mock_affirm_prefix=True` →
  `"Sure, here is exactly what you need to do.\n"`, and `pad_to_max_tokens` (padding by appending `'\n-'` — the
  author's own comment calls it "an ugly hack").
- `before_instr_tok_count` / `after_instr_tok_count` are attached to `tl_model.cfg` in `load_model()` from the
  `ModelBase`. Gemma2 hardcodes them (`GEMMA2_PRE_INSTRUCT_TOK_COUNT = 4`, `GEMMA_POST_INSTRUCT_TOK_COUNT = 5`);
  **Llama3 and Qwen2 derive them properly** — copy this one:
  ```python
  str_before, str_after = tokenizer.apply_chat_template(
      [{"role":"user","content":"DUMMY_TXT_FOR_SPLIT"}], tokenize=False, add_generation_prompt=True
      ).split("DUMMY_TXT_FOR_SPLIT")
  if tokenizer.bos_token and str_before.startswith(tokenizer.bos_token):
      str_before = str_before.replace(tokenizer.bos_token, "")
  n_before = len(tokenizer(str_before)["input_ids"])                       # includes BOS
  n_after  = len(tokenizer(str_after, add_special_tokens=False)["input_ids"])
  ```
- **The whole span algebra assumes `prompt == message + suffix` concatenated as one user turn** and that the
  tokenizer does not merge across the message/suffix boundary. `load_data` in `src/evaluate/utils.py` enforces
  `message_str` ends with `". "` precisely to stabilize that boundary.
- **Layer windows** are *not* a data structure — they are ad hoc:
  - `grid_hijacking` emits one row per layer and lets the plotting stage filter (`layer == 20` default for Gemma2).
  - Paper §5.2 aggregates over the **upper half of layers**; §6 reads a **single layer** per model
    (Gemma2 L20, Qwen2.5-0.5B L15, Qwen2.5-1.5B L21, Qwen2.5-32B L35, Llama3.1-8B L14).
  - Paper §7.1 uses `l1 = floor(0.1·L)`, `l2 = ceil(0.9·L)` for the GCG-Hij loss window.
  - `aggr_all_layers=True` in code encodes layer `-1` in the dataframe.

---

## 3. Hijacking strength: per-suffix aggregation and the universality correlation (Fig. 8/9)

Two functions in `src/interp/experiments/grid_hijacking.py`.

### 3.1 Grid producer

```python
def grid_hijacking(model_name="google/gemma-2-2b-it", n_messages=30, n_suffixes=400,
                   suffix_interval_diff=0.05,
                   inspected_dom_scores=('Y@attn','A','Y@resid','Y@dcmp_resid','(X@W_VO)@attn','norm(X)','norm(Y)'),
                   dst_slc_name='chat[-1]', src_slc_names=('instr','adv','chat','input'))
```
CLI: `python -m src.interp.experiments.grid_hijacking --model-name google/gemma-2-2b-it` (typer; the only flag is
`--model-name`, everything else is code-level). `REPRODUCIBLE_SEED = 42`.

Suffix sampling is **stratified over universality**, which is the load-bearing design choice for the correlation plot:
```python
intervals = [0, 0.005, 0.01] + np.arange(0.05, data_df.univ_score.max(), 0.05).tolist()
for i in range(len(intervals)-1):
    pool = data_df[data_df.univ_score.between(intervals[i], intervals[i+1])].suffix_id.unique().tolist()
    suffix_ids.extend(random.sample(pool, min(n_suffixes // len(intervals), len(pool))))
```
Then a full `tproduct(message_ids, suffix_ids)` (tqdm-wrapped itertools.product): **one forward pass per (message,
suffix) pair**, whose `hs_dict` is reused across `itertools.product(inspected_dom_scores, ['sum','sum-top_q'],
[True, False])` — 7 × 2 × 2 = 28 `get_dominance_scores` calls per forward pass.

Long-format output dataframe, one row per (pair × metric × flavor × src × layer):

```
message_id, suffix_id, suffix_category, suffix_univ, response_score, response_category,
dom_score_name, dom_score_flavor_name, src, layer, dom_score
```
(`layer = -1` means "aggregated over all layers".)
Saved to `results/grid_hijacking[{dst_slc_name}]_{model_name.replace('/','_')}-n=[{n_messages}, {n_suffixes}].csv`
(the path is built once, then rebuilt inline for `to_csv` — harmless duplication).

### 3.2 The aggregation → hijacking strength

```python
def make_box_plot(csv_path, layer=20, slc_src_name='adv', dom_score_name='Y@attn',
                  dom_score_flavor_name='sum', sample_filter=None, save_fig=False)
```
Filters to one (layer, src, metric, flavor) cell, optionally to `response_category == 'fail[cannot]'`
(this is the paper's Fig. 8c control: correlation survives when *all* samples refuse), then:

```python
agg_df = df.groupby('suffix_id').agg({'suffix_univ': 'first', 'dom_score': 'mean'}).reset_index()
bins   = [0, 0.01, 0.05] + np.arange(0.10, max_univ + 0.10, 0.10).tolist()
labels = [f"[{bins[i]:.2f}, {bins[i+1]:.2f}]" for i in range(len(bins)-1)]
agg_df["univ_bin"] = pd.cut(agg_df["suffix_univ"], bins=bins, labels=labels, include_lowest=True)
spearman_corr, _ = spearmanr(agg_df['suffix_univ'], agg_df['dom_score'])
trend_df = agg_df.groupby("univ_bin", observed=True)["dom_score"].median().reset_index()
```

**Hijacking strength ≡ `dom_score` of `src='adv'`, `dst='chat[-1]'`, metric `Y@attn`, flavor `sum`, at a fixed
layer, averaged over the 30 instructions** (`groupby('suffix_id').dom_score.mean()`). One scalar per suffix.
Universality = `univ_score` = mean StrongReject-finetuned grade of that suffix over all messages
(`src/evaluate/utils.py::load_data`, `df.groupby('suffix_id').strongreject_finetuned.mean()`), also exposed as
`suffix_rank` (0 = most universal). Reported Spearman ρ: 0.425 / 0.620 / 0.650 / 0.719 for Qwen2.5-0.5B / 1.5B /
32B / Llama3.1-8B (Fig. 9); the metric is **rank correlation only**, computed on unbinned pairs — the bins are
purely for the box plot.

Note the statistic is a **mean over instructions but a median over bins** for the trendline. Deliberate: means for
the per-suffix estimator, medians for the visual trend so outlier suffixes don't drag the line.

---

## 4. Attention-edge manipulation — **NOT IN THIS REPO**

Exhaustively: there is **no** code anywhere in `src/` that writes to attention. No `add_hook`, no `run_with_hooks`,
no `fwd_hooks`, no `hook_attn_scores`, no masking, no patching. `run_with_cache` is the only TL entry point used
(twice: `dominance_tools.get_model_hidden_states`, and `demo.ipynb` cell 9). `src/attack/README.md` and
`src/defense/README.md` are one-liners saying "Coming soon!". `src/evaluate/build_dataset.py` is a **0-byte file**.
So §4.1 knockout, §4.2 patching, §7.1 GCG-Hij, §7.2 Hij. Suppr., §7.3 Hij. Detect. are all unreleased.

### 4.1 What the paper specifies (so we can build it)

**(a) Attention knockout (§4.1, Geva et al. 2023).** For each edge `adv → {chat, affirm, bad, ...}`, set the
attention **logits** of that (query_pos ∈ dst_span, key_pos ∈ adv_span) block to `-inf`, **in all layers and all
heads**, then softmax renormalizes the surviving edges. Metric: **Jailbreak Flip Rate (JFR)** = fraction of
originally-successful attacks that become failures. Result: JFR ≈ 1 for `adv→chat`; other edges only occasionally
flip. Control: repeat under prefilling (generation forced to start after an affirmative prefix) → `adv→chat` still
top, most suffixes > 0.6 JFR; plus dummy-prefix ablations (whitespace, punctuation, extra chat tokens) all keeping
JFR ≈ 1.

**(b) Activation patching (§4.2).** Patch the *attention output* at `chat` (all layers) from a successful sample
into an instruction-matched failed sample; extend to `chat+i` for i ∈ {0,1,3,5,10,15,20,30}. Majority of the effect
at i ≈ 0–5 → the mechanism is shallow.

**(c) Hijacking Suppression (§7.2, Eq. 6).** Candidate set = all transformed vectors `input → chat` (user prompt
tokens, excluding special tokens). Score each `(l, h, j, i)` by its **attention weight `A_{j,i}^(l,h)`**, take the
**top 1%**, and scale: `Y'_{i→j}^(l,h) := β · Y_{i→j}^(l,h)` with **β = 0.1**. Reported: attack success down
1.5×–10×, MMLU/AlpacaEval down ≤ 2%, AlpacaEval RougeL 0.55–0.70 vs unsuppressed.

**(d) GCG-Hij loss (§7.1, Eqs. 4–5).**
`L_HijEnh := avg{ A_{j,i}^(l,h) : l ∈ [l1,l2], all h, i ∈ adv, j ∈ chat }`, `L_GCG-Hij := L_GCG − α · L_HijEnh`,
with α = 85 / 100 / 150 (Gemma2 / Qwen2.5-1.5B / Llama3.1), `l1 = ⌊0.1L⌋`, `l2 = ⌈0.9L⌉`.

### 4.2 Exactly what hook we need, and where it attaches

Crucial simplification, straight from Eq. 1: `Y_{i→j}^(l,h) = A_{j,i}^(l,h) · X_i^(l-1) W_VO^(l,h)` is **linear in
the attention weight**. Therefore *every* intervention above can be implemented as a write to the attention
probability tensor — no fine-grained fork hook is needed for the intervention, only for the *measurement*.

- **Attach point (post-softmax, for Eq. 6 scaling):** `blocks.{l}.attn.hook_pattern`,
  tensor `[batch, head, query_pos, key_pos]`. Multiply the selected entries by β. **Do not renormalize** — that is
  precisely Eq. 6, and un-normalized rows are exactly the intended "delete this contribution from the sum".
- **Attach point (pre-softmax, for Geva knockout):** `blocks.{l}.attn.hook_attn_scores`,
  same `[batch, head, query_pos, key_pos]` shape. Set the block to `-1e5` (not `-torch.inf`; -inf gives NaN if an
  entire row is masked, and fp16/bf16 overflow). Softmax then renormalizes over the surviving keys, which is the
  paper's `adv→chat` knockout semantics. **These two are different interventions**: `hook_attn_scores = -inf`
  redistributes mass to other sources; `hook_pattern *= 0` destroys mass. §4.1 uses the first, §7.2 the second.

Both are stock upstream TL hooks. `hook_pattern` materialization requires eager attention
(`attn_implementation="eager"`, which `Gemma2Model._load_model` already sets) — SDPA/flash kernels never form the
matrix. TL sets this itself for `HookedTransformer`.

Sketch (upstream TL API, no fork needed):

```python
from transformer_lens.hook_points import HookPoint
def knockout_edge(dst: slice, src: slice, heads=None, mode='mask', beta=0.0):
    def hook(t, hook: HookPoint):          # t: [b, head, q, k]
        h = slice(None) if heads is None else heads
        if mode == 'mask':  t[:, h, dst, src] = -1e5      # attach to hook_attn_scores
        else:               t[:, h, dst, src] *= beta      # attach to hook_pattern
        return t
    return hook

name = 'attn.hook_attn_scores' if mode == 'mask' else 'attn.hook_pattern'
fwd_hooks = [(f'blocks.{l}.{name}', knockout_edge(...)) for l in layers]
logits = model.run_with_hooks(toks, fwd_hooks=fwd_hooks)
# or, to keep hooks alive across model.generate():
with model.hooks(fwd_hooks=fwd_hooks):
    out = model.generate(toks, max_new_tokens=64, do_sample=False, prepend_bos=False, use_past_kv_cache=False)
```

**Generation-time landmines (all real, none handled by this repo):**
1. **KV cache breaks absolute dst indices.** With `use_past_kv_cache=True` the query dim is 1 after the prefill
   step, so `t[:, :, dst, src]` silently hits the wrong position. `src/interp/utils.py::generate` defaults to
   `use_past_kv_cache=False` — keep it that way for any hooked generation, or index dst relative to
   `t.shape[-2]`/absolute-position offset. (This is precisely the "absolute position-index reused across examples"
   bug class already logged twice in our repo memory.)
2. `load_model()` sets `tl_model.cfg.ungroup_grouped_query_attention = True`, so head indices are *ungrouped*
   (n_heads, not n_kv_heads) — a head index in a hook means a query head. And there is an explicit HACK:
   `tl_model.cfg.n_key_value_heads = tl_model.cfg.n_heads` "due to bug in transformer_lens, when ungrouping attn
   heads" with kv-cache.
3. `src` positions of a suffix are stable across generation steps (they're in the prompt); `dst` positions past
   `chat[-1]` grow. For "knock out adv→everything downstream", use `dst = slice(chat_start, None)`.

If we *also* want the fork's `Y` at intervention time, the fork's `hook_Y_out` is on the **block**
(`blocks.{l}.hook_Y_out`), not on `attn` — but writing to `hook_pattern` is strictly cheaper (O(H·T²) vs
O(H·T²·d)) and mathematically equivalent for scaling-type edits.

---

## 5. Plotting and aggregation conventions

- **Plotly, not seaborn/matplotlib** throughout (`plotly.express as px`, `plotly.graph_objects as go`).
  `pio.templates.default = "plotly_white"`, `pio.renderers.default = "svg"` in `demo.ipynb` cell 2.
  Export to PDF via `fig.write_image(...)` (needs `kaleido==1.0.0`, pinned).
- **Fig. 5 (per-layer dominance) = stacked area chart**, `demo.ipynb::show_dominance_area_plot(dom_scores, name)`:
  long df with columns `src_name, layer, val`; `px.area(df, x='layer', y='val', color='src_name', ...)`,
  `width=500, height=350`. The stacking is meaningful *because the scores sum to 1*. Fixed span palette worth
  copying wholesale:
  ```python
  colors = {'bos':'#A9A9A9', 'chat_pre':'#D3D3D3', 'instr':'#4B77BE',
            'adv':'#E8362D', 'chat[:-1]':'#FFA500', 'chat[-1]':'#FFB84D'}
  ```
  (grey = template/special, blue = instruction, red = adversarial, orange = chat.)
- **Fig. 8 (strength vs universality) = binned box plot + median trendline**:
  `px.box(agg_df, x="univ_bin", y="dom_score", points="outliers", width=500, height=350,
  color_discrete_sequence=["cornflowerblue"])`, then `fig.add_trace(go.Scatter(..., mode="lines+markers",
  line=dict(color="crimson", width=3), marker=dict(size=6), name="Median Trend"))`,
  `fig.update_layout(xaxis_tickangle=45, showlegend=False)`. Axis relabeling is done through the `labels={}` dict
  (`univ_bin → "Universality Score"`, `dom_score → "Hijacking Strength"`), never `update_xaxes`.
- **Fig. 2 (universality distribution) = horizontal bar**, `px.bar(univ_scores, x='univ_score', orientation='h')`
  with `yaxis=dict(autorange="reversed")` so rank 0 sits on top.
- **Dataframe discipline:** everything is long-format, built as a `list[dict]` accumulated in a loop and turned
  into a DataFrame once (`df = pd.DataFrame(df)`) — never `df.append`. Filtering is a single boolean-mask
  expression with an `assert not df.empty, ...` immediately after (`make_box_plot`). Column-name convention:
  `{thing}_id`, `{thing}_category`, `{thing}_str`, `dom_score_name` / `dom_score_flavor_name` for
  metric-identifying columns.
- **Response taxonomy** (`src/evaluate/utils.py::enrich_with_categorization`, thresholds `success_thr=0.65`,
  `fail_thr=0.35`, borderline in between): categories `fail[other] / fail[cannot] / fail[sure_other] /
  fail[sure_eos] / fail[sure_cannot] / success[other] / success[cannot_~sure] / success[cannot_sure] /
  success[sure]`, derived from the *first token* of the response against per-model `refusal_toks` / `affirm_toks`
  (Gemma: `[235285,1718,107,1]` = I/It/<end_of_turn>/<eos>, affirm `[21404,1620,4858,1917,14692,94638]` =
  Sure/##/Here/```/Okay/Certainly; Llama3 refusal `[40]`='I', affirm `[40914]`; Qwen refusal `[40,2121]`, affirm
  `[39814]`). `fail[cannot]` is the filter used for the "control for success" panel.
- Nice trick in `get_logits_stats` (the author flags it himself as `[COOL CODE ALERT]`):
  `logits_ranks = torch.argsort(torch.argsort(probs, descending=True))` — double argsort maps token_id → rank.

---

## 6. Caching / batching patterns worth copying

1. **Compute `hs_dict` once, slice many times.** `grid_hijacking` calls `get_model_hidden_states(...)` once per
   (message, suffix) and threads the result into 28 `get_dominance_scores(..., hs_dict=hs_dict)` calls. All the
   metric/flavor/layer/span variation is pure tensor slicing on CPU. This is the single most important structural
   idea to copy: **one forward pass → a full metric grid.**
2. **Cache to CPU immediately.** `cache = cache.to('cpu')` right after `run_with_cache`, with
   `gc.collect(); torch.cuda.empty_cache()` on both sides of the forward. Every dominance return value ends in
   `.cpu()`.
3. **Fine-grained hooks are toggled, not left on** — the O(T²·d) `Y` tensor is only materialized inside the window:
   ```python
   _orig = model.cfg.use_attn_fine_grained
   model.set_use_attn_fine_grained(True)
   _, cache = model.run_with_cache(toks)
   model.set_use_attn_fine_grained(_orig)
   ```
   Memory math (fp32, the dtype `load_model` forces): `Y` is `L · H · T² · d · 4` bytes. Gemma2-2b (L=26, H=8,
   d=2304) at T=30 → ~1.7 GB; at T=120 → ~28 GB. **`Y` caching is quadratic in sequence length and will not
   survive long Boombness prompts** — use `hook_pattern` (`L·H·T²·4`, 4600× smaller) plus an explicit
   `A_{j,i} · (X_i W_VO)` recomputation for only the spans we care about.
4. **Batch size is 1 everywhere in the interp path.** `toks[0]`, `.squeeze(0)`, `assert len(messages)==1` in
   `ModelBase.get_activations`. Batching exists only in `ModelBase.generate_batch(..., batch_size=8,
   max_new_tokens=256, do_sample=False)` with `tokenizer.padding_side='left'`. If we batch dominance we must
   re-derive spans per row (left padding shifts every index).
5. **`torch.set_grad_enabled(False)` globally** in `load_model()`, and the HF model is deleted right after the TL
   model is constructed (`model_base.del_model(); del model_base`) — TL wraps the same weights.
6. **fp32 for the analysis model** (`HookedTransformer.from_pretrained_no_processing(..., dtype=torch.float32)`)
   even though `ModelBase._load_model` loads bf16 — the projection ratios are numerically delicate.
   `from_pretrained_no_processing` (not `from_pretrained`) means **no weight folding / no LayerNorm folding**, which
   is required for the `Y` decomposition to reproduce the true residual.
7. **Dataset caching via HF hub**, not local files: `pd.read_parquet(hf_hub_download(repo_id='MatanBT/gcg-evaluated-data',
   repo_type="dataset", filename=f"{model_name.split('/')[-1]}_eval_data.parquet"))` — 952,926 rows, 1,286 suffixes ×
   741 messages for gemma-2-2b-it. Columns we care about: `message_id, message_str, suffix_id, suffix_str,
   suffix_cat/suffix_category, suffix_optimizer, suffix_objective, is_mult_attack, strongreject_finetuned,
   prefilled__strongreject_finetuned` (+ derived `suffix_rank`, `univ_score`, `is_hard_message`).
   `data/other_suffix_dists.json` holds the hand-crafted suffix distributions (`style_suffixes`,
   `start-with_suffixes`, …) used for the Fig. 6 baseline comparison.
8. `tqdm.contrib.itertools.product as tproduct` — drop-in progress bar over a nested loop.
