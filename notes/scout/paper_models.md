# Scout: `interp-jailbreak` (Ben-Tov / Geva / Sharif, "Universal Jailbreak Suffixes Are Strong Attention Hijackers")

Repo root scanned: `/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood/external_repos/interp-jailbreak`
Second, byte-identical copy of `src/` lives at `/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood/interp-jailbreak` (`diff -rq` of the two `src/` trees is empty; `requirements.txt` identical). The top-level copy additionally has `src/attack/README.md` and `src/defense/README.md`, both containing only "Coming soon!" — **the GCG-boosting and hijacking-suppression code is NOT released**.

Total released Python: 1459 lines across 8 non-empty files. `src/evaluate/build_dataset.py`, `src/evaluate/__init__.py`, `src/interp/__init__.py`, `src/models/__init__.py` are all **0 bytes**.

---

## 0. TransformerLens availability in THIS environment — **NOT INSTALLED**

```
$ python -c "import transformer_lens, sys; print(transformer_lens.__version__, transformer_lens.__file__)"
ModuleNotFoundError: No module named 'transformer_lens'
$ pip show transformer_lens
WARNING: Package(s) not found: transformer_lens
```
`which python` -> `/home/sharifm/students/omeryosef/miniconda3/bin/python` (conda `base`). **`base` does not even have `torch`** (`import torch` -> ModuleNotFoundError).

Searched every other interpreter on the box:
- `conda env list` -> only `base` and `poc_stage2`.
- `/home/sharifm/students/omeryosef/miniconda3/envs/poc_stage2/lib/python3.12/site-packages/`: has `torch`, `transformers-5.12.1`, `jaxtyping-0.2.29`. **No `transformer_lens`.**
- `/home/.../teza_first_poc_with_mahmood/TROPT/.venv/lib/python*/site-packages/`: has `torch`, `transformers-5.8.1`, `sentence_transformers`. **No `transformer_lens`.**

**Verdict: TransformerLens is not installed anywhere in this environment, therefore it is certainly not Matan's fork.** To run any of `src/interp/*` we must first install:

```
pip install "transformer-lens @ git+https://github.com/matanbt/TransformerLens.git@d68e8b596e097750ec386d6f9f4dd6edaaa4aae7"
```

(pinned commit `d68e8b596e097750ec386d6f9f4dd6edaaa4aae7`, from `requirements.txt` line 14). Do this in an **isolated env** — the README explicitly warns the fork will shadow/override any stock TransformerLens.

### Why the fork is needed
Stock TransformerLens caches attention only as `hook_pattern` (`layer, head, dst, src`) and `hook_z` / `hook_attn_out` (`layer, seq, d_model`). It **cannot give you the per-(head, dst, src) contribution vector** — i.e. the value vector of source token `s`, pushed through `W_V W_O`, weighted by `A[h,t,s]`, still un-summed over `s`. The dominance score (Eq. 3, §5) is exactly a projection of that un-summed tensor. The fork adds three hook points and a switch:

| fork-only hook | shape | meaning |
|---|---|---|
| `blocks.{layer}.attn.hook_X_in` | `batch, head, src, d_model` | per-head input to attention (pre-`W_V`) |
| `blocks.{layer}.attn.hook_X_WVO` | `batch, head, src, d_model` | source vector after `W_V W_O`, **before** attention weighting |
| `blocks.{layer}.hook_Y_out` | `batch, head, dst, src, d_model` | `A[h,t,s] * (x_s W_V W_O)` — the fully decomposed attention output |
| `model.set_use_attn_fine_grained(bool)` | — | toggles materialisation of the above (memory-explosive, so off by default) |
| `model.cfg.use_attn_fine_grained` | bool | the backing config flag |

Identity the fork guarantees (asserted in `dominance_tools.py:99-103` under `apply_sanity_checks=True`):
```
hs['Y'][L].sum(dim=(0,2))                                  == hs['decompose_resid__attns'][L]     # sum over head & src == attn_out
embed + mlps.sum(0) + Y.sum(dim=(0,1,3))                   == resid[-1]                            # full residual reconstruction
```

