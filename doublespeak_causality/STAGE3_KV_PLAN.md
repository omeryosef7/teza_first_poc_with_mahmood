# Stage 3 — Demonstration K/V Mediation: Build Plan

**Gate:** PASSED (Stage 2: DE_context substantial after controlling query state). Goal: localize *where* in the receiver context the effect is routed, and **resolve the cloze-readout-attends-context confound** (Stage 2 caveat 2).
**Source:** reconnaissance agent (2026-07-30), all citations verified against `.py`.

## Key facts
- **No KV-cache/`past_key_values` code exists** in the project. Build the demo-K/V swap as a **`resid_pre` write-hook at demonstration positions** (K,V are projected from resid_pre, so overwriting demo-token resid_pre swaps the K/V the query attends to) — preserves sequence length, works under default SDPA, ~20 lines.
- Richer primitive library is in **`pair_common.py`** (not ds_common): `ComponentCapture` (resid_pre/attn_out/mlp_out/resid_post capture, :83-159), `SubmodulePatch` (:189-242), `AttentionKnockout` (4-D mask, needs eager, :248-299), `semantic_score` (:315-331), `resolve_positions`/`PairPositions` (:44-77).
- **Confound-free readout:** `PatchscopeDecoder` (`07_patchscope_readout.py:49-68`) injects the codeword rep into a **demo-free** inspection prompt (`"hello hello\nworld world\ncat cat\nX"`) — the "?" position cannot re-read the demos, so it isolates whether the concept lives *in the codeword vector* vs is re-read from context. This directly adjudicates trivial-re-read vs genuine consolidation.

## New code (minimal)
1. `DemoStateSwap` (~20 lines, add to `pair_common.py`): `register_forward_pre_hook(with_kwargs=True)` on chosen layers; overwrite `hidden_states[0, demo_positions, :]` with source rows captured by `ComponentCapture(resid_pre)`.
2. `44_kv_mediation.py` (~80 lines, model on `34`'s cell loop + `emit`): realize the 2×2, persist scalars, reduce with `43`/`stats` estimand+CI code.

## The 2×2 (receiver always DOUBLESPEAK — only condition with demo tokens)
Factor A = query **state** at `codeword_last` (`LayerPatch replace`, source via `source_vec`). Factor B = demo **K/V** (`DemoStateSwap` at demo sites).

| Cell | query state | demo K/V | realization |
|---|---|---|---|
| C1 | h_DS (self) | DS (identity) | plain DS forward ≈ baseline |
| C2 | h_N transplant | DS | = existing `DS_from_Neutral` arm (34:377) |
| C3 | h_DS (self) | Neutralized | `DemoStateSwap` at demo sites, query untouched |
| C4 | h_N transplant | Neutralized | `LayerPatch` (query) + `DemoStateSwap` (demos) together |

**Contrasts** (feed the `43` estimand reducer):
- `DE_via_demoKV = Y(C2) − Y(C4)` — concept reading carried specifically by demo K/V.
- **`ReRead_test = Y(C1) − Y(C3)`** — THE discriminator: if neutralizing demo K/V collapses the concept *even with the genuine DS query state*, the cloze readout is re-reading the demos (trivial); if it survives, the state is self-sufficient (genuine consolidation).
- `INT_2x2 = [Y(C1)−Y(C3)] − [Y(C2)−Y(C4)]`.

**Neutralized demo source (length-preserving):**
- *Primary:* swap only at demo-codeword occurrences `prev_cw = hit.last_idx[:-1]`, source rows from the NEUTRAL_CODEWORD codeword token (count/position-matched, no length assumption — isolates the substitution history).
- *Secondary:* whole demo-column swap from a length-matched control demo_style.
- *Extreme reference:* `AttentionKnockout` blocking `q=codeword_last → demo keys` (36_pair_attention.py verbatim) = "demo-KV absent" upper bound.

## Controls (reuse verbatim)
Count-matched random demo tokens (`09:131-139` `rand_demos_matched`; `36:103-114` `random_matched`, both exclude/precede codeword) → concept must NOT move if codeword-specific. Position-matched `adjacent`/`random_token` (`34.patch_sites`). Shuffled cross-item donor (`34:408-427`). Self-swap faithfulness (must reproduce baseline).

## Readouts
1. `semantic_score` next-token mass (comparable to Stage 2).
2. **`PatchscopeDecoder` confound-free cross-check** (demo-free inspection) — isolates in-vector vs re-read. Positive-control gating built in (`07:126-127`).

## Compute
Core 2×2 + confound-free readout: **~15–20 min** on one L40S (forward-only, ~1k–5k forwards). Optional per-head demo-KV attribution (`AttentionKnockout per_head`, eager) only on the winning window. Total < 1 GPU-hr.

## Imports for 44_kv_mediation.py
`ds_common` (load_model, apply_template, LayerPatch, find_word_occurrences, request_start_token); `pair_common` (resolve_positions, semantic_score, ComponentCapture, + new DemoStateSwap); reduce with `43`/`stats`. Reuse `36.source_positions` for demo/prev-codeword sets. Persist scalars only.
