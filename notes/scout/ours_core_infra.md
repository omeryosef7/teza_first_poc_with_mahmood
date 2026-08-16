# OUR core infra — `doublespeak_causality/` (scout notes for the Boombness sprint)

Repo root: `/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood`
Package dir (`DC`): `<repo>/doublespeak_causality`

Layout note: **`doublespeak_causality/shared` is a 0-byte regular FILE, not a package** —
there is no `shared/` module. The real shared layer is the three flat modules
`ds_common.py` (1027 lines), `pair_common.py` (1050 lines), `stats.py`, `plots.py`, plus
`src/probes/` (a real package with `__init__.py`).

Import idiom used everywhere (scripts live in `DC/` or `DC/scripts/`):

```python
_HERE = os.path.dirname(os.path.abspath(__file__)); _DC = os.path.dirname(_HERE)
_REPO = os.path.dirname(_DC)
sys.path.insert(0, _DC); sys.path.insert(0, os.path.join(_REPO, "poc_stage3"))  # strongreject_scoring
import ds_common as dc
import pair_common as pc
```

---

## 1. Model / tokenizer loading

`doublespeak_causality/ds_common.py::load_model` — the ONLY loader anyone calls.

```python
PRIMARY_MODEL = "meta-llama/Llama-3.1-8B-Instruct"          # ds_common.py:70

def load_model(model_id: str = PRIMARY_MODEL,
               dtype: torch.dtype = torch.bfloat16,
               device_map: str = "auto",
               revision: Optional[str] = None,
               attn_implementation: str = "sdpa",
               quantize: Optional[str] = None) -> LoadedModel   # ds_common.py:368
```

* House standard: **bfloat16 + `attn_implementation="sdpa"`**. `quantize` ∈
  `None|"8bit"|"4bit"` (bnb NF4, `bnb_4bit_compute_dtype=dtype`).