---

## 1. The `ModelBase` abstraction

`src/models/model_base.py:10` — `class ModelBase(ABC)`.

### Constructor
```python
def __init__(self, model_name_or_path: str, model_obj: PreTrainedModel = None):
```
`model_obj` is a test-injection escape hatch (skips `_load_model`).

### Exact abstract methods a subclass MUST provide (declared `@abstractmethod`)
| method | signature | returns |
|---|---|---|
| `_load_model` | `(self, model_name_or_path: str) -> PreTrainedModel` | HF causal-LM, `.eval()`, `requires_grad_(False)` |
| `_load_tokenizer` | `(self, model_name_or_path: str) -> PreTrainedTokenizer` | HF tokenizer, `padding_side` set |
| `_get_tokenize_instructions_fn` | `(self)` | a `functools.partial` callable `(instructions, outputs=None, system=None, include_trailing_whitespace=True, wo_tempalte_chat_suffix=False) -> BatchEncoding` |
| `_get_refusal_toks` | `(self)` | `List[int]` of token ids |

### Methods called in `__init__` but **NOT declared abstract** (latent-`AttributeError` trap if you subclass)
| method | returns | note |
|---|---|---|
| `_get_affirm_toks(self)` | `List[int]` | called at `model_base.py:21`, no `@abstractmethod` |
| `_get_before_after_instr_tok_count(self)` | `Tuple[int, int]` | called at `model_base.py:23`, no `@abstractmethod` |
| `_get_eoi_toks(self)` | — | declared in `Llama3Model` only, body is `pass`, never called. Dead. |

### Attributes populated by `__init__`
```
self.model_name_or_path : str            # .lower()'ed
self.model              : PreTrainedModel
self.tokenizer          : PreTrainedTokenizer
self.device             : torch.device   # == self.model.device
self.tokenize_instructions_fn : Callable
self.refusal_toks       : List[int]
self.affirm_toks        : List[int]
self.before_instr_tok_count : int        # tokens before the user instruction (incl. BOS)
self.after_instr_tok_count  : int        # tokens after the instruction (chat suffix / gen prompt)
self.short_name         : str            # path.split('/')[-1]
self.n_layers           : int            # model.config.num_hidden_layers
self.hidden_dim         : int            # model.config.hidden_size
self.tl_model           : None           # placeholder, NEVER assigned anywhere in the repo
```

### Concrete methods
| symbol | signature | notes |
|---|---|---|
| `del_model` | `(self)` | `del self.model` — used by `load_model()` to free the HF copy after TL ingests the weights |
| `_post_init_validations` | `(self)` | warns if dtype not fp16/bf16; **asserts** `tokenizer.chat_template is not None` |
| `generate_batch` | `(self, messages: List[str], prefix_fillers: List[str]=None, return_full_chat=False, wo_tempalte_chat_suffix=False, batch_size=8, max_new_tokens=256) -> List[str]` | greedy (`do_sample=False`) |
| `get_activations` | `(self, messages, force_output_prefixes=None)` | **asserts `len(messages)==1`**; returns `(hs [n_layers+1, seq, d], attns [n_layers, heads, seq, seq], logits [vocab])`, all `.detach().cpu()` |
| `calc_gcg_ce_loss` | `(self, messages: List[str], target: str) -> List[float]` | per-message mean CE of `target` as forced response prefix |
| `calc_sim_with_dir` | `(self, messages, direction: Float[Tensor,"d_model"]=None, layer:int=15, tok_pos:int=-1)` | cosine sim of `hidden_states[layer][:, tok_pos, :]` with `direction` |
| `to_toks` | `(self, instruction, add_template=True, output=None)` | thin wrapper |

