# research/heretic_csi

Research code for the **Heretic × Causal-Semantic-Installation (CSI)** sprint. See the authoritative
plan & append-only log: `external_md/HERETIC_CAUSAL_SEMANTIC_INSTALLATION_PLAN_AND_PROGRESS_20261001.md`.

## Question
Can the causal semantic-installation mechanism (CSI) be distilled into a compact **weight-level
operator** `ΔW = BA` of some effective rank, and does the required rank/location explain the
**basket-vs-button** dissociation (basket: rank-1 axis rescue PASSES; button: rank-1 NEGATIVE at
matched power; whole-state rescue works for both)?

## Architecture (see log S-004 for the full ruling)
- **Headline rank sweep (P2)** runs in the CSI **rescue-under-knockout** paradigm, forced to **eager**
  attention, reusing the frozen CSI readout (`y_install = logistic(logp_concept − logp_codeword)`),
  the per-example **codeword-row** anchor (`rel_end=-10`, never last-token / never absolute), and the
  existing **rank-matched control families** — with Heretic's ARA L-BFGS kNN optimizer + plugin API +
  Optuna as the operator-fitting engine. TARGET = clean module-I/O; SOURCE = knockout module-I/O.
- **Phase B** runs **native Heretic ARA** (shipped, last-position, knockout-free) as a baseline/control.
- Endpoint scored in `poc_stage2` (eager) by loading the exported LoRA adapter into the frozen
  `score_behavior.py` readout, AND by an inline heretic scorer cross-checked against it.

## Modules
- `positions.py` — per-example end-relative anchor location (`rel_end=-10` codeword row, `-6` axis),
  with a LOUD codeword-decode self-check and left-padding handling. (env-agnostic; tokenizer only)
- `semantic_scorer.py` — the `y_install` semantic-installation endpoint (ports `signals.readout_id_pair`
  + `score_behavior.next_token_readout` logic); usable standalone and as a Heretic `Scorer` plugin. (TBD)
- `preservation_scorer.py` — unrelated/control-representation preservation + KL. (TBD)
- `position_aware_ara.py` — `PositionAwareARA`, a Heretic `Modifier` plugin that captures module-I/O at
  the per-example codeword row and fits `ΔW=BA` at a configurable rank/layer-range/component. (TBD)
- `head_restricted_ara.py` — restrict `ΔW` to specific attention heads' `o_proj` columns (P4). (TBD)
- `extract_learned_subspace.py` — SVD of the learned `ΔW`; truncation/removal interventions (P3). (TBD)
- `configs/` — Heretic TOML configs per phase. `tests/` — unit + synthetic + small-real smoke tests.

## Environment
Runs in conda env **`heretic_csi`** (isolated; torch 2.13 / transformers 5.6 / optuna 4.8 / peft 0.19)
for Heretic-side optimization; the endpoint eval runs in **`poc_stage2`** (frozen CSI stack, eager).
Model `meta-llama/Llama-3.1-8B-Instruct` (pinned rev), **bfloat16 + eager**. Native-bf16 GPUs only
(3090/L40S/a5000); V100 PROHIBITED.

## Provenance / license
Heretic is **AGPL-3.0** (pinned `external_repos/heretic/` @ `662e4ba2`). This code builds against it via
the external plugin API; it does not vendor large chunks. Reused CSI logic is tagged with its source
file in-code. Do not distribute / network-serve a derivative without AGPL compliance review.