* **`attn_implementation="eager"` is REQUIRED for any attention-mask knockout** —
  under SDPA a custom 4-D additive mask is silently ignored and the knockout becomes a
  no-op (`pair_common.AttentionKnockout` raises if the mask isn't 4-D).
* Native, possibly list-valued EOS is preserved (`lm.eos_token_ids`); pad only set if
  missing. Never overwrite EOS (documented prior severe bug).
* `LoadedModel` dataclass (`ds_common.py:346`): `.model .tokenizer .model_id .revision
  .dtype .device .num_layers .hidden_size .eos_token_ids`, plus `.meta()` →
  dict + `env_metadata()` (explicitly NOT `asdict`, which would deep-copy the nn.Module and OOM).
* `ds_common._get_layers(model)` → the decoder `ModuleList` (`model.model.layers` or
  `model.transformer.h`). Every hook class goes through this.

**Models actually used** (occurrence counts across `*.py` + `slurm/*.sh`):
`meta-llama/Llama-3.1-8B-Instruct` (111), `Qwen/Qwen3-14B` (16),
`microsoft/Phi-4-mini-reasoning` (1), `deepseek-ai/DeepSeek-R1-Distill-Llama-8B`
(referenced in tokenizer-quirk comments).

**HF cache** — set by every slurm wrapper, offline:
```
HF_HOME=$PROJECT_DIR/.cache/huggingface
HF_HUB_CACHE=$PROJECT_DIR/.cache/huggingface/hub
HF_HUB_OFFLINE=1 ; TORCH_HOME=$PROJECT_DIR/.cache/torch ; TRITON_CACHE_DIR=$PROJECT_DIR/.cache/triton
```
Present on disk: `models--meta-llama--Llama-3.1-8B-Instruct`, `models--Qwen--Qwen3-14B`,
`models--microsoft--Phi-4-mini-reasoning`, `models--deepseek-ai--DeepSeek-R1-Distill-Llama-8B`.
Conda env with torch: `conda activate poc_stage2` (login-node `python3` has NO torch).

---

## 2. Activation extraction — shapes and the layer convention

**THE convention (repo-wide, stated in `pair_common` docstring):**
`hidden_states` is a tuple of length `num_layers + 1`; **index 0 = embeddings**;
`hidden_states[L+1]` = residual stream AFTER block `L` (post-block, 0-indexed block L).
So *"direction at layer L" == `hidden_states[L+1]` == `resid_post[L]` == the tensor a
`LayerPatch(model, L, ...)` forward hook edits.*

| helper | file:line | returns |
|---|---|---|
| `forward_hidden_states(lm, text) -> dict` | ds_common.py:870 | `{"input_ids": [...], "hidden_states": tuple[L+1] of [1,seq,H], "logits": [1,seq,V]}`. Tokenizes with `add_special_tokens=True` (adds BOS). |
| `capture_target_reps(lm, text, codeword) -> dict` | ds_common.py:886 | `{"reps": {"codeword_last": Tensor[L+1, H], "following": ...}, "positions": ..., "input_ids": ...}` — **includes the embedding row 0**. |
| `pair_common.ComponentCapture(lm, components, positions)` | pair_common.py:95 | ctx-mgr; `.stacked() -> {comp: Tensor[n_layers, n_positions, H]}` float32 CPU. **No embedding row** — indexed by block 0..n_layers-1. |
| `pair_common.capture_components(lm, templated_text, probe_word, components=COMPONENTS, position_names=POSITIONS)` | pair_common.py:178 | one forward → `{"reps": {...}, "position_names": [...], "positions": {...}, "logits_last": [V]}`; tokenizes with `add_special_tokens=False` (template already emitted BOS). |

`COMPONENTS = ("resid_pre","attn_out","mlp_out","resid_post")`;
`POSITIONS = ("codeword_last","following","final_prompt","first_generated")`
(`first_generated` aliases `final_prompt`).

Hooks used by `ComponentCapture`: `layer.register_forward_pre_hook` (resid_pre),
`layer.register_forward_hook` (resid_post), `layer.self_attn` / `layer.mlp` forward hooks.

### Word → token span finders

```python
ds_common.find_word_occurrences(tokenizer, input_ids, word) -> WordHit      # :518  id-matching + suffix fallback
ds_common.find_word_occurrences_in_text(tokenizer, text, word,
                                        add_special_tokens=False) -> WordHit # :668  char-offset based (PREFERRED)
ds_common.target_positions(tokenizer, input_ids, codeword, text=None) -> TargetPositions  # :748
pair_common.resolve_positions(lm, templated_text, probe_word) -> PairPositions            # :64
```
`WordHit` (ds_common.py:449): `.word .variant .subtoken_ids .spans[(s,e)] .first_idx[] .last_idx[] .n`.
`PairPositions`: `.codeword_all .codeword_last .following .final_prompt .seq_len`, `.get(name)`.
`TargetPositions`: `.codeword_last .codeword_all_last .following .seq_len`.

Gotchas baked into the code: `resolve_positions` tokenizes `add_special_tokens=False`
(template already has BOS) — mixing it with `capture_target_reps` (which uses True) is a
one-token index shift. Offset finder handles DeepSeek's fused/overlapping offsets.
Also `ds_common.request_start_token(tokenizer, text, fallback, req_prefix="Do not reason, just")`
(:589) locates the demo↔request boundary for knockouts.

---

## 3. Intervention machinery (all context managers; all handle-cleaning on `__exit__`)

### (a) Replace / add / project-out at FIXED positions, ONE layer
```python
ds_common.LayerPatch(model, layer_idx, positions, vector=None,
                     mode="replace"|"add"|"project_out", alpha=1.0)   # ds_common.py:910
```
Forward hook on the decoder BLOCK output ⇒ writes `hidden_states[L+1]`.
Generation-safe: on KV-cached decode steps (`seq==1`) out-of-range prompt positions are
skipped, so it is **prefill-only** for generated tokens.

Sub-block variant:
```python
pair_common.SubmodulePatch(model, layer_idx,
   component="attn_out"|"mlp_out"|"resid_post"|"resid_pre",
   positions, vector=None, mode="replace"|"add"|"project_out", alpha=1.0)  # :286
```
(`resid_pre` uses a forward-PRE hook on the block; batch>1 raises `NotImplementedError`.)

Per-position donor swaps (distinct row per position):
```python
pair_common.DemoStateSwap(model, positions, source: {L: Tensor[n_pos,H]}, ...)  # :204  (writes resid_pre)
pair_common.ComponentOutSwap(model, positions, source: {L: Tensor[n_pos,H]},
                             component="mlp_out"|"attn_out"|"resid_post", batch_index=0)  # :374
```
⚠ `ComponentOutSwap` is **prefill-only** (documented: the `0<=p<seq` guard makes it a
no-op on decode steps) — use the AllPosition* classes for generation-time necessity.

### (b) ADD a direction
```python
pair_common.make_add_hook(direction, alpha=1.0)                              # :883
pair_common.AllPositionAdd(model, layer_idx, direction, alpha=1.0)           # :910
pair_common.AllPositionAddMultiLayer(model, layer_idxs, direction, alpha=1.0)# :930
```
All-position **and** all-timestep (fires on prefill and every decode step). `direction`
is normalized inside, so `alpha` is an absolute residual-space magnitude.
Fixed-position add = `LayerPatch(mode="add", alpha=...)`.

### (c) PROJECT OUT a direction
```python
pair_common.make_project_out_hook(direction, alpha=1.0)                          # :637
pair_common.AllPositionProjectOut(model, layer_idx, direction, alpha=1.0)        # :664
pair_common.AllPositionProjectOutMultiLayer(model, layer_idxs, direction, alpha) # :692  (Arditi-style directional ablation)
pair_common.make_single_position_project_out_hook(direction, alpha=1.0, pos=-1)  # :742
pair_common.SinglePositionProjectOut(model, layer_idx, direction, alpha=1.0, pos=-1) # :773  (D3 scope-matched control, prefill-only by design)
pair_common.AllPositionMLPAblate(model, layer_idxs,
        mode="zero"|"scale"|"project_out"|"mean", direction=None, alpha=1.0)     # :800
```
`mode="mean"` in `AllPositionMLPAblate` / `AllPositionZHeadAblate` is **prefill-only**
(mean over seq is identity when seq==1) — use `"zero"` for generation-time tests.

### (d) Attention knockout
```python
pair_common.AttentionKnockout(model, layer_idxs, query_positions,
                              blocked_keys, heads: Optional[Sequence[int]] = None)  # :436
```
Forward-pre hook on `layer.self_attn` with `with_kwargs=True`; clones the 4-D additive
mask and writes `finfo.min` at `(q,k)`. **Requires `attn_implementation="eager"`; raises
`RuntimeError` if the mask isn't 4-D; batch>1 raises.** `heads=None` = all heads;
head list expands over the QUERY-head axis (`config.num_attention_heads`, not KV heads/GQA).

Head-level z (o_proj input, `[batch, seq, n_heads*head_dim]`):
```python
pair_common.ZHeadPatch(model, layer_idx, head, positions, corrupt_vec)   # :509  fixed positions
pair_common.AllPositionZHeadAblate(model, heads_by_layer: {L:[h,...]}, mode="zero")  # :553  decode-safe
pair_common.ZHeadCapture(model, layer_idxs)                              # :601  grad-retaining, for AtP
pair_common._attn_head_dims(model) -> (n_heads, head_dim)                # :501
```

**The two knockout scripts** (older, hand-rolled — `AttentionKnockout` supersedes them):
* `DC/09_attention_knockout.py` — `build_mask(seq, device, dtype, q_pos, blocked_keys)`
  builds a full causal 4-D mask passed as `attention_mask=` to the forward;
  `rep_under_mask(lm, input_ids, mask4d, pos, readout_layer)` returns
  `out.hidden_states[readout_layer+1][0, pos, :]`. Loads with
  `attn_implementation="eager"` (line 81). CLI: `--model --data --templated --dtype
  {bfloat16,float16} --readout-layer 30 --only virus_muffin --seed --out-dir`.
* `DC/10_layerwise_knockout.py` — per-layer pre-hook version:
  `make_block_hook(cw_pos, demo_keys, min_val, status=None)` and
  `rep_with_layer_block(lm, tok, layers_to_block, cw_pos, demo_keys, readout_layer, status=None)`.
  `status["mask_ok"]=False` + stderr warning if the mask isn't 4-D (fix C6b: it used to
  silently no-op and report "attention has no causal effect").