### Refusal-direction plumbing — **essentially absent**
There is **no** refusal-direction computation, no direction-ablation, no projection-out in the released code. The only reference is a dangling one:
```python
# model_base.py:143
direction = direction or self.refusal_dir     # BUG x2
```
`self.refusal_dir` is **never assigned anywhere in the repo** (`grep -rn refusal_dir src/` returns this one line only) -> `AttributeError` whenever `direction is None`. And `tensor or x` raises `RuntimeError: Boolean value of Tensor with more than one element is ambiguous` when `direction` *is* a tensor. **`calc_sim_with_dir` cannot execute as written on either branch.** The `Y@dir` dominance metric (`dominance_tools.py:150`) takes `given_dir` as a caller-supplied argument, so it sidesteps this — the caller must produce the direction (e.g. via `andyrdt/refusal_direction`, credited in the README).

`refusal_toks` / `affirm_toks` are the only "refusal signal" primitives shipped:
```python
LLAMA3_REFUSAL_TOKS = [40]                                  # 'I'
LLAMA3_AFFIRM_TOKS  = [40914]                               # 'Sure'
QWEN_REFUSAL_TOKS   = [40, 2121]                            # ['I', 'As']
QWEN_AFFIRM_TOKS    = [39814]                               # ['Sure']
GEMMA_REFUSAL_TOKS  = [235285, 1718, 107, 1]                # ['I','It','<end_of_turn>','<eos>']
GEMMA_AFFIRM_TOKS   = [21404, 1620, 4858, 1917, 14692, 94638] # ['Sure','##','Here','```','Okay','Certainly']
```

### Factory
`src/models/model_factory.py:3` — `construct_model_base(model_path: str) -> ModelBase`. Substring dispatch on `model_path.lower()`, in order: `'qwen'` -> `Qwen2Model`; `'llama-3'` -> `Llama3Model`; `'gemma-2-'` -> `Gemma2Model`; else `ValueError`. Note `'gemma-2-'` has a trailing hyphen so `gemma-2b` (v1) would not match, and Gemma-3/Gemma-4 fall through to the error.

---

## 2. Model + tokenizer loading (dtype, device, HF vs TransformerLens)

### Per-family HF load
| | dtype | device_map | attn_impl | tokenizer flags |
|---|---|---|---|---|
| `Llama3Model._load_model(self, model_path, dtype=torch.bfloat16)` | `bfloat16` | `"cuda"` | default (SDPA) | `padding_side="left"`, `pad_token = eos_token` |
| `Qwen2Model._load_model(self, model_path, dtype=torch.float16)` | **`torch_dtype="auto"`** (the `dtype` arg is commented out at `qwen2_model.py:84` — the default is dead) | `"auto"` | default | `trust_remote_code=True`, **`use_fast=False`**, `padding_side='left'`, **no `pad_token` set** |
| `Gemma2Model._load_model(self, model_path, dtype=torch.bfloat16)` | `bfloat16` | `"cuda"` | **`attn_implementation="eager"`** (required so `output_attentions=True` returns real patterns) | `padding_side='left'`, asserts `chat_template is not None` |

All three call `.eval()` then `model.requires_grad_(False)`.

### The TransformerLens path
`src/interp/utils.py:8` — `load_model(model_name)`:
```python
model_base = construct_model_base(model_name)
tl_model = HookedTransformer.from_pretrained_no_processing(
    model_name, hf_model=model_base.model, device=model_base.device, dtype=torch.float32)