### Composition + cheap outcomes
```python
pair_common.semantic_score(lm, templated_text, id_groups: {name:[ids]},
                           patches=[(layer, positions, vec, mode, alpha), ...]) -> {name: prob}  # :979
pair_common.patched_generate(lm, templated_text, patches=(), max_new_tokens=8) -> str            # :998
pair_common.word_first_ids(tokenizer, word) -> [int]                                             # :968
ds_common.generate(lm, prompt, max_new_tokens=256, templated=True, enable_thinking=None) -> dict # :997
ds_common.apply_template(tokenizer, prompt, add_generation_prompt=True, enable_thinking=None)    # :848
ds_common.patch_layer_sweep(readout_layer) -> [0..readout_layer-1]                               # :972
```
`patch_layer_sweep` encodes the C1/C3 defect fix: **never patch at the readout layer**
(it overwrites the measured vector with zero propagation).
Everything composes via `contextlib.ExitStack` (that's the pattern in
`scripts/phase4_bombness_intervention.py`).

Matched-control vectors:
```python
pair_common.norm_matched_random(direction, n, seed=0) -> [n,H]   # :1016
pair_common.orthogonal_random(direction, n, seed=0)              # :1024
pair_common.in_subspace_random(basis, direction, n, seed=0)      # :1033
```

Synthetic unit tests exist for essentially every hook: `DC/tests/test_layerpatch_synthetic.py`,
`test_attnknockout_synthetic.py`, `test_projectout_hook_synthetic.py`, `test_alladd_hook_synthetic.py`,
`test_allposmlp_synthetic.py`, `test_allposzheadablate_synthetic.py`, `test_zhead_synthetic.py`,
`test_componentcapture_synthetic.py`, `test_componentoutswap_synthetic.py`,
`test_demostateswap_synthetic.py`, `test_submodulepatch_components_synthetic.py`,
`test_singleposition_projectout_synthetic.py`, `test_resolve_positions_synthetic.py`,
`test_hook_firing_synthetic.py`.

---

## 4. Direction building + what already exists ON DISK

### Builders
| script | builds | layer naming |
|---|---|---|
| `DC/build_refusal_direction_llama.py` | `v_refusal[L] = normalize(mean(h_harmful) - mean(h_harmless))` at the **last input token**, captured as `forward_hidden_states(...)["hidden_states"][L+1][0,-1,:]` | file suffix `_L{L}` == block L == `hidden_states[L+1]` |
| `DC/33_build_directions.py` | `d_Direct`, `d_DS`, `d_benign`, `d_unrelated` (all minus `NEUTRAL_CODEWORD` mean) + top-k PCA subspaces, **cross-fitted on `dev` and `heldout`** | keys `d_Direct\|<split>\|<comp>\|<pos>` in `directions.npz` |
| `DC/scripts/build_unified_directions.py` | merges concept / signature / refusal into one `.npz` per cohort, keeps them DISTINCT, reports cross-cosines | `[32, H]` arrays indexed by block L |
| `DC/scripts/build_random_dir_L18.py` | one norm-matched Gaussian control at L18 | bare `float32` tensor, `torch.load(..., weights_only=True)` |
| `DC/scripts/build_random_dir_anylayer.py` | per-layer norm-matched randoms, `seed = base_seed + L` | `refusal_rand_L{L}_normmatched_seed{seed}.pt` |
| `DC/src/probes/build_intervention_directions.py` | **the Bombness bundle** (see below) | band `range(8,22)` |

CLI shapes:
```
python scripts/build_unified_directions.py --concept-dir outputs/pair_directions_<...> \
  --refusal-dir outputs/refusal_alllayers --cohort clearharm [--split dev] \
  [--component resid_post] [--position codeword_last] [--out-dir outputs/unified_directions]

python scripts/build_random_dir_anylayer.py --src-dir outputs/refusal_alllayers \
  --src-prefix refusal_direction_llama_L --layers 12,18 \
  --out-dir outputs/gate7_v3_randdirs --base-seed 20260809

python src/probes/build_intervention_directions.py --run <acts run dir> \
  --refusal outputs/stage_gcg_full/refusal_direction_llama_L18.pt --out <out.pt> [--band 8,..,21]
```

### Direction tensors ON DISK (all paths relative to `DC/`)

**Bombness (already exists!) — `outputs/phase4_directions/`**
`v_bomb_advbench.pt`, `v_bomb_advbench_v2.pt`, `v_bomb_clearharm.pt`,
`v_bomb_generated.pt`, `v_bomb_Phi-4-mini-reasoning.pt`, `v_bomb_Qwen3-14B.pt`.
Payload (from `build_intervention_directions.py:87`):
```python
{"layers": [8..21],
 "v_bomb":          {L: Tensor[H]},   # unit diff-of-means (doublespeak - benign) at codeword_last
 "v_bomb_perp_ref": {L: Tensor[H]},   # v_bomb orthogonalized against refusal_L18
 "v_random":        {L: Tensor[H]},   # norm-matched control, seed 20260814
 "gap":             {L: float},       # ||mean_ds - mean_benign||, the NATURAL DOSE UNIT
 "cos_vs_refusal":  {L: float}, "gap_over_sd": {L: float}, "meta": {...}}
```
Convention: `WRITE_CARRY_BAND = list(range(8, 22))` — write L8–11 + carry L14–21.

**Refusal directions** (bare `float32` tensors; `.json` sibling carries `separation`):
* `outputs/stage_gcg_full/refusal_direction_llama_L{12,14,16,18,20}.pt` + `_SELECTED.json`
  — **L18 is the canonical Llama refusal direction** (default `--refusal-pt` everywhere).