tl_model.cfg.use_attn_in = True
tl_model.cfg.use_attn_result = True                     # for `attn.result`
tl_model.cfg.ungroup_grouped_query_attention = True     # expand GQA kv-heads to n_heads
tl_model.cfg.use_hook_mlp_in = True
tl_model.cfg.n_key_value_heads = tl_model.cfg.n_heads   # HACK: TL kv-cache bug when ungrouping
tl_model.cfg.before_instr_tok_count = model_base.before_instr_tok_count
tl_model.cfg.after_instr_tok_count  = model_base.after_instr_tok_count
model_base.del_model(); del model_base
torch.set_grad_enabled(False)
```
Three things to internalise:
1. **`from_pretrained_no_processing`**, not `from_pretrained` — no LayerNorm folding, no weight centering, no unembed centering. Necessary because the dominance decomposition must reproduce the *actual* HF residual stream bit-for-bit (see the sanity checks in §0).
2. **dtype is forced to `float32`** even though the HF model was loaded bf16. The residual reconstruction identity does not hold numerically in bf16. Cost: 2x weights + a fp32 activation cache. This is why the paper's demos use gemma-2-**2b**-it / qwen2.5-**1.5b**.
3. The HF model is deleted right after; only the TL copy survives. `model_base.tokenizer` is gone too — downstream code uses `model.tokenizer` (TL re-exposes it).

`grid_hijacking.py` CLI (`typer`) is the only entry point with real flags:
```
python -m src.interp.experiments.grid_hijacking --model-name google/gemma-2-2b-it
```
Everything else in `grid_hijacking(...)` (`n_messages=30`, `n_suffixes=400`, `suffix_interval_diff=0.05`, `inspected_dom_scores`, `dst_slc_name`, `src_slc_names`) is a Python kwarg only — the `@app.command()` wrapper `grid_hijacking_cli` exposes **only** `--model-name`.

---

## 3. Activations / caching

### The HF path (no TL needed)
`ModelBase.get_activations(messages, force_output_prefixes=None)` — single message only, `output_hidden_states=True, output_attentions=True`, stacks and moves to CPU. Returns `hs` of shape `[n_layers+1, seq, d]` (index 0 = embeddings).

### The TL path — `src/interp/dominance_tools.py:10`
```python
def get_model_hidden_states(model: HookedTransformer, toks: Union[List[int], str],
    return_labels: bool=False, force_output_prefix: str=None, apply_sanity_checks: bool=False,
    add_dominance_calc: bool=False, given_dir: Float[Tensor,"n_layer d_model"]=None,
    selected_dom_scores: List[str]=['Y@attn']):
```
Core:
```python
gc.collect(); torch.cuda.empty_cache()
_orig = model.cfg.use_attn_fine_grained
model.set_use_attn_fine_grained(True)
_, cache = model.run_with_cache(toks)         # toks is a 1-D tensor, NO batch dim
model.set_use_attn_fine_grained(_orig)
cache = cache.to('cpu')
gc.collect(); torch.cuda.empty_cache()
```
Then it stacks every hook across layers into `hs_dict[name]` of shape `layer, [head,] ... , d`:

```python
supported_hooks = {
    'resid':        'blocks.{layer}.hook_resid_post',   # layer, seq, d_model
    'resid_pre':    'blocks.{layer}.hook_resid_pre',
    'decompose_resid': 'decompose_resid',               # special: cache.decompose_resid(return_labels=True)
    'attn':         'blocks.{layer}.hook_attn_out',     # layer, seq, d_model
    'attn_pattern': 'blocks.{layer}.attn.hook_pattern', # layer, head, dst, src
    'mlp':          'blocks.{layer}.hook_mlp_out',
    'X_in':         'blocks.{layer}.attn.hook_X_in',    # FORK: layer, head, src, d_model
    'X_WVO':        'blocks.{layer}.attn.hook_X_WVO',   # FORK: layer, head, src, d_model
    'Y':            'blocks.{layer}.hook_Y_out',        # FORK: layer, head, dst, src, d_model
}
```
Derived keys it also fills: `decompose_resid__embed` (`[0]`), `decompose_resid__attns` (odd indices `1,3,5,...`), `decompose_resid__mlps` (even `2,4,6,...`), `decompose_resid_coar` (embed + per-layer attn + mlp), and legacy aliases `resids_pre_attn` (= `X_in`), `A` (= `attn_pattern`), plus `X_WVO` gets an extra dst axis via `.unsqueeze(2)`.

### Memory handling — the real constraint
- `hook_Y_out` is `[batch, n_head, dst, src, d_model]`. For gemma-2-2b (`n_heads=8`, `d_model=2304`) at **seq=100**, fp32: `8 * 100 * 100 * 2304 * 4 B ≈ 737 MB` **per layer**; `torch.stack` over 26 layers ≈ **19 GB** on CPU. It grows as **O(n_layers · n_heads · seq² · d_model)**.
- Mitigations actually used: single sequence (no batch), `cache.to('cpu')` immediately, `gc.collect()` + `torch.cuda.empty_cache()` before and after, `set_use_attn_fine_grained(False)` restored right after, and `torch.set_grad_enabled(False)` globally in `load_model`.
- Even so, `get_model_hidden_states` **unconditionally materialises all nine hooks including `Y`** — there is no way to ask for only `resid`. For long prompts this OOMs.

---

## 4. Interventions / hooks

**There are none in the released code.** `grep -rn "fwd_hooks\|run_with_hooks\|add_hook\|HookPoint" src/ demo.ipynb` returns **zero** matches. The only `run_with_cache` call is `dominance_tools.py:57`. Ablation, direction projection, attention editing and patching (paper §2 causal experiments, §7 attack boosting, §8 mitigation) live in `src/attack/` and `src/defense/`, both of which contain only a "Coming soon!" README.

What the code *does* instead is a **read-only, post-hoc decomposition**, `src/interp/dominance_tools.py:118`:
```python
def _calculate_hooks_for_dom_scores(hs_dict, selected_dom_scores=['Y@attn'],
    given_dir: Float[Tensor,"n_layer d_model"]=None, dst_slc: slice=slice(None,None)):