* `outputs/refusal_alllayers/refusal_direction_llama_L{0..31}.pt` (+ `.json`, `DONE.json`).
* `outputs/refusal_qwen3/refusal_direction_llama_L{16,20,24,28,32}.pt` (name kept "llama"; content is Qwen3-14B).
* `outputs/refusal_phi/refusal_direction_llama_L{12,14,16,18,20,22}.pt` + `_SELECTED.json`.
* `outputs/refval_clearharm_<ts>_<jobid>/refusal_direction_clearharm_L{k}.pt` — validated
  ClearHarm-fit variants; the all-layer ones are
  `refval_clearharm_20260805_215332_717880` and `refval_clearharm_20260806_054117_722611`
  (L0–L31); subsets in `..._20260806_033340_720463`, `..._20260806_051728_721957` (L9/16/18/22/28)
  and `..._20260806_111105_724931` (L9/16/18/21/22/30).

**Concept directions**
* `outputs/concept_qwen3/concept_direction_qwen3_L{16,20,24,28,32}.pt` (+ `.json`)
* `outputs/concept_phi/concept_direction_qwen3_L{12,14,16,18,20,22}.pt` (name is a copy-paste; content is Phi)
* `outputs/gate7_v3_conceptdirs/{concept_L9_unit.pt, concept_L16_unit.pt,
  concept_neg_L9_unit.pt, concept_neg_L16_unit.pt,
  concept_rand_L{9,16}_normmatched_seed20260809.pt}`

**Random controls**
* `outputs/gate7_firstcut/refusal_rand_L18_normmatched_seed20260808.pt`
* `outputs/gate7_v3_randdirs/refusal_rand_L{12,18,22}_normmatched_seed20260809.pt`

**Bundled / multi-direction `.npz`**
* `outputs/unified_directions/{clearharm,curated}.npz` (+ `.json`, RUNMETA, DONE) —
  arrays `concept[32,H] signature[32,H] refusal[32,H]`.
* `outputs/pair_directions_<ts>_<uniq>/directions.npz` (3 dirs, keys `d_*|split|comp|pos`).
* `outputs/pair_reps_<ModelTag>_<ts>_<uniq>/{means,per_prompt,subsample}.npz`
  (`per_prompt.npz["resid_post_codeword"]`).

Nothing under `DC/data/` holds direction tensors — `data/` is corpora/splits only
(`data/splits/clearharm_doublespeak_v3.json`, `advbench_doublespeak_v2_lenmatched.json`,
`data/behavioral_v3/beh_clearharm.json`, `data/pair_benchmark/pair_carrot_bomb.json`, …).

---

## 5. Logit lens / patchscope readouts that already exist

**`DC/07_patchscope_readout.py`** — free-next-token patchscope.
```python
class PatchscopeDecoder:                                        # 07:49
    def __init__(self, lm, inspection_prompt=INSPECTION_PROMPT)  # identity prompt "cat->cat; 1124->1124; hello->hello; ?"
    def decode(self, vector, inspect_layer, harm_id, code_id) -> (p_harm, p_code)
        # dc.LayerPatch(model, inspect_layer, [self.q_pos], vector, mode="replace"); softmax at q_pos

def patched_codeword_rep(lm, text, patch_layer, patch_pos, vector,
                         readout_layer, mode="replace")          # 07:72
    # -> out.hidden_states[readout_layer + 1][0, patch_pos, :]
def token_id(tokenizer, word)                                    # 07:43  (last id of " word")
```
Measures necessity (DS←Neutral patch) and sufficiency (Neutral←Direct patch) at
readout layer R, sweeping patch layers `[0, R)`.
CLI: `--model --data --templated --dtype --readout-layer --only --seed --out-dir`.

**`DC/46_forced_choice_patchscope.py`** — forced-choice patchscope; removes the
"safety-tuned model won't *emit* the harmful word" floor.
```python
class PatchscopeForcedChoice:                                    # 46:97
    def __init__(self, lm, concept, codeword, probe_word=None)   # injects at last subtoken of FIRST probe occurrence
    def decode(self, vector, inspect_layer, concept_ids, code_ids) -> (p_concept, p_code)  # read at FINAL position
def patchscope_gate(scores, thresh=0.1)                          # 46:76  positive-control gate
```
Gated: only runs if a clean DIRECT-concept rep from SOME layer forces the concept
choice (`pos_ctrl_max > 0.1`, records `best_ps_layer`).
CLI: `--bench --model --readout forced_choice --inspect-layer --splits dev,heldout --seed --out`.