```
It computes, for each `(layer, head, dst, src)`, the scalar coefficient of `Y` along a reference vector:
```python
dot_prod_vals = torch.einsum('lhtsd,lktkd->lhts', main_vecs, ref_vecs)   # layer, head, dst, src
dot_prod_vals = dot_prod_vals / torch.norm(ref_vecs, dim=-1).pow(2)      # normalise per layer & dst
```
Supported `(main, ref)` pairs — the `dominance_metric` vocabulary:
```
'Y@resid'        : (hs['Y'], hs['resid'])
'Y@dcmp_resid'   : (hs['Y'], hs['decompose_resid_coar'])
'Y@attn'         : (hs['Y'], hs['attn'])           # <- the paper's default (Eq. 3)
'(X@W_VO)@attn'  : (hs['X_WVO'], hs['attn'])
'Y@dir'          : einsum with a unit-normalised `given_dir`  ('...d,d->...' if 1-D else 'lhtsd,ld->lhts')
'norm(X)'        : hs['X_in'].unsqueeze(2).norm(dim=-1)
'norm(Y)'        : hs['Y'].norm(dim=-1)
'A'              : raw attention pattern
```
Note `dst_slc` is a parameter of `_calculate_hooks_for_dom_scores` but is **immediately overwritten** by `dst_slc = slice(None, None)` on its first line (`dominance_tools.py:124`) — the argument is dead; slicing happens later in `get_dominance_scores`.

Public aggregator, `src/interp/dominance_tools.py:165`:
```python
def get_dominance_scores(model, msg: str, suffix: str, hs_dict=None,
    dst_slc_name: str='chat[-1]',
    src_slc_names: Tuple[str]=('bos','chat_pre','instr','adv','chat[:-1]','chat[-1]'),
    dominance_metric: str='Y@attn',
    dominance_metric_flavor: str='sum',        # 'sum' | 'sum-top_q'
    dominance_metric_flavor_q: float=0.1,
    aggr_all_layers: bool=False) -> Dict[str, List[float]]:
```
Aggregation: slice `[:, :, dst_slc, src_slc]`, flatten from dim `1` (or `0` if `aggr_all_layers`), `topk(k=max(1,int(q*N)))` then `.sum(-1)`. `'sum'` is implemented as `q=1.0`, i.e. it is literally top-100%.

---

## 5. Prompt construction, tokenisation, token spans, BOS gotchas

### Two divergent templating code paths — know which you are on
**Path A (HF / `ModelBase`)** — `tokenize_instructions_<family>_chat(tokenizer, instructions, outputs=None, system=None, include_trailing_whitespace=True, **kwargs)`:
- Llama3 & Qwen2 build the string with `tokenizer.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)`.
- **Gemma2 does NOT** — it uses a hardcoded literal (`gemma2_model.py:14`):
  ```python
  GEMMA_CHAT_TEMPLATE = "<start_of_turn>user\n{instruction}<end_of_turn>\n<start_of_turn>model\n"
  GEMMA_CHAT_TEMPLATE_WO_CHAT = "<start_of_turn>user\n{instruction}"   # ablation: no chat suffix
  ```
- Forced output is **string concatenation after templating**: `formatted_instruction += output`. So the "target prefix" is not a separate turn; its tokenisation is affected by the preceding character.
- **`system` is a trap in all three families**: `if system is not None: append({"role":"system", ...})` `else: append({"role":"user", "content": instruction})`. i.e. **passing a system prompt silently drops the user instruction entirely.** Gemma at least raises `ValueError`. Everything in the repo passes `system=None`.
- `add_special_tokens`: Llama3 passes **`add_special_tokens=False`** (its template already emits `<|begin_of_text|>`). Qwen2 and Gemma2 pass **nothing** (default `True`). This is correct-by-accident: Qwen2's tokenizer adds no BOS; Gemma2's hardcoded template omits `<bos>` so the tokenizer must add it. **Any new family you add must be audited on this axis or you get a double-BOS.**

**Path B (TransformerLens / `src/interp/utils.py:39`)** — `to_toks(message, model, force_output_prefix=None, add_template_if_possible=True)`:
```python
wrapped = model.tokenizer.apply_chat_template([{"role":"user","content":message}],
                                              tokenize=False, add_generation_prompt=True)
start_of_gen_idx = model.tokenizer.encode(wrapped, add_special_tokens=False, return_tensors="pt").shape[-1]
if force_output_prefix is not None: wrapped = wrapped + force_output_prefix
input_ids = model.tokenizer.encode(wrapped, add_special_tokens=False, return_tensors="pt")
if model.tokenizer.bos_token_id not in input_ids:
    print("[WARN] BOS token not found after adding chat template. ...")
```
Always `add_special_tokens=False`, relying on `apply_chat_template` to emit BOS in the string. For Gemma this **is** what `apply_chat_template` does, so Path A and Path B produce the same tokens by different routes — but they are not the same code. `start_of_gen_idx` is computed **before** appending the forced prefix, so it is the index of the first generated token. Generation uses `prepend_bos=False`.

`generate(message, model=None, force_output_prefix=None, max_new_tokens=256, add_template_if_possible=True, return_logits=False, use_past_kv_cache=False)` returns `(full_chat_toks: List[int], full_chat_str, response_str[, logits])`; when `return_logits=True` it returns `model(input_ids, prepend_bos=False)[0, -1]` — the **last** position (with output forcing), not `[0, start_of_gen_idx-1]` (that variant is commented out at `utils.py:122`).

### Prefix/suffix token counts
```python
# llama3_model.py:103 / qwen2_model.py:114 — identical bodies
def _get_before_after_instr_tok_count(self):
    str_before, str_after = self.tokenizer.apply_chat_template(
        [{"role":"user","content":"DUMMY_TXT_FOR_SPLIT"}], tokenize=False, add_generation_prompt=True
        ).split("DUMMY_TXT_FOR_SPLIT")
    if self.tokenizer.bos_token and str_before.startswith(self.tokenizer.bos_token):
        str_before = str_before.replace(self.tokenizer.bos_token, "")
    n_toks_before = len(self.tokenizer(str_before)["input_ids"])                     # add_special_tokens=True -> re-adds BOS
    n_toks_after  = len(self.tokenizer(str_after, add_special_tokens=False)["input_ids"])
    return n_toks_before, n_toks_after