**`DC/31_validate_readouts.py`** — the S2 gate: validates *every* safe semantic readout
before any intervention is interpreted (positive control DIRECT_CONCEPT vs negative
control NEUTRAL_CODEWORD), from ONE greedy generation per prompt:
next-token prob of concept-vs-codeword + generated one-word answer mapped to a lexicon.
```python
word_first_ids(tokenizer, word); normalize_answer(text)
classify_answer(text, lexicons, concept_key=None, codeword_key=None)
generate_with_first_scores(lm, templated_text, max_new_tokens, id_groups, ...)   # 31:111
```
CLI: `--bench --model --out-root outputs --max-new-tokens 8 --limit --seed
--enable-thinking {default,true,false} --answer-marker --reanalyze`.

Cheap non-generative readout used by the sweeps: `pair_common.semantic_score`
(next-token mass on id groups under patches). Bombness readout (projection onto
`v_bomb[L]` at unpatched downstream layers) is
`scripts/phase4_bombness_intervention.py::bombness_readout(lm, text, cw_pos, vbomb, patches)`,
with `READOUT_LAYERS = [20, 24, 28, 31]`.

---

## 6. Run-metadata contract

`ds_common.py` — YES, there is a full helper pair. Contract: `RUNMETA.json` first,
`DONE.json` last. **Neither ever raises** (provenance must not kill a run).

```python
ds_common.RUNMETA_NAME = "RUNMETA.json"; ds_common.DONE_NAME = "DONE.json"

write_runmeta(out_dir: str, args: Any = None,
              extra: Optional[Dict] = None) -> Dict      # ds_common.py:184
write_done(out_dir: str, rows_written: Optional[int] = None,
           extra: Optional[Dict] = None) -> Dict         # ds_common.py:282
env_metadata() -> Dict                                    # ds_common.py:131
git_commit() -> str ; git_dirty() -> Optional[bool]       # :76 / :116
set_seed(seed: int) -> None                               # :332
```