```
The strip-then-let-the-tokenizer-re-add dance is deliberate: it forces the BOS to be counted exactly once. Note the **asymmetry** — `str_before` is tokenised with `add_special_tokens` defaulting to `True`, `str_after` with `False`.

Gemma hardcodes instead (`gemma2_model.py:26`):
```python
GEMMA2_PRE_INSTRUCT_TOK_COUNT = 4   # <bos><start_of_turn>user\n
GEMMA_POST_INSTRUCT_TOK_COUNT = 5   # <end_of_turn>\n<start_of_turn>model\n
```
with a `# TODO can automate this` — so **any Gemma variant with a different template silently produces wrong spans.**

### Span computation — `src/interp/utils.py:185`
```python
def get_idx_slices(model, message, suffix, response_str=""):
    _a = enrich_with_affirm_length(pd.DataFrame([{'response': response_str}]), model.tokenizer)
    affirm_str, affirm_tok_len = _a.affirm_str.item(), _a.affirm_tok_len.item()
    affirm_tok_len = affirm_tok_len or 20
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
        input    = slice(chat_pre_len, input_len - chat_suffix_len))
    slcs['chat[-1]']  = slice(slcs['chat'].stop - 1, slcs['chat'].stop)
    slcs['chat[:-1]'] = slice(slcs['chat'].start, slcs['chat'].stop - 1)
    return slcs
```

**Off-by-one / BOS handling we must copy or consciously reject:**
1. **`bos = slice(0,1)` is assumed unconditionally.** True for Llama-3 (`<|begin_of_text|>`) and Gemma (`<bos>`). **False for Qwen** — Qwen2/2.5 emit no BOS, so `slcs['bos']` actually points at `<|im_start|>`. The slices still *tile* the sequence correctly (`bos ∪ chat_pre = [0, chat_pre_len)`), so aggregate numbers are fine, but the per-slice label `'bos'` is wrong for Qwen. Do not trust the `bos`/`chat_pre` split cross-family.
2. **`adv_suffix_len` is measured on the suffix in isolation** (`tokenizer.encode(suffix, add_special_tokens=False)`) but applied as a span inside the **jointly tokenised** `message + suffix`. If the suffix's first token merges with the message's last character under BPE, the `adv` and `instr` boundaries drift by one. The repo defends against this upstream, not here:
   ```python
   # src/evaluate/utils.py:63  — every message is coerced to end with '. '
   df['message_str'] = df.message_str.apply(lambda x: x if x.endswith('. ') else x + '. ')
   ```
   i.e. **a trailing `". "` on the instruction is a load-bearing invariant, not cosmetics.** Same class of bug as our `feedback_absolute_position_index_bug` note.
3. `instr` is computed by **subtraction from the right**, not by locating the instruction. Any change to the chat suffix or a stray token shifts every boundary simultaneously.
4. `affirm`/`bad` slices index **past `input_len`**, i.e. they only exist if you actually appended the forced response. `to_toks(message+suffix, model)` inside `get_idx_slices` does **not** pass `force_output_prefix`, so `input_len` is the prompt length — correct, but easy to break.
5. `affirm_tok_len = affirm_tok_len or 20` — a `0`-token affirm silently becomes 20.