`RUNMETA.json` (`"schema": "RUNMETA/1"`) fields: `run_id, output_dir, script, argv, args,
seed, slurm_job_id, slurm_nodelist, hostname, git_commit, git_dirty, python,
python_executable, torch, transformers, cuda_available, gpu, start_ts, start_epoch, cwd`.
Calling it a SECOND time with the same `out_dir` **merges/enriches** (keeps the original
`start_ts`/`start_epoch`) — the idiom is: call once at the top with `args`, call again
after `load_model` with `extra=lm.meta()`.
`DONE.json` (`"schema": "DONE/1"`): `run_id, status, rows_written, end_ts, end_epoch,
wall_seconds` (computed from RUNMETA's `start_epoch`, `null` if absent).

Reconstruction tool for pre-contract dirs — `DC/scripts/backfill_runmeta.py`
(login-node, stdlib only, read-only by default; writes `RUNMETA/1-reconstructed` /
`DONE/1-reconstructed` with `{value, source, evidence}` objects, never overwrites):
```
python scripts/backfill_runmeta.py                                    # dry run (default)
python scripts/backfill_runmeta.py --apply [--overwrite] [--clean]
python scripts/backfill_runmeta.py --apply --report-json outputs/backfill_report.json
  # other flags: --outputs --logs --slurm --strict-names --only <glob>
```
Sources it will use: dir name, `logs/<prefix>_<jobid>.out` (producer-only), the matching
`slurm/*.sh` wrapper (argv template, unexpanded), `summary.json`, mtimes.
It counts `raw.jsonl` rows in BINARY without decoding (never materializes harmful text).

**Run-dir naming convention** (used by ~15 scripts):
`outputs/<prefix>_<ModelTag>_<YYYYMMDD_HHMMSS>_<SLURM_JOB_ID or PID>`
```python
uniq = os.environ.get("SLURM_JOB_ID") or str(os.getpid())
```
Companion tooling: `scripts/update_registry.py` (→ `EXPERIMENT_REGISTRY.csv`),
`scripts/audit_artifacts.py`, `scripts/validate_all_outputs.py`,
`scripts/validate_experiment_coverage.py`, `scripts/check_report_vs_json.py`, and
expected-arm manifests in `DC/configs/manifests/*.json`
(`baseline_drift, behav_carry, defense_gated, defense_util, phase9_gcg_mac_matrix,
refdecpatch, refsuploc, refval, role_probe_sprint_v1`) with fields
`phase, title, plan, source_script, validator_type, created, spec_version,
expected_arms, min_n_per_split, _what_this_is, _notes`.

---

## 7. SLURM — best 1-GPU L40S template to copy

**Copy `DC/slurm/run_behav_carry.sh`** (a generation + GPU-hook job, hard-gated to L40S,
with the fully documented resource footprint). Second-best for a forward/patching-only
job: `DC/slurm/run_phase4_mediation.sh` (looser ≥23 GB GPU allowlist).

Header (every `#SBATCH` line is a DEFAULT — override on the `sbatch` line, no file edit):
```bash
#!/bin/bash
#SBATCH --job-name=ds_behcarry
#SBATCH --output=doublespeak_causality/logs/ds_behcarry_%j.out
#SBATCH --error=doublespeak_causality/logs/ds_behcarry_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=48G
#SBATCH --time=06:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-801,n-802,n-803,n-804,n-805,t-806
```
Body:
```bash
set -euo pipefail
PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
cd "$PROJECT_DIR"
source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate poc_stage2
if [ -f "$PROJECT_DIR/.env" ]; then set -a; source "$PROJECT_DIR/.env"; set +a; fi
mkdir -p doublespeak_causality/logs doublespeak_causality/outputs "$PROJECT_DIR/.cache"/{huggingface,torch,triton}
export HF_HOME="$PROJECT_DIR/.cache/huggingface"; export HF_HUB_CACHE="$PROJECT_DIR/.cache/huggingface/hub"
export HF_HUB_OFFLINE=1; export TORCH_HOME="$PROJECT_DIR/.cache/torch"; export TRITON_CACHE_DIR="$PROJECT_DIR/.cache/triton"
export PYTORCH_CUDA_ALLOC_CONF="${PYTORCH_CUDA_ALLOC_CONF:-expandable_segments:True}"; export PYTHONUNBUFFERED=1
: "${DSBENCH:=doublespeak_causality/data/behavioral/beh_clearharm.json}"
: "${DSMODEL:=meta-llama/Llama-3.1-8B-Instruct}"
: "${DSN:=0}"; : "${DSSEED:=0}"
echo "=== ... ==="; date; hostname; echo "git=$(git rev-parse HEAD 2>/dev/null||echo NA)"
GPU_ALL="$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null || true)"; GPU_TYPE="${GPU_ALL%%$'\n'*}"
case "$GPU_TYPE" in *L40S*|*l40s*) echo "GPU ok: $GPU_TYPE";; *) echo "ERROR need L40S got '$GPU_TYPE'"; exit 1;; esac
python -u doublespeak_causality/scripts/<your_script>.py --model "$DSMODEL" ... --seed "$DSSEED"
echo "=== done ==="; date
```

Hard-won rules encoded in these files — do not re-litigate:
* **`cpus=4 mem=48G` is the fast-allocating default.** 8cpu/64G sat PENDING 3h32m
  (jobs 716187/716188); the identical work at 4cpu/48G allocated in 6m32s (717879/717880).
  Node `RealMemory=515600MB / 8 GPUs = 64450MB` per GPU-share, so `--mem=64G` makes only
  7 of 8 GPUs feasible per node. `--time` is not the lever.
* **NEVER use `--exclude`.** Passing `--exclude` on the sbatch line NULLIFIES the
  `#SBATCH --nodelist` and the job lands anywhere in the partition (2026-08-06 jobs
  721954/721955 → n-306, an RTX 3090; only the GPU guard caught it). To skip a node, pass
  a REDUCED nodelist: `sbatch --nodelist=n-802,n-803,n-804,n-805,t-806 slurm/<w>.sh`.
* L40S nodelist: `n-801,n-802,n-803,n-804,n-805,t-806`. n-801 is included (full
  gpu:l40s:8) but every weight-load >15 min in 232 logged runs happened there (worst 79 min).
* **`--export` truncates comma-list values** (`LENGTHS=5,20` silently becomes `5`).
  Comma-lists (heads, splits) stay as in-file DEFAULTS; `run_phase4_mediation.sh` even
  loops over scalar vars and `exit 1`s if any contains a comma. Verify row counts after
  a "COMPLETED".
* Forward/patching-only jobs may use the wider guard from `run_phase4_mediation.sh`:
  allowlist `L40S|A5000|A6000|A100|A40|H100|H200|L40|3090|4090` **and** `GPU_MEM >= 23000` MiB.
* Smoke idiom: `sbatch --export=ALL,DSN=2 slurm/<wrapper>.sh`.

---

## 8. Ready-made Boombness harness (already written — start here)

`DC/scripts/phase4_bombness_intervention.py` is a complete necessity/sufficiency harness
for `v_bomb`. Constants: `PATCH_BAND = list(range(8,19))`, `READOUT_LAYERS=[20,24,28,31]`,
`REFUSAL_LAYER=18`.
```
--corpus data/splits/clearharm_doublespeak_v3.json  --directions <v_bomb .pt> (required)
--refusal-pt outputs/stage_gcg_full/refusal_direction_llama_L18.pt
--split test --cohort clearharm --out <dir> (required) --alpha 1.0 --max-new 220 --limit 0
--with-refusal --factorial --base-field doublespeak_prompt|neutral_prompt
--intervene ablate|add --dose 1.0 --no-judge --model --quantize {8bit,4bit} --seed 20260814
```
Arms: `ds_base`, `ds_bomb_ablate|ds_bomb_add`, `ds_bomb_random`,
(`ds_refusal_ablate`), (`ds_bomb_and_refusal_ablate`); prefix becomes `neu_` with
`--base-field neutral_prompt`. Ablate = stacked `dc.LayerPatch(..., mode="project_out",
alpha)` at `[codeword_last]` over the band; add = `mode="add", alpha=dose*gap[L]`;
refusal control = `pc.AllPositionProjectOutMultiLayer(model, range(num_layers), v_ref, alpha)`.
Judge = `strongreject_scoring.load_strongreject_evaluate()` from `<repo>/poc_stage3`.
Outputs `raw.jsonl` (per example: `example_id, split, codeword,
<arm>_bombness_readout {L: proj}, <arm>_score, <arm>_label`), `gens.jsonl`, `DONE.json`.
Analysis: `DC/scripts/analyze_phase4.py` / `src/probes/analyze_phase4.py`.
Existing runs: `outputs/phase4_bombness_full_{clearharm,generated,advbench_*}_...`,
`phase4_bombness_smoke_*`.

Activation extractor that feeds it:
`DC/src/probes/activation_extraction.py` (GPU) →
`acts.npy [n_items, n_layers, n_positions, hidden]` + `items.jsonl` (ids/labels only, no
prompt text) + RUNMETA/DONE. `PRIMARY_POSITIONS=("codeword_last","final_prompt")`,
`COMPONENT="resid_post"`. Batch-1 forwards by design (no left-pad position drift).
CLI: `--corpus --cohort --conditions doublespeak,benign,neutral --out (req) --model
--dtype --revision --space {resid_post,norm_mid} --quantize --limit`.
Loader/probe helpers: `src/probes/probe_dataset.py` (`load_corpus`, `build_items`,
`assert_split_discipline`, `BINDING_CONDITIONS=("doublespeak","neutral","benign")`,
`POSITIVE_CONDITION="doublespeak"`, `NEGATIVE_CONDITION="benign"`),
`src/probes/smoke_fit.py` (`load_run(run_dir)`, `POSITIONS=("codeword_last","final_prompt")`,
`fit_per_layer(acts, items, position="codeword_last", seed=0)`),
`src/probes/contextual_identity_probe.py` (`diff_of_means_direction(X,y)`,
`fit_and_eval(...)`, `evaluate_direction(v,b,X,y,groups,n_boot=2000,seed=0)`,
`control_label_shuffle`, `control_random_direction`, `cosine`).

---

## 9. Stats + plots

`DC/stats.py`:
```python
paired_bootstrap_ci(x, y, n_boot=10000, alpha=0.05, seed=0) -> dict
mcnemar_test(b, c) -> dict
permutation_test_paired(x, y, n_perm=10000, seed=0, alternative="two-sided") -> dict
paired_cohens_d(x, y) -> float
rank_biserial_paired(x, y) -> float
holm_bonferroni(pvals) -> List[float]
```
`DC/plots.py` (matplotlib, no seaborn):
```python
layer_trajectory(layers, series, out_path, title="", ylabel="value", ci=None)
layer_metric_heatmap(matrix, row_labels, col_labels, out_path, title="", cbar_label="")
grouped_bars(categories, group_values, out_path, title="", ylabel="")
vline_annotate(ax, x, label="", color="#555555")
```

## 10. Known footguns worth re-reading before writing new code
* `DC/BUG_AND_DEVIATION_LOG.md` (24 KB) — the running bug ledger.
* Prefill-only vs decode-safe: `LayerPatch`, `SubmodulePatch`, `ComponentOutSwap`,
  `SinglePositionProjectOut`, and `mode="mean"` ablations are **prefill-only**;
  `AllPosition*` classes with `mode="zero"/"scale"/"project_out"` and `make_add_hook`
  fire on every decode step.
* `add_special_tokens` mismatch between `ds_common` (True) and `pair_common` (False).
* Never patch at the readout layer (`patch_layer_sweep`).
* Attention knockout needs `attn_implementation="eager"`.
* Batch>1 raises in `SubmodulePatch` / `AttentionKnockout` (deliberate: they edit row 0).