### Affirm-prefix heuristic — `src/interp/utils.py:138`
```python
def enrich_with_affirm_length(df, tokenizer, set_mock_affirm_prefix=False, pad_to_max_tokens=None):
```
Adds `df['affirm_str']`, `df['affirm_tok_len']`. Heuristic: first line -> first sentence -> if empty take first 5 tokens; then split at the 2nd `:` or `,` after char 10; then trim to 20 tokens. With `set_mock_affirm_prefix=True` it fixes `"Sure, here is exactly what you need to do.\n"`. `pad_to_max_tokens` pads short prefixes with `'\n-'` repeats (author's own comment: "THIS IS HACKY AND UGLY").

---

## 6. What we must write ourselves to score a hidden state at a *specific word occurrence* in a long prompt

Their utilities give us **positional spans for a fixed 5-region layout only** (`bos / chat_pre / instr / adv / chat / affirm / bad`). Nothing in the repo can answer "where is the 3rd occurrence of 'bomb' in this prompt". Concretely, the gaps:

**(a) A char-span -> token-span mapper. Does not exist; must be written.**
`get_idx_slices` is purely arithmetic on lengths. We need offset-based lookup:
```python
def word_occurrence_token_spans(tokenizer, rendered_prompt: str, word: str, occurrence: int = 0):
    enc = tokenizer(rendered_prompt, add_special_tokens=False, return_offsets_mapping=True)
    hits = [m.span() for m in re.finditer(rf'\b{re.escape(word)}\b', rendered_prompt, re.I)]
    cs, ce = hits[occurrence]
    idx = [i for i, (a, b) in enumerate(enc['offset_mapping']) if a < ce and b > cs]
    return slice(idx[0], idx[-1] + 1)          # token span covering the occurrence
```
Blockers to fix first:
- **`Qwen2Model._load_tokenizer` sets `use_fast=False`** -> `return_offsets_mapping` raises `NotImplementedError`. We must override to `use_fast=True` (and re-verify token ids match).
- We must run the regex on the **rendered/templated** string, not the raw instruction — the template inserts characters and Gemma's Path A uses a hardcoded literal rather than `apply_chat_template`. Build the string once, tokenise once, and derive both the prompt tensor and the spans from that *same* string, never from two separate `encode` calls (this is exactly the bug class in §5.2).
- Prepend-BOS bookkeeping: if the encode used `add_special_tokens=False` (their convention) and a `<bos>` is present *inside* the templated string, offsets are already aligned — but if we ever let the tokenizer add BOS, every index shifts by +1.

**(b) A word-level (as opposed to region-level) scorer. Does not exist.**
`calc_sim_with_dir(messages, direction, layer=15, tok_pos=-1)` is the closest thing and it takes a **single scalar `tok_pos`**, defaults to `-1`, and is **currently broken** (`self.refusal_dir` undefined, `tensor or x` ambiguous). We would write:
```python
@torch.no_grad()
def score_span(model, tokenizer, prompt, span: slice, direction, layer, reduce='mean'):
    ids = tokenizer(prompt, add_special_tokens=False, return_tensors='pt').to(model.device)
    hs  = model(**ids, output_hidden_states=True).hidden_states[layer + 1]   # +1: index 0 == embeddings
    v   = hs[0, span, :]                                          # [span_len, d_model]
    v   = v.mean(0) if reduce == 'mean' else v[-1]
    return torch.nn.functional.cosine_similarity(v.float(), direction.float(), dim=-1).item()
```
**Layer-index off-by-one to decide explicitly:** HF `hidden_states[i]` has `i=0` = embedding output, so block `L`'s output is `hidden_states[L+1]`. TL's `blocks.{L}.hook_resid_post` == HF `hidden_states[L+1]`. Their `calc_sim_with_dir(layer=15)` indexes `hidden_states[15]` = **output of block 14**. Pick one convention and assert it once.

**(c) The direction itself.** Not shipped (see §1). Must come from our own pipeline or `andyrdt/refusal_direction`.

**(d) Multi-example batching.** `ModelBase.get_activations` hard-asserts `len(messages)==1` and `get_model_hidden_states` passes an unbatched 1-D tensor to `run_with_cache`. Batched scoring over a "Boombness" corpus is ours to write — and note `padding_side='left'` on all three tokenizers means **every token index shifts per-example under padding**; offset-derived spans must be recomputed post-pad or we must pad right / use per-example forward passes.

**(e) What we can reuse as-is.** For pure hidden-state scoring at a word position, **we need none of the fork and none of TransformerLens** — plain HF `output_hidden_states=True` suffices, which sidesteps the whole `float32` + `O(seq²)` `hook_Y_out` memory problem. The fork only becomes necessary if we want *attributional* Boombness ("which source tokens wrote the bomb-ness into position t"), i.e. `Y@dir` with `given_dir` = our bomb direction. That is a genuinely attractive extension — `get_dominance_scores(..., dominance_metric='Y@dir')` already implements it — but it costs the fork install plus fp32 plus quadratic memory, so it should be a second phase on short prompts only.
